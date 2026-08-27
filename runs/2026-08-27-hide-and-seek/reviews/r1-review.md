# r1 review — hide-and-seek

Repo: `/workspace/cogame-hide-and-seek` @ `a6d3a86cd1f545b6a031bc43d166c758d424776c` (main)
Starter (read-only): `/workspace/starters/coworld-ctf`
Design note: `runs/2026-08-27-hide-and-seek/design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files opened: 48 (all of `src/hns/*.nim`, both entrypoints, all of `tests/`, `replay-viewer/*`,
`client/replay_broadcast.html` + `broadcast_core.js` + `chrome_common.js`, the three workflows,
`tools/ci/*`, `tools/build_replay_viewer.sh`, `coworld_manifest_template.json`, `data/rooms/*.json`,
plus the starter counterparts I diffed against).

Every finding below cites `file:line` at the reviewed sha. "Observed" = I read it. "Inferred" = I
reasoned from what I read. "Untested" = it would need a run to settle.

---

## Blocking

### F1 — `knownEnemy` has no success path: it always reports "no enemy known"

- **Where:** `src/hns/control.nim:329-338` (proc body ends at 338); starter counterpart
  `/workspace/starters/coworld-ctf/src/ctf/control.nim:297-308`.
- **Observed.** The whole proc is:

  ```nim
  proc knownEnemy*(
    ctl: ControlState, sim: SimServer, cogIndex: int
  ): tuple[known: bool, x, y, index, ticksAgo: int] =
    if cogIndex >= ctl.lastSeenTick.len:
      return (false, 0, 0, -1, 0)
    let age = sim.tickCount - ctl.lastSeenTick[cogIndex]
    if age > HuntMemoryTicks or ctl.lastSeenIndex[cogIndex] < 0:
      return (false, 0, 0, -1, 0)
  ```

  The starter's file is identical up to line 306 and then ends with the two lines this fork does
  not have:

  ```nim
    (true, ctl.lastSeenX[cogIndex], ctl.lastSeenY[cogIndex],
     ctl.lastSeenIndex[cogIndex], age)
  ```

  When an enemy *is* known (age ≤ `HuntMemoryTicks`, `lastSeenIndex ≥ 0`) control falls off the end
  of the proc and Nim returns the zero-initialised implicit `result`, i.e.
  `(known: false, x: 0, y: 0, index: 0, ticksAgo: 0)` (inferred from Nim's implicit-`result`
  semantics; the file compiles — CI run 33125685503 is green).
  `observeEnemies` (`control.nim:305-327`) still fills `lastSeenX/Y/Tick/Index` correctly; nothing
  ever reads them successfully.

- **What it reaches, traced:**
  - `src/hns/decide.nim:178-185` — `seen_enemies` in every seat's observation is built only under
    `if enemy.known`, so **every LLM prompt in every episode carries `"seen_enemies": []`**, contra
    design §Per-seat observation ("every enemy cog inside your cone or bubble right now, and every
    enemy your side saw within the last `HuntMemoryTicks = 72` ticks, tagged `ticks_ago`").
  - `src/hns/baselines.nim:224-241` (`burrow` hider rule 5, the `flinchRadius` re-hide) — never
    fires. Design §Scripted baselines rule 5.
  - `src/hns/baselines.nim:304-308` (`burrow` seeker `chase`) and `374-380` (`scatter` seeker
    `chase`) — never fire; neither baseline can ever emit `intChase`.
  - `src/hns/baselines.nim:353-359` (`scatter` hider flinch) — never fires.
  - `src/hns/control.nim:407-409` — `intChase`'s goal degenerates to the cog's own position, so an
    LLM's `{"intent":"chase"}` is a stand-still; `control.nim:538-542` (chase aim) is dead too.
  - Net effect: three of the eight published intents (`chase`) and the two documented reactive
    rules are inert, and no seat — LLM or scripted — is ever told an enemy position.
- **Checklist item:** 7 — "Scripted baseline plays full episodes legally … **The baseline's
  parameters were tuned with a grid harness, not guessed.**" Two of the six shipped tunables
  (`flinchRadius`, `chaseRadius`) are read only through `knownEnemy` and therefore cannot affect
  play, so the recorded sweep did not tune them. The committed sweep artifact says so itself:
  `tools/ci/baseline_tuning.json:20-73` records three `flinchRadius` values (140/180/220) at each
  `panelReach`, and **every triple has an identical margin** (`-99, -99, -99`; `-300, -300, -300`;
  `-250, -250, -250`) — a parameter with literally zero measured effect.
- **Why blocking:** the design's decision layer and both baselines are specified around enemy
  intel; with this proc the game has none. If the judge reads item 7 as covering only "plays a full
  episode legally and completes", F1 does not falsify it and drops to a non-blocking `correctness`
  finding — I am stating the mapping I used rather than asserting the category.
- **Not caught by any test:** `tests/test_hns_control.nim:34-107` asserts only that emitted orders
  and masks are legal; an order kind that is never emitted passes. No test in `tests/` references
  `knownEnemy` or asserts a `chase` is ever produced (`grep -rn knownEnemy tests/` → no hits).

### F2 — the shout bubble is placed unclamped above the cog; the starter's clamp for exactly this was dropped

- **Where:** `src/hns/global.nim:667-683`, specifically the placement at `679-681`:
  `packet.addBoardObject(objectId, shout.x - art.w div 2, shout.y - SoldierBodyPx - art.h, …)`.
  Bubble size: `src/hns/global.nim:484-492` (`w = textWidth + 8`, `h = font.height + 10`).
- **Observed.** No clamp on either axis. The starter has a dedicated proc for this and calls it at
  all three of its bubble sites:
  `/workspace/starters/coworld-ctf/src/ctf/global.nim:3950-3972` —
  "*The bubble grows UPWARD from the shouter, and a cog can stand on the top row of the arena:
  placing it at `tailTipY - bubbleH` unclamped puts the body at a negative y, where the map layer
  canvas silently clips it and a sentence renders as a sliver. That is the cogchemists defect of
  2026-08-24 verbatim*" — clamping both axes and flipping the bubble below the cog when it does not
  fit; called at `src/ctf/global.nim:4949, 6030, 6164`.
- **Arithmetic (observed inputs, inferred result):** `SoldierBodyPx = 34`
  (`src/hns/sim_types.nim:69`); `data/ascii.png` is decoded at cell height 9
  (`src/hns/sim.nim:426`), so a bubble is 19 px tall. A cog shouting at `y = 40` places the bubble
  at `y = 40 − 34 − 19 = −13`. All three committed rooms have `pocket` anchors at `y = 40`
  (`data/rooms/room_warren.json`, `room_atrium.json`, `room_long_hall.json`), and the `hide` intent
  parks hiders exactly on pockets (`src/hns/baselines.nim:271-294`). The x axis is unclamped the
  same way: a 10-rune shout is ≈78 px wide, so a cog at `x < 39` puts the bubble body at negative x.
- **Checklist item:** 15 — "Any text laid out **relative to another element** — a speech bubble over
  a cog … gets a **reserved band in the layout** … Sizing by eye, or letting the bubble grow into
  whatever happens to be above it, is the bug above."
- **Why blocking, and why no gate sees it:** `viewer_smoke.mjs`'s `canvas_text` instrumentation
  hooks canvas text calls; this bubble is a *sprite* rasterised in Nim, so it is invisible to it.
  CI run 33125685503, step "Load the bundle in a real browser", reports
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)` — `total: 0`, which item 15 names explicitly as "not evidence of
  anything". The flag is on and inert.
- **Untested:** whether a bubble actually clipped in the CI replay — I could not read pixel output;
  the placement arithmetic and the missing clamp are what I observed.

### F3 — no worst-case renderer fixture, and the repo's viewer does draw model-authored text

- **Where:** absent — there is no `tools/ci/renderer_fixture.html` (`find . -name 'renderer*'` →
  nothing) and no step referencing one in `.github/workflows/ci.yml` (three jobs only: `test`
  `:43`, `docker-smoke` `:156`, `wasm-viewer` `:211`; the only `viewer_smoke.mjs` invocation is
  `ci.yml:318-323`).
- **The viewer does draw model text (observed):** `say` becomes an on-board speech bubble
  (`src/hns/global.nim:667-683`, fed from `src/hns/server.nim:1938-1941`); `radio` and the whole
  directive feed are rendered as feed rows by the appended chrome block
  (`client/replay_broadcast.html:2846-2850` `feedRow`, and the `directive`/`radio` routing at
  `2860-2980`); the design's readouts 7 and 5 (§Viewer) describe both.
- **The CI replay carries none of it:** `tools/ci/docker_smoke.sh` runs with no `ANTHROPIC_API_KEY`,
  so every seat is scripted (`src/hns/llm.nim:124-130` disables the client). `scatter` emits
  nothing and `burrow` emits at most one 5-character `"on it"` per game
  (`src/hns/baselines.nim:256-258`); neither baseline ever emits `radio` or `notes`
  (asserted at `tests/test_hns_control.nim:71-72`). So no CI artifact exercises a full-cap remark,
  the radio feed row, or six simultaneous bubbles.
- **Checklist item:** 15, final bullet — "A repo whose viewer draws LLM-authored text must
  therefore ship a **worst-case renderer fixture** … a repo that draws model text and has no such
  fixture is a blocking `legibility` finding." Also design §Tests item 44, which specifies the
  fixture, its contents and its own `ci.yml` step.
- **Why blocking:** combined with F2 and with `canvas_text total: 0`, nothing in the tree measures
  whether any drawn string lands inside the frame.

### F4 — `results.stopDetail` reaches the replay untruncated

- **Where:** `src/hns/sim.nim:615-629` (`forceFaultStop` assigns `sim.stopDetail = detail` raw),
  emitted at `src/hns/roster.nim:520` (`"stopDetail": sim.stopDetail`), which
  `src/hns/decide.nim:549-556` (`resultRecord`) embeds verbatim into the replay's `result` chat
  record. `grep -rn stopDetail src/` returns exactly four hits and none of them truncates.
- **Observed.** The *stop record* is sanitised — `src/hns/server.nim:2017-2019` wraps the same text
  in `sanitizeLine(faultDetail, MaxFallbackDetailRunes)` — but the results document is not, and the
  detail it carries is the caught exception's `msg` (`server.nim:2006, 2013`).
- **What the note says:** §End conditions — "`results.stopDetail` names it (**≤ 200 runes,
  rune-truncated**)"; §Reply schema — "Every string that lands in the replay — `say`, `radio`,
  `notes`, the policy label, **`stopDetail`**, recorded error text — is truncated on RUNE
  boundaries".
- **Checklist item:** 9 — "Every string that reaches the replay (`say`, `notes`, prompts, **captured
  errors**) is truncated on **rune** boundaries."
- **Why blocking:** it falsifies item 9 for one named string class. Scope, stated plainly: the rest
  of item 9 *is* satisfied and tested (`tests/test_hns_control.nim:216-242` feeds 4-byte emoji at
  each cap and asserts `validateUtf8 < 0`; `tests/test_hns_replay.nim:86-140` round-trips a
  full-cap `radio`/`notes` through `replay_summary.py` under a strict parser). The practical
  exposure here is a Nim exception message, which is usually ASCII — so this is a cap violation
  first and a UTF-8 risk second.

---

## Non-blocking

### F5 — one byte-index slice on the model reply path

- **Where:** `src/hns/decide.nim:474-475` — `if text.len > MaxReplyBytes: text = text[0 ..< MaxReplyBytes]`.
- **Observed and traced.** This is the design's own rule (§Reply schema: "whole reply | bytes | ≤
  4096 bytes read from the provider before parsing"), but it is a byte cut and can sever a
  codepoint. I followed both paths the cut string can take to the replay and neither carries the
  broken tail: (a) `extractJsonObject` (`directives.nim:118-157`) only ever returns
  `parseJson(text[start .. i])` or `parseJson(text[first .. last])`, and the last `}` necessarily
  precedes the cut, so parsed fields are clean; (b) the "no JSON object" error message
  (`directives.nim:152-156`) does `head.truncateRunes(160)`, and any text long enough to have been
  byte-cut has ≥1024 runes, so the broken tail is always dropped before the message is built.
  `llm.nim:174, 182, 190, 199` all use `truncateRunes` on provider bodies.
- Reported as an observation, not a defect: I could not construct a path from this slice to the
  replay bytes.

### F6 — the shipped baseline tuning does not meet the note's target, and the test checks the file against itself

- **Where:** `tools/ci/baseline_tuning.json:8-13` (`"margin": -99`, `"marginBand": [-400, 400]`);
  `tests/test_hns_control.nim:265-272`.
- **Observed.** The note (§Scripted baselines) says: "The sweep's target is a `burrow`-vs-`scatter`
  margin in `[+80, +400]` permille: `burrow` must clearly win as a hider (tool use beats no tool
  use)". The recorded margin is **−99** — `burrow` loses — and the recorded band has been widened
  to `[-400, +400]`. The test asserts `margin` is inside the band **read from the same file**
  (`267-269`) plus `abs(margin) <= 400` (`270-271`), so it can never fail on a bad pick.
  Shipped defaults also differ from the numbers the note prints: `panelReach 200` vs 260,
  `flinchRadius 140` vs 180 (`src/hns/baselines.nim:45-52`). The note does say the six tunables are
  the sweep's pick, so differing numbers are legitimate; the *sign of the margin* is not.
- Related: `flinchRadius` is inoperative (see F1), which is a plausible cause of the sign — inferred.
- Also: the note says "`ci.yml` re-runs the sweep with `--check`". No such step exists in
  `.github/workflows/ci.yml`; `tools/tune_baselines.nim` is committed but never invoked by CI.

### F7 — a held object is not dropped at the phase change

- **Where:** `src/hns/sim.nim:119-159` (`resolveGrabs`). The drop branch (`132`) fires on
  `not input.c`, on `pushBlockedTicks >= GrabBreakTicks`, or on `airborne`.
- **What the note says:** tick step 4 — "`C` released (**or** held while the cog is dead-stopped
  against a refusal for `grabBreakTicks = 24` ticks, **or the phase changed, or the game ended**) →
  the held object is dropped".
- **Observed:** neither the phase transition (`sim.nim:524-531`) nor `finishGame`
  (`sim.nim:333-341`) drops held objects. Game-to-game leakage *is* prevented, one layer later, by
  `startGame` (`sim.nim:312-313` sets `holding = -1`) and `resetObjectsToDeal`
  (`objects.nim:234-243`). The prep→hunt case is simply not implemented: a hider may carry a crate
  across the release.
- The note's own test 3 claims coverage ("releasing `C`, **a phase change and a game end** all drop
  it"); the shipped test asserts only the `C`-release case (`tests/test_hns_sim.nim:82-86`).

### F8 — the blocked-push velocity rule differs from the note; `accel` is also scaled by `carrySpeedPct`

- **Where:** `src/hns/motion.nim:218-224` and `src/hns/motion.nim:269-275`.
- **Observed.** On a refused push the code zeroes the *carry* and breaks
  (`carry = 0; break`, `223-224`) and increments `pushBlockedTicks`; it does not zero `player.velX`
  / `velY`. The note (tick step 6) says "the cog's velocity on the blocked axis is zeroed".
  Behaviourally the cog still does not move (carry is re-accumulated from velocity next tick and
  re-zeroed), so this is a wording/implementation divergence rather than a stuck cog — inferred.
  Separately, `applyInput` scales acceleration as well as `maxSpeed` when holding
  (`accel * carrySpeedPct div 100`, `272-273`); the note describes only `MaxSpeed` being scaled.

### F9 — `client/broadcast_core.js` is the starter's file, not the fork the note describes

- **Where:** `diff /workspace/starters/coworld-ctf/client/broadcast_core.js
  /workspace/cogame-hide-and-seek/client/broadcast_core.js` → **4 changed lines**: line 49
  (`CTF_WIRE` → `HNS_WIRE`) and line 268 (a comment path `src/ctf/sim.nim` → `src/hns/sim.nim`).
- **What the note says** (§Viewer): "`client/broadcast_core.js` is forked … **Deleted:** every
  weapon, paint, hill and flag draw call and the FPV pipeline. **Added:** `drawRoom`, `drawObjects`
  (with the padlock overlay), `drawCones`, `drawVaultArc`, `drawExposureRibbon`, `drawFortPanel`."
  `grep -n 'drawRoom\|drawObjects\|drawCones\|drawVaultArc\|drawExposureRibbon\|drawFortPanel'
  client/broadcast_core.js` → no hits.
- **Observed:** nothing is missing functionally. The starter's `broadcast_core.js` is a generic
  sprite compositor with no game-specific draws either (`grep -ic 'flag\|paint\|hill'` on the
  starter's copy returns 12 hits, all of which are `ZoomableFlag`, `layer.flags` and the word
  "repaint"). The board drawing this game needs lives server/wasm-side in `src/hns/global.nim`
  (objects `595-612`, padlocks `604-612`, cones `572-592`, tethers `649-665`, spotted ring
  `632-648`). For checklist 14, byte-identity is the strongest possible provenance; the note
  describes a file that does not exist. Reporting the doc-vs-code mismatch only.

### F10 — `replay_broadcast.html` is not "starter bytes then an append"; the shipped test asserts something weaker

- **Where:** `client/replay_broadcast.html`; splice banner at `:2652`.
- **Observed.** The fork and the starter share a **159-byte** common prefix and then diverge at the
  `<title>` (`Ctf — Broadcast Replay` → `Hns — Broadcast Replay`), and the region above the banner
  is edited throughout (deletions of `#viewpanel`/`#fpv`/`#povBadge`, the label re-mappings). The
  note's test 36 says "the file begins with the starter's bytes up to the documented splice marker
  and only appends after it"; that is not true of the shipped file. `tests/test_hns_viewer.nim:38-69`
  asserts the weaker (and achievable) property: the inherited region still carries 41 named ids and
  `window.PaintballChrome`, the appended region installs through `install: function (ctx)` and
  closes the document.
- **Against checklist 14 the file passes what I could check:** 165 843 B vs the starter's 234 070 B
  (71 %, consistent with the enumerated deletions, not a rewrite); `chrome_common.js` is
  **byte-identical** (sha256 `7ace7287…d72f7c`, 40 022 B, pinned at `tests/test_hns_viewer.nim:11-16`);
  all of `#viewport #stage #board #lightpool #grain #lockerroom #lk-bg #lk-art #lk-sprites #lk-cap
  #chrome #scorebug #plates-l #plates-r #clock #clock-time #clock-caption #bannerlane #killfeed
  #mmwarn #transport (all 13 children incl. #ffwd-mini) #scrub #momentum #scrub-fill #lulls
  #scrub-win #scrub-head #endcard (5 children) #status` are present; `#viewpanel`, `#minimap*`,
  `#zoom*`, `#fpv*`, `#povBadge` and `attachMinimap` are gone (verified by grep and by
  `tests/test_hns_viewer.nim:72-81`).

### F11 — vision cones are drawn unclipped, and are rebuilt from scratch for every cog every frame

- **Where:** `src/hns/global.nim:431-462` (`buildConeSprite`), called at `572-592` for every live
  cog every frame.
- **Observed (clipping).** The note's readout 2 says cones are "clipped by walls and objects exactly
  as the sim clips it". The code draws the full wedge and layers it under the objects; the code's
  own comment says so (`434-436`: "the board draws the unclipped wedge UNDER the objects, so an
  object drawn on top of it reads as the thing that stopped it"). A wall does not stop the drawn
  wedge.
- **Observed (cost), impact inferred.** `n = range * 2 + 2 = 682` at `sightRange 340`, so each call
  allocates and fills a 682×682×4 ≈ 1.86 MB RGBA buffer, for up to six cogs, on every frame — before
  `addBoardSpriteChanged`'s dedup (`global.nim:207-227`) can discard it, and the dedup key includes
  the aim (`585-587`), which changes almost every tick. The note claims "one static bake per room,
  so the per-frame cost is six cogs, eight objects and the overlays".
- **The one measurement I have:** CI run 33125685503's viewer smoke reports
  `soak: 10s of playback kept advancing ("0 / 948" -> "174 / 948" -> "198 / 948")` — ≈19.8
  ticks/s against `ReplayFps = 24`, i.e. the wasm viewer plays the 900-tick fixture slightly under
  real time. Whether that degrades on the 2160-tick league episode is **untested**.

### F12 — a new float expression feeds a hashed value, in a module the determinism grep does not cover

- **Where:** `src/hns/vision.nim:267-283` (the airborne branch of `playerVisibleTo`), reached from
  `src/hns/phase.nim:109-156` (`scoreExposure`) → `seenTicks`/`hiddenTicks` → hashed at
  `src/hns/sim_state.nim:138-139`.
- **Observed.** The branch computes `cos(float(visionConeDeg) * PI / 180.0)` and
  `sqrt(vx*vx + vy*vy)` on float coordinates. This expression is **new** — the starter has no
  airborne state — while the note's determinism rule (§Integer arithmetic and determinism) is:
  "What must never happen is a *new* float expression feeding a hashed value".
  `tests/test_hns_determinism.nim:8-11` greps only `objects.nim, phase.nim, fort.nim, motion.nim`,
  so `vision.nim` is out of scope by construction, and `54-59` checks only that the strings
  `coneCos` and `sqrt(d2)` still appear — the note's test 14 says `applyFovCone` is "asserted
  byte-identical to the starter's", and no such assertion exists.
- I read the starter's `castFovOctant`/`applyFovCone` alongside the fork's: the octant cast is
  textually identical, and `applyFovCone` differs only in `visionRange()` now reading
  `config.sightRange` (`vision.nim:83-88`) instead of `gunRange * 3 div 2`, which is the note's one
  declared edit. **Untested:** whether the airborne expression actually diverges native↔wasm; the
  same-libm argument the note makes for `applyFovCone` plausibly covers it (inferred).

### F13 — structural deviations from the note's test layout (content located, not missing)

- `tests/shard_1..4.nim` — **absent**. `ci.yml:115-150` runs every `tests/*.nim` individually in
  debug and release instead, and `tests/tests.nim:1-19` imports all 13 modules for local runs.
  Nothing is lost; the note's §Tests preamble names files that do not exist.
- `tests/test_hns_scoring.nim` — **absent**; its asserted content is
  `tests/test_hns_sim.nim:314-343` (`marginPermille` cases; 500 randomised end states with
  odd `huntTicks`; `sum(scorePermille) == 0`; range ±1000). Two clauses of the note's test 12 are
  **not** asserted anywhere: `win == (scorePermille > 0)` and "an all-zero margin leaves every `win`
  false" (`roster.nim:490` implements both).
- `tests/test_hns_tuning.nim` — **absent**; content at `tests/test_hns_control.nim:249-272` (see F6).
- Extra files not in the note: `tests/test_hns_engine_support.nim`, `tests/helpers.nim`,
  `src/hns/map_art.nim`, `tools/ci/page_smoke.mjs`.

### F14 — the endcard-vocabulary test is phrase-level, not the note's word list, and inherited dead chrome survives

- **Where:** `tests/test_hns_endcard_labels.nim:35-46`.
- **Observed.** The note's test 40 asks for zero matches of the word list `Lives, LIVES, Clstr,
  Cap<, flag, heart, paint, hopper, hill, POV, spray, grenade, med kit, kill, HP` outside comments.
  The shipped test uses 17 whole phrases instead, with the narrowing documented in-file (`42-46`:
  "the inherited chrome legitimately keeps ids like `lives-num` and `flagicon`"). Consequences I
  verified in the page: `buildFlag()` and its flag SVG survive at
  `client/replay_broadcast.html:1550-1558`; the `.ec-heart` endcard glyph rules and their base64
  heart images survive at `905-917` (the note's removal list names ".ec-heart endcard glyphs");
  `.squad-pip` survives at `1112` (also on the removal list); the achievement plumbing `ACH_FOCUS`
  survives at `1508-1523`. All of it is unreachable for this game's state stream (inferred: nothing
  emits `s.ach`, flags or hearts), so this is dead inherited code, not a visible string.
- The `git log -p -- tests/` history for this run shows this file was **tightened**, not loosened
  (`c7e4020` adds four forbidden phrases and one required string).

### F15 — CI gates the note names that do not exist

- `.github/workflows/ci.yml` has exactly three jobs. Absent relative to the note:
  - the manifest-CLI step (note test 34: "a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest`"); the only place `coworld build` runs is
    `coworld-release.yml:159-172`, i.e. at release time, not in CI;
  - the tuning sweep `--check` re-run (§Scripted baselines);
  - `tools/ci/page_smoke.mjs` is never invoked by CI directly — only from
    `tests/test_hns_viewer.nim:206-220`, which **skips itself** when `node` is absent (`215-216`).
    It does run inside the `test` job because GitHub runners have node (inferred).
  - the `wasm_replay_smoke.cjs` step (note test 45): `tools/wasm_replay_smoke.cjs` is committed but
    `grep -n wasm_replay_smoke .github/workflows/*.yml` → no hits.

### F16 — `docker_smoke.sh` does not fail on `reason == "fault"`, and has no expected-key set

- **Where:** `tools/ci/docker_smoke.sh:299-308`.
- **Observed.** The script checks only that `results.names`/`results.scores` are `seats` long and
  then *prints* the reason (`print(f"episode end reason: {reason}")`). The note (§End conditions)
  says "A defect: `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it
  [`fault`]", and §Results document says adding a key means updating "`tools/ci/docker_smoke.sh`'s
  expected-key set" — there is no such set. The file is the shared template with only the three
  documented substitutions (`diff` against `templates/tools/ci/docker_smoke.sh` shows 5 hunks, all
  `<slug>`/`<IMAGE>`/`<SEATS>`), which is what checklist 6 wants; the note over-claims.

### F17 — no shout-jitter stream; `heard` reports the exact shout position

- **Where:** `src/hns/decide.nim:187-196` puts `shout.x, shout.y` straight into the observation.
  `grep -rn 'jitter' src/` → no hits; only three draws come off `setupRng`
  (`sim.nim:445` room, `sim.nim:459`/`objects.nim:170-232` deal, `sim.nim:268-300` hider pads).
- **What the note says:** §observation — "the team that shouted, the text, **the jittered
  position**"; §determinism draw 4 — "the **shout jitter** stream, the starter's, used only for the
  cosmetic offset of a heard shout". Absent. A shout therefore leaks the shouter's exact pixel.

### F18 — the record→re-derive test never covers a shout, which is hashed state

- **Where:** `tests/test_hns_engine_support.nim:19-66` (`recordEpisode`) never calls `applyShout`
  and never writes a shout chat line, so the replay it produces has only control records
  (`{`-prefixed). `tests/test_hns_replay.nim:26-61` re-derives that replay.
- **Observed.** The live server *does* write shouts (`src/hns/server.nim:1938-1941`), playback
  re-applies them into hashed state (`src/hns/replays.nim:410-413` → `sim.applyShout`), and
  `recentShouts` is in `gameHash` (`src/hns/sim_state.nim:145-154`). I traced the tick alignment —
  the server applies the shout and stamps `tickTime(sim.tickCount)` before `sim.step`, and
  `applyReplayEvents` runs before `sim.step` at the same `tickCount` — and it looks correct. This
  is a coverage note, not a defect: the one code path that can move the hash chain through a chat
  record is exercised only by the docker-smoke episode, where a mismatch surfaces as `#mmwarn`
  rather than as a failing gate.

### F19 — three weak or conditional sim assertions

- `tests/test_hns_sim.nim:184-199` (keep-clear) asserts `canPlaceObject(rect) ⇒ not
  keepClearViolated(rect)`. `src/hns/objects.nim:294-319` makes that true by construction
  (`canPlaceObject` calls `keepClearViolated` at `317-318`), so the loop cannot fail. The note's
  test 6 asks for "no sequence of **pushes**" — this tests placement, not pushes.
- `tests/test_hns_sim.nim:218-230` (vault) wraps every launch/airborne/landing assertion in
  `if game.vaultSpanClear(...)`; when the seeded deal offers no clear span the block asserts
  nothing and still prints ok.
- `tests/test_hns_sim.nim:303-312` (sealed scan) asserts only the negative case (a hider in the
  open is not sealed). The note's test 11 asks for the walled-in positive case, the same wall
  unlocked, the cog-sized gap, and the "only at turn boundaries" property.

### F20 — cosmetics

- `src/hns/decide.nim:335-344` — `installOrder` takes `source` and `latencyMs` and `discard`s both;
  the real values travel in `sources`/`latencies` (`decide.nim:399, 409, 510-511`).
- `src/hns/server.nim:1444, 1495, 1503, 1690` — comments still say "holdline baseline" (paintbot's name) where
  this game's fallback is `burrow`.
- `src/hns/decide.nim:410` — `discard index` after the variable is used only in the discarded form.
- The note's §Viewer says the embed bridge posts `ready`; the page posts `boot`/`frame`/`esc`
  (`client/replay_broadcast.html:1524-1526, 1594, 1647, 2439`) — identical in shape to the starter
  (`/workspace/starters/coworld-ctf/client/replay_broadcast.html:1917, 1987, 2040, 3993`). The load
  marker checklist 13 actually requires is present (below), so this is wording only.

---

## Traced and consistent

**CI (checklist 1).** `gh run list -R Metta-AI/cogame-hide-and-seek --branch main -w ci.yml` →
run **33125685503**, conclusion **success**, `headSha a6d3a86cd1f545b6a031bc43d166c758d424776c` —
the reviewed sha. All three jobs green; `wasm-viewer` includes the step
"Load the bundle in a real browser" with conclusion `success` and it is not `continue-on-error`
(`ci.yml:297-323`). `git log -p --stat -- tests/` across this run's five commits shows only
additions and tightenings: `a6d3a86` +29 lines, `c7e4020` +5/−2 (adds four forbidden phrases and a
required string), `c011e86` +17/−6 (unique temp paths), `d28389d` +17/−1. No assertion deleted, no
tolerance widened, no `skip` added, no test file removed.

**Replay re-derivation (checklist 2).** `src/hns/replays.nim:488-496` — `stepReplay` re-applies the
recorded masks (`443-453`) and chat records (`395-414`) and then calls `checkReplayHash`
(`455-486`), which compares `sim.gameHash()` against the recorded hash **at every recorded tick**
and latches `hashMismatchTick`. `tests/test_hns_replay.nim:16-61` records a real six-seat episode
and re-derives it for **all three end reasons** (`full_time`, `wall_clock`, `sim_fault`), asserting
`mismatch < 0` each time. The viewer runs the same code: `replay-viewer/hns_replay.nim:56-93` builds
its frames from `initReplayRuntime` + `advanceReplayFrame` + `buildReplayViewerPacket`
(`src/hns/replay_runtime.nim:51-140`) — the display is derived from the re-simulated sim, not from a
parallel recording. The load-bearing stop is one record applied by the same proc on both sides
(`src/hns/sim.nim:596-629`, `631-652`; recorder `server.nim:1364-1379`, and the "step one more tick
and hash it" detail is present in both the server and `tests/test_hns_engine_support.nim:102-120`).

**Static viewer (checklist 3).** `coworld_manifest_template.json` declares
`game.replay_viewer = {"bundle": "static-replay-viewer"}` (asserted at
`tests/test_hns_manifest.nim:36-37`); `tools/build_replay_viewer.sh` exists, is mode **100755**, and
is invoked by path at `ci.yml:253`, with the exec bit asserted at `ci.yml:229-240`; the manifest
declares no `/client/replay` path anywhere (`grep '/client/replay' coworld_manifest_template.json`
→ no hits). The bundle fetches only its own assets plus the `?replay=` URL
(`replay-viewer/static_replay.js:184-206`).

**Both name spaces (checklist 4).** `src/hns/roster.nim:46-52` — `cogAlias` is
`roleLabel(team) & "-" & IdentityNames[slot div 2]`, and it is the only name in the observation
(`decide.nim:153, 172, 182, 219, 239`), in orders, and in sprite labels
(`global.nim:623-624`). Real names live in `results.names` (`roster.nim:457-461`), in the replay's
join records (`server.nim:1586-1594`) and in the scorebug. `showPlayerLabels: false` in both
variants and the fixture (asserted `tests/test_hns_manifest.nim:138-139`).

**Degrade-never-hang (checklist 5).** Every wait I could find is bounded:
`attempt1Ms 7000` / `retryMs 3000` handed to `curl.makeRequests` as whole seconds
(`decide.nim:447-465`); at most two attempts (`while open.len > 0 and attempt < 2`, `438`);
an outer monotonic `turnBudgetMs 16000` checked before each batch (`441-446`); the rate floor sleeps
at most `turnSpacingMs` and only when a batch is actually going out (`416-422`); the rolling 60 s
rate guard never sleeps (`315-334`); the budget guard drops every seat to scripted when
`elapsed + 2 × ceil(turnBudgetMs/1000) > wallClockBudgetSeconds` (`370-378`), i.e. at 628 s of 660;
`lobbyJoinTimeoutTicks` bounds the lobby and does **not** kill the episode in squad mode
(`server.nim:1492-1505`, roster completion at `1606-1632` with `deadSeats` set); the engine stop
fires at `wallClockBudgetSeconds` at the top of the loop (`server.nim:1355-1379`); the frame limiter
sleeps ≤2 ms per iteration until the frame elapses (`server.nim:949-960`); the shutdown grace is
`ShutdownGraceSeconds = 20` (`server.nim:138, 2269-2272`). `boundedOrderRecord`'s shrink loop is
guarded at 12 iterations (`directives.nim:323-331`); `applyMomentumAxis`'s loop decrements or breaks
(`motion.nim:197-224`); `vaultSpanClear` and `nearestOpenCell` are range-bounded
(`objects.nim:368`, `control.nim:107`). Arithmetic: 24 turns × 13 s spacing ≈ 312 s, worst
≈ 384 s + lobby + hold, against 720 s (60 % of 1200) — matches the note's table. All seats go out as
**one** `curl.makeRequests` batch per turn (`decide.nim:449-465`); nothing is sequential.

**`num_agents` (checklist 6).** Present in both variants' `game_config`, in
`certification.game_config`, and pinned `minimum: 6, maximum: 6` in `config_schema`
(verified by reading the JSON; asserted at `tests/test_hns_manifest.nim:115-146`).
`tools/ci/docker_smoke.sh:106-152` is the template's four-invariant block verbatim, and
`SMOKE_SEATS` is substituted to `6` (`:54`) and passed from `ci.yml:184`. I grepped the full CI log
of run 33125685503: **`SEAT-COUNT FAIL` occurs 0 times**; the smoke printed
`smoke OK: seats=6 results=931B replay=34421B reason=complete`.

**Scripted baseline completes an episode (checklist 7, first half).**
`tests/test_hns_engine.nim:10-37` runs a real six-seat all-scripted episode to its natural end and
asserts `reason == "complete"`, `endRule == "full_time"`, `games == 2`, `sum(scorePermille) == 0`,
and every seat-indexed array exactly 6 long. `tests/test_hns_control.nim:34-107` asserts every
baseline order is in the intent enum, names a published object legal for that intent, is inside the
board, `say ≤ MaxSayRunes`, no `radio`/`notes`, and serialises ≤ 1024 B — and that every compiled
mask uses only the eight legal buttons, never opposing directions, and never `A` under cooldown.
The CI smoke episode ended `complete` (log line above).

**LLM reply handling (checklist 8).** Parsing is tolerant: `extractJsonObject`
(`directives.nim:118-157`) scans for the outermost balanced object, tolerates fences and prose, and
falls back to first-brace..last-brace; `tests/test_hns_control.nim:244-247` feeds
`Sure! ```json {…} ``` ok?`. Retry is exactly once — the `attempt < 2` loop at `decide.nim:438`,
with attempt 2 appending "Your previous reply was not usable" (`452-454`). Every failure raises into
`except CatchableError` (`512-522`), which writes a `fallback` record with a cause in
{timeout, transport_error, throttled, parse_error} and re-queues the seat; the second failure lands
in the tail loop (`532-547`) which installs `burrowFor` and writes a second `fallback` record with
the phrase "falling back" that phase 60 greps for (`546`). A 429 with no other model sets
`client.throttled` (`llm.nim:181-187`) and the turn loop breaks out of the retry rather than
spending it (`decide.nim:525-530`). Fallbacks are counted into `results.fallbackTurns`
(`server.nim:1915-1916`, `roster.nim:474-475`) and re-counted at playback
(`sim.nim:679-685`). A reply with `say`/`radio` but no `intent` keeps the standing order
(`directives.nim:232-236`, `decide.nim:494-508`), and an unknown object repairs to the previous
order and increments `ordersRejected` (`decide.nim:502-508`, `server.nim:1918-1919`).

**Rune truncation (checklist 9, except F4).** `truncateRunes` is the single cut
(`directives.nim:70-77`, `runeSubStr`); `sanitizeSay` cuts on runes *before* the ASCII filter
(`79-92`); `sanitizeLine`/`sanitizeRadio`/`sanitizeNote` at `94-103`; the prompt is cut at
registration (`server.nim:1717`) and again in `operatorBlock` (`llm.nim:263`); the policy label at
`directives.nim:355`; `fallback.detail` at `343`; provider bodies at `llm.nim:174, 182, 190, 199`;
the whole directive record shrinks by re-serialising, never by slicing the JSON
(`directives.nim:308-331`). The multi-byte tests are `tests/test_hns_control.nim:216-242` and
`tests/test_hns_replay.nim:86-140`.

**Manifest (checklist 10).** `game.docs` is `{"readme": {"type":"text","value":…}, "pages":[3 ×
{id,title,content:{type,value}}]}` — read from the JSON and asserted at
`tests/test_hns_manifest.nim:49-60`. `game.protocols` carries **both** `player` and `global`, each a
`{"type":"uri","value":"https://…"}` object (`39-47`). `config_schema` is
`additionalProperties: false`, requires `tokens` + `players`, gives every array `minItems`/`maxItems`
(`tokens` 6/6, `players` 6/6, `slots` 0/6), has no `maxTicks`, and pins `num_agents` 6/6.
`results_schema` is closed and its `reason`/`endRule` enums are exactly the note's three and four
values; `tests/test_hns_engine.nim:39-56` asserts the emitted key set equals `ResultsKeys`
(`roster.nim:524-529`) equals the schema's property set, in both directions. Top-level
`episode_timeout_minutes: 20`, five tags, no `game.tags`, no top-level `version`.

**Legibility at 360 px (checklist 11).** `client/replay_broadcast.html:2678-2683` —
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }`.
Labels are hidden under `.tiny` (`2725-2727`), toggled at `boardW <= 620` by the starter's
`relayout()` (`:2620`) — the checklist says 640 px; the threshold is the starter's inherited 620 and
the note documents it. `--band`/`--topband`/`--hudscale` are set on `document.documentElement`
(asserted `tests/test_hns_viewer.nim:133-145`, which checks `root.style.setProperty('--band'`);
`#endcard { bottom: var(--band, 0px) }` is kept (`:717-739`) and dismissed by every seek
(`classList.remove('on')`). The exposure ribbon, the one absolutely-positioned addition, sits at
`bottom: calc(var(--band, 0px) + 1px)` — asserted at `tests/test_hns_viewer.nim:147-155`, which also
caps the appended block at one absolutely-positioned overlay.

**Release order and scaffold (checklist 12).** `coworld-release.yml` runs build (`:159`) → certify
(`:173`, with `--timeout-seconds 300` at `:184`) → **upload policies** (`:216`) → upload-coworld
(`:314`) → secret put (`:410`), with the ordering rationale in the header comment (`:10-15`).
All three workflows present. `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both
mode **100755**. `tools/ci/policies.json` has four entries — two `PLAYER_PROMPT` champions
(`hns-quartermaster`, `hns-torchbearer`) and two scripted fillers (`hns-burrow`, `hns-scatter`) —
with champion #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; asserted at
`tests/test_hns_manifest.nim:199-223`. The placeholder gate
(`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files) **exits non-zero, i.e. finds
nothing** — I ran it.

**Viewer executes (checklist 13).** `wasm-viewer` `needs: docker-smoke` (`ci.yml:216`) and loads the
replay docker-smoke produced (`:281-308`). The link flags and the bootstrap come from the **same**
starter and agree: `replay-viewer/config.nims:42-54` has **no** `MODULARIZE` and **no**
`EXPORT_NAME`, emits `hns_replay.js` non-modularised, and carries `-s ABORTING_MALLOC=1`,
`-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`,
`-s EXPORTED_RUNTIME_METHODS=HEAPU8` and the 13 `_hns_*` exports; the Worker sets
`Module.onRuntimeInitialized` (`static_replay_worker.js:8, 188, 192`) and `importScripts(...,
'./hns_replay.js')` (`:239`) — which is the correct pairing for a non-`MODULARIZE` build.
`diff` against the starter shows config.nims, static_replay.js and static_replay_worker.js are the
starter's files with identifier renames only (`ctf_` → `hns_`, `CtfStaticReplay` → `HnsStaticReplay`,
worker name). `data-replay-loaded="true"` is set on `<html>` in the `'loaded'` branch
(`static_replay.js:158-162`) and `data-replay-error` in `showFailure` (`:14-20`) — both the
starter's own code paths. CI evidence: the smoke reported
`soak: 10s of playback kept advancing ("0 / 948" -> "174 / 948" -> "198 / 948")`.

**Resolution rules.** I walked `src/hns/sim.nim:496-594` against the note's thirteen ordered steps:
tick increment and phase transition at `503, 524-531` (release event + fov invalidation + immediate
sealed scan); mask compile with a frozen seeker forced to `0` at `533-543`
(`frozenSeeker` = prep ∧ Blue, `phase.nim:47-51`); aim `545-547`; grab `549-550`; lock `552-553`;
movement `555-557`; vault `559-560`; geometry refresh inside `moveObject`'s dirty rect
(`objects.nim:131-158, 321-326`) with `geometryEpoch++` and cache invalidation; fov refresh skipping
frozen seekers `562-567`; exposure hunt-only `569-577`; sealed scan at turn boundaries `579-586`;
shout expiry `588-590`; end evaluation `592-594`. Grab ties resolve to the lower slot
(`sim.nim:123, 151-153`, tested `test_hns_sim.nim:88-103`); the probe returns the **first** object
along the aim (`objects.nim:259-273`); `mayTouch` refuses the other team's locked object
(`objects.nim:249-257`); lock cooldown is 24 ticks per cog (`sim.nim:164-199`); keep-clear discs are
enforced inside `canPlaceObject` so a refused push moves neither body and increments
`pushBlockedTicks` (`objects.nim:294-319`, `motion.nim:73-90, 205-222`); the vault needs
`along ≥ maxSpeed div 2` and a span ≤ `vaultSpanPx`, lasts `vaultTicks` at `VaultSpeed`, refunds to
the foot on a blocked landing, and cannot grab or lock while airborne (`sim.nim:204-262`).

**Scoring.** `marginPermille = (hidden − seen) * 1000 div played` from the hiding trio's view, 0 for
an unplayed game (`phase.nim:62-69`); `scorePermille = Σ side(s,g)·margin[g] div games` with
`side = +1` when the seat hid (`phase.nim:74-86`); `scores[s] = permille/1000.0`,
`win[s] = permille > 0` (`roster.nim:488-490`). Nim's `div` truncates toward zero, so opposite-sign
seats are exact negatives and the six sum to zero — asserted over 500 randomised end states
(`test_hns_sim.nim:321-343`), for a deadline episode (`352-364`) and for a dead-seat episode
(`test_hns_engine.nim:116-125`). `settleEpisode`/`forceWallClockStop` pad the per-game arrays so a
stopped episode is still rankable (`sim.nim:596-613, 689-696`).

**Seeding.** `pickRoom` is `pool[seed mod 3]` with a negative-seed guard (`room.nim:469-476`); the
deal is shuffled off `setupRng` before any seat connects (`sim.nim:431-459`, `objects.nim:170-232`);
hider pads come off the same stream (`sim.nim:268-300`); the room document is pinned into the config
**as a document** and re-read from the replay, never from disk
(`sim_config.nim:337-340, 420-423`; `room.nim:490-496`); `tests/test_hns_seeding.nim` asserts all of
it including the anti-collusion pin. The seed is randomised before `config.update`
(`src/hide_and_seek.nim:79-89`).

**Replay writer.** Magic `COWLDHNS`, format version 1, game name/version header
(`replays.nim:143-154`); per-cog mask deltas (`replays.nim:162-183`, written at
`server.nim:1957-1958` and, for non-Playing ticks, zeroed at `1967-1968`); one `gameHash` per tick
(`server.nim:2043`); chat records for `register`/`directive`/`fallback`/`budget_guard`/`stop`/
`result`, all `{`-prefixed and told apart from real shouts by that first byte
(`replays.nim:410-413`; `sanitizeSay` strips `{`/`}` from shouts, `directives.nim:86-90`).
Config echo carries seed, `num_agents`, `mapSpec`, `crates/panels/ramps`, all the deadlines and the
player names (`sim_config.nim` `configJson`), so the deal re-derives; `tests/test_hns_replay.nim:63-84`
asserts the bytes alone resolve the pinned room. Smoke replay size 34 421 B, in line with the note's
~40 KB estimate.

**Rooms.** All three are 720 × 400, `symNone`, with 23-25 `objectSpawns`, 8 pockets, 6 patrol
anchors and exactly 3 + 3 pads; sha256s pinned at `tests/test_hns_room.nim:9-13` and re-validated
through the real loader, including `validateMapWalkability`'s "every region reachable from every
seeker pad with no objects placed" flood fill (`room.nim:310-360`).

---

## Could not determine

- **Whether the shout bubble actually clips in a rendered frame (F2).** I have the placement
  arithmetic and the missing clamp; I do not have a frame. What would settle it: a render at a
  shout whose cog sits within 53 px of the top wall (or 39 px of the left wall) with the bubble's
  bounding box logged — i.e. exactly the fixture F3 says is missing.
- **Whether the per-frame cone rasterisation (F11) breaches the frame budget on a full 2160-tick
  episode.** CI has only ever played the 900-tick fixture, at ≈19.8 ticks/s. What would settle it:
  a `viewer_smoke.mjs --soak` run against a league-length replay, or a `hns_frame` timing histogram.
- **Whether the new airborne float expression (F12) diverges native↔wasm.** No mismatch has been
  observed (`hns_mismatch_tick` was not reported by the CI smoke), but no test forces an airborne
  visibility check across the native↔wasm boundary. What would settle it: a committed fixture replay
  containing a vault, run through `tools/wasm_replay_smoke.cjs` — which is committed but,
  per F15, never invoked by CI.
- **Whether `flinchRadius`/`chaseRadius` would move the sweep once F1 is fixed.** The flat grid in
  `tools/ci/baseline_tuning.json` is consistent with F1 but does not prove causation; re-running
  `tools/tune_baselines.nim` after a fix would settle both F1's blast radius and F6's sign.
- **`git log -p -- tests/` "since run start" boundary.** I read every commit that touches `tests/`
  in the repo's whole history (five of them, all in this run) rather than filtering by date, so the
  item-1 verdict covers the full history and not just the window.
