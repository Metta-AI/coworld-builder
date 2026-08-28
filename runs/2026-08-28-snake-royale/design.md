# cogame-snake-royale — design note (2026-08-28)

> **Destination path in the new repo: `docs/plans/2026-08-28-snake-royale-design.md`.** Phase 20
> commits identical bytes there. This copy under `runs/2026-08-28-snake-royale/design.md` is the
> run's record; the two files are byte-for-byte the same.

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` re-exporting the sim modules,
`sim_types.nim` owning `GameVersion` / `ReplayFps = 24` / `TargetFps = 24` and the rune caps
`MaxSayRunes` / `MaxNoteRunes` / `MaxPromptRunes = 4000`, the flatty wire types whose field order is
sacred); the Sprite v1 mummy HTTP/websocket server implementing the Coworld contract
(`src/ctf/server.nim`, `roster.nim`); the `decide.nim` / `directives.nim` / `llm.nim` /
`baselines.nim` / `control.nim` commander layer with its **one-parallel-batch-per-turn** shape, its
`attempt1Ms` / `retryMs` / `turnBudgetMs` / `turnSpacingMs` deadlines, its budget guard
(`decide.nim:335-346`), its rate floor (`decide.nim:384-392`), its tolerant JSON extraction, its
rune-boundary truncation and its repair-don't-reject validator; the binary `COWLD…` replay of
recorded inputs plus a per-tick `gameHash`, re-simulated by **the same sim module** compiled to wasm
by `replay-viewer/config.nims`; the `client/` broadcast chrome (`chrome_common.js` +
`broadcast_core.js` + `replay_broadcast.html`, with the appended game block spliced in through the
`window.PaintballChrome.install(PB_CTX)` hook at `client/replay_broadcast.html:4337`); nimby +
`Dockerfile` + `Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh`; and the Nim test suite
with its four shards (`tests/shard_1..4.nim`, `tests/config.nims`).

**Starter choice, one line:** this is a new real-time-loop game whose rules are written for this
coworld — a grid step loop, a per-turn replay, a static wasm viewer and broadcast chrome — which is
row 1 of the starter table in `prompts/10-design.md` and `playbooks/make-coworld.md` §Phase 0 ("any
real-time game loop, **grid** OR continuous physics, new rules written for this coworld"), and
`coworld-ctf` is that row's starter. It is deliberately **not** `cogame-moba`: nothing here is a
bit-exact port — kaggle-environments' `hungry_geese` is a Python `interpreter`, Battlesnake is an
HTTP league spec and OpenSpiel's `snake` is C++, and this repo merges their *rules* into one Nim
engine rather than reproducing any one of them byte-for-byte (the divergences are enumerated below
and pinned by a test). It is also not `cogame-babel`: the game has a board, a per-turn animated
replay and a spectator broadcast, which is exactly what paintbot supplies and what the parley stack
does not.

Where this note departs from coworld-ctf it says so. The departures are: **the board is a small
integer grid, not a continuous 2-D arena** (the whole `arena.nim` / `map_art.nim` / `map_pool.nim` /
`mapgen_styles.nim` map machinery, the map editor, the mapkit and the pool review page are deleted,
not disabled); **there are no weapons, no paint, no flags, no hill, no hit points, no lives and no
respawns**; **a tick is a turn** — the sim's authoritative unit is one simultaneous move by every
snake, the loop runs `fastMode` with no frame pacing, and `ReplayFps` survives only as the *viewer's*
render rate; **fog of war is gone** — the idea pins perfect information, so the shadowcast, the
vision cones and the FPV pipeline are deleted; and the game is a **four-way free-for-all**, so
`slots`/teams disappear from the config and scoring is a placement vector, not a team margin.

---

### Source idea (verbatim)

> KAG Snake Royale — Hungry Geese, Battlesnake and Tron: grow long, don't hit anything, and outlive
> the others
>
> Merged port of the multiplayer snake family: Kaggle Hungry Geese (4 geese on a 7×11 torus, eat food
> to grow, lose a segment every 40 turns, last goose standing), Battlesnake (4+ snakes, health that
> drains, hazards, official online league with thousands of bots), OpenSpiel snake, and Tron / Atari
> Surround (light cycles — no growth, just walls). One engine, rule modules. Simultaneous moves,
> perfect information, short episodes, brutal tie-breaks.
>
> Seats: 2-8
> Motive: zero-sum free-for-all (last standing)
> Policy interface: one direction per turn; LLM trivial to wire; very fast batteries
> Fills gap: simplest possible spatial FFA with emergent 'who blocks whom' diplomacy; a good
> entry-level coworld and a weekly-rules-rotation candidate
> Integrity (anti-collusion): FFA ganging — seat randomisation, anonymous aliases, alliance audit.
>
> Replay plan (watchability): self-explanatory; add a 'trapped' prediction overlay and a
> last-three-alive slow-mo.
>
> Source: kaggle-environments hungry_geese; docs.battlesnake.com; OpenSpiel snake.

---

### Upstream, consulted and pinned

The claims this note makes about the four upstreams are exactly the five below. Each is transcribed
into `src/snake/upstream.nim` with its citation comment beside it, and
`tests/test_snake_upstream.nim` asserts the shipped constants still match.

| Upstream fact | How it lands here | Where |
|---|---|---|
| **Kaggle Hungry Geese**: 4 geese, a 7-row × 11-column **torus**, food to grow, a segment lost every 40 steps, last goose standing | the `geese` rule module: an 11 × 7 wrapping board, `foodCount 2`, `shrinkEvery` on, `headToHead both_die` | §The game → Rule modules |
| **Battlesnake**: `health` drains one per turn and resets on food; **head-to-head is won by the strictly longer snake**, equal lengths both die; a snake may enter a tail cell that vacates this turn | the `royale` module: `healthStart 30`, `headToHead longer_wins`, the tail rule in resolution steps 7 and 10 | §The game → resolution |
| **Tron / Atari _Surround_**: light cycles — **no growth mechanic, just walls**; the trail never vacates and there is no food | the `tron` module: `leaveTrail true`, `foodCount 0`, `startLength 1` | §The game → Rule modules |
| **OpenSpiel `snake`**: simultaneous moves, perfect information | one direction per seat per turn resolved simultaneously; every seat sees the whole board every turn | §Server, player, protocol → observation |
| All four: **one direction per turn is the entire action space** | the reply schema's `dir` (plus an optional `alt` used only against the neck rule) | §Server, player, protocol → reply schema |

**Documented divergences** (also in `docs/RULES.md` §Divergences and as citation comments in
`src/snake/upstream.nim`, asserted by `tests/test_snake_upstream.nim`):

1. Hungry Geese shrinks every **40** steps across a 200-step episode. A 50-turn episode would show
   that clock once. `geese` uses **`shrinkEvery = 20`** so the hunger clock bites twice and a
   spectator can see it working.
2. Battlesnake health is **100** across long games. `royale` uses **30** across 50 turns for the same
   "you must eat about twice per episode" pressure.
3. Hungry Geese starts a goose at length 1. Here every module except `tron` starts at **3**
   (Battlesnake's convention), so the neck rule is meaningful from turn 2 and a snake reads as a
   snake on the first drawn frame.
4. In Hungry Geese and Battlesnake, naming your own neck is a **death**. Here it is **repaired** —
   `alt`, then `last_dir` — and counted in `results.reverseRepaired`. Reason: a model's formatting
   slip must not be an instant loss; the transport is not the game. Every other death cause is
   upstream's.
5. Battlesnake **hazards** ("sauce") are not implemented in v1 (§Out of scope).

---

### Design pins, and where each is satisfied

Every pin in `playbooks/make-coworld.md` §Phase 0 ("Pins that are never optional"), and where this
note answers it:

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — a real-time **grid** loop with rules written into this repo (title paragraph) |
| Repo `Metta-AI/cogame-snake-royale`, **public** (`source-resolves` 404s on private) | §Packaging |
| Build **both** an LLM policy and a scripted baseline day one, same image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=coil\|forager`) |
| Replays are a **static file + browser wasm viewer, never a pod** | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`, no `/client/replay` ever declared to the platform) |
| Starter chrome **verbatim** — page + appended block, byte-identical `chrome_common.js`, transport rules, zoom decision | §Viewer → Chrome provenance, Transport rules |
| **Real art, not placeholders** | §Viewer → Art (nano-banana snake kit + the starter's shipped chrome art) |
| Legible to a casual spectator (render "10" not "T"; show what agents are doing) | §Viewer → Readouts, Legible at 360 px (plain-language feed, no internal notation) |
| **Two name spaces** — anonymous cog aliases in-game, real policy names spectator-side | §The game → Seats, aliases, seat randomisation |
| **Degrade, never hang**; assume `episodeTimeoutSeconds` 1200 and play inside **60 %** (≈720 s) | §Decisions → Cadence and the wall-clock arithmetic; → Degrade, never hang |
| `num_agents` in **every** variant AND the cert fixture, **inside `game_config`** | §Packaging — `num_agents: 4`, four times (three variants + certification) |
| Simultaneous decisions issued as **one parallel batch per turn** | §Decisions → Cadence (`curly.makeRequests`, one batch of 4) |
| Replay bytes self-sufficient (names, config, per-turn state, seed) | §Server → Replay bytes |
| Rune-boundary truncation on every free-text field | §Server → Reply schema and per-field caps |
| Anti-collusion (the idea's own note): seat randomisation, anonymous aliases, alliance audit | §The game → Seats (seeded `spawnDeal`), §The game → The alliance audit (`results.declinedKills`) |
| Prove it in CI: sim tests, scripted-bot test, an end-to-end episode writing a replay, a viewer smoke | §Tests |

---

## The game

Four snakes on a small rectangular grid. Every turn all four move **one cell at the same time** —
nobody sees anybody else's move before it lands. Run into a wall, into anybody's body (your own
included), or out of health, and you are gone. Run your head into somebody else's head and, on the
default board, the **longer snake lives** and the shorter one does not. Food makes you longer and
refills your health; length is the only thing that wins a head-on; and the board only ever gets
smaller. The last snake alive takes the round. It takes about ninety seconds to watch and one
sentence to explain.

The strategy the idea is buying is **"who blocks whom"**: with four snakes on 153 cells, cutting a
rival's escape route is far cheaper than out-eating it, and cutting one rival's route usually helps a
third snake more than it helps you. There is a public one-line `say` channel, so a snake can announce
which lane it is taking — and everyone, including the snake it is about to seal in, reads it.

### Seats, aliases, seat randomisation

- **`num_agents` = 4.** Exactly four seats, always — in all three manifest variants and in the
  certification fixture. One snake per seat. The reasoning, stated once:
  - Four is Hungry Geese's own number and the canonical shape of every upstream the idea names.
  - Four is the smallest free-for-all in which the idea's "who blocks whom" exists at all. At two it
    is heads-up Tron and there is no third party to benefit from your block; at three, blocking is a
    duel with one bystander. At four, every block is also a gift, which is the whole game.
  - Four seats is **one parallel batch of four LLM calls per turn**, which at `turnSpacingMs = 9000`
    is 4 × 60/9 = **26.7 requests/minute**, inside the Bedrock sidecar's 30-per-minute per-episode
    cap, and fits the wall clock with ≈220 s of headroom (§Decisions). Eight seats would need a 15 s
    floor and would halve the turn count for the same money.
  - Four seats give the exact integer zero-sum placement vector `[+1000, +333, −333, −1000]`
    permille (§Scoring).
- **Seat randomisation (the idea's anti-collusion ask).** The mapping from seat index to **spawn
  anchor and colour** is `spawnDeal = shuffle(setupRng, [0,1,2,3])`, drawn from the seeded setup RNG
  **before any seat connects**, so nothing a policy does can shift it and no seat can learn "I am
  always the top-left snake". `spawnDeal` is pinned in the replay config and asserted to be a pure
  function of the seed by `tests/test_snake_seeding.nim`.
- **Two name spaces.** In-game a snake is `COG-alpha`, `COG-beta`, `COG-gamma`, `COG-delta` — the
  starter's identity-name array (`src/ctf/roster.nim`), fixed to the seat for the whole episode.
  Those aliases are the only names in an observation, a prompt, a reply, a `say`, a feed row or a
  board label. The seats' **real policy/player names** (`daveey`, `daveey-1`, `Baseline (1)`,
  `Baseline (2)`) live only in `results.names`, in the replay's join records, and in the viewer's
  scorebug plates and endcard. `showPlayerLabels` is **false** in every variant, so no on-board label
  can leak an identity. `tests/test_snake_identity_privacy.nim` (the starter's
  `test_pb_identity_privacy.nim` pattern) asserts no real name appears in any observation JSON, any
  prompt or any broadcast label.
- **Colours** follow `spawnDeal`, not the seat index: `amber`, `teal`, `violet`, `lime`. The scorebug
  maps colour → alias → real policy name, so a spectator can follow a policy while an agent cannot.

### The board

An integer grid of `boardW × boardH` cells, `cellPx = 32` map pixels per cell. Coordinates are
`[x, y]` with **x growing right and y growing down**; `[0,0]` is the top-left. Directions:
`up` = y−1, `right` = x+1, `down` = y+1, `left` = x−1. That is the whole coordinate system; there are
no floats anywhere in hashed code (`tests/test_snake_sim.nim` greps for them).

The four **spawn anchors** of a `w × h` board are the fixed points
`(w div 4, h div 4)`, `(w − 1 − w div 4, h div 4)`, `(w div 4, h − 1 − h div 4)`,
`(w − 1 − w div 4, h − 1 − h div 4)` — derived from the dimensions, not authored, so a new board size
needs no new data file. A snake starts with `startLength` segments **all stacked on its anchor cell**
(Battlesnake's convention), and its `last_dir` is the axis with the larger absolute delta toward the
board centre, x winning a tie. On turn 1 there is no neck, so all four directions are legal.

**Boards are fixed and authored by two integers.** There is no map generator, no map pool, no map
editor and no mapkit — all of that is deleted with `arena.nim` (§Sim module). A board is fully
described by `{w, h, wrap, cellPx}` and that document is pinned into the replay config, so a later
change to a variant cannot change what an old replay renders.

### Rule modules

One engine, three named presets of the same eight switches. `module` selects a preset; every switch
is also independently settable in a `game_config`, and `tests/test_snake_manifest.nim` asserts each
shipped variant's `game_config` really constructs the module it names.

| Switch | `royale` (default) | `geese` | `tron` |
|---|---|---|---|
| `boardW` × `boardH` | **17 × 9** (153 cells) | **11 × 7** (77 cells) | **21 × 9** (189 cells) |
| `wrap` (torus) | `false` — walls | `true` — torus | `false` — walls |
| `foodCount` (maintained on the board) | `3` | `2` | `0` |
| `healthStart` (0 = health off) | `30` | `0` | `0` |
| `shrinkEvery` (0 = off) | `0` | `20` | `0` |
| `leaveTrail` (tail never vacates) | `false` | `false` | `true` |
| `headToHead` | `longer_wins` | `both_die` | `both_die` |
| `startLength` | `3` | `3` | `1` |
| `maxTurns` | `50` | `50` | `50` |

Why these three and no others in v1: `royale` is the merged flagship and the league's default;
`geese` is the faithful Kaggle board (11 columns × 7 rows, torus, hunger shrink, both-die head-ons)
and is the module a Hungry Geese person recognises; `tron` is the same engine with growth and food
switched off, which is the cheapest possible proof that the rule-module axis is real. A fourth module
would add a manifest variant, a league division and a viewer state without adding a new question for
a policy to answer.

Why `royale` has **walls** while `geese` has a **torus**: on screen, a torus is a lie — a snake
crossing the left edge reappears on the right and a spectator loses it. Walls make the trap story
readable (a snake pinned against an edge is obvious), so the flagship module has walls and the
faithful-Kaggle module keeps the torus it is faithful to. The `geese` viewer draws **wrap ghosts**
(§Viewer) precisely because a torus needs the help.

Why `17 × 9`: 153 cells with four snakes is dense enough that turn 20 already has choke points, and
the **1.889 aspect is the embed frame's own aspect**, so almost nothing is letterboxed at 360 px and
a cell stays as large as the frame allows (§Viewer → Legible at 360 px).

### The clock

- **A turn is the atom.** There are no sub-turn ticks in the sim. One server-loop iteration = one
  decision round + one resolution. `fastMode: true`, so the loop is never frame-paced and the sim
  costs milliseconds; the episode's wall clock is the 50 LLM turns (§Decisions).
- **`maxTurns = 50`** in every variant. Most episodes end earlier, on `last_standing`.
- **Playback** is the viewer's business: `renderFramesPerTurn = 12` at `ReplayFps = 24`, i.e. **0.5 s
  of playback per turn**, so a full 50-turn episode plays for **25 s** at 1× and the head positions
  interpolate between turns instead of teleporting. When `aliveCount` first reaches 2 the viewer
  switches to 24 frames/turn — the idea's slow-mo (§Viewer).

### Turn structure — the exact resolution order

**Decision phase**, at the top of turn `T`, in this order:

D1. The engine snapshots the board and builds an observation for every **live** seat (§Server →
    observation). Dead seats are never queried again.
D2. Every live LLM seat's request goes out as **ONE parallel batch** (`curly.makeRequests`, the
    starter's `decide.nim:427` shape), attempt-1 deadline `attempt1Ms = 6000`. Scripted seats compute
    locally, in microseconds, and consume no request.
D3. Every seat that timed out, errored, returned non-JSON or returned no usable `dir` is retried
    **once**, again as one batch, `retryMs = 3000`. A provider 429 with no other candidate model
    skips the retry (it cannot land) and falls straight through — the starter's fail-fast.
D4. A seat still without a usable reply takes the **`coil`** scripted direction and a `fallback`
    record is written naming the cause (§Decisions → Degrade).
D5. Directions are installed in ascending slot. A field that does not validate is **repaired**, never
    dropped (§Server → reply schema); a repair increments `ordersRejected[s]`.
D6. `say` (≤ 24 runes, rune-truncated) is published to **every** seat's next observation and drawn as
    a board bubble for `SayTurns = 2`. It is public by construction: there is no private channel in
    this game, which is what makes the "diplomacy" auditable.
D7. `turnSpacingMs = 9000` is a floor on wall-clock time between consecutive **batch starts** (the
    starter's mechanism at `decide.nim:384-392`, kept), which is what keeps four seats under the
    sidecar's 30-request-per-minute per-episode cap.

**Resolution phase.** In this order, and **this is the whole physics of the game — nothing else
mutates the board**:

1. `turn += 1`.
2. **Neck repair.** For each live snake, `d = dir`. If `length > 1` and `head + d` equals the second
   body segment (the neck), then `d = alt` if `alt` is present and is not the neck, else
   `d = last_dir`. `reverseRepaired[s] += 1` in either case. The repair never invents a *legal* move —
   if `last_dir` walks into a wall, step 4 kills the snake.
3. **Targets.** `target[s] = head[s] + d`, taken modulo `(w, h)` when `wrap`, otherwise left
   off-board. `last_dir[s] = d`.
4. **Wall deaths** (`wrap == false` only). Any snake whose target is off the board dies this turn,
   cause `wall`.
5. **Heads move.** Every still-live snake pushes `target` onto the front of its body.
6. **Eat.** If `target[s]` held food: remove that food, `ate[s] = true`, `health[s] = healthStart`,
   `foodEaten[s] += 1`, emit `eat`.
7. **Tails.** For every still-live snake: if `leaveTrail` is false **and** `ate[s]` is false, pop the
   last segment. So a snake that ate keeps its tail and is one longer; a `tron` snake never pops.
8. **Hunger.** If `healthStart > 0`: `health[s] -= 1`, and `health[s] <= 0` kills it, cause `starve`.
   If `shrinkEvery > 0` and `turn mod shrinkEvery == 0`: every live snake pops one more tail segment,
   and a snake reduced to length 0 dies, cause `starve`.
9. **Head-to-head.** Group the still-live snakes by `target` cell. For each group of size ≥ 2:
   - `headToHead == "longer_wins"` **and** exactly one member has the strictly greatest **post-step-8
     length** → that member survives, every other member of the group dies (cause `headon`,
     `killedBy` = the winner's slot);
   - otherwise (`both_die`, or a length tie at the top) → **every** member of the group dies (cause
     `headon`, `killedBy = -1`).
   Head-ons resolve **before** body collisions on purpose: without that ordering the head-on winner
   would immediately be killed by the loser's neck, and "longer wins" would mean nothing.
10. **Body collisions.** Occupancy is the union of every still-live snake's segments **after** steps
    5–9, frozen before any death in this step is applied. A still-live snake whose head cell is also
    occupied by any segment other than its own head dies, cause `body`, `killedBy` = the owner of that
    segment (its own slot when it hit itself). Deaths here are simultaneous: two snakes can die into
    each other on the same turn.
    - Because tails popped in step 7 *before* this test, **a snake may legally follow a vacating
      tail** — Battlesnake's rule — but not the tail of a snake that ate this turn.
    - A snake killed in step 4, 8 or 9 **still occupies the board for this test**: its corpse does not
      retroactively free a cell that another snake was already committed to.
11. **Remove the dead.** Every snake that died in steps 4, 8, 9 or 10 has its segments cleared, after
    step 10's occupancy test. Record `deathTurn`, `deathCause`, `killedBy`, `finalLength`,
    `survivedTurns`. Emit `death` per snake, ascending slot.
12. **Food respawn.** While `len(food) < foodCount` and a free cell exists (no segment, no food), draw
    one uniformly from `foodRng` over the free cells and emit `foodspawn`. `foodRng` is a **separate
    stream** seeded `seed xor 0x5EED` (the starter's separate-stream convention for endzone
    archetypes, `AGENTS.md` §Terrain), so a change to seat behaviour can never shift the food draw.
13. **Derived measurements** (recorded and drawn, never scored): a bounded flood fill from each live
    head gives `freeSpace[s]`; a snake with `freeSpace[s] < length[s]` emits `trapped`; the alliance
    audit below increments `declinedKills[s]` and emits `decline`.
14. **Bubbles age** (`SayTurns`), `gameHash` folds over the whole board state (bodies, food, health,
    alive flags, turn, food-RNG state), and the turn's direction byte per seat plus the hash are
    appended to the replay.
15. **End evaluation.** `aliveCount <= 1` ends the episode (`endRule = "last_standing"`);
    `turn == maxTurns` ends it (`endRule = "full_time"`). `duel` is emitted on the turn `aliveCount`
    first reaches 2; `gameover` at the end.

### The alliance audit (the idea's anti-collusion ask)

FFA ganging is the failure mode the idea names, and it is invisible in a scoreboard. This game
measures it directly and puts the number in `results`, on the endcard and in the feed — and never in
the score.

`declinedKills[s]` counts the turns on which seat `s` had a **free kill and did not take it**:
some direction `d` was legal for `s`, its target cell was also reachable by exactly one opponent's
head, `headOnOutcome(s, d)` was `win` (post-move `s` is strictly longer), the move's `free_space` was
at least `s`'s own length — and `s` moved somewhere else. It is computed by the same
`headOnOutcome` / `willOccupy` / `freeSpaceFrom` procs the resolver uses, so it can never disagree
with the rules. A pair of policies that systematically decline each other while taking every other
kill shows up as two large `declinedKills` counts with a one-sided `killedBy` matrix, which is
exactly the audit the idea asked for. `results.declinedKills` is a first-class results key, the
endcard's `Soft` column, and a `decline` feed row (`COG-beta declines a free head-on with
COG-delta`). It is **not** in `scores` — §Out of scope records why.

### Scoring formula and sign

Every seat is ranked by a three-key ordering, **descending**:

```
key(s) = ( survivedTurns[s], finalLength[s], foodEaten[s] )

survivedTurns[s] = turnsPlayed          if the snake was alive when the episode ended
                 = deathTurn[s] - 1     otherwise
```

Seats with an identical key share a place — that is a genuine tie, and the tie-breaks are the idea's
"brutal" ones: outliving beats everything, then length, then food. Places 1..4 pay a fixed zero-sum
vector:

```
placementPermille = [ +1000, +333, -333, -1000 ]        # places 1, 2, 3, 4
```

A tied group occupying places `p .. p+k-1` splits that slice **exactly**:

```
total = sum(placementPermille[p .. p+k-1])
base  = floorDiv(total, k)                 # floorDiv/floorMod from std/math, NOT Nim's `div`
rem   = floorMod(total, k)                 # 0 <= rem < k, so base*k + rem == total exactly
```

each member gets `base`, and the first `rem` members **in ascending slot order** get one extra
permille. (`floorDiv`, not `div`: Nim's `div` truncates toward zero, which loses a permille on a
negative slice and breaks the exact zero sum.)

```
scorePermille[s] ∈ [-1000, +1000]
scores[s]        = scorePermille[s] / 1000.0        ∈ [-1.0, +1.0]
```

**Sign: higher is better.** `+1.0` is "last snake alive". `−1.0` is "first snake dead". The four
scores **sum to exactly 0** — the idea's zero-sum FFA — and
`tests/test_snake_scoring.nim` asserts `sum(scorePermille) == 0` over 1000 randomised end states
including every tie shape (2-way, 3-way, 4-way, and a 4-way tie where nobody moved).

**The league ranks by `results.scores[s]`.** `results.win[s]` is `place[s] == 1`, so a shared first
place gives every tied seat a win. There is no `results.winner` key: a four-way FFA has a placement
vector, not a winner.

**Everything else is measured and shown, never scored**: `finalLength`, `maxLength`, `foodEaten`,
`declinedKills`, `trappedTurns`, `reverseRepaired`, `saidTurns`. Weighting any of them would need a
magnitude the idea does not pin and would break the exact zero sum the league ranks on.

**Cross-play.** The certification fixture seats `coil, forager, coil, forager` and the league division
runs **two scripted fillers alongside the two prompt champions** (§Packaging), so a four-seat draw
seats a champion against unfamiliar rivals in essentially every episode. `results.policyKinds` records
what the game was given per seat, and `results.crossPlay` is true when at least one LLM seat and at
least one scripted seat played together.

### End conditions and legal `results.reason` values

The episode ends at the first of: **one or zero snakes alive**, **`turn == maxTurns`**, the
**wall-clock stop**, or a **fault**.

`results.reason` is a closed enum; **exactly these three values are legal** and the game emits nothing
else:

- **`complete`** — the healthy value. Covers both natural endings: `aliveCount <= 1`
  (`results.endRule = "last_standing"`) and `turn == maxTurns` (`results.endRule = "full_time"`).
  Settles after the `gameOverTurns = 2` display hold, then writes artifacts.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (**640 s**; the starter's check at
  the top of the loop, `server.nim:1407-1417`, kept). The engine stops at the current turn and settles
  with the **real** numbers so far: survivors are ranked by `survivedTurns = turnsPlayed`, then length,
  then food, exactly as at `full_time`, so a deadline episode is still rankable and still sums to
  zero. Artifacts are written, exit 0. `results.endRule = "wall_clock"`. **Declared acceptable** for
  SPEC §Definition of done check 4 — the budget guard below exists so that it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop, caught; the episode settles from the
  last completed turn, `results.endRule ∈ {"sim_fault", "host_error"}`,
  `results.stopDetail` names it (≤ 200 runes, rune-truncated), artifacts are still written, exit 0.
  A defect: `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum: **`last_standing | full_time | wall_clock |
sim_fault | host_error`**.

**Budget guard.** At the start of each turn, if `elapsed + 2 × turnBudgetSeconds >
wallClockBudgetSeconds`, the LLM is switched off for every remaining turn (all seats fall to `coil`,
microseconds per turn), the remaining turns run at full speed, and the episode still ends
`complete`. A `budget_guard` record names the turn it fired. This is the starter's guard at
`decide.nim:335-346`, kept.

**A seat that never connects, disconnects, or fails every decision does not end the episode**: its
snake is driven by `coil` and the episode runs to its natural end with `deadSeats[s] = true`. Nothing
a player container does can stop the clock — `lobbyJoinTimeoutSeconds` bounds the lobby and the
per-turn deadlines bound everything after it.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {coil, forager}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=coil` — the starter's "anything unrecognised is the published default" rule in
`baselines.nim:parseBaseline`. A scripted policy seated as a champion is a failure state, and phase 60
audits it by per-seat `llmTurns`.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/snake-royale/anthropic_api_key"` — the
hive 2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. **No
`USE_BEDROCK` flag** is set on the policies, because the player pod makes no LLM call (the cogolf
2026-08-24 gotcha applies to player-side-LLM lineages, not this one).

`src/snake_royale_player.nim` (`/bin/snake-royale-player`, forked from `src/paintball_player.nim`) is
a thin seat registrar: it opens the player websocket, sends one `register` packet carrying
`PLAYER_PROMPT` (rune-truncated at `MaxPromptRunes = 4000`), `PLAYER_SCRIPTED` and
`PLAYER_POLICY_LABEL`, and then holds the socket open. **The server logs loudly and marks
`deadSeats[s]` when a seat produces no `register` record** (the grf-football 2026-08-27 scar: a lost
register packet silently demoted a champion to the default script for a whole episode), and
`results.policyKinds` plus the replay's `register` records make it auditable afterwards.

### Cadence, batching, and the wall-clock arithmetic

**All four seats' calls go out as ONE parallel batch per turn.** This is a simultaneous-decision game;
querying seats one after another would quadruple the wall clock for no gain
(`playbooks/make-coworld.md` gotcha table: "LLM game blows the 720 s play budget → issue all seats'
LLM calls as one parallel batch per turn (`curly.makeRequests` in Nim)"). One call per seat per turn;
one batch per turn; at most two batches per turn (attempt + retry).

| Knob | Value | Why |
|---|---|---|
| `maxTurns` | 50 | see the arithmetic below |
| `turnSpacingMs` | 9000 | 4 seats × 60/9 = **26.7 req/min**, inside the sidecar's 30/min per-episode cap |
| `attempt1Ms` | 6000 | `curly` hands the deadline to `CURLOPT_TIMEOUT`, whose granularity is **whole seconds**, so this must be a whole number of seconds — `sim_config` rejects a sub-second value (the starter's 0.1.2 scar, `decide.nim:418-426`). 6 s covers the hosted **batch** p90, not one call |
| `retryMs` | 3000 | one retry, 3 s |
| `turnBudgetMs` | 11000 | hard per-turn cap: 6 + 3 = 9 s of calls plus slack |
| `wallClockBudgetSeconds` | 640 | the engine's own stop; the budget guard fires from `elapsed + 22 > 640`, i.e. ≈618 s |
| `lobbyJoinTimeoutSeconds` | 90 | bounds the lobby (seconds, not ticks: a `fastMode` turn has no wall-clock meaning) |
| `gameOverTurns` | 2 | the display hold before artifacts are written |

**The arithmetic, out loud** (`episodeTimeoutSeconds` = 1200, the 60 % budget = **720 s**):

- **Typical.** A four-call batch measures ≈4 s and hides entirely inside the 9 s spacing floor, so a
  turn costs **9.0 s**. `50 × 9.0 = 450 s`, plus lobby ≤ 30 s, plus the `gameOverTurns` hold and the
  artifact write ≈ 20 s → **≈ 500 s = 69 % of the 720 s budget, 42 % of the 1200 s timeout.**
- **Worst case.** Every turn burns attempt 1 (6 s) *and* the retry (3 s) and is capped by
  `turnBudgetMs`: **11 s/turn**. `50 × 11 = 550 s` + 50 s → **≈ 600 s = 83 % of the 720 s budget.**
- **Guard.** The engine's own stop is 640 s and the budget guard switches every remaining turn to
  `coil` from ≈618 s, so the worst case above settles `complete` / `full_time`, not `deadline`, and
  nothing can overrun 720 s.
- Most episodes never reach turn 50: `aliveCount <= 1` typically arrives between turns 25 and 45.
- Scripted-only episodes (certification, `docker_smoke.sh`, every CI run) cost **milliseconds**:
  `turnSpacingMs: 0` and no LLM client.

### Degrade, never hang

Every wait is bounded, and no failure mode leaves a snake unactuated.

| Failure | What happens |
|---|---|
| A seat's attempt 1 times out, errors, or returns text with no usable JSON | it goes into the retry batch; the log says **`will retry`**, never `falling back` (the pommerman 0.1.1 wording rule — only a genuine fallback may say `falling back`, because phase 60 greps for it) |
| The retry also fails | the seat takes the **`coil`** scripted direction for that turn; a `fallback` record with `cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard}` and a ≤ 200-rune `detail` is written to the replay; `fallbackTurns[s] += 1`; the game log prints `falling back` |
| A provider 429 with no other candidate model | the retry is **skipped** (it cannot land) and the seat falls straight to `coil`, `cause = throttled` |
| No `ANTHROPIC_API_KEY` at all (certification, CI) | the client is `disabled`; every LLM seat records `cause = no_credentials` per turn, so `llmTurns 0 / fallbackTurns N` is countable rather than silently zero (the starter's `decide.nim:358-372` fix, kept) |
| A reply parses but a field is illegal | **repaired, never rejected** (§Server → reply schema); `ordersRejected[s] += 1` |
| A seat never connects, or connects and never answers | its snake plays `coil` for the whole episode, `deadSeats[s] = true`, and exactly one closed-schema `{"message", "failed_policy_index"}` payload is POSTed to `COGAME_PLAYER_FAILURE_URI` |
| The wall clock approaches | the budget guard switches everything to `coil` and the episode finishes `complete` |
| Everything else | `wallClockBudgetSeconds = 640` stops the loop and settles `deadline` with real numbers |

**The fallback path and the `coil` baseline resolve to the same proc**, so they cannot drift
(`tests/test_snake_control.nim` asserts it).

### The two scripted baselines

Both emit the **same object an LLM emits** (`{"dir", "alt", "say", "notes"}`), on the same cadence, so
they are strictly comparable and one validator covers both — which is what makes the bounded-orders
test meaningful. Both are **pure functions of the board state** with no RNG.

Shared skeleton, `scoreDir(d)`; the snake takes the highest-scoring direction, ties broken by the
fixed order `up, right, down, left`:

```
if d is the neck                      -> not proposed at all
t = step(head, d)                      # wrapped if `wrap`
if t is off the board and not wrap     -> -infinity
if willOccupy(t)                       -> -infinity    # the RESOLVER's own predicate
space = freeSpaceFrom(t, cap = 4 * length)             # src/snake/space.nim, bounded BFS
risk  = headOnOutcome(t)               # the RESOLVER's own predicate: safe|win|tie|lose

s  = spaceWeight * min(space, spaceCap * length)
s -= headRiskPenalty      if risk in {lose, tie}
s += killBonus            if risk == win
if foodCount > 0:
  s -= foodWeight * bfsDist(t, nearest food, cap = 99)
  s += 300                if t holds food and health <= hungerThreshold
s += 40                   if d == last_dir              # prefer straight: fewer self-traps
```

If every direction scores `-infinity` the snake returns `last_dir` and dies — which is the correct
outcome for a sealed-in snake, and is never an unactuated seat.

| Tunable | `coil` | `forager` |
|---|---|---|
| `spaceWeight` | 1000 | 400 |
| `spaceCap` (× own length) | 2 | 1 |
| `headRiskPenalty` | 900 | 500 |
| `killBonus` | 120 | 60 |
| `foodWeight` | 8 | 40 |
| `hungerThreshold` | 12 | 999 (always hungry) |

- **`coil`** is the survival heuristic: space first, food only when hungry or free. It is the
  certification player, the per-turn fallback, the default for an unregistered seat, and filler #1.
- **`forager`** is visibly greedier: it beelines for food and accepts tighter space, so it grows
  faster and traps itself more. It is filler #2 and the thing a champion should be able to beat.

Neither ever emits `say` or `notes` (both empty), which is why the viewer's text chrome needs the
renderer fixture in §Tests: a CI replay contains no LLM text at all (the cogchemists 2026-08-24 scar).

Cost per call: four directions × one BFS capped at `4 × length` (≤ ~50 cells) — microseconds. The
tunables are **swept, not guessed**: `tools/tune_baselines.nim` plays a bounded matrix over a fixed
24-episode ladder and writes `tools/ci/baseline_tuning.json`; `ci.yml` re-runs the sweep with
`--check`, and `tests/test_snake_control.nim` asserts the shipped defaults equal the recorded pick and
that `coil`'s mean score over that ladder beats `forager`'s by a margin inside `[+0.30, +1.20]`.

### The system prompt (fixed, identical for both champions)

Lives in `src/snake/llm.nim` as `SystemPrompt*`, replacing the starter's paintball const — the only
game-specific text in that file, which is otherwise kept structurally verbatim (§Sim module).

```
You are one snake in a four-snake free-for-all on a rectangular grid. Every turn all four
snakes move ONE cell at the same time; nobody sees anybody else's move before it happens.
You choose one direction per turn and nothing else.
Coordinates are [x, y] with x growing RIGHT and y growing DOWN, so "up" is y-1, "down" is
y+1, "left" is x-1, "right" is x+1, and [0,0] is the top-left cell.
Your body is a list of cells, head first. Each turn your head enters the cell you chose and
your tail leaves its cell, so your length is unchanged unless you eat. Eating food adds one
segment and refills your health.
You die if your head leaves the board (unless this board wraps), or enters ANY snake's body
including your own, or if your health reaches zero. If two heads enter the same cell, this
board's rule decides it: "longer_wins" means the strictly longer snake lives and the rest
die; "both_die" means everyone in that cell dies. Equal lengths always all die.
You may not move into your own neck, the cell directly behind your head. If you name it
anyway the game silently uses your "alt", then your last direction.
The whole board is visible to you. The `moves` list has already been computed by the SAME
code that resolves the turn: for each of the four directions it gives the target cell,
whether it is off the board, whose body is in it, whether food is there, how many free cells
you could still reach from it, and whether a head-on there would be a win, a tie or a loss
for you. Trust it. A `free_space` smaller than your own length means you are sealing
yourself in and will die inside your own coil.
The winner is the LAST SNAKE ALIVE. Placement pays +1.000, +0.333, -0.333, -1.000 and the
four scores always sum to zero, so outliving one more snake is worth as much as anything
else you can do. Ties in survival are broken by length, then by food eaten.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"dir":"up|down|left|right",
 "alt":"up|down|left|right",
 "say":"<=24 chars, PUBLIC - every snake reads it next turn",
 "notes":"<=160 chars, private, handed back to you next turn"}
"dir" is your move. "alt" is used only if "dir" is your neck. "say" is broadcast to all four
snakes and drawn on the replay: it is the only channel you have, and everyone, including the
snake you are about to seal in, reads it.
```

### Champion #1 — `snake-royale-strangler` (owner **daveey**), `PLAYER_PROMPT`

```
Win by shrinking everybody else's room, not by racing them to food. Every turn read the
`moves` list first and throw away any direction whose `legal` is false or whose `head_risk`
is "lose" or "tie" - no plan is worth a coin-flip death. Among what is left, take the one
with the largest `free_space`, and break that tie with food only.
Never let your own `free_space` fall below twice your length. If it has, spend the turn
turning back toward open board even if that means giving up a nearby apple.
Eat only when `health` is under 12, or when the food sits on a cell you were moving through
anyway, or when you are the shortest snake alive - length is only worth having because it
wins head-ons.
Once you are strictly the longest snake, hunt: take a direction whose `head_risk` is "win"
whenever one exists and its `free_space` is at least your length, because a won head-on
removes a whole snake for free. Otherwise steer to sit between the two shortest snakes and
the open half of the board, so their space closes before yours does.
When a rival's `free_space` in the report is below its length it is already dead. Do not
spend a turn near it; just stay out of the cells it will thrash into.
Use `say` to claim the lane you are actually taking, four or five words, and then take it.
A rival who believes you detours; a rival who does not learns nothing.
```

### Champion #2 — `snake-royale-glutton` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Get long early, then let length do the killing. For the first third of the episode take the
shortest safe path to the nearest food every single turn: from `moves` drop anything with
`legal` false or `head_risk` "lose" or "tie", then take the direction whose target has
`food` true, else the legal direction that shortens the distance to the nearest cell in
`food` while keeping `free_space` at least your length plus four.
Refuse exactly two things while feeding: a move whose `free_space` is below your length plus
four, and a move into a one-cell-wide corridor with a rival head within two cells of its far
end.
From the moment you are the longest snake alive, stop chasing food unless `health` is under
10, and start steering INTO the shortest rival: prefer a direction whose `head_risk` is
"win", then one that puts your head within two cells of that rival's head on its open side,
because a snake that keeps turning away from you runs out of board.
Hug a wall only when your `free_space` is at least three times your length. A wall is a free
half of a trap and it is usually yours, not theirs.
If two rivals are converging on the same apple, take neither: go eat the far apple, let them
settle it, and take the survivor's space.
Use `say` to announce what you just ate and how long you now are. It is true, it is free, and
a rival that starts avoiding your head has already given you the board.
```

---

## Sim module

Nim, in the starter's layout, under `src/snake/` (Nim identifiers cannot carry the dashed slug; only
the two entry files and the two binaries do). `src/snake/sim.nim` imports and **re-exports** all of
them, so `import snake/sim` still sees everything — the starter's rule.

### Kept, by path

**Byte-for-byte (a test pins the sha256 of each):**

| Path | Note |
|---|---|
| `client/chrome_common.js` | 40 022 bytes, unedited, unreformatted (§Viewer) |
| `tools/wasm_replay_smoke.cjs` | headless-node run of the exact emitted wasm module; only the module filename string changes |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py`, `tools/ci/test_next_coworld_version.py` | unchanged |
| `tests/config.nims` (`--path:"../src"`) | unchanged |

**Structurally verbatim (forked in place, the named parts asserted identical to the starter's text):**

| Path (starter → here) | What is kept, what changes |
|---|---|
| `src/ctf/llm.nim` → `src/snake/llm.nim` | the whole Bedrock/Anthropic transport — `resolveApiKey`, `bedrockModelIds`, `tryNextBedrockModel`, `bedrockUrl`, `newLlmClient`, `requestFor`, `textOf` (including the `max_tokens`-cut-off raise), `operatorBlock`, `userMessage` — kept and pinned function-by-function by `tests/test_snake_llm.nim`. **Only the `SystemPrompt*` const is replaced** (§Decisions) |
| `src/ctf/directives.nim` → `src/snake/directives.nim` | `truncateRunes`, `sanitizeSay`, `sanitizeNote`, `extractJsonObject` lifted verbatim, including the rune-discipline doc comment and the `{`/`}` exclusion in `sanitizeSay` (the replay chat stream tells a control record from a shout by a leading brace). The `Intent` enum and `CogOrder` are replaced by `SnakeOrder` (§Server → reply schema) |
| `src/ctf/decide.nim` → `src/snake/decide.nim` | the whole per-turn loop shape: the budget guard (`decide.nim:335-346`), the rate floor (`384-392`), the two parallel batches with `attempt1Ms`/`retryMs`/`turnBudgetMs` (`394-470`), the throttle fail-fast (`472-479`), the final fallback ladder and its `cause` enum (`481-492`), and the exact `falling back` log phrase phase 60 greps. **Only `seatViewJson`, the parse call and the fallback baseline change** |
| `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js` | kept; only the module filename (`ctf_replay.js` → `snake_replay.js`) and the exported symbol prefix (`_ctf_*` → `_snake_*`) are renamed. `data-replay-loaded` / `data-replay-error` are the starter's own signals, inherited unchanged (§Viewer) |
| `replay-viewer/config.nims` | kept; `-o` target renamed, `EXPORTED_FUNCTIONS` renamed, everything else (including **`-s ABORTING_MALLOC=1`** and its comment) unchanged (§Viewer) |
| `tools/build_replay_viewer.sh` | kept; image tag and the `docker cp` source path (`/workspace/ctf/replay-viewer/dist/.` → `/workspace/snake/replay-viewer/dist/.`) changed. It already carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling. Committed **executable** (`coworld build` hard-requires `os.X_OK`) |
| `Dockerfile`, `Dockerfile.replay-viewer` | structure verbatim; §Packaging lists the named edits |

**Forked and retargeted in place:** `sim_types.nim`, `sim_config.nim`, `sim_state.nim`, `roster.nim`,
`sim.nim`, `server.nim`, `global.nim`, `broadcast.nim`, `events.nim`, `labels.nim`, `control.nim`,
`baselines.nim`, `replays.nim`, `replay_runtime.nim`, `wire_constants.nim`,
`rig_art.nim` → `snake_art.nim`; `client/broadcast_core.js`, `client/replay_broadcast.html`;
`replay-viewer/ctf_replay.nim` → `replay-viewer/snake_replay.nim`; `tools/gen_wire_constants.nim`,
`tools/replay_summary.py`, `tools/tune_baselines.nim`, `tools/record_fixture.sh`,
`tools/extract_events.nim`, `tools/benchmark_game.nim`.

### Deleted (with their tests, tools, docs and config surfaces), not disabled

`src/ctf/arena.nim` (3849 lines of continuous-2-D map geometry, the terrain generator, its validators,
`mapSpec` and the process-global map install), `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`,
`paint.nim`; every weapon, bullet, hit point, life, respawn, spray, paint grid, hill, heart, flag,
grenade, med kit, shield, barrier, trench, puddle, perk, handicap, achievement, four-team and campaign
mechanic; the fog-of-war shadowcast and the whole vision system (this game is perfect information);
the first-person PIP; `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`,
`tools/render_map_pool.nim`, `tools/map_render.nim`, `tools/build_pool_review.py`, `docs/MAPKIT.md`,
`docs/pool-review.html`, `docs/designs/map-editor.md`; `client/league_replayer.html` and, with it, the
`league.html` `sed` splice and its four `test -f`/`grep -q` assertions in `Dockerfile.replay-viewer`;
`players/`, `caos/`, `caos-tools/`, `arena/`; and every `tests/test_*` that covers a deleted mechanic.
Deleted, not gated: a gate-off config that still compiles a paint grid is 8000 lines of code nobody in
this repo can reason about.

### New modules

| Module | Contents |
|---|---|
| `src/snake/board.nim` | the grid: `Board{w, h, wrap, cellPx}`, `step(cell, dir)` with the modulo, `inBounds`, `cellIndex`, the four derived spawn anchors, free-cell enumeration, and the `Dir` enum (`dUp = 0, dRight = 1, dDown = 2, dLeft = 3` — the wire order of the replay's direction byte) |
| `src/snake/rules.nim` | `RuleModule` presets and the resolver: `willOccupy`, `headOnOutcome`, `resolveTurn` implementing steps 1–15 verbatim. **`willOccupy` and `headOnOutcome` have exactly one implementation each** and are called by the resolver, the observation builder, both baselines, the validator and the viewer pre-scan, so no consumer can disagree with the rules (the escrow 2026-08-23 lesson: precompute the legal choice set with the same predicate the validator applies) |
| `src/snake/space.nim` | `freeSpaceFrom(cell, cap)` — one bounded BFS over the grid, and `bfsDist(from, to, cap)`. Four callers, one implementation |
| `src/snake/upstream.nim` | the transcribed upstream facts and divergences with citations, asserted by `tests/test_snake_upstream.nim` |

### Determinism

All arithmetic is integer; `tests/test_snake_sim.nim` greps `src/snake/{board,rules,space}.nim` for
float literals, `/` and `sqrt` and asserts none. Two RNG streams, both the starter's integer generator
from `sim_state.nim`: `setupRng` (seeded `seed`) draws `spawnDeal` **before any seat connects**;
`foodRng` (seeded `seed xor 0x5EED`) draws every food cell. Separating them is what makes the food
sequence a pure function of the seed regardless of how the snakes play, and what makes
`tests/test_snake_seeding.nim`'s "no seat behaviour changes either stream" assertion meaningful.

Native ↔ wasm: the same `src/snake/` modules compile both ways; `tools/wasm_replay_smoke.cjs` runs the
**exact emitted** module against the committed fixtures, because wasm32-only failures (integer traps,
address-space exhaustion) are invisible to the native 64-bit shards.

### The named edits to the forked server/roster/global

**`server.nim` — three edits.** (1) The tick loop becomes a **turn** loop: one decision round plus one
`resolveTurn` per iteration, `fastMode` always on, no frame pacing; `maxTicks`/`startWaitTicks`/
`gameOverTicks`/`lobbyJoinTimeoutTicks` are renamed `maxTurns`/`gameOverTurns`/
`lobbyJoinTimeoutSeconds` — the last in **seconds**, because a `fastMode` turn has no wall-clock
meaning. (2) The wall-clock check at the top of the loop (`server.nim:1407-1417`) is kept as-is,
reading `wallClockBudgetSeconds`. (3) The certifier's browser probes stay registered **before** any
catch-all asset route and keep answering for the `gameOverTurns` grace after artifacts are written:
`GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket — the
flatland 0.1.1 scar), `GET /client/global`, the `/global` websocket's first message, and `/healthz`
(the lantern 0.1.1 and 0.1.3 scars). Global broadcasts stay fire-and-forget so a slow viewer can never
stall the episode.

**`roster.nim` — two edits.** (1) Teams are deleted: a seat is its own side, `slots` is gone from the
runtime config, and `cogAlias(slot)` returns `COG-<identity>` from the starter's identity array.
(2) A seat with no `register` record is logged loudly (`ERROR: seat N never registered — playing coil`)
and flagged `deadSeats[s]`.

**`global.nim` — three edits.** (1) Every weapon/paint/flag/hill/FPV draw path and its wire fields are
deleted. (2) The broadcast state carries the grid: `board`, `snakes[].body`, `health`, `alive`,
`length`, `food`, `bubbles`, `freeSpace`, `place`. (3) `window.CTF_WIRE` becomes `window.SNAKE_WIRE`,
emitted by the forked `tools/gen_wire_constants.nim`.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local developer replay mode (never declared to
the platform); `HOST`/`PORT`; player sockets at `/player?slot=<i>&token=<t>`, closed unless the token
matches the seat.

### Per-seat observation — exactly what is visible and what is hidden

The idea pins **perfect information**, so the whole board is in every observation. Built by
`seatViewJson` (the starter's proc, retargeted), in board cells, integers only:

```json
{
  "module": "royale",
  "board": {"w": 17, "h": 9, "wrap": false},
  "turn": 17, "max_turns": 50, "turns_left": 33, "alive": 3,
  "rules": {"head_to_head": "longer_wins", "food_count": 3,
            "health_start": 30, "shrink_every": 0, "leave_trail": false},
  "you": {
    "id": "COG-beta", "colour": "teal", "alive": true,
    "head": [7,4], "body": [[7,4],[7,5],[6,5],[6,6]],
    "length": 4, "health": 21, "last_dir": "up",
    "free_space": 62, "food_eaten": 2
  },
  "snakes": [
    {"id":"COG-alpha","colour":"amber","alive":true,"head":[2,2],
     "body":[[2,2],[3,2],[3,3]],"length":3,"health":9,"last_dir":"left",
     "free_space":48,"food_eaten":1,"death_turn":0,"death_cause":""},
    {"id":"COG-gamma","colour":"violet","alive":false,"head":[0,8],
     "body":[],"length":0,"health":0,"last_dir":"down",
     "free_space":0,"food_eaten":0,"death_turn":11,"death_cause":"wall"}
  ],
  "food": [[0,7],[11,1],[14,6]],
  "moves": [
    {"dir":"up",   "to":[7,3],"legal":true, "wall":false,"body":"none","food":false,
     "head_risk":"safe","free_space":58},
    {"dir":"right","to":[8,4],"legal":true, "wall":false,"body":"none","food":false,
     "head_risk":"win", "free_space":58},
    {"dir":"down", "to":[7,5],"legal":false,"wall":false,"body":"self","food":false,
     "head_risk":"safe","free_space":0},
    {"dir":"left", "to":[6,4],"legal":true, "wall":false,"body":"none","food":true,
     "head_risk":"lose","free_space":31}
  ],
  "said": [{"id":"COG-delta","text":"north lane is mine"}],
  "your_notes": "hold the north corridor, alpha is short"
}
```

- `snakes[]` lists **every seat, in the same order every turn**, including dead ones (with their
  `death_turn` and `death_cause`), so a model can count who is left without diffing.
- `moves[]` always has exactly four entries, in the `up, right, down, left` wire order, and it is the
  **precomputed legal choice set**: `legal` is `willOccupy` + bounds from the resolver;
  `body ∈ {none, self, other, tail}` where `tail` is a cell that vacates this turn (legal unless that
  snake ate); `head_risk ∈ {safe, win, tie, lose}` from `headOnOutcome`; `free_space` from
  `freeSpaceFrom`. The neck direction is present with `legal: false, body: "self"`. One predicate,
  four callers (§Sim module) — the observation can never claim something the resolver disagrees with.
- `said[]` carries last turn's `say` from every **other** live seat (public by construction).
- `your_notes` is the seat's own previous `notes`, handed back; no other seat's notes are ever in it.

**Hidden from a seat:** every seat's **real policy/player name** (only aliases and colours appear);
the other seats' `notes`; the other seats' **pending direction for this turn** (moves are
simultaneous); the future of the `foodRng` stream; and `spawnDeal`. Nothing else on the board is
hidden — that is the idea's perfect information.

### Reply schema and per-field caps

One object per seat per turn:

```json
{"dir":"up","alt":"left","say":"north lane is mine","notes":"cut alpha off at 7,3"}
```

| Field | Type | Cap | Repair on a bad value |
|---|---|---|---|
| `dir` | enum `up\|down\|left\|right` (case-insensitive; `u/d/l/r`, `north/south/west/east` and hyphen/space forms normalised) | — | unparseable or absent → `alt`, then `last_dir`, then the first legal direction in the order `up, right, down, left`; `ordersRejected[s] += 1` |
| `alt` | same enum, optional | — | absent or unparseable → skipped in the ladder |
| `say` | string, public | **24 runes** | `truncateRunes(24)` on a **rune boundary**, then the starter's printable-ASCII shout filter (which also strips `{` and `}` so a shout can never be mistaken for a control record) |
| `notes` | string, private | **160 runes** (`MaxNoteRunes`) | `sanitizeNote` — newlines collapsed to spaces, then `truncateRunes(160)` on a **rune boundary** |

The whole reply is read with a **4096-byte** cap and the JSON is extracted by the starter's tolerant
`extractJsonObject` (markdown fences and surrounding prose survive). `PLAYER_PROMPT` is itself capped
at `MaxPromptRunes = 4000`, rune-truncated, and is never echoed into the replay or the results.

**Every truncation in this game lands on a rune boundary.** No string that reaches the replay is ever
sliced by byte index — a byte-truncated multi-byte character renders in a browser and then fails a
strict UTF-8 parser, which is the class of bug that makes a replay unreadable to everything but the
one lenient viewer (`playbooks/make-coworld.md` gotcha table).

The validator **repairs, never rejects**: there is no reply that leaves a snake unactuated.

### Results document (closed schema; `snakeResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":           ["daveey","daveey-1","Baseline (1)","Baseline (2)"],
  "aliases":         ["COG-alpha","COG-beta","COG-gamma","COG-delta"],
  "colours":         ["amber","teal","violet","lime"],
  "scores":          [1.0, 0.333, -0.333, -1.0],
  "win":             [true, false, false, false],
  "place":           [1, 2, 3, 4],
  "reason":          "complete",
  "endRule":         "last_standing",
  "module":          "royale",
  "turnsPlayed":     37,
  "survivedTurns":   [37, 36, 30, 11],
  "deathTurn":       [0, 37, 31, 12],
  "deathCause":      ["", "headon", "body", "wall"],
  "killedBy":        [-1, 0, 1, -1],
  "finalLength":     [11, 8, 6, 4],
  "maxLength":       [11, 9, 6, 4],
  "foodEaten":       [8, 5, 3, 1],
  "declinedKills":   [0, 3, 1, 0],
  "trappedTurns":    [0, 2, 5, 1],
  "reverseRepaired": [0, 1, 0, 4],
  "saidTurns":       [12, 9, 0, 0],
  "policyKinds":     ["llm","llm","scripted","scripted"],
  "crossPlay":       true,
  "llmTurns":        [37, 36, 0, 0],
  "fallbackTurns":   [0, 1, 0, 0],
  "ordersRejected":  [0, 2, 0, 0],
  "deadSeats":       [false, false, false, false],
  "seed":            1734029581,
  "stopDetail":      ""
}
```

Every seat-indexed array is exactly **4** long. `deathTurn[s] == 0` means "alive when the episode
ended". Adding a key means updating `snakeResultsJson`, the manifest's `results_schema` and
`tools/ci/docker_smoke.sh`'s expected-key set **in the same commit** — Coworld schemas are closed and
undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDSNK`** format (`replays.nim`'s `CtfReplayMagic` renamed).
The static wasm viewer parses exactly this; a JSON replay would mean rewriting `replays.nim`,
`replay_runtime.nim`, `static_replay_worker.js` and `wasm_replay_smoke.cjs` — the machinery this fork
exists to reuse (the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (template line 31/57).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker),
  retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"snake-royale/v1","gameVersion":"1","seed":…,"module":"royale","board":{…},
  "names":[…],"aliases":[…],"policyKinds":[…],"turnCount":…,"dirs":[…],"says":[…],"notes_count":…,
  "fallbacks":N,"results":{…}}` — by brace-matching the config JSON from the first `{` (the technique
  `AGENTS.md` documents for prod forensics) and decoding the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                      # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.place, .results.finalLength' /tmp/ep.json
  jq -r '[.dirs[]|select(.source=="llm")]|length, .fallbacks, (.says|length)' /tmp/ep.json
  ```
  Require `protocol == "snake-royale/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `sum(results.scores) == 0`, a non-zero `sum(results.foodEaten)` in a food module, and
  the champion seats' turns with `source == "llm"`, real directions and non-empty `says` — not all
  fallbacks.

Everything the viewer needs is in the bytes; **no server is contacted except S3 for the `.replay`
file**:

| Replay content | Carries |
|---|---|
| header | magic `COWLDSNK`, format version, `gameName snake-royale`, `gameVersion "1"` |
| config JSON | `seed`, `module`, the full board document (`w`, `h`, `wrap`, `cellPx`), `foodCount`, `healthStart`, `shrinkEvery`, `leaveTrail`, `headToHead`, `startLength`, `maxTurns`, `num_agents`, `spawnDeal`, `spawnAnchors`, `players[].name` (**real names**), `aliases`, `colours`, `attempt1Ms`, `retryMs`, `turnBudgetMs`, `turnSpacingMs`, `renderFramesPerTurn`, `sayTurns`, `fastMode`, `showPlayerLabels` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| direction log | one byte per seat per turn — `0=up, 1=right, 2=down, 3=left, 255=already dead`. This game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per turn — the integrity chain the viewer checks (`#mmwarn` on divergence) |

**Food is not recorded** and does not need to be: `foodRng` is a pure function of the seed and the
resolution order, so the wasm module re-derives every apple, and the per-turn `gameHash` proves it.
`tests/test_snake_replay.nim` asserts the re-derivation is hash-identical **at every turn including
the stop turn** (the particle-worlds scar).

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `colour`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `dir`, `alt`, `repaired` (bool), `say` (≤ 24 runes), `view` (the observation minus `your_notes`) |
| `fallback` | `turn`, `slot`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `turn`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end (the starter's `resultRecord`) |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay.
**A closed enum of sixteen kinds:**

`gamestart` `{module, board}`; `spawn` `{slot, alias, at, colour}`; `turn` `{n, alive}`;
`move` `{slot, dir, from, to, source}`; `say` `{slot, text, x, y}`;
`eat` `{slot, at, length, health}`; `foodspawn` `{at}`; `shrink` `{slot, length, cause}`;
`headon` `{at, slots, winner}`; `death` `{slot, alias, turn, cause, killedBy, length}`;
`trapped` `{slot, freeSpace, length}`; `decline` `{slot, target, at}`;
`duel` `{turn, slots}`; `fallback` `{slot, cause}`; `gameover` `{turn, place, endRule}`;
`end` `{reason, endRule, scores}`.

`tests/test_snake_events.nim` asserts the emitted set equals **exactly** this list, and that every kind
the appended viewer block consumes is in it.

**Beats** — the scrubber markers, and the only kinds the appended game block turns into buttons:
**`eat`, `headon`, `death`, `trapped`, `duel`, `fallback`, `gameover`.** To keep a 50-turn scrubber
readable, an `eat` beat is emitted only for a snake's **first** apple and for any apple that makes it
the longest snake; the rest drive the feed only. `gamestart`, `spawn`, `turn`, `move`, `say`,
`foodspawn`, `shrink`, `decline` and `end` never make beats.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `TurnStart, Move, Eat, FoodSpawn, Shrink, HeadOn, Death, Trapped, Decline,
Duel, Say, Directive, Fallback, GameOver` and the mandatory trailing summary row (`type`, `turns`,
`events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook (§Sim module) building `Dockerfile.replay-viewer`'s `replay-viewer-builder`
target and copying the dist out. It stays committed **executable**. No `/client/replay` live-server
viewer is ever declared to the platform; the game still serves `/client/replay` locally for
developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/snake_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
this repo's own starter. **Never a mixture.** Splicing one starter's shell onto another's emscripten
link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer
silently (cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one piece:

- the Worker sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`), so the module is
  emitted **non-modularized** as `snake_replay.js`;
- `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang` through `emcc`, `--mm:arc
  --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`, `--preload-file data@data`,
  `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable, and the starter's own comment
  explaining it is kept verbatim: with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has
  no memory protection, so a failed allocation would write a seq header through nil into address 0 and
  silently corrupt the module's own globals), `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`,
  `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, and
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_snake_load_replay,_snake_frame,_snake_input,
  _snake_packet_ptr,_snake_packet_len,_snake_mismatch_tick,_snake_error_ptr,_snake_error_len,
  _snake_stage_ptr,_snake_stage_len`;
- `static_replay_worker.js` does
  `importScripts('./wire_constants.js', './broadcast_core.js', './snake_replay.js')` in that order
  (the starter's line 239, renamed only).

`snake_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress buffer
that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `snake_load_replay` re-simulates the whole episode once headlessly (≤ 50
  turns × 4 snakes of integer work plus one bounded BFS each — under a millisecond in wasm), and
  records the per-turn length series, the per-turn alive count, the `duel` turn, every beat turn and
  the lull spans, then resets and renders frame 0. That is what lets the length ribbon, the momentum
  graph and the scrubber beats draw at **full width on the first frame** instead of growing in.
- `snake_mismatch_tick` returns `checkReplayHash`'s divergence turn, or `−1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (starter line 161) — posted by the Worker only
*after* `ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute
means "a frame is on the canvas", not "a file was fetched". On failure it sets **`data-replay-error`**
on `<html>` with the message, in `showFailure()` (starter lines 8-20). Both are coworld-ctf's own
signals, inherited unchanged — this fork adds neither and removes neither. The `coworld-replay`
postMessage bridge's `ready` is posted **from a callback fired after** `data-replay-loaded="true"` is
set, never on rAF timing at the call site (chorus `3c11c953`, 2026-08-24), or the softmax.com embed
samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes in the starter). Not edited, not
  reformatted; `tests/test_snake_viewer.nim` pins its sha256 against the starter's file. Everything
  this game adds lives in the appended game block. Its `markBeat` / `renderBeatMarkers` /
  `ingestBeats` / `renderClock` / `renderTransport` / `ingestLullSpans` / `renderMomentum` remain, and
  `ingestBeats` ignores kinds it does not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (lines 4276-4325), transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density system
  are untouched, and the block is installed through the starter's **own splice hook**:
  `window.PaintballChrome` is renamed `window.SnakeChrome` and its `install(PB_CTX)` /
  `frame(s, ctx, jumped)` / `event(e, s, ctx)` entry points (starter lines 4337, 2075, 3480-3481,
  defined at 4651) keep the same signatures and the same `PB_CTX` contents
  (`$, C, esc, fmt, send, pushFeed, banner, getState, …`, lines 4331-4336). The appended block replaces
  only the *contents* of the scorebug plates, adds the length ribbon and the duel banner, and retargets
  the feed rows, the beat rendering, the momentum series and the endcard columns.
  `tests/test_snake_viewer.nim` asserts the file begins with the starter's bytes up to the documented
  splice marker and only appends after it.
- **`client/broadcast_core.js` is forked** — it is paintbot's continuous-2-D draw layer and this game
  is a grid. Kept and pinned function-by-function against the starter's text: the canvas/DPR sizing,
  `relayout()`, the camera, the feed queue and **`pushFeed` including its signature**
  (`replay_broadcast.html:3558` — the cogball 0.1.4 latch scar: a signature drift threw mid-replay and
  latched `static_replay.js` into `failed`), `banner`, the beat and lull machinery, the endcard
  builder, the speed chips, the `?embed=1` path, the shout-bubble renderer, and the
  `window.CTF_WIRE` → `window.SNAKE_WIRE` rename emitted by `tools/gen_wire_constants.nim`. Deleted:
  every weapon, paint, hill, flag and fog draw call, the FPV pipeline and `attachMinimap`'s callers.
  Added: `drawGrid`, `drawSnakes` (segments, head sprite, tail taper, dead-wreck fade),
  `drawFood`, `drawTrails` (tron), `drawWrapGhosts` (geese), `drawLengthRibbon`, `drawTrappedRing`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `core.attachMinimap($('minimap-canvas'))` call
    (`replay_broadcast.html:4200`). **Zoom decision: DROPPED ENTIRELY.** All three boards are small,
    fixed rectangles with no off-frame area; `relayout()` letterboxes each whole at every width, so per
    the pin ("the zoom bar + minimap exist only for boards larger than the frame — a fixed arena
    removes them") this arena removes them. `broadcast_core.js` already tolerates never being attached:
    `minimapSurface`/`minimapCtx` (starter lines 540-541) stay null and `drawMinimap()` returns on its
    first guard.
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — this game is perfect
    information and the whole board is on screen; a single-snake inset would show strictly less.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture`, `.hillflip`, `.tagout` and `.gamestart`
    CSS rules (starter lines 919-934, 4431-4443) — those kinds are never emitted here. `.gameover`
    keeps its rule; the other six kinds get new ones.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with
    `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`/`#ffwd-mini`, `#bannerlane`,
    `#killfeed`, `#mmwarn`, **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`,
    `#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`,
    `#tick-clock`, `#speedchips`), `#scrub` with
    `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/`#scrub-head`, `#endcard` with
    `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`, and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here and
enforced by a test:

| Starter string (`client/replay_broadcast.html:line`) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (3795) | `<span>Cog</span><span>Place</span><span>Turns</span><span>Length</span><span>Ate</span><span>Soft</span>` |
| `<span class="fl-cap">Lives left</span>` (3793) | `<span class="fl-cap">Turns survived</span>` |
| `<span class="fl-cap">Hill time</span>` (3786) | `<span class="fl-cap">Final length</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (1576) | `<span class="momentum-label">LENGTH</span>` |
| `<span class="lives-label">Lives</span>` (2241) | `<span class="len-label">Len</span>` |
| `<span class="lives-label pb-lbl">Hill</span>` (2224) | `<span class="hp-label">HP</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (1480) | "Coiling up…" |
| `#clock-caption` "In the locker room" (1499) | "Before the first move" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (1524) | "Replay hash mismatch at turn N — showing recorded moves" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline ahead of the playhead (o)" (1564) | "deaths / head-ons / winner on the timeline ahead of the playhead (o)" |
| team words `RED`/`BLUE` in `ec-tname`/plates | the four aliases and their colour chips — there are no teams |

**`tests/test_snake_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `spray`, `grenade`, `med kit`, `kill`, `HP pips`, `RED`, `BLUE` — outside comment
blocks, and asserts **zero** matches; and asserts each replacement string above is present exactly
once. A rename that reintroduces paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (starter lines 4291-4318). **No overlay sits in the transport band**: the board is
laid out between the two bands and every addition here (the length ribbon, the duel banner, the feed,
the say bubbles) is positioned inside the board region or in the top band. The **endcard stops at
`var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule at line 1047, kept) so the
scrubber stays clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept).

**Scrubber beats are clickable, labelled buttons.** The appended block's
`snakeBeat(s, turn, kind, colour, label)` — named so it can never shadow `chrome_common.js`'s
`markBeat` alias (the tandem 2026-08-23 hoisting trap; a scope-duplication test over the alias list
enforces it) — appends
`<button class="beat-marker <kind> <colour>" title="…" aria-label="…">` to `#scrub` and seeks on
click. CSS exists for **every kind emitted and no others**: `.beat-marker.eat`, `.headon`, `.death`,
`.trapped`, `.duel`, `.fallback`, `.gameover`. The game block never calls `markBeat`, so an unlabelled
div marker cannot appear.

**Playback rate: `renderFramesPerTurn = 12` at `ReplayFps = 24`** — 0.5 s per turn, speed chips
`[1, 2, 3, 4, 8, 16]` (the starter's `PlaybackSpeeds`, default **1×**). A 50-turn episode plays for
**25 s**; the 40-turn certification replay for **20 s**, which is what lets `viewer_smoke.mjs --soak 10`
observe real advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar).
**Duel slow-mo:** from the pre-scan's `duel` turn (the turn `aliveCount` first reaches 2) the block
doubles `renderFramesPerTurn` to 24, i.e. half speed, and shows `DUEL — half speed` in `#bannerlane`
(the top band, never the transport band). The speed chips still override it.

### Readouts

1. **The board**, drawn edge to edge: a subtle grid on a dark felt floor; walls as a lit border
   (`royale`, `tron`); in `geese` the border is replaced by **wrap ghosts** — a dimmed one-cell repeat
   of each snake's head and body across the opposite edge, so a spectator can see where a snake is
   about to reappear on a torus. Snakes are chunky rounded segments in their colour with a head sprite
   (eyes, facing) and a tapering tail; a snake that ate this turn flashes its new segment; a dead snake
   fades to a grey wreck over 6 render frames and clears. In `tron` the trail is drawn as a solid neon
   wall instead of segments, because a light cycle is a wall.
2. **Food** as apples on the grid, with a soft pulse; `foodspawn` pops a new one in.
3. **Head-on halo** — on the turn two heads target one cell, both approach cells flash and the loser's
   head cracks. This is the game's most-brutal rule and it must not be a silent disappearance.
4. **Trapped ring** — a snake whose `freeSpace < length` gets a red ring on its head and a red border on
   its plate. It is a **measured fact** from the resolver, not a prediction (§Out of scope explains why
   the idea's full "trapped prediction overlay" is deferred).
5. **Scorebug plates** — two in `#plates-l`, two in `#plates-r`: each carries the seat's **real policy
   name** (spectator side only), its in-game alias, its colour chip, its **length** as a big numeral, a
   health bar (drawn only when `healthStart > 0`), a place badge once dead, and a `↯` glyph on any seat
   that has taken a fallback. The big central numeral is `ALIVE 3/4`.
6. **Clock** — `#clock` shows `ALIVE 3/4`; `#clock-time` shows `turn 17/50`; `#clock-caption` shows the
   module line `royale · 17×9 · walls · food 3 · health on`.
7. **Length ribbon** — the starter's `#momentum` SVG retargeted: four length series across the whole
   episode in the snakes' colours, deaths marked with a cross at their turn, drawn **full width from
   the pre-scan on the first frame**, with the playhead crossing 1:1 with the scrubber. It is the score
   drawn literally: the line that stays on the chart longest wins.
8. **Match feed** (`#killfeed`) — plain language, never internal notation:
   `COG-beta eats — length 6`, `COG-delta runs into the north wall`,
   `HEAD-ON — COG-alpha (8) beats COG-gamma (6)`, `HEAD-ON — COG-beta and COG-delta both die (7 v 7)`,
   `COG-gamma is TRAPPED — 4 free cells, length 6`, `COG-alpha starves`,
   `HUNGER — everyone loses a segment`, `COG-beta declines a free head-on with COG-delta`,
   `COG-alpha: "north lane is mine"` (with the bubble on the board), and
   `COG-delta MISSED THE CALL — coil move (timeout)`.
9. **Say bubbles** on the board above the head. The bubble's box is laid out from `MaxSayRunes = 24`
   **measured in `data/font.ttf`** and clamped inside the board rect, so a bubble on a top-row snake is
   never drawn at a negative y (the cogchemists 2026-08-24 scar); `--strict-text-bounds` stays on in CI
   and `canvas_text.never_inside` must be 0.
10. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
    6 consecutive turns with no `eat`, `headon`, `death`, `trapped` or `decline` event, from the
    pre-scan), spoilers switch, turn readout, speed chips, the scrubber with its seven beat kinds, and
    `#mmwarn` on a hash mismatch — all the starter's, verbatim.
11. **Endcard** — `COG-alpha SURVIVES — 11 long, 8 eaten, 37 turns`, then the four-row table under the
    re-mapped header (`Cog | Place | Turns | Length | Ate | Soft`), the seat scores, and a module
    summary (`royale · 17×9 · walls · 3 food · last standing at turn 37`). It stops at `var(--band)`
    and any seek dismisses it.

### Art

**Real art, no placeholders, no solid-colour squares.** Two sources, both committed:

- **Snake kit — nano-banana** (`playbooks/art-nanobanana.md`, `gemini-2.5-flash-image`, ≤ 3 generations
  total). One sheet: a top-down segmented snake in **four colourways** (amber, teal, violet, lime), each
  with a **head** in four facings (up/right/down/left, with eyes and a small screen-face visor so it
  reads as a Softmax cog snake, anchored on the starter's own cog reference as an `inline_data` part), a
  **body** segment, a **corner** segment, and a **tail** segment. The sheet is chroma-keyed and split by
  `scripts/art/split_snake_sheet.py` into `data/snake_<colour>_{head_u,head_r,head_d,head_l,body,corner,
  tail}.png`, committed alongside `scripts/art/source/snakes_sheet.png`, and fed to the starter's
  **existing** `rig_art.nim` bake plumbing (renamed `snake_art.nim`; same masters/pivots/scale path) so
  every piece is baked once at `cellPx` and composited per turn. A second generation produces
  `data/food_apple.png` and `data/wreck.png` (the grey remains of a dead snake) in the same style.
  Colours read at board scale without labels, which is the point of the rule.
- **Board and chrome — the starter's shipped assets plus install-time bakes.** The floor is
  `data/arena_floor.png` tiled and darkened 22 % with the grid stroked over it; the wall border is
  textured from `client/art/walls/{wall_h,wall_v}.jpg`; the tron trail, the head-on flash, the trapped
  ring, the length ribbon and the say bubbles are procedural in the bake's palette
  (`data/pallete.png`); labels and numerals are `data/font.ttf`. The loading screen is the starter's
  locker room (`client/art/lockerroom/bg.jpg` plus the colour webps) with the caption re-labelled. If
  the Gemini endpoint is unavailable at build time the builder falls back to recolouring the starter's
  `soldier_*_front.png` masters into head sprites and says so in `log.md` — never a flat rectangle.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (starter lines 4307-4312).

The arithmetic: in a 360 × 203 frame, the two measured bands at `--hudscale = 0.5` come to ≈34 px
(scorebug) + ≈46 px (transport), so `availH ≈ 123`. `royale`'s board is 17 × 9 cells = 544 × 288 map
px, aspect **1.889**, and `boxW / availH = 360/123 = 2.93 > 1.889`, so **height binds**: the board
renders at **232 × 123**, i.e. **13.7 screen px per cell**. `geese` (11 × 7, aspect 1.571) renders at
**194 × 123**, **17.6 px per cell**; `tron` (21 × 9, aspect 2.333) at **287 × 123**, **13.7 px per
cell**. The 17 × 9 shape was chosen *because* 1.889 is close to the frame's own aspect — a taller board
would shrink every cell without adding play. At desktop widths everything scales up linearly and the
whole board is always in frame, which is why `#viewpanel` is dropped.

Four rules are added and asserted by `tests/test_snake_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps only `colour chip + name + length`; the health bar becomes a 3 px
   underline on the chip and the fallback glyph moves inline.
3. Under `.tiny`, cell coordinates are never drawn on the board and the say bubble's font floor is
   9 px × `--hudscale` with the bubble clamped inside the board rect; the trapped ring and the head-on
   flash keep full weight — those are the two things a spectator must not lose.
4. Under `.tiny`, the length ribbon keeps full width and halves in height, and the feed shows three
   rows instead of four. Every size derives from `--hudscale`, so nothing is drawn outside the canvas
   (`--strict-text-bounds` stays on).

---

## Packaging

- **Repo**: `Metta-AI/cogame-snake-royale`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `snake-royale`; **`game.name` is
  `snake-royale`** so the secret namespace `secret://coworld/snake-royale/anthropic_api_key`, the page
  slug `softmax.com/snake-royale`, the `POST /coworld-league-seeds` body and the docs all agree (the
  cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name by uppercasing and mapping `-` → `_` (`{{GAME_IMAGE}}` is not a thing —
  lantern 0.1.0). ctf ships two services/two images; this fork uses the one-image / two-entrypoints
  shape because the shared `docker_smoke.sh` and `policies.json` assume a single image (the
  knights-archers precedent):

  ```yaml
  services:
    snake-royale:
      image: coworld-snake-royale:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder **`{{SNAKE_ROYALE_IMAGE}}`**.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4` — the starter's `Dockerfile:29`, not the README's local 2.2.10 —
  `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:snake-royale src/snake_royale.nim`
  → `/bin/snake-royale`, and the same for `src/snake_royale_player.nim` → `/bin/snake-royale-player`.
  The runtime stage copies both binaries, `data/`, `client/` and `*.json`.
  `CMD ["/bin/snake-royale"]`, runtime `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby 0.1.27 with its sha256 check, `nimby use 2.2.4`, the marker `sed` splices, the whole
  `test -f` / `grep -q` assertion block) with three named edits: the `WORKDIR` becomes
  `/workspace/snake`; the `league.html` splice and its four assertions are **deleted** with
  `client/league_replayer.html`; and the asset list is swapped to
  `data/{arena_floor,ascii,pallete}.png`, `data/snake_*_{head_u,head_r,head_d,head_l,body,corner,tail}.png`,
  `data/{food_apple,wreck}.png`, `data/font.ttf`, `client/art/walls/*`, `client/art/lockerroom/*`,
  `snake_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`. The `grep -q '^window.CTF_WIRE={'`
  assertion becomes `'^window.SNAKE_WIRE={'`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["snake", "free-for-all", "grid", "survival",
    "simultaneous"]` (≥ 3; **`game.tags` must not exist** — pistonball 0.1.0);
    **`episode_timeout_minutes: 20` at the top level**, not under `game`.
  - `game.name = "snake-royale"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/snake-royale"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/snake-royale/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 4/4, `players` 4/4, `slots` 0/4 — the tandem 0.1.0 scar). `tokens` is described as
    runner-injected; **no `game_config` anywhere in this manifest contains a literal `tokens` array**
    (matriculate rejects "game_config must not include runner-managed tokens" — knights-archers
    0.1.0), while `config_schema` keeps *requiring* it because the runner injects it. Properties:
    `tokens`, `players`, `slots`, `seed`, `module` (enum `["royale","geese","tron"]`, default
    `"royale"`), `boardW` (7–31), `boardH` (5–21), `wrap`, `foodCount` (0–8), `healthStart` (0–200),
    `shrinkEvery` (0–200), `leaveTrail`, `headToHead` (enum `["longer_wins","both_die"]`),
    `startLength` (1–5), `maxTurns` (5–200), `renderFramesPerTurn` (1–48), `sayTurns` (0–8),
    `attempt1Ms`, `retryMs`, `turnBudgetMs`, `turnSpacingMs`, `wallClockBudgetSeconds`,
    `lobbyJoinTimeoutSeconds`, `gameOverTurns`, `minPlayers`, `fastMode`, `showPlayerLabels`, and
    **`num_agents` (integer, `minimum: 4`, `maximum: 4`, default 4)**.
    **`slots` is declared (0/4) for the starter's `GameConfig` and is absent from every `game_config`**
    — a free-for-all has no sides, and the colour/spawn deal comes from the seeded `spawnDeal`, not
    from `slots`.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}` and
    `endRule: {"type":"string","enum":["last_standing","full_time","wall_clock","sim_fault","host_error"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-snake-royale/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar). Both point at the same document because
    both streams speak the same wire types, exactly as the starter declares them.
  - **`game.docs`** = `{"readme": {"type":"text","value":"<the README body, inlined>"},
    "pages": [{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined>"}}, {"id":"modules.md","title":"Rule modules","content":{"type":"text","value":
    "<docs/MODULES.md inlined>"}}, {"id":"protocol.md","title":"Wire protocol","content":
    {"type":"text","value":"<docs/PROTOCOL.md inlined>"}}]}` — inlined text so the pages render before
    the repo is indexed.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "200m", memory: "128Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). Two entries, `coil` and `forager`, so **every declared
    player occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 4` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0). Three variants ship in v1, one per rule
  module:

  ```json
  "variants": [
    {"id": "royale",
     "name": "Snake Royale (4 snakes, walls, food, longer head wins)",
     "description": "Four snakes on a 17x9 walled grid. Every turn all four move one cell at the same time. Food makes you longer and refills your health, health drains one a turn, and a head-on is won by the strictly longer snake - equal lengths both die. Run into a wall, into anybody's body including your own, or out of health, and you are gone. Last snake alive takes the round; placement pays +1.000, +0.333, -0.333, -1.000 and the four scores always sum to zero.",
     "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},{"name":"Cog4"}],
                     "num_agents": 4, "minPlayers": 4,
                     "module": "royale", "boardW": 17, "boardH": 9, "wrap": false,
                     "foodCount": 3, "healthStart": 30, "shrinkEvery": 0, "leaveTrail": false,
                     "headToHead": "longer_wins", "startLength": 3, "maxTurns": 50,
                     "renderFramesPerTurn": 12, "sayTurns": 2,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 11000, "turnSpacingMs": 9000,
                     "wallClockBudgetSeconds": 640, "lobbyJoinTimeoutSeconds": 90,
                     "gameOverTurns": 2, "fastMode": true, "showPlayerLabels": false}},

    {"id": "geese",
     "name": "Hungry Geese (4 geese, 11x7 torus, hunger every 20 turns)",
     "description": "The Kaggle board: four geese on an 11x7 torus with no walls at all - leave the left edge and you come back on the right. Two apples are always out. There is no health; instead every twentieth turn everybody loses a segment, so a goose that stops eating starves down to nothing. A head-on kills everyone in the cell no matter who is longer, which makes the torus's blind corners genuinely dangerous. Last goose standing.",
     "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},{"name":"Cog4"}],
                     "num_agents": 4, "minPlayers": 4,
                     "module": "geese", "boardW": 11, "boardH": 7, "wrap": true,
                     "foodCount": 2, "healthStart": 0, "shrinkEvery": 20, "leaveTrail": false,
                     "headToHead": "both_die", "startLength": 3, "maxTurns": 50,
                     "renderFramesPerTurn": 12, "sayTurns": 2,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 11000, "turnSpacingMs": 9000,
                     "wallClockBudgetSeconds": 640, "lobbyJoinTimeoutSeconds": 90,
                     "gameOverTurns": 2, "fastMode": true, "showPlayerLabels": false}},

    {"id": "tron",
     "name": "Tron light cycles (4 cycles, no food, the trail never clears)",
     "description": "The same engine with growth and food switched off: four light cycles on a 21x9 walled grid, each leaving a permanent wall behind it. Nothing is ever eaten and no tail ever vacates, so the board only fills. There is nothing to optimise except space - every turn is a choice about whose room closes first, yours or theirs. A head-on kills everyone in the cell. Last cycle running.",
     "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},{"name":"Cog4"}],
                     "num_agents": 4, "minPlayers": 4,
                     "module": "tron", "boardW": 21, "boardH": 9, "wrap": false,
                     "foodCount": 0, "healthStart": 0, "shrinkEvery": 0, "leaveTrail": true,
                     "headToHead": "both_die", "startLength": 1, "maxTurns": 50,
                     "renderFramesPerTurn": 12, "sayTurns": 2,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 11000, "turnSpacingMs": 9000,
                     "wallClockBudgetSeconds": 640, "lobbyJoinTimeoutSeconds": 90,
                     "gameOverTurns": 2, "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 4` again, inside `certification.game_config`, and exactly
  four players so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS
  == 4` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks), with **both** declared
  players seated:

  ```json
  "certification": {
    "players": [{"player_id":"coil"},{"player_id":"forager"},
                {"player_id":"coil"},{"player_id":"forager"}],
    "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},{"name":"Cog4"}],
                    "num_agents": 4, "minPlayers": 4, "seed": 42,
                    "module": "royale", "boardW": 17, "boardH": 9, "wrap": false,
                    "foodCount": 4, "healthStart": 60, "shrinkEvery": 0, "leaveTrail": false,
                    "headToHead": "longer_wins", "startLength": 3, "maxTurns": 40,
                    "renderFramesPerTurn": 12, "sayTurns": 2,
                    "turnSpacingMs": 0, "wallClockBudgetSeconds": 200,
                    "lobbyJoinTimeoutSeconds": 45, "gameOverTurns": 2,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  Forty turns is milliseconds of sim but **20 s of playback**, which the viewer soak needs.
  `foodCount: 4` and `healthStart: 60` are raised above the league values so nobody starves out of a
  40-turn fixture. `turnSpacingMs: 0` because certification runs with no API key and every seat is
  scripted. **Seed 42 is asserted by `tests/test_snake_engine.nim` to produce a fixture episode that
  runs at least 34 turns and contains at least one `eat`, one `headon` and one `death`**, so the CI
  smoke replay always exercises the beats, the feed and a soak longer than 10 s; if a rules change
  makes seed 42 uninteresting, `tools/scan_event_seeds.sh` (the starter's) picks the next seed and the
  test's pinned literal moves with it in the same commit. The certify step in `coworld-release.yml`
  passes **`--timeout-seconds 300`** (the default 60 covers start + connect grace + play + linger —
  cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/snake-royale-player"`,
  following the starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"snake-royale-strangler","run":"/bin/snake-royale-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"strangler"}},
   {"name":"snake-royale-glutton","run":"/bin/snake-royale-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"glutton"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"snake-royale-coil","run":"/bin/snake-royale-player",
    "env":{"PLAYER_SCRIPTED":"coil","PLAYER_POLICY_LABEL":"coil"}},
   {"name":"snake-royale-forager","run":"/bin/snake-royale-player",
    "env":{"PLAYER_SCRIPTED":"forager","PLAYER_POLICY_LABEL":"forager"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `coil` and `forager`, and their
  versions must differ from the champions'. **No `USE_BEDROCK` flag**: the LLM call is made by the
  **game** pod (§Decisions).
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps
  the template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `snake-royale`,
  `<IMAGE>` → `coworld-snake-royale`, `<SEATS>` → **`4`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0`
  (§Server) and `--soak 10` added to the `viewer_smoke.mjs` invocation. `coworld-release.yml` and
  `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on the certify step.
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed **executable**
  (mode 100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_snake_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in both
debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_snake_sim.nim`)

1. `board and wrap` — `step()` wraps on all four edges when `wrap`, leaves the board when not; the four
   derived spawn anchors are in bounds, distinct, and at least three cells apart on every shipped board.
2. `spawn` — every snake starts `startLength` segments stacked on its anchor with `last_dir` toward the
   centre; on turn 1 all four directions are legal because there is no neck.
3. `neck repair` — naming the neck falls to `alt`, then to `last_dir`; `reverseRepaired` counts it;
   `alt` equal to the neck is skipped; a length-1 snake has no neck and every direction stands.
4. `wall deaths` — with `wrap` false, a head leaving any of the four edges dies with cause `wall`; with
   `wrap` true it never does.
5. `eat and grow` — a head onto food removes the food, keeps the tail this turn (length +1), sets
   `health = healthStart` and emits `eat`; a head onto no food pops the tail and the length is
   unchanged.
6. `tail follow` — a snake may enter the cell a rival's tail vacates this turn and lives; it may **not**
   enter the tail cell of a rival that ate this turn, and dies with cause `body`.
7. `head-to-head` — under `longer_wins`, the strictly longest survives and the rest die with
   `killedBy` = the winner; an equal-length pair both die; a three-way with two equal leaders kills all
   three; under `both_die` everyone in the cell dies regardless of length. Post-step-8 lengths are the
   ones compared.
8. `head-on precedes body` — the head-on winner is **not** then killed by the loser's neck; reordering
   the two steps flips the outcome, which is why the test exists.
9. `corpses do not free cells` — a snake that starved or hit a wall on turn T still blocks a rival's
   head on turn T; it stops blocking on turn T+1.
10. `hunger` — with `healthStart > 0`, health drains one a turn, resets on food and kills at 0 with
    cause `starve`; with `shrinkEvery > 0`, every live snake loses a segment on the right turns and a
    snake at length 0 dies.
11. `tron` — with `leaveTrail`, no tail ever pops, length grows every turn, no food is ever placed, and
    a snake that fills its own region dies with cause `body`.
12. `food respawn is seeded` — the food sequence is a pure function of `seed xor 0x5EED` and the
    resolution order; replaying the same directions on the same seed places identical apples; changing a
    snake's direction changes which cells are free but not the RNG stream's draw order.
13. `free space` — `freeSpaceFrom` equals a from-scratch BFS on 500 randomised boards; the cap is
    honoured; a snake sealed in a pocket reports fewer free cells than its length and emits `trapped`
    exactly on the transition.
14. `declined kills` — the audit counts exactly the turns matching its definition, over 200 scripted
    situations, and counts zero when the seat takes the kill.
15. `scoring` — `scorePermille` matches the formula for 1000 randomised end states; the four values sum
    to **exactly 0** for every tie shape (no tie, 2-way, 3-way, 4-way, and a tie spanning places 2-4
    where naive `div` loses a permille); `scores ∈ [−1, +1]`; `win[s] == (place[s] == 1)`.
16. `end conditions` — `last_standing`, `full_time`, a forced wall-clock stop and a forced fault each
    produce the right `endRule` and the right `reason`; a deadline mid-episode still ranks and still
    sums to zero; an all-four-die turn ends `complete`/`last_standing` with the length tie-break applied.
17. `no floats in hashed code` — a source grep over `src/snake/{board,rules,space}.nim` finds no float
    literal, no `/` and no `sqrt`.
18. `turn budget` — a full 50-turn, four-snake, all-scripted episode on the largest board completes in
    < 1 s in a release build, and no single turn exceeds 3 ms.

**Upstream and seeding**

19. `tests/test_snake_upstream.nim` — the shipped constants in `src/snake/upstream.nim` equal the table
    at the head of this note, and the five documented divergences are present with their citations. A
    constant edited without editing the citation fails.
20. `tests/test_snake_seeding.nim` — `spawnDeal` is a pure function of the seed, is drawn **before any
    seat connects**, and does not change when seat behaviour changes; `foodRng` is stream-separated from
    `setupRng`; the same seed on the same module produces the same opening board (the anti-collusion
    pin).
21. `tests/test_snake_determinism.nim` — re-simulate from the replay's seed and recorded direction bytes
    alone on a fresh sim; identical final turn, bodies, food, health, alive flags and per-turn
    `gameHash`.

**Bounded orders / legality on the scripted baselines** (`tests/test_snake_control.nim`)

22. `baselines are bounded` — for 500 pseudo-random world states (all three modules, every slot, every
    length from 1 to 20, boards from empty to nearly full) and for **both** `coil` and `forager`: the
    returned object has a `dir` in the enum, an `alt` in the enum or absent, `say` and `notes` empty, a
    serialised directive ≤ 1024 bytes, and **the returned direction is never the neck**. A baseline that
    ever proposes an out-of-enum or neck direction fails the build.
23. `baselines never leave a snake unactuated` — over the same states, including states where every
    direction is fatal, a direction is always returned (`last_dir` in the sealed case) and the snake
    dies rather than the loop stalling.
24. `baselines agree with the resolver` — for every state, every direction the baseline scored
    `-infinity` is one the resolver would have killed the snake for, and every direction it scored
    finite is one the resolver accepts. The predicates are the same procs, and this test is what stops
    a second copy appearing.
25. `fallback is the coil proc` — the decision engine's fallback path and the `coil` baseline resolve to
    the same proc, so they cannot drift.
26. `reply validation` — the validator accepts the schema; **repairs** an unknown `dir` to `alt`, then
    `last_dir`, then the first legal direction; accepts `dir` in any of the tolerated spellings; accepts
    a reply with only `dir`; rejects a non-object; truncates `say`/`notes` on **rune** boundaries at
    24/160 with 4-byte emoji sitting exactly on each boundary; caps the read at 4096 bytes; and never
    leaves a snake without a direction.
27. `baseline tuning is the swept pick` — the shipped six tunables per baseline equal
    `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern; `ci.yml` re-runs the sweep with
    `--check`), and `coil`'s mean score over the recorded 24-episode ladder beats `forager`'s by a margin
    inside `[+0.30, +1.20]`.

**End-to-end episode writing a replay** (`tests/test_snake_engine.nim`)

28. `episode writes artifacts` — run a real four-seat episode (`royale`, `maxTurns 40`, all seats
    scripted, no API key so the LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert
    `results.json` and the `.replay` are written, `reason == "complete"`,
    `endRule ∈ {"last_standing","full_time"}`, `sum(scorePermille) == 0`, every seat-indexed array is
    4 long, and the results key set equals the manifest's `results_schema` key set **exactly**.
29. `the cert seed is interesting` — seed 42 on `royale` with the fixture's config runs ≥ 34 turns and
    yields ≥ 1 `eat`, ≥ 1 `headon` and ≥ 1 `death`, so the CI smoke replay always exercises the beats
    and outlasts the 10 s soak.
30. `every variant runs` — each of the three shipped `game_config`s constructs a valid `GameConfig`,
    builds its board, plays a full scripted episode and produces the module's claimed board size, food
    count and death causes (the collab-cooking 0.1.1 scar: test every variant, not just the fixture).
31. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, the loud unregistered-seat log line present, and exactly one closed-schema
    `{"message","failed_policy_index"}` failure payload.
32. `budget guard settles early` — with the guard forced, the episode finishes `complete`, not
    `deadline`, and the `budget_guard` record names the turn.

**Replay** (`tests/test_snake_replay.nim`)

33. `record then re-derive, every end reason` — for `last_standing`, `full_time`, `wall_clock` **and**
    `sim_fault`, record an episode and re-derive it from the bytes; assert identical `gameHash` at every
    turn **including the stop turn** (the particle-worlds scar).
34. `replay is self-sufficient` — the bytes alone yield seat names, aliases, colours, policy kinds, the
    full config **including the board document, the module and `spawnDeal`**, the seed, every direction
    byte, every chat record and the result; deleting every file in `data/` except the art does not change
    what the bytes render.
35. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports
    `protocol == "snake-royale/v1"`.
36. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`, kept.

**Manifest** (`tests/test_snake_manifest.nim`)

37. `manifest pins` — `num_agents == 4` in **all three** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens` in
    any `game_config`; no `slots` in any `game_config`; `len(player) == 2` and every declared player
    seated in `certification.players`; `len(certification.players) ==
    len(certification.game_config.players) == 4`; every array in `config_schema` has
    `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both `game.protocols.player` and
    `.global` present as `{"type","value"}` objects; `game.docs.readme` + three `pages`, every value
    non-empty text; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 640`; every variant's
    `maxTurns ≤ 60`; and `game.replay_viewer.bundle == "static-replay-viewer"`.
38. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` — the
    collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_snake_viewer.nim`, static assertions in the `test` job)

39. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals the starter's, pinned
    as a literal (40 022 bytes).
40. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker and only appends after it; `broadcast_core.js`'s kept procs are
    byte-identical to the starter's, **`pushFeed`'s signature included**.
41. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap); the beat builder is `snakeBeat`, never
    `markBeat`.
42. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{eat, headon, death, trapped, duel, fallback, gameover}`.
43. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band;
    the four 360 px rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`, `#fpv*`,
    `#povBadge`, …) appear nowhere.
44. `endcard labels` — `tests/test_snake_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
45. `label manifest` — the starter's `test_label_contract` pattern: the emitted board-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
46. `events are the closed enum` — `tests/test_snake_events.nim`: the set of kinds `stepEvents` can emit
    equals exactly the sixteen listed in §Server, and every kind used by the appended game block is in
    that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**

47. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`, no substitutions) is run by **`ci.yml`'s
    `wasm-viewer` job**, which `needs: docker-smoke` and runs it against **the replay `docker-smoke`
    produced** (downloaded as the `smoke-replay` artifact), in headless chromium (Playwright pinned
    1.55.0 in both the npm module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives, the clock/turn readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays on.
48. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `say` at all**, so the
    smoke replay can never exercise the bubble or the feed's say path (the cogchemists 2026-08-24 scar).
    The fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only
    the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) — driving
    the real page with a full-cap 24-rune `say` on all four seats **including a snake on the top row**
    (the negative-y bubble case), a three-way head-on, a trapped snake, a full length ribbon, the duel
    banner, and all three modules' board shapes, at several canvas widths including 360 px.
49. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm module
    against the committed fixtures, kept: wasm32-only failures (integer traps, address-space exhaustion)
    are invisible to the native shards. Three fixtures are committed and re-recorded on every
    `GameVersion` bump, one per module (`tests/fixtures/royale-seed42`, `geese-seed7`, `tron-seed13`),
    with their recipes in `tests/test_snake_replay.nim` (the starter's fixture-recipe discipline,
    `AGENTS.md` §Replay fixtures).

---

## Out of scope (v1)

- **The 'trapped' prediction overlay.** The idea asks for one; v1 ships the **measured** half — a
  `trapped` event and a red head ring the moment `freeSpace < length`, which is a fact the resolver
  already computes — and defers the *predictive* half: a per-cell heat map of "if you enter here you are
  dead in N turns". That needs a bounded game-tree search per cell per turn in the wasm pre-scan, a
  second colour channel on a 13.7 px cell at 360 px, and a claim the sim cannot verify. The measured
  version says the same thing one turn later and cannot ever be wrong.
- **Last-*three*-alive slow-mo, as literally asked.** With four seats, "last three alive" begins at the
  first death and covers most of the episode, so the slow-mo would be the normal speed. v1 ships the same
  idea retargeted to the **last two** (`duel`, half speed, with a banner), which is the moment that
  actually deserves it. §Viewer records the substitution.
- **Battlesnake hazards ("sauce").** A hazard region that drains extra health is a fourth rule-module
  axis, a fourth board layer in the renderer and a fifth thing in the observation. It is the obvious v2
  module and it needs a module of its own, not a switch bolted onto `royale`.
- **Seat counts other than 4, and 2-seat or 8-seat variants.** `num_agents` is fixed at 4 in every
  variant and in the cert fixture, for the batch-size, wall-clock and zero-sum-vector reasons in §The
  game. Two seats is a different game (heads-up Tron, no third party, no diplomacy) and eight needs a
  15 s spacing floor that halves the turn count; both are a different manifest and a different cadence.
- **Battlesnake HTTP API compatibility.** Serving `/start`, `/move`, `/end` so an existing Battlesnake
  bot could play here is attractive and is a whole second protocol surface, a second certification path
  and a second set of gotchas. The Coworld player socket is the only protocol in v1.
- **A bit-exact `hungry_geese` port.** `geese` reproduces the rules, not kaggle-environments' Python
  bytes; the five divergences are enumerated, cited and tested (§Upstream). Anyone wanting bit-exactness
  wants the `cogame-moba` starter and a different note.
- **Weekly rules rotation.** The idea names it as a candidate. The rule-module axis exists and is a
  manifest variant, so a rotation is a league-settings change, not a game change — but nothing in v1
  automates it, and no scheduler ships.
- **Scoring anything but placement.** `finalLength`, `foodEaten`, `declinedKills`, `trappedTurns` and
  `reverseRepaired` are measured, recorded in `results`, shown on the endcard and in the feed, and
  deliberately **not** in `scores`. Weighting them would need a magnitude the idea does not pin and would
  break the exact zero sum the league ranks on — and a scored `declinedKills` would turn the alliance
  audit into a thing to game rather than a thing to read.
- **A private team channel.** `say` is public to all four seats by construction. A private channel in a
  four-way FFA is a collusion machine with no audit trail, which is the exact failure the idea's
  integrity note names.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, bullets, hit points, lives, respawns,
  spray, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches, puddles, perks,
  handicaps, achievements, four-team play, campaign mode, fog of war and the vision cones, the
  first-person PIP, continuous 2-D motion, the procedural map generator, the map pool, the map editor and
  mapkit — all deleted, not disabled (§Sim module), and none of them return in v1.
