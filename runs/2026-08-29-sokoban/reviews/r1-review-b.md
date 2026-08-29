# r1 review (B) — sokoban

> **Second independent trace of round 1.** A first `r1-review.md` was already committed and a
> fixer dispatched against it (`616c2db`) before this reviewer finished, so this file is filed
> alongside it rather than over it. It is an independently produced trace of the same sha by a
> second reviewer; it did not read the other review. The coordinator decides whether to merge
> its findings into round 1 or carry them into round 2.


Repo: `Metta-AI/cogame-sokoban` @ **`464b2abda558bb7c36949dd8dbd783d638f479de`** (`main` HEAD, verified
by `git log -1` on a fresh clone).
Design note: `runs/2026-08-29-sokoban/design.md` (2000 lines).
Starter for provenance: `/workspace/starters/coworld-ctf` @ `a7484eb47b14bde20678ff106c684a633b4f294c`.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15).
Files opened: 47 (all of `src/sokoban/*.nim`, `src/sokoban.nim`, `src/sokoban_player.nim`,
`replay-viewer/*`, `client/*`, `tests/*.nim`, `tools/`, `.github/workflows/*`,
`coworld_manifest_template.json`, `scripts/build_broadcast_page.py`) plus the CI run log for
33243111396.

This is a neutral trace. Findings are numbered F1…F22 and are **not** ranked; the table records
which checklist item each one touches (or "none — note only"), and the judge categorises. Every
finding is labelled **observed** (I read it), **inferred** (I reasoned from what I read) or
**untested** (a run would be needed to settle it).

---

## Summary table (severity-neutral)

| # | One line | Where | Checklist item touched | Basis |
|---|---|---|---|---|
| F1 | `last_turn.dropped` reported to the seat is hard-coded 0 | `src/sokoban/sim.nim:393` | none — note only (§observation, §reply schema) | observed |
| F2 | broadcast `fallback` event carries a constant `cause: "fallback"` | `src/sokoban/sim.nim:295` | none — note only (§Record vocabulary B, §Readouts 9) | observed |
| F3 | `cause = "throttled"` is outside the note's closed cause set | `src/sokoban/decide.nim:270` | none — note only (§Degrade never hang) | observed |
| F4 | `turnBudgetMs` gates attempt *starts*, not the turn: worst turn ≈ spacing + 6 s + 3 s | `src/sokoban/decide.nim:149,212-216,226-229` | 5 (degrade-never-hang) | observed + inferred |
| F5 | server logs loudly but does **not** refuse to start when a joined seat never registers | `src/sokoban/server.nim:221-248`; test `tests/test_sokoban_engine.nim:158-161` | none — note only (§named edits 2, §Tests 32) | observed |
| F6 | `.tiny` dead-square inset is anchored `bottom: 30·--u` with no `var(--band)` | `client/replay_broadcast.html:3140` (`client/sokoban_block.html:214`) | 14(b) (transport band) | observed CSS, **inferred** overlap |
| F7 | `.tiny` inset is pinned to the **left**, on top of ribbon+pips, not the right gutter | `client/replay_broadcast.html:3110,3124,3140` | none — note only (§Legible at 360 px, rule 5) | observed |
| F8 | full-cap `say` rides the starter's `.feed-row{white-space:nowrap;max-width:none}` with no `.say` rule | `client/replay_broadcast.html:488-505`, `client/sokoban_block.html:553-554` | 15 (every drawn string fits) | observed CSS, **inferred** clipping |
| F9 | both `--strict-text-bounds` gates report `canvas_text.total: 0`; fixture asserts no string lengths | CI run 33243111396 wasm-viewer; `tools/ci/renderer_fixture.html:183-191`; `tools/ci/viewer_smoke.mjs:585-600` | 15 (`total: 0` is "not evidence of anything") | observed |
| F10 | `docker_smoke.sh` prints the end reason but never fails on `fault` | `tools/ci/docker_smoke.sh:306-308` | none — note only (design.md:381-382) | observed |
| F11 | `tools/ci/page_smoke.mjs` and `tools/wasm_replay_smoke.cjs` are invoked by no workflow | `.github/workflows/ci.yml` (absent); commit `2647295` message | none — note only (§Tests 51) | observed |
| F12 | `tune_baselines.nim --check` is not run by CI; the test asserts the recorded JSON's own numbers | `.github/workflows/ci.yml`, `tests/test_sokoban_events.nim:157-168` | 7 (second sentence) | observed |
| F13 | the episode tests drive a re-implemented loop (`helpers.runEpisode`), not `runGame` | `tests/helpers.nim:28-87` vs `src/sokoban/server.nim:276-351` | 2, 7 | observed |
| F14 | test sweep sizes reduced to 8 (release) / 2 (debug) seeds; strength band widened | `tests/helpers.nim:11-17`, `tests/test_sokoban_baselines.nim:206-224` | none — note only (§Tests 15-18, 25) | observed |
| F15 | `src/sokoban.nim` docstring says seed randomisation precedes `config.update`; code does the reverse | `src/sokoban.nim:4-8` vs `:46,49-51` | none — note only | observed |
| F16 | `plan` event omits `pushes`/`blocked`, adds `actions`/`source` | `src/sokoban/sim.nim:286-291` | none — note only (§Record vocabulary B) | observed |
| F17 | the seat's private `notes` are written into the replay bytes | `src/sokoban/replays.nim:180`, `src/sokoban/server.nim:313-316` | none — note only (§Reply schema) | observed |
| F18 | `GET /client/replay` route exists in the game server | `src/sokoban/server.nim:589` | 3 ("no /client/replay pod path anywhere") | observed |
| F19 | `game.docs` entries use `"type":"uri"` where checklist item 10's shape shows `"type":"text"` | `coworld_manifest_template.json` `game.docs`; design.md:1646-1649 | 10 (manifest) | observed |
| F20 | relaxed-tier fallback picks the deepest `reached`, not "closest to `bandMin`" | `src/sokoban/levelgen.nim:299-322` | none — note only (§Level sourcing 11) | observed |
| F21 | macros expand against a forward-advanced snapshot, not the literal turn-start board | `src/sokoban/driver.nim:104-127` | none — note only (§The driver) | observed |
| F22 | a records-exhausted replay with no stop record settles `complete/ladderComplete` and synthesises extra ticks | `src/sokoban/replay_runtime.nim:118-138` | 2 (latent; `turnCap` is unreachable in shipped configs) | observed + inferred |

---

## Findings

### F1 — the seat is never told how many of its actions were dropped
- Where: `src/sokoban/sim.nim:386-396` (`endTurn`), read back at `src/sokoban/sim.nim:605-613`.
- Observed: `endTurn` builds the turn report with a literal `dropped: 0,` (`:393`). Nothing else
  writes `sim.lastReport.dropped`. `observationJson` then serialises
  `"dropped": sim.lastReport.dropped` (`:611`), so `last_turn.dropped` is **always 0**, even on a
  turn where `parseDirective` dropped entries (`src/sokoban/directives.nim:196-198`) and
  `beginTurn` counted them into `actionsDropped` / `repliesRepaired`
  (`src/sokoban/sim.nim:278-280`). The true count *is* written to the replay's `directive` record
  (`src/sokoban/decide.nim:107` `"dropped": directive.dropped + directive.overCap`).
- Note says: §Turn and tick structure step 6b — an entry that does not validate is "**dropped** …
  counted in `actionsDropped`, and **reported back next turn**" (design.md:220-222); §observation
  lists `last_turn … dropped` (design.md:557-559); §Tests 24 says the validator "reports
  `truncated` / `dropped` / `unreachable` back accurately" (design.md:1841).
- Basis: observed. No test covers `last_turn.dropped`.

### F2 — the broadcast `fallback` event has a constant cause
- Where: `src/sokoban/sim.nim:294-295`; consumed at `client/sokoban_block.html:556-558` and
  `src/sokoban/replay_runtime.nim:217-220`.
- Observed: `beginTurn` emits `%*{"k": "fallback", "cause": "fallback"}` — the literal string
  `"fallback"`, not the turn's real cause. The real cause is carried in the replay *chat* record
  (`src/sokoban/decide.nim:68-72`), which `applyChat` pushes to `sim.feed`
  (`replay_runtime.nim:84-85`) but which the feed renderer never reads. The game block's feed line
  is therefore always `MISSED THE CALL — pusher plan` with no cause, and the scrubber beat label is
  the same string.
- Note says: §Record vocabulary B — `fallback` `{cause}` (design.md:1281); §Readouts 9 — the feed
  line is `MISSED THE CALL — pusher plan (timeout)` (design.md:1514).
- Basis: observed.

### F3 — `"throttled"` is a cause outside the declared closed set
- Where: `src/sokoban/decide.nim:263-272`.
- Observed: on a `CatchableError` whose message starts with `llm throttled`, `lastCause` is set to
  `"throttled"`, which then reaches `fallbackRecord(turnIndex, …, cause, …)` (`:170`, `:278`,
  `:287`) and the replay.
- Note says: `cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard,
  budget_guard, disconnected}` (design.md:511-513). `disconnected` is never emitted; `throttled` is
  emitted but not declared.
- Basis: observed.

### F4 — `turnBudgetMs` bounds attempt *starts*, not the turn
- Where: `src/sokoban/decide.nim:148-150` (`budget`, `turnStart`), `:212-216` (the spacing sleep),
  `:223-231` (the loop and its deadline check), `:249-250` (the curl timeout).
- Observed: `turnStart` is taken at the top of `turn()`. The `turnSpacingMs` floor then sleeps up to
  2600 ms *inside* that window (`sleep(min(turnSpacingMs, turnSpacingMs - since))`). The loop's only
  budget check is `if getMonoTime() - turnStart >= budget: break` **before** each attempt; once an
  attempt starts it runs to its own curl timeout (`attempt1Ms div 1000` = 6 s, then
  `retryMs div 1000` = 3 s). A worst-case turn is therefore ≈ 2.6 + 6 + 3 = **11.6 s**, not the
  9 s `turnBudgetMs` pins.
- Note says: `turnBudgetMs = 9.0 s` is "a monotonic deadline around the whole turn"
  (design.md:467); the wall-clock arithmetic budgets "60 turns × turnBudgetMs 9.0 s, absolute worst
  = 540 s" (design.md:471).
- Consequence traced: every wait is still explicitly bounded (spacing ≤ 2600 ms, attempt ≤ 6 s,
  retry ≤ 3 s), the budget guard switches the LLM off once `elapsed + 2×9 s > 690 s`
  (`decide.nim:174-181`), and the wall-clock stop at the top of the loop
  (`src/sokoban/server.nim:279-286`) forces `deadline/wallClock` at 690 s < 720 s. So the episode
  settles inside the checklist's 60 % window either way; what is off is the arithmetic's premise,
  not the bound.
- Basis: observed (code) + inferred (the 11.6 s figure; untested at runtime).

### F5 — the server does not "refuse to start" on a joined-but-unregistered seat
- Where: `src/sokoban/server.nim:221-248`; the test at `tests/test_sokoban_engine.nim:158-161`.
- Observed: when `everRegistered[slot]` is false the server echoes
  `"ERROR seat N connected but never sent a register frame; refusing to treat it as a policy and
  seating the pusher baseline"`, sets `isLlm=false`, `scripted=blPusher`, `dead=true`, declares the
  player failure (`:249-252`) — and **starts the game anyway**. The in-file comment at `:229-230`
  states this deliberately ("The episode still runs — nothing a player container does may stop the
  clock"). The test asserts only that those two log substrings appear in `server.nim`; it does not
  exercise the behaviour.
- Note says: two things that pull against each other. §The three named edits to `server.nim` 2:
  "the server **logs loudly and refuses to start the game** when the joined seat has no register
  record" (design.md:1106-1107) and §Tests 32: "the server refuses to start the game (loudly)"
  (design.md:1871-1872). §Decisions: "A silent seat does not end the episode … the ladder runs to
  its natural end with `deadSeats[0] = true`" (design.md:394-398). The implementation follows the
  second.
- Basis: observed.

### F6 — the `.tiny` dead-square inset does not ride `var(--band)`
- Where: `client/replay_broadcast.html:3140-3146` (from `client/sokoban_block.html:213-219`).
- Observed: the appended block's `.tiny` rules anchor the ribbon at
  `bottom: calc(var(--band, 0px) + 124 * var(--u))` (`:3122`) and the pips at
  `calc(var(--band, 0px) + 112 * var(--u))` (`:3126`) — both correctly clear of the band — but the
  inset is `#stage.tiny #fpv { left: calc(4 * var(--u)); bottom: calc(30 * var(--u)); }` (`:3140`)
  with `width/height: calc(84 * var(--u)) !important` (`:3142-3143`). There is no `var(--band)` term.
  `#fpv` carries `z-index: 11` (`:544`) while `#transport` declares no `z-index`
  (`:1285` markup, rule at `#transport {`), so `#fpv` paints above it, and `#fpv` keeps the
  starter's `cursor: grab` drag handlers.
- Inferred: the transport strip is built entirely from `--u` units — `padding 8u+8u`, `gap 5u`,
  `.scrub { height: calc(34 * var(--u)) }` (`:656-660`) and a `.tbar` of eight `.tbtn`
  (`min-width: 26u`, `padding: 5u 8u`, `font-size: 11u`) with `flex-wrap: wrap`. That puts `--band`
  at ≳ 76·`--u` with one button row, and materially more once the bar wraps, which it must at the
  360 px embed where the design's own arithmetic makes the stage 120 px wide (design.md:1552-1556).
  30·`--u` is then inside the band, i.e. the inset overlaps (and paints over) the transport
  controls.
- Note says: §Transport rules — "**No overlay sits in the transport band**: … every addition here
  (the level ribbon, the level pips, the dead-square inset, the feed) is positioned inside the board
  region, in the letterbox gutters beside it, or in the top band" (design.md:1458-1461). Checklist
  item 14(b): "nothing fixed-positioned … sits inside the band — they ride
  `bottom: calc(var(--band, 0px) + …)`".
- Also observed: the repo's own test for this, `tests/test_sokoban_viewer.nim:134-140`, checks only
  `"top: calc(var(--topband, 0px)" in gameBlock` and that the literal string `bottom: 0` is absent;
  its comment claims "the inset keeps the starter's own bottom offset", which the `.tiny` override
  at `:3140` contradicts (the starter's value is `bottom: calc(64 * var(--u))`).
- Basis: CSS observed; the overlap is **inferred**, not measured (no chromium available in this
  sandbox). See "Could not determine".

### F7 — the `.tiny` inset is pinned into the left gutter, over the ribbon and pips
- Where: `client/replay_broadcast.html:3110-3146`.
- Observed: under `.tiny` the ribbon (`:3110`, `left: calc(4 * var(--u))`), the pips (`:3124`,
  `left: calc(4 * var(--u))`) and the inset (`:3140`, `left: calc(4 * var(--u))`) all sit at the
  same left edge. Vertically the ribbon is at `band+124u`, the pips at `band+112u`, and the inset
  spans `30u … 114u` (84u tall from a 30u bottom) — the pip row at 112u and the inset's top at 114u
  are 2u apart, and both are measured from different origins (the pips include `var(--band)`, the
  inset does not), so the gap closes to a negative once `--band > 0`.
- Note says: §Legible at 360 px rule 5 — "Under `.tiny`, the dead-square inset is pinned to 84 px
  square in the **right gutter**" (design.md:1571-1574); §Legible at 360 px — "the **level ribbon
  and the six pips live in the left gutter**, the **dead-square inset in the right**"
  (design.md:1556-1558).
- Related, and coherent: the builder's documented deviation "ribbon/pips inside the board region"
  is real and necessary — `relayout()` sets `#stage`'s width to the board width
  (`client/replay_broadcast.html:2888-2889`), so there is no gutter *inside* `#stage` for an
  absolutely positioned child to occupy. The note's gutter geometry cannot be realised without
  moving these elements outside `#stage`. That part is internally consistent; the collision above
  is the part that is not.
- Basis: observed (CSS); the collision magnitude is inferred.

### F8 — a full-cap `say` is a single unbreakable feed row
- Where: `client/sokoban_block.html:553-554` (`skFeed(g.alias + ': “' + e.text + '”', 'say')`),
  rendering into `client/replay_broadcast.html:488-505` (`.feed-row`) inside `#killfeed`
  (`:470-486`).
- Observed: `.feed-row` is the starter's rule, inherited unchanged: `max-width: none;`
  and `white-space: nowrap;` (`:502-503`), with the comment "Size to content so full names never
  truncate … bounded by the small font + the pre-bounded 10-char name, so it can't run away". The
  game block now feeds it a whole sentence: `MaxSayRunes = 140` (`src/sokoban/sim_types.nim:36`)
  plus the alias and quotes. There is **no** `.feed-row.say` rule anywhere in the page or the block
  (`grep '\.feed-row\.say'` returns nothing); the `say` class is applied but unstyled. `#killfeed`
  is `width: calc(228 * var(--u))` with `align-items: flex-end`, inside `#stage { overflow: hidden }`
  (`:75-85`).
- Inferred: at the 360 px embed the design's own arithmetic puts the stage at 120 px wide
  (design.md:1552-1556) with `--hudscale` clamped to 0.5, so `.feed-row` renders at
  `font-size: 8·0.5 = 4 px`; a ~145-character nowrap row is several times the stage width and is
  clipped by `#stage`'s `overflow: hidden`. The same classes carry `bad`/`good` in the block
  (`sokoban_block.html:560,571,577`), for which no CSS rule exists either.
- Note says: checklist item 15 — "Any text laid out **relative to another element** … gets a
  **reserved band in the layout**, sized from the cap the server enforces on that string
  (`MaxSayLen` and its kin)"; "Ellipsis is a design choice for **labels** and a defect for
  **sentences**". §Readouts 9 lists the `say` line as a feed row (design.md:1509-1515).
- Basis: CSS observed; the visual outcome is **inferred**, not measured.

### F9 — both text-bounds gates covered nothing, and the fixture asserts nothing about its strings
- Where: CI run **33243111396**, job `wasm-viewer`. Step "Load the bundle in a real browser":
  `{"loaded":true,"ms":565,…}` then `canvas text: 0 drawn, 0 never inside the canvas (0 draws
  crossed an edge), 0 ellipsized (--strict-text-bounds)`. Step "Drive the shipped chrome with a
  worst-case frame": `{"loaded":true,"ms":630,"clock":null,"scorebug":null,"feed_lines":0}` then the
  same `canvas text: 0 drawn` line.
- Observed, and why: `replay-viewer/static_replay.js:88-92` hands the board canvas to the Worker
  with `transferControlToOffscreen()`, so all board drawing happens off the main thread, where
  `viewer_smoke.mjs`'s `addInitScript` hook on `CanvasRenderingContext2D.prototype.fillText`
  (`tools/ci/viewer_smoke.mjs:405-415`) does not run. Independently, `grep -c 'fillText\|strokeText'`
  returns **0** for `client/broadcast_core.js`, `client/replay_broadcast.html` and
  `client/sokoban_block.html` — and 0 for the starter's `broadcast_core.js` too: this chrome family
  draws every string in the DOM, not on canvas. The only main-thread canvas drawing the game adds is
  the dead-square inset, which is chips only and draws no text by design
  (`client/sokoban_block.html:396-400` comment, and its body).
- Also observed: `tools/ci/renderer_fixture.html` does load the shipped `index.html` in iframes at
  360/640/1280 (`:38`, `:145-151`) and drives `SokobanChrome.frame`/`.event` with a 140-rune `SAY`
  (`:43-46`, `:169-174`). Its success condition is only "no exception was thrown":
  `finish()` sets `data-replay-loaded="true"` unless `failed` was assigned (`:183-191`). It makes no
  assertion that the `say` still has 140 runes, that it was rendered, or that it fits.
  `viewer_smoke.mjs` reads the bounds report with `page.evaluate` on the **top** frame only
  (`:596-600`), so the iframes' own `__coworldTextBounds` are never collected — the fixture's
  `canvas_text` is structurally 0 regardless of what the iframes draw.
- Note says: checklist item 15 — "`total: 0` means the check covered nothing (a worker/OffscreenCanvas
  or WebGL renderer) and **is not evidence of anything**"; and the fixture "asserts its own strings
  are still full-length — one quietly shortened remark leaves it passing while testing nothing".
  The fixture and its own `ci.yml` step both exist (`.github/workflows/ci.yml:342-361`).
- Basis: observed (CI log lines cited, code cited).

### F10 — the smoke does not fail on `reason == "fault"`
- Where: `tools/ci/docker_smoke.sh:305-308`.
- Observed: `reason = results.get("reason") or results.get("end_reason")` then
  `print(f"episode end reason: {reason}")`. There is no comparison and no `SystemExit`. The
  CI log for run 33243111396 shows `episode end reason: complete` /
  `smoke OK: seats=1 results=924B replay=53113B reason=complete`, so nothing fired here — but a
  `fault` episode would print and pass.
- Note says: §End conditions, `fault` — "A defect: `tools/ci/docker_smoke.sh` fails the build if the
  smoke episode reports it" (design.md:381-382).
- Basis: observed.

### F11 — two committed harnesses are not wired into any workflow
- Where: `tools/ci/page_smoke.mjs` (125 lines), `tools/wasm_replay_smoke.cjs`;
  `.github/workflows/ci.yml` (no reference to either — `grep -rn 'page_smoke\|wasm_replay_smoke'
  .github/workflows/` matches only a prose comment at `ci.yml:188` about `static_replay_worker.js`).
- Observed: commit `2647295`'s message states "tools/ci/page_smoke.mjs is **the gate** that caught
  all three". It is a developer script; nothing runs it in CI. `tools/wasm_replay_smoke.cjs` is
  likewise present and unrun.
- Note says: §Tests 51 lists `tools/wasm_replay_smoke.cjs` as a shipped test —
  "the starter's headless-node run of the *exact emitted* wasm module against the committed
  fixtures, kept: wasm32-only failures … are invisible to the native shards" (design.md:1960-1962).
- Basis: observed.

### F12 — the tuning sweep is not re-run in CI; the test reads back the recorded numbers
- Where: `tools/tune_baselines.nim:81-108` (the `--check` path), `tests/test_sokoban_events.nim:143-168`,
  `.github/workflows/ci.yml`.
- Observed: a real grid harness exists and is genuinely a sweep —
  `for nodeCap in [8, 16, 24, 40, 80, 150, 300, 600, 1200, 20000] × greedyMatch × tieOnH`, scoring
  each configuration's per-tier solve rate over 40 cached seeds and picking the in-band point
  nearest the band centre (`tools/tune_baselines.nim:114-141`). Its pick, `nodeCap: 8`, is recorded
  in `tools/ci/baseline_tuning.json` and is what `DefaultSearchParams` ships
  (`src/sokoban/search.nim:29-30`) and what all three `game_config` blocks carry. But `ci.yml` never
  invokes `tune_baselines.nim --check`; the shipped test at `test_sokoban_events.nim:157-168`
  asserts the *numbers stored in the JSON file* are inside the band, which the file itself supplies —
  it cannot detect a drift in the measured rates. The independent re-measurement is
  `tests/test_sokoban_baselines.nim:194-224`, which measures over `SweepSeeds` (F14) against a
  widened band.
- Note says: §Scripted baselines — "`tools/ci/baseline_tuning.json` records the sweep's pick and
  `tests/test_sokoban_tuning.nim` asserts the shipped defaults still equal it" (design.md:866-868);
  §Tests 26 — "`ci.yml` re-runs the sweep with `--check`" (design.md:1848).
- On the deviation itself (20000 → 8): coherent and internally consistent.
  `src/sokoban/search.nim:31-36` records the rationale ("a 20 000-node cap measured 1.00 / 1.00 /
  0.99 across the tiers, which is precisely the superhuman floor the design note's test 25 exists to
  keep out"), the sweep's own log confirms 20000 was a candidate and lost, and every shipped surface
  (default config, both variants, cert fixture, tuning JSON, tests) says 8. No contradiction found.
- Basis: observed.

### F13 — the end-to-end tests drive a re-implementation of the server loop
- Where: `tests/helpers.nim:28-87` vs `src/sokoban/server.nim:276-351`.
- Observed: `runEpisode` is a second copy of the turn/tick loop ("the same loop
  `src/sokoban/server.nim` runs, minus the sockets", `helpers.nim:3-6`). It is used by every episode
  test, including the replay re-derivation suite. Two places where it does not match the shipped
  server:
  1. `helpers.nim:55-60` writes a `rkStop` record for **every** forced stop, including the
     `turnCap` scenario (`reason = endComplete`). `server.nim:347-349` writes a stop record **only**
     `if reason != endComplete`, so a real `turnCap` episode carries no stop record. The
     `turnCap` case of `tests/test_sokoban_replay.nim:19-42` therefore exercises a byte shape the
     server never produces (see F22 for what the shipped shape would do).
  2. Nothing in `tests/` calls `runGameServer`/`finishEpisode`/`writeArtifact`, so the artifact
     path (`server.nim:163-193`) — replay-before-results ordering, `COGAME_*` URI handling, the
     events sink — is covered only by `docker_smoke.sh`. The design note's test 30 asks for a real
     episode "against a temp-dir `COGAME_*` URI set" asserting "`results.json` **and** the `.replay`
     are written" (design.md:1860-1864); the shipped test asserts `episode.replay.len > 0` on the
     harness's in-memory bytes (`tests/test_sokoban_engine.nim:18`).
  Related: `tests/test_sokoban_engine.nim:149-156` "the player-failure payload is the platform's
  CLOSED two-key schema" constructs the payload inside the test rather than calling
  `declarePlayerFailure`, so it asserts the literal it just wrote.
- Note says: §Tests 30 and 32 as quoted; checklist 7 asks for "a test [that] runs an all-scripted
  episode to the natural end, asserts `results.reason == "complete"`" — which
  `test_sokoban_engine.nim:12-18` does do, through the harness, and which `docker-smoke` also does
  through the real binary (`reason=complete` in the run log).
- Basis: observed.

### F14 — sweep sizes and the strength band are reduced from the note's figures
- Where: `tests/helpers.nim:11-17`, `tests/helpers.nim:89`, `tests/test_sokoban_baselines.nim:206-215`.
- Observed: `const SweepSeeds* = when defined(release): 8 else: 2` and
  `const SampleStates* = when defined(release): 60 else: 12`, both with an in-file comment naming
  the divergence explicitly ("DIVERGENCE, recorded here rather than hidden: the design note asks for
  5 000-seed sweeps"). `test_sokoban_baselines.nim:214-215` widens the pinned band from the note's
  `unfiltered 0.60-0.95, medium 0.15-0.55, hard 0.00-0.20` to `low = [45, 10, 0]`,
  `high = [100, 65, 30]` percent, with a comment naming the reason. In a debug run
  (`SweepSeeds = 2`) each tier is sampled 4 times, so `rate >= 45` is a 2-of-4 gate.
- Note says: §Tests 16 "over 2 000 seeds per tier … The relaxed rate is asserted to be **< 1 %**"
  (design.md:1810-1812); 17 "5 000 seeds"; 18 "1 000 seeds"; 25 "over 100 seeds of `ladder` …
  unfiltered 0.6–0.95, medium 0.15–0.55, hard 0.0–0.2" (design.md:1842-1845).
- Traced: the assertions themselves are all still present — the reduction is in sample size, not in
  what is checked. `git log -p -- tests/` shows tests/ was touched by exactly one commit (`3724a05`,
  all files added); commits `2647295` and `464b2ab` touch no test file, so nothing was loosened
  *during* this run.
- Basis: observed.

### F15 — the entrypoint docstring inverts the order the code uses
- Where: `src/sokoban.nim:4-8` vs `src/sokoban.nim:44-51`.
- Observed: the module comment reads "SEED RANDOMISATION HAPPENS HERE, **before** `config.update`'s
  pinned seed is honoured". The code calls `config.update(parseJson(runtimeConfig.config))` at `:46`
  and only then `if not seedPinned(...): config.seed = randomSeed()` at `:49-51`.
- Traced: functionally immaterial here — nothing consumes `config.seed` between the two lines
  (`generateLevel` is first called from `server.nim:289`, after both), and `seedPinned` reads the raw
  config text rather than the merged struct, so a runner-pinned seed still wins.
- Note says: §Kept, by path — "`src/ctf.nim` → `src/sokoban.nim` … **including seed randomisation
  before `config.update`** so seed-derived draws follow the final seed" (design.md:960).
- Basis: observed.

### F16 — the `plan` event's field set differs from the note's
- Where: `src/sokoban/sim.nim:286-291`.
- Observed: the emitted object is
  `{k, n, moves, actions, truncated, dropped, unreachable, source, t}` — no `pushes`, no `blocked`
  (both are unknowable at `beginTurn`, before the ticks run), plus two fields the note does not list.
  The feed line built from it (`client/sokoban_block.html:548-552`) reads
  `TURN n — A ACTIONS, M MOVES[, PLAN CUT OFF][, U UNREACHABLE]`.
- Note says: §Record vocabulary B — `plan` `{n, moves, pushes, blocked, truncated, dropped,
  unreachable}` (design.md:1279); §Readouts 9 — `TURN 23 — 4 ACTIONS, 6 PUSHES, 3 MOVES BLOCKED`
  (design.md:1511). §Tests 48 checks the set of event **kinds**, not their fields, and
  `tests/test_sokoban_events.nim:8-42` matches that.
- Basis: observed.

### F17 — the seat's private `notes` are written into the replay bytes
- Where: `src/sokoban/server.nim:313-316` (`writePlan(..., notes: directive.notes)`),
  `src/sokoban/replays.nim:164-180` (`writer.body.addText(plan.notes)`),
  `src/sokoban/replays.nim:262-263` (read back).
- Observed: every turn's `notes` is serialised into the plan record. It is not used at playback —
  `replay_runtime.nim:100-105` copies it into the reconstructed `Directive`, and `beginTurn` never
  reads `directive.notes` — so it is carried but not load-bearing. The `directive` **chat** record
  deliberately carries only `say` (`decide.nim:94-110`), and `directiveRecord` strips `notes` from
  the mirrored observation (`decide.nim:111-116`).
- Note says: §Reply schema — `notes` is the "private scratchpad, echoed to this seat only next turn"
  (design.md:646); §Record vocabulary A's `directive` row lists `say` and `view` but not `notes`
  (design.md:1268); §Replay bytes' `plans` row is "per turn: the accepted action list — this game's
  entire input log" (design.md:1256).
- Basis: observed.

### F18 — `/client/replay` is a registered route on the game server
- Where: `src/sokoban/server.nim:589` (`result.get("/client/replay", replayPageHandler)`),
  `:389-390`, `docs/PROTOCOL.md:10,18`.
- Observed: the route exists and serves the broadcast page locally. The manifest declares only
  `game.replay_viewer = {"bundle": "static-replay-viewer"}` and no pod viewer; `coworld-release.yml:211`
  even carries a guard string `"/client/replay viewer is not acceptable."`. The starter also serves
  its replay routes locally (`/workspace/starters/coworld-ctf/src/ctf/server.nim:631,646,844`).
- Note says: §Viewer — "No `/client/replay` live-server viewer is ever declared to the platform; the
  game still serves `/client/replay` locally for developers" (design.md:1315-1317). Checklist item 3
  reads "No `/client/replay` pod path **anywhere**". Recording the tension; the declared surface is
  the static bundle only.
- Basis: observed.

### F19 — `game.docs` uses `"type":"uri"`, checklist item 10's shape shows `"type":"text"`
- Where: `coworld_manifest_template.json`, `game.docs`; asserted by
  `tests/test_sokoban_manifest.nim:63-76`.
- Observed: the structure is exactly
  `{"readme":{"type":"uri","value":"https://…/README.md"},"pages":[{"id":"rules.md","title":"Rules",
  "content":{"type":"uri","value":"https://…/docs/RULES.md"}}, … actions.md, levels.md]}` — three
  pages, each with `id`, `title` and a `content` object. All four referenced files exist in the tree.
- Note says: §Packaging pins exactly this with `"type":"uri"` (design.md:1646-1649). Checklist item
  10 writes the shape as `{"readme":{"type":"text","value":…},"pages":[{"id","title",
  "content":{"type":"text","value":…}}]}`. Keys and nesting match; the `type` discriminator does not.
- Basis: observed.

### F20 — the relaxed-tier fallback picks the deepest attempt, not the one closest to `bandMin`
- Where: `src/sokoban/levelgen.nim:299-322`.
- Observed: when no attempt hits its drawn `targetDepth`, the code keeps the attempt with the
  largest `bfs.reached` (`if bfs.reached > bestReached`) and sets `optPushes = bestReached`,
  `tierRelaxed = true`. Since `reached` is clamped to `targetDepth` (`:201-202`) and
  `targetDepth ≥ bandMin`, "deepest" and "closest to `bandMin` from below" coincide in most cases but
  are not the same rule. The relaxed path also re-draws the player cell with
  `hashAt(seed, levelIndex, 0, 500)` (`:315`) — attempt index `0`, not the attempt that produced
  `bestNode`. Both remain pure functions of `(seed, levelIndex, tier)`, so determinism and the
  "levels are pure" property (`tests/test_sokoban_levelgen.nim:42-56`) are unaffected.
- Note says: §Level sourcing 11 — "take the attempt whose `reachedDepth` is **closest to `bandMin`**"
  (design.md:924-927).
- Basis: observed.

### F21 — macros expand against a forward-advanced snapshot
- Where: `src/sokoban/driver.nim:53-55`, `:104-127`.
- Observed: `expandDirective` keeps a mutable `state` that it advances by replaying each macro's
  produced primitives before expanding the next one, and a `live[]` array that tracks where each
  turn-start crate index currently stands (`:122-125`). So macro *k+1*'s walk BFS runs from where
  macro *k* left the cog, while `push.box` still indexes the turn-start order the observation handed
  the policy. The behaviour is documented in the code at `:48-52` and `:104-106`.
- Note says: §Turn and tick structure 6c — "Macros are expanded against the **turn-start snapshot**"
  (design.md:222-225); §The driver repeats it and defines `push`'s approach square in terms of "the
  box's turn-start cell" (design.md:800, 806).
- Traced as coherent: the literal reading would make a two-macro turn plan every walk from the
  original player cell, which cannot execute. The box-index half of the pin *is* honoured, and
  expansion mirrors execution exactly (the blocked-primitive no-op path at `:113-118` is the same
  logic as `sim.stepTick`'s `:321-349`), which is what the note's "expansion and replay identical"
  requirement is for.
- Basis: observed.

### F22 — a replay whose records run out with a level still active is settled as `ladderComplete`
- Where: `src/sokoban/replay_runtime.nim:118-138`.
- Observed: `stepReplay` settles `endComplete/erLadderComplete` in two places (`:124`, `:132`) with
  no reference to the recorded end rule. A `rkStop` record (`:112-116`) is the only thing that can
  produce `deadline` or `fault` at playback, and `server.nim:347` writes one only when
  `reason != endComplete`. For a `turnCap` episode the server writes **no** stop record, so playback
  would run past the last recorded plan on `wait` primitives (`queueOrWait`, `sim.nim:310-311`) until
  the step budget fires, changing that level's `levelOutcome` and adding ticks beyond
  `data.hashes.len` (the hash comparison is guarded by `if player.hashIndex < player.data.hashes.len`,
  so no false mismatch is raised).
- Inferred, and why it is latent: `erTurnCap` is set only when `turnsPlayed >= maxTurns` **and** the
  ladder is not complete (`server.nim:339-340`). With `maxTurns = levelCount × levelTurnCap` and
  `stepBudget = levelTurnCap × turnMoves`, a level that consumes all ten of its turns has spent 200
  moves and has already finished on the step cap (`sim.nim:371-373`), so reaching turn 60 implies the
  ladder finished. I could not construct a shipped config where this fires.
- Note says: §Determinism 6 and §Tests 34 require record → re-derive for **every** end reason
  including `turnCap` (design.md:1056-1060, 1877-1880). The test covers it (F13) by writing a stop
  record the server would not write.
- Basis: observed + inferred.

---

## Traced and consistent

Chrome and viewer provenance
- `client/chrome_common.js` — `diff` against `/workspace/starters/coworld-ctf/client/chrome_common.js`
  is **empty**; 40 022 bytes; sha256 `7ace7287…72f7c`, matching the note (design.md:1368-1369) and
  the literal pinned at `tests/test_sokoban_viewer.nim:15-17`. The `window.CTF_WIRE` alias deviation
  is real and is what makes the byte-for-byte pin possible: `chrome_common.js:72` reads
  `window.CTF_WIRE`, and `src/sokoban/wire_constants.nim:30` publishes
  `window.SOKOBAN_WIRE={…};window.CTF_WIRE=window.SOKOBAN_WIRE;`.
- `client/replay_broadcast.html` is **mechanically reproducible** from the starter: running
  `python3 scripts/build_broadcast_page.py /workspace/starters/coworld-ctf/client/replay_broadcast.html
  /tmp/regen.html client/sokoban_block.html` produces a file byte-identical to the committed page
  (170 201 bytes). Every `cut()`/`swap()` in the script asserts its anchors exist, so the page cannot
  drift silently from the starter.
- Diffing the shipped page's pre-banner region (lines 1-2926) against the starter's (1-4343) gives 33
  hunks. Every deletion maps to a removal the note lists: `#povBadge` CSS+markup (starter :526),
  `.fpv-hp`/`.fpv-gear` (:649), the fpv inset-map CSS and markup, `4b. VIEW CONTROLS` /
  `#viewpanel` / zoombar CSS and markup, the `#viewpanel` opt-out (:1449), `#endcard .ec-heart`
  (:1218), the `.beat-marker.kill/.steal/.return/.capture` rules (:914), the 941-line raycast FPV
  pipeline (`renderFpv` … `renderMismatch`, :2529), the fp-map ingest (:2080), the board zoom/pan keys
  (:3968), the zoom+minimap wiring (:4129) and the eye-level billboard art (:1668). Every insertion
  is a re-label from the note's table or the block itself. CSS sections 1 (scorebug), 2 (kill feed),
  3 (banner lane), 5 (transport) and 6 (end-card) survive with their headers; only 4b (view controls)
  is gone, by design.
- `#viewpanel` and its ids appear nowhere but a comment (`client/replay_broadcast.html:2932-2933`).
  `attachMinimap`'s call site and `ZOOM_STEP` are gone; `broadcast_core.js` still defines
  `attachMinimap` and tolerates never being attached, exactly as the note predicted
  (design.md:1401-1402).
- Every kept id the note lists is present (I grepped 31 directly; `tests/test_sokoban_viewer.nim:165-182` checks 49); `#plates-r` is kept and rendered
  empty because `teamsJson` (`src/sokoban/broadcast.nim:34-49`) emits one team.

Emscripten flags vs the bootstrap (checklist 13)
- `replay-viewer/config.nims` differs from the starter's only in the four rename lines (`ctf_replay.js`
  → `sokoban_replay.js`, the `_ctf_*` → `_sokoban_*` export list, two comment lines). No `MODULARIZE`,
  no `EXPORT_NAME`. `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`,
  `-s ENVIRONMENT=web,worker,node`, `--preload-file`, `-O2` all present.
- `replay-viewer/static_replay_worker.js` differs from the starter's only in renames, and it
  bootstraps with `var Module = {}` (`:8`) + `Module.onRuntimeInitialized = …` (`:188`) +
  `importScripts('./wire_constants.js', './broadcast_core.js', './sokoban_replay.js')` (`:239`).
  Non-modularized build + `onRuntimeInitialized` shell = a matched pair from the same starter.
- `replay-viewer/static_replay.js` differs from the starter's in exactly two lines (worker name,
  `window.CtfStaticReplay` → `window.SokobanStaticReplay`). `data-replay-loaded="true"` is set at
  `:161` in the Worker's `'loaded'` branch; `data-replay-error` at `:20` in `showFailure`. Both from
  the shell's own code paths.
- The only network call in the whole bundle is `fetch(message.replayUrl, …)`
  (`static_replay_worker.js:113`). No other `fetch`, `XMLHttpRequest` or absolute URL in the page,
  `broadcast_core.js` or either replay JS.
- Evidence it actually runs: CI 33243111396, `wasm-viewer` → "Load the bundle in a real browser" →
  `{"loaded":true,"ms":565,…}`, `soak: 10s of playback kept advancing ("1 / 430" -> "97 / 430" ->
  "121 / 430")`, three distinct scrub readouts.

Playback opens at the game start (checklist 13, third bullet)
- There is **no recorded lobby**. `newReplayWriter` is constructed at `src/sokoban/server.nim:263`,
  *after* the lobby loop (`:201-219`), and `writeHash` is only ever called inside the tick loop
  (`:324`). The first records are written at tick 0 (`:266`, `:298`, `:313`). `ReplayPlayer.startTick`
  is `0` (`replay_runtime.nim:245`), which is broadcast as `st` (`broadcast.nim:118`) and is the
  clamp floor for `,`/`b` seeks (`replay_runtime.nim:280,283`). `newSimFromReplay` sets
  `phase = phPlaying` immediately (`:59`), so the locker-room curtain never shows in a replay.
  A long `lobbyJoinTimeoutTicks` produces zero frozen frames because the writer does not exist yet.
  This is why the checklist's "record with a LATE gameStart" probe cannot apply here — inferred from
  the code, not from a run.

Replay re-derivation (checklist 2)
- `tests/test_sokoban_replay.nim:96-113` re-steps the recorded bytes and asserts
  `data.hashes[game.tick - 1] == game.gameHashValue` **at every tick**, plus equal final tick, levels
  solved and box credit. `:19-42` repeats the round trip for all four end reasons asserting
  `hashMismatchTick == -1` and identical `ladderResultsJson()`.
- The viewer derives its display from that same re-derivation: `replay-viewer/sokoban_replay.nim:3`
  imports `sokoban/[broadcast, global, replay_runtime, replays, sim]` — the same modules the server
  runs — and `renderCurrent` builds the packet from the re-derived `game`, never from a parallel
  recording. `sokoban_mismatch_tick` surfaces the divergence tick (`:120-123`) into `#mmwarn`.
- The level grids are recorded, not regenerated: `replays.nim:287-296` (`levelFromPayload`),
  `sim.nim:203-207` (the sim never calls the generator), and
  `tests/test_sokoban_replay.nim:92-94` asserts `"generateLevel" notin` `replay_runtime.nim`.

Resolution rules
- `sim.stepTick` (`sim.nim:300-381`) implements the note's numbered order literally: tick/levelMove
  increment (1), `queueOrWait` (2), the four-case primitive application with `blockedMoves` on both
  failure cases and `boxon`/`boxoff` emission (3), `levelBoxesPlaced` as a running maximum (4),
  termination evaluated **only when `boxMoved`** and in the order solved → deadlocked (5), the step
  cap on every tick (6), the hash mix (7), `turnEnded` (8). Boxes are moved in exactly one place
  (`:332`); there is no pull, undo or restart anywhere in the tree.
- `deadlock.isDeadlocked` (`deadlock.nim:83-110`) is the ordered disjunction dead_square →
  frozen_block → no_push, with the static set computed from walls and targets only
  (`deadSquares`, `:22-53`) — the fixpoint marks `c-d` alive when `c-d` and `c-2d` are floor, matching
  design.md:275-283. `legalPushes` (`grid.nim:179-203`) is the single predicate shared by
  `pushes_available`, deadlock test 3, both baselines and the search, exactly as the note asks.
- `tests/test_sokoban_sim.nim:267-281` is the soundness test (positions drawn from the generator's own
  backward BFS are never flagged); `:176-206` brute-forces the dead-square set on small boards.

Level generation
- `generateLevel` (`levelgen.nim:232-326`) follows steps 1-12 with every draw an independent
  `mix64(seed, levelIndex, attempt, salt)` (`:30-44`) — a hash, never a consumed stream, so level *k*
  cannot depend on play in level *k-1*. `genAttemptCap` bounds the outer loop (`:243`), `genNodeCap`
  bounds dequeues (`:148`). Connectivity ≥ 44 floor cells (`:245-248`), 4 distinct targets by
  rejection sampling (`:64-84`), the ≤ 1-parked rejection (`:267-277`), the player draw from the
  chosen state's own region (`:285-292`). The three `data/levels/fallback_*.xsb` files exist and
  carry `; optPushes = N` headers (`fallback_medium.xsb` = 13, inside the medium band).
- `tests/test_sokoban_levelgen.nim` covers purity, exactness against an independent forward search,
  band membership, well-formedness (border, connectivity, counts, no crate on a dead square) and
  the no-network/no-dataset grep.

Decision path (checklist 8)
- One request per attempt through the starter's batch path: `batch.post(...)` then
  `engine.client.curl.makeRequests(batch, max(1, deadlineMs div 1000))` (`decide.nim:242-250`), a
  batch of one for the single seat.
- `while attempt < 2` (`:223`) — attempt 1 at `attempt1Ms`, exactly one retry at `retryMs`
  (`:230-231`), with the retry's user message carrying a "your previous reply was not usable"
  nudge (`:233-236`).
- Tolerant parsing: `extractJsonObject` (`directives.nim:72-111`) scans for the outermost balanced
  `{…}`, skips string contents and escapes, falls back to first-brace…last-brace, and is tested
  against fences plus trailing prose (`test_sokoban_baselines.nim:187-193`).
- Fallback is the `pusher` proc itself: `decide.nim:167` calls `sim.scriptedDirective(blPusher)`,
  which is `sim.nim:625-630` → `baselines.scriptedPlan`. `test_sokoban_baselines.nim:106-117`
  asserts the two resolve to the same plan.
- The fallback is recorded three ways: a `fallback` chat record with turn/attempt/cause/detail
  (`decide.nim:68-72`, written to the replay at `server.nim:306-308`), `seat.fallbackTurns` →
  `results.fallbackTurns` (`server.nim:311-312`, `sim.nim:478-482,523`), and the log line. The two
  phrasings are correct: attempt 1 logs `"attempt 1 failed, will retry"` (`:276`), only the second
  failure logs `"falling back to pusher"` (`:288`).

Every wait and its bound
- Lobby: `while epochTime() < connectDeadline` with `sleep(200)`, `connectDeadline = start +
  lobbyJoinTimeoutTicks/24` (`server.nim:199-208`) — 100 s in the variants, 25 s in the cert fixture.
- Register grace: `min(now + 4.0, connectDeadline + 4.0)` (`:210-219`).
- Per-turn: `turnSpacingMs` sleep ≤ 2600 ms (`decide.nim:212-215`), attempt deadlines 6 s / 3 s,
  outer gate `turnBudgetMs` (see F4), rolling-60 s request cap of 28 (`:47-55,126-136`).
- Episode: wall-clock stop at the top of every loop iteration (`server.nim:279-286`), budget guard at
  `elapsed + 2·turnBudgetMs > wallClockBudgetSeconds` (`decide.nim:174-181`), turn cap and ladder end
  (`sim.nim:632-633`).
- Shutdown: `sleep(ShutdownGraceSeconds * 1000)` = 20 s **after** artifacts are written
  (`server.nim:351-355`), so settle-and-score happens at ≤ 690 s < 720 s.
- Tick loop: `while not sim.turnComplete()` with `queueIndex` incremented on every `stepTick`
  (`sim.nim:312`) and an explicit `break` on `turnEnded`. `stepTick`'s early return
  (`:304-305`) fires only when `turnEnded` is already true or the level is inactive, and the only
  path that clears `levelActive` mid-loop (`finishLevel`) also sets `turnEnded` — so the loop cannot
  spin. Inferred, not exhaustively proved.
- Generator: `genNodeCap` × `genAttemptCap`; search: `params.nodeCap` expansions
  (`search.nim:135`); walk BFS: ≤ 100 cells.
- No blocking read anywhere in the game loop; mummy serves on its own threads
  (`server.nim:626-628`), and `broadcastPacketLocked` swallows send failures (`:129-132`).

Rune-safe truncation (checklist 9)
- One implementation: `truncateRunes` (`sim_types.nim:185-193`) → `runeSubStr`, never a byte index.
  Applied at every cap I could find: `say`/`notes` (`directives.nim:53-70`), the policy label and
  name (`server.nim:518,523`), the prompt at registration (`server.nim:504`,
  `sokoban_player.nim:34`), the operator block (`llm.nim:276`), `stopDetail`
  (`sim.nim:525,651`), `fallback.detail` (`decide.nim:71`), provider error bodies
  (`llm.nim:182,190,196`), the no-JSON error head (`directives.nim:107-108`) and the whole
  serialised directive record (`boundedRecord`, `directives.nim:214-228`, which shrinks the free-text
  fields rather than cutting the JSON).
- Tests: `test_sokoban_baselines.nim:174-185` feeds 400 × U+1F9CA and asserts
  `runeLen == MaxSayRunes` / `MaxNoteRunes` and `validateUtf8() == -1`;
  `test_sokoban_replay.nim:116-148` fills every capped replay field with the same emoji, runs
  `tools/replay_summary.py` and asserts strict-UTF-8 JSON with no lone surrogates.
- The one byte slice on the path — `llm.nim:208-209` `result[0 ..< MaxReplyBytes]`, which the note
  itself specifies in bytes (design.md:647) — cannot reach the replay as invalid UTF-8:
  `sanitizeSay` re-encodes rune by rune (`directives.nim:57-64`).

Scoring
- `sim.nim:421-427`: `1_000_000 * solvedWeight() + 10_000 * boxCredit() + movesSavedTotal()`,
  character for character the pinned formula (design.md:312-315). `solvedWeight` sums
  `TierWeights[tier]` over solved levels (`:402-405`); `boxCredit` sums `levelBoxesPlaced` over all
  six (`:412-414`); `movesSavedTotal` is `max(0, stepBudget - moves)` over solved levels only
  (`:416-419`). `TierWeights = [1, 2, 3]` (`sim_types.nim:158`). `win = solvedWeight >= parWeight`
  (`:429-430`); `winner` is `%0` when `win` else `newJNull()` (`:488`). No term subtracts.
- `tests/test_sokoban_sim.nim:364-434` asserts the formula, both dominance bounds
  (241 194 < 1 000 000 and 1 194 < 10 000), both maxima (12 241 194 / 16 241 194), the minimum of 0
  and the win/winner rules, over 500 randomised end states.
- All six results identities are asserted at `tests/test_sokoban_engine.nim:21-69`, and the produced
  key set is checked equal to the manifest's `results_schema` in both directions (`:71-87`) — I
  independently diffed the two: 39 keys, identical.

Replay writer self-sufficiency
- Header: magic `COWLDSOK` (`replays.nim:23`), format version, game name/version, protocol name, then
  the resolved config JSON (`:141-148`). `configJson` (`sim_config.nim:150-192`) carries every key
  the note's config-JSON row names, including `tierWeights` and `tierBands`.
- Records: one `rkLevel` per level with ten XSB rows, tier, `optPushes`, `tierRelaxed` and the
  dead-square list (`:150-162`); one `rkPlan` per turn with the accepted actions; chat records for
  `register`/`directive`/`fallback`/`budget_guard`/`result`; a `rkStop` for a non-complete end; and
  one `gameHash` per tick (`:194-203`).
- `tests/test_sokoban_replay.nim:45-82` asserts all of that from the bytes alone (23 config keys, ten
  rows per level, exactly one `register` and one `result`, `hashes.len == sim.tick`). The seed lives
  in the config JSON and in `results.seed`, and is never in an observation or prompt
  (`test_sokoban_obs.nim:80-110`).

Manifest (checklist 6, 10, 12)
- `num_agents: 1` inside `variants[0].game_config`, `variants[1].game_config` **and**
  `certification.game_config`; absent at every variant top level (variant keys are exactly
  `id, name, description, game_config`). `certification.players` has 1 entry,
  `certification.game_config.players` has 1 entry, `player[]` has exactly 1 entry (`pusher`) and it
  is the seated one.
- No literal `tokens` array in any `game_config` (the two `"tokens"` occurrences are both in
  `config_schema`, where the note requires it). `config_schema` is
  `additionalProperties: false`, `required: ["tokens","players"]`, and every array property carries
  `minItems`/`maxItems`: `tokens` 1/1, `players` 1/1, `slots` 0/1, `tierLadder` 6/6.
- `replay_viewer: {"bundle": "static-replay-viewer"}` under `game`; `tools/build_replay_viewer.sh`
  present and mode `100755` (git index confirms), invoked by path in ci.yml `:256`, carrying the
  `mkdir -p "$(dirname …)"` fix, the buildx/`--platform linux/amd64` handling, and
  `docker cp "…:/workspace/sokoban/replay-viewer/dist/." "${output_dir}"`.
- `episode_timeout_minutes: 20` at top level; five top-level `tags`; no `game.tags`;
  `game.description` present; `game.owner = daveey@softmax.com`; `player[0].resources.limits.cpu = "1"`.
- `game.protocols` carries both `player` and `global` as `{"type","value"}` objects.
- Both variants and the cert fixture satisfy `stepBudget == levelTurnCap × turnMoves` (200 = 10×20),
  `maxTurns == levelCount × levelTurnCap` (60 = 6×10), `maxTicks == maxTurns × turnMoves`
  (1200 = 60×20), `len(tierLadder) == levelCount`, `attempt1Ms + retryMs ≤ turnBudgetMs`
  (6000+3000 = 9000), both whole seconds, and `wallClockBudgetSeconds ≤ 690`.
  `tests/test_sokoban_manifest.nim:126-150` additionally constructs and *plays* every variant.
- `tools/ci/docker_smoke.sh` mode `100755`, and enforces the four seat-count invariants at `:113-150`
  with `SEAT-COUNT FAIL:` prefixes plus the independent `SMOKE_SEATS` cross-check (`:54,141-150`).
  **`grep -c 'SEAT-COUNT FAIL' ` over the full run-33243111396 log returns 0.**
- The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files finds
  nothing. Surviving angle-bracket names are `<cow_id>`/`<sha>` in `ci.yml:210`, `<run_id>` in
  `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>` in `coworld-submit.yml:31`, plus two
  further `<cow_id>` in `coworld-release.yml:75,358` — all runtime values in comments, none of them a
  gated name.
- `tools/ci/policies.json`: four policies, one image, `run: "/bin/sokoban-player"` —
  `sokoban-lookahead` (`PLAYER_PROMPT`, 1754 chars), `sokoban-orderfirst` (`PLAYER_PROMPT`, 1713
  chars) carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, `sokoban-pusher` and
  `sokoban-nudger` (`PLAYER_SCRIPTED`). Both prompts match the note's champion texts.
- Release order in `coworld-release.yml`: `coworld build` (`:165`) → `coworld certify …
  --timeout-seconds 300` (`:182-185`) → "Upload the policies" (`:216`) → "Upload the Coworld"
  (`:314`) → "Put the Coworld secret" (`:410`). All three workflows present.
- `ci.yml`: `wasm-viewer` declares `needs: docker-smoke` (`:220`); the smoke step is a plain `run:`
  with no `continue-on-error` and no `if:`; the replay it loads is the artifact `docker-smoke`
  uploaded (`:200-206`, `:285-292`).

CI green and no test loosened (checklist 1)
- `gh run list -R Metta-AI/cogame-sokoban --branch main -w ci.yml` → run **33243111396**,
  conclusion `success`, head sha `464b2abda558bb7c36949dd8dbd783d638f479de`. All three jobs
  (`test`, `docker-smoke`, `wasm-viewer`) and every step within them are `success`.
- `git log -p -- tests/` shows tests/ touched by exactly one commit, `3724a05`, in which every test
  file is added from `/dev/null`. Commits `2647295` and `464b2ab` touch no test file. No deleted
  assertion, no widened tolerance, no `skip`/`xfail`, no removed test file. Verified.

Both name spaces (checklist 4)
- Agent side: `observationJson`'s `"you": seatAlias(seat)` (`sim.nim:574`) is the only name in the
  observation; the system prompt and operator block contain no names (`llm.nim:219-273`);
  `showPlayerLabels` defaults false (`sim_types.nim:231`) and `labels.nim:17-21` allows exactly one
  name on the board, `ALPHA`. `tests/test_sokoban_obs.nim:98-110` greps a serialised observation and
  prompt for the real policy name.
- Spectator side: `rosterJson` and `teamsJson` carry the real name (`broadcast.nim:21-22,40`),
  `results.names` carries it (`sim.nim:453`), and the plate writes it into `#name-red`
  (`sokoban_block.html:381-384`) beside the `ALPHA` alias chip (`:398-407`).
  `tests/test_sokoban_events.nim:124-141` asserts both.

Scripted baseline plays legally (checklist 7)
- `tests/test_sokoban_engine.nim:12-18` runs an all-scripted `ladder` episode to the natural end and
  asserts `sim.reason == endComplete`. `docker-smoke` does the same through the real binary
  (`reason=complete` in the run log).
- `tests/test_sokoban_baselines.nim:36-59` asserts, for both baselines over `SampleStates` positions,
  `actions.len ≤ maxActionsPerTurn`, `box ∈ 0..3`, `times ∈ 1..8`, `seq ⊆ {U,D,L,R}` and
  `≤ MaxActionSeqRunes`, `x,y ∈ 0..9`, empty `say`/`notes`, serialised directive ≤ 1024 bytes.
  `:62-83` asserts neither emits a suicidal push while a safe one exists; `:85-105` bounds the
  driver's queue and macro expansion.
- The tuning harness `tools/tune_baselines.nim` is a real grid sweep (see F12) — the parameters were
  not guessed.

Chrome transport rules
- `relayout()` (`client/replay_broadcast.html:2860-2903`) measures `#transport` and
  `#scorebug` and sets `--hudscale`, `--topband` and `--band` on `document.documentElement`
  (`:2894,2896-2897`) — on `:root`, not on `#stage`.
- `#endcard { bottom: var(--band, 0px) }` (`:830`), shown with `#endcard.on` (`:841`), and removed on
  every frame whose phase is not `gameover` (`:1760`) — which every seek produces, because
  `seekReplay` rebuilds from a fresh `phPlaying` sim (`replay_runtime.nim:140-150`).
- Beats are real `<button>`s with `title` + `aria-label` that `ctx.send('s:' + tick)` on click
  (`sokoban_block.html:257-272`), built by `skBeat` — never `markBeat` — and the block declares no
  identifier `chrome_common.js` exports (asserted at `tests/test_sokoban_viewer.nim:71-92`).
- The set of `.beat-marker.<kind>` CSS rules in the page is exactly
  `{levelstart, boxon, solved, failed, fallback, end, deadlock}` (page `:3087-3094`), equal to
  `BeatKinds` (`sim.nim:667-668`) and a subset of `EventKinds`; `.deadlock` is the tallest/reddest
  rule (`:3094`). The inherited `kill`/`steal`/`return`/`capture` rules were cut.
- `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`
  (`:2954-2960`), and `@media (max-width: 640px) { .solved-label, .sk-alias, .fl-cap { display: none } }`
  (`:3148-3150`). Checklist item 11 satisfied literally.
- Speed chips: `PlaybackSpeeds = [1, 2, 4, 8]` (`sim_types.nim:53`) → `window.SOKOBAN_WIRE.speeds` →
  `chrome_common.js:72-73`'s `SPEEDS`, whose command map (`:437`) only knows `{1,2,3,4,8,16}`. The
  builder's "no 0.5x" deviation is therefore *required* by the inherited chrome, not merely
  different; `applyReplayCommand` handles exactly `'1','2','4','8'` plus `+`/`-`
  (`replay_runtime.nim:270-277`).

Other deviations checked and found coherent
- `league_replayer.html` dropped: the file is absent, nothing references it, and the manifest
  declares only the static bundle.
- Endcard-label test folded into `tests/test_sokoban_viewer.nim:221-248`: it checks 13 forbidden
  paintbot strings are absent and 9 re-mapped strings are present exactly once (plus
  `Levels solved` twice, with the reason stated). The vocabulary itself deviates from the note's
  table in one consistent way — `CRATES PARKED`/`Crates` where the note wrote `BOXES PARKED`/`Boxes`
  (`scripts/build_broadcast_page.py:182-197`, page `:3103`) — and the test pins the shipped wording,
  so page, script and test agree.
- `stepEvents` derived in `sim.nim` rather than `broadcast.nim`: events are emitted by
  `sim.emit` during stepping and drained per frame (`sim.nim:181-189`), so live and replay produce
  the same stream from the same code, which is the property the note was after.
- No test shards (`tests/shard_*.nim` absent): `ci.yml:104-150` runs every `tests/*.nim` in both
  debug and `-d:release` directly, so nothing is skipped by the missing shards.
- Compact modules instead of in-place edits: `sim_state.nim`, `roster.nim`, `rig_art.nim`,
  `control.nim` do not exist as separate files; their contents live in `sim.nim`, `broadcast.nim`,
  `global.nim` and `driver.nim`. Every behaviour the note attributed to them
  (`gameHash`/`mixHash`, `emitEvent`, `seatAlias`, `ladderResultsJson`) is present and cited above.
- `scripts/build_broadcast_page.py` (an extra file) is what makes the provenance claim mechanically
  checkable; I re-ran it and it reproduces the shipped page byte for byte.

---

## Could not determine

- **F6 / F8, the two layout findings.** No browser is available in this sandbox
  (`/root/.cache/ms-playwright` is absent; `npx playwright install` was not attempted). Both are
  CSS-level observations plus arithmetic. What would settle them: load
  `dist/static-replay-viewer/index.html` at 360×203, then evaluate
  `getComputedStyle(document.documentElement).getPropertyValue('--band')`,
  `document.getElementById('fpv').getBoundingClientRect()` and
  `document.getElementById('transport').getBoundingClientRect()` (F6); and, after driving a
  140-rune `say` through `SokobanChrome.event`, compare `.feed-row.say`'s `scrollWidth` against
  `#stage`'s `clientWidth` (F8). `tools/ci/renderer_fixture.html` already builds exactly this page
  at exactly this width — adding the two measurements to it would settle both.
- **Whether the CI viewer smoke's `never_inside == 0` means anything (F9).** `canvas_text.total` is 0
  in both steps. I established *why* (OffscreenCanvas in a Worker; zero `fillText` calls in the whole
  chrome family, starter included), but I cannot show from the tree whether any string is drawn
  outside its frame, because nothing in CI measures DOM text overflow. What would settle it: a
  DOM-side measurement in the fixture, or a screenshot diff at 360 px.
- **Whether `erTurnCap` is reachable at all (F22).** I argued from `maxTurns = levelCount ×
  levelTurnCap` and `stepBudget = levelTurnCap × turnMoves` that turn 60 implies a completed ladder,
  so the un-stopped-replay path is latent. A counterexample would need a `game_config` where those
  identities hold but a level can consume a turn without consuming 20 moves — I could not construct
  one, because `stepTick` always spends a move (`sim.nim:307-308`) and `turnComplete` only returns
  true at `queueIndex >= turnMoves` or `turnEnded`. Settled by: a test that forces
  `turnsPlayed == maxTurns` through the *server's* loop and re-derives the resulting bytes.
- **Runtime behaviour of the rate guard and the throttle path.** `RollingRequestCap = 28` and the
  `throttled` fail-fast branch (`decide.nim:280-285`) are exercised by no test and cannot fire in CI
  (no `ANTHROPIC_API_KEY` in `docker_smoke.sh`, so `client.disabled` short-circuits at `:189`). Read
  and traced only.
- **Whether a real LLM episode stays inside the budget.** Every episode CI produces is fully scripted
  (`docker-smoke` runs without a key). The 690 s stop, the budget guard and the `turnSpacingMs` floor
  are traced in code and covered by unit tests that force them, but no run in this repo has made a
  provider call. Phase 60 is where that gets observed.
