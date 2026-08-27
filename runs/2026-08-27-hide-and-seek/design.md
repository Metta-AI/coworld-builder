# cogame-hide-and-seek — design note (2026-08-27)

**Starter: `Metta-AI/coworld-ctf`** (paintbot / the crewrift-derived engine the idea names), mounted
read-only at `/workspace/starters/coworld-ctf` and read for this note. **Every convention there holds
here unless this note says otherwise.** That means: Nim throughout; the `src/ctf/` module split
(`sim.nim` re-exporting the sim modules, `sim_types.nim` owning `GameVersion`, `TargetFps = 24`,
`ReplayFps = 24`, `PlayerHalf = 6`, the fixed-point motion constants `Accel 76 / FrictionNum 144 /
MotionScale 256 / MaxSpeed 704`, the flatty wire types and the rune caps `MaxSayRunes` /
`MaxNoteRunes` / `MaxPromptRunes`); the continuous-2D movement with slide collision; the recursive
shadowcast fog-of-war on an 8 px cell grid plus the aim-carried vision cone
(`sim.nim:2489-2718` — `castFovOctant`, `computeFovShadowcast`, `applyFovCone`, `refreshPlayerFov`,
`playerVisibleTo`); the Sprite v1 protocol and the mummy HTTP/websocket server implementing the
Coworld contract; the `decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` / `control.nim`
commander layer with its one-parallel-batch-per-turn shape, its `attempt1Ms` / `retryMs` /
`turnBudgetMs` / `turnSpacingMs` deadlines, its tolerant JSON extraction, rune truncation,
repair-don't-reject validator and fallback ladder; the binary `COWLD…` replay of *per-tick input
masks plus a per-tick `gameHash`*, re-simulated by **the same sim module** compiled to wasm by
`replay-viewer/config.nims`; the `client/` broadcast chrome (`chrome_common.js` +
`broadcast_core.js` + `replay_broadcast.html`, with the appended game block spliced in through the
`window.PaintballChrome.install(PB_CTX)` hook at `client/replay_broadcast.html:4337`); nimby +
`Dockerfile` + `Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh`; and the Nim test suite
with its four shards (`tests/shard_1..4.nim`, `tests/config.nims`).

Starter choice, one line: **the idea explicitly asks for a new object layer on the crewrift/ctf
engine — continuous 2D movement, line-of-sight cones, Sprite v1, replay infra — which is the first
row of the starter table** (`prompts/10-design.md`: "any real-time game loop (grid OR continuous
physics), new rules written for this coworld"), and `coworld-ctf` *is* that engine in this fleet
(`coworld-ctf`'s own README: "a fork of Crewrift … keeps Crewrift's continuous 2D movement,
line-of-sight, Sprite v1 protocol, websocket server, and replay infrastructure"). It is deliberately
**not** the `cogame-moba` row: nothing pre-exists to port bit-exactly — Baker et al.'s
`multi-agent-emergence-environments` is a MuJoCo 3-D RL environment whose physics cannot be
re-derived in a wasm replay, so what this repo reproduces is its **rules idiom** (two-phase clock,
movable boxes, ramps, a lock action, ±1/tick seen/unseen team reward), not its bytes.

Where this note departs from coworld-ctf it says so. The departures are: **no weapons at all** (the
gun, spray, grenades, med kits, shields, barriers, hit points, lives and respawns are deleted, not
disabled); the flag/heart objective, floor paint and King of the Hill are deleted; the board is a
small authored **room** (720 × 400 px) instead of the 1235 × 659 procedurally generated arena, and
the map generator, map pool, map editor and mapkit go with it; obstacles become **dynamic** (movable
crates, panels and ramps, with a lock action), which forces a dirty-rect rebuild of the wall mask
and an epoch-invalidated fov cache; the episode has a **two-phase clock** and two side-swapped
games; and the scoring rule is the idea's **±1 per tick seen/unseen**, zero-sum between the trios.

### Source idea (verbatim)

> HNS Hide and Seek (fork of the crewrift/ctf engine) — hiders, seekers, movable boxes and lockable
> ramps on the continuous-2D line-of-sight runtime we already have
>
> Build on the Metta-AI/coworld-crewrift engine (continuous 2D movement, line-of-sight cones, Sprite
> v1 protocol, replay infra) the same way coworld-ctf, coworld-cogtank and coworld-battle-royale
> did — Hide and Seek is mostly a new object layer (movable boxes, ramps, lock action) plus a
> two-phase clock (hider prep, then seekers released) and the ±1/tick seen/unseen reward. The OpenAI
> autocurriculum (fort → ramp → lock → box-surf) is the hoped-for spectacle.
>
> Also absorbs 04 Lantern (hide-and-seek with crates and flashlights) — treat Lantern's flashlight as
> the seeker vision cone crewrift already has, and close that card into this one when built.
>
> Seats: 2-3 hiders + 2-3 seekers
> Motive: team zero-sum with tool use
> Policy interface: crewrift per-tick protocol + grab/lock
> Integrity: room layout seeded; anonymous aliases.
> Replay plan: crewrift viewer; annotate locked objects; fort-reveal beat.
>
> Source: github.com/openai/multi-agent-emergence-environments (Baker et al. 2019);
> github.com/Metta-AI/coworld-crewrift.

### Upstream, consulted and pinned

The rules idiom reproduced here is Baker et al. 2019, *Emergent Tool Use From Multi-Agent
Autocurricula* (`openai/multi-agent-emergence-environments`). The claims this note makes about it are
exactly the five below; each is transcribed into `src/hns/upstream.nim` with its citation comment
beside it, and `tests/test_hns_upstream.nim` asserts the shipped constants still match.

| Upstream fact | How it lands here | Where |
|---|---|---|
| Two-phase episode: hiders get a **preparation phase** during which seekers are immobilised and cannot observe | `prepTurns` of frozen, unobserving seekers; seekers released at `prepTicks` | §The game → The clock |
| Reward is **±1 per timestep, team-based**: hiders `+1` if **all** hiders are hidden from all seekers, `−1` otherwise; seekers get the negation | `hiddenTicks`/`seenTicks` over the hunt phase, zero-sum margin | §The game → Scoring |
| Visibility is a **line-of-sight cone** with a limited range, blocked by objects | the starter's shadowcast + `applyFovCone`, retargeted; boxes are opaque and dynamic | §Sim module |
| Objects (boxes, ramps) are **movable and lockable**; a locked object can only be unlocked by the team that locked it | grab (`C`) / lock (`A`), `lockedBy ∈ {none, hiders, seekers}` | §The game → Objects |
| Ramps let an agent **cross a barrier it otherwise could not**, and hiders' counter is to lock the ramps away | the vault rule, `VaultSpanPx` | §The game → Vaulting |

**Box surfing is deliberately not reproduced** — it is an exploit of MuJoCo's 3-D contact dynamics
(standing on a box and dragging it under yourself) with no meaning in a top-down 2-D sim. §Out of
scope records the decision and what replaces it in the autocurriculum story (fort → ramp → lock).

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time continuous-2D loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-hide-and-seek` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=burrow\|scatter`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance, byte-for-byte `chrome_common.js`, nano-banana cog kits + starter art) |
| Two name spaces | §The game → Seats (`HIDER-alpha`… in-game; real policy names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (typical 353 s, worst 510 s, engine stop 660 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 6`, three times |
| Simultaneous decisions as one parallel batch | §Decisions (all live seats in one `curl.makeRequests` batch per turn) |
| Replay bytes self-sufficient | §Server (config + room spec + object deal, joins, per-tick masks, chats, per-tick hashes, seed) |
| Rune-boundary truncation on every free-text field | §Decisions → Reply schema |
| Room layout seeded, anonymous aliases (the idea's integrity note) | §Sim module (room `pool[seed mod 3]`, object deal from the seeded stream, aliases only) |

---

## The game

A **room**, 720 × 400 pixels, with walls, doorways and eight pieces of movable furniture: four
crates, two panels and two ramps. **Three hiders** get fifteen seconds alone in it — they can drag
the furniture, wall off a doorway, build a fort, lock what they have built, and drag the ramps out of
reach. Then a door opens and **three seekers** walk in with torch-beam vision cones and thirty
seconds to look. Every tick in which **any** hider is inside **any** seeker's cone costs the hiders a
point and pays the seekers one; every tick in which all three hiders are unseen does the reverse.
Then the two trios swap sides and play the room again, and the episode's score is the average. There
are no weapons and nobody can be killed: the only thing that happens in this game is that somebody is
looking and somebody else does not want to be found.

### Seats, cogs, aliases

- **`num_agents` = 6.** Exactly six seats, always — in both manifest variants and in the
  certification fixture. **One cog per seat**: three hiders and three seekers, which is the top of
  the idea's own "2-3 hiders + 2-3 seekers" range. The reasoning, stated once:
  - Three-a-side is the smallest number at which the idea's spectacle exists. A fort needs one cog
    dragging while another holds the far side of the panel; a sweep needs one seeker at each doorway.
    At 2v2 the prep phase is one crate and the hunt is a footrace, and the autocurriculum story the
    idea is buying (fort → ramp → lock) never appears.
  - Six seats is one parallel batch of six LLM calls per hunt turn, which fits the Bedrock sidecar's
    30-request-per-minute per-episode cap at `turnSpacingMs = 13000` (6 × 60/13 = 27.7 req/min) and
    fits the wall clock with 210 s of headroom (§Decisions). Eight seats would not.
  - One cog per seat — not paintbot's squad-of-four — because the idea's policy interface is
    "crewrift per-tick protocol + grab/lock", i.e. a cog, and because a seat that commands one body
    can be given the whole grab/lock/vault vocabulary without a per-cog order array.
- **Sides are dealt by slot parity and swap between the episode's two games.** Game 1: slots 0, 2, 4
  are the **hiders** (`Team.Red` internally), slots 1, 3, 5 the **seekers** (`Team.Blue`). Game 2:
  the same six seats, sides swapped. This is what makes the duel fair — hiding and seeking are not
  symmetric jobs, so a league that graded a seat on one of them would be grading the deal, not the
  policy. It reuses the starter's `maxGames` multi-game episode (paintbot ships `maxGames: 2`), and
  it makes the per-episode score exactly zero-sum (§Scoring).
- **Two name spaces.** In-game a cog is `<ROLE>-<identity>`: `HIDER-alpha`, `HIDER-beta`,
  `HIDER-gamma`, `SEEKER-alpha`, `SEEKER-beta`, `SEEKER-gamma`, where the identity is fixed to the
  seat for the whole episode (`IdentityNames[slot div 2]`, the starter's array at
  `src/ctf/roster.nim:64`) and only the role prefix flips at the side swap. Those aliases are the
  only names in an observation, a prompt, an order, a shout, a radio line or a sprite label. The
  seats' **real policy/player names** (`daveey`, `daveey-1`, `Baseline (1)`…) live only in
  `results.names`, in the replay's join records and in the viewer's scorebug and leaderboard.
  `showPlayerLabels` is **false** in every variant, so no in-board sprite can leak an identity.
- **Colours** are cosmetic and fixed by role, not by seat: hiders are the starter's blue palette,
  seekers its red. A seat therefore changes colour at the side swap; the scorebug names the trio by
  its three aliases, so a spectator can still follow a policy.

### The room

The board is **720 × 400 px**. It is installed the way the starter installs any map — through
`selectCtfMap` (`src/ctf/arena.nim:3442`), which sets `MapWidth`, `MapHeight`, the fov grid
dimensions and `ShoutRange = MapWidth div 5` from the loaded map, so no engine constant is edited to
shrink the board. `ShoutRange` therefore lands at **144 px** and the fov grid at
**90 × 50 = 4500 cells** (`FovCellSize = 8`, unchanged).

Why 720 × 400 rather than the starter's 1235 × 659: a cog moves at `MaxSpeed 704 / MotionScale 256 =
2.75 px/tick`, i.e. 66 px/s, so crossing the starter's arena takes 18.7 s — longer than this game's
whole hunt phase. At 720 px a crossing is **262 ticks (10.9 s)**, which makes a 15 s prep and a 30 s
hunt both meaningful, and it doubles the on-screen size of everything at 360 px (§Viewer).

**Rooms are authored, not generated**, and the episode's room is **chosen by the seed** —
`room = pool[seed mod 3]` — which is the idea's "room layout seeded" without the implementation-
defined behaviour of a procedural generator. The three rooms live in
`data/rooms/room_{warren,atrium,long_hall}.json` and are **the starter's own `mapSpec` document**
(`arena.nim:3200 mapSpecJson` / `arena.nim:3271 mapFromSpecJson`, the format `config.mapSpec` already
carries and replays already pin — `sim_config.nim:844-855, 1062-1063`), with `symmetry: "symNone"`
(full-board authoring) and four new arrays:

| New key in the room spec | Contents |
|---|---|
| `regions` | `{"id":"r1","box":[x,y,w,h],"doors":["d1","d2"],"name":"west closet"}` — the named parts of the room the LLM talks about |
| `doors` | `{"id":"d1","at":[x,y],"w":56,"axis":"v"}` — the gaps between regions |
| `anchors` | `{"id":"p1","kind":"pocket"\|"pad"\|"patrol","at":[x,y],"team":"hiders"\|"seekers"\|null}` — hiding pockets, spawn pads, baseline patrol points |
| `objectSpawns` | `{"at":[x,y],"kinds":["crate","panel","ramp"],"axis":"h"\|"v"}` — ≥ 14 candidate positions per room |

Static walls are 16 px thick; doorways are **56 px** wide (a cog's solid footprint is 12 px and its
drawn body 34 px, so two cogs do not fit abreast). `room_warren` is six small regions and five doors;
`room_atrium` is one central hall with four alcoves; `room_long_hall` is a single long hall with two
stub walls — the room where nothing is hideable until you build something, which is why the second
manifest variant pins it.

**Load-time validation** (`tests/test_hns_room.nim` runs it over every committed room, and the server
refuses to start on a failure): the spec parses; every wall rect is inside the board; every door is a
real gap between exactly two regions; every anchor and every `objectSpawn` is on walkable floor with
the full 12 px footprint's clearance; every region is reachable from every seeker pad over walkable
floor with **no** objects placed; there are ≥ 14 `objectSpawns`, ≥ 6 `pocket` anchors, exactly 3
hider pads and exactly 3 seeker pads; and the file's sha256 equals the literal pinned in the test.

### The objects

Eight objects per game, all axis-aligned rectangles, all opaque to vision, all solid to movement:

| Id | Kind | Size (px) | Count | Notes |
|---|---|---|---|---|
| `box1`…`box4` | crate | 64 × 64 | 4 | the fort bricks |
| `pan1`, `pan2` | panel | 128 × 32 (`h`) or 32 × 128 (`v`) | 2 | one panel walls off a 56 px door with room to spare |
| `ramp1`, `ramp2` | ramp | 40 × 80 (`v`) or 80 × 40 (`h`) | 2 | the only way over a locked wall |

**The deal is seeded, not authored**: the room's `objectSpawns` are shuffled by the episode's
`setupRng` and the first four crate-capable, two panel-capable and two ramp-capable candidates are
taken in that fixed order, each object taking its candidate's `axis`. The same deal is used for both
games of the episode (the two trios play the same room and the same furniture — that is what makes
the swap a fair comparison), and it is pinned into the replay config.

Every object carries `pos` (integer px, top-left), `kind`, `axis`, `lockedBy ∈ {none, hiders,
seekers}`, `heldBy` (slot index or −1). All of it is in `gameHash`.

### The controls (Sprite v1, unchanged bits, new meanings)

| Input | Meaning here | Starter's meaning |
|---|---|---|
| d-pad | locomotion, never changes aim | same |
| `B` / `Select` | rotate aim counter-clockwise / clockwise, `aimTurnRate = 6` brads/tick (≈ 8.4°/tick, a full turn in 43 ticks) | same, rate 5 |
| `A` (`0x04`) | **lock / unlock** the object in reach | fire |
| `C` (bit 7, `0x80`) | **hold to grab**, release to drop | charge/throw a grenade |

`docs/PROTOCOL.md` is forked, not rewritten: the bit-7 row becomes the grab row, the `own aim`
readback marker and the frame-pacing/lobby-detection sections are kept verbatim, and the Player Ready
(`0x85`) section keeps its warning (irrelevant here — seats send no inputs at all, the server
computes every mask, so the dead-reckoning hazard cannot arise; `fastMode` is on).

### Vision — the seeker's torch, and Lantern's flashlight

Vision is the starter's, retargeted by config only:

- **Forward cone**: half-angle `visionConeDeg = 35` (a 70° beam) around the **aim** angle, reaching
  `sightRange = 340 px` (47 % of the room's width), with walls **and objects** blocking it.
- **Bubble**: `visionBubble = 48 px` omnidirectional, still line-of-sight-blocked (the starter's
  `applyFovCone` keeps bubble cells only if the shadowcast reached them), so a hider pressed against
  the far side of a crate is not seen from 20 px away.
- Aim carries vision: you see where you point, not where you walk. Both roles have the **same** eyes.
  That is deliberate: it makes a hider's peek out of a fort a real risk, and it is exactly the
  mechanic card 04 Lantern asked for — **Lantern's flashlight is this cone**, and this coworld closes
  that card.

`sightRange` is a new config field replacing the starter's `visionRange = gunRange * 3 div 2`
(`sim.nim:2550`), because `gunRange` is deleted with the gun.

### The clock

- **Tick** = 1/24 s (`TargetFps = 24`, unchanged). **Turn** = one order round every
  `turnTicks = 90` ticks (3.75 s).
- **One game** = `prepTurns = 4` (360 ticks, **15.0 s**) + `huntTurns = 8` (720 ticks, **30.0 s**) =
  **12 turns, `maxTicks = 1080` ticks (45 s)**.
- **One episode** = `maxGames = 2`, sides swapped between them: **24 turns, 2160 ticks, 90 s of
  sim**. Between turns the loop runs uncapped (`fastMode: true`), so the sim costs seconds of CPU and
  the episode's wall clock is the 24 LLM turns (§Decisions).
- **Prep**: seekers are frozen at their pads — their input masks are forced to zero, they take no
  LLM call, their fov is not computed, and no scoring runs. Hiders move, drag, lock and talk.
- **Release**: at `tick == prepTicks` the seekers' torches come on, a `release` event fires and the
  viewer plays the **fort-reveal beat** (§Viewer). Scoring starts on the **first hunt tick**.

### Turn and tick structure — the exact resolution order

Per **decision turn** `T` (at tick `turnTicks·(T−1)` of the current game), in this order:

1. The engine snapshots the world and builds an observation for every **live** seat — during prep
   that is the three hiders only, during hunt all six (§Decisions → observation).
2. All live seats' LLM requests go out as **one parallel batch** (`curl.makeRequests`, the starter's
   `decide.nim` shape), attempt-1 deadline `attempt1Ms = 7000`. Scripted seats compute locally, in
   microseconds, and consume no request.
3. Every seat that timed out, errored, returned non-JSON, or returned no usable `intent` is retried
   **once**, again as one batch, `retryMs = 3000`. A provider 429 with no other candidate model skips
   the retry (it cannot land) and falls straight through.
4. A seat still without a usable reply takes the **`burrow`** scripted order for its role, and a
   `fallback` record is written (§Decisions → degrade).
5. Orders are installed in ascending slot. A field that does not validate is **repaired**, never
   dropped: an unknown `intent` becomes `watch`; an unknown `object` id, or one the seat may not
   touch, drops back to the seat's **previous** order (else `burrow`'s) and counts in
   `ordersRejected`; an out-of-box `to` is clamped into the board.
6. `say` (≤ `MaxSayRunes` = 10 runes) becomes an in-world **shout** at the cog's position — the
   starter's mechanic, verbatim: audible to **anyone of any team** within `ShoutRange` (144 px),
   drawn as a speech bubble, alive for `ShoutTicks` (72 ticks), and in `gameHash`. Shouting gives
   your position away; that is the point. `radio` (≤ 96 runes) is the **team** channel: delivered to
   the two teammates' next observation and drawn in the spectator feed, never as a bubble, never
   audible to the other trio. `notes` (≤ `MaxNoteRunes` = 160 runes) is private to the seat.
7. `turnSpacingMs = 13000` is a floor on wall-clock time between consecutive **batch starts** (the
   starter's mechanism in `decide.nim`, kept), which is what keeps six seats under the sidecar's
   30 req/min per-episode cap.

Then, for each of the next `turnTicks` ticks, in this order — **this is the whole physics of the game
and nothing else mutates the world**:

1. `tick += 1`. If `tick == prepTicks`, the phase becomes `hunt`: seeker inputs stop being zeroed,
   seeker fov starts being computed, a `release` event is emitted and the sealed-fort scan of step 11
   runs immediately.
2. **Compile actuator masks.** For every cog in ascending slot the control layer turns its standing
   order into a Sprite v1 mask (§Decisions → the driver). A seeker's mask during prep is forced to
   `0`. The masks — not the orders — are what the replay records.
3. **Aim.** Each cog's `aimBrads` rotates by `±aimTurnRate` if `B`/`Select` is held. Aim is
   independent of movement and of everything below.
4. **Grab / release**, ascending slot:
   - `C` released (or held while the cog is dead-stopped against a refusal for `grabBreakTicks = 24`
     ticks, or the phase changed, or the game ended) → the held object is dropped, `heldBy = -1`,
     `drop` event.
   - `C` newly pressed and the cog holds nothing → probe a segment from the cog's centre along its
     aim, from the body edge out to `grabReach = 30 px`. The first object whose rectangle the segment
     intersects, that is **not** `lockedBy` the other team and **not** already `heldBy` another cog,
     binds: `heldBy = slot`, `grab` event. Ties (two cogs in the same tick) go to the lower slot; the
     loser gets nothing and a `grab_failed` result. An object locked by the other team refuses and
     emits `lock_refused`.
5. **Lock toggle**, ascending slot. `A` newly pressed and `lockCooldown[slot] == 0`: take the held
   object, else the object nearest the cog's centre within `lockReach = 30 px` of its rectangle. If
   `lockedBy == none` → `lockedBy = cog's team`, `lock` event. If `lockedBy == cog's team` →
   `lockedBy = none`, `unlock` event, and the object is released if held by the other team (it is
   not — the other team could not have held it). If `lockedBy` is the other team → refused,
   `lock_refused` event. Either way `lockCooldown[slot] = 24`; every cog decrements it.
6. **Movement**, ascending slot, the starter's integer fixed-point integrator (`applyInput`,
   `sim.nim:2333`) with two additions:
   - a cog holding an object has its `MaxSpeed` scaled by `carrySpeedPct = 55`;
   - the proposed displacement `(dx, dy)` is applied to the cog **and, rigidly, to its held object**.
     The move is committed only if, after it, the object's rectangle overlaps no static wall, no
     other object, no cog other than the holder, and no **keep-clear disc** (below); otherwise
     **neither** moves this tick, the cog's velocity on the blocked axis is zeroed, and
     `pushBlockedTicks[slot] += 1`. The starter's per-axis slide (`MovementSlideMaxScan`) is applied
     to the pair, so a crate slides along a wall instead of sticking.
   Cog-cog collisions keep the starter's `PlayerSolidSpan` / `PlayerBouncePct` behaviour. Objects are
   solid to every cog, held or not.
   - **Keep-clear discs.** No object may be moved to within `keepClearPx = 96` of a **seeker pad**.
     Without this a hider trio can wall the seekers in during prep and win 1000 permille with no game
     played; with it, sealing a *fort* is legal and sealing the *door the seekers come out of* is not.
     The refusal is the ordinary push refusal above, so it degrades into "the crate stops here".
7. **Vault**, ascending slot. A cog that holds nothing, whose centre is inside a ramp's rectangle,
   whose velocity along the ramp's axis toward its **head** end is at least
   `vaultMinSpeed = MaxSpeed div 2`, and for which the first blocking span (wall or object) beyond
   the head is at most `vaultSpanPx = 112 px` thick, enters the **airborne** state:
   `vaultTicks = 10`, moving along the ramp axis at `vaultSpeed = 5 px/tick` (50 px in all) and
   ignoring wall and object collisions. A `vault` event is emitted at the launch. On the last
   airborne tick the cog lands at the first position along the axis whose 12 px footprint is clear;
   if none is clear within the 50 px, it is refunded to the ramp's foot (`vault_failed`). While
   airborne a cog cannot grab or lock, **and it is visible over the furniture**: visibility of an
   airborne target is tested against the **static wall mask only** (§Sim module), because its head is
   above the crates. Vaulting is how you get in; being seen doing it is what it costs.
8. **Geometry refresh.** If any object moved, was created or changed state this tick, the union of
   its old and new rectangles is re-rasterised into `objectMask`, the affected cells of `fovBlocked`
   are recomputed from `wallMask or objectMask`, and `geometryEpoch += 1`, which invalidates every
   cog's cached shadowcast (`PlayerFov.cellValid = false`). Nothing outside the dirty rect is
   touched.
9. **Fov refresh**, ascending slot: `refreshPlayerFov` for every cog whose cell, aim or
   `geometryEpoch` changed. During prep, seekers are skipped.
10. **Exposure scoring** — hunt phase only. `exposed = ∃ seeker s, ∃ hider h : playerVisibleTo(s, h)`
    (an airborne hider uses the static-mask test of step 7). If `exposed`, `seenTicks += 1`,
    otherwise `hiddenTicks += 1`. Per hider, `seatSeenTicks[h] += 1` if any seeker sees **that**
    hider. On a transition for a `(seeker, hider)` pair, a `spotted` or `lost` event is emitted with
    the pair, the tick and the position.
11. **Sealed-fort scan** — only at a turn boundary and at the release tick (not every tick). A
    breadth-first fill over the 8 px fov grid from every seeker's current cell, blocked by static
    walls and by objects **locked by the hiders** (unlocked objects are passable: a seeker can shove
    them). Every hider whose cell is not reached is `sealed`. `sealedMask` is hashed; per hider
    `sealedTicks` accumulates the ticks it spent sealed. Emits `sealed` / `unsealed` on change.
12. **Shout expiry** (`pruneAgedFx(recentShouts, …)`, hashed) and cosmetic FX pruning — the
    starter's, unchanged.
13. **End evaluation**: `tick == maxTicks` finishes the game (§End conditions).

### Scoring formula and sign

Per game `g` (720 hunt ticks in the default variant):

```
huntTicks[g]       = huntTurns * turnTicks                        (720)
seenTicks[g]       = hunt ticks on which ANY seeker saw ANY hider
hiddenTicks[g]     = huntTicks[g] - seenTicks[g]
marginPermille[g]  = (hiddenTicks[g] - seenTicks[g]) * 1000 div huntTicks[g]     ∈ [-1000, +1000]
```

`marginPermille[g]` is written **from the hiding trio's point of view** in that game. For each seat
`s`, with `side(s, g) = +1` when the seat hid in game `g` and `−1` when it sought:

```
scorePermille[s] = ( side(s,0) * marginPermille[0] + side(s,1) * marginPermille[1] ) div 2
scores[s]        = scorePermille[s] / 1000.0                                     ∈ [-1.0, +1.0]
```

**Sign: higher is better.** `+1.0` means "my trio was never seen while hiding and never lost sight
while seeking"; `−1.0` is the reverse. Because every seat hides in exactly one game and seeks in the
other, and the two trios are complementary, **the six scores sum to exactly zero** — the idea's "team
zero-sum". `tests/test_hns_scoring.nim` asserts `sum(scorePermille) == 0` over 500 randomised end
states, including the odd-`huntTicks` truncation case.

**The league ranks by `results.scores[s]`.** `results.win[s]` is `scorePermille[s] > 0`; a
`scorePermille` of exactly 0 for all six is a draw and every `win` is false. There is no
`results.winner` key — the trios change composition between games, so the only meaningful verdict is
the per-seat number.

**Everything else is measured and shown, never scored**: `seatSeenTicks`, `sealedTicks`, `locks`,
`grabs`, `vaults`, `pushedPx`, `shouts`. Weighting any of them would need a magnitude the idea does
not pin and would break the exact zero sum; §Out of scope records the decision.

**Cross-play (the idea's integrity note).** The certification fixture seats **three `burrow` and
three `scatter`** scripted cogs, alternating by slot so each trio is mixed, and the league division
runs **two scripted fillers alongside the two prompt champions** (§Packaging), so a six-seat draw
seats a champion with unfamiliar partners in essentially every episode. The game records what it was
given: `results.policyKinds` per seat and `results.crossPlay = true` when at least one LLM seat and
at least one scripted seat sat together. Both seeded streams are unsteerable: the room is
`pool[seed mod 3]` and the object deal is drawn from `setupRng` **before any seat connects**, so no
seat's behaviour can shift either.

### End conditions and legal `results.reason` values

The episode ends at the first of: **both games played out**, or the **wall-clock stop**, or a
**fault**.

- **Full time** — game 2 reaches `maxTicks`. Settles after the `gameOverTicks` display hold.
- **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of the loop
  (`server.nim:1407-1417`), kept.
- **Fault** — an unexpected exception in the sim or the loop.

`results.reason` is the starter's closed enum; **exactly these three values are legal** and the game
emits nothing else:

- **`complete`** — both games played to `maxTicks`. `results.endRule = "full_time"`. The healthy
  value.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (default **660 s**). The engine
  stops at the current tick and settles with the **real** numbers so far: a game that reached its
  hunt phase contributes `marginPermille` computed over the hunt ticks **played** (`huntTicksPlayed`,
  recorded), and a game that never started contributes `0`, so a deadline episode is still rankable
  and still zero-sum. Artifacts are written, exit 0. `results.endRule = "wall_clock"`. **Declared
  acceptable** for SPEC §Definition of done check 4; the budget guard below exists so it should never
  fire.
- **`fault`** — caught; the episode is settled from the last completed tick,
  `results.endRule ∈ {"sim_fault", "host_error"}`, `results.stopDetail` names it (≤ 200 runes,
  rune-truncated), artifacts are still written, exit 0. A defect: `tools/ci/docker_smoke.sh` fails
  the build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum: `full_time | wall_clock | sim_fault | host_error`
— four of the six values the starter's schema already declares, with `mercy` and `wipe` deleted along
with the mechanics that produced them.

**Budget guard.** At the start of each turn, if `elapsed + 2 × turnBudgetSeconds >
wallClockBudgetSeconds`, the LLM is switched off for every remaining turn (all seats fall to
`burrow`, microseconds per turn), the remaining ticks run at full speed, and the episode still ends
`complete` / `full_time`. A `budget_guard` record names the turn it fired. This is the starter's
guard at `decide.nim:341-345`, kept.

**A seat that never connects, disconnects, or fails every decision does not end the episode**: its
cog is driven by `burrow` and the episode runs to its natural end with `deadSeats[s] = true`. Nothing
a player container does can stop the clock — `lobbyJoinTimeoutTicks` bounds the lobby and the
per-turn deadlines bound everything after it.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {burrow, scatter}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=burrow` — the starter's "anything unrecognised is the published default" rule in
`baselines.nim`. A scripted policy seated as a champion is a failure state.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/hide-and-seek/anthropic_api_key` — the
hive 2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/hide_and_seek_player.nim` is `src/paintball_player.nim` forked with **no behaviour change**:
read `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries
(240 × 500 ms), send — and **re-send for the first ~10 s of received frames** (the paintball
2026-08-25 slot-sequential-join scar) — the registration blob

```json
{"type":"register","policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"burrow"|"scatter"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at
`MaxPolicyLabelRunes` = 64 runes, then acknowledge frames until the socket closes, **exiting 0 on a
dead socket** (the raid 0.1.3 close-frame race). The `0x85` Player Ready send is kept and is
legitimate for the same reason it is in the starter: this seat sends no inputs at all.

`src/hns/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (via `readCogameUri`) → **none**, in which case the
  client is `disabled = true` and every turn falls back instantly with no network wait, so offline
  certification finishes in seconds.
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 700`. **No `output_config.effort`** when the model string contains `haiku` or
  `4-5`. Bedrock bodies carry `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (outermost balanced
  `{…}`, fence-tolerant, prose-tolerant — `directives.nim:104`) and `truncateRunes` / `sanitizeSay`
  unchanged.

### Cadence, batching, and the wall-clock arithmetic

One turn every **90 ticks**; **12 turns per game, 24 per episode**. At each turn the server builds
every live seat's request body and issues them as **one parallel batch** — never sequentially; this
is a simultaneous-decision game and serial calls would multiply the wall clock by six for nothing.
During prep only the three hiders are live (a frozen, unobserving seeker has nothing to decide and
its call would be a wasted request against the rate cap), during hunt all six are. At most 6 calls in
flight; at most `(4×3 + 8×6) × 2 games × 2 attempts = 240` calls per episode including retries.

```
attempt1Ms                           7.0 s        (curl floors CURLOPT_TIMEOUT to whole seconds)
retryMs                              3.0 s
turnBudgetMs                        16.0 s        (monotonic deadline around the whole turn)
turnSpacingMs                       13.0 s   -> 6 seats x 60/13 = 27.7 req/min  (sidecar cap 30)

24 turns x spacing 13 s, typical (haiku answers in ~3-5 s, so spacing binds)  = 312 s
24 turns x turnBudget 16 s, absolute worst                                    = 384 s
2160 ticks x 6 cogs: fixed-point movement, dirty-rect mask rebuilds, 4500-cell
   shadowcasts, fastMode                                                      =   6 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400 = 100 s cap at 24 fps)       =  15 s typical
gameOverTicks hold + results + replay write (retried uploader)                =  20 s
                                                                              -------
typical total                                                                 = 353 s   < 720 s
absolute worst (384 + 6 + 100 s lobby cap + 20)                               = 510 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                                       = 660 s   -> "deadline"
platform kill (episodeTimeoutSeconds)                                         = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_hns_manifest.nim` asserts it. The `long-hall`
variant runs 28 turns: typical 405 s, worst 574 s — also inside.

**Rate guard.** `turnSpacingMs` pins the steady state at 27.7 req/min, but a turn in which every seat
retries issues 12 requests. The engine therefore keeps a **rolling 60 s request counter**: if issuing
the next batch would push the trailing-60 s count above **28**, the seats that would exceed it skip
the call for that turn and take the `burrow` order with `cause = "rate_guard"`. Bounded, logged,
never a sleep on the episode's critical path (the raid round 2 sidecar-throttle scar).

`fastMode: true` in every variant, as in the starter's paintball variant.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turnBudgetMs`, the rate guard,
`lobbyJoinTimeoutTicks`, mummy's socket timeouts on the serve thread (which runs independently of the
game loop, so a 16 s LLM stall cannot drop a connection or stall `/healthz`), the 660 s engine stop,
and the `gameOverTicks` hold before exit — kept so `/healthz` and `/global` keep answering for a
bounded grace after artifacts are written (the lantern 0.1.3 `/global` ping scar).

On a seat's timeout or parse failure: **retry once** in the next batch; on the second failure that
seat's order for that turn becomes the **`burrow`** scripted order for its current role (the same
proc the `burrow` baseline uses — imported, never duplicated), and a `fallback` record is written
with `cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, rate_guard,
budget_guard, disconnected}`. `results.fallbackTurns[s]` counts them.

**No failure mode leaves a cog unactuated.** The control layer always has an order: this turn's, else
last turn's, else `burrow`'s. A seat that never connects is reported once to
`COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload — exactly
`{"message", "failed_policy_index"}`, nothing else.

**The episode settles early rather than overrunning**: the budget guard drops every seat to scripted
play the moment two more full turns would not fit, and the remaining ticks then run at sim speed
(seconds), so the episode still ends `complete` / `full_time`.

### Per-seat observation: exactly what is visible and what is hidden

The guiding line: **the room and its furniture are public; bodies and intentions are not.** A cog
that walks into a room sees the crates; it does not see the girl behind them, and it never sees the
other trio's plan. That is what makes the fort worth building.

**Visible to a live seat.**

- **The room, once, at its first turn** — the static wall rectangles, the doors (id, position,
  width), the named regions and which doors they join, the pocket anchors, and the seeker pads with
  their `keep_clear_px`. Static for the whole episode; afterwards referred to by id.
- **Every object, every turn** — id, kind, rectangle, `locked` (`none`/`hiders`/`seekers`) and
  `held_by` (an alias or null). Both teams, always. Furniture is 64 px of painted crate in a 720 px
  room; pretending a seeker cannot see it would be a lie the renderer would have to tell too.
- **Everything about your own cog** — position, aim, which region you are in, what you hold, whether
  you are airborne, your last order and its `result`, and your `notes` echoed back.
- **Your two teammates** — alias, position, what they hold, and their last `radio` line. Teammates
  are **not** fogged: a trio in one room can hear each other move, and fogging them would make the
  coordination the game is about impossible at a 3.75 s cadence. (This is a deliberate divergence
  from the starter, whose cogs cannot see their own team; §Sim module records it.)
- **Enemies you can actually see** — every enemy cog inside your cone or bubble right now, and every
  enemy your side saw within the last `HuntMemoryTicks = 72` ticks, tagged `ticks_ago` and with the
  position **as it was when seen** (the starter's `ControlState.knownEnemy` intel window). Nothing
  else about them.
- **What you heard** — every shout within `ShoutRange` of your cog in the last 72 ticks: the team
  that shouted, the text, the jittered position, and `ticks_ago`. This is how a seeker finds a
  careless hider.
- **The public score** — `team_seen_ticks`, `team_hidden_ticks`, the current `margin`, the ticks left
  in the phase, and `seen_now` (is any hider visible to any seeker at this instant). Both trios get
  the same numbers: the scoreboard is public.
- **The fort scan** — which hiders are currently `sealed` (unreachable from the seekers without a
  vault) and how many objects each team has locked.

**Hidden.** Every other trio's orders, notes, radio and prompt; every seat's real player name, policy
name and kind; enemy positions outside your cone, bubble and 72-tick memory; the seed and the
unselected rooms; and, for a **seeker during prep**, absolutely everything — a frozen seeker gets no
observation at all and makes no call.

The observation is a JSON object appended to the user message and is mirrored (minus `your_notes`)
into the replay's `directive` record, so the replay explains every decision.

```json
{
  "you": "HIDER-beta",
  "role": "hider",
  "game": 1, "of": 2,
  "phase": "prep",
  "turn": 3, "turns": 12,
  "clock": {"phase": "prep", "phase_left_s": 4, "hunt_len_s": 30},
  "room": {"name": "warren", "w": 720, "h": 400,
           "walls": [[0,0,720,16],[0,384,720,16],[248,16,16,120],[248,220,16,164]],
           "doors": [{"id":"d1","at":[256,178],"w":56,"axis":"v"},
                     {"id":"d2","at":[470,96],"w":56,"axis":"h"}],
           "regions": [{"id":"r1","name":"west closet","box":[16,16,232,368],"doors":["d1"]},
                       {"id":"r2","name":"hall","box":[264,16,440,368],"doors":["d1","d2"]}],
           "pockets": [{"id":"p1","at":[64,320]},{"id":"p2","at":[648,64]}],
           "seeker_pads": [[684,200],[684,240],[684,160]], "keep_clear_px": 96},
  "you_at": {"pos": [212,301], "aim": 96, "region": "r1", "holding": "box2", "airborne": false},
  "objects": [
    {"id":"box1","kind":"crate","box":[288,160,64,64],"locked":"none","held_by":null},
    {"id":"box2","kind":"crate","box":[188,272,64,64],"locked":"none","held_by":"HIDER-beta"},
    {"id":"pan1","kind":"panel","box":[240,150,32,128],"locked":"hiders","held_by":null},
    {"id":"ramp1","kind":"ramp","box":[600,300,40,80],"locked":"none","held_by":null}
  ],
  "teammates": [
    {"id":"HIDER-alpha","pos":[240,168],"holding":"pan1","last_radio":"pan1 is on d1, locked"},
    {"id":"HIDER-gamma","pos":[96,80],"holding":null,"last_radio":"taking ramp2 to the far corner"}
  ],
  "seen_enemies": [],
  "heard": [],
  "exposure": {"team_seen_ticks":0,"team_hidden_ticks":0,"margin":0.0,
               "you_seen_ticks":0,"seen_now":false,"hunt_ticks_left":720},
  "fort": {"sealed":["HIDER-alpha"],"locked_by_us":1,"locked_by_them":0},
  "your_last_order": {"intent":"push","object":"box2","to":[188,208],"result":"pushing"},
  "your_notes": "box2 seals the gap under pan1, then lock both"
}
```

Field rules. `aim` is brads (256 per turn, 0 = east, counter-clockwise). `margin` is
`(hidden − seen) / huntTicks` rounded to 2 dp, from the **hiding** trio's view, and is therefore
negated in a seeker's observation so that "higher is better for me" always holds. `result` is one of
`moving | arrived | holding | pushing | pushed | push_stuck | grab_failed | locked | unlocked |
lock_refused | vaulted | vault_failed | no_route | chasing | unknown_object` — the driver's honest
report of how the previous order ended, which is what lets a seat recover from a race it could not
see. `objects` is always all eight entries in id order. A seeker's observation is the same document
with `role: "seeker"`, no `fort.sealed` list (it may not be told where the fort is — it is told only
`sealed_count`), and `pockets` present (the room is public) but `seeker_pads` replaced by `your_pad`.

### Reply schema and per-field caps

```json
{"intent": "push", "object": "box2", "to": [188, 208], "at": "d1", "face": [300, 200],
 "say": "on it", "radio": "pan1 on d1, I take the gap under it", "notes": "then lock both"}
```

| Field | Type | Cap / domain |
|---|---|---|
| `intent` | string | **≤ 12 runes**; enum `move_to` \| `hide` \| `watch` \| `chase` \| `push` \| `lock` \| `unlock` \| `vault`, lower-cased, hyphens/spaces normalised to `_` before matching. Anything unknown is repaired to **`watch`** (always actuatable, needs no target) |
| `object` | string | **≤ 8 runes**; required for `push`/`lock`/`unlock`/`vault`; must be one of the eight published ids, and for `vault` a `ramp`. Unknown → repair to the previous order, count `ordersRejected`, report `unknown_object` |
| `to` | `[x, y]` | two numbers (int, float or numeric string — the starter's tolerant `readPoint`), clamped into `[0, w−1] × [0, h−1]` |
| `at` | string | **≤ 4 runes**; a published anchor, door or region id. If present it **wins over** `to` and resolves to that id's point |
| `face` | `[x, y]` | optional; the bearing the driver aims at once it arrives. Clamped like `to` |
| `say` | string | **≤ 10 runes** (`MaxSayRunes` = `ShoutMaxChars`, the starter's cap, unchanged) — an **in-world shout**: heard by *both* teams within 144 px, drawn as a speech bubble |
| `radio` | string | **≤ 96 runes** (`MaxRadioRunes`, new) — the **team** channel: delivered to your two teammates' next observation, drawn in the spectator feed, never audible in-world |
| `notes` | string | **≤ 160 runes** (`MaxNoteRunes`, the starter's cap, unchanged) — private, echoed to this seat only next turn |
| whole reply | bytes | **≤ 4096** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

`MaxSayRunes` stays at the starter's 10 **because the in-world bubble is kept verbatim** — the
starter's chunky 9 px shout font draws a 10-character bubble, and widening it would mean rewriting
the bubble renderer. Coordination lives in `radio` instead, which has no renderer constraint. That
split is also good design: the cheap channel is loud and gives your position away, the expensive one
is private.

**Every string that lands in the replay — `say`, `radio`, `notes`, the policy label, `stopDetail`,
recorded error text — is truncated on RUNE boundaries** via the starter's
`truncateRunes` / `runeSubStr` (`directives.nim:61`), never by byte index. Byte truncation is what
makes a replay that renders in a browser fail a strict UTF-8 parser;
`tests/test_hns_replay.nim` asserts it with 4-byte emoji sitting exactly on every cap.

Unknown top-level keys are ignored. A reply with a valid `say`/`radio` but no `intent` is **usable**:
the cog keeps its standing order and the line is delivered. A reply that is not a JSON object is a
parse failure. An intent whose required argument is missing or unresolvable is **repaired to the
previous order**, counted in `ordersRejected`, and reported next turn in `result`.

### System prompt (fixed, identical for both champions)

```
You are ONE cog in a hide-and-seek room. Three cogs hide, three cogs seek. You are told
which you are. Every 90 ticks (3.75 seconds) you give your cog ONE order and a
deterministic driver carries it out until you change it.

THE ROOM
- A walled room with doorways. You see the walls, the doors, the named regions and every
  piece of furniture at all times.
- FURNITURE: four crates (64x64), two panels (128x32 - one panel covers a whole 56px
  doorway), two ramps. All of it can be dragged. Dragging is 45% slower than walking.
- LOCKING: lock a crate, panel or ramp and the OTHER team can no longer drag it. Only the
  team that locked it can unlock it. Locking is the whole game: an unlocked wall is a wall
  for ten seconds, a locked wall is a wall forever.
- RAMPS: a cog that runs up a ramp aimed at a wall or a crate vaults OVER it - the only way
  past a locked barrier. While you are in the air you are visible over everything, and you
  cannot carry anything. Hiders who lock the ramps in a far corner take that away.
- Nothing may be dragged within 96px of a seeker pad. The seekers always get out.

VISION
Both sides see the same way: a 70-degree cone out to 340px along your AIM, plus a 48px
bubble around you. Walls and furniture block it. You see where you POINT, not where you
walk.

SCORING - the only thing that counts
Every tick of the hunt phase: if ANY hider is inside ANY seeker's cone, the seekers score
that tick. If ALL hiders are unseen, the hiders score it. One hider caught in the open
loses the tick for all three. The score is public to both sides.

THE CLOCK
Phase 1 PREP (15s): seekers are frozen and blind. Hiders build.
Phase 2 HUNT (30s): seekers released, scoring runs.
Then the two teams SWAP SIDES and play the same room again. Your episode score is the
average of the two.

YOUR ORDER (one per turn; your cog keeps it until you change it)
  {"intent":"move_to","to":[x,y]}            walk there
  {"intent":"hide","at":"p2"}                walk there, stop, keep still, watch the door
  {"intent":"watch","to":[x,y]}              stand still and sweep your cone across that point
  {"intent":"chase"}                         go to where an enemy was last seen and sweep
  {"intent":"push","object":"box2","to":[x,y]}  fetch it, drag it there, let go
  {"intent":"lock","object":"box2"}          walk to it and lock it
  {"intent":"unlock","object":"box2"}        walk to it and unlock it (yours only)
  {"intent":"vault","object":"ramp1"}        run up that ramp and jump whatever is past it

TALKING
"say" is at most 10 characters and is SHOUTED OUT LOUD: everybody within 144px hears it and
sees where it came from, including the other team. "radio" is up to 96 characters and only
your two teammates hear it, next turn. "notes" comes back to you and nobody else.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the character { and
end with }. No prose, no markdown, no code fences.
{"intent":"push","object":"box2","to":[188,208],"say":"<=10 chars","radio":"<=96 chars","notes":"<=160 chars"}
```

### Champion #1 — `hns-quartermaster` (owner **daveey**), `PLAYER_PROMPT`

```
Build a room inside the room, and lock it.
AS A HIDER: turn 1, pick the region with the FEWEST doors that no seeker pad is in, radio
its id and claim one door each. Your first order is always "push" - fetch the nearest crate
or panel to your door and drop it IN the gap. A panel covers a 56px door on its own; a
crate needs a second crate beside it. Turn 2, "lock" what you just placed - an unlocked
crate is a ten-second delay, a locked one lasts the whole hunt. Turn 3, if both your
doors are sealed and locked, take the nearest RAMP and push it to the far corner of the
map, then lock it there: a ramp left near your fort is the seekers' key. Only when the
ramps are gone do you "hide" at a pocket inside the fort, facing the sealed door, and then
you do not move again - a moving cog is a seen cog. Never shout during the hunt.
AS A SEEKER: turn 1, radio which door you take and go straight to the region the hiders
did NOT wall up - the open ones are checked in ten seconds. When you find a sealed door,
do not stand there: say "wall" and check whether a ramp is still unlocked; if one is,
"push" it to the sealed wall and then "vault" it. If every ramp is locked, "push" the
crates that are NOT locked out of the gap instead - unlocked furniture is a door with a
delay. Once you have a hider in your cone, "watch" it and radio its position: the tick
counts while ANY seeker sees ANY hider, so the cog that has one holds it and the other two
go find the next one.
```

### Champion #2 — `hns-torchbearer` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Deny sightlines, do not build walls.
AS A HIDER: forts fail when the seekers bring a ramp, so spend prep making the room
UNSEEABLE instead. Turn 1: push a crate into the middle of the longest open sightline in
the room and radio which line you broke. Turn 2: push a second crate 100-150px from the
first so the two together break the diagonal as well. Turn 3: lock both, then take a ramp
to a corner and lock it. Then "hide" behind a crate - not in a pocket a seeker will sweep,
but on the far side of an object it must walk around, and re-choose that side EVERY turn
from where the seekers were last seen: if "seen_enemies" or "heard" puts one within 250px,
your next order moves you to the opposite face of your crate. Keep moving in small steps
and never cross an open region.
AS A SEEKER: split the room and never re-check a region a teammate has cleared. Turn 1
radio the region you take and "watch" its far corner from the doorway before you enter -
your cone is 340px, so standing in a doorway sees the whole small region without walking
into an ambush. Then sweep: "watch" a point, then "watch" a point 90 degrees off it, then
move. When "heard" reports a shout, go straight to it. When you spot a hider, do NOT chase
it out of your cone: "watch" the point it is standing on, radio it, and let a teammate cut
it off - the score counts every tick it is visible, and a chase you lose is worth nothing.
```

### The driver (deterministic, shared by every policy)

`src/hns/control.nim` — the starter's `control.nim`, retargeted. It runs once per cog per tick and is
the **only** producer of input masks. It sits **outside** the determinism boundary exactly as the
starter's does (the recorded masks, not the orders, are what the replay re-plays), so it may use
ordinary floating-point navigation maths.

Kept verbatim from the starter: the `NavCell = 12` nav grid, `buildNavGrid`, `computeField` (BFS flow
field), `fieldFor` with `FieldRefreshTicks = 12` and `MaxCachedFields = 64`, `navSteer`,
`ArriveRadius = 20`, `AimDeadBrads = 4`, `bradsErr`, `StuckTicks = 8` obstacle-sliding, and
`observeEnemies` / `knownEnemy` with `HuntMemoryTicks = 72`. Two changes: the nav grid is rebuilt
when `geometryEpoch` changes (at most once per `FieldRefreshTicks`, and the cached fields are
dropped with it), and the grid is built over `wallMask or objectMask` so a cog paths **around**
furniture, including furniture it cannot move.

| Intent | What the driver does | Finishes with |
|---|---|---|
| `move_to` | flow-field nav to the point; aim along velocity unless `face` is given; stop inside `ArriveRadius` | `moving` → `arrived`; `no_route` if the field cannot reach |
| `hide` | nav to the point (`at` anchor wins), then stop dead and aim at `face`, else at the nearest door of the region it is standing in; zero d-pad from then on | `arrived` then `holding` |
| `watch` | never moves; aims at the point and then oscillates ±32 brads around that bearing at `aimTurnRate` | `holding` |
| `chase` | nav to `knownEnemy`'s last position; on arrival, `watch` that point. With no memory it is `watch` on the current bearing | `chasing` → `arrived` |
| `push` | four stages: (a) nav to the standoff point 18 px off the centre of the object's nearest face; (b) aim at the object centre and hold `C` until `heldBy == slot`; (c) nav so that the **object's** centre reaches `to`/`at`, still holding; (d) inside `ArriveRadius`, or after `pushGiveUpTicks = 120` ticks of zero object displacement, release `C` | `pushing` → `pushed`, else `push_stuck` / `grab_failed` |
| `lock` / `unlock` | nav to the standoff, then press `A` on the first tick the object is inside `lockReach`; then stop | `locked` / `unlocked` / `lock_refused` |
| `vault` | nav to the standoff at the ramp's **foot**, then drive along the ramp axis at full speed until the vault triggers | `vaulted`, else `vault_failed` |

No intent can leave a cog unactuated: an unreachable target degrades to `watch` on the current
bearing, which is a legal mask (`0x00` plus an aim button).

### Scripted baselines (both shipped as fillers; `burrow` is also the server-side fallback)

`src/hns/baselines.nim`, the starter's module retargeted. Both emit the **same** order object an LLM
does, through the same validator, which is what makes the bounded-orders test meaningful. Both
implement **both roles**, because sides swap mid-episode. Neither ever emits `radio` or `notes`;
`burrow` emits one shout per game, `scatter` none.

**`burrow`** — `PLAYER_SCRIPTED=burrow`, and the fallback. Deterministic, first matching rule wins.

*As a hider:*
1. Turn 1: pick `home` = the region containing this cog's spawn pad, or if that region holds a seeker
   pad, the nearest region that does not. Pick `myDoor` = the `homeDoorIndex`-th door of `home`, where
   `homeDoorIndex = (slot div 2) mod doors(home).len` — so the three hiders take different doors.
   Order: `push` the nearest unheld, unlocked object that can cover `myDoor` (a panel if one is within
   `panelReach = 260 px`, else the nearest crate) to `myDoor`'s centre.
2. If that object is at `myDoor` (within 24 px) and unlocked → `lock` it.
3. If it is locked and a **ramp** is within `rampSweep = 300 px` of `home`'s box → `push` that ramp to
   the map corner furthest from `home`, then `lock` it.
4. Otherwise → `hide` at the `pocket` anchor inside `home` nearest this cog, facing `myDoor`.
5. During hunt, if a seeker is known within `flinchRadius = 180 px`, re-issue `hide` at the pocket
   **furthest** from that seeker inside `home`; otherwise keep the standing order.

*As a seeker:* sweep the room's `patrol` anchors in ascending id order, starting at
`(slot div 2)`-th, one `watch` per turn at each anchor with a `move_to` between; if a hider is known
within `chaseRadius = 340 px`, `chase`; if the path to the next anchor is blocked by an **unlocked**
object, `push` it 80 px aside; if it is blocked by a **locked** object and a ramp is unlocked,
`push` the nearest ramp to that object and then `vault` it.

**`scatter`** — `PLAYER_SCRIPTED=scatter`. Deliberately weaker and different in *shape*, so the
ladder gets a spread rather than two versions of one bot: **it never touches the furniture.**

*As a hider:* `hide` at the `pocket` anchor furthest from the seeker pads; every turn after the
first, alternate between that pocket and the second-furthest one — a moving target with no fort. If a
seeker is known within 180 px, `move_to` the furthest pocket immediately.
*As a seeker:* the three seekers split the patrol ring by slot — `(slot div 2)` picks a starting
anchor a third of the way round — and walk it in a fixed rotational direction, one `move_to` per
turn, `chase` when a hider is known within 340 px, and never grab, lock or vault.

Like the starter's `DefaultBaselineParams`, the six tunables (`panelReach 260`, `rampSweep 300`,
`flinchRadius 180`, `chaseRadius 340`, `pushGiveUpTicks 120`, `homeDoorIndex`'s rotation) are a
parameter object chosen by `tools/tune_baselines.nim`'s head-to-head sweep, not guessed;
`tools/ci/baseline_tuning.json` records the sweep's pick and `tests/test_hns_tuning.nim` asserts the
shipped defaults still equal it. The sweep's target is a `burrow`-vs-`scatter` margin in
`[+80, +400]` permille: `burrow` must clearly win as a hider (tool use beats no tool use) without
making the room unhuntable.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/hns/`. The fork is a rename sweep
(`ctf` → `hns`, `CTF_WIRE` → `HNS_WIRE`; a CI grep asserts no `ctf_`/`CTF_` identifier survives
outside comment history) plus the changes below. **The same modules compile twice**: natively into
`/bin/hide-and-seek` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/hns/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop at `server.nim:1407-1417` |
| `src/ctf/sim.nim` (fov half) → `src/hns/vision.nim` | **fork**, one named edit | `castFovOctant`, `computeFovShadowcast`, `applyFovCone`, `refreshPlayerFov`, `fovVisibleAt`, `playerVisibleTo`, `lineOfSightClear` — the whole line-of-sight engine, which is the reason this starter was chosen |
| `src/ctf/sim.nim` (motion half) → `src/hns/motion.nim` | **fork** | `applyInput`, the fixed-point integrator, per-axis slide, player-player collision and bounce |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/hns/` | **fork** (magic + game name only: `CtfReplayMagic = "COWLDCTF"` → **`HnsReplayMagic = "COWLDHNS"`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/hns/` | **fork**, retargeted not rewritten | the per-turn parallel batch, the two deadlines, `turnSpacingMs`, the budget guard at `decide.nim:341-345`, tolerant parsing, the rune caps, repair-don't-reject, the fallback ladder, the nav grid and flow fields |
| `src/ctf/sim_state.nim` → `src/hns/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, `pushFeedDirective`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/hns/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames`, the results JSON builder |
| `src/ctf/events.nim` → `src/hns/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/hns/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline, the vision-cone wire block (`broadcast.nim:532, 813`) — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/hns/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families, `RenderScale` |
| `src/ctf/arena.nim` → `src/hns/room.nim` | **fork, heavily cut** | `selectCtfMap` (the map-install choke point), `mapSpecJson` / `mapFromSpecJson`, `inShape` / `inRect` / `pointInPolygon`, `rasterizeWallMasks`, `validateMapWalkability`, `mapWallAt` — **without** the generator, the symmetry lift, the pool, the endzones, the puddles and the diamonds |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/hns/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps = 24`, `ReplayFps = 24`, `PlayerHalf = 6`, the motion constants, the flatty wire types (field order sacred), `MaxSayRunes = ShoutMaxChars = 10`, `MaxNoteRunes = 160`, `MaxPromptRunes = 4000`, and the new `MaxRadioRunes = 96` |
| `src/ctf/sim_config.nim` → `src/hns/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, the `mapSpec` pinning at `sim_config.nim:844-855` |
| `src/ctf.nim` → `src/hide_and_seek.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/hide_and_seek_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/hns_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*,blue_*}.webp` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its windup, jitter, exposure and accuracy model; hit points, lives, damage,
deaths, respawns and kill/death accounting; spray cans, floor paint, the paint grid, the paint buff,
puddles and stains; King of the Hill and `hillTicks`; hearts/flags/pedestals/carriers/capture zones
and endzones; grenades, the barrage, med kits, shields and cardboard barriers; trenches; perks and
handicaps; four-team play and the `resident`/`visitor` regimes; achievements and the achievement
focus; campaign mode; the first-person PIP and `povBadge`; and **all of the map-generation
machinery** — `mapgen_styles.nim`, `map_pool.nim`, the symmetry lift (`mirrorX`/`rot90`/
`symmetryImages`/`teamImagePoint`), the animated spinning diamonds, `tools/mapkit.nim`,
`tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`,
`scripts/gen_campaign_maps.py`, `docs/MAPKIT.md`, `docs/pool-review.html`. The board here is three
committed authored rooms; every one of those is a config surface the object layer would otherwise
have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`paintbomb`, `medkit`, `shield`, `crew`, `*_crown`, `rig_real/`, `soldier_{green,yellow}*`).

### New modules

- `src/hns/objects.nim` — the object table (`id`, `kind`, `axis`, `pos`, `lockedBy`, `heldBy`), the
  seeded deal, `objectMask` rasterisation with dirty rects, `objectAt` / `objectHit` queries, the
  grab probe, the lock rules, the keep-clear discs, and the vault geometry (`vaultSpanPx` scan,
  landing search, refund).
- `src/hns/phase.nim` — the two-phase clock: `prepTicks`, `huntTicks`, the release transition, the
  per-game reset and the side swap, and the `exposed` evaluation with its `seenTicks` / `hiddenTicks`
  counters.
- `src/hns/fort.nim` — the sealed-fort BFS of tick step 11, the `sealedMask`, and the sealed spans
  the viewer's scrubber and ribbon read.
- `src/hns/room.nim` — described above (the cut-down `arena.nim`) plus the four new spec arrays, the
  load-time validator, the region/door/anchor id tables and the `data/rooms/*.json` loader.
- `src/hns/upstream.nim` — the five borrowed upstream facts with their citation comments, the one
  file `tests/test_hns_upstream.nim` checks.

### Integer arithmetic and determinism

**Everything inside `gameHash` is integer only** — positions, velocities in `MotionScale` units,
object rectangles, tick counters, the exposure counters, the sealed mask. The starter's fov cone
filter uses floating point (`applyFovCone`'s `cos`/`sqrt`), and it is kept **exactly as written**,
byte-for-byte, because it is already the mechanism the starter's own native↔wasm hash chain survives:
the same expression, the same order, the same libm on both targets. What must never happen is a *new*
float expression feeding a hashed value; `tests/test_hns_determinism.nim` greps
`src/hns/{objects,phase,fort,motion}.nim` for float literals and division and requires none.

**One seeded source, consumed in this fixed order before any seat connects** (`setupRng`,
splitmix64 over `seed`):

1. the room, `pool[seed mod 3]`;
2. the **object deal** — the room's `objectSpawns` are shuffled and the first four crate-capable, two
   panel-capable and two ramp-capable candidates taken in that order;
3. the **hider pad assignment** — the room's three hider pads shuffled and dealt to slots 0, 2, 4 in
   ascending slot order (and to 1, 3, 5 in game 2);
4. the **shout jitter** stream, the starter's, used only for the cosmetic offset of a heard shout.

Nothing a seat does can shift any of them. The seed is randomised in `src/hide_and_seek.nim` before
`config.update` (the starter's rule), recorded in the replay config and in `results.seed`;
`results.room` records the chosen room. Two episodes with the same seed and the same masks are
byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDHNS`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (including the full room `mapSpec` and the object deal), then the record
   stream — joins, leaves, **the per-tick input masks** the control layer produced, chat records and
   **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/hns_replay.nim` — which imports the **same**
   `src/hns/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
3. In the browser, `hns_load_replay` runs `parseReplayBytes` + `initReplayRuntime`; `hns_frame`
   re-steps the sim from the recorded masks and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens and surfaced
   as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: the starter's kept fields (tick, phase, gameOverTimer,
   gameStartTick, startWaitTimer, nextJoinOrder, and per cog `x, y, velX, velY, flipH, aimBrads,
   team, joinOrder, color`) — with every deleted mechanic's fields removed — then, **appended after
   them** so the inherited ordering never moves: per cog `holding`, `airborne`, `vaultLeft`,
   `vaultDirBrads`, `lockCooldown`, `pushBlockedTicks`; per object `kind`, `axis`, `x`, `y`,
   `ord(lockedBy)`, `heldBy`; then `ord(phase)`, `prepTicks`, `gameIndex`, `hiddenTicks`, `seenTicks`,
   per-hider `seatSeenTicks`, the `sealedMask` as one `uint64`, `geometryEpoch`; then the starter's
   shout block (address, team, text, tick, x, y), unchanged.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact
   cannot be re-derived from sim state, so the stop is written as one record applied by the *same
   proc* on record and on playback, and `tests/test_hns_replay.nim` runs the record→re-derive check
   for **every** end reason (`full_time`, `wall_clock`, `sim_fault`), not just the healthy one
   (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 2160 hashes + 2160 × 6 mask bytes + ~120 chat records ≈ **40 KB**. Everything else is
re-derived in the browser.

### Documented divergences, and why (mirrored into `docs/RULES.md` §Divergences)

1. **This is a rules-idiom reimplementation of Baker et al., not a port.** MuJoCo physics, the
   3-D geometry, the RL observation vectors and box surfing are not reproduced; the five facts in the
   upstream table are.
2. **Teammates are not fogged** (the starter fogs everyone: "teammates are NOT [visible] — no team
   radio"). Three cogs coordinating a fort at a 3.75 s cadence cannot do it blind, and the `radio`
   channel already gives them a voice; fogging their bodies as well would make every fort an
   accident. Enemies are fogged exactly as the starter fogs them.
3. **Objects are dynamic occluders**, which the starter's static `fovBlocked` grid never had to be.
   The dirty-rect rebuild and `geometryEpoch` cache invalidation of tick step 8 are the whole cost;
   `tests/test_hns_vision.nim` asserts that a full rebuild and an incremental one agree cell for cell.
4. **An airborne cog is visible over furniture.** Visibility of a vaulting target uses
   `lineOfSightClear` against the **static wall mask** rather than the cached fov grid. Without it,
   the vault — the one dramatic act in the game — would happen invisibly behind the crate it is
   jumping.
5. **The keep-clear discs around seeker pads.** Upstream has no such rule because upstream's seekers
   start outside the arena. Without it the dominant hider strategy is to brick the seekers in, which
   is a 1000-permille win and a boring replay.
6. **`maxGames = 2` with a side swap**, and the episode score is the mean of the two games. Upstream
   trains both roles across episodes; a league needs the comparison inside one episode.
7. **The 15 s prep / 30 s hunt split** is this note's, sized by the wall clock (§Decisions), not
   upstream's step counts.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with `turnTicks = 90` and the live-seat set (three during
   prep, six during hunt) in the batch.
2. **Registration interception** — a player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed
   as registration, **not** applied as a shout and **not** written to the replay chat stream; the
   server writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim. Any other chat text from a seat is dropped — cogs speak through `say`.
3. **Wall-clock stop** — the starter's check at `server.nim:1407-1417`, kept, forcing `phase =
   GameOver`, `reason = deadline`, `endRule = wall_clock`, written as the load-bearing stop record.

### The two named edits to `roster.nim`

1. **Aliases.** `cogAlias(slot)` returns `roleLabel(sideOf(slot, gameIndex)) & "-" &
   IdentityNames[slot div 2]`, where `roleLabel(Red) = "HIDER"` and `roleLabel(Blue) = "SEEKER"`. The
   `IdentityNames` array itself (`roster.nim:64`) is unchanged. `showPlayerLabels` is false.
2. **`squadResultsJson` → `roomResultsJson`** — one entry per seat, six entries in every seat-indexed
   array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **Object pools.** New sprite pools `ObjectSpriteBase` (8 objects × body + padlock overlay) and
   `ConeOverlayBase` (6 vision wedges), filled in id/slot order and emitted incrementally like the
   starter's other object families.
2. **Vision cones are broadcast.** The starter already ships a cone block on the global stream
   (`broadcast.nim:532, 813`); here it is emitted for **every** cog every frame with its
   `coneDeg`, `range`, `aim` and an `on` flag (false for a frozen seeker during prep), because the
   cones are the spectator's whole understanding of the game.
3. **Baked room bed.** `arena_floor.png` is tiled and darkened at install with pixie, exactly the way
   the starter bakes endzone paint, and the wall faces are textured from `client/art/walls/*.jpg`
   once — one static bake per room, so the per-frame cost is six cogs, eight objects and the
   overlays.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST`/`PORT`; player sockets
at `/player?slot=<i>&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering
for the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). Global
broadcasts are fire-and-forget so a slow viewer can never stall the episode.

### Results document (closed schema; `roomResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":            ["daveey","daveey-1","Baseline (1)","Baseline (2)","Baseline (1)","Baseline (2)"],
  "aliases":          ["HIDER-alpha","SEEKER-alpha","HIDER-beta","SEEKER-beta","HIDER-gamma","SEEKER-gamma"],
  "team":             ["hiders","seekers","hiders","seekers","hiders","seekers"],
  "scores":           [0.213, -0.213, 0.213, -0.213, 0.213, -0.213],
  "win":              [true, false, true, false, true, false],
  "reason":           "complete",
  "endRule":          "full_time",
  "games":            2,
  "gameMargins":      [426, 0],
  "hiddenTicks":      [513, 360],
  "seenTicks":        [207, 360],
  "huntTicksPlayed":  [720, 720],
  "seatSeenTicks":    [96, 0, 141, 0, 62, 0],
  "sealedTicks":      [540, 0, 180, 0, 0, 0],
  "grabs":            [3, 1, 2, 0, 4, 1],
  "pushedPx":         [412, 96, 388, 0, 502, 74],
  "locks":            [2, 0, 1, 0, 2, 1],
  "vaults":           [0, 1, 0, 0, 0, 2],
  "shouts":           [1, 4, 0, 3, 2, 5],
  "room":             "warren",
  "policyKinds":      ["llm","llm","scripted","scripted","scripted","scripted"],
  "crossPlay":        true,
  "llmTurns":         [24, 20, 0, 0, 0, 0],
  "fallbackTurns":    [0, 1, 0, 0, 0, 0],
  "ordersRejected":   [0, 2, 0, 0, 0, 0],
  "deadSeats":        [false, false, false, false, false, false],
  "finalTick":        2160,
  "seed":             1734029581,
  "stopDetail":       ""
}
```

Every seat-indexed array is exactly 6 long; `gameMargins`, `hiddenTicks`, `seenTicks` and
`huntTicksPlayed` are exactly `games` long. `team[s]` is the seat's **game-1** side (its game-2 side
is the other one, by construction). Adding a key means updating `roomResultsJson`, the manifest's
`results_schema` and `tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld
schemas are closed and undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDHNS`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (`SMOKE_REQUIRE_REPLAY_JSON`, template line 31).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"hide-and-seek/v1","gameVersion":"1","seed":…,"room":"…","names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"orders":[…],"radio":[…],"shouts":[…],"fallbacks":N,"results":{…}}`
  — by brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md`
  documents for prod forensics) and decoding the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                      # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.gameMargins, .results.locks' /tmp/ep.json
  jq -r '[.orders[]|select(.source=="llm")]|length, .fallbacks, (.radio|length)' /tmp/ep.json
  ```
  Require `protocol == "hide-and-seek/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.games == 2`, a non-zero `sum(results.locks)` or
  `sum(results.grabs)` (somebody used the furniture), and the champion seats' orders with
  `source == "llm"`, real intents and non-empty radio lines — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDHNS`, format version, `gameName` `hide-and-seek`, `gameVersion` `1` |
| config JSON | `seed`, `room` (name) **and the full room `mapSpec`**, the object deal (`id`, `kind`, `axis`, spawn `pos`), `num_agents`, `maxGames`, `maxTicks`, `turnTicks`, `prepTurns`, `huntTurns`, `sightRange`, `visionConeDeg`, `visionBubble`, `aimTurnRate`, `carrySpeedPct`, `grabReach`, `lockReach`, `vaultSpanPx`, `keepClearPx`, `players[].name` (real names), `slots[]`, `fastMode`, `showPlayerLabels` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| input masks | one byte per cog per tick — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

The room spec is pinned in the config **as a document, not as a name**, exactly as the starter pins a
generated map (`sim_config.nim:849-855`), so a later edit to `data/rooms/*.json` cannot change what an
old replay renders. The room files' sha256s are also pinned by `tests/test_hns_room.nim` and a change
to one is a `GameVersion` bump.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields;
they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `game`, `turn`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `intent`, `object`, `to`, `at`, `say` (≤ 10 runes), `radio` (≤ 96 runes), `view` (the observation minus `your_notes`) |
| `fallback` | `game`, `turn`, `slot`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end (the starter's `resultRecord`) |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of nineteen kinds:**

`phase` `{phase}`; `gamestart` `{game}`; `release` `{tick}`; `turn` `{n, phase}`;
`order` `{slot, alias, intent, object, to}`; `say` `{slot, text, x, y}`; `radio` `{slot, text}`;
`fallback` `{slot, cause}`; `grab` `{slot, object}`; `drop` `{slot, object, moved_px}`;
`lock` `{slot, object, team}`; `unlock` `{slot, object, team}`; `lockrefused` `{slot, object}`;
`vault` `{slot, object, from, to, ok}`; `spotted` `{seeker, hider, x, y, tick}`;
`lost` `{seeker, hider, ticks}`; `sealed` `{hiders, tick}`; `unsealed` `{hiders, tick}`;
`gameover` `{game, margin, hidden, seen}`; plus `end` `{reason, endRule, scores}`.

`tests/test_hns_events.nim` asserts the emitted set equals exactly this list.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`release`,
`spotted`, `lock`, `vault`, `sealed`, `fallback`, `gameover`.** To keep the scrubber readable a
`spotted` beat is emitted only for (a) the **first** spot of each hider in each game and (b) any spot
that begins an exposure run of ≥ 48 ticks; the rest drive the feed only. `turn`, `order`, `say`,
`radio`, `grab`, `drop`, `unlock`, `lockrefused`, `lost`, `unsealed` and `phase` never make beats.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `PhaseChange, Release, Grab, Drop, Lock, Unlock, LockRefused, Vault,
Spotted, Lost, Sealed, Unsealed, ShoutEvent, TurnStart, Directive, Fallback` and the mandatory
trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed
(`/workspace/ctf/replay-viewer/dist/.` → `/workspace/hns/replay-viewer/dist/.`) — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/hns_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
which is this repo's own starter. **Never a mixture.** Splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks
the viewer silently (cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one
piece: the Worker sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`), the module is
emitted **non-modularized** as `hns_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32
--cc:clang` through `emcc`, `--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`,
`-O2`, `--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`**
(non-negotiable: with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory
protection, so a failed allocation would write through nil into address 0 and corrupt the module's
own globals — the starter's own comment in `config.nims`), `-s FILESYSTEM=1`,
`-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_hns_load_replay,_hns_frame,_hns_input,_hns_packet_ptr,
_hns_packet_len,_hns_mismatch_tick,_hns_error_ptr,_hns_error_len,_hns_stage_ptr,_hns_stage_len`;
and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './hns_replay.js')` in that order (the
starter's line 239, renamed only).

`hns_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress buffer
that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `hns_load_replay` re-simulates the whole episode once headlessly (2160
  ticks × 6 cogs of integer work plus fov — tens of milliseconds in wasm), records the **per-tick
  exposure bit** (the ribbon), the cumulative margin series, the sealed spans, the lock/vault/spot
  beat ticks and the lull spans, then resets and renders frame 0. That is what lets the exposure
  ribbon and the scrubber beats draw at **full width on the first frame** instead of growing in.
- `hns_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `−1`.

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

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes in the starter). Not edited,
  not reformatted; `tests/test_hns_viewer.nim` pins its sha256 against the starter's file. Everything
  this game adds lives in the appended game block. Its `markBeat` / `renderBeatMarkers` /
  `ingestBeats` / `renderClock` / `renderTransport` / `ingestLullSpans` / `renderMomentum` remain;
  `ingestBeats` ignores kinds it does not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (lines 4276-4325), transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density
  system are untouched, and the block is installed through the starter's own splice hook:
  `window.PaintballChrome` is renamed `window.HnsChrome` and its `install(PB_CTX)` /
  `frame(s, ctx, jumped)` / `event(e, s, ctx)` entry points (starter lines 4337, 2075, 3480-3481,
  defined at 4651) are kept with the same signatures. The appended block replaces only the *contents*
  of the scorebug plates, adds the exposure ribbon, the fort panel and the phase clock, and retargets
  the feed rows, the beat rendering, the momentum series and the endcard columns. A test asserts the
  starter's byte prefix is intact up to the documented splice marker and that the file only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades, hearts or bullets. Kept and pinned function-by-function against the
  starter's text by `tests/test_hns_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the
  feed queue and `pushFeed` **including its signature** (`replay_broadcast.html:3558`; the cogball
  0.1.4 latch scar: a signature drift threw mid-replay and latched `static_replay.js` into `failed`),
  `banner`, the beat and lull machinery, the endcard builder, the speed chips, the `?embed=1` path,
  the shout-bubble renderer, and the `window.CTF_WIRE` → `window.HNS_WIRE` rename emitted by
  `tools/gen_wire_constants.nim`. Deleted: every weapon, paint, hill and flag draw call and the FPV
  pipeline. Added: `drawRoom`, `drawObjects` (with the padlock overlay), `drawCones`, `drawVaultArc`,
  `drawExposureRibbon`, `drawFortPanel`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `core.attachMinimap($('minimap-canvas'))` call
    (`replay_broadcast.html:4200`). **Zoom decision: dropped.** The board is a fixed 720 × 400 room
    with no off-frame area; `relayout()` letterboxes it whole at every width (see "Legible at
    360 px"), so per the pin a fixed arena drops `#viewpanel` entirely. `broadcast_core.js` already
    tolerates never being attached: `minimapSurface`/`minimapCtx` (`broadcast_core.js:540-541`) stay
    null and `drawMinimap()` returns on its first guard.
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — the vision cones are
    drawn on the board itself, which shows all six points of view at once and is the whole story; a
    single-cog inset would show less, not more.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture`, `.hillflip`, `.tagout`, `.gamestart`
    and `.gameover` CSS rules (starter lines 919-934, 4431-4443) — those kinds are never emitted here
    (this game's `gameover` beat gets its own new rule alongside the other six).
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with
    `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#bannerlane`, `#killfeed`,
    `#mmwarn`, **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
    `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`,
    `#tick-clock`, `#speedchips`), `#scrub` with
    `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/`#scrub-head`, `#endcard` with
    `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`, and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here
and enforced by a test:

| Starter string (file:where) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (`replay_broadcast.html:3795`) | `<span>Cog</span><span>Unseen</span><span>Seen</span><span>Locks</span><span>Vaults</span>` |
| `<span class="fl-cap">Lives left</span>` (endcard team block, 3793) | `<span class="fl-cap">Ticks unseen</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (scrub graph, 1576) | `<span class="momentum-label">HIDDEN LEAD</span>` |
| `<span class="lives-label">Lives</span>` (scorebug plate, 2241) | `<span class="hidden-label">Unseen</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (1480 / 1833) | "Counting to twenty…" |
| `#clock-caption` "In the locker room" (1499) | "Before the door opens" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (1524) | "Replay hash mismatch at tick N — showing recorded inputs" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline ahead of the playhead (o)" (1564) | "sightings / locks / vaults on the timeline ahead of the playhead (o)" |
| team words `RED`/`BLUE` in `ec-tname`/plates | `HIDERS` / `SEEKERS` plus the colour chip |

**`tests/test_hns_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `spray`, `grenade`, `med kit`, `kill`, `HP` — outside comment blocks, and asserts
**zero** matches; and asserts each replacement string above is present exactly once. A rename that
reintroduces paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (starter lines 4291-4318). **No overlay sits in the transport band**: the board is
laid out between the two bands and every addition here (the exposure ribbon, the fort panel, the feed,
the banners) is positioned inside the board region or in the top band. The **endcard stops at
`var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule at line 1047, kept) so
the scrubber stays clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `hnsBeat(tick, kind, side, label)` — named so it can never shadow
`chrome_common.js`'s `markBeat` alias (the tandem 2026-08-23 hoisting trap) — appends
`<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind emitted and no others**: `.beat-marker.release`, `.spotted`, `.lock`,
`.vault`, `.sealed`, `.fallback`, `.gameover`. The game block never calls `markBeat`, so an
unlabelled div marker cannot appear.

**Playback rate: 1 tick per frame at `ReplayFps = 24`** (speed chips `[1, 2, 3, 4, 8, 16]`, the
starter's `PlaybackSpeeds`, default **1×**). A 2160-tick episode therefore plays for **90 s**, and the
900-tick certification replay for **37.5 s**, which is what lets `viewer_smoke.mjs --soak 10` observe
real advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar).

### Readouts

1. **The room**, drawn edge to edge: the baked floor and textured walls; the eight objects as painted
   crates, panels and ramps, each drawn **with its lock state annotated** (the idea's ask) — an
   unlocked object plain, a locked one with a padlock glyph on its centre and a 2 px outline in the
   locking team's colour, so a spectator can see at a glance which walls are permanent; the six cogs
   in their role kits with a heading chevron; a cog dragging something drawn with a tether line to
   the object it holds; a vaulting cog drawn with a shadow beneath it and an arc trail.
2. **Vision cones** — every cog's cone drawn as a translucent wedge (seekers amber, hiders faint
   blue), clipped by walls and objects exactly as the sim clips it, and **off** for a frozen seeker
   during prep. When a cone touches a hider, that hider gets a red ring and the cone flares. This is
   the game made visible; without it a spectator sees six dots wander.
3. **Phase clock** — `#clock` shows the phase word (`PREP` / `HUNT`) and its countdown as a big
   numeral; `#clock-time` shows `tick 1284/2160 · turn 6/12 · game 2/2`; `#clock-caption` shows
   `unseen 513 · seen 207 · locked 3 · sealed 2`.
4. **Exposure ribbon** (the score, drawn literally) — a full-width strip above the transport band:
   one pixel column per hunt tick, **green when the hiders were unseen and red when they were seen**,
   with the playhead marked and the two games separated by a divider. Filled from the load-time
   pre-scan, so it is complete on the first frame. A red block is a spectator's whole explanation of
   a losing round.
5. **Scorebug plates** — three plates in `#plates-l` (the hiding trio) and three in `#plates-r` (the
   seeking trio): each carries the seat's **real policy name** (spectator side only), its in-game
   alias, its role colour chip, its personal `seen`/`unseen` tick counts, and a `↯` glyph on any seat
   that has taken a fallback. The big central numeral is the running margin in permille.
6. **Fort panel** — a small labelled block in the top band: `LOCKED 3 · SEALED 2/3 · RAMPS LOCKED
   1/2`, re-computed at each turn boundary. It is how a spectator understands why nobody can get in.
7. **Match feed** (`#killfeed`) — plain language, never internal notation: `HIDER-beta drags box2 to
   the west door`, `HIDER-alpha LOCKS pan1`, `SEEKER-gamma tries pan1 — LOCKED BY HIDERS`,
   `SEEKER-alpha VAULTS ramp1 over the crate wall`, `SPOTTED — SEEKER-beta sees HIDER-gamma`,
   `LOST — HIDER-gamma back in cover after 41 ticks`, `FORT SEALED — 2 hiders unreachable`,
   `HIDER-beta: "over here"` (shouts, with the bubble on the board),
   `HIDERS radio: "pan1 on d1, I take the gap under it"`, and
   `SEEKER-beta MISSED THE CALL — scripted order (timeout)`.
8. **Momentum graph** — the starter's `#momentum` SVG retargeted to the cumulative margin
   (hidden − seen) across both games, with the sealed spans shaded green and the exposure runs shaded
   red behind it, and the playhead marked. From the pre-scan, so it draws at full width immediately.
9. **Endcard** — `HIDERS UNSEEN 71% — MARGIN +426` for the game, then the episode line
   `EPISODE +0.213 / −0.213`, the six-row table under the re-mapped header
   (`Cog | Unseen | Seen | Locks | Vaults`), a room summary (`warren · 8 objects · 3 locked · 2
   vaults · 1 sealed fort`), and the seat scores. It stops at `var(--band)` and any seek dismisses it.
10. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
    72 consecutive ticks with no `grab`, `lock`, `vault`, `spotted`, `lost` or `sealed` event, from
    the pre-scan), spoilers switch, tick readout, speed chips, the scrubber with its seven beat
    kinds, and `#mmwarn` on a hash mismatch — all the starter's, verbatim.

### Art

**Real art, no placeholders, no solid-colour squares.** Two sources, both committed:

- **Cog kits — nano-banana** (`playbooks/art-nanobanana.md`, `gemini-2.5-flash-image`, ≤ 3
  generations total). One sheet, two role kits of the Softmax cog, anchored on the starter's own cog
  reference as an `inline_data` part: **HIDER** — matte blue plating, a soft hood/tarp over the
  shoulders, screen face dimmed; **SEEKER** — red plating, a bright headlamp visor and a shoulder
  torch. The sheet is chroma-keyed and split by `scripts/art/split_cog_sheet.py` into
  `data/cog_hider.png` and `data/cog_seeker.png`, committed alongside
  `scripts/art/source/cogs_sheet.png`, and fed to the starter's **existing** `rig_art.nim` rotation
  compositor in place of `data/soldier_{red,blue}.png` (same masters/pivots/scale plumbing, so a cog
  is still baked to a 34 px body on a 72 px canvas, at `RenderScale`, in `SoldierRotations` facings).
  A second generation produces the **furniture sheet** — a wooden crate, a plank panel and a ramp,
  top-down, same style — split into `data/obj_crate.png`, `data/obj_panel.png`, `data/obj_ramp.png`
  and drawn tiled/nine-sliced to each object's rectangle. Roles read at board scale without labels,
  which is the point of the rule.
- **Room and chrome — the starter's shipped assets plus install-time bakes.** The floor is
  `data/arena_floor.png` tiled and darkened 18 %; wall faces are textured from
  `client/art/walls/{wall_h,wall_v}.jpg`; region names, door ids and object ids are set in
  `data/font.ttf`; the padlock glyph, the lock outline, the cone wedges, the vault arc, the exposure
  ribbon and the tether line are procedural in the bake's palette (`data/pallete.png`). The loading
  screen is the starter's locker room (`client/art/lockerroom/bg.jpg` plus the blue/red webps) with
  the caption re-labelled. If the Gemini endpoint is unavailable at build time the builder falls back
  to the starter's `soldier_{blue,red}.png` masters recoloured, and says so in `log.md` — never a
  flat rectangle.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (starter lines 4307-4312). The board's aspect is `720/400 = 1.80`; in a 360 × 203 frame
`boxW / availH = 1.77 < 1.80`, so **width binds**: the board renders at **360 × 200**, i.e. exactly
0.5 board pixels per map pixel, and the whole room is in frame — which is why `#viewpanel` is
dropped. At that scale a cog body is 17 px, a crate 32 px, a panel 64 × 16 px, a doorway 28 px and a
cone 170 px long. Four rules are added and asserted by `tests/test_hns_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps only `alias + name + unseen`; the colour chip shrinks to 6 px and
   the fallback glyph moves inline.
3. Under `.tiny`, **object ids are not drawn on the objects** (the padlock glyph and the coloured
   outline stay — lock state must never be lost), cone wedges drop to 45 % alpha so overlapping cones
   stay readable, and the fort panel drops to `LOCKED n · SEALED n/3`.
4. Under `.tiny`, the exposure ribbon keeps full width but halves in height, and the feed shows three
   rows instead of four. All sizes derive from `--hudscale` so nothing is drawn outside the canvas
   (`--strict-text-bounds` stays on).

---

## Packaging

- **Repo**: `Metta-AI/cogame-hide-and-seek`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `hide-and-seek`; **`game.name` is
  `hide-and-seek`** so the secret namespace `secret://coworld/hide-and-seek/anthropic_api_key`, the
  page slug `softmax.com/hide-and-seek`, the `POST /coworld-league-seeds` body and the docs all agree
  (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name by uppercasing and mapping `-` → `_` (`{{GAME_IMAGE}}` is not a thing —
  lantern 0.1.0). ctf ships two services/two images; this fork uses the one-image / two-entrypoints
  shape because the shared `docker_smoke.sh` and `policies.json` assume a single image (the
  knights-archers precedent):

  ```yaml
  services:
    hide-and-seek:
      image: coworld-hide-and-seek:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder **`{{HIDE_AND_SEEK_IMAGE}}`**.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4` — the starter's `Dockerfile:29`, not the README's local 2.2.10 —
  `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:hide-and-seek
  src/hide_and_seek.nim` → `/bin/hide-and-seek`, and the same for `src/hide_and_seek_player.nim` →
  `/bin/hide-and-seek-player`. (The Nim module tree is `src/hns/`; only the two entry files and the
  binaries carry the dashed slug, because Nim identifiers cannot.) The runtime stage copies both
  binaries, `data/` (including `data/rooms/`), `client/`, `*.json`. `CMD ["/bin/hide-and-seek"]`,
  runtime `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block)
  with the asset list swapped to `data/{arena_floor,ascii,pallete}.png`,
  `data/cog_{hider,seeker}.png`, `data/obj_{crate,panel,ramp}.png`, `data/font.ttf`,
  `data/rooms/*.json`, `client/art/walls/*`, `client/art/lockerroom/*`, `hns_replay.{js,wasm,data}`,
  `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`, `static_replay.js`,
  `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["hide-and-seek", "stealth", "team", "tool-use",
    "line-of-sight"]` (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0); **`episode_timeout_
    minutes: 20` at the top level**, not under `game`.
  - `game.name = "hide-and-seek"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/hide-and-seek"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/hide-and-seek/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 6/6, `players` 6/6, `slots` 0/6 — the tandem 0.1.0 scar). `tokens` is described as
    runner-injected; **no `game_config` anywhere in this manifest contains a literal `tokens` array**
    (matriculate rejects "game_config must not include runner-managed tokens" — knights-archers
    0.1.0), while `config_schema` keeps *requiring* it because the runner injects it. Properties:
    `tokens`, `players`, `slots`, `seed`, `roomPool` (enum `["all","warren","atrium","long_hall"]`,
    default `"all"`), `crates` (0–6, default 4), `panels` (0–4, default 2), `ramps` (0–3, default 2),
    `turnTicks`, `prepTurns`, `huntTurns`, `maxGames`, `sightRange`, `visionConeDeg`, `visionBubble`,
    `aimTurnRate`, `carrySpeedPct`, `grabReach`, `lockReach`, `vaultSpanPx`, `vaultTicks`,
    `keepClearPx`, `attempt1Ms`, `retryMs`, `turnBudgetMs`, `turnSpacingMs`,
    `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `gameOverTicks`, `startWaitTicks`,
    `minPlayers`, `fastMode`, `showPlayerLabels`, `mapSpec`, and **`num_agents` (integer,
    `minimum: 6`, `maximum: 6`, default 6)**. `maxTicks` is **derived**
    (`(prepTurns + huntTurns) * turnTicks`) and is not a config field, so the phase clock and the
    tick cap can never disagree.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}` and
    `endRule: {"type":"string","enum":["full_time","wall_clock","sim_fault","host_error"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-hide-and-seek/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar). Both point at the same document because
    both streams speak Sprite v1 with the same extensions, exactly as the starter declares them.
  - **`game.docs`** = `{"readme": {"type":"text","value":"<the README body, inlined>"},
    "pages": [{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined>"}}, {"id":"objects.md","title":"Boxes, ramps and the lock","content":{"type":"text",
    "value":"<docs/OBJECTS.md inlined>"}}, {"id":"protocol.md","title":"Wire protocol",
    "content":{"type":"text","value":"<docs/PROTOCOL.md inlined>"}}]}` — inlined text so the pages
    render before the repo is indexed.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "200m", memory: "128Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). Two entries, `burrow` and `scatter`, so **every declared
    player occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 6` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0). `slots` alternates
  `red, blue, red, blue, red, blue`, which is what deals slots 0/2/4 the hiding side in game 1:

  ```json
  "variants": [
    {"id": "warren", "name": "Three rooms (3 hiders v 3 seekers, seeded room)",
     "description": "Six cogs in a 720x400 room drawn from three seeded layouts. Three hiders get fifteen seconds alone with four crates, two panels and two ramps: drag them, wall a doorway, lock what you built, and drag the ramps out of reach. Then three seekers walk in with 70-degree torch cones and thirty seconds. Every tick any hider is inside any cone pays the seekers; every tick all three are unseen pays the hiders. Then the trios swap sides and play the same room again.",
     "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},
                                 {"name":"Cog4"},{"name":"Cog5"},{"name":"Cog6"}],
                     "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},
                               {"team":"blue"},{"team":"red"},{"team":"blue"}],
                     "num_agents": 6, "minPlayers": 6,
                     "roomPool": "all", "crates": 4, "panels": 2, "ramps": 2,
                     "turnTicks": 90, "prepTurns": 4, "huntTurns": 8, "maxGames": 2,
                     "sightRange": 340, "visionConeDeg": 35, "visionBubble": 48,
                     "aimTurnRate": 6, "carrySpeedPct": 55, "grabReach": 30, "lockReach": 30,
                     "vaultSpanPx": 112, "vaultTicks": 10, "keepClearPx": 96,
                     "attempt1Ms": 7000, "retryMs": 3000,
                     "turnBudgetMs": 16000, "turnSpacingMs": 13000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "startWaitTicks": 120, "gameOverTicks": 240,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "long-hall", "name": "The long hall (nothing to hide behind until you build it)",
     "description": "One open hall, two stub walls, and six crates, three panels and two ramps. There is no pocket to sit in: a hider who does not build has nowhere to be. Prep runs six turns instead of four, so a trio that can plan a wall, lock it and hide the ramps has time to do it - and a trio that cannot is visible for thirty straight seconds. Sides swap and the hall is played again.",
     "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},
                                 {"name":"Cog4"},{"name":"Cog5"},{"name":"Cog6"}],
                     "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},
                               {"team":"blue"},{"team":"red"},{"team":"blue"}],
                     "num_agents": 6, "minPlayers": 6,
                     "roomPool": "long_hall", "crates": 6, "panels": 3, "ramps": 2,
                     "turnTicks": 90, "prepTurns": 6, "huntTurns": 8, "maxGames": 2,
                     "sightRange": 380, "visionConeDeg": 35, "visionBubble": 48,
                     "aimTurnRate": 6, "carrySpeedPct": 55, "grabReach": 30, "lockReach": 30,
                     "vaultSpanPx": 112, "vaultTicks": 10, "keepClearPx": 96,
                     "attempt1Ms": 7000, "retryMs": 3000,
                     "turnBudgetMs": 16000, "turnSpacingMs": 13000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "startWaitTicks": 120, "gameOverTicks": 240,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 6` again, inside `certification.game_config`, and exactly
  six players so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS
  == 6` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks), with **both** declared
  players seated and both sides mixed:

  ```json
  "certification": {
    "players": [{"player_id":"burrow"},{"player_id":"scatter"},{"player_id":"burrow"},
                {"player_id":"scatter"},{"player_id":"burrow"},{"player_id":"scatter"}],
    "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},
                                {"name":"Cog4"},{"name":"Cog5"},{"name":"Cog6"}],
                    "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},
                              {"team":"blue"},{"team":"red"},{"team":"blue"}],
                    "num_agents": 6, "minPlayers": 6, "seed": 42,
                    "roomPool": "warren", "crates": 4, "panels": 2, "ramps": 2,
                    "turnTicks": 90, "prepTurns": 2, "huntTurns": 3, "maxGames": 2,
                    "sightRange": 340, "visionConeDeg": 35, "visionBubble": 48,
                    "aimTurnRate": 6, "carrySpeedPct": 55, "grabReach": 30, "lockReach": 30,
                    "vaultSpanPx": 112, "vaultTicks": 10, "keepClearPx": 96,
                    "turnSpacingMs": 0, "wallClockBudgetSeconds": 240,
                    "lobbyJoinTimeoutTicks": 600, "startWaitTicks": 0, "gameOverTicks": 24,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  Two games of `(2 + 3) × 90 = 450` ticks is **900 ticks**, about a second of sim but **37.5 s of
  playback**, which the viewer soak needs — and it exercises the side swap in CI, not only in the
  league. `turnSpacingMs: 0` because certification runs with no API key and every seat is scripted.
  Seed 42 is asserted by `tests/test_hns_engine.nim` to produce a fixture episode with at least one
  `grab`, one `lock` and one `spotted` event, so the smoke replay always exercises the object layer.
  The certify step in `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 covers
  start + connect grace + play + linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/hide-and-seek-player"`,
  following the starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"hns-quartermaster","run":"/bin/hide-and-seek-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"quartermaster"}},
   {"name":"hns-torchbearer","run":"/bin/hide-and-seek-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"torchbearer"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"hns-burrow","run":"/bin/hide-and-seek-player",
    "env":{"PLAYER_SCRIPTED":"burrow","PLAYER_POLICY_LABEL":"burrow"}},
   {"name":"hns-scatter","run":"/bin/hide-and-seek-player",
    "env":{"PLAYER_SCRIPTED":"scatter","PLAYER_POLICY_LABEL":"scatter"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `burrow` and `scatter`, and their
  versions must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the
  **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps
  the template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `hide-and-seek`,
  `<IMAGE>` → `coworld-hide-and-seek`, `<SEATS>` → **`6`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0`
  (§Server) and `--soak 10` added to the `viewer_smoke.mjs` invocation. `coworld-release.yml` and
  `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on the certify step.
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed **executable**
  (mode 100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_hns_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in
both debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_hns_sim.nim`)
1. `phase clock` — the phase is `prep` for exactly `prepTurns × turnTicks` ticks and `hunt` after;
   `release` fires exactly once per game at `tick == prepTicks`; seeker input masks are zero for every
   prep tick and non-zero-capable after; no exposure tick is counted during prep.
2. `two games, sides swapped` — after game 1 the sides flip, aliases re-prefix, cogs return to the
   pads of their new role, the object deal is re-applied identically, and the per-game counters reset
   while the episode totals accumulate.
3. `grab` — `C` binds the first object along the aim probe within 30 px and nothing beyond it; two
   cogs contesting the same object in one tick resolve to the lower slot with the other reporting
   `grab_failed`; the object never has two holders; releasing `C`, a phase change and a game end all
   drop it.
4. `push` — a held object translates by exactly the holder's integer delta; a push into a wall,
   another object, a third cog or a keep-clear disc moves **neither** body and increments
   `pushBlockedTicks`; the per-axis slide lets a crate run along a wall; the holder's speed is
   `carrySpeedPct` of normal, measured over 100 ticks.
5. `lock` — locking sets `lockedBy` to the actor's team; the other team's grab and unlock are refused
   and emit `lock_refused`; the owning team can unlock; `lockCooldown` blocks a second toggle for 24
   ticks; a locked object is still solid and still opaque to both teams.
6. `keep-clear` — no sequence of pushes can place any object within 96 px of a seeker pad, over 200
   randomised push attempts; and a room whose objects all start outside the discs never has one
   inside them.
7. `vault` — a cog running up a ramp at ≥ `vaultMinSpeed` with a ≤ 112 px span beyond the head goes
   airborne for exactly 10 ticks, crosses, and lands clear; a > 112 px span does not trigger; a
   blocked landing refunds it to the foot with `vault_failed`; an airborne cog cannot grab or lock;
   an airborne cog **is** visible across an intervening crate and **is not** visible across a static
   wall.
8. `vision` — a hider directly behind a crate is invisible to a seeker 40 px away and visible when
   the crate is dragged aside on the very next tick (the dirty-rect/epoch path); the cone is 35° each
   side of aim and dies at exactly `sightRange`; the 48 px bubble does not see through a wall; a
   frozen seeker's fov is never computed during prep.
9. `incremental geometry equals full rebuild` — after 500 randomised object moves, `objectMask`,
   `fovBlocked` and every cog's visibility set are cell-for-cell identical to a from-scratch rebuild.
10. `exposure counting` — over a scripted world, `seenTicks + hiddenTicks == huntTicksPlayed` exactly;
    a tick with two seekers seeing two hiders counts **once**; `seatSeenTicks` counts per hider;
    `spotted`/`lost` fire exactly on transitions.
11. `sealed scan` — a hider walled in by hider-locked crates is `sealed`; the same wall unlocked is
    **not** sealed; a wall with a gap the size of a cog is not sealed; the scan runs only at turn
    boundaries and at the release tick.
12. `scoring` — `scorePermille` matches the formula for 500 randomised end states, the six values sum
    to exactly 0, `scores` is in `[−1, +1]`, `win` is `scorePermille > 0`, and an all-zero margin
    leaves every `win` false.
13. `end conditions` — `full_time`, a forced wall-clock stop and a forced fault each produce the right
    `endRule` and the right `reason`; a deadline in the middle of game 2's hunt settles with
    `huntTicksPlayed[1] < huntTicks` and still sums to zero.
14. `no new floats in hashed code` — a source grep over `src/hns/{objects,phase,fort,motion}.nim`
    finds no float literal, no `/` and no `sqrt`; `vision.nim`'s inherited `applyFovCone` maths is
    whitelisted by exact line range and asserted byte-identical to the starter's.
15. `tick budget` — a full 2160-tick, six-cog, all-scripted episode completes in < 15 s in a release
    build, and no single tick exceeds 8 ms.

**Room and upstream fidelity**
16. `tests/test_hns_room.nim` — for each of the three committed rooms: the sha256 equals the pinned
    literal; the spec parses through `mapFromSpecJson`; every wall is in bounds; every door joins
    exactly two regions; every anchor and `objectSpawn` is walkable with full clearance; every region
    is reachable from every seeker pad with no objects placed; ≥ 14 `objectSpawns`, ≥ 6 pockets,
    3 hider pads, 3 seeker pads; and the walkability sweep (`validateMapWalkability`) passes.
17. `tests/test_hns_upstream.nim` — the shipped constants in `src/hns/upstream.nim` equal the table at
    the head of this note: the two-phase clock with immobilised, unobserving seekers; the ±1/tick
    all-hiders-hidden team reward; cone-based visibility; movable, lockable objects unlockable only by
    the locking team; ramps as barrier-crossers. A constant edited without editing the citation fails.
18. `tests/test_hns_seeding.nim` — the room is `pool[seed mod 3]`; the object deal is a pure function
    of the seed and the room; hider pads are dealt from the same stream; and **none** of it changes
    when seat behaviour changes (the anti-collusion pin).
19. `tests/test_hns_determinism.nim` — re-simulate from the replay's seed and recorded masks alone on
    a fresh sim; identical final tick, object positions, lock states, exposure counters and per-tick
    `gameHash`.

**Bounded orders / legality on the scripted baselines** (`tests/test_hns_control.nim`)
20. `baselines are bounded` — for 200 pseudo-random world states (both phases, both games, every
    slot, both roles, all three rooms, objects locked and held in every combination) and for **both**
    `burrow` and `scatter`: the returned order has an `intent` in the enum, an `object` that is one of
    the eight published ids and legal for that intent, a `to`/`at` inside the board, `say` ≤ 10 runes,
    `radio` and `notes` empty, and a serialised directive ≤ 1024 bytes. A baseline that ever proposes
    an illegal or unbounded order fails the build.
21. `driver never emits an illegal mask` — over the same states, every compiled mask uses only the
    d-pad, `A`, `B`, `Select` and bit 7; no mask presses `A` while `lockCooldown > 0`; no order can
    leave a cog with no mask; and a target inside a wall degrades to `watch`, never to a stuck cog
    pressing the same direction forever (the starter's `StuckTicks` path, exercised).
22. `fallback is the burrow proc` — the decision engine's fallback path and the `burrow` baseline
    resolve to the same proc, so they cannot drift.
23. `reply validation` — the validator accepts the schema, **repairs** an unknown intent to `watch`
    and an unknown object to the previous order, clamps `to`, resolves `at` over `to`, accepts a
    `say`-only reply, rejects a non-object, truncates `say`/`radio`/`notes` on **rune** boundaries at
    10/96/160 with 4-byte emoji sitting exactly on each boundary, caps the read at 4096 bytes, and
    never leaves a cog without an order.
24. `baseline tuning is the swept pick` — the shipped six tunables equal `tools/ci/baseline_tuning.json`
    (the starter's `test_tuning` pattern; `ci.yml` re-runs the sweep with `--check`), and the recorded
    `burrow`-vs-`scatter` hiding margin is inside `[+80, +400]` permille.

**End-to-end episode writing a replay** (`tests/test_hns_engine.nim`)
25. `episode writes artifacts` — run a real six-seat episode (`warren`, `prepTurns 2`, `huntTurns 3`,
    `maxGames 2`, all seats scripted, no API key so the LLM client is `disabled`) against a temp-dir
    `COGAME_*` URI set; assert `results.json` and the `.replay` are written, `reason == "complete"`,
    `endRule == "full_time"`, `games == 2`, `sum(scorePermille) == 0`, and the results key set equals
    the manifest's `results_schema` key set **exactly**.
26. `the cert seed is interesting` — seed 42 on `warren` yields at least one `grab`, one `lock` and
    one `spotted` event inside the fixture's 900 ticks, so the CI smoke replay always exercises the
    object layer and the exposure path.
27. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure
    payload.
28. `budget guard and rate guard settle early` — with each guard forced, the episode finishes
    `complete` / `full_time`, not `deadline`, and the matching record names the turn.

**Replay** (`tests/test_hns_replay.nim`)
29. `record then re-derive, every end reason` — for `full_time`, `wall_clock` **and** `sim_fault`,
    record an episode and re-derive it from the bytes; assert identical hashes at every tick
    **including the stop tick** (the particle-worlds scar).
30. `replay is self-sufficient` — the bytes alone yield seat names, aliases, policy kinds, the full
    config **including the room `mapSpec` and the object deal**, the seed, every mask, every chat
    record and the result; deleting `data/rooms/` from disk does not change what the bytes render.
31. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports
    `protocol == "hide-and-seek/v1"`.
32. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`,
    kept.

**Manifest** (`tests/test_hns_manifest.nim`)
33. `manifest pins` — `num_agents == 6` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens`
    in any `game_config`; `len(player) == 2` and every declared player seated in
    `certification.players`; `len(certification.players) ==
    len(certification.game_config.players) == 6`; every `slots` array alternates red/blue and is 6
    long; every array in `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes`
    top-level; both `game.protocols.player` and `.global` present as `{"type","value"}` objects;
    `game.docs.readme` + three `pages`, every value non-empty text; `game.description` present and
    `game.tags` absent; ≥ 3 top-level tags; `player[].resources.limits.cpu >= "1"`; every
    `wallClockBudgetSeconds ≤ 660`; the derived `maxTicks` of every variant ≤ 3000; **and every
    variant's `game_config` actually constructs a valid `GameConfig`, loads its room pool, deals its
    objects and produces the object counts and phase lengths this note claims** (the collab-cooking
    0.1.1 scar: test every variant, not just the fixture).
34. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` —
    the collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_hns_viewer.nim`, static assertions in the `test` job)
35. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals the starter's,
    pinned as a literal (40 022 bytes).
36. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker and only appends after it; `broadcast_core.js`'s kept procs are
    byte-identical to the starter's, `pushFeed`'s signature included.
37. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap); the beat builder is `hnsBeat`, never
    `markBeat`.
38. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{release, spotted, lock, vault, sealed, fallback, gameover}`.
39. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()`
    sets `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the
    band; the four 360 px rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`,
    `#fpv*`, `#povBadge`, …) appear nowhere.
40. `endcard labels` — `tests/test_hns_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
41. `label manifest` — the starter's `test_label_contract` pattern: the emitted sprite-label
    vocabulary (`crate`, `panel`, `ramp`, `locked crate`, …, `own aim <brads>`) equals
    `tests/label_manifest.txt`, regenerated in the same commit as any label change.
42. `events are the closed enum` — `tests/test_hns_events.nim`: the set of kinds `stepEvents` can emit
    equals exactly the nineteen listed in §Server, and every kind used by the appended game block is
    in that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**
43. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`, no substitutions) is run by **`ci.yml`'s
    `wasm-viewer` job**, which `needs: docker-smoke` and runs it against **the replay `docker-smoke`
    produced** (downloaded as the `smoke-replay` artifact), in headless chromium (Playwright pinned
    1.55.0 in both the npm module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay"
    --timeout 90 --soak 10 --strict-text-bounds`. It fails the job unless
    `data-replay-loaded="true"` (or the bridge `ready` posted after it) arrives, the clock/tick
    readouts **advance** across the soak, and `canvas_text.never_inside == 0` — this is a fixed board,
    so `--strict-text-bounds` stays on.
44. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `radio` at all**,
    so the smoke replay can never exercise the feed's radio path (the cogchemists 2026-08-24 scar).
    The fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims
    only the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) —
    driving the real page with a full-cap 96-rune `radio` and 10-rune `say` on all six seats, three
    locked objects with padlocks, an active sealed fort, a vault in flight, two overlapping cones on
    one hider, and a full exposure ribbon, at several canvas widths including 360 px.
45. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.

---

## Out of scope (v1)

- **Box surfing.** Baker et al.'s hiders learn to stand on a box and drag it under themselves to
  ride over walls; it is an artefact of MuJoCo's 3-D contact model and has no meaning in a top-down
  2-D sim where a cog and a crate cannot occupy the same pixel. The autocurriculum this game ships is
  **fort → ramp → lock**, which is the part of the story that survives the projection. Adding a
  "stand on" state would need a height axis in the collision model, the fov and the renderer.
- **Seat counts other than 6, and one policy commanding several cogs.** `num_agents` is fixed at 6 in
  every variant and in the cert fixture, for the batch-size and wall-clock reasons in §The game. A
  2v2 or a squad-per-seat variant is a different manifest and a different cadence.
- **Rotating a held object.** Objects are axis-aligned and keep the orientation they were dealt.
  Rotation would make every push a polygon rasterisation and a fresh fov rebuild per tick, and it
  would let a single panel do the job of three. Panels ship in both orientations instead, chosen by
  the seeded deal.
- **Tagging, catching, damage or elimination.** There are no weapons, no hit points and no way to
  remove a cog from the board. Being seen is the only thing that happens, which is what makes the
  ±1/tick rule the whole game.
- **Procedurally generated rooms.** Three committed authored rooms with pinned sha256s, chosen by
  seed. A generator would reintroduce degenerate layouts, an unpinnable topology and a legibility
  risk at 360 px.
- **Scoring anything but exposure.** `sealedTicks`, `locks`, `grabs`, `vaults`, `pushedPx` and
  `shouts` are measured, recorded in `results`, shown on the endcard and in the feed, and
  deliberately **not** in `scores`: weighting them would need a magnitude the idea does not pin and
  would break the exact zero sum the league ranks on.
- **A per-hider individual reward.** Upstream's reward is team-based and so is this one. A per-cog
  term would reward a hider for sacrificing a teammate to a cone, which is the opposite of the game.
- **Fogging teammates, and a fog-of-war minimap for spectators.** Teammates are visible to each other
  (§Sim module → divergences) and the spectator sees the whole room with every cone drawn; a
  per-seat fogged spectator view is a second renderer.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the
  hosted spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, bullets, hit points, lives, respawns,
  spray, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches, puddles,
  perks, handicaps, achievements, four-team play, campaign mode, the first-person PIP, the procedural
  map generator, the map pool, the map editor and mapkit — all deleted, not disabled (§Sim module),
  and none of them return in v1.
