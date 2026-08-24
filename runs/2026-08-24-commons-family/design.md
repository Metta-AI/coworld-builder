# Commons Family — design note (2026-08-24)

Repo: `Metta-AI/cogame-commons-family` (public). Coworld/game name `commons_family`, slug
`commons-family`, page `https://softmax.com/commons-family`. In the new repo this note lives at
`docs/plans/2026-08-24-commons-family-design.md`.

**Starter: `Metta-AI/coworld-meadow`** (not mounted; cloned read-only to `/tmp/coworld-meadow` and
read in full — `README.md`, `src/coworld/examples/meadow/README.md`, `game/engine.py` (309 lines),
`game/server.py` (327), `player/policies.py` (335), `player/player.py`, `grader/meadow_grader.py`,
`headless.py`, `game/docs/player_protocol_spec.md`, `game/docs/global_protocol_spec.md`,
`coworld_manifest_template.json` (383), `compose.yaml`, `Dockerfile`,
`tools/build_replay_viewer.sh`, `static-replay-viewer/index.html`, `game/client/*.html`,
`tests/test_meadow_engine.py`, `shared/artifact_io.py`). It is the starter because the idea pins
it and because the institutional layer this coworld is *about* — public ledger, costly sanctions,
posted norms, chat, welfare-against-a-computed-optimum grading — already exists there as working
code we extend rather than re-derive. **Every convention there holds here unless this note says
otherwise.** Where meadow is silent or wrong for us — it has **no wasm replay viewer** (its
`static-replay-viewer/index.html` is a hand-written single-file HTML player, not a bundle with a
wasm module), **no `num_agents` anywhere in its manifest**, no `.github/workflows`, no
`tools/ci/`, and it leaks real player names into the in-game ledger — this note names
**`Metta-AI/cogame-bullwhip`** (mounted at `/workspace/starters/cogame-bullwhip`, read in full)
as the **single** starter for all four viewer files plus the chrome, and coworld-builder
`templates/` for CI. `Metta-AI/cogame-babel` (`/workspace/starters/cogame-babel`) was read too
and is not used; §Viewer says why.

---

**Source idea (verbatim):**

```
EXTENSION of Metta-AI/coworld-meadow — Meadow is a live round-based commons coworld built to measure how LLM societies handle a destructible shared resource under reputation, costly punishment, posted norms and chat, scored against a computed social optimum. Melting Pot's four commons substrates are different resource dynamics on top of exactly that institutional layer, so they become Meadow resource modules rather than new worlds (Meadow keeps its chat/norms/punishment toggles; each module defines the resource physics):
    Clean Up: apple orchard + river that silts up; apple regrowth falls with pollution; cleaning is a local action away from the apples; zap = punishment. Public goods with physical opportunity cost.
    Commons Harvest (open / closed / partnership): apples regrow only while a patch keeps ≥1 apple; strip it and it's dead forever; closed rooms give single-cog excludability, partnership rooms need two cogs to hold. Property rights as an A/B.
    Allelopathic Harvest: three berry colours that inhibit each other's growth; every cog has a secret favourite; replanting is costly. Heterogeneous-preference commons — the good outcome needs a majority to give up its preference.
    Externality Mushrooms: red = +1 to eater, green = +2 split among all, blue = +3 split among everyone except the eater; digestion freezes; regrowth depends on what's eaten. The instant-externality control case.


Seats: 5-8 (Meadow's range)
Motive: social dilemma / public goods, with and without institutions
Policy interface: Meadow's existing round-based prompt protocol; spatial modules (Clean Up, Harvest) need a small grid layer — decide whether Meadow gets a grid or these run at Meadow's abstract-round granularity (the latter preserves exact solvability, which is Meadow's selling point).
Integrity (anti-collusion): Meadow's existing reputation/sanction instrumentation + resident/visitor scoring with scripted free-rider / cleaner / punisher bots.
Replay plan (watchability): Meadow's replay + per-module overlays (pollution gradient, dead-patch tombstones, colour-share bar, reward particles to whoever a bite pays).

Absorbed cards: MP Clean Up, MP Commons Harvest, MP Allelopathic Harvest, MP Externality Mushrooms.
Source: meltingpot clean_up, commons_harvest__*, allelopathic_harvest(_open), externality_mushrooms(_dense); github.com/Metta-AI/coworld-meadow.
```

---

## The game

Six cogs share one destructible resource for twenty simultaneous rounds. Every round each cog
splits **three units of effort** between taking from the resource and doing the thing that keeps
the resource alive, then everyone's choices settle at once. The resource physics come from one of
four **modules**; the institutions around them — a public ledger of who took what, costly
punishment, a posted norm, and one signed chat line per cog per round — are meadow's, unchanged,
and are switched per variant. Taking pays you. Maintaining pays everyone, including the cogs who
did not maintain. That is the entire game, four times over.

**The granularity is meadow's abstract round, not a grid. This is settled, not open.** The idea
names it as the reading that preserves exact solvability, and the coordinator pinned it. A Clean
Up cog does not walk to the river; it spends one of its three effort units on `clean`, which is
the same opportunity cost expressed as a number. A Commons Harvest cog does not stand in a room;
it names a `patch`, and the room's excludability is a rule about who may name it. No module in
this repo has positions, movement, sight, or ticks.

### Seats

**`num_agents` = 6.** One number, no range. It appears in **every** manifest variant's
`game_config`, in `certification.game_config`, in `config_schema.properties.num_agents`
(`minimum: 6, maximum: 6`), and as `SMOKE_SEATS=6` in `tools/ci/docker_smoke.sh`. Reasoning:
6 is inside meadow's 5–8 range, it is divisible by 2 (Commons Harvest *partnership* needs whole
pairs) and by 3 (Allelopathic needs the three secret favourites handed out evenly — two cogs per
colour, so no colour is a natural majority), and it keeps Externality Mushrooms' blue split
(3 ÷ (N−1) = 0.6 each) a clean number that beats red (1.0 to the eater) on welfare by 3× while
losing to it privately, which is the tension the module exists to measure. Six seats also means
six LLM requests per round, which sizes the round budget below (§Decisions).

### The four modules

Four resource physics, one institutional layer, one repo. Each module is a `game_config.module`
value and ships as manifest variants (six of them — Commons Harvest ships its property-rights
A/B as three separate variants, because the A/B *is* the finding):

| module | the resource | the extractive act | the maintenance act | the trap |
|---|---|---|---|---|
| `cleanup` | one apple stock + one pollution level | `harvest` apples | `clean` the river | cleaning pays nothing; unclean → apples stop regrowing |
| `harvest` | six independent apple patches | `harvest` from a named `patch` | leaving ≥ 1 apple in a patch | a stripped patch is dead **forever** |
| `allelopathic` | 60 plant slots in three colours + ripeness | `eat` ripe berries of a colour | `plant` (convert a slot to a colour) | ripening scales with a colour's **share**, so a split field starves everyone; your favourite pays double, so agreeing on one colour costs four of the six cogs |
| `mushrooms` | red / green / blue mushroom counts | `eat` a colour | eating green or blue | red pays you 1, green pays the group 2, blue pays *everyone but you* 3; eating freezes you for as many rounds as you ate |

### Rules, complete

Everything below is exact. `N = 6` throughout. All quantities are floats unless stated; demands
are integers.

**Shared per-round contract.** Each cog gets `effort_budget = 3` units per round and submits one
decision (§Server, player, protocol). Common fields: `sanction` (a slot to punish, when
`sanctions_enabled`), `message` (one public chat line), `note` (private, echoed back to that cog
next round). Sanctions cost the payer `sanction_cost = 1.0` and burn `sanction_burn = 3.0` from
the target — meadow's numbers, unchanged, and welfare-negative on purpose.

**Module `cleanup`.** `apples` starts at 60.0, capacity 100.0, `regrowth_rate = 0.35`,
`collapse_threshold = 10.0` (meadow's constants). `pollution` ∈ [0, 1] starts at 0.30,
`silt_rate = 0.12` per round, `clean_power = 0.05` per clean unit. Decision fields: `harvest`
(0..3) and `clean` (0..3) with `harvest + clean ≤ 3`. Effective regrowth is
`regrowth_rate × (1 − pollution)`; at the starting pollution the sustainable aggregate near
half capacity is `0.35 × 0.70 × 100 / 4 = 6.1` apples per round for six cogs — about one each,
deliberately the same shape as meadow's headline number. Holding pollution steady costs
`0.12 / 0.05 = 2.4` clean units per round, i.e. 13 % of the society's total effort, permanently,
paid by whoever volunteers. Below `collapse_threshold` the orchard is dead **forever** (meadow's
latch, unchanged): no regrowth for the rest of the episode, remaining apples can still be
scavenged.

**Module `harvest`.** `patch_count = 6` independent patches, each `patch_capacity = 20.0`,
`patch_start = 12.0`, `patch_regrowth = 0.40`. Decision fields: `patch` (0..5) and `harvest`
(0..3). A patch with stock < 1.0 after harvest is **dead**: stock set to 0.0, `dead = true`, no
regrowth ever, a tombstone in the viewer. A live patch regrows logistically. Sustainable per
patch is `0.40 × 20 / 4 = 2.0` per round, 12.0 across the six patches, i.e. 2 per cog against a
cap of 3 — the temptation is exactly one unit wide. `property_rights` selects the room type:

- `open` — any cog may name any patch.
- `closed` — patch *p* belongs to the cog in seat `owner[p]`, a seeded 1:1 permutation of the six
  seats onto the six patches, **public** to everyone. A demand by a non-owner yields nothing and
  writes a `trespass` event. (The deal is `owner[p] = patch_deal[p] mod num_agents`, and it is a
  1:1 permutation *because* every shipped variant has `patch_count == num_agents == 6` — the
  manifest pins `num_agents` at 6..6 and `patch_count` at 6 in all six variants. The modulo is
  what keeps a hand-edited `game_config` legal rather than merely lucky: every patch still has
  exactly one owner and every allowed set stays inside the patch range, seats just own two patches
  or none. A parametrised test plays 3, 6 and 12 patches through all three rights.)
- `partnership` — the six patches are dealt to three seeded pairs, two patches per pair, **public**.
  A patch yields this round only if **both** partners named it this round (either may demand 0 —
  naming it is "holding" it). Otherwise every demand on it yields nothing and writes an `unheld`
  event. **A seat that did not answer names nothing**: a pass, a `no_submission` and a seat that
  never connected all arrive as the all-zero default decision, and counting that default as
  "holding patch 0" would let an absent seat's partner harvest patch 0 alone every round while the
  pair's other patch could never be held at all. The resolver skips a decision whose `src` is
  `pass` — it names no patch, it cannot trespass, and it draws no `unheld` event of its own.

**Module `allelopathic`.** `field_size = 60` plant slots; colours `red`, `green`, `blue` in that
canonical order. `planted` starts 20/20/20, `ripe` starts 6/6/6, `ripen_base = 0.5`. Every cog is
dealt a **secret favourite** colour from the seed, exactly two cogs per colour. Decision fields:
`eat` (0..3) with `eat_color`, `plant` (0..3) with `plant_color`, `eat + plant ≤ 3`. A berry pays
its eater **2.0 if it is that cog's favourite colour, else 1.0**. Planting pays nothing at all;
its cost is the effort unit it consumes (this is the idea's "replanting is costly", expressed as
opportunity cost so the module stays exactly solvable). Ripening per round is
`ripe[c] ← min(planted[c], ripe[c] + 0.5 × planted[c]² / field_size)` — quadratic in the colour's
own share, which is the inhibition: at 20/20/20 the whole field yields 10.0 berries per round for
six cogs with 18 units of demand; at a 60-slot monoculture it yields 30.0 and nobody is ever
short. The good outcome needs four of six cogs to eat a colour that pays them 1.0 instead of 2.0.

**Module `mushrooms`.** Counts start 8/8/8, `mushroom_capacity = 30` total and 15 per colour,
`spawn_per_round = 3`. Decision fields: `eat` (0..3) with `eat_color`. Payoffs per mushroom
eaten: **red** → +1.0 to the eater; **green** → +2.0 split equally among all six cogs
(+0.3333… each, eater included); **blue** → +3.0 split among the five cogs who did **not** eat it
(+0.6 each, eater gets nothing). Digestion freezes: a cog that ate `k` mushrooms in round *r*
may not eat again until round `r + ceil(k)` (so k = 1 costs nothing, k = 3 skips two rounds); a
frozen cog's eat demand is voided with a `digesting` event, and it may still chat and sanction.
Regrowth follows appetite: spawn weights are `w[c] = 1 + eaten_total[c]` (episode-cumulative),
`spawn_per_round = 3` new mushrooms are apportioned by largest remainder with ties broken in
canonical colour order, then clamped to the per-colour and total caps (excess dropped from the
largest colour first, ties in canonical order). Welfare-optimal play is a blue chain; privately
optimal play is red; green is the compromise. Nothing here can collapse permanently — this is the
control case, and it is meant to be the module where institutions have the least excuse.

### Turn structure and the exact resolution order

One round = one simultaneous decision from every seat. For round *r* (0-indexed) the engine
executes exactly this order. Ties everywhere resolve by ascending slot, then canonical colour
order (`red`, `green`, `blue`), then ascending patch index. Nothing in this list is
order-independent, so this list is the specification.

1. **Open.** Snapshot the pre-round module state, compute one observation per seat (§Per-seat
   observation), write a `round_open` event carrying the public state.
2. **Decide.** The game issues **one parallel batch** of LLM requests covering every prompt seat
   (§Decisions) and evaluates every scripted seat in-process against the same observation. The
   round's hard deadline is `round_seconds = 20 s` from step 1; a pacing floor of
   `min_round_seconds = 3 s` keeps an all-scripted episode watchable and rate-safe.
3. **Validate.** Each reply becomes a `Decision` clamped to bounds: integers to their ranges,
   colours to the enum, `patch` to `0..patch_count-1`, the effort budget enforced by reducing the
   *maintenance* field first and the extractive field second, `sanction` dropped unless
   `sanctions_enabled` and `0 ≤ target < N` and `target ≠ self`, free text truncated on rune
   boundaries. A seat that timed out or produced garbage twice takes its fallback baseline's
   decision and gets a `fallback` event; a seat with no policy at all passes (all zeros) and gets
   a `no_submission` event.
4. **Publish chat.** Messages are attached to round *r* and become visible in round *r+1*'s
   observation. They are never visible within their own round — decisions are simultaneous, and a
   protocol that let one cog read another's line before deciding would not be. One `chat` event
   per non-empty message.
5. **Resolve the module** (below), producing `gain[i] ≥ 0` for every seat and the module's events.
6. **Apply sanctions**, ascending slot: payer `scores[by] -= sanction_cost`, target
   `scores[target] -= sanction_burn`, `sanctions_given/received` incremented, one `sanction` event
   each. (Scores are additive, so this cannot change step 5's splits; the order is fixed anyway so
   two implementations cannot differ.)
7. **Run resource dynamics** (regrowth / pollution / ripening / spawn — below), latching any
   permanent death.
8. **Book the round.** `scores[i] += gain[i]`; update ledger totals; append the settled
   `RoundRecord`; write `round_end`.
9. **Deadline guard.** If `now > play_deadline` (§Decisions), settle immediately with
   `reason: "deadline"`.
10. If `r + 1 == rounds`, settle with `reason: "complete"`.

**Step 5, module `cleanup`:**

1. Clamp `clean_i + harvest_i ≤ 3`, reducing `clean` first.
2. `D = Σ harvest_i`. If `D ≤ apples`, `gain_i = harvest_i`; else `gain_i = harvest_i × apples / D`.
3. `apples -= Σ gain_i`.
4. `pollution = clamp(pollution + silt_rate − clean_power × Σ clean_i, 0.0, 1.0)`. Silting happens
   every round, cleaning or not.

**Step 7, `cleanup`:** if not already dead and `apples < collapse_threshold`, latch
`dead = true`, record `collapse_round = r`, write `collapse`, and never regrow again. Otherwise
`apples = min(capacity, apples + regrowth_rate × (1 − pollution) × apples × (1 − apples/capacity))`.

**Step 5, module `harvest`:**

1. Void every demand aimed at a dead patch (`void` event, `cause: "dead"`); in `closed`, every
   demand by a non-owner (`trespass`); in `partnership`, every demand on a patch not named by both
   partners this round (`unheld`).
2. Per patch, ascending index: `D_p = Σ` surviving demands. If `D_p ≤ stock_p`,
   `gain = demand`; else pro-rata `demand × stock_p / D_p`.
3. `stock_p -= Σ gains`.

**Step 7, `harvest`:** per patch, ascending index: if `stock_p < 1.0`, set `stock_p = 0.0`,
`dead = true`, write `patch_dead`, never regrow; else
`stock_p = min(patch_capacity, stock_p + patch_regrowth × stock_p × (1 − stock_p/patch_capacity))`.

**Step 5, module `allelopathic`:**

1. Clamp `eat_i + plant_i ≤ 3`, reducing `plant` first.
2. Eating, per colour in canonical order: `D_c = Σ eat_i` over seats naming *c*. If
   `D_c ≤ ripe[c]`, `berries_i = eat_i`; else pro-rata. `ripe[c] -= Σ berries`.
3. `gain_i = Σ_c berries_{i,c} × (2.0 if c == favourite_i else 1.0)`.
4. Planting, ascending slot, one unit at a time: the source colour is the colour with the largest
   `planted` among colours ≠ `plant_color` (ties canonical). If the source has 0 slots the unit is
   void. Otherwise `planted[source] -= 1`, `planted[target] += 1`, and if
   `ripe[source] > planted[source]` then `ripe[source] = planted[source]` — a converted slot takes
   its ripe berry with it. Planting yields no score.

**Step 7, `allelopathic`:** per colour, canonical order,
`ripe[c] = min(planted[c], ripe[c] + ripen_base × planted[c]² / field_size)`. If the whole field's
ripe total is 0.0 after this, write a `barren` event (informational; the field can always recover,
so there is no permanent death in this module).

**Step 5, module `mushrooms`:**

1. Void the eat demand of every seat with `r < frozen_until_i` (`digesting` event).
2. Per colour, canonical order: `D_c = Σ` surviving demands for *c*. If `D_c ≤ count[c]`,
   `eaten_{i,c} = demand`; else pro-rata. `count[c] -= Σ eaten`.
3. Payoffs, ascending slot then canonical colour, with `k = eaten_{i,c}`: red → `gain_i += 1.0×k`;
   green → every seat *j* gets `gain_j += 2.0×k/N`; blue → every seat `j ≠ i` gets
   `gain_j += 3.0×k/(N−1)`.
4. `k_i = Σ_c eaten_{i,c}`; if `k_i > 0` then `frozen_until_i = r + ceil(k_i)`.

**Step 7, `mushrooms`:** `w[c] = 1 + eaten_total[c]`; apportion `spawn_per_round = 3` by largest
remainder (ties canonical); `count[c] += alloc[c]`; clamp each colour to 15 and the total to 30,
dropping excess from the largest colour first. `eaten_total[c] +=` this round's total per colour is
booked in **step 5**, where the eating happens and the numbers are in hand, and step 7 reads the
already-updated totals — the spawn weights are exactly the same either way, and the accumulator
lives next to the thing it counts. `tests/test_modules.py` asserts the totals after `resolve`.

### Scoring, sign, and what the league ranks by

```
gain_i(r)  = the module payoff in step 5 of round r          (always ≥ 0)
score_i    = Σ_r gain_i(r)
             − sanction_cost × sanctions_given_i
             − sanction_burn × sanctions_received_i
results.scores[i] = round(score_i, 3)
```

**Sign: higher is better.** Every module payoff is non-negative; the only negative terms are the
two sanction terms, so a score goes below zero only when a cog punished a lot or was punished a
lot. **The league ranks by `results.scores[i]`** (the platform's Elo is computed from these
per-episode scores). Ties are ties.

The grader keeps meadow's social-planner framing and is **not** what the league ranks by:
`grade.score = welfare / optimum_welfare`, where
`welfare = Σ_i score_i + residual_value(final module state)` and `residual_value` is remaining
apples (`cleanup`), the sum of patch stocks (`harvest`), total ripe berries × 1.0
(`allelopathic`), or total mushrooms × 1.0 (`mushrooms`). `optimum_welfare` is exact for
`cleanup` (a 2-D DP over discretised apples × pollution with one aggregate effort split per round),
for `harvest` (the per-patch 1-D DP summed — exact here because the planner's optimal aggregate
demand is ≈ 12.0 per round against an 18-unit effort cap, so the cap never binds), and for
`mushrooms` (a DP over the three counts and the number of unfrozen seats; welfare per mushroom is
1/2/3 regardless of who is paid). For `allelopathic` v1 uses the **best-monoculture planner
schedule** (a DP over the reduced state "slots converted to the target colour × ripe berries of
that colour", maximised over the three target colours) and says so in `grade.scale`; the exact
joint DP is in `## Out of scope (v1)`. `grade` also keeps meadow's `survived`, `collapse_round`,
`synchrony_same_action_rate` and `harvest_gini`, plus a new `public_effort_share` (maintenance
units ÷ total effort units) — the number the whole family is really about.

### End conditions and the legal `results.reason` values

Exactly three values are legal, and the game emits nothing else:

- **`complete`** — all `rounds` rounds settled. The normal path. A dead orchard or six dead
  patches do **not** end the episode: the remaining rounds are played out (they are cheap, and the
  post-collapse scavenging is data), so collapse is a *field* (`collapse_round`, `dead_patches`),
  never a reason.
- **`deadline`** — the wall-clock guard in step 9 fired. Rounds already settled are scored as they
  stand, the remaining rounds are not played, a `deadline` event is written, `results.rounds`
  records how many actually ran, and the process writes its artifacts and exits **0**. Scores are
  real, not zeroed, so a deadline episode is still rankable. With the arithmetic in §Decisions it
  should never fire.
- **`no_players`** — zero seats connected within `player_connect_timeout_seconds` (180, meadow's
  default). `results.json` is written with all-zero scores and the process exits **0**.

If *some* seats connect, the episode runs with the seats it has: absent seats pass every round,
score 0, and are flagged `disconnected: true` in the replay and results. If **every** seat
disconnects mid-episode the remaining rounds settle immediately with no waiting (no barrier to
wait on), and the reason is still `complete` — that is how the episode settles early. The game
never exits non-zero on a player-side problem and never waits on a player socket without a bound.

### Per-seat observation: exactly what is visible and what is hidden

One `observation` message per seat per round, extending meadow's (`game/engine.py:observation`).
Shared block, always present:

```json
{"type":"observation","protocol":"commons-family.player.v1",
 "slot":2,"alias":"Cog-C","round":7,"rounds":20,"round_seconds":20.0,
 "module":"allelopathic","num_players":6,"effort_budget":3,
 "ledger_public":true,"sanctions_enabled":true,"sanction_cost":1.0,"sanction_burn":3.0,
 "chat_enabled":true,"chat_max_chars":140,"norm_text":"Posted quota: one unit each.",
 "score":11.33,"your_last_gain":2.0,"sanctions_received_last_round":0,
 "last_round_total_extracted":9.0,
 "messages_last_round":[{"alias":"Cog-A","text":"everyone on green from now"}],
 "your_note":"Cog-A and Cog-E kept their word last round.",
 "ledger":[{"alias":"Cog-A","total_extracted":15.0,"public_effort":4,
            "recent":["e:g2","e:g2","p:g1 e:g1","e:g3","e:g2"],
            "sanctions_given":0,"sanctions_received":1}],
 "module_state":{ … }}
```

`module_state` per module: `cleanup` → `{"apples":58.4,"capacity":100.0,"pollution":0.42,
"effective_regrowth":0.203,"collapse_threshold":10.0,"dead":false,"cleaned_last_round":2}`;
`harvest` → `{"property_rights":"partnership","patches":[{"id":0,"stock":11.2,"dead":false,
"holders":["Cog-A","Cog-D"]}, …],"your_patches":[2,5]}`; `allelopathic` →
`{"planted":{"red":18,"green":26,"blue":16},"ripe":{"red":2.7,"green":5.6,"blue":2.1},
"your_favorite":"green","field_size":60}`; `mushrooms` →
`{"counts":{"red":7,"green":9,"blue":5},"frozen_until":8,"you_may_eat":false,
"payoff":{"red":"1.0 to you","green":"2.0 split among all 6","blue":"3.0 split among the other 5"}}`.

**Visible:** everything above — the full public resource state, the norm text, your own score,
your own last gain, your own private note, the aggregate extracted last round, everyone's signed
chat from last round, and (when `ledger_public`) every other cog's alias, cumulative extraction,
cumulative maintenance effort, last five compact actions, and sanction counters. Property-rights
assignments in `harvest` are public by construction.

**Hidden:** every other cog's **secret favourite colour** in `allelopathic` (a cog's own favourite
is in its own observation and nowhere else; it can be inferred from behaviour on the ledger,
which is the point); every other cog's private `note`; every cog's decision for the *current*
round until it settles; the episode `seed` (it determines favourites and property-rights deals, so
seats never see it — the replay does); the real policy name behind any alias, including your own
(§Two name spaces); the grader's optimum; and, when `ledger_public` is false, the entire `ledger`
key and all per-cog attributions — only `last_round_total_extracted`, your own fields and signed
chat survive, exactly as in meadow's anonymous treatment.

An LLM seat's prompt is composed from **exactly this observation object** and nothing else, so a
prompt seat can never see further than a scripted seat.

---

## Decisions: LLM with scripted fallback

### Where the LLM lives: the game container, not the player container

Meadow puts the LLM inside the *player* container (`player/policies.py:LlmPolicy`, one Bedrock
client per pod). **We move it to the game container**, adopting bullwhip's split wholesale
(`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim`, `src/bullwhip/server.nim:runGame`):
the player container's only job is to register its policy, and the game makes every decision.
Four reasons, all load-bearing: (1) "all seats' LLM calls go out as ONE parallel batch per round"
is literally satisfiable only by the party that owns the round barrier; (2) the
retry-once-then-fall-back-to-scripted rule must be enforced by that same party, or a hung player
pod silently becomes a passing seat; (3) one container needs the secret instead of six, matching
`ANTHROPIC_API_KEY_URI` on the game runnable; (4) meadow's scripted policies are already pure
`obs → action` functions, so they move server-side unchanged and become the fallback in the same
process. The pin holds exactly as it does in bullwhip: **`PLAYER_PROMPT` vs
`PLAYER_SCRIPTED=<name>`, same image, env-switched.**

### The LLM policy

Ported from `player/policies.py:LlmPolicy` into `game/llm.py`, keeping its Bedrock-sidecar-first
transport ladder verbatim (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` present → Bedrock `InvokeModel`;
else `ANTHROPIC_API_KEY`; else `ANTHROPIC_API_KEY_URI`; else **disabled**), its haiku-4.5 default,
its assistant-prefill trick for pre-4.6 models, and its "auth/validation errors raise immediately,
throttling retries" discipline. Three changes: the throttle ladder is truncated from meadow's
`(1, 2, 4, 8, 16, 30, 60)` — two minutes, far past our round deadline — to **`(0.5, 1.0, 2.0)`**;
every request carries a per-call deadline of `decision_timeout_seconds = 8`; and all six seats go
out together on one `concurrent.futures.ThreadPoolExecutor(max_workers=6)` batch per round
(meadow's `headless.run_episode(parallel_seats=True)` already proves the shape).

**System prompt** (one per seat, built once per episode; the seat's `PLAYER_PROMPT` is appended
verbatim as a `STANDING ORDERS` block, truncated to 1200 runes):

```
You are {alias}, one of 6 cogs sharing a commons for {rounds} rounds. Module: {module}.
{module_rules}
Every round all 6 cogs decide at the same time and the results settle together. You have
{effort_budget} effort units per round to split between taking and maintaining.
Your score is everything you take, minus punishment you pay or receive.{sanction_rules}{norm_line}
The resource is shared: what you take is not there next round for anyone, including you.
Each round you receive the game state as JSON. Reply with ONLY one JSON object, no other text.
Your reply MUST begin with the character {.
Schema: {schema_line}
```

`{module_rules}` is a fixed four-to-six line block per module giving the physics in words with the
episode's actual numbers (regrowth, thresholds, payoffs, digestion, the ripening rule);
`{schema_line}` is the module's field list from the table below. `{sanction_rules}` is meadow's
line ("You may also sanction one cog per round: you pay 1.0, they lose 3.0") when sanctions are
on, empty otherwise. The **user message is the observation object, serialised compactly** with
`type` and `round_seconds` dropped — meadow's rule, unchanged — so there is exactly one
description of the world and no drift between the prompt and the engine. `max_tokens` 300 with
prefill, 4000 without (meadow's numbers).

### Reply schema and character caps

One JSON object. Unknown keys are ignored. Extraction takes the first balanced `{...}` span, so
leading or trailing prose is tolerated.

| field | modules | type | cap / range | invalid → |
|---|---|---|---|---|
| `harvest` | `cleanup`, `harvest` | int | 0..3 | 0 |
| `clean` | `cleanup` | int | 0..3, `harvest+clean ≤ 3` | 0 / reduced first |
| `patch` | `harvest` | int | 0..5 | 0 |
| `eat` | `allelopathic`, `mushrooms` | int | 0..3 | 0 |
| `eat_color` | `allelopathic`, `mushrooms` | enum | `red\|green\|blue` (≤ 5 chars) | `red` |
| `plant` | `allelopathic` | int | 0..3, `eat+plant ≤ 3` | 0 / reduced first |
| `plant_color` | `allelopathic` | enum | `red\|green\|blue` | `eat_color` |
| `sanction` | all | int or null | `0..5`, ≠ self | null |
| `message` | all | free text | **≤ 140 runes** (`chat_max_chars`) | truncated |
| `note` | all | free text | **≤ 200 runes** | truncated |

**Every free-text field is truncated on rune boundaries, never byte boundaries.** In Python a
`str` slice is already a code-point slice, so the truncator is `text.strip()[:cap]` applied in one
helper (`game/engine.py:truncate_runes`) to `message`, `note`, policy names, the manifest-authored
`norm_text` (≤ 400 runes, and `config_schema` carries the same `maxLength`), and every error
string that can reach the replay; artifacts are written with `ensure_ascii=False` and encoded
UTF-8 exactly once, so a half rune can never reach the replay bytes (which the strict-UTF-8 test
asserts). `note` is private: it is echoed back only to its own seat and is **not** written to the
replay.

### Simultaneous decisions and the time budget

**All six seats' LLM calls go out as ONE parallel batch per round.** Scripted seats resolve
in-process in the same step. The round barrier releases when the batch is complete or when
`round_seconds = 20 s` elapses, whichever comes first, and never before
`min_round_seconds = 3 s`.

Per-seat worst case inside a round, said exactly: each of the two attempts walks the throttle
ladder, which is **three sleeps and therefore up to four requests** (`llm.py`'s
`for sleep_seconds in (*THROTTLE_SLEEPS, None)`), so a seat the provider throttles on every call
issues up to **8 requests** in one round — `tests/test_llm.py` asserts exactly that count. What
bounds it is not that arithmetic but the clock: every request's timeout is
`min(decision_timeout_seconds, round_deadline − now)` and every throttle sleep is clamped to the
same deadline, so the ladder cannot outlive the round and the seat falls back at the barrier. A
*legitimate* reply is one call at ≤ 8 s inside a 20 s round, so the round deadline never cuts a
healthy answer short; it is the backstop.

Episode arithmetic, said out loud:

- **Worst case:** ≤ 180 s of `player_connect_timeout_seconds` if seats are slow to appear, plus
  the 5 s registration grace, plus 20 rounds × 20 s = **400 s** of play = **585 s** to written
  artifacts, which is **48.8 %** of the 1200 s `episodeTimeoutSeconds`. Meadow's 30 s post-game
  linger runs *after* both artifacts are written, so it is outside the settle-and-score budget.
  The **hard ceiling** is the guard itself: `play_deadline` is anchored at **process start**
  (`server.py:PROCESS_START`), not when `_play_game` begins, so the connect wait is inside the
  budget rather than on top of it and the artifacts are on disk by 0.6 × 1200 = **720 s** even
  with a hand-edited `rounds`/`round_seconds`. Anchoring after the connect wait would have made
  that ceiling 180 + 5 + 720 = 905 s (75 %).
- **Typical:** haiku answering a ~900-token prompt with a one-line JSON object in 3–5 s, six in
  parallel → a round settles in ~5 s → 20 rounds ≈ **100–140 s**, plus ~15 s of pod startup.
- **All-scripted (CI, cert):** the 3 s pacing floor makes the episode 60 s, not 200 ms — long
  enough for the hosted certifier's `/global` probes and for a replay the viewer can soak.

The guard: the game reads `COWORLD_TIMEOUT_SECONDS` if the environment has it and otherwise
assumes `episode_timeout_seconds = 1200` (it does **not** receive that variable in hosted
episodes — only the worker sidecar does), and sets
`play_deadline = PROCESS_START + 0.6 × timeout = process start + 720 s`. Step 9 checks it
**between rounds**, so a deadline settle always lands on a clean round boundary, and it checks it
**before** a round rather than after one, so the artifacts are written inside the budget instead
of up to one `round_seconds` past it. Round 0 always plays: a deadline episode is still scored.

**Request rate:** a healthy round is 6 requests, one per prompt seat. A round in which the
provider throttles every call is up to 8 per seat and so up to **48**, which is why the ceiling is
enforced rather than argued: `llm_max_requests_per_minute = 120` is a **rolling 60 s budget shared
by all six seats**, retries and ladder steps draw from it, and a request that would exceed it is
not made. That is the bound — the game cannot issue more than 120 requests a minute whatever the
ladder does. A seat that cannot be called because the budget is exhausted plays its fallback
baseline for that round with `fallback` cause `rate_budget`, rather than waiting for the window.

### Scripted baselines (same image, env-switched)

`PLAYER_SCRIPTED=<name>` registers a seat as scripted; the game plays it deterministically.
Ported from `player/policies.py` into `game/baselines.py`, generalised across the four modules:

**`steward` — the default and the fallback baseline** (`fallback_scripted`, default `steward`).
It is meadow's `SustainablePolicy` generalised, and its algorithm is:

1. Compute the module's **sustainable aggregate** from the observation: `cleanup` →
   `regrowth_rate × (1 − pollution) × capacity / 4`; `harvest` → `patch_regrowth × capacity / 4`
   per live patch; `allelopathic` → this round's total ripening
   `Σ_c 0.5 × planted[c]² / field_size`; `mushrooms` → `spawn_per_round`.
2. Its personal quota is `floor(sustainable / num_players)`, at least 0 and at most
   `effort_budget`.
3. `cleanup`: if `pollution > 0.15`, spend 1 unit on `clean`; harvest the quota with what is left;
   harvest 0 while `apples < 30`.
4. `harvest`: choose the **fullest live patch it is allowed to name** (`open` → any; `closed` →
   its own; `partnership` → the pair patch with the higher stock, always naming it so a partner
   who also names it can be paid); demand `min(quota, floor(stock − 1))` so it never kills a patch.
   In an **`open` room the ranking is offset by the seat** (`ranked[slot % len(ranked)]`), and
   only there. Every patch starts identical, so six stewards all reading "the fullest patch" queue
   on patch 0 and six individually restrained demands strip it in one round: measured over a
   20-round episode, the plain maximum kills patch 0 and the society scores 126 where the offset
   scores 240 with every patch alive. `closed` and `partnership` keep the plain maximum, because a
   partnership patch pays only when BOTH partners name it and partners can only agree on a rule
   that does not read the seat. A test asserts both halves.
5. `allelopathic`: eat its favourite while its favourite is the plurality colour; otherwise spend
   1 unit planting the plurality colour and eat the plurality colour with the rest. Never eats
   more than `ripe[c] / num_players`.
6. `mushrooms`: eat exactly 1 green while green is available (2.0 of welfare for one round of
   freeze), else 1 red, else nothing. Never eats more than 1 per round, so it is never frozen for
   more than a round.
7. Never sanctions. Emits a one-line `message` naming its quota when `chat_enabled`.

The rest, each a small precise rule:

- **`free_rider`** — meadow's `GreedyPolicy`: extract `effort_budget` every round, never clean,
  never plant, in `mushrooms` always red, never sanction. The tragedy, distilled. (One of the
  idea's three named bots.)
- **`cleaner`** — spends **1 unit on the maintenance act every round** (clean / plant the plurality
  colour / hold the pair patch / eat blue) and stewards with the other 2. The idea's cleaner bot;
  it is the pure public-goods contributor and it is exploitable, which is the measurement.
- **`punisher`** — meadow's `EnforcerPolicy`: steward, plus, when `sanctions_enabled` and the
  ledger is public, sanction the cog with the highest `total_extracted` above quota, ties to the
  lowest slot. The idea's punisher bot.
- **`reciprocator`** — meadow's, unchanged: steward until the always-visible aggregate says the
  average other cog took more than `quota + 0.5`, then take `effort_budget` for one round.
- **`deterrable`** — meadow's `DeterrableGreedyPolicy`, unchanged: free-rider until sanctioned,
  then five contrite quota rounds.
- **`random`** — meadow's, unchanged, seeded per slot: uniform over legal decisions. The
  maximum-variance control and the fuzz source for the legality test.

**The steward's two constants are tuned by a grid harness, not guessed.**
`tools/tune_baselines.py` sweeps `CLEAN_POLLUTION_TRIGGER ∈ {0.05 … 0.55}` × `CLEANUP_STOCK_FLOOR
∈ {0 … 50}` — 36 combinations — and plays each one through **all four modules** in **three
societies**: six stewards, the mixed room (two stewards, a cleaner, a punisher, a free rider, a
random cog) and a pressure room (three stewards, three free riders). Each of those 12 episodes
scores the combination as *what a steward took plus its equal share of what it left standing*
(`mean(steward scores) + residual_value / num_agents`), and a combination whose monoculture kills
the resource in any module is inadmissible whatever it scores. Everything is seeded and
deterministic, so the table is reproducible and `tests/test_tuning.py` runs the same sweep in CI.

The sweep is what set `CLEAN_POLLUTION_TRIGGER = 0.15`: the original guess of 0.35 scores 384.6
against the grid's best 409.3 (−6.0 %), and 0.15 scores 405.0 (−1.0 %). The corner the grid likes
best, `trigger = 0.05`, makes the steward clean whenever the river is dirty at all — an
unconditional rule, which is exactly the `cleaner` baseline, and the difference between a
conditional steward and an unconditional contributor is one of the things this coworld measures;
so the shipped value is the best *conditional* one and the test's tolerance is 2 %.
`CLEANUP_STOCK_FLOOR = 30` costs 0.5 % against the grid's best floor and buys what the score does
not price: under pressure it stops a steward taking the last apples of a dying orchard.

### Degrade, never hang

| failure | response |
|---|---|
| a seat's LLM call times out (8 s) or throttles past the ladder | **retry once**, that seat only, with the hint `Your last reply was not usable. Reply with ONE JSON object beginning with { and only the fields in the schema.` |
| reply is not JSON / has no balanced object / omits every schema field | same single retry |
| retry also fails | that seat plays `fallback_scripted` (`steward`) for this round; `fallback` event with `cause ∈ {timeout, parse, rate_budget, transport, disabled}`; counted in `results.fallbacks[slot]` |
| an unclassified transport failure (a rejected credential, a response shape the parser does not expect) | logged with its traceback, then the same retry-once-then-fall-back path with `cause: transport`. It is never allowed out of the batch: an exception escaping `decide` would unwind the round loop, and `_play_game` is a task nobody awaits |
| no credentials at all (offline CI, cert without a key) | the client marks itself **disabled at startup, makes zero network calls**, and every prompt seat plays `steward` all episode with `cause: disabled` on every `fallback` event — which is the fifth cause, and what a CI replay is full of (`results.fallbacks` counts them); the episode still finishes `reason: "complete"` |
| a seat's websocket never connects | it passes every round, scores 0, `disconnected: true` in replay and results |
| every seat disconnects mid-episode | remaining rounds settle with no waiting; `reason: "complete"` |
| zero seats ever connect | `reason: "no_players"`, artifacts written, exit 0 |
| the wall-clock guard fires between rounds | settle with `reason: "deadline"`, artifacts written, exit 0 |
| the episode ends | meadow's post-game linger (30 s, hard cap 90 s, extended while a `/global` viewer is attached) is **kept verbatim** — the hosted certifier probes `/global` around game end and a fast exit fails the episode |

Nothing in the round loop blocks on an unbounded read. Artifact writes stay on
`asyncio.to_thread`, as meadow already does, so websocket pings keep answering during them.

### Two name spaces

- **In-game:** seats are `Cog-A` … `Cog-F`, assigned by a seeded permutation of slots so a policy
  cannot infer "slot 0 is always the strongest entrant". Aliases are the only identifiers in
  observations, prompts, the ledger, chat lines and events. **This is a change from meadow**,
  whose `observation()` puts `player_names[other]` — the real policy names, since the runner sets
  them — straight into the ledger. `game/engine.py:observation` takes `aliases`, never
  `player_names`.
- **Spectator-side only:** `config.players[].name` (the runner's real policy names) appears only in
  the replay's `seats[].name` / `policyNames[]`, in `results.names[]`, and therefore in the viewer,
  which renders `Cog-C · commons-family-warden` through bullwhip's existing
  `makeNameMap(names, policyNames)`.

---

## Sim module

Meadow's package layout is kept (its `Dockerfile` mirrors the source tree into
`/app/coworld/examples/…`, so absolute imports resolve identically in tests and in the image); the
example is renamed and the resource physics are factored out of the engine into a module registry:

| path | from | change |
|---|---|---|
| `src/coworld/examples/commons_family/game/engine.py` | meadow `game/engine.py` | keeps the round loop, institutions (ledger, sanctions, chat, norm), `RoundRecord`, `welfare`, `observation`, `truncate_runes`; the single-stock physics move out to `modules/cleanup.py`; `observation` now takes aliases |
| `…/game/modules/base.py` | new | the module protocol: `name`, `defaults`, `new_state(config, rng)`, `parse_decision(raw, slot, config, state)`, `resolve(state, decisions, config) -> (gains, events)`, `dynamics(state, config) -> events`, `observe(state, config, slot)`, `residual_value(state)`, `planner_optimum(config)` |
| `…/game/modules/{cleanup,harvest,allelopathic,mushrooms}.py` | new (cleanup derives from meadow's stock code) | the four physics, exactly as specified above |
| `…/game/llm.py` | meadow `player/policies.py:LlmPolicy` | moved server-side; truncated throttle ladder; per-call deadline; one parallel batch per round; retry-once-then-fallback |
| `…/game/baselines.py` | meadow `player/policies.py` (the six scripted classes) | generalised across modules; `steward` is the fallback |
| `…/game/server.py` | meadow `game/server.py` | round barrier becomes "batch complete or `round_seconds`", with the `min_round_seconds` floor and the `play_deadline` guard; `/player` registration message; alias assignment; the richer replay writer; **linger and artifact handling kept verbatim** |
| `…/player/player.py` | meadow `player/player.py` | registers `{"type":"prompt","prompt":…,"scripted":…}` from `PLAYER_PROMPT` / `PLAYER_SCRIPTED`, then spectates until `final` — **bounded on both ends**: the connect retries inside a 150 s window, the socket carries `ping_interval = 20 s` / `ping_timeout = 30 s` so a game that died without closing its socket is noticed, and the spectate loop has a 1080 s deadline (past the game's own worst case of a 720 s play budget plus the 90 s hard-cap linger). Every one of those exits 0 |
| `…/grader/commons_grader.py` | meadow `grader/meadow_grader.py` | per-module `planner_optimum`, plus `public_effort_share` |
| `…/headless.py` | meadow `headless.py` | unchanged in shape (`parallel_seats=True` is how tests exercise the batch) |
| `…/shared/{artifact_io,log_shipper}.py` | meadow's | **verbatim, byte-for-byte** |
| `…/game/client/{player,global,admin}.html` | meadow's | kept and made module-aware; they exist because certification probes them, not because we invest in them |

**Deleted, not adapted:** meadow's `static-replay-viewer/index.html` (a hand-written HTML player)
and its `tools/build_replay_viewer.sh` (which only copies that file). Both are replaced by the
bullwhip four-file wasm bundle in §Viewer. Meadow's manifest value
`"replay_viewer": {"bundle": "build/static-replay-viewer"}` is corrected to
`{"bundle": "static-replay-viewer"}`.

**Config**, fully (`config_schema` mirrors this with `additionalProperties: false` and
`minItems`/`maxItems` = 6 on every array):

```
tokens: list[str]                      # 6
players: list[{name: str}]             # 6, real policy names, spectator-side only
num_agents: int = 6                    # min 6, max 6
seed: int = 20260824
module: str = "cleanup"                # cleanup | harvest | allelopathic | mushrooms
rounds: int = 20                       # 1..100
round_seconds: float = 20.0            # 1..120
min_round_seconds: float = 3.0
decision_timeout_seconds: float = 8.0
episode_timeout_seconds: float = 1200.0
play_budget_fraction: float = 0.6
player_connect_timeout_seconds: float = 180.0
effort_budget: int = 3                 # 1..10
ledger_public: bool = true
sanctions_enabled: bool = false
sanction_cost: float = 1.0
sanction_burn: float = 3.0
chat_enabled: bool = true
chat_max_chars: int = 140              # 1..1000
norm_text: str = ""
fallback_scripted: str = "steward"
llm_max_requests_per_minute: int = 120
# cleanup
stock_start = 60.0  stock_capacity = 100.0  regrowth_rate = 0.35
collapse_threshold = 10.0  pollution_start = 0.30  silt_rate = 0.12  clean_power = 0.05
# harvest
patch_count = 6  patch_capacity = 20.0  patch_start = 12.0  patch_regrowth = 0.40
property_rights = "open"               # open | closed | partnership
# allelopathic
field_size = 60  ripen_base = 0.5  planted_start = [20,20,20]  ripe_start = [6,6,6]
favorite_bonus = 2.0  favorite_base = 1.0
# mushrooms
mushroom_start = [8,8,8]  mushroom_capacity = 30  mushroom_color_cap = 15
spawn_per_round = 3  red_value = 1.0  green_value = 2.0  blue_value = 3.0
```

**Determinism.** One `random.Random(seed)` is drawn from exactly three times, in this order:
alias permutation, `allelopathic` favourite deal, `harvest` ownership/partnership deal. Nothing
else in the sim is stochastic — every resolution rule above is a closed-form function of the
decisions. Two runs with the same seed and the same decisions produce identical state, asserted by
a test.

---

## Server, player, protocol

### Game server

`python -m coworld.examples.commons_family.game.server`, launched in the image through the shim
`/bin/commons-family` (a two-line `exec` script) so `tools/ci/docker_smoke.sh` works unmodified.
Meadow's FastAPI routing is kept exactly: `GET /healthz`, `GET /client/player`,
`GET /client/global`, `GET /client/admin`, websockets `/player?slot=N&token=T`, `/global`,
`/admin` (pause / resume / round_seconds). Config in via `COGAME_CONFIG_URI`, results to
`COGAME_RESULTS_URI`, replay to `COGAME_SAVE_REPLAY_URI`, both through
`shared/artifact_io.write_data` off the event loop.

### Player protocol (`game.protocols.player`)

`commons-family.player.v1`, JSON text frames over the socket named by `COWORLD_PLAYER_WS_URL`.

**player → game, once immediately after connect:**
`{"type":"prompt","prompt":"<≤ 1200 runes>","scripted":"<baseline name or empty>"}`. The reference
player sends `PLAYER_PROMPT` and `PLAYER_SCRIPTED` from its environment. `scripted` non-empty wins
and names one of `steward, free_rider, cleaner, punisher, reciprocator, deterrable, random`; an
unknown name, a malformed frame, or no registration within 5 s of connect is treated as
`{"scripted":"steward"}` — never a disconnect.

**game → player:** `{"type":"welcome","protocol":"commons-family.player.v1","slot":N,
"alias":"Cog-C","module":"cleanup","rounds":20,"num_players":6}` on connect; the full
`observation` object (§Per-seat observation) after every settled round; and once at the end the
same shape with `"type":"final","done":true,"reason":"complete","scores":[…],"names":[…],
"aliases":[…]`, after which the player exits.

**A player may also send a decision** — `{"type":"decision", …schema fields…}` — and if one
arrives before the round deadline it **overrides** the game-side decision for that seat. This
keeps meadow's original protocol (and its browser player client, which the certifier opens)
working, and it is how a future non-prompt policy could play. Policies we ship do not use it.

### Global protocol (`game.protocols.global`)

Meadow's `/global` snapshot, generalised: the same 0.5 s-polled, progress-gated, coalesced sender
(kept **verbatim**, including the comment explaining why an unconditional 2 Hz stream breaks the
hosted certifier), with `last_round` carrying the settled `RoundRecord`, plus `module`,
`module_state`, `aliases`, `player_names`, `connected`, `submitted`, `started`, `paused`, `done`,
`reason`.

### Replay bytes (self-sufficient, strict UTF-8 JSON)

One UTF-8 JSON document. `docker_smoke.sh` parses it (`SMOKE_REQUIRE_REPLAY_JSON=1`), the wasm
module parses it in the browser, and nothing else is ever contacted — no server, no config
lookup, no name service.

```json
{"format":"commons-family/1","protocol":"commons-family.replay.v1","version":"0.1.0",
 "coworld":"commons_family","module":"allelopathic","variant":"allelopathic",
 "generated_at":"2026-08-24T12:00:00Z","seed":20260824,
 "config":{ …every resolved config field except tokens, defaults expanded… },
 "names":["Cog-A","Cog-B","Cog-C","Cog-D","Cog-E","Cog-F"],
 "policyNames":["commons-family-steward","commons-family-warden","baseline", …],
 "seats":[{"slot":0,"alias":"Cog-A","name":"commons-family-steward","kind":"prompt",
           "scripted":"","color":0,"favorite":"green","patches":[],"disconnected":false}],
 "rounds":[{"r":0,"state_before":{…module_state…},"decisions":[{"slot":0,"harvest":1,"clean":1,
            "eat":0,"eat_color":"green","plant":0,"plant_color":"green","patch":0,
            "sanction":null,"message":"one each","src":"llm"}],
            "gains":[1.0,2.0,0.0,1.0,1.0,2.0],"scores":[1.0,2.0,0.0,1.0,1.0,2.0],
            "state_after":{…module_state…},"total_extracted":7.0,"public_effort":3,
            "seat_public_effort":[1,0,2,0,0,0],"collapsed":false}],
 "events":[{"kind":"round_open","r":0}, …],
 "results":{"reason":"complete","rounds":20,"scores":[…],"total_extracted":[…],
            "public_effort":[…],"sanctions_given":[…],"sanctions_received":[…],
            "welfare":118.4,"residual_value":22.0,"collapse_round":null,
            "dead_patches":[],"fallbacks":[0,1,0,0,0,0],"llm_requests":118,
            "names":[…],"aliases":[…],"disconnected":[false, …]}}
```

**Event vocabulary — the complete list the replay may carry, and the only kinds the viewer must
know:** `episode_start`, `round_open`, `chat`, `decision`, `resolve`, `sanction`, `void`,
`trespass`, `unheld`, `patch_dead`, `collapse`, `barren`, `digesting`, `fallback`,
`no_submission`, `deadline`, `round_end`, `episode_end`. Every event carries `kind` and `r`; the
per-seat ones carry `slot` and `alias`. `decision` carries `src ∈ {llm, scripted:<name>,
fallback:<cause>, pass, player}`. There is no other kind, and a test asserts it.

Everything the viewer needs is in these bytes: aliases (`names`), real policy names
(`policyNames`), the resolved config, the seed, the per-round state before and after, every
decision, every event, and the results.

---

## Viewer

**A static wasm bundle, never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` (the
`coworld build` hook, committed mode 100755) builds it; the platform serves it from its static
replay path with `?replay=<s3 url>`. There is no `/client/replay` route and no live replay server.

### All four viewer files come from ONE starter: `Metta-AI/cogame-bullwhip`

coworld-meadow has no wasm viewer at all — its `static-replay-viewer/` is a single hand-written
`index.html` with no `.nim`, no `config.nims`, no `static_replay*.js` and no bundle step (verified
by `find` over the clone). So all four files come from **bullwhip and only bullwhip** — never a
mixture, because splicing one starter's shell onto another's emscripten link flags
(`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer silently
(cogame-lantern, 2026-08-23).

**Bullwhip over babel** (both were read in full): they are the same four-file shape, but
bullwhip is the newer descendant and its renderer already does the three things we need and babel
does not — a `drawChart()` time series over rounds (our stock / pollution / colour-share curve),
`makeNameMap(names, policyNames)` (our two name spaces, already implemented), and a
`results.reason` line that already special-cases `deadline`. Its scorebug plates are already
per-seat rows with a score and a role label, which is our scorebug with two words changed.

| file | copied from `cogame-bullwhip` | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | output path → `commons_family_replay.js`; `EXPORT_NAME=CommonsReplayModule`; `EXPORTED_FUNCTIONS=_main,_malloc,_free,_cf_load_replay,_cf_payload_ptr,_cf_payload_len,_cf_error_ptr,_cf_error_len`. **Every other flag byte-identical** — keep `MODULARIZE=1`, `ENVIRONMENT=web`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `EXPORTED_RUNTIME_METHODS=HEAPU8`, `--mm:arc`, `--exceptions:goto`, `-d:useMalloc` |
| wasm entry `replay-viewer/commons_family_replay.nim` | `replay-viewer/bullwhip_replay.nim` | same skeleton, same `exportc` pattern, same `emscripten_exit_with_live_runtime` epilogue (its comment explains why: Nim's generated main would destroy the payload globals JS still reads); exports `cf_load_replay, cf_payload_ptr, cf_payload_len, cf_error_ptr, cf_error_len`; imports **only `std/json`** |
| `replay-viewer/static_replay.js` | same file | `BullwhipReplayModule` → `CommonsReplayModule`, `_bw_*` → `_cf_*` (renamed on both sides together, never one side), `BullwhipRenderer` → `CommonsRenderer`; the header comment; and ONE behavioural edit — the `ready` bridge. Bullwhip posts `tell("ready")` from a double `requestAnimationFrame` at the `attachReplay` call site, which can fire before the renderer's first paint; here a `whenDrawn()` helper waits on `<html data-replay-loaded="true">` (a `MutationObserver` on that one attribute, or straight through if the renderer beat us to it) and posts `ready` from there, so `ready` means a picture and not a parsed payload (chorus 3c11c953, 2026-08-24; `tests/test_viewer_contract.py` asserts it). The `?replay=` fetch, the 20 s `AbortController` timeout, the Retry button, the `{src:"coworld-replay"}` envelope and the `data-replay-error` write/remove are untouched |
| `replay-viewer/index.html` | same file | wordmark, `<title>`, the extra game-block nodes below; script tags point at `commons_family_replay.js` |

The bundle also carries `client/renderer.js` and `client/chrome.css`, copied from bullwhip.

**The shell sets `data-replay-loaded="true"` on its first drawn frame** — in bullwhip that write
lives at the end of `attachReplay()` in `renderer.js` (line 1390), inside `makeRenderer`'s ready
callback, i.e. after the first real draw; it is kept exactly there — **and `data-replay-error` on
failure**, written by `static_replay.js:fail()` and removed on every successful load. Both are
load-bearing: `tools/ci/viewer_smoke.mjs` fails on silence and on the error attribute.

**Pipeline.** The game is Python and CPython does not compile to wasm, so the wasm module does
**not** re-run the physics — and it must not, because a Nim reimplementation of four resource
modules would be a second source of truth for the rules. It does not need to: the replay records
each round's fully settled `state_before` / `state_after` / `gains` / `scores`, so every frame is
*recorded*, not derived. `cf_load_replay` parses the replay JSON, validates the required keys and
the event vocabulary, **expands the round records into one renderer state per event** (the
scrubber indexes events, as bullwhip's does), and emits the payload the renderer reads. A
malformed replay sets `lastError` and returns 0, which the shell turns into `data-replay-error`.

**The expander derives nothing.** Every number in a `states[i]` is copied out of a round record —
including each seat's maintenance effort, which the round record carries per seat as
`seat_public_effort` exactly as the engine booked it in step 8. The wasm module must never
recompute it from the decision (`clean`, `plant`, `effort_budget − harvest`, a non-red `eat`),
because that is `Module.public_effort` written a second time in a second language, and the two
copies drift the first time a module's maintenance act changes. A test asserts both halves: that
the record carries the per-seat effort the module computes, and that the Nim reads it.

**The exact state JSON the viewer reads** (`cf_payload_ptr` → `JSON.parse` →
`CommonsRenderer.attachReplay({payload})`):

```json
{"type":"replay","protocol":"commons-family.replay.v1",
 "names":["Cog-A", …], "policyNames":["commons-family-steward", …],
 "config":{ …resolved config… }, "results":{ …as in the replay… },
 "events":[ …the replay's events, in order… ],
 "states":[{"r":7,"rounds":20,"module":"allelopathic","phase":"resolve",
            "done":false,"reason":"",
            "seats":[{"slot":0,"alias":"Cog-A","name":"commons-family-steward",
                      "score":11.33,"gain":2.0,"extracted":15.0,"public_effort":4,
                      "favorite":"green","frozen":false,"patches":[],
                      "pending":false,"say":"everyone on green"}],
            "resource":{"kind":"allelopathic","planted":{"red":18,"green":26,"blue":16},
                        "ripe":{"red":2.7,"green":5.6,"blue":2.1},"dead":false},
            "series":{"total":[60.0,58.4, …],"maintenance":[0.30,0.42, …]},
            "flow":[{"from":2,"to":0,"amount":0.6,"kind":"blue"}]}]}
```

One `states[i]` per `events[i]`, same length, so `scrub.update(index)` addresses both. `series`
is the chart (module-primary quantity and the maintenance quantity, cumulative to this event);
`flow` is non-empty only in `mushrooms` and drives the reward particles.

### Chrome provenance

- **`client/renderer.js` is bullwhip's file: its chrome scaffolding kept, its board block
  replaced.** Said exactly, because "byte-for-byte" is not true of this file and the difference is
  what a reviewer needs to check: the *scaffolding* — `makeRenderer`, `attachLive`,
  `attachReplay`, `stateToView`, `makeEffects`, `makeNameMap`, `applyNames`, `renderFeed`,
  `bindFeedToggle`, `buildScrub`, `blockHead`, `describeEvent`, `reasonLine`, `matchHeader`,
  `updateScorebug`, `updateEndscreen`, `drawChart`, `computeLayout`, `wrapLines`, `drawBubble`,
  `roundRect`, `ellipsize`, `escapeHtml`, `clampName`, `seatColor`, `hexToRgb`, `rgba`,
  `assetUrl`, `loadImages`, `isBaselineFiller` — keeps the starter's names, its call graph and its
  structure, and eight of them are byte-identical to bullwhip's; the rest differ only in this
  game's strings, its six seats and its module fields. The *board* is the retarget §Readouts
  describes: bullwhip's supply-chain drawing functions (`drawBelt`, `drawCrate`, `drawDock`,
  `drawStation`, `drawShipment`, `drawProduction`, `drawCustomers`, `drawSlip`, `drawStack`,
  `drawTag`, `drawCrateCluster`, `drawCustomerDelivery`, `slotX`, `stageOfSeat`, `peakOrders`,
  `playerFrameToState`) are gone and this game's four module boards (`drawOrchard`, `drawPatches`,
  `drawField`, `drawMushrooms`, `drawFlow`, `drawCogRow` and their helpers `cogCentre`,
  `mushroomRowY`, `moduleBadge`, `maintenanceChip`, `beatLabel`, `chartTitle`) stand in their
  place, called from the same `draw()` switch. Three further named edits sit outside that: `money`
  is renamed `score` (the same function, a different unit); `paint()` is added, and every board
  string is drawn through it, so each one is ellipsized to the frame and its box clamped inside
  the canvas; and `String()` coercions in `escapeHtml`/`wrapLines` plus a radius clamp in
  `roundRect` harden those three helpers against non-string and degenerate input. The identifier
  rename `BullwhipRenderer` → `CommonsRenderer` is applied to the export object and its two call
  sites, and the export object's key set is unchanged.
- **`client/chrome.css` is bullwhip's file with three in-place edits and one appended block.** The
  three, and there are no others (`diff` against the starter is exactly these hunks plus the
  append): the header comment, which now records this provenance; `#scorebug`
  `grid-template-columns: repeat(4, 1fr)` → `repeat(6, 1fr)`, because this game seats six where
  bullwhip seats four; and `#endscreen { bottom: var(--band, 0px) }`, which is transport edit 2
  below. Everything above the banner comment is otherwise the starter's, unmodified — the stage,
  the top band, the scorebug plates (`.plate-name { flex: 1 1 auto; min-width: 3.2em }` included),
  the feed, the transport and scrubber, the endscreen and both narrow-width media queries. The
  appended block under the banner `commons-family additions to the inherited cogame-bullwhip
  chrome` carries the beat-kind rules, the plate decorations and `#modulebar`/`#patchgrid`.
  (Bullwhip's lineage keeps its chrome in `renderer.js` + `chrome.css`; it has no
  `chrome_common.js` and no `replay_broadcast.html` — those are the paintbot lineage's names, and
  this repo does not take anything from paintbot.)
- **`replay-viewer/index.html` is bullwhip's page with a game block appended** — not a rewrite that
  reuses its ids (cogame-gridlock, 2026-08-23). The `<head>`, `#layout`, `#stage`, `#topband`,
  `#wordmark`, `#clock`, `#topright`, `#statuschip`, `#feedtoggle`, `#scorebug`, `#board-wrap`,
  `#table`, `#lightpool`, `#grain`, `#endscreen`, `#transport`, `#scrub`, `#play`, `#pos`,
  `#feed`, `#loading` nodes and the inline `fit()` / `bindFeedToggle` script all stay exactly as
  they are, because `renderer.js` and `static_replay.js` resolve every one of them by id.
- **Removed** starter elements: **none.** Bullwhip's page has no game-specific markup to strip —
  its supply chain is drawn on `#table` in canvas, not in DOM — so nothing is deleted and the
  page is the starter's plus our block. The appended block is
  `<div id="modulebar">` (module name + the resource readout chips) and, for `harvest`, a
  `<div id="patchgrid">`, both **outside** `#transport` and **outside** `#board-wrap`.
- **Zoom decision: dropped — there is nothing to drop.** Bullwhip's page has no `#viewpanel`, no
  zoom bar and no minimap, and this is a fixed abstract arena that is always drawn in full at
  whatever size the frame is. We add none.
- The appended block must not declare a top-level `function` with any name `renderer.js` exports
  or uses as a global (`CommonsRenderer`, `attachReplay`, `renderFeed`, `bindFeedToggle`,
  `makeNameMap`, `buildScrub`, `updateScorebug`, `updateEndscreen`, `fit`) — hoisting would shadow
  them and the affected chrome would render as dead nodes (tandem, 2026-08-23). Ours are
  `cfModuleBar` and `cfPatchGrid`. A test asserts this by reading the file.

### Transport rules

The four surgical edits to the copied chrome, and nothing else:

1. **`--band` and `--hudscale` are set on `:root` by `relayout()`.** Bullwhip's page sizes the
   transport in CSS and has only `fit()`; we extend that inline function into `relayout()`, which
   measures `#transport` and writes `--band: <height>px` and `--hudscale` (a 0.75–1.0 factor from
   the frame width) onto `document.documentElement`. Everything else reads them; nothing else
   writes them.
2. **No overlay sits in the transport band.** `#endscreen` is `position:absolute; inset:0` inside
   `#board-wrap`, which is already a sibling *above* `#transport`; we pin it explicitly with
   `bottom: var(--band, 0px)` so it can never grow over the bar, and `#modulebar` /`#patchgrid`
   live above the board.
3. **Every seek dismisses the endcard.** `attachReplay`'s seek callback calls
   `options.endscreen.classList.remove("show")` before `setIndex(next, true)`, in addition to
   `updateEndscreen`'s existing "only show at the last event" rule.
4. **Scrubber beats are clickable labelled buttons.** In `buildScrub`, the `div.beat-marker`
   elements become `<button type="button" class="beat-marker <kind>" aria-label="<label>"
   title="<label>">` that seek to their event index; the CSS keeps `.beat-marker` and adds a rule
   for **every kind we emit** — `.beat-marker.round`, `.chat`, `.sanction`, `.collapse`,
   `.patchdead`, `.fallback`, `.end` — and no other kind is ever put on the scrubber. Beat labels
   are spectator English ("Round 7", "Cog-C punishes Cog-A", "Patch 3 stripped bare"), never
   internal notation.

### Readouts

- **Scorebug** (`#scorebug`, six plates in slot order): seat colour chip, `Cog-C`, the real policy
  name underneath, the score in big digits, a maintenance chip (`clean ×4`, `planted ×6`,
  `blue ×3`, `held 2/2`), a `▶` while a seat's decision is pending, and a module badge — the
  secret favourite dot in `allelopathic` (spectator-only, the cogs never see it), `FROZEN 2` in
  `mushrooms`, the owned patch numbers in `harvest`. Plate CSS keeps
  `.plate-name { flex: 1 1 auto; min-width: 3.2em }` and hides the secondary labels under 640 px.
- **Board** (`#table`, canvas, bullwhip's `draw()` retargeted): `cleanup` → an orchard block whose
  apple count is drawn as apples, over a river strip whose **pollution gradient** darkens with
  `pollution` (the idea's overlay); `harvest` → six patch cards with apple counts and a **tombstone
  glyph** on dead patches; `allelopathic` → a **colour-share stacked bar** over the 60 slots with a
  ripeness overlay; `mushrooms` → three mushroom rows plus **reward particles that fly from the
  bite to every seat plate the bite pays** (`flow[]`), which is the only way a spectator can see
  who a blue mushroom paid.
- **Clock** (`#clock`): `ROUND 7 OF 20 · WAITING ON 2` / `· SETTLED` / `· FINAL` — real numbers,
  never internal notation.
- **Feed** (`#feed`, bullwhip's `renderFeed`, per-round blocks): one line per decision
  ("Cog-C eats 2 green, plants 1 blue — +2.0"), per chat line, per sanction ("Cog-D burns Cog-A:
  −1.0 / −3.0"), per collapse or dead patch, and a muted line per fallback ("Cog-E fell back to
  steward — timeout").
- **Chart** (bullwhip's `drawChart` on the board): the module's primary resource over rounds with
  the maintenance quantity as a second trace (pollution / dead-patch count / plurality share /
  green+blue share).
- **Endcard** (`#endscreen`): final standings — alias, policy name, score — plus welfare, whether
  the commons survived, and the end reason when it is not `complete`.
- **Legible at 360 px wide.** The softmax.com featured-match iframe is about that wide, so the
  scorebug, clock, chart and feed are checked at 360 px, not at desktop width, and
  `viewer-smoke.png` is the evidence.
- **The say band, and the worst-case text fixture.** A seat's remark is model-authored text drawn
  on the canvas, and the server caps it at `chat_max_chars = 140` runes. The layout **reserves a
  band for it above the cog row**, sized from that cap in the bubble's own font (`sayMetrics()` in
  `renderer.js`) and reserved whether or not anyone is speaking, so the board does not jump when a
  remark lands; the bubble wraps to as many lines as the text needs and a word wider than the box
  is broken on rune boundaries. **A remark is never ellipsized** — ellipsis is for a label, and
  when the band would take more than 45 % of the frame the font shrinks instead of the text.
  Because every replay CI can produce is written by scripted baselines (no `ANTHROPIC_API_KEY`, so
  the longest thing anyone says is 40 runes), that path is exercised by a **worst-case renderer
  fixture**: `tools/ci/text_fixture/index.html` loads the real `client/renderer.js` and hands it a
  full-cap remark on **every** seat at once — Latin, one unbroken 140-rune word, CJK,
  surrogate-pair emoji — over each of the four module boards at five canvas sizes down to 360 px.
  It asserts its own strings are still 140 runes and that every rune of them came back out of a
  `fillText` call with no ellipsis, and `ci.yml`'s own step drives it with
  `viewer_smoke.mjs --strict-text-bounds`, whose `canvas_text` line is the evidence.

---

## Packaging

**`compose.yaml`** (meadow's, renamed — the manifest image placeholder is derived from the compose
**service name**):

```yaml
services:
  commons_family:
    image: coworld-commons-family:latest
    platform: linux/amd64
    build:
      context: .
      network: host
```

so the placeholder is `{{COMMONS_FAMILY_IMAGE}}`.

**`Dockerfile`** — meadow's, unchanged in shape (python:3.12-slim, the same pinned
fastapi/uvicorn/websockets/pydantic/numpy/boto3 line, the same `/app/coworld/examples/…` mirror),
plus two shims so the CI smoke and the manifest have real entrypoints:
`/bin/commons-family` → `exec python -m coworld.examples.commons_family.game.server` and
`/bin/commons-family-player` → `exec python -m coworld.examples.commons_family.player.player`,
both `chmod +x`. **`Dockerfile.replay-viewer`** is bullwhip's, verbatim except the workdir name and
the module path (emscripten/emsdk 4.0.15, nimby 0.1.27, Nim 2.2.4).

**`coworld_manifest_template.json`** — meadow's, with: `$schema` kept; tags
`["social","commons","public-goods","melting-pot","simultaneous","multiplayer","llm"]`;
`game.name: "commons_family"`; `game.runnable` `{type:"game", image:"{{COMMONS_FAMILY_IMAGE}}",
run:["/bin/commons-family"], env:{"ANTHROPIC_API_KEY_URI":
"secret://coworld/commons-family/anthropic_api_key"}}` (without that env the hosted game container
never receives the secret and every league episode silently plays scripted);
`"replay_viewer": {"bundle": "static-replay-viewer"}`; a real `config_schema` with
`additionalProperties: false`, `num_agents` `minimum: 6, maximum: 6`, and `minItems: 6,
maxItems: 6` on `tokens` and `players`; a `results_schema` covering every results key above with
`reason` an enum of exactly `["complete","deadline","no_players"]`.

**`game.docs`** — `readme` `{"type":"text","value":"<the whole of
src/coworld/examples/commons_family/README.md, inline>"}`, **inline text and not a `uri`**: the
acceptance checklist spells this member out literally, and a reader of the manifest should not
have to fetch a URL to read the game's own front page (a test asserts the value is byte-identical
to the README). Plus `pages[]`: `rules.md` (the shared round and the scoring formula), `modules.md` (the four
physics with their numbers), `institutions.md` (ledger / sanctions / norm / chat and what each
variant switches on), `policies.md` (how to field a policy: `PLAYER_PROMPT` vs `PLAYER_SCRIPTED`,
the reply schema and its caps). **`game.protocols` carries BOTH `player` and `global`**, each an
object (`{"type":"uri","value":"…/game/docs/player_protocol_spec.md"}` and
`…/global_protocol_spec.md`), never a bare string.

**Variants — six, `num_agents: 6` in every one.** Every variant also carries `rounds: 20`,
`round_seconds: 20`, `min_round_seconds: 3`, `player_connect_timeout_seconds: 180` and six
`players[]` display names:

| id | name | distinguishing `game_config` |
|---|---|---|
| `cleanup` | Clean Up | `module:"cleanup"`, `ledger_public:true`, `sanctions_enabled:true`, `chat_enabled:true`, `norm_text:"Posted norm: one apple each, and someone cleans every round."`, `seed:20260824` |
| `harvest-open` | Commons Harvest (Open) | `module:"harvest"`, `property_rights:"open"`, `ledger_public:true`, `sanctions_enabled:false`, `chat_enabled:true`, `seed:20260825` |
| `harvest-closed` | Commons Harvest (Closed) | `module:"harvest"`, `property_rights:"closed"`, same institutions as `harvest-open`, `seed:20260826` |
| `harvest-partnership` | Commons Harvest (Partnership) | `module:"harvest"`, `property_rights:"partnership"`, same institutions, `seed:20260827` |
| `allelopathic` | Allelopathic Harvest | `module:"allelopathic"`, `ledger_public:true`, `sanctions_enabled:true`, `chat_enabled:true`, `seed:20260828` |
| `mushrooms` | Externality Mushrooms | `module:"mushrooms"`, `ledger_public:true`, `sanctions_enabled:true`, `chat_enabled:true`, `seed:20260829` |

The three `harvest-*` variants are the idea's property-rights A/B and differ **only** in
`property_rights` and `seed`, which is what makes them comparable.

**Certification fixture** — `certification.game_config`:
`{"num_agents": 6, "module": "cleanup", "rounds": 8, "round_seconds": 6, "min_round_seconds": 3,
"seed": 20260824, "ledger_public": true, "sanctions_enabled": true, "chat_enabled": true,
"norm_text": "Posted norm: one apple each, and someone cleans every round.",
"player_connect_timeout_seconds": 180, "players": [six names]}`, and `certification.players`
seats **all six**, one per declared bundled player:
`[commons-prompt, steward, cleaner, punisher, free-rider, random]`. Every declared bundled player
occupies at least one slot (a fixture that omits a declared runnable fails `players_missing`), and
`len(certification.players) == num_agents == 6 == SMOKE_SEATS`. Duration: 8 rounds × the 3 s
pacing floor ≈ **24–48 s** with no credentials; the replay is ~110 events at bullwhip's 450–1500 ms
per-event dwell ≈ **70 s of playback**, comfortably longer than the viewer smoke's 10 s soak.

**Bundled players** (`player[]`, all six on `{{COMMONS_FAMILY_IMAGE}}` running
`["/bin/commons-family-player"]`):

| id | env | description |
|---|---|---|
| `commons-prompt` | `PLAYER_PROMPT: "<default steward strategy in words>"` | the reference prompt policy |
| `steward` | `PLAYER_SCRIPTED: "steward"` | takes a sustainable share, maintains when the resource needs it |
| `cleaner` | `PLAYER_SCRIPTED: "cleaner"` | spends one unit on the public good every round |
| `punisher` | `PLAYER_SCRIPTED: "punisher"` | steward that pays to burn the worst over-taker on the ledger |
| `free-rider` | `PLAYER_SCRIPTED: "free_rider"` | takes the maximum, never maintains |
| `random` | `PLAYER_SCRIPTED: "random"` | uniform legal decisions; the variance control |

**Grader** (`grader[]`): `commons-grader`, same image,
`run: ["python","-m","coworld.examples.commons_family.grader.commons_grader"]`.

**`tools/ci/policies.json`** (phase 40 mints these; **both champions are `PLAYER_PROMPT`**,
fillers are the scripted baselines and must be distinct versions from the champions):

```json
[{"name":"commons-family-steward","run":"/bin/commons-family-player",
  "env":{"PLAYER_PROMPT":"Take the sustainable share and no more: work out what the resource replaces each round, divide by six, take that. Spend an effort unit on the maintenance act whenever the resource is degrading. Say what your quota is and keep to it.","USE_BEDROCK":"true"}},
 {"name":"commons-family-warden","run":"/bin/commons-family-player",
  "env":{"PLAYER_PROMPT":"Read the ledger first. Match the most restrained cog, not the average one. If one cog is taking more than its share two rounds running, punish it once and say why; otherwise never pay for punishment.","USE_BEDROCK":"true"},
  "player":"<daveey-1 player id>"},
 {"name":"commons-family-freerider","run":"/bin/commons-family-player",
  "env":{"PLAYER_SCRIPTED":"free_rider"}},
 {"name":"commons-family-cleaner","run":"/bin/commons-family-player",
  "env":{"PLAYER_SCRIPTED":"cleaner"}}]
```

**Workflows** — `.github/workflows/ci.yml` and `coworld-release.yml` from coworld-builder
`templates/`, with `<slug>` = `commons-family`, `<IMAGE>` = `coworld-commons-family`,
`<SEATS>` = `6`. `tools/ci/docker_smoke.sh` (mode 100755) and `tools/ci/viewer_smoke.mjs`
(verbatim, no substitutions) copied from the same templates. **One substitution the template does
not anticipate:** its `test` job is Nim (`nim r … tests/*.nim`); this game is Python, so that job
becomes `actions/setup-python@v5` (3.12) → `pip install -r requirements.txt pytest` →
`PYTHONPATH=src python -m pytest tests/ -v`. The `docker-smoke` and `wasm-viewer` jobs are taken
unchanged (the wasm job's Nim/emsdk toolchain is for `replay-viewer/`, which *is* Nim).

---

## Tests

`ci.yml`'s `test` job runs `pytest` over `tests/`:

1. **`tests/test_modules.py`** — the four physics, positive and negative, one exact-arithmetic case
   per numbered rule: `cleanup` pro-rata over-demand, pollution clamped at 0 and 1, effective
   regrowth at three pollution levels, the collapse latch (dead means dead for the rest of the
   episode); `harvest` per-patch splitting, the `< 1.0 → dead forever` rule, `closed` voiding a
   non-owner's demand, `partnership` yielding only when both partners name the patch;
   `allelopathic` the favourite bonus (2.0 vs 1.0), the plant conversion source rule with its
   tie-break and the lost ripe berry, the quadratic ripening at 20/20/20 (10.0/round) and at
   monoculture (30.0/round); `mushrooms` the three payoff splits summing to 1/2/3 of welfare, the
   blue eater getting exactly nothing, `frozen_until = r + ceil(k)`, and the largest-remainder
   spawn with its tie-break.
2. **`tests/test_institutions.py`** — meadow's institutional invariants, kept and extended:
   sanction cost and burn, `ledger_public: false` removing the `ledger` key and every per-cog
   attribution, chat truncated at `chat_max_chars` on rune boundaries, chat visible only in the
   *next* round's observation, the norm text carried through, and **no real policy name anywhere in
   any observation** (the two-name-spaces assertion: `player_names` never appears in an
   `observation` payload).
3. **`tests/test_baselines.py`** — the **bounded-orders / legality assertion on the scripted
   baselines**: every baseline × every module × 400 fuzzed observations (including degenerate ones
   — dead orchard, all patches dead, barren field, frozen seat, `ledger_public: false`). Assert
   every emitted decision parses, every integer is inside its range, `extract + maintain ≤
   effort_budget`, `patch` addresses a real patch, colours are in the enum, `sanction` is never
   self and never out of range and is never set when `sanctions_enabled` is false, `message`
   ≤ 140 runes and `note` ≤ 200 runes, and no baseline ever demands from a dead patch. A baseline
   that produces an illegal or unbounded order fails CI.
4. **`tests/test_episode.py`** — an **end-to-end episode writing a replay**: six scripted seats,
   `rounds: 8`, run through `headless.run_episode(parallel_seats=True)` and through the server's
   settle path, writing `results.json` and `replay.json` to a temp dir. Assert the episode settles
   `reason: "complete"`, the process exits 0, `len(replay["rounds"]) == 8`, scores match the
   formula recomputed independently from the round records, and determinism: two runs with the same
   seed and the same policies produce byte-identical replays modulo `generated_at`. A second case
   drives the deadline path with `play_budget_fraction` set tiny and asserts
   `reason: "deadline"`, partial rounds scored rather than zeroed, exit 0. A third asserts the
   `no_players` path.
5. **`tests/test_replay_parse.py`** — a **strict-UTF-8 replay parse** of the artifact test 4 wrote:
   `data.decode("utf-8")` with no error handler, then `json.loads`; every required key present
   (`format, protocol, config, seed, names, policyNames, seats, rounds, events, results`);
   `len(names) == len(policyNames) == len(seats) == num_agents`; `results.reason` in the legal
   enum; every event `kind` inside the vocabulary and every event carrying `r`; a `message` seeded
   with a multi-byte rune exactly at the 140-rune cap surviving as valid UTF-8; and `note` absent
   from the replay entirely.
6. **`tests/test_llm.py`** — decision handling with a stubbed transport: clean JSON; JSON with
   trailing prose; prose before `{`; missing fields defaulted; an out-of-range field clamped; a
   timeout triggering exactly one retry and then the `steward` fallback with the right `cause`; the
   batch issuing all six requests concurrently (asserted by a barrier in the stub); and the
   **no-credentials path making zero network calls** and returning baseline decisions immediately.
7. **`tests/test_grader.py`** — `welfare` accounting (sanctions are welfare-negative), residual
   value per module, `0 < score` for a steward population and a strictly lower score for a
   free-rider population, `optimum_welfare` finite and ≥ the welfare of a 500-sample random
   population in every module.
8. **`tests/test_viewer_contract.py`** — the payload contract, checked without a browser: the event
   kinds the engine can emit equal the documented vocabulary; every scrubber beat kind has a
   `.beat-marker.<kind>` rule in `client/chrome.css`; the appended game block in
   `replay-viewer/index.html` declares no top-level `function` colliding with the renderer's
   globals; and the four viewer files plus `renderer.js`/`chrome.css` all name the same module
   symbols (`CommonsReplayModule`, `_cf_*`), which is the check that would have caught
   cogame-lantern's split bootstrap statically.

**`docker-smoke` job:** builds the image and runs `tools/ci/docker_smoke.sh` with `SMOKE_SEATS=6`,
`SMOKE_GAME_BIN=/bin/commons-family`, `SMOKE_PLAYER_BIN=/bin/commons-family-player`,
`SMOKE_REQUIRE_REPLAY_JSON=1` — one game container plus six player containers on a per-run
network, driven by the certification fixture. Asserts the game exits 0 having written
`results.json` and a replay that parses as JSON, and that **every player container exited 0**.
Uploads `dist/smoke/replay.json` as the `smoke-replay` artifact.

**`wasm-viewer` job (`needs: docker-smoke`):** asserts `tools/build_replay_viewer.sh` and
`tools/ci/viewer_smoke.mjs` exist and the hook is executable; builds the bundle; asserts
`index.html` and a non-empty `.wasm` are present; then **executes** it —

```
node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
  --replay dist/smoke/replay.json --timeout 90 --strict-text-bounds
```

— in headless chromium against the replay `docker-smoke` just produced. The bundle is **run, not
merely built**: it must set `data-replay-loaded="true"`, never set `data-replay-error`, keep the
clock, position and scorebug advancing through the soak with no uncaught page error, answer the
0 % / 50 % / 100 % scrub probes with three different clocks, and draw no text outside the canvas
(`--strict-text-bounds` is kept: this arena is fixed and the whole board always fits the frame).

---

## Out of scope (v1)

1. **A grid layer.** The idea offers it and the coordinator ruled it out: everything here runs at
   meadow's abstract-round granularity, which is what keeps the planner optimum computable and the
   game exactly solvable. Spatial Clean Up and spatial Commons Harvest, if they are ever wanted,
   are a different coworld built on coworld-ctf, not a variant here.
2. **The exact joint DP for `allelopathic`.** v1 grades that module against the best-monoculture
   planner schedule and says so in `grade.scale`. The exact optimum over heterogeneous colour
   schedules is a research task, not a release blocker, and the league ranks by `results.scores`
   regardless.
3. **Seat counts other than 6.** The idea allows 5–8; v1 pins 6 in the schema (`minimum: 6,
   maximum: 6`), every variant, the cert fixture and `SMOKE_SEATS`, so the four declarations
   cannot drift apart. Other counts are a later variant set, not a v1 knob.
4. **Cross-module episodes and mid-episode institution switching.** One episode is one module with
   one fixed set of institutional dials. The A/B is across episodes, which is how meadow's
   experiment grid already works.
5. **Meadow's `experiments/` sweep drivers, `meadow-rs`, and the blog-post assets.** They are a
   research harness for the single-stock game and its published results; the fork carries the
   engine and the grader, not the sweep. `meadow-rs` in particular would be a second
   implementation of physics that this note deliberately keeps in exactly one place.
6. **Meadow's original single-file HTML replay viewer.** Deleted, not maintained alongside the wasm
   bundle. There is one viewer.
7. **Human playability.** `/client/player`, `/client/global`, `/client/admin` and the `/global`
   socket are served because certification probes them and meadow already has them, but no work
   goes into making them pleasant, and the `{"type":"decision"}` player message exists for protocol
   completeness rather than for a human UI.
8. **Sanction variants beyond meadow's pay-1-burn-3.** No graduated fines, no messaging-only
   shaming channel, no institution the cogs vote on. Those are the obvious follow-ups once the
   four modules have ranked episodes on the board.
