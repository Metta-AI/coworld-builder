# r1 fixes — garble

Repo: `Metta-AI/cogame-garble`, branch `main`.
Head: local `e414ea1` = remote **`de841a155af848bbe5c470f59ad44e6434476f8b`**
(the local tree is byte-identical to remote `main`: `git diff HEAD origin/main --stat` is empty).
CI: <https://github.com/Metta-AI/cogame-garble/actions/runs/32706190772> (id **32706190772**,
`push`, head `de841a15`) — **conclusion: `success`**; jobs `test` ✓, `docker-smoke` ✓,
`wasm-viewer` ✓. `SEAT-COUNT FAIL` appears **0 times** in the log; the viewer smoke printed
`{"loaded":true,"ms":281,…,"feed_lines":221}`, `soak: 10s of playback kept advancing` and three
differing scrub readouts; `smoke OK: seats=5 results=438B replay=14090B reason=complete` and
`every player container exited 0`. 172 `[OK]` lines across the six test runs (three files ×
debug/`-d:release`); no test was deleted, skipped, weakened or loosened — every test change in
these commits **adds** assertions (F6, F7, F8, F9, F10, F20).

Commits are one per finding, in finding order. Remote shas are re-authored by the Git Data API
push helper, so both are given.

| finding | disposition | local sha | remote sha | files |
|---|---|---|---|---|
| F1 | fixed (note amended, per coordinator ruling) | `1dee5f4` | `add8fcd7` | `docs/plans/2026-08-24-garble-design.md:900,1002-1006,1091-1102` |
| F2 | fixed | `f61dd77` | `7b37a6a7` | `coworld_manifest_template.json:287` |
| F3 | fixed (note corrected; code was right) | `1ed0e79` | `29f732c1` | `docs/plans/…-design.md:95-96` |
| F4 | fixed (note corrected; code was right) | `b05d931` | `6c482e8a` | `docs/plans/…-design.md:99-103` |
| F5 | fixed (note corrected; code was right) | `7e67b22` | `07193c41` | `docs/plans/…-design.md:151,155-157,718` |
| F6 | fixed | `74c68e2` | `8958586e` | `src/garble/sim.nim:438-443`, `tests/test_sim.nim:140-158` |
| F7 | fixed | `f25d8ca` | `6b4fc5ae` | `src/garble/sim.nim:398-411`, `tests/test_sim.nim:117-138` |
| F8 | fixed | `abf91a4` | `35f42ae7` | `src/garble/sim.nim:912-935,996-1011`, `tests/test_sim.nim:603-632` |
| F9 | fixed | `8edde07` | `c0536900` | `src/garble/sim.nim:959-981`, `tests/test_sim.nim:634-677` |
| F10 | fixed | `aa29cb6` | `da35af01` | `src/garble/server.nim:205-215,600-615`, `replay-viewer/garble_replay.nim:38-54`, `tests/test_sim.nim:679-698` |
| F11 | fixed | `c632c77` | `e81db51e` | `src/garble/llm.nim:709-717` |
| F12 | fixed | `f9681d4` | `26a276df` | `client/renderer.js:113-135` |
| F13 | fixed | `4eb9646` | `c03e77c7` | `client/renderer.js:156-172` |
| F14 | fixed | `39f65c3` | `1b167264` | `client/renderer.js:1149-1290,1222-1259,1487-1495` |
| F15 | fixed | `b29ca50` | `f6e26415` | `client/renderer.js:909-930,944-945,989` |
| F16 | fixed (note amended) | `a05de6d` | `f2497625` | `docs/plans/…-design.md:923-926` |
| F17 | fixed | `d24ae5f` | `8dd18c15` | `scripts/tune_baselines.nim` (new), `docs/tuning/baseline-grid.md` (new), `src/garble/llm.nim:156-170,188-205,249-253`, `docs/plans/…-design.md:582-591`, `README.md:90-91` |
| F18 | fixed (note corrected with measurements) | `3b18e54` | `4fede6d5` | `docs/plans/…-design.md:521-531`, `src/garble/llm.nim:349-354` |
| F19 | **REFUTED** | — | — | `src/garble/server.nim:352-358` |
| F20 | fixed | `ef352e2` | `ac7e7d11` | `tests/test_sim.nim:329,414-435,590-601` |
| F21 | fixed | `e414ea1` | `de841a15` | `src/garble/server.nim:278,417-437` |

Acceptance-checklist item satisfied is named per finding below. Findings that are observations of a
mismatch between the note and correct code are recorded as *note corrected* — the code was not
changed and the reason is given.

**Design-note mirroring:** F1, F3, F4, F5, F16, F17 and F18 amend the repo's copy
(`docs/plans/2026-08-24-garble-design.md`). Per the coordinator's instruction I did **not** touch
`runs/2026-08-24-garble/design.md`; those seven edits need mirroring so the two copies match again.

---

## F1 — the cog sprites are generated art, not the starter's soldier sprites

Coordinator ruling: the nano-banana cogs stay; the playbook (`make-coworld.md` §Phase 0 "Real art,
not placeholders", `art-nanobanana.md`) is binding over the note's violet-tint plan. So the fix is
to the note's copy in the repo, not to the art. §*The stage* now describes the five generated
128×128 `data/cog_*_front.png` sprites and states there is **no tint path**; §*Packaging* records
`data/` as babel's floor/font/licence plus the five cogs (and that the four `soldier_*` sprites are
not shipped because nothing references them), adds a `scripts/art/` entry naming
`gen_cog_sheet.py` and `split_cog_sheet.py`, and marks the deviation as accepted on 2026-08-24.
The same commit corrects "the six `data/` assets" the replay-viewer hook copies to **seven** —
`tools/build_replay_viewer.sh:57-59` copies five cogs, `arena_floor.png` and `font.ttf`.
Evidence: `grep -rn soldier` over the tree returns only the new note sentence; the bundle built in
CI (`wasm-viewer`, "Assert the bundle is complete") lists the seven assets.
Checklist: no item (art provenance is playbook, not checklist), but it removes a note-vs-tree
contradiction that item 1's reviewers would otherwise re-file.

## F2 — `game.docs.readme` was a bare string

`coworld_manifest_template.json:287` is now
`"readme": { "type": "text", "value": "Five cogs sit on one exchange …" }`, matching the two
`pages` entries and all three talk-lineage starters. The file still parses
(`python3 -c "import json; json.load(...)"`) and the only changed line is the readme.
**Checklist item 10** (`game.docs` shape; category `manifest`).

## F3 — `premium` / `quota` draw literals

Not a code defect: Nim's `rand(max)` is inclusive, so `sim.nim:188,190` (`6 + rng.rand(3)`,
`12 + rng.rand(7)`) produce exactly the 6…9 and 12…19 ranges the note states in the same sentence
and `tests/test_sim.nim:37-38` asserts. The note's expressions (`rand(4)`, `rand(8)`) would give
6…10 and 12…20 and contradict its own ranges, so the note's literals are corrected to the code's.
Changing the code instead would have widened the ranges and broken the note and the test together.
Checklist: none directly; keeps item 1's "note vs tree" reading clean.

## F4 — two RNG streams, not one

Not a code defect. The aliases must be drawn before a `Sim` exists (`tableNames(players, seed)` is
called in `initSim`'s constructor line and is public for the server), so they come from their own
seeded stream `initRand(seed*6779+31)` (`sim.nim:118`) — babel's shape, commented at
`sim.nim:159-162` — and everything else from `initRand(seed*7919+17)` in the note's order minus the
aliases. The invariant the note is actually asserting, "`seed` alone reproduces all of it", holds
and is pinned by `tests/test_sim.nim:48-55` (same seed reproduces prices, interference, names,
sur/dem; different seed differs). The note now describes the two seeded streams accurately.

## F5 — the published `curve` carries `noiseScale`

Not a code defect. `sim.nim:201` publishes `clamp(base * noiseScale, 0.05, 0.95)`, which is the
only reading that makes the forecast usable: the published curve must be on the same scale as the
meter it predicts (`interference[t]` differs from it only by the burst, `sim.nim:202-203`), and it
is what the note's own "derivable from `seed` + `turns` + `noiseScale`" means — an unscaled curve
would not depend on `noiseScale` at all. The note's pseudocode now includes the `curve[t]` line and
§*tableStateJson* says the published base is on the `noiseScale` scale.

## F6 — an empty transmission at a zero meter was not flagged `silent`

`sim.nim` was `silent = line.len > 0`, so a seat with an empty meter that said nothing recorded
`silent = false`. design.md:270-272 makes the flag a property of the **meter** ("If
`airtime[s] == 0`, the transmission is dropped entirely and the event is flagged `silent`"), so it
is now `silent = true` whenever `airtime[seat] <= 0`. That also makes the flag **re-derivable**,
which F9 depends on: a recorded silent say carries `text = ""`, and the replayed seat has the same
empty meter. Evidence: `tests/test_sim.nim` "an empty meter silences the seat and opens no ticket"
now also asserts a full-meter empty say is *not* silent and a zero-meter empty say *is*.
**Checklist item 2** (the recorded flag now re-derives).

## F7 — sim-side truncation carried no `…` marker

design.md:541-543: "Every truncation is on rune boundaries (`runeSubStr`, with `…` marking the
cut)". `llm.nim`'s `cleanText` marked it; `sim.nim`'s `clipRunes` — the 160-rune text cap, the
airtime clip and the 400-rune notes cap — did not. `clipRunes` now returns
`runeSubStr(0, limit - 1) & "…"`, i.e. the marker is taken **out of** the limit, so a clipped string
is still exactly `limit` runes and an airtime clip still fits the meter (`cost == airtime`,
`airtimeLeft == 0`). Evidence: the two airtime tests now assert `event.text.endsWith("…")` on top of
the existing `runeLen` and `validateUtf8() == -1` checks; CI's strict-UTF-8 replay parse
(`SMOKE_REQUIRE_REPLAY_JSON=1`) passed. **Checklist item 9.**

## F8 — `sameEvent` covered a subset, and any string was a legal ending

Two changes at `sim.nim`. (a) `sameEvent` now compares **every** field `eventToJson` writes for a
derived event: the previous list plus the `turn` event's `airtime`, the `deal` event's `cash`, and
the `end` event's `text` and `scores` (floats within `1e-9` via `sameFloats`). (b) the `evEnd`
branch rejects a reason outside `{complete, deadline}` (`LegalReasons`) *before* settling, and then
checks the recorded end event against the re-derived one with `sameEvent` — previously it ran no
comparison at all, so a replay that stopped short could name any ending and carry invented scores
and portfolios and the viewer would draw them. Evidence: new test "a tampered turn airtime, end
score or ending reason raises" tampers the turn `airtime`, the end `scores`, the end `portfolios`
and the ending reason; all four raise `GarbleError`. **Checklist item 2.**

## F9 — a replayed `silent` say re-derived with `silent = false`

The say branch compared only `ticket`, `cost` and `hasTerms`. It now compares `text`, `notes`,
`channel`, `silent`, `cost`, `airtimeLeft`, `ticket`, `hasTerms` and every scanned term field
(`side`, `qty`, `commodity`, `price`, `kQty`, `kCom`, `kPrice`) against the re-derivation. One
field, `clipped`, is **not** re-derivable — the replay is handed the already-clipped text, so the
clip never fires a second time — and is checked for consistency instead: a clipped transmission is
exactly the one that spent its meter to the last rune (`cost > 0 and airtimeLeft == 0`), and a
derived clip on replay is itself a mismatch. This is stated in the code comment rather than papered
over. Evidence: new test drives seat 0's meter to empty over 8 turns (turn 5 clips, 6-7 are
silent), replays the honest log, then tampers the `silent` flag, a scanned term and the `clipped`
flag — each raises. End-to-end: a real 8-turn episode from the compiled binary
(`COGAME_SAVE_REPLAY_URI=file:…`) was re-read through `eventFromJson` + `replayMatch` with the
viewer's alias-built config and produced 65 frames for 64 events with no raise. **Checklist item 2.**

## F10 — the endcard read the recorded `results` block

`renderer.js:1393` draws the endcard from `payload.results`, which both payload builders copied
verbatim out of the replay file while every other readout reads the `replayMatch` frames. Both
builders now emit the results of the **last re-derived frame**: `server.nim`'s `statesFromEvents`
becomes `derivedFrames`, returning `(states, results)` from one `replayMatch` pass, and
`replay-viewer/garble_replay.nim` does the same. The renderer is unchanged — it now receives a
re-derived block. Evidence: new test "the endcard's results are the re-derived ones, field for
field" rebuilds the config from the replay's **aliases** exactly as the viewer does and asserts the
re-derived results equal the recorded ones on every key but `names` (results are platform-facing and
record POLICY names; the endcard maps by seat index through `nameMap` regardless). Confirmed
against a real episode too: the replay-mode server's `/replay` payload carried
`results.scores == [1.062, 1.133, 1.071, 1.167, 1.078]`, identical to the recorded block, with
`names` the aliases. **Checklist item 2** ("the viewer derives its display from that same
re-derivation — not from a parallel recording").

## F11 — the retry gate's probe could not reject anything

`llm.nim:700-705` copied the whole `Sim` per open seat per attempt and re-applied the parsed say to
the copy, claiming to "reject illegal replies here". `applySay` raises only on `done`,
`phase != phWire`, a bad seat index or a repeat say (`sim.nim:416-424`); the snapshot is taken
immediately after `beginTurn` (`server.nim:338-344`), so none of those is reachable, and
`parseDecision` has already capped `text`/`notes`/`channel` and bounded the seat. The probe is
removed and the comment now names the real gate (`parseDecision`, which is exactly the note's
definition of ill-formed at design.md:257-261) and keeps the "an inadmissible confirm is not
ill-formed" statement. Behaviour is unchanged; a per-seat `Sim` copy per turn is not.
**Checklist item 8** (the described parse/retry/fallback path is now what the code does).

## F12 — the live interference column was missing below 560 px

`drawMeter` wrapped both the sparkline and the live amber column in `!layout.compact`. Only the
sparkline is wide-only now; the column draws at every width, so the compact meter is "the live
column plus the band word" as design.md:1045-1046 says. At 360 px the plot is 304 px wide, well
past the `plot.w > 40` guard. **Checklist item 11** (360 px legibility).

## F13 — the burst wash did not drive `#grain`

design.md:969-971 and :917 make `#grain` part of the burst. `drawBurstWash` now calls `driveGrain`,
which sets `#grain`'s **inline** opacity to `0.10` (double the inherited `0.05`) for the wash's
~700 ms and clears the inline value afterwards, so the element returns to the stylesheet's rule and
`client/chrome.css` stays byte-identical to babel's — the CI provenance step re-checked that and
printed "chrome.css is the starter's, plus one appended block". **Checklist item 14** (chrome not
edited).

## F14 — audio: gain floor, per-word crackle, seek cancellation

Three parts of design.md:996-1007 were missing. `level()` mapped `interference * 0.19`, which is
0.038 at a CLEAR 0.20 meter; it now ramps from **0 at 0.25** (the CLEAR ceiling) to **0.18 at 0.75**
(STORM) and clamps. `makeStatic` gained `crackle(count)` — short bandpassed pops through the same
seeded buffer and master bus, one per garbled word, capped at six per transmission and spaced 90 ms
— and `cancel()`, which stops and disconnects every still-scheduled node. Both drivers fire
`crackle(garbledIn(...))` as a transmission lands; the replay driver calls `cancel()` on **every**
seek, and `stop()` cancels too. Every new call is inside the existing `try/catch` and behind the
`♪ STATIC` button, so audio still never gates `data-replay-loaded` and never touches the render
loop — the headless smoke, which never clicks the button, reported `loaded: true` in 281 ms and a
clean 10 s soak. **Checklist item 13** (the viewer still executes).

## F15 — the feed's closing lines omitted the leader and the turn cap

`endText(event, nameMap, maxTurns)` replaces the two hard-coded strings: a completed episode reads
`FINAL — Sprocket 1.42× (312 cr) · 12 turns played.` (leader, ratio and credits come off the end
event's own `scores`/`portfolios`), a deadline ending reads
`Episode deadline — scored on 7 of 12 turns.` The cap is the one value the events do not carry, so
it is threaded into `renderFeed` from `payload.config.turns` (replay) or the live state's `turns`;
`renderFeed`'s extra parameter is optional and it has no external callers. Matches design.md:1029.

## F16 — one rename beyond the note's three

The `#clock` placeholder `ROUND 0` → `TURN 0` in the three client pages and the viewer shell is a
real, deliberate fourth rename (Garble counts turns; the renderer overwrites the text on the first
drawn frame). Recorded in the note's list of admissible renames so the page-provenance diff is
exact. **Checklist item 14** (provenance of the inherited page).

## F17 — no grid-tuning harness in the tree

Checklist item 7's second sentence had no artefact to point at. The baselines' five tunables move
into `BaselineParams` with `DefaultBaseline` **exactly** the shipped constants (floor 30, loud 0.50,
sell +3, buy +1, lot 5), so no behaviour changes — `scriptedAction`'s new parameter defaults to it
and every existing call site is untouched. `scripts/tune_baselines.nim` sweeps the 576-point grid
around them over 60 seeds × four tables (all-quoter, shark-heavy, quiet, storm) — 138 240 twelve-turn
episodes, 105 s under `-d:release` — gating on the four properties the note asks of the baselines
and ranking candidates by the mean quoter score. `docs/tuning/baseline-grid.md` records the run: the
top of the ranking, the shipped row (rank 218/576, mean 1.1985 vs the argmax 1.2314, but 9 median
deals vs 7 and the strongest quiet-vs-storm signal of the high-scoring lots), and a per-parameter
curve for each of the five knobs — including the finding that `airtimeFloor` is **inert** over this
grid because a baseline's 16–26-rune offers never approach the 900-rune meter. The note and README
point at the harness. **Checklist item 7.** The shipped values are the ones the note fixes
(§*Scripted baselines* states each of them), so the harness justifies them rather than replacing
them; moving them would be a design change, not a fix.

## F18 — the prompt runs larger than the note's estimate

Measured here over 20 seeds of a full scripted table: peak user prompt **5 436 runes at 12 turns**,
7 084 at 18, 8 057 at the 24-turn cap, against a constant **3 059-rune** system prompt. The note and
`heardBlock`'s doc comment both claimed "roughly 3 000 runes on a twelve-turn episode"; both now
carry the measured figures and name the reason — the heard window is the only *windowed* block,
while the public tape and the confirmable-ticket block print in full. No code change: ~3 000 tokens
at the 24-turn cap is one ordinary request, and the windowing itself (`llm.nim:354`) is correct.

## F19 — the inter-batch spacing floor is paid even with no LLM call — **REFUTED**

The reviewer's own text concedes it: "the code follows the rule as written". design.md:394-396
states the floor as `max(minTurnSpacingMs, callsIssuedLastTurn * 2400 ms)` **unconditionally**, and
`server.nim:352-358` is that expression. No bound is exceeded either:

- certification/`docker-smoke` sets `minTurnSpacingMs: 0` (`coworld_manifest_template.json:492`) —
  the CI episode ran 8 turns in ~1 s of play (log 08:26:12→08:26:13);
- the worst hosted case is `long-session`, 18 turns × (12 000 ms + 400 ms) ≈ **223 s**, against a
  720 s play budget (`PlayBudgetFraction = 0.6` of the 1200 s default), and `sampleEpisode` caps
  turns at 24 → 298 s worst case at any variant;
- the deadline check runs *before* each turn opens (`server.nim:331-336`), so even an unexpected
  wait ends the episode scored rather than killed.

Making the floor conditional on `callsIssued > 0` would also remove the spectator pacing the note
gives it and would diverge from the stated rule. No change. **Checklist item 5** holds as written.

## F20 — three assertions from the note's test list were missing

- design.md:1272 "over 500 random confirm sequences": the non-negativity test ran 20 seeded
  episodes; it now runs **500** (still ~0.2 s under `-d:release`).
- design.md:1281 "selling its demand commodity below price lowers it": new scoring test endows
  seat 1 with 10 units of its contract commodity — in `startUnits` too, so `hold` prices them in and
  the pre-trade score is exactly 1.0 — then sells five at 1 credit and asserts `score(1) < 1.0`.
- design.md:1292 "a tampered `turn` event (interference **or** a price changed) raises": the tamper
  test only mutated `prices[0]`; it now also mutates `interference` in its own block.

No assertion was removed or weakened. **Checklist item 1** (the test suite matches the note's list).

## F21 — the game thread had no top-level guard

The episode loop moves into `playEpisode` and `runGame` becomes a wrapper: on any `CatchableError`
it logs, settles what was played (`endEarly` + a final broadcast) and writes the artifacts, quitting
non-zero only if even that fails. Previously an escaping exception anywhere outside the two
`applySay`/`applyConfirm` guards would kill the thread while the HTTP thread kept answering
`/healthz`, and the platform would kill the container with **nothing** written. No reachable raise
is known (the reviewer found none and neither did I) — this is the guard that makes the unknown one
survivable, and it is 20 lines with no effect on the happy path. Evidence: a full offline episode
run from the compiled binary still exits 0 having written `results.json` (437 B) and
`replay.json` (13 900 B); CI's `docker-smoke` printed
`smoke OK: seats=5 results=438B replay=14090B reason=complete`. **Checklist item 5**
(degrade-never-hang: the container can no longer look alive while writing nothing).

---

## NOTED (not fixed)

- `client/renderer.js:901` `lastTurn` in `renderFeed` is assigned and never read (inherited shape).
  Out of scope for this round.
- `tools/ci/viewer_smoke.mjs`'s soak line prints `(null -> null -> null)` because Garble has no
  `tick` readout; the harness passes on the clock, which moves. Template file, byte-verbatim — left
  alone.
- `scripts/tune_baselines.nim` is not compiled by CI (it lives outside `tests/`). It compiles and
  runs clean locally under `-d:release`; if the fleet wants it gated, a one-line `nim check` step
  in `ci.yml`'s `test` job would do it.
