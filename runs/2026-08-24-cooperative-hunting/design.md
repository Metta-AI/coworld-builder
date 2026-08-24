# Cooperative Hunting — design note (2026-08-24)

Repo: `Metta-AI/cogame-cooperative-hunting` (public). Coworld/game name `cooperative_hunting`,
slug `cooperative-hunting`, page `https://softmax.com/cooperative-hunting`.

**Starter: `Metta-AI/coworld-staghunt`** (cloned read-only to `/tmp/coworld-staghunt` and read in
full: `src/staghunt.nim` 2544 lines, all eight `players/*.nim`, `coworld_manifest.json`,
`Dockerfile`, `nimby.lock`, `staghunt.nimble`, `tools/`). It is the starter because the idea
pins it and because the game shape is identical: a real-time BitWorld grid loop whose rules
already exist as the code we are extending — variants are knobs on its capture predicate, not a
new game. **Every convention there holds here unless this note says otherwise.** Where staghunt
is silent — it has no replay viewer, no `compose.yaml`, no `.github/workflows`, no
`coworld_manifest_template.json`, and a pod-served binary replay — this note names
`Metta-AI/coworld-ctf` (paintbot, mounted at `/workspace/starters/coworld-ctf`, staghunt's
lineage parent for BitWorld sprite_v1 games) as the **single** starter for all four viewer files,
and coworld-builder `templates/` for CI.

---

**Source idea (verbatim):**

```
EXTENSION of Metta-AI/coworld-staghunt — an incomplete BitWorld coworld where rabbits go down alone but stags, moose and elephants need coordinated multi-player encirclement; it already has eight scripted hunter players (rabbiteer, stag_hunter, moose_hunter, elephant_hunter, sidekick, modeler…). Every assurance / coordination-with-a-capability-sum game below is the same mechanic with different numbers, so they become variants, not repos. First job: certify staghunt itself.

Variants to add:
    MP Coop Mining: iron = solo +1; gold = exactly two hunters within a 3-tick window, +8 each; the flash-and-revert timing rule is the only new code.
    LBF Level-Based Foraging: agents and food carry levels; a pickup succeeds when adjacent loaders' levels sum ≥ food level; reward split. Generalises the encirclement rule into a single knob; include the paper's H1-H4 heuristics as fillers.
    MP Boat Race: eight races with a 75-tick partner-choice phase then a 225-tick paddle/flail race — the reputation + partner-selection variant.
    MP Predator-Prey (alley_hunt / open / orchard / random_forest): seats split into hunters and prey that must forage to score; tall grass hides prey. Adds the asymmetric role to the same world.

Seats: 2-8
Motive: assurance / coordination, mixed-motive in LBF, asymmetric in predator-prey
Policy interface: staghunt's existing per-tick BitWorld protocol
Integrity (anti-collusion): cooperative cross-play scoring with the bundled scripted hunters as background bots; spawns seeded.
Replay plan: staghunt viewer + countdown rings (coop mining), levels over heads (LBF), race bracket (boat race), grass opacity toggle (predator-prey).

Absorbed cards: MP Stag Hunt in the Matrix (the matrix version now lives in MP Matrix Games), MP Coop Mining, LBF, MP Boat Race, MP Predator Prey.
Source: Melting Pot coop_mining, boat_race__eight_races, predator_prey__*; github.com/semitable/lb-foraging; github.com/Metta-AI/coworld-staghunt.
```

---

## The game

Six hunters share a 32×32 tile forest (12 px tiles, 384×384 px world — staghunt's
`WorldWidthTiles`/`StagTileSize` unchanged). Animals wander. A hunter takes an animal by
standing on the right **cardinal sides of it at the same moment as enough allies**: a rabbit
falls to one hunter, a boar to two on perpendicular sides, a stag to two on opposite sides, a
moose to any three, an elephant to all four. Everyone who was on a side when it fell gets the
full score — so the whole game is the assurance problem: rabbits are a guaranteed +1, an
elephant is +18 each but only if four hunters commit to the same animal on the same tick, and
a half-formed ring just gets trampled (−30 energy) or gutted (−10 energy and shoved).

### Seats

**`num_agents` = 6, in every manifest variant and in the certification fixture. One number, no
range.** Reasoning: 4 is the largest coalition the world requires (elephant), and 6 leaves two
hunters free to defect to rabbits — without spare seats the assurance tension disappears and
every episode is a forced full-party hunt. 6 is even (the predator-prey split is 3v3) and 6
seats × one LLM request per 15 s planning turn = 24 requests/min, under the Bedrock sidecar's
30 req/min-per-episode cap.

### Time base and the four variants

The sim runs at **`tickHz = 8`** ticks of wall clock per second during an episode (staghunt's
`TargetFps = 24` becomes a config value; all balance constants stay in **ticks**, so nothing about
the game changes — only how fast it plays out). A round ends with a **40-tick (5 s) round card**
during which the world freezes and the per-seat overlay is forced on (staghunt's
`RoundEndDisplayTicks`, rescaled from 240).

| variant id | rounds × ticks | play ticks | capture rule | what is different |
|---|---|---|---|---|
| `staghunt` | 3 × 960 | 2880 | `sides` | the base world, unchanged |
| `coop-mining` | 3 × 960 | 2880 | `window` (3 ticks) | animals replaced by immobile ore; a side stays "occupied" for 3 ticks |
| `lbf` | 3 × 960 | 2880 | `levelsum` | hunters and food carry levels 1–4 / 1–6; adjacent levels must sum ≥ food level; reward is split |
| `predator-prey` | 4 × 720 | 2880 | `sides` for tagging | 3 seats hunt, 3 seats forage; roles alternate per round; tall grass hides foragers |

All four are the same sim with a different `captureRule` enum value plus a small amount of
per-variant furniture. Boat race is **not** — see `## Out of scope (v1)`.

### Rules, complete

**World.** 32×32 tiles. Border ring is rock. Interior: 11 % of tiles are obstacles, half tree
half rock (`ObstacleDensityPerMille = 110`, unchanged). A 7×7 block at the centre and six
random 3×3 blocks are cleared. The map is generated once per episode from `seed`; rounds re-roll
prey with `seed + roundIndex` but keep the same map (staghunt's `resetRound`, unchanged).

**Hunters.** Start at a free tile within 4 tiles of the centre, `energy = 120`, `score = 0`,
facing down. Energy cap 200; passive recharge +1 every 18 ticks but only up to 100. Moving costs
2 energy and sets a 5-tick move cooldown. A hunter with < 2 energy cannot move (it can still
recharge). No elimination and no negative score.

**Animals.** Populations are maintained per kind, and a kind is only spawned when the connected
seat count is at least its coalition size (`preyMinPlayers`): rabbits 12, boars 6, stags 6, moose
3, elephants 2. `RespawnIntervalTicks = 60` between spawns, dropping to 3 while the population is
4 or more below target. Think cadences: rabbit 10, boar 14, stag 16, moose 20; elephant 12–24
with a 30 % chance per think to charge 2–4 tiles in a straight line. Flee radius 3 (Chebyshev);
flee probability by distance 75/50/25 scaled per kind ×1.00 rabbit, ×0.80 boar, ×0.70 stag,
×0.20/0.60/0.40 moose, ×0.25 elephant. A moose cardinal-adjacent to a hunter gores it 30 % of the
time (5 % diagonally): −10 energy and a one-tile shove. An elephant that steps onto a hunter
tramples it: −30 energy, the elephant slides two tiles through over 4 ticks, and if the far tile
is blocked it stays put — which is exactly why a complete four-side ring can hold one. All of this
is staghunt's, verbatim, and is not to be retuned in v1.

**Rewards.** Rabbit 1 score / 15 energy, boar 3/90, stag 5/60, moose 10/140, elephant 18/220 —
each awarded **in full to every participant** (except in `lbf`, below). A capture leaves a corpse
sprite for 48 ticks and puts a 20-tick yellow kill glow on the killers.

**`coop-mining` furniture.** No animals. 18 iron nodes and 8 gold nodes, immobile, respawning on
the same 60-tick cadence at random free tiles. Iron: 1 adjacent hunter on any side → +1 score /
+10 energy. Gold: **two different hunters on any two sides within a 3-tick window** → +8 score /
+40 energy each. The window is the only new mechanic: the sim keeps
`sideSeen[preyIndex][side] = (tick, slot)` and a side counts as occupied when
`tick - sideSeen.tick <= windowTicks - 1`. `windowTicks = 1` reproduces base staghunt exactly, so
the base game runs through the same code path.

**`lbf` furniture.** Each seat gets `level = 1 + (slot mod 4)` (so 1,2,3,4,1,2 for slots 0–5),
drawn as a digit sprite over the hunter's head. Food items carry `level ∈ 1..6`, drawn the same
way, with 14 items maintained. A pickup succeeds when the **sum of the levels of the hunters
cardinally adjacent to the food** is ≥ the food's level. Reward: `score = 2 × level`,
`energy = 20 × level`, **split**: each participant gets `floor(score / n)`, and the integer
remainder goes to the participant with the lowest slot (deterministic, stated so two
implementations cannot differ). Energy is not split — each participant gets it in full, because
energy is a resource, not the ranked quantity.

**`predator-prey` furniture.** No animals. Seats split by role each round:
`role = hunter if (slot + roundIndex) mod 2 == 0 else forager` — with 6 seats and 4 rounds every
seat hunts exactly twice and forages exactly twice, so the asymmetry cancels in the ranking. 40
berry tiles and 120 tall-grass tiles are placed from the seed. A **forager** standing on a berry
tile consumes it at end of tick: +1 score, +12 energy, and the tile regrows after 90 ticks. A
**hunter** pair tags a forager when two hunters occupy opposite cardinal sides of it (the stag
predicate applied to a player): +6 score to each hunter, the forager loses 30 energy and no score,
and respawns 24 ticks later at a free tile within 4 of the map edge. **Tall grass hides
foragers:** a forager standing on a tall-grass tile is not drawn in a hunter's per-seat frame
unless the hunter is within Chebyshev distance 2. It is always drawn in the global/replay stream —
the viewer gets a grass-opacity toggle instead (idea's replay plan), so the spectator sees the
ambush the hunter could not.

### Turn/tick structure — exact resolution order

Every tick, in this order. Ties resolve by ascending slot, then ascending prey index; nothing in
this list is order-independent, so this list is the specification.

1. **Ingest input.** For each seat take the most recent 2-byte input mask received since the last
   tick (last write wins). A seat that sent nothing keeps its previous mask. A disconnected seat
   contributes mask 0.
2. **Plan distribution** (prompt seats only, and only on a planning boundary — see
   `## Decisions`): deliver any plan that arrived from the LLM batch as a `0x91` message and log a
   `plan` event.
3. **Hunter phase**, ascending slot: toggle the overlay on a `select` rising edge; increment the
   recharge counter and grant +1 energy at 18 if energy < 100; decrement `killGlow`,
   `trampleGlow`, `pushStep`; if `moveCooldown > 0`, decrement it and stop here. Otherwise read
   one direction bit with priority up > down > left > right, set facing, and — if energy ≥ 2 and
   the destination is in bounds, not tree/rock, and holds no hunter and no animal — move there,
   pay 2 energy, set `moveCooldown = 5`.
4. **Animal phase**, ascending prey index: run the trample/gut animation counters first (they
   freeze logical position); then `thinkCooldown`; then the kind's think (elephant stride/step/
   trample; others gore/flee/wander) exactly as in staghunt's `thinkPrey`.
5. **Side bookkeeping:** for every animal/node, stamp `sideSeen[side] = (tick, slot)` for each of
   the four cardinal tiles currently occupied by a hunter.
6. **Capture resolution**, ascending prey index: a side counts as occupied when
   `tick - sideSeen[side].tick <= windowTicks - 1`; evaluate the variant predicate
   (`sides` | `window` | `levelsum`) over the occupied sides; on success credit every distinct
   `sideSeen[side].slot`, award score and energy per the formula above, set `killGlow = 20`, push a
   corpse, log a `catch` event, and remove the animal.
7. **`predator-prey` only:** tag resolution (opposite-side hunter pair over a forager), then
   forage resolution (forager standing on a ripe berry tile).
8. **Housekeeping:** age corpses; tick berry/ore regrowth; cull animals whose coalition size now
   exceeds the connected seat count; run the population maintainer.
9. **Emit:** build the global sprite_v1 frame (including the chrome label on sprite 4090), append
   the tick record to the in-memory replay, send each seat its per-seat frame.
10. **Round/episode bookkeeping:** if `tick == ticksPerRound`, freeze scores into the round table,
    log `round_end`, force overlays on, and enter the 40-tick round card; at the end of the card
    either `resetRound` and log `round_start`, or finish the episode.
11. **Deadline guard:** if `monotonic_now - episodeStart >= playBudgetSeconds`, settle immediately
    (see end conditions).

### Scoring, sign, and what the league ranks by

```
roundScore[slot]  = Σ over captures in the round in which slot participated of
                      (variant == "lbf" ? floor(rewardScore(item) / |participants|)
                                          + (slot == min(participants) ? rewardScore(item) mod |participants| : 0)
                                        : rewardScore(item))
results.scores[slot] = Σ over rounds of roundScore[slot]        // integer, ≥ 0
```

**Sign: higher is better, and no term is ever negative.** Trample and gore cost energy, never
score. The league ranks by `results.scores[slot]` (the platform's Elo is computed from these
per-episode scores; 1000 start, K=32). Ties are ties — the game breaks nothing.

### End conditions and legal `results.reason` values

Exactly three values are legal, and the game emits nothing else:

- **`complete`** — all `rounds` rounds ran to `ticksPerRound` and their round cards finished. The
  normal path.
- **`deadline`** — the wall-clock guard in step 11 fired (`playBudgetSeconds`, default 660 s).
  The current round is scored as it stands at that tick, the remaining rounds are not played, a
  `deadline` event is written, and the episode settles and exits **0**. Scores are real, not
  zeroed, so a deadline episode is still rankable. This is the degrade-never-hang backstop; with
  the numbers in `## Packaging` it should never fire.
- **`no_players`** — zero seats connected within `player_connect_timeout_seconds` (default 120 s).
  `results.json` is written with all-zero scores and the process exits **0** (never hangs, never
  non-zero). If ≥ 1 seat connects the episode runs with the seats it has; absent seats score 0 and
  are flagged `disconnected: true` in the replay and results.

The game **never** exits non-zero on a player-side problem, and never waits on a player socket
without a bound.

### Per-seat observation: what is visible, what is hidden

A seat's window on the world is exactly staghunt's per-player sprite_v1 frame: a 128×128 px
viewport (`ScreenWidth`/`ScreenHeight`) centred on the hunter and clamped to the world — **about
10×10 tiles of a 32×32 world**. Per frame a seat receives:

*Visible:* the terrain (grass/tree/rock) inside the viewport; every animal, ore node, berry tile,
corpse and **other hunter** whose sprite intersects the viewport; the capture-readiness indicator
dots on the sides that would complete a capture; level digits over heads and over food in `lbf`;
its **own** score and energy as HUD digit sprites at (1,1) and (1,7); and a `0x07` identity packet
naming its own object id. Prompt seats additionally receive the plan text the game produced for
them (`0x91`), which is a rendering of their own observation, not privileged information.

*Hidden:* everything outside the viewport (22 of the 32 tiles in each axis); other hunters'
energy, score, level intent and policy identity — a rival hunter is a coloured sprite and nothing
more; all animal internals (think cooldowns, flee rolls, stride state); the seed; the map beyond
what has been seen; other seats' prompts, plans and `note` memories; and, in `predator-prey`,
foragers standing in tall grass more than 2 tiles away. Real policy names are **never** visible
in-game (see two name spaces, below).

The LLM observation is composed **from exactly this visibility set** — the game computes it with
the same predicate it uses to build that seat's frame, so a prompt seat cannot see further than a
scripted seat.

---

## Decisions: LLM with scripted fallback

### Reconciling "both champions are `PLAYER_PROMPT`" with a per-tick BitWorld engine

The pin (SPEC §Design pins, playbook §Phase 2) is that both champions are LLM **prompt** policies
env-switched against a scripted baseline in the same image. staghunt's policy interface is a
per-tick websocket that carries 2 bytes of button state at 8–24 Hz; no LLM can answer at that
rate, and the eight bundled bots are compiled Nim, not prompts. Both facts are real; here is how
they are made to hold together, and this is a decision, not an option.

**The champion policy type is an LLM prompt policy (`PLAYER_PROMPT`), decided at a slower cadence
and executed per tick.** Concretely, the bullwhip/babel split is adopted wholesale: the **game
container owns the LLM calls** (`src/cooperative_hunting/llm.nim` is a port of
`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim` — same transport ladder: Bedrock
sidecar via `AWS_ENDPOINT_URL_BEDROCK_RUNTIME` + `AWS_BEARER_TOKEN_BEDROCK`, else
`ANTHROPIC_API_KEY`, else `ANTHROPIC_API_KEY_URI`, else disabled; same haiku-first model list;
same `curly.makeRequests` parallel batch), and the **player container is the policy**: it either
registers a prompt with the game and executes the plans it gets back, or it runs one of the eight
scripted bots locally. So:

- a champion seat is a `PLAYER_PROMPT` policy whose prompt genuinely decides *what animal to
  commit to, from which side, and with whom* every 15 s;
- a scripted seat is a `PLAYER_SCRIPTED=<name>` policy that never touches the LLM;
- both are the **same image**, `{{COOPERATIVE_HUNTING_IMAGE}}`, same entrypoint
  `/bin/cooperative-hunting-player`, switched only by env;
- the per-tick BitWorld protocol is preserved for both, so the idea's "policy interface" pin holds
  and the eight bundled bots keep working unmodified.

Two additive protocol messages make this work (full wire spec in `## Server, player, protocol`):
`0x90` player→game registration (prompt or baseline name) and `0x91` game→player plan. `0x91` is
sent **only** to seats that registered a prompt, because the bundled bots' parsers reject unknown
message types and would drop the frame.

### The LLM policy

**Planning turn.** Every `planIntervalTicks = 120` ticks (= 15 s wall at 8 Hz) the game composes
one observation per prompt seat and issues **all prompt seats' requests as ONE parallel batch**
(`curly.makeRequests`) — decisions are simultaneous, so they must be. Per-turn wall budget: the
batch has a **12 s** deadline (`planTimeoutSeconds`). The sim does **not** wait for it: hunters
keep executing their previous plan (or the scripted fallback) while the batch is in flight, and a
plan that lands late is applied on the next tick after it arrives. So the LLM contributes **0 s**
to the critical path, and the play budget is set purely by ticks: 3000 ticks ÷ 8 Hz = 375 s, plus
≤ 45 s roster wait, 5 s of round cards already counted, and a 20 s shutdown grace = **≤ 442 s,
which is 37 % of the 1200 s `episodeTimeoutSeconds` and well inside the 60 % (720 s) rule.** 25
planning turns per episode.

**Rate discipline.** ≤ 6 requests per 15 s = 24 req/min against a 30 req/min-per-episode sidecar
cap. The game additionally enforces a hard rolling budget of **28 requests per 60 s**; when the
budget is exhausted the turn is skipped, every prompt seat keeps its previous plan, and a
`fallback` event with `cause: "rate_budget"` is written. Retries (below) draw from the same
budget, and a seat that consumed a retry **skips its next planning turn**, so the worst case is
2 requests per seat per 30 s = 24 req/min.

**System prompt** (constant for every champion; the champion's own `PLAYER_PROMPT` is appended as
a `STRATEGY` block):

```
You are one hunter in a six-hunter cooperative hunting party on a 32x32 forest grid.
Rabbits die to one hunter. Boars need two hunters on perpendicular sides at once, stags
two on opposite sides, moose any three sides, elephants all four. Everyone standing on a
side when the animal falls scores the full value, so a moose or an elephant is worth many
rabbits - but only if your allies commit to the same animal at the same time. A half-formed
ring gets trampled or gored and scores nothing.
You give one high-level plan; a controller walks you there tile by tile until your next plan.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with the character {.
Schema:
{"intent":"hunt|assist|forage|rest|regroup|flee","target":"<one id from LEGAL TARGETS, or none>",
 "side":"N|S|E|W|any","with":["<ally alias>",...],"say":"<=120 chars","note":"<=200 chars"}
"say" is broadcast to spectators. "note" is private and is handed back to you next turn.
```

**User message** — the observation, deterministic, ≤ 2000 characters, every list bounded:

```
TURN 7/25  ROUND 2/3  TICK 1080/2880  VARIANT staghunt
YOU Cog-C at (14,19) facing N energy 86/200 score 14 level 2 role hunter
PARTY VISIBLE (<=5 lines)
  Cog-A (12,18) d=2
  Cog-E (19,22) d=5
ANIMALS VISIBLE (<=12 lines, nearest first)
  stag@13,17 needs 2 (opposite sides) sides taken: N d=2 worth 5
  rabbit@18,21 needs 1 sides taken: - d=4 worth 1
LEGAL TARGETS: stag@13,17, rabbit@18,21, none
BLOCKED TILES NEAR YOU (<=40): (13,18) (15,20) ...
LAST PLAN: intent=hunt target=stag@13,17 side=S result=not captured
YOUR NOTE: Cog-A followed me to the stag last turn; keep pairing with A.
RECENT (<=5 lines): t1032 Cog-A+Cog-C caught boar +3  t1050 Cog-E caught rabbit +1
STRATEGY: <the seat's PLAYER_PROMPT, truncated to 1200 runes>
```

`LEGAL TARGETS` is precomputed by the same predicate the validator applies (escrow 2026-08-23:
prompt drills alone do not fix formal-output fallbacks — ship the legal set in the observation).
`maxOutputTokens = 900` (400 truncates — playbook §Phase 1), Bedrock haiku first,
`output_config.effort` never sent.

**Reply schema and character caps.** JSON object; unknown keys ignored; extraction accepts
leading/trailing prose by taking the first balanced `{...}` span.

| field | type | cap | rule |
|---|---|---|---|
| `intent` | string enum | 12 chars | one of `hunt,assist,forage,rest,regroup,flee`; anything else → `hunt` |
| `target` | string | 24 chars | must be a member of `LEGAL TARGETS` or `none`; otherwise the reply is **illegal** and retried |
| `side` | string enum | 3 chars | one of `N,S,E,W,any`; anything else → `any` |
| `with` | array of string | ≤ 3 items, 8 chars each | non-alias entries dropped |
| `say` | free text | **≤ 120 runes** | rune-boundary truncation |
| `note` | free text | **≤ 200 runes** | rune-boundary truncation; private, echoed back next turn only to this seat |

**Every free-text field is truncated on rune boundaries, never byte boundaries** — a byte-cut
multi-byte rune is what makes replay bytes fail a strict JSON parser while still rendering in a
browser (playbook gotcha). The truncator is one helper (`std/unicode` `runeSubStr`) applied to
`say`, `note`, the registered prompt, policy names, and every error string that reaches the
replay or a sprite label.

**Executor.** The player turns a plan into per-tick masks with the pathfinding the bundled bots
already use (`bitworld/pathfinding`'s `pathStep`/`unstickStep`, plus staghunt's
`findKillSpot`/`bestCaptureSide`/anti-stuck ring buffer, lifted verbatim from
`players/big_game_hunter/big_game_hunter.nim`): walk to the chosen side tile of the chosen
target; if already on a 1-dot indicator tile, hold; if energy < 30, rest until 60; if the target
disappears, hold position until the next plan. The plan chooses *what and with whom*; the
executor chooses *which tile next*.

### Scripted baseline (same image, env-switched)

`PLAYER_SCRIPTED=<name>`, one of the eight ported from `players/*.nim` into
`src/cooperative_hunting/baselines.nim`: `rabbiteer`, `nearest_hunter`, `stag_hunter`,
`moose_hunter`, `elephant_hunter`, `big_game_hunter`, `sidekick`, `modeler`. They are the
starter's code, restructured from eight binaries into one binary with a dispatch, and their
behaviour is not to be retuned in v1.

**`big_game_hunter` is the default and the fallback baseline** (`PLAYER_FALLBACK_SCRIPTED`,
default `big_game_hunter`). Its algorithm, as read from the starter:

1. Derive the camera from any visible background tile object (`objectId = 8000 + ty*32 + tx` was
   drawn at `x = tx*12 - cameraX`), then locate self via the `0x07` identity packet.
2. Rebuild the obstacle map from visible tile sprites (tree/rock = blocked, grass = clear).
3. **Priority 1:** if any 1-dot capture indicator is within Manhattan 2, path to it and stand on
   it — that is a capture this tick.
4. Decode own energy from the HUD digit sprites at y=7; if energy < 30 sit still until it reaches
   60 (otherwise long episodes end frozen at 0).
5. Count allies within sight, derive the set of prey kinds catchable at that coalition size, and
   choose the highest-reward catchable prey, distance-penalised.
6. If cardinally adjacent to the target: hold. If holding for ≥ 12 ticks and the target is not a
   rabbit, reposition to the capture side that best completes the ring (rank-based side
   assignment among visible hunters, sorted by object id, so two bots do not pick the same side).
7. Otherwise A*/BFS-step toward the target; after 15 ticks with no position change, take an
   unstick step.
8. Emit at most one direction bit per tick, and only when the mask changed.

`sidekick` (follows the nearest ally and takes the complementary flank) and `modeler` (scores
every prey by `reward × learned per-ally cooperation probability × distance penalty`) ship as the
league fillers.

### Degrade, never hang

| failure | response |
|---|---|
| batch request times out (12 s) | retry **once**, that seat only, immediately, with the hint `Your last reply was not usable. Reply with ONE JSON object beginning with { and a target from LEGAL TARGETS.` |
| reply unparseable / not JSON / no balanced object | same single retry |
| `target` not in `LEGAL TARGETS` | same single retry |
| retry also fails | seat plays `PLAYER_FALLBACK_SCRIPTED` for this planning window; `fallback` event with `cause` ∈ `timeout,parse,illegal_target,rate_budget,no_credentials`; counted in `results.fallbacks[slot]` |
| no credentials at all (offline CI, cert without a key) | LLM client marks itself disabled at startup, **no network calls at all**, every prompt seat plays the fallback baseline; the episode still completes with `reason: complete` |
| a seat's websocket closes mid-episode | the seat is removed, its hunter leaves the world, remaining seats play on; its score is frozen and `disconnected: true` recorded |
| the wall-clock guard fires | episode settles at that tick with `reason: deadline` (see end conditions) |
| the game finishes | artifacts written, then `/healthz` and `/global` keep answering for a **20 s shutdown grace** before `quit(0)` — the certification runner pings `/global` *after* the player pods start and a fast exit fails the episode (lantern 0.1.3) |

Nothing in the tick loop ever blocks on a network read. The LLM batch lives on its own thread with
a deadline; the sim only ever polls a result slot.

### Two name spaces

- **In-game:** each seat is `Cog-A` … `Cog-F`, assigned once per episode by a seeded permutation
  of slots (so a policy cannot infer "slot 0 is always the strongest entrant"). Aliases are the
  only identifiers in prompts, plans, `with[]`, and `say` lines. The sprite stream carries no
  names at all, so scripted seats are anonymous by construction.
- **Spectator-side only:** the real policy name arrives on the player websocket query
  (`?name=<policy>`) and appears **only** in the replay's `seats[].name`, the chrome label the
  viewer reads, and `results.names[]`. The viewer shows `Cog-C · pack-caller`; the hunters never
  see the right-hand half.

---

## Sim module

Forked from `src/staghunt.nim` (one 2544-line file) and split, because the wasm replay module must
import the rendering half without the mummy server half:

| new path | from | change |
|---|---|---|
| `src/cooperative_hunting/sim_types.nim` | `staghunt.nim` types + consts | add `GameConfig` fields, `CaptureRule`, `PlayerRole`, `level`, `sideSeen`, `Item` (ore/food/berry) |
| `src/cooperative_hunting/sim.nim` | `staghunt.nim` L376–1274, 1912–1949 | world gen, movement, prey AI, capture resolution, variant rules. Pure; no mummy, no sockets, no files |
| `src/cooperative_hunting/art.nim` | `staghunt.nim` L432–614, 1280–1508 | sprite patterns, PNG loading, sprite cache, `addSpriteProtocolInit` |
| `src/cooperative_hunting/frames.nim` | `staghunt.nim` L1513–1906 | `buildPlayerFrame`, `buildGlobalFrame`, plus the new chrome label |
| `src/cooperative_hunting/replay.nim` | new (replaces `staghunt.nim` L2153–2223) | JSON replay writer + reader; the binary frame blob and `runReplayServer` are **deleted** — replays are never served by a pod |
| `src/cooperative_hunting/llm.nim` | `cogame-bullwhip/src/bullwhip/llm.nim` | transport ladder, batch, parse, truncation, fallback |
| `src/cooperative_hunting/baselines.nim` | the eight `players/*.nim` | one dispatch over eight bots |
| `src/cooperative_hunting.nim` | `staghunt.nim` L1955–2544 | the server: routes, roster, tick loop, results, replay write, shutdown grace |
| `src/cooperative_hunting_player.nim` | `players/rabbiteer/rabbiteer.nim` skeleton | the one player binary: registration, executor, baselines |

Kept verbatim, byte-for-byte: `sprites/12px/*.png` (rabbit, boar, stag, moose, elephant, hunter,
tree, rock, grass, ded), `nimby.lock`, the `Dockerfile` build stage recipe (nimby 0.1.26, Nim
2.2.4, `-d:release -d:useMalloc --opt:speed`), and `.claude/skills/*` (the balance-iteration
skills are still true of this sim).

**New art, real, not placeholders**, drawn with the starter's own `patternToRgbaSprite` pattern
DSL (the same one that draws the kill glow and the indicator dots) and baked into the sprite cache
at startup: iron node (grey rock silhouette with three white flecks), gold node (same silhouette,
palette index 8 flecks), a 3-tick countdown ring around a gold node with one side taken (the
idea's "countdown rings"), berry bush (tree silhouette recoloured with index-3 berries), tall
grass (two blade rows over the grass tile), and the level digit badge (reuse `DigitSpriteBase`
30–39 at a 1-px offset above the head — the idea's "levels over heads"). No new PNG asset is
needed and no placeholder box is acceptable.

`GameConfig`, fully:

```
tokens: seq[string]                       # 6 entries, one per slot
players: seq[string]                      # 6 display names, spectator-side only
num_agents: int = 6
seed: int = 5743127
variant: string = "staghunt"              # staghunt | coop-mining | lbf | predator-prey
rounds: int = 3
ticksPerRound: int = 960
tickHz: int = 8
planIntervalTicks: int = 120
planTimeoutSeconds: int = 12
playBudgetSeconds: int = 660
player_connect_timeout_seconds: int = 120
maxOutputTokens: int = 900
model: string = "claude-haiku-4-5"        # direct-Anthropic transport only
```

Derived per variant and not configurable: `captureRule`, `windowTicks`, `rewardSplit`, `roles`,
item populations. `focus: "elephant"` (staghunt's debug mode) is carried over unchanged for local
balance work and is never set by a manifest variant.

Determinism: one `Rand` seeded `seed + roundIndex`, advanced only inside the sim in the order
above. Given identical inputs, two runs produce identical state — asserted by a test.

---

## Server, player, protocol

### Game server

`/bin/cooperative-hunting --address:0.0.0.0 --port:8080`, mummy, staghunt's routing kept:

- `GET /healthz` → 200 `healthy`.
- `GET /player` **without** a websocket upgrade → the bitworld static player client page;
  `GET /client/player`, `/client/global`, `/client/snappy*` → the same static assets copied from
  `bitworld/client` in the Dockerfile. Registered before any catch-all. Neither route opens a
  player socket (lantern 0.1.1: the certification runner probes both **before** starting player
  pods and 404 or a socket side effect fails the episode).
- `GET /player?slot=N&token=T&name=NAME` **with** upgrade → seat N, token checked against
  `config.tokens[N]` when the roster is closed, else 403.
- `GET /global` with upgrade → the spectator sprite stream (also the runner's ping target).
- Everything else → 200 text.

**Roster.** The game waits for `num_agents` seats up to `player_connect_timeout_seconds`, then
starts. Config `players[]` names are display names; the real policy name comes from `?name=`.

**Artifacts.** `COGAME_CONFIG_URI` in, `COGAME_RESULTS_URI` → `results.json`,
`COGAME_SAVE_REPLAY_URI` → `replay.json`, then a 20 s grace, then `quit(0)`.

### Player protocol (`game.protocols.player`)

Base: **bitworld sprite_v1**, unchanged — server→client `0x01` sprite, `0x02` object, `0x03` remove,
`0x04` clear, `0x05` viewport, `0x06` layer, `0x07` identity; client→server the 2-byte
`[0x84|0x00, mask]` input packet (bit 0 up, 1 down, 2 left, 3 right, 4 A, 5 B, 6 select).

Two additive messages, and only two:

- **`0x90` client→server, registration**, sent once immediately after connect:
  `0x90 <u16 len> <len bytes UTF-8 JSON>`, `len ≤ 4096`. Body:
  `{"kind":"prompt","prompt":"<≤1200 runes>"}` or `{"kind":"scripted","baseline":"<name>"}`.
  Malformed, oversized or non-UTF-8 bodies are dropped and the seat is treated as
  `{"kind":"scripted","baseline":"big_game_hunter"}` — never a disconnect.
- **`0x91` server→client, plan**, sent only to seats that registered `kind: "prompt"`, at most one
  per planning turn: `0x91 <u16 len> <len bytes UTF-8 JSON>`, body
  `{"turn":7,"intent":"hunt","target":"stag@13,17","side":"S","with":["Cog-A"],"say":"...","src":"llm"}`
  where `src ∈ llm | fallback:<cause>`. Scripted seats never receive it, because the bundled bots'
  parsers reject unknown message types and would drop the whole frame.

### Global protocol (`game.protocols.global`)

The same sprite_v1 stream at world scale (384×384 px viewport, no identity packet), plus — copied
straight from paintbot — the **broadcast chrome smuggled as the label of a reserved 1×1 sprite,
id 4090**, re-emitted every tick. `client/broadcast_core.js` already routes sprite 4090's label to
`onText` and never registers it as drawable, so this path works identically live, in the generic
client, and in the hosted static replay. Label body (UTF-8 JSON, ≤ 4 KB, every free-text field
rune-truncated):

```json
{"tick":1080,"round":2,"rounds":3,"ticksPerRound":960,"phase":"play",
 "variant":"staghunt","reason":null,
 "seats":[{"slot":0,"alias":"Cog-A","name":"cooperative-hunting-pack-caller","kind":"prompt",
           "color":0,"score":14,"energy":86,"level":2,"role":"hunter","dc":false}],
 "feed":[{"t":1078,"kind":"catch","text":"Cog-A + Cog-C bring down a stag  +5 each"}],
 "beats":[{"t":210,"k":"round"},{"t":1078,"k":"bigcatch"}],
 "final":null}
```

`beats` is shipped **complete on the first frame** (paintbot's `ingestBeats` pattern) so the
scrubber tells the story before playback reaches it; `feed` carries only lines new since the
previous frame; `final` is null until the last round card, then
`{"reason":"complete","order":[{"alias":"Cog-A","name":"…","score":34},…]}`.

### Replay bytes (self-sufficient, strict UTF-8 JSON)

Written to `COGAME_SAVE_REPLAY_URI` as one UTF-8 JSON document. `docker_smoke.sh` parses it
(`SMOKE_REQUIRE_REPLAY_JSON=1`), the wasm module parses it in the browser, and nothing else is
contacted — no server, no config lookup, no name service.

```json
{"format":"cooperative-hunting/1","version":"0.1.0","coworld":"cooperative_hunting",
 "variant":"staghunt","generated_at":"2026-08-24T12:00:00Z",
 "seed":5743127,
 "config":{ ...every resolved GameConfig field, defaults expanded... },
 "world":{"w":32,"h":32,"tilePx":12,
          "tiles":"<1024 chars, '.'=grass 'T'=tree 'R'=rock, row-major>",
          "grass":[[x,y],...],"berries":[[x,y],...]},
 "seats":[{"slot":0,"alias":"Cog-A","name":"cooperative-hunting-pack-caller","kind":"prompt",
           "baseline":"","color":0,"level":2,"disconnected":false}],
 "rounds":[{"n":1,"startTick":1,"ticks":960,"seed":5743127,
            "roles":["hunter","forager",...]}],
 "ticks":[{"t":1,
           "p":[[x,y,facing,energy,score,flags],...],
           "q":[[id,kindOrd,x,y,flags],...],
           "c":[[x,y,ttl],...],
           "ev":[{"ev":"catch","kind":"Stag","x":13,"y":17,
                  "by":[{"slot":2,"alias":"Cog-C","score":14},{"slot":0,"alias":"Cog-A","score":21}],
                  "score":5,"energy":60}]}],
 "results":{"reason":"complete","names":[...],"aliases":[...],"scores":[...],
            "rounds":[[...],[...],[...]],"catches":[[r,b,s,m,e],...],
            "co_captures":[[...],...],"fallbacks":[0,1,0,0,0,0],"llm_requests":142}}
```

`p` is present on every tick (slot order, always `num_agents` entries). **`q`, `c` and `ev` are
omitted when unchanged/empty; an absent field means "identical to the previous tick".** That rule
takes the replay from ~2.1 MB to ~400 KB for a 3000-tick episode and is the only compression.
`flags` bits: 1 kill glow, 2 trample/gore glow, 4 alerted/pushed, 8 hidden in tall grass,
16 disconnected.

Event vocabulary — the complete list the replay may carry, and the only names the viewer must
know: `round_start`, `player_spawn`, `prey_spawn`, `catch`, `mine`, `pickup`, `forage`, `tag`,
`trample`, `moose_gut`, `plan`, `fallback`, `deadline`, `round_end`, `episode_end`. Per-tick
movement is **not** an event — it is in `p`/`q`. `plan` carries
`{alias, turn, intent, target, side, with, say, src}`; `fallback` carries `{alias, cause}`.

Everything the viewer needs is in these bytes: names (`seats[].name`), aliases, config, seed,
per-tick state, obstacles, events, results.

---

## Viewer

**A static wasm bundle, never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` (the
`coworld build` hook, committed mode 100755) builds it; the platform serves it from
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`. staghunt's
`runReplayServer` / `/client/replay` live-server path is **deleted**, not adapted.

### All four viewer files come from ONE starter: `Metta-AI/coworld-ctf`

staghunt has **no replay viewer at all** — no `replay-viewer/` directory, no `client/`, no
`static_replay*.js`, no `index.html` (verified by `find` over the whole clone). So the viewer
starter is its lineage parent, **`Metta-AI/coworld-ctf` (paintbot)**, and all four files come from
there and only there — never a mixture, because splicing one starter's shell onto another's
emscripten link flags deadlocks the viewer silently (cogame-lantern, 2026-08-23):

| file | copied from `coworld-ctf` | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | paths + `EXPORTED_FUNCTIONS` renamed `ctf_*`→`ch_*`; `--preload-file <root>/sprites@sprites` replaces `data@data`. **No `MODULARIZE`, no `EXPORT_NAME`** — keep the plain `-o …/cooperative_hunting_replay.js` link, `-s ENVIRONMENT=web,worker,node`, `-s ALLOW_MEMORY_GROWTH`, `-s ABORTING_MALLOC=1`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, `-d:useMalloc` |
| wasm entry `replay-viewer/cooperative_hunting_replay.nim` | `replay-viewer/ctf_replay.nim` | imports `cooperative_hunting/{sim,art,frames,replay}`; exports `ch_load_replay, ch_frame, ch_seek, ch_packet_ptr, ch_packet_len, ch_error_ptr, ch_error_len, ch_stage_ptr, ch_stage_len`; keeps the fixed `stageNote` buffer verbatim |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | same two files | `ctf_*` → `ch_*` in the worker's `Module._…` calls **and** in `importScripts` — renamed together, never one side; worker name `cooperative-hunting-static-replay`. Two deltas, both required: (a) `showFailure()` also sets `document.documentElement.setAttribute('data-replay-error', message)` — paintbot only writes `#status`; (b) the `coworld-replay` bridge `ready` is posted from **inside** the `loaded` branch, immediately after `data-replay-loaded="true"` is set, never on rAF at the call site (chorus `3c11c953`, 2026-08-24) |
| `index.html` | `client/replay_broadcast.html`, sed-substituted at bundle time exactly as `Dockerfile.replay-viewer` does | see chrome provenance below |

The bundle also carries `client/broadcast_core.js` (paintbot's sprite_v1 parser/renderer — it
already decodes `0x01/0x02/0x04/0x05/0x06` and routes sprite 4090's label to `onText`, which is
precisely our chrome channel) and `client/chrome_common.js`.

**The shell sets `data-replay-loaded="true"` on its first drawn frame and `data-replay-error` on
failure.** Both are load-bearing: `tools/ci/viewer_smoke.mjs` fails on silence and on the error
attribute.

**Pipeline:** `replay.json` → `ch_load_replay` parses it in wasm → for each frame the module
rebuilds the tick's `SimServer` state from `ticks[i]` and calls the **same `buildGlobalFrame`
the live server uses** → sprite_v1 bytes → `broadcast_core.js` → canvas + `onText` chrome. The
viewer re-derives every frame from the recorded state in the browser; the art is the game's own
PNG sprites, preloaded into the wasm filesystem.

### Chrome provenance

- `client/chrome_common.js` is copied **byte-for-byte** from `coworld-ctf`. Nothing in it is
  edited. It owns the clock, the transport bar, the scrubber, beat markers, lull spans and the
  spoiler toggle, and it resolves these ids by `getElementById`, every one of which the page must
  therefore keep: `btn-loop, btn-play, btn-skip, btn-spoilers, clock, clock-caption, clock-time,
  ffwd-chip, ffwd-mini, lulls, momentum, scrub, scrub-fill, scrub-head, scrub-win, speedchips,
  tick-clock, transport, win-chip`.
- `client/replay_broadcast.html` is **paintbot's page with a game block appended** — not a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The starter's `<head>`, CSS variables,
  `relayout()`, transport markup, endcard skeleton and bridge stay as they are.
- **Removed** starter elements (ctf-specific, replaced by the appended game block):
  `#fpv, #fpv-canvas, #fpv-cap, #fpv-gear, #fpv-grip, #fpv-hp, #fpv-hud, #fpv-map,
  #fpv-map-canvas, #fpv-name`, `#lockerroom, #lk-art, #lk-bg, #lk-cap, #lk-sprites`,
  `#killfeed` (replaced by `#feed`), `#povBadge`, `#mmwarn`, and — per the zoom decision —
  `#viewpanel, #zoombar, #zoom-in, #zoom-out, #zoom-read, #zoom-slider, #minimap,
  #minimap-canvas`. `#momentum`, `#lulls` and `#win-chip` are **kept as empty nodes** because
  `chrome_common.js` resolves them.
- **Zoom decision: dropped.** The arena is a fixed 32×32 tile board that is always drawn in full,
  scaled to fit the frame; nothing is ever off-screen, so the zoom bar and minimap have no job.
  `#viewpanel` is removed entirely, and `static_replay.js`'s `attachMinimap` is never called.
- The game block must **not** define a function named `markBeat` (or any other name in the
  ChromeCommon alias list) — hoisting shadows the alias and the beats render as unlabeled dead
  divs (tandem, 2026-08-23). Ours is `pushHuntBeat`.

### Transport rules

`--band` and `--hudscale` are set on `:root` by the starter's `relayout()`; the game block reads
them and never writes them. **Nothing is overlaid inside the transport band.** The endcard is
absolutely positioned with `bottom: var(--band, 0px)` so it stops above the bar, and **every seek
dismisses it** (the seek handler hides `#endcard` before issuing the seek). Scrubber beats are
clickable labelled `<button>` elements that seek to their tick, with CSS for **every kind
emitted** — `.beat-marker.round`, `.bigcatch`, `.smallcatch`, `.tag`, `.end` — and no other kind
is ever emitted.

### Readouts

- **Scorebug** (`#scorebug`, six plates in slot order): colour chip matching the hunter sprite,
  `Cog-C` alias, real policy name, score in big digits, an energy bar 0–200, and a role/level
  badge (`L2` in `lbf`, `HUNT`/`FORAGE` in `predator-prey`). Plate CSS:
  `.plate-name { flex: 1 1 auto; min-width: 3.2em }` and labels hidden under `640px`, because the
  softmax.com featured-match iframe is ~360 px wide and names otherwise collapse to "…".
- **Clock** (`#clock-caption` / `#clock-time` / `#tick-clock`): `ROUND 2 OF 3` and
  `1080 / 2880` — real numbers, never internal notation.
- **Feed** (`#feed`): one line per catch ("Cog-A + Cog-C bring down a stag  +5 each"), per plan
  `say` ("Cog-C: taking the north side, A come south"), per trample/gore, per tag and forage, and
  a muted line per fallback ("Cog-E fell back to big_game_hunter — timeout").
- **Scrubber** with beats, transport buttons, speed chips — all the starter's.
- **Endcard**: final standings, alias + policy name + score, and the end reason when it is not
  `complete`.
- **Grass toggle** (`predator-prey` only): a chip in the game block that switches tall-grass tiles
  between opaque and 40 % alpha so a spectator can see the hidden forager.
- **Legible at 360 px wide** — the scorebug, clock and feed are checked at that width, not at
  desktop width, and the `viewer_smoke.mjs` screenshot is the evidence.

---

## Packaging

**`compose.yaml`**

```yaml
services:
  cooperative_hunting:
    image: coworld-cooperative-hunting:latest
    platform: linux/amd64
    build:
      context: .
      network: host
```

The manifest image placeholder is derived from the **compose service name**, so it is
`{{COOPERATIVE_HUNTING_IMAGE}}` (lantern 0.1.0: `{{GAME_IMAGE}}` is not a thing; the manifest
generator reads `compose.yaml`).

**`Dockerfile`** — staghunt's two-stage build kept, extended to emit both binaries
(`/bin/cooperative-hunting`, `/bin/cooperative-hunting-player`), copy `bitworld/client` to
`./client`, `sprites/` and `coworld_manifest.json`. **`Dockerfile.replay-viewer`** is paintbot's,
retargeted at our module and sprite preload.

**`coworld_manifest_template.json`** — `$schema` set, ≥ 3 tags
(`coordination`, `multi-agent`, `grid`, `stag-hunt`), `game.runnable.type: "game"`,
`episode_timeout_minutes: 20` top-level, `game.config_schema` a real JSON Schema with
`minItems`/`maxItems` on **every** array property (`tokens` 6/6, `players` 6/6 — tandem 0.1.0),
`"replay_viewer": {"bundle": "static-replay-viewer"}`, and the game runnable env carrying
`ANTHROPIC_API_KEY_URI: "secret://coworld/cooperative-hunting/anthropic_api_key"` (hive,
2026-08-23 — without it the hosted container never receives the secret and every league episode
silently plays scripted).

**Variants — `num_agents: 6` in every one:**

| id | name | `game_config` |
|---|---|---|
| `staghunt` | Stag Hunt | `{num_agents:6, variant:"staghunt", rounds:3, ticksPerRound:960, tickHz:8, seed:5743127}` |
| `coop-mining` | Cooperative Mining | `{num_agents:6, variant:"coop-mining", rounds:3, ticksPerRound:960, tickHz:8, seed:5743128}` |
| `lbf` | Level-Based Foraging | `{num_agents:6, variant:"lbf", rounds:3, ticksPerRound:960, tickHz:8, seed:5743129}` |
| `predator-prey` | Predator & Prey | `{num_agents:6, variant:"predator-prey", rounds:4, ticksPerRound:720, tickHz:8, seed:5743130}` |

Each variant carries a `description` (required by the 0.1.42 upload contract) and its six
`players[]` display names.

**Certification fixture** — `certification.game_config`:
`{num_agents: 6, variant: "staghunt", rounds: 2, ticksPerRound: 480, tickHz: 8, seed: 5743127,
players: [six names], tokens: [six]}`, and `certification.players` seats **all six**:
`[pack-caller, pack-caller, big-game-hunter, big-game-hunter, sidekick, modeler]`. Every declared
bundled player occupies at least one slot (raid 0.1.2 → 0.1.3: a fixture that omits a declared
runnable fails `players_missing`), and `len(certification.players) == num_agents == 6 ==
SMOKE_SEATS`. Duration: 1040 ticks ÷ 8 Hz = **130 s**, and the replay is 1040 frames = 43 s of
playback at the viewer's 24 fps — comfortably longer than the 10 s soak window (ecos, 2026-08-23).

**Bundled players** (`player[]`, all four on `{{COOPERATIVE_HUNTING_IMAGE}}`, all running
`/bin/cooperative-hunting-player`):

| id | env | description |
|---|---|---|
| `pack-caller` | `PLAYER_PROMPT: "<default hunting strategy in words>"` | the reference prompt policy |
| `big-game-hunter` | `PLAYER_SCRIPTED: "big_game_hunter"` | coalition-aware highest-reward baseline |
| `sidekick` | `PLAYER_SCRIPTED: "sidekick"` | follows an ally and takes the complementary flank |
| `modeler` | `PLAYER_SCRIPTED: "modeler"` | expected-value bot with learned per-ally cooperation rates |

**`game.docs`** — `readme` `{type:"text", value:"…"}` plus `pages[]`:
`rules.md` (Cooperative Hunting Rules), `variants.md` (the four variants and their numbers),
`protocol.md` (sprite_v1 plus the `0x90`/`0x91` extension, with byte layouts), `policies.md` (how
to field a policy: `PLAYER_PROMPT` vs `PLAYER_SCRIPTED`, and the reply schema with its caps).
**`game.protocols` carries both `player` and `global`**, each as
`{"type":"text","value":"…"}` objects — not bare strings (cogame-garble 0.1.0, 2026-08-24).

**`tools/ci/policies.json`** (phase 40 mints these; fillers must be distinct versions from the
champions, and both champions carry `USE_BEDROCK: "true"` alongside the prompt):

```json
[{"name":"cooperative-hunting-pack-caller","run":"/bin/cooperative-hunting-player",
  "env":{"PLAYER_PROMPT":"Commit to the biggest animal your visible party can actually take. Name the allies you need in \"with\" and take the side you name in \"side\"; do not switch targets while a ring is forming.","USE_BEDROCK":"true"}},
 {"name":"cooperative-hunting-quartermaster","run":"/bin/cooperative-hunting-player",
  "env":{"PLAYER_PROMPT":"Watch energy first. Below 60 energy take rabbits and recharge; above it, join whichever big animal already has the most sides taken and hold the side you claimed.","USE_BEDROCK":"true"},
  "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
 {"name":"cooperative-hunting-biggame","run":"/bin/cooperative-hunting-player",
  "env":{"PLAYER_SCRIPTED":"big_game_hunter"}},
 {"name":"cooperative-hunting-sidekick","run":"/bin/cooperative-hunting-player",
  "env":{"PLAYER_SCRIPTED":"sidekick"}}]
```

Champion #1 (`pack-caller`) is owned by daveey, champion #2 (`quartermaster`) by daveey-1 via the
`player` field; the two scripted entries are the league fillers. **Both champions are
`PLAYER_PROMPT`** — a scripted policy seated as a champion is a failure state.

**Workflows** — `.github/workflows/ci.yml` and `coworld-release.yml` from coworld-builder
`templates/`, with `<slug>` = `cooperative-hunting`, `<IMAGE>` = `coworld-cooperative-hunting`,
`<SEATS>` = `6`. `tools/ci/docker_smoke.sh` (mode 100755) and `tools/ci/viewer_smoke.mjs`
(verbatim, no substitutions) copied from the same templates.

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` twice (debug and `-d:release`).

1. **`tests/test_capture.nim`** — the capture predicates, positive and negative: rabbit on any one
   side; boar on each of the four perpendicular pairs and *not* on an opposite pair; stag on each
   opposite pair and *not* on a perpendicular pair; moose at 3 and 4 sides but not 2; elephant only
   at 4. `windowTicks = 1` reproduces the base rule exactly; `windowTicks = 3` captures a gold node
   from two hunters 2 ticks apart, does **not** at 3 ticks apart, and credits both slots.
   `levelsum`: levels 1+2 take a level-3 food, 1+1 do not, and the split floors with the remainder
   to the lowest slot. `predator-prey` tagging fires only on opposite sides.
2. **`tests/test_step.nim`** — resolution order and movement: 5-tick cooldown, 2 energy per move,
   blocked by tree/rock/hunter/animal, passive recharge stops at 100, trample −30 and the two-tile
   slide, gore −10 with the shove, corpse lifetime 48, tall-grass hiding only beyond distance 2.
   Plus **determinism**: two 500-tick runs from the same seed and the same input script produce an
   identical state digest.
3. **`tests/test_scoring.nim`** — the scoring formula per variant, cumulative round totals, sign
   (no score is ever decremented), `results.json` shape: `names`/`scores`/`aliases` all length
   `num_agents`, `reason ∈ {complete, deadline, no_players}`, and the deadline path scoring the
   partial round rather than zeroing it.
4. **`tests/test_baseline_orders.nim`** — the **bounded-orders / legality assertion on the scripted
   baseline**: all eight baselines driven against a scripted 2000-tick world; assert every emitted
   mask has at most one direction bit set, is `≤ 0x7f`, sets no undefined bit, and is emitted at
   most once per tick; assert every `0x90` body is ≤ 4096 bytes, valid UTF-8 and valid JSON; assert
   no baseline ever emits a move it cannot pay for. A baseline that produces an illegal or
   unbounded order fails CI.
5. **`tests/test_episode.nim`** — **end-to-end episode writing a replay**: six scripted seats, 2
   rounds × 120 ticks, in-process, writing `results.json` and `replay.json` to a temp dir; assert
   the game settles with `reason: complete`, exits 0, and the replay's `ticks.len` equals the
   recorded tick count including round cards.
6. **`tests/test_replay_parse.nim`** — **strict UTF-8 replay parse**: `validateUtf8(bytes) == -1`
   and `parseJson` succeeds on the replay written by test 5; every required key present
   (`format, config, seed, world, seats, rounds, ticks, results`); `seats[].name` and `.alias` both
   populated; every `say` ≤ 120 runes and every `note` absent from the replay; a `say` seeded with
   a multi-byte rune at the cap boundary survives as valid UTF-8; and re-feeding each tick through
   the replay renderer yields a non-empty sprite packet.
7. **`tests/test_llm_reply.nim`** — reply handling: clean JSON; JSON with trailing prose; prose
   before `{`; missing fields defaulted; a `target` outside `LEGAL TARGETS` triggering exactly one
   retry and then the fallback; over-long `say`/`note` truncated on rune boundaries; and the
   no-credentials path making zero network calls and returning the baseline plan immediately.
8. **`tests/test_chrome.nim`** — the sprite-4090 chrome label is valid UTF-8 JSON, ≤ 4 KB, carries
   every field the page reads, emits only beat kinds in `{round,bigcatch,smallcatch,tag,end}`, and
   — reading `client/replay_broadcast.html` — the appended game block declares no
   `function <name>` colliding with the ChromeCommon alias list (tandem, 2026-08-23).

`docker-smoke` job: builds the image and runs `tools/ci/docker_smoke.sh` with `SMOKE_SEATS=6`,
one game container plus six player containers on a per-run network, driven by the certification
fixture; asserts the game exits 0, `results.json` and `replay.json` exist, the replay parses as
UTF-8 JSON, and **every player container exited 0** (raid 0.1.4 — the starter smoke only checks
the game; the player's receive loop must catch `CatchableError` on a dead socket and exit 0).
Uploads `dist/smoke/` as the `smoke-replay` artifact.

`wasm-viewer` job (`needs: docker-smoke`): asserts `tools/build_replay_viewer.sh` and
`tools/ci/viewer_smoke.mjs` exist and the hook is executable; builds the bundle; then
**executes** it —

```
node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
  --replay dist/smoke/replay.json --timeout 90 --soak 10
```

— against the replay `docker-smoke` just produced. The bundle is run in headless chromium, not
merely built: it must set `data-replay-loaded="true"`, keep the clock/tick/scorebug advancing
through the soak with no uncaught page error, and answer the 0 %/50 %/100 % scrub probes with
three different clocks. The 43 s cert replay outlasts the 10 s soak by design.

---

## Out of scope (v1)

1. **MP Boat Race (eight races, 75-tick partner choice + 225-tick paddle/flail).** This is the one
   variant in the idea that is *not* the same mechanic with different numbers: it needs a pairing
   market, a race track with lanes and progress, a per-tick two-action payoff matrix, and a
   reputation carried between races. None of that is a knob on the capture predicate; it is a
   second sim living in the same repo. It ships as its own coworld, or as a v2 variant once the
   four in scope are certified and ranked.
2. **LBF's H1–H4 heuristic fillers.** The league needs ≥ 1 scripted filler and gets two
   (`big_game_hunter`, `sidekick`); the paper's heuristics add four more near-duplicates of
   behaviour the level-sum rule already exercises. Deferred until there is evidence the ladder
   needs more spread.
3. **Seat counts other than 6.** The idea allows 2–8; v1 pins 6 everywhere so the manifest, the
   cert fixture and `SMOKE_SEATS` cannot drift apart. Other counts are a later variant set, not a
   v1 knob.
4. **Animals in `predator-prey`.** That variant ships with NPC animals disabled — the only targets
   are berry tiles and forager seats — so the asymmetric role is tested on its own rather than
   tangled with the encirclement economy.
5. **staghunt's `tools/` grader and reporter runnables** (the episode-interestingness grader and
   the Bedrock sports-commentary reporter, plus `Dockerfile.tools` and `tools/staghunt_tools/`).
   They are not required for certification, add a second image and a second Python toolchain to
   the release, and the reporter's narration duplicates the viewer feed. Dropped from the fork;
   the code stays in `coworld-staghunt` if it is wanted later.
6. **The live human/spectator client beyond what the platform probes.** `/client/player`,
   `/client/global` and the `/global` socket are served (certification requires them), but no work
   goes into human playability, and `/client/replay` is deliberately gone — replays are the static
   wasm bundle only.
7. **Retuning staghunt's balance constants.** Flee probabilities, gut/trample numbers, reward
   table and spawn targets are carried over unchanged. `.claude/skills/stag-hunt-balance` and
   `balance_sweep.sh` come along for a later balance pass, and CI does not run them.
