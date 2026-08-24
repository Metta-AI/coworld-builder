# r1 review — matrix-games

Repo: `Metta-AI/cogame-matrix-games` at `7b7d5866c6b5c8010624b60efa2b800230c621a4`
(verified: `git -C /tmp/cogame-matrix-games log --oneline -1` → `7b7d586 viewer worker: read the
load-built packet for meta instead of packetAt(0)`).
Design note: `/workspace/coworld-builder/runs/2026-08-24-matrix-games/design.md` (1104 lines).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Starters diffed: `/workspace/starters/coworld-ctf` (paintbot), `/workspace/starters/cogame-bullwhip`.
Files opened: 38 (all of `src/matrix_games/*.nim`, `src/matrix_games.nim`,
`src/matrix_games_player.nim`, all 8 test files, all 4 replay-viewer files, `client/*.js`,
`client/replay_broadcast.html`, `coworld_manifest_template.json`, both Dockerfiles,
`tools/build_replay_viewer.sh`, `tools/ci/{docker_smoke.sh,viewer_smoke.mjs,policies.json}`,
`.github/workflows/*.yml`, `compose.yaml`, `scripts/art/gen_matrix_art.py`).

Every finding below is marked **match**, **gap** or **unclear**, and every one cites `file:line`.
*Observed* = I read it. *Inferred* = I reasoned from code I read. *Untested* = would need a run.
No fixes are proposed.

**Counts: 43 match · 21 gap · 7 unclear (71 findings).**

---

## 1. Resolution rules — the ten numbered tick steps

### F1 — the ten steps run in the note's order with the note's constants — **match**
- Where: `src/matrix_games/sim.nim:60-159`
- Observed. Step 1 timers `sim.nim:62-66` (decrement-if-positive, equivalent to the note's
  `max(x-1,0)` at design.md:193-194); step 2 respawn on `refillAt == t` `sim.nim:69-73`
  (design.md:195); step 3 intent evaluation into a `micros[]` array built from the state at the
  start of the step `sim.nim:77-79` (design.md:196-198); step 4 movement in ascending slot order
  with the occupancy re-check `sim.nim:83-94` (design.md:199-202); step 5 pickup in ascending slot
  order `sim.nim:97-110` (design.md:203-205); step 6 beam fire in ascending slot order
  `sim.nim:115-147` (design.md:206-215); steps 7+8 in `resolve` `sim.nim:16-56` (design.md:216-231);
  step 9 leader detection `sim.nim:150-154` (design.md:232-234); step 10 record + tick increment
  `sim.nim:157-159` (design.md:235-236).
- Constants: `stepCooldownTicks = 3`, `beamRange = 4`, `freezeTicks = 12`, `beamResetCooldown = 25`,
  `beamMissCooldown = 6`, `tokenRespawnTicks = 45`, `tokenCap = 8`, `viewRadius = 7`,
  `ImmuneTicks = 12`, `beats = 12`, `ticksPerBeat = 50` — `src/matrix_games/sim_types.nim:44-54`,
  defaults wired at `src/matrix_games/sim_config.nim:39-61`. All match design.md:193-236 and the
  observation block at design.md:334-336.

### F2 — the payoff formula and its truncation direction — **match**
- Where: `src/matrix_games/matrices.nim:120-142`
- Observed. `rowSum = Σᵢ Σⱼ nᵢ·mⱼ·rowPay[i][j]`, then `(rowSum * 100) div (n * m)` at
  `matrices.nim:142`. Algebraically identical to design.md:220-221. Nim's `div` truncates toward
  zero, which the note pins at design.md:223. Guarded against `n <= 0 or m <= 0` at
  `matrices.nim:133-134` (unreachable given the endowment, but harmless).
- The cell hit is `(argmaxᵢ n, argmaxⱼ m)` with ties → lowest index: `sim.nim:36-37` calling
  `argmaxLowest` (`sim_types.nim:265-271`, strict `>` so ties keep the lowest index) — design.md:226.

### F3 — all seven matrices are the note's tables — **match**
- Where: `src/matrix_games/matrices.nim:49-86`
- Observed, entry by entry against the table at design.md:145-153: RWS
  `[[0,-3,3],[3,0,-3],[-3,3,0]]` `matrices.nim:56`; PD `[[3,0],[5,1]]`, `coopToken 0`
  `matrices.nim:60-61`; chicken `[[3,1],[4,0]]`, coop 0 `matrices.nim:64-65`; stag-hunt
  `[[4,0],[2,2]]`, coop 0 `matrices.nim:68-69`; BoS `rowPay [[3,0],[0,2]]`, `colPay [[2,0],[0,3]]`,
  `crossCampOnly` `matrices.nim:71-76`; pure-coordination identity `matrices.nim:79`;
  rationalizable `[[1,0,0],[0,2,0],[0,0,3]]` `matrices.nim:83`. Symmetric variants take
  `colPay = transpose(rowPay)` at `matrices.nim:46`. Token name lists match design.md:147-153.
  An unknown `matrix` raises rather than defaulting (`matrices.nim:86`).
- Best-response tables derived, ties → lowest index: `matrices.nim:88-101` (design.md:163-164).

### F4 — the reset (rule 8) — **match**
- Where: `src/matrix_games/sim.nim:50-56`
- Observed. Both participants: `inv[i] = 1` for every `i < k`, `freeze = freezeTicks`,
  `immune = ImmuneTicks (12, sim_types.nim:54)`, `beamCd = beamResetCooldown`, one `reset` event
  each. Exactly design.md:228-231.

### F5 — the bach-or-stravinsky row rule and same-camp no-contest — **match**
- Where: `src/matrix_games/sim.nim:22-26` and `sim.nim:141-145`
- Observed. `resolve` swaps shooter/target so the row-camp (blue, slots 0-3 via
  `rowCamp`, `sim_types.nim:179-180`) participant is always the row player regardless of who fired
  (design.md:217). Rule 6's same-camp branch emits `nocontest` with `why: "same_camp"` and sets
  `beamCd = beamMissCooldown` (design.md:212-214). The immune/frozen branch at `sim.nim:136-140`
  emits `why: "immune"` (design.md:210-211). Both branch orders match the note's list.

### F6 — the committed arena is the note's ASCII map — **match**
- Where: `src/matrix_games/arena_map.nim:15-31`
- Observed: the 14 rows are byte-identical to design.md:93-106. I verified the four claimed
  properties mechanically from the source file: 24×14, 216 free cells, mirror-symmetric
  left–right **and** top–bottom, and a single connected free component of 216 cells.
  `FreeCellCount* = 216` at `arena_map.nim:31`. `tests/test_sim.nim:11-38` asserts all four.

### F7 — spawner layout and zones — **match**
- Where: `src/matrix_games/sim_state.nim:76-106`, zone rectangles `sim_types.nim:63-78`
- Observed. Zone A `x∈[1,7] y∈[1,5]`, zone B `x∈[16,22] y∈[1,5]`, zone C (K=3 only)
  `x∈[8,15] y∈[8,12]`, mixed band `y∈[6,7]` with the `n`-th spawner carrying `n mod K`
  (`sim_state.nim:104-106`) — design.md:121-126. 16 per zone, 12 mixed
  (`sim_types.nim:77-78`). I counted the free cells in each rectangle from the map: A=28, B=28,
  C=34, mixed=36, so no draw is short. Every spawner starts with a token (`hasToken: true`,
  `sim_state.nim:100-106`). Seeded Fisher–Yates then a canonical `(y,x)` sort so `spawners[]`
  order is stable (`sim_state.nim:59-74`) — required for the replay's positional `tok` block.

### F8 — a `leadchange` event is emitted at tick 0 with every score still zero — **gap**
- Where: `src/matrix_games/sim_state.nim:121` (`result.lastLeader = -1`) and
  `src/matrix_games/sim.nim:150-154`
- Observed + inferred. `lastLeader` is initialised to `-1`; at tick 0 `leader()`
  (`sim_state.nim:231-235`) returns `0` because all `scoreCp` are 0 and ties go to the lowest slot,
  so `lead != sim.lastLeader` holds and a `leadchange` for seat 0 with `scoreCp: 0` is recorded at
  `t = 0`. The note (design.md:232-234) describes step 9 as emitting "when it differs from **last
  tick**", which has no meaning at tick 0.
- Downstream: `src/matrix_games/broadcast.nim:55-59` and `src/matrix_games/global.nim:155-160` turn
  every `leadchange` into a scrubber beat marker, so the timeline carries a "Lead change" button at
  tick 0 in every episode (`client/replay_broadcast.html:1985-1987`). Inferred, not run.

### F9 — `updateSight()` runs as an unnumbered step between rules 5 and 6 — **gap**
- Where: `src/matrix_games/sim.nim:112`, implementation `src/matrix_games/sim_state.nim:200-206`
- Observed. The note's tick has exactly ten steps (design.md:191-236) and none of them is a sight
  update; the per-observer memory that `buildObservation` reads (`sim.nim:254-263`) is refreshed
  here. Functionally this is bookkeeping, not a rule — it writes only `memX/memY/memTick` — but it
  is a step in the tick that the note does not describe.

### F10 — pathing takes a "least-bad sidestep" where the note says a cog waits — **gap**
- Where: `src/matrix_games/kernel.nim:109-122`
- Observed. `bfsStep` first looks for a free neighbour that strictly reduces the BFS distance
  (`kernel.nim:100-110`); if none exists it falls through to a second loop that takes the best free
  sidestep with `d <= sideBest` where `sideBest` starts at `here + 1` — i.e. it will step
  *sideways or backwards* rather than wait. design.md:181-182: "Pathing is a breadth-first search
  over free cells from the cog's cell, ties broken by the direction order N, E, S, W …
  **A cog that has no legal step waits.**" The code's comment (`kernel.nim:86-91`) states the
  reason (deadlock between two cogs) and names `tests/test_indices.nim` gate (a) as what forced it.
  The behaviour is deterministic; it is not what the note says.
- Related, same proc: the BFS also treats cells occupied by another cog as impassable
  (`kernel.nim:103`, `kernel.nim:117`), where the note says the search is "over free cells".

### F11 — `hunt` has a `sweepStep` fallback the note's intent table does not list — **gap**
- Where: `src/matrix_games/kernel.nim:222-236`, called from `kernel.nim:278`
- Observed. design.md:177 defines `hunt` as "path toward that cog's last known cell; fire the beam
  the first tick the target is in the ray and the beam is ready." The code adds a third branch:
  when `bfsStep` to the last known cell returns `-1`, the cog walks to the centre of the mixed band
  (`BoardW div 2, MixedY0`) and, once there, turns one quarter every four ticks. Deterministic and
  documented in the comment, but absent from the note.

### F12 — `gather`/`deny` target selection reads the full spawner list, not the seat's view — **unclear**
- Where: `src/matrix_games/kernel.nim:124-141` (`nearestTokenCell`) and `kernel.nim:156-175`
  (`denyTokenCell`)
- Observed: both iterate `sim.spawners` directly, with no `viewRadius` or line-of-sight filter.
  design.md:175 says `gather` paths to "the **nearest** cell holding a token of that type
  (Chebyshev distance from the seat's own observation…)". The kernel's own header
  (`kernel.nim:9-11`) states "The kernel is the game's executor, not a policy: it reads sim state
  directly", and design.md:535 lists the kernel as game-side. Whether "from the seat's own
  observation" names the distance metric or an information restriction is not settled by the note.
  Tie-breaks (lowest `y`, then lowest `x`) do match design.md:175-176.

### F13 — the three per-room indices — **match**
- Where: `src/matrix_games/indices.nim:42-105`
- Observed. Convention histogram `conventionCounts[cellRow][cellCol]` incremented per resolution
  (`indices.nim:46`) — design.md:259-260. Cooperation rate `Σ(n[coop]+m[coop]) / Σ(N+M)`
  (`indices.nim:47-50`, `indices.nim:60-63`), `null` when `coopToken < 0` — design.md:262-265.
  Exploitability `bestPureValue(avgOpp) − realised` in centipoints, `null` for seats with zero
  resolutions (`indices.nim:65-92`) — design.md:266-270. `pureValueAgainst`
  (`matrices.nim:144-157`) indexes `colPay[opp][own]` for the column side, which is correct given
  `colPay` is `[rowChoice][colChoice]`.

### F14 — exploitability picks the row/column side by majority — **unclear**
- Where: `src/matrix_games/indices.nim:74` (`let asRow = idx.rowSides[slot] * 2 >= count`)
- Observed. design.md:269 says the best pure value is computed "under the matrix that seat faced
  (row or column side)" without saying what happens to a seat that was the row player in some
  resolutions and the column player in others. The code resolves it by majority (ties → row).
  In `bach-or-stravinsky` a seat's side is fixed by camp so this never bites; in the six symmetric
  variants `rowPay`/`colPay` are transposes so the answer differs only through `avgOpp`. Not
  falsifiable against the note as written.

### F15 — the three end conditions and `results.reason` — **match**
- Where: `src/matrix_games/server.nim:207-227` and `server.nim:251-252`;
  `src/matrix_games/sim_types.nim:89`
- Observed. `complete`/`full_match` when the beat loop finishes (`server.nim:251-252`);
  `deadline`/`deadline` when `epochTime() - gameStart > deadline`, checked between beats only
  (`server.nim:221-227`); `forfeit`/`forfeit` with zero scores when no socket connected inside
  `playerConnectTimeoutSeconds`, and `results.json` + the replay are still written
  (`server.nim:207-216`). `LegalReasons = ["complete","deadline","forfeit"]`. Exactly
  design.md:274-286. No early-termination rule exists in the tick loop.

### F16 — scoring and `results.json` — **match**
- Where: `src/matrix_games/sim.nim:349-397`
- Observed. `scores[i] = scoreCp[i] / 100.0` (`sim.nim:349-351`), higher better;
  `win[i] = (scores[i] == max(scores))` (`sim.nim:371`); `meanPayoff` = `scores/interactions` or
  `0.0` (`sim.nim:373-375`); `exploitability` in points with `null` for zero-resolution seats
  (`sim.nim:389` → `indices.nim:86-92`); `coopRate` `null` for the four variants with none
  (`sim.nim:390`). Field-for-field the object at design.md:674-689, plus `perSeatInteractions`,
  `conventionCounts`, `tokens`, `beats`, `ticks`. `names` are policy names, `aliases` are the cog
  aliases (`sim.nim:367-368`) — the two name spaces of design.md:79-82.

### F17 — the observation carries `you.fixedType`, a seed-derived value — **gap**
- Where: `src/matrix_games/sim.nim:328`, source `src/matrix_games/sim_state.nim:139-141`
  (`cog.fixedType = (cfg.seed + slot) mod k`)
- Observed. The note's observation block (design.md:327-351) does not include `fixedType`, and
  design.md:365 lists "the RNG seed" among the hidden quantities. `fixedType` reveals
  `(seed + slot) mod K`. It exists because `scripted.nim:62` reads it for the `fixed-pick`
  baseline, which design.md:466 requires to run off `buildObservation` alone.
- Two other additions to the observation are consistent with the note: `legal.{tokens,targets}`
  (`sim.nim:343`), which design.md:396-398 requires, and a per-cog `eligible` flag
  (`sim.nim:267`).

### F18 — rule 4 turns a blocked cog anyway — **unclear**
- Where: `src/matrix_games/sim.nim:87-94`
- Observed. `sim.cogs[slot].facing = micro.dir` is assigned at `sim.nim:90` *before* the
  `isFloor && unoccupied` test at `sim.nim:91`, so a cog whose step is blocked still changes
  facing. design.md:199-202 reads "moves one cell if that cell is floor and currently unoccupied
  …; its facing becomes `dir`", which does not say whether the facing change is conditional on the
  move. Deterministic either way.

---

## 2. The decision path

### F19 — one parallel batch per beat, all open seats — **match**
- Where: `src/matrix_games/llm.nim:478-498`
- Observed. `runBatch` builds a single `RequestBatch` (`llm.nim:484-489`, one `batch.post` per open
  seat) and issues it with one `client.curl.makeRequests(batch, client.timeoutSeconds)`
  (`llm.nim:490`). No per-seat loop of single requests exists anywhere in the file.
  `decideAll` collects every open seat into `open` (`llm.nim:513-524`) and builds one
  `system[]`/`user[]` pair per attempt (`llm.nim:528-536`). `batchSizes`/`batchStarts`
  (`llm.nim:52-53`, `llm.nim:480`, `llm.nim:476`) exist purely so the test can prove it.
- Asserted by `tests/test_llm.nim:98-99` (`sizes == @[Seats]`, `client.batchSizes == @[Seats]`)
  and `tests/test_llm.nim:125` (scripted seats excluded).

### F20 — tolerant parse, exactly one retry, `counter` fallback — **match**
- Where: `src/matrix_games/llm.nim:330-341` (extract), `llm.nim:353-409` (validate),
  `llm.nim:525-563` (retry + fallback)
- Observed. `extractJsonObject` takes `text[find('{') .. rfind('}')]`, tolerating fences, a prose
  preamble and trailing prose (design.md:390). `parseOrder` validates `intent` against the five,
  `token` against this seat's `legal.tokens` (case-insensitive, integer index accepted,
  `llm.nim:369-392`), `target` against this seat's `legal.targets` (case-insensitive, eligible-only,
  `llm.nim:393-407`) — the same lists the user prompt enumerates (`llm.nim:303-313`), which is the
  escrow property at design.md:396-398. `for attempt in 0 .. 1` (`llm.nim:525`) is exactly two
  attempts; the retry appends `retryHint` (`llm.nim:534-535`, text at `llm.nim:316-326`, matching
  design.md:494-496). Anything still open afterwards gets
  `scriptedDecision(obs, skCounter, osFallback)` with the log line
  `matrix-games llm: seat N falling back to scripted intent` (`llm.nim:560-563`) — the exact string
  at design.md:498.

### F21 — the fallback is recorded on the `order` event — **match**
- Where: `src/matrix_games/sim.nim:201`, `sim.nim:205-206`, `src/matrix_games/events.nim:38-46`
- Observed. `installOrders` stores `decisions[slot].source` and emits `orderEvent(...)`, which
  writes `"source": $source` where `OrderSource` stringifies to `llm|retry|fallback|scripted`
  (`sim_types.nim:101-105`). design.md:499 and the event table at design.md:547.
  `tests/test_llm.nim:147` and `:167` assert `osFallback` and `osRetry` respectively.

### F22 — a 429 is retried inside the same beat — **unclear**
- Where: `src/matrix_games/llm.nim:449-451` and `llm.nim:545-549`
- Observed. `textOf` raises `llm throttled (429)` for a 429; in `decideAll` any reply with a
  non-empty `error` goes into `stillOpen` and is retried in attempt 2 of the *same* beat. The note
  is internally split: design.md:492-497 says a transport error or non-2xx is "retried **once** in
  the same beat", while design.md:501 says "429 is logged and that seat is retried in the next
  beat's batch". The code satisfies the first and, by falling back for this beat and reopening next
  beat, also the second — but it does *not* skip the same-beat retry.

### F23 — no test exercises 401/403 disabling the client — **gap**
- Where: `src/matrix_games/llm.nim:444-448` vs `tests/test_llm.nim:169-198`
- Observed. `client.disabled = true` on a 401/403 is set inside `textOf`, which is only reached on
  the real curl path (`llm.nim:494`); when `batchHook != nil`, `runBatch` returns the hook's replies
  at `llm.nim:482-483` and never calls `textOf`. The 403 case in the test is a pre-baked
  `BatchReply(error: "llm auth failed (403) …")` string (`test_llm.nim:176`), so the disable branch
  is not covered. design.md:500 pins the behaviour ("401/403 disables the client for the rest of the
  episode"). The behaviour itself is present in the code; only the test coverage is absent.
- The consumption side is present and correct: `decideAll` breaks out of the attempt loop on
  `client.disabled` (`llm.nim:526`) and the next beat routes every seat to `counter`
  (`llm.nim:518-520`).

### F24 — the no-credentials path — **match**
- Where: `src/matrix_games/llm.nim:113-116` and `llm.nim:518-523`
- Observed. With neither Bedrock env nor `ANTHROPIC_API_KEY`/`ANTHROPIC_API_KEY_URI`,
  `newLlmClient` sets `transport = ltNone; disabled = true` and logs
  `matrix-games llm: no LLM credentials; every seat plays 'counter'`; `decideAll` then produces a
  `counter` decision with `source = osFallback` for every LLM seat and never touches the network.
  design.md:437-438. `tests/test_llm.nim:200-209` asserts `batchSizes.len == 0`.
- Credential precedence Bedrock → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`:
  `llm.nim:94-116`, `llm.nim:62-74`. Haiku-only ladder, `BEDROCK_MODEL` override:
  `llm.nim:76-80` (design.md:433-434). No `output_config.effort` (`llm.nim:429-430`).
  `maxOutputTokens` default 900 (`sim_config.nim:56`).

### F25 — prompts carry what the note specifies — **match**
- Where: `src/matrix_games/llm.nim:149-210` (system), `llm.nim:217-314` (user)
- Observed. System prompt: alias and camp in capitals (`llm.nim:154-160`), the yard, the beat
  structure and all five intents (`llm.nim:161-179`), the beam (`llm.nim:181-183`),
  "YOUR STRATEGY IS YOUR INVENTORY MIX, NOT A DECLARATION" with the payoff formula
  (`llm.nim:185-191`), the labelled two-payoff matrix table (`llm.nim:132-147`, `llm.nim:193-194`),
  the reset rule (`llm.nim:195-196`), the scoring statement and the simultaneity/no-channel
  statement (`llm.nim:198-201`), and the output contract ending "must begin with the character {
  and end with }" (`llm.nim:203-205`) — design.md:401-415. User prompt: `BEAT n / N` header, the
  YOU row, the eight-row scoreboard, the zone table with live counts, the visible-token list, the
  full public resolution log, the indices line, `YOUR NOTES FROM LAST BEAT`, the operator block
  with the note's exact wording (`llm.nim:299-301`), and the enumerated legal tokens/targets
  (`llm.nim:309-313`) — design.md:418-430.

---

## 3. Every wait and its bound

### F26 — the LLM batch timeout is a real bound — **match**
- Where: `src/matrix_games/llm.nim:490`; curly `makeRequests(curl, batch, timeout = 60)` at
  `/root/.nimby/pkgs/curly/src/curly.nim:711-715`, `rw.timeout = timeout` at `curly.nim:739`,
  applied as libcurl `OPT_TIMEOUT` at `curly.nim:290` and as a watchdog at `curly.nim:413-427`.
- Observed. `client.timeoutSeconds` is `llmTimeoutSeconds` (default 20, `sim_config.nim:54`),
  passed in seconds. `makeRequests` blocks on a wait group until every request completes or times
  out; there is no unbounded read.

### F27 — the inter-batch pacing sleep is bounded by `minBeatSeconds` — **match**
- Where: `src/matrix_games/llm.nim:466-476`
- Observed. `wait = minBeatSeconds - (now - lastBatchStart)`, slept only when positive, so the
  sleep is at most `minBeatSeconds` (17 s, `sim_config.nim:55`). design.md:308-309.

### F28 — the episode worst case fits inside the 720 s deadline, and `validate()` enforces it — **match**
- Where: `src/matrix_games/sim_config.nim:66-70` and `sim_config.nim:92-99`
- Observed + inferred. `playDeadlineSeconds = 0.6 * episodeTimeoutSeconds` = 720 s at the default
  1200 (design.md:279, design.md:317-319). `validate()` raises unless
  `beats * 2 * llmTimeoutSeconds <= playDeadline`: 12 × 2 × 20 = 480 ≤ 720.
- Inferred bound on wall time, since pacing and timeout interact: at most 24 batches
  (12 beats × 2 attempts), each costing `max(minBeatSeconds, batchDuration) ≤ max(17, 20) = 20 s`,
  because `paceBatch` measures from the previous batch *start*. Worst case 480 s, matching the
  note's arithmetic at design.md:310-312. Untested at runtime.

### F29 — the play deadline is measured from before the 180 s connect wait — **gap**
- Where: `src/matrix_games/server.nim:162` (`let gameStart = epochTime()`) vs `server.nim:163-171`
  (the connect loop) and `server.nim:221` (`if epochTime() - gameStart > deadline`)
- Observed. `gameStart` is stamped at the top of `runGame`, before the up-to-180 s connect wait
  and the up-to-3 s registration wait, so the 720 s budget is spent on connect time too. The note's
  arithmetic (design.md:307-313) budgets 480 s of *play* against 720 s and does not account for the
  connect wait. Inferred worst case: 180 + 3 + 480 = 663 s ≤ 720 s, so the deadline still is not
  crossed at the defaults — but the headroom the note describes (240 s) is actually ~57 s.
  Untested at runtime.

### F30 — the other server-side waits are all explicitly bounded — **match**
- Where: `src/matrix_games/server.nim`
- Observed, each with its bound:
  - connect wait, `server.nim:163-171`, bounded by `playerConnectTimeoutSeconds` (180), polled at
    200 ms;
  - registration grace, `server.nim:173-182`, `min(now + 3.0, connectDeadline + 3.0)`;
  - `broadcastFinal`, `server.nim:118-123`, a cumulative 1 s allowance per seat, skipping seats
    once spent — a slow reader cannot hold the artifact writes (design.md:665-670);
  - `sleep(500)` before the artifacts, `server.nim:146`;
  - artifact POST, `server.nim:91`, `curl.post(uri, headers, data, 60)`;
  - shutdown grace `sleep(shutdownGraceSeconds * 1000)` then `quit(0)` on both the forfeit path
    (`server.nim:215-216`) and the normal path (`server.nim:263-264`) — design.md:506-507;
  - `pushStateFrames` (`server.nim:97-106`) sends and never waits for a reply, so the round barrier
    the checklist names does not exist as a wait at all;
  - the websocket handler never blocks: a bad token is refused with 403 before the upgrade
    (`server.nim:337-339`), a duplicate with 409 (`server.nim:340-342`).
- No `while true` without a deadline and no blocking read exist in the file.

### F31 — the player process has a bounded connect retry and a guarded receive loop — **match**
- Where: `src/matrix_games_player.nim:22-23`, `:61-73`, `:79-121`
- Observed. `ConnectAttempts = 5` with `ConnectBackoffMs * attempt` linear backoff (250/500/750/1000
  ms), then `quit(0)` — a no-show leaves quietly and the game plays the seat as `counter`
  (design.md:502-503). The receive loop wraps `socket.receiveMessage()` in
  `try/except CatchableError` and `break`s, and `quit(0)` is the only exit
  (`matrix_games_player.nim:87-94`, `:121`) — the raid learning at design.md:668-670. The prompt is
  re-sent after `welcome` (`matrix_games_player.nim:110`) — design.md:656-657.

### F32 — the game thread body has no exception guard — **unclear**
- Where: `src/matrix_games/server.nim:159-264` (`runGame`), started at `server.nim:471`
- Observed: no `try`/`except` wraps the beat loop. `decideAll` documents itself as never raising
  (`llm.nim:511`) and I found no `raise` on its path, but `installOrders`, `runBeat`,
  `buildObservation`, `resultsJson` and `replayBytes` are not guarded. If any of them raised, the
  thread would die while `gameServer.serve` keeps `/healthz` answering, with no artifacts written
  and no `quit`. Whether any of them can raise on the live path I could not determine from reading
  alone — the arithmetic is integer and the indices are bounded by `Seats`/`k`, so I have no
  concrete raising path to name. Untested.

---

## 4. String truncation

### F33 — `cleanText` is rune-safe and is applied at every recording site — **match**
- Where: `src/matrix_games/sim_types.nim:223-233`
- Observed. `cleanText` replaces `\r`/`\n` with spaces, runs `utf8Only`, strips, and — if
  `runeLen > limit` — returns `runeSubStr(0, limit - 1) & "…"`. Rune boundaries, never bytes.
  Exactly design.md:391-393.
- Applied at: `installOrders` for `say`/`notes` before anything downstream sees them
  (`sim.nim:198-199`, caps `MaxSayRunes = 64` / `MaxNotesRunes = 400`, `sim_types.nim:83-84`);
  `orderEvent` again on the way into the replay (`events.nim:43-44`); `parseOrder` on the model's
  own strings (`llm.nim:408-409`); and every captured HTTP error body at
  `MaxDetailRunes = 200` (`llm.nim:448`, `:451`, `:454`) and the `max_tokens` fragment at 160
  (`llm.nim:464`). design.md:113 of the checklist ("say, notes, prompts, captured errors").
- `utf8Only` (`sim_types.nim:206-221`) drops malformed bytes before anything is recorded.

### F34 — `extractJsonObject`'s error preamble is a byte cut, not a rune cut — **gap**
- Where: `src/matrix_games/llm.nim:336-340`
```
      var head = text.strip()
      if head.len > 160:
        head = head[0 ..< 160] & "..."
```
- Observed. `head.len` is bytes and `head[0 ..< 160]` is a byte slice, so a reply whose first 160
  bytes end mid-rune (any non-ASCII prose preamble, which is precisely the case this branch fires
  on) produces an invalid-UTF-8 error message. This is the one truncation in the tree that is not
  rune-based, and it is the same shape as the bullwhip bug the note cites at design.md:392-393.
- Scope, traced: the resulting `MatrixGamesError.msg` is only `echo`ed at `llm.nim:557`. I grepped
  the tree for any path recording an LLM error string into the replay or `results.json` and found
  none — the `order` event carries only `say`, `notes`, `intent`, `token`, `target`, `source`,
  `latencyMs` (`events.nim:38-46`). So the invalid bytes reach stdout, not the replay.
  The identical line exists in the starter it was forked from
  (`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:327`).

### F35 — prompt and policy-label truncation — **match**
- Where: `src/matrix_games/server.nim:392-393` and `server.nim:404-405`
- Observed. An incoming `prompt` longer than `MaxPromptRunes = 4000` is cut with
  `runeSubStr(0, MaxPromptRunes)` (rune-safe); the `policy` label goes through
  `cleanText(…, MaxPolicyLabelRunes = 48)`. The policy label is the one that reaches the replay
  (`gameSim.names[slot]`, `server.nim:198` → `replays.nim:48`) and it is rune-truncated.

### F36 — a test feeds multi-byte input at the cap — **match**
- Where: `tests/test_replay.nim:97-136`
- Observed. `repeat("\u4e2d", MaxSayRunes)` and `repeat("\u00e9\u4e2d", MaxNotesRunes)` are fed
  through `installOrders`, the replay bytes are re-read, and `validateUtf8(bytes) == -1`,
  `validateUtf8(say) == -1`, `say.runeLen <= MaxSayRunes` are asserted. A second test sweeps
  `cleanText` over limits 1..40. Checklist item 9's test clause is satisfied.

---

## 5. The replay writer

### F37 — the `matrix.replay.v1` layout is the one the note pins — **match**
- Where: `src/matrix_games/replays.nim:41-72`
- Observed, key by key against design.md:566-591: `protocol`, `game`, `gameVersion`, `variant`,
  `seed`, `names` (aliases), `policyNames`, `liveries`, `camps`, `config`, `map`, `spawners`,
  `frames`, `series`, `indices`, `events`, `results`. Nothing is missing and nothing extra is
  present.
- `frames[i]` is `{t, c, inv, tok, sc}` with `c` a flat `8 × (x,y,facing,freeze)`, `inv` a flat
  `8 × K`, `tok` one 0/1 per spawner in `spawners[]` order, `sc` eight cumulative centipoints —
  `src/matrix_games/sim_state.nim:276-288` and `replays.nim:20-25`. design.md:593-596.
- `series.share[t] = [t, permille…]` and `series.score[t] = [t, sc0..sc7]` —
  `sim_state.nim:290-307`. design.md:586-587, 597-599.
- `config` is the fully resolved config with the matrix inlined and connection tokens excluded
  (`sim_config.nim:158-195`) — design.md:573-578.

### F38 — self-sufficiency — **match**
- Where: `src/matrix_games/replays.nim:41-72`, consumed at `src/matrix_games/global.nim:317-344`
- Observed. Every field the viewer reads comes out of the replay: `viewerMeta` pulls `protocol`,
  `gameVersion`, `variant`, `seed`, `config`, `map`, `spawners`, `names`, `policyNames`, `liveries`,
  `camps`, `results`, `indices`, `events`, plus the three derived once-per-match payloads. The only
  network the bundle does is `fetch(message.replayUrl)` in the worker
  (`replay-viewer/static_replay_worker.js:132`) plus same-origin art
  (`static_replay_worker.js:87-90`). design.md:600-603.

### F39 — strict UTF-8 on read — **match**
- Where: `src/matrix_games/replays.nim:77-88`
- Observed. `parseReplayBytes` raises before `parseJson` if `validateUtf8(data) >= 0`, and rejects a
  wrong `protocol`. design.md:562. Asserted at `tests/test_replay.nim:20-25`.

### F40 — `conventionCounts` is recorded twice and never cross-checked — **unclear**
- Where: `src/matrix_games/replays.nim:67` (`state.idx.conventionJson()`, the sim's running
  accumulator) vs `src/matrix_games/global.nim:119-121` and `global.nim:273-278` (the viewer's
  re-derivation from the `interact` events)
- Observed. The viewer never reads `replay.indices.conventionCounts`; it recomputes the histogram
  from `cellRow`/`cellCol` on each `interact` event. Both are functions of the same resolutions and
  should agree, but nothing in `tests/` compares them. Same shape for `coopRate`
  (`indices.nim:60-63` vs `global.nim:297-300`) and for the `beats` timeline
  (`broadcast.nim:37-65` vs `global.nim:140-165`, two independent implementations of the same
  derivation; they differ on the terminal `over` row — `broadcast.nim:62-65` uses
  `sim.leader()` and its real `scoreCp`, `global.nim:163-165` uses the last `leadchange` seat and
  `cp: 0`). This is the closest thing in the tree to checklist item 2's "parallel recording"
  concern; it is a duplicated *derivation*, not a duplicated recording of state.

---

## 6. The viewer's re-derivation and the static bundle

### F41 — `config.nims` is the starter's, non-modularized — **match**
- Where: `replay-viewer/config.nims:42-54`
- Observed by diff against `/workspace/starters/coworld-ctf/replay-viewer/config.nims`: the only
  changes are three comment renames, the emitted name `matrix_games_replay.js`
  (`config.nims:45`), and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_mg_*` with
  `_ctf_mismatch_tick` dropped (`config.nims:53`). No `-s MODULARIZE=1`, no `-s EXPORT_NAME`.
  `-s ALLOW_MEMORY_GROWTH`, `-s ABORTING_MALLOC=1`, `-s FILESYSTEM=1`,
  `-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--define:useMalloc`,
  `--preload-file` all present. Exactly design.md:718.

### F42 — the worker bootstrap is the matched pair for those flags — **match**
- Where: `replay-viewer/static_replay_worker.js:10-18` (`var Module = {}`), `:201`
  (`Module.onRuntimeInitialized = function () {`), `:244`
  (`importScripts('./wire_constants.js', './broadcast_core.js', './matrix_games_replay.js')`)
- Observed. A non-`MODULARIZE` build patches a pre-declared `Module` and calls
  `onRuntimeInitialized`; that is what this worker waits for. No factory call anywhere in the
  file. This is the paintbot lineage on both sides — the cogame-lantern splice is not present.
  design.md:720. Asserted at `tests/test_viewer.nim:212-231`, and confirmed empirically by the
  CI viewer smoke reporting `loaded: true` (see F62).

### F43 — both readiness markers are set from the shell's own code — **match**
- Where: `replay-viewer/static_replay.js:145` (`data-replay-loaded`) and `:40`
  (`data-replay-error`)
- Observed. `data-replay-loaded="true"` is set in the `loaded` branch of `onWorkerMessage`, which
  fires on the worker's first built packet; `data-replay-error` is set inside `showFailure` before
  the `#status` line renders. The `coworld-replay` bridge's `ready` is posted from a double-rAF
  *after* `data-replay-loaded` is set (`static_replay.js:146-152`) — the chorus fix at
  design.md:729-731. Asserted at `tests/test_viewer.nim:247-256`.
- Bounded: a 20 s `FETCH_TIMEOUT_MS` watchdog fails the load rather than hanging
  (`static_replay.js:4`, `:181-186`).

### F44 — meta rides the first packet, and the worker reads that packet — **match**
- Where: `src/matrix_games/global.nim:346-358`, `replay-viewer/matrix_games_replay.nim:53-55`,
  `replay-viewer/static_replay_worker.js:138-162`
- Observed. `renderCurrent()` calls `viewerPacket(cursor, not firstPacketDone)` and then sets
  `firstPacketDone = true`, so `meta` is attached exactly once — to the packet built by
  `mg_load_replay`. The worker reads that packet with `currentPacket()` (`:143`) rather than
  `packetAt(0)`, which would call `mg_frame(0)` and rebuild it without `meta`; the comment at
  `:138-142` states this and it is the subject of the head commit. `meta.beats`, `meta.lulls`,
  `meta.lead` are what the page uses thereafter (`client/replay_broadcast.html:2109-2110`), and
  `chromeStateAt(t, false)` correctly ships them empty on every later frame
  (`global.nim:307-310`).

### F45 — the wasm entry is the starter's shape with the exports the note lists — **match**
- Where: `replay-viewer/matrix_games_replay.nim`
- Observed. Exports `mg_load_replay` (`:57`), `mg_frame` (`:101`), `mg_input` (`:90`),
  `mg_packet_ptr`/`_len` (`:116`, `:119`), `mg_error_ptr`/`_len` (`:122`, `:125`),
  `mg_stage_ptr`/`_len` (`:128`, `:134`) — the exact list at design.md:719, and the exact list in
  `config.nims:53`. `ctf_mismatch_tick` is dropped. The `stageNote` buffer + `stampStage` calls
  (`:37-46`, `:61,63,70,74,108`), the `ABORTING_MALLOC` rationale (`:29-36`), the capacity check
  (`:71-73`) and the `emscripten_exit_with_live_runtime()` epilogue (`:137-148`) are all present.
  Catches `Exception`, not just `CatchableError`, so a wasm Defect surfaces as a message (`:80-88`).

### F46 — the viewer derives its display from the recorded frames, not a parallel stream — **match**
- Where: `src/matrix_games/global.nim:62-82`, `:185-230`, `:232-252`, `:254-310`
- Observed. `initViewer` binds `view.frames = replay{"frames"}` and every per-tick readout comes out
  of that array by index: positions/facing/freeze from `frame{"c"}[slot*4 + …]`
  (`global.nim:222-225`), inventory from `frame{"inv"}[slot*k + i]` (`global.nim:196`), score from
  `frame{"sc"}[slot]` (`global.nim:227`), token presence from `frame{"tok"}[index]`
  (`global.nim:246`). Cumulative quantities (per-seat interactions, the convention histogram,
  coop mass) are folded forward from the recorded `events` in one pass and snapshotted per tick
  (`global.nim:103-135`). There is no second recording and no re-simulation — which is the
  architecture the note pins at design.md:562-564 and design.md:1099-1100.
- Note that the seq assignments at `global.nim:130-135` copy (Nim value semantics), so each tick's
  snapshot is genuinely per-tick, not an alias of the running accumulator.

### F47 — no test asserts the re-derivation frame by frame — **gap**
- Where: `tests/test_viewer.nim:122-140`
- Observed. The one test that touches the viewer packet checks `view.tickCount == state.tick`, that
  the chrome key set is present, `seats.len == 8`, `b.c.len == 32`, that the last packet is
  terminal, and that `meta` carries `beats`/`policyNames`/`spawners`. It does **not** compare any
  recorded value (a cog's `x`, an `inv` entry, a `scoreCp`) against the sim state at that tick, and
  no test re-derives the recorded state at all. Checklist item 2 asks for a test that asserts
  frame-by-frame reproduction. The design note's `## Tests` §4 (design.md:1022-1031) likewise does
  not call for one, so the code matches the note here and the note is what falls short of the
  checklist. Reported as observed; the categorisation is the judge's.

### F48 — `client/chrome_common.js` is byte-identical to the starter's — **match**
- Where: `client/chrome_common.js` (838 lines)
- Observed. `diff client/chrome_common.js /workspace/starters/coworld-ctf/client/chrome_common.js`
  → no output. Zero edits, as design.md:734 requires and checklist item 14 demands.

### F49 — `client/replay_broadcast.html` is the starter's page with a game block appended — **match**
- Where: `client/replay_broadcast.html:1380` (CSS banner) and `:1613-1625` (script banner), both
  reading `MATRIX-GAMES additions to the inherited coworld-ctf chrome`
- Observed by diff of the region above each banner against the starter's corresponding region:
  - CSS above the banner: 1373 lines vs the starter's 1454, with 139 removed and 58 added lines.
    The removals are the `#viewpanel`/`#minimap`/`#zoombar`/`.zbtn`/`#zoom-slider`/`#zoom-read`
    block (starter lines 705-833) and the `body[data-noviewpanel]` rule — exactly the list at
    design.md:757-760. Sections 1-5 of the starter's chrome (stage, scorebug, banner lane, kill
    feed, transport, scrubber + momentum + beat markers + lulls + spoilers, endcard, locker-room
    curtain) are present and otherwise unchanged.
  - Body markup: 90 lines vs the starter's 142. The removals are `#viewpanel` and its children,
    `#mmwarn`, `#povBadge`, `#fpv` and its children — again exactly design.md:757-760. The
    additions are `#mg-matrix`, `#mg-indices`, `#mg-legend`
    (`client/replay_broadcast.html:1559-1565`), plus the three re-captions.
  - This is not the cogame-gridlock shape: the page is the starter's file with the named removals,
    not a rewrite that reuses ids.
- One inherited-CSS edit that is *not* on the note's removals list is at
  `client/replay_broadcast.html:469-470`: `#killfeed`'s `bottom: calc(76 * var(--u))` becomes
  `bottom: calc(var(--band, 0px) + 40 * var(--u))`. That moves the feed out of the transport band,
  which is what checklist rule 14(b) wants.

### F50 — a foreign, unused `.ev-lane` CSS block sits above the banner — **gap**
- Where: `client/replay_broadcast.html:781-835`
- Observed. 55 lines of CSS added to the *inherited* region, whose comment reads "Encounter events
  on the timeline: deaths, phase starts, the enrage, interrupts and crucible soaks", with rules
  `.ev.death`, `.ev.phase`, `.ev.enrage`, `.ev.interrupt`, `.ev.crucible`, `.ev.crucible.soaked` —
  cogame-raid's event vocabulary, not matrix-games'. I grepped the whole page: `ev-lane`, `.ev` and
  `.ev-tip` appear only in this CSS block and are never emitted by the markup or the game block.
  design.md:747-750 says of the region above the banner: "Nothing above them is rewritten".

### F51 — the feed rows and banner chips use class names with no CSS rule — **gap**
- Where: `client/replay_broadcast.html:1926` (`row.className = 'kf-row';`) and `:1948`
  (`chip.className = 'banner';`)
- Observed. The inherited stylesheet defines `.feed-row` (`:489-523`, the padded, tinted
  lower-third row) and `.banner-chip` (`:448-465`). Neither `.kf-row` nor `.banner` matches any
  selector anywhere in the page — I grepped both. `#killfeed` (`:470-488`) and `#bannerlane`
  (`:438-447`) are laid out and positioned, so the text appears, but the rows and chips carry no
  background plate, no pixel font, no size and no colour of their own. design.md:825-830 and
  design.md:836-837 describe styled feed rows and chips.

### F52 — the beat markers are labelled clickable buttons with a CSS rule per kind — **match**
- Where: `client/replay_broadcast.html:1958-1973` (`mgMarkBeat`) and `:1485-1504` (CSS)
- Observed. Each marker is a `<button type="button" class="beat-marker <kind>">` with `title`,
  `aria-label` and an `onclick` that calls `mgCore.seek(tick)`. CSS rules exist for all four kinds
  the stream can emit — `.beat-marker.interact` (`:1485`), `.bigpay` (`:1489`), `.leadchange`
  (`:1493`), `.over` (`:1497`) — plus `button.beat-marker` (`:1501`) and `.ahead` (`:1504`). The
  emitter is closed to those four kinds (`src/matrix_games/broadcast.nim:37-65` and
  `src/matrix_games/global.nim:140-165`), so "a CSS rule per kind" is a closed assertion.
  Asserted at `tests/test_viewer.nim:146-153`. Checklist rule 14(d).
- chrome_common's own `markBeat` is never called by the page, and `renderBeatMarkers`
  (`client/chrome_common.js:550-561`) only appends — it cannot wipe the game block's buttons.

### F53 — the endcard bound and seek dismissal — **match**
- Where: `client/replay_broadcast.html:963-985` (CSS) and `:2190-2201` (JS)
- Observed. `#endcard { top: var(--topband, 0px); bottom: var(--band, 0px) }` is byte-for-byte the
  starter's rule (`/workspace/starters/coworld-ctf/client/replay_broadcast.html:1036-1048`), and
  it is shown with `#endcard.on` (`:985`), the class its CSS rule uses. `mgCore.seek` is wrapped so
  that **every** seek below the final tick removes `.on` (`:2194-2200`), and the loop path clears
  it too (`:2180-2185`). Checklist rule 14(c).

### F54 — `relayout()` is reimplemented, not kept verbatim — **gap**
- Where: `client/replay_broadcast.html:2212-2231` (`mgRelayout`) vs the starter's
  `/workspace/starters/coworld-ctf/client/replay_broadcast.html:4110-…`
- Observed. The starter's `relayout()` is a four-pass fixed-point iteration that measures both
  bands, letterboxes the board between them and sizes `#stage`. `mgRelayout` is a single pass that
  reads `stage.clientWidth`, sets `--hudscale` (clamped 0.5..1.6 against the 760 px reference),
  toggles `#stage.tiny` at `width <= 620`, and sets `--band` and `--topband` from
  `transport.offsetHeight` / `scorebug.offsetHeight`; the board fit is delegated to
  `mgCore.setViewportFit()`. design.md:749 and design.md:779-781 say `relayout()` is kept verbatim
  and letterboxes by fixed-point iteration.
- Checklist rule 14(a) is nonetheless satisfied as written: `--band` (and `--hudscale`,
  `--topband`) are set on `document.documentElement` (`root` at `:2214`), not on `#stage`.
- Checklist item 11 says labels hide "under `640px`"; the code's threshold is `620`
  (`:2219`), inherited from the starter's own `boardW <= 620`, which design.md:870 states.

### F55 — `static_replay.js` is not "verbatim apart from the export names plus one added line" — **gap**
- Where: `replay-viewer/static_replay.js` (256 lines) vs
  `/workspace/starters/coworld-ctf/replay-viewer/static_replay.js`
- Observed by diff. Beyond the `ctf_*` → `mg_*` renames and the worker name string, the file adds:
  a `FETCH_TIMEOUT_MS` watchdog (`:4`, `:179-186`), the whole `coworld-replay` `tell()` bridge
  (`:9-24`) — which is *added*, not "moved", because the starter's file has no `postMessage` to a
  parent at all — a retry button in `showFailure` (`:33-38`), the `data-replay-error` line (`:40`),
  a play/pause + speed + `seek` transport API replacing `sendCommand`/`clickMap`
  (`:221-231`), and `onMeta`/`onLoaded`/`onFrame`/`onEnd` callbacks (`:134-160`). The export object
  is renamed `window.MatrixStaticReplay` (`:255`). design.md:720 and design.md:723-731 describe one
  added line in `showFailure` and a moved `ready` post.
- Provenance is still single-starter: every line is paintbot-lineage or new; nothing is spliced in
  from babel or bullwhip.

### F56 — `client/broadcast_core.js` is a 358-line rewrite, not the starter's file — **gap**
- Where: `client/broadcast_core.js:1-14` and `:357` (`scope.MatrixBroadcastCore = { create: create }`)
- Observed. The starter's `client/broadcast_core.js` is 1407 lines and exports `BroadcastCore`
  over paintbot's binary sprite protocol; this file is 358 lines, exports `MatrixBroadcastCore`,
  and draws from the JSON packet described in its own header. design.md:763-764 states
  "`broadcast_core.js`'s zoom/pan/minimap code stays in the file, **verbatim**, simply never
  driven." What survives is stubs: `attachMinimap` (`:335`), `zoomAt` (`:339`),
  `setZoom` (`:343`). Nothing in the page calls any of them — I grepped
  `client/replay_broadcast.html` for `zoomAt|setZoom|attachMinimap|minimap` and the only hit is a
  comment at `:677`.
- Bearing on checklist 14's last bullet ("removes the panel — markup, CSS, the
  `core.zoomAt/setZoom/attachMinimap` wiring, and the ids from the test list"): the markup, the CSS
  and the ids are gone (F49, and `tests/test_viewer.nim:193-198` asserts it), but the three methods
  still exist in `client/broadcast_core.js` and in `replay-viewer/static_replay.js:226-244`. The
  design note explicitly asks for them to stay (design.md:763-764); the checklist asks for them to
  go. Reported as observed; I am not adjudicating the conflict.

### F57 — the 360 px rules — **match**
- Where: `client/replay_broadcast.html:1408` and `:1510-1519`
- Observed. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow:
  ellipsis; }` at `:1408`, character-for-character the rule checklist item 11 names.
  Under `.tiny`: the plates drop `.plate-enc`, `.plate-name` and `.plate-camp` (`:1510-1513`);
  `#mg-matrix` drops the per-cell payoff pairs and the title (`:1514-1516`); `#mg-indices` shrinks
  (`:1518`); `#mg-legend` hides (`:1519`). `mgRenderIndices` emits the short form
  `19 ENC · 41% COOP` under `.tiny` (`:1854-1858`). design.md:873-878. Asserted at
  `tests/test_viewer.nim:155-159`.

### F58 — the three added overlays stay out of the transport band — **match**
- Where: `client/replay_broadcast.html:1559-1565` (markup, all inside `#chrome`) and the CSS rules
  for `#mg-matrix`, `#mg-indices`, `#mg-legend` in the game block
- Observed. All three are declared inside `#chrome` and above `#transport` in the markup, and each
  rule is positioned relative to `--topband` or `--band`. `tests/test_viewer.nim:161-169` asserts
  each of the three rules contains `var(--topband)` or `var(--band)`. Checklist rule 14(b).

### F59 — the game server registers a `/client/replay` pod route — **gap**
- Where: `src/matrix_games/server.nim:434` (`result.get("/client/replay", replayPageHandler)`),
  documented at `server.nim:14`; handler at `server.nim:291-294`; also
  `src/matrix_games/server.nim:436` (`/replay-data`) and `runReplayServer` (`server.nim:441-447`)
- Observed. Checklist item 3 says "No `/client/replay` pod path anywhere." The route serves
  `client/replay_broadcast.html` off the game container. The design note's own route table
  (design.md:638-646) lists only `/healthz`, `/client/player`, `WS /player`, `/client/global` and
  `WS /global` — `/client/replay` is not in it. The page is also linked from
  `client/global.html:40` and `client/player.html:38`.
- Provenance, for context: the starter serves the same path — `coworld-ctf/src/ctf/server.nim:820-822`
  dispatches `bitworldClient.ReplayClientRoute`, which is `"/client/replay"`
  (`/root/.nimby/pkgs/bitworld/src/bitworld/client.nim:21`). So the route is inherited, not invented.
- The *manifest* declares no pod viewer: `replay_viewer` is `{"bundle": "static-replay-viewer"}`
  and `tests/test_manifest.nim:62-65` asserts `replay_viewer.url == nil` and
  `"/client/replay" notin $game.runnable`.

---

## 7. The manifest

### F60 — every manifest item the note and checklist name is present and correct — **match**
- Where: `coworld_manifest_template.json`, read in full
- Observed, item by item:
  - `num_agents: 8` in **all seven** variants (`variants[*].game_config.num_agents`) and in
    `certification.game_config.num_agents`; each variant's `players[]` has 8 entries and so does
    `certification.game_config.players`. design.md:953-965, 967-969.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`; no `url` key. design.md:913.
  - `game.runnable` = `{"type":"game","image":"{{GAME_IMAGE}}","run":["/bin/matrix-games"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/matrix-games/anthropic_api_key"},
    "source_url":…}`. design.md:914-917. `compose.yaml` declares service `game`, so the derived
    placeholder is `{{GAME_IMAGE}}` (`tests/test_manifest.nim:39-60` derives it rather than
    hard-coding).
  - `game.docs` = `{"readme":{"type":"text","value":…4640 chars},"pages":[rules.md, matrices.md,
    policies.md]}`, each page `{id,title,content:{type:"text",value:…}}` with 2806-5213 chars.
    Checklist item 10 first half. design.md:933-939.
  - `game.protocols` carries **both** `player` and `global`, each a `{"type":"text","value":…}`
    object, not a bare string. Checklist item 10 second half. design.md:941-943.
  - `player[]` has exactly six entries, all `{{GAME_IMAGE}}` on `/bin/matrix-games-player`:
    `matrix-games-player` (no env) plus the five `PLAYER_SCRIPTED` baselines. design.md:944-950.
  - `certification.players` seats all eight, and every one of the six declared ids appears at
    least once (I verified the set difference is empty both ways). design.md:970-976.
  - `config_schema`: `additionalProperties: false`, `required: [tokens, players]`, both array
    properties (`tokens`, `players`) carry `minItems: 1` / `maxItems: 8`, and every scalar carries
    the note's default and range (design.md:920-930). I diffed the property list against
    design.md:920-929: identical, with the note's ranges present on all of them.
  - `results_schema`: `["number","null"]` on `exploitability[].items` and on `coopRate`.
    design.md:931-932, 696-697.
  - Top-level: `$schema`, `episode_timeout_minutes: 20`, six `tags`. design.md:906-908.
  - Cert fixture: `seed 7`, `matrix prisoners-dilemma`, `beats 6`, `ticksPerBeat 50`,
    `playerConnectTimeoutSeconds 180` — 300 ticks = 12.5 s at 24 fps, longer than the 10 s soak.
    design.md:967-978, asserted at `tests/test_manifest.nim:179-182`.
  - The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`,
    `coworld-release.yml`, `coworld-submit.yml`, `tools/ci/docker_smoke.sh`,
    `tools/ci/policies.json` returns nothing. Checklist item 12.

### F61 — the cert fixture names the seats with the aliases, so the two name spaces coincide offline — **unclear**
- Where: `coworld_manifest_template.json` `certification.game_config.players` =
  `[{"name":"Ash"},…,{"name":"Holly"}]`, consumed at `src/matrix_games/server.nim:464-466`
- Observed. `runGameServer` seeds `gameSim.names[slot]` from `config.players[slot].name`, and the
  player container sends no `policy` label unless `PLAYER_POLICY_LABEL` is set
  (`src/matrix_games_player.nim:50`, `:57`), so in the certification fixture `policyNames[]` equals
  `names[]` and the scorebug shows the aliases. Confirmed in the CI docker-smoke output, where the
  viewer smoke's scorebug reads `Ash 0.00 0 enc Birch 0.00 0 enc …` (CI run 32749463742,
  `Load the bundle in a real browser`). The note pins those fixture names itself
  (design.md:954, 969), and on the hosted platform the game config supplies real policy names,
  so I cannot tell whether this is intended or an oversight in the fixture. The *mechanism* for two
  name spaces is present and correct (F16, F48, `broadcast.nim:100-120`, `global.nim:215-216`).

---

## 8. Tests and CI

### F62 — CI is green on `main` at the reviewed sha, including the executed viewer smoke — **match**
- Evidence: `gh run list -R Metta-AI/cogame-matrix-games --branch main -w ci.yml` →
  run id **32749463742**, conclusion **success**, `headSha 7b7d5866c6b5c8010624b60efa2b800230c621a4`
  — the reviewed sha. All three jobs green: `test`, `docker-smoke`, `wasm-viewer`.
- `wasm-viewer` `needs: docker-smoke` (`.github/workflows/ci.yml:212`), and its step
  `Load the bundle in a real browser` **ran and passed** — no `continue-on-error`, not commented
  out. Its output line:
  `{"loaded":true,"ms":571,"clock":"BEAT 1 / 6 TICK 5 OF 300","scorebug":"…","feed_lines":0}`
  followed by `scrub readouts: 0%="BEAT 1 / 6 TICK 5 OF 300" 50%="BEAT 4 / 6 TICK 167 OF 300"
  100%="BEAT 6 / 6 TICK 299 OF 300"` — three distinct clock readouts. Checklist item 13's
  `loaded: true` evidence.
- `docker-smoke`: I grepped the full run log for `SEAT-COUNT FAIL` — **0 occurrences**. The smoke
  reported `game=matrix-games seats=8 …`, `episode end reason: complete`,
  `smoke OK: seats=8 results=709B replay=118954B reason=complete`. Checklist item 6.

### F63 — no test was disabled, skipped or loosened during this run — **match**
- Evidence: `git -C /tmp/cogame-matrix-games log --oneline --name-status -- tests/` shows a single
  commit touching `tests/`: `599f4ad`, which **adds** all eight files (`A` status on
  `tests/support/helpers.nim` and `tests/test_{sim,baseline,indices,replay,llm,manifest,viewer}.nim`).
  The head commit `7b7d586` touches no test file. There is no deletion, no widened tolerance, no
  `skip`. Checklist item 1's second half.

### F64 — `ci.yml` does not pass `--soak`, so the playback soak never runs — **gap**
- Where: `.github/workflows/ci.yml:306-309`
```
          node tools/ci/viewer_smoke.mjs \
            --bundle dist/static-replay-viewer \
            --replay "${replay}" \
            --timeout 90
```
- Observed. `tools/ci/viewer_smoke.mjs:115` defaults `soak: 0`, and `:387` gates the whole soak
  behind `if (loaded && args.soak > 0)`. `grep -n soak .github/workflows/*.yml` returns nothing.
  design.md:1063-1069 specifies `--soak 10` and states that pass requires
  "an uninterrupted 10 s of playback that keeps advancing (the cogball soak)". The load signal and
  the three scrub readouts are still checked and did pass (F62); the "keeps advancing over 10 s"
  half is not exercised. `viewer_smoke.mjs` itself is byte-identical to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (I diffed it), as design.md:985 requires.

### F65 — `test_indices.nim` restates two of five "matrix bites" and drops half of a third — **gap**
- Where: `tests/test_indices.nim:9-22` (the file's own statement of the substitutions),
  `:62-79`, `:90-92`, `:106-109`
- Observed against design.md:619-625:
  - PD "a room of seven `always-first` plus one `always-second` gives the `always-second` seat the
    top score" → replaced by a per-resolution assertion that the defect side out-earns the
    cooperate side in every mixed cell (`:62-79`). The file argues (`:12-18`) that the note's form
    measures positional encounter counts, and that the replacement is strictly stronger.
  - RWS "`counter` outscores `fixed-pick` over seeds 1..8" → replaced by `counter` vs
    `always-first` (`:91`), argued at `:19-22`.
  - Chicken: the note asks for **two** things — "one `always-second` in a room of `always-first`
    tops the table" **and** "an all-`always-second` room's mean is the lowest of the five scripted
    rooms". Only the second is asserted, and in a per-resolution rather than per-room-mean form
    (`:106-109`). The first is not asserted anywhere and the file's header does not list it among
    the restatements.
  - The other two (stag-hunt `:81-88`, BoS `:111-127`) are asserted as written.
- Gates (a) and (c) match the note exactly (`:52-59`, `:129-146`), as do the two null rules
  (`:148-169`).

### F66 — `docker_smoke.sh` does not validate `results.json` against the results schema — **gap**
- Where: `tools/ci/docker_smoke.sh:284-304`
- Observed. The smoke checks that `results.json` exists, is non-empty, decodes as UTF-8 JSON, is a
  non-empty object, and that `names`/`scores` have `seats` entries — and prints a **warning**, not
  an error, if either key is absent (`:300`). It does not load
  `game.results_schema` from the manifest or validate against it. design.md:1057 says the smoke
  "validates `results.json` against the results schema".
- Everything else the note asks of the smoke is present: the four seat-count invariants, each
  exiting with a `SEAT-COUNT FAIL:` prefix (`:110-151`), the independent `SMOKE_SEATS` cross-check
  (`:146-151`, `seats_expected="${SMOKE_SEATS:-8}"` at `:54`), the game exit-code assertion
  (`:237-242`), **every player** container's exit code (`:250-266`), and the replay copy to
  `dist/smoke/replay.json` (`:334-338`).

### F67 — the determinism test runs two fresh `Sim`s in one process, not a separate process — **gap**
- Where: `tests/test_sim.nim:243-251`
- Observed. `runScripted(...)` is called twice and the hashes compared, plus a third run at a
  different seed to prove the hash discriminates. design.md:1005-1006 asks for the identical
  `gameHash` after 600 ticks "twice in one process **and across a fresh `SimServer`**". Each
  `runScripted` builds a fresh `Sim` via `initSim` (`tests/support/helpers.nim:24`), so two fresh
  sim objects are compared; no second process or server instance is involved.

### F68 — the other tests assert what the note's `## Tests` section says — **match**
- `tests/test_sim.nim` (design.md:997-1006): the PD hand-computed case `366`
  (`:41-46`), a mixed case for each of the seven (`:48-64`), negative-RWS truncation direction
  (`:66-75`), argmax ties (`:87-90`), beam ray length + wall blocking + first-cog targeting
  (`:93-108`), pickup with a full type + the respawn timer (`:110-133`), freeze/immune/
  beamResetCooldown + the endowment reset (`:135-165`), BoS same-camp `nocontest` and the blue-camp
  row rule (`:167-205`), BFS tie-breaking and the occupied-cell block (`:207-223`), movement
  never sharing a cell (`:225-241`), determinism (F67), inventory range (`:253-258`).
- `tests/test_baseline.nim` (design.md:1007-1014): all five baselines × all seven variants ×
  seeds 1..8 with a per-order legality check (`:38-51`, `checkOrder` at `:17-35` covering
  intent-in-set, token present iff required and in `0..K-1`, target present iff required and
  non-self and in `legal.targets`); wall/shared-cell/inventory-range over whole episodes
  (`:53-65`); the "reads only the observation" assertion done by capturing observations in a
  `block:` and letting the `Sim` go out of scope (`:67-79`); degrade-not-raise on `%*{}` (`:81-85`);
  the <1 ms per beat budget (`:87-106`). `src/matrix_games/scripted.nim` imports no sim module —
  only `std/json` and `sim_types` (`scripted.nim:13-14`) — so the property holds structurally.
- `tests/test_replay.nim` (design.md:1022-1031): every assertion the note lists is present —
  `validateUtf8 == -1` (`:21`), protocol (`:23`), `frames.len == ticksPlayed` (`:30`), both series
  lengths (`:31-32`), event ticks in range (`:49-50`), ≥1 pickup/beam/interact (`:55-57`),
  `reset == 2 × interact` (`:58`), `beatclose == beats` (`:59`), exactly one `end` (`:60`),
  `results.scores.len == 8` (`:71`), `reason` in the legal set (`:72`),
  `names.len == policyNames.len == 8` (`:65-66`), `config.rowPay`/`colPay` (`:69-70`), `< 8 MiB`
  (`:80`), and the rune cap case (F36).
- `tests/test_llm.nim` (design.md:1032-1037): every clause covered — see F19-F24.
- `tests/test_manifest.nim` (design.md:1038-1045): every clause covered, plus the policies.json
  and CI-scaffold suites (`:184-242`).
- `tests/test_viewer.nim` (design.md:1046-1054): the chrome key set as a closed set (`:56-63`),
  `teams` = exactly the K token keys (`:65-73`), `lead.pts` rows of length `K+1` (`:75-79`), eight
  `seats` with policy name / livery / score / interactions (`:81-91`), `over` on the terminal frame
  (`:93-101`), a `.beat-marker` rule per emitted kind (`:146-148`), the `.plate-name` and two
  `.tiny` rules (`:155-159`), and the no-collision check against the chrome alias list parsed out of
  `chrome_common.js`'s `return {…}` block (`:171-191`, requiring every game-block top-level function
  to be `mg`-prefixed).

### F69 — `tools/ci/policies.json` and the release order — **match**
- Where: `tools/ci/policies.json`, `.github/workflows/coworld-release.yml`
- Observed. Four policies, all on `/bin/matrix-games-player`: `matrix-games-reader` (801-char
  `PLAYER_PROMPT`, `USE_BEDROCK: "true"`, no `player`), `matrix-games-brinkman` (637-char prompt,
  `USE_BEDROCK: "true"`, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), plus
  `matrix-games-counter` and `matrix-games-tit-for-tat` as `PLAYER_SCRIPTED` fillers — checklist
  item 12's "≥ four distinct policies, two `PLAYER_PROMPT` champions plus ≥1 scripted filler,
  champion #2 carrying that player id". design.md:986-989.
- Release order: `Build the Coworld manifest` (`coworld-release.yml:153`) → `Certify locally`
  (`:167`) → `Upload the policies` (`:206`) → `Upload the Coworld` (`:304`) →
  `Put the Coworld secret` (`:342`). All three workflows present (`ci.yml`, `coworld-release.yml`,
  `coworld-submit.yml`); `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both
  mode `-rwxr-xr-x`. Checklist item 12.
- `tools/build_replay_viewer.sh` is the starter's script with the three named edits: `image_tag`
  renamed (`:35`), `docker cp` source `/workspace/matrix_games/replay-viewer/dist/.` (`:61-62`),
  and the ecos `mkdir -p "$(dirname "${requested_output}")"` placed **before** the containment
  resolution (`:27-29`). design.md:704-708.

### F70 — art provenance differs from what the note describes — **gap**
- Where: `scripts/art/gen_matrix_art.py:9-14` vs design.md:851-853
- Observed. The note says the eight liveries are "retinted from paintbot's shipped
  `data/rig_real/{blue,red,green,yellow}/*` rigs" using "`scripts/art/retint_team_props.py`, which
  the repo already ships". In the repo the generator's stated inputs are
  `data/cog/cog_{idle,carry,hold,fire}.png`, "the four poses split out of the nano-banana render
  `scripts/art/source/cogs_sheet.png`", and "nothing else". `data/rig_real` exists in the starter
  (`/workspace/starters/coworld-ctf/data/rig_real`) but is not present in this repo, and
  `scripts/art/retint_team_props.py` is in the starter's `scripts/art/` but not in this one
  (this repo ships `gen_matrix_art.py` and `split_cog_sheet.py`).
- The art itself is real, committed and deterministic, and every asset the manifest names exists:
  `data/rig_matrix/<livery>/{idle,carry,hold,fire,armband}.png` for all eight liveries,
  17 token sprites across the seven variants, `data/yard_floor.png`,
  `data/beam_<livery>.png`, `data/reset_burst.png`, `data/pickup_spark.png`, and the locker-room
  art. `tests/test_viewer.nim:258-277` asserts every path in `artManifest`
  (`src/matrix_games/map_art.nim:35-59`) exists, and `Dockerfile.replay-viewer` repeats the
  `test -f` assertions. No placeholders, no TODO assets.

### F71 — the shutdown writes the replay before `results.json` — **gap** (documented deviation)
- Where: `src/matrix_games/server.nim:148-156`
- Observed. design.md:665-667 pins the order "write `results.json` … → write the replay". The code
  writes the replay first and states why in a comment (`server.nim:148-152`): the hosted worker
  treats `results.json` as the end of the episode and tears the pods down, so a replay written
  after it can be lost; paintbot and cogame-raid both do it this way. Everything else in the
  shutdown sequence matches design.md:664-670: `final` to every player socket
  (`server.nim:144`), last global frame (`:145`), `sleep 500` (`:146`), both artifacts as
  `application/json` through `COGAME_SAVE_REPLAY_METHOD` / `COGAME_RESULTS_METHOD` (`:153-156`),
  then the 20 s `/healthz` + `/global` grace and `quit(0)` (`:261-264`).

---

## Traced and consistent (verified, no finding)

- `src/matrix_games.nim:49-51` — the seed is randomised **before** the config is consulted for a
  pinned seed and before `initSim`, so every seed-derived draw (the spawner layout at
  `sim_state.nim:88-106` and `fixedType` at `sim_state.nim:139`) follows the final seed
  (design.md:659-661). `seedPinned` (`:22-29`) parses the raw config text for a `seed` key rather
  than comparing against a sentinel value.
- `src/matrix_games/sim_config.nim:72-99` — `validate()` hard-requires `numAgents == Seats`, so a
  variant that changes the seat count cannot start (design.md:1103-1104). It also range-checks
  `beats`, `ticksPerBeat`, `tokenCap`, `beamRange`, `stepCooldownTicks`, `viewRadius` and
  `llmTimeoutSeconds`; the remaining ranges the note lists (`freezeTicks`, `beamResetCooldown`,
  `beamMissCooldown`, `tokenRespawnTicks`, `minBeatSeconds`, `maxOutputTokens`, …) are enforced only
  by `config_schema`, which is where the note states them (design.md:920-929).
- `src/matrix_games/server.nim:428-439` — `/client/player` and `/client/global` are registered
  **before** the `/client/@name` catch-all asset route (design.md:648). `/player` is not registered
  in replay mode.
- `src/matrix_games/server.nim:375-377` — the websocket handler answers `Ping` with `Pong`, which
  hosted certification pings `/global` for.
- `src/matrix_games/server.nim:296-311` — the asset handler rejects any `name` containing `/`,
  `\` or a leading `.`, so there is no path traversal off `clientDir()`.
- `src/matrix_games/server.nim:231-240` — a seat that dropped mid-episode is switched to
  `skCounter` for the remaining beats each beat, and `pushStateFrames` is fire-and-forget, so the
  episode never waits on a dropped socket (design.md:502-503).
- `src/matrix_games/broadcast.nim:154-200` — `buildStateJson` emits paintbot's exact chrome key
  set plus `seats` and four named extras, and ships `beats`/`lulls`/`lead` whole on the first frame
  only (design.md:832-834). `teams` carries the K token-chrome keys `red`/`blue`/`green`
  (`broadcast.nim:122-141`, `sim_types.nim:41`), which chrome_common's `TEAM_ORDER`/`teamCol`
  already know.
- `src/matrix_games/scripted.nim:102-140` — the five baselines are exactly the note's algorithms
  (design.md:479-483): `always-first` `commit(0)`, `always-second` `commit(min(1, k-1))`,
  `fixed-pick` `commit(fixedType)`, `tit-for-tat` `commit(lastSeen[t])` hunting `t`, `counter`
  `commit(bestResponseRow[j])` or `bestResponseCol[j]` for a column-camp cog in BoS
  (`scripted.nim:57-58`, `:134-136`), all with `commitTarget = 5` (`sim_types.nim:59`,
  `scripted.nim:105`). `lastSeen` walks the public log forward so the last write wins, i.e. the most
  recent resolution (`scripted.nim:80-90`), defaulting to token 0 (`scripted.nim:64`).
- `src/matrix_games/arena_map.nim:59-81` — line of sight is Bresenham over the wall grid with the
  origin cell excluded, used for both `visible()` (`sim_state.nim:191-198`) and the visible-token
  list (`sim.nim:242-247`), both gated on `viewRadius` (design.md:357-359).
- `src/matrix_games/sim.nim:277-292` — the observation's `log` is the **complete** public
  resolution log for the whole episode, both participants, both mixes, both payoffs
  (design.md:360-363). No other seat's `intent`, `notes`, `say`, prompt or policy name appears
  anywhere in `buildObservation` — I read the whole proc (`sim.nim:215-345`) checking for it.
- `src/matrix_games/events.nim:17-19` — the event vocabulary is exactly the note's nine kinds, and
  every field list at `sim.nim:38-44, 107-110, 128-132, 137-138, 142-143, 56, 153-154, 165-167,
  187-188` matches the table at design.md:545-555.
- `Dockerfile.replay-viewer` — splices the three HTML markers, copies `chrome_common.js`,
  `broadcast_core.js`, both `static_replay*.js`, `font.ttf` and all of `client/art/`, then asserts
  every one is non-empty plus `! grep -q '<!-- BROADCAST_CORE -->'` on the output. The bundle
  therefore cannot ship an unspliced page.
- `compose.yaml` — one service named `game`, image `cogame-matrix-games:latest`, building
  `Dockerfile`; `Dockerfile:58-64` installs `/bin/matrix-games` and `/bin/matrix-games-player` from
  one image with `CMD ["/bin/matrix-games"]` (design.md:889-904, 980-981).
- `tools/ci/viewer_smoke.mjs` — byte-identical to `coworld-builder/templates/tools/ci/viewer_smoke.mjs`
  (diff produced no output), as design.md:985 requires.

---

## Could not determine

- **Whether `mgRelayout`'s single pass letterboxes as well as the starter's fixed-point loop.**
  The board fit is delegated to `mgCore.setViewportFit()` (`client/replay_broadcast.html:2226-2229`,
  `client/broadcast_core.js`), which I read but cannot exercise. What would settle it: a 360 px and a
  desktop-width screenshot from the phase-60 viewer check, or a `--soak` run that also captures the
  board rect. (Related to F54.)
- **Whether the unstyled `.kf-row` / `.banner` elements are legible at 360 px.** The CI viewer smoke
  reported `feed_lines: 0` at tick 5 (no events yet), so the screenshot in the `viewer-smoke`
  artifact does not show a populated feed. What would settle it: a screenshot taken mid-episode, or
  the phase-60 360 px check. (Related to F51.)
- **Whether the tick-0 `leadchange` marker is visible on the scrubber.** I traced the emission and
  the marker construction but did not run the viewer. What would settle it: a viewer smoke that
  counts `.beat-marker.leadchange` elements, or a run. (Related to F8.)
- **Whether any code on the live beat-loop path can raise.** I found no raising call, but the loop
  is unguarded and I cannot prove absence by reading. What would settle it: a fuzzed
  `decideAll`/`installOrders` test, or wrapping and observing. (Related to F32.)
- **Whether `replay.indices.conventionCounts` and the viewer's re-derived histogram agree on a real
  episode.** Both are derived from the same resolutions but by different code. What would settle
  it: a test that loads the replay bytes and compares `initViewer(...).conventionAt[^1]` against
  `replay.indices.conventionCounts`. (Related to F40.)
- **Whether the note's intent for `gather`'s "from the seat's own observation" is a metric or an
  information restriction.** (Related to F12.) What would settle it: a coordinator ruling on the
  note's wording.
- **Whether the checklist's "remove the `core.zoomAt/setZoom/attachMinimap` wiring" or the design
  note's "the zoom/pan/minimap code stays in the file, verbatim, simply never driven" governs.**
  (Related to F56.) What would settle it: a judge ruling; the two documents ask for opposite things.
- **Runtime behaviour of the LLM path.** Every finding about batching, retry, pacing and the
  deadline is read from source and from the stub-driven tests; no episode in this run had
  credentials (the CI smoke logs `no ANTHROPIC_API_KEY: the game must complete on its scripted
  baselines`). What would settle it: a phase-60 league episode with the fallback counter.
