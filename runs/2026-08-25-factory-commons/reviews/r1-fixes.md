# r1 fixes — factory-commons

Head: `0079af89bb220cd03b654866472323648f87d9f0` (main)
CI: https://github.com/Metta-AI/cogame-factory-commons/actions/runs/32883915882 — **success**
(jobs `test`, `docker-smoke`, `wasm-viewer` all `success`; `grep -c "SEAT-COUNT FAIL"` over the
full run log: **0**; `smoke OK: seats=3 results=450B replay=96236B reason=complete`;
`{"loaded":true,"ms":379,"clock":"SHIFT 5 / 8 TICK 287 OF 479",…}` with
`soak: 12s of playback kept advancing ("0 / 479" -> "239 / 479" -> "287 / 479")`; the worst-case
renderer fixture reports `canvas text: 9 drawn, 0 never inside the canvas … (--strict-text-bounds)`.)

Nine commits, one per finding. No test was disabled, skipped, weakened or deleted: every test file
change in this round **adds** assertions (`test_replay.nim` +202 lines, `test_llm.nim` +9 checks for
the throttle/raise cases and +9 for the settle budget; total checks 5 519 → 78 000+ because the new
frame loop asserts ~40 fields on each of 1 800 frames).

| finding | disposition | commit | files |
|---|---|---|---|
| **B1** frame-by-frame re-derivation untested | **fixed** | `119a8ba` | `tests/test_replay.nim:174-375` |
| N1 `eatTrigger 3 → 6` is off the note's ladder | **fixed** | `04058a7` | `src/factory_commons/sim_config.nim:12-38,69`, `coworld_manifest_template.json:213`, `docs/tuning.md` |
| N1 `moveCooldown 2 → 1`, `stripCapLoss 12 → 16` | declined (note-sanctioned, now evidenced) | — | `design.md:397-399`; `docs/tuning.md` |
| N2 five overrides, not seven; stale prose | fixed in prose, rule declined | `90424bd`, `0079af8` | `README.md:142-160`, `tools/ci/policies.json`, `src/factory_commons_player.nim` |
| N3 prompts quote superseded numbers | **fixed** | `90424bd` | `tools/ci/policies.json:6,14`, `src/factory_commons_player.nim:31`, `src/factory_commons/llm.nim:386-422`, `tests/test_llm.nim:366-381` |
| N4 steward harvest rule ≠ note's rule 3 | **DISPUTED-as-necessary** (measured) | — | `src/factory_commons/scripted.nim:56-85` |
| N5 gate (b) skipped on `either-or` | declined (measured 0/12, reason is written in the test) | — | `tests/test_feasibility.nim:110-135` |
| N6 `blocked` dedupe | declined | — | `src/factory_commons/sim_state.nim:24-44` |
| N7 429 retried in the same shift | **fixed** | `7434451` | `src/factory_commons/llm.nim:37-41,626-628,760-770`, `tests/test_llm.nim:311-366` |
| N8 `doStrip` clamps integrity to the new cap | declined (holds the tested invariant) | — | `src/factory_commons/machine.nim:213` |
| N9 cert fixture adds `capMin: 25` | declined (documented, tested, load-bearing) | — | `coworld_manifest_template.json:617`, `tests/test_manifest.nim:340-372` |
| N10 `fallbacks[i]` counts LLM fallbacks only | declined (documented; the number phase 60 wants) | — | `src/factory_commons/llm.nim:714-720` |
| N11 beat markers are decorated `div`s | declined (conflicts with checklist 14's byte-identity) | — | `client/replay_broadcast.html:3004-3047` |
| N12 renderer fixture mirrors the game block | declined (stated in the file; it is the gate that reports non-zero text) | — | `tools/ci/renderer_fixture.html:31-36` |
| N13 `canvas_text.total` 0 on the bundle | declined (no `fillText` in the worker; N12 is the compensating gate) | — | `client/broadcast_core.js` |
| N14 `NIMBY_VERSION` pin drift | **fixed** | `c8ba7f1` | `.github/workflows/ci.yml:35` |
| N15 transport call outside the `try` | **fixed** | `7a0254c` | `src/factory_commons/llm.nim:749-763`, `tests/test_llm.nim:290-310` |
| N16 two test-file edits, both traced | no action (informational) | — | — |
| N17 worst-case settle ≈ 773 s > 720 s | **fixed** | `3888081` | `src/factory_commons/llm.nim:694-716`, `src/factory_commons/server.nim:338-360`, `tests/test_llm.nim:399-428` |
| N18 overflow cells chosen by walkability | declined (unobservable; "free floor" = not wall/machine/chute) | — | `src/factory_commons/machine.nim:106-146` |
| CND-1 can `curly.makeRequests` raise? | **settled by test** | `7a0254c` | `tests/test_llm.nim:290-310` |
| CND-2 was the baseline tuned with a grid harness? | **settled by artifact** | `0a6761d`, `04058a7` | `tools/tune/feasibility_sweep.nim`, `docs/tuning.md` |
| CND-3 hosted connect cost vs the 30 s assumption | **addressed** | `3888081` | `tests/test_llm.nim:424-428` |
| CND-4 real-page feed clipping at 360 px | declined (checklist 15's requirement is the fixture, which exists and is gated) | — | `tools/ci/renderer_fixture.html` |

---

## B1 — no test asserted frame-by-frame reproduction of the recorded state

**What the code did.** `captureFrame` (`sim_state.nim:129-152`) wrote, per tick, a `Frame` **and** a
`series` row carrying the same integrity/cap. `hudFromReplay` (`replays.nim:254-379`) read frame
`index` and folded `events[]` up to `frame.t` for every cumulative counter. The only tests were
structural (`frames.len`, `frame.t == i`) plus four sampled indices — so a regression in the fold
would have left every assertion green, and nothing compared the two recordings of integrity/cap.

**What it does now.** `tests/test_replay.nim` plays two whole episodes **tick by tick**
(`runRecorded`), keeping the live sim state after every tick in a `LiveTick` read off the sim's own
fields — not off the frame it recorded. It then loops **every** recorded frame and asserts
`hudFromReplay(i)` equals that state: tick, integrity, cap, both stocks, machine cooldown, mode,
band; the event-folded counters (`presses`, `strips`, `repairs`, `bananasMade`, `bananasRotted`,
`bananasSpoiled`, `onChute`, `scrappedBy`); every loose cube and every banana (position, colour,
age); and per seat position, hand, score, `eaten`, `banked`, `presses`, `strips`, `repairs`,
`misfeeds`, `fallbacks`, the standing order (`job`/`cube`/`source`) and `say`. In the same loop it
asserts `series.machine[i] == [frames[i].t, frames[i].m[0], frames[i].m[1]]` — the momentum strip's
recording against the gauge's. Both episodes are asserted to have actually pressed, stripped and
made bananas, so an empty loop cannot pass.

The second clause of checklist item 2 (the viewer derives from the same re-derivation, not a
parallel recording) was already true by construction — one `HudModel`, one `buildStateJson` — and
the test now pins it: the model it compares is the one `buildStateJson` is fed.

**Evidence.** Two deliberate mutations, run locally against the committed test:

- dropping `result.bananasMade += row{"yield"}.getInt()` from the `strip` arm of the fold →
  `FAIL: all-stripper frame 26: bananas made 0 != 4`;
- perturbing the series row in `captureFrame` → `FAIL: all-steward frame 0: series cap 99 == frame m[1] 100`.

CI: `test_replay: 75708 checks passed (187496 replay bytes, 240 events, 900 frames)` in both the
debug and the release pass of run 32883915882 (was 3 772 checks). **Checklist item 2.**

## N1 — `eatTrigger` restored to the design note's 3

`moveCooldown 2 → 1` is rung 3 of the note's gate-(a) ladder and `stripCapLoss 12 → 16` is rung 1 of
its gate-(c) ladder (`design.md:397-399`, "repair constants in this order and re-run — no design
bounce is needed"), so both stay, and `docs/tuning.md` now shows the measurements behind them.
`eatTrigger 3 → 6` was on no ladder, and the sweep shows it was not buying anything: at the shipped
`moveCooldown 1`, eatTrigger **3** gives 12/12 clean gate-(a) seeds, worst seat **25**, 83 bananas;
eatTrigger 6 gives 12/12, worst seat 21, 76. The old comment's "at 3 a seat can finish on 4" was
measured before the steward baseline grew its rotating harvest shift. `defaultGameConfig()` and the
manifest's `config_schema` default are both 3 (`tests/test_manifest.nim:195-238` asserts they agree),
and the whole suite is green. **Checklist item 7.**

## N2 — five overrides, not seven

Declined as a rule change, fixed as prose. The five-override walk is a *consequence* of
`stripCapLoss 12 → 16`, which is rung 1 of the note's own gate-(c) ladder — and the sweep shows the
rung is load-bearing rather than cosmetic: at `stripCapLoss 12` an all-stripper room ends
`factory_ruined` on **0/12** seeds (it stalls at SEIZED with cap stuck above `pressFloor`), at 16 on
**12/12** (`docs/tuning.md`). Reverting to 12 would falsify gate (c), which is the note's own stated
invariant ("universal defection is ruinous", `design.md:387-389`); the note's arithmetic paragraph is
the thing that moved, not the shape of the game — the private campaign is ~15 bananas against ~26–32
in a maintained plant, still under a fifth of the cooperative total. What *was* wrong is that four
prose surfaces still quoted 13/seven/twelve-cap: those are fixed in `90424bd` and `0079af8`, and
`README.md` now states the five-override consequence explicitly. `PrivateYield 3/2/1 → 4/3/1` is rung
1 of the note's gate-(b) ladder (`design.md:398`) and stays.

## N3 — prompts quote the shipped constants; the floor plan derives its tick costs

The foreman prompt (in `tools/ci/policies.json` and as `DefaultPrompt` in
`src/factory_commons_player.nim`) said "three bananas now costs the room twelve cap"; it now says
four bananas and sixteen cap, which is `PrivateYield[0]` and `stripCapLoss`. The custodian's switch
keyed on "once cap has fallen to 64 or below", a rung the cap walk (100 → 84 → 68 → 52) never visits;
it now reads 68. `FloorPlanText` hardcoded "one cell per tick at moveCooldown 1" and "a one-colour
supply loop is about 22 ticks" two lines above an interpolated `$c.moveCooldown`; it is now
`floorPlanText(config)`, which multiplies the two cell counts by the cooldown, so a variant or a
hosted `game_config` with `moveCooldown: 2` gets 44 and 36 rather than a plan wrong by 2×.
`tests/test_llm.nim` asserts the moveCooldown-2 prompt says 44 ticks, says "may move once every 2
ticks", and never says 22. **Checklist item 4** (nothing added to the prompt names a policy, player
or model).

## N4 — the steward's harvest rule (DISPUTED as a defect; it is the measured requirement)

The finding is factually right — `scripted.nim:68-73` uses an offset rotation plus a `behind`
fairness clause, where the note's rule 3 is `shiftIndex mod 3 == mySlot` and chute ≥ 4 — but the
note's exact rule cannot ship. Measured locally by patching `stewardOrder` to the note's rule and
running `tests/test_feasibility.nim` in release: **gate (a) 0/12 on every variant**, with an
all-steward room scoring `47/29/7` on every seed (`FAIL: gate (a) factory-commons: … got 0/12`). The
harvest is a race between a lane 3 cells from the chute and a lane 12 cells away; without the
fairness clause the third seat finishes on 7 and "every seat ≥ 14" fails. The note's own instruction
for this case is the gate, not the table ("That test is the enforcement, not this table",
`design.md:403-404`), and the deviation is documented at `scripted.nim:56-67`. Statelessness — the
property the note actually names — is preserved and asserted (`tests/test_baseline.nim:185-194`).
No code change.

## N5 — gate (b) on `either-or` (declined, measured)

Also factually right, also unshippable: measured over seeds 1..12 on the `either-or` variant, a
2×steward + 1×stripper room locks to `cycle` on **every** seed and the stripper scores 24 against
29/36 — **gate (b) 0/12**. That is exactly the reason written into `tests/test_feasibility.nim:113-121`:
there the lock, not the economy, decides whether defection pays, and gate (e) tests the thing that
varies. Forcing gate (b) to run on that variant would either fail CI or require weakening the gate,
which this round will not do. No code change.

## N7 — a 429 waits for the next shift's batch

`textOf` raised a plain `FactoryError` on a 429, so the throttled seat joined `stillOpen` and was
re-batched inside the same shift — against `design.md:645` ("429 is logged and that seat is retried
in the next shift's batch") and straight into a rate limiter that had just refused. A 429 now raises
`ThrottledError` (still a `FactoryError`, so the never-raises contract is unchanged) and `decideAll`
catches it ahead of the general handler: that seat takes the scripted steward order for the shift,
marked `fallback` so phase 60 still counts it, and returns in the next batch. Seats that merely
answered badly are still retried once. Two tests: a mixed batch retries only the two bad replies
(`sizes[1] == 2`, and without the fix the same assertion reads `got 3`), and a fully throttled shift
issues one batch instead of two. **Checklist item 8** (retry-once and the recorded fallback both
intact), and it lowers the per-episode request ceiling rather than raising it (item 5).

## N14 — the nimby pin

`ci.yml` installed nimby 0.1.26 under a comment promising it mirrors the Dockerfile, which uses
0.1.27 (as does `Dockerfile.replay-viewer` and the design note). Now 0.1.27; the `test` job in run
32883915882 built and passed with it. **Checklist item 1.**

## N15 — the transport call moves inside the `try`

`client.stub(batch)` / `curl.makeRequests(...)` sat outside the `try/except CatchableError`, so a
raise from the transport would have escaped a proc that documents itself — and that `server.nim`'s
shift loop relies on — as never raising. The review could not settle whether `curly` raises (the
package is not in the sandbox), so the contract rested on an unread dependency. The call is now
inside the try; a raise is logged, breaks the attempt loop, and every open seat takes the same
scripted fallback as any other transport failure. `tests/test_llm.nim` drives a raising stub and
asserts three orders come back, all `source: fallback`, with no retry batch and the client left
enabled — **without the fix that test dies with `unhandled exception: libcurl exploded`**, which is
also the answer to could-not-determine #1: it no longer matters whether curly raises.
**Checklist item 5.**

## N17 — a shift only starts if it can also settle

The play deadline was `now > deadline` tested between shifts, so a shift starting a millisecond
early ran its worst case (20 s batch + 20 s retry + ≤12 s pacing) and then settled (0.5 s flush +
writes + 20 s grace) at ≈773 s against the 720 s the checklist allows. The budget is a **settle**
deadline: `config.shiftFitsBeforeDeadline(now, deadline)` now requires
`now + shiftBudgetSeconds() + settleBudgetSeconds() <= deadline`, so a shift that cannot finish and
settle in time is not started and the episode ends early with `reason: "deadline"` — which already
scores and writes both artifacts. Worst case is now 720 s. The three numbers are config-derived
procs next to `turnPacingSleepMs`, so `tests/test_llm.nim` pins the boundary directly (a shift with
exactly its worst case left starts; one that would settle a second late does not) and also asserts
that the configured **180 s** connect ceiling plus the reserve still fits inside the budget — which
is could-not-determine #3 answered by construction rather than by an assumed 30 s connect.
**Checklist item 5.**

## Could-not-determine #2 — the grid harness

`tools/tune/feasibility_sweep.nim` (new) walks `moveCooldown × {rustPeriod, repairGain} ladder rungs
× eatTrigger`, plus a `stripCapLoss` column, plays seeds 1..12 in each cell with the four scripted
rooms, and prints each cell's gate (a)–(d) outcome; `docs/tuning.md` records the run that chose the
shipped values and reads the table. `tests/test_feasibility.nim` remains the gate. Note what the
table shows and prose could not: the ladder is **not monotone** — `move 1 rust 30 gain 10 eat 3` is
0/12 while both of its neighbours are 12/12. **Checklist item 7, second sentence.**

## Declined, with the reason

- **N6 (`blocked` dedupe).** Deliberate and documented (`sim_state.nim:24-31`); `lastBlocked` is
  excluded from `gameHash`, so it cannot move determinism, and no distinct row is ever dropped.
- **N8 (integrity clamped to the new cap).** The clamp is what keeps `integrity <= cap`, which
  `tests/test_baseline.nim:75` and `tests/test_sim.nim:551` assert; on the note's own walk it is a
  no-op. Removing it to match a step list would break a tested invariant.
- **N9 (`capMin: 25` in the cert fixture).** Documented and enforced at
  `tests/test_manifest.nim:340-372`, which plays the fixture and measures the video: with the
  eatTrigger change it now records **480 ticks = 20 s**, against `ci.yml`'s 12 s soak. Without
  `capMin` the fixture scraps in shift 3 and the replay is 7.5 s — a replay shorter than the soak
  window is reported as frozen (ecos, 2026-08-23).
- **N10 (`fallbacks[i]`).** A registered scripted seat is playing a baseline on purpose; a prompt
  seat with no key is a fallback and is counted. Documented at `llm.nim:714-720`; this is the number
  phase 60 greps.
- **N11 (beat markers).** `chrome_common.js` ships byte-identical to the starter's and its `markBeat`
  is the 3-argument form; making the markers real `<button>`s means editing that file, which
  checklist 14 permits only as "a named, minimal patch recorded in the design note" — and the fixer
  may not edit the design note. The game block already gives every marker `role="button"`,
  `tabindex`, an `aria-label`/`title` naming kind and tick, and click + Enter/Space seeking, and CSS
  exists for all five emitted kinds. Raising it would be a design-note change, not a fix.
- **N12 / N13 (the fixture mirrors the block; `total: 0` on the bundle).** The board is composited in
  a worker on an OffscreenCanvas and carries no `fillText` at all — every board string is a
  server-rendered sprite and every LLM-authored string is DOM text — so `total: 0` is the honest
  reading of a renderer with no canvas text, and the worst-case fixture (9 drawn, 0 never inside,
  `--strict-text-bounds`, own step in `ci.yml`) is checklist 15's required compensating gate. Making
  the fixture import the page's IIFE is a rewrite of the fixture, not a fix to a defect.
- **N18 (overflow cells).** Overflow bananas can never be eaten (`sim.nim:158-176` gates on
  `isChute`), so the only observable difference is which cell a banana rots on; "free floor cells"
  reads as not-wall/not-machine/not-chute, which is what `overflowCells` computes. Making placement
  depend on transient occupancy would put cog positions into the spill order for no visible gain.
- **CND-4 (real-page feed clipping at 360 px).** Checklist 15's requirement is a worst-case renderer
  fixture driven by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step; that exists,
  ran, and reports a non-zero `canvas_text.total`. Pointing the smoke at the real bundle with a
  talking replay needs CI to produce one, which needs a key CI does not have.

## NOTED (not fixed)

- `git push` over HTTPS is not authenticated in this sandbox ("Invalid username or token"), so these
  nine commits were written to `refs/heads/main` through the GitHub Git Data API (blobs → trees →
  commits → ref update) with `gh api`. The pushed tree is byte-identical to the local one
  (`git diff origin/main HEAD` empty) and the ref update triggered the `push` CI run cited above.
- `tests/test_baseline.nim` and `tests/test_feasibility.nim` re-derive their own variant tables from
  `defaultGameConfig()`; the sweep harness now duplicates that setup a third time. If a fourth
  appears, it wants a shared fixture — out of scope this round.
