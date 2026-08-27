# r1 review — rware-warehouse

Repo: `/workspace/cogame-rware-warehouse` @ `d303e6c004dea8a7fcf2cc4e2da1fcea4d71a565` (main)
Starter (read-only): `/workspace/starters/coworld-ctf`
Design note: `/workspace/coworld-builder/runs/2026-08-27-rware-warehouse/design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files opened: 58 (all of `src/rware/`, `replay-viewer/`, `client/`, `tests/`, `tools/ci/`, `vendor/`, `docs/`, the manifest, the three workflows, and the starter counterparts diffed below).

This is a neutral trace. Findings are numbered F1…F23; each says what the code does and what the
note says it should do. Categorisation against the checklist is left to the judge. Nothing here is
a proposed fix.

Two brief-level corrections up front, because they affect how the rest reads:

- **`vendor/PATCHES.md` has 11 entries, and they are not the 11 the brief lists.** The file
  (`vendor/PATCHES.md:10-60`) carries the note's 7 upstream divergences plus exactly four
  implementation-forced ones: #8 contention-penalty sign, #9 courteous release valve, #10 `yield`
  planning with robots as obstacles, #11 two integer RNG streams. **JS-baked art, `fetch` steering
  to the current cell, `game.docs` type `text`, speed chips `[1,2,4,8]`, the dropped `kill`
  forbidden-word, and the dropped `--preload-file` are *not* in `PATCHES.md`** (nor in
  `docs/PORTING-RWARE.md:41-93`, which mirrors it entry-for-entry). Each of those is documented
  only in a code comment, or nowhere. They are F4, F6, F7, F9, F11, F12 below.
- `docs/PORTING-RWARE.md` is byte-parallel to `vendor/PATCHES.md`'s divergence list; I diffed the
  two lists item by item and they agree.

---

## Findings

### F1 — `hold` drives the robot to a park cell instead of standing still
- **Where:** `src/rware/pilot.nim:184-191`
- **Code:**
  ```nim
  if result.outcome != orRunning or order.kind == okHold:
    ## Idle: park on the nearest aisle cell outside the queue lane and hold.
    let park = parkCell(sim, seat)
    if park < 0 or robot.cell == park: return
    let step = stepToward(sim, seat, park)
    result.action = step.action
    return
  ```
  `okHold` is routed into the park branch before the on-goal branch is reached, so
  `pilot.nim:215-216`'s `of okHold: discard` is unreachable. A robot standing on a storage cell or
  in the workstation queue lane and given `hold` will rotate and drive to the nearest non-lane,
  unoccupied highway cell.
- **Note says:** `design.md:612` — `hold` | goal cell "—" | terminal action "`NOOP` every tick" |
  "never finishes". The shipped system prompt says the same thing to the model
  (`src/rware/llm.nim:220`, `{"verb":"hold"}  stand still`), and `docs/RULES.md:102` repeats it
  (`| hold | — | NOOP every tick | never finishes |`).
- **Observable:** champion #2's prompt (`design.md:586`) instructs `"hold" and say "holding, you
  go"` as the *stay-put* half of a jam standoff; under this code the holding robot moves.
- Not in `vendor/PATCHES.md`.

### F2 — the ASCII floor plan is never sent to any seat
- **Where:** `src/rware/warehouse.nim:275-287` (`asciiMap`), `src/rware/decide.nim:139-148`
- **Code:** `asciiMap` has exactly one caller in the tree and it is a test
  (`tests/test_rware_layout.nim:138`). `grep -rn asciiMap src/ tools/` returns only the definition.
  The observation's `warehouse` object is:
  ```nim
  "warehouse": { "width": …, "height": …,
                 "stations": {"W1": …, "W2": …},
                 "storage_slots": wh.shelfCount(), "sensor_range": … }
  ```
  There is no map, no highway mask, no storage-cell list. `userMessage`
  (`src/rware/llm.nim:246-249`) is `operatorBlock(prompt) & viewJson` — nothing else is appended,
  and the registration path (`src/rware/server.nim:444-474`) only *reads* the seat's blob; it sends
  nothing back.
- **Note says:** `design.md:409-412` — "**The floor plan, in full and always** … It is static for
  the whole episode and is sent once, at registration, as an ASCII map (`#` storage slot, `.`
  aisle, `W` workstation), then referred to by coordinates." `docs/PROTOCOL.md:103` repeats the
  claim verbatim, so the shipped protocol doc and the code disagree.
- **Observable:** a driver can see `requests[].home` and up to 8 visible `free_slots`, but has no
  way to know which arbitrary cell is a storage slot or an aisle, which is what the system prompt's
  `'#'`/`'.'`/`'W'` vocabulary (`llm.nim:203-205`) presumes it has.

### F3 — the request refill can immediately re-draw the shelf just delivered; the candidate set differs from upstream
- **Where:** `src/rware/sim.nim:313-321`, `src/rware/robots.nim:142-152`
- **Code:** `sim.nim` clears the flag *before* the draw:
  ```nim
  sim.world.requested[shelfHere] = false
  let replacement = sim.world.refillDraw(sim.config.seed, sim.refillDraws)
  ```
  and `refillDraw` builds its candidate list from that same flag:
  ```nim
  for id in 0 ..< world.shelves.len:
    if not world.requested[id]: candidates.add(id)
  ```
  so the delivered shelf is in the pool and can be drawn back onto the board on the same tick.
- **Upstream says** (`vendor/upstream/warehouse.py:915-917`), candidates are computed *before* the
  queue slot is replaced, so the delivered shelf is excluded:
  ```python
  candidates = [s for s in self.shelfs if s not in self.request_queue]
  new_request = self.np_random.choice(candidates)
  self.request_queue[self.request_queue.index(shelf)] = new_request
  ```
- **Note says:** `design.md:78` and `design.md:216-217` — "that queue entry is refilled with a shelf
  drawn by the **request RNG** uniformly from the shelves **not currently in the queue**". At the
  moment of the draw the delivered shelf *is* still in `world.requestQueue` (it is overwritten at
  `sim.nim:316-321`).
- The candidate-set cardinality therefore differs from upstream by one on every refill, which
  changes the whole request stream, not only the immediate-repeat case.
- `tests/test_rware_sim.nim:275` (`check not sim.world.requested[carried]`) asserts the delivered
  shelf is not re-requested; that assertion holds at the fixture's seed but is not implied by the
  code.

### F4 — `fetch` steers to the shelf's current standing cell, not its home cell
- **Where:** `src/rware/pilot.nim:18-29`; the same substitution in `src/rware/baselines.nim:127`
- **Code:**
  ```nim
  proc shelfGoal*(sim: SimServer, shelf: int): int =
    if sim.world.shelves[shelf].carrier >= 0: return sim.world.shelves[shelf].home
    sim.world.shelves[shelf].cell
  ```
  and `baselines.nim:127` — `let home = sim.world.shelves[id].cell` (named `home`, but it is the
  current cell).
- **Note says:** `design.md:608` — `fetch S` | goal cell `S`'s **home cell**. The observation still
  advertises the *home* cell to the model (`src/rware/decide.nim:93` —
  `"home": [cellX(shelves[id].home), cellY(shelves[id].home)]`), so a driver told
  `{"shelf":"S19","home":[2,6]}` may be driven somewhere else by the pilot once S19 has been
  re-stowed.
- Justified in the proc's own docstring and reflected in `docs/RULES.md:98`; **not** in
  `vendor/PATCHES.md`.

### F5 — the baselines' `fetch` tie-break is by request-queue position, not by lowest shelf id
- **Where:** `src/rware/baselines.nim:122,139`
- **Code:** `for id in sim.world.requestQueue:` … `if result.kind == okHold or cost < best:` — the
  strict `<` keeps the first equal-cost candidate encountered, and the iteration order is the
  queue's draw order (`robots.nim:129`, `sim.nim:316-321`), not ascending shelf id.
- **Note says:** `design.md:638` (`shuttle` rule 3) and `design.md:652` (`courteous` rule 4) both
  pin "ties by lowest shelf id"; test 16's spec (`design.md:1409-1414`) does not re-check it and
  `tests/test_rware_pilot.nim:55-70` checks only that the shelf is on the board.
- The behaviour is still deterministic and re-derivable; it is a different deterministic rule from
  the one the note pins.

### F6 — `--preload-file` and `-s FILESYSTEM=1` are dropped from the emscripten link line
- **Where:** `replay-viewer/config.nims:48-58` (diff against
  `/workspace/starters/coworld-ctf/replay-viewer/config.nims`)
- **Code:** the starter's `--preload-file {rootDir / "data"}@data` and `-s FILESYSTEM=1` are both
  absent from the fork's `passL` string; everything else (`-O2`, `ALLOW_MEMORY_GROWTH`,
  `ABORTING_MALLOC=1`, `ENVIRONMENT=web,worker,node`, `EXPORTED_RUNTIME_METHODS=HEAPU8`, the
  renamed `EXPORTED_FUNCTIONS`) is present.
- **Note says:** `design.md:1001-1004` lists `--preload-file data@data` and `-s FILESYSTEM=1` among
  the flags kept as one internally-consistent set from the single starter; `design.md:1233` lists
  `rware_replay.{js,wasm,data}` in the bundle asset list.
- **Internally consistent:** `Dockerfile.replay-viewer:50-77` never mentions a `.data` file and
  copies every asset next to the worker instead; `client/broadcast_core.js:266-272` fetches them
  over HTTP; `tests/test_rware_viewer.nim:281` now pins the absence (commit `d303e6c` replaced a
  vacuous `… or true` with `check "--preload-file" notin config` — a strengthening, not a
  loosening).
- Not in `vendor/PATCHES.md`.

### F7 — speed chips are `[1, 2, 4, 8]`; the note pins `[0.5, 1, 2, 4, 8]`
- **Where:** `src/rware/sim_types.nim:50` (`PlaybackSpeeds* = [1, 2, 4, 8]`),
  `src/rware/replay_runtime.nim:60-61` and `:234-237` (`'1' → 0 … '8' → 3`),
  `src/rware/wire_constants.nim:19` (`jsIntArray(PlaybackSpeeds)` — an integer array, so 0.5 is not
  representable), `client/broadcast_core.js:61` (`WIRE.speeds || [1, 2, 4, 8]`).
- **Note says:** `design.md:1118` — "speed chips `[0.5, 1, 2, 4, 8]`, default 1".
- Default is 1 (`replay_runtime.nim:191`, `speedIndex = 0`), so the note's playback-length
  arithmetic (500 ticks ⇒ 16.7 s) is unaffected. Not in `vendor/PATCHES.md`.

### F8 — the `.tiny` density threshold is 640 px, not the starter's 620
- **Where:** `client/page_script.js:586` — `stage.classList.toggle('tiny', boardW < 640);`
- **Note says:** `design.md:1180` — "`relayout()` sets `--hudscale = clamp(0.5, boardW/760, 1.6)`
  and toggles `#stage.tiny` at `boardW <= 620`, **both kept verbatim**."
- The `--hudscale` clamp *is* verbatim (`page_script.js:580`). The threshold change is explained in
  the adjacent comment (`page_script.js:582-585`) as aligning with checklist item 11's "labels
  hidden under `640px`". Not in `vendor/PATCHES.md`.

### F9 — no `rig_art.nim`; robot/crate/floor baking is JS, and `global.nim` is a JSON payload module
- **Where:** `src/rware/` contains no `rig_art.nim` (`ls src/rware/`);
  `client/broadcast_core.js:101` (`bakeRobotChips`), `:166` (`bakeCrates`), `:339` (`bakeFloor`),
  `:266-272` (asset fetch); `src/rware/global.nim:1-110`.
- **Note says:** `design.md:682` lists `src/ctf/rig_art.nim` as **forked**; `design.md:693` keeps
  the art byte-for-byte; `design.md:1168-1171` — "Robots are **baked at load** by `rig_art.nim`'s
  compositor … 96 pre-baked chips"; `design.md:844-854` — the three named edits to `global.nim`
  keep "the sprite/object pools, the compositor" and bake the floor "at install with pixie".
- **Code:** `global.nim` emits `robotsJson`/`shelvesJson`/`requestsJson` cell-space arrays and
  carries the pool bases as bare constants (`RobotSpriteBase* = 1000`, `ShelfObjectBase* = 2000`,
  `FloorDarkenPermille* = 180`); there is no pixie import and no compositor. The observable
  outcome the note describes (96 chips, three sizes × four facings × loaded/empty, tinted crates,
  darkened tiled floor) is produced, but in `broadcast_core.js`, at page load, from the same
  starter PNG/JPEG assets. Not in `vendor/PATCHES.md`.

### F10 — `--strict-text-bounds` measured zero canvas strings in both CI steps
- **Where (evidence):** CI run `33074159923` (main, `d303e6c`, conclusion `success`), job
  `wasm-viewer` (id `98524413139`):
  - `Load the bundle in a real browser` →
    `{"loaded":true,"ms":319,"clock":"DELIVERED 12 / 8 PAR · TICK 289/500 · TURN 15/25 · JAM 6 · BLOCKED 219", …,"feed_lines":0}`
    then `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`
  - `Worst-case renderer fixture (full-cap commander lines)` →
    `{"loaded":true,"ms":2052,"clock":null,"scorebug":null,"feed_lines":0}` then the same
    `canvas text: 0 drawn, …` line.
- **Where (cause, inferred from code):** the board canvas is transferred to a Dedicated Worker —
  `replay-viewer/static_replay.js:91-96` (`canvas.transferControlToOffscreen()`, with
  `showFailure('This browser does not support OffscreenCanvas Workers')` as the only alternative),
  `client/broadcast_core.js:48,74`. `tools/ci/viewer_smoke.mjs:360` hooks
  `window.CanvasRenderingContext2D.prototype` only, injected via `page.addInitScript`
  (`viewer_smoke.mjs:467`), which does not reach Worker globals. The two canvas `fillText` calls
  in the tree (`broadcast_core.js:394` — the `W1`/`W2` pad labels; `:458` — requested-shelf ids)
  therefore run where the instrumentation is not.
- **Checklist says** (item 15): "`total: 0` means the check covered nothing (a worker/OffscreenCanvas
  or WebGL renderer) and is not evidence of anything."
- **What the fixture does instead:** `tools/ci/renderer_fixture.html:167-219` measures the *DOM*:
  it asserts a `.rw-say` feed row exists at 360/620/630/1024 px, that its box is ≥ 20×6 px and not
  at a negative top/left, that `textContent` still contains the full 120-rune emoji-terminated
  string, that `#reqrail` has chips, that `#jamchip` is `.on`, and that `#pname-0` is ≥ 18 px wide.
  It fails by setting `data-replay-error`, which `viewer_smoke.mjs` reads. This is real coverage of
  the LLM-text path; it is simply not the `canvas_text` number the checklist gates on. **This game
  draws no LLM text on canvas at all** — no speech bubbles anywhere in `broadcast_core.js` or
  `client/game_block.html` (grep for `bubble`/`drawSay`/`speech` returns nothing); the radio lands
  in the DOM `#killfeed`.
- **Untested:** whether any board-canvas string (`W1`, `W2`, a shelf id at 12 px per cell) ever
  lands outside the canvas. Nothing in the tree measures it.

### F11 — the forbidden-vocabulary list drops `kill`
- **Where:** `tests/test_rware_endcard_labels.nim:13-17`
  ```nim
  Forbidden = ["Lives", "LIVES", "Clstr", "Cap<", "flag", "heart", "paint",
               "hopper", "hill", "POV", "spray", "grenade", "med kit"]
    ## The design note's list, minus `kill`: `#killfeed` is one of the ids the
    ## same note lists as KEPT …
  ```
- **Note says:** `design.md:1097-1098` includes `kill` in the list and asserts **zero** matches.
- The stated reason checks out: `design.md:1071` lists `#killfeed` among the ids kept, and
  `client/replay_broadcast.html:1002` has `<div id="killfeed"></div>`. The removed
  `.beat-marker.kill` CSS rule *is* separately enforced by
  `tools/build_broadcast_page.py:34` (in `REMOVED_SELECTORS`) and by
  `tests/test_rware_viewer.nim:141` (beat CSS set equals `{delivery, jam, fallback, end}`).
  Not in `vendor/PATCHES.md`.

### F12 — `game.docs` uses inline `{"type":"text"}` values, not the note's `uri` form
- **Where:** `coworld_manifest_template.json` → `game.docs.readme = {"type":"text","value":"# cogame-rware-warehouse\n…"}`;
  `game.docs.pages = [{"id":"rules.md","title":"Rules","content":{"type":"text","value":<8418 chars>}},
  {"id":"porting.md","title":"Porting RWARE","content":{"type":"text","value":<6369 chars>}}]`.
  Embedded by `tools/embed_manifest_docs.py` and re-checked by
  `tests/test_rware_manifest.nim:129` ("the embedded docs equal the files they were embedded from").
- **Note says:** `design.md:1261-1263` — `{"readme": {"type":"uri","value":".../README.md"}, "pages":
  [{"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}}, …]}`.
- **Checklist item 10 says** `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`
  — i.e. the code matches the checklist and diverges from the note. Not in `vendor/PATCHES.md`.

### F13 — `throttled` is a fallback `cause` outside the note's closed enum
- **Where:** `src/rware/decide.nim:354-355` (`cause = "throttled"` when the error message starts
  with `llm throttled`) and `:379` (`elif engine.client.throttled: "throttled"`).
- **Note says:** `design.md:397-398` — "`cause ∈ {timeout, parse_error, transport_error,
  no_credentials, rate_guard, budget_guard, disconnected}`". `design.md:955` repeats `cause` as a
  `fallback`-record field without re-listing it.
- The record schema is otherwise as pinned (`decide.nim:194-204`: `k/turn/slot/attempt/cause/detail`,
  detail `sanitizeLine`d at `MaxFallbackDetailRunes = 200`).

### F14 — the `turnSpacingMs` sleep is inside the `turnBudgetMs` window, so the single retry is often skipped
- **Where:** `src/rware/decide.nim:242-244` (`turnStart = getMonoTime()` before anything else),
  `:296-299` (the spacing sleep), `:306-314` (the loop's budget check).
- **Trace:** `turnStart` is taken at the top of `turn()`. The spacing floor then sleeps up to
  `turnSpacingMs` (12 000 ms) *after* `turnStart` is taken. The attempt loop's first statement is
  `if getMonoTime() - turnStart >= budget:` with `budget = turnBudgetMs` (14 000 ms). In the
  steady state the note describes (haiku answering in 3–4 s, `design.md:362`), the sleep is ~8–9 s;
  a seat whose attempt-1 request runs to the 9 s `attempt1Ms` deadline leaves ~17–18 s elapsed, so
  the `attempt == 1` iteration takes the `break` branch and writes
  `fallbackRecord(turn, seat, 2, "timeout", "per-turn budget exhausted before attempt 2")`
  **without issuing the retry batch**. A fast parse failure (~3 s) still leaves ~11 s and does
  retry.
- **Note says:** `design.md:164-165` — "Each seat that timed out, errored, returned non-JSON or
  returned no usable `verb` is retried **once**"; `design.md:394-396` — "On a seat's timeout or
  parse failure: **retry once** in the next batch". Checklist item 8 says the same.
- **Wall clock, traced:** with `b_N` = batch start of turn N, the floor gives `b_N ≥ b_{N-1} + 12 s`
  and the budget caps the post-batch work at ~9 s (no retry) or ~13 s (retry), so the steady-state
  period is ≤ ~13 s and 25 turns ≤ ~325 s — comfortably inside the 660 s stop and the 720 s
  (60 % of 1200 s) target. The note's own worst case is 350 s (`design.md:361`). No hang path.
  The sleep itself is bounded: `sleep(min(turnSpacingMs, turnSpacingMs - since))` with
  `since < turnSpacingMs` (`decide.nim:298-299`).

### F15 — `detectJam` returns only the largest linked group, not the union of all jams
- **Where:** `src/rware/jam.nim:74-86`
  ```nim
  if group.len >= 2 and group.len > best.len: best = group
  ```
- **Note says:** `design.md:219-222` — "A **jam** is the set of robots with `stuck ≥ jamTicks = 8`
  that are linked by the blocking relation …, closed transitively, with **at least 2 members**."
  Two disjoint 2-robot standoffs are possible at four seats; only one would be reported, counted
  in `jams`, hashed (`sim_state.nim:175-176` mixes `jamState.members`) and shown.
- The blocking relation, the `≥ 2` floor, the `stuck ≥ jamTicks` gate and the single-robot-against-
  a-wall exclusion are all as the note pins them (`jam.nim:37-73`).
- Related, same file: `jam.nim:100-101` re-raises `started` when the membership *changes* while a
  jam is already active, without an intervening `cleared` — so a `jam` beat/event can follow a
  `jam` with no `jamclear` between them. `design.md:221-222` describes only enter/leave.

### F16 — the replay's re-derived `fallbackTurns`/`llmTurns` do not match the recorded ones
- **Where:** live side `src/rware/episode.nim:95-100` (`of dsFallback: inc sim.fallbackTurns[seat]`
  — every turn whose installed directive is a fallback); playback side
  `src/rware/roster.nim:163-165`:
  ```nim
  of "fallback":
    if slot >= 0 and slot < SeatCount and node{"attempt"}.getInt(1) == 2:
      inc sim.fallbackTurns[slot]
  ```
- **Trace:** `decide.nim:278` writes the `budget_guard` / `rate_guard` / `no_credentials` fallbacks
  with `attempt = 1`, and `decide.nim:290` writes the `disconnected` record with `attempt = 1` for
  a seat whose directive source is `dsScripted` (so the live counter does *not* move for it). The
  two counters therefore disagree in both directions after a re-derivation.
- These are non-hashed fields (`sim_state.nim:149-177` mixes none of them), so the hash chain is
  unaffected; and the authoritative numbers ride in the `result` control record
  (`roster.nim:119-124`). The note (`design.md:948-949`) says chat records are "re-applied at
  playback into non-hashed fields" without pinning agreement, so this is an internal inconsistency
  rather than a stated-contract break.

### F17 — after a delivery is credited, a standing `deliver` order parks the robot **on** the workstation
- **Where:** `src/rware/pilot.nim:197-217`
  ```nim
  if robot.cell == goal:
    case order.kind
    …
    of okDeliver:
      ## The engine credits the delivery when the shelf arrives; standing on
      ## the pad is the whole action.
      discard
  ```
  The credit at `src/rware/sim.nim:303-304` sets `lastResult = orDone` but nothing marks the
  directive finished; `chooseAction` never reads `lastResult`. The robot is still carrying
  (`sim.nim` never detaches the shelf — `design.md:217`), so the `okDeliver` refusal at
  `pilot.nim:164-166` does not fire either. The robot emits `NOOP` on the pad every tick until the
  next command turn changes the order — up to 19 ticks.
- **Note says:** `design.md:609` — `deliver W` "Finishes with `done` on credit"; `design.md:622-625`
  — "An order that has finished leaves the robot **idle**, and an idle robot executes the fixed
  **park rule** … Without it, a robot that finished a delivery mid-turn would stand on the
  workstation and wall off the only lane to it."
- Both scripted baselines switch to `stow` on the next turn (`baselines.nim:155-156`, `:201-202`),
  so the exposure is bounded by `turnTicks`; an LLM seat that repeats `deliver` extends it.

### F18 — turn-1's default order is `hold`, not `courteous`'s order
- **Where:** `src/rware/directives.nim:54-58` (`defaultOrder()` → `okHold`), `src/rware/sim.nim:25-26`
- **Note says:** `design.md:169-170` — "an order whose fields do not validate is repaired to that
  seat's previous order (**turn 1's default is `courteous`'s order**)"; `design.md:400-401` — "the
  pilot always has an order: this turn's, else last turn's, else `courteous`'s."
- **Trace:** in practice `engine.turn` computes a scripted/fallback directive for every non-LLM and
  every unreachable seat at turn 1 before any tick, so the default is only reachable for an LLM
  seat whose *turn-1* reply is say-only: `decide.nim:158-160` returns with
  `order.fromReply = false`, and `sim.nim:25` (`haveDirective[seat]` still false) installs the
  `hold` default rather than the courteous order. The robot is actuated either way (F1
  notwithstanding), so "never unactuated" holds.

### F19 — `yield` excludes the robot's own cell and every queue-lane cell from the passing-place table
- **Where:** `src/rware/warehouse.nim:93-107` (`if x == laneLeft or x == laneRight: continue`),
  `src/rware/robots.nim:240-262` (`if cell != me: result.add(cell)`)
- **Note says:** `design.md:611` — `yield`'s goal is "the nearest **passing place** — a highway cell
  with ≥ 3 free orthogonal neighbours, i.e. an aisle junction (ties by lowest cell index)". Neither
  exclusion is named.
- Both are explained in the code (`robots.nim:243-246`: standing still is a length-1 cycle, so the
  robot behind you still cannot pass) and both are reflected in `docs/RULES.md:101`. The `≥ 3`
  neighbour rule and the lowest-cell-index tie-break are exactly as pinned
  (`warehouse.nim:101-107`, `robots.nim:251-262`). `PATCHES.md:49-53` covers only the
  robots-as-obstacles half.

### F20 — the endcard's "TEAM SCORE" is seat 0's score
- **Where:** `src/rware/broadcast.nim:170` — `"score": sim.scoreOf(0)`, rendered by
  `client/page_script.js:467` as `TEAM SCORE <n>`.
- **Code:** `scoreOf(0) = 100 * teamDelivered + delivered[0]` (`sim_state.nim:74-79`), so the
  headline number carries seat 0's individual epsilon.
- **Note says:** `design.md:1156` — "and `TEAM SCORE 1403`", against
  `design.md:885` `"delivered": [5, 3, 3, 3]` — 1403 is the score of a seat with 3, i.e. not
  seat 0 (1405). Cosmetic; the league reads `results.scores`, which is correct
  (`roster.nim:80`).

### F21 — stale copy-paste text in the provenance tooling and the page comment
- **Where:** `tools/build_broadcast_page.py:7` ("appends the **MAGENT-BATTLE** game block"),
  `tools/build_broadcast_page.py:24` ("the board is a fixed **45x45** grid with a 1:1 aspect"),
  `client/page_script.js:600` and the copy of it at `client/replay_broadcast.html:1656`
  ("The context the appended **MAGENT-BATTLE** block reads the inherited chrome").
- The board is 10×11 / 16×11 (`design.md:86-93`) and the slug is `rware-warehouse`. The banner the
  script actually emits (`build_broadcast_page.py:57-79`) is correct. Comment text only; no
  behaviour.

### F22 — test 22's "connects then never answers" half is not covered
- **Where:** `tests/test_rware_engine.nim:53-78` — the test drives
  `runScriptedEpisode(config, "", joinSeats = {0'u8, 2'u8})`, i.e. only the *never connects* case.
- **Note says:** `design.md:1435-1437` — "22. `no seat can stall` — **a seat that connects then
  never answers**, *and* a seat that never connects at all, both produce a finished episode…"
- The budget-guard test (`test_rware_engine.nim:80-101`) exercises an LLM seat with no credentials
  falling back every turn, which is adjacent but not the same path (no socket, no per-turn
  deadline consumed).

### F23 — the rate guard is applied only to attempt 1
- **Where:** `src/rware/decide.nim:261-267` computes `rateBudget` once per turn and decrements it
  while building `open`; `:327` records every request's timestamp, including the retry batch, but
  the retry batch itself is never checked against `RateWindowLimit`.
- **Note says:** `design.md:376-380` — "if issuing **the next batch** would push the trailing-60 s
  count above **28**, the seats that would exceed it skip the call for that turn". The retry batch
  is a batch.
- Bounded regardless: at most 8 requests per turn and one turn every ≥ 12 s
  (`decide.nim:296-299`), so the trailing-60 s count cannot exceed ~40 even with universal retries;
  the steady state is the note's 20/min. Never a sleep on the critical path, as pinned.

---

## Traced and consistent

Everything below I opened and checked line by line; none of it produced a finding.

**Resolution rules (RWARE collision semantics)**
- `src/rware/sim.nim:224-238` — loaded-move veto: cancelled to `NOOP` only when the target is a
  different cell, holds a **standing** shelf (`robots.nim:80-88` keeps carried shelves out of
  `shelfAt`), and the occupant is not itself carrying. Line-for-line equivalent to
  `vendor/upstream/warehouse.py:829-844`; upstream's `_LAYER_SHELFS` includes carried shelves at the
  carrier's cell, which the port folds into the layer-exclusion instead — the truth table is the
  same because two robots can never share a cell.
- `src/rware/sim.nim:65-195` (`commitMovers`) vs `warehouse.py:848-869`: functional graph
  (out-degree ≤ 1, `sim.nim:93-98`), weakly-connected components by union-find (`:100-133`),
  2-cycle ⇒ nobody in the component moves (`:153-156` `continue`), longer cycle ⇒ every robot on a
  cycle node (`:157-161`), self-edge is a length-1 cycle so a queue behind a stationary robot stays
  (verified by hand on the {4→5, 5→5} case), otherwise the DAG longest path (`:162-195`).
- Determinism pins (`design.md:201-205`): cells ordered by `y·W + x` (`warehouse.nim:23-24`);
  `members` is built by ascending cell scan so `members[0]` is the lowest-indexed node
  (`sim.nim:129-134`); the cycle walk starts there (`:139`); the longest-path tie-break keeps the
  first (lowest-index) start via `bestStart < 0` (`sim.nim:185`). I verified the reachability
  argument that makes a walk from the lowest node always find the component's unique cycle.
- Wall bump clamps to the robot's own cell and becomes a self-edge (`warehouse.nim:142-153`,
  `sim.nim:56-63`) — upstream's `req_location` clamp.
- `LEFT`/`RIGHT` walk `[UP, RIGHT, DOWN, LEFT]` (`upstream.nim:37`, `warehouse.nim:155-166`).
- Load/unload (`sim.nim:258-284`): lift only from the robot's own cell when empty; drop refused on
  **every** highway cell including the delivery row and the queue lane (`isHighway`).
- Delivery order `W1` then `W2` (`sim.nim:292-321`), credit only to the robot on the pad, shelf
  stays on the forks, `teamDelivered` +1 once.
- Jam step (`sim.nim:324-348`): `stuck`/`blockedMoves`/`blockedThisTurn` increment for a robot that
  requested FORWARD (including one vetoed to NOOP — `requestedForward` is snapshotted at
  `sim.nim:218`, before the veto) and did not move; `stuck` reset otherwise.
- No floating point in the sim modules; `streamDraw` is splitmix64 over `(seed, stream, index)`
  (`robots.nim:51-69`), so the request stream is a pure function of `(seed, k)` with `k` =
  deliveries so far (`sim.nim:314`) — the anti-collusion pin, apart from the candidate-set issue in
  F3.

**Decision path**
- One `RequestBatch` per attempt, all open seats, one `makeRequests` call
  (`decide.nim:317-333`) — a single parallel batch per turn, retry as a second batch, `attempt < 2`
  hard cap (`:306`). No sequential path anywhere.
- Deadlines: `attempt1Ms 9000` / `retryMs 4000` converted with `max(1, deadlineMs div 1000)`
  (`:315-333`) — floors to 9 s / 4 s, and `sim_config.nim:61-62` clamps both to ≥ 1000 ms so the
  floor is an identity.
- Tolerant parse: `extractJsonObject` (`directives.nim:75-113`) scans for the outermost balanced
  `{…}` with string/escape awareness, tolerates prose and fences, falls back to first-brace…
  last-brace, and raises only when there is no object at all.
- Repair-don't-reject (`directives.nim:128-192`): unknown verb / off-board `fetch` shelf → previous
  order + `rejected++`; say-only reply is usable and keeps the standing order; `deliver` with an
  unknown station defaults to W1; `stow` coordinates clamped into the board; non-object raises.
- Fallback is literally the `courteous` proc (`baselines.nim:224-231`, asserted by
  `tests/test_rware_pilot.nim:101-115`), and every fallback writes a record
  (`decide.nim:278, 311, 356, 381`) counted into `results.fallbackTurns` (`episode.nim:97-98`).
- Credential ladder and model rotation match `design.md:332-346` exactly
  (`llm.nim:92-126`, `:67-90`, `:147-148`, `:139`); `sonnet-4-6` is absent; `maxOutputTokens = 900`
  (`sim_config.nim:32`); the system prompt in `llm.nim:197-235` is textually identical to
  `design.md:513-551`.
- No-credentials path sets `disabled = true` and every turn falls back instantly with no network
  wait (`llm.nim:119-125`, `decide.nim:264-281`), and logs both phrases phase 60 greps
  (`llm.nim:124` "LLM provider is unavailable", `decide.nim:384` "falling back").

**Waits and bounds** (checklist 5)
- `attempt1Ms 9000`, `retryMs 4000`, `turnBudgetMs 14000`, `turnSpacingMs 12000`,
  `wallClockBudgetSeconds 660`, `lobbyJoinTimeoutTicks 2400` (240 in the cert fixture) — all in
  `sim_config.nim:22-27` and clamped at `:59-66`, `wallClockBudgetSeconds` hard-capped at 660.
- Budget guard: `elapsed + 2 × ceil(turnBudgetMs/1000) > wallClockBudgetSeconds`
  (`decide.nim:250-257`) → `llmOff`, a `budget_guard` record, remaining turns scripted; the episode
  still ends `complete` (asserted `tests/test_rware_engine.nim:80-101`).
- Rolling-60 s rate guard, limit 28 (`decide.nim:22-29`, `:225-232`, `:261-267`) — see F23 for the
  one gap.
- Wall-clock stop at `elapsed >= wallClockBudgetSeconds` (`episode.nim:43-52`), written as one
  `stop` record and applied by `sim.applyStop` on record **and** on playback
  (`sim.nim:47-54`, `replay_runtime.nim:95-98`).
- No unbounded loop: `runHeadlessEpisode` caps at `maxFrames` (`episode.nim:181`); the server frame
  limiter sleeps at most one 1/30 s frame (`server.nim:542-550`); the shutdown grace is 20 s
  (`server.nim:39, 581-584`); `yieldStep` probes at most 16 junctions (`pilot.nim:134-138`);
  `advanceReplayFrame` advances at most 8 frames and skips at most 64 lull frames
  (`replay_runtime.nim:261, 270-273`); `boundedDirectiveRecord` has a 16-iteration guard
  (`directives.nim:240`). Mummy serves on its own thread (`server.nim:382-388`), so a 14 s LLM
  stall cannot stall `/healthz`.
- Arithmetic: 660 s stop + 20 s grace = 680 s < 720 s (60 % of the manifest's
  `episode_timeout_minutes: 20`). Cert fixture uses 240 s.

**String truncation** (checklist 9)
- `truncateRunes` uses `runeLen`/`runeSubStr` (`sim_types.nim:103-112`); `truncateBytes` is the one
  byte cap and walks back off continuation bytes (`:114-125`); `sanitizeLine` and `sanitizeSay`
  truncate in runes *before* filtering (`:127-142`).
- Caps applied: `say` 120 (`directives.nim:154`, `:223`), `notes` 240 (`:155`), policy label 64
  (`decide.nim:213`), fallback detail 200 (`decide.nim:203`), `stopDetail` 200
  (`roster.nim:116`, `episode.nim:118`), prompt 4000 (`server.nim:452-453`), reply body 4096 bytes
  (`llm.nim:181-186`), provider error bodies (`llm.nim:165, 174, 180`).
- Tested at the cap with 4-byte emoji: `tests/test_rware_pilot.nim:162-179` and `:201-211`;
  whole-replay UTF-8 validation at `tests/test_rware_replay.nim:184-209`; strict-parser round trip
  through `tools/replay_summary.py` at `:137-182`. (Note: in the replay-side tests the per-frame
  `say` the test writes is overwritten by the scripted directive before the record is emitted, so
  the emoji reaching the replay there come from the join names and `stopDetail`; the *direct*
  cap-boundary assertions in `test_rware_pilot.nim` are the load-bearing ones and they are real.)

**Replay writer / re-derivation** (checklist 2)
- `COWLDRWH` magic + `u16` format + game name/version + resolved config JSON
  (`replays.nim:137-147`, `sim_types.nim:17-19`); records `join/leave/gamestart/orders/chat/hash/stop`
  (`:149-205`); one hash per frame (`episode.nim:123`).
- Config JSON carries seed, `num_agents`, every layout and deadline field, `players[].name` and
  `slots[]` — and **no tokens** (`sim_config.nim:162-215`).
- `frameCount` is the max tick over hashes **and** stops **and** gamestarts/orders/chats
  (`replays.nim:279-288`) — the fix for the stop landing past `maxFrame`.
- Playback drives `sim.advanceFrame`, the same proc the live loop drives
  (`replay_runtime.nim:104` / `episode.nim:115`), applies recorded orders at their frame before the
  advance (`replay_runtime.nim:85-94`) exactly as `runTurnIfDue` does live
  (`episode.nim:89-101` then `:147`), and compares `sim.gameHash()` against the record every tick
  (`replay_runtime.nim:105-115`).
- `gameHash` mix order is *exactly* `design.md:770-772`: per robot `(slot, x, y, facing, carrying,
  stuck)`; per shelf `(id, x, y, carrier)`; the queue in order; `teamDelivered`; per-seat
  `delivered` and `stowed`; the jam members; `tick` (`sim_state.nim:149-177`).
- The load-bearing stop is tested for all three end reasons — `tickCap`, `wallClock`, `fault` —
  with `hashMismatchTick == -1` after full playback (`tests/test_rware_replay.nim:29-91`).
  A corrupted hash is caught at its tick (`:210-221`).
- The wasm entry imports the same `rware/sim` (`replay-viewer/rware_replay.nim:13`), runs the
  load-time pre-scan then renders frame 0 (`:50-79`), and exposes `rware_mismatch_tick`
  (`:108-109`) surfaced as `#mmwarn` (`broadcast.nim:222` `mismatchTick`).

**Viewer executes / provenance** (checklist 3, 13, 14)
- `coworld_manifest_template.json` → `game.replay_viewer = {"bundle": "static-replay-viewer"}`
  under `game`; `tools/build_replay_viewer.sh` present and mode 100755; no `/client/replay` route
  is declared to the platform (the server serves it locally only — `server.nim:250-255`, marked
  "NEVER declared to the platform"). The worker fetches only the replay URL
  (`static_replay_worker.js:118-137`).
- **`client/chrome_common.js` is byte-identical to the starter's** — `diff` clean,
  sha256 `7ace7287…72f7c` on both, and pinned as a literal at `tests/test_rware_viewer.nim:13-14`.
- **`client/replay_broadcast.html` provenance verified by reproduction.** I ran
  `python3 tools/build_broadcast_page.py --starter /workspace/starters/coworld-ctf/client/replay_broadcast.html
  --page-script client/page_script.js --game-block client/game_block.html --out /tmp/rebuilt.html`
  and `diff` against the committed file is **empty**. So the page is provably the starter's page
  with (a) exactly the CSS selectors in `REMOVED_SELECTORS` (`build_broadcast_page.py:28-39`)
  dropped, (b) the two `BODY_CUTS` (`#viewpanel`, `#fpv`) and the `#povBadge` line removed,
  (c) the seven relabels at `:181-197`, (d) the page IIFE swapped for `client/page_script.js`,
  (e) the banner + `client/game_block.html` appended. The removal list is the note's
  (`design.md:1053-1067`) plus a few consistent extras (`.zbtn`, `.mm-cap`, `.pgrp`,
  `.beat-marker.hillhold`, `flagflip`, `flagkill`). Sections 1–5 of the starter's stylesheet, the
  transport, the scrubber/momentum/beats/lulls, the endcard and the locker-room curtain are all
  present above the banner. The 2 154-line / 4 660-line size ratio is accounted for entirely by
  the deleted `#fpv` + `#viewpanel` blocks and the replaced IIFE, not by a rewrite.
- **One starter, one bootstrap.** `replay-viewer/config.nims` emits **non-modularized**
  (no `MODULARIZE`, no `EXPORT_NAME` anywhere in the tree) and
  `static_replay_worker.js:188` sets `Module.onRuntimeInitialized`;
  `:239` `importScripts('./wire_constants.js', './broadcast_core.js', './rware_replay.js')` in that
  order. The `config.nims`/worker/`static_replay.js` diffs against coworld-ctf are pure
  `ctf_`→`rware_` renames plus the F6 flag removal and the fps source at `static_replay.js:46`.
- `data-replay-loaded="true"` is set on `<html>` in the `'loaded'` branch
  (`static_replay.js:161-164`), which the Worker posts only *after* `ingestPacket()`
  (`static_replay_worker.js:129-136`); `data-replay-error` is set in `showFailure`
  (`static_replay.js:8-20`).
- **CI evidence:** run `33074159923` on `main` at `d303e6c`, conclusion `success`; jobs
  `test` ✓, `manifest` ✓, `docker-smoke` ✓, `wasm-viewer` ✓. `wasm-viewer` `needs: docker-smoke`
  (`ci.yml:350`), downloads the `smoke-replay` artifact, and its `Load the bundle in a real
  browser` step **ran** with `--timeout 90 --soak 10 --strict-text-bounds` and reported
  `{"loaded":true,…}` with a live clock string (`DELIVERED 12 / 8 PAR · TICK 289/500 · TURN 15/25`).
  No `continue-on-error` anywhere in `ci.yml`. `tools/ci/viewer_smoke.mjs` is byte-identical to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs`.
- Transport rules: `relayout()` sets `--hudscale`, `--topband`, `--band` on
  `document.documentElement` (`page_script.js:559, 581, 590-591`), iterating to a fixed point.
  `#endcard { top: var(--topband, 0px); bottom: var(--band, 0px) }`
  (`replay_broadcast.html:569-570`), shown with `#endcard.on` (`:582`, set at
  `page_script.js:476`). Seeks take it down: `seekToFraction` removes `.on` directly
  (`page_script.js:506-507`) and `renderEndcard` removes it on any frame whose phase is not
  `gameover` (`:461-465`), which covers the beat buttons, the transport buttons and the keyboard.
  Nothing the game block adds is in the transport band — `#reqrail` and `#jamchip` hang off
  `--topband` (`replay_broadcast.html:1772-1780`, `:1808-1812`), which commit `bd19767` moved
  there deliberately.
- Beats are labelled `<button>`s with `title` + `aria-label` that `send('s:'+tick)`
  (`game_block.html:245-266`), built by `warehouseBeat` — never `markBeat`; the CSS set is exactly
  `.beat-marker.{delivery,jam,fallback,end}` (`replay_broadcast.html:1835,1840,1845,1851`), pinned
  by `tests/test_rware_viewer.nim:141`.
- `#viewpanel`/`#minimap`/`#zoom*`/`#fpv*`/`#povBadge` appear nowhere in the page except inside
  explanatory comments (`replay_broadcast.html:1263, 1684-1687`) — verified by grep; the board is
  fixed 10×11 / 16×11 so dropping the panel is what the pin requires.
- 360 px rules: `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow:
  ellipsis }` (`replay_broadcast.html:1717-1722`); `.tiny` plate/rail/jam-chip rules at
  `:1761-1763`, `:1805-1806`, `:1824`.

**Manifest and `num_agents`** (checklist 6, 10, 12)
- `num_agents: 4` in `variants[0].game_config`, `variants[1].game_config` and
  `certification.game_config`; absent at every variant top level (variant keys are exactly
  `id/name/description/game_config`). No literal `tokens` array in any `game_config`.
- `len(certification.players) == len(certification.game_config.players) == num_agents == 4`, and
  both declared players (`courteous`, `shuttle`) are seated twice each.
- `config_schema`: `additionalProperties: false`, `required: ["tokens","players"]`, every array
  carries `minItems`/`maxItems` (`tokens` 4/4, `players` 4/4, `slots` 0/4),
  `num_agents {integer, minimum 4, maximum 4, default 4}`, and the full property list of
  `design.md:1250-1255`.
- `game.protocols` carries **both** `player` and `global` as `{"type":"uri","value":…}` objects.
- `results_schema` properties are exactly the 24 keys `fleetResultsJson` emits
  (`roster.nim:92-117`), asserted by `tests/test_rware_engine.nim:43-51`;
  `reason: enum ["complete","deadline","fault"]`.
- Top level: `$schema`, 5 tags, `episode_timeout_minutes: 20`, no `game.tags`, `game.description`
  present, `game.owner`, `game.runnable.run = ["/bin/rware-warehouse"]`,
  `env.ANTHROPIC_API_KEY_URI = secret://coworld/rware-warehouse/anthropic_api_key`,
  `player[].resources.limits.cpu == "1"`.
- `tools/ci/docker_smoke.sh:106-150` enforces all four SEAT-COUNT invariants plus the
  `SMOKE_SEATS` second declaration, each with a `SEAT-COUNT FAIL:` prefix. **`grep -i "SEAT-COUNT"`
  over the docker-smoke job log for run `33074159923` returns nothing**; the job printed
  `smoke OK: seats=4 results=601B replay=141714B reason=complete`.
- The checklist's placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three
  workflows, `docker_smoke.sh` and `policies.json` matches nothing. The only surviving
  angle-bracket names are `<run_id>` in the two artifact-readback comments — the documented
  expected residue.
- `coworld-release.yml`: build (`:165`) → certify (`:183`, with `--timeout-seconds 300`) →
  upload-policies (`:217`) → upload-coworld (`:315`) → secret put (`:414`). All three workflows
  present; `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are mode 100755.
- `tools/ci/policies.json`: four policies on one image `/bin/rware-warehouse-player` — two
  `PLAYER_PROMPT` champions (`rware-warehouse-picker`, `rware-warehouse-router`) and two
  `PLAYER_SCRIPTED` fillers; champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`.

**Both name spaces** (checklist 4)
- Agents see aliases only: `seatView` emits `you`/`fleet`/`seen.robots[].alias`/`radio[].from` from
  `seatAliasName` (`decide.nim:82-130`); no `seatNames` read anywhere in `decide.nim` or `llm.nim`.
  `tests/test_rware_labels.nim:51-70` asserts it.
- The viewer maps aliases to real names: `rosterJson`/`seatsJson`/`endcardJson` carry both
  (`broadcast.nim:105-174`) from `sim.seatNames`, restored on playback from the join and `register`
  records (`roster.nim:131-162`). `showPlayerLabels` default false (`sim_config.nim:30`) and false
  in both variants and the cert fixture.
- The registration record is redacted — policy label, kind, baseline; never the prompt
  (`decide.nim:206-216`, `server.nim:469-472`), asserted by
  `tests/test_rware_replay.nim:135` (`check "a strategy" notin writer.bytes()`).

**Scripted baseline plays full episodes legally** (checklist 7)
- `tests/test_rware_engine.nim:16-51` runs a real four-seat all-scripted episode through
  `runHeadlessEpisode` (the same per-frame proc `server.nim` calls), asserts
  `endReason == complete`, `endRule == tickCap`, `teamDelivered > 0`, the score formula per seat,
  and the exact results key set. `tests/test_rware_pilot.nim:38-99` asserts bounded orders over
  200 states × both baselines and legal actions over 40 states × all five verbs × four seats.
  `tools/ci/baseline_tuning.json` + `tests/test_rware_tuning.nim` + the `ci.yml:185` re-run of
  `tools/tune_baselines.nim --check` back the "tuned, not guessed" pin.
- The CI docker smoke ran a real containerised episode with no API key and reported
  `episode end reason: complete`, 545 frames, 141 714-byte replay.

**Port fidelity gates**
- `vendor/upstream/{warehouse.py,__init__.py}` sha256 match `vendor/UPSTREAM.md` and
  `src/rware/upstream.nim:19-22` (`cc1be89d…`, `a5aa8b89…`), commit
  `96fbc64e3eae5fee915e0d390f864fa06ddccd47`. `vendor/LICENSE-rware` present.
- `tests/test_rware_upstream.nim` regex-checks the action enum, the direction wrap list, the two
  grid formulas, the four `highway_func` clauses, the goal formula, the size and difficulty tables,
  `max_steps`, `sensor_range`, `msg_bits`, `request_queue_size`, and the collision text
  (`:124-139`). `tests/test_rware_layout.nim` covers five `(rows, cols)` shapes cell for cell plus
  the 10×11/32/(4,10)(5,10) and 16×11/64/(7,10)(8,10) assertions and the one-cell-aisle check.

---

## Could not determine

- **No Nim toolchain in this sandbox** (`nim: command not found`), so I could not execute
  `tests/*.nim` at this sha. Everything I say about the tests is read from their source; the
  *outcome* rests on CI run `33074159923`'s green `test` job. The one test-file change during this
  run (`d303e6c`, `git show -- tests/`) tightens an assertion — it does not loosen one; the other
  two commits add tests wholesale.
- **F3's practical effect.** Whether the immediate-re-request case actually occurs at the shipped
  seeds, and by how much the off-by-one candidate set shifts the stream, would be settled by
  running `initWorld` + a delivery loop for a range of seeds and comparing against a transcription
  of `warehouse.py:915-917`. `tests/test_rware_requests.nim` asserts the stream is a pure function
  of `(seed, k)` and unsteerable — both still true under the port's rule — but does not compare
  against upstream's candidate set.
- **F10's blind spot.** Whether any board-canvas string ever lands outside the canvas is not
  observable from the current gate, because the drawing happens in a Worker the instrumentation
  does not reach. It would be settled by an equivalent hook on
  `OffscreenCanvasRenderingContext2D.prototype` inside the Worker, or by a fixture that renders
  through `broadcast_core.js` on a main-thread canvas.
- **F1/F17's episode-level cost.** Whether `hold`-as-park or the workstation squat measurably
  reduces `teamDelivered` in a real four-seat episode would need a run of both variants with an
  LLM seat; the scripted baselines mask both (neither ever issues `hold`, and both switch to
  `stow` on the turn after credit).
- I did not attempt to verify the **hosted** certification, the league seeding, or anything outside
  the repo and its CI logs.
