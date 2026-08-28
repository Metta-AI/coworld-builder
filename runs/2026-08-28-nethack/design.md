# cogame-nethack — design note (2026-08-28)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` importing and re-exporting the sim
modules, `sim_types.nim` owning `GameVersion` (`src/ctf/sim_types.nim:21`) and `TargetFps* = 24`
(`:376`) with its prepend-only changelog-comment discipline, the flatty wire types whose field order
is sacred, and the rune caps `MaxNoteRunes` / `MaxSayRunes` / `MaxPromptRunes` (`:747`, `:794-795`,
`:799`)); the mummy HTTP/websocket server implementing the Coworld contract, including its
`wallClockBudgetSeconds` stop at `src/ctf/server.nim:1407-1417`; the `decide.nim` / `directives.nim`
/ `llm.nim` / `baselines.nim` / `control.nim` commander layer with its one-batch-per-turn shape
(`src/ctf/decide.nim:427` `engine.client.curl.makeRequests`), its `attempt1Ms` / `retryMs` /
`turnBudgetMs` / `turnSpacingMs` deadlines (`src/ctf/decide.nim:386-389, 406, 421-427`), its budget
guard (`:328-346`), its tolerant JSON extraction (`src/ctf/directives.nim:102`), its rune truncation
(`src/ctf/directives.nim:61-90`) and its fallback ladder with the exact log phrasing
(`src/ctf/decide.nim:463` "failed, falling back if it fails again" for attempt 1, `:491`
"falling back" only on the second failure); the binary `COWLDCTF` replay of *inputs plus a per-tick
`gameHash`* (`src/ctf/replays.nim:142`), re-simulated by **the same sim module** compiled to wasm by
`replay-viewer/config.nims`; the `client/` broadcast chrome (`chrome_common.js` + `broadcast_core.js`
+ `replay_broadcast.html` with its `window.PaintballChrome.install(PB_CTX)` splice hook at
`client/replay_broadcast.html:4330-4337` and the game-block banner at `:4344`); nimby + `Dockerfile`
+ `Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh`; and the Nim test suite with its four
shards (`tests/shard_1..4.nim`, `tests/config.nims`).

Starter choice, one line: **this is a real-time tick loop whose rules are written into this repo and
whose single seat is an LLM dispatcher over a deterministic per-tick driver — the first row of the
starter table** (`prompts/10-design.md` §Starter table: "any real-time game loop (grid OR continuous
physics), new rules written for this coworld"). It is deliberately **not** the `cogame-moba`
bit-exact-port row, and that is a **rail the coordinator already set, which this note states and does
not revisit**: this coworld does **not** vendor, embed or bit-exactly port NLE, NetHack's C source or
MiniHack. NetHack is 40 years of C with its own RNG, its own tty layer and a 250 kLOC surface;
NLE/MiniHack wrap it in Python. Embedding any of them means a simulator that **cannot compile to
wasm**, which makes the static replay viewer — a non-optional pin
(`playbooks/make-coworld.md` §Phase 0) — impossible. What this repo implements is the *problem class*
NetHack poses: a **procedurally generated, seeded, multi-level roguelike dungeon** with monsters,
items, hunger, traps, permadeath, a descend-the-stairs depth ladder and a score, presented through a
**text-native observation** (a rendered ASCII map + a message line + a status line), written as its
own deterministic **integer Nim sim** for this coworld. Every deliberate divergence from real NetHack
is named in §Sim module → "Documented divergences" and mirrored into `docs/PORTING-NETHACK.md`. The
precedent for forking paintbot for a procedurally generated grid game is deep and recent: minigrid,
procgen, atari-57, vizdoom-deathmatch, flatland, rware-warehouse, magent-battle, smac-starcraft-micro.

Where this note departs from coworld-ctf it says so. The departures are: the rules are roguelike
dungeon rules, not paintbot's (§Sim module lists what is deleted); the board is a **48 × 18 integer
cell grid per dungeon level**, authored by seeded generators, so ctf's pixel arena, procedural pixel
map generator, map pool, map editor and mapkit are deleted; there is **one seat, not eight**, and no
teams; the seat is **partially observed** by NetHack's own lit-room / dark-corridor rule, so ctf's
raycast fog and first-person pipeline are replaced by a much simpler exact-visibility rule; the board
is **larger than the frame**, so unlike most paintbot forks this one **keeps `#viewpanel`** (zoom bar
+ minimap); and `MaxSayRunes` / `MaxNoteRunes` are re-pinned (§Decisions → reply schema).

### Source idea (verbatim)

> SA NetHack — the hardest game in RL: procedurally generated dungeons, permadeath, and forty years of lore
>
> Single-agent coworld over the NetHack Learning Environment (NLE) and MiniHack. Full NetHack: ASCII dungeon, hundreds of monsters/items/spells, hunger, permadeath; tasks: score, staircase depth, gold, eat, oracle; the 2021 NetHack Challenge left strong symbolic bots (AutoAscend) as fillers. MiniHack: small authored levels (corridors, lava crossings, monster rooms, skill tasks) as a ladder. Observations are glyphs + message line + stats — text, which makes this the flagship LLM-agent environment (BALROG, NetPlay).
>
> Seats: 1
> Motive: score / depth attack
> Policy interface: keystroke per turn over a text observation; LLM native; symbolic bots as baseline
> Fills gap: long-horizon, text-observable, procedurally generated — the best single-agent test of an LLM policy's planning and memory on the site
> Integrity: seeded dungeons per round; action-log replay verification; hard episode cap.
>
> Replay plan (watchability): ttyrec playback (native); a 'dungeon level reached' ladder and a death-cause feed.
>
> Source: github.com/facebookresearch/nle, minihack; NetHack Challenge 2021.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time tick loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-nethack` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=delver\|bumbler`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance, byte-for-byte `chrome_common.js`, starter art + install-time bakes) |
| Two name spaces | §The game (in-game alias `Alpha the Digger`; real policy names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (typical 227 s, worst 645 s, engine stop 660 s, budget 720 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 1`, three times |
| Per-turn LLM call budget stated (single seat) | §Decisions (exactly one request per turn, two with the retry; ≤ 110 per episode) |
| Replay bytes self-sufficient | §Server (config JSON, join, per-turn plans, chats, per-tick hashes, seed, variant) |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |
| Seeded dungeons per round; action-log replay verification; hard episode cap (the idea's integrity note) | §The game → Integrity; §Server → Determinism |

---

## The game

One cog, alone, at the top of a dungeon it has never seen. Below it are eight levels of rooms and
corridors that were generated out of this episode's seed and exist nowhere else. It has a dagger, a
food ration, a suit of leather armour and twelve hit points. Rats, jackals, kobolds, gnomes and
worse are down there; so is gold, so is food, so is the Oracle, and so — on every level — is a
staircase down. It gets hungrier every turn. It has **one life**: nothing in this game restores,
resurrects or reloads. The only number the league reads is **how deep it got**; gold, experience and
three named deeds are the tie-break.

The whole game is the gap between what the cog can see and what it must remember. It reads an ASCII
map of what it has explored, one message line of what just happened, and one status line of what it
is. Everything else — the shape of the level below, what is behind that door, whether the smoky
potion is healing or sleeping, whether the thing that just bit it is worth fighting — has to be
inferred, written down in a 400-rune note, and carried forward. That is exactly the long-horizon,
text-observable, procedurally generated test the idea asks for.

### Seats and aliases

- **`num_agents` = 1.** Exactly one seat, always — in both manifest variants and in the certification
  fixture. This is the idea's own "Seats: 1", and it is what the game is: NetHack is a single-player
  roguelike and a second seat would have nothing to do. Every episode is a solo descent; policies are
  compared across episodes, never within one.
- **Two name spaces.** In-game the seat is **`Alpha`** — `IdentityNames[0]` from the starter's
  `src/ctf/roster.nim:64-65`, title-cased by `seatAlias(slot)` — and it is styled in-world as
  **`Alpha the Digger`** (a NetHack rank title; `the Digger` is a constant, not a name). That alias
  is the only name that appears in an observation, in a prompt, in a `say`, in a message line or on
  the board. The seat's **real policy/player name** (`daveey`, `daveey-1`, `Baseline (1)`) lives only
  in `results.names`, in the replay's join record, and spectator-side in the viewer's scorebug plate,
  the tombstone endcard and the feed captions. `showPlayerLabels` is **false**, as in the starter's
  paintball variant, so nothing drawn on the board leaks an identity. With one seat there is nobody
  to meta-game against, but the pin is satisfied both ways, not either way: the alias is what the
  model sees, the real name is what the spectator sees.

### The board — one dungeon level

Every level of every variant is the **same size**: **48 columns × 18 rows** of cells, `levelW = 48`,
`levelH = 18`, indexed `(x, y)` with `x` the column `0 … 47` (west → east) and `y` the row `0 … 17`
(north → south). `(0, 0)` is the north-west corner. **The entire border ring is solid rock**, so the
diggable interior is 46 × 16. One level size everywhere, forever: it is what makes `travel x y` a
stable contract in the reply schema and what lets the viewer's camera arithmetic be written once
(§Viewer → Legible at 360 px). This is a **documented divergence**: real NetHack maps are 80 × 21,
and 80 columns cannot be drawn legibly in a 360 px-wide embed.

**A cell holds one terrain, optionally one trap, optionally one item stack, optionally one monster.**
The closed terrain enum and its glyphs — these are NetHack's glyphs, not inventions:

| Terrain | Glyph | Passable | Sight | Notes |
|---|---|---|---|---|
| solid rock | ` ` (space) | no | blocks | also what an unseen cell renders as |
| room floor | `.` | yes | clear | |
| corridor | `#` | yes | clear | dark: sight radius 1 |
| horizontal wall | `-` | no | blocks | |
| vertical wall | `\|` | no | blocks | |
| open doorway | `'` | yes | clear | a doorway with no door in it |
| closed door | `+` | **no** | blocks | walking into it **opens** it (NetHack's `autoopen`) |
| locked door | `+` | **no** | blocks | identical glyph; only the message line says it is locked; needs `kick` |
| secret door | ` ` | no | blocks | looks like solid rock until `search` finds it |
| staircase down | `>` | yes | clear | |
| staircase up | `<` | yes | clear | |
| lava | `}` | yes | clear | **entering it is instant death** (`burned`) |
| discovered trap | `^` | yes | clear | the glyph a trap shows *after* it is discovered |

Item glyphs (five classes, closed): **`$` gold**, **`%` food**, **`!` potion**, **`)` weapon**,
**`[` armour**. Monster glyphs are the eleven letters in the monster table below, plus **`O` the
Oracle**. The cog is **`@`**. A cell that holds both a monster and an item renders the monster; a
cell that holds the cog renders `@`.

### The cog

`hp` / `maxHp` (start **12 / 12**), `ac` (**armour class, lower is better**, `ac = 9 − armourBonus`,
so 7 in the starting leather), `xlevel` (start 1), `xpPoints` (start 0), `gold` (start 0),
`nutrition` (start **900**), a position `(x, y)`, a current `depth`, an inventory of at most **26**
stacks lettered `a … z`, and a status set drawn from `{confused, paralysed, stuck, trapped}`.

**Starting inventory** (identical every episode — no character generation):
`a` — a dagger (wielded; damage die 4, hit bonus +1);
`b` — a food ration (800 nutrition);
`c` — leather armour (worn; armour bonus 2).

**Hunger.** `nutrition` falls by **1 every tick**. States: `Satiated` > 1000; `Not Hungry`
150 … 1000; `Hungry` 50 … 149; `Weak` 1 … 49; `Fainting` ≤ 0. While `Weak` or `Fainting` the cog
does not regenerate and takes **−2** to hit. At **`nutrition ≤ −200` the cog dies of starvation**.
The arithmetic is deliberate: 900 nutrition covers 900 of the episode's 2200 ticks, the starting
ration covers 800 more, so **a cog that wants to use its whole clock must find and eat food at least
once more** — which is the idea's "eat" task, made structural rather than bolted on.

**Regeneration.** `hp += 1` on every tick where `tick mod 20 == 0`, `hp < maxHp`, and hunger is
better than `Weak`.

**Experience.** A kill awards the species' `xpValue`. `xlevel` is `1 +` the number of thresholds
passed in `[20, 40, 80, 160, 320, 640, 1280]` (so `xlevel ≤ 8`). On each level-up,
`gain = 1 + rnd(8)`, `maxHp += gain`, `hp += gain`.

### Combat — exact integer rules

`rnd(n)` throughout this note means `mix64(seed, depth, tick, salt) mod n`, a **pure hash read**,
never a consumed stream (§Sim module → determinism). `d20` means `rnd(20) + 1`.

1. **To hit.** The attacker hits iff `d20 + attackBonus + defenderAc ≥ 11`.
   - The cog's `attackBonus` is `xlevel + weaponHitBonus − (2 if hunger ≤ Weak else 0)`.
   - A monster's `attackBonus` is its species `level`.
   - `defenderAc` is the defender's armour class (lower is better; unarmoured is 9, plate is 3).
2. **Damage.** `1 + rnd(die)`: the cog's die is the wielded weapon's (unarmed = 2); a monster's is
   its species `dmg`.
3. **Death.** `hp ≤ 0` ends the run immediately (§End conditions). There is no "you die at −1".
4. **Passive: the floating eye.** A melee attack on `e` (a floating eye) — hit **or** miss —
   **paralyses the cog for 12 ticks** ("You are frozen by the floating eye's gaze!"). This is the
   single most famous piece of NetHack lore that kills new players, it is preserved exactly, and it
   is the clearest test in this game of whether an LLM policy actually knows NetHack.
5. **Passive: the lichen.** A lichen `F` that hits the cog sets `stuck` for 3 ticks: the cog may
   attack and act but any `move` away from the lichen fails ("You are stuck to the lichen.").
6. The cog attacks by **moving into** a monster's cell. There are no ranged attacks, no spells and
   no wands (§Documented divergences).

### The monsters (eleven species, closed table)

| Glyph | Name | Depths | hp | ac | level | dmg die | speed | xp | Special |
|---|---|---|---|---|---|---|---|---|---|
| `x` | grid bug | 1–3 | 3 | 9 | 0 | 2 | 12 | 1 | **moves orthogonally only** (authentic) |
| `r` | sewer rat | 1–4 | 5 | 7 | 1 | 3 | 12 | 2 | |
| `F` | lichen | 1–5 | 4 | 9 | 0 | 2 | 3 | 4 | sticks (rule 5) |
| `d` | jackal | 1–5 | 6 | 7 | 0 | 2 | 12 | 2 | spawns in packs of **3** |
| `k` | kobold | 2–6 | 8 | 6 | 1 | 4 | 12 | 4 | |
| `G` | gnome | 2–7 | 10 | 5 | 1 | 6 | 12 | 8 | drops `10 + rnd(50)` gold |
| `Z` | gnome zombie | 3–8 | 12 | 5 | 1 | 6 | 6 | 8 | half speed |
| `e` | floating eye | 3–8 | 10 | 9 | 2 | 0 | **0** | 10 | never moves; paralysis passive (rule 4) |
| `o` | hill orc | 4–8 | 14 | 4 | 2 | 6 | 12 | 12 | spawns in pairs |
| `h` | dwarf | 4–8 | 14 | 4 | 2 | 8 | 12 | 12 | |
| `M` | gnome mummy | 6–8 | 20 | 4 | 3 | 8 | 6 | 20 | |

**Speed** is movement points per 12 ticks. A monster acts on tick `t` exactly
`(t × speed) div 12 − ((t − 1) × speed) div 12` times — so speed 12 is one action a tick, speed 6 is
every other tick, speed 3 is one tick in four, speed 0 never. Integer-exact and authentic
(NetHack's own movement-point model).

**Monster AI**, evaluated per granted action, first matching rule:
1. If the cog is 8-adjacent, **attack** it.
2. If the cog is within `aggroRange = 10` cells (Chebyshev) **and** the monster's cell and the cog's
   cell are both on the monster's current room or corridor component, step to the 8-neighbour that
   minimises Chebyshev distance to the cog, ties broken in the fixed direction order
   `e, se, s, sw, w, nw, n, ne`; a grid bug is restricted to `e, s, w, n`.
3. Otherwise wander: direction `rnd(8)` in the same order; move iff the target cell is passable and
   unoccupied.
A monster never enters lava, never opens a door, and never steps onto the cog's cell (it attacks
instead).

### Items

- **Gold `$`** — picked up with `pickup`; adds to `gold`.
- **Food `%`** — `food ration` (800), `tripe ration` (200), `apple` (50). `eat` restores nutrition.
- **Potions `!`** — four kinds: `healing` (`hp += 1 + rnd(8)`, capped at `maxHp`),
  `extra healing` (`hp += 2 + rnd(8)`, `maxHp += 1`), `confusion` (`confused` for 10 ticks: every
  `move` goes in direction `rnd(8)` instead of the one asked for), `sleeping` (`paralysed` for 10
  ticks). **Appearances are a seeded permutation** of `pink, ruby, milky, smoky, cloudy, dark`; a
  potion is shown as "a smoky potion" until one of that appearance has been quaffed, after which
  every potion of that appearance shows its true name. Learning the mapping by drinking is the
  identification game, in miniature, and it is a memory test the note field exists to serve.
- **Weapons `)`** — `dagger` (die 4, hit +1), `short sword` (die 6, hit 0), `mace` (die 6, hit +1),
  `long sword` (die 8, hit 0). `wield` swaps the wielded weapon.
- **Armour `[`** — `leather armour` (2), `ring mail` (3), `plate mail` (6). `wear` replaces what is
  worn; `ac = 9 − armourBonus`.

### Traps

`trapCount = (depth + 1) div 2` per level, each on a hash-chosen floor cell, **hidden** (the cell
renders as its terrain) until triggered or found. Kinds, chosen by `rnd(4)`:

| Kind | Effect on trigger |
|---|---|
| `arrow trap` | `1 + rnd(6)` damage |
| `dart trap` | `1 + rnd(3)` damage |
| `pit` | `1 + rnd(3)` damage and `trapped` for 3 ticks (every queued primitive is discarded, one per tick, message "You crawl to the edge of the pit.") |
| `teleport trap` | the cog is moved to a hash-chosen free floor cell on the same level |

A triggered trap becomes **discovered**, renders `^` forever after, and never triggers again for
this cog. **`search`** reveals every undiscovered trap **and secret door** 8-adjacent to the cog on
the **third** `search` executed while adjacent to it (`searchesToReveal = 3`, a per-cell counter, so
searching is deterministic and always eventually works — a divergence from NetHack's per-turn
probability, chosen so a stuck cog is never stuck forever).

### Level generation — pure function of `(seed, depth)`

The `descend` variant generates every level this way; the `minihack` variant substitutes authored
templates (below). Every draw is `mix64(seed, depth, salt)`.

1. Partition the interior into a **3 × 3 grid of slots**, each 16 wide × 6 tall.
2. `roomCount = 6 + rnd(3)` (6 … 8). The nine slot indices are ordered by a hash key
   (`mix64(seed, depth, 100 + slot)`, ties by slot index) and the first `roomCount` are used.
3. In each used slot, a room: width `4 + rnd(9)` (4 … 12), height `3 + rnd(2)` (3 … 4), top-left
   offset hash-chosen so the room's wall ring stays strictly inside the slot. Interior is `.`,
   ringed by `-` / `|`.
4. **Corridors**: a spanning tree over the used slots under 4-adjacency on the 3 × 3 grid — Prim
   from the lowest used slot index, ties by lowest neighbour index — plus `rnd(2)` extra edges.
   Each edge is dug as an **L-shaped corridor** (`#`) between the two rooms' facing wall midpoints
   with the elbow at a hash-chosen offset. Where a corridor meets a room wall, that wall cell
   becomes a door: `rnd(100) <` **55** → open doorway `'`; `< 85` → closed door `+`; `< 95` →
   **locked** door `+`; else **secret** door.
5. **A secret door is only created when the level stays connected without it** — the generator
   re-runs its connectivity check and downgrades the door to `closed` if the conversion would make
   the secret door the only route. Locked doors are exempt: they are always kickable.
6. **Stairs**: `<` on a hash-chosen floor cell of the **lowest-index used slot** (call it the
   arrival room); `>` on a hash-chosen floor cell of the room **farthest from it in spanning-tree
   hops** (ties by lowest slot index). They are never in the same room, so every level must be
   traversed.
7. **Lit rooms**: room `s` is lit iff `mix64(seed, depth, s, 7) mod 100 < max(20, 100 − 10 × depth)`
   — DL1 is 90 % lit, DL8 is 20 %. Corridors are never lit.
8. **Contents**, on hash-chosen free floor cells, never on a staircase and never twice on one cell:
   `goldPiles = 2 + (depth mod 3)` of `10 + rnd(20 × depth + 20)` gold each; **exactly one food
   item** (guaranteed — hunger must be survivable); `1 + (depth mod 3)` further items drawn from
   {potion, weapon, armour}; and `min(12, 3 + depth)` monsters drawn from the species whose depth
   range contains `depth`, **never in the arrival room**, so a cog never materialises next to a
   dwarf.
9. **Depth 5 of `descend` is the Oracle level**: the centre slot's room is forced to exist, is
   forced lit, holds **`O`** (the Oracle) on its centre cell, and holds no monsters. This is
   NetHack's own placement (the Oracle lives on DL 5–9).
10. **Generator postcondition, asserted in code and in tests**: `<` and `>` are mutually reachable
    treating locked doors and secret doors as passable, and every placed item is reachable from `<`
    under the same rule.

### The MiniHack ladder (the `minihack` variant)

The idea's "small authored levels as a ladder", five of them, in this fixed order; each is a 48 × 18
template whose details are seeded, and each still has a `>` so the depth ladder and the scoring
formula are shared with `descend`:

1. **`corridor`** — two rooms at opposite ends of the map joined by a serpentine corridor with three
   hash-placed bends; two grid bugs in the corridor; `>` in the far room. Pure navigation.
2. **`lavacross`** — one wide hall bisected north-to-south by a **3-cell-wide lava river `}`** at a
   hash-chosen column, with a **single 1-cell floor bridge** at a hash-chosen row; `>` beyond it.
   Entering lava is instant death, so this level is about *reading the map before moving*.
3. **`monsterroom`** — one big lit room with `>` at the far end and **four monsters** (two jackals,
   two sewer rats) between the cog and it, plus a mace on the floor.
4. **`lockedvault`** — a small vault room containing `>` and a large gold pile, its only door
   **locked**. The only way in is `kick`. This is the idea's "skill task".
5. **`oracle`** — a four-room level with **`O`** in the centre room and gold in the outer ones; `>`
   in a corner room. Descending needs nothing from the Oracle; the `oracle` **deed** needs a
   consultation.

### The Oracle

`chat` with `dir` pointing at an 8-adjacent `O` consults the Oracle. If `gold ≥ consultCost = 50`,
the cost is deducted, the `oracle` deed is earned, and the message line delivers a real hint: *"The
Oracle whispers: the staircase down lies to the north-east."* (the true compass octant from the cog
to `>` on the current level). If `gold < 50`: *"The Oracle scowls at your empty purse."*, no deed, no
hint, the tick is spent. The Oracle never moves, never attacks, and cannot be attacked (a `move`
into it is a no-op with the message *"You swap places with nobody."*).

### Turn and tick structure — the exact resolution order

- **Tick** = one dungeon turn = one primitive by the cog, followed by the monsters' actions.
- **`turnTicks = 40`**: one command turn executes at most forty primitives.
- **`maxTurns = 55`**, so **`maxTicks = 2200`**. One game per episode (`maxGames = 1`).
- Between turns the tick loop runs **uncapped** (`fastMode: true`); 2200 ticks over a 864-cell grid
  with ≤ 12 monsters is integer work measured in milliseconds. The wall clock of an episode is the
  ≤ 55 LLM turns (§Decisions).

Per **command turn** `T`, in this order:

1. If the run has ended (death, bottom, escape), settle the episode (§End conditions).
2. Recompute visibility from the cog's pose, merge it into the level's memory, and build the seat's
   observation object (§Decisions → observation).
3. Issue the seat's LLM request. There is exactly **one** seat, so this is a batch of one through the
   starter's unchanged `engine.client.curl.makeRequests` path (`src/ctf/decide.nim:427`) — the code
   is the starter's batching code, carrying one request. Attempt-1 deadline `attempt1Ms = 6000`. A
   scripted seat computes locally, instantly, and consumes no request.
4. If the seat timed out, errored, returned non-JSON, or returned no usable `actions` array, it is
   retried **once**, `retryMs = 3000`.
5. Still no usable reply → the **`delver`** scripted plan is computed server-side (the same proc the
   `delver` baseline uses — imported, never duplicated) and a `fallback` record is written.
6. **Validate and expand the plan**, in the order the reply lists it:
   a. Entries past `maxActionsPerTurn = 10` are dropped and counted in `actionsDropped`.
   b. Each entry is validated against the reply schema; an entry that does not validate is
      **dropped** (never turned into a different action), counted in `repliesRepaired`, and reported
      back next turn.
   c. Macros are expanded against the **remembered map as of turn start**: `travel x y` becomes the
      BFS path's move primitives (§Decisions → the driver), yielding at most
      `macroPrimitiveCap = 40` primitives. A `travel` whose target is not reachable through
      remembered passable cells yields **zero** primitives, counts in `macrosUnreachable`, and is
      reported next turn as `unreachable`.
   d. The whole expanded queue is truncated to `turnTicks = 40` primitives; the surplus is discarded
      and `planTruncated` is reported next turn. **Nothing carries over to the next turn.**
7. `say` (≤ 140 runes) and `notes` (≤ 400 runes) are sanitised on rune boundaries and, with the
   accepted plan, written as the turn's `directive` replay record. `notes` is echoed back to this
   seat next turn and to nobody else; `say` is drawn in the spectator feed.
8. `turnSpacingMs = 2600` is a floor on wall-clock time between consecutive request **starts** (the
   starter's mechanism at `src/ctf/decide.nim:386-389`, kept), pinning the steady state at 23 req/min
   against the sidecar's 30/min per-episode cap.

Then, for each of the next `turnTicks` ticks, in this order — **this is the whole physics of the game
and nothing else mutates the world**:

1. `tick += 1`; `nutrition -= 1`; the hunger state is recomputed (a change emits a message).
2. **Involuntary states first.** If `paralysed > 0` or `trapped > 0`, decrement it, **discard** the
   next queued primitive, emit the matching message, and jump to step 5. (A paralysed cog is still
   attacked; that is what makes the floating eye lethal.)
3. Pop the next primitive from the queue. If the queue is empty the primitive is **`wait`** — a real
   cost: the tick and its nutrition are spent.
4. **Apply the primitive**, exactly:
   - `move dir` — if `confused`, `dir` is replaced by `rnd(8)`. Let `C` be the 8-neighbour in `dir`.
     If `C` holds a monster → **attack** it (combat rules above; a floating eye's passive fires
     whether or not the blow lands). Else if `C` is a **closed, unlocked** door → it opens (`'`),
     the tick is spent, the cog does **not** move (NetHack `autoopen`). Else if `C` is a **locked**
     door → *"This door is locked."*, nothing else. Else if `C` is `}` lava → the cog enters and
     **dies** (`burned`). Else if `C` is passable → the cog moves into it. Else → *"You cannot move
     there."*, the tick is spent.
   - `search` — increment the search counter of every 8-adjacent hidden feature; any that reaches 3
     is revealed (`^`, or a secret door becoming `+`).
   - `pickup` — take the whole item stack under the cog into the inventory at the lowest free letter
     (gold merges into `gold`). Nothing under the cog → *"There is nothing here to pick up."*
   - `eat item` — the inventory letter must be a food item; `nutrition += its value`, the item is
     consumed, `timesAte += 1`.
   - `quaff item` — the letter must be a potion; its effect applies, its appearance becomes
     identified, the potion is consumed.
   - `wield item` / `wear item` — the letter must be a weapon / armour; it becomes the wielded /
     worn one, the previous one returns to the pack, `ac` is recomputed.
   - `kick dir` — if the 8-neighbour is a locked door: it breaks open (becoming `'`) iff
     `rnd(3) == 0` **and** hunger is better than `Weak`, else *"WHAMM!!"*. If it is a monster: an
     unarmed attack with damage die 3. Otherwise *"Ouch! That hurts!"* and `1` damage.
   - `chat dir` — the Oracle rule above; against anything else, *"They seem not to notice you."*
   - `down` — legal only while standing on `>`. The cog leaves this level, `depth += 1`, and arrives
     on the new level's `<` (generating that level if it has never been visited; a revisited level is
     restored exactly as it was left, monsters and all). On the **last** level, `down` ends the run
     (`bottom`).
   - `up` — legal only while standing on `<`. `depth -= 1`, arriving on that level's `>`. On level 1,
     `up` ends the run (`escaped`) — NetHack's own rule.
   - `wait` — nothing happens.
5. **Traps.** If the cog's cell holds an undiscovered trap and the cog *entered* it this tick, it
   triggers: reveal, apply, message.
6. **Monsters act**, in ascending monster index, each granted `(t × speed) div 12 −
   ((t−1) × speed) div 12` actions, under the AI rules above. Monster damage is applied immediately.
7. **Death checks**, in this order: (a) `hp ≤ 0` → `died`, `causeOfDeath` and `killer` recorded;
   (b) `nutrition ≤ −200` → `starved`; (c) the cog stands in lava → `burned`. Any of them ends the
   run.
8. **Regeneration and experience.** `hp += 1` if `tick mod 20 == 0`, `hp < maxHp` and hunger is
   better than `Weak`; then the `xlevel` threshold check.
9. **Visibility, memory and deeds.** Recompute the visible set (below) and merge it into this
   level's memory, stamping each newly observed cell with `tick`; recompute `depthReached`; award any
   deed that just became true (each once, permanently, emitting `deed`).
10. Mix the tick into `gameHash` and append it to the replay's hash chain.
11. If the run ended at step 7 or in step 4's `down`/`up`, **break out of the tick loop** — the turn
    ends early.

### Visibility — the exact rule

NetHack's lighting model, restated as integer code, and the only visibility rule in this game:

```
visible = {}
if the cog stands on a floor cell belonging to a LIT room:
    visible = every floor cell of that room, plus its whole wall ring and its doors
else:
    visible = the cog's own cell and its 8 neighbours
```

- **Terrain** in `visible` is merged into the level's **memory** and stays there forever, stamped
  with the tick it was last seen.
- **Items** are remembered at the position they were last seen; if the cell is visible and the item
  is gone, the memory is cleared.
- **Monsters are never remembered.** A monster appears in the map and in `visible_monsters` only
  while it is on a visible cell — exactly NetHack, and the reason a dark corridor is frightening.
- **Traps** appear only once discovered. Secret doors render as solid rock until found.
- A cell never in `visible` renders as ` ` (space) and is indistinguishable from solid rock — which
  is what the cog is being asked to solve.

### Scoring formula and sign

At the end of the episode:

```
depthReached  = the deepest dungeon level the cog ever STOOD on          (1 .. dungeonLevels)
gold          = gold carried at the end                                  (>= 0)
xpPoints      = experience points earned                                 (>= 0)
deedCount     = |{fed, hoard, oracle} earned|                            (0 .. 3)

scores[0] = 100_000 * (depthReached - 1)          # 0 .. 700_000 in `descend`
          +      10 * min(gold, 2_000)            # 0 ..  20_000
          +      50 * min(xpPoints, 1_000)        # 0 ..  50_000
          +   5_000 * deedCount                   # 0 ..  15_000
```

The three **deeds**, which are the idea's "gold / eat / oracle" tasks made into named, scored,
feed-visible facts:

| Deed | Earned when |
|---|---|
| `fed` | the cog has eaten at least once (`timesAte ≥ 1`) |
| `hoard` | the cog has carried **≥ 500 gold** at any moment |
| `oracle` | the cog has consulted the Oracle successfully |

**Sign: higher is better, and every term only ever adds** — `scores[0]` is never negative, and the
minimum (0) is the honest score of a cog that died on level 1 with nothing. **Death does not subtract
anything.** That is NetHack's own rule: you score the run you had, and dying merely stops you from
scoring more. A death penalty would reward a cog that sat on the up-staircase for 55 turns over one
that fought its way to DL 5 and was killed by a dwarf, which is the opposite of the idea's "depth
attack".

**The ordering is strictly lexicographic in depth, by construction:** the largest possible total of
the three non-depth terms is `20_000 + 50_000 + 15_000 = 85_000 < 100_000`, so **one more dungeon
level always beats any amount of gold, experience and deeds**. Beneath depth, experience outranks
gold in the limit (both are capped, and the caps are chosen so that a full experience haul,
50 000, dominates a full gold haul, 20 000: killing things is worth more than picking things up,
which is what makes diving past monsters a real trade rather than a free lunch).
Maximum attainable score in `descend`: `700_000 + 20_000 + 50_000 + 15_000 = 785_000`.
`tests/test_nethack_scoring.nim` asserts the formula, the dominance bound and the maximum,
analytically and over 500 randomised end states.

**The league ranks by `results.scores[0]`.** With one seat, every episode is a solo run and the
platform's Elo (1000 start / K 32) is computed from these per-episode per-seat numbers; a policy
climbs by getting deeper across more seeds, which is exactly the idea's "score / depth attack".
`results.win[0]` is `depthReached >= parDepth` — a "did the cog clear the bar" flag, not a duel —
and **`results.winner` is `0` when `win[0]` is true and `null` otherwise** (there is no opponent, so
the only honest winner is the seat itself or nobody).

**Measured but never scored:** `monstersKilled`, `itemsPicked`, `timesAte`, `doorsKicked`,
`trapsTriggered`, `potionsQuaffed`, `cellsSeen`, `primitivesExecuted`, `actionsDropped`,
`macrosUnreachable`, `repliesRepaired`, and the per-level arrays. All are in `results`, on the
endcard and in the feed. Exploration is a *means*, not a currency: paying for cells seen would let a
policy farm the metric by pacing a lit room (§Out of scope).

### Integrity (the idea's note), decided

- **"Seeded dungeons per round."** The episode `seed` is randomised by the runner, recorded in the
  replay config and in `results.seed`, and **never appears in any observation or prompt**. Every
  level is a pure function of `(seed, depth)` (§Sim module → determinism), so a round's dungeon is
  reproducible from the replay and identical for every policy that draws that seed, while no policy
  can compute it in advance.
- **"Action-log replay verification."** The replay stores the seat's **accepted action log** and one
  `gameHash` per tick; the wasm viewer re-simulates the whole run from the seed and the action log
  and compares hashes **every tick** (`checkReplayHash`), surfacing the first divergent tick in
  `#mmwarn`. That is the idea's verification, implemented as the starter's own mechanism.
- **"Hard episode cap."** Three independent caps: `maxTurns = 55`, `maxTicks = 2200`, and
  `wallClockBudgetSeconds = 660`. No policy behaviour can extend any of them.

### End conditions and legal `results.reason` values

The run ends at the first of: **death**, **the bottom staircase**, **escaping at level 1**, the
**turn cap**, or the **wall-clock stop**.

- **Death** — `hp ≤ 0`, starvation, or lava. Permadeath: the episode settles immediately with the
  score earned so far. `results.endRule = "death"`, `results.causeOfDeath ∈ {killed, starved,
  burned}` and `results.killer` names the species (or `"starvation"` / `"lava"`).
- **Bottom** — `down` on the last level. `endRule = "bottom"`.
- **Escaped** — `up` on level 1. `endRule = "escaped"`. Banking a run is a legal, and sometimes
  correct, decision: it stops the hunger clock and the monsters.
- **Turn cap** — `turnsPlayed == maxTurns` (55) or `tick == maxTicks` (2200), whichever first.
  `endRule = "turnCap"`.
- **Wall-clock stop** — the engine's `wallClockBudgetSeconds` guard, the starter's check at
  `src/ctf/server.nim:1407-1417`, kept.

`results.reason` is the starter's closed enum; **exactly these three values are legal** and the game
emits nothing else:

- **`complete`** — the run finished on its own terms: death, bottom, escape or the turn cap. The
  healthy value; **a death is a `complete` episode**, not an error. `results.endRule` says which:
  `death` | `bottom` | `escaped` | `turnCap`.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (default **660 s**). The engine
  stops at the current tick, settles with the **real** depth, gold, experience and deeds so far
  (never zeroed, so a deadline episode is still rankable), writes `results.json` and the replay, and
  exits 0. `results.endRule = "wallClock"`. **Declared acceptable** for `docs/SPEC.md` §Definition of
  done check 4. The budget guard below exists so it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop. Caught; the episode is settled from
  the last completed tick, `results.endRule = "fault"`, `results.stopDetail` names it (≤ 200 runes,
  rune-truncated), artifacts are still written, exit 0. A defect: `tools/ci/docker_smoke.sh` fails
  the build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum:
`death | bottom | escaped | turnCap | wallClock | fault`.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × turnBudgetMs > wallClockBudgetSeconds`, the LLM is switched off for every remaining
turn (the seat falls to `delver`, microseconds per turn), the run still plays out at full speed, and
the episode still ends `complete`. A `budget_guard` record names the turn it fired
(`src/ctf/decide.nim:328-346`, kept).

**A silent seat does not end the episode.** A seat that never connects, disconnects mid-episode, or
fails every decision is driven by `delver` and the run reaches its natural end with
`deadSeats[0] = true`. Nothing a player container does can stop the clock: the starter's
`lobbyJoinTimeoutTicks` bounds the lobby, and a silent seat cannot consume more than the per-turn
deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes the seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {delver, bumbler}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=delver` (the starter's "anything unrecognised is the published default" rule at
`src/ctf/baselines.nim:52-58`). **A scripted policy seated as a champion is a failure state.**

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/nethack/anthropic_api_key` — the hive
2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/nethack_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar) — the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"delver"|"bumbler"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at 64 runes, then
acknowledge frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3
close-frame race: whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/nethack/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION` / `AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (via `readCogameUri`) → **none**, in which case the
  client is `disabled = true` and every turn falls back instantly with no network wait, so offline
  certification finishes in seconds.
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 900` (not 400 — "cut off at max_tokens"). **No `output_config.effort`** when the
  model string contains `haiku` or `4-5`. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject`
  (`src/ctf/directives.nim:102` — outermost balanced `{…}`, fence-tolerant, tolerant of trailing
  prose) and `truncateRunes` / `sanitizeSay` / `sanitizeNote` (`src/ctf/directives.nim:61-90`)
  unchanged.

### Cadence, the per-turn call budget, and the wall-clock arithmetic

One command turn every ≤ 40 ticks; **at most 55 turns per episode**. **The per-turn LLM call budget
is exactly ONE request, plus at most ONE retry** — there is a single seat, so the starter's
one-parallel-batch-per-turn machinery (`src/ctf/decide.nim:427`) carries a batch of one and is
otherwise untouched. **At most `55 × 2 = 110` provider calls per episode**, and never more than one
in flight.

```
attempt1Ms                          6.0 s   (whole seconds - sim_config.nim:686-713 rejects otherwise)
retryMs                             3.0 s   (whole seconds; attempt1Ms + retryMs <= turnBudgetMs)
turnBudgetMs                        9.5 s   (monotonic deadline around the whole turn)
turnSpacingMs                       2.6 s   -> 1 seat x 60/2.6 = 23 req/min  (sidecar cap: 30)

55 turns x max(spacing 2.6 s, latency ~3.4 s)  typical            = 190 s
55 turns x turnBudgetMs 9.5 s, absolute worst                     = 523 s
2200 ticks, <=12 monsters/level, integer Nim, fastMode            =   2 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400 = 100 s at       =  15 s   (cap: 100 s)
   TargetFps 24; typical 15 s)
gameOverTicks hold + results + replay write (retried uploader)    =  20 s
                                                                  -------
typical total                                                     = 227 s   < 720 s
absolute worst case (523 + 2 + 100 + 20)                          = 645 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                           = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                             = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_nethack_manifest.nim` asserts it. The typical
figure is conservative: a cog that dies on DL 3 uses far fewer than 55 turns, and permadeath makes
short episodes common.

**Rate guard.** `turnSpacingMs` pins the steady state at 23 req/min, but a run of retrying turns
issues two requests each. The engine therefore keeps a **rolling 60 s request counter**: if issuing
the next request would push the trailing-60 s count above **28**, that turn skips the call and takes
the `delver` plan with `cause = "rate_guard"`. Bounded, logged, never a sleep on the episode's
critical path (the raid round 2 sidecar-throttle scar).

`fastMode: true` in every variant, as in the starter's paintball variant: the seat sends no per-tick
inputs (the server computes every primitive), so the Sprite v1 Ready packet's dead-reckoning hazard
cannot arise.

### Degrade, never hang

Every wait is bounded: the two request deadlines, the outer `turnBudgetMs`, the rate guard,
`lobbyJoinTimeoutTicks`, mummy's socket timeouts on the serve thread (which runs independently of the
game loop, so a 9.5 s LLM stall cannot drop a connection or stall `/healthz`), the 660 s engine stop,
and ctf's `gameOverTicks` hold before exit — kept so `/healthz` and `/global` keep answering for a
bounded grace after artifacts are written (the lantern 0.1.3 `/global` ping scar).

On the seat's timeout or parse failure: **retry once**; on the second failure that turn's plan
becomes the **`delver`** scripted plan computed inside the game (the same proc the `delver` baseline
uses — imported, never duplicated), and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns` counts them. The attempt-1 notice says **`will retry`**; only
a genuine second failure logs **`falling back`** (the pommerman 0.1.1 phase-60 grep scar; the
starter's two phrasings live at `src/ctf/decide.nim:463` and `:491`).

**No failure mode leaves the cog without an action.** The tick loop always has a primitive: the
turn's queue, else `wait`, which is a legal state that costs a tick and its nutrition and nothing
else. A seat that never connects is reported once to `COGAME_PLAYER_FAILURE_URI` with the platform's
**closed** payload — exactly `{"message", "failed_policy_index"}`, nothing else.

**The episode settles early rather than overrunning**: permadeath ends it the tick the cog dies, the
bottom staircase and the level-1 up-staircase end it on the spot, and the budget guard drops the seat
to scripted play the moment two more full turns would not fit.

### Per-seat observation: exactly what is visible and what is hidden

The guiding line: **the cog knows what it has seen, what it is carrying, and what the message line
just told it — and nothing else.** The observation is text-native, as the idea requires.

**Visible.**

- **The rules of the world, once, at registration** — `levelW` 48, `levelH` 18, `dungeonLevels`, the
  full glyph legend, the verb list with what each does, `turnTicks`, `maxTurns`, `maxActionsPerTurn`,
  the hunger thresholds, and the fact that lava and starvation kill. Static; afterwards referred to
  by id.
- **`map`** — **eighteen strings of forty-eight characters**, the cog's memory of the **current
  level**: remembered terrain, remembered items, **currently visible monsters**, `@` for itself, and
  ` ` for everything never seen. This is the ASCII dungeon the idea names.
- **`messages`** — the NetHack message line, as **at most 8 strings of ≤ 160 runes each**, in tick
  order, covering the ticks since the last observation. Everything the world says to the cog goes
  here: *"You hit the sewer rat."*, *"The sewer rat bites!"*, *"This door is locked."*, *"You are
  frozen by the floating eye's gaze!"*, *"You feel weak now."*, *"$ - 43 gold pieces."*
- **`status_line`** — the NetHack bottom line, rendered:
  `Dlvl:3 $:214 HP:9(14) AC:7 Xp:3/42 T:517 Hungry`.
- **`you`** — the same facts structured: `x`, `y`, `depth`, `hp`, `max_hp`, `ac`, `xlevel`, `xp`,
  `gold`, `nutrition`, `hunger` (`Satiated|Not Hungry|Hungry|Weak|Fainting`), `status` (the subset of
  `confused|paralysed|stuck|trapped` currently on), and `under_foot` (the glyph and the item, if any,
  on the cog's own cell).
- **`inventory`** — every stack: `{letter, name, kind, count, equipped}`, where `name` is the
  **identified** name for identified things and the **appearance** for unidentified potions
  ("a smoky potion").
- **`visible`** — every monster and item on a currently visible cell:
  `{glyph, name, x, y, kind}`, sorted ascending by `(y, x)`. Monsters vanish from this list the
  moment they leave sight.
- **`level`** — `{depth, stairs_down: {x,y} | null, stairs_up: {x,y} | null, rooms_seen, lit}` —
  stairs only if they have been seen.
- **Its own last turn** — `last_plan.executed` (the primitives that actually ran), `truncated`,
  `dropped`, `unreachable`.
- **Its own progress** — `deeds` (the three named credits and which are earned), `depth_reached`,
  `turns_left`, `ticks_left`.
- **`notes`** — its own note from last turn, echoed back.

**Hidden.** The episode **seed**; every cell of every level never seen; every level not yet visited;
undiscovered traps and secret doors; **monsters out of sight** (never remembered); a monster's hit
points, remaining hit points and exact statistics (the cog is told the species name and nothing
more — NetHack does not show monster HP); the **kind of an unidentified potion**; the Oracle's hint
before it is bought; the cog's own **score**; the par depth of the variant; and its own real
player/policy name. Nothing about identity ever reaches a prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `map` and
minus `notes`) into the replay's `directive` record — the map is omitted because the viewer
**re-simulates** it exactly (§Server → Replay bytes), so storing it would be 60 KB of derivable
bytes.

```json
{
  "you_are": "Alpha the Digger",
  "turn": 22, "tick": 517, "turns_left": 33, "ticks_left": 1683,
  "status_line": "Dlvl:3 $:214 HP:9(14) AC:7 Xp:3/42 T:517 Hungry",
  "you": {"x": 10, "y": 5, "depth": 3, "hp": 9, "max_hp": 14, "ac": 7,
          "xlevel": 3, "xp": 42, "gold": 214, "nutrition": 118,
          "hunger": "Hungry", "status": [], "under_foot": {"glyph": ".", "item": null}},
  "map": [
    "                                                ",
    "                                                ",
    "  ------------                                  ",
    "  |..........|                                  ",
    "  +.........r|                                  ",
    "  |.......@..'#########                         ",
    "  |..$.......|        #                         ",
    "  ------------        #                         ",
    "                      #       --------------    ",
    "                      #       |............|    ",
    "                      ########'....<.......|    ",
    "                              |.......%....|    ",
    "                              |............|    ",
    "                              --------------    ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                "
  ],
  "messages": ["You hit the sewer rat.", "The sewer rat bites!",
               "You feel hungry now."],
  "visible": [{"glyph": "$", "name": "43 gold pieces", "x": 5, "y": 6, "kind": "gold"},
              {"glyph": "r", "name": "sewer rat", "x": 12, "y": 4, "kind": "monster"}],
  "inventory": [{"letter": "a", "name": "dagger", "kind": "weapon", "count": 1, "equipped": "wielded"},
                {"letter": "c", "name": "leather armour", "kind": "armour", "count": 1, "equipped": "worn"},
                {"letter": "d", "name": "a smoky potion", "kind": "potion", "count": 1, "equipped": ""}],
  "level": {"depth": 3, "stairs_down": null, "stairs_up": {"x": 35, "y": 10},
            "rooms_seen": 2, "lit": true},
  "last_plan": {"executed": ["travel", "move", "move", "move"],
                "truncated": false, "dropped": 0, "unreachable": 0},
  "deeds": [{"name": "fed", "earned": true}, {"name": "hoard", "earned": false},
            {"name": "oracle", "earned": false}],
  "depth_reached": 3,
  "notes": "DL3: came down at (35,10) NE room. no > yet. west room lit, closed door at (2,4) unexplored. ate ration at T:340. smoky potion untested."
}
```

Reading it: the cog is at `(10, 5)` in a **lit** room, so the whole room and its walls are in `map`;
a sewer rat is one step north-east at `(12, 4)` and is in `visible` because it is in the lit room;
43 gold sits at `(5, 6)`; the corridor it came down and the north-east room with the up-staircase
`<` at `(35, 10)` and a food item at `(38, 11)` are **remembered**, not currently seen. The closed
door `+` at `(2, 4)` in the west wall is the only unexplored exit it knows about, and `>` has not
been found — everything beyond is ` `, and that is the whole problem the turn has to solve.

Field rules. `map` is always **18 strings of exactly 48 characters**; the array shape never changes.
Glyphs are exactly the closed set in the legend. `messages` is at most 8 entries; if more than 8
messages were produced, the **oldest** are dropped and the first entry becomes
`"(3 earlier messages)"`. `visible` and `inventory` are sorted (by `(y, x)` and by letter). `status`
lists only the effects currently on.

### Reply schema and per-field caps

```json
{"actions": [{"do": "move", "dir": "ne"},
             {"do": "move", "dir": "ne"},
             {"do": "travel", "x": 5, "y": 6},
             {"do": "pickup"},
             {"do": "eat", "item": "b"}],
 "say": "rat first, then the gold, then the closed door west",
 "notes": "DL3: no > yet. west door (2,4) is next. 214 gold. smoky potion untested."}
```

| Field | Type | Cap / domain |
|---|---|---|
| `actions` | array | **≤ 10 entries** (`maxActionsPerTurn`). Entries past the cap are dropped and counted in `actionsDropped`. Absent or empty = the turn is forty `wait` ticks, and the reply is still **usable** |
| `actions[].do` | string | **≤ 8 runes**; enum `move` \| `travel` \| `search` \| `pickup` \| `eat` \| `quaff` \| `wield` \| `wear` \| `kick` \| `chat` \| `down` \| `up` \| `wait`, lower-cased before matching |
| `actions[].dir` | string | required iff `do ∈ {move, kick, chat}`; **≤ 2 runes**; matched case-insensitively against `n, s, e, w, ne, nw, se, sw`; anything else **drops the entry** |
| `actions[].x`, `.y` | integer | required iff `do == "travel"`; **clamped to 0 … 47 / 0 … 17**; a non-integer or absent value **drops the entry** and counts in `repliesRepaired` |
| `actions[].item` | string | required iff `do ∈ {eat, quaff, wield, wear}`; **exactly 1 rune**, `a … z`; a letter not in the inventory drops the entry |
| `say` | string | **≤ 140 runes** (`MaxSayRunes`) — the cog thinking out loud; drawn in the spectator feed and in the replay, never fed back to the seat |
| `notes` | string | **≤ 400 runes** (`MaxNoteRunes`) — private scratchpad, echoed to this seat only next turn |
| whole reply | bytes | **≤ 4096** read from the provider before parsing (10 actions ≈ 400 B + `say` ≤ 560 B + `notes` ≤ 1600 B + JSON overhead ≈ 2700 B worst case, so 4096 is comfortable) |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

`MaxSayRunes` and `MaxNoteRunes` are **re-pinned in this fork**: the starter has
`MaxSayRunes = ShoutMaxChars = 10` and `MaxNoteRunes = 160` (`src/ctf/sim_types.nim:747, 794-795`),
which are a 10-character in-world shout and a short note. A cog narrating a dungeon crawl needs a
sentence, and a cog carrying a dungeon map, a potion-identification table and a staircase location
between turns needs more than 160 runes — the note **is** this game's long-horizon memory, and 400
runes is the smallest cap that holds "level, stairs, unexplored exits, potion table, plan".
`MaxSayRunes = 140` and `MaxNoteRunes = 400` here, and `ShoutMaxChars` is deleted with the shout
mechanic (§Sim module → Deleted).

**Every string that lands in the replay — `say`, `notes`, message lines, item names, the policy
label, `causeOfDeath`, `stopDetail`, recorded error text — is truncated on RUNE boundaries** via the
starter's `truncateRunes` / `runeSubStr` (`src/ctf/directives.nim:61-68`), never by byte index. Byte
truncation is what makes a replay that renders in a browser fail a strict UTF-8 parser;
`tests/test_nethack_replay.nim` asserts it with 4-byte emoji sitting exactly on every cap.

Unknown top-level and per-action keys are ignored. A reply with a valid `say` but no `actions` is
**usable** (the turn is spent waiting and the narration is delivered). A reply that is not a JSON
object is a parse failure. **Invalid actions are dropped, never rewritten**: a mis-specified move in
a permadeath game has no meaningful repair — turning an invalid `travel` into a `move` could walk the
cog into lava on the game's own initiative — so the entry is removed, counted, and reported back as
`dropped` next turn.

### System prompt (fixed, identical for both champions)

```
You are Alpha the Digger, alone in a randomly generated dungeon. It is NetHack
in miniature: rooms, corridors, monsters, hunger, traps, permadeath. You have
ONE life. If you die the run is over.

WHAT YOU GET EACH TURN
- "map": 18 rows of 48 characters, the level as YOU REMEMBER IT. A space is a
  cell you have never seen - it may be rock, or a room, or the way down.
- "messages": what just happened, in order, like NetHack's message line.
- "status_line": Dlvl / gold / HP / AC / experience / turn / hunger.
- "visible": monsters and items you can see RIGHT NOW. Monsters are NOT
  remembered: if one is not in this list, you do not know where it is.
- "inventory": your pack, by letter. Unidentified potions show a colour only.

GLYPHS
  @ you        . floor      # corridor    - | wall      ' open doorway
  + door (closed OR locked - the message line tells you which)
  < stairs up  > stairs DOWN (this is what you are looking for)
  } LAVA - entering it kills you instantly
  ^ a trap you have already found
  $ gold  % food  ! potion  ) weapon  [ armour
  O the Oracle
  letters are monsters: x grid bug, r sewer rat, F lichen, d jackal, k kobold,
  G gnome, Z gnome zombie, e floating eye, o hill orc, h dwarf, M gnome mummy

WHAT YOU SEND
One JSON object with up to 10 actions. They run one per dungeon turn, in order,
up to 40 turns, and then you are asked again. Anything past 40 turns of
movement is CUT OFF - re-issue it next turn.
  {"do":"move","dir":"ne"}   step one cell (n s e w ne nw se sw). Moving INTO a
                    monster attacks it. Moving into a closed door opens it.
  {"do":"travel","x":31,"y":8}  WALK THERE. Your main action. Shortest path
                    through cells you have ALREADY SEEN. It refuses to path
                    through unseen cells, lava, locked doors and monsters. If
                    it says "unreachable" you have not found a route yet.
  {"do":"down"}     take > down a level. You must be standing on it.
  {"do":"up"}       take < up. On level 1 this ENDS the run.
  {"do":"pickup"}   pick up what is under you
  {"do":"eat","item":"b"}    eat a food item from your pack
  {"do":"quaff","item":"d"}  drink a potion (you find out what it was)
  {"do":"wield","item":"a"}  {"do":"wear","item":"c"}
  {"do":"kick","dir":"n"}    kick a LOCKED door open. May take several kicks.
  {"do":"search"}   search the 8 cells around you for secret doors and traps.
                    Three searches next to a hidden thing finds it.
  {"do":"chat","dir":"e"}    talk to the Oracle (O). Costs 50 gold, tells you
                    which way the stairs down are.
  {"do":"wait"}     waste a turn

THINGS THAT KILL YOU
Hit points reaching 0. Stepping into lava (}). Starving: your nutrition falls
by 1 every turn, and at -200 you die. Eat before you are Weak.
NEVER melee a floating eye (e). Hitting one freezes you for 12 turns and
everything else in the room gets 12 free attacks. Walk around it.

HOW YOU ARE SCORED
Depth, overwhelmingly. Every dungeon level you reach is worth more than all the
gold, experience and deeds you could possibly collect. Gold, experience, and
three deeds (eat once, carry 500 gold, consult the Oracle) are tie-breaks.
Dying does not subtract anything - but it stops you going deeper.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the
character { and end with }. No prose, no markdown, no code fences.
{"actions":[{"do":"travel","x":31,"y":8},{"do":"down"}],"say":"<=140 chars","notes":"<=400 chars"}
```

### Champion #1 — `nethack-divemaster` (owner **daveey**), `PLAYER_PROMPT`

```
Depth is the only thing that scores. Get down the stairs.
Every turn, in this order:
1. If you are standing on >, {"do":"down"}. No exceptions, no "one more room".
2. If > is on your map, travel to it and take it in the SAME turn:
   [{"do":"travel","x":X,"y":Y},{"do":"down"}].
3. If HP is below one third of max, do not fight anything. Travel away from the
   monster toward the stairs you know, and drink an unidentified potion only if
   you would otherwise die this turn - it is a coin flip and a coin flip beats
   certain death.
4. If hunger says Hungry or worse and you carry food, eat it NOW. A Weak cog
   fights at -2 and cannot kick doors. Never let the clock reach Fainting.
5. Otherwise explore toward the unknown: pick the cell on your map that is
   floor or corridor AND touches the most spaces, travel to it, then add two or
   three {"do":"move"} in the same heading so you actually cross into the dark.
   Corridors only show you one cell at a time - keep moving.
6. If nothing on the map touches a space and you have no >, you are behind a
   secret door. Travel to a dead-end corridor cell and {"do":"search"} eight
   times. Three searches next to a hidden door finds it.
Fight only what blocks the route, and only with HP above half. Pick up gold
that is on your way and food ALWAYS. Never melee e. Never travel across }.
Write "notes" every turn as: DL, where < and > are, which exits are still dark,
what is in your pack, and what you learned about a potion colour. Notes are the
only memory you have.
```

### Champion #2 — `nethack-loremaster` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Play like someone who has read the wiki. Survive first, then dive.
Lore you already know and must use:
- e is a floating eye. NEVER attack it in melee, at any HP, for any reason.
  Walk around it. It never moves, so it is only ever a wall.
- F is a lichen. It sticks to you. Kill it or you will not get away.
- d jackals come in threes. Fight them in a doorway or a corridor so only one
  reaches you at a time - never in the open room.
- A + you cannot walk through is locked. Kick it: {"do":"kick","dir":"..."}
  repeatedly, up to four kicks a turn. You cannot kick while Weak, so eat first.
- Unidentified potions are worth drinking when you are healthy and stuck, not
  when you are dying: you want to LEARN the colour before you need it. Record
  every colour you have drunk and what it did in "notes" and never re-test a
  known colour.
- The Oracle is O. Fifty gold buys the direction of the stairs down. If you
  have 50 gold and see an O, buy it - it is a deed and a shortcut at once.
Turn order:
1. On >? Go down.
2. Hungry or worse and carrying food? Eat.
3. Adjacent monster you should fight (not e, not more than one at once)?
   Attack it with two or three {"do":"move"} into it.
4. > known? Travel there, then down.
5. Otherwise explore the darkest edge of the map, and pick up food and gold on
   the way; 500 gold is a deed.
Keep a running note in this exact shape and rewrite it every turn:
  "DL<n> <(x,y) of < and >> | dark: <which side> | pack: <letters> |
   potions: pink=heal, smoky=? | plan: <one clause>"
If "last_plan" says truncated, re-issue the same travel - you were partway.
If it says unreachable, you have not found a route; explore toward that side.
```

### The driver (deterministic, shared by every policy)

`src/nethack/driver.nim` — the starter's `src/ctf/control.nim` (directive → per-tick actuation),
retargeted from pixel steering to a **primitive queue**. It is the **only** producer of primitives,
and it contains no randomness.

| Action | Expands to |
|---|---|
| `move` `search` `pickup` `eat` `quaff` `wield` `wear` `kick` `chat` `down` `up` `wait` | itself, one primitive |
| `travel x y` | the `move` primitives that walk the BFS path below |

**The `travel` BFS**, run against the **remembered map of the current level as of turn start**:

- Nodes are cells; edges are the **eight** neighbours in the fixed order `e, se, s, sw, w, nw, n, ne`.
- A cell is **traversable** iff its remembered terrain is `.`, `#`, `'`, `>`, `<` or a discovered
  `^` trap. Unseen (` `), walls, `+` (closed **or** locked), `}` lava and any cell holding a
  currently visible monster are **not**. The driver plans on what is known, not on hope, and it never
  walks the cog into lava or into a fight it did not ask for.
- **Diagonal moves may not cut a doorway corner**: a diagonal step is illegal if either orthogonal
  neighbour it passes is a wall or a doorway (NetHack's own rule).
- Breadth-first from the cog's cell; ties broken by the neighbour order above, so the path is unique
  for a given remembered map.
- If the **target** is traversable, the path ends **on** it. If it is not traversable but is
  8-adjacent to a reached cell, the path ends on the nearest such cell (so `travel` to a closed door
  puts the cog next to it, ready to `move` into it or `kick` it). If neither, the macro yields
  **zero** primitives and counts as `unreachable`.
- Bounded by `macroPrimitiveCap = 40` primitives; the whole turn's queue is then truncated to
  `turnTicks = 40`.

The driver never invents an action the schema does not express. It makes no promise about a cell the
cog has never seen, which is why crossing into the dark costs an explicit `move` from the policy —
the single most important thing this interface asks a policy to understand.

### Scripted baselines (both shipped as league fillers; `delver` is also the server-side fallback)

`src/nethack/baselines.nim`, the starter's module retargeted. Both emit the **same** reply objects an
LLM does, through the same validator, which is what makes the bounded-orders test meaningful.
Neither ever emits `say` or `notes` — a baseline that narrated would make the feed lie about which
seats are LLMs.

**`delver`** — `PLAYER_SCRIPTED=delver`, and the fallback. A deterministic dungeon crawler, an
honest stand-in for the symbolic bots the idea names (AutoAscend et al.), scaled to this sim. Every
turn, first matching rule wins, emitting at most 10 actions:

1. **Eat if weak.** Hunger is `Weak` or `Fainting` and the pack holds food → `{"do":"eat","item":L}`
   for the lowest food letter.
2. **Descend now.** Standing on `>` → `{"do":"down"}`.
3. **Flee if hurt.** `hp × 3 ≤ maxHp` and a monster is 8-adjacent → travel to the remembered `>` if
   any, else the remembered `<`, else the reachable remembered cell at maximum BFS distance from
   that monster (ties by lowest `(y, x)`).
4. **Fight what is adjacent.** A monster is 8-adjacent, it is **not** a floating eye `e`, and
   `hp × 3 > maxHp` → four `{"do":"move","dir":D}` into it.
5. **Take the stairs.** `>` is in memory and reachable → `[{"do":"travel","x":X,"y":Y},{"do":"down"}]`.
6. **Loot on the way.** An item is under foot → `{"do":"pickup"}`. Else a remembered food item is
   reachable within 15 steps → travel + `pickup`; else a remembered gold pile within 15 steps →
   travel + `pickup`. Food outranks gold, always.
7. **Kick what is locked.** A locked door is 8-adjacent and hunger is better than `Weak` → four
   `{"do":"kick","dir":D}`.
8. **Explore.** Travel to the **nearest frontier** — the remembered traversable cell 8-adjacent to
   the most unseen cells, ties by lowest BFS distance then lowest `(y, x)` — then two
   `{"do":"move"}` continuing the last heading, so the plan actually crosses into the dark.
9. **Search.** No frontier and no known `>` → `searchBurst = 8` × `{"do":"search"}` at the current
   cell (the authentic move when a level looks closed).

`delver` never travels through lava, never melees a floating eye, and never routes through an unseen
cell. It has no notion of potion identification, so it never quaffs — which is deliberate: it is the
floor, not a strategy.

**`bumbler`** — `PLAYER_SCRIPTED=bumbler`. The reactive control, four rules: emit ten actions; each
is `{"do":"move","dir":H}` where `H` is the current heading if the remembered cell ahead is
traversable, else the next heading clockwise in `e, se, s, sw, w, nw, n, ne`; if an item is under
foot the first action is `pickup`; if standing on `>` the first action is `down`; it never eats and
never fights on purpose. It has no BFS, no memory beyond the heading, and no hunger management, so it
starves or is killed on DL 1–2. It is the control that answers "did the LLM actually crawl?"

Like the starter's `DefaultBaselineParams` (`src/ctf/baselines.nim:38`), `delver`'s tunables
(`fleeHpNumerator`, the loot radius 15, `searchBurst = 8`, and whether the frontier score breaks ties
by distance or by `(y, x)`) are a parameter object chosen by `tools/tune_baselines.nim`'s sweep, not
guessed; `tools/ci/baseline_tuning.json` records the sweep's pick and `tests/test_nethack_tuning.nim`
asserts the shipped defaults still equal it.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/nethack/`. The fork is a rename sweep
(`ctf` → `nethack`, `CTF_WIRE` → `NETHACK_WIRE`; a CI grep asserts no `ctf_` / `CTF_` identifier
survives outside comment history) plus the changes below. **The same modules compile twice**:
natively into `/bin/nethack` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language and the whole reason NLE/MiniHack are not an option here.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/nethack/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop at `server.nim:1407-1417` |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/nethack/` | **fork** (magic + game name only: `CtfReplayMagic = "COWLDCTF"` (`replays.nim:142`) → **`NethackReplayMagic = "COWLDNET"`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/nethack/` (`control.nim` → `driver.nim`) | **fork**, retargeted not rewritten | the per-turn batch (`decide.nim:427`), the two deadlines, `turnSpacingMs` (`decide.nim:386-389`), the budget guard (`decide.nim:328-346`), tolerant parsing (`directives.nim:102`), the rune caps, the fallback ladder and its two log phrasings (`decide.nim:463`, `:491`) |
| `src/ctf/sim_state.nim` → `src/nethack/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/nethack/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames` (`roster.nim:64`), the results JSON builder (`squadResultsJson`, `roster.nim:650`) |
| `src/ctf/events.nim` → `src/nethack/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/nethack/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/nethack/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/nethack/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps = 24` (`:376`), the flatty wire types (field order sacred), and the re-pinned `MaxSayRunes = 140`, `MaxNoteRunes = 400`, `MaxPromptRunes = 4000` |
| `src/ctf/sim_config.nim` → `src/nethack/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, and the validators at `:686-713` (whole-second `attempt1Ms`/`retryMs`, `attempt1Ms + retryMs ≤ turnBudgetMs`, non-negative `turnSpacingMs`, positive `wallClockBudgetSeconds`) — all kept, and §Decisions' numbers are chosen to satisfy them |
| `src/ctf.nim` → `src/nethack.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/nethack_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** (40 022 bytes, sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`) | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/nethack_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling, and its `docker cp` source path changes from `/workspace/ctf/replay-viewer/dist/.` to `/workspace/nethack/replay-viewer/dist/.` |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_red.png`, `data/soldier_red_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*.webp}` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, **fog-of-war
raycasting and the first-person raycast pipeline** (replaced by the exact lit-room rule above and a
2-D terminal panel), spray cans, floor paint and the paint grid, the paint buff, King of the Hill and
`hillTicks`, the `resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the
barrage, med kits, shields, cardboard barriers, trenches, perks, handicaps, lives and respawns,
**teams and four-team free-for-all** (there is one seat), **shouts-as-cog-speech and
`ShoutMaxChars`**, achievements, campaign mode, `maxGames > 1` side-swapping, and **all of the
pixel-space map machinery**: `arena.nim`'s wall masks and pixel queries, `map_art.nim`,
`mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`, `tools/map_editor*.nim`,
`tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `docs/pool-review.html`, `docs/MAPKIT.md`.
Dungeon levels here are fixed 48 × 18 integer cell grids built by seeded generators in code; every
one of those is a config surface the dungeon rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `*_front_gun`, `soldier_{blue,
green,yellow}*`, `rig_real/`) and the blue/green/yellow locker-room webps — there is one cog and it
is red.

### New modules

- `src/nethack/dungeon.nim` — the terrain enum, the glyph table, the passability and sight tables,
  the 48 × 18 level type, 8-adjacency in the fixed order `e, se, s, sw, w, nw, n, ne`, the
  corner-cutting rule, the BFS used by `travel` and by `delver`, the **lit-room visibility rule**,
  the memory merge, and the level **generator** with its connectivity postcondition. Pure integer;
  no pixie, no pixel queries.
- `src/nethack/mobs.nim` — the eleven-species table, the movement-point clock, the AI of §The game,
  the combat rules, and the death-cause strings.
- `src/nethack/items.nim` — the five item classes, the seeded potion-appearance permutation and the
  identification state, `eat` / `quaff` / `wield` / `wear`, the inventory letters, and the hunger
  clock.
- `src/nethack/minihack.nim` — the five authored ladder templates and their seeded details.
- `src/nethack/sim.nim` — the step loop of §The game exactly as numbered, `gameHash`, run-end
  evaluation, scoring, the deeds, and the seat's observation builder (including the ASCII map
  renderer, the message queue and the status-line renderer). Imports and re-exports the sim modules,
  as the starter's does, so `import nethack/sim` sees everything.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cell coordinates, hit points, damage, nutrition, movement
points, BFS distances, scores. There is no floating point anywhere in `sim.nim`, `dungeon.nim`,
`mobs.nim`, `items.nim`, `minihack.nim`, `driver.nim` or `baselines.nim`, and a test greps for it.
That makes the native ↔ wasm hash chain exact by construction.

**One seeded source, and it is a hash, not a stream.** Every generated quantity — room slots, room
rectangles, corridor elbows, door kinds, lit flags, stair cells, gold amounts, item kinds, potion
appearances, monster species and spawn cells, trap kinds and cells, every `d20`, every damage die,
every kick roll, every wander direction — is a read of the pure hash `mix64(seed, depth, salt)` or
`mix64(seed, depth, tick, salt)` (splitmix64 over the mixed words), evaluated independently. Nothing
the policy does can shift a draw, reorder draws, or consume one out from under a later level:
**level `k`'s layout is identical no matter what happened on level `k − 1`**, which is the strongest
form of the idea's "seeded dungeons per round" and what makes per-seed comparisons across policies
meaningful. `tests/test_nethack_dungeon.nim` asserts it by generating every level of a 500-seed sweep
under three different policy behaviours and comparing the full layouts byte for byte.

There is no other random draw. The seed is randomised in `src/nethack.nim` before `config.update`
(the starter's rule), recorded in the replay config and in `results.seed`. Two episodes with the same
seed and the same plans are byte-identical.

**Revisited levels.** A level's *mutable* state (items taken, doors opened, monsters killed and their
positions, traps discovered) is retained in memory for the whole episode; going `up` and back `down`
finds the level exactly as it was left. Levels are generated lazily on first arrival and never
re-generated.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDNET`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, variant, `num_agents`, every rule constant, the level ladder for
   `minihack`, `players[].name`, `slots[]`, `fastMode`), then the record stream — the join record,
   **per-turn plan records** (the only inputs this game has), chat records (`register` / `directive`
   / `fallback` / `budget_guard` / `stop` / `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/nethack_replay.nim` — which imports the
   **same** `src/nethack/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
3. In the browser, `nethack_load_replay` runs `parseReplayBytes` + `initReplayRuntime`;
   `nethack_frame` re-steps the sim from the recorded plans and compares `sim.gameHash()` against the
   recorded hash **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it
   happens and surfaced as `mismatchTick` in `#mmwarn`. **This is the idea's "action-log replay
   verification", running in the spectator's browser.**
4. **`gameHash` mixes**, in this fixed order: `depth`, `tick`; the cog's
   `(x, y, hp, maxHp, ac, xlevel, xpPoints, gold, nutrition, statusBits)`; then every cell of the
   **current** level in ascending `(y, x)` as `(terrain, doorState, trapKind, trapDiscovered,
   itemId)`; then every live monster on the current level in ascending index as
   `(species, x, y, hp)`; then the inventory as `(kind, id, count, equippedBits)` in letter order;
   then `depthReached`, the deeds bitmask, `monstersKilled`, `timesAte`; then `tick`.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact
   cannot be re-derived from sim state, so the stop is written as one record applied by the *same
   proc* on record and on playback, and `tests/test_nethack_replay.nim` runs the record → re-derive
   check for **every** end reason (`death`, `bottom`, `escaped`, `turnCap`, `wallClock`, `fault`),
   not just the healthy one (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 2200 hashes + ≤ 55 plan records + ~90 chat records ≈ **30 KB**. Everything else — every
level, every room, every monster, every item, every message line — is re-generated in the browser
from the seed, the variant and the action log.

### Documented divergences (mirrored into `docs/PORTING-NETHACK.md`)

1. **No NLE, no NetHack C source, no MiniHack dependency, and no bit-exactness.** Decided as a
   scoping rail before design. NetHack is a 250 kLOC C program with its own RNG and tty layer;
   NLE/MiniHack wrap it in Python. Embedding any of them means a simulator that cannot compile to
   wasm, so the static replay viewer — a non-optional pin — would be impossible. No upstream code is
   vendored, no upstream numbers are claimed as reproduced, and **no score from this coworld is
   comparable to an NLE, NetHack Challenge or BALROG number**. What is reproduced is the *problem*:
   a seeded procedurally generated multi-level dungeon, a text observation of glyphs + message line +
   stats, hunger, permadeath, and a depth ladder.
2. **48 × 18 maps, not NetHack's 80 × 21.** Chosen for viewer legibility (§Viewer → Legible at
   360 px); everything else about the map — rooms, corridors, doors, secret doors, stairs — keeps
   NetHack's shape and glyphs.
3. **Eight dungeon levels, one branch.** No Gnomish Mines, no Sokoban, no Big Room, no quest, no
   Gehennom, no Amulet, no ascension, no branch stairs, no trapdoors, no level teleporters.
4. **Eleven monster species, not hundreds.** No monster inventories, no pets, no ranged attacks
   (the arrow trap aside), no spellcasting, no polymorph, no engulfing, no corpses (and therefore no
   corpse-eating and no petrification).
5. **Five item classes.** Gold, food, potions, weapons, armour, with the small tables above. No
   scrolls, wands, rings, amulets, spellbooks, tools, gems, artifacts, containers or shops; no
   blessed/cursed status; no enchantment; no encumbrance; no erosion.
6. **No roles, races, alignments, gods, prayer, luck or attributes.** One implicit role, "the
   Digger", with a fixed starting kit. NetHack's prayer — the classic get-out-of-jail for
   starvation — is deliberately absent, which is what makes the hunger clock bite.
7. **Nutrition is a flat 1 per tick** and `Fainting` does not cause random fainting; starvation kills
   at −200. NetHack's hunger is more elaborate and its `Fainting` state is stochastic.
8. **Turn model.** One primitive = one dungeon turn; monster speed is movement points per 12 ticks;
   the only multi-turn occupations are pit escape (3), lichen stickiness (3), potion sleep (10) and
   the floating eye's paralysis (12). No speed potions, no fast/slow, no elbereth.
9. **Keystrokes are named verbs in JSON, batched under a driver, not raw tty keys stepped one per
   call.** The idea's "keystroke per turn over a text observation" is preserved as the primitive set
   and the text observation; what changed is *who calls it*. Ten commands per LLM turn expanding to
   at most forty primitives, with `travel` (NetHack's own `_` command) as the one macro. One LLM call
   per keystroke would be 2200 calls in a 720 s budget — impossible — and a policy that cannot
   express "walk over there" spends every turn walking one square.
10. **`autoopen` is on** (moving into a closed unlocked door opens it, spending the tick), and
    **locked doors are opened by `kick` only** — no `#force`, no unlocking tools, no key items.
11. **The Oracle is `O`, not a white `@`**, and the consultation is a flat 50 gold for the compass
    direction of the down staircase plus a scored deed. NetHack's minor/major consultations, the
    fountains and the centaur statues are absent.
12. **Vision** is the lit-room / radius-1 rule above. No light sources, no blindness, no telepathy,
    no infravision, no clairvoyance, no magic mapping.
13. **Searching is deterministic** (three adjacent searches always reveal), where NetHack rolls each
    turn. Chosen so a level can never be permanently unsolvable in a 55-turn budget.
14. **Score is not NetHack's score formula.** NetHack scores gold + 50 × (deepest − 1) + experience
    and multiplies for ascension; this game makes depth strictly dominant (§The game) because the
    idea's motive is "score / depth attack" and the league needs one rankable integer. All the
    underlying quantities are in `results`, so an NLE-style per-run report is directly readable.
15. **Permadeath is faithful and total**: one life, no life saving, no amulet of life saving, no
    save/restore, no quit, no `#chronicle`.
16. **`maxGames = 1`** — the starter's multi-game episode is not used; a dungeon run has no side to
    swap.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with a variable turn length (the tick loop breaks early
   when the run ends or the cog changes level) and one seat in the batch.
2. **Registration interception** — the seat's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed
   as registration, **not** applied as a shout and **not** written to the replay chat stream; the
   server writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim, and the server **logs loudly and refuses to start the game** when the joined seat has no
   register record (the grf-football 2026-08-27 silent-default scar). Any other chat text from the
   seat is dropped — the cog speaks through `say`.
3. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration (`server.nim:1407-1417`), kept, forcing `phase = GameOver`, `reason = deadline`,
   `endRule = wallClock`, and written as the load-bearing stop record of §Determinism point 5.

### The two named edits to `roster.nim`

1. **Alias.** `seatAlias(slot)` returns `IdentityNames[slot]` title-cased → **`Alpha`** for the only
   seat, rendered in-world as `Alpha the Digger`. The `IdentityNames` array itself
   (`roster.nim:64-65`) is unchanged. Board labels and the label manifest inherit the two-name-space
   rule with no further change, and `showPlayerLabels` is false.
2. **`squadResultsJson` → `runResultsJson`** (`roster.nim:650`) — one entry per seat, one entry in
   every seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a 48 × 18 cell grid, not a pixel arena.** `buildSpriteProtocolPlayerUpdates` emits
   cell-space coordinates; the raycast fov cache and shadowcasting are deleted and replaced by the
   lit-room visibility rule's boolean mask plus the per-level memory mask, which the viewer draws as
   the two-level dark wash.
2. **Monster, item and feature pools.** New pools `MonsterBase` (sized to 12), `ItemBase` (sized to
   16) and `FeatureBase` (doors, stairs, traps, the Oracle; sized to 32), filled in ascending
   `(y, x)` and emitted incrementally like the starter's other object families.
3. **Baked dungeon bed.** `arena_floor.png` is tiled and darkened at install with pixie, exactly the
   way the starter bakes endzone paint, and the floor grain, the corridor gravel and the wall bevels
   are baked onto it once (§Viewer → Art) — one static bake per level size, so the per-frame cost is
   the cog, ≤ 12 monsters, ≤ 16 items, ≤ 32 features and the two wash masks.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST` / `PORT`; the player
socket at `/player?slot=0&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering
for the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). The
player websocket handler **closes unless the token matches the seat** (the certifier probes with a
bad token — cogame-flatland 0.1.1). Global broadcasts are fire-and-forget so a slow viewer can never
stall the episode.

### Results document (closed schema; `runResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":              ["daveey"],
  "aliases":            ["Alpha"],
  "scores":             [309240],
  "win":                [true],
  "winner":             0,
  "reason":             "complete",
  "endRule":            "death",
  "variant":            "descend",
  "seed":               1734029581,
  "dungeonLevels":      8,
  "parDepth":           4,
  "depthReached":       4,
  "finalDepth":         4,
  "gold":               214,
  "xpPoints":           42,
  "xlevel":             3,
  "monstersKilled":     11,
  "itemsPicked":        7,
  "timesAte":           2,
  "potionsQuaffed":     1,
  "oracleConsults":     0,
  "doorsKicked":        1,
  "trapsTriggered":     2,
  "deeds":              ["fed"],
  "deedCount":          1,
  "hpFinal":            0,
  "maxHpFinal":         21,
  "causeOfDeath":       "killed",
  "killer":             "hill orc",
  "levelTurns":         [6, 9, 7, 5, 0, 0, 0, 0],
  "levelTicks":         [214, 331, 268, 187, 0, 0, 0, 0],
  "levelKills":         [3, 4, 3, 1, 0, 0, 0, 0],
  "levelGold":          [41, 78, 95, 0, 0, 0, 0, 0],
  "cellsSeen":          712,
  "cellsTotal":         6912,
  "primitivesExecuted": 934,
  "actionsDropped":     4,
  "macrosUnreachable":  3,
  "repliesRepaired":    1,
  "finalTick":          1000,
  "turnsPlayed":        27,
  "policyKinds":        ["llm"],
  "llmTurns":           26,
  "fallbackTurns":      1,
  "deadSeats":          [false],
  "stopDetail":         ""
}
```

`causeOfDeath` is a closed enum: **`killed` | `starved` | `burned` | `none`** (`none` for a run that
ended by `bottom`, `escaped`, `turnCap`, `wallClock` or `fault`). `killer` is the species name, or
`"starvation"`, `"lava"`, or `""`. `deeds` is a subset of `["fed", "hoard", "oracle"]` in that fixed
order. The per-level arrays are always `dungeonLevels` long, zero-filled for levels never visited.
`cellsTotal` is `levelW × levelH × dungeonLevels` = `48 × 18 × 8` = 6912. `primitivesExecuted` counts
every primitive that was **not** `wait`, so `finalTick − primitivesExecuted` is the number of dungeon
turns the cog stood still. Five identities hold in every results document and are asserted by
`tests/test_nethack_engine.nim`:
`Σ levelTurns == turnsPlayed`; `Σ levelTicks == finalTick`;
`Σ levelGold ≤ gold` is **not** asserted (gold is also dropped by gnomes — instead
`Σ levelGold == goldPickedUp`, a recorded intermediate);
`depthReached == max{ i+1 : levelTicks[i] > 0 }`; `deedCount == len(deeds)`; and
`scores[0] == 100_000 × (depthReached − 1) + 10 × min(gold, 2_000) + 50 × min(xpPoints, 1_000) +
5_000 × deedCount`. The example satisfies the last one: `100_000×3 + 10×214 + 50×42 + 5_000×1 =
300_000 + 2_140 + 2_100 + 5_000 = 309_240`.

Adding a key means updating `runResultsJson`, the manifest's `results_schema` and
`tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld schemas are closed and
undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDNET`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (`SMOKE_REQUIRE_REPLAY_JSON`, template line 31).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"nethack/v1","gameVersion":"1","seed":…,"variant":"…","names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"plans":[…],"says":[…],"fallbacks":N,"results":{…}}` — by
  brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md`
  documents for prod forensics) and decoding the chat records.
- **The phase-60 substitute for `docs/SPEC.md` §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.endRule, .results.depthReached' /tmp/ep.json
  jq -r '[.plans[]|select(.source=="llm")]|length, .fallbacks, (.says|length)' /tmp/ep.json
  ```
  Require `protocol == "nethack/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.depthReached >= 2`, and the champion seat's plans with `source == "llm"`,
  real verbs (including at least one `travel` and at least one `down`) and non-empty `say` lines —
  not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDNET`, format version, `gameName` `nethack`, `gameVersion` `1` |
| config JSON | `seed`, `variant`, `num_agents`, `levelW`, `levelH`, `dungeonLevels`, `levelLadder` (empty for `descend`), `turnTicks`, `maxTurns`, `maxTicks`, `parDepth`, `maxActionsPerTurn`, `macroPrimitiveCap`, `startHp`, `startNutrition`, `consultCost`, `searchesToReveal`, `searchBurst`, `aggroRange`, `players[].name` (real name), `slots[]`, `fastMode` |
| join | the seat's `name` (real policy name), `slot`, `token` |
| plans | per turn: the accepted action list — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

**The dungeon generator, the monster table, the item tables and the message strings are code,
compiled into both the binary and the wasm module**, and the replay carries the seed, the variant and
every rule constant; the viewer therefore reconstructs every level, every monster, every item, every
message line and every status line from bytes it already has, with no fetch. A generator change is a
`GameVersion` bump, and the committed fixtures' version sweep makes an unversioned change fail the
build.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields;
they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `depth`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `actions` (the accepted array), `executed` (the primitives that ran), `truncated`, `dropped`, `unreachable`, `say` (≤ 140 runes), `obs` (the observation **minus `map` and `notes`**: status line, messages, visible, inventory, level, deeds) |
| `fallback` | `turn`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of twenty-one kinds, plus `end`:**

`turn` `{n, depth}`; `plan` `{n, verbs, truncated, dropped}`; `say` `{text}`; `fallback` `{cause}`;
`descend` `{from, to}`; `ascend` `{from, to}`; `kill` `{monster, x, y}`;
`hurt` `{by, dmg, hp, maxhp}`; `gold` `{amount, total}`; `item` `{name, letter}`;
`eat` `{name, nutrition}`; `quaff` `{appearance, effect}`; `trap` `{kind, dmg}`;
`door` `{action: open|kick|locked, x, y}`; `oracle` `{paid, hint}`; `levelup` `{xlevel, maxhp}`;
`deed` `{name}`; `hunger` `{state}`; `death` `{cause, killer, depth, tick}`; `bottom` `{depth}`;
`escaped` `{depth}`; plus `end` `{reason, endRule, depth, score}`.

`tests/test_nethack_events.nim` asserts the emitted set equals exactly this list. `plan` and `turn`
fire once per turn (≤ 55 each); `hurt` fires only when the cog **takes** damage, so it is bounded by
the fights it chooses; nothing fires per tick, so the feed never floods.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`descend`,
`ascend`, `levelup`, `deed`, `oracle`, `death`, `bottom`, `escaped`, `fallback`, `end`.** `turn`,
`plan`, `say`, `kill`, `hurt`, `gold`, `item`, `eat`, `quaff`, `trap`, `door` and `hunger` drive the
feed, not the scrubber (a fight would otherwise carpet the timeline).

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `TurnStart, Directive, Fallback, Primitive, Attack, Damage, Kill, Pickup,
Eat, Quaff, DoorOpen, DoorKick, TrapTrigger, Descend, Ascend, LevelUp, Deed, Oracle, Death` and the
mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept. `Primitive` is the
per-tick row that makes this stream a full action trace for `cogamer-rl` — up to 2200 rows an
episode, which is what a long-horizon RL consumer needs and what the replay deliberately does not
carry.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed
(`/workspace/ctf/replay-viewer/dist/.` → `/workspace/nethack/replay-viewer/dist/.`) — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/nethack_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
which is this repo's own starter. **Never a mixture.** Splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE` / `EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks
the viewer silently (cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one
piece: the Worker sets `Module.onRuntimeInitialized`
(`replay-viewer/static_replay_worker.js:188`), the module is emitted **non-modularized** as
`nethack_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang` through `emcc`,
`--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable:
with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and corrupt the module's own globals — the
starter's own comment at `replay-viewer/config.nims:33-41`), `-s FILESYSTEM=1`,
`-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_nethack_load_replay,_nethack_frame,_nethack_input,
_nethack_packet_ptr,_nethack_packet_len,_nethack_mismatch_tick,_nethack_error_ptr,
_nethack_error_len,_nethack_stage_ptr,_nethack_stage_len`; and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './nethack_replay.js')` in that order
(the starter's line 239, renamed only).

`nethack_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress
buffer that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`,
and the `emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running
module destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `nethack_load_replay` re-simulates the whole episode once headlessly
  (2200 ticks over 864-cell levels — a few milliseconds in wasm), records the per-tick depth, HP,
  score and cells-seen series, the level-arrival ticks, the beat ticks and the lull spans, then
  resets and renders frame 0. That is what lets the depth ladder, the sparkline and the scrubber
  beats draw at **full width on the first frame** instead of growing in.
- `nethack_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (`replay-viewer/static_replay.js:158-161`) —
posted by the Worker only *after* `ingestPacket()` (`static_replay_worker.js:64`) has handed
BroadcastCore the first frame and it has drawn, so the attribute means "a frame is on the canvas",
not "a file was fetched". On failure it sets **`data-replay-error`** on `<html>` with the message, in
`showFailure()` (`static_replay.js:8-20`). Both are coworld-ctf's own signals, inherited unchanged —
this fork adds neither and removes neither. The `coworld-replay` postMessage bridge's `ready` is
posted **from a callback fired after** `data-replay-loaded="true"` is set, never on rAF timing at the
call site (chorus `3c11c953`, 2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes; sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`). Not edited, not reformatted;
  `tests/test_nethack_viewer.nim` pins that sha256 as a literal. Everything this game adds lives in
  the appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats` / `renderClock` /
  `renderTransport` / `ingestLullSpans` / `renderMomentum` remain; `ingestBeats` ignores kinds it does
  not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (`client/replay_broadcast.html:4276-4325`), transport, endcard, locker-room loader, `?embed=1` mode
  and `.tiny` density system are untouched, and the block is installed through the starter's own
  splice hook: `window.PaintballChrome` (context built at `:4330`, installed at `:4337`) is renamed
  `window.NethackChrome` and its `install(PB_CTX)` / `frame(s, ctx, jumped)` (`:2075`) /
  `event(e, s, ctx)` (`:3480-3481`) entry points are kept with the same signatures. The appended
  block replaces only the *contents* of the scorebug plates, adds the depth ladder, the two-level
  dark wash and the terminal panel's drawing, and retargets the feed rows, the beat rendering, the
  momentum series and the endcard columns. The block sits after the starter's banner comment at
  `:4344` and a test asserts the starter's byte prefix is intact up to that marker and that the file
  only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text
  by `tests/test_nethack_viewer.nim`: the canvas/DPR sizing, `relayout()`, **the camera and
  `attachMinimap`** (both kept and used — see the zoom decision), the feed queue and `pushFeed`
  **including its signature** (the cogball 0.1.4 latch scar: a signature drift threw mid-replay and
  latched `static_replay.js` into `failed`), `banner`, the beat and lull machinery, the endcard
  builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` → `window.NETHACK_WIRE`
  rename emitted by `tools/gen_wire_constants.nim`. Deleted: every ctf-specific draw call and the
  raycast FPV pipeline (the `#fpv` **canvas** is reused as the terminal panel, the raycaster is not).
  Added: `drawDungeonBed`, `drawTerrain`, `drawFeatures`, `drawItems`, `drawMonsters`, `drawCog`,
  `drawMemoryWash`, `drawTerminalPanel`, `drawDepthLadder`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#povBadge`** (`replay_broadcast.html:1525`) and the `togglePov` wiring — with one seat there
    is nothing to select.
  - Inside the kept `#fpv`: **`#fpv-hp`** (`:1537`), **`#fpv-gear`** (`:1538`), **`#fpv-map`** and
    **`#fpv-map-canvas`** (`:1542-1543`) — the terminal panel already draws the status line, and a
    second small map is redundant next to the kept `#minimap`.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip` (`:300-330`), `.pb-tags`, `.squad` (`:2219-2244`), and the `.ec-heart` endcard glyphs
    (`:1221-1231`).
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture` (`:919-934`) and `.gamestart`,
    `.hillflip`, `.tagout`, `.gameover` (`:4431-4443`) CSS rules — those kinds are never emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS, `:245`).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with `#plates-l` / `#plates-r` /
    `#clock` / `#clock-time` / `#clock-caption` / `#ffwd-mini`, **`#viewpanel` in full** (`#minimap`,
    `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`, `#zoom-slider`, `#zoom-read`,
    `:1510-1521`, and the page's `core.attachMinimap($('minimap-canvas'))` call at `:4200`),
    **`#fpv` with `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-cap` and `#fpv-grip`** (repurposed as
    the terminal panel, caption `TERMINAL 48×18`, `#fpv-name` reading `ALPHA THE DIGGER · DLVL 3`,
    still draggable and resizable by the starter's own grip), `#bannerlane`, `#killfeed`, `#mmwarn`,
    **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`,
    `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`, `#tick-clock`,
    `#speedchips`), `#scrub` with `#momentum` / `#scrub-fill` / `#lulls` / `#scrub-win` /
    `#scrub-head`, `#endcard` with `#ec-headline` / `#ec-wincond` / `#ec-how` / `#ec-teams` /
    `#ec-replay`, and `#status`.

**Zoom decision: `#viewpanel` is KEPT.** The pin says the zoom bar and minimap exist only for boards
larger than the frame. **This board is larger than the frame**: a dungeon level is 48 × 18 cells and
the viewer clamps the cell size to a **minimum of 12 px**, so at any width below ~600 px the camera
shows a window of the level and follows the cog rather than shrinking the dungeon to illegibility
(§Legible at 360 px). That is precisely the case the starter's own game-block banner describes
("classic boards can be colossal"), so `#minimap` (the whole level, 2 px per cell, with the cog, the
stairs and the seen region marked) and `#zoombar` (reading `1.6×`, `FIT` at desktop width) are kept,
wired exactly as the starter wires them. `#plates-r` is kept and **carries the three deed chips**
(`FED`, `HOARD`, `ORACLE`, lit when earned) — it is one of the scorebug's three flex columns and
leaving it empty would un-centre `#clock`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here
and enforced by a test:

| Starter string (`client/replay_broadcast.html:line`) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (`:3795`) | `<span>Dlvl</span><span>Turns</span><span>Kills</span><span>Gold</span><span>Seen</span>` |
| `<div class="ec-thead"><span>Cog</span><span>Tags</span><span>Out</span><span>Paint</span></div>` (`:3788`) | `<span>Cog</span><span>Depth</span><span>Gold</span><span>Score</span>` |
| `<span class="fl-cap">Lives left</span>` (`:3793`) | `<span class="fl-cap">Deepest level</span>` |
| `<span class="fl-cap">Hill time</span>` (`:3786`) | `<span class="fl-cap">Experience</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (`:1576`) | `<span class="momentum-label">DEPTH</span>` |
| `<span class="lives-label">Lives</span>` (`:2241`) | `<span class="hp-label">HP</span>` |
| `<span class="lives-label pb-lbl">Hill</span>` (`:2224`) | `<span class="hp-label pb-lbl">Hunger</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (`:1480`, `:1842`) | "Rolling up the dungeon…" |
| `#clock-caption` "In the locker room" (`:1499`) | "Waiting for the cog" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (`:1524`) | "Replay hash mismatch at tick N — showing recorded actions" |
| `#fpv-cap` "EYES" (`:1545`) | "TERMINAL 48×18" |
| `#btn-spoilers` title "Spoilers: kills / flag story / winner on the timeline ahead of the playhead (o)" (`:1564`) | "Spoilers: descents and the death on the timeline ahead of the playhead (o)" |
| team words `RED` / `BLUE` in `.ec-tname` / plates (`:2222`, `:2239`, `:3783`, `:3790`, `:3836`) | the seat's **alias** (`ALPHA THE DIGGER`) on the plate, and `DUNGEON LEVEL n` as the endcard section head |

**`tests/test_nethack_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `EYES`, `spray`, `grenade`, `med kit`, `team` — outside comment blocks, and asserts
**zero** matches; and asserts each replacement string above is present exactly once. (`kill` is
deliberately **not** forbidden here: killing monsters is this game's own vocabulary, and `#killfeed`
is a kept starter id.) A rename that reintroduces paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (`client/replay_broadcast.html:4291-4317`). **No overlay sits in the transport
band**: the board is laid out between the two bands and every addition here (the depth ladder, the
terminal panel, the feed, the deed chips) is positioned inside the board region or in the top band,
never below `100% - var(--band)`. The **endcard stops at `var(--band)`**
(`#endcard { bottom: var(--band, 0px) }`, `:1047`, the starter's rule, kept) so the scrubber stays
clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `nhBeat(tick, kind, label)` — named with the `nh-` prefix so it can
never shadow `chrome_common.js`'s `markBeat` alias (`client/replay_broadcast.html:1635`; the tandem
2026-08-23 hoisting trap, and the same prefix discipline the starter's own `pbBeat` at `:4475` uses)
— appends `<button class="beat-marker <kind>" title="…" aria-label="…">` to `#scrub` and seeks on
click. CSS exists for **every kind emitted and no others**: `.beat-marker.descend`,
`.beat-marker.ascend`, `.beat-marker.levelup`, `.beat-marker.deed`, `.beat-marker.oracle`,
`.beat-marker.death`, `.beat-marker.bottom`, `.beat-marker.escaped`, `.beat-marker.fallback`,
`.beat-marker.end`. The game block never calls `markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: one tick per two animation frames at 30 fps = 15 ticks/second** (speed chips
`[0.5, 1, 2, 4, 8]`, default 1), with the cog's and the monsters' positions interpolated across the
two frames so a step glides rather than snapping. A full 2200-tick episode therefore plays for
**147 s** at 1× and 18 s at 8×; a typical run that ends in death around tick 1000 plays for 67 s. The
skip-lulls control (a lull = 40 consecutive ticks with no `kill`, `hurt`, `gold`, `item`, `door`,
`trap`, `descend` or `deed` event, from the pre-scan) compresses long corridor travel, and
`viewer_smoke.mjs --soak 10` always observes real advancement (the ecos 2026-08-23 scar).

### Readouts

1. **The dungeon**, drawn as tiles with the camera following the cog: the baked stone bed; room
   floors and corridor gravel; bevelled masonry walls; doors as timber panels (a keyhole when
   locked, swung open when open, a dark arch for a doorway); staircases as cut steps with a down/up
   chevron; discovered traps as a sprung-metal chip; lava as an animated two-frame bake; gold, food,
   potions, weapons and armour as their own baked chips; the eleven monster species as composited
   chips carrying their letter; the Oracle as a robed chip; and the **cog** as the composited soldier
   rig with a facing wedge.
2. **The two-level memory wash** — every cell never seen is fully dark; a cell seen but not currently
   visible is drawn at 45 % with its remembered contents and **no monsters**; a cell in the current
   visible set is drawn clean and bright with everything on it. The spectator therefore sees, at a
   glance, **how much of the level the cog knows and what it is walking into blind** — the single
   most important readout in this game, and the one that makes a fatal mistake legible as a mistake.
3. **The terminal panel** (the idea's "ttyrec playback", honestly re-implemented) — the repurposed
   `#fpv` panel, bottom-right, drawing **exactly the text the cog receives**: the 48 × 18 glyph map in
   `data/font.ttf` at the panel's measured monospace cell size, the last message line beneath it, and
   the status line `Dlvl:3 $:214 HP:9(14) AC:7 Xp:3/42 T:517 Hungry` beneath that, captioned
   `TERMINAL 48×18` with `ALPHA THE DIGGER · DLVL 3` above. This is what a spectator watches to
   understand that the policy is reading text, not pixels. Draggable and resizable by the starter's
   own `#fpv-grip`.
4. **The depth ladder** (the idea's ask) — a vertical ladder of `dungeonLevels` rungs pinned to the
   board's left edge: each rung is labelled `DL1 … DL8`, filled when visited, ringed when current,
   marked with a skull on the level where the run ended, and captioned with the tick the cog arrived.
   The deepest rung reached is drawn with a bright rule across it — the "dungeon level reached"
   readout, present from the first frame courtesy of the pre-scan.
5. **Clock** — `#clock` shows the big numeral `DLVL 4`; `#clock-time` shows `T:1000 · turn 27/55`;
   `#clock-caption` shows `HP 0/21 · $214 · Weak · score 309240`.
6. **Scorebug** — `#plates-l` carries one plate: the seat's **real policy name** (spectator side
   only), its in-game alias `ALPHA THE DIGGER`, the cog avatar from `data/soldier_red_front.png`, the
   running score as the numeral, an **HP bar**, a **hunger chip** (`Satiated … Fainting`, amber at
   `Hungry`, red at `Weak`), and a `↯` glyph if the seat has taken a fallback. `#plates-r` carries the
   three **deed chips**.
7. **Match feed** (`#killfeed`) — plain language, never internal notation:
   `DESCENDED TO DUNGEON LEVEL 4`, `KILLED A SEWER RAT`, `THE HILL ORC HITS — 6 DAMAGE, 3 HP LEFT`,
   `PICKED UP 43 GOLD PIECES`, `ATE A FOOD RATION`, `DRANK THE SMOKY POTION — IT WAS SLEEPING`,
   `KICKED THE LOCKED DOOR OPEN`, `FELL INTO A PIT — 4 DAMAGE`, `CONSULTED THE ORACLE — 50 GOLD`,
   `DEED EARNED: FED`, `WELCOME TO EXPERIENCE LEVEL 3`,
   `Alpha: "rat first, then the gold, then the closed door west"`, and
   `MISSED THE CALL — delver plan (timeout)`. The `say` lines and the plan lines are where a
   spectator sees the LLM playing.
8. **The death-cause feed line and tombstone** (the idea's ask) — the moment the run ends, the feed
   prints the NetHack death line in full: `ALPHA THE DIGGER, KILLED BY A HILL ORC ON DUNGEON LEVEL 4,
   WITH 309240 POINTS.` and `#bannerlane` holds it for three seconds.
9. **Depth sparkline** — the starter's `#momentum` SVG retargeted to the cumulative **depth** series
   drawn as a descending staircase (deeper = lower on the chart), with a red band behind every span
   where `hp × 3 ≤ maxHp` and a hatched band where hunger is `Weak` or worse, and the playhead
   marked. Filled from the load-time pre-scan, so it draws at full width on the first frame. A long
   flat line at DL 2 inside a red band is the whole story of a run in one glance.
10. **Endcard — a tombstone.** The starter's endcard, re-laid as NetHack's: a graven headstone
    reading `ALPHA THE DIGGER / KILLED BY A HILL ORC / ON DUNGEON LEVEL 4 / 309240 POINTS`, the
    re-mapped per-level table (`Dlvl | Turns | Kills | Gold | Seen`), a summary line (`11 monsters
    killed, 214 gold, 2 meals, 1 door kicked, 712 of 6912 cells seen, 1 fallback turn`), the three
    deed chips, and `SCORE 309240`. For a `bottom` / `escaped` / `turnCap` run the headstone becomes a
    plaque with the matching headline (`REACHED THE BOTTOM`, `ESCAPED THE DUNGEON`, `OUT OF TIME`).
    It stops at `var(--band)` and any seek dismisses it.
11. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls,
    spoilers switch, tick readout, speed chips, the scrubber with its ten beat kinds, the zoom bar,
    the minimap, and `#mmwarn` on a hash mismatch — all the starter's, verbatim.

### Art

**Real art, from the starter's shipped assets plus install-time bakes — no placeholders, no
solid-colour squares, no downloads.** The floor is `data/arena_floor.png`, tiled and darkened 40 %,
with baked flagstone seams in the palette from `data/pallete.png` — one pixie bake at install,
exactly the way the starter bakes endzone paint; corridors are the same bed at 60 % with a gravel
grain. **Walls** are cut from `client/art/walls/wall_h.jpg` and `wall_v.jpg` at cell size with a baked
bevel and a shadow lip, so a wall run reads as dungeon masonry rather than a black bar. **Doors** are
baked once: 3 states (timber panel, panel with a keyhole, arch swung open) plus the broken state.
**Staircases** are baked cut steps with a chevron. **Lava** is a two-frame procedural bake in the
palette's reds and oranges with a crust pattern, cycled at 4 Hz. **Items** are baked once per kind:
gold heap, three foods, six potion colours (matching the seeded appearance names), four weapons,
three armours = **17 chips**, drawn in the palette with a specular. **Monsters** are the eleven
species baked from `data/ascii.png`'s glyph set composited over a species-tinted body chip, so a
`d` reads as a jackal-coloured shape carrying its letter — legible at 12 px and unmistakable at
24 px; the Oracle gets a robed chip. The **cog** is `data/soldier_red.png` composited by
`rig_art.nim` into 4 facings × 2 sizes = **8 chips**; `data/soldier_red_front.png` is its avatar on
the scorebug plate and on the tombstone. The terminal panel, every chrome numeral and the tombstone
lettering are set in `data/font.ttf`. The memory wash, the depth ladder, the deed chips and the
sparkline are procedural in the bed bake's palette. The loading screen is the starter's locker room
(`client/art/lockerroom/bg.jpg` plus the four red webps) with the caption re-labelled.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (`client/replay_broadcast.html:4307-4312`).

The arithmetic, stated: a level is 48 × 18 cells. In a 360 × 203 frame, `relayout()` reserves
`--topband` and `--band`, leaving a play region of roughly 360 × 120. Fitting the whole level would
give `360/48 = 7.5` px per cell — **illegible**, and the reason this game does not letterbox. Instead
the renderer clamps cell size to **`minCell = 12` px** and centres the camera on the cog, so at
360 px the board shows a **30 × 10-cell window** of the level, panning as the cog moves. The board is
therefore **larger than the frame**, which is why `#viewpanel` is kept: `#minimap` draws the whole
48 × 18 level at 2 px per cell (seen region, stairs, cog, deepest rung) in the corner, and `#zoombar`
reads `1.6×`. At desktop width (≥ 620 px board) the level fits whole at ≥ 12 px per cell and the zoom
bar reads `FIT`.

Because the board fills the frame there are no letterbox gutters at 360 px, so every addition is an
overlay **inside the board region** — never in the transport band. Five rules are added and asserted
by `tests/test_nethack_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, the single plate keeps only `alias + name + score + HP bar + hunger chip`; the
   avatar shrinks to 10 px and the fallback glyph moves inline; the three deed chips in `#plates-r`
   become 8 px dots with tooltips.
3. Under `.tiny`, the **depth ladder** pins to the board's left edge as a 24 px-wide strip of eight
   10 px rungs with the level numbers dropped to tooltips and only the current and deepest rungs
   labelled.
4. Under `.tiny`, the **terminal panel** drops the 48 × 18 glyph grid — 7.5 px monospace is not
   legible — and renders **only the message line and the status line**, two rows at 9 px, pinned
   bottom-right above the band, with `#fpv-grip` resizing disabled below 620 px so it cannot be
   dragged over the board. At ≥ 620 px the full glyph grid returns. In both modes the panel measures
   its own cell size from its pixel box and **drops any row that would not fit** rather than drawing
   outside the canvas, so `--strict-text-bounds` (which the CI viewer smoke keeps **on**) stays
   satisfied.
5. Under `.tiny`, the memory wash uses a **two-step** (unseen / seen-or-visible at higher contrast)
   instead of the three-step, because a 12 px cell under a 45 % wash loses its item chip.

---

## Packaging

- **Repo**: `Metta-AI/cogame-nethack`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `nethack`; **`game.name` is `nethack`** —
  identical to the slug, so the secret namespace `secret://coworld/nethack/anthropic_api_key`, the
  page slug, the `POST /coworld-league-seeds` body and the docs all agree (the commons-family
  2026-08-24 scar, where `game.name` and the slug differed by an underscore).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two services/two
  images (`compose.yaml` `game` + `player`); this fork uses the one-image / two-entrypoints shape
  because the shared `docker_smoke.sh` and `policies.json` assume a single image (the knights-archers
  precedent):

  ```yaml
  services:
    nethack:
      image: coworld-nethack:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{NETHACK_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:nethack src/nethack.nim` →
  `/bin/nethack`, and the same for `src/nethack_player.nim` → `/bin/nethack-player`. The runtime
  stage copies both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/nethack"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block)
  with the asset list swapped to `data/{arena_floor,ascii,pallete}.png`,
  `data/soldier_red{,_front}.png`, `data/font.ttf`, `client/art/walls/*`,
  `client/art/lockerroom/{bg.jpg,red_*.webp}`, `nethack_replay.{js,wasm,data}`, `wire_constants.js`,
  `broadcast_core.js`, `chrome_common.js`, `static_replay.js`, `static_replay_worker.js`,
  `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["roguelike", "single-agent", "procedural-generation",
    "long-horizon", "text-observation", "nethack"]` (≥ 3; `game.tags` must **not** exist —
    pistonball 0.1.0); **`episode_timeout_minutes: 20` at the top level**, not under `game`.
  - `game.name = "nethack"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/nethack"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/nethack/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 1/1, `players` 1/1, `slots` 0/1, `levelLadder` 0/5 — the tandem 0.1.0 scar). `tokens`
    is described as runner-injected; **no `game_config` anywhere in this manifest contains a literal
    `tokens` array** (matriculate rejects "game_config must not include runner-managed tokens" —
    knights-archers 0.1.0), while `config_schema` keeps *requiring* it because the runner injects it.
    Properties: `tokens`, `players`, `slots`, `seed`, `num_agents`, `minPlayers`, `levelW`, `levelH`,
    `dungeonLevels`, `levelLadder`, `turnTicks`, `maxTurns`, `maxTicks`, `parDepth`,
    `maxActionsPerTurn`, `macroPrimitiveCap`, `startHp`, `startNutrition`, `consultCost`,
    `searchesToReveal`, `searchBurst`, `aggroRange`, `attempt1Ms`, `retryMs`, `turnBudgetMs`,
    `turnSpacingMs`, `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `gameOverTicks`, `fastMode`,
    `showPlayerLabels`, `model`, `maxOutputTokens`; with **`num_agents`** an integer, `minimum: 1`,
    `maximum: 1`, default 1.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}`,
    `endRule: {"type":"string","enum":["death","bottom","escaped","turnCap","wallClock","fault"]}`,
    `causeOfDeath: {"enum":["killed","starved","burned","none"]}` and `deeds` items
    `{"enum":["fed","hoard","oracle"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-nethack/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"actions.md","title":"Actions and the reply format","content":{"type":"uri","value":".../docs/ACTIONS.md"}},
    {"id":"porting.md","title":"What this is and is not a port of","content":{"type":"uri","value":".../docs/PORTING-NETHACK.md"}}]}`.
  - Top-level `player[]` with `id` / `type` / `name` / `description` / `image` / `run` /
    `source_url` and `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` —
    **`limits.cpu` must be at least `"1"`** (pistonball 0.1.1). **Exactly ONE entry, `delver`**:
    `num_agents = 1` leaves exactly one certification slot, and **every declared player must occupy a
    certification slot** (the raid 0.1.2 scar), so a second declared player could not be seated.
    `bumbler` still ships in the image, is exercised by `tests/test_nethack_driver.nim`, and is a
    league filler in `tools/ci/policies.json` — it is simply not a *declared manifest* player.

  **Variants — `num_agents: 1` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "descend", "name": "The Descent (1 cog, 8 procedurally generated levels)",
     "description": "One cog, one life, eight levels of a dungeon generated fresh from this round's seed. Rooms, corridors, locked doors and secret passages; eleven kinds of monster; gold, food and unidentified potions; traps you cannot see until you step on them; and a hunger clock that will kill you if you ignore it. The cog reads an ASCII map, a message line and a status line - the same text a NetHack player reads - and answers with commands. Score is how deep it got.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "levelW": 48, "levelH": 18, "dungeonLevels": 8, "levelLadder": [],
                     "turnTicks": 40, "maxTurns": 55, "maxTicks": 2200, "parDepth": 4,
                     "maxActionsPerTurn": 10, "macroPrimitiveCap": 40,
                     "startHp": 12, "startNutrition": 900, "consultCost": 50,
                     "searchesToReveal": 3, "searchBurst": 8, "aggroRange": 10,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9500, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "minihack", "name": "MiniHack ladder (1 cog, 5 authored levels)",
     "description": "Five small hand-authored levels in a fixed order, each seeded: a long winding corridor, a lava river with one bridge, a room with four monsters between the cog and the stairs, a vault whose only door is locked and must be kicked open, and the Oracle's level. Same dungeon, same permadeath, same text observation - but each level asks one clean question, which makes this the ladder to teach a policy on.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "levelW": 48, "levelH": 18, "dungeonLevels": 5,
                     "levelLadder": ["corridor", "lavacross", "monsterroom", "lockedvault", "oracle"],
                     "turnTicks": 40, "maxTurns": 55, "maxTicks": 2200, "parDepth": 3,
                     "maxActionsPerTurn": 10, "macroPrimitiveCap": 40,
                     "startHp": 12, "startNutrition": 900, "consultCost": 50,
                     "searchesToReveal": 3, "searchBurst": 8, "aggroRange": 10,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9500, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  In the `minihack` variant `cellsTotal` is `48 × 18 × 5 = 4320` and the maximum score is
  `100_000 × 4 + 85_000 = 485_000`; both are derived from `dungeonLevels`, never hard-coded.

  **Certification fixture** — `num_agents: 1` again, inside `certification.game_config`, and exactly
  one player so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS == 1`
  (the four `SEAT-COUNT` invariants `tools/ci/docker_smoke.sh` cross-checks at template lines
  141-150), with the single declared player seated:

  ```json
  "certification": {
    "players": [{"player_id": "delver"}],
    "game_config": {"players": [{"name": "Alpha"}],
                    "num_agents": 1, "minPlayers": 1, "seed": 42,
                    "levelW": 48, "levelH": 18, "dungeonLevels": 8, "levelLadder": [],
                    "turnTicks": 40, "maxTurns": 55, "maxTicks": 2200, "parDepth": 4,
                    "maxActionsPerTurn": 10, "macroPrimitiveCap": 40,
                    "startHp": 12, "startNutrition": 900, "consultCost": 50,
                    "searchesToReveal": 3, "searchBurst": 8, "aggroRange": 10,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  A `delver`-only episode is scripted throughout, so 2200 ticks is a couple of seconds of sim, but the
  replay is up to 2200 ticks ⇒ **up to 147 s of playback**, which the viewer soak needs. Seed 42 is
  asserted by `tests/test_nethack_engine.nim` to produce a fixture episode in which `delver` reaches
  at least dungeon level 2, kills at least one monster, picks up gold, eats at least once and opens
  at least one door, so the smoke replay always exercises the `descend`, `kill`, `gold`, `eat` and
  `door` paths. The certify step in `coworld-release.yml` passes **`--timeout-seconds 300`** (the
  default 60 covers start + connect grace + play + linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/nethack-player"`, following the
  starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"nethack-divemaster","run":"/bin/nethack-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"divemaster"}},
   {"name":"nethack-loremaster","run":"/bin/nethack-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"loremaster"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"nethack-delver","run":"/bin/nethack-player",
    "env":{"PLAYER_SCRIPTED":"delver","PLAYER_POLICY_LABEL":"delver"}},
   {"name":"nethack-bumbler","run":"/bin/nethack-player",
    "env":{"PLAYER_SCRIPTED":"bumbler","PLAYER_POLICY_LABEL":"bumbler"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `delver` and `bumbler`, and their
  versions must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the
  **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps
  the template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `nethack`,
  `<IMAGE>` → `coworld-nethack`, **`<SEATS>` → `1`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server)
  and `--soak 10` added to the `viewer_smoke.mjs` invocation (which already passes
  `--strict-text-bounds`). `coworld-release.yml` and `coworld-submit.yml` are the templates, with
  `--timeout-seconds 300` on the certify step. `tools/ci/docker_smoke.sh` and
  `tools/build_replay_viewer.sh` are committed **executable** (mode 100755) — CI asserts the bit and
  invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_nethack_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in
both debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_nethack_sim.nim`, `tests/test_nethack_dungeon.nim`)

1. `terrain and glyphs` — 48 × 18; the border ring is solid rock; the glyph table, passability table
   and sight table are total over the terrain enum and match §The game exactly; the item, monster and
   feature glyph sets are disjoint and closed.
2. `level generator well-formedness` — over **500 seeds × 8 depths**: 6 … 8 rooms, every room's wall
   ring intact and inside its slot, no two rooms overlapping, every corridor cell 4-connected to a
   door or another corridor cell, exactly one `<` and one `>` and never in the same room, no object on
   a staircase, no two objects on one cell, exactly one food item, monster count `min(12, 3 + depth)`
   and none in the arrival room.
3. **`level connectivity`** — over the same sweep, `<` and `>` are mutually reachable and every placed
   item is reachable from `<`, treating locked doors and secret doors as passable; and **no secret
   door is ever a cut vertex** (the generator's downgrade rule).
4. `levels are a pure function of (seed, depth)` — generating every level of a 500-seed sweep under
   three different agent behaviours yields byte-identical levels; and a revisited level is restored
   exactly as it was left (items taken stay taken, dead monsters stay dead, opened doors stay open).
5. `primitives` — each of the thirteen verbs does exactly what §The game's table says and nothing
   else: `move` into a monster attacks, into a closed door opens without moving, into a locked door
   does nothing but message, into lava kills, into rock is a spent tick; `pickup` / `eat` / `quaff` /
   `wield` / `wear` / `kick` / `chat` / `down` / `up` / `search` / `wait` each behave per the table;
   an inapplicable primitive is a no-op that still costs a tick and a nutrition point.
6. `diagonal rules` — a diagonal step is refused when it would cut a doorway or a wall corner; the
   grid bug never moves diagonally.
7. `visibility` — the lit-room / radius-1 rule cell for cell against twelve hand-built fixtures (lit
   room, dark room, corridor, doorway, corner, cog on a staircase, cog in lava-adjacent floor);
   monsters are never remembered; items are remembered and cleared when seen to be gone; a secret
   door renders as rock until found; a never-seen cell is ` ` in `map`.
8. `combat is deterministic and integer` — the to-hit and damage rules over 10 000 hash inputs; the
   same `(seed, depth, tick, salt)` always yields the same roll; a floating eye paralyses on hit
   **and** on miss; a lichen sticks; a monster never enters lava, never opens a door and never steps
   onto the cog.
9. `monster speed` — the movement-point identity `(t × speed) div 12 − ((t−1) × speed) div 12` gives
   exactly `speed` actions per 12 ticks for every species; speed 0 never acts.
10. `hunger and starvation` — nutrition falls 1/tick; the five states switch at exactly
    1000/150/50/1/0; eating restores the item's value; `Weak` costs 2 to hit and blocks kicking and
    regeneration; death at −200 is `starved`; a cog that never eats dies at tick 1100 from a fresh
    start, exactly.
11. `traps` — each of the four kinds applies its exact effect once, becomes discovered, renders `^`
    and never fires again; three adjacent `search`es reveal a hidden trap or secret door, two do not.
12. `items and identification` — potion appearances are a seeded permutation of the six colour names;
    an unidentified potion shows its appearance and an identified one its true name; the four effects
    apply exactly; `wield` / `wear` swap correctly and `ac = 9 − armourBonus`.
13. `stairs and depth` — `down` on `>` arrives on the next level's `<` and vice versa; `up` on level 1
    ends the run `escaped`; `down` on the last level ends it `bottom`; `depthReached` is monotone.
14. `oracle` — a consultation with ≥ 50 gold deducts 50, earns the deed once (never twice) and returns
    the true compass octant of `>`; below 50 gold it does nothing but message.
15. `minihack templates` — each of the five templates over 200 seeds: well-formed, `>` reachable,
    `lavacross` always has exactly one bridge cell and lava is otherwise unbroken, `lockedvault`'s
    door is always locked and always the only route, `oracle` always places `O` reachable.
16. `turn and tick order` — the numbered resolution order of §The game end to end: the queue empties
    into `wait`; paralysis and pits discard primitives without dropping the tick; a run-ending event
    breaks the tick loop; ticks after the break are never counted.
17. `scoring` — `scores[0] == 100_000×(depthReached−1) + 10×min(gold,2000) + 50×min(xp,1000) +
    5_000×deedCount` over 500 randomised end states; the dominance bound `85_000 < 100_000` holds; the
    maximum is `785_000` in `descend` and `485_000` in `minihack`; the minimum is 0; `win[0]` is
    `depthReached >= parDepth`; `winner` is `0` when `win[0]` and `null` otherwise; **death never
    subtracts**.
18. `end conditions` — `death` (all three causes), `bottom`, `escaped`, `turnCap`, a forced wall-clock
    stop and a forced fault each produce the right `endRule`, the right `reason`, the right
    `causeOfDeath`/`killer`, and a settled, rankable score; a wall-clock stop mid-run keeps the real
    depth and deeds.
19. `no floating point in the sim` — a source grep over
    `src/nethack/{sim,dungeon,mobs,items,minihack,driver,baselines}.nim` finds no `float`, `/`,
    `sqrt` or float literal.
20. `tick budget` — a full 2200-tick `descend` episode completes in < 1 s in a release build.

**Bounded orders / legality on the scripted baselines** (`tests/test_nethack_driver.nim`)

21. `baselines are bounded` — for 300 pseudo-random game states (every depth, both variants, varied
    memories, full and empty packs, adjacent to monsters, doors, lava and the Oracle) and for **both**
    `delver` and `bumbler`: the reply has at most 10 actions, every `do` is in the enum, every `dir`
    is in the enum, `travel` targets are inside 0…47 / 0…17, every `item` is a letter actually in the
    pack, `say` and `notes` are empty, and the serialised directive is ≤ 1024 bytes. A baseline that
    ever proposes an illegal or unbounded action fails the build.
22. `baselines never suicide` — over the same states, neither baseline ever emits a plan whose
    deterministic expansion steps into a **known** lava cell, and **`delver` never melees a floating
    eye and never travels through an unseen cell**.
23. `driver never produces an illegal primitive` — over the same states, every expanded queue is ≤ 40
    primitives, every entry is one of the thirteen verbs, `travel` expands to at most
    `macroPrimitiveCap`, a diagonal never cuts a corner, and an empty queue yields `wait`, never
    nothing.
24. `fallback is the delver proc` — the decision engine's fallback path and the `delver` baseline
    resolve to the same proc, so they cannot drift.
25. `reply validation` — the validator accepts the schema, **drops** (never rewrites) an invalid
    action, clamps `travel` coordinates, lower-cases `do`, case-folds `dir`, rejects a multi-rune
    `item`, accepts a `say`-only reply, rejects a non-object, truncates `say`/`notes` on **rune**
    boundaries at 140/400 with 4-byte emoji sitting exactly on the boundary, caps the read at 4096
    bytes, caps `actions` at 10, and reports `truncated` / `dropped` / `unreachable` back accurately.
26. `baseline tuning is the swept pick` — the shipped `fleeHpNumerator` / loot radius / `searchBurst`
    / tie-break rule equal `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern;
    `ci.yml` re-runs the sweep with `--check`).
27. `delver beats bumbler` — over 100 seeds of `descend`, `delver`'s total `depthReached` is strictly
    greater than `bumbler`'s, `delver` reaches DL 3 at least once, and `bumbler` reaches DL 2 at least
    once — the two controls are genuinely different controllers and neither is a zero.

**End-to-end episode writing a replay** (`tests/test_nethack_engine.nim`)

28. `episode writes artifacts` — run a real one-seat episode (`descend`, scripted, no API key so the
    LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert `results.json` and the
    `.replay` are written, `reason == "complete"`, `scores` agree with the formula, the results
    identities of §Server hold, and the results key set equals the manifest's `results_schema` key set
    **exactly**.
29. `the cert seed is interesting` — seed 42 on `descend` yields `depthReached ≥ 2`, at least one
    kill, at least one gold pickup, at least one meal and at least one door opened inside 2200 ticks,
    so the CI smoke replay always exercises those paths.
30. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure
    payload; the server refuses to start the game (loudly) when the joined seat has no register
    record.
31. `budget guard and rate guard settle early` — with each guard forced, the episode finishes
    `complete`, not `deadline`, and the matching record names the turn.
32. `permadeath settles immediately` — a forced killing blow ends the episode on that tick: no further
    ticks are simulated, `finalTick` equals the death tick, and the results carry the killer.

**Replay** (`tests/test_nethack_replay.nim`)

33. `record then re-derive, every end reason` — for `death`, `bottom`, `escaped`, `turnCap`,
    `wallClock` **and** `fault`, record an episode and re-derive it from the bytes; assert identical
    hashes at every tick **including the stop tick** (the particle-worlds scar).
34. `replay is self-sufficient` — the bytes alone yield the seat's real name, its alias, the policy
    kind, the full config (every constant in §Server's config-JSON row), the seed, the variant, every
    plan record, every chat record and the result; and re-simulating from them reproduces every level,
    every monster, every item, every message line and every status line with no fetch.
35. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports `protocol ==
    "nethack/v1"`.
36. `determinism from the replay alone` — re-simulate from the replay's seed and plan records on a
    fresh sim; identical final tick, depth, gold, experience, deeds and per-tick `gameHash`.
37. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`,
    kept.

**Manifest** (`tests/test_nethack_manifest.nim`)

38. `manifest pins` — `num_agents == 1` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens`
    in any `game_config`; `len(player) == 1` and that player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 1`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 660`;
    `attempt1Ms + retryMs ≤ turnBudgetMs` and both whole seconds; `maxTicks == maxTurns × turnTicks`;
    `levelLadder` is empty for `descend` and exactly 5 long for `minihack` with
    `len(levelLadder) == dungeonLevels`; `game.name` equals the slug and the secret URI's namespace;
    **and every variant's `game_config` actually constructs a valid `GameConfig`, generates all of its
    levels, and produces the connectivity, the ladder and the 55-turn schedule this note claims** (the
    collab-cooking 0.1.1 scar: test every variant, not just the fixture).
39. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` —
    the collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_nethack_viewer.nim`, static assertions in the `test` job)

40. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals
    `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, pinned as a literal.
41. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker (`replay_broadcast.html:4344`) and only appends after it;
    `broadcast_core.js`'s kept procs are byte-identical to the starter's, `pushFeed`'s signature and
    `attachMinimap` included.
42. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (`replay_broadcast.html:1635`, the tandem hoisting trap); the beat
    builder is `nhBeat`, never `markBeat`.
43. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{descend, ascend, levelup, deed, oracle, death, bottom, escaped, fallback, end}`.
44. `transport, endcard, viewpanel and 360 px rules` — `#endcard { bottom: var(--band` present;
    `relayout()` sets `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is
    positioned inside the band; the five `.tiny` rules exist; the removed ids (`#povBadge`,
    `#fpv-hp`, `#fpv-gear`, `#fpv-map*`) appear nowhere, while the kept `#viewpanel`, `#minimap`,
    `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`, `#zoom-slider`, `#zoom-read`, `#fpv`,
    `#fpv-canvas`, `#fpv-name`, `#fpv-cap` and `#fpv-grip` are all present and the page still calls
    `core.attachMinimap`.
45. `endcard labels` — `tests/test_nethack_endcard_labels.nim`: zero matches for the forbidden
    paintbot vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
46. `label manifest` — the starter's `test_label_contract` pattern: the emitted board-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
47. `events are the closed enum` — `tests/test_nethack_events.nim`: the set of kinds `stepEvents` can
    emit equals exactly the twenty-two listed in §Server, and every kind used by the appended game
    block is in that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**

48. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced** (downloaded
    as the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both the npm
    module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the
    bridge `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — `--strict-text-bounds` stays **on** even though this game draws
    a terminal panel, because the panel measures its box and drops rows that do not fit (§Viewer →
    Legible at 360 px).
49. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, the CI replay's seat plays scripted and emits **no `say` at all**, so the
    smoke replay can never exercise the feed's narration path (the cogchemists 2026-08-24 scar). The
    fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only
    the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) —
    driving the real page with a full-cap 140-rune `say`, a fully dark level, a lit-room reveal, an
    oracle banner, all eight depth-ladder rung states, a floating-eye paralysis, and the **tombstone**
    endcard for each of `death` / `bottom` / `escaped` / `turnCap`, at several canvas widths including
    360 px.
50. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.

---

## Out of scope (v1)

- **Any NLE, NetHack-source or MiniHack dependency, and bit-exactness with any of them.** Decided as
  a scoping rail before design and recorded in `docs/PORTING-NETHACK.md`: no upstream code is
  vendored, no upstream numbers are claimed as reproduced, and **no score from this coworld is
  comparable to a published NLE, NetHack Challenge or BALROG number**. This coworld implements the
  problem, not the package. A future version may add a *reporting* mapping (depth, gold, experience)
  so runs can be read alongside NLE reports; it will never claim parity.
- **A real ttyrec.** The viewer's terminal panel renders *this* sim's glyph map, message line and
  status line; it does not emit or play a NetHack ttyrec, because there is no NetHack process to
  record. The panel is the honest equivalent and is labelled as such in `docs/RULES.md`.
- **The rest of NetHack.** The Gnomish Mines, Sokoban, the Oracle's minor consultations, Mine Town,
  the Big Room, the quest, the Castle, Gehennom, the Amulet, ascension, branches, trapdoors, level
  teleporters, shops, temples, altars, fountains, thrones, graves, vaults with guards, scrolls, wands,
  rings, amulets, spellbooks, tools, gems, artifacts, containers, blessed/cursed status,
  enchantment, encumbrance, erosion, corpses and corpse-eating, petrification, polymorph, pets,
  roles, races, alignment, gods, prayer, luck, attributes, Elbereth, and the several hundred monster
  species this note does not ship. Eleven species, five item classes, four potion effects, four trap
  kinds and eight levels are the smallest world that still poses NetHack's actual problem.
- **Seat counts other than 1, and map sizes other than 48 × 18.** `num_agents` is fixed at 1 in every
  variant and in the cert fixture; a multi-agent roguelike is a different coworld. A second map size
  would fork the viewer's camera arithmetic and the generator's slot bounds for no gain the idea asks
  for.
- **Per-keystroke LLM stepping, and an RL-vector observation.** The seat batches up to ten commands a
  turn under a deterministic driver (§Decisions, divergence 9). A per-tick socket interface for an RL
  policy, and a numeric glyph/stat tensor to go with it, are what `COGAME_EVENTS_URI`'s `Primitive`
  rows exist to make possible **later**; they are not a v1 interface.
- **Scoring exploration, kill counts, survival time or turn efficiency directly.** `cellsSeen`,
  `monstersKilled`, `itemsPicked`, `doorsKicked`, `trapsTriggered`, `potionsQuaffed` and
  `primitivesExecuted` are measured, recorded in `results`, shown on the endcard and drawn in the
  feed, and deliberately **not** in `scores` (§The game). Paying for cells seen would let a policy
  farm the metric by pacing a lit room; paying for survival would reward sitting on the up-staircase.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the
  hosted spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, vision cones, raycast fog, the
  first-person renderer, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches,
  perks, handicaps, lives, teams, four-team play, shouts, achievements, campaign mode, multi-game
  episodes, the pixel map generator, the map pool, the map editor and mapkit — all deleted, not
  disabled (§Sim module), and none of them return in v1.
