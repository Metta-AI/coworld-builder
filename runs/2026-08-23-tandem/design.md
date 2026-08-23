# tandem — design note (2026-08-23, paintbot lineage)

`Metta-AI/cogame-tandem` is a two-seat, fully cooperative carrying game: two cogs are rigidly
gripped to the two handles of one couch and must walk it through a procedurally generated
warehouse obstacle course, room by room, doorway by doorway, with no communication channel of any
kind. It is forked from **`Metta-AI/coworld-ctf`** (paintbot), read at its read-only mount
`/workspace/starters/coworld-ctf`. **Every convention there holds here unless this note says
otherwise.**

Paintbot is the right starter by game shape: this is a real-time 24 Hz tick loop with rules
written fresh for this coworld (nothing external pre-exists to port, so not `cogame-moba`; the
game logic is native Nim, so not `cogame-factorio`), RL-vector policies, and it needs exactly what
paintbot ships — a wall-clock-paced game loop with a per-tick replay + hash chain
(`src/ctf/server.nim`, `src/ctf/replays.nim`), a static wasm replay viewer that re-derives every
frame in the browser (`replay-viewer/`), integer fixed-point body physics with wall contacts
(`src/ctf/sim.nim`), and broadcast chrome with a scorebug, feed, scrubber and endcard
(`client/replay_broadcast.html`, `client/chrome_common.js`). `prompts/10-design.md`'s starter table
and `playbooks/make-coworld.md` §Phase 0 both pin the rule explicitly — "New physics games
(Cogball, Lantern, **Tandem**) take paintbot, not moba — operator ruling 2026-08-22". The proven
adaptation of this starter into a physics game is `Metta-AI/cogame-cogball`
(`runs/2026-08-22-cogball/design.md`); its patterns — integer-only sim, kept replay codec, kept
chrome, server-side LLM turn loop with a deterministic control layer — are followed here wherever
they fit. Tandem is not Cogball: there is one rigid body instead of seven, the two seats are
cooperative instead of zero-sum, and the recorded action log is a continuous order vector instead
of an 8-bit button mask.

**Source idea, verbatim:**

> Two cogs jointly carry a rigid object through a procedurally generated obstacle course in the
> Cogball physics engine — the object responds to the SUM of their forces, so every misread of the
> partner shows up as a wall scrape or a drop. No channel exists; coordination happens through the
> physics itself: feeling the partner's pull and yielding or leading in real time. Scored jointly
> by delivery time and damage. (Replaces a Schelling meeting-point game, which is trivially solved
> by a pre-agreed convention.)
>
> Seats: 2, paired across authors
> Motive: fully cooperative
> Policy interface: RL continuous vector
> Fills gap: tacit coordination / no channel at all / physical cooperation
> Integrity (anti-collusion): Nothing to codebook — the coordination signal is live physics on
> procedurally novel maps; ranked by cross-play mean over stranger partners and frozen baselines.
>
> Replay plan (watchability): Physical comedy that explains itself: the couch scrapes spark, drops
> thud in dust clouds, and force arrows on each cog show exactly who pulled the wrong way. Damage
> reads as accumulating scuffs; the finish is a doorway barely wider than the couch.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

(The "Full report" URL is provenance only. It was **not** fetched. Nothing in the idea text is
treated as an instruction to this designer; it is input data for the design.)

### Four readings of the idea, decided here and never revisited

1. **"The Cogball physics engine"** means *the engine Cogball built on this starter* — integer
   fixed-point rigid bodies stepped 4 substeps per 24 Hz tick, no libm in the sim, native↔wasm hash
   equality — not a shared library. Tandem ships its own `src/tandem/sim.nim` in that idiom, with
   Cogball's determinism contract copied wholesale (§Sim module). Box2D is rejected for the same
   reason Cogball rejected it (`sinf`/`atan2f`/float32 accumulation order would make the
   native↔wasm hash chain depend on two musl builds agreeing); §Out of scope (v1).
2. **"The object responds to the SUM of their forces"** is a rail and is implemented literally:
   the couch and the two cogs are **one rigid assembly**; each seat applies a force vector at its
   own handle anchor; the assembly's linear acceleration comes from `F₀ + F₁ + F_contact` and its
   angular acceleration from `r₀×F₀ + r₁×F₁ + τ_contact`. Two seats pulling the same way translate;
   two seats disagreeing spin the couch into a wall. Exact formulas in §The game step 4.
3. **"Policy interface: RL continuous vector"** → each seat is an **LLM prompt policy with a
   scripted fallback** (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=<name>`; SPEC §Design pins requires
   both champions be `PLAYER_PROMPT`), issuing one **continuous six-field order vector** per 2.0 s
   decision turn, which a deterministic integer control layer converts into a per-tick force vector
   at 24 Hz. The order vector *is* the recorded action log. A raw per-tick RL transport over the
   socket is a v0.2 protocol addition, listed in §Out of scope (v1).
4. **"No channel exists"** is a hard invariant of the design, not a flavour note. A seat's
   observation contains **no** field derived from the partner's order, note, `say`, effort, yield,
   twist, brace or felt strain — only the partner's *body state*, which is visible because both cogs
   are gripping the same object. `say` exists solely for the spectator feed and is never delivered
   to the other seat. `tests/test_no_channel.nim` asserts it against the composed LLM user message
   (§Tests 9).

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and where each is satisfied

| Pin | How tandem satisfies it |
|---|---|
| Starter by game shape | **`Metta-AI/coworld-ctf` (paintbot)** — a real-time 24 Hz loop with new rules and RL-vector policies. The rigid-body course replaces the arena rules; the loop, protocol, replay codec, viewer and CI wiring stay. (§Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-tandem`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions: `tandem-anchor`, `tandem-feather`) vs `PLAYER_SCRIPTED=porter` / `PLAYER_SCRIPTED=mule` (both fillers). One image `coworld-tandem`, one player entrypoint `/bin/tandem-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; ctf's `tools/build_replay_viewer.sh` kept; the **same** `src/tandem/sim.nim` compiles into `replay-viewer/tandem_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | `client/chrome_common.js` copied **byte-for-byte**; `client/replay_broadcast.html` is ctf's page with a game block **appended**; walls use ctf's shipped `client/art/walls/wall_h.jpg`/`wall_v.jpg`; the cogs are ctf's shipped `data/rig_real/blue` and `data/rig_real/red` rigs; couch/floor/scuffs baked with pixie. No placeholders. (§Viewer) |
| Two name spaces | In-game everything is `Cobalt` / `Rust`; real policy names appear only in the replay config JSON, the DOM scorebug/roster/endcard and `results.names`. Test-enforced. (§Server, §Viewer, §Tests) |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | ≈300 s expected / 490 s absolute worst case against the 720 s budget; a 660 s engine hard stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 2** in variant `default`, variant `sprint`, and `certification.game_config`; `<SEATS>` = **2** in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**Tandem is two cogs carrying one couch through a procedurally generated warehouse.** The couch and
the two cogs form a single rigid assembly. Each cog can push with its own force vector; the
assembly obeys the sum. There is no way to say anything. The only signal about what your partner
intends is what you feel through the handle — and the only way to get a 2.20 m couch through a
1.05 m doorway is for one of you to lead and the other to yield, decided live, without a word.

### Seats

**`num_agents` = 2. One seat = one cog.** Seat 0 is **Cobalt** (blue rig), gripping the **fore**
handle at body-local `x = +1.40 m`. Seat 1 is **Rust** (red rig), gripping the **aft** handle at
`x = −1.40 m`. The idea pins two seats and this note fixes it at exactly two everywhere — variants,
cert fixture and `SMOKE_SEATS`. Two is also what makes the wall-clock budget comfortable: two
parallel LLM calls per decision turn, 100 calls per episode (§Decisions). The blue/red liveries are
chosen so the cogs are ctf's already-shipped real rig art with no recolouring work.

The seats are **not symmetric in the world** (fore vs aft handle) but they *are* symmetric in
rules, scoring and observation shape, so a policy is never advantaged by its slot. Which handle a
seat holds is stated in its own observation (`"you": {"handle": "fore"}`).

### World, units, and why they are integers

The whole sim runs in **integers**, for exactly Cogball's reason: replays are re-simulated by the
**emscripten/wasm32** build of the same Nim module that the **native amd64** server ran, and their
per-tick `gameHash` chain must match bit-for-bit. Integers make that true by construction instead
of by an argument about libm. `src/tandem/{sim,course,control,trig}.nim` contain **no floating
point at all** (grep-enforced in CI, §Tests 2d).

| Quantity | Unit | Type |
|---|---|---|
| Position | micrometres (µm) | `int32` |
| Linear velocity | µm per tick | `int32` |
| Angle (`headingQ`) | 1/16 brad, 0..4095 (256 brads = 1 turn, 0 = +x, ccw on screen — ctf's convention) | `int32` |
| Angular velocity (`spin`) | 1/16 brad per tick | `int32` |
| Force | millinewtons (mN) | `int32` |
| Torque | millinewton-metres (mN·m) | `int32` (accumulated in `int64`) |
| Mass | grams | `int32` const |
| Moment of inertia | milli-kg·m² | `int32` const |
| Damage | scuff points, 0..1000 | `int32` |

World box: `x ∈ [0, 44 400 000] µm`, `y ∈ [0, 25 200 000] µm` (44.4 m × 25.2 m), origin top-left,
y down (ctf's screen convention). Map render scale **1 map pixel = 40 000 µm** → `MapWidth = 1110`,
`MapHeight = 630` — a 1.762:1 board, the same size class as ctf's arena, so every viewer buffer
budget in `replay-viewer/ctf_replay.nim` (`predictedViewerRenderBytes`,
`MaxSupersampledMapPixels`, `WasmViewerBudgetBytes`) is already satisfied and is kept unchanged.

**View coordinates** — the only coordinates a policy ever sees or sends — are **metres, origin at
the world centre, y up**: `X = (x_µm − 22 200 000) / 1 000 000`, `Y = (12 600 000 − y_µm) / 1 000 000`.
So the floor is `X ∈ [−22.2, +22.2]`, `Y ∈ [−12.6, +12.6]`, and a positive `Y` in an order means
"push toward the top of the screen". Angles reported to policies are **degrees ccw from +X**,
rounded to 1°.

### The course (procedural generation, exact, deterministic from `seed`)

The floor is a **9 × 5 grid of 4.8 m cells** inside a 0.6 m outer wall ring: the interior spans
`x ∈ [600 000, 43 800 000]`, `y ∈ [600 000, 24 600 000] µm`; cell `(c, r)`, `c ∈ 0..8`, `r ∈ 0..4`,
spans `x ∈ [600 000 + 4 800 000·c, 600 000 + 4 800 000·(c+1)]` and likewise in y. Internal walls are
**0.30 m thick**, centred on the grid lines.

`generateCourse(seed: int64): Course` uses one dedicated `std/random` `Rand` stream seeded from
`config.seed`, integer draws only, in exactly this order:

1. **Route.** `r0 = rand(0..4)` (start cell `(0, r0)`), `r1 = rand(0..4)` (goal cell `(8, r1)`).
   A self-avoiding walk starts at `(0, r0)` and steps **east / north / south with weights 60 / 20 /
   20** (never west), rejecting any step that leaves the grid or revisits a cell; on a dead end it
   backtracks one cell and re-draws with the taken direction excluded. The walk ends when it enters
   `(8, r1)`. If the resulting route length is outside `9 ≤ len ≤ 15`, the whole walk is re-run;
   after 64 failed attempts the generator falls back to the monotone path
   `(0,r0) → (1,r0) → … → (8,r0)` with `r1 := r0` (deterministic, never random).
2. **Doorways.** For each of the `len − 1` consecutive route pairs `k`, a gap is punched through
   the shared 0.30 m wall: width `w_k` drawn uniformly from
   `{1 050 000, 1 200 000, 1 400 000, 1 700 000, 2 200 000} µm` and centre offset `o_k` drawn
   uniformly from `[−1 200 000, +1 200 000] µm`, then clamped so the gap's edges stay ≥ 200 000 µm
   inside the shared face. **The last doorway (into the goal cell) is forced to `w = 1 050 000 µm`
   and `o = 0`** — the idea's "finish is a doorway barely wider than the couch" (couch width
   900 000 µm; clearance 75 mm per side).
3. **Blocks.** Every cell **not** on the route becomes one solid `WallRect` filling its 4.8 m ×
   4.8 m extent. Every internal boundary between two route cells that are **not** consecutive on
   the route becomes one full 0.30 m `WallRect`; every consecutive boundary becomes **two stub
   `WallRect`s** either side of the doorway gap. The outer ring is four `WallRect`s.
4. **Pillars.** For each route cell that is neither the start nor the goal, with probability 45 %
   (`rand(0..99) < 45`), one **0.8 m × 0.8 m** static `WallRect` is placed at the cell centre offset
   by `(±1 400 000, ±1 400 000) µm`, quadrant drawn from `rand(0..3)`. The placement is **rejected
   and the pillar skipped** if the square comes within 1 300 000 µm of the segment joining the
   cell's two doorway centres — so every cell always retains a ≥ 1.30 m clear through-line, wider
   than the 0.90 m couch.
5. **Route polyline and par.** `routePts` = start-cell centre, then each doorway centre, then each
   intermediate cell centre in route order, then the goal-pad centre (cell centres and doorway
   centres interleaved in traversal order). `routeLen` = the polyline length in µm.
   `parTicks = (routeLen div 1000) * 24 div 1600 + 36 * narrowDoors`, where `narrowDoors` is the
   count of doorways with `w < 1 400 000` — i.e. a reference carry at 1.6 m/s plus 1.5 s of fiddling
   per tight door. Typical: 12 route cells → `routeLen ≈ 53 m` → `parTicks ≈ 940` (39 s).
6. **Goal pad.** The goal cell's interior rectangle, inset 100 000 µm on every side.
7. **Digest.** `courseDigest: uint32` = a FNV-1a over the serialized `Course` (route cells, doorway
   widths/offsets, wall rects, pillars, `parTicks`). It is mixed into `gameHash` every tick.

**Seed handling.** `config.seed` comes from the platform (ctf's `src/ctf.nim` randomises it when
unpinned; kept verbatim). The **fully expanded `Course` object is written into the replay's config
JSON** as well as the seed — the viewer reads the recorded course and never regenerates it, so a
future generator change can never desynchronise an old replay. `tests/test_course.nim` asserts
`generateCourse(recorded.seed) == recorded.course` for the committed fixtures, which keeps the two
paths honest.

### Bodies

One rigid assembly, seven collision discs, one pose:

| Part | Local offsets (body frame, metres) | Radius | Mass |
|---|---|---|---|
| Couch hull discs ×5 | `x ∈ {−0.65, −0.325, 0, +0.325, +0.65}`, `y = 0` | 0.45 m | 12 000 g each |
| Cog discs ×2 | `x = +1.40` (Cobalt, fore), `x = −1.40` (Rust, aft) | 0.30 m | 30 000 g each |

Couch overall footprint: 2.20 m × 0.90 m with rounded ends (a capsule). Assembly overall length
3.40 m. `TotalMassGrams = 120 000`. `InertiaMilliKgM2 = 139 000` (139 kg·m² — the sum
`Σ mᵢrᵢ² + ½mᵢrᵢ²` over the seven discs about the assembly centre, which is the couch centre by
symmetry; `tests/test_physics.nim` re-derives it from the mass table and asserts the constant).

The assembly's state is exactly: `pos` (µm, the couch centre), `vel` (µm/tick), `headingQ`
(1/16 brad), `spin` (1/16 brad per tick), `damage` (0..1000), `slip[2]`, `lastStrain[2]` (mN vector
per seat), `phase`, `bestProgressPermille`, plus the two `activeOrder[seat]` quantised orders.
**Cogs cannot let go, walk around, or change grip in v1** — the grip is rigid and the compliance
knob is `yield` (§Decisions). The articulated alternative is §Out of scope (v1).

### Time

`TargetFps = ReplayFps = 24` — **kept verbatim from ctf** (`src/ctf/sim_types.nim:294,353`),
because every speed-coupled layer (`PlaybackSpeeds`, the lull scan, the momentum series,
`tickTime`, the transport bar) is keyed to it. Each tick integrates **4 substeps of 1/96 s**.

A run is at most **`maxTicks = 2400` ticks = 100 s**, divided into **50 decision turns of
`turnTicks = 48` ticks (2.0 s)**. At the assembly's 2.5 m/s terminal speed a turn covers ≤ 5 m —
about one room — which is the right granularity for "head for that doorway" while leaving the
real-time yielding to the control layer's per-tick reflex.

### Resolution order (exact, every tick `t`, no exceptions)

1. **Turn boundary.** If `t mod 48 == 0` and `phase ∈ {Carrying, Regrip}`: the order collected for
   turn `t div 48` becomes each seat's `activeOrder[seat]` (§Server), quantised to integers on
   parse. The server writes one **`order` chat record** per seat into the replay. `activeOrder` **is
   mixed into `gameHash`** — unlike Cogball's directives, because here the order *is* the action
   log and the viewer must prove it applied the same one.
2. **Regrip gate.** If `phase == Regrip` and `t < regripUntil`: both seat forces are zero, `vel` and
   `spin` are held at 0, and steps 3–6 are skipped (the couch is on the floor). Steps 7–10 still
   run. At `t == regripUntil` the cogs re-attach at their handle anchors in the couch's current
   pose, `slip[0] = slip[1] = 0`, `lastStrain = 0`, `phase = Carrying`, and a `regrip` event is
   emitted.
3. **Control compile**, seat order 0 then 1. `control.seatForce(sim, seat)` is a pure integer
   function of `(assembly state, activeOrder[seat], lastStrain[seat], course)` returning
   `F_seat: (int32, int32)` mN and `gripLimit_seat: int32` mN (§Decisions "The control layer").
   **This is inside the determinism boundary** — the viewer runs this same code.
4. **Four substeps** (`dtSub = 1/96 s`), each substep in this exact order:
   1. **Contacts.** For each of the 7 discs in index order (hull 0..4, then Cobalt, then Rust),
      against each `WallRect` registered in the disc's current grid cell or its 8 neighbours
      (broadphase built once at course generation), compute the penetration `δ` and outward normal
      `n̂` of the closest-point test (disc centre vs axis-aligned rectangle; `δ = radius − dist`,
      skipped when `δ ≤ 0`). Then, with `v_c` = the assembly velocity at the contact point
      (`v + ω × r_c`), `v_n = v_c · n̂` and `v_t = v_c − v_n·n̂`:
      - `Fn_mN = 200 · δ_µm + 29 · max(0, −v_n_µmPerTick)`, clamped to `≥ 0` (contacts push, never
        stick) and to `≤ 40 000 000` mN;
      - `Ft_mN = −min(354 · Fn_mN div 1024, |v_t| · 200) · û(v_t)` (Coulomb µ = 0.346 with a viscous
        cap that prevents sign-flip chatter at rest);
      - accumulate `F_contact += Fn·n̂ + Ft` and `τ_contact += r_c × (Fn·n̂ + Ft)` (µm × mN,
        converted to mN·m by `div 1 000 000`, in `int64`);
      - record `(disc, δ, −v_n, |v_t|)` into this tick's contact log for damage and FX.
   2. **Sum of forces (the rule the idea names).**
      `F = F₀ + F₁ + F_contact`; `τ = (r₀ × F₀ + r₁ × F₁) div 1 000 000 + τ_contact`, where
      `r₀ = +1.40 m`, `r₁ = −1.40 m` rotated into world by `headingQ`.
   3. **Velocity (semi-implicit Euler).**
      `Δv_µmPerTick = (int64(F_mN) * 1_000_000) div (TotalMassGrams * 96 * 24)`; `v += Δv`;
      then linear drag `v -= (v * 171) div 4096` (c_lin = 4.0 s⁻¹ → 2.5 m/s terminal at both seats'
      full 600 N);
      `Δspin = (int64(τ_mNm) * 28_294) div (int64(InertiaMilliKgM2) * 100_000)`; `spin += Δspin`;
      then angular drag `spin -= (spin * 341) div 4096` (c_ang = 8.0 s⁻¹).
      Clamp `|v| ≤ 145 833` µm/tick (3.5 m/s) and `|spin| ≤ 68` (2.5 rad/s).
   4. **Pose.** `pos += v div 4`; `headingQ = (headingQ + spin div 4 + 4096) mod 4096`.
   5. **Felt strain.** For each seat, the anchor velocity `v_i = v + ω × r_i` is evaluated before
      and after this substep; `a_i = (v_i_after − v_i_before) · 96` (µm/tick per second) and the
      handle force is `H_i = m_cog · a_i − F_i` in mN — **the force the cog's hand is carrying**.
      The four substeps' `H_i` are averaged into `lastStrain[i]` at the end of the tick. This is the
      entire coordination channel: `H_i` contains the partner's force by construction, because `a_i`
      depends on `F₀ + F₁`.
5. **Damage**, once per tick, over the tick's contact log in disc index order. **Cog discs damage
   nothing** (bruised cogs, unscuffed couch). For each *hull* disc:
   - **Impact** — if the disc was not in contact last tick and its peak approach speed this tick
     exceeded 250 mm/s: `dmg = clamp(((approach_mm_s − 250) * 40) div 1000, 0, 200)`; emit
     `impact` when `dmg ≥ 8`.
   - **Scrape** — if the disc stayed in contact with tangential slide > 50 mm/s:
     `dmg = clamp(slide_mm_s div 800, 1, 4)` per tick; emit `scrape`, throttled to at most one event
     per disc per 6 ticks.
   `damage = min(1000, damage + Σdmg)`. The seat whose handle is nearer the damaging disc gets the
   points added to its `blame[seat]` meter — **a spectator meter only; it is not in the score**
   (§Scoring).
6. **Grip and drops**, seat order 0 then 1. `strain = |lastStrain[i]|` (integer `isqrt`).
   `slip[i] = max(0, slip[i] + max(0, (strain − gripLimit_i) div 100_000) − 4)`.
   If `slip[i] ≥ 240` → **drop**: emit `drop` (seat, strain, pos, speed);
   `damage += 60 + clamp(|v|_mm_s div 60, 0, 40)`; `vel = 0`; `spin = 0`; `phase = Regrip`;
   `regripUntil = t + 48` (2.0 s); `slip[0] = slip[1] = 0`; `drops += 1`. Either seat's slip drops
   the couch — it takes two to hold it.
7. **Progress and delivery.** Project `pos` onto `routePts`: find the segment minimising the
   perpendicular distance (ties by lowest index), take the clamped arc length, and
   `bestProgressPermille = max(bestProgressPermille, 1000 · arc div routeLen)`. Emit a `doorway`
   event the first time all five hull-disc centres are past a doorway plane. If all five hull-disc
   centres are inside the goal pad → `phase = Delivered`, `deliveryTick = t`,
   `bestProgressPermille = 1000`, emit `delivered`.
8. **Stats.** `contactTicks`, `scrapeTicks`, `impacts`, `strainPeak[seat]`, `forceIntegral[seat]`,
   `yieldTicks[seat]` (ticks where the seat's yield term exceeded its drive term) — all spectator
   meters.
9. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's per-tick hash chain,
   unchanged. `gameHash` mixes `tick`, `phase`, `pos`, `vel`, `headingQ`, `spin`, `damage`,
   `slip[]`, `lastStrain[]`, `bestProgressPermille`, `deliveryTick`, both quantised `activeOrder`s
   and `courseDigest`. It never mixes FX, notes, `say`, feed text or policy labels.
10. **End checks**, in this order: `Delivered` → end `complete` / `delivered`; `damage ≥ 1000` →
    end `complete` / `wrecked`; wall-clock stop tripped → end `deadline` / `wall_clock`;
    `t + 1 ≥ maxTicks` → end `complete` / `out_of_time`; an invariant guard failure (a disc outside
    the world box, `|v|` or `|spin|` above the clamp, `damage` negative, `headingQ` outside 0..4095)
    → end `fault` / `sim_fault`.

There is **no rescue rule**. A pair that wedges the couch across a doorway and cannot free it burns
the clock and ends `out_of_time` with partial credit — that is a legible, correctly-scored failure,
not a stalemate that needs a teleport (Cogball's neutral drop existed because a 0–0 soccer match
carries no information; a jammed couch carries plenty).

### Scoring, sign, and what the league ranks by

The game is **fully cooperative**: both seats receive **the identical score**, computed once.

```
par        = course.parTicks                              (integer, from the generator)
t          = deliveryTick if delivered else finalTick     (ticks used)
dmg        = clamp(damage, 0, 1000)
cond       = (1000 - dmg) / 1000                          in [0, 1]   -- couch condition
speed      = clamp(2 - t / par, 0, 1)                     in [0, 1]   -- 1.0 at par, 0 at 2x par
progress   = bestProgressPermille / 1000                  in [0, 1]

delivered:      score = 0.30 + 0.35 * speed + 0.35 * cond            in [0.30, 1.00]
not delivered:  score = 0.25 * progress * cond                       in [0.00, 0.25)

results.scores = [score, score]
results.win    = [delivered, delivered]
```

**Higher is better.** The two terms are exactly the idea's "scored jointly by delivery time and
damage", weighted equally, over a 0.30 delivery floor so that **any** delivery beats **every**
non-delivery. A wrecked couch (`dmg = 1000`) scores 0.000 — destroying the furniture is the one
outcome worth nothing. `score` is emitted as a double rounded to 6 decimal places, computed once and
copied into both slots so the two numbers are bit-identical. A `fault` scores the same formula
against the state at the fault tick, with no special case: `reason: "fault"` is the flag the league
uses to discard the episode, so the score need not also punish.

Worked examples:

| Outcome | `t` | `par` | `dmg` | `progress` | score |
|---|---|---|---|---|---|
| Textbook: delivered at par, unscratched | 940 | 940 | 0 | 1.00 | **1.000** |
| Good run: delivered a bit slow, some scuffs | 986 | 940 | 214 | 1.00 | **0.908** |
| Ugly delivery: 1.9× par, one drop, heavy scuffing | 1786 | 940 | 600 | 1.00 | **0.475** |
| Delivered past 2× par, nearly wrecked | 2100 | 940 | 900 | 1.00 | **0.335** |
| Jammed in the last doorway, out of time | 2400 | 940 | 380 | 0.86 | **0.133** |
| Wrecked the couch two rooms in | 620 | 940 | 1000 | 0.31 | **0.000** |

**What the league ranks by: the seat's mean `results.scores` value across its episodes — its
cross-play mean.** Elo is **wrong** for this coworld and phase 50 must not use it: with two
identical scores every episode is a draw and Elo cannot separate anybody (the same ruling as
`cogame-raid`, `runs/2026-08-22-raid/design.md` §Scoring). The sim's obligation is to write one
identical, comparable, higher-is-better number into both seats; the division's ranking mode is a
phase-50 setting. This is also exactly the idea's integrity clause: because the score is joint and
the maps are procedurally novel, there is nothing to codebook, and a policy that only performs
alongside its own twin is visible as such the moment its cross-play mean includes episodes seated
with `tandem-porter` and `tandem-mule` (a phase-50 scheduling requirement, recorded here; **v1 game
code has no notion of who is in the other seat**).

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail. No
other value may appear in either field.

| `reason` | `endRule` | When | Scored |
|---|---|---|---|
| `complete` | `delivered` | All five hull-disc centres inside the goal pad. The normal, good ending. | delivered branch |
| `complete` | `wrecked` | `damage` reached 1000. | non-delivered branch (`cond = 0` → 0.000) |
| `complete` | `out_of_time` | `maxTicks` reached with the couch undelivered and intact. | non-delivered branch |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660) elapsed first. The sim stops at that tick, scores the state as it stands, writes the game-over frame and a complete replay up to that tick. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. | as at the stop tick |
| `fault` | `sim_fault` | A step-10 invariant guard tripped. Partial replay written. | as at the fault tick |
| `fault` | `host_error` | An unexpected server-side exception. Best-effort artifacts written before re-raising. | as at the fault tick |

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (2400 = 100 s of
lobby) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only, `src/ctf/server.nim`), its cog is driven by the
`porter` baseline for the whole run, and the run plays to a normal ending.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {porter, mule}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=porter`. A scripted policy seated as a champion is a FAILURE state.

### Where the decision happens, and the LLM client

**coworld-ctf ships no LLM client in the episode server**, so tandem ports the credential ladder and
transport from `/workspace/starters/cogame-babel/src/babel/llm.nim` into the ctf-lineage server as
`src/tandem/llm.nim` (Cogball's precedent). Ported verbatim in behaviour:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (read with `readCogameUri`) → **none** (client
  `disabled = true`, every turn falls back instantly with no network wait, so offline certification
  completes in seconds).
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. **`us.anthropic.claude-sonnet-4-6` is
  deliberately NOT in the list** — it times out on every sidecar call, so one throttle on haiku
  cascades into all-scripted play (playbook gotcha, raid round 2, 2026-08-23).
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
- `max_tokens = 900` (400 truncates). **No `output_config.effort`** when the model string contains
  `haiku` or `4-5`. Bedrock bodies carry `anthropic_version: "bedrock-2023-05-31"`. No
  `temperature`.
- A system prompt that demands the reply **begins with `{`** (Haiku answers prose-first otherwise).
- `extractJsonObject` (first `{` … last `}`, fence-tolerant) and `cleanNotes`' **rune-boundary**
  truncation (`runeLen`/`runeSubStr`) ported unchanged.

The decision happens in the **game server**, not the player container (the parley/babel/cogball
lineage): the `anthropic_api_key` coworld secret is injected into the *game* pod via
`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/tandem/anthropic_api_key` — without
that manifest env the hosted container never receives the secret and every league episode plays
scripted while local certify still passes (hive, 2026-08-23). Phase 60 greps the *game* log for
`falling back` / `LLM provider is unavailable`.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **48 ticks (2.0 s of sim time)**, **50 turns** per run. At each turn the
server builds both seats' request bodies and issues them as **ONE parallel batch**:
`client.curl.makeRequests(@[req0, req1], timeout)` — curly's batch API, the shape the playbook names
for Nim. **Seats are never queried sequentially.** One call per seat per turn ⇒ 2 × 50 = **100
calls** per episode, at most 2 in flight.

Per-turn timing, all monotonic-deadline bounded:

- attempt 1 batch deadline **4.5 s**;
- any seat that timed out, errored, returned non-JSON or returned no usable order is retried
  **once**, again as a single batch, deadline **2.0 s**;
- an **inter-batch wall floor of 4.5 s**: the loop will not issue turn `k+1`'s batch until 4.5 s of
  wall clock have passed since turn `k`'s. This is not padding — the Bedrock sidecar caps **30
  requests/minute per episode**, and 2 requests per 4.5 s = 26.7 rpm, safely under it (raid round 2
  learning). The wait is a bounded `sleep`, interruptible by the wall-clock stop.
- the turn's total wall cost is therefore `max(4.5 s, llm elapsed)`, hard-capped at
  `turnBudgetMs = 7000`.

```
50 turns x 7.0 s per-turn hard cap                          = 350 s   (worst case)
50 turns x ~5.0 s typical (4.5 s floor dominates)           = 250 s   (expected)
lobby / connect wait (typical 15 s; cap 2400 ticks = 100 s) =  15 s   (typical)
2400 ticks of physics (fastMode; ~40 us/tick)               =   1 s
game-over hold + results + replay write (retrying uploader) =  20 s
                                                            -------
expected total                                              ~ 290 s   < 720 s budget
absolute worst case (100 + 350 + 1 + 20)                    = 471 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                     = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                       = 1200 s
```

`fastMode: true` in every variant: the sim advances as soon as both player containers report ready,
so sim time is not charged against the wall clock — the decision turns are the pacing. The seats
send no inputs at all (the server computes both force vectors), so ctf's `docs/PROTOCOL.md` warning
about the Sprite v1 Ready packet (`0x85`) corrupting dead-reckoned input timing does not apply here
and the player harness sends `0x85` every frame.

**Budget guard (settles early without shortening the run).** At the start of each turn, if
`elapsed + 2 × turnBudget > wallClockBudgetSeconds`, the LLM is switched off for every remaining
turn and the run finishes on the scripted layer (microseconds per turn), so the episode ends
`complete/*` rather than `deadline`. A `budget_guard` record names the turn it fired.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the inter-batch floor, the
outer per-turn deadline, `lobbyJoinTimeoutTicks` on the connect wait, mummy's own socket timeouts on
the serve thread (which runs independently of the game loop, so a 7 s LLM stall cannot drop a
connection), the 660 s engine stop, and ctf's `gameOverTicks` hold before exit. On **two**
consecutive failures for a seat (attempt + retry) that seat's order for the turn is the **`porter`**
scripted order and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`. A seat that
disconnects mid-run keeps playing: its order source degrades to `porter` and revives on reconnect.
**No failure mode leaves a cog unactuated** — the control layer always has an order, defaulting to
the previous turn's, then to `porter`.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are one of two cogs carrying a couch through a warehouse obstacle course.
You and your partner are gripped to opposite ends of the same rigid couch: you
hold one handle, your partner holds the other. The couch moves according to the
SUM of the two forces you apply, and it TURNS according to the difference. If you
both push the same way it slides; if you disagree it spins into a wall.
THERE IS NO COMMUNICATION CHANNEL. You cannot talk to your partner and your
partner never sees anything you write. The only information you get about your
partner is the force you feel through your own handle ("strain") and where their
end of the couch is. Read the strain: it tells you whether to lead or to yield.
Every 2 seconds you set your carry parameters for the next 2 seconds. A
deterministic controller executes them at 24 Hz.
The couch is 2.20 m long and 0.90 m wide. Doorways are between 1.05 m and 2.20 m
wide; the last one is 1.05 m. Scraping a wall and slamming into one both damage
the couch; if the strain in your hands stays too high for too long you drop it,
which costs 2 seconds and a chunk of condition. Your score is the SAME as your
partner's and comes half from delivery time and half from the couch's condition.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars",
 "drive":[x,y],    // direction to push, metres frame, each in [-1,1]; magnitude ignored
 "effort":0..1,    // how hard you push along drive (1 = your full 600 N)
 "yield":0..1,     // how much of the force you FEEL you push along with
                   // (1 = pure follower, 0 = ignore your partner completely)
 "twist":-1..1,    // rotate the couch: +1 counter-clockwise, -1 clockwise, 0 none
 "brace":0..1,     // plant your feet: halves your push, raises your grip limit
 "say":"<=48 chars"}   // spectators only; your partner NEVER sees this
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(babel's `operatorBlock`, ported), a blank line, then the seat's view JSON (§Server). The prompt
text is never echoed into the replay — only `policyKind` and the resulting order are.

### Champion #1 — `tandem-anchor` (owner daveey), `PLAYER_PROMPT`

```
Carry like a professional mover: commit to a line and make your partner's job
obvious. Every turn, aim "drive" straight at the centre of the NEXT doorway in
your route list, not at the goal. Run effort 0.7 in open floor and 0.45 within
2 metres of a doorway. Keep yield low but never zero - 0.15 in the open, 0.35
when the strain you feel is more than 90 degrees away from your drive, because
that means your partner has already committed to a different line and fighting
them will spin the couch. Use twist to line the couch axis up with the corridor
you are about to enter: aim to be within 15 degrees of the doorway's through
direction BEFORE you are within 1.5 metres of it, and set twist back to 0 once
you are aligned. Raise brace to 0.8 whenever your strain is above 600 N or you
are inside a doorway, and drop it to 0 in open floor - braced you push half as
hard but you will not drop the couch. If the couch is scraping, cut effort to
0.25 for one turn and drive directly away from the wall you are touching.
```

### Champion #2 — `tandem-feather` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Carry by feel: let the couch tell you what your partner is doing and be the one
who adapts. Start every turn by reading the strain vector. If it points roughly
where you want to go (within 60 degrees of the next doorway), your partner is
leading well: set yield 0.6, effort 0.5 and add your force along the SAME line -
two cogs pulling together move twice as fast as one. If the strain points away
from the route, your partner is wrong or stuck: drop yield to 0.1, raise effort
to 0.8 and drive at the doorway yourself, becoming the leader for a turn or two,
then hand it back by raising yield again once the strain agrees with you. Never
run effort above 0.5 while the couch is turning faster than 30 degrees per
second - damp it first with twist against the spin. Inside a doorway run brace
0.9, effort 0.3, yield 0.5 and let the geometry do the work. If condition drops
below 70 percent, prioritise condition over speed for the rest of the run: half
effort, brace 0.6, and never drive into a wall you are already touching.
```

### The control layer (deterministic, integer-only, shared by every policy)

`src/tandem/control.nim`, a pure function `(sim, seat) → (F_seat, gripLimit_seat)` evaluated once
per tick per seat. Both LLM orders and scripted orders are compiled by the *same* code, so the two
policy kinds are strictly comparable. Constants: `MaxSeatForce = 600_000` mN, `TwistForce =
400_000` mN, `GripLimitBase = 850_000` mN, `YieldGainQ = 3277` (0.80 in Q12).

1. **Drive term.** `d̂ = unitQ12(order.driveX, order.driveY)` (zero vector → zero term).
   `F_drive = (d̂ · MaxSeatForce · effort255) div (4096 · 255)`.
2. **Twist term.** `n̂_i` = the body-frame perpendicular at this seat's handle, signed so that a
   positive `twist` from **both** seats produces a positive (ccw) torque and no net force:
   `n̂_fore = rot(headingQ + 64 brads)`, `n̂_aft = −n̂_fore`.
   `F_twist = (n̂_i · TwistForce · twist255) div (4096 · 255)` (sign from `twist`).
3. **Yield term.** `F_yield = (lastStrain[i] · yield255 · YieldGainQ) div (255 · 4096)`, clamped to
   `|F_yield| ≤ MaxSeatForce`. This is the compliance knob: at `yield = 1` you push 80 % of the way
   the handle is already pulling you, i.e. you go where your partner is taking you.
4. **Brace.** `F_total = F_drive + F_twist + F_yield`, then scaled by `(255 − brace255 div 2) div
   255` (full brace halves your push) and clamped to `|F| ≤ MaxSeatForce` by proportional
   shortening (integer `isqrt`, never per-axis clipping, so the direction is preserved).
   `gripLimit_i = GripLimitBase + (450_000 · brace255) div 255`.
5. **Regrip / delivered / game-over phases** force `F = 0`.

The control layer contains **no path planning, no obstacle avoidance and no automatic braking**.
The only reflex it implements is the one the idea asks for — compliance with the felt force — and
its strength is a policy parameter, not a constant. Everything else is the policies' problem.

### Scripted baselines

Both emit the *same* order object on the same 2.0 s cadence, so their output is legal by
construction and directly comparable to an LLM's. Both are pure functions of the observation a seat
would receive (they never read the partner's order — a baseline that peeked would break the
no-channel invariant and `tests/test_no_channel.nim` asserts the function's signature cannot).

- **`porter`** — the certification player, the fallback order, and the default. Strain-arbitrated
  leader/follower with no communication:
  1. `drive` = the unit vector from the couch centre to the next doorway centre (or to the goal-pad
     centre in the last cell);
  2. `align = cos∠(lastStrain, drive)` in Q12. If `align < 0` (the felt force opposes where you
     want to go, i.e. your partner has committed elsewhere) → `yield = 0.55`, `effort = 0.35`;
     else → `yield = 0.20`, `effort = 0.65`. **Both copies run this rule, so two porters converge
     within a turn or two without any convention** — and against a stranger the same rule still
     arbitrates, which is the point.
  3. `twist` = `clamp(angleError(couchAxis, doorwayThroughDirection) / 45°, −1, +1)`, where the
     doorway through-direction is the route direction out of the current cell; 0 when the error is
     under 10°.
  4. `brace` = 0.85 when the couch centre is within 1.5 m of a doorway plane **or**
     `|lastStrain| > 600 N`; else 0.
  5. `note` = a fixed short string; `say` = one of four fixed strings selected by state.
- **`mule`** — the second filler, deliberately weaker and different in shape: `drive` straight at
  the **goal-pad centre** (ignoring the route), `effort = 1.0`, `yield = 0`, `twist = 0`,
  `brace = 0`. A stubborn carrier who never yields and never braces; it scrapes constantly, drops
  often, and usually still delivers on wide courses. It exists to give the ladder a spread and to
  be the "bad partner" a champion has to cope with.

---

## Sim module

### What is replaced and what is kept, by path

**Replaced — the ctf arena rules go** (teams, guns, flags, fog of war, lives, respawn, grenades,
spray cans, shields, barriers, puddles, trenches, perks, handicaps, barrage, the map pool and the
map editor all leave the repo):

| ctf path | tandem |
|---|---|
| `src/ctf/sim.nim` (3711 lines: gameplay core, combat, vision, items) | `src/tandem/sim.nim` — the rigid-body core and the step loop of §The game. |
| `src/ctf/arena.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`, `docs/MAPKIT.md`, `docs/pool-review.html` | `src/tandem/course.nim` — the 9×5 cell generator of §The game, the `WallRect` list, the broadphase buckets, the route polyline and `parTicks`, plus the pixie floor/wall bake. **Deleted, not ported.** |
| `src/ctf/global.nim` fog of war, vision cones, first-person raycast, killfeed art, item sprites | `src/tandem/global.nim` — floor/wall/couch/cog/force-arrow/FX sprite composition. Perfect information: no fog. |
| `players/baseline/baseline.nim` (3236-line CTF bot) | `src/tandem_player.nim` — a thin registrar (§Server). |
| `docs/RULES.md`, `docs/PROTOCOL.md`, `docs/ENV_VARIATION.md`, `docs/designs/`, `docs/ladder/`, `docs/plans/*` | rewritten for tandem; ctf's plans/designs deleted. |
| `arena/`, `caos/`, `caos-tools/`, `scripts/`, every `tools/*probe*.nim`, `tools/*spray*`, `tools/nade_probe.nim`, `tools/perk_check.nim`, `tools/four_team_map_probe.nim`, `tools/symnone_*`, `tools/render_replay_movie*`, `tests/*` | deleted. |

**Kept verbatim** (mechanical `ctf` → `tandem` / `CTF_WIRE` → `TANDEM_WIRE` rename sweep only; a CI
grep asserts no `ctf_`/`CTF_` identifier survives outside comments):

| Path | Why it is kept |
|---|---|
| `src/ctf/replays.nim` → `src/tandem/replays.nim` | the whole replay codec wrapper, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`. Two named edits below. |
| `src/ctf/replay_runtime.nim` → `src/tandem/replay_runtime.nim` | `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` — byte-identical apart from imports. |
| `src/ctf/server.nim` → `src/tandem/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, the replay-switch path, the `COGAME_*` runtime contract, `declarePlayerFailure`, the artifact-write block. Five named edits below. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, lobby countdown. New fields, same machinery. |
| `src/ctf/roster.nim` | join/auth/rewards/`playerResultsJson`. Same shape; tandem result keys. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | the one-source JS wire-constant block. |
| `src/ctf/labels.nim`, `src/ctf/rig_art.nim` | HUD labels and the wheeled-rig art compositor (the cogs). |
| `src/ctf/broadcast.nim` | `stepEvents` / `BroadcastTracker` — the state-delta → broadcast-event derivation, retargeted to tandem's event kinds. |
| `replay-viewer/config.nims`, `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js` | the emscripten link flags and the OffscreenCanvas Worker (§Viewer). |
| `client/broadcast_core.js` | game-agnostic sprite-protocol ingest, canvas blit, zoom/pan, minimap. Verbatim apart from the one `window.CTF_WIRE` identifier. |
| `client/chrome_common.js` | **byte-for-byte**, zero edits (§Viewer). |
| `client/replay_broadcast.html`, `client/league_replayer.html` | the broadcast chrome, with a game block appended (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix` | build, bundle and forensics wiring. `tools/build_replay_viewer.sh` gets the `mkdir -p` of the output parent **before** the containment check (ecos, 2026-08-23: paintbot's hook exits 1 on a fresh CI checkout). |
| `data/font.ttf`, `data/atlas/*`, `data/rig_real/blue/*`, `data/rig_real/red/*`, `data/ascii.png`, `data/darkbg.png`, `client/art/walls/*`, `client/art/lockerroom/{bg.jpg,blue_1,red_1}` | real art, kept. Everything CTF-specific (`soldier_*`, `heart_*`, `paintgun*`, `medkit`, `shield`, `spraycan`, `paintbomb`, `ped_*`, the green/yellow locker-room sprites) is deleted. |

**The five named edits to `server.nim`:**

1. **Input source.** Where ctf reads `appState.inputMasks` (the socket) into `inputs[playerIndex]`,
   tandem calls `control.seatForce(sim, seat)` for the two seats and passes the force pair into
   `sim.step`. `inputs` stays a 2-element array of zero masks so ctf's frame plumbing is untouched;
   `writeInputFrameMasks` is still called and simply never records a change. **Player sockets
   contribute no input.**
2. **Turn boundary.** Immediately before stepping a tick where `tick mod turnTicks == 0`, the loop
   runs `decide.turn(sim, llm, seats)`, which enforces the inter-batch floor, issues the one
   parallel batch, applies the deadlines, installs the orders and writes the `order`/`fallback`
   records. All of it inside a monotonic `turnBudgetMs` bound.
3. **Registration interception.** A player's Sprite v1 chat message (`SpriteClientChatMessage`,
   surfaced by `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object
   is consumed as registration and **is not written to the replay chat stream** — the server writes
   a redacted `register` record instead (policy label and kind, never the prompt). Any other chat
   text from a player is dropped.
4. **Wall-clock stop.** A `wallClockBudgetSeconds` check at the top of every loop iteration forces
   `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`.
5. **Shutdown grace.** `/healthz` and `/global` keep answering for a bounded ~20 s after the
   artifacts are written, then the process exits (lantern 0.1.3: the episode runner pings `/global`
   with a 2 s deadline *after* the player pods start, and a short episode can already be gone).

**The two named edits to `replays.nim`:**

1. **`serializeReplaySim`/`deserializeReplaySim` cover the new sim fields** — `pos`, `vel`,
   `headingQ`, `spin`, `damage`, `slip[]`, `lastStrain[]`, `bestProgressPermille`, `deliveryTick`,
   `phase`, `regripUntil`, `activeOrder[]` — because keyframes are how the viewer seeks, and the
   control layer reads all of them. The `Course` is **excluded** from keyframes (it is static and
   already in the config JSON — ctf's own rule for the static map bakes).
2. **`CtfReplayMagic "COWLDCTF"` → `TandemReplayMagic "COWLDTDM"`**, `GameName* = "tandem"`,
   `GameVersion* = "1"`, with ctf's prepend-only changelog-comment discipline and
   `tools/ci/check_gameversion.sh` kept as is.

**No new replay record kind is introduced.** The per-tick action is *derived*: the viewer runs the
same `control.seatForce` over the same recorded orders and the same reconstructed state, and the
per-tick `gameHash` chain proves it derived the same forces. That is why the orders are hashed
(§The game step 1) and why the control layer must obey the integer rules below — the control layer
is inside the determinism boundary here, deliberately, in exchange for a replay that carries 100
order records instead of 4800 action records and for force arrows the viewer can draw exactly.

### Integer arithmetic rules (the determinism contract)

Nim's `int` is 64-bit natively and **32-bit under `--cpu:wasm32`**, which is the exact hazard ctf
documents (`AGENTS.md`; `tools/wasm_replay_smoke.cjs`: "overflow checks trap on arithmetic that is
silently fine natively"). So:

- Every stored sim field is explicitly `int32` (positions, velocities, `headingQ`, `spin`, forces,
  strains, counters) or `bool`/`enum`. No bare `int` in a hashed field.
- **Every product or quotient of two sim quantities is computed in `int64`** and narrowed back with
  an explicit truncating `div` (Nim's `div` truncates toward zero, so the arithmetic is symmetric
  under negation — which is what makes the two handles exactly fair).
- **No floating point anywhere under `src/tandem/{sim,course,control,trig}.nim`.** No `sin`, `cos`,
  `arctan2`, `sqrt`, `pow`, `float`, `float32`, `float64`. Grep-enforced in CI. Floats remain legal
  in the *render* modules (`global.nim`, `rig_art.nim`, the pixie bakes) because rendering never
  enters `gameHash`, exactly as in ctf.
- Trigonometry is a **committed literal table**: `SinQ12*: array[256, int32]` in
  `src/tandem/trig.nim`, `SinQ12[b] = round(4096·sin(2πb/256))`, generated once by
  `tools/gen_trig_table.nim` and checked in; `cosQ12(b) = SinQ12[(b + 64) and 255]`. Sub-brad
  rotation uses linear interpolation between two table entries in `int64`. A test re-derives every
  entry from `math.sin`, so the table can never drift and the *sim* never calls libm.
- `isqrt(v: int64): int64` — Newton's method with an integer seed, committed and unit-tested
  against an exhaustive small-value table plus perfect squares up to 2⁴⁰. The only square root in
  the sim (vector magnitudes, force clamping, strain).
- `bradsOfVectorI(dx, dy: int32): int32` — the integer atan2: fold into the first octant by sign and
  swap, 5-step binary search over brads comparing `int64(dy)·cosQ12(m) ≶ int64(dx)·SinQ12[m]`,
  unfold. Exact, branch-deterministic, no libm.
- Randomness: one seeded `std/random` `Rand` stream from `config.seed`, integer draws only, used for
  exactly one thing — course generation, entirely at `t = 0`. **The sim draws no random numbers
  after tick 0.**

### How the replay achieves server ↔ viewer determinism

The mechanism is ctf's, unchanged:

1. The server writes a `COWLDTDM` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, the expanded `Course`, every physics constant, the roster with
   real names), then the record stream — joins, leaves, chat records (`register`, `order`,
   `fallback`, `budget_guard`, `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/tandem_replay.nim` — which imports the
   **same** `src/tandem/sim.nim` and `src/tandem/control.nim` — through the pinned
   `emscripten/emsdk:4.0.15` + `nimby 2.2.4` container in `Dockerfile.replay-viewer`.
3. In the browser, `tandem_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then
   `tandem_frame` re-steps the sim (compiling the same forces from the same orders) and compares
   `sim.gameHash()` against the recorded hash **every tick** (`checkReplayHash`). One divergent bit
   is caught at the tick it happens, surfaced as `mismatchTick` in the chrome (`#mmwarn`, "Replay
   hash mismatch — showing recorded inputs") and, in CI, as a hard failure.
4. **CI proves the cross-build equality on every push**: the `wasm-viewer` job builds the bundle and
   runs `tools/ci/viewer_smoke.mjs` against the replay `docker-smoke` produced (§Tests), which fails
   if the viewer errors, never draws, freezes, or reports a mismatch tick.

Perf target: 2400 ticks of physics + serve in under 5 s on a CI runner; `tests/test_perf.nim` bounds
it at 60 s.

---

## Server, player, protocol

`src/tandem/server.nim` is ctf's `server.nim` with the five edits above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`) — **both `/client/` routes serve
real pages, registered before any catch-all asset route, and neither opens the player socket**
(lantern 0.1.1: the certifier probes them before starting player pods). Same `COGAME_*` runtime
contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`,
`COGAME_HOST`/`COGAME_PORT`), same 403 on a bad slot/token, same done-before-artifact-writes
ordering, same `src/tandem.nim` entrypoint.

### The player container

`src/tandem_player.nim` (built to `/bin/tandem-player`) reads `COWORLD_PLAYER_WS_URL`,
`PLAYER_PROMPT`, `PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, connects, and sends **one Sprite v1
chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"porter"|"mule"|null,"policy":"<free label>"}
```

It then sends the Sprite v1 Ready packet (`0x85`) after each received frame and otherwise only
receives, until the socket closes. Registration is re-sent once after the first received frame, in
case the first send raced slot registration (babel's pattern). **The receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket** — whisky's `receiveMessage` *raises* on a
close frame and mummy's `send` only queues, so the game's `quit(0)` can outrun the flushed `done`
frame and fail the player container intermittently (raid 0.1.3 → 0.1.4). A seat that never
registers, or registers with neither field, is `scripted: "porter"`.

### The per-seat stream (what a seat can see)

Each seat's websocket receives ctf's normal per-player Sprite v1 frame, one binary message per tick,
built by `buildSpriteProtocolPlayerUpdates`. **Visible**: the whole warehouse and both cogs — there
is no fog of war (ctf's vision cone, bubble, window and first-person modules are deleted), because
two people carrying a couch can see the room and each other. **Hidden**: the partner's order, note,
`say`, effort, yield, twist, brace and felt strain; the partner's `PLAYER_PROMPT`; **real player
names** (board labels carry only `Cobalt`/`Rust`; `showPlayerLabels` is forced false on the player
stream); and future ticks.

### The per-seat view given to the LLM

Numbers rounded to 2 decimals, in **view coordinates** (metres, centred, y up) and degrees. This
object is the tail of the LLM user message and is mirrored into the `order` record for the feed.

```json
{"turn": 12, "of": 50, "clock": {"elapsed_s": 24.0, "par_s": 39.2, "left_s": 76.0},
 "you": {"alias": "Cobalt", "handle": "fore", "pos": [-4.10, 2.35]},
 "partner": {"alias": "Rust", "handle": "aft", "pos": [-6.90, 1.05]},
 "couch": {"pos": [-5.50, 1.70], "angle_deg": 25.0, "vel": [1.02, 0.41],
           "speed": 1.10, "spin_deg_s": -18.0, "length_m": 2.20, "width_m": 0.90},
 "strain": {"vec": [-310, 145], "newtons": 342, "grip_limit_newtons": 850,
            "headroom_pct": 60, "slip_pct": 12,
            "note": "this is the force in YOUR hands; it is the only thing your partner can send you"},
 "condition": {"damage": 214, "condition_pct": 78.6, "damage_last_turn": 31,
               "touching": ["couch_left_rear"], "drops": 1},
 "route": {"progress_pct": 46.2, "cell": [3, 2],
           "next_doorways": [
             {"centre": [-3.20, 1.70], "width_m": 1.20, "through_deg": 0.0, "dist_m": 2.30},
             {"centre": [1.60, 3.40], "width_m": 1.70, "through_deg": 90.0, "dist_m": 7.10},
             {"centre": [6.40, 3.40], "width_m": 1.05, "through_deg": 0.0, "dist_m": 11.90}],
           "goal": {"centre": [18.60, 3.40], "dist_along_route_m": 28.4}},
 "room": {"walls": [{"x": [-7.80, -3.00], "y": [3.30, 3.60]}, "… the rects within 6 m …"],
          "pillars": [{"centre": [-4.10, 0.30], "size_m": 0.80}]},
 "your_last_order": "… the order your seat played last turn, or null on turn 0 …"}
```

Everything in it is either your own state, the shared body's state, or the map. **Nothing in it is
derived from the partner's order** — `tests/test_no_channel.nim` asserts that the composed user
message for seat *i* contains no substring of seat *1−i*'s `note`, `say` or numeric order fields,
over 200 randomised orders.

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"note": "aligning for the 1.2 m door, easing off",
 "drive": [0.98, 0.20], "effort": 0.45, "yield": 0.35,
 "twist": -0.40, "brace": 0.8, "say": "you lead, I'll follow"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `drive` | `[num, num]` | finite, each clamped to `[−1, 1]`; quantised to a Q12 unit vector | non-finite / missing / `[0,0]` → last turn's `drive`, else the vector to the next doorway |
| `effort` | number | finite, clamped `[0, 1]`, quantised to `0..255` | non-finite/missing → `0.5` |
| `yield` | number | finite, clamped `[0, 1]`, quantised to `0..255` | non-finite/missing → `0.25` |
| `twist` | number | finite, clamped `[−1, 1]`, quantised to `−255..255` | non-finite/missing → `0` |
| `brace` | number | finite, clamped `[0, 1]`, quantised to `0..255` | non-finite/missing → `0` |
| `say` | string | **≤ 48 runes** | truncated to 48 runes |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and the whole serialized `order` record **≤ 900
runes**, asserted in `tests/test_replay.nim`. `register.prompt` is capped at **≤ 4000 runes** at the
transport (over-long is truncated, never rejected) and is **never** written to the replay or the
results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — in Nim, `runeLen` /
`runeSubStr` (babel's `cleanNotes`, ported). Slicing a `string` by byte index on any path to the
replay is forbidden. A byte-truncated multi-byte character is exactly the bug that makes replay
bytes render in a browser but fail a strict parser (playbook gotcha); §Tests 6 pins it with a
4-byte emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose (`extractJsonObject`); accept numeric strings; accept `drive` as `{"x":…,"y":…}`;
accept integer percentages (`45`) for the `0..1` fields and divide by 100 when the value exceeds 1.
Only when no object with at least one usable field can be recovered do the retry and then the
fallback fire.

### Results document

Written by `sim.playerResultsJson()` (ctf's function, tandem keys) to `COGAME_RESULTS_URI`. It must
equal the manifest's `results_schema` key-for-key — that schema is `additionalProperties: false` and
the certifier rejects any unknown field. Adding or removing a key here means editing
`coworld_manifest_template.json` in the same commit.

```json
{"names": ["daveey", "daveey-1"],
 "aliases": ["Cobalt", "Rust"],
 "policyKinds": ["llm", "llm"],
 "scores": [0.908, 0.908],
 "win": [true, true],
 "jointScore": 0.908,
 "delivered": true,
 "damage": 214,
 "condition": 0.786,
 "deliveryTicks": 986,
 "parTicks": 940,
 "progress": 1.0,
 "drops": 1,
 "impacts": 6,
 "scrapeTicks": 143,
 "strainPeakNewtons": [1840, 2210],
 "blame": [96, 118],
 "llmTurns": [21, 20],
 "fallbackTurns": [0, 1],
 "reason": "complete",
 "endRule": "delivered",
 "finalTick": 986,
 "seed": 4417231}
```

`names` are the **real policy names** (spectator side). `aliases` are the in-game names. `scores`
holds two copies of one number. `deliveryTicks` is the delivery tick when `delivered`, else
`finalTick`. `blame` is a spectator meter and is **not** part of the score.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDTDM`** format: the static wasm viewer parses exactly
this format, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and the whole seek/keyframe machinery. Consequences handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design ("set 0 for a binary replay format").
- The repo ships **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker): given a
  `.replay` path it prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"tandem/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"course":{…},"orders":[…],"fallbacks":N,"results":{…}}`. It
  brace-matches the config JSON from the first `{` (the technique ctf's `AGENTS.md` documents for
  prod forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.endRule' /tmp/ep.json
  jq -r '[.orders[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "tandem/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), and the champion seats' orders `source == "llm"` with varying `drive`/`yield` values
  — not all fallbacks, and not a constant order.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDTDM`, format version, `gameName` `tandem`, `gameVersion` `1` |
| config JSON | `seed`, the **fully expanded `Course`** (route cells, every `WallRect`, doorway widths/offsets, pillars, `routePts`, `parTicks`, `courseDigest`), `num_agents`, `maxTicks`, `turnTicks`, every physics constant, `players[].name` (**real names**), `slots[].alias`, `fastMode` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| inputs | none (masks never change; the action log is the `order` records) |
| chats | `register` / `order` / `fallback` / `budget_guard` / `result` records (below) |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: 2400 hashes (8 B each) + 100 order records (≈ 300 B each) + a ≈ 25 KB config ≈ **75 KB**.

### Record and event vocabulary

**A. Replay chat records** (written by the server; re-applied at playback in order):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `order` | `turn`, `seat`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `drive` `[x,y]`, `effort`, `yield`, `twist`, `brace`, `say` — **the action log**; the quantised fields are re-applied into `activeOrder` and are hashed |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `result` | the full results document, written once at game over |

**B. Derived broadcast events** — `stepEvents` (ctf's `broadcast.nim`, retargeted) derives these
from state deltas during playback, so they cost no replay bytes and are identical live and in
replay: `phase`, `scrape`, `impact`, `drop`, `regrip`, `doorway`, `strain_warn` (a seat crossing
80 % of its grip limit), `turn_end`, `delivered`, `wrecked`, `gameover`. **Beats** (scrubber
markers): `doorway`, `impact` (≥ 20 points), `drop`, `wrecked`, `delivered`, `gameover`. `scrape` is
throttled to at most one per disc per 6 ticks.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets ctf's JSON-lines `eventsJsonl`, with
`SimEventKind` extended to `Scrape, Impact, Drop, Regrip, Doorway, StrainWarn, Order, PhaseChange,
Delivered, Wrecked`, and the mandatory trailing summary row (`type`, `ticks`, `events`,
`gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is ctf's
script, kept (with `image_tag`, the `docker cp` source path `/workspace/tandem/replay-viewer/dist/.`
and the ecos `mkdir -p` fix); it builds `Dockerfile.replay-viewer`'s `replay-viewer-builder` target
and copies the dist out. `coworld build` invokes it with the absolute bundle directory; the script
already refuses any output path that is not a `static-replay-viewer` directory inside the repo, and
it must stay committed **executable** (`coworld build` hard-requires `os.X_OK`).

### One starter supplies all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and from no other starter:**

| File | Source |
|---|---|
| `replay-viewer/config.nims` | `coworld-ctf`'s `replay-viewer/config.nims`, verbatim except `ctf_replay.js` → `tandem_replay.js` and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_tandem_*`. **No `MODULARIZE`, no `EXPORT_NAME`** — the flags stay exactly as ctf links them. |
| the wasm entry `.nim` | `replay-viewer/tandem_replay.nim`, forked from `coworld-ctf`'s `replay-viewer/ctf_replay.nim` (stage-note buffer, `ABORTING_MALLOC` diagnostics, `predictedViewerRenderBytes` capacity check, `emscripten_exit_with_live_runtime` lifetime — all kept), exporting `tandem_load_replay`, `tandem_frame`, `tandem_input`, `tandem_packet_ptr/len`, `tandem_mismatch_tick`, `tandem_error_ptr/len`, `tandem_stage_ptr/len`. |
| `static_replay*.js` | `coworld-ctf`'s `replay-viewer/static_replay.js` **and** `static_replay_worker.js`, whose bootstrap is the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts` form — which is why `config.nims` must not gain `MODULARIZE`/`EXPORT_NAME`. Splicing one starter's shell onto another's link flags deadlocks the viewer silently with every file present and 200 (cogame-lantern, 2026-08-23). |
| `index.html` | built from `coworld-ctf`'s `client/replay_broadcast.html` (see below). |

`static_replay.js` keeps its `document.documentElement.setAttribute('data-replay-loaded', 'true')`
on the first drawn frame (line 144 of the starter's file) and gains **one** addition: `showFailure()`
also sets `document.documentElement.setAttribute('data-replay-error', message)` before it renders
the `#status` line, so a failure is machine-readable. Those two attributes are what
`tools/ci/viewer_smoke.mjs` waits on. The Worker name becomes `tandem-static-replay`.

### Chrome provenance: what is copied, what is appended, what is removed

- **`client/chrome_common.js` is copied byte-for-byte from `coworld-ctf`. Zero edits.** Its
  CTF-specific paths (perks, handicaps, lives, flag story) stay in the file and are inert because
  the corresponding state fields are simply absent from tandem's stream. Every tandem-specific
  readout lives in the appended game block, and the state JSON **keeps ctf's key names**
  (`t, mt, ph, pl, sp, mx, st, lp, sk, ff, en, mm, bs, teams, roster, events, lead, beats, lulls,
  over, hold`) so chrome_common's plate rendering, feed rows, beat markers, momentum curve, spoilers
  switch and endcard run unmodified against tandem values. A from-scratch page that reuses the
  starter's ids is explicitly **not** what happens here (cogame-gridlock, 2026-08-23).
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one
  `<style>` and one `<script>` block at the end of the file, which inject tandem's readouts into the
  existing containers. Nothing above them is rewritten; the CSS variables, `relayout()`, the
  transport, the endcard, the locker-room loader and the `?embed=1` mode are the starter's.
- **Removed starter elements (exactly these):** `#viewpanel` and its children `#minimap`,
  `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`; `#fpv` and
  its children `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`; and `#povBadge`.
  **Zoom decision: the arena is fixed and the board (1110 × 630 px) always fits the frame, so
  `#viewpanel` — the zoom bar and minimap — is dropped entirely**, per the checklist rule that it
  exists only for boards larger than the frame. `broadcast_core.js`'s zoom/pan/minimap code stays in
  the file, verbatim, simply never driven.
- **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (re-captioned
  "Wedging the couch through the door…", art from `client/art/lockerroom/{bg.jpg,blue_1,red_1}`),
  `#chrome`, `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`,
  `#mmwarn`, `#bannerlane`, `#killfeed`, `#transport` with every button, `#speedchips`, `#scrub`,
  `#momentum`, `#lulls`, `#scrub-win`, `#scrub-head`, `#tick-clock`, `#endcard`, `#status`.

### Transport rules

- `relayout()` is kept verbatim (`client/replay_broadcast.html:4110-4155`): it sets `--hudscale`,
  `--topband` and **`--band`** on `:root` by fixed-point iteration, so the board is letterboxed
  between the scorebug band and the transport band.
- **No overlay sits in the transport band.** Every tandem overlay the game block adds — the
  condition meter, the route progress rail, the force-arrow legend, the doorway callout — is
  positioned inside `#chrome` with `bottom: calc(var(--band) + N * var(--u))`, never over it.
- The **endcard stops at `var(--band)`** (the starter's `#endcard { bottom: var(--band) }` rule is
  kept) and is **dismissed by every seek** (the starter's behaviour, kept).
- **Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">`** elements — the
  game block upgrades chrome_common's markers to buttons with `aria-label` and `title` (e.g.
  "Doorway 4 cleared — 24.1 s"), and a click seeks to that tick. **CSS exists for every kind
  emitted**: `.beat-marker.doorway`, `.impact`, `.drop`, `.wrecked`, `.delivered`, `.over` — a rule
  per kind, asserted by `tests/test_viewer.nim`.

### Readouts

1. **Run bug** (top, always on): two plates — left `Cobalt`, right `Rust` — each with the **real
   policy name** (spectator side), the seat's livery chip, a live **strain bar** (fill = strain ÷
   grip limit, turning amber over 80 %), and a drop counter. `teams.cobalt` / `teams.rust` carry
   `{strain, headroom, drops, blame, policies}` in place of ctf's `{lives, flag, carrier, prog}`.
2. **Centre column**: the clock as `M:SS` from `tick div 24`, with `par 0:39` in the caption, and
   the **condition** figure `78%` as the headline number (green → amber → red).
3. **Route progress rail**: a thin horizontal rail under the scorebug showing `progress_pct` with a
   tick mark per doorway; cleared doorways fill in.
4. **Force arrows** — the idea's headline: an arrow drawn from each cog in its livery colour, length
   ∝ `|F_seat|` (full 600 N = 1.5 m on the board), plus a thinner **white strain arrow** at each
   handle showing `lastStrain`. Drawn Nim-side as sprite objects on ctf's existing FX layer, so they
   are identical live and in replay and cost no extra replay bytes. This is what makes "who pulled
   the wrong way" legible without labels.
5. **Scuff decals**: the couch sprite accumulates baked scuff marks at the disc that took the
   damage, keyed to `damage` in 100-point steps — the idea's "damage reads as accumulating scuffs".
6. **Scrape sparks**: a short spark burst at the contact point every scrape event, scaled by slide
   speed.
7. **Drop**: a dust cloud at the couch, a 6-frame screen shake, a `THUD` chip in `#bannerlane`, and
   the couch sprite dropping its shadow for the 48-tick regrip.
8. **Doorway callout**: the next doorway glows with its width printed in centimetres ("105 cm") —
   the final door reads `105 cm` against a 90 cm couch, which is the whole joke.
9. **Match feed** (`#killfeed`, renamed in copy only): plain language — "Cobalt braces (grip 41 %)",
   "SCRAPE — left rear, −3 condition", "Rust: you lead, I'll follow", "DROP — Rust's grip went at
   2210 N", "DOORWAY 4 CLEARED — 105 cm". Order `note`/`say` strings appear here; this is where a
   spectator sees the LLM playing.
10. **Momentum graph**: ctf's `lead` series repurposed to the **condition curve** (1000 → 0) over the
    whole timeline, drawn from the first frame.
11. **Transport and integrity**: ctf's play/pause, step-back, +5 s, jump-to-end, loop, skip-lulls,
    spoilers, speeds `[1,2,3,4,8,16]`, scrubber with beat markers, tick readout, the end-hold
    countdown and `#mmwarn` — all verbatim.
12. **Endcard**: "DELIVERED in 41.1 s · condition 78 % · score 0.908", the two policy names, and a
    two-row meter table (drops, impacts, scrape seconds, peak strain, blame) — chrome_common's
    `ec-*` machinery, unmodified.

### Art

Real, and mostly already in the repo. The cogs are ctf's shipped **`data/rig_real/blue/*`**
(Cobalt) and **`data/rig_real/red/*`** (Rust) rigs composed by `rig_art.nim`. Walls use ctf's
shipped **`client/art/walls/wall_h.jpg`** and **`wall_v.jpg`** tiles. The floor is baked once at
startup with pixie (already a dependency, already how ctf bakes its board): stained concrete slabs
with expansion joints, painted safety hatching along the route walls, and a dark vignette. The couch
is a baked sprite — shaded upholstery, two cushions, rolled arms, a drop shadow — with a scuff decal
sheet composited on top as damage accrues. The goal pad is a painted loading-bay rectangle with
chevrons. No solid-colour placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter already engineers this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW ≤ 620`. Kept
verbatim. Tandem's game block adds two rules of its own: `.plate-name { flex: 1 1 auto; min-width:
3.2em; overflow: hidden; text-overflow: ellipsis }` so a policy name never collapses to "…", and
under `.tiny` the strain numerals, the blame figure and the doorway callout text are hidden so the
plates read `▮ daveey 78% 0:24 daveey-1 ▮` plus the progress rail. The board aspect is 1110:630,
which the chrome derives from the stream. `tests/test_viewer.nim` asserts both rules are present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-tandem`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `tandem`.
- **`compose.yaml`** — one service, named for the coworld, so the manifest placeholder is
  `{{TANDEM_IMAGE}}` (placeholders are derived from **compose service names**; `{{GAME_IMAGE}}` is
  not a thing — lantern 0.1.0):

  ```yaml
  services:
    tandem:
      image: coworld-tandem:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

  (ctf ships two services/two images; tandem uses babel's one-image/two-entrypoints shape because
  the shared `docker_smoke.sh` and `policies.json` assume a single image.)
- **`Dockerfile`** — ctf's two-stage debian-slim + nimby layout verbatim in structure (nimby 0.1.26,
  `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the container's
  package tree), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:tandem src/tandem.nim` →
  `/bin/tandem`, and the same for `src/tandem_player.nim` → `/bin/tandem-player`. The runtime stage
  copies `/bin/tandem`, `/bin/tandem-player`, `data/`, `client/`, `*.json`. `CMD ["/bin/tandem"]`.
- **`Dockerfile.replay-viewer`** — ctf's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby 0.1.27
  with its sha256 check, the marker splices, the `test -f`/`grep -q` assertion block) with the asset
  list swapped.
- **`coworld_manifest_template.json`** (written against the `coworld` 0.1.42 upload contract —
  validate offline with the CLI's `validate_upload_manifest` before dispatching):
  - top-level `$schema`, `episode_timeout_minutes: 20`, and `tags` ≥ 3.
  - `game.name` `tandem`; `game.runnable` `{"type":"game","image":"{{TANDEM_IMAGE}}",
    "run":["/bin/tandem"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/tandem/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-tandem/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`: `tokens`, `players`, `slots`, `closedRoster`, `seed`, **`num_agents`**,
    `minPlayers`, `maxTicks` (default 2400), `maxGames` (default 1), `turnTicks` (default 48),
    `turnBudgetMs` (default 7000), `attempt1Ms` (default 4500), `retryMs` (default 2000),
    `minBatchSpacingMs` (default 4500), `wallClockBudgetSeconds` (default 660),
    `lobbyJoinTimeoutTicks` (default 2400), `startWaitTicks` (default 24), `gameOverTicks`,
    `regripTicks` (default 48), `fastMode` (default true), `showPlayerLabels`, `model`,
    `maxOutputTokens` (default 900), `maxSeatForceMilliNewtons`, `gripLimitMilliNewtons`,
    `damageCap` (default 1000). The CLI validates every variant and the cert fixture against this
    schema (injecting `tokens`), so every key either appears here or is not settable.
  - `game.results_schema`: exactly the 24 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","reason","endRule","delivered","damage","jointScore"]`,
    `reason` enum `["complete","deadline","fault"]`, `endRule` enum
    `["delivered","wrecked","out_of_time","wall_clock","sim_fault","host_error"]`, every per-seat
    array `minItems: 2, maxItems: 2`.
  - `game.protocols`: **both `player` and `global`**, each `{"type":"text","value":"…"}` — `player`
    describing the registration chat frame, the per-tick Sprite v1 frames and the order schema;
    `global` describing the `/global` spectator snapshot and the static replay bundle. Text form,
    not URIs (playbook gotcha; ctf's URI form is not copied).
  - `game.docs`: `readme` = `{"type":"text","value":"<the README body inlined>"}` and `pages` =
    three entries — `{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined: every number in §The game>"}}`, `{"id":"protocol.md","title":"Wire protocol",…}`,
    `{"id":"carrying.md","title":"Writing a tandem prompt",…}`. A manifest test asserts all four
    values are non-empty text.
  - `game.tags`: `["physics","cooperative","carrying","continuous","llm"]`.
  - `player[0]` (top-level bundled player, with id/type/name/description) =
    `{"id":"baseline","type":"player","name":"Tandem Porter Baseline",
    "description":"Strain-arbitrated scripted carrier; no LLM.",
    "image":"{{TANDEM_IMAGE}}","run":["/bin/tandem-player"],
    "env":{"PLAYER_SCRIPTED":"porter"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}`.
    It is the **only** declared player entry, and it occupies both certification slots — every
    declared player must occupy a slot or cert fails `players_missing` (raid 0.1.2 → 0.1.3).
  - **Variants — `num_agents` is 2 in both, and `description` is required on each:**

    | id | name | description | **`num_agents`** | `players`/`slots` | `minPlayers` | `maxTicks` | turns | `turnTicks` | `turnBudgetMs` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|---|
    | `default` | Delivery (2 cogs, 100 s) | Full course, 50 decision turns. | **2** | 2 | 2 | 2400 | 50 | 48 | 7000 | 660 |
    | `sprint` | Sprint (2 cogs, 60 s) | Same course generator, 30 decision turns, for cheap ladder rounds. | **2** | 2 | 2 | 1440 | 30 | 48 | 7000 | 420 |

    Both seat two players, `slots: [{"alias":"Cobalt"},{"alias":"Rust"}]`, `fastMode: true`,
    `maxGames: 1`. `sprint` changes only run length, **never** the seat count.
  - **Certification fixture** — `num_agents` is 2 here too:
    `certification.players` = `[{"player_id":"baseline"},{"player_id":"baseline"}]`;
    `certification.game_config` = `{"players":[{"name":"Cobalt"},{"name":"Rust"}],
    "slots":[{"alias":"Cobalt"},{"alias":"Rust"}], "num_agents": 2, "minPlayers": 2,
    "seed": 4417231, "maxTicks": 900, "maxGames": 1, "turnTicks": 48, "turnBudgetMs": 7000,
    "minBatchSpacingMs": 0, "wallClockBudgetSeconds": 180, "lobbyJoinTimeoutTicks": 1440,
    "fastMode": true}` — 18 turns, both seats scripted, no LLM, a handful of wall-clock seconds. At
    900 ticks the fixture replay is **37.5 s of playback**, comfortably longer than the viewer
    smoke's soak window (ecos, 2026-08-23: a replay shorter than the soak reads as "frozen").
- **Scaffold from `templates/`** with `<slug>` = `tandem`, `<IMAGE>` = `coworld-tandem`,
  `<SEATS>` = **2**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (copied verbatim, no
  substitutions), `tools/ci/policies.json`, and ctf's `tools/build_replay_viewer.sh`
  (**`chmod +x`**). One addition to the template `ci.yml`: the `docker-smoke` step gets
  `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format). The `NIM_TESTS_RELEASE_ONLY` repo
  variable lists `tests/test_perf.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/tandem-player"`, one image, env-switched):

  | name | env | role |
  |---|---|---|
  | `tandem-anchor` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `tandem-feather` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `tandem-porter` | `PLAYER_SCRIPTED` = `porter` | filler |
  | `tandem-mule` | `PLAYER_SCRIPTED` = `mule` | filler |

- **Repo layout**: `src/tandem.nim`, `src/tandem_player.nim`,
  `src/tandem/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, course.nim, control.nim,
  orders.nim, baselines.nim, llm.nim, decide.nim, trig.nim, roster.nim, replays.nim,
  replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, rig_art.nim,
  wire_constants.nim, server.nim}`, `replay-viewer/{tandem_replay.nim, config.nims,
  static_replay.js, static_replay_worker.js}`, `client/`, `data/`, `tests/`, `tools/`,
  `docs/{RULES.md, PROTOCOL.md, CARRYING.md, plans/}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `tandem.nimble`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for a fixed-point overflow). CI is the only
harness; the sandbox has no Nim, Docker, emsdk or browser. The **determinism gate** (test 2 plus the
viewer smoke) is inviolable: if it fails, the physics or a build flag changed — fix the code, never
the test.

1. **`tests/test_physics.nim`** — sim unit tests: `InertiaMilliKgM2` re-derived from the mass table;
   equal forces at both handles produce pure translation and **zero** `spin` over 480 ticks;
   opposite equal forces produce pure rotation and **zero** displacement; the sum rule holds
   (`F₀ = a, F₁ = b` gives the same `vel` after one tick as `F₀ = F₁ = (a+b)/2`); terminal speed at
   both seats' full force is 2.5 m/s ± the fixed-point quantum; a disc driven into a wall at the
   speed cap for 600 ticks never leaves the world box and its penetration never exceeds 60 000 µm;
   contact normal force is never negative (contacts never stick); friction never reverses the slide
   direction within one substep; the felt strain `H_i` of a free-floating assembly with `F₁ = 0`
   equals `−F₀ · m_cog/M` to within the quantum (the analytic value).
2. **`tests/test_determinism.nim`** (**the gate**) — (a) same seed + same order log ⇒ identical
   `gameHash` at every tick over a full 2400-tick run, twice in one process and once in a fresh sim;
   (b) a one-unit change in any quantised order field changes the final hash; (c) a committed golden
   fixture `tests/data/golden_hashes.json` pins the hash at every 50th tick for seed 4417231;
   (d) **a source guard** that greps `src/tandem/{sim,course,control,trig,sim_types,sim_config,
   sim_state}.nim` for `sin|cos|tan|arctan|arcsin|exp|ln|pow|sqrt|hypot|float` and the build scripts
   for `-ffast-math`, failing on any hit; (e) `SinQ12` re-derived from `math.sin` entry by entry,
   `isqrt` checked exhaustively below 2¹⁶ and on perfect squares to 2⁴⁰; (f) `bradsOfVectorI` agrees
   with a float `arctan2` reference to ±1 brad over 100 000 pseudo-random vectors and is exactly
   antisymmetric under `(dx,dy) → (dx,−dy)`.
3. **`tests/test_course.nim`** — generation: over **500 seeds**, the route is self-avoiding, starts
   in column 0, ends in column 8, has length 9..15; every doorway width is one of the five legal
   values and the **last is exactly 1 050 000 µm**; every doorway gap lies fully inside its face
   with ≥ 200 000 µm margin; no pillar comes within 1 300 000 µm of its cell's through-line; every
   `WallRect` is inside the world box; the broadphase buckets contain every rect that overlaps
   their cell; `routeLen` and `parTicks` are positive and monotone in route length; and
   `generateCourse(seed)` is byte-identical across two calls **and** equal to the `Course` recorded
   in the committed replay fixture.
4. **`tests/test_control.nim`** — the control layer: `|F_seat| ≤ MaxSeatForce` for every one of
   1000 randomised (state, order) pairs; the clamp preserves direction to ±1 brad; the same
   (state, order) pair always yields the same `int32` pair; `brace = 1` exactly halves the drive
   term and raises `gripLimit` to 1 300 000 mN; `yield = 0` makes the force independent of
   `lastStrain`; `twist = +1` from both seats produces a torque and **no** net force; a `Regrip`
   or `Delivered` phase forces `F = 0`.
5. **`tests/test_baselines.nim`** — **the bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random world states × both baselines, the emitted order validates
   against the reply schema — every numeric field finite and inside its range, `drive` non-zero,
   `note` ≤ 160 runes, `say` ≤ 48 runes — and the compiled force is inside `MaxSeatForce`. Plus:
   `porter` × `porter` over **20 seeds** ends `complete/delivered` on every one, with mean damage
   < 400 and no seed exceeding 700; `porter` × `mule` delivers on at least 14 of 20; `porter` scores
   strictly above `mule` × `mule` in mean joint score. (This is the anti-regression pin for the
   whole physics tuning: if the baselines cannot carry the couch, the numbers are wrong, not the
   test.)
6. **`tests/test_orders.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   percentages instead of 0..1, `drive` as an object, NaN/absent fields, out-of-range values, a
   300-character `note`, and a `say` whose 48th and 49th characters are a **4-byte emoji** — the
   truncation must land on the **rune** boundary and the result must still round-trip
   `%$` → `parseJson` and decode as UTF-8. Two consecutive failures ⇒ the `porter` order plus a
   `fallback` record; a timeout on attempt 1 ⇒ exactly one retry.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: both seats' calls go out in
   **one parallel batch** (the fake records in-flight windows; the test asserts they intersect); the
   inter-batch floor keeps consecutive batches ≥ `minBatchSpacingMs` apart; the per-turn budget is
   enforced with a hung client; the budget guard switches to scripted and the episode still ends
   `complete/*`; the 660 s stop yields `deadline/wall_clock`; a tripped invariant yields
   `fault/sim_fault` with a partial replay; a disconnected seat plays `porter` and revives on
   reconnect; a never-connecting seat is reported to `COGAME_PLAYER_FAILURE_URI` and the run still
   reaches a normal ending.
8. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full
   scripted-vs-scripted episode writes `results.json` and a `COWLDTDM` replay; `parseReplayBytes`
   accepts it; re-simulating from the config + order log reproduces **every** recorded hash;
   `tools/replay_summary.py` output parses under a **strict UTF-8 JSON** parser
   (`json.loads(out.decode("utf-8"))`) with the fixture forced to carry a non-ASCII `say` and a
   non-ASCII policy label, so the UTF-8 path is real; the embedded config JSON decodes strictly and
   contains the full `Course` and `seed`; every `order` record is ≤ 900 runes; `results.reason` and
   `results.endRule` are in the legal enums; the stream contains at least one `scrape`, one
   `doorway`, one `order` per seat per turn, and exactly one `result` record.
9. **`tests/test_server.nim`** and **`tests/test_no_channel.nim`** — websocket contract: registration
   chat accepted and **not** echoed into the replay chat stream; a prompt over 4000 runes truncated,
   not rejected; a non-registration chat from a player dropped; bad token 403; `/healthz`;
   `/global` snapshot → ticks → game over; `/client/global` and `/client/player` serve real pages
   and neither opens the player socket; `/healthz` and `/global` still answer 15 s after the
   artifacts are written; artifact writes to `file://` URIs. **Two name spaces**: the composed LLM
   user message and the player-stream board labels contain no `sim.players[i].address`, while the
   chrome roster and `results.names` do. **No channel**: over 200 randomised order pairs, seat *i*'s
   composed user message contains no substring of seat *1−i*'s `note`, `say`, or any of its numeric
   order fields, and `control.seatForce`'s inputs are structurally limited to that seat's own order.
10. **`tests/test_manifest.nim`** — **`num_agents == 2` in every variant *and* in
    `certification.game_config`**; `len(certification.players) == 2`; every declared `player[]` id
    occupies at least one certification slot; `results_schema` keys == `playerResultsJson` keys;
    `game.protocols` has **both** `player` and `global`; `game.docs.readme` and all three pages are
    non-empty **text**; `replay_viewer.bundle == "static-replay-viewer"`; every variant's
    `wallClockBudgetSeconds ≤ 0.6 × 1200`; `attempt1Ms + retryMs ≤ turnBudgetMs`; the compose service
    name and image match `{{TANDEM_IMAGE}}` / `coworld-tandem`; `config_schema` covers every field
    `sim_config.update` reads.
11. **`tests/test_viewer.nim`** — static assertions over `client/replay_broadcast.html` and
    `client/chrome_common.js`: `chrome_common.js` is **byte-identical** to the starter's copy
    (sha256 pinned); `replay_broadcast.html` still contains ctf's `relayout()` with `--band`,
    `--topband` and the `--hudscale` clamp on `:root`; `#endcard { bottom: var(--band) }`;
    `#scorebug`, `#bannerlane`, `#killfeed`, `#transport`, `#mmwarn`, `#endcard`, `#momentum` and
    the `.tiny` block are present; `#viewpanel`, `#fpv` and `#povBadge` are **absent**; a
    `.beat-marker` CSS rule exists for **every** beat kind the sim emits (`doorway`, `impact`,
    `drop`, `wrecked`, `delivered`, `over`) and every marker is a `<button>`; the
    `.plate-name { flex: 1 1 auto; min-width: 3.2em` rule is present; `broadcast_core.js` differs
    from the starter's copy in **exactly** the `TANDEM_WIRE` identifier; no `ctf_`/`CTF_` identifier
    survives anywhere in `client/`, `replay-viewer/` or `src/`; `static_replay.js` sets both
    `data-replay-loaded` and `data-replay-error`; and `config.nims` contains **no** `MODULARIZE` or
    `EXPORT_NAME`.
12. **`tests/test_startup.nim`** — `/bin/tandem` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised when
    unpinned and honoured when pinned; both entrypoints exist and are executable in the image.
13. **`tests/test_perf.nim`** (release-only) — 2400 ticks of physics plus control compilation
    complete in under 60 s.

**CI jobs beyond the Nim tests:**

- `docker-smoke` — `tools/ci/docker_smoke.sh` runs a raw-Docker episode from the certification
  fixture with `SMOKE_SEATS=2` (an independent cross-check against
  `certification.game_config.num_agents`; a mismatch prints `SEAT-COUNT FAIL:`) and
  `SMOKE_REQUIRE_REPLAY_JSON=0`, asserts **every player container's exit code** as well as the
  game's, and uploads the replay it produced as the `smoke-replay` artifact.
- `wasm-viewer` (`needs: docker-smoke`) — asserts `tools/build_replay_viewer.sh` and
  `tools/ci/viewer_smoke.mjs` exist and the hook is executable, builds the bundle, asserts a
  non-empty `.wasm`, downloads the smoke replay, and then **EXECUTES the bundle in headless
  chromium**:
  ```
  node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
       --replay dist/smoke/<name>.replay --timeout 90 --soak 12
  ```
  The job fails if `data-replay-loaded` never arrives, if `data-replay-error` is set, or if the
  soak sees playback stop advancing. The 900-tick fixture is 37.5 s long, so a 12 s soak cannot end
  the replay. **This is the only gate that runs the viewer rather than checking that its files
  exist** (cogame-lantern, 2026-08-23).

---

## Out of scope (v1)

- **Articulated grips and free-walking carriers.** In v1 each cog is *rigidly* attached to its
  handle; the compliance knob is `yield`, not foot placement. Spring-damper grips, letting go on
  purpose, re-gripping at a different point, and walking around the couch to swap ends are the
  obvious v0.2 depth and are deliberately not in the first build — they add three more constraint
  solvers to the determinism boundary for a coordination problem the rigid model already poses.
- **A raw per-tick RL vector transport.** The v1 control channel is one continuous order per 2 s
  decision turn plus the server-side control layer; the per-tick force vector is derived, not sent.
  Because the control layer is already a pure function of `(state, order)`, exposing a per-tick
  socket action is a protocol addition, not a redesign.
- **Box2D**, joints, polygons, friction cones, restitution tuning per material, and any rigid-body
  feature beyond discs versus axis-aligned rectangles with penalty contacts. Rejected for the same
  reason Cogball rejected it: its solver rides on `sinf`/`cosf`/`atan2f` and float32 accumulation
  order, which would make the native↔wasm hash chain depend on two musl builds agreeing.
- **More than two seats, or objects other than the couch.** A three-cog piano, a rope-and-plank
  bridge and asymmetric loads are all natural sequels; each changes `num_agents` or the body
  definition, and the seat-count pin forbids that in v1.
- **Stairs, ramps, doors that open, moving obstacles, other movers in the warehouse, gravity in a
  third dimension.** The world is a flat plane; "drop" means the grip failed, not that the couch
  fell down a stairwell.
- **Any rescue rule for a wedged couch** — no teleport, no auto-unstick, no timeout reset. A jam is
  a scored failure (`out_of_time` with partial progress).
- **Damage to the cogs.** Cog discs collide but take no damage and have no stamina, injuries or
  fatigue; only the couch has condition.
- **Inter-seat communication of any kind**, in any form, at any bandwidth — including emergent side
  channels through the observation. `say` and `note` are one-way to the spectator feed. This is not
  a v0.2 item; it is the point of the coworld.
- **Everything ctf's arena rules carried**: guns, flags, fog of war, first-person POV, lives,
  respawn, grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, the grenade
  barrage, procedural terrain, the map pool, the map editor and mapkit. Deleted, not disabled.
- **Player debug-sprite overlays** (ctf's `0x86` channel). The seats send no inputs and draw no
  overlays in v1; the code path is deleted rather than left dangling.
- **Audio, 3D, camera cuts, slow-motion replays** and any downloaded art asset.
- **Persistent memory across episodes** (no notes carried between runs) and any tournament structure
  beyond the platform league.
- **Campaign mode.** ctf's territory-campaign integration is a platform-side feature and is not
  wired up for tandem in v1.
