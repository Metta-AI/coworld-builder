# lantern — design note (2026-08-22)

`Metta-AI/cogame-lantern`, a 3v3 hide-and-seek Coworld played in the dark on a top-down warehouse
floor: three cogs push and lock crates into a fort while three cogs hunt them with flashlights,
then the sides swap and the halves are compared. It is forked from **`Metta-AI/coworld-ctf`
(paintbot)**, read at its read-only mount `/workspace/starters/coworld-ctf`. **Every convention
there holds here unless this note says otherwise.** The starter is pinned by the operator ruling of
2026-08-22 recorded in `playbooks/make-coworld.md` §Phase 0 — "New physics games (Cogball, Lantern,
Tandem) take paintbot" — and it is the right pin by game shape: Lantern is a real-time tick loop
with rules written fresh for this coworld, nothing pre-exists to port, and paintbot already ships
every piece the hunt needs — a 24 Hz integer-physics cog sim (`src/ctf/sim.nim`), **shadowcast
fog-of-war with an aim-locked vision cone** (`src/ctf/sim.nim:2257-2475`, `applyFovCone`,
`sim.fovCaches`), pushable/destructible props (`PlacedBarrier`, `src/ctf/sim.nim:1550-1975`), a
per-tick recorded-input replay, a static wasm replay viewer, and a broadcast chrome
(`client/replay_broadcast.html` + `client/chrome_common.js`) that is already built for a 360 px
embed. The flashlight *is* paintbot's vision cone; the fort *is* paintbot's barrier prop with a
lock; the arena rules are what get replaced.

Two pieces come from paintbot's sibling in the builder's starter set, `Metta-AI/cogame-bullwhip`
(read at `/workspace/starters/cogame-bullwhip`), because paintbot predates both and the pins
require them: the **server-side LLM client with a one-parallel-batch-per-turn decision loop**
(`src/bullwhip/llm.nim:419-472`, `decideAll` over `curly.makeRequests`) and the **`coworld-replay`
postMessage bridge** in `replay-viewer/static_replay.js:20-33,120-124` (`tell("loading")` /
`tell("ready")` / `tell("error")`), which SPEC §Definition of done check 8(c) greps for and which
paintbot's `replay-viewer/static_replay.js` does not have. Bullwhip also supplies the packaging
shape the builder scaffold expects — one image, two entrypoints, single-service `compose.yaml`.

Three deliberate deviations from paintbot are listed and justified where they occur: a **UTF-8 JSON
replay** instead of the binary `COWLDCTF` format (§Server — SPEC check 4 and
`tools/ci/docker_smoke.sh`'s `SMOKE_REQUIRE_REPLAY_JSON=1` both require JSON); **decisions made in
the game server** instead of in the player container (§Decisions); and **one authored map instead
of the procedural generator** (§Sim module).

There is **no `OPEN` section.** Every rule the idea leaves loose is one the rails say the designer
settles (seat count, scoring when the idea pins one, parameter values, viewer composition, policy
prompts), and each is decided below with its reason.

**Source idea, verbatim** (Asana idea task 1217704658739440, "04 Lantern (hide-and-seek) — hiders
get 60 ticks and movable crates; seekers get flashlights"):

> Asymmetric teams in the Cogball physics world: hiders push and lock blocks into forts, seekers
> ramp and climb. Scored by seconds-hidden; teams swap sides each half. The 'tool use from scratch'
> game.
>
> Seats: 2 teams x 3
> Motive: asymmetric team zero-sum
> Policy interface: RL continuous vector
> Fills gap: asymmetric teams / construction / emergent tool use
> Integrity (anti-collusion): Zero-sum between sides, so collusion only pays as cross-episode
> win-trading — blocked by anonymous seat aliases (already site practice in Focus/Cosino).
>
> Replay plan (watchability): Two acts on a phase clock: fort-building in timelapse, then the hunt —
> flashlight cones sweeping darkness, a proximity heartbeat bar, spotlight burst on a find.
> Side-swap intermission card keeps the score honest.

**Three re-readings of the idea, decided here and never revisited:**

1. **"in the Cogball physics world"** → Lantern runs on **paintbot's own integer 2D physics**, not
   on cogball's engine. Cogball is a separate coworld being built in parallel; it is not a library
   this repo can import, and the starter pin is paintbot. The phrase is read as "a physical,
   continuous-motion world rather than a grid", which paintbot's sub-pixel integer motion
   (`MotionScale = 256`, `Accel = 76`, `MaxSpeed = 704`, `src/ctf/sim_types.nim:340-352`) already is.
2. **"seekers ramp and climb"** is a 3-D affordance (the OpenAI hide-and-seek lineage). In a
   top-down 2-D warehouse there is no verticality, so the seekers' counter-tool is **prying**: a
   seeker can breach a locked crate in 3 seconds, loudly. Same role in the design — the hiders'
   construction is defeasible by a slow, noisy seeker tool — with no z-axis.
3. **"Policy interface: RL continuous vector"** → every seat is an **LLM prompt policy with a
   scripted fallback** (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=<name>`), issuing one *order* per
   decision turn that a deterministic control layer executes at 24 Hz. This is an inherited pin
   (SPEC §Design pins: both champions must be `PLAYER_PROMPT` policies), and the recorded action
   log is already the quantised per-tick control vector, so an RL transport is a v0.2 protocol
   addition, not a v1 redesign. It is listed in §Out of scope (v1).

**"hiders get 60 ticks" (from the idea's Asana title).** Read literally at paintbot's 24 Hz that is
2.5 seconds, which builds nothing. It is honoured as **60 seconds of hider head start per episode**
— a 30-second fort-building act at the top of each of the two halves (720 ticks × 2). The number
survives; the unit is the one that makes the game.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")
and where each is satisfied:**

| Pin | How lantern satisfies it |
|---|---|
| Starter by game shape | `coworld-ctf` (paintbot) — real-time tick loop, new rules, per-tick replay, static wasm viewer; operator ruling 2026-08-22 (title paragraph above). |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-lantern`, **public at creation** — public is a certification prerequisite (`source-resolves` 404s on private). §Packaging. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (two champion prompts) vs `PLAYER_SCRIPTED=warden` / `PLAYER_SCRIPTED=moth`; one image `coworld-lantern:latest`, `run: /bin/lantern-player`. §Decisions, §Packaging. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`, built by `tools/build_replay_viewer.sh` (forked from paintbot's). §Viewer, §Packaging. |
| Real art, starter chrome verbatim | Paintbot's `client/replay_broadcast.html` chrome block and `client/chrome_common.js` kept verbatim (id-for-id list in §Viewer); cog art from `data/rig_real/` recoloured, an authored painted crate sprite, no placeholders. §Viewer. |
| Two name spaces | Prompts and observations see only `Moth-1..3` / `Owl-1..3`; real policy names appear only in `replay.names.players`, `results.names` and the viewer scorebug plates. §Server, §Viewer. |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | 602 s expected worst case / 660 s hard stop against a 720 s budget, arithmetic spelled out in §Decisions; every wait bounded; LLM failure → one retry → scripted order. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 6** in variant `default`, variant `sprint`, and `certification.game_config`; `SMOKE_SEATS=6`. §Packaging. |

---

## The game

**Lantern is 3v3 hide-and-seek in the dark, played twice with the sides swapped.** Six cogs share a
walled 1235 × 659 px warehouse floor lit only by the seekers' flashlights. In each half, one trio
(the **hiders**) gets a 30-second lights-on build act to shove and bolt down wooden crates into a
fort, then the lights go out, the seekers' pen door opens, and the seekers get 75 seconds to sweep
the dark and find all three. A hider's score is the time it survives unfound. Then the sides swap,
the map resets to its exact starting layout, and the second half is played under identical
conditions. The team that hid longer wins.

**Seats: `num_agents` = 6.** Two teams of three; **one seat = one cog**. The idea pins 2 × 3 and
there is no stronger reason to move: three hiders is the smallest number that makes a fort a
division of labour (one pusher, one locker, one lookout), three seekers is the smallest number that
makes lane assignment a decision, and six single-cog seats let the ladder seat six distinct
policies with no teammate-attribution problem inside a trio. Seat → team is fixed:
**even slots (0, 2, 4) are team `Moth`; odd slots (1, 3, 5) are team `Owl`.** With the platform
seating champion #1 at the lowest slot and champion #2 next, the two champions land on opposite
sides in every episode.

**Aliases (the in-game name space).** Team Moth's cogs are `Moth-1`, `Moth-2`, `Moth-3` (slots 0, 2,
4); team Owl's are `Owl-1`, `Owl-2`, `Owl-3` (slots 1, 3, 5). The aliases are **side-neutral on
purpose** — a cog is not "a hider", it *is hiding this half* — and they are the only names any
prompt or observation ever contains.

**Sides.** In **half 1** Moth hides and Owl seeks. In **half 2** Owl hides and Moth seeks. The map,
crate layout, spawns and seed are identical in both halves (§"Half reset"), so the two hide
fractions are directly comparable.

### The world

- **Floor.** 1235 × 659 px (paintbot's `MapWidth`/`MapHeight`, `src/ctf/sim_types.nim:787-788`),
  origin top-left, +x right, +y down. Solid outer wall. The interior is one authored map, `vault`
  (§Sim module): six square pillars, four three-sided alcoves, two long racks, and the **seeker
  pen** — a 120 × 110 px room at the bottom-centre edge, `x ∈ [558, 678]`, `y ∈ [545, 655]`, whose
  north door is a wall segment that is solid during the build act and open during the hunt.
- **Cogs.** Paintbot's body: `PlayerHalf = 6` px half-extent (a 12 × 12 footprint),
  `MotionScale = 256` sub-pixel motion, `Accel = 76`, friction `144/256`, `MaxSpeed = 704`
  (2.75 px/tick ≈ 66 px/s), `StopThreshold = 8`, wall sliding via `MovementSlideMaxScan = 3`,
  cog–cog restitution `PlayerBouncePct = 40`. Seekers get `MaxSpeed = 768` (+9 %, 72 px/s) because
  they must cover ground; hiders keep 704. A **crawling** cog (an order flag) is capped at 40 % of
  its max speed and makes no footstep sound.
- **Aim / lantern heading.** Every cog carries an aim angle in **brads** (256 per turn, 0 = east,
  counter-clockwise — paintbot's convention), turned at most `aimTurnRate = 5` brads/tick. A
  seeker's flashlight points along its aim.
- **Crates.** Ten crates `C0`…`C9`, each a 48 × 48 px axis-aligned square. A crate is **solid**
  (blocks movement) and **opaque** (blocks light and line of sight). States: `loose` (pushable),
  `locked` (immovable, bolted), `broken` (removed from the world). Starting positions are authored
  and exactly 180°-rotationally symmetric about (617, 329):
  `C0 (300,180) C1 (935,479) C2 (500,120) C3 (735,539) C4 (300,470) C5 (935,189) C6 (500,540)
  C7 (735,119) C8 (617,240) C9 (618,419)`.
- **Darkness.** Outside the lit sets defined below, the world is unobserved by seekers. Static wall
  geometry is **not** secret — the warehouse blueprint is in every seat's observation, both roles,
  always. What darkness hides is *where the crates ended up and where the bodies are*.
- **Lantern.** A seeker's lit set is: every map cell within `lanternRangePx = 420` of its body whose
  bearing from the body is within `lanternConeBrads = 18` (±25.3°, a 50.6° beam) of its aim **and**
  has line of sight through walls and non-broken crates; **plus** an omni bubble of
  `visionBubblePx = 60` with line of sight. Lanterns are **off** during the build act and **on** for
  every hunt tick. The three seekers **share** their lit sets (one team radio): anything one seeker
  lights is in all three seekers' observations that turn.
- **Sound.** Three ring kinds, each recorded with a deterministic jitter so a listener gets a place,
  not a point: footsteps (any non-crawling cog moving faster than 50 % of its max speed) emit a
  260 px ring at most once per 24 ticks, jittered ±40 px; a crate push emits a 420 px ring at most
  once per crate per 12 ticks, jittered ±60 px; a crate break emits a 900 px ring, jittered ±30 px.
  Rings live 24 ticks. Seekers hear rings whose radius covers them; hiders hear only break rings.
- **Heartbeat.** Every hunt tick each seeker is told a five-band proximity reading derived from the
  straight-line distance `d` to the nearest **unfound** hider, with no direction:
  `burning` (d ≤ 120), `hot` (≤ 260), `warm` (≤ 450), `cool` (≤ 750), `cold` (> 750). It is the
  idea's heartbeat bar, and it is real information, not decoration.

### Time, acts, halves, turns

`dt = 1/24 s` (paintbot's `TargetFps`/`ReplayFps` = 24, `src/ctf/sim_types.nim:294,353`). The
episode is a fixed 5040 ticks = 210 s of sim time:

| Segment | Ticks | Sim time | Decision turns |
|---|---|---|---|
| Half 1 — **build** act (Moth hides) | 0 – 719 | 30 s | 6 |
| Half 1 — **hunt** act | 720 – 2519 | 75 s | 15 |
| Intermission / half reset | at tick 2520 (instant) | — | — |
| Half 2 — **build** act (Owl hides) | 2520 – 3239 | 30 s | 6 |
| Half 2 — **hunt** act | 3240 – 5039 | 75 s | 15 |
| **Total** | **5040** | **210 s** | **42** |

A **decision turn** is `turnTicks = 120` ticks (5.0 s). At the first tick of a turn the server
freezes the state, builds the seats' views, collects one **order** per active seat (§Server), and
hands them to the deterministic control layer, which drives the cogs for all 120 ticks of that
turn. The LLM is the tactician at 0.2 Hz; the control layer is the reflexes at 24 Hz. **During a
build act only the three hiding seats are queried** — the seekers are locked in the pen, blind and
frozen, and are not asked for an order they could not act on (it also saves 3 calls per prep turn).

**Half reset (exact, at tick 2520).** Every crate returns to its authored start position in state
`loose`; all `broken` crates return; every cog's velocity, aim and lock/pry progress are zeroed;
`locks_used` is cleared; found hiders leave the caught pen. The new hiders spawn at
`(150,110) (617,110) (1085,110)` — slot-ascending within the team — and the new seekers at
`(588,600) (617,600) (646,600)` in the pen. Emit `half_end` then `half_start`. Nothing carries
across the intermission except the score.

### Resolution order (exact, per tick `t`)

Applied in this order every tick, with no exceptions. "Seat order" always means ascending slot
index 0…5.

1. **Phase clock.** Derive `half`, `act` and `turn` from `t` and the table above. If `t` is the
   first tick of a turn, install the orders collected for that turn (§Server: how they are
   collected, and what happens when one is late). If `t == 2520`, run the half reset first.
2. **Frozen seats.** During a build act, each seeker's control is forced to
   `(move_x 0, move_y 0, aim_turn 0, action 0)`, its velocity is held at 0, its aim is held, its
   lantern is off, and the pen's north door is solid. Steps 3–4 and 9–12 are skipped for those
   cogs; the tick still records controls (step 5), keyframes (step 14) and phase events (step 15).
3. **Control compile.** For each cog in seat order, the control layer (§Decisions, "The control
   layer") reads the current world state and the seat's active order and produces
   `(move_x, move_y, aim_turn, action)`.
4. **Quantise.** `move_x`, `move_y` → `int8` in −100…100; `aim_turn` → `int8` clamped to
   ±`aimTurnRate` (±5); `action` → `uint8` bitfield `bit0 = lock`, `bit1 = pry`, `bit2 = crawl`,
   bits 3–7 reserved 0. **The sim consumes only these bytes and the replay records only these
   bytes** — this is the determinism boundary (§Sim module).
5. **Aim.** `aim = (aim + aim_turn) mod 256` per cog in seat order.
6. **Motion.** Paintbot's integer step per cog in seat order: accelerate by `Accel` along
   `(move_x, move_y)/100` (halved when the crawl bit is set), apply friction `×144/256`, clamp to
   the cog's `MaxSpeed` (halved to 40 % when crawling), integrate position, resolve walls with the
   slide scan (`MovementSlideMaxScan = 3`), then resolve cog–cog overlap for each unordered pair in
   ascending index order with restitution `PlayerBouncePct = 40`.
7. **Crates.** For each crate in index order, for each cog in seat order whose footprint now
   overlaps it: let `a` be the dominant axis of that cog's displacement this tick (x if
   `|dx| ≥ |dy|`, else y; ties → x). If the crate is `loose` and its 48 × 48 box translated by
   `sign(displacement_a) × pushPx` along `a` is clear of walls, other crates and other cogs — where
   `pushPx = 6` for a hider and `4` for a seeker (a seeker can shove a loose crate but not fast) —
   the crate moves and a `crate_push` event + push sound ring are emitted (rate-limited to one per
   crate per 12 ticks). Otherwise the crate does not move and the cog's position is reverted along
   `a` (the crate is solid). A crawling cog cannot push (crawl and shove are exclusive).
8. **Lock and pry.** A **hider** with the lock bit set, speed below `StopThreshold`, and its body
   within 20 px of a `loose` crate's box accrues `lock_progress += 1` on that crate; at
   `lockTicks = 24` the crate becomes `locked`, `locks_used[seat] += 1`, and `crate_lock` is
   emitted. A lock is refused if `locks_used[seat] == maxLocksPerHider = 3`. A **seeker** with the
   pry bit set, speed below `StopThreshold`, within 20 px of a `locked` crate accrues
   `pry_progress += 1`; at `pryTicks = 72` (3.0 s) the crate becomes `broken`, `crate_break` is
   emitted with a 900 px sound ring. Any progress resets to 0 the moment the cog moves, clears the
   bit, or changes target crate. `crate_pry` is emitted at 25/50/75 % so the viewer can show the
   breach building.
9. **Occlusion rebake.** If any crate moved, locked or broke this tick, rebuild `blockMask` =
   static `wallMask` bits OR the footprints of all non-broken crates. Ten AABB stamps; bounded.
10. **Lanterns and sight.** Hunt act only. For each seeker in seat order run the shadowcast over
    `blockMask` from its cell, apply the cone (`|brad_delta| ≤ 18`, integer comparison — **no
    trigonometry anywhere in the sim step**, §Sim module) and the range test
    (`dx*dx + dy*dy ≤ 420²`, integers), then union in the 60 px bubble. Union the three seekers'
    sets into `teamLit`. For each hider compute `seekers_seen` (seekers within 700 px with line of
    sight) and `beams` (seekers whose lit set covers any cell within 220 px of the hider).
11. **Detection.** For each unfound hider `H` in seat order: if `H`'s body cell ∈ `teamLit`, then
    `lit_streak[H] += 1`, else `lit_streak[H] = 0`; emit `spot` on the tick the streak becomes 1.
    `H` is **FOUND** when `lit_streak[H] ≥ lockOnTicks = 12` (0.5 s held in the beam) **or** when
    any seeker's body centre is within 24 px of `H` with line of sight (a touch tag). On FOUND:
    emit `found` (with `mode: "beam"` or `"tag"`, the finding seeker's alias and the hider's hidden
    seconds), set `found_tick[H] = t`, and teleport `H` to the caught pen at
    `(617, 620) + (24 × index_in_team, 0)`, where it is inert for the rest of the half.
12. **Score accrual.** Hunt act only: for each hider that is not found *as of this tick*,
    `hidden_ticks[seat] += 1`.
13. **Heartbeat and sound decay.** Compute each seeker's heartbeat band; expire sound rings older
    than 24 ticks.
14. **Keyframe.** If `t mod 24 == 0`, append a keyframe: tick, each cog `(x, y, aim, state)`, each
    crate `(x, y, state)`, per-seeker heartbeat band, hidden-tick totals, and the u32 state digest
    (§Sim module).
15. **Act / half / match end.** If `t + 1` ends a build act → emit `act_end{reason:"time"}` and
    `act_start{act:"hunt"}` (pen door opens, lanterns on). If all three hiders are found before the
    hunt act's last tick → emit `act_end{reason:"all_found"}` and **skip the remaining hunt ticks of
    that half** (they would accrue nothing; the denominator is unchanged, see §Scoring — this also
    returns wall clock to the budget). If `t + 1` ends half 1 → `half_end`, then the half reset at
    tick 2520. If `t + 1 == 5040` (or the variant's total) → end the match, `reason: "complete"`,
    `end_rule: "full_time"`.

### Scoring, sign, and what the league ranks by

Seconds-hidden, normalised, compared across the two symmetric halves, exactly zero-sum between the
sides:

```
huntTicksPlayed(half)   = hunt ticks actually simulated in that half   (1800 unless the
                          episode was cut short by the wall-clock stop)
hidden_ticks(seat)      = hunt ticks in that seat's HIDING half during which it was unfound
                          (0 <= hidden_ticks <= huntTicksPlayed)
f(team)                 = sum over the team's 3 seats of hidden_ticks
                          -------------------------------------------
                                3 * huntTicksPlayed(the half that team hid)

score(Moth) = 0.5 + 0.5 * (f(Moth) - f(Owl))
score(Owl)  = 1.0 - score(Moth)
```

**Higher is better.** `f ∈ [0, 1]`, so `score ∈ [0, 1]` and `score(Moth) + score(Owl) == 1.0` for
every legal outcome — the game is exactly zero-sum between the sides, which is the idea's integrity
claim. **Every seat carries its team's score**, so `results.scores` is three copies of one number
and three copies of the other and sums to 3.0 across six seats. Hiding well and seeking well are
the same skill on this scale: a team's own `f` is its hiding, and the *opponent's* `f` is what its
seeking held down. `win[seat] = score(seat) > 0.5`; `f(Moth) == f(Owl)` is a draw
(`winner: null`, all `win` false).

Worked example: Moth's three hiders survive 75 s, 41 s and 12 s (`f = 128/225 = 0.569`); Owl's
survive 75 s, 75 s and 33 s (`f = 183/225 = 0.813`). `score(Owl) = 0.5 + 0.5 × 0.244 = 0.622`,
`score(Moth) = 0.378`.

**The league ranks by Elo computed from `results.scores`** (the platform's `scores` array is the
only cross-game ranking input; Elo 1000 start, K 32, per the phase-50 league settings). A `fault`
episode scores 0.5 for every seat — an infra fault is nobody's loss.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.end_rule` carries the detail.

| `reason` | `end_rule` | When |
|---|---|---|
| `complete` | `full_time` | All 5040 ticks (or the variant's total) simulated, including any hunt act cut short by `all_found`. The normal ending. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660 by default) elapsed before full time. The sim stops at that tick; the score uses `huntTicksPlayed` per half as above. **Declared acceptable** for phase-60 verification: it means the hosted LLM was slow, not that the game broke, and the replay is complete up to the stop tick. If half 2's hunt never started, both sides score 0.5 and `winner` is `null`. |
| `fault` | `sim_fault` | A sim invariant guard tripped (a cog outside the arena, a crate overlapping a wall, a negative hidden-tick count). All scores 0.5, `winner: null`, partial replay written. |
| `fault` | `host_error` | An unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

No other value may appear. A seat that never connects does **not** end the episode: its cog is
driven by the `warden` scripted baseline for the whole match, the no-show is reported to
`COGAME_PLAYER_FAILURE_URI` (lowest offending slot only, paintbot's `declarePlayerFailure`,
`src/ctf/server.nim:1213-1230`), and the match plays to `full_time`.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {warden, moth}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=warden`. **A scripted policy seated as a champion is a failure state.**

**Where the decision happens.** *Deviation from paintbot, deliberate:* paintbot's bot decides inside
its own container (`players/baseline/baseline.nim`, a Sprite-v1 client). In lantern the **game
server** owns the LLM client, exactly as bullwhip does (`src/bullwhip/llm.nim`). Reasons: the hosted
Bedrock sidecar credentials and the `anthropic_api_key` coworld secret are injected into the *game*
pod; phase 60 greps the *game* log for `falling back` / `LLM provider is unavailable`; "one parallel
batch per turn" is a game-server property; `templates/tools/ci/docker_smoke.sh` forwards
`ANTHROPIC_API_KEY` to the game container only; and keeping both policy kinds inside the server
makes the recorded action log reproducible with no network in the loop. The player container is
therefore thin: it connects, sends one `register` frame carrying its prompt (or its baseline name),
and thereafter only receives (§Server).

**Cadence and batching.** One decision turn every `turnTicks = 120` ticks (5.0 s of sim time), 42
turns per episode. At each turn the server builds the active seats' request bodies and issues them
as **one parallel batch** — a single `curly.makeRequests(batch, timeoutSeconds)` over all open
seats, exactly bullwhip's `decideAll` (`src/bullwhip/llm.nim:419-472`) — wrapped in one per-turn
deadline. **Seats are never queried sequentially.** A hunt turn batches 6 requests; a build turn
batches 3 (seekers are frozen). Per episode: 30 hunt turns × 6 + 12 build turns × 3 = **216 LLM
calls**, at most 6 in flight.

**Wall-clock arithmetic (must stay inside 60 % of `episodeTimeoutSeconds` 1200 = 720 s):**

```
42 turns x 13.0 s per-turn budget            = 546 s
player connect wait (6 seats, typical)       =  20 s   (cap: playerConnectTimeoutSeconds 90)
sim: 5040 ticks x 6 cogs incl. FOV, native   =   6 s   (perf test bounds this at <= 30 s)
board bake + results + replay writes         =  30 s
                                             -------
expected worst case                          = 602 s   < 720 s  (118 s margin)
engine hard stop wallClockBudgetSeconds      = 660 s   -> reason "deadline"
platform kill (episode_timeout_minutes 20)   = 1200 s
```

Typical is far under: a turn whose slowest seat answers in 4 s costs 4 s, not 13. With no
credentials at all (offline certification, the docker smoke) the LLM client disables itself on
first discovery, every turn falls back instantly with no network wait, and the whole episode
finishes in seconds.

**Per-turn timing, per seat:** first attempt deadline **8.5 s**. On timeout, transport error,
non-JSON reply, or a reply carrying no usable order → **one retry** with a 3.5 s deadline and the
"your previous reply was invalid" hint appended (bullwhip's retry shape). If that also fails →
that seat's order for this turn is the **`warden` scripted order**, computed in microseconds, and a
`fallback` event is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`. Worst case
8.5 + 3.5 = 12.0 s ≤ the 13.0 s turn budget.

**Budget guard (settle early rather than overrun).** At the start of each turn, if
`elapsed + 2 × turnBudgetSeconds > wallClockBudgetSeconds`, the LLM is skipped for **all remaining
turns** and the episode finishes on the scripted layer (< 1 ms per turn), so it ends
`complete/full_time` instead of `deadline`. A `budget_guard` event records the turn it engaged.
Only if even that overruns — arithmetically impossible, but the check is unconditional — does the
engine stop at 660 s with `deadline/wall_clock`.

**Degrade, never hang.** Every wait is bounded: the two attempt deadlines, one outer per-turn
deadline of 13.0 s, `playerConnectTimeoutSeconds` (90 hosted, 60 in the cert fixture) on the connect
wait, a 3.0 s per-seat deadline on the final done-broadcast, and the 660 s engine stop. The game
container does **not** receive `COWORLD_TIMEOUT_SECONDS`; 1200 s is assumed and never approached. A
seat that disconnects mid-match keeps playing: its order source degrades to `warden` and revives on
reconnect. No failure mode leaves a cog unactuated — the control layer always has an order,
defaulting to the previous turn's, then to `warden`.

**The LLM client** (`src/lantern/llm.nim`) is bullwhip's `llm.nim` with lantern's schema. Credential
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
You are one cog in a 3v3 hide-and-seek match on a dark warehouse floor, 1235 by 659
pixels, x right, y down. Each half has two acts. In the BUILD act (30 s) the hiding
team has the lights on and can shove and bolt down 48x48 crates; the seeking team is
locked in its pen. In the HUNT act (75 s) the lights go out, the pen opens, and the
seekers sweep the dark with flashlights. A hider scores one point per tick it is not
yet found. Held in a beam for half a second, or touched, and you are found. Sides swap
at half time, so you will play both roles - your prompt must cover both.
Every 5 seconds you issue ONE order. A deterministic controller executes it for the
next 5 seconds: it steers you to your target, turns your aim, and holds the lock or pry
button when the order says so. You do not drive motors directly.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"intent":"<one of the legal intents for your role>",
 "target":[x,y],          // a point on the floor; clamped into the map
 "crate":"C0".."C9"|null,  // the crate a push/lock/pry order acts on
 "aim":"sweep|hold|track|target",
 "crawl":true|false,       // crawl: 40% speed, no footsteps, cannot push
 "note":"<=140 chars",     // your reasoning, shown to spectators only
 "say":"<=32 chars"}       // one short line, shown to spectators only
Hider intents: push (shove crate toward target), lock (bolt crate down; 3 locks each
per half, 1 s each), hide (go to target and hold still), flee (move away from the
nearest beam or seen seeker), scout (move to target), wait (hold position).
Seeker intents: sweep (advance to target while the beam sweeps), beeline (straight to
target, beam forward), chase (drive at the last lit hider), pry (breach a locked crate;
3 s, very loud), hold (hold target, beam sweeping), wait (hold position).
A locked crate cannot be pushed by anyone; only a pry breaks it. Crates block light and
line of sight. Pushing and running make noise; crawling does not.
```

**User message** = the seat's `PLAYER_PROMPT` text, then a blank line, then the seat's view JSON
(§Server). The prompt text is never echoed into the replay (only `policy_kind`).

**Champion #1 — `lantern-warren` (owner daveey), `PLAYER_PROMPT`:**

```
Build a warren, then vanish into it; when you seek, cut the map into thirds and never
leave one uncleared.
As a hider: spend the first two orders pushing, not walking. Pick the nearest loose
crate and push it toward the alcove you intend to occupy so the alcove ends up with one
opening you can watch, then lock exactly that crate with intent "lock" - a locked crate
is the only thing a seeker cannot shove aside. Keep one lock in reserve for the hunt.
Coordinate by geography, not by chat: take the alcove nearest your spawn and leave the
others to your team, so all three of you are not in one room for one beam to sweep. The
moment the hunt starts, set crawl true and stop moving: a still cog behind an opaque
crate is invisible, and footsteps are the only thing that gives a good hiding place
away. Use "flee" only when a beam is reported within 220 px AND the seeker is not
already looking at you; break contact around a crate corner, never down a straight lane.
As a seeker: on the first hunt order claim a third of the map by x (left is 0-410,
middle 410-825, right 825-1235) and sweep it with intent "sweep", aim "sweep", targeting
the far corner of your third; do not follow your team-mates. Read the heartbeat every
turn: cold or cool means your third is empty and you should push deeper, warm means slow
down and let the beam do the work, hot or burning means stop advancing and sweep in
place. On any lit hider switch to "chase" with aim "track" and stay on it - half a
second in the beam is a find. Only pry a locked crate when the heartbeat is burning and
nothing has been lit for two orders.
```

**Champion #2 — `lantern-owlnight` (owner daveey-1,
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`:**

```
Hide in the open and hunt by sound.
As a hider: do not build a room - build a screen. Push one crate into the middle of a
long sightline so it splits the lane, lock it, and then keep that crate between you and
wherever the beams are. Prefer "hide" targets that sit against the outer wall behind a
pillar rather than inside an alcove: an alcove is the first place a seeker sweeps and it
has one exit, while a wall line has two. Always crawl once the hunt begins, and when a
beam is reported, "flee" perpendicular to its bearing rather than away from it - you
want to leave the cone, not outrun it. Spend at most two locks; the third crate is worth
more loose, because a loose crate you can shove again mid-hunt to close a lane behind
you.
As a seeker: hunt the noise. Open with "beeline" to the centre of the floor so all three
lanes are within reach, then let sound and the heartbeat pick your next target - a push
ring means someone was still building, a footstep ring means someone just moved, and
both are worth more than an unmotivated sweep. Keep aim "sweep" while travelling and aim
"track" the instant anything is lit. Split from your team-mates by heartbeat, not by
map: if two of you read the same band, one should turn away. When the clock is under 20
seconds and nothing is lit, pry the nearest locked crate - the noise costs nothing at
that point and a broken crate turns a hiding place into an empty floor.
```

### The control layer (deterministic; shared by every policy)

LLM orders and scripted orders are compiled by the *same* code, so the two policy kinds are
strictly comparable and the recorded control bytes are the whole truth. Per cog per tick:

1. **Steering point `p*`** (`x` = own position, `c` = the order's crate centre, `T` = the order's
   target, clamped into the map on parse):
   - `push` — if `|x − (c − û(T − c)·30)| > 10`, `p* = c − û(T − c)·30` (get behind the crate);
     else `p* = T` (shove it that way). `û(v)` is `v` scaled to length 1 in integer units.
   - `lock` / `pry` — `p* =` the midpoint of `c`'s nearest edge; on arrival (≤ 10 px) `p* = x`
     (hold still) and the lock/pry bit is set.
   - `hide` / `scout` / `hold` / `beeline` / `sweep` — `p* = T`.
   - `flee` — `p* = x + 200 · û(x − threat)`, where `threat` is the nearest seen seeker, else the
     source of the nearest reported beam, else the nearest heard ring, else the map centre;
     recomputed every tick.
   - `chase` — `p* =` the most recent lit position of the nearest unfound hider, else `T`.
   - `wait` — `p* = x`.
2. **Move command.** `d = p* − x`; if `|d| ≤ 8`, `move = (0, 0)`; else `move = û(d)·100` in
   integers. **Unstick rule:** if the cog's net displacement over the last 24 ticks is < 6 px while
   `move ≠ (0,0)`, rotate `move` by +45° (an eight-entry integer direction table) and keep rotating
   once per 24 ticks until it moves. There is **no pathfinder** — a target chosen behind a wall is
   a bad order, and that is part of the skill; the unstick rule only guarantees the cog never welds
   itself to a corner.
3. **Aim command.** `sweep`: `+aimTurnRate` for 24 ticks, `−aimTurnRate` for 48, `+` for 48, … a
   4 s triangle whose phase is seeded by `seat_index × 16` ticks so the three beams are not
   synchronised. `hold`: 0. `target`: turn toward `p*`, at most `aimTurnRate` per tick.
   `track`: turn toward the nearest lit hider, else the newest heard ring, else `p*`.
4. **Action bits.** `lock` / `pry` as in step 1; `crawl` straight from `order.crawl` (forced off
   while an active `push` order is in contact with its crate).

**Scripted baselines** (both emit the identical order JSON on the same 5 s cadence, so their output
is legal by construction and directly comparable to an LLM's; both are pure functions of the world
state — no randomness beyond the episode seed — which is what makes the bounded-orders test in
§Tests meaningful):

- **`warden`** — the certification player, the default, and the stronger of the two.
  *Hiding:* seat `k` of the team is assigned nook `k` from the map file's authored `nooks[]` list
  (three three-sided alcoves, ordered by x). Build act: push the nearest `loose` crate toward the
  nook's opening (`intent: push`) until the crate's box covers ≥ 60 % of the opening's width, then
  `lock` it; repeat while `locks_used < 2`; if the opening is already covered, `hide` at the nook
  anchor. Hunt act: `hide` at the nook anchor with `crawl: true`; if a beam is reported within
  220 px, `flee` for one turn, then `hide` at the *next* nook anchor in cyclic order.
  *Seeking:* seat `k` takes lane `k` of the authored `sweep_lanes[]` (left / middle / right) and
  walks its waypoint list in order with `intent: sweep`, `aim: sweep`; on any lit hider →
  `chase` / `aim: track` until it is found or two turns pass unlit; if the heartbeat has been `hot`
  or `burning` for two consecutive turns with nothing lit → `pry` the nearest `locked` crate.
- **`moth`** — the second filler, deliberately weaker and different in shape, so the ladder has a
  spread. *Hiding:* never touches a crate; walks to the floor cell farthest from the pen (authored
  as `far_corner`) and stands still, `crawl: true`. *Seeking:* all three `beeline` to the map
  centre, then `sweep` toward a waypoint drawn from a PCG32 stream seeded with
  `episode_seed xor (seat << 8)`, re-drawn every four turns; `chase` on anything lit.

---

## Sim module

`src/lantern/sim.nim` is paintbot's `src/ctf/sim.nim` with the CTF rule surface removed and the
hide-and-seek rules put in its place. What is kept, what is dropped, and what is new:

**Kept from paintbot, by path:**

- `src/ctf/sim_types.nim` → `src/lantern/types.nim` — the motion constants
  (`MotionScale`, `Accel`, `FrictionNum/Den`, `MaxSpeed`, `StopThreshold`, `PlayerHalf`,
  `PlayerBouncePct`, `MovementSlideMaxScan`), `TargetFps`/`ReplayFps` = 24, `PlaybackSpeeds`,
  `MapWidth`/`MapHeight`, and the **flatty wire types whose field order is sacred** (paintbot's
  `AGENTS.md` rule; it still holds — the broadcast stream is flatty-encoded).
  `GameVersion` is kept as the rules gate and starts at `"1"` for lantern (paintbot's GV43 history
  does not travel; the changelog-comment convention does).
- `src/ctf/arena.nim` → `src/lantern/arena.nim` — the `mapSpec` loader, the `ArenaShape`
  rect/disc/diamond/diagonal/polygon stamping, the `wallMask` bake, the integer even-odd
  `pointInPolygon` with its STRICT-STRADDLE convention, the pixel/line-of-sight queries, and the
  process-global map install. **Dropped:** the procedural generator, the validators, `mapDiagnostics`,
  `map_pool.nim`, `mapgen_styles.nim` and the whole `mapSize`/`mapSymmetry`/`mapEndzone` knob family.
  *Deviation from paintbot, deliberate:* lantern ships **one authored map**, because both halves
  must be geometrically identical for the score to compare like with like and because a hiding game
  wants a hand-tuned distribution of alcoves and sightlines, not a seeded draw. Terrain variety is
  §Out of scope (v1).
- `src/ctf/sim.nim:2257-2475` — the shadowcast FOV, `FovCellCount`, `fovCellIndex`, the per-player
  `fovCaches`, and `visiblePlayer`-style queries. This is the flashlight, and it is the single
  biggest reason paintbot is the right starter. **One change:** `applyFovCone` currently tests the
  cone with `cos(float(visionConeDeg) * PI / 180.0)`. Lantern replaces that with the integer test
  `abs(((bearingBrads - aimBrads + 128) mod 256) - 128) <= lanternConeBrads` and the range test with
  `dx*dx + dy*dy <= lanternRangePx*lanternRangePx`. **No `sin`, `cos`, `atan2`, `pow`, `sqrt`, `exp`,
  `log`, `fmod` or float arithmetic of any kind appears in the sim step** — the whole step is
  integer, so the native build and the emscripten viewer build agree bit-for-bit by construction.
  A source-grep test enforces the ban (§Tests).
- `src/ctf/sim.nim:1550-1975` (`placeBarrier`, `barrierIndexAt`, `playerTouchesBarrier`,
  `damageBarrier`, `flattenBarrier`, `updateBarriers`) → `src/lantern/crates.nim`. The crate is the
  barrier grown up: same "prop with a footprint, a state and a touch radius" shape, now 48 px,
  opaque, pushable, lockable and pryable.
- `src/ctf/sim_state.nim` → `src/lantern/state.nim` — logging, the `gameHash` state digest, the
  event buffer, spawn placement. `src/ctf/sim_config.nim` → `src/lantern/config.nim` — the
  `GameConfig` lifecycle and `configJson()`. `src/ctf/roster.nim` → `src/lantern/roster.nim` —
  join/auth/slots/tokens. `src/ctf/events.nim`, `src/ctf/labels.nim`, `src/ctf/broadcast.nim` and
  `src/ctf/global.nim`'s sprite-protocol broadcast layer are kept (the live `/global` stream and the
  viewer both ride them); the CTF-specific art in `global.nim` is replaced (§Viewer).
- `src/ctf.nim` → `src/lantern.nim` — the entrypoint, **including the rule that seed randomisation
  happens before `config.update`** so every seed-derived draw follows the final seed.

**Dropped entirely:** guns, hitscan, aim jitter, grenades, the barrage, med kits, shields, the
plasma arc, paint puddles, spray cans, lives/hit points/respawn, perks, handicaps, achievements,
the four-team mode, shouts, the map editor (`tools/map_editor*`), the `arena/` WIT component
bindings, `caos/` and `caos-tools/`. Roughly two thirds of paintbot's 38 k lines do not survive the
fork; what survives is the loop, the physics, the fog, the props, the replay and the chrome.

**New:** `src/lantern/rules.nim` — the phase clock, detection, locking/prying, sound rings,
heartbeat bands, the half reset and the score; `src/lantern/control.nim` — the control layer;
`src/lantern/orders.nim` — the order schema, tolerant parsing and repair; `src/lantern/llm.nim` —
bullwhip's client; `src/lantern/baselines.nim` — `warden` and `moth`; `src/lantern/replay.nim` —
the JSON replay writer/reader.

**The map file.** `data/vault.mapspec.json`, loaded by `mapPath: "vault"`, is authored (not
generated) and pinned verbatim into every replay's config, exactly as paintbot pins `mapSpec`:

```json
{"name": "vault", "width": 1235, "height": 659,
 "obstacles": [ {"kind": "rect", "x": …, "y": …, "w": …, "h": …}, … ],
 "pen": {"x": 558, "y": 545, "w": 120, "h": 110, "door": {"x": 558, "y": 545, "w": 120, "h": 8}},
 "hider_spawns": [[150,110],[617,110],[1085,110]],
 "seeker_spawns": [[588,600],[617,600],[646,600]],
 "caught_pen": [617, 620],
 "crates": [[300,180],[935,479],[500,120],[735,539],[300,470],
            [935,189],[500,540],[735,119],[617,240],[618,419]],
 "nooks": [{"anchor": [220,300], "opening": [[196,246],[196,354]]},
           {"anchor": [617,470], "opening": [[563,446],[671,446]]},
           {"anchor": [1015,300], "opening": [[1039,246],[1039,354]]}],
 "sweep_lanes": [[[205,560],[205,120],[400,120],[400,560]],
                 [[617,470],[617,150],[500,300],[735,300]],
                 [[1030,560],[1030,120],[835,120],[835,560]]],
 "far_corner": [1085, 90]}
```

A test asserts the geometry is symmetric under 180° rotation about (617, 329) — the map must not
favour a spawn — and that every hider spawn, seeker spawn, nook anchor and crate box sits on free
floor.

**Randomness.** One PCG32 stream seeded from the episode seed, integer arithmetic only, used for
exactly two things: the sound-ring jitter and `moth`'s waypoint draws. Everything else is
deterministic. `src/lantern.nim` randomises the seed at startup unless the config pins one
(paintbot's `seedPinned`/`stripUnpinnedSeed` logic kept verbatim, `src/ctf.nim:7-46`).

**State digest.** `lanternStateDigest()` returns an FNV-1a u32 over the raw bytes of every cog's
position/velocity/aim/state, every crate's position/state, the per-seat hidden-tick counters, the
phase clock and the tick. It is paintbot's `gameHash` idea widened to the full state, it goes into
every keyframe, and it is the cross-build equality check that lets the wasm viewer prove it
re-derived the same match (paintbot already surfaces a mismatch as the `#mmwarn` line — kept).

**Determinism contract (the inviolable property).** Same seed + same control bytes ⇒ same digest at
every keyframe, in the native build *and* in the emscripten build. It holds because the step is
integer-only. `-ffast-math` and float sim arithmetic are banned and the ban is grepped in CI.

**Performance.** The heavy per-tick cost is three shadowcasts (hunt act only) over a 1235 × 659
cell mask. Paintbot runs sixteen of these at 24 fps live; three is comfortable. Target ≥ 4000
ticks/s native (a full match ≈ 1.3 s of CPU), tested with a generous 30 s bound.

---

## Server, player, protocol

`src/lantern/server.nim` is a fork of `src/ctf/server.nim`: the same mummy HTTP/WebSocket server
(`newServer(httpHandler, websocketHandler, workerThreads = 4)`), the same routes
(`GET /healthz`, the player WebSocket at `/player?slot=N&token=T`, the spectator `/global`, the
browser clients under `/client/…`, and in replay mode `/replay-data` + `/client/replay`), the same
403 on a bad slot/token and 409 on a duplicate connection, the same
`bitworld/runtime` `RuntimeConfig` contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`,
`COGAME_SAVE_REPLAY_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`,
`COGAME_EVENTS_URI`, `COGAME_METRICS_URI` — the last two `file://`-only and loudly rejected
otherwise), the same **write order at the end of an episode** (broadcast `done` to every seat with a
3.0 s per-seat deadline → write the replay → `writeResults`), and the same pre-listen board bake so
a viewer's first frame is instant.

**Player handshake (the only thing a player container must do).** On connect the player sends
exactly one text frame:

```json
{"type": "register", "prompt": "<strategy text or empty>",
 "scripted": "warden" | "moth" | null,
 "policy": "<free label, <=48 runes>"}
```

`src/lantern_player.nim` reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED` and
`PLAYER_POLICY_LABEL`, sends that frame, then receives until `{"done": true, …}` and exits 0. A seat
that never registers, or registers with neither field, is treated as `scripted: "warden"`.
`PLAYER_SCRIPTED` parsing follows bullwhip's `parseScriptKind`: `warden`/`1`/`true`/`yes` → warden,
`moth` → moth, anything else → none.

**Per turn the server pushes to each seat** (informational — the seat is not required to answer;
decisions are made server-side):

```json
{"type": "turn", "turn": 17, "tick": 2040, "half": 1, "act": "hunt",
 "role": "hider", "view": { … }, "order_source": "llm"}
```

and at the end `{"done": true, "result": { …the results document… }}`, then close.

### The per-seat view (exactly what is visible, and what is hidden)

Coordinates are integers (map pixels). This object is both the `view` in the turn frame and the tail
of the LLM user message. Two shapes, one per role.

**Hider view:**

```json
{"turn": 4, "of": 42, "half": 1, "act": "build",
 "clock": {"act_left_s": 10.0, "hunt_left_s": 75.0},
 "you": {"alias": "Moth-2", "pos": [612, 118], "aim": 64, "crawl": false,
         "found": false, "hidden_s": 0.0, "locks_left": 3},
 "map": {"w": 1235, "h": 659,
         "walls": [[0,0,1235,16], …],
         "nooks": [{"anchor": [220,300], "opening": [[196,246],[196,354]]}, …],
         "pen": [558, 545, 120, 110]},
 "crates": [{"id": "C0", "pos": [300,180], "state": "loose"},
            {"id": "C8", "pos": [617,240], "state": "locked"}, … 10 … ],
 "team": [{"alias": "Moth-1", "pos": [150,110], "found": false, "hidden_s": 0.0}, … 3 … ],
 "seekers_seen": [{"alias": "Owl-3", "pos": [700,540], "aim": 96, "dist": 430}],
 "beams": [{"bearing": 192, "band": "near"}],
 "sounds": [{"kind": "break", "pos": [742,520], "age_ticks": 8}],
 "found_count": 0,
 "your_last_order": { …the order you played last turn, or null on turn 0… }}
```

**Seeker view:**

```json
{"turn": 19, "of": 42, "half": 1, "act": "hunt",
 "clock": {"act_left_s": 40.0},
 "you": {"alias": "Owl-1", "pos": [430, 300], "aim": 32,
         "heartbeat": "warm", "prying": null},
 "map": { …identical to the hider's map block… },
 "lit": {"crates": [{"id": "C4", "pos": [352,470], "state": "locked"}],
         "hiders": [{"alias": "Moth-3", "pos": [910,215], "lit_by": "Owl-2",
                     "streak_ticks": 4}]},
 "team": [{"alias": "Owl-2", "pos": [900,240], "aim": 200, "heartbeat": "hot"}, … 3 … ],
 "sounds": [{"kind": "push", "pos": [560,180], "age_ticks": 14},
            {"kind": "step", "pos": [905,260], "age_ticks": 3}],
 "found": [{"alias": "Moth-1", "at_s": 21.5, "by": "Owl-2", "mode": "beam"}],
 "found_count": 1, "hiders_left": 2,
 "your_last_order": { … }}
```

**Visible to a hider:** the full static map, **all ten crate positions and states** (a hider knows
the fort it built — this is the asymmetry that makes construction pay), its own trio's positions and
found state, its own clock and locks left, seekers within 700 px with line of sight, the bearing and
proximity band of any beam whose lit area comes within 220 px, and break-ring sounds.
**Hidden from a hider:** seekers outside 700 px or behind cover, seekers' aim while unseen, footstep
and push rings, seekers' orders/notes/prompts, the seed.

**Visible to a seeker:** the full static map, its own position/aim/heartbeat, **only what the team's
three lanterns currently light** (crates and hiders, exact), the team-mates' positions and heartbeat
bands, every sound ring within earshot (jittered), the found list and the clock.
**Hidden from a seeker:** every unlit crate and every unlit hider — a seeker does not know where the
crates ended up, which is what makes the fort worth building — the hiders' orders, notes, prompts and
`say` text, the exact heartbeat distance (only the band), and the seed.

**Hidden from everyone, both roles:** the opponent's prompts, notes and `say` strings (they exist
only in the replay, for spectators), the real player names behind the aliases, and future ticks.
That asymmetry — aliases in-game, real names spectator-side — is the two-name-space pin.

### Order schema and character caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"intent": "push", "target": [196, 300], "crate": "C4",
 "aim": "target", "crawl": false,
 "note": "screening the west alcove before the lights go", "say": "west screen"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `intent` | enum | hider: `push` `lock` `hide` `flee` `scout` `wait`; seeker: `sweep` `beeline` `chase` `pry` `hold` `wait` | unknown, or legal-for-the-other-role → `hide` (hider) / `sweep` (seeker) |
| `target` | `[int, int]` | finite; clamped to `x ∈ [8, 1227]`, `y ∈ [8, 651]` | missing/non-finite → the cog's current position |
| `crate` | string / null | `C0`…`C9`, case-insensitive, **≤ 4 runes** | unknown id → the nearest crate legal for the intent; none legal → intent degrades (`push`/`lock` → `hide`, `pry` → `sweep`) |
| `aim` | enum | `sweep` `hold` `track` `target` | → `target`; ignored for hiders (they carry no lantern) |
| `crawl` | bool | `true`/`false`; accepts `"true"`/`"false"`/`0`/`1` | → `false`; forced `false` for a seeker (seekers do not crawl) |
| `note` | string | **≤ 140 runes** | truncated to 140 runes |
| `say` | string | **≤ 32 runes** | truncated to 32 runes |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and `register.prompt` **≤ 4000 runes** at the
transport (an over-long prompt is truncated, not rejected) — the prompt is never written to the
replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes.** In Nim that means walking the
string with `runeSubStr`/`toRunes` and never slicing a `string` by byte index on any path that
reaches the replay. A byte-truncated multi-byte character is exactly the bug that makes replay bytes
render in a browser but fail a strict JSON parser (playbook gotcha), and §Tests pins it with a
4-byte emoji sitting on the 32nd rune of a `say`.

**Parsing is tolerant** (bullwhip's `extractJsonObject` shape): strip markdown fences, take the
outermost balanced `{…}` if the model prefixed prose, accept numeric strings for `target`, accept
`crate` as an integer 0–9. Only when no object with a usable `intent` can be recovered does the
retry, then the fallback, fire.

### Results document (closed schema — must equal the manifest `results_schema` key-for-key)

Per-seat arrays are length 6 in slot order; `team_*` arrays are length 2, index 0 = Moth, 1 = Owl.

```json
{"names": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)", "Baseline (1)", "Baseline (2)"],
 "aliases": ["Moth-1", "Owl-1", "Moth-2", "Owl-2", "Moth-3", "Owl-3"],
 "teams": ["Moth", "Owl", "Moth", "Owl", "Moth", "Owl"],
 "hid_in_half": [1, 2, 1, 2, 1, 2],
 "policy_kinds": ["llm", "llm", "scripted", "scripted", "scripted", "scripted"],
 "scores": [0.378, 0.622, 0.378, 0.622, 0.378, 0.622],
 "win": [false, true, false, true, false, true],
 "hidden_ticks": [1800, 1800, 984, 1800, 288, 792],
 "hidden_seconds": [75.0, 75.0, 41.0, 75.0, 12.0, 33.0],
 "finds": [1, 0, 0, 2, 0, 1],
 "crates_pushed": [2, 1, 1, 0, 3, 2],
 "crates_locked": [2, 1, 1, 0, 2, 2],
 "crates_broken": [0, 1, 0, 0, 0, 0],
 "team_hidden_frac": [0.569, 0.813],
 "team_hidden_seconds": [128.0, 183.0],
 "reason": "complete",
 "end_rule": "full_time",
 "winner": 1,
 "final_tick": 5040,
 "final_turn": 42,
 "halves_played": 2,
 "hunt_ticks_played": [1800, 1800],
 "seed": 679961,
 "llm_turns": [21, 21, 0, 0, 0, 0],
 "fallback_turns": [0, 0, 0, 0, 0, 0],
 "fallback_causes": [{"timeout": 0, "parse_error": 0, "transport_error": 0,
                      "no_credentials": 0, "budget_guard": 0}, … 6 … ]}
```

`winner` is `0` (Moth), `1` (Owl) or `null` (draw). Adding or removing a key here means editing
`coworld_manifest_template.json`'s `results_schema` and `tools/ci/docker_smoke.sh`'s expectations in
the same commit.

### Replay bytes (self-sufficient, strict UTF-8 JSON)

*Deviation from paintbot, deliberate:* paintbot writes the binary `COWLDCTF` format (a JSON config
followed by recorded inputs). Lantern writes **UTF-8 JSON**, following bullwhip's
`bullwhip.replay.v1` (`src/bullwhip/server.nim:149`), because SPEC §Definition of done check 4
fetches the replay from S3 and requires valid UTF-8 JSON with a matching `protocol` and a legal
`results.reason`, and the shared `tools/ci/docker_smoke.sh` defaults to
`SMOKE_REQUIRE_REPLAY_JSON=1`. The bulk payload — the per-tick control bytes — rides as one base64
string, so the file stays small and the document stays parseable.

```json
{"protocol": "lantern.replay.v1",
 "format_version": 1,
 "game_version": "1",
 "seed": 679961,
 "config": { …the fully resolved game config, tokens excluded: num_agents, prepTicks,
             huntTicks, turnTicks, halves, turnBudgetSeconds, wallClockBudgetSeconds,
             playerConnectTimeoutSeconds, lanternRangePx, lanternConeBrads,
             visionBubblePx, crateCount, lockTicks, pryTicks, lockOnTicks,
             maxLocksPerHider, mapPath, players:[{"name":…}] … },
 "map": { …data/vault.mapspec.json inlined verbatim… },
 "names": {"players": ["daveey", "daveey-1", "Baseline (1)", …],
           "aliases": ["Moth-1", "Owl-1", "Moth-2", "Owl-2", "Moth-3", "Owl-3"],
           "teams": ["Moth", "Owl", "Moth", "Owl", "Moth", "Owl"],
           "policy_kinds": ["llm", "llm", "scripted", "scripted", "scripted", "scripted"],
           "colors": {"Moth": "#f2c14e", "Owl": "#4ecdc4"}},
 "ticks_per_second": 24, "turn_ticks": 120, "tick_count": 5040,
 "phases": [{"half": 1, "act": "build", "from": 0, "to": 719},
            {"half": 1, "act": "hunt", "from": 720, "to": 2519},
            {"half": 2, "act": "build", "from": 2520, "to": 3239},
            {"half": 2, "act": "hunt", "from": 3240, "to": 5039}],
 "controls_b64": "<base64 of tick_count x 6 x 4 bytes: (move_x i8, move_y i8,
                   aim_turn i8, action u8) per cog per tick>",
 "keyframes": [{"t": 0, "d": 2947483111,
                "cogs": [[150,110,64,0], … 6 … ],
                "crates": [[300,180,0], … 10 … ],
                "hb": [0,0,0], "hid": [0,0,0,0,0,0]}, … every 24 ticks … ],
 "events": [ … the vocabulary below … ],
 "results": { …the results document verbatim… }}
```

`seed` + `map` + `controls_b64` + the integer sim reproduce the episode exactly; `keyframes` carry
the per-second state and its digest `d` so the viewer (and the tests, and a human reading the JSON)
can verify the re-derivation and read the match without running wasm at all. Cog state codes:
`0 = active`, `1 = frozen in pen`, `2 = crawling`, `3 = found`. Crate state codes: `0 = loose`,
`1 = locked`, `2 = broken`. `hb` is the three seekers' heartbeat bands (0 cold … 4 burning); `hid`
is the six hidden-tick counters. Size: 5040 × 24 B → 161 KB of base64, 210 keyframes ≈ 55 KB, events
≈ 90 KB — comfortably under 400 KB.

**Everything the viewer needs is in these bytes** (names, colours, config, map geometry, phase
table, per-tick controls, per-second states, events, seed, results). The viewer contacts nothing but
the S3 URL it was given.

**Event vocabulary** (every record carries `t` = tick; `turn`, `half`, `act` where meaningful):

| `type` | Fields |
|---|---|
| `match_start` | `t`, `seed`, `map`, `aliases`, `teams`, `hid_in_half` |
| `half_start` | `t`, `half`, `hiders` (aliases), `seekers` (aliases) |
| `act_start` | `t`, `half`, `act` (`build`\|`hunt`) |
| `turn_start` | `t`, `turn`, `half`, `act`, `hidden_s` (per team), `hiders_left` |
| `order` | `t`, `turn`, `seat`, `alias`, `role`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `intent`, `target`, `crate`, `aim`, `crawl`, `note`, `say` |
| `fallback` | `t`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `t`, `turn`, `remaining_s` |
| `crate_push` | `t`, `seat`, `alias`, `crate`, `from`, `to` |
| `crate_lock` | `t`, `seat`, `alias`, `crate`, `pos` |
| `crate_pry` | `t`, `seat`, `alias`, `crate`, `pct` (25\|50\|75) |
| `crate_break` | `t`, `seat`, `alias`, `crate`, `pos` |
| `sound` | `t`, `kind` (`step`\|`push`\|`break`), `pos` (jittered), `radius` |
| `spot` | `t`, `seeker`, `hider`, `dist` |
| `found` | `t`, `half`, `hider`, `seeker`, `mode` (`beam`\|`tag`), `hidden_s`, `hiders_left` |
| `act_end` | `t`, `half`, `act`, `reason` (`time`\|`all_found`) |
| `half_end` | `t`, `half`, `hidden_frac`, `hidden_s`, `per_hider` |
| `end` | `t`, `reason`, `end_rule`, `scores`, `team_hidden_frac`, `winner` |

`order`, `found`, `crate_lock`, `crate_break` and `fallback` are the records the phase-60 verifier
reads to judge "the champion seats doing the thing the game is about": a champion seat's `order`
events must carry `source: "llm"` with real `intent`/`note` content, not all fallbacks.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` (forked from
paintbot's, `chmod +x`, invoked by `coworld build` with the absolute bundle directory, keeping
paintbot's safety checks that the target is absolute and named `static-replay-viewer` and lies
inside the repo) builds `Dockerfile.replay-viewer`'s `replay-viewer-builder` stage —
`emscripten/emsdk:4.0.15` + `nimby 0.1.27` pinned by sha256, `nimby use 2.2.4`,
`nimby --global sync nimby.lock` — which compiles **the same Nim sim** as
`nim c -d:emscripten replay-viewer/lantern_replay.nim`, then copies `/workspace/lantern/replay-viewer/dist/.`
into the bundle. The viewer re-derives every frame in the browser from `seed` + `map` +
`controls_b64`, and validates itself against the keyframe digests. The game server still serves
`/client/replay` for local viewing off the identical `dist`. Nothing but S3 is contacted at view
time.

**Files in the bundle** (each must return 200 with a non-trivial size for phase-60 check 8(b)):
`index.html`, `static_replay.js`, `static_replay_worker.js`, `chrome_common.js`,
`wire_constants.js`, `lantern_replay.js`, `lantern_replay.wasm`, `lantern_replay.data`,
`art/floor.jpg`, `art/crate.png`, `art/crate_locked.png`, `art/crate_broken.png`,
`art/cog_moth.png`, `art/cog_owl.png`, `font.ttf`.

**Chrome kept verbatim.** `client/chrome_common.js` is copied unchanged. `client/replay_broadcast.html`
keeps its CSS block and its markup ids exactly: `#viewport`, `#stage`, `#board`, `#lightpool`,
`#grain`, `#chrome`, `#scorebug`, `#plates-l`, `#plates-r`, `#clock`, `#clock-time`,
`#clock-caption`, `#ffwd-mini`, `#viewpanel`, `#minimap`, `#minimap-canvas`, `#zoombar`,
`#zoom-out`, `#zoom-slider`, `#zoom-in`, `#zoom-read`, `#mmwarn`, `#bannerlane`, `#killfeed`,
`#transport`, `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`, `#btn-loop`,
`#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`, `#tick-clock`, `#speedchips`, `#scrub`,
`#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`, `#scrub-head`, `#endcard`, `#ec-headline`,
`#ec-wincond`, `#ec-how`, `#ec-teams`, `#status`, and the `--hudscale` / `--topband` / `--band` /
`.tiny` relayout loop (`client/replay_broadcast.html:4100-4133`) unchanged. The pre-load locker-room
curtain (`#lockerroom`, `#lk-art`, `#lk-bg`, `#lk-sprites`, `#lk-cap`) is kept with lantern's own
plate. **Added markup, and nothing else:** `#heartbar` (three seeker heartbeat bars), `#hidebug`
(the two hidden-second clocks), `#actchip` (BUILD / HUNT / HALF), `#intermission` (the side-swap
card), and `#burst` (the find flash). Removed: the CTF flag icons, the first-person PiP (`#fpv…`),
the kill/lives plumbing that has no counterpart here.

`replay-viewer/static_replay.js` keeps paintbot's OffscreenCanvas-Worker shell verbatim (the
`createCore` / `start` / `stop` / `advance` / `resize` / transform-and-minimap message protocol with
`static_replay_worker.js`, the `data-replay-loaded` and `data-replay-mismatch-tick` attributes and
`showFailure`), with two changes: the loader hands the JSON replay to the wasm module instead of the
binary one, and **bullwhip's `coworld-replay` postMessage bridge is added verbatim** —
`tell("loading")` on script entry, `tell("error", msg)` on failure, and `tell("ready")` inside a
double `requestAnimationFrame` after the first drawn frame (`cogame-bullwhip/replay-viewer/static_replay.js:20-33,120-124`).
SPEC check 8(c) greps the served JS for exactly that bridge. The fetch is bounded by a 20 s
`AbortController` with a Retry button, also from bullwhip.

**Split of responsibilities.** The wasm canvas draws the world (floor, walls, crates, cogs,
darkness, light cones, sound rings, bursts); the DOM chrome draws the scorebug, clocks, heartbeat
bars, event feed, transport and warnings. DOM text is set with `textContent` only (names are
player-controlled data) and stays crisp at any zoom — which is what makes 360 px legibility
achievable.

**Readouts** (the idea's replay plan, item for item):

1. **Flashlight cones sweeping darkness.** The board renders at full brightness only inside the
   union of the three lit sets; everything else is drawn through `#lightpool` as a near-black
   multiply layer (8 % floor luminance, so the geometry is a suggestion, not a void). Each seeker's
   cone is a soft-edged wedge in its team colour at 22 % alpha with a hot 6 px core along the aim
   ray, and it moves every frame because the aim does. Crates inside a cone throw hard shadow
   wedges away from the lantern — the fort is *visibly* what is hiding the hiders.
2. **Hiders in the dark.** Unlit hiders are drawn as a 30 %-alpha silhouette with a thin team-colour
   rim, so the spectator sees the dramatic irony the seekers do not. This is bound to the inherited
   `#btn-spoilers` toggle (paintbot's own control, kept verbatim), **default on**: the tension of
   hide-and-seek is watching someone walk past a cog you can see.
3. **Proximity heartbeat bar.** `#heartbar`: one bar per seeker, filling cold → burning in the
   seeker's colour, pulsing at 1 Hz (cool) up to 4 Hz (burning). Sourced from the keyframe `hb`
   array, so it is exactly what the seeker was told.
4. **Spotlight burst on a find.** On a `found` event: a one-frame white flash, a 240-frame-radius
   expanding ring at the hider's position, the beam that found it snapping to a hard white for 12
   frames, a `#bannerlane` banner (`FOUND — Moth-3 after 41.0 s, by Owl-2`), and a `#killfeed` line.
   The playhead holds for 0.4 s on the burst.
5. **Fort-building in timelapse.** Every `build` act is registered as a timelapse span in the
   inherited lull machinery (`skipLulls` / `lullSpans` / `#btn-skip` / `#ffwd-chip`): playback runs
   the 30 s build at **4×** with `#clock-caption` reading `BUILD — 4×` and `#ffwd-chip` lit, then
   drops back to 1× the moment the hunt starts. Crate motion leaves a fading 48 px ghost trail
   during the timelapse so a 7-second render still reads as construction. `#btn-skip` turns it off.
6. **Side-swap intermission card.** At the half boundary the playhead holds 2.0 s on `#intermission`
   over a dimmed board: `HALF 1 — Moth hid 128.0 s of 225.0 s (57 %)` / `SIDES SWAP` /
   `HALF 2 — Owl hides`, with both teams' plates and the same crate layout drawn as a small diagram
   so a viewer can see the reset is real.
7. **Scorebug** (`#scorebug`, always on): `▮ daveey · Moth 128.0s — 183.0s Owl · daveey-1 ▮`, the
   two colour chips, the leading team's plate brightened, plus `#actchip` (`H1 BUILD` / `H1 HUNT` /
   `H2 BUILD` / `H2 HUNT`) and `#clock-time` showing `MM:SS` of act time remaining over
   `turn 19/42`. **Real player names live here and only here** (plus the endcard and the feed);
   the board itself labels cogs `Moth-1`…`Owl-3`.
8. **Event feed** (`#killfeed`, plain language, last 6): `Moth-2 bolts C4 across the west opening`,
   `Owl-1 hears a push near (560,180)`, `Owl-3 pries C8 — 50 %`, `Moth-1 says "west screen"`.
   Order `note`/`say` strings surface here — this is where a spectator sees the LLM playing.
9. **Sound rings.** Every `sound` event draws an expanding ring at its jittered position, dashed for
   `step`, solid for `push`, thick and white for `break`, fading over 24 frames — the only thing
   visible in the dark other than the beams.
10. **Transport** (verbatim): play/pause, back one tick, +5 s, jump to end, loop, lull-skip,
    spoilers, the speed chips over `PlaybackSpeeds = [1,2,3,4,8,16]`, the scrubber with the
    `#momentum` graph re-purposed to plot **hiders remaining** across the whole match, `found` ticks
    marked on the scrub bar, the `#tick-clock` readout, the `#endcard`
    (`Owl wins 0.622 — 0.378 (hid 183.0 s to 128.0 s)`), and the `#mmwarn` digest-mismatch line.

**Art is real, not placeholder.** The floor is paintbot's painted `data/arena_floor.png` retinted to
cool concrete; walls use `client/art/walls/wall_h.jpg` / `wall_v.jpg` verbatim; cogs are paintbot's
`data/rig_real/` rig recoloured to Moth amber `#f2c14e` and Owl teal `#4ecdc4` with a lantern
housing sprite on the seeker rig; crates are authored painted wooden crates in three states
(`crate.png`, `crate_locked.png` with visible bolts, `crate_broken.png` with splintered planks),
generated by a committed script under `scripts/art/` the way paintbot generates its props. The
locker-room curtain plate is lantern's own. No solid-colour rectangles standing in for anything, no
TODO assets.

**Legible at 360 px** — the embedded featured-match iframe is ~360 px wide, so the composition is
checked at 360 px, not at desktop width. Paintbot's `--hudscale` (`clamp(0.5, boardW/760, 1.6)`) and
its `.tiny` class at `boardW <= 620` are inherited and do the heavy lifting. On top of that:
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }` so
player names never collapse to "…" (playbook gotcha); a `@media (max-width: 640px)` rule collapses
`#heartbar` to three 8 px dots, hides `#viewpanel` (minimap + zoom bar) and the speed-chip labels,
and reduces the feed to two lines under the board; `#actchip` and the two hidden-second clocks never
wrap; the intermission card's text is `font-size: clamp(11px, 3.4vw, 17px)`. A static test asserts
the `.plate-name` rule and the `640px` media block are present (§Tests).

---

## Packaging

- **Repo:** `Metta-AI/cogame-lantern`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `lantern`.
- **`compose.yaml`** — bullwhip's single-service shape (paintbot's two-image split does not survive
  the fork: the shared `tools/ci/docker_smoke.sh` runs the game and every player container from one
  image):

  ```yaml
  services:
    lantern:
      image: coworld-lantern:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — paintbot's/bullwhip's two-stage Nim build: `debian:bookworm-slim` + `nimby`
  0.1.26 pinned, `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the
  container's synced package tree, then two binaries —
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:lantern src/lantern.nim` and the
  same for `src/lantern_player.nim`. Run stage `debian:bookworm-slim` with `ca-certificates` and
  `libcurl4`, copying `/bin/lantern`, `/bin/lantern-player`, `./data`, `./client`.
  `CMD ["/bin/lantern"]`.
- **`Dockerfile.replay-viewer`** — paintbot's, with the CTF asset copies replaced by lantern's:
  `emscripten/emsdk:4.0.15`, nimby 0.1.27 (sha256-checked), `nim c -d:emscripten
  replay-viewer/lantern_replay.nim`, `tools/gen_wire_constants.nim > replay-viewer/dist/wire_constants.js`,
  the `chrome_common.js` / `static_replay.js` / `static_replay_worker.js` copies, the marker `sed`
  that splices `<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->` and `<!-- BROADCAST_CORE -->` into
  `index.html`, the art copies, and the same `test -f` / `grep -q` assertion tail (adjusted to
  lantern's file names, and extended with `grep -q 'coworld-replay' replay-viewer/dist/static_replay.js`).
- **`coworld_manifest_template.json`:**
  - `game.name` `lantern`; `episode_timeout_minutes` **20**; `game.runnable.image` `{{GAME_IMAGE}}`,
    `run` `["/bin/lantern"]`, `source_url`
    `https://github.com/Metta-AI/cogame-lantern/tree/main`; `game.owner` `daveey@softmax.com`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.config_schema`: `tokens`, `players` (6), `slots` (optional team pin), `seed`,
    **`num_agents`** (integer, default **6**), `prepTicks` (720), `huntTicks` (1800), `turnTicks`
    (120), `halves` (2), `turnBudgetSeconds` (13), `wallClockBudgetSeconds` (660),
    `playerConnectTimeoutSeconds` (90), `lanternRangePx` (420), `lanternConeBrads` (18),
    `visionBubblePx` (60), `crateCount` (10), `lockTicks` (24), `pryTicks` (72), `lockOnTicks` (12),
    `maxLocksPerHider` (3), `mapPath` (`"vault"`), `showPlayerLabels` (true), `gameOverTicks` (96).
  - `game.results_schema`: exactly the closed key set in §Server, with `reason` enum
    `["complete","deadline","fault"]` and `end_rule` enum
    `["full_time","wall_clock","sim_fault","host_error"]`.
  - `game.protocols`: **both `player` and `global`**, each `{"type": "text", "value": "…"}` —
    `player` describing the `register` frame, the `turn` frames and the `done` frame; `global`
    describing the `/global` spectator snapshot and the static replay bundle. Text form, not URIs
    (paintbot uses URIs; the playbook gotcha row requires text).
  - `game.docs`: `readme` = `{"type": "text", "value": "<the README body, inlined>"}` and `pages` =
    two entries — `{"id": "rules.md", "title": "Rules", "content": {"type": "text", "value":
    "<docs/RULES.md inlined>"}}` and `{"id": "protocol.md", "title": "Wire protocol", "content":
    {"type": "text", "value": "<docs/PROTOCOL.md inlined>"}}`. A manifest test asserts all three
    values are non-empty text.
  - `game.player[0]` = `{"id": "baseline", "name": "warden", "type": "player", "image":
    "{{PLAYER_IMAGE}}", "run": ["/bin/lantern-player"], "env": {"PLAYER_SCRIPTED": "warden"},
    "source_url": "https://github.com/Metta-AI/cogame-lantern/tree/main"}` — the bundled
    certification player, no LLM. `{{GAME_IMAGE}}` and `{{PLAYER_IMAGE}}` both resolve to
    `coworld-lantern`.
  - **Variants — `num_agents` is 6 in every one:**

    | id | name | `num_agents` | `prepTicks` | `huntTicks` | total ticks | turns | `turnBudgetSeconds` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|
    | `default` | Warehouse (2 teams × 3, two halves) | **6** | 720 | 1800 | 5040 | 42 | 13 | 660 |
    | `sprint` | Sprint (2 teams × 3, short halves) | **6** | 480 | 1080 | 3120 | 26 | 13 | 400 |

    Both variants seat six players and pin `slots` to
    `[{"team":"moth"},{"team":"owl"},{"team":"moth"},{"team":"owl"},{"team":"moth"},{"team":"owl"}]`.
    `sprint` exists for cheap ladder rounds; it changes only the act lengths, **never the seat
    count**.
  - **Certification fixture** (`certification`): `players` =
    `[{"player_id": "baseline"} × 6]`; `game_config` =
    `{"players": [{"name":"P1"},{"name":"P2"},{"name":"P3"},{"name":"P4"},{"name":"P5"},{"name":"P6"}],
    "slots": [ …the same six team pins… ], "num_agents": 6, "seed": 42, "prepTicks": 240,
    "huntTicks": 480, "turnTicks": 120, "halves": 2, "turnBudgetSeconds": 13,
    "wallClockBudgetSeconds": 180, "playerConnectTimeoutSeconds": 60, "mapPath": "vault"}` — 1440
    ticks, 12 turns, all six seats scripted, no LLM, wall clock ≈ 5 s.
- **Scaffold from `coworld-builder/templates/`** with `<slug>` = `lantern`, `<IMAGE>` =
  `coworld-lantern`, `<SEATS>` = **6**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/build_replay_viewer.sh` (**`chmod +x`** —
  `coworld build` hard-requires `os.X_OK`), `tools/ci/policies.json`. `SMOKE_REQUIRE_REPLAY_JSON`
  stays at its default `1`; `SMOKE_SEATS` is `6` and is an independent cross-check against
  `certification.game_config.num_agents`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/lantern-player"`, one image, env-switched):

  | name | env | role |
  |---|---|---|
  | `lantern-warren` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `lantern-owlnight` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `lantern-warden` | `PLAYER_SCRIPTED` = `warden` | filler |
  | `lantern-moth` | `PLAYER_SCRIPTED` = `moth` | filler |

- **Repo layout:** `src/lantern.nim`, `src/lantern_player.nim`, `src/lantern/` (`types.nim`,
  `arena.nim`, `crates.nim`, `sim.nim`, `rules.nim`, `control.nim`, `orders.nim`, `baselines.nim`,
  `llm.nim`, `state.nim`, `config.nim`, `roster.nim`, `events.nim`, `labels.nim`, `broadcast.nim`,
  `render.nim`, `replay.nim`, `server.nim`), `replay-viewer/` (`lantern_replay.nim`, `config.nims`,
  `static_replay.js`, `static_replay_worker.js`), `client/` (`replay_broadcast.html`,
  `chrome_common.js`, `broadcast_core.js`, `art/`), `data/` (`vault.mapspec.json`, art, `font.ttf`),
  `players/` is **not** used (the player is `src/lantern_player.nim`), `tests/` (+ `tests/support/`),
  `tools/`, `scripts/art/`, `docs/` (`RULES.md`, `PROTOCOL.md`, `plans/`), `AGENTS.md`, `README.md`,
  `nimby.lock`, `lantern.nimble`, `config.json`.

---

## Tests

CI is the only harness — the sandbox has no Docker, no Nim, no emsdk. The template `ci.yml` runs
**every `tests/*.nim` file individually, twice (debug and `-d:release`)**, so each test file is a
standalone program and shared helpers live in **`tests/support/helpers.nim`** (a subdirectory, so
the `tests/*.nim` glob never executes a helper module). No aggregator file.

1. **`tests/test_motion.nim`** — sim unit tests on movement: a cog accelerates to exactly `MaxSpeed`
   and no further; friction brings it to rest below `StopThreshold`; the wall slide keeps a cog
   inside the arena for 2000 ticks of input hammering every wall; cog–cog overlap resolves
   symmetrically (swapping slot indices mirrors the outcome); a crawling cog's top speed is exactly
   40 % and it emits no `step` sound.
2. **`tests/test_crates.nim`** — push/lock/pry: a hider pushes a loose crate at exactly 6 px/tick and
   a seeker at 4; a push into a wall, another crate or a cog moves nothing and reverts the pusher
   along that axis only; a lock takes exactly 24 ticks and is refused at `locks_used == 3`; a locked
   crate is immovable by both roles; a pry takes exactly 72 ticks and emits a 900 px ring; any
   progress resets on movement; a crawling cog cannot push.
3. **`tests/test_vision.nim`** — the lantern: a hider dead centre at 419 px is lit and at 421 px is
   not; at ±18 brads lit, ±19 not; a non-broken crate occludes and a broken one does not; the bubble
   sees behind you at 59 px; team sharing puts one seeker's lit hider in all three views; lanterns
   are off for every build tick. Plus the **no-trigonometry source guard**: grep `src/lantern/*.nim`
   for `sin|cos|tan|atan|arctan|exp|ln(|pow|fmod|hypot|sqrt` and for `float`/`float64` inside the
   step path, and the build scripts for `-ffast-math`; any hit fails.
4. **`tests/test_rules.nim`** — detection and the clock: `lockOnTicks` fires at exactly 12
   consecutive lit ticks and an 11-tick streak broken for one tick does not; a touch tag at 24 px
   fires instantly and at 25 px does not; a found hider stops accruing and is inert; the phase table
   maps ticks to (half, act, turn) exactly at every boundary; the half reset restores all ten crates,
   all six positions, `locks_used` and the pen door; `all_found` ends the act and the denominator
   stays 3 × `huntTicks`.
5. **`tests/test_scoring.nim`** — the formula and its sign: the worked example above yields
   `[0.378, 0.622]`; `score(Moth) + score(Owl) == 1.0` over 200 randomised tick splits; a perfect
   shutout in one half and a perfect hide in the other gives 1.0/0.0; equal fractions give 0.5/0.5
   with `winner: null`; a `deadline` cut mid-half-2 normalises by `hunt_ticks_played`; a
   `deadline` before half 2's hunt gives 0.5 to every seat.
6. **`tests/test_determinism.nim`** (**the gate**) — same seed + same control bytes ⇒ identical
   digest at every keyframe over a full 5040-tick match, run twice in one process and once in a
   fresh instance; a one-bit change in any control byte changes the final digest; a committed golden
   fixture `tests/fixtures/golden_digests.json` pins the digests for seed 42 over 1440 ticks, so any
   rule change shows up in the diff.
7. **`tests/test_baselines.nim`** — **the bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random world states × both baselines × both roles, the emitted order
   validates against the schema — `intent` legal for that role, `target` finite and inside the map,
   `crate` a real id legal for that intent or null, `aim` legal, `note` ≤ 140 runes, `say` ≤ 32
   runes — **and** the compiled control bytes are in range (`move` −100…100, `aim_turn` ±5, action
   bits ≤ 0b111) for every cog on every tick of the turn. Plus: a `warden` vs `moth` match at seed 42
   completes and `warden` wins (the baselines are ordered, so the ladder has a spread), and no
   baseline ever emits a lock beyond its third.
8. **`tests/test_orders.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   unknown enums, a seeker sending a hider intent, `target` as numeric strings, `target` out of
   bounds, `crate` as `4` and as `"c4"` and as `"C42"`, missing fields, a 400-character `note`, and a
   `say` whose 32nd and 33rd runes are a 4-byte emoji — the truncation must land on the **rune**
   boundary and the result must still round-trip `%*`/`$`/`parseJson` and encode as valid UTF-8.
   Two consecutive failures ⇒ the `warden` order plus a `fallback` event; a timeout on attempt 1 ⇒
   exactly one retry.
9. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: all open seats' calls go
   out in **one parallel batch** (the fake records in-flight windows and the test asserts they
   intersect); build turns batch exactly 3 requests and hunt turns exactly 6; the per-turn budget is
   enforced with a hung client; the budget guard switches to scripted and the episode still ends
   `complete/full_time`; the 660 s stop yields `deadline/wall_clock`; a raised sim fault yields
   `fault/sim_fault` with 0.5 for every seat and a partial replay; a seat that never registers plays
   `warden` and is reported to `COGAME_PLAYER_FAILURE_URI`; a mid-match disconnect degrades to
   `warden` and revives on reconnect.
10. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full
    scripted-vs-scripted episode (cert-fixture length) runs over the real sim, writes `results.json`
    and the replay; the replay is parsed **strictly**
    (`parseJson(readFile(path).validateUtf8 == -1 ...)` — the bytes are asserted valid UTF-8 first,
    and the fixture forces a non-ASCII `say` into the event stream so the UTF-8 path is real);
    `protocol == "lantern.replay.v1"`; `controls_b64` decodes to exactly `tick_count × 24` bytes;
    every documented top-level key is present and `map`, `names`, `config`, `phases`, `keyframes`,
    `events`, `results` are non-empty; `results.reason` is in the legal enum; the event stream
    contains at least one `order` per active seat per turn, one `crate_lock`, one `found` and one
    `half_end`; and re-deriving from `seed` + `map` + `controls_b64` reproduces **every keyframe
    digest**.
11. **`tests/test_server.nim`** — the websocket contract: the `register` frame is accepted, a bad
    token 403s, a duplicate connection 409s, `/healthz` answers, `/global` streams a snapshot,
    artifact writes land on `file://` URIs, `COGAME_EVENTS_URI`/`COGAME_METRICS_URI` reject non-file
    schemes loudly, and replay mode serves `/replay-data` and `/client/replay`.
12. **`tests/test_manifest.nim`** — `num_agents == 6` in **every** variant *and* in
    `certification.game_config`; `len(certification.players) == 6` and
    `len(certification.game_config.players) == 6`; `results_schema` keys equal the keys
    `src/lantern/server.nim`'s results builder emits; `game.protocols` carries **both** `player` and
    `global`; `game.docs.readme` and both pages are non-empty **text**; `replay_viewer.bundle ==
    "static-replay-viewer"`; `episode_timeout_minutes == 20`; every variant's
    `wallClockBudgetSeconds ≤ 0.6 × 1200`; the compose image name matches the `<IMAGE>` used in the
    scaffold.
13. **`tests/test_map.nim`** — `data/vault.mapspec.json` loads; the geometry is invariant under 180°
    rotation about (617, 329); every spawn, nook anchor, `far_corner` and crate box is on free floor
    and non-overlapping; the pen door opens and closes with the act; every `sweep_lanes` waypoint is
    reachable from the pen by the unstick-augmented steering within 40 s.
14. **`tests/test_viewer.nim`** — **the viewer smoke** (no browser): the node harness forked from
    paintbot's `tools/wasm_replay_smoke.cjs` loads `replay-viewer/dist/lantern_replay.js` with a
    recorded replay, advances to the end, and asserts the tick total, the final digest and that
    seek-to-mid / seek-to-end land exactly; malformed inputs (bad `protocol`, bad base64 length,
    truncated JSON, `tick_count`/payload mismatch) are all rejected with a message rather than a
    crash. Plus static assertions over `client/replay_broadcast.html` and
    `replay-viewer/static_replay.js`: the `coworld-replay` bridge **including `tell("ready")`** is
    present; the inherited chrome ids listed in §Viewer are all still there; `#heartbar`,
    `#hidebug`, `#actchip`, `#intermission` and `#burst` exist; `.plate-name { flex: 1 1 auto;
    min-width: 3.2em` and a `@media (max-width: 640px)` block are present. (Marked
    `NIM_TESTS_RELEASE_ONLY` if the debug wasm harness proves slow.)
15. **`tests/test_startup.nim`** — `/bin/lantern` exits 2 with a clean one-line message and no
    traceback when `COGAME_CONFIG_URI` is missing or invalid; `--help` works; the player binary exits
    0 on an unreachable `COWORLD_PLAYER_WS_URL` after its bounded connect retry.
16. **`tests/test_perf.nim`** — 5040 ticks with three lanterns complete in under 30 s in a release
    build.

CI additionally runs `tools/ci/docker_smoke.sh` (a raw-Docker episode from the certification
fixture, `SMOKE_SEATS=6` cross-checked against the manifest, replay required to parse as JSON) with
`docker-smoke` depending on the image build in the same run so a stale binary can never be smoked,
and `tools/build_replay_viewer.sh` (the bundle builds, contains `index.html` and a non-empty
`.wasm`, and is uploaded as the `static-replay-viewer` artifact).

---

## Out of scope (v1)

- **Verticality.** No ramps, no climbing, no z-axis, no jumping onto crates. The idea's "seekers ramp
  and climb" is realised as prying (§The game); a 2.5-D layer would need a new renderer and a new
  collision model.
- **Procedural terrain.** One authored map, `vault`. Paintbot's generator, validators, curated pool,
  size/symmetry/endzone knobs and map editor are all dropped. Map variety is the first v0.2 feature
  once the ladder is healthy, and it must keep the both-halves-identical property.
- **An RL continuous-vector policy interface.** The idea's stated interface is reinterpreted as the
  LLM-order + deterministic-control-layer stack (an inherited pin: both champions must be
  `PLAYER_PROMPT`). Exposing the per-tick `(move_x, move_y, aim_turn, action)` vector to external
  policies over the websocket is a v0.2 protocol addition; the control layer and the quantised
  action log are already shaped for it.
- **Everything CTF that is not hide-and-seek:** guns, hitscan, aim jitter, grenades, the barrage,
  med kits, shields, the plasma arc, paint puddles, spray cans, lives/hit points/respawn, perks,
  handicaps, achievements, the four-team mode and shouts. None of them survive the fork.
- **Inter-seat chat.** Teammates coordinate only through the world (where they went, what they
  built) and through their shared lit sets. `note` and `say` are one-way to the spectator feed and
  are never delivered to another seat, this half or any other.
- **Persistent memory across episodes or halves.** A seat carries nothing from half 1 into half 2
  except what its prompt already said; there are no notes, no scouting reports, no cross-episode
  state.
- **More than two halves, overtime, sudden death, or mercy rules.** Both halves always play in full
  (an `all_found` hunt act ends early but the denominator does not change).
- **Crate variety.** One crate type, one size, three states. No barrels, no doors, no ramps, no
  destructible walls, no crate stacking.
- **Audio, 3-D, camera cuts other than the find hold and the intermission card, and any downloaded
  art asset** (the bundle stays hermetic).
- **A 4-seat or 8-seat variant, or asymmetric team sizes** (2 hiders vs 4 seekers). Any of those
  changes `num_agents`, which the seat-count pin forbids in v1.
