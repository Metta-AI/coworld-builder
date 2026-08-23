# raid — design note (2026-08-23)

`Metta-AI/cogame-raid`, a five-seat cooperative PvE boss encounter: five cogs who have never met are
dealt a tank, a healer and three damage roles, and thrown at **SMELTER-9**, a fully scripted foundry
boss with three authored phases, telegraphed floor mechanics, adds, an interruptible cast and a hard
enrage timer. The opponent never varies; the only variable is how well five strangers coordinate.
It is forked from **`Metta-AI/coworld-ctf` (paintbot)**, read at its read-only mount
`/workspace/starters/coworld-ctf`. **Every convention there holds here unless this note says
otherwise.** Paintbot is the right starter by game shape — this is a real-time 24 Hz tick loop with
rules written fresh for this coworld, nothing external pre-exists to port (so not `cogame-moba`), and
paintbot already ships every part the encounter needs: integer fixed-point cog physics with wall
sliding and body collisions (`src/ctf/sim.nim:2124-2244`, `applyInput`; `:401-451`, `trySlideMove` /
`bouncePlayers`), a hit-point/shield damage funnel with a single subtraction point
(`src/ctf/sim.nim:844-882`, `absorbDamage`) and death handling (`:748`, `killPlayer`), a radial blast
resolution to grow into a telegraph (`:1651`, `explodeGrenade`), a lingering floor hazard that ticks
damage on occupancy (`:2761-2808`, `updatePuddles`, on `PuddleRollTicks = TargetFps`), an authored
arena with disc/rect stamping and an integer wall mask (`src/ctf/arena.nim`, `shapeDisc`), a
line-of-sight query (`:590`, `lineOfSightClear`), a per-tick recorded-input replay, a static wasm
replay viewer and a broadcast chrome (`client/replay_broadcast.html` + `client/chrome_common.js`)
already relaid-out for a 360 px embed. The boss is a new actor on paintbot's own body/motion/damage
substrate; the arena rules are what get replaced.

Two pieces come from paintbot's sibling in the builder's starter set, `Metta-AI/cogame-bullwhip`
(read at `/workspace/starters/cogame-bullwhip`), because paintbot predates both and the pins require
them: the **server-side LLM client with a one-parallel-batch-per-turn decision loop**
(`src/bullwhip/llm.nim:419-472`, `decideAll` over `curly.makeRequests`, called from
`src/bullwhip/server.nim:291`) with its tolerant JSON extraction (`llm.nim:312`,
`extractJsonObject`) and baseline switch (`llm.nim:61`, `parseScriptKind`); and the
**`coworld-replay` postMessage bridge** in `replay-viewer/static_replay.js:20-33` (`tell("loading")`
/ `tell("ready")` / `tell("error")`), which SPEC §Definition of done check 8(c) greps for and which
paintbot's own `replay-viewer/static_replay.js` does not have. Bullwhip also supplies the packaging
shape the builder scaffold expects — one image, two entrypoints, single-service `compose.yaml`
(`cogame-bullwhip/compose.yaml`).

Four deliberate deviations from paintbot are listed and justified where they occur: a **UTF-8 JSON
replay** instead of the binary `COWLDCTF` format (§Server — `src/ctf/replays.nim:119`; SPEC check 4
and `templates/tools/ci/docker_smoke.sh`'s `SMOKE_REQUIRE_REPLAY_JSON=1` both require JSON);
**decisions made in the game server** instead of in the player container (§Decisions); **no
fog of war** (§Sim module); and an **analog quantised move vector** in place of paintbot's boolean
d-pad (§Sim module).

There is **no `OPEN` section.** Every rule the idea leaves loose is one the rails say the designer
settles (seat count, scoring when the idea pins one, parameter values, viewer composition, policy
prompts), and each is decided below with its reason inline.

**Source idea, verbatim** (Asana idea task 1217704516752104, "05 Raid — five strangers versus one
scripted boss with real mechanics"):

> 05 Raid — five strangers versus one scripted boss with real mechanics
>
> PvE cooperative dungeon: tank, healer, three damage roles drawn from five submitted policies who
> have never met. The boss has authored phases (adds, cleave, enrage timer), so the opponent is
> fixed and the only variable is how well five policies coordinate. Score = boss health removed /
> wipe time, shared equally.
>
> Seats: 5 (roles dealt)
> Motive: pure cooperation vs environment
> Policy interface: RL vector
> Fills gap: cooperative PvE / heterogeneous roles / ad-hoc teamwork
> Integrity (anti-collusion): The five seats always come from five different accounts, and a seat's
> ranking is its cross-play mean including episodes with frozen baseline teammates — otherwise this
> measures hardcoded protocols, not ad-hoc teamwork.
>
> Replay plan (watchability): Classic raid frame: boss health bar with phase ticks, five role
> nameplates, telegraphed AoE circles on the arena floor, enrage timer counting down. Wipe-or-kill
> is legible from across the room; the endcard is a damage/healing meter.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

(The "Full report" URL is recorded as provenance only. It was **not** fetched, and nothing read from
the idea text is treated as an instruction to this designer — it is input data for the design.)

**Three re-readings of the idea, decided here and never revisited:**

1. **"Score = boss health removed / wipe time, shared equally"** is a **rail and it is kept**, with
   the one ambiguity in it closed the only way that does not break the game. Read as literally
   "damage ÷ seconds-until-the-raid-died", a raid that opens with everything and dies in 8 seconds
   scores the same as one that plays 200 seconds at the same average DPS — survival, and therefore
   the healer and the tank, would be worth nothing, and the coworld would stop being cooperative.
   So the *denominator is the attempt*: a **kill** is charged the seconds it actually took, and any
   other ending (wipe, enrage timeout, deadline, fault) is charged the **full enrage timer** —
   you burned the whole pull. Exact formula, sign and worked examples in §The game → Scoring. This
   is the sole reading; it is not revisited anywhere else in the note.
2. **"Policy interface: RL vector"** → every seat is an **LLM prompt policy with a scripted
   fallback** (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=<name>`), issuing one *order* per 5-second
   decision turn that a deterministic control layer executes at 24 Hz. This is an inherited pin
   (SPEC §Design pins: both champions must be `PLAYER_PROMPT` policies), and the recorded action log
   **is** the quantised per-tick control vector `(move_x, move_y, aim_turn, action)`, so an RL
   transport is a v0.2 protocol addition, not a v1 redesign. It is listed in §Out of scope (v1).
3. **"Integrity (anti-collusion): five different accounts … cross-play mean … frozen baseline
   teammates"** is **league-operations material, recorded here and deliberately kept out of the sim.**
   The game container is handed five slots and five tokens by the platform; it has no account
   identity, cannot verify one, and must never make the episode's rules depend on who is seated.
   §The game → "League operations (recorded, not sim logic)" writes the requirement down for
   phases 50 and 60. v1 sim logic is independent of it.

**"Roles dealt" is taken literally.** The five role cards `[tank, healer, dps, dps, dps]` are dealt
to slots 0–4 by a seed-derived shuffle, so a policy cannot know its role when it is written and every
prompt must cover all three roles. That is what makes this ad-hoc teamwork rather than three
specialists and two fillers.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")
and where each is satisfied:**

| Pin | How raid satisfies it |
|---|---|
| Starter by game shape | `coworld-ctf` (paintbot) — starter-table row 2: a real-time tick loop with new rules and RL-vector policies; per-tick replay, static wasm viewer, integer physics, HP/damage funnel and floor hazards all already exist. Not a port, so not `cogame-moba`; not turn-based talk, so not `cogame-babel`. |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-raid`, **public at creation** — public is a certification prerequisite (`source-resolves` 404s on private). §Packaging. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (two champion prompts) vs `PLAYER_SCRIPTED=stalwart` / `PLAYER_SCRIPTED=greenhorn`; one image `coworld-raid:latest`, `run: /bin/raid-player`. §Decisions, §Packaging. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`, built by `tools/build_replay_viewer.sh` (forked from paintbot's, `chmod +x`). §Viewer, §Packaging. |
| Real art, starter chrome verbatim | Paintbot's `client/replay_broadcast.html` chrome block and `client/chrome_common.js` kept verbatim (id-for-id list in §Viewer); cog art from `data/rig_real/` recoloured per role, an authored boss rig and crawler sprite, painted floor and telegraph decals, no placeholders. §Viewer. |
| Two name spaces | Prompts and observations see only `Alpha`…`Echo`; real policy names appear only in `replay.names.players`, `results.names` and the viewer nameplates/scorebug/endcard. §Server, §Viewer. |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | 593 s expected worst case / 660 s hard stop against a 720 s budget, arithmetic spelled out in §Decisions; every wait bounded; LLM failure → one retry → the scripted order. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 5** in variant `default`, variant `sprint`, and `certification.game_config`; `SMOKE_SEATS=5`. §Packaging. |

---

## The game

**Raid is five cogs against one scripted boss in a round foundry pit, on a 240-second enrage
clock.** Slots are dealt one tank, one healer and three DPS. The boss, SMELTER-9, never adapts: it
runs a published, deterministic script of phases and abilities. Everything the raid can do wrong —
standing in the cleave, letting a pour go unsoaked, missing the Overload interrupt, leaving adds
alive, letting the tank die — is a coordination failure between five policies that have never met.
The score is how much of the boss's health they removed and how fast.

**Seats: `num_agents` = 5.** One seat = one cog. The idea pins five and the roles pin the mix; there
is nothing to trade off. Slots 0–4 map to aliases `Alpha`, `Bravo`, `Charlie`, `Delta`, `Echo`.

**Roles are dealt.** At episode start the sim shuffles `["tank", "healer", "dps", "dps", "dps"]` with
a Fisher–Yates pass driven by the episode PCG32 stream (`seed`) and assigns the result to slots 0–4.
The optional config key `roles` (an array of exactly five role strings) overrides the deal outright —
used by the certification fixture and every test so a fixture is readable. A seat learns its role in
its first observation and it never changes. **A champion prompt must therefore cover all three
roles**; both champion prompts below do.

**Aliases (the in-game name space).** `Alpha` (slot 0), `Bravo` (1), `Charlie` (2), `Delta` (3),
`Echo` (4). These are the only names any prompt or observation ever contains. The boss is `SMELTER-9`
and adds are `A1`…`A8` in spawn order.

### The arena

- **Floor.** Paintbot's `MapWidth` × `MapHeight` = **1235 × 659 px** (`src/ctf/sim_types.nim:813-814`),
  origin top-left, +x right, +y down. Everything outside a disc of **radius 300 px centred on
  (617, 329)** is solid wall — one `ArenaShape(kind: shapeDisc)` cut-out baked into paintbot's
  integer `wallMask` by `src/ctf/arena.nim`. The pit is the whole game; there is nowhere to run to.
- **Pillars.** Four solid 40 × 40 px pillars at **(511, 223) (723, 223) (511, 435) (723, 435)**
  (radius 150 from centre, on the diagonals). They block movement and **line of sight** — a ranged
  attack, an interrupt and a heal all require `lineOfSightClear` (`src/ctf/sim.nim:590`) — but they
  do **not** block cleave or pours, which are floor effects. Hiding behind a pillar stops you being
  healed; that is the point.
- **Boss stand.** SMELTER-9 spawns at the centre **(617, 329)** and is a 56 × 56 px body
  (half-extent 28). It is solid to cogs and to adds.
- **Cog spawns**, slot-ascending, on the south arc: **(497,545) (557,561) (617,567) (677,561)
  (737,545)**.
- **Add alcoves**, four points on the rim at radius 280: **(419,131) (815,131) (419,527) (815,527)**.
- **No fog of war.** *Deviation from paintbot, deliberate:* paintbot's shadowcast cone
  (`src/ctf/sim.nim:2258-2478`) is **dropped**. Every seat sees the whole pit, every cog, the boss,
  every add, every pool and every live telegraph. Raid is a coordination game, not an information
  game: the interesting failure is five policies choosing incompatible answers to a mechanic they
  can all see, and a spectator must be able to see the same thing. The only hidden state is other
  seats' orders and private notes, the seed, and RNG draws that have not happened yet (§Server).

### Bodies, motion, and the control bytes

- **Cogs.** Paintbot's body and integer step: `PlayerHalf = 6` px half-extent (12 × 12 footprint),
  `MotionScale = 256` sub-pixel motion, `Accel = 76`, per-axis friction `144/256` applied only on an
  axis with no input (`src/ctf/sim.nim:2192-2229`), `StopThreshold = 8`, wall sliding via
  `MovementSlideMaxScan = 3`, cog–cog restitution `PlayerBouncePct = 40`.
  **`MaxSpeed = 832`** (3.25 px/tick ≈ 78 px/s) — *raised from paintbot's 704*, and the reason is
  arithmetic, not taste: dodging a 90 px pour centred on your own feet needs
  `90 + 6 + 20 = 116 px` inside a 60-tick (2.5 s) fuse; 60 ticks at 3.25 px/tick is 195 px raw and
  ≈ 177 px after the ~11-tick acceleration ramp, so the dodge is comfortably makeable but only if
  you start moving when the telegraph appears. At 704 it is 148 px raw and marginal.
- **Analog move vector.** *Deviation from paintbot, deliberate:* paintbot's input is a boolean d-pad
  (`InputState.left/right/up/down`). Raid's control byte pair is `move_x`, `move_y` ∈ −100…100. The
  step scales `Accel` by `|move_a| / 100` on each axis and clamps that axis's speed to
  `MaxSpeed × |move_a| / 100`, so a diagonal is not faster than a cardinal and a control layer can
  steer to a point instead of snapping to eight directions. Everything else in the step is paintbot's.
- **Aim.** Every cog carries an aim angle in **brads** (256 per turn, 0 = east, counter-clockwise —
  paintbot's convention, `src/ctf/sim.nim:2149-2157`), turned at most `aimTurnRate = 8` brads/tick.
  Aim is cosmetic for cogs (sprite facing and the viewer's little indicator line): a cog's attacks
  hit their chosen target, not wherever they point. **The boss's aim is not cosmetic** — its cleave
  cone is taken from its facing.
- **The determinism boundary.** The sim consumes, and the replay records, exactly four bytes per cog
  per tick: `(move_x i8, move_y i8, aim_turn i8, action u8)`, where `action` is a bitfield
  `bit0 = attack`, `bit1 = taunt`, `bit2 = heal`, `bit3 = shield`, `bit4 = interrupt`, bits 5–7
  reserved 0. Ability *targets* are not in the bytes; they are part of the installed order and are
  re-derived identically by the control layer from the recorded state (§Sim module, "Determinism
  contract").

### Roles, abilities, and resources

Damage and healing are integers. Every subtraction goes through one funnel modelled on paintbot's
`absorbDamage` (`src/ctf/sim.nim:844-882`): an absorb shield is spent first, then hit points.

| | **Tank** | **Healer** | **DPS** (×3) |
|---|---|---|---|
| Max HP | **300** | **160** | **180** |
| Attack range | 40 px (melee) | 300 px | 420 px |
| Attack cooldown | 12 ticks (0.5 s) | 24 ticks (1.0 s) | 18 ticks (0.75 s) |
| Attack damage | 12 | 8 | 34 |
| Threat per damage | **×3** | ×1 | ×1 |
| Signature | **Taunt** | **Heal**, **Shield** | **Interrupt** |

- **Attack** is automatic: the control layer holds `bit0` whenever the order's target is alive, in
  range and line-of-sight-clear and the cooldown is at 0. The order chooses *what* to hit.
- **Taunt** (tank, `bit1`): range 200 px, cooldown **192 ticks (8 s)**, instant. Sets the tank's
  threat to `1.15 ×` the highest current threat and **locks the boss's target to the tank for 72
  ticks (3 s)**. A taunt fired while the tank already holds the target still consumes the cooldown
  and records `taunt{result:"already_target"}` — wasting it is a real mistake.
- **Heal** (healer, `bit2`): range 360 px, LOS required, **cast 24 ticks (1.0 s)**, heals **90 HP**,
  costs **60 mana**, no cooldown. The cast is cancelled (mana refunded, `heal{result:"cancelled"}`)
  if the healer moves more than 8 px, the target dies, or LOS breaks. Overheal is recorded and
  wasted. Healing adds **0.25 threat per HP actually healed** to the healer.
- **Shield** (healer, `bit3`): instant, range 360 px, **120 absorb** on one ally, costs **150 mana**,
  cooldown **360 ticks (15 s)**, expires after 480 ticks (20 s) if unspent. Reuses paintbot's
  `shieldHp` layer inside `absorbDamage`.
- **Mana** (healer only): **1200 max**, **+30 on every tick where `t mod 24 == 0`** (30/s), so the
  sustained ceiling is 45 HP/s of healing and the 1200-point pool is a burst reserve worth ~20
  extra heals. Triage is forced; blanket-healing runs the pool dry before phase 3.
- **Interrupt** (DPS, `bit4`): instant, range 420 px, LOS required, cooldown **480 ticks (20 s)**.
  If SMELTER-9 is casting an interruptible ability it is cancelled. If two interrupts land on the
  same cast in the same tick, the **lower slot index wins** and the other records
  `interrupt{result:"wasted"}` with its cooldown burned — three DPS with one interrupt each and one
  cast every 20 s means the raid must actually assign the job.
- **Death is final.** No resurrection, no respawn: paintbot's `respawnPlayers`
  (`src/ctf/sim.nim:3473`) is dropped. A dead cog is inert, contributes nothing, and is not asked for
  an order. Five deaths is a wipe.

### SMELTER-9 — the scripted boss (exact)

`bossMaxHp = 26000`. Body 56 × 56 at (617, 329); the boss **never moves** — it is bolted to its
stand. It faces its current target: its aim turns at most 6 brads/tick toward that target, except
during a cleave telegraph, when **its facing is frozen** (that is what makes side-stepping work).

**Threat and targeting.** Every point of damage dealt to the boss adds threat (tank ×3); every HP
healed adds 0.25 threat to the healer. On every tick where `t mod 24 == 0` the boss retargets to the
highest-threat living cog, but only if that cog's threat exceeds the current target's by **more than
10 %** (stickiness). A taunt overrides both rules for 72 ticks.

**Boss melee.** Every **36 ticks (1.5 s)**, `bossMeleeDamage = 55` to its current target if that cog
is within **60 px**; if the target is out of reach the swing whiffs and is recorded
(`boss_hit{ability:"swing", amount:0}`) — kiting the boss out of melee is legal, costs the raid
nothing directly, and is exactly the thing that gets a tank killed when the healer follows.

**Phases** — by boss HP percentage, checked every tick, one-way, never re-entered:

| Phase | Boss HP | Name | What is on |
|---|---|---|---|
| **1** | 100 % → 70 % | *Forge* | melee, Cleave, Slag Pour |
| **2** | 70 % → 35 % | *Slag* | + Slag Crawler waves, + Overload |
| **3** | 35 % → 0 % | *Meltdown* | melee, Cleave (faster), **Crucible Pour** replaces Slag Pour, Overload, one add wave at entry |
| **Enrage** | any, at `t ≥ 5760` (240 s) | *Enrage* | boss damage **×3**, melee period 36 → 24 ticks; permanent |

A phase transition zeroes every ability's schedule counter and restarts it, emits `phase_start`, and
(entering 2 or 3) spawns an add wave immediately.

**Ability 1 — Cleave** (all phases). A frontal cone: **±32 brads (±45°) around the boss's frozen
facing, reach 180 px** from the boss's centre. **Telegraph 48 ticks (2.0 s)** — the cone is drawn on
the floor from the tick the cast starts. On resolution: **120 damage** to every living cog whose body
centre is inside the cone. Cadence, measured from the previous cleave's resolution:
**192 ticks (8 s) in phase 1, 168 (7 s) in phase 2, 144 (6 s) in phase 3.** The first cleave of an
encounter starts at tick 96.

**Ability 2 — Slag Pour** (phases 1 and 2). At cast start the boss draws one living **non-tank** cog
uniformly from the episode PCG32 stream and stamps a circle of **radius 90 px** on that cog's
position *at that instant*. **Telegraph 60 ticks (2.5 s).** On resolution: **80 damage** to every
living cog inside, and a **slag pool** of radius 90 px is left for **240 ticks (10 s)**, dealing
**12 damage** to every cog inside it on every 24th tick after the pool's spawn tick (paintbot's
`updatePuddles` occupancy shape, `src/ctf/sim.nim:2761-2808`, made RNG-free). At most **6** pools
exist; a seventh expires the oldest. Cadence from previous resolution: **240 ticks (10 s) phase 1,
216 (9 s) phase 2.** First pour at tick 192.

**Ability 3 — Crucible Pour** (phase 3 only; replaces Slag Pour). Same draw, **radius 110 px**,
**telegraph 72 ticks (3.0 s)**, cadence **168 ticks (7 s)**. On resolution, let `k` be the number of
living cogs whose body centre is inside:
- `k == 0` → nobody soaked: the boss gains one permanent **Spill** stack, **+20 % boss damage each,
  maximum 5 stacks**, and no pool is left.
- `k ≥ 1` → **240 damage split evenly**, `240 div k` to each (240 alone, 120 each for two, 80 for
  three), and a 240-tick pool is left.
This is the encounter's one true soak: one DPS alone dies to it, the tank alone survives it and then
needs a heal, two cogs eat it cheaply. It is the mechanic that most rewards five strangers agreeing
on something in advance, and the viewer draws the required-bodies pip on the circle.

**Ability 4 — Overload** (phases 2 and 3). A **96-tick (4.0 s) cast** with a visible cast bar,
started every **480 ticks (20 s)** measured from the phase's entry tick. **Interruptible.** If it
completes: **70 damage to all five cogs** and the boss **heals 400 HP** (which can push it back
above a phase threshold in HP but never re-enters a phase — the phase only ever advances). If
interrupted: the cast is cancelled, `interrupt{result:"success"}` is recorded, and the next Overload
is scheduled 480 ticks from the cancellation.

**Ability 5 — Slag Crawlers (the adds)** — phase 2, plus one wave at phase-3 entry. At phase-2 entry
and every **360 ticks (15 s)** while in phase 2, **2 crawlers** spawn at the two alcoves furthest
from the current boss target. A crawler: **220 HP**, `MaxSpeed = 640` (2.5 px/tick), body 16 × 16,
melee **range 30 px**, **18 damage every 24 ticks (1.0 s)**, no ranged attack, moves by the same
integer step as a cog with straight-line steering plus the unstick rule (§Decisions). It targets the
highest-threat cog within 400 px, else the nearest living cog, retargeting every 24 ticks. Crawlers
take player damage normally and give no threat on the boss. **Cap 8 alive**; a wave that would exceed
it spawns fewer. **Feed:** while **4 or more** crawlers are alive the boss gains **+25 % damage**
(a visible buff, `feed_buff` events on both edges) — ignoring adds is not a free trade.

**Enrage** (`t ≥ enrageTicks = 5760`, 240 s). Emitted once as `enrage`. Boss damage ×3 (multiplying
with Feed and Spill), melee period 36 → 24 ticks. A raid at full health dies in roughly 10–15
seconds. The encounter still hard-stops at `maxTicks = 6480` (270 s), so enrage is a 30-second
execution window, not an infinite one.

**Damage multiplier order** (fixed, so the numbers are reproducible): `final = base × (1 + 0.25·feed)
× (1 + 0.20·spill_stacks) × (3 if enraged else 1)`, integer-truncated at the end.

### Time and turns

`dt = 1/24 s` (`TargetFps` / `ReplayFps` = 24, `src/ctf/sim_types.nim:294,353`).

| | Default variant |
|---|---|
| `turnTicks` (decision turn) | **120** ticks = 5.0 s |
| `enrageTicks` | **5760** = 240 s |
| `maxTicks` (hard end) | **6480** = 270 s |
| Decision turns, maximum | **54** |

A **decision turn** is 120 ticks. At the first tick of a turn the server freezes the state, builds a
view for every **living** seat, collects one **order** each (§Server), and hands them to the
deterministic control layer, which drives the cogs for all 120 ticks. The LLM is the raid leader at
0.2 Hz; the control layer is the reflexes at 24 Hz, and the order's `on_telegraph` field is how a
5-second decision reaches a 2-second mechanic (§Decisions). Dead seats are not queried.

### Resolution order (exact, per tick `t`)

Applied in this order every tick, no exceptions. "Seat order" always means ascending slot index 0…4;
"add order" means ascending add id.

1. **Clock and orders.** Derive `turn = t div turnTicks`. If `t mod turnTicks == 0`, install the
   orders collected for this turn (§Server: how they are collected and what happens when one is
   late). If `t == enrageTicks`, set `enraged = true` and emit `enrage`.
2. **Control compile.** For each **living** cog in seat order, the control layer (§Decisions, "The
   control layer") reads the current world state and that seat's active order and produces
   `(move_x, move_y, aim_turn, action)`. A dead cog produces `(0, 0, 0, 0)`.
3. **Quantise and record.** `move_x`, `move_y` → `int8` in −100…100; `aim_turn` → `int8` clamped to
   ±`aimTurnRate` (±8); `action` → the `uint8` bitfield. **These bytes are the whole input record**
   (§Sim module).
4. **Aim.** `aim = (aim + aim_turn) mod 256` per cog in seat order; then the boss turns at most
   6 brads toward its target **unless a cleave telegraph is live** (facing frozen); then each add
   faces its target (cosmetic).
5. **Cog motion.** Paintbot's integer step per cog in seat order: accelerate per axis by
   `Accel × |move_a|/100` in the sign of `move_a`, apply friction `×144/256` on any axis with
   `move_a == 0`, clamp each axis to `MaxSpeed × |move_a|/100`, integrate with
   `applyMomentumAxis`, resolve walls with the slide scan, then resolve cog–cog overlap for each
   unordered pair in ascending index order with restitution `PlayerBouncePct = 40`.
6. **Add motion.** Same step per add in add order, steering straight at its target with the unstick
   rule; adds collide with walls, pillars, the boss body and cogs.
7. **Timers.** Decrement every cooldown, tick every live cast (player heal casts and the boss's
   Overload), age every pool and telegraph, and on `t mod 24 == 0` add 30 mana to the healer (cap
   1200).
8. **Player abilities**, in this fixed sub-order so races are decidable:
   **(a) interrupt** (seat order; lowest slot wins a tie, the rest record `wasted`),
   **(b) taunt** (seat order), **(c) shield**, **(d) heal completion** (a cast that reaches 24 ticks
   this tick applies now), **(e) attacks** (seat order; each cog whose `bit0` is set, cooldown 0,
   target alive, in range, LOS clear deals its damage and resets its cooldown).
9. **Threat.** Fold this tick's damage and healing into the threat table.
10. **Boss retarget.** On `t mod 24 == 0`, and not while a taunt lock is live, retarget by the
    stickiness rule.
11. **Boss scheduling.** If no cast or telegraph is live and an ability's cadence counter has
    expired, start the highest-priority available ability in the order
    **Overload > Crucible/Slag Pour > Cleave** (only one boss ability is ever in flight); emit
    `cast_start` and/or `telegraph`.
12. **Telegraph resolution.** Every telegraph whose fuse expires this tick resolves, in creation
    order: compute the hit set, apply damage through the absorb funnel, spawn pools, apply Spill,
    emit `telegraph_resolve`.
13. **Pools.** For each pool in creation order, if `(t − pool.spawn_tick) mod 24 == 0` and `t >
    pool.spawn_tick`, deal 12 damage to every living cog whose centre is inside. Expire pools older
    than 240 ticks (`pool_expire`).
14. **Boss and add attacks.** Boss swing if its period elapsed; then each add in add order.
15. **Deaths.** Any cog at `hp ≤ 0` dies (`death`, killer attributed to the last damage source), is
    frozen in place as a wreck and stops accruing anything; any add at `hp ≤ 0` dies (`add_death`);
    if the boss reaches `hp ≤ 0` it is dead as of this tick.
16. **Phase check.** If the boss is alive and its HP fraction has crossed 0.70 or 0.35 downward,
    advance the phase (§Phases) and emit `phase_start`.
17. **Meters.** Accrue per-seat `damage_to_boss`, `damage_to_adds`, `healing_done`, `overhealing`,
    `damage_taken`, `avoidable_hits` (a hit by a telegraph the cog was inside at resolution).
18. **Keyframe.** If `t mod 24 == 0`, append a keyframe (§Server → Replay bytes).
19. **End check.** In order: boss dead → `complete`/`kill`; all five cogs dead → `complete`/`wipe`;
    `t + 1 == maxTicks` → `complete`/`enrage_timeout`; wall-clock budget exceeded → `deadline`/
    `wall_clock`. Emit `end`, score, write artifacts.

### Scoring, sign, and what the league ranks by

The idea's pin, with the denominator closed as decided in re-reading 1:

```
bossMaxHp        = 26000                       (variant config)
removed          = bossMaxHp - max(0, bossHpFinal)
f                = removed / bossMaxHp                       in [0, 1]
T                = enrageTicks / 24             = 240.0 s    (variant config)
elapsed          = finalTick / 24                            seconds actually simulated
charged          = elapsed        if end_rule == "kill"
                 = T              for every other ending (wipe, enrage_timeout,
                                   wall_clock, sim_fault, host_error)

score            = clamp(f * T / charged, 0.0, 3.0)          -- one number
results.scores   = [score, score, score, score, score]       -- shared equally
```

**Higher is better.** `score` is exactly "boss health removed ÷ time spent", expressed in units of
the enrage timer so that **1.0 means "killed it exactly on the enrage timer"**. Faster kills score
above 1.0; anything that is not a kill scores the fraction of the boss it removed, because the raid
consumed the whole attempt. Zero is the floor (a raid that never lands a hit). The clamp at 3.0 is a
guard, not a design target: the arena's maximum sustained raid output is ≈ 168 HP/s (3 DPS at
45.3 + tank 24 + healer 8), so the fastest physically possible kill is ≈ 155 s → 1.548, and a real
kill lands between 1.05 and 1.35.

Worked examples:

| Ending | `f` | `elapsed` | `charged` | score |
|---|---|---|---|---|
| Clean kill at 192 s | 1.00 | 192.0 | 192.0 | **1.250** |
| Kill 4 s into enrage, 244 s | 1.00 | 244.0 | 244.0 | **0.984** |
| Wipe at 150 s with 71 % removed | 0.71 | 150.0 | 240.0 | **0.710** |
| Survived to the 270 s hard end at 88 % | 0.88 | 270.0 | 240.0 | **0.880** |
| Wall-clock `deadline` at 130 s, 44 % removed | 0.44 | 130.0 | 240.0 | **0.440** |
| Instant faceplant: wipe at 12 s, 3 % removed | 0.03 | 12.0 | 240.0 | **0.030** |

Note the last row against the naive reading: charging the wipe the full attempt is what makes
"everyone burns and dies" score 0.03 instead of 0.60.

**Every seat carries the identical score** — the idea's "shared equally", and the reason a healer
who never damages the boss can still be a champion. `results.scores` is five copies of one number.
There is no per-seat differentiation in the score at all; the per-seat *meters* (damage, healing,
avoidable hits) are recorded for the endcard and for humans, and are **not** part of the score.

**What the league ranks by:** the seat's **mean `results.scores` value across its episodes**. Elo is
wrong here and phase 50 must not use it — with five identical scores every episode is a five-way
draw and Elo cannot separate anybody. The sim's obligation is only to write one identical,
comparable, higher-is-better number into every seat of `results.scores`; the division's ranking mode
is a phase-50 setting.

**League operations (recorded, not sim logic).** The idea's integrity clause is a scheduling
requirement on the ladder, and the sim is deliberately blind to it:
(a) the five seats of an episode must be drawn from **five different accounts** — no account may hold
two seats in one episode; (b) a seat's ranking figure is its **cross-play mean**, computed over
episodes whose teammate mix varies, and must **include episodes seated with frozen scripted
baselines** (`raid-stalwart`, `raid-greenhorn`) so that a policy which only performs alongside its
own twin is visible as such. Without (b) the ladder measures a hardcoded protocol between
co-submitted policies rather than ad-hoc teamwork. Phases 50 and 60 own this; **v1 game code has no
notion of accounts, and no rule in this note depends on who is seated.**

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly **three** values; `results.end_rule` carries the detail
and is a closed enum of exactly **five**.

| `reason` | `end_rule` | When | Score |
|---|---|---|---|
| `complete` | `kill` | Boss HP ≤ 0. The good ending. | `f = 1`, `charged = elapsed` |
| `complete` | `wipe` | All five cogs dead. | `f` as removed, `charged = T` |
| `complete` | `enrage_timeout` | `maxTicks` (6480) reached with the boss alive and ≥ 1 cog alive. | `f` as removed, `charged = T` |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660) elapsed before any of the above. The sim stops at that tick. **Declared acceptable** for phase-60 verification: it means the hosted LLM was slow, not that the game broke, and the replay is complete up to the stop tick. | `f` as removed, `charged = T` |
| `fault` | `sim_fault` | A sim invariant guard tripped (a cog outside the disc, negative HP on a live entity, a pool or telegraph with a negative fuse, boss HP above max). | `f` as removed, `charged = T` |
| `fault` | `host_error` | An unexpected server-side exception. Best-effort artifacts are written before re-raising. | `f` as removed, `charged = T` |

No other value may appear in either field. A `fault` scores exactly like a `deadline` — the damage
actually dealt, with no speed credit — rather than a punitive zero; `reason: "fault"` is the flag the
league uses to discard the episode, so the score need not also punish. A seat that never connects
does **not** end the episode: its cog is driven by the `stalwart` scripted baseline for the whole
encounter, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` (lowest offending slot only,
paintbot's `declarePlayerFailure`, `src/ctf/server.nim:1213-1230`), and the raid plays on.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {stalwart, greenhorn}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=stalwart`. **A scripted policy seated as a champion is a failure state.**

**Where the decision happens.** *Deviation from paintbot, deliberate:* paintbot's bot decides inside
its own container (`players/baseline/baseline.nim`, a Sprite-v1 client). In raid the **game server**
owns the LLM client, exactly as bullwhip does (`src/bullwhip/llm.nim`). Reasons: the hosted Bedrock
sidecar credentials and the `anthropic_api_key` coworld secret are injected into the *game* pod;
phase 60 greps the *game* log for `falling back` / `LLM provider is unavailable`; "one parallel batch
per turn" is a game-server property; `templates/tools/ci/docker_smoke.sh` forwards
`ANTHROPIC_API_KEY` to the game container only (line 186-191); and keeping both policy kinds inside
the server makes the recorded control log reproducible with no network in the loop. The player
container is therefore thin: it connects, sends one `register` frame carrying its prompt (or its
baseline name), and thereafter only receives (§Server).

**Cadence and batching.** One decision turn every `turnTicks = 120` ticks (5.0 s), at most 54 turns.
At each turn the server builds the **living** seats' request bodies and issues them as **one parallel
batch** — a single `curly.makeRequests(batch, timeoutSeconds)` over all open seats, exactly
bullwhip's `decideAll` (`src/bullwhip/llm.nim:419-472`) — wrapped in one per-turn deadline.
**Seats are never queried sequentially.** A full turn batches 5 requests; after two deaths it batches
3. Per episode, worst case: 54 × 5 = **270 LLM calls**, at most 5 in flight; a typical kill at ~200 s
is 40 turns and fewer than 200 calls.

**Wall-clock arithmetic (must stay inside 60 % of `episodeTimeoutSeconds` 1200 = 720 s):**

```
54 turns x 10.0 s per-turn budget             = 540 s
player connect wait (5 seats, typical)        =  20 s   (cap: playerConnectTimeoutSeconds 90)
sim: 6480 ticks x (5 cogs + boss + <=8 adds)  =   3 s   (perf test bounds this at <= 30 s)
board bake + results + replay writes          =  30 s
                                              -------
expected worst case                           = 593 s   < 720 s  (127 s margin)
engine hard stop wallClockBudgetSeconds       = 660 s   -> reason "deadline"
platform kill (episode_timeout_minutes 20)    = 1200 s
```

Typical is far under: a turn whose slowest living seat answers in 4 s costs 4 s, not 10; most
episodes end on a kill or a wipe before turn 54; and dead seats drop out of the batch. With no
credentials at all (offline certification, the docker smoke) the LLM client disables itself on first
discovery, every turn falls back instantly with no network wait, and the whole episode finishes in
seconds.

**Per-turn timing, per seat:** first attempt deadline **6.5 s**. On timeout, transport error,
non-JSON reply, or a reply carrying no usable order → **one retry** with a **3.0 s** deadline and the
"your previous reply was invalid, reply with a single JSON object beginning with `{`" hint appended
(bullwhip's retry shape). If that also fails → that seat's order for this turn is the **`stalwart`
scripted order**, computed in microseconds, and a `fallback` event is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`. Worst case
6.5 + 3.0 = 9.5 s ≤ the 10.0 s turn budget.

**Budget guard (settle early rather than overrun).** At the start of each turn, if
`elapsed + 2 × turnBudgetSeconds > wallClockBudgetSeconds`, the LLM is skipped for **all remaining
turns** and the encounter finishes on the scripted layer (< 1 ms per turn), so it ends
`complete/kill|wipe|enrage_timeout` instead of `deadline`. A `budget_guard` event records the turn it
engaged. Only if even that overruns — arithmetically impossible, but the check is unconditional —
does the engine stop at 660 s with `deadline/wall_clock`.

**Degrade, never hang.** Every wait is bounded: the two attempt deadlines, one outer per-turn
deadline of 10.0 s, `playerConnectTimeoutSeconds` (90 hosted, 60 in the cert fixture) on the connect
wait, a 3.0 s per-seat deadline on the final done-broadcast, and the 660 s engine stop. The game
container does **not** receive `COWORLD_TIMEOUT_SECONDS`; 1200 s is assumed and never approached. A
seat that disconnects mid-encounter keeps playing: its order source degrades to `stalwart` and
revives on reconnect. No failure mode leaves a cog unactuated — the control layer always has an
order, defaulting to the previous turn's, then to `stalwart`.

**The LLM client** (`src/raid/llm.nim`) is bullwhip's `llm.nim` with raid's schema. Credential
ladder, in order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` + `AWS_BEARER_TOKEN_BEDROCK`,
region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI` (read through `readCogameUri`) → none (disabled, instant fallback, one log
line). Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, `us.anthropic.claude-sonnet-4-6`,
`us.anthropic.claude-sonnet-4-5-20250929-v1:0`; on a 403 the client advances to the next candidate.
`max_tokens = 900` (400 truncates — playbook gotcha), **no `output_config.effort`** (Haiku 4.5
rejects it), `temperature = 0.4`.

**System prompt (fixed, identical for every seat and both champions, sent as the system message):**

```
You are one of five cogs fighting SMELTER-9, a scripted foundry boss, in a round pit
300 pixels in radius centred at (617,329) on a 1235x659 floor, x right, y down. Four
40x40 pillars at (511,223) (723,223) (511,435) (723,435) block movement, sight, heals
and ranged attacks - but not floor effects.
Your role was DEALT to you this episode: tank, healer or dps. It is in your view. Play
the role you got.
The boss is bolted to the centre and never moves. It swings at its highest-threat cog
every 1.5 s. It has three phases: Forge (100-70% hp), Slag (70-35%: adds and Overload),
Meltdown (35-0%: Crucible Pours). At 240 s it ENRAGES (triple damage) and the fight is
hard-stopped at 270 s.
Mechanics: CLEAVE is a 90-degree cone 180 px in front of the boss, telegraphed for 2 s -
only the tank should be in it. SLAG POUR drops a 90 px circle on a random non-tank,
telegraphed 2.5 s, and leaves a burning pool for 10 s. CRUCIBLE POUR (phase 3) is a
110 px circle telegraphed 3 s: 240 damage SPLIT between everyone standing in it, and if
NOBODY stands in it the boss gains a permanent +20% damage stack. OVERLOAD is a 4 s cast
that hits all five for 70 and heals the boss 400 unless ONE dps interrupts it - two
interrupts on the same cast wastes one. SLAG CRAWLERS spawn in pairs during phase 2; at
four or more alive the boss deals +25% damage.
Every 5 seconds you issue ONE order. A deterministic controller executes it for the next
5 seconds: it walks you to your station, holds your attack on your target, and performs
the reaction you pre-authorised in "on_telegraph" the instant a telegraph appears. You
do not drive motors directly, and you cannot react faster than your order allows - so
choose the reaction, not the dodge.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"intent":"<one of the legal intents for your role>",
 "target":"boss|A1..A8|Alpha|Bravo|Charlie|Delta|Echo|null",
 "station":"melee|ranged|spread|edge|point|soak",
 "point":[x,y],              // used when station is "point"; clamped into the pit
 "on_telegraph":"dodge|hold|soak|spread",
 "note":"<=160 chars",       // your reasoning, shown to spectators only
 "say":"<=32 chars"}         // one short callout; your four team-mates SEE this next turn
Tank intents: tank_boss, taunt, pick_up_adds, kite, soak, wait.
Healer intents: heal_lowest, heal_target, shield_target, conserve, soak, wait.
Dps intents: burn_boss, kill_adds, interrupt, assist_target, soak, wait.
Stations: melee = 40 px ring around your target; ranged = 260 px ring from the boss;
spread = at least 140 px from every team-mate; edge = the pit rim behind you;
point = the exact point you named; soak = the middle of the live pour circle.
on_telegraph: dodge = leave the shape; hold = stay and keep attacking; soak = step into
a pour circle; spread = get 140 px from everyone. The tank normally holds cleaves and
everyone else dodges them.
```

**User message** = the seat's `PLAYER_PROMPT` text, then a blank line, then the seat's view JSON
(§Server). The prompt text is never echoed into the replay or the results (only `policy_kind`).

**Champion #1 — `raid-anvil` (owner daveey), `PLAYER_PROMPT`:**

```
Hold the pull together: nothing kills a raid faster than five cogs answering the same
mechanic differently.
If you are the TANK: open with intent "tank_boss", station "point", point [617,180] -
stand NORTH of the boss so its facing, and therefore every cleave, points at the empty
top of the pit and never at your team. Keep on_telegraph "hold" for the whole fight: you
are supposed to eat cleaves, and stepping out of one drags the cone across the raid on
the next retarget. Taunt the moment the boss's target in your view is not you - do not
taunt on cooldown for its own sake, a wasted taunt is eight seconds you do not have when
a dps pulls. When crawlers spawn, switch to "pick_up_adds" for exactly one order to
gather them, then back to "tank_boss": adds beating on you are adds not beating on the
healer. In phase 3 take the crucible yourself with intent "soak" whenever your hp is
above 60% - you are the only cog who survives it alone.
If you are the HEALER: station "ranged" and stand where a pillar is never between you
and the tank. Use "heal_lowest" while anyone is under 60%, "conserve" whenever everyone
is above 75% - your mana is 1200 and regenerates 30 a second, so blanket-healing runs
you dry before Meltdown and a dry healer is a wipe. Shield the tank just before a cleave
lands, not after. on_telegraph "dodge" always; you cannot afford one avoidable hit.
If you are DPS: "burn_boss" from station "ranged", on_telegraph "dodge". Say your
interrupt claim out loud on the first turn of phase 2 - "I interrupt" - and if a
team-mate already claimed it, do not hold "interrupt" yourself, stay on "burn_boss".
Switch to "kill_adds" the moment three or more crawlers are alive and switch back the
moment it is under three. In phase 3, if your hp is above 150 and no team-mate has
called a soak, take the crucible with intent "soak".
```

**Champion #2 — `raid-triage` (owner daveey-1,
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`:**

```
Play the clock, not the boss. 240 seconds of enrage timer is the only real enemy;
everything else is a tax on your damage.
If you are the TANK: station "point" and put yourself on the far side of the boss from
wherever the pour circles have been landing, so the cleave cone sweeps dead floor.
on_telegraph "hold". Taunt pre-emptively at the start of every phase - the retarget on a
phase change is where tanks lose the boss - and never otherwise. Do not chase crawlers
across the pit: use "pick_up_adds" only when the adds are already within 200 px of you,
otherwise the boss walks out of your team's range and every dps loses uptime.
If you are the HEALER: triage by role, not by percentage. The tank is the only cog whose
death ends the fight immediately, so keep it topped with "heal_target" on the tank
whenever the tank is under 80%; a dps at 40% that is dodging correctly will live. Shield
the cog the pour just picked, not the lowest one. Spend your whole mana pool in phase 3
- there is no phase 4 to save it for. on_telegraph "dodge", except "soak" in phase 3 if
your hp is over 120 and you can see the tank is already low.
If you are DPS: your job is dps uptime, so pick a station and stop moving. Use "ranged"
and on_telegraph "dodge"; only spread when the raid is bunched. Take "interrupt" as your
standing intent for the entire fight if nobody else has said they are on it - an
Overload that lands costs the raid 400 boss hp plus 350 raid hp, which is worth more than
four seconds of your damage. Ignore crawlers entirely unless four are up (that is when
the boss starts hitting 25% harder) and then kill exactly enough to get back under four.
Call your target out with "say" every time you switch.
```

### The control layer (deterministic; shared by every policy)

LLM orders and scripted orders are compiled by the *same* code, so the two policy kinds are strictly
comparable and the recorded control bytes are the whole truth. Per living cog per tick:

1. **Reaction override.** If a telegraph is live *and* its shape contains (or, for `soak`, does not
   contain) this cog, the order's `on_telegraph` value takes over the steering point for as long as
   the telegraph is live:
   - `dodge` → `p* = ` the nearest point **20 px outside** the shape along the outward direction
     (for a circle, away from its centre; for the cleave cone, perpendicular to the cone's bisector,
     picking the side with more free floor by an integer free-cell count).
   - `hold` → no override.
   - `soak` → `p* = ` the circle's centre (no effect on a cleave).
   - `spread` → `p* = x + 160 · û(x − centroid_of_other_living_cogs)`.
2. **Steering point `p*`** otherwise, from `intent` and `station` (`x` = own position, `B` = boss
   centre, `Tg` = the order's target entity):
   - `station: melee` → the point 40 px from `Tg` on the line from `Tg` to `x`.
   - `station: ranged` → the point 260 px from `B` on the line from `B` to `x`.
   - `station: spread` → `x` if already ≥ 140 px from every other living cog, else
     `x + 140 · û(x − nearest_cog)`.
   - `station: edge` → the point on the 280 px radius circle nearest `x`.
   - `station: point` → the order's `point`, clamped into the pit.
   - `station: soak` → the live pour circle's centre if one exists, else falls through to `ranged`.
   - `intent: kite` (tank) → `p* = x + 120 · û(x − B)`, recomputed every tick.
   - `intent: wait` → `p* = x`.
3. **Move command.** `d = p* − x`; if `|d| ≤ 8`, `move = (0, 0)`; else `move = û(d)·100` in integers.
   `û(v)` scales `v` to length 100 using an integer square root — **no floating point** (§Sim
   module). **Unstick rule:** if the cog's net displacement over the last 24 ticks is < 6 px while
   `move ≠ (0,0)`, rotate `move` by +45° from an eight-entry integer direction table and keep
   rotating once per 24 ticks until it moves. There is **no pathfinder**: a station behind a pillar
   is a bad order, and reading the pit is part of the skill.
4. **Aim command.** Turn at most `aimTurnRate = 8` brads/tick toward the current attack target,
   else hold.
5. **Action bits.**
   - `bit0 attack` — set whenever the resolved attack target is alive, within the role's range and
     LOS-clear. Resolved target: `boss` for `tank_boss`/`burn_boss`/`taunt`/`kite`; the nearest
     living add for `pick_up_adds`/`kill_adds`; the ally's current target for `assist_target`; the
     named entity for an explicit `target`; for the healer, the boss whenever no heal is pending.
   - `bit1 taunt` (tank) — set on the first tick of the turn for `intent: taunt`, and additionally
     on any tick where the boss's target is not the tank **and** taunt is off cooldown, for
     `intent: tank_boss`. (So "hold aggro" is a standing behaviour and "taunt now" is an explicit
     order.)
   - `bit2 heal` (healer) — set when a heal target is selected and mana ≥ 60 and no cast is running.
     Target selection: `heal_lowest` → lowest `hp/maxHp` among living allies; `heal_target` → the
     named ally, falling back to lowest; `conserve` → lowest, but only while that ally is under
     40 % (else no heal, attack instead).
   - `bit3 shield` (healer) — set for `shield_target` when off cooldown and mana ≥ 150; also set
     automatically for any intent when a telegraph is live whose shape contains an ally with
     `hp < 40 %` and the shield is off cooldown.
   - `bit4 interrupt` (DPS) — for `intent: interrupt`, set on the first tick at which the boss has a
     live interruptible cast, the cog is in range with LOS, and the cooldown is 0. For every other
     DPS intent the bit is never set — the interrupt is only ever spent on purpose.

**Scripted baselines** (both emit the identical order JSON on the same 5 s cadence, so their output
is legal by construction and directly comparable to an LLM's; both are pure functions of the world
state — no randomness beyond the episode seed — which is what makes the bounded-orders test in
§Tests meaningful):

- **`stalwart`** — the certification player, the default, and the stronger of the two. Role-aware,
  written as the "correct" execution of the encounter:
  - *Tank:* `tank_boss`, `station: point`, `point = (617, 180)` (north of the boss, cone pointed at
    empty floor), `on_telegraph: hold`. Emits `taunt` on the first turn of every phase and on any
    turn whose view shows the boss's target is not the tank. Switches to `pick_up_adds` for one turn
    whenever ≥ 2 adds are alive within 260 px, then back. In phase 3 takes `soak` when
    `hp > 0.6 × maxHp`.
  - *Healer:* `station: ranged`, `heal_lowest` while any ally is under 70 %, `conserve` otherwise;
    `shield_target` on the tank whenever the shield is off cooldown and a cleave telegraph is live;
    `on_telegraph: dodge`.
  - *DPS:* `burn_boss` from `station: ranged`, `on_telegraph: dodge`; the **lowest-slot living DPS**
    takes `intent: interrupt` for the whole of phases 2 and 3 (that is the coordination the baseline
    hardcodes and an LLM has to discover); any DPS switches to `kill_adds` while ≥ 3 adds are alive;
    in phase 3 the highest-HP DPS takes `soak` when the tank is under 60 %.
- **`greenhorn`** — the second filler, deliberately weaker and different in shape, so the ladder has
  a spread. Everyone plays `burn_boss` / `heal_lowest` / `tank_boss` from `station: melee`,
  `on_telegraph: dodge` always (so the tank dodges its own cleaves and loses the boss), nobody ever
  takes `interrupt`, nobody ever takes `soak`, and adds are ignored entirely. It reaches phase 2
  reliably and almost never phase 3 — a clean floor for the ladder.

---

## Sim module

`src/raid/sim.nim` is paintbot's `src/ctf/sim.nim` with the CTF rule surface removed and the boss
encounter put in its place. What is kept, what is dropped, and what is new:

**Kept from paintbot, by path:**

- `src/ctf/sim_types.nim` → `src/raid/types.nim` — the motion constants (`MotionScale`, `Accel`,
  `FrictionNum`/`FrictionDen`, `StopThreshold`, `PlayerHalf`, `PlayerBouncePct`,
  `MovementSlideMaxScan`, `AimBradsTurn`), `TargetFps`/`ReplayFps` = 24, `PlaybackSpeeds`,
  `MapWidth`/`MapHeight`, and the **flatty wire types whose field order is sacred** (paintbot's
  `AGENTS.md` rule; it still holds — the live `/global` broadcast stream is flatty-encoded).
  `MaxSpeed` is re-pinned to 832 (§The game). `GameVersion` is kept as the rules gate and starts at
  `"1"` for raid (paintbot's GV43 history does not travel; the changelog-comment convention does).
- `src/ctf/arena.nim` → `src/raid/arena.nim` — the `mapSpec` loader, the `ArenaShape`
  rect/disc/diamond/diagonal/polygon stamping (raid uses `shapeDisc` for the pit and `shapeRect` for
  the pillars), the `wallMask` bake, the integer even-odd `pointInPolygon` with its STRICT-STRADDLE
  convention, the pixel and `lineOfSightClear` queries (`src/ctf/sim.nim:590`), and the
  process-global map install. **Dropped:** the procedural generator, the validators,
  `mapDiagnostics`, `map_pool.nim`, `mapgen_styles.nim` and the whole
  `mapSize`/`mapSymmetry`/`mapEndzone` knob family. *Deviation, deliberate:* raid ships **one
  authored map**, `foundry`, because a boss encounter is tuned against a specific floor — pillar
  positions decide whether the healer can see the tank — and a seeded draw would make two episodes
  incomparable. Arena variety is §Out of scope (v1).
- `src/ctf/sim.nim:303-498` — `signOf`, `slideScanRadius`, `playersOverlapAt`, `blockingPlayerAt`,
  `canSlideHorizontal`/`canSlideVertical`, `trySlideOffset`, `trySlideMove`, `bouncePlayers`,
  `applyMomentumAxis`: the whole integer motion and collision core, unchanged except for the analog
  accel/clamp scaling in §The game.
- `src/ctf/sim.nim:844-882` (`absorbDamage`) and `:748` (`killPlayer`) → `src/raid/combat.nim` —
  the single damage subtraction point with the shield-absorb layer and the per-entity
  `damageTaken`/`damageDealt` counters that become the endcard meters. Death handling loses respawn
  and lives.
- `src/ctf/sim.nim:2761-2808` (`updatePuddles`) → `src/raid/pools.nim` — the occupancy-timed floor
  hazard, with paintbot's `PuddleRollTicks = TargetFps` cadence kept and its **RNG roll removed**
  (a raid pool bites every second, deterministically).
- `src/ctf/sim.nim:1651-1819` (`explodeGrenade`) → the shape of `src/raid/telegraphs.nim`'s radial
  resolution: a centre, a radius, an integer `dx*dx + dy*dy <= r*r` body test against `±PlayerHalf`,
  and one damage call per victim in index order.
- `src/ctf/sim_state.nim` → `src/raid/state.nim` — logging, the `gameHash` state digest, the event
  buffer, spawn placement. `src/ctf/sim_config.nim` → `src/raid/config.nim` — the `GameConfig`
  lifecycle and `configJson()`. `src/ctf/roster.nim` → `src/raid/roster.nim` — join/auth/slots/
  tokens. `src/ctf/events.nim`, `src/ctf/labels.nim`, `src/ctf/broadcast.nim` and the sprite-protocol
  broadcast layer of `src/ctf/global.nim` are kept (the live `/global` stream and the viewer both
  ride them); the CTF-specific art in `global.nim` is replaced (§Viewer).
- `src/ctf.nim` → `src/raid.nim` — the entrypoint, **including the rule that seed randomisation
  happens before `config.update`** (`src/ctf.nim:7-46`, `seedPinned` / `randomSeed` /
  `stripUnpinnedSeed`) so every seed-derived draw — here, the role deal and the pour target draws —
  follows the final seed.

**Dropped entirely:** guns and hitscan, aim jitter, grenades, the barrage, med kits, the plasma arc,
paint puddles and stains, spray cans, flags and pedestals, teams, lives/respawn, perks, handicaps,
achievements, shouts, the four-team mode, **the shadowcast FOV and `fovCaches`
(`src/ctf/sim.nim:2245-2498`)**, the map editor (`tools/map_editor*`), the `arena/` WIT component
bindings, `caos/` and `caos-tools/`. Roughly two thirds of paintbot's ~25 k lines of `src/` do not
survive the fork; what survives is the loop, the physics, the damage funnel, the floor hazard, the
arena, the replay and the chrome.

**New:** `src/raid/boss.nim` — the phase clock, the ability scheduler, threat and retargeting, adds;
`src/raid/telegraphs.nim` — telegraph shapes, fuses and resolution; `src/raid/pools.nim`;
`src/raid/abilities.nim` — taunt/heal/shield/interrupt/attack and the mana pool;
`src/raid/control.nim` — the control layer; `src/raid/orders.nim` — the order schema, tolerant
parsing and repair; `src/raid/llm.nim` — bullwhip's client; `src/raid/baselines.nim` — `stalwart` and
`greenhorn`; `src/raid/scoring.nim` — the formula in §The game; `src/raid/replay.nim` — the JSON
replay writer/reader.

**The map file.** `data/foundry.mapspec.json`, loaded by `mapPath: "foundry"`, is authored (not
generated) and pinned verbatim into every replay's config, exactly as paintbot pins `mapSpec`:

```json
{"name": "foundry", "width": 1235, "height": 659,
 "pit": {"cx": 617, "cy": 329, "r": 300},
 "pillars": [{"x": 491, "y": 203, "w": 40, "h": 40},
             {"x": 703, "y": 203, "w": 40, "h": 40},
             {"x": 491, "y": 415, "w": 40, "h": 40},
             {"x": 703, "y": 415, "w": 40, "h": 40}],
 "boss_stand": [617, 329],
 "cog_spawns": [[497,545],[557,561],[617,567],[677,561],[737,545]],
 "add_alcoves": [[419,131],[815,131],[419,527],[815,527]],
 "ranged_ring_px": 260, "edge_ring_px": 280}
```

(Pillar rects are given top-left; their centres are the (511,223)… quartet in §The game.) A test
asserts every spawn, alcove and ring point sits on free floor inside the pit, that the pit is
four-fold symmetric about its centre, and that from every cog spawn there is a line of sight to the
boss stand.

**Randomness.** One PCG32 stream seeded from the episode seed, integer arithmetic only, used for
exactly two things: the **role deal** and the **pour target draw**. Everything else — every cadence,
every damage number, every add spawn point — is deterministic. Two episodes with the same seed and
the same control bytes are byte-identical.

**No fog of war** (deviation, reason in §The game). `computeFovShadowcast`, `applyFovCone`,
`refreshPlayerFov`, `playerVisibleTo` and the `fovCaches` are removed; `lineOfSightClear` stays,
because ranged attacks, heals and interrupts need it.

**State digest.** `raidStateDigest()` returns an FNV-1a u32 over the raw bytes of every cog's
position/velocity/aim/hp/shield/mana/cooldowns, the boss's hp/aim/target/phase/schedule counters,
every add's position/hp/target, every pool's centre/age, every live telegraph's kind/centre/fuse, the
threat table and the tick. It is paintbot's `gameHash` idea widened to the full state, it goes into
every keyframe, and it is the cross-build equality check that lets the wasm viewer prove it
re-derived the same encounter (paintbot already surfaces a mismatch as the `#mmwarn` line — kept).

**Determinism contract (the inviolable property).** Same seed + same control bytes ⇒ same digest at
every keyframe, in the native build *and* in the emscripten build. It holds because the whole step is
integer: **no `sin`, `cos`, `tan`, `atan2`, `pow`, `exp`, `ln`, `fmod`, `hypot`, `sqrt` or float
arithmetic of any kind appears in the sim step** — cones are compared in brads
(`abs(((bearing - facing + 128) mod 256) - 128) <= 32`), ranges as squared integers, unit vectors via
an integer square root. `-ffast-math` and float sim arithmetic are banned and the ban is grepped in
CI (§Tests). Ability *targets* are re-derived by the control layer from recorded state rather than
stored in the control bytes, so target selection is part of the same deterministic function.

**Performance.** The heavy per-tick cost is 5 cogs + 1 boss + ≤ 8 adds of integer motion plus at most
6 pool occupancy tests and 1 telegraph. This is an order of magnitude lighter than paintbot's
sixteen-player live game with shadowcasting. Target ≥ 20 000 ticks/s native (a full encounter ≈ 0.3 s
of CPU), tested with a generous 30 s bound.

---

## Server, player, protocol

`src/raid/server.nim` is a fork of `src/ctf/server.nim`: the same mummy HTTP/WebSocket server
(`newServer(httpHandler, websocketHandler, workerThreads = 4)`, `src/ctf/server.nim:1330-1333`), the
same routes (`GET /healthz` — `HealthPath`, `src/ctf/server.nim:60`; the player WebSocket at
`/player?slot=N&token=T`; the spectator `/global`; the browser clients under `/client/…`; and in
replay mode `/replay-data` + `/client/replay`), the same 403 on a bad slot/token and 409 on a
duplicate connection, the same `bitworld/runtime` `RuntimeConfig` contract (`COGAME_CONFIG_URI`,
`COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_LOAD_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI` — the last two `file://`-only
and loudly rejected otherwise, `src/ctf/server.nim:1288-1310`), the same **write order at the end of
an episode** (broadcast `done` to every seat with a 3.0 s per-seat deadline → write the replay →
`writeResults`, `src/ctf/server.nim:1940-1956`), and the same pre-listen board bake so a viewer's
first frame is instant.

**Player handshake (the only thing a player container must do).** On connect the player sends
exactly one text frame:

```json
{"type": "register", "prompt": "<strategy text or empty>",
 "scripted": "stalwart" | "greenhorn" | null,
 "policy": "<free label, <=48 runes>"}
```

`src/raid_player.nim` reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED` and
`PLAYER_POLICY_LABEL`, sends that frame, then receives until `{"done": true, …}` and exits 0. A seat
that never registers, or registers with neither field, is treated as `scripted: "stalwart"`.
`PLAYER_SCRIPTED` parsing follows bullwhip's `parseScriptKind` (`src/bullwhip/llm.nim:61`):
`stalwart`/`1`/`true`/`yes` → stalwart, `greenhorn` → greenhorn, anything else → none.

**Per turn the server pushes to each living seat** (informational — the seat is not required to
answer; decisions are made server-side):

```json
{"type": "turn", "turn": 17, "tick": 2040, "phase": 2,
 "role": "healer", "view": { … }, "order_source": "llm"}
```

and at the end `{"done": true, "result": { …the results document… }}`, then close. A seat that dies
receives one `{"type": "turn", …, "view": {"you": {"alive": false, …}}}` on the turn after its death
and nothing further until `done`.

### The per-seat view (exactly what is visible, and what is hidden)

Coordinates are integers (map pixels); times are seconds to one decimal. This object is both the
`view` in the turn frame and the tail of the LLM user message. **One shape for all three roles** —
role-specific blocks (`mana`, `cooldowns`) are present only where they apply.

```json
{"turn": 17, "of": 54, "tick": 2040, "phase": 2, "phase_name": "Slag",
 "clock": {"elapsed_s": 85.0, "enrage_in_s": 155.0, "hard_end_in_s": 185.0},
 "you": {"alias": "Charlie", "role": "healer", "pos": [742, 402], "alive": true,
         "hp": 132, "max_hp": 160, "shield": 0, "mana": 640, "max_mana": 1200,
         "threat": 1180, "attacking": "boss",
         "cooldowns_s": {"heal": 0.0, "shield": 7.5},
         "casting": {"ability": "heal", "target": "Alpha", "remaining_s": 0.4}},
 "boss": {"name": "SMELTER-9", "pos": [617, 329], "facing_brads": 64,
          "hp": 16120, "max_hp": 26000, "hp_pct": 62.0, "phase": 2,
          "target": "Alpha", "enraged": false,
          "buffs": {"feed": true, "spill_stacks": 0},
          "casting": {"ability": "overload", "remaining_s": 2.1,
                      "interruptible": true},
          "next_s": {"cleave": 3.5, "pour": 6.0, "overload": 22.1, "adds": 9.0}},
 "telegraphs": [{"id": 41, "kind": "pour", "shape": "circle",
                 "centre": [520, 430], "radius": 90, "resolves_in_s": 1.4,
                 "soak_needed": 0, "you_are_inside": false}],
 "raid": [{"alias": "Alpha", "role": "tank", "pos": [617, 180], "alive": true,
           "hp": 188, "max_hp": 300, "shield": 60, "threat": 41200,
           "attacking": "boss", "last_intent": "tank_boss",
           "say": "cone is north"}, … 5 entries, slot order … ],
 "adds": [{"id": "A5", "pos": [700, 250], "hp": 140, "max_hp": 220,
           "target": "Alpha"}, … ],
 "pools": [{"id": 12, "centre": [560, 470], "radius": 90, "expires_in_s": 4.0}],
 "callouts": [{"alias": "Alpha", "say": "cone is north"},
              {"alias": "Delta", "say": "I interrupt"}],
 "meters": {"damage_to_boss": [0, 4120, 3980, 4410, 210],
            "healing_done": [0, 0, 0, 0, 5320]},
 "your_last_order": { …the order you played last turn, or null on turn 0… }}
```

**Visible to every seat:** the whole pit and its geometry; the boss's exact HP, phase, facing,
target, buffs, live cast and the **seconds until each of its abilities next fires** (the schedule is
deterministic and documented in `docs/RULES.md`, so hiding it would reward memorisation, not play);
every live telegraph with its exact shape, fuse and, for a crucible, the bodies it needs; every add
and pool; all five cogs' positions, HP, shields, threat, current attack target and **last order
intent**; the running damage and healing meters; and the four other seats' **`say` callouts from the
previous turn** — the raid's one communication channel, capped at 32 runes, deliberately public and
deliberately one turn stale.

**Hidden from every seat:** the other seats' full orders and their private `note` text; the episode
`seed`; the PCG32 draw for the *next* pour (the target is revealed only when the telegraph appears);
the boss's remaining schedule beyond the published `next_s` figures; every policy's `PLAYER_PROMPT`;
and the **real player names behind the aliases** — a seat never learns whether `Bravo` is a champion
or a baseline. That last asymmetry — aliases in-game, real names spectator-side — is the
two-name-space pin.

### Reply schema and character caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"intent": "heal_target", "target": "Alpha", "station": "ranged",
 "point": [742, 402], "on_telegraph": "dodge",
 "note": "tank is eating cleave plus feed; topping it and saving shield for the next cone",
 "say": "tank heals, dodge pours"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `intent` | enum, **≤ 16 runes** | tank: `tank_boss` `taunt` `pick_up_adds` `kite` `soak` `wait`; healer: `heal_lowest` `heal_target` `shield_target` `conserve` `soak` `wait`; dps: `burn_boss` `kill_adds` `interrupt` `assist_target` `soak` `wait` | unknown, or legal-for-another-role → `tank_boss` (tank) / `heal_lowest` (healer) / `burn_boss` (dps) |
| `target` | string / null, **≤ 12 runes** | `boss`, `A1`…`A8`, `Alpha`…`Echo`; case-insensitive | unknown id, dead entity, or an id illegal for the intent → the intent's natural target (boss for `burn_boss`/`tank_boss`, lowest ally for `heal_target`, nearest add for `kill_adds`); none available → the intent degrades to `wait` |
| `station` | enum, **≤ 8 runes** | `melee` `ranged` `spread` `edge` `point` `soak` | → `melee` for a tank, `ranged` otherwise |
| `point` | `[int, int]` | finite; clamped into the pit (any point whose distance from (617,329) exceeds 288 is pulled onto that circle) | missing/non-finite → the cog's current position |
| `on_telegraph` | enum, **≤ 8 runes** | `dodge` `hold` `soak` `spread` | → `dodge` |
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `say` | string | **≤ 32 runes** | truncated to 32 runes |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and `register.prompt` **≤ 4000 runes** at the
transport (an over-long prompt is truncated, not rejected) — the prompt is never written to the
replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes.** In Nim that means walking the
string with `runeSubStr`/`toRunes` and never slicing a `string` by byte index on any path that
reaches the replay, the results or another seat's `callouts`. A byte-truncated multi-byte character
is exactly the bug that makes replay bytes render in a browser but fail a strict JSON parser
(playbook gotcha), and §Tests pins it with a 4-byte emoji sitting on the 32nd rune of a `say`.

**Parsing is tolerant** (bullwhip's `extractJsonObject` shape, `src/bullwhip/llm.nim:312`): strip
markdown fences, take the outermost balanced `{…}` if the model prefixed prose, accept numeric
strings inside `point`, accept `target` as an integer 1–8 (read as `A<n>`) or as a slot index 0–4
(read as that alias). Only when no object with a usable `intent` can be recovered does the retry, and
then the fallback, fire.

### Results document (closed schema — must equal the manifest `results_schema` key-for-key)

Per-seat arrays are length **5** in slot order.

```json
{"names": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)", "Baseline (1)"],
 "aliases": ["Alpha", "Bravo", "Charlie", "Delta", "Echo"],
 "roles": ["tank", "dps", "healer", "dps", "dps"],
 "policy_kinds": ["llm", "llm", "scripted", "scripted", "scripted"],
 "scores": [1.25, 1.25, 1.25, 1.25, 1.25],
 "boss_hp_removed": 26000,
 "boss_max_hp": 26000,
 "boss_hp_removed_frac": 1.0,
 "elapsed_seconds": 192.0,
 "charged_seconds": 192.0,
 "enrage_seconds": 240.0,
 "phase_reached": 3,
 "kill": true,
 "wipe": false,
 "deaths": 1,
 "alive_at_end": 4,
 "damage_to_boss": [4980, 8210, 1020, 7900, 3890],
 "damage_to_adds": [820, 1140, 60, 900, 1180],
 "healing_done": [0, 0, 9860, 0, 0],
 "overhealing": [0, 0, 1240, 0, 0],
 "damage_taken": [9200, 640, 810, 1490, 2210],
 "avoidable_hits": [0, 1, 0, 2, 4],
 "interrupts_landed": [0, 3, 0, 2, 0],
 "interrupts_wasted": [0, 0, 0, 1, 0],
 "overloads_resolved": 1,
 "adds_killed": 8,
 "spill_stacks": 0,
 "reason": "complete",
 "end_rule": "kill",
 "final_tick": 4608,
 "final_turn": 39,
 "seed": 679961,
 "llm_turns": [39, 39, 0, 0, 0],
 "fallback_turns": [0, 0, 0, 0, 0],
 "fallback_causes": [{"timeout": 0, "parse_error": 0, "transport_error": 0,
                      "no_credentials": 0, "budget_guard": 0}, … 5 … ]}
```

Adding or removing a key here means editing `coworld_manifest_template.json`'s `results_schema` and
`tools/ci/docker_smoke.sh`'s expectations in the same commit.

### Replay bytes (self-sufficient, strict UTF-8 JSON)

*Deviation from paintbot, deliberate:* paintbot writes the binary `COWLDCTF` format
(`src/ctf/replays.nim:119`, a JSON config followed by recorded inputs). Raid writes **UTF-8 JSON**,
following bullwhip's `bullwhip.replay.v1`, because SPEC §Definition of done check 4 fetches the
replay from S3 and requires valid UTF-8 JSON with a matching `protocol` and a legal `results.reason`,
and the shared `tools/ci/docker_smoke.sh` defaults to `SMOKE_REQUIRE_REPLAY_JSON=1` (line 50, 277).
The bulk payload — the per-tick control bytes — rides as one base64 string, so the file stays small
and the document stays parseable.

```json
{"protocol": "raid.replay.v1",
 "format_version": 1,
 "game_version": "1",
 "seed": 679961,
 "config": { …the fully resolved game config, tokens excluded: num_agents, turnTicks,
             enrageTicks, maxTicks, bossMaxHp, bossMeleeDamage, cleaveDamage,
             pourDamage, crucibleDamage, overloadDamage, overloadHeal, addHp,
             addDamage, roleHp, healAmount, healCost, shieldAbsorb, manaMax,
             manaRegenPerSecond, interruptCooldownTicks, tauntCooldownTicks,
             turnBudgetSeconds, wallClockBudgetSeconds, playerConnectTimeoutSeconds,
             mapPath, roles, players:[{"name":…}] … },
 "map": { …data/foundry.mapspec.json inlined verbatim… },
 "names": {"players": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)", "Baseline (1)"],
           "aliases": ["Alpha", "Bravo", "Charlie", "Delta", "Echo"],
           "roles": ["tank", "dps", "healer", "dps", "dps"],
           "policy_kinds": ["llm", "llm", "scripted", "scripted", "scripted"],
           "colors": {"tank": "#4b7bec", "healer": "#2ecc71",
                      "dps": ["#f2c14e", "#e8743b", "#a55eea"],
                      "boss": "#d63031", "add": "#8d6e63"}},
 "ticks_per_second": 24, "turn_ticks": 120, "tick_count": 4608,
 "phases": [{"phase": 1, "name": "Forge", "from": 0, "to": 1103},
            {"phase": 2, "name": "Slag", "from": 1104, "to": 3011},
            {"phase": 3, "name": "Meltdown", "from": 3012, "to": 4607}],
 "controls_b64": "<base64 of tick_count x 5 x 4 bytes: (move_x i8, move_y i8,
                   aim_turn i8, action u8) per cog per tick>",
 "keyframes": [{"t": 0, "d": 2947483111,
                "cogs": [[617,567,192,300,0,0,0], … 5 … ],
                "boss": [617,329,64,26000,1,0,0],
                "adds": [], "pools": [], "tel": [],
                "mtr": [[0,0,0,0], … 5 … ]}, … every 24 ticks … ],
 "events": [ … the vocabulary below … ],
 "results": { …the results document verbatim… }}
```

Keyframe encodings: a cog is `[x, y, aim, hp, shield, mana, state]` with
`state 0 = alive, 1 = casting, 2 = dead`; the boss is
`[x, y, aim, hp, phase, feed(0|1), spill_stacks]`; an add is `[id, x, y, hp]`; a pool is
`[id, cx, cy, r, age_ticks]`; a live telegraph is `[id, kind(0=cleave,1=pour,2=crucible), cx, cy,
r_or_facing, fuse_left, soak_needed]`; `mtr` is `[damage_to_boss, damage_to_adds, healing_done,
damage_taken]` per seat. `seed` + `map` + `config` + `controls_b64` + the integer sim reproduce the
encounter exactly; `keyframes` carry the per-second state and its digest `d` so the viewer (and the
tests, and a human reading the JSON) can verify the re-derivation and read the fight without running
wasm at all.

Size: 4608 ticks × 20 B → 123 KB of base64; 192 keyframes ≈ 60 KB; events ≈ 120 KB — comfortably
under 400 KB. **Auto-attacks and pool ticks are deliberately not evented** (they would be ~1500
records a minute and would drown the feed); they are carried in the per-second keyframe meters
instead. Every damage instance of **40 or more**, and every death, is evented.

**Everything the viewer needs is in these bytes** (names, colours, config, map geometry, phase table,
per-tick controls, per-second states, events, seed, results). The viewer contacts nothing but the S3
URL it was given.

**Event vocabulary** (every record carries `t` = tick; `turn` and `phase` where meaningful):

| `type` | Fields |
|---|---|
| `encounter_start` | `t`, `seed`, `aliases`, `roles`, `boss_max_hp`, `enrage_s`, `hard_end_s` |
| `phase_start` | `t`, `phase` (1\|2\|3), `name`, `boss_hp`, `boss_hp_pct`, `elapsed_s` |
| `turn_start` | `t`, `turn`, `boss_hp_pct`, `alive`, `enrage_in_s` |
| `order` | `t`, `turn`, `seat`, `alias`, `role`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `intent`, `target`, `station`, `point`, `on_telegraph`, `note`, `say` |
| `fallback` | `t`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `t`, `turn`, `remaining_s` |
| `cast_start` | `t`, `ability` (`overload`), `cast_ticks`, `interruptible` |
| `telegraph` | `t`, `id`, `kind` (`cleave`\|`pour`\|`crucible`), `centre`, `radius` or `facing_brads`+`half_angle_brads`+`reach`, `fuse_ticks`, `soak_needed`, `drawn_on` (alias, for a pour) |
| `telegraph_resolve` | `t`, `id`, `kind`, `hit` (aliases), `damage_each`, `soakers`, `spill_gained`, `pool_id` |
| `interrupt` | `t`, `seat`, `alias`, `ability`, `result` (`success`\|`wasted`\|`late`\|`out_of_range`) |
| `taunt` | `t`, `seat`, `alias`, `result` (`pulled`\|`already_target`\|`out_of_range`) |
| `heal` | `t`, `seat`, `alias`, `target`, `amount`, `overheal`, `mana_left`, `result` (`applied`\|`cancelled`) |
| `shield` | `t`, `seat`, `alias`, `target`, `absorb` |
| `adds_spawn` | `t`, `wave`, `ids`, `positions`, `alive_after` |
| `add_death` | `t`, `id`, `killer` (alias), `alive_after` |
| `feed_buff` | `t`, `active` (bool), `adds_alive` |
| `boss_hit` | `t`, `target` (alias), `ability` (`swing`\|`cleave`\|`pour`\|`crucible`\|`overload`\|`add`\|`pool`), `amount`, `absorbed`, `hp_left` |
| `boss_damaged` | `t`, `seat`, `alias`, `amount`, `boss_hp`, `boss_hp_pct` — emitted only when a hit crosses a 5 % boss-HP boundary, so the feed can pace the burn without one record per shot |
| `pool_spawn` / `pool_expire` | `t`, `id`, `centre`, `radius` |
| `death` | `t`, `alias`, `role`, `killer` (`SMELTER-9`\|`A<n>`\|`pool`), `elapsed_s`, `alive_left` |
| `enrage` | `t`, `elapsed_s`, `boss_hp_pct` |
| `end` | `t`, `reason`, `end_rule`, `boss_hp_removed_frac`, `elapsed_s`, `charged_s`, `score`, `meters` |

`order`, `interrupt`, `taunt`, `telegraph_resolve`, `death` and `fallback` are the records the
phase-60 verifier reads to judge "the champion seats doing the thing the game is about": a champion
seat's `order` events must carry `source: "llm"` with real `intent`/`note` content, not all
fallbacks.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` (forked from
paintbot's verbatim, `chmod +x`, invoked by `coworld build` with the absolute bundle directory,
keeping paintbot's safety checks that the target is absolute, is named `static-replay-viewer`, is not
a symlink and lies inside the repo) builds `Dockerfile.replay-viewer`'s `replay-viewer-builder`
stage — `emscripten/emsdk:4.0.15` + `nimby` pinned by sha256, `nimby use 2.2.4`,
`nimby --global sync nimby.lock` — which compiles **the same Nim sim** as
`nim c -d:emscripten replay-viewer/raid_replay.nim`, then `docker cp`s
`/workspace/raid/replay-viewer/dist/.` into the bundle. The viewer re-derives every frame in the
browser from `seed` + `map` + `config` + `controls_b64`, and validates itself against the keyframe
digests. The game server still serves `/client/replay` for local viewing off the identical `dist`.
Nothing but S3 is contacted at view time.

**Files in the bundle** (each must return 200 with a non-trivial size for phase-60 check 8(b)):
`index.html`, `static_replay.js`, `static_replay_worker.js`, `chrome_common.js`, `wire_constants.js`,
`raid_replay.js`, `raid_replay.wasm`, `raid_replay.data`, `art/floor_foundry.jpg`,
`art/boss_smelter.png`, `art/add_crawler.png`, `art/cog_tank.png`, `art/cog_healer.png`,
`art/cog_dps.png`, `art/pool.png`, `art/telegraph_ring.png`, `art/pillar.png`, `font.ttf`.

**Chrome kept verbatim.** `client/chrome_common.js` is copied unchanged.
`client/replay_broadcast.html` keeps its CSS block and its markup ids exactly, as read from the
starter: `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#chrome`, `#scorebug`,
`#plates-l`, `#plates-r`, `#clock`, `#clock-time`, `#clock-caption`, `#ffwd-mini`, `#viewpanel`,
`#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-slider`, `#zoom-in`, `#zoom-read`,
`#mmwarn`, `#bannerlane`, `#killfeed`, `#transport`, `#btn-restart`, `#btn-back`, `#btn-play`,
`#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`,
`#tick-clock`, `#speedchips`, `#scrub`, `#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`,
`#scrub-head`, `#endcard`, `#ec-headline`, `#ec-wincond`, `#ec-how`, `#ec-teams`, `#ec-replay`,
`#status`, and the `--hudscale` / `--topband` / `--band` / `.tiny` relayout loop
(`client/replay_broadcast.html:4091-4133`) unchanged. The pre-load locker-room curtain
(`#lockerroom`, `#lk-art`, `#lk-bg`, `#lk-sprites`, `#lk-cap`) is kept with raid's own plate.
**Added markup, and nothing else:** `#bossbar` (with `#bossbar-fill`, `#phasetick-70`,
`#phasetick-35`, `#bossbar-label`), `#castbar`, `#enrageclock`, `#nameplates` (five plates),
`#soakpip`, `#buffrow` (Feed / Spill / Enraged chips) and `#meters` (the endcard damage/healing
meter). Removed: the CTF flag icons, the first-person PiP (`#fpv`, `#fpv-canvas`, `#fpv-hud`,
`#fpv-hp`, `#fpv-map`, `#fpv-map-canvas`, `#fpv-name`, `#fpv-cap`, `#fpv-gear`, `#fpv-grip`), and the
kill/lives plumbing that has no counterpart here.

`replay-viewer/static_replay.js` keeps paintbot's OffscreenCanvas-Worker shell verbatim (the
`createCore` / `start` / `stop` / `advance` / `resize` / transform-and-minimap message protocol with
`static_replay_worker.js`, the `data-replay-loaded` and `data-replay-mismatch-tick` attributes and
`showFailure`), with two changes: the loader hands the JSON replay to the wasm module instead of the
binary one, and **bullwhip's `coworld-replay` postMessage bridge is added verbatim** —
`tell("loading")` on script entry, `tell("error", msg)` on failure, and `tell("ready")` inside a
double `requestAnimationFrame` after the first drawn frame
(`cogame-bullwhip/replay-viewer/static_replay.js:20-33`). SPEC check 8(c) greps the served JS for
exactly that bridge. The fetch is bounded by a 20 s `AbortController` (`FETCH_TIMEOUT_MS`) with a
Retry button, also from bullwhip.

**Split of responsibilities.** The wasm canvas draws the world (floor, pit rim, pillars, boss, cogs,
adds, pools, telegraph decals, damage pops); the DOM chrome draws the boss bar, nameplates, cast bar,
enrage clock, event feed, transport, endcard and warnings. DOM text is set with `textContent` only
(names are player-controlled data) and stays crisp at any zoom — which is what makes 360 px
legibility achievable.

**Readouts** (the idea's replay plan, item for item):

1. **Boss health bar with phase ticks.** `#bossbar` spans the top band: SMELTER-9's name, a red fill
   that drains right-to-left, hard tick marks at **70 %** and **35 %** with the phase names *Forge /
   Slag / Meltdown* under them, and the numeric `16,120 / 26,000 (62 %)` — digits, never a glyph.
   The bar flashes white for 6 frames on each phase crossing and turns molten-orange at enrage.
2. **Five role nameplates.** `#nameplates`: one plate per seat, always visible, in slot order, each
   showing the **role icon** (shield / cross / sword), the **alias** (`Alpha`), the **real policy
   name** (`daveey`), an HP bar with the number, the healer's mana bar, an absorb pip when shielded,
   the seat's current intent in plain words (`tanking`, `healing Alpha`, `interrupting`), and a
   greyed plate with a red X and the death time when the cog dies. **Real player names live here,
   in the scorebug and in the endcard, and nowhere else**; the board itself labels cogs
   `Alpha`…`Echo`.
3. **Telegraphed AoE on the floor.** Every live telegraph is drawn as a decal on the arena floor
   under the sprites: a pour is a hot-orange ring with a hatched interior that **fills from the edge
   inward as its fuse burns**, a crucible is the same in white with a `#soakpip` counter reading
   `SOAK ×1` (and `NOBODY IN IT` in red for the last 12 frames if it is empty), and a cleave is a
   90° wedge from the boss with a sweeping fill. On resolution the decal snaps to a 6-frame flash and
   every cog it hit gets a floating damage number (paintbot's `DamageFx` pop, kept).
4. **Enrage timer counting down.** `#enrageclock` next to the boss bar: `ENRAGE 2:35`, mono digits,
   amber under 60 s, red and pulsing at 1 Hz under 30 s, and at zero it becomes a fixed red
   `ENRAGED` chip. `#clock-time` keeps its inherited role showing elapsed `MM:SS` over
   `turn 39/54`.
5. **Cast bar with the interrupt prompt.** `#castbar` appears over the boss while Overload casts: a
   4-second filling bar labelled `OVERLOAD`, with `INTERRUPT!` in white above it; it turns green and
   shatters on a successful interrupt (with the interrupting alias) and flares red on a resolve.
6. **Buff row.** `#buffrow`: a `FEED ×n` chip while ≥ 4 adds are alive, a `SPILL ×n` chip per Spill
   stack, and `ENRAGED` — the three reasons the boss suddenly starts one-shotting people, made
   visible so a spectator can see *why*.
7. **Wipe-or-kill from across the room.** The `#endcard` headline is one of `KILL — 3:12`,
   `WIPE — 71 % at 2:30`, `ENRAGE TIMEOUT — 88 %`, in the largest type on screen, with
   `#ec-wincond` reading `score 1.250 (boss removed 100 % in 192 s of a 240 s timer)` and
   `#ec-how` the one-line story (`killed 8 s after the third crucible; Delta died at 2:41`).
8. **Damage / healing meter endcard.** `#meters`, shown on the endcard and reachable from the
   transport at any time: five horizontal bars sorted descending, each `alias · policy name` with
   damage-to-boss in the role colour, damage-to-adds as a lighter segment, and a parallel green
   healing bar for the healer, with absolute numbers and DPS/HPS. Underneath, a small
   `avoidable hits` column — the raid's execution score in one glance.
9. **Event feed** (`#killfeed`, plain language, last 6): `Alpha taunts — boss turns`,
   `Delta interrupts OVERLOAD`, `Bravo's interrupt is wasted`, `Crucible unsoaked — SMELTER-9 +20 %`,
   `Charlie says "tank heals, dodge pours"`, `Echo dies to a slag pool at 2:41`. Order `note` and
   `say` strings surface here — this is where a spectator sees the LLM playing.
10. **Transport** (verbatim): play/pause, back one tick, +5 s, jump to end, loop, lull-skip,
    spoilers, the speed chips over `PlaybackSpeeds = [1,2,3,4,8,16]`, the scrubber with the
    `#momentum` graph re-purposed to plot **boss HP %** across the encounter, phase crossings and
    deaths marked on the scrub bar, the `#tick-clock` readout, and the `#mmwarn` digest-mismatch
    line. Every `telegraph_resolve` that killed a cog and every phase crossing is registered as a
    highlight so `#btn-skip` fast-forwards the quiet burn between mechanics at 4× with
    `#clock-caption` reading `BURN — 4×`.

**Art is real, not placeholder.** The floor is paintbot's painted arena floor retinted to scorched
foundry stone with a cast-iron rim; pillars use `client/art/walls/wall_v.jpg` verbatim as their
side texture; cogs are paintbot's `data/rig_real/` rig recoloured per role — tank steel-blue
`#4b7bec` with a riveted pauldron overlay, healer green `#2ecc71` with a canister, the three DPS
amber `#f2c14e`, ember `#e8743b` and violet `#a55eea`; SMELTER-9 is an authored 128 × 128 painted
smelter-golem rig with a glowing crucible chest that brightens per phase; the Slag Crawler is an
authored 32 × 32 sprite; pools and telegraph rings are authored decals. All generated by committed
scripts under `scripts/art/`, the way paintbot generates its props (`scripts/art/build_cvc_rig.py`,
`scripts/art/gen_crew.py`). The locker-room curtain plate is raid's own. No solid-colour rectangles
standing in for anything, no TODO assets.

**Legible at 360 px** — the embedded featured-match iframe is ~360 px wide, so the composition is
checked at **360 px**, not at desktop width. Paintbot's `--hudscale`
(`clamp(0.5, boardW/760, 1.6)`) and its `.tiny` class at `boardW <= 620`
(`client/replay_broadcast.html:1424-1428`) are inherited and do the heavy lifting. On top of that:
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }` so
policy names never collapse to "…" (playbook gotcha); a `@media (max-width: 640px)` rule stacks the
five nameplates into two rows of compact 8 px HP pips, hides `#viewpanel` (minimap + zoom bar) and
the speed-chip labels, drops the feed to two lines under the board, and keeps `#bossbar`,
`#enrageclock` and `#castbar` full width and unwrapped; the endcard headline is
`font-size: clamp(13px, 4.2vw, 26px)`. The boss bar, the five HP bars and the enrage clock are the
three things that must read at 360 px, and they are the three the media query protects. A static test
asserts the `.plate-name` rule and the `640px` media block are present (§Tests).

---

## Packaging

- **Repo:** `Metta-AI/cogame-raid`, **public at creation** (public is a certification prerequisite —
  `source-resolves` 404s on private). Slug `raid`.
- **`compose.yaml`** — bullwhip's single-service shape (paintbot's two-image split does not survive
  the fork: the shared `tools/ci/docker_smoke.sh` runs the game and every player container from one
  image):

  ```yaml
  services:
    raid:
      image: coworld-raid:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — paintbot's/bullwhip's two-stage Nim build: `debian:bookworm-slim` + `nimby`
  0.1.26 pinned, `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the
  container's synced package tree, then two binaries —
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:raid src/raid.nim` and the same
  for `src/raid_player.nim`. Run stage `debian:bookworm-slim` with `ca-certificates` and `libcurl4`,
  copying `/bin/raid`, `/bin/raid-player`, `./data`, `./client`. `CMD ["/bin/raid"]`.
- **`Dockerfile.replay-viewer`** — paintbot's, with the CTF asset copies replaced by raid's:
  `emscripten/emsdk:4.0.15`, nimby pinned by sha256, `nim c -d:emscripten
  replay-viewer/raid_replay.nim`, `tools/gen_wire_constants.nim > replay-viewer/dist/wire_constants.js`,
  the `chrome_common.js` / `static_replay.js` / `static_replay_worker.js` copies, the marker `sed`
  that splices `<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->` and `<!-- BROADCAST_CORE -->` into
  `index.html`, the art copies, and the same `test -f` / `grep -q` assertion tail (adjusted to raid's
  file names, and extended with
  `grep -q 'coworld-replay' replay-viewer/dist/static_replay.js`).
- **`coworld_manifest_template.json`:**
  - `game.name` `raid`; `episode_timeout_minutes` **20**; `game.runnable.image` `{{GAME_IMAGE}}`,
    `run` `["/bin/raid"]`, `source_url` `https://github.com/Metta-AI/cogame-raid/tree/main`;
    `game.runnable.env.ANTHROPIC_API_KEY_URI` `secret://coworld/raid/anthropic_api_key`;
    `game.owner` `daveey@softmax.com`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.config_schema`: `tokens` (5), `players` (5), `seed`, **`num_agents`** (integer,
    min 5, max 5, default **5**), `roles` (optional array of 5 role strings; omit to deal from the
    seed), `turnTicks` (120), `enrageTicks` (5760), `maxTicks` (6480), `bossMaxHp` (26000),
    `turnBudgetSeconds` (10), `wallClockBudgetSeconds` (660), `episodeTimeoutSeconds` (1200),
    `playerConnectTimeoutSeconds` (90), `mapPath` (`"foundry"`), `model`, `maxOutputTokens` (900),
    `llmAttemptSeconds` (6.5 — the first-attempt per-seat deadline), `llmRetrySeconds` (3.0 — the
    retry deadline; `llmAttemptSeconds + llmRetrySeconds` must be ≤ `turnBudgetSeconds`, asserted at
    config load), `showPlayerLabels` (true), `gameOverTicks` (96).
  - `game.results_schema`: exactly the closed key set in §Server, with `reason` enum
    `["complete","deadline","fault"]` and `end_rule` enum
    `["kill","wipe","enrage_timeout","wall_clock","sim_fault","host_error"]`; `scores` is
    `minItems 5, maxItems 5`, items `number, minimum 0`.
  - `game.protocols`: **both `player` and `global`**, each `{"type": "text", "value": "…"}` —
    `player` describing the `register` frame, the `turn` frames and the `done` frame; `global`
    describing the `/global` spectator snapshot and the static replay bundle. Text form, not URIs
    (paintbot uses URIs; the playbook gotcha row requires text).
  - `game.docs`: `readme` = `{"type": "text", "value": "<the README body, inlined>"}` and `pages` =
    two entries — `{"id": "rules.md", "title": "Rules", "content": {"type": "text", "value":
    "<docs/RULES.md inlined: the full boss script, every number in §The game>"}}` and
    `{"id": "protocol.md", "title": "Wire protocol", "content": {"type": "text", "value":
    "<docs/PROTOCOL.md inlined>"}}`. A manifest test asserts all three values are non-empty text.
  - `game.player[0]` = `{"id": "baseline", "name": "stalwart", "type": "player", "image":
    "{{PLAYER_IMAGE}}", "run": ["/bin/raid-player"], "env": {"PLAYER_SCRIPTED": "stalwart"},
    "source_url": "https://github.com/Metta-AI/cogame-raid/tree/main"}` — the bundled certification
    player, no LLM. `game.player[1]` is the same with `greenhorn`. `{{GAME_IMAGE}}` and
    `{{PLAYER_IMAGE}}` both resolve to `coworld-raid`.
  - **Variants — `num_agents` is 5 in every one:**

    | id | name | `num_agents` | `bossMaxHp` | `enrageTicks` | `maxTicks` | turns | `turnBudgetSeconds` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|
    | `default` | SMELTER-9 (5 cogs, 240 s enrage) | **5** | 26000 | 5760 | 6480 | 54 | 10 | 660 |
    | `sprint` | SMELTER-9 Sprint (5 cogs, 120 s enrage) | **5** | 13000 | 2880 | 3600 | 30 | 10 | 400 |

    `sprint` exists for cheap ladder rounds: it halves the boss's health pool and the enrage timer
    together, so the score scale is unchanged (a kill on the timer is still 1.0), and it **never**
    changes the seat count. Neither variant pins `roles` — both deal from the seed.
  - **Certification fixture** (`certification`): `players` = `[{"player_id": "baseline"} × 5]`;
    `game_config` =
    `{"players": [{"name":"P1"},{"name":"P2"},{"name":"P3"},{"name":"P4"},{"name":"P5"}],
    "num_agents": 5, "seed": 42, "roles": ["tank","healer","dps","dps","dps"],
    "bossMaxHp": 3000, "turnTicks": 120, "enrageTicks": 960, "maxTicks": 1200,
    "turnBudgetSeconds": 10, "wallClockBudgetSeconds": 180,
    "playerConnectTimeoutSeconds": 60, "mapPath": "foundry"}` — a 3000-HP boss killed by five
    scripted seats in ≈ 18 s of sim time, 10 turns, no LLM, wall clock ≈ 5 s, ending
    `complete`/`kill` so the happy path is what certification exercises.
- **Scaffold from `coworld-builder/templates/`** with `<slug>` = `raid`, `<IMAGE>` = `coworld-raid`,
  `<SEATS>` = **5**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/build_replay_viewer.sh` (**`chmod +x`** —
  `coworld build` hard-requires `os.X_OK`), `tools/ci/policies.json`. `SMOKE_REQUIRE_REPLAY_JSON`
  stays at its default `1`; `SMOKE_SEATS` is **5** and is an independent cross-check against
  `certification.game_config.num_agents` (`templates/tools/ci/docker_smoke.sh:133-143`).
- **`tools/ci/policies.json`** (all four `"run": "/bin/raid-player"`, one image, env-switched):

  | name | env | role |
  |---|---|---|
  | `raid-anvil` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `raid-triage` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `raid-stalwart` | `PLAYER_SCRIPTED` = `stalwart` | filler |
  | `raid-greenhorn` | `PLAYER_SCRIPTED` = `greenhorn` | filler |

- **Repo layout:** `src/raid.nim`, `src/raid_player.nim`, `src/raid/` (`types.nim`, `arena.nim`,
  `sim.nim`, `combat.nim`, `abilities.nim`, `boss.nim`, `telegraphs.nim`, `pools.nim`,
  `control.nim`, `orders.nim`, `baselines.nim`, `llm.nim`, `scoring.nim`, `state.nim`, `config.nim`,
  `roster.nim`, `events.nim`, `labels.nim`, `broadcast.nim`, `render.nim`, `replay.nim`,
  `server.nim`), `replay-viewer/` (`raid_replay.nim`, `config.nims`, `static_replay.js`,
  `static_replay_worker.js`), `client/` (`replay_broadcast.html`, `chrome_common.js`,
  `broadcast_core.js`, `art/`), `data/` (`foundry.mapspec.json`, art, `font.ttf`), `tests/`
  (+ `tests/support/`), `tools/`, `scripts/art/`, `docs/` (`RULES.md`, `PROTOCOL.md`, `plans/`),
  `AGENTS.md`, `README.md`, `nimby.lock`, `raid.nimble`, `config.json`. `players/` is **not** used
  (the player is `src/raid_player.nim`).

---

## Tests

CI is the only harness — the sandbox has no Docker, no Nim, no emsdk. The template `ci.yml` runs
**every `tests/*.nim` file individually, twice (debug and `-d:release`)**, so each test file is a
standalone program and shared helpers live in **`tests/support/helpers.nim`** (a subdirectory, so the
`tests/*.nim` glob never executes a helper module). No aggregator file.

1. **`tests/test_motion.nim`** — **sim unit tests** on movement: a cog accelerates to exactly
   `MaxSpeed = 832` on a cardinal and no further; a full-diagonal order is not faster than a cardinal
   on either axis; friction brings an uncommanded axis to rest below `StopThreshold`; the wall slide
   keeps a cog inside the pit for 3000 ticks of input hammering the rim and the pillars; cog–cog
   overlap resolves symmetrically (swapping slot indices mirrors the outcome); a cog can cross
   116 px from a standing start inside 60 ticks (the dodge-budget arithmetic in §The game, asserted).
2. **`tests/test_combat.nim`** — **sim unit tests** on damage: `absorbDamage` spends shield before
   HP and drops the shield exactly at 0; a tank auto-attack lands every 12 ticks for 12 and gives 36
   threat; a DPS attack out of range or through a pillar does not land; a heal cast completes at
   exactly 24 ticks, heals 90, costs 60, and is cancelled with a refund if the healer moves 9 px or
   the target dies; mana regenerates 30 per 24 ticks and caps at 1200; a shield expires unspent after
   480 ticks; the damage multiplier order `base × feed × spill × enrage` produces the documented
   integers at every combination.
3. **`tests/test_boss.nim`** — the boss script, number for number: the phase table crosses at exactly
   70 % and 35 % and never re-enters; cleave cadence is 192/168/144 by phase and its cone is exactly
   ±32 brads and 180 px (a cog at 181 px or at 33 brads is not hit, at 179/31 is); the boss's facing
   is frozen for the whole 48-tick cleave telegraph; a pour draws only non-tank living cogs; a pool
   bites every 24 ticks and expires at 240; the pool cap of 6 expires the oldest; Overload heals 400
   and hits all five for 70 when it resolves and does neither when interrupted; two interrupts in one
   tick give the lower slot `success` and the other `wasted`; taunt locks the target for exactly 72
   ticks and the 10 % stickiness margin behaves at 1.09× and 1.11×; add waves spawn 2 at 360-tick
   intervals in phase 2 only, cap at 8, and Feed toggles at exactly 4 alive; enrage fires at tick
   5760 and triples damage.
4. **`tests/test_telegraphs.nim`** — the crucible in particular: `k == 0` grants exactly one Spill
   stack (capped at 5) and leaves no pool; `k == 1` deals 240, `k == 2` deals 120 each, `k == 3`
   deals 80 each; membership is by body centre and is decided at the resolution tick, not at cast
   start; a cog that dies mid-fuse is not counted; the `dodge` reaction leaves the shape with ≥ 20 px
   of margin within the fuse from any starting point inside it.
5. **`tests/test_scoring.nim`** — the formula and its sign: every row of the worked-example table in
   §The game reproduces to 3 decimals; all five entries of `results.scores` are identical for 200
   randomised endings; a kill is the only ending charged `elapsed`; `deadline`, `wipe`,
   `enrage_timeout` and both faults are charged `T`; score is monotone increasing in `removed` and
   (for kills) decreasing in `elapsed`; score is never negative and is clamped at 3.0; a zero-damage
   wipe scores exactly 0.0.
6. **`tests/test_determinism.nim`** (**the gate**) — same seed + same control bytes ⇒ identical
   digest at every keyframe over a full 6480-tick encounter, run twice in one process and once in a
   fresh instance; a one-bit change in any control byte changes the final digest; a committed golden
   fixture `tests/fixtures/golden_digests.json` pins the digests for seed 42 over 1200 ticks, so any
   rule change shows up in the diff. Plus the **no-floating-point source guard**: grep
   `src/raid/*.nim` for `sin|cos|tan|atan|arctan|exp|ln(|pow|fmod|hypot|sqrt` and for
   `float`/`float64` inside the step path, and the build scripts for `-ffast-math`; any hit fails.
7. **`tests/test_baselines.nim`** — **the bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random world states × both baselines × all three roles, the emitted
   order validates against the schema — `intent` legal for that role, `target` a live entity legal
   for that intent or null, `station` and `on_telegraph` legal, `point` inside the pit, `note` ≤ 160
   runes, `say` ≤ 32 runes — **and** the compiled control bytes are in range (`move` −100…100,
   `aim_turn` ±8, action bits ≤ 0b11111, and no role ever sets a bit it does not own: no taunt from a
   non-tank, no heal/shield from a non-healer, no interrupt from a non-DPS) for every cog on every
   tick of the turn. Plus: five `stalwart` seats kill the boss at seed 42 in the default variant and
   five `greenhorn` seats do not (the baselines are ordered, so the ladder has a spread), and no
   baseline ever fires an ability on cooldown.
8. **`tests/test_orders.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   unknown enums, a healer sending a DPS intent, `point` as numeric strings, `point` outside the pit,
   `target` as `3` and as `"a3"` and as `"A99"` and as a dead cog, missing fields, a 400-character
   `note`, and a `say` whose 32nd and 33rd runes are a 4-byte emoji — the truncation must land on the
   **rune** boundary, the result must still round-trip `%*`/`$`/`parseJson`, encode as valid UTF-8,
   and survive being copied into another seat's `callouts`. Two consecutive failures ⇒ the `stalwart`
   order plus a `fallback` event; a timeout on attempt 1 ⇒ exactly one retry.
9. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: all living seats' calls go
   out in **one parallel batch** (the fake records in-flight windows and the test asserts they
   intersect); a turn with two dead cogs batches exactly 3 requests; the per-turn budget is enforced
   with a hung client; the budget guard switches to scripted and the episode still ends `complete`;
   the 660 s stop yields `deadline/wall_clock`; a raised sim fault yields `fault/sim_fault` with a
   partial replay and the damage-only score; a seat that never registers plays `stalwart` and is
   reported to `COGAME_PLAYER_FAILURE_URI`; a mid-encounter disconnect degrades to `stalwart` and
   revives on reconnect; a dead seat is never queried.
10. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay** plus the **strict-UTF-8
    parse**: a full scripted-vs-boss episode (cert-fixture length) runs over the real sim, writes
    `results.json` and the replay; the replay bytes are asserted **valid UTF-8 first**
    (`validateUtf8(readFile(path)) == -1`) and only then `parseJson`ed, with the fixture forcing a
    non-ASCII `say` into the event stream so the UTF-8 path is real; `protocol == "raid.replay.v1"`;
    `controls_b64` decodes to exactly `tick_count × 20` bytes; every documented top-level key is
    present and `map`, `names`, `config`, `phases`, `keyframes`, `events`, `results` are non-empty;
    `results.reason` is in the legal enum and `results.end_rule` in its own; the event stream contains
    at least one `order` per living seat per turn, one `telegraph`, one `telegraph_resolve`, one
    `phase_start` and one `end`; and re-deriving from `seed` + `map` + `config` + `controls_b64`
    reproduces **every keyframe digest**.
11. **`tests/test_server.nim`** — the websocket contract: the `register` frame is accepted, a bad
    token 403s, a duplicate connection 409s, `/healthz` answers, `/global` streams a snapshot,
    artifact writes land on `file://` URIs, `COGAME_EVENTS_URI`/`COGAME_METRICS_URI` reject non-file
    schemes loudly, replay mode serves `/replay-data` and `/client/replay`, and the `done` broadcast
    is bounded at 3.0 s per seat.
12. **`tests/test_view.nim`** — the observation contract: the view contains every field listed in
    §Server and **none** of the hidden ones (a grep of the serialised view for the seed, for any
    other seat's `note`, for any `PLAYER_PROMPT` text and for any real player name must find
    nothing); `callouts` carry exactly the previous turn's `say` strings; a dead seat's view has
    `you.alive == false`; role-specific blocks appear only for the role that owns them.
13. **`tests/test_manifest.nim`** — `num_agents == 5` in **every** variant *and* in
    `certification.game_config`; `len(certification.players) == 5` and
    `len(certification.game_config.players) == 5`; `results_schema` keys equal the keys
    `src/raid/server.nim`'s results builder emits; `game.protocols` carries **both** `player` and
    `global`; `game.docs.readme` and both pages are non-empty **text**;
    `replay_viewer.bundle == "static-replay-viewer"`; `episode_timeout_minutes == 20`; every
    variant's `wallClockBudgetSeconds ≤ 0.6 × 1200`; the compose image name matches the `<IMAGE>`
    used in the scaffold.
14. **`tests/test_map.nim`** — `data/foundry.mapspec.json` loads; the pit is four-fold symmetric
    about (617, 329); every cog spawn, add alcove, boss stand and ring point is on free floor inside
    the pit and non-overlapping; every cog spawn has line of sight to the boss stand; the four
    pillars are the only interior obstacles and each blocks LOS across its own footprint.
15. **`tests/test_viewer.nim`** — **the viewer smoke** (no browser): the node harness forked from
    paintbot's `tools/wasm_replay_smoke.cjs` loads `replay-viewer/dist/raid_replay.js` with a
    recorded replay, advances to the end, and asserts the tick total, the final digest and that
    seek-to-mid / seek-to-end land exactly; malformed inputs (bad `protocol`, bad base64 length,
    truncated JSON, `tick_count`/payload mismatch) are all rejected with a message rather than a
    crash. Plus static assertions over `client/replay_broadcast.html` and
    `replay-viewer/static_replay.js`: the `coworld-replay` bridge **including `tell("ready")`** is
    present; the inherited chrome ids listed in §Viewer are all still there; `#bossbar`,
    `#bossbar-fill`, `#phasetick-70`, `#phasetick-35`, `#castbar`, `#enrageclock`, `#nameplates`,
    `#soakpip`, `#buffrow` and `#meters` exist; `.plate-name { flex: 1 1 auto; min-width: 3.2em` and
    a `@media (max-width: 640px)` block are present. (Marked `NIM_TESTS_RELEASE_ONLY` if the debug
    wasm harness proves slow.)
16. **`tests/test_startup.nim`** — `/bin/raid` exits 2 with a clean one-line message and no traceback
    when `COGAME_CONFIG_URI` is missing or invalid; `--help` works; the player binary exits 0 on an
    unreachable `COWORLD_PLAYER_WS_URL` after its bounded connect retry.
17. **`tests/test_perf.nim`** — 6480 ticks with 5 cogs, the boss and 8 adds complete in under 30 s in
    a release build.

CI additionally runs `tools/ci/docker_smoke.sh` (a raw-Docker episode from the certification fixture,
`SMOKE_SEATS=5` cross-checked against the manifest, replay required to parse as JSON) with
`docker-smoke` depending on the image build in the same run so a stale binary can never be smoked,
and `tools/build_replay_viewer.sh` (the bundle builds, contains `index.html` and a non-empty `.wasm`,
and is uploaded as the `static-replay-viewer` artifact).

---

## Out of scope (v1)

- **A second boss, trash packs, or any encounter other than SMELTER-9.** One authored encounter on
  one authored floor. A boss roster is the first v0.2 feature once the ladder is healthy, and it must
  keep the "the opponent never varies within a variant" property or the score stops comparing.
- **Procedural arenas.** One authored map, `foundry`. Paintbot's generator, validators, curated pool,
  size/symmetry/endzone knobs and map editor are all dropped.
- **Resurrection, combat res, wipe-and-retry, or multiple pulls per episode.** One pull, dead is
  dead. Anything else changes what "wipe time" means and therefore the score.
- **An RL continuous-vector policy interface.** The idea's stated interface is reinterpreted as the
  LLM-order + deterministic-control-layer stack (an inherited pin: both champions must be
  `PLAYER_PROMPT`). Exposing the per-tick `(move_x, move_y, aim_turn, action)` vector to external
  policies over the websocket is a v0.2 protocol addition; the control layer and the quantised action
  log are already shaped for it.
- **Account-aware sim logic.** The five-different-accounts rule and the cross-play-mean ranking are
  recorded in §The game as league operations and are enforced by phases 50/60. The game container has
  no notion of accounts in v1 and no rule depends on one.
- **Gear, talents, cooldowns chosen before the pull, or any pre-episode loadout.** Every seat gets
  the same kit for its dealt role, every episode.
- **Free-form chat between seats.** The only channel is `say`, 32 runes, one turn stale, public to
  all four team-mates and to the spectator feed. No private messages, no multi-turn negotiation, no
  pre-pull planning phase.
- **Aggro-table exposure beyond the numbers already in the view**, threat meters as a first-class UI,
  or a combat log the policies can query. Everything a seat knows is in the per-turn view.
- **Everything CTF that is not this raid:** guns and hitscan, aim jitter, grenades, the barrage, med
  kits, the plasma arc, paint puddles and stains, spray cans, flags, teams, lives and respawn, perks,
  handicaps, achievements, shouts, the four-team mode, and the shadowcast fog of war. None of them
  survive the fork.
- **Audio, 3-D, camera cuts other than the endcard hold, and any downloaded art asset** (the bundle
  stays hermetic).
- **A 4-seat, 6-seat or 10-seat variant, or a variant that changes the role mix.** Any of those
  changes `num_agents` or what a prompt must cover, which the seat-count pin forbids in v1.
