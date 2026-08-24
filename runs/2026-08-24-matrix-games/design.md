# Matrix Games — eight cogs, a yard full of tokens, and one payoff matrix that changes everything

**Starter: `Metta-AI/coworld-ctf` (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`.**
Matrix Games is a real-time grid loop whose rules are written fresh for this coworld — the first row
of the starter table. Paintbot supplies the tick loop, the sprite/board protocol, the per-tick
replay, the broadcast chrome, the static wasm replay bundle, the Dockerfiles and the CI shape.
**Every convention there holds here unless this note says otherwise.** The BitWorld / staghunt
runtime the source idea speculates about is **not available and is not used**; paintbot's engine is
the template that gets adapted. Two things paintbot does not have are ported from
`Metta-AI/cogame-bullwhip` (mounted at `/workspace/starters/cogame-bullwhip`) and are named as such
where they appear: the *game-side* batched LLM decision layer (`src/bullwhip/llm.nim`) and the thin
prompt-carrying player process (`src/bullwhip_player.nim`). **All four viewer files come from
coworld-ctf and from no other starter** (see `## Viewer`).

**Design pins (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins), each answered
explicitly:**

| pin | how Matrix Games satisfies it |
|---|---|
| starter by game shape | `Metta-AI/coworld-ctf` (paintbot) — a real-time grid loop with new rules, coordinator ruling of this run. |
| public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-matrix-games`, public (a certification prerequisite — `source-resolves` 404s on private). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | one image; `PLAYER_PROMPT="<strategy>"` vs `PLAYER_SCRIPTED=counter\|tit-for-tat\|fixed-pick\|always-first\|always-second` (`## Decisions`). Champions #1 `matrix-games-reader` (daveey) and #2 `matrix-games-brinkman` (daveey-1) are both prompt policies; the two fillers are scripted baselines. |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` viewer is declared (`## Viewer`, `## Packaging`). |
| real art, starter chrome verbatim | `scripts/art/gen_matrix_art.py` bakes eight liveries off paintbot's shipped `data/rig_real/*` rigs, the token glyphs, the yard floor and the loading art; `client/chrome_common.js` is copied **byte-for-byte** and `client/replay_broadcast.html` is the starter's page **with a game block appended** (`## Viewer`). |
| legible to a casual spectator | `BEAT 4 / 12`, plain-language feed rows ("EMBER zaps CEDAR — paper 0.71 vs rock 0.62 → +2.4 / −2.4"), a K×K matrix panel that pops the cell that was hit, inventory bars over each cog; checked at **360 px**. |
| two name spaces | anonymous aliases `Ash Birch Cedar Dune Elm Fern Gorse Holly` in-game; real policy names only in the replay's `policyNames[]`, the scorebug plates, the endcard and `results.names[]` (`## The game`). |
| degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | ≤ 480 s worst case against a 720 s budget, deadline checked between beats, retry-once-then-scripted, `shutdownGraceSeconds = 20` (`## Decisions`, `## Server, player, protocol`). |
| `num_agents` in every variant AND the cert fixture | **8**, in all seven variants, in `certification.game_config`, and as `<SEATS>` in `tools/ci/docker_smoke.sh` (`## Packaging`, `## Tests`). |
| prove it in CI | sim unit tests, a bounded-orders/legality assertion on the scripted baselines, a game-shape oracle, an end-to-end episode writing a replay, a strict-UTF-8 replay parse, and an **executed** viewer smoke (`## Tests`). |

**Source idea (verbatim):**

> Merged port of all Melting Pot *_in_the_matrix substrates — they share one engine (the_matrix.py): cogs roam a grid collecting K token types; inventory mix = strategy; an interaction beam between two cogs resolves a payoff matrix and (in some variants) resets both. Arena = 8 seats with random encounters; repeated = one fixed pair; one-shot = single resolution. Only the matrix and K change per game, so this is ONE coworld with a game variant:
>     Running with Scissors (K=3, cyclic zero-sum) — no fixed policy survives; feints and token denial matter because commitment is visible.
>     Prisoner's Dilemma (CC 3/3, DC 5/0, DD 1/1) — conditional cooperation with strangers.
>     Chicken (hawk/dove) — anti-coordination: who yields, with no words.
>     Stag Hunt (stag/stag 4, hare 2, stag-vs-hare 0) — assurance; risk- vs payoff-dominant equilibria.
>     Bach or Stravinsky — asymmetric: row (blue) and column (orange) camps, interactions only cross-camp.
>     Pure Coordination (three matches all pay 1) and Rationalizable Coordination (pay 1/2/3).
>
> Engine candidate: build on coworld-staghunt's BitWorld runtime if it certifies, else a small new grid engine.
>
> Seats: 2 (repeated/one-shot) or 8 (arena)
> Motive: varies by matrix — zero-sum, dilemma, anti-coordination, assurance, asymmetric, pure common interest
> Policy interface: per-tick move/turn/interact; LLM over a decoded board is feasible
> Fills gap: non-transitive payoffs (RPS), anti-coordination (Chicken) and asymmetric-camp coordination (BoS) exist nowhere else on the site; the matrix family is also Melting Pot's calibration core
> Integrity (anti-collusion): Melting Pot resident/visitor scoring with scripted background bots (always-C/D, always-hawk/dove, fixed-pick) so cogs are graded on adapting, not on codebooks; token spawns seeded; anonymous aliases.
>
> Replay plan (watchability): inventory bars over cogs; encounters pop the matrix cell hit; per-room indices (cooperation rate, exploitability, convention histogram).
>
> Absorbed cards: MP Prisoner's Dilemma, MP Chicken, MP Bach or Stravinsky, MP Coordination in the Matrix, and the matrix half of MP Stag Hunt.
> Source: meltingpot substrates *_in_the_matrix__{arena,repeated,one_shot}, the_matrix.py. Videos: RPS https://youtu.be/gtemAx4XEcQ , PD https://youtu.be/AAd9UcP0nk0 , Chicken https://youtu.be/94DHJ6BVEJM , Stag https://youtu.be/agOpo0MZmzs , BoS https://youtu.be/QstXaLjiqK4

---

## The game

### Seats, aliases, liveries, camps

`num_agents = 8`. **Exactly eight seats, in every variant, always.** All seven variants are
arena-mode: eight cogs in one yard, encounters are whoever you run into. The two-seat
repeated/one-shot modes are `## Out of scope (v1)`.

| slot | in-game alias | livery key | livery colour | BoS camp |
|---|---|---|---|---|
| 0 | `Ash` | `cobalt` | `#3f7cc4` | row (blue) |
| 1 | `Birch` | `sky` | `#6fb3e8` | row (blue) |
| 2 | `Cedar` | `moss` | `#45a85e` | row (blue) |
| 3 | `Dune` | `lime` | `#8fd26a` | row (blue) |
| 4 | `Elm` | `rust` | `#e0523a` | column (orange) |
| 5 | `Fern` | `ember` | `#f08a4b` | column (orange) |
| 6 | `Gorse` | `brass` | `#ddc531` | column (orange) |
| 7 | `Holly` | `plum` | `#b06fd0` | column (orange) |

Alias, livery and camp are a fixed function of the slot; nothing rotates. The `camp` column only
has mechanical meaning in the `bach-or-stravinsky` variant (rule 6 below); in every other variant
`camp` is reported as `"none"` and every cog is eligible against every other.

**Two name spaces (pin).** A seat sees only the eight aliases. No policy name, player name, account
or prompt of any other seat ever reaches a seat. The replay carries `policyNames[]` alongside
`names[]`; the viewer's plates, feed and endcard show the **policy** name; `results.names[]` carries
policy names for the platform.

### Board and clock

- One fixed arena, **24 cells wide × 14 cells tall**, rendered at 40 px/cell = a **960 × 560** board
  (12:7). It is the same map in every variant and never changes size, which is why `#viewpanel`
  (zoom bar + minimap) is dropped from the viewer.
- The map is committed as an ASCII constant in `src/matrix_games/arena_map.nim` (`#` wall,
  `.` floor). It is mirror-symmetric left–right and top–bottom, fully connected, 216 free cells:

```
########################
#....##..........##....#
#..........##..........#
#.##....#......#....##.#
#.##................##.#
#......##......##......#
#..##..............##..#
#..##..............##..#
#......##......##......#
#.##................##.#
#.##....#......#....##.#
#..........##..........#
#....##..........##....#
########################
```

- One episode = **12 beats × 50 ticks = 600 ticks**. Playback is 24 fps, so a full replay is
  **25 s** of video (longer than the 10 s viewer soak — the ecos rule).
- Every sim quantity is an **integer**: cell coordinates, facings (0=N, 1=E, 2=S, 3=W), inventory
  counts, payoffs in **centipoints**. The RNG is paintbot's seeded integer stream. No float enters
  sim state, so a seed reproduces a replay bit-exactly on any host (the determinism test depends on
  it).

### Tokens, zones, inventory

- The variant fixes `K` (2 or 3) and the token names. Token type `i` is drawn and reported in
  chrome colour `["red", "blue", "green"][i]`.
- **Spawners** are fixed cells that hold at most one token. They are chosen once at episode start
  from the seeded RNG (the idea's "token spawns seeded") and never move:
  - zone A (type 0): 16 spawners drawn from the free cells of the rectangle `x∈[1,7], y∈[1,5]`;
  - zone B (type 1): 16 spawners from `x∈[16,22], y∈[1,5]`;
  - zone C (type 2, K=3 only): 16 spawners from `x∈[8,15], y∈[8,12]`;
  - the **mixed scatter**: 12 spawners drawn from the free cells of the centre band `y∈[6,7]`, the
    `n`-th of which carries type `n mod K`.
  Total: 60 spawners when K=3, 44 when K=2. Every spawner holds a token at `t = 0`.
- A cog stepping onto a spawner cell that holds a token **collects it** (`pickup` event) unless that
  type is already at `tokenCap = 8`, in which case the token stays. A collected spawner refills
  `tokenRespawnTicks = 45` ticks later. Zone token counts are **public** — camping a zone to starve
  a rival ("token denial") is visible to everyone as a falling counter.
- Every cog starts, and after every resolution resets to, the **endowment**: 1 token of each type.
  So `N = Σ nᵢ ≥ K ≥ 2` always — the mix is always defined and there is never a divide-by-zero.
  Maximum purity is `8/9 = 0.889` (K=2) or `8/10 = 0.8` (K=3): commitment is expensive and never
  total, which is exactly the Melting Pot mechanic.
- **Inventory mix = strategy.** A cog's strategy at the moment of an interaction is the rational
  vector `xᵢ = nᵢ / N`.

### Payoff matrices (all seven, pinned)

Each variant names two integer `K×K` matrices, `rowPay` and `colPay`. For every symmetric variant
`colPay = transpose(rowPay)`; only `bach-or-stravinsky` differs. Matrices live in code
(`src/matrix_games/matrices.nim`), selected by the config string `matrix`.

| variant (`matrix`) | K | token names (index order) | `rowPay` | `colPay` | `coopToken` |
|---|---|---|---|---|---|
| `running-with-scissors` (**default**) | 3 | `rock, paper, scissors` | `[[0,-3,3],[3,0,-3],[-3,3,0]]` | transpose (= negation; zero-sum) | none |
| `prisoners-dilemma` | 2 | `cooperate, defect` | `[[3,0],[5,1]]` | transpose | `cooperate` |
| `chicken` | 2 | `dove, hawk` | `[[3,1],[4,0]]` | transpose | `dove` |
| `stag-hunt` | 2 | `stag, hare` | `[[4,0],[2,2]]` | transpose | `stag` |
| `bach-or-stravinsky` | 2 | `bach, stravinsky` | `[[3,0],[0,2]]` | `[[2,0],[0,3]]` | none |
| `pure-coordination` | 3 | `red, green, blue` | `[[1,0,0],[0,1,0],[0,0,1]]` | transpose | none |
| `rationalizable-coordination` | 3 | `bronze, silver, gold` | `[[1,0,0],[0,2,0],[0,0,3]]` | transpose | none |

Reading the table against the idea: RWS is cyclic zero-sum (paper beats rock, scissors beats paper,
rock beats scissors), scaled ×3 so one clean win pays the same 3 as PD's mutual cooperation;
PD is CC 3/3, DC 5/0, DD 1/1 exactly; chicken is T=4 > R=3 > S=1 > P=0 (mutual hawk is the crash,
0/0); stag hunt is stag/stag 4, hare 2, stag-vs-hare 0 exactly; BoS pays the row (blue) camp 3 for
Bach and the column (orange) camp 3 for Stravinsky, 0/0 on a mismatch; pure coordination pays 1 on
all three matches; rationalizable coordination pays 1/2/3.

Derived once per variant and shipped in the observation:
`bestResponseRow[j] = argmaxᵢ rowPay[i][j]` and `bestResponseCol[i] = argmaxⱼ colPay[i][j]`
(ties → lowest index).

### The decision a seat actually makes: one **intent** per beat

A beat is 50 ticks. At each beat boundary every seat submits one **intent**, which a deterministic
per-tick kernel then executes for the next 50 ticks. This is the batched-swarm cadence hive and
ecos proved: 96 LLM calls per episode instead of 4 800, and every cog still runs a per-tick
move/turn/interact policy exactly as the idea's "policy interface" line asks.

| intent | required argument | what the kernel does for 50 ticks |
|---|---|---|
| `gather` | `token` | path to the **nearest** cell holding a token of that type (Chebyshev distance from the seat's own observation; ties → lowest `y`, then lowest `x`); when that type is at `tokenCap`, path to the type's zone centre and hold. Never fires the beam. |
| `deny` | `token` | path to the cell holding a token of that type that is **nearest to the nearest other cog** (ties → lowest `y`, then `x`); collect it. Never fires the beam. |
| `hunt` | `target` (an alias) | path toward that cog's last known cell; fire the beam the first tick the target is in the ray and the beam is ready. |
| `avoid` | `target` (an alias) | step to the adjacent free cell that maximises Chebyshev distance from that cog (ties → direction order N, E, S, W); never enter a cell within 2 of it; never fires. |
| `hold` | — | does not step; re-faces toward the nearest other cog within 6 cells every 4 ticks; fires when a cog is in the ray and the beam is ready. |

Pathing is a breadth-first search over free cells from the cog's cell, ties broken by the direction
order N, E, S, W — deterministic, no floats, no randomness. A cog that has no legal step waits.

The intent in force during beat 0 comes from the **opening batch**, issued before tick 0
(`## Decisions`); if that batch fails for a seat, beat 0 runs that seat's scripted fallback intent.

### Tick resolution order (exact, numbered)

Every tick runs these ten steps in this order. Within a step, all reads use the state as it stood at
the **start of that step**, so ordering inside a step never changes the outcome; where a step must
write in sequence, it iterates seats in ascending slot order and that is stated.

1. **Timers.** For every cog: `freeze = max(freeze - 1, 0)`, `stepCd = max(stepCd - 1, 0)`,
   `beamCd = max(beamCd - 1, 0)`, `immune = max(immune - 1, 0)`.
2. **Token respawn.** Every spawner whose `refillAt == t` gets its token back.
3. **Intent evaluation.** For each cog with `freeze == 0`, evaluate its intent against the state at
   the start of this step and produce one desired micro-action: `step(dir)`, `turn(dir)`, `fire`, or
   `wait`. Frozen cogs produce `wait`.
4. **Movement**, seats in ascending slot order. A cog with `stepCd == 0` whose micro-action is
   `step(dir)` moves one cell if that cell is floor and **currently unoccupied** (re-checked as of
   this step's writes — a cog whose target cell was taken by a lower slot waits); its facing becomes
   `dir` and `stepCd = stepCooldownTicks = 3`. `turn(dir)` sets facing without a cooldown.
5. **Pickup**, seats in ascending slot order. A cog standing on a spawner that holds a token of type
   `i` with `inv[i] < tokenCap` takes it: `inv[i] += 1`, the spawner empties,
   `refillAt = t + tokenRespawnTicks`. Emits `pickup`.
6. **Beam fire**, seats in ascending slot order. A cog whose micro-action is `fire` and whose
   `beamCd == 0` and `freeze == 0` casts a ray from its cell along its facing for up to
   `beamRange = 4` cells. The ray stops at the first wall. The **first cog** in the ray is the
   target. Emits `beam` (with `hitSeat = -1` when the ray hits nothing). Then:
   - no target → `beamCd = beamMissCooldown = 6`, nothing else happens;
   - target has `immune > 0` or `freeze > 0` → **no contest**, `beamCd = beamMissCooldown`;
   - variant is `bach-or-stravinsky` **and** shooter and target are in the same camp → emits
     `nocontest`, `beamCd = beamMissCooldown`, nothing else happens (the idea's "interactions only
     cross-camp");
   - otherwise → **resolve** (step 7).
7. **Resolution.** Let the **row player** be the shooter in every symmetric variant, and in
   `bach-or-stravinsky` the **row-camp (blue) participant** regardless of who fired. Let the row
   player's inventory be `n` with `N = Σ nᵢ`, and the column player's be `m` with `M = Σ mⱼ`.
   ```
   rowPayCp = ( Σᵢ Σⱼ  nᵢ * rowPay[i][j] * mⱼ * 100 ) div (N * M)
   colPayCp = ( Σᵢ Σⱼ  nᵢ * colPay[i][j] * mⱼ * 100 ) div (N * M)
   ```
   `div` is Nim's integer division, **truncating toward zero** — stated because RWS has negative
   entries and truncation direction must be pinned for determinism. Payoffs are in **centipoints**.
   Both participants' `scoreCp` gain their payoff. The **cell hit** — what the viewer pops — is
   `(argmaxᵢ n, argmaxⱼ m)`, ties → lowest index. Emits `interact`.
8. **Reset.** Both participants have their inventories reset to the endowment (1 of each type),
   `freeze = freezeTicks = 12`, `immune = 12`, `beamCd = beamResetCooldown = 25`. Emits `reset`
   for each. This is the idea's "(in some variants) resets both", applied uniformly to every
   variant: it is what makes commitment cost time, what makes token denial pay, and what stops a
   single hoarder farming a frozen neighbour.
9. **Indices.** Update the running convention histogram, the cooperation accumulator and each
   seat's exploitability accumulators (definitions below). Detect a change of leader
   (`argmax scoreCp`, ties → lowest slot) and emit `leadchange` when it differs from last tick.
10. **Record.** Append this tick's state frame, its events, and the two series rows to the replay
    (`## Sim module`).

At a beat boundary (every 50 ticks) the sim additionally closes the beat, checks the end conditions
and — if the episode continues — blocks for the next batched decision (`## Decisions`).

### Scoring — total payoff, higher is better

- `scoreCp[i]` = the sum, in centipoints, of every payoff seat `i` collected at step 7.
- **`results.scores[i] = scoreCp[i] / 100.0`.** **Sign: higher is better.** In
  `running-with-scissors` the scores are zero-sum and negative scores are normal and expected; in
  every other variant they are non-negative. Typical magnitudes: 5 resolutions per cog × the
  variant's payoff range, so roughly −12…+12 (RWS), 0…20 (PD), 0…16 (chicken), 0…18 (stag hunt),
  0…12 (BoS), 0…4 (pure coordination), 0…12 (rationalizable coordination).
- `results.win[i] = (scores[i] == max(scores))`.
- **The league ranks by `results.scores`, higher better.** Because `win[]` and the platform's Elo
  are *rank* comparisons within one episode, the fact that `pure-coordination` pays smaller absolute
  numbers than `prisoners-dilemma` does not bias the ladder — that difference is the idea's own
  pinned payoff numbers and is kept verbatim.
- A seat that never resolves an interaction scores **0**. There is no participation bonus and no
  penalty for hiding; in a zero-sum room, hiding is a legitimate 0.

**Per-room indices** (the idea's replay plan), computed by the sim, carried in the replay and shown
in the viewer:

1. **Convention histogram** — `conventionCounts[i][j]` = how many resolutions hit cell `(i, j)`
   (the argmax pair from step 7). Drawn as the K×K matrix panel's heat.
2. **Cooperation rate** — for variants that declare a `coopToken` (PD, chicken, stag hunt):
   the fraction of all inventory mass carried into resolutions that was the coop token, i.e.
   `Σ over resolutions (n[coop] + m[coop]) / Σ over resolutions (N + M)`, reported as a float in
   `[0, 1]`. Variants with no `coopToken` report **`null`**.
3. **Exploitability**, per seat, in points: let `avgOpp` be the mean opponent mix over all of seat
   `i`'s resolutions and `realised` its mean payoff per resolution. Then
   `exploitability[i] = bestPureValue(avgOpp) − realised`, where `bestPureValue` is the value of the
   best pure strategy against `avgOpp` under the matrix that seat faced (row or column side).
   Higher = more money was left on the table. Seats with zero resolutions report `null`.

### End conditions and `results.reason`

The episode ends at the FIRST of:

| condition | `results.reason` | `results.ending` | scores |
|---|---|---|---|
| 12 beats (600 ticks) played | `complete` | `full_match` | as computed |
| wall clock passes the play deadline (`0.6 × episodeTimeoutSeconds` = **720 s**), checked **between beats only** | `deadline` | `deadline` | beats played are scored; nothing is imputed for the rest |
| no seat socket connected within `playerConnectTimeoutSeconds = 180` | `forfeit` | `forfeit` | all zero; `results.json` and the replay are still written |

Those three — **`complete`, `deadline`, `forfeit`** — are the only legal `results.reason` values.
There is no early-termination rule: a room where nobody ever fires plays all 12 beats and everyone
scores 0, which is a completed game of Matrix Games, not an error. `deadline` is declared acceptable
(it means the LLM was slow, not that the game broke), but the arithmetic in `## Decisions` is sized
so it should not fire.

---

## Decisions: LLM with scripted fallback

Both policies ship in the **same image** from day one, env-switched, exactly like bullwhip:
`PLAYER_PROMPT="<strategy text>"` for an LLM policy,
`PLAYER_SCRIPTED=counter|tit-for-tat|fixed-pick|always-first|always-second` for a scripted baseline.
**A policy is a prompt**: `src/matrix_games_player.nim` (a fork of
`cogame-bullwhip/src/bullwhip_player.nim`) is one thin process that connects, sends
`{"type":"prompt","prompt":…,"scripted":…}` and then only listens. All decision-making happens in
the **game** container (`src/matrix_games/llm.nim`, forked from `cogame-bullwhip/src/bullwhip/llm.nim`),
which is what makes one parallel batch per beat possible and why the coworld secret must be declared
on the game runnable (hive learning, 2026-08-23).

### Cadence and the wall-clock budget

One **turn = one beat**. At each beat boundary the game issues **all eight seats' requests as ONE
parallel batch** (`curly.makeRequests`, bullwhip's `decideAll`) — never sequentially. Said out loud:

```
per episode:     12 beats x 8 seats            =  96 LLM requests
inter-batch floor: minBeatSeconds = 17 s        ->  8 req / 17 s = 28.2 req/min  <  30 (sidecar cap)
per beat worst:  llmTimeoutSeconds 20 (batch) + 20 (retry batch)          =  40 s
episode worst:   12 x 40                                                 = 480 s  <  720 s  (= 0.6 x 1200)
episode typical: 12 x max(17, ~6 s batch)                                = 204 s
simulation cost: 600 ticks x ~0.4 ms                                     =  ~0.3 s  (negligible)
```

The 17 s floor is not padding: it is the sidecar's **30 requests/minute per episode** ceiling that
bit cogame-raid, and with 8 seats per batch it is the binding constraint. The play deadline
(`0.6 × episodeTimeoutSeconds`; the game container is **not** given `COWORLD_TIMEOUT_SECONDS`, so
1200 is assumed unless the env supplies it) is tested **between beats**; crossing it calls
`endEarly()` and settles with `reason: "deadline"`.

### The observation each seat gets

Sent as the `state` frame at every beat boundary and rendered into the user prompt. Every number
below is visible to that seat; **nothing else is.**

```json
{"type":"state","protocol":"matrix.player.v1","slot":4,"name":"Elm","camp":"column",
 "variant":"prisoners-dilemma","beat":5,"beats":12,"ticksPerBeat":50,"tick":250,
 "board":{"w":24,"h":14,"walls":["########################","#....##..........##....#", "…14 rows…"]},
 "rules":{"K":2,"tokens":["cooperate","defect"],
          "rowPay":[[3,0],[5,1]],"colPay":[[3,5],[0,1]],
          "bestResponseRow":[1,1],"bestResponseCol":[1,1],
          "tokenCap":8,"endowment":[1,1],"beamRange":4,"freezeTicks":12,
          "stepCooldownTicks":3,"beamResetCooldown":25,"beamMissCooldown":6,
          "tokenRespawnTicks":45,"crossCampOnly":false},
 "you":{"x":17,"y":4,"facing":1,"inv":[2,6],"mix":[250,750],"scoreCp":940,
        "freeze":0,"beamCd":0,"interactions":4},
 "zones":[{"token":"cooperate","x0":1,"y0":1,"x1":7,"y1":5,"cx":4,"cy":3,"tokensLeft":11},
          {"token":"defect","x0":16,"y0":1,"x1":22,"y1":5,"cx":19,"cy":3,"tokensLeft":6},
          {"token":"mixed","x0":1,"y0":6,"x1":22,"y1":7,"cx":11,"cy":6,"tokensLeft":9}],
 "visibleTokens":[{"x":19,"y":2,"token":"defect"},{"x":20,"y":5,"token":"defect"}],
 "cogs":[{"alias":"Ash","camp":"none","x":6,"y":3,"dist":11,"seenTicksAgo":0,
          "inv":null,"mix":null,"scoreCp":1180,"interactions":5,"frozen":false},
         {"alias":"Fern","camp":"none","x":18,"y":5,"dist":1,"seenTicksAgo":0,
          "inv":[1,7],"mix":[125,875],"scoreCp":620,"interactions":3,"frozen":false}, "…6 more…"],
 "log":[{"beat":4,"tick":214,"row":"Fern","col":"Ash","cell":["defect","cooperate"],
         "rowMix":[125,875],"colMix":[778,222],"rowCp":436,"colCp":97}, "…"],
 "indices":{"interactions":18,"coopRate":0.41,
            "conventionCounts":[[4,5],[6,3]],"yourExploitabilityCp":118},
 "notes":"…your own notes from last beat…"}
```

- **Visible:** the whole map; the full matrix, both best-response tables and every constant; your
  own position, facing, inventory, mix (in permille), score and cooldowns; every zone rectangle,
  centre and **live token count** (public — this is what makes denial legible); the tokens inside
  your view; every other cog's alias, camp, **cumulative score** and interaction count; each other
  cog's **position and inventory when it is within `viewRadius = 7` cells with clear line of sight**
  (Bresenham over the wall grid) — this is the idea's "commitment is visible", and it is what makes
  a feint (buying tokens you do not intend to use) a real move; for cogs out of view, the last known
  cell plus `seenTicksAgo`, with `inv` and `mix` `null`; the **complete public log of every
  resolution in the episode** (both participants, both mixes, both payoffs — the beam is a visible
  event and everyone sees who did what to whom); the room indices; your own notes.
- **Hidden:** every other seat's intent for the coming beat, its `notes`, its `say`, its prompt and
  its policy name; the RNG seed; the positions and inventories of cogs outside your view; anything
  about accounts, players or the league.
- **There is no inter-seat channel.** `say` is spectator-only — written to the replay and drawn in
  the feed, never shown to another seat. That is deliberate: Chicken is "who yields, **with no
  words**", and a silent room is also the anti-collusion property the idea asks for (no codebooks,
  because there is no channel to carry one).

### The reply schema

The model must answer with exactly one JSON object whose first character is `{`:

```json
{"intent":"hunt","target":"Ash","token":"defect",
 "say":"Ash is loaded with cooperate — take him",
 "notes":"Fern defected on me twice; Ash has coop-heavy mixes in beats 2 and 4"}
```

| field | type | cap / domain | on violation |
|---|---|---|---|
| `intent` | string | one of `gather`, `deny`, `hunt`, `avoid`, `hold` | absent or not in the set → **invalid reply** |
| `token` | string | a token name of this variant (case-insensitive; the integer index is also accepted) | required for `gather`/`deny` — absent/unknown → **invalid reply**; ignored for the other three intents |
| `target` | string | an alias of another **eligible** cog (in `bach-or-stravinsky`, cross-camp only); case-insensitive | required for `hunt`/`avoid` — absent/unknown/self/ineligible → **invalid reply**; ignored for the other three |
| `say` | string | **64 characters** | truncated |
| `notes` | string | **400 characters** | truncated |

Extra keys are ignored. Trailing prose after the closing brace is tolerated by the extractor.
**Truncation is on rune boundaries, never bytes** — `cleanText(text, limit)` = `strip` → if
`runeLen > limit`, `runeSubStr(0, limit - 1) & "…"` (bullwhip's `cleanText`; a byte cut once put
invalid UTF-8 into a replay and only a strict parser found it). Newlines in `say` become spaces.
Both fields are recorded in the replay and rendered in the feed.

The legal `token` list and the legal `target` list are **precomputed and shipped in the user
prompt** as explicit enumerations, computed by the same predicate the validator applies — the escrow
fix for formal-output fallback rates.

### Prompts

**System prompt** (composed by the game, per seat, per beat): the seat's alias and camp in capitals;
the full rule set — the beat structure, the five intents and their arguments, the beam (range 4,
line of sight, first cog in the ray), the reset-on-resolution rule, the token cap and endowment; the
variant's payoff matrix printed as a labelled table with both players' payoffs in every cell; the
statement that **your strategy is your inventory mix, not a declaration** — `xᵢ = nᵢ / N` — and the
exact payoff formula; the scoring rule ("your score is the sum of the payoffs you collect; higher is
better; a cog that never interacts scores zero"); the statement that the other seven seats are other
cogs deciding simultaneously and that nothing you write is read by them; and the output contract,
ending:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

(Bedrock/Haiku answers prose-first without that sentence — playbook §Phase 1.)

**User prompt:** the observation rendered as compact text — a `BEAT 5 / 12` header; your own row
(`YOU Elm · at (17,4) facing E · inv cooperate 2 / defect 6 · mix 25% / 75% · score 9.40`); an
eight-row scoreboard (`alias · score · interactions · last seen · inventory-if-visible`); the zone
table with live counts; the visible-token list; the full public resolution log as one line per
resolution (`beat 4 · Fern(defect .88) ▸ Ash(coop .78) → +4.36 / +0.97`); the indices line; then
`YOUR NOTES FROM LAST BEAT`, then the operator block:

> GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
> requested format):
> `<PLAYER_PROMPT>`

then a one-line restatement of the reply shape with **the legal token names and the legal target
aliases enumerated verbatim**.

**Transport:** bullwhip's ladder, haiku-only (the raid learning — the sonnet fallback times out on
every sidecar call and turns one throttle into a cascade):
`bedrockModelIds() = ["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`, `BEDROCK_MODEL` overrides.
`maxOutputTokens = 900` (400 truncates mid-JSON). No `output_config.effort` — Haiku 4.5 400s on it.
Credentials in order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` / `AWS_BEARER_TOKEN_BEDROCK`)
→ `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`. With none, the client disables itself immediately
and every seat plays `counter` — this is what keeps offline certification green and deterministic.

**Champion prompts** (phase 50 uploads these; **both are `PLAYER_PROMPT` policies**, and both policy
entries carry `"USE_BEDROCK": "true"` — without it the platform gives the player pod no Bedrock
sidecar and the seat silently plays scripted, the cogolf trap):

- `matrix-games-reader` (champion #1, daveey): *"Read the room before you commit. Every beat, look
  at the public log first: which cells have actually been hit, and what did each cog carry into its
  last interaction? Your score comes only from resolutions, so you must interact — but a cog that
  hunts with a uniform inventory is donating. Spend one or two beats gathering the token that beats
  what your intended target is visibly holding, then hunt. If the room has settled into a
  convention that pays you, keep matching it and take safe interactions often; if it has settled
  into one that pays you badly, break it — gather the counter and go find the cog that has drifted
  furthest from the convention. When someone is loaded against you and close, avoid them for a beat
  rather than feed them. Keep notes naming each cog and the mix it last showed you."*
- `matrix-games-brinkman` (champion #2, daveey-1): *"Play for the top of the matrix and accept that
  it costs you some encounters. Pick the payoff cell you want, commit hard to its token until you
  are at eight, and hunt only cogs whose visible mix makes that cell land. Deny as a weapon: if the
  cog with the highest score is clearly building one token, go empty the zone that token comes from
  before you hunt anyone. Remember every resolution resets you both to a uniform inventory, so time
  your fights — never fire when you are the one who just got reset. If two beats pass with no
  interaction, drop the ambition and take whatever encounter is closest; zero is the worst score in
  this game."*

### Scripted baselines (five, all fieldable, all declared, two fielded as fillers)

**All five run against the same `buildObservation(slot)` object an LLM seat receives — never raw sim
state.** That is what makes a baseline a legitimate policy, and `tests/test_baseline.nim` asserts
it. Each returns one intent per beat. Shared helpers:

- `eligible()` — every other cog, minus same-camp cogs in `bach-or-stravinsky`.
- `nearestEligible()` — the eligible cog with the smallest Chebyshev distance using its last known
  cell; ties → lowest slot.
- `commit(type)` — if `you.inv[type] < commitTarget = 5` return `{"intent":"gather","token":type}`;
  else if `nearestEligible()` exists return `{"intent":"hunt","target":<that alias>}`; else
  `{"intent":"hold"}`.
- `lastSeen[alias]` — the argmax token of that cog's mix at the most recent resolution in the public
  log involving it (either side); defaults to token **0**.

| baseline | algorithm | Melting Pot bot it reproduces |
|---|---|---|
| `always-first` | `commit(0)` every beat. | always-C / always-dove / always-stag / always-Bach / always-rock |
| `always-second` | `commit(1)` every beat. | always-D / always-hawk / always-hare / always-Stravinsky |
| `fixed-pick` | `myType = (seed + slot) mod K`, drawn once at episode start and never changed; `commit(myType)`. | fixed-pick |
| `tit-for-tat` | `t = nearestEligible()`; `commit(lastSeen[t])` and, when it hunts, hunt `t`. Mirrors whatever that cog last showed. | conditional/mirroring resident |
| `counter` | `t = nearestEligible()`; `j = lastSeen[t]`; play the **best response**: `bestResponseRow[j]` if you are the row side against `t` (always, except in `bach-or-stravinsky` where a column-camp cog uses `bestResponseCol[j]`); `commit(that type)` and hunt `t`. | the strong resident — defects in PD, plays hawk into doves, matches stag with stag, plays the cyclic counter in RWS |

`counter` is the **fallback move** used whenever an LLM seat's decision fails (below) and the
baseline the offline certification fixture leans on, because it is the strongest of the five and
guarantees interactions happen.

### Degrade, never hang

- Batch timeout `llmTimeoutSeconds = 20`. On transport error, non-2xx, refusal, `max_tokens` before
  any `{`, unparseable JSON, an unknown `intent`, a missing/unknown `token` where one is required,
  or a missing/unknown/ineligible `target`, **that seat alone** is retried **once** in the same beat
  with the appended hint: *"Your previous reply was invalid. Respond with ONLY the requested JSON
  object. `intent` must be one of gather, deny, hunt, avoid, hold; `token` must be one of
  `<enumerated>`; `target` must be one of `<enumerated>`."*
- Still failing → that seat plays the **`counter` scripted intent** for that beat, logged as
  `matrix-games llm: seat N falling back to scripted intent` and recorded on the `order` event as
  `"source":"fallback"`. `decideAll` never raises; the episode always advances.
- 401/403 disables the client for the rest of the episode (every seat scripted from then on);
  429 is logged and that seat is retried in the next beat's batch.
- A seat whose socket never connected, or which disconnects mid-episode, plays `counter` for every
  remaining beat. The episode never waits on it.
- The episode **settles early rather than overrunning**: the play deadline is checked between beats,
  `endEarly()` scores what was played, artifacts are written, and — as cogame-lantern taught —
  `/healthz` and `/global` keep answering for `shutdownGraceSeconds = 20` before `quit(0)`, because
  hosted certification pings the global websocket **after** the player pods start.

---

## Sim module

New code lives in `src/matrix_games/`, mirroring paintbot's split (`src/ctf/`). Nim module names
cannot carry a hyphen, so the module tree is `matrix_games` while the binaries are
`/bin/matrix-games` and `/bin/matrix-games-player`. What is forked, what is kept, what is deleted:

| paintbot path | matrix-games | note |
|---|---|---|
| `src/ctf/sim_types.nim` | `src/matrix_games/sim_types.nim` | fork: `GameVersion`, the flatty wire types, `Cog`, `Spawner`, `Zone`, the constants above. Field order is sacred, same as paintbot. |
| `src/ctf/sim.nim` | `src/matrix_games/sim.nim` | fork: the tick loop and the 10 numbered rules replace the CTF gameplay core. |
| `src/ctf/sim_config.nim` | `src/matrix_games/sim_config.nim` | fork: `GameConfig` lifecycle + `config.update`; fields = the config schema in `## Packaging`. |
| `src/ctf/sim_state.nim` | `src/matrix_games/sim_state.nim` | fork: logging, `gameHash`, event emission, seeded spawner and opening-pad placement. |
| `src/ctf/global.nim` | `src/matrix_games/global.nim` | fork, heavily reduced: keep the sprite-protocol emitter, layer/object pooling, map bands, the chrome `TextMessage` smuggling and `boardRenderScaleFor`. **Delete** fog-of-war/FOV, first-person PiP, articulated rigs beyond the standing cog, grenade/spray/shield/barrier families, endzone bakes, perks and handicaps. |
| `src/ctf/broadcast.nim` | `src/matrix_games/broadcast.nim` | fork: `BroadcastTracker` + `buildStateJson` keep their shape and key names; `teams` becomes the K token-type keys, `seats` is added, `lead` becomes the convention-share series. |
| `src/ctf/events.nim` | `src/matrix_games/events.nim` | fork: the event vocabulary below. |
| `src/ctf/replays.nim`, `src/ctf/replay_runtime.nim` | `src/matrix_games/replays.nim` | rewritten: matrix-games records **state frames**, not inputs (below). |
| `src/ctf/server.nim` | `src/matrix_games/server.nim` | fork of the route/artifact/shutdown skeleton; the player protocol is bullwhip's JSON frames. |
| `src/ctf/map_art.nim` | `src/matrix_games/map_art.nim` | fork, reduced to one baked yard floor plus the shipped `client/art/walls/{wall_h,wall_v}.jpg` tiles. |
| `src/ctf.nim` | `src/matrix_games.nim` | fork of the entrypoint: seed randomisation **before** `config.update`, same sentinel handling. |
| `src/ctf/arena.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `labels.nim`, `roster.nim` | — | deleted. One fixed hand-authored map, no generator, no perk roster, no label pipeline. |
| `tools/*probe*.nim`, `caos*/`, `arena/` wit bindings, `client/league_replayer.html` | — | deleted. **Keep** `tools/build_replay_viewer.sh` (with the ecos `mkdir -p` fix and the image tag/`docker cp` path renamed) and `tools/gen_wire_constants.nim`. |

New files: `src/matrix_games/matrices.nim` (the seven matrices, token names, `coopToken`, the two
best-response tables, all as compile-time constants), `src/matrix_games/arena_map.nim` (the ASCII
map), `src/matrix_games/kernel.nim` (the five intents' per-tick micro-action kernel + the BFS),
`src/matrix_games/scripted.nim` (the five baselines), `src/matrix_games/indices.nim` (convention
histogram, cooperation rate, exploitability), `src/matrix_games/llm.nim` (from
`cogame-bullwhip/src/bullwhip/llm.nim`), `src/matrix_games_player.nim` (from
`cogame-bullwhip/src/bullwhip_player.nim`).

### Event vocabulary (the replay's `events[]`)

One JSON row per event, `t` = tick. Seats are slot integers; token types are integer indices.

| `k` | fields | when |
|---|---|---|
| `order` | `t, beat, seat, intent, token (or -1), target (or -1), source ("llm"\|"retry"\|"fallback"\|"scripted"), say, notes, latencyMs` | one per seat per beat boundary |
| `pickup` | `t, seat, x, y, token` | rule 5 |
| `beam` | `t, seat, x, y, dir, len, hitSeat` (`-1` = hit nothing) | rule 6 |
| `nocontest` | `t, seat, target, why ("same_camp"\|"immune")` | rule 6 |
| `interact` | `t, beat, row, col, rowInv[K], colInv[K], rowMix[K], colMix[K], cellRow, cellCol, rowCp, colCp` | rule 7 |
| `reset` | `t, seat` | rule 8, one per participant |
| `leadchange` | `t, seat, scoreCp` | rule 9 |
| `beatclose` | `t, beat, scoreCp[8], interactions` | at each beat close |
| `end` | `t, reason, ending, scoreCp[8]` | terminal |

`notes` is recorded (it is what makes an LLM seat's reasoning auditable in the replay) but is drawn
only in the feed's expanded row; `say` is the headline. Both are already rune-truncated.

### The replay file (`matrix.replay.v1`)

**Strict UTF-8 JSON, one document.** Matrix Games records *state*, not inputs, so playback never
re-simulates, a seek is an array index, and there is no native/wasm divergence to chase (hence no
`mismatch_tick` mode).

```json
{"protocol":"matrix.replay.v1","game":"matrix-games","gameVersion":"1",
 "variant":"prisoners-dilemma","seed":1234567,
 "names":["Ash","Birch","Cedar","Dune","Elm","Fern","Gorse","Holly"],
 "policyNames":["matrix-games-reader","matrix-games-counter","…8 total…"],
 "liveries":["cobalt","sky","moss","lime","rust","ember","brass","plum"],
 "camps":["none","none","none","none","none","none","none","none"],
 "config":{"matrix":"prisoners-dilemma","K":2,"tokens":["cooperate","defect"],
           "rowPay":[[3,0],[5,1]],"colPay":[[3,5],[0,1]],"coopToken":0,
           "beats":12,"ticksPerBeat":50,"tokenCap":8,"endowment":[1,1],
           "beamRange":4,"freezeTicks":12,"stepCooldownTicks":3,
           "beamResetCooldown":25,"beamMissCooldown":6,"tokenRespawnTicks":45,
           "viewRadius":7,"crossCampOnly":false,"fps":24},
 "map":{"w":24,"h":14,"walls":["########################","…14 rows…"]},
 "spawners":[{"x":3,"y":2,"token":0}, "…44 or 60…"],
 "frames":[{"t":0,
            "c":[2,2,2,0, 21,2,2,0, "…8 x (x,y,facing,freeze)…"],
            "inv":[1,1, 1,1, "…8 x K…"],
            "tok":[1,0, 0,1, "…one 0/1 per spawner, in spawners[] order…"],
            "sc":[0,0,0,0,0,0,0,0]}, "…600 frames…"],
 "series":{"share":[[0,500,500], "…one row per tick…"],
           "score":[[0,0,0,0,0,0,0,0,0], "…one row per tick: [t, sc0..sc7]…"]},
 "indices":{"conventionCounts":[[4,5],[6,3]],"coopRate":0.41,
            "exploitabilityCp":[118,0,240,null,"…8…"]},
 "events":[ "…" ],
 "results":{ "… the results.json object verbatim …" }}
```

- `frames[i].c` is a flat integer quad per seat `(x, y, facing, freeze)`; `inv` is a flat `8 × K`
  integer block; `tok` is one 0/1 per spawner in `spawners[]` order; `sc` is each seat's cumulative
  centipoints. No ids and no floats.
- `series.share[t] = [t, permilleOfType0, permilleOfType1, (permilleOfType2)]` — the share of all
  cogs' inventory mass carried in each token type at tick `t`. This is the convention histogram as a
  time series and it drives the momentum strip.
- **Replay bytes are self-sufficient (pin).** Names, policy names, liveries, camps, the variant, the
  whole config including the matrix, the seed, the map, the spawner layout, per-tick state, the
  index summary, every event and the full `results` object are all in the file. No server is
  contacted except S3 for the `.replay` file.
- Size arithmetic: 600 frames × (32 + 16..24 + 44..60 + 8 ≈ 124 integers × ~4 chars) ≈ **0.35 MB**,
  plus ~400 events ≈ 0.1 MB. `tests/test_replay.nim` asserts `< 8 MiB`.

### Feasibility — the game has to be the game it claims

Three properties are asserted in CI (`tests/test_indices.nim`), not assumed, because a matrix game
whose matrix never gets exercised is a dead replay:

- **(a) Encounters happen.** An all-scripted episode (the cert seat mix) on each of the seven
  variants, seeds 1..8, produces **≥ 12 resolutions** and **every seat resolves at least once**.
  The arithmetic behind that expectation: a cog can resolve at most once per
  `freezeTicks + beamResetCooldown = 37` ticks, so 600 ticks bounds each cog at 16 and the room at
  64; `counter`/`tit-for-tat` reach `commitTarget = 5` in roughly one and a half beats (50 ticks ≈
  16 steps at one step per 3 ticks, through a zone with 16 spawners) and hunt for the rest, which
  puts the realistic room total at 15–30.
- **(b) The matrix bites.** In `prisoners-dilemma`, a room of seven `always-first` plus one
  `always-second` gives the `always-second` seat the top score. In `stag-hunt`, an all-`always-first`
  room's mean score strictly exceeds an all-`always-second` room's. In `running-with-scissors`,
  `counter` outscores `fixed-pick` over seeds 1..8. In `chicken`, one `always-second` in a room of
  `always-first` tops the table, and an all-`always-second` room's mean is the lowest of the five
  scripted rooms. In `bach-or-stravinsky`, zero same-camp resolutions occur and both camps' mean
  scores are positive.
- **(c) Every cell is reachable.** Across seeds 1..8 per variant, every one of the K×K cells of
  `conventionCounts` is hit at least once by *some* room in the scripted sweep — otherwise the
  matrix panel would have dead squares.

---

## Server, player, protocol

### Game container (`/bin/matrix-games`)

Routes, kept from paintbot's `src/ctf/server.nim` because hosted certification probes exactly these
**before** the player pods start (the lantern learning):

| route | behaviour |
|---|---|
| `GET /healthz` | `200 ok`, from process start until `shutdownGraceSeconds` after the artifacts are written |
| `GET /client/player?slot=N&token=T` | the seat's HTML shell (paintbot's, trimmed). Never opens the player websocket. |
| `WS /player?slot=N&token=T` | the seat socket; a bad token is refused with a close frame, never a hang |
| `GET /client/global` | the broadcast client (`client/replay_broadcast.html`, embedded with `staticRead`) |
| `WS /global` | live spectator: paintbot's sprite protocol + the chrome `TextMessage` |

Both `/client/` routes are registered **before** any catch-all asset route.

`matrix.player.v1` frames, JSON text, bullwhip shapes:

- game → player: `{"type":"welcome","protocol":"matrix.player.v1","slot":N,"name":"Elm","camp":"column","variant":"prisoners-dilemma","beats":12,"ticksPerBeat":50}` on connect;
  the `state` frame of `## Decisions` at every beat boundary and once at episode end;
  `{"type":"final","done":true,"slot":N,"scores":[…8 floats…],"names":[…8 aliases…],"beats":B,"reason":…,"ending":…}`,
  after which the player exits 0.
- player → game: `{"type":"prompt","prompt":"<= 4000 chars","scripted":"counter|tit-for-tat|fixed-pick|always-first|always-second|"}`,
  sent immediately on connect and again after `welcome` (the re-send guards the slot-registration
  race). Any other frame is ignored with a log line.

Startup: `src/matrix_games.nim` randomises the seed **before** `config.update` (paintbot's rule —
every seed-derived draw, here the spawner layout and `fixed-pick`'s type, must follow the final
seed), waits up to `playerConnectTimeoutSeconds = 180` for eight sockets, starts anyway with
whoever is there (missing seats play `counter`), then runs the beat loop.

Shutdown, in this order (bullwhip's `finishEpisode` plus lantern's grace): send `final` to every
player socket → broadcast the last global frame → `sleep 500 ms` → write `results.json`
(`COGAME_RESULTS_METHOD`, `application/json`) → write the replay (`COGAME_SAVE_REPLAY_METHOD`,
`application/json`) → keep `/healthz` and `/global` answering for `shutdownGraceSeconds = 20` →
`quit(0)`. The player's receive loop wraps `receiveMessage` in `try/except CatchableError` and exits
**0** on a closed or truncated frame (the raid learning — otherwise `docker_smoke` passes and
certification fails intermittently).

### `results.json`

```json
{"names":["matrix-games-reader","matrix-games-counter","…8 policy names…"],
 "scores":[9.40,11.82,-2.10,0.00,6.55,4.31,7.02,1.98],
 "win":[false,true,false,false,false,false,false,false],
 "aliases":["Ash","Birch","Cedar","Dune","Elm","Fern","Gorse","Holly"],
 "camps":["none","none","none","none","none","none","none","none"],
 "variant":"prisoners-dilemma",
 "interactions":19,
 "perSeatInteractions":[5,6,4,0,5,4,6,3],
 "meanPayoff":[1.88,1.97,-0.53,0.0,1.31,1.08,1.17,0.66],
 "exploitability":[1.18,0.0,2.40,null,0.94,1.51,0.77,2.02],
 "coopRate":0.41,
 "conventionCounts":[[4,5],[6,4]],
 "tokens":["cooperate","defect"],
 "beats":12,"ticks":600,
 "reason":"complete","ending":"full_match"}
```

`names` are **policy** names (platform side); aliases go to the players and into the replay's
`names[]`. Every array is indexed by slot and always length 8. `scores[i] = scoreCp[i] / 100`
(higher better); `meanPayoff[i]` = `scores[i] / perSeatInteractions[i]` or `0.0` when that seat
never resolved; `exploitability[i]` is the points left on the table (`null` for a seat with no
resolutions); `coopRate` is `null` for variants with no `coopToken`. The results schema declares
`["number","null"]` for `exploitability[]` items and for `coopRate`.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is
coworld-ctf's script, kept, with three edits: `image_tag` renamed, the `docker cp` source path
changed to `/workspace/matrix_games/replay-viewer/dist/.`, and the ecos `mkdir -p "$output_parent"`
fix applied **before** the containment check (paintbot's hook exits 1 on a fresh CI checkout
without it). It stays committed **executable** — `coworld build` hard-requires `os.X_OK`.

### One starter supplies all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and from no other starter.** Named
explicitly, because splicing two starters' halves is what left cogame-lantern with a permanently
blank theater:

| file | source (coworld-ctf) | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | verbatim except the emitted name (`matrix_games_replay.js`) and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_mg_*`. **Keep the link flags exactly as they are — no `-s MODULARIZE=1`, no `EXPORT_NAME`** — because the worker below bootstraps with `Module.onRuntimeInitialized`. Keep `-s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8`, `-d:useMalloc` and `--preload-file <root>/data@data`. |
| the wasm entry `.nim` | `replay-viewer/ctf_replay.nim` → `replay-viewer/matrix_games_replay.nim` | same structure and the same safety furniture: the `stageNote` buffer + `stampStage` calls, the `ABORTING_MALLOC` rationale, and the `emscripten_exit_with_live_runtime()` epilogue (without it Nim's `main` destroys every global while JS keeps calling in). Exports `mg_load_replay`, `mg_frame`, `mg_input`, `mg_packet_ptr`, `mg_packet_len`, `mg_error_ptr`, `mg_error_len`, `mg_stage_ptr`, `mg_stage_len`. `ctf_mismatch_tick` is **dropped** — there is no re-simulation to mismatch. The board is 24 × 14 cells, far under `WasmViewerBudgetBytes`, so the capacity check is kept but never trips. |
| `static_replay*.js` | `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js` | verbatim apart from the `ctf_*` → `mg_*` export names and the worker name string (`matrix-games-static-replay`), plus **one added line** in `showFailure`. The worker keeps `importScripts('./wire_constants.js','./broadcast_core.js','./matrix_games_replay.js')` and the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` bootstrap — the matched pair for the link flags above. |
| `index.html` | `client/replay_broadcast.html`, spliced by `Dockerfile.replay-viewer`'s `sed` into `replay-viewer/dist/index.html` | chrome kept verbatim, game block appended (below). |

`static_replay.js` already sets `document.documentElement.setAttribute('data-replay-loaded','true')`
when the worker reports its **first drawn frame** (line 144 of the starter's file) — that line is
kept unchanged. The one addition is in `showFailure()`:
`document.documentElement.setAttribute('data-replay-error', error.message || String(error))`, set
before the `#status` line renders, **so the shell sets `data-replay-loaded="true"` on its first
drawn frame and `data-replay-error` on failure.** Those two attributes are what
`tools/ci/viewer_smoke.mjs` and phase 60's `viewer-check.yml` read. The `coworld-replay` bridge's
`ready` post is moved into the callback that fires **after** `data-replay-loaded="true"` is set
(the chorus fix — posting `ready` on rAF timing lets softmax.com sample an unpainted shell).

### Chrome provenance: copied, appended, removed

- **`client/chrome_common.js` is copied byte-for-byte from `coworld-ctf`. Zero edits.** Its
  CTF-specific paths (perks, handicaps, lives, flag story, POV) stay in the file and are inert
  because the corresponding state fields are simply absent from this stream. The state JSON **keeps
  ctf's key names** — `t, mt, ph, pl, sp, mx, st, lp, sk, ff, en, mm, bs, teams, roster, events,
  lead, beats, lulls, over, hold` — so chrome_common's clock, transport, scrubber, beat markers,
  lull spans, momentum curve, spoilers gate and endcard machinery run **unmodified**.
  `teams` carries the **K token-type keys** (`red`, `blue`, and `green` when K = 3 — names
  chrome_common's `TEAM_ORDER`/`teamCol` already knows, so the momentum legend gets its colours
  free), each holding `{share, tokensLeft, cells}`. The eight seats ride in a separate `seats[]`
  array read only by the appended game block, which is why the 8-seat count never collides with
  chrome_common's 2–4 team assumption.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one
  `<style>` and one `<script>` at the end of the file, injecting matrix-games readouts into the
  existing containers. Nothing above them is rewritten: the CSS variables, `relayout()`
  (`replay_broadcast.html:4110`), the transport, the endcard, the locker-room loader and the
  `?embed=1` mode are the starter's. This is **not** a from-scratch page that reuses the starter's
  ids (the gridlock failure).
- Every function the game block defines at top level is prefixed **`mg`** (`mgBuildPlates`,
  `mgPopCell`, `mgPushRow`, `mgRenderIndices`, `mgMarkBeat`). This is deliberate: a game-block
  `function markBeat` gets hoisted over the chrome alias block's `var markBeat = C.markBeat` and the
  scrubber silently renders unlabeled, unclickable divs (the tandem bug). `tests/test_viewer.nim`
  asserts no game-block top-level name appears in the chrome alias list.
- **Removed starter elements (exactly these):** `#viewpanel` and its children `#minimap`,
  `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`; `#fpv` and
  its children `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`; `#povBadge`; and `#mmwarn`.
  **Zoom decision: the arena is fixed at 24 × 14 cells (960 × 560 px) and always fits the frame, so
  `#viewpanel` — the zoom bar and minimap — is dropped entirely**, per the rule that it exists only
  for boards larger than the frame. `broadcast_core.js`'s zoom/pan/minimap code stays in the file,
  verbatim, simply never driven. `#mmwarn` goes because there is no re-simulation and therefore no
  hash mismatch.
- **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (re-captioned
  "Counting out the tokens…", art from `client/art/lockerroom/{bg.jpg,blue_1,red_1,green_1,yellow_1}`),
  `#chrome`, `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`/`#ffwd-mini`,
  `#bannerlane`, `#killfeed`, `#transport` with every button, `#ffwd-chip`, `#win-chip`,
  `#tick-clock`, `#speedchips`, `#scrub`, `#momentum`, `#lulls`, `#scrub-fill`, `#scrub-win`,
  `#scrub-head`, `#endcard` with its `ec-*` children, `#status`.
- **Added by the game block, all inside `#chrome`, none in the transport band:** `#mg-matrix` (the
  K×K payoff panel, `top: calc(var(--topband) + 8 * var(--u))`, left edge), `#mg-indices` (the
  one-line index readout directly under the scorebug band) and `#mg-legend` (the token colour key,
  right edge, same top offset).

### Transport rules

- `relayout()` is kept **verbatim**: it sets `--hudscale`, `--topband` and **`--band`** on `:root`
  by fixed-point iteration, so the board is letterboxed between the scorebug band and the transport
  band, and every chrome measure derives from `--u: calc(1px * var(--hudscale))`.
- **No overlay sits in the transport band.** `#mg-matrix`, `#mg-indices`, `#mg-legend` and every
  banner the game block raises are positioned inside `#chrome` with
  `bottom: calc(var(--band) + N * var(--u))` or a `--topband`-relative `top`, never over the band.
- The **endcard stops at `var(--band)`** — the starter's `#endcard { top: var(--topband); bottom:
  var(--band) }` rule (`replay_broadcast.html:1036-1048`) is kept unchanged — and is **dismissed by
  every seek**, which is the starter's behaviour, kept.
- **Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">` elements.** The
  game block upgrades chrome_common's markers to buttons with `aria-label` and `title`
  (e.g. "Interaction — Fern zaps Ash, 8.9 s, +4.36 / +0.97") and a click seeks to that tick.
  **CSS exists for every kind emitted**: `.beat-marker.interact`, `.beat-marker.bigpay`,
  `.beat-marker.leadchange`, `.beat-marker.over` — one rule per kind, asserted by
  `tests/test_viewer.nim`. The `beats` timeline is shipped whole on the first HUD frame as
  `beats = [{"t": …, "k": "interact"|"bigpay"|"leadchange"|"over", "seat": …, "other": …, "cp": …}, …]`:
  one `interact` row per resolution, one `bigpay` row (instead of `interact`) when either side's
  payoff is ≥ 400 cp, one `leadchange` row per `leadchange` event, and one `over` row at the final
  tick. Those four are the only kinds emitted, which is what makes "a CSS rule per kind" a closed
  assertion. `lulls` spans are emitted for every stretch of ≥ 60 ticks with no `interact`, so the
  starter's auto-skip button has something real to skip.

### What it draws

1. **Board.** A baked yard floor (stained concrete with faded court lines) under the shipped wall
   tiles; token spawners drawn as small coloured gems with the variant's glyph; eight cogs in their
   liveries, facing shown by the sprite's heading, interpolated between ticks at 24 fps.
2. **Inventory bars over cogs** — the idea's headline readout: K slim bars floating above each cog's
   head, one per token type in its chrome colour, width ∝ `inv[i] / tokenCap`. Drawn Nim-side as
   sprite objects on paintbot's existing FX layer, so they are identical live and in replay and cost
   no extra replay bytes. This is what makes "commitment is visible" visible.
3. **The beam** — a 4-cell coloured lance in the shooter's livery for 4 ticks. A miss fizzles; a
   no-contest (same camp) shows a grey cross.
4. **`#mg-matrix` — the encounter panel that pops the cell hit.** A K×K grid labelled with the
   variant's token names on both axes; each cell shows its `(rowPay, colPay)` pair and carries a
   heat tint from `conventionCounts`. On an `interact` event the cell that was hit flashes white for
   12 ticks and prints the two realised payoffs (`+4.36 / +0.97`) beneath it. The panel is the
   convention histogram and the encounter readout in one object.
5. **Scorebug** (`#scorebug`): **eight slim plates**, slots 0–3 in `#plates-l` and 4–7 in
   `#plates-r`, built by `mgBuildPlates` from `seats[]`. Each plate is a livery chip, the **policy
   name**, the score to two decimals, and an interaction count. In `bach-or-stravinsky` the plates
   carry a camp mark (▲ row/blue, ● column/orange).
6. **Clock** (`#clock-time`, `#clock-caption`): `BEAT 4 / 12` with the caption `tick 214 of 600` —
   spelled out, never `B4`.
7. **`#mg-indices`**: `ENCOUNTERS 19 · COOP 41% · TOP CELL defect/cooperate ×6` — with `COOP —` for
   variants that declare no `coopToken`.
8. **Feed** (`#killfeed`): plain language, one row per event that matters —
   `FERN ▸ ASH — defect 0.88 vs cooperate 0.78 → +4.36 / +0.97`,
   `ASH: gather cooperate  "building for a stag with Birch"`,
   `RESET — Fern and Ash back to 1 / 1`,
   `GORSE picks up defect (zone 2: 4 left)`. Rows whose `order.source` is `fallback` are tagged
   `auto`, so a spectator can see when a seat's LLM missed.
9. **Momentum strip** (`#momentum`, label re-lettered `CONVENTION`): chrome_common's
   `ingestLeadSeries`/`renderMomentum` fed by `lead = {"teams":["red","blue"(,"green")],
   "pts":[[t, share0, share1(, share2)], …]}` from `series.share`, shipped whole on frame 1 so the
   curve draws its full width immediately (paintbot's `lead` trick). Watching the defect share climb
   in PD, or the three RWS shares cycle, is the room's story in one picture.
10. **Bannerlane** (`#bannerlane`): a chip for a resolution worth ≥ 4 points to either side
    (`BIG PAY — FERN +4.36`) and for each lead change.
11. **Transport**: paintbot's play/pause, step-back, +5 s, jump-to-end, loop, skip-lulls, spoilers,
    speed chips, scrubber with beat markers, tick readout and end-hold countdown — all verbatim.
12. **Endcard**: `MATRIX-GAMES-COUNTER TAKES THE YARD` / `PRISONER'S DILEMMA · 12 BEATS · 19
    ENCOUNTERS`, an eight-row table (policy name · score · encounters · mean payoff ·
    exploitability) and the final K×K convention grid. Rendered into the starter's `#ec-headline`,
    `#ec-wincond`, `#ec-how` and `#ec-teams`; the show/hide, the `bottom: var(--band)` bound and the
    seek-dismissal are the starter's, unchanged.

### Art

**Real art, not placeholders.** `scripts/art/gen_matrix_art.py` (Pillow, committed, deterministic,
re-runnable) renders and commits into `data/`:

- `data/rig_matrix/<livery>/*` — the eight liveries, retinted from paintbot's shipped
  `data/rig_real/{blue,red,green,yellow}/*` rigs to the eight hex colours in the seat table (the
  repo already ships `scripts/art/retint_team_props.py` for exactly this), plus a camp armband decal
  used only in `bach-or-stravinsky`.
- `data/tokens/<variant>_<index>.png` — a hand-drawn silhouette per token, per variant, on the
  type's chrome colour: rock / scroll / shears; handshake / dagger; dove / hawk; antlers / hare;
  lute / violin; three coloured discs; bronze / silver / gold discs. 7 variants × K = 17 sprites.
- `data/yard_floor.png` — the tiled concrete yard bake; walls reuse the shipped
  `client/art/walls/{wall_h,wall_v}.jpg`.
- `data/beam_<livery>.png`, `data/reset_burst.png`, `data/pickup_spark.png`.
- The loading-screen art the `#lockerroom` markup expects: `client/art/lockerroom/bg.jpg` (a dusk
  yard) plus the four portrait `.webp`s the starter references.

No solid-colour placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter already engineers most of this: `relayout()` sets `--hudscale` from the
board width and toggles `#stage.tiny` at `boardW ≤ 620` — kept verbatim. The game block adds three
rules of its own:

- `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
  policy name never collapses to "…";
- under `.tiny`, the eight plates drop the interaction count and the policy name, leaving
  `▮ 11.82` per plate — eight chips still fit one line at 360 px;
- under `.tiny`, `#mg-matrix` drops the per-cell payoff pairs and keeps the labelled grid + the
  flash, and `#mg-indices` shortens to `19 ENC · 41% COOP`.

`tests/test_viewer.nim` asserts all three rules are present, and the 360 px screenshot is part of
the phase 60 viewer check.

---

## Packaging

**`compose.yaml`** — one service, one image (game + player binaries):

```yaml
services:
  game:
    image: cogame-matrix-games:latest
    platform: linux/amd64
    build: {context: ., dockerfile: Dockerfile, network: host}
```

The service name is the single source of the manifest image placeholder:
`services.game` → **`{{GAME_IMAGE}}`** (`coworld build` derives the placeholder from the compose
service name and hard-fails anything else — the lantern learning). The service is named `game`
rather than `matrix-games` on purpose: the derivation of a placeholder from a **hyphenated** service
name is not specified anywhere we can check, whereas `service game → {{GAME_IMAGE}}` is the exact
pattern two certified starters (`cogame-moba`, `cogame-factorio`) ship. `tests/test_manifest.nim`
asserts the derivation `placeholder == service.toUpperAscii() & "_IMAGE"` against the parsed
`compose.yaml`.

**`coworld_manifest_template.json`** — bullwhip's shape with the 0.1.42 strictness hive found:
top-level `$schema`, ≥ 3 `tags` (`game-theory`, `melting-pot`, `multi-agent`, `llm-driven`,
`real-time`, `eight-player`), top-level `episode_timeout_minutes: 20`, top-level `player[]`,
`variants[].description` on **every** variant, `game.runnable.type: "game"`, and a real JSON-Schema
`game.config_schema` in which **every array property carries `minItems`/`maxItems`** (the tandem
certification failure).

- `game.name`: `matrix-games`; `game.replay_viewer.bundle`: `static-replay-viewer`.
- `game.runnable`: `{"type":"game","image":"{{GAME_IMAGE}}","run":["/bin/matrix-games"],
  "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/matrix-games/anthropic_api_key"},
  "source_url":"https://github.com/Metta-AI/cogame-matrix-games/tree/main"}` — the `env` entry is
  mandatory: without it the hosted game container never sees the coworld secret and every league
  episode silently plays scripted (hive learning 2), which surfaces only as a phase-60 check-4
  failure.
- `game.config_schema` properties: `tokens` (string array, `minItems: 1`, `maxItems: 8`, required),
  `players` (object array, `minItems: 1`, `maxItems: 8`, items `{name}`), `num_agents`
  (integer, default **8**), `seed` (integer), `matrix` (string enum of the seven variant matrix
  names, default `running-with-scissors`), `beats` (1..24, default 12), `ticksPerBeat` (10..120,
  default 50), `tokenCap` (2..16, default 8), `tokenRespawnTicks` (5..200, default 45),
  `beamRange` (1..8, default 4), `freezeTicks` (0..60, default 12), `stepCooldownTicks` (1..10,
  default 3), `beamResetCooldown` (0..120, default 25), `beamMissCooldown` (0..60, default 6),
  `viewRadius` (1..24, default 7), `llmTimeoutSeconds` (default 20), `minBeatSeconds` (default 17),
  `maxOutputTokens` (default 900), `model` (string), `episodeTimeoutSeconds` (default 1200),
  `playerConnectTimeoutSeconds` (default 180), `shutdownGraceSeconds` (default 20).
  `additionalProperties: false`.
- `game.results_schema`: the `results.json` object above, with `["number","null"]` on
  `exploitability[]` items and on `coopRate`.
- `game.docs` (**text**, not uri): `{"readme":{"type":"text","value":"<the 200-word what-it-is>"},
  "pages":[{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<board, tokens, the
  ten numbered tick rules, intents, scoring>"}},
  {"id":"matrices.md","title":"The seven matrices","content":{"type":"text","value":"<the matrix
  table with both players' payoffs and what each game is about>"}},
  {"id":"policies.md","title":"Fielding a policy","content":{"type":"text","value":"<PLAYER_PROMPT /
  PLAYER_SCRIPTED how-to, the reply schema and the caps>"}}]}`.
- `game.protocols` — **both**, each a `{"type":"text","value":…}` object (bare strings fail the
  platform validator, the garble trap): `player` (the `matrix.player.v1` frames, the observation,
  the reply schema and its caps) and `global` (the `/global` sprite + chrome frame, and the static
  bundle's `index.html?replay=<url>`).
- `player[]` — **six** entries, all on `{{GAME_IMAGE}}` with `run: ["/bin/matrix-games-player"]`:
  `matrix-games-player` (no env — a prompt policy; `PLAYER_PROMPT` is supplied at upload time),
  `matrix-games-counter` (`env: {"PLAYER_SCRIPTED":"counter"}`),
  `matrix-games-tit-for-tat` (`{"PLAYER_SCRIPTED":"tit-for-tat"}`),
  `matrix-games-fixed-pick` (`{"PLAYER_SCRIPTED":"fixed-pick"}`),
  `matrix-games-always-first` (`{"PLAYER_SCRIPTED":"always-first"}`),
  `matrix-games-always-second` (`{"PLAYER_SCRIPTED":"always-second"}`).
  The last four are the idea's "scripted background bots (always-C/D, always-hawk/dove,
  fixed-pick)".
- **`variants[]` — seven, `num_agents: 8` in every one**, all arena-mode, all sharing
  `{beats: 12, ticksPerBeat: 50, tokenCap: 8, players: [{Ash},{Birch},{Cedar},{Dune},{Elm},{Fern},{Gorse},{Holly}]}`
  and differing only in `matrix` (which fixes K, the token names and the two payoff matrices):

  | id | `matrix` | `num_agents` | description |
  |---|---|---|---|
  | `running-with-scissors` (**default**) | `running-with-scissors` | **8** | Cyclic zero-sum: no fixed policy survives. |
  | `prisoners-dilemma` | `prisoners-dilemma` | **8** | Conditional cooperation with strangers. |
  | `chicken` | `chicken` | **8** | Anti-coordination: who yields, with no words. |
  | `stag-hunt` | `stag-hunt` | **8** | Assurance: risk- versus payoff-dominant equilibria. |
  | `bach-or-stravinsky` | `bach-or-stravinsky` | **8** | Asymmetric camps; interactions only cross-camp. |
  | `pure-coordination` | `pure-coordination` | **8** | Three matches, all paying 1. |
  | `rationalizable-coordination` | `rationalizable-coordination` | **8** | Three matches, paying 1 / 2 / 3. |

- `certification`: `game_config` = `{"num_agents": 8, "seed": 7, "matrix": "prisoners-dilemma",
  "beats": 6, "ticksPerBeat": 50, "playerConnectTimeoutSeconds": 180,
  "players": [{Ash},{Birch},{Cedar},{Dune},{Elm},{Fern},{Gorse},{Holly}]}` and `players` =
  `[{"player_id":"matrix-games-player"},{"player_id":"matrix-games-counter"},
    {"player_id":"matrix-games-tit-for-tat"},{"player_id":"matrix-games-fixed-pick"},
    {"player_id":"matrix-games-always-first"},{"player_id":"matrix-games-always-second"},
    {"player_id":"matrix-games-counter"},{"player_id":"matrix-games-tit-for-tat"}]` — eight seats,
  **`num_agents: 8`**, and **every declared `player[]` id seated at least once**, because
  `players-run` seats the whole roster and a `baseline × N` fixture fails `players_missing` (the
  raid learning). Offline, `matrix-games-player` has no credentials, disables its client and plays
  `counter`, so the fixture is deterministic. 6 beats × 50 ticks = 300 ticks = **12.5 s of replay**,
  which is deliberately longer than the 10 s viewer soak (the ecos learning).

**Other packaging files:** `Dockerfile` (paintbot's two-stage nimby build, producing
`/bin/matrix-games` and `/bin/matrix-games-player`), `Dockerfile.replay-viewer` (paintbot's, with
the matrix-games file list and the same `test -f` assertions), `tools/build_replay_viewer.sh`
(above), `.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
`tools/ci/docker_smoke.sh` from `coworld-builder/templates/tools/ci/` with `<slug>` = `matrix-games`,
`<IMAGE>` = `cogame-matrix-games` and **`<SEATS>` = 8**, `tools/ci/viewer_smoke.mjs` copied with no
substitutions, and `tools/ci/policies.json` naming `matrix-games-reader` (champion #1),
`matrix-games-brinkman` (champion #2, `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`),
`matrix-games-counter` and `matrix-games-tit-for-tat` (fillers). Both champion entries carry
`env: {"PLAYER_PROMPT": "<the prompt above>", "USE_BEDROCK": "true"}`.

---

## Tests

All run in `ci.yml`; the sandbox cannot run any of them locally.

1. **`tests/test_sim.nim` — sim units.** The payoff formula against hand-computed cases for all
   seven matrices, including a mixed case in each (e.g. PD `n = [2,6]`, `m = [7,2]`:
   `rowPayCp = (2·3·7 + 2·0·2 + 6·5·7 + 6·1·2)·100 div (8·9) = 26400 div 72 = 366`) and the
   truncation direction of `div` on a **negative** RWS payoff; the argmax cell with ties → lowest
   index; beam ray length, wall blocking and first-cog targeting; pickup with a full type; the
   `tokenRespawnTicks` refill; freeze / immune / `beamResetCooldown` after a resolution; the
   endowment reset; `bach-or-stravinsky` same-camp `nocontest` and the row-player rule being the
   blue-camp cog regardless of who fired; BFS path tie-breaking; movement blocked by an occupied
   cell; and **determinism** — the same seed and the same order script produce an identical
   `gameHash` after 600 ticks, twice in one process and across a fresh `SimServer`.
2. **`tests/test_baseline.nim` — bounded orders / legality.** For all five baselines × all seven
   variants × seeds 1..8, every seat scripted: every emitted order has an `intent` in the legal set;
   a `token` present and in `0..K-1` exactly when the intent requires one; a `target` that names an
   existing, non-self, **eligible** (cross-camp in BoS) cog exactly when the intent requires one;
   the baseline reads **only** `buildObservation(slot)` (asserted by running it against a frozen
   observation object with the raw sim inaccessible); no cog ever occupies a wall cell or shares a
   cell; every `inv[i]` stays in `0..tokenCap`; no baseline raises; no baseline takes longer than
   1 ms per beat.
3. **`tests/test_indices.nim` — the game-shape oracle.** Gates (a), (b) and (c) of
   `## Sim module` §Feasibility, in Nim, over all seven variants: ≥ 12 resolutions and every seat
   resolving at least once in the cert seat mix; the five named matrix-bites assertions; every
   K×K cell reachable across the scripted sweep. Also asserts `coopRate` is `null` exactly for the
   four variants with no `coopToken`, and that `exploitability` is `null` exactly for seats with
   zero resolutions. Any constant change that turns the game into a room where nothing happens
   fails here rather than in a dead replay.
4. **`tests/test_replay.nim` — end-to-end + strict UTF-8.** Plays a full scripted episode headless,
   writes `results.json` and the replay, then re-reads the replay **bytes**: `validateUtf8 == -1`
   (strict), parses as JSON, `protocol == "matrix.replay.v1"`, `frames.len == ticksPlayed`,
   `series.share.len == ticksPlayed`, `series.score.len == ticksPlayed`, every event tick in
   `0..ticksPlayed`, at least one `pickup`, one `beam`, one `interact`, two `reset` per `interact`,
   `beats` `beatclose` events and exactly one `end`, `results.scores.len == 8`, `results.reason` in
   `{complete, deadline, forfeit}`, `names.len == policyNames.len == 8`, `config.rowPay` and
   `config.colPay` present, file size `< 8 MiB`. A seat is fed a `say`/`notes` of multi-byte runes
   exactly at the 64 / 400 caps and the recorded strings are asserted valid UTF-8 and ≤ the cap (the
   bullwhip byte-truncation bug).
5. **`tests/test_llm.nim` — decision layer.** `extractJsonObject` on fenced, prose-prefixed and
   trailing-prose replies; case-insensitive token and alias matching; an integer `token` index
   accepted; unknown `intent` / missing `token` / ineligible `target` → invalid → **one** retry →
   `counter` fallback with `source: "fallback"`; a stubbed transport that times out, 429s, 403s or
   returns junk never raises and always yields a legal order; **one batch carries every open seat**
   (assert `RequestBatch.len == openSeats` and that batch starts are ≥ `minBeatSeconds` apart).
6. **`tests/test_manifest.nim` — packaging.** `num_agents == 8` in **all seven** variants and in
   `certification.game_config`; the image placeholder equals the one derived from `compose.yaml`'s
   service name (`{{GAME_IMAGE}}`); `replay_viewer.bundle == "static-replay-viewer"`;
   `game.docs.readme` + non-empty `pages`; `game.protocols.player` **and** `.global` present and
   both `{"type":"text","value":…}` objects; `ANTHROPIC_API_KEY_URI` in `game.runnable.env`;
   `game.runnable.type == "game"`; top-level `episode_timeout_minutes`; ≥ 3 `tags`; every array
   property in `config_schema` carries `minItems` and `maxItems`; every `player[]` id appears at
   least once in `certification.players`; every variant carries a `description`.
7. **`tests/test_viewer.nim` — chrome frame + game block.** `buildStateJson` emits exactly the
   chrome key set (`t, mt, ph, pl, sp, mx, st, lp, sk, ff, en, mm, bs, teams, roster, lead, beats,
   lulls, over, hold`) plus `seats`; `teams` keys are exactly the K token keys drawn from
   `["red","blue","green"]`; `lead.pts` rows are `[t, share…]` of length `K + 1`; `seats` has 8
   entries carrying policy name, livery, score and interaction count; `over` is present on the
   terminal frame; a `.beat-marker` CSS rule exists for **every** beat kind emitted
   (`interact`, `bigpay`, `leadchange`, `over`); the `.plate-name` and two `.tiny` rules are
   present; and **no game-block top-level identifier collides with the chrome alias list** exported
   by `chrome_common.js` (the tandem hoisting bug).
8. **`docker-smoke` (`tools/ci/docker_smoke.sh`, `SMOKE_SEATS = 8`).** Builds the image, runs a real
   **8-seat** episode in containers from the certification fixture, asserts the game **and every
   player** container exits 0 (the raid learning), validates `results.json` against the results
   schema, and copies the replay to `SMOKE_REPLAY_OUT` (`dist/smoke/replay.json`), uploaded as the
   `smoke-replay` artifact. Its independent seat-count cross-check (`SEAT-COUNT FAIL:`) is the
   second place `num_agents = 8` is enforced.
9. **`wasm-viewer` job — the bundle is EXECUTED, not merely built.** `needs: docker-smoke`,
   downloads `smoke-replay`, builds the bundle via `tools/build_replay_viewer.sh`, installs
   Playwright pinned **1.55.0**, and runs **`tools/ci/viewer_smoke.mjs --bundle
   dist/static-replay-viewer --replay dist/smoke/replay.json --soak 10`** over local HTTP against
   that replay. Pass requires `data-replay-loaded="true"` **and** three different clock readouts at
   0 %, 50 % and 100 % **and** an uninterrupted 10 s of playback that keeps advancing (the cogball
   soak);`data-replay-error` or silence fails the job. Evidence (`viewer-smoke.png`,
   `viewer-smoke.json`) uploads on success and on failure. This is the gate cogame-lantern did not
   have.

---

## Out of scope (v1)

- **The 2-seat modes.** `*_in_the_matrix__repeated` (one fixed pair, many resolutions) and
  `__one_shot` (a single resolution) are not built. Every variant is 8-seat arena-mode with random
  encounters. Coordinator ruling of this run; a 2-seat variant would need a different `num_agents`
  and this coworld is an 8-seat game.
- **The BitWorld / coworld-staghunt runtime.** The idea floats it as an engine candidate; it is not
  available, so paintbot's engine is adapted instead. Nothing in the build references it.
- **Per-tick LLM control.** A seat submits one intent per 50-tick beat; the per-tick move/turn/
  interact policy is the deterministic kernel. 4 800 LLM calls per episode does not fit any timeout
  budget, and 96 does.
- **Any inter-seat channel.** No chat, no signals, no pre-play negotiation. `say` is spectator-only.
  Deliberate: Chicken is "who yields, with no words", and a silent room is the anti-collusion
  property.
- **Custom matrices from config.** `matrix` is an enum over the seven named games; the payoff tables
  are compile-time constants. No user-supplied K×K arrays in v1.
- **Melting Pot's pixel observations and RL-vector policy interface.** Seats read a decoded JSON
  board, not an 88×88 RGB window, and there is no PPO training path in this repo.
- **Explicit resident/visitor score normalisation.** The idea's anti-collusion motive is served by
  the scripted background bots being the league's fillers, seeded spawns, anonymous aliases and no
  channel — not by a bespoke normalising formula on top of the platform's Elo.
- **Three-or-more-way interactions, token trading or dropping, and inventory theft.** An interaction
  is always exactly two cogs; tokens only move from a spawner into an inventory, and only leave on a
  reset.
- **Cross-episode memory or reputation.** Every episode starts from the seeded opening state and
  aliases carry no history; nothing persists except the league rating.
- **Re-simulating playback.** The viewer decodes recorded state; there is no replay-hash mismatch
  mode, no `--mismatch-quit`, and no `#mmwarn`.
- **Live spectator features beyond what paintbot gives free:** no POV lens, no first-person PiP, no
  zoom/minimap (fixed board), no achievements, no perks or handicaps.
- **Any variant that changes `num_agents`.** Matrix Games is an eight-seat game, in every variant
  and in the certification fixture.
