# r1 review — garble

Repo: `/workspace/cogame-garble` (tree-identical to `Metta-AI/cogame-garble` main @ `d76e12c`)
Design note: `/workspace/coworld-builder/runs/2026-08-24-garble/design.md`
(byte-identical to `docs/plans/2026-08-24-garble-design.md` in the repo — verified by `diff`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files opened: every `.nim` (9), every `client/*` (6), every `replay-viewer/*` (4), the manifest,
the three workflows, `tools/build_replay_viewer.sh`, `tools/ci/*` (3), `compose.yaml`,
`garble.nimble`, both Dockerfiles, `README.md`, `scripts/art/*` (2), the babel starter's
counterparts, and bullwhip's `llm.nim`.
Executed: all three test files locally (debug + `-d:release` for `test_bot`), four ad-hoc Nim
probes against `src/`, and read the CI logs and the `smoke-replay` artifact of run
**32700138054** (`gh run view/download`).

Observations are numbered F1…F21 and reported neutrally: what the code does, at a line, and what
the note says. No severity is assigned and no fix is proposed.

---

## Findings

### F1 — the cog sprites are newly generated art, not the starter's soldier sprites

- Code: `data/` holds five 128×128 RGBA PNGs `cog_{red,blue,green,yellow,violet}_front.png`
  (committed in `f1aeb04`); commit `8336352` ("Drop the four unreferenced starter sprites") deleted
  `data/soldier_{red,blue,green,yellow}_front.png`. `client/renderer.js:611-613` loads
  `["cog_red_front.png", … "cog_violet_front.png", "arena_floor.png"]`;
  `renderer.js:391` resolves `images["cog_" + color + "_front.png"]` and `drawCog` contains no
  tinting path. `tools/build_replay_viewer.sh:57-59` copies the five cog PNGs plus
  `arena_floor.png` and `font.ttf` (seven assets). The sprites were produced by
  `scripts/art/gen_cog_sheet.py` (a Gemini "nano-banana" render from
  `scripts/art/source/cog_reference.png`, a blue Softmax cog that is *not* babel's
  `soldier_blue_front.png` — both opened and compared) and `scripts/art/split_cog_sheet.py`.
- Note: design.md:1067-1069 — "`data/` — babel's `arena_floor.png`, `font.ttf`,
  `FONT_LICENSE.txt` and the four `soldier_<red|blue|green|yellow>_front.png` sprites, unchanged.
  Real art from the starter; the fifth cog is the red sprite violet-tinted at draw time"; and
  design.md:979-982 — "Seats 0–3 use babel's `soldier_<…>_front.png` sprites verbatim; **seat 4
  uses `soldier_red_front.png` drawn through a violet tint** (offscreen canvas, `source-atop` fill
  at 0.75 with `COLOR_HEX.violet`)". `arena_floor.png`, `font.ttf` and `FONT_LICENSE.txt` are
  unchanged from the starter (byte-identical). `README.md:88-91` documents the substitution.
  Inspected visually: the five PNGs are finished illustrated cogs with distinct radio kits, not
  placeholder boxes.

### F2 — `game.docs.readme` is a bare string, not `{"type":"text","value":…}`

- Code: `coworld_manifest_template.json:287` — `"readme": "Five cogs sit on one exchange …"`.
  The two `pages` entries (lines 289-305) do carry `{id, title, content:{type:"text", value}}`.
- Note: design.md:1126-1129 names both keys but not the readme's inner shape. Checklist item 10
  specifies `game.docs` is
  `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`.
  All three talk-lineage starters use the object form
  (`cogame-babel`, `cogame-bullwhip`, `cogame-parley` — all `{"type":"text","value":…}`; `cogame-moba`
  uses `{"type":"uri",…}`). The release workflow's `coworld certify` step is the only place that
  would exercise the platform schema; I could not run it here (see *Could not determine*).

### F3 — `premium` / `quota` draw expressions differ from the note's literals (ranges agree)

- Code: `src/garble/sim.nim:188` `result.premium.add(6 + rng.rand(3))` → 6…9;
  `sim.nim:190` `result.quota.add(12 + rng.rand(7))` → 12…19 (Nim's `rand(max)` is inclusive).
- Note: design.md:95-96 — `premium[s] = 6 + rng.rand(4)` (6…9), `quota[s] = 12 + rng.rand(8)`
  (12…19). The literals would give 6…10 and 12…20 under Nim semantics; the code matches the
  parenthesised ranges, which `tests/test_sim.nim:37-38` asserts. The price draw
  (`sim.nim:167` `8 + rng.rand(6)` → 8…14) matches both the literal and the range in
  design.md:88.

### F4 — two RNG streams, not one

- Code: aliases come from `tableNames`'s own stream, `sim.nim:118`
  `initRand(int64(seed) * 6779 + 31)`; everything else from `sim.nim:163`
  `initRand(int64(config.seed) * 7919 + 17)`, in the order prices (165-173), surplus/demand deal
  (175-186), premiums (187-188), quotas (189-190), interference phase (193), burst table
  (194-197) — i.e. the note's order minus the aliases. `sim.nim:159-162` comments the split.
- Note: design.md:99-101 — "Every draw above comes from **one** RNG stream at `initSim`, in this
  order: aliases, prices, surplus/demand deal, premiums, quotas, interference phase, burst table.
  `seed` alone reproduces all of it." Both streams derive from `seed`; `tests/test_sim.nim:48-55`
  asserts full reproduction from the seed and difference across seeds.

### F5 — the published `curve` is scaled by `noiseScale`

- Code: `sim.nim:199-203` — `base` is the unscaled cosine swell, then
  `result.curve.add(round3(clamp(base * config.noiseScale, 0.05, 0.95)))` and
  `interference.add(round3(clamp((base + burst*0.35) * noiseScale, …)))`. Measured with a probe:
  seed 3 turn 0 gives `curve[0] = 0.6` at `noiseScale = 1.0` and `0.9` at `noiseScale = 1.5`.
  `curve` is what `tableStateJson` publishes (`sim.nim:731-733`) and what the prompt's forecast
  block prints (`llm.nim:290-295`).
- Note: design.md:144-151 defines `base` without `noiseScale` and design.md:697-698 calls `curve`
  "the published interference base for every turn"; design.md:153-156 says the base curve is
  published and is derivable from `seed` + `turns` + `noiseScale`. The note does not state
  explicitly whether the published curve carries the scale.

### F6 — an empty transmission at a zero meter is not flagged `silent`

- Code: `sim.nim:434-436` — `if sim.airtime[seat] <= 0: silent = line.len > 0; line = ""`. Probed:
  `applySay(0, Radio, "", …)` with `airtime[0] = 0` records `silent = false`. With non-empty text
  and a zero meter the flag is set (`tests/test_sim.nim:137-147`).
- Note: design.md:270-272 — "If `airtime[s] == 0`, the transmission is dropped entirely and the
  event is flagged `silent`." The viewer's `SILENT` tag and the feed's "— SILENT (no airtime)"
  line key off this flag (`renderer.js:462`, `renderer.js:831-833`).

### F7 — sim-side truncation carries no `…` marker

- Code: `sim.nim:398-406` `clipRunes` returns `text.runeSubStr(0, limit)` with no marker; it is
  what truncates `text` (426), the airtime clip (438) and `notes` (443).
  `llm.nim:552-559` `cleanText` does mark the cut (`runeSubStr(0, limit - 1) & "\u2026"`).
- Note: design.md:541-543 — "Every truncation is on rune boundaries (`runeSubStr`, with `…`
  marking the cut)". Both paths are rune-safe; `tests/test_sim.nim:117-135` and
  `tests/test_bot.nim:234-243` assert `validateUtf8() == -1` at the caps, and the smoke's
  strict-UTF-8 replay parse passed in CI.

### F8 — `replayMatch`'s equality check covers a subset of the recorded fields, and accepts any `end` reason on a short replay

- Code: `sim.nim:905-914` `sameEvent` compares kind, turn, seat, ticket, qty, price, commodity,
  fill, seller, buyer, said{Qty,Commodity,Price}, partial, misheard, reason, prices, portfolios,
  interference and burst. It does **not** compare the `turn` event's `airtime` array, the `end`
  event's `scores` array, or the `say` event's `text`/`notes`/`cost`/`silent`/`clipped`/`scripted`
  (`say` gets its own narrower check at `sim.nim:940-944`: ticket, cost, hasTerms). At
  `sim.nim:959-968` the `end` branch calls `sim.settle(event.text)` when the replayed sim is not
  already done and then compares `sim.reason` to `event.text` — so any string is accepted as the
  ending reason of a replay that stops short.
- Note: design.md:656-660 — "`turn`, `deal`, `void` and `end` are **derived** facts that are
  nevertheless **recorded**, and `replayMatch` re-derives them and raises `GarbleError` on any
  mismatch"; design.md:339-345 — `reason` has exactly two legal values. The two tamper cases the
  note's test list names (design.md:1290-1292: a `deal` `fill`, a `turn` price) do raise —
  `tests/test_sim.nim:539-554`, which I ran.

### F9 — a replayed `silent` say re-derives with `silent = false`

- Code: same mechanism as F6. A recorded silent `say` has `text = ""`; replaying it through
  `applySay` (`sim.nim:938`) produces `silent = false`, and `sameEvent` is not applied to `say`
  events (`sim.nim:940-944` checks ticket/cost/hasTerms only), so the difference does not raise.
  No render consequence was found: `heardFor` returns `@[]` for an empty word list and the wire
  entry's `said` is `""` either way (`sim.nim:296-308`, `689-698`).
- Note: design.md:650 lists `silent` as a recorded `say` field; design.md:656-660 as above.

### F10 — the endcard reads the recorded `results` block; every other readout reads the re-derived frames

- Code: `renderer.js:1393-1394` — `updateEndscreen(options.endscreen, payload.results, …)`. The
  clock, scorebug, legend, stage and audio level all read `currentState()` =
  `payload.states[index]`, which the wasm module builds with `replayMatch`
  (`replay-viewer/garble_replay.nim:39-40`), as does the server in replay mode
  (`server.nim:205-209`). Babel's `attachReplay` does the same with `payload.results`.
- Note: design.md:722-726 — the viewer "re-derives every frame with `replayMatch`"; checklist item
  2 — "the viewer derives its display from that same re-derivation — not from a parallel
  recording." `tests/test_sim.nim:513-514` asserts the final replayed frame's `tableStateJson`
  **and** `resultsJson` equal the live sim's, but nothing compares the replay file's `results`
  block to the re-derived one at load time.

### F11 — the retry gate's "probe" cannot reject on reply content

- Code: `llm.nim:700-705` — after `parseDecision`, `var probe = sim; probe.applySay(seat,
  decision.channel, decision.text, decision.notes, false)`, commented "Reject illegal replies here
  so the retry carries the hint." `applySay` raises only on `done`, `phase != phWire`, a bad seat
  index, or a repeat say (`sim.nim:416-424`); the snapshot handed to `decideAll` is taken
  immediately after `beginTurn` (`server.nim:338-344`), so `phase == phWire` and `said[seat]` is
  false for every seat. Text and notes are already rune-capped by `parseDecision`
  (`llm.nim:607-609`) and cannot make `applySay` raise. In practice every ill-formed reply is
  caught by `extractJsonObject`/`parseDecision` before the probe.
- Note: design.md:257-261 — ill-formed means "the JSON is unreadable or a confirm's fields are
  missing or out of range", which is exactly what `parseDecision` enforces; the note does not
  require the probe.

### F12 — below 560 px the live interference column is not drawn

- Code: `renderer.js:113` — `if (!layout.compact && curve.length > 1 && plot.w > 40) { … }` wraps
  both the sparkline (115-123) and the live amber column (125-131). In compact mode only the
  percentage (136-139), the band word (140-142) and the `STATIC BURST` tag (144-149) are drawn.
- Note: design.md:1045-1046 — below 560 px "the interference sparkline drops to the live column
  plus the band word".

### F13 — the burst wash does not drive `#grain`

- Code: `renderer.js:154-166` `drawBurstWash` draws a seeded scanline overlay on the canvas for
  `BURST_MS = 700` ms and nothing else; `#grain` is never touched anywhere in `renderer.js`
  (no match for `getElementById("grain")`). `#lightpool` is driven (`renderer.js:560-580`).
- Note: design.md:969-971 — the burst wash is "a seeded scanline overlay plus `#grain` at double
  opacity for ~700 ms"; design.md:917 — "`#grain` is doubly apt here and is driven harder during a
  static burst". The element is present in the page and keeps its starter CSS
  (`client/replay_broadcast.html:23`).

### F14 — audio: no per-word crackle, and the gain floor is not zero at CLEAR

- Code: `renderer.js:1123-1205` `makeStatic` builds one looping seeded-noise buffer → bandpass
  1800 Hz → gain → master 0.2 → compressor (1138-1168), constructed on the button's first click
  (1171-1174), fully wrapped in `try/catch` with a `♪ STATIC N/A` disabled state (1178-1182), and
  exposes only `level` and `stop`. `renderer.js:1192` — `target = Math.max(0, Math.min(0.18,
  interference * 0.19))`, so at `interference = 0.20` (CLEAR) the gain is 0.038, not 0.
  There is no per-word crackle call anywhere in `drawWordRow` (199-250) and no scheduled node to
  cancel on a seek (`setIndex` calls `noise.level(state.interference)`, 1390).
- Note: design.md:996-1000 — "a `GainNode` whose level tracks `interference[t]` (0.0 at `CLEAR`,
  0.18 at `STORM`), plus a short crackle burst on every garbled word as it is drawn";
  design.md:1007 — "A seek cancels every scheduled node." The fencing, the button placement inside
  `.tbar`, and the "audio never gates `data-replay-loaded`" property all hold (F-conformant list
  below).

### F15 — the feed's closing lines omit the leader and the turn cap

- Code: `renderer.js:939-943` — `end` renders as `"Episode deadline — scored on " + event.turn +
  " turns."` or `"FINAL — " + event.turn + " turns played."`.
- Note: design.md:1029 — "`FINAL — Sprocket 1.42× (312 cr)` / `Episode deadline — scored on 7 of
  12 turns.`" The endcard itself does carry the ranked table with credits and the
  "episode deadline: scored on N of M turns" sub-line (`renderer.js:784-786`).

### F16 — one rename beyond the three the note lists

- Code: `client/replay_broadcast.html:13`, `client/global.html:13`, `client/player.html:13` and
  `replay-viewer/index.html:13` change the starter's `<div id="clock">ROUND 0</div>` to
  `TURN 0`. Diffs against the starter show this is the only change beyond the note's three
  (`BabelRenderer`→`GarbleRenderer`, `<title>`, `#wordmark`) plus the one inserted
  `<script src=".../chrome_common.js">` and the appended banner block.
- Note: design.md:906-909 — "(a) the identifier renames a fork requires — `BabelRenderer` →
  `GarbleRenderer`, the `<title>`, and the `#wordmark` text".

### F17 — no grid-tuning harness for the baselines is present in the tree

- Code: the only calibration evidence is `tests/test_bot.nim:100-125`: a 200-seed shark-heavy vs
  all-quoter mishearing comparison and a 200-seed `noiseScale 0.5` vs `1.5` mean-score comparison,
  both `echo`ed (observed locally: "misheard deals: shark-heavy 668 all-quoter 365"; "mean quoter
  score: quiet 1.2564 storm 1.1335"). `scripts/` contains only the two art scripts; `tools/`
  contains the build hook and `ci/`.
- Note: the design note does not describe a harness either (§*Scripted baselines*, design.md:550-580
  states the rules directly). Checklist item 7's second sentence — "The baseline's parameters were
  tuned with a grid harness, not guessed" — has no artefact in the tree to point at.

### F18 — the observation prompt runs larger than the note's estimate

- Code: `llm.nim:341-364` `heardBlock` emits one line per past `say` the seat heard, for **every**
  turn (older than `HeardWindow = 3` turns it truncates the heard text to 40 runes, but does not
  drop the line); `llm.nim:366-381` `tapeBlock` emits one line per settled deal for the whole
  episode; `llm.nim:316-339` `ticketBlock` emits four lines per confirmable ticket. Measured with a
  probe driving a full all-`quoter` episode through `userPrompt`: peak user prompt **5405 runes**
  at `turns = 12` and **7036 runes** at `turns = 18` (system prompt 3057 runes).
- Note: design.md:518-519 — "`HeardWindow = 3`: the last three turns of heard traffic are printed
  in full, earlier turns compress to `turn t <alias> → <channel>: <first 40 runes>…`, which bounds
  the prompt at roughly 3 000 runes on a twelve-turn episode." The full-vs-summarised window itself
  is correct: `llm.nim:354` prints in full when `event.turn >= sim.turn - HeardWindow`, and since
  observations are built before any `say` of the live turn lands, that is exactly turns
  `t-3, t-2, t-1`.

### F19 — the inter-batch spacing floor is paid even when no LLM call was issued

- Code: `server.nim:352-358` — `spacingMs = max(config.minTurnSpacingMs, callsLastTurn *
  MsPerCall)` and the sleep is taken whenever `lastBatchStart > 0.0`, which is set every turn
  (line 358) regardless of whether `decideAll` issued anything. With no credentials (`client.disabled`,
  `callsIssued = 0`, `llm.nim:664-674`) a turn still sleeps up to `minTurnSpacingMs` — 12 000 ms at
  the variants' setting, i.e. ~132 s over `standard` and ~204 s over `long-session`, both inside
  the 720 s play budget. The certification fixture sets `minTurnSpacingMs: 0`
  (`coworld_manifest_template.json:492`), so `docker-smoke` does not pay it (observed: the whole
  8-turn episode ran in ~1 s of play plus the 20 s shutdown grace, CI log 07:08:33→07:08:54).
- Note: design.md:394-396 states the floor as `max(minTurnSpacingMs, callsIssuedLastTurn * 2400 ms)`
  unconditionally, and design.md:396 notes "Certification sets it to 0 because certification runs
  with no credentials", so the code follows the rule as written. Recorded here because it is the
  one wait whose bound is not a function of the number of calls actually made.

### F20 — three assertions in the note's test list are not in the test files

- `tests/test_sim.nim:314-339` runs 20 episodes × 12 turns of random confirms (up to ~1200
  confirms) for the non-negativity property; design.md:1272 says "over 500 random confirm
  sequences".
- design.md:1281 — "selling its demand commodity below price lowers it" — has no counterpart; the
  scoring suite (`test_sim.nim:373-420`) asserts the never-trade = 1.0 case, the
  portfolio/hold identity with the quota cap, and the buy-cheap > 1.0 case.
- design.md:1292 — "a tampered `turn` event (interference **or** a price changed) raises" — the
  test (`test_sim.nim:539-554`) only mutates `prices[0]`; `sameEvent` does compare `interference`
  (`sim.nim:914`).
- Everything else in the note's three test lists is present; I ran all three files (165 `[OK]`
  lines in the CI `test` job; all green locally in debug, and `test_bot` also under `-d:release`).

### F21 — the game thread has no top-level exception guard (inherited shape)

- Code: `server.nim:272-409` `runGame` catches `GarbleError` around `applySay` (376-383) and
  around `applyConfirm` (392-398); `beginTurn`, `endTurn`, the fallback `applySay` inside the
  first `except` (383), `broadcastLocked` and `finishEpisode` are unguarded, and the thread is
  created with `createThread` (`server.nim:604`) while the main thread serves HTTP forever
  (`server.nim:606`). If the game thread died, the container would keep answering `/healthz`
  with no artifacts written until the platform's kill. I found no reachable path: `beginTurn`
  raises only when `done` (checked at 329) or when every turn is played (which sets `done` first,
  `sim.nim:394-396`). `cogame-babel/src/babel/server.nim:250-358` has the identical structure, so
  this is the starter's shape, not a Garble change. **Inferred, not observed** — no run in CI or
  locally exercised it.
- Note: design.md:418-419 — "Every wait in the game is bounded: the player-connect wait (180 s),
  the LLM batch (25 s), the artifact writes (60 s inside `writeArtifact`), and the pacing sleeps."
  Each of those bounds is present (see the conformance list).

---

## Checked and conformant

**Resolution rules**

- Seven-step turn order, in order, in `server.nim:320-408`: deadline check before the turn opens
  (331-336, `endEarly()`), `beginTurn` (338), snapshot + prompts under the lock (344-346), one
  batch (365), `applySay` for seats 0…4 (371-384), `applyConfirm` for seats 0…4 after every say
  (386-399), `endTurn` (400), `sleep(turnDelayMs)` (404-405).
- Scanner: `wire.nim:203-242` implements the note's seven steps exactly — first verb, first `AT`
  after it, modal qty with last-wins ties (`modalValue(..., lastWins = true)`, 171-186), modal
  commodity with last-wins ties (188-201), modal price with first-wins ties, `qty == 0` ⇒ none.
  `Terms` carries `kQty/kCom/kPrice` and the three modal words (`wire.nim:50-61`).
  Asserted by `tests/test_wire.nim:60-113`, which I ran.
- Neighbour table: `wire.nim:124-154` — digit rules first (append-0 only when the value ×10 ≤ 99,
  drop-last for 2-digit, last digit ±1 mod 10 bounded to ≤ 99), then the spelled matching
  (`wire.nim:37-43`, 11 pairs, `ZERO ONE FOUR SEVEN EIGHT ELEVEN` unpaired) and the commodity pairs.
  Probed: `neighborsOf("5") = {50,6,4}`, `neighborsOf("50") = {5,51,59}`, `neighborsOf("FIVE") =
  {NINE}`, `SELL/BUY/AT/chatter = {}`. Symmetry-and-matching asserted over the whole lexicon
  (`test_wire.nim:135-145`).
- Per-delivery RNG: `wire.nim:246-251` `initRand(seed*1_000_003 + turn*997 + from*31 + to*7 + 1)`,
  exactly the note's expression, and depends on nothing but `(seed, turn, from, to)`.
  `wire.nim:253-281` applies drop < 0.45n, swap < 0.85n (drop when the neighbour set is empty),
  then the shared burst run at `int(burstFrac * n_words)` for `burstLen` words.
  `noiseFor` (`sim.nim:292-294`) uses `LineNoiseFactor = 0.6` off the radio.
  `test_wire.nim:153-221` asserts the rates, the neighbour-set membership, the identical burst run
  across recipients, and per-`to` divergence.
- Redundancy shield: `wire.nim:299-317` — exact value always admissible; otherwise `k == 1` **and**
  the asserted value in the single said word's neighbour values; `side` never admits a change.
  `applyConfirm` checks side first with its own `side` void (`sim.nim:546-548`) then
  `admissible` → `inadmissible` (549-551), matching design.md:290-292.
  End-to-end headline case asserted in `test_sim.nim:341-371` (terse offer robbed for 20 units,
  `misheard` + `partial`; the repeated offer voids `inadmissible`).
- Void reasons: all eight of the note's strings are produced and no others —
  `no-ticket` (`sim.nim:524`, and 539 for a same-turn confirm), `expired` (528),
  `already-settled` (531), `own-ticket` (534), `not-addressed` (542), `side` (547),
  `inadmissible` (550), `uncovered` (559).
- Ticket life and reach: `expiry = turn + TicketLife + 1` (`sim.nim:471`), `mayConfirm` requires
  `turn > ticket.turn` and `turn < expiry` (`sim.nim:328`), radio ⇒ any non-offerer, line ⇒ the
  addressee (330-333). Same-turn race resolves in seat order and the second confirm voids
  `already-settled` (`test_sim.nim:206-219`).
- Coverage and settlement: `fill = min(qty, seller units, (price > 0 ? buyer cash div price :
  qty))` (`sim.nim:555-557`), `fill <= 0` ⇒ `uncovered`, then the four-line transfer (562-565),
  ticket closed (566), `partial`/`misheard` computed (568, 582-583), and both versions recorded
  (579-581). Cash and units never negative over randomised traffic (`test_sim.nim:314-339`).
- Airtime: transmission costs its rune length, clipped to the meter on a rune boundary with
  `clipped` (`sim.nim:437-441`); a confirm is a flat 40 floored at 0 and is never blocked
  (`sim.nim:509`, asserted at `test_sim.nim:149-157`); `airtimeUsed = 900 - airtime`
  (`sim.nim:635`) and `≤ 900` is asserted.
- Scoring: `portfolio = cash + Σ units·F + premium·min(units[dem], quota)` at the last opened
  turn's prices (`sim.nim:234-261`), `hold` is the same formula on the starting position
  (263-268), `score = portfolio/hold` clamped to 0…10 (270-276). Never-trade = exactly 1.0 and
  `hold ≥ 180` asserted (`test_sim.nim:373-384`).
- Endings: `reason` is `""` until settled, then `complete` (`sim.nim:396`) or `deadline`
  (`sim.nim:605`); `endEarly` is idempotent (602-603) and scores on `turnsPlayed` at the last
  opened turn's prices (`test_sim.nim:582-595`). Observed in the smoke replay: `reason: "complete"`,
  `turns: 8`, `maxTurns: 8`.

**Decision path, waits and bounds** (checklist 5, 8)

- One parallel batch per turn: `llm.nim:675-691` builds a single `RequestBatch` over every open
  seat and calls `client.curl.makeRequests(batch, timeoutSeconds)` (curly's parallel multi-handle
  call, `{.raises: [].}`); scripted seats never enter the batch (667-674). No sequential per-seat
  request path exists. `requestFor`/`textOf`/`decideAll` are the bullwhip port the note permits —
  `requestFor` is line-identical to `cogame-bullwhip/src/bullwhip/llm.nim:332-356`.
- Retry once then fall back: `for attempt in 0 .. 1` (`llm.nim:675`), the retry batch carries the
  explicit hint (682-687), and every seat still open plays `scriptedAction(sim, seat, skQuoter)`
  with the greppable line `garble llm: seat N falling back to scripted decision`
  (`llm.nim:711-715`); the fallback is recorded on the event (`scripted` flag, set from
  `client.decidedScripted` in `server.nim:373-374`, 390-391) and in the replay
  (`sim.nim:807`, 823).
- Tolerant parsing: `extractJsonObject` takes the first `{` to the last `}` (`llm.nim:477-490`);
  `parseDecision` accepts int / numeric-string / float / spelled-word numbers, any case for
  `side`/`commodity`, an unknown or self channel → radio, missing/`null` confirm
  (`llm.nim:563-644`). Rejections are exactly the note's list (`test_bot.nim:217-232`).
  An inadmissible confirm is never retried — nothing in `decideAll` inspects admissibility.
- Credential ladder and degradation: Bedrock sidecar → `ANTHROPIC_API_KEY` →
  `ANTHROPIC_API_KEY_URI` (`llm.nim:122-152`), haiku-first candidate list (`llm.nim:102-106`),
  401/403 ⇒ `client.disabled` for the episode (`llm.nim:526-534`), 429 ⇒ rotate the model
  (535-538), no credentials ⇒ `disabled` at construction ⇒ every seat scripted with zero network
  calls (`test_bot.nim:127-153`, asserts `callsIssued == 0` and < 1000 ms).
- Every wait bounded: player connect 180 s polling loop (`server.nim:278-284`); batch timeout
  clamped to the remaining budget, `min(llmTimeoutSeconds, max(5, playDeadline - now))`
  (`server.nim:362-364`); spacing sleep capped at `spacingMs` (`server.nim:357`); pacing sleep
  (404); `sleep(500)` + artifact writes + a 20 s shutdown grace then `quit(0)`
  (`server.nim:243-259`); `writeArtifact`'s POST passes `60` and the PUT path goes through
  `writeCogameUri`, whose curly `put` default timeout is also 60 s
  (`/root/.nimby/pkgs/curly/src/curly.nim:659-666`).
- Budget arithmetic: `PlayBudgetFraction = 0.6` (`server.nim:261`), the game assumes
  `episodeTimeoutSeconds` when `COWORLD_TIMEOUT_SECONDS` is absent (`server.nim:299-308`) →
  `playDeadline = start + 720 s` at the default 1200. Because the spacing is measured from the
  previous **batch start** (`server.nim:354`), a slow batch absorbs the floor, so the note's
  "≈50.4 s worst case per turn, 12 × 50.4 ≈ 605 s" holds as written.
- `sampleEpisode` caps `turns` at `120 div 5 = 24`, floors at 6, caps `turnDelayMs` at
  `60000 div turns`, and is idempotent via `sampled` (`sim.nim:127-138`); the entrypoint fits the
  cap after the seed is settled (`src/garble.nim:34-42`).
- Player binary: prompt sent on connect and re-sent after `welcome`, receive loop wrapped in
  `try/except CatchableError`, `quit(0)` on a dead socket (`src/garble_player.nim:51-90`).
  CI observed "every player container exited 0".

**Strings and the replay writer** (checklist 9, 2)

- Rune-safe cuts at every boundary: `text` 160 (`sim.nim:426`, `llm.nim:607`), `notes` 400
  (`sim.nim:443`, `llm.nim:609`), `channel` 16 (`llm.nim:568`), player `prompt` 4000
  (`server.nim:528-529`), captured model text quoted at 160/300/400 bytes in error strings that do
  **not** reach the replay (`llm.nim:486-489`, 527, 536, 541). Multi-byte tests at every cap
  (`test_sim.nim:465-478`, `test_bot.nim:234-243`) and the smoke's strict-UTF-8 replay parse.
- Event kinds: exactly the note's seven (`types.nim:35-42`), with the note's field sets
  (`sim.nim:785-846`), unset fields omitted, `terms` present only when the said text parsed
  (808-813). Round-trip asserted for every kind (`test_sim.nim:530-537`).
- Heard text is never recorded: no `heard` key in `eventToJson`; `heardFor` re-derives it from
  `(seed, turn, from, to)` (`sim.nim:296-308`), and the replayed deliveries are asserted identical
  to the live ones for every delivery of a 12-turn episode (`test_sim.nim:516-528`). Confirmed on
  the real artifact: `dist/smoke/replay.json` (68 events) carries no heard text.
- Self-sufficiency: `replayPayload` writes protocol, `names` (aliases), `policyNames`, the whole
  config incl. `seed`, `noiseScale`, `sampled`, `commodities`, `airtimeBudget`, every event and
  the results (`server.nim:162-193`). Verified on the downloaded artifact:
  `{"protocol":"garble.replay.v1","names":["Piston","Gizmo","Sprocket","Ratchet","Tinker"],
  "policyNames":["Sprocket",…],"config":{"turns":8,"seed":11,"noiseScale":1.0,"sampled":true,…}}`.
- `replayMatch(config, events).len == events.len + 1`, final frame equal to the live sim's
  `tableStateJson` and `resultsJson` (`test_sim.nim:508-514`, run locally).

**Viewer** (checklist 3, 13, 14, 11)

- All four viewer files are babel's with renames only — `diff`ed: `config.nims` (3 lines),
  `static_replay.js` (7 lines), `index.html` (renames + one `chrome_common.js` script tag + the
  appended banner block), `garble_replay.nim` (symbol/prefix renames + `turns`/`noiseScale`).
  Nothing from bullwhip or any other starter.
- MODULARIZE contract agrees: `replay-viewer/config.nims:38-39` sets `-s MODULARIZE=1
  -s EXPORT_NAME=GarbleReplayModule`; `replay-viewer/static_replay.js:138` calls the factory
  `GarbleReplayModule()`. Exported functions list matches the `gar_*` symbols the shell calls
  (`config.nims:41` ↔ `static_replay.js:94-103`). `emscripten_exit_with_live_runtime()` is present
  (`garble_replay.nim:74-83`).
- Both load signals from the shell's own code: `data-replay-loaded="true"` at the end of
  `attachReplay`'s `makeRenderer` callback after the first synchronous draw
  (`client/renderer.js:1425`, byte-for-byte babel's placement) and `data-replay-error="<message>"`
  in `fail()` (`static_replay.js:56`), removed on a successful retry (107, 134). The 20 s fetch
  timeout is `AbortController`-bounded (`static_replay.js:67-89`). Nothing about audio gates
  either signal.
- The bundle is executed in CI: run **32700138054**, job `wasm-viewer` (id 97350078918),
  `needs: docker-smoke` (`ci.yml:212`), step "Load the bundle in a real browser" ran
  `node tools/ci/viewer_smoke.mjs --bundle … --replay dist/smoke/replay.json --timeout 90 --soak 10`
  and printed `{"loaded":true,"ms":287,"clock":"TURN 2 / 8 · STORM 95% · STATIC BURST · WAITING ON 2",
  "scorebug":"Sprocket 300 CREDITS 1.00× …","feed_lines":221}`,
  `soak: 10s of playback kept advancing`, and three differing scrub readouts
  (0 % "TURN 2 / 8 …", 50 % "TURN 5 / 8 · HAZY 30%", 100 % "FINAL — WIDGET 1.90×").
  No `continue-on-error` on the step. (The soak line's `(null -> null -> null)` is the *tick*
  probe, which Garble has no readout for; `advanced()` in `viewer_smoke.mjs:402-403` passes on any
  of clock/tick/scorebug, and the clock moved.)
- `client/chrome_common.js`: every one of the 15 functions and all 8 palette constants is
  character-identical to `cogame-babel/client/renderer.js`'s (checked programmatically by
  brace-matched block extraction — 15/15 SAME, constants identical, `makeNameMap` including its
  third `glyphs` parameter and `.glyph` accessor). The only additions are the IIFE wrapper, the
  `window.GarbleChrome` export (224-249) and the one marked `relayout()` (206-219), which measures
  `#topband`/`#transport` with `getBoundingClientRect()` and writes `--topband`, `--band` and
  `--hudscale` on `document.documentElement`, on `load` and every `resize` (221-222).
- `client/chrome.css`: `diff` of the first 443 lines against the starter's is empty; everything
  Garble adds is below `/* ---------- garble additions ---------- */` at line 445. The CI job
  re-checks this against `raw.githubusercontent.com/Metta-AI/cogame-babel/main/client/chrome.css`
  (`ci.yml:356-367`) and passed.
- `client/replay_broadcast.html` is babel's `client/replay.html` (74 lines) with the renames, the
  one inserted `chrome_common.js` tag before `renderer.js` (37-38), and the banner-marked game
  block appended before `</body>` (75-115) that adds only the `♪ STATIC` button *inside* the
  existing `.tbar` and the `#legend` strip before `#transport`. Every starter id is present
  (`#layout #stage #topband #wordmark #clock #topright #statuschip #feedtoggle #scorebug
  #board-wrap #table #lightpool #grain #endscreen #transport #scrub .tbar #play #pos #feed
  #loading`); no `#viewpanel`, zoom bar or minimap anywhere.
- Transport rules: `--band`/`--hudscale` land on `:root` (F-conformant `relayout`), the appended
  CSS pins `#endscreen { bottom: var(--band, 0px); }` (chrome.css:528) and `#endscreen` lives
  inside `#board-wrap`, a sibling above `#transport` (replay_broadcast.html:20-32). The endcard is
  shown with the class its rule uses (`#endscreen.show`, chrome.css:381 ↔ `classList.toggle("show",
  …)`, renderer.js:759) and every seek takes it down, because `setIndex` calls `updateEndscreen`
  on every index change (renderer.js:1393) and the toggle is that function's first statement.
- Scrubber beats are `<button type="button">` with `aria-label`, `title` and an `onclick` that
  seeks (`renderer.js:991-1006`), one per event (1074-1081), alongside kept drag-to-seek
  (1087-1107) and one `.round-span` per turn (1055-1072). Every emitted class has CSS:
  `start turn turn.burst say say.silent confirm deal deal.misheard void end`
  (chrome.css:470-522) plus the seat colours (`.seat0…seat4`, chrome.css:205-209).
  No game-block function shares a name with a `GarbleChrome` key (checked by hand and by the CI
  step at `ci.yml:316-355`, which passed).
- 360 px legibility: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (chrome.css:452) and
  `@media (max-width: 640px) { .plate-label { display: none; } … }` (461-467); `fit()` on resize is
  kept verbatim in both pages; compact composition at < 560 px in `layoutOf`/`cogSpots`/`drawTape`
  (renderer.js:42, 77-84, 520); words and numerals throughout (`ORE`, `1.42×`, `MISHEARD`).
- Both name spaces: agents see only aliases — `tableNames` (sim.nim:114-125) from babel's
  `CogNames` pool, and `systemPrompt`/`userPrompt` are asserted to contain the seat's alias and
  **none** of the five policy display names (`test_sim.nim:618-631`, run). Spectator side,
  `makeNameMap(payload.names, payload.policyNames)` maps aliases to policy names for non-baseline
  seats (renderer.js:1347), while `resultsJson.names` are policy names (sim.nim:623) — confirmed on
  the artifact (`names` aliases vs `results.names` policy names).

**Manifest, packaging, CI** (checklist 3, 6, 10, 12)

- `"replay_viewer": {"bundle": "static-replay-viewer"}` (manifest:15-17); no pod replay URL in the
  manifest. `tools/build_replay_viewer.sh` exists, is committed `755`, is babel's hook with paths
  renamed, `mkdir -p "$(dirname "${output_dir}")"` before the first copy (line 22), and keeps the
  final `grep -q 'data-replay'` assertion (line 64).
- `num_agents: 5` in all three variants (manifest:399, 429, 459) and in
  `certification.game_config` (487); `certification.players` names five slots covering all three
  declared runnables (495-511); `game_config.players` is five (470-486). `tools/ci/docker_smoke.sh`
  carries the four seat-count invariants plus the `SMOKE_SEATS` cross-check, all prefixed
  `SEAT-COUNT FAIL:` (lines 108-152), unmodified from the template; `SMOKE_SEATS` default is `5`
  (line 54). **Zero occurrences of `SEAT-COUNT FAIL` in the docker-smoke log** of run 32700138054
  (grepped); the job printed `game=garble seats=5 …` and
  `smoke OK: seats=5 results=438B replay=14090B reason=complete`, plus
  `every player container exited 0` (the one appended assertion, lines 243-269, bounded by a 60 s
  deadline).
- `config_schema`: `additionalProperties: false`, `required: ["tokens","players"]`, every array
  property carries `minItems`/`maxItems`, and every property/bound/default in the note's table is
  present with the note's values (manifest:31-140), matching `defaultGameConfig`
  (`types.nim:85-97`). `results_schema` matches `resultsJson` key for key with
  5-item arrays, `scores` 0…10, `units` 4-item integer arrays, `maxTurns ≥ 6` (manifest:141-281).
- `game.protocols` carries **both** `player` and `global` (manifest:282-285); the global text
  states the commodity indexing, `channel:-1 = radio`, the append-only transcript, "HEARD TEXT IS
  DERIVED, NEVER TRANSPORTED", and `index.html?replay=<url>`. `game.docs.pages` has the two entries
  with the full scanner spec, neighbour table, worked admissibility examples and the scoring
  formulas (see F2 for the `readme` shape).
- Eight tags (≥ 3), `episode_timeout_minutes: 20`, `owner`, `source_url`,
  `env.ANTHROPIC_API_KEY_URI: "secret://coworld/garble/anthropic_api_key"` (manifest:27),
  three `player[]` runnables with the note's ids/names/envs/resources.
- `compose.yaml` service is `garble` and the manifest placeholder is `{{GARBLE_IMAGE}}`;
  `Dockerfile` and `Dockerfile.replay-viewer` are babel's with `babel`→`garble` substituted (both
  diff clean under `sed`); `nimby.lock` is byte-identical to babel's; `garble.nimble` has the
  note's version and requires.
- All three workflows present and template-identical apart from the `<slug>`/`<IMAGE>`/`<SEATS>`
  substitutions, the `--soak 10` addition and the chrome provenance step in `ci.yml`, and the one
  appended player-exit assertion in `docker_smoke.sh`. `tools/ci/viewer_smoke.mjs` is byte-verbatim.
  The placeholder gate (`grep -n '<slug>\|<IMAGE>\|<SEATS>' …`) exits 0 — run and confirmed.
  `coworld-release.yml` order is build (159) → certify (167-175) → **upload policies (206)** →
  upload-coworld (304) → secret put (342).
- `tools/ci/policies.json`: four policies — two `PLAYER_PROMPT` champions with materially different
  strategies (`garble-signal` protocol-discipline, `garble-shortwave` terse/bait/steal), champion
  #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, plus the two
  `PLAYER_SCRIPTED` fillers.
- CI green on `main` at the reviewed tree: `gh run list -R Metta-AI/cogame-garble --branch main -w
  ci.yml` → **32700138054 `success`** (jobs `test`, `docker-smoke`, `wasm-viewer` all ✓). No test
  file was touched after the initial fork commit: `git log --oneline -- tests/` returns only
  `f1aeb04`, so nothing was deleted, skipped or loosened during this run.

---

## Could not determine

- **Whether `game.docs.readme` as a bare string passes the platform's manifest schema** (F2). The
  `$schema` URL is not reachable from this sandbox and no local copy of
  `coworld_manifest_schema.json` exists. What would settle it: a `coworld certify` run (the
  release workflow's step 167-175), or the schema file itself.
- **Whether the hosted league episode stays inside 720 s with real model latency.** Every bound is
  present and the arithmetic checks out on paper (F19 and the budget item above), but no LLM-backed
  episode exists to measure — CI runs with no credentials. What would settle it: a hosted episode's
  log with the per-turn `garble: turn N … at Ms` lines.
- **Whether the note's "baseline tuned with a grid harness" (checklist 7) was done off-tree** (F17).
  The tree carries the two 200-seed comparison tests and their echoed means, and nothing else.
- **F21's unguarded game thread** is reasoned about, not observed; I found no reachable raise.
