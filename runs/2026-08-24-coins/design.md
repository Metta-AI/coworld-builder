# Coins — two cogs, one small room, and every coin a choice

**Starter: `Metta-AI/coworld-ctf` (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`.**
Coins is a real-time grid loop whose rules are written fresh for this coworld — the first row of the
starter table (`prompts/10-design.md` §Starter table): "any real-time game loop (grid OR continuous
physics), new rules written for this coworld". Paintbot supplies the tick loop, the sprite/board
protocol, the per-tick replay, the broadcast chrome, the static wasm replay bundle, the two
Dockerfiles, the build hook and the CI shape. **Every convention there holds here unless this note
says otherwise.** Two things paintbot does not have are forked from `Metta-AI/cogame-bullwhip`
(mounted at `/workspace/starters/cogame-bullwhip`) and are named as such where they appear: the
*game-side* batched LLM decision layer (`src/bullwhip/llm.nim`) and the thin prompt-carrying player
process (`src/bullwhip_player.nim`). **All four viewer files come from coworld-ctf and from no other
starter** (see `## Viewer`).

**Design pins (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins every coworld
inherits), each answered explicitly:**

| pin | how Coins satisfies it |
|---|---|
| starter by game shape | `Metta-AI/coworld-ctf` (paintbot) — a real-time grid loop with new rules and no pre-existing code to port. The Melting Pot substrate is a *reference*, not a codebase we reproduce bit-exactly, so this is the first starter row, not `cogame-moba`. |
| public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-coins`, **public** — public is a certification prerequisite (`source-resolves` 404s on private). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | one image; `PLAYER_PROMPT="<strategy>"` vs `PLAYER_SCRIPTED=honest\|greedy\|reciprocator\|tit-for-tat` (`## Decisions`). Champions #1 `coins-truce` (daveey) and #2 `coins-ledger` (daveey-1) are both prompt policies; the two fillers are the scripted `reciprocator` and `tit-for-tat`. |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` live-server viewer is declared anywhere (`## Viewer`, `## Packaging`). |
| real art, the starter's chrome verbatim | `scripts/art/gen_coins_art.py` bakes the two cog liveries off paintbot's shipped `data/rig_real/{red,blue}` rigs, both coin faces, the tiled room floor and the loading art; `client/chrome_common.js` is copied **byte-for-byte** and `client/replay_broadcast.html` is the starter's page **with a game block appended** (`## Viewer`). |
| legible to a casual spectator | `BEAT 7 / 18`, plain-language feed rows ("COBALT **STEALS** a copper coin — +1 COBALT / −2 COPPER"), a theft counter on each scorebug plate, a reciprocity timeline strip; checked at **360 px**. |
| two name spaces | anonymous cog aliases `Copper` / `Cobalt` in-game; real policy names only in the replay's `policyNames[]`, the scorebug plates, the feed, the endcard and `results.names[]` (`## The game`). |
| degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | ≤ 576 s worst case against a 720 s budget, deadline checked at every beat close, retry-once-then-scripted, `shutdownGraceSeconds = 20` (`## Decisions`, `## Server, player, protocol`). |
| `num_agents` in every variant AND the cert fixture | **2**, in all five variants, in `certification.game_config`, and as `<SEATS>` = `2` in `tools/ci/docker_smoke.sh` (`## Packaging`, `## Tests`). |
| prove it in CI | sim unit tests, a bounded-orders/legality assertion on the scripted baselines, a dilemma-shape oracle, an end-to-end episode writing a replay, a strict-UTF-8 replay parse, and an **executed** viewer smoke (`## Tests`). |

**Source idea (verbatim):**

> Port of Melting Pot's coins. Two cogs, one room, coins of two colours spawning at random. Each cog owns a colour. Picking up any coin is +1 to you; picking up the other cog's colour is additionally –2 to them. Long episode with a random end. It's a spatial repeated Prisoner's Dilemma: the greedy policy (grab everything) is a mutual-harm trap, the restrained policy needs trust, and tit-for-tat in coin-space is the obvious emergent strategy. Melting Pot's scoring scenarios pair the focal cog with a reciprocating bot that starts punishing after N thefts.
>
> Seats: 2
> Motive: social dilemma, dyadic
> Policy interface: per-tick grid actions; tiny enough to run huge batteries
> Fills gap: the minimal two-player dilemma — a fast calibration coworld and a good first LLM-RL target (cf. cogamer-rl)
> Integrity (anti-collusion): only two seats, so the ladder must be built on mixed pairings + scripted reciprocators; anonymous aliases.
>
> Replay plan (watchability): a 'theft counter' per cog and a reciprocity timeline; the moment one cog starts leaving the other's coins alone is the beat.
>
> Source: substrate coins. Video https://youtu.be/a_SYgt4tBsc

---

## The game

### Seats, aliases, colours

**`num_agents = 2`. Exactly two seats, in every variant, in the certification fixture, always.**
There is no variant with any other seat count; a Coins episode is a dyad by definition.

| slot | in-game alias | owned coin colour | chrome team key | hex | spawn cell |
|---|---|---|---|---|---|
| 0 | `Copper` | `copper` | `red` | `#e0523a` | (1, 1) |
| 1 | `Cobalt` | `cobalt` | `blue` | `#3f7cc4` | (7, 7) |

Alias, colour and spawn cell are a fixed function of the slot; nothing rotates within an episode.
The chrome team keys are `red` and `blue` because `chrome_common.js`'s `TEAM_COLOR` / `TEAM_ORDER`
already know those two names, which gets the scorebug plates, the momentum legend and the endcard
their colours with **zero edits to that file** (it is copied byte-for-byte — see `## Viewer`).

**Two name spaces (pin).** A seat sees only the two aliases, `Copper` and `Cobalt`. No policy name,
player name, account, prompt or league standing of the other seat ever reaches a seat. The replay
carries `policyNames[]` alongside `names[]`; the viewer's plates, feed and endcard show the **policy**
name (`coins-truce`, `coins-reciprocator`, …); `results.names[]` carries policy names for the
platform. This is also the idea's anti-collusion requirement: with only two seats the ladder is
carried by mixed pairings against the scripted reciprocators (both fillers), and an anonymous alias
means a champion cannot recognise, and therefore cannot privately agree with, a specific opponent.

### The room

- One fixed arena, **9 × 9 cells** including a one-cell wall ring: **7 × 7 = 49 walkable interior
  cells**, `x, y ∈ [1, 7]`, fully open (no interior obstacles). Rendered at 56 px/cell = a
  **504 × 504** board (1:1). It never changes size or shape, in any variant — which is exactly why
  `#viewpanel` (zoom bar + minimap) is dropped from the viewer: **this is a fixed arena, the whole
  board always fits the frame.**
- The map is a compile-time ASCII constant in `src/coins/room.nim` (`#` wall, `.` floor):

```
#########
#.......#
#.......#
#.......#
#.......#
#.......#
#.......#
#.......#
#########
```

- Moves are 4-way: `north` (−y), `east` (+x), `south` (+y), `west` (−x). There are no diagonals.
  Distance everywhere in this note means **Manhattan** distance.
- Every sim quantity is an **integer**: cell coordinates, facings (0 = N, 1 = E, 2 = S, 3 = W),
  scores in whole points, tick counts. The RNG is paintbot's seeded integer stream. No float enters
  sim state, so one seed reproduces one episode bit-exactly on any host (the determinism test in
  `## Tests` depends on it).

### Clock: ticks, beats, and the random end

- The sim runs at **24 ticks per second of replay video** (paintbot's `fps`), and a **beat is
  `ticksPerBeat = 20` ticks**. One intent per seat per beat (`## Decisions`).
- `minBeats = 12`, `maxBeats = 24`, `endChancePermille = 120` in the default variant. So an episode
  is **240 to 480 ticks = 10.0 to 20.0 s of replay video** — deliberately longer than the 10 s
  viewer soak even at its shortest (the ecos learning).
- **The random end, exactly.** A dedicated RNG stream `endRng`, seeded `seed xor 0x00C0_1175`, is
  drawn **once at the close of every beat `b ≥ minBeats`**, in beat order:

  ```
  at the close of beat b:
    if maxBeats > minBeats and b >= minBeats and b < maxBeats:
        r = endRng.next() mod 1000            # uniform 0..999
        if r < endChancePermille: end the episode now, reason "random_end"
    if b == maxBeats:            end the episode now, reason "beat_cap"
  ```

  The stream is separate from the coin-spawn and move-contest streams (paintbot's `seed xor const`
  convention) so that adding or removing a draw elsewhere never shifts which beat the episode ends
  on for a given seed. **When `minBeats == maxBeats` the draw is skipped entirely** and the episode
  always runs exactly that many beats — that is how the certification fixture is made deterministic.
  Expected length in the default variant ≈ 18.4 beats.
- **The drawn end beat is hidden from both seats.** A seat is told `beat`, `minBeats`, `maxBeats`
  and `endChancePermille` — so it knows the *distribution* of the remaining shadow of the future,
  which is the whole point of a random end — but never the realised end beat. The realised end beat
  is recorded in the replay as `endBeat` and revealed to the spectator only on the endcard.

### Coins

- A coin occupies one interior cell. At most one coin per cell; a coin never occupies a cell a cog
  is standing on.
- **Opening:** `initialCoins = 6` coins are placed at tick 0 — 3 `copper` and 3 `cobalt` — at cells
  drawn from `coinRng` (seeded `seed xor 0x00C0_1147`) uniformly among interior cells that are not
  the two spawn cells and not already holding a coin.
- **Spawning:** at every tick `t` with `t mod coinSpawnIntervalTicks == 0` and `t > 0`, if the board
  holds fewer than `coinCap = 8` coins, **one** coin is spawned: its colour is `copper` if
  `coinRng.next() mod 2 == 0` else `cobalt` (a fair 50/50 draw, so the two colours are supplied
  equally in expectation), and its cell is drawn uniformly from the interior cells that hold no coin
  and no cog. If no such cell exists, nothing spawns this tick. `coinSpawnIntervalTicks = 12`.
- **The room is deliberately coin-starved.** 480 ticks ÷ 12 = 40 spawns + 6 opening coins = **46
  coins per full-length episode**, against two cogs that can each reach a coin roughly every 12
  ticks. Supply, not walking speed, is the binding constraint — that is what makes taking the other
  cog's coin a real gain rather than a redistribution, and it is what makes this a Prisoner's
  Dilemma rather than a Chicken game (the arithmetic is in `## Sim module` §The game has to be the
  dilemma it claims).

### Scoring — exact formula and sign

When seat `i` picks up a coin of colour `c`:

1. **`score[i] += pickupReward` (= +1). Always. Every coin is +1 to whoever takes it.**
2. **If `c` is not seat `i`'s owned colour, additionally `score[1 - i] -= theftPenalty` (= −2).**
   The thief still keeps its +1; the victim loses 2. Net to the pair on a theft: **−1**.

Nothing else changes a score. There is no participation bonus, no movement cost, no end-of-episode
bonus, no normalisation. Scores are whole integers and **can go negative**.

Counters, all integers, all per seat:

- `pickups[i]` — coins of any colour seat `i` collected.
- `thefts[i]` — coins of the **other** cog's colour seat `i` collected. `thefts[i] ≤ pickups[i]`.
- `stolenFrom[i]` — coins of seat `i`'s **own** colour the other cog collected. In a two-seat game
  this is identically `thefts[1 - i]`; both are reported because both read naturally in the viewer.
- Identity that CI asserts: `score[i] == pickups[i] * pickupReward - stolenFrom[i] * theftPenalty`.

**`results.scores[i] = float(score[i])`. Sign: HIGHER IS BETTER.**
**The league ranks by `results.scores`, higher better** (the platform's Elo consumes `scores` and
`win`). `results.win[i] = (scores[i] == max(scores))` — on an exact tie both seats are winners.

### Tick resolution order (exact, numbered)

Every tick runs these eight steps in this order. Within a step, all reads use the state as it stood
at the **start of that step**, so no hidden ordering can change an outcome; the one place where two
seats genuinely contend (step 3d) is settled by a seeded coin flip, not by slot order.

1. **Timers.** For each cog: `stepCd = max(stepCd - 1, 0)`.
2. **Intent evaluation.** For each cog, evaluate its current beat's intent against the state at the
   start of this step and produce a **target cell** (or "none"). The five intents and their targets
   are in `## Decisions` §The five intents. From the target, compute the ordered list of
   *reducing directions*: those of `N, E, S, W` (in that order) that strictly reduce the Manhattan
   distance to the target. A cog with `stepCd > 0`, or with no target, produces `wait`.
3. **Movement**, both cogs resolved **simultaneously**:
   - **a. Legality.** A candidate cell is legal for cog `i` iff it is an interior floor cell, it is
     **not** the cell the other cog occupied at the start of this step (there is no follow-through:
     a cog never steps into a cell that was occupied when the tick began, even if its occupant is
     also moving away), and it does **not** hold a coin of a colour this cog's intent forbids.
   - **b. Choice.** Cog `i`'s desired step is the first legal cell among its reducing directions. If
     none is legal, it is the first legal cell among **all** of `N, E, S, W` in that order (a
     sidestep, which may increase the distance — this is what guarantees a restrained cog can never
     deadlock behind a coin it refuses to take). If that is also empty, the cog waits.
   - **c. Swap.** If each cog's desired cell is the other's starting cell, **both wait** (cogs never
     swap through each other).
   - **d. Same-target contest.** If both cogs desire the **same** cell, one flip is drawn from
     `moveRng` (seeded `seed xor 0x004D_4F56`): `moveRng.next() mod 2` names the winner's slot. The
     winner moves; the loser **waits**, and its `stepCd` is *not* charged. **This is the rule that
     settles a simultaneous pickup conflict**: two cogs can never occupy one cell, so they can never
     both take one coin — the flip decides who reaches it.
   - **e. Commit.** Each moving cog's position becomes its desired cell, its facing becomes the
     direction it moved, and `stepCd = stepCooldownTicks = 3`.
   - A cog that was blocked emits one `blocked` event with `why` ∈ `restraint` (a coin its intent
     forbids stood in the way), `contested` (it lost the flip at 3d) or `occupied` (3a/3c).
4. **Pickup.** For each cog that ended step 3 standing on a cell holding a coin, that coin is
   removed and collected: `pickups += 1`, and if the coin's colour is not the cog's own colour,
   `thefts += 1` and the other cog's `stolenFrom += 1`. Because step 3 guarantees the two cogs are
   on different cells, no coin is ever collected twice.
5. **Scoring.** Apply the formula above for each pickup made in step 4: `+pickupReward` to the
   collector, and `-theftPenalty` to the victim when the coin was not the collector's colour.
   Emits `pickup` (own colour) or `theft` (other colour).
6. **Spawn.** The spawn rule above.
7. **Counters.** Update the per-beat theft tallies, the restraint streaks, and the leader
   (`argmax score`, ties → slot 0); emit `leadchange` when the leader differs from the previous
   tick's.
8. **Record.** Append this tick's state frame and its events to the replay (`## Sim module`).

At a **beat close** (the last tick of every beat, `t mod ticksPerBeat == ticksPerBeat - 1`) the sim
additionally, in this order: emits `beatclose`; emits any `truce` beats earned (below); runs the
random-end draw; checks the play deadline; and — if the episode continues — blocks for the next
batched decision (`## Decisions`).

**The `truce` beat** — the idea's headline moment, "the moment one cog starts leaving the other's
coins alone", defined so a test can assert it. At the close of beat `b`, a `truce` event is emitted
for seat `i` iff **all** of: (1) `thefts[i] ≥ 1` (it has stolen at some point), (2) `thefts[i]` has
not increased during the last `truceBeats = 3` consecutive beats, and (3) no `truce` has been
emitted for seat `i` since its most recent theft. Every later theft re-arms it.

### End conditions and the legal `results.reason` values

The episode ends at the FIRST of:

| condition | `results.reason` | scores |
|---|---|---|
| the random-end draw fires at a beat close (`b ≥ minBeats`) | `random_end` | as computed |
| beat `maxBeats` closes without the draw having fired | `beat_cap` | as computed |
| wall clock passes the play deadline (`0.6 × episodeTimeoutSeconds` = **720 s**), checked **at beat closes only** | `deadline` | the beats played are scored exactly as they happened; nothing is imputed for the beats not played |
| **no** seat socket connected within `playerConnectTimeoutSeconds = 180` | `forfeit` | both `0.0`; `results.json` and the replay are still written |

**`random_end`, `beat_cap`, `deadline`, `forfeit` are the only legal `results.reason` values.**
There is no other early termination: a room where neither cog ever moves plays to its end and both
score 0, which is a completed game of Coins, not an error. If **one** seat's socket never connects
(or it disconnects mid-episode), the episode still plays to a normal end — that cog is driven by the
`reciprocator` scripted baseline for every remaining beat — and the reason is `random_end` or
`beat_cap` as usual; `forfeit` is reserved for the case where *neither* seat connected.
`deadline` is declared acceptable (it means the LLM was slow, not that the game broke), but the
arithmetic in `## Decisions` is sized so that it should not fire.

---

## Decisions: LLM with scripted fallback

Both policies ship in the **same image** from day one, env-switched, exactly like bullwhip:
`PLAYER_PROMPT="<strategy text>"` for an LLM policy, `PLAYER_SCRIPTED=honest|greedy|reciprocator|tit-for-tat`
for a scripted baseline. **A policy is a prompt**: `src/coins_player.nim` (a fork of
`cogame-bullwhip/src/bullwhip_player.nim`) is one thin process that connects, sends
`{"type":"prompt","prompt":…,"scripted":…}` and then only listens. All decision-making happens in
the **game** container (`src/coins/llm.nim`, forked from `cogame-bullwhip/src/bullwhip/llm.nim`),
which is what makes one parallel batch per beat possible and why the coworld secret must be declared
on the **game** runnable (the hive learning, 2026-08-23).

### The five intents

A seat submits **one intent per beat**; a deterministic per-tick kernel (`src/coins/kernel.nim`)
then executes it for the next `ticksPerBeat = 20` ticks, producing the per-tick grid actions the
idea's policy interface asks for. This is the batched-swarm cadence hive, ecos and matrix-games
proved: ≤ 48 LLM calls per episode instead of 960, with the per-tick loop intact.

The kernel's job each tick is to produce a **target cell** and a **forbidden colour set**; step 2/3
of the tick order does the rest.

| intent | target cell each tick | forbidden colours | if no coin qualifies |
|---|---|---|---|
| `take_mine` | the nearest coin of **your own** colour | the **other** colour | `hold` (do not move) |
| `take_any` | the nearest coin of **any** colour; ties broken **own colour first**, then lowest `y`, then lowest `x` | none | walk to the room centre (4, 4) and wait there |
| `take_theirs` | the nearest coin of the **other** cog's colour | none (an own-colour coin stepped on is still collected: it is a free +1) | fall back to `take_mine`'s target; if that is also empty, `hold` |
| `guard` | the coin of **your own** colour that is nearest **to the other cog** (ties → lowest `y`, then lowest `x`) — bank the coins most at risk first | the **other** colour | `hold` |
| `hold` | none | the **other** colour | — |

"Nearest" is Manhattan distance from the cog's current cell, ties broken lowest `y` then lowest `x`.
**"Forbidden" is enforced as a movement rule, not a pickup rule**: a cog whose intent forbids a
colour never *steps onto* a coin of that colour, so restraint is something a spectator literally
watches — the cog walks around the coin it will not take, and the sim emits a `blocked`
`why: "restraint"` event when it does. Pickup itself is unconditional on entering a cell.

The intent in force during beat 1 comes from an **opening batch** issued before tick 0; if that batch
fails for a seat, beat 1 runs that seat's scripted fallback intent.

### Cadence and the wall-clock budget

One **turn = one beat**, and **both seats decide simultaneously**: at every beat close the game
issues **both seats' requests as ONE parallel batch** (`curly.makeRequests`, bullwhip's `decideAll`)
— never sequentially, never one seat waiting on the other. Said out loud:

```
per episode:        <= 24 beats x 2 seats                      = <= 48 LLM requests
inter-batch floor:  minBeatSeconds = 5 s  ->  2 req / 5 s      = 24 req/min  <  30 (sidecar cap)
per beat worst:     llmTimeoutSeconds 12 (batch) + 12 (retry)  = 24 s
episode worst:      24 beats x 24 s                            = 576 s
  + connect/settle margin (connect wait already elapsed, final frames, artifact writes, grace)
                                                               ~  30 s
  = 606 s   <  720 s   ( = 0.6 x episodeTimeoutSeconds 1200 )
episode typical:    ~18 beats x max(5 s floor, ~3 s batch)      =  90 s
simulation cost:    480 ticks x ~0.05 ms                        =  ~0.03 s  (negligible)
```

The 5 s floor is not padding: the Bedrock sidecar caps **30 requests/minute per episode** (the raid
learning), and with 2 seats per batch a 5 s floor lands at 24 req/min with margin. The play deadline
(`0.6 × episodeTimeoutSeconds`; the game container is **not** given `COWORLD_TIMEOUT_SECONDS`, so
1200 is assumed unless the environment supplies it) is tested **at beat closes**; crossing it calls
`endEarly()` and settles with `reason: "deadline"`. `short-fuse`'s worst case is 14 × 24 = 336 s;
every other variant caps at `maxBeats = 24`, hence 576 s. **No variant can exceed the budget.**

### The observation each seat gets

Sent as the `state` frame at every beat close (and once at episode end) and rendered into the user
prompt. Every number below is visible to that seat; **nothing else is.**

```json
{"type":"state","protocol":"coins.player.v1","slot":0,"alias":"Copper","colour":"copper",
 "beat":7,"minBeats":12,"maxBeats":24,"endChancePermille":120,
 "ticksPerBeat":20,"tick":140,"ticksPlayed":140,
 "room":{"w":9,"h":9,"interior":[1,1,7,7]},
 "rules":{"pickupReward":1,"theftPenalty":2,"coinCap":8,"coinSpawnIntervalTicks":12,
          "stepCooldownTicks":3,"moves":["north","east","south","west"],
          "intents":["take_mine","take_any","take_theirs","guard","hold"],
          "restraint":"an intent that forbids a colour never steps onto a coin of that colour",
          "endRule":"after beat 12 each beat close ends the episode with probability 0.120; it always ends by beat 24"},
 "you":{"x":4,"y":6,"facing":2,"score":11,"pickups":13,"thefts":2,"stolenFrom":5},
 "them":{"alias":"Cobalt","colour":"cobalt","x":7,"y":3,
         "score":4,"pickups":12,"thefts":5,"stolenFrom":2},
 "coins":[{"x":1,"y":4,"colour":"copper"},{"x":6,"y":2,"colour":"cobalt"}],
 "beatLog":[{"beat":6,"you":{"intent":"take_mine","pickups":2,"thefts":0},
             "them":{"pickups":3,"thefts":2},"score":[9,6]}, "…every beat so far…"],
 "notes":"…your own notes from last beat…"}
```

- **Visible:** the whole room (it is 7 × 7 and open — there is no fog of war and no partial
  observability in Coins); every coin on the board with its colour; **both** cogs' exact positions;
  **both** cogs' scores, pickups, thefts and stolen-from counters — the theft counter is public,
  because a dilemma in which you cannot see that you were robbed is not a dilemma; the complete
  per-beat history of the episode so far (each beat's pickups and thefts for both cogs, and the
  running score after it) — **your own intent per beat is included, the other cog's is not**; the
  full rule set and every constant; and your own notes from last beat.
- **Hidden:** the other cog's **intent for the coming beat**; the other cog's `say` and `notes`; the
  other cog's policy name, prompt and player account; the RNG seed and every RNG stream; the
  **drawn end beat**; anything about the league, ratings or previous episodes.
- **There is no inter-seat channel.** `say` is spectator-only — written to the replay and drawn in
  the viewer's feed, never shown to the other seat. Melting Pot's coins has no communication
  channel, "the restrained policy needs trust" only means something if trust cannot be replaced by
  a promise, and a silent room is the anti-collusion property the idea asks for: with no channel
  there is no codebook.

### The reply schema

The model must answer with exactly one JSON object whose first character is `{`:

```json
{"intent":"take_mine","say":"your coins are yours","notes":"Cobalt stole 2 in beat 5, 3 in beat 6; punished beats 7-8, watching now"}
```

| field | type | cap / domain | on violation |
|---|---|---|---|
| `intent` | string | one of `take_mine`, `take_any`, `take_theirs`, `guard`, `hold` (case-insensitive) | absent or not in the set → **invalid reply** |
| `say` | string | **48 characters** | truncated |
| `notes` | string | **300 characters** | truncated |

Those are the only two free-text fields and **both carry a character cap**. Extra keys are ignored;
trailing prose after the closing brace is tolerated by the extractor.
**Truncation is on RUNE boundaries, never bytes** — `cleanText(text, limit)` = `strip` → if
`runeLen > limit`, `runeSubStr(0, limit - 1) & "…"` (bullwhip's `cleanText`; a byte cut once put
invalid UTF-8 into a replay and only a strict parser found it). Newlines in `say` become spaces.
Both fields are recorded in the replay and rendered in the feed; `notes` is returned to the same
seat (and only that seat) in the next beat's observation.

### Prompts

**System prompt** (composed by the game, per seat, per beat): the seat's alias and owned colour in
capitals; the full rule set — the 7 × 7 room, the 4-way moves and the 3-tick step cooldown, the beat
structure, the five intents and exactly what the kernel does with each, the restraint-is-a-movement-
rule sentence, the coin spawn cadence and cap; the scoring rule stated twice, once as prose and once
as the formula:

> Every coin you pick up is **+1 to you, whatever its colour**. If the coin was COBALT — your
> opponent's colour — your opponent additionally loses **2**. You keep the +1 either way. Your score
> is `pickups − 2 × (coins of your colour your opponent took)`. Higher is better. Scores can go
> negative.

then the shadow-of-the-future sentence ("the episode has run `<beat>` beats; from beat 12 on, each
beat close ends it with probability 0.120, and it always ends by beat 24 — so on average there are
several beats left, and you will meet this cog again in each of them"); then the statement that the
other cog is another policy deciding **at the same moment**, that nothing you write is read by it,
and that it can see your position, your score and your theft counter exactly as you can see its own;
and the output contract, ending:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

(Bedrock/Haiku answers prose-first without that final sentence — playbook §Phase 1.)

**User prompt:** the observation rendered as compact text — a `BEAT 7 (ends by beat 24)` header;
your own row (`YOU Copper (copper) at (4,6) · score 11 · took 13 coins, 2 of them Cobalt's · Cobalt has taken 5 of yours`);
their row; the coin list (`COINS ON THE BOARD: copper at (1,4) · cobalt at (6,2)`); the per-beat
history as one line per beat (`beat 6 · you take_mine: 2 coins, 0 thefts · Cobalt: 3 coins, 2 thefts · score 9–6`);
then `YOUR NOTES FROM LAST BEAT`, then the operator block:

> GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
> requested format):
> `<PLAYER_PROMPT>`

then a one-line restatement of the reply shape **with the five legal intent names enumerated
verbatim** (the escrow fix for formal-output fallback rates).

**Transport:** bullwhip's ladder, haiku-only (the raid learning — the sonnet fallback times out on
every sidecar call and turns one throttle into a cascade):
`bedrockModelIds() = ["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`, `BEDROCK_MODEL` overrides.
`maxOutputTokens = 500`. No `output_config.effort` — Haiku 4.5 400s on it. Credentials in order:
Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` / `AWS_BEARER_TOKEN_BEDROCK`) →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`. With none present, the client disables itself
immediately and every seat plays `reciprocator` — which is what keeps offline certification green
and deterministic.

**Champion prompts** (phase 50 uploads these; **both are `PLAYER_PROMPT` policies**, and both policy
entries carry `"USE_BEDROCK": "true"` — without it the platform gives the player pod no Bedrock
sidecar and the seat silently plays scripted, the cogolf trap):

- `coins-truce` (champion #1, daveey): *"Open restrained: take only your own colour and let the
  other cog's coins sit, even when one is closer than yours. You are trying to establish a truce
  worth more to both of you than a scramble, and the only way you can say so is by walking past
  their coins where they can see you do it. Watch their theft counter every beat, not their words.
  If it does not move, keep taking only yours. If it moves by one, hold your line for one more beat
  — a single theft can be a coin they stumbled onto. If it moves twice, switch to take_theirs for
  exactly two beats so the cost is unmistakable, then go straight back to take_mine and give them a
  clean beat to reciprocate. Never punish for longer than they stole; never punish twice for the
  same theft. Late in the episode, when the end could come at any beat, keep the truce anyway — a
  last-minute grab wins you one coin and costs you the two beats you spend being robbed back."*
- `coins-ledger` (champion #2, daveey-1): *"Keep a ledger and play the balance. Every beat, compute
  what each of you has taken from the other and what the score gap is. Your score is pickups minus
  twice their thefts, so their thefts hurt you exactly twice as much as your own pickups help — a
  cog that steals from you is the single biggest term in your score, and matching them is cheaper
  than absorbing them. Default to take_mine. The moment their thefts exceed yours by two, play
  take_theirs until the ledger is level again, then stop the same beat it levels. When two of your
  coins are on the board and they are closer to one than you are, play guard and bank the one they
  can reach first — a coin you already hold cannot be taken. If the board is empty of your colour
  and full of theirs, hold rather than take_any: an unforced theft restarts a war you were winning
  quietly."*

### The scripted baselines (four, all fieldable, all env-switched)

**All four read the same `buildObservation(slot)` object an LLM seat receives — never raw sim
state.** That is what makes a baseline a legitimate policy, and `tests/test_baseline.nim` asserts it
by running each against a frozen observation with the sim inaccessible. Each returns **one intent
per beat**. Helpers, all computed from the observation: `theirThefts = them.thefts` (the coins of
YOUR colour they have taken, cumulatively), `theirTheftsInBeat(b)` from `beatLog`, and
`ownCoinExists` / `theirCoinExists` from `coins`.

| baseline | algorithm | Melting Pot bot it reproduces |
|---|---|---|
| `honest` | `take_mine` if `ownCoinExists`, else `hold`. Never steals, ever. | always-cooperate |
| `greedy` | `take_any`, every beat, unconditionally. | always-defect |
| **`reciprocator`** | State: `armed` (an integer threshold, initialised to `punishThreshold = 2`) and `punishUntil` (a beat number, initially 0). At each beat `b`: if `b ≤ punishUntil` play `take_theirs`. Else if `theirThefts ≥ armed`, set `punishUntil = b + punishBeats - 1` (`punishBeats = 4`), set `armed = theirThefts + punishThreshold`, and play `take_theirs`. Else play `take_mine` (or `hold` when no own coin exists). In words: **stay honest until they have stolen 2 coins; then take their coins for 4 beats; then go back to honest with the trigger re-armed at 2 more thefts.** | the idea's "reciprocating bot that starts punishing after N thefts", **N = 2**, forgiving rather than grim so a truce can re-form and be watched. |
| `tit-for-tat` | Beat 1: `take_mine`. Beat `b > 1`: `take_any` if `theirTheftsInBeat(b-1) ≥ 1`, else `take_mine` (or `hold` when no own coin exists). Beat-local mirror — the idea's "tit-for-tat in coin-space". | conditional resident |

`reciprocator` is the **fallback move** used whenever an LLM seat's decision fails (below), the
policy a never-connected seat plays, and the baseline the offline certification fixture leans on —
it is the strongest of the four against an unknown opponent and it guarantees the episode has both
thefts and truces in it.

### Degrade, never hang

- Batch timeout `llmTimeoutSeconds = 12`. On transport error, non-2xx, refusal, `max_tokens` before
  any `{`, unparseable JSON, or an `intent` outside the five, **that seat alone** is retried
  **once** in the same beat with the appended hint: *"Your previous reply was invalid. Respond with
  ONLY the requested JSON object. `intent` must be exactly one of take_mine, take_any, take_theirs,
  guard, hold."*
- Still failing → that seat plays **`reciprocator`'s intent** for that beat, logged as
  `coins llm: seat N falling back to scripted intent` and recorded on the `order` event as
  `"source":"fallback"`. `decideAll` never raises; the episode always advances.
- 401/403 disables the client for the rest of the episode (both seats scripted from then on); 429 is
  logged and that seat is retried in the next beat's batch.
- A seat whose socket never connected, or which disconnects mid-episode, plays `reciprocator` for
  every remaining beat. The episode never waits on it. Only *both* seats missing at
  `playerConnectTimeoutSeconds = 180` is a `forfeit`.
- **The episode settles early rather than overrunning.** The play deadline is checked at every beat
  close; crossing it calls `endEarly()`, which scores the beats actually played, writes
  `results.json` and the replay, and — as cogame-lantern taught — keeps `/healthz` and `/global`
  answering for `shutdownGraceSeconds = 20` before `quit(0)`, because hosted certification pings the
  global websocket **after** the player pods start.

---

## Sim module

New code lives in `src/coins/`, mirroring paintbot's split (`src/ctf/`). Binaries are `/bin/coins`
and `/bin/coins-player`. What is forked, what is kept, what is deleted:

| paintbot path | coins | note |
|---|---|---|
| `src/ctf/sim_types.nim` | `src/coins/sim_types.nim` | fork: `GameVersion`, the flatty wire types, `Cog`, `Coin`, the constants above. Field order is sacred, same as paintbot. |
| `src/ctf/sim.nim` | `src/coins/sim.nim` | fork: the tick loop and the eight numbered rules replace the CTF gameplay core. |
| `src/ctf/sim_config.nim` | `src/coins/sim_config.nim` | fork: `GameConfig` lifecycle + `config.update`; fields = the config schema in `## Packaging`. |
| `src/ctf/sim_state.nim` | `src/coins/sim_state.nim` | fork: logging, `gameHash`, event emission, the three seeded RNG streams (`coinRng`, `moveRng`, `endRng`). |
| `src/ctf/global.nim` | `src/coins/global.nim` | fork, heavily reduced: keep the sprite-protocol emitter, layer/object pooling, map bands, the chrome `TextMessage` smuggling and `boardRenderScaleFor`. **Delete** fog-of-war/FOV, the first-person PiP, articulated rigs beyond the standing cog, the grenade/spray/shield/barrier families, endzone bakes, perks and handicaps. |
| `src/ctf/broadcast.nim` | `src/coins/broadcast.nim` | fork: `BroadcastTracker` + `buildStateJson` keep their shape and key names (`## Viewer`); `teams` carries `red`/`blue` = Copper/Cobalt, `lead` carries the score series, and one game key `cn` is added. |
| `src/ctf/events.nim` | `src/coins/events.nim` | fork: the event vocabulary below. |
| `src/ctf/replays.nim`, `src/ctf/replay_runtime.nim` | `src/coins/replays.nim` | rewritten: Coins records **state frames**, not inputs (below), so playback never re-simulates and a seek is an array index. |
| `src/ctf/server.nim` | `src/coins/server.nim` | fork of the route/artifact/shutdown skeleton; the player protocol is bullwhip's JSON frames. |
| `src/ctf/map_art.nim` | `src/coins/map_art.nim` | fork, reduced to one baked room floor plus the shipped `client/art/walls/{wall_h,wall_v}.jpg` tiles. |
| `src/ctf.nim` | `src/coins.nim` | fork of the entrypoint: seed randomisation **before** `config.update` (paintbot's rule — every seed-derived draw, here all three RNG streams, must follow the final seed), same sentinel handling. |
| `src/ctf/arena.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `labels.nim`, `roster.nim` | — | deleted. One fixed 9 × 9 room, no generator, no perk roster, no label pipeline. |
| `tools/*probe*.nim`, `caos*/`, `arena/`, `client/league_replayer.html`, `tests/` (all of paintbot's) | — | deleted. **Kept:** `tools/build_replay_viewer.sh` (with the ecos `mkdir -p` fix and the image tag / `docker cp` path renamed) and `tools/gen_wire_constants.nim`. |

New files: `src/coins/room.nim` (the ASCII room), `src/coins/kernel.nim` (the five intents' per-tick
target/forbidden-colour kernel), `src/coins/scripted.nim` (the four baselines),
`src/coins/indices.nim` (theft counters, restraint, reciprocity lag, the truce rule),
`src/coins/llm.nim` (from `cogame-bullwhip/src/bullwhip/llm.nim`), `src/coins_player.nim` (from
`cogame-bullwhip/src/bullwhip_player.nim`).

### Event vocabulary (the replay's `events[]`)

One JSON row per event, `t` = tick, seats are slot integers, colours are the strings `copper` /
`cobalt`. **This is the complete vocabulary; nothing else is emitted.**

| `k` | fields | when |
|---|---|---|
| `order` | `t, beat, seat, intent, source ("llm"\|"retry"\|"fallback"\|"scripted"), say, notes, latencyMs` | one per seat per beat, at the beat boundary |
| `spawn` | `t, x, y, colour` | rule 6 |
| `pickup` | `t, seat, x, y, colour, score[2]` | rule 5, own-colour coin |
| `theft` | `t, seat, victim, x, y, colour, penalty, score[2]` | rule 5, other-colour coin |
| `blocked` | `t, seat, x, y, why ("restraint"\|"contested"\|"occupied")` | rule 3e |
| `truce` | `t, beat, seat, sinceBeat` | beat close, the truce rule |
| `leadchange` | `t, seat, score[2]` | rule 7 |
| `beatclose` | `t, beat, score[2], pickups[2], thefts[2]` | every beat close |
| `end` | `t, beat, reason, score[2]` | terminal, exactly one per episode |

`notes` is recorded (it is what makes an LLM seat's reasoning auditable in the replay) but is drawn
only in the feed's expanded row; `say` is the headline. Both are already rune-truncated.

### The replay file (`coins.replay.v1`)

**Strict UTF-8 JSON, one document**, written to `COGAME_SAVE_REPLAY_URI` with
`COGAME_SAVE_REPLAY_METHOD` and content type `application/json` (so `docker_smoke.sh` keeps its
default `SMOKE_REQUIRE_REPLAY_JSON=1`).

```json
{"protocol":"coins.replay.v1","game":"coins","gameVersion":"1","variant":"standard","seed":1234567,
 "names":["Copper","Cobalt"],
 "policyNames":["coins-truce","coins-reciprocator"],
 "colours":["copper","cobalt"],
 "config":{"ticksPerBeat":20,"minBeats":12,"maxBeats":24,"endChancePermille":120,
           "coinCap":8,"coinSpawnIntervalTicks":12,"initialCoins":6,
           "pickupReward":1,"theftPenalty":2,"stepCooldownTicks":3,
           "punishThreshold":2,"punishBeats":4,"truceBeats":3,"fps":24},
 "room":{"w":9,"h":9,"walls":["#########","#.......#","…9 rows…"]},
 "beats":18,"endBeat":18,"ticksPlayed":360,
 "frames":[{"t":0,"c":[1,1,2, 7,7,0],
            "k":[3,2,0, 5,6,1,"…one (x,y,colourIndex) triple per coin on the board…"],
            "sc":[0,0],"th":[0,0]}, "…360 frames…"],
 "series":{"score":[[0,0,0],"…one row per tick: [t, score0, score1]…"],
           "beatThefts":[[1,0,0],[2,0,1],"…one row per beat: [beat, thefts0InBeat, thefts1InBeat]…"]},
 "indices":{"pickups":[13,12],"thefts":[2,5],"stolenFrom":[5,2],
            "restraint":[0.846,0.583],"firstTheftBeat":[9,5],"reciprocityLagBeats":[4,null]},
 "events":[ "…" ],
 "results":{ "… the results.json object verbatim …" }}
```

- `frames[i].c` is a flat integer triple per seat `(x, y, facing)`; `k` is a flat integer triple per
  coin `(x, y, colourIndex)` with `colourIndex` 0 = copper, 1 = cobalt; `sc` and `th` are the two
  seats' running score and theft counters. No ids and no floats anywhere in `frames`.
- **Replay bytes are self-sufficient (pin).** Aliases, **policy names**, colours, the variant, the
  **whole config** including every constant the viewer needs, the **seed**, the room, **per-tick
  state**, the beat and end-beat, both series, the index summary, every event and the full `results`
  object are all in the file. The viewer re-derives every frame from these bytes; **no server is
  contacted except S3 for the `.replay` file.**
- Size arithmetic: 480 frames × (6 + ≤ 24 + 4 ≈ 34 integers × ~4 chars) ≈ **70 KB**, plus ~600 events
  ≈ 60 KB. `tests/test_replay.nim` asserts `< 4 MiB`.

### The game has to be the dilemma it claims

A coins room whose payoffs are not a Prisoner's Dilemma is a dead coworld, so the ordering is
asserted in CI (`tests/test_dilemma.nim`), not assumed. The arithmetic that motivates the tuning,
for a full-length 480-tick episode with 46 coins spawned (23 of each colour on average) and two cogs
that can each reach a coin roughly every 12 ticks — i.e. **supply-limited, not speed-limited**:

| pairing | pickups (Copper / Cobalt) | thefts | scores | payoff role |
|---|---|---|---|---|
| both `honest` | 23 / 23 (each takes only its own colour, uncontested) | 0 / 0 | **23 / 23** | **R** (mutual restraint) |
| `greedy` vs `honest` | 34 / 12 (Copper takes all 23 copper plus about half the cobalt) | 11 / 0 | **34 / −10** | **T / S** |
| both `greedy` | 23 / 23 (46 coins split evenly, half of each haul stolen) | ~11 / ~11 | **~1 / ~1** | **P** (mutual-harm trap) |

`T (34) > R (23) > P (~1) > S (−10)`, and `2R (46) > T + S (24)` — a textbook Prisoner's Dilemma in
which mutual restraint is also the efficient outcome, exactly what the idea asks for. Taking a coin
is *always* individually +1, so greed is a dominant one-shot move; only the random-end shadow of the
future makes restraint rational, which is why `minBeats` is 12 and not 1.

`tests/test_dilemma.nim` asserts the **ordering**, not these estimates, over seeds 1..8 at cert
length:

- **(a)** `honest` vs `honest`: both scores strictly positive, both `thefts == 0`, mean ≥ 10.
- **(b)** `greedy` vs `greedy`: both scores strictly below the `honest`/`honest` mean, and the mean
  is below 5 (the mutual-harm trap).
- **(c)** `greedy` vs `honest`: the greedy seat strictly outscores the `honest`/`honest` mean
  (temptation) **and** the honest seat's score is strictly negative (the sucker payoff).
- **(d)** `greedy` vs `reciprocator`: the reciprocator's score is strictly greater than the honest
  seat's score against `greedy` on the same seed — punishment beats pacifism, which is the property
  that makes the Melting Pot scoring bot a fair grader.
- **(e)** Liveness: every episode has ≥ 20 total pickups, both cogs pick up ≥ 1 coin, and at least
  one `theft` and one `truce` event occur in the `greedy`-vs-`reciprocator` sweep — otherwise the
  replay has no story and the reciprocity timeline is empty.
- **(f)** The score identity `score[i] == pickups[i] - 2 * stolenFrom[i]` holds at every tick.

---

## Server, player, protocol

### Game container (`/bin/coins`)

Routes, kept from paintbot's `src/ctf/server.nim` because hosted certification probes exactly these
**before** the player pods start (the lantern learning):

| route | behaviour |
|---|---|
| `GET /healthz` | `200 ok`, from process start until `shutdownGraceSeconds` after the artifacts are written |
| `GET /client/player?slot=N&token=T` | the seat's HTML shell (paintbot's, trimmed). **Never opens the player websocket.** |
| `WS /player?slot=N&token=T` | the seat socket; a bad token is refused with a close frame, never a hang |
| `GET /client/global` | the broadcast client (`client/replay_broadcast.html`, embedded with `staticRead`) |
| `WS /global` | live spectator: paintbot's sprite protocol + the chrome `TextMessage` |

Both `/client/` routes are registered **before** any catch-all asset route.

`coins.player.v1` frames, JSON text, bullwhip shapes:

- game → player: `{"type":"welcome","protocol":"coins.player.v1","slot":0,"alias":"Copper","colour":"copper","opponent":"Cobalt","ticksPerBeat":20,"minBeats":12,"maxBeats":24}` on connect;
  the `state` frame of `## Decisions` at every beat close and once at episode end;
  `{"type":"final","done":true,"slot":0,"scores":[11.0,4.0],"names":["Copper","Cobalt"],"beats":18,"reason":"random_end"}`,
  after which the player exits **0**.
- player → game: `{"type":"prompt","prompt":"<= 4000 chars","scripted":"honest|greedy|reciprocator|tit-for-tat|"}`,
  sent immediately on connect and again after `welcome` (the re-send guards the slot-registration
  race). Any other frame is ignored with a log line.

**Startup:** `src/coins.nim` randomises the seed **before** `config.update`, waits up to
`playerConnectTimeoutSeconds = 180` for two sockets, starts anyway with whoever is there (a missing
seat plays `reciprocator`), issues the opening decision batch, then runs the beat loop.

**Shutdown**, in this order (bullwhip's `finishEpisode` plus lantern's grace): send `final` to every
player socket → broadcast the last global frame → `sleep 500 ms` → write `results.json`
(`COGAME_RESULTS_METHOD`, `application/json`) → write the replay → keep `/healthz` and `/global`
answering for `shutdownGraceSeconds = 20` → `quit(0)`. The player's receive loop wraps
`receiveMessage` in `try/except CatchableError` and exits **0** on a closed or truncated frame (the
raid learning — otherwise `docker_smoke` passes and hosted certification fails intermittently).

### `results.json`

```json
{"names":["coins-truce","coins-reciprocator"],
 "scores":[11.0,4.0],
 "win":[true,false],
 "aliases":["Copper","Cobalt"],
 "colours":["copper","cobalt"],
 "pickups":[13,12],
 "thefts":[2,5],
 "stolenFrom":[5,2],
 "restraint":[0.846,0.583],
 "firstTheftBeat":[9,5],
 "reciprocityLagBeats":[4,null],
 "beats":18,"endBeat":18,"ticks":360,
 "reason":"random_end"}
```

`names` are **policy** names (platform side); aliases go to the players and into the replay's
`names[]`. Every array is indexed by slot and is always length **2**.
`restraint[i] = (pickups[i] - thefts[i]) / pickups[i]` in `[0, 1]`, **`null`** when
`pickups[i] == 0`. `firstTheftBeat[i]` is the beat of seat `i`'s first theft, **`null`** if it never
stole. `reciprocityLagBeats[i] = firstTheftBeat[i] - firstTheftBeat[1-i]` when both are non-null,
**`null`** otherwise — negative means seat `i` stole first, positive means it retaliated after that
many beats. `reason` is one of the four legal values in `## The game`. The results schema declares
`["number","null"]` for the items of `restraint`, `firstTheftBeat` and `reciprocityLagBeats`.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and no `/client/replay` viewer is declared
anywhere. `tools/build_replay_viewer.sh` is coworld-ctf's script, kept, with three edits: `image_tag`
renamed to `cogame-coins-replay-viewer-build:$$`, the `docker cp` source path changed to
`/workspace/coins/replay-viewer/dist/.`, and the **ecos `mkdir -p "$(dirname "${requested_output}")"`
fix applied before the containment check** (paintbot's hook exits 1 on a fresh CI checkout without
it). It stays committed **executable** — `coworld build` hard-requires `os.X_OK` on the build hook.

### One starter supplies all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and from no other starter.** Named
explicitly, because splicing one starter's shell onto another's emscripten link flags is what left
cogame-lantern with a viewer that deadlocked silently and a permanently blank theater:

| file | source (coworld-ctf) | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | verbatim except the emitted name (`coins_replay.js`) and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_coins_*`. **Keep the link flags exactly as they are — no `-s MODULARIZE=1`, no `EXPORT_NAME`** — because the worker below bootstraps with `Module.onRuntimeInitialized`. Keep `-s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8`, `-d:useMalloc` and `--preload-file <root>/data@data`. |
| the wasm entry `.nim` | `replay-viewer/ctf_replay.nim` → `replay-viewer/coins_replay.nim` | same structure and the same safety furniture: the `stageNote` buffer + `stampStage` calls, the `ABORTING_MALLOC` rationale, and the `emscripten_exit_with_live_runtime()` epilogue (without it Nim's `main` destroys every module global while JS keeps calling in). Exports `coins_load_replay`, `coins_frame`, `coins_input`, `coins_packet_ptr`, `coins_packet_len`, `coins_error_ptr`, `coins_error_len`, `coins_stage_ptr`, `coins_stage_len`. `ctf_mismatch_tick` is **dropped** — Coins records state, so there is no re-simulation to mismatch. The 9 × 9 board is orders of magnitude under `WasmViewerBudgetBytes`, so the capacity check is kept but never trips. |
| `static_replay*.js` | `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js` | verbatim apart from the `ctf_*` → `coins_*` export names and the worker name string (`coins-static-replay`), plus **one added line** in `showFailure` (below). The worker keeps `importScripts('./wire_constants.js','./broadcast_core.js','./coins_replay.js')` and the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` bootstrap — the matched pair for the link flags above. |
| `index.html` | `client/replay_broadcast.html`, spliced by `Dockerfile.replay-viewer`'s `sed` over the `<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->` and `<!-- BROADCAST_CORE -->` markers into `replay-viewer/dist/index.html` | chrome kept verbatim, game block appended (below). |

`static_replay.js` already sets
`document.documentElement.setAttribute('data-replay-loaded', 'true')` when the worker reports its
first drawn frame (line 144 of the starter's file) — that line is kept unchanged. The one addition
is in `showFailure()`:
`document.documentElement.setAttribute('data-replay-error', error.message || String(error))`, set
before the `#status` line renders. **So the shell sets `data-replay-loaded="true"` on its first
drawn frame and `data-replay-error` on failure.** Those two attributes are exactly what
`tools/ci/viewer_smoke.mjs` and phase 60's `viewer-check.yml` read. The `coworld-replay` bridge's
`ready` post is fired from the callback that runs **after** `data-replay-loaded="true"` is set (the
chorus fix — posting `ready` on rAF timing lets softmax.com sample an unpainted shell).

### Chrome provenance: copied, appended, removed

- **`client/chrome_common.js` is copied BYTE-FOR-BYTE from `coworld-ctf`. Zero edits.** Its
  CTF-specific paths (perks, handicaps, lives, flag story, POV) stay in the file and are inert
  because the corresponding state fields are simply absent from this stream. The chrome frame
  **keeps ctf's key names** — `t, mt, ph, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams,
  roster, events, lead, beats, lulls, over, hold` — so chrome_common's clock, transport, scrubber,
  beat markers, lull spans, momentum curve, spoilers gate and endcard machinery run **unmodified**.
  `teams` carries exactly two keys, `red` (Copper) and `blue` (Cobalt), each holding
  `{score, pickups, thefts, stolenFrom, policies}`; `roster` carries the two seats. One game key is
  added, `cn = {"beat":7,"beats":18,"recip":[[1,0,0],…],"truce":[[b,seat],…],"coinsOnBoard":2}`,
  read only by the appended game block.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one
  `<style>` and one `<script>` at the very end of the file, injecting Coins readouts into the
  existing containers. Nothing above them is rewritten: the CSS variables, `relayout()`
  (`client/replay_broadcast.html:4110`), the transport, the endcard (`:1036–1048`), the locker-room
  loader and the `?embed=1` mode are the starter's, untouched. **This is not a from-scratch page
  that reuses the starter's ids** (the cogame-gridlock failure).
- Every function the game block defines at top level is prefixed **`cn`** (`cnBuildPlates`,
  `cnRenderRecip`, `cnPushRow`, `cnMarkBeat`). Deliberate: a game-block `function markBeat` gets
  hoisted over the chrome alias block's `var markBeat = C.markBeat`, and the scrubber then silently
  renders unlabeled, unclickable divs (the tandem bug). `tests/test_viewer.nim` asserts that no
  game-block top-level name appears in the chrome alias list.
- **Removed starter elements (exactly these):** `#viewpanel` and its children `#minimap`,
  `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`; `#fpv` and
  its children `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`; `#povBadge`; and `#mmwarn`.
  **Zoom decision: the room is a FIXED arena — 9 × 9 cells, 504 × 504 px, never larger than the
  frame in any variant — so `#viewpanel` (the zoom bar and the minimap) is dropped entirely**, per
  the rule that it exists only for boards larger than the frame. `broadcast_core.js`'s zoom/pan/
  minimap code stays in the file, verbatim, simply never driven. `#mmwarn` goes because there is no
  re-simulation and therefore no hash mismatch.
- **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (re-captioned
  "Minting the coins…", art from `client/art/lockerroom/{bg.jpg,red_1.webp,blue_1.webp}`),
  `#chrome`, `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`/
  `#ffwd-mini`, `#bannerlane`, `#killfeed`, `#transport` with every button, `#ffwd-chip`,
  `#win-chip`, `#tick-clock`, `#speedchips`, `#scrub`, `#momentum`, `#lulls`, `#scrub-fill`,
  `#scrub-win`, `#scrub-head`, `#endcard` with its `ec-*` children, `#status`.
- **Added by the game block, all inside `#chrome`, none in the transport band:** `#cn-recip` (the
  reciprocity timeline, pinned `top: calc(var(--topband) + 8 * var(--u))`, right edge) and
  `#cn-thefts` (the two-cog theft counter headline, directly under the scorebug band, left edge).

### Transport rules

- `relayout()` is kept **verbatim**: it sets **`--hudscale`** and **`--band`** (and `--topband`) on
  `:root` by fixed-point iteration (`client/replay_broadcast.html:4126–4151`), so the board is
  letterboxed between the scorebug band and the transport band, and every chrome measure derives
  from `--u: calc(1px * var(--hudscale))`.
- **No overlay sits in the transport band.** `#cn-recip`, `#cn-thefts` and every banner the game
  block raises are positioned inside `#chrome` with `bottom: calc(var(--band) + N * var(--u))` or a
  `--topband`-relative `top`, never over the band.
- The **endcard stops at `var(--band)`** — the starter's `#endcard { top: var(--topband); bottom:
  var(--band) }` rule is kept unchanged — and is **dismissed by every seek**, which is the starter's
  behaviour, kept.
- **Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">` elements.** The
  game block upgrades chrome_common's `renderBeatMarkers` divs to buttons carrying `aria-label` and
  `title` (e.g. "Theft — Cobalt takes a copper coin, 5.8 s, +1 / −2") and seeking to that tick on
  click. **CSS exists for every kind emitted**: `.beat-marker.theft`, `.beat-marker.truce`,
  `.beat-marker.leadchange`, `.beat-marker.over` — one rule per kind, asserted by
  `tests/test_viewer.nim`. The `beats` timeline is shipped whole on the first HUD frame as
  `beats = [{"t":…, "k":"theft"|"truce"|"leadchange"|"over", "seat":…, "team":"red"|"blue"}, …]`:
  one `theft` row per `theft` event, one `truce` row per `truce` event, one `leadchange` row per
  `leadchange`, and one `over` row at the final tick. **Those four are the only kinds emitted**,
  which is what makes "a CSS rule per kind" a closed assertion. `lulls` spans are emitted for every
  stretch of ≥ 40 ticks with no `pickup` and no `theft`, so the starter's auto-skip button has
  something real to skip.

### What it draws (the readouts)

1. **Board.** The baked room floor (a worn tiled vault floor with a faint chalk grid) under the
   shipped wall tiles; coins as struck coin faces in their colour with a mint sheen and a slow
   idle spin; the two cogs in their liveries, facing shown by the sprite heading, interpolated
   between ticks at 24 fps. A cog that steps around a coin it refuses (a `blocked`
   `why: "restraint"`) shows a brief hand-off glyph over that coin — the restraint is *seen*.
2. **Scorebug plates** (`#scorebug`): two plates, Copper in `#plates-l` and Cobalt in `#plates-r`,
   built by `cnBuildPlates` from `teams` + `roster`. Each plate is a colour chip, the **policy
   name**, the score in large digits, and — the idea's headline readout — **`STOLE n`, the per-cog
   theft counter**, which flashes on every `theft` event.
3. **Clock** (`#clock-time`, `#clock-caption`): `BEAT 7 / 18` with the caption `tick 140 of 360 ·
   2 coins on the board` — spelled out, never `B7`.
4. **`#cn-recip` — the reciprocity timeline.** Two rows, Copper above Cobalt, one narrow cell per
   beat across the width of the panel, fed from `cn.recip` (`[beat, thefts0InBeat, thefts1InBeat]`).
   A cell is dim slate for 0 thefts, amber for 1, and the cog's own colour at full brightness for
   ≥ 2. A `truce` beat plants a white flag notch on that cog's row. The playhead beat is outlined.
   Read left to right, the strip is the whole social history of the episode in one object: who
   started it, how fast the other answered, and where — the idea's beat — one cog stopped.
5. **`#cn-thefts`**: `COPPER STOLE 2 · COBALT STOLE 5` in the two colours, with the running
   restraint percentage under each.
6. **Feed** (`#killfeed`): plain language, one row per event that matters —
   `COPPER takes a copper coin  +1`,
   `COBALT STEALS a copper coin  +1 COBALT / −2 COPPER`,
   `COPPER: hold  "your coins are yours"`,
   `TRUCE — COBALT has left copper alone for 3 beats`.
   Rows whose `order.source` is `fallback` are tagged `auto`, so a spectator can see when a seat's
   LLM missed and the scripted move played instead.
7. **Momentum strip** (`#momentum`, label re-lettered `SCORE LEAD`): chrome_common's
   `ingestLeadSeries` / `renderMomentum` fed by `lead = {"teams":["red","blue"],"pts":[[t, score0,
   score1], …]}` from `series.score`, shipped whole on frame 1 so the curve draws its full width
   immediately (paintbot's `lead` trick).
8. **Bannerlane** (`#bannerlane`): a chip for the first theft of the episode (`FIRST THEFT —
   COBALT`), for every `truce` (`TRUCE — COBALT`), and for every lead change.
9. **Transport**: paintbot's play/pause, step-back, +5 s, jump-to-end, loop, skip-lulls, spoilers,
   speed chips, scrubber with beat markers, tick readout and end-hold countdown — all verbatim.
10. **Endcard**: `COINS-TRUCE HOLDS THE ROOM` / `18 BEATS · ENDED AT RANDOM · 25 COINS`, a two-row
    table (policy name · score · coins taken · thefts · stolen from · restraint) and the final
    reciprocity strip at full width. Rendered into the starter's `#ec-headline`, `#ec-wincond`,
    `#ec-how` and `#ec-teams`; the show/hide, the `bottom: var(--band)` bound and the seek-dismissal
    are the starter's, unchanged.

### Art

**Real art, not placeholders.** `scripts/art/gen_coins_art.py` (Pillow, committed, deterministic,
re-runnable) renders and commits into `data/`:

- `data/rig_coins/{copper,cobalt}/*` — the two cog liveries, retinted from paintbot's shipped
  `data/rig_real/{red,blue}/*` rigs to `#e0523a` and `#3f7cc4` (the repo already ships
  `scripts/art/retint_team_props.py` for exactly this), each with a small purse decal in its colour.
- `data/coin_copper.png`, `data/coin_cobalt.png` — struck coin faces, 40 px, with a milled rim, a
  raised device (a spark for copper, a crescent for cobalt) and a specular sheen; plus
  `data/coin_copper_spin.png` / `data/coin_cobalt_spin.png` (a 4-frame edge-on spin strip).
- `data/room_floor.png` — the tiled vault-floor bake; walls reuse the shipped
  `client/art/walls/{wall_h,wall_v}.jpg`.
- `data/pickup_spark.png`, `data/theft_burst.png` (a cracked-coin flash in the victim's colour),
  `data/decline_glyph.png` (the restraint hand-off).
- The loading art the `#lockerroom` markup expects: `client/art/lockerroom/bg.jpg` (a dim mint
  floor) plus the `red_1.webp` / `blue_1.webp` portraits the starter references.

No solid-colour placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter engineers most of it: `relayout()` sets `--hudscale` from the board width
and toggles `#stage.tiny` at `boardW ≤ 620` — kept verbatim. The game block adds three rules of its
own:

- `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
  policy name never collapses to "…";
- under `.tiny`, each plate keeps the colour chip, the score and `STOLE n` and drops the restraint
  percentage — two plates plus the clock still fit one line at 360 px;
- under `.tiny`, `#cn-recip` drops its beat numbers and halves its cell height (the two coloured
  rows survive, which is the readout that matters), and `#cn-thefts` shortens to `2 ✦ 5`.

`tests/test_viewer.nim` asserts all three rules are present, and the 360 px screenshot is part of
the phase 60 viewer check.

---

## Packaging

**`compose.yaml`** — one service, one image (game + player binaries):

```yaml
services:
  game:
    image: cogame-coins:latest
    platform: linux/amd64
    build: {context: ., dockerfile: Dockerfile, network: host}
```

The service name is the single source of the manifest image placeholder: `services.game` →
**`{{GAME_IMAGE}}`** (`coworld build` derives the placeholder from the compose service name and
hard-fails anything else — the lantern learning). `tests/test_manifest.nim` asserts the derivation
`placeholder == service.toUpperAscii() & "_IMAGE"` against the parsed `compose.yaml`.

**`coworld_manifest_template.json`** — bullwhip's shape with the 0.1.42 strictness hive found:
top-level `$schema`, ≥ 3 `tags` (`social-dilemma`, `melting-pot`, `two-player`, `grid`,
`llm-driven`, `prisoners-dilemma`), top-level `episode_timeout_minutes: 20`, top-level `player[]`,
a `description` on **every** variant, `game.runnable.type: "game"`, and a real JSON-Schema
`game.config_schema` in which **every array property carries `minItems`/`maxItems`** (the tandem
certification failure).

- `game.name`: `coins`; `game.replay_viewer.bundle`: **`static-replay-viewer`**.
- `game.runnable`: `{"type":"game","image":"{{GAME_IMAGE}}","run":["/bin/coins"],
  "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/coins/anthropic_api_key"},
  "source_url":"https://github.com/Metta-AI/cogame-coins/tree/main"}` — the `env` entry is
  mandatory: without it the hosted **game** container never sees the coworld secret and every league
  episode silently plays scripted (hive learning 2), which surfaces only as a phase-60 check-4
  failure.
- `game.config_schema` properties, `additionalProperties: false`: `tokens` (string array,
  `minItems: 2`, `maxItems: 2`, required), `players` (object array of `{name}`, `minItems: 2`,
  `maxItems: 2`, required), **`num_agents` (integer, `minimum: 2`, `maximum: 2`, default `2`)**,
  `seed` (integer), `ticksPerBeat` (10..60, default 20), `minBeats` (1..24, default 12), `maxBeats`
  (1..24, default 24), `endChancePermille` (0..1000, default 120), `coinCap` (2..24, default 8),
  `coinSpawnIntervalTicks` (2..60, default 12), `initialCoins` (0..24, default 6), `pickupReward`
  (1..5, default 1), `theftPenalty` (0..10, default 2), `stepCooldownTicks` (1..10, default 3),
  `punishThreshold` (1..10, default 2), `punishBeats` (1..10, default 4), `truceBeats` (1..10,
  default 3), `llmTimeoutSeconds` (default 12), `minBeatSeconds` (default 5), `maxOutputTokens`
  (default 500), `model` (string), `episodeTimeoutSeconds` (default 1200),
  `playerConnectTimeoutSeconds` (default 180), `shutdownGraceSeconds` (default 20).
- `game.results_schema`: the `results.json` object above, with `["number","null"]` on the items of
  `restraint`, `firstTheftBeat` and `reciprocityLagBeats`, and `minItems: 2`/`maxItems: 2` on every
  per-seat array.
- **`game.docs`** (**text**, not uri): `{"readme":{"type":"text","value":"<the 200-word what-it-is>"},
  "pages":[
  `{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<the room, coins, the eight numbered tick rules, the intents, the scoring formula, the random end>"}}`,
  `{"id":"policies.md","title":"Fielding a policy","content":{"type":"text","value":"<PLAYER_PROMPT / PLAYER_SCRIPTED how-to, the observation, the reply schema and its 48/300 rune caps>"}}`
  `]}` — **`readme` plus a non-empty `pages`.**
- **`game.protocols` — BOTH `player` and `global`**, each a `{"type":"text","value":…}` object (bare
  strings fail the platform validator, the garble trap): `player` documents the `coins.player.v1`
  frames, the observation and the reply schema with its caps; `global` documents the `/global`
  sprite + chrome frame and the static bundle's `index.html?replay=<url>`.
- **`player[]` — exactly TWO entries**, both on `{{GAME_IMAGE}}` with `run: ["/bin/coins-player"]`:
  `coins-player` (no env — a prompt policy; `PLAYER_PROMPT` is supplied at upload time) and
  `coins-reciprocator` (`env: {"PLAYER_SCRIPTED":"reciprocator"}`). **Exactly two, because
  certification's `players-run` seats the whole manifest roster and this is a two-seat game**: a
  third declared entry could not be seated in a 2-seat fixture and would fail `players_missing`
  (the raid learning). The other three baselines (`honest`, `greedy`, `tit-for-tat`) are reachable
  through `PLAYER_SCRIPTED` on uploaded **policies**, which carry their own `run` + `env` and do not
  need a manifest `player[]` entry.
- **`variants[]` — five, and `num_agents: 2` in EVERY ONE.** All five share
  `{"players":[{"name":"Copper"},{"name":"Cobalt"}], "num_agents": 2, "ticksPerBeat": 20,
  "stepCooldownTicks": 3, "seed": 679961}` and differ only in the fields named:

  | id | `num_agents` | differing fields | worst-case wall clock | description |
  |---|---|---|---|---|
  | `standard` (**default**) | **2** | `minBeats 12, maxBeats 24, endChancePermille 120, coinCap 8, coinSpawnIntervalTicks 12, initialCoins 6, theftPenalty 2` | 24 × 24 s = 576 s | The base dilemma: a coin-starved room, a random end after beat 12. |
  | `long-shadow` | **2** | `minBeats 18, maxBeats 24, endChancePermille 60` | 576 s | A long shadow of the future — restraint is much easier to sustain. |
  | `short-fuse` | **2** | `minBeats 6, maxBeats 14, endChancePermille 250` | 14 × 24 s = 336 s | The end comes early and often: endgame grabs are rational sooner. |
  | `harsh` | **2** | `theftPenalty 3` | 576 s | Every theft costs the victim 3, so the mutual-harm trap is deeper. |
  | `scarce` | **2** | `coinCap 4, coinSpawnIntervalTicks 20, initialCoins 3` | 576 s | Barely any coins: every single spawn is a decision both cogs are watching. |

- **`certification`**: `game_config` =
  `{"num_agents": 2, "seed": 7, "minBeats": 16, "maxBeats": 16, "ticksPerBeat": 20, "coinCap": 8,
  "coinSpawnIntervalTicks": 12, "initialCoins": 6, "playerConnectTimeoutSeconds": 180,
  "players": [{"name":"Copper"},{"name":"Cobalt"}]}` and `players` =
  `[{"player_id":"coins-player"},{"player_id":"coins-reciprocator"}]` — **two seats,
  `num_agents: 2`**, and **every declared `player[]` id seated**. `minBeats == maxBeats` disables the
  random-end draw, so the fixture is exactly **16 beats × 20 ticks = 320 ticks = 13.3 s of replay**,
  deliberately longer than the 10 s viewer soak (the ecos learning), and it ends with
  `reason: "beat_cap"`. Offline, `coins-player` has no credentials, disables its LLM client and
  plays `reciprocator`, so the fixture is deterministic.

**Other packaging files:** `Dockerfile` (paintbot's two-stage nimby build, producing `/bin/coins`
and `/bin/coins-player`), `Dockerfile.replay-viewer` (paintbot's, with the Coins file list and the
same `test -f` / `grep -q` assertions on `index.html`, the `.wasm`, `chrome_common.js` and
`wire_constants.js`), `tools/build_replay_viewer.sh` (above),
`.github/workflows/ci.yml` and `.github/workflows/coworld-release.yml` from
`coworld-builder/templates/`, `tools/ci/docker_smoke.sh` from `coworld-builder/templates/tools/ci/`
with `<slug>` = `coins`, `<IMAGE>` = `cogame-coins` and **`<SEATS>` = `2`**,
`tools/ci/viewer_smoke.mjs` copied with **no substitutions**, and `tools/ci/policies.json` naming
`coins-truce` (champion #1), `coins-ledger` (champion #2,
`"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `coins-reciprocator` and `coins-titfortat`
(the two fillers, `PLAYER_SCRIPTED=reciprocator` and `PLAYER_SCRIPTED=tit-for-tat`). Both champion
entries carry `env: {"PLAYER_PROMPT": "<the prompt above>", "USE_BEDROCK": "true"}`; all four use
`"run": "/bin/coins-player"`.

---

## Tests

All run in `ci.yml`; the sandbox cannot run any of them locally.

1. **`tests/test_sim.nim` — sim units.** The scoring formula in both directions (own-colour pickup:
   `+1` to the collector and no change to the other; other-colour pickup: `+1` to the collector and
   `−theftPenalty` to the victim) including a case that drives a score negative; the identity
   `score[i] == pickups[i] - theftPenalty * stolenFrom[i]` after 480 ticks; the movement rules —
   wall and out-of-bounds rejection, the no-follow-through rule, the swap rule (both wait), the
   same-target contest resolved by `moveRng` with a pinned seed and pinned winner, the restraint
   block and the sidestep that guarantees no deadlock, `stepCooldownTicks` charged only on an actual
   move and **not** charged to the loser of a contest; the coin spawn cadence, the cap, and that a
   coin never spawns under a cog or on an occupied cell; the five intents' target selection
   including every tie-break and every "no coin qualifies" fallback; the truce rule firing at
   exactly `truceBeats` and re-arming after a later theft; the random end — with a pinned seed the
   drawn end beat is a fixed value, `minBeats == maxBeats` skips the draw entirely, and the draw
   stream is unaffected by the number of coin spawns; and **determinism** — the same seed and the
   same intent script produce an identical `gameHash` after 480 ticks, twice in one process and
   across a fresh `SimServer`.
2. **`tests/test_baseline.nim` — bounded orders / legality.** For all four baselines × all five
   variants × seeds 1..8, both seats scripted: every emitted order carries an `intent` in the legal
   five and **nothing else**; each baseline reads **only** `buildObservation(slot)` (asserted by
   running it against a frozen observation object with the raw sim inaccessible); no cog ever
   occupies a wall cell, leaves the interior, or shares a cell with the other cog; no coin is ever
   collected twice; no baseline raises; no baseline takes longer than 1 ms per beat; and the
   `honest` baseline's `thefts` is **0** in every one of those episodes (its restraint is an
   invariant, not a tendency).
3. **`tests/test_dilemma.nim` — the game-shape oracle.** Gates (a)–(f) of `## Sim module` §The game
   has to be the dilemma it claims, in Nim, over seeds 1..8 at cert length: the `T > R > P > S`
   ordering, the sucker payoff being negative, punishment beating pacifism, the liveness floor
   (≥ 20 pickups, both cogs ≥ 1, ≥ 1 theft and ≥ 1 truce in the reciprocator sweep), and the score
   identity. Any constant change that turns Coins into a Chicken game, or into a room where nothing
   happens, fails here rather than in a dead replay.
4. **`tests/test_replay.nim` — end-to-end + strict UTF-8.** Plays a full scripted episode headless,
   writes `results.json` and the replay, then re-reads the replay **bytes**: `validateUtf8 == -1`
   (strict), parses as JSON, `protocol == "coins.replay.v1"`, `frames.len == ticksPlayed`,
   `series.score.len == ticksPlayed`, `series.beatThefts.len == beats`, every event tick in
   `0..ticksPlayed`, at least one `spawn`, one `pickup`, one `theft` and one `order` per seat per
   beat, exactly `beats` `beatclose` events and exactly one `end`, `results.scores.len == 2`,
   `results.reason` in `{random_end, beat_cap, deadline, forfeit}`,
   `names.len == policyNames.len == 2`, `config` and `seed` present, `room.walls` present, file size
   `< 4 MiB`. A seat is fed a `say`/`notes` of multi-byte runes exactly at the **48 / 300** caps and
   the recorded strings are asserted valid UTF-8 and ≤ the cap in **runes** (the bullwhip
   byte-truncation bug).
5. **`tests/test_llm.nim` — decision layer.** `extractJsonObject` on fenced, prose-prefixed and
   trailing-prose replies; case-insensitive intent matching; an unknown `intent` → invalid → **one**
   retry → `reciprocator` fallback recorded with `source: "fallback"`; a stubbed transport that
   times out, 429s, 403s or returns junk never raises and always yields a legal intent; and **one
   batch carries every open seat** (assert `RequestBatch.len == openSeats` and that consecutive
   batch starts are ≥ `minBeatSeconds` apart).
6. **`tests/test_manifest.nim` — packaging.** **`num_agents == 2` in all five variants and in
   `certification.game_config`**; `certification.players.len == 2`; the image placeholder equals the
   one derived from `compose.yaml`'s service name (`{{GAME_IMAGE}}`);
   `replay_viewer.bundle == "static-replay-viewer"` and no `/client/replay` viewer is declared;
   `game.docs.readme` present **and** `game.docs.pages` non-empty; `game.protocols.player` **and**
   `game.protocols.global` both present and both `{"type":"text","value":…}` objects;
   `ANTHROPIC_API_KEY_URI` in `game.runnable.env`; `game.runnable.type == "game"`; top-level
   `episode_timeout_minutes`; ≥ 3 `tags`; every array property in `config_schema` carries `minItems`
   and `maxItems`; **every `player[]` id appears at least once in `certification.players`**; every
   variant carries a `description`; and every variant's `maxBeats × (2 × llmTimeoutSeconds)` is
   `< 0.6 × episodeTimeoutSeconds` (the budget assertion, checked from the manifest itself).
7. **`tests/test_viewer.nim` — chrome frame + game block.** `buildStateJson` emits exactly the
   chrome key set (`t, mt, ph, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams, roster, events,
   lead, beats, lulls, over, hold`) plus `cn`; `teams` keys are exactly `red` and `blue`; `lead.pts`
   rows are `[t, score0, score1]`; `roster` has 2 entries carrying policy name, colour and score;
   `over` is present on the terminal frame; a `.beat-marker` CSS rule exists for **every** beat kind
   emitted (`theft`, `truce`, `leadchange`, `over`) and the kinds emitted are exactly those four;
   the beat markers are `<button>` elements with an `aria-label`; the `.plate-name` and two `.tiny`
   rules are present; `#viewpanel`, `#fpv`, `#povBadge` and `#mmwarn` are absent from the built
   page; `chrome_common.js` in the bundle is **byte-identical** to `client/chrome_common.js`; and
   **no game-block top-level identifier collides with the chrome alias list** exported by
   `chrome_common.js` (the tandem hoisting bug).
8. **`docker-smoke` (`tools/ci/docker_smoke.sh`, `SMOKE_SEATS = 2`).** Builds the production image,
   runs a real **2-seat** episode in raw docker from the certification fixture, asserts the game
   **and every player** container exits 0 (the raid learning), validates `results.json` (2 names,
   2 scores, a legal `reason`), asserts the replay parses as UTF-8 JSON, and copies it to
   `SMOKE_REPLAY_OUT` (`dist/smoke/replay.json`), uploaded as the `smoke-replay` artifact. Its
   independent seat-count cross-check (`SEAT-COUNT FAIL:`) is the second place `num_agents = 2` is
   enforced — this note and the manifest must agree or the job goes red.
9. **`wasm-viewer` job — the bundle is EXECUTED, not merely built.** `needs: docker-smoke`,
   downloads the `smoke-replay` artifact, builds the bundle via `tools/build_replay_viewer.sh`,
   installs Playwright pinned **1.55.0** (module and browser together), and runs
   **`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
   dist/smoke/replay.json --timeout 90 --soak 10 --strict-text-bounds`** over local HTTP against
   **that** replay. Pass requires `data-replay-loaded="true"`, three different clock readouts at
   0 % / 50 % / 100 %, an uninterrupted 10 s of playback that keeps advancing (the cogball soak),
   and **zero never-inside canvas strings** — `--strict-text-bounds` is kept because Coins is a
   fixed arena (the cogchemists learning). `data-replay-error`, a bridge error, or silence until the
   timeout fails the job. Evidence (`viewer-smoke.png`, `viewer-smoke.json`) uploads on success and
   on failure. This is the gate cogame-lantern did not have.

---

## Out of scope (v1)

- **Any seat count other than 2.** Coins is a dyad in every variant and in the certification
  fixture. No 4-cog room, no spectator seat, no team variant.
- **Per-tick LLM control.** A seat submits one intent per 20-tick beat; the per-tick grid actions are
  produced by the deterministic kernel. 960 LLM calls per episode fits no timeout budget; ≤ 48 does.
  The RL-vector policy interface the idea points at (`cogamer-rl`) can drive the same per-tick
  action space later — the sim already exposes it — but no training path ships in this repo.
- **Any inter-seat channel.** No chat, no signals, no pre-play negotiation, no gesture. `say` is
  spectator-only. Deliberate: Melting Pot's coins has no channel, restraint has to be shown rather
  than promised, and a silent room is the anti-collusion property the idea asks for.
- **Partial observability.** No fog of war, no view radius, no pixel observation window. The room is
  7 × 7 and both cogs see all of it; the dilemma is about intentions, not information.
- **More than two coin colours, coin values other than 1, coin decay, and coins that can be dropped
  or traded.** A coin only ever moves from the board into a score.
- **Melting Pot's resident/visitor score normalisation.** The idea's integrity motive is served by
  mixed pairings against the two scripted reciprocator fillers, seeded spawns, anonymous aliases and
  no channel — not by a bespoke normalising formula layered on the platform's Elo.
- **Cross-episode memory or reputation.** Every episode starts from the seeded opening state;
  aliases carry no history and nothing persists except the league rating.
- **Configurable room geometry.** The room is a fixed 9 × 9 with a wall ring in every variant; there
  is no `roomSize` knob, no map generator, no obstacles. This is what lets the viewer drop
  `#viewpanel` and run `--strict-text-bounds`.
- **Re-simulating playback.** The viewer decodes recorded state frames; there is no replay-hash
  mismatch mode, no `--mismatch-quit`, and no `#mmwarn`.
- **Live spectator features beyond what paintbot gives free:** no POV lens, no first-person PiP, no
  zoom or minimap (fixed arena), no achievements, no perks, no handicaps.
- **A grim (never-forgiving) reciprocator as the shipped bot.** `reciprocator` punishes for 4 beats
  and re-arms; the permanently-grim reading is not built, because a truce that can never re-form
  makes the idea's headline replay beat — "the moment one cog starts leaving the other's coins
  alone" — unreachable in half the episodes.
