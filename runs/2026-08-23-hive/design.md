# hive — design note (2026-08-23)

`Metta-AI/cogame-hive`, a four-colony ant-foraging Coworld played on one shared 160 × 88 cell
meadow: each seat is a single policy driving twenty-four identical ants that see one cell around
themselves, drop and smell two decaying pheromones, and carry food home. It is forked from
**`Metta-AI/coworld-ctf` (paintbot)**, read at its read-only mount `/workspace/starters/coworld-ctf`.
**Every convention there holds here unless this note says otherwise.** The starter is pinned by game
shape: hive is a real-time tick loop with rules written fresh for this coworld — nothing pre-exists
to port, so it is the first row of the starter table (`prompts/10-design.md` §"Starter table"),
never `cogame-moba` — and paintbot already ships every piece a swarm game needs: a 24 Hz integer
step loop with a recorded-input replay (`src/ctf/sim.nim`, `src/ctf/replays.nim`), a
**static wasm replay viewer that re-derives every frame in the browser**
(`replay-viewer/ctf_replay.nim`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`), a
broadcast chrome whose **scorebug is already built for 2–4 teams**
(`client/replay_broadcast.html:177-180,1487-1494` — `ensureScorebug()` puts two plates per side for a
3–4 team game, which is exactly four colonies on one line) and whose relayout loop is already
authored down to a **360 px** board (`client/replay_broadcast.html:4085-4133`, `--hudscale =
clamp(0.5, boardW/760, 1.6)`, `.tiny` at `boardW <= 620`), a per-tick keyframe/digest discipline
(`gameHash`), and a bake-then-serve server (`src/ctf/server.nim`) with the `bitworld/runtime`
artifact contract.

Two pieces come from paintbot's sibling in the builder's starter set, `Metta-AI/cogame-bullwhip`
(read at `/workspace/starters/cogame-bullwhip`), because paintbot predates both and the pins require
them: the **server-side LLM client with a one-parallel-batch-per-turn decision loop**
(`src/bullwhip/llm.nim:419-472`, `decideAll` over `client.curl.makeRequests(batch,
client.timeoutSeconds)`) and the **`coworld-replay` postMessage bridge** in
`replay-viewer/static_replay.js:20-33,120-124` (`tell("loading")` / `tell("ready")` /
`tell("error")`), which SPEC §Definition of done check 8(c) greps for and which paintbot's own
`replay-viewer/static_replay.js` does not have. Bullwhip also supplies the packaging shape the
builder scaffold expects — one image, two entrypoints, single-service `compose.yaml`.

Four deliberate deviations from paintbot are listed and justified where they occur: a **UTF-8 JSON
replay** instead of the binary `COWLDCTF` format (§Server — SPEC check 4 and the shared
`tools/ci/docker_smoke.sh`'s `SMOKE_REQUIRE_REPLAY_JSON=1` both require JSON); **decisions made in
the game server** instead of in the player container (§Decisions); **a cell grid instead of
paintbot's sub-pixel continuous motion** (§Sim module — a pheromone field is a lattice, and an
integer lattice is what makes the wasm re-derivation bit-exact); and **one authored field instead of
the procedural terrain generator** (§Sim module).

There is **no `OPEN` section.** Every rule the idea leaves loose is one the rails say the designer
settles (seat count inside the idea's stated 2–4, scoring when the idea pins one, parameter values,
viewer composition, policy prompts), and each is decided below with its reason.

**Source idea, verbatim:**

> Each seat drives a colony of identical agents with tiny local views; they drop and sense two
> decaying pheromone types. Food sources appear and vanish; colonies compete for them on a shared
> field. No direct messaging — coordination has to be stigmergic. Scored by food returned to nest.
>
> Seats: 2-4 colonies
> Motive: competitive between colonies, cooperative within
> Policy interface: RL vector, batched over bodies
> Fills gap: swarm scale / indirect communication / one-policy-many-bodies
> Integrity (anti-collusion): A colony is one policy, so pheromone conventions are the intended
> coordination, not an exploit; colonies compete over food and colony identities are anonymized per
> episode.
>
> Replay plan (watchability): Pheromone fields glow as two decaying overlay colors, so each colony's
> strategy is literally painted on the ground; ant flows read like traffic. Time-compressed, nest
> counters pulsing on every delivery; trail wars between colonies are the highlight reel.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c
>
> *(The link is recorded as provenance only. It was not fetched, and nothing inside it is part of
> this design.)*

**Three re-readings of the idea, decided here and never revisited:**

1. **"Seats: 2-4 colonies"** → **exactly 4**, always, in every variant and the cert fixture
   (§Packaging). Four is the top of the stated range and it is the number that lets one episode seat
   champion #1, champion #2 and both scripted fillers simultaneously, which is what the league wants
   (`playbooks/make-coworld.md` §Phase 4: two ranked champions plus ≥1, normally 2, fillers). Four
   nests at the four corners of a rectangle is also the largest seat count that stays *exactly* fair:
   the corner set is closed under both mirror axes, so every colony's situation — one horizontal
   neighbour, one vertical neighbour, one diagonal, one equidistant centre — is identical.
2. **"Policy interface: RL vector, batched over bodies"** → every seat is an **LLM prompt policy with
   a scripted fallback** (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=<name>`), emitting one **doctrine
   vector** per decision turn that the deterministic ant kernel applies to all twenty-four bodies at
   24 Hz. This is an inherited pin (SPEC §Design pins: both champions must be `PLAYER_PROMPT`
   policies). The doctrine *is* a batched-over-bodies vector — nine integers and a target block — and
   it is recorded as such, so exposing it over the wire to an external RL policy is a v0.2 protocol
   addition, not a v1 redesign. It is listed in §Out of scope (v1).
3. **"No direct messaging — coordination has to be stigmergic"** is enforced structurally, not by
   politeness. An ant's only inputs are the eight cells around it, its own carrying state, and — only
   within 12 cells of home — a bearing to its nest. There is no ant-to-ant channel, no shared blackboard,
   no colony-wide broadcast. The colony policy itself is deliberately given a **coarse, lagged,
   partly-blind** view (§Server): an 8 × 8-cell block downsample of its *own* two pheromone planes,
   rival trail readings only where its own ants have walked in the last turn, and food amounts only
   as last seen. The policy can bias the heading ants leave the nest with (`focus`) — that is a
   physical act at the nest mouth, not a message — and it can tune the kernel. It cannot address an
   ant, name an ant, or move an ant. Nothing a colony learns about a rival arrives except through the
   ground.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and
where each is satisfied:**

| Pin | How hive satisfies it |
|---|---|
| Starter by game shape | `coworld-ctf` (paintbot) — any real-time game loop with rules written for this coworld; paintbot supplies the loop, the per-tick replay, the static wasm viewer and the 2–4 team chrome (title paragraph above). |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-hive`, **public at creation** — public is a certification prerequisite (`source-resolves` 404s on private). §Packaging. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (two champion prompts) vs `PLAYER_SCRIPTED=marcher` / `PLAYER_SCRIPTED=driftling`; one image `coworld-hive:latest`, `run: /bin/hive-player`. §Decisions, §Packaging. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`, built by `tools/build_replay_viewer.sh` (forked from paintbot's). §Viewer, §Packaging. |
| Real art, starter chrome verbatim | Paintbot's `client/replay_broadcast.html` chrome block and `client/chrome_common.js` kept verbatim (id-for-id list in §Viewer); painted meadow floor, painted rock, painted food caches, authored ant sprites. No placeholders. §Viewer. |
| Two name spaces | Prompts and observations see only the colony aliases `Amber` / `Teal` / `Lime` / `Magenta`, and the alias→seat assignment is **re-drawn from the episode seed every episode**; real policy names appear only in `replay.names.players`, `results.names` and the viewer's scorebug plates. §Server, §Viewer. |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | 495 s expected worst case / 660 s hard stop against a 720 s budget, arithmetic spelled out in §Decisions; every wait bounded; LLM failure → one retry → the scripted doctrine. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4** in variant `default`, variant `sprint`, and `certification.game_config`; `SMOKE_SEATS=4`. §Packaging. |

---

## The game

**Hive is four ant colonies foraging one meadow.** Each seat owns a nest in one corner and
twenty-four identical ants. An ant sees one cell in every direction and nothing else. Ants drop two
pheromones — a **food trail** when they walk home carrying, a **home trail** when they walk out
empty — and both fade. Food caches appear in symmetric sets, get eaten, and vanish. A colony's score
is its share of all the food returned to nests. There is no combat, no chat, and no way for a
colony's policy to steer an individual ant: the only levers are the kernel weights every ant runs and
the heading ants leave the nest with. Everything else the colony does, it does by painting the
ground.

**Seats: `num_agents` = 4.** One seat = one colony = twenty-four bodies. Reason in re-reading 1
above.

### The field

- **Grid.** `fieldCols = 160` × `fieldRows = 88` cells, `cellPx = 8`, so the board is
  **1280 × 704 px**. *Deviation from paintbot, deliberate:* paintbot's board is 1235 × 659
  (`src/ctf/sim_types.nim:813-814`); hive's dimensions are chosen so the cell grid divides evenly
  into 20 × 11 observation blocks of 8 × 8 cells and so the board is exactly mirror-symmetric on both
  axes. Cell `(cx, cy)` occupies pixels `[cx*8, cx*8+7] × [cy*8, cy*8+7]`; `cx ∈ 0..159`,
  `cy ∈ 0..87`; origin top-left, +x right, +y down.
- **Rock.** Static impassable cells, authored in `data/meadow.fieldspec.json` (§Sim module) as
  rectangles and discs, **invariant under reflection in `cx → 159 − cx` and in `cy → 87 − cy`**. A
  test enforces the invariance and that the free floor is one 4-connected component. Rock blocks ant
  movement and holds no pheromone. Rock is **not secret** — the terrain is in every seat's
  observation, always.
- **Nests.** Four, one per corner, each a 5 × 5 cell pad (Chebyshev radius 2 around its centre):

  | Nest | Centre cell | Colour | Hex |
  |---|---|---|---|
  | `N0` | (16, 12) | Amber | `#f2c14e` |
  | `N1` | (143, 12) | Teal | `#4ecdc4` |
  | `N2` | (16, 75) | Lime | `#9fd356` |
  | `N3` | (143, 75) | Magenta | `#e26db5` |

  The four centres are the orbit of (16, 12) under both mirrors, so the set is exactly symmetric.
  **Colour is a property of the nest, never of the seat.** The seat→nest assignment is a permutation
  of `[0,1,2,3]` drawn from the episode seed (§Sim module, "Randomness") and re-drawn every episode —
  that is the idea's per-episode anonymisation: `Amber` names a corner, and tells an opponent nothing
  about which policy sits there.
- **Ants.** `antsPerColony = 24`, so 96 bodies on the field. An ant has a cell, a heading (one of 8,
  `0 = E`, counter-clockwise in 45° steps), a carrying flag, and — when carrying — the id of the
  source the unit came from. Ants have no health, never die, never fight, and **never block each
  other**: many ants may share a cell (that is what makes a trail read like traffic). Only rock and
  the field edge block movement. An ant acts once every `antStepTicks = 2` ticks: ant with global
  index `g = nestIndex * 24 + antIndex` acts on tick `t` iff `(t + g) mod 2 == 0`, so the load is
  split evenly across ticks and the flow looks continuous.
- **Pheromones.** Two planes per colony — `F` (food trail) and `H` (home trail) — each a
  `uint16` per cell, `0 … pheromoneMax = 4000`. Total field state 160 × 88 × 4 × 2 × 2 B = 220 KiB.
  Both **decay**: every `decayPeriodTicks = 8` ticks, every non-zero cell of every plane becomes
  `p ← (p * pheromoneDecayNum) shr 8` with `pheromoneDecayNum = 248`, and any `p < pheromoneFloor = 4`
  becomes `0`. Per-tick retention is `0.96875^(1/8) = 0.99604`; **half-life ≈ 175 ticks ≈ 7.3 s**, so
  an unmaintained trail is gone in about half a minute and a trail that pays keeps itself alive. Zero
  cells are skipped, which is most of the field for most of the episode.
- **Food.** A source is `{id, cell, amount, spawn_tick, life_ticks}`. Sources **appear in symmetric
  sets** so that no colony is handed a closer meadow than another:
  - **Orbits.** Every `sourceSpawnPeriod = 240` ticks, if fewer than `maxOrbits = 3` orbits are alive,
    exactly one new orbit spawns. A cell is drawn from the PCG stream inside the top-left quadrant
    (`cx ∈ 4..79`, `cy ∈ 4..43`), rejected and re-drawn (up to 64 tries, then the spawn is skipped)
    unless it is free floor at Chebyshev distance ≥ `minNestClearance = 14` from every nest centre
    and ≥ 3 from every live source. The orbit is that cell plus its three mirror images; each of the
    four sources gets `sourceAmount = 60` units and `sourceLifeTicks = 1440` (60 s).
  - **Bonanzas.** At `t = 1200` and `t = 3600`, four sources spawn on the exact centre block —
    (79, 43), (80, 43), (79, 44), (80, 44) — each with `bonanzaAmount = 100` and
    `bonanzaLifeTicks = 900`. Equidistant from all four nests, four hundred units, and the reason the
    middle of the meadow becomes a battlefield twice per match.

  A source retires when `amount` hits 0 (`cause: "depleted"`) or when its life expires
  (`cause: "expired"`). Over a 4800-tick episode this offers roughly 18 orbits × 60 = **~1080 units
  per colony's quadrant** plus **800 contested centre units**; total deliveries across four colonies
  typically land between 1500 and 3000, so the nest counters pulse constantly and the score is a
  large, well-separated number rather than a coin flip.

### The ant kernel (identical for every ant of every colony; parameters come from the doctrine)

An acting ant at cell `c` with heading `d` considers exactly **three** candidate cells:
`c + dir((d+7) and 7)`, `c + dir(d)`, `c + dir((d+1) and 7)` — forward-left, forward, forward-right.
It cannot reverse (except on a pickup or a stall). Candidates that are rock or off-field are
discarded. If all three are discarded the ant sets `d ← (d + 2) and 7` (a 90° turn) and does not move
this activation; the free-floor connectivity invariant guarantees this terminates.

For a **searching** (not carrying) ant, candidate `k` scores, in `int32`:

```
score(k) = ((alphaFood  * F_own[k])      shr 4)
         + ((alphaRival * F_rivalMax[k]) shr 4)
         - ((alphaHome  * H_own[k])      shr 4)
         + (if k is the forward cell: alphaFwd else 0)
         + alphaScent * foodAdjacent(k)
         + rnd(0 .. alphaNoise - 1)
```

`F_rivalMax[k]` is the largest food-trail value among the other three colonies at `k` — an ant
literally smells a rival's road under its feet. `foodAdjacent(k)` is 1 when a live source with
`amount > 0` sits in `k` or one of `k`'s eight neighbours, else 0. `alphaScent = 900` is fixed: food
you can smell always wins.

For a **carrying** ant:

```
score(k) = ((betaHome * H_own[k]) shr 4)
         + (if within nestSenseCells = 12 of own nest centre AND k reduces the
            Chebyshev distance to it: betaNest else 0)
         + (if k is the forward cell: betaFwd else 0)
         + rnd(0 .. 32 - 1)
```

with `betaNest = 1200` and `betaFwd = 260` fixed. **Path integration is deliberately short-ranged.**
Beyond 12 cells a laden ant has no idea where home is and must ride the home trail its nestmates
laid — that is what makes `H` load-bearing rather than decorative, and it is why a colony that lets
its home trail rot loses its harvest on the way back.

Highest score wins; ties break in candidate order **left, forward, right**. The ant moves to the
winner and sets `d` to the direction it moved.

The doctrine maps to the coefficients by this exact table (all integer):

| Coefficient | From the doctrine | Range |
|---|---|---|
| `alphaFood` | `trail_gain * 4` | 0 … 400 |
| `alphaRival` | `poach * 3` | 0 … 300 |
| `alphaHome` | `spread * 3` | 0 … 300 |
| `alphaFwd` | `320 - spread * 2` | 320 … 120 |
| `alphaNoise` | `40 + (100 - trail_gain) * 4` | 40 … 440 |
| `betaHome` | `200 + trail_gain * 2` | 200 … 400 |
| `layFood` | `40 + lay_food * 3` | 40 … 340 |
| `layHome` | `20 + lay_home * 2` | 20 … 220 |
| `scoutCount` | `(scouts * 24 + 50) div 100` | 0 … 24 |

The first `scoutCount` ants of the colony by index are **scouts** for that turn; the rest are
**foragers**. A scout runs the same kernel with `alphaFood ← alphaFood div 4`, `alphaRival ← 0` and
`alphaNoise ← alphaNoise * 2`: it ignores the roads and wanders. Its deposits are unchanged, so the
instant a scout finds food it becomes a carrier and lays a full-strength trail home — that is the
recruitment moment, and it is the single most watchable thing in the game.

### Time and turns

`dt = 1/24 s` (paintbot's `TargetFps` / `ReplayFps` = 24, `src/ctf/sim_types.nim:294,353`, kept).
The episode is a fixed **`episodeTicks = 4800` ticks = 200 s** of sim time, divided into
**20 decision turns of `turnTicks = 240` ticks (10.0 s)**. At the first tick of a turn the server
freezes the state, builds all four seats' views, collects one **doctrine** per seat as one parallel
batch (§Server), and installs them; the ant kernel then runs those doctrines for all 240 ticks. The
LLM is the queen at 0.1 Hz; the kernel is the colony at 24 Hz.

### Resolution order (exact, per tick `t`, no exceptions)

"Ant order" always means ascending global index `g = nestIndex * 24 + antIndex`; "seat order" means
ascending slot 0…3.

1. **Turn clock.** `turn = t div 240`. If `t mod 240 == 0`: install the doctrines collected for this
   turn (§Server), clear each colony's `sensed` block map, roll `delivered_last_turn`, emit
   `turn_start` and one `doctrine` event per seat.
2. **Source lifecycle.** If `t mod 240 == 0` and `orbits_alive < 3`, draw and spawn one orbit →
   `source_spawn{kind:"orbit"}`. If `t == 1200` or `t == 3600`, spawn the four centre sources →
   `source_spawn{kind:"bonanza"}`. Then, in ascending source id, retire every source with
   `amount == 0` or `t - spawn_tick >= life_ticks` → `source_gone` with its `cause` and the
   per-colony tally of what was taken from it.
3. **Activation set.** Ant `g` acts iff `(t + g) mod 2 == 0`. Steps 4–9 process the acting ants in ant
   order.
4. **Recall modifier.** If the acting ant's colony has `recall: true` in its active doctrine, the ant
   deposits nothing (step 5 is skipped for it), uses the **carrying** kernel in step 8 regardless of
   its carrying flag, and once inside its nest pad holds still with its heading frozen and takes no
   release (step 9 skipped) until a turn arrives whose doctrine has `recall: false`.
5. **Deposit.** The acting ant adds to its **current** cell: carrying → `F_own += layFood`;
   searching → `H_own += layHome`; saturating at `pheromoneMax`. It also stamps
   `sensed[colony][block(cell)] = turn` (this is what unlocks rival readings in the next view).
   Depositing before moving is what makes the trail include the cell the ant stood on.
6. **Pickup.** If the acting ant is not carrying, scan its own cell then its eight neighbours in the
   fixed order N, NE, E, SE, S, SW, W, NW for the lowest-id live source with `amount > 0`. On a hit:
   `amount -= 1`, `carrying = true`, `carried_from = source.id`, `d ← (d + 4) and 7` (about-face),
   and the unit is added to the 24-tick `harvest` bucket for (source, colony). **Skip step 8 for this
   ant this activation.**
7. **Delivery.** If the acting ant is carrying and its cell lies inside its **own** nest pad:
   `delivered[seat] += 1`, `carrying = false`, emit `deliver`. If `carried_from`'s cell was within
   `raidRadius = 20` Chebyshev cells of a *different* colony's nest centre, the delivery is flagged
   `raid: true` and a `raid` event names the victim. A carrying ant that walks over a **rival's** nest
   pad does nothing — you cannot deliver to, or steal from, another nest. **Skip step 8 for this ant
   this activation**, then apply step 9.
8. **Move.** Every other acting ant runs the kernel above and steps.
9. **Release.** An ant that just delivered, and any ant standing inside its own nest pad that is not
   carrying and did not move this activation, is re-launched: with probability `focus_weight` percent
   (one PCG draw, integer compare) its heading becomes the one of the eight best matching the bearing
   from the nest centre to the focus cell; otherwise a uniform draw over the eight. `focus == null` ⇒
   always uniform. **This is the only colony-level steering that exists**, and it acts at the nest
   mouth on a departing body, never on an ant in the field.
10. **Trail-war scan.** If `t mod 48 == 0`, for every 8 × 8 block compute each colony's mean `F`; if
    two or more colonies exceed `trailWarThreshold = 800` in the same block, emit one `trail_war`
    naming the block, the colonies and their strengths (at most one per block per scan).
11. **Pheromone decay.** If `t mod 8 == 0`, apply the decay rule above to every non-zero cell of all
    eight planes.
12. **Harvest flush.** If `t mod 24 == 0`, emit the accumulated `harvest` records (one per
    source × colony pair with a non-zero bucket) and clear the buckets.
13. **Keyframe.** If `t mod 24 == 0`, append a keyframe: tick, the 96 ants' `(cx, cy, state)`, the
    four `delivered` counters, the four carrying counts, the live sources, and the u32 state digest
    (§Sim module).
14. **Seek snapshot.** If `t mod 240 == 0`, the *runtime* (native and wasm alike) keeps a full state
    snapshot in memory — the eight pheromone planes, the ants, the sources, the counters, the PCG
    state (220 KiB + change; 21 snapshots ≈ 4.7 MB). Snapshots are **not** written to the replay; they
    exist so a backward seek in the viewer replays at most 240 ticks (§Viewer).
15. **End check.** If `t + 1 == episodeTicks` → end the match, `reason: "complete"`,
    `end_rule: "full_time"`. Else if the wall-clock stop has tripped → `deadline` / `wall_clock`. Else
    if `t mod 24 == 0` and an invariant guard fails (an ant off-field or on rock, a source amount
    below zero, a `delivered` counter that decreased, a pheromone value above `pheromoneMax`) →
    `fault` / `sim_fault`.

### Scoring, sign, and what the league ranks by

Food returned to nest, as a share of all food returned:

```
delivered[s]  = units this seat's ants carried into their own nest pad over the episode
total         = delivered[0] + delivered[1] + delivered[2] + delivered[3]
score[s]      = delivered[s] / total            if total > 0
score[s]      = 0.25                            if total == 0 (no colony found anything)
```

**Higher is better.** `score ∈ [0, 1]` and `sum(score) == 1.0` exactly, for every legal outcome —
the game is exactly constant-sum across the four colonies, which is the idea's integrity claim: the
only way to raise your score is to take food a rival did not. `win[s] = delivered[s] == max(delivered)
and that maximum is unique`; `winner` is that slot index, or `null` when the maximum is tied.
Rounding: `score[s]` is emitted as the double `delivered[s] / total`, and the fourth value is emitted
as `1.0 - (score[0] + score[1] + score[2])` so the four printed numbers sum to exactly 1.0.

Worked example: `delivered = [412, 366, 289, 233]`, `total = 1300` →
`scores = [0.31692, 0.28154, 0.22231, 0.17923]`, `win = [true, false, false, false]`, `winner = 0`.

**The league ranks by Elo computed from `results.scores`** (the platform's `scores` array is the only
cross-game ranking input; Elo 1000 start, K 32, per the phase-50 league settings). A `fault` episode
scores 0.25 for every seat — an infra fault is nobody's loss.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.end_rule` carries the detail.

| `reason` | `end_rule` | When |
|---|---|---|
| `complete` | `full_time` | All 4800 ticks (or the variant's total) simulated. The normal ending. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660 by default) elapsed before full time. The sim stops at that tick and scores the `delivered` counters as they stand; shares still sum to 1.0. **Declared acceptable** for phase-60 verification: it means the hosted LLM was slow, not that the game broke, and the replay is complete and self-consistent up to the stop tick. If it stops before tick 240 and `total == 0`, all four seats score 0.25 and `winner` is `null`. |
| `fault` | `sim_fault` | An invariant guard from step 15 tripped. All scores 0.25, `winner: null`, partial replay written. |
| `fault` | `host_error` | An unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

No other value may appear. A seat that never connects does **not** end the episode: its colony is
driven by the `marcher` scripted baseline for the whole match, the no-show is reported to
`COGAME_PLAYER_FAILURE_URI` (lowest offending slot only, paintbot's `declarePlayerFailure`,
`src/ctf/server.nim:1213`), and the match plays to `full_time`.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {marcher, driftling}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=marcher`. **A scripted policy seated as a champion is a failure state**
(`playbooks/make-coworld.md` §Phase 2).

**Where the decision happens.** *Deviation from paintbot, deliberate:* paintbot's bot decides inside
its own container (`players/baseline/baseline.nim`, a Sprite-v1 client). In hive the **game server**
owns the LLM client, exactly as bullwhip does (`src/bullwhip/llm.nim`). Reasons: the hosted Bedrock
sidecar credentials and the `anthropic_api_key` coworld secret are injected into the *game* pod;
phase 60 greps the *game* log for `falling back` / `LLM provider is unavailable`; "one parallel batch
per turn" is a game-server property; the shared `tools/ci/docker_smoke.sh` forwards
`ANTHROPIC_API_KEY` to the game container only; and keeping both policy kinds inside the server makes
the recorded doctrine stream reproducible with no network in the loop. The player container is
therefore thin: it connects, sends one `register` frame carrying its prompt (or its baseline name),
and thereafter only receives (§Server).

**Cadence and batching — this is what makes an LLM feasible for a swarm.** One decision every
`turnTicks = 240` ticks (10.0 s of sim time), **20 turns per episode**, **one call per colony —
never one call per ant**. 96 bodies are driven by 80 LLM calls in the whole episode. At each turn the
server builds all four seats' request bodies and issues them as **one parallel batch** — a single
`client.curl.makeRequests(batch, client.timeoutSeconds)` over all open seats, exactly bullwhip's
`decideAll` (`src/bullwhip/llm.nim:419-472`) — wrapped in one per-turn deadline. **Seats are never
queried sequentially.** Every turn batches exactly 4 requests; at most 4 are in flight.

**Wall-clock arithmetic (must stay inside 60 % of `episodeTimeoutSeconds` 1200 = 720 s):**

```
20 turns x 22.0 s per-turn budget                = 440 s
player connect wait (4 seats, typical)           =  15 s   (cap: playerConnectTimeoutSeconds 90)
sim: 4800 ticks, 96 ants + 220 KiB field, native =  10 s   (perf test bounds this at <= 45 s)
field bake + results + replay writes             =  30 s
                                                 -------
expected worst case                              = 495 s   < 720 s  (225 s margin)
engine hard stop wallClockBudgetSeconds          = 660 s   -> reason "deadline"
platform kill (episode_timeout_minutes 20)       = 1200 s
```

Per-tick sim cost, out loud: 48 ant activations per tick × 3 candidates × ~8 integer ops ≈ 1.2 k ops,
plus amortised decay of 8 planes × 14 080 cells every 8 ticks ≈ 14 k cell updates per tick (skipping
zeros, so far fewer in practice) ≈ 42 k ops — call it 45 k integer ops per tick, 2.2 × 10⁸ for the
episode. That is a couple of seconds in a `-d:release` native build and under ten in wasm; the perf
test's 45 s bound is deliberately loose.

Typical wall clock is far under the worst case: a turn whose slowest seat answers in 5 s costs 5 s,
not 22. With no credentials at all (offline certification, the docker smoke) the LLM client disables
itself on first discovery, every turn falls back instantly with no network wait, and the whole
episode finishes in seconds.

**Per-turn timing, per seat:** first attempt deadline **14.0 s**. On timeout, transport error,
non-JSON reply, or a reply carrying no usable doctrine → **one retry** with a 6.0 s deadline and the
"your previous reply was invalid" hint appended (bullwhip's retry shape). If that also fails → that
seat's doctrine for this turn is the **`marcher` scripted doctrine**, computed in microseconds, and a
`fallback` event is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`. Worst case
14.0 + 6.0 = 20.0 s ≤ the 22.0 s turn budget.

**Budget guard (settle early rather than overrun).** At the start of each turn, if
`elapsed + 2 * turnBudgetSeconds > wallClockBudgetSeconds`, the LLM is skipped for **all remaining
turns** and the episode finishes on the scripted layer (< 1 ms per turn), so it ends
`complete/full_time` instead of `deadline`. A `budget_guard` event records the turn it engaged. Only
if even that overruns — arithmetically impossible, but the check is unconditional — does the engine
stop at 660 s with `deadline/wall_clock`.

**Degrade, never hang.** Every wait is bounded: the two attempt deadlines, one outer per-turn deadline
of 22.0 s, `playerConnectTimeoutSeconds` (90 hosted, 60 in the cert fixture) on the connect wait, a
3.0 s per-seat deadline on the final done-broadcast, and the 660 s engine stop. The game container
does **not** receive `COWORLD_TIMEOUT_SECONDS`; 1200 s is assumed and never approached. A seat that
disconnects mid-match keeps playing: its doctrine source degrades to `marcher` and revives on
reconnect. No failure mode leaves a colony unactuated — a colony always has a doctrine, defaulting to
the previous turn's, then to `marcher`.

**The LLM client** (`src/hive/llm.nim`) is bullwhip's `llm.nim` with hive's schema. Credential ladder,
in order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` + `AWS_BEARER_TOKEN_BEDROCK`, region
from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI` (read through `readCogameUri`) → none (disabled, instant fallback, one log
line). Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, `us.anthropic.claude-sonnet-4-6`,
`us.anthropic.claude-sonnet-4-5-20250929-v1:0`; on a 403 the client advances to the next candidate.
`max_tokens = 900` (400 truncates — playbook gotcha), **no `output_config.effort`** (Haiku 4.5 rejects
it), `temperature = 0.4`.

**System prompt (fixed, identical for every seat and both champions, sent as the system message):**

```
You are the whole mind of one ant colony on a 160x88 cell meadow shared with three
rival colonies. You have 24 identical ants. You cannot see through their eyes, you
cannot talk to them, and you cannot move any single ant. Each ant sees only the eight
cells around it. It drops a FOOD trail while carrying food home and a HOME trail while
searching, and it steers by the trails it smells. Both trails fade with a half-life of
about 7 seconds. Ants know the way home only within 12 cells of the nest; further out
they must ride the home trail their nestmates laid.
Food caches appear in symmetric sets - one near each colony - and twice per match a big
cache appears dead centre. A cache runs out. Every unit of food an ant carries into
your nest pad is one point. You score your share of ALL food returned by ALL FOUR
colonies, so taking food a rival would have taken is worth exactly as much as finding
your own.
Every 10 seconds you set the colony's DOCTRINE: how many ants explore instead of
following roads, how strongly ants follow trails, whether they poach rival roads, how
hard they avoid their own outbound trail, how much scent they lay, and which direction
departing ants face. That is all. Everything else your colony does is emergent.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"scouts":0-100,        // percent of your 24 ants that ignore trails and wander
 "trail_gain":0-100,    // how strongly searching ants follow YOUR food trail
 "poach":0-100,         // how strongly searching ants follow RIVAL food trails
 "spread":0-100,        // how hard ants avoid your own home trail (fan out)
 "lay_food":0-100,      // strength of the food trail a laden ant lays
 "lay_home":0-100,      // strength of the home trail a searching ant lays
 "recall":true|false,   // true: every ant drops its road and walks home, then waits
 "focus":[bx,by]|null,  // the 20x11 observation block departing ants head toward
 "focus_weight":0-100,  // percent of departing ants that take the focus bearing
 "note":"<=140 chars",  // your reasoning, shown to spectators only
 "say":"<=32 chars"}    // one short line, shown to spectators only
High trail_gain plus low scouts exploits a known cache hard and goes blind when it runs
out. High scouts finds the next cache but wastes ants. High poach walks your ants onto
a rival's road, which leads to their cache and puts your paint over theirs. High spread
stops your column doubling back on itself. recall is the reset: it abandons a dead road
and lets it fade before you launch somewhere else.
```

**User message** = the seat's `PLAYER_PROMPT` text, then a blank line, then the seat's view JSON
(§Server). The prompt text is never echoed into the replay (only `policy_kind`).

**Champion #1 — `hive-pathwright` (owner daveey), `PLAYER_PROMPT`:**

```
Build one road at a time and keep it alive.
Open wide and close fast: for the first two turns run scouts near 60 with trail_gain
under 30, because you have no road yet and a strong road to nowhere is worse than no
road. The moment a food cache appears in your sources list, invert: scouts 12,
trail_gain 85, lay_food 90, spread 30, focus on the block that cache sits in with
focus_weight 80. A column that is fed keeps itself fed - every laden ant reinforces the
same trail, and the half-life does the rest.
Watch delivered_last_turn like a fuel gauge. If it is climbing, change nothing; a
doctrine you keep for three turns is worth more than three clever doctrines, because
trails take turns to build and one turn to lose. If it drops by more than a third in one
turn your cache is out: do not keep pumping. Set recall true for exactly one turn, then
relaunch with scouts 50, trail_gain 25 and focus null. Never set recall two turns running.
Keep lay_home at 55 or above whenever your ants are working more than 25 cells out.
Ants beyond 12 cells find the nest ONLY by the home trail, and a colony with a strong
food road and a rotten home road drops its harvest in the grass.
Poach at 15 as a standing habit, never more than 40. It is cheap directional information:
your ants drift onto whatever road exists nearby, and any road nearby leads to food. Raise
it only when your own sources list has been empty for two turns.
Twice per match a big cache lands dead centre. When the scoreboard shows every colony
gaining fast at once, that is it: focus the centre block with focus_weight 90 and
trail_gain 90 and take your share while it lasts.
```

**Champion #2 — `hive-swarmraid` (owner daveey-1,
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`:**

```
Let the others find the food. Take it off their road.
Run poach high - 60 to 85 - almost the whole match. Your ants do not need to find
caches; they need to find ROADS, and a rival's food trail is a signed arrow pointing at
a cache with a queue already on it. Every unit you lift there is a unit they do not
score, and the scoring is a share, so it counts twice.
Read the rival plane. Where your trails.rival grid shows a digit of 5 or more you are
standing on somebody's highway - focus that block with focus_weight 75 and push
trail_gain to 70 so your own ants pile onto the same lane and your paint goes over
theirs. Where the rival grid is all dots you are blind, and blind is the one thing you
cannot afford: hold scouts at 35 or above so there is always fresh rival paint in your
readings.
Keep spread high, 60 to 75. A raiding column that follows itself gets stuck behind its
own traffic; you want a wide front that crosses more of the enemy's lanes.
Keep lay_food moderate, around 55, and lay_home high, around 75. Your ants are usually
working far from home on somebody else's ground, so the road back is the fragile part.
Contest the centre without exception. At the two bonanzas, focus the centre block,
focus_weight 95, poach 40, trail_gain 80 - the centre needs no scouting and every colony
will be there, so it is the cheapest raid on the board.
Use recall only if your scoreboard position has been last for four straight turns; then
recall one turn, come back with scouts 70 and focus null, and start hunting roads again.
```

### Scripted baselines

Both emit the identical doctrine JSON on the same 10 s cadence, so their output is legal by
construction and directly comparable to an LLM's; both are pure functions of the seat's view (plus
the episode seed), which is what makes the bounded-orders test in §Tests meaningful.

- **`marcher`** — the certification player, the default, and the stronger of the two. Turns 0–2:
  `{scouts: 55, trail_gain: 25, poach: 10, spread: 55, lay_food: 70, lay_home: 55, recall: false,
  focus: null, focus_weight: 0}`. From turn 3 on: if the view lists at least one known source with
  `amount_seen > 0`, pick the one maximising `amount_seen - 2 * blockDistance(nest_block, block)` and
  emit `{scouts: 15, trail_gain: 78, poach: 12, spread: 32, lay_food: 88, lay_home: 52,
  recall: false, focus: <that block>, focus_weight: 70}`; otherwise emit
  `{scouts: 60, trail_gain: 25, poach: 25, spread: 65, lay_food: 55, lay_home: 60, recall: false,
  focus: <the block one step from nest_block toward the field centre>, focus_weight: 40}`. If
  `delivered_last_turn == 0` for two consecutive turns *and* the previous turn had a focus, emit
  `recall: true` once. `note` is a fixed template ("marcher: <mode>"), `say` is `""`.
- **`driftling`** — the second filler, deliberately weaker and different in shape so the ladder has a
  spread. Every turn, unconditionally: `{scouts: 70, trail_gain: 25, poach: 45, spread: 70,
  lay_food: 40, lay_home: 60, recall: false, focus: null, focus_weight: 0}`. It explores forever,
  builds only weak roads, and finds food by luck and by wandering onto other colonies' paint.

---

## Sim module

`src/hive/sim.nim` is paintbot's `src/ctf/sim.nim` with the CTF rule surface removed and the foraging
rules put in its place. What is kept, what is dropped, and what is new:

**Kept from paintbot, by path:**

- `src/ctf/sim_types.nim` → `src/hive/types.nim` — `TargetFps` / `ReplayFps` = 24,
  `PlaybackSpeeds = [1,2,3,4,8,16]` (`src/ctf/sim_types.nim:294,353,354`), the map-global install
  pattern, and the **flatty wire types whose field order is sacred** (paintbot's `AGENTS.md` rule; it
  still holds — the live `/global` broadcast is flatty-encoded). `GameVersion` is kept as the rules
  gate and starts at `"1"` for hive (paintbot's GV43 history does not travel; the prepend-only
  `GVnn (short rule name): HEADLINE` changelog-comment convention does).
  **Dropped:** the whole continuous-motion constant family (`MotionScale`, `Accel`, `FrictionNum`,
  `MaxSpeed`, `StopThreshold`, `PlayerHalf`, `PlayerBouncePct`, `MovementSlideMaxScan`,
  `src/ctf/sim_types.nim:337-354`) — *deviation from paintbot, deliberate:* a pheromone field is a
  lattice, ants step cell to cell, and an integer lattice is what makes the native and emscripten
  builds agree bit-for-bit with no float anywhere. `MapWidth`/`MapHeight` become
  `fieldCols * cellPx` / `fieldRows * cellPx` = 1280 × 704.
- `src/ctf/arena.nim` → `src/hive/field.nim` — the `mapSpec`-style loader, the `ArenaShape`
  rect/disc/polygon stamping, the mask bake, the integer even-odd `pointInPolygon` with its
  STRICT-STRADDLE convention, and the process-global install. **Dropped:** the procedural generator,
  the validators, `mapDiagnostics`, `src/ctf/map_pool.nim`, `src/ctf/mapgen_styles.nim` and the whole
  `mapSize`/`mapSymmetry`/`mapEndzone` knob family. *Deviation from paintbot, deliberate:* hive ships
  **one authored field**, because four-way mirror fairness plus a hand-tuned distribution of rock
  (enough to make trails follow corridors, not so much that the meadow fragments) is not something a
  seeded draw gives you. Field variety is §Out of scope (v1).
- `src/ctf/sim_state.nim` → `src/hive/state.nim` — logging, the `gameHash` state digest, the event
  buffer, spawn placement. `src/ctf/sim_config.nim` → `src/hive/config.nim` — the `GameConfig`
  lifecycle and `configJson()`. `src/ctf/roster.nim` → `src/hive/roster.nim` — join/auth/slots/tokens.
  `src/ctf/events.nim` → `src/hive/events.nim` (the `SimEventKind` → JSON-key discipline and the
  trailing summary row of `eventsJsonl`, `src/ctf/events.nim:64-93`, kept verbatim in shape).
  `src/ctf/labels.nim`, `src/ctf/broadcast.nim` and `src/ctf/global.nim`'s sprite-protocol broadcast
  layer are kept (the live `/global` stream and the viewer both ride them, including the
  `BroadcastChromeSpriteId` JSON-chrome channel that is the only chrome path surviving a hosted
  replay, `src/ctf/server.nim:1890-1905`); the CTF-specific art in `global.nim` is replaced (§Viewer).
- `src/ctf/replay_runtime.nim` + `src/ctf/replays.nim` → `src/hive/replay.nim` — the
  `parseReplayBytes` / `initReplayRuntime` / `advanceReplayFrame(seekTicks, commands)` shape that the
  wasm viewer drives (`replay-viewer/ctf_replay.nim:46-113`), including the hash-mismatch surface
  (`ctf_mismatch_tick` → `#mmwarn`). The bytes it reads are JSON, not `COWLDCTF` (§Server).
- `src/ctf.nim` → `src/hive.nim` — the entrypoint, **including the rule that seed randomisation
  happens before `config.update`** so every seed-derived draw follows the final seed
  (`src/ctf.nim:69-91`, `seedPinned` / `stripUnpinnedSeed` / `randomSeed` kept verbatim).

**Dropped entirely:** guns, hitscan, aim, aim jitter, the vision cone and the shadowcast FOV,
grenades, the barrage, med kits, shields, the plasma arc, paint puddles, spray cans, lives / hit
points / respawn, perks, handicaps, achievements, shouts, teams-as-sides, the map editor
(`tools/map_editor*`), the `arena/` WIT component bindings, `caos/` and `caos-tools/`. Hive has no
combat and no fog cone; what survives the fork is the loop, the field bake, the replay, the digest
discipline, the broadcast layer and the chrome.

**New:** `src/hive/pheromones.nim` — the eight `uint16` planes, deposit, saturate, decay, block
downsample; `src/hive/ants.nim` — the kernel, activation striping, release; `src/hive/sources.nim` —
orbit and bonanza spawning, depletion, expiry, the harvest buckets; `src/hive/rules.nim` — the turn
clock, delivery, raids, the trail-war scan, the invariant guards and the score;
`src/hive/doctrine.nim` — the doctrine schema, tolerant parsing, repair, and the coefficient table;
`src/hive/llm.nim` — bullwhip's client; `src/hive/baselines.nim` — `marcher` and `driftling`;
`src/hive/replay.nim` — the JSON replay writer/reader.

**The field file.** `data/meadow.fieldspec.json`, loaded by `fieldPath: "meadow"`, is authored (not
generated) and pinned verbatim into every replay's `field` key, exactly as paintbot pins `mapSpec`:

```json
{"name": "meadow", "cols": 160, "rows": 88, "cell_px": 8,
 "rock": [{"kind": "rect", "cx": 46, "cy": 20, "w": 8, "h": 26},
          {"kind": "disc", "cx": 72, "cy": 30, "r": 6},
          {"kind": "polygon", "points": [[30,52],[44,50],[46,60],[28,62]]}, … ],
 "nests": [{"id": "N0", "cell": [16, 12],  "colour": "#f2c14e", "alias": "Amber"},
           {"id": "N1", "cell": [143, 12], "colour": "#4ecdc4", "alias": "Teal"},
           {"id": "N2", "cell": [16, 75],  "colour": "#9fd356", "alias": "Lime"},
           {"id": "N3", "cell": [143, 75], "colour": "#e26db5", "alias": "Magenta"}],
 "nest_radius": 2,
 "spawn_quadrant": [4, 4, 79, 43],
 "bonanza_cells": [[79,43],[80,43],[79,44],[80,44]]}
```

Only rock shapes in the top-left quadrant are authored; the loader **generates the other three
quadrants by mirroring**, so the symmetry cannot drift. A test asserts the baked mask is invariant
under both mirrors, that every nest pad and every bonanza cell is free floor, and that the free floor
is a single 4-connected component.

**Randomness.** One PCG32 stream seeded from the episode seed, integer arithmetic only, used for
exactly four things: the seat→nest permutation, orbit spawn cells, the kernel's `rnd(0..alphaNoise-1)`
tie-noise, and the release-bearing draw. Everything else is deterministic. The stream is advanced in a
fixed order (seat permutation once at init, then per tick: sources, then ants in ant order), so the
draw sequence is a function of the seed and the doctrines alone.

**State digest.** `hiveStateDigest()` returns an FNV-1a u32 over the raw bytes of: every ant's
`(cx, cy, heading, carrying, carried_from)`, every live source's `(id, cx, cy, amount)`, the four
`delivered` counters, the PCG state, the tick — **and all eight pheromone planes in full**. It is
paintbot's `gameHash` idea widened to the whole state, it goes into every keyframe, and it is the
cross-build equality check that lets the wasm viewer prove it re-derived the same match (paintbot
already surfaces a mismatch as the `#mmwarn` line — kept). Hashing 220 KiB every 24 ticks is 44 MB
per episode, well under a tenth of a second.

**Determinism contract (the inviolable property).** Same seed + same resolved doctrine stream ⇒ same
digest at every keyframe, in the native build *and* in the emscripten build. It holds because the
whole step is integer. **No `sin`, `cos`, `tan`, `atan`, `exp`, `ln`, `pow`, `sqrt`, `hypot`, `fmod`
or float arithmetic of any kind appears in the sim step**, and `-ffast-math` is banned; a source-grep
test enforces both (§Tests).

---

## Server, player, protocol

`src/hive/server.nim` is a fork of `src/ctf/server.nim`: the same mummy HTTP/WebSocket server
(`newServer(httpHandler, websocketHandler, workerThreads = 4)`, `src/ctf/server.nim:1333`), the same
routes (`GET /healthz` — `src/ctf/server.nim:60`; the player WebSocket at `/player?slot=N&token=T`;
the spectator `/global`; **real browser pages on `GET /client/player` and `GET /client/global`,
registered before any catch-all asset route and neither of them opening the player socket** — the
episode runner probes both before starting player pods, and a 404 there is a
`game_contract_violation` (playbook gotcha, lantern 0.1.1); and in replay mode `/replay-data` +
`/client/replay`), the same 403 on a bad slot/token and 409 on a duplicate connection, the same
`bitworld/runtime` `RuntimeConfig` contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`,
`COGAME_SAVE_REPLAY_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`,
`COGAME_METRICS_URI` — the last two `file://`-only and loudly rejected otherwise), the same **write
order at the end of an episode** (broadcast `done` to every seat with a 3.0 s per-seat deadline →
write the replay → `writeResults`, `src/ctf/server.nim:1940-1960`), and the same pre-listen field bake
so a viewer's first frame is instant. `/healthz` and `/global` keep answering for a **20 s shutdown
grace** after artifacts are written, then the process exits — the cert runner pings `/global` with a
2 s deadline *after* the player pods start and a short episode would otherwise already be gone
(playbook gotcha, lantern 0.1.3).

**Player handshake (the only thing a player container must do).** On connect the player sends exactly
one text frame:

```json
{"type": "register", "prompt": "<strategy text or empty>",
 "scripted": "marcher" | "driftling" | null,
 "policy": "<free label, <=48 runes>"}
```

`src/hive_player.nim` reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED` and
`PLAYER_POLICY_LABEL`, sends that frame, then receives until `{"done": true, …}` and exits 0. A seat
that never registers, or registers with neither field, is treated as `scripted: "marcher"`.
`PLAYER_SCRIPTED` parsing follows bullwhip's `parseScriptKind`: `marcher`/`1`/`true`/`yes` → marcher,
`driftling` → driftling, anything else → none.

**Per turn the server pushes to each seat** (informational — the seat is not required to answer;
decisions are made server-side):

```json
{"type": "turn", "turn": 7, "tick": 1680, "colony": "Amber",
 "view": { … }, "doctrine_source": "llm"}
```

and at the end `{"done": true, "result": { …the results document… }}`, then close.

### The per-seat view (exactly what is visible, and what is hidden)

This object is both the `view` in the turn frame and the tail of the LLM user message. All
coordinates are integers. Blocks are 8 × 8 cells, so the block grid is **20 × 11**; block `(bx, by)`
covers cells `cx ∈ [8bx, 8bx+7]`, `cy ∈ [8by, 8by+7]`, and its centre cell is `(8bx+4, 8by+4)`.

```json
{"turn": 7, "of": 20, "tick": 1680, "ticks_left": 3120, "seconds_left": 130.0,
 "you": {"colony": "Amber", "colour": "#f2c14e", "nest": [16, 12], "nest_block": [2, 1],
         "ants": 24, "carrying": 6, "scouts": 4, "at_nest": 3,
         "delivered": 118, "delivered_last_turn": 21, "mean_range_cells": 27,
         "last_doctrine": { …the resolved doctrine you played last turn, or null on turn 0… }},
 "field": {"cols": 160, "rows": 88, "cell_px": 8, "blocks": [20, 11], "block_cells": 8,
           "rock": ["....................", "....##..............", … 11 rows of 20 chars … ]},
 "trails": {"food":  ["00000000000000000000", "00012000000000000000", … 11 rows … ],
            "home":  ["01100000000000000000", "02341000000000000000", … 11 rows … ],
            "rival": ["....................", "...3................", … 11 rows … ]},
 "sources": [{"id": 12, "block": [9, 5], "cell": [76, 43], "amount_seen": 41,
              "seen_turn": 6, "near_nest": null},
             {"id": 9, "block": [3, 2], "cell": [28, 19], "amount_seen": 0,
              "seen_turn": 4, "near_nest": "Amber"}],
 "contacts": [{"colony": "Teal", "blocks": [[9,5],[10,5]], "ants": 7}],
 "scoreboard": [{"colony": "Amber", "delivered": 118}, {"colony": "Teal", "delivered": 96},
                {"colony": "Lime", "delivered": 71}, {"colony": "Magenta", "delivered": 64}],
 "sources_live_total": 9}
```

- `field.rock[by][bx]` is `#` when more than half the block's cells are rock, else `.`.
- `trails.food[by][bx]` and `trails.home[by][bx]` are digits `0`–`9`:
  `min(9, (meanBlockValue * 10) div (pheromoneMax + 1))` over **your own** planes.
- `trails.rival[by][bx]` is the same digit computed as `max` over the other three colonies' `F`
  planes, **but only for blocks where `sensed[you][block] >= turn - 1`** — that is, blocks one of your
  own ants stood in during the previous turn. Every other block is `.`, meaning *no reading*, not
  *no trail*. This is the stigmergic constraint made literal: you learn about rivals by walking where
  they walked.
- `sources[]` lists only sources at least one of your ants has been within one cell of. `amount_seen`
  and `seen_turn` are **as of the last time you saw it**, never live — a cache you scouted five turns
  ago may already be empty. `near_nest` names a colony when the source is within `raidRadius = 20`
  cells of that colony's nest centre, else `null`.
- `contacts[]` lists, per rival colony, the blocks where your ants shared a cell with theirs during
  the previous turn and how many of your ants were involved.
- `scoreboard[]` is **public**: every nest counter is visible to everyone, always, in a fixed
  alias-sorted order. Deliveries are physical and loud; the idea's pulsing counters are diegetic.

**Visible to a seat:** everything above — the full static rock map, its own two pheromone planes at
block resolution, rival food-trail readings where its own ants have recently been, its own aggregate
colony state, sources it has personally discovered (at last-seen amounts), rival contact blocks, the
public scoreboard, and the clock.

**Hidden from a seat:** the positions, headings and carrying state of **individual ants — its own
included** (the policy is never given a god's-eye per-ant readout; it cannot micro-manage, which is
the point of the game); rival ant positions; rival colonies' pheromone planes outside sensed blocks;
rival colonies' `H` planes entirely; the live amount of any source it has not just seen; the existence
of any source it has never seen; every rival's doctrine, `note`, `say` and prompt; the seat→nest
permutation for any other seat; the episode seed; and the future.

**Hidden from everyone, both in-game name spaces:** the real player names behind the colony aliases.
Aliases (`Amber`, `Teal`, `Lime`, `Magenta`) are the only names any prompt, view or event body
contains; real policy names exist only in `replay.names.players`, `results.names` and the viewer's
scorebug plates. That is the two-name-space pin, and the per-episode seat→nest permutation is the
idea's "colony identities are anonymized per episode".

### Doctrine schema and character caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"scouts": 15, "trail_gain": 78, "poach": 12, "spread": 32,
 "lay_food": 88, "lay_home": 52, "recall": false,
 "focus": [9, 5], "focus_weight": 70,
 "note": "cache at (76,43) is fat and Teal has not found it; pump the road",
 "say": "west road, full pump"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `scouts` | int | 0…100 | missing/non-numeric → previous turn's value, or 40 on turn 0; out of range → clamped |
| `trail_gain` | int | 0…100 | as `scouts`, default 50 |
| `poach` | int | 0…100 | as `scouts`, default 15 |
| `spread` | int | 0…100 | as `scouts`, default 40 |
| `lay_food` | int | 0…100 | as `scouts`, default 70 |
| `lay_home` | int | 0…100 | as `scouts`, default 50 |
| `recall` | bool | `true`/`false`; accepts `"true"`/`"false"`/`0`/`1` | → `false`. Forced `false` if the previous turn's doctrine had `recall: true` (recall may not run two turns in a row) |
| `focus` | `[int,int]` or null | `bx ∈ 0…19`, `by ∈ 0…10` | out of range → clamped; non-array, wrong length, or non-numeric → `null` |
| `focus_weight` | int | 0…100 | as `scouts`, default 0; forced 0 when `focus` is `null` |
| `note` | string | **≤ 140 runes** | truncated to 140 runes |
| `say` | string | **≤ 32 runes** | truncated to 32 runes |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and `register.prompt` **≤ 4000 runes** at the
transport (an over-long prompt is truncated, not rejected) — the prompt is never written to the
replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes.** In Nim that means walking the
string with `runeSubStr` / `toRunes` and never slicing a `string` by byte index on any path that
reaches the replay. A byte-truncated multi-byte character is exactly the bug that makes replay bytes
render in a browser but fail a strict JSON parser (playbook gotcha), and §Tests pins it with a 4-byte
emoji sitting on the 32nd rune of a `say`.

**Parsing is tolerant** (bullwhip's `extractJsonObject` shape): strip markdown fences, take the
outermost balanced `{…}` if the model prefixed prose, accept numeric strings for any integer field,
accept `focus` as `{"bx":…,"by":…}`, accept percentages written as `"70%"`. Only when no object
containing at least one recognised doctrine key can be recovered does the retry, then the fallback,
fire. **The resolved, repaired, clamped doctrine is what is installed and what is recorded** — the
replay never depends on re-running the repair.

### Results document (closed schema — must equal the manifest `results_schema` key-for-key)

All per-seat arrays are length 4 in **slot** order (not nest order).

```json
{"names": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
 "aliases": ["Amber", "Magenta", "Teal", "Lime"],
 "colours": ["#f2c14e", "#e26db5", "#4ecdc4", "#9fd356"],
 "nests": [[16,12], [143,75], [143,12], [16,75]],
 "policy_kinds": ["llm", "llm", "scripted", "scripted"],
 "scores": [0.31692, 0.28154, 0.22231, 0.17923],
 "win": [true, false, false, false],
 "delivered": [412, 366, 289, 233],
 "harvested": [415, 371, 292, 236],
 "raided_units": [18, 74, 5, 0],
 "raided_from_you": [61, 12, 20, 4],
 "peak_food_trail": [3980, 2440, 4000, 1180],
 "ants": [24, 24, 24, 24],
 "recalls": [1, 0, 2, 0],
 "turns_llm": [20, 19, 0, 0],
 "fallback_turns": [0, 1, 0, 0],
 "fallback_causes": [{"timeout": 0, "parse_error": 0, "transport_error": 0,
                      "no_credentials": 0, "budget_guard": 0}, … 4 … ],
 "total_delivered": 1300,
 "sources_spawned": 76,
 "reason": "complete",
 "end_rule": "full_time",
 "winner": 0,
 "final_tick": 4800,
 "final_turn": 20,
 "seed": 679961}
```

`winner` is a slot index `0…3` or `null` (tied maximum). Adding or removing a key here means editing
`coworld_manifest_template.json`'s `results_schema` and `tools/ci/docker_smoke.sh`'s expectations in
the same commit.

### Replay bytes (self-sufficient, strict UTF-8 JSON)

*Deviation from paintbot, deliberate:* paintbot writes the binary `COWLDCTF` format
(`src/ctf/replays.nim:119` — a JSON config brace-matched from the first `{`, then recorded inputs).
Hive writes **UTF-8 JSON**, following bullwhip's `bullwhip.replay.v1`, because SPEC §Definition of
done check 4 fetches the replay from S3 and requires valid UTF-8 JSON with a matching `protocol` and
a legal `results.reason`, and the shared `tools/ci/docker_smoke.sh` defaults to
`SMOKE_REQUIRE_REPLAY_JSON=1`.

The **input log is the doctrine stream** — 20 turns × 4 seats of nine integers and a block — because
the ant kernel is a pure function of `(seed, field, doctrines)`. That is why hive's replay is small
and why the viewer can re-derive the pheromone field, which no keyframe could carry.

```json
{"protocol": "hive.replay.v1",
 "format_version": 1,
 "game_version": "1",
 "seed": 679961,
 "config": { …the fully resolved game config, tokens excluded: num_agents, antsPerColony,
             episodeTicks, turnTicks, antStepTicks, cellPx, pheromoneMax, pheromoneFloor,
             pheromoneDecayNum, decayPeriodTicks, nestSenseCells, maxOrbits,
             sourceSpawnPeriod, sourceAmount, sourceLifeTicks, minNestClearance,
             bonanzaTicks, bonanzaAmount, bonanzaLifeTicks, raidRadius,
             trailWarThreshold, turnBudgetSeconds, wallClockBudgetSeconds,
             playerConnectTimeoutSeconds, fieldPath, players:[{"name":…}] … },
 "field": { …data/meadow.fieldspec.json inlined verbatim, pre-mirroring… },
 "seat_nests": [0, 3, 1, 2],
 "names": {"players": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
           "aliases": ["Amber", "Magenta", "Teal", "Lime"],
           "policy_kinds": ["llm", "llm", "scripted", "scripted"],
           "colours": ["#f2c14e", "#e26db5", "#4ecdc4", "#9fd356"]},
 "ticks_per_second": 24, "turn_ticks": 240, "tick_count": 4800,
 "doctrines": [{"turn": 0, "seat": 0, "source": "llm", "latency_ms": 4120,
                "scouts": 55, "trail_gain": 25, "poach": 10, "spread": 55,
                "lay_food": 70, "lay_home": 55, "recall": false,
                "focus": null, "focus_weight": 0,
                "note": "no road yet; open wide", "say": "spread out"}, … 80 … ],
 "keyframes": [{"t": 0, "d": 2947483111, "del": [0,0,0,0], "car": [0,0,0,0],
                "src": [[3,76,43,60], … ]}, … every 24 ticks … ],
 "ants_b64": "<base64 of keyframeCount x 96 x 3 bytes: (cx u8, cy u8, state u8) per ant
              per keyframe, ants in global index order>",
 "events": [ … the vocabulary below … ],
 "results": { …the results document verbatim… }}
```

`seed` + `field` + `seat_nests` + `doctrines` + the integer sim reproduce the episode exactly;
`keyframes` and `ants_b64` carry the per-second state and its digest `d` so the viewer (and the tests,
and a human reading the JSON) can verify the re-derivation and read the match without running wasm at
all. Ant state codes: `0 = searching forager`, `1 = searching scout`, `2 = carrying`, `3 = at nest,
held by recall`. `src` rows are `[id, cx, cy, amount]` for every live source.

**Size:** doctrines ≈ 20 KB, keyframes ≈ 30 KB, `ants_b64` = 201 × 96 × 3 = 57 888 B → 77 KB base64,
events ≈ 110 KB (the high-frequency `deliver` and `harvest` records use short keys for exactly this
reason). Total ≈ 240 KB — comfortably small.

**Everything the viewer needs is in these bytes** (names, colours, policy kinds, config, field
geometry, seat→nest permutation, doctrine stream, per-second states, events, seed, results). The
viewer contacts nothing but the S3 URL it was given.

**Event vocabulary** (every record carries `t` = tick; `turn` where meaningful):

| `type` | Fields |
|---|---|
| `match_start` | `t`, `seed`, `field` (name), `colonies` (`alias`, `colour`, `nest`, `seat`), `ants_per_colony`, `episode_ticks` |
| `turn_start` | `t`, `turn`, `delivered` (4), `sources_live` |
| `doctrine` | `t`, `turn`, `seat`, `colony`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `scouts`, `trail_gain`, `poach`, `spread`, `lay_food`, `lay_home`, `recall`, `focus`, `focus_weight`, `note`, `say` |
| `fallback` | `t`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `t`, `turn`, `remaining_s` |
| `recall` | `t`, `turn`, `colony`, `ants_recalled` |
| `source_spawn` | `t`, `kind` (`orbit`\|`bonanza`), `orbit`, `sources` (`id`, `cell`, `amount`), `near` (per source: the nearest colony alias or null) |
| `source_gone` | `t`, `source`, `cell`, `cause` (`depleted`\|`expired`), `taken` (per-colony units) |
| `harvest` | `t`, `s` (source id), `c` (seat), `u` (units in the last 24 ticks) |
| `deliver` | `t`, `c` (seat), `n` (that colony's running total), `s` (source id), `r` (raid, 0\|1) |
| `raid` | `t`, `colony`, `victim`, `source`, `units` (running total lifted from within the victim's `raidRadius`) |
| `trail_war` | `t`, `block`, `colonies`, `strengths` |
| `end` | `t`, `reason`, `end_rule`, `delivered`, `scores`, `winner` |

`doctrine`, `deliver`, `raid`, `trail_war` and `fallback` are the records the phase-60 verifier reads
to judge "the champion seats doing the thing the game is about": a champion seat's `doctrine` events
must carry `source: "llm"` with varying parameter values and real `note` content, not all fallbacks.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` (forked from
paintbot's, `chmod +x` — `coworld build` hard-requires `os.X_OK` — keeping paintbot's safety checks
that the target is absolute, named `static-replay-viewer` and inside the repo, and that
`index.html` exists at the end) builds `Dockerfile.replay-viewer`'s `replay-viewer-builder` stage —
`emscripten/emsdk:4.0.15` + nimby 0.1.27 pinned by sha256, `nimby use 2.2.4`,
`nimby --global sync nimby.lock` — which compiles **the same Nim sim** as
`nim c -d:emscripten replay-viewer/hive_replay.nim`, then copies
`/workspace/hive/replay-viewer/dist/.` into the bundle. The game server still serves `/client/replay`
for local viewing off the identical `dist`. Nothing but S3 is contacted at view time.

**How playback works.** `replay-viewer/hive_replay.nim` is paintbot's `replay-viewer/ctf_replay.nim`
with hive's parser: the same exported surface (`hive_load_replay`, `hive_input`, `hive_frame`,
`hive_packet_ptr`, `hive_packet_len`, `hive_mismatch_tick`, `hive_error_ptr/len`,
`hive_stage_ptr/len`), the same `stampStage` progress-note discipline, the same
`-s ABORTING_MALLOC=1` link and the same `emscripten_exit_with_live_runtime()` epilogue skip
(`replay-viewer/ctf_replay.nim:14-34,152-165`) — all four of those exist because of bugs paintbot
already paid for. The module **re-runs the integer sim** from the doctrine stream, so the pheromone
field is re-derived, not transported. Forward playback is one tick per step. A **backward seek**
restarts from the nearest in-memory turn snapshot (§The game, step 14) and replays at most 240 ticks
— under 15 ms — instead of paintbot's replay-from-zero. Every keyframe's digest is compared against
the recorded `d`; the first mismatch lights `#mmwarn` and playback continues (paintbot's
`mismatchQuit = false` default, kept).

**Files in the bundle** (each must return 200 with a non-trivial size for phase-60 check 8(b)):
`index.html`, `static_replay.js`, `static_replay_worker.js`, `chrome_common.js`, `wire_constants.js`,
`hive_replay.js`, `hive_replay.wasm`, `hive_replay.data`, `art/meadow_floor.jpg`, `art/rock.png`,
`art/nest_amber.png`, `art/nest_teal.png`, `art/nest_lime.png`, `art/nest_magenta.png`,
`art/food_cache.png`, `art/ant.png`, `art/ant_laden.png`, `font.ttf`.

**Chrome kept verbatim.** `client/chrome_common.js` is copied unchanged. `client/replay_broadcast.html`
keeps its CSS block and its markup ids exactly: `#viewport`, `#stage`, `#board`, `#lightpool`,
`#grain`, `#chrome`, `#scorebug`, `#plates-l`, `#plates-r`, `#clock`, `#clock-time`, `#clock-caption`,
`#ffwd-mini`, `#viewpanel`, `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-slider`,
`#zoom-in`, `#zoom-read`, `#mmwarn`, `#bannerlane`, `#killfeed`, `#transport`, `#btn-restart`,
`#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`,
`#ffwd-chip`, `#win-chip`, `#tick-clock`, `#speedchips`, `#scrub`, `#momentum`, `#scrub-fill`,
`#lulls`, `#scrub-win`, `#scrub-head`, `#endcard`, `#ec-headline`, `#ec-wincond`, `#ec-how`,
`#ec-teams`, `#ec-replay`, `#status`, and the `--hudscale` / `--topband` / `--band` / `.tiny`
fixed-point relayout loop (`client/replay_broadcast.html:4085-4133`) unchanged. **The four-colony
scorebug needs no new layout**: `ensureScorebug()`'s 3–4 team path already puts two `.plate`s per side
on one row (`client/replay_broadcast.html:177-190,1487-1494`), and `.plate .team-name`'s
`flex: 0 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis`
(`client/replay_broadcast.html:201-219`) is already the fix for the "names collapse to …" gotcha; hive
keeps it and adds `min-width: 3.2em` so a name never shrinks below three characters at 360 px.
The pre-load locker-room curtain (`#lockerroom`, `#lk-art`, `#lk-bg`, `#lk-sprites`, `#lk-cap`) is
kept with hive's own plate. **Added markup, and nothing else:** `#nestbug` (four delivery counters),
`#doctrinebar` (the four colonies' current `scouts/trail/poach` chips), `#warflash` (the trail-war
overlay) and `#cachebar` (live caches remaining). Removed: the CTF flag icons, the lives line, the
squad pips, the first-person PiP (`#fpv…`) and the kill plumbing, none of which has a counterpart
here.

`replay-viewer/static_replay.js` keeps paintbot's OffscreenCanvas-Worker shell verbatim (the
`createCore` / `start` / `stop` / `advance` / `resize` / transform-and-minimap message protocol with
`static_replay_worker.js`, the `data-replay-loaded` and `data-replay-mismatch-tick` attributes and
`showFailure`), with two changes: the loader hands the JSON replay to the wasm module instead of the
binary one, and **bullwhip's `coworld-replay` postMessage bridge is added verbatim** —
`tell("loading")` on script entry, `tell("error", msg)` on failure, and `tell("ready")` inside a
double `requestAnimationFrame` after the first drawn frame
(`/workspace/starters/cogame-bullwhip/replay-viewer/static_replay.js:20-33,120-124`). SPEC check 8(c)
greps the served JS for exactly that bridge. The fetch is bounded by a 20 s `AbortController` with a
Retry button, also from bullwhip.

**Split of responsibilities.** The wasm canvas draws the world (floor, rock, nests, pheromone glow,
ants, caches, war flashes); the DOM chrome draws the scorebug, nest counters, doctrine chips, event
feed, transport and warnings. DOM text is set with `textContent` only (names are player-controlled
data) and stays crisp at any zoom — which is what makes 360 px legibility achievable.

**Readouts** (the idea's replay plan, item for item):

1. **Pheromone fields glow as two decaying overlay colours.** Every frame the wasm module draws, per
   colony, two additive layers over the floor: the **food trail** in the colony's hue at
   `alpha = min(0.55, F/4000 * 0.55)` with a 1-cell bloom, and the **home trail** in the same hue
   desaturated 60 % and darkened, at `alpha = min(0.22, H/4000 * 0.22)`, drawn *under* the food layer.
   Four hues × two layers, all re-derived from the sim, all visibly fading between deliveries. This is
   the headline: each colony's strategy is literally painted on the ground, and you can watch a road
   brighten as it pays and dim as it dies.
2. **Ant flows read like traffic.** Each ant is a 3 px dot in its colony hue; a laden ant is 4 px with
   a white food pip and a slightly brighter core. At 24 fps with 96 ants on staggered activation, the
   columns read as continuous flow, and a scout breaking off a road is visible as a dot leaving the
   glow.
3. **Nest counters pulsing on every delivery.** `#nestbug`: four counters in colony colours showing
   `delivered`. Every `deliver` event triggers a 6-frame scale bump on that counter plus a one-frame
   ring at the nest on the board. During a busy road that is a heartbeat, which is exactly the idea's
   ask.
4. **Trail wars are the highlight reel.** On a `trail_war` event the contested block gets a hatched
   two-colour overlay in `#warflash` for 48 frames and a `#bannerlane` banner
   (`TRAIL WAR — Amber vs Teal over block 9,5`). On a `raid` event: a banner
   (`RAID — Magenta lifts 8 from Amber's doorstep`), the victim's nest counter flashing red for 12
   frames, and a `#killfeed` line. These two events are what a highlight-reel scrub jumps between —
   both are marked on the scrub bar.
5. **Caches.** A live source is a painted food-cache sprite scaled by `amount / spawn_amount`; a
   `source_spawn` pops it in with a 12-frame ring (bonanzas get a bigger gold ring and a
   `BONANZA — CENTRE` banner); a `source_gone` collapses it with a puff, grey for `expired`, white for
   `depleted`.
6. **Time-compressed.** Default playback is **4×** on the inherited `#speedchips`
   (`PlaybackSpeeds = [1,2,3,4,8,16]`), so a 200 s match watches in 50 s. Spans of 240 ticks with no
   `deliver`, no `source_spawn` and no `trail_war` are registered as lull spans in the inherited
   `skipLulls` / `lullSpans` / `#btn-skip` / `#ffwd-chip` machinery and run at 16× with
   `#clock-caption` reading `FORAGING — 16×`. `#btn-skip` turns it off.
7. **Scorebug** (`#scorebug`, always on): four plates —
   `▮ daveey · Amber 412` / `▮ Baseline (1) · Teal 289` on the left, `Lime 233 · Baseline (2) ▮` /
   `Magenta 366 · daveey-1 ▮` on the right — each with its colour chip, the leader's plate brightened,
   and `#clock-time` showing `MM:SS` remaining over `turn 7/20`. **Real player names live here and
   only here** (plus the endcard and the feed); the board itself labels nests `Amber`…`Magenta`.
8. **Doctrine feed** (`#killfeed`, plain language, last 6): `Amber → 15% scouts, trail 78, poach 12,
   focus block 9,5`, `Amber says "west road, full pump"`, `Magenta → RECALL`,
   `Teal falls back (timeout)`. Plus `#doctrinebar`: four always-visible chips showing each colony's
   current `scouts / trail / poach`, so a spectator can see a strategy change *before* the ground
   changes. This is where the LLM is visible playing.
9. **Transport** (verbatim): play/pause, back one tick, +5 s, jump to end, loop, lull-skip, spoilers,
   the speed chips, the scrubber with `#momentum` re-purposed to plot **all four delivered curves**
   across the match, `source_spawn` / `trail_war` / `raid` ticks marked on the scrub bar, the
   `#tick-clock` readout, the `#endcard` (`Amber wins — 412 of 1300 (31.7%)` with the four-row
   breakdown), and the `#mmwarn` digest-mismatch line.

**Art is real, not placeholder.** The floor is an authored painted meadow tile (`art/meadow_floor.jpg`,
seamless, cool green, subtly noisy so the pheromone glow reads against it); rock is a painted
grey-lichen tile masked to the baked rock shape; each nest is an authored painted mound sprite tinted
to its colony hue with a visible entrance; caches are painted seed piles in three fullness states;
ants are two authored 8 px sprites (`ant.png`, `ant_laden.png`) tinted per colony at draw time. All of
it is generated by committed scripts under `scripts/art/` the way paintbot generates its props. The
locker-room curtain plate is hive's own. Paintbot's `client/art/walls/wall_h.jpg` / `wall_v.jpg` are
reused verbatim for the field border. No solid-colour rectangles standing in for anything, no TODO
assets.

**Legible at 360 px** — the embedded featured-match iframe is ~360 px wide, so the composition is
checked at 360 px, not at desktop width. Paintbot's `--hudscale` (`clamp(0.5, boardW/760, 1.6)`) and
its `.tiny` class at `boardW <= 620` are inherited and do the heavy lifting. On top of that:
`.plate .team-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }`
so player names never collapse to "…" (playbook gotcha); a `@media (max-width: 640px)` rule collapses
`#nestbug` to four 8 px colour dots with the numeral beside them, hides `#doctrinebar` and
`#viewpanel` (minimap + zoom bar) and the speed-chip labels, and reduces the feed to two lines under
the board; the four scorebug plates drop the colour-word label and keep chip + number + name; banner
text is `font-size: clamp(11px, 3.4vw, 17px)` and never wraps to three lines. A static test asserts
the `.team-name` rule and the `640px` media block are present (§Tests).

---

## Packaging

- **Repo:** `Metta-AI/cogame-hive`, **public at creation** (public is a certification prerequisite —
  `source-resolves` 404s on private). Slug `hive`.
- **`compose.yaml`** — bullwhip's single-service shape (paintbot's two-image split does not survive
  the fork: the shared `tools/ci/docker_smoke.sh` runs the game and every player container from one
  image). The manifest's image placeholder is derived from the **compose service name**
  (`service hive` → `{{HIVE_IMAGE}}`) — `{{GAME_IMAGE}}` is not a thing (playbook gotcha, lantern
  0.1.0):

  ```yaml
  services:
    hive:
      image: coworld-hive:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — paintbot's/bullwhip's two-stage Nim build: `debian:bookworm-slim` + nimby 0.1.26
  pinned, `nimby use 2.2.4`, `nimby --global sync nimby.lock`, then two binaries —
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:hive src/hive.nim` and the same for
  `src/hive_player.nim`. Run stage `debian:bookworm-slim` with `ca-certificates` and `libcurl4`,
  copying `/bin/hive`, `/bin/hive-player`, `./data`, `./client`, `./*.json`. `CMD ["/bin/hive"]`.
- **`Dockerfile.replay-viewer`** — paintbot's, with the CTF asset copies replaced by hive's:
  `emscripten/emsdk:4.0.15`, nimby 0.1.27 (sha256-checked), `nim c -d:emscripten
  replay-viewer/hive_replay.nim`, `tools/gen_wire_constants.nim > replay-viewer/dist/wire_constants.js`,
  the `chrome_common.js` / `static_replay.js` / `static_replay_worker.js` / `font.ttf` copies, the
  marker `sed` that splices `<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->` and
  `<!-- BROADCAST_CORE -->` into `index.html`, the art copies, and the same `test -f` / `grep -q`
  assertion tail (adjusted to hive's file names, and extended with
  `grep -q 'coworld-replay' replay-viewer/dist/static_replay.js`).
- **`coworld_manifest_template.json`:**
  - `game.name` `hive`; `episode_timeout_minutes` **20**; `game.runnable.image` `{{HIVE_IMAGE}}`,
    `run` `["/bin/hive"]`, `source_url` `https://github.com/Metta-AI/cogame-hive/tree/main`;
    `game.owner` `daveey@softmax.com`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.config_schema`: `tokens`, `players` (4), `seed`, **`num_agents`** (integer, default **4**),
    `antsPerColony` (24), `episodeTicks` (4800), `turnTicks` (240), `antStepTicks` (2), `cellPx` (8),
    `pheromoneMax` (4000), `pheromoneFloor` (4), `pheromoneDecayNum` (248), `decayPeriodTicks` (8),
    `nestSenseCells` (12), `maxOrbits` (3), `sourceSpawnPeriod` (240), `sourceAmount` (60),
    `sourceLifeTicks` (1440), `minNestClearance` (14), `bonanzaTicks` (`[1200, 3600]`),
    `bonanzaAmount` (100), `bonanzaLifeTicks` (900), `raidRadius` (20), `trailWarThreshold` (800),
    `turnBudgetSeconds` (22), `wallClockBudgetSeconds` (660), `playerConnectTimeoutSeconds` (90),
    `fieldPath` (`"meadow"`), `showPlayerLabels` (true), `gameOverTicks` (96).
  - `game.results_schema`: exactly the closed key set in §Server, with `reason` enum
    `["complete","deadline","fault"]` and `end_rule` enum
    `["full_time","wall_clock","sim_fault","host_error"]`.
  - `game.protocols`: **both `player` and `global`**, each `{"type": "text", "value": "…"}` — `player`
    describing the `register` frame, the `turn` frames, the view schema and the `done` frame; `global`
    describing the `/global` spectator snapshot and the static replay bundle. Text form, not URIs
    (paintbot uses URIs; the playbook gotcha row requires text or the docs go missing on the coworld
    page).
  - `game.docs`: `readme` = `{"type": "text", "value": "<the README body, inlined>"}` and `pages` =
    two entries — `{"id": "rules.md", "title": "Rules", "content": {"type": "text", "value":
    "<docs/RULES.md inlined>"}}` and `{"id": "protocol.md", "title": "Wire protocol", "content":
    {"type": "text", "value": "<docs/PROTOCOL.md inlined>"}}`. A manifest test asserts all three
    values are non-empty text.
  - `game.player[0]` = `{"id": "baseline", "name": "marcher", "type": "player", "image":
    "{{HIVE_IMAGE}}", "run": ["/bin/hive-player"], "env": {"PLAYER_SCRIPTED": "marcher"},
    "source_url": "https://github.com/Metta-AI/cogame-hive/tree/main"}` — the bundled certification
    player, no LLM.
  - **Variants — `num_agents` is 4 in every one:**

    | id | name | `num_agents` | `antsPerColony` | `episodeTicks` | `turnTicks` | turns | `turnBudgetSeconds` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|
    | `default` | Meadow (4 colonies, 200 s) | **4** | 24 | 4800 | 240 | 20 | 22 | 660 |
    | `sprint` | Sprint meadow (4 colonies, 120 s) | **4** | 24 | 2880 | 240 | 12 | 22 | 420 |

    `sprint` exists for cheap ladder rounds; it changes only the episode length, **never the seat
    count** and never `antsPerColony`. Both variants list four `players` entries.
  - **Certification fixture** (`certification`): `players` = `[{"player_id": "baseline"} × 4]`;
    `game_config` =
    `{"players": [{"name":"P1"},{"name":"P2"},{"name":"P3"},{"name":"P4"}], "num_agents": 4,
    "seed": 42, "antsPerColony": 24, "episodeTicks": 960, "turnTicks": 240,
    "turnBudgetSeconds": 22, "wallClockBudgetSeconds": 180, "playerConnectTimeoutSeconds": 60,
    "bonanzaTicks": [480], "fieldPath": "meadow"}` — 960 ticks, 4 turns, all four seats scripted, no
    LLM, wall clock ≈ 4 s.
- **Scaffold from `coworld-builder/templates/`** with `<slug>` = `hive`, `<IMAGE>` = `coworld-hive`,
  `<SEATS>` = **4**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**committed mode 100755**), `tools/build_replay_viewer.sh` (**committed
  mode 100755** — `coworld build` hard-requires `os.X_OK`), `tools/ci/policies.json`.
  `SMOKE_REQUIRE_REPLAY_JSON` stays at its default `1`; `SMOKE_SEATS` is `4` and is an independent
  cross-check against `certification.game_config.num_agents` (a mismatch prints `SEAT-COUNT FAIL:`).
- **`tools/ci/policies.json`** (all four `"run": "/bin/hive-player"`, one image, env-switched):

  | name | env | role |
  |---|---|---|
  | `hive-pathwright` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `hive-swarmraid` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `hive-marcher` | `PLAYER_SCRIPTED` = `marcher` | filler |
  | `hive-driftling` | `PLAYER_SCRIPTED` = `driftling` | filler |

- **Repo layout:** `src/hive.nim`, `src/hive_player.nim`, `src/hive/` (`types.nim`, `field.nim`,
  `pheromones.nim`, `ants.nim`, `sources.nim`, `sim.nim`, `rules.nim`, `doctrine.nim`,
  `baselines.nim`, `llm.nim`, `state.nim`, `config.nim`, `roster.nim`, `events.nim`, `labels.nim`,
  `broadcast.nim`, `global.nim`, `render.nim`, `replay.nim`, `server.nim`), `replay-viewer/`
  (`hive_replay.nim`, `config.nims`, `static_replay.js`, `static_replay_worker.js`), `client/`
  (`replay_broadcast.html`, `chrome_common.js`, `broadcast_core.js`, `art/`), `data/`
  (`meadow.fieldspec.json`, art, `font.ttf`), `tests/` (+ `tests/support/`), `tools/`,
  `scripts/art/`, `docs/` (`RULES.md`, `PROTOCOL.md`, `plans/`), `AGENTS.md`, `README.md`,
  `nimby.lock`, `hive.nimble`, `config.json`. `players/` is **not** used (the player is
  `src/hive_player.nim`).

---

## Tests

CI is the only harness — the sandbox has no Docker, no Nim, no emsdk. The template `ci.yml` runs
**every `tests/*.nim` file individually, twice (debug and `-d:release`)**
(`templates/ci.yml:101-131`), so each test file is a standalone program and shared helpers live in
**`tests/support/helpers.nim`** (a subdirectory, so the `tests/*.nim` glob never executes a helper
module). No aggregator file.

1. **`tests/test_pheromones.nim`** — **sim unit tests** on the field: a deposit saturates at exactly
   `pheromoneMax` and never wraps the `uint16`; decay runs only on ticks divisible by 8 and applies
   `(p*248) shr 8`; a cell at 4000 with no reinforcement is below 2000 after 175 ± 2 ticks
   (the stated half-life) and exactly 0 once it drops under `pheromoneFloor`; a zero cell is skipped
   and stays zero; the 8 × 8 block downsample of a hand-built plane equals a hand-computed digit
   string; the four colonies' planes are fully independent (writing Amber's `F` never moves Teal's).
2. **`tests/test_ants.nim`** — **sim unit tests** on the kernel: an ant with a strong `F` gradient
   on its forward-left cell turns onto it; ties break left-forward-right; an ant boxed by rock on all
   three candidates turns 90° and does not move; an ant never enters rock or leaves the field over
   50 000 randomised activations; activation striping puts exactly 48 ants on every tick; a carrying
   ant beyond 12 cells ignores the nest and follows `H`, and inside 12 cells walks the Chebyshev
   gradient home; pickup takes exactly one unit, sets `carried_from` and about-faces; delivery
   increments exactly one counter and only on the ant's **own** pad; a rival's pad does nothing;
   scouts get `alphaFood div 4`, `alphaRival 0` and doubled noise. Plus the **no-float source guard**:
   grep `src/hive/*.nim` for `sin|cos|tan|atan|arctan|exp|ln(|pow|fmod|hypot|sqrt` and for
   `float`/`float64` inside the step path, and the build scripts for `-ffast-math`; any hit fails.
3. **`tests/test_sources.nim`** — spawn and decay of food: an orbit is exactly four mirror-symmetric
   cells; no orbit spawns while three are alive; a drawn cell is never rock, never within 14 of a
   nest, never within 3 of a live source, and the 64-try rejection loop terminates; the two bonanzas
   land on the four centre cells at ticks 1200 and 3600; a source retires with `depleted` at zero and
   `expired` at its life; `harvest` buckets flush every 24 ticks and their sum equals total units
   removed.
4. **`tests/test_field.nim`** — `data/meadow.fieldspec.json` loads; the baked rock mask is invariant
   under `cx → 159 − cx` and `cy → 87 − cy`; every nest pad and every bonanza cell is free floor;
   the free floor is a single 4-connected component; the four nest centres are the mirror orbit of
   (16, 12); block indices map to cells as documented.
5. **`tests/test_scoring.nim`** — the formula and its sign: the worked example
   `[412, 366, 289, 233]` yields `[0.31692, 0.28154, 0.22231, 0.17923]`; `sum(scores) == 1.0` exactly
   over 500 randomised delivery vectors (including the fourth-value residual rule); `total == 0`
   gives four 0.25s and `winner: null`; a tied maximum gives `win` all false and `winner: null`;
   higher `delivered` always means a higher score; a `deadline` cut mid-episode scores the counters as
   they stand and still sums to 1.0.
6. **`tests/test_determinism.nim`** (**the gate**) — same seed + same doctrine stream ⇒ identical
   digest at every keyframe over a full 4800-tick match, run twice in one process and once in a fresh
   instance; a one-unit change in any single doctrine integer changes the final digest; a committed
   golden fixture `tests/fixtures/golden_digests.json` pins the digests for seed 42 over 960 ticks, so
   any rule change shows up in the diff; the turn snapshots (step 14) reproduce the state the forward
   run had at the same tick, byte for byte.
7. **`tests/test_baselines.nim`** — **the bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random views × both baselines, the emitted doctrine validates against
   the schema — every integer field present and in 0…100, `focus` either `null` or inside
   `[0..19] × [0..10]`, `focus_weight` 0 when `focus` is null, `recall` never true two turns running,
   `note` ≤ 140 runes, `say` ≤ 32 runes — **and** the compiled coefficients are inside their stated
   ranges (`alphaFood` 0…400, `alphaRival` 0…300, `alphaHome` 0…300, `alphaFwd` 120…320,
   `alphaNoise` 40…440, `betaHome` 200…400, `layFood` 40…340, `layHome` 20…220, `scoutCount` 0…24) for
   every colony on every turn. Plus: a `marcher` vs `driftling` match at seed 42 (two seats each)
   completes and the `marcher` seats out-deliver the `driftling` seats — the baselines are ordered, so
   the ladder has a spread.
8. **`tests/test_doctrine.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   `"70%"` strings, `focus` as `{"bx":9,"by":5}`, `focus` out of range, `focus` of the wrong arity,
   negative and 300-valued integers, missing fields on turn 0 and on turn 7, `recall` as `"true"`, a
   400-character `note`, and a `say` whose 32nd and 33rd runes are a 4-byte emoji — the truncation must
   land on the **rune** boundary and the result must still round-trip `%*` / `$` / `parseJson` and
   encode as valid UTF-8. Two consecutive failures ⇒ the `marcher` doctrine plus a `fallback` event; a
   timeout on attempt 1 ⇒ exactly one retry.
9. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: all four seats' calls go out
   in **one parallel batch** (the fake records in-flight windows and the test asserts all four
   intersect); every turn batches exactly 4 requests; the per-turn budget is enforced with a hung
   client; the budget guard switches to scripted and the episode still ends `complete/full_time`; the
   660 s stop yields `deadline/wall_clock`; a raised sim fault yields `fault/sim_fault` with 0.25 for
   every seat and a partial replay; a seat that never registers plays `marcher` and is reported to
   `COGAME_PLAYER_FAILURE_URI`; a mid-match disconnect degrades to `marcher` and revives on reconnect.
10. **`tests/test_view.nim`** — the observation contract: a seat's `trails.rival` shows `.` for every
    block none of its ants entered last turn and a digit for every block one did; `sources[]` never
    contains a source the seat's ants have not been within one cell of, and its `amount_seen` equals
    the value at the last sighting, not the live value; no view, event body or prompt anywhere in an
    episode contains any string from `results.names` (the two-name-space assertion, run over a full
    scripted episode); the scoreboard is present and complete for every seat.
11. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full
    scripted-vs-scripted episode (cert-fixture length) runs over the real sim, writes `results.json`
    and the replay; the replay is parsed **strictly** — the bytes are asserted valid UTF-8 first
    (`validateUtf8(readFile(path)) == -1`) and then `parseJson`ed, and the fixture forces a non-ASCII
    `say` into the doctrine stream so the UTF-8 path is real; `protocol == "hive.replay.v1"`;
    `ants_b64` decodes to exactly `keyframeCount × 96 × 3` bytes; every documented top-level key is
    present and `field`, `names`, `config`, `seat_nests`, `doctrines`, `keyframes`, `events`,
    `results` are non-empty; `results.reason` is in the legal enum; the event stream contains exactly
    one `doctrine` per seat per turn and at least one `source_spawn`, one `harvest` and one `deliver`;
    and re-deriving from `seed` + `field` + `seat_nests` + `doctrines` reproduces **every keyframe
    digest and every byte of `ants_b64`**.
12. **`tests/test_server.nim`** — the websocket and HTTP contract: the `register` frame is accepted, a
    bad token 403s, a duplicate connection 409s, `/healthz` answers, **`GET /client/player?slot=0&token=…`
    and `GET /client/global` both return real pages and neither opens the player socket**, `/global`
    streams a snapshot and keeps answering for the 20 s shutdown grace after artifacts are written,
    artifact writes land on `file://` URIs, `COGAME_EVENTS_URI` / `COGAME_METRICS_URI` reject non-file
    schemes loudly, and replay mode serves `/replay-data` and `/client/replay`.
13. **`tests/test_manifest.nim`** — `num_agents == 4` in **every** variant *and* in
    `certification.game_config`; `len(certification.players) == 4` and
    `len(certification.game_config.players) == 4`; `results_schema` keys equal the keys
    `src/hive/server.nim`'s results builder emits; `game.protocols` carries **both** `player` and
    `global`; `game.docs.readme` and both pages are non-empty **text**;
    `replay_viewer.bundle == "static-replay-viewer"`; `episode_timeout_minutes == 20`; every variant's
    `wallClockBudgetSeconds ≤ 0.6 × 1200`; the image placeholder matches the compose service name
    (`hive` → `{{HIVE_IMAGE}}`).
14. **`tests/test_viewer.nim`** — **the viewer smoke** (no browser): the node harness forked from
    paintbot's `tools/wasm_replay_smoke.cjs` loads `replay-viewer/dist/hive_replay.js` with a recorded
    replay, advances to the end, and asserts the tick total, the final digest, and that seek-to-mid,
    seek-backwards and seek-to-end land exactly (the snapshot path); malformed inputs (bad `protocol`,
    bad base64 length, truncated JSON, `tick_count`/`ants_b64` mismatch, a doctrine with an
    out-of-range integer) are all rejected with a message rather than a crash. Plus static assertions
    over `client/replay_broadcast.html` and `replay-viewer/static_replay.js`: the `coworld-replay`
    bridge **including `tell("ready")`** is present; every inherited chrome id listed in §Viewer is
    still there; `#nestbug`, `#doctrinebar`, `#warflash` and `#cachebar` exist;
    `.plate .team-name { … min-width: 3.2em` and a `@media (max-width: 640px)` block are present.
    (Marked `NIM_TESTS_RELEASE_ONLY` if the debug wasm harness proves slow.)
15. **`tests/test_startup.nim`** — `/bin/hive` exits 2 with a clean one-line message and no traceback
    when `COGAME_CONFIG_URI` is missing or invalid; `--help` works; the player binary exits 0 on an
    unreachable `COWORLD_PLAYER_WS_URL` after its bounded connect retry.
16. **`tests/test_perf.nim`** — 4800 ticks with 96 ants and the full 220 KiB field complete in under
    45 s in a release build, and one turn snapshot round-trip costs under 5 ms.

CI additionally runs `tools/ci/docker_smoke.sh` (a raw-Docker episode from the certification fixture,
`SMOKE_SEATS=4` cross-checked against the manifest, replay required to parse as JSON) with the
`docker-smoke` job depending on the image build **in the same run** so a stale binary can never be
smoked (playbook gotcha, bullwhip 2026-08-22), and `tools/build_replay_viewer.sh` (the bundle builds,
contains `index.html` and a non-empty `.wasm`, and is uploaded as the `static-replay-viewer`
artifact).

---

## Out of scope (v1)

- **A true per-ant RL vector transport.** The idea's stated interface is realised as the colony
  doctrine vector plus the deterministic ant kernel (an inherited pin: both champions must be
  `PLAYER_PROMPT`). Shipping the 96 × (local view) observation batch and accepting a 96 × (action)
  response over the websocket is a v0.2 protocol addition; the doctrine record and the striped
  activation order are already shaped for it.
- **More or fewer than four colonies.** No 2-seat or 3-seat variant, no asymmetric colony sizes. Any
  of those changes `num_agents`, which the seat-count pin forbids in v1.
- **Combat, ant death, ant birth, and colony growth.** Colonies are exactly 24 ants for the whole
  episode. No fighting at caches, no raiding a rival's nest for stored food, no starvation, no brood,
  no queen mechanics, no ant lifespan.
- **More than two pheromone types**, per-ant pheromone budgets, pheromone that diffuses spatially
  (hive's fields decay in place but do not spread), or colony-specific pheromone that rivals cannot
  smell. Two planes, one shared smell space, everybody's paint readable by everybody who walks on it.
- **Procedural fields.** One authored field, `meadow`. Paintbot's generator, validators, curated pool,
  size/symmetry knobs and map editor are all dropped. Field variety is the first v0.2 feature once the
  ladder is healthy, and it must keep the two-mirror symmetry.
- **Continuous motion.** No sub-pixel positions, no velocity, no collision, no wall sliding.
  Paintbot's motion constants do not survive the fork; ants step cell to cell on an integer lattice,
  which is what buys bit-exact wasm re-derivation.
- **Fog of war over the terrain.** Rock is public. What is hidden is where the food is, where the
  rivals are, and what their paint says — not the shape of the meadow.
- **Any inter-seat channel.** `note` and `say` are one-way to the spectator feed and are never
  delivered to another seat. There is no chat, no trade, no truce mechanism, and no cross-episode
  memory of any kind.
- **Weather, seasons, day/night, obstacles that move, water, or elevation.**
- **Audio, 3-D, camera cuts other than the trail-war and raid holds, and any downloaded art asset**
  (the bundle stays hermetic).
