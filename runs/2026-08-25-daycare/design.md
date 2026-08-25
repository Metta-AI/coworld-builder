# Daycare — one cog can reach the fruit, the other one knows which fruit it wants, and neither can say a word

**Starter: `Metta-AI/coworld-ctf` (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`.**
Daycare is a real-time grid loop with rules written fresh for this coworld, per-tick grid actions and
a per-tick replay — the first row of the starter table ("any real-time game loop, grid OR continuous
physics, new rules written for this coworld"). The Melting Pot substrate is the *design source*, not
a binary to reproduce bit-exactly, so this is not a `cogame-moba` port. Paintbot supplies the tick
loop, the sprite-protocol board renderer, the broadcast chrome, the static wasm replay bundle and the
CI shape. **Every convention there holds here unless this note says otherwise.** Two things paintbot
does not have are ported from `Metta-AI/cogame-bullwhip` (mounted at
`/workspace/starters/cogame-bullwhip`) and are named as such where they appear: the *game-side*
batched LLM decision layer (`src/bullwhip/llm.nim`) and the thin prompt-carrying player process
(`src/bullwhip_player.nim`). **All four viewer files come from coworld-ctf only** (see `## Viewer`).
There is no `OPEN` section: every rule the idea leaves loose — including the reward wiring the idea's
build note wanted checked against Lua that does not exist in this sandbox — is decided below with the
reason stated.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design), each answered
explicitly:**

| pin | how Daycare satisfies it |
|---|---|
| starter by game shape | `Metta-AI/coworld-ctf` (paintbot) — a real-time grid loop with per-tick grid actions and rules written for this coworld; nothing external is reproduced bit-for-bit (chemistry / paintball precedent, same day). |
| public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-daycare`, **public** — a certification prerequisite (`source-resolves` 404s on private). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | one image; `PLAYER_PROMPT="<strategy>"` vs `PLAYER_SCRIPTED=caretaker\|stubborn` (`## Decisions`). Champions #1 `daycare-attentive` (daveey) and #2 `daycare-provider` (daveey-1) are both prompt policies; the two fillers are the two scripted baselines. |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` live viewer is declared (`## Viewer`, `## Packaging`). |
| real art, starter chrome verbatim | `scripts/art/gen_daycare_art.py` commits grass/fence/tree/shrub/fruit/basket/cog art; `client/chrome_common.js` ships **byte-for-byte** and `client/replay_broadcast.html` is the starter's page with a game block appended (`## Viewer`). |
| legible to a casual spectator | `TURN 4 / 15`, plates that read `PARENT` and `CHILD` with whole-number scores, a spectator-only `BRAMBLE WANTS: BANANA` badge over `ALDER GUESSES: APPLE — WRONG`, a 15-chip guess tape, and a feed that says `BRAMBLE ATE BANANA +3`; checked at 360 px. |
| two name spaces | anonymous cog aliases `Alder` (parent) and `Bramble` (child) in-game and in every prompt; policy names only spectator-side (`roster[].pol`, the roster strip, `results.names`) — `## The game` §Seats. |
| degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | ≤ 661 s worst case against a 720 s budget, deadline checked between turns, retry-once-then-scripted, `shutdownGraceSeconds = 20` (`## Decisions`, `## Server, player, protocol`). |
| `num_agents` in every variant AND the cert fixture | **2**, in all four variants, in `certification.game_config`, and as `<SEATS>` in `tools/ci/docker_smoke.sh` (`## Packaging`, `## Tests`). |
| replay bytes self-sufficient | aliases, policy names, roles, full yard geometry, every rule constant, the seed, **the child's secret preference**, per-tick state, the score series, beats, events and final results all live in the replay (`## Sim module` §The replay file). |
| prove it in CI | sim tests, bounded-orders/legality tests on both baselines, a feasibility oracle, two **no-leak** tests, an end-to-end episode writing a replay, a strict-UTF-8 parse, an **executed** viewer smoke (`## Tests`). |

**Source idea (verbatim, Asana idea task 1217762644766180):**

> Port of Melting Pot's daycare. Two roles: parent and child. Apple and banana trees; fruit in tall trees can only be harvested by the parent, shrubs by either (the config deliberately gives the child a low chance of reaching what it likes). The child has a preference the parent can't see directly and has to infer from behaviour (what the child approaches / grabs); the parent is rewarded through the child being fed. Caregiving as a game: read another agent's goals from its actions and provide for them, with no explicit channel.
>
> Seats: 2 (parent + child), roles by seat
> Motive: asymmetric cooperation / theory of mind
> Policy interface: per-tick grid actions; LLM variant gets a 'what the child did last' summary
> Fills gap: the only idea where one seat's reward depends on correctly modelling another seat's hidden preference from movement alone
> Integrity (anti-collusion): preference seeded per episode; score both roles; anonymous aliases.
>
> Replay plan (watchability): reveal the child's secret preference to spectators (not the parent) so the audience can see the parent guess right or wrong in real time.
>
> Build note: daycare.py has no docstring — verify exact reward wiring (parent reward = child consumption?) from the Lua components before writing the spec.
>
> Source: substrate daycare.

---

## The game

### Seats, roles, aliases, names

**`num_agents = 2`.** Exactly two seats, one cog each, no teams. Role is fixed **by seat**, exactly as
the idea pins it:

| slot | role (default) | in-game cog alias | body colour (paintbot `slots[].color`) | spawn cell |
|---|---|---|---|---|
| 0 | **parent** | `Alder` | `blue` | (12, 9) |
| 1 | **child** | `Bramble` | `yellow` | (11, 4) |

Aliases are fixed to slots and never rotate. Cells are `(col, row)`, origin top-left. The config key
`slot0Role` (`"parent"` default, `"child"` in the `daycare-swapped` variant) is the **only** thing
that swaps which slot carries which role; the aliases follow the role, so `Alder` is always the
parent and `Bramble` always the child, whichever slot they sit in. That variant exists so the ladder
can rate a policy in both roles without any change to `num_agents` (which is 2 everywhere).

**Two name spaces (pin).** A seat sees only aliases — its own and the other one — in every
observation and every prompt. No policy name, player name, account or model name ever reaches a seat,
and **neither seat ever sees the episode seed**. The replay carries `policyNames[]` alongside
`names[]`; the viewer's roster strip and plate sublines show the **policy** name (paintbot's
`roster[].pol` path in `client/chrome_common.js`, `teamPolicies()`), and `results.names[]` carries
policy names for the platform. Both, not either.

### The yard

- A fixed grid, `cols = 24` × `rows = 14`, cell size 48 board-px → a 1152 × 672 board. **The whole
  board always fits the frame**, which is why the viewer drops `#viewpanel` (zoom bar + minimap)
  entirely (`## Viewer`).
- **Fence:** the full border ring (row 0, row 13, col 0, col 23) is impassable fence. Everything
  inside is grass floor except the sources listed below.
- **Tall trees** — 8, impassable, 4 apple + 4 banana:
  apple `(4,2) (16,2) (7,11) (19,11)`; banana `(7,2) (19,2) (4,11) (16,11)`.
- **Shrubs** — 4, impassable, 2 apple + 2 banana:
  apple `(9,5) (14,8)`; banana `(14,5) (9,8)`. The `daycare-sparse` variant keeps only
  apple `(9,5)` and banana `(14,5)`.
- **Basket mat** — 4 walkable cells `(11,6) (12,6) (11,7) (12,7)`. Fruit resting on a mat cell does
  **not** rot; the mat holds at most `basketCapacity = 2` fruit in total (one per cell, first two
  cells in `(row, col)` order).
- **The layout is species-congruent by construction.** The reflection `x → 23 − x` maps the apple set
  exactly onto the banana set (trees and shrubs alike), so no species is nearer to anything than the
  other and a policy cannot infer the preference from the map. A `mirror` bit drawn from the layout
  RNG sub-stream (see below) reflects the whole yard, so "apples live on the left" is not a learnable
  prior either. `tests/test_noleak.nim` asserts the congruence and the independence.
- Every sim quantity is an **integer** (chances are per-mille ints); the RNG is paintbot's seeded
  stream. No floats enter sim state, so a seed reproduces a replay bit-exactly.
- **Two RNG sub-streams, deliberately separate.** `rngLayout = seededRng(seed)` draws the `mirror`
  bit and every tie-arbitrary layout choice. `rngSecret = seededRng(seed xor 0x0DA9CA12)` draws the
  child's preference and (in `daycare-fickle`) the switch turn. Nothing the parent can observe is
  ever drawn from `rngSecret`, and nothing the preference depends on is drawn from `rngLayout` —
  which is what makes "the parent cannot see it directly" true of the *bytes* and not just of the
  prompt.

### Fruit, sources, and who can reach what

Two species: **`apple`** and **`banana`**. That is the whole vocabulary — the idea names exactly these
two, and a third species is out of scope (v1).

| source | capacity | initial ripe | regrow | parent may harvest | child may harvest |
|---|---|---|---|---|---|
| tall tree | `tallCapacity = 3` | 2 | +1 ripe every `tallRegrowTicks = 36` ticks, capped | **always** | **never** — the attempt is the "reach" |
| shrub | `shrubCapacity = 1` | 1 | +1 ripe every `shrubRegrowTicks = 240` ticks, capped | **always** | with probability `childShrubPickPermille / 1000` (**250** base, **150** in `daycare-sparse`) |
| ground fruit | 1 per cell | — | — | always | always (it is on the floor; no reaching involved) |

- A failed child pick at a **tall tree** costs nothing but the tick and emits a `reach` event — the
  futile reach is the game's whole signalling surface and must stay cheap.
- A failed child pick at a **shrub** emits a `reach` event and puts that seat on a
  `childReachCooldownTicks = 6` fumble cooldown during which every action degrades to `wait`.
- Ground fruit ages: `ttl` starts at `fruitLifetime = 120` ticks and decrements on non-mat cells only;
  at 0 the fruit is removed (`rot`). A delivery therefore has to land near the child, not anywhere.

This is exactly the idea's "the config deliberately gives the child a low chance of reaching what it
likes", and it is implemented **species-neutrally on purpose**: making the child's *preferred* species
the scarce one would leak the preference to the parent through the map. The scarcity is on the child's
*hands*, not on the fruit.

### What a cog can do (per-tick grid actions)

Each cog occupies one cell, carries at most one fruit (`carryCap = 1`) and emits exactly one action
per tick from this vocabulary:

`move_n` · `move_s` · `move_e` · `move_w` · `pick` · `drop` · `eat` · `wait`

- `move_*` is legal only every `moveCooldown = 2` ticks (12 cells/s) and only into a grass or mat cell
  that is not fence, not a tree/shrub and not occupied by the other cog; an illegal move degrades to
  `wait`.
- `pick` with an **empty hand**: first, if the cog's own cell holds ground fruit, take it (always
  succeeds). Otherwise choose the first orthogonally adjacent source (N, E, S, W order) that holds
  ≥ 1 ripe fruit **and** matches the standing order's named species if one is named, else the first
  ripe adjacent source; then apply the reach table above. With a full hand, `pick` degrades to `wait`.
- `drop` with a **full hand** puts the fruit on the cog's own cell if that cell holds no fruit (and,
  on the mat, if the mat is below `basketCapacity`); otherwise `wait`.
- `eat` consumes the carried fruit if the hand is full, else the ground fruit on the cog's own cell,
  else `wait`. Scoring is in §Scoring — the short version is that only the **child** eating scores,
  and a parent that eats destroys the fruit for **0**.

**Where the per-tick actions come from.** A seat does not hand-author 720 actions — no LLM can. Once
per **turn** (`ticksPerTurn = 48`) each seat submits a **standing order** (`## Decisions`), and a
deterministic **kernel** turns that order into the per-tick action stream for the whole turn. The
sim's policy interface is per-tick grid actions exactly as the idea says; the LLM chooses the *job*,
the kernel walks the yard. 30 LLM calls per episode instead of 1 440 (the batched cadence that worked
in cogame-hive, cogame-ecos and cogame-chemistry).

BFS is over walkable cells only (the other cog is not an obstacle for path *planning*, only for the
move itself), with neighbour expansion in N, E, S, W order, so paths are unique and deterministic.
Ties between equidistant targets break by `(row, col)` ascending.

**Parent kernel jobs** (order fields `{job, fruit, guess}`):

1. `provide` (species `F`) — if the hand holds `F`: BFS to the **drop target** = the nearest cell with
   no fruit on it within Chebyshev distance 1 of the child, else within distance 2, else the child's
   own cell's nearest free neighbour; `drop` on arrival. If the hand is empty: BFS to the nearest
   source of `F` that the parent may harvest, in the order ground fruit → tall tree → shrub, and
   `pick` on arrival. If the hand holds the other species: `drop` in place if the cell is free, else
   step one cell (first legal of N, E, S, W) and `drop`.
2. `stock` (species `F`) — as `provide`, but the destination is the nearest free basket-mat cell. If
   the mat is full, `drop` on the nearest free cell adjacent to the mat.
3. `watch` — BFS to the nearest free cell within Chebyshev distance 2 of the child, then `wait`. Costs
   a turn and feeds nobody; it exists so "spend a turn observing" is expressible.
4. `idle` — `wait` in place.

**Child kernel jobs** (order fields `{job, fruit}`):

1. `seek` (species `F`) — if the hand holds a fruit, `eat` it. Else if the own cell holds ground fruit
   of `F`, `eat` it. Else BFS to the nearest source of `F` in the order ground fruit of `F` → shrub of
   `F` → tall tree of `F`, and on arrival `pick` **every tick** (at a tall tree that is the visible,
   repeated reaching).
2. `show` (species `F`) — BFS to the nearest **tall tree** of `F` and `pick` every tick. Pure
   signalling: it can never yield food. It exists because the idea's channel is behaviour, and a child
   that can spend a turn shouting with its body is what makes the parent's inference tractable.
3. `graze` — as `seek` but species-blind: nearest ground fruit of **any** species → `eat`; else nearest
   **shrub** of any species → `pick`. Never approaches a tall tree. A grazing child emits no species
   signal at all — which is precisely why the `stubborn` baseline grazes.
4. `beg` — BFS to the nearest free cell within Chebyshev distance 1 of the parent, then `wait`; eats
   any ground fruit it is standing on. Shortens the parent's delivery loop at the cost of saying
   nothing.
5. `idle` — `wait` in place.

Note what `seek` does **not** do: it never eats a ground fruit of the *other* species. A child standing
on an unwanted apple and refusing it is a legal, deliberate, and highly informative act (counted as
`groundPasses.apple` in the parent's summary) — and it costs the pair the `+1` it declined. That
trade-off is the game.

### Turns, and the exact tick resolution order

One episode = `turns = 15` × `ticksPerTurn = 48` = **720 ticks**. Playback is 24 fps, so a full replay
is 30 s of video (comfortably longer than the 10 s viewer soak gate — ecos, 2026-08-23).

Every tick runs these nine steps in this order. Within a step, seats resolve in **ascending slot
order**, and sources in the fixed order tall trees then shrubs, each by `(row, col)`. All reads inside
a step use the state as it stood at the start of that step unless the step says otherwise.

1. **Regrow.** Every source whose `ripe < capacity` advances its regrow counter; on reaching
   `tallRegrowTicks` / `shrubRegrowTicks` it adds one ripe fruit, resets the counter and emits `ripen`.
2. **Kernel intent.** Each cog's kernel computes this tick's action from its standing order and the
   current state. A cog whose `moveCooldown` counter or `childReachCooldownTicks` fumble counter is
   still running emits `wait` instead.
3. **`pick` resolves**, slot order, per the `pick` rule above. Success emits `pick`; a failed
   tree/shrub attempt emits `reach` and (shrub only) starts the fumble cooldown. A `pick` of a ground
   fruit the other cog already took this tick degrades to `wait`.
4. **`drop` resolves**, slot order. The new ground fruit gets `ttl = fruitLifetime`, or `ttl = -1`
   (never rots) on a mat cell. Emits `drop` with `near = "child" | "basket" | "floor"`.
5. **`eat` resolves**, slot order. If the eater is the **child**: `+rewardPreferred = 3` when the
   species equals the child's current preference, else `+rewardOther = 1`, credited to **both** seats
   (see §Scoring); emits `eat` with `pref` and `pts`. If the eater is the **parent**: the fruit is
   destroyed, **0** to both seats, emits `waste`.
6. **Moves resolve**, slot order, against the *live* board: a move into a cell the lower-numbered seat
   has already moved into this tick fails and degrades to `wait`. Cooldown counters reset on a
   successful move.
7. **Ground fruit ages.** Every ground fruit with `ttl > 0` decrements; at 0 it is removed and emits
   `rot`. Mat fruit (`ttl == -1`) is skipped.
8. **Behaviour accounting.** For each seat, and per species, increment the counters the other seat's
   summary is built from: `adjacentTicks` (ended the tick orthogonally adjacent to a source of that
   species), `reachAttempts`, `reachFails`, `groundPasses` (ended the tick standing on a ground fruit
   of that species without eating it), `ate`, `carriedTicks`, plus scalar `cellsWalked` and
   `idleTicks`. These are the idea's "what the child did last" summary, computed by the sim so it is
   identical for every policy.
9. **Record.** Append this tick's state frame, its events and the score-series row to the replay.

At a turn boundary (every 48 ticks) the sim additionally: closes the turn accounting and emits `turn`;
in `daycare-fickle`, applies the preference switch if this is `preferenceSwitchTurn` (emitting
`switch`); checks the end conditions; and — if the episode continues — blocks for the next batched
decision (`## Decisions`).

### Scoring — the child's meals, mirrored to the parent; higher is better

**The reward wiring, decided here.** The idea's build note asked for the Melting Pot Lua components to
be checked; that source is not present in this sandbox, so this note fixes the wiring itself and states
the reason rather than leaving a hole:

- **Child score `S_child`** = `3 ×` (preferred fruit the child ate) `+ 1 ×` (other fruit the child ate).
- **Parent score `S_parent` = `S_child`, exactly mirrored.** The parent is rewarded *through the child
  being fed*, for every meal, whoever picked it.
- **The parent eating scores 0** for both seats and destroys the fruit.
- **Sign: higher is better.** Both integers, `≥ 0`. **The league ranks by `results.scores`** (the
  platform's mean over episodes). Nothing else is ranked; deliveries, reaches, guess accuracy and
  waste are reported for the viewer and analysis only.

Why mirrored and not "credit only fruit the parent delivered": mirroring is the faithful reading of
"the parent is rewarded through the child being fed", it needs no provenance bookkeeping on every
fruit, and it does **not** let a lazy parent free-ride — because the reach table above means the child
can barely feed itself (feasibility gate (d) pins that at ≤ 35 % of a working pair's score). The bite
comes from the *multiplier*: a correctly-read delivery is worth 3, a misread one is worth 1, so
reading the child right is a 3× score, not a tie-break.

Why the parent can eat at all: it makes the naive "food is good, eat food" failure mode expressible
and legible — the feed says `ALDER ATE THE APPLE — WASTED` — which is exactly the kind of visible
mistake a spectator can read. It is never rewarded.

`results.win[i] = (scores[i] >= parScore)` with **`parScore = 2 × turns = 30`**. Daycare is
cooperative: there is no loser to declare, the platform wants a boolean, so the boolean is "the pair
beat par". Par 30 sits deliberately between the arithmetic below for a random-guessing parent (≈ 30)
and a reading parent (≈ 45): a pair that reads the child beats par, a pair that flips a coin does not
reliably.

**Anti-collusion, as the idea specifies it.** The preference is drawn per episode from `rngSecret`
(seed-derived, and the seed is never shown to a seat); **both** roles are scored; aliases are anonymous.
There is **no inter-seat text channel at all** — see the reply schema: each seat's `hunch` and `notes`
are spectator-side and private respectively, and `tests/test_noleak.nim` asserts that neither the
child's preference, `hunch`, nor `notes` ever appears in a byte of the parent's `state` frame.

### End conditions and `results.reason`

The episode ends at the FIRST of these, all checked at a **turn boundary**:

| condition | `results.reason` | `results.ending` | scores |
|---|---|---|---|
| 15 turns played | `complete` | `turn_limit` | as computed |
| wall clock passes the play deadline (0.6 × `episodeTimeoutSeconds` = **720 s**) | `deadline` | `deadline` | turns played are scored; the rest add nothing |
| no seat connected within `playerConnectTimeoutSeconds = 120` | `forfeit` | `forfeit` | all zero; results + replay are still written |

Those three — **`complete`, `deadline`, `forfeit`** — are the only legal `results.reason` values, and
`turn_limit`, `deadline`, `forfeit` the only legal `results.ending` values. There is no famine case:
tall trees always regrow, so a fed-nobody episode is a *completed game of Daycare* with a low score,
which is the correct outcome and keeps phase 60's check 4 green. `deadline` is admissible (it means the
LLM was slow, not that the game broke) but the arithmetic in `## Decisions` is sized so it should not
fire. A seat that never connects does **not** end the episode: it plays `caretaker` and the game runs.

### Throughput arithmetic, and the feasibility gates

These are **design targets derived from the constants above, not measurements**. The enforcement is
`tests/test_feasibility.nim` (`## Tests`), not this table — ecos, 2026-08-23, shipped a note whose
"measured" oracle was a hypothesis the builder had to repair.

- Parent delivery loop: ~8 cells to a tree + ~8 back at `moveCooldown = 2` → 32 ticks, plus a `pick`
  and a `drop` → **≈ 1 delivery per 48-tick turn**, occasionally 2 when the child is `beg`ging next to
  a tree. Over 15 turns: **15–20 deliveries**.
- A read-right pair: 15–20 × 3 = **45–60** points. A coin-flipping parent: 15–20 × 2 = **30–40**. A
  parent that always brings the wrong species: 15–20 × 1 = **15–20**. That 3× spread is the skill
  signal the league needs to see.
- Child self-feeding: 4 shrubs, one ripe fruit each per 240 ticks → ≈ 12 fruit exist per episode, but
  the child can only stand at one shrub at a time, needs ~22 ticks per success at
  `childShrubPickPermille = 250` with a 6-tick fumble cooldown, and has to walk 5–8 cells between
  shrubs → **≈ 6–8 fruit, ≈ 12–16 points, ~half of them the wrong species**. In `daycare-sparse` (2
  shrubs, 150 ‰) it is ≈ 3 fruit. The parent is necessary; the child is not helpless.
- Hedging is dominated, which is what forces inference: a parent that alternates apple and banana
  ("stock both, let the child choose") halves its useful throughput, so ≈ 8 × 3 + 8 × 1 = **32** — no
  better than a coin flip and far below 45. `basketCapacity = 2` is what keeps that true; a bottomless
  pantry would delete the game.
- Sim cost: 720 ticks × 2 BFS over 336 cells ≈ **0.5 s** total.

The gates `tests/test_feasibility.nim` enforces, over seeds 1..12 on all four variants:

- **(a) The baselines play the game.** `caretaker` parent + `caretaker` child: ≥ 10/12 seeds end
  `complete` / `turn_limit` with `score ≥ parScore` (30) and the parent's guess correct on ≥ 10 of 15
  turns. This is what makes certification, `docker-smoke` and all-filler league episodes finish and
  look like Daycare.
- **(b) Ignoring the child costs.** `stubborn` parent (always apple) + `caretaker` child scores
  ≤ 0.7 × the (a) mean.
- **(c) Being unreadable costs.** `caretaker` parent + `stubborn` child (grazer) scores ≤ 0.8 × the (a)
  mean, and the parent's guess accuracy over the episode lands in 0.35..0.65 — i.e. with no behaviour
  to read, inference degrades to chance, on purpose.
- **(d) The parent is necessary.** `idle` parent (a test-only kernel order) + `caretaker` child scores
  ≤ 0.35 × the (a) mean.
- **(e) Hedging is dominated.** A test-only `hedge` parent (alternate `stock apple` / `stock banana`)
  + `caretaker` child scores ≤ 0.8 × the (a) mean.
- **(f) No species bias.** Across seeds 1..12, the (a) mean with the preference forced to `apple` and
  forced to `banana` differ by ≤ 5 %.

**If a gate fails, repair constants in this order and re-run — no design bounce is needed:** (a)
`ticksPerTurn 48 → 60` then `tallRegrowTicks 36 → 24`; (b) `rewardOther 1 → 0` **only as a last
resort** (it removes the consolation prize and sharpens the multiplier); (c) `fruitLifetime 120 → 96`;
(d) `shrubRegrowTicks 240 → 320`, then `childShrubPickPermille 250 → 150`; (e) `basketCapacity 2 → 1`;
(f) fix the layout congruence, never the reward. Any change to a constant in this section re-runs the
oracle. **That test is the enforcement, not this table.**

---

## Decisions: LLM with scripted fallback

Both policies ship in the **same image** from day one, env-switched, exactly like bullwhip:
`PLAYER_PROMPT="<strategy text>"` for an LLM policy, `PLAYER_SCRIPTED=caretaker|stubborn` for a
scripted baseline. **A policy is a prompt.** `src/daycare_player.nim` (a fork of
`cogame-bullwhip/src/bullwhip_player.nim`) is one thin process that connects, sends
`{"type":"prompt","prompt":…,"scripted":…}` and then only listens. All decision-making happens in the
**game** container (`src/daycare/llm.nim`, forked from `cogame-bullwhip/src/bullwhip/llm.nim`) — which
is what makes one parallel batch per turn possible, and is why the coworld secret must be declared on
the *game* runnable (hive, 2026-08-23).

### Cadence and the wall-clock budget

One **turn = 48 ticks**. At each turn boundary the game issues **both seats' requests as ONE parallel
batch** (`curly.makeRequests`, bullwhip's `decideAll`) — never sequentially. Decisions are
**simultaneous**: neither seat sees the other's order for the turn about to be played.

```
per turn:      1 batch of 2 requests, llmTimeoutSeconds = 18
worst case:    18 s (batch) + 18 s (one retry batch)              =  36 s
15 turns:      15 x 36 s                                          = 540 s
+ connect:     playerConnectTimeoutSeconds ceiling on the wait     <= 120 s
+ sim:         720 ticks x ~0.7 ms (2 BFS/tick over 336 cells)     ~   0.5 s
total worst:   ~661 s   <   720 s   ( = 0.6 x episodeTimeoutSeconds 1200 )
typical:       max(minTurnSeconds 8, ~6 s batch) x 15              ~ 120 s
```

`minTurnSeconds = 8` floors the spacing between batch starts, so the episode issues at most
2 requests / 8 s = **15 requests per minute**, under the Bedrock sidecar's 30 rpm per-episode ceiling
that bit cogame-raid. Requests per episode: 30, plus ≤ 30 retries. The play deadline
(0.6 × `episodeTimeoutSeconds`; the game container is **not** given `COWORLD_TIMEOUT_SECONDS`, so 1200
is assumed unless that env var is present) is tested **between turns**; hitting it calls `endEarly()`
and settles with `reason: "deadline"`.

### The observation each seat gets

Sent as the `state` frame at every turn boundary and rendered into the user prompt. Every number below
is visible to that seat; **nothing else is**.

**Parent (`role: "parent"`):**

```json
{"type":"state","protocol":"daycare.player.v1","slot":0,"role":"parent","name":"Alder",
 "turn":4,"turns":15,"ticksPerTurn":48,"tick":192,
 "yard":{"cols":24,"rows":14,"variant":"daycare-sparse","mirrored":false},
 "you":{"cell":[11,7],"carrying":"apple","score":8,"par":30,
        "delivered":{"apple":3,"banana":1},"stocked":{"apple":0,"banana":1},"wasted":0,
        "lastOrder":{"job":"provide","fruit":"apple","guess":"apple","source":"llm"}},
 "child":{"alias":"Bramble","cell":[18,4],"carrying":null,"score":8,
          "lastTurn":{"adjacentTicks":{"apple":22,"banana":0},
                      "reachAttempts":{"apple":19,"banana":0},
                      "reachFails":{"apple":19,"banana":0},
                      "groundPasses":{"apple":0,"banana":6},
                      "ate":{"apple":1,"banana":0},
                      "carriedTicks":{"apple":3,"banana":0},
                      "cellsWalked":14,"idleTicks":2},
          "cumulative":{"adjacentTicks":{"apple":71,"banana":6},
                        "reachAttempts":{"apple":58,"banana":2},
                        "reachFails":{"apple":57,"banana":2},
                        "groundPasses":{"apple":1,"banana":14},
                        "ate":{"apple":4,"banana":2},
                        "carriedTicks":{"apple":9,"banana":1},
                        "cellsWalked":63,"idleTicks":11}},
 "sources":[{"id":"T1","kind":"tall","fruit":"apple","cell":[4,2],"ripe":2,"nextRipeIn":12},
            {"id":"S3","kind":"shrub","fruit":"banana","cell":[14,5],"ripe":0,"nextRipeIn":180}],
 "ground":[{"cell":[17,4],"fruit":"banana","ttl":86}],
 "basket":{"cells":[[11,6],[12,6],[11,7],[12,7]],"apple":0,"banana":1,"capacity":2},
 "history":[{"turn":3,"guess":"apple","childAte":{"apple":1,"banana":0},
             "delivered":{"apple":2,"banana":0},"score":6}],
 "notes":"turn 2: it stood under the apple tree the whole turn and walked over a banana",
 "rules":{"reach":"you may harvest tall trees and shrubs; the child may NEVER harvest a tall tree and picks a shrub only 15% of attempts (this variant)",
          "reward":"the child scores 3 for eating the fruit it prefers and 1 for the other; YOUR SCORE IS THE SAME NUMBER",
          "wasted":"if you eat a fruit yourself it is destroyed and nobody scores",
          "carryCap":1,"moveCooldown":2,"fruitLifetime":120,"basketNoRot":true,
          "channel":"there is NO message channel: you cannot talk to the child and it cannot talk to you",
          "hidden":"the child's preference is not shown to you anywhere"}}
```

- **Visible to the parent:** the whole yard (every source's kind, species, cell, ripe count and time to
  next ripen; every ground fruit and its `ttl`; the basket), both cogs' cells, carried fruit and score,
  its own delivery/stock/waste counters and last order, **the child's behaviour summary for the last
  turn and cumulatively** (the idea's "what the child did last"), the per-turn history including its
  own past guesses, its own private `notes`, and the rules.
- **Hidden from the parent:** the child's **preference** (nowhere, ever), the child's standing order —
  past or pending — its `hunch`, its `notes`, the episode seed, `preferenceSwitchTurn`, the other
  seat's prompt/policy/player name, and anything about the league.

**Child (`role: "child"`):** the same yard/ground/basket/sources blocks and the same shape of summary
about the **parent** (`parent.lastTurn` = `{delivered:{apple,banana}, stocked:{…}, adjacentTicks:{…},
carriedTicks:{…}, wasted, cellsWalked, idleTicks}`), plus:

```json
 "you":{"cell":[18,4],"carrying":null,"score":8,"par":30,
        "preference":"banana","rewardPreferred":3,"rewardOther":1,
        "ate":{"apple":4,"banana":2},"reachFails":{"apple":57,"banana":2},
        "shrubPickChancePermille":150,"reachCooldownTicks":6,
        "lastOrder":{"job":"show","fruit":"banana","source":"llm"}},
```

- **Visible to the child:** everything above **plus its own preference and the two reward values**.
- **Hidden from the child:** the parent's **guess**, its standing order, its `hunch`, its `notes`, the
  seed, `preferenceSwitchTurn` (in `daycare-fickle` the child learns of the switch only from its own
  observation changing at the boundary), and anything about the league.

### The reply schema

The model must answer with exactly one JSON object whose first character is `{`.

Parent: `{"job":"provide","fruit":"banana","guess":"banana","hunch":"It only ever reaches for bananas","notes":"turn 3 it walked over an apple twice"}`
Child: `{"job":"show","fruit":"banana","hunch":"I will stand under the banana tree until it notices","notes":"apples keep arriving"}`

| field | type | cap / range | on violation |
|---|---|---|---|
| `job` | string enum | parent: `provide` \| `stock` \| `watch` \| `idle`; child: `seek` \| `show` \| `graze` \| `beg` \| `idle` | missing, or not in **this role's** enum → **invalid reply** |
| `fruit` | string enum | `apple` \| `banana` | required for parent `provide`/`stock` and child `seek`/`show`; missing or unknown there → **invalid reply**. Ignored for the other jobs. |
| `guess` | string enum | `apple` \| `banana` | **required from the parent every turn**; missing or unknown → **invalid reply**. Ignored (and not recorded) from the child. A `guess` that disagrees with the `fruit` being delivered is **accepted as written** — testing a hypothesis by delivering the other species must stay expressible. |
| `hunch` | string | **80 characters** | truncated |
| `notes` | string | **240 characters** | truncated |

Extra keys are ignored. **Truncation is on rune boundaries**, never bytes: `cleanText(text, limit)` =
`strip` → if `runeLen > limit`, `runeSubStr(0, limit - 1) & "…"` (bullwhip's `cleanText`; a byte cut put
invalid UTF-8 into a replay and only a strict parser found it — bullwhip, 2026-08-22). Newlines in
`hunch` become spaces. The same rune-safe truncation applies to every string that reaches the replay,
including LLM error text (capped at 200 characters).

**`hunch` is spectator-only and `notes` is private.** Neither is ever delivered to the other seat —
that is how "no explicit channel" is enforced mechanically rather than by convention. `hunch` exists so
the broadcast can show what each cog *thought* it was doing; `notes` is the seat's own memory, returned
to it next turn. Both are recorded in the replay. `tests/test_noleak.nim` asserts that no seat's
`hunch`/`notes`/`preference` string appears in the other seat's `state` frame bytes.

### Prompts

**System prompt** (composed by the game, per seat, per turn): the seat's alias in capitals and its
**role**; the yard and the action vocabulary; the standing-order model ("you choose one job for the next
48 ticks; a kernel walks it for you, tick by tick"); the reach table (who can harvest what); the reward
rule stated in full for both seats ("the child scores 3 for its preferred fruit and 1 for the other, and
the parent's score is exactly the same number"); the flat statement that **there is no message channel
in either direction**, that the other seat is a different policy deciding **simultaneously**, that
`hunch` is seen only by spectators and `notes` only by you; for the parent, the sentence "the child's
preference is never shown to you — infer it from where it walks, what it reaches for, and what it
refuses to eat"; and the output contract, ending:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

(Bedrock/Haiku answers prose-first without that sentence — playbook §Phase 1.)

**User prompt:** the observation rendered compactly — a source table (`id | kind | fruit | cell | ripe |
next`), a ground-fruit line, the basket line, then for the parent a **behaviour table** whose columns are
`apple | banana` and whose rows are `adjacent ticks · reach attempts · failed reaches · walked over
without eating · eaten · carried ticks` for last turn and cumulative (this is the inference surface and
it is rendered as a table on purpose), then the per-turn history table, then `YOUR NOTES FROM LAST TURN`,
then the operator block:

> GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
> requested format):
> `<PLAYER_PROMPT>`

then a one-line restatement of the reply shape with the legal enum values **for this role** (precomputing
the legal choice set in the observation is what halved formal-output fallbacks in escrow).

**Transport:** bullwhip's ladder, haiku-only (raid, 2026-08-23 — the sonnet fallback times out on every
sidecar call and turns one throttle into a cascade):
`bedrockModelIds() = ["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`, `BEDROCK_MODEL` overrides.
`maxOutputTokens = 600`. No `output_config.effort` — Haiku 4.5 400s on it. Credentials in order:
Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` / `AWS_BEARER_TOKEN_BEDROCK`) →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`. With none, the client disables itself immediately and both
seats play `caretaker` — which is what keeps offline certification green and deterministic.

**Champion prompts** (phase 50 uploads these; both are `PLAYER_PROMPT` policies, and both must cover
**both roles** because the ladder seats a policy in either):

- `daycare-attentive` (champion #1, daveey): *"Whichever role you draw, the game is reading the other
  cog. AS THE PARENT: your score is whatever the child eats, tripled when it is the fruit it secretly
  wants, so your whole job is to work out which fruit that is and then keep it coming. Read the
  behaviour table first, in this order of trust: failed reaches at tall trees (it cannot pick them, so
  reaching there is pure desire), then fruit it walked over WITHOUT eating (that species is the one it
  does not want), then ticks spent adjacent to a species, then what it actually ate. Set `guess` to the
  species with the most failed reaches, breaking ties with the walked-over column inverted. Then
  `provide` that species and keep providing it every single turn — a delivery is worth 3 and a turn
  spent watching is worth 0, so never `watch` twice in a row and never `stock` unless the child is
  standing on the mat. Never eat a fruit yourself; that is a wasted turn and a wasted fruit. If the
  child suddenly starts refusing what you bring, change your guess immediately. AS THE CHILD: be
  legible. Pick the fruit you prefer and `seek` it; when there is nothing of yours on the ground and no
  ripe shrub, spend the turn on `show` under a tall tree of your species — you cannot pick it, but that
  is the only way to tell the parent what you want. Eat your own species the instant it lands. Refuse the
  other species while your parent is still learning, then take it once your species is arriving reliably —
  1 point is better than 0."*
- `daycare-provider` (champion #2, daveey-1): *"Play the throughput, then the guess. AS THE PARENT: count
  your deliveries — you get about one per turn and there are only fifteen turns, so every turn without a
  drop next to the child is a point you will not get back. Open with two turns of evidence-gathering while
  you deliver: bring one apple, then one banana, and watch which one is eaten within a few ticks and which
  one is stepped over. From turn three onward commit hard to the winner and stop experimenting; a wrong
  commitment costs you 2 points a turn, an uncommitted parent costs 1.5. State the species you have
  committed to in `hunch` with the evidence in one clause. Drop within one cell of the child, never on the
  far side of the yard — ground fruit rots in 120 ticks. Use `stock` only when the child is grazing the
  centre. AS THE CHILD: keep the loop short. `beg` next to the parent when it is carrying your species so
  it can drop and turn around; `show` under your tall tree when it is carrying the wrong one; `seek` the
  moment your species is on the ground. Never `graze` — indiscriminate eating teaches your parent
  nothing and it is the single worst thing you can do in this game."*

### Scripted baselines (both fieldable, both league fillers)

Both are **role-aware**: one baseline plays either seat, deciding purely from its own observation at each
turn boundary (no shared state).

`caretaker` — the working baseline, and the fallback every failed LLM decision lands on.

*As parent:*
1. Score each species: `w(f) = 3·reachFails[f] + 2·groundPasses[other(f)] + adjacentTicks[f] + 4·ate[f]`
   over the **cumulative** summary (so it does not thrash on a quiet turn).
2. `guess` = the species with the larger `w`; on a tie, the one with more `adjacentTicks`; on a further
   tie, `apple`.
3. If the child's cell is within Chebyshev distance 1 of a mat cell and the mat holds a fruit of `guess`,
   emit `{"job":"watch"}`; otherwise `{"job":"provide","fruit":guess,"guess":guess}`.
4. `hunch` = `"reaches: <a> apple / <b> banana"`; `notes` = `""`.

*As child:*
1. If a ground fruit of `preference` exists, `{"job":"seek","fruit":preference}`.
2. Else if a shrub of `preference` is ripe, `{"job":"seek","fruit":preference}`.
3. Else if the parent is carrying `preference`, `{"job":"beg"}`.
4. Else `{"job":"show","fruit":preference}`.
5. `hunch` = `"I want <preference>"`; `notes` = `""`.

`stubborn` — the anti-theory-of-mind foil, and the second league filler. *As parent:*
`{"job":"provide","fruit":"apple","guess":"apple"}` every turn, forever, ignoring the child entirely.
*As child:* `{"job":"graze"}` every turn — eats whatever is nearest, never reaches at a tall tree, and
therefore emits no species signal at all. One exception so a `stubborn` pair is never a guaranteed zero
and never deadlocks: if the child has eaten nothing for 4 consecutive turns it plays
`{"job":"beg"}` for one turn.

Every field either baseline emits is inside its declared enum **for its role** by construction, asserted
in `tests/test_baseline.nim`.

### Degrade, never hang

- Batch timeout `llmTimeoutSeconds = 18`. On transport error, non-2xx, refusal, `max_tokens` before any
  `{`, unparseable JSON, or any **invalid reply** in the table above, that seat alone is retried **once**
  in the same turn's retry batch, with the appended hint *"Your previous reply was invalid. Respond with
  ONLY the requested JSON object, using one of the listed job and fruit values (and a guess, if you are
  the parent)."*
- Still failing → that seat plays the **`caretaker` order** for that turn, logged as
  `daycare llm: seat N falling back to scripted order` and recorded on the `order` event as
  `"source":"fallback"`. `decideAll` never raises; the episode always advances.
- 401/403 disables the client for the rest of the episode (both seats scripted from then on); 429 is
  logged and the seat is retried in the next turn's batch.
- A seat that never connected, or whose socket dies mid-episode, plays `caretaker` for every remaining
  turn. The episode never waits on a socket beyond `playerConnectTimeoutSeconds = 120` at the start and
  never blocks on one mid-episode.
- The episode settles early rather than overrunning: the play deadline is checked between turns,
  `endEarly()` scores what was played, artifacts are written, and — as cogame-lantern taught — `/healthz`
  and `/global` keep answering for `shutdownGraceSeconds = 20` before `quit(0)`, because hosted
  certification pings the global websocket **after** the player pods start.

---

## Sim module

New code lives in `src/daycare/`, mirroring paintbot's split (`src/ctf/`). What is forked, what is kept
and what is deleted — by path:

| paintbot path | daycare | note |
|---|---|---|
| `src/ctf/sim_types.nim` | `src/daycare/sim_types.nim` | fork: `GameVersion`, the flatty wire types, the constants above. Field order is sacred, same as paintbot. |
| `src/ctf/sim.nim` | `src/daycare/sim.nim` | fork: the tick loop and the nine numbered steps replace the CTF gameplay core. |
| `src/ctf/sim_config.nim` | `src/daycare/sim_config.nim` | fork: `GameConfig` lifecycle + `config.update`; fields = the config schema in `## Packaging`. |
| `src/ctf/sim_state.nim` | `src/daycare/sim_state.nim` | fork: logging, `gameHash`, event emission, spawn placement, the two RNG sub-streams. |
| `src/ctf/arena.nim` | `src/daycare/yard.nim` | heavily reduced fork: the **fixed** 24×14 cell grid (fence, trees, shrubs, mat, spawns), the `mirror` reflection, and the BFS the kernels use. The terrain generator, `mapSpec`, symmetry machinery, validators, pixel queries and `map_pool` are **deleted** — Daycare has one authored yard per variant. |
| `src/ctf/global.nim` | `src/daycare/global.nim` | fork, heavily reduced: keep the sprite-protocol emitter, layer/object pooling, the chrome `TextMessage` smuggling and `boardRenderScaleFor`. **Delete** fog-of-war/FOV, first-person PiP, rig art, gun/grenade/spray/shield/barrier families, endzone bakes, perks and handicaps. |
| `src/ctf/broadcast.nim` | `src/daycare/broadcast.nim` | fork: `BroadcastTracker` + `buildStateJson` keep their shape; `teams` becomes the two roles, `roster` the two cogs, `lead` the score series, plus the appended `secret` block (`## Viewer`). |
| `src/ctf/events.nim` | `src/daycare/events.nim` | fork: the event vocabulary below (same `jsonRow`/`eventsJsonl` shape and the same "live emission and re-simulation must be byte-identical" rule). |
| `src/ctf/replays.nim`, `src/ctf/replay_runtime.nim` | `src/daycare/replays.nim` | rewritten: Daycare records **state frames**, not inputs (below). |
| `src/ctf/server.nim` | `src/daycare/server.nim` | fork of the route/artifact/shutdown skeleton; the player protocol becomes bullwhip's JSON frames. |
| `src/ctf/labels.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `roster.nim` | — | deleted. No articulated rigs, no perk roster, no generated terrain. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | kept, forked | still emits `window.CTF_WIRE={…}`. **The global keeps its name**: `client/chrome_common.js` reads `window.CTF_WIRE` at its line 72 and that file ships byte-for-byte, so renaming the global would force a byte change in a file that must not change. |
| `tools/` probes, `caos*`, `arena/` wit bindings, `client/league_replayer.html`, `tools/map_editor*`, `tools/record_*.sh`, `players/baseline/` | — | deleted. Keep `tools/build_replay_viewer.sh` and `tools/ci/`. |
| `ctf.nimble` | `daycare.nimble` | fork: binaries `daycare` and `daycare_player` → `/bin/daycare`, `/bin/daycare-player`. |

New files: `src/daycare/kernel.nim` (both kernels + BFS), `src/daycare/llm.nim` (from
`cogame-bullwhip/src/bullwhip/llm.nim`), `src/daycare/scripted.nim` (the two role-aware baselines),
`src/daycare.nim` (entrypoint, forked from `src/ctf.nim`: seed randomisation **before** `config.update`,
same sentinel handling), `src/daycare_player.nim` (from `cogame-bullwhip/src/bullwhip_player.nim`).

`tools/build_replay_viewer.sh` is paintbot's with the image tag renamed (`coworld-daycare-replay-viewer-build`),
the `docker cp` path changed to `/workspace/daycare/replay-viewer/dist/.` **and the inherited bug fixed**:
`mkdir -p` the output parent before the containment check, because the hook `cd`s into a parent that
`coworld build` pre-creates and CI does not (ecos, 2026-08-23).

### Event vocabulary (the replay's `events[]`)

One JSON row per event; `t` = tick, `seat` = slot, `f` = fruit species, `src` = source id.

| `k` | fields | when |
|---|---|---|
| `pick` | `t, seat, f, src, from` (`tall`\|`shrub`\|`ground`)`, x, y` | step 3, a successful pickup |
| `reach` | `t, seat, f, src, kind` (`tall`\|`shrub`)`, n` | step 3, a **failed** child attempt. Coalesced: the first failure at a source emits immediately, then at most one row per 8 ticks while the streak continues, with `n` = attempts since the last row. Uncoalesced this would be ~700 rows an episode. |
| `drop` | `t, seat, f, x, y, near` (`child`\|`basket`\|`floor`) | step 4 |
| `eat` | `t, seat, f, pref` (bool)`, pts` (3\|1) | step 5, the child ate |
| `waste` | `t, seat, f, x, y` | step 5, the parent ate |
| `rot` | `t, f, x, y` | step 7 |
| `ripen` | `t, src, f` | step 1 |
| `order` | `t, seat, turn, role, job, f, guess, source` (`llm`\|`retry`\|`fallback`\|`scripted`)`, hunch, notes, latencyMs` | one per seat per turn boundary |
| `guess` | `t, turn, guess, correct` (bool) | turn 1, and every turn the parent's `guess` **changes**. `correct` is spectator-side truth, never sent to a seat. |
| `switch` | `t, turn, from, to` | `daycare-fickle` only: the preference switched at this boundary |
| `turn` | `t, turn, scores[2], guess, guessCorrect, childAte[2], delivered[2], reaches[2]` (arrays indexed `[apple, banana]`) | each turn close |
| `end` | `t, reason, ending, scores[2], preference, guessTurnsCorrect, turns` | terminal |

Volume per episode: ~120 `ripen`, ~90 coalesced `reach`, ~40 `pick`/`drop`, ~25 `eat`, 30 `order`, 15
`turn`, plus incidentals — under 400 rows. `notes` is recorded (it makes an LLM seat's reasoning
auditable) and drawn only in the feed's expanded row; `hunch` is the headline. Both are already
rune-truncated.

### The replay file (`daycare.replay.v1`)

**Strict UTF-8 JSON, one document.** Daycare records *state*, not inputs, so playback never
re-simulates, a seek is an array index, and there is no native/wasm divergence to chase (which is also
why `#mmwarn` and `ctf_mismatch_tick` are dropped).

```json
{"protocol":"daycare.replay.v1","game":"daycare","gameVersion":"1",
 "seed":1234567,
 "names":["Alder","Bramble"],
 "policyNames":["daycare-attentive","daycare-caretaker"],
 "roles":["parent","child"],
 "colors":["blue","yellow"],
 "config":{"variant":"daycare-sparse","cols":24,"rows":14,"cell":48,"mirrored":false,
           "turns":15,"ticksPerTurn":48,"parScore":30,
           "fence":[[0,0],[1,0],"…"],
           "sources":[{"id":"T1","kind":"tall","fruit":"apple","cell":[4,2]},
                      {"id":"S1","kind":"shrub","fruit":"apple","cell":[9,5]},"…"],
           "basket":[[11,6],[12,6],[11,7],[12,7]],"basketCapacity":2,
           "spawns":[[12,9],[11,4]],
           "tallCapacity":3,"tallRegrowTicks":36,"shrubCapacity":1,"shrubRegrowTicks":240,
           "childShrubPickPermille":150,"childReachCooldownTicks":6,
           "fruitLifetime":120,"moveCooldown":2,"carryCap":1,
           "rewardPreferred":3,"rewardOther":1,"slot0Role":"parent"},
 "secret":{"preference":"banana","switchTurn":0},
 "frames":[{"t":0,"c":[12,9,-1,0,11,4,-1,0],
            "g":[17,4,1,86],
            "s":[2,0,1,3,"…one pair (ripe, regrowIn) per source in config order…"],
            "b":[0,1]}, "…720 frames…"],
 "series":{"score":[[0,0,0],[1,0,0],"…one row per tick: [t, parentScore, childScore]…"],
           "guessRight":[[0,1],[48,0],"…one row per turn boundary: [t, 0|1]…"]},
 "beats":[{"t":48,"k":"turn","n":1},{"t":96,"k":"guess","g":"banana","ok":true},
          {"t":288,"k":"feast","n":6},{"t":720,"k":"gameover"}],
 "events":[ "… the rows above …" ],
 "results":{ "… the results.json object verbatim …" }}
```

- **Self-sufficient by construction.** Aliases, policy names, roles, body colours, the full yard
  geometry, every rule constant, the seed, **the child's secret preference (and its switch turn)**,
  per-tick state, the score and guess series, the beat timeline, every event and the final results all
  live in these bytes. The viewer contacts **no** server except S3 for the `.replay` file. The `secret`
  block is what makes the idea's "reveal the child's secret preference to spectators" possible without a
  live server, and it is written **after** the episode, so no player process can ever read it.
- Frame encoding: `c` = 4 integers per cog (`x, y, carryFruitId, score`), `g` = 4 per ground fruit
  (`x, y, fruitId, ttl`), `s` = 2 per source (`ripe, regrowIn`) in `config.sources` order, `b` = mat
  counts `[apple, banana]`. Fruit ids are `0 apple, 1 banana`; `-1` = empty hand.
- Size arithmetic: 720 frames × ~40 integers ≈ **0.15 MB**, plus ~400 events ≈ 0.06 MB.
  `tests/test_replay.nim` asserts `< 8 MiB`.

---

## Server, player, protocol

### Game container (`/bin/daycare`)

Routes, kept from paintbot's `src/ctf/server.nim` because hosted certification probes exactly these
**before** the player pods start (lantern, 2026-08-23):

| route | behaviour |
|---|---|
| `GET /healthz` | `200 ok`, from process start until `shutdownGraceSeconds` after the artifacts are written |
| `GET /client/player?slot=N&token=T` | the seat's HTML shell (paintbot's, trimmed); it never opens the player socket |
| `WS /player?slot=N&token=T` | the seat socket; a bad token is refused with a close, never a hang |
| `GET /client/global` | the broadcast client (`client/replay_broadcast.html`, embedded with `staticRead`) |
| `WS /global` | live spectator: paintbot's sprite protocol + the chrome `TextMessage` |

`daycare.player.v1` frames, JSON text, bullwhip shapes:

- game → player: `{"type":"welcome","protocol":"daycare.player.v1","slot":N,"role":"parent","name":"Alder","turns":15,"ticksPerTurn":48,"variant":"…"}` on connect; the role-specific `state` frame from `## Decisions` at every turn boundary and at episode end; `{"type":"final","done":true,"slot":N,"scores":[…2…],"names":["Alder","Bramble"],"roles":["parent","child"],"turns":T,"reason":…,"ending":…}`, after which the player exits **0**.
- player → game: `{"type":"prompt","prompt":"<= 4000 chars","scripted":"caretaker|stubborn|"}`, sent
  immediately on connect and again after `welcome` (the re-send guards the slot-registration race). Any
  other frame is ignored with a log line.

The `final` frame carries **no** `preference` field: the child already knows it and the parent must never
learn it, not even at the buzzer, because a policy could otherwise log it and the anti-collusion pin
(preference seeded per episode) would be worth less. Spectators get it from the replay.

Startup: `src/daycare.nim` randomises the seed **before** `config.update` (paintbot's rule — every
seed-derived draw must follow the final seed), waits up to `playerConnectTimeoutSeconds = 120` for the
two sockets, starts anyway with whoever is there (a missing seat plays `caretaker`; **no** seat present
→ `forfeit`), then runs the turn loop.

Environment the game reads (from `tools/ci/docker_smoke.sh` and the platform): `COGAME_HOST`,
`COGAME_PORT`, `COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, plus `ANTHROPIC_API_KEY` / `ANTHROPIC_API_KEY_URI` and the Bedrock sidecar
pair. The player reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED`.

Shutdown, in this order (bullwhip's `finishEpisode` plus lantern's grace): send `final` to both player
sockets → broadcast the last global frame → `sleep 500 ms` → write `results.json` to `COGAME_RESULTS_URI`
→ write the replay to `COGAME_SAVE_REPLAY_URI` → keep `/healthz` and `/global` answering for
`shutdownGraceSeconds = 20` → `quit(0)`. The player's receive loop wraps `receiveMessage` in
`try/except CatchableError` and exits **0** on a closed or truncated frame (raid, 2026-08-23 — otherwise
`docker_smoke` passes and certification fails intermittently).

### `results.json`

```json
{"names":["daycare-attentive","daycare-caretaker"],
 "aliases":["Alder","Bramble"],
 "roles":["parent","child"],
 "scores":[41,41],
 "win":[true,true],
 "preference":"banana",
 "child_ate":[4,11],
 "delivered":[3,12],
 "wasted":[0,0],
 "reaches":[0,118],
 "guess_turns_correct":11,
 "turns":15,
 "par":30,
 "reason":"complete",
 "ending":"turn_limit"}
```

Arrays indexed by **slot**, always length 2, except `child_ate` and `delivered` which are indexed
`[apple, banana]` (also length 2). Field definitions, so nothing is guessed: `scores[i]` = the mirrored
consumption score (higher better, and equal by construction); `win[i] = scores[i] >= par`;
`preference` = the child's preference at the end of the episode (spectator/analysis only — it is in
`results`, which the platform stores, not in any player frame); `child_ate[f]` = fruit of species `f` the
child ate; `delivered[f]` = fruit of species `f` the parent dropped that the child then ate;
`wasted[i]` = fruit that seat ate as the parent (always `[n, 0]`); `reaches[i]` = failed pick attempts by
that seat; `guess_turns_correct` = turns whose parent `guess` equalled the live preference; `turns` =
turns completed. `names` are **policy** names (platform side); `aliases` go to the players and into the
replay's `names[]`.

---

## Viewer

**All four viewer files come from ONE starter: `Metta-AI/coworld-ctf`.** Named explicitly, because
splicing two starters' halves (one's `MODULARIZE`/`EXPORT_NAME` link flags onto the other's
`onRuntimeInitialized` bootstrap) is what left cogame-lantern with a permanently blank theater:

| file | source (coworld-ctf, one starter for all four) | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | verbatim except the emitted name (`daycare_replay.js`) and the export list renamed `_daycare_*`. **Keep the non-`MODULARIZE` link flags exactly as they are** — no `-s MODULARIZE=1`, no `EXPORT_NAME` — because the worker bootstraps with `Module.onRuntimeInitialized`. Keep `-O2 -s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--preload-file <root>/data@data`, `--mm:arc`, `--exceptions:goto` and `-d:useMalloc`. |
| the wasm entry `.nim` | `replay-viewer/ctf_replay.nim` → `replay-viewer/daycare_replay.nim` | same structure: `stampStage`, `daycare_load_replay`, `daycare_frame`, `daycare_input`, `daycare_packet_ptr/_len`, `daycare_error_ptr/_len`, `daycare_stage_ptr/_len`, and the `emscripten_exit_with_live_runtime()` epilogue (without it Nim's `main` destroys every global while JS keeps calling in). `daycare_load_replay` parses the JSON replay and hydrates the frame array; `daycare_frame` advances/seeks and rebuilds the viewer packet. `ctf_mismatch_tick` is **dropped** — there is no re-simulation to mismatch. **The packet built by `daycare_load_replay` is the only one carrying `meta`** (aliases, policy names, roles, config **and the `secret` block**); read it directly and never re-derive it via `packetAt(0)` (matrix-games, 2026-08-24). |
| `static_replay*.js` | `replay-viewer/static_replay.js` + `replay-viewer/static_replay_worker.js` | verbatim apart from the `ctf_*` → `daycare_*` export names, the worker name string, and **one added line** in `showFailure`: `document.documentElement.setAttribute('data-replay-error', error.message \|\| String(error))`. The worker keeps `importScripts('./wire_constants.js','./broadcast_core.js','./daycare_replay.js')` and `Module.onRuntimeInitialized` — the matched pair for the link flags above. |
| `index.html` | `client/replay_broadcast.html`, spliced by `Dockerfile.replay-viewer`'s `sed` into `replay-viewer/dist/index.html` | the starter's page with a game block appended (below). |

`static_replay.js` already sets `data-replay-loaded="true"` on `<html>` when the worker reports `loaded`
(its line 144); with the added failure line it sets **`data-replay-error`** on any failure. Those are the
two signals `tools/ci/viewer_smoke.mjs` and phase 60's `viewer-check.yml` read. If a `coworld-replay`
bridge `ready` message is posted at all, it is posted from a callback that fires **after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus, 2026-08-24). The
manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` and
`tools/build_replay_viewer.sh` is the `coworld build` hook that produces the bundle.
**Never a `/client/replay` pod.**

### Chrome provenance (exact)

- `client/chrome_common.js` is copied **byte-for-byte**. Nothing in it is edited — which is why the
  wire-constants global keeps the name `window.CTF_WIRE`, why the two role plates ride the starter's own
  `teams` / `roster` machinery, and why the score strip is fed through `ingestLeadSeries` /
  `renderMomentum` in the starter's own `lead` shape rather than a new one.
- `client/broadcast_core.js` is **forked** (it is paintbot's renderer — the playbook's "treat
  `client/renderer.js` as the exact template"): the board draw becomes the grass grid, fence, tall trees,
  shrubs, basket mat, ground fruit and the two cogs. Its ingest/packet plumbing, letterboxing and layer
  pooling are untouched.
- `client/replay_broadcast.html` is **the starter's page with a game block appended**, never a rewrite
  that reuses its ids. The only edits inside the starter's own markup/script are these three, and no
  others:
  1. **Removed elements** (with their CSS blocks and the JS branches that touch them):
     `#viewpanel` and its children `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`,
     `#zoom-slider`, `#zoom-in`, `#zoom-read`; `#fpv` and its children `#fpv-canvas`, `#fpv-hud`,
     `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`;
     `#povBadge`; `#mmwarn`.
     **Zoom decision: `#viewpanel` is dropped entirely.** The 24×14 board is fixed at 1152 × 672 and
     always fits the frame, so there is nothing to pan to and nothing a minimap could add; the zoom bar
     + minimap exist only for boards larger than the frame.
  2. **Two re-lettered literals**: the scorebug's `Lives` label becomes `Score`, and the momentum strip's
     label becomes `SCORE`.
  3. `#lockerroom` gains `pointer-events: none` so its ~1.5 s overlay stops swallowing transport clicks
     (ecos, 2026-08-23).
  Everything else — `#stage`, `#viewport`, `#board`, `#chrome`, `#scorebug`, `#plates-l`, `#plates-r`,
  `#clock`, `#clock-time`, `#clock-caption`, `#tick-clock`, `#bannerlane`, `#killfeed`, `#grain`,
  `#lightpool`, `#speedchips`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`, `#transport` and all seven
  transport buttons (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-skip`, `#btn-end`,
  `#btn-loop`) plus `#btn-spoilers`, `#scrub`, `#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`,
  `#scrub-head`, `#endcard` with `#ec-headline`/`#ec-how`/`#ec-teams`/`#ec-wincond`/`#ec-replay`, and
  `#status` — is the starter's, unchanged.
- **The appended game block** owns: the two role plates' sublines, the **secret panel** (below), the
  guess tape, the roster strip, the feed row builders, the beat-marker CSS, and the plate colours
  (`.plate.parent{--tc:#4a7ad6}`, `.plate.child{--tc:#e0b23c}` — unknown team keys fall back to the
  starter's `AMBER` constant in `buildFlag`, so nothing breaks if a rule is missed). Its beat builder is
  named **`buildCareBeats`**, never `markBeat`: a game-block `function markBeat` is hoisted over the
  chrome alias block's `var markBeat = C.markBeat` and silently kills every scrubber beat (tandem,
  2026-08-23). A scope-duplication test over the alias list enforces it.

### Transport rules

`relayout()` sets `--band` and `--hudscale` on `:root` (and `--topband` for the scorebug strip); every
chrome measure derives from `--u = 1px * var(--hudscale)`. **No overlay sits in the transport band**: the
secret panel, the guess tape, the roster strip, the feed and the banner lane are all clipped to the board
region between `var(--topband)` and `var(--band)`. The **endcard stops at `var(--band)`** (it is
`inset: var(--topband) 0 var(--band) 0`, the starter's own rule) and is dismissed by **every** seek.
Scrubber beats are clickable, labelled buttons — one per emitted kind, with CSS for **every** kind the
game emits: **`turn`, `guess`, `switch`, `feast`, `gameover`** (`feast` = a turn in which the child ate
≥ 2 preferred fruit; `switch` only exists in `daycare-fickle`). The whole beat timeline ships on the
first HUD frame (paintbot's `beats` field), so the scrubber is complete before playback starts, and
`?spoilers=0` still holds beats back until the playhead reaches them.

### What it draws

- **Board.** A tiled grass yard inside a wooden fence; **tall trees drawn 1.6 cells high** so "too tall"
  is legible at a glance, with a small ripe-fruit cluster in the canopy and a count pip; **shrubs** drawn
  knee-high with at most one berry; the **basket mat** as a woven mat with the fruit resting on it;
  ground fruit as 20 px sprites that blink in their last 24 ticks of `ttl`; the **parent** as a 40 px
  adult body in `blue` and the **child** as a 28 px body in `yellow`, each with its alias under the feet
  and the carried fruit drawn as a sprite **over the head**. A child reach plays the arms-up frame with a
  short grey "…" puff over the canopy — the single most important thing on screen, because it is the
  signal the parent is supposed to read. A `waste` puffs a grey cloud over the parent.
- **Scorebug** (`#scorebug` / `#plates-l` / `#plates-r`, paintbot's plate machinery, already 2-plate
  ready): two plates keyed `parent` and `child`. Headline = `PARENT` / `CHILD` (fed through
  `teams[k].policies = ["Parent"]`, the starter's own headline path); the big number = that seat's
  **score** (`lives-<k>`, label re-lettered `Score`); the subline = `ALDER · daycare-attentive`.
- **Secret panel** (appended, inside the board region, top-right, above the feed): two rows —
  `BRAMBLE WANTS: 🍌 BANANA` (the spectator reveal the idea asks for, read from `secret.preference` at
  the playhead, so in `daycare-fickle` it changes exactly when the preference does) and
  `ALDER GUESSES: 🍎 APPLE` with the state word **`RIGHT`** (green) or **`WRONG`** (red), plus
  `RIGHT 6 / 15 TURNS`. Under them, the **guess tape**: 15 small chips, one per turn, green when that
  turn's guess was correct, red when not, grey for turns not yet reached. This panel is the whole
  broadcast premise; it is always shown (the `?spoilers=0` flag governs *beats*, not the reveal), and it
  never overlaps the transport band.
- **Clock** (`#clock-time`, `#clock-caption`): `TURN 4 / 15`, caption `tick 192 of 720`. Spelled out,
  never `T4`.
- **Feed** (`#killfeed`, the starter's `pushFeed(row)` — one argument, the row element; the signature is
  the starter's and is not changed, which is what broke cogball 0.1.4): one row per `order` event
  (`ALDER → provide APPLE (guess APPLE) "It only reaches for apples"`, tagged `auto` when `source` is
  `fallback` or `scripted`), plus rows for `eat` (`BRAMBLE ATE BANANA +3`, `BRAMBLE ATE APPLE +1`),
  `reach` (`BRAMBLE REACHED FOR BANANAS ×8 — TOO TALL`), `drop` (`ALDER LEFT AN APPLE BESIDE BRAMBLE`),
  `waste` (`ALDER ATE THE APPLE — WASTED`), `rot` (`A BANANA ROTTED`), `guess`
  (`ALDER NOW GUESSES BANANA — RIGHT`) and `switch` (`BRAMBLE'S TASTE CHANGED: APPLE`).
- **Score strip** (`#momentum`, the SVG under the scrub track, label `SCORE`): the two stepped lines from
  `series.score`, fed exactly like paintbot's lives series —
  `state.lead = {"teams":["parent","child"], "pts":[[t, parentScore, childScore], …]}` — so
  `ingestLeadSeries` / `renderMomentum` in `client/chrome_common.js` need **no change**. The two lines
  coincide by construction, which is itself the visual statement that the parent is paid through the
  child.
- **Endcard**: the ending in words (`TURN LIMIT` / `TIME`), then
  `BRAMBLE WANTED BANANA · ALDER GUESSED RIGHT FROM TURN 3`, the two scores against par
  (`41 / 30 — PAR BEATEN`), and the line `12 bananas · 3 apples · 1 wasted · 118 reaches`.
- **Broadcast frame contract** (`buildStateJson`): the starter's `teams`, `roster` (2 entries, `name` =
  alias, `pol` = policy name, `s` = slot), `lead`, `beats`, `over`, plus the appended
  `secret: {"pref":"banana","guess":"apple","right":false,"tape":[1,1,0,…],"rightTurns":6}`.

**Legibility at 360 px is a requirement** — the featured-match iframe is ~360 px wide. `#stage.tiny`
(already switched on at `boardW <= 620`) shrinks the feed and pips; carry bullwhip's
`.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and hide plate sublines under 640 px so the plates
degrade to `PARENT 41`. Check at 360 px: both plates with their numbers, the `WANTS` / `GUESSES` rows with
their `RIGHT`/`WRONG` word, the guess tape (chips shrink to 6 px, still two-colour), the `TURN 4 / 15`
clock, and the newest two feed rows.

**Real art, not placeholders.** `scripts/art/gen_daycare_art.py` (Pillow, committed, deterministic)
renders and commits into `data/`: grass and path floor tiles, the fence tiles (`fence_h.png`,
`fence_v.png`, corners), tall apple and tall banana trees (3 canopy states: full / picked / bare), apple
and banana shrubs (ripe / bare), apple and banana fruit sprites (readable by **shape**, not only colour —
round vs crescent — so the guess is legible in greyscale), the basket mat, the parent body
(`cog_parent_front.png`, `_carry_apple.png`, `_carry_banana.png`), the child body (same three plus
`_reach.png`), the reach puff, the eat sparkle, and the loading screens the `#lockerroom` markup expects
(`client/art/lockerroom/bg.jpg` = a sunny yard, plus two portraits replacing the soldier `.webp`s).
`Dockerfile.replay-viewer`'s copy list and its `test -f` assertions are updated to those file names; the
`league.html` `sed` step, its two `grep -q` assertions and `client/league_replayer.html` are dropped with
it.

---

## Packaging

**`compose.yaml`** — one service, one image (game + player binaries):

```yaml
services:
  daycare:
    image: coworld-daycare:latest
    platform: linux/amd64
    build: {context: ., dockerfile: Dockerfile, network: host}
```

The service name is the single source of the manifest placeholder: `services.daycare` →
**`{{DAYCARE_IMAGE}}`** (lantern, 2026-08-23 — `coworld build` hard-fails anything else;
`tests/test_manifest.nim` asserts the derivation).

**`coworld_manifest_template.json`** — bullwhip's shape with the 0.1.42 strictness hive found: top-level
`$schema`, ≥ 3 `tags` (`daycare`, `cooperation`, `theory-of-mind`, `grid`, `llm-driven`, `melting-pot`,
`two-player`), top-level `episode_timeout_minutes: 20`, top-level `player[]`, `variants[].description` on
every variant, and a real JSON-Schema `game.config_schema` with `required: ["tokens"]` and
`minItems`/`maxItems` on **every** array property (tandem, 2026-08-23).

- `game.name`: `daycare`; `game.replay_viewer.bundle`: `static-replay-viewer`.
- `game.runnable`: `{"type":"game","image":"{{DAYCARE_IMAGE}}","run":["/bin/daycare"],
  "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/daycare/anthropic_api_key"},
  "source_url":"https://github.com/Metta-AI/cogame-daycare/tree/main"}` — the `env` entry is mandatory:
  without it the hosted game container never sees the coworld secret and every league episode silently
  plays scripted (hive, 2026-08-23), which surfaces only at phase 60 check 4.
- `game.config_schema` properties: `tokens` (string array, `minItems 1`, `maxItems 2`, required),
  `players` (array of `{name}`, `minItems 1`, `maxItems 2`), **`num_agents` (integer, 1..2, default 2)**,
  `seed`, `slot0Role` (enum `parent`\|`child`, default `parent`), `turns` (1..30, default 15),
  `ticksPerTurn` (12..120, default 48), `moveCooldown` (1..8, default 2), `carryCap` (1..2, default 1),
  `shrubs` (2..4, default 4), `tallCapacity` (1..8, default 3), `tallRegrowTicks` (6..240, default 36),
  `shrubCapacity` (1..4, default 1), `shrubRegrowTicks` (24..960, default 240),
  `childShrubPickPermille` (0..1000, default 250), `childReachCooldownTicks` (0..48, default 6),
  `fruitLifetime` (24..960, default 120), `basketCapacity` (0..4, default 2), `rewardPreferred` (1..10,
  default 3), `rewardOther` (0..10, default 1), `preferenceSwitch` (bool, default false),
  `llmTimeoutSeconds` (5..60, default 18), `minTurnSeconds` (0..60, default 8), `maxOutputTokens`
  (200..2000, default 600), `model` (string), `episodeTimeoutSeconds` (default 1200),
  `playerConnectTimeoutSeconds` (default 120), `shutdownGraceSeconds` (default 20), `showPlayerLabels`
  (bool, default true). `additionalProperties: false`.
- `game.results_schema`: the `results.json` object above — `required: ["names","scores","win","reason","ending"]`,
  every array `minItems: 2, maxItems: 2`, `reason` enum `["complete","deadline","forfeit"]`, `ending` enum
  `["turn_limit","deadline","forfeit"]`, `preference` enum `["apple","banana"]`.
- `game.docs` (**text**, not uri — bullwhip's shape, so the pages render without a network fetch):
  `{"readme":{"type":"text","value":"<what it is: two cogs in a yard; the child wants one of two fruits
  and cannot reach the tall trees; the parent can reach everything and is paid only when the child eats;
  there is no way to talk>"},
    "pages":[{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<the yard, the reach
      table, the nine-step tick order, the standing-order jobs, scoring and par, end conditions>"}},
             {"id":"policies.md","title":"Fielding a policy","content":{"type":"text","value":"<the
      per-role reply schema, the caps, the behaviour summary the parent gets, PLAYER_PROMPT /
      PLAYER_SCRIPTED how-to>"}}]}`. A manifest test asserts all three values are non-empty.
- `game.protocols` — **both**, as `{"type":"text","value":…}` objects (the platform validator rejects
  bare strings): `player` (the `daycare.player.v1` frames, the per-role observation, the reply schema and
  its caps) and `global` (the `/global` sprite + chrome frame, and the static bundle's
  `index.html?replay=<url>`).
- `player[]` — **exactly two entries**, both on `{{DAYCARE_IMAGE}}` with `run: ["/bin/daycare-player"]`:
  `daycare-caretaker` (`env: {"PLAYER_SCRIPTED":"caretaker"}`) and `daycare-stubborn`
  (`env: {"PLAYER_SCRIPTED":"stubborn"}`), each with
  `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}`. Two entries, not three:
  every declared player entry must occupy a certification slot (raid 0.1.2 → 0.1.3, `players_missing`) and
  this game has exactly **2** slots, so declaring a third runnable would make the fixture unsatisfiable.
  The champion prompt policies need no `player[]` entry — `coworld upload-policy` takes `run` + `env` from
  `tools/ci/policies.json`, as bullwhip's set does.
- **`variants[]` — four; `num_agents: 2` in every one**, and `players` is the two aliases in slot order in
  every one:

  | id | name | `shrubs` | `childShrubPickPermille` | `preferenceSwitch` | `slot0Role` | `num_agents` |
  |---|---|---|---|---|---|---|
  | `daycare` | Daycare | 4 | 250 | false | `parent` | **2** |
  | `daycare-sparse` | Daycare (sparse shrubs) | 2 | 150 | false | `parent` | **2** |
  | `daycare-fickle` | Daycare (changing taste) | 4 | 250 | **true** | `parent` | **2** |
  | `daycare-swapped` | Daycare (child in seat 0) | 4 | 250 | false | **`child`** | **2** |

  All four share `turns: 15, ticksPerTurn: 48` and the constants above. In `daycare-fickle` the switch
  turn is drawn from `rngSecret` uniformly in `6..9`, so the parent has time to be right, then wrong, then
  right again — the best 30 seconds of television this game can make. **The league default variant is
  `daycare-sparse`** — with the child barely able to self-feed, the parent's read is nearly the whole
  score, which is where an LLM champion visibly outplays a filler; phase 50 passes it as
  `default_variant_id` at seed time (gridlock, 2026-08-23: the variant is chosen at seed time or not
  cheaply again).
- `certification`:
  `game_config` = `{num_agents: 2, seed: 7, turns: 6, ticksPerTurn: 48, shrubs: 4,
  childShrubPickPermille: 250, minTurnSeconds: 0, playerConnectTimeoutSeconds: 120,
  players: [{"name":"Alder"},{"name":"Bramble"}]}` and `players` =
  `["daycare-caretaker","daycare-stubborn"]` — **both declared player entries seated**, because
  `players-run` seats the whole roster and a fixture that omits one fails `players_missing` (raid,
  2026-08-23). Slot 0 (`caretaker`) is the parent, so the fixture produces a real, non-zero, readable
  episode. **6 × 48 = 288 ticks = 12 s of video**, which outlasts the 10 s viewer soak (ecos,
  2026-08-23), and with `minTurnSeconds: 0` and no credentials it runs in a couple of seconds — well
  inside `coworld certify`'s 60 s default (`grace + rounds × pacing + linger < 50 s`, commons-family,
  2026-08-24).

**Other packaging files:** `Dockerfile` (paintbot's two-stage nimby build; produces `/bin/daycare` and
`/bin/daycare-player`), `Dockerfile.replay-viewer` (paintbot's, with the daycare file list and the same
`test -f` assertions, minus `league.html`), `tools/build_replay_viewer.sh` (paintbot's, image tag renamed,
`mkdir -p` fix), `.github/workflows/ci.yml` and `coworld-release.yml` copied from
`coworld-builder/templates/`, `tools/ci/docker_smoke.sh` with `<slug>` = `daycare`, `<IMAGE>` =
`coworld-daycare` and **`<SEATS>` substituted to 2**, `tools/ci/viewer_smoke.mjs` copied **verbatim**,
`tools/ci/renderer_fixture.html`, and `tools/ci/policies.json` naming the two champions
`daycare-attentive` and `daycare-provider` (both `PLAYER_PROMPT`, each with
`env: {"USE_BEDROCK":"true"}` — without it the platform gives the player pod no Bedrock sidecar and the
seat silently plays scripted, cogolf 2026-08-24) plus the two fillers `daycare-caretaker` and
`daycare-stubborn` (`PLAYER_SCRIPTED`).

---

## Tests

All run in `ci.yml`; the sandbox cannot run any of them locally.

1. **`tests/test_sim.nim` — sim units.** The reach table (parent picks a tall tree always; the child's
   tall-tree pick **always** fails and emits `reach`; the child's shrub pick succeeds at exactly
   `childShrubPickPermille` over 10 000 seeded attempts ±1 %; a failed shrub pick starts a 6-tick fumble
   during which every action degrades to `wait`); ground pickup always succeeds for both roles;
   `carryCap 1`; `drop` refused onto an occupied cell and onto a full mat; mat fruit never rots and floor
   fruit rots at exactly `fruitLifetime`; `eat` scores `3` / `1` for the child and `0` + `waste` for the
   parent, and credits **both** seats identically; regrow at exactly `tallRegrowTicks` /
   `shrubRegrowTicks` and capped at capacity; move cooldown; the two cogs cannot share a cell and the
   lower slot wins; trees/shrubs/fence are impassable; BFS determinism (the same state yields the same
   path twice); the `daycare-fickle` switch fires exactly once, at a turn boundary in `6..9`;
   **determinism** — the same seed and the same order script produce an identical `gameHash` after 720
   ticks, twice in one process and across a fresh server.
2. **`tests/test_noleak.nim` — the hidden preference is actually hidden.** (a) The parent's `state` frame
   bytes, at every turn boundary of a full episode, contain neither the string `preference` nor the
   preference value in any field the parent reads, nor the child's `hunch` or `notes`; (b) the same for
   the child's frame with respect to the parent's `guess`, `hunch` and `notes`; (c) `layoutHash(seed)` is
   **identical** whether the preference is forced to `apple` or `banana` — the layout comes from
   `rngLayout`, the preference from `rngSecret`; (d) the apple source set maps exactly onto the banana
   source set under `x → 23 − x`, in both mirror states and in all four variants; (e) the `final` frame
   carries no `preference` key.
3. **`tests/test_baseline.nim` — bounded orders / legality.** For 12 seeds × 720 ticks on all four
   variants, for each of the four baseline pairings (`caretaker`/`caretaker`, `caretaker`/`stubborn`,
   `stubborn`/`caretaker`, `stubborn`/`stubborn`): every emitted order's `job` is inside **that role's**
   enum, `fruit` is inside the species enum wherever required, the parent emits a legal `guess` every
   turn; every per-tick action is one of the eight vocabulary values; no cog is ever outside the yard,
   inside fence/tree/shrub, or sharing a cell; no cog carries more than one fruit; no score, `ripe` or
   `ttl` goes negative; `ripe` never exceeds capacity; the mat never exceeds `basketCapacity`; neither
   baseline raises, and neither takes more than 1 ms per turn.
4. **`tests/test_feasibility.nim` — the oracle, as a CI precondition.** Gates (a)–(f) of `## The game`,
   over seeds 1..12 on all four variants, including the test-only `idle` and `hedge` parent kernels for
   gates (d) and (e). Any constant change that breaks the economy — or that makes the parent's inference
   pointless — fails here rather than in a dead replay.
5. **`tests/test_replay.nim` — end-to-end + strict UTF-8.** Plays a full scripted episode headless,
   writes `results.json` and the replay, then re-reads the replay **bytes**: `validateUtf8 == -1`
   (strict), parses as JSON, `protocol == "daycare.replay.v1"`, `frames.len == ticksPlayed`,
   `series.score.len == ticksPlayed`, `series.guessRight.len == turnsPlayed`, `secret.preference` present
   and in the species enum, every event tick in `0..ticksPlayed`, at least one `pick`, `reach`, `drop` and
   `eat`, exactly `turns` `turn` events and exactly one `end`, `results.scores.len == 2` and
   `scores[0] == scores[1]`, `results.reason` in `{complete, deadline, forfeit}`, `results.ending` in
   `{turn_limit, deadline, forfeit}`, file size `< 8 MiB`. A seat is fed a `hunch`/`notes` of multi-byte
   runes exactly at the 80/240 caps and the recorded strings are asserted valid UTF-8 and ≤ the cap (the
   bullwhip byte-truncation bug).
6. **`tests/test_llm.nim` — decision layer.** `extractJsonObject` on fenced and prose-prefixed replies; a
   parent reply with a child-only `job` → invalid; a parent reply missing `guess` → invalid; `provide`
   without `fruit` → invalid; a `guess` that disagrees with `fruit` → **accepted** (hypothesis-testing
   must stay expressible); a stubbed transport that times out, 429s, 403s or returns junk produces
   `caretaker` orders for those seats, never raises, and marks `source: "fallback"`; **one batch carries
   both open seats** (assert `RequestBatch.len == openSeats`, i.e. 2 on turn 1); `minTurnSeconds` floors
   the spacing between batch starts.
7. **`tests/test_manifest.nim` — packaging.** `num_agents == 2` in **all four** variants and in
   `certification.game_config`; the image placeholder equals the one derived from `compose.yaml`'s service
   name (`{{DAYCARE_IMAGE}}`); `replay_viewer.bundle == "static-replay-viewer"`; `game.docs.readme`
   non-empty + non-empty `pages`; `game.protocols.player` **and** `global` present and both
   `{"type":"text",…}` objects; `ANTHROPIC_API_KEY_URI` in `game.runnable.env`; **every** `player[]` id
   appears at least once in `certification.players`; `episode_timeout_minutes` top-level; every array
   property in `config_schema` carries `minItems` **and** `maxItems`; `results_schema` arrays are all
   `minItems 2, maxItems 2`.
8. **`tests/test_broadcast.nim` — chrome frame.** `teams` keys are exactly `parent` and `child`, each
   carrying `policies: ["Parent"|"Child"]`, `lives` = that seat's score; `roster[]` has 2 entries carrying
   the alias in `name` and the **policy** name in `pol`; `lead.teams` / `lead.pts` shape matches
   `chrome_common.js`'s expectation (`[t, parent, child]` rows); the appended `secret` block carries
   `pref`, `guess`, `right`, `rightTurns` and a `tape` of length `turns`; `beats` carries only the five
   declared kinds; `over` is present on the terminal frame with the ending string; every feed row's text
   is ≤ the caps; and a **scope-duplication test** asserts no game-block function name collides with the
   chrome alias list (`markBeat` et al., tandem).
9. **`docker-smoke` (`tools/ci/docker_smoke.sh`, `<SEATS>` = 2).** Builds the image, runs a real 2-seat
   episode in containers off the cert fixture, asserts **both player containers exit 0** (raid,
   2026-08-23) as well as the game, validates `results.json` against the results schema, and copies the
   replay to `SMOKE_REPLAY_OUT` (`dist/smoke/replay.json`), uploaded as the `smoke-replay` artifact.
10. **`wasm-viewer` job — the bundle is EXECUTED, not merely built.** `needs: docker-smoke`, downloads
    `smoke-replay`, builds the bundle via `tools/build_replay_viewer.sh`, installs Playwright pinned
    **1.55.0**, and runs **`tools/ci/viewer_smoke.mjs`** against that replay over local HTTP with
    `--strict-text-bounds` (fixed arena → `canvas_text.never_inside` must be 0) and `--soak` (the 12 s
    cert replay outlasts the 10 s window). Pass requires `data-replay-loaded="true"` **and** three
    different clock readouts at 0 %, 50 % and 100 %; `data-replay-error` or silence fails the job.
    Evidence (`viewer-smoke.png`, `viewer-smoke.json`) uploads on success and failure. A second step in
    the same job runs `viewer_smoke.mjs --strict-text-bounds` against **`tools/ci/renderer_fixture.html`**
    — the worst-case renderer fixture that loads the real renderer with a full-cap 80-char `hunch` and
    240-char `notes` on **both** seats, the guess tape at 15 chips, and the secret panel at several canvas
    sizes including 360 px, because `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY` and therefore
    produces a replay with zero LLM text (cogchemists, 2026-08-24).

---

## Out of scope (v1)

- **Per-tick policy sockets.** A seat submits one standing order per 48-tick turn; the kernel emits the
  per-tick grid actions. A direct per-tick action channel for RL/vector policies is not shipped.
- **Any explicit channel between the seats.** No `say`, no gestures with a fixed meaning, no shared
  memory, no field of one seat's reply reaching the other. `hunch` is spectator-only, `notes` is private.
  The absence is the game.
- **A third fruit species.** Apple and banana, exactly as the idea names. `plum`, preference *intensities*
  and multi-species preference vectors are all out.
- **Preference revealed at the buzzer.** The parent never learns the answer, not even in the `final`
  frame; only the replay and `results.json` carry it.
- **More than two seats.** No siblings, no second parent, no daycare full of children. `num_agents` is 2
  in every variant.
- **Hunger, health, growth or any child-state meter.** The child does not starve, cannot die and does not
  grow up; a fruit not eaten is only a point not scored.
- **Theft, blocking, doors, combat.** Neither cog can take fruit from the other's hand or damage the
  other; they interact only through the ground, the basket and what each can see the other doing.
- **Fog of war / partial observation of the yard.** The whole yard is visible to both seats; paintbot's
  FOV, first-person PiP and POV lens are deleted, not repurposed. The only hidden state in this game is
  the preference and the other seat's pending order.
- **Procedural yards.** One authored 24×14 layout, mirrored or not. Paintbot's terrain generator,
  `mapSpec`, map pool, map editor and all its style machinery are deleted.
- **Cross-episode persistence.** Every episode redraws the preference from its own seed; nothing carries
  over except the league rating.
- **Re-simulating playback.** The viewer decodes recorded state; there is no replay-hash mismatch mode,
  no `--mismatch-quit`, and no `#mmwarn`.
- **Achievements, perks, handicaps, the league replayer page.** All inherited paintbot machinery, all
  deleted rather than carried dark.
