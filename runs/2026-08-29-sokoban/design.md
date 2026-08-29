# cogame-sokoban — design note (2026-08-29)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` importing and re-exporting the sim
modules; `sim_types.nim` owning `GameVersion`, `TargetFps* = 24` (`src/ctf/sim_types.nim:376`) and
the rune caps `ShoutMaxChars`/`MaxNoteRunes`/`MaxSayRunes`/`MaxPromptRunes`
(`src/ctf/sim_types.nim:747, 794-799`), with its prepend-only changelog-comment discipline and the
flatty wire types whose field order is sacred); the mummy HTTP/websocket server implementing the
Coworld contract including its `wallClockBudgetSeconds` stop (`src/ctf/server.nim:1407-1417`); the
`decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` / `control.nim` commander layer with
its one-batch-per-turn shape (`src/ctf/decide.nim:427` `engine.client.curl.makeRequests`), its
`attempt1Ms` / `retryMs` / `turnBudgetMs` / `turnSpacingMs` deadlines (`src/ctf/decide.nim:386-389,
406`), its tolerant JSON extraction (`src/ctf/directives.nim:102`), its rune truncation
(`src/ctf/directives.nim:61-68`) and its fallback ladder with the exact two log phrasings
(`src/ctf/decide.nim:463` for attempt 1, `:491` "falling back" only on the second failure); the
binary `COWLDCTF` replay of *inputs plus a per-tick `gameHash`* (`src/ctf/replays.nim:142`),
re-simulated by **the same sim module** compiled to wasm by `replay-viewer/config.nims`; the
`client/` broadcast chrome (`chrome_common.js` + `broadcast_core.js` + `replay_broadcast.html` with
its `window.PaintballChrome.install(PB_CTX)` splice hook at `client/replay_broadcast.html:4330-4337`
and the game-block banner at `:4344`); nimby + `Dockerfile` + `Dockerfile.replay-viewer` +
`tools/build_replay_viewer.sh`; and the Nim test suite with its four shards (`tests/shard_1..4.nim`,
`tests/config.nims`).

Starter choice, one line: **this is a real-time tick loop whose rules are written into this repo and
whose single seat is an LLM dispatcher over a deterministic per-tick driver — the first row of the
starter table** (`prompts/10-design.md` §Starter table: "any real-time game loop (grid OR continuous
physics), new rules written for this coworld"). It is deliberately **not** the `cogame-moba`
bit-exact-port row: gym-sokoban is a Python/gym package and Boxoban is a 1.5 M-level text dataset;
neither can be embedded in a module that must also compile to wasm for the static replay viewer,
which is a non-optional pin. What this repo implements is the *problem* — 10 × 10 four-box Sokoban
with irreversible pushes, tiered by exact optimal push count — on its own deterministic, seeded,
integer Nim sim. Every divergence from the sources is named in §Sim module → "Documented
divergences" and mirrored into `docs/LEVELS.md`. The precedent for forking paintbot for a
single-agent grid puzzle is two deep and recent (cogame-minigrid and cogame-crafter, both
2026-08-28).

Where this note departs from coworld-ctf it says so. The departures are: the rules are Sokoban's,
not paintbot's (§Sim module lists what is deleted); the board is a fixed 10 × 10 integer **cell
grid** built by a seeded generator, so ctf's pixel arena, procedural map generator, map pool, map
editor and mapkit are deleted; there is **one seat, not eight**, and no teams; the game is
**perfect information**, so ctf's fog, vision cones and raycasting are deleted outright rather than
replaced; and `MaxSayRunes` / `MaxNoteRunes` are re-pinned (§Decisions → reply schema).

### Source idea (verbatim)

> SA Sokoban — push every box onto a goal; one wrong push and the level is dead
>
> Single-agent coworld over gym-sokoban / Boxoban (DeepMind's 1.5M procedurally generated levels, tiered unfiltered / medium / hard). 10×10 grid, push boxes onto targets, boxes can't be pulled — irreversible mistakes make it the canonical planning benchmark (used for MuZero, Thinker, and LLM reasoning evals). Score = levels solved from a held-out set within a step budget, weighted by tier.
>
> Seats: 1
> Motive: puzzle solve rate
> Policy interface: one move per tick; text-renderable, so LLM policies play it directly — reasoning-model vs search ladder
> Fills gap: pure planning with irreversibility; nothing on the site isolates lookahead this cleanly
> Integrity: held-out levels; step cap; deterministic.
>
> Replay plan (watchability): simple grid; 'deadlock created' marker when a box gets cornered.
>
> Source: github.com/mpSchrader/gym-sokoban; github.com/google-deepmind/boxoban-levels.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time tick loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-sokoban` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=pusher\|nudger`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance, byte-for-byte `chrome_common.js`, starter art + install-time bakes) |
| Two name spaces | §The game → Seats and aliases (in-game alias `Alpha`; real policy names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions → Cadence (typical 246 s, worst 667 s, engine stop 690 s, budget 720 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 1`, three times |
| Per-turn LLM call budget stated (single seat) | §Decisions (exactly one request per turn, two with the retry; ≤ 120 per episode) |
| Replay bytes self-sufficient | §Server → Replay bytes (names, config, the six level grids, per-turn plans, per-tick hashes, seed) |
| Rune-boundary truncation on every free-text field | §Decisions → Reply schema and per-field caps |
| Held-out levels, step cap, determinism (the idea's integrity note) | §Sim module → Level sourcing (levels are a pure hash of a runner-randomised seed the seat never sees; `stepBudget` 200 moves/level; integer-only sim) |

---

## The game

One cog, alone, in a 10 × 10 walled room with four crates and four marked squares. It can walk, and
when it walks into a crate the crate slides one square ahead of it. **It can never pull.** A crate
shoved into a corner is there forever; a crate shoved against a wall in a row with no marked square
on it is there forever; four crates shoved into a 2 × 2 clump are there forever. The level is over
the instant the position becomes unwinnable — that is the whole game, and the replay says so out
loud with a **DEADLOCK CREATED** marker on the scrubber.

An episode is a **ladder of six levels**, each generated fresh from the episode's secret seed, each
labelled with the tier it was built to (`unfiltered`, `medium`, `hard`) and its **exact optimal push
count**. Each level gets a hard **step budget of 200 moves**. The league reads one number: the
tier-weighted count of levels solved.

Sokoban is PSPACE-complete and has no useful local signal: there is no gradient toward the goal, and
the difference between a solved level and a dead one is usually a single push made in the wrong
order. That is exactly what this coworld exists to measure, and why the idea's own framing —
"reasoning-model vs search ladder" — is literally what the four shipped policies are.

### Seats and aliases

- **`num_agents` = 1.** Exactly one seat, always — in both manifest variants and in the
  certification fixture. This is the idea's own "Seats: 1", and it is what Sokoban is: a solitaire
  planning puzzle. Every episode is a solo run; policies are compared across episodes, never within
  one.
- **Two name spaces.** In-game the seat is **`Alpha`** — `IdentityNames[0]` from the starter's
  `src/ctf/roster.nim:64-65` (`"alpha"`), title-cased by `seatAlias(slot)`. That alias is the only
  name that appears in an observation, in a prompt, in a `say`, or drawn on the board. The seat's
  **real policy/player name** (`daveey`, `daveey-1`, `Baseline (1)`) lives only in `results.names`,
  in the replay's join record, and spectator-side in the viewer's scorebug plate and endcard.
  `showPlayerLabels` is **false**, as in the starter's paintball variant, so nothing drawn on the
  board leaks an identity. With one seat there is nobody to meta-game against, but the pin is
  satisfied both ways, not either way: the alias is what the model sees, the real name is what the
  spectator sees.

### The board and its notation

Every level in every variant is played on the **same board size**: a **10 × 10** grid of cells,
`gridSize = 10`, indexed `(x, y)` with `x` the column `0 … 9` (west → east) and `y` the row `0 … 9`
(north → south). `(0, 0)` is the north-west corner. **The entire border ring is wall**, so the
playable interior is 8 × 8 = 64 cells. This is gym-sokoban's and Boxoban's own board size and it
never changes: it is what lets `relayout()` letterbox a square board at any width (§Viewer → Legible
at 360 px) and what makes `{"do":"goto","x":..,"y":..}` a stable contract.

A cell is one of: **wall**, or **floor**; independently, a floor cell may hold **the player** and may
hold **a box**, and may be **a target**. `boxCount = targetCount = 4` on every level, every tier —
Boxoban's own count.

The board is rendered to the seat, to the tests and to `docs/RULES.md` in **canonical XSB
notation**, the format every published Sokoban level and every Sokoban solver on the internet uses,
and therefore the format an LLM has actually seen:

| Glyph | Means |
|---|---|
| `#` | wall |
| (space) | empty floor |
| `.` | target, empty |
| `$` | box, not on a target |
| `*` | box, on a target |
| `@` | player, on plain floor |
| `+` | player, standing on a target |

Rows are always exactly 10 characters and there are always exactly 10 of them; leading and trailing
spaces are significant and are never trimmed. No other glyph is ever emitted or accepted.

### Directions and the four primitives

`Dir` is a closed enum in this fixed order, used for every tie-break in the game:
**`U` (y−1), `D` (y+1), `L` (x−1), `R` (x+1)** — indices 0, 1, 2, 3.

There are exactly **four primitives**, one per direction, plus `wait`. A primitive is one **tick**
and one **move** against the step budget, whether or not it changes anything.

### Level tiers, and where levels come from

Three tiers, distinguished **only** by the level's *exact* optimal push count `optPushes` — the
minimum number of pushes in which the level can be solved, known exactly because of how levels are
generated (§Sim module → Level sourcing):

| Tier | `optPushes` band | Weight |
|---|---|---|
| `unfiltered` | 6 … 12 | **1** |
| `medium` | 13 … 22 | **2** |
| `hard` | 23 … 34 | **3** |

The names and the three-way split are Boxoban's. The bands are this repo's, chosen so that a
bounded search baseline clears most of `unfiltered`, some of `medium` and little of `hard` — the
ladder the idea asks for. `optPushes` is recorded per level in `results` and in the replay, and it
is **shown to the seat**: knowing "this is solvable in 17 pushes" is a legitimate part of a Sokoban
statement and it is what makes a wasted push legible to a spectator too.

### The ladder, and the clock

- **Tick** = one primitive by the cog. **`turnMoves = 20`**: every command turn executes at most
  twenty primitives.
- **`levelTurnCap = 10`** turns per level ⇒ **`stepBudget = levelTurnCap × turnMoves = 200`** moves
  per level. `stepBudget` is the idea's "step cap" and the identity is asserted in the manifest test.
- **`levelCount = 6`** levels per episode ⇒ **`maxTurns = 60`**, **`maxTicks = 1200`**.
- One game per episode (`maxGames = 1`): a ladder has no side to swap.
- Levels run **strictly in the variant's declared tier order**, one at a time, and are generated
  **lazily** — level `k`'s grid is built when level `k` starts, so a level the episode never reaches
  costs nothing.
- A level that finishes (solved, deadlocked, out of steps) **ends its turn immediately**: the
  remaining primitives of that turn are discarded and the next level begins on the next turn. Turns
  saved this way are **not** transferable — they simply shorten the episode.
- Between turns the tick loop runs **uncapped** (`fastMode: true`); 1200 ticks over a 100-cell grid
  is well under a second of CPU. The wall clock of an episode is the ≤ 60 LLM turns (§Decisions).

**Variants** (both `num_agents: 1`):

| Variant | Tier ladder (in order) | `maxWeight` | `parWeight` |
|---|---|---|---|
| `ladder` | `unfiltered`, `unfiltered`, `medium`, `medium`, `hard`, `hard` | 1+1+2+2+3+3 = **12** | **5** |
| `hard` | `medium`, `medium`, `hard`, `hard`, `hard`, `hard` | 2+2+3+3+3+3 = **16** | **6** |

`ladder` is the reporting variant: it walks the three Boxoban tiers in order, so a division's
episodes yield a per-tier solve rate directly. `hard` exists because a strong reasoning policy will
saturate `unfiltered` and the interesting separation is at the top of the distribution.

### Turn and tick structure — the exact resolution order

Per **command turn** `T`, in this order:

1. If the current level has finished, record its result, emit `failed`/`solved`, and start the next
   level: generate it (§Sim module → Level sourcing), place boxes and player, emit `levelstart`. If
   there is no next level, end the episode (§End conditions).
2. Build the seat's observation object (§Decisions → observation) from the **current** state,
   including the player-reachability flood that `pushes_available` needs.
3. Issue the seat's LLM request. There is exactly **one** seat, so this is a batch of one through
   the starter's unchanged `engine.client.curl.makeRequests` path (`src/ctf/decide.nim:427`) — the
   code is the starter's batching code carrying one request. Attempt-1 deadline `attempt1Ms = 6000`.
   A scripted seat computes locally, instantly, and consumes no request.
4. If the seat timed out, errored, returned non-JSON, or returned no usable `actions` array, it is
   retried **once**, `retryMs = 3000`.
5. Still no usable reply → the **`pusher`** scripted plan is computed server-side (the same proc the
   `pusher` baseline uses — imported, never duplicated) and a `fallback` record is written.
6. **Validate and expand the plan**, in the order the reply lists it:
   a. Entries past `maxActionsPerTurn = 8` are dropped and counted in `actionsDropped`.
   b. Each entry is validated against the reply schema; an entry that does not validate is
      **dropped** (never rewritten into a different action), counted in `repliesRepaired`, and
      reported back next turn.
   c. Macros are expanded against the **turn-start snapshot** of the board: `moves` into its literal
      primitive sequence, `goto` into the BFS walk, `push` into the BFS walk to the pushing square
      followed by `times` primitives in `dir` (§Decisions → the driver). Each macro yields at most
      `macroPrimitiveCap = 32` primitives. A `goto` or `push` whose approach square is not reachable
      through free floor yields **zero** primitives, counts in `macrosUnreachable`, and is reported
      next turn as `unreachable`.
   d. The whole expanded queue is truncated to `turnMoves = 20` primitives; the surplus is discarded
      and `planTruncated` is reported next turn. **Nothing carries over to the next turn.**
7. `say` (≤ 140 runes) and `notes` (≤ 320 runes) are sanitised on rune boundaries and, with the
   accepted plan, written as the turn's `directive` replay record. `notes` is echoed back to this
   seat next turn and to nobody else; `say` is drawn in the spectator feed.
8. `turnSpacingMs = 2600` is a floor on the wall clock between consecutive request **starts** (the
   starter's mechanism at `src/ctf/decide.nim:386-389`, kept), which pins the steady state at
   23 req/min against the sidecar's 30/min per-episode cap.

Then, for each of the next `turnMoves` ticks, in this order — **this is the whole physics of the
game and nothing else mutates the world**:

1. `tick += 1`; `levelMove += 1`.
2. Pop the next primitive from the queue. If the queue is empty the primitive is **`wait`** (a real
   cost: the move is spent).
3. **Apply the primitive.** For a direction `d`, let `A` be the cell adjacent to the player in `d`
   and `B` the cell beyond `A` in `d`:
   a. `A` is **wall** → nothing happens. `blockedMoves += 1`.
   b. `A` holds a **box**, and `B` is a wall or holds a box → nothing happens. `blockedMoves += 1`.
      **This is the only place a push can fail, and boxes are never moved by anything else — there
      is no pull, no undo and no restart.**
   c. `A` holds a **box** and `B` is free floor → the box moves `A → B`, the player moves into `A`,
      `pushes += 1`, `boxMoved = true`. Emit `boxon` if `B` is a target, `boxoff` if `A` was a
      target.
   d. Otherwise (`A` is free floor) → the player moves into `A`.
   `wait` → nothing happens.
4. **`boxesOnTargets`** is recomputed; `levelBoxesPlaced = max(levelBoxesPlaced, boxesOnTargets)`.
5. **Level termination**, evaluated in this order and only when `boxMoved` is true (nothing else can
   change any of the three predicates):
   a. `boxesOnTargets == 4` → **`solved`**; emit `solved`.
   b. `isDeadlocked(state)` (the exact detector below) → **`deadlocked`**; emit `deadlock` carrying
      the `kind` and the offending box's cell.
   c. Otherwise fall through.
6. `levelMove == stepBudget` → **`outofsteps`**; emit `failed`. (Checked on every tick, `boxMoved`
   or not.)
7. Mix the tick into `gameHash` and append it to the replay's hash chain.
8. If the level finished at step 5 or 6, **break out of the tick loop** — the turn ends early.

### Deadlock detection — the exact rule

`isDeadlocked(state)` is **sound and deliberately incomplete**: it never flags a position that is
still winnable, and some unwinnable positions are not flagged and simply burn out on the step
budget. Soundness is what makes "the level ends the instant it goes dead" honest; completeness would
require solving the level. It is the disjunction of exactly three tests, evaluated in this order,
and the first that fires supplies the `kind` recorded in the `deadlock` event:

1. **`dead_square`** — some box that is **not on a target** stands on a cell in the level's static
   dead-square set `D`. `D` is computed **once per level, at generation time, from walls and targets
   only** (never from box positions, which is what makes it sound):
   - Mark every target cell `alive`.
   - Repeat to a fixpoint: for every `alive` cell `c` and every direction `d`, mark `c − d` `alive`
     if `c − d` is floor **and** `c − 2d` is floor. (That is: a box on `c − d` could have been pulled
     to `c` by a player standing on `c − 2d`, ignoring all other boxes.)
   - `D` = every floor cell not marked `alive`.
   A box on a cell of `D` can never reach any target under any sequence of pushes, so the position is
   lost. `D` is what catches the corner shove and the box-against-a-bare-wall shove — the idea's "a
   box gets cornered".
2. **`frozen_block`** — there is a 2 × 2 block of cells (top-left at any `(x, y)` with
   `0 ≤ x ≤ 8`, `0 ≤ y ≤ 8`) in which **all four cells are wall-or-box** and **at least one is a box
   not on a target**. No box in such a block can ever move again.
3. **`no_push`** — at least one box is off-target **and** the set of legal pushes is empty. The legal
   pushes are enumerated as: for every box at `c` and every `d`, the push is legal iff `c + d` is
   free floor and `c − d` is free floor **and** `c − d` is in the player's reachable region (a
   4-connected flood from the player's cell through free floor, boxes blocking). If no box can be
   pushed at all and the level is unsolved, it is over.

Tests 1 and 2 are the ones that fire in practice; test 3 is the catch-all that guarantees the sim
can never spin out a level in a frozen position. All three are integer set operations over ≤ 100
cells and cost microseconds.

### Scoring formula and sign

At the end of the episode, over the six levels `i = 0 … 5`:

```
weight(unfiltered) = 1,  weight(medium) = 2,  weight(hard) = 3

solved[i]        = 1 if levelOutcome[i] == "solved" else 0
placed[i]        = the MAXIMUM number of boxes simultaneously on targets during level i   (0 .. 4)
saved[i]         = (stepBudget - levelMoves[i]) if solved[i] else 0                       (0 .. 199)

solvedWeight     = sum over i of weight(levelTier[i]) * solved[i]        (0 .. 12 ladder, 0 .. 16 hard)
boxCredit        = sum over i of placed[i]                               (0 .. 24)
movesSavedTotal  = sum over i of saved[i]                                (0 .. 1194)

scores[0]        = 1_000_000 * solvedWeight
                 +    10_000 * boxCredit
                 +         1 * movesSavedTotal
```

**Sign: higher is better, and every term only ever adds** — `scores[0]` is never negative, and the
minimum, 0, is the honest score of a cog that solved nothing and never got a box onto a target.
There is **no penalty term for deadlocking**: creating a deadlock already costs the level, and a
second penalty would make a cog that shuffles safely and solves nothing outrank one that solved four
levels and blew the fifth. `deadlocks`, `outOfSteps`, `blockedMoves` and `pushesTotal` are recorded
and shown, never scored.

**The ordering is strictly lexicographic, by construction:**

- one more unit of tier weight is worth `1_000_000`, and the largest possible total of the other two
  terms is `10_000 × 24 + 1_194 = 241_194 < 1_000_000` — **tier-weighted solves first, always**;
- one more box parked on a target is worth `10_000`, and the largest possible speed total is
  `1_194 < 10_000` — **partial progress second**;
- moves saved is the last tie-break, worth 1 a move.

Maximum attainable: `ladder` `12_000_000 + 240_000 + 1_194 = 12_241_194`; `hard`
`16_000_000 + 240_000 + 1_194 = 16_241_194`. `tests/test_sokoban_scoring.nim` asserts the formula,
both dominance bounds and both maxima, analytically and over 500 randomised end states.

**The league ranks by `results.scores[0]`.** With one seat every episode is a solo run and the
platform's Elo (1000 start / K 32) is computed from these per-episode per-seat numbers; a policy
climbs by solving more and harder levels across more seeds — the idea's "puzzle solve rate".
`results.win[0]` is `solvedWeight >= parWeight` (a "did the cog clear the bar" flag, not a duel), and
**`results.winner` is `0` when `win[0]` is true and `null` otherwise** — there is no opponent, so the
only honest winner is the seat itself or nobody.

**Measured but never scored:** `pushesTotal`, `blockedMoves`, `deadlocks`, `outOfSteps`,
`levelPushes`, `levelMoves`, `actionsDropped`, `macrosUnreachable`, `repliesRepaired`. All are in
`results`, on the endcard and in the feed.

**Integrity (the idea's note), decided.** *Held-out levels*: the episode `seed` is randomised by the
runner and **never appears in any observation or prompt**; every level is a pure function of
`(seed, levelIndex, tier)` over a 2⁶⁴ seed space, so no policy can have memorised the level it is
playing, and no level is fetched from anywhere at runtime (§Sim module → Level sourcing). *Step cap*:
`stepBudget = 200` moves per level, enforced at tick step 6. *Deterministic*: integer-only sim, one
hashed seed source, a per-tick hash chain (§Sim module → determinism).

### End conditions and legal `results.reason` values

The episode ends at the first of: **the ladder finishing**, the **turn cap**, or the **wall-clock
stop**.

- **Ladder complete** — all six levels have resolved (`solved`, `deadlocked` or `outofsteps`).
  Settles immediately.
- **Turn cap** — `turnsPlayed == maxTurns` (60). Reachable only if every level ran its full ten-turn
  window, in which case it coincides with the ladder finishing; it is kept as an independent guard so
  no arithmetic error can produce an unbounded loop.
- **Wall-clock stop** — the engine's `wallClockBudgetSeconds` guard, the starter's check at
  `src/ctf/server.nim:1407-1417`, kept.

`results.reason` is the starter's closed enum; **exactly these three values are legal** and the game
emits nothing else:

- **`complete`** — the episode finished on its own terms: the ladder ran out of levels, or the turn
  cap fired. The healthy value. `results.endRule` says which: `ladderComplete` | `turnCap`.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (**690 s**). The engine stops at
  the current tick, settles with the **real** levels solved so far (never zeroed, so a deadline
  episode is still rankable), marks every unstarted level `levelOutcome = "unreached"` with
  `levelMoves = 0`, `levelTurns = 0`, `levelPushes = 0`, `levelBoxesPlaced = 0`, writes
  `results.json` and the replay, and exits 0. `results.endRule = "wallClock"`. **Declared
  acceptable** for `docs/SPEC.md` §Definition of done check 4. The budget guard below exists so it
  should never fire.
- **`fault`** — an unexpected exception in the sim or the loop. Caught; the episode is settled from
  the last completed tick, `results.endRule = "fault"`, `results.stopDetail` names it (≤ 200 runes,
  rune-truncated), artifacts are still written, exit 0. A defect: `tools/ci/docker_smoke.sh` fails
  the build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum: `ladderComplete | turnCap | wallClock | fault`.

`results.levelOutcome[i]` is a closed enum: **`solved` | `deadlocked` | `outofsteps` | `unreached`**.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × turnBudgetMs > wallClockBudgetSeconds`, the LLM is switched off for every remaining
turn (the seat falls to `pusher`, microseconds per turn), the remaining levels still play out at full
speed, and the episode still ends `complete`. A `budget_guard` record names the turn it fired (the
starter's guard at `src/ctf/decide.nim:328-346`, kept).

**A silent seat does not end the episode.** A seat that never connects, disconnects mid-episode, or
fails every decision is driven by `pusher` and the ladder runs to its natural end with
`deadSeats[0] = true`. Nothing a player container does can stop the clock: the starter's
`lobbyJoinTimeoutTicks` bounds the lobby, and a silent seat cannot consume more than the per-turn
deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes the seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {pusher, nudger}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=pusher` (the starter's "anything unrecognised is the published default" rule at
`src/ctf/baselines.nim:52-58`). **A scripted policy seated as a champion is a failure state.**

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/sokoban/anthropic_api_key` — the hive
2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/sokoban_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar) — the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"pusher"|"nudger"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at 64 runes, then
acknowledge frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3
close-frame race: whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/sokoban/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION` / `AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (via `readCogameUri`) → **none**, in which case the
  client is `disabled = true` and every turn falls back instantly with no network wait, so offline
  certification finishes in seconds.
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 900` (not 400 — "cut off at max_tokens"). **No `output_config.effort`** when the
  model string contains `haiku` or `4-5`. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**, and the assistant turn is **prefilled with
  `{`** (both Anthropic Messages and Bedrock invoke accept it; the prefill is re-prefixed before
  parsing and a provider that echoes it is guarded) — the procgen 0.1.2 `cut off at max_tokens` fix,
  taken from day one rather than after the fact.
- `extractJsonObject` (`src/ctf/directives.nim:102` — outermost balanced `{…}`, fence-tolerant,
  tolerant of trailing prose) and `truncateRunes` / `sanitizeSay` / `sanitizeNote`
  (`src/ctf/directives.nim:61-90`) unchanged.

### Cadence, the per-turn call budget, and the wall-clock arithmetic

One command turn every ≤ 20 ticks; **at most 60 turns per episode**. **The per-turn LLM call budget
is exactly ONE request, plus at most ONE retry** — there is a single seat, so the starter's
one-parallel-batch-per-turn machinery (`src/ctf/decide.nim:427`) carries a batch of one and is
otherwise untouched. **At most `60 × 2 = 120` provider calls per episode**, never more than one in
flight.

```
attempt1Ms                          6.0 s   (whole seconds - sim_config.nim:695-706 rejects otherwise)
retryMs                             3.0 s   (whole seconds; attempt1Ms + retryMs <= turnBudgetMs - :691)
turnBudgetMs                        9.0 s   (monotonic deadline around the whole turn)
turnSpacingMs                       2.6 s   -> 1 seat x 60/2.6 = 23 req/min  (sidecar cap: 30)

60 turns x max(spacing 2.6 s, latency ~3.4 s)  typical            = 204 s
60 turns x turnBudgetMs 9.0 s, absolute worst                     = 540 s
6 lazy level generations, bounded backward BFS (genNodeCap 200k)  =   6 s   (worst; ~0.3 s typical)
1200 ticks of integer grid work + deadlock tests, fastMode        =   1 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400 = 100 s at       =  15 s   (cap: 100 s)
   TargetFps 24; typical 15 s)
gameOverTicks hold + results + replay write (retried uploader)    =  20 s
                                                                  -------
typical total                                                     = 246 s   < 720 s
absolute worst case (540 + 6 + 1 + 100 + 20)                      = 667 s   < 690 s stop
engine hard stop wallClockBudgetSeconds                           = 690 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                             = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 690 and `tests/test_sokoban_manifest.nim` asserts it. The typical
figure is conservative: a level that solves or deadlocks early ends its turn immediately, and a
strong policy uses well under 60 turns.

**Rate guard.** `turnSpacingMs` pins the steady state at 23 req/min, but a run of retrying turns
issues two requests each. The engine therefore keeps a **rolling 60 s request counter**: if issuing
the next request would push the trailing-60 s count above **28**, that turn skips the call and takes
the `pusher` plan with `cause = "rate_guard"`. Bounded, logged, never a sleep on the episode's
critical path (the raid round 2 sidecar-throttle scar).

`fastMode: true` in every variant, as in the starter's paintball variant: the seat sends no per-tick
inputs (the server computes every primitive), so the Sprite v1 Ready packet's dead-reckoning hazard
cannot arise.

### Degrade, never hang

Every wait is bounded: the two request deadlines, the outer `turnBudgetMs`, the rate guard, the
generator's `genNodeCap` / `genAttemptCap`, the baseline solver's `baselineNodeCap`,
`lobbyJoinTimeoutTicks`, mummy's socket timeouts on the serve thread (which runs independently of the
game loop, so a 9 s LLM stall cannot drop a connection or stall `/healthz`), the 690 s engine stop,
and ctf's `gameOverTicks` hold before exit — kept so `/healthz` and `/global` keep answering for a
bounded grace after artifacts are written (the lantern 0.1.3 `/global` ping scar).

On the seat's timeout or parse failure: **retry once**; on the second failure that turn's plan
becomes the **`pusher`** scripted plan computed inside the game (the same proc the `pusher` baseline
uses — imported, never duplicated), and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns` counts them. The attempt-1 notice says **`will retry`**; only
a genuine second failure logs **`falling back`** (the pommerman 0.1.1 phase-60 grep scar; the
starter's two phrasings live at `src/ctf/decide.nim:463` and `:491`).

**No failure mode leaves the cog without a move.** The tick loop always has a primitive: the turn's
queue, else `wait`, which is a legal state that costs a move and nothing else. A seat that never
connects is reported once to `COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload —
exactly `{"message", "failed_policy_index"}`, nothing else.

**The episode settles early rather than overrunning**: a level ends the moment it is solved or dead,
the ladder ends the moment its sixth level resolves, and the budget guard drops the seat to scripted
play the moment two more full turns would not fit.

### Per-seat observation: exactly what is visible and what is hidden

**Sokoban is perfect information and this game keeps it that way.** The cog sees the entire board.
There is no fog, no partial view and no hidden object; the difficulty is entirely lookahead, which is
the idea's "pure planning with irreversibility ... nothing on the site isolates lookahead this
cleanly". Hiding anything would turn a planning benchmark into an exploration benchmark.

**Visible.**

- **The rules of the world, once, at registration** — `gridSize` 10, the XSB glyph legend, the four
  directions, `turnMoves`, `levelTurnCap`, `stepBudget`, `levelCount`, `maxActionsPerTurn`, the three
  tiers and their weights, and the fact that boxes cannot be pulled and a dead level ends
  immediately. Static; afterwards referred to by id.
- **The whole board**, `board`: ten strings of ten XSB characters — the text rendering an LLM policy
  receives, and exactly what the tests and `docs/RULES.md` print.
- **The same board structurally**, so no model has to parse ASCII to act: `player {x, y}`,
  `boxes [{i, x, y, on_target}]` sorted ascending by `(y, x)` (**`i` is the index the `push` action
  takes, re-derived every turn from that order and stable within a turn**), and
  `targets [{x, y, filled}]` sorted the same way.
- **`dead_squares`** — the level's static dead-square set `D` as a list of `[x, y]`, computed by the
  flood in §The game → Deadlock detection. It is a pure function of walls and targets, derivable by
  anyone from `board`, and handing it over deliberately moves the game off "can the model do a
  corner-detection subroutine correctly" and onto **push ordering and freeze deadlocks**, which is
  what the benchmark is for. Precedent: escrow 0.1.3 — precomputing a legal/derived set in the
  observation is the single most effective anti-fallback measure in this fleet.
- **`pushes_available`** — every push that is legal *right now*: `{box, dir, to: [x, y]}` for each
  box index and direction whose push passes the legality test in §The game → Deadlock detection
  test 3 (including player reachability). **It carries no deadlock annotation**: the model must
  cross-reference `to` against `dead_squares` itself and must reason about freezes on its own. That
  line is where this game stops being bookkeeping and starts being Sokoban.
- **The current level** — its index (`1 … 6`), its `tier`, its `opt_pushes`, `moves_left`,
  `turns_left`, `pushes_made`, `boxes_on_targets`.
- **Its own last turn** — `last_turn`: `executed` (the LURD string that actually ran), `pushes`,
  `blocked` (primitives that hit a wall or a stuck box), `truncated`, `dropped`, `unreachable`, and
  `notes` echoed back.
- **Its own progress** — `levels_solved`, `solved_weight`, and the tier of each level already played
  with its outcome.

**Hidden.** The episode **seed**; the levels of any tier not yet started (their grids do not exist
until their level begins); the level's *solution* (the generator knows a 17-push solution; the seat
is told only that one exists); the agent's own **score**; and its own real player/policy name.
Nothing about identity ever reaches a prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `notes`) into
the replay's `directive` record, so the replay explains every decision.

```json
{
  "you": "Alpha",
  "level": {"index": 3, "of": 6, "tier": "medium", "opt_pushes": 17,
            "moves_left": 162, "turns_left": 8, "pushes_made": 5,
            "boxes_on_targets": 1},
  "turn": 23, "tick": 421,
  "world": {"size": 10,
            "legend": {"#": "wall", " ": "floor", ".": "target",
                       "$": "box", "*": "box on target",
                       "@": "you", "+": "you on a target"},
            "dirs": ["U", "D", "L", "R"],
            "moves_per_turn": 20, "step_budget": 200},
  "board": ["##########",
            "#        #",
            "#  #  #  #",
            "#  .$    #",
            "#   @ $. #",
            "# #  #   #",
            "#  .$    #",
            "#     $. #",
            "#   #    #",
            "##########"],
  "player": {"x": 4, "y": 4},
  "boxes":   [{"i": 0, "x": 4, "y": 3, "on_target": false},
              {"i": 1, "x": 6, "y": 4, "on_target": false},
              {"i": 2, "x": 4, "y": 6, "on_target": false},
              {"i": 3, "x": 6, "y": 7, "on_target": false}],
  "targets": [{"x": 3, "y": 3, "filled": false},
              {"x": 7, "y": 4, "filled": false},
              {"x": 3, "y": 6, "filled": false},
              {"x": 7, "y": 7, "filled": false}],
  "dead_squares": [[1,1],[8,1],[1,8],[8,8],[7,1],[1,7]],
  "pushes_available": [{"box": 0, "dir": "U", "to": [4, 2]},
                       {"box": 1, "dir": "R", "to": [7, 4]},
                       {"box": 2, "dir": "D", "to": [4, 7]},
                       {"box": 3, "dir": "R", "to": [7, 7]}],
  "last_turn": {"executed": "RRUULLLDD", "pushes": 2, "blocked": 3,
                "truncated": false, "dropped": 0, "unreachable": 1},
  "levels_solved": 1,
  "solved_weight": 1,
  "history": [{"tier": "unfiltered", "outcome": "solved"},
              {"tier": "unfiltered", "outcome": "deadlocked"}],
  "notes": "box 1 -> (7,4) and box 3 -> (7,7) are one push each. do the LEFT pair first: pushing box 0 left needs the corridor at row 3 clear."
}
```

Reading it: the board and the structured lists say the same thing twice, and they must always agree —
`tests/test_sokoban_obs.nim` re-parses `board` and asserts it reconstructs `player`, `boxes` and
`targets` exactly. `dead_squares` in this example is abridged for readability; the shipped value is
whatever the fixpoint flood computes, always. `pushes_available` is abridged the same way. Field
shapes never change: `board` is always **10 strings of 10 characters**, `boxes` and `targets` always
have exactly 4 entries, `dirs` is always `["U","D","L","R"]`.

### Reply schema and per-field caps

```json
{"actions": [{"do": "push", "box": 1, "dir": "R", "times": 1},
             {"do": "push", "box": 3, "dir": "R", "times": 1},
             {"do": "goto", "x": 5, "y": 3},
             {"do": "moves", "seq": "LLU"}],
 "say": "parking the two right-hand boxes first, then coming back for the pair on the left",
 "notes": "order: box1, box3, box2, box0. never push box0 down - (4,7) is not a target and row 7 has none."}
```

| Field | Type | Cap / domain |
|---|---|---|
| `actions` | array | **≤ 8 entries** (`maxActionsPerTurn`). Entries past the cap are dropped and counted in `actionsDropped`. Absent or empty = the turn is twenty `wait` ticks, and the reply is still **usable** |
| `actions[].do` | string | **≤ 6 runes**; enum `moves` \| `push` \| `goto` \| `wait`, lower-cased before matching |
| `actions[].seq` | string | required iff `do == "moves"`; **≤ 20 runes**; characters from `UDLRudlr` only (case-insensitive; lower case means the same move — the LURD convention's push/non-push distinction is *derived*, never *asserted*). Any other character **drops the entry** |
| `actions[].box` | integer | required iff `do == "push"`; **0 … 3**, indexing the turn-start `boxes` order; out of range **drops the entry** and counts in `repliesRepaired` |
| `actions[].dir` | string | required iff `do == "push"`; **≤ 5 runes**; matched case-insensitively against `U`,`D`,`L`,`R`,`up`,`down`,`left`,`right`; anything else drops the entry |
| `actions[].times` | integer | optional for `push`; **clamped to 1 … 8**; absent = 1 |
| `actions[].x`, `.y` | integer | required iff `do == "goto"`; **clamped to 0 … 9**; a non-integer or absent value drops the entry |
| `say` | string | **≤ 140 runes** (`MaxSayRunes`) — the cog thinking out loud; drawn in the spectator feed and in the replay, never fed back to the seat |
| `notes` | string | **≤ 320 runes** (`MaxNoteRunes`) — private scratchpad, echoed to this seat only next turn. Sized for a four-box push order plus the forbidden pushes |
| whole reply | bytes | **≤ 4096** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

`MaxSayRunes` and `MaxNoteRunes` are **re-pinned in this fork**: the starter has
`MaxSayRunes = ShoutMaxChars = 10` and `MaxNoteRunes = 160` (`src/ctf/sim_types.nim:747, 794-795`),
a 10-character in-world shout and a short note. A cog narrating a puzzle needs a sentence and a cog
carrying a push order between turns needs more than 160 runes, so `MaxSayRunes = 140` and
`MaxNoteRunes = 320` here, and `ShoutMaxChars` is deleted with the shout mechanic (§Sim module →
Deleted).

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded
error text — is truncated on RUNE boundaries** via the starter's `truncateRunes` / `runeSubStr`
(`src/ctf/directives.nim:61-68`), never by byte index. Byte truncation is what makes a replay that
renders in a browser fail a strict UTF-8 parser; `tests/test_sokoban_replay.nim` asserts it with
4-byte emoji sitting exactly on every cap.

Unknown top-level and per-action keys are ignored. A reply with a valid `say` but no `actions` is
**usable** (the turn is spent waiting and the narration is delivered). A reply that is not a JSON
object is a parse failure. **Invalid actions are dropped, never rewritten**: in a game where one
wrong push is fatal, repairing a malformed push into a different push would let the *game* lose the
level on the policy's behalf. The entry is removed, counted, and reported back as `dropped`.

### System prompt (fixed, identical for both champions)

```
You are one cog alone in a 10x10 Sokoban room. Four crates, four marked
squares. Push every crate onto a marked square.

THE ONE RULE THAT MATTERS
You can only PUSH. You walk into a crate and it slides one square away from
you. You can NEVER pull, never undo, never restart. A crate shoved into a
corner is lost forever, and the level ends the instant the position becomes
unwinnable. Think first. A push you cannot take back is worth ten seconds of
checking.

WHAT YOU GET EACH TURN
- "board": ten rows of ten characters, the WHOLE room, no fog.
    #  wall        (space) floor      .  marked square
    $  crate       *  crate already on a marked square
    @  you         +  you standing on a marked square
  x is the column 0-9 counting left to right, y is the row 0-9 counting top
  to bottom. board[y][x]. Row 0 is the top wall.
- "boxes": the four crates with their index, x and y. Index order is top row
  first, then left to right. It is RECOMPUTED EVERY TURN.
- "targets": the four marked squares.
- "dead_squares": squares from which NO crate can ever reach ANY marked
  square. Push a crate onto one of these and the level is over. This list is
  free; it is the easy half. The hard half is crates that block each other.
- "pushes_available": every push that is legal RIGHT NOW, with the square the
  crate would land on. Cross-check every one against dead_squares yourself.
- "opt_pushes": this level IS solvable in that many pushes. If your plan needs
  three times that, your plan is wrong.

WHAT YOU SEND
One JSON object with up to 8 actions. They run in order, one move per tick,
and everything past 20 moves in a turn is CUT OFF - re-issue it next turn.
  {"do":"push","box":1,"dir":"R","times":2}
        walk to the square you have to stand on and push crate 1 right twice.
        THIS IS YOUR MAIN ACTION. dir is U, D, L or R.
  {"do":"goto","x":5,"y":3}    walk to that floor square (crates block you)
  {"do":"moves","seq":"UULDR"} raw moves, up to 20, from U D L R
  {"do":"wait"}                waste a move

WHAT KILLS A LEVEL
1. A crate on a dead square.
2. Four cells in a 2x2 block that are all wall-or-crate, with any crate in it
   not yet on a marked square. Two crates side by side against a wall is the
   classic one.
3. No legal push left anywhere.
Any of those and the level ends immediately, scored on how many crates you had
parked.

HOW YOU ARE SCORED
Levels solved, weighted by tier: unfiltered 1, medium 2, hard 3. Crates parked
on marked squares is the tie-break, and finishing in fewer moves is the
tie-break after that. Time spent thinking costs nothing. A dead level costs
everything.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the
character { and end with }. No prose, no markdown, no code fences.
{"actions":[{"do":"push","box":1,"dir":"R","times":2}],"say":"<=140 chars","notes":"<=320 chars"}
```

### Champion #1 — `sokoban-lookahead` (owner **daveey**), `PLAYER_PROMPT`

```
Simulate before you commit. Never push a crate you have not first checked
three ways.
Before your FIRST action on a level, spend the whole turn planning and send
zero or one action. Write in "notes", in this order:
1. the four crates and, for each, which marked square you intend it for -
   match them so no two paths cross;
2. the crates that are ALREADY safe (on a marked square, or in a corridor
   where only one push direction exists);
3. the crates that are one bad push from death - name the exact forbidden
   push, e.g. "box0 D is dead: (4,7) is not a target and row 7 has none".
Then, every turn, for each push you are about to send, check all three:
  a. is the landing square in dead_squares? If yes, never.
  b. after this push, would the crate sit in a 2x2 block of wall-or-crate?
     Walk the four 2x2 blocks that contain the landing square. If yes, never.
  c. after this push, can you still walk round to the OTHER sides of this
     crate you will need later? If the push seals you out, do it last, not
     first.
Push the crates that can only be finished from one side FIRST, and the crates
you can approach from anywhere LAST. That ordering is what Sokoban is.
Prefer "push" over "moves": "push" walks you to the right square for free and
never wastes moves on pathfinding you got wrong. Use "moves" only for a
one-square adjustment.
If "last_turn" says blocked > 0 you pushed into something solid - re-read
"pushes_available" and stop guessing. If it says unreachable, the square you
must stand on is walled off or crate-blocked; clear a path first.
If opt_pushes is 17 and you have made 30 pushes, you are lost - stop pushing
and park whatever crates you can still reach on marked squares, because
crates parked is the tie-break.
```

### Champion #2 — `sokoban-orderfirst` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Solve the ORDER, then execute it without improvising.
Turn 1 of every level: pick a permutation of the four crates and an assignment
of crates to marked squares, and say it out loud in "say" - "3 to (7,7), 1 to
(7,4), then 2 and 0 on the left". Put the full order in "notes" and DO NOT
change it unless a push you planned turns out illegal.
Choose the order by these rules, in priority order:
1. A crate already on a marked square is finished. Never touch it again, and
   never route yourself through the square behind it.
2. Crates whose target is against a wall or in a corner go FIRST, while the
   room is still empty - you will not be able to get behind them later.
3. Crates nearest to you, and crates you can push in a straight line with no
   turns, go next: they are cheap and they open the floor.
4. The crate in the middle of the room goes LAST. It has the most push
   directions available, so it is the one that survives the room filling up.
Execute one crate per turn where you can: a single {"do":"push","box":i,
"dir":d,"times":n} with the largest n that is still safe, then stop. Twenty
moves a turn is plenty for one crate and it keeps every turn checkable.
Two hard bans, no exceptions: never push a crate onto a dead_square, and never
create a 2x2 of wall-or-crate containing an unparked crate. If your planned
push would do either, the ORDER was wrong - re-plan the whole order this turn
and say so.
When only one crate is left, count: moves_left must exceed the walking
distance plus the pushes. If it does not, you are out of time; spend the rest
parking nothing and simply stop pushing, because a deadlock and a timeout
score the same but a wrong push can undo a crate you already parked.
```

### The driver (deterministic, shared by every policy)

`src/sokoban/driver.nim` — the starter's `src/ctf/control.nim` (directive → per-tick actuation),
retargeted from pixel steering to a **primitive queue**. It is the **only** producer of primitives
and it contains no randomness. **Every macro is expanded against the turn-start snapshot; execution
is always the literal primitive sequence, and a primitive that turns out to be blocked at execution
time is a no-op that still costs a move.** That is what keeps expansion and replay identical.

| Action | Expands to |
|---|---|
| `moves seq` | the literal `seq`, one primitive per character, upper-cased |
| `goto x y` | the turn primitives of the walk BFS below; **zero** primitives if `(x, y)` is not free floor or is not reachable (`unreachable`) |
| `push box dir times` | the walk BFS to the **approach square** `c − dir` (where `c` is the box's turn-start cell), then `times` primitives in `dir`; **zero** primitives if `c − dir` is not free floor, is not reachable, or if `c + dir` is not free floor (`unreachable`) |
| `wait` | itself, one primitive |

**The walk BFS**, run against the turn-start board:

- Nodes are floor cells; a cell is traversable iff it is floor and holds no box. Targets are
  traversable. Edges are 4-adjacency in the fixed order **U, D, L, R**.
- Breadth-first from the player's cell; ties broken by that neighbour order, so the path is unique
  for a given board.
- The path is rendered into one primitive per step.
- Bounded by `macroPrimitiveCap = 32` primitives per macro; the whole turn's queue is then truncated
  to `turnMoves = 20`.

The driver never invents a move the schema does not express, and it never converts an illegal macro
into a different legal one.

### Scripted baselines (both shipped as league fillers; `pusher` is also the server-side fallback)

`src/sokoban/baselines.nim`, the starter's module retargeted. Both emit the **same** reply objects an
LLM does, through the same validator, which is what makes the bounded-orders test meaningful. Neither
ever emits `say` or `notes` — a baseline that narrated would make the feed lie about which seats are
LLMs.

**`pusher`** — `PLAYER_SCRIPTED=pusher`, and the server-side fallback. **A bounded best-first search
over push space**, and the "search" half of the idea's "reasoning-model vs search ladder":

1. State = (the four box cells sorted ascending by `(y, x)`, the **normalised** player cell = the
   lowest-index cell of the player's 4-connected reachable region given those boxes). Encoded as one
   `uint64` (five cell bytes), stored in a hash set.
2. Successors = the legal pushes of §The game → Deadlock detection test 3, generated in ascending
   box index then `U, D, L, R`.
3. Any successor that `isDeadlocked` flags is **pruned** and never expanded.
4. `h(state)` = the sum, over boxes, of the Manhattan distance from the box to its assigned target,
   under a greedy matching that repeatedly takes the globally smallest (box, unmatched target)
   distance, ties broken by ascending box index then ascending target index. `g` = pushes so far,
   `f = g + h`.
5. Best-first on `(f, h, insertion index)` — a total order, so the search is deterministic.
   `baselineNodeCap = 20_000` expansions; the search also stops the moment `h == 0` (solved).
6. If a solution was found, emit the **first ≤ 20 moves** of the primitive sequence that realises the
   solution's first pushes; the rest is re-issued on subsequent turns (the search is re-run from the
   new state each turn — it is cheap and it keeps the baseline stateless, so a fallback turn in the
   middle of an LLM episode behaves identically to a filler episode). If no solution was found, emit
   the first ≤ 20 moves toward the lowest-`h` state reached.
7. If not even one legal non-deadlocking push exists, emit the single push that minimises `h`
   regardless (the level is lost either way, and a `deadlock` beat is more honest and more watchable
   than twenty `wait`s).

`pusher` will clear most `unfiltered` levels, roughly a third of `medium` and few `hard` — measured
by `tests/test_sokoban_baselines.nim` over 100 seeds and pinned as a range, so a change that makes
the floor superhuman fails the build.

**`nudger`** — `PLAYER_SCRIPTED=nudger`. The one-ply control, and the answer to "did the champion
actually plan?": every turn, enumerate the legal pushes, drop the ones the deadlock detector flags,
and take the single push that most reduces `h` (ties: ascending box index, then `U, D, L, R`),
emitted as one `{"do":"push","box":i,"dir":d,"times":1}`. If every legal push is flagged, take the
one that minimises `h` anyway. It has no search, no ordering and no lookahead; it solves the trivial
end of `unfiltered` and deadlocks constantly, which is exactly the floor this benchmark needs.

Like the starter's `DefaultBaselineParams` (`src/ctf/baselines.nim:38`), the tunables
(`baselineNodeCap`, the `h` matching rule, and whether `f` ties break on `h` or on insertion) are a
parameter object chosen by `tools/tune_baselines.nim`'s sweep, not guessed;
`tools/ci/baseline_tuning.json` records the sweep's pick and `tests/test_sokoban_tuning.nim` asserts
the shipped defaults still equal it.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/sokoban/`. The fork is a rename sweep
(`ctf` → `sokoban`, `CTF_WIRE` → `SOKOBAN_WIRE`; a CI grep asserts no `ctf_` / `CTF_` identifier
survives outside comment history) plus the changes below. **The same modules compile twice**:
natively into `/bin/sokoban` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language and the whole reason vendoring gym-sokoban is not an option here.

### Level sourcing — decided, and reproducible from this repo alone

**No dataset is downloaded, ever, at build time or at runtime.** Boxoban's 1.5 M levels are a
1 GB-ish text corpus in another repo, and a coworld that fetched it would be neither hermetic nor
"held out" (a published corpus is exactly what a language model may have memorised). Instead
`src/sokoban/levelgen.nim` **generates every level by reverse play from the solved position**, which
is gym-sokoban's own generation method and which yields, as a free by-product, the **exact** optimal
push count — the number the tiers are defined by.

`generateLevel(seed, levelIndex, tier)`, with `h(k) = mix64(seed, levelIndex, attempt, k)` (splitmix64
over the mixed words — a pure hash, never a consumed stream):

1. For `attempt = 0 ..< genAttemptCap` (**`genAttemptCap = 8`**):
2. Build the room: 10 × 10, the border ring wall, the 8 × 8 interior all floor. Draw
   `wallCells = 8 + (h(1) mod 5)` interior cells, cell `j` at
   `(1 + h(10+j) mod 8, 1 + h(100+j) mod 8)`, and set each to wall. Repeats simply re-set the same
   cell, so the realised wall count may be lower — deterministic, no retry loop.
3. **Reject the attempt** if the floor cells are not 4-connected, or if there are fewer than 44 of
   them.
4. Place the 4 targets: distinct floor cells drawn by rejection sampling on `h(200 + j)` over the
   floor list.
5. Compute the static dead-square set `D` by the fixpoint flood of §The game → Deadlock detection
   test 1.
6. **Backward BFS over push space.** The goal states are: boxes on the four targets, player anywhere
   on a free floor cell, normalised to the lowest-index cell of the player's reachable region — all
   distinct normalisations seeded at depth 0. The successor relation is the **pull**: for a box at
   `q` and a direction `d`, the pull is legal iff `q − d` and `q − 2d` are both free floor **and**
   `q − d` is in the player's reachable region; it yields the box at `q − d` and the player at
   `q − 2d`. Because a pull is exactly a push run backwards, BFS depth in this graph **is** the
   minimum number of pushes needed to solve the resulting position.
7. Draw `targetDepth = bandMin + (h(300) mod (bandMax − bandMin + 1))` for the tier's band. Run the
   BFS until depth `targetDepth` is completed, or the queue empties, or **`genNodeCap = 200_000`**
   states have been dequeued. Record `reachedDepth` = the deepest completed depth.
8. If `targetDepth` was reached: collect the states first discovered at exactly that depth, in BFS
   discovery order, and pick index `h(400) mod count`. `optPushes = targetDepth`, **exactly**.
   Otherwise remember this attempt's `(reachedDepth, best state at reachedDepth)` and go to the next
   attempt.
9. **Reject** the chosen state if more than one box starts on a target (a level that starts a quarter
   solved is not a puzzle). A box can never start on a dead square: every BFS state is reachable from
   the goal, so every box in it can reach a target by construction — an invariant asserted by a test,
   not assumed.
10. Player start = the cell of the chosen state's player region at index `h(500) mod regionSize`, in
    ascending cell index.
11. If all `genAttemptCap` attempts failed to hit the band, take the attempt whose `reachedDepth` is
    closest to `bandMin`, use its best state, set `optPushes = reachedDepth` and
    `levelTierRelaxed[i] = true` in `results` (the level is still solvable and still played; the tier
    weight is still the declared one, because the ladder's shape must not depend on the seed).
12. If **no** attempt produced a state at depth ≥ 4 — which requires a degenerate room and has never
    been observed over the 5 000-seed sweep in `tests/test_sokoban_levelgen.nim` — the generator
    falls back to the tier's committed hand-authored level, `data/levels/fallback_<tier>.xsb`, three
    small files that ship in the repo and are also the fixtures the unit tests use. `results` records
    `levelTierRelaxed[i] = true`.

**Every level is therefore a pure function of `(seed, levelIndex, tier)`**, needs no network, and is
reproducible from a clone of this repo plus the seed. **Held out**: the seed is randomised by the
runner, never disclosed to the seat, and spans 2⁶⁴; the only fixed levels in the repo are the three
degenerate-case fallbacks. `docs/LEVELS.md` documents the generator, prints the three fallbacks, and
states plainly that no Boxoban level is used and no Boxoban number is comparable.

**Cost, bounded.** Generation is lazy (level `k` is built when level `k` starts) and the BFS stops as
soon as `targetDepth ≤ 34` is completed, so the realised cost is a few tens of milliseconds per level;
`genNodeCap × genAttemptCap = 1.6 M` dequeues is the hard ceiling per level, ≈ 1 s in a release
build, and §Decisions' arithmetic budgets 6 s for all six.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/sokoban/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop at `server.nim:1407-1417`, and the `Ping → Pong` branch in `websocketHandler` (lost twice in this fleet — lux-ai 0.1.0, snake-royale 0.1.0 — and guarded by nothing else) |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/sokoban/` | **fork** (magic + game name only: `CtfReplayMagic = "COWLDCTF"` (`replays.nim:142`) → **`SokobanReplayMagic = "COWLDSOK"`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/sokoban/` (`control.nim` → `driver.nim`) | **fork**, retargeted not rewritten | the per-turn batch (`decide.nim:427`), the two deadlines, `turnSpacingMs` (`decide.nim:386-389`), the budget guard (`decide.nim:328-346`), tolerant parsing (`directives.nim:102`), the rune caps, the fallback ladder and its two log phrasings (`decide.nim:463`, `:491`) |
| `src/ctf/sim_state.nim` → `src/sokoban/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/sokoban/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames` (`roster.nim:64-65`), the results JSON builder (`squadResultsJson`, `roster.nim:650`) |
| `src/ctf/events.nim` → `src/sokoban/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/sokoban/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/sokoban/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/sokoban/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps = 24` (`:376`), the flatty wire types (field order sacred), and the re-pinned `MaxSayRunes = 140`, `MaxNoteRunes = 320`, `MaxPromptRunes = 4000` |
| `src/ctf/sim_config.nim` → `src/sokoban/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, and the validators at `:688-713` (whole-second `attempt1Ms`/`retryMs`, `attempt1Ms + retryMs ≤ turnBudgetMs`, positive `wallClockBudgetSeconds`) — all kept, and §Decisions' numbers satisfy them |
| `src/ctf.nim` → `src/sokoban.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/sokoban_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** (40 022 bytes, sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`) | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/sokoban_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling, and its `docker cp` source path changes from `/workspace/ctf/replay-viewer/dist/.` to `/workspace/sokoban/replay-viewer/dist/.` |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_red.png`, `data/soldier_red_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*.webp}` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling, vision cones, **fog-of-war raycasting
and the entire first-person raycast pipeline** (this game is perfect information — there is nothing
to occlude), spray cans, floor paint and the paint grid, the paint buff, King of the Hill and
`hillTicks`, the `resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the
barrage, med kits, shields, cardboard barriers, trenches, perks, handicaps, lives and respawns,
**teams and four-team free-for-all** (there is one seat), **shouts-as-cog-speech and
`ShoutMaxChars`**, achievements, campaign mode, `maxGames > 1` side-swapping, and **all of the
pixel-space map machinery**: `arena.nim`'s wall masks and pixel queries, `map_art.nim`,
`mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`, `tools/map_editor*.nim`,
`tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `docs/pool-review.html`, `docs/MAPKIT.md`. The
board here is a fixed 10 × 10 integer cell grid built by `levelgen.nim`; every one of those is a
config surface the puzzle rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `*_front_gun`,
`soldier_{blue,green,yellow}*`, `rig_real/`) and the blue/green/yellow locker-room webps — there is
one cog and it is red.

### New modules

- `src/sokoban/grid.nim` — the cell type, the XSB glyph table (parse and render, both total and
  round-tripping), the 10 × 10 board type, the direction enum in `U, D, L, R` order, 4-adjacency, the
  player-reachability flood, the legal-push enumerator, and the walk BFS used by `goto`, `push` and
  `pusher`. Pure integer; no pixie, no pixel queries.
- `src/sokoban/deadlock.nim` — the static dead-square fixpoint flood, the 2 × 2 frozen-block test,
  the no-push test, and `isDeadlocked` as their ordered disjunction, returning the `kind` and the
  offending cell.
- `src/sokoban/levelgen.nim` — the reverse-play generator of §Level sourcing, the tier bands and
  weights, the state encoding and the backward BFS, and the loader for the three committed fallback
  `.xsb` files.
- `src/sokoban/search.nim` — the bounded best-first push-space search and the greedy matching
  heuristic, shared by `pusher`, by `nudger`'s one-ply scoring, and by the tests. One
  implementation, three callers, so the fallback and the filler can never drift.
- `src/sokoban/sim.nim` — the step loop of §The game exactly as numbered, `gameHash`, level and
  episode end evaluation, scoring, and the seat's observation builder. Imports and re-exports the sim
  modules, as the starter's does, so `import sokoban/sim` sees everything.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cell coordinates, directions, tick counters, BFS distances,
heuristics, scores. There is no floating point anywhere in `sim.nim`, `grid.nim`, `deadlock.nim`,
`levelgen.nim`, `search.nim`, `driver.nim` or `baselines.nim`, and a test greps for it. That makes
the native ↔ wasm hash chain exact by construction.

**One seeded source, and it is a hash, not a stream.** Every generated quantity — wall cells, target
cells, `targetDepth`, the state choice at that depth, the player cell — is a read of
`mix64(seed, levelIndex, attempt, salt)`, evaluated independently. Nothing the policy does can shift
a draw, reorder draws, or consume one out from under a later level: **level `k`'s grid is identical
no matter what happened in level `k − 1`**, which is what makes per-tier solve rates comparable
across policies. `tests/test_sokoban_levelgen.nim` asserts it by generating every level of every
variant under three different policy behaviours and comparing the boards character for character.

There is no other random draw. The seed is randomised in `src/sokoban.nim` before `config.update`
(the starter's rule), recorded in the replay config and in `results.seed`. Two episodes with the same
seed and the same plans are byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDSOK`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, variant, `num_agents`, every rule constant, the tier ladder,
   `players[].name`, `slots[]`, `fastMode`), then the record stream — the join record, **one
   `level` record per level carrying its ten XSB rows, its tier, its `optPushes`, its dead-square
   list and its `tierRelaxed` flag**, **per-turn plan records** (the only inputs this game has), chat
   records (`register` / `directive` / `fallback` / `budget_guard` / `stop` / `result`) and **one
   `gameHash` per tick**.
2. **The level grids are recorded, not regenerated.** This is a deliberate divergence from
   cogame-minigrid, which re-runs its generators in wasm: here the generator is a bounded BFS costing
   up to a second per level, and paying that on viewer load would delay the first drawn frame for no
   benefit. Six levels × (10 rows + ~40 dead-square pairs) ≈ 1.5 KB. The viewer therefore re-derives
   every frame by re-stepping the sim from the recorded boards and the recorded plans, with no
   generator call and no fetch.
3. `tools/build_replay_viewer.sh` builds `replay-viewer/sokoban_replay.nim` — which imports the
   **same** `src/sokoban/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
4. In the browser, `sokoban_load_replay` runs `parseReplayBytes` + `initReplayRuntime`;
   `sokoban_frame` re-steps the sim from the recorded plans and compares `sim.gameHash()` against the
   recorded hash **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it
   happens and surfaced as `mismatchTick` in `#mmwarn`.
5. **`gameHash` mixes**, in this fixed order: `levelIndex`, `levelMove`; the player's `(x, y)`; then
   every cell of the 10 × 10 grid in ascending `(y, x)` as `(isWall, isTarget, hasBox)`; then
   `boxesOnTargets`, `levelBoxesPlaced`, `pushes`, `blockedMoves`; then the six `levelOutcome` codes
   and six `levelBoxesPlaced` values; then `tick`.
6. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact
   cannot be re-derived from sim state, so the stop is written as one record applied by the *same
   proc* on record and on playback, and `tests/test_sokoban_replay.nim` runs the record → re-derive
   check for **every** end reason (`ladderComplete`, `turnCap`, `wallClock`, `fault`), not just the
   healthy one (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 1200 hashes + 6 level records + ≤ 60 plan records + ~80 chat records ≈ **22 KB**.

### Documented divergences (mirrored into `docs/LEVELS.md`)

1. **No gym-sokoban dependency, no Boxoban levels, and no bit-exactness with either.** Decided as a
   scoping rail: gym-sokoban is a Python gym package and Boxoban is a downloaded corpus; embedding
   either means a simulator that cannot compile to wasm, so the static replay viewer — a
   non-optional pin — would be impossible, and a public corpus is the opposite of "held out". No
   upstream code is vendored, no upstream numbers are claimed as reproduced, and no score from this
   coworld is comparable to a published Boxoban number. What is reproduced is the *problem*: 10 × 10,
   four boxes, push-only, tiered by difficulty.
2. **Tiers are defined by exact optimal push count, not by Boxoban's filtering procedure.** Boxoban's
   `unfiltered`/`medium`/`hard` split came from which levels a trained agent could solve. That is not
   reproducible here, so the tiers are `optPushes` bands (§The game), which is a stable, checkable,
   seed-independent definition and is *shown* to the policy.
3. **The level ends the instant a deadlock is detected**, rather than letting the agent flail until
   the step cap. The detector is sound, so this never truncates a winnable position; it is what makes
   the idea's "one wrong push and the level is dead" literally true, it saves budget, and it is what
   the `deadlock` scrubber beat marks.
4. **Moves are batched under a driver, not stepped one per call.** The idea's "one move per tick"
   interface is preserved as the primitive set and the tick; what changed is *who calls it*. Up to
   twenty primitives per LLM turn under a deterministic driver, plus two macros (`push`, `goto`) that
   expand to primitives. One LLM call per move would be up to 1 200 calls in a 720 s budget —
   impossible — and a policy that cannot express "push box 1 right" spends every turn walking.
5. **`dead_squares` and `pushes_available` are given to the policy.** Both are pure functions of the
   board a policy could compute itself; handing them over moves the measurement onto push ordering
   and freeze deadlocks. Deliberate, and recorded here so a reviewer does not read it as a leak.
6. **Reward shape.** gym-sokoban's reward is a small per-step penalty plus a bonus per box on a
   target plus a large completion bonus. The league needs one rankable integer, so §The game makes
   tier-weighted solves the dominant term, boxes parked the second and moves saved the third. All
   three underlying quantities are in `results`, so a solve-rate-per-tier is directly readable.
7. **No undo, no restart, no pull-mode.** gym-sokoban ships `push`/`pull` variants; only push exists
   here, because irreversibility is the entire point.
8. **`maxGames = 1`** — the starter's multi-game episode is not used; a ladder has no side to swap.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with a variable turn length (the tick loop breaks early
   when a level finishes) and one seat in the batch.
2. **Registration interception** — the seat's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed
   as registration, **not** applied as a shout and **not** written to the replay chat stream; the
   server writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim, and the server **logs loudly and refuses to start the game** when the joined seat has no
   register record (the grf-football 2026-08-27 silent-default scar). Any other chat text from the
   seat is dropped — the cog speaks through `say`.
3. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration (`server.nim:1407-1417`), kept, forcing `phase = GameOver`, `reason = deadline`,
   `endRule = wallClock`, and written as the load-bearing stop record of §Determinism point 6.

### The two named edits to `roster.nim`

1. **Alias.** `seatAlias(slot)` returns `IdentityNames[slot]` title-cased → **`Alpha`** for the only
   seat. The `IdentityNames` array itself (`roster.nim:64-65`) is unchanged. Board labels and the
   label manifest inherit the two-name-space rule with no further change, and `showPlayerLabels` is
   false.
2. **`squadResultsJson` → `ladderResultsJson`** (`roster.nim:650`) — one entry per seat, one entry in
   every seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a 10 × 10 cell grid, not a pixel arena.** `buildSpriteProtocolPlayerUpdates` emits
   cell-space coordinates; the raycast fov cache and shadowcasting are **deleted outright** (perfect
   information — there is no fog layer at all).
2. **Box and target pools.** New pools `BoxBase` (sized to 4) and `TargetBase` (sized to 4), filled
   in ascending `(y, x)` and emitted incrementally like the starter's other object families, plus a
   per-level static `DeadSquareMask` sent once at `levelstart`.
3. **Baked room bed.** `arena_floor.png` is tiled and darkened at install with pixie, exactly the way
   the starter bakes endzone paint, and the floor grain, the cell gridlines and the wall bevels are
   baked onto it once per level (§Viewer → Art) — one bake per level, so the per-frame cost is the
   cog, four boxes, four targets and the overlays.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST` / `PORT`; the player
socket at `/player?slot=0&token=<t>`. Protocol name **`sokoban/v1`**.

The certifier's browser probes are served for real and registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering
for the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). The
player websocket handler **closes unless the token matches the seat** (the certifier probes with a
bad token — cogame-flatland 0.1.1), and `websocketHandler` keeps the starter's
`Ping → socket.send(message.data, Pong)` branch with **no** additional `kind` guard (a
`kind != TextMessage` guard drops the player's binary registration frames — lux-ai 0.1.0,
snake-royale 0.1.0). Global broadcasts are fire-and-forget so a slow viewer can never stall the
episode.

### Results document (closed schema; `ladderResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":              ["daveey"],
  "aliases":            ["Alpha"],
  "scores":             [7210382],
  "win":                [true],
  "winner":             0,
  "reason":             "complete",
  "endRule":            "ladderComplete",
  "variant":            "ladder",
  "seed":               1734029581,
  "levelCount":         6,
  "stepBudget":         200,
  "parWeight":          5,
  "maxWeight":          12,
  "solvedWeight":       7,
  "levelsSolved":       4,
  "boxCredit":          21,
  "movesSavedTotal":    382,
  "levelTier":          ["unfiltered","unfiltered","medium","medium","hard","hard"],
  "levelOptPushes":     [9, 11, 17, 20, 26, 24],
  "levelOutcome":       ["solved","solved","solved","deadlocked","outofsteps","solved"],
  "levelBoxesPlaced":   [4, 4, 4, 2, 3, 4],
  "levelMoves":         [58, 71, 126, 44, 200, 163],
  "levelTurns":         [3, 4, 7, 3, 10, 9],
  "levelPushes":        [12, 14, 21, 9, 38, 31],
  "levelTierRelaxed":   [false,false,false,false,false,false],
  "deadlocks":          1,
  "outOfSteps":         1,
  "pushesTotal":        125,
  "blockedMoves":       47,
  "actionsDropped":     3,
  "macrosUnreachable":  5,
  "repliesRepaired":    1,
  "finalTick":          662,
  "turnsPlayed":        36,
  "policyKinds":        ["llm"],
  "llmTurns":           35,
  "fallbackTurns":      1,
  "deadSeats":          [false],
  "stopDetail":         ""
}
```

Six identities hold in every results document and are asserted by `tests/test_sokoban_engine.nim`:

1. `Σ levelMoves == finalTick` — `58+71+126+44+200+163 = 662` ✓
2. `Σ levelTurns == turnsPlayed` — `3+4+7+3+10+9 = 36` ✓
3. `levelOutcome[i] == "solved"` ⇔ `levelBoxesPlaced[i] == 4` ✓
4. `solvedWeight == Σ weight(levelTier[i])` over solved `i` — `1+1+2+3 = 7` ✓
5. `boxCredit == Σ levelBoxesPlaced` — `4+4+4+2+3+4 = 21` ✓, and
   `movesSavedTotal == Σ (200 − levelMoves[i])` over solved `i` —
   `142+129+74+37 = 382` ✓
6. `scores[0] == 1_000_000×solvedWeight + 10_000×boxCredit + movesSavedTotal` —
   `7_000_000 + 210_000 + 382 = 7_210_382` ✓, and `win[0] == (solvedWeight >= parWeight)` —
   `7 ≥ 5` ✓, `winner == 0`.

`levelOutcome` is the closed enum `solved | deadlocked | outofsteps | unreached`; `levelTier` is
`unfiltered | medium | hard`. Adding a key means updating `ladderResultsJson`, the manifest's
`results_schema` and `tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld
schemas are closed and undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDSOK`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (template line 31 / 319).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"sokoban/v1","gameVersion":"1","seed":…,"variant":"…","names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"levels":[…],"plans":[…],"says":[…],"fallbacks":N,"results":{…}}` —
  by brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md`
  documents for prod forensics) and decoding the level and chat records.
- **The phase-60 substitute for `docs/SPEC.md` §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.endRule, .results.solvedWeight' /tmp/ep.json
  jq -r '[.plans[]|select(.source=="llm")]|length, .fallbacks, (.says|length)' /tmp/ep.json
  ```
  Require `protocol == "sokoban/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.levelsSolved >= 1`, and the champion seat's plans with `source == "llm"`,
  real actions (including at least one `push`) and non-empty `say` lines — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDSOK`, format version, `gameName` `sokoban`, `gameVersion` `1` |
| config JSON | `seed`, `variant`, `num_agents`, `gridSize`, `boxCount`, `levelCount`, `tierLadder`, `tierWeights`, `tierBands`, `turnMoves`, `levelTurnCap`, `stepBudget`, `maxTurns`, `maxTicks`, `parWeight`, `maxActionsPerTurn`, `macroPrimitiveCap`, `genNodeCap`, `genAttemptCap`, `baselineNodeCap`, `players[].name` (real name), `slots[]`, `fastMode` |
| join | the seat's `name` (real policy name), `slot`, `token` |
| levels | per level: ten XSB rows, `tier`, `optPushes`, the dead-square list, `tierRelaxed` |
| plans | per turn: the accepted action list — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields;
they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `level`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `actions` (the accepted array), `executed` (the LURD string that ran), `pushes`, `blocked`, `truncated`, `dropped`, `unreachable`, `say` (≤ 140 runes), `view` (the observation minus `notes`) |
| `fallback` | `turn`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of eleven kinds, plus `end`:**

`levelstart` `{i, tier, optPushes, boxes, targets}`; `turn` `{n, level, levelTurn}`;
`plan` `{n, moves, pushes, blocked, truncated, dropped, unreachable}`; `say` `{text}`;
`fallback` `{cause}`; `boxon` `{box, x, y, placed}`; `boxoff` `{box, x, y, placed}`;
`deadlock` `{kind, box, x, y}` with `kind ∈ {dead_square, frozen_block, no_push}`;
`solved` `{i, moves, pushes, turns}`; `failed` `{i, why}` with
`why ∈ {deadlocked, outofsteps}`; `budget` `{turn, remaining_s}`;
plus `end` `{reason, endRule, solved, of, weight, score}`.

`tests/test_sokoban_events.nim` asserts the emitted set equals exactly this list. **Nothing fires per
tick**: individual pushes and blocked moves are *summarised* on the once-per-turn `plan` event and
animated by the renderer from state deltas, so the feed never floods even when a policy sends twenty
moves a turn. `plan` fires ≤ 60 times an episode; `boxon`/`boxoff` are bounded by the pushes onto and
off targets.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`levelstart`,
`boxon`, `deadlock`, `solved`, `failed`, `fallback`, `end`.** `boxon` is beaten **only when it raises
that level's `placed` to a new maximum**, so a box shuffled on and off a target draws one marker, not
ten. `turn`, `plan`, `say`, `boxoff` and `budget` drive the feed, not the scrubber.
**`deadlock` is the idea's "deadlock created" marker** and it is a first-class beat kind with its own
CSS and its own label (`DEADLOCK CREATED — box 2 cornered at (7,1)`).

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `LevelStart, TurnStart, Directive, Fallback, Move, Push, BoxOn, BoxOff,
Deadlock, Solved, Failed` and the mandatory trailing summary row (`type`, `ticks`, `events`,
`gameVersion`) kept. `Move` is the per-tick row that makes this stream a full action trace for
`cogamer-rl` — up to 1 200 rows an episode, which the replay deliberately does not carry.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed
(`/workspace/ctf/replay-viewer/dist/.` → `/workspace/sokoban/replay-viewer/dist/.`) — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/sokoban_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
this repo's own starter. **None of the four comes from `cogame-babel`, `cogame-bullwhip`,
`cogame-parley`, `cogame-moba` or `cogame-factorio`, and none is written fresh. Never a mixture.**
Splicing one starter's shell onto another's emscripten link flags (`MODULARIZE` / `EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23). The set
is internally consistent and is kept as one piece: the Worker sets `Module.onRuntimeInitialized`
(`replay-viewer/static_replay_worker.js:188`), the module is emitted **non-modularized** as
`sokoban_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang` through `emcc`,
`--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable:
with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and corrupt the module's own globals — the
starter's own comment at `replay-viewer/config.nims:33-41`), `-s FILESYSTEM=1`,
`-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_sokoban_load_replay,_sokoban_frame,_sokoban_input,
_sokoban_packet_ptr,_sokoban_packet_len,_sokoban_mismatch_tick,_sokoban_error_ptr,
_sokoban_error_len,_sokoban_stage_ptr,_sokoban_stage_len`; and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './sokoban_replay.js')` in that order
(the starter's line 239, renamed only).

`sokoban_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress
buffer that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`,
and the `emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running
module destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `sokoban_load_replay` re-simulates the whole episode once headlessly
  (≤ 1 200 ticks over a 100-cell grid — sub-millisecond in wasm, and there is no generator to re-run
  because the boards are in the bytes), records the per-tick cumulative boxes-parked and solved
  weight, the level boundary ticks, the beat ticks and the lull spans, then resets and renders frame
  0. That is what lets the progress sparkline and the scrubber beats draw at **full width on the
  first frame** instead of growing in.
- `sokoban_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (`replay-viewer/static_replay.js:161`) —
posted by the Worker only *after* `ingestPacket()` (`static_replay_worker.js:64`) has handed
BroadcastCore the first frame and it has drawn, so the attribute means "a frame is on the canvas",
not "a file was fetched". **On failure it sets `data-replay-error`** on `<html>` with the message, in
`showFailure()` (`static_replay.js:8-20`). Both are coworld-ctf's own signals, inherited unchanged —
this fork adds neither and removes neither. The `coworld-replay` postMessage bridge's `ready` is
posted **from a callback fired after** `data-replay-loaded="true"` is set, never on rAF timing at the
call site (chorus `3c11c953`, 2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes; sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`). Not edited, not reformatted;
  `tests/test_sokoban_viewer.nim` pins that sha256 as a literal. Everything this game adds lives in
  the appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats` / `renderClock` /
  `renderTransport` / `ingestLullSpans` / `renderMomentum` remain; `ingestBeats` ignores kinds it does
  not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (`client/replay_broadcast.html:4276-4325`), transport, endcard, locker-room loader, `?embed=1` mode
  and `.tiny` density system are untouched, and the block is installed through the starter's own
  splice hook: `window.PaintballChrome` (context built at `:4330`, installed at `:4337`, declared at
  `:4651`) is renamed `window.SokobanChrome` and its `install(PB_CTX)` / `frame(s, ctx, jumped)`
  (`:2075`) / `event(e, s, ctx)` (`:3480-3481`) entry points are kept with the same signatures. The
  appended block replaces only the *contents* of the scorebug plate, adds the level ribbon, the six
  level pips and the dead-square inset, and retargets the feed rows, the beat rendering, the momentum
  series and the endcard columns. The block sits after the starter's banner comment at `:4344`, and a
  test asserts the starter's byte prefix is intact up to that marker and that the file only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text by
  `tests/test_sokoban_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  `pushFeed` **including its signature** (the cogball 0.1.4 latch scar: a signature drift threw
  mid-replay and latched `static_replay.js` into `failed`), `banner`, the beat and lull machinery, the
  endcard builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` →
  `window.SOKOBAN_WIRE` rename emitted by `tools/gen_wire_constants.nim`. Deleted: every ctf-specific
  draw call, the raycast FPV pipeline (the `#fpv` **canvas** is reused, the raycaster is not), and
  `attachMinimap`'s call site. Added: `drawRoomBed`, `drawWalls`, `drawTargets`, `drawBoxes`,
  `drawCog`, `drawDeadSquares`, `drawDeadlockFlash`, `drawLevelRibbon`, `drawLevelPips`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read` (`replay_broadcast.html:1510-1521`), and the page's
    `core.attachMinimap($('minimap-canvas'))` call (`:4200`). **Zoom decision: dropped entirely.** The
    board is a fixed 10 × 10 cell grid with no off-frame area; `relayout()` letterboxes it whole at
    every width (see "Legible at 360 px"), so per the pin a fixed arena drops `#viewpanel`.
    `broadcast_core.js` already tolerates never being attached: `minimapSurface` / `minimapCtx` stay
    null and `drawMinimap()` returns on its first guard.
  - **`#povBadge`** (`:1525`) and the `togglePov` wiring — with one seat there is nothing to select.
  - Inside the kept `#fpv`: **`#fpv-hp`** (`:1537`), **`#fpv-gear`** (`:1538`), **`#fpv-map`** and
    **`#fpv-map-canvas`** (`:1542-1543`) — the cog has no hit points and no gear, and the panel is
    repurposed wholesale (below).
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad` (`:2219-2244`), and the `.ec-heart` endcard glyphs
    (`:1221-1231`).
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture` (`:919-934`) and `.gamestart`,
    `.hillflip`, `.tagout`, `.gameover` (`:4431-4443`) CSS rules — those kinds are never emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS, `:245`).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with `#plates-l` / `#plates-r` /
    `#clock` / `#clock-time` / `#clock-caption` / `#ffwd-mini`, **`#fpv` with `#fpv-canvas`,
    `#fpv-hud`, `#fpv-name`, `#fpv-cap` and `#fpv-grip`** (repurposed as the **dead-square map**,
    caption `DEAD SQUARES`, `#fpv-name` reading `ALPHA · 2 OF 4 PARKED`, still draggable and
    resizable by the starter's own grip), `#bannerlane`, `#killfeed`, `#mmwarn`, **`#transport` in
    full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`, `#btn-loop`,
    `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`, `#tick-clock`, `#speedchips`), `#scrub`
    with `#momentum` / `#scrub-fill` / `#lulls` / `#scrub-win` / `#scrub-head`, `#endcard` with
    `#ec-headline` / `#ec-wincond` / `#ec-how` / `#ec-teams` / `#ec-replay`, and `#status`.
    **`#plates-r` is kept but rendered empty** — it is one of the scorebug's three flex columns and
    removing it would un-centre `#clock`; with one seat the single plate lives in `#plates-l`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here
and enforced by a test:

| Starter string (`client/replay_broadcast.html:line`) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (`:3795`) | `<span>Level</span><span>Tier</span><span>Result</span><span>Moves</span><span>Boxes</span>` |
| `<div class="ec-thead"><span>Cog</span><span>Tags</span><span>Out</span><span>Paint</span></div>` (`:3788`) | `<span>Cog</span><span>Solved</span><span>Pushes</span><span>Score</span>` |
| `<span class="fl-cap">Lives left</span>` (`:3793`) | `<span class="fl-cap">Levels solved</span>` |
| `<span class="fl-cap">Hill time</span>` (`:3786`) | `<span class="fl-cap">Pushes made</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (`:1576`) | `<span class="momentum-label">BOXES PARKED</span>` |
| `<span class="lives-label">Lives</span>` (`:2241`) | `<span class="solved-label">Solved</span>` |
| `<span class="lives-label pb-lbl">Hill</span>` (`:2224`) | `<span class="solved-label pb-lbl">Level</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (`:1480`, `:1833`, `:1842`) | "Sizing up the first level…" |
| `#clock-caption` "In the locker room" (`:1499`) | "Waiting for the cog" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (`:1524`) | "Replay hash mismatch at tick N — showing recorded moves" |
| `#fpv-cap` "EYES" (`:1545`) | "DEAD SQUARES" |
| `#btn-spoilers` title "Spoilers: kills / flag story / winner on the timeline ahead of the playhead (o)" (`:1564`) | "Spoilers: solved / deadlocked levels on the timeline ahead of the playhead (o)" |
| team words `RED` / `BLUE` in `.ec-tname` / plates (`:2222`, `:2239`, `:3783`, `:3790`, `:3836`) | the seat's **alias** (`ALPHA`) on the plate, and the **tier name** (`UNFILTERED` / `MEDIUM` / `HARD`) as the endcard section head |

**`tests/test_sokoban_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `EYES`, `spray`, `grenade`, `med kit`, `kill`, `team` — outside comment blocks, and
asserts **zero** matches; and asserts each replacement string above is present exactly once. A rename
that reintroduces paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (`client/replay_broadcast.html:4290-4317`). **No overlay sits in the transport
band**: the board is laid out between the two bands and every addition here (the level ribbon, the
level pips, the dead-square inset, the feed) is positioned inside the board region, in the letterbox
gutters beside it, or in the top band. The **endcard stops at `var(--band)`**
(`#endcard { bottom: var(--band, 0px) }`, `:1047`, the starter's rule, kept) so the scrubber stays
clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `skBeat(tick, kind, label)` — named with the `sk-` prefix so it can
never shadow `chrome_common.js`'s `markBeat` alias (`client/replay_broadcast.html:1635`; the tandem
2026-08-23 hoisting trap, and the same prefix discipline the starter's own `pbBeat` at `:4475` uses)
— appends `<button class="beat-marker <kind>" title="…" aria-label="…">` to `#scrub` and seeks on
click. CSS exists for **every kind emitted and no others**: `.beat-marker.levelstart`,
`.beat-marker.boxon`, `.beat-marker.deadlock`, `.beat-marker.solved`, `.beat-marker.failed`,
`.beat-marker.fallback`, `.beat-marker.end`. `.deadlock` is the tallest, reddest marker on the bar —
it is the moment the spectator came for. The game block never calls `markBeat`, so an unlabelled div
marker cannot appear.

**Playback rate: one tick per three animation frames at 30 fps = 10 ticks/second** (speed chips
`[0.5, 1, 2, 4, 8]`, default 1), with the cog's position and any pushed box interpolated across the
three frames so a push glides instead of snapping. A 1 200-tick episode plays for **120 s**, and even
a fast 400-tick episode plays for 40 s, which is what lets `viewer_smoke.mjs --soak 10` observe real
advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar).

### Readouts

1. **The board**, drawn edge to edge: the baked floor bed with gridlines; walls as bevelled masonry;
   **targets** as recessed amber diamonds inlaid in the floor; **boxes** as wooden crates, tinted
   green with a seated shadow when parked on a target; and the **cog** as the composited soldier rig
   at its four facings. This is the idea's "simple grid", and at 10 × 10 it is readable at a glance.
2. **The dead-square wash** — every cell of the level's static dead-square set is drawn under a faint
   red hatch on the main board. A spectator can therefore *see the trap before the cog walks into
   it*, which is what turns a planning benchmark into something worth watching.
3. **The deadlock flash** (the idea's ask) — on a `deadlock` event the offending box is ringed in red,
   the cell flashes twice, `#bannerlane` reads **`DEADLOCK CREATED — BOX CORNERED AT (7,1)`** for two
   seconds, and the scrubber gets its `.deadlock` beat.
4. **The dead-square inset** — the repurposed `#fpv` panel, bottom-right in the board's letterbox
   gutter: the same 10 × 10 grid stripped to walls, targets, dead squares and boxes, so the geometry
   of the trap is legible even when the main board is busy. Captioned `DEAD SQUARES`, with
   `ALPHA · 2 OF 4 PARKED` beneath. Draggable and resizable by the starter's own `#fpv-grip`.
5. **Level ribbon** — in the board's left gutter: `LEVEL 3/6 · MEDIUM · SOLVABLE IN 17 PUSHES`, with
   `MOVES 38/200` under it.
6. **Level pips** — six pips under the ribbon, one per level in ladder order, sized by tier (small =
   unfiltered, medium, large = hard): pending (hollow), current (amber ring), solved (green fill),
   deadlocked (red fill with a slash), out of steps (grey fill), unreached (grey outline). Each pip
   carries its tier name at full width and a tooltip at `.tiny`.
7. **Clock** — `#clock` shows the big numeral `SOLVED 3/6`; `#clock-time` shows
   `weight 4/12 · boxes 2/4`; `#clock-caption` shows `move 38/200 · push 12 · score 4180345`.
8. **Scorebug plate** — one plate in `#plates-l`: the seat's **real policy name** (spectator side
   only), its in-game alias `ALPHA`, the cog avatar from `data/soldier_red_front.png`, the running
   score as the numeral, four small **box chips** filled as boxes are parked, and a `↯` glyph if the
   seat has taken a fallback.
9. **Match feed** (`#killfeed`) — plain language, never internal notation: `LEVEL 3 OF 6 — MEDIUM,
   SOLVABLE IN 17 PUSHES`, `BOX 1 PARKED — 2 OF 4`, `BOX 0 PUSHED OFF ITS TARGET — 1 OF 4`,
   `TURN 23 — 4 ACTIONS, 6 PUSHES, 3 MOVES BLOCKED`, `PLAN CUT OFF — 27 MOVES ASKED, 20 RUN`,
   `DEADLOCK CREATED — BOX 2 CORNERED AT (7,1)`, `OUT OF STEPS — 200 MOVES USED, 3 OF 4 PARKED`,
   `LEVEL 3 SOLVED IN 126 MOVES / 21 PUSHES`, `Alpha: "parking the two right-hand boxes first"`, and
   `MISSED THE CALL — pusher plan (timeout)`. The `say` lines and the plan lines are where a
   spectator sees the LLM playing.
10. **Progress sparkline** — the starter's `#momentum` SVG retargeted to one cumulative series (boxes
    parked, 0 … 24) with **level spans shaded** in the pip colours behind it, level boundaries as
    vertical ticks, and the playhead marked. Filled from the load-time pre-scan, so it draws at full
    width on the first frame. A flat line inside a red span is the whole story of a dead level in one
    glance.
11. **Endcard** — `4 OF 6 SOLVED — WEIGHT 7 OF 12, PAR 5 MET`, a six-row table under the re-mapped
    header (`Level | Tier | Result | Moves | Boxes`), a summary line (`125 pushes, 47 blocked moves,
    1 deadlock, 1 out of steps, 1 fallback turn`), and `SCORE 7210382`. It stops at `var(--band)` and
    any seek dismisses it.
12. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
    40 consecutive ticks with no push, no `boxon`/`boxoff` and no level change, from the pre-scan),
    spoilers switch, tick readout, speed chips, the scrubber with its seven beat kinds, and `#mmwarn`
    on a hash mismatch — all the starter's, verbatim.

### Art

**Real art, from the starter's shipped assets plus install-time bakes — no placeholders, no
solid-colour squares, no downloads.** The floor is `data/arena_floor.png`, tiled and darkened 30 %,
with baked gridlines in the palette from `data/pallete.png` — one pixie bake per level, exactly the
way the starter bakes endzone paint. **Walls** are cut from `client/art/walls/wall_h.jpg` and
`wall_v.jpg` at cell size with a baked bevel, so a wall run reads as masonry rather than a black bar.
**Boxes** are baked once: a wooden crate with cross-bracing tinted from `wall_h.jpg`, in two states
(loose, and parked — parked gets a green rim light and a seated shadow) = **2 chips**. **Targets** are
a baked recessed amber diamond with the starter's endzone hatch, in two states (empty, filled) = **2
chips**. The **dead-square hatch** is a procedural 45° hatch in the palette's reds at 18 % alpha. The
**cog** is `data/soldier_red.png` composited by `rig_art.nim` into 4 facings × 2 sizes = **8 chips**;
`data/soldier_red_front.png` is its avatar on the scorebug plate. Every chrome numeral and label is
set in `data/font.ttf`. The level pips, the ribbon, the deadlock flash and the sparkline are
procedural in the bed bake's palette. The loading screen is the starter's locker room
(`client/art/lockerroom/bg.jpg` plus the four red webps) with the caption re-labelled.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (`client/replay_broadcast.html:4307-4312`). The board's aspect is **10/10 = 1.000**. In a
360 × 203 frame, `relayout()` reserves `--topband` and `--band`, leaving a play region roughly
360 × 120; since `360/120 = 3.0 > 1.000`, **height binds**: the board renders **120 × 120**, i.e.
**12.0 px per cell**, with the whole grid in frame — which is why `#viewpanel` is dropped. That
letterbox leaves **two ~120 px gutters**, and this game uses them: the **level ribbon and the six
pips live in the left gutter**, the **dead-square inset in the right**, so neither ever overlaps the
board and neither ever enters the transport band. Five rules are added and asserted by
`tests/test_sokoban_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, the single plate keeps only `alias + name + solved + the four box chips`; the avatar
   shrinks to 10 px and the fallback glyph moves inline.
3. Under `.tiny`, the level ribbon wraps to at most **two lines at 9 px** (`LEVEL 3/6 · MEDIUM` /
   `17 PUSHES · MOVE 38/200`), with the full string in the `title` attribute and re-announced in
   `#bannerlane` at every `levelstart`.
4. Under `.tiny`, the level pips drop their tier captions to tooltips and render as six 12 px pips in
   a row; the dead-square hatch goes to a **higher-contrast** 26 % alpha, because a 12 px cell cannot
   carry a subtle wash.
5. Under `.tiny`, the dead-square inset is pinned to 84 px square in the right gutter (the `#fpv-grip`
   resize is disabled below 620 px so it cannot be dragged over the board), and every glyph it draws
   is a chip, never text, at `--hudscale`-derived sizes so nothing is drawn outside the canvas
   (`--strict-text-bounds` stays on).

---

## Packaging

- **Repo**: `Metta-AI/cogame-sokoban`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `sokoban`; **`game.name` is `sokoban`** —
  identical to the slug, so the secret namespace `secret://coworld/sokoban/anthropic_api_key`, the
  page slug, the `POST /coworld-league-seeds` body and the docs all agree (the commons-family
  2026-08-24 scar, where `game.name` and the slug differed by an underscore).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two services/two
  images (`compose.yaml` `game` + `player`); this fork uses the one-image / two-entrypoints shape
  because the shared `docker_smoke.sh` and `policies.json` assume a single image (the knights-archers
  precedent):

  ```yaml
  services:
    sokoban:
      image: coworld-sokoban:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{SOKOBAN_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:sokoban src/sokoban.nim` →
  `/bin/sokoban`, and the same for `src/sokoban_player.nim` → `/bin/sokoban-player`. The runtime stage
  copies both binaries, `data/` (including `data/levels/fallback_{unfiltered,medium,hard}.xsb`),
  `client/`, `*.json`. `CMD ["/bin/sokoban"]`, runtime `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block)
  with the asset list swapped to `data/{arena_floor,ascii,pallete}.png`,
  `data/soldier_red{,_front}.png`, `data/font.ttf`, `client/art/walls/*`,
  `client/art/lockerroom/{bg.jpg,red_*.webp}`, `sokoban_replay.{js,wasm,data}`, `wire_constants.js`,
  `broadcast_core.js`, `chrome_common.js`, `static_replay.js`, `static_replay_worker.js`,
  `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["sokoban", "single-agent", "planning", "puzzle",
    "irreversible"]` (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0);
    **`episode_timeout_minutes: 20` at the top level**, not under `game`.
  - `game.name = "sokoban"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/sokoban"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/sokoban/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 1/1, `players` 1/1, `slots` 0/1, `tierLadder` 6/6 — the tandem 0.1.0 scar). `tokens` is
    described as runner-injected; **no `game_config` anywhere in this manifest contains a literal
    `tokens` array** (matriculate rejects "game_config must not include runner-managed tokens" —
    knights-archers 0.1.0), while `config_schema` keeps *requiring* it because the runner injects it.
    Properties: `tokens`, `players`, `slots`, `seed`, **`num_agents`** (integer, `minimum: 1`,
    `maximum: 1`, default 1), `minPlayers`, `gridSize`, `boxCount`, `levelCount`, `tierLadder`,
    `turnMoves`, `levelTurnCap`, `stepBudget`, `maxTurns`, `maxTicks`, `parWeight`,
    `maxActionsPerTurn`, `macroPrimitiveCap`, `genNodeCap`, `genAttemptCap`, `baselineNodeCap`,
    `attempt1Ms`, `retryMs`, `turnBudgetMs`, `turnSpacingMs`, `wallClockBudgetSeconds`,
    `lobbyJoinTimeoutTicks`, `gameOverTicks`, `fastMode`, `showPlayerLabels`, `model`,
    `maxOutputTokens`.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}`,
    `endRule: {"type":"string","enum":["ladderComplete","turnCap","wallClock","fault"]}`,
    `levelOutcome` items `{"enum":["solved","deadlocked","outofsteps","unreached"]}` and `levelTier`
    items `{"enum":["unfiltered","medium","hard"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-sokoban/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"actions.md","title":"Actions and the reply format","content":{"type":"uri","value":".../docs/ACTIONS.md"}},
    {"id":"levels.md","title":"Where the levels come from","content":{"type":"uri","value":".../docs/LEVELS.md"}}]}`.
  - Top-level `player[]` with `id` / `type` / `name` / `description` / `image` / `run` /
    `source_url` and `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` —
    **`limits.cpu` must be at least `"1"`** (pistonball 0.1.1). **Exactly ONE entry, `pusher`**:
    `num_agents = 1` leaves exactly one certification slot, and **every declared player must occupy a
    certification slot** (the raid 0.1.2 scar), so a second declared player could not be seated.
    `nudger` still ships in the image, is exercised by `tests/test_sokoban_baselines.nim`, and is a
    league filler in `tools/ci/policies.json` — it is simply not a *declared manifest* player.

  **Variants — `num_agents: 1` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "ladder", "name": "Tier ladder (1 cog, 6 Sokoban levels)",
     "description": "Six freshly generated 10x10 Sokoban levels, four crates each, walked up the three Boxoban tiers: two unfiltered, two medium, two hard. Crates can only be pushed, never pulled, so one crate shoved into a corner ends the level on the spot. Two hundred moves a level. Score is levels solved, weighted 1/2/3 by tier.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "gridSize": 10, "boxCount": 4, "levelCount": 6,
                     "tierLadder": ["unfiltered","unfiltered","medium","medium","hard","hard"],
                     "turnMoves": 20, "levelTurnCap": 10, "stepBudget": 200,
                     "maxTurns": 60, "maxTicks": 1200, "parWeight": 5,
                     "maxActionsPerTurn": 8, "macroPrimitiveCap": 32,
                     "genNodeCap": 200000, "genAttemptCap": 8, "baselineNodeCap": 20000,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9000, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 690, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "hard", "name": "Hard ladder (1 cog, 6 levels, four of them hard)",
     "description": "The same six-level format with the easy tier removed: two medium levels and then four hard ones, each solvable in 23 to 34 pushes and each one bad shove from dead. This is where a searching baseline stops scoring and a planning policy separates.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "gridSize": 10, "boxCount": 4, "levelCount": 6,
                     "tierLadder": ["medium","medium","hard","hard","hard","hard"],
                     "turnMoves": 20, "levelTurnCap": 10, "stepBudget": 200,
                     "maxTurns": 60, "maxTicks": 1200, "parWeight": 6,
                     "maxActionsPerTurn": 8, "macroPrimitiveCap": 32,
                     "genNodeCap": 200000, "genAttemptCap": 8, "baselineNodeCap": 20000,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9000, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 690, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 1` again, inside `certification.game_config`, and exactly
  one player so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS == 1`
  (the four `SEAT-COUNT` invariants `tools/ci/docker_smoke.sh` cross-checks at template lines
  113-150), with the single declared player seated:

  ```json
  "certification": {
    "players": [{"player_id": "pusher"}],
    "game_config": {"players": [{"name": "Alpha"}],
                    "num_agents": 1, "minPlayers": 1, "seed": 42,
                    "gridSize": 10, "boxCount": 4, "levelCount": 6,
                    "tierLadder": ["unfiltered","unfiltered","medium","medium","hard","hard"],
                    "turnMoves": 20, "levelTurnCap": 10, "stepBudget": 200,
                    "maxTurns": 60, "maxTicks": 1200, "parWeight": 5,
                    "maxActionsPerTurn": 8, "macroPrimitiveCap": 32,
                    "genNodeCap": 200000, "genAttemptCap": 8, "baselineNodeCap": 20000,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  A `pusher`-only episode is scripted throughout, so the whole ladder is a couple of seconds of sim,
  but the replay is hundreds of ticks ⇒ **tens of seconds of playback**, which the viewer soak needs.
  Seed 42 is asserted by `tests/test_sokoban_engine.nim` to produce a fixture episode with **at least
  400 recorded ticks, at least one `solved` level and at least one `deadlock` event**, so the smoke
  replay always exercises the `solved`, `boxon` and `deadlock` beat paths. The certify step in
  `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 covers start + connect
  grace + play + linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/sokoban-player"`, following the
  starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"sokoban-lookahead","run":"/bin/sokoban-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"lookahead"}},
   {"name":"sokoban-orderfirst","run":"/bin/sokoban-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"orderfirst"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"sokoban-pusher","run":"/bin/sokoban-player",
    "env":{"PLAYER_SCRIPTED":"pusher","PLAYER_POLICY_LABEL":"pusher"}},
   {"name":"sokoban-nudger","run":"/bin/sokoban-player",
    "env":{"PLAYER_SCRIPTED":"nudger","PLAYER_POLICY_LABEL":"nudger"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `pusher` and `nudger`, and their
  versions must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the
  **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps
  the template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `sokoban`,
  `<IMAGE>` → `coworld-sokoban`, **`<SEATS>` → `1`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server) and
  `--soak 10` added to the `viewer_smoke.mjs` invocation (which already passes
  `--strict-text-bounds`). The push-triggered `upload-coworld` job is gated on the `UPLOAD_REQUIRED`
  repo variable (derks-gym 0.1.1). `coworld-release.yml` and `coworld-submit.yml` are the templates,
  with `--timeout-seconds 300` on the certify step. `tools/ci/docker_smoke.sh` and
  `tools/build_replay_viewer.sh` are committed **executable** (mode 100755) — CI asserts the bit and
  invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_sokoban_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in
both debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_sokoban_sim.nim`)
1. `grid and XSB` — 10 × 10; the whole border ring is wall; the glyph table is total and
   round-trips (parse → render → parse is the identity over 1 000 random boards); rows are always
   exactly 10 characters and there are always exactly 10.
2. `the four primitives` — walking into floor moves; walking into a wall is a no-op that still costs
   a move and increments `blockedMoves`; walking into a box with free floor beyond pushes it and moves
   the player; walking into a box with a wall or a box beyond is a no-op; `wait` mutates nothing.
   **No rule anywhere moves a box backwards** — a source-level assertion plus a 10 000-step random
   walk in which the multiset of box cells only ever changes by a legal push.
3. `push accounting` — `pushes`, `boxesOnTargets`, `levelBoxesPlaced` (a running maximum, never
   decremented) and `boxon`/`boxoff` all update exactly per tick step 3–4.
4. `dead squares` — the fixpoint flood over 12 hand-built fixtures: every interior corner without a
   target is dead; a wall-line with no target on it is dead end to end; a target cell is never dead; a
   cell with a legal pull chain to a target is never dead. Cross-checked by brute force on 200 small
   boards: a cell is in `D` iff an exhaustive push search from a single box on that cell reaches no
   target.
5. `2x2 frozen block` — fires on four wall-or-box cells with an unparked box; does **not** fire when
   every box in the block is parked; does not fire on a 2 × 2 of walls alone.
6. `no-push deadlock` — fires exactly when the legal-push set is empty and a box is unparked.
7. `detector soundness` — over 5 000 random reachable positions drawn from the generator's backward
   BFS (every one of which is solvable **by construction**), `isDeadlocked` returns false **every
   time**. A detector that ever flags a winnable position fails the build. This is the single most
   important test in the repo.
8. `walk BFS` — the path is unique for a given board (neighbour order `U, D, L, R`), never passes
   through a wall or a box, and yields zero primitives with `unreachable` for a walled-off target.
9. `turn and tick order` — the numbered resolution order of §The game end to end: the queue empties
   into `wait`; a finished level breaks the tick loop; the next level starts on the next turn; skipped
   ticks are never counted in `levelMoves`; the step cap fires at exactly move 200.
10. `scoring` — `scores[0] == 1_000_000×solvedWeight + 10_000×boxCredit + movesSavedTotal` over 500
    randomised end states; both lexicographic dominance bounds hold (`241_194 < 1_000_000` and
    `1_194 < 10_000`); the maxima are `12_241_194` (ladder) and `16_241_194` (hard); the minimum is 0;
    `win[0]` is `solvedWeight >= parWeight`; `winner` is `0` when `win[0]` and `null` otherwise.
11. `end conditions` — `ladderComplete`, `turnCap`, a forced wall-clock stop and a forced fault each
    produce the right `endRule` and the right episode `reason`; a wall-clock stop mid-ladder marks
    every unstarted level `unreached` with zero moves, zero turns and zero boxes placed, and still
    scores the levels that ran.
12. `no floating point in the sim` — a source grep over
    `src/sokoban/{sim,grid,deadlock,levelgen,search,driver,baselines}.nim` finds no `float`, `/`,
    `sqrt` or float literal.
13. `tick budget` — a full 1 200-tick episode completes in < 1 s in a release build.

**Level generation** (`tests/test_sokoban_levelgen.nim`)
14. `levels are pure` — every level of every variant is identical under three different policy
    behaviours, character for character, including its dead-square set and `optPushes`.
15. `optPushes is exact` — over 300 generated levels of all three tiers, an independent forward
    breadth-first push search (written separately from `search.nim`, unbounded on these small
    instances) finds a solution in exactly `optPushes` pushes and none shorter.
16. `tier bands hold` — over 2 000 seeds per tier, `optPushes` lands inside the declared band, and
    `levelTierRelaxed` is set on every level where it does not. The relaxed rate is asserted to be
    **< 1 %** so a bounced band shows up as a test failure, not as a quietly easier ladder.
17. `every level is solvable and well-formed` — 5 000 seeds: the border ring is intact, the floor is
    4-connected with ≥ 44 cells, exactly 4 boxes and 4 targets, at most one box starts parked, **no
    box ever starts on a dead square**, and the player starts on a free floor cell.
18. `generation is bounded` — `genNodeCap` and `genAttemptCap` are respected; the worst observed
    wall time for six levels over 1 000 seeds is asserted under 6 s in a release build; the
    degenerate-room path loads the committed `data/levels/fallback_*.xsb` and those three files parse,
    are solvable, and carry the tier they are filed under.
19. `no network, no dataset` — a source grep asserts the repo contains no URL fetch, no Boxoban file
    and no level data outside `data/levels/fallback_*.xsb`.

**Bounded orders / legality on the scripted baselines** (`tests/test_sokoban_baselines.nim`)
20. `baselines are bounded` — for 300 pseudo-random states (all three tiers, mid-level and fresh,
    boxes parked and loose) and for **both** `pusher` and `nudger`: the reply has at most 8 actions,
    every `do` is in the enum, every `box` is 0…3, every `dir` is in the enum, every `times` is 1…8,
    `seq` is `UDLR`-only and ≤ 20 characters, `say` and `notes` are empty, and the serialised
    directive is ≤ 1024 bytes. A baseline that ever proposes an illegal or unbounded action fails the
    build.
21. `baselines never deadlock on purpose` — over the same states, neither baseline emits a push onto
    a dead square or a push creating a 2 × 2 frozen block **while a non-deadlocking push exists**.
22. `driver never produces an illegal primitive` — every expanded queue is ≤ 20 primitives, every
    entry is one of `U, D, L, R, wait`, every macro expands to at most `macroPrimitiveCap`, and an
    empty queue yields `wait`, never nothing.
23. `fallback is the pusher proc` — the decision engine's fallback path and the `pusher` baseline
    resolve to the same proc, so they cannot drift.
24. `reply validation` — the validator accepts the schema, **drops** (never rewrites) an invalid
    action, clamps `goto` coordinates and `times`, lower-cases `do`, case-folds `dir` and `seq`,
    accepts a `say`-only reply, rejects a non-object, truncates `say`/`notes` on **rune** boundaries at
    140/320 with 4-byte emoji sitting exactly on the boundary, caps the read at 4096 bytes, caps
    `actions` at 8, and reports `truncated` / `dropped` / `unreachable` back accurately.
25. `baseline strength is in range` — over 100 seeds of `ladder`, `pusher`'s solve rate is inside the
    pinned band (unfiltered 0.6–0.95, medium 0.15–0.55, hard 0.0–0.2) and `nudger`'s is strictly
    lower on every tier while still solving at least one level across the sweep. Neither a zero floor
    nor a superhuman filler can ship.
26. `baseline tuning is the swept pick` — the shipped `baselineNodeCap` / matching rule / tie-break
    equal `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern; `ci.yml` re-runs the
    sweep with `--check`).

**Observation** (`tests/test_sokoban_obs.nim`)
27. `board and structure agree` — over 1 000 states, re-parsing `board` reconstructs `player`,
    `boxes` (with the same indices) and `targets` exactly; `boxes` is sorted ascending by `(y, x)`.
28. `pushes_available is exactly the legal set` — over 1 000 states it equals the set the sim itself
    would accept, computed by the independent legality predicate, and it carries **no** deadlock
    annotation.
29. `nothing hidden leaks` — the serialised observation and prompt contain no `seed`, no future
    level, no solution, no score, and no real policy name; a grep test over a full recorded episode.

**End-to-end episode writing a replay** (`tests/test_sokoban_engine.nim`)
30. `episode writes artifacts` — run a real one-seat episode (`ladder`, scripted, no API key so the
    LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert `results.json` and the
    `.replay` are written, `reason == "complete"`, `scores` agree with the formula, all six results
    identities of §Server hold, and the results key set equals the manifest's `results_schema` key set
    **exactly**.
31. `the cert seed is interesting` — seed 42 on `ladder` yields ≥ 400 recorded ticks, at least one
    solved level and at least one `deadlock` event, so the CI smoke replay always exercises those
    paths and always outlasts the 10 s viewer soak.
32. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure
    payload; the server refuses to start the game (loudly) when the joined seat has no register
    record.
33. `budget guard and rate guard settle early` — with each guard forced, the episode finishes
    `complete`, not `deadline`, and the matching record names the turn.

**Replay** (`tests/test_sokoban_replay.nim`)
34. `record then re-derive, every end reason` — for `ladderComplete`, `turnCap`, `wallClock` **and**
    `fault`, record an episode and re-derive it from the bytes; assert identical hashes at every tick
    **including the stop tick** (the particle-worlds scar).
35. `replay is self-sufficient` — the bytes alone yield the seat's real name, its alias, the policy
    kind, the full config (every constant in §Server's config-JSON row), the seed, the variant, **all
    six level boards with their tiers, `optPushes` and dead-square lists**, every plan record, every
    chat record and the result; and re-simulating from them reproduces every frame with **no
    generator call and no fetch**.
36. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports
    `protocol == "sokoban/v1"`.
37. `determinism from the replay alone` — re-simulate from the replay's levels and plan records on a
    fresh sim: identical final tick, levels solved, box credit and per-tick `gameHash`.
38. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`,
    kept.

**Manifest** (`tests/test_sokoban_manifest.nim`)
39. `manifest pins` — **`num_agents == 1` in both variants' `game_config` AND in
    `certification.game_config`**; `num_agents` absent at every variant top level; no literal `tokens`
    in any `game_config`; `len(player) == 1` and that player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 1`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 690`;
    `attempt1Ms + retryMs ≤ turnBudgetMs` and both whole seconds;
    `stepBudget == levelTurnCap × turnMoves`, `maxTurns == levelCount × levelTurnCap`,
    `maxTicks == maxTurns × turnMoves`, `len(tierLadder) == levelCount`;
    `game.name` equals the slug and the secret URI's namespace; **and every variant's `game_config`
    actually constructs a valid `GameConfig`, generates all six of its levels, and produces the tier
    ladder and the 60-turn schedule this note claims** (the collab-cooking 0.1.1 scar: test every
    variant, not just the fixture).
40. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` —
    the collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_sokoban_viewer.nim`, static assertions in the `test` job)
41. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals
    `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, pinned as a literal, and the
    file is 40 022 bytes.
42. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker (`replay_broadcast.html:4344`) and only appends after it;
    `broadcast_core.js`'s kept procs are byte-identical to the starter's, `pushFeed`'s signature
    included.
43. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (`replay_broadcast.html:1635`, the tandem hoisting trap); the beat
    builder is `skBeat`, never `markBeat`.
44. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{levelstart, boxon, deadlock, solved, failed, fallback, end}`.
45. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()`
    sets `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the
    band; the five `.tiny` rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`,
    `#zoom-*`, `#povBadge`, `#fpv-hp`, `#fpv-gear`, `#fpv-map*`) appear nowhere, while the kept
    `#fpv`, `#fpv-canvas`, `#fpv-name`, `#fpv-cap` and `#fpv-grip` are all present.
46. `endcard labels` — `tests/test_sokoban_endcard_labels.nim`: zero matches for the forbidden
    paintbot vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
47. `label manifest` — the starter's `test_label_contract` pattern: the emitted board-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
48. `events are the closed enum` — `tests/test_sokoban_events.nim`: the set of kinds `stepEvents` can
    emit equals exactly the twelve listed in §Server, every kind used by the appended game block is in
    that set, and **no kind fires per tick**.

**Viewer smoke — the bundle is EXECUTED, not merely built**
49. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced** (downloaded
    as the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both the npm
    module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the
    bridge `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays on.
50. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, the CI replay's seat plays scripted and emits **no `say` at all**, so the
    smoke replay can never exercise the feed's narration path (the cogchemists 2026-08-24 scar). The
    fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only
    the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) —
    driving the real page with a full-cap 140-rune `say`, a fully hatched dead-square board, a
    `DEADLOCK CREATED` banner, all six level-pip states, all three tier names, and a deadlocked
    endcard, at several canvas widths including 360 px.
51. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.

---

## Out of scope (v1)

- **Any gym-sokoban or Boxoban dependency, and bit-exactness with either.** Decided as a scoping rail
  and recorded in `docs/LEVELS.md`: no upstream code is vendored, no Boxoban level is shipped or
  fetched, no upstream numbers are claimed as reproduced, and no score from this coworld is comparable
  to a published Boxoban number. This coworld implements the problem, not the package.
- **Board sizes other than 10 × 10, box counts other than 4, and seat counts other than 1.**
  `num_agents` is fixed at 1 in every variant and in the cert fixture. A second board size would fork
  the viewer's layout arithmetic and every generator bound for no gain the idea asks for; a
  multi-agent Sokoban is a different coworld.
- **Pull mode, undo, and level restart.** gym-sokoban ships push-and-pull variants and every human
  Sokoban client has undo. All three are the exact opposite of "one wrong push and the level is dead"
  and none of them ships.
- **A complete deadlock oracle.** The detector is sound and incomplete on purpose (§The game). Corral
  deadlocks, bipartite-matching deadlocks and full freeze-set recursion are out; a position that is
  dead but undetected simply burns its 200 moves, which costs the policy the level exactly as a
  detected deadlock would.
- **Per-move LLM stepping, and an RL-vector observation.** The seat batches up to twenty moves a turn
  under a deterministic driver (§Sim module, divergence 4). A per-tick socket interface for an RL
  policy, and a numeric tensor observation to go with it, are what `COGAME_EVENTS_URI`'s `Move` and
  `Push` rows exist to make possible **later**; they are not a v1 interface.
- **A solver-strength ladder inside the game.** `pusher` is a fixed 20 000-node best-first search.
  Exposing node budget as a config knob so the league can run a "search strength" axis is a good idea
  and it is not v1: it would need its own variants, its own par values and its own leaderboard story.
- **Scoring pushes, walking efficiency or deadlock avoidance directly.** `pushesTotal`,
  `blockedMoves`, `deadlocks` and `outOfSteps` are measured, recorded in `results`, shown on the
  endcard and drawn in the feed, and deliberately **not** in `scores` (§The game). Paying for
  deadlock avoidance would reward a cog that never pushes at all.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the
  hosted spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, vision cones, raycast fog, the
  first-person renderer, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches,
  perks, handicaps, lives, teams, four-team play, shouts, achievements, campaign mode, multi-game
  episodes, the procedural map generator, the map pool, the map editor and mapkit — all deleted, not
  disabled (§Sim module), and none of them return in v1.
