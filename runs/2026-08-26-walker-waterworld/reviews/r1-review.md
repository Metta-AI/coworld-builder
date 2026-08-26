# r1 review — walker-waterworld

Repo: `/workspace/cogame-walker-waterworld` @ `41bae66305db6da58dc0256d54bb5c3ac913cce9` (main)
Starter: `/workspace/starters/coworld-ctf` @ `bb1bf7b` (read-only mount)
Design note: `/workspace/coworld-builder/runs/2026-08-26-walker-waterworld/design.md` (1648 lines)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
simultaneous-decision batching rule)
Files read: 62 (all 21 `src/waterworld/*.nim`, both entrypoints, all 17 `tests/*.nim`
+ `helpers.nim`, all 4 `replay-viewer/*`, `client/{replay_broadcast.html,chrome_common.js,broadcast_core.js}`,
`scripts/{fork_broadcast_page.py,waterworld_block.html,art/split_sheet.py}`, all 3 workflows,
`tools/ci/{docker_smoke.sh,policies.json,viewer_smoke.mjs,renderer_fixture.html,baseline_tuning.json}`,
`tools/{replay_summary.py,build_replay_viewer.sh}`, `coworld_manifest_template.json`, `AGENTS.md`,
`docs/*`, plus the CI logs for run 32954530460)

**Method note.** Where provenance mattered I did not eyeball a diff: I re-ran
`scripts/fork_broadcast_page.py` against the mounted starter into a scratch copy and diffed
the result against the committed page (F-P1 below), and I `sha256sum`'d every asset the note
claims is inherited.

---

## Blocking

All four blocking findings are the **same class**: assertion changes made to `tests/` during
this run, in commit `b3686ba` ("Fix compile errors and land swept baseline tuning"). Checklist
item 1's second half is explicit — *"a deleted assertion, a widened tolerance, a
`skip`/`t.Skip`/`xfail`/`--skip` added, or a test file removed is a blocking finding"* — and it
names `git log -p -- tests/` as the way to see them. I am reporting them under that rule and
recording the builder's stated justification for each verbatim, because in two of the four the
justification is sound and in two it is either arithmetically short of the change made or
absent from the builder's disclosure list. The judge should read the hunks.

`git log --oneline -- tests/` for this run: `a8d30d1` (all 18 files created), `b3686ba` (14
files changed, 466+/178−), `41bae66` (test_viewer +59, additive only).

### F1 — the rock-tangent assertion's tolerance was widened from a sign test to a 69° cone, and the comment's justification supports ~5.6°
- Where: `tests/test_control.nim:301-312`; before: `git show b3686ba -- tests/test_control.nim` (old lines 246-256)
- Observed. The assertion was:
  ```nim
  check("the tangent rule never thrusts straight into the rock", dot <= 0, $dot)
  ```
  and is now:
  ```nim
  # The steering is quantised to 32 directions, so a tangent lands within
  # 5.6 deg of perpendicular: assert the ANGLE stays well off the rock
  # (a cosine under 0.35 is more than 69 deg away) rather than a bare sign.
  bound = int64(0.35 * sqrt(float(toRockX * toRockX + toRockY * toRockY)) * float(Q12))
  check("the tangent rule never thrusts into the rock", dot < bound, $dot & " vs " & $bound)
  ```
  `dot / (|toRock| · Q12)` is exactly `cos(angle between the thrust direction and the rock)`.
  The old bound admitted `cos ≤ 0` (≥ 90° away). The new bound admits `cos < 0.35`, i.e. any
  angle greater than 69.5° — a thrust with a component **toward** the rock up to 35 % of its
  magnitude now passes.
- Arithmetic against the stated reason: the block sets `sim.skimmers[0].vx = 0; .vy = 0`
  (`test_control.nim:273-274`), so in `control.nim:236-245` the acceleration vector is
  `steer · target` and its direction *is* the steer direction; `nearestDirIndex` over 32
  entries can be off by at most half a step, 5.625°. A perfect tangent quantised by ≤ 5.625°
  gives `|cos| ≤ sin(5.625°) = 0.098`. The comment's own justification therefore supports a
  bound near 0.10; 0.35 is ~3.6× that. I could not determine from the tree whether 0.098 would
  pass — that needs a run (see *Could not determine*).
- Also changed in the same hunk, and worth separating out because it is a **strengthening**:
  the trigger gate moved from "the skimmer is within keep-out + 0.30 m of the rock" to "the
  straight path p → G clips the keep-out ring" (`test_control.nim:279-299`), which is the
  rule's own condition, and a new `check("the sweep actually exercised the rock rule",
  clipping > 200)` at line 313 pins that the block is not vacuous. So the hunk widens the
  tolerance and broadens the trigger set at the same time.
- Checklist item: **1** ("no test … loosened during this run" — "a widened tolerance").
- Why blocking: item 1 makes a widened tolerance blocking on its face, and here the widening
  is 3.6× larger than the reason given for it, so a real regression in the tangent rule (a
  thrust up to 69° off-tangent toward the rock) would now pass.

### F2 — the poison-repulsion assertion was deleted and replaced with a weaker, differently-shaped one
- Where: `tests/test_control.nim:191-227`; before: `git show b3686ba -- tests/test_control.nim` (old lines 185-231)
- Observed. The old block asserted, for **five** standoffs `[500, 900, 1200, 1800, 2500]` mm,
  with the waypoint set *straight through* a pinned bloom, that after 48 ticks
  `sim.poison[0].state == psLive` — i.e. "the skimmer did not eat the poison". The new block
  moves the bloom **0.55 m off** the path (`4_500_000, 6_850_000` against a path along
  `y = 7_400_000`), measures closest approach for **three** standoffs (0, 900, 1800), and
  asserts only:
  ```nim
  check("a standoff holds the skimmer farther off than no standoff at all", narrow > off, …)
  check("a wider standoff holds it farther off still", wide >= narrow, …)
  check("and a 1.8 m standoff clears the contact radius entirely", wide > int64(SkimmerRadius + PoisonRadius), …)
  ```
  The property "repulsion prevents the contact" is gone; what remains is monotonicity in the
  standoff plus one absolute clearance at 1.8 m. Standoffs 500, 1200 and 2500 mm are no longer
  exercised.
- The design note asks for the deleted form: §Tests 4 (`design.md:1478-1479`) — *"poison
  repulsion strictly increases the distance to a stationary poison over 48 ticks for every
  `standoff_m ≥ 0.5`"*.
- Builder's stated reason, in the test's own comment (`test_control.nim:191-195`): *"The
  repulsion term is RADIAL, so it cannot sidestep a bloom that sits exactly on the line to the
  goal — it can only slow the approach. That is why `avoid` exists as its own mode."* I
  confirmed this is a true statement about the code: `control.nim:172-187` accumulates
  `unit = normalise(p − z)` scaled by `RepulsionGain · (standoff − d)/standoff` and adds it to
  `normalise(G − p)`; with `z` exactly on the segment `p → G` the two vectors are antiparallel,
  so the sum can only shrink or reverse the steer, never rotate it. This is the builder's
  disclosed deviation (7), and it is a correct description of the mechanism.
- Checklist item: **1** ("a deleted assertion").
- Why blocking: a five-value assertion that the autopilot does not drive into a bloom was
  removed and replaced by a three-value comparison in a geometry the old one did not test. The
  *reason* is legitimate (the old assertion was testing something the radial term cannot do),
  but the removal happened inside this run and item 1 has no "unless justified" clause.

### F3 — the `hold`-brake stop threshold was widened 100× during this run
- Where: `tests/test_control.nim:91-97`; before: `git show b3686ba -- tests/test_control.nim` (old lines 91-96)
- Observed. `if speed < 1.0 and stopped < 0:` became `if speed < 100.0 and stopped < 0:`
  (speed here is in µm/tick), and the label changed from "hold brakes to a full stop within 96
  ticks" to "hold brakes to a standstill (under 0.01 m/s) within 96 ticks".
- Builder's stated reason (`test_control.nim:91-93`): *"Nim's `div` truncates toward zero, so
  drag cannot take the last unit off."* I verified this against the code: `sim.nim:166`
  computes `s.vx - (s.vx * 39) div 1024`; for `|v| < 1024/39 = 26.3` µm/tick the drag term is
  0, so drag alone cannot reach zero. And the servo cannot either: at `|v| = 26` µm/tick,
  `control.nim:247` computes `level = round(|a| · 7 / MaxThrustAccel) = round(26·7/5208) =
  round(0.035) = 0`, so `cmd = 0`. An exact stop is genuinely unreachable, and the old
  assertion was unsatisfiable.
- The arithmetic bound is ≤ 26 µm/tick (0.00063 m/s); the new threshold is 100 µm/tick
  (0.0024 m/s), ~3.8× that.
- Checklist item: **1** ("a widened tolerance").
- Why blocking: literal read of item 1. Unlike F1, the widening here is provably *necessary*
  (the old bound could never pass), so the judge may reasonably dismiss it; I am reporting it
  because item 1 names the mechanical test and this is one of the hunks it will surface.

### F4 — a near-tangent skip was added to the rock ray-cast pin
- Where: `tests/test_tank.nim:143-150`; added in `b3686ba`
- Observed. Inside `block rayCasts`, before the float-reference comparison:
  ```nim
  let perpendicular = sqrt(max(0.0, fx * fx + fy * fy - b * b))
  if abs(perpendicular - float(RockRadius)) < 20_000.0:
    continue
  let gotRock = float(rayRockDistanceUm(mx, my, dir))
  check("the integer rock cast matches a float ray-cast within 2 mm", abs(gotRock - rock) <= 2000.0, …)
  ```
  Every ray whose perpendicular distance to the rock centre is within 20 mm of `RockRadius`
  (900 000 µm) is now excluded from the pin. The stated reason (`test_tank.nim:143-147`) is
  that the hit distance's sensitivity diverges at tangency, so the 0.1 mm quantisation of
  `tank.rayRockDistanceUm` (`tank.nim:240-265`) can move the answer by centimetres or flip a
  graze into a miss. That is a correct statement about `t = (-b - isqrt(b²−ac)) div isqrt(a)`
  near `disc = 0`.
- Checklist item: **1** — this is a coverage exclusion added to a test during the run. Item 1
  names `skip`/`t.Skip`/`xfail`/`--skip`, which are test-*framework* skips; a `continue` over a
  sample class is not literally one of those. I flag it as touching item 1 and leave the
  categorisation to the judge; it is the weakest of the four.
- Why blocking (if it is): the ray-cast/float-reference pin the design note asks for
  (`design.md:1470-1471`, *"a ray's `rock`/`wall` distance matches a float ray-cast to within
  2 000 µm"*) now has a hole exactly where the integer cast is least accurate.

**Not a loosening — recorded here so it is not mistaken for one.** `tests/test_physics.nim:59`
changed from `"level 7 for 24 ticks reaches 2.6 .. 3.3 m/s"` to `"1.8 .. 2.1 m/s"`, and a new
assertion `"held at level 7 it settles on the 3.24 m/s terminal speed"` (3.15–3.25) was added
at line 66. The new band is **narrower** (0.3 wide vs 0.7) and an assertion was **added**. I
checked the design note's number and it is arithmetically impossible from its own constants:
with `a = MaxThrustAccel = 5208` µm/tick² and drag `r = 985/1024`, `v₂₄ = a·r·(1−r²⁴)/(1−r) =
79 738` µm/tick = **1.914 m/s**, and the asymptote is `a·r/(1−r) = 131 540` µm/tick =
**3.157 m/s** (clamped at 3.24). This is the builder's disclosed deviation (6) and it is what
it claims to be. It is documented in the test at `test_physics.nim:41-44`.

---

## Non-blocking

### F5 — the inter-batch floor sleeps *inside* the per-turn budget window, so a full 12 s spacing can pre-empt the retry
- Where: `src/waterworld/decide.nim:288-291`, `:341-347`, `:354-358`
- Observed, step by step. `turnStart = getMonoTime()` is taken at line 291, before anything
  else. The rate floor at 341-344 then sleeps up to `turnSpacingMs` (12 000 ms in both shipped
  variants) *after* `turnStart`. The attempt loop's guard at 354 is
  `if getMonoTime() - turnStart >= budget` with `budget = turnBudgetMs` (16 000 ms). So:
  sleep 7 s + attempt-1 deadline 9 s = 16 s elapsed → the guard trips and the **retry is
  skipped**, with `fallbackRecord(…, "timeout", "per-turn budget exhausted before attempt 2")`
  written. Worst case the whole `turn()` call takes `12 + 9 = 21` s, not the 16 s the note
  describes.
- What the note says: `design.md:498` — *"the whole turn is wrapped in `turnBudgetMs = 16 000`
  (`attempt1Ms + retryMs = 14 000 ≤ 16 000`, asserted by §Tests 12)"* — i.e. the budget is
  sized to cover the two attempts, with the 12 s floor treated as separate
  (`design.md:500-501`, "measured start-to-start").
- Not a hang: both the sleep and both deadlines are bounded, so checklist item 5 is not
  falsified. The episode arithmetic is unaffected — the floor is start-to-start, so 24 turns
  still cost `23 × 12 + 16 = 292` s, and `test_engine.nim:141-147` asserts the 416 s worst case
  against the 660 s stop. The consequence is behavioural: on turns where the floor happens to
  be long, a seat whose first call fails gets no retry.
- Checklist item: advisory (touches 5 and 8, falsifies neither).

### F6 — the inter-batch floor is a plain `os.sleep`, not the "stop-interruptible" sleep the note describes
- Where: `src/waterworld/decide.nim:344` — `sleep(min(sim.config.turnSpacingMs, sim.config.turnSpacingMs - since))`
- Observed: `std/os.sleep`. Nothing can shorten it; the engine's wall-clock stop
  (`server.nim:494-501`) is only evaluated at the top of the next loop iteration, so a stop
  that becomes true during the sleep is acted on up to 12 s late.
- What the note says: `design.md:501` — *"a bounded, stop-interruptible `sleep`"*.
- Bounded, so item 5 holds. Checklist item: advisory.

### F7 — `tests/test_engine.nim` never drives a fake LLM client, so three assertions the note promises are absent
- Where: `tests/test_engine.nim:27-47` (the batching block), and `:19-21`
- Observed. The test sets `ANTHROPIC_API_KEY`/`AWS_*` to empty so
  `newLlmClient` (`llm.nim:126-132`) disables itself, and then asserts the batch **shape**:
  `engine.openSeats(sim).len == 4` and `engine.batchBodies(...).len == 4`, with the comment
  *"a length of four here IS 'seats are never queried sequentially'"*. There is no fake client
  and no `makeRequests` interception anywhere in `tests/` (`grep -rn "throttl\|attempt" tests/`
  returns only `throttle255` field uses and `test_manifest`'s arithmetic check).
- What the note says: §Tests 7 (`design.md:1501-1503`) — *"the fake records in-flight windows;
  the test asserts all four intersect … the per-turn budget is enforced with a hung client"*;
  §Tests 6 (`design.md:1498-1500`) — *"Two consecutive failures ⇒ the `shoal` intent plus a
  `fallback` record; a timeout on attempt 1 ⇒ exactly one retry; a `throttled` client ⇒ **zero**
  retries."* None of those three is asserted anywhere.
- The **behaviour** is present and I traced it: one batch (`decide.nim:361-376`,
  `curly.RequestBatch` + `client.curl.makeRequests(batch, max(1, deadlineMs div 1000))`,
  identical in shape to the starter's `src/ctf/decide.nim:407-427`); retry once
  (`while open.len > 0 and attempt < 2`, line 351); throttle fast-fail (lines 408-414); fallback
  recorded with cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials,
  budget_guard} (lines 356, 396-402, 422-429). Checklist item 8 asks for the behaviour, not a
  test, and item 2's "a test asserts it" clause is about re-derivation, which *is* tested.
- Checklist item: advisory (touches 8 and the simultaneous-decision rule; falsifies neither —
  the batching is structurally one `makeRequests` call, which I read directly).

### F8 — `tests/test_server.nim` tests a *copy* of the registration parser, not the server's
- Where: `tests/test_server.nim:21-37` vs `src/waterworld/server.nim:193-215`
- Observed: the test re-declares `proc parseRegistration` inline with the comment *"The
  server's own parser, re-declared here in the shape the server uses it"*. The two bodies are
  currently identical, but a change to `server.nim`'s copy would not be caught.
- This is the builder's disclosed deviation (11) ("test_server.nim covers
  registration/admission/routes without a real websocket") and it is what it claims to be —
  but the disclosure does not mention the re-declaration.
- Checklist item: advisory.

### F9 — the held-registration path is not tested
- Where: `src/waterworld/server.nim:569-599` (the `held` sequence) — no test exercises it
- Observed: the mechanism is present and correct (a registration whose seat is not yet
  admitted is pushed onto `held` and re-inserted into `appState.chatMessages` at line 598-599).
  §Tests 7 (`design.md:1507-1508`) promises *"a registration that arrives before its player
  index exists is **held and applied**, not dropped"*; nothing in `tests/` asserts it.
- Checklist item: advisory.

### F10 — `sanitizeSay` strips every brace, not just a leading one
- Where: `src/waterworld/intents.nim:82` — `if value >= 32 and value < 127 and value != ord('{') and value != ord('}')`
- Observed: any `{` or `}` anywhere in a `say` is silently dropped.
- What the note says (`design.md:976`): *"then ctf's printable-ASCII shout sanitiser (which
  also strips a **leading** `{`, since the replay chat stream distinguishes control records by
  it)"*. The code's own comment (lines 75-78) states the broader rule deliberately.
- Checklist item: advisory. (Rune safety is unaffected — the cut happens first, at line 80, via
  `truncateRunes`, and `test_intents.nim:146-153` pins that a stripped emoji leaves valid UTF-8.)

### F11 — the terminal fallback record always reports `attempt: 2`, even when only one attempt was made
- Where: `src/waterworld/decide.nim:428` — `result.add(fallbackRecord(turnIndex, seat, 2, cause, …))`
- Observed: when the client is `throttled`, the loop breaks after attempt 1 (lines 408-414) and
  the seats land in this block, which hard-codes `attempt = 2`. The `attempt` field's declared
  domain is `1|2` (`design.md:1081`), so the value is legal, but a phase-60 count of "seats
  that used their retry" from the replay would over-count throttled turns.
- Checklist item: advisory.

### F12 — two comments disagree about whether the action log is indexed by seat or by skimmer
- Where: `src/waterworld/server.nim:658-661` vs `src/waterworld/replays.nim:219-221`
- Observed. The server writes: *"The byte is recorded BY SKIMMER INDEX, not by seat"* and does
  `replayWriter.writeInputMaskChange(tickTime(sim.tickCount), i, cmds[i])` for `i` in skimmer
  index order. `replays.nim:220-221` says *"the recorded bytes are indexed BY SEAT, so deleting
  a row would silently re-point every later byte at the wrong skimmer"*. The **code** is
  consistent (nothing shifts the array either way, and `sim.step(cmds)` consumes `cmds[i]` as
  skimmer `i` at `sim.nim:353-357`); only the comment is wrong.
- This is the builder's disclosed deviation (12) and the behaviour is what it claims to be; the
  stale comment is the residue.
- Checklist item: advisory.

### F13 — the board art is newly generated per-role PNGs, not the pixie bakes from starter assets the note describes
- Where: `data/art/{skim_1..4,plankton,poison,rock}.png`, `scripts/art/split_sheet.py:1-26`,
  `src/waterworld/global.nim:300-310`
- Observed: `bakeArtSprite("rock.png", …)`, `"plankton.png"`, `"poison.png"`,
  `"skim_<n>.png"` read committed PNGs generated by `scripts/art/split_sheet.py` from
  `scripts/art/source/{skimmers,particles}_sheet.png`, described in the script's docstring as
  *"Gemini (`gemini-2.5-flash-image`) renders … (playbooks/art-nanobanana.md)"*.
- What the note says (`design.md:1275-1280`): *"The water, caustics, tank rim, rock, skimmer
  hulls, thruster plumes, plankton and poison discs and the vignette are baked once at startup
  with **pixie** … using ctf's shipped `data/arena_floor.png` and
  `client/art/walls/wall_h.jpg`/`wall_v.jpg` … No solid-colour placeholders, no TODO assets, no
  downloaded art."* The water and rim are still pixie bakes from the starter's plates
  (`global.nim:165-167`, `:203-216`); the six object sprites are not.
- This is **not** on the builder's 14-item disclosure list. The assets are real art with a
  documented generator, not placeholders, so the pin's substance holds.
- Checklist item: advisory.

### F14 — several files the note's "kept verbatim" table lists are absent, and only two of them are disclosed
- Where: the note's table at `design.md:753-771` and `design.md:1424-1431`
- Observed absent: `client/league_replayer.html` (disclosed, item 1), `tools/expand_replay.nim`
  and `tools/extract_events.nim` (disclosed, item 2), and — **not disclosed** —
  `tools/record_fixture.sh`, `flake.nix`, `flake.lock`, `src/waterworld/labels.nim`,
  `data/darkbg.png`, `data/ascii.png`, `data/atlas/*`.
- Nothing in the tree references any of them (`grep -rn "league_replayer\|record_fixture\|flake\|labels"`
  over `.nim/.md/.yml/.sh/.json`, excluding `docs/plans/`, returns no hits), and the HUD label
  composition `labels.nim` was to carry lives in `global.nim` instead. So these are deletions,
  not dangling references.
- Checklist item: advisory.

### F15 — the repo's own copy of the design note is verbatim, so it still asserts the things the code deviates from
- Where: `docs/plans/2026-08-26-walker-waterworld-design.md` — byte-identical to
  `/workspace/coworld-builder/runs/2026-08-26-walker-waterworld/design.md` (verified with `diff`)
- Observed: `AGENTS.md` calls it *"the design note this repo implements"*. It still says
  `2.6 … 3.3 m/s` (§Tests 1), still lists `client/league_replayer.html`,
  `tools/expand_replay.nim`, `tools/extract_events.nim`, `flake.nix` as kept, still describes
  the art as pixie bakes, still says the swept test and the end test "return the **same**
  answer", still specifies §Tests 4's poison-repulsion assertion, and still gives
  `BaselineParams` as (3.20 m, 1.20 m, 8) at `design.md:720`. There is no errata section and
  `docs/{RULES,PROTOCOL,ORDERS}.md` (35–38 lines each) carry no deviation register. Each
  deviation *is* documented at its own site in code or test comments (I verified all 14, see
  §Builder disclosures below).
- Checklist item: advisory.

### F16 — the worst-case renderer fixture re-implements the bubble band rather than loading the shipped renderer
- Where: `tools/ci/renderer_fixture.html:109-142`, against `src/waterworld/global.nim:364-393` and `:603-623`
- Observed: the fixture loads the real `chrome_common.js` and `wire_constants.js` (lines 58-59,
  copied from the built bundle by `ci.yml:341-342`) and pins its own strings against the Nim
  caps (`test_viewer.nim:136-193` re-derives the JS literals' rune length from Nim, so a
  `MaxSayRunes` bump reddens it). But `drawBoard()` is a **hand-written** canvas painter that
  reproduces the band geometry by arithmetic (`BAND_TOP/BAND_BOTTOM` at lines 106-107, three
  evenly-spaced slots at line 125), not a call into the shipped renderer.
- Checklist item 15's wording is *"a page that loads the real `client/renderer.js`"*. This repo
  has **no** `client/renderer.js`: the board is composed Nim-side in `global.nim` into pixie-baked
  sprites and blitted by `broadcast_core.js`, which is the starter's architecture (AGENTS.md
  §"The board is Nim-side"). So the checklist's literal file cannot exist here, and the fixture
  is the closest available substitute — but the consequence is that if `global.nim`'s band
  moved, the fixture would not notice.
- The gate itself is real and I have the evidence: run 32954530460, `wasm-viewer` step
  *"Worst-case text render fixture"* →
  `{"loaded":true,"ms":287,…}` and `canvas text: 2850 drawn, 0 never inside the canvas
  (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
- Checklist item: advisory against 15 (the fixture exists, runs, is `--strict-text-bounds`-gated
  and self-checks its caps — item 15's actual requirements are met).

### F17 — the shipped speech-bubble pill is centred on a fixed slot with no clamp to the board
- Where: `src/waterworld/global.nim:603-623` and `:364-393`, `:459-467`
- Observed: `bubbleSprite` sizes the pill as `pillW = ceil(font.layoutBounds(text).x) + 24` at
  `font.size = 26/1.15 ≈ 22.6` px; `addBubbles` places it with
  `cx = BoardW * (slot * 2 + 1) div 6` (slots 0..2 → x = 400, 1200, 2000 on a
  `BoardW = MapWidth * RenderScale = 2400` board), and `place()` (line 459-467) subtracts
  `w div 2` — i.e. the pill is centred with **no clamp** into `[0, BoardW]`.
  A 48-rune `say` of average-width glyphs is ~566 px wide (half-width 283 < 400, fits), but
  `sanitizeSay` admits any printable ASCII, so 48 wide capitals would be ~980 px (half-width
  490 > 400) and the leftmost pill's left edge would land at a negative board x.
- Inferred, not observed running: I could not measure `data/font.ttf`'s advance widths here.
  This is also invisible to the `canvas_text` gate either way — the pill is a blitted sprite,
  not a `fillText` (see F18).
- Checklist item: advisory against 15 (item 15's gated number is `never_inside`, which is 0 in
  the fixture; the shipped path is not measured by it).

### F18 — the main viewer smoke reports `canvas_text.total = 0`, so its text-bounds number is not evidence
- Where: `tools/ci/viewer_smoke.mjs:359-365` (it wraps `window.CanvasRenderingContext2D.prototype.fillText/strokeText`
  **in the page**), against `replay-viewer/static_replay_worker.js` (OffscreenCanvas in a Worker) and
  `src/waterworld/global.nim` (all board text is pixie-baked into sprites and blitted)
- Observed in CI: run 32954530460, `wasm-viewer` step *"Load the bundle in a real browser"* →
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
- Checklist item 15 says exactly this: *"`total: 0` means the check covered nothing (a
  worker/OffscreenCanvas or WebGL renderer) and is not evidence of anything."* The repo ships
  the fixture precisely for this reason and the fixture's 2850 draws are the evidence (F16).
- Checklist item: advisory — recorded so the judge does not read the main smoke's `0` as a pass.

### F19 — "labels hidden under 640 px" is implemented as the starter's `#stage.tiny` at `boardW ≤ 620`
- Where: `client/replay_broadcast.html:2694` (`stage.classList.toggle('tiny', boardW <= 620)`,
  the starter's line, unmodified) and `:2864-2871` (the ww block's `.tiny` rules)
- Observed: there is no `@media (max-width: 640px)` anywhere in the page (`grep "@media"` returns
  only two `prefers-reduced-motion` blocks). The hiding is
  `#stage.tiny #ww-legend, #stage.tiny .ww-thrust, #stage.tiny .plate .ww-sub .ww-nibbles { display: none; }`.
  `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; }` is at `:2752-2757`, exactly as item 11 requires, and
  `test_viewer.nim:128-134` pins both.
- Checklist item: **11** — satisfied in substance (labels do go below 620 px, which is under
  640). Recorded because the mechanism is a class toggle on measured board width, not a media
  query, so a grep for `640px` finds nothing.

### F20 — `broadcast_core.js` differs from the starter in two places; the test pins only one
- Where: `client/broadcast_core.js:49` and `:268`
- Observed (`diff` against the starter): line 49 `window.CTF_WIRE` → `window.WATERWORLD_WIRE`,
  and line 268 a comment path `src/ctf/sim.nim` → `src/waterworld/sim_types.nim`.
  `tests/test_viewer.nim:204-212` asserts the identifier and three surviving functions, not
  byte-equality-modulo-one-token.
- What the note says (`design.md:1563-1564`): *"`broadcast_core.js` differs from the starter's
  copy in **exactly** the `WATERWORLD_WIRE` identifier"*. The second diff is a comment, forced
  by the no-`ctf_` grep at `test_viewer.nim:254-269`.
- Checklist item: advisory (item 14 names `chrome_common.js` and `replay_broadcast.html`, both
  of which are exact — see F-P1/F-P2).

### F21 — the chrome_common pin is sha1, the note says sha256
- Where: `tests/test_viewer.nim:32` — `ChromeCommonSha1 = "D970EBE4EFF1B0154BA604B4E9ADF62D601CB3EB"`
- Observed: matches `sha1sum` of both copies. `design.md:1143` and `:1557` say *"A test pins the
  file's sha256"*. This is the builder's disclosed deviation (10); the disclosure says
  "sha1-pinned byte-identical", which is what the code does.
- Checklist item: advisory.

### F22 — `config_schema` declares `speed`, which the note's schema list omits
- Where: `coworld_manifest_template.json` `game.config_schema.properties.speed`, and
  `src/waterworld/sim_config.nim:119` (`config.speed = node.readInt("speed", …, 1, 16)`)
- Observed: `sim_config.update` reads it, so `test_manifest.nim:96-114`'s "config_schema covers
  every field `sim_config.update` reads" requires it to be declared. The note's enumeration
  (`design.md:1345-1353`) does not list it. The manifest is the consistent one.
- Checklist item: advisory (item 10 is about `docs`/`protocols` and is satisfied).

### F23 — the `.tiny` sensor-ray rule is not implemented as described; rays are dimmed per-kind, server-side
- Where: `src/waterworld/global.nim:280-283` (`rayAlpha`: `rkClear → 0.30`, else `0.95`),
  `:538-566` (`addRays`: 3 pips for a clear ray, 5 + a hit disc otherwise), and
  `client/replay_broadcast.html:2868-2870` (only `#ww-legend`, `.ww-thrust`, `.ww-nibbles` go under `.tiny`)
- Observed: all sixteen rays are drawn at every board size; a *clear* ray is drawn dim (α 0.30)
  and short at all sizes. There is no `.tiny`-conditional ray drawing, and structurally there
  cannot be — the board packet is built server-side and does not know the client's stage width.
- What the note says (`design.md:1228-1229`): *"Under `.tiny` (≤ 620 px board) only the hit rays
  are drawn, at half opacity."* This is the builder's disclosed deviation (9) ("sensor-ray
  `.tiny` dimming handled DOM-side"); what is actually DOM-side is the **legend**, not the ray
  dimming. The disclosure understates the change.
- Checklist item: advisory.

---

## Traced and consistent

**Provenance (checklist 14)**

- **F-P1 — `client/replay_broadcast.html` regenerates byte-identically from the starter.** I
  copied the repo to `/tmp/wwfork`, ran `python3 scripts/fork_broadcast_page.py
  /workspace/starters/coworld-ctf`, and `diff`'d the output against the committed file: **no
  differences**. The script (`scripts/fork_broadcast_page.py:325-357`) asserts 26 line-boundary
  anchors against the starter before touching anything, applies 11 named line-range cuts
  (1658 lines, of which 1119 are `renderPov` + the FPV picture-in-picture), 7 named range
  replacements (the scorebug plate contents, the endcard columns and verdict), 40 exact-count
  string edits, and appends `scripts/waterworld_block.html`. Lines 420-427 then re-assert that
  no removed id, CSS rule, wiring call, `PB_MODE`/`PaintballChrome`/`CtfStaticReplay`
  identifier survived. This is the strongest provenance evidence available: the page is
  literally a function of the starter's page. 3078 lines vs the starter's 4660, and the
  1582-line delta is accounted for by the cut list.
- **F-P2 — `client/chrome_common.js` is byte-identical.** `sha256 =
  7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` on both copies; `diff -q`
  reports no difference. `test_viewer.nim:34-37` pins the sha1.
- **F-P3 — the banner and the appended-block structure.** `client/replay_broadcast.html:2726-2748`
  is `<!-- ==== / WALKER-WATERWORLD additions to the inherited coworld-ctf chrome / ==== -->`
  followed by one `<style>` and one `<script>`. Everything above it is the starter's, per F-P1.
- **F-P4 — removals.** `test_viewer.nim:74-87` asserts all 19 removed ids, 5 CSS rules and 5
  wiring calls are absent; I re-grepped `#viewpanel`, `#fpv`, `#povBadge`, `$('minimap')`,
  `core.attachMinimap(` directly — none present. `broadcast_core.js` keeps `zoomAt`/`attachMinimap`
  verbatim, undriven, as the note says.
- **F-P5 — transport rules.** `relayout()` at `:2658-2703` sets `--hudscale`, `--topband` and
  `--band` on `document.documentElement` by fixed-point iteration (4 passes) — the starter's
  code, unmodified. `#endcard { top: var(--topband, 0px); bottom: var(--band, 0px) }` at
  `:730-741`, shown with `#endcard.on` at `:752`, taken down on every non-gameover frame at
  `:1661` (`$('endcard').classList.remove('on')`) — the starter's behaviour. The ww block's
  overlays sit inside `#chrome`; `#ww-legend` at `:2801-2822`.
- **F-P6 — beat markers.** `wwMarkBeat` at `:2895-2915` builds
  `document.createElement('button')`, sets `type`, `className = 'beat-marker ' + kind`,
  `title`, `aria-label`, and a click handler that does `CTX.send('s:' + tick)` (a seek). CSS
  exists for every kind `broadcast.nim:23` emits (`ScrubberBeatKinds = ["capture", "poison",
  "target_met", "gameover"]`): `.beat-marker.capture` `:2848`, `.poison` `:2849`,
  `.target_met` `:2850`, `.gameover, .over` `:2855`, base `.beat-marker` `:2834`. Both the
  live-event path (`:2945-2984`) and the replay-beats path (`:3054-3063`) route through it.
- **F-P7 — the four viewer files all come from coworld-ctf.** `replay-viewer/config.nims` diffs
  against the starter's in exactly 4 hunks, all renames (`ctf_replay.js` →
  `waterworld_replay.js`, `_ctf_*` → `_waterworld_*`, two comments). `static_replay.js` diffs in
  exactly 2 lines (worker name, `window.WaterworldStaticReplay`). `static_replay_worker.js`
  diffs in exactly 14 lines, all `_ctf_*` → `_waterworld_*` plus the `importScripts` target.
- **F-P8 — the matched pair (checklist 13, third bullet).** `config.nims:42-54` contains **no**
  `MODULARIZE` and **no** `EXPORT_NAME`; `static_replay_worker.js` uses `var Module = {};` +
  `Module.onRuntimeInitialized = function` + `importScripts('./wire_constants.js',
  './broadcast_core.js', './waterworld_replay.js')`. Both halves come from coworld-ctf and they
  agree. `test_viewer.nim:228-252` and `test_determinism.nim:140-142` both pin it.
- **F-P9 — `data/art/rim_h.jpg` / `rim_v.jpg` are byte-identical to the starter's
  `client/art/walls/wall_h.jpg` / `wall_v.jpg`** (sha256 `0a96ef46…` and `77fa2eb3…` on both
  sides). The move is documented at `global.nim:206-209` with the `--preload-file data@data`
  reason — builder disclosure (3), confirmed.

**Checklist item 1 — CI green.** `gh run list -R Metta-AI/cogame-walker-waterworld --branch main
-w ci.yml`: run **32954530460**, conclusion **success**, head `41bae66`, 2026-08-26T09:43:38Z.
Jobs: `test` 32 s, `docker-smoke` 1m33s, `wasm-viewer` 2m40s (`needs: docker-smoke`, ci.yml:217).
From the `test` job log: `NIM_TESTS` empty (so `ls tests/*.nim`), `NIM_TESTS_RELEASE_ONLY:
tests/test_perf.nim tests/test_baselines.nim`. Every file printed `<name>: ok`, twice for the
13 dual-mode files and once each for `test_perf` and `test_baselines` — 15 test files plus
`helpers.nim` and `config.nims`. No `FAILED`, no skip. (The 32 s is a warm `~/.cache/nim` from
`actions/cache@v4`, keyed on `nimby.lock`.) The "no test loosened" half is F1–F4 above.

**Checklist item 2 — replay re-derivation.**
`tests/test_replay.nim:107-132` records a real 720-tick four-seat episode through the same
sensor→intent→controller→byte→step path the server uses, writes a `COWLDWWD` replay, then
builds a **fresh** sim from `data.configJson` alone, sets `player.mismatchQuit = true`, and
steps it from the recorded bytes only — asserting `raised.len == 0` (i.e. every recorded hash
matched, frame by frame, via `replays.nim:255-284`), `checked > 100`, and
`replaySim.scoreMicro == tank.scoreMicro`. `test_determinism.nim:19-34` does the same for a full
1728-tick run twice. The viewer runs the **same module**:
`replay-viewer/waterworld_replay.nim:1-4` imports `waterworld/[broadcast, global, replay_runtime,
replays, sim]`, and `waterworld_frame` calls `stepReplay` → `sim.step` → `checkReplayHash`. Not
a parallel recording: the only thing recorded per tick is the command byte
(`server.nim:662-664`) and the hash (`:684`).

**Checklist item 3 — static viewer.** `coworld_manifest_template.json`
`game.replay_viewer = {"bundle": "static-replay-viewer"}` (nested under `game`, no top-level
`replay_viewer`, no top-level `version` — `test_manifest.nim:71-74`). `tools/build_replay_viewer.sh`
is mode `100755` (`git ls-files -s`), refuses any output path not named `static-replay-viewer`
(line 12), and is asserted present+executable in `ci.yml:230-241`. The bundle contacts nothing
but the replay URL it is given. No `/client/replay` pod path: the only occurrences are the
server's own inherited HTML route and a comment in `coworld-release.yml:207` that *rejects* it.

**Checklist item 4 — both name spaces.** `sim_types.nim:318-322` `skimmerAlias = "SKIM-" & $(i+1)`
is the only in-game name; `PlayerInfo.address` (`:173-180`) is the real name and is documented as
spectator-side. `decide.nim:99-225` `seatViewJson` composes the LLM message from
`skimmerAlias` only. `test_server.nim:81-123` sets `seatNames[seat] = "SECRET-POLICY-<n>"` and
asserts none of the four reaches any seat's composed message while all four appear in
`buildStateJson().roster[].name` and `results.names`; `test_locality.nim:70-74` repeats it over
200 randomised states, also checking no other seat's prompt leaks. `broadcast.nim:300-307`
carries the real names into the chrome; `roster.nim:100-120` into `results.names` with
`results.aliases` carrying `SKIM-n`.

**Checklist item 5 — degrade-never-hang.** Every wait I could find and its bound:
| wait | where | bound |
|---|---|---|
| attempt-1 batch | `decide.nim:359-376` | `attempt1Ms` 9000 → `CURLOPT_TIMEOUT` 9 s |
| retry batch | same | `retryMs` 5000 → 5 s |
| per-turn wrapper | `decide.nim:289, 354` | `turnBudgetMs` 16 000 ms, monotonic |
| inter-batch floor | `decide.nim:341-344` | `min(spacing, spacing − since)` ≤ 12 000 ms |
| lobby join | `sim.nim:130-132`, `server.nim:548-562` | `lobbyJoinTimeoutTicks` 1728 = 72 s, then plays on with the no-show reported |
| frame limiter | `server.nim:368-384` | `frameDuration` = 1/24 s, `sleep(max(1, min(2, …)))` |
| engine hard stop | `server.nim:494-501` | `wallClockBudgetSeconds` 660 s → `deadline/wall_clock` |
| shutdown grace | `server.nim:788-791` | `ShutdownGraceSeconds = 20` |
| spawn rejection sampler | `tank.nim:170-177` | `SpawnAttempts = 64`, then a bounded lattice scan |
| lattice scan | `tank.nim:149-164` | two bounded `while` loops over a 0.50 m grid |
| replay seek | `replays.nim:428-443` | `SeekTicksPerFrame = 240` per frame |
| replay precompute | `replays.nim:343-389` | `maxTicks` slice per call |
No unbounded loop and no blocking read. Budget arithmetic: `test_engine.nim:141-147` computes
`(24−1)·12 + 16 + 72 + 2 + 20 + 30 = 416` s < 660 s stop < 720 s (60 % of 1200), and
`test_manifest.nim:236-246` re-checks it per variant. Budget guard at `decide.nim:301-309` is
`elapsed + 2·⌈(turnBudgetMs + turnSpacingMs)/1000⌉ > wallClockBudgetSeconds`, exactly the note's
formula, and `test_engine.nim:84-106` asserts it fires and that the episode still ends
`complete/*`.

**Checklist item 6 — `num_agents`.** `num_agents: 4` in `variants[default].game_config`,
`variants[sprint].game_config`, and `certification.game_config`; `len(certification.players) = 4`;
`len(certification.game_config.players) = 4`; `slots` 4 in all three.
`tools/ci/docker_smoke.sh:106-149` enforces the four invariants and prints
`SEAT-COUNT FAIL:` on each; `seats_expected="${SMOKE_SEATS:-4}"` at line 54 is the independent
second declaration. **`grep -c "SEAT-COUNT FAIL" ` over the full docker-smoke job log of run
32954530460 → 0.** The job log's own line: `game=walker-waterworld seats=4 config={"num_agents": 4, …}`,
then `all 4 player containers exited 0`, `episode end reason: complete`,
`smoke OK: seats=4 results=571B replay=31037B reason=complete`. `test_manifest.nim:216-267`
pins all of it from Nim.

**Checklist item 7 — scripted baseline plays full episodes legally.**
`tests/test_engine.nim:103-105` runs `sim.runScripted(blShoal)` to the natural end and asserts
`sim.endReason == ReasonComplete`. `tests/test_scoring.nim:139-165` runs another full episode
and asserts the 22-key results document, four bit-identical scores and the closed
`reason`/`endRule` enums. `tests/test_baselines.nim:19-86` is the legality assertion: 500
randomised states × both baselines, every field checked against the reply schema — including
*"target is either none or a CURRENTLY DETECTED plankton"* (`frame.foodDetection(...) >= 0`) and
*"partner is another skimmer, never its own alias"* — plus the compiled byte decoding into
`dir ∈ 0..31, level ∈ 0..7`. Tuned by grid harness, not guessed: `tools/tune_baselines.nim`
(104 lines) sweeps a 4×4×4 matrix, `tools/ci/baseline_tuning.json` records the pick and the
grid, `tests/test_tuning.nim:24-36` asserts the shipped defaults equal the pick **and** that the
pick is a cell the grid actually covered, and `test_baselines.nim:143-201` asserts against both
the recorded measurement and the design note's own floor (18/20 at 8+ captures, mean > +70,
16/20 for the mix) so a re-recorded downward drift still trips. CI panel from run 32954530460:
`shoal: 20/20 seeds at 8+ captures, mean score 175.63`; `drifter: 19/20, mean 110.73`;
`mix 2+2: 20/20 at 4+, mean 137.22`.

**Checklist item 8 — LLM reply handling.** Tolerant parse: `intents.nim:111-150`
`extractJsonObject` walks braces with string/escape awareness and falls back to
first-`{`..last-`}`; `parseIntent` (`:215-328`) repairs every field per the note's table —
percentage `throttle` above 1 (line 320), centimetres for `standoff_m` and `waypoint` above 30
(lines 288, 309), `{"x":…,"y":…}` waypoints (line 280), case-insensitive `mode`/`target`/`partner`
(lines 105, 178, 198), `"plankton F2"` and `"2"` (line 181-186), and raises only when
`usable == 0`. Retry exactly once: `while open.len > 0 and attempt < 2` (`decide.nim:351`).
Fallback recorded: `fallbackRecord(turn, seat, attempt, cause, detail)` at lines 356, 402, 428,
written into the replay chat stream at `server.nim:639-640`, counted per seat in
`roster.nim:66-70` and emitted as `results.fallbackTurns`. The log phrase phase 60 greps for is
present twice (`decide.nim:328, 431` "falling back", `llm.nim:131` "the LLM provider is
unavailable"). Test gap noted at F7.

**Checklist item 9 — rune-safe truncation.** `intents.nim:61-68` `truncateRunes` is the single
shortening path (`runeLen` / `runeSubStr`). Every recorded string routes through it:
`say` → `sanitizeSay` (cut *then* ASCII-filter, line 80 — the order matters and the comment says
why); `note` → `sanitizeNote` (line 89); `register.policy` ≤ 48 (line 390);
`fallback.detail` ≤ 200 (line 404); the whole `intent` record ≤ 600 via `boundedIntentRecord`
(lines 362-378, which shrinks `note`/`say` rather than cutting the serialized JSON);
`register.prompt` ≤ 4000 at `server.nim:581`; provider error bodies at `llm.nim:176, 184, 190,
199`. `tests/test_intents.nim:126-153` is the required test: 47 `'a'` + two 4-byte fish = 49
runes, truncated to 48, `validateUtf8() == -1`, round-trips `%$` → `parseJson`, and
`sanitizeSay` on the same input still validates. `test_replay.nim:26, 54-55, 207-208` forces a
non-ASCII policy label and note through the real replay and asserts
`tools/replay_summary.py`'s output decodes strictly.

**Checklist item 10 — manifest validates.** `game.docs.readme = {"type":"text","value":…}`
(1448 chars) and `game.docs.pages` = three `{id,title,content:{type,value}}` entries
(`rules.md`/2778, `protocol.md`/822, `orders.md`/2628). `game.protocols` carries **both**
`player` and `global`, each a `{"type":"text","value":…}` object.
`test_manifest.nim:160-189` pins all of it.

**Checklist item 12 — release order and scaffold.** `coworld-release.yml` step order:
"Build the Coworld manifest" (153) → "Certify locally" (167, with `--timeout-seconds 300`) →
"Upload the policies" (212) → "Upload the Coworld" (310) → "Put the Coworld secret" (348). All
three workflows present. `tools/ci/docker_smoke.sh` mode `100755`. `tools/ci/policies.json`
holds exactly four entries, all `"run": "/bin/walker-waterworld-player"`: two `PLAYER_PROMPT`
champions (`walker-waterworld-tandemhunt`, `walker-waterworld-relay`) with champion #2 carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, and two `PLAYER_SCRIPTED` fillers
(`shoal`, `drifter`). Both champion prompts are the design note's verbatim, whitespace-joined.
I ran the gate:
`grep -n '<slug>\|<IMAGE>\|<SEATS>' ci.yml coworld-release.yml coworld-submit.yml docker_smoke.sh policies.json`
→ **no matches, exit 0**. Submit workflow inputs: `player_id`, `policy` (`<name>:vN` — the
documented expected residue), `league_id`; artifacts `submit-result` / `release-result` +
`release-logs`.

**Checklist item 13 — viewer executes.** Run 32954530460, `wasm-viewer` (`needs: docker-smoke`),
step *"Load the bundle in a real browser"* ran and printed:
`{"loaded":true,"ms":593,"clock":"0:18 TIME LEFT","scorebug":"THE POD 23.098 4 SKIMMERS 3 NIBBLES 0:18 TIME LEFT CAUGHT 3 / 20 POISON 3 THRUST −1.05","feed_lines":0}` —
i.e. it loaded the `docker-smoke` replay (31 037 B, artifact sha256 `743fcf29…`, the same digest
downloaded by `wasm-viewer`) in headless chromium (Playwright 1.55.0, Chromium 140.0.7339.16),
rendered a real scorebug from real state, and survived the 12 s soak with `--strict-text-bounds`.
Not `continue-on-error`, not commented out. Both markers are set from the shell's own code:
`static_replay.js:161` sets `data-replay-loaded="true"` from the Worker's `'loaded'` message
(the first drawn frame), `:20` sets `data-replay-error` in `showFailure()`, `:32` sets
`data-replay-mismatch-tick`; `test_viewer.nim:214-226` pins all three plus
`"message.type === 'loaded'"` so the marker cannot drift onto rAF timing.

**Sim / resolution order (design §Resolution order, `design.md:271-354`).** Traced step by
step against `src/waterworld/sim.nim:294-504`:
1. Turn boundary — `server.nim:629-649`, `gameTicksElapsed() mod turnTicks == 0 and turnIndex != lastTurnIndex`; one `intent` chat record per seat; `activeIntent` never hashed. ✓
2. Controller compile — `server.nim:650-665`, `for i in 0 ..< SkimmerCount` (skimmer index order), `cmd = ctl.thrustCommand(...)`, `writeInputMaskChange(tickTime, i, cmds[i])` (change-only guard at `replays.nim:112-117`). ✓
3. Skimmer dynamics — `sim.nim:150-210`: stun→level 0 & decrement; thrust `v += DirQ12·MaxThrustAccel·level / (7·4096)` in int64; drag `v -= v·39 div 1024`; speed clamp via `isqrt`; move; walls x-then-y with `−(v·2) div 5`; rock push-out to exactly `R` and `v -= 7·vn·n̂ / (5·4096)`. All seven sub-steps in the note's order. ✓
4. Particle motion — `sim.nim:359-379`, food id order then poison id order, index reflections, respawn timer. ✓
5. Sensor frames — derived, not hashed; built in `server.nim:632-634` and `sensors.nim:65-158`. ✓
6. Contacts — poison first (`:381-411`, skimmer order then poison id order, consume + `poisonHits` + `scoreMicro` + `stun` + halve `v`, and a skimmer touching two blooms pays both), then capture/nibble (`:413-476`, plankton id order, `holders.len >= coopNeeded`, stunned skimmers counted, assists per participant, nibble re-arm at `NibbleRearmUm` and forced true on respawn at `:368-369`). All swept (`tank.nim:81-121`). ✓
7. Thrust cost — `:478-485`, only the level actually applied; a stunned skimmer pays nothing (`appliedLevel[i] = 0` at `:355-356`). ✓
8. Score — `:487-492`, `10e6·captures + 5e4·nibbles − 2e6·poisonHits − thrustMicro`, exactly the note's formula. ✓
9. Hash — `server.nim:684`, `writeHash(uint32(tick), sim.gameHash())` every tick. `sim_state.nim:64-118` mixes everything the note lists plus `gameStartTick`, `startWaitTimer`, `gameOverTimer`, `nibbleArmed`, the four per-seat counter arrays and `latticeFallbacks` (a superset), and never mixes `cmd`, sensor frames, FX, bubbles, feed text or names. ✓
10. End checks — `sim.nim:496-504` target_met → full_time → guard; wall-clock lives at `server.nim:494-501` ahead of the tick, and `fault/{sim_fault,host_error}` at `:671-683`. ✓

**Determinism boundary.** `src/waterworld/{sim,tank,trig,sensors,sim_types,sim_config,sim_state}.nim`
carry no float — grep-enforced by `test_determinism.nim:105-142`, which strips comments and
`isqrt(` before searching for 13 banned tokens plus `rand(`, and also greps
`build_replay_viewer.sh`, both Dockerfiles and `config.nims` for `-ffast-math`. Every stored
field is `int32`/`int64`/`uint8`/`bool`/`enum` (`sim_types.nim:157-300`). Every draw goes through
`tank.nim:18-24` `drawInt` on `rng.next()`'s uint64 domain, with `rngDraws` incremented and
hashed. `DirQ12` re-derived entry-by-entry from `math.cos`/`math.sin`
(`test_determinism.nim:145-154`), `isqrt` exhaustive below 2¹⁶ and on perfect squares to 2⁴⁰
(`:155-166`). Golden fixture `tests/data/golden_hashes.json`: 36 samples (every 48th tick of
1728), `gameVersion: "1"`, seed 8 821 477.

**Replay writer / codec.** `WaterworldReplayMagic = "COWLDWWD"`, `formatVersion 1`,
`gameName "walker-waterworld"`, `gameVersion "1"`, `hashOrder: rhoStop` (`replays.nim:88-99`);
`GameVersion`'s comment at `sim_types.nim:21-29` carries the prepend-only changelog discipline
and `tools/ci/check_gameversion.sh` is kept. Config completeness (`sim_config.nim:184-259` +
`roster.nim:148-170`): `seed`, `perm`, `num_agents`, `maxTicks`, `turnTicks`, the whole geometry
table (tank box, board scale, rock, three radii, sensor count, four spawn points), every physics
constant (thrust, levels, drag num/den, speed clamp, restitution, both speed sets, nibble re-arm),
the reward constants, `captureTarget`, the **seeded initial particle table**
(`initialFood` 5 rows + `initialPoison` 8 rows of `{id,x,y,dir,speed}`), `players[].name` — the
**real** names, spectator side — and `slots[].alias`. `test_replay.nim:93-105` pins seed, perm
length, the geometry, both initial tables and the four real names.

**Manifest details beyond items 6/10/12.** Top-level `$schema`, `episode_timeout_minutes: 20`,
5 top-level `tags`; `game.description` present, **`game.tags` absent**, no `game.display_name`,
no top-level `version`. `game.runnable.env.ANTHROPIC_API_KEY_URI =
secret://coworld/walker-waterworld/anthropic_api_key`, and the namespace equals `game.name`
exactly (`test_manifest.nim:44-52`). `config_schema` is `additionalProperties: false`, required
`["tokens","players"]`, every array property carries `minItems`/`maxItems` (`tokens` 1..4,
`players` 1..4, `slots` 0..4). `results_schema` has exactly the 22 keys, `additionalProperties:
false`, required 7, `reason`/`endRule` closed enums of 3 and 5, every per-seat array
`minItems: 4, maxItems: 4` — and `test_manifest.nim:120-157` cross-checks the schema keys against
the keys `playerResultsJson()` actually emits, in both directions. One bundled player entry
occupying all four cert slots, `resources.limits.cpu == "1"`.

**Tests — what each of the 15 actually asserts.** (Deltas from the note's §Tests are in
F1–F4, F7, F9 and below.)
- `test_physics.nim` (281) — thrust ramp + terminal + clamp; drag 3.5–4.2 %/tick and <1 % in 120 ticks; wall rebound 35–45 % and containment over 400 random-drive ticks; rock push-out to exactly `R` (±2 µm); particle speed **bit-exactly** constant over 5000 ticks with ≥40 bounces, never inside the rock or outside the tank; the three index reflections vs a float reference (rock reflection checked as an involution, not against a float bearing — a slightly weaker form than the note's wording); the no-tunnelling bound asserted directly for both particle kinds; the swept test as a **superset** of the end test over 50 000 pairs with `endOnly == 0` (disclosure 5, present since the first commit, not a later change).
- `test_determinism.nim` (211) — (a)–(g) all present as the note specifies.
- `test_tank.nim` (211) — spawn predicate over 20 000+ accepted draws across 200 seeds with **zero** lattice fallbacks; detection exactly `≤ 2 400 000 µm` over 50 000 pairs; 16 sectors tiling, index vs float reference within one; wall and rock casts vs a float ray-cast within 2 mm (with F4's near-tangent exclusion); `closing` sign both ways; partners always 3, a far partner flagged `in_sensors: false` and occupying no ray.
- `test_control.nim` (317) — 3000 random (state, intent) pairs: byte range, decode range, implied accel ≤ `MaxThrustAccel + 1`, purity; all five modes' goal points; `hold` brake; stun and non-`Playing` force `cmd = 0`; poison repulsion (F2); rock tangent over 10 000 goals (F1).
- `test_baselines.nim` (219, release-only) — see item 7 above.
- `test_intents.nim` (190) — every tolerance in the note's list plus the emoji rune-boundary case, the three record caps, and the two raise conditions. Missing: the three retry/throttle assertions (F7).
- `test_engine.nim` (209) — batch shape (F7), instant credential-less fallback with cause `no_credentials` and `source == isFallback`, scripted seats write no fallback record, budget guard + `complete/*`, a measured bounded floor, the deadline arithmetic, `deadline/wall_clock` and `fault/sim_fault` endings, a never-connecting seat, a dropped seat keeping its skimmer. Missing: hung-client budget enforcement, reconnect revival, the `COGAME_PLAYER_FAILURE_URI` call itself, held registration (F9).
- `test_locality.nim` (104) — 200 randomised states × 4 seats: particle appears **iff** within 2.40 m (both kinds, all 13 particles), exactly 3 partners, exactly 16 sensors, no real name, no other seat's prompt, and a 9-token banned-substring sweep (`perm`, `"seed"`, `rngDraws`, `initialFood`, `initialPoison`, `latticeFallbacks`, `policyKind`, `fallback`, `variant`) plus the structural check on `control.nim`/`sensors.nim`.
- `test_scoring.nim` (193) — all six worked examples to 3 decimals; the sim matching the formula; one skimmer = nibble not capture; 480 ticks parked = **one** nibble; 2 and 3 holders both = one capture with `holders` assists; poison = exactly −2.000 + 12 stun + consumed; 6.912 full-throttle bill; the 22-key shape with four bit-identical scores; target ends the episode `complete/target_met`.
- `test_replay.nim` (213) — the end-to-end episode, `parseReplayBytes`, the config JSON, the frame-by-frame re-simulation, the shared `initReplayRuntime` scan + keyframe seek, the record census (4 registers, 4 intents/turn, exactly 1 result, every intent ≤ 600 runes), and `replay_summary.py` under a strict UTF-8 parse with a forced non-ASCII label and note.
- `test_server.nim` (196) — registration shapes (F8), token admission and slot-sequential joins, the two name spaces, the 19-key chrome frame shape with exactly one `teams` key, the wire-constant fallbacks vs the engine, `/client/` routes serving a real page that never opens `/player?`, and `file://` artifact writes.
- `test_manifest.nim` (327) — see items 6/10/12 above, plus the compose-service→placeholder derivation, the secret namespace, `maxTicks mod turnTicks == 0`, `attempt1Ms + retryMs ≤ turnBudgetMs`, per-variant worst-case arithmetic, and the `config_schema`-covers-`update` cross-check.
- `test_viewer.nim` (273) — see F-P2/F-P4/F-P6/F-P8, plus the 42-id keep list, the 40-name alias-collision sweep over the appended block, the `.plate-name` rule, the fixture's own cap pin (added in `41bae66`), the board-aspect/render-scale/capacity-preflight triple, and the `ctf_`/`CTF_`/`paintball`/`PB_MODE` sweep over `client/`, `replay-viewer/` and `src/` with `chrome_common.js` exempted (disclosure 10).
- `test_startup.nim` (89) — clean single-line errors with no traceback on a bad config, seed pinning/sentinel/strip, seed-before-`update` ordering, and the Dockerfile's two entrypoints.
- `test_perf.nim` (22, release-only) — the 60 s bound.

**Builder disclosures — all 14 verified.**
| # | claim | verdict |
|---|---|---|
| 1 | `client/league_replayer.html` not forked | Confirmed absent; nothing references it. Undocumented in-repo (F14/F15). |
| 2 | `expand_replay.nim`/`extract_events.nim` → `replay_summary.py` | Confirmed. `tools/replay_summary.py` (249 lines, stdlib-only) documents the substitution in its docstring and is exercised by `test_replay.nim:176-208`. |
| 3 | wall art → `data/art/rim_{h,v}.jpg` for emscripten preload | Confirmed byte-identical (F-P9); reason documented at `global.nim:206-209`, `config.nims:46`, AGENTS.md. |
| 4 | decimillimetres, not µm, in ray/contact maths | Confirmed: `tank.nim:73-79` and `:212-213` document it; the divisor is `100` (100 µm = 0.1 mm) at `:102-108, 225-228, 246-249`; the end-position test stays exact at µm (`:88`); pinned to a float reference within 2 mm at `test_tank.nim:128, 152`. |
| 5 | swept test asserts superset, not equality | Confirmed (`test_physics.nim:244-277`). Present since the first commit; the added guard "a swept-only contact was genuinely close" keeps it from being vacuous. |
| 6 | the note's 2.6–3.3 m/s is impossible; 1.8–2.1 + 3.24 terminal instead | Confirmed by arithmetic (above). The replacement band is narrower and adds an assertion. |
| 7 | radial repulsion cannot sidestep a bloom dead ahead | Confirmed against `control.nim:172-187`. Documented at `test_control.nim:191-195`. The consequence is F2. |
| 8 | rock keep-out steers outward, not tangentially | Confirmed at `control.nim:196-217`: **both** branches exist — `if fromRock < keepOut` steers radially outward (the anti-orbit-trap, documented at lines 198-200), `elif` the segment clips, the tangent rule of the note applies. It is an addition, not a replacement. |
| 9 | sensor-ray `.tiny` dimming handled DOM-side | Partly. The **legend** is DOM-side (`:2868`); the ray dimming is server-side and unconditional (F23). |
| 10 | chrome_common exempt from the CTF grep, sha-pinned | Confirmed (`test_viewer.nim:254-269` exempts it by filename; `:32-37` pins it). sha1 not sha256 (F21). |
| 11 | `test_server.nim` has no real websocket | Confirmed; also re-declares the parser (F8). |
| 12 | action log indexed by skimmer index, not seat | Confirmed in code; one stale comment disagrees (F12). |
| 13 | golden fixture is a joint sim+controller+shoal pin, re-mintable | Confirmed: `test_determinism.nim:55-101`, `WATERWORLD_WRITE_GOLDEN=1`, documented in AGENTS.md. The `runScripted` log it replays is the `shoal` baseline's, so all three are pinned together. |
| 14 | shipped `BaselineParams` are the sweep winner, not the note's guess | Confirmed: `baselines.nim:40-56` ships (2 400 000 µm, 1800 mm, 12) against the note's (3 200 000, 1200, 8) at `design.md:720`, with the sweep's numbers (180.9 vs 154.6) in the comment; `tools/ci/baseline_tuning.json` + `test_tuning.nim` pin it and check the pick was a covered cell. |

---

## Could not determine

- **Whether F1's bound could be tightened to the value its own comment justifies.** The block
  sets velocity to zero, so the accel direction is the steer direction and the quantisation
  error is ≤ 5.625° (`|cos| ≤ 0.098`); I can see no other source of error in `control.nim`'s
  path for this block. But whether `dot < 0.098·|toRock|·Q12` actually passes over the 10 000
  sampled goal points cannot be settled from the tree — the sandbox has no Nim. What would
  settle it: run `nim r -d:release --path:src tests/test_control.nim` with the bound at 0.10
  and read the failure count (and, if it fails, the reported `dot vs bound` pairs, which would
  identify the real error source).
- **Whether F17's worst-case `say` actually overhangs the board.** The pill width is
  `pixie`'s `font.layoutBounds(text).x` in `data/font.ttf` at 22.6 px; I cannot measure that
  font here. What would settle it: render `bubbleSprite("W"×48, …)` and compare
  `image.width div 2` against 400 board pixels — or, cheaply, add a clamp of `cx` into
  `[w div 2, BoardW − w div 2]` and stop needing to know.
- **Whether `docker_smoke.sh`'s `dist/smoke/replay.json` naming is deliberate.** The file is
  the binary `COWLDWWD` replay written to a `.json` path (`docker_smoke.sh:58, 208, 339`), which
  is why `ci.yml:305`'s glob loop (`dist/smoke/*.replay dist/smoke/replay.json`) resolves and
  why the fixture step's `--replay dist/smoke/replay.json` finds a file. It works and CI is
  green; I could not determine whether the template intends the extension to track the format.
- **`llmTurns` / `fallbackTurns` accuracy on a live LLM episode.** They are incremented in
  `roster.nim:66-70` from the `intent` record's `source` field, which is fed by
  `sim.pushFeedIntent(record)` at `server.nim:647` and again during replay chat re-application
  at `replays.nim:251-252`. Nothing in CI produces an LLM episode (no key), so the counters are
  only ever exercised with `source == "scripted"`. What would settle it: a phase-60 hosted
  episode, or a unit test that pushes synthetic `llm`/`fallback` intent records and reads
  `playerResultsJson()`.

---

## Summary

**24 findings: F1–F4 blocking (all against checklist item 1's "no test loosened" half, all in
commit `b3686ba`), F5–F23 non-blocking/advisory** (F19 and F16 are recorded against checklist
items 11 and 15 respectively but do **not** falsify them).

Checklist items 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 and 15 are all satisfied, with cited
evidence from the tree and from CI run 32954530460. Item 1's first half (CI green on `main` at
the reviewed sha) is satisfied; its second half is F1–F4.
