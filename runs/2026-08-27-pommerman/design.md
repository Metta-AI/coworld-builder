# cogame-pommerman — design note (2026-08-27)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/<game>/` module split with `sim.nim` re-exporting the sim modules and
`sim_types.nim` owning `GameVersion`, the flatty wire types and every rune cap; the mummy server
implementing the Coworld contract; the `decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` /
`control.nim` commander layer with its one-parallel-batch-per-turn, its two bounded deadlines, its
rune caps and its repair-don't-reject fallback ladder; the binary `COWLD…` replay of *inputs plus a
per-tick `gameHash`*, re-simulated by **the same sim module** compiled to wasm by
`replay-viewer/config.nims`; the `client/` broadcast chrome; nimby + `Dockerfile` +
`Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh`; and the four-shard Nim test suite.
The starter is chosen by game shape — **a real-time grid loop with rules written for this coworld**
is the first row of the starter table — and the precedent for forking it into an integer grid game is
now several deep (knights-archers, pistonball, particle-worlds, magent-battle).

**One starter, end to end.** The sim, the server, the commander layer, the tests, the packaging and
**all four viewer files** come from coworld-ctf and nowhere else. No subsystem is spliced in from
another starter; two-starter hybrids are a documented recurring failure (a viewer shell from one
starter over another's emscripten link flags deadlocks silently — cogame-lantern, 2026-08-23).

Where this note departs from coworld-ctf it says so and gives the reason. The departures are: the
rules are Pommerman's, not paintbot's (§Sim module lists what is deleted); the arena is an **11 × 11
integer grid**, so ctf's pixel geometry, procedural map generator, map pool, map editor and mapkit
are deleted; and the game carries a **two-integer private team radio**, which paintbot has no
analogue of and which is the reason this coworld exists.

### Source idea (verbatim)

> Port of Pommerman (NeurIPS 2018 competition) with Bomberland (Coder One) as the modern sibling.
> 11×11 grid, four bombers; place bombs to clear wooden walls and kill opponents; power-ups (extra
> bomb, range, kick). Modes: free-for-all, 2v2 team, and 2v2 team-radio where teammates exchange two
> small integers per tick — an emergent-language channel under fire. Partial observability variant.
> Bomberland adds a larger map, fire shrinking the arena, and a web-replay.
>
> Seats: 4 (FFA or 2v2)
> Motive: zero-sum / team zero-sum with a tiny comm channel
> Policy interface: per-tick move/bomb/radio; LLM possible at ~2 Hz with a decoded board
> Fills gap: 25 Grid Wars is scripted-warrior bombs; Pommerman is live per-tick bombs with a
> constrained radio — tests emergent comm under competition
> Integrity (anti-collusion): FFA collusion (two seats ganging up) is the classic Pommerman exploit
> — prefer 2v2 with server-assigned partners; anonymous aliases.
> Replay plan (watchability): bomb timers and blast ranges drawn; radio messages shown as glyphs over
> the team; 'kicked bomb' highlight.
> Source: github.com/MultiAgentLearning/playground (Pommerman); github.com/CoderOneHQ/bomberland.

### Upstream, and what this coworld takes from it

This is **not** a bit-exact port — it is a Pommerman-shaped game with rules written for this coworld
(coordinator rail, 2026-08-27), so `coworld-ctf` is the starter, not `cogame-moba`. Where a constant
is upstream's it is cited; where it is this coworld's it is stated as such. Upstream is
`MultiAgentLearning/playground`, `pommerman/constants.py` + `pommerman/forward_model.py`.

| Fact | Upstream Pommerman | Here | Why |
|---|---|---|---|
| Board | 11 × 11 | **11 × 11** | adopted |
| Bombers | 4, in the four corners | **4, in the four corners** | adopted |
| Team pairing | agents `{0,2}` vs `{1,3}` (diagonal partners) | **seats `{0,2}` = RED, `{1,3}` = BLUE** | adopted |
| Action space | 6: `Stop, Up, Down, Left, Right, Bomb` | **6, same order and meaning** | adopted |
| Radio | two integers, each in `1..8` | **two integers, each in `1..8`** | adopted |
| Bomb fuse | `DEFAULT_BOMB_LIFE = 10` ticks | **8 ticks** | fits `turnTicks = 4` exactly two command turns |
| Blast strength | `DEFAULT_BLAST_STRENGTH = 2` (own cell + 1 per direction) | **2, same meaning; cap 6** | adopted |
| Flame life | 2 ticks | **2 ticks** | adopted |
| Starting ammo | 1 | **1; cap 5** | adopted, cap added |
| Wooden walls | `NUM_WOOD = 36` | **36** | adopted |
| Power-ups | `NUM_ITEMS = 20`, extra-bomb / incr-range / kick | **20, same three kinds** | adopted |
| Rigid walls | 36, placed at random | **57: a 40-cell rigid border + a 16-cell classic even-lattice + centre-adjacent none** | see §Sim module → Map |
| Map generation | random, then a connectivity repair pass | **4-fold rotationally symmetric, connected by construction** | league fairness: every seat's corner is a rotation of every other's |
| Episode length | `max_steps = 800` | **`maxTicks = 144`, 36 command turns** | the 720 s wall-clock budget (§Decisions) |
| Arena collapse | v2 "collapsing walls"; Bomberland's shrinking fire | **two rings collapse, at ticks 96 and 120** | guarantees the endgame closes inside the tick cap |
| Who acts each tick | the policy, per tick | **a deterministic controller, from a per-turn commander order** | an LLM cannot answer 144 × 4 times inside 720 s (§Decisions) |

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | Where |
|---|---|
| Starter chosen by game shape | `coworld-ctf` — real-time grid loop, new rules (title paragraph) |
| Public `Metta-AI/cogame-pommerman` | §Packaging |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=sapper\|camper`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance; ctf soldier/crown art, `paintbomb.png`, `arena_floor.png`) |
| Two name spaces | §The game (aliases `RED-1/RED-2/BLUE-1/BLUE-2` in-game; real names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (typical 395 s, worst 553 s, hard stop 640 s, worst settle 649 s = 54 %) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 4`, three times, never at a variant top level |
| Simultaneous decisions as one parallel batch | §Decisions |
| Replay bytes self-sufficient | §Server (plus `tools/replay_summary.py`, the strict-UTF-8 JSON view of them) |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |
| Anti-collusion | §The game (2v2 with server-assigned partners, anonymous aliases, exactly zero-sum score, rotationally symmetric map) |

**No `OPEN` section.** The coordinator's rails settled mode (2v2 team-radio), seat count (4) and
observability (full board, private radio); every remaining constant is this note's to pin and is
pinned below. Nothing in the idea is left with two readings that give materially different games.

---

## The game

Four bombers stand in the four corners of an 11 × 11 walled grid packed with wooden walls. They are
two teams of two: **RED** holds the north-west and south-east corners, **BLUE** the north-east and
south-west. Bombs clear wooden walls, wooden walls hide power-ups, and power-ups make your bombs
more numerous, longer-reaching and kickable. A team wins by killing both opponents — including by
tricking them into a blast they cannot outrun. Twice near the end the outer rings of the arena turn
to rigid wall and crush whatever stands on them, so the fight is forced into the middle and closes.

Each seat's policy commands **one bomber**. Every four sim ticks it issues that bomber one order and
sends its **teammate** two integers in `1..8` — a two-symbol private channel with **no meaning the
game assigns**. That channel is the whole point of this coworld: it is an emergent-language link
between two independent policies that were seated as partners by the ladder and have never met.

### Seats, teams, corners, aliases

- **`num_agents` = 4.** Exactly four seats, always, in every variant and in the certification
  fixture. There is no other seating.
- **Teams are fixed by slot parity and assigned by the server**, never chosen by a policy: seats
  **0 and 2 are RED**, seats **1 and 3 are BLUE**. The manifest pins this with
  `slots: [{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"}]`. This is the idea's
  anti-collusion requirement: with server-assigned partners and an exactly zero-sum team score, no
  two seats can raise their joint total by cooperating across the table, which is the classic FFA
  Pommerman exploit. FFA is §Out of scope.
- **Corners**, with `x` the column `0..10` left→right and `y` the row `0..10` top→bottom:

  | Seat | Alias | Team | Corner |
  |---|---|---|---|
  | 0 | `RED-1` | RED | NW `(1,1)` |
  | 1 | `BLUE-1` | BLUE | NE `(9,1)` |
  | 2 | `RED-2` | RED | SE `(9,9)` |
  | 3 | `BLUE-2` | BLUE | SW `(1,9)` |

  Partners sit on a diagonal, as upstream. Because the map is 4-fold rotationally symmetric about
  `(5,5)` (§Sim module → Map), every corner's surroundings are an exact rotation of every other's:
  **no seat has a positional advantage**, and therefore no side-swap game is needed. One game per
  episode.
- **Two name spaces.** In-game, the four seats are **`RED-1`, `BLUE-1`, `RED-2`, `BLUE-2`** and
  nothing else. Those aliases are the only names that appear in an observation, in a prompt, in an
  order, in a `say`, or on a sprite label. The seats' **real policy/player names** (`daveey`,
  `daveey-1`, `Baseline (1)`, `Baseline (2)`) live only in `results.names`, in the replay's join
  records, and in the viewer's scorebug and endcard. `showPlayerLabels` is **false**, as in the
  starter's paintball variant, so no in-board sprite can leak an identity. **A seat cannot learn who
  its partner is**, which is what makes the radio a real coordination problem rather than a
  pre-agreed protocol between two copies of one prompt.

### The board, the bomber, the clock

- Board: 11 × 11 cells. The outer ring (`x == 0 or x == 10 or y == 0 or y == 10`) is **rigid wall**.
  Cell contents are one of: `rigid`, `wood`, `passage`, plus at most one of `{bomb}` and at most one
  of `{extrabomb, incrrange, kick}` and a `flame` timer. One living bomber per cell.
- Bomber state: `alive`, `x`, `y`, `ammo` (start **1**, cap **5**), `blast` (start **2**, cap **6**),
  `kick` (start **false**). A bomber has no hit points: a flame kills instantly.
- Bomb state: `id` (creation order, ascending), `x`, `y`, `fuse` (**8** at placement), `blast`
  (copied from the owner at placement, never updated afterwards), `owner` seat, `velocity`
  (`none|up|down|left|right`).
- Flame: a cell timer, **2** ticks, set at detonation and decremented at the end of every tick, so a
  flame is lethal on the tick it appears and on the one after it.
- Power-ups: `extrabomb` (`ammo += 1`, capped), `incrrange` (`blast += 1`, capped), `kick`
  (`kick = true`, idempotent). Picked up by stepping onto the cell; consumed. A power-up lying in a
  blast cell is destroyed.
- **Tick** = one Pommerman step. **Command turn** = one order round, every `turnTicks = 4` ticks,
  beginning with turn 1 before tick 1. `maxTicks = 144` ⇒ **36 command turns**, which is what the
  wall-clock arithmetic in §Decisions is sized for.
- **Collapse**: let `ring(x,y) = min(x, y, 10-x, 10-y)`. Ring 0 is the permanent border. At tick
  **96** every cell of **ring 1** becomes rigid; at tick **120** every cell of **ring 2** becomes
  rigid. Play ends inside the 5 × 5 block `x,y ∈ [3,7]`.

### Turn and tick structure — the exact resolution order

Per **command turn** `T` (immediately before tick `4·(T−1)+1`), in this order:

1. The engine snapshots the world and builds **all four** seats' observation objects (§Decisions).
2. **Radio delivery.** Each seat's observation carries `radio_from_teammate` = the pair its
   **partner** sent with its turn `T−1` order (`null` on turn 1). It is delivered to that one seat
   and to no other; **the opposing team's pairs are never in any observation.** Delivery is exactly
   one turn late, always, including when the partner fell back (a fallback still sends a pair).
3. All four seats' LLM requests go out as **one parallel batch** (`curly.makeRequests`, the
   starter's `decideAll` shape), attempt-1 deadline `attempt1Ms = 8000`. Scripted seats compute
   locally, instantly.
4. Each seat that timed out, errored, returned non-JSON or returned no usable `order` is retried
   **once**, again as a single batch, `retryMs = 3000`.
5. A seat still without a usable reply gets the **`sapper`** scripted order computed server-side and
   a `fallback` record is written (§Decisions).
6. Orders are installed. A seat that names no `order` **keeps last turn's order** (turn 1's default
   for every seat is `break`). An order whose fields do not validate is **repaired** field by field
   (clamped coordinates, unknown verb → the seat's previous verb, unknown target → nearest living
   enemy) and counted in `ordersRejected` — the starter's `directives.nim` repair-don't-reject rule.
7. `say` (≤ 100 runes) and the accepted order become replay chat records; `notes` (≤ 200 runes) is
   stored and echoed back **to that seat only** next turn; `radio` (two ints, `1..8`) is stored for
   step 2 of turn `T+1`.
8. `turnSpacingMs = 10000` is a floor on the wall clock between consecutive **batch starts**, not a
   sleep on the critical path: the loop keeps stepping ticks while it waits.

Then, for each of the next `turnTicks = 4` ticks, in this order — **this is the whole physics of the
game and nothing else mutates the world.** Every rule reads the snapshot taken in step 1, never a
partially updated world.

1. `tick += 1`. Snapshot the board, the bomber positions and state, every bomb's fuse / position /
   velocity, and every flame timer.
2. **Collapse.** If `tick` is a collapse tick, every cell of that ring becomes rigid; a living
   bomber there dies with `cause: "crushed"`; a bomb there is removed (it does not detonate); a
   power-up there is destroyed; a flame there is cleared. Done first so nothing else acts on a cell
   that is about to be wall.
3. **Choose one action per living bomber**, in ascending seat order, from that seat's current order
   via the controller (§Decisions → "The controller"). The action is one of
   `stay | up | down | left | right | bomb`.
4. **Bomb placement**, in ascending seat order. A bomber whose action is `bomb` places a bomb on its
   own cell iff `ammo > 0` **and** no bomb already occupies that cell; then `ammo -= 1`, the bomb
   gets `fuse = 8`, `blast = ` the placer's current `blast`, `velocity = none`, and the next `id`.
   Otherwise the action degrades to `stay`. A bomber that places a bomb does not move this tick.
5. **Kicked-bomb movement**, in ascending bomb `id`. A bomb with `velocity ≠ none` advances one cell
   in that direction iff the destination is passage, holds no bomb, holds no living bomber and holds
   no flame. Otherwise it stops: `velocity = none`, position unchanged.
6. **Bomber movement**, in ascending seat order, from the snapshot positions:
   1. `stay` and `bomb` do not move.
   2. Destination = current cell + the direction. If it is rigid or wood, the move **fails** (the
      bomber stays).
   3. If the destination holds a **bomb**: iff the mover has `kick` **and** the cell one further in
      the same direction is passage, bomb-free, bomber-free and flame-free, the bomb's `velocity` is
      set to that direction (it starts moving at step 5 of the **next** tick) and a `kick` event is
      recorded. **The kicker does not move this tick** — it may follow next tick. Without `kick`, or
      with the far cell blocked, the move fails.
   4. If the destination holds a living bomber, or a bomber that already moved there earlier this
      tick, the move **fails**. Two bombers targeting the same empty cell: the **lower seat index
      wins**, the higher stays. (Upstream reverts both; a fixed winner is required for a
      re-derivable replay — a documented divergence.) There are no swaps.
   5. Otherwise the bomber moves.
   6. If the new cell holds a power-up, it is picked up and applied immediately and a `pickup` event
      is recorded.
7. **Fuse tick.** Every bomb, moving or not, `fuse -= 1`.
8. **Detonation, with chain reaction.** Let `D` = the bombs with `fuse <= 0`. Repeat to a fixpoint:
   for each bomb in `D` in ascending `id`, its blast cells are its own cell plus, in each of the four
   directions, up to `blast - 1` cells, walking outward and **stopping before** the first rigid cell,
   **stopping at and including** the first wood cell, and passing through passage, power-ups, bombers
   and bombs. Any bomb whose cell is a blast cell and is not yet in `D` joins `D` with `fuse = 0`.
   Iterate until `D` stops growing (bounded: at most one pass per live bomb).
9. **Flames and wood.** Every blast cell becomes flame with `life = 2`. Wood in a blast cell is
   destroyed → passage, a `wood` event is recorded and credited to the owning team of the bomb with
   the lowest `id` covering it; if that wood hid a power-up, the power-up now lies on the cell
   (upstream's rule — it survives the blast that revealed it). A power-up **already lying** on a
   blast cell is destroyed. Every bomb in `D` is removed and its owner's `ammo += 1` (capped).
10. **Deaths, simultaneous.** Every living bomber standing on a flame cell dies — all of them, in
    one step, with no ordering, so mutual annihilation is a real outcome. Each death records
    `killer` = the owner of the lowest-`id` bomb whose blast covers that cell, and
    `cause ∈ {bomb, suicide, friendlyfire, crushed}` (`suicide` = killer is the victim,
    `friendlyfire` = killer is the victim's partner). `kills[team]` increments **only** for a victim
    on the other team; a suicide or a friendly kill increments nothing and still costs the team a
    bomber.
11. **Flame decay.** Every flame `life -= 1`; a flame at 0 becomes passage.
12. Mix the tick into `gameHash` and append it to the replay's hash chain.
13. Evaluate the end conditions.

### Scoring formula and sign

Let `alive[t]` be team `t`'s living bombers when the episode ends, `kills[t]` its kills of the other
team, and `wood[t]` its wooden walls cleared.

```
outcome[t] = +1 if alive[t] > 0 and alive[other] == 0
              0 if alive[t] == alive[other]  (both 0, or the tick cap with equal counts)
             -1 if alive[t] == 0 and alive[other] > 0
             +1/-1/0 by (alive[t] - alive[other]) sign at the tick cap otherwise

teamScore[t] = 100 * outcome[t]
             +  20 * (alive[t]  - alive[other])
             +   1 * (wood[t]   - wood[other])

score[seat] = teamScore[team(seat)]
```

**Higher is better.** Both seats of a team receive the identical team score, so the four seat scores
sum to exactly zero: `2·teamScore[RED] + 2·teamScore[BLUE] = 0` because every term is an
antisymmetric difference. **Exactly zero-sum** is the integrity requirement, and it holds without a
tie-break clause. Range: `100 + 20·2 + 36 = ±176`. The `100 ×` term makes winning dominate; the alive
differential rewards winning without losing your partner; the wood term (at most ±36) is a small,
honest tie-break that rewards the team that actually played the board rather than one that hid in a
corner for 36 turns. `results.scores` carries `score[seat]`, `results.win` carries `score[seat] > 0`,
and **the league ranks by `scores`** (Elo 1000/32 from the head-to-head ordering).

### End conditions and legal `results.reason` values

The **game** ends at the first of:

- **Team wipe** — a team reaches 0 living bombers at the end of a tick. Both at once is a draw.
  `endRule = "wipe"`.
- **Tick cap** — `tick == maxTicks` (144). Settled by living-bomber count; equal counts is a draw.
  `endRule = "tickCap"`.
- **Wall-clock stop** — the engine's own `wallClockBudgetSeconds` (640 s) is reached.
  `endRule = "wallClock"`.
- **Fault** — an unexpected exception. `endRule = "fault"`.

`results.reason` is the starter's closed enum and exactly these three values are legal:

- **`complete`** — the game ended by `wipe` or `tickCap`. The healthy value; the collapse rings make
  it overwhelmingly `wipe`.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds = 640`. The engine stops at the
  current tick, settles by living-bomber count, and still writes results and replay. **Declared
  acceptable** for SPEC §Definition of done check 4. The budget guard below exists so it should never
  fire; the worst modelled episode finishes 87 s early.
- **`fault`** — a caught exception in the sim or the loop. The episode is settled from the last
  completed tick, `results.stopDetail` names it (≤ 200 runes, rune-truncated), artifacts are still
  written. A defect: `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × turnBudgetSeconds > wallClockBudgetSeconds` (i.e. `elapsed > 616 s`), the LLM is
switched off for every remaining turn (all seats fall to `sapper`, microseconds per turn), the
remaining ticks run at full speed, and the episode still ends `complete`. A `budget_guard` record
names the turn it fired. Worst settle after the guard: `616 + 12 (this turn) + 20 (hold + write) =
649 s`, which is **54 % of the 1200 s `episodeTimeoutSeconds`** — inside the 60 % pin with the guard
netted off one worst-case decision, as the poker 2026-08-26 ruling requires.

A seat that never connects, disconnects, or fails every decision **does not end the episode** — its
bomber plays `sapper` and the game runs to its natural end. Nothing a player container does can stop
the clock: `lobbyJoinTimeoutTicks` bounds the lobby and the starter's strike rule stops a silent seat
from consuming the per-turn deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {sapper, camper}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=sapper` (the starter's "anything unrecognised is the published default" rule in
`baselines.nim`). A scripted policy seated as a champion is a failure state.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/pommerman/anthropic_api_key` — the hive
2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` /
`LLM provider is unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game
container only. No `USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM
call.

`src/pommerman_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar: a first registration can land before the seat has an index) — the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"sapper"|"camper"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at **48** runes, then
acknowledge frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3
close-frame race: whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).
**The server logs loudly and names the seat when a seat produces no `register` record by the end of
the lobby** (the grf-football 2026-08-27 scar: a lost register packet made a champion play scripted
for a whole episode with `latency_ms: 0` and no error anywhere); `results.deadSeats` and
`results.policyKinds` carry the same fact.

`src/pommerman/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (via `readCogameUri`) → **none**, in which case the
  client is `disabled = true` and every turn falls back instantly with no network wait, so offline
  certification finishes in seconds.
- Bedrock model candidates: **`us.anthropic.claude-haiku-4-5-20251001-v1:0` only**, `BEDROCK_MODEL`
  pins one. `us.anthropic.claude-sonnet-4-5-20250929-v1:0` and `...-4-6` are deliberately **not**
  candidates — both time out on every sidecar call (raid round 2, 2026-08-23; paintball 0.1.2). With
  no second candidate a 429 sets `throttled` and the seat **fails fast** to the scripted layer for
  that turn instead of burning the turn budget on a retry that cannot land.
- `maxOutputTokens = 900` (not 400 — "cut off at max_tokens"). **No `output_config.effort`** when the
  model string contains `haiku` or `4-5`. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (outermost balanced
  `{…}`, fence-tolerant, tolerant of trailing prose) and `truncateRunes` / `sanitizeSay` kept
  unchanged.

### Cadence, batching, and the wall-clock arithmetic

One command turn every **4 ticks**; **36 turns per episode**. At each turn the server builds **all
four** seats' request bodies and issues them as **ONE parallel batch** — never sequentially; this is
a simultaneous-decision game and serial calls would quadruple the wall clock for nothing. At most 4
calls in flight, at most `4 × 36 × 2 = 288` calls per episode including retries.

```
attempt1Ms                          8.0 s
retryMs                             3.0 s
turnBudgetMs                       12.0 s   (monotonic deadline around the whole turn)
turnSpacingMs                      10.0 s   -> 4 seats x 60/10 = 24 req/min  (sidecar cap: 30)

36 turns x max(spacing 10 s, budget 12 s), absolute worst         = 432 s
   typical (haiku answers in ~3-4 s, so spacing dominates)        = 360 s
144 ticks, 4 bombers, 121 cells, integer Nim, fastMode            =  <1 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400; typical 15 s)   =  15 s   (cap: 100 s)
gameOverTicks 90 hold (15 s at TargetFps 6) + results + replay    =  20 s
                                                                  -------
typical total                                                     = 395 s   < 720 s
absolute worst case (432 + 1 + 100 + 20)                          = 553 s   < 640 s stop
budget guard fires at elapsed > 616 s; worst settle after it      = 649 s   = 54 % of 1200 s
engine hard stop wallClockBudgetSeconds                           = 640 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                             = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 640 and `tests/test_pom_manifest.nim` asserts it. `fastMode: true` in
every variant, as in the starter's paintball variant: seats send no inputs (the server computes every
action), so the Sprite v1 Ready packet's dead-reckoning hazard cannot arise.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turnBudgetMs`, `lobbyJoinTimeoutTicks`,
mummy's socket timeouts on the serve thread (which runs independently of the game loop, so a 12 s LLM
stall cannot drop a connection or stall `/healthz`), the 640 s engine stop, and ctf's `gameOverTicks`
hold before exit — kept so `/healthz` and `/global` keep answering for a bounded grace after
artifacts are written (the lantern 0.1.3 `/global` ping scar).

On a seat's timeout or parse failure: **retry once** in the next batch; on the second failure that
seat's order for that turn becomes the **`sapper`** scripted order computed inside the game (the same
proc the `sapper` baseline uses — imported, never duplicated), its radio pair becomes `sapper`'s, and
a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard, disconnected}`.
`results.fallbackTurns[seat]` counts them.

**No failure mode leaves a bomber unactuated.** The control layer always has an order: this turn's,
else last turn's, else `sapper`'s. A seat that never connects is reported once to
`COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload — exactly
`{"message", "failed_policy_index"}`, nothing else.

**How the episode settles early.** Three independent mechanisms, in increasing severity: the budget
guard (turns off the LLM, episode still `complete`); the collapse rings (the arena is 25 cells from
tick 120, so a wipe almost always arrives before the cap); and the engine's 640 s stop
(`reason = deadline`, written as a **load-bearing `stop` record** — see §Sim module → Determinism).

### Per-seat observation: exactly what is visible and what is hidden

**Visible.** The whole board — terrain, flames, every bomb with its fuse and blast, every dropped
power-up, every bomber's position, ammo, blast and kick flag. This is the shipped v1 mode: full
observability of the board, so the game the LLM plays is a *reasoning* problem, not a memory problem
(partial observability is §Out of scope). The observation also carries a **`danger` grid** — the
decoded, chain-reaction-resolved "ticks until this cell is on fire" map that the idea's
"LLM possible at ~2 Hz with a decoded board" line asks for.

**Hidden.**
- **The opposing team's radio integers — never, in any seat's observation, at any delay.** Only your
  own partner's pair reaches you, and only one turn late.
- What lies under an **unbroken** wooden wall.
- Every other seat's order, `notes`, prompt and `say`-not-yet-spoken.
- Every seat's **real policy and player name**, including your own partner's. Nothing about any
  identity ever reaches a prompt.
- Every other seat's fallback and latency statistics.

The observation is a JSON object appended to the user message, and is mirrored (minus `your_notes`)
into the replay's `directive` record so the replay explains every decision.

```json
{
  "you": "RED-1", "team": "RED", "teammate": "RED-2", "enemies": ["BLUE-1", "BLUE-2"],
  "turn": 19, "of": 36, "tick": 76, "ticks_left": 68, "turn_ticks": 4,
  "collapse": {"next_tick": 96, "next_ring": 1, "collapsed_rings": []},
  "legend": "# rigid  W wood  . passage  * flame  e extra-bomb  r range  k kick",
  "board": [
    "###########", "#..W...W..#", "#W#W#W#W#W#", "#.W..*..W.#", "#W#W#W#W#W#",
    "#..r..W...#", "#W#W#W#W#W#", "#.W..W..W.#", "#W#W#W#W#W#", "#..W...W..#",
    "###########"
  ],
  "danger": [
    "...........", "...........", "...........", "..123210...", "....1......",
    "...........", "...........", "...........", "...........", "...........",
    "..........."
  ],
  "bombs": [
    {"x": 5, "y": 3, "fuse": 2, "range": 3, "owner": "BLUE-1", "moving": "none"},
    {"x": 4, "y": 7, "fuse": 6, "range": 2, "owner": "RED-1", "moving": "left"}
  ],
  "bombers": [
    {"id": "RED-1",  "x": 4, "y": 6, "alive": true,  "ammo": 0, "range": 2, "kick": true},
    {"id": "BLUE-1", "x": 6, "y": 3, "alive": true,  "ammo": 1, "range": 3, "kick": false},
    {"id": "RED-2",  "x": 8, "y": 8, "alive": true,  "ammo": 2, "range": 2, "kick": false},
    {"id": "BLUE-2", "x": 2, "y": 9, "alive": false, "ammo": 0, "range": 2, "kick": false}
  ],
  "radio_from_teammate": [3, 7],
  "your_last_order": {"verb": "break"},
  "your_notes": "clearing toward the middle; RED-2 holds the SE pocket",
  "score_now": 41
}
```

Field rules. `board` is always 11 strings of 11 characters; a bomb is not drawn on `board` (it is in
`bombs`), a bomber is not drawn on `board` (it is in `bombers`), so the layers never collide.
`danger[y][x]` is the digit `0..9` giving the number of ticks until that cell first becomes flame,
computed from the current bombs **with chain reactions and with the scheduled collapse rings**, or
`.` for "safe for at least 10 ticks". `bombers` always lists all four in the fixed order
`RED-1, BLUE-1, RED-2, BLUE-2`, dead ones included, so the array shape never changes. `score_now` is
the running `teamScore[you]`.

### Reply schema and per-field caps

```json
{
  "order": {"verb": "hunt", "target": "BLUE-1"},
  "radio": [3, 7],
  "say": "boxing him against the SE lattice",
  "notes": "3 means 'I am out of ammo'; 7 means 'enemy is north of me'"
}
```

| Field | Type | Cap / domain |
|---|---|---|
| `order` | object | one order, for your own bomber; an array is accepted and its **first** element used |
| `order.verb` | string | **≤ 8 runes**; enum `go` \| `bomb` \| `hunt` \| `break` \| `hide` \| `kick` \| `follow`, lower-cased, hyphens/spaces normalised to `_` before matching; unknown → **the seat's previous verb** |
| `order.x`, `.y` | integer | required iff `verb == "go"`; clamped into `[0,10]`; if the cell is rigid, retargeted to the nearest passable cell (lowest `y`, then lowest `x`) |
| `order.target` | string | required iff `verb == "hunt"`; **≤ 6 runes**; must be a **living enemy** alias; unmatched or dead → the nearest living enemy |
| `order.dir` | string | required iff `verb == "kick"`; **≤ 5 runes**; enum `up` \| `down` \| `left` \| `right` |
| `radio` | array | **exactly 2 integers**, each clamped into **`[1,8]`**; missing, wrong length or non-numeric → **repeat this seat's previous pair**; turn-1 default `[1,1]` |
| `say` | string | **≤ 100 runes** (`MaxSayRunes`) — spectator chatter, rendered in the feed and as a speech bubble |
| `notes` | string | **≤ 200 runes** (`MaxNoteRunes`) — private, echoed to this seat only next turn |
| whole reply | bytes | **≤ 8192** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |
| `policy` label | string | **≤ 48 runes** (`MaxPolicyLabelRunes`) |
| `fallback.detail` | string | **≤ 200 runes** (`MaxFallbackDetailRunes`) |
| whole `directive` record | string | **≤ 900 runes** (`MaxDirectiveRunes`); `notes` is not in it, `say` shrinks first |

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded
error text — is truncated on RUNE boundaries** via the starter's `truncateRunes` / `runeSubStr`,
never by byte index. Byte truncation is what makes a replay that renders in a browser fail a strict
UTF-8 parser; `tests/test_pom_replay.nim` asserts it with 4-byte emoji sitting exactly on every cap.

Unknown top-level keys are ignored. A reply with a valid `radio` and no `order` is **usable** (the
seat keeps last turn's order and the radio still goes out) — the radio is a first-class output, not a
rider on the order. A reply that is not a JSON object is a parse failure and nothing else is.

### System prompt (fixed, identical for every LLM seat)

```
You command ONE bomber in a 2v2 bomb-and-dodge match on an 11x11 walled grid. You and
one PARTNER are a team; two opponents are the other team. You did not choose your
partner and you will never learn which policy it is.

THE BOARD, EVERY TURN
- "board" is 11 rows of 11 characters: # rigid wall, W wooden wall, . floor,
  * fire, and e/r/k for the three power-ups (extra bomb, +1 blast range, kick).
- "danger" is the same grid decoded for you: a digit is how many ticks until that
  cell catches fire, counting chain reactions and the closing walls. A '.' is safe
  for at least 10 ticks. Standing on a digit 0 or 1 kills you.
- "bombs" lists every live bomb with its fuse and blast range. "bombers" lists all
  four of us with ammo, blast range and whether we have kick.

THE RULES
- A bomb has an 8-tick fuse and clears its own cell plus (range - 1) cells in each of
  the four directions, stopping at the first wall. Wood is destroyed; rigid stops it.
  Fire lasts 2 ticks and kills instantly - you, your partner, anyone.
- You start with 1 bomb and range 2. Breaking wood reveals power-ups; walk onto one
  to take it. Extra bomb, +1 range, and kick (kick lets you shove a bomb you walk
  into down a clear lane).
- One command turn is 4 ticks. You give ONE order; a controller executes it tick by
  tick and will ALWAYS pull you out of fire first if it can. It will refuse to lay a
  bomb it cannot see an escape from. It cannot save you from a trap with no exit.
- At tick 96 the outer ring of floor turns to wall and crushes anyone on it. At tick
  120 the next ring goes. From then on the arena is the middle 5x5.
- Your team wins by killing BOTH opponents. Blowing yourself or your partner up costs
  your team the same as being killed. The game ends at tick 144.

THE RADIO
- Every turn you send your PARTNER two integers, each 1 to 8. Your partner receives
  them on the FOLLOWING turn. The opponents NEVER see them.
- The game assigns these numbers NO meaning. Any meaning is whatever you and your
  partner manage to establish while under fire. Your partner may be running a
  completely different policy from yours, so: send something SIMPLE, send it
  CONSISTENTLY, and read your partner's pair against what you can see it actually
  doing on the board. A code nobody can decode is worth nothing.

YOUR ORDERS - exactly one per turn, executed until you change it:
- {"verb":"break"}                    walk to the nearest wood and bomb it
- {"verb":"bomb"}                     bomb where you stand right now, then retreat
- {"verb":"go","x":5,"y":5}           walk to that cell (it also picks up anything on the way)
- {"verb":"hunt","target":"BLUE-1"}   close on that enemy and bomb when it is in your blast lane
- {"verb":"hide"}                     move to the safest reachable cell and sit
- {"verb":"kick","dir":"left"}        shove the bomb on your left down the lane
- {"verb":"follow"}                   move to your partner and break wood beside it

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with { and end
with }. No prose, no markdown, no code fences.
{"order":{"verb":"break"},"radio":[3,7],"say":"<=100 chars","notes":"<=200 chars"}
"say" is shown to spectators. "notes" comes back to you next turn and to nobody else.
An order you omit repeats; a radio pair you omit repeats.
```

### Champion #1 — `pommerman-firestarter` (owner **daveey**), `PLAYER_PROMPT`

```
Play forward and make the board yours. Turn 1 through 6: "break", every turn, without
exception - you cannot fight with range 2 and one bomb, and every wooden wall you take
down is a lane you can retreat along and a chance at a power-up. The moment "board"
shows an e, r or k you can reach, "go" to it; range and extra bombs beat position this
early.
From turn 7, read "danger" before anything else. If your own cell shows a digit, order
"hide" and lose the turn - a dead bomber scores nothing. If you are clean and an enemy
is on your row or column within (your range - 1) cells with nothing but floor between
you, order "hunt" on it. Otherwise keep breaking toward the middle.
From turn 22 head inward: "go" to a cell in the 5x5 middle block (x and y both between
3 and 7) and be inside it before tick 96. Outside the ring is a death sentence at 96
and again at 120, and the bomber that arrives first picks the corner.
Once inside, hunt. Prefer the opponent with lower ammo. If you take kick, use it: a
kicked bomb down a straight lane is the only way to hit something that will not come
to you, and it costs you nothing.
RADIO. Send [a, b] where a is your intent this turn and b is where you are:
a = 1 breaking wood, 2 collecting a power-up, 3 hunting, 4 hiding, 5 I am in the middle,
6 I am about to bomb next to you so move, 7 I am out of ammo, 8 I am in trouble.
b = 1..4 for which quadrant you are in (1 NW, 2 NE, 3 SE, 4 SW), 5..8 for the same
quadrant when you are already inside the middle 5x5.
Read your partner's pair the same way and BELIEVE the position half even if the intent
half looks like noise - if partner says 6, get off its row and column this turn.
```

### Champion #2 — `pommerman-cornerman` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Win by not dying, and by making the enemy die of the walls. Most bombers in this game
kill themselves; you will not.
Rule one, absolute: if your own cell in "danger" shows any digit at all, order "hide".
Nothing else. Rule two: never order "bomb" or "hunt" unless "danger" shows at least two
'.' cells you can reach in three steps in DIFFERENT directions. A dead end plus a bomb
is a suicide.
Turns 1 through 10: "break", staying inside your own quadrant, and take any power-up
that appears within about five cells - do not cross the board for one. You want range 3
and two bombs by turn 10 and you want to still be alive.
Turns 11 through 24: hold the mouth of your own corridor. Order "hide" whenever no
enemy is within five cells, and "hunt" the moment one comes inside five. Let them walk
into your ground. If your partner's radio says it is in trouble, order "follow" for
exactly one turn and then go back to holding.
Turn 25 onward: "go" into the middle 5x5 (x and y between 3 and 7), take the cell with
the most exits, and from then on alternate "hide" and "hunt" - hide when both opponents
are alive and more than three cells away, hunt the nearer one otherwise. The rings do
half your work; you only have to outlive them.
RADIO. Send [a, b] where a counts your bombs in hand plus one (so 1 means empty, 2
means one bomb, and so on up to 6) and b is the number of living enemies you can see
within four cells, plus one (1 = none nearby, 2 = one, 3 = both), except send b = 8
when you are about to die and want your partner clear of you.
Read the partner's a as "can it help me right now" and its b as "is it in contact".
An 8 in either half means get away from that bomber this turn.
```

### The controller (deterministic, shared by every policy)

`src/pommerman/control.nim` — the starter's directive→actuator module, retargeted from pixel steering
to grid actions. It runs once per living bomber per tick. There is **no randomness in the controller
at all**; every tie breaks by the fixed direction order `up, down, left, right, stay`, then by
ascending seat id.

**Step A — the danger map.** Compute `danger[t][cell]` for `t = 0 .. dodgeHorizon` (`dodgeHorizon =
6`): the cells that will be flame at tick `now + t`, derived from every live bomb's fuse, position,
velocity and blast, resolved through the same chain-reaction fixpoint as §The game step 8, plus every
cell of a ring whose collapse tick falls inside the horizon. Identical to what the observation's
`danger` grid reports, from one shared proc.

**Step B — the survival override.** If the bomber's current cell is in `danger[t]` for any
`t ≤ dodgeHorizon`, the controller ignores the order and escapes: BFS over cells passable *now*, up
to depth `dodgeHorizon`, taking the first step of the shortest path to the nearest cell that is safe
for **every** `t ≤ dodgeHorizon` along a path whose every cell is safe at its own arrival tick. If no
such cell exists, take the step that maximises the tick at which the destination first becomes flame.
This is the deliberate departure from per-tick play: without it the LLM's 4-tick cadence would make
every commander a suicide, and with it the real skill — trapping, lane control, power-up tempo,
partner coordination — is what decides the game. **The override is not a shield:** a bomber boxed
into a dead end still dies, which is exactly how Pommerman is won.

**Step C — the order.** `T(u)` is the target cell, `bombOk` says when a bomb may be laid.

| Verb | `T(u)` | Bomb when |
|---|---|---|
| `go x y` | `(x,y)`; if rigid, the nearest passable cell | never |
| `bomb` | own cell | on the **first tick of the turn** if `ammo > 0`, no bomb on the cell, and an escape exists |
| `hunt A` | living enemy `A`'s cell; if `A` died, the nearest living enemy | when `A` is on the same row or column within `blast − 1` cells with only passage between, `ammo > 0`, and an escape exists |
| `break` | the nearest passage cell orthogonally adjacent to a wooden wall | on arrival, if `ammo > 0` and an escape exists |
| `hide` | the reachable cell (≤ 6 steps) maximising the tick at which it first becomes dangerous; ties by fewest steps, then by most orthogonal exits | never |
| `kick dir` | own cell; the bomber emits the `dir` move so §The game step 6.3 fires. If it is not adjacent to a bomb in `dir`, or lacks `kick`, it behaves as `hide` | never |
| `follow` | the partner's cell; once within 2 cells of the partner, behave as `break`. If the partner is dead, behave as `break` | as `break` |

**Step D — the step.** BFS over cells passable now (passage or power-up, no bomb, no living bomber,
no flame), take the first step of the shortest path to `T(u)`. If `T(u)` is unreachable, step toward
the reachable cell minimising Manhattan distance to `T(u)`; if that is the current cell, `stay`.

**"An escape exists"** means: after hypothetically placing the bomb, the Step-B escape BFS from the
bomber's own cell finds a cell safe for all `t ≤ dodgeHorizon`. **This is the one place the
controller refuses a commander's order**, it is stated in the system prompt, and
`tests/test_pom_control.nim` asserts it directly.

### Scripted baselines (both shipped as fillers; `sapper` is also the server-side fallback)

`src/pommerman/baselines.nim`, the starter's module retargeted. Both emit the **same** order object
an LLM does, with a radio pair, through the same validator — which is what makes the bounded-orders
test meaningful.

**`sapper`** — `PLAYER_SCRIPTED=sapper`, the published default and the fallback. Each turn, in order:

1. If a living enemy is on my row or column within `bombEnemyRange = 2` cells with only passage
   between, and `ammo > 0` → `bomb`.
2. Else if I am orthogonally adjacent to a wooden wall and `ammo > 0` → `bomb`.
3. Else if a power-up is reachable within `powerupSearch = 8` steps (BFS over currently-passable
   cells; ties by lowest `y`, then lowest `x`) → `go` to it.
4. Else if any wooden wall is reachable → `break`.
5. Else if the collapse ring for tick 96 or 120 already threatens my cell, or `tick >= 88` and I am
   outside the middle 5 × 5 → `go` to `(5,5)`.
6. Else → `hunt` the nearest living enemy.
7. `radio` = `[clamp(1 + ammo, 1, 8), clamp(1 + (living enemies within 4 steps), 1, 8)]` — a real,
   legible signal, so the channel is exercised even in an all-scripted episode and a champion partnered
   with a filler has something to decode.
8. `say` and `notes` are empty.

**`camper`** — `PLAYER_SCRIPTED=camper`. Deliberately weaker and **different in shape**, so the
ladder gets a spread rather than two versions of one bot:

1. If a living enemy is orthogonally adjacent and `ammo > 0` → `bomb`.
2. Else if I am adjacent to wood, `ammo > 0`, and at least `campExits = 2` of my orthogonal
   neighbours are currently safe → `bomb`.
3. Else if `tick >= 88` and I am outside the middle 5 × 5 → `go` to `(5,5)`.
4. Else → `hide`.
5. `radio` = `[1, 1]`, every turn — a deliberately silent partner. It is the control against which
   "did the radio matter?" is measured on the ladder.
6. `say` and `notes` are empty.

Like the starter's `DefaultBaselineParams`, the four tunables (`bombEnemyRange = 2`,
`powerupSearch = 8`, `dodgeHorizon = 6`, `campExits = 2`) are a **parameter object chosen by
`tools/tune_baselines.nim`'s head-to-head sweep, not guessed**; `tools/ci/baseline_tuning.json`
records the sweep's pick and `tests/test_pom_tuning.nim` asserts the shipped defaults still equal it.
Phase 20 runs the sweep before pinning them (the liars-dice 2026-08-26 learning: a note's pinned
constants are falsifiable and the sweep may really retune them; a retune is a `design.md` errata, not
a redesign).

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/pommerman/`. The fork is a rename
sweep (`ctf` → `pommerman`, `CTF_WIRE` → `POM_WIRE`; a CI grep asserts no `ctf_`/`CTF_` identifier
survives outside comment history) plus the changes below. **The same modules compile twice**:
natively into `/bin/pommerman` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason this game lives in the
starter's language.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/pommerman/server.nim` | **fork**, four named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/pommerman/` | **fork** (magic + game name only) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/pommerman/` | **fork**, retargeted not rewritten | the per-turn parallel batch, the two deadlines, `turnSpacingMs`, the budget guard, tolerant parsing, the rune caps, repair-don't-reject, the fallback ladder, the `throttled` fail-fast |
| `src/ctf/sim_state.nim` → `src/pommerman/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/pommerman/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames`, the results JSON builder |
| `src/ctf/events.nim` → `src/pommerman/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/pommerman/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/pommerman/global.nim` | **fork**, three named edits below | the sprite/object pools, the bomber compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label-vocabulary contract (+ `tests/label_manifest.txt`), the rig compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/pommerman/sim_types.nim` | **fork** | `GameVersion` (starts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), the flatty wire types (field order sacred), `MaxSayRunes` (100), `MaxNoteRunes` (200), `MaxPolicyLabelRunes` (48), `MaxFallbackDetailRunes` (200), `MaxDirectiveRunes` (900), `MaxPromptRunes` (4000) |
| `src/ctf/sim_config.nim` → `src/pommerman/sim_config.nim` | **fork** | `GameConfig` lifecycle and `config.update`; the sub-second-deadline rejection kept (`curly` floors `CURLOPT_TIMEOUT` to whole seconds) |
| `src/ctf.nim` → `src/pommerman.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/pommerman_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags (`ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `FILESYSTEM=1`, `ENVIRONMENT=web,worker,node`, `useMalloc`, `EXPORTED_RUNTIME_METHODS=HEAPU8`, the `EXPORTED_FUNCTIONS` list), the OffscreenCanvas Worker, the stage-note diagnostics, the `data-replay-loaded` / `data-replay-error` signalling |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/pommerman_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/soldier_red.png`, `soldier_blue.png`, `soldier_red_crown.png`, `soldier_blue_crown.png`, `paintbomb.png`, `spraycan.png`, `medkit.png`, `shield.png`, `arena_floor.png`, `font.ttf`, `ascii.png`, `data/atlas/*`, `client/art/walls/{wall_h.jpg,wall_v.jpg}`, `client/art/lockerroom/{bg.jpg,red_*.webp,blue_*.webp}` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter / windup / exposure model, aim decoupling and vision cones, fog-of-war
raycasting and the first-person PIP, spray cans and the spray cone, floor paint and the paint grid,
the paint buff, King of the Hill and `hillTicks`, the `resident`/`visitor` regimes, hearts / flags /
capture / carriers, grenades and the barrage, med kits, shields, cardboard barriers, trenches, perks,
handicaps, four-team free-for-all, shouts-as-cog-speech, achievements, campaign mode, lives and hit
points, respawning, and **all of the pixel-space map machinery**: `arena.nim`'s wall masks and pixel
queries, `map_art.nim`, `mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`,
`tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`,
`docs/pool-review.html`. The board here is an 11 × 11 integer grid; every one of those is a config
surface these rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`crew`, `spraycan_held`, all green/yellow art, `data/rig_real/`), since bombers are drawn as baked
chips (§Viewer → Art) and the 128 px rig is never used at 32 px per cell.

### New modules

- `src/pommerman/board.nim` — the grid: cell↔index helpers, terrain enum, the **map generator**
  below, the ring/collapse table, the occupancy grid, the four corner spawns. Pure integer; no pixie,
  no pixel queries.
- `src/pommerman/bombs.nim` — bombs, fuses, kicking, the blast-cell walk, the chain-reaction fixpoint
  and the flame timers. Exposes `dangerMap(sim, horizon)`, the **one** proc that both the observation
  builder, the controller and the viewer's overlay call, so the three can never disagree.
- `src/pommerman/sim.nim` — the tick loop of §The game: collapse, action selection, placement, kick
  movement, bomber movement, fuses, detonation, flames, deaths, decay, `gameHash`, end evaluation.
  Imports and re-exports the sim modules, as the starter's does, so `import pommerman/sim` sees
  everything.
- `src/pommerman/radio.nim` — the per-seat radio mailbox: store on turn `T`, deliver to the partner
  only on turn `T+1`, clamp to `1..8`, and **assert at compile-time-of-shape and at runtime that no
  read is ever indexed by a seat outside the sender's own team.** (The fog-of-war-boards 2026-08-27
  scar: a per-seat structure written under the wrong index silently leaks; every write and read here
  goes through two procs that take a `team` and a `seat` and check `team(seat)` matches.)

### Integer arithmetic (the determinism pin)

**All new sim arithmetic is integer only.** Positions, fuses, blast ranges, ammo, flame timers,
scores and distances are `int`. Distances are Manhattan or BFS depth; there is no floating point
anywhere in `sim.nim`, `board.nim`, `bombs.nim`, `control.nim` or `baselines.nim`, and
`tests/test_pom_sim.nim` greps for it. That is the precondition for the native ↔ wasm hash chain.

**The only randomness is the seed, and it is used in exactly one place** — the map generator's orbit
draw. The seed is randomised in `src/pommerman.nim` before `config.update` (the starter's rule),
recorded in the replay config and in `results.seed`. Two episodes with the same seed and the same
orders are byte-identical.

### Map generation (deterministic, 4-fold rotationally symmetric)

Rotation is `rot(x,y) = (10 − y, x)`, a 90° turn about `(5,5)`.

1. The outer ring (`ring == 0`, 40 cells) is **rigid**.
2. Interior cells with **both coordinates even** (`x,y ∈ {2,4,6,8}`, 16 cells) are **rigid** — the
   classic Bomberman lattice. It is closed under `rot`, and it guarantees the board is **connected by
   construction**: every cell with an odd coordinate lies on an all-odd row or column, and those form
   a spanning grid. No connectivity repair pass is needed.
3. **Reserved passage**: the four corner cells `(1,1) (9,1) (9,9) (1,9)` and their two interior
   orthogonal neighbours each — 12 cells, exactly three `rot` orbits. Always passage.
4. `(5,5)` is passage (it is its own `rot` orbit).
5. The remaining 52 interior cells form exactly **13 orbits** of 4. Sort them by their canonical
   representative (lowest `y`, then lowest `x`), Fisher–Yates shuffle with a xorshift64\* seeded by
   `seed`, then: **the first 9 orbits are wooden wall (36 cells)**, the last 4 are passage (16 cells).
6. Of the 9 wood orbits, in that same shuffled order: orbits 1–2 hide an **extra-bomb**, orbits 3–4
   hide **+1 range**, orbit 5 hides **kick**, orbits 6–9 hide nothing. **20 power-ups**, upstream's
   `NUM_ITEMS`.

Totals: 57 rigid, 36 wood, 28 passage at tick 0; 64 open cells once all wood is cleared.
**Every seat's quadrant is an exact rotation of every other's**, including which power-up sits where
relative to its corner — so a score difference is a policy difference, not a spawn difference.
`tests/test_pom_board.nim` asserts the symmetry, the counts, the connectivity and the invariance over
1000 seeds.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDPOM`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `num_agents`, every rule constant, `players[].name`, `slots[]`),
   then the record stream — joins (name, slot, token), leaves, **per-turn order records** (verb, arg,
   radio pair — the only inputs this game has), chat records
   (`register` / `directive` / `fallback` / `budget_guard` / `stop` / `result`) and **one `gameHash`
   per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/pommerman_replay.nim` — which imports the
   **same** `src/pommerman/sim.nim` — through the pinned `emscripten/emsdk` + nimby container in
   `Dockerfile.replay-viewer`.
3. In the browser, `pom_load_replay` runs `parseReplayBytes` + `initReplayRuntime`; `pom_frame`
   re-steps the sim from the recorded orders and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens and
   surfaced as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order, appended after the starter's existing mixes so ordering
   stays stable: per cell `(terrain, itemKind, flameLife)`; per bomber
   `(seat, x, y, alive, ammo, blast, kick)`; per bomb `(id, x, y, fuse, blast, owner, velocity)`; per
   team `(alive, kills, wood)`; then `tick`, `collapsedRings` and the four seats' stored radio pairs.
   **The radio pairs are hashed** — they are inputs, and a replay that got them wrong would draw the
   wrong glyphs while claiming a clean hash.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact
   cannot be re-derived from sim state, so the stop is written as one `stop` record applied by the
   *same proc* on record and on playback, and `tests/test_pom_replay.nim` runs the record→re-derive
   check for **every** end reason (`wipe`, `tickCap`, `wallClock`, `fault`), not just the healthy one
   (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 144 hashes + 144 order records + ~15 chat records ≈ **20 KB**. Everything else is
re-derived.

### The four named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with `turnTicks = 4` and four seats in the batch.
2. **Registration interception** — a player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed
   as registration, **not** applied as a shout and **not** written to the replay chat stream; the
   server writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim, and the server **logs a named warning for any seat still without a register record when
   the lobby closes**. Any other chat text from a seat is dropped — bombers speak through `say`.
3. **Single game** — `maxGames = 1`; the `gamesPlayed` loop is kept but never iterates, because the
   symmetric map removes the side-swap need. The archive/`resetToLobby` path stays so a future
   best-of-N variant is a config change.
4. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration, kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wallClock`, and
   written as the load-bearing `stop` record of point 5 above.

### The two named edits to `roster.nim`

1. **Aliases are identity-anonymous.** `seatAlias(slot)` returns `IdentityNames[slot]` →
   `RED-1, BLUE-1, RED-2, BLUE-2`. Sprite labels and the label manifest inherit the two-name-space
   rule with no further change, and `showPlayerLabels` is false.
2. **`squadResultsJson` → `bomberResultsJson`** — one entry per seat, four entries in every
   seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a grid, not a pixel arena.** `buildSpriteProtocolPlayerUpdates` emits cell-space
   coordinates; the fov cache and shadowcasting are deleted (spectators see everything, and there is
   no per-seat fog in v1).
2. **Bomber, bomb and item chip pools.** New pools `BomberSpriteBase`, `BombObjectBase`,
   `ItemObjectBase`, `FlameFxBase`, sized to 4 / 32 / 24 / 128, filled in id order and emitted
   incrementally like the starter's other object families.
3. **Baked arena.** `arena_floor.png` is tiled and darkened at map install with pixie, exactly the
   way the starter bakes endzone paint, plus `client/art/walls/wall_h.jpg` / `wall_v.jpg` composited
   onto the rigid cells and a procedural plank texture on the wood cells, plus 1 px cell gridlines so
   the grid reads with the HUD off.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST`/`PORT`; player sockets
at `/player?slot=<i>&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering
for the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). Global
broadcasts are fire-and-forget so a slow viewer can never stall the episode.

### Results document (closed schema; `bomberResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":         ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
  "aliases":       ["RED-1", "BLUE-1", "RED-2", "BLUE-2"],
  "teams":         ["RED", "BLUE", "RED", "BLUE"],
  "scores":        [141, -141, 141, -141],
  "win":           [true, false, true, false],
  "winner":        "RED",
  "reason":        "complete",
  "endRule":       "wipe",
  "teamScores":    [141, -141],
  "teamAlive":     [2, 0],
  "teamKills":     [2, 0],
  "teamWood":      [21, 20],
  "alive":         [true, false, true, false],
  "kills":         [1, 0, 1, 0],
  "deaths":        [0, 1, 0, 1],
  "suicides":      [0, 0, 0, 0],
  "bombsPlaced":   [14, 11, 9, 13],
  "woodCleared":   [12, 11, 9, 9],
  "kicks":         [2, 0, 0, 1],
  "pickups":       [3, 1, 2, 2],
  "radioSent":     [36, 36, 36, 36],
  "finalTick":     118,
  "turnsPlayed":   30,
  "seed":          1734029581,
  "policyKinds":   ["llm", "llm", "scripted", "scripted"],
  "llmTurns":      [30, 30, 0, 0],
  "fallbackTurns": [1, 0, 0, 0],
  "ordersRejected":[0, 0, 0, 0],
  "deadSeats":     [false, false, false, false],
  "stopDetail":    ""
}
```

`teamScores` / `teamAlive` / `teamKills` / `teamWood` are two-element arrays indexed `[RED, BLUE]`.
`winner` is `"RED"`, `"BLUE"` or `null` (draw). Adding a key means updating `bomberResultsJson`, the
manifest's `results_schema` and `tools/ci/docker_smoke.sh`'s expected-key set in the same commit —
Coworld schemas are closed and undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDPOM`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"pommerman/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],"teams":[…],
  "policyKinds":[…],"tickCount":…,"orders":[…],"radio":[…],"fallbacks":N,"results":{…}}` — by
  brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md`
  documents for prod forensics) and decoding the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                        # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.teamKills[0]' /tmp/ep.json
  jq -r '[.orders[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  jq -r '[.radio[]|select(.a!=1 or .b!=1)]|length' /tmp/ep.json
  ```
  Require `protocol == "pommerman/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), non-zero `bombsPlaced` on every seat, the champion seats' orders with
  `source == "llm"` and real verbs (not all fallbacks), and a non-trivial radio stream from the
  champion seats.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDPOM`, format version, `gameName` `pommerman`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `maxTicks`, `turnTicks`, `bombFuse`, `flameLife`, `startAmmo`, `maxAmmo`, `startBlast`, `maxBlast`, `collapseTicks`, `dodgeHorizon`, `players[].name` (real names), `slots[]` (teams), `fastMode` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| orders | per turn, per seat: `verb`, `arg`, `radio` — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields;
they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `team`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `seat`, `alias`, `team`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `verb`, `arg` (`{x,y}` \| `target` \| `dir` \| `null`), `radio` `[a,b]`, `radio_in` `[a,b]`\|`null`, `say` (≤ 100 runes), `view` (the observation minus `your_notes`) |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of thirteen kinds:**

`turn` `{n}`; `order` `{seat, verb, arg}`; `radio` `{seat, team, a, b}`; `say` `{seat, text}`;
`fallback` `{seat, cause}`; `bomb` `{seat, x, y, fuse, range}`; `kick` `{seat, x, y, dir}`;
`pickup` `{seat, kind, x, y}`; `wood` `{x, y, team}`; `firstblood` `{killer, victim}`;
`death` `{victim, killer, cause, x, y}`; `collapse` `{ring, tick}`;
`end` `{reason, winner, alive}`.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`firstblood`,
`kick`, `death`, `collapse`, `fallback`, `end`.** `bomb`, `wood`, `pickup`, `radio`, `order`, `say`
and `turn` drive the feed, not the scrubber (100+ bomb markers would make it unreadable). At most 4
`death`, 2 `collapse` and a handful of `kick` beats exist in an episode, so the scrubber stays
readable.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to
`BombPlaced, BombKicked, Explosion, WoodCleared, Pickup, Death, Collapse, TurnStart, Directive, Radio, Fallback, PhaseChange`
and the mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.

### The state JSON the viewer reads

`broadcast.nim`'s `buildStateJson` (and, in the wasm viewer, `buildReplayViewerPacket`) emits exactly
this object once per drawn frame. It is the whole contract between the sim and `broadcast_core.js`:

```json
{
  "tick": 76, "maxTicks": 144, "turn": 19, "turns": 36, "phase": "playing",
  "board": {
    "w": 11, "h": 11,
    "terrain": ["###########","#..W...W..#","#W#W#W#W#W#","#.W.....W.#","#W#W#W#W#W#",
                "#..r......#","#W#W#W#W#W#","#.W..W..W.#","#W#W#W#W#W#","#..W...W..#",
                "###########"],
    "flame":  [[5,3,2],[6,3,1]],
    "items":  [{"x":3,"y":5,"kind":"range"}],
    "collapsedRings": []
  },
  "bombs": [
    {"id":14,"x":5,"y":3,"fuse":2,"range":3,"seat":1,"team":"blue","moving":"none",
     "blast":[[5,3],[4,3],[6,3],[5,2],[5,4]]},
    {"id":15,"x":4,"y":7,"fuse":6,"range":2,"seat":0,"team":"red","moving":"left",
     "blast":[[4,7],[3,7],[5,7],[4,6],[4,8]]}
  ],
  "danger": ["...........","...........","...........","..123210...","....1......",
             "...........","...........","...........","...........","...........",
             "..........."],
  "bombers": [
    {"seat":0,"alias":"RED-1","team":"red","x":4,"y":6,"alive":true,"ammo":0,"range":2,
     "kick":true,"radio":[3,7],"radioAge":1,"skin":"plain","fallback":false},
    {"seat":1,"alias":"BLUE-1","team":"blue","x":6,"y":3,"alive":true,"ammo":1,"range":3,
     "kick":false,"radio":[1,1],"radioAge":1,"skin":"plain","fallback":true},
    {"seat":2,"alias":"RED-2","team":"red","x":8,"y":8,"alive":true,"ammo":2,"range":2,
     "kick":false,"radio":[1,4],"radioAge":1,"skin":"crown","fallback":false},
    {"seat":3,"alias":"BLUE-2","team":"blue","x":2,"y":9,"alive":false,"ammo":0,"range":2,
     "kick":false,"radio":[1,1],"radioAge":1,"skin":"crown","fallback":false}
  ],
  "teams": [
    {"team":"red","alive":2,"kills":1,"wood":21,"score":41,"radio":[3,7],
     "names":["daveey","Baseline (1)"],"aliases":["RED-1","RED-2"],"fallback":false},
    {"team":"blue","alive":1,"kills":0,"wood":20,"score":-41,"radio":[1,1],
     "names":["daveey-1","Baseline (2)"],"aliases":["BLUE-1","BLUE-2"],"fallback":true}
  ],
  "collapse": {"nextTick": 96, "nextRing": 1},
  "events": [{"k":"bomb","seat":1,"x":5,"y":3,"fuse":8,"range":3}],
  "feed": [{"t":74,"text":"RED-1 kicks a bomb west","team":"red"}],
  "result": null
}
```

`terrain` is 11 strings of 11 characters (`#`/`W`/`.`, plus `e`/`r`/`k` for a revealed item, which
`items` repeats structurally). `flame` entries are `[x, y, life]`. `bombs[].blast` is the
chain-resolved footprint the viewer draws, computed by the **same** `bombs.nim` proc the sim and the
observation use. `result` becomes the results document at episode end and is what the endcard reads.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/pommerman_replay.nim`, forked
from `replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`,
and `index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter:
`coworld-ctf`** — which is this repo's own starter. **Never a mixture, and no file in this set comes
from cogame-babel, cogame-bullwhip, cogame-parley, cogame-moba or cogame-factorio.** Splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23). The set
is internally consistent and is kept as one piece: the Worker sets `Module.onRuntimeInitialized`, the
module is emitted **non-modularized** as `pommerman_replay.js`, `config.nims` keeps
`--os:linux --cpu:wasm32 --cc:clang` through `emcc`, `--mm:arc --exceptions:goto -d:useMalloc
-d:release -d:noSignalHandler`, `-O2`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`**
(non-negotiable: wasm32 has no memory protection, so a failed malloc would otherwise write through
nil into address 0 and corrupt the module's own globals), `-s FILESYSTEM=1`,
`--preload-file data@data`, `-s ENVIRONMENT=web,worker,node`,
`-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_pom_load_replay,_pom_frame,_pom_input,_pom_packet_ptr,
_pom_packet_len,_pom_mismatch_tick,_pom_error_ptr,_pom_error_len,_pom_stage_ptr,_pom_stage_len`; and
`static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './pommerman_replay.js')` in that order.

`pommerman_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress
buffer that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`,
and the `emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running
module destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `pom_load_replay` re-simulates the whole episode once headlessly (144
  ticks × 121 cells of integer work — sub-millisecond in wasm), records the per-tick living-bomber
  counts, the cumulative wood, the lull spans and the beat ticks, then resets and renders frame 0.
  That is what lets the sparkline and the scrubber beats draw at **full width on the first frame**
  instead of growing in.
- `pom_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch — posted by the Worker only *after*
`ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute means
"a frame is on the canvas", not "a file was fetched". **On failure it sets `data-replay-error` on
`<html>`** with the message, in `showFailure()`. Both are coworld-ctf's own signals, inherited
unchanged — this fork adds neither and removes neither. The `coworld-replay` postMessage bridge's
`ready` is posted **from a callback fired after** `data-replay-loaded="true"` is set, never on rAF
timing at the call site (chorus `3c11c953`, 2026-08-24), or the softmax.com embed samples an
unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte.** Not edited, not reformatted;
  `tests/test_pom_viewer.nim` pins its sha256 against the starter's file. Everything this game adds
  lives in the appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats` remain;
  `ingestBeats` ignores kinds it does not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). Concretely: everything **above** the
  starter's own `<!-- ==== PAINTBALL additions to the inherited coworld-ctf chrome ==== -->` banner
  (the classic broadcast page — its CSS, markup, `relayout()`, transport, endcard, locker-room
  loader, `?embed=1` mode and `.tiny` density system) is copied **byte-for-byte**; the paintball
  block **below** that banner is deleted whole (it draws hills, paint, tags and flags this game does
  not have); and a **`<!-- ==== POMMERMAN additions to the inherited coworld-ctf chrome ==== -->`**
  block is appended in its place under the same discipline. `tests/test_pom_viewer.nim` pins the
  sha256 of the byte prefix up to the splice marker and asserts the file only grows after it.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text
  by `tests/test_pom_viewer.nim`: the canvas/DPR sizing, the camera, the feed queue and `pushFeed`
  **including its signature** (the cogball 0.1.4 latch scar: a signature drift threw mid-replay and
  latched `static_replay.js` into `failed`), the beat and lull machinery, the endcard builder, the
  speed chips, the `?embed=1` path, and the `window.CTF_WIRE` → `window.POM_WIRE` rename emitted by
  `tools/gen_wire_constants.nim`. Deleted: every ctf-specific draw call and the FPV pipeline. Added:
  `drawArena`, `drawBombs`, `drawBlastFootprint`, `drawDanger`, `drawRadioGlyphs`, `drawKickTrail`,
  `drawScorch`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `attachMinimap(...)` call. **Zoom decision:
    dropped.** The board is a fixed 11 × 11 grid with a 1 : 1 aspect and no off-frame area;
    `relayout()` fits it whole at every width, and at the 360 px embed each cell is ~32 px, so per
    the pin a fixed arena drops `#viewpanel` entirely. `broadcast_core.js` tolerates a missing
    minimap (`pendingMinimap` stays null).
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — there is no
    per-bomber point of view worth showing; the whole board is the shot.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.steal`, `.beat-marker.return`, `.beat-marker.capture`, `.beat-marker.hillflip`,
    `.beat-marker.hillhold`, `.beat-marker.tagout` and `.beat-marker.gamestart` CSS rules — those
    kinds are never emitted here.
  - The perk and handicap badges.
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom`, `#chrome`,
    `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#bannerlane`,
    `#killfeed`, `#mmwarn`, **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`,
    `#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#ffwd-mini`,
    `#win-chip`, `#tick-clock`, `#speedchips`), `#scrub` with
    `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/`#scrub-head`, `#endcard` with
    `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`, and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here
and enforced by a test. The rule the builder follows is **by purpose, not by count**: rename the
paintball/CTF vocabulary wherever the copied regions surface it, and take this table as the
authoritative wording (the fog-of-war-boards 2026-08-27 scar: pinning "exactly N edits" made a
builder keep the starter's wrong words).

| Starter string (where) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` | `<span>Bomber</span><span>Kills</span><span>Bombs</span><span>Wood</span><span>Radio</span>` |
| `<span class="fl-cap">Lives left</span>` (endcard team block) | `<span class="fl-cap">Bombers left</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (scrub graph) | `<span class="momentum-label">BOMBERS STANDING</span>` |
| `<span class="lives-label">Lives</span>` (scorebug plate) | `<span class="alive-label">Alive</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (locker room) | "Lighting the fuses…" |
| `#clock-caption` "In the locker room" | "Taking corners" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" | "Replay hash mismatch at tick N — showing recorded orders" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline" | "kills / collapses / winner on the timeline" |
| team words `RED`/`BLUE` in `ec-tname` / plates | kept — they are this game's real team names |

**`tests/test_pom_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `spray`, `grenade`, `med kit`, `trench` — outside comment blocks, and asserts **zero**
matches; and asserts each replacement string above is present exactly once.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), **`--topband`** and **`--hudscale`**
on `:root`, unchanged (`--hudscale = clamp(0.5, boardW/760, 1.6)`, `.tiny` toggled at
`boardW <= 620`). **No overlay sits in the transport band**: the board is laid out between the two
bands, and every addition here (the danger overlay, the radio glyphs, the blast footprints, the feed,
the banners, the DANGER toggle) is positioned inside the board region or in the top band. The
**endcard stops at `var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule,
kept) so the scrubber stays clickable underneath, and it is **dismissed by every seek** (the
starter's `else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are
clickable, labelled buttons**: the appended block's `pomBeat(tick, kind, team, label)` — named so it
can never shadow `chrome_common.js`'s hoisted `markBeat` alias, the tandem 2026-08-23 trap — appends
`<button class="beat-marker <kind> <team>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind emitted and no others**: `.beat-marker.firstblood`, `.beat-marker.kick`,
`.beat-marker.death`, `.beat-marker.collapse`, `.beat-marker.fallback`, `.beat-marker.end`. The game
block never calls `markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: `TargetFps = 6`, one tick per 167 ms** (speed chips `[0.5, 1, 2, 4, 8]`, default 1).
A 144-tick episode therefore plays for **24 s**, which is what lets `viewer_smoke.mjs --soak 10`
observe real advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar). At
6 ticks/s an 8-tick fuse is 1.3 s — long enough to read the countdown, short enough to stay tense.

### Readouts

1. **The arena** — the 11 × 11 grid drawn edge to edge: baked floor, rigid walls, planked wooden
   walls. A wooden wall that breaks shatters into 6 frames of debris and leaves a scorch for 60
   frames, so the shape of the fight persists. Bombers are baked team chips (see Art); a bomber that
   dies flashes white, falls, and leaves a chalk outline for the rest of the replay.
2. **Bomb timers** (the idea's first ask) — every bomb draws its art plus a **countdown ring** whose
   arc shrinks with the fuse and the **numeric fuse in the centre** (render "3", never a symbol);
   the ring pulses red on the last two ticks.
3. **Blast ranges** (the idea's first ask) — every bomb draws its **chain-resolved blast footprint**
   as a translucent team-tinted cross on exactly the cells it will cover, from the same
   `bombs.nim` proc the sim uses, so what a spectator sees is what will burn. Overlapping footprints
   blend, which is how a spectator sees a chain coming.
4. **Danger overlay** — the state packet's `danger` grid drawn as an amber tint on cells that catch
   fire within 3 ticks, deepening as the count falls. On by default, toggled by a labelled `DANGER`
   chip in the **top** band, never in the transport band.
5. **Radio glyphs** (the idea's second ask) — the pair a seat sent this turn is drawn **over that
   bomber** as two digits `1..8` in the team colour inside a small radio-wave badge, with an arrow
   from sender to partner for the first frame of the turn, fading over the turn's 4 ticks. The pair
   is repeated on the team's scorebug plate with its age in turns. **Both teams' pairs are visible to
   the spectator** — the replay is spectator-side; the hiding is enforced in the observation builder,
   not the renderer, and §Decisions says so.
6. **Kicked-bomb highlight** (the idea's third ask) — a bomb with `moving != "none"` draws a bright
   team-coloured motion trail with a chevron in its direction of travel, the kicking bomber flashes
   for 3 frames, the feed says `RED-1 KICKS A BOMB WEST`, and a `kick` beat marks the tick on the
   scrubber.
7. **Scorebug plates** — two plates, one per team: the team name, the **real policy names** of its
   two seats (spectator side only, `.plate-name`), a chip per bomber showing alive/dead plus its
   `ammo`/`range` numerals and a small `K` when it holds kick, the team's kill count as the big
   numeral, the team's latest radio pair, and a `↯` glyph on any seat that has taken a fallback.
8. **Clock** — `#clock-time` shows `turn 19/36`; `#clock-caption` shows
   `tick 76/144 · walls close in 20`.
9. **Match feed** (`#killfeed`) — plain language, never internal notation: `RED-1 drops a bomb`,
   `BLUE-2 breaks a wall`, `RED-2 picks up EXTRA BOMB`, `RED-1 kicks a bomb west`,
   `RED radios 3·7`, **`FIRST BLOOD — RED-1 KILLS BLUE-2`**, `BLUE-1 blows itself up`,
   **`THE WALLS CLOSE IN — RING 1`**, `RED-1: "boxing him against the SE lattice"`, and
   `BLUE-1 MISSED THE CALL — scripted order (timeout)`. The `say` lines, the order lines and the
   radio lines are where a spectator sees the LLM playing.
10. **Momentum sparkline** — the starter's `#momentum` SVG retargeted to two series over the whole
    episode: living bombers per team (a 0–2 step line) and cumulative wood cleared per team, with the
    playhead marked, the two collapse ticks ruled, and the death ticks flagged. Filled from the
    load-time pre-scan, so it draws at full width on the first frame.
11. **Endcard** — `RED TAKES IT — BLUE WIPED AT TICK 118`, the four-row table under the re-mapped
    header (`Bomber | Kills | Bombs | Wood | Radio`, where `Radio` is that seat's most-sent pair),
    the end rule, and `SCORE +141 / −141`. It stops at `var(--band)` and any seek dismisses it.
12. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull
    = 24 consecutive ticks with no `bomb`, `wood`, `pickup`, `kick` or `death` event, from the
    pre-scan), spoilers switch, tick readout, speed chips, the scrubber with its six beat kinds, and
    `#mmwarn` on a hash mismatch — all the starter's, verbatim.

### Art

**Real art, from the starter's shipped assets — no placeholders, no solid-colour squares, no
downloads.**

- **Floor**: `data/arena_floor.png`, tiled and darkened 18 %, with 1 px cell gridlines, baked once at
  map install by pixie (the way the starter bakes endzone paint).
- **Rigid walls**: `client/art/walls/wall_h.jpg` and `wall_v.jpg` composited per cell at bake time
  with a 1 px highlight; the collapsed rings reuse the same tile with a red-hot rim so the shrink
  reads instantly.
- **Wooden walls**: a procedural plank texture in the floor bake's palette, with a per-cell seeded
  grain so 36 crates do not look stamped.
- **Bombers**: baked at load by `rig_art.nim`'s compositor from `data/soldier_red.png`,
  `soldier_blue.png` (seat `-1`, plain) and `soldier_red_crown.png`, `soldier_blue_crown.png`
  (seat `-2`, so partners are distinguishable at a glance) — each rendered once into three chip
  sizes (16, 24, 32 px) with a 1 px team rim, plus a dead/outline variant: **24 pre-baked chips**, so
  drawing four bombers a frame is four blits.
- **Bombs**: `data/paintbomb.png`, scaled to the cell, with the procedural countdown ring over it.
- **Power-ups**: `data/paintbomb.png` at half scale with a `+` badge = extra bomb;
  `data/spraycan.png` = +1 range; `data/shield.png` = kick. Each baked once into a 20 px chip with a
  gold rim so they read as loot against the floor.
- **Flames**: procedural additive orange/white quads from the starter's FX families, three frames.
- Loading screen: the starter's locker room (`client/art/lockerroom/bg.jpg` plus the red/blue cog
  webps) with the caption re-labelled. Text is `data/font.ttf`; small numerals use
  `data/atlas/nes-pixel.ttf`.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim. At 360 px the 11 × 11 board renders 360 px square: **~32 px per cell**, so a bomber chip is
24 px, a bomb's fuse digit 14 px and a radio digit 12 px — all comfortably legible, and the whole
board is in frame, which is why `#viewpanel` is dropped. Three rules are added and asserted by
`tests/test_pom_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps team name + the two policy names + the kill numeral + the radio
   pair; the per-bomber `ammo`/`range` numerals are hidden from the plate (they stay on the board).
3. Under `.tiny`, the bomb fuse digit draws at 14 px and the radio digits at 12 px, both with a 1 px
   dark outline, and the danger overlay drops to a flat tint with no per-cell digits.

---

## Packaging

- **Repo**: `Metta-AI/cogame-pommerman`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `pommerman`; **`game.name` is `pommerman`**
  so the secret namespace `secret://coworld/pommerman/anthropic_api_key`, the page slug, the
  `POST /coworld-league-seeds` body and the docs all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two services /
  two images; this fork uses the one-image / two-entrypoints shape because the shared
  `docker_smoke.sh` and `policies.json` assume a single image (the knights-archers precedent):

  ```yaml
  services:
    pommerman:
      image: coworld-pommerman:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{POMMERMAN_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:pommerman src/pommerman.nim`
  → `/bin/pommerman`, and the same for `src/pommerman_player.nim` → `/bin/pommerman-player`. The
  runtime stage copies both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/pommerman"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk`, pinned nimby
  with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block) with
  the asset list swapped to `data/{soldier_red,soldier_blue,soldier_red_crown,soldier_blue_crown,
  paintbomb,spraycan,shield,arena_floor}.png`, `data/font.ttf`, `data/ascii.png`,
  `data/atlas/nes-pixel.ttf`, `client/art/walls/*`, `client/art/lockerroom/*`,
  `pommerman_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["bomberman", "pommerman", "grid", "team", "emergent-comm"]`
    (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0); **`episode_timeout_minutes: 20` at the
    top level**, not under `game`.
  - `game.name = "pommerman"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/pommerman"]`,
    `game.runnable.image = "{{POMMERMAN_IMAGE}}"`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/pommerman/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 4/4, `players` 4/4, `slots` 0/4, `collapseTicks` 0/3 — the tandem 0.1.0 scar).
    `tokens` is described as runner-injected; **no `game_config` anywhere in this manifest contains a
    literal `tokens` array** (matriculate rejects "game_config must not include runner-managed
    tokens" — knights-archers 0.1.0), while `config_schema` keeps *requiring* it because the runner
    injects it. Properties: `tokens`, `players`, `slots`, `seed`, `minPlayers`, `maxTicks`,
    `turnTicks`, `bombFuse`, `flameLife`, `startAmmo`, `maxAmmo`, `startBlast`, `maxBlast`,
    `collapseTicks`, `dodgeHorizon`, `turnBudgetMs`, `attempt1Ms`, `retryMs`, `turnSpacingMs`,
    `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `startWaitTicks`, `gameOverTicks`, `fastMode`,
    `showPlayerLabels`, `model`, `maxOutputTokens`, and **`num_agents` (integer, `minimum: 4`,
    `maximum: 4`, default 4)**.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}` (the starter's own enum) and
    `endRule: {"type":"string","enum":["wipe","tickCap","wallClock","fault"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-pommerman/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"radio.md","title":"The radio channel","content":{"type":"uri","value":".../docs/RADIO.md"}}]}`.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). Two entries, `sapper` and `camper`, so **every declared
    player occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 4` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "teams", "name": "2v2 Team Radio (11x11)",
     "description": "Four bombers on an 11x11 grid, two teams of two on the diagonals, 36 command turns. Bombs clear wood and kill; power-ups give extra bombs, longer blasts and the ability to kick. Every turn each seat sends its partner two integers in 1..8 that the game gives no meaning and the opposing team never sees. The outer rings collapse at tick 96 and 120.",
     "game_config": {"players": [{"name":"RED-1"},{"name":"BLUE-1"},{"name":"RED-2"},{"name":"BLUE-2"}],
                     "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"}],
                     "num_agents": 4, "minPlayers": 4,
                     "maxTicks": 144, "turnTicks": 4,
                     "bombFuse": 8, "flameLife": 2,
                     "startAmmo": 1, "maxAmmo": 5, "startBlast": 2, "maxBlast": 6,
                     "collapseTicks": [96, 120], "dodgeHorizon": 6,
                     "attempt1Ms": 8000, "retryMs": 3000,
                     "turnBudgetMs": 12000, "turnSpacingMs": 10000,
                     "wallClockBudgetSeconds": 640, "lobbyJoinTimeoutTicks": 2400,
                     "startWaitTicks": 24, "gameOverTicks": 90,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "blitz", "name": "Blitz (11x11, 96 ticks)",
     "description": "The same rules and the same radio on a 96-tick clock - 24 command turns, rings collapsing at 64 and 80. A faster ladder round with the identical command surface, for divisions that want more episodes per hour.",
     "game_config": {"players": [{"name":"RED-1"},{"name":"BLUE-1"},{"name":"RED-2"},{"name":"BLUE-2"}],
                     "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"}],
                     "num_agents": 4, "minPlayers": 4,
                     "maxTicks": 96, "turnTicks": 4,
                     "bombFuse": 8, "flameLife": 2,
                     "startAmmo": 1, "maxAmmo": 5, "startBlast": 2, "maxBlast": 6,
                     "collapseTicks": [64, 80], "dodgeHorizon": 6,
                     "attempt1Ms": 8000, "retryMs": 3000,
                     "turnBudgetMs": 12000, "turnSpacingMs": 10000,
                     "wallClockBudgetSeconds": 640, "lobbyJoinTimeoutTicks": 2400,
                     "startWaitTicks": 24, "gameOverTicks": 90,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  `tests/test_pom_manifest.nim` asserts that **every** variant's `game_config` constructs a valid
  `GameConfig`, generates a legal symmetric board and spawns exactly four bombers — not just the
  fixture's, because a config-scaled construct that fits the small fixture and breaks the big variant
  is exactly the collab-cooking 0.1.1 failure.

  **Certification fixture** — `num_agents: 4` again, inside `certification.game_config`, and exactly
  four players so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS == 4`
  (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks):

  ```json
  "certification": {
    "players": [{"player_id":"sapper"},{"player_id":"camper"},
                {"player_id":"sapper"},{"player_id":"camper"}],
    "game_config": {"players": [{"name":"RED-1"},{"name":"BLUE-1"},{"name":"RED-2"},{"name":"BLUE-2"}],
                    "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"}],
                    "num_agents": 4, "minPlayers": 4, "seed": 42,
                    "maxTicks": 144, "turnTicks": 4,
                    "bombFuse": 8, "flameLife": 2,
                    "startAmmo": 1, "maxAmmo": 5, "startBlast": 2, "maxBlast": 6,
                    "collapseTicks": [96, 120], "dodgeHorizon": 6,
                    "attempt1Ms": 8000, "retryMs": 3000,
                    "turnBudgetMs": 12000, "turnSpacingMs": 0,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "startWaitTicks": 24, "gameOverTicks": 90,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  The fixture seats `sapper` on both RED seats and `camper` on both BLUE seats, so both declared
  players occupy a slot **and** the stronger baseline wins decisively — the smoke replay therefore
  ends `wipe`, not a flat draw. 144 ticks of scripted play is under a second of sim, but the replay
  is 144 ticks ⇒ **24 s of playback**, which the viewer soak needs. `turnSpacingMs: 0` because the
  offline client is `disabled` and there is nothing to rate-limit. The certify step in
  `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 covers start + connect
  grace + play + the 15 s `gameOverTicks` linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/pommerman-player"`:

  ```json
  [{"name":"pommerman-firestarter","run":"/bin/pommerman-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>"}},
   {"name":"pommerman-cornerman","run":"/bin/pommerman-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"pommerman-sapper","run":"/bin/pommerman-player","env":{"PLAYER_SCRIPTED":"sapper"}},
   {"name":"pommerman-camper","run":"/bin/pommerman-player","env":{"PLAYER_SCRIPTED":"camper"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `sapper` and `camper`, and their
  versions must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the
  **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps
  the template's nimby/Nim toolchain and runs the four shards, and the `docker-smoke` and
  `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `pommerman`, `<IMAGE>` →
  `coworld-pommerman`, **`<SEATS>` → `4`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server).
  `coworld-release.yml` and `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on
  the certify step and a "Confirm canonical" poll between `upload-coworld` and `secret put`
  (atari-cabinet 0.1.0–0.1.3). `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are
  committed **executable** (mode 100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_pom_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and as four shard binaries in `ci.yml`'s `test` job.
`tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_pom_sim.nim`)

1. `bomb fuse and blast` — a bomb placed at tick `t` detonates at `t+8`; its blast is its own cell
   plus `blast−1` cells each direction; it stops **before** rigid and **at and including** wood; it
   passes through passage, power-ups, bombers and other bombs.
2. `chain reaction` — three bombs in a line, only the first fusing, all three detonate on the same
   tick; a fourth outside every footprint does not; the fixpoint terminates with 32 bombs on the
   board.
3. `flame lifetime` — a flame kills on the tick it appears and on the next, and is gone on the third;
   a bomber that walks onto a live flame dies.
4. `wood and power-ups` — wood in a blast becomes passage, is credited once to the bomb owner's team,
   and reveals its hidden power-up **on** that cell; a power-up already lying in a blast is
   destroyed; walking onto a power-up applies it and consumes it; `ammo` and `blast` cap at 5 and 6.
5. `movement` — a move into rigid or wood fails; two bombers into one cell resolve lower-seat-wins;
   no swaps; a bomber that places a bomb does not move that tick.
6. `kick` — a bomber with `kick` moving into a bomb with a clear far cell sets the bomb moving and
   does not move itself; without `kick`, or with the far cell blocked/occupied/aflame, the move
   fails; a moving bomb advances one cell per tick and stops at the first obstruction; a moving bomb
   never enters a flame cell.
7. `simultaneous death` — two bombers on flames from the same detonation both die in one step;
   mutual team annihilation is a draw; `cause` is `suicide` / `friendlyfire` / `bomb` correctly and
   `kills` increments **only** for a cross-team victim.
8. `ammo return` — a bomb's owner regains ammo exactly when that bomb detonates, and never when it is
   removed by a collapse.
9. `collapse` — at tick 96 ring 1 is rigid and a bomber standing there dies `crushed`; bombs and
   power-ups there vanish without detonating; at tick 120 ring 2 goes; the playable set is the 5 × 5
   block afterwards.
10. `radio isolation` — the pair a seat sends on turn `T` reaches **only** its partner and **only**
    on turn `T+1`; over 500 randomised turns no observation for a seat on team `t` ever contains a
    pair sent by a seat on the other team; a fallback seat still sends a pair.
11. `scoring is zero-sum` — over 500 randomised end states, `sum(scores) == 0`, the sign is right,
    both seats of a team hold the identical score, and a mutual wipe with equal wood is a draw.
12. `end conditions` — team wipe, mutual wipe, tick cap and the wall-clock stop each produce the
    right `endRule`, `winner` and `alive`, and the right episode `reason`.
13. `no floating point in the sim` — a source grep over
    `src/pommerman/{sim,board,bombs,control,baselines}.nim` finds no `float`, `sqrt` or float
    literal.
14. `tick budget` — a full 144-tick episode completes in < 1 s in a release build.

**Board** (`tests/test_pom_board.nim`)

15. `map is symmetric and correct` — for 1000 seeds: the board is invariant under `rot(x,y) =
    (10−y,x)`; counts are exactly 57 rigid / 36 wood / 28 passage; the 12 corner-pocket cells and
    `(5,5)` are passage; exactly 20 power-ups (8 extra-bomb, 8 range, 4 kick) sit under wood, 5
    per quadrant-orbit; every non-rigid cell is reachable from `(1,1)` treating wood as passable
    **and** treating wood as solid the moment it is cleared.
16. `spawns` — the four bombers start at `(1,1) (9,1) (9,9) (1,9)` in seat order 0,1,2,3, teams
    RED = {0,2} and BLUE = {1,3}, and each corner's 5 × 5 neighbourhood is a rotation of every
    other's.

**Bounded orders / legality on the scripted baselines** (`tests/test_pom_control.nim`)

17. `baselines are bounded` — for 200 pseudo-random world states (varying alive sets, ammo, blast,
    kick, live bombs, collapsed rings, both variants) and for **both** `sapper` and `camper`: the
    returned order has a `verb` in the enum, `go` coordinates on the board, a `hunt` target that is a
    **living enemy**, a `kick` dir in the enum, a `radio` of exactly two integers in `[1,8]`, and the
    serialised directive ≤ 900 runes. A baseline that ever proposes an illegal or unbounded order
    fails the build.
18. `fallback is the sapper proc` — the decision engine's fallback path and the `sapper` baseline
    resolve to the same proc, so they cannot drift.
19. `the controller never suicides on its own order` — for 500 states, a controller asked to `bomb`,
    `hunt` or `break` either lays a bomb from which the escape BFS finds a safe cell, or lays none;
    and a bomber whose cell is in `danger[0..6]` always takes the escape step, whatever the order.
    Also: a bomber in a genuine dead end with a lit fuse **does** die (the override is not a shield).
20. `reply validation` — the validator accepts the schema; repairs an unknown verb to the previous
    verb, a dead `hunt` target to the nearest living enemy, and out-of-range coordinates by clamping;
    clamps radio integers into `[1,8]` and repeats the previous pair on a missing/malformed one;
    accepts a reply with `radio` and no `order`; rejects a non-object; truncates `say`/`notes` on
    **rune** boundaries at 100/200 with 4-byte emoji sitting exactly on the boundary; caps the read
    at 8192 bytes; and never leaves a bomber unactuated.
21. `baseline tuning is the swept pick` — the shipped `bombEnemyRange` / `powerupSearch` /
    `dodgeHorizon` / `campExits` equal `tools/ci/baseline_tuning.json` (the starter's `test_tuning`
    pattern; `ci.yml` re-runs the sweep with `--check`).

**End-to-end episode writing a replay** (`tests/test_pom_engine.nim`)

22. `episode writes artifacts` — run a real four-seat episode (all seats scripted, no API key so the
    LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert `results.json` and the
    `.replay` are written, `reason == "complete"`, `sum(scores) == 0`, both teammates share a score,
    and the results key set equals the manifest's `results_schema` key set **exactly**.
23. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure
    payload.
24. `budget guard settles early` — with the guard forced, the episode finishes `complete`, not
    `deadline`, and a `budget_guard` record names the turn.
25. `a missing register record is loud` — a seat whose registration packet is dropped produces a
    named warning line in the game log and `policyKinds[seat] == "scripted"` with
    `deadSeats[seat] == false`, so the grf-football failure mode is visible in artifacts.

**Replay** (`tests/test_pom_replay.nim`)

26. `record then re-derive, every end reason` — for `wipe`, `tickCap`, `wallClock` **and** `fault`,
    record an episode and re-derive it from the bytes; assert `hashMismatchTick == -1` and identical
    end state, including at the stop tick (the particle-worlds scar).
27. `replay is self-sufficient` — the bytes alone yield seat names, aliases, teams, policy kinds, the
    full config, the seed, every order record **including both radio integers**, every chat record
    and the result.
28. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports
    `protocol == "pommerman/v1"`.
29. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`,
    kept.

**Manifest** (`tests/test_pom_manifest.nim`)

30. `manifest pins` — `num_agents == 4` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens`
    in any `game_config`; `len(player) == 2` and every declared player seated in
    `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 4`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 640`; **and every
    variant's `game_config` constructs a valid `GameConfig`, generates a legal symmetric board and
    seats exactly four bombers.**
31. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (wants `game.replay_viewer`, no top-level
    `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` — the
    collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_pom_viewer.nim`, static assertions in the `test` job)

32. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals the starter's,
    pinned as a literal.
33. `broadcast html is starter plus block` — the file begins with the starter's classic bytes up to
    the documented splice marker (sha256-pinned) and only appends after it; `broadcast_core.js`'s
    kept procs are byte-identical to the starter's, `pushFeed`'s signature included.
34. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap); the beat builder is `pomBeat`, never
    `markBeat`.
35. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{firstblood, kick, death, collapse, fallback, end}`.
36. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()`
    sets `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the
    band; every seek clears `#endcard.on`; the three 360 px rules exist; the removed ids
    (`#viewpanel`, `#minimap`, `#zoombar`, `#fpv*`, `#povBadge`, …) appear nowhere.
37. `endcard labels` — `tests/test_pom_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
38. `label manifest` — the starter's `test_label_contract` pattern: the emitted sprite-label
    vocabulary equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.

**Viewer smoke — the bundle is EXECUTED, not merely built**

39. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer`
    job**, which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced**
    (downloaded as the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in
    both the npm module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay"
    --timeout 90 --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"`
    (or the bridge `ready` posted after it) arrives, `data-replay-error` never appears, the
    clock/tick readouts **advance** across the soak, and `canvas_text.never_inside == 0` — this is a
    fixed board, so `--strict-text-bounds` stays on. The 24 s replay comfortably outlasts the 10 s
    soak (the ecos scar).
40. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `say` at all**, so
    the smoke replay can never exercise the feed's or the speech bubble's text path (the cogchemists
    2026-08-24 scar). The fixture **loads the shipped `dist/static-replay-viewer/index.html` in an
    iframe** and shims only the wasm entry — it does not re-implement the drawing (the
    particle-worlds 2026-08-26 scar) — re-points the iframe's `window.parent` so the shell's own
    bridge `ready` cannot end the harness early, installs the `fillText`/`strokeText` measurer on the
    **iframe's** `CanvasRenderingContext2D` and publishes the merged report as top-level
    `window.__coworldTextBounds`. It drives the real page with a **full-cap 100-rune `say` on all
    four seats**, padded with `·` (U+00B7), never `…` (the fog-of-war-boards 2026-08-27 scar), and
    asserts the drawn string is **exactly** 100 runes, at canvas widths 360, 640 and 1280 px.
41. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.

---

## Out of scope (v1)

- **Free-for-all.** The idea's other mode is not shipped. FFA is where two seats gang up on a third —
  the classic Pommerman exploit the idea's own integrity note names — and it would break the exactly
  zero-sum claim. `num_agents` stays 4 and teams stay server-assigned by slot parity in every
  variant. Adding FFA later is a new variant with a different score formula, not a change to these
  rules.
- **The partial-observability variant.** v1 gives every seat the whole board (what lies under
  unbroken wood is the only board fact hidden). A fog variant means a per-seat view radius, a
  last-seen memory in the observation, a fog layer in the replay config and a spectator/seat split in
  the renderer — a follow-up, not a v1 toggle. The radio's value in v1 comes from *intent* being
  private, not from position being hidden.
- **Per-tick LLM control at 2 Hz.** 144 ticks × 4 seats is 576 calls minimum, which does not fit
  720 s. Commanders issue one order per 4-tick turn and a deterministic controller executes it. The
  order vocabulary is deliberately small; a commander never names a raw action index or a cell-by-cell
  path.
- **Bomberland's additions beyond the shrinking arena.** The larger map, the different item table,
  the ore/HP blocks, the detonator (remote-triggered bombs), the freeze mechanic and Coder One's own
  web replay are all out. What this coworld takes from Bomberland is the collapsing arena, and it
  takes it as two rigid rings at fixed ticks.
- **Upstream's random map generator and its connectivity repair pass.** v1 generates a 4-fold
  rotationally symmetric board that is connected by construction, because a league needs positional
  fairness across four seats more than it needs upstream's exact spawn distribution.
- **Upstream's RL observation tensors, its `SimpleAgent`, its docker-evaluation harness, and any
  pretrained Pommerman weights.** No weights are vendored, no inference module ships, and no seat
  receives an observation tensor.
- **Best-of-N episodes and side swaps.** One game per episode: the symmetric map removes the reason
  paintbot's `maxGames: 2` exists. The loop that would run a second game is kept in `server.nim` so a
  future variant is a config change.
- **Teams larger than two, and boards other than 11 × 11.** `num_agents` is 4 in every variant.
- **A radio vocabulary the game assigns meaning to.** The two integers stay uninterpreted by the sim,
  the score and the viewer; the viewer draws the digits and nothing else. Any semantics that appear
  are the policies'.
- **Live spectating.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, vision cones, fog-of-war
  rendering, the first-person PIP, paint, hills, hearts, flags, grenades, med kits, shields,
  barriers, trenches, perks, handicaps, lives, respawning, four-team play, achievements, campaign
  mode, the procedural map generator, the map pool, the map editor and mapkit — all deleted, not
  disabled (§Sim module), and none of them return in v1.
