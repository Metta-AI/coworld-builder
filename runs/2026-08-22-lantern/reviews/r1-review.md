# r1 review — lantern

Repo: `Metta-AI/cogame-lantern` at `06d4da71149c7581d940c1ccb371fec3467890aa` (clean checkout at
`/workspace/scratch/cogame-lantern-review`).
Range: `bafbc3d..06d4da7` (three commits: bootstrap, the fork, one manifest fix).
Design note: `/workspace/coworld-builder/runs/2026-08-22-lantern/design.md` (byte-identical to the
repo's `docs/plans/2026-08-22-lantern-design.md` — verified with `diff`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–12 plus the
simultaneous-decision batching rule).
Files read in full: 42 — all 19 `src/lantern*/*.nim`, all 16 `tests/*.nim` + `tests/support/helpers.nim`,
`replay-viewer/{lantern_replay.nim,static_replay.js,static_replay_worker.js,config.nims}`,
`client/{chrome_common.js,replay_broadcast.html (CSS + chrome regions),broadcast_core.js (render/event regions)}`,
`coworld_manifest_template.json`, `data/vault.mapspec.json`, `tools/ci/{docker_smoke.sh,policies.json}`,
`tools/build_replay_viewer.sh`, `.github/workflows/ci.yml`, the relevant regions of
`.github/workflows/coworld-release.yml`, `Dockerfile`, `Dockerfile.replay-viewer`, `compose.yaml`, `AGENTS.md`.
CI evidence cited: `gh run list -R Metta-AI/cogame-lantern --branch main -w ci.yml` → run **32610126558**,
conclusion **success**, on the reviewed sha; `gh run view 32610126558 --log` (3493 lines) read for the
test list, the smoke output and the skip lines.

Findings are numbered F1… continuously across sections, as the brief asks.

---

## Blocking

### F1 — captured LLM error text reaches the replay through byte-index string slices

- **Where:** `src/lantern/llm.nim:175`, `:183`, `:188`, `:197` → `src/lantern/llm.nim:215-220` →
  `src/lantern/llm.nim:303-309` → `src/lantern/server.nim:266-270` → `src/lantern/events.nim:16-23,61-65`
- **Observed**, traced step by step:
  1. `textOf` builds every error message it raises out of a **byte** slice of the provider payload:
     ```nim
     175:    let detail = response.body[0 .. min(response.body.high, 400)]
     183:    let detail = response.body[0 .. min(response.body.high, 300)]
     187-188: raise newException(LanternError, "anthropic error " & $response.code &
                ": " & response.body[0 .. min(response.body.high, 300)])
     196-197: raise newException(LanternError, "reply cut off at max_tokens before " &
                "any JSON: " & result[0 .. min(result.high, 160)].replace("\n", " "))
     ```
     Line 197 is the most reachable of the four: `result` there is the **model's own generated text**,
     which the system prompt (`llm.nim:35-63`) actively invites to be non-ASCII (`note`, `say`).
  2. `curlySender` catches that and stores the message verbatim:
     `llm.nim:219-220  except CatchableError as error: result[index].error = error.msg`.
  3. `decideAll` copies it into the fallback note without touching it:
     `llm.nim:303-309  ... detail: reply.error))`.
  4. The server emits it as a replay event: `server.nim:266-270  state.sim.emit(fallbackEvent(..., note.detail))`.
  5. The only downstream guard is `events.nim:65  "detail": clipRunes(detail, MaxDetailRunes)`, and
     `clipRunes` (`events.nim:16-23`) is:
     ```nim
     result = text.strip()
     if result.runeLen <= limit: return
     result = result.runeSubStr(0, limit)
     ```
     It **returns the string unchanged** when it is already ≤ 200 runes. A sequence that was already
     split mid-codepoint at byte 160/300/400 is ≤ 200 runes in the overwhelming majority of cases, so
     it is passed through untouched. Even on the long path, `runeSubStr(0, 200)` counts from the front
     and preserves a break that lands inside the first 200 runes.
  6. `fallback` events go into `sim.events` (`sim.nim:29-30`), into `buildReplay`'s `events` array
     (`replay.nim:163-165,180`), and out to `COGAME_SAVE_REPLAY_URI` (`server.nim:341-342`).

  By contrast, every other error string on this path *is* rune-safe: `orders.nim:60-62` uses
  `head.runeSubStr(0, 160)`, `orders.nim:163` uses `clip(...)`, and `orders.nim:22-28` / `roster.nim:48-49,56-59`
  are all `runeSubStr`. These four lines in `llm.nim` are the only byte slices left on a replay path.
- **Checklist item:** #9 — "**Rune-safe truncation.** Every string that reaches the replay (`say`,
  `notes`, prompts, **captured errors**) is truncated on **rune** boundaries." The design note states the
  same rule in stronger words (§Order schema and character caps): "never slicing a `string` by byte index
  on any path that reaches the replay", and pins `fallback.detail` at ≤ 200 **runes**.
- **Why blocking:** the replay is fetched from S3 and strictly parsed by the platform (SPEC definition-of-done
  check 4, and `tools/ci/docker_smoke.sh:277-284` enforces the same locally). A `fallback` event carrying a
  half-codepoint makes the whole replay document invalid UTF-8, which is exactly the failure the note calls
  out as "renders in a browser and then fails a strict JSON parser".
- **Observed vs inferred:** the byte slicing and the absence of a repairing guard are **observed** (read at
  the lines above). That invalid UTF-8 actually lands in a shipped replay is **inferred** — it needs a
  provider error body or a `max_tokens`-truncated reply whose non-ASCII codepoint straddles the cut. It is
  **untested**: no test exercises `textOf`, and `tests/test_orders.nim:120-124` only feeds *valid* input to
  `clip`, so the "captured errors" half of item 9 has no coverage. What would settle it: a unit test that
  passes a `Response` whose body is e.g. `"é".repeat(200)` through `textOf` → `fallbackEvent` and asserts
  `validateUtf8(...) == -1` on the serialised event.

**No other checklist item is falsified.** Items 1–8 and 10–12, and the one-parallel-batch rule, are all
traced and satisfied — see "Traced and consistent" below.

---

## Non-blocking

### F2 — `crate_push` is emitted every push tick; only the sound ring is rate-limited

- **Where:** `src/lantern/sim.nim:419-432`
- **Observed:** on every tick a loose crate actually moves, the code emits
  `sim.emit(cratePushEvent(...))` (`:425-427`) and increments `sim.cogs[slot].cratesPushed` (`:424`)
  unconditionally; the 12-tick gate at `:428-430` guards only `sim.addSound(sndPush, ...)`.
- **Note says:** §Resolution order step 7 — "the crate moves and a `crate_push` event + push sound ring
  are emitted (rate-limited to one per crate per 12 ticks)". The parenthetical reads as covering both.
  §The world/§Sound only rate-limits the ring ("a crate push emits a 420 px ring at most once per crate per
  12 ticks"), which is what the code does, so the two note passages are themselves ambiguous.
- **Knock-on, observed:** `results.crates_pushed` therefore counts *push ticks*, not crates. The manifest is
  self-consistent about this — `results_schema.properties.crates_pushed.description` reads "Push ticks this
  seat contributed" — but the note's §Results document example `"crates_pushed": [2, 1, 1, 0, 3, 2]`
  reads as crate counts.
- **Event volume is not a problem in practice:** the CI wasm-viewer job reports "1440 ticks, 339 events"
  (run log, `wasm-viewer` job), and the committed `tests/fixtures/smoke_replay.json` is 98 KB — well inside
  the note's ≈ 90 KB event budget.

### F3 — the seeker view's `found[]` entries drop two documented fields

- **Where:** `src/lantern/render.nim:120-123`
  ```nim
  found.add(%*{"alias": aliasOfSlot(other),
               "at_s": hider.foundTick.float / TargetFps.float})
  ```
- **Note says:** §Seeker view — `"found": [{"alias": "Moth-1", "at_s": 21.5, "by": "Owl-2", "mode": "beam"}]`.
  `by` and `mode` are absent from the emitted object.
- **Also observed:** `at_s` is `foundTick / 24`, i.e. seconds since **match** start, so a half-2 find reports
  ~141 s rather than the ~21 s the note's example implies. `mode` and the finding seeker *are* in the
  replay's `found` event (`events.nim:96-100`), so only the in-episode seeker observation is affected.

### F4 — the two attempt deadlines round up to 9 s + 4 s = exactly the 13 s turn budget; no separate outer per-turn deadline

- **Where:** `src/lantern/config.nim:19,22-23`; `src/lantern/llm.nim:294-297`; `src/lantern/server.nim:249-252`
- **Observed:** `attempt1Ms = 8_500`, `attempt2Ms = 3_500`, `turnBudgetMs = 13_000`. `decideAll` converts
  each to whole seconds by ceiling, because `curly.makeRequests(batch, timeout)` takes an int seconds
  timeout (`/workspace/scratch/pkgs/curly/src/curly.nim:711-715,739`):
  ```nim
  294-296: let budget = if attempt == 1: (sim.config.attempt1Ms + 999) div 1000
                        else: (sim.config.attempt2Ms + 999) div 1000
  ```
  → 9 and 4. `tests/test_engine.nim:99-101` pins exactly that and asserts `9 + 4 <= 13`.
  `server.nim:249-252` calls `decideAll` with no enclosing timer; the per-turn bound is the sum of the two
  inner deadlines plus prompt building and parsing for up to 6 seats.
- **Note says:** §Decisions — "first attempt deadline **8.5 s** … one retry with a **3.5 s** deadline …
  Worst case 8.5 + 3.5 = 12.0 s ≤ the 13.0 s turn budget", and §Degrade-never-hang lists "one outer per-turn
  deadline of 13.0 s" as a distinct bound.
- **Effect on the note's arithmetic: none.** The note already budgets 13.0 s/turn × 42 = 546 s, so
  602 s expected < 720 s stands. Every wait is still explicitly bounded (checklist item 5 is satisfied); the
  observation is that the bound is the sum of the inner deadlines rather than a separate outer one, and that
  it equals rather than undercuts the turn budget.

### F5 — `all_found` (declared deviation #2): ticks continue, and only the hider seats stop being queried

- **Where:** `src/lantern/sim.nim:592`, `:623-630`; `src/lantern/server.nim:137-147`; `src/lantern/types.nim:312`
- **Observed:** on the tick the last hider is found, `sim.nim:623-626` emits `act_end{reason:"all_found"}`
  and sets `sim.actEnded[half-1] = true`. `actEnded` is then **never read** anywhere else — `grep -rn actEnded
  src/ tests/ replay-viewer/` returns only `types.nim:312` and `sim.nim:623-629`. The loop keeps ticking, and
  `inc sim.huntTicksPlayed[half - 1]` at `sim.nim:592` keeps counting.
  `activeSeats` (`server.nim:137-147`) drops found hiders but still returns the three seekers, so **3 LLM
  calls per turn continue** for the rest of the act.
- **Note says:** §Resolution order step 15 — "emit `act_end{reason:"all_found"}` and **skip the remaining
  hunt ticks of that half** (they would accrue nothing; the denominator is unchanged … this also returns
  wall clock to the budget)."
- **Does the deviation preserve the observable rules?** For scoring, yes and exactly: because the ticks run,
  `huntTicksPlayed` reaches the full `huntTicks`, which is precisely the "denominator is unchanged" the note
  asks for. `tests/test_rules.nim:142-161` asserts both the `act_end` reason sequence `@["time","all_found"]`
  and `huntTicksPlayed[0] == huntTicksPlayed[1] == config.huntTicks`. What is not realised is the wall-clock
  saving; the builder's summary "all_found stops LLM turns" holds for 3 of the 6 seats, not all 6.

### F6 — the aim hold-on-contact reflex overrides the note's aim table, and keys on the team lit set rather than the seeker's own

- **Where:** `src/lantern/control.nim:206-246`, in particular `:214-228`; `src/lantern/control.nim:100-116`
- **Observed:** before dispatching on `cog.order.aim`, `aimTurnFor` short-circuits:
  ```nim
  222:  if cog.order.aim != amHold:
  223-225:    var litNow = false
              let point = litHiderPoint(sim, slot, half, litNow)
              if litNow: return clampInt(bradDelta(bearingBrads(point.x - cog.px, ...)), ...)
  ```
  so `sweep`, `target` and `track` all behave as `track` whenever a hider is lit.
  The reflex's justification is sound: at `AimTurnRate = 5` brads/tick a swept beam crosses a 13 px body in
  ~1–7 ticks, well under `lockOnTicks = 12` (`config.nim:30`), so without it the beam→`found` path would be
  unreachable and only touch tags would ever fire.
  The comment at `:218-221` says "whenever **this seeker's own** lantern is on a hider"; the helper it calls,
  `litHiderPoint` (`control.nim:100-116`), tests `sim.teamLit(hider.px, hider.py)` at `:109` — i.e. **any**
  seeker's lantern. So all three seekers snap their aim onto a hider the moment one of them lights it.
- **Note says:** §The control layer step 3 gives a closed aim table with no such override, and lists `track`
  as the mode that "turns toward the nearest lit hider".

### F7 — pointwise visibility instead of a rasterised shadowcast (declared deviation #1)

- **Where:** `src/lantern/sim.nim:116-147`; `src/lantern/arena.nim:192-243`; `src/lantern/types.nim:63-69`
- **Observed:** there is no shadowcast, no `applyFovCone`, no `FovCellCount`, no `fovCaches`. `litBySeeker`
  (`sim.nim:122-136`) answers one point at a time: bubble test → range test (`d2 > range²`) → integer cone
  test (`absInt(bradDelta(bearing, cog.aim)) > lanternConeBrads`) → `lineOfSight`. `teamLit` (`sim.nim:138-147`)
  ORs the three seekers on demand rather than materialising a set. `lineOfSight` (`arena.nim:211-243`) is an
  integer DDA over the **8 px** occlusion grid (`FovCell = 8`, `types.nim:63-69`), with endpoint cells exempt.
- **Note says:** §Sim module keeps "`src/ctf/sim.nim:2257-2475` — the shadowcast FOV, `FovCellCount`,
  `fovCellIndex`, the per-player `fovCaches`", and §Resolution step 10 says "run the shadowcast over
  `blockMask` from its cell … then union in the 60 px bubble. Union the three seekers' sets into `teamLit`."
- **Does it preserve the observable rules?** Yes for the definition the note itself gives in §The world /
  §Lantern — "within `lanternRangePx = 420` … within `lanternConeBrads = 18` … **and** has line of sight …
  plus an omni bubble of `visionBubblePx = 60` with line of sight" — which is exactly what `litBySeeker`
  computes, and the integer cone/range tests are the ones the note specifies. Two consequences:
  occlusion is quantised to 8 px cells rather than exact pixels (a determinism-safe approximation, identical
  in both builds), and the note's step-10 promise that step 10 is a per-tick pass is replaced by lazy queries
  from step 11 and from the view builders. `tests/test_vision.nim:27-97` pins the range, cone, occlusion,
  bubble, team-radio and lanterns-off-during-build behaviours exactly at their boundaries.

### F8 — the committed map differs substantially from the note's authored JSON block, not just "nudged"

- **Where:** `data/vault.mapspec.json`; note §Sim module, "The map file"
- **Observed** (`python3` read of the committed file):
  | | note | committed |
  |---|---|---|
  | crates | `(300,180) (935,479) (500,120) (735,539) (300,470) (935,189) (500,540) (735,119) (617,240) (618,419)` | `(150,329) (1085,330) (250,290) (985,369) (450,380) (785,279) (300,180) (935,479) (617,270) (618,389)` |
  | nook anchors | `(220,300) (617,470) (1015,300)` | `(240,329) (450,490) (995,329)` |
  | sweep lanes | start at `(205,560) / (617,470) / (1030,560)` | all three start at `(617,500)`, the pen mouth |
  | pen, spawns, caught_pen, far_corner | as in the note | identical to the note |
  The lane change is explained in `AGENTS.md:88-93` ("a lane whose first waypoint is unreachable pins a
  seeker against the pen wall for a whole half — that happened in development").
- **Fairness invariants, checked directly:** all 36 obstacles have their exact 180° twin about (617.5, 329.5),
  and all 10 crates do too (I re-ran the check independently; `tests/test_map.nim:23-39` asserts the same).
  The three **nooks are not** rotationally symmetric — the twin of the middle anchor `(450,490)` would be
  `(785,169)`, which is absent — and no test asserts nook symmetry. This does **not** affect half-comparability,
  because both halves use the identical map, identical nooks and the same bottom-centre pen; the note's own
  test spec (§Sim module) only names "the geometry" and `test_map.nim` covers obstacles and crates.
- **Note says:** the note pins the crate/nook/lane coordinates verbatim in a JSON block. The declared
  deviation ("map coordinates nudged for exact 180° symmetry and one-crate-wide nook doorways") understates
  the size of the change: the note's crate list is already 180°-symmetric about (617.5, 329.5), so symmetry
  alone does not explain the new coordinates.

### F9 — `lantern_replay.data` is in the note's bundle manifest but not in the bundle (declared deviation #7)

- **Where:** `tools/build_replay_viewer.sh:66-71`; `Dockerfile.replay-viewer:47-54`;
  `replay-viewer/config.nims:36-47`; `client/replay_broadcast.html:36`
- **Observed:** the bundle copy list is `index.html static_replay.js static_replay_worker.js chrome_common.js
  broadcast_core.js wire_constants.js lantern_replay.js lantern_replay.wasm font.ttf` plus `art/*`. No `.data`.
  `config.nims` passes no `--preload-file`, so emscripten emits no data package; the only asset the page loads
  out of the bundle is `url('./font.ttf')` (`replay_broadcast.html:36`), and `font.ttf` **is** copied
  (`build_replay_viewer.sh:70`, `Dockerfile.replay-viewer:38,50`). The Dockerfile assertion tail
  (`:47-54`) lists exactly the 15 files that do exist and `test -s` each.
- **Note says:** §Viewer, "Files in the bundle (each must return 200 with a non-trivial size for phase-60
  check 8(b))" includes `lantern_replay.data`.
- **Consequence:** nothing is missing at run time; the note's file list is the thing that is wrong. A phase-60
  check driven off the note's list rather than off `Dockerfile.replay-viewer:48-52` would 404 on
  `lantern_replay.data`.

### F10 — float arithmetic does run inside the step, in `events.nim`

- **Where:** `src/lantern/events.nim:12-14`, called from `src/lantern/sim.nim:586-588` (`foundEvent`),
  `sim.nim:321-322` (`halfEndEvent`, inside `prepareTick`), `server.nim:231-233` (`turnStartEvent`);
  guard at `tests/test_vision.nim:103-112,157-178`
- **Observed:** `proc seconds*(ticks: int): float = round(ticks.float * 10.0 / TargetFps.float) / 10.0`
  is float arithmetic, and it executes inside `applyTick`/`prepareTick`. The float guard scopes to seven
  modules — `StepPath = ["types.nim","arena.nim","crates.nim","rules.nim","sim.nim","control.nim","baselines.nim"]`
  (`test_vision.nim:104-105`) — deliberately excluding `events.nim`, per the comment at `:106-110`. The
  trigonometry ban *is* applied to all of `src/lantern` and `replay-viewer` (`test_vision.nim:142-155`), i.e.
  broader than the note's `src/lantern/*.nim`.
- **Note says:** §Sim module — "**No `sin`, `cos`, `atan2`, `pow`, `sqrt`, `exp`, `log`, `fmod` or float
  arithmetic of any kind appears in the sim step**". §Tests item 3, however, scopes the float grep to
  "`float`/`float64` **inside the step path**", which is what the test does. So the test matches the note's
  test spec and the prose is the absolute statement that is not literally true.
- **Determinism is unaffected, traced:** the digest (`state.nim:70-87`) covers only integer cog/crate/tick
  state; event JSON is never read back into the sim, and the viewer reads events from the replay bytes
  (`lantern_replay.nim:126`) rather than recomputing them. So no cross-build divergence follows from this.

### F11 — the canvas find-burst is dead code, and there is no 0.4 s find hold

- **Where:** `client/broadcast_core.js:34,319-326,388-389`; `replay-viewer/lantern_replay.nim:63-72`;
  `src/lantern/broadcast.nim:45-72`; `replay-viewer/static_replay_worker.js:99-107`;
  `client/replay_broadcast.html:1749-1797`
- **Observed:** `broadcast_core.js:388-389` reads `packet.bursts` and pushes an expanding-ring entry;
  nothing ever writes that key — `packetJson()` (`lantern_replay.nim:63-72`) emits
  `type, tick, half, act, turn, act_left_ticks, cogs, crates, sounds, hb, hidden_s, hiders_left, intermission`
  and `snapshotJson` (`broadcast.nim:54-72`) has no `bursts` either. So the 240-radius board ring at
  `broadcast_core.js:319-326` never draws.
  The DOM side of readout 4 **does** work: `drainEvents` (`replay_broadcast.html:1783-1802`) fires
  `fireBurst(hider.x, hider.y)` (the `#burst` CSS flash, `:1548-1555`), the `#bannerlane` banner, the
  `#killfeed` line and a `found` beat marker.
  The playhead hold exists only for the intermission: `static_replay_worker.js:106`
  `if (packet.intermission) play.holdUntil = Date.now() + 2000;` — there is no find hold.
- **Note says:** §Viewer readout 4 — "a one-frame white flash, a **240-frame-radius expanding ring** at the
  hider's position, the beam that found it snapping to a hard white for 12 frames … **The playhead holds for
  0.4 s on the burst.**" The flash, banner and feed line are present; the ring, the beam-snap and the hold
  are not.

### F12 — `chrome_common.js` is rewritten, not "copied unchanged" (declared deviation #3)

- **Where:** `client/chrome_common.js:1-27` vs `/workspace/starters/coworld-ctf/client/chrome_common.js`
- **Observed:** 256 lines against the starter's 838. The header at `:10-16` states what was dropped
  ("four teams, perks, lives meters, flag beats and the POV lens"). The factory shape survives:
  `test_viewer.nim:85-90` asserts `window.ChromeCommon = function (ctx)`, `renderTransport`, `renderClock`,
  `renderMomentum`, `getSpoilers`, and all five are present.
- **Note says:** §Viewer — "`client/chrome_common.js` is copied unchanged."
- **The markup half of the claim checks out.** I enumerated the `id="…"` set of both HTML files: the starter
  has 66, lantern 64; the only ids dropped are `fpv, fpv-canvas, fpv-cap, fpv-gear, fpv-grip, fpv-hp, fpv-hud,
  fpv-map, fpv-map-canvas, fpv-name, povBadge` — exactly the first-person PiP family the note authorises
  removing — and the ids added are `actchip, burst, heartbar, hidebug, hidebug-moth, hidebug-owl, im-half,
  im-next, intermission`, i.e. the note's five plus four children of them. Every one of the ~57 inherited ids
  the note lists by name is still present (`test_viewer.nim:17-38` asserts the same list).

### F13 — the determinism gate runs 1440 ticks, not the note's "full 5040-tick match"

- **Where:** `tests/test_determinism.nim:13-15`; `tests/support/helpers.nim:27,34`
- **Observed:** `recordEpisode` calls `testSim(seed = seed, prep = 240, hunt = 480)` and `testSim`/`testConfig`
  default to `prep = 240, hunt = 480` → `totalTicks == 1440`. All four determinism tests (`:18-53`) run at
  that length. The golden fixture is also 1440 ticks (`tools/record_fixtures.nim:20-23`), which **is** what
  the note specifies for the fixture.
- **Note says:** §Tests item 6 — "identical digest at every keyframe over **a full 5040-tick match**, run
  twice in one process and once in a fresh instance; … a committed golden fixture … pins the digests for
  seed 42 over 1440 ticks".
- **The 5040-tick path is exercised elsewhere but not for digest equality:** `tests/test_perf.nim:9-23`
  runs 5040 ticks and asserts `sim.tick == 5040` and `keyframes.len == 210`; `test_perf.nim:25-39` re-derives
  a 5040-tick replay and asserts `again.ok` (which *is* a full-length digest match, just against the same run
  rather than a second one); `test_baselines.nim:56-84` plays 5040 ticks. No test compares two independent
  5040-tick runs' digests.

### F14 — three of `test_engine`'s cases assert at the results/roster layer, not through the turn loop

- **Where:** `tests/test_engine.nim:182-214`, `:216-244`; `src/lantern/server.nim:174-186`, `:201-205`, `:289-296`
- **Observed:** the fault case (`:182-201`) and the wall-clock case (`:203-214`) construct results with
  `sim.scriptedResults(erFault, edSimFault)` / `(erDeadline, edWallClock)` directly rather than driving
  `runEpisode`; the never-registers case (`:217-223`) and the disconnect case (`:235-244`) exercise the
  `Roster` object. Nothing asserts the `COGAME_PLAYER_FAILURE_URI` write at `server.nim:180-183`, nothing
  asserts that a budget-guarded episode ends `complete/full_time` end to end (`test_engine.nim:146-156` checks
  only that the decisions are `osFallback` with cause `budget_guard`), and nothing drives the
  `nowMs() > wallDeadline` branch at `server.nim:201-205`.
- **Note says:** §Tests item 9 phrases all of these as turn-loop properties.
- This is a coverage gap, not a behavioural one: I read the corresponding server code and it does what the
  note describes. It is also outside the checklist — item 5's requirement is that the waits are bounded, which
  they are (see "Traced and consistent"), not that a test drives each branch.

### F15 — `test_viewer`'s wasm harness self-skips in the `test` job (declared deviation #9)

- **Where:** `tests/test_viewer.nim:93-104`; `tools/build_replay_viewer.sh:81-83`; CI run 32610126558 log
- **Observed:** the test checks `fileExists(dist / "lantern_replay.js")` and calls `skip()` when the bundle is
  absent. The `test` job has no bundle, so the run log shows the skip twice (debug and release):
  `"skipped: no replay-viewer/dist (built by the wasm-viewer CI job, which runs tools/wasm_replay_smoke.cjs itself)"`
  followed by `[SKIPPED] the node harness runs when the bundle has been built`.
  The real invocation happens in the `wasm-viewer` job, where `build_replay_viewer.sh:81-83` runs
  `node tools/wasm_replay_smoke.cjs`, and the log records
  `wasm viewer smoke OK: 1440 ticks, 339 events, digests all matched`.
  The rest of the file does not skip: the static chrome assertions, the `coworld-replay` bridge assertions and
  `check rederive(fixture).ok` on the committed smoke replay (`:106-110`) all ran in both modes.
- **Not a checklist-item-1 violation:** the skip is present in the initial commit `61e7325`, not added during
  this run. `git log -p -- tests/` over the whole history shows exactly one test change on this run, in
  `06d4da7`, and it *adds* two assertions to `test_manifest.nim` (`manifest["episode_timeout_minutes"] == 20`
  and `not game.hasKey("episode_timeout_minutes")`) while replacing one weaker assertion on the same key.
  Nothing was deleted, widened, skipped or removed.

### F16 — `decideAll` runs outside `stateLock` while `/global` reads the same `Sim` under it

- **Where:** `src/lantern/server.nim:214-252` (esp. `:220 simRef = state.sim`, `:249-252`), `:461-467`;
  `src/lantern/baselines.nim:89,106,132,141,155`
- **Observed:** the turn block releases `stateLock` before calling `client.decideAll(simRef, ...)`, which is
  correct for not blocking the socket threads for up to 13 s. But `decideAll` → `scriptedOrder` writes
  `sim.cogs[slot].memo[...]` (`baselines.nim:89,106,132,141,155`) and reads `sim.cogs` / `sim.crates`, while
  `globalUpgradeHandler` (`server.nim:461-467`) and `broadcastGlobalLocked` (`:113-119`) read the same `Sim`
  from mummy's worker threads under the lock.
- **Inferred, benign:** the only shared state `decideAll` writes is `memo`, an `array[4, int]`
  (`types.nim:241`), which `snapshotJson`/`cogsJson` (`broadcast.nim:12-31`) never reads. The string fields a
  spectator does read — `cog.order.note`, `cog.order.say` — are assigned only under the lock
  (`server.nim:256-260`), so there is no torn string. A concurrent `/global` connect during a turn can
  therefore see a stale int, not corrupted memory. Not on the checklist; recorded because the lock discipline
  is not uniform and the reason it is safe is non-obvious.

---

## Traced and consistent

**Checklist item 1 — CI green, no test loosened.**
`gh run list -R Metta-AI/cogame-lantern --branch main -w ci.yml` → run **32610126558**, `completed success`,
on the reviewed sha `06d4da7`; jobs `test` (48 s), `docker-smoke` (59 s), `wasm-viewer` (1 m 5 s) all ✓.
I grepped the run log for the test invocations: all **16** `tests/*.nim` files ran **twice** each
(`--hints:off` and `--hints:off -d:release`), 32 invocations, no file omitted. Repo variables that could
narrow the set are empty (`gh api repos/Metta-AI/cogame-lantern/actions/variables` → `total_count: 0`).
`git log -p -- tests/` across the whole history: one hunk this run, in `06d4da7`, adding assertions — see F15.

**Checklist item 2 — replay re-derivation, and the viewer derives from it.**
`replay.nim:192-232 rederive` rebuilds a `Sim` from `config` + `map` + `decodeControls(controls_b64)`, steps it
with `prepareTick`/`applyTick` and compares every keyframe digest (`:217-231`), reporting the first mismatch tick.
`tests/test_replay.nim:110-115` asserts `again.ok`, `mismatchTick == -1` and `checked == keyframes.len` on a real
end-to-end episode; `:117-126` flips two control bits and asserts the digests catch it; `:139-143` re-derives the
committed fixture. The viewer runs the **same** `rederive` (`lantern_replay.nim:95`) and then draws from a sim it
re-derives itself with the same controls (`:74-86,136,143-157`), reading `world.cogs`/`world.crates` in
`packetJson` (`:34-72`) — not from the recorded keyframes. `mismatchTick` is surfaced to the page as
`data-replay-mismatch-tick` (`static_replay.js:54-59,166,172`) and `#mmwarn`.

**Checklist item 3 — static viewer.**
`coworld_manifest_template.json` → `game.replay_viewer == {"bundle": "static-replay-viewer"}`
(asserted at `test_manifest.nim:73-74`). `tools/build_replay_viewer.sh` exists, is committed **100755**
(`git ls-files -s` → `100755 0a672e33…`), takes the absolute bundle dir, refuses a relative path or a
wrongly-named dir (`:16-23`), and is invoked by path in `ci.yml:218-219` after an explicit `test -x` gate
(`:205-216`). The only network call the viewer makes is `fetch(message.replayUrl)` in
`static_replay_worker.js:128-153`, where `replayUrl` comes from `?replay=` (`static_replay.js:186`); no other
`fetch`/`XMLHttpRequest`/`importScripts` of a remote origin exists (`importScripts` at
`static_replay_worker.js:272` is three relative bundle files). The manifest declares no `/client/replay` pod
path — the string appears only in `game.protocols.global` prose and in a release-workflow error message; the
server route (`server.nim:514`) is the local-viewing route the note explicitly keeps (§Viewer, §Server).

**Checklist item 4 — both name spaces.**
In-game: `labels.nim:14-39` derives `Moth-1..3`/`Owl-1..3` from slot parity; `render.nim` uses `aliasOfSlot`
exclusively (I grepped — no `config.players` reference in `render.nim`); the welcome frame carries
`alias`/`team`/`hides_in_half` and no name (`server.nim:455-459`); the LLM user message is `PLAYER_PROMPT` +
`seatView` (`llm.nim:250-261`), so no real name can reach a model.
Spectator: `replay.names.players` (`replay.nim:63-77`), `results.names` (`replay.nim:105-106`),
`/global.policyNames` (`broadcast.nim:45-53`), and the scorebug plates
(`chrome_common.js:93,98-106` `teamPlayers`/`teamHeadline` reading `meta.names.players`, driven from
`replay_broadcast.html:1828`). The board itself labels cogs with `cog.alias` — `broadcast_core.js:278` and
`:310-314` ("the in-game alias, never the player name").

**Checklist item 5 — degrade-never-hang; every wait bounded.** I enumerated every blocking construct:
| wait | where | bound |
|---|---|---|
| player connect | `server.nim:155-162` | `playerConnectTimeoutMs` (90 s hosted, 60 s cert), `sleep(200)` poll |
| LLM attempt 1 | `llm.nim:294-297,210` | 9 s (`curly.makeRequests` int-seconds timeout, `curly.nim:711-715,739`) |
| LLM attempt 2 | same | 4 s; `for attempt in 1 .. 2` (`llm.nim:285`) — never a third |
| per-turn | `server.nim:249-252` | sum of the two above (see F4) |
| budget guard | `server.nim:240-247` | `remainingMs < 2 * turnBudgetMs` → all remaining turns scripted |
| engine hard stop | `server.nim:192,201-205` | `wallClockBudgetMs` = 660 s → `deadline/wall_clock` |
| done broadcast | `server.nim:33,330-337` | `DoneBroadcastMs = 3_000` |
| artifact POST | `server.nim:98` | `curl.post(..., 60)` |
| player connect retry (client side) | `lantern_player.nim:35-36,60-71` | 12 × 500 ms, then `quit(0)` |
The main loop (`server.nim:195-288`) advances `sim.tick` by exactly one per iteration (`sim.nim:631`), so it
terminates. Every other loop I checked is bounded by construction: `slideAxis` (`sim.nim:206-235`, `remaining`
strictly decreases), `intRoot` Newton (`types.nim:333-344`), `bearingBrads` bisection (`types.nim:449-455`),
`lineOfSight` Bresenham with an out-of-bounds exit (`arena.nim:228-243`), `stepTo` (`lantern_replay.nim:81-86`).
There is no blocking read anywhere: the player socket is fire-and-forget from the server's side
(`server.nim:121-131` only `send`s; the seat is informational, per the note). Arithmetic: 42 × 13 s = 546 s
+ 20 s connect + 6 s sim + 30 s writes = 602 s < 720 s, and both variants' `wallClockBudgetSeconds` (660 and
400) plus the cert fixture's (180) are asserted ≤ 720 at `test_manifest.nim:82-87`.

**Checklist item 6 — `num_agents`.** Present and `== 6` in `variants[default].game_config`,
`variants[sprint].game_config` and `certification.game_config`; `len(certification.players) == 6` and
`len(certification.game_config.players) == 6` (read directly from the manifest, and asserted at
`test_manifest.nim:15-31`). `tools/ci/docker_smoke.sh:102-143` enforces all four invariants — key present
(`:102-110`), positive integer (`:111-117`), `len(certification.players)` equal (`:121-126`),
`len(certification.game_config.players)` equal (`:127-132`) — each raising a `SEAT-COUNT FAIL:`-prefixed
`SystemExit`, plus the `SMOKE_SEATS` cross-check at `:133-143`. `SMOKE_SEATS` defaults to `6`
(`docker_smoke.sh:47`, asserted against `Seats` at `test_manifest.nim:39-42`). The script is committed
**100755** and `ci.yml:162-170` `test -x`'s it before invoking by path. **I grepped the whole 3493-line CI log
for `SEAT-COUNT FAIL`: 0 matches**, and the smoke printed `game=lantern seats=6 …` and
`smoke OK: seats=6 results=1366B replay=129917B reason=complete`. The engine independently refuses any other
seat count (`config.nim:117-120`, asserted by `test_startup.nim:55-60`).

**Checklist item 7 — scripted baseline plays a full episode legally.**
`tests/test_replay.nim:14-39,52-58` runs a full scripted-vs-scripted episode over the real sim to
`totalTicks`, writes `results.json`, and asserts `parseJson(readFile(resultsPath))["reason"] == "complete"`.
`test_scoring.nim:66-77` runs another and asserts `reason == "complete"`, `end_rule == "full_time"`.
`test_baselines.nim:26-53` is the bounded-orders assertion: 2 baselines × 4 seeds × both roles, ≥ 500 orders
checked against `legalOrder` (intent legal for the role, target inside `[8,1227]×[8,651]`, crate a real id or
`-1`, `needsCrate ⇒ crate ≥ 0`, `note ≤ 140` runes, `say ≤ 32` runes, seekers never crawl) and ≥ 5000 compiled
controls checked against `boundedControl` (`move ∈ [-100,100]`, `aimTurn ∈ ±5`, `action and not 0b111 == 0`).
`:55-61` asserts no fourth lock; `:63-73` asserts warden beats moth at seed 42 on both sides of the ledger.
(The clause "tuned with a grid harness" — see "Could not determine".)

**Checklist item 8 — LLM reply handling.**
Tolerance: `orders.nim:53-83 extractJsonObject` finds the first `{`, tracks string/escape state and brace
depth, and returns the outermost balanced object — so prose before *and* after, markdown fences, and a stray
`}` in the prose all parse (`test_orders.nim:26-46`). `asInt` (`:85-111`) accepts JInt, JFloat and numeric
strings; `asBool` (`:113-123`) accepts `true`/`"true"`/`1`/`"yes"`; `crate` accepts `"C4"`, `"c4"` and `4`
(`:180-192`, `crates.nim:16-33`). Repair: illegal-for-role intent → `defaultIntent(role)` (`:164`), unknown
crate → nearest legal (`:125-148`), unknown aim → `amTarget` (`:194-196`), seeker crawl forced false (`:197`).
Only a reply with no recoverable `intent` raises (`:155-163`), which is the sole thing that costs an attempt
(`test_orders.nim:129-140`). Retry: exactly one — `for attempt in 1 .. 2` (`llm.nim:285`) with the
"your previous reply was invalid" hint appended on attempt 2 (`llm.nim:258-261`, `:293`);
`test_engine.nim:108-120` asserts `recorded.batchSizes.len == 2` ("never a third") and
`:122-143` asserts one bad then one good reply costs exactly one retry.
Fallback: `llm.nim:326-330` sets `source = osFallback` and the warden order; the cause is recorded as a
`fallback` event with `cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`
(`types.nim:153-158`, `llm.nim:277-281,304-309`, `server.nim:266-270`, `events.nim:61-65`) and counted into
`results.fallback_turns` / `results.fallback_causes` (`server.nim:263-267`, `replay.nim:120-125,156-158`).
The log line phase 60 greps for is `llm.nim:328  "lantern llm: seat ", seat, " falling back to the scripted order"`.

**The simultaneous-decision rule — one parallel batch per turn.**
`curlySender` (`llm.nim:199-221`) builds one `RequestBatch`, posts every open seat into it, and issues a single
`client.curl.makeRequests(batch, timeoutSeconds)` — the only `makeRequests` call in the repo.
`test_engine.nim:68-90` asserts `activeSeats(sim, 1, actBuild).len == 3` → `batchSizes == @[3]` and
`activeSeats(sim, 1, actHunt).len == 6` → `batchSizes == @[6]`, plus `recorded.windows.len == 1` (all six
requests share one in-flight window, which a sequential walk cannot produce) and `seatsSeen[0] == huntSeats`.
`activeSeats` (`server.nim:137-147`) is what drops the three frozen seekers during a build act.

**Checklist item 9 (the parts that hold).** `orders.nim:22-28 clip` and `events.nim:16-23 clipRunes` both use
`runeLen`/`runeSubStr`. `note ≤ 140` and `say ≤ 32` are applied at `orders.nim:198-199`; `policy ≤ 48` and
`prompt ≤ 4000` at `roster.nim:48-49,56-59` (and `llm.nim:332-336 clipPrompt`); `fallback.detail ≤ 200` at
`events.nim:65`. `tests/test_orders.nim:105-118` is the note's pinned case: 31 ASCII runes + two 4-byte emoji
(`runeLen == 33`, `len == 39`), cut to exactly 32 runes keeping the first emoji whole, then `validateUtf8 == -1`
and a round trip through `orderJson`/`parseJson`. `tests/test_replay.nim:12,26-29,52-68` forces
`"vanish 🔦 é"` into the live event stream and validates the **bytes on disk** as UTF-8 before parsing.
F1 is the one class this does not cover.

**Checklist item 10 — manifest shape.** `game.docs.readme` is `{"type":"text","value":<5093 chars>}`;
`game.docs.pages` is two entries `rules.md`/`protocol.md`, each `{"id","title","content":{"type":"text","value":…}}`
(6920 and 10661 chars). `game.protocols` carries **both** `player` and `global`, each
`{"type":"text","value":…}`. Asserted at `test_manifest.nim:89-108`. `results_schema` is closed
(`additionalProperties: false`) and its 26 `properties` keys exactly equal its 26 `required` entries and exactly
equal the 26 keys `buildResults` emits — I compared all three sets; `test_manifest.nim:45-59` asserts the same
against a live `scriptedResults()`. `reason` and `end_rule` enums match the note
(`test_manifest.nim:61-70`). `episode_timeout_minutes: 20` is **top level**, not under `game`
(`test_manifest.nim:76-81`).

**Checklist item 11 — 360 px legibility.** `client/replay_broadcast.html:1484`
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }`
and `:1563-1573` the `@media (max-width: 640px)` block, which collapses `#heartbar` to 8 px dots, hides
`#viewpanel` (`display: none !important`), hides `#speedchips .chip-label`, caps `#killfeed` at two lines and
shrinks `#actchip`/`#hidebug`. `#intermission` uses `font-size: clamp(11px, 3.4vw, 17px)` (`:1535-1544`).
The inherited `--hudscale`/`--topband`/`--band`/`.tiny` relayout loop is present
(`test_viewer.nim:44-47` greps `--hudscale`, `--topband`, `--band`, `classList.toggle('tiny'`,
`ResizeObserver`, `BOARD_ASPECT`). `test_viewer.nim:49-53` pins the exact `.plate-name` string, the
`640px` media query, the `#viewpanel` rule and the clamp. `test_viewer.nim:55-60` also pins the
"names are set with `textContent`, never `innerHTML`" rule.

**Checklist item 12 — release order and scaffold.** `coworld-release.yml` step order is
Build the Coworld manifest (`:153`) → Certify locally (`:167`) → **Upload the policies** (`:206`, with the
comment "BEFORE upload-coworld") → Upload the Coworld (`:304`) → Put the Coworld secret (`:342`). All three
workflows present. Both hooks are mode `100755` and both are gated with `test -x` before invocation
(`ci.yml:162-170`, `:205-216`). `tools/ci/policies.json` has 4 policies, all `"run": "/bin/lantern-player"`:
`lantern-warren` (`PLAYER_PROMPT`), `lantern-owlnight` (`PLAYER_PROMPT` **plus**
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` at `:15`), `lantern-warden`
(`PLAYER_SCRIPTED=warden`), `lantern-moth` (`PLAYER_SCRIPTED=moth`) — asserted at
`test_manifest.nim:145-171`, including that the two champion prompts differ (identical content would dedupe to
one ladder entry). The placeholder gate:
```
grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/ci.yml .github/workflows/coworld-release.yml \
  .github/workflows/coworld-submit.yml tools/ci/docker_smoke.sh tools/ci/policies.json
```
→ **no matches, exit 0**. The `docker-smoke` job builds the image in the same job before running the smoke
(`ci.yml:172-181`), so the binary is fresh.

**Resolution order, step by step** (note §The game "Resolution order" vs `sim.nim`):
1. Phase clock — `sim.nim:312-331 prepareTick`: half boundary → `half_end`, `resetHalf`, `half_start`,
   `act_start{build}` (`:313-329`); keyframe on `tick mod 24 == 0` (`:330-331`). Order install is at
   `server.nim:256-260`, on `isTurnStart` (`rules.nim:44-45`). `phaseAt` (`rules.nim:27-42`) verified exactly
   at all eight boundaries by `test_rules.nim:11-17`.
2. Frozen seats — `sim.nim:346-355`: `frozen = phase.act == actBuild and role == roSeeker` zeroes velocity and
   crawl, holds aim, and `continue`s past motion. Frozen seekers are skipped in crates (`:390-392`),
   lock/pry (`:446-450`), footsteps (`:522`) and control compile (`control.nim:253-254` returns `Control()`),
   but still record controls (`server.nim:281-283`) and appear in keyframes (`:295-299`). Door solid during
   build (`sim.nim:104`, `arena.nim:200-201`), opened at the act boundary (`sim.nim:618-622`), verified by
   `test_map.nim:70-77`.
3–4. Control compile + quantise — `control.nim:248-298`, `moveX/moveY` clamped ±100 (`:267-268`), `aimTurn`
   clamped ±5 (`:288-289`), `action` only bits 0–2 (`:290-297`). `test_baselines.nim:18-23,47-51` bounds all
   three over 5000+ controls.
5. Aim — `sim.nim:358  cog.aim = (cog.aim + int(control.aimTurn)) and 255`.
6. Motion — `sim.nim:359-383`: `Accel` halved when crawling, friction `×144/256` on an unpowered axis with a
   `StopThreshold` snap, clamp to `topSpeed(role, crawling)` (`:189-193`, seeker 768 / hider 704 / crawl 40 %),
   per-axis slide with `MovementSlideMaxScan = 3` (`:198-235`), then cog–cog separation over every unordered
   pair in ascending order with `PlayerBouncePct = 40` (`:237-272,381-383`). `test_motion.nim` pins all of it,
   including the symmetric-under-slot-swap property (`:48-65`) and the 2000-tick wall hammer (`:32-46`).
7. Crates — `sim.nim:386-440`: crate-major then seat order, dominant axis with x on ties (`:401`),
   `pushPx` 6 hider / 4 seeker (`crates.nim:86-89`), target box tested clear of walls, other live crates and
   other cogs (`crates.nim:44-58`), crawling cannot push (`:404`), otherwise the pusher is reverted along that
   axis only (`:433-440`). `test_crates.nim:23-63` pins the 6/4 px, the crawl ban, and both blocked cases
   including "reverted along x, and only along x". See F2 for the event rate limit.
8. Lock and pry — `sim.nim:443-516`: lock needs the bit, `still` (both `|v| < StopThreshold`), a loose crate
   within `InteractRangePx = 20` and `locksUsed < maxLocksPerHider`; 24 ticks → `csLocked`, `locks_used++`,
   `crate_lock`. Pry needs the bit, `still`, a locked crate within 20 px; 72 ticks → `csBroken`, `crate_break`
   + a 900 px ring; `crate_pry` at 25/50/75 % (`:496-502`). Any progress resets on movement, on clearing the
   bit, or on changing target (`:466-468,479-481,493-495,513-515`). `test_crates.nim:65-119` pins exactly 24
   and exactly 72, the refusal at 3 locks, the reset-on-move, the immovable locked crate for both roles, and
   the 900 px ring.
9. Occlusion rebake — `sim.nim:534-535` on `blockDirty`, set by every push/lock/break (`:422,472,505`);
   `arena.nim:192-204` re-stamps static grid + door + non-broken crates.
10–12. Lanterns, detection, score accrual — `sim.nim:538-592`. Detection: `litStreak` increments while any
   seeker lights the hider, `spot` on the tick the streak becomes 1 (`:549-556`); FOUND at
   `litStreak >= lockOnTicks` (mode `beam`) or a seeker within `TouchTagPx = 24` with sight (mode `tag`)
   (`:559-574`); on FOUND, `found_tick`, teleport to `caughtPen + (24 × indexInTeam, 0)`, inert
   (`:575-588`); otherwise `hiddenTicks++` (`:589-591`), so a hider found on tick *t* does not bank *t*.
   `test_rules.nim:32-114` pins 12-exactly, the broken-streak-does-not-find case, 24 px yes / 64 px no, and
   the inert-after-found property.
13. Heartbeat and sound decay — `sim.nim:595-613`: five bands from `bandFor` (`rules.nim:50-55`,
   `types.nim:83-86`: 120/260/450/750), rings expire after `SoundLifeTicks = 24`.
14. Keyframe — `sim.nim:291-305`, appended in `prepareTick` when `tick mod 24 == 0`; carries
   `t`, FNV-1a `digest`, per-cog `[x,y,aim,stateCode]`, per-crate `[x,y,state]`, the 3 seekers' `hb`, the
   6 `hid`. State codes match the note: `0 active, 1 frozen, 2 crawling, 3 found` (`state.nim:63-68`).
15. Act/half/match end — `sim.nim:616-633`: build→hunt at the act boundary with `act_end{time}` +
   `act_start{hunt}` + door open; hunt `act_end` with `all_found` (see F5) or `time`; `finished` at
   `totalTicks`.

**Half reset** — `sim.nim:99-108` restores every crate to its authored position in `csLoose` (broken ones
return), re-places every cog with a fresh `Cog` (velocities, aim, lock/pry progress, `locksUsed`, `found`,
`memo` all zeroed) carrying **only** the score fields across (`:61-66`), clears the sounds and re-solidifies
the door. `test_rules.nim:117-140` asserts all of it plus one `half_end` and one `half_start`.

**Scoring** — `rules.nim:95-118` matches the note's formula exactly, in fixed point:
`hiddenFracMicro = clamp(Σticks × 10⁶ / (3 × huntTicksPlayed), 0, 10⁶)`;
`scoreMilli = round((10⁶ + fMoth − fOwl) / 2 / 1000)` with `owl = 1000 − moth`, so the two always sum to
exactly 1000; `comparable == false` → (500, 500). `replay.nim:91-96` sets `comparable` to
`reason != erFault and huntTicksPlayed[0] > 0 and huntTicksPlayed[1] > 0` and derives `winner` only when
comparable. `test_scoring.nim:13-18` reproduces the note's worked example to the digit (378/622);
`:20-34` asserts the sum over 200 randomised splits; `:36-64` covers the shutout, the draw, the mid-half-2
deadline normalisation and the pre-half-2 deadline; `:66-77` asserts six scores summing to 3.0.

**Results document** — `replay.nim:79-159` emits all 26 documented keys, per-seat arrays length 6 in slot
order, `team_*` arrays length 2 with index 0 = Moth. `win[seat] = comparable and milli > 500`;
`winner` null on a draw or a non-comparable episode; `final_turn = tick div turnTicks`;
`halves_played` from `huntTicksPlayed`; `fallback_causes` a 5-key object per seat over the full
`FallbackCause` enum.

**Replay writer** — `replay.nim:161-182`: `protocol == "lantern.replay.v1"` (`types.nim:19`),
`format_version 1`, `game_version "1"`, `seed`, the fully resolved `config` (tokens excluded,
`config.nim:136-163`), the map **raw node** inlined verbatim (`arena.nim:39`, `replay.nim:172`),
`names` with players/aliases/teams/policy_kinds/colors, `ticks_per_second 24`, `turn_ticks`,
`tick_count = controls.len div numAgents`, the phase table (`:41-49`), `controls_b64`
(4 bytes/cog/tick, tick-major, slot-ascending, `:18-27`), keyframes with `d` (`:51-61`), the event array and
the results document. `test_replay.nim:70-91` asserts every documented key is present, that `map`/`names`/
`config`/`phases`/`keyframes`/`events`/`results` are non-empty, and that
`decode(controls_b64).len == tick_count × 6 × 4`. `test_replay.nim:52-58` validates the bytes on disk as UTF-8
**before** parsing. Everything the viewer needs is in these bytes — the wasm module reads
`config`, `map`, `names`, `phases`, `events`, `results`, `seed`, `controls_b64` and nothing else
(`lantern_replay.nim:93-134`).

**Event vocabulary** — all 17 event types in the note's table are produced with the documented fields:
`match_start` (`server.nim:576`), `half_start` (`:582`, `sim.nim:328`), `act_start` (`server.nim:583`,
`sim.nim:329,620`), `turn_start` (`server.nim:231`), `order` (`:271`), `fallback` (`:268`),
`budget_guard` (`:244`), `crate_push`/`crate_lock`/`crate_pry`/`crate_break` (`sim.nim:425,477,501,509`),
`sound` (`sim.nim:282`), `spot` (`:554`), `found` (`:586`), `act_end` (`:619,626,630`),
`half_end` (`:321`), `end` (`server.nim:318`). `test_replay.nim:93-108` asserts an `order` per active seat per
turn across all 12 turns, ≥ 1 `crate_lock`, ≥ 1 `found`, exactly one `half_end`.

**The `coworld-replay` bridge** — `static_replay.js:19-25` (`tell` + `tell('loading')` on script entry),
`:51` (`tell('error', message)`), `:148-155` (`tell('ready')` inside a **double** `requestAnimationFrame`
after the first painted frame). Asserted at `test_viewer.nim:63-69` and grepped again in
`build_replay_viewer.sh:74-76` and `Dockerfile.replay-viewer:55-58`. Fetch bounded at 20 s by an
`AbortController` (`static_replay_worker.js:15,128-153`) with a Retry button (`static_replay.js:42-49`).

**Policy/baseline env switch** — one image, `run: /bin/lantern-player` for all four policies.
`PLAYER_PROMPT` non-empty → `policyKind == "llm"` (`roster.nim:34-39`); `PLAYER_SCRIPTED` parsed by
`parseScriptKind` (`baselines.nim:18-24`: `1`/`true`/`yes`/`warden` → warden, `moth` → moth, else none,
case-insensitive, pinned at `test_baselines.nim:87-95`); a seat with neither, or one that never registers at
all, plays warden (`baselines.nim:196-200`, `roster.nim:29`, `test_engine.nim:217-223`). Scripted seats never
reach the model (`llm.nim:270-283`, asserted `test_engine.nim:170-180`). No credentials at all → the client
disables itself once with one log line and every turn falls back instantly with no network wait
(`llm.nim:245-248`, `test_engine.nim:158-168`) — which is exactly why the offline docker smoke completed in
4 seconds with `reason=complete`.

**Two scripted baselines, different in shape** — `warden` (`baselines.nim:54-157`): nook `k` by
`indexInTeam`, push the crate nearest the doorway until ≥ 60 % coverage then lock, cap at 2 locks in the
build act, hide crawling in the hunt, flee one turn on a reported beam then cycle nooks; seeking, walk lane
`k`'s waypoints with `aim: sweep`, chase anything lit with `aim: track`, pry after two `hot`/`burning` turns
with nothing lit. `moth` (`:159-194`): never touches a crate, walks to `far_corner` and stands still crawling;
seeking, beeline to the centre then sweep at PCG32 waypoints seeded `seed xor (slot shl 8)`, re-drawn every
four turns. Both are pure functions of the world plus their own `memo`.

**Randomness** — one PCG32 per sim seeded from the episode seed (`sim.nim:91`, `state.nim:18-42`), used for
exactly two things: `addSound`'s jitter (`sim.nim:278-282`) and `moth`'s waypoints (`baselines.nim:188-192`).
Seed randomisation happens in `src/lantern.nim:73-80` **before** `config.update`, with the pinned-seed check
at `:37-44`, as the note requires.

**Manifest ↔ engine agreement** — `test_manifest.nim:134-140` loads every variant's and the cert fixture's
`game_config` through the real `config.update` and asserts it validates. `config.nim:69-82` refuses a `slots`
pin that disagrees with lantern's fixed parity rather than silently reinterpreting it.

---

## Could not determine

- **Checklist item 7's second sentence — "The baseline's parameters were tuned with a grid harness, not
  guessed."** There is no grid harness, sweep script or tuning record anywhere in the tree: `tools/` contains
  only `build_replay_viewer.sh`, `ci/`, `gen_manifest.py`, `gen_wire_constants.nim`, `record_fixtures.nim` and
  `wasm_replay_smoke.cjs`; `scripts/art/` contains only `author_map.py`, `build_art.py`, `gen_unit_table.py`;
  neither `AGENTS.md` nor `docs/` mentions tuning. What the tree *does* carry is the ordering property the
  harness would exist to establish: `test_baselines.nim:63-73` asserts warden beats moth at seed 42 on both
  `team_hidden_frac` and `scores`. I cannot show the clause is falsified — tuning may have happened outside
  the repo — so I am not filing it as blocking. **What would settle it:** a committed harness (or its output
  table) under `tools/`, or a line in `log.md`/`AGENTS.md` naming the sweep and the parameters it chose.

- **Whether F1 is reachable in a hosted episode.** It needs a provider response (401/403/429/non-2xx) or a
  `max_tokens`-truncated model reply whose non-ASCII codepoint straddles byte 400/300/160. I have no way to
  produce a real Bedrock/Anthropic error body from the sandbox, and the CI smoke runs with no credentials at
  all (`no ANTHROPIC_API_KEY: the game must complete on its scripted baselines`), so the LLM path never
  executed in run 32610126558. **What would settle it:** a unit test over `textOf` with a non-ASCII body, or a
  phase-60 episode whose replay is checked with `validateUtf8` after a real fallback was recorded.

- **Whether the 8 px line-of-sight quantisation (F7) ever disagrees visibly with the note's pixel-exact
  intent.** `test_vision.nim:28-58` pins the range and cone at ±1 px / ±1 brad and the crate occlusion, but
  nothing probes a sightline that grazes a crate corner, where an 8 px cell either occludes a pixel-clear ray
  or vice versa. It is deterministic and identical in both builds, so it cannot break re-derivation.
  **What would settle it:** a test placing a crate so the ray passes within 4 px of its corner and asserting
  the expected lit/unlit outcome.

- **Whether the viewer's three-pass load (`rederive`, then the `hiders_left` series sim, then `rebuildWorld`)
  is comfortable at 5040 ticks in wasm.** `lantern_replay.nim:95,103-111,136` runs the full match three times
  on load. `test_perf.nim:25-39` bounds one native re-derivation at 30 s release, and the CI wasm smoke did
  1440 ticks fine, but no measurement exists for 5040 ticks under emscripten.
  **What would settle it:** running `tools/wasm_replay_smoke.cjs` against a 5040-tick fixture in the
  `wasm-viewer` job and printing the load time.
