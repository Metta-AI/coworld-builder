# Ecos — grass, grazers, predators, and you are a species, not an individual

**Starter: `Metta-AI/coworld-ctf` (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`.**
Ecos is a real-time continuous-field loop with new rules, RL-vector-shaped bodies and a per-tick
replay, which is exactly the first row of the starter table (and the operator ruling of
2026-08-22 that new physics/ecology games take paintbot, not moba). Paintbot supplies the tick
loop, the sprite-protocol board renderer, the broadcast chrome, the static wasm replay bundle and
the CI shape. **Every convention there holds here unless this note says otherwise.** Two things
paintbot does not have are ported from `Metta-AI/cogame-bullwhip` (mounted at
`/workspace/starters/cogame-bullwhip`) and are named as such where they appear: the *game-side*
batched LLM decision layer (`src/bullwhip/llm.nim`) and the thin prompt-carrying player process
(`src/bullwhip_player.nim`). The four viewer files come from **coworld-ctf only** (see `## Viewer`).

**Design pins (`playbooks/make-coworld.md` §Phase 0), each answered explicitly:**

| pin | how Ecos satisfies it |
|---|---|
| starter by game shape | coworld-ctf (paintbot) — real-time loop, new rules, bodies with vector policies (§ above). |
| public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-ecos`, public — a certification prerequisite (`source-resolves` 404s on private). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | one image; `PLAYER_PROMPT=<strategy>` vs `PLAYER_SCRIPTED=steward\|opportunist` (`## Decisions`). Champions #1 `ecos-keeper` (daveey) and #2 `ecos-bloom` (daveey-1) are both prompt policies; the two fillers are the two scripted baselines. |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` viewer is declared (`## Viewer`, `## Packaging`). |
| real art, starter chrome verbatim | `scripts/art/gen_ecos_art.py` commits the tuft/grazer/predator/soil/loading art; `broadcast_core.js`, `chrome_common.js` and `replay_broadcast.html`'s scorebug/clock/feed/scrubber are reused unchanged (`## Viewer`). |
| legible to a casual spectator | `GEN 4 / 10`, populations as big numbers, doctrine sentences in the feed, three-line population strip; checked at 360 px. |
| two name spaces | aliases `Sedge`/`Bramble`/`Quill` in-game; policy names only in the replay, the scorebug and `results.names` (`## The game`). |
| degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | ≤ 500 s worst case against a 720 s budget, deadline checked between generations, retry-once-then-scripted, `shutdownGraceSeconds = 20` (`## Decisions`, `## Server`). |
| `num_agents` in every variant AND the cert fixture | **3**, in `standard`, in `harsh-spring`, in `certification.game_config`, and as `<SEATS>` in `tools/ci/docker_smoke.sh` (`## Packaging`, `## Tests`). |
| prove it in CI | sim tests, scripted-bot legality test, feasibility oracle, end-to-end episode writing a replay, strict-UTF-8 parse, executed viewer smoke (`## Tests`). |

**Source idea (verbatim, Asana idea task 1217704767328275):**

> 07 Ecos — grass, grazers, predators, and you are a species, not an individual
>
> Three seats take the three trophic roles on a continuous field with births, deaths and energy
> budgets. An episode is ten generations; a seat's score is its population's integrated biomass,
> but any role that crashes the others crashes itself a generation later. Winning means staying in
> balance.
>
> Seats: 3 (roles rotate across episodes)
> Motive: interdependent, non-zero-sum
> Policy interface: RL vector per body
> Fills gap: population dynamics / asymmetric species / evolutionary horizon
> Integrity (anti-collusion): One seat per account per episode; throwing your population to boost a
> friend is expensive and visible — ranking uses the robust mean across full role rotations.
>
> Replay plan (watchability): Field view synced to a live three-line population strip along the
> bottom; births sparkle, deaths fade, and a crash desaturates the whole board (silent spring).
> Boom-bust waves make the ecology readable as rhythm.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

---

## The game

### Seats, roles, names

`num_agents = 3`. Exactly three seats, one per trophic role. **Bodies are sim entities, not
agents** — a seat is a *species* that may have 1 or 200 bodies alive; the platform still seats
three policies.

| slot | in-game cog alias | role when `roleOffset = 0` | chrome team key | colour |
|---|---|---|---|---|
| 0 | `Sedge` | grass (producer) | `green` | `#45a85e` |
| 1 | `Bramble` | grazer (herbivore) | `yellow` | `#ddc531` |
| 2 | `Quill` | predator (carnivore) | `red` | `#e0523a` |

Roles rotate across episodes: `role(slot) = (slot + roleOffset) mod 3`, with
`roleOffset = seed mod 3` when the config leaves `roleOffset = -1` (the default), or pinned by
config for fixtures. Roles rotate, **aliases do not** — `Sedge` is always slot 0. The chrome team
key follows the ROLE, not the slot, so green is always grass on the board and in the strip.

**Two name spaces (pin).** Seats see only the three aliases (`Sedge`, `Bramble`, `Quill`) and role
names in every observation and every prompt; no policy name, player name or account ever reaches a
seat. The replay carries `policyNames[]` alongside `names[]`, and the viewer's scorebug headline
shows the **policy** name (paintbot's `teamName()` in `client/chrome_common.js` already does exactly
this). `results.names[]` carries policy names for the platform.

### Field and clock

- Continuous field, `fieldW = 1000` × `fieldH = 562` world units (16:9), no walls, no obstacles.
  Bodies are clamped to `[0, fieldW] × [0, fieldH]`; there is no wrap-around.
- One episode = **10 generations × 60 ticks = 600 ticks**. Playback is 24 fps, so a full replay is
  25 s of video.
- Every sim quantity is an **integer**. Positions are whole world units; headings are brads
  (0..255, paintbot's convention) resolved through a 256-entry integer sine table; the RNG is
  paintbot's seeded stream. No floats enter sim state, so a seed reproduces a replay bit-exactly on
  any host (the CI determinism test depends on it).

### Bodies

Every body of every species is `{x, y, energy, age, heading, cooldown}`. Caps
(`capGrass = 220`, `capGrazers = 140`, `capPredators = 30`) are hard: a birth that would exceed the
cap does not happen (the parent still pays nothing — see rule 9). Energy ceilings:
`grassEMax = 200`, `grazerEMax = 260`, `predatorEMax = 480`.

Opening state (`standard` variant): 160 grass tufts at 90 energy, 40 grazers at 100, 10 predators
at 220, all placed by the seeded RNG at least 20 units inside the border.

### Doctrine — the decision a seat actually makes

Once per generation each seat submits a **doctrine**: four integers that reparameterise the
deterministic per-body kernel its bodies then run for 60 ticks. This is the batched-swarm cadence
that worked in cogame-hive (LEARNINGS 2026-08-23 hive, item 6) and is the right reading of the
idea's "RL vector per body" for an LLM stack: 30 LLM calls per episode instead of ~250 000
per-body calls, and every body still runs a per-body vector policy.

| role | field | range | default (steward) | meaning in the kernel |
|---|---|---|---|---|
| grass | `seed_threshold` | 60..200 | **100** | tuft seeds when `energy >= seed_threshold` |
| grass | `seed_range` | 24..240 | **90** | dispersal distance of the seedling, world units |
| grass | `seed_cost` | 20..80 | **40** | energy handed to the seedling |
| grass | `crowd_limit` | 0..6 | **3** | refuse to seed if ≥ this many tufts already lie within 55 units of the target point (0 = never refuse) |
| grazer | `birth_threshold` | 80..240 | **90** | grazer splits when `energy >= birth_threshold` |
| grazer | `bite` | 2..14 | **10** | energy drawn from a tuft per tick while grazing |
| grazer | `flee_range` | 0..300 | **40** | sprint away when a predator is nearer than this |
| grazer | `herd` | 0..100 | **40** | weight of steering to the herd centroid vs. to food |
| predator | `birth_threshold` | 150..400 | **320** | predator splits when `energy >= birth_threshold` |
| predator | `hunt_range` | 40..400 | **140** | max lock-on distance to a grazer |
| predator | `rest_energy` | 0..400 | **240** | above this energy it idles instead of hunting |
| predator | `spread` | 0..100 | **40** | weight of steering away from the nearest other predator |

A doctrine holds until the next generation. The doctrine in force during generation 1 is the
steward default for every seat (the first batch of LLM calls goes out **before** generation 1 —
see `## Decisions`; if it fails, generation 1 runs on defaults).

### Tick resolution order (exact, numbered)

Each tick runs these steps in this order, over bodies in ascending index order within each species.
All reads inside a step use the state as it stood at the start of that step, so ordering inside a
species never matters.

1. **Grass photosynthesis.** For each grass tuft: `n` = number of *other* grass tufts within
   `shadeRadius = 55`. `gain = clamp(grassGain - n, 0, grassGain)` with `grassGain = 5`.
   `energy += gain - grassMetabolism` (`grassMetabolism = 1`), clamped to `grassEMax`.
2. **Grazer sense.** For each grazer: `crowd` = grazers within `crowdRadius = 60` (excluding self);
   `stress = min(2, crowd div 6)`. `nearestPredator` = distance to the closest predator.
   `fleeing = nearestPredator < flee_range`. `grazing = (not fleeing) and (nearest tuft within
   biteRadius = 16)`.
3. **Grazing.** For each grazing grazer, in index order: `bite = min(doctrine.bite, tuft.energy)`
   on the nearest tuft (ties → lowest index); `tuft.energy -= bite`;
   `grazer.energy += (bite * 4) div 5` (80 % conversion, integer division). Emits no event.
4. **Grazer movement and metabolism.**
   - grazing → does not move; `energy -= grazerMetabolism + stress` (`grazerMetabolism = 1`).
   - fleeing → moves directly away from the nearest predator at
     `grazerFleeSpeed = 9` units/tick, or **11** if `crowd >= 4` (the many-eyes bonus);
     `energy -= grazerFleeMetabolism + stress` (`grazerFleeMetabolism = 2`).
   - otherwise → target = the **nearest** tuft whose energy is `>= 4 * doctrine.bite`, else the
     nearest tuft of any energy, else a random heading. The step direction is the unit-ish integer
     blend `(100 - herd) * toFood + herd * toHerdCentroid` (herd centroid = mean position of
     grazers within 200 units; if none, `toFood` alone). Speed `grazerSpeed = 6`;
     `energy -= grazerMetabolism + stress`.
5. **Predator sense.** For each predator: `pcrowd` = predators within `crowdRadius = 60`;
   `pstress = min(2, pcrowd div 2)`. `cooldown = max(cooldown - 1, 0)`.
6. **Predator act.**
   - `energy >= rest_energy` → idles in place; `energy -= predatorIdle + pstress`
     (`predatorIdle = 1`).
   - else the target is the nearest grazer within `hunt_range` not already killed this tick.
     - target within `killRadius = 16` **and** `cooldown == 0` → **kill**:
       `gain = min(killCap, killBase + grazer.energy)` with `killBase = 60`, `killCap = 180`;
       `predator.energy = min(predatorEMax, predator.energy + gain)`; the grazer is marked eaten;
       `cooldown = huntCooldown = 12`. The predator does not move this tick.
     - else chase: direction = blend `(100 - spread) * toTarget + spread * awayFromNearestPredator`
       (the avoidance term only when that predator is within 200 units), speed
       `predatorChaseSpeed = 12`; `energy -= predatorChase + pstress` (`predatorChase = 3`).
   - no target in range → roam on a heading redrawn every 12 ticks, speed `predatorSpeed = 7`;
     `energy -= predatorRoam + pstress` (`predatorRoam = 2`).
7. **Clamp positions** to the field rectangle.
8. **Deaths.** Grazers marked eaten die (`predation` event). Any body with `energy <= 0` dies
   (`starve` event). Dead bodies are removed before births.
9. **Births**, grass then grazers then predators, each in index order, each stopping at its cap:
   - grass: for each tuft with `energy >= seed_threshold`, draw a heading, target point at
     `seed_range` units (clamped into the field). If `crowd_limit > 0` and the target already has
     `crowd_limit` or more tufts within 55 units, the seed fails: the parent pays `seedLoss = 10`
     and nothing is born. Otherwise the parent pays `seed_cost + seedLoss` and a tuft is born at
     the target with `seed_cost` energy (`birth` event).
   - grazers / predators: for each body with `energy >= birth_threshold`,
     `half = (energy - splitOverhead) div 2` with `splitOverhead = 20`; the parent keeps `half`, a
     child is born 8 units away on a drawn heading with `half` energy (`birth` event).
10. **Record.** Append this tick's state frame, its events, and the population/biomass series row
    to the replay (see `## Sim module`).

At a generation boundary (every 60 ticks) the sim additionally: closes the generation's
biomass accumulator, checks the end conditions, and — if the episode continues — blocks for the
next batched decision (`## Decisions`).

### Scoring — integrated biomass, higher is better

- Instantaneous biomass `B_i(t)` = sum of the energy of species *i*'s living bodies at the end of
  tick *t* (integer).
- Reference biomass, one per role: `R_grass = 20000`, `R_grazer = 4000`, `R_predator = 3000`.
  These are the healthy steady-state levels measured by the feasibility oracle below; they make the
  three roles commensurable so a rotation-averaged league ranking is meaningful.
- Generation term: `G_i(g) = (Σ_{t in generation g} B_i(t)) / (60 * R_i)` — a float.
- **Seat score** `S_i = Σ_{g=1..10} min(G_i(g), 2.0)`. Generations that were never played
  contribute **0**.
- **Sign: higher is better.** Range 0..20; a balanced ecosystem scores 6..13 per seat (measured).
  `results.win[i] = (S_i == max(S))`.

The `min(·, 2.0)` cap is the anti-boom clause: a generation spent at twice your reference pays no
more than two generations spent at reference, so a boom that risks the crash never pays more than
steady abundance that does not.

**Crash coupling, exactly.** Two mechanisms, both stated, no third:

1. *Mechanical.* Energy only flows up the chain. A grazer's only income is grass energy; a
   predator's only income is grazer energy. Measured half-lives: a predator with no kills loses
   2–3 energy/tick and dies within ~90 ticks (1.5 generations); a grazer with no grass loses
   1–3/tick and dies within ~90 ticks. So a role that strips the level below it starves **about one
   generation later** — the idea's clause, produced by the energy budget rather than declared.
2. *Terminal.* **The episode ends the instant any species' population reaches 0.** Every remaining
   generation scores 0 for **all three seats**. A predator seat that eats the grazers to extinction
   in generation 2 caps its own score near 1.5 where balance would have paid 4–8 (measured below).
   This is what makes "throwing your population" expensive and visible: the wreck is in the replay,
   in the strip, and in every seat's score.

The league ranks by `results.scores` (higher better), and — because roles rotate by seed — a
policy's rating is the platform's mean over episodes that dealt it different roles. That is the
idea's "robust mean across full role rotations"; nothing in the game needs to enforce it. One seat
per account per episode is the platform's seating rule, which three distinct entrant policies
satisfy by construction.

### End conditions and `results.reason`

The episode ends at the FIRST of:

| condition | `results.reason` | `results.ending` | scores |
|---|---|---|---|
| 10 generations played | `complete` | `ten_generations` | as computed |
| any species' population hits 0 (checked at step 9 of every tick) | `complete` | `collapse_grass` / `collapse_grazers` / `collapse_predators` | as computed; unplayed generations score 0 |
| wall clock passes the play deadline (0.6 × `episodeTimeoutSeconds` = 720 s), checked **between generations only** | `deadline` | `deadline` | generations played are scored; the rest are 0 |
| no seat connected within `playerConnectTimeoutSeconds = 180` | `forfeit` | `forfeit` | all zero; results + replay still written |

Those four `results.reason` values — `complete`, `deadline`, `forfeit` — are the only legal ones.
A collapse is a *completed game of Ecos*, not an error, so it reports `complete` and carries the
detail in `results.ending`; phase 60's check 4 therefore passes on a crashed ecology as it should.
`deadline` is declared acceptable here (it means the LLM was slow, not that the game broke), but
the arithmetic in `## Decisions` is sized so it should never fire.

---

## Decisions: LLM with scripted fallback

Both policies ship in the **same image** from day one, env-switched, exactly like bullwhip:
`PLAYER_PROMPT="<strategy text>"` for an LLM policy, `PLAYER_SCRIPTED=steward|opportunist` for a
scripted baseline. **A policy is a prompt**: `players/…` here is one thin process
(`src/ecos_player.nim`, a fork of `src/bullwhip_player.nim`) that connects, sends
`{"type":"prompt","prompt":…,"scripted":…}`, and then only listens. All decision-making happens in
the **game** container (`src/ecos/llm.nim`, forked from `src/bullwhip/llm.nim`), which is what
makes one parallel batch per turn possible and is why the coworld secret must be on the game
runnable (LEARNINGS 2026-08-23 hive, item 2).

### Cadence and the wall-clock budget

One **turn = one generation**. At each generation boundary the game issues **all three seats'
requests as ONE parallel batch** (`curly.makeRequests`, bullwhip's `decideAll`), never sequentially.

```
per generation:  1 batch of 3 requests, llmTimeoutSeconds = 25
worst case:      25 s (batch) + 25 s (one retry batch) = 50 s
10 generations:  <= 500 s   <  720 s  (= 0.6 x episodeTimeoutSeconds 1200)
typical:         ~9 s per batch  ->  ~90 s of LLM + ~4 s of simulation (600 ticks x ~6 ms)
```

`minTurnSeconds = 6` floors the spacing between batch starts, so the episode issues at most
3 requests / 6 s = **30 requests per minute**, the sidecar ceiling that bit cogame-raid
(LEARNINGS 2026-08-23 raid, item 4). Total requests per episode: 30 (+ ≤30 retries).
The play deadline (`0.6 * episodeTimeoutSeconds`, env `COWORLD_TIMEOUT_SECONDS` when present,
otherwise the assumed 1200 — the game container is not given the timeout) is tested **between
generations**; hitting it calls `endEarly()` and settles with `reason: "deadline"`.

### The observation each seat gets

Sent as the `state` frame at every generation boundary, and rendered into the user prompt. Every
number below is visible to the seat; **nothing else is**.

```json
{"type":"state","protocol":"ecos.player.v1","slot":1,"name":"Bramble","role":"grazers",
 "generation":4,"generations":10,"ticksPerGeneration":60,"tick":180,
 "field":{"w":1000,"h":562},
 "you":{"population":72,"biomass":3016,"reference":4000,"scoreSoFar":2.71,
        "doctrine":{"birth_threshold":90,"bite":10,"flee_range":40,"herd":40},
        "meanEnergy":41,"meanCrowd":3,"cap":140},
 "species":[{"role":"grass","alias":"Sedge","population":196,"biomass":14936,"reference":20000,"cap":220},
            {"role":"grazers","alias":"Bramble","population":72,"biomass":3016,"reference":4000,"cap":140},
            {"role":"predators","alias":"Quill","population":9,"biomass":1738,"reference":3000,"cap":30}],
 "history":[{"g":1,"pop":[167,109,10],"bio":[11886,5104,2157],
             "births":[240,61,0],"starved":[97,9,1],"eaten":18,"score":[0.59,1.28,0.72]}, …],
 "density":{"cols":10,"rows":6,
            "grass":[…60 ints…],"grazers":[…60 ints…],"predators":[…60 ints…]},
 "notes":"…your own notes from last generation…",
 "rules":{"metabolism":1,"fleeMetabolism":2,"speed":6,"fleeSpeed":9,"biteRadius":16,
          "conversionPercent":80,"crowdRadius":60,"splitOverhead":20,"energyMax":260}}
```

- **Visible:** all three species' populations, biomass, births, starvations, predation counts and
  per-generation scores for every generation so far; a 10×6 cell density grid per species; the
  seat's own doctrine, mean body energy, mean crowding, and its own constants; the alias of each
  role.
- **Hidden:** the other seats' doctrine numbers, their `notes`, their `say` text, their prompts and
  policy names; the RNG seed; individual body positions and energies (only the coarse density grid
  is given); anything about accounts or the league.

`say` is spectator-only: it is written to the replay and drawn in the feed, and is **never** shown
to another seat. Ecos has no inter-seat channel by design — the anti-collusion motive means a seat
must not be able to negotiate a throw.

### The reply schema

The model must answer with exactly one JSON object, first character `{`:

```json
{"doctrine":{"birth_threshold":110,"bite":8,"flee_range":90,"herd":55},
 "say":"backing off the north pasture",
 "notes":"grass fell 18% last gen; predators at 11 and rising — hold bite <= 8"}
```

| field | type | cap | on violation |
|---|---|---|---|
| `doctrine.<4 role fields>` | integer (a numeric string or float is accepted and rounded) | the ranges in `## The game` | absent / non-numeric → **invalid reply**; out of range → **clamped** to the range, recorded as `"clamped":true` on the `doctrine` event |
| `say` | string | **64 characters** | truncated |
| `notes` | string | **400 characters** | truncated |

Extra keys are ignored. **Truncation is on rune boundaries**, never bytes:
`cleanText(text, limit)` = `strip` → if `runeLen > limit`, `runeSubStr(0, limit-1) & "…"`
(bullwhip's `cleanText`; LEARNINGS 2026-08-22 bullwhip — a byte cut put invalid UTF-8 into a replay
and only a strict parser found it). Newlines in `say` become spaces. Both fields are recorded in the
replay and rendered in the feed.

### Prompts

**System prompt** (composed by the game, per seat, per generation): the seat's alias and role in
capitals; the full rule set for that role (its kernel, its four doctrine fields with ranges and
defaults, its metabolism/speeds/caps, what it eats and what eats it); the scoring rule verbatim
including the `min(G, 2.0)` cap and the "episode ends the moment any species hits zero, and every
remaining generation scores zero for everyone" clause; the statement that the other two seats are
run by other cogs deciding simultaneously and that nothing it writes is read by them; and the
output contract, ending:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

(Bedrock/Haiku answers prose-first without that sentence — playbook §Phase 1.)

**User prompt:** the observation above rendered as a compact table (one row per generation played,
columns `gen | grass n/B | grazers n/B | predators n/B | births | starved | eaten | your score`),
then the density grid as three 10×6 integer grids, then `YOUR NOTES FROM LAST GENERATION`, then the
operator block:

> GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
> requested format):
> `<PLAYER_PROMPT>`

then a one-line restatement of the reply shape with the seat's own four field names and ranges.

**Transport:** bullwhip's ladder, haiku-only (LEARNINGS 2026-08-23 raid, item 4 — the sonnet
fallback times out on every sidecar call and turns one throttle into a cascade):
`bedrockModelIds() = ["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`, `BEDROCK_MODEL` overrides.
`maxOutputTokens = 900` (400 truncates mid-JSON). No `output_config.effort` — Haiku 4.5 400s on it.
Credentials in order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` / `AWS_BEARER_TOKEN_BEDROCK`)
→ `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`. With none, the client disables itself immediately
and every seat plays `steward` — this is what keeps offline certification green.

**Champion prompts** (phase 50 uploads these; both are `PLAYER_PROMPT` policies):

- `ecos-keeper` (champion #1, daveey): *"You are a steward. Your score is integrated biomass, so
  what you want is many generations of solid, boring abundance — not one spike. Every generation,
  read the two other populations first: if the species you depend on has fallen more than 20% since
  last generation, back off before you do anything else (grass: seed cheaper and wider; grazers:
  drop bite by 2 and raise flee_range; predators: raise rest_energy and cut hunt_range). Only push
  for growth when the level below you is at or above its reference. Never let any population fall
  under a fifth of its cap — if one does, the whole episode can end and every remaining generation
  scores zero for you too. Keep notes of the last three generations' populations and of what your
  last change did."*
- `ecos-bloom` (champion #2, daveey-1): *"You play for high steady yield, close to the limit but
  never over it. Each generation estimate the maximum sustainable harvest: your reproduction should
  roughly match the losses you took last generation, no more. Push your own numbers up while the
  species below you is growing, and cut hard the moment its growth turns negative — a crash costs
  you every remaining generation, so treat the first shrinking generation as the alarm, not the
  second. Vary one doctrine number at a time so you can tell what worked, and write the experiment
  in your notes."*

### Scripted baselines (both fieldable, both fillers)

`steward` — the verified default doctrine (the bold column in the doctrine table) plus two
closed-loop corrections applied at each generation boundary, in this order:

1. **Recruit when thin.** If my population `< 0.4 × myCap`: grass `seed_threshold -= 20`;
   grazers `birth_threshold -= 20`; predators `birth_threshold -= 40`.
2. **Back off when my food is thin.** If the species I eat is below `0.4 ×` its cap
   (grass reads *grazer pressure* instead — grazers above `0.6 ×` their cap):
   grazers `bite -= 4`, `flee_range += 40`; predators `hunt_range -= 60`, `rest_energy += 80`;
   grass `seed_range += 40`, `seed_cost -= 10`.

Every result is clamped to the declared range, so the baseline is legal by construction (asserted
in `tests/test_baseline.nim`).

`opportunist` — the same two corrections over a greedier constant doctrine: grass
`{120, 140, 30, 4}`, grazers `{100, 12, 30, 20}`, predators `{280, 200, 300, 30}`. It scores higher
when the other two seats are cautious and crashes the field when they are not — a useful, honestly
weaker filler.

### Degrade, never hang

- Batch timeout `llmTimeoutSeconds = 25`. On transport error, non-2xx, refusal, `max_tokens`
  before any `{`, unparseable JSON, or a missing/non-numeric doctrine field, that seat alone is
  retried **once** in the next batch with the appended hint *"Your previous reply was invalid.
  Respond with ONLY the requested JSON object, with all four doctrine fields as whole numbers in
  range."*
- Still failing → that seat plays the **`steward` scripted doctrine** for that generation, logged
  as `ecos llm: seat N falling back to scripted doctrine` and recorded on the `doctrine` event as
  `"source":"fallback"`. `decideAll` never raises; the episode always advances.
- 401/403 disables the client for the rest of the episode (all seats scripted from then on);
  429 is logged and retried in the next generation's batch.
- The episode settles early rather than overrunning: the play deadline is checked between
  generations, `endEarly()` scores what was played, artifacts are written, and — as
  cogame-lantern taught — `/healthz` and `/global` keep answering for
  `shutdownGraceSeconds = 20` before `quit(0)`, because hosted certification pings the global
  websocket **after** the pods start.

---

## Sim module

New code lives in `src/ecos/`, mirroring paintbot's split (`src/ctf/`). What is forked, what is
kept verbatim, and what is deleted:

| paintbot path | ecos | note |
|---|---|---|
| `src/ctf/sim_types.nim` | `src/ecos/sim_types.nim` | fork: `GameVersion`, the flatty wire types, the constants above. Field order is sacred, same as paintbot. |
| `src/ctf/sim.nim` | `src/ecos/sim.nim` | fork: the tick loop and the 10 numbered rules replace the CTF gameplay core. |
| `src/ctf/sim_config.nim` | `src/ecos/sim_config.nim` | fork: `GameConfig` lifecycle + `config.update`, fields = the config schema in `## Packaging`. |
| `src/ctf/sim_state.nim` | `src/ecos/sim_state.nim` | fork: logging, `gameHash`, event emission, spawn placement. |
| `src/ctf/global.nim` | `src/ecos/global.nim` | fork, heavily reduced: keep the sprite-protocol emitter, layer/object pooling, map bands, the chrome `TextMessage` smuggling and `boardRenderScaleFor`. **Delete** fog-of-war/FOV, first-person PiP, rig art, grenade/spray/shield/barrier families, endzone bakes, perks and handicaps. |
| `src/ctf/broadcast.nim` | `src/ecos/broadcast.nim` | fork: `BroadcastTracker` + `buildStateJson` keep their shape; teams become the three roles; `lead` becomes the population strip series. |
| `src/ctf/events.nim` | `src/ecos/events.nim` | fork: the event vocabulary below. |
| `src/ctf/replays.nim`, `replay_runtime.nim` | `src/ecos/replays.nim` | rewritten: Ecos records **state frames**, not inputs (see below). |
| `src/ctf/server.nim` | `src/ecos/server.nim` | fork of the route/artifact/shutdown skeleton; the player protocol is bullwhip's JSON frames. |
| `src/ctf/arena.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `labels.nim`, `roster.nim` | — | deleted. Ecos has no walls, no map generator, no articulated rigs, no perk roster. A single tiled soil bake replaces the map. |
| `tools/` probes, `caos*`, `arena/` wit bindings, `client/league_replayer.html` | — | deleted. Keep `tools/build_replay_viewer.sh` and `tools/ci/`. |

New: `src/ecos/llm.nim` (from `cogame-bullwhip/src/bullwhip/llm.nim`), `src/ecos/scripted.nim`
(the two baselines), `src/ecos.nim` (entrypoint, forked from `src/ctf.nim`: seed randomisation
before `config.update`, same sentinel handling), `src/ecos_player.nim` (from
`cogame-bullwhip/src/bullwhip_player.nim`).

### Event vocabulary (the replay's `events[]`)

One JSON row per event, `t` = tick. `sp` is `"grass" | "grazers" | "predators"`.

| `k` | fields | when |
|---|---|---|
| `birth` | `t, sp, x, y, e, px, py` | rule 9; `px,py` = parent position (the sparkle draws parent→child) |
| `starve` | `t, sp, x, y, age` | rule 8, `energy <= 0` |
| `predation` | `t, x, y, e, byX, byY` | rule 8, grazer eaten; `by*` = the predator's position |
| `doctrine` | `t, seat, sp, gen, fields{4 ints}, source ("llm"\|"retry"\|"fallback"\|"scripted"), clamped (bool), say, notes, latencyMs` | one per seat per generation boundary |
| `generation` | `t, gen, pop[3], bio[3], score[3]` | at each generation close |
| `alarm` | `t, sp, pop, cap` | first tick a species drops below `0.15 × cap` (once per species per crossing) — drives the desaturation |
| `collapse` | `t, sp` | a species reached 0 |
| `end` | `t, reason, ending, scores[3]` | terminal |

`notes` is recorded (it is what makes an LLM seat's reasoning auditable in the replay) but is drawn
only in the feed's expanded row; `say` is the headline. Both are already rune-truncated.

### The replay file (`ecos.replay.v1`)

**Strict UTF-8 JSON, one document.** Ecos records *state*, not inputs, so playback never
re-simulates and a seek is an array index — the wasm module decodes and draws, and there is no
native/wasm divergence to chase.

```json
{"protocol":"ecos.replay.v1","game":"ecos","gameVersion":"1",
 "seed":1234567,"roleOffset":1,
 "names":["Sedge","Bramble","Quill"],
 "policyNames":["ecos-keeper","ecos-steward","ecos-bloom"],
 "roles":["grazers","predators","grass"],
 "config":{"fieldW":1000,"fieldH":562,"generations":10,"ticksPerGeneration":60,
           "capGrass":220,"capGrazers":140,"capPredators":30,
           "references":[20000,4000,3000],"grassGain":5,"shadeRadius":55,
           "initGrass":160,"initGrazers":40,"initPredators":10,"variant":"standard"},
 "frames":[{"t":0,"g":[512,88,90, 940,301,90, …],"h":[…],"p":[…]}, …],
 "series":{"pop":[[0,160,40,10], …],"bio":[[0,14400,4000,2200], …]},
 "events":[ … ],
 "results":{ … the results.json object verbatim … }}
```

- `frames[i].g|h|p` are flat integer triples `x, y, energy` per living body of that species, in
  sim index order, one frame per tick. No ids: identity is not needed to draw, and births/deaths
  carry their own positions in `events`.
- `series` is the whole-episode population and biomass curve, shipped once so the population strip
  draws its full width on frame 1 (this is paintbot's `lead` trick).
- Everything the viewer needs is in these bytes: names, policy names, roles, config, seed,
  per-tick state, events, results. No server is contacted except S3 for the file.
- Size arithmetic: ≤ 390 bodies × ~12 chars × 600 ticks ≈ **2.8 MB**, plus ~1500 events ≈ 0.3 MB.
  `tests/test_replay.nim` asserts `< 8 MiB`.

### Feasibility check (the solvability oracle — run in phase 10, re-run in CI)

Lighthouse's rule (LEARNINGS 2026-08-22) and lantern's restatement for continuous games: every
threshold must be *reachable by the mechanics*. The constants above were not guessed — they are the
output of a 240-configuration random search plus a 192-point doctrine grid over the exact rules in
`## The game`, scored on 8–12 seeds. Measured, with all three seats playing `steward`:

| run | seeds reaching generation 10 | grass score | grazer score | predator score |
|---|---|---|---|---|
| **all-`steward`** | **12 / 12** | 7.5 – 12.5 | 5.7 – 10.6 | 3.6 – 7.7 |
| greedy predator (`hunt_range 400, birth 200, rest 480`) | 0 / 6 (collapse at gen 1–2) | 2.0 – 4.0 | 0.9 – 1.6 | **1.2 – 1.6** |
| timid predator (`hunt_range 40, rest 60`) | 0 / 6 (predators die by gen 4–5) | 2.7 – 4.2 | 4.3 – 7.9 | **1.3 – 1.5** |
| greedy grazer (`bite 14, birth 80, flee 0`) | 2 / 6 | 3.9 – 11.7 | **2.4 – 4.7** | 6.4 – 13.8 |
| hoarding grass (`seed_threshold 200, crowd_limit 1`) | 4 / 6 | **4.8 – 9.8** | 2.5 – 7.2 | 2.2 – 4.2 |

Typical steward trajectory (seed 3): grass 167→220 tufts (B 11.9k→18.7k), grazers 110→87
(B 5.1k→3.8k), predators 10→4 (B 2.2k→0.8k); 97 kills, 515 grazer births, 1399 grass births,
3 predator births over the episode. Populations stay inside
grass 144–220, grazers 57–140, predators 4–11 — three legible, out-of-phase waves, which is exactly
the "boom-bust rhythm" the idea asks the strip to show. Minimum observed margins across all 12
seeds: grazers ≥ 14, predators ≥ 1.

Two conclusions the builder must preserve: **(a)** the scripted baselines sustain ten generations,
so certification, `docker-smoke` and every all-filler league episode terminate with
`reason: "complete"`, `ending: "ten_generations"`; **(b)** every crash the idea talks about is
reachable, and each one costs its author more than restraint would have. Any change to a constant
in `## The game` re-runs `tests/test_feasibility.nim` (below) — that test is the enforcement, not
this table.

---

## Server, player, protocol

### Game container (`/bin/ecos`)

Routes, kept from paintbot's `src/ctf/server.nim` because hosted certification probes exactly
these before the player pods start (LEARNINGS 2026-08-23 lantern):

| route | behaviour |
|---|---|
| `GET /healthz` | `200 ok`, from process start until `shutdownGraceSeconds` after the artifacts are written |
| `GET /client/player?slot=N&token=T` | the seat's HTML shell (paintbot's, trimmed) |
| `WS /player?slot=N&token=T` | the seat socket; a bad token is refused with a close, never a hang |
| `GET /client/global` | the broadcast client (`client/replay_broadcast.html`, embedded with `staticRead`) |
| `WS /global` | live spectator: paintbot's sprite protocol + the chrome `TextMessage` |

`ecos.player.v1` frames, JSON text, bullwhip shapes:

- game → player: `{"type":"welcome","protocol":"ecos.player.v1","slot":N,"name":"Bramble","role":"grazers","generations":10,"ticksPerGeneration":60}` on connect;
  the `state` frame in `## Decisions` at every generation boundary and at episode end;
  `{"type":"final","done":true,"slot":N,"scores":[…],"roles":[…],"names":[aliases],"generations":G,"reason":…,"ending":…}`, after which the player exits 0.
- player → game: `{"type":"prompt","prompt":"<= 4000 chars","scripted":"steward|opportunist|"}`,
  sent immediately on connect and again after `welcome` (the re-send guards the slot-registration
  race). Any other frame is ignored with a log line.

Startup: `src/ecos.nim` randomises the seed **before** `config.update` (paintbot's rule — every
seed-derived draw, here the opening placement and `roleOffset`, must follow the final seed), waits
up to `playerConnectTimeoutSeconds = 180` for three sockets, starts anyway with whoever is there
(missing seats play `steward`), then runs the generation loop.

Shutdown, in this order (bullwhip's `finishEpisode`, plus lantern's grace): send `final` to every
player socket → broadcast the last global frame → `sleep 500ms` → write
`results.json` (`COGAME_RESULTS_METHOD`, `application/json`) → write the replay
(`COGAME_SAVE_REPLAY_METHOD`, `application/json`) → keep `/healthz` and `/global` answering for
`shutdownGraceSeconds = 20` → `quit(0)`. The player loop wraps `receiveMessage` in
`try/except CatchableError` and exits **0** on a closed or truncated frame (LEARNINGS
2026-08-23 raid, item 3 — otherwise `docker_smoke` passes and certification fails intermittently).

### `results.json`

```json
{"names":["ecos-keeper","ecos-steward","ecos-bloom"],
 "scores":[8.71,6.19,4.95],
 "win":[true,false,false],
 "roles":["grazers","predators","grass"],
 "biomass":[34820,18570,148900],
 "population":[86,4,220],
 "generations":10,
 "births":[515,3,1399],
 "starved":[418,9,1176],
 "predation":97,
 "reason":"complete",
 "ending":"ten_generations"}
```

`names` are **policy** names (platform side); the aliases go to the players and into the replay's
`names[]`. Arrays are indexed by slot, always length 3. Field definitions, so nothing is guessed:
`scores[i] = S_i` (the capped integrated-biomass sum, higher better); `biomass[i]` = the mean of
`B_i(t)` over the ticks actually played, rounded to an integer; `population[i]` = that species'
population on the last played tick; `births[i]`, `starved[i]` = lifetime counts for that species;
`predation` = total grazers eaten; `generations` = generations completed.

---

## Viewer

**All four viewer files come from ONE starter: `Metta-AI/coworld-ctf`.** Named explicitly, because
splicing two starters' halves is what left cogame-lantern with a permanently blank theater
(LEARNINGS 2026-08-23 lantern post-mortem):

| file | source (coworld-ctf) | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | verbatim except the emitted name (`ecos_replay.js`) and the export list renamed `_ecos_*`. **Keep the non-`MODULARIZE` link flags exactly as they are** — no `-s MODULARIZE=1`, no `EXPORT_NAME` — because the worker below bootstraps with `Module.onRuntimeInitialized`. Keep `-s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8` and `--preload-file <root>/data@data`. |
| the wasm entry `.nim` | `replay-viewer/ctf_replay.nim` → `replay-viewer/ecos_replay.nim` | same structure: `stampStage`, `ecos_load_replay`, `ecos_frame`, `ecos_input`, `ecos_packet_ptr/len`, `ecos_error_ptr/len`, `ecos_stage_ptr/len`, and the `emscripten_exit_with_live_runtime()` epilogue (without it Nim's `main` destroys every global while JS keeps calling in). `ecos_load_replay` parses the JSON replay and hydrates the frame array; `ecos_frame` advances/seeks and rebuilds the viewer packet. `ecos_mismatch_tick` is dropped — there is no re-simulation to mismatch. |
| `static_replay*.js` | `replay-viewer/static_replay.js` + `replay-viewer/static_replay_worker.js` | verbatim apart from the `ctf_*` → `ecos_*` export names, the worker name string, and **one added line** in `showFailure`: `document.documentElement.setAttribute('data-replay-error', error.message || String(error))`. The worker keeps `importScripts('./wire_constants.js','./broadcast_core.js','./ecos_replay.js')` and `Module.onRuntimeInitialized` — the matched pair for the link flags above. |
| `index.html` | `client/replay_broadcast.html`, spliced by `Dockerfile.replay-viewer`'s `sed` into `replay-viewer/dist/index.html` | chrome kept verbatim (see below). |

`static_replay.js` already sets `data-replay-loaded="true"` on `<html>` when the worker reports
`loaded` (its line 144); with the added failure line it sets `data-replay-error` on any failure.
Those are the two signals `tools/ci/viewer_smoke.mjs` and phase 60's `viewer-check.yml` read.
`client/broadcast_core.js` and `client/chrome_common.js` ship **verbatim** (they are the renderer
and the chrome library); `tools/gen_wire_constants.nim` still generates `wire_constants.js`.
The manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` and
`tools/build_replay_viewer.sh` (paintbot's, with the image tag renamed) is the `coworld build` hook
that produces the bundle. **Never a `/client/replay` pod.**

### What it draws

Paintbot's chrome elements, reused by id, with Ecos content:

- **Board.** A tiled soil/meadow bake (one static map band set, no walls) under three sprite
  families: grass tufts drawn at one of four energy stages (`grass_tuft_1..4.png`, 24→48 px),
  grazers (`grazer_idle.png` / `grazer_run.png`, 28 px, flipped by heading), predators
  (`predator_idle.png` / `predator_run.png`, 40 px). Body sprites tint slightly darker as energy
  falls, so a starving field reads as dull before anything dies.
- **Births sparkle:** a 6-tick `sparkle.png` burst at the child's position with a hairline to the
  parent's. **Deaths fade:** the body sprite fades to zero alpha over 8 ticks; a `predation` death
  also throws a short red splash. **Crash desaturation:** on an `alarm` event the whole board layer
  crossfades toward greyscale over 24 ticks (and back when the species recovers above
  `0.2 × cap`) — the idea's "silent spring", implemented as a board-layer tint, cosmetic only.
- **Scorebug** (`#scorebug`, `ensureScorebug()` in `client/replay_broadcast.html`, three plates —
  paintbot's plate machinery is already 2–4 team ready, hive learning 7): per role, the **policy
  name** as headline, the current **population** as the big number, and `B 14.9k · 8.71` (biomass ·
  score so far) as the sub-line. Plate colours green / yellow / red by role.
- **Clock** (`#clock-time`, `#clock-caption`): `GEN 4 / 10` with the caption
  `tick 214 of 600` — spelled out, never `T4`.
- **Feed** (`#killfeed`, `pushFeed()`): one row per `doctrine` event —
  `QUILL  hunt 180 · birth 300 · rest 260  "thin the herd"` — plus rows for `alarm`
  (`GRAZERS CRASHING — 18 left`), `collapse` and `end`. Fallback decisions are tagged `auto` so a
  spectator can see when a seat's LLM missed.
- **Population strip** (`#momentum`, the SVG under the scrubber, label re-lettered
  `POPULATION`): the idea's three-line strip, one stepped line per species from `series.pop`,
  each normalised by its own cap so all three share the 0..1 axis. It is fed exactly like
  paintbot's lives series — `state.lead = {"teams":["green","yellow","red"], "pts":[[t,g,h,p], …]}`
  — so `ingestLeadSeries`/`renderMomentum` in `client/chrome_common.js` need no change, and the
  strip is on the same tick axis as the playhead, i.e. synced to the field view.
- Transport, scrubber, spoilers gate, minimap, end-card: paintbot's, untouched. The end-card names
  the ending (`TEN GENERATIONS` / `COLLAPSE — GRAZERS`) and the three scores.

**Legibility at 360 px is a requirement**: the featured-match iframe is ~360 px wide.
`#stage.tiny` (already switched on at `boardW <= 620`) shrinks the feed and pips; carry
bullwhip's `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` plus the under-640px label hiding
into `client/chrome_common.js`/the page CSS, and check the strip's three lines and the `GEN 4 / 10`
clock at 360 px before calling the viewer done.

**Real art, not placeholders.** `scripts/art/gen_ecos_art.py` (Pillow, committed, deterministic)
renders and commits `data/`: the four tuft stages, the two grazer and two predator frames, the
sparkle, the tiled soil, and the loading-screen images the `#lockerroom` markup expects
(`client/art/lockerroom/bg.jpg` = a dawn meadow, plus one portrait per species replacing the
soldier `.webp`s). Regenerating is a committed step, like lantern's map generator, so the art is
reviewable and reproducible rather than hand-dropped binaries.

---

## Packaging

**`compose.yaml`** — one service, one image (game + player binaries):

```yaml
services:
  ecos:
    image: coworld-ecos:latest
    platform: linux/amd64
    build: {context: ., dockerfile: Dockerfile, network: host}
```

The service name is the single source of the manifest placeholder: `services.ecos` →
**`{{ECOS_IMAGE}}`** (LEARNINGS 2026-08-23 lantern — `coworld build` hard-fails anything else;
`tests/test_manifest.nim` asserts the derivation).

**`coworld_manifest_template.json`** — bullwhip's shape with the 0.1.42 strictness hive found
(item 1): top-level `$schema`, ≥3 `tags` (`ecology`, `population-dynamics`, `llm-driven`,
`non-zero-sum`, `three-player`, `real-time`), top-level `episode_timeout_minutes: 20`, top-level
`player[]`, `variants[].description` on every variant, and a real JSON-Schema `game.config_schema`
with `required: ["tokens"]`.

- `game.name`: `ecos`; `game.replay_viewer.bundle`: `static-replay-viewer`.
- `game.runnable`: `{"type":"game","image":"{{ECOS_IMAGE}}","run":["/bin/ecos"],
  "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/ecos/anthropic_api_key"},
  "source_url":"https://github.com/Metta-AI/cogame-ecos/tree/main"}` — the `env` entry is
  mandatory: without it the hosted game container never sees the coworld secret and every league
  episode silently plays scripted (hive learning 2), which surfaces only as a phase-60 check-4
  failure.
- `game.config_schema` properties: `tokens` (string array, 1..8, required), `players`
  (`[{name}]`), `num_agents` (int, default **3**), `seed`, `roleOffset` (-1..2, default -1),
  `generations` (1..12, default 10), `ticksPerGeneration` (10..90, default 60), `initGrass`,
  `initGrazers`, `initPredators`, `grassGain`, `capGrass`, `capGrazers`, `capPredators`,
  `llmTimeoutSeconds` (default 25), `minTurnSeconds` (default 6), `maxOutputTokens` (default 900),
  `model`, `episodeTimeoutSeconds` (default 1200), `playerConnectTimeoutSeconds` (default 180),
  `shutdownGraceSeconds` (default 20). `additionalProperties: false`.
- `game.results_schema`: the `results.json` object above.
- `game.docs` (**text**, not uri — bullwhip's shape):
  `{"readme":{"type":"text","value":"<the 200-word what-it-is>"},
    "pages":[{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<the tick order, doctrine table, scoring>"}},
             {"id":"policies.md","title":"Fielding a policy","content":{"type":"text","value":"<PLAYER_PROMPT / PLAYER_SCRIPTED how-to>"}}]}`.
- `game.protocols` — **both**: `player` (text: the `ecos.player.v1` frames, the doctrine schema and
  the caps) and `global` (text: the `/global` sprite + chrome frame, and the static bundle's
  `index.html?replay=<url>`).
- `player[]`, three entries, all on `{{ECOS_IMAGE}}` with `run: ["/bin/ecos-player"]`:
  `ecos-player` (no env — a prompt policy; `PLAYER_PROMPT` is supplied at upload time),
  `ecos-steward` (`env: {"PLAYER_SCRIPTED":"steward"}`),
  `ecos-opportunist` (`env: {"PLAYER_SCRIPTED":"opportunist"}`).
- `variants[]` — **`num_agents: 3` in both**:
  - `standard`: `{num_agents: 3, generations: 10, ticksPerGeneration: 60, roleOffset: -1,
    initGrass: 160, initGrazers: 40, initPredators: 10, grassGain: 5,
    capGrass: 220, capGrazers: 140, capPredators: 30, players: [{Sedge},{Bramble},{Quill}]}`.
  - `harsh-spring`: same seats, `{num_agents: 3, initGrass: 120, grassGain: 4, initGrazers: 32,
    initPredators: 8}` — a leaner field where restraint matters sooner. It must clear gate (a) of
    `tests/test_feasibility.nim` (all-`steward`, seeds 1..12, all reaching generation 10) before it
    ships; the repair rule if it does not, applied in this order until the gate passes, is
    `initGrass 120 → 140 → 160`, then `grassGain 4 → 5`. No other knob moves, and the shipped values
    are whatever the gate accepted.
- `certification`: `game_config` `{num_agents: 3, seed: 7, generations: 3, ticksPerGeneration: 30,
  playerConnectTimeoutSeconds: 180, players: [{Sedge},{Bramble},{Quill}]}` and
  `players: [{"player_id":"ecos-player"},{"player_id":"ecos-steward"},{"player_id":"ecos-opportunist"}]`
  — every declared player entry seated exactly once, because `players-run` seats the whole roster
  and a `baseline × N` fixture fails `players_missing` (LEARNINGS 2026-08-23 raid, item 2).
  With no credentials offline, `ecos-player` falls back to `steward`, so the fixture is
  deterministic.

**Other packaging files:** `Dockerfile` (paintbot's two-stage nimby build; produces `/bin/ecos` and
`/bin/ecos-player`), `Dockerfile.replay-viewer` (paintbot's, with the ecos file list and the same
`test -f` assertions), `tools/build_replay_viewer.sh` (paintbot's, image tag renamed),
`.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
`tools/ci/docker_smoke.sh` with `<SEATS>` substituted to **3**, `tools/ci/policies.json` naming
`ecos-keeper`, `ecos-bloom`, `ecos-steward`, `ecos-opportunist`.

---

## Tests

All run in `ci.yml`; the sandbox cannot run any of them locally.

1. **`tests/test_sim.nim` — sim units.** Shade-gain table (0..6 neighbours → gain 5..0); bite
   transfer and the `(bite*4) div 5` rounding; predation gain `min(180, 60 + e)` and the 12-tick
   cooldown; crowding stress steps at 6/12 grazers and 2/4 predators; the many-eyes flee speed;
   split arithmetic `(e-20) div 2` and cap refusal; death removal before birth; field clamping;
   doctrine clamping at both ends of all twelve ranges; **determinism** — the same seed and the same
   doctrine script produce an identical `gameHash` after 600 ticks, twice in one process and across
   a fresh `SimServer`.
2. **`tests/test_baseline.nim` — bounded orders / legality.** For 12 seeds × 600 ticks with
   `steward` and with `opportunist` on all three seats: every doctrine field emitted is inside its
   declared range after the closed-loop corrections; every body position is inside the field; no
   energy is negative or above its ceiling; population never exceeds a cap; the baselines never
   raise and never take longer than 1 ms per generation.
3. **`tests/test_feasibility.nim` — the ecological oracle, as a CI precondition.** Re-runs the
   phase-10 check in Nim over both variants: (a) all-`steward`, seeds 1..12, **every** seed reaches
   generation 10 with all three species alive, and per-generation mean populations stay inside
   grass 60..220, grazers 10..140, predators 1..30; (b) collapse stays reachable — greedy predator
   `(400,200,480)` reaches generation 10 in ≤1 of 6 seeds, timid predator `(40, rest 60)` in ≤1 of
   6, greedy grazer `(bite 14, birth 80, flee 0)` in ≤3 of 6; (c) mis-play costs its author —
   the greedy-predator predator score and the hoarding-grass `(200, crowd 1)` grazer score are each
   below 0.75× the all-`steward` mean for that role. Any constant change that breaks the ecology
   fails here rather than in a dead replay.
4. **`tests/test_replay.nim` — end-to-end + strict UTF-8.** Plays a full scripted episode headless,
   writes `results.json` and the replay, then re-reads the replay bytes: `validateUtf8 == -1`
   (strict), parses as JSON, `protocol == "ecos.replay.v1"`, `frames.len == ticksPlayed`,
   `series.pop.len == ticksPlayed`, every event tick in `0..ticksPlayed`, at least one `birth`, one
   `starve`, one `predation`, ten `generation` events and exactly one `end`, `results.scores.len ==
   3`, `results.reason` in `{complete, deadline, forfeit}`, file size `< 8 MiB`. A seat is fed a
   `say`/`notes` of multi-byte runes exactly at the 64/400 caps and the recorded strings are
   asserted valid UTF-8 and ≤ the cap (the bullwhip byte-truncation bug).
5. **`tests/test_llm.nim` — decision layer.** `extractJsonObject` on fenced/prose-prefixed replies;
   numeric strings and floats accepted; out-of-range clamped with `clamped: true`; missing field →
   invalid; a stubbed transport that times out, 429s, 403s or returns junk produces `steward`
   decisions for those seats, never raises, and marks `source: "fallback"`; one batch carries all
   open seats (assert `RequestBatch.len == openSeats`).
6. **`tests/test_manifest.nim` — packaging.** `num_agents == 3` in **every** variant and in the
   certification fixture; the image placeholder equals the one derived from `compose.yaml`'s
   service name (`{{ECOS_IMAGE}}`); `replay_viewer.bundle == "static-replay-viewer"`;
   `game.docs.readme` + non-empty `pages`; `game.protocols.player` **and** `global` present;
   `ANTHROPIC_API_KEY_URI` present in `game.runnable.env`; every `player[]` id appears at least once
   in `certification.players`; `episode_timeout_minutes` top-level.
7. **`tests/test_broadcast.nim` — chrome frame.** `teams` keys are exactly `green|yellow|red` and
   map to grass/grazers/predators under a rotated `roleOffset`; plate numbers equal populations;
   `lead.teams`/`lead.pts` shape matches `chrome_common.js`'s expectation (`[t, g, h, p]` rows);
   `over` present on the terminal frame with the ending string; feed rows for `doctrine`, `alarm`,
   `collapse` are well-formed and their text is ≤ the caps.
8. **`docker-smoke` (`tools/ci/docker_smoke.sh`, `<SEATS>` = 3).** Builds the image, runs a real
   3-seat episode in containers, asserts the **player** containers exit 0 (raid item 3), validates
   `results.json` against the results schema, and writes the replay to `SMOKE_REPLAY_OUT`
   (`dist/smoke/replay.json`), uploaded as the `smoke-replay` artifact.
9. **`wasm-viewer` job — the bundle is EXECUTED, not merely built.** `needs: docker-smoke`,
   downloads `smoke-replay`, builds the bundle via `tools/build_replay_viewer.sh`, installs
   Playwright pinned **1.55.0**, and runs **`tools/ci/viewer_smoke.mjs`** against that replay over
   local HTTP. Pass requires `data-replay-loaded="true"` (or the `coworld-replay` bridge `ready`)
   **and** three different clock readouts at 0 %, 50 % and 100 %; `data-replay-error` or silence
   fails the job. Evidence (`viewer-smoke.png`, `viewer-smoke.json`) uploads on success and failure.
   This is the gate that cogame-lantern did not have.

---

## Out of scope (v1)

- **Mutation / heritable traits.** Doctrines are per-species, not per-body, and children inherit
  nothing but position and energy. The idea's "evolutionary horizon" is served by ten generations of
  policy adaptation, not by genetics.
- **Per-body policy calls.** A seat never addresses one body. The RL-vector-per-body interface is
  the deterministic kernel; the LLM reparameterises it.
- **Weather, seasons, terrain, water, obstacles.** The field is flat, uniform and wall-free; the
  only spatial structure is the bodies themselves. `harsh-spring` varies the opening richness, not
  the terrain.
- **Inter-seat messaging.** No channel, by design (anti-collusion). `say` is spectator-only.
- **Disease, scavengers, decomposers, a fourth trophic level, omnivory.**
- **Live spectator features beyond what paintbot gives free:** no POV lens, no first-person PiP, no
  minimap authoring, no achievements, no perks/handicaps.
- **Cross-episode persistence.** Every episode starts from the seeded opening state; nothing carries
  over except the league rating.
- **Re-simulating playback.** The viewer decodes recorded state; there is no replay-hash mismatch
  mode and no `--mismatch-quit`.
- **More than two variants**, and any variant that changes `num_agents`. Ecos is a three-seat game.
