# r1 review — gen-generals-io

Range: `c9d16f1..56e7b17` (the whole history; the repo was created this run)
Repo: `/tmp/cogame-gen-generals-io`, main at `56e7b170ee8039a84cecaf65447e2ee80cdf3d3e`
Starter: `/workspace/starters/coworld-ctf` (read-only mount)
Files read: 78 (every `src/generals/*.nim`, both entrypoints, all 4 viewer files,
`client/{chrome_common.js,broadcast_core.js,replay_broadcast.html,gen_block.html}`,
all 17 `tests/*.nim`, all 3 workflows, `tools/*`, the manifest, and the CI log of run 33145429852)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the parallel-batch rule)

Labels used below: **observed** = I read the line; **inferred** = I reasoned from lines I read;
**untested** = would need a run to settle.

---

## Blocking

### B1 — Replay playback opens 48 presentation ticks *before* `gameStart`, and no seek is clamped there
- Where: `src/generals/replay_runtime.nim:190-199` (`initReplaySession`), `:204-227` (`seekTo`),
  `:201-202` (`turnAt`), `:229-248` (`applyCommand`), `replay-viewer/gen_replay.nim:58-77`,
  `src/generals/broadcast.nim:121-123` (`t`/`st`)
- Observed, traced step by step:
  1. `initReplaySession` (`replay_runtime.nim:190-199`) sets `result.startTick =
     result.sim.config.startWaitTicks` (48 in **every** shipped variant and in the cert fixture —
     `coworld_manifest_template.json`, all four `game_config` blocks) and then
     `result.cursor = 0` (line 197). Playback therefore opens at presentation tick 0, i.e. 48 ticks
     before the game starts.
  2. `turnAt` (`:201-202`) is `clamp(cursor - startTick, 0, endTurn)`, so for `cursor` in `0..47` the
     sim is pinned at turn 0; `seekTo` (`:222-227`) sets `session.sim.phase = phLobby` for
     `target < startTick`. The board does not move and the locker-room curtain is up.
  3. `advance()` (`:256-272`) steps the cursor by `max(1, speed)` per frame, so the runtime walks
     through all 48 lobby ticks at presentation cadence rather than opening past them.
  4. `seekTo` clamps to `clamp(tick, 0, session.endTick)` (`:207`) — **not** to
     `[startTick, endTick]`. `applyCommand(',')` (`:235`) is `seekTo(0)`, and
     `client/replay_broadcast.html:1694` / `:1728` wire `#btn-restart` and the `,` key to `,`, so the
     restart control drops the viewer back into the lobby prefix every time.
  5. The scrubber axis disagrees: `broadcast.nim:121-123` emits `"t": context.tick` (the raw cursor)
     and `"st": context.startTick` (48), and `client/chrome_common.js:460-472` — byte-identical to
     the starter's — computes `frac = (s.t - st) / (mx - st)` and
     `#tick-clock = max(0, s.t - st) + ' / ' + span`. During the prefix the playhead sits at 0 %,
     `#tick-clock` reads `0 / 312`, and the momentum axis (`chrome_common.js:691-693`, whose comment
     is "the lobby prefix is flat/even and carries no signal, so dropping it just removes dead
     leading space") has already dropped the same 48 ticks.
  6. `gen_replay.nim:69` computes `lobbyCountdown = max(0, (startTick - cursor) div ReplayFps)`,
     i.e. the runtime deliberately renders a 4-second lobby countdown.
- CI evidence: run 33145429852, job `wasm-viewer`, step `Load the bundle in a real browser`:
  `soak: 10s of playback kept advancing ("0 / 312" -> "147 / 312" -> "195 / 312")`. The first sample
  is the clamped `0 / 312` readout, consistent with (but not by itself proof of) the cursor starting
  at 0; the code above is the proof.
- Checklist item: 13, third bullet — "**Playback opens at the game start, never the recorded lobby.**
  … The replay runtime must open playback at `gameStarts[0].tick` and clamp every seek there,
  matching the scrubber axis (`st`) that already skips the dead lobby."
- Why blocking: the runtime does neither of the two things the item names. Magnitude, stated
  honestly: the prefix is a fixed `startWaitTicks = 48` — 4.0 s at the nominal `ReplayFps = 12`,
  ~2.5 s at the rate the CI soak observed (195 ticks in 10 s). It is **not** the 63–270 frozen
  frames the scar describes, and the checklist's suggested probe (a replay with a large
  `lobbyJoinTimeoutTicks` and no joining seats) cannot make it worse here, because this replay
  format records no lobby at all: the prefix is a constant, not a recorded lobby length
  (`server.nim:74` sets `tick = startWaitTicks + turn`; the replay carries only hashes from turn 0).
  So the consequence is a short frozen open and a restart button that returns to it, not an
  indefinite hang.

### B2 — The worst-case renderer fixture never makes the page draw an LLM remark, and asserts nothing about its strings' length
- Where: `tools/ci/renderer_fixture.html:41-43` (the 160-char `NOTE`), `:72-75` (the note is placed
  only in `state.plan[]`), `:112-124` (`FRAMES` — the `events` arrays contain
  `citytaken`/`generalspotted`/`generalcaptured`/`eliminated`/`growth`/`stackclash` and **no**
  `{k:'plan'}`), `:148-175` (`transcribe`); `client/gen_block.html:394-399`
- Observed, traced step by step:
  1. In the shipped page the only code path that draws a plan `note` is
     `gen_block.html:394-399` — `case 'plan':` inside `event(e, s, ctx)`, which is driven from
     `s.events` via `applyEvent` (`client/replay_broadcast.html:1655-1662`).
  2. `client/gen_block.html` never reads `s.plan`: `frame()` (`:472-512`) reads `w/h/cells/ph/turn/
     turns/stand/alive/growthEvery/growthIn/beats`; `scorebug()` (`:409-448`) reads
     `stand/teams/roster/alive/out`; `endcard()` (`:520-588`) reads `over/stand/roster/out/outBy`.
     Grep for `s.plan` in that file returns nothing.
  3. The fixture puts its full-cap note in `state.plan[]` only (`renderer_fixture.html:72-75`) and
     never emits a `{k:'plan'}` event, so the page's remark path is not entered. The fixture's
     `transcribe()` selector list (`:153-156`) does include `.feed-row`, so any remark that *had*
     been drawn would be measured — none is.
  4. `transcribe()` paints `el.textContent` at the measured rect and returns `nodes.length`. It
     never compares a drawn string against the source string, so a silently shortened remark would
     leave it green.
- CI evidence: run 33145429852, step `Drive the shipped page with the worst-case renderer fixture`:
  `{"loaded":true,"ms":6868,"clock":null,"scorebug":null,"feed_lines":0}` and
  `canvas text: 27 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`.
  `feed_lines: 0` on the fixture is consistent with the trace above.
- Checklist item: 15, last bullet — "A repo whose viewer draws LLM-authored text must therefore ship
  a **worst-case renderer fixture**: a page that … drives it with a full-cap remark on *every* seat
  at once … The fixture asserts its own strings are still full-length — one quietly shortened remark
  leaves it passing while testing nothing."
- Why blocking: the fixture exists, loads the real page, sets `data-replay-loaded`, and is driven by
  `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step (`ci.yml:378-399`) — the "has no
  such fixture" clause of the item is satisfied. The two remaining clauses of the same bullet are
  not: the full-cap remark is never handed to the page along the path that draws it, and the fixture
  makes no assertion that its strings are still full-length. That is exactly the state the bullet
  describes as "passing while testing nothing". A judge that reads the bullet as satisfied by the
  fixture's mere presence would dismiss this; I am reporting it against the sentence as written.

---

## Non-blocking

### N1 — On a replay, a plan `note` cannot reach the feed at all
- Where: `src/generals/replays.nim:95-102` (`writePlanInput`), `src/generals/directives.nim:444-451`
  (`planJson`), `:453-467` (`planFromJson`), `src/generals/replay_runtime.nim:57-66`
  (`applyRecordedPlans`), `:82-83` (`planFeed`), `src/generals/server.nim:206-208`
- Observed: the load-bearing plan input record is `planJson(plan)` — `intent`, `target`, `reserve`,
  `cities`, `scouts`; **no `note`** (`directives.nim:444-451`). `planFromJson` likewise never reads
  `note`, so on playback `sim.plan[seat].note` stays `""` and `broadcast.nim:88-92`'s
  `state.plan[].note` is empty. The note *is* in the replay as a `plan` **chat** record
  (`server.nim:199-205`), and `initReplayPlayer` collects those into `player.planFeed`
  (`replay_runtime.nim:82-83`) — but `planFeed` is read by nothing (grep over `src/` and
  `replay-viewer/` returns only the declaration and the write). The `plan` *event* that the game
  block renders is emitted only by `server.nim:206` on the live path; `applyRecordedPlans` calls
  `sim.installPlan` (`sim.nim:39-52`), which records no event, and `stepTurn` resets `frameEvents`
  each turn (`sim.nim:114`).
- What the note says: §Viewer Readouts 6 — "The plan `note` appears here [`#killfeed`] and nowhere
  else; this is where a spectator sees the LLM playing"; §The state JSON a viewer reads — "`plan`
  carries the most recent plan per living seat and is where the feed's commander lines come from";
  §Out of scope — "the hosted spectator experience is the static replay bundle only".
- Consequence (inferred): in the hosted static viewer, an LLM's remark is never shown. The live
  `/global` path does show it. Not named by any checklist item, hence non-blocking here; it is the
  underlying cause of B2.

### N2 — The captain's threat override is dead code
- Where: `src/generals/captain.nim:242-247`, `:249-263`, `:464-465`
- Observed: step 2 sets `mission = MissionState(kind: mkDefend, source: -1, goal: view.generalCell,
  stepsLeft: config.defendTurns, active: true)` — with `source: -1`. Step 3's continue guard
  (`:249-250`) requires `mission.source >= 0`, so the override mission is never continued; control
  falls through to steps 4–6, which pick a mission from `plan.intent` unchanged, and line 464
  overwrites the mission wholesale (`mission = MissionState(kind: kind, source: step, …)`). On the
  no-move paths the mission is simply deactivated (`:451`, `:458`, `:462`). `mission.kind == mkDefend`
  is read nowhere else in the file.
- What the note says: §The captain step 2 — "discard the current mission and set `mission =
  Gather(goal = general)` with `stepsLeft = 6`. This override re-arms every turn the threat is
  visible and **cannot be switched off by a plan**"; the system prompt promises the same
  (`directives.nim:82-84`: "the captain comes home for six turns. You do not have to ask for that").
- Note: the *plan-level* defend does work — both baselines set `intent = defend` when threatened
  (`baselines.nim:31-33`, `:56-58`) and `tests/test_gen_baselines.nim:61-77` asserts it. No test
  covers the captain-level override.

### N3 — `heldRegistrations` is declared and initialised but never used
- Where: `src/generals/server.nim:40`, `:600`
- Observed: the field is `Table[int, string]`, initialised once, never written or read. The starter's
  equivalent (`/workspace/starters/coworld-ctf/src/ctf/server.nim:1730,1745,1791`) holds a
  registration from a socket with no slot yet and replays it once the slot lands.
- What the note says: §The four named edits to `server.nim` #2 — "The starter's 'hold an unappliable
  registration and re-read it when the slot lands' behaviour is kept verbatim (the paintball round-3
  scar)."
- Inferred mitigation: in this fork the slot is bound at websocket upgrade (`server.nim:445-448`), so
  a seat's registration always arrives with a known slot; and the player re-sends registration ten
  times (`gen_generals_io_player.nim:24`, `:121-126`). The scar's failure mode looks unreachable, but
  the field is dead.

### N4 — `engine.seats[].connected` is set once and never updated, so a mid-episode drop is not the
documented "plays sprawl, revives on reconnect"
- Where: `src/generals/server.nim:274-280` (the only `setSeatPolicy` calls), `:537-548` (`CloseEvent`
  clears `shared.registered[slot]` and the socket but touches no engine state),
  `src/generals/decide.nim:140-156`
- Observed: `connected` is computed once, before the loop, as
  `shared.playerSockets.hasKey(slot) or not isLlm`. `fcDisconnected` is therefore reachable only for
  an LLM seat whose socket was already gone at game start. `tests/test_gen_engine.nim:365-377` proves
  the *engine* honours the flag, by calling `setSeatPolicy` directly.
- What the note says: §End conditions — "A seat that drops mid-episode keeps playing on `sprawl` and
  revives on reconnect."
- No hang results: the decision layer does not depend on the seat socket at all.

### N5 — `ci.yml`'s "The manifest loads under the installed coworld CLI" step failed in the reviewed
run and is `continue-on-error: true`
- Where: `.github/workflows/ci.yml:162-176`
- Observed in CI: run 33145429852, job `test`:
  `ModuleNotFoundError: No module named 'coworld'` → `##[error]Process completed with exit code 1.`
  (annotation `test: .github#24`). `continue-on-error: true` (`ci.yml:176`) kept the job green.
- What the note says: §Tests 22 — "**`manifest loads under the installed CLI`** — a CI step runs the
  installed `coworld`'s own `validate_upload_manifest` / `_load_template_manifest`."
- Consequence: the platform validator has not actually seen this manifest. Checklist item 10's named
  properties (`game.docs` shape, both `game.protocols`) I verified directly from the file — see
  "Traced and consistent" — so item 10 is not falsified by this. Checklist item 1's "no test
  loosened" is verified from `git log -p -- tests/` and is clean (see below); this step is not in
  `tests/`.

### N6 — A crown capture updates neither `tilesTaken` nor `tilesLost`
- Where: `src/generals/resolve.nim:87-90` (early return into `captureGeneral`), `:10-45`, vs `:93-97`
- Observed: `applyMove` returns from the capture branch before the `tilesTaken.inc` /
  `tilesLost.inc` at `:93-95`, and `captureGeneral` records only `landInherited` / `armyInherited`.
  So the crown cell and the whole inherited estate are invisible to those two counters.
- What the note says: §Turn structure 3.f — "Ownership changes update `tilesTaken[s]` and
  `tilesLost[victim]`" — while the capture sub-order (3.e.1–4) mentions only `landInherited` /
  `armyInherited`. The note is ambiguous; the code is self-consistent and `gameHash` mixes both
  counters identically on both sides, so determinism is unaffected.

### N7 — `known_cities` and `fog.frontier` are ordered by Manhattan distance, not BFS distance
- Where: `src/generals/directives.nim:176-183` (cities), `:230-237` (frontier)
- Observed: both comparators use `abs(dx) + abs(dy)` from the crown / the largest stack.
- What the note says: §observation field rules — "`known_cities` at most 8, **nearest first by BFS
  distance**"; the frontier rule says only "nearest … first". With mountains on the board the two
  orders differ; both are deterministic, so the hash chain is unaffected.

### N8 — A remembered neutral city reports the config garrison, not its last-seen value
- Where: `src/generals/captain.nim:177-178` (`rememberedCityArmy` → `config.cityArmy` when not
  visible), `src/generals/vision.nim:34-38` (`Memory` stores `seenTurn`/`kindSeen`/`ownerSeen` only)
- What the note says: §The captain step 5 — "A remembered city's army is its last-seen value."
  The memory arrays carry no armies at all, so the last-seen value is not recoverable. The note's own
  observation contract also says a remembered cell's `army` is `null` — the two rules conflict in the
  note; the code follows the `null` rule and substitutes the constant.

### N9 — `sprawl`'s attack target is the lowest-index visible enemy cell, not the nearest
- Where: `src/generals/baselines.nim:40-49` — the loop takes `if best < 0: best = cell` on the first
  matching cell in ascending index and never compares distance.
- What the note says: §Scripted baselines — "`target` = the nearest visible enemy-owned cell when
  `intent == "attack"`". Deterministic either way; the captain re-targets to the nearest visible
  enemy when the plan target is unusable (`captain.nim:372-381`).

### N10 — Two of the four 360 px legibility rules are not implemented
- Where: `src/generals/global.nim:220-234`, `src/generals/rig_art.nim:17-18`, `:243-254`,
  `client/gen_block.html:440-447`
- Observed: numerals are pre-baked 9 × 14 px digit sprites (`DigitH = 14`, width `DigitH div 2 + 2`)
  placed at `startX = px + (CellPx - len*digitW) div 2`, `y = py + CellPx - digitH - 2` — always
  inside the 40 px cell, never at a negative coordinate. Drawn for **every** cell with
  `army > 0 and kind != ckMountain and army <= 9999` (`global.nim:222`). There is no `.tiny`
  condition anywhere in `src/` (grep for `tiny` in `src/generals/*.nim` returns nothing), and no
  per-cell horizontal scaling: the whole board layer is scaled uniformly by the client transform.
- What the note says: §Legible at 360 px rule 1 ("horizontally scaled to fit `cellPx - 2` with a
  floor of 0.55×") and rule 2 ("Under `.tiny`, a numeral is drawn only on cells with `army >= 5` and
  on every city and crown"). Rules 3 and 4 **are** implemented (`gen_block.html:428-430`, `:440-447`
  for `#stacktop`; `:18` and `:44-46` for `.plate-name` / the 640 px label rule).
  A cell holding ≥ 10 000 armies draws no numeral, and `#stacktop` (rule 3's stated fallback) carries
  only per-seat army totals and only under `.tiny`, without the note's "biggest stack R 96 at (1,1)"
  clause.
- `tests/test_gen_viewer.nim:133-139` ("the four 360 px rules exist") checks `.plate-name`, the
  640 px media query, and two comment strings in `global.nim`; it does not check rules 1 or 2.

### N11 — The 4096 reply cap is applied in runes, not bytes
- Where: `src/generals/directives.nim:296-298` — `if body.len > MaxReplyBytes: body =
  truncateRunes(body, MaxReplyBytes)`; `truncateRunes` (`sim_types.nim:160-168`) compares `runeLen`.
- What the note says: §Reply schema — "whole reply | **bytes** | ≤ 4096 read from the provider before
  parsing". A multi-byte reply can survive at up to 4× the byte cap. The truncation is still
  rune-safe, which is what checklist item 9 asks for.

### N12 — The general's placement formula differs from the note's expression (the range matches)
- Where: `src/generals/board.nim:186-187` — `gx = 1 + rng.rand(max(1, qw - 2))`,
  `gy = 1 + rng.rand(max(1, qh - 2))`
- What the note says: §The board step 2 — "`gx = 1 + mapRng.rand(qw - 3)`, `gy = 1 +
  mapRng.rand(qh - 3)` (on 8 × 5: `gx ∈ 1..6`, `gy ∈ 1..3`, never on a board edge)". The note's
  formula yields `1..5` / `1..2`; the code yields the note's parenthetical `1..6` / `1..3`. The
  invariant the note actually asserts (off the edge, mirrored) holds and is tested
  (`tests/test_gen_board.nim:36-56`).

### N13 — Board-generator tests sweep fewer seeds than the note claims
- Where: `tests/test_gen_board.nim:9` (2000 seeds, symmetry), `:23` (400, counts), `:38` (500,
  generals), `:59` (2000, connectivity)
- What the note says: §Tests 1 — "for **10 000 seeds** and both board sizes".

### N14 — The determinism test compares final state, not the per-turn stream
- Where: `tests/test_gen_determinism.nim:142-158` — two full episodes are run, then only
  `first.turn`, `first.gameHash()`, `first.board.army` and `generalsResultsJson` are compared;
  `hashesA`/`hashesB` each receive one element, and `for turn in 0 ..< 1: discard` is a no-op.
- What the note says: §Tests 5 — "two runs from the same seed and the same plans produce
  byte-identical **state streams**". The frame-by-frame property is covered elsewhere, by
  `tests/test_gen_replay.nim:81-99` (every recorded hash re-derived), which is what checklist item 2
  needs.

### N15 — One assertion in the reply-cap test is a tautology
- Where: `tests/test_gen_directives.nim:93-97` — `check (ok or not ok)` after the 9 KB reply. The
  useful assertion on the same case (`check extractJsonObject(text).len <= MaxReplyBytes`, line 95)
  is real.
- What the note says: §Tests 14 — "a 9 KB reply (capped at 4096 **then parsed**)". Whether the
  truncated body still parses is not asserted.

### N16 — The rotated-priority test asserts a different index than the note's sentence
- Where: `tests/test_gen_resolve.nim:163-186` — the test is titled "the winner of a contested cell on
  turn t is seat t mod 4" but asserts `sim.board.ownerOf(target) == (turn + 2) mod Seats`, with a
  comment deriving why (four equal 2-army pushes: 1st takes it, 2nd strips it to 0 without flipping,
  3rd takes it, 4th strips it again).
- Observed: the derivation is correct for that setup given `resolve.nim:105-110`, and the assertion
  does track the turn number, so rotation is demonstrated. The note's literal claim (§Tests 2,
  "the winner on turn `t` is seat `t mod 4`") is not the assertion made.

### N17 — `tools/ci/baseline_tuning.json`'s `"picked"` is the shipped default, not the sweep's argmax
- Where: `tools/tune_baselines.nim:88-104` — `--write` writes `DefaultTuning`'s three fields verbatim
  as `"picked"` and the 36-row grid alongside; `:106-118` — `--check` verifies only that the shipped
  defaults equal the recorded pick and that `shippedMargin > 0`.
- Observed in the data: the pick (4 / 20 / 2) scores margin `0.0417`. Under the stated shape
  constraint (`crownReserve > 0` and `crownScouts > 1`) the best row is 3 / 10 / 3 at `0.0625`;
  the unconstrained best is 3 / 0 / 3 at `0.1042`. 19 of the 36 rows have margin ≤ 0.
- What the note says: §Tests 13 — "the pick from `tools/tune_baselines.nim`'s head-to-head sweep".
  The builder's documented deviation (2) states the objective as "sprawl ahead, crown keeps
  documented shape", which the pick does satisfy; it is not the argmax under that objective. The
  harness is a real 36-point grid over 8 seeds × 4 rotations (`:19`, `:47-57`, `:77-86`), so
  checklist item 7's "tuned with a grid harness, not guessed" holds.

### N18 — `replay-viewer/config.nims` adds one line beyond identifier renames
- Where: `replay-viewer/config.nims:47` — `--preload-file {rootDir / "client" / "art"}@art`, absent
  from the starter's file. Everything else in the diff against
  `/workspace/starters/coworld-ctf/replay-viewer/config.nims` is `ctf_`→`gen_` renames.
- What the note says: §Kept, by path — "`replay-viewer/config.nims`, `static_replay.js`,
  `static_replay_worker.js` | **fork: identifiers and the output name only**". The added preload is
  required by `rig_art.nim`'s wall textures under emscripten (inferred).

### N19 — The page requests four assets the repo does not ship
- Where: `client/replay_broadcast.html:1158-1159` — `COG_ART_GUN[team].src = COG_BASE +
  '/soldier_' + team + '_front_gun.png'`, used by `cogArtFor` (`:1164-1169`). No
  `soldier_*_front_gun.png` exists in `data/` and none is copied by `Dockerfile.replay-viewer:70-79`.
- Consequence (inferred): four 404s per viewer load, swallowed by `cogArtReady`. This is inherited
  starter code the cut list in `tools/build_broadcast_page.py` does not touch.

### N20 — The forbidden-vocabulary list is narrower than the note's in two places
- Where: `tests/test_gen_endcard_labels.nim:65-67` — the list uses `flagicon` (not `flag`) and
  `kills` / ` killed` (not `kill`), and adds `Tags`, `Hill time`, `Cog`.
- What the note says: §Endcard and chrome label re-mapping — the list is "`Lives`, `LIVES`, `Clstr`,
  `flag`, `heart`, `paint`, `hopper`, `hill`, `POV`, `spray`, `grenade`, `med kit`, `kill`".
- Observed reason: the bare words survive as inherited identifiers, not as spectator text —
  `@keyframes flagflip`, `.feed-row.flagkill` and `#killfeed` in the page (the note's "Kept" list
  keeps `#killfeed`), and `flags:`/`defineLayer(..., flags)` in `broadcast_core.js`. The game block
  reuses the paintbot class `flagkill` for its `generalspotted` feed row
  (`client/gen_block.html:358`). Every re-mapped string the note enumerates is asserted present
  exactly once (`test_gen_endcard_labels.nim:72-87`).

### N21 — The replay's config JSON omits `tokens` and `slots`
- Where: `src/generals/sim_config.nim:197-233` — "TOKENS EXCLUDED"; no `slots` key either.
- What the note says: §Replay bytes, the content table — "config JSON | … `players[].name` (**real**
  names), `slots[]`, `tokens[]`, `fastMode`, `fullyObservable: false`". Excluding them is the safer
  choice and `replay_runtime.simFromReplay` clears tokens anyway (`:42`).

### N22 — Seed randomisation happens after `config.update`, not before
- Where: `src/gen_generals_io.nim:80-87` — `config.update(...)` then `if not
  seedPinned(runtimeConfig.config): config.seed = randomSeed()`; the module docstring (`:41-44`)
  claims the opposite ordering.
- What the note says: §Sim module — "`src/ctf.nim` → `src/gen_generals_io.nim` | fork | the
  entrypoint, **including seed randomisation before `config.update`**".
- Effect is equivalent (observed): the board is generated in `initSim` (`sim_state.nim:104`), which
  runs inside `runGameServer` after the seed is final, so every seed-derived draw follows the final
  seed.

### N23 — The system prompt hard-codes the `ffa` clock
- Where: `src/generals/directives.nim:43-44` ("every 25 turns"), `:57` ("turn 240").
  `systemPromptFor` (`:89-90`) substitutes only the board dimensions.
- Consequence: on the `blitz` (160 turns / growth 15) and `citadels` (growth 30) variants the prompt
  misstates the clock and the growth beat. The observation JSON carries the correct
  `of` / `growth_every` per turn (`:251-257`).

### N24 — Speed chip `0.5` is genuinely unavailable (documented deviation 6 verified)
- Where: `src/generals/sim_types.nim:29` — `PlaybackSpeeds* = [1, 2, 4, 8]`;
  `client/chrome_common.js:437` — `var map = { 1: '1', 2: '2', 3: '3', 4: '4', 8: '8', 16: '6' }`
- Observed: a `0.5` entry would render a chip that sends no command, because the byte-identical
  chrome has no key for it. The note's §Transport rules asks for `[0.5, 1, 2, 4, 8]`. The deviation's
  stated justification checks out.

### N25 — The player container's receive loop is a blocking read with no timeout
- Where: `src/gen_generals_io_player.nim:86-88` — `socket.receiveMessage()` inside
  `while running:`, wrapped in `try/except CatchableError`, with a redial cap of 6 (`:97-98`).
- Observed: bounded by the game pod, which always closes: the game loop's own wall-clock stop
  (`server.nim:287-291`), `broadcastDone` (`:134-149`, 3 s per socket budget) and `quit(0)` after a
  20 s grace (`:330-331`). Every other wait in the player is bounded (dial 240 × 500 ms `:22-23`,
  registration re-sends 10 × ~1 s `:24-25`). This is the starter's shape; I record it because
  checklist item 5 names "no … blocking read", and this one is bounded only indirectly.

---

## Traced and consistent

**Checklist 1 — CI green, no test loosened.** `gh run list -R Metta-AI/cogame-gen-generals-io --branch
main -w ci.yml`: run **33145429852**, conclusion **success**, head_sha
`56e7b170ee8039a84cecaf65447e2ee80cdf3d3e` (= the reviewed sha), jobs `test` ✓ / `docker-smoke` ✓ /
`wasm-viewer` ✓. `git log -p -- tests/` shows exactly two commits touching `tests/`: `929e58e`
(19 files, all additions) and `9509f0c`, whose entire test diff is a **+12-line added test** ("the
page and the shell agree on the adapter's name"). No deleted assertion, no widened tolerance, no
`skip`/`xfail` added by a later commit, no test file removed. (`tests/test_gen_viewer.nim:209-212`
contains a conditional `skip()` for the wasm harness when no bundle is staged; it was present in the
initial commit, and `ci.yml:318-326` runs the same gate directly in `wasm-viewer`.)

**Checklist 2 — replay re-derivation.** `tests/test_gen_replay.nim:81-113`: for `conquest`,
`full_time`, `wall_clock` (stop turn included) and `sim_fault`, an episode is recorded and
`initReplaySession(...)` + `seekTo(endTick)` walks every turn through `stepReplay`
(`replay_runtime.nim:150-162`), which compares `player.data.hashAt(sim.turn)` against
`sim.gameHash()` **each turn** and asserts `hashMismatchTick == -1`. The viewer renders from that
same `session.sim` (`replay-viewer/gen_replay.nim:79-83` → `buildStateJson(session.sim, …)` +
`buildViewerPacket(session.sim, …)`), not from a parallel recording. `gameHash`
(`sim_state.nim:171-203`) mixes turn, per cell `(kind, owner, army)`, twelve per-seat counters, the
per-seat fog memory digest and each seat's structured plan, and excludes note/source/latency/labels —
exactly the note's §Determinism 4 list. The native↔wasm gate runs the *emitted* module
(`ci.yml:318-326`, `tools/wasm_replay_smoke.cjs`) and passed in the reviewed run.

**Checklist 3 — static viewer.** `coworld_manifest_template.json` → `game.replay_viewer =
{"bundle": "static-replay-viewer"}` under `game`; no top-level `replay_viewer`.
`tools/build_replay_viewer.sh` exists, is committed `100755` (`git ls-files -s`), carries the ecos
`mkdir -p "$(dirname …)"` fix (line 20) and the buildx / `--platform linux/amd64` handling
(lines 42-55), and is invoked by path in `ci.yml:279` and asserted executable at `ci.yml:255-266`.
The only network call in the shipped shell is `fetch(message.replayUrl)`
(`replay-viewer/static_replay_worker.js:113`); everything else is same-origin bundle assets. No
`/client/replay` path is declared to the platform — the string appears only in the inlined protocol
docs, in `coworld-release.yml:211`'s own guard message ("a pod-served /client/replay viewer is not
acceptable"), and as the local developer route `server.nim:556`, which the note explicitly keeps.

**Checklist 4 — both name spaces.** `cogAlias` (`sim_types.nim:144-147`) yields exactly `RED-alpha` /
`BLUE-alpha` / `GREEN-alpha` / `YELLOW-alpha`; `pushSeatFrames` (`server.nim:115-132`) sends a seat
its alias and nothing else; the observation builder uses `cogAlias` throughout
(`directives.nim:151`, `:164`, `:191`, `:204`, `:249`). The spectator side carries real names:
`rosterJson` (`broadcast.nim:50-65`, `name`/`pol`) and `results.names` (`roster.nim:63`).
Asserted from both sides by `tests/test_gen_identity_privacy.nim:222-275` and
`tests/test_gen_observation.nim:153-180` with a sentinel policy address.
`showPlayerLabels: false` in all four `game_config` blocks.

**Checklist 5 — degrade-never-hang.** Every wait, with its bound:
connect wait `lobbyJoinTimeoutTicks / TargetFps` = 100 s, 200 ms poll (`server.nim:218-226`);
registration grace ≤ 3 s (`:228-237`); `turnSpacingMs` rate floor, a single `sleep` bounded by
9 000 ms (`decide.nim:163-167`); attempt-1 deadline 7 s and retry deadline 3 s handed to
`curly.makeRequests` as whole seconds (`decide.nim:212-237`, whole-second rule enforced by
`sim_config.nim:116-123`); outer monotonic `turnBudgetMs` 11 s checked before each attempt
(`decide.nim:201-211`); attempts capped at 2 (`:198`); rolling 60 s request cap 28 with no sleep
(`:104-116`, `:172-187`); budget guard reserve `2 × (9 + 11) = 40 s` (`:290-302`); engine stop at
`wallClockBudgetSeconds` checked at the top of every iteration (`server.nim:287-291`); post-artifact
grace 20 s then `quit(0)` (`:330-331`). `sim_config.validate` refuses
`wallClockBudgetSeconds * 10 > episodeTimeoutSeconds * 6` (`sim_config.nim:134-138`), i.e. the 60 %
rule, and every shipped variant is 660 (cert fixture 240). Worst case (inferred): 660 s stop + up to
one 20 s directive turn in flight + 20 s grace ≈ 700 s < 720 s. The game loop runs on its own thread
(`server.nim:607`) while mummy serves on the main thread, so an 11 s LLM stall cannot stall
`/healthz`. No unbounded loop: `runGame`'s `while not gameSim.done` is bounded by `maxTurns`
(`sim.nim:106-107`) and by the stop.

**Parallel batch (the "Additionally" rule).** `decide.nim:215-237` builds one `BatchRequest` per open
seat and issues them in a single `engine.runner(requests, …)` call, which
`defaultRunner` (`:56-77`) turns into one `client.curl.makeRequests(batch, …)`. No per-seat call site
exists. `tests/test_gen_engine.nim:200-216` records each call's in-flight window and asserts all four
intersect, and that `batches == 1`.

**Checklist 6 — `num_agents`.** `num_agents: 4` inside `game_config` of `ffa`, `blitz` and
`citadels` and inside `certification.game_config`; absent at every variant top level (verified by
parsing the manifest). `certification.players` has 4 entries and `certification.game_config.players`
has 4. `tools/ci/docker_smoke.sh` is the template with only the three documented substitutions
(`diff` against `templates/tools/ci/docker_smoke.sh` → 5 comment/default lines), so all four
`SEAT-COUNT` invariants are intact, and `ci.yml:210-215` passes `SMOKE_SLUG` with `SEATS` = 4.
**`grep SEAT-COUNT` over the full CI log of run 33145429852 returns nothing**; the docker-smoke log
reads `game=gen-generals-io seats=4 …` and `smoke OK: seats=4 results=792B replay=38000B
reason=complete`. `tests/test_gen_manifest.nim:18-29` asserts the same from the tree.

**Checklist 7 — scripted baseline plays full episodes legally.**
`tests/test_gen_baselines.nim:80-104` runs 4 seeds × 4 seat rotations of all-scripted episodes to the
natural end and asserts `sim.reason == "complete"` on each; `:106-134` runs the seed-42 cert fixture
to the end and asserts ≥ 1 `citytaken`, ≥ 1 `generalspotted`, ≥ 1 `growth`.
`tests/test_gen_captain.nim:40-95` asserts every emitted move is legal (owned source, `army >= 2`,
`1 ≤ amount ≤ army-1`, on board, not a known mountain) over 30 seeds × 120 turns and over 200 random
valid plans; `:97-119` asserts a dead seat gets no move and a boxed-in seat increments `passes`;
`:121-153` is the fog-blindness test (identical move against a garbled out-of-fog board).
`tests/test_gen_baselines.nim:24-59` asserts both baselines' plans stay inside the reply schema over
≥ 300 states. Tuning: `tools/tune_baselines.nim` grid (36 points × 8 seeds × 4 rotations), re-run
with `--check` at `ci.yml:156-157` (see N17 for the pick's exact status).

**Checklist 8 — LLM reply handling.** Tolerant parse: fence stripping, outermost balanced `{…}`,
first-brace..last-brace rescue (`directives.nim:292-325`); numeric strings, `{"x","y"}` targets,
enum case/separator folding, clamping, unknown keys ignored, note-only replies usable
(`:351-431`). Retry exactly once — `while open.len > 0 and attempt < 2` (`decide.nim:198`), with
`stillOpen.add(seat)` only when `attempt == 0` (`:252-253`, `:264-265`). `throttled` fails fast
without a retry (`:252`, `:275-285`). Second failure → `fallbackDecision`, whose plan is
`fallbackPlan(view)` = `sprawlPlan(view)` (`directives.nim:469-471`, asserted by
`test_gen_captain.nim:170-177`). Every fallback is recorded: `engine.fallbacks` →
`replayWriter.writeChat("fallback", …)` and `sim.record(seFallback, …)`
(`server.nim:209-212`), and `results.fallbackTurns[s]` counts them (`sim.nim:51-52`,
`roster.nim:81`). Covered by `tests/test_gen_engine.nim:231-307`.

**Checklist 9 — rune-safe truncation.** `truncateRunes` uses `runeLen`/`runeSubStr`
(`sim_types.nim:160-168`); `sanitizeNote` (`:173-187`) iterates `text.runes`. Every string reaching
the replay goes through one of them: `note` (`server.nim:202`, `:208`), `register.policy`
(`:260-261`), `fallback.detail` (`decide.nim:102`, `:128`), `results.stopDetail` (`roster.nim:114`),
`sim.stopDetail` (`server.nim:309`, `:314`), captured provider text (`llm.nim:170`, `:178`, `:184`,
`:193`), `PLAYER_PROMPT` (`llm.nim:202`, `server.nim:480`), `how_it_went` (`sim.nim:75`), player
names (`sim_state.nim:128`). `tests/test_gen_directives.nim:109-135` feeds a 4-byte emoji sitting on
the 160-rune cap and asserts `runeLen == 160`, `len == 163`, `validateUtf8() == -1`, and a JSON
round-trip; `tests/test_gen_replay.nim:184-212` runs `tools/replay_summary.py` over a replay whose
notes are filled with emoji and asserts strict-UTF-8 stdout and `protocol ==
"gen-generals-io/v1"`.

**Checklist 10 — manifest validates (structure).** `game.docs` = `{"readme": {"type":"text",
"value": …3884 chars}, "pages": [3 × {"id","title","content":{"type":"text","value": …}}]}` with ids
`rules.md` / `protocol.md` / `commanding.md`. `game.protocols` carries **both** `player` (2047 chars)
and `global` (2619 chars), each a `{"type":"text","value":…}` object. Also verified: `$schema`
present; 6 top-level tags; `episode_timeout_minutes: 20` at top level; no `game.tags`, no top-level
`version`, no top-level `replay_viewer`, no `game.display_name`; `config_schema`
`additionalProperties: false`, `required: ["tokens","players"]`, arrays `tokens` 4/4, `players` 4/4,
`slots` 0/4, `num_agents` `{integer, min 4, max 4, default 4}`; `results_schema` closed with exactly
the 29 keys of `roster.nim:116-122` and every one of the 21 seat-indexed arrays at
`minItems: maxItems: 4`; `reason` enum of 3, `endRule` enum of 5, `winner`
`{"type":["integer","null"],"minimum":0,"maximum":3}`; no literal `tokens` array in any
`game_config`; `game.name == "gen-generals-io" ==` the secret namespace in
`runnable.env.ANTHROPIC_API_KEY_URI`. `config_schema.properties` covers every key
`sim_config.update` reads, plus `slots` only. (See N5 for the CLI validator.)

**Checklist 11 — 360 px legibility.** `client/gen_block.html:18` —
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis;
white-space: nowrap; }`; `:44-46` — `@media (max-width: 640px) { .land-label { display: none; } }`;
`:83-85` — the fog chips drop their words at the same breakpoint. Asserted by
`tests/test_gen_viewer.nim:133-137`.

**Checklist 12 — release order and scaffold.** `coworld-release.yml`: `Build the Coworld manifest`
(`:159`, `coworld build` from `compose.yaml` in the same run) → `Certify locally` (`:173`,
`--timeout-seconds 300`, and it fails unless the certifier reports the **static** bundle, `:205-211`)
→ `Upload the policies` (`:216`, with the comment explaining why it precedes the next step) →
`Upload the Coworld` (`:314`) → `Put the Coworld secret` (`:410`). All three workflows present.
`tools/ci/docker_smoke.sh`, `tools/build_replay_viewer.sh` and `tools/ci/check_gameversion.sh` are all
mode `100755`. `tools/ci/policies.json` has four policies, one image, two `PLAYER_PROMPT` champions
and two `PLAYER_SCRIPTED` fillers, with champion #2 carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The placeholder gate
(`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files) **exits non-zero — no matches**; the
only surviving angle-bracket names are the four documented runtime ones (`<cow_id>`/`<sha>` in
`ci.yml:232`, `<run_id>` in `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` in
`coworld-submit.yml:31`).

**Checklist 13 — viewer executes** (other than B1). `wasm-viewer` is green on the reviewed sha, has
`needs: docker-smoke` (`ci.yml:242`), and its `Load the bundle in a real browser` step
(`ci.yml:339-368`) **ran**, is not commented out and carries no `continue-on-error`; it printed
`{"loaded":true,"ms":799,…}` and `soak: 10s of playback kept advancing ("0 / 312" -> "147 / 312" ->
"195 / 312")`. `data-replay-loaded="true"` is set on `<html>` in `static_replay.js:161`, in the
Worker's `'loaded'` branch, which the worker posts only after `ingestPacket()`
(`static_replay_worker.js:124-129`); `data-replay-error` is set in `showFailure()`
(`static_replay.js:8-20`). Both are the starter's own code paths, unchanged. Emscripten flags and
bootstrap are a matched pair from **one** starter: `config.nims` has no `MODULARIZE` and no
`EXPORT_NAME`, emits `gen_replay.js` non-modularized, and the Worker sets
`Module.onRuntimeInitialized` (`static_replay_worker.js:188`) and `importScripts('./wire_constants.js',
'./broadcast_core.js', './gen_replay.js')` (`:239`). Diffing all four viewer files against
`/workspace/starters/coworld-ctf/replay-viewer/` shows only `ctf_`→`gen_` renames plus the one line in
N18. `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`,
`-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and the ten `_gen_*` exports
are all present and match `gen_replay.nim`'s `exportc` names one-for-one.

**Checklist 14 — chrome provenance.**
`client/chrome_common.js` is **byte-identical** to the starter's:
`sha256 7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` on both files (also pinned
as a literal in `tests/test_gen_viewer.nim:29-31`). `client/broadcast_core.js` differs from the
starter's by **exactly one line** — `diff` output is a single hunk at line 49,
`window.CTF_WIRE` → `window.GEN_WIRE` (documented deviation 4 verified). The `CTF_WIRE` name survives
only where the note allows: `src/generals/wire_constants.nim:36-37` emits `window.GEN_WIRE={…};` then
`window.CTF_WIRE=window.GEN_WIRE;`, and `Dockerfile.replay-viewer:59-60` asserts **both** lines.
`client/replay_broadcast.html` is provably derived from the starter's page: re-running
`python3 tools/build_broadcast_page.py /workspace/starters/coworld-ctf/client/replay_broadcast.html
client/gen_block.html /tmp/regen.html` reproduces the committed file **byte for byte**. I enumerated
every top-level CSS rule in both pages: 248 in the starter, 181 here; every removed rule belongs to a
group the note enumerates (`#viewpanel`/`#minimap`/`#zoombar`/`#zoom-*`, `#povBadge`, `#fpv*`,
`.squad*`, `.flagicon`, `.hillchip`/`.hcap`/`.pb-tags`/`.pb-sub`/`#pb-regime`, `.ec-heart*`, the perk
and handicap badges, and the nine `.beat-marker` kinds this game never emits) or to the removed
paintball block itself; nothing in sections 1–5 is otherwise modified. `.lives-num` / `.lives-label`
are **renamed** to `.land-num` / `.land-label` rather than dropped, so the plate CSS survives — the
note lists them in both its removal list and its re-mapping table, and the generator followed the
latter. The page is 2 627 lines vs the starter's 4 660 (56 %), and the deletions account for it.
Transport rules: (a) `relayout()` (`:1958-2003`) measures `#transport` and `#scorebug` and sets
`--band`, `--topband` and `--hudscale` on `document.documentElement`, with `--u` defined on `:root`
(`:42`); (b) the game block's only positioned element is `#genband`, anchored
`top: var(--topband, 0px)` (`gen_block.html:49-62`) — `bottom: var(--band` appears nowhere in the
block; (c) `#endcard { … bottom: var(--band, 0px) }` (`:586-597`), shown via `#endcard.on`
(`:608`, `:1683`) and removed on every non-gameover frame (`:1529`), so any seek pulls it down;
(d) beats are `<button class="beat-marker <kind> <side>">` with `title` + `aria-label` that
`CTX.send('s:' + tick)` on click (`gen_block.html:309-330`), and CSS exists for exactly the four
kinds `genBeat` is ever called with — `citytaken`, `generalspotted`, `generalcaptured`, `end`
(`:116-119` vs `:354`, `:359`, `:368`, `:401`, `:465-468`), asserted set-equal by
`tests/test_gen_viewer.nim:84-99`. `#viewpanel` and the minimap are **removed**, not hidden
(markup, CSS, the `attachMinimap` call and the ids), which the note justifies with a fixed
16 × 10 board.

**Checklist 15 — drawn strings** (other than B2). `--strict-text-bounds` is present on **both**
smoke invocations (`ci.yml:363-368`, `:394-399`). The fixture step reported
`canvas text: 27 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`. The main
step reported `canvas text: 0 drawn, 0 never inside` — `total: 0`, which the checklist itself says
"means the check covered nothing … and is not evidence of anything"; the cause is observable in the
tree: the board renders as sprite objects through an OffscreenCanvas Worker
(`static_replay.js:89`, `static_replay_worker.js`) and every army numeral is a pre-baked digit
**image**, not `fillText` (`global.nim:220-234`, `rig_art.nim:243-254`). Text placement itself is
sound: digits are centred with `startX = px + (CellPx - len*digitW) div 2` and
`y = py + CellPx - digitH - 2`, both inside the 40 px cell for `len ≤ 4` (`digitW = 9`), so no draw
can land at a negative coordinate.

**Resolution rules, the note's 8 numbered steps** (`src/generals/sim.nim:109-122`,
`src/generals/resolve.nim`): step 1 directive install is the caller's (`server.nim:292-305`) and
writes the structured plan as an input record before the turn is stepped (`:198`); step 2
`compileMoves` runs the captain per living seat from `sim.viewOf(seat)` only (`sim.nim:77-95`);
step 3 rotated priority `order[k] = (turn + k) mod 4` (`resolve.nim:117-121`), with 3a discarding a
move whose source is unowned / has `army < 2` / is off-board / targets a mountain / belongs to a dead
seat, each incrementing `invalidMoves` once (`:49-68`); 3b `clamp(move.amount, 1, army-1)` and
`army(from) -= amount` (`:71-72`); 3c friendly add (`:76-80`); 3d `amount > d` flips with
`amount - d`, `amount <= d` leaves `d - amount` with the owner unchanged and fires `stackclash` when
`min(amount, d) >= 10` (`:84-110`); 3e the crown-capture sub-order exactly as written — every
non-crown victim cell to the attacker at `army div 2` (a 1-army tile becomes 0 and stays owned), the
crown becomes an owned `city` with `amount - d`, `alive/eliminatedTurn/eliminatedBy/
generalsCaptured` set and the victim zeroed, then `generalcaptured` + `eliminated`
(`:10-45`); chain captures fall out of the sequential application and are tested
(`tests/test_gen_resolve.nim:234-262`). Step 4 per-turn growth on **owned** cities and generals only,
ascending index (`:123-129`); step 5 periodic growth on every owned cell when
`turn > 0 and turn mod growthPeriod == 0`, with the `growth` event (`:131-145`); step 6 vision =
owned ∪ 8-neighbours (`vision.nim:48-56`), memory update and `generalspotted` once per ordered pair
(`resolve.nim:147-163`); step 7 `checkGeneralsInvariants` implements all eleven invariants the note
lists, including `visible ⊆ seen` and the four-fold mountain symmetry (`sim_state.nim:207-262`);
step 8 `writeHash` + the end check (`server.nim:318`, `sim.nim:97-107`). One ordering detail worth
recording: `sim.turn.inc` sits between steps 4 and 5 (`sim.nim:118`), so resolution and per-turn
growth use turn *t* and the growth beat fires when the counter reaches a multiple of `growthPeriod` —
nine beats in 240 turns, as the note says.

**Fog-of-war observation.** Three states implemented exactly: visible → exact `kind`/`owner`/`army`;
remembered → `kindSeen`/`ownerSeen` as of `seenTurn` with `army: null`; never-seen → `?` in all three
layers and no entry anywhere (`directives.nim:94-116`, `vision.nim:126-154`). `buildView`
(`vision.nim:101-112`) zeroes every out-of-fog cell so the captain literally cannot read the true
board. Caps: `armies` 40 largest with `armies_omitted`, `known_generals` 3, `known_cities` 8 with
`cities_omitted`, `fog.frontier` 8, `how_it_went` 240 runes. `standing` is public and identical for
all four seats. No floats anywhere in the object (asserted, `test_gen_observation.nim:140-151`).

**Scoring.** Ladder alive → outTurn → land → army → cities, first difference decides
(`scoring.nim:22-39`); standard competition rank by counting strictly-better seats (`:41-60`);
`win = rank == 0`; `winner` is the unique rank-0 seat else `null` (`:62-70`, `roster.nim:90`);
`placePoint(r) = (S-1-r)/(S-1)` with a tie group taking the average over its block
(`roster.nim:16-29`) — kept in `roster.nim` so `scoring.nim` stays integer-only (documented deviation
3 verified; the CI grep at `test_gen_determinism.nim:127-140` covers `scoring.nim`).
`tests/test_gen_scoring.nim:15-53` asserts `sum(scores) == 2.0` over 5 000 randomised end states and
every tie shape, and that no score leaves `[0, 1]`. A `deadline` episode is scored by the same ladder
at the stop turn (`test_gen_endings.nim:63-79`).

**Replay writer, self-sufficiency.** `COWLDGEN` magic + format version + game name/version + the
resolved config JSON + the record stream (`replays.nim:16-117`); joins carry the real names
(`server.nim:587-588`), plan input records are load-bearing, the six chat kinds
(`register`/`plan`/`fallback`/`budget_guard`/`stop`/`result`) are all written, and one hash per tick
(`server.nim:282`, `:318`). `stop` is applied on both sides by the single proc
`sim.applyWallClockStop` (`sim_state.nim:264-272`, `server.nim:290`, `replay_runtime.nim:100`,
`:156`, `:217`). The config JSON carries the seed, board and every timing constant, so the board is
re-derived rather than stored. `tests/test_gen_replay.nim:115-166` asserts the bytes alone yield
names, aliases, policy kinds, config, seed, every plan and the result, and that the results key set
equals the manifest's both ways.

**Deviations the builder documented, verified as claimed:** (1) `tests/test_gen_baselines.nim:80-104`
is a mean-placement margin over 4 seeds × 4 rotations, not the note's per-seat ordering — see N17 for
the tuning-pick nuance; (2) objective string in `tools/ci/baseline_tuning.json` and
`tools/tune_baselines.nim:60-65`, `--check` at `ci.yml:156-157`; (3) `placePoint` in `roster.nim:16`;
(4) `broadcast_core.js` one-line diff, board drawn by `global.nim:175-238` through the starter's
generic sprite renderer, no new draw procs; (5) `tools/build_broadcast_page.py` reproduces the page
byte-for-byte from the starter's, deletions and re-mappings match the note's enumerations (see N20
for the one vocabulary narrowing); (6) `PlaybackSpeeds = [1,2,4,8]` forced by
`chrome_common.js:437` — see N24; (7) no `tests/shard_*.nim`; `ci.yml:115-150` runs every
`tests/*.nim` in debug and release; (8) `git diff --stat` against the starter shows no new binary
assets — `data/` and `client/art/` are the starter's files; (9) ten commits with a real author and
committer, `git log` clean.

**Design-note copy.** `docs/plans/2026-08-28-gen-generals-io-design.md` is byte-identical to
`runs/2026-08-28-gen-generals-io/design.md`.

---

## Could not determine

- **Whether `results.names` actually carries real policy names in a league episode.** `sim.names`
  comes from `config.players[].name` (`sim_state.nim:124-128`), i.e. from the injected
  `game_config`, and is never overwritten from the registration's `PLAYER_POLICY_LABEL` (which lands
  in `sim.policies` only, `server.nim:255-256`). In the docker-smoke episode the names were the
  fixture's `Red`/`Blue`/`Green`/`Yellow` (CI: `scorebug: 'Red LAND 30 107 army · 0 cities …'`).
  Whether the hosted runner substitutes policy names into `game_config.players[].name` is a platform
  behaviour I cannot read from this tree. **Would settle it:** one hosted episode's `results.json`,
  or the starter's own prod results document.
- **Whether the `.tiny` class is ever reached in the shipped bundle at 360 px** (N10's practical
  impact). `relayout()` toggles it at `boardW <= 620` and the fixture drives 360 px, but the fixture
  reports `scorebug: null`, so I could not confirm from the log which branch the plates took.
  **Would settle it:** the `viewer-smoke.png` artifact from run 33145429852 at the 360 px pass, or a
  fixture assertion on `#stage.tiny`.
- **The real-world duration of B1's lobby prefix in the hosted player.** The CI soak advanced 195
  ticks in 10 s (≈19.5 tick/s), implying ≈2.5 s; the nominal `ReplayFps` is 12, implying 4.0 s. The
  actual frame cadence of the shipped shell on softmax.com is untested here. **Would settle it:** a
  wall-clock measurement of the time from `data-replay-loaded` to the first frame with
  `#tick-clock > 0`.
- **Whether the `test` job ran `tests/test_gen_perf.nim` in debug as well as release.** `ci.yml`
  reads `NIM_TESTS_RELEASE_ONLY` from a repo variable I cannot see from the sandbox; the note
  (§Tests 6) says the perf test is release-only. The job was green either way.
