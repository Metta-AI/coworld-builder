# r1 fixes — 2026-08-24-cogplomacy

Repo: `Metta-AI/cogame-cogplomacy`
Head: `9711b80ccc28aa711872ca007b7d0ccba0134279` (main, was `1b9ddad`)
CI: https://github.com/Metta-AI/cogame-cogplomacy/actions/runs/32728438824 — **success**
(`test` success, `docker-smoke` success, `wasm-viewer` success; `grep -c "SEAT-COUNT FAIL"`
over the whole run log = **0**).

The review had **0 blocking** and 14 non-blocking findings. All 14 were worked; 13 produced a
commit, one (N14b) is recorded as no-change with evidence. One commit per finding, in finding
order, nothing else folded in.

| finding | disposition | commit | files |
|---|---|---|---|
| N1 expander never builds a fleet | fixed | `35b766d` | `src/cogplomacy/llm.nim:375-410`, `tests/test_bot.nim` |
| N2 support rule fires only at rank (d) | fixed | `96df449` | `src/cogplomacy/llm.nim:219-310`, `tests/test_bot.nim` |
| N3 illegal order does not consume its slot | fixed | `9f0fe87` | `src/cogplomacy/orders.nim:150-347`, `src/cogplomacy/sim.nim:605-625`, `tests/test_sim.nim` |
| N4 `replayMatch` checks too little | fixed | `ff2f6da` | `src/cogplomacy/sim.nim:1250-1320`, `tests/test_sim.nim` |
| N5 5 s prompt grace, late prompt takes over | fixed | `abae9fe` | `src/cogplomacy/server.nim:288-300, 520-535` |
| N6 feed prints raw notation / unnamed provinces | fixed | `20b9d10` | `client/renderer.js:1425-1600`, `scripts/art/build_map1901.py`, `data/map1901.json`, `tests/test_viewer.nim` |
| N7 retreat into a dislodged unit's province | fixed | `a14365c` | `src/cogplomacy/orders.nim:465-510, 554`, `src/cogplomacy/sim.nim:712`, `src/cogplomacy/llm.nim:333, 553`, `tests/test_adjudicate.nim` |
| N8 a letter to `ALL` is dropped | fixed | `b7fa634` | `src/cogplomacy/llm.nim:650-665`, `src/cogplomacy/sim.nim:411-432`, `client/renderer.js:1508-1525`, `tests/test_sim.nim`, `tests/test_bot.nim` |
| N9 `docker_smoke.sh` asserts less than §CI jobs | fixed (new CI step, template untouched) | `8c1ed92` | `.github/workflows/ci.yml`, `tools/ci/assert_smoke_artifacts.py` |
| N10 byte-sliced error text | fixed | `d871fb6` | `src/cogplomacy/llm.nim:616-625, 755-785`, `tests/test_bot.nim` |
| N11 non-positive timeout ⇒ no play deadline | fixed | `555c5e7` | `src/cogplomacy/server.nim:322-336, 346` |
| N12 two event kinds not required by the test | fixed | `ac58396` | `tests/test_sim.nim:44-80, 450-465` |
| N13 "tuned with a grid harness" has no artefact | fixed | `586a768` | `tools/tune_baselines.nim`, `src/cogplomacy/llm.nim:194-205`, `tests/test_bot.nim` |
| N14a vacuous split-coast assertion | fixed | `d20c543` | `tests/test_map.nim:118-134` |
| N14b `pkDone` is not in the note's `PhaseKind` list | **no change** | — | `src/cogplomacy/types.nim:111` |
| N14c stabs persist into the next phase's frames | fixed | `9711b80` | `src/cogplomacy/sim.nim:972-980`, `tests/test_sim.nim` |

---

## N1 — the expander never built a fleet

`buildSites` emits a centre's army option before its fleet options and `scriptedBuilds` took the
first option it saw, then skipped the rest of that province under the one-build-per-province
guard, so `wantFleet` was unreachable and every build was an army. The kind is now decided once
per centre — a fleet when the centre is coastal and the power holds fewer fleets than armies,
otherwise an army — and of a split coast's sites it takes the one with the most water, which is
the note's "`STP` builds `F STP/SC`".

Evidence, from CI rather than from reading: the `smoke-replay` artifact of the **new** run
32728438824 contains `{"action":"build","unit":{"power":6,"kind":"F","province":3}}` (Turkey,
`F ANK`) and `{"power":3,"kind":"F","province":9}` (Germany, `F BER`) where the reviewed sha's
artifact had `"kind":"A"` for both. New tests: `tests/test_bot.nim` "a vacant coastal home centre
builds a fleet when fleets trail armies" (asserts exactly `BUILD F STP/SC`) and "the hedgehog
builds an army in the same place" (`BUILD A STP`, the hedgehog's rule is unchanged).
Checklist item **7**.

## N2 — the expander now supports at rank (c)

The support substitution ran only when no destination survived the claim filters (`entry.dest <
0`). Ranks now carry their pre-penalty category (`MoveOption.base`), and a unit whose own best
option is only rank (c) or (d) backs one of ours that is really moving. Two care points: the
category used is the **unpenalised** rank, so the Spring home-centre penalty (which the note
describes as dropping a rank for ordering purposes) cannot silently turn a centre-grab into a
support; and only units that end up moving are supported, so the baseline still never writes a
void support. Evidence: `tests/test_bot.nim` "a unit that would only close the distance supports
a neighbour" (RUH's own best is HOL, rank (c); it writes `A RUH S A BUR - BEL` instead), and the
existing seeds-1..8 legality sweep plus `expanderTotal > hedgehogTotal` still pass in run
32728438824. Checklist item **7**.

## N3 — an illegal order consumes its unit's slot

`submitOrders` recorded the illegal order and `continue`d before claiming the province, so
`["A PAR - ENG", "A PAR - BUR"]` played `A PAR - BUR`. `badOrder` now leaves `unit.province = -1`
and `parseOrder` fills in the unit whenever the order's head names one of the power's units
(`namedUnit`), so `submitOrders` can do what steps 1–2 say: record the illegal order, hold that
unit, claim its province, and drop any later order for it. Evidence: `tests/test_sim.nim` "an
illegal order holds its unit and a later order for it is dropped" — `illegal.len == 1`,
`why == "wrongunit"`, `"A PAR H" in orders`, `"A PAR - BUR" notin orders`. Design-note resolution
steps 1–2; feeds checklist item **2** (the replayed order list is the one the rules produced).

## N4 — `replayMatch` checks the fields it re-derives

`phase` compared only year/season/phaseKind and `adjudicate` only `results.len`. It now compares
the `start` and `phase` events' `units` (power, kind, province, coast, in order), `owners` (all
34 slots) and `counts[7]`, and every recorded `OrderResult`'s outcome and canonical order, plus
the dislodged units and the standoff list. Evidence: `tests/test_sim.nim` "replayMatch rejects a
recorded board the rules do not re-derive" — deleting one unit from a recorded `phase` event, and
flipping one recorded outcome, each raise `CogplomacyError`; the existing frame-by-frame test
(`frames.len == events.len + 1`, final frame equal to the live `tableStateJson`) still passes, and
so does the wasm viewer, which runs this same `replayMatch` over the smoke replay
(`{"loaded":true,…,"feed_lines":36}` in run 32728438824). Checklist item **2**.

## N5 — the prompt wait is the note's bound, and the switch is permanent

The grace was `min(deadline, epochTime() + 5.0)`; it is now the connect deadline itself
(`playerConnectTimeoutSeconds`, default 180), and it still breaks the moment every seat has
delivered, so the smoke's timing is unchanged. The websocket handler no longer writes a late
`prompt` frame into `state.scripted` for a seat that play started without: it logs
`slot N delivered a prompt after play started; ignoring it`. A seat that *did* deliver before the
start can still update (the reference player sends its prompt twice, on connect and after
`welcome`) because the guard is `state.started and not state.promptSeen[slot]`. No wait grew
unbounded: the connect loop's deadline is the only bound involved and it is unchanged.
Checklist item **5**.

## N6 — the feed reads in words, with full province names

`renderFeed`'s `orders` line printed canonical notation and the adjudication lines named no
province. The renderer already fetches `data/map1901.json`; that map now also feeds a
code→name and id→code lookup (`diploLearnProvinces`, called from `makeRenderer`'s map callback),
and the appended block gained `diploPlaceWords` / `diploProvinceWords` / `diploOrderWords` /
`diploMoveWords`. Lines now read `France orders Paris → Burgundy; Brest supports Paris →
Burgundy.`, `Germany's Munich → Burgundy bounces.`, `STANDOFF in Burgundy — nothing enters.`,
`Austria's Trieste is dislodged by an attack out of Venice and must retreat.`, `Austria's Trieste
retreats to Albania.`, `France builds a fleet in Brest.` Events name provinces by **id**, so
`data/map1901.json` now carries `"id"` per province, emitted by its committed generator
(`scripts/art/build_map1901.py`) and pinned to `mapdata.nim` by `tests/test_viewer.nim`
(`entry["id"].getInt() == index`). Every lookup falls back to the code, and every line to its old
wording, if the map fetch fails, so `data-replay-loaded` stays honest. Evidence: the wasm-viewer
job of run 32728438824 renders the bundle with `"loaded":true` and `feed_lines: 36`; the helper
outputs were also exercised directly (`A PAR - BUR` → `Paris → Burgundy`, `F ENG C A LON - BRE` →
`English Channel convoys London → Brest`, `F STP/SC - BOT` → `St Petersburg (SC) → Gulf of
Bothnia`, unparsable text prints unchanged). Checklist item **11** (legibility: words and
numerals, never internal notation).

## N7 — a province a dislodged unit still stands in is not a retreat square

`resolveOrders` lifts dislodged units off `board.units` before the retreat phase, so
`retreatDestinations`' emptiness test read their provinces as empty. The reviewer flagged this as
a divergence rather than asserting the note is wrong, and the brief asked for a rules judgement:
**standard Diplomacy bars a retreat into an occupied province however its occupier got there** —
a dislodged unit does not leave until its own retreat resolves, which is why two dislodged units
cannot swap or chain. The note's step 9 wording ("empty after the movement phase") is satisfied by
the stricter reading, so this is a fix rather than a design change. `retreatDestinations` and
`legalRetreats` now take the dislodged list and skip those provinces; `applyRetreats` passes the
whole list to `parseRetreat` (which already filtered by power when finding the unit, so its own
lookup is unchanged). Evidence: `tests/test_adjudicate.nim` "a province another dislodged unit
still stands in is barred" — with `A VIE` and `A TYR` both dislodged, `TYR notin open` and
`BOH in open`. Correctness against the rules the note ports.

## N8 — a letter addressed to `ALL` is published

`parsePress` resolved the recipient with `powerByName` alone (`ALL` → −1 → dropped) and
`applyPress` dropped any letter with `toPower < 0`. `ALL` is now accepted case-insensitively and
kept as a **public** letter: every power's `inboxOf` sees it, the spectator frame's `press` array
carries it as `"public": true`, the event and the replay carry it, and the feed prints
`France writes to everyone: "…"`. Only an unknown recipient is still dropped. One subtlety the fix
had to handle: `applyPress` puts the broadcast into the same `letters` list, so replaying a press
event would have published the broadcast twice — a public letter whose text equals the broadcast
is skipped, which keeps `replayMatch` byte-identical (the frame-by-frame replay test passes).
Evidence: `tests/test_sim.nim` "a letter to an unknown power is dropped, one to ALL is published"
(the `ATLANTIS` letter is still dropped; every one of the seven powers reads the `ALL` letter) and
`tests/test_bot.nim` "a letter addressed to ALL is kept as a public letter" (`{"to":"all"}`).
Design-note reply schema.

## N9 — CI asserts what §CI jobs describes; the template stays verbatim

The two halves of the note disagreed and the code followed the copy-verbatim half. Per the brief,
verification was strengthened **without** diverging the scaffold: `tools/ci/docker_smoke.sh` is
untouched (still byte-identical to `templates/tools/ci/docker_smoke.sh` modulo the
`<slug>`/`<IMAGE>`/`<SEATS>` substitution), and `ci.yml`'s `docker-smoke` job gained one step
after it, `Assert the smoke artifacts against the manifest`, running the new
`tools/ci/assert_smoke_artifacts.py` (mode 100755). It validates `dist/smoke/results.json` against
`game.results_schema` **from the manifest itself** (type, required, `additionalProperties: false`,
`minItems`/`maxItems`, item types, `minimum`/`maximum`), requires `reason == "complete"` and seven
entries in `names`/`powers`/`scores`/`centres`/`units`, and requires the replay to parse as UTF-8
JSON carrying `events`, `results`, `names`, `policyNames`, `powers` and `config`. Every failure
prints `::error::SMOKE ARTIFACT FAIL: …` and exits 1. Evidence: run 32728438824,
`smoke artifacts OK: reason=complete scores=7 events=40 replay keys=['config', 'events', 'names',
'policyNames', 'powers', 'protocol', 'results']`; negative paths were exercised locally against a
doctored results file (`reason='deadline'`, a score of 2.0, an extra key) and all three were
reported and exited 1. Checklist items **1**, **6**, **12**.

## N10 — error text is cut on rune boundaries

`extractJsonObject` and `textOf` cut model text and response bodies with byte ranges. They now use
the same `cleanText` / `oneLine` every replay string uses. These strings still only reach stdout,
but item 9 names captured errors and the cost of being right is one call each. Evidence:
`tests/test_bot.nim` "the error text for an unusable reply is cut on rune boundaries" — 400 doves
in, `validateUtf8(error.msg) == -1` and `runeLen <= 200`. Checklist item **9**.

## N11 — the play deadline is always set

`playDeadline` was `0.0` for a non-positive timeout and the pre-batch check had an escape branch
(`playDeadline > 0.0 and …`). A non-positive resolved timeout now falls back to
`defaultGameConfig().episodeTimeoutSeconds` (1200) and the deadline is unconditional, so the 60 %
budget cannot be switched off by a config the manifest happens not to forbid. Checklist item **5**.

## N12 — all nine event kinds are required

The presence assertion listed seven kinds. The test now also plays an episode with a forced
dislodgement (`dislodgementEpisode`: Austria takes Venice with `F TRI - VEN` + `A TYR S F TRI -
VEN` while Italy holds, every other seat on the baseline) and requires **every** member of
`EventKind` across the two episodes, with the round trip
(`$eventToJson(eventFromJson(eventToJson(e))) == $eventToJson(e)`) asserted on each event of both.
Evidence: green `test` job in run 32728438824 (the assertion fails if `retreat` or `build` is
missing). Checklist item **2**, design-note §Tests.

## N13 — a committed grid harness for the baseline's numbers

The expander has exactly two numbers in it: the Spring home-centre rank penalty and the rank at
which a unit supports instead of moving. They are now data (`ExpanderTuning`, shipped at the
note's values `1` / rank (c)) and `tools/tune_baselines.nim` sweeps the 3 × 3 grid over a seed set
on a mixed table (four expanders on the swept tuning against three hedgehogs), reporting per cell
the centres each side ended with, the illegal orders written and whether every episode reached
`complete`. `tests/test_bot.nim` runs a reduced sweep **through the same module**, so the harness
is compiled and its table printed by every CI run and cannot rot; the test asserts every cell
plays legal, complete episodes and that the shipped cell beats the wall. The recorded grid from
run 32728438824 (seeds 1–2, 2 years):

```
springHomePenalty=0 supportFromRank=1  expanders= 36  hedgehogs= 20  illegal=0  complete=true
springHomePenalty=0 supportFromRank=2  expanders= 36  hedgehogs= 20  illegal=0  complete=true
springHomePenalty=0 supportFromRank=3  expanders= 38  hedgehogs= 20  illegal=0  complete=true
springHomePenalty=1 supportFromRank=1  expanders= 41  hedgehogs= 20  illegal=0  complete=true
springHomePenalty=1 supportFromRank=2  expanders= 41  hedgehogs= 20  illegal=0  complete=true   <- shipped
springHomePenalty=1 supportFromRank=3  expanders= 39  hedgehogs= 20  illegal=0  complete=true
springHomePenalty=2 supportFromRank=1  expanders= 41  hedgehogs= 20  illegal=0  complete=true
springHomePenalty=2 supportFromRank=2  expanders= 41  hedgehogs= 20  illegal=0  complete=true
springHomePenalty=2 supportFromRank=3  expanders= 39  hedgehogs= 20  illegal=0  complete=true
```

The shipped cell is on the grid's maximum (41, tied with three others; every alternative that is
strictly worse is note-incompatible anyway — the note pins both numbers). Checklist item **7**,
second sentence.

## N14a — the split-coast assertion can now fail

The old test built the union over a province's own coast nodes and then checked each node's
neighbours were in that union: true by construction. It now asserts what the property is for —
every coast reaches some water (`part.len > 0`) and **strictly less** of it than the province as a
whole (`part < whole`, proper subset) — which is false the moment a split coast is transcribed
with the whole province's neighbours. Checklist item **1** ("no test loosened": this is the
opposite direction).

## N14b — `pkDone` — no change, by design

`types.nim:111` adds a fifth `PhaseKind`, `pkDone`, which the note's `types.nim` list does not
name, and it surfaces as `"phase":"done"` in `tableStateJson` after `settle`. Left as is: it is a
terminal marker, not a playable phase — nothing is ever `pending` in it, `scriptedDecision`,
`applyDecision` and `parseDecision` all `discard` it, and it is what lets those `case` statements
be exhaustive without an `else`. Removing it would mean either a non-exhaustive case or leaving
the sim reading `"phase":"builds"` after the episode ended, which is worse for the viewer (the
readout is driven by `gameDone`/`reason`, and `FINAL · RUSSIA 4 CENTRES` is what the smoke's 100 %
scrub position prints in run 32728438824). No checklist item is engaged; recorded so the judge can
weigh it.

## N14c — stabs belong to the turn they happened in

`tableStateJson` scanned back to the most recent `adjudicate` event whatever phase the frame was
in, so the STAB stamps stayed on the board through the following press and orders frames while the
per-seat `stabbedThisTurn` chip had already been cleared. The scan now stops at the first `press`
or `orders` event, which is exactly when `openPress`/`openOrders` clear that flag — retreat and
build frames of the same turn still carry the stamps, matching the chip. Evidence:
`tests/test_sim.nim` "a stab is stamped for its turn and comes down at the next press" — France
pledges `keepout BUR` and then orders `A PAR - BUR`; `stabs.len == 1` on the adjudication frame
and `0` after the next press event. Checklist item **11**.

---

## "No test loosened" (checklist item 1, second half)

Every hunk in `git diff 1b9ddad..HEAD -- tests/` is an addition or a strengthening. The only
removals are:

- four `retreatDestinations(...)` call sites gaining the dislodged-list argument (N7);
- `test "a coast's fleet adjacency is a subset of the province's"` replaced by the proper-subset
  version (N14a) — strictly stronger;
- `test "a letter to an unknown power is dropped"` replaced by "a letter to an unknown power is
  dropped, one to ALL is published" (N8) — the unknown-power drop is still asserted, plus the new
  `ALL` behaviour the note requires;
- the seven-kind list in the round-trip test replaced by `for kind in EventKind` (N12) — strictly
  stronger.

Nothing was deleted, skipped, `xfail`ed or given a wider tolerance. Net: +23 removed lines against
+270 added across five test files, and two new test files' worth of cases (`tests/test_bot.nim`
+101, `tests/test_sim.nim` +129).

## NOTED (not fixed)

Seen while working, out of scope for this round, no code touched:

- `client/renderer.js:704-730` still carries the starter's `describeEvent`, which nothing calls
  now that `diploFeedLines` exists (the review noted it under N6); `mapdata.nim:463`
  `powerAdjective` and `orders.nim:52-68` `orderWords` are likewise uncalled — the feed wording is
  implemented on the JS side because that is where the map's names live.
- The `centres` feed line names counts and deltas but not **which** centre changed hands
  (the note's example says `France 6 (+1 Belgium)`); the `centres` event carries `gained`/`lost`
  counts only, so naming the province would need a new event field.
- The dislodgement feed line does not say who supported the attack or where the unit retreated to
  (the note's example does); both live in other events (`results`, the later `retreat` event) and
  joining them would be a feed-state change rather than a line change.
