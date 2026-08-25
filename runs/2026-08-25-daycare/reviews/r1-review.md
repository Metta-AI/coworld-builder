# r1 review — 2026-08-25-daycare

Range: `0cd19b1..12d58b5` (bootstrap → `Endcard: sum the per-slot wasted/reaches arrays`), reviewed at
`12d58b593a005e8b6498c7833b4efc0815302c3f` on `main`.
Files read: 46 (all of `src/`, all of `tests/`, all of `client/` + `replay-viewer/` diffed against
`/workspace/starters/coworld-ctf`, `coworld_manifest_template.json`, `tools/ci/*`,
`tools/build_replay_viewer.sh`, both Dockerfiles, `daycare.nimble`, all three workflows) plus the
`ci.yml` run 32853852532 job logs for `docker-smoke` and `wasm-viewer`.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision
addendum).

Labelling convention below: **observed** = I read it in the file at the cited line; **inferred** = I
reasoned from what I read; **untested** = it would need a run to settle.

---

## Blocking

### B1 — `game.config_schema` caps `tokens` and `players` at **one** item in a two-seat game, so the manifest's own variants and certification fixture violate the schema the same file declares
- Where: `coworld_manifest_template.json:39-48` (`tokens`), `:49-66` (`players`);
  violated by `:486-493` (`variants[0].game_config.players`, 2 entries), `:509`, `:532`, `:555`
  (the other three variants) and `:576-583` (`certification.game_config.players`, 2 entries).
- Observed:
  ```json
  "tokens":  { "type": "array", "minItems": 1, "maxItems": 1, "items": {...} }   // :39-48
  "players": { "type": "array", "minItems": 1, "maxItems": 1, "items": {...} }   // :49-66
  ```
  while every `game_config` in the same document carries two:
  `"players": [{"name": "Alder"}, {"name": "Bramble"}]` (`:486-493`, `:509`, `:532`, `:555`, `:576-583`).
  The runtime config the smoke writes is also two-of-each — `tools/ci/docker_smoke.sh:156-157`:
  `config["players"] = players[:seats]` / `config["tokens"] = [f"token-{i}" for i in range(seats)]`
  with `seats == 2` (confirmed in the CI log: `game=daycare seats=2 config={"players": [{"name":
  "Alder"}, {"name": "Bramble"}], ... "tokens": ["token-0", "token-1"]}`) — and the server refuses to
  start with fewer: `src/daycare/server.nim:529-530`
  `if config.tokens.len < 2 or config.players.len < 2: raise ... "daycare needs 2 tokens and 2 players"`.
- What the note says: `design.md:952-954` — "`game.config_schema` properties: `tokens` (string array,
  `minItems 1`, `maxItems 2`, required), `players` (array of `{name}`, `minItems 1`, `maxItems 2`)".
  Both maxima are **2** in the note.
- Why nothing catches it: `tests/test_manifest.nim:151-170` asserts only that every array property
  *has* `minItems` and `maxItems` (the `want = 2` exactness argument is passed for
  `results_schema` only, line 170), so `maxItems: 1` is green.
- Checklist item: 10, "**Manifest validates.**" *(category: manifest)*. Note honestly: item 10's
  spelled-out conditions are about `game.docs` shape and both `game.protocols` — **those two are
  satisfied** (see Traced §M). The finding is against the item's subject ("manifest validates"): the
  manifest declares a JSON-Schema that its own four variants and its own certification fixture fail.
- Why blocking: a validator that applies `game.config_schema` to `game_config` rejects all four
  variants and the certification fixture; if nothing applies it, the schema is a wrong public
  contract for a two-seat game (a policy author reading it is told one seat). Which of the two
  happens is **untested** here — see Could-not-determine C1.

No other finding in this review falsifies a checklist item.

---

## Non-blocking

### N1 — the repaired `shrubRegrowTicks` is one rung past the value the note's ladder names
- Where: `src/daycare/sim_types.nim:39-41`, `:52`.
- Observed: `DefaultShrubRegrowTicks* = 480`, with the comment "`(d) shrubRegrowTicks 240 -> 480 (one
  step beyond the named 320; 320 alone left gate (b) at 0.82 on daycare-fickle)`".
- Note: `design.md:336` — "(d) `shrubRegrowTicks 240 → 320`, then `childShrubPickPermille 250 → 150`".
  The ladder's next rung after 320 is the per-mille, not a larger regrow. The note also says
  "**That test is the enforcement, not this table**" (`design.md:338`) and `tests/test_feasibility.nim`
  does gate all six outcomes, which is why this is advisory rather than blocking. The other three
  repairs (`ticksPerTurn 48→60`, `tallRegrowTicks 36→24`, `fruitLifetime 120→96`,
  `sim_types.nim:46,50,55`) are exactly the note's named rungs, and `rewardOther` stayed 1
  (`:58`), `basketCapacity` 2 (`:56`), the per-mille 250/150 (`:53`, manifest `:517`) and the 6..9
  switch window (`:93-94`) as the note requires.

### N2 — the note's derived episode numbers are now stale (inherited from N1's `ticksPerTurn 60`)
- Where: `src/daycare/sim_types.nim:46` (`DefaultTicksPerTurn* = 60`), manifest `:494` etc.
- Observed consequence: an episode is 15 × 60 = **900** ticks / 37.5 s of video, not the note's
  "720 ticks … 30 s of video" (`design.md:199-200`); the certification fixture is 6 × 60 = **360**
  ticks / 15 s, not "6 × 48 = 288 ticks = 12 s" (`design.md:1012`). Both move the right way for the
  10 s soak gate, and the CI readout confirms it: `clock: "TURN 5 / 6 TICK 242 OF 359"`, soak
  `"2 / 359" -> "194 / 359" -> "242 / 359"` (run 32853852532, `wasm-viewer`). `tests/test_manifest.nim:73-78`
  re-derives the ≥12 s requirement from the fixture rather than hard-coding 288, so the drift is
  self-checking. No in-repo document repeats the stale numbers.

### N3 — the move cooldown gates moves only, not the whole tick
- Where: `src/daycare/kernel.nim:263-275`.
- Observed: `if sim.cogs[seat].fumbleCd > 0: return aWait` (fumble gates everything), then
  `if intent in {aMoveN..aMoveW} and sim.cogs[seat].moveCd > 0: return aWait` — a `pick` is legal on
  every tick.
- Note: `design.md:209-210` step 2 says "A cog whose `moveCooldown` counter **or**
  `childReachCooldownTicks` fumble counter is still running emits `wait` instead", but
  `design.md:132` ("`move_*` is legal only every `moveCooldown = 2` ticks … an illegal move degrades
  to `wait`") and `design.md:180` ("on arrival `pick` **every tick**") require exactly what the code
  does. The note contradicts itself; the code follows the two specific statements. The in-code
  comment (`kernel.nim:265-267`) says so.

### N4 — the shrub-pick coin is seeded off `rngSecret`, which the note says can never happen
- Where: `src/daycare/sim_state.nim:110-112`, used at `src/daycare/sim.nim:127`.
- Observed: `result.pickRng = seededRng(int(result.rngSecret.nextU64() and 0x7FFF_FFFF'u64))`, and the
  child's shrub success is `sim.pickRng.chancePermille(...)` — an outcome the parent sees as a `reach`
  event and in `reachFails`. The same docstring says both "rngSecret … -> the preference, the switch
  turn, **the picks**" (`:90-91`) and "**Nothing the parent can observe is ever drawn from
  rngSecret**" (`:92`); those two sentences contradict each other.
- Note: `design.md:100-105` — "Nothing the parent can observe is ever drawn from `rngSecret` … which
  is what makes 'the parent cannot see it directly' true of the *bytes*."
- Inferred, and this is why it is advisory: the preference *value* does not move the stream —
  `rand(2)` consumes exactly one `nextU64()` whatever it returns (`sim_types.nim:320-323`) — so pick
  outcomes are independent of the preference **given the seed**; both are functions of the same seed,
  which leaves only a brute-force-the-seed channel (seed space is 31 bits, `src/daycare.nim:16-21`)
  against ~10 bits of observable pick outcomes per episode. `tests/test_noleak.nim:98-118` cannot see
  this either way, because with `forcePreference` set the `rand(2)` draw is skipped for **both**
  branches (`sim_state.nim:102-104`), so both forced runs share one `pickRng` by construction.

### N5 — the live `/global` stream carries the child's preference from tick 0, and `/global` takes no token
- Where: `src/daycare/broadcast.nim:159` (`result.preference = sim.preference`) → `:111-117`
  (`state["secret"] = {"pref": $input.preference, …}`); route `src/daycare/server.nim:525`
  (`result.get("/global", globalUpgrade)`) and `:443-457` (`globalUpgrade` upgrades with no token
  check, unlike `playerUpgradeHandler:419-425`).
- Observed: the spectator frame is emitted every turn from the first broadcast
  (`server.nim:138-151`, called at `:260` before turn 1), and it contains `secret.pref`.
- Note: `design.md:697-698` says the `secret` block "is written **after** the episode, so no player
  process can ever read it" — true of the replay (`src/daycare/replays.nim:107`, written in
  `finishEpisode`), but the same value is on the live socket during play. A player container is given
  `COWORLD_PLAYER_WS_URL` (`tools/ci/docker_smoke.sh:218`), i.e. the host:port that also serves
  `/global`. **Inferred**: a policy image that opened `/global` instead of only `/player` would read
  the preference mid-episode. Nothing in the shipped player does this
  (`src/daycare_player.nim:47-48` connects to the one URL and only listens), and no checklist item
  covers it (item 4 is about name spaces, which is satisfied).

### N6 — a child reach at a **bare** tall tree emits nothing
- Where: `src/daycare/sim.nim:109-115` — the adjacent-source scan does
  `if sim.yard.sources[si].ripe < 1: continue`, so with no ripe fruit `chosen < 0` and the tick
  degrades to `wait` with no `reach` event, no `reachAttempts` and no `reachFails`.
  `src/daycare/kernel.nim:231-232` walks the child there anyway (`requireRipe = false`).
- Note: `design.md:114` — the child "**never**" harvests a tall tree and "the attempt **is** the
  'reach'"; `design.md:1036-1037` — "the child's tall-tree pick **always** fails and emits `reach`".
  Observed: it fails silently when the canopy is empty, so the signalling surface goes quiet exactly
  when the child is trying hardest. With `TallInitialRipe = 2`, `tallCapacity 3` and
  `tallRegrowTicks 24` (`sim_types.nim:49-50,61`) a tree refills every 24 ticks, so the window is
  short; `tests/test_sim.nim:113-138` forces `ripe = 3` and so never exercises the bare case.

### N7 — step 3's "the other cog already took it" clause degrades to the source scan, not to `wait`
- Where: `src/daycare/sim.nim:96-117`.
- Observed: seats resolve in slot order and `sim.groundAt` is re-read per seat, so when slot 0 takes
  the fruit, slot 1's `here` is `-1` and execution falls through to the orthogonal-source scan
  (`:107-115`) and may pick from a tree/shrub in the same tick.
- Note: `design.md:213` — "A `pick` of a ground fruit the other cog already took this tick degrades
  to `wait`."

### N8 — the caretaker's final tie-break is "nearest source to the child", not "apple"
- Where: `src/daycare/scripted.nim:41-61` (`caretakerGuess`), helper `:32-39`.
- Observed: after the `w(f)` comparison and the `adjacentTicks` tie-break, the last rung is
  `nearestSourceDistance(fApple)` vs `(fBanana)` from the **child's** cell, `apple` only on a further
  tie. The rationale is in the code (`:53-56`): a flat "apple" opens correct in every apple episode,
  which is what gate (f) measures.
- Note: `design.md:556-557` — "on a further tie, `apple`". Both values are inside the enum, so
  `tests/test_baseline.nim:38-51` is unaffected; the substantive claim ("species-neutral across
  seeds") rests on the layout congruence and the mirror bit, which `tests/test_noleak.nim:139-184`
  does pin.

### N9 — feasibility gate (c)'s accuracy band is measured pooled, and pooling can mask a per-variant miss
- Where: `tests/test_feasibility.nim:14-22` (the stated reading), `:103-104` (`accHit`/`accTotal`
  accumulate across the variant loop), `:122-126` (one `gate(...)` after the loop).
- Note: `design.md:323-325` — gate (c) reads "…and the parent's guess accuracy over the episode lands
  in 0.35..0.65", inside a per-variant list.
- Observed and **inferred**: the header argues pooling "makes the gate tighter, not looser". That is
  true of estimator noise (48 episodes vs 12) but **not** of per-variant compliance: one variant at
  0.30 offset by another at 0.60 pools to 0.45 and passes, where four per-variant gates would fail.
  The band itself is unchanged. Every other gate (a),(b),(d),(e),(f) is evaluated per variant
  (`:87-120`) as the note says, and (f) is evaluated across all four (`:129-138`), which is what the
  note asks for there.

### N10 — no-leak gate (a) is implemented as a key walk plus a turn-1 byte-identity test, not the note's byte grep
- Where: `tests/test_noleak.nim:65-96` (walks `keysOf(...)` for banned **keys**) and `:98-118` (gate
  a2: the parent's turn-1 frame is byte-identical under `forcePreference` 0 and 1).
- Note: `design.md:1047-1049` — "(a) The parent's `state` frame **bytes** … contain neither the string
  `preference` nor the preference value in any field the parent reads".
- Observed why the literal test is impossible as written: the parent's own rules block contains the
  word — `src/daycare/sim.nim:538` `"hidden": "the child's preference is not shown to you anywhere"` —
  and every `sources[]` row contains the value `"apple"`/`"banana"` (`sim.nim:419-426`). The test says
  so at `:65-69`. Gate (a2) is a stronger property than the note's grep for the only turn where no
  behaviour exists yet; after turn 1 the frames legitimately differ.

### N11 — a 429 is retried inside the same turn rather than deferred to the next turn's batch
- Where: `src/daycare/llm.nim:399-402` (429 raises `DaycareError`), caught at `:527-531`, so the seat
  lands in `stillOpen` and rides `attempt == 1` of the same turn; `tests/test_llm.nim:330-333`
  asserts `run.hits == 4` for `smThrottled`, i.e. two batches in one turn.
- Note: `design.md:589` — "429 is logged and the seat is retried in the **next** turn's batch."
  Consequence observed: one extra request per throttled seat per turn (still inside the "≤ 30
  retries" the note budgets at `design.md:371`) and the seat still falls back to `caretaker` in the
  same turn, so nothing hangs.

### N12 — checklist item 2's first clause has no analogue here, by design, and no test compares reloaded frames element-wise
- Where: `src/daycare/replays.nim:1-11` (state, not inputs), `:149-227` (`loadReplay` hydrates
  frames), `src/daycare/broadcast.nim:198-255` (`replayChromeInput` reads only the `ReplayPlayer`),
  `replay-viewer/daycare_replay.nim:49-53` (`renderCurrent` = `snapshotAt(tick)` +
  `replayChromeInput`).
- Observed: there is exactly **one** recording and the viewer reads it — the board from `frames[]`
  (`replays.nim:256-298`), the scores from `frames[i].c[3]/c[7]` (`:300-304`), so the anti-pattern
  item 2 targets ("a parallel recording") is not present. Determinism is pinned separately by
  `tests/test_sim.nim:403-417` (`gameHash` identical for the same seed twice in-process and in a
  fresh sim), and the replay→chrome path by `tests/test_broadcast.nim:136-166` and `:168-196`.
- What is **not** asserted anywhere: `frames[i]` re-read from the JSON equals `sim.frames[i]`
  field-by-field (`tests/test_replay.nim:94-109` checks lengths, encoding widths, `names`,
  `preference` and one snapshot at `maxTick`), and `series.score`/`series.guessRight`/`beats`/`events`
  — which the viewer also reads (`broadcast.nim:214,227-231`, `replays.nim:216-222`) — are recorded
  beside the frames rather than derived from them (both come from the same sim values in
  `sim.nim:250-254` and `sim.nim:350`, so they agree by construction, untested).
- Note: `design.md:658-660` chooses this explicitly ("Daycare records *state*, not inputs, so playback
  never re-simulates"), which is why I do not read item 2 as falsified.

### N13 — `canvas_text` is structurally 0 on both smoke steps, and the renderer fixture measures its own replica CSS rather than the shipped page
- Where: CI run 32853852532, `wasm-viewer`: bundle step `canvas text: 0 drawn, 0 never inside the
  canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`; fixture step the same
  numbers. `tools/ci/viewer_smoke.mjs` is byte-identical to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (verified by `diff`) and hooks only
  `CanvasRenderingContext2D.prototype.fillText/strokeText` (`:414-415`).
- Observed why 0 is expected here: the only text the **board** draws is the cog alias, and it is a
  server-side sprite (`src/daycare/art.nim:195-226` `textSprite`, blitted at
  `src/daycare/global.nim:257-264`), not a canvas `fillText`; the bundle additionally renders in a
  Worker/OffscreenCanvas (`replay-viewer/static_replay_worker.js:71`), which the main-thread hook
  cannot see. Every LLM string lives in the DOM chrome — the feed row
  (`client/replay_broadcast.html:1520-1529`) and the secret panel (`:1674-1716`). The checklist says
  so itself: "`total: 0` means the check covered nothing … and is not evidence of anything."
- The fixture (`tools/ci/renderer_fixture.html`) does exist, is driven by
  `viewer_smoke.mjs --strict-text-bounds` in its own step (`.github/workflows/ci.yml:335-344`), loads
  the **real** `client/chrome_common.js` and `client/broadcast_core.js` (`:185-186`), builds an
  80-rune `hunch` and a 240-rune `notes` on both seats (`:205-206`), self-checks those rune counts and
  the 15-chip tape (`:215-216`, `:301`), renders at 360/620/1152 (`:412`) and sets
  `data-replay-loaded` only after all three (`:441`). Three gaps I observed:
  (a) it re-declares the chrome CSS inline (`:30-118`) instead of loading
  `client/replay_broadcast.html`, so the shipped `#care-secret`/`.feed-row`/`@media` rules are not the
  ones measured; (b) it resizes `#stage` in px, and `@media (max-width: 640px)` keys off the
  **viewport**, so the shipped 360 px plate/subline collapse (`replay_broadcast.html:1171-1174`) is
  never triggered by any gate; (c) it renders a `.care-hunch` block (`:146`, `:293`) and a feed
  `.notes` span (`:319`) that the shipped page never emits — the shipped feed row carries the `hunch`
  inside its text and no `notes` at all (`:1520-1529`). So the fixture proves "the real chrome runs
  with full-cap strings without throwing", not "the shipped boxes fit them".

### N14 — `#viewpanel` is fully gone, but the canvas's own zoom handlers still call `core.zoomAt/setZoom`
- Where: removed — markup/CSS/ids/JS (`grep` for `viewpanel|minimap|zoombar|zoom-|fpv|povBadge|mmwarn`
  over `client/replay_broadcast.html` returns nothing; `tests/test_broadcast.nim:277-281` asserts it,
  including `attachMinimap`'s caller, `syncViewUi` and the keyboard pan). Still present:
  `client/replay_broadcast.html:2893` (wheel → `core.zoomAt`), `:2910` (gesture → `core.setZoom`),
  `:2965-2966` (pinch → `zoomAt`/`panBy`), `:2979` (drag → `panBy`), `:2996` (dblclick →
  `resetView`).
- Checklist 14's last bullet names "the `core.zoomAt/setZoom/attachMinimap` wiring" among what a
  fixed-arena game removes with the panel. Read as "the panel's wiring", this is satisfied; read
  literally as "every call", it is not. The note pulls the other way: its removal list
  (`design.md:818-829`) covers only `#viewpanel`/`#fpv`/`#povBadge`/`#mmwarn`, and "Everything else …
  is the starter's, unchanged" (`design.md:830-836`). I am recording the tension rather than picking
  a side.

### N15 — the game block puts two elements inside the starter's own markup
- Where: `client/replay_broadcast.html:1366-1379` (`#care-layer` inserted where `#viewpanel`/`#fpv`
  were, before `#transport`) and `:1423` (`<div id="care-endcard">` inside the starter's `#endcard`,
  between `#ec-teams` and `#ec-replay`).
- Note: `design.md:816-829` lists exactly three edits "inside the starter's own markup/script" and
  says the appended block is "appended under a banner comment". Both insertions carry the banner
  comment (`:1359-1365`) and both are inert to the starter's own JS (the endcard panel is filled from
  the wrapper at `:1781-1794`; `#ec-teams` is hidden by CSS at `:1286` rather than removed, so
  `ensureEndcardTeams` keeps working). The board region is where the note requires the panel to be
  (`design.md:872-879`), so there is nowhere else it could go.

### N16 — `careFeed` mirrors `pushFeed`'s signature but not its speed-aware timing
- Where: `client/replay_broadcast.html:1503-1518` (fixed `250ms` animation, fixed `3200ms` dwell) vs
  the starter's `:2526-2537` (`250 / animFactor()` and `dwellFloor('feed')`).
- Observed: the one-argument signature, the insert-at-head order and the `CARE_MAX_FEED = 4` cap
  (`:1457`) match the starter's `MAX_FEED = 4` (`:2525`), so the cogball 0.1.4 hazard the note names
  (`design.md:882`) is avoided; only the fast-forward dwell scaling is dropped. **Inferred** effect:
  at 8×/16× a daycare row holds for the same wall-clock 3.2 s the starter would have stretched.

### N17 — `docker_smoke.sh` checks the shape of `results.json`, not the declared `results_schema`
- Where: `tools/ci/docker_smoke.sh:299-308` (only `len(results[key]) == seats` for `names`/`scores`,
  plus a printed `reason`).
- Note: `design.md:1102` — docker-smoke "validates `results.json` against the results schema". The
  property is covered elsewhere: `tests/test_manifest.nim:187-211` validates a real `resultsJson()`
  against `game.results_schema` key by key, enum by enum, in-process. The smoke script is the
  template's own file otherwise.

### N18 — two board details the note describes are not drawn
- Where: `src/daycare/global.nim:190-203` emits one tree sprite per source keyed by ripe count
  (`src/daycare/art.nim:228-236`, three canopy states) — there is no separate "count pip"; `:222-254`
  swaps the whole cog body for `cog_*_carry_apple/banana` rather than drawing the fruit sprite over
  the head.
- Note: `design.md:860-866` — "a small ripe-fruit cluster in the canopy **and a count pip**" and "the
  carried fruit drawn as a sprite **over the head**". The information is on screen either way (ripe
  count via the canopy state, the carried species via the body art); the mechanism differs.
  Everything else in that paragraph checks out numerically: trees are 77 px = 1.60 cells
  (`data/tree_*.png`), shrubs 34 px, ground fruit 20 px, parent drawn 40 px and child 28 px
  (`global.nim:238`), blink in the last 24 ticks of `ttl` (`global.nim:40`, `:209`), reach puff +
  waste cloud + alias under the feet (`:257-291`).

### N19 — no grid harness is committed for the tuning claim
- Where: `src/daycare/sim_types.nim:29-44` — "a sweep of the ladder's parameter space found exactly
  one region where all six gates hold on all four variants, and this is it". `ls tools scripts` and a
  repo-wide grep for `sweep|grid|harness` return only that comment (and
  `tests/test_feasibility.nim`, which evaluates the outcome, not the search).
- Checklist 7's second sentence is "The baseline's parameters were tuned with a grid harness, not
  guessed." What the tree does prove: the six gates hold over 4 variants × 12 seeds × 6 pairings
  (`tests/test_feasibility.nim:27,73-138`) and CI is green on it. What it does not contain: the
  harness, or a cited run of one. Also unswept-in-tree: the caretaker weight coefficients
  `3·reachFails + 2·groundPasses + adjacentTicks + 4·ate` (`src/daycare/scripted.nim:25-30`).

### N20 — scrubber beats are `role="button"` divs upgraded in place, not literal `<button>`s
- Where: `client/replay_broadcast.html:1626-1653` (`careUpgradeBeats` sets `role`, `tabindex`,
  `aria-label`, `title`, a click handler and an Enter/Space handler, each seeking `el.__tick`),
  `:1595-1605` (`buildCareBeats` → `chrome.markBeat(b.t, b.k, '')`), CSS for all five kinds at
  `:1277-1281`.
- Observed why: `client/chrome_common.js:538-562` creates `document.createElement('div')` and takes
  `(tick, kind, team)` — three arguments, not four — and that file ships byte-for-byte
  (`diff` against the starter: identical), so the element type cannot be changed there.
  Checklist 14(d)'s substance (labelled, seeks to its tick, CSS for every emitted kind) is met;
  its literal "`<button>`s" and 4-arg signature are not available in this starter.

### N21 — the `final`-frame no-leak test asserts against a copy of the server's object literal
- Where: `tests/test_noleak.nim:190-204` rebuilds the frame inline ("This is the exact object
  src/daycare/server.nim sends as `final`") rather than calling the server; the real one is
  `src/daycare/server.nim:187-196` (which additionally sets `final["slot"]`, `:198`).
- Observed: the two agree today — neither carries `preference` — but a future edit to `server.nim`
  would not fail this test.

### N22 — the player's receive loop is a blocking read with no explicit timeout
- Where: `src/daycare_player.nim:58-66` — `while true: let received = socket.receiveMessage()`.
- Observed mitigations: whisky raises on a close or truncated frame and the whole loop is wrapped to
  exit 0 (`:52-57`, `:84-89`); the game always sends `final` before writing artifacts
  (`src/daycare/server.nim:184-199`); `tools/ci/docker_smoke.sh:253-269` fails if any player container
  has not exited 0 within 60 s of the game, and the CI log shows `all 2 player containers exited 0`.
  Checklist 5's "every wait … has an explicit bound" is about the **episode**, and every wait on the
  game side does have one (Traced §W); I record the player-side read because it is a blocking read
  by the letter of the item.

### N23 — `feed_lines` in the smoke JSON is structurally 0 for this repo
- Where: `tools/ci/viewer_smoke.mjs:425` selects `#feed, .feed, #log`; daycare's feed is the
  starter's `#killfeed` (`client/replay_broadcast.html:1357`). Both CI steps report
  `"feed_lines":0`. Not a defect in the repo (the template is shipped verbatim, as the note requires),
  but the number carries no signal here and should not be read as "the feed is empty".

---

## Traced and consistent

**Resolution rules**
- `src/daycare/sim.nim:256-341` — the nine steps run in the note's order (`design.md:206-231`):
  regrow `:261-270`, kernel intent `:272-275`, `pick` `:277-280`, `drop` `:282-285`, `eat` `:287-295`,
  moves `:297-299`, ageing `:301-313`, accounting `:315-336`, record `:338-341`; seats iterate
  `for seat in 0 .. 1` in every step, sources in `yard.sources` order, which
  `src/daycare/yard.nim:126-148` builds tall-then-shrub sorted by `(row, col)`.
- Reach table (`design.md:112-123`) — parent always harvests (`sim.nim:120` gates on `rChild` only);
  child at a tall tree always fails and emits `reach` (`:121-126`); child at a shrub succeeds at
  `childShrubPickPermille` else emits `reach` and takes `childReachCooldownTicks + 1` fumble
  (`:127-132`, decremented at `:335-336`, so exactly 6 subsequent `wait` ticks — asserted at
  `tests/test_sim.nim:184-191`); ground fruit always succeeds for both (`:97-106`);
  `carryCap 1` enforced at `:95-96`; mat fruit `ttl = -1` and never rots (`:153`, `:311-312`); floor
  fruit rots after exactly `fruitLifetime` ticks (`:302-310`, asserted `tests/test_sim.nim:242-263`).
- Scoring (`design.md:244-248`) — `sim.nim:190-203`: `rewardPreferred` / `rewardOther` credited to
  **both** `cogs[0].score` and `cogs[1].score`; a parent that eats destroys the fruit for 0 and emits
  `waste` (`:204-209`); `parScore = 2 * turns` and `win[i] = scores[i] >= par`
  (`sim_types.nim:363-366`, `sim.nim:589`). `tests/test_sim.nim:265-293` and
  `tests/test_feasibility.nim:49-50` pin the mirror.
- Kernels (`design.md:161-195`) — parent `provide` drop-target ladder d≤1 → d≤2 → child's free
  neighbour (`kernel.nim:78-88`), `stock` → mat then mat-adjacent (`:168-189`), `watch` → within
  Chebyshev 2 then `wait` (`:190-196`), `idle` (`:197-198`); harvest order ground → tall → shrub
  (`:121-139`); child `seek` order ground → shrub → tall with `eat` on its own species only
  (`:205-226`), `show` = tall tree of `F`, pick every tick (`:227-235`), `graze` species-blind and
  never a tall tree (`:236-248`), `beg` within Chebyshev 1 of the parent (`:249-259`), `idle`. BFS is
  over walkable cells with N,E,S,W expansion and `(row, col)` tie-break
  (`yard.nim:191-253`, tie-break comment and `n < best` at `:244-246`); determinism asserted
  `tests/test_sim.nim:371-379`.
- End conditions (`design.md:277-290`) — `complete/turn_limit` at `server.nim:343-345`,
  `deadline/deadline` at `sim.nim:399-401` driven from `server.nim:296-302`,
  `forfeit/forfeit` at `sim.nim:403-408` driven from `server.nim:262-271`; no other value is
  reachable, and `results_schema` pins the same three enums (manifest `:180-183` via
  `tests/test_manifest.nim:180-183`).

**Decision path** (checklist 8 + the simultaneous-decision addendum)
- `src/daycare/llm.nim:479-537` — one `RequestBatch` per attempt with **both** open seats posted
  before `makeRequests` (`:503-513`); `client.lastBatchSize = batch.len` is asserted `== 2` on turn 1
  by `tests/test_llm.nim:263-264` and again on a warm second turn at `:295-296`, with a wall-clock
  probe (`:300-303`) that fails if the two 500 ms requests were serialised.
- Tolerant parse: `extractJsonObject` takes the first `{` to the last `}` and tolerates fences and
  prose either side (`llm.nim:347-358`, tested `tests/test_llm.nim:19-34`); retry **once** —
  `for attempt in 0 .. 1` (`:500`) with the hint appended (`:475-477`, `:508-509`) and only the
  failing seats re-posted (`:530-531`); then the `caretaker` order tagged
  `osFallback` (`:532-536`), which reaches the replay as `"source":"fallback"` on the `order` row
  (`sim.nim:60-65`, `events.nim:39-44`) so phase 60 can count it. `tests/test_llm.nim:305-342`
  exercises junk / 429 / 403 / timeout against a real mummy server through the shipped
  `curly.makeRequests` path and asserts the fallback identity, `source`, legality and the 403 disable.
- Role-crossed jobs, a missing parent `guess`, `provide` without `fruit` are all invalid
  (`llm.nim:418-464`, `sim.nim:30-40`), while a `guess` that disagrees with `fruit` is accepted
  (`tests/test_llm.nim:93-99`). Credentials ladder Bedrock → `ANTHROPIC_API_KEY` →
  `ANTHROPIC_API_KEY_URI`, haiku-only, no `output_config.effort` for haiku
  (`llm.nim:97-126`, `:74-81`, `:376-379`); with none the client disables itself and both seats play
  `caretaker` (`:123-126`, tested `tests/test_llm.nim:136-152`).

**Every wait and its bound** (checklist 5) — §W
- connect: `server.nim:231-237`, bounded by `playerConnectTimeoutSeconds` (120, manifest `:501`);
  prompt settle: `:243-253`, bounded 2.0 s; LLM: `makeRequests(batch, client.timeoutSeconds)`
  (`llm.nim:513`) with `llmTimeoutSeconds` 18 clamped 5..60 (`sim_config.nim:86-88`); pacing sleep:
  `paceDelayMs` ≤ `minTurnSeconds` (`llm.nim:466-473`, `server.nim:339-341`); shutdown:
  `sleep(500)` + `sleep(grace * 1000)` with grace ≤ 120 (`server.nim:202`, `:216`). No unbounded loop
  on the game side; the deadline is re-checked at the top of every turn (`:296-302`) against
  `gameStart + episodeTimeoutSeconds * PlayBudgetFraction` = 720 s, with
  `COWORLD_TIMEOUT_SECONDS` honoured when present (`:278-290`, `sim_types.nim:79`).
- Worst-case arithmetic, **inferred** from those bounds: 120 (connect) + 2 (prompt) + 15 × 36
  (batch + one retry) + 18 (llm.nim:16-18's first-batch multiplex penalty) + ~1 (900 ticks of sim)
  ≈ **681 s** to settle, inside 720 s; the 20 s serving grace and the 0.5 s flush follow the artifact
  write. Even the pathological `minTurnSeconds = 60` config cannot overrun, because the deadline
  check settles the episode with `reason: "deadline"`. **Untested** against real Bedrock latency.

**String truncation** (checklist 9)
- `sim_types.nim:270-285` — `cleanText` strips, then `runeSubStr(0, limit - 1) & "…"`;
  `cleanHunch` folds newlines to spaces first. Applied on the parse path (`llm.nim:441-442`) **and**
  again on install (`sim.nim:53-55`), so a scripted or fallback order is truncated too; LLM error
  text is capped at 200 runes before logging (`llm.nim:529`) and the no-JSON diagnostic at 160
  (`llm.nim:353-355`); the player prompt is cut on runes at 4000 (`server.nim:489-490`).
  `tests/test_replay.nim:14-20,71-79` feeds multi-byte runes **at** and **over** both caps and
  asserts `validateUtf8 == -1` on the whole replay and `runeLen <= cap` on every recorded `hunch`
  and `notes`; `tests/test_llm.nim:101-114` and `tests/test_broadcast.nim:116-129` repeat it on the
  parse and the live-frame paths.

**Replay writer**
- `src/daycare/replays.nim:76-113` emits `daycare.replay.v1` with every field the note's schema lists
  (`design.md:662-691`): `seed`, `names`, `policyNames`, `roles`, `colors`, the full `config` block
  including the fence, sources, basket, spawns and all ten rule constants (`:23-62`), the `secret`
  block, per-tick `frames`, `series.score` + `series.guessRight`, `beats`, `events`, `results`.
  Frame encoding is 4 ints per cog / 4 per ground fruit / 2 per source / 2 mat counts
  (`sim.nim:235-254`, asserted `tests/test_replay.nim:93-98`), `frames[i].t == i` (`:338-341`).
  The `secret` block is produced only inside `finishEpisode` (`server.nim:181`), after the last
  player frame.
- `tests/test_replay.nim` covers the note's item 5 in full on all four variants: strict UTF-8,
  `< 8 MiB`, protocol/game/version/seed, `frames.len == ticksPlayed`,
  `series.guessRight.len == turnsPlayed`, `secret.preference` in the enum, every event tick in range,
  `pick`/`reach`/`drop`/`eat` present, exactly `turns` `turn` rows and one `end`,
  `scores[0] == scores[1]`, the reason/ending enums, and a disk round-trip.

**Viewer derivation** (checklist 3, 13, 14)
- Provenance: `client/chrome_common.js` is **byte-identical** to
  `/workspace/starters/coworld-ctf/client/chrome_common.js` (`diff` reports no difference; 838 lines
  both). `client/broadcast_core.js` is also byte-identical — the note called it "forked"
  (`design.md:811-814`), and the board draw instead lives server-side in
  `src/daycare/global.nim` + `src/daycare/art.nim`, emitted through the starter's own sprite protocol
  (bands at z `-32768`, `global.nim:153-170`; chrome smuggled in sprite 4090's label, `:301-303`).
  `tests/test_broadcast.nim:311-319` asserts neither file mentions "daycare"; `:168-196` parses a real
  packet and checks the chrome label and the static bands.
- `client/replay_broadcast.html` is the starter's page (4165 lines) minus the four documented
  removals plus a 435-line game block: the diff is 1739 removed / 654 added lines, and every removed
  hunk I read is `#povBadge`, `#fpv*`, `#viewpanel`/`#minimap`/`#zoombar`/`#zoom-*`, `#mmwarn`, or
  their CSS and JS (`renderPov`, `renderFpv*`, `renderMismatch`, `ingestFpMap`, `syncViewUi`, the
  zoom/minimap wiring, the `?viewpanel=0` opt-out, the FPV art loaders). Sections 1–6 headers survive
  (`:711` "6. END-CARD", the section-5 TRANSPORT header at the top of the first hunk). The two
  re-lettered literals are `>Score<` (`:2374`) and `SCORE` (`:1406`), and `#lockerroom {
  pointer-events: none; }` is the third edit (`:973-974`) — `tests/test_broadcast.nim:271-307`
  asserts all of it plus the presence of the 40 kept ids.
- Transport rules: (a) `relayout()` measures `#scorebug`/`#transport` and sets `--topband`, `--band`
  and `--hudscale` on `document.documentElement` (`:3025-3070`, `root = document.documentElement` at
  `:3039`); (b) the whole appended layer is `inset: var(--topband, 0px) 0 var(--band, 0px) 0` with
  `pointer-events: none` (`:1181-1187`), and the feed/banner lane are the starter's own board-region
  elements; (c) `#endcard` keeps `top: var(--topband)` / `bottom: var(--band)` (`:723-724`), is shown
  with `#endcard.on` (`:735`, added at `:1765`), and comes down on any non-gameover frame
  (`:2266`) and on a backwards tick inside the wrapper (`:1817-1822`) — `tests/test_broadcast.nim:161-166`
  asserts a seek to 0 drops `over`; (d) beats — see N20.
- Static bundle: `replay-viewer/config.nims` differs from the starter's only in the emitted name and
  the `_daycare_*` export list — **no** `MODULARIZE`, **no** `EXPORT_NAME`, keeping `-O2
  ALLOW_MEMORY_GROWTH ABORTING_MALLOC=1 FILESYSTEM=1 ENVIRONMENT=web,worker,node
  EXPORTED_RUNTIME_METHODS=HEAPU8 --preload-file`, and `static_replay_worker.js:164-167` bootstraps
  with `Module.onRuntimeInitialized`. That is the matched pair; `tests/test_broadcast.nim:321-350`
  asserts both halves and that `mismatch_tick` is gone. `static_replay.js:147` sets
  `data-replay-loaded="true"` on the worker's `loaded` message and `:17` sets `data-replay-error`
  from `showFailure` — both from the shell's own code paths.
- CI evidence (run 32853852532, `wasm-viewer` green, `needs: docker-smoke` at `ci.yml:212`):
  `{"loaded":true,"ms":313,"clock":"TURN 5 / 6 TICK 242 OF 359", ...}`,
  `soak: 10s of playback kept advancing ("2 / 359" -> "194 / 359" -> "242 / 359")`,
  `scrub readouts: 0%="TURN 5 / 6 TICK 242 OF 359" 50%="TURN 4 / 6 TICK 196 OF 359"
  100%="FINAL TICK 359 OF 359"` — three different readouts, loaded true, no `data-replay-error`.
  The smoke step carries `--strict-text-bounds` and `--soak 10` and is not `continue-on-error`
  (`ci.yml:293-324`). `viewer_smoke.mjs` is byte-identical to the builder template. There is no
  `/client/replay` route (`server.nim:517-526`; the only textual matches are comments and the
  starter's `broadcast_core.js:196` path table), and the manifest declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}` (`:28-30`) with
  `tools/build_replay_viewer.sh` present, 0755, and carrying the `mkdir -p` fix
  (`:26-27`) plus the renamed image tag and `docker cp` path.
- Legibility at 360 px (checklist 11): `.plate-name, .plate .team-name { flex: 1 1 auto; min-width:
  3.2em; }` at `:1156` and `@media (max-width: 640px) { .plate .plate-sub { display: none; } .plate
  .lives-label { display: none; } }` at `:1171-1174`, asserted `tests/test_broadcast.nim:301-303`;
  `#stage.tiny` at `boardW <= 620` (`:3062`) shrinks the panel and the chips to 6 px
  (`:1305-1308`).

**No-leak properties**
- Parent frame (`sim.nim:475-539`): no `preference`, `rewardPreferred`, `rewardOther`, `switchTurn`,
  `seed` or `shrubPickChancePermille` key; the child block carries only cells, carry, score and the
  sim-computed counters (`sim_state.nim:199-214`, which has no `hunch`/`notes`/order field); `notes`
  is the parent's own (`sim.nim:500`); history rows carry the parent's own past guesses only
  (`:441-455`). Child frame: `historyJson(rChild)` omits `guess` entirely, no parent order, no
  parent `hunch`/`notes`, plus its own preference and the two reward values (`:540-578`).
  `tests/test_noleak.nim:37-96` plants unique multi-byte markers in each seat's `hunch`/`notes` for a
  whole episode on all four variants and asserts neither crosses, on all four variants; `:120-137`
  pins `layoutHash` and the whole `configJson` identical under a forced apple vs banana preference
  over 12 seeds; `:139-158` pins the `x → 23 − x` congruence of the apple and banana source sets in
  both mirror states and all four variants; `:160-184` pins that the spawns do **not** mirror (the
  builder's fix — `yard.nim:150-159` explains why: the reflection is an isometry, so reflecting the
  spawns with the sources would leave both species' distances unchanged and the mirror bit could not
  cancel the bias); `:186-207` pins the `final` frame. The prompts carry the same asymmetry
  (`llm.nim:186-204` hides the guess column from the child; `:313-321`).

**Manifest** (checklist 6, 10, 12) — §M
- `num_agents: 2` in all four variants (`:494`, `:517`, `:540`, `:563`) and in
  `certification.game_config` (`:584`); `certification.players` seats both declared `player[]`
  entries (`:593-601` vs `:404-478`), exactly two entries, both `{{DAYCARE_IMAGE}}` +
  `/bin/daycare-player` + `resources`. `tests/test_manifest.nim:45-99` asserts each of those,
  re-derives each variant id from its own `game_config` through the real `config.update`, and checks
  the cert fixture is ≥ 12 s of video with `minTurnSeconds: 0`.
- `tools/ci/docker_smoke.sh:106-151` enforces the four seat-count invariants before any container
  starts, each with a `SEAT-COUNT FAIL:` prefix, plus the independent `SMOKE_SEATS` cross-check
  (`:146-151`, substituted to 2 at `:54`). The `docker-smoke` log for run 32853852532 contains no
  `SEAT-COUNT FAIL` and reports `game=daycare seats=2`, `all 2 player containers exited 0`,
  `smoke OK: seats=2 results=294B replay=59617B reason=complete`.
- `game.docs` is `{"readme":{"type":"text","value":…},"pages":[{id,title,content:{type:text,value}}]}`
  with `rules.md` and `policies.md`, all three values non-empty (569 / >200 / >200 chars);
  `game.protocols` carries **both** `player` (1618 chars) and `global` (1055 chars) as
  `{"type":"text",…}` objects — asserted `tests/test_manifest.nim:128-147`.
  `ANTHROPIC_API_KEY_URI: secret://coworld/daycare/anthropic_api_key` is on
  `game.runnable.env` (`:20-26`, asserted `:116-126`). Top-level `$schema`, 7 `tags`,
  `episode_timeout_minutes: 20`, `variants[].description` on all four, `additionalProperties: false`.
- Release order: `coworld-release.yml` runs build (`:153`) → certify (`:167`) → **upload the
  policies** (`:206`) → upload-coworld (`:304`) → secret put (`:342`), in that order, and the certify
  step hard-fails unless the log names the static bundle (`:194-199`). All three workflows are
  present; `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both 0755;
  `tools/ci/policies.json` declares four policies — two `PLAYER_PROMPT` champions
  (`daycare-attentive`, `daycare-provider`, both with `USE_BEDROCK: true`, both covering
  "AS THE PARENT" and "AS THE CHILD") and two `PLAYER_SCRIPTED` fillers — with champion #2 carrying
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The checklist's placeholder gate
  (`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files) exits 1, i.e. no match; the only
  angle-bracket residue is the four expected runtime names (`<cow_id>`/`<sha>` in `ci.yml:202`,
  `<run_id>` in both release/submit recipes, `<name>:vN` in `coworld-submit.yml:31`).

**Tests and CI** (checklist 1, 7)
- `gh run list -R Metta-AI/cogame-daycare --branch main -w ci.yml`: run **32853852532** at the
  reviewed sha, conclusion **success**, jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓ (only
  Node-20 deprecation annotations). `git log -p -- tests/` for this run shows **2106 insertions and
  zero deletions** across nine files (and 5 insertions in the follow-up commit): no assertion
  removed, no tolerance widened, no `skip`/`xfail` added, no test file removed.
- All ten items of `design.md:1035-1115` have a corresponding file and the assertions they name:
  `test_sim.nim` (446 lines, every unit in item 1 including the 10 000-attempt shrub-rate check at
  ±10‰ and the `gameHash` determinism pair), `test_noleak.nim` (five gates + two extras),
  `test_baseline.nim` (4 variants × 4 pairings × 12 seeds × full episodes, per-tick legality,
  `slowestTurnMs <= 1.0`), `test_feasibility.nim` (gates (a)–(f), each episode asserted
  `complete`/`turn_limit`), `test_replay.nim`, `test_llm.nim`, `test_manifest.nim`,
  `test_broadcast.nim` (including the scope-duplication walk over the real page at `:198-269`, which
  asserts `buildCareBeats` exists and no game-block `function` name collides with the 20+ chrome
  aliases), `docker-smoke`, `wasm-viewer`. Every test runs twice (debug and `-d:release`,
  `ci.yml:104-150`).

---

## Could not determine

- **C1 (B1's consequence).** Whether any tool actually validates `variants[].game_config` /
  `certification.game_config` against `game.config_schema`. What would settle it: the
  `coworld build` + `coworld certify` output from `.github/workflows/coworld-release.yml:153-199`
  (phase 40), or a local `coworld certify dist/coworld_manifest.json`. Neither is available in this
  sandbox (no `coworld`, no docker). Either way the declared schema contradicts the shipped fixtures.
- **C2.** Whether the 720 s play budget holds with real Bedrock latencies. The bounds are all
  explicit and the arithmetic lands at ~681 s worst case (§W), but every measured number in CI comes
  from a run with **no** credentials (`docker_smoke.sh:194-199` prints "no ANTHROPIC_API_KEY: the
  game must complete on its scripted baselines"), so no LLM turn has ever been timed end to end here.
  What would settle it: a hosted episode's log, or phase 60's fallback count.
- **C3.** Whether the *shipped* chrome keeps a full-cap 80-rune `hunch` legible at a 360 px viewport.
  No gate measures DOM text (N13), the fixture measures its own replica CSS at stage widths rather
  than viewport widths, and every CI replay carries zero LLM text. What would settle it: a screenshot
  of `client/replay_broadcast.html` (or the built `index.html`) at a 360 px **viewport** with a
  full-cap `hunch` and `notes` in the frame, or a DOM overflow assertion
  (`scrollWidth > clientWidth`) added to the fixture.
- **C4.** Whether a grid harness was run for the constants and the caretaker weights (N19). The only
  in-tree evidence is the comment at `src/daycare/sim_types.nim:29-44`. What would settle it: the
  harness script or its output committed, or a cited run.
- **C5.** Whether `client/replay_broadcast.html`'s inherited CSS above the banner is unmodified
  *byte for byte* outside the removals. I read every hunk of the 2544-line diff and every removed
  line I sampled belonged to a documented removal, but I did not verify line-by-line that no
  surviving starter rule was altered; the two intentional literal changes and the one
  `#lockerroom` addition are the only additions inside the starter's CSS that the diff shows.
