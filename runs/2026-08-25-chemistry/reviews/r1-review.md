# r1 review — chemistry

Repo: `/workspace/chemistry` (`Metta-AI/cogame-chemistry`) at `2c34a025c4968c48918bc619caab9e44360a9c5c`
Design note: `/workspace/coworld-builder/runs/2026-08-25-chemistry/design.md` (byte-identical to the
repo's own `docs/plans/2026-08-25-chemistry-design.md`)
Starters diffed: `/workspace/starters/coworld-ctf`, `/workspace/starters/cogame-bullwhip`
Checklist read for scope: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files opened: 44 (14 `src/chemistry/*.nim`, 2 entrypoints, 4 `replay-viewer/*`, 4 `client/*`,
7 `tests/*.nim`, 4 `tools/ci/*` + `tools/build_replay_viewer.sh`, 3 workflows, manifest, compose,
2 Dockerfiles, both starters' counterparts, `curly`/`bitworld` sources for timeout semantics)

**Register.** This is a trace, not a verdict. Findings are numbered `F1…F60` and each is labelled
`MATCH` (code does what the note says), `MISMATCH` (code and note disagree), or `OBSERVED` (a fact
the note is silent or ambiguous on). No severity is assigned; categorisation is the judge's.
Statements are marked *observed* (read in the file), *inferred* (reasoned from what was read), or
*untested* (would need a run to settle).

---

## 1. Resolution rules — the nine-step tick order

### F1 — MATCH: the nine steps run in the note's order
`src/chemistry/sim.nim:358-376`. `stepTick` increments `sim.tick` then calls, in order,
`stepVents`, `stepIntent`, `stepTakeDrop`, `stepMoves`, `stepEat`, `stepReactions`, `stepDecay`,
`stepRot`, `stepRecord`, then `closeShift` when `tick mod ticksPerShift == 0`. That is design
§"Shifts, and the exact tick resolution order" steps 1–9 plus the shift-boundary clause (note
lines 202-222). *Observed.*

### F2 — MATCH: vents emit in species order, N/E/S/W, gated by the ground cap
`sim.nim:30-44`. `for species in Species` iterates the enum declared at `sim_types.nim:67-74` as
`resin, spark, brine, glitter, quartz` — the note's order (line 202). `sim.nim:35` skips when
`period <= 0` (so `distractorPeriod = 0` means the vent does not exist, note line 148);
`sim.nim:37` skips when `looseCount(species) >= ventCapFor(species)`; `sim.nim:40-45` walks
`direction 0..3` against `StepOrder` = N,E,S,W (`room.nim:85-89`) and places on the first
qualifying neighbour. *Observed.*

### F3 — OBSERVED: a vent's "free neighbour" test ignores cogs
`sim.nim:42` accepts a neighbour when `sim.room.isFloor(cell) and not sim.hasMoleculeAt(cell)`. A
cell occupied by a cog is therefore emitted onto. The note (line 146-147) says "the first free cell
among its orthogonal neighbours … or if all four neighbours are occupied" without defining
"occupied". *Observed*; the note does not settle which reading it intends.

### F4 — MATCH: kernel intent is computed against the state at the start of step 2
`sim.nim:50-59`. All eight actions are computed into a local `actions` array in the first loop
(which mutates nothing) and only then written to `cogs[].lastAction`. A cog with
`moveTimer > 0` has a `move_*` rewritten to `acWait` at `sim.nim:54-56` — note line 203-204.
*Observed.*

### F5 — MATCH: take/drop, misdrop, and the double-take rule
`sim.nim:65-114`. `acTake` fails to `acWait` when the hand is full or the cell is empty
(`sim.nim:70-71`); a successful take clears the cell (`sim.nim:74`), so a later slot's `take` on the
same cell this tick finds nothing and degrades — the note's "a take of a molecule another cog
already took this tick fails" (line 205-206). `acDrop` on a pad either enters stock
(`sim.nim:87-94`) or fires `misdrop` and destroys the molecule (`sim.nim:95-102`), matching note
lines 133-138. *Observed.*

### F6 — MISMATCH: `hoard` is counted on any drop at home, and `results.hoarded` is that counter,
not an end-state census
`sim.nim:109-110` increments `cogs[slot].hoard` whenever a drop lands on the seat's own home cell,
irrespective of the standing order's `job`. The note (line 185-187) attaches the increment to the
`hoard` job; more materially, note line 691 defines `hoarded[i]` as "molecules **on** that seat's
home cell **at the end**". `sim.nim:478` reports `sim.cogs[slot].hoard` — a cumulative drop
counter, which does not decrease if the molecule is later picked up. The manifest's own
`results_schema` description (`coworld_manifest_template.json:312`) reads "Molecules that seat
dropped on its own home cell", i.e. it agrees with the code and not with the note.
`src/chemistry/broadcast.nim:103-115` derives the viewer's `hd` the same way (from `drop` events at
`SeatHomes[seat]`), so code and viewer are internally consistent. *Observed.*

### F7 — MATCH: moves resolve in slot order against the live board
`sim.nim:120-144`. The target must not be a wall (`sim.nim:131`; `room.isWall` returns `true`
out-of-bounds, `room.nim:24-27`) and must not hold any other cog (`sim.nim:136-140`). Because
`cogs[slot].cell` is updated in place inside the same loop, a lower-numbered seat that already moved
there blocks a higher one — note line 209-211. *Observed.*

### F8 — MATCH: move cooldown is 2 ticks
`sim.nim:145-149`. A successful move sets `moveTimer = max(0, moveCooldown - 1)` = 1; a tick without
a move decrements it. Combined with F4 this yields one move every 2 ticks = 12 cells/s at
`TargetFps = 24` (`sim_types.nim:33`), the note's figure (line 158). Asserted by
`tests/test_sim.nim:198-213`. *Observed.*

### F9 — MATCH: auto-eat, and the reaction/cold-start/decay/rot arithmetic
- Eat: `sim.nim:155-163`, +1 `foodEaten`, `eat` event, in slot order (note line 212-213).
- Reaction preconditions and yield: `sim.nim:219-235` — `cooldown == 0`, both stocks ≥ 1, consume 1
  of each, `charge = min(chargeMax, charge+1)`, `cooldown = reactionCooldown`,
  `produced = 1 + charge div 3` on the **post-increment** charge (note line 120-123).
- Cold start: `sim.nim:205-218` — at `charge == 0`, if both stocks ≥ `coldStartCost`, subtract that
  from each, `charge = 1`, `restart` event, **no** food, and `continue` so no reaction that tick
  (note line 127-131 and line 214-215 "cold start first … else a reaction").
- Decay: `sim.nim:241-251` — `tick > 0 and tick mod chargeDecayPeriod == 0`, `-1` floored at 0, and
  a `cold` event plus a `cold` beat on the 0 crossing (note lines 124-126, 216).
- Rot: `sim.nim:257-266` — ages every token, removes at `age >= foodLifetime` with a `rot` event
  (note line 217). *Observed.*

### F10 — OBSERVED: a token's in-game lifetime is 239 ticks after the tick it is placed on, not 240
`sim.nim:220` (`placeFood` sets age 0) runs in step 6 of tick *T*; `sim.nim:262` increments every
token's age in step 8 of that same tick *T*. A token therefore reaches `age == foodLifetime` at tick
*T+239* and is removed there. `tests/test_sim.nim:143-153` places the token *outside* the tick loop
(before any `stepTick`), so it measures the full 240 and passes. The note says "not eaten within
`foodLifetime = 240` ticks (10 s) rots" (line 143-144). *Observed*; the one-tick offset is a
consequence of the step order the note itself specifies.

### F11 — MATCH: spill-ring placement order, and the `spoil` path
`sim.nim:169-197`. Candidate cells are `room.spill[index]` (built at `room.nim:56-67` as the 5×5
border minus its four diagonal corners = 12 cells, asserted at `tests/test_sim.nim:42-43`), filtered
to those without food, sorted by Manhattan distance to the deliverer's cell then by `a.y` then `a.x`
— "ties by `(row, col)`" (note line 141-143). Surplus fires `spoil` with `lost = count - placed`
(`sim.nim:196-197`, note line 143-144). *Observed.*

### F12 — OBSERVED: "free" spill-ring cell means "no food there", not "nothing there"
`sim.nim:177-179` only excludes cells that already hold food. A ring cell holding a loose molecule,
or one a cog is standing on, still receives a token. (A cog standing on a fresh token eats it next
tick at step 5, which is the note's camping strategy, so this reading is coherent; the note does not
state it.) *Observed.*

### F13 — MISMATCH: `STARVING` drops the note's "a stock is 0" clause
`src/chemistry/sim_state.nim:122-128`: `charge <= 0 → COLD`; `ticksSinceReaction <= 48 → RUNNING`;
otherwise `STARVING`. `src/chemistry/broadcast.nim:117-120` (`statusWord`, the viewer's copy, driven
off `tick - tracker.lastReaction`) is the same three-way test. The note (line 779-782) defines
`STARVING` as "charge ≥ 1 **but a stock is 0 or** no reaction for 48 ticks". A vat with charge ≥ 1,
an empty stock, and a reaction 10 ticks ago therefore reads `RUNNING` in both the observation
(`llm.nim:131`) and the scorebug. *Observed.*

### F14 — MATCH: shift accounting
`sim.nim:308-340`. `closeShift` increments `sim.shift`, records per-reactor `reactions`/`foodMade`
and current `charge`, per-seat `shiftEaten`, and diffs `misdrops`/`coldStarts` against the running
totals; emits `shift` with `charge[]`, `foodMade[]`, `eaten[8]`, `misdrops`, `coldStarts`
(`events.nim:111-117`) and a `shift` beat; then resets the per-shift counters. That is the note's
`shift` event row (line 577). *Observed.*

### F15 — MATCH: the four end conditions and the three legal `reason` values
`sim.nim:283-306, 342-356`. Shift limit first (`sim.nim:348-350` → `complete`/`shift_limit`), then
famine (`coldStreak >= FamineShifts (3)` **and** `foodCells().len == 0` → `complete`/`famine`, with a
`famine` event and beat latched once). `endEarly` → `deadline`/`deadline` (`sim.nim:297-299`);
`forfeit` zeroes every score then → `forfeit`/`forfeit` (`sim.nim:301-306`). `EndReason` has exactly
`complete|deadline|forfeit` (`sim_types.nim:182-186`) — the note's "only legal values" (line 261).
*Observed.*

### F16 — MATCH: scoring is food eaten, higher better, ties are multiple winners
`sim.nim:290-292` (scores = `foodEaten`), `sim.nim:467-474` (`win[i] = (score == max)`). Note lines
226-230. *Observed.*

### F17 — OBSERVED: the seed does not vary anything; every seed plays the same episode
`sim_state.nim:58-67` defines `nextRandom` and `initSim` seeds `sim.rng` from `config.seed`
(`sim_state.nim:234-236`), but `nextRandom` has **no call site anywhere in `src/` or `tests/`**
(verified by grep). The room is a pure function of the config (`room.nim:32-73`), opening state is
fixed (`sim_state.nim:241-262`), and every rule the note names resolves by fixed order rather than a
draw. This is consistent with the note's own statement that the RNG "is used only for
tie-free-but-arbitrary choices that the rules below name explicitly" (line 91-93) and none do.
*Inferred consequence:* the "seeds 1..12" loops in `tests/test_baseline.nim:72` and
`tests/test_feasibility.nim:28` are twelve identical repetitions of one episode per
(variant, policy-mix), not twelve samples. *Observed + inferred.*

### F18 — OBSERVED: `react.by` / food anchoring use the reactor's *last* deliverer, which can be
from an earlier tick
`sim.nim:204` reads `sim.reactors[index].lastDeliverer`, set at `sim.nim:89` on every successful
drop into stock and never cleared. When a reaction fires because a cooldown expired rather than
because a delivery just completed the pair, `by` and the food anchor are the most recent depositor,
which may have moved away. The note says "`by` = the seat whose delivery triggered it" (line 570)
and "the cog that delivered the molecule which triggered the reaction" (line 141). *Observed.*

### F19 — OBSERVED: the courier kernel adds an equal-distance "sidestep" the note does not describe
`src/chemistry/kernel.nim:76-86`. When every strictly-descending neighbour is a wall or another cog,
`walk` takes an equal-distance step instead of waiting, with a comment explaining the deadlock it
avoids. The note's kernel spec (lines 174-191) describes only BFS-descent + arrival actions. The
addition is deterministic (first equal-distance neighbour in N,E,S,W order) so it does not disturb
the determinism claim. *Observed.*

### F20 — MATCH: the rest of the kernel
`kernel.nim:106-148`. `supply`: carrying the wanted species → walk to `room.pad[reactor]`, `drop` on
arrival; empty hand → walk to the nearest loose unit (`looseCells` is row-major,
`sim_state.nim:108-114`, giving the note's `(row, col)` tie order), `take` on arrival; none loose →
walk to a free vent neighbour and `wait`; wrong molecule in hand → `offPadStep` then `drop`.
`forage`: nearest food, else the named/highest-charge reactor's spill ring, `wait` there.
`hoard`: as supply with `home` as the destination. `idle`: `wait`. Note lines 176-188. *Observed.*

---

## 2. Scripted baselines

### F21 — MISMATCH (documented in-code): the courier's per-slot lane index
The note (line 493-494) says: sort the lanes by `need` desc → charge asc → fixed lane order, then
emit `lanes[mySlot mod lanes.len]`. `src/chemistry/scripted.nim:94-96` instead does
`if slot < fixed.len: fixed[slot] else: priority[(slot - fixed.len) mod priority.len]` — slots 0–5
take the **fixed, unsorted** lane order and slots 6–7 take the two neediest sorted lanes. The
comment at `scripted.nim:78-83` states the reason (lane stability across shift boundaries). The
*set* of lanes covered and the note's prose outcome ("slots 0–5 take one lane each and slots 6–7
double up on the two neediest", line 497-498) are preserved; the per-slot mapping is not the note's
formula. *Observed.*

### F22 — MATCH: the rest of both baselines
`scripted.nim:40-58` builds the lane table with `target = coldStartCost` when charge 0 else 2
(note step 1); `scripted.nim:60-66` sorts need-desc / charge-asc / lane-order (note step 2);
`scripted.nim:88-92` emits `forage` at the highest-charge reactor when every `need <= 0` (note step
3); `say = "<species> to <Reactor>"`, `notes` empty (`scripted.nim:102`, note step 4).
`freeloaderOrder` (`scripted.nim:104-127`) is always `forage` at the highest-charge reactor with
`say = "waiting by the vats"`, with the single all-cold exception taking the largest-need lane —
note lines 500-504. *Observed.*

---

## 3. The decision path

### F23 — MATCH: one parallel batch per shift, retry once, fall back to courier, source recorded
`src/chemistry/llm.nim:567-619`. `decideAll` partitions seats into scripted/disabled (served
immediately from `scriptedOrder`, `llm.nim:579-581`) and `open`. `for attempt in 0 .. 1` builds a
single `RequestBatch` over every open seat and issues it with one
`client.curl.makeRequests(batch, client.timeoutSeconds)` (`llm.nim:588-600`) — one parallel batch,
never sequential (note line 318-319; checklist's simultaneous-decision clause). Attempt 1 appends
`RetryHint` (`llm.nim:563-565, 592-593`), whose text is the note's verbatim hint (note lines
512-514). Seats still failing after the retry get `sim.courierOrder(slot)` with
`source = osFallback` and the log line `"chemistry llm: seat N falling back to scripted order"`
(`llm.nim:616-619`) — the note's exact string (line 516). `decideAll` never raises: every per-seat
failure is caught at `llm.nim:611-614`. *Observed.*

### F24 — MATCH: tolerant parsing and the reply schema
`llm.nim:457-468` (`extractJsonObject`) takes the substring from the first `{` to the last `}`, so
markdown fences and surrounding prose are tolerated; no object at all raises with a truncated,
rune-safe excerpt. `llm.nim:470-507` (`parseDecision`) rejects a missing/unknown `job` and an
unknown `molecule`/`reactor` string, then defers to `sim.normalizeOrder`. Note lines 400-415.
*Observed.*

### F25 — MATCH: `normalizeOrder`'s clamp / invalid split
`sim.nim:388-429`. `supply` without a reactor → invalid (`sim.nim:412-413`); `supply`/`hoard` without
a molecule → invalid (`sim.nim:406-407`); a species absent in this variant → invalid
(`sim.nim:408-410`); a reactor absent in this variant on `supply` → **clamped** to the present
reactor with the lowest charge with `clamped = true` (`sim.nim:414-424`); a feedstock the named
reactor does not take → **accepted as written** (no test exists in the procedure — the misdrop stays
expressible). Note lines 410-412. *Observed.*

### F26 — MISMATCH: on `forage`, an absent reactor is silently dropped rather than clamped
`sim.nim:402-404`: for `jobForage`, `if order.hasReactor and not sim.config.hasReactor(...)` sets
`hasReactor = false` and leaves `clamped = false`. The note's `reactor` row (line 412) says
"required for `supply`; optional for `forage`. Naming a reactor absent in this variant → **clamped**
… recorded as `"clamped":true`" — the clamp sentence is not scoped to `supply`. The kernel's
`bestForageReactor` (`kernel.nim:12-25`) then falls back to the highest-charge reactor, so the
played behaviour is defined; only the `clamped` flag on the `order` event differs. *Observed.*

### F27 — MISMATCH: a seat that never connected is sent to the LLM rather than played as `courier`
`src/chemistry/server.nim:432-433` initialises `state.prompts` to eight empty strings and
`state.scripted` to eight `skNone` (the enum's first value, `scripted.nim:15`). Those are only
overwritten when a `prompt` frame arrives (`server.nim:396-398`). In `decideAll`
(`llm.nim:577-583`), a seat with `kind == skNone` and a non-disabled client is added to `open` and
issued a request whose operator block is empty (`llm.nim:374-378` returns `""` for an empty prompt).
The note (line 520-521) says "a seat that never connected, or whose socket dies mid-episode, plays
`courier` for every remaining shift". Offline (no credentials) the client disables itself
(`llm.nim:113-116`) and every seat plays `courier`, so this only diverges when credentials are
present. `Cog.connected` is declared at `sim_types.nim:157` and is **never assigned anywhere** in
`src/`. *Observed.*

### F28 — OBSERVED: a 429 is retried inside the same shift, not deferred to the next shift's batch
`llm.nim:546-549` raises on 429; `llm.nim:611-614` catches it and puts the seat in `stillOpen`, so
attempt 1 retries it in the same shift's retry batch and a second 429 lands on the courier fallback.
The note (line 518) says "429 is logged and the seat is retried in the next shift's batch". 401/403
does match the note: `llm.nim:542` sets `client.disabled = true` for the rest of the episode.
*Observed.*

### F29 — OBSERVED: `nearestCellOf` computes a BFS field and then discards it
`llm.nim:141-154` builds `sim.room.distanceField(cells)`, never reads it (`discard field`,
`llm.nim:153`), and returns the Manhattan-nearest cell. The observation's `nearestToYou` is
therefore straight-line-nearest, not walk-nearest. The note does not specify the metric (line 355).
*Observed.*

### F30 — MATCH: the observation contains what the note lists and nothing more
`llm.nim:165-282`. Present: `type/protocol/slot/name`, `shift = sim.shift + 1`, `shifts`,
`ticksPerShift`, `tick`, `room{cols,rows,variant}`, `you{cell,carrying,home,foodEaten,delivered,
misdrops,hoard,lastOrder(+source)}`, `reactors[]` with every field in the note's example
(`llm.nim:120-139`), `molecules{}` per present species with `inert/vent/loose/nearestToYou`,
`food{loose,cells}`, `cogs[8]` with `lastOrder` **without** `source` (`llm.nim:196`), `history[]`,
the seat's own `notes`, and `rules{}`. Absent: any other seat's `notes`, any policy/player name, the
seed. `tests/test_llm.nim:149-165` asserts the negative half. Note lines 342-390. *Observed.*

### F31 — MATCH: prompts
`llm.nim:310-372` (system) carries the alias in capitals, the grid, the action vocabulary,
`carryCap`/`moveCooldown`, the standing-order model, the reaction graph including the inert species,
charge/decay/cold-start/yield, the scoring rule with the spill-ring sentence, the "other seven cogs
decide SIMULTANEOUSLY / `say` is heard next shift / `notes` is private" paragraph, and the note's
verbatim `OUTPUT FORMAT:` sentence (`llm.nim:372`). `llm.nim:380-453` (user) renders the vat table,
the molecule table, the cog table, the history table, `YOUR NOTES FROM LAST SHIFT`, the operator
block with the note's verbatim wording (`llm.nim:377-378`), then a one-line restatement whose enums
are computed **for this variant** (`llm.nim:291-301`). Note lines 425-453; asserted at
`tests/test_llm.nim:167-177`. *Observed.*

### F32 — MATCH: the transport ladder
`llm.nim:63-71` returns exactly `["us.anthropic.claude-haiku-4-5-20251001-v1:0"]` unless
`BEDROCK_MODEL` is set — a one-rung, haiku-only ladder (note line 454-455). `llm.nim:511-531` sends
no `output_config.effort` (comment at `llm.nim:525-526`), `max_tokens = maxOutputTokens` (default
700, `sim_config.nim:66`). Credential order is Bedrock sidecar → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI` (`llm.nim:50-61, 93-116`); with none, `disabled = true` immediately
(note lines 456-459). *Observed.*

---

## 4. Every wait and its bound

### F33 — MATCH: player connect
`server.nim:193-199`. `while epochTime() < connectDeadline` with
`connectDeadline = gameStart + playerConnectTimeoutSeconds` (180 by default,
`sim_config.nim:69`), 200 ms sleeps, early break when `playerSockets.len >= numAgents`. Bounded;
no blocking read. Note line 654-655. *Observed.*

### F34 — MATCH: the LLM batch
`llm.nim:600` passes `client.timeoutSeconds` (= `llmTimeoutSeconds`, default 20,
`sim_config.nim:64` / `llm.nim:91`) to `curly.makeRequests`. In `/root/.nimby/pkgs/curly/src/curly.nim:711-760`
that value is set as each request's `rw.timeout`, and the worker at `curly.nim:416-417` fails a
request whose `secondsSinceLastUpdate >= request.timeout`. `makeRequests` blocks only until every
request has a response or an error. *Observed + inferred* (the bound is per-request idle time, so
a batch is bounded at ~20 s of no-progress per seat, not a hard 20 s wall on the batch).

### F35 — MATCH: the play deadline is 0.6 × `episodeTimeoutSeconds`, checked between shifts
`server.nim:29` `PlayBudgetFraction = 0.6`; `server.nim:220-233` reads
`COWORLD_TIMEOUT_SECONDS` and falls back to `config.episodeTimeoutSeconds` (1200) when the env is
absent — the note's exact reasoning (line 332-334). `server.nim:242-250` tests
`epochTime() > playDeadline` at the **top of each shift**, before `decideAll`, and on a hit calls
`endEarly()`, broadcasts, and breaks. With the defaults the deadline is `gameStart + 720 s`.
*Observed.*

### F36 — OBSERVED: exact wall-clock envelope, traced
`gameStart` is taken at `server.nim:189`, **before** the connect wait, so the ≤180 s connect grace
counts against the 720 s play budget rather than adding to it. Once the deadline check at
`server.nim:242` passes, the shift that starts runs to completion: `decideAll` (≤ ~20 s + ~20 s
retry) + `runShift` + up to `minTurnSeconds` (18) of pacing sleep at `server.nim:277-279`. After the
loop, `finishEpisode` (`server.nim:133-180`) sleeps 500 ms, writes two artifacts (each bounded — the
`POST` path uses `curl.post(..., 60)` at `server.nim:126`), then sleeps
`shutdownGraceSeconds` (20) and `quit(0)`. *Inferred* worst case to process exit:
720 + 40 + 18 + 0.5 + ≤120 + 20 ≈ 918 s = 77 % of 1200; the **play** phase itself stops at 720 s =
60 %. The note's own arithmetic (lines 320-327) assumes a ≤30 s connect grace rather than the 180 s
bound and does not count the trailing `minTurnSeconds` sleep or the grace. *Observed + inferred;
untested* (no hosted run in evidence).

### F37 — OBSERVED: one further bounded wait the note's arithmetic does not list
`llm.nim:58` calls `readCogameUri` for `ANTHROPIC_API_KEY_URI`. In
`/root/.nimby/pkgs/bitworld/src/bitworld/runtime.nim:97-115` that is a `CurlPool.get(value)` whose
default timeout is 60 s (`curly.nim:1184-1192`). It runs once, at `server.nim:218`, after the connect
wait and inside the play budget. Bounded. *Observed.*

### F38 — MATCH: the shift-pacing floor is on batch **starts**
`server.nim:259` takes `batchStart` before `decideAll`; `server.nim:277-279` sleeps the remainder of
`minTurnSeconds` measured from that point. Note line 329-331. *Observed.* One consequence: after the
final shift the loop sleeps up to `minTurnSeconds` before re-entering the top and breaking on
`sim.done` (`server.nim:240-241`) — a bounded ≤18 s tail. *Observed.*

### F39 — MATCH: no blocking read on a player socket, and a bad token is refused
`server.nim:328-331` responds `401` for a slot/token mismatch and returns — no upgrade, no hang. The
shift loop never reads from a player socket; it only sends (`server.nim:271-272`). Player frames are
handled asynchronously by mummy's callback (`server.nim:356-417`). Note lines 641, 521-522.
*Observed.*

### F40 — MATCH: the player process exits 0 on any dead socket
`src/chemistry_player.nim:61-69` wraps `socket.receiveMessage()` in `try/except CatchableError` and
breaks on either the exception or `isNone`, then `quit(0)` at line 95 — the raid fix the note
requires (line 661-663). Diffed against `cogame-bullwhip/src/bullwhip_player.nim`: the fork is that
file with the strings renamed, the `role`→`variant` field, and this try/except added. *Observed.*
`newWebSocket(url)` at line 48 carries no explicit connect timeout — same as the starter. *Observed.*

### F41 — MATCH: shutdown order
`server.nim:133-180` — `final` to every player socket, last global frame, `sleep 500`, write
`results.json`, write the replay, log, `sleep(grace * 1000)`, `quit(0)`. The HTTP server runs on the
main thread (`server.nim:436-438`) and this runs on the game thread, so `/healthz` and `/global`
keep answering through the grace. Exactly the note's order (line 657-661). *Observed.*

---

## 5. String truncation

### F42 — MATCH: rune-safe truncation at 80 / 320 / 200
`sim_types.nim:264-271` — `cleanText` strips, returns early when `runeLen <= limit`, else
`runeSubStr(0, limit - 1) & "\u2026"` (80 runes total at the say cap). `sayText`
(`sim_types.nim:273-275`) folds `\n` and `\r` to spaces first; `notesText` (277-278) and `errorText`
(280-281, cap 200) are the same path. `MaxSayLen = 80`, `MaxNotesLen = 320`, `MaxErrorLen = 200` at
`sim_types.nim:40-43`. Note lines 413-421. *Observed.*

### F43 — MATCH: every string reaching the replay goes through it
- LLM reply: `llm.nim:476-477` on parse, then again at `sim.nim:427-428` in `normalizeOrder`.
- Scripted `say`: `scripted.nim:92, 102, 121, 127`.
- Captured LLM errors: `llm.nim:467, 484, 492, 501, 535, 541, 544, 548, 551, 560, 613` all wrap
  through `errorText`.
- The `order` event carries only the already-cut `final.say` / `final.notes` (`sim.nim:449-450`),
  and `events.nim:108-109` writes them straight out — `events.nim:61-62` states the invariant.
- The inbound player prompt is cut rune-safely at `server.nim:388-389`
  (`prompt.runeSubStr(0, MaxPromptLen)`), though it never reaches the replay.
*Observed.*

### F44 — MATCH: a test feeds multi-byte input at the cap and asserts valid UTF-8
`tests/test_replay.nim:22-31` feeds seat 3 a `say` of 180 multi-byte runes and `notes` of 600 every
shift; `tests/test_replay.nim:102-116` re-reads the recorded bytes and asserts
`validateUtf8 == -1`, `runeLen <= MaxSayLen/MaxNotesLen`, **and** that at least one recorded pair sat
exactly at both caps (`sawLong`). `tests/test_sim.nim:331-342` covers `sayText`/`notesText`/
`errorText` directly. Checklist item 9. *Observed.*

---

## 6. The replay writer (`chemistry.replay.v1`)

### F45 — MATCH: the document is self-sufficient and carries every field the note lists
`src/chemistry/replays.nim:62-91` writes `protocol`, `game`, `gameVersion`, `seed`, `names`
(aliases), `policyNames`, `colors`, `config` (`sim_config.nim:203-250` — variant, grid, cell,
shifts, ticksPerShift, cycles, reactors with cells + feedstocks, vents with cells + inert, homes and
every rule constant), `frames`, `series.charge`, `beats`, `events`, `results`. The note's `walls`
key (line 603) is absent, but `room.nim:32-42` derives walls deterministically from `RoomCols`/
`RoomRows` + `PillarCells`, and the viewer rebuilds the room with `buildRoom(data.config)`
(`replay-viewer/chemistry_replay.nim:79`), so no server round-trip is introduced. *Observed.*

### F46 — MISMATCH: frames and the charge series start at tick 1, not tick 0
`sim.nim:359` increments `tick` before any step and `sim.nim:272-277` records after them, so
`frames[0].tick == 1` and `series.charge[0][0] == 1`. The note's replay example shows
`"frames":[{"t":0,…}` and `"series":{"charge":[[0,3,3,3],[1,3,3,3],…]}` (lines 608-612). Frame
**count** still equals ticks played (`tests/test_replay.nim:61-62`), and
`tests/test_replay.nim:64` asserts `t >= 1` — i.e. the tests encode the code's convention.
*Observed.*

### F47 — OBSERVED: the eight shift-1 `order` events sit at tick 0, before the first frame, and can
never reach the viewer's feed
`server.nim:263-264` calls `applyOrder` before `runShift`, so at the first boundary
`sim.tick == 0` and `emit` stamps `tick = 0` (`sim_state.nim:73-76`). The viewer's per-frame event
window is `eventsBetween(fromTick, toTick)` with `tick > fromTick` (`replays.nim:228-235`), and the
first frame is tick 1, so `t == 0` rows are never returned; the load packet is built with an empty
event array (`chemistry_replay.nim:100`). *Consequence, inferred:* the feed shows no `order` rows for
shift 1. The broadcast tracker is unaffected — `broadcast.nim:74-77` includes every event with
`tick <= upto`, so `roster[].say` / `roster[].job` do carry shift 1. *Observed.*

### F48 — MATCH: strict UTF-8, one document, and the size ceiling
`replays.nim:77` serialises with Nim's `$` over a `JsonNode`, and every embedded string has already
been rune-cut (F43). `tests/test_replay.nim:42-43` asserts `validateUtf8(raw) == -1` on the bytes
read back from disk; `tests/test_replay.nim:118-119` asserts `< 8 MiB` (note line 626).
`docker_smoke.sh:317-324` independently re-decodes the CI replay as UTF-8 JSON. *Observed.*

### F49 — MATCH: the event vocabulary
`events.nim:11-24` declares exactly the thirteen kinds the note tables (line 565-579), and
`events.nim:60-123` emits exactly the fields the note lists for each — including `rx: ""` for an
off-pad drop (`events.nim:75`), `by` on `react`/`restart`, `lost` on `spoil`, and the full
`order` row (`seat, shift, job, sp, rx, source, clamped, say, notes, latencyMs`). *Observed.*

---

## 7. The viewer

### F50 — MATCH: `config.nims` link flags and the worker bootstrap are the same starter's, and they
agree
`diff` against `/workspace/starters/coworld-ctf/replay-viewer/config.nims` shows only the emitted
name, the export-list rename, the dropped `_ctf_mismatch_tick`, and comment text. There is **no**
`-s MODULARIZE=1` and no `EXPORT_NAME` (`replay-viewer/config.nims:42-54`), and
`replay-viewer/static_replay_worker.js:8,162` declares `var Module = {}` and
`Module.onRuntimeInitialized = …` — the matched non-MODULARIZE pair. The **built** module confirms
it: `replay-viewer/dist/chemistry_replay.js` contains `var Module=typeof Module` and one
`onRuntimeInitialized`, with no factory. `tests/test_broadcast.nim:303-335` asserts the pairing.
Checklist item 13's third bullet. *Observed.*

### F51 — MATCH: `static_replay*.js` are verbatim apart from the three permitted changes
`diff` against the starter yields exactly: the added
`document.documentElement.setAttribute('data-replay-error', …)` in `showFailure`
(`static_replay.js:15-18`), the removal of the `setMismatchTick` helper and its two call sites, the
worker-name string `'chemistry-static-replay'` (line 165), and the `ctf_*`→`chemistry_*` export
renames in the worker plus `importScripts('./…chemistry_replay.js')` (worker line 210). The success
signal `document.documentElement.setAttribute('data-replay-loaded', 'true')` is the starter's own,
at `static_replay.js:140-141`, set when the worker reports `loaded` — after the runtime rendered and
`ingestPacket()` succeeded (worker lines 120-133) — and immediately before
`requestAnimationFrame(animate)`. `dist/` copies are byte-identical to the sources. Note lines
704-713; checklist item 13's second bullet. *Observed.*

### F52 — MATCH: the wasm entry mirrors the starter's structure and reads `meta` from the load packet
`replay-viewer/chemistry_replay.nim` exports `chemistry_load_replay/_frame/_input/_packet_ptr/_len/
_error_ptr/_len/_stage_ptr/_len` (lines 87-160), keeps `stampStage` (27-31) and
`emscripten_exit_with_live_runtime()` (162-173), drops `ctf_mismatch_tick`, and at lines 63-70 sends
the whole-timeline chrome (`beats` + `lead`) **only** on the load packet, never by re-deriving via
`packetAt(0)` — the matrix-games rule the note cites (line 705). *Observed.*

### F53 — MATCH: `client/chrome_common.js` is byte-identical to the starter's
`cmp` against `/workspace/starters/coworld-ctf/client/chrome_common.js` reports no difference; md5
`80ea4eb19cee21cb61fb1f009f1f45ab` on both. `tests/test_broadcast.nim:292-301` pins the SHA-1.
Checklist item 14's first bullet; note line 720. *Observed.*

### F54 — OBSERVED: `client/replay_broadcast.html` is the starter's page with a banner-marked block
appended, but the edits inside the inherited region are broader than the note's "these three, and
no others"
The banner `CHEMISTRY additions to the inherited coworld-ctf chrome` is at line 1826; everything
after it is new (500 lines). The inherited region is 1825 lines against the starter's 4165. Diffing
lines 1-1825 against the starter (21 hunks) shows:
- **On the note's list** (line 729-740): `#viewpanel` + children, `#fpv` + children, `#povBadge`,
  `#mmwarn` and their CSS and JS branches; CSS section "4b. VIEW CONTROLS" gone entirely while
  sections 1, 2, 3, 5, 6 remain at the same offsets (`replay_broadcast.html:150, 437, 469, 528, 711`
  vs the starter's `150, 437, 469, 834, 1035`); the `CYCLE CHARGE` re-lettering
  (`replay_broadcast.html:1200`); `#lockerroom { pointer-events: none; }`
  (`replay_broadcast.html:1854`).
- **Not on the note's list**: the `<title>` (line 6); `BOARD_W/BOARD_H` 1235×659 → 1536×864
  (line 1505); the locker-room `LK_BOTS` table rewritten from four CTF teams to the eight chemistry
  colours (lines 1359-1376) plus the caption/prep-talk literals (lines 1148, 1150, 1415-1422);
  `onFirstFrame`/`onTransform` reduced to drop `syncViewUi` (lines 1535-1536); and, largest, the
  starter's own game renderers — `renderScorebug`, `renderClock`, `applyEvent`, `renderEndcard`,
  `ingestBeats`, `ingestCapHearts`, `renderPov`, `renderMismatch`, `ingestFpMap` — replaced in
  `onFrame` by `CHEM_HOOKS.*` delegation (lines 1609-1628) with their ~1400-line bodies deleted
  (hunk `@@ -2065,1409 +1633,9 @@`) and a `window.CHEM` bridge published at lines 1800-1818.
Some of these are the note's own "the JS branches that touch them" allowance for the removed
elements (`renderPov`, `renderMismatch`, `ingestFpMap`, `syncViewUi`); the scorebug/clock/feed/
endcard/beats hook-out is a re-wiring the note's edit list does not mention. The note's promise is
"The only edits inside the starter's own markup/script are these three, and no others" (line 728).
`tests/test_broadcast.nim:175-203` checks that the listed ids are gone and that a list of kept ids is
still present, but does not check that nothing else changed. *Observed.*

### F55 — MATCH: the transport rules, checked in the page
(a) `relayout()` at `replay_broadcast.html:1752-1796` sets `--hudscale`, `--topband` and `--band`
on `document.documentElement` (lines 1787, 1792-1793), which is where `--u` and
`#board`/`#endcard` read them (lines 40-42, 96-98, 112). (b) Nothing the game block adds sits in the
band: `#killfeed { bottom: calc(var(--band, 0px) + 10 * var(--u)); }` (line 1955), `#shame`
`bottom: calc(var(--band,0px) + 118*var(--u))` (line 1935), `#roster`/`#bannerlane` hang off
`--topband` (lines 1897, 1956). (c) `#endcard` is `inset: var(--topband) 0 var(--band) 0` /
`bottom: var(--band, 0px)` (lines 712-723), is shown with `#endcard.on` (line 734) via
`card.classList.add('on')` (line 2278), and is removed on any frame whose phase is not `gameover`
(line 1628) — and `chemistry_replay.nim:58-59` computes `phase = "gameover"` only when
`currentTick() >= maxTick()`, so every backward seek re-enters `playing` and takes the card down.
(d) beats are labelled `<button>`s with a click that seeks — see F56. Checklist item 14's third
bullet. *Observed.*

### F56 — OBSERVED: beat markers are the game block's own buttons, not `chrome_common.markBeat`
markers, so the `?spoilers=0` gate does not reach them
`replay_broadcast.html:2183-2209` (`buildChemBeats`) creates `<button type="button"
class="beat-marker chem <kind>">`, positions it on the scrub track, gives it a `title`/`aria-label`
and a visible `.lab` for every kind but `shift`, wires `click → C.seek(beat.t)` (lines 2202-2205),
and appends it directly to `#scrub` (line 2206). CSS exists for all five emitted kinds — `shift`,
`cold`, `restart`, `famine`, `gameover` (lines 1986-1991) — plus the shared `.beat-marker.chem`
rule; the base `.beat-marker` positioning rule is the starter's (line 603). The name is
`buildChemBeats`, never `markBeat`, per the note (line 750-751), and
`tests/test_broadcast.nim:230-289` enforces that with a scope-duplication scan.
The consequence: `chrome_common.js`'s spoiler gate iterates `markerEls`
(`chrome_common.js:489-497`), which is populated only by `renderBeatMarkers`
(`chrome_common.js:550-561`). The game block never calls `markBeat`/`renderBeatMarkers`, so its
buttons are not in `markerEls` and `?spoilers=0` leaves every beat visible from the first frame. The
note claims "`?spoilers=0` still holds beats back until the playhead reaches them" (line 763).
The checklist's own parenthetical names `chrome_common.markBeat(tick, kind, team, label)` as the
mechanism; the starter's `markBeat` takes three arguments and produces non-clickable `<div>`s
(`chrome_common.js:538-561`), so using it would not have produced clickable labelled buttons.
*Observed.*

### F57 — MATCH: `#viewpanel` is removed, not hidden
No `zoomAt`, `setZoom`, `attachMinimap`, `minimap`, `zoombar` or `viewpanel` identifier survives
anywhere in `client/replay_broadcast.html` outside the banner comment's prose (lines 1834-1836).
`tests/test_broadcast.nim:194-202` asserts the ids are absent. The note's zoom decision (lines
735-738) and checklist item 14's fourth bullet — the 32×18 board is fixed and always fits.
*Observed.*

### F58 — MATCH: the 360 px rules
`replay_broadcast.html:1861` carries `.plate-name, .plate .team-name { flex: 1 1 auto;
min-width: 3.2em; }`; `replay_broadcast.html:2000-2004` hides `#roster .chip .pol` under
`@media (max-width: 640px)` (so a chip degrades to `DRAM 14`) and caps the shame panel at its first
three rows (`#shame .row:nth-child(n+5) { display: none; }` — child 1 is `.title`, so rows 1–3
survive); `#stage.tiny` is toggled at `boardW <= 620` in `relayout()` (line 1789) and also hides
`.pol` (line 2005). `tests/test_broadcast.nim:225-228` pins the first two. Checklist item 11; note
lines 805-809. *Observed.*

### F59 — MATCH: the drawn board, and the two name spaces on the spectator side
`src/chemistry/global.nim:252-369` emits the baked ground once (object 40, z −32768), the vents, the
vats at one of three charge states (`global.nim:237-240`), a reaction flash derived from the recorded
cooldown, loose molecules, food (with a `food_ripe` sprite in the last 48 ticks,
`global.nim:316-317`), each cog's body/carry sprite, **the carried molecule drawn above the head**
(`global.nim:356-357`, `py - 22`) and **the alias under the feet** (`global.nim:358-364`,
`py + CellPx - 4`) — the idea's requirement (note line 770-772). The chrome frame carries the alias
in `roster[].name` and the policy name in `roster[].pol` (`broadcast.nim:171-189`), and the roster
strip renders `pol` only where it differs from the alias (`replay_broadcast.html:2140-2143`).
Checklist item 4. *Observed.*

### F60 — MISMATCH: the momentum strip's normalisation, and `notes` is never drawn
- `replays.nim:237-255` emits `lead = {teams:[…], pts:[[t, charge…]]}` in exactly the shape
  `ingestLeadSeries` reads (`chrome_common.js:453-472`), so that file needs no change — the note's
  claim (line 799-801) holds. But the note also says each line is "normalised by `chargeMax`"
  (line 798). The unmodified `renderMomentum` normalises the ≥3-team branch by the **peak observed
  value** (`chrome_common.js:794-798`) and, for **two** cycles, draws a two-sided lead **diff**
  around a midline (`chrome_common.js:744-792`) rather than one line per cycle. *Observed.*
- The note says `notes` is "drawn only in the feed's expanded row" (line 583). The string `notes`
  does not appear anywhere in `client/replay_broadcast.html` after the banner; `applyChemEvent`'s
  `order` case (lines 2230-2241) renders `say` and the `auto` badge only. *Observed.*
- Minor, same area: `leadSeries` keeps a point every `ticksPerShift div 2` ticks (`replays.nim:247`)
  where its own comment and the note say "one point per shift boundary".
- Minor: the live `/global` chrome never sets `lead` — `server.nim:69-92` leaves
  `ChromeInput.lead` nil — so the momentum strip is empty for a live spectator and populated only in
  the replay bundle (`chemistry_replay.nim:67-69`). The note describes the strip under §Viewer
  without distinguishing the two. *Observed.*

---

## 8. The manifest

### F61 — MATCH: `num_agents: 8` in all four variants and in the certification fixture
`coworld_manifest_template.json:439, 478, 517, 556` (variants) and `:593` (certification).
Every variant also carries `description` (`:437, 476, 515, 554`) and the eight aliases in slot order
in `players` (`:445-470, 484-509, 523-548, 562-587`); `certification.game_config.players` and
`certification.players` are both length 8 (`:602-627, 629-654`). Asserted by
`tests/test_manifest.nim:101-123`. Checklist item 6. *Observed.*

### F62 — MATCH: static viewer, secret env, docs shape, both protocols
`"replay_viewer": {"bundle": "static-replay-viewer"}` at `:14-16`;
`"env": {"ANTHROPIC_API_KEY_URI": "secret://coworld/chemistry/anthropic_api_key"}` at `:25-27`;
`game.docs` is `{"readme":{"type":"text","value":…},"pages":[{id,title,content:{type,value}}×2]}` at
`:360-383`; `game.protocols.player` **and** `.global` are both `{"type":"text","value":…}` at
`:384-393`. No `/client/replay` path exists anywhere in the repo (grep). Checklist items 3 and 10;
note lines 845-874. *Observed.*

### F63 — MATCH: config_schema bounds and derivation
`required: ["tokens"]` (`:34-36`), `additionalProperties: false` (`:33`), and both array properties
(`tokens` `:38-47`, `players` `:48-66`) carry `minItems`/`maxItems`; every array in
`results_schema` does too, with `reactions` capped at `maxItems: 3` (`:320-328`). Every field the
note lists at lines 852-862 is present with the note's bounds and defaults, and
`tests/test_manifest.nim:88-99` cross-checks the property list against what `sim_config.nim` reads.
The image placeholder `{{CHEMISTRY_IMAGE}}` is the one derived from `compose.yaml`'s service name
`chemistry` (`compose.yaml:2`), asserted at `tests/test_manifest.nim:37-43`. *Observed.*

### F64 — MATCH: the certification fixture
`:592-654` — `num_agents 8, seed 7, cycles 3, shifts 6, ticksPerShift 60, distractorPeriod 6,
distractorGroundCap 12, minTurnSeconds 0, playerConnectTimeoutSeconds 180`, and a seat mix of
2 × `chemistry-player`, 4 × `chemistry-courier`, 2 × `chemistry-freeloader` — every declared
`player[]` id seated at least once (`tests/test_manifest.nim:124-130`). 6 × 60 = 360 ticks = 15 s at
24 fps, asserted to sit between 12 and 25 s at `tests/test_manifest.nim:132-141`. Note lines
897-907. *Observed.*

---

## 9. Workflows and scaffold

### F65 — MATCH: CI is green on `main` at the reviewed sha, with the gating steps present and run
`gh run list -R Metta-AI/cogame-chemistry --branch main -w ci.yml` → run **32813430266**,
conclusion **success**, `headSha 2c34a025c4968c48918bc619caab9e44360a9c5c` (verified via
`gh run view … --json headSha`). All three jobs succeeded; `wasm-viewer` `needs: docker-smoke`
(`.github/workflows/ci.yml:212`) and its step list includes both
`Load the bundle in a real browser` and `Load the worst-case renderer fixture`, each `success`,
neither `continue-on-error`. Log evidence:
- `{"loaded":true,"ms":345,"clock":"SHIFT 4 / 6 TICK 242 OF 360",…}`
- `soak: 10s of playback kept advancing ("1 / 359" -> "193 / 359" -> "241 / 359")`
- `scrub readouts: 0%="SHIFT 4 / 6 TICK 242 OF 360"  50%="SHIFT 3 / 6 TICK 198 OF 360"  100%="FINAL SHIFT OVER"` — three distinct readouts
- `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`
- renderer fixture: `{"loaded":true,…}` and `canvas text: 64 drawn, 0 never inside … 0 ellipsized`
`grep -c "SEAT-COUNT FAIL"` over the full 4610-line run log: **0**. Checklist items 1, 6, 13.
*Observed.*

### F66 — MATCH: no test was loosened during this run
`git log --oneline --all -- tests/` returns exactly one commit, `23389c5`, the initial feature
commit; `git log -p 23389c5..HEAD -- tests/` is empty. No test file has been edited, deleted,
skipped or widened since it was written. Checklist item 1's second half. *Observed.*

### F67 — MATCH: `docker_smoke.sh` enforces the four seat-count invariants plus the second
declaration
`tools/ci/docker_smoke.sh:115-156` — `num_agents` present (`:115-123`), a positive non-bool integer
(`:124-130`), `len(certification.players) == num_agents` (`:134-139`),
`len(certification.game_config.players) == num_agents` (`:140-145`), and `SMOKE_SEATS` (defaulted to
`8` at `:59`, passed explicitly from `ci.yml:184`) cross-checked at `:151-156`. Every message is
prefixed `SEAT-COUNT FAIL:` and raised as `SystemExit`, so the step exits non-zero. The script is
mode `100755` and `ci.yml:166-174` asserts the exec bit before invoking it by path. Checklist item 6.
*Observed.*

### F68 — OBSERVED: the smoke validates `results.json` structurally, not against `results_schema`
`docker_smoke.sh:279-329` asserts the file exists, decodes as UTF-8 JSON, is a non-empty object, and
that `names`/`scores` are each length `seats`; it also asserts every **player** container exited 0
(`:257-274`, the design's test-8 delta over the template, documented at `:42-44`) and copies the
replay to `SMOKE_REPLAY_OUT` (`:342-347`). The note says it "validates `results.json` against the
results schema" (line 975); no JSON-Schema validation is performed. *Observed.*

### F69 — MATCH: `viewer_smoke.mjs` is the template verbatim
`diff /workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs tools/ci/viewer_smoke.mjs` is
empty; md5 `4cd55746bf2a6f50bcb2e18e4fc0272d` on both. *Observed.*

### F70 — MATCH: `policies.json` shape
`tools/ci/policies.json` — four entries, all `"run": "/bin/chemistry-player"`. Champions
`chemistry-foreman` and `chemistry-metabolist` each carry `PLAYER_PROMPT` (the note's champion
prompts, lines 463-479) **and** `"USE_BEDROCK": "true"`; champion #2 (the second `PLAYER_PROMPT`
entry) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Fillers
`chemistry-courier` and `chemistry-freeloader` carry `PLAYER_SCRIPTED`. Asserted by
`tests/test_manifest.nim:143-173`. Checklist item 12. *Observed.*

### F71 — MATCH: the three workflows, the release order, and the placeholder gate
All three are present. `coworld-release.yml` and `coworld-submit.yml` are byte-identical to
`/workspace/coworld-builder/templates/` after substituting `chemistry`/`coworld-chemistry`
(verified by diff). `coworld-release.yml`'s step order is Build the Coworld manifest (`:153`) →
Certify locally (`:167`) → **Upload the policies** (`:206`) → Upload the Coworld (`:304`) → Put the
Coworld secret (`:342`). `ci.yml` is the template plus `--soak 10 --strict-text-bounds` on the
bundle smoke and the whole renderer-fixture step. The checklist's gate
`grep -n '<slug>\|<IMAGE>\|<SEATS>' ci.yml coworld-release.yml coworld-submit.yml docker_smoke.sh
policies.json` exits 1 (no match). Exactly the four documented residues survive: `<cow_id>`/`<sha>`
at `ci.yml:202`, `<run_id>` at `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` at
`coworld-submit.yml:31`. Checklist item 12. *Observed.*

### F72 — MATCH: the build hook carries the `mkdir -p` fix and the renamed tag
`tools/build_replay_viewer.sh:20` runs `mkdir -p "$(dirname "${requested_output}")"` **before** the
`cd`-based containment check at `:22-27`; the image tag is
`coworld-chemistry-replay-viewer-build:$$` (`:32`). Mode `100755`, asserted at `ci.yml:225-236`.
Note lines 557-559. *Observed.*

### F73 — MATCH: `Dockerfile.replay-viewer` file list, assertions, and the dropped league page
`Dockerfile.replay-viewer:23-56` builds the wasm, generates `wire_constants.js`, copies
`broadcast_core.js`/`chrome_common.js`/`font.ttf`/both `static_replay*.js`, splices `index.html`
from `client/replay_broadcast.html`, copies the locker-room art, and asserts fourteen conditions
including `grep -q 'CHEMISTRY additions to the inherited coworld-ctf chrome'` on the emitted
`index.html`. No `league.html` step and no `client/league_replayer.html` in the tree. Note lines
811-819, 911. *Observed.*

### F74 — OBSERVED: the renderer fixture measures text it has itself pre-fitted to the canvas
`tools/ci/renderer_fixture.html` loads the real `client/replay_broadcast.html` and the real
`client/chrome_common.js` (lines 230-253), splices them the way `Dockerfile.replay-viewer` does,
stubs `BroadcastCore` (lines 146-169), and pumps frames whose every seat carries a full-cap 80-rune
`say` and 320-rune `notes` at 360/620/900/1280 px (lines 171-223), setting `data-replay-loaded` at
the end and `data-replay-error` on any throw. It **asserts its own strings are still full-length**
at lines 66-69 — the checklist's requirement. Two facts about what the `--strict-text-bounds` number
covers:
- The board renderer is not exercised: `client/broadcast_core.js` is stubbed out, and in this repo
  that file is 6 changed lines from the starter (`diff`) and draws only `drawImage` — the alias
  labels are baked server-side by pixie (`global.nim:146-161`) and blitted as sprites. That is why
  the **bundle** smoke reported `canvas text: 0 drawn`; the checklist notes `total: 0` "is not
  evidence of anything".
- The 64 canvas strings the fixture reports are drawn by the fixture's own `paintBoard`
  (lines 175-196), which shortens each line in a `while … measureText(line).width > canvas.width -
  68` loop before drawing it. So the strict-bounds count on this page cannot go non-zero for a
  width-related reason. The chrome text the fixture genuinely exercises — feed rows, roster chips,
  plate names, endcard — is DOM, not canvas, and is therefore not counted by `canvas_text` at all.
*Observed.*

---

## 10. The tests, item by item against the note's `## Tests` section

| note item | file | present | notes |
|---|---|---|---|
| 1 sim units + determinism | `tests/test_sim.nim` (342 lines) | yes | F75 |
| 2 bounded orders / legality | `tests/test_baseline.nim` (95) | yes | F76 |
| 3 feasibility oracle (a)–(d) | `tests/test_feasibility.nim` (152) | yes | F77 |
| 4 end-to-end + strict UTF-8 | `tests/test_replay.nim` (187) | yes | F78 |
| 5 decision layer | `tests/test_llm.nim` (177) | yes | F79 |
| 6 manifest | `tests/test_manifest.nim` (173) | yes | F61-F64, F70 |
| 7 chrome frame + scope duplication | `tests/test_broadcast.nim` (340) | yes | F80 |
| 8 docker-smoke | `tools/ci/docker_smoke.sh` | yes | F67, F68 |
| 9 wasm-viewer executed | `.github/workflows/ci.yml` | yes | F65, F74 |

### F75 — MATCH with one gap: `test_sim.nim`
Every item the note lists at lines 926-934 has a test: reaction preconditions (`:59-83`), yield over
charge 0..12 post-increment (`:85-94`), cold start 3+3 with no food (`:96-106`) and the one-short
case (`:108-114`), decay + `cold` at the crossing (`:126-141`), rot at `foodLifetime` (`:143-153`),
vent N/E/S/W order and the ground-cap gate (`:156-177`), `carryCap 1` (`:186-196`), move cooldown
(`:198-213`), two cogs cannot share a cell and the lower slot wins (`:215-232`), misdrop
(`:234-250`), spill-ring ordering (`:253-275`) and the `spoil` path (`:277-286`), BFS determinism
(`:47-56`), and `gameHash` equality twice in one process (`:302-308`) and across three fresh
`initSim`s (`:310-318`) after 720 ticks. Gap: the note says the misdrop test asserts the counter
"increments the right seat" — it does (`:245-246`); the note's "reactionCooldown" is not in its own
list but is covered at `:116-123`. The "fresh server" is a fresh `initSim`, not a re-launched
process (`:311-313` says so). *Observed.*

### F76 — OBSERVED: `test_baseline.nim` differs from the note in two measurable ways
It runs 12 seeds × all four variants × both baselines to the natural end and asserts the order enums
and variant legality (`:28-44`), in-bounds/on-floor/no-shared-cell/non-negative counters/charge ≤
`chargeMax` (`:46-65`), that `lastAction` is one of the seven vocabulary values (`:55-56`), and that
neither baseline raises. Differences from the note (lines 936-940):
- The per-tick action check is sampled at shift boundaries (`checkState` runs after `runShift`,
  `:84-85`), not on every tick.
- `check order.say.len <= MaxSayLen * 4` (`:39`) is a **byte** bound with 4× slack, not a rune
  bound; the rune bound is asserted elsewhere (`test_replay.nim:112-113`,
  `test_broadcast.nim:136`).
- The timing assertion is `worstShiftNanos < 1_000_000 * 8` = 8 ms (`:95`) while the comment above it
  and the note both say "no more than 1 ms per shift"; the timed region is all eight seats' decisions
  (`:77-83`), so the bound reads as 1 ms per seat.
- Per F17 the twelve seeds are twelve identical episodes.
*Observed.*

### F77 — MATCH: `test_feasibility.nim` implements gates (a)–(d) as written
(a) `:82-98` — all-courier, ≥10/12 seeds with every reactor `charge >= 1`, `foodMade >= 40` and every
seat `>= 3`, **plus** an unconditional `ending == shift_limit` / `reason == complete` on every seed
and variant (stricter than the note). (b) `:100-117` — 6 couriers + 2 freeloaders, freeloader mean >
courier mean, on all four variants. (c) `:119-132` — all-freeloader food < 15 % of all-courier, **or**
famine on all 12 seeds. (d) `:134-152` — the test-only `nearest` kernel (`:40-63`, defined in the
test file and nowhere in `src/`) scores below `0.6 ×` the courier mean on
`three-cycles-plentiful-distractors`. The file's header records that no constant repair was needed.
This is also the checklist-item-7 "scripted baseline plays full episodes legally" evidence, together
with F76. Note lines 284-300, 941-943. *Observed.*

### F78 — MATCH: `test_replay.nim` asserts every clause the note lists
`validateUtf8 == -1` on the bytes read back (`:42-43`); parses; `protocol == "chemistry.replay.v1"`
(`:47`); `frames.len == ticksPlayed` and `series.charge.len == ticksPlayed` (`:61-62`); every event
tick in `0..ticksPlayed` (`:71-73`); at least one `take`, `drop`, `react`, `eat` (`:77-80`); exactly
`shifts` `shift` events and exactly one `end` (`:81-82`); `results.scores.len == 8` (`:92`);
`reason ∈ {complete, deadline, forfeit}` and `ending ∈ {shift_limit, famine, deadline, forfeit}`
(`:95-97`); `< 8 MiB` (`:118-119`); and the multi-byte cap assertions of F44. A second suite
(`:135-187`) drives exactly the calls `replay-viewer/chemistry_replay.nim` makes — parse → hydrate →
`buildBoardPacket` + `buildStateJson` for 60 frames, plus seek/transport commands. Note lines
944-952. *Observed.*

### F79 — OBSERVED: `test_llm.nim` covers the note's list, with the four failure modes collapsed into
one
Covered: `extractJsonObject` on fenced and prose-prefixed replies (`:19-30`); unknown job invalid
(`:35-37`); `supply` without reactor invalid (`:43-46`); an absent reactor clamped with
`clamped == true` (`:59-66`); a feedstock the reactor does not take accepted (`:68-75`); a broken
transport producing `courier` orders with `source == "fallback"` without raising (`:103-127`); and
`RequestBatch.len == openSeats == 8` on shift 1 via `client.lastBatchSize` (`:120`) — the note's
explicit assertion (line 957-958). Differences from the note (line 955-958):
- The note lists "times out, 429s, 403s or returns junk" as four stubbed transports; the test uses a
  single closed port (`http://127.0.0.1:9/bedrock`, `:106`) and says so in a comment (`:104-105`).
  The 401/403 `disabled` latch and the 429 path have no direct test.
- Nothing asserts that the retry happened **exactly once** — only that the end state is a fallback.
- `:81-82` bounds `say`/`notes` in bytes at `cap * 4`; the rune bound is asserted in
  `test_replay.nim` and `test_broadcast.nim`.
*Observed.*

### F80 — MATCH: `test_broadcast.nim` covers the note's item 7 and adds viewer-provenance pins
`teams` keys are exactly the present cycles, each `policies: [<Cycle name>]`, `lives == charge`
(`:102-116`), two cycles → two plates (`:117-123`); `roster[]` is 8 entries with alias in `name` and
policy in `pol` (`:125-136`); `lead` is `{teams, pts:[[t, …]]}` with `reactors.len + 1` per row
(`:138-144`); `beats` carry only the five declared kinds (`:146-150`); `over` on the terminal frame
with the ending string (`:152-159`); every feed string inside its rune cap (`:161-166`); and the
scope-duplication test collects the chrome's `var X = C.X` alias list and every `function` **declaration**
in the game block over a comment-stripped copy and asserts they are disjoint (`:242-289`). The
`viewer provenance` suite (`:291-340`) pins the `chrome_common.js` SHA-1, the absence of
`MODULARIZE`/`EXPORT_NAME`, the presence of `Module.onRuntimeInitialized`, every emscripten flag the
note names, all nine `_chemistry_*` exports, the absence of any `mismatch` residue, and both
`data-replay-loaded` / `data-replay-error` markers. Note lines 966-972. *Observed.*

---

## Traced and consistent (verified, nothing to report)

- `src/chemistry.nim:30-47` — the seed is randomised **before** `config.update` and only when the
  runtime config does not pin one (`seedPinned`, `:21-28`); `config.update` never touches `seed`
  unless the JSON carries it (`sim_config.nim:122-123`). Note line 652.
- `src/chemistry/server.nim:419-424` — the five routes the note requires and no others:
  `/healthz`, `/client/global`, `/client/player`, `WS /global`, `WS /player`. No `/client/replay`.
- `server.nim:369-371` — mummy `Ping` frames are answered with a `Pong`, which the note's
  certification lesson requires.
- `server.nim:60-63` + `Dockerfile.replay-viewer:31-34` — the same three splice markers are used by
  the live server (`staticRead` + `replace`) and by the bundle build (`sed`), so both serve the same
  page from one source.
- `sim_config.nim:105-201` — every config field is clamped to the manifest's declared bounds;
  `numAgents` is clamped to `1..8`; `players` is padded/truncated to 8 so the seat records always
  exist.
- `sim_config.nim:74-83` — `variantId()` is derived from `cycles` + `distractorPeriod` rather than
  carried as a field, and `tests/test_manifest.nim:113-117` re-derives it from each variant's own
  `game_config`, so a manifest variant cannot claim an id it does not play.
- `sim_state.nim:144-166` — the frame's `f` triples record `foodLifetime - age` as `ttl`, matching
  the note's `[x,y,ttl]` and driving the viewer's ripe-pulse sprite at `global.nim:316`.
- `replays.nim:93-134` — `parseReplayBytes` rejects an unknown protocol, a missing `config` block and
  an empty `frames` array, and back-fills `names`/`policyNames`/`colors` to 8.
- `broadcast.nim:63-115` — the tracker re-derives every cumulative counter from the event log up to
  the playhead on every frame, so a seek needs no separate code path; `delivered` counts only drops
  with a non-empty `rx`, `hoard` only drops on the seat's own home.
- `.gitignore` — `replay-viewer/dist/`, `dist/`, `scratch/`, `__pycache__/`, `nim.cfg` and
  `.apipush.py` are ignored; `git status --porcelain` is clean and `git ls-files` is 115 files, so no
  build artifact is committed. `ci.yml:85-102` regenerates `nim.cfg` from the runner's package tree.
- `data/` — 44 tracked files (floor, wall, pad, home, 3 vat tints × 3 states, 5 vents, 5 molecules,
  food + food_ripe, flash, 8 cog bodies × 2 poses, font + licence), plus 9 tracked locker-room
  assets under `client/art/lockerroom/`. `scripts/art/gen_chemistry_art.py` is committed.
- `README.md`, `docs/plans/2026-08-25-chemistry-design.md` — the latter is byte-identical to the run's
  `design.md`.

## Could not determine

1. **Whether the note's "one parallel batch" holds against a live Bedrock sidecar.** The batch
   construction is a single `makeRequests` call (F23) and the closed-port test proves the fallback
   path, but no run in evidence exercised a real 200 response — `docker_smoke.sh` runs without
   `ANTHROPIC_API_KEY` by design (`:199-204`, and the CI log line "no ANTHROPIC_API_KEY: the game
   must complete on its scripted baselines"). Settled by a phase-60 league episode's per-seat
   `order.source` distribution, or by a manual run with credentials.
2. **Whether F27 (an unconnected seat is sent to the LLM) can occur in the hosted path.** It requires
   credentials present **and** a seat that never delivers a `prompt` frame. The platform normally
   starts every player pod, so this may be unreachable in practice. Settled by a hosted episode with
   a deliberately failed player pod, or by reading the dispatcher's seat contract.
3. **Whether the feed renders any `order` row in a hosted replay.** The CI smoke reports
   `feed_lines: 0` at both sample moments. Two innocent explanations are visible in the code — rows
   self-expire after `dwellFloor('feed')` (`replay_broadcast.html:1653-1655`), and shift 1's rows are
   structurally missing (F47) — but I could not distinguish "expired" from "never pushed" from the
   log alone. Settled by a `viewer_smoke.mjs` sample taken within a second of a shift boundary, or by
   reading `viewer-smoke.png` from the run's artifacts.
4. **Whether `--strict-text-bounds` on the bundle smoke can ever fail for this repo.** It reported
   `canvas text: 0 drawn` (F65), which the checklist itself says is not evidence. The only text the
   product draws on the board is a pixie-baked sprite (F59), which `canvas_text` cannot see. Settled
   by a screenshot review of `viewer-smoke.png` at 360 px, which is outside what I can read from the
   log text.
