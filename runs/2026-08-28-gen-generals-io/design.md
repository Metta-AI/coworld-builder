# cogame-gen-generals-io — design note (2026-08-28, paintbot lineage)

*Destination path in the new repo: `docs/plans/2026-08-28-gen-generals-io-design.md`. This file is
the run-directory copy (`runs/2026-08-28-gen-generals-io/design.md`); phase 20 places the identical
bytes at the destination path above.*

`Metta-AI/cogame-gen-generals-io` is a **four-seat, free-for-all, fog-of-war conquest game on a
16 × 10 grid**: a standalone generals.io-style coworld. Every commander starts on one crowned tile
in one corner of a four-fold-symmetric board, sees only the tiles it owns and the ring of tiles
touching them, and spends one move a turn pushing armies outward. Armies grow on cities and crowns
every turn and on every owned tile every twenty-five turns. **Capture another commander's crown and
you inherit every tile they own** — their land, their armies (halved), their cities — and they are
out. Last crown standing wins; if the clock runs out first, the ranking is survival, then land, then
army. It is forked from **`Metta-AI/coworld-ctf`** (paintbot), read at its read-only mount
`/workspace/starters/coworld-ctf`. **Every convention there holds here unless this note says
otherwise** — the tick loop and the `Lobby → Playing → GameOver` phase machine, the `COWLDCTF`
binary replay codec with its per-tick `gameHash` chain and `ReplayKeyframeTicks`, the lull scan and
the beat timeline, the whole server-side decision layer (`src/ctf/{decide,directives,llm,baselines,
control}.nim` — one parallel batch per turn, two bounded whole-second deadlines, the `turnSpacingMs`
rate floor, the budget guard, tolerant JSON parsing, rune caps, scripted fallback), the mummy server
and its `COGAME_*` runtime contract, the four-team seating and the `cogAlias` two-name-space rule,
the broadcast chrome (`client/replay_broadcast.html` + `client/chrome_common.js` +
`client/broadcast_core.js`, whose scorebug already lays out four plates on one band —
`.plates.row`, `client/replay_broadcast.html:2204-2208`), the emscripten static replay bundle
(`replay-viewer/`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`) and the `GameVersion`
changelog discipline are all inherited.

**Starter choice, in one line:** coworld-ctf is the starter table's row for **any real-time game
loop whose rules are written for this coworld** — this is a new grid game, not a bit-exact port of an
existing C/RL environment (so the `cogame-moba` row does not apply) and not a talk/cards game (so
babel does not) — and paintbot already ships, tested, every layer this game needs except the
generals rules themselves: a tick loop with a per-tick hash chain, a **four-team** seating and alias
system, a server-side per-turn LLM directive layer with a deterministic compiler and a scripted
fallback beneath it, a binary replay the browser re-simulates, and a static wasm viewer with real
art and real chrome.

**Source idea, verbatim:**

> GEN Generals.io (variant of coworld-planet-wars) — fog of war and a capture-the-general snowball on the existing conquer-and-send-ships map
>
> Candidate EXTENSION of Metta-AI/coworld-planet-wars — Planet Wars (players conquer planets and launch ships across a small star map; Nim; certified 0.1.4) already has the growth-and-capture loop. Generals.io differs in three rules that fit as a variant: (1) fog of war — you only see tiles/planets adjacent to yours; (2) a general/capital whose capture hands the captor everything the victim owned; (3) per-tile army growth (+1 every 25 turns) with cities/planets as accelerators. If Planet Wars' map model can't express adjacency fog, fall back to a standalone grid port (github.com/strakam/generals-bots has a PettingZoo env).
>
> Seats: 2 or up to 8 FFA
> Motive: zero-sum
> Policy interface: one move per tick; LLM plausible with a decoded fog map
> Fills gap: fog-of-war snowball; 23 Cogplomacy has no fog
> Integrity (anti-collusion): FFA teaming endemic on the real site — seat randomisation, anonymous aliases, alliance audit; 1v1 as the clean ladder.
>
> Source: generals.io bot API; github.com/strakam/generals-bots; github.com/Metta-AI/coworld-planet-wars.

**The coordinator ruling this note is written inside, and does not reopen.** This coworld is a
**STANDALONE grid game built on coworld-ctf** — the idea's own fallback path. `coworld-planet-wars`
is not one of the six starters, is not mounted, and **nothing here is designed as an extension of
it**. The three generals.io rules the idea names (adjacency fog, crown capture transfers everything,
+1 per owned tile every 25 turns with cities and crowns growing every turn) are implemented directly
on a new integer grid. No file, constant or trajectory in this repo is compared against
`generals-bots` or against generals.io itself; the PettingZoo environment is a reference for the
*rules*, not a port target.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")

| Pin | How cogame-gen-generals-io satisfies it |
|---|---|
| Starter by game shape | **`coworld-ctf` (paintbot)** — a game loop with rules written for this coworld; the tick loop, four-team seating, decision layer, replay codec and wasm viewer fork rather than get rewritten. (§The game, §Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-gen-generals-io`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions) vs `PLAYER_SCRIPTED=sprawl` / `PLAYER_SCRIPTED=crown` (both fillers); one image `coworld-gen-generals-io`, player entrypoint `/bin/gen-generals-io-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`; ctf's `tools/build_replay_viewer.sh` and `Dockerfile.replay-viewer` kept; the **same Nim sim modules** compile into `replay-viewer/gen_replay.nim` under emscripten and re-simulate every turn in the browser. (§Viewer) |
| Real art, starter chrome verbatim | ctf's `client/chrome_common.js` **byte-for-byte**; `client/replay_broadcast.html` = the starter's page **with one appended game block**; the board is baked from `data/arena_floor.png`, `client/art/walls/*.jpg` and `data/pallete.png`, crowns from `data/soldier_{red,blue,green,yellow}_crown.png`, keeps from the wall textures. No placeholders, no downloads. (§Viewer → Art) |
| Two name spaces | In-game the seats are `RED-alpha`, `BLUE-alpha`, `GREEN-alpha`, `YELLOW-alpha` (the starter's **unmodified** `cogAlias`, `src/ctf/sim.nim:280`); real policy names live only in `results.names`, the replay join records, the DOM scorebug and the endcard. Test-enforced from both sides. (§Server, §Viewer, §Tests) |
| Degrade-never-hang, inside 60 % of `episodeTimeoutSeconds` 1200 | typical 304 s / absolute worst 452 s against a 720 s budget; a 660 s engine stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4** inside `game_config` of variants `ffa`, `blitz` and `citadels` **and** inside `certification.game_config`; `<SEATS>` = 4 in `tools/ci/docker_smoke.sh`. Never at a variant's top level. (§Packaging) |

**There is no `OPEN` section.** Everything the idea leaves loose — seat count, board size and shape,
the clock, city defence, what a fogged tile reports, how a four-way free-for-all is scored on an Elo
ladder, how a 240-turn game is priced against an LLM budget — is a designer or coordinator rail, and
each is decided below with its reason. Nothing is deferred to the builder.

---

## The game

**Four crowns, one grid, and a fog you have to walk into.** Turn 0: each commander owns exactly one
tile — its **general**, drawn as a crown — with one army on it. The crown gains +1 army every turn,
so at turn 20 it holds 21 armies and the commander can start pushing them outward: a move sends
armies from a tile you own onto a touching tile, taking it if you send more than sits there. Empty
plains hold nothing, so early expansion is nearly free and the first sixty turns are a land grab
into the dark. Neutral **cities** hold 40 armies and are the only structures on the board worth
breaking: once yours, a city grows +1 every turn just like a crown, and two cities roughly triples
your production.

Every **25 turns** every tile you own gains +1 army at once. That is the beat the whole game is
played against — land is production, and a commander with forty tiles gains forty armies where a
commander with twelve gains twelve. It is also why the fog matters: you always know, from the public
standings, exactly how much land and army each rival has; you do not know **where** any of it is, or
where their crown is, until you walk a scout into their half and see it.

And then the snowball. Move enough armies onto a rival's crown and you take **everything they own**
— every tile, with its armies halved — their crown becomes a city of yours, and they are out of the
game. One capture in a four-way game typically doubles the captor. The remaining commanders can see
it happen in the standings the same turn, and they have to decide whether to keep expanding or come
for the leader.

### Seats, sides, aliases

- **`num_agents` = 4.** Exactly four seats, always — in all three manifest variants and in the
  certification fixture. **One seat commands one army**: every tile and every crown it owns.
  **Why four and not two:** the idea's headline mechanic is a *snowball* — "a general whose capture
  hands the captor everything the victim owned" — and in a duel that rule is not a snowball at all,
  it is simply the win condition, firing once at the end of the game with nothing left to compound
  into. Three or more seats is the minimum for the inherited land to be *used*, and four is the
  number the starter's chrome and art already carry (four team colours `Red/Blue/Green/Yellow`,
  `src/ctf/sim_types.nim:991`; a four-plate scorebug row, `client/replay_broadcast.html:2204`;
  `data/soldier_{red,blue,green,yellow}_front.png` and their crown variants already copied into the
  viewer bundle by `Dockerfile.replay-viewer`). Four is also exactly the platform's standard policy
  set — champion #1, champion #2, filler #1, filler #2 — so one episode seats the whole ladder.
- **The idea's collusion worry is answered structurally, not by policy.** The idea flags that FFA
  teaming is endemic on the real generals.io. Here there is **no inter-seat channel of any kind** —
  no chat, no radio, no `say`, no emote, and no shared state a seat could signal through (§Decisions
  → observation). Seats see only anonymous aliases and never learn which policy or player holds a
  rival seat, and the platform assigns policies to slots. A durable alliance needs identification and
  a channel; this game supplies neither, and the scoring is strictly constant-sum (§Scoring), so
  helping a rival is always a loss. The idea's "alliance audit" is therefore not needed as a separate
  mechanism; what it would audit cannot be expressed.
- **Two name spaces.** In-game the four seats are **`RED-alpha`** (seat 0), **`BLUE-alpha`**
  (seat 1), **`GREEN-alpha`** (seat 2) and **`YELLOW-alpha`** (seat 3) — the starter's `cogAlias`
  (`toUpperAscii(teamText(team)) & "-" & IdentityNames[identityIndex]`) with `teams: 4`,
  `cogsPerTeam: 1`, so `roster.nim`'s alias machinery needs **no edit at all** and its inherited
  privacy test applies unchanged. Prompts, observations, the ASCII maps and every sprite label carry
  only those four strings (abbreviated `RED` / `BLUE` / `GREEN` / `YELLOW` in map legends and the
  feed). The seats' **real policy and player names** (`daveey`, `daveey-1`,
  `gen-generals-io-sprawl`, `gen-generals-io-crown`) appear only in `results.names`, in the replay's
  join records, in the viewer's scorebug plates and on the endcard. `showPlayerLabels` is **false**.
  A seat can never learn who it is playing.
- Colours and corners are fixed by seat: seat 0 red / top-left, seat 1 blue / top-right, seat 2
  green / bottom-left, seat 3 yellow / bottom-right.

### The board

`boardW` = **16**, `boardH` = **10** — 160 cells (`ffa`, `citadels`; 12 × 8 = 96 in `blitz`). Cells
are `(x, y)`, `x` rightwards from 0, `y` downwards from 0; the cell index is `y * boardW + x`, and
every tie-break in this note that says "lowest cell index" means that number. A 16 : 10 board is
chosen because the featured-match iframe is 16 : 9 — a square board wastes a third of the frame, and
cell size is what decides whether an army numeral is readable (§Viewer → Legible at 360 px).

Each cell carries `kind ∈ {plain, mountain, city, general}`, `owner ∈ {none, 0, 1, 2, 3}` and
`army: int32 ≥ 0`. Mountains are impassable and never owned. Cities and generals are passable and
ownable. Only `plain`, `city` and `general` cells can hold armies.

**The map is generated once, at reset, from the episode seed, and is four-fold symmetric** under
reflection in both axes: the top-left quadrant (`qw = boardW div 2` = 8 columns × `qh = boardH div 2`
= 5 rows) is drawn, then copied to `(boardW-1-x, y)`, `(x, boardH-1-y)` and `(boardW-1-x, boardH-1-y)`.
Every seat therefore gets a congruent starting position — same crown offset, same mountains, same
cities, same distances to each of the three rivals — which is the idea's "maps seeded" integrity
requirement made structural: no seat can be dealt a better corner, and a spectator can see that at a
glance.

Generation runs from a dedicated `mapRng` stream seeded by `seed`, over the **top-left quadrant
only**, in this exact order:

1. Every quadrant cell is `plain`, `owner = none`, `army = 0`.
2. **General.** `gx = 1 + mapRng.rand(qw - 3)`, `gy = 1 + mapRng.rand(qh - 3)` (on 8 × 5:
   `gx ∈ 1..6`, `gy ∈ 1..3`, never on a board edge). That cell becomes `kind = general`,
   `owner = 0`, `army = 1`.
3. **Mountains.** `mountainsPerQuadrant = (qw * qh * mountainPct) div 100` = `(40 * 22) div 100` =
   **8** (32 on the board). Rejection sampling: draw a uniform quadrant cell; accept only if it is
   `plain` and its Chebyshev distance from the general is ≥ 2. Set `kind = mountain`.
4. **Cities.** `citiesPerQuadrant = cityCount div 4` = **2** (8 on the board). Rejection sampling:
   draw a uniform quadrant cell; accept only if it is `plain`, its Chebyshev distance from the
   general is ≥ 3, and its Chebyshev distance from every already-placed city is ≥ 2. Set
   `kind = city`, `owner = none`, `army = cityArmy` (**40**).
   Both samplers retry at most 500 times and then relax their separation by 1 each further 200
   attempts, so they always terminate.
5. **Mirror** the quadrant into the other three. The general in quadrant `q` becomes seat `q`'s, in
   the order top-left, top-right, bottom-left, bottom-right.
6. **Connectivity repair, symmetric.** Flood-fill 4-connected from seat 0's general over all
   non-mountain cells. While some non-mountain cell is unreached: take the unreached non-mountain
   cell with the lowest index, run a Dijkstra from the reached set to it with `mountain` costing
   1000 and everything else costing 1, take the **first mountain cell on that path** (ties by lowest
   cell index), and convert that cell **and its three mirror images** to `plain`. Re-run the fill.
   Bounded by the mountain count, so it terminates; symmetric by construction, so step 5's
   invariant survives. `tests/test_gen_board.nim` asserts both properties over 10 000 seeds.

The board is a pure function of `(seed, boardW, boardH, mountainPct, cityCount, cityArmy)`. `mapRng`
is consumed by the generator at reset and **never again**, so nothing a policy does can steer a draw.

### The clock

- **One tick = one turn.** `maxTurns` = **240** (`ffa`, `citadels`) / **160** (`blitz`).
- **Growth beat** = `growthPeriod` **25** turns (**15** in `blitz`): on every turn where
  `turn > 0 and turn mod growthPeriod == 0`, every owned cell gains +1. Nine growth beats in 240
  turns.
- **Directive turn** = every `directiveEvery` = **8** turns, beginning at turn 0 before any turn is
  stepped: turns 0, 8, 16, …, 232. **30 directive turns per episode** (20 in `blitz`). Eight is
  chosen because it is a whole number of turns shorter than the 25-turn growth beat — a commander is
  re-asked at least twice inside every production cycle, so a plan can react to a growth beat rather
  than straddle it — and because 30 × 4 seats is the largest call count that fits the wall clock
  (§Decisions).
- One game per episode (`maxGames = 1`). The board is four-fold symmetric, so there is no side to
  swap.
- The **lobby** runs at the starter's real-time 24 Hz before `Playing` (`startWaitTicks` = 48,
  `lobbyJoinTimeoutTicks` = 2400 = 100 s). Lobby ticks are not turns; `gameTurn =
  sim.gameTicksElapsed()`, the starter's existing split.

### Turn and tick structure — the exact resolution order

Everything below is one tick of `sim.step`. The steps run in this order and nothing else mutates the
world. **An action that is illegal at the moment it is evaluated is discarded and costs nothing
else** — the starter's repair-don't-punish discipline, applied to the sim.

1. **Directive install (directive turns only).** If `turn mod directiveEvery == 0`, the four
   directives collected by the decision layer *before* this tick is stepped (§Decisions) become each
   seat's `activeDirective`. The structured directive is written to the replay as an **input record**
   — it is load-bearing input, re-applied at playback before this same turn is stepped — and the
   human-facing `note`, `source` and `latency_ms` go out separately as a presentation chat record.
   The structured directive **is** mixed into `gameHash`; the `note` is **not**.
2. **Move compilation.** For each seat `s` in ascending seat index with `alive[s]`,
   `captain.compileMove(view(s), activeDirective[s], s)` returns at most one
   `Move(fromCell, dir ∈ {N,E,S,W}, amount: int32)` or nothing (§Decisions → "The captain"). This is
   a pure function of `(that seat's fogged view, its directive, its seat index)` — **the captain
   never reads a cell the seat cannot see**, which is what makes this a fog game rather than a fog
   costume. It is the determinism boundary, and the browser runs the identical code.
3. **Move resolution, in rotated seat order.** This is the **simultaneous-move conflict rule** and it
   is the only one: the four moves are applied **one at a time**, each fully evaluated against the
   already-updated board, in the order `order[k] = (turn + k) mod 4` for `k = 0, 1, 2, 3`. The
   rotation means priority moves round the table every turn — over 240 turns each seat leads 60 times
   — so no seat has a standing advantage, and every episode is decidable from the turn number alone.
   For each seat in that order:
   - **a. Legality re-check.** The move is **discarded** (nothing changes, `invalidMoves[s] += 1`)
     if any of: `fromCell` is not owned by `s`; `army(fromCell) < 2`; the target cell is off the
     board; the target cell's `kind == mountain`; the seat is no longer `alive` (its crown was taken
     earlier in this same turn). A seat whose source tile was captured by an earlier mover this turn
     loses its move — that is the cost of moving late, and it rotates.
   - **b. Amount.** `amount = clamp(move.amount, 1, army(fromCell) - 1)`. `army(fromCell) -= amount`.
     A tile always keeps at least 1 army.
   - **c. Friendly target** (`owner(target) == s`): `army(target) += amount`.
   - **d. Neutral or hostile target.** Let `d = army(target)` (a neutral plain has `d = 0`, a neutral
     city has `d = cityArmy` until first taken).
     - If `amount > d`: the target's `owner` becomes `s` and `army(target) = amount - d`. If the
       target's `kind == city`, `cities[s] += 1` and `cities[previousOwner] -= 1`; a `citytaken`
       event fires. If the target's `kind == general` and it belonged to a living seat `v`, go to
       **e**.
     - Else (`amount <= d`): `army(target) = d - amount`, the owner does **not** change, and
       `tilesLost` is not incremented (nothing was lost). A `stackclash` event fires when
       `min(amount, d) >= 10`.
   - **e. Crown capture** — seat `s` captures seat `v`'s general, in this sub-order:
     1. Every cell **other than the captured general cell** whose `owner == v` becomes
        `owner = s` with `army = army div 2` (integer division; a tile with 1 army becomes 0 and is
        still owned). `landInherited[s] += that count`; `armyInherited[s] += the halved sum`.
     2. The captured general cell becomes `kind = city`, `owner = s`,
        `army = amount - d` (the surviving attacker army, always ≥ 1). `cities[s] += 1`.
     3. `alive[v] = false`, `eliminatedTurn[v] = turn`, `eliminatedBy[v] = s`,
        `generalsCaptured[s] += 1`, `land[v] = 0`, `army[v] = 0`, `cities[v] = 0`.
     4. Events `generalcaptured {seat: s, victim: v, cell, landGained, armyGained}` and
        `eliminated {seat: v, turn, by: s}`.
     A seat eliminated this way emits no further moves for the rest of the episode; its directives
     stop being requested from the next directive turn.
   - **f.** `movesMade[s] += 1`. Ownership changes update `tilesTaken[s]` and `tilesLost[victim]`.
4. **Per-turn growth.** Every cell whose `kind ∈ {city, general}` **and** whose `owner != none` gains
   `+1` army, in ascending cell index. **Neutral cities do not grow** — their 40 is a fixed toll.
5. **Periodic growth.** If `turn > 0 and turn mod growthPeriod == 0`, every cell with
   `owner != none` gains `+1` army, in ascending cell index, regardless of kind. A `growth` event
   fires with the per-seat land and army totals.
6. **Vision and memory.** For each seat `s` with `alive[s]`, recompute
   `visible[s] = {c : owner(c) == s} ∪ {c : Chebyshev(c, c') == 1 for some c' owned by s}`. For every
   `c ∈ visible[s]`: `seenTurn[s][c] = turn`, `kindSeen[s][c] = kind(c)`,
   `ownerSeen[s][c] = owner(c)`. The first time a seat's `visible` set contains another living seat's
   general cell, a `generalspotted {seat, victim, cell}` event fires (once per ordered pair).
7. **Sim guard** — `checkGeneralsInvariants()` (§Sim module). A trip raises `GenGuardError` →
   `fault` / `sim_fault`.
8. **Hash and end check.** `replayWriter.writeHash(tick, sim.gameHash())`, then §End conditions.

Nothing else in the game is stochastic, ordered by anything but cell index or seat index, or
dependent on wall-clock time.

### Scoring formula and sign

Measured at the final turn (whatever ends the episode):

```
alive[s]           = true if seat s still owns its general
outTurn[s]         = eliminatedTurn[s] if not alive[s], else turnsPlayed
land[s]            = number of cells seat s owns
army[s]            = sum of army over the cells seat s owns
cities[s]          = number of cells of kind `city` seat s owns
```

Seats are ordered by this ladder — the first difference decides, and two seats equal on all five
terms are a genuine tie:

```
1. alive[s]   > alive[o]     ->  s ranks higher      (a survivor beats anyone eliminated)
2. outTurn[s] > outTurn[o]   ->  s ranks higher      (among the dead, whoever lasted longer)
3. land[s]    > land[o]      ->  s ranks higher      (generals.io's own leaderboard)
4. army[s]    > army[o]      ->  s ranks higher
5. cities[s]  > cities[o]    ->  s ranks higher
```

`rank[s] ∈ 0..3` is the standard competition rank under that ladder (a tie group of size `n` starting
at rank `r` occupies ranks `r .. r+n-1`). **The score the league ranks by is the placement point:**

```
placePoint(r) = (S - 1 - r) / (S - 1)     with S = num_agents = 4   ->  [1.0, 2/3, 1/3, 0.0]
scores[s]     = the AVERAGE of placePoint over the ranks that seat's tie group occupies
win[s]        = (rank[s] == 0)
winner        = the seat index with rank 0 when exactly one seat has it, otherwise null
```

**Sign: higher is better, and no term is ever negative.** `sum(scores) == S / 2 == 2.0` on every
episode without exception, ties included — a strictly constant-sum four-way game, which is the
zero-sum motive the idea asks for and is what the platform's Elo (1000 start, K 32) wants to eat.
Margin is deliberately not paid: a commander who wins with 90 land and one who wins with 41 both take
1.0, because generals.io margins are dominated by which corner the fog opened first and paying Elo
for margin would rank the seed. The margin is still fully recorded — `rank`, `land`, `army`,
`cities`, `generalsCaptured`, `eliminatedTurn`, `tilesTaken`, `tilesLost`, `movesMade`,
`invalidMoves`, `passes` are all in `results` (§Server) and all on the endcard.

A `deadline` episode is scored by the **same ladder at the turn the clock stopped**, never zeroed, so
it stays rankable.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly **three** values. `results.endRule` carries the detail
and is a closed enum of exactly **five**.

| `reason` | `endRule` | When |
|---|---|---|
| `complete` | `conquest` | At the end of step 8, exactly one seat has `alive == true`. The last crown standing wins outright: it takes rank 0, and the three eliminated seats are ranked by `outTurn`. This is the game's headline ending and the one the snowball produces. |
| `complete` | `full_time` | `turn == maxTurns` (240 / 160) with two or more seats still alive. Ranked by the full ladder above. The normal path in a cautious four-way game. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (default **660**) elapsed. The engine stops at the current turn, settles with the **real** ladder at that turn, writes `results.json` and the replay, and exits 0. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted model was slow, not that the game broke. The budget guard (§Decisions) exists so it should never fire. |
| `fault` | `sim_fault` | `checkGeneralsInvariants()` tripped. Settled from the last completed turn, `stopDetail` names it, artifacts still written, exit 0. A defect — `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it. |
| `fault` | `host_error` | An unexpected server-side exception. Same treatment. |

No other `reason` or `endRule` string is ever emitted; `game.results_schema` declares both enums and
`tests/test_gen_endings.nim` asserts the closure from both directions.

**Nothing a player container does can stop the clock.** A seat that never connects does not end the
episode: `lobbyJoinTimeoutTicks` expires, the no-show is reported once to
`COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload (exactly
`{"message", "failed_policy_index"}`, lowest missing slot only), that seat plays the `sprawl`
baseline for the whole episode, `deadSeats[s] = true`, and all 240 turns run. A seat that drops
mid-episode keeps playing on `sprawl` and revives on reconnect. An **eliminated** seat is not a
failure: its socket stays open, it receives frames to the end, and it is simply never asked for
another directive.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {sprawl, crown}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=sprawl` (the starter's "anything unrecognised is the published default" rule). A
scripted policy seated as a champion is a failure state.

### The split: a sparse plan over a dense deterministic captain

The idea's policy interface is "one move per tick". Taken literally with an LLM in the loop it does
not close: **240 turns × 4 seats is 960 calls; at even 3 s a call that is 2880 s of wall clock
against a 720 s budget — a factor of four over, before a single retry.** So the interface is split
along the line the game itself already has:

- The **LLM decides the plan**, once every `directiveEvery = 8` turns: 30 plans per seat per episode.
  One plan is a five-field object plus a spectator note (§Reply schema) — an intent, a target cell, a
  crown reserve, a city policy, and how much of the next eight turns goes to scouting.
- The **deterministic captain compiles that plan into exactly one legal move per turn**, every turn,
  from **the seat's own fogged view**. It is a pure function of `(view, plan, seat)` with no
  randomness and no network, it runs in microseconds, and **the browser runs the identical Nim code**
  — which is why the replay carries 120 plans rather than 960 moves.

The LLM therefore plays the layer that decides generals.io games (where to push, when to stop
expanding, when to go hunting, how much to leave on the crown) and the captain plays the layer that
is pathfinding.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/gen-generals-io/anthropic_api_key` — the
hive 2026-08-23 scar), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag on the policies: the player pod makes no LLM call.

`src/generals/llm.nim` is `src/ctf/llm.nim`, forked with **no behaviour change**:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (via `readCogameUri`) → **none**, in which case the
  client is `disabled = true` and every directive turn falls back instantly with no network wait, so
  offline certification finishes in seconds.
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 700`. **No `output_config.effort`** when the model string contains `haiku` or
  `4-5`. Bedrock bodies carry `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (outermost balanced
  `{…}`, fence-tolerant, with the first-brace..last-brace rescue) and rune-boundary truncation
  (`runeLen` / `runeSubStr`) kept unchanged.

### Cadence, batching, and the wall-clock arithmetic

At each directive turn the server builds **every living seat's** request body and issues them as
**ONE PARALLEL BATCH** — `client.curl.makeRequests(batch, deadlineMs div 1000)`, the shape of the
starter's `decide.turn` (`src/ctf/decide.nim:394-428`). Seats are **never** queried sequentially:
this is a simultaneous-decision game and serial calls would quadruple the wall clock for nothing. At
most 4 calls in flight; at most `4 × 30 × 2 = 240` calls per episode including retries. Scripted
seats compute locally, instantly, and consume no request; eliminated seats are dropped from the batch
the turn after they die, which is why the worst case below is an over-estimate.

```
attempt1Ms                          7.0 s   (whole seconds: sim_config.validate rejects anything
retryMs                             3.0 s    else, because curl's CURLOPT_TIMEOUT is second-grained)
turnBudgetMs                       11.0 s   (monotonic deadline around the whole directive turn;
                                             attempt1Ms + retryMs = 10 s <= 11 s, which validate checks)
turnSpacingMs                       9.0 s   -> 4 seats x 60/9 = 26.7 req/min  (sidecar cap: 30)

30 directive turns x max(spacing 9 s, budget 11 s), absolute worst  = 330 s
   typical (haiku answers in ~3-4 s, so the spacing floor dominates)= 270 s
240 turns of integer sim + four captains, fastMode                  =   2 s
lobby / connect wait (typical 12 s; cap lobbyJoinTimeoutTicks 2400) =  12 s   (cap: 100 s)
gameOverTicks hold + results + replay write (retrying uploader)     =  20 s
                                                                    -------
typical total                                                       = 304 s   < 720 s
absolute worst case (330 + 2 + 100 + 20)                            = 452 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                             = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                               = 1200 s
```

**720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_gen_manifest.nim` asserts it.**

**Rate guard.** `turnSpacingMs` pins the steady state at 26.7 req/min, but a directive turn in which
all four seats retry issues 8 requests. The engine keeps a **rolling 60 s request counter**: if
issuing the next batch would push the trailing-60 s count above **28**, the seats that would exceed
it skip the call for that turn and take the `sprawl` plan with `cause = "rate_guard"`. Bounded,
logged, never a sleep on the critical path (the raid round 2 sidecar-throttle scar).

**Budget guard (settle early rather than overrun).** At the start of each directive turn, if
`elapsed + 2 * (turnSpacingSeconds + turnBudgetSeconds) > wallClockBudgetSeconds` (a 40 s reserve at
the shipped settings), the LLM is switched off for **every remaining directive turn**, all seats
finish on the scripted layer at microseconds per turn, and the episode ends `complete` rather than
`deadline`. A `budget_guard` record names the turn it fired.

`fastMode: true` in every variant: seats send no per-tick inputs (the server computes every move), so
the Sprite v1 Ready-packet dead-reckoning hazard `docs/PROTOCOL.md` warns about cannot arise here.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turnBudgetMs` monotonic deadline, the rate
guard, `lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the serve thread
(which runs independently of the game loop, so an 11 s LLM stall can neither drop a connection nor
stall `/healthz`), the 660 s engine stop, and ctf's `gameOverTicks` hold before exit.

On a seat's **timeout, transport error or parse failure**: **retry once** in the next batch (a
`throttled` failure with no other candidate model **skips the retry outright** — it cannot land — and
fails fast to the scripted layer for that turn, the starter's behaviour, kept). On the second failure
that seat's plan for that turn becomes the **`sprawl`** scripted plan, computed inside the game by
**the same proc the `sprawl` baseline uses** — imported, never duplicated, so the fallback and the
filler cannot drift — and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns[s]` counts them.

**No failure mode leaves a seat without a move.** The captain always has a plan: this turn's, else
last turn's, else `sprawl`'s (the starter's `repairMissingOrders` ladder, kept). Turn 0's default
before any reply lands is `sprawl`'s. A seat with no legal move (every tile at 1 army, or boxed in)
emits nothing and `passes[s] += 1` — a legal, recorded outcome, never a stall.

**How the episode settles early.** `conquest` ends it the turn the third crown falls; the budget
guard converts a slow provider into a scripted finish rather than an overrun; the 660 s stop settles
with the real ladder and writes every artifact. There is no path on which the engine waits for
something that may not come.

### Per-seat observation: exactly what is visible and what is hidden

**This is a fog-of-war game and the fog is the point.** A seat sees a cell if and only if it **owns
that cell** or the cell is **one of the 8 neighbours (Chebyshev distance 1) of a cell it owns**.
Nothing else widens vision — owning a city or a crown does not grant a bigger radius, and there are
no scouts-as-units. `fullyObservable` is **false** in every variant.

A cell is in exactly one of three states for a seat, and this is the complete list of what each
reports:

| State | Reports |
|---|---|
| **Visible** (owned, or touching an owned cell) | `kind` (`plain` / `mountain` / `city` / `general`), `owner` (an alias or `neutral`) and the **exact `army`**, all current as of the end of last turn. |
| **Remembered** (`seenTurn >= 0` but not visible now) | the `kind` and the `owner` **as of `seenTurn`**, plus `seenTurn` itself. `army` is reported as **`null`** — never a stale number, never an estimate. A remembered enemy general therefore stays on the map as a known location with an unknown garrison, which is exactly the hunt the idea describes. |
| **Unknown** (`seenTurn == -1`) | the single character `?` in every layer and **no fields at all**. Not the kind, not whether it is a mountain, not whether anything is there. |

**Public even under fog — and deliberately so:** each seat's `land`, `army`, `cities` and `alive` are
in every seat's observation, every turn, for every seat. That is generals.io's own rule (its
scoreboard is public) and it is what makes the fog interesting rather than merely dark: you always
know who is winning and by how much; you never know where they are. It is also the anti-snowball
signal a three-way endgame needs.

**Hidden from a seat — the complete list:**

- Every rival's **plan** for the turn being decided (all four are decided simultaneously) **and for
  every past turn**. A plan is intent, not a game-state fact; a rival's *moves* are visible where the
  fog allows, its *reasoning* never is.
- Every rival's `note` — ever. `note` is spectator-only: it reaches the match feed and the replay and
  is never shown to another seat.
- The `army`, `owner` and `kind` of every cell the seat cannot currently see, beyond the memory rule
  above.
- Every seat's `PLAYER_PROMPT`, and the identity of any policy: real player and policy names never
  reach a prompt or an observation. Only `RED-alpha` / `BLUE-alpha` / `GREEN-alpha` / `YELLOW-alpha`.
- The episode **seed** and the `mapRng` state — which here also hides the board's symmetry-derived
  layout of the quadrants a seat has not walked into.
- Any seat's fallback or latency statistics.

**There is no inter-seat channel of any kind.** No chat, no radio, no `say`, no emote. See §The game
→ seats for why: it is the structural answer to the idea's collusion note.

The observation is built server-side from `view(s)` — the *same* structure the captain compiles from,
so a seat's model and its captain never disagree about what is known — appended to the user message,
and mirrored verbatim into the replay's `directive` chat record, so the replay explains every
decision. It is **bounded independently of how much land is alive**. Three ASCII layers, `boardH`
lines of `boardW` characters each, plus bounded structured blocks:

```json
{
  "you": "RED-alpha", "corner": "top-left",
  "turn": 96, "of": 240, "directive_turn": 12, "of_directives": 30,
  "growth_in": 4, "growth_every": 25,
  "board": {
    "w": 16, "h": 10,
    "terrain": ["^.....o.???????.", ".*..............", "… 10 lines …"],
    "owner":   ["RRRR...b??????..", "… 10 lines …"],
    "sight":   ["++++--?????????-", "… 10 lines …"],
    "legend": {
      "terrain": ". plain, ^ mountain, o city, * general, ? never seen",
      "owner":   ". neutral, R/B/G/Y the owner NOW (visible cells), r/b/g/y the owner WHEN LAST SEEN (remembered cells), ? never seen",
      "sight":   "+ visible this turn, - remembered (army unknown), ? never seen"
    }
  },
  "your_general": {"cell": [1, 1], "army": 96, "threatened": false},
  "armies": [
    {"cell": [4, 2], "army": 54, "owner": "RED-alpha", "kind": "plain"},
    {"cell": [6, 0], "army": 40, "owner": "neutral",   "kind": "city"},
    "… every VISIBLE cell with army >= 1, largest first, at most 40 …"
  ],
  "armies_omitted": 0,
  "known_generals": [
    {"owner": "BLUE-alpha", "cell": [12, 1], "seen_turn": 88, "visible_now": false}
  ],
  "known_cities": [
    {"cell": [6, 0], "owner": "neutral", "army": 40, "seen_turn": 96, "visible_now": true},
    "… at most 8, nearest first …"
  ],
  "standing": [
    {"who": "RED-alpha",    "land": 31, "army": 210, "cities": 1, "alive": true},
    {"who": "BLUE-alpha",   "land": 27, "army": 188, "cities": 2, "alive": true},
    {"who": "GREEN-alpha",  "land": 0,  "army": 0,   "cities": 0, "alive": false, "out_turn": 71, "out_to": "BLUE-alpha"},
    {"who": "YELLOW-alpha", "land": 34, "army": 156, "cities": 0, "alive": true}
  ],
  "fog": {"unknown_cells": 61, "frontier": [[7, 4], [8, 6], "… at most 8 …"]},
  "your_last_plan": {"intent": "expand", "target": [7, 4], "reserve": 0,
                     "cities": "cheap", "scouts": 1},
  "how_it_went": "8 moves: claimed 5 tiles, broke no city, lost 2 tiles to BLUE at (9,3); your crown holds 96"
}
```

Field rules. `armies` is capped at the **40 largest** visible army cells (ties by lowest cell index)
with `armies_omitted` giving the remainder; `known_generals` is at most 3 (one per rival);
`known_cities` at most 8, nearest first by BFS distance, with `cities_omitted`; `fog.frontier` is at
most 8 cells — the visible cells that touch an unknown cell, nearest to the seat's largest stack
first. `how_it_went` is generated by the engine, never by a model, and is capped at **240 runes**.
Every count is an integer; there are no floats anywhere in the observation. On 16 × 10 the whole
object is ≈ 2.2 KB.

### Reply schema and per-field caps

The LLM must return this object; **the scripted baselines produce the identical shape** through the
identical validator, which is what makes the bounded-orders test in §Tests meaningful.

```json
{"intent": "attack",
 "target": [12, 1],
 "reserve": 20,
 "cities": "cheap",
 "scouts": 1,
 "note": "blue's crown is at 12,1 and they just spent 60 on a city - going now"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `intent` | string | **≤ 10 runes**; enum `expand` \| `gather` \| `attack` \| `defend` \| `scout` \| `raid` | lower-cased, `-`/space → `_`; still unknown → keep last turn's, else `expand` |
| `target` | `[int,int]` or `null` | each component clamped to `[0, boardW-1]` / `[0, boardH-1]`; an `{"x":…,"y":…}` object accepted | missing / unparseable → `null` (the captain picks its own target) |
| `reserve` | integer | **0 … 999**, clamped; numeric strings accepted | missing / non-finite → keep last turn's, else `0` |
| `cities` | string | **≤ 8 runes**; enum `never` \| `cheap` \| `always` | unknown → `cheap` |
| `scouts` | integer | **0 … 3**, clamped; numeric strings accepted | missing / non-finite → keep last turn's, else `1` |
| `note` | string | **≤ 160 runes** (`MaxNoteRunes`), **spectator-only** — feed + replay, never shown to another seat | truncated to 160 **runes**; newlines collapse to spaces (`sanitizeNote`) |
| whole reply | bytes | **≤ 4096** read from the provider before parsing | over-long is truncated then parsed |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration | truncated, never rejected; never written to the replay or results |

Two further caps on strings that reach the replay: `register.policy` **≤ 48 runes**
(`MaxPolicyLabelRunes`, the starter's value, `src/ctf/sim_types.nim:796`) and any recorded error text
(`fallback.detail`, `results.stopDetail`) **≤ 200 runes** (`MaxFallbackDetailRunes`).

**Truncation is on RUNE (Unicode codepoint) boundaries, never bytes** — the starter's `truncateRunes`
(`runeLen` / `runeSubStr`). Slicing a `string` by byte index on any path to the replay is forbidden.
A byte-truncated multi-byte character is exactly the bug that makes replay bytes render in a browser
but fail a strict parser; §Tests pins it with a 4-byte emoji sitting on every cap.

**Parsing is tolerant** (the starter's `parseSquadDirective`, retargeted): strip markdown fences; take
the outermost balanced `{…}` if the model prefixed prose; accept numeric strings; normalise enum case
and separators. **Unknown top-level keys are ignored. A reply with a valid `note` and no usable field
is usable** — the seat keeps its current plan and the note reaches the feed. Only when **no** JSON
object at all can be recovered do the retry and then the fallback fire. Every repaired field is
counted in `results.directivesRejected[s]` and reported nowhere to the model except through the
effect it has.

### System prompt (fixed; identical for both champions)

Sent as the system message.

```
You command ONE ARMY on a 16 by 10 grid in a four-way war. Three other
commanders are doing the same. You cannot talk to them and you cannot see
their plans. Nobody knows who anybody is.

WHAT YOU CAN SEE
You see a tile only if you OWN it or it TOUCHES one of your tiles (all
eight directions). Everything else is fog.
- A tile you have seen before is shown from MEMORY: the terrain is what it
  was when you last looked, the owner is who held it THEN, and the army on
  it is UNKNOWN.
- A tile you have never seen is "?". You do not know what is there.
- Land, army, city counts and who is still alive are PUBLIC for everyone,
  every turn. You always know how big your rivals are. You never know
  where they are until you look.

THE BOARD
  .  plain        ^  mountain (impassable)
  o  city         *  general (a crown)
Your crown is your life. Whoever captures it takes EVERY TILE YOU OWN and
every army on them (halved), turns your crown into a city of theirs, and
you are out of the game.

THE RULES
- One move per turn. A move sends armies from a tile you own to a touching
  tile (up, down, left or right). A tile always keeps at least 1 army.
- Onto your own tile: the armies add up.
- Onto a neutral or enemy tile: if you send MORE than the army sitting
  there, you take the tile and the difference stays on it. If you send the
  same or less, the tile keeps the difference and stays theirs.
- Empty plains hold 0 army, so claiming land is nearly free. A neutral
  city holds 40 and is the only real toll on the board.
- GROWTH: every city and crown you own gains +1 army EVERY TURN. Every
  tile you own gains +1 army every 25 turns. Neutral land never grows.
  Land is production: 40 tiles is 40 free armies every 25 turns.
- All four commanders move in the same turn. Priority rotates every turn,
  so nobody has a standing advantage.

HOW YOU PLAY
You do NOT type moves. Every 8 turns you send ONE plan object and a
deterministic captain executes it, one move a turn, for the next 8 turns:
it walks your stacks along shortest paths, claims land, breaks cities,
keeps your reserve sitting on your crown, and spends the turns you allot
to walking into the fog.

WINNING
Last crown standing wins outright. If the clock runs out at turn 240 with
more than one alive, the ranking is: still alive, then who survived
longest, then most land, then biggest army, then most cities.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with {
and end with }. No prose, no markdown, no code fences.
{"intent":"expand|gather|attack|defend|scout|raid",
 "target":[x,y] or null,          where the effort aims
 "reserve":0,                     armies left sitting on your crown, 0-999
 "cities":"never|cheap|always",   when to spend a stack on a neutral city
 "scouts":1,                      how many of every 4 turns go scouting, 0-3
 "note":"<=160 chars for the audience watching the replay - no rival ever
         sees it"}

WHAT THE INTENTS DO
expand - your biggest stack walks to the nearest unclaimed land and takes
         it, preferring land that already touches two of your tiles.
gather - armies walk to your biggest stack, building one hammer.
attack - your biggest stack walks at `target`; with no target, at the
         nearest enemy tile you can see, else the nearest you remember.
defend - armies walk home to the crown and retake the tiles beside it.
scout  - a small party (at most 8 armies) walks into the nearest fog.
raid   - your biggest stack walks at the nearest crown you have SEEN,
         routing around visible enemy stacks bigger than itself.
Whatever the intent, if an enemy stack at least as big as your crown's
garrison appears within two tiles of your crown, the captain comes home
for six turns. You do not have to ask for that.
```

**User message** = the seat's `PLAYER_PROMPT` under the starter's "GUIDANCE FROM YOUR OPERATOR"
heading (`operatorBlock`), a blank line, then the observation JSON above.

### Champion #1 — `gen-generals-io-landgrab` (owner **daveey**), `PLAYER_PROMPT`

```
Land is the only thing that compounds. Take it first, fight later.
Turns 0-56: intent "expand", target null, reserve 0, cities "cheap",
scouts 1. Never set reserve above 0 in this phase - armies sitting on your
crown are armies not claiming tiles, and an empty plain costs one army
where an enemy tile costs its whole garrison.
Watch "standing" every single plan. It is public and it is the truth. If
your land is the largest of the living, keep expanding; you are winning
the only race that pays every 25 turns.
Break a city as soon as your biggest visible stack is over 90: 40 armies
buys a tile that prints one army a turn forever, and by turn 200 that is
worth more than the 40 tiles you could have claimed instead. Set cities
"always" the first time your army total passes 150, and back to "cheap"
once you hold two.
From turn ~120 on, set scouts 2 for one plan every time "unknown_cells"
is above 40. You cannot win the endgame without knowing where at least one
crown is, and a scout costs 8 armies.
Set intent "attack" with target on the nearest enemy tile only when your
land lead is 10 or more, or when someone else has just eaten a crown - the
"standing" line where a rival's land doubles in one plan is that event.
Set intent "defend" the moment "your_general" reports threatened true, and
keep it there for two plans. Losing your crown loses everything you built;
losing five tiles costs five armies every 25 turns.
```

### Champion #2 — `gen-generals-io-regicide` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
One crown is worth thirty tiles. Find one, then take it.
Turns 0-32: intent "expand", reserve 0, cities "never", scouts 2. You are
buying map knowledge, not land. Two scouting turns in four is expensive
and it is the whole plan - a crown you have seen never disappears from
"known_generals", and every plan after this one is cheaper for it.
The moment "known_generals" is non-empty: intent "raid", target that
crown's cell, scouts 0, cities "never", reserve 10. Do not stop to take
land on the way; the captain routes you round stacks bigger than yours.
Read the target's owner in "standing" before you commit: if their army is
more than double yours, switch to "gather" for one plan to build the
hammer, then raid. A raid that arrives 20 armies short hands them your
whole stack.
If two crowns are known, go for the one whose owner has the SMALLER army,
even if it is further. You are not looking for a fair fight, you are
looking for an inheritance.
If you take a crown, immediately set intent "expand", cities "always",
reserve 40 and scouts 0 for two plans: you have just inherited land you
have never seen and armies at half strength, and the other survivors can
read exactly what happened in the public standing. Consolidate before you
hunt again.
Set intent "defend" whenever "your_general" reports threatened true, and
raise reserve to 40 for the rest of the game afterwards. A hunter who
loses their own crown finishes last.
```

### The captain (deterministic, shared by every policy)

`src/generals/captain.nim`, forked from `src/ctf/control.nim` (directive → per-tick actuation),
retargeted from pixel steering to a single discrete move. It runs once per living seat per turn and
is the **only** producer of moves. **There is no randomness in it at all, and it reads only
`view(s)`** — the exact structure of §observation, never the true board.

`path(from, goal, seat, mode)` is a breadth-first search, 4-connected, over `view(s)`: **known
mountains are impassable; unknown cells are passable at cost 2; every other cell costs 1**; in
`raid` mode a cell orthogonally adjacent to a currently-visible enemy cell whose army ≥ the moving
amount costs **+8**. Neighbours are expanded in the fixed order `N, E, S, W`, so the path is unique;
ties break by lowest cell index. Flow fields are cached per `(goal, seat)` and recomputed at most
once per turn per distinct goal.

A **mission** is `(kind, source, path, amount, stepsLeft)`. `missionMaxSteps` = **12**. Per living
seat, once per turn, in this order:

1. **No material.** If the seat owns no cell with `army >= 2` → emit nothing, `passes[s] += 1`.
2. **Threat override.** If any currently-visible cell within Chebyshev 2 of the seat's general is
   owned by another seat and has `army >= army(general)`, discard the current mission and set
   `mission = Gather(goal = general)` with `stepsLeft = 6`. This override re-arms every turn the
   threat is visible and cannot be switched off by a plan; it is announced in the system prompt so no
   commander is surprised by it.
3. **Continue.** If a mission exists, `stepsLeft > 0`, and its next step is legal against the current
   view (source owned, `army(source) >= 2`, target not a known mountain and on the board) → emit it,
   `stepsLeft -= 1`, and advance `source` to the target cell so the stack keeps walking. Done.
4. **Scout slot.** Otherwise, if `turn mod 4 < directive.scouts` and at least one unknown cell is
   reachable → `mission = Scout`: `source` = the owned cell with `army >= 2` whose BFS distance to
   the nearest unknown cell is smallest (ties: larger army, then lowest cell index); `goal` = that
   unknown cell; `amount = min(scoutArmy (8), army(source) - 1)`. This is how `scouts` is spent: it
   is a share of turns, not a number of units, which is what makes it exactly implementable with one
   move per turn.
5. **City override.** Otherwise, if `directive.cities != "never"`, let `S` be the owned cell with the
   largest army and `C` the nearest **known** neutral city within BFS 6 of `S` whose remembered or
   visible army is `cA`. Take the mission `Attack(source = S, goal = C)` when
   `cities == "always"` and `army(S) - 1 - reserveIfCrown(S) > cA`, or when `cities == "cheap"` and
   `army(S) - 1 - reserveIfCrown(S) > 2 * cA`. (A remembered city's army is its last-seen value; if
   it has since been taken the move simply fails the arithmetic on arrival and the mission is
   re-picked next turn.)
6. **Intent mission.** Otherwise, by `directive.intent`, with `S` = the owned cell with the largest
   army that is legal as a source (ties by lowest cell index):
   - `expand` — `goal` = the nearest cell that is not owned by this seat and is either an unknown
     cell or a known `plain` with `army == 0`; among equal-distance candidates prefer one
     orthogonally adjacent to ≥ 2 of the seat's cells, then lowest cell index.
   - `gather` — `goal` = the seat's largest-army cell; `S` = its **second** largest-army cell. If the
     seat owns fewer than two cells with `army >= 2`, fall through to `expand`.
   - `attack` — `goal` = `directive.target` when it is set and is not a known mountain; else the
     nearest currently-visible cell owned by another seat; else the nearest **remembered**
     enemy-owned cell; else fall through to `expand`.
   - `defend` — `goal` = the seat's general; `S` = the largest-army cell that is **not** the general.
     If no visible threat exists and every cell orthogonally adjacent to the general is already the
     seat's, fall through to `expand`.
   - `scout` — as step 4, unconditionally.
   - `raid` — `goal` = the nearest cell in `known_generals` (visible or remembered), path mode
     `raid`. If `known_generals` is empty, fall through to `scout`.
7. **Amount.** `amount = army(source) - 1`, except: a `Scout` mission uses `min(8, army(source) - 1)`;
   and when `source` is the seat's **general**, `amount = army(general) - 1 - directive.reserve`, and
   the mission is only taken at all when that value is ≥ 1. That is the entire meaning of `reserve`,
   and it is exact.
8. **Nothing legal.** If no mission can be formed — no reachable goal, or every candidate move fails
   legality — emit nothing and `passes[s] += 1`.

**The captain never emits:** a move from a cell the seat does not own; `amount < 1` or
`amount > army(source) - 1`; a move off the board or onto a known mountain; more than one move for a
seat in a turn; any move for a seat that is not `alive`; or a move derived from a cell the seat
cannot see (asserted by running the captain against a view with the true board zeroed outside
`visible ∪ remembered`). `tests/test_gen_captain.nim` asserts every one of those.

### Scripted baselines (both shipped as fillers; `sprawl` is also the server-side fallback)

`src/generals/baselines.nim`, the starter's module retargeted. Both emit the **same** plan object an
LLM does, through the same validator, and both are pure functions of **the seat's own fogged view**,
which is what makes the bounded-orders test meaningful and what stops a filler from cheating the fog.
Neither ever writes a `note` — they are the commanders who do not explain themselves. Both are
documented in `docs/RULES.md`.

**`sprawl`** — `PLAYER_SCRIPTED=sprawl`, the certification player, the per-turn fallback, the driver
of a no-show or disconnected seat, and the default. The strong simple generals.io opening, held all
game:

```
intent  = "defend"  if your_general.threatened
        = "expand"  if land < (boardW * boardH) div 4          (40 on 16x10)
        = "attack"  otherwise
target  = the nearest visible enemy-owned cell when intent == "attack", else null
reserve = 0
cities  = "cheap"
scouts  = 1
```

**`crown`** — `PLAYER_SCRIPTED=crown`, the second filler, deliberately different in **shape** so the
ladder gets a spread rather than two versions of one bot: it buys map knowledge early and pays for it
in land.

```
intent  = "defend"  if your_general.threatened
        = "raid"    if known_generals is non-empty
        = "expand"  otherwise
target  = the nearest known general's cell when intent == "raid", else null
reserve = 20
cities  = "never"
scouts  = 2
```

`sprawl` finishes ahead of `crown` at the pinned seed on the `ffa` variant with two seats of each —
40 tiles of production beats a raid that arrives short — and `tests/test_gen_baselines.nim` asserts
it (both `sprawl` seats outrank both `crown` seats). It is a real bar for a champion to clear, and
`crown` is the control that answers "did the LLM actually learn to hunt?".

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/generals/`. The fork is a rename sweep
(`ctf` → `generals`, `CtfError` → `GenError`, `COWLDCTF` → `COWLDGEN`; a CI grep asserts no
`ctf_`/`CTF_` identifier survives outside comment history **and outside the two documented `CTF_WIRE`
alias lines** in §Viewer) plus the changes below. **The same modules compile twice**: natively into
`/bin/gen-generals-io` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/generals/server.nim` | **fork**, four named edits below | mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, `/reward`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop, the bounded post-artifact shutdown grace |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/generals/` | **fork** (magic + game name only: `COWLDCTF` → **`COWLDGEN`**) | the whole replay codec, keyframes (`ReplayKeyframeTicks` 100), `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/generals/` (`control.nim` → `captain.nim`) | **fork**, retargeted not rewritten | the parallel batch, the two whole-second deadlines, `turnSpacingMs`, the budget guard, `throttled` fail-fast, tolerant parsing, rune caps, `repairMissingOrders`, the BFS/flow-field cache |
| `src/ctf/sim_state.nim` → `src/generals/sim_state.nim` | **fork** | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/generals/roster.nim` | **fork**, one named edit below | join/auth/identities/`IdentityNames`/**`cogAlias` untouched**/the results JSON builder |
| `src/ctf/events.nim` → `src/generals/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/generals/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline, the `lead` series — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/generals/global.nim` | **fork**, three named edits below | the sprite/object pools, the pixie compositor, the FX families, the baked-floor path |
| `src/ctf/sim_types.nim` → `src/generals/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), the flatty wire types (field order sacred), `MaxNoteRunes = 160`, `MaxPolicyLabelRunes = 48`, `MaxFallbackDetailRunes = 200`, `MaxPromptRunes = 4000`, `Team` (all four members active), `teamText`, `TargetFps`/`ReplayFps` |
| `src/ctf/sim_config.nim` → `src/generals/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, `validate` (incl. the whole-second and `attempt1Ms + retryMs <= turnBudgetMs` checks at `src/ctf/sim_config.nim:688-713`) |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf.nim` → `src/gen_generals_io.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so every seed-derived draw follows the final seed |
| `src/paintball_player.nim` → `src/gen_generals_io_player.nim` | **fork** | the thin seat registrar (§Server) |
| `client/chrome_common.js` | **byte-for-byte** | §Viewer |
| `client/broadcast_core.js`, `client/replay_broadcast.html`, `client/league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/gen_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix (line 20) and the buildx / `--platform linux/amd64` handling (lines 42-55) |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*` (incl. `nes-pixel.ttf`), `data/soldier_{red,blue,green,yellow}.png`, `data/soldier_{red,blue,green,yellow}_front.png`, `data/soldier_{red,blue,green,yellow}_crown.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*,blue_*,green_*,yellow_*}.webp` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, **pixel-space
shadowcast fog and the first-person PIP** (this game's fog is an integer set, not a raycast), spray
cans, floor paint, the paint grid and the paint buff, King of the Hill and `hillTicks`, the
`resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the barrage, med kits,
shields, cardboard barriers, puddles, trenches, perks, handicaps, hit points, lives, respawns and
kills (nothing here is shot), shouts-as-cog-speech, the achievements catalog, campaign mode,
`maxGames > 1` side-swapping, multi-cog squads (`cogsPerTeam > 1`), and **all of the pixel-space map
machinery**: `arena.nim`'s per-pixel wall masks and pixel queries, `map_art.nim`'s procedural arena
bake, `mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`, `tools/map_editor*.nim`,
`tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `docs/pool-review.html`. The board here is a
16 × 10 integer grid generated by the formula in §The game; every one of those is a config surface
the generals rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `spraycan*`, `crew`, `rig_real/`) — but **not** the four crown
sprites, which this game uses for its generals.

### New modules

- `src/generals/board.nim` — the seeded four-fold-symmetric generator of §The game, the
  kind/owner/army arrays, cell↔index helpers, the mirror orbit, the connectivity repair, and BFS +
  the per-turn flow-field cache. Pure integer.
- `src/generals/vision.nim` — `visible(s)`, the `seenTurn` / `kindSeen` / `ownerSeen` memory arrays,
  and `view(s)` — the single struct both the observation builder and the captain read, so a seat's
  model and its captain can never disagree about what is known.
- `src/generals/resolve.nim` — steps 3–5 of §Turn and tick structure, in that order, including the
  rotated priority, the collision arithmetic and the crown-capture inheritance.
- `src/generals/scoring.nim` — the rank ladder, `scores`, `win`, `winner`, and the per-seat counters.
- `src/generals/captain.nim` — the compiler of §Decisions.
- `src/generals/sim.nim` — the step loop; imports and re-exports the sim modules as the starter's
  does, so `import generals/sim` sees everything.

### The four named edits to `server.nim`

1. **Directive turn.** The starter's turn-boundary block, with `turnTicks` replaced by
   `directiveEvery` and the batch built over **living** seats instead of the starter's squad count,
   plus the structured-plan input-record write.
2. **Registration interception.** A player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed
   as registration and is **not** applied as a bubble and **not** written to the replay chat stream;
   the server writes a redacted `register` record instead (policy label and kind, never the prompt).
   The starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is
   kept verbatim (the paintball round-3 scar, where a champion played the baseline for a whole
   episode). Any other chat text from a seat is dropped — this game has no inter-seat channel.
3. **Wall-clock stop.** The starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration, kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`, **and
   writing the load-bearing `stop` record** (the particle-worlds r2 scar: the stop is a wall-clock
   fact no re-simulation can derive, so it is recorded and applied on both sides by one proc,
   `sim.applyWallClockStop`).
4. **Conquest check.** After step 8, the `conquest` end rule of §End conditions.

### The one named edit to `roster.nim`

`squadResultsJson` becomes `generalsResultsJson` — four entries in every seat-indexed array, keys
exactly as §Server lists them. `cogAlias`, `slotIdentityIndex`, `shoutIdentityName` and
`IdentityNames` are **untouched**, so the two-name-space rule and its inherited test apply with no
further change.

### The three named edits to `global.nim`

1. **The board is baked floor art plus per-cell chips, not sprites.** At reset, pixie composites one
   board bitmap: the tiled `data/arena_floor.png` darkened 18 %, a 1 px chalk grid on the cell
   lattice, and mountains stamped from `client/art/walls/wall_h.jpg` / `wall_v.jpg` as rough blocks.
   Only the mutable layers (ownership tint, army numerals, city and crown chips, the fog wash) are
   drawn per frame, so a 160-cell board is one blit plus at most 160 small draws. This is the same
   path the starter uses to bake endzone paint.
2. **Fog is `#lightpool`.** The starter already ships a full-stage `#lightpool` element and its
   compositing rule; the **fog lens** (§Viewer) drives it: with a seat selected, every cell outside
   that seat's `visible` set is washed to 55 % and every never-seen cell is stippled. With `ALL`
   selected the element is transparent and the spectator sees the whole board.
3. **Cell chips.** `rig_art.nim`'s compositor bakes, at load: a neutral city keep and an owned city
   keep in each of the four team tints, a crown chip in each tint from
   `data/soldier_<team>_crown.png`, and a 5-step ownership tint ramp — 4 × (2 + 1) + 4 × 5 = 32
   pre-baked chips. Drawing a frame is 160 blits plus the numerals. No text is ever drawn at a
   negative coordinate: every numeral's reserved band is measured in the font it is drawn in (the
   cogchemists 2026-08-24 rule), which is why `--strict-text-bounds` stays on in CI.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cells, armies, land counts, BFS distances, ranks. There is
no floating point anywhere in `board.nim`, `vision.nim`, `resolve.nim`, `scoring.nim`, `captain.nim`,
`baselines.nim` or `sim.nim`, and a CI grep over exactly those files for `float|sqrt|hypot|sin|cos`
enforces it. `results.scores` (0.0 / 1/3 / 2/3 / 1.0) is produced at serialisation time from the
integer rank and never enters the sim. Nim's `int` is 32-bit under `--cpu:wasm32`; per-cell armies are
`int32` with a guard at 100 000, and episode totals (`army[s]`, `tilesTaken`) are `int64`.

**One RNG stream**, `mapRng`, derived from `seed`, consumed **only** by the map generator at reset and
never again — so nothing a policy does can steer a draw, and the map is a pure function of
`(seed, boardW, boardH, mountainPct, cityCount, cityArmy)`. That is the idea's "maps seeded" integrity
pin, and `tests/test_gen_board.nim` asserts it by generating from the same seed after different play.

The seed is randomised in `src/gen_generals_io.nim` **before** `config.update` (the starter's rule),
recorded in the replay config and in `results.seed`.

### Determinism, native ↔ wasm

The mechanism is ctf's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDGEN`** replay: magic + format version + game name/version header, the
   **resolved config JSON**, then the record stream — joins (name, slot, token), leaves, the
   **plan input records**, the presentation chat records, and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/gen_replay.nim` — which imports the **same**
   `src/generals/sim.nim` — through the pinned `emscripten/emsdk` + nimby container in
   `Dockerfile.replay-viewer`.
3. In the browser, `gen_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then `gen_frame`
   re-steps the sim — **re-running the four captains from the recorded plans, including each seat's
   fog and memory** — and compares `sim.gameHash()` against the recorded hash **every tick**
   (`checkReplayHash`). A single divergent bit is caught at the tick it happens and surfaced as
   `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: `turn`; per cell in ascending index
   `(kind, owner, army)`; per seat in ascending index `(alive, eliminatedTurn, eliminatedBy, land,
   army, cities, generalsCaptured, tilesTaken, tilesLost, movesMade, invalidMoves, passes)`; per seat
   the **memory digest** `(count of seen cells, xor of (cellIndex * 31 + kindSeen))` — the fog is
   game state and a divergence in it must be caught; and each seat's **structured plan**. The `note`,
   `source`, `latency_ms` and every policy label are **excluded** — the starter's rule that nothing a
   commander *says* may move the hash chain.

**The sim guard `checkGeneralsInvariants()`** (step 7), evaluated every turn: every cell's `army >= 0`
and `<= 100000`; a `mountain` cell has `owner == none` and `army == 0`; a cell with `owner == none`
and `kind == plain` has `army == 0`; every living seat owns exactly one `general` cell and it is the
cell recorded in `generalCell[s]`; a dead seat owns nothing; `land[s]` equals the counted cells;
`army[s]` equals the summed armies; `cities[s]` equals the counted owned `city` cells;
`sum(land) <= boardW * boardH`; `turn <= maxTurns`; the board's **mountain layout is still four-fold
symmetric** (kinds only — ownership and armies diverge the moment anyone moves); and
`visible[s] ⊆ seen[s]`. A trip raises `GenGuardError` → `fault`/`sim_fault`.

**Perf target:** 240 turns of four captains plus resolution in under 2 s on a CI runner;
`tests/test_gen_perf.nim` bounds it at 60 s.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`,
`COGAME_METRICS_URI` out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode;
`COGAME_HOST`/`COGAME_PORT`; player sockets at `/player?slot=<i>&token=<t>` with a 403 on a bad
slot/token.

The certifier's browser probes are served **for real** and registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket —
the lantern 0.1.1 cert probe), `GET /client/global`, the `/global` websocket's first message, and
`/healthz` — all kept answering for a bounded ~20 s grace after artifacts are written (lantern 0.1.3).
Global broadcasts are fire-and-forget so a slow spectator can never stall the episode.

### The player container

`src/gen_generals_io_player.nim` (built to `/bin/gen-generals-io-player`) is the starter's
`src/paintball_player.nim`, forked with the baseline names changed. It reads
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), `PLAYER_PROMPT`, `PLAYER_SCRIPTED`
and `PLAYER_POLICY_LABEL`, dials with bounded retries (240 × 500 ms), and sends **one Sprite v1 chat
message** carrying its registration:

```json
{"type":"register","policy":"<label, <=48 runes>",
 "prompt":"<PLAYER_PROMPT or empty, <=4000 runes>",
 "scripted":"sprawl"|"crown"|null}
```

Registration is **re-sent** 10 times, ~1 s apart, over the first ~10 s of received frames, because
joins are slot-sequential and a seat whose slot is not the next open one is not admitted until the
lower slot has joined (the paintball round-3 scar). It then sends the Sprite v1 Ready packet (`0x85`)
after each received frame — legitimate here because it never sends inputs — and otherwise only
receives. A seat that never registers, or registers with neither field, is `scripted: "sprawl"`. The
receive loop is wrapped in `try/except CatchableError`, re-dials a dropped socket up to 6 times, and
**exits 0 on a dead socket** (the raid 0.1.3 scar: whisky's `receiveMessage` raises on a close frame
and the game's `quit(0)` can outrun the flushed `done` frame, so a naive player exits 1 and fails
certification intermittently). An **eliminated** seat's container keeps receiving frames and exits 0
with everyone else — elimination is a game state, not a disconnection.

### Results document

Written by `sim.generalsResultsJson()` to `COGAME_RESULTS_URI`. It must equal the manifest's
`results_schema` key-for-key — that schema is `additionalProperties: false` and the certifier drops
unknown fields. Adding or removing a key means editing `coworld_manifest_template.json` and
`tools/ci/docker_smoke.sh`'s expected-key set in the same commit. Exactly **29** keys:

```json
{"names":            ["daveey", "daveey-1", "gen-generals-io-sprawl", "gen-generals-io-crown"],
 "aliases":          ["RED-alpha", "BLUE-alpha", "GREEN-alpha", "YELLOW-alpha"],
 "scores":           [1.0, 0.3333333333333333, 0.6666666666666666, 0.0],
 "win":              [true, false, false, false],
 "winner":           0,
 "reason":           "complete",
 "endRule":          "conquest",
 "rank":             [0, 2, 1, 3],
 "land":             [96, 0, 0, 0],
 "army":             [814, 0, 0, 0],
 "cities":           [4, 0, 0, 0],
 "generalsCaptured": [2, 0, 1, 0],
 "eliminatedTurn":   [-1, 187, 203, 96],
 "eliminatedBy":     [-1, 0, 0, 2],
 "tilesTaken":       [141, 62, 88, 31],
 "tilesLost":        [45, 71, 88, 31],
 "movesMade":        [203, 178, 196, 92],
 "invalidMoves":     [1, 6, 3, 2],
 "passes":           [0, 9, 4, 1],
 "turnsPlayed":      203,
 "boardW":           16,
 "boardH":           10,
 "seed":             1734029581,
 "policyKinds":      ["llm", "llm", "scripted", "scripted"],
 "llmTurns":         [30, 24, 0, 0],
 "fallbackTurns":    [0, 1, 0, 0],
 "directivesRejected":[0, 2, 0, 0],
 "deadSeats":        [false, false, false, false],
 "stopDetail":       ""}
```

`tests/test_gen_manifest.nim` asserts the exact key set in both directions. `names` are the **real
policy names** (spectator side); `aliases` carry the in-game names. **All twenty-one seat-indexed
arrays** (`names`, `aliases`, `scores`, `win`, `rank`, `land`, `army`, `cities`, `generalsCaptured`,
`eliminatedTurn`, `eliminatedBy`, `tilesTaken`, `tilesLost`, `movesMade`, `invalidMoves`, `passes`,
`policyKinds`, `llmTurns`, `fallbackTurns`, `directivesRejected`, `deadSeats`) have exactly
`num_agents` = **4** entries — which is what `docker_smoke.sh` cross-checks against `SMOKE_SEATS`.
`eliminatedTurn[s]` and `eliminatedBy[s]` are `-1` for a survivor. `winner` is an integer seat index
or `null` when the top rank is shared.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDGEN`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse.
The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (line 31/57/319).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"gen-generals-io/v1","gameVersion":"1","seed":…,"boardW":16,"boardH":10,"names":[…],
  "aliases":[…],"policyKinds":[…],"turnCount":…,"plans":[…],"fallbacks":N,"results":{…}}` — by
  brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md`
  documents for prod forensics) and decoding the record stream.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.land[]' /tmp/ep.json
  jq -r '[.plans[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  jq -r '[.plans[]|select(.note!="")]|length' /tmp/ep.json
  ```
  Require `protocol == "gen-generals-io/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.land | add > 40` (somebody actually expanded), and the
  champion seats' plans with `source == "llm"` and non-empty `note`s — not all fallbacks — because a
  coworld about hidden-information strategy whose replay contains no strategy is broken even if it is
  green.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDGEN`, format version, `gameName` `gen-generals-io`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `boardW`, `boardH`, `mountainPct`, `cityCount`, `cityArmy`, `maxTurns`, `growthPeriod`, `directiveEvery`, `scoutArmy`, `missionMaxSteps`, `defendTurns`, every LLM timing constant, `players[].name` (**real** names), `slots[]`, `tokens[]`, `fastMode`, `fullyObservable: false` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| plan input records | per directive turn, per living seat: the structured five-field plan — **this game's entire input log**, load-bearing, applied before the turn is stepped |
| chats | `register` / `plan` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

The **board is re-derived** from the seed rather than being a load-bearing record (it is in
`gameHash` from turn 0, so a divergence surfaces immediately), which is why the file stays small: 240
hashes + ≤ 120 plan input records + ≤ 120 plan chat records + the config ≈ **75 KB**.

### Record and event vocabulary

**A. Replay records.** The plan's structured five fields are an **input record** (load-bearing,
re-applied on playback). Everything below is a **chat record**: presentation-only, re-applied into
non-hashed fields, driving the feed and `replay_summary.py` — with the single documented exception of
`stop`.

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `plan` | `turn`, `seat`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, the five plan fields, `note` (≤ 160 runes), `view` (the observation object verbatim) |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `turn`, `endRule` (`wall_clock`) — **the one load-bearing chat record**, applied on both sides by `sim.applyWallClockStop` before that turn's step (the particle-worlds r2 scar) |
| `result` | the full results document, written once at episode end — without it a spectator holding the file reads `results: {}` |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of eleven kinds:**

`phase` `{from,to}`; `growth` `{turn, land:[4], army:[4]}` (every growth beat);
`claim` `{seat, cell, land}` (a neutral plain taken); `citytaken` `{seat, cell, from, cost, cities}`;
`tilelost` `{seat, to, cell, count}` (throttled to one per ordered seat pair per turn);
`stackclash` `{cell, attacker, defender, attackerArmy, defenderArmy, held}` (only when
`min(amount, defence) >= 10`); `generalspotted` `{seat, victim, cell}`;
`generalcaptured` `{seat, victim, cell, landGained, armyGained}`;
`eliminated` `{seat, turn, by}`; `plan` `{seat, intent, note}`;
`end` `{reason, endRule, land:[4], rank:[4], winner}`.

**Beats** — the scrubber markers, and the only kinds the appended game block emits, all bounded by
construction: **`citytaken`** (throttled to the first capture of each city — ≤ 8, ≤ 12 in
`citadels`), **`generalspotted`** (≤ 12: 4 seats × 3 rivals, once per ordered pair),
**`generalcaptured`** (≤ 3), **`end`** (1). At most **28** markers on a 240-turn scrubber. `growth`,
`claim`, `tilelost`, `stackclash`, `eliminated` and `plan` drive the feed and the banners, not the
scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `PhaseChange, Growth, Claim, CityTaken, TileLost, StackClash,
GeneralSpotted, GeneralCaptured, Eliminated, Plan, Fallback` and the mandatory trailing summary row
(`type`, `ticks`, `events`, `gameVersion`) kept.

### The state JSON a viewer reads

One object per presentation frame, from `buildStateJson` — identical live and in replay, and the
**only** thing the renderer reads. The inherited keys are unchanged: `t` (tick), `mt`, `ph`, `lob`,
`sp`, `mx`, `st`, `lp`, `sk`, `ff`, `en`, `mm` (mismatch tick), `bs` (board scale), `teams`, `roster`
(per seat: `s`, `team`, `name` — the **real** policy name, spectator side — `pol`, `col`, `alias`,
`seat`), `events`, `plans`, `lead` (sent once). gen-generals-io adds exactly these:

```json
{"turn": 96, "turns": 240, "growthIn": 4, "growthEvery": 25,
 "w": 16, "h": 10,
 "cells": [{"i": 37, "k": "plain", "o": 0, "a": 54},
           {"i": 38, "k": "city",  "o": -1, "a": 40},
           "… only cells whose kind, owner or army changed since the last frame …"],
 "gen":   [17, 28, 129, 142],
 "alive": [true, true, false, true],
 "stand": {"land": [31, 27, 0, 34], "army": [210, 188, 0, 156], "cities": [1, 2, 0, 0]},
 "out":   [-1, -1, 71, -1],
 "outBy": [-1, -1, 1, -1],
 "plan":  [{"seat": 0, "turn": 96, "intent": "expand", "note": "taking the middle before blue does"},
           {"seat": 1, "turn": 96, "intent": "raid",   "note": ""},
           {"seat": 3, "turn": 96, "intent": "gather", "note": ""}]}
```

`cells` is a **delta** (the full 160-entry array on the first frame and on every keyframe), which is
what keeps a 240-frame state stream small; `i` is always a cell index and `o` is a seat index or `-1`
for neutral. `gen[s]` is seat `s`'s general cell index, or `-1` once captured. **The per-seat fog is
NOT transmitted** — the viewer derives `visible[s] = owned ∪ 8-neighbours(owned)` from `cells` in the
browser, exactly as the sim does, which costs zero replay bytes and cannot drift. `plan` carries the
most recent plan per living seat and is where the feed's commander lines come from.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` **under `game`**, and
`tools/build_replay_viewer.sh` is coworld-ctf's hook — kept, with the `image_tag` literal (line 32)
and the `docker cp` source path (line 57, `/workspace/generals/replay-viewer/dist/.`) changed —
building `Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It
already carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx /
`--platform linux/amd64` handling, and it stays committed **executable** (`coworld build`
hard-requires `os.X_OK`). No `/client/replay` live-server viewer is ever declared to the platform;
the game still serves `/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/gen_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html` by `Dockerfile.replay-viewer`'s marker `sed`)
ALL come from ONE starter: `coworld-ctf`** — which is this repo's own starter. **Never a mixture.**
Splicing one starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23).
coworld-ctf's set is internally consistent and is kept as one piece: the Worker sets
`Module.onRuntimeInitialized`, the module is emitted **non-modularized** as `gen_replay.js`,
`config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang` through `emcc`,
`--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable:
with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and silently corrupt the module's own globals — the
starter's own comment, `replay-viewer/config.nims:35-41`), `-s FILESYSTEM=1`,
`-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_gen_load_replay,_gen_frame,_gen_input,_gen_packet_ptr,
_gen_packet_len,_gen_mismatch_tick,_gen_error_ptr,_gen_error_len,_gen_stage_ptr,_gen_stage_len`; and
`static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './gen_replay.js')` in that order.

`gen_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress buffer
that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `gen_load_replay` re-simulates the whole episode once headlessly (240
  turns of integer work on 160 cells — under a millisecond in wasm), records the per-turn land and
  army counts for all four seats, the elimination turns, the lull spans and the beat turns, then
  resets and renders frame 0. That is what lets the land-lead graph and the scrubber beats draw at
  **full width on the first frame** instead of growing in.
- `gen_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (line 161 of the starter's file) — posted by
the Worker only *after* `ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so
the attribute means "a frame is on the canvas", not "a file was fetched". **On failure the shell sets
`data-replay-error` on `<html>`** with the message, in `showFailure()` (line 8, attribute set at line
20). Both signals are coworld-ctf's own and are inherited **unchanged** — this fork adds neither and
removes neither. The `coworld-replay` postMessage bridge's `ready` is posted from a callback fired
**after** `data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus
`3c11c953`, 2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied BYTE-FOR-BYTE from coworld-ctf.** Not edited, not
  reformatted, not one identifier changed; `tests/test_gen_viewer.nim` pins its sha256 against the
  starter's file. Everything gen-generals-io adds lives in the appended game block. Its `markBeat` /
  `renderBeatMarkers` / `ingestBeats` / `renderClock` / `renderTransport` / `ingestLullSpans` /
  `setVerdict` all remain, and `ingestBeats` ignores kinds it does not know.
  - Its **line 72** reads `var WIRE = window.CTF_WIRE || {}`. Rather than edit a file the pin says
    must be byte-identical, `tools/gen_wire_constants.nim` emits two lines —
    **`window.GEN_WIRE={…};`** then **`window.CTF_WIRE=window.GEN_WIRE;`** — the game's own code reads
    `GEN_WIRE`, and the one aliasing line exists solely to keep `chrome_common.js` untouched.
    `Dockerfile.replay-viewer`'s assertion `grep -q '^window.CTF_WIRE={'` becomes
    `grep -q '^window.GEN_WIRE={'` **and** `grep -q '^window.CTF_WIRE=window.GEN_WIRE;'`, so the
    alias is asserted rather than assumed. Those two lines (the emitter and chrome_common's reader,
    plus `broadcast_core.js:49`'s read, which is retargeted to `GEN_WIRE`) are the **only** places
    `CTF_WIRE` survives, each carries a comment naming this note, and the CI rename grep excludes
    exactly them.
- **`client/replay_broadcast.html` is the starter's page WITH A GAME BLOCK APPENDED** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (line 4276), transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density system are
  untouched; the appended `gen-` block replaces only the *contents* of the scorebug plates, adds the
  fog-lens chip row and the growth bar, and retargets the feed rows, the beat rendering, the momentum
  series and the endcard columns. The splice point is the starter's own documented banner comment at
  line 4344 (`PAINTBALL additions to the inherited coworld-ctf chrome`); **the starter's paintball
  block is removed with the paintball mechanics** and the `gen-` block takes its place, so the page
  carries exactly one game block. A test asserts the starter's byte prefix is intact up to that
  marker and that nothing above it changes.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. It is pinned function-by-function against the starter's text by
  `tests/test_gen_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  **`pushFeed` including its signature** (the cogball 0.1.4 latch scar: a signature drift threw
  mid-replay and latched `static_replay.js` into `failed`), the beat and lull machinery, the endcard
  builder, the speed chips, the `?embed=1` path, and the `teamCol`/`activeTeams`/`teamOf` helpers the
  four-plate scorebug uses. Deleted: every ctf-specific draw call and the FPV pipeline. Added:
  `drawBoard`, `drawCells`, `drawArmies`, `drawCrowns`, `drawFogLens`, `drawGrowthBar`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `attachMinimap(...)` call. **Zoom decision:
    DROPPED.** The board is a fixed 16 × 10 (or 12 × 8) grid with no off-frame area and `relayout()`
    fits it whole at every width including 360 px (see "Legible at 360 px"), so per the pin a fixed
    arena drops `#viewpanel` entirely. `broadcast_core.js` tolerates a missing minimap
    (`pendingMinimap` stays null).
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — there is no
    per-unit point of view here; the fog lens replaces it and lives in the top band.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.squad`, `.pb-tags`, `#pb-regime`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture`, `.hillflip`, `.hillhold`, `.tagout`,
    `.gamestart` and `.gameover` CSS rules — none of those kinds is emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS).
  - **Kept:** `#viewport`, `#stage`, `#board`, **`#lightpool`** (retargeted to the fog wash),
    `#grain`, `#lockerroom` (`#lk-bg`, `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug`
    with `#plates-l`/`#plates-r` (in `.row` mode — the starter's own four-team layout) /`#clock`/
    `#clock-time`/`#clock-caption`, `#bannerlane`, `#killfeed`, `#mmwarn`, **`#transport` in full**
    (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`,
    `#btn-spoilers`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`, `#tick-clock`, `#speedchips`), `#scrub`
    with `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/`#scrub-head`, `#endcard` with
    `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`, and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings. The re-labelings are
therefore enumerated here and enforced by `tests/test_gen_endcard_labels.nim`:

| Starter string | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` | `<span>Commander</span><span>Land</span><span>Army</span><span>Cities</span><span>Crowns</span>` |
| `<span class="fl-cap">Lives left</span>` | `<span class="fl-cap">Land</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` | `<span class="momentum-label">LAND</span>` |
| `<span class="lives-label">Lives</span>` (scorebug plate) | `<span class="land-label">Land</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" | "Raising the standards…" |
| `#clock-caption` "In the locker room" | "Four crowns, one map" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" | "Replay hash mismatch at turn N — showing recorded plans" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline" | "cities / crowns found / crowns taken / winner on the timeline" |

The test greps the built `index.html` and `broadcast_core.js` for a forbidden-vocabulary list —
`Lives`, `LIVES`, `Clstr`, `flag`, `heart`, `paint`, `hopper`, `hill`, `POV`, `spray`, `grenade`,
`med kit`, `kill` — outside comment blocks, and asserts **zero** matches, plus each replacement
present exactly once.

### Transport rules

`relayout()` (`client/replay_broadcast.html:4276-4320`) sets **`--band`** (the measured transport
strip), **`--topband`** (the scorebug strip) and **`--hudscale`** on `:root`, unchanged. **No overlay
sits in the transport band**: the board is laid out between the two bands, and every
gen-generals-io addition (the fog-lens chip row, the growth bar, the feed, the banners) is positioned
inside the board region or in the top band. The **endcard stops at `var(--band)`**
(`#endcard { bottom: var(--band, 0px) }`, the starter's rule at line 1047, kept) so the scrubber stays
clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `genBeat(turn, kind, seat, label)` — named with the `gen` prefix so it
can never be shadowed by the chrome alias block's hoisted `var markBeat` (the tandem 2026-08-23
hoisting trap) — appends
`<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind gen-generals-io emits and no others**: `.beat-marker.citytaken`,
`.beat-marker.generalspotted`, `.beat-marker.generalcaptured`, `.beat-marker.end`. The game block
never calls `chrome_common.js`'s `markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: 12 turns per second** (speed chips `[0.5, 1, 2, 4, 8]`, default 1). An `ffa` replay
is 48 lobby ticks + 240 turns + 72 `gameOverTicks` = 360 ticks ⇒ **30 s of playback**; `blitz` is
23 s. Both comfortably outlast `viewer_smoke.mjs --soak 10`, which needs to observe real advancement
rather than a legitimately-finished replay (the ecos 2026-08-23 scar). Twelve turns a second is also
the tempo at which a human can read this board: one move a turn per seat is four tile changes a
frame, which is followable.

### Readouts

1. **The board**, drawn edge to edge: the baked floor with its chalk grid; mountains as wall-textured
   blocks; neutral cities as grey stone keeps with their **exact garrison numeral** on the roof;
   owned cities as keeps in the owner's colour; generals as a crowned keep using
   `data/soldier_<team>_crown.png`; owned plains tinted in the owner's colour with a 5-step
   brightness ramp by army; neutral plains bare. **Every cell that holds an army shows the exact
   integer** (see "Legible at 360 px" for the one density rule).
2. **The fog lens** — a labelled chip row in the **top band** (never the transport band):
   `ALL · RED · BLUE · GREEN · YELLOW`. `ALL` (default) shows the whole board. Selecting a seat
   drives `#lightpool` to wash every cell that seat cannot currently see to 55 % and to stipple every
   cell it has never seen, so a spectator can watch a raid arrive out of the dark exactly as the
   victim experienced it. The lens is derived in the browser from `cells` (owned ∪ 8-neighbours,
   accumulated for the "never seen" layer), so it costs zero replay bytes and works on any replay.
   Seats that are eliminated grey out in the row.
3. **Scorebug** — four plates, two in `#plates-l` and two in `#plates-r` under the starter's own
   `.plates.row` four-team layout, each with the seat's **real policy name** (spectator side only),
   its in-game alias, its colour chip, **land as the big numeral**, and beneath it `army · cities`. A
   `↯` glyph lights on any seat that has taken a fallback; a `✕` and 40 % opacity mark an eliminated
   seat, with `out t187` in place of the sub-line.
4. **Growth bar** — a labelled strip in the top band showing the 25-turn production cycle as a bar
   with the playhead on it and `GROWTH IN 4` beside it. When it fires, every plate's land numeral
   pulses and a banner reads `GROWTH — every tile +1 · RED +31 BLUE +27 YELLOW +34`.
5. **Clock** — `#clock-time` shows `TURN 96 / 240`; `#clock-caption` shows
   `plan 12/30 · 3 crowns standing · RED leads 34 land`.
6. **Match feed** (`#killfeed`) — plain language, never internal notation: `RED takes the city at
   (6,0) for 40`, `BLUE walks into RED at (9,3) — 54 against 61, RED holds`,
   **`YELLOW SEES BLUE'S CROWN at (12,1)`**, `GREEN claims 4 tiles`, and the commander lines
   `RED-alpha: "taking the middle before blue does"`. The plan `note` appears here and nowhere else;
   this is where a spectator sees the LLM playing.
7. **Banners** (`#bannerlane`) — the three moments that decide the game:
   `RED TAKES BLUE'S CROWN — inherits 24 tiles and 118 armies`, `BLUE IS ELIMINATED (turn 187)`,
   and the growth banner from 4.
8. **Land-lead graph** — the starter's `#momentum` SVG retargeted to **four** cumulative land series
   in team colours, with the nine growth beats ticked on the axis, the elimination turns marked with
   a vertical rule in the victim's colour, and the playhead. Filled from the load-time pre-scan, so
   it draws at full width on the first frame. A green line that stops dead and a red line that jumps
   by 24 in the same turn is the whole story of a crown capture in one glance.
9. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
   30 consecutive turns with no `citytaken`, `generalspotted`, `generalcaptured` or `growth` event,
   from the pre-scan), spoilers switch, tick readout, speed chips, the scrubber with its four beat
   kinds, and `#mmwarn` on a hash mismatch — all the starter's, verbatim.
10. **Endcard** — `GENERALS — daveey TAKES TWO CROWNS`, the four-seat table under the re-mapped
    header (`Commander | Land | Army | Cities | Crowns`) with rank and `out t187` on the eliminated
    rows, a second row of `taken / lost / moves`, and the story line `daveey found blue's crown on
    turn 88 and spent the next hundred turns walking a hammer at it`. It stops at `var(--band)` and
    any seek dismisses it.

### Art

**Real art, from the starter's shipped assets — no placeholders, no solid-colour squares, no
downloads.** The floor is `data/arena_floor.png`, tiled and darkened 18 % with a chalk grid, baked
once at reset by pixie (the path the starter uses for endzone paint). Mountains are stamped from
`client/art/walls/wall_h.jpg` and `wall_v.jpg`; city keeps are baked from the same wall textures
tinted through `data/pallete.png`; crowns are `data/soldier_{red,blue,green,yellow}_crown.png`, which
the starter already copies into the viewer bundle. Ownership tints come from the four team colours
the chrome already knows. Numerals use `data/atlas/nes-pixel.ttf` (tabular, pixel-exact at small
sizes) and labels use `data/font.ttf`. The loading screen is the starter's locker room
(`client/art/lockerroom/bg.jpg` plus the red, blue, green and yellow cog webps — all four already
asserted present by `Dockerfile.replay-viewer`) with the caption re-labelled "Raising the
standards…".

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim. In a 360 × 203 embed `--hudscale` clamps to **0.5**, at which `relayout()` measures
`--topband` ≈ 46 px and `--band` ≈ 38 px, leaving a **360 × 119** board region; a 16 : 10 board
letterboxes to **190 × 119**, i.e. **11.9 px per cell** (`blitz`'s 12 × 8 gives 14.9 px). That is the
binding constraint on this game's chrome, and it is met by four rules, all asserted by
`tests/test_gen_viewer.nim`:

1. **Numerals are always the exact integer** — "10", never "T", never "1.2k". They are drawn in
   `nes-pixel.ttf` at `max(5, floor(cellPx * 0.42))` px, horizontally scaled to fit `cellPx - 2` with
   a floor of 0.55×. At 11.9 px that is a 5 px face: one and two digits render clean, three digits
   render at 0.72× and remain readable as digits. A value needing a scale below 0.55 (five digits,
   which the sim guard makes unreachable) is not drawn on the cell; the `#stacktop` HUD row (rule 3)
   carries it instead.
2. Under `.tiny`, a numeral is drawn only on cells with `army >= 5` and on **every** city and crown
   regardless of army. Below 5 the cell is its tint alone. This removes roughly two thirds of the
   numerals — a freshly claimed plain reads as colour, not as a "1" — and leaves the remaining ones
   room.
3. Under `.tiny`, each plate keeps only `colour chip + name + land`; `army · cities` moves to a
   single `#stacktop` line under the clock reading
   `R 210 · B 188 · Y 156 — biggest stack R 96 at (1,1)`, and the fallback glyph goes inline.
4. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…" in a four-plate row; and under `.tiny` the fog-lens chips drop
   their words to four colour squares plus `ALL`.

All four are sized from `--hudscale`, so nothing is ever drawn outside the canvas and
`--strict-text-bounds` stays on in CI.

---

## Packaging

- **Repo**: `Metta-AI/cogame-gen-generals-io`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `gen-generals-io`; **`game.name` is
  `gen-generals-io`** (hyphenated, matching the slug) so the secret namespace
  `secret://coworld/gen-generals-io/anthropic_api_key`, the page slug, the
  `POST /coworld-league-seeds` body and the docs all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, underscored, because the manifest image placeholder is
  derived from the compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships
  two services / two images; this fork uses the one-image / two-entrypoints shape because the shared
  `docker_smoke.sh` and `policies.json` assume a single image:

  ```yaml
  services:
    gen_generals_io:
      image: coworld-gen-generals-io:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{GEN_GENERALS_IO_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby 0.1.26, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:gen-generals-io
  src/gen_generals_io.nim` → **`/bin/gen-generals-io`**, and the same for
  `src/gen_generals_io_player.nim` → **`/bin/gen-generals-io-player`**. Those two paths are exactly
  `docker_smoke.sh`'s defaults `/bin/${slug}` and `/bin/${slug}-player`, so no `SMOKE_GAME_BIN`
  override is needed. The runtime stage copies both binaries, `data/`, `client/`, `*.json`.
  `CMD ["/bin/gen-generals-io"]`, runtime `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (`emscripten/emsdk:4.0.15` pinned, nimby
  0.1.27 pinned by its sha256, `nimby use 2.2.4`, `nimby --global sync nimby.lock`, the marker
  splices, the whole `test -f` / `grep -q` assertion block) with `WORKDIR /workspace/generals`, the
  entry renamed to `replay-viewer/gen_replay.nim`, the wire-constants assertion changed as §Viewer
  describes, and the asset list swapped to `data/{arena_floor,ascii,pallete}.png`,
  `data/soldier_{red,blue,green,yellow}_front.png`,
  `data/soldier_{red,blue,green,yellow}_crown.png`, `data/font.ttf`, `data/atlas/*`,
  `client/art/walls/*`, `client/art/lockerroom/{bg.jpg,*.webp}`, `gen_replay.{js,wasm,data}`,
  `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`, `static_replay.js`,
  `static_replay_worker.js`, `index.html`, `league.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  validated offline with the installed CLI's `validate_upload_manifest` before the first dispatch
  (the hive 0.1.0 scar), with these decisions:
  - `$schema` present; top-level `tags: ["generals", "grid", "fog-of-war", "conquest", "ffa",
    "zero-sum"]` (≥ 3; **`game.tags` must not exist** — pistonball 0.1.0); top-level
    **`episode_timeout_minutes: 20`**, not under `game`; top-level `player[]`; **no** top-level
    `replay_viewer`, **no** top-level `version`, **no** `game.display_name`.
  - `game.name` `gen-generals-io`; `game.owner` `daveey@softmax.com`; `game.description` present
    (required); `game.runnable = {"type":"game","image":"{{GEN_GENERALS_IO_IMAGE}}",
    "run":["/bin/gen-generals-io"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/gen-generals-io/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-gen-generals-io/tree/main"}` — the `env` entry is
    mandatory: without it the hosted game container never sees the coworld secret and every league
    episode silently plays scripted (hive, 2026-08-23).
  - `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`**, not top level.
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens","players"]`, **every array property carrying `minItems`/`maxItems`** (the
    tandem 0.1.0 scar): `tokens` 4/4, `players` 4/4, `slots` 0/4. `tokens` is described as
    runner-injected and **no `game_config` anywhere in this manifest contains a literal `tokens`
    array** (matriculate rejects "game_config must not include runner-managed tokens" —
    knights-archers 0.1.0), while `config_schema` keeps *requiring* it. Scalar properties, with
    defaults: **`num_agents`** (integer, `minimum: 4`, `maximum: 4`, default 4), `minPlayers` (4),
    `teams` (4), `cogsPerTeam` (1), `seed` (1734029581), `boardW` (16), `boardH` (10),
    `mountainPct` (22), `cityCount` (8), `cityArmy` (40), `maxTurns` (240), `growthPeriod` (25),
    `directiveEvery` (8), `scoutArmy` (8), `missionMaxSteps` (12), `defendTurns` (6),
    `attempt1Ms` (7000), `retryMs` (3000), `turnBudgetMs` (11000), `turnSpacingMs` (9000),
    `wallClockBudgetSeconds` (660), `lobbyJoinTimeoutTicks` (2400), `startWaitTicks` (48),
    `gameOverTicks` (72), `fastMode` (true), `showPlayerLabels` (false), `fullyObservable` (false),
    `model` (""), `maxOutputTokens` (700).
  - `game.results_schema` — closed (`additionalProperties: false`), exactly the 29 keys of §Server,
    `required: ["names","scores","win","reason","endRule","rank","land","turnsPlayed"]`; every
    seat-indexed array `minItems: 4, maxItems: 4`; `reason` enum `["complete","deadline","fault"]`;
    `endRule` enum `["conquest","full_time","wall_clock","sim_fault","host_error"]`; `winner`
    `{"type":["integer","null"],"minimum":0,"maximum":3}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"text","value":"<docs/PROTOCOL.md section inlined>"}` — objects, never bare strings (the
    garble v0.1.0 scar). `player` documents the seat websocket, the registration blob, the Sprite v1
    frame a seat receives and the fact that a seat sends no inputs; `global` documents the spectator
    frame — the exact state JSON of §Server, the eleven event kinds, the four beat kinds and the
    record vocabulary.
  - **`game.docs`** = **`readme`** `{"type":"text","value":"<README body inlined>"}` and **`pages`** =
    three entries, each `{"id","title","content":{"type":"text","value":…}}`: `rules.md` / "Rules"
    (`docs/RULES.md`), `protocol.md` / "Wire protocol" (`docs/PROTOCOL.md`), `commanding.md` /
    "Writing a generals plan prompt" (`docs/COMMANDING.md`). **Text form, not URIs.**
    `tests/test_gen_manifest.nim` asserts all four values are non-empty.
  - Top-level `player[]` — **two** entries, `sprawl` and `crown`, each with
    `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "200m", memory: "128Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). Both are seated in the certification fixture, because
    **every declared player entry must occupy a certification slot** (the raid 0.1.2
    `players_missing` scar).

  **Variants — `num_agents: 4` inside each `game_config`, NEVER at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0). Three, differing in board and clock only:

  ```json
  "variants": [
    {"id": "ffa", "name": "Four crowns (16x10, 240 turns)",
     "description": "Four commanders, one crown each, on a seeded four-fold-symmetric 16x10 grid. You see only the tiles you own and the ring around them. Cities and crowns grow every turn; every tile you own grows every 25 turns. Take a rival's crown and you inherit everything they own. Last crown standing wins.",
     "game_config": {"players": [{"name": "Red"}, {"name": "Blue"}, {"name": "Green"}, {"name": "Yellow"}],
                     "num_agents": 4, "minPlayers": 4, "teams": 4, "cogsPerTeam": 1,
                     "boardW": 16, "boardH": 10, "mountainPct": 22, "cityCount": 8, "cityArmy": 40,
                     "maxTurns": 240, "growthPeriod": 25, "directiveEvery": 8,
                     "scoutArmy": 8, "missionMaxSteps": 12, "defendTurns": 6,
                     "attempt1Ms": 7000, "retryMs": 3000, "turnBudgetMs": 11000,
                     "turnSpacingMs": 9000, "wallClockBudgetSeconds": 660,
                     "lobbyJoinTimeoutTicks": 2400, "startWaitTicks": 48, "gameOverTicks": 72,
                     "fastMode": true, "showPlayerLabels": false, "fullyObservable": false,
                     "seed": 1734029581}},
    {"id": "blitz", "name": "Blitz (12x8, 160 turns, growth every 15)",
     "description": "A tighter map and a faster production beat: the corners are eight tiles apart, the fog runs out early, and a crown is usually taken before the clock is.",
     "game_config": {"players": [{"name": "Red"}, {"name": "Blue"}, {"name": "Green"}, {"name": "Yellow"}],
                     "num_agents": 4, "minPlayers": 4, "teams": 4, "cogsPerTeam": 1,
                     "boardW": 12, "boardH": 8, "mountainPct": 18, "cityCount": 4, "cityArmy": 40,
                     "maxTurns": 160, "growthPeriod": 15, "directiveEvery": 8,
                     "scoutArmy": 8, "missionMaxSteps": 12, "defendTurns": 6,
                     "attempt1Ms": 7000, "retryMs": 3000, "turnBudgetMs": 11000,
                     "turnSpacingMs": 9000, "wallClockBudgetSeconds": 660,
                     "lobbyJoinTimeoutTicks": 2400, "startWaitTicks": 48, "gameOverTicks": 72,
                     "fastMode": true, "showPlayerLabels": false, "fullyObservable": false,
                     "seed": 1734029581}},
    {"id": "citadels", "name": "Citadels (16x10, twelve cities)",
     "description": "Twelve neutral cities at a garrison of 50 and a slower 30-turn production beat: land alone stops paying, and the map is decided by who can afford the keeps.",
     "game_config": {"players": [{"name": "Red"}, {"name": "Blue"}, {"name": "Green"}, {"name": "Yellow"}],
                     "num_agents": 4, "minPlayers": 4, "teams": 4, "cogsPerTeam": 1,
                     "boardW": 16, "boardH": 10, "mountainPct": 22, "cityCount": 12, "cityArmy": 50,
                     "maxTurns": 240, "growthPeriod": 30, "directiveEvery": 8,
                     "scoutArmy": 8, "missionMaxSteps": 12, "defendTurns": 6,
                     "attempt1Ms": 7000, "retryMs": 3000, "turnBudgetMs": 11000,
                     "turnSpacingMs": 9000, "wallClockBudgetSeconds": 660,
                     "lobbyJoinTimeoutTicks": 2400, "startWaitTicks": 48, "gameOverTicks": 72,
                     "fastMode": true, "showPlayerLabels": false, "fullyObservable": false,
                     "seed": 1734029581}}
  ]
  ```

  **`num_agents` is 4 in all three variants' `game_config` and in the certification fixture.** `ffa`
  is what the league ranks.

  **Certification fixture** — `num_agents: 4` again, inside `certification.game_config`, exactly four
  players, and **both declared players seated** (each twice), so that
  `len(certification.players) == len(certification.game_config.players) == num_agents ==
  SMOKE_SEATS == 4` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks at lines
  106-149):

  ```json
  "certification": {
    "players": [{"player_id": "sprawl"}, {"player_id": "crown"},
                {"player_id": "sprawl"}, {"player_id": "crown"}],
    "game_config": {"players": [{"name": "Red"}, {"name": "Blue"}, {"name": "Green"}, {"name": "Yellow"}],
                    "num_agents": 4, "minPlayers": 4, "teams": 4, "cogsPerTeam": 1,
                    "boardW": 16, "boardH": 10, "mountainPct": 22, "cityCount": 8, "cityArmy": 40,
                    "maxTurns": 240, "growthPeriod": 25, "directiveEvery": 8,
                    "scoutArmy": 8, "missionMaxSteps": 12, "defendTurns": 6,
                    "turnSpacingMs": 0, "wallClockBudgetSeconds": 240,
                    "lobbyJoinTimeoutTicks": 600, "startWaitTicks": 48, "gameOverTicks": 72,
                    "fastMode": true, "showPlayerLabels": false, "fullyObservable": false,
                    "seed": 42}
  }
  ```

  All four seats scripted, no LLM, no rate floor: 240 turns of integer play is ~2 s of wall clock,
  while the replay is 360 ticks ⇒ **30 s of playback**, deliberately longer than any viewer soak
  window (the ecos 2026-08-23 scar). Seed 42 is pinned because it produces a fixture that crosses at
  least one city capture, at least one `generalspotted` and at least one growth beat, so every beat
  kind and every readout is exercised; `tests/test_gen_baselines.nim` asserts those three facts about
  seed 42 so a rules change that flattens the fixture fails the shards rather than the viewer job.
  The `certify` step in `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 s
  does not cover start + connect grace + play + linger — cooperative-hunting 0.1.2).
- **`tools/ci/policies.json`** — four policies, one image, all
  `"run": "/bin/gen-generals-io-player"`:

  ```json
  [{"name":"gen-generals-io-landgrab","run":"/bin/gen-generals-io-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text in §Decisions>"}},
   {"name":"gen-generals-io-regicide","run":"/bin/gen-generals-io-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text in §Decisions>"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"gen-generals-io-sprawl","run":"/bin/gen-generals-io-player",
    "env":{"PLAYER_SCRIPTED":"sprawl"}},
   {"name":"gen-generals-io-crown","run":"/bin/gen-generals-io-player",
    "env":{"PLAYER_SCRIPTED":"crown"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `gen-generals-io-sprawl` and
  `gen-generals-io-crown`, and their versions must differ from the champions' or the platform renames
  a champion "Baseline (N)". No `USE_BEDROCK` flag: the LLM call is made by the **game** pod. Because
  `num_agents` is 4, one league episode seats exactly this set.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml` with `<slug>` →
  `gen-generals-io`, `<IMAGE>` → `coworld-gen-generals-io`, `<SEATS>` → **`4`**, plus
  `SMOKE_REQUIRE_REPLAY_JSON: "0"` on the `docker-smoke` step (binary replay format), `--soak 10`
  added to the `viewer_smoke.mjs` invocation, and a final `wasm-viewer` step running
  `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300` as the
  native ↔ wasm hash gate. `coworld-release.yml` and `coworld-submit.yml` are the templates, with
  `--timeout-seconds 300` on the certify step. `tools/ci/docker_smoke.sh`,
  `tools/build_replay_viewer.sh` and `tools/ci/check_gameversion.sh` are committed **executable**
  (mode 100755) and CI asserts the bit. `tools/ci/viewer_smoke.mjs` is copied **verbatim** from
  `coworld-builder/templates/tools/ci/`, no substitutions.
- **Repo layout**: `src/gen_generals_io.nim`, `src/gen_generals_io_player.nim`,
  `src/generals/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, board.nim, vision.nim,
  resolve.nim, scoring.nim, captain.nim, directives.nim, baselines.nim, llm.nim, decide.nim,
  roster.nim, replays.nim, replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim,
  rig_art.nim, wire_constants.nim, server.nim}`,
  `replay-viewer/{gen_replay.nim, config.nims, static_replay.js, static_replay_worker.js}`,
  `client/`, `data/`, `tests/`, `tools/{build_replay_viewer.sh, gen_wire_constants.nim,
  expand_replay.nim, extract_events.nim, replay_summary.py, record_fixture.sh, tune_baselines.nim,
  wasm_replay_smoke.cjs, ci/}`,
  `docs/{RULES.md, PROTOCOL.md, COMMANDING.md, plans/2026-08-28-gen-generals-io-design.md}`,
  `AGENTS.md`, `README.md`, `config.json`, `nimby.lock`, `gen_generals_io.nimble`, `compose.yaml`,
  `coworld_manifest_template.json`, `Dockerfile`, `Dockerfile.replay-viewer`.

---

## Tests

Nim, in the starter's layout: `tests/test_gen_*.nim`, imported by four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** and as four shard
binaries in `ci.yml`'s `test` job, **in both debug and release** (debug enables Nim's range/overflow
checks — the cheapest catch for an index or accumulator overflow). `tests/config.nims`
(`--path:"../src"`) is the starter's, unchanged. The sandbox can run none of this: `ci.yml` is the
only harness.

**Sim unit tests**

1. **`tests/test_gen_board.nim`** — the seeded generator: the board is **exactly four-fold symmetric**
   in `kind` at reset, for 10 000 seeds and both board sizes; mountain and city counts match the
   formulas in §The game; every general is off the board edge, has `army == 1`, and its three mirror
   images are the other seats'; the rejection samplers terminate for every one of those seeds; the
   connectivity repair leaves **every** non-mountain cell reachable from every other and preserves
   symmetry; and the board is a pure function of `(seed, boardW, boardH, mountainPct, cityCount,
   cityArmy)` — **identical after different play** (the anti-collusion pin) — with `mapRng` consumed
   by nothing but the generator (a call-count assertion).
2. **`tests/test_gen_resolve.nim`** — the ordered rules, one case per numbered step:
   - `legality`: a move from an unowned cell, from a cell with 1 army, off the board, and onto a
     mountain are each discarded, change nothing, and increment `invalidMoves` exactly once.
   - `amount clamping`: `amount` is clamped into `1 .. army-1`; the source always keeps ≥ 1.
   - `friendly`: armies add; `land` and `cities` do not change.
   - `neutral plain`: 1 army takes a 0-army plain and leaves 1 behind on it.
   - `neutral city`: 40 armies against a 40-garrison city fails and leaves the city at 0 armies but
     still neutral; 41 takes it with 1 army on it and `cities` goes up.
   - `enemy tile`: `amount > d` flips ownership with `amount - d`; `amount == d` leaves the defender
     with 0 armies and the tile; `amount < d` leaves `d - amount`.
   - `rotated priority`: with all four seats moving onto the same cell, the winner on turn `t` is
     seat `t mod 4`, and a seat whose source was captured earlier in the same turn has its move
     discarded, not applied to a stale board.
   - `crown capture`: every victim cell **except** the crown transfers with `army div 2` (a 1-army
     tile becomes 0 and is still owned); the crown becomes an owned `city` with exactly
     `amount - d`; the victim is `alive == false` with `eliminatedTurn`/`eliminatedBy` set and zero
     land, army and cities; `generalsCaptured` goes up by one; both events fire; and a chain capture
     in the same turn (A takes B, then C takes A) transfers **B's inherited tiles too**.
   - `growth`: cities and crowns gain +1 every turn and **neutral cities do not**; on
     `turn mod growthPeriod == 0` every owned cell gains exactly +1 including cities and crowns; a
     neutral plain never grows.
   - `vision`: `visible` is exactly owned ∪ 8-neighbours; a cell that leaves vision keeps its
     `kindSeen`/`ownerSeen`/`seenTurn` and reports `army: null`; a never-seen cell reports `?` and no
     fields; `generalspotted` fires once per ordered pair and never twice.
3. **`tests/test_gen_scoring.nim`** — the ladder and its sign: `sum(scores) == 2.0` on 5 000
   randomised end states including every tie shape (two-way, three-way, four-way); the ladder resolves
   in order alive → outTurn → land → army → cities; `win[s]` is exactly `rank[s] == 0`; `winner` is
   null exactly when the top rank is shared; no score is ever negative or above 1.0; a `deadline`
   episode is scored by the same ladder at the stop turn and is never zeroed.
4. **`tests/test_gen_endings.nim`** — `conquest` the turn the third crown falls and not before;
   `full_time` at exactly `maxTurns` and not the turn before or after; `wall_clock` at the 660 s stop
   with a rankable result and a complete replay up to that turn; `sim_fault` on a forced invariant
   trip with a partial replay; `results.reason` and `results.endRule` are always members of their
   declared enums and nothing else is ever emitted.
5. **`tests/test_gen_determinism.nim`** — no floating point in
   `src/generals/{sim,board,vision,resolve,scoring,captain,baselines}.nim` (a source grep); two runs
   from the same seed and the same plans produce byte-identical state streams and two different seeds
   do not; the fog memory digest is in `gameHash` (a hand-forged memory divergence is caught);
   per-cell armies stay inside the 100 000 guard under a 240-turn four-way snowball.
6. **`tests/test_gen_perf.nim`** (release-only, listed in `NIM_TESTS_RELEASE_ONLY`) — a full 240-turn
   four-seat episode with four captains completes in under 60 s.

**Bounded orders / legality on the scripted baselines** — `tests/test_gen_baselines.nim` and
`tests/test_gen_captain.nim`

7. **`baselines are bounded`** — for 300 pseudo-random world states (varying land, army, fog extent,
   city ownership, threatened and unthreatened crowns, both board sizes, all four seats) × **both**
   `sprawl` and `crown`: the emitted plan validates against the reply schema of §Decisions —
   `intent` in the enum, `target` null or inside the board, `reserve` in 0..999, `cities` and
   `scouts` in their domains, `note` empty — and the serialised plan is ≤ 256 bytes. A baseline that
   ever proposes an out-of-domain field fails the build.
8. **`the captain never emits an illegal move`** — over the same states, for both baselines and for
   200 randomly-generated *valid* plans: every emitted move has a source the seat owns with
   `army >= 2`, `1 <= amount <= army(source) - 1`, a target on the board that is not a known
   mountain; at most one move per seat per turn; never a move for a seat that is not `alive`; and a
   seat with no legal move emits nothing and increments `passes` rather than stalling.
9. **`the captain is blind outside the fog`** — the captain is run twice on the same state: once
   normally, once with every cell outside `visible ∪ remembered` replaced by garbage (random kinds,
   owners and armies). The emitted move must be **identical** in both runs, for both baselines and
   for 200 random plans. This is the test that makes the fog real rather than decorative.
10. **`fallback is the sprawl proc`** — the decision engine's fallback path and the `sprawl` baseline
    resolve to the same proc, so they cannot drift.
11. **`the captain is a pure function`** — the same `(view, plan, seat)` triple yields the identical
    move on every call and in both the native and the wasm build.
12. **`sprawl beats crown`** — a scripted-only `ffa` episode at seed 1734029581 with seats
    `[sprawl, crown, sprawl, crown]` completes `complete` (either end rule) with **both** `sprawl`
    seats ranked above **both** `crown` seats; and the seed-42 certification fixture contains at least
    one `citytaken`, one `generalspotted` and one `growth` event.
13. **`baseline tuning is the swept pick`** — `sprawl`'s land threshold (`boardCells div 4`) and
    `crown`'s `reserve = 20` / `scouts = 2` equal `tools/ci/baseline_tuning.json`, the pick from
    `tools/tune_baselines.nim`'s head-to-head sweep (the starter's `test_tuning` pattern; `ci.yml`
    re-runs the sweep with `--check`).

**Plans, observation and privacy**

14. **`tests/test_gen_directives.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced
    JSON, numeric strings, an unknown `intent`, a hyphenated enum, `reserve: 5000` and
    `reserve: -3` (clamped), `scouts: 9` (clamped), `target` off the board (clamped), `target` as
    `{"x":…,"y":…}`, a 300-character `note`, a reply with only a `note` (usable), a non-object reply
    (a parse failure), a 9 KB reply (capped at 4096 then parsed), **and a `note` whose 160th and
    161st characters are a 4-byte emoji** — truncation must land on the **rune** boundary and the
    result must still round-trip `%$` → `parseJson` and decode as strict UTF-8. Two consecutive
    failures ⇒ the `sprawl` plan plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one
    retry; a `throttled` attempt 1 with no other candidate model ⇒ **no** retry and a `throttled`
    fallback.
15. **`tests/test_gen_observation.nim`** — the observation contract: the three ASCII layers are
    exactly `boardH` lines of exactly `boardW` characters drawn only from their declared legends; a
    visible cell reports the exact current `kind`, `owner` and `army`; a remembered cell reports the
    `kind`/`owner` **as of `seen_turn`** and `army: null`; a never-seen cell is `?` in all three
    layers with no entry anywhere else in the object; **no army count, owner or kind of any cell
    outside `visible ∪ remembered` appears anywhere in any seat-facing byte** (a sentinel-army sweep
    over the whole object); `standing` is present, complete and **identical for all four seats**
    (public by design); `armies` caps at 40 with `armies_omitted` correct, `known_cities` at 8,
    `known_generals` at 3, `fog.frontier` at 8; `how_it_went` is ≤ 240 runes; and the seed, the
    `mapRng` state, another seat's plan (this turn's **or any past turn's**), another seat's `note`,
    and any real policy name appear **nowhere** in any seat-facing byte.
16. **`tests/test_gen_identity_privacy.nim`** — the starter's test, kept and extended: no seat frame,
    no LLM system-or-user message and no `plan` record's `view` ever contains a sentinel policy
    address — while the broadcast stream, `roster[].name`, the DOM scorebug and `results.names`
    **must** contain it. That is the two-name-space pin, asserted from both sides, for all four seats.

**Engine and end-to-end**

17. **`tests/test_gen_engine.nim`** — the directive loop against a fake LLM client: **all four** seats'
    calls go out in **one parallel batch** (the fake records in-flight windows and the test asserts
    all four intersect); an eliminated seat is dropped from the next batch; the per-turn budget is
    enforced with a hung client; `sim_config.validate` rejects `attempt1Ms`/`retryMs` that are not
    whole seconds and rejects `attempt1Ms + retryMs > turnBudgetMs`; `turnSpacingMs` holds the batch
    rate at ≤ 30 req/min for four seats and the rolling counter caps an all-retry turn at 28; the
    budget guard switches to scripted and the episode still ends `complete`; a disconnected seat plays
    `sprawl` and revives on reconnect; a never-connecting seat is reported **once** to
    `COGAME_PLAYER_FAILURE_URI` with exactly the closed `{"message","failed_policy_index"}` payload
    and all 240 turns still play; and no living seat is ever left without either a move or a recorded
    `pass` on any turn.
18. **`tests/test_gen_replay.nim`** — **an end-to-end episode writing a replay**: a full four-seat,
    240-turn scripted episode against a temp-dir `COGAME_*` URI set writes `results.json` and a
    `COWLDGEN` replay; `parseReplayBytes` accepts it; **re-simulating from the config + the plan input
    records alone reproduces every recorded `gameHash`**, for all four end reasons — `conquest`,
    `full_time`, `wall_clock` **including the stop turn** (the particle-worlds r2 scar) and
    `sim_fault`; the bytes alone yield seat names, aliases, policy kinds, the full config, the seed,
    every plan and the result; the results key set equals the manifest's `results_schema` key set
    exactly; every `plan` record is within its caps; and the stream contains ≥ 1 `claim`, ≥ 1
    `growth`, ≥ 1 `citytaken`, ≥ 1 `generalspotted` and exactly one `result` record.
19. **`strict-UTF-8 replay parse`** (in the same file) — `tools/replay_summary.py` is run over a
    replay whose every capped field is filled to **exactly** its cap with 4-byte emoji and whose
    policy labels are non-ASCII; its stdout must parse under `json.loads(out.decode("utf-8"))` with
    **strict** UTF-8, contain no lone surrogates, and report `protocol == "gen-generals-io/v1"`. The
    embedded config JSON must decode strictly too.
20. **`every committed fixture carries the current GameVersion`** — the starter's sweep over `tests/`,
    kept, with `tools/ci/check_gameversion.sh`.

**Manifest**

21. **`tests/test_gen_manifest.nim`** — `num_agents == 4` in **all three** variants' `game_config`
    **and** in `certification.game_config`; `num_agents` **absent at every variant top level**; no
    literal `tokens` array in any `game_config`; `len(player) == 2` and **both** declared players
    seated in `certification.players`; `len(certification.players) ==
    len(certification.game_config.players) == 4`; every array in `config_schema` declares
    `minItems`/`maxItems`; `episode_timeout_minutes` at the top level and equal to 20; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme`
    and all three `pages` non-empty **text**; `game.description` present and `game.tags` **absent**;
    ≥ 3 top-level tags; `game.replay_viewer.bundle == "static-replay-viewer"` under `game`;
    `player[].resources.limits.cpu >= "1"`; every variant's `wallClockBudgetSeconds <= 660`
    (≤ 60 % of 1200); `game.name` equals the secret namespace in
    `game.runnable.env.ANTHROPIC_API_KEY_URI`; `results_schema` keys == `generalsResultsJson` keys in
    both directions; `config_schema` covers every field `sim_config.update` reads and no field it
    does not; the compose service name derives `{{GEN_GENERALS_IO_IMAGE}}` and the image is
    `coworld-gen-generals-io`; the runnable's `run` is `/bin/gen-generals-io` and every
    `policies.json` entry's `run` is `/bin/gen-generals-io-player` (the `docker_smoke.sh`
    `/bin/${slug}` defaults); and **every variant's `game_config` actually constructs a valid
    `GameConfig` and generates the board, mountain and city counts this note claims** (the
    collab-cooking 0.1.1 scar: test every variant, not just the fixture).
22. **`manifest loads under the installed CLI`** — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest`.

**Viewer**

23. **`tests/test_gen_viewer.nim`** (static assertions in the `test` job) — `chrome_common.js` is
    **byte-identical** to the starter's (sha256 pinned as a literal) and contains no gen edit;
    `replay_broadcast.html` begins with the starter's bytes up to the documented splice marker and
    only appends after it; `broadcast_core.js`'s kept procs are byte-identical to the starter's,
    `pushFeed`'s signature included; no identifier in the appended game block collides with any name
    in `chrome_common.js`'s alias list (the tandem hoisting trap) and the beat builder is `genBeat`,
    never `markBeat`; the set of `.beat-marker.<kind>` CSS rules equals **exactly**
    `{citytaken, generalspotted, generalcaptured, end}`; `#endcard { bottom: var(--band` is present;
    `relayout()` sets `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is
    positioned inside the transport band; the four 360 px rules exist (including the exact-integer
    numeral rule and the `army >= 5` density rule); `#viewpanel`, `#minimap`, `#zoombar`, `#fpv*` and
    `#povBadge` appear nowhere; and no `ctf_`/`CTF_`/`PB_` identifier survives in `client/`,
    `replay-viewer/` or `src/` **except** the two documented `CTF_WIRE` alias lines.
24. **`tests/test_gen_endcard_labels.nim`** — the forbidden-vocabulary grep of §Viewer, zero matches,
    and each re-mapped string present exactly once.
25. **`tests/test_gen_label_contract.nim`** — the starter's `test_label_contract` pattern: the emitted
    sprite-label vocabulary equals `tests/label_manifest.txt`, regenerated in the same commit as any
    label change.

**Viewer smoke — the bundle is EXECUTED, not merely built**

26. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`, no substitutions) is run by **`ci.yml`'s
    `wasm-viewer` job**, which `needs: docker-smoke` and runs it against **the replay `docker-smoke`
    produced** (downloaded as the `smoke-replay` artifact), in headless chromium (Playwright pinned
    1.55.0 in both the npm module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. The job fails unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives inside the timeout, the clock and tick readouts **advance**
    across the soak, and `canvas_text.never_inside == 0`. `--strict-text-bounds` stays on: the board
    is fixed and fits the frame, so any text drawn outside the canvas is a bug — and this game draws
    a numeral in every occupied cell, which is exactly the surface that scar covers. The job also
    asserts `tools/build_replay_viewer.sh` is present and **executable** and that `index.html` and a
    non-empty `.wasm` exist before running.
27. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module, kept: `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300`
    fails if `gen_mismatch_tick() != -1`. wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.
28. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `note` at all**, so
    the smoke replay can never exercise the feed's commander-line path (the cogchemists 2026-08-24
    scar). The fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and
    shims only the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26
    scar) — driving the real page with a full-cap 160-rune `note` on all four seats, a board where
    every cell holds a three-digit army, a crown-capture banner, an eliminated plate, and the fog lens
    on each of the four seats in turn, at 360 / 620 / 1280 px.

**Docker smoke**

29. **`tools/ci/docker_smoke.sh`** — a raw-Docker episode from the certification fixture in the
    production image, seats cross-checked against **`SMOKE_SEATS=4`**, `SMOKE_REQUIRE_REPLAY_JSON=0`,
    asserting the game container exits 0 with `results.json` and a replay, that `results.reason` is
    not `fault`, and that **every player container exited 0** — including the containers of seats
    eliminated mid-episode (the raid 0.1.3 scar plus this game's own elimination path). Its replay is
    uploaded as the `smoke-replay` artifact and is the input to the `wasm-viewer` job.

---

## Out of scope (v1)

- **Any dependency on `Metta-AI/coworld-planet-wars`.** The coordinator ruled this a standalone grid
  game and that ruling is final: no code, config, map model, manifest fragment or variant of planet
  wars is read, imported or extended, and this coworld is not shipped as a variant of it.
- **A bit-exact port of generals.io or of `strakam/generals-bots`.** The rules here are an adaptation
  of a public specification, not a reproduction of anyone's engine, and no test compares a trajectory
  to a reference implementation. The documented divergences, each listed with its generals.io
  counterpart in `docs/RULES.md`: a **move carries an explicit `amount`** in `1 .. army-1` rather than
  only "all" or "half" (a strict superset, and it is what makes `reserve` exact); **priority rotates
  by turn number** rather than by a server-side move queue; **generals start at 1 army** on a board
  generated by this repo's own symmetric generator; **swamps, lookout towers, desert tiles and the
  50/50 city-spawn variance are absent**; and **a 240-turn clock** stands in for generals.io's
  open-ended games.
- **Seat counts other than 4.** The idea allows 2–8; 4 is fixed everywhere (§The game), and
  `num_agents` is 4 in every variant and in the cert fixture. An 8-seat FFA needs a board roughly
  twice the area, which fails the 360 px legibility arithmetic in §Viewer, and a 2-seat duel removes
  the snowball this coworld exists to show. Neither is a config flip and neither is shipped.
- **Per-turn LLM control of individual moves.** The idea's "one move per tick" is honoured at the
  plan layer; the move layer is the deterministic captain. A per-turn protocol is a plausible v0.2 —
  the move stream already exists and is already re-derived by the viewer — but 960 calls do not fit
  720 s and it is not shipped.
- **Any inter-seat channel** — chat, radio, `say`, emotes, or a diplomacy phase. This is the
  structural answer to the idea's FFA-teaming worry (§The game) and removing it is not a tuning knob.
  `note` stays spectator-only.
- **An explicit alliance mechanic, an alliance audit tool, or seat-randomisation logic in this repo.**
  Seat assignment belongs to the platform; alliances cannot be expressed without a channel; and an
  audit of something inexpressible is dead code.
- **Fog rendering as a player-facing pod view.** The spectator viewer shows the whole board by
  default and offers the per-seat fog lens as a *lens*; there is no live per-seat client and no live
  spectating. `/global` broadcasts a status feed (the certifier requires it) but the hosted spectator
  experience is the static replay bundle only.
- **Learned RL-vector policies and any third-party bot corpus.** Both champions are LLM prompt
  policies and both fillers are scripted; nothing here trains, and no external bot — including
  `generals-bots`' PettingZoo baselines — is vendored or run.
- **Everything the starter had that this game does not.** Guns, aim, vision cones, pixel shadowcast
  fog, the first-person PIP, paint, hills, hearts, flags, grenades, med kits, shields, barriers,
  trenches, perks, handicaps, lives, respawns, kills, multi-cog squads, achievements, campaign mode,
  multi-game episodes, the procedural terrain generator, the map pool, mapkit and the map editor —
  all deleted, not disabled (§Sim module), and none of them return in v1.
