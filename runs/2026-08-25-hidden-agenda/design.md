# Hidden Agenda — four cogs mine a station, one of them carries a freeze beam, and nobody may say a word

**Starter: `Metta-AI/coworld-ctf` (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`.**
Hidden Agenda is a real-time grid loop with fog-of-war vision, per-tick grid actions and a per-tick
replay — the first row of the starter table ("any real-time game loop, grid OR continuous physics, new
rules written for this coworld"). Paintbot is the only starter that already owns the three things this
game is built out of: a tick loop with **line-of-sight fog**, a **static wasm replay bundle** with the
broadcast chrome, and the CI shape. **Every convention there holds here unless this note says
otherwise.** Two things paintbot does not have are ported from `Metta-AI/cogame-bullwhip` (mounted at
`/workspace/starters/cogame-bullwhip`) and are named as such where they appear: the *game-side* batched
LLM decision layer (`src/bullwhip/llm.nim`) and the thin prompt-carrying player process
(`src/bullwhip_player.nim`). **All four viewer files come from coworld-ctf only** (see `## Viewer`).

`Metta-AI/coworld-among-them` is the **rules reference only**, read at `/tmp/among-them`
(`docs/rules.md`, `sim.nim`, `config.json`). Its engineering scaffold is *not* copied: it carries the
old multi-role manifest schema (commissioner / grader / diagnoser / reporter), a Bitscreen pixel
player protocol, no static wasm replay viewer, and none of the builder CI conventions. What is
carried over from it is **game-rule fidelity only**, and where a constant is inherited it is named:
`TaskCompleteTicks = 72` becomes `mineTicks = 72`, `killCooldownTicks` becomes
`freezeCooldownTicks`, its meeting → chat → simultaneous-vote → ejection loop becomes the meeting
loop below, and its "teleport everyone to the meeting button and restore afterwards"
(`meetingHome`) behaviour is kept.

There is **no `OPEN` section**: every rule the idea leaves loose — ejection rules, tie rules, freeze
range and cooldown, gem economy, map, vision model, whether an ejected impostor ends the game — is
decided below with the reason stated inline.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins), each answered
explicitly:**

| pin | how Hidden Agenda satisfies it |
|---|---|
| starter by game shape | `Metta-AI/coworld-ctf` (paintbot) — a real-time grid loop with fog-of-war vision and rules written for this coworld; nothing external is reproduced bit-for-bit, so this is not a `cogame-moba` port, and it is not a parley/babel turn-based talk game. |
| public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-hidden-agenda`, **public** — a certification prerequisite (`source-resolves` 404s on private). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | one image; `PLAYER_PROMPT="<strategy>"` vs `PLAYER_SCRIPTED=miner\|lurker` (`## Decisions`). Champions #1 `hidden-agenda-sleuth` (daveey) and #2 `hidden-agenda-shadow` (daveey-1) are **both prompt policies**; the two fillers are the two scripted baselines. Both baselines and both prompts cover **both roles**, because a filler can be seated as the impostor. |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` live viewer is declared (`## Viewer`, `## Packaging`). |
| real art, starter chrome verbatim | `scripts/art/gen_agenda_art.py` commits the station tiles, seams, grate, five cog bodies, the ice block and the beam FX; `client/chrome_common.js` ships **byte-for-byte** and `client/replay_broadcast.html` is the starter's page with a game block appended (`## Viewer`). |
| legible to a casual spectator | `DEPOSITS 21 / 32`, `CREW LEFT 3`, `MEETING 4 — VOTING`, a vote board that reads `PINK → BLUE`, and a full-width `CAUGHT! PINK FROZE GREEN — RED SAW IT` banner; checked at 360 px. |
| two name spaces | anonymous cog aliases `RED BLUE GREEN YELLOW PINK` in-game and in every prompt; policy names only spectator-side (`roster[].pol`, the roster strip, `results.names`) — `## The game` §Seats. |
| degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | ≤ 686 s worst case against a 720 s budget, deadline checked between decision batches, retry-once-then-scripted, `maxDecisionBatches = 20`, `shutdownGraceSeconds = 20` (`## Decisions`). |
| `num_agents` in every variant AND the cert fixture | **5**, in all three variants, in `certification.game_config`, and as `<SEATS>` in `tools/ci/docker_smoke.sh` (`## Packaging`, `## Tests`). |
| replay bytes self-sufficient | aliases, policy names, **roles**, the full map, every rule constant, the seed, per-tick state, the per-tick visibility masks, the race series, every event (including the witnessed-freeze log, the vote-change rows and the `caught` banner rows) and the final results all live in the replay (`## Sim module` §The replay file). |
| prove it in CI | sim tests, bounded-orders/legality tests on both baselines, a feasibility oracle, a no-leak test, an end-to-end episode writing a replay, a strict-UTF-8 parse, an **executed** viewer smoke (`## Tests`). |

**Source idea (verbatim):**

> MP Hidden Agenda (mod of coworld-among-them) — a no-talk, freeze-beam, witnessed-kill variant of the live Among Them
>
> EXTENSION of Metta-AI/coworld-among-them — Among Them (crewmates do tasks, report bodies, chat in meetings, vote; impostors kill on cooldown) is already uploaded and live. Hidden Agenda is the same game with Melting Pot's rules, so ship it as a variant:
>     Gem economy: crewmates carry ≤2 gems to a central grate; 32 deposits = crew win (replaces task list).
>     Freeze beam: the impostor freezes rather than kills; frozen crew stay on the map (evidence) and can't act.
>     Witness trigger: a meeting starts immediately when a freeze happens inside another player's field of view — plus the fixed 200-tick cadence.
>     No-talk deliberation: 25 ticks of visible, changeable votes with no chat — the pure spatial-evidence mode; keep Among Them's chat as the default.
>     Win/tie rules: impostor wins at one crewmate left; 3000-tick timeout is a 0-0 tie.
>
> Seats: 5 (4 crew + 1 impostor)
> Motive: zero-sum hidden-role
> Integrity: roles seeded; anonymous aliases; witnessed-freeze trigger logged.
> Replay plan: spectator sees roles; 'caught!' banner on a witnessed freeze; live vote changes in the last ticks.
>
> Source: meltingpot hidden_agenda (https://youtu.be/voJWckiOh5k); github.com/Metta-AI/coworld-among-them.

---

## The game

### Seats, roles, aliases, names

**`num_agents = 5`.** Exactly five seats, one cog each. **Four crew and exactly one impostor**, as the
idea pins.

| slot | in-game cog alias | body colour (`slots[].color`) | spawn cell (rotation offset 0) |
|---|---|---|---|
| 0 | `RED` | `red` | (13, 7) |
| 1 | `BLUE` | `blue` | (11, 7) |
| 2 | `GREEN` | `green` | (15, 7) |
| 3 | `YELLOW` | `yellow` | (11, 11) |
| 4 | `PINK` | `pink` | (15, 11) |

Cells are `(col, row)`, origin top-left. Aliases are fixed to slots and never rotate — a vote for
`PINK` is unambiguously a vote for the pink cog on screen, which is what makes the broadcast readable.
The **spawn list is rotated by `seed mod 5`**, so no slot has a fixed starting cell and a policy cannot
learn "slot 4 starts in the south-east". Each cog spawns **facing away from the grate centre** (the
quadrant containing the vector from (13,9) to its spawn cell; exact ties resolve to `N`).

**Role assignment.** The impostor slot is drawn uniformly from `0..4` by
`rngRole = seededRng(seed xor 0x1DEA5EED)`, a sub-stream used for **nothing else**; every other draw in
the game (spawn rotation, seam order, tie-breaks) comes from `rngWorld = seededRng(seed)`. The seed is
never shown to a seat. The config field `impostorSlot` (default `-1` = draw it) pins the impostor for
the certification fixture and for tests; league variants leave it at `-1`. This is the idea's "roles
seeded", and the separation of sub-streams is what makes it true of the *bytes*: `worldHash(seed)` is
identical whichever slot ends up as the impostor (`tests/test_noleak.nim`).

**Who knows what about roles.** **Nobody in-game sees another seat's role.** The impostor is told it is
the impostor and — because there is exactly one — is told that the other four are crew. Each crew seat
is told it is crew and that **exactly one of the other four is the impostor**. No seat ever receives
another seat's role, plan, `hunch`, `notes`, or the seed. **The spectator and the replay see every
role**: `roles[]` is in the replay header, one `reveal` event per seat is emitted at tick 0, and
`results.roles[]` carries them — but no player frame ever does, not even the terminal `final` frame
(§`Server, player, protocol`).

**Two name spaces (pin).** A seat sees only aliases in every observation and every prompt. No policy
name, player name, account or model name reaches a seat. The replay carries `policyNames[]` alongside
`names[]`; the viewer's roster strip and plate sublines show the **policy** name (paintbot's
`roster[].pol` path in `client/chrome_common.js`, `teamPolicies()`); `results.names[]` carries policy
names for the platform. Both, not either.

### The station

A single authored map, `data/maps/vault.txt`, **27 cols × 19 rows**, cell 40 board-px → a **1080 × 760**
board. **The whole board always fits the frame**, which is why the viewer drops `#viewpanel` (zoom bar +
minimap) entirely (`## Viewer`). The map is loaded from this exact committed ASCII file — it is the
specification, not an illustration:

```
###########################
#.......##.......##.......#
#.S.....##...S...##.....S.#
#....#..##.#...#.##..#....#
#.......##.......##.......#
#.......#####.#####.......#
####.########.########.####
####.####.........####.####
####.####.#.GGG.#.####.####
####........GGG........####
####.####.#.GGG.#.####.####
####.####.........####.####
####.########.########.####
#.......#####.#####.......#
#.......##.......##.......#
#....#..##.#...#.##..#....#
#.S.....##...S...##.....S.#
#.......##.......##.......#
###########################
```

Legend: `#` wall (impassable, blocks line of sight), `.` floor, `G` the **grate** (walkable, 3 × 3 at
`x 12..14, y 8..10`), `S` a **gem seam** (impassable, blocks line of sight, mined from any orthogonally
adjacent floor cell). 249 cells are walkable and every one of them is reachable from the grate
(`tests/test_map.nim` asserts connectivity, and that every seam has ≥ 1 walkable orthogonal neighbour).

Rooms, named because the observation, the `patrol` job and the feed all use these names:

| id | name | interior | seam | walk distance, grate centre → nearest mining cell |
|---|---|---|---|---|
| `NW` | NORTHWEST VAULT | x 1..7, y 1..5 | `S1` (2, 2) | 17 |
| `N` | NORTH GALLERY | x 10..16, y 1..4 | `S2` (13, 2) | 6 |
| `NE` | NORTHEAST VAULT | x 19..25, y 1..5 | `S3` (24, 2) | 17 |
| `SW` | SOUTHWEST VAULT | x 1..7, y 13..17 | `S4` (2, 16) | 17 |
| `S` | SOUTH GALLERY | x 10..16, y 14..17 | `S5` (13, 16) | 6 |
| `SE` | SOUTHEAST VAULT | x 19..25, y 13..17 | `S6` (24, 16) | 17 |
| `HUB` | THE GRATE | x 9..17, y 7..11 | — | 0 |

Each room has **exactly one doorway** (`NW` (4,6), `NE` (22,6), `SW` (4,12), `SE` (22,12), `N` (13,5),
`S` (13,13)) and interior pillars that break sightlines. A cul-de-sac is a dangerous place to mine —
that is deliberate, and it is the whole reason the gem economy creates freeze opportunities. The two
galleries are cheap (6 cells) and the four vaults are expensive (17); a crew that only works the cheap
seams runs them dry and must eventually walk into a vault alone.

Every sim quantity is an **integer** (there are no floats in sim state anywhere), and the RNG is
paintbot's seeded stream, so a seed reproduces a replay bit-exactly.

### Vision: a facing cone, and why it is a cone

Vision is the whole game — the witness trigger, the alibi, the "who could have seen that" reasoning all
hang off it. **Vision is a 90° facing cone plus a small omnidirectional awareness ring, both gated by
line of sight.** Every cog has a `facing ∈ {N, E, S, W}`.

A cell `c` is **visible** to an active cog `p` iff **both**:

1. `los(p.cell, c)` is clear — the supercover Bresenham walk from `p.cell` to `c` crosses no `#` wall
   and no `S` seam cell (endpoints excluded); **and**
2. `chebyshev(p.cell, c) ≤ awarenessRadius = 2`, **or**
   `chebyshev(p.cell, c) ≤ visionRadius = 8` **and** `c` lies in `p`'s facing quadrant, where for
   `facing = N` the quadrant is `dy < 0 and abs(dx) <= -dy`, and the other three are the same wedge
   rotated (`S`: `dy > 0 and abs(dx) <= dy`; `E`: `dx > 0 and abs(dy) <= dx`; `W`: `dx < 0 and
   abs(dy) <= -dx`).

Frozen bodies and ejected cogs do **not** block movement or line of sight — a body in a one-wide
corridor would otherwise permanently sever the map.

**Why a cone and not a circle.** A symmetric circle would make vision reflexive: if A cannot see B then
B cannot see A, and the impostor's own "is anybody watching me?" check would be a *perfect* witness
detector. The witnessed freeze — the idea's headline mechanic and the `CAUGHT!` banner — would then
never fire against a competent impostor. A facing cone makes vision genuinely asymmetric: somebody
behind you sees you and you do not see them. That is the risk the beam carries.

**Facing is not micro-managed by a policy, and it is not arbitrary either.** Facing is set
deterministically by the kernel from the job the seat chose (§Jobs, step 8 of the tick order), and
every rule is documented so a policy can reason about it: a moving cog faces its direction of travel; a
mining cog faces its seam; a `watch` cog faces its target; a `guard` cog sweeps one quadrant clockwise
every `sweepTicks = 8`. Choosing `guard` over `mine` is therefore a real, legible choice about what you
will be able to see.

**Vision is evaluated on demand for objects, never per cell.** The sim tests visibility of the 4 other
cogs, the 6 seams, the grate and the known bodies — ~15 `los` calls per cog per tick — so the FOV cost
is ~75 `los` walks per tick, not 249 × 5. The viewer draws the wedge geometrically from
`(cell, facing, visionRadius)`; no per-cell mask is ever recorded.

### The gem economy

- **Seams.** 6 seams, `seamCapacity = 3` gems each (18 standing at tick 0), regrowing **+1 gem every
  `seamRegrowTicks = 120` ticks** up to capacity. Global supply ≈ 1 gem / 20 ticks once all six are
  regrowing; global crew demand at full tilt ≈ 1 gem / 24 ticks. Supply is deliberately *just* ahead of
  demand, so the cheap galleries run dry under load and force vault trips.
- **Mining.** A cog standing on a floor cell orthogonally adjacent to a seam, with a `mine` intent and
  hands not full, advances `mineProgress`; at **`mineTicks = 72`** (Among Them's `TaskCompleteTicks`,
  kept deliberately) it takes one gem: `seam.gems -= 1`, `carry += 1`, `mineProgress = 0`, emits `mine`.
  Progress resets to 0 if the cog moves, is frozen, or a meeting opens. Any number of cogs may mine the
  same seam simultaneously from different adjacent cells; supply, not exclusivity, is the limit.
- **Carrying.** `carryCap = 2` — the idea's "crewmates carry ≤2 gems". Hands full ⇒ `mine` degrades to
  `wait`.
- **Depositing.** A cog standing on any grate cell with a `deposit` intent and `carry > 0` deposits
  **one gem per tick**. For a **crew** cog: `deposits += 1`, `carry -= 1`, emits `deposit`. For the
  **impostor**: `carry -= 1`, the gem is destroyed, the counter does **not** move, and it emits
  `fakedeposit` carrying `seenBy` = the aliases of active cogs whose FOV contains that grate cell.
- **The impostor really mines and really carries.** It is not a pantomime: gems it takes leave the seam
  (a real cost to crew supply) and it visibly holds them. The *only* difference is that its deposit
  does not move the counter. `deposits` is public to every seat, so a crew cog that is standing at the
  grate watching the impostor deposit **and** sees the counter fail to advance has caught it cold. That
  is a genuine spatial-evidence channel — it costs you a trip to the grate to be there — and it is
  exactly the kind of inference this game should reward. It is also why the `miner` baseline's impostor
  branch refuses to fake-deposit while anything is in view.
- **`depositTarget = 32`.** Reaching it is an immediate crew win, exactly as the idea pins.

### The freeze beam

- Impostor-only action `freeze`, with target alias. Legal iff **all** of: the impostor is active;
  `freezeCooldown == 0`; the target is an **active crew** cog; `chebyshev(impostor, target) ≤
  freezeRange = 2`; and `los(impostor.cell, target.cell)` is clear. Range is a Chebyshev *radius*, not
  the vision cone — you may freeze something beside or behind you.
- On success: the target's state becomes **`frozen`** at its current cell, permanently for the episode
  (there is no thaw — the idea says frozen crew "stay on the map (evidence) and can't act"). It stops
  acting, stops mining, **does not vote**, and its carried gems are lost with it. The impostor's
  `freezeCooldown` is set to **`freezeCooldownTicks = 220`**. Emits `freeze`.
- At most one freeze resolves per tick.
- **Freezes never happen during a meeting.**

`freezeCooldownTicks = 220` is the balance knob. The impostor needs **three** removals (from four crew
down to one), so three clean freezes cost ≥ 440 ticks of cooldown plus travel — against a clean crew's
~800–1000 ticks to 32 deposits. That is the race, and `tests/test_feasibility.nim` gate (b) is what
holds it.

### The witness trigger

At the tick a freeze resolves, compute the witness set **W** = every **active** cog other than the
impostor and the victim, evaluated with the positions and facings **as they stood at the start of that
tick**, whose FOV contains the **victim's cell or the impostor's cell**.

- For each `w ∈ W` emit a `witness` row: `{t, witness, freezer, victim, cell, sawFreezer, sawVictim}`.
  This is the idea's "witnessed-freeze trigger logged" integrity requirement, and it is in the replay
  bytes, not only in a log line.
- If `W` is non-empty, emit **`caught`** `{t, freezer, victim, witnesses[]}` (the banner event) and
  **open a meeting immediately**, at the end of that same tick, with `cause: "witness"`. Immediately
  means immediately: no cooldown, no cadence check.
- Each witness's own observation from then on carries a private `youWitnessed[]` entry. In the chat
  variant it can say so; in the no-talk variant its only channel is its vote — which is precisely "the
  pure spatial-evidence mode" the idea asks for.

Seeing the *victim's* cell counts even without seeing the freezer, because what a bystander actually
perceives is a crewmate turning to ice. `sawFreezer` distinguishes "I know who did it" from "I know it
happened here"; the observation carries both flags so a policy can weigh them.

The number of witnessed meetings is bounded by three (three removals ends the game), which is what keeps
the decision-batch budget bounded (`## Decisions`).

### Meetings, deliberation, and the vote

Meetings open on exactly **two** causes, as the idea pins:

1. **`cadence`** — the `meetingCadenceTicks = 200` timer reaches 0. The timer is **reset to 200 at the
   end of every meeting**, of either cause, so meetings are ≥ 200 play-ticks apart unless a freeze is
   witnessed.
2. **`witness`** — a witnessed freeze, immediately, as above.

There is **no manual report button and no emergency button.** Among Them has both; Hidden Agenda
deliberately has neither, because the idea names exactly two triggers and a report button would let a
crew cog convert "I found a body" into a meeting without ever having been in the room when it happened,
which flattens the spatial-evidence premise.

On open, all **active** cogs' positions and facings are saved and they are teleported to five fixed
meeting seats around the grate — `(11,8) (15,8) (11,10) (15,10) (13,11)`, assigned in slot order among
the active seats — each facing the grate centre. This is Among Them's `meetingHome` behaviour, kept.
Frozen cogs stay where they are (they are the evidence). Positions and facings are restored exactly at
the end of the meeting.

**Meeting timeline.** `m0` is the tick the meeting opens. Two shapes, one per deliberation mode:

| offset from `m0` | `hidden-agenda` (chat, `meetingTicks = 60`) | `hidden-agenda-notalk` / `-blind` (`meetingTicks = 25`) |
|---|---|---|
| 0 | meeting opens; teleport; `meeting` event; **the decision batch is issued and awaited** | same |
| `sayTick` | **10** — every seat's `say` is revealed to all seats simultaneously and appended to the public transcript; `say` events emitted | — (no chat; `say` is not requested, not accepted and never recorded) |
| `revealTick` | **24** — all initial votes posted simultaneously and become visible; `vote` events, `phase: "initial"` | **5** — same |
| `switchTick` | **46** — conditionals evaluated; changed votes emitted, `phase: "switch"` | **18** — same |
| `resolveTick` | **56** — tally, ejection | **23** — same |
| `meetingTicks` | **60** — restore positions, reset the cadence timer, resume play | **25** — same |

The 25-tick no-talk shape is the idea's number, and the switch at `m0+18` with the resolve at `m0+23` is
what puts "live vote changes in the last ticks" on screen exactly where the idea's replay plan asks for
it.

**Votes are visible and changeable, on one LLM call.** A seat's meeting reply carries `vote` (its
first choice) and an optional one-shot conditional `switch = {"if": X, "to": Y}`:

- `X` ∈ active aliases ∪ `"tie"`; `Y` ∈ active aliases ∪ `"skip"`. Self-votes are legal.
- At `switchTick`, a **single snapshot** `T` of the tally as it stood at `switchTick − 1` is taken. For
  each seat with a non-null `switch`: if `X` is an alias, the condition holds iff `X` is the **unique**
  cog with the strictly highest count in `T`; if `X == "tie"`, it holds iff no cog has a strictly
  highest count (the all-`skip` case included). Every matching seat's vote changes to `Y`
  **simultaneously**, against the same snapshot.
- Only seats whose vote actually changed emit a `vote` row with `phase: "switch"`.

This is the whole reason the meeting costs **one** LLM batch instead of two. A genuine two-round
discussion would double the batch count and blow the 720 s budget (`## Decisions` arithmetic); a single
conditional buys real, visible, reactive vote movement for zero extra requests, and it is expressible
in one JSON field.

**Chat, in the default variant.** Each meeting gives each seat one `say` line (≤ 90 characters),
composed before it sees anyone else's and revealed to everyone at `sayTick`. The full transcript of
every meeting so far is in every later observation, so a claim made at meeting 3 can be answered at
meeting 4 or punished by a vote switch at meeting 3's `switchTick`. That is a statement round per
meeting, not a conversation, and the reason is stated rather than hidden: the budget buys one batch per
meeting. In the no-talk variants `say` is not requested, is rejected if sent, and never reaches the
replay — there is no side channel at all.

**Tally rule (exact).** At `resolveTick`, let `m` = the highest vote count among **aliases** and `s` =
the number of `skip` votes. Every active seat casts exactly one vote (a seat whose reply failed casts
`skip`; frozen and ejected seats cast nothing).

- If `m > s` **and** exactly one alias has count `m` → that cog is **ejected**:
  `eject {t, target, tally, outcome: "plurality"}`.
- If `m > s` and two or more aliases tie at `m` → nobody is ejected, `outcome: "tie"`.
- If `s >= m` → nobody is ejected, `outcome: "skip"`.

An **ejected** cog is removed from the map entirely (no body, no evidence — it walked out the airlock);
its carried gems are lost.

### What a cog can do — jobs, plans, and the per-tick vocabulary

Each cog occupies one cell and emits exactly one action per tick from this vocabulary:

`move_n` · `move_e` · `move_s` · `move_w` · `mine` · `deposit` · `freeze` · `face_n` · `face_e` ·
`face_s` · `face_w` · `wait`

`move_*` is legal only every `moveCooldown = 2` ticks and only into a floor or grate cell not occupied
by another **active** cog; an illegal move degrades to `wait`.

**Where the per-tick actions come from.** No LLM authors 3000 ticks of movement. At each decision point
(episode start, and the open of every meeting) a seat submits a **plan of up to `planSteps = 3` jobs**,
and a deterministic **kernel** turns that plan into the per-tick action stream. Steps run in order; when
a step completes the next begins; when the plan is exhausted the **last step repeats** until the next
decision point. The sim's policy interface is per-tick grid actions exactly as a paintbot-lineage game
should be; the LLM chooses the jobs, the kernel walks the station.

BFS is over walkable cells only, neighbour expansion in **N, E, S, W** order, other cogs are not
obstacles for path *planning* (only for the move itself), ties between equidistant targets break by
`(row, col)` ascending. Paths are unique and deterministic.

**Crew jobs** (six; the impostor may use all of them, to blend):

1. `mine at:<seam>` — BFS to the nearest walkable cell orthogonally adjacent to that seam, then `mine`
   every tick, facing the seam. Completes when hands are full or the seam is empty. If the seam is empty
   on arrival, the step completes immediately.
2. `deposit` — BFS to the nearest grate cell, then `deposit` every tick facing the grate centre.
   Completes when hands are empty.
3. `watch who:<alias>` — BFS to the nearest walkable cell whose distance to that cog's **last known
   cell** is in `3..5`, then `wait`, **facing the quadrant containing that cog's last known cell**,
   re-targeting every tick as the target moves. Never mines. This is the deliberate act of buying
   vision at the cost of throughput.
4. `patrol room:<room>` — BFS to that room's doorway, then walk its four waypoint corners in a fixed
   cycle, facing the direction of travel. Sweeps a room for bodies and for who is in it.
5. `guard` — BFS to the nearest grate cell, then `wait`, rotating facing one quadrant clockwise every
   `sweepTicks = 8`. The only job that sees in every direction over time; it also parks you where you
   can audit the deposit counter.
6. `hold` — `wait` in place, facing unchanged.

**Impostor-only jobs** (three more):

7. `hunt who:<alias>` — BFS toward that cog's last known cell; when the freeze is legal **and no third
   active cog is inside the impostor's own FOV**, fire. Otherwise keep closing. The safety check uses
   only what the impostor can see, which — because vision is a cone — is *not* the same as "no witness":
   somebody behind it sees it. That fallibility is the point.
8. `strike who:<alias>` — as `hunt`, but fires the instant the freeze is legal, witnesses or not.
9. `lurk room:<room>` — BFS to the room's far corner from the doorway, then `wait` facing the doorway.
   Waits for a lone crewmate to walk in.

A plan step naming a seam/room/alias that does not exist, or an impostor-only job in a crew reply, is an
**invalid reply** (§Reply schema) — retried once, then the scripted fallback.

### Turns, ticks, and the exact resolution order

One episode is at most `maxTicks = 3000` ticks (the idea's number). Playback is **24 fps**
(`tickHz = 24`), so a 1000-tick game is ~42 s of video and a full 3000-tick game is 125 s. **The sim is
not wall-clock paced**: ticks advance as fast as they compute, and the only wall-clock floor in the
whole game is `minBatchSeconds` (`## Decisions`), which exists solely to respect the Bedrock sidecar's
per-episode rate cap.

Every **play** tick runs these twelve steps in this order. Within a step, seats resolve in **ascending
slot order**, and seams in `S1..S6` order. All reads inside a step use the state as it stood at the
start of that step unless the step says otherwise.

1. **Timers.** Decrement every move cooldown and the impostor's `freezeCooldown`; advance each seam's
   regrow counter and, on reaching `seamRegrowTicks`, add one gem up to `seamCapacity`, reset the
   counter and emit `seam`.
2. **Kernel intent.** Each active cog's kernel computes this tick's action from its current plan step.
   A cog whose move cooldown is still running emits `wait` instead of a move. Frozen and ejected cogs
   emit nothing.
3. **Freeze resolves** (impostor only, at most one). Legality exactly as §The freeze beam. On success:
   victim → `frozen`, cooldown set, `freeze` emitted.
4. **Witness check.** Exactly as §The witness trigger, using start-of-tick positions and facings.
   Emits `witness` rows and, if `W` is non-empty, `caught`, and arms an immediate meeting for step 11.
5. **Deposits resolve**, slot order. Crew → `deposits += 1`, `deposit` emitted. Impostor → gem
   destroyed, counter unmoved, `fakedeposit` emitted with `seenBy`.
6. **Mining resolves**, slot order. `mineProgress` advances; at `mineTicks` a gem transfers and `mine`
   is emitted.
7. **Moves resolve**, slot order, against the **live** board: a move into a cell a lower-numbered seat
   has already taken this tick fails and degrades to `wait`. A successful move sets `facing` to the
   direction of travel and resets the move cooldown.
8. **Facing (non-movers).** Any cog that did not move this tick sets `facing` per its job rule (`mine`
   → the seam; `deposit` → the grate centre; `watch` → the target's last known cell; `guard` → rotate
   one quadrant every `sweepTicks`; `patrol` → direction of travel, held; `lurk` → the doorway; `hold`
   → unchanged). An explicit `face_*` from the kernel overrides.
9. **FOV and memory.** Recompute each active cog's visible object set; update that seat's private
   memory — `lastSeen[alias] = {t, cell, doing}`, `bodies[]` (`{alias, cell, firstSeenTick}` for every
   frozen cog it has ever seen), `togetherTicks[alias]` (ticks that cog has been in view, the alibi
   counter), and `youWitnessed[]`.
10. **Win check**, in this fixed order: (a) `deposits >= depositTarget` → **crew win**,
    `ending: "crew_deposits"`; (b) the impostor is ejected → **crew win**,
    `ending: "impostor_ejected"` (evaluated at step M5 of a meeting, listed here for completeness);
    (c) active crew `<= 1` → **impostor win**, `ending: "impostor_isolation"`; (d) `t == maxTicks` →
    **tie**, `ending: "timeout"`.
11. **Meeting trigger.** If step 4 armed a witnessed meeting → open a meeting at `t+1` with
    `cause: "witness"`. Else decrement the cadence timer; at 0 → open a meeting at `t+1` with
    `cause: "cadence"`.
12. **Record.** Append this tick's frame, its events and the series rows to the replay.

**Meeting ticks** run their own order (M1–M6, §Meetings). During a meeting there is no movement, no
mining, no depositing and no freezing; frames are still recorded every tick with `state = meeting`, so
the vote board animates.

### Scoring — zero-sum, ±4 against ±1; higher is better

The idea pins the motive ("zero-sum hidden-role") and the tie ("3000-tick timeout is a 0-0 tie"). The
formula, decided here, is paintbot's own four-way ante shape (`+4` to the winner, `−1` to each loser),
which is exactly right for 4-vs-1:

```
winner = "crew"     -> scores[i] = +1 for each of the 4 crew seats,  -4 for the impostor seat
winner = "impostor" -> scores[i] = -1 for each of the 4 crew seats,  +4 for the impostor seat
winner = "none"     -> scores[i] =  0 for all five seats
```

- **The sum is exactly 0 in every case** (4 × 1 − 4 = 0). Zero-sum, as the idea requires.
- **Sign: higher is better.** **The league ranks by `results.scores`** (the platform's mean over
  episodes). Nothing else is ranked. Deposits, freezes, witnessed freezes, ejections and meeting counts
  are reported for the viewer and for analysis only.
- Crew who were frozen or ejected **still receive the crew result**. It is a team game: being frozen is
  the impostor's success, not the victim's failure, and scoring the victim separately would reward crew
  for hiding in the hub instead of mining.
- `results.win[i] = (scores[i] > 0)` — false for everyone on a tie.
- **There is no partial credit for deposits.** A crew side that reaches 31 of 32 and loses scores −1,
  same as a side that reaches 3. This is the idea's pin ("0-0 tie", zero-sum) taken at its word: the
  race is the game, and a deposit-proportional consolation would let a crew policy farm score by
  ignoring the impostor entirely.

Because the impostor slot is redrawn every episode from the seed, a policy plays both roles across a
league season and its mean score is a fair rating of both halves of its play.

### End conditions and `results.reason`

The episode ends at the **first** of these:

| condition | `results.reason` | `results.ending` | `winner` | scores |
|---|---|---|---|---|
| `deposits >= 32` | `complete` | `crew_deposits` | `crew` | +1 ×4 / −4 |
| the impostor is ejected at a meeting | `complete` | `impostor_ejected` | `crew` | +1 ×4 / −4 |
| active crew `<= 1` (frozen and/or ejected) | `complete` | `impostor_isolation` | `impostor` | −1 ×4 / +4 |
| tick 3000 reached | `complete` | `timeout` | `none` | all 0 |
| wall clock passes the play deadline (0.6 × `episodeTimeoutSeconds` = **720 s**) | `deadline` | `deadline` | `none` | all 0 |
| no seat connected within `playerConnectTimeoutSeconds = 120` | `forfeit` | `forfeit` | `none` | all 0 |

Those three — **`complete`, `deadline`, `forfeit`** — are the only legal `results.reason` values, and
**`crew_deposits`, `impostor_ejected`, `impostor_isolation`, `timeout`, `deadline`, `forfeit`** the only
legal `results.ending` values. `timeout` is a *completed game of Hidden Agenda* that ended 0-0, which is
what the idea pins, so it carries `reason: "complete"`; `deadline` is the distinct case where the LLM
transport was slow and the game had to settle early. `deadline` is admissible (phase 60 accepts a
declared `deadline`) but the arithmetic in `## Decisions` is sized so it should not fire. A seat that
never connects does **not** end the episode: it plays `miner` and the game runs.

### Throughput arithmetic, and the feasibility gates

These are **design targets derived from the constants above, not measurements.** The enforcement is
`tests/test_feasibility.nim`, not this table (ecos, 2026-08-23, shipped a note whose "measured" oracle
was a hypothesis the builder had to repair).

- Crew round trip, cheap gallery: 6 cells out + 6 back at `moveCooldown = 2` = 24 ticks, plus
  2 × `mineTicks` = 144, plus 2 deposit ticks ≈ **170 ticks for 2 deposits**. Expensive vault:
  17 + 17 cells = 68 ticks travel ≈ **214 ticks for 2 deposits**. Blended ≈ 95 ticks per deposit per
  crew.
- 4 crew in parallel: 32 deposits ≈ **760 play ticks**, plus ~4 meetings (100–240 ticks) ⇒ **a clean,
  unmolested crew wins around tick 900–1050.**
- Impostor: 3 removals at `freezeCooldownTicks = 220` ⇒ ≥ 440 ticks of cooldown, plus ~30–60 ticks of
  travel per hunt ⇒ **a clean impostor wins around tick 650–950.** Mis-ejections by the crew shorten
  that; a witnessed freeze usually ends it the other way.
- Gem supply: 18 standing + 1 gem / 20 ticks global regrowth against 1 gem / 24 ticks of demand — never
  binding on its own, but the *cheap* seams (2 of 6) run dry within ~400 ticks of four-crew pressure,
  which is what pushes crew into the vaults alone.
- Meetings: bounded by the 200-tick cadence reset plus ≤ 3 witnessed ⇒ ≤ `ceil(3000 / 225) + 3 = 17`
  meetings in the no-talk shape, ≤ `ceil(3000 / 260) + 3 = 15` in the chat shape. Plus the opening
  decision = **≤ 18 decision batches**; `maxDecisionBatches = 20` caps it with headroom.
- Sim cost: 3000 ticks × (5 BFS over 249 cells + ~75 `los` walks) ≈ **3–6 s** for a whole episode.

The gates `tests/test_feasibility.nim` enforces, over seeds 1..16 on **all three** variants:

- **(a) The baselines play the game.** All-`miner`: ≥ 14/16 seeds end `complete` with `ending` in
  `{crew_deposits, impostor_ejected, impostor_isolation}`; ≤ 2/16 end `timeout`. This is what makes
  certification, `docker-smoke` and all-filler league episodes finish and look like Hidden Agenda.
- **(b) Both sides can win.** All-`miner` crew-win rate on the default variant is in **0.30 .. 0.70**.
- **(c) Recklessness is punished.** With `lurker` pinned as the impostor and `miner` crew: mean
  witnessed freezes per episode ≥ 0.5 **and** impostor win rate ≤ 0.35.
- **(d) Watching has a real cost.** A test-only `watcher` crew kernel (every crew seat `watch`es its
  nearest neighbour and nobody mines) loses to a `miner` impostor in ≥ 0.85 of seeds — mining must be
  the thing that wins, or the game degenerates into five cogs staring at each other.
- **(e) The evidence channel actually carries.** Over the episodes in (a) that contain ≥ 1 witnessed
  freeze, the meeting immediately following ejects the impostor in ≥ 0.60 of cases with `miner` crew,
  **in the no-talk variant** — i.e. spatial evidence alone is sufficient to convict.
- **(f) No slot bias.** Over seeds 1..64 the drawn impostor slot is within ±20 % of uniform, and the
  crew-win rate with the impostor pinned to each of the five slots in turn varies by ≤ 10 %.
- **(g) Budget.** Over seeds 1..16 on every variant, the decision-batch count never exceeds
  `maxDecisionBatches` and the meeting count never exceeds 18.

**If a gate fails, repair constants in this order and re-run — no design bounce is needed:**
(b) `freezeCooldownTicks` 220 → 260 if the impostor is too strong, 220 → 180 if too weak;
(a) `mineTicks` 72 → 60, then `seamRegrowTicks` 120 → 90;
(c) `visionRadius` 8 → 9;
(d) `mineTicks` 72 → 84;
(e) `awarenessRadius` 2 → 3;
(f) fix the spawn rotation or the `rngRole` sub-stream, never the reward.
**`depositTarget = 32`, `maxTicks = 3000`, `carryCap = 2`, `meetingCadenceTicks = 200`,
`meetingTicks = 25` in the no-talk shape and `num_agents = 5` are pinned by the idea and are never
tuning knobs.** Any change to a non-pinned constant re-runs the oracle. **That test is the enforcement,
not this table.**

---

## Decisions: LLM with scripted fallback

Both policies ship in the **same image** from day one, env-switched, exactly like bullwhip:
`PLAYER_PROMPT="<strategy text>"` for an LLM policy, `PLAYER_SCRIPTED=miner|lurker` for a scripted
baseline. **A policy is a prompt.** `src/hidden_agenda_player.nim` (a fork of
`cogame-bullwhip/src/bullwhip_player.nim`) is one thin process that connects, sends
`{"type":"prompt","prompt":…,"scripted":…}` and then only listens. All decision-making happens in the
**game** container (`src/hidden_agenda/llm.nim`, forked from `cogame-bullwhip/src/bullwhip/llm.nim`) —
which is what makes one parallel batch per decision point possible, and is why the coworld secret must
be declared on the *game* runnable (hive, 2026-08-23).

### Cadence and the wall-clock budget

There are exactly two kinds of decision point: **the episode opening** (plan only) and **every meeting
open** (plan + vote + switch + say). At each one the game issues **every eligible seat's request as ONE
parallel batch** (`curly.makeRequests`, bullwhip's `decideAll`) — never sequentially. Decisions are
**simultaneous**: no seat sees another seat's plan, vote or `say` before submitting its own. Frozen and
ejected seats are **not** in the batch (they cannot act and cannot vote), so batches shrink from 5
requests to 4 and then 3 as the game goes on.

```
per batch:     <= 5 requests, llmTimeoutSeconds = 14
worst case:    14 s (batch) + 14 s (one retry batch)                =  28 s
max batches:   maxDecisionBatches = 20  (1 opening + <= 17 meetings, capped)
20 batches:    20 x 28 s                                            = 560 s
+ connect:     playerConnectTimeoutSeconds ceiling on the wait      <= 120 s
+ sim:         3000 ticks x ~1.5 ms                                 ~   5 s
total worst:   ~685 s   <   720 s   ( = 0.6 x episodeTimeoutSeconds 1200 )
typical:       ~6 meetings x max(minBatchSeconds 14, ~7 s batch)    ~  90 s
```

`minBatchSeconds = 14` floors the spacing between batch **starts**, so the episode issues at most
5 requests / 14 s ≈ **21 requests per minute** (≈ 26 rpm on the rare turn that also needs a retry
batch), under the Bedrock sidecar's **30 rpm per-episode** ceiling that bit cogame-raid. Requests per
episode: ≤ 100, plus ≤ 100 retries.

`maxDecisionBatches = 20` is a hard cap: after the 20th batch, every subsequent meeting reuses each
seat's **previous** vote/switch/plan, recorded on the `order` event as `"source":"budget"`. It cannot be
reached by the arithmetic above (≤ 18), and exists so no rules change can silently make the game
unbounded.

The **play deadline** (0.6 × `episodeTimeoutSeconds`; the game container is **not** given
`COWORLD_TIMEOUT_SECONDS`, so 1200 is assumed unless that env var is present) is tested **before every
batch and at every meeting open**; hitting it calls `endEarly()` and settles with `reason: "deadline"`,
`ending: "deadline"`, all scores 0.

### The observation each seat gets

Sent as the `state` frame at every decision point (and once more at episode end), and rendered into the
user prompt. Every number below is visible to that seat; **nothing else is**.

**Crew seat:**

```json
{"type":"state","protocol":"hidden_agenda.player.v1","slot":1,"role":"crew","name":"BLUE",
 "tick":812,"maxTicks":3000,"decision":4,"cause":"witness","phase":"meeting","chat":false,
 "you":{"cell":[13,15],"facing":"N","carrying":1,"carryCap":2,"state":"active",
        "mined":6,"deposited":5,"lastPlan":[{"job":"mine","at":"S5"},{"job":"deposit"}]},
 "station":{"deposits":21,"depositTarget":32,"map":"vault","cols":27,"rows":19,
            "rooms":["NW","N","NE","SW","S","SE","HUB"],
            "seams":[{"id":"S1","room":"NW","cell":[2,2]},{"id":"S2","room":"N","cell":[13,2]},
                     {"id":"S3","room":"NE","cell":[24,2]},{"id":"S4","room":"SW","cell":[2,16]},
                     {"id":"S5","room":"S","cell":[13,16]},{"id":"S6","room":"SE","cell":[24,16]}],
            "grate":[[12,8],[13,8],[14,8],[12,9],[13,9],[14,9],[12,10],[13,10],[14,10]]},
 "roster":[{"alias":"RED","state":"active"},{"alias":"BLUE","state":"active"},
           {"alias":"GREEN","state":"frozen"},{"alias":"YELLOW","state":"active"},
           {"alias":"PINK","state":"active"}],
 "inView":[{"alias":"PINK","cell":[13,14],"facing":"S","doing":"walking","carrying":1}],
 "lastSeen":{"RED":{"t":640,"cell":[4,3],"doing":"mining","room":"NW"},
             "YELLOW":{"t":790,"cell":[13,9],"doing":"depositing","room":"HUB"},
             "GREEN":{"t":806,"cell":[13,16],"doing":"frozen","room":"S"},
             "PINK":{"t":812,"cell":[13,14],"doing":"walking","room":"S"}},
 "togetherTicks":{"RED":118,"GREEN":204,"YELLOW":96,"PINK":41},
 "bodies":[{"alias":"GREEN","cell":[13,16],"room":"S","firstSeenTick":806}],
 "youWitnessed":[{"t":806,"freezer":"PINK","victim":"GREEN","cell":[13,16],
                  "sawFreezer":true,"sawVictim":true}],
 "seamsSeen":[{"id":"S5","gems":1,"t":806}],
 "meetings":[{"n":3,"t":600,"cause":"cadence",
              "votes":{"RED":"skip","BLUE":"skip","GREEN":"YELLOW","YELLOW":"skip","PINK":"YELLOW"},
              "switched":{},"outcome":"skip","ejected":null,"say":{}}],
 "vision":{"visionRadius":8,"awarenessRadius":2,"cone":"90 degrees on your facing",
           "facingRule":"you face where you walk; mining faces the seam; watch faces your target; guard sweeps"},
 "rules":{"role":"you are CREW. Exactly ONE of the other four cogs is the impostor.",
          "win":"crew win at 32 deposits or by ejecting the impostor; the impostor wins when only one crewmate is left; tick 3000 is a 0-0 tie",
          "freeze":"the impostor freezes at range 2 with line of sight, then cannot freeze again for 220 ticks; frozen crew stay on the map and never act again",
          "meeting":"meetings open every 200 ticks and IMMEDIATELY when a freeze happens inside someone's field of view",
          "vote":"the cog with strictly the most votes is ejected; a tie or a skip majority ejects nobody",
          "deposit":"only a crewmate's deposit moves the counter",
          "channel":"there is NO chat in this variant. Your vote is your only signal.",
          "mineTicks":72,"carryCap":2,"moveCooldown":2,"freezeRange":2}}
```

- **Visible to a crew seat:** its own cell/facing/carry/state and counters; the full **static** map
  (walls, seams, rooms, grate — the crew work here, they know the floor plan); the **public deposit
  counter**; the public roster of who is `active` / `frozen` / `ejected`; every cog currently **in its
  own FOV** with cell, facing, what it is doing and whether it is carrying; its **own memory** of
  everyone else (`lastSeen`, `togetherTicks`, `bodies`, `seamsSeen`); its own `youWitnessed[]`; the
  **complete public meeting history** (every vote, every switch, every outcome — votes are public by
  construction) and, in the chat variant, the full `say` transcript; its own `notes` from last time; and
  the rules.
- **Hidden from a crew seat:** every other seat's **role**, plan, `hunch` and `notes`; the position,
  facing and activity of any cog **not currently in its FOV** (it gets only its own remembered
  `lastSeen`); the gem count of any seam it cannot see; the freeze cooldown; the seed; the impostor
  slot; and anything about the league or the other seats' policies.

**Impostor seat:** the same blocks, plus in `you`:

```json
 "you":{"cell":[13,14],"facing":"S","carrying":1,"carryCap":2,"state":"active",
        "freezeCooldown":0,"freezeCooldownTicks":220,"freezeRange":2,
        "freezes":1,"fakeDeposits":2,"lastFakeDepositSeenBy":["YELLOW"],
        "canFreezeNow":["GREEN"],
        "lastPlan":[{"job":"lurk","room":"S"},{"job":"hunt","who":"GREEN"}]},
```

and `rules.role` reads *"you are the IMPOSTOR. The other four cogs are all crew. Your deposits are
destroyed and never move the counter."* `canFreezeNow` is the precomputed set of legal targets right
now — precomputing the legal choice set in the observation is what halved formal-output fallbacks in
escrow (2026-08-23), and it is computed by the **same predicate** the sim's legality check applies.

- **Visible to the impostor and to nobody else:** its cooldown, its own freeze/fake-deposit counters,
  `lastFakeDepositSeenBy`, and `canFreezeNow`.
- **Hidden from the impostor:** who can currently see *it* (that is the risk it is taking), everything
  outside its own FOV, and every other seat's plan/`hunch`/`notes`.

**Frozen or ejected seat:** receives a `state` frame with `you.state = "frozen"|"ejected"`,
`canAct: false`, `canVote: false`, the public roster, the deposit counter and the meeting history —
and is **not** included in any decision batch. Its socket stays open until `final`.

### The reply schema

The model must answer with exactly one JSON object whose first character is `{`.

```json
{"plan":[{"job":"mine","at":"S5"},{"job":"deposit"},{"job":"watch","who":"PINK"}],
 "vote":"PINK","switch":{"if":"YELLOW","to":"PINK"},
 "say":"pink was standing over green in the south gallery",
 "hunch":"pink froze green at 806 and I saw it","notes":"red has been in NW since 640"}
```

| field | type | cap / range | on violation |
|---|---|---|---|
| `plan` | array of step objects | **1..3** steps | missing, empty, > 3 steps, or not an array → **invalid reply** |
| `plan[].job` | string enum | crew: `mine` \| `deposit` \| `watch` \| `patrol` \| `guard` \| `hold`. impostor: those six **plus** `hunt` \| `strike` \| `lurk` | missing, or not in **this role's** enum → **invalid reply** |
| `plan[].at` | string enum | `S1`..`S6` | required for `mine`; missing or unknown there → **invalid reply**. Ignored elsewhere. |
| `plan[].who` | string enum | an alias that is `active` **now** | required for `watch`, `hunt`, `strike`; missing, unknown or not active → **invalid reply**. Ignored elsewhere. |
| `plan[].room` | string enum | `NW` \| `N` \| `NE` \| `SW` \| `S` \| `SE` \| `HUB` | required for `patrol`, `lurk`; missing or unknown there → **invalid reply**. Ignored elsewhere. |
| `vote` | string enum | an `active` alias, or `"skip"` | **required at a meeting**; missing or unknown → **invalid reply**. Ignored (and not recorded) at the opening decision. |
| `switch` | object or `null` | `{"if": <active alias> \| "tie", "to": <active alias> \| "skip"}` | absent or `null` = no conditional. Present but malformed, or naming an inactive cog → **invalid reply**. |
| `say` | string | **90 characters** | truncated. **Only in the chat variant**; in a no-talk variant the field is ignored, never recorded and never shown to anyone. |
| `hunch` | string | **80 characters** | truncated |
| `notes` | string | **240 characters** | truncated |

Extra keys are ignored. **Truncation is on rune boundaries**, never bytes: `cleanText(text, limit)` =
`strip` → if `runeLen > limit`, `runeSubStr(0, limit - 1) & "…"` (bullwhip's `cleanText`; a byte cut put
invalid UTF-8 into a replay and only a strict parser found it — bullwhip, 2026-08-22). Newlines in
`say` and `hunch` become spaces. The same rune-safe truncation applies to **every** string that reaches
the replay, including the recorded LLM error text (capped at 200 characters) and the echoed
`PLAYER_PROMPT` (capped at 4000).

**`hunch` is spectator-only; `notes` is private; `say` is the only field that ever reaches another
seat, and only in the chat variant.** That is how "no-talk" is enforced mechanically rather than by
convention, and `tests/test_noleak.nim` asserts that no seat's `hunch`/`notes`/`plan`/`role` string ever
appears in another seat's `state` frame bytes, and that `say` never appears in a no-talk episode's bytes
at all.

### Prompts

**System prompt** (composed by the game, per seat, per decision): the seat's alias in capitals and its
**role**, with the flat statement of how many impostors there are and that the seat cannot see anyone
else's role; the station and the action vocabulary; the plan model ("you choose up to three jobs; a
kernel walks them for you, tick by tick, until the next meeting"); the **vision model spelled out** (a
90° cone on your facing to 8 cells, 2 cells in every direction, walls and seams block it — *somebody
behind you can see you and you cannot see them*); the freeze rule with range and cooldown; the meeting
rules including **both** triggers; the tally rule; the fact that only a crewmate's deposit moves the
counter; the statement that the other seats are different policies deciding **simultaneously**, that
`hunch` is seen only by spectators and `notes` only by you, and — in a no-talk variant — that **there is
no chat and the vote is the only signal**; and the output contract, ending:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

(Bedrock/Haiku answers prose-first without that sentence — playbook §Phase 1.)

**User prompt:** the observation rendered compactly — a station line (`DEPOSITS 21/32 · TICK 812/3000 ·
MEETING 4 (witness)`), the roster with states, an **in-view table** (`alias | cell | facing | doing |
carrying`), a **last-seen table** (`alias | last seen tick | room | doing | ticks together`), the bodies
line, the `YOU SAW` block if `youWitnessed` is non-empty, the seam table, the **meeting history table**
(one row per meeting: `n | cause | votes | switched | outcome`), the chat transcript when the variant
has one, `YOUR NOTES FROM LAST TIME`, then the operator block:

> GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
> requested format):
> `<PLAYER_PROMPT>`

then a one-line restatement of the reply shape with the legal enum values **for this role and this
moment** — the active aliases, the seam ids, the room ids, and (for the impostor) `canFreezeNow`.

**Transport:** bullwhip's ladder, haiku-only (raid, 2026-08-23 — the sonnet fallback times out on every
sidecar call and turns one throttle into a cascade):
`bedrockModelIds() = ["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`, `BEDROCK_MODEL` overrides.
`maxOutputTokens = 900` (not 400 — "cut off at max_tokens"). No `output_config.effort` — Haiku 4.5 400s
on it. Credentials in order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` /
`AWS_BEARER_TOKEN_BEDROCK`) → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`. With none, the client
disables itself immediately and every seat plays `miner` — which is what keeps offline certification
green and deterministic.

**Champion prompts** (phase 50 uploads these; **both are `PLAYER_PROMPT` policies**, and both must
cover **both roles**, because the ladder seats a policy in either):

- `hidden-agenda-sleuth` (champion #1, daveey): *"Whichever role you draw, this game is won by
  controlling who can see what. AS CREW: your job is deposits first and evidence second — 32 deposits
  wins outright, so never spend more than one plan in a row on `watch` or `guard`. Work the galleries
  (S2, S5) while they hold gems and take a vault seam only when someone else is heading the same way;
  a crewmate alone in a vault is a free freeze. Every meeting, reason from three things in this order:
  (1) anything in YOU SAW — a witnessed freeze is proof, vote it and never switch off it; (2) who was
  NOT seen by anyone for a long stretch that ends with a body appearing — cross the last-seen table
  against where the body lies; (3) who was at the grate when the counter did not move. If you have
  nothing, vote `skip` rather than lynching a random crewmate: a wrong ejection is a free kill for the
  impostor. Set `switch` to `{"if":"<you>","to":"<your best suspect>"}` so a bandwagon on you does not
  end your game unanswered. AS IMPOSTOR: be patient and be boring. Mine and deposit like everyone else,
  even though your gems vanish — but never fake a deposit while anything is in view. Use `lurk` in a
  vault whose seam still has gems and let a crewmate walk to you; `hunt` only when your own view is
  empty, and remember your view is a cone: check that nobody was walking behind you two seconds ago.
  You need three removals and one of them can come from the vote — spend your meetings building a
  plausible, specific story about someone else's gaps, and vote with the majority, never first."*
- `hidden-agenda-shadow` (champion #2, daveey-1): *"Play the clock. AS CREW: count it out — a gallery
  trip is about 170 ticks for two deposits and there are only four of you, so the crew wins near tick
  1000 if nobody wastes a plan. Chain `mine` then `deposit` in every plan and put a third step on
  `watch` only when you are already walking past that cog. Pair up: name the cog you can see in your
  `watch` step, because two crew in one room cannot be frozen quietly and you both get an alibi worth
  citing. At meetings, trust `togetherTicks` above accusation: the cog you have personally been beside
  for hundreds of ticks is almost certainly clean, so say so and spend your vote on the one nobody can
  account for. Do not switch your vote unless the tally is about to land on someone you know is clean.
  AS IMPOSTOR: kill the tempo, not the crew. Freeze the cog that is closest to the grate with a full
  hand — you delete two deposits and 150 ticks of work with one shot. Then walk somewhere public and be
  seen. Between freezes, use `guard` at the grate: it sweeps, it looks industrious, and it puts you
  where you can watch who leaves alone. If you are ever accused with real evidence, do not argue with
  the tally — set `switch` to move your vote onto the second-place suspect and hope for a tie, because
  a tie ejects nobody."*

### Scripted baselines (both fieldable, both league fillers, both role-aware)

One baseline plays either role, deciding purely from its own observation at each decision point (no
shared state, no access to anything a policy could not see).

**`miner`** — the working baseline, and the fallback every failed LLM decision lands on.

*As crew:*
1. Plan step 1: if `carrying < carryCap`, `{"job":"mine","at":S}` where `S` is the seam minimising
   `walkDistance(me, S) + 40 * (S.gems == 0 as last seen)`, ties by seam id. Else `{"job":"deposit"}`.
2. Plan step 2: `{"job":"deposit"}` (or, if step 1 was already `deposit`, `{"job":"mine","at":S}` for the
   next-best seam).
3. Plan step 3: `{"job":"watch","who":X}` where `X` is the active cog with the **largest** `t - lastSeen[X].t`,
   ties by alias order.
4. `vote`: the maximum of a deterministic suspicion score over active cogs other than itself —
   `susp(x) = 20*witnessedFreezing(x) + 8*witnessedVictimSideOnly(x) + 6*sawFakeDeposit(x)
   + 3*(bodyFoundInRoom(x_lastSeenRoom)) + 1*floor((t - lastSeen[x].t) / 100)`
   — ties by alias order. If the best score is `< 6`, vote `"skip"`.
5. `switch`: `{"if": <own alias>, "to": <the second-highest suspect, else "skip">}`.
6. `hunch` = `"susp <top> <score>"`; `notes` = `""`; `say` (chat variant) =
   `"<top alias> unseen <n> ticks"` or `"nothing solid"`.

*As impostor:*
1. If `freezeCooldown == 0` and `canFreezeNow` is non-empty and **no third cog is in view**:
   `{"job":"hunt","who": canFreezeNow[0]}`.
2. Else if `freezeCooldown == 0`: `{"job":"lurk","room": the room of the active cog with the largest
   t - lastSeen[x].t}` then `{"job":"hunt","who": that cog}`.
3. Else `{"job":"mine","at": nearest seam}` then `{"job":"deposit"}` — **but a `deposit` step is
   replaced by `guard` whenever any cog was in view at the moment of planning**, so it never
   fake-deposits in front of an audience.
4. `vote`: bandwagon — the active cog (other than itself) with the most votes in the **previous**
   meeting, else the crew cog with the largest `t - lastSeen[x].t`, else `"skip"`.
5. `switch`: `{"if": <own alias>, "to": <the cog with the second-most votes last meeting, else "skip">}`.

**`lurker`** — the foil, and the second league filler.

*As crew:* mines **one fixed seam for the whole episode** (the nearest at tick 0), never `watch`es,
never `guard`s, and votes `"skip"` unless it personally witnessed a freeze, in which case it votes the
freezer and never switches. Head-down crew: high throughput, no situational awareness.
*As impostor:* `strike` — closes on the nearest active crew cog and fires the instant the freeze is
legal, witnesses or not. It is loud, it gets caught, and that is deliberate: it is what guarantees the
all-scripted certification and `docker-smoke` replays contain a **witnessed freeze and a `CAUGHT!`
banner**, so the game's headline chrome is exercised by CI rather than only in production.

Every field either baseline emits is inside its declared enum **for its role and for the current
active roster** by construction, asserted in `tests/test_baseline.nim`.

### Degrade, never hang

- Batch timeout `llmTimeoutSeconds = 14`. On transport error, non-2xx, refusal, `max_tokens` before any
  `{`, unparseable JSON, or any **invalid reply** in the table above, that seat alone is retried **once**
  in the same decision point's retry batch, with the appended hint *"Your previous reply was invalid.
  Respond with ONLY the requested JSON object, using one of the listed job names, a seam id from the
  list, an alias that is active right now, and a vote that is an active alias or the word skip."*
- Still failing → that seat plays the **`miner` decision** for that decision point (plan **and** vote),
  logged as `hidden-agenda llm: seat N falling back to scripted decision` and recorded on the `order`
  event as `"source":"fallback"`. `decideAll` never raises; the episode always advances.
- 401/403 disables the client for the rest of the episode (every seat scripted from then on); 429 is
  logged and the seat is retried at the next decision point.
- A seat that never connected, or whose socket dies mid-episode, plays `miner` for the rest of the
  episode. The episode never waits on a socket beyond `playerConnectTimeoutSeconds = 120` at the start
  and never blocks on one mid-episode.
- **The episode settles early rather than overrunning.** The play deadline is checked before every batch
  and at every meeting open; `endEarly()` writes `reason: "deadline"`, `ending: "deadline"`, all scores
  0, then the artifacts. `maxDecisionBatches = 20` is a second, independent bound. As cogame-lantern
  taught, `/healthz` and `/global` keep answering for `shutdownGraceSeconds = 20` before `quit(0)`,
  because hosted certification pings the global websocket **after** the player pods start.

---

## Sim module

New code lives in `src/hidden_agenda/`, mirroring paintbot's split (`src/ctf/`). What is forked, what is
kept and what is deleted — by path:

| paintbot path | hidden-agenda | note |
|---|---|---|
| `src/ctf/sim_types.nim` | `src/hidden_agenda/sim_types.nim` | fork: `GameVersion`, the flatty wire types, the constants above, `Role`, `CogState`, `Facing`. Field order is sacred, same as paintbot. |
| `src/ctf/sim.nim` | `src/hidden_agenda/sim.nim` | fork: the tick loop and the twelve numbered steps replace the CTF gameplay core; the meeting state machine (M1–M6) is new. |
| `src/ctf/sim_config.nim` | `src/hidden_agenda/sim_config.nim` | fork: `GameConfig` lifecycle + `config.update`; fields = the config schema in `## Packaging`. |
| `src/ctf/sim_state.nim` | `src/hidden_agenda/sim_state.nim` | fork: logging, `gameHash`, event emission, spawn placement, the two RNG sub-streams (`rngWorld`, `rngRole`). |
| `src/ctf/arena.nim` | `src/hidden_agenda/station.nim` | heavily reduced fork: the **fixed** 27 × 19 cell grid loaded from `data/maps/vault.txt`, room/seam/grate tables, the BFS the kernels use, and **`los()` / `visible()`** — the one piece of paintbot's arena that is kept and adapted, from its map LOS code (`tests/test_map_los.nim`, `test_fov.nim` are the behavioural reference). The terrain generator, `mapSpec`, symmetry machinery, pixel queries and `map_pool` are **deleted** — one authored map. |
| `src/ctf/global.nim` | `src/hidden_agenda/global.nim` | fork, heavily reduced: keep the sprite-protocol emitter, layer/object pooling, the chrome `TextMessage` smuggling and `boardRenderScaleFor`. **Delete** first-person PiP, rig art, gun/grenade/spray/shield/barrier families, endzone bakes, perks and handicaps. **Keep** the fog/vision-cone drawing primitives — this game needs them. |
| `src/ctf/broadcast.nim` | `src/hidden_agenda/broadcast.nim` | fork: `BroadcastTracker` + `buildStateJson` keep their shape; `teams` becomes `crew` / `impostor`, `roster` the five cogs, `lead` the race series, plus the appended `agenda` block (`## Viewer`). |
| `src/ctf/events.nim` | `src/hidden_agenda/events.nim` | fork: the event vocabulary below (same `jsonRow` / `eventsJsonl` shape and the same "live emission and re-simulation must be byte-identical" rule). |
| `src/ctf/replays.nim`, `src/ctf/replay_runtime.nim` | `src/hidden_agenda/replays.nim` | rewritten: Hidden Agenda records **state frames**, not inputs (below). |
| `src/ctf/server.nim` | `src/hidden_agenda/server.nim` | fork of the route/artifact/shutdown skeleton; the player protocol becomes bullwhip's JSON frames. |
| `src/ctf/labels.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `roster.nim`, `paint.nim`, `directives.nim`, `control.nim`, `decide.nim`, `baselines.nim` | — | deleted. No articulated rigs, no perks, no paint, no generated terrain, no CTF directives. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | kept, forked | still emits `window.CTF_WIRE={…}`. **The global keeps its name**: `client/chrome_common.js` reads `window.CTF_WIRE` at its line 72 and that file ships **byte-for-byte**, so renaming the global would force a byte change in a file that must not change. |
| `tools/` probes, `caos*`, `arena/` wit bindings, `client/league_replayer.html`, `tools/map_editor*`, `tools/record_*.sh`, `players/baseline/`, `scripts/gen_campaign_maps.py` | — | deleted. **Keep `tools/build_replay_viewer.sh` and `tools/ci/`.** |
| `ctf.nimble` | `hidden_agenda.nimble` | fork: binaries emitted as `/bin/hidden-agenda` and `/bin/hidden-agenda-player` (Nim module names use the underscore, the binaries use the hyphenated slug, via `-o:`). |

**New files:** `src/hidden_agenda/kernel.nim` (all nine jobs + BFS), `src/hidden_agenda/vision.nim`
(`los`, `visible`, quadrant maths, the per-seat memory update), `src/hidden_agenda/meeting.nim` (the
M1–M6 state machine, the switch evaluation and the tally), `src/hidden_agenda/llm.nim` (from
`cogame-bullwhip/src/bullwhip/llm.nim`), `src/hidden_agenda/scripted.nim` (the two role-aware
baselines), `src/hidden_agenda.nim` (entrypoint, forked from `src/ctf.nim`: seed randomisation
**before** `config.update`, same `LegacyFixedSeed` sentinel handling),
`src/hidden_agenda_player.nim` (from `cogame-bullwhip/src/bullwhip_player.nim`).

`tools/build_replay_viewer.sh` is paintbot's with the image tag renamed
(`coworld-hidden-agenda-replay-viewer-build`), the `docker cp` path changed to
`/workspace/hidden_agenda/replay-viewer/dist/.` **and the inherited bug fixed**: `mkdir -p` the output
parent before the containment check, because the hook `cd`s into a parent that `coworld build`
pre-creates and CI does not (ecos, 2026-08-23).

### Event vocabulary (the replay's `events[]`)

One JSON row per event; `t` = tick, `seat` = slot, aliases are strings.

| `k` | fields | when |
|---|---|---|
| `reveal` | `t (=0), seat, alias, role, policy` | five rows at tick 0. **Spectator-side role reveal**; never sent to any seat. |
| `seam` | `t, id, gems` | step 1, a seam regrew |
| `mine` | `t, seat, id, carry` | step 6, a gem was extracted |
| `deposit` | `t, seat, total` | step 5, a **crew** deposit; `total` is the new counter |
| `fakedeposit` | `t, seat, seenBy[]` | step 5, the impostor deposited into the grate and the counter did not move |
| `freeze` | `t, seat, victim, cell, witnesses[]` | step 3 |
| `witness` | `t, witness, freezer, victim, cell, sawFreezer, sawVictim` | step 4, **one row per witness** — the idea's witnessed-freeze trigger log |
| `caught` | `t, freezer, victim, witnesses[]` | step 4, iff the witness set is non-empty — **the `CAUGHT!` banner event** |
| `meeting` | `t, n, cause` (`cadence`\|`witness`)`, active[], frozen[], ejected[]` | M1 |
| `say` | `t, seat, text` | M2, chat variant only |
| `vote` | `t, seat, target, phase` (`initial`\|`switch`) | M3 and M4 — **the vote-change rows the last-ticks display reads** |
| `eject` | `t, target` (alias or `null`)`, tally, outcome` (`plurality`\|`tie`\|`skip`)`, wasImpostor` | M5. `wasImpostor` is spectator-side truth, never sent to a seat. |
| `order` | `t, seat, decision, plan, vote, switch, say, hunch, notes, source` (`llm`\|`retry`\|`fallback`\|`scripted`\|`budget`)`, latencyMs` | one per eligible seat per decision point |
| `end` | `t, reason, ending, winner, deposits, scores[5], roles[5], freezes, witnessedFreezes, ejections, meetings` | terminal |

Volume per episode: ~150 `seam`, ~130 `mine`, ~64 `deposit`, ≤ 3 `freeze` (+ their `witness` / `caught`),
≤ 18 `meeting`, ≤ 90 `vote`, ≤ 18 `eject`, ≤ 100 `order`, plus incidentals — **under 700 rows**.
`notes` is recorded (it makes an LLM seat's reasoning auditable) and drawn only in the feed's expanded
row; `hunch` is the headline. Both are already rune-truncated.

### The replay file (`hidden_agenda.replay.v1`)

**Strict UTF-8 JSON, one document.** Hidden Agenda records *state*, not inputs, so playback never
re-simulates, a seek is an array index, and there is no native/wasm divergence to chase (which is also
why `#mmwarn` and `ctf_mismatch_tick` are dropped).

```json
{"protocol":"hidden_agenda.replay.v1","game":"hidden_agenda","gameVersion":"1",
 "seed":1234567,"tickHz":24,
 "names":["RED","BLUE","GREEN","YELLOW","PINK"],
 "policyNames":["hidden-agenda-sleuth","hidden-agenda-shadow","hidden-agenda-miner",
                "hidden-agenda-miner","hidden-agenda-lurker"],
 "roles":["crew","crew","crew","crew","impostor"],
 "colors":["red","blue","green","yellow","pink"],
 "config":{"variant":"hidden-agenda-notalk","chat":false,"map":"vault","cols":27,"rows":19,"cell":40,
           "grid":["###########################","#.......##.......##.......#","…19 rows…"],
           "rooms":[{"id":"NW","name":"NORTHWEST VAULT","x0":1,"x1":7,"y0":1,"y1":5,"door":[4,6]},"…"],
           "seams":[{"id":"S1","room":"NW","cell":[2,2]},"…6…"],
           "grate":[[12,8],"…9…"],"spawns":[[13,7],[11,7],[15,7],[11,11],[15,11]],
           "maxTicks":3000,"depositTarget":32,"carryCap":2,"mineTicks":72,
           "seamCapacity":3,"seamRegrowTicks":120,"moveCooldown":2,
           "freezeRange":2,"freezeCooldownTicks":220,
           "visionRadius":8,"awarenessRadius":2,"sweepTicks":8,
           "meetingCadenceTicks":200,"meetingTicks":25,
           "sayTick":-1,"revealTick":5,"switchTick":18,"resolveTick":23,
           "impostorSlot":4,"planSteps":3},
 "frames":[{"t":0,
            "c":[13,7,0,0,0,0, 11,7,3,0,0,0, 15,7,1,0,0,0, 11,11,2,0,0,0, 15,11,2,0,0,0],
            "v":[6,5,3,3,3],
            "g":[3,3,3,3,3,3],
            "d":0,"m":0,"ph":0},
           "…one frame per tick…"],
 "series":{"race":[[0,0,0],[812,21,11],"…change-points: [t, deposits, impostorProgress]…"],
           "crew":[[0,4],[806,3],"…change-points: [t, activeCrew]…"]},
 "beats":[{"t":200,"k":"meeting","n":1},{"t":806,"k":"freeze"},{"t":806,"k":"caught"},
          {"t":829,"k":"eject","who":"PINK"},{"t":400,"k":"deposit","n":8},
          {"t":829,"k":"gameover","winner":"crew"}],
 "events":[ "… the rows above …" ],
 "results":{ "… the results.json object verbatim …" }}
```

- **Self-sufficient by construction.** Aliases, policy names, **roles**, body colours, the entire map as
  ASCII, every rule constant including the meeting tick offsets, the seed, per-tick state, the per-tick
  **visibility masks**, the race series, the beat timeline, every event (witness rows, vote-change rows,
  the `caught` rows) and the final results all live in these bytes. The viewer contacts **no** server
  except S3 for the `.replay` file. `roles[]` is written into the header **after** the episode by the
  same writer that writes `results`, so no player process can ever read it.
- Frame encoding: `c` = **6 integers per cog** in slot order — `x, y, facing (0=N,1=E,2=S,3=W),
  state (0 active, 1 mining, 2 depositing, 3 frozen, 4 ejected, 5 in-meeting), carry (0..2),
  mineProgress (0..72)`; `v` = per-cog 5-bit mask of which cogs that cog can currently see (bit `i` =
  slot `i`; a cog never sees itself, so its own bit is 0); `g` = gems remaining per seam in `S1..S6`
  order; `d` = deposits; `m` = meeting phase (`0` none, `1` open, `2` said, `3` voted, `4` switched,
  `5` resolved).
- Size arithmetic: 3000 frames × 40 integers ≈ **0.45 MB**, plus ≤ 700 events ≈ 0.1 MB.
  `tests/test_replay.nim` asserts `< 8 MiB`.

---

## Server, player, protocol

### Game container (`/bin/hidden-agenda`)

Routes, kept from paintbot's `src/ctf/server.nim` because hosted certification probes exactly these
**before** the player pods start (lantern, 2026-08-23):

| route | behaviour |
|---|---|
| `GET /healthz` | `200 ok`, from process start until `shutdownGraceSeconds` after the artifacts are written |
| `GET /client/player?slot=N&token=T` | the seat's HTML shell (paintbot's, trimmed); it **never** opens the player socket |
| `WS /player?slot=N&token=T` | the seat socket; a bad token is refused with a close, never a hang |
| `GET /client/global` | the broadcast client (`client/replay_broadcast.html`, embedded with `staticRead`) |
| `WS /global` | live spectator: paintbot's sprite protocol + the chrome `TextMessage` |

`hidden_agenda.player.v1` frames, JSON text, bullwhip shapes:

- **game → player**
  - `{"type":"welcome","protocol":"hidden_agenda.player.v1","slot":N,"role":"crew","name":"BLUE",
     "variant":"hidden-agenda-notalk","chat":false,"maxTicks":3000,"depositTarget":32,
     "aliases":["RED","BLUE","GREEN","YELLOW","PINK"]}` on connect. **`role` is this seat's own role and
     nothing else's.**
  - the `state` frame from `## Decisions` at every decision point and once at episode end.
  - `{"type":"final","done":true,"slot":N,"scores":[…5…],"win":[…5…],"winner":"crew",
     "names":["RED","BLUE","GREEN","YELLOW","PINK"],"deposits":32,"ticks":1832,
     "reason":"complete","ending":"crew_deposits"}`, after which the player exits **0**.
- **player → game**: `{"type":"prompt","prompt":"<= 4000 chars","scripted":"miner|lurker|"}`, sent
  immediately on connect and again after `welcome` (the re-send guards the slot-registration race). Any
  other frame is ignored with a log line.

**The `final` frame carries no `roles[]` and no `impostorSlot`.** Nobody learns the answer from the game,
not even at the buzzer, because a policy could otherwise log role↔alias pairs across episodes and the
anti-collusion pin ("roles seeded; anonymous aliases") would be worth less. Spectators get roles from the
replay and the platform gets them from `results.json`.

Startup: `src/hidden_agenda.nim` randomises the seed **before** `config.update` (paintbot's rule — every
seed-derived draw, including `rngRole`, must follow the final seed), waits up to
`playerConnectTimeoutSeconds = 120` for the five sockets, starts anyway with whoever is there (a missing
seat plays `miner`; **no** seat present → `forfeit`), then runs the tick loop.

Environment the game reads (from `tools/ci/docker_smoke.sh` and the platform): `COGAME_HOST`,
`COGAME_PORT`, `COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, plus `ANTHROPIC_API_KEY` / `ANTHROPIC_API_KEY_URI` and the Bedrock sidecar
pair. The player reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED`.

Shutdown, in this order (bullwhip's `finishEpisode` plus lantern's grace): send `final` to all five
player sockets → broadcast the last global frame → `sleep 500 ms` → write `results.json` to
`COGAME_RESULTS_URI` → write the replay to `COGAME_SAVE_REPLAY_URI` → keep `/healthz` and `/global`
answering for `shutdownGraceSeconds = 20` → `quit(0)`. The player's receive loop wraps `receiveMessage`
in `try/except CatchableError` and exits **0** on a closed or truncated frame (raid, 2026-08-23 —
otherwise `docker_smoke` passes and certification fails intermittently).

### `results.json`

```json
{"names":["hidden-agenda-sleuth","hidden-agenda-shadow","hidden-agenda-miner",
          "hidden-agenda-miner","hidden-agenda-lurker"],
 "aliases":["RED","BLUE","GREEN","YELLOW","PINK"],
 "roles":["crew","crew","crew","crew","impostor"],
 "scores":[1,1,1,1,-4],
 "win":[true,true,true,true,false],
 "winner":"crew",
 "deposits":32,"depositTarget":32,
 "freezes":2,"witnessedFreezes":1,"ejections":1,"ejectedImpostor":true,
 "wrongEjections":0,"fakeDeposits":3,"meetings":5,"ticks":1832,
 "reason":"complete","ending":"crew_deposits"}
```

Arrays indexed by **slot**, always length 5. Field definitions, so nothing is guessed: `scores[i]` = the
zero-sum result above (higher is better; the five always sum to 0); `win[i] = scores[i] > 0`;
`winner ∈ {crew, impostor, none}`; `roles[i]` = that seat's role (spectator/analysis only — it is in
`results`, which the platform stores, **never** in a player frame); `deposits` = crew deposits at the
end; `freezes` = successful freezes; `witnessedFreezes` = freezes with a non-empty witness set;
`ejections` = meetings that ejected somebody; `ejectedImpostor` = whether the impostor was one of them;
`wrongEjections` = ejections of crew; `fakeDeposits` = impostor deposits that moved no counter;
`meetings` = meetings held; `ticks` = ticks played. `names` are **policy** names (platform side);
`aliases` go to the players and into the replay's `names[]`.

---

## Viewer

**All four viewer files come from ONE starter: `Metta-AI/coworld-ctf`.** Named explicitly, because
splicing two starters' halves (one's `MODULARIZE` / `EXPORT_NAME` link flags onto the other's
`onRuntimeInitialized` bootstrap) is what left cogame-lantern with a permanently blank theater:

| file | source (**coworld-ctf**, one starter for all four) | change |
|---|---|---|
| `replay-viewer/config.nims` | `coworld-ctf` `replay-viewer/config.nims` | verbatim except the emitted name (`hidden_agenda_replay.js`) and the export list renamed `_hidden_agenda_*`. **Keep the non-`MODULARIZE` link flags exactly as they are** — no `-s MODULARIZE=1`, no `EXPORT_NAME` — because the worker bootstraps with `Module.onRuntimeInitialized`. Keep `-O2 -s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--preload-file <root>/data@data`, `--mm:arc`, `--exceptions:goto` and `-d:useMalloc`. |
| the wasm entry `.nim` | `coworld-ctf` `replay-viewer/ctf_replay.nim` → `replay-viewer/hidden_agenda_replay.nim` | same structure: `stampStage`, `hidden_agenda_load_replay`, `hidden_agenda_frame`, `hidden_agenda_input`, `hidden_agenda_packet_ptr/_len`, `hidden_agenda_error_ptr/_len`, `hidden_agenda_stage_ptr/_len`, and the `emscripten_exit_with_live_runtime()` epilogue (without it Nim's `main` destroys every global while JS keeps calling in). `ctf_mismatch_tick` is **dropped** — there is no re-simulation to mismatch. **The packet built by `hidden_agenda_load_replay` is the only one carrying `meta`** (aliases, policy names, **roles**, config); read it directly and never re-derive it via `packetAt(0)` (matrix-games, 2026-08-24). |
| `static_replay*.js` | `coworld-ctf` `replay-viewer/static_replay.js` + `replay-viewer/static_replay_worker.js` | verbatim apart from the `ctf_*` → `hidden_agenda_*` export names, the worker name string, and **one added line** in `showFailure`: `document.documentElement.setAttribute('data-replay-error', error.message \|\| String(error))`. The worker keeps `importScripts('./wire_constants.js','./broadcast_core.js','./hidden_agenda_replay.js')` and `Module.onRuntimeInitialized` — the matched pair for the link flags above. |
| `index.html` | `coworld-ctf` `client/replay_broadcast.html`, spliced by `Dockerfile.replay-viewer`'s `sed` into `replay-viewer/dist/index.html` | the starter's page **with a game block appended** (below). |

`static_replay.js` already sets **`data-replay-loaded="true"`** on `<html>` when the worker reports
`loaded` — i.e. **on its first drawn frame** (its line 161); with the added failure line it sets
**`data-replay-error`** on any failure. Those are the two signals `tools/ci/viewer_smoke.mjs` and phase
60's `viewer-check.yml` read. If a `coworld-replay` bridge `ready` message is posted at all, it is
posted from a callback that fires **after** `data-replay-loaded="true"` is set, never on rAF timing at
the call site (chorus, 2026-08-24). The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and `tools/build_replay_viewer.sh` is the
`coworld build` hook that produces the bundle. **Never a `/client/replay` pod.**

### Chrome provenance (exact)

- **`client/chrome_common.js` is copied byte-for-byte.** Nothing in it is edited — which is why the
  wire-constants global keeps the name `window.CTF_WIRE`, why the two plates ride the starter's own
  `teams` / `roster` machinery, and why the race strip is fed through `ingestLeadSeries` /
  `renderMomentum` in the starter's own `lead` shape (`{teams:[…], pts:[[t, v…], …]}`) rather than a new
  one.
- `client/broadcast_core.js` is **forked** (it is paintbot's renderer — the playbook's "treat
  `client/renderer.js` as the exact template"): the board draw becomes the station floor, walls, seams,
  grate, cogs, ice blocks and vision wedges. Its ingest/packet plumbing, letterboxing and layer pooling
  are untouched.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED**, never a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The only edits inside the starter's own
  markup/script are these three, and no others:
  1. **Removed elements** (with their CSS blocks and the JS branches that touch them):
     `#viewpanel` and its children `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`,
     `#zoom-slider`, `#zoom-in`, `#zoom-read`; `#fpv` and its children `#fpv-canvas`, `#fpv-hud`,
     `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`;
     `#povBadge`; `#mmwarn`.
     **Zoom decision: `#viewpanel` is dropped entirely.** The 27 × 19 board is fixed at 1080 × 760 and
     always fits the frame, so there is nothing to pan to and nothing a minimap could add; the zoom bar
     + minimap exist only for boards larger than the frame.
  2. **Two re-lettered literals**: the scorebug's `Lives` label becomes `Deposits` on the crew plate and
     `Crew left` on the impostor plate; the momentum strip's label becomes `RACE TO WIN`.
  3. `#lockerroom` gains `pointer-events: none` so its ~1.5 s overlay stops swallowing transport clicks
     (ecos, 2026-08-23).
  Everything else — `#stage`, `#viewport`, `#board`, `#chrome`, `#scorebug`, `#plates-l`, `#plates-r`,
  `#clock`, `#clock-time`, `#clock-caption`, `#tick-clock`, `#bannerlane`, `#killfeed`, `#grain`,
  `#lightpool`, `#speedchips`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`, `#transport` and all seven
  transport buttons (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-skip`, `#btn-end`,
  `#btn-loop`) plus `#btn-spoilers`, `#scrub`, `#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`,
  `#scrub-head`, `#endcard` with `#ec-headline` / `#ec-how` / `#ec-teams` / `#ec-wincond` /
  `#ec-replay`, and `#status` — is the starter's, unchanged.
- **The appended game block** owns: the two plate sublines, the **vote board**, the **roster strip with
  the spectator role reveal**, the `CAUGHT!` banner builder, the vision-wedge overlay, the feed row
  builders, the beat-marker CSS and the plate colours (`.plate.crew{--tc:#3f7cc4}`,
  `.plate.impostor{--tc:#e0523a}` — unknown team keys fall back to the starter's `AMBER` constant in
  `buildFlag`, so nothing breaks if a rule is missed). Its beat builder is named **`buildAgendaBeats`**,
  never `markBeat`: a game-block `function markBeat` is hoisted over the chrome alias block's
  `var markBeat = C.markBeat` and silently kills every scrubber beat (tandem, 2026-08-23). A
  scope-duplication test over the alias list enforces it.

### Transport rules

`relayout()` sets **`--band` and `--hudscale` on `:root`** (and `--topband` for the scorebug strip);
every chrome measure derives from `--u = 1px * var(--hudscale)`. **No overlay sits in the transport
band**: the vote board, the roster strip, the banner lane and the feed are all clipped to the board
region between `var(--topband)` and `var(--band)`. **The endcard stops at `var(--band)`** (it is
`inset: var(--topband) 0 var(--band) 0`, the starter's own rule) **and is dismissed by every seek.**

**Scrubber beats are clickable, labelled buttons.** `buildAgendaBeats(state)` ingests `state.beats` on
the first HUD frame, calls the chrome's aliased `markBeat(t, kind, team)` for each, and a post-pass
`upgradeBeatButtons()` replaces each placed `.beat-marker` div with a
`<button class="beat-marker <kind>" aria-label="…">` wired to `ctx.seek(tick)`. There is CSS for
**every kind the game emits** — `meeting`, `freeze`, `caught`, `eject`, `deposit`, `gameover` — and no
others are emitted. The whole beat timeline ships on the first HUD frame (paintbot's `beats` field), so
the scrubber is complete before playback starts, and `?spoilers=0` still holds beats back until the
playhead reaches them.

### What it draws

- **Board.** A riveted station floor with rooms in distinct floor tints, solid walls, six **gem seams**
  drawn as glittering ore blocks with a pip count of the gems remaining, and the **grate** as a
  three-by-three lit plate with a gem counter etched beside it. Five cogs in their body colours, 30 px,
  alias under the feet, carried gems drawn as 1–2 pips over the head; a **mining** cog plays the pick
  animation with a progress arc; a **frozen** cog is an ice block with the colour showing through and
  never moves again; an **ejected** cog is gone. A **freeze** plays a 6-tick beam from impostor to
  victim with a shatter puff.
- **Vision wedges.** The **impostor's** cone is drawn permanently as a faint red wedge (the spectator
  knows who it is — that is the idea's "spectator sees roles"), and on any `witness` event the
  **witness's** cone flashes white for 24 ticks so the audience sees exactly why the meeting fired.
  Both are drawn geometrically from `(cell, facing, visionRadius)`; nothing per-cell is recorded.
- **Scorebug** (`#scorebug` / `#plates-l` / `#plates-r`, paintbot's plate machinery): two plates keyed
  `crew` and `impostor`. Crew plate: headline `CREW`, big number = **deposits**, label `Deposits`,
  subline `21 / 32`. Impostor plate: headline `IMPOSTOR`, big number = **active crew**, label
  `Crew left`, subline the alias + policy of the impostor and a freeze-cooldown pip bar.
- **Roster strip** (appended, under the scorebug): five chips, `RED · hidden-agenda-sleuth`, each with
  its body colour, a state glyph (`●` active, `❄` frozen, `✕` ejected) and — spectator-side only — a
  **red ring on the impostor**.
- **Vote board** (appended, centre-right of the board region, visible only while `m > 0`): five rows
  `VOTER → TARGET`, greyed until `revealTick`, filled simultaneously at `revealTick`, and animated with a
  colour flip on any row that changes at `switchTick`; a tally column of chips beside it; the header
  reads `MEETING 4 — WITNESSED FREEZE` or `MEETING 3 — SCHEDULED`, and a countdown `RESOLVES IN 5`.
  This is where "live vote changes in the last ticks" is legible.
- **`CAUGHT!` banner** (`#bannerlane`, the starter's lane): on a `caught` event, a full-width red banner
  `CAUGHT! PINK FROZE GREEN — RED SAW IT` for 48 ticks. On a `freeze` with no witnesses, a quieter grey
  banner `GREEN WAS FROZEN — NOBODY SAW IT`.
- **Clock** (`#clock-time`, `#clock-caption`): `TICK 812 / 3000`, caption `MEETING 4 — VOTING` during a
  meeting, `DEPOSITS 21 / 32` otherwise. Spelled out, never `M4`.
- **Feed** (`#killfeed`, the starter's `pushFeed(row)` — **one argument, the row element; the signature
  is the starter's and is not changed**, which is what broke cogball 0.1.4): rows for `freeze`
  (`PINK FROZE GREEN IN THE SOUTH GALLERY`), `witness` (`RED SAW IT`), `deposit` milestones
  (`DEPOSITS 24 / 32`), `fakedeposit` (`PINK DROPPED A GEM — THE COUNTER DIDN'T MOVE`), `meeting`
  (`MEETING 4 CALLED — WITNESSED FREEZE`), `vote` (`BLUE → PINK`, and `BLUE SWITCHED → YELLOW`),
  `eject` (`PINK EJECTED 3-1 — THE IMPOSTOR`, or `YELLOW EJECTED 3-1 — CREW`), and `order`
  (`BLUE → mine S5, deposit, watch PINK "pink froze green at 806"`, tagged `auto` when `source` is
  `fallback`, `scripted` or `budget`).
- **Race strip** (`#momentum`, the SVG under the scrub track, label `RACE TO WIN`): the two stepped
  lines from `series.race`, fed exactly like paintbot's lives series —
  `state.lead = {"teams":["crew","impostor"], "pts":[[t, deposits, impostorProgress], …]}` where
  `impostorProgress = removedCrew * depositTarget / 3` (integer division), so **both curves run 0 → 32
  and whoever reaches the top wins**. `ingestLeadSeries` / `renderMomentum` in `client/chrome_common.js`
  need **no change**.
- **Endcard**: the verdict in words — `CREW WIN — 32 DEPOSITS`, `CREW WIN — THE IMPOSTOR WAS EJECTED`,
  `IMPOSTOR WINS — ONE CREWMATE LEFT`, `TIE — 3000 TICKS, 0-0` or `TIME` — then the **role reveal
  table** (all five aliases with role and policy name, the impostor highlighted), then the line
  `2 freezes · 1 witnessed · 1 ejection (right) · 3 fake deposits · 5 meetings`.
- **Broadcast frame contract** (`buildStateJson`): the starter's `teams` (`crew`, `impostor`), `roster`
  (5 entries, `name` = alias, `pol` = policy name, `s` = slot), `lead`, `beats`, `over`, plus the
  appended `agenda` block:
  `{"dep":21,"tgt":32,"crew":3,"imp":4,"cool":180,"m":{"n":4,"cause":"witness","phase":3,
  "votes":{"RED":"PINK","BLUE":"PINK","YELLOW":"skip","PINK":"YELLOW"},"tally":{"PINK":2},"in":5},
  "roles":["crew","crew","crew","crew","impostor"],"wedges":[{"s":4,"f":2,"r":8,"k":"imp"}]}`.

**Legibility at 360 px is a requirement** — the featured-match iframe is ~360 px wide.
`#stage.tiny` (already switched on at `boardW <= 620`) shrinks the feed, the roster chips and the vote
board; carry bullwhip's `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and hide plate sublines
under 640 px so the plates degrade to `CREW 21` / `IMPOSTOR 3`. Check at 360 px: both plates with their
numbers, the vote board's five rows (aliases shorten to three letters — `RED BLU GRN YEL PNK`), the
`CAUGHT!` banner (font shrinks, text never wraps out of the lane), the `TICK 812 / 3000` clock, and the
newest two feed rows.

**Real art, not placeholders.** `scripts/art/gen_agenda_art.py` (Pillow, committed, deterministic)
renders and commits into `data/`: four room floor tints and a corridor tile, wall tiles (horizontal,
vertical, corner, pillar), the gem seam in four richness states (3/2/1/0 gems), the grate plate lit and
dim, the five cog bodies (`cog_<colour>_front.png`, `_walk.png`, `_mine.png`, `_carry1/2.png`), the ice
block (`frozen_<colour>.png`), the freeze beam and shatter FX, the gem sprite, the vote chip, and the
loading screens the `#lockerroom` markup expects (`client/art/lockerroom/bg.jpg` = the station hub, plus
five colour portraits replacing the soldier `.webp`s). `Dockerfile.replay-viewer`'s copy list and its
`test -f` assertions are updated to those file names; the `league.html` `sed` step, its two `grep -q`
assertions and `client/league_replayer.html` are dropped with it.

---

## Packaging

**`compose.yaml`** — one service, one image (game + player binaries):

```yaml
services:
  hidden_agenda:
    image: coworld-hidden-agenda:latest
    platform: linux/amd64
    build: {context: ., dockerfile: Dockerfile, network: host}
```

The service name is the single source of the manifest placeholder: `services.hidden_agenda` →
**`{{HIDDEN_AGENDA_IMAGE}}`** (lantern, 2026-08-23 — `coworld build` hard-fails anything else;
`tests/test_manifest.nim` asserts the derivation). **The service name is underscored on purpose**:
`game.name` must equal the secret namespace exactly (cooperative-hunting, 2026-08-25), so
`game.name = "hidden_agenda"`, the secret URI is `secret://coworld/hidden_agenda/anthropic_api_key`, and
`POST /coworld-league-seeds` is given `hidden_agenda`. The **repo, image and page slug stay hyphenated**
(`cogame-hidden-agenda`, `coworld-hidden-agenda`, `https://softmax.com/hidden-agenda`), and `ci.yml`'s
`SLUG` stays `hidden-agenda` — exactly the commons-family split, left alone.

**`coworld_manifest_template.json`** — bullwhip's shape with the 0.1.42 strictness hive found: top-level
`$schema`, ≥ 3 `tags` (`social-deduction`, `hidden-role`, `grid`, `fog-of-war`, `llm-driven`,
`melting-pot`, `five-player`), top-level `episode_timeout_minutes: 20`, top-level `player[]`,
`variants[].description` on every variant, `game.runnable.type: "game"`, `game.owner`, no top-level
`version`, no `game.display_name`, and a real JSON-Schema `game.config_schema` with `required:
["tokens"]` and `minItems` / `maxItems` on **every** array property (tandem, 2026-08-23).

- `game.name`: `hidden_agenda`; `game.replay_viewer.bundle`: `static-replay-viewer`.
- `game.runnable`: `{"type":"game","image":"{{HIDDEN_AGENDA_IMAGE}}","run":["/bin/hidden-agenda"],
  "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/hidden_agenda/anthropic_api_key"},
  "source_url":"https://github.com/Metta-AI/cogame-hidden-agenda/tree/main"}` — the `env` entry is
  mandatory: without it the hosted game container never sees the coworld secret and every league episode
  silently plays scripted (hive, 2026-08-23), which surfaces only at phase 60 check 4.
- `game.config_schema` properties: `tokens` (string array, `minItems 1`, `maxItems 5`, required),
  `players` (array of `{name}`, `minItems 1`, `maxItems 5`), **`num_agents` (integer, 5..5, default 5)**,
  `seed`, `impostorSlot` (integer −1..4, default −1), `maxTicks` (240..3000, default 3000),
  `depositTarget` (4..64, default 32), `carryCap` (1..4, default 2), `mineTicks` (12..240, default 72),
  `seamCapacity` (1..8, default 3), `seamRegrowTicks` (24..480, default 120), `moveCooldown` (1..8,
  default 2), `freezeRange` (1..4, default 2), `freezeCooldownTicks` (30..600, default 220),
  `visionRadius` (3..14, default 8), `awarenessRadius` (0..4, default 2), `sweepTicks` (1..32, default
  8), `meetingCadenceTicks` (50..1000, default 200), `meetingTicks` (10..200, default 25), `chat` (bool,
  default true), `sayTick` (−1..200, default −1), `revealTick` (1..200, default 5), `switchTick` (1..200,
  default 18), `resolveTick` (1..200, default 23), `planSteps` (1..5, default 3), `llmTimeoutSeconds`
  (5..60, default 14), `minBatchSeconds` (0..60, default 14), `maxDecisionBatches` (1..60, default 20),
  `maxOutputTokens` (200..2000, default 900), `model` (string), `episodeTimeoutSeconds` (default 1200),
  `playerConnectTimeoutSeconds` (default 120), `shutdownGraceSeconds` (default 20), `showPlayerLabels`
  (bool, default true). `additionalProperties: false`.
- `game.results_schema`: the `results.json` object above — `required:
  ["names","aliases","roles","scores","win","winner","reason","ending"]`, every array
  `minItems: 5, maxItems: 5`, `reason` enum `["complete","deadline","forfeit"]`, `ending` enum
  `["crew_deposits","impostor_ejected","impostor_isolation","timeout","deadline","forfeit"]`, `winner`
  enum `["crew","impostor","none"]`, `roles[]` items enum `["crew","impostor"]`.
- `game.docs` (**text**, not uri — bullwhip's shape, so the pages render without a network fetch):
  `{"readme":{"type":"text","value":"<what it is: five cogs mine a station and carry gems to a central
  grate; one of them is an impostor with a freeze beam; frozen crew stay on the floor as evidence; a
  meeting fires every 200 ticks and instantly when a freeze happens in somebody's field of view; in the
  no-talk variant the only channel is a visible, changeable vote>"},
  "pages":[{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<the map, the vision cone,
  the gem economy, the freeze beam, both meeting triggers, the meeting timeline and tally rule, the
  twelve-step tick order, scoring and end conditions>"}},
  {"id":"policies.md","title":"Fielding a policy","content":{"type":"text","value":"<the per-role
  observation, the plan/vote/switch reply schema and its caps, the nine jobs, PLAYER_PROMPT /
  PLAYER_SCRIPTED how-to>"}}]}`. A manifest test asserts all three values are non-empty.
- `game.protocols` — **both**, as `{"type":"text","value":…}` objects (the platform validator rejects
  bare strings — cogame-garble, 2026-08-24): **`player`** (the `hidden_agenda.player.v1` frames, the
  per-role observation, the reply schema and its caps) and **`global`** (the `/global` sprite + chrome
  frame, the `agenda` block, and the static bundle's `index.html?replay=<url>`).
- `player[]` — **exactly two entries**, both on `{{HIDDEN_AGENDA_IMAGE}}` with
  `run: ["/bin/hidden-agenda-player"]`: `hidden-agenda-miner` (`env: {"PLAYER_SCRIPTED":"miner"}`) and
  `hidden-agenda-lurker` (`env: {"PLAYER_SCRIPTED":"lurker"}`), each with
  `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}`. Every declared player entry
  must occupy a certification slot (raid 0.1.2 → 0.1.3, `players_missing`) and both do. The champion
  prompt policies need no `player[]` entry — `coworld upload-policy` takes `run` + `env` from
  `tools/ci/policies.json`, as bullwhip's set does.
- **`variants[]` — three; `num_agents: 5` in every one**, and `players` is the five aliases in slot order
  in every one:

  | id | name | `chat` | `meetingTicks` | `sayTick` / `revealTick` / `switchTick` / `resolveTick` | `visionRadius` | `freezeCooldownTicks` | `num_agents` |
  |---|---|---|---|---|---|---|---|
  | `hidden-agenda` | Hidden Agenda | **true** | 60 | 10 / 24 / 46 / 56 | 8 | 220 | **5** |
  | `hidden-agenda-notalk` | Hidden Agenda (no talk) | false | **25** | −1 / 5 / 18 / 23 | 8 | 220 | **5** |
  | `hidden-agenda-blind` | Hidden Agenda (narrow eyes) | false | 25 | −1 / 5 / 18 / 23 | **5** | **120** | **5** |

  All three share `maxTicks: 3000`, `depositTarget: 32`, `carryCap: 2`, `mineTicks: 72`,
  `meetingCadenceTicks: 200` and every other constant above. `hidden-agenda` is the **chat default the
  idea asks for** ("keep Among Them's chat as the default") and is therefore the **league default
  variant** — phase 50 passes it as `default_variant_id` at seed time (gridlock, 2026-08-23: the variant
  is chosen at seed time or not cheaply again). `hidden-agenda-notalk` is the idea's headline
  pure-spatial-evidence mode and is what the certification fixture runs, so both deliberation shapes are
  exercised by CI. `hidden-agenda-blind` tightens the cones and shortens the beam cooldown: witnessed
  freezes become rare, absence-evidence and the deposit counter dominate, and the impostor can press —
  a materially different game on one map and one rule set.
- `certification`:
  `game_config` = `{num_agents: 5, seed: 11, impostorSlot: 4, chat: false, meetingTicks: 25,
  sayTick: -1, revealTick: 5, switchTick: 18, resolveTick: 23, maxTicks: 900, depositTarget: 12,
  minBatchSeconds: 0, playerConnectTimeoutSeconds: 120,
  players: [{"name":"RED"},{"name":"BLUE"},{"name":"GREEN"},{"name":"YELLOW"},{"name":"PINK"}]}` and
  `players` = `["hidden-agenda-miner","hidden-agenda-miner","hidden-agenda-miner",
  "hidden-agenda-miner","hidden-agenda-lurker"]` — **both declared player entries seated**, with
  `lurker` pinned on the impostor slot so the fixture reliably produces a freeze, a witnessed freeze and
  a `CAUGHT!` banner. `depositTarget: 12` keeps a crew win reachable inside `maxTicks: 900`.
  **900 ticks = 37.5 s of video at 24 fps**, which comfortably outlasts the 10 s viewer soak (ecos,
  2026-08-23), and with `minBatchSeconds: 0` and no credentials every seat is scripted, so the episode
  runs in a couple of seconds — well inside `coworld certify`'s 60 s default
  (`grace + rounds × pacing + linger < 50 s`, commons-family, 2026-08-24). No `--timeout-seconds`
  override is needed; `tests/test_manifest.nim` pins the arithmetic so it stays true.

**Other packaging files:** `Dockerfile` (paintbot's two-stage nimby build; produces `/bin/hidden-agenda`
and `/bin/hidden-agenda-player`), `Dockerfile.replay-viewer` (paintbot's, with the hidden-agenda file
list and the same `test -f` assertions, minus `league.html`), `tools/build_replay_viewer.sh` (paintbot's,
image tag renamed, `mkdir -p` fix), `.github/workflows/ci.yml` and `coworld-release.yml` copied from
`coworld-builder/templates/`, `tools/ci/docker_smoke.sh` with `<slug>` = `hidden-agenda`, `<IMAGE>` =
`coworld-hidden-agenda` and **`<SEATS>` substituted to 5**, `tools/ci/viewer_smoke.mjs` copied
**verbatim**, `tools/ci/renderer_fixture.html`, and `tools/ci/policies.json` naming the two champions
`hidden-agenda-sleuth` and `hidden-agenda-shadow` (**both `PLAYER_PROMPT`**, each with
`env: {"USE_BEDROCK":"true"}` — without it the platform gives the player pod no Bedrock sidecar and the
seat silently plays scripted, cogolf 2026-08-24; champion #2 carries
`"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) plus the two fillers `hidden-agenda-miner` and
`hidden-agenda-lurker` (`PLAYER_SCRIPTED`).

---

## Tests

All run in `ci.yml`; the sandbox cannot run any of them locally.

1. **`tests/test_map.nim` — the station.** `data/maps/vault.txt` is 27 × 19; every walkable cell is
   reachable from the grate; every seam has ≥ 1 walkable orthogonal neighbour; each room has exactly one
   doorway at the declared cell; the grate is the declared 3 × 3; the five spawn cells are walkable,
   distinct, and rotate with `seed mod 5`; the room table's rectangles do not overlap and contain their
   seams.
2. **`tests/test_vision.nim` — the cone.** Quadrant membership for all four facings on a hand-checked
   grid; `los` is symmetric as a *predicate on cells* and blocked by both `#` and `S`; `visible` is
   **not** symmetric between cogs (an explicit case where A sees B and B does not see A — the property
   the whole witness mechanic rests on); the awareness ring sees behind you at range 2 and not at 3;
   walls block the ring too; a cog never sees itself; the recorded `v` bitmask equals a recomputed
   `visible()` for every cog on every tick of a full episode.
3. **`tests/test_sim.nim` — sim units.** Mining takes exactly `mineTicks` and resets on move/freeze/
   meeting; `carryCap` is enforced; a crew deposit moves the counter by exactly 1 per tick and an
   impostor deposit moves it by 0 and emits `fakedeposit` with the correct `seenBy`; seams regrow at
   exactly `seamRegrowTicks` and cap at `seamCapacity`; the freeze is refused out of range, without LOS,
   on cooldown, on a frozen target, on the impostor itself and during a meeting, and accepted exactly
   otherwise; a frozen cog never acts, never votes and never moves again; `freezeCooldownTicks` is set
   on success only; the witness set is computed from **start-of-tick** positions and facings; a
   witnessed freeze opens a meeting on the **very next tick** regardless of the cadence timer, and an
   unwitnessed one does not; the cadence timer resets to 200 at the **end** of every meeting; move
   cooldown; two cogs cannot share a cell and the lower slot wins; walls and seams are impassable;
   bodies block neither movement nor sight; BFS determinism; **determinism** — the same seed and the
   same scripted decisions produce an identical `gameHash` after 3000 ticks, twice in one process and
   across a fresh server.
4. **`tests/test_meeting.nim` — deliberation and the vote.** The six meeting steps fire at exactly
   `sayTick` / `revealTick` / `switchTick` / `resolveTick` / `meetingTicks` for **both** shapes;
   positions and facings are saved and restored exactly; frozen and ejected cogs neither vote nor
   teleport; the switch snapshot is taken at `switchTick − 1` and **all** conditionals evaluate against
   the same snapshot; `"if":"tie"` fires only when no alias leads strictly; a switch that does not
   change a vote emits no row; the tally ejects only on `m > s` with a unique maximum, and emits
   `outcome` `tie` / `skip` otherwise; ejecting the impostor ends the episode `impostor_ejected`;
   ejecting the last-but-one crew ends it `impostor_isolation`; a seat with no valid reply casts `skip`.
5. **`tests/test_noleak.nim` — the hidden role is actually hidden.** (a) Every seat's `state` frame
   bytes, at every decision point of a full episode, contain no other seat's `role`, `plan`, `hunch` or
   `notes`, and no cell of any cog that was outside that seat's FOV and not in its own remembered
   `lastSeen`; (b) the `welcome` and `final` frames carry no `roles[]`, no `impostorSlot` and no seed;
   (c) in a no-talk variant the string of any `say` field never appears in any seat's frame or in the
   replay; (d) `worldHash(seed)` is **identical** whichever slot `rngRole` draws — the role comes from
   `rngRole`, everything observable from `rngWorld`; (e) the impostor's frame never contains who can see
   it.
6. **`tests/test_baseline.nim` — bounded orders / legality.** For 16 seeds × up to 3000 ticks on all
   three variants, for each of the four baseline pairings (`miner` crew × `miner` impostor,
   `miner` × `lurker`, `lurker` × `miner`, `lurker` × `lurker`): every emitted plan has 1..3 steps and
   every `job` is inside **that role's** enum; every `at` / `who` / `room` names a live seam / active
   alias / real room; every `vote` is an active alias or `skip`; every `switch` names active aliases;
   every per-tick action is one of the twelve vocabulary values; no cog is ever outside the map, inside a
   wall or seam, or sharing a cell with another active cog; no cog carries more than `carryCap`; no
   `gems`, `deposits` or cooldown goes negative; `gems` never exceeds `seamCapacity`; the impostor never
   freezes on cooldown; neither baseline raises, and neither takes more than 1 ms per decision.
7. **`tests/test_feasibility.nim` — the oracle, as a CI precondition.** Gates (a)–(g) of `## The game`,
   over seeds 1..16 (1..64 for the slot-bias gate) on all three variants, including the test-only
   `watcher` crew kernel for gate (d). Any constant change that breaks the race — or that makes the
   evidence channel useless — fails here rather than in a dead replay.
8. **`tests/test_replay.nim` — end-to-end + strict UTF-8.** Plays a full scripted episode headless,
   writes `results.json` and the replay, then re-reads the replay **bytes**: `validateUtf8 == -1`
   (strict), parses as JSON, `protocol == "hidden_agenda.replay.v1"`, `frames.len == ticksPlayed`,
   every frame's `c` array has exactly 30 integers and `v` exactly 5, `roles.len == 5` and each is in
   the enum, `config.grid` is 19 strings of 27 characters, every event tick in `0..ticksPlayed`, at
   least one `mine`, `deposit`, `meeting` and `vote`, exactly one `end`, exactly five `reveal` rows at
   tick 0, `results.scores.len == 5` and **`sum(results.scores) == 0`**, `results.reason` in
   `{complete, deadline, forfeit}`, `results.ending` in the six-value enum, file size `< 8 MiB`. A seat
   is fed a `say`/`hunch`/`notes` of multi-byte runes exactly at the 90/80/240 caps and the recorded
   strings are asserted valid UTF-8 and ≤ the cap (the bullwhip byte-truncation bug).
9. **`tests/test_llm.nim` — decision layer.** `extractJsonObject` on fenced and prose-prefixed replies;
   a crew reply containing `hunt` → invalid; a plan of 4 steps → invalid; `mine` without `at` → invalid;
   `watch` naming a frozen cog → invalid; a `vote` for an ejected cog → invalid; `switch` naming an
   inactive cog → invalid; a `say` in a no-talk variant → **ignored, not an error, and not recorded**;
   a stubbed transport that times out, 429s, 403s or returns junk produces `miner` decisions for those
   seats, never raises, and marks `source: "fallback"`; **one batch carries every eligible seat**
   (assert `RequestBatch.len == activeSeats`, i.e. 5 at the opening and 4 after one freeze);
   `minBatchSeconds` floors the spacing between batch starts; `maxDecisionBatches` switches `source` to
   `"budget"` and never issues a 21st batch; the play deadline settles with `reason: "deadline"`.
10. **`tests/test_manifest.nim` — packaging.** `num_agents == 5` in **all three** variants and in
    `certification.game_config`; the image placeholder equals the one derived from `compose.yaml`'s
    service name (`{{HIDDEN_AGENDA_IMAGE}}`); `game.name == "hidden_agenda"` and the
    `ANTHROPIC_API_KEY_URI` namespace equals it exactly; `replay_viewer.bundle ==
    "static-replay-viewer"`; `game.docs.readme` non-empty + non-empty `pages`; `game.protocols.player`
    **and** `global` present and both `{"type":"text",…}` objects; **every** `player[]` id appears at
    least once in `certification.players`; `episode_timeout_minutes` top-level; every array property in
    `config_schema` carries `minItems` **and** `maxItems`; `results_schema` arrays are all
    `minItems 5, maxItems 5`; the cert fixture's `maxTicks / tickHz + startup + linger < 50 s`; and the
    installed coworld's own `_load_template_manifest` accepts the file (collab-cooking, 2026-08-25).
11. **`tests/test_broadcast.nim` — chrome frame.** `teams` keys are exactly `crew` and `impostor`;
    `roster[]` has 5 entries carrying the alias in `name` and the **policy** name in `pol`; `lead.teams`
    / `lead.pts` shape matches `chrome_common.js`'s expectation (`[t, crew, impostor]` rows) and both
    series are bounded by `depositTarget`; the appended `agenda` block carries `dep`, `tgt`, `crew`,
    `imp`, `roles` and, during a meeting, `m.votes` / `m.tally` / `m.phase`; `beats` carries only the
    six declared kinds; `over` is present on the terminal frame with the ending string; every feed row's
    text is ≤ its cap; and a **scope-duplication test** asserts no game-block function name collides
    with the chrome alias list (`markBeat` et al., tandem).
12. **`docker-smoke` (`tools/ci/docker_smoke.sh`, `<SEATS>` = 5).** Builds the image, runs a real
    5-seat episode in containers off the cert fixture, asserts **all five player containers exit 0**
    (raid, 2026-08-23) as well as the game, validates `results.json` against the results schema, and
    copies the replay to `SMOKE_REPLAY_OUT` (`dist/smoke/replay.json`), uploaded as the `smoke-replay`
    artifact.
13. **`wasm-viewer` job — the bundle is EXECUTED, not merely built.** `needs: docker-smoke`, downloads
    `smoke-replay`, builds the bundle via `tools/build_replay_viewer.sh`, installs Playwright pinned
    **1.55.0**, and runs **`tools/ci/viewer_smoke.mjs`** against that replay over local HTTP with
    `--strict-text-bounds` (fixed arena → `canvas_text.never_inside` must be 0) and `--soak 10` (the
    37.5 s cert replay outlasts the window). Pass requires `data-replay-loaded="true"` **and** three
    different clock readouts at 0 %, 50 % and 100 %; `data-replay-error` or silence fails the job.
    Evidence (`viewer-smoke.png`, `viewer-smoke.json`) uploads on success and failure. A second step in
    the same job runs `viewer_smoke.mjs --strict-text-bounds` against **`tools/ci/renderer_fixture.html`**
    — the worst-case renderer fixture that loads the real renderer with a full-cap 90-char `say`,
    80-char `hunch` and 240-char `notes` on **all five** seats, the vote board at five rows with the
    longest aliases, the `CAUGHT!` banner at full length, and several canvas sizes including 360 px,
    because `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY` and therefore produces a replay with zero
    LLM text (cogchemists, 2026-08-24).

---

## Out of scope (v1)

- **Per-tick policy sockets.** A seat submits a plan of ≤ 3 jobs per decision point and the kernel emits
  the per-tick grid actions. A direct per-tick action channel for RL/vector policies is not shipped.
- **A real multi-round discussion.** Chat is one statement round per meeting, revealed simultaneously,
  plus one conditional vote switch. Free back-and-forth inside a single meeting would need a second LLM
  batch per meeting and would blow the 720 s play budget; it is not shipped.
- **More than one impostor.** Exactly one, in every variant, as the idea pins. No impostor-to-impostor
  channel, no impostor count config.
- **Any seat count other than five.** `num_agents` is **5** in every variant, in the cert fixture and in
  `<SEATS>`. No 8-seat Among Them parity mode.
- **Thawing, reviving, or ghost play.** A frozen crewmate is out for the episode: it does not act, does
  not vote, does not observe for anyone else, and is not scored separately. An ejected one is gone
  entirely.
- **Report and emergency buttons.** Meetings open on exactly two triggers — the 200-tick cadence and a
  witnessed freeze. Finding a body is evidence you carry to the next meeting, not a meeting you can call.
- **Vents, sabotage, doors, lights, or any impostor ability besides the beam.** One beam, one cooldown,
  one range.
- **Procedural stations.** One authored 27 × 19 map (`data/maps/vault.txt`). Paintbot's terrain
  generator, `mapSpec`, map pool, map editor and all its style machinery are deleted, not carried dark.
- **Bitscreen / pixel observations.** Among Them's player protocol is a framebuffer; Hidden Agenda's is
  JSON. Nothing from `coworld-among-them`'s server, protocol, manifest schema, bot sidecar or CI is
  copied — it is a rules reference only.
- **Partial credit for deposits.** The score is the zero-sum ±4 / ±1 above, and a 3000-tick game is 0-0.
  No deposit-proportional consolation, no per-seat bonus for freezes or correct votes.
- **Cross-episode persistence or reputation.** Every episode redraws the impostor from its own seed;
  nothing carries over except the league rating.
- **Re-simulating playback.** The viewer decodes recorded state; there is no replay-hash mismatch mode,
  no `--mismatch-quit`, and no `#mmwarn`.
- **Achievements, perks, handicaps, first-person PiP, the POV lens, the league replayer page.** All
  inherited paintbot machinery, all deleted rather than carried dark.
