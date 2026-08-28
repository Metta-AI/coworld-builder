# cogame-procgen — design note (2026-08-28)

> **Destination path in the new repo: `docs/plans/2026-08-28-procgen-design.md`.** Phase 20 commits
> identical bytes there. This copy under `runs/2026-08-28-procgen/design.md` is the run's record; the
> two files are byte-for-byte the same.

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` re-exporting the sim modules,
`sim_types.nim` owning `GameVersion` / `ReplayFps = 24` / `TargetFps = 24` and the rune caps
`MaxNoteRunes = 160` / `MaxSayRunes` / `MaxPromptRunes = 4000`, the flatty wire types whose field
order is sacred); the Sprite v1 mummy HTTP/websocket server implementing the Coworld contract
(`src/ctf/server.nim`, `roster.nim`) including its `Ping → Pong` branch; the
`decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` / `control.nim` commander layer with its
one-batch-per-turn shape, its `attempt1Ms` / `retryMs` / `turnBudgetMs` / `turnSpacingMs` deadlines,
its budget guard (`decide.nim:335-346`), its rate floor (`decide.nim:384-392`), its tolerant JSON
extraction, its rune-boundary truncation (`directives.nim:71-90`) and its repair-don't-reject
validator; the binary `COWLD…` replay of recorded inputs plus a per-step `gameHash`, re-simulated by
**the same sim module** compiled to wasm by `replay-viewer/config.nims`; the `client/` broadcast
chrome (`chrome_common.js` + `broadcast_core.js` + `replay_broadcast.html`, with the appended game
block spliced in through the `window.PaintballChrome.install(PB_CTX)` hook at
`client/replay_broadcast.html:4337`); nimby + `Dockerfile` + `Dockerfile.replay-viewer` +
`tools/build_replay_viewer.sh`; and the Nim test suite with its four shards (`tests/shard_1..4.nim`,
`tests/config.nims`).

**Starter choice, one line:** this is a **real-time game loop whose rules are written for this
coworld** — an integer tile sim stepped frame by frame, a per-frame input log, a static wasm replay
viewer and broadcast chrome — which is row 1 of the starter table in `prompts/10-design.md` and
`playbooks/make-coworld.md` §Phase 0, and `coworld-ctf` is that row's starter.

**It is deliberately NOT `cogame-moba` / `docs/PORTING.md`.** OpenAI Procgen is a **C++ engine**
(`gym3`/`libenv`, 64×64 RGB framebuffers) that we cannot embed in a Nim coworld image and cannot
compile to the replay viewer's wasm module. So this repo is **not a bit-exact port**. It is an
**original suite of procedurally generated minigame archetypes written in Nim in the spirit of
Procgen**, on the paintbot stack, graded on held-out seeds. Every claim it makes about Procgen is
confined to the divergence table below, and `docs/RULES.md` says on its first line that this is a
reimplementation, not a port. Anyone who wants bit-exact `coinrun` wants a different starter and a
different note.

Where this note departs from coworld-ctf it says so. The departures are: **the board is a small
integer tile grid, not a continuous 2-D arena** (the whole `arena.nim` / `map_art.nim` /
`map_pool.nim` / `mapgen_styles.nim` map machinery, the map editor, the mapkit and the pool review
page are deleted, not disabled); **there are no weapons, no paint, no flags, no hill, no hit points,
no lives, no teams and no respawns**; **there is exactly one seat**, so `slots`/teams disappear from
the config and scoring is a single non-negative scalar, not a team margin; **fog of war is gone** —
the whole level is visible, so the shadowcast, the vision cones and the FPV pipeline are deleted; and
**the episode is a gauntlet of eight independently generated levels**, so the sim has a level
lifecycle the starter does not have.

---

### Source idea (verbatim)

> SA Procgen — sixteen procedurally generated games where the level you're graded on is one you've
> never seen
>
> Single-agent generalisation coworld over OpenAI Procgen: coinrun, starpilot, caveflyer, dodgeball,
> fruitbot, chaser, miner, jumper, leaper, maze, bigfish, heist, climber, plunder, ninja, bossfight.
> 64×64 pixels, 15 actions, every episode a new procedurally generated level. Score = mean return
> over N unseen levels (test seeds held by the server), so memorising levels is worthless — the
> league grades generalisation directly.
>
> Seats: 1
> Motive: score attack on held-out seeds
> Policy interface: per-frame discrete over pixels — neural-policy coworld
> Fills gap: generalisation-as-the-score; pairs with SA Atari (memorisable) as a deliberate contrast
> Integrity: test seeds never published; N-level average, not best-of; deterministic replay
> verification.
>
> Replay plan (watchability): native pixels; a 'seen levels vs unseen' split score.
>
> Source: github.com/openai/procgen; Cobbe et al. 2020.

---

### What the idea asks for, and what this repo actually builds

Eight readings the idea leaves loose, closed here. Each is a decision, not a survey.

1. **"Sixteen procedurally generated games"** → **four archetypes** in v1: `maze` (maze/collect),
   `chaser` (chase/avoid), `climber` (platform/gap, gravity), `miner` (dig/boulder). Reason: one
   shared 15×9 tile/entity sim can host exactly these four honestly — each reuses the same grid, the
   same six-symbol action alphabet, the same collect/exit scoring and the same renderer, and each
   adds one physics hook. The other twelve need different engines (a scrolling shooter, a fish-size
   ecology, a boss state machine) and go to §Out of scope.
2. **"64×64 pixels … per-frame discrete over pixels — neural-policy coworld"** → the **policy sees a
   symbolic observation** (an ASCII tile grid plus structured fields) and issues discrete actions;
   the **viewer** renders the native-pixel look. Reason (a rail from the coordinator, restated here
   because it is load-bearing): the fleet's policies are an LLM prompt policy and a scripted
   baseline, not a convnet; a 4096-pixel byte array in a prompt is unreadable and unscorable, and the
   decision the idea is actually buying ("route through a level you have never seen") survives the
   change of encoding intact.
3. **"15 actions"** → **six action symbols**: `L R U D X .` — see §The game → The action alphabet,
   which states the divergence and why.
4. **"every episode a new procedurally generated level"** → **every episode is a gauntlet of eight
   levels**, each independently generated from its own seed, four from a **published** training-seed
   table and four drawn **fresh per episode** from a 2-billion-wide space the seat never sees.
5. **"Score = mean return over N unseen levels (test seeds held by the server)"** → `scores[0]` is
   exactly the mean per-level return over the **unseen** levels only, in `[0.000, 1.000]`, higher
   better (§Scoring). The seen half is measured, drawn and recorded — never scored.
6. **"test seeds never published"** → the held-out seeds are **drawn per episode** from the platform's
   random episode seed through a stream the policy cannot observe or influence, from
   `[100000, 2147483646]`, disjoint by construction from the 128 published training seeds. There is
   therefore no fixed hidden set that can leak; memorising is worthless because the level did not
   exist when the prompt was written. This is a **stronger** mechanism than the idea's literal
   "server holds a fixed test set", and §The game → Seen and unseen states it as the divergence it is.
7. **"N-level average, not best-of"** → `unseenMilli` is the arithmetic mean over all four unseen
   levels, including the ones the agent died on. There is no drop-worst, no best-of and no retry.
8. **"deterministic replay verification"** → the replay records the episode seed, the eight level
   seeds, one action byte per sim frame and one `gameHash` per sim frame; the wasm viewer
   **re-generates every level from its seed** and re-simulates, and `#mmwarn` fires on the first
   divergent frame. Levels are never stored as tiles.

**There is no `OPEN` section.** The one reading that could have produced a materially different game
— item 6, whether "test seeds held by the server" means a fixed hidden list or a fresh draw — is
decided above (fresh draw), with the reason stated, and both readings are recorded in `docs/RULES.md`
§Integrity so a later operator can see what was chosen and why.

---

### Upstream, consulted and pinned

The only claims this repo makes about OpenAI Procgen are the four below. Each is transcribed into
`src/procgen/upstream.nim` with its citation comment beside it, and
`tests/test_procgen_upstream.nim` asserts the shipped text still matches. The repo makes no other
claim, and `docs/RULES.md` opens with "this is a reimplementation in the spirit of Procgen, not a
port of it".

| Upstream fact (github.com/openai/procgen; Cobbe et al. 2020, *Leveraging Procedural Generation to Benchmark Reinforcement Learning*) | How it lands here |
|---|---|
| Procgen's headline claim is that **training and test levels are drawn from the same generator but are different levels**, and that the interesting number is the **test** return | `scores[0]` is the unseen-level mean and nothing else; the seen mean exists only to display the generalisation gap |
| Procgen ships **sixteen** games sharing one engine and one action interface | four archetypes share one 15×9 tile sim, one action alphabet, one scoring formula and one renderer |
| Procgen levels are **seed-deterministic**: a seed reproduces a level exactly | `generateLevel(archetype, seed, difficulty)` is a pure function; `tests/test_procgen_gen.nim` asserts byte-identical grids across 500 seeds and across native/wasm |
| Procgen's observation is a **64×64×3 frame** and its action space has **15** entries | **Both diverge here.** Observation is symbolic (§Server → observation); the alphabet is six symbols (§The game → The action alphabet). Both divergences are listed in `docs/RULES.md` §Divergences with their reasons |

**Documented divergences** (also `docs/RULES.md` §Divergences, cited in `src/procgen/upstream.nim`,
asserted by `tests/test_procgen_upstream.nim`):

1. **Not a port.** No Procgen C++ code, no `gym3`, no `libenv`, no asset from the upstream repo. The
   archetypes are named after Procgen games because they are in the same spirit; the rules are
   written here.
2. **Symbolic observation, not pixels** (reason: item 2 above).
3. **Six action symbols, not fifteen** (reason: §The game → The action alphabet).
4. **A decision is a plan of up to six primitive frames**, not one frame (reason: §The game → Why a
   turn is a plan). Procgen's agent acts every frame at 15 Hz; an LLM cannot.
5. **A fresh per-episode test seed, not a fixed held-out set** (reason: item 6 above).

---

### Design pins, and where each is satisfied

Every pin in `playbooks/make-coworld.md` §Phase 0 ("Pins that are never optional") and
`docs/SPEC.md` §"Design pins every coworld inherits", and where this note answers it:

| Pin | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — a real-time tile loop with rules written into this repo; **not** moba, because nothing is being ported bit-exactly (title paragraph) |
| Repo `Metta-AI/cogame-procgen`, **public** (`source-resolves` 404s on private) | §Packaging |
| Build **both** an LLM policy and a scripted baseline day one, same image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=pathfinder\|scavenger`) |
| Replays are a **static file + browser wasm viewer, never a pod** | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`; no `/client/replay` viewer is ever declared to the platform) |
| Starter chrome **verbatim** — page + appended block, byte-identical `chrome_common.js`, transport rules, zoom decision | §Viewer → Chrome provenance, → Transport rules |
| **Real art, not placeholders** | §Viewer → Art (nano-banana tile kit + the starter's shipped chrome art) |
| Legible to a casual spectator | §Viewer → Readouts and → Legible at 360 px (plain-language feed, "gem 3 of 4", never internal notation) |
| **Two name spaces** — anonymous cog alias in-game, real policy name spectator-side | §The game → Seat, alias, and the second hidden name space |
| **Degrade, never hang**; assume `episodeTimeoutSeconds` 1200 and play inside **60 %** (≈720 s) | §Decisions → Cadence and the wall-clock arithmetic; → Degrade, never hang |
| `num_agents` in **every** variant AND the cert fixture, **inside `game_config`** | §Packaging — `num_agents: 1`, four times (three variants + certification) |
| Decisions issued as **one batch per turn** (here a batch of one) | §Decisions → Cadence |
| Replay bytes self-sufficient (names, config, per-frame state, seed) | §Server → Replay bytes |
| Rune-boundary truncation on every free-text field | §Server → Reply schema and per-field caps |
| Integrity (the idea's own note): unpublished test seeds, N-level average, deterministic replay verification | §The game → Seen and unseen; §Scoring; §Server → Replay bytes |
| Prove it in CI: sim tests, scripted-bot legality test, an end-to-end episode writing a replay, a strict-UTF-8 replay parse, a viewer smoke that **executes** the bundle | §Tests |

---

## The game

One cog is dropped into eight small levels in a row. Each level is built from scratch by a generator
from a number nobody tells it: a maze with four gems and a locked door; an open room full of pellets
with two hunters walking it down; a stack of platforms over a pit; a wall of dirt with diamonds and
boulders behind it. It gets ten decisions per level, and each decision is up to six moves it commits
to in advance. Half the levels come from a seed table published in this repo, so a good prompt may
have studied them; the other half were drawn out of two billion possibilities the moment the episode
started, so nobody has ever seen them. **The score is what it does on the ones nobody has seen.** The
replay shows both numbers side by side, and the gap between them is the whole point of the coworld.

### Seat, alias, and the second hidden name space

- **`num_agents` = 1.** Exactly one seat, always — in all three manifest variants and in the
  certification fixture, and substituted into `<SEATS>` in `tools/ci/docker_smoke.sh` as `1`. The
  idea pins it ("Seats: 1"), and the motive ("score attack on held-out seeds") is single-player by
  construction: adding a second seat would mean two agents on one level, which is a race, which is a
  different game with a different score.
- **Two name spaces (the pin).** In-game the cog is **`COG-alpha`** — the starter's identity array
  (`src/ctf/roster.nim:64`, `IdentityNames[0]`), fixed for the whole episode. That alias is the only
  name in the observation, the prompt, the reply, the `say`, the feed and the board label. The seat's
  **real policy/player name** (`daveey`, `daveey-1`, `Baseline (1)`) lives only in `results.names`, in
  the replay's join record, and in the viewer's scorebug plate and endcard. `showPlayerLabels` is
  **false** in every variant. `tests/test_procgen_identity_privacy.nim` (the starter's
  `test_pb_identity_privacy.nim` pattern) asserts no real name appears in any observation JSON, any
  prompt or any broadcast label. With one seat there is nobody to meta-game against, but the pin
  still binds: a policy that can read its own player name can condition on it, and the ladder's
  anonymity property has to hold uniformly or it holds nowhere.
- **A second hidden name space, specific to this game.** The seat is never told **which levels are
  seen and which are unseen**, nor **any level's seed**. The spectator is told both, on the scorebug
  chip, in the clock caption and on the endcard. This is the same discipline as the alias split —
  information the audience needs and the player must not have — and it is what makes the split score
  meaningful. `tests/test_procgen_identity_privacy.nim` asserts the strings `"seen"`, `"unseen"` and
  every level seed are absent from every observation and every prompt.

### The board

Every level, in every archetype, is a **15 × 9 tile grid**, `cellPx = 32` map pixels per tile, with
the outer ring always `Wall`. Coordinates are `[x, y]`, **x growing right, y growing down**; `[0,0]`
is the top-left. `L` = x−1, `R` = x+1, `U` = y−1, `D` = y+1.

15 × 9 is fixed for all four archetypes and all three variants, and it is fixed on purpose:

- `BOARD_ASPECT` is then a constant **1.667** for the whole episode, so `relayout()` never re-fits
  mid-replay and a tile is the same size in every level (§Viewer → Legible at 360 px).
- The interior 13 × 7 is an odd lattice, which is exactly what a backtracker maze wants (7 × 4 = 28
  maze cells).
- 135 tiles is a 135-character ASCII grid in the observation — cheap enough to send every turn.
- 13.7 screen pixels per tile at a 360 px embed (§Viewer) is the smallest tile that still reads.

Tiles are one closed enum, `src/procgen/tiles.nim`:

| Value | Name | ASCII in the observation | Passable? |
|---|---|---|---|
| 0 | `Empty` | `.` | yes |
| 1 | `Wall` | `#` | never (bedrock; `miner` cannot dig it) |
| 2 | `Dirt` | `:` | only in `miner`, by digging |
| 3 | `Boulder` | `O` | only in `miner`, by pushing |
| 4 | `Gem` | `*` | yes (collects) |
| 5 | `Pellet` | `o` | yes (collects) |
| 6 | `ExitLocked` | `+` | no |
| 7 | `ExitOpen` | `E` | yes (finishes the level) |
| 8 | `Platform` | `=` | no (stood on, in `climber`) |
| 9 | `Ladder` | `H` | yes (climbable with `U`/`D`) |
| 10 | `Spike` | `^` | yes, and lethal |

The agent is `@` in the ASCII grid; a hunter is `X`. `tests/test_procgen_sim.nim` asserts the enum,
the glyph table and the passability table are the single source both the resolver and the observation
builder read.

### The action alphabet

**Exactly six symbols: `L R U D X .`** — left, right, up, down, the archetype's special, and wait.
Case-insensitive on the wire, uppercased on parse.

`X` is the only symbol whose meaning changes:

| Archetype | `X` means |
|---|---|
| `maze` | nothing — treated as `.` |
| `chaser` | **dash**: move two tiles in `last_dir` if both are passable, then a 4-frame cooldown during which `X` is `.` |
| `climber` | **jump**: set `jumpFuel = 2`; while `jumpFuel > 0` the cog rises one tile per frame instead of falling |
| `miner` | **dig**: convert the `Dirt` tile in `last_dir` to `Empty` without moving |

**The divergence from Procgen's 15 actions, and why.** Procgen's action space is a 3 × 5 product
(`{left, none, right} × {down, none, up, special-1, special-2}`), and in most of its sixteen games
several of those combinations are no-ops. Diagonal movement in a tile sim is a corner-cutting rules
problem (may you cut a corner past two walls?) that adds a rule and no decision; the two spare
specials are unused by every archetype here. Six symbols with one archetype-specific special is the
honest reimplementation: it is the smallest alphabet in which all four archetypes are fully playable,
it fits in a spectator's head, and it fits in one line of a system prompt. Logged as divergence 3.

### Why a turn is a plan

Procgen runs at 15 frames per second and the agent acts on every frame. An LLM cannot: one call per
frame at 15 Hz is three orders of magnitude outside the episode budget. So:

**One decision turn = one `moves` string of up to `framesPerTurn = 6` symbols, executed one symbol
per sim frame, in order.** The seat sees the level, commits to six frames, and watches them run. That
is the only change to the interface, and it is the change that makes the game playable at LLM
latency: 8 levels × 10 turns = **80 LLM calls** and up to **480 sim frames** per episode.

Committing blind for six frames would be suicide in `chaser` and `miner`, so the plan is
**interruptible**: see `## Sim module` → Danger interrupt. That is the whole mechanism; there is
nothing else in it.

### Archetypes

Four, each a `LevelKind` in `src/procgen/levels.nim`. All four share the grid, the alphabet, the
scoring formula, the exit rule ("the exit is locked until every collectible on the level is taken")
and the renderer. Each contributes exactly one generator and one physics hook.

| | `maze` | `chaser` | `climber` | `miner` |
|---|---|---|---|---|
| Shape | perfect maze on the 7 × 4 odd lattice, `braidCount` dead ends knocked out | open room with scattered 1 × 1 pillars | four platform rows (`y ∈ {7,5,3,1}`) over a pit, ladders between | interior filled with `Dirt`, bedrock veins, boulders |
| Collectibles | 4 `Gem` on the four lattice cells farthest from the start | 8 `Pellet` on seeded free cells | 4 `Gem`, one per platform row | 4 `Gem` behind dirt |
| Hazards | none | 2 hunters (3 on `hard`) | `Spike` tiles, lethal falls, the pit | falling boulders |
| Gravity | no | no | **yes**, on the cog | **yes**, on boulders and gems |
| `X` | wait | dash | jump | dig |
| Death causes | — | `caught` | `fell`, `spiked` | `crushed` |
| Ends when | 10 turns used, or exit reached | caught, 10 turns used, or exit reached | dead, 10 turns used, or exit reached | dead, 10 turns used, or exit reached |

Why these four and no others in v1: they are the four *decision* shapes the whole Procgen suite is
built out of — search a topology (`maze`), evade a pursuer (`chaser`), commit to a jump you cannot
take back (`climber`), and reshape the terrain you are standing in (`miner`) — and they are exactly
the four that a single 15 × 9 integer tile sim can carry without a second engine. A fifth archetype
would add a generator, a physics hook, a renderer layer and a manifest surface without adding a fifth
kind of question. §Out of scope names the twelve that are deferred and what each would need.

**Every generator is seed-deterministic and validated.** `generateLevel(kind, seed, difficulty)` is a
pure function of its three arguments, uses one `levelRng` seeded from `seed` alone, and ends with an
archetype validator (all collectibles and the exit reachable; the start not adjacent to a hunter
spawn; `climber`'s every row reachable from the row below within jump range). A draw that fails the
validator is **redrawn with `levelRng` advanced**, up to **40 attempts**; attempt 41 falls back to the
archetype's hand-authored `FallbackLevel` const (committed, one per archetype) and emits a
`gen_fallback` chat record. Bounded, never a loop, never an unplayable level.
`tests/test_procgen_gen.nim` asserts the fallback is never reached across 5000 seeds per archetype
per difficulty.

`difficulty ∈ {easy, standard, hard}` is one integer table per archetype
(`braidCount`, `pillarCount`, `hunterCount`, `spikeCount`, `boulderCount`, `bedrockPct`), nothing
more. `standard` is the league default; `hard` is a manifest variant.

### Seen and unseen

- **The published half.** `src/procgen/seeds.nim` holds `TrainSeeds`, **32 seeds per archetype,
  128 in total**, and they are the literal ranges `maze 1001–1032`, `chaser 2001–2032`,
  `climber 3001–3032`, `miner 4001–4032`. They are printed in `docs/TRAINING_SEEDS.md`, inlined into
  `game.docs.pages`, and anyone may generate, study, solve and hard-code them. A champion prompt that
  memorises all 128 levels is playing the game as intended — and it earns nothing, because those
  levels are not scored.
- **The held-out half.** `testRng`, an integer stream seeded **`seed xor 0x7E57`**, draws each unseen
  level's seed uniformly from **`[100000, 2147483646]`** — disjoint from `TrainSeeds` by construction
  (every training seed is < 5000), asserted by `tests/test_procgen_seeding.nim`. `seed` is the episode
  seed the platform randomises per episode, so an unseen level did not exist when the prompt was
  written. There are ~2.1 × 10⁹ levels per archetype; the four unseen levels of an episode have
  never been played before with probability ≈ 1.
- **The gauntlet plan is drawn before the seat connects.** At episode start, with no seat attached:

  ```
  setupRng = rng(seed)                      # play order + which training seeds are used
  testRng  = rng(seed xor 0x7E57)           # held-out seeds only
  plan = []
  for kind in [maze, chaser, climber, miner]:            # fixed order, then shuffled
    plan.add (kind, "seen",   TrainSeeds[kind][setupRng.rand(0 ..< 32)])
    plan.add (kind, "unseen", testRng.rand(100000 .. 2147483646))
  shuffle(setupRng, plan)                   # PLAY ORDER only; never the split
  ```

  For `levelCount = 8` that is one seen and one unseen level of **each** archetype, so the split score
  is a paired comparison on the same four generators — the cleanest possible generalisation gap. For
  `levelCount = 4` (the `sprint` variant) each archetype appears once and `setupRng` picks a 2-subset
  of the archetypes to be `seen`. `levelCount` is required to be **4 or 8**; `sim_config` rejects
  anything else.
  Because both streams are drawn **before the first turn and before any seat connects**, nothing the
  policy does can shift a seed or a split, which is the integrity property the idea asks for and
  `tests/test_procgen_seeding.nim` asserts.
- **What "never published" means here.** The seeds are recorded in the replay and in
  `results.levelSeeds` **after the fact**, so a spectator (and the deterministic re-simulation) can
  verify the episode. That does not weaken anything: the set is not fixed, so there is nothing to
  memorise for next time. §What the idea asks for, item 6, records this as the divergence it is.

### The clock

- **A sim frame is the atom.** One frame = one primitive symbol resolved. `fastMode: true` — the loop
  is never wall-clock paced and the sim costs microseconds; the episode's wall clock is the 80 LLM
  turns (§Decisions).
- **`framesPerTurn = 6`**, **`turnsPerLevel = 10`**, **`levelCount = 8`** ⇒ at most **80 decision
  turns** and **480 sim frames** per episode. A level that ends early (cleared or dead) forfeits its
  remaining turns; they are **not** reallocated to later levels — every level gets the same budget or
  the score is not comparable across levels, and a shorter episode only helps the wall clock.
- **Playback** is the viewer's business: **`renderFramesPerStep = 4`** at `ReplayFps = 24`, i.e.
  **6 sim frames per second**, so a 45-frame level plays for 7.5 s and a full episode for ≈ 50 s.
  That is what lets `viewer_smoke.mjs --soak 10` observe real advancement (the ecos 2026-08-23 scar).

### Turn structure — the exact resolution order

**Level lifecycle**, at the start of each level, in this order:

L1. `levelIndex += 1`. `(kind, split, levelSeed)` is read from the pre-drawn plan; nothing is drawn
    here.
L2. `grid = generateLevel(kind, levelSeed, difficulty)` — pure, validated, bounded redraw.
L3. `collected = 0`; `collectTotal = 4` (`maze`, `climber`, `miner`) or `8` (`chaser`);
    `alive = true`; `finished = false`; `frame = 0`; `levelTurn = 0`; `last_dir = R`.
L4. `startDist = bfsDist(start, exit)` over the archetype's **dig-and-push-inclusive** passability;
    `bestDist = startDist`. The generator guarantees `startDist >= 1`.
L5. Emit `levelstart`.
L6. Decision turns run (below) until `finished`, `not alive`, or `levelTurn == turnsPerLevel`.
L7. `outcome = cleared | died | timeup`; `returnMilli[levelIndex]` is computed (§Scoring); emit
    `levelend`.
L8. If `levelIndex == levelCount`, emit `gauntletend` and end the episode; else go to L1.

**Decision phase**, at the top of each turn, in this order:

D1. The engine snapshots the level and builds the seat's observation (§Server → observation).
D2. The seat's LLM request goes out as **ONE batch** — the starter's `curly.makeRequests` at
    `decide.nim:427`, unchanged, degenerating to a batch of one — with attempt-1 deadline
    `attempt1Ms = 5000`. A scripted seat computes locally in microseconds and consumes no request.
D3. If attempt 1 timed out, errored, returned non-JSON or returned no usable `moves`, it is retried
    **once**, `retryMs = 2000`. A provider 429 with no other candidate model skips the retry (it
    cannot land) and falls straight through — the starter's fail-fast at `decide.nim:467-479`.
D4. Still no usable reply → the **`pathfinder`** scripted plan is used and a `fallback` record naming
    the cause is written (§Decisions → Degrade).
D5. The plan is parsed and **repaired, never rejected** (§Server → reply schema); a repair increments
    `ordersRejected`.
D6. `say` (≤ 24 runes, rune-truncated) is drawn as a board bubble for `sayFrames = 12` and pushed to
    the feed. With one seat it is spectator narration only and is never fed back into an observation.
D7. `turnSpacingMs = 2500` is a floor on wall-clock time between consecutive **batch starts** (the
    starter's mechanism at `decide.nim:384-392`, kept), which holds the episode at **24 requests per
    minute**, inside the sidecar's 30-per-minute per-episode cap.

**Frame resolution.** For each symbol of the plan, in order, and **this is the whole physics of the
game — nothing else mutates the level**:

1. `frame += 1`; pop the next symbol `a`.
2. **Intent.** `applyAction(kind, a)` resolves `a` into either a target cell (for `L R U D`), an
   archetype special (`X`), or nothing (`.`). `L R U D` set `last_dir = a` **whether or not the move
   succeeds** — naming a direction is how you aim a dig or a dash.
3. **Cog move.** If the target is passable under the archetype's predicate, the cog moves there;
   otherwise the frame records `blocked` and the cog stays. `miner`: a `Dirt` target is dug and
   entered in the same frame; a `Boulder` target is **pushed** one tile if the cell beyond is `Empty`
   and the push is horizontal, otherwise the move is blocked. `climber`: `U`/`D` move only on a
   `Ladder`; horizontal moves are legal in mid-air.
4. **Collect.** If the cog's cell holds a `Gem` or `Pellet`, remove it, `collected += 1`, emit
   `collect`. When `collected == collectTotal`, the `ExitLocked` tile becomes `ExitOpen` and
   `exitopen` is emitted.
5. **Archetype physics**, exactly one hook per archetype:
   - `maze`: none.
   - `chaser`: each hunter takes one step toward the cog along a BFS shortest path (ties broken in the
     fixed order `L, R, U, D`), **except on frames where `frame mod 3 == 0`**, where hunters do not
     move — so the cog is strictly faster, 3 cog steps per 2 hunter steps. The dash cooldown
     decrements.
   - `climber`: if `jumpFuel > 0`, the cog rises one tile (if the cell above is not solid) and
     `jumpFuel -= 1`; else if the cell below is not solid, the cog falls one tile and `fallDepth += 1`;
     landing on a solid cell resets `fallDepth`.
   - `miner`: the falling scan, in the **fixed order bottom row to top row, left to right**: any
     `Boulder` or `Gem` with `Empty` directly below moves down one tile and is marked `falling`; a
     marked entity that can no longer fall is unmarked. One tile per entity per frame.
6. **Hazards**, evaluated after physics: a hunter sharing the cog's cell → `alive = false`, cause
   `caught`; the cog's cell is `Spike` → cause `spiked`; a **falling** boulder entering the cog's cell
   → cause `crushed`; `fallDepth > fallLethal = 4`, or the cog below row 8 → cause `fell`. On death,
   emit `death` and stop.
7. **Exit.** If the cog stands on `ExitOpen`, `finished = true`.
8. **Progress.** `d = bfsDist(cog, exit)`; `bestDist = min(bestDist, d)`. This is the only measurement
   the score reads besides `collected` and `finished`, and it uses the same `path.nim` BFS the
   baselines and the observation use.
9. **Record.** `gameHash` folds the whole level state (grid, cog, entities, `collected`, `alive`,
   `finished`, `frame`, both RNG states); the action byte and the hash are appended to the replay.
10. **Frame end.** If `finished` or `not alive`, the rest of the plan is discarded and the level ends
    (L7). Otherwise, if the **danger interrupt** (§Sim module) fires, the rest of the plan is
    discarded, `planInterrupts += 1`, and control returns to D1 for the next turn.

### Scoring formula and sign

Per level `i`, an integer **return in milli-points**, `0 … 1000`:

```
collectMilli[i]  = (700 * collected[i]) div collectTotal[i]                      # 0 .. 700
approachMilli[i] = (200 * max(0, startDist[i] - bestDist[i])) div startDist[i]   # 0 .. 200
finishMilli[i]   = 100 if finished[i] else 0                                     # 0 or 100
returnMilli[i]   = collectMilli[i] + approachMilli[i] + finishMilli[i]           # 0 .. 1000
```

`collectTotal[i]` is 4 or 8 and never zero; `startDist[i] >= 1` by generator validation; every term
uses non-negative integer `div`, so the arithmetic is exact and identical native and in wasm. A level
where the cog collected everything and walked out scores exactly **1000**. A level where it died on
frame 1 scores **0**. There is no death penalty — dying already costs the rest of the level, and a
negative term would make the mean unreadable on a scorebug.

Then, over the gauntlet:

```
unseenMilli = sum(returnMilli[i] for i where split[i] == "unseen") div unseenCount
seenMilli   = sum(returnMilli[i] for i where split[i] == "seen")   div seenCount
gapMilli    = seenMilli - unseenMilli                     # may be negative; reported, NEVER scored

scores[0]   = unseenMilli / 1000.0                        # 0.000 .. 1.000
win[0]      = every unseen level ended `cleared`
```

**Sign: higher is better.** The minimum is `0.000`, the maximum `1.000`, and nothing is negative.
**The league ranks by `results.scores[0]` — the mean return over the unseen levels, and nothing
else.** That is the idea's "Score = mean return over N unseen levels", literally: an N-level
arithmetic mean including the failures, never a best-of, never a drop-worst.

**Everything else is measured and shown, never scored**: `seenMilli`, `gapMilli`, `levelReturns`,
`levelOutcome`, `levelFrames`, `collected`, `planInterrupts`, `ordersRejected`, `fallbackTurns`.
`seenMilli` in particular is *deliberately* excluded — the moment the seen half pays, memorising 128
levels becomes worth doing, which is the exact failure the coworld exists to avoid.

`tests/test_procgen_scoring.nim` asserts, over 2000 randomised end states: `returnMilli ∈ [0,1000]`;
`returnMilli == 1000` iff (all collected and finished); `scores[0] ∈ [0.0, 1.0]`; the mean is the
arithmetic mean of all four unseen levels with no term dropped; and `gapMilli == seenMilli -
unseenMilli` exactly.

**Cross-play.** With one seat there is no cross-play in an episode; the comparison the league makes
is between *episodes*. `results.policyKinds` records what the seat was given (`llm` or `scripted`),
and phase 60 audits `llmTurns` per episode to prove a champion is not silently playing scripted.

### End conditions and legal `results.reason` values

The episode ends at the first of: **the eighth level's `levelend`**, the **wall-clock stop**, or a
**fault**. There is no early win and no early loss — a cog that dies on level 1 still plays levels 2
through 8, because the score is an N-level mean and a missing level is not a zero, it is a hole.

`results.reason` is a closed enum; **exactly these three values are legal** and the game emits nothing
else:

- **`complete`** — the healthy value. `results.endRule = "gauntlet_complete"`. All `levelCount` levels
  were played to one of `cleared | died | timeup`. Settles after the `gameOverFrames = 12` display
  hold, then writes artifacts.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (**660 s**; the starter's check at
  the top of the loop, `server.nim:1407-1417`, kept). The engine stops at the current frame and
  settles with the **real** numbers so far: levels not reached score `0` and are marked
  `outcome = "unplayed"`, `unseenMilli` still divides by the full `unseenCount`, so a deadline episode
  is still rankable and still comparable. Artifacts are written, exit 0.
  `results.endRule = "wall_clock"`. **Declared acceptable** for SPEC §Definition of done check 4 — and
  the budget guard below exists so that it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop, caught; the episode settles from the
  last completed frame, `results.endRule ∈ {"sim_fault", "host_error"}`, `results.stopDetail` names it
  (≤ 200 runes, rune-truncated), artifacts are still written, exit 0. A defect:
  `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum: **`gauntlet_complete | wall_clock | sim_fault |
host_error`**. `results.levelOutcome[i]` is a fourth closed enum:
**`cleared | died | timeup | unplayed`**.

**Budget guard.** At the start of each turn, if `elapsed + 2 × turnBudgetSeconds >
wallClockBudgetSeconds` (i.e. from ≈ 645 s), the LLM is switched off for the rest of the episode, the
seat falls to `pathfinder` (microseconds per turn), the remaining levels run at full speed, and the
episode still ends `complete` / `gauntlet_complete`. A `budget_guard` record names the turn. This is
the starter's guard at `decide.nim:335-346`, kept.

**A seat that never connects, disconnects, or fails every decision does not end the episode**: the cog
is driven by `pathfinder`, the gauntlet runs to its natural end, and `deadSeats[0] = true`. Nothing a
player container does can stop the clock — `lobbyJoinTimeoutSeconds = 90` bounds the lobby and the
per-turn deadlines bound everything after it.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes the seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {pathfinder, scavenger}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=pathfinder` — the starter's "anything unrecognised is the published default" rule in
`baselines.nim:parseBaseline`. A scripted policy seated as a champion is a failure state, and phase 60
audits it by `results.llmTurns`.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/procgen/anthropic_api_key"` — the hive
2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. **No
`USE_BEDROCK` flag** is set on the policies, because the player pod makes no LLM call (the cogolf
2026-08-24 gotcha applies to player-side-LLM lineages, not this one).

`src/procgen_player.nim` (`/bin/procgen-player`, forked from `src/paintball_player.nim`) is a thin
seat registrar: it opens the player websocket, sends one `register` packet carrying `PLAYER_PROMPT`
(rune-truncated at `MaxPromptRunes = 4000`), `PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, and then
holds the socket open. Its receive loop is wrapped in `try/except CatchableError` and exits **0** on a
dead socket (the raid 0.1.3 scar: whisky's `receiveMessage` raises on a close frame and races the
game's `quit(0)`). **The server logs loudly and marks `deadSeats[0]` when the seat produces no
`register` record** (the grf-football 2026-08-27 scar), and `results.policyKinds` plus the replay's
`register` record make it auditable afterwards.

### Cadence, batching, and the wall-clock arithmetic

**One seat means one LLM call per turn, issued through the starter's one-batch-per-turn path
unchanged.** `curly.makeRequests` is called with a one-element request list rather than being
bypassed, deliberately: the batch path is where the deadline handling, the throttle detection, the
retry ladder and the fallback accounting live, and a "simpler" single-request path would be a second
implementation of all of it. At most two batches per turn (attempt + retry).

| Knob | Value | Why |
|---|---|---|
| `levelCount` | 8 | four archetypes × (one seen + one unseen) |
| `turnsPerLevel` | 10 | 10 × 6 = 60 frames per level; the longest `pathfinder` route on a 15 × 9 `hard` maze measures 41 frames, so 60 leaves real slack for a policy that backtracks |
| `framesPerTurn` | 6 | see §Why a turn is a plan |
| `turnSpacingMs` | 2500 | 1 seat × 60/2.5 = **24 req/min**, inside the sidecar's 30/min per-episode cap |
| `attempt1Ms` | 5000 | `curly` hands the deadline to `CURLOPT_TIMEOUT`, whose granularity is **whole seconds**, so this must be a whole number of seconds — `sim_config` rejects a sub-second value (the starter's 0.1.2 scar, `decide.nim:418-426`). 5 s covers the hosted single-call p90 with margin |
| `retryMs` | 2000 | one retry, 2 s |
| `turnBudgetMs` | 7500 | hard per-turn cap: 5 + 2 = 7 s of calls plus slack |
| `wallClockBudgetSeconds` | 660 | the engine's own stop; the budget guard fires from `elapsed + 15 > 660`, i.e. ≈ 645 s |
| `lobbyJoinTimeoutSeconds` | 90 | bounds the lobby (seconds, not frames: a `fastMode` frame has no wall-clock meaning) |
| `gameOverFrames` | 12 | the display hold before artifacts are written |

**The arithmetic, out loud** (`episodeTimeoutSeconds` = 1200, the 60 % budget = **720 s**):

- **Typical.** A single hosted call measures ≈ 3.0 s and hides inside the 2.5 s spacing floor only
  partly, so a turn costs `max(2.5, 3.0) ≈ 3.2 s`. The upper bound on turns is
  `levelCount × turnsPerLevel = 8 × 10 = 80`. `80 × 3.2 = 256 s`, plus lobby ≤ 30 s, plus the
  `gameOverFrames` hold and the artifact write ≈ 20 s → **≈ 306 s = 43 % of the 720 s budget, 26 % of
  the 1200 s timeout.**
- **Worst case.** Every turn burns attempt 1 (5 s) *and* the retry (2 s) and is capped by
  `turnBudgetMs`: **7.5 s/turn**. `80 × 7.5 = 600 s` + 50 s → **≈ 650 s = 90 % of the 720 s budget.**
- **Guard.** The engine's own stop is 660 s and the budget guard switches every remaining turn to
  `pathfinder` from ≈ 645 s, so even the worst case settles `complete` / `gauntlet_complete`, not
  `deadline`, and nothing can overrun 720 s.
- Most episodes use far fewer than 80 turns: a level that is cleared or lost forfeits its remaining
  turns, and a competent policy clears a `maze` level in 5–7 turns.
- Scripted-only episodes (certification, `docker_smoke.sh`, every CI run) cost **milliseconds**:
  `turnSpacingMs: 0` and no LLM client.

### Degrade, never hang

Every wait is bounded, and no failure mode leaves the cog unactuated.

| Failure | What happens |
|---|---|
| Attempt 1 times out, errors, or returns text with no usable JSON | it goes into the retry; the log says **`will retry`**, never `falling back` (the pommerman 0.1.1 wording rule — only a genuine fallback may say `falling back`, because phase 60 greps for it) |
| The retry also fails | the seat takes the **`pathfinder`** plan for that turn; a `fallback` record with `cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard}` and a ≤ 200-rune `detail` is written to the replay; `fallbackTurns += 1`; the game log prints `falling back` |
| A provider 429 with no other candidate model | the retry is **skipped** (it cannot land) and the seat falls straight to `pathfinder`, `cause = throttled` |
| No `ANTHROPIC_API_KEY` at all (certification, CI) | the client is `disabled`; every turn records `cause = no_credentials`, so `llmTurns 0 / fallbackTurns N` is countable rather than silently zero (the starter's `decide.nim:358-372` fix, kept) |
| A reply parses but `moves` is illegal | **repaired, never rejected** (§Server → reply schema); `ordersRejected += 1` |
| A reply parses but `moves` is empty after filtering | it becomes `"."` — one wait frame. The cog is always actuated |
| The seat never connects, or connects and never answers | the cog plays `pathfinder` for the whole gauntlet, `deadSeats[0] = true`, and exactly one closed-schema `{"message", "failed_policy_index"}` payload is POSTed to `COGAME_PLAYER_FAILURE_URI` |
| A generator draws 40 invalid levels in a row | the archetype's committed `FallbackLevel` is used and a `gen_fallback` record is written. The episode never loops |
| The wall clock approaches | the budget guard switches to `pathfinder` and the episode finishes `complete` |
| Everything else | `wallClockBudgetSeconds = 660` stops the loop and settles `deadline` with real numbers, unplayed levels scored 0 |

**The fallback path and the `pathfinder` baseline resolve to the same proc**, so they cannot drift
(`tests/test_procgen_control.nim` asserts it).

### The two scripted baselines

Both emit the **same object an LLM emits** (`{"moves", "say", "notes"}`), on the same cadence, so they
are strictly comparable and one validator covers both — which is what makes the bounded-orders test
meaningful. Both are **pure functions of the observation state** with no RNG.

Shared skeleton, in `src/procgen/baselines.nim`:

```
target = nearest uncollected Gem/Pellet by bfsDist over the archetype's passability
         (Dirt costs digCost in `miner`), else the exit if collected == collectTotal
path   = the BFS shortest path to target, ties broken in the fixed order L, R, U, D
syms   = symbolsFor(path[0 ..< framesPerTurn])      # the SAME proc applyAction inverts
apply the archetype veto to syms (below); drop from the first vetoed symbol onward
if syms is empty -> the single safest symbol; if none is safe -> "."
```

Archetype vetoes, all computed with the **resolver's own** `passable` / `hunterStep` / `willFall`
procs, never a second copy:

- `chaser`: simulate the hunters forward with `hunterStep` alongside the plan; veto the first symbol
  whose post-frame cog cell is within Chebyshev 1 of any hunter. `X` (dash) is proposed when it
  strictly increases the distance to the nearest hunter and the cooldown is clear.
- `climber`: a symbol that would start a fall deeper than `fallLethal` is vetoed; a step onto a
  `Spike` is vetoed; a step that needs a gap crossed emits `X` then the horizontal symbol.
- `miner`: a symbol that would leave the cog under a boulder with `Empty` between is vetoed; `X` is
  proposed to dig sideways out from under one.
- `maze`: no veto — there are no hazards.

| Tunable | `pathfinder` | `scavenger` |
|---|---|---|
| `lookaheadFrames` (hunter/boulder projection) | 6 (the whole plan) | 1 |
| `digCost` (BFS weight of a `Dirt` tile in `miner`) | 3 | 1 |
| `commitFrames` (symbols emitted per turn) | up to 6, truncated at the first veto | always 6 |
| `detourBudget` (extra BFS steps accepted to avoid a hazard) | 6 | 0 |
| `exitFirst` (route to the exit while collectibles remain) | never | never |

- **`pathfinder`** is the careful one: full-plan projection, expensive digs, short commitments. It is
  the certification player, the per-turn fallback, the default for an unregistered seat, and filler #1.
- **`scavenger`** is visibly greedier: one-frame lookahead, cheap digs, always six symbols committed.
  It scores higher on `maze` (no hazards, so commitment is free) and dies far more on `chaser` and
  `miner`. It is filler #2 and the thing a champion should beat.

Neither ever emits `say` or `notes` (both empty), which is why the viewer's text chrome needs the
renderer fixture in §Tests: a CI replay contains no LLM text at all (the cogchemists 2026-08-24 scar).

Cost per call: one BFS over ≤ 135 tiles plus ≤ 6 × 3 hunter projections — microseconds. The tunables
are **swept, not guessed**: `tools/tune_baselines.nim` plays a bounded matrix over a fixed 24-episode
ladder (all three difficulties, seeds pinned) and writes `tools/ci/baseline_tuning.json`; `ci.yml`
re-runs the sweep with `--check`, and `tests/test_procgen_control.nim` asserts the shipped defaults
equal the recorded pick and that `pathfinder`'s mean `scores[0]` over that ladder beats
`scavenger`'s by a margin inside **`[+0.05, +0.45]`**.

### The system prompt (fixed, identical for both champions)

Lives in `src/procgen/llm.nim` as `SystemPrompt*`, replacing the starter's paintball const — the only
game-specific text in that file, which is otherwise kept structurally verbatim (§Sim module).

```
You are one cog playing a gauntlet of eight small tile levels, one after another. Each
level is 15 tiles wide and 9 tall and was built by a generator from a number you are not
told. You have TEN decisions per level and each decision is a plan of up to SIX moves that
run one after another before you are asked again.
Coordinates are [x, y] with x growing RIGHT and y growing DOWN, so "U" is y-1, "D" is y+1,
"L" is x-1, "R" is x+1, and [0,0] is the top-left tile.
The action alphabet is exactly six letters: L R U D X . ("." is wait.) What X does depends
on the level kind: maze - nothing; chaser - dash two tiles the way you last faced; climber
- jump, which lifts you two tiles while you keep moving sideways; miner - dig the dirt tile
you last faced without moving.
The map is drawn for you as rows of characters. '#' bedrock (never passable), ':' dirt
(only miner can dig it), 'O' boulder (miner can push it sideways; it falls when nothing is
under it and it kills you if it lands on you), '*' gem, 'o' pellet, '+' locked exit,
'E' open exit, '=' platform, 'H' ladder, '^' spikes (lethal), '.' empty, '@' you, 'X' a
hunter.
The exit is LOCKED until you have taken every gem or pellet on the level. Then it opens.
Reaching an open exit clears the level.
Your plan runs blind, but it is cut short the moment a hunter comes next to you, a boulder
starts falling above you, or you go into free fall - you are asked again immediately, so a
six-move plan is not a six-move gamble.
Scoring, per level: 700 points x (collectibles taken / total), plus up to 200 for how much
closer to the exit you ever got than where you started, plus 100 for reaching the exit.
1000 is a perfect level. Your EPISODE SCORE is the average over four of the eight levels -
and you are not told which four. Assume every level counts, because for scoring purposes
four of them do and you cannot tell them apart.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"moves":"<=6 letters from LRUDX. , executed in order>",
 "say":"<=24 chars, spectators only, never read by anyone in the game",
 "notes":"<=160 chars, private, handed back to you next turn"}
"moves" is your plan. Anything outside the six letters is dropped; an empty plan becomes
one wait. Use "notes" to carry what you worked out about this level - the map is redrawn
every turn but your reasoning is not.
```

### Champion #1 — `procgen-cartographer` (owner **daveey**), `PLAYER_PROMPT`

```
Solve the level as a route, not as a reflex. Before you move, read the map rows and decide
the ORDER you will take the collectibles in: always the one whose path from where you
stand is shortest, then re-decide from there. Write that order into "notes" as a list of
coordinates and follow it across turns, so you never re-plan from scratch and never oscillate
between two gems.
Spend your six moves on ONE leg of that route. If a leg is longer than six moves, take six
and write the remaining waypoint into "notes"; do not try to be clever in the last two moves
of a plan.
In maze levels commit hard: there is nothing that can hurt you, so use all six moves every
turn and never wait. Dead ends cost you two moves; hesitation costs you a whole turn.
In chaser levels never plan a move that ends within two tiles of a hunter's current position,
because a hunter takes two steps for every three of yours. Prefer routes that keep a pillar
between you and the nearest hunter, and keep the dash for the single move that breaks a
pincer, not for making progress.
In climber levels treat every gap as a jump you must set up: face the way you are going with
one horizontal move, then X, then the horizontal moves that carry you across. Never step onto
'^'. Never walk off a platform you cannot see the landing for; if the map shows more than
four empty tiles below you, that fall is fatal.
In miner levels dig DOWN and SIDEWAYS, never straight up under an 'O'. Before you take a gem
with a boulder above it, dig out a sideways escape tile first and put its coordinate in
"notes". A boulder you pushed is a boulder that will fall the moment you leave the tile
under it.
When every collectible is gone, stop optimising and walk the shortest path to 'E'.
```

### Champion #2 — `procgen-scrambler` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Assume you have never seen this level and never will again, so buy information cheaply and
bank the guaranteed points early. The first 700 points are collectibles and they are the
only points that are certain; the 200 for approach and the 100 for the exit are what you take
if the level lets you.
Turn one is a survey turn in any level with hazards: take three or four moves toward the
nearest collectible, not six, and use the extra turn to see what moved. In maze levels there
is nothing to survey, so take six every time.
Rank the collectibles by (distance) + (danger), where danger is 4 per hunter within four
tiles, 4 per boulder directly above the tile, and 4 per spike adjacent to the approach. Take
the cheapest first. If two are equal, take the one that leaves you closer to the exit tile,
because approach points are free points you keep even if you die later.
Never spend more than two turns on a single collectible. If it has cost you two turns it is
guarded, and the other three are worth more than it is. Say so in "notes" and abandon it.
If you are down to one collectible and it is genuinely lethal to reach, do not reach it.
Walk toward the locked exit instead and park next to it: 700x3/4 plus a full 200 for approach
beats 700 plus a death at zero approach.
In chaser levels move along walls, not through the middle, and count that a hunter closes one
tile every turn and a half. In miner levels never stand under a column of dirt with an 'O'
above it, even two tiles up.
Put one concrete fact in "notes" every turn - which gem you abandoned, which tile is a trap,
which way the hunters came from. That note is the only memory you have.
```

---

## Sim module

Nim, in the starter's layout, under `src/procgen/`. `src/procgen/sim.nim` imports and **re-exports**
all of them, so `import procgen/sim` still sees everything — the starter's rule. `GameVersion*` in
`src/procgen/sim_types.nim` is reset to `"1"` with a fresh changelog comment in the starter's
`GVnn (short rule name): HEADLINE` shape.

### Kept, by path

**Byte-for-byte (a test pins the sha256 of each):**

| Path | Note |
|---|---|
| `client/chrome_common.js` | **40 022 bytes**, sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, unedited, unreformatted (§Viewer) |
| `tools/wasm_replay_smoke.cjs` | headless-node run of the exact emitted wasm module; only the module filename string changes |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py`, `tools/ci/test_next_coworld_version.py` | unchanged |
| `tests/config.nims` (`--path:"../src"`) | unchanged |

**Structurally verbatim (forked in place, the named parts asserted identical to the starter's text):**

| Path (starter → here) | What is kept, what changes |
|---|---|
| `src/ctf/llm.nim` → `src/procgen/llm.nim` | the whole Bedrock/Anthropic transport — `resolveApiKey`, `bedrockModelIds`, `tryNextBedrockModel`, `bedrockUrl`, `newLlmClient`, `requestFor`, `textOf` (including the `max_tokens`-cut-off raise), `operatorBlock`, `userMessage` — kept and pinned function-by-function by `tests/test_procgen_llm.nim`. **Only the `SystemPrompt*` const is replaced** (§Decisions). `maxOutputTokens` stays at **900** (the playbook's Bedrock note) |
| `src/ctf/directives.nim` → `src/procgen/directives.nim` | `truncateRunes`, `sanitizeSay`, `sanitizeNote`, `extractJsonObject` lifted verbatim, including the rune-discipline doc comment and the `{`/`}` exclusion in `sanitizeSay` (the replay chat stream tells a control record from a shout by a leading brace). The `Intent` enum and `CogOrder` are replaced by `PlanOrder` (§Server → reply schema) |
| `src/ctf/decide.nim` → `src/procgen/decide.nim` | the whole per-turn loop shape: the budget guard (`decide.nim:335-346`), the rate floor (`384-392`), the batch call with `attempt1Ms`/`retryMs`/`turnBudgetMs` (`394-470`), the throttle fail-fast (`472-479`), the final fallback ladder and its `cause` enum (`481-492`), and the exact `falling back` log phrase phase 60 greps. **Only `seatViewJson`, the parse call and the fallback baseline change** |
| `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js` | kept; only the module filename (`ctf_replay.js` → `procgen_replay.js`) and the exported symbol prefix (`_ctf_*` → `_procgen_*`) are renamed. `data-replay-loaded` / `data-replay-error` are the starter's own signals, inherited unchanged (§Viewer) |
| `replay-viewer/config.nims` | kept; `-o` target renamed, `EXPORTED_FUNCTIONS` renamed, everything else (including **`-s ABORTING_MALLOC=1`** and its comment at lines 35-41) unchanged (§Viewer) |
| `tools/build_replay_viewer.sh` | kept; image tag and the `docker cp` source path (`/workspace/ctf/replay-viewer/dist/.` → `/workspace/procgen/replay-viewer/dist/.`) changed. It already carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix (line 20) and the buildx / `--platform linux/amd64` handling. Committed **executable** (`coworld build` hard-requires `os.X_OK`) |
| `Dockerfile`, `Dockerfile.replay-viewer` | structure verbatim; §Packaging lists the named edits |

**Forked and retargeted in place:** `sim_types.nim`, `sim_config.nim`, `sim_state.nim`, `roster.nim`,
`sim.nim`, `server.nim`, `global.nim`, `broadcast.nim`, `events.nim`, `labels.nim`, `control.nim`,
`baselines.nim`, `replays.nim`, `replay_runtime.nim`, `wire_constants.nim`,
`rig_art.nim` → `procgen_art.nim`; `client/broadcast_core.js`, `client/replay_broadcast.html`;
`replay-viewer/ctf_replay.nim` → `replay-viewer/procgen_replay.nim`; `tools/gen_wire_constants.nim`,
`tools/replay_summary.py`, `tools/tune_baselines.nim`, `tools/record_fixture.sh`,
`tools/extract_events.nim`, `tools/benchmark_game.nim`, `tools/scan_event_seeds.sh`.

### Deleted (with their tests, tools, docs and config surfaces), not disabled

`src/ctf/arena.nim` (3849 lines of continuous-2-D map geometry, the terrain generator, its
validators, `mapSpec` and the process-global map install), `map_art.nim`, `map_pool.nim`,
`mapgen_styles.nim`, `paint.nim`; every weapon, bullet, hit point, life, respawn, spray, paint grid,
hill, heart, flag, grenade, med kit, shield, barrier, trench, puddle, perk, handicap, achievement,
team, four-team and campaign mechanic; the fog-of-war shadowcast and the whole vision system (the
level is fully observed); the first-person PIP; `tools/map_editor*`, `tools/mapkit.nim`,
`tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `tools/map_render.nim`,
`tools/build_pool_review.py`, `docs/MAPKIT.md`, `docs/pool-review.html`,
`docs/designs/map-editor.md`; `client/league_replayer.html` and, with it, the `league.html` `sed`
splice and its four `test -f`/`grep -q` assertions in `Dockerfile.replay-viewer`; `players/`,
`caos/`, `caos-tools/`, `arena/`; and every `tests/test_*` that covers a deleted mechanic. Deleted,
not gated: a gate-off config that still compiles a paint grid is 8000 lines of code nobody in this
repo can reason about.

### New modules

| Module | Contents |
|---|---|
| `src/procgen/tiles.nim` | the grid: `Tile` enum and its glyph/passability tables, `Grid{w = 15, h = 9, cells}`, `step(cell, dir)`, `inBounds`, `cellIndex`, and the `Dir` enum (`dL = 0, dR = 1, dU = 2, dD = 3` — the wire order of the replay's action byte, with `4 = X`, `5 = .`) |
| `src/procgen/gen.nim` | the four generators, each `proc generate<Kind>(rng: var Rng, d: Difficulty): Grid`, plus `generateLevel(kind, seed, difficulty)` with the validator and the bounded 40-attempt redraw, and the four committed `FallbackLevel` consts |
| `src/procgen/levels.nim` | `LevelKind`, the difficulty tables, `applyAction`, `passable`, `hunterStep`, `willFall`, and `stepFrame` implementing frame-resolution steps 1–10 verbatim. **`applyAction`, `passable`, `hunterStep` and `willFall` have exactly one implementation each** and are called by the resolver, the observation builder, both baselines, the validator and the viewer pre-scan, so no consumer can disagree with the rules (the escrow 2026-08-23 lesson) |
| `src/procgen/path.nim` | `bfsDist(from, to, passPred)` and `bfsPath(from, to, passPred)` — one bounded BFS over ≤ 135 tiles, plus `symbolsFor(path)`. Five callers, one implementation |
| `src/procgen/seeds.nim` | `TrainSeeds` (128 published seeds), `drawGauntletPlan(seed, levelCount)`, and the `TestSeedLow = 100000` / `TestSeedHigh = 2147483646` bounds |
| `src/procgen/scoring.nim` | `returnMilli`, `unseenMilli`, `seenMilli`, `gapMilli` — the formulas of §Scoring and nothing else |
| `src/procgen/upstream.nim` | the transcribed upstream facts and the five divergences with citations, asserted by `tests/test_procgen_upstream.nim` |

### Danger interrupt

Evaluated at the end of frame-resolution step 9, only when `interruptOnDanger` (default **true**).
The remaining symbols of the plan are discarded, `planInterrupts += 1`, and the turn ends, when:

- `chaser`: any hunter is within **Chebyshev distance 1** of the cog; or
- `miner`: a boulder marked `falling` is in the cog's column, at most **3** tiles above it, with only
  `Empty` between; or
- `climber`: the cog is in free fall with `fallDepth >= 2`; or
- any archetype: the cog stands adjacent to a `Spike` it did not see at plan time.

`maze` therefore never interrupts, and a `maze` plan always runs all six frames. The interrupt is
recorded in the turn's `directive` chat record as `executed: k` (how many symbols actually ran), so
the viewer can draw the unspent tail of the plan greyed out and `replay_summary.py` can report it.
It **never** changes the score and never mutates the level; it only ends a turn early.

### Determinism

All arithmetic is integer; `tests/test_procgen_sim.nim` greps
`src/procgen/{tiles,gen,levels,path,scoring}.nim` for float literals, `/` and `sqrt` and asserts none.
Three RNG streams, all the starter's integer generator from `sim_state.nim`:

- `setupRng` (seeded `seed`) — picks which training seeds are used and shuffles the play order.
- `testRng` (seeded `seed xor 0x7E57`) — draws the held-out seeds and nothing else.
- `levelRng` (seeded from a **level seed alone**) — every draw inside a generator.

Separating them is what makes a level a pure function of its own seed regardless of the episode, and
what makes `tests/test_procgen_seeding.nim`'s "no seat behaviour changes any stream" assertion
meaningful. All three are drawn **before any seat connects**.

Native ↔ wasm: the same `src/procgen/` modules compile both ways; `tools/wasm_replay_smoke.cjs` runs
the **exact emitted** module against the committed fixtures, because wasm32-only failures (integer
traps, address-space exhaustion) are invisible to the native 64-bit shards.
`tests/test_procgen_gen.nim`'s cross-target case asserts `generateLevel` produces identical grids in
both.

### The named edits to the forked server/roster/global

**`server.nim` — four edits.** (1) The tick loop becomes a **frame** loop wrapped in a **level**
loop: one decision round per turn, up to `framesPerTurn` `stepFrame` calls per turn, `fastMode`
always on, no frame pacing; `maxTicks`/`startWaitTicks`/`gameOverTicks`/`lobbyJoinTimeoutTicks`
become `levelCount`/`turnsPerLevel`/`framesPerTurn`/`gameOverFrames`/`lobbyJoinTimeoutSeconds` — the
last in **seconds**, because a `fastMode` frame has no wall-clock meaning. (2) The wall-clock check at
the top of the loop (`server.nim:1407-1417`) is kept as-is, reading `wallClockBudgetSeconds`.
(3) The certifier's browser probes stay registered **before** any catch-all asset route and keep
answering for the `gameOverFrames` grace after artifacts are written:
`GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket — the
flatland 0.1.1 scar), `GET /client/global`, the `/global` websocket's first message, and `/healthz`
(the lantern 0.1.1 and 0.1.3 scars). (4) `websocketHandler` **keeps its `Ping → Pong` branch**
(`socket.send(message.data, Pong)`) and guards nothing else — a `kind != TextMessage` guard drops the
player's binary registration frames (the lux-ai 0.1.0 / snake-royale 0.1.0 scar, twice observed).
Global broadcasts stay fire-and-forget so a slow viewer can never stall the episode.

**`roster.nim` — two edits.** (1) Teams are deleted: there is one seat, `slots` is gone from the
runtime config, and `cogAlias(0)` returns `COG-alpha` from the starter's `IdentityNames` array
(`roster.nim:64`). (2) A seat with no `register` record is logged loudly
(`ERROR: seat 0 never registered — playing pathfinder`) and flagged `deadSeats[0]`.

**`global.nim` — three edits.** (1) Every weapon/paint/flag/hill/FPV draw path and its wire fields are
deleted. (2) The broadcast state carries the level: `levelIndex`, `levelCount`, `kind`, `split`,
`difficulty`, `grid` (run-length encoded tile bytes), `cog{at, lastDir, jumpFuel, fallDepth,
dashCooldown}`, `hunters[]`, `falling[]`, `collected`, `collectTotal`, `exitOpen`, `frame`,
`levelTurn`, `plan` (the current turn's symbols and how many have run), `returns[]`, `bubbles`.
(3) `window.CTF_WIRE` becomes `window.PROCGEN_WIRE`, emitted by the forked
`tools/gen_wire_constants.nim`.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local developer replay mode (never declared to
the platform); `HOST`/`PORT`; the player socket at `/player?slot=0&token=<t>`, closed unless the token
matches the seat.

### Per-seat observation — exactly what is visible and what is hidden

Built by `seatViewJson` (the starter's proc, retargeted), in tiles, integers only:

```json
{
  "level": {"index": 3, "of": 8, "kind": "miner", "w": 15, "h": 9, "difficulty": "standard"},
  "turn": 4, "turns_left_this_level": 6, "frame": 18, "frames_per_turn": 6,
  "map": [
    "###############",
    "#@:::*::::::::#",
    "#:::##::O:::::#",
    "#::::::::::::*#",
    "#:O:::###:::::#",
    "#::::::*::::::#",
    "#:::::::::::O:#",
    "#*::::::::::+:#",
    "###############"
  ],
  "legend": {"#":"bedrock","::":"dirt","O":"boulder","*":"gem","+":"locked exit",
             "E":"open exit","=":"platform","H":"ladder","^":"spikes",".":"empty",
             "@":"you","X":"hunter"},
  "you": {"at": [1,1], "last_dir": "R", "alive": true,
          "jump_fuel": 0, "fall_depth": 0, "dash_cooldown": 0},
  "collected": 0, "collect_total": 4, "exit_open": false, "exit_at": [12,7],
  "exit_distance": 19, "nearest_gem": [5,1], "nearest_gem_distance": 4,
  "hunters": [],
  "falling": [],
  "actions": [
    {"a":"L","to":[0,1],"legal":false,"effect":"blocked","kills":false},
    {"a":"R","to":[2,1],"legal":true, "effect":"dig","kills":false},
    {"a":"U","to":[1,0],"legal":false,"effect":"blocked","kills":false},
    {"a":"D","to":[1,2],"legal":true, "effect":"dig","kills":false},
    {"a":"X","to":[2,1],"legal":true, "effect":"dig_in_place","kills":false},
    {"a":".","to":[1,1],"legal":true, "effect":"wait","kills":false}
  ],
  "levels_done": [
    {"index":1,"kind":"maze","outcome":"cleared","return":1000},
    {"index":2,"kind":"chaser","outcome":"died","return":425}
  ],
  "your_notes": "gem at 5,1 is clean; boulder at 8,2 sits over the direct line"
}
```

- `map[]` is always exactly 9 strings of exactly 15 characters, top row first, using the glyph table
  of §The game → The board. It is the whole level: **this game is fully observed**.
- `actions[]` always has exactly six entries, in the wire order `L, R, U, D, X, .`, and it is the
  **precomputed legal choice set**: `legal`, `to`, `effect ∈ {move, dig, dig_in_place, push, jump,
  dash, climb, collect, exit, wait, blocked}` and `kills` all come from the resolver's own
  `applyAction`/`passable` procs. One predicate, five callers (§Sim module) — the observation can
  never claim something the resolver disagrees with, which is the escrow fix for formal-output
  fallback rates.
- `levels_done[]` gives the outcome and return of every completed level, so a policy can pace itself.
- `your_notes` is the seat's own previous `notes`, handed back verbatim.

**Hidden from the seat**, explicitly and by test:

- the **level's seed**, and every other level's seed;
- whether this level (or any level) is **`seen` or `unseen`**, and the counts of each;
- the `TrainSeeds` membership of the current seed;
- the **kind, seed and split of levels not yet played** (`levels_done` lists only completed ones);
- the `setupRng` / `testRng` / `levelRng` states and futures;
- the seat's **real policy/player name** (only `COG-alpha` appears anywhere);
- the running `seenMilli` / `unseenMilli` / `gapMilli` and therefore `scores[0]`.

Nothing about the current level's geometry is hidden — that is the "64×64 pixels of the whole level"
property of Procgen's fully-observed games, carried across.

### Reply schema and per-field caps

One object per turn:

```json
{"moves":"RRXDDL","say":"digging under the rock","notes":"gem 4 needs a side escape at 11,6"}
```

| Field | Type | Cap | Repair on a bad value |
|---|---|---|---|
| `moves` | string over the alphabet `L R U D X .` | **6 runes** | uppercased; characters outside the six are **dropped**; longer than 6 → `truncateRunes(6)` on a **rune boundary**; empty or absent after filtering → `"."`; a non-string → `"."`. Any of these increments `ordersRejected` |
| `say` | string, spectator-only | **24 runes** (`MaxSayRunes`) | `truncateRunes(24)` on a **rune boundary**, then the starter's printable-ASCII shout filter (which also strips `{` and `}` so a shout can never be mistaken for a control record) |
| `notes` | string, private | **160 runes** (`MaxNoteRunes`) | `sanitizeNote` — newlines collapsed to spaces, then `truncateRunes(160)` on a **rune boundary** |

The whole reply is read with a **4096-byte** cap and the JSON is extracted by the starter's tolerant
`extractJsonObject` (markdown fences and surrounding prose survive). `PLAYER_PROMPT` is itself capped
at `MaxPromptRunes = 4000`, rune-truncated, and is never echoed into the replay or the results.

**Every truncation in this game lands on a rune boundary.** No string that reaches the replay is ever
sliced by byte index — a byte-truncated multi-byte character renders in a browser and then fails a
strict UTF-8 parser, which is the class of bug that makes a replay unreadable to everything but the
one lenient viewer (`playbooks/make-coworld.md` gotcha table).

The validator **repairs, never rejects**: there is no reply that leaves the cog unactuated.

### Results document (closed schema; `procgenResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":           ["daveey"],
  "aliases":         ["COG-alpha"],
  "scores":          [0.570],
  "win":             [false],
  "reason":          "complete",
  "endRule":         "gauntlet_complete",
  "variant":         "gauntlet",
  "difficulty":      "standard",
  "seed":            1734029581,
  "levelCount":      8,
  "levelKinds":      ["maze","chaser","climber","miner","chaser","maze","miner","climber"],
  "levelSplit":      ["seen","unseen","seen","unseen","seen","unseen","unseen","seen"],
  "levelSeeds":      [1017, 1836471221, 3004, 908314772, 2029, 415521080, 1755930411, 3031],
  "levelReturns":    [1000, 425, 850, 300, 700, 1000, 555, 640],
  "levelOutcome":    ["cleared","died","cleared","timeup","cleared","cleared","died","cleared"],
  "levelDeathCause": ["","caught","","","","","crushed",""],
  "levelFrames":     [38, 26, 51, 60, 44, 47, 19, 55],
  "levelCollected":  [4, 3, 4, 1, 8, 4, 2, 4],
  "levelCollectTotal":[4, 8, 4, 4, 8, 4, 4, 4],
  "seenMilli":       797,
  "unseenMilli":     570,
  "gapMilli":        227,
  "seenCleared":     4,
  "unseenCleared":   2,
  "policyKinds":     ["llm"],
  "llmTurns":        63,
  "fallbackTurns":   2,
  "ordersRejected":  1,
  "planInterrupts":  11,
  "genFallbacks":    0,
  "deadSeats":       [false],
  "stopDetail":      ""
}
```

Every **seat-indexed** array (`names`, `aliases`, `scores`, `win`, `policyKinds`, `deadSeats`) is
exactly **1** long; every **level-indexed** array is exactly `levelCount` long. Adding a key means
updating `procgenResultsJson`, the manifest's `results_schema` and `tools/ci/docker_smoke.sh`'s
expected-key set **in the same commit** — Coworld schemas are closed and undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDPGN`** format (`replays.nim`'s `CtfReplayMagic`
renamed). The static wasm viewer parses exactly this; a JSON replay would mean rewriting
`replays.nim`, `replay_runtime.nim`, `static_replay_worker.js` and `wasm_replay_smoke.cjs` — the
machinery this fork exists to reuse (the knights-archers precedent). The consequences are handled
explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (template lines 31/57/319).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"procgen/v1","gameVersion":"1","seed":…,"variant":…,"difficulty":…,
  "levelKinds":[…],"levelSeeds":[…],"levelSplit":[…],"names":[…],"aliases":[…],
  "policyKinds":[…],"frameCount":…,"actions":[…],"says":[…],"notes_count":…,"fallbacks":N,
  "interrupts":N,"results":{…}}` — by brace-matching the config JSON from the first `{` (the technique
  the starter's `AGENTS.md` documents for prod forensics) and decoding the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                      # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.scores, .results.levelReturns' /tmp/ep.json
  jq -r '[.actions[]|select(.source=="llm")]|length, .fallbacks, (.says|length)' /tmp/ep.json
  ```
  Require `protocol == "procgen/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.levelSeeds | length == results.levelCount`, every `levelSplit` entry in
  `{seen, unseen}` with both present, a non-zero `results.unseenMilli`, and the seat's turns with
  `source == "llm"`, real plans and non-empty `says` — not all fallbacks.

Everything the viewer needs is in the bytes; **no server is contacted except S3 for the `.replay`
file**:

| Replay content | Carries |
|---|---|
| header | magic `COWLDPGN`, format version, `gameName procgen`, `gameVersion "1"` |
| config JSON | `seed`, `variant`, `difficulty`, `levelCount`, `turnsPerLevel`, `framesPerTurn`, `boardW 15`, `boardH 9`, `cellPx 32`, **`levelKinds`**, **`levelSeeds`**, **`levelSplit`**, `interruptOnDanger`, `fallLethal`, `num_agents`, `players[].name` (**real names**), `aliases`, `renderFramesPerStep`, `sayFrames`, `attempt1Ms`, `retryMs`, `turnBudgetMs`, `turnSpacingMs`, `wallClockBudgetSeconds`, `gameOverFrames`, `fastMode`, `showPlayerLabels` |
| joins / leaves | `name` (real policy name), `slot 0`, `token` |
| action log | **one byte per sim frame** — `0=L, 1=R, 2=U, 3=D, 4=X, 5=., 255=level boundary`. This game's entire input log |
| chats | `register` / `directive` / `fallback` / `gen_fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` **per sim frame** — the integrity chain the viewer checks (`#mmwarn` on divergence) |

**The level grids are not recorded** and do not need to be: `generateLevel(kind, seed, difficulty)` is
a pure function, so the wasm module re-generates all eight levels from `levelKinds` + `levelSeeds` +
`difficulty`, and the per-frame `gameHash` proves it — which is exactly the "deterministic replay
verification" the idea's integrity note asks for. `tests/test_procgen_replay.nim` asserts the
re-derivation is hash-identical **at every frame including the stop frame** (the particle-worlds
scar).

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `level`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `moves`, `executed` (how many symbols ran), `repaired` (bool), `say` (≤ 24 runes), `view` (the observation minus `your_notes`) |
| `fallback` | `turn`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `gen_fallback` | `level`, `kind`, `seed` — the 41st-attempt hand-authored level |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `frame`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end (the starter's `resultRecord`) |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay.
**A closed enum of sixteen kinds:**

`gamestart` `{levelCount, difficulty, variant}`;
`levelstart` `{index, of, kind, split, seed}`;
`plan` `{turn, moves, source}`;
`step` `{frame, action, from, to, blocked}`;
`collect` `{at, kind, collected, total}`;
`dig` `{at}`;
`push` `{from, to}`;
`fall` `{entity, from, to}`;
`hunter` `{id, from, to}`;
`interrupt` `{frame, cause, unspent}`;
`death` `{frame, cause, at}`;
`exitopen` `{at, frame}`;
`levelend` `{index, outcome, returnMilli, frames, collected, total}`;
`say` `{text, x, y}`;
`fallback` `{turn, cause}`;
`gauntletend` `{seenMilli, unseenMilli, gapMilli, score}`.

The episode's final `end` state is carried by `gauntletend` plus the starter's own `end`
`{reason, endRule, scores}` — **seventeen kinds in total** counting `end`.
`tests/test_procgen_events.nim` asserts the emitted set equals **exactly** this list, and that every
kind the appended viewer block consumes is in it.

**Beats** — the scrubber markers, and the only kinds the appended game block turns into buttons:
**`levelstart`, `collect`, `exitopen`, `death`, `levelend`, `fallback`, `gauntletend`.** To keep a
480-frame scrubber readable, a `collect` beat is emitted only for a level's **first** collectible and
for the one that opens the exit; the rest drive the feed only. `gamestart`, `plan`, `step`, `dig`,
`push`, `fall`, `hunter`, `interrupt`, `say` and `end` never make beats.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `LevelStart, Plan, Step, Collect, Dig, Push, Fall, Hunter, Interrupt,
Death, ExitOpen, LevelEnd, Say, Directive, Fallback, GauntletEnd` and the mandatory trailing summary
row (`type`, `frames`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook (§Sim module) building `Dockerfile.replay-viewer`'s `replay-viewer-builder`
target and copying the dist out. It stays committed **executable**. No `/client/replay` live-server
viewer is ever declared to the platform; the game still serves `/client/replay` locally for
developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/procgen_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html` by `Dockerfile.replay-viewer`'s marker `sed`)
ALL come from ONE starter: `coworld-ctf`** — this repo's own starter, for all four files. **Never a
mixture.** Splicing one starter's shell onto another's emscripten link flags
(`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer silently
(cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one piece:

- the Worker sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`), so the module is
  emitted **non-modularized** as `procgen_replay.js`;
- `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang` through `emcc`, `--mm:arc
  --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`, `--preload-file data@data`,
  `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable, and the starter's own comment
  at lines 35-41 explaining it is kept verbatim: with `-d:useMalloc` Nim never checks malloc for nil
  and wasm32 has no memory protection, so a failed allocation would write a seq header through nil
  into address 0 and silently corrupt the module's own globals), `-s FILESYSTEM=1`,
  `-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, and
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_procgen_load_replay,_procgen_frame,_procgen_input,
  _procgen_packet_ptr,_procgen_packet_len,_procgen_mismatch_tick,_procgen_error_ptr,
  _procgen_error_len,_procgen_stage_ptr,_procgen_stage_len`;
- `static_replay_worker.js` does
  `importScripts('./wire_constants.js', './broadcast_core.js', './procgen_replay.js')` in that order
  (the starter's line 239, renamed only).

`procgen_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress
buffer that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`,
and the `emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running
module destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `procgen_load_replay` re-generates all eight levels and re-simulates the
  whole episode once headlessly (≤ 480 frames of integer work over ≤ 135 tiles, plus one bounded BFS
  per frame — under two milliseconds in wasm), and records the per-level return series, the per-level
  frame spans, every beat frame and the lull spans, then resets and renders frame 0. That is what lets
  the **split bar**, the clock and the scrubber beats draw at **full width on the first frame**
  instead of growing in.
- `procgen_mismatch_tick` returns `checkReplayHash`'s divergence **frame**, or `−1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (starter line 161) — posted by the Worker
only *after* `ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the
attribute means "a frame is on the canvas", not "a file was fetched". On failure it sets
**`data-replay-error`** on `<html>` with the message, in `showFailure()` (starter lines 8-20). Both
are coworld-ctf's own signals, inherited unchanged — this fork adds neither and removes neither. The
`coworld-replay` postMessage bridge's `ready` is posted **from a callback fired after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus `3c11c953`,
2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** — 40 022 bytes, sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`. Not edited, not reformatted;
  `tests/test_procgen_viewer.nim` pins that sha256 as a literal. Everything this game adds lives in the
  appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats` / `renderClock` /
  `renderTransport` / `ingestLullSpans` / `renderMomentum` remain, and `ingestBeats` ignores kinds it
  does not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (lines 4276-4321), transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density
  system are untouched, and the block is installed through the starter's **own splice hook**:
  `window.PaintballChrome` is renamed `window.ProcgenChrome` and its `install(PB_CTX)` /
  `frame(s, ctx, jumped)` / `event(e, s, ctx)` entry points (starter lines 4337, 2075, 3480-3481,
  defined at 4651) keep the same signatures and the same `PB_CTX` contents
  (`$, C, esc, fmt, send, pushFeed, banner, getState, …`, lines 4330-4336). The appended block replaces
  only the *contents* of the scorebug plate, adds the split bar and the plan trail, and retargets the
  feed rows, the beat rendering, the momentum series and the endcard columns.
  `tests/test_procgen_viewer.nim` asserts the file begins with the starter's bytes up to the
  documented splice marker and only appends after it.
- **`client/broadcast_core.js` is forked** — it is paintbot's continuous-2-D draw layer and this game
  is a tile grid. Kept and pinned function-by-function against the starter's text: the canvas/DPR
  sizing, `relayout()`, the camera, the feed queue and **`pushFeed` including its signature**
  (`replay_broadcast.html:3558` — the cogball 0.1.4 latch scar: a signature drift threw mid-replay and
  latched `static_replay.js` into `failed`), `banner`, the beat and lull machinery, the endcard
  builder, the speed chips, the `?embed=1` path, the shout-bubble renderer, and the
  `window.CTF_WIRE` → `window.PROCGEN_WIRE` rename emitted by `tools/gen_wire_constants.nim`.
  Deleted: every weapon, paint, hill, flag and fog draw call, the FPV pipeline and `attachMinimap`'s
  callers. Added: `drawTiles`, `drawCog` (four facings, a jump squash and a dig pose), `drawEntities`
  (gems, pellets, boulders with a fall streak, hunters with eyes, spikes), `drawExit` (barred vs lit),
  `drawPlanTrail`, `drawSplitBar`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `core.attachMinimap($('minimap-canvas'))` call
    (`replay_broadcast.html:4200`). **Zoom decision: DROPPED ENTIRELY.** Every level in every
    archetype and every variant is the same fixed 15 × 9 rectangle with no off-frame area;
    `relayout()` letterboxes it whole at every width, so per the pin ("the zoom bar + minimap exist
    only for boards larger than the frame — a fixed arena removes them") this arena removes them.
    `broadcast_core.js` already tolerates never being attached: `minimapSurface`/`minimapCtx` (starter
    lines 540-541) stay null and `drawMinimap()` returns on its first guard.
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** (starter lines
    529-547, 553-582) — the whole level is on screen and there is one cog; an inset would show
    strictly less.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad`, and the `.ec-heart` endcard glyphs.
  - `#plates-r` **and the second plate column** — there is one seat, so the scorebug's right plate
    column is removed and `#plates-l` carries the single plate; the space it frees goes to the clock
    and the split readout.
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture`, `.hillflip`, `.tagout` CSS rules
    (starter lines 919-934, 4431-4443) — those kinds are never emitted here. `.gamestart` and
    `.gameover` rules are retargeted to `.levelstart` and `.gauntletend`; the other five kinds get new
    ones.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS), and every
    team-colour path (`TEAM_ORDER`, `.ec-tname` team words).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with
    `#plates-l`/`#clock`/`#clock-time`/`#clock-caption`/`#ffwd-mini`, `#bannerlane`, `#killfeed`,
    `#mmwarn`, **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
    `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`, `#tick-clock`,
    `#speedchips`), `#scrub` with `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/`#scrub-head`,
    `#endcard` with `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`, and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here
and enforced by a test:

| Starter string (`client/replay_broadcast.html:line`) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (3795) | `<span>Level</span><span>Kind</span><span>Seed</span><span>Split</span><span>Outcome</span><span>Gems</span><span>Return</span>` |
| `<span class="fl-cap">Lives left</span>` (3793) | `<span class="fl-cap">Unseen mean</span>` |
| `<span class="fl-cap">Hill time</span>` (3786) | `<span class="fl-cap">Seen mean</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (1576) | `<span class="momentum-label">SEEN vs UNSEEN</span>` |
| `<span class="lives-label">Lives</span>` (2241) | `<span class="gem-label">Gems</span>` |
| `<span class="lives-label pb-lbl">Hill</span>` (2224) | `<span class="lvl-label">Level</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (1480) | "Generating levels…" |
| `#clock-caption` "In the locker room" (1499) | "Before the first level" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (1524) | "Replay hash mismatch at frame N — showing recorded moves" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline ahead of the playhead (o)" (1564) | "deaths / level results / final score on the timeline ahead of the playhead (o)" |
| team words `RED`/`BLUE` in `ec-tname`/plates | the single alias `COG-alpha` and its policy name — there are no teams |

**`tests/test_procgen_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `spray`, `grenade`, `med kit`, `kill`, `HP pips`, `RED`, `BLUE`, `Team` — outside
comment blocks, and asserts **zero** matches; and asserts each replacement string above is present
exactly once. A rename that reintroduces paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (starter lines 4291-4318). **No overlay sits in the transport band**: the board is
laid out between the two bands and every addition here (the split bar, the plan trail, the feed, the
say bubble, the level banner) is positioned inside the board region or in the top band. The **endcard
stops at `var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule at line 1047,
kept) so the scrubber stays clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept).

**Scrubber beats are clickable, labelled buttons.** The appended block's
`procgenBeat(s, frame, kind, tone, label)` — named so it can never shadow `chrome_common.js`'s
`markBeat` alias (the tandem 2026-08-23 hoisting trap; a scope-duplication test over the alias list
enforces it) — appends
`<button class="beat-marker <kind> <tone>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind emitted and no others**: `.beat-marker.levelstart`, `.collect`,
`.exitopen`, `.death`, `.levelend`, `.fallback`, `.gauntletend`. The `levelstart` beat is drawn taller
than the rest, so the scrubber reads as eight chapters at a glance. The game block never calls
`markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: `renderFramesPerStep = 4` at `ReplayFps = 24`** — 6 sim frames per second, speed
chips `[1, 2, 3, 4, 8, 16]` (the starter's `PlaybackSpeeds`, default **1×**). A full 8-level episode of
≈ 300 frames plays for **≈ 50 s**; the 4-level certification replay for **≈ 30 s**, which is what lets
`viewer_smoke.mjs --soak 10` observe real advancement instead of a legitimately-finished replay (the
ecos 2026-08-23 scar). **Level transition:** on each `levelstart` the block holds for 24 render frames
and shows `LEVEL 3 of 8 — MINER — UNSEEN` in `#bannerlane` (the top band, never the transport band).
The speed chips still override it.

### Readouts

1. **The board**, drawn edge to edge: the level's tiles as chunky native-pixel art on a dark CRT floor
   with a faint scanline wash — bedrock as riveted blocks, dirt as granular fill, platforms as beams,
   ladders as rungs, spikes as a lit hazard band. The cog is a Softmax cog sprite with four facings, a
   squash on landing and a dig pose. Gems and pellets pulse; a boulder that is `falling` gets a motion
   streak; hunters have eyes that track the cog. The exit is a **barred door** while locked and a
   **lit doorway** once open — the single most important state change on the board, so it is a
   silhouette change, not a colour change.
2. **The plan trail** — the turn's six symbols drawn as a ghost arrow chain from the cog the moment
   the decision lands, consumed one arrow per frame as it executes; the unspent tail of an interrupted
   plan greys out and a small `CUT` tag appears. This is the readout that makes an LLM's actual
   decision visible, and it is the reason this game is watchable at all.
3. **Scorebug plate** (one, in `#plates-l`): the seat's **real policy name** (spectator side only),
   its in-game alias `COG-alpha`, the level chip `L3/8 · MINER`, a **`SEEN` / `UNSEEN` chip**
   (spectator-only; the seat never has this), gems `3/4`, and a `↯` glyph on any turn that took a
   fallback.
4. **Clock** — `#clock` shows `LEVEL 3/8`; `#clock-time` shows `turn 4/10 · frame 18`;
   `#clock-caption` shows `miner · 15×9 · standard · UNSEEN seed 908314772`.
5. **The split bar** — the starter's `#momentum` SVG retargeted, and the idea's "seen levels vs
   unseen split score" drawn literally: `levelCount` bars in play order, each the level's
   `returnMilli` out of 1000, **seen bars in slate and unseen bars in amber**, with two horizontal
   mean lines (`seen` dashed, `unseen` solid) and the gap annotated between them. Drawn **full width
   from the pre-scan on the first frame**; the playhead crosses it 1:1 with the scrubber; bars fill
   in as their level completes. A spectator can read "it aces what it studied and flails on what it
   has not seen" without reading a number.
6. **Match feed** (`#killfeed`) — plain language, never internal notation:
   `COG-alpha takes gem 3 of 4`, `the exit unlocks`, `COG-alpha clears MAZE — 1000`,
   `a hunter catches COG-alpha — level over at 425`, `a boulder lands on COG-alpha`,
   `COG-alpha runs out of turns on CLIMBER — 640`, `plan cut short — hunter alongside`,
   `COG-alpha: "digging under the rock"`, and
   `COG-alpha MISSED THE CALL — pathfinder plan (timeout)`.
7. **Say bubbles** on the board above the cog. The bubble's box is laid out from `MaxSayRunes = 24`
   **measured in `data/font.ttf`** and clamped inside the board rect, so a bubble on a top-row cog is
   never drawn at a negative y (the cogchemists 2026-08-24 scar); `--strict-text-bounds` stays on in
   CI and `canvas_text.never_inside` must be 0.
8. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
   30 consecutive frames with no `collect`, `death`, `exitopen`, `interrupt` or `levelend` event, from
   the pre-scan), spoilers switch, frame readout, speed chips, the scrubber with its seven beat kinds,
   and `#mmwarn` on a hash mismatch — all the starter's, verbatim.
9. **Endcard** — headline `SCORE 0.570 — mean over four unseen levels`, then
   `seen 0.797 · unseen 0.570 · gap +0.227`, then the eight-row table under the re-mapped header
   (`Level | Kind | Seed | Split | Outcome | Gems | Return`) with the unseen rows highlighted, and a
   one-line summary (`gauntlet · standard · 4 seen / 4 unseen · 2 of 4 unseen levels cleared`). It
   stops at `var(--band)` and any seek dismisses it.

### Art

**Real art, no placeholders, no solid-colour squares.** Two sources, both committed:

- **Tile and entity kit — nano-banana** (`playbooks/art-nanobanana.md`, `gemini-2.5-flash-image`,
  ≤ 3 generations total). Sheet 1: a 32 px tile set in one coherent pixel-art palette — bedrock,
  dirt, platform beam, ladder, spike band, empty floor, locked door, open door — plus their edge
  variants. Sheet 2: entities — gem, pellet, boulder (still and falling), hunter (four facings, eyes)
  — anchored on the starter's own cog reference as an `inline_data` part so the hunter reads as a
  hostile cog. Sheet 3: the player cog in four facings plus a jump pose and a dig pose. All three are
  chroma-keyed and split by `scripts/art/split_tile_sheet.py` into
  `data/tile_<name>.png` / `data/ent_<name>.png` / `data/cog_<pose>.png`, committed alongside
  `scripts/art/source/*.png`, and fed to the starter's **existing** `rig_art.nim` bake plumbing
  (renamed `procgen_art.nim`; same masters/pivots/scale path) so every piece is baked once at
  `cellPx = 32` and composited per frame.
- **Board and chrome — the starter's shipped assets plus install-time bakes.** The floor wash is
  `data/arena_floor.png` tiled and darkened 30 % under the tile layer; the frame border is textured
  from `client/art/walls/{wall_h,wall_v}.jpg`; the scanline wash, the fall streaks, the plan trail,
  the split bar and the say bubbles are procedural in the bake's palette (`data/pallete.png`); labels
  and numerals are `data/font.ttf`. The loading screen is the starter's locker room
  (`client/art/lockerroom/bg.jpg` plus the colour webps) with the caption re-labelled "Generating
  levels…". If the Gemini endpoint is unavailable at build time the builder falls back to
  recolouring the starter's `soldier_*_front.png` masters into cog poses and hand-drawing the tile set
  from `data/ascii.png`, and says so in `log.md` — never a flat rectangle.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (starter lines 4307-4312).

The arithmetic: the board is 15 × 9 tiles at `cellPx = 32` = 480 × 288 map px, aspect **1.667**, for
**every archetype, every variant and every level** — `BOARD_ASPECT` is a constant, so `relayout()`
never re-fits mid-episode. In a 360 × 203 frame, the two measured bands at `--hudscale = 0.5` come to
≈ 34 px (scorebug) + ≈ 46 px (transport), so `availH ≈ 123`. `boxW / availH = 360/123 = 2.93 >
1.667`, so **height binds**: the board renders at **205 × 123**, i.e. **13.7 screen px per tile** —
enough for a 32 px sprite scaled to 13 px to keep its silhouette, which is why the art brief demands
silhouette differences (barred door vs lit doorway, boulder vs gem) rather than colour differences.
At desktop widths everything scales up linearly and the whole board is always in frame, which is why
`#viewpanel` is dropped.

Four rules are added and asserted by `tests/test_procgen_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, the plate keeps only `alias + name + level chip + gems`; the `SEEN`/`UNSEEN` chip
   becomes a 3 px underline on the level chip and the fallback glyph moves inline.
3. Under `.tiny`, tile coordinates are never drawn on the board and the say bubble's font floor is
   9 px × `--hudscale` with the bubble clamped inside the board rect; the plan trail and the death
   flash keep full weight — those are the two things a spectator must not lose.
4. Under `.tiny`, the split bar keeps full width and halves in height (the two mean lines stay), and
   the feed shows three rows instead of four. Every size derives from `--hudscale`, so nothing is
   drawn outside the canvas (`--strict-text-bounds` stays on).

---

## Packaging

- **Repo**: `Metta-AI/cogame-procgen`, **public at creation** (public is a certification prerequisite
  — `source-resolves` 404s on private). Slug `procgen`; **`game.name` is `procgen`** so the secret
  namespace `secret://coworld/procgen/anthropic_api_key`, the page slug `softmax.com/procgen`, the
  `POST /coworld-league-seeds` body and the docs all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name by uppercasing and mapping `-` → `_` (`{{GAME_IMAGE}}` is not a thing —
  lantern 0.1.0). ctf ships two services/two images; this fork uses the one-image / two-entrypoints
  shape because the shared `docker_smoke.sh` and `policies.json` assume a single image (the
  knights-archers precedent):

  ```yaml
  services:
    procgen:
      image: coworld-procgen:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder **`{{PROCGEN_IMAGE}}`**.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4` — the starter's `Dockerfile:29`, not the README's local 2.2.10 —
  `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:procgen src/procgen.nim` →
  `/bin/procgen`, and the same for `src/procgen_player.nim` → `/bin/procgen-player`. The runtime stage
  copies both binaries, `data/`, `client/` and `*.json`. `CMD ["/bin/procgen"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby 0.1.27 with its sha256 check, `nimby use 2.2.4`, the three marker `sed` splices for
  `index.html`, the whole `test -f` / `grep -q` assertion block) with three named edits: the
  `WORKDIR` becomes `/workspace/procgen`; the `league.html` splice and its four assertions are
  **deleted** with `client/league_replayer.html`; and the asset list is swapped to
  `data/{arena_floor,ascii,pallete}.png`, `data/tile_*.png`, `data/ent_*.png`, `data/cog_*.png`,
  `data/font.ttf`, `client/art/walls/*`, `client/art/lockerroom/*`,
  `procgen_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`. The
  `grep -q '^window.CTF_WIRE={'` assertion becomes `'^window.PROCGEN_WIRE={'`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["procgen", "single-agent", "generalisation", "score-attack",
    "grid"]` (≥ 3; **`game.tags` must not exist** — pistonball 0.1.0);
    **`episode_timeout_minutes: 20` at the top level**, not under `game`.
  - `game.name = "procgen"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/procgen"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/procgen/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 1/1, `players` 1/1 — the tandem 0.1.0 scar). `tokens` is described as runner-injected;
    **no `game_config` anywhere in this manifest contains a literal `tokens` array** (matriculate
    rejects "game_config must not include runner-managed tokens" — knights-archers 0.1.0), while
    `config_schema` keeps *requiring* it because the runner injects it. Properties: `tokens`,
    `players`, `seed`, `levelCount` (4–8), `turnsPerLevel` (4–20), `framesPerTurn` (1–8),
    `difficulty` (enum `["easy","standard","hard"]`, default `"standard"`),
    `interruptOnDanger` (boolean, default true), `fallLethal` (2–8),
    `renderFramesPerStep` (1–12), `sayFrames` (0–48), `attempt1Ms`, `retryMs`, `turnBudgetMs`,
    `turnSpacingMs`, `wallClockBudgetSeconds`, `lobbyJoinTimeoutSeconds`, `gameOverFrames`,
    `minPlayers`, `fastMode`, `showPlayerLabels`, and
    **`num_agents` (integer, `minimum: 1`, `maximum: 1`, default 1)**.
    **`slots` is not declared and is absent from every `game_config`** — there is one seat and there
    are no teams. `boardW`/`boardH` are **not** configurable: 15 × 9 is a compiled constant, because
    a variable board would make `BOARD_ASPECT` variable and every generator's validator re-derivable.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}`,
    `endRule: {"type":"string","enum":["gauntlet_complete","wall_clock","sim_fault","host_error"]}`
    and `levelOutcome` items enumerated `["cleared","died","timeup","unplayed"]`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-procgen/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar). Both point at the same document because
    both streams speak the same wire types, exactly as the starter declares them.
  - **`game.docs`** = `{"readme": {"type":"text","value":"<the README body, inlined>"},
    "pages": [{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined>"}}, {"id":"archetypes.md","title":"The four archetypes","content":{"type":"text",
    "value":"<docs/ARCHETYPES.md inlined>"}}, {"id":"training-seeds.md","title":"Published training
    seeds","content":{"type":"text","value":"<docs/TRAINING_SEEDS.md inlined>"}},
    {"id":"protocol.md","title":"Wire protocol","content":{"type":"text","value":"<docs/PROTOCOL.md
    inlined>"}}]}` — inlined text so the pages render before the repo is indexed. The training-seed
    page is a **product requirement**, not documentation: the seen half of the score only means
    something if the seeds really are public.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "200m", memory: "128Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). **Exactly ONE entry, `pathfinder`.** Reason, stated
    because it differs from the multi-seat precedents: every declared bundled player must occupy a
    certification slot (the raid 0.1.2 scar), and a 1-seat fixture has exactly one slot — so declaring
    two bundled players would be unsatisfiable. `scavenger` is still built into the image and still
    ships as a league **policy** through `tools/ci/policies.json`, which is a different surface.

  **Variants — `num_agents: 1` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0). Three variants ship in v1:

  ```json
  "variants": [
    {"id": "gauntlet",
     "name": "Procgen Gauntlet (8 levels, half of them nobody has ever seen)",
     "description": "One cog plays eight procedurally generated 15x9 levels back to back: a maze with four gems behind a locked door, an open room of pellets patrolled by hunters, a stack of platforms over a lethal pit, and a wall of dirt hiding diamonds under falling boulders - each archetype twice. Four of the eight are built from seeds published in this repo; the other four are drawn out of two billion possibilities the moment the episode starts, and the cog is never told which is which. Ten decisions per level, six moves per decision, executed blind but cut short the instant something dangerous happens. The score is the average return on the four levels nobody has ever seen.",
     "game_config": {"players": [{"name":"Cog1"}],
                     "num_agents": 1, "minPlayers": 1,
                     "levelCount": 8, "turnsPerLevel": 10, "framesPerTurn": 6,
                     "difficulty": "standard", "interruptOnDanger": true, "fallLethal": 4,
                     "renderFramesPerStep": 4, "sayFrames": 12,
                     "attempt1Ms": 5000, "retryMs": 2000,
                     "turnBudgetMs": 7500, "turnSpacingMs": 2500,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutSeconds": 90,
                     "gameOverFrames": 12, "fastMode": true, "showPlayerLabels": false}},

    {"id": "sprint",
     "name": "Procgen Sprint (4 levels, deeper play on each)",
     "description": "The same four archetypes, but one level each and fourteen decisions instead of ten - room to backtrack out of a bad maze branch or wait out a hunter. Two of the four levels come from the published seed table and two are drawn fresh at episode start, chosen by the episode seed, and the cog is never told which. The score is still the average return on the unseen half, so a single bad unseen level costs twice what it costs in the eight-level gauntlet. This is the high-variance ladder.",
     "game_config": {"players": [{"name":"Cog1"}],
                     "num_agents": 1, "minPlayers": 1,
                     "levelCount": 4, "turnsPerLevel": 14, "framesPerTurn": 6,
                     "difficulty": "standard", "interruptOnDanger": true, "fallLethal": 4,
                     "renderFramesPerStep": 4, "sayFrames": 12,
                     "attempt1Ms": 5000, "retryMs": 2000,
                     "turnBudgetMs": 7500, "turnSpacingMs": 2500,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutSeconds": 90,
                     "gameOverFrames": 12, "fastMode": true, "showPlayerLabels": false}},

    {"id": "hardpool",
     "name": "Procgen Hard (8 levels, denser hazards)",
     "description": "The eight-level gauntlet with the generator's difficulty turned up: mazes with more loops and longer routes, three hunters instead of two, more spikes and wider gaps over the pit, and more boulders sitting on top of the diamonds. Same ten decisions and six moves per decision, same published-versus-unseen split, same scoring. It is the same four questions asked with less margin, and it is where a careful policy separates from a greedy one.",
     "game_config": {"players": [{"name":"Cog1"}],
                     "num_agents": 1, "minPlayers": 1,
                     "levelCount": 8, "turnsPerLevel": 10, "framesPerTurn": 6,
                     "difficulty": "hard", "interruptOnDanger": true, "fallLethal": 4,
                     "renderFramesPerStep": 4, "sayFrames": 12,
                     "attempt1Ms": 5000, "retryMs": 2000,
                     "turnBudgetMs": 7500, "turnSpacingMs": 2500,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutSeconds": 90,
                     "gameOverFrames": 12, "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 1` again, inside `certification.game_config`, and exactly
  one player so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS
  == 1` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks), with the single declared
  bundled player seated:

  ```json
  "certification": {
    "players": [{"player_id":"pathfinder"}],
    "game_config": {"players": [{"name":"Cog1"}],
                    "num_agents": 1, "minPlayers": 1, "seed": 42,
                    "levelCount": 4, "turnsPerLevel": 10, "framesPerTurn": 6,
                    "difficulty": "standard", "interruptOnDanger": true, "fallLethal": 4,
                    "renderFramesPerStep": 4, "sayFrames": 12,
                    "turnSpacingMs": 0, "wallClockBudgetSeconds": 200,
                    "lobbyJoinTimeoutSeconds": 45, "gameOverFrames": 12,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  Four levels is milliseconds of sim but **≈ 30 s of playback** at 6 sim frames per second, which the
  viewer soak needs. `turnSpacingMs: 0` because certification runs with no API key and the seat is
  scripted. **Seed 42 is asserted by `tests/test_procgen_engine.nim` to produce a fixture episode of
  at least 180 sim frames that contains at least one `collect`, one `exitopen`, one `death` and one
  `levelend` of each of `cleared` and one of `{died, timeup}`**, so the CI smoke replay always
  exercises the beats, the feed and a soak longer than 10 s; if a rules change makes seed 42
  uninteresting, `tools/scan_event_seeds.sh` (the starter's, retargeted) picks the next seed and the
  test's pinned literal moves with it in the same commit. The certify step in `coworld-release.yml`
  passes **`--timeout-seconds 300`** (the default 60 covers start + connect grace + play + linger —
  cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/procgen-player"`, following the
  starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"procgen-cartographer","run":"/bin/procgen-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"cartographer"}},
   {"name":"procgen-scrambler","run":"/bin/procgen-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"scrambler"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"procgen-pathfinder","run":"/bin/procgen-player",
    "env":{"PLAYER_SCRIPTED":"pathfinder","PLAYER_POLICY_LABEL":"pathfinder"}},
   {"name":"procgen-scavenger","run":"/bin/procgen-player",
    "env":{"PLAYER_SCRIPTED":"scavenger","PLAYER_POLICY_LABEL":"scavenger"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `pathfinder` and `scavenger`, and
  their versions must differ from the champions'. **No `USE_BEDROCK` flag**: the LLM call is made by
  the **game** pod (§Decisions).
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps
  the template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `procgen`,
  `<IMAGE>` → `coworld-procgen`, `<SEATS>` → **`1`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server) and
  `--soak 10` added to the `viewer_smoke.mjs` invocation. `coworld-release.yml` and
  `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on the certify step. The
  push-triggered `upload-coworld` job is gated on the `UPLOAD_REQUIRED` repo variable (the derks-gym
  0.1.1 scar). `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed
  **executable** (mode 100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_procgen_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in both
debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_procgen_sim.nim`)

1. `tiles and passability` — the glyph table, the tile enum and the passability table are one source;
   every archetype's `passable` agrees with the table for every tile; the outer ring is `Wall` on
   every generated level.
2. `action alphabet` — exactly six symbols; `applyAction` is total over
   (6 symbols × 4 archetypes × every tile) and never raises; `L R U D` set `last_dir` even when the
   move is blocked; unknown symbols never reach `applyAction` (the validator drops them).
3. `maze physics` — no gravity, no hazards; a gem is collected on entry; the exit stays `ExitLocked`
   until `collected == 4` and becomes `ExitOpen` on that exact frame; standing on `ExitOpen` finishes.
4. `chaser physics` — hunters take a BFS step every frame except `frame mod 3 == 0`; ties break
   `L, R, U, D`; contact either way kills with cause `caught`; `X` dashes two tiles and only when both
   are passable; the cooldown blocks the next 4 frames' `X`.
5. `climber physics` — `X` sets `jumpFuel = 2` and the cog rises one tile per frame while it lasts;
   horizontal moves work mid-air; gravity pulls one tile per frame when nothing is under; `fallDepth >
   4` kills with cause `fell`; leaving the bottom row kills with cause `fell`; a `Spike` kills with
   cause `spiked`; `U`/`D` move only on a `Ladder`.
6. `miner physics` — a `Dirt` target is dug and entered in one frame; a horizontal `Boulder` push
   succeeds only when the far cell is `Empty` and never vertically; `X` digs the `last_dir` tile
   without moving; the falling scan runs bottom-to-top left-to-right, one tile per entity per frame;
   a falling boulder entering the cog's cell kills with cause `crushed`; a boulder resting on the cog
   does **not**.
7. `exit rule is uniform` — in all four archetypes the exit is locked until every collectible is
   taken, `exitopen` is emitted on exactly that frame, and entering a locked exit is a blocked move.
8. `danger interrupt` — fires exactly on its four conditions and on no others; `maze` never
   interrupts; the unspent tail of the plan is discarded, `planInterrupts` counts it, the level state
   is unchanged by the interrupt itself, and the next turn's observation is taken from the interrupted
   frame.
9. `progress measure` — `bestDist` is monotone non-increasing within a level and equals a from-scratch
   BFS minimum over the frames actually played, on 500 randomised trajectories.
10. `scoring` — `returnMilli` matches the formula for 2000 randomised end states; it is in
    `[0, 1000]`; it is 1000 iff everything was collected and the exit reached; `unseenMilli` is the
    arithmetic mean over **all** unseen levels including zeros; `gapMilli == seenMilli - unseenMilli`;
    `scores[0] == unseenMilli / 1000.0` and lies in `[0.0, 1.0]`; `win[0]` is true iff every unseen
    level ended `cleared`.
11. `end conditions` — `gauntlet_complete`, a forced wall-clock stop and a forced fault each produce
    the right `endRule` and the right `reason`; a deadline mid-gauntlet marks unreached levels
    `unplayed` with return 0 and still divides by the full `unseenCount`; the legal `reason` set is
    exactly `{complete, deadline, fault}` and the legal `levelOutcome` set exactly
    `{cleared, died, timeup, unplayed}`.
12. `no floats in hashed code` — a source grep over
    `src/procgen/{tiles,gen,levels,path,scoring}.nim` finds no float literal, no `/` and no `sqrt`.
13. `frame budget` — a full 8-level, all-scripted, `hard` episode completes in < 1 s in a release
    build, and no single frame exceeds 1 ms.

**Generators and seeding**

14. `tests/test_procgen_gen.nim` — `generateLevel` is a pure function of `(kind, seed, difficulty)`:
    identical grids across 500 seeds × 4 archetypes × 3 difficulties on repeat calls, and identical
    between the native build and the wasm build (the cross-target case runs the emitted module through
    `tools/wasm_replay_smoke.cjs`).
15. `generators validate` — over 5000 seeds per archetype per difficulty: every collectible and the
    exit is reachable, the start is never adjacent to a hunter spawn, `climber`'s every row is
    reachable from the row below within jump range, `startDist >= 1`, and the 41st-attempt
    `FallbackLevel` is **never** reached (`genFallbacks == 0`).
16. `tests/test_procgen_seeding.nim` — `TrainSeeds` has 128 entries, 32 per archetype, all < 5000;
    `testRng` draws only from `[100000, 2147483646]`, so seen and unseen seed sets are **disjoint by
    construction**; the gauntlet plan is a pure function of the episode seed, is drawn **before any
    seat connects**, and does not change when seat behaviour changes; `setupRng` and `testRng` are
    stream-separated; `levelCount = 8` yields exactly one seen and one unseen level of each archetype
    and `levelCount = 4` exactly two of each split; `levelCount` outside `{4, 8}` is rejected by
    `sim_config`.
17. `tests/test_procgen_identity_privacy.nim` — no real player name, no level seed, and neither of the
    strings `"seen"` / `"unseen"` appears in any observation JSON, any prompt, any `directive.view` or
    any broadcast board label; they appear in `results`, the replay config and the DOM scorebug.
18. `tests/test_procgen_determinism.nim` — re-simulate from the replay's seed, `levelKinds`,
    `levelSeeds` and recorded action bytes alone on a fresh sim; identical final frame, grids, entity
    positions, collected counts, returns and per-frame `gameHash`.
19. `tests/test_procgen_upstream.nim` — the shipped text in `src/procgen/upstream.nim` equals the
    table and the five divergences at the head of this note, and `docs/RULES.md` opens with the
    "reimplementation, not a port" sentence. A claim edited without editing its citation fails.

**Bounded orders / legality on the scripted baselines** (`tests/test_procgen_control.nim`)

20. `baselines are bounded` — for 500 pseudo-random level states (all four archetypes, all three
    difficulties, every phase from full to nearly-cleared) and for **both** `pathfinder` and
    `scavenger`: the returned object has `moves` of length 1…6 drawn **only** from `LRUDX.`, `say` and
    `notes` empty, and a serialised directive ≤ 1024 bytes. A baseline that ever proposes a symbol
    outside the alphabet or a plan longer than `framesPerTurn` fails the build.
21. `baselines never leave the cog unactuated` — over the same states, including states where every
    symbol is fatal, a non-empty plan is always returned (`"."` in the sealed case) and the cog dies
    or waits rather than the loop stalling.
22. `baselines agree with the resolver` — every symbol a baseline emits, executed by `stepFrame`,
    produces the effect the baseline predicted for it, and every symbol it vetoed as fatal is one
    `stepFrame` would have killed the cog for. The predicates are the same procs, and this test is
    what stops a second copy appearing.
23. `fallback is the pathfinder proc` — the decision engine's fallback path and the `pathfinder`
    baseline resolve to the same proc, so they cannot drift.
24. `reply validation` — the validator accepts the schema; **repairs** a `moves` string with junk
    characters by dropping them; truncates a 40-character `moves` to 6 on a **rune** boundary; turns an
    empty/absent/non-string `moves` into `"."`; accepts a reply with only `moves`; rejects a non-object;
    truncates `say`/`notes` on **rune** boundaries at 24/160 with 4-byte emoji sitting exactly on each
    boundary; caps the read at 4096 bytes; and never leaves the cog without a plan.
25. `baseline tuning is the swept pick` — the shipped tunables equal `tools/ci/baseline_tuning.json`
    (the starter's `test_tuning` pattern; `ci.yml` re-runs the sweep with `--check`), and
    `pathfinder`'s mean `scores[0]` over the recorded 24-episode ladder beats `scavenger`'s by a margin
    inside `[+0.05, +0.45]`.

**End-to-end episode writing a replay** (`tests/test_procgen_engine.nim`)

26. `episode writes artifacts` — run a real one-seat episode (`gauntlet`, `levelCount 4`, scripted, no
    API key so the LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert
    `results.json` and the `.replay` are written, `reason == "complete"`,
    `endRule == "gauntlet_complete"`, `scores[0] ∈ [0.0, 1.0]`, every seat-indexed array is 1 long,
    every level-indexed array is `levelCount` long, and the results key set equals the manifest's
    `results_schema` key set **exactly**.
27. `the cert seed is interesting` — seed 42 with the fixture's config runs ≥ 180 sim frames and yields
    ≥ 1 `collect`, ≥ 1 `exitopen`, ≥ 1 `death`, ≥ 1 `levelend` with `cleared` and ≥ 1 with
    `died`/`timeup`, so the CI smoke replay always exercises the beats and outlasts the 10 s soak.
28. `every variant runs` — each of the three shipped `game_config`s constructs a valid `GameConfig`,
    draws a legal gauntlet plan, plays a full scripted episode and produces the variant's claimed level
    count, difficulty and split shape (the collab-cooking 0.1.1 scar: test every variant, not just the
    fixture).
29. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats[0]` set, the loud unregistered-seat log line present, and exactly one closed-schema
    `{"message","failed_policy_index"}` failure payload.
30. `budget guard settles early` — with the guard forced, the episode finishes `complete`, not
    `deadline`, and the `budget_guard` record names the turn.
31. `certifier probes` — `/healthz`, `GET /client/player?slot=0&token=<t>` (with a bad token refused
    and the player socket **not** opened), `GET /client/global`, the `/global` first message and a
    websocket `Ping → Pong` all answer, and keep answering for the shutdown grace after artifacts are
    written.

**Replay** (`tests/test_procgen_replay.nim`)

32. `record then re-derive, every end reason` — for `gauntlet_complete`, `wall_clock` **and**
    `sim_fault`, record an episode and re-derive it from the bytes; assert identical `gameHash` at every
    frame **including the stop frame** (the particle-worlds scar).
33. `replay is self-sufficient` — the bytes alone yield the seat name, alias, policy kind, the full
    config **including `levelKinds`, `levelSeeds`, `levelSplit`, `difficulty` and `num_agents`**, the
    seed, every action byte, every chat record and the result; the eight grids are re-generated, not
    stored; deleting every file in `data/` except the art does not change what the bytes render.
34. **`replay_summary is strict UTF-8 JSON`** — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports `protocol == "procgen/v1"`
    with `levelSeeds | length == levelCount`.
35. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`, kept.

**Manifest** (`tests/test_procgen_manifest.nim`)

36. `manifest pins` — `num_agents == 1` in **all three** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens` in
    any `game_config`; no `slots` anywhere; `len(player) == 1` and that player seated in
    `certification.players`; `len(certification.players) == len(certification.game_config.players)
    == 1`; every array in `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes`
    top-level; both `game.protocols.player` and `.global` present as `{"type","value"}` objects;
    `game.docs.readme` + four `pages`, every value non-empty text; `game.description` present and
    `game.tags` absent; ≥ 3 top-level tags; `player[].resources.limits.cpu >= "1"`; every
    `wallClockBudgetSeconds <= 660`; every variant's `levelCount ∈ {4, 8}` and
    `levelCount × turnsPerLevel <= 80`; and `game.replay_viewer.bundle == "static-replay-viewer"`.
37. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` —
    the collab-cooking 2026-08-25 scar).
38. `wall-clock arithmetic holds` — for every variant, `levelCount × turnsPerLevel × turnBudgetMs / 1000
    + 50 <= 720`, asserted from the shipped numbers so a later knob change cannot silently blow the
    60 % budget.

**Viewer** (`tests/test_procgen_viewer.nim`, static assertions in the `test` job)

39. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals
    `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` and its length 40 022, both
    pinned as literals.
40. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker and only appends after it; `broadcast_core.js`'s kept procs are
    byte-identical to the starter's, **`pushFeed`'s signature included**.
41. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap); the beat builder is `procgenBeat`,
    never `markBeat`.
42. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{levelstart, collect, exitopen, death, levelend, fallback, gauntletend}`.
43. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band;
    the four 360 px rules exist; `BOARD_ASPECT` is the constant 15/9; the removed ids (`#viewpanel`,
    `#minimap`, `#zoombar`, `#fpv*`, `#povBadge`, `#plates-r`, …) appear nowhere.
44. `endcard labels` — `tests/test_procgen_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
45. `label manifest` — the starter's `test_label_contract` pattern: the emitted board-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
46. `events are the closed enum` — `tests/test_procgen_events.nim`: the set of kinds `stepEvents` can
    emit equals exactly the seventeen listed in §Server, and every kind used by the appended game block
    is in that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**

47. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`, no substitutions) is run by **`ci.yml`'s
    `wasm-viewer` job**, which `needs: docker-smoke` and runs it against **the replay `docker-smoke`
    produced** (downloaded as the `smoke-replay` artifact), in headless chromium (Playwright pinned
    1.55.0 in both the npm module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives, the clock/frame readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays on.
48. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, the seat in the CI replay plays scripted and emits **no `say` at all**, so the
    smoke replay can never exercise the bubble or the feed's say path (the cogchemists 2026-08-24
    scar). The fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and
    shims only the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26
    scar) — driving the real page with a full-cap 24-rune `say` **on a cog standing on the top row**
    (the negative-y bubble case), an interrupted plan trail, a death flash, all four archetypes' tile
    sets, a full eight-bar split bar with both mean lines, and the endcard, at several canvas widths
    including 360 px.
49. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards. Four fixtures are committed and re-recorded on every
    `GameVersion` bump — `tests/fixtures/gauntlet-seed42`, `sprint-seed7`, `hard-seed13`,
    `deadline-seed21` — with their recipes in `tests/test_procgen_replay.nim` (the starter's
    fixture-recipe discipline, `AGENTS.md` §Replay fixtures, including its rule that a recipe must pin
    every field its ending depends on).

---

## Out of scope (v1)

- **Twelve of the sixteen Procgen games.** `starpilot`, `caveflyer`, `dodgeball`, `fruitbot`,
  `jumper`, `leaper`, `bigfish`, `heist`, `plunder`, `ninja`, `bossfight` and `coinrun` as a game
  distinct from `climber` are all deferred. Each needs an engine this repo does not have: `starpilot`
  and `plunder` are scrolling shooters with projectiles and continuous motion; `bigfish` is a
  size-ordered ecology; `bossfight` is a boss state machine with phases; `caveflyer` and `fruitbot`
  need continuous flight; `heist` needs a key/lock graph on top of the maze. Four archetypes on one
  tile sim is what v1 can build and prove; adding a fifth engine is a second note, not a switch.
- **A bit-exact port of OpenAI Procgen.** The upstream is C++ (`gym3`/`libenv`) and cannot be embedded
  in this image or compiled to the viewer's wasm module. Anyone wanting byte-identical `coinrun`
  wants the `cogame-moba` starter, `docs/PORTING.md` and a different note. Every divergence this repo
  makes is enumerated in §Upstream and pinned by a test.
- **Raw-pixel observations (64 × 64 × 3) and a neural policy interface.** The fleet's policy contract
  is `PLAYER_PROMPT` / `PLAYER_SCRIPTED` on the Coworld player socket; a convnet policy needs a
  different runnable type, a different upload path and a different scoring cadence. The symbolic
  observation is the substitution and §What the idea asks for records it.
- **Procgen's 15-action space.** Diagonals and the two spare specials are dropped; see §The game →
  The action alphabet. Adding diagonals means a corner-cutting rule in four archetypes and a fifth
  physics case in `climber`, for no new decision.
- **A fixed, permanently held-out test-seed set.** v1 draws unseen seeds fresh per episode from
  2.1 × 10⁹ per archetype. A fixed hidden list would need a secret store, a leak policy and a rotation
  schedule, and it would be strictly weaker: a leak would be unrecoverable, whereas a fresh draw
  cannot leak. §What the idea asks for, item 6, records the reading not taken.
- **`distribution_mode` and curricula.** Procgen ships `easy`/`hard`/`extreme`/`memory`/`exploration`
  modes. v1 ships three difficulty tables and nothing that schedules them; a curriculum is a league
  settings feature, not a game feature.
- **Speed as a scoring term.** Finishing a level in 20 frames and in 55 frames pay the same. A speed
  bonus needs a magnitude the idea does not pin, and it would reward committing six blind moves in
  `chaser` — the exact behaviour the danger interrupt exists to make unnecessary.
- **Scoring the seen half.** `seenMilli` and `gapMilli` are measured, recorded in `results`, drawn as
  the split bar and printed on the endcard, and deliberately **not** in `scores`. The moment the seen
  half pays, memorising 128 published levels becomes worth doing, which is the failure the whole
  coworld exists to avoid.
- **More than one seat, and racing two policies through the same seeds.** `num_agents` is fixed at 1
  in every variant and the cert fixture. A head-to-head on identical seeds is an attractive second
  coworld — it is a different score (a margin, not a mean), a different observation (you can see the
  rival), a different wall clock (two calls per turn) and a different manifest.
- **A private channel or any inter-episode memory.** `notes` survives within an episode and nothing
  survives across episodes. Persisting notes between episodes would let a policy accumulate a map of
  the unseen pool, which is memorisation by another name.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the
  hosted spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, bullets, hit points, lives, respawns,
  spray, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches, puddles, perks,
  handicaps, achievements, teams, four-team play, campaign mode, fog of war and the vision cones, the
  first-person PIP, continuous 2-D motion, the procedural *arena* generator, the map pool, the map
  editor and the mapkit — all deleted, not disabled (§Sim module), and none of them return in v1.
