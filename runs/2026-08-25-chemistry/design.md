# MP Chemistry — keep three autocatalytic food cycles fed while the room is full of shiny useless molecules

**Starter: `Metta-AI/coworld-ctf` (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`.**
Chemistry is a real-time grid loop with new rules, per-tick grid actions and a per-tick replay —
the first row of the starter table ("any real-time game loop, grid OR continuous physics, new rules
written for this coworld"). Paintbot supplies the tick loop, the sprite-protocol board renderer, the
broadcast chrome, the static wasm replay bundle and the CI shape. **Every convention there holds
here unless this note says otherwise.** Two things paintbot does not have are ported from
`Metta-AI/cogame-bullwhip` (mounted at `/workspace/starters/cogame-bullwhip`) and are named as such
where they appear: the *game-side* batched LLM decision layer (`src/bullwhip/llm.nim`) and the thin
prompt-carrying player process (`src/bullwhip_player.nim`). **All four viewer files come from
coworld-ctf only** (see `## Viewer`). There is no `OPEN` section: every rule the idea leaves loose is
decided below, with the reason.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design), each answered explicitly:**

| pin | how Chemistry satisfies it |
|---|---|
| starter by game shape | `Metta-AI/coworld-ctf` (paintbot) — a real-time grid loop with rules written for this coworld; nothing external to port bit-exactly (the Melting Pot substrate is the *inspiration*, not a binary we reproduce). |
| public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-chemistry`, **public** — a certification prerequisite (`source-resolves` 404s on private). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | one image; `PLAYER_PROMPT="<strategy>"` vs `PLAYER_SCRIPTED=courier\|freeloader` (`## Decisions`). Champions #1 `chemistry-foreman` (daveey) and #2 `chemistry-metabolist` (daveey-1) are both prompt policies; the two fillers are the two scripted baselines — `freeloader` **is** the idea's "background shirker bots in scoring". |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` viewer is declared (`## Viewer`, `## Packaging`). |
| real art, starter chrome verbatim | `scripts/art/gen_chemistry_art.py` commits floor/wall/vat/vent/molecule/cog art; `client/chrome_common.js` ships **byte-for-byte** and `client/replay_broadcast.html` is the starter's page with a game block appended (`## Viewer`). |
| legible to a casual spectator | `SHIFT 4 / 12`, three named gauges reading `RUNNING` / `STARVING` / `COLD`, molecules drawn over heads, a shame panel naming hoarders; checked at 360 px. |
| two name spaces | anonymous cog aliases `Argon … Hob` in-game and in every prompt; policy names only spectator-side (`roster[].pol`, the roster strip, `results.names`) — `## The game` §Seats. |
| degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | ≤ 513 s worst case against a 720 s budget, deadline checked between shifts, retry-once-then-scripted, `shutdownGraceSeconds = 20` (`## Decisions`, `## Server`). |
| `num_agents` in every variant AND the cert fixture | **8**, in all four variants, in `certification.game_config`, and as `<SEATS>` in `tools/ci/docker_smoke.sh` (`## Packaging`, `## Tests`). |
| prove it in CI | sim tests, bounded-orders/legality test on both baselines, a feasibility oracle, an end-to-end episode writing a replay, a strict-UTF-8 parse, an **executed** viewer smoke (`## Tests`). |

**Source idea (verbatim, Asana idea task 1217748465122695):**

> MP Chemistry — keep three autocatalytic food cycles fed while the room is full of shiny useless molecules
>
> Port of Melting Pot's chemistry (two / three metabolic cycles, with and without distractors — one coworld, four configs). A reaction graph of molecules; certain combinations react, some reactions yield edible food, and some cycles are autocatalytic — they keep producing food once running, but only if cogs keep delivering the right intermediates. Distractor variants litter the map with molecules that do nothing but can be hoarded; there are more cogs than distractors, so someone must work. Public-goods provision with division of labour and a built-in temptation to shirk.
>
> Seats: 8
> Motive: public goods / role allocation
> Policy interface: per-tick grid actions (pick up, carry, drop to trigger reactions); LLM variant exposes the reaction graph as text — an unusually good fit for language policies
> Fills gap: the only idea with a real crafting/reaction graph; tests whether cogs can self-assign roles across parallel tasks
> Integrity (anti-collusion): role-splits that leak via replays are in-band skill; background shirker bots in scoring.
>
> Replay plan (watchability): each cycle drawn as a gauge ('running / starving'); molecules carried shown over heads; a 'who's hoarding distractors' shame panel.
>
> Source: substrates chemistry__{two,three}_metabolic_cycles{,_with(_plentiful)_distractors}.

---

## The game

### Seats, aliases, names

`num_agents = 8`. Exactly eight seats, one cog each, all in one room, no teams. Eight is the idea's
number and it is also the number the labour arithmetic below is built on: the three-cycle room has
**six supply lanes**, so two cogs are always surplus — someone can always shirk, and the room still
works if they do. Nobody is "on a team": the plates in the scorebug are the three *cycles*, not
sides.

| slot | in-game cog alias | body colour (paintbot `slots[].color`) | home / cache cell |
|---|---|---|---|
| 0 | `Argon` | `red` | (2, 2) |
| 1 | `Borax` | `orange` | (2, 4) |
| 2 | `Cinder` | `yellow` | (2, 6) |
| 3 | `Dram` | `lime` | (2, 8) |
| 4 | `Ember` | `light blue` | (29, 2) |
| 5 | `Flint` | `blue` | (29, 4) |
| 6 | `Gilt` | `pink` | (29, 6) |
| 7 | `Hob` | `white` | (29, 8) |

Aliases are fixed to slots and never rotate. Cells are `(col, row)`, origin top-left.

**Two name spaces (pin).** A seat sees only aliases — its own and the other seven — in every
observation, every prompt and every broadcast `say`. No policy name, player name, account or model
name ever reaches a seat. The replay carries `policyNames[]` alongside `names[]`; the viewer's roster
strip and the `#squad` pips show the **policy** name for non-baseline seats (paintbot's
`roster[].pol` path in `client/chrome_common.js`, `teamPolicies()`), and `results.names[]` carries
policy names for the platform. Both, not either.

### The room

- A fixed grid, `cols = 32` × `rows = 18`, cell size 48 board-px → a 1536 × 864 board. **The whole
  board always fits the frame**, which is why the viewer drops `#viewpanel` (zoom bar + minimap)
  entirely (`## Viewer`).
- Walls: the full border ring (row 0, row 17, col 0, col 31) plus two 2×2 pillars at
  {(13,8),(14,8),(13,9),(14,9)} and {(18,8),(19,8),(18,9),(19,9)}. Everything else is floor.
- **Three vents**, one per feedstock species, each a single cell:
  `resin` at (4, 3), `spark` at (28, 3), `brine` at (16, 15).
- **Three reactors** ("vats"), each a 3×3 pad centred on:
  `amber` (16, 4), `beryl` (23, 11), `cobalt` (9, 11).
  Each pad's **spill ring** is the 12 floor cells orthogonally/diagonally surrounding the 3×3 pad.
- **Distractor vents** (variants 2 and 4 only): `glitter` at (9, 3), `quartz` at (23, 3).
- Every sim quantity is an **integer**; the RNG is paintbot's seeded stream and is used only for
  tie-free-but-arbitrary choices that the rules below name explicitly. No floats enter sim state, so
  a seed reproduces a replay bit-exactly (the determinism test depends on it).

Lane lengths are deliberately equal — every vent→reactor Manhattan distance is 11–13 cells:

| reactor | feedstocks | lane 1 | lane 2 |
|---|---|---|---|
| `amber` (16,4) | `resin` + `spark` | resin (4,3) → 13 | spark (28,3) → 13 |
| `beryl` (23,11) | `spark` + `brine` | spark (28,3) → 13 | brine (16,15) → 11 |
| `cobalt` (9,11) | `resin` + `brine` | resin (4,3) → 13 | brine (16,15) → 11 |

### The reaction graph (this is the text the LLM gets)

Five molecule species exist. Three are feedstocks, two are inert distractors:

| species | kind | source | used by |
|---|---|---|---|
| `resin` | feedstock | resin vent (4,3) | `amber`, `cobalt` |
| `spark` | feedstock | spark vent (28,3) | `amber`, `beryl` |
| `brine` | feedstock | brine vent (16,15) | `beryl`, `cobalt` |
| `glitter` | **inert** | glitter vent (9,3) | nothing |
| `quartz` | **inert** | quartz vent (23,3) | nothing |

Each reactor consumes a *distinct pair*, so every feedstock serves two reactors — that shared
scarcity is what makes role allocation a real decision instead of a fixed assignment.

Reactor state is `{charge, stock[two feedstocks], cooldown}`.

- **Reaction.** When `charge ≥ 1`, `cooldown == 0` and both stocks ≥ 1: consume 1 of each feedstock,
  set `charge = min(chargeMax, charge + 1)`, set `cooldown = reactionCooldown`, and emit
  `foodYield = 1 + charge div 3` FOOD tokens (charge *after* the increment; 1..5 at
  `chargeMax = 12`).
- **Autocatalysis, exactly.** Charge is the catalyst. Every reaction makes the next one *more*
  productive (`1 + charge div 3`), and a running cycle needs no restart — but charge decays, so
  "running" is a state that has to be *held*, not reached.
- **Decay.** Every `chargeDecayPeriod = 60` ticks (once per shift) each reactor's `charge -= 1`,
  floored at 0. Reaching 0 emits a `cold` event.
- **Cold start.** A reactor at `charge == 0` cannot react. When `charge == 0` and both stocks ≥
  `coldStartCost = 3`: consume **3 of each** feedstock, set `charge = 1`, emit **no food**, emit a
  `restart` event. Letting a cycle die therefore costs the room six deliveries of pure investment —
  the public-goods bite, priced in labour rather than declared.
- **Misdrop.** Any molecule dropped on a reactor pad that the reactor does not take (a distractor,
  or the third feedstock) is **absorbed and destroyed**; a `misdrop` event fires and the delivering
  seat's `misdrops` counter increments. Matter is lost, the reactor is unharmed. This is the graph
  test: a policy that reads the graph never pays it, a policy that grabs the nearest shiny thing pays
  it constantly. (Chosen over a jam-and-clear mechanic because it needs no repair job and keeps the
  board legible.)
- **Food.** A FOOD token is not a molecule: it cannot be picked up or carried, only eaten. Newly
  produced tokens are placed on free spill-ring cells of their reactor, **ordered by Manhattan
  distance to the cog that delivered the molecule which triggered the reaction** (ties by `(row,
  col)`), so a supplier's work pays out at its own feet. If the ring has fewer free cells than
  `foodYield`, the surplus is lost and a `spoil` event fires. A token that is not eaten within
  `foodLifetime = 240` ticks (10 s) rots (`rot` event).
- **Vents.** Every `ventPeriod = 8` ticks a feedstock vent emits one unit onto the first free cell
  among its orthogonal neighbours in N, E, S, W order; it emits nothing while `ventGroundCap = 6` or
  more units of its species already lie loose on the floor, or if all four neighbours are occupied.
  Distractor vents use `distractorPeriod` (0 = the vent does not exist) and `distractorGroundCap`.

### What a cog can do (per-tick grid actions)

Each cog occupies one cell, carries **at most one molecule** (`carryCap = 1`), and emits exactly one
action per tick from this vocabulary — this is the idea's "per-tick grid actions (pick up, carry,
drop to trigger reactions)":

`move_n` · `move_s` · `move_e` · `move_w` · `take` · `drop` · `wait`

- `move_*` is legal only every `moveCooldown = 2` ticks (12 cells/s) and only into a floor cell that
  is not a wall and not occupied by another cog; an illegal move degrades to `wait`.
- `take` picks up a molecule lying on the cog's own cell if the hand is empty; otherwise `wait`.
- `drop` puts the carried molecule on the cog's cell if the hand is full **and** the cell holds no
  molecule; on a reactor pad it goes into that reactor's stock (or is absorbed as a misdrop).
- Eating is **not** an action: any cog whose cell holds a FOOD token at resolution step 5 eats it
  (+1 score, `eat` event). That is what makes camping the spill ring a strategy and shirking a
  temptation.

**Where the actions come from.** A seat does not emit 720 actions by hand — no LLM can. Once per
**shift** (60 ticks) each seat submits a **standing order** (`## Decisions`), and a deterministic
**courier kernel** turns that order into the per-tick action stream for the whole shift. The sim's
policy interface is per-tick grid actions exactly as the idea says; the LLM chooses the *job*, the
kernel walks the floor. This is the batched-swarm cadence that worked in cogame-hive and cogame-ecos:
96 LLM calls per episode instead of 5 760.

The kernel, given order `{job, molecule, reactor}` and the current tick's state:

1. `supply` — if the hand holds `molecule`: BFS to the nearest cell of the target reactor's 3×3 pad
   and `drop` on arrival. If the hand is empty: BFS to the nearest loose unit of `molecule` (ties by
   `(row, col)`) and `take` on arrival; if no unit is loose, BFS to that species' vent's nearest free
   orthogonal neighbour and `wait` there. If the hand holds anything else: step one cell off any pad
   (first legal of N,E,S,W) and `drop`.
2. `forage` — BFS to the nearest FOOD token; if none exists, BFS to the spill ring of the named
   reactor (or, if none named, of the live reactor with the highest charge; ties by reactor order
   amber, beryl, cobalt) and `wait` there.
3. `hoard` — as `supply`, but the destination is the seat's own **home cell** (table above); dropping
   there increments that seat's `hoard` counter. Hoarding scores nothing, ever. It exists because
   the idea's shame panel needs something to shame and because misreading the graph must be
   *expressible*.
4. `idle` — `wait` in place.

BFS is over floor cells only (other cogs are not obstacles for path *planning*, only for the move
itself), with neighbour expansion in N, E, S, W order, so paths are unique and deterministic.

### Shifts, and the exact tick resolution order

One episode = `shifts = 12` × `ticksPerShift = 60` = **720 ticks**. Playback is 24 fps, so a full
replay is 30 s of video (comfortably longer than the viewer soak gate — ecos, 2026-08-23).

Every tick runs these nine steps in this order. Within a step, seats resolve in **ascending slot
order**, and reactors in the fixed order amber, beryl, cobalt. All reads inside a step use the state
as it stood at the start of that step unless the step says otherwise.

1. **Vents emit** (resin, spark, brine, glitter, quartz in that order), per the vent rule above.
2. **Kernel intent.** Each cog's kernel computes this tick's action from its standing order and the
   current state. A cog whose `moveCooldown` counter is still running emits `wait` instead of a
   `move_*`.
3. **`take` / `drop` resolve**, in slot order. A `take` of a molecule another cog already took this
   tick fails (degrades to `wait`). A `drop` on a pad updates that reactor's stock, or fires
   `misdrop`.
4. **Moves resolve**, in slot order, against the *live* board: a move into a cell a lower-numbered
   seat has already moved into this tick fails and degrades to `wait`. Cooldown counters reset on a
   successful move.
5. **Auto-eat**, in slot order: every cog standing on a FOOD token eats it (+1 to that seat's
   `foodEaten`, `eat` event), whether or not it moved this tick.
6. **Reactions**, reactor order: cold start first (if `charge == 0`), else a reaction if the
   preconditions hold. Food placement per the spill-ring rule.
7. **Charge decay** on ticks where `tick mod chargeDecayPeriod == 0` and `tick > 0`.
8. **Food rot**: any token whose age reaches `foodLifetime` is removed (`rot` event).
9. **Record**: append this tick's state frame, its events and the charge-series row to the replay.

At a shift boundary (every 60 ticks) the sim additionally closes the shift accounting, emits the
`shift` event, checks the end conditions, and — if the episode continues — blocks for the next
batched decision (`## Decisions`).

### Scoring — food eaten, higher is better

- **Seat score `S_i` = the number of FOOD tokens seat *i* ate over the episode.** An integer,
  0 upward.
- **Sign: higher is better.** `results.win[i] = (S_i == max(S))` — ties mark multiple winners, which
  is correct for a public-goods game and needs no tiebreak.
- **The league ranks by `results.scores`** (the platform's mean over episodes). Nothing else is
  ranked; deliveries, hoards and misdrops are reported for the viewer and for analysis, and are
  **not** in the score.

The score is deliberately pure Melting Pot: your reward is what you ate. That is what makes the
dilemma real. What keeps it from collapsing into "everyone camps" is mechanical, not moral:

1. Food lands at the **deliverer's** feet first (the spill-ring ordering rule), so working pays
   directly. A camper's edge is that it is already standing on a ring cell and eats one tick sooner.
2. `foodYield` grows with charge, so a well-fed cycle drops 3–5 tokens at once and one camper cannot
   eat them all before the supplier turns around.
3. Nothing is produced without deliveries. A room of eight shirkers eats the opening food, watches
   three cycles go cold, and scores near zero **for everyone** — visible in the replay as three grey
   gauges and an empty floor.

The idea's "integrity" clause needs no extra machinery: role splits announced in `say` are broadcast,
recorded, and are in-band skill; and the shirker bot the idea asks to be present in scoring is
`chemistry-freeloader`, a league **filler**, so every champion is graded in a room that already
contains shirkers.

### End conditions and `results.reason`

The episode ends at the FIRST of these, all checked at a **shift boundary**:

| condition | `results.reason` | `results.ending` | scores |
|---|---|---|---|
| 12 shifts played | `complete` | `shift_limit` | as computed |
| every reactor has been `charge == 0` for 3 consecutive shift boundaries **and** no FOOD token is on the floor | `complete` | `famine` | as computed; unplayed shifts add nothing |
| wall clock passes the play deadline (0.6 × `episodeTimeoutSeconds` = **720 s**) | `deadline` | `deadline` | shifts played are scored; the rest add nothing |
| no seat connected within `playerConnectTimeoutSeconds = 180` | `forfeit` | `forfeit` | all zero; results + replay are still written |

Those three — **`complete`, `deadline`, `forfeit`** — are the only legal `results.reason` values. A
famine is a *completed game of Chemistry*, not an error, so it reports `complete` and carries the
detail in `results.ending`; phase 60's check 4 therefore passes on a dead room, as it should.
`deadline` is admissible (it means the LLM was slow, not that the game broke), but the arithmetic in
`## Decisions` is sized so it should not fire.

### Throughput arithmetic, and the feasibility gates

These are **design targets derived from the constants above, not measurements**. The enforcement is
`tests/test_feasibility.nim` (`## Tests`), not this table — ecos, 2026-08-23, shipped a note whose
"measured" oracle was a hypothesis the builder had to repair.

- A courier's round trip is ~12 cells out + ~12 back at 2 ticks/cell ≈ 50 ticks, plus a `take` and a
  `drop` → **≈ 1 delivery per 60-tick shift per courier**.
- A reactor loses 1 charge per shift (`chargeDecayPeriod = 60`), so holding it steady needs 1
  reaction/shift = **2 deliveries/shift**. Three reactors → 6 deliveries/shift → **6 couriers**, out
  of 8 seats. The two-cycle variants need 4. That knife-edge is the game: two cogs may shirk for
  free; three cannot.
- Food: ~1 reaction/shift/reactor at charge 3–8 yields 2–3 tokens → ~6–9 tokens/shift → **≈ 80–100
  tokens per episode**, ~10–12 per seat in a working room; single digits in a lazy one.
- A cold start costs 6 deliveries ≈ 6 courier-shifts and produces no food: half a cycle's whole
  episode-long output.

The gates `tests/test_feasibility.nim` enforces, over seeds 1..12 on all four variants:

- **(a) The baselines sustain the room.** All-`courier`: ≥ 10/12 seeds finish with every reactor at
  `charge ≥ 1`, total food made ≥ 40, and every seat scoring ≥ 3. This is what makes certification,
  `docker-smoke` and all-filler league episodes end `complete` / `shift_limit`.
- **(b) The temptation is real.** In a 6 × `courier` + 2 × `freeloader` room, the freeloaders' mean
  score exceeds the couriers' mean score.
- **(c) Shirking is collectively self-defeating.** All-`freeloader` rooms make less than 15 % of the
  all-`courier` food total, or end `famine`.
- **(d) Distractors bite.** On `three-cycles-plentiful-distractors`, a test-only `nearest` kernel
  (take the nearest molecule of any species, carry it to the nearest reactor) scores below 0.6 × the
  `courier` mean. `nearest` lives only in `tests/test_feasibility.nim`; it is not a shipped policy.

**If a gate fails, repair constants in this order and re-run — no design bounce is needed:** gate
(a): `ventPeriod 8 → 6`, then `moveCooldown 2 → 1`, then `chargeDecayPeriod 60 → 72`; gate (b):
`foodLifetime 240 → 180`; gate (c): `charge0 3 → 2`; gate (d): `distractorPeriod 2 → 1`. Any change
to a constant in this section re-runs the oracle. **That test is the enforcement, not this table.**

---

## Decisions: LLM with scripted fallback

Both policies ship in the **same image** from day one, env-switched, exactly like bullwhip:
`PLAYER_PROMPT="<strategy text>"` for an LLM policy, `PLAYER_SCRIPTED=courier|freeloader` for a
scripted baseline. **A policy is a prompt.** `src/chemistry_player.nim` (a fork of
`cogame-bullwhip/src/bullwhip_player.nim`) is one thin process that connects, sends
`{"type":"prompt","prompt":…,"scripted":…}` and then only listens. All decision-making happens in the
**game** container (`src/chemistry/llm.nim`, forked from `src/bullwhip/llm.nim`) — which is what makes
one parallel batch per turn possible, and is why the coworld secret must be on the *game* runnable
(hive, 2026-08-23).

### Cadence and the wall-clock budget

One **turn = one shift**. At each shift boundary the game issues **all eight seats' requests as ONE
parallel batch** (`curly.makeRequests`, bullwhip's `decideAll`) — never sequentially.

```
per shift:     1 batch of 8 requests, llmTimeoutSeconds = 20
worst case:    20 s (batch) + 20 s (one retry batch)          = 40 s
12 shifts:     12 x 40 s                                      = 480 s
+ sim:         720 ticks x ~1.5 ms (8 BFS/tick on 480 cells)  ~  1.1 s
+ connect:     player connect grace                           <= 30 s
total worst:   ~513 s   <   720 s  ( = 0.6 x episodeTimeoutSeconds 1200 )
typical:       max(minTurnSeconds 18, ~9 s batch) x 12         ~ 216 s
```

`minTurnSeconds = 18` floors the spacing between batch starts, so the episode issues at most
8 requests / 18 s = **26.7 requests per minute**, under the Bedrock sidecar's 30 rpm per-episode
ceiling that bit cogame-raid. Requests per episode: 96, plus ≤ 96 retries. The play deadline
(`0.6 × episodeTimeoutSeconds`; the game container is **not** given `COWORLD_TIMEOUT_SECONDS`, so
1200 is assumed unless that env var is present) is tested **between shifts**; hitting it calls
`endEarly()` and settles with `reason: "deadline"`.

### The observation each seat gets

Sent as the `state` frame at every shift boundary and rendered into the user prompt. Every number
below is visible to that seat; **nothing else is**.

```json
{"type":"state","protocol":"chemistry.player.v1","slot":3,"name":"Dram",
 "shift":4,"shifts":12,"ticksPerShift":60,"tick":180,
 "room":{"cols":32,"rows":18,"variant":"three-cycles-plentiful-distractors"},
 "you":{"cell":[14,9],"carrying":"resin","home":[2,8],
        "foodEaten":6,"delivered":9,"misdrops":1,"hoard":0,
        "lastOrder":{"job":"supply","molecule":"resin","reactor":"amber","source":"llm"}},
 "reactors":[{"name":"amber","cell":[16,4],"feedstocks":["resin","spark"],
              "charge":7,"chargeMax":12,"status":"running","yieldNow":3,
              "stock":{"resin":2,"spark":0},"cooldown":0,
              "ticksSinceReaction":9,"foodMade":14,"coldStartCost":3},
             {"name":"beryl","…":"…"},{"name":"cobalt","…":"…"}],
 "molecules":{"resin":{"inert":false,"vent":[4,3],"loose":4,"nearestToYou":[12,7]},
              "spark":{"inert":false,"vent":[28,3],"loose":6,"nearestToYou":[24,5]},
              "brine":{"inert":false,"vent":[16,15],"loose":2,"nearestToYou":[16,14]},
              "glitter":{"inert":true,"vent":[9,3],"loose":17,"nearestToYou":[11,6]},
              "quartz":{"inert":true,"vent":[23,3],"loose":14,"nearestToYou":[21,6]}},
 "food":{"loose":3,"cells":[[15,6],[15,7],[22,10]]},
 "cogs":[{"alias":"Argon","cell":[15,3],"carrying":"spark","foodEaten":8,
          "delivered":11,"misdrops":0,"hoard":0,
          "lastOrder":{"job":"supply","molecule":"spark","reactor":"amber"},
          "say":"I hold spark to Amber all game"}, "… 8 entries, slot order …"],
 "history":[{"shift":3,"reactions":[2,1,0],"foodMade":[5,3,0],
             "eaten":[1,0,2,1,0,1,0,0],"coldStarts":0,"misdrops":2,
             "charge":[6,4,0]}, "…"],
 "notes":"…your own notes from last shift…",
 "rules":{"reactions":[{"reactor":"amber","inputs":["resin","spark"],"output":"food",
                        "yield":"1 + charge div 3","requires":"charge >= 1 and both stocks >= 1"},
                       {"reactor":"beryl","inputs":["spark","brine"],"output":"food",
                        "yield":"1 + charge div 3","requires":"charge >= 1 and both stocks >= 1"},
                       {"reactor":"cobalt","inputs":["resin","brine"],"output":"food",
                        "yield":"1 + charge div 3","requires":"charge >= 1 and both stocks >= 1"}],
          "autocatalysis":"every reaction adds 1 charge (max 12); yield rises with charge",
          "chargeDecay":"-1 charge per reactor every 60 ticks (once per shift)",
          "coldStart":"at charge 0 a reactor consumes 3 of EACH feedstock to return to charge 1 and makes no food",
          "misdrop":"a molecule dropped on a reactor that does not take it is absorbed and destroyed",
          "inert":["glitter","quartz"],
          "carryCap":1,"moveCooldown":2,"foodLifetime":240,"ventPeriod":8,
          "scoring":"your score is the number of food tokens YOU eat; food is eaten automatically by standing on it"}}
```

- **Visible:** the whole room's aggregate state — every reactor's charge, status, stocks, yield and
  food made; every species' vent, loose count and the nearest unit to you; every loose food token's
  cell; all eight cogs' cells, carried molecule, food eaten, deliveries, misdrops, hoard, **last
  shift's order** and last shift's broadcast `say`; the full per-shift history; your own private
  `notes`; and the complete reaction graph as text.
- **Hidden:** the other seats' orders **for the shift about to be played** (decisions are
  simultaneous); their private `notes`; their prompts, policy names, player names and accounts; the
  RNG seed; the vent emission schedule beyond the stated period; anything about the league.

`say` **is** an inter-seat channel, by design: this game is about self-assigning roles across
parallel tasks, so an 80-character broadcast is the coordination surface. It is delivered to every
seat in the next shift's observation, drawn in the viewer feed, and recorded in the replay. The
anti-collusion posture the idea states is exactly this: role splits leak via replays and are in-band
skill.

### The reply schema

The model must answer with exactly one JSON object whose first character is `{`:

```json
{"job":"supply","molecule":"resin","reactor":"cobalt",
 "say":"Cobalt is cold - I bring resin, someone bring brine",
 "notes":"amber at 7 and safe; cobalt died in shift 3 because nobody covered brine"}
```

| field | type | cap / range | on violation |
|---|---|---|---|
| `job` | string enum | `supply` \| `forage` \| `hoard` \| `idle` | missing or not in the enum → **invalid reply** |
| `molecule` | string enum | `resin` \| `spark` \| `brine` \| `glitter` \| `quartz` | required for `supply` and `hoard`; missing/unknown there → **invalid reply**. A feedstock the named reactor does not take is **accepted as written** (the misdrop is the graph test and must stay expressible). A species whose vent is absent in this variant → **invalid reply**. Ignored for `forage`/`idle`. |
| `reactor` | string enum | `amber` \| `beryl` \| `cobalt` | required for `supply`; optional for `forage`. Naming a reactor absent in this variant → **clamped** to the present reactor with the lowest charge, recorded as `"clamped":true` on the `order` event. Missing for `supply` → **invalid reply**. |
| `say` | string | **80 characters** | truncated |
| `notes` | string | **320 characters** | truncated |

Extra keys are ignored. **Truncation is on rune boundaries**, never bytes: `cleanText(text, limit)`
= `strip` → if `runeLen > limit`, `runeSubStr(0, limit-1) & "…"` (bullwhip's `cleanText`; a byte cut
put invalid UTF-8 into a replay and only a strict parser found it — bullwhip, 2026-08-22). Newlines
in `say` become spaces. Both fields are recorded in the replay; both are rendered in the feed. The
same rune-safe truncation applies to every string that reaches the replay, including LLM error text
(capped at 200 characters).

### Prompts

**System prompt** (composed by the game, per seat, per shift): the seat's alias in capitals; the full
rule set — the grid, the action vocabulary, `carryCap 1`, `moveCooldown 2`, the standing-order model
("you choose a job for the next 60 ticks; a courier kernel walks it for you"); the reaction graph as
the table in `## The game` including which species are **inert**; charge, decay, cold-start cost and
the yield formula; the scoring rule verbatim ("your score is the food *you* eat; food appears on the
spill ring nearest the cog that delivered the triggering molecule"); the statement that the other
seven cogs are other policies deciding **simultaneously**, that `say` is heard by all of them next
shift, and that `notes` is private; and the output contract, ending:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

(Bedrock/Haiku answers prose-first without that sentence — playbook §Phase 1.)

**User prompt:** the observation above rendered compactly — a reactor table (`reactor | takes |
charge | status | stock | yield | food made`), a molecule table (`species | inert | loose | nearest to
you`), a cog table (`alias | cell | carrying | ate | delivered | hoard | last job | last say`), the
per-shift history table, `YOUR NOTES FROM LAST SHIFT`, then the operator block:

> GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
> requested format):
> `<PLAYER_PROMPT>`

then a one-line restatement of the reply shape with the legal enum values **for this variant** (the
absent reactor and the absent distractor species are omitted from the list — precomputing the legal
choice set in the observation is what halved formal-output fallbacks in escrow).

**Transport:** bullwhip's ladder, haiku-only (raid, 2026-08-23 — the sonnet fallback times out on
every sidecar call and turns one throttle into a cascade):
`bedrockModelIds() = ["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`, `BEDROCK_MODEL` overrides.
`maxOutputTokens = 700`. No `output_config.effort` — Haiku 4.5 400s on it. Credentials in order:
Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` / `AWS_BEARER_TOKEN_BEDROCK`) →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`. With none, the client disables itself immediately and
every seat plays `courier` — which is what keeps offline certification green and deterministic.

**Champion prompts** (phase 50 uploads these; both are `PLAYER_PROMPT` policies):

- `chemistry-foreman` (champion #1, daveey): *"You are the shift foreman. Before anything else, read
  the three reactors: any cycle at charge 0 is a hole in the floor — restarting it costs three of
  each feedstock and makes no food, so never let one fall to 1 without covering it. Each shift, pick
  the single lane (reactor + feedstock) whose stock is lowest on the reactor with the lowest charge,
  and take it. Announce your lane in `say` in the form 'resin to Amber' and keep it for as long as
  nobody else claims it, so the others can fill the lanes you left. Never carry glitter or quartz —
  they are inert, and dropping one on a vat destroys it and wastes your whole shift. Only forage
  when all three reactors have both stocks at 2 or more. Keep notes of which alias covered which lane
  last shift."*
- `chemistry-metabolist` (champion #2, daveey-1): *"You play the catalyst, not the calendar. Charge
  compounds: a vat at charge 9 pays three food a reaction and a vat at charge 3 pays two, so pour
  surplus into whichever vat is already highest **once every vat is above 2**, and starve nothing to
  do it. Compute each shift how many deliveries the room needs to hold steady — one reaction per vat
  per shift, two deliveries each — and compare it to how many cogs actually delivered last shift; if
  the room is short, take a lane, and if the room is over-covered, go eat, because unclaimed food
  rots in ten seconds. State plainly in `say` whether the room is short or covered and by how much.
  Ignore glitter and quartz entirely; they are inert and they exist to waste your hands."*

### Scripted baselines (both fieldable, both league fillers)

`courier` — the working baseline, and the fallback every failed LLM decision lands on. At each shift
boundary, purely from the observation and its own slot number (no shared state, so eight couriers
coordinate implicitly by computing the same table):

1. Build the **lane list**: for every reactor present, for each of its two feedstocks,
   `lane = (reactor, species)` with `need = target - stock`, where `target = coldStartCost (3)` if
   the reactor is at charge 0, else `2`.
2. Sort lanes by `need` descending, then by reactor `charge` ascending (feed the dying cycle first),
   then by fixed lane order (amber-resin, amber-spark, beryl-spark, beryl-brine, cobalt-resin,
   cobalt-brine).
3. If every lane has `need <= 0`, emit `{"job":"forage","reactor":<highest charge>}`.
   Otherwise emit `{"job":"supply", …lanes[mySlot mod lanes.len]…}`.
4. `say` = `"<species> to <Reactor>"`; `notes` = "".

With 8 seats and 6 lanes, slots 0–5 take one lane each and slots 6–7 double up on the two neediest —
which is exactly the labour the arithmetic says the room needs.

`freeloader` — the shirker, and the idea's "background shirker bot". Always
`{"job":"forage","reactor":<live reactor with the highest charge>}`, `say = "waiting by the vats"`.
One exception, so a room of eight freeloaders is not a guaranteed zero and never deadlocks the
episode: if **every** reactor is at charge 0, it takes the single largest-`need` lane for that shift.

Every field either baseline emits is inside its declared enum by construction, asserted in
`tests/test_baseline.nim`.

### Degrade, never hang

- Batch timeout `llmTimeoutSeconds = 20`. On transport error, non-2xx, refusal, `max_tokens` before
  any `{`, unparseable JSON, or any **invalid reply** in the table above, that seat alone is retried
  **once** in the same shift's retry batch, with the appended hint *"Your previous reply was
  invalid. Respond with ONLY the requested JSON object, using one of the listed job, molecule and
  reactor values."*
- Still failing → that seat plays the **`courier` order** for that shift, logged as
  `chemistry llm: seat N falling back to scripted order` and recorded on the `order` event as
  `"source":"fallback"`. `decideAll` never raises; the episode always advances.
- 401/403 disables the client for the rest of the episode (all seats scripted from then on); 429 is
  logged and the seat is retried in the next shift's batch.
- A seat that never connected, or whose socket dies mid-episode, plays `courier` for every remaining
  shift. The episode never waits on a socket beyond `playerConnectTimeoutSeconds = 180` at the start
  and never blocks on one mid-episode.
- The episode settles early rather than overrunning: the play deadline is checked between shifts,
  `endEarly()` scores what was played, artifacts are written, and — as cogame-lantern taught —
  `/healthz` and `/global` keep answering for `shutdownGraceSeconds = 20` before `quit(0)`, because
  hosted certification pings the global websocket **after** the player pods start.

---

## Sim module

New code lives in `src/chemistry/`, mirroring paintbot's split (`src/ctf/`). What is forked, what is
kept, and what is deleted — by path:

| paintbot path | chemistry | note |
|---|---|---|
| `src/ctf/sim_types.nim` | `src/chemistry/sim_types.nim` | fork: `GameVersion`, the flatty wire types, the constants above. Field order is sacred, same as paintbot. |
| `src/ctf/sim.nim` | `src/chemistry/sim.nim` | fork: the tick loop and the nine numbered steps replace the CTF gameplay core. |
| `src/ctf/sim_config.nim` | `src/chemistry/sim_config.nim` | fork: `GameConfig` lifecycle + `config.update`; fields = the config schema in `## Packaging`. |
| `src/ctf/sim_state.nim` | `src/chemistry/sim_state.nim` | fork: logging, `gameHash`, event emission, spawn placement. |
| `src/ctf/arena.nim` | `src/chemistry/room.nim` | heavily reduced fork: a **fixed** 32×18 cell grid (walls, pads, vents, homes) and the BFS the kernel uses. The terrain generator, mapSpec, symmetry, validators, pixel queries and `map_pool` are **deleted** — Chemistry has one authored room per variant. |
| `src/ctf/global.nim` | `src/chemistry/global.nim` | fork, heavily reduced: keep the sprite-protocol emitter, layer/object pooling, the chrome `TextMessage` smuggling and `boardRenderScaleFor`. **Delete** fog-of-war/FOV, first-person PiP, rig art, grenade/spray/shield/barrier families, endzone bakes, perks and handicaps. |
| `src/ctf/broadcast.nim` | `src/chemistry/broadcast.nim` | fork: `BroadcastTracker` + `buildStateJson` keep their shape; `teams` becomes the three cycles, `roster` the eight cogs, `lead` the charge series. |
| `src/ctf/events.nim` | `src/chemistry/events.nim` | fork: the event vocabulary below (same `jsonRow`/`eventsJsonl` shape and the same "live emission and re-simulation must be byte-identical" rule). |
| `src/ctf/replays.nim`, `src/ctf/replay_runtime.nim` | `src/chemistry/replays.nim` | rewritten: Chemistry records **state frames**, not inputs (below). |
| `src/ctf/server.nim` | `src/chemistry/server.nim` | fork of the route/artifact/shutdown skeleton; the player protocol becomes bullwhip's JSON frames. |
| `src/ctf/labels.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `roster.nim` | — | deleted. No articulated rigs, no perk roster, no generated terrain. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | kept, forked | still emits `window.CTF_WIRE={…}`. **The global keeps its name**: `client/chrome_common.js` reads `window.CTF_WIRE` at its line 72 and that file ships byte-for-byte, so renaming the global would force a byte change in a file that must not change. |
| `tools/` probes, `caos*`, `arena/` wit bindings, `client/league_replayer.html`, `tools/map_editor*`, `tools/record_*.sh` | — | deleted. Keep `tools/build_replay_viewer.sh` and `tools/ci/`. |

New files: `src/chemistry/kernel.nim` (the courier kernel + BFS), `src/chemistry/llm.nim` (from
`cogame-bullwhip/src/bullwhip/llm.nim`), `src/chemistry/scripted.nim` (the two baselines),
`src/chemistry.nim` (entrypoint, forked from `src/ctf.nim`: seed randomisation **before**
`config.update`, same sentinel handling), `src/chemistry_player.nim` (from
`cogame-bullwhip/src/bullwhip_player.nim`).

`tools/build_replay_viewer.sh` is paintbot's with the image tag renamed **and the inherited bug
fixed**: `mkdir -p` the output parent before the containment check, because the hook `cd`s into a
parent that `coworld build` pre-creates and CI does not (ecos, 2026-08-23).

### Event vocabulary (the replay's `events[]`)

One JSON row per event; `t` = tick, `seat` = slot, `sp` = species, `rx` = reactor name.

| `k` | fields | when |
|---|---|---|
| `take` | `t, seat, sp, x, y` | step 3, a successful pickup |
| `drop` | `t, seat, sp, x, y, rx` (`rx` empty off-pad) | step 3, a successful drop |
| `misdrop` | `t, seat, sp, rx` | step 3, a molecule the reactor does not take |
| `react` | `t, rx, charge, yield, by` (`by` = the seat whose delivery triggered it, `-1` if none) | step 6 |
| `restart` | `t, rx, by` | step 6, a cold start consumed 3+3 |
| `cold` | `t, rx` | step 7, a reactor's charge reached 0 |
| `eat` | `t, seat, x, y` | step 5 |
| `rot` | `t, x, y` | step 8 |
| `spoil` | `t, rx, lost` | step 6, no free spill-ring cell for `lost` tokens |
| `order` | `t, seat, shift, job, sp, rx, source (`llm`\|`retry`\|`fallback`\|`scripted`), clamped (bool), say, notes, latencyMs` | one per seat per shift boundary |
| `shift` | `t, shift, charge[3], foodMade[3], eaten[8], misdrops, coldStarts` | at each shift close |
| `famine` | `t` | the famine end condition latched |
| `end` | `t, reason, ending, scores[8]` | terminal |

Volume per episode: ~200 `take`/`drop`, ~90 `eat`, 96 `order`, ~12 `shift`, plus incidentals —
under 500 rows. `notes` is recorded (it makes an LLM seat's reasoning auditable) and drawn only in
the feed's expanded row; `say` is the headline. Both are already rune-truncated.

### The replay file (`chemistry.replay.v1`)

**Strict UTF-8 JSON, one document.** Chemistry records *state*, not inputs, so playback never
re-simulates, a seek is an array index, and there is no native/wasm divergence to chase (which is
also why `#mmwarn` and `ctf_mismatch_tick` are dropped).

```json
{"protocol":"chemistry.replay.v1","game":"chemistry","gameVersion":"1",
 "seed":1234567,
 "names":["Argon","Borax","Cinder","Dram","Ember","Flint","Gilt","Hob"],
 "policyNames":["chemistry-foreman","chemistry-courier","…8…"],
 "colors":["red","orange","yellow","lime","light blue","blue","pink","white"],
 "config":{"variant":"three-cycles-plentiful-distractors","cols":32,"rows":18,"cell":48,
           "shifts":12,"ticksPerShift":60,"cycles":3,
           "reactors":[{"name":"amber","cell":[16,4],"feedstocks":["resin","spark"]},
                       {"name":"beryl","cell":[23,11],"feedstocks":["spark","brine"]},
                       {"name":"cobalt","cell":[9,11],"feedstocks":["resin","brine"]}],
           "vents":[{"sp":"resin","cell":[4,3],"inert":false}, "…"],
           "walls":[[13,8],[14,8],"…"],
           "homes":[[2,2],[2,4],"…"],
           "chargeMax":12,"charge0":3,"chargeDecayPeriod":60,"reactionCooldown":6,
           "coldStartCost":3,"foodLifetime":240,"moveCooldown":2,
           "ventPeriod":8,"distractorPeriod":2},
 "frames":[{"t":0,"c":[2,2,-1,0, "…8 quads x,y,carrySpeciesId,foodEaten…"],
            "m":[5,3,0, "…triples x,y,speciesId…"],
            "f":[15,6,240, "…triples x,y,ttl…"],
            "r":[3,0,0,0, "…quads charge,stockA,stockB,cooldown per reactor…"]}, "…720 frames…"],
 "series":{"charge":[[0,3,3,3],[1,3,3,3], "…one row per tick…"]},
 "beats":[{"t":60,"k":"shift","n":1},{"t":352,"k":"cold","rx":"cobalt"},
          {"t":471,"k":"restart","rx":"cobalt"},{"t":720,"k":"gameover"}],
 "events":[ "… the rows above …" ],
 "results":{ "… the results.json object verbatim …" }}
```

- **Self-sufficient by construction.** Names (aliases), policy names, body colours, the full room
  geometry and every rule constant, the seed, per-tick state, the charge series, the beat timeline,
  every event and the final results all live in these bytes. The viewer contacts **no** server except
  S3 for the `.replay` file.
- Species ids are the fixed order `0 resin, 1 spark, 2 brine, 3 glitter, 4 quartz`; `-1` = empty
  hand.
- Size arithmetic: 720 frames × ~250 integers ≈ **0.7 MB**, plus ~500 events ≈ 0.1 MB.
  `tests/test_replay.nim` asserts `< 8 MiB`.

---

## Server, player, protocol

### Game container (`/bin/chemistry`)

Routes, kept from paintbot's `src/ctf/server.nim` because hosted certification probes exactly these
**before** the player pods start (lantern, 2026-08-23):

| route | behaviour |
|---|---|
| `GET /healthz` | `200 ok`, from process start until `shutdownGraceSeconds` after the artifacts are written |
| `GET /client/player?slot=N&token=T` | the seat's HTML shell (paintbot's, trimmed); it never opens the player socket |
| `WS /player?slot=N&token=T` | the seat socket; a bad token is refused with a close, never a hang |
| `GET /client/global` | the broadcast client (`client/replay_broadcast.html`, embedded with `staticRead`) |
| `WS /global` | live spectator: paintbot's sprite protocol + the chrome `TextMessage` |

`chemistry.player.v1` frames, JSON text, bullwhip shapes:

- game → player: `{"type":"welcome","protocol":"chemistry.player.v1","slot":N,"name":"Dram","shifts":12,"ticksPerShift":60,"variant":"…"}` on connect; the `state` frame from `## Decisions` at every shift boundary and at episode end; `{"type":"final","done":true,"slot":N,"scores":[…8…],"names":[…aliases…],"shifts":S,"reason":…,"ending":…}`, after which the player exits **0**.
- player → game: `{"type":"prompt","prompt":"<= 4000 chars","scripted":"courier|freeloader|"}`, sent
  immediately on connect and again after `welcome` (the re-send guards the slot-registration race).
  Any other frame is ignored with a log line.

Startup: `src/chemistry.nim` randomises the seed **before** `config.update` (paintbot's rule — every
seed-derived draw must follow the final seed), waits up to `playerConnectTimeoutSeconds = 180` for
eight sockets, starts anyway with whoever is there (missing seats play `courier`), then runs the
shift loop.

Shutdown, in this order (bullwhip's `finishEpisode` plus lantern's grace): send `final` to every
player socket → broadcast the last global frame → `sleep 500 ms` → write `results.json`
(`COGAME_RESULTS_METHOD`, `application/json`) → write the replay (`COGAME_SAVE_REPLAY_METHOD`,
`application/json`) → keep `/healthz` and `/global` answering for `shutdownGraceSeconds = 20` →
`quit(0)`. The player's receive loop wraps `receiveMessage` in `try/except CatchableError` and exits
**0** on a closed or truncated frame (raid, 2026-08-23 — otherwise `docker_smoke` passes and
certification fails intermittently).

### `results.json`

```json
{"names":["chemistry-foreman","chemistry-courier","chemistry-courier","chemistry-metabolist",
          "chemistry-courier","chemistry-freeloader","chemistry-courier","chemistry-freeloader"],
 "aliases":["Argon","Borax","Cinder","Dram","Ember","Flint","Gilt","Hob"],
 "scores":[12,9,10,14,8,15,7,13],
 "win":[false,false,false,false,false,true,false,false],
 "food_eaten":[12,9,10,14,8,15,7,13],
 "delivered":[11,12,12,10,13,1,12,1],
 "misdrops":[0,0,1,0,0,0,4,0],
 "hoarded":[0,0,0,0,0,0,9,0],
 "reactions":[13,11,7],
 "food_made":94,
 "food_rotted":6,
 "cold_starts":1,
 "shifts":12,
 "reason":"complete",
 "ending":"shift_limit"}
```

`names` are **policy** names (platform side); aliases go to the players and into the replay's
`names[]`. Arrays indexed by slot, always length 8 (`reactions` is length 2 or 3 — one per reactor
present). Field definitions, so nothing is guessed: `scores[i] == food_eaten[i]` (the score, higher
better); `delivered[i]` = molecules that entered a reactor's stock from that seat; `misdrops[i]` =
molecules that seat had absorbed by a reactor that does not take them; `hoarded[i]` = molecules on
that seat's home cell at the end; `reactions[k]` / `food_made` / `food_rotted` / `cold_starts` are
whole-episode counts; `shifts` = shifts completed.

---

## Viewer

**All four viewer files come from ONE starter: `Metta-AI/coworld-ctf`.** Named explicitly, because
splicing two starters' halves (one's `MODULARIZE`/`EXPORT_NAME` link flags onto the other's
`onRuntimeInitialized` bootstrap) is what left cogame-lantern with a permanently blank theater:

| file | source (coworld-ctf, one starter for all four) | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | verbatim except the emitted name (`chemistry_replay.js`) and the export list renamed `_chemistry_*`. **Keep the non-`MODULARIZE` link flags exactly as they are** — no `-s MODULARIZE=1`, no `EXPORT_NAME` — because the worker bootstraps with `Module.onRuntimeInitialized`. Keep `-O2 -s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--preload-file <root>/data@data` and `-d:useMalloc`. |
| the wasm entry `.nim` | `replay-viewer/ctf_replay.nim` → `replay-viewer/chemistry_replay.nim` | same structure: `stampStage`, `chemistry_load_replay`, `chemistry_frame`, `chemistry_input`, `chemistry_packet_ptr/_len`, `chemistry_error_ptr/_len`, `chemistry_stage_ptr/_len`, and the `emscripten_exit_with_live_runtime()` epilogue (without it Nim's `main` destroys every global while JS keeps calling in). `chemistry_load_replay` parses the JSON replay and hydrates the frame array; `chemistry_frame` advances/seeks and rebuilds the viewer packet. `ctf_mismatch_tick` is **dropped** — there is no re-simulation to mismatch. **The packet built by `chemistry_load_replay` is the only one carrying `meta`**; read it directly and never re-derive it via `packetAt(0)` (matrix-games, 2026-08-24). |
| `static_replay*.js` | `replay-viewer/static_replay.js` + `replay-viewer/static_replay_worker.js` | verbatim apart from the `ctf_*` → `chemistry_*` export names, the worker name string, and **one added line** in `showFailure`: `document.documentElement.setAttribute('data-replay-error', error.message || String(error))`. The worker keeps `importScripts('./wire_constants.js','./broadcast_core.js','./chemistry_replay.js')` and `Module.onRuntimeInitialized` — the matched pair for the link flags above. |
| `index.html` | `client/replay_broadcast.html`, spliced by `Dockerfile.replay-viewer`'s `sed` into `replay-viewer/dist/index.html` | the starter's page with a game block appended (below). |

`static_replay.js` already sets `data-replay-loaded="true"` on `<html>` when the worker reports
`loaded` (its line ~144); with the added failure line it sets `data-replay-error` on any failure.
Those are the two signals `tools/ci/viewer_smoke.mjs` and phase 60's `viewer-check.yml` read. If a
`coworld-replay` bridge `ready` message is posted at all, it is posted from a callback that fires
**after** `data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus,
2026-08-24). The manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` and
`tools/build_replay_viewer.sh` is the `coworld build` hook that produces the bundle.
**Never a `/client/replay` pod.**

### Chrome provenance (exact)

- `client/chrome_common.js` is copied **byte-for-byte**. Nothing in it is edited — which is why the
  wire-constants global keeps the name `window.CTF_WIRE` and why the cycle plates ride the starter's
  own `teams` / `roster` machinery rather than a new one.
- `client/broadcast_core.js` is **forked** (it is paintbot's renderer — the playbook's "treat
  `client/renderer.js` as the exact template"): the board draw becomes the tile grid, vats, vents,
  molecules, food and cogs. Its ingest/packet plumbing, letterboxing and layer pooling are untouched.
- `client/replay_broadcast.html` is **the starter's page with a game block appended**, never a
  rewrite that reuses its ids. The only edits inside the starter's own markup/script are these three,
  and no others:
  1. **Removed elements** (with their CSS blocks and the JS branches that touch them):
     `#viewpanel` and its children `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`,
     `#zoom-slider`, `#zoom-in`, `#zoom-read`; `#fpv` and its children `#fpv-canvas`, `#fpv-hud`,
     `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`;
     `#povBadge`; `#mmwarn`.
     **Zoom decision: `#viewpanel` is dropped entirely.** The 32×18 board is fixed and always fits
     the frame, so there is nothing to pan to and nothing a minimap could add; the zoom bar + minimap
     are for boards larger than the frame only.
  2. **Two re-lettered literals**: the scorebug's `Lives` label becomes `Charge`, and the momentum
     strip's label becomes `CYCLE CHARGE`.
  3. `#lockerroom` gains `pointer-events: none` so its ~1.5 s overlay stops swallowing transport
     clicks (ecos, 2026-08-23).
  Everything else — `#stage`, `#board`, `#chrome`, `#scorebug`, `#plates-l`, `#plates-r`, `#clock`,
  `#clock-time`, `#clock-caption`, `#bannerlane`, `#killfeed`, `#transport` and all seven transport
  buttons plus `#btn-spoilers`, `#scrub`, `#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`,
  `#scrub-head`, `#endcard`, `#status` — is the starter's, unchanged.
- **The appended game block** owns: the three cycle plates' gauge bars and status words, the roster
  strip, the shame panel, the feed row builders, the beat-marker CSS, and the plate colours
  (`.plate.amber{--tc:#d9a02b}`, `.beryl{--tc:#3ea08a}`, `.cobalt{--tc:#4a7ad6}` — unknown team keys
  fall back to the starter's `AMBER` constant in `buildFlag`, so nothing breaks if a rule is missed).
  Its beat builder is named **`buildChemBeats`**, never `markBeat`: a game-block `function markBeat`
  is hoisted over the chrome alias block's `var markBeat = C.markBeat` and silently kills every
  scrubber beat (tandem, 2026-08-23). A scope-duplication test over the alias list enforces it.

### Transport rules

`relayout()` sets `--band` and `--hudscale` on `:root` (and `--topband` for the scorebug strip);
every chrome measure derives from `--u = 1px * var(--hudscale)`. **No overlay sits in the transport
band**: the shame panel, the roster strip, the feed and the banner lane are all clipped to the board
region between `var(--topband)` and `var(--band)`. The **endcard stops at `var(--band)`** (it is
`inset: var(--topband) 0 var(--band) 0`, the starter's own rule) and is dismissed by **every** seek.
Scrubber beats are clickable, labelled buttons — one per emitted kind, with CSS for **every** kind
the game emits: `shift`, `cold`, `restart`, `famine`, `gameover`. The whole beat timeline ships on
the first HUD frame (paintbot's `beats` field), so the scrubber is complete before playback starts
and `?spoilers=0` still holds beats back until the playhead reaches them.

### What it draws

- **Board.** A tiled lab floor with the wall ring and the two pillars; three **vats** (3×3, tinted
  amber / teal / blue) whose glass glows brighter with charge and goes grey at charge 0; three
  feedstock **vents** (pipes with a coloured collar) and, in distractor variants, two glittering
  vents; loose molecules as 20 px sprites on their cells; FOOD as a warm bun sprite that pulses in
  its last 48 ticks of life; eight cogs as 36 px bodies in their slot colour with the alias under the
  feet, and **the carried molecule drawn as a sprite over the head** (the idea's requirement).
  A reaction flashes the vat and throws the new tokens outward along the ring; a `misdrop` puffs a
  grey cloud over the vat and pushes a feed row.
- **Scorebug** (`#scorebug` / `#plates-l` / `#plates-r`, paintbot's plate machinery, which is already
  2–4 plate ready): one plate **per cycle**, keyed `amber` / `beryl` / `cobalt` (two plates in the
  two-cycle variants). Headline = the cycle name (fed through `teams[k].policies = ["Amber"]`, the
  starter's own headline path); the big number = **charge** (`lives-<k>`, label re-lettered
  `Charge`); the appended gauge bar = `charge / chargeMax`; the status word underneath is
  **`RUNNING`** (reacted within the last 48 ticks), **`STARVING`** (charge ≥ 1 but a stock is 0 or no
  reaction for 48 ticks), or **`COLD`** (charge 0, drawn in grey with the cold-start cost `NEEDS 3+3`
  beneath). That is the idea's per-cycle gauge, literally.
- **Roster strip** (appended, under the scorebug): eight chips in score order —
  `DRAM · chemistry-metabolist · 14` — each tinted with the seat's body colour, with a molecule pip
  when the cog is carrying. The **policy name** appears here and only here (plus `results.names`);
  the board and every prompt show the alias.
- **Clock** (`#clock-time`, `#clock-caption`): `SHIFT 4 / 12`, caption `tick 214 of 720`. Spelled
  out, never `S4`.
- **Feed** (`#killfeed`, the starter's `pushFeed(row)` — one argument, the row element; the signature
  is the starter's and is not changed, which is what broke cogball 0.1.4): one row per `order` event
  (`ARGON → resin to AMBER  "I hold spark to Amber"`, tagged `auto` when `source` is `fallback` or
  `scripted`), plus rows for `misdrop` (`GILT dropped glitter in BERYL — lost`), `restart`
  (`COBALT RESTARTED — 3 resin + 3 brine`), `cold` (`COBALT WENT COLD`) and `famine`.
- **Shame panel** (appended, right, above the feed): `HOARDING` — every seat with `hoard > 0`, in
  descending order, `GILT 9 shiny`. Hidden entirely when `distractorPeriod == 0`; capped at the top
  three rows under 640 px.
- **Cycle-charge strip** (`#momentum`, the SVG under the scrub track, label `CYCLE CHARGE`): one
  stepped line per cycle from `series.charge`, each normalised by `chargeMax`, on the same tick axis
  as the playhead. Fed exactly like paintbot's lives series —
  `state.lead = {"teams":["amber","beryl","cobalt"], "pts":[[t,a,b,c], …]}` — so
  `ingestLeadSeries` / `renderMomentum` in `client/chrome_common.js` need **no change**.
- **Endcard**: the ending in words (`SHIFT LIMIT` / `FAMINE` / `TIME`), the winner's alias and
  policy, the eight scores and the line `94 food made · 6 rotted · 1 cold start`.

**Legibility at 360 px is a requirement** — the featured-match iframe is ~360 px wide. `#stage.tiny`
(already switched on at `boardW <= 620`) shrinks the feed and pips; carry bullwhip's
`.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and hide chip labels under 640 px so the roster
chips degrade to `DRAM 14`. Check at 360 px: three gauges readable with their status words, the
`SHIFT 4 / 12` clock, the top three roster chips and the shame panel's first row.

**Real art, not placeholders.** `scripts/art/gen_chemistry_art.py` (Pillow, committed,
deterministic) renders and commits into `data/`: the floor and wall tiles, the three vat states
(cold / warm / bright) per cycle tint, the five vent sprites, the five molecule sprites (three
feedstocks readable by *shape*, not only colour; two distractors deliberately shiny), the food token,
eight cog bodies (`cog_<colour>_front.png` and `_carry.png`), the reaction flash, and the loading
screens the `#lockerroom` markup expects (`client/art/lockerroom/bg.jpg` = a lit lab, plus eight
portraits replacing the soldier `.webp`s). `Dockerfile.replay-viewer`'s copy list and its `test -f`
assertions are updated to those file names; the `league.html` sed step and
`client/league_replayer.html` are dropped with it.

---

## Packaging

**`compose.yaml`** — one service, one image (game + player binaries):

```yaml
services:
  chemistry:
    image: coworld-chemistry:latest
    platform: linux/amd64
    build: {context: ., dockerfile: Dockerfile, network: host}
```

The service name is the single source of the manifest placeholder: `services.chemistry` →
**`{{CHEMISTRY_IMAGE}}`** (lantern, 2026-08-23 — `coworld build` hard-fails anything else;
`tests/test_manifest.nim` asserts the derivation).

**`coworld_manifest_template.json`** — bullwhip's shape with the 0.1.42 strictness hive found:
top-level `$schema`, ≥ 3 `tags` (`chemistry`, `public-goods`, `grid`, `llm-driven`, `melting-pot`,
`eight-player`), top-level `episode_timeout_minutes: 20`, top-level `player[]`,
`variants[].description` on every variant, and a real JSON-Schema `game.config_schema` with
`required: ["tokens"]` and `minItems`/`maxItems` on **every** array property (tandem, 2026-08-23).

- `game.name`: `chemistry`; `game.replay_viewer.bundle`: `static-replay-viewer`.
- `game.runnable`: `{"type":"game","image":"{{CHEMISTRY_IMAGE}}","run":["/bin/chemistry"],
  "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/chemistry/anthropic_api_key"},
  "source_url":"https://github.com/Metta-AI/cogame-chemistry/tree/main"}` — the `env` entry is
  mandatory: without it the hosted game container never sees the coworld secret and every league
  episode silently plays scripted (hive, 2026-08-23), which surfaces only at phase 60 check 4.
- `game.config_schema` properties: `tokens` (string array, `minItems 1`, `maxItems 8`, required),
  `players` (array of `{name}`, `minItems 1`, `maxItems 8`), **`num_agents` (integer, 1..8, default
  8)**, `seed`, `cycles` (enum 2 or 3, default 3), `shifts` (1..24, default 12), `ticksPerShift`
  (10..120, default 60), `moveCooldown` (1..8, default 2), `carryCap` (1..2, default 1), `ventPeriod`
  (1..48, default 8), `ventGroundCap` (1..24, default 6), `distractorPeriod` (0..64, default 0; 0 =
  no distractor vents), `distractorGroundCap` (0..64, default 12), `chargeMax` (1..24, default 12),
  `charge0` (0..24, default 3), `chargeDecayPeriod` (1..240, default 60), `reactionCooldown` (0..48,
  default 6), `coldStartCost` (1..8, default 3), `foodLifetime` (24..960, default 240),
  `llmTimeoutSeconds` (5..60, default 20), `minTurnSeconds` (0..60, default 18), `maxOutputTokens`
  (200..2000, default 700), `model` (string), `episodeTimeoutSeconds` (default 1200),
  `playerConnectTimeoutSeconds` (default 180), `shutdownGraceSeconds` (default 20),
  `showPlayerLabels` (bool, default true). `additionalProperties: false`.
- `game.results_schema`: the `results.json` object above (slot arrays `minItems 1`, `maxItems 8`;
  `reactions` `maxItems 3`).
- `game.docs` (**text**, not uri — bullwhip's shape):
  `{"readme":{"type":"text","value":"<what it is: eight cogs, three autocatalytic vats, five
  molecules, two of them useless; your score is what you eat>"},
    "pages":[{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<the reaction graph,
      the nine-step tick order, charge/decay/cold-start, scoring, end conditions>"}},
             {"id":"policies.md","title":"Fielding a policy","content":{"type":"text","value":"<the
      standing-order schema, the caps, PLAYER_PROMPT / PLAYER_SCRIPTED how-to>"}}]}`.
- `game.protocols` — **both**, as `{"type":"text","value":…}` objects (the platform validator rejects
  bare strings): `player` (the `chemistry.player.v1` frames, the reply schema and its caps) and
  `global` (the `/global` sprite + chrome frame, and the static bundle's `index.html?replay=<url>`).
- `player[]` — three entries, all on `{{CHEMISTRY_IMAGE}}` with `run: ["/bin/chemistry-player"]`:
  `chemistry-player` (no env — a prompt policy; `PLAYER_PROMPT` is supplied at upload time),
  `chemistry-courier` (`env: {"PLAYER_SCRIPTED":"courier"}`),
  `chemistry-freeloader` (`env: {"PLAYER_SCRIPTED":"freeloader"}`).
- **`variants[]` — four, mapping the idea's four configs one-for-one; `num_agents: 8` in every one**,
  and `players` is the eight aliases in slot order in every one:

  | id | name | `cycles` | `distractorPeriod` | `distractorGroundCap` | `num_agents` |
  |---|---|---|---|---|---|
  | `two-cycles` | Two metabolic cycles | 2 (`amber`, `beryl`) | 0 | 0 | **8** |
  | `two-cycles-distractors` | Two cycles with distractors | 2 | 6 | 12 | **8** |
  | `three-cycles` | Three metabolic cycles | 3 | 0 | 0 | **8** |
  | `three-cycles-plentiful-distractors` | Three cycles, plentiful distractors | 3 | 2 | 24 | **8** |

  All four share `shifts: 12, ticksPerShift: 60` and the constants above. The mapping decision: the
  source substrate list names `with_distractors` and `with_plentiful_distractors`; rather than ship
  six variants, the two-cycle room takes the ordinary distractor load and the three-cycle room takes
  the plentiful one, so all of the idea's settings are represented in exactly the four configs it
  asks for. **The league default variant is `three-cycles-plentiful-distractors`** — it is the config
  where reading the reaction graph beats grabbing the nearest shiny object, i.e. where an LLM
  champion visibly outplays a filler; phase 50 passes it as `default_variant_id` at seed time
  (gridlock, 2026-08-23: the variant is chosen at seed time or not cheaply again).
- `certification`:
  `game_config` = `{num_agents: 8, seed: 7, cycles: 3, shifts: 6, ticksPerShift: 60,
  distractorPeriod: 6, distractorGroundCap: 12, minTurnSeconds: 0,
  playerConnectTimeoutSeconds: 180, players: [ …the eight aliases… ]}` and
  `players` = 2 × `chemistry-player`, 4 × `chemistry-courier`, 2 × `chemistry-freeloader` — **every
  declared player entry seated at least once**, because `players-run` seats the whole roster and a
  `baseline × N` fixture fails `players_missing` (raid, 2026-08-23). Offline the `chemistry-player`
  seats fall back to `courier`, so the fixture is deterministic. **6 × 60 = 360 ticks = 15 s of
  video**, which outlasts the 10 s viewer soak (ecos, 2026-08-23), and with `minTurnSeconds: 0` and
  no credentials it runs in a couple of seconds — well inside `coworld certify`'s 60 s default
  (`grace + rounds × pacing + linger < 50 s`, commons-family, 2026-08-24).

**Other packaging files:** `Dockerfile` (paintbot's two-stage nimby build; produces `/bin/chemistry`
and `/bin/chemistry-player`), `Dockerfile.replay-viewer` (paintbot's, with the chemistry file list
and the same `test -f` assertions, minus `league.html`), `tools/build_replay_viewer.sh` (paintbot's,
image tag renamed, `mkdir -p` fix), `.github/workflows/ci.yml` and `coworld-release.yml` from
`coworld-builder/templates/`, `tools/ci/docker_smoke.sh` with `<SEATS>` substituted to **8**,
`tools/ci/viewer_smoke.mjs` copied verbatim, `tools/ci/renderer_fixture.html`, and
`tools/ci/policies.json` naming `chemistry-foreman` and `chemistry-metabolist` (both `PLAYER_PROMPT`,
each with `env: {"USE_BEDROCK":"true"}` — without it the platform gives the player pod no Bedrock
sidecar and the seat silently plays scripted, cogolf 2026-08-24) plus the fillers
`chemistry-courier` and `chemistry-freeloader`.

---

## Tests

All run in `ci.yml`; the sandbox cannot run any of them locally.

1. **`tests/test_sim.nim` — sim units.** Reaction preconditions (charge 0 / cooldown / a zero stock
   each block it); `foodYield == 1 + charge div 3` across charge 0..12 with the post-increment charge;
   cold start consumes exactly 3+3 and yields no food; decay at `tick mod 60 == 0` and the `cold`
   event at the 0 crossing; misdrop destroys the molecule and increments the right seat; spill-ring
   ordering (nearest-to-deliverer, ties by `(row,col)`) and the `spoil` path when the ring is full;
   food rot at exactly 240 ticks; vent emission order N,E,S,W and the ground-cap gate; `carryCap 1`;
   move cooldown; two cogs cannot share a cell and the lower slot wins; BFS determinism (the same
   state yields the same path twice); **determinism** — the same seed and the same order script
   produce an identical `gameHash` after 720 ticks, twice in one process and across a fresh server.
2. **`tests/test_baseline.nim` — bounded orders / legality.** For 12 seeds × 720 ticks on all four
   variants, with all-`courier` and with all-`freeloader`: every emitted order's `job`, `molecule` and
   `reactor` is inside the enum **and legal for that variant**; every per-tick action is one of the
   seven vocabulary values; no cog is ever outside the room, inside a wall or sharing a cell; no cog
   carries more than one molecule; no stock, charge or score goes negative; charge never exceeds
   `chargeMax`; neither baseline raises, and neither takes more than 1 ms per shift.
3. **`tests/test_feasibility.nim` — the oracle, as a CI precondition.** Gates (a)–(d) of
   `## The game`, over seeds 1..12 on all four variants, including the test-only `nearest` kernel for
   gate (d). Any constant change that breaks the economy fails here rather than in a dead replay.
4. **`tests/test_replay.nim` — end-to-end + strict UTF-8.** Plays a full scripted episode headless,
   writes `results.json` and the replay, then re-reads the replay **bytes**: `validateUtf8 == -1`
   (strict), parses as JSON, `protocol == "chemistry.replay.v1"`, `frames.len == ticksPlayed`,
   `series.charge.len == ticksPlayed`, every event tick in `0..ticksPlayed`, at least one `take`,
   `drop`, `react` and `eat`, exactly `shifts` `shift` events and exactly one `end`,
   `results.scores.len == 8`, `results.reason` in `{complete, deadline, forfeit}`, `results.ending` in
   `{shift_limit, famine, deadline, forfeit}`, file size `< 8 MiB`. A seat is fed a `say`/`notes` of
   multi-byte runes exactly at the 80/320 caps and the recorded strings are asserted valid UTF-8 and
   ≤ the cap (the bullwhip byte-truncation bug).
5. **`tests/test_llm.nim` — decision layer.** `extractJsonObject` on fenced and prose-prefixed
   replies; unknown `job` → invalid; `supply` without `reactor` → invalid; an absent reactor →
   clamped with `clamped: true`; a feedstock the reactor does not take → **accepted** (the misdrop
   must stay expressible); a stubbed transport that times out, 429s, 403s or returns junk produces
   `courier` orders for those seats, never raises, and marks `source: "fallback"`; **one batch carries
   all open seats** (assert `RequestBatch.len == openSeats`, i.e. 8 on shift 1).
6. **`tests/test_manifest.nim` — packaging.** `num_agents == 8` in **all four** variants and in
   `certification.game_config`; the image placeholder equals the one derived from `compose.yaml`'s
   service name (`{{CHEMISTRY_IMAGE}}`); `replay_viewer.bundle == "static-replay-viewer"`;
   `game.docs.readme` + non-empty `pages`; `game.protocols.player` **and** `global` present and both
   `{"type":"text",…}` objects; `ANTHROPIC_API_KEY_URI` in `game.runnable.env`; every `player[]` id
   appears at least once in `certification.players`; `episode_timeout_minutes` top-level; every array
   property in `config_schema` carries `minItems` and `maxItems`.
7. **`tests/test_broadcast.nim` — chrome frame.** `teams` keys are exactly the present cycles
   (`amber`,`beryl`[,`cobalt`]) and each carries `policies: [<cycle name>]`, `lives` = charge and the
   status word; `roster[]` has 8 entries carrying alias in `name` and the **policy** name in `pol`;
   `lead.teams` / `lead.pts` shape matches `chrome_common.js`'s expectation (`[t, a, b, c]` rows);
   `beats` carries only the five declared kinds; `over` is present on the terminal frame with the
   ending string; every feed row's text is ≤ the caps; and a **scope-duplication test** asserts no
   game-block function name collides with the chrome alias list (`markBeat` et al., tandem).
8. **`docker-smoke` (`tools/ci/docker_smoke.sh`, `<SEATS>` = 8).** Builds the image, runs a real
   8-seat episode in containers off the cert fixture, asserts the **player** containers each exit 0
   (raid, 2026-08-23) as well as the game, validates `results.json` against the results schema, and
   copies the replay to `SMOKE_REPLAY_OUT` (`dist/smoke/replay.json`), uploaded as the `smoke-replay`
   artifact.
9. **`wasm-viewer` job — the bundle is EXECUTED, not merely built.** `needs: docker-smoke`, downloads
   `smoke-replay`, builds the bundle via `tools/build_replay_viewer.sh`, installs Playwright pinned
   **1.55.0**, and runs **`tools/ci/viewer_smoke.mjs`** against that replay over local HTTP with
   `--strict-text-bounds` (fixed arena → `canvas_text.never_inside` must be 0) and `--soak` (the
   15 s cert replay outlasts the 10 s window). Pass requires `data-replay-loaded="true"` **and** three
   different clock readouts at 0 %, 50 % and 100 %; `data-replay-error` or silence fails the job.
   Evidence (`viewer-smoke.png`, `viewer-smoke.json`) uploads on success and failure. A second step in
   the same job runs `viewer_smoke.mjs --strict-text-bounds` against
   **`tools/ci/renderer_fixture.html`** — the worst-case renderer fixture that loads the real renderer
   with a full-cap 80-char `say` and 320-char `notes` on **every** seat at several canvas sizes,
   because `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY` and therefore produces a replay with
   zero LLM text (cogchemists, 2026-08-24).

---

## Out of scope (v1)

- **Per-tick policy sockets.** A seat submits one standing order per shift; the kernel emits the
  per-tick grid actions. A direct per-tick action channel for RL/vector policies is not shipped.
- **More molecules, deeper chains, tools.** Five species, three reactions, one product. No
  intermediate molecules that feed other reactions, no reaction discovery, no recipes to learn at
  runtime — the graph is given as text, and reading it correctly is the skill.
- **Sludge, jams, cleaning and repair jobs.** A misdrop destroys the molecule and nothing else.
- **Carrying or hoarding food.** Food is eaten by standing on it; it cannot be picked up, stored,
  traded or given away.
- **Combat, theft, blocking, doors.** Cogs cannot take a molecule from another cog's hand, cannot
  damage each other, and only interact through the floor, the vats and `say`.
- **Fog of war / partial observation.** The whole room is visible to every seat; paintbot's FOV,
  first-person PiP and POV lens are deleted, not repurposed.
- **A fifth and sixth variant.** Four configs, exactly as the idea pins, and no variant changes
  `num_agents` — Chemistry is an eight-seat game.
- **Cross-episode persistence.** Every episode starts from the seeded opening state; nothing carries
  over except the league rating.
- **Re-simulating playback.** The viewer decodes recorded state; there is no replay-hash mismatch
  mode, no `--mismatch-quit`, and no `#mmwarn`.
- **Achievements, perks, handicaps, map generation, the map editor and the league replayer page** —
  all inherited paintbot machinery, all deleted rather than carried dark.
