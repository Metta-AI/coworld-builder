# cogame-halite — design note (2026-08-27, moba lineage / bit-exact Kaggle port)

*Destination path in the new repo: `docs/plans/2026-08-27-halite-design.md`. This file is the
run-directory copy (`runs/2026-08-27-halite/design.md`); phase 20 commits the identical bytes at the
destination path above.*

`Metta-AI/cogame-halite` is a **four-seat, free-for-all economy race with physical risk on every
move**: a bit-exact port of **Kaggle's Halite IV** (`kaggle-environments`, Two Sigma seasons I–IV;
the shipped env is season IV) onto the Coworld platform. Four fleets mine a 21 × 21 torus of halite,
haul it home to their shipyards, and ram each other — the ship carrying *less* survives the collision
and takes the other's cargo. Most banked halite at turn 400 wins.

It is forked from **`Metta-AI/cogame-moba`**, read at its read-only mount
`/workspace/starters/cogame-moba` (including `docs/PORTING.md`, `docs/PROTOCOL.md`,
`server/cogame_moba/*.py`, `players/*.py`, `tests/*.py`, `coworld_manifest_template.json`,
`tools/ci/docker_smoke.sh`, `Dockerfile`, `compose.yaml`, `AGENTS.md`). **Every convention there holds
here unless this note says otherwise.** That means: Python + `uv` + `pytest`; the
`server/cogame_<slug>/{config,defaults,engine,replay,server,sim,uris}.py` module split; the lockstep
episode engine with a per-turn deadline, a degrade-to-fallback rule and a dead-seat strike rule; the
`COGAME_CONFIG_URI` / `COGAME_RESULTS_URI` / `COGAME_SAVE_REPLAY_URI` / `COGAME_PLAYER_FAILURE_URI` /
`COGAME_LOAD_REPLAY_URI` / `HOST` / `PORT` runtime contract with `/player?slot=&token=`,
`/client/player`, `/client/global`, `/global` and `/healthz`; the **closed** results schema mirrored
between `server.py` and the manifest and `tools/ci/docker_smoke.sh`; the closed player-failure
payload `{"message", "failed_policy_index"}`; players as extra entrypoints of the **one** image; the
`vendor/` discipline of `AGENTS.md` (`vendor/upstream/` is byte-pristine, `vendor/UPSTREAM.md`
records commit + per-file sha256, every deviation documented in `vendor/PATCHES.md`); and
`docs/PORTING.md`'s two inviolable rules — **never fix an upstream quirk, and the fidelity gate is
the acceptance criterion for the whole port**.

**Starter choice, in one line:** cogame-moba is the starter table's row for a **bit-exact port of an
existing external environment** — Halite IV's rules already exist as running code
(`kaggle_environments/envs/halite/helpers.py`), so the job is to reproduce that code's behaviour and
prove it, which is exactly the discipline (vendor pristine → assemble → differential fidelity gate →
permanent CI gate) that cogame-moba exists to demonstrate.

**One departure, named up front: the viewer.** cogame-moba's viewer is the vendored C renderer
compiled with emscripten; Halite's upstream renderer is a Kaggle HTML/JS bundle we are pinned *not*
to embed, and there is no C renderer to compile. **All four viewer files come from one starter,
`Metta-AI/coworld-ctf`** — see `## Viewer`, which names them. The precedent for exactly this
combination (Python game server from the moba/factorio side + coworld-ctf's Nim → emscripten static
replay viewer, rendering **recorded per-turn state** rather than re-simulating) is
`Metta-AI/cogame-factorio`, whose `client/static_replay.js` header records the three adaptations it
made to ctf's files. We make the same three and take the files themselves from coworld-ctf, so the
emscripten link flags and the JS bootstrap can never disagree (the cogame-lantern 2026-08-23 scar).

**Source idea, verbatim:**

> KAG Halite — four fleets mine halite, collide to steal cargo, and every ship is a tiny decision
>
> Port of Kaggle's Halite (Two Sigma, seasons I-IV). 21×21 torus of halite cells; four players; ships mine by sitting still (25% of the cell per turn), carry halite back to shipyards to bank it; ships collide — the one carrying less survives and takes the other's cargo; convert ships into shipyards; 400 turns; most banked halite wins. Simultaneous per-turn orders for every ship and shipyard. The Kaggle leaderboard left hundreds of open bots.
>
> Seats: 4
> Motive: mixed — four-way zero-sum with local truces
> Policy interface: per-turn orders bundle; LLM + scripted ship micro is the Kaggle-proven pattern
> Fills gap: 4-player economy race with a *cargo-theft* collision rule — closest existing is Lux (2p) and 08 Gridlock; this is the free-for-all with physical risk on every move
> Integrity (anti-collusion): 4-seat FFA — seat randomisation, anonymous aliases, alliance-pattern audit.
>
> Replay plan (watchability): Kaggle's HTML replay renderer is open — embed; add a cargo-at-risk heatmap.
>
> Source: github.com/Kaggle/kaggle-environments (halite).

**One ruling this note makes against the idea text, and the reason.** The idea says "Kaggle's HTML
replay renderer is open — embed". **Overridden.** SPEC's viewer pin is a static wasm bundle this repo
owns, with the starter's chrome; an iframe to a third-party renderer is neither. The cargo-at-risk
overlay the idea asks for **is** built, in v1, from the recorded state (§Viewer). The Kaggle renderer
embed is in `## Out of scope (v1)`.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")

| Pin | How cogame-halite satisfies it |
|---|---|
| Starter by game shape | **`cogame-moba`** — bit-exact port of an existing external env; its vendor/patch/fidelity-gate discipline is the whole point of this coworld. Viewer files: **`coworld-ctf`**, all four, named in §Viewer. |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-halite`, **public at creation** (`source-resolves` 404s on private). §Packaging. |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `PLAYER_PROMPT=<strategy>` (both champions) vs `PLAYER_SCRIPTED=tidewalker` / `PLAYER_SCRIPTED=corsair` (both fillers). One image `coworld-halite`, one player entrypoint `python -m players.halite_player`. §Decisions, §Packaging. |
| Static wasm replay viewer, never a pod | `game.replay_viewer.bundle = "static-replay-viewer"`, built by `tools/build_replay_viewer.sh` from the Dockerfile's `wasm-builder` stage. The bundle reads the `.replay` JSON from S3 and nothing else. §Viewer. |
| Real art, starter chrome verbatim | ctf's `client/chrome_common.js` **byte-for-byte**; `client/replay_broadcast.html` = ctf's page **with one appended game block**; four hull kits + four shipyard kits + a six-step halite crystal sheet rendered with `playbooks/art-nanobanana.md`, committed as PNGs. §Viewer §Art. |
| Two name spaces | In-game: `FLEET-ALPHA/BRAVO/CHARLIE/DELTA` only. Real policy names live only in `results.names`, the replay header's `names`, the scorebug plates and the endcard. Test-enforced both ways. §Server, §Viewer, §Tests. |
| Degrade-never-hang inside 60 % of `episodeTimeoutSeconds` (1200 s) | Typical 195 s, worst modelled 537 s, budget guard at 600 s, hard stop at 660 s = **55 %**. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4**, inside `game_config` of variants `standard`, `sprint` and `richfields` **and** inside `certification.game_config`; never at a variant's top level; `<SEATS>` = **4** in `tools/ci/docker_smoke.sh`. §Packaging. |

**There is no `OPEN` section.** Halite IV's rules are fully determined by the upstream code quoted
below; everything the idea leaves loose (seat count, episode length against an LLM budget, how a
four-way FFA is ranked, viewer composition, baseline algorithms) is a rail decided here with its
reason.

---

## The game

**Four fleets, one salt flat, four hundred turns.** Every fleet starts with one ship and 5 000
banked halite in its own quadrant of a 21 × 21 wrap-around board holding about 24 000 halite in
uneven clusters. A ship that holds still scrapes **25 %** of the halite under it into its hold. A ship
that moves carries its hold with it — and a hold is a target: when two ships end a turn on the same
cell, the one carrying **less** survives and **takes the other's cargo**, and if they carry exactly
the same, both are destroyed. Cargo only becomes score when a ship ends its move on one of its own
shipyards. You get shipyards by burning a ship and 500 halite (`CONVERT`); you get ships by burning
500 banked halite at a shipyard (`SPAWN`). An enemy ship that walks onto your shipyard destroys the
shipyard and itself. Everyone moves at once, every turn, with no information hidden.

The tension the game is built on: halite in a hold is worth nothing and is *stealable*; halite in the
bank is worth everything and can never be lost. Mining longer earns more but makes you heavier, and
heavy loses every collision. That is why the idea calls it "physical risk on every move".

### The reference implementation this port reproduces

| What | Where |
|---|---|
| Repository | `github.com/Kaggle/kaggle-environments`, Apache-2.0 |
| Spec + config defaults | `kaggle_environments/envs/halite/halite.json` (`"name": "halite"`, `"title": "Halite 4"`, spec `"version": "1.2.1"`, `"agents": [1, 2, 4]`) |
| Board generation, elimination, rewards, ASCII renderer | `kaggle_environments/envs/halite/halite.py` (`populate_board`, `interpreter`, `renderer`) |
| **Turn resolution** | `kaggle_environments/envs/halite/helpers.py` → `Board.next()` |
| Geometry, `Point`, `group_by` | `kaggle_environments/helpers.py` |
| Pinned release | PyPI `kaggle-environments==1.32.7`, and the git commit that release was cut from — phase 20 records the commit hash and the sha256 of each vendored file in `vendor/UPSTREAM.md` and pins `kaggle-environments==1.32.7` in the CI-only `fidelity` dependency group. |

**Rule constants (all upstream defaults, all served unchanged):**

| Constant | Value | Upstream key |
|---|---|---|
| Board edge | **21** (441 cells, wraps in both axes) | `size` |
| Turns in an episode | **400** | `episodeSteps` |
| Board halite at turn 0 | **24 000** (normalisation target) | `startingHalite` |
| Bank per fleet at turn 0 | **5 000** | `reward.default`, written by `populate_board` as `state[0].reward` |
| Mine rate | **0.25** of the cell, `int()`-truncated | `collectRate` |
| Regeneration rate | **0.02** per turn, on cells with no ship | `regenRate` |
| Cell cap | **500** | `maxCellHalite` |
| Ship cost | **500** | `spawnCost` |
| Convert cost | **500** | `convertCost` |
| Move cost | **0.0** (a move costs no cargo) | `moveCost` |
| Actions | `NORTH`, `SOUTH`, `EAST`, `WEST`, `CONVERT` (ships), `SPAWN` (shipyards), plus *no action* = mine | `action.enum` |

Anything not in that table is not a knob: `size`, `spawnCost`, `convertCost`, `moveCost`,
`collectRate`, `regenRate` and `maxCellHalite` are pinned to the upstream defaults in
`config_schema` so a variant cannot drift them (only `episodeSteps` and `startingHalite` vary, and
both are first-class upstream config fields — the rules stay bit-exact in every variant).

### Seats, aliases, quadrants

- **`num_agents` = 4.** Exactly four seats, in every variant and in the certification fixture. One
  seat commands one whole fleet: every ship and every shipyard it owns. Four is the idea's seat count
  and the only free-for-all agent count upstream supports well (`"agents": [1, 2, 4]`).
- **Two name spaces.** In-game, seats are **`FLEET-ALPHA`** (seat 0), **`FLEET-BRAVO`** (1),
  **`FLEET-CHARLIE`** (2), **`FLEET-DELTA`** (3). Observations, prompts, the ASCII board legend, the
  event feed's in-board lines and every `note` carry only those strings. The seats' **real policy and
  player names** (`daveey`, `daveey-1`, `halite-tidewalker`, `halite-corsair`) appear only in
  `results.names`, in the replay header's `names`, in the viewer's scorebug plates and on the
  endcard. A seat can never learn who it is playing (`tests/test_privacy.py`).
- Colours are fixed by seat: 0 amber, 1 teal, 2 magenta, 3 lime — four hues that stay distinct on the
  dark seabed at 360 px.
- **Quadrants and integrity.** `populate_board` mirrors one 11 × 11 quartile into all four quadrants,
  so the board is **exactly 4-fold symmetric** and the four starting cells are equivalent by
  construction: seat 0 at index **110** = `(x 5, y 15)`, seat 1 at **120** = `(15, 15)`, seat 2 at
  **320** = `(5, 5)`, seat 3 at **330** = `(15, 5)`. No seat can be dealt a better island, so no seat
  randomisation is needed (and none is applied — permuting seats would be a deviation from upstream
  for no gain). Anti-collusion rests on the anonymous aliases plus the fact that **every order of
  every seat is in the replay**, so an alliance-pattern audit needs no extra instrumentation (the
  audit *tool* is out of scope for v1; the data is not).

### Geometry, exactly

Upstream `Point` semantics are load-bearing and the viewer must agree with them:

- A cell is `Point(x, y)` with `x` rightwards and **`y` upwards**; `index = (size - y - 1) * size + x`
  and `Point.from_index(i) = (i % size, size - 1 - i // size)` (`kaggle_environments/helpers.py`).
- Therefore **index 0 is the top-left cell on screen** and index 440 the bottom-right; the viewer
  draws the `halite` array in raster order and gets upstream's own orientation for free.
- `NORTH = (0, +1)` = `index - size` = **up on screen**; `SOUTH` down; `EAST` `+1`; `WEST` `-1`; all
  four wrap (`halite.py::get_to_pos`, `Point.translate`).
- Distances in this note are **torus Manhattan** (`Point.distance_to`).
- Asset ids are strings minted `f"{turn}-{n}"`, `n` counting from 1 across **all** players within one
  resolution (`Board.next().create_uid`); the four opening ships are `0-1`, `0-2`, `0-3`, `0-4`.

### The clock

- **One tick = one Halite turn.** Turns are numbered **0 … 399**. Turn 0 is the generated board;
  `Board.next()` is applied **399 times**, producing the states at turns 1 … 399. That is upstream's
  `episodeSteps = 400` exactly (`kaggle_environments/core.py` keeps `episodeSteps` entries in
  `steps`, index 0 being the populated board), and the fidelity gate pins the off-by-one.
- **Every turn takes orders from every seat.** This is a simultaneous-decision game: all four seats
  are asked at once, always (§Decisions).
- **Directive turns** are turns where `turn mod directiveEvery == 0`, `directiveEvery` = **20** in
  `standard` and `richfields`, **10** in `sprint`: turns 0, 20, 40, …, 380 — **20 LLM batches per
  episode**. On every other turn a seat answers from its own compiled plan in milliseconds. The
  cadence is 20 because that is what fits the wall-clock budget with room to spare (§Decisions), and
  because a Halite directive — where to mine, when to come home, how many ships, whom to hunt — is a
  20-turn decision, not a 1-turn one; per-ship micro is the part the Kaggle leaderboard automated.
- **The turn count is NOT reduced for v1.** 400 turns, bit-exact, in the default variant. The
  `sprint` variant (200 turns) exists for ladder throughput, not because the budget needs it.
- One game per episode. The board is 4-fold symmetric, so there are no sides to swap.

### Turn resolution — the exact order

Everything below is one call of `sim.step(orders)` and is a transcription of `Board.next()`
(`kaggle_environments/envs/halite/helpers.py`) followed by the elimination block of
`interpreter()` (`halite.py`). **In the built repo this is not a re-implementation: the vendored
`Board` class is imported and called** (§Sim module), so "bit-exact" is a property of the code, not
of a careful reading. The order is written out here so a reader knows what the game *is*, and so
`tests/test_sim.py` has a numbered list to assert against.

Let `orders[p]` be seat `p`'s accepted action map (`{asset_id: ACTION}`) for this turn (§Server).

1. **Bind actions.** For each seat `p` in ascending seat order, each of its ships and shipyards takes
   at most one action from `orders[p]`. A value not in the enum, or an id the seat does not own, is
   simply **not bound** — upstream's `ShipAction[raw] if raw in ShipAction.__members__ else None`.
   `SPAWN` on a ship and a direction on a shipyard are likewise not bound.
2. **Per-seat action processing, seats in ascending seat order.** Within a seat:
   - **a. `SPAWN`**, shipyards in the seat's shipyard-insertion order. If `bank >= 500`: `bank -= 500`
     and a new ship with **0 cargo** appears on that shipyard's cell with a fresh uid. A seat that
     orders more spawns than it can pay for gets the ones its bank covers, **in that order** — which
     is why the observation's asset ordering is part of the contract (§Server).
   - **b. `CONVERT`**, ships in the seat's ship-insertion order. Allowed only if the ship's cell holds
     **no shipyard** (of anyone) and `ship.cargo + bank >= 500`. Then `delta = ship.cargo - 500`;
     `bank += min(delta, 0)` immediately; `max(delta, 0)` is **held aside** in
     `leftover_convert_halite` and added only after all of this seat's converts (upstream's explicit
     guard against chaining one convert's change into another); a shipyard with a fresh uid appears
     on that cell, **the cell's halite is set to 0** (`Board._add_shipyard`), and the ship is deleted.
   - **c. Moves.** A ship with `NORTH`/`SOUTH`/`EAST`/`WEST` moves one cell with wrap. `moveCost` is
     0, so cargo is unchanged. Two ships may land on the same cell — that is the point.
   - **d.** `bank += leftover_convert_halite`, then `assert bank >= 0` (a trip is a sim fault, §Sim
     module).
3. **Ship-to-ship collisions**, over every cell that ends step 2 holding more than one ship. The ship
   with the **strictly smallest cargo survives** and **absorbs the cargo of every ship destroyed on
   that cell**. If two or more ships tie for smallest cargo, **all ships on that cell are destroyed**
   and their cargo is gone from the world. Ownership is irrelevant: friendly ships collide with each
   other on exactly the same rule.
4. **Ship-to-shipyard collisions.** For every shipyard, if a ship of a **different** seat is standing
   on it after step 3, **both the shipyard and that ship are destroyed**.
5. **Deposit.** For every surviving shipyard, if the ship standing on it belongs to the **same** seat,
   that seat's `bank += ship.cargo` and the ship's cargo becomes 0. This is the only way halite is
   ever banked.
6. **Mining.** For every surviving ship: `delta = int(cell.halite * 0.25)`. The ship mines iff its
   bound action was **not** one of the four moves, the cell holds **no shipyard**, and `delta > 0`.
   Then `ship.cargo += delta` and `cell.halite -= delta`. (A ship spawned this turn is standing on a
   shipyard, so it never mines on its birth turn; a ship that converted no longer exists.) Cargo is
   uncapped — a hold can carry thousands, which is exactly what makes it worth ramming.
7. **Regeneration.** For every cell **with no ship on it**:
   `halite = min(round(halite * 1.02, 3), 500)`. Cells under a ship do **not** regenerate. The
   `round(x, 3)` is Python's round-half-to-even at three decimals and is part of the contract — cell
   halite is a float, and the port keeps it a float (`assert halite >= 0`).
8. **Turn counter.** `turn += 1`.
9. **Elimination** (`interpreter`). A seat still active whose ships are all gone **and** which either
   has no shipyard or has `bank < 500` is marked **eliminated at this turn**: it can never act again,
   its remaining assets are cleared, and its final score is frozen at
   `turn - 400 - 1` (upstream's rule — a negative number; being eliminated later is worth more).
10. **Last-fleet check.** If fewer than two seats are still active, every remaining active seat is
    marked done and the episode ends at this turn (`endRule = "last_fleet"`).
11. **Record.** The engine appends the turn's state, accepted orders, derived events and state hash
    to the replay (§Server), then evaluates the end conditions.

Notes a builder will otherwise get wrong, each an upstream fact:

- Spawn is processed **before** convert within a seat, and a seat's whole block is processed before
  the next seat's — but no seat can see another's actions, so the ordering only decides how a *single*
  seat's bank is spent, never a cross-seat outcome.
- Collisions are resolved **after all movement**, so head-on swaps (A→B, B→A) do **not** collide in
  Halite IV; both ships pass through each other. Do not add a swap rule.
- Deposit happens **after** collisions: a loaded ship that is rammed on the doorstep of its own
  shipyard loses everything.
- A cell that becomes a shipyard loses its halite permanently.
- A ship standing still on a cell suppresses that cell's regeneration *and* mines it: the "sitting on
  a rich cell" strategy drains it faster than the 2 % can heal it.

### Scoring formula and sign

Measured when the episode ends (turn 399, last-fleet, or a wall-clock stop):

```
banked[s]      = seat s's bank
eliminated[s]  = the turn s was eliminated, or null

score[s]       = banked[s]                       if eliminated[s] is null
               = eliminated[s] - 400 - 1         otherwise      (negative, upstream's own rule)
```

**Sign: higher is better.** A surviving fleet always outranks an eliminated one (banks are ≥ 0,
elimination scores are ≤ −2), and among eliminated fleets, surviving longer ranks higher — exactly
Kaggle's leaderboard rule (`halite.json`: *"the amount of player owned halite … if the player has not
been eliminated, else step_eliminated − episode_steps − 1"*). It is not zero-sum (halite enters the
world by regeneration and leaves it in tied collisions), which is correct for a four-way FFA and is
what the idea calls "mixed — four-way zero-sum with local truces".

**The league ranks by `results.scores`**, higher first; the platform's Elo (1000 start, K 32) eats the
resulting four-way ordering. `results.placement[s]` ∈ {1,2,3,4} is that ordering, computed with this
tie-break ladder, first difference deciding:

```
1. score[s]              descending
2. shipyards[s] + ships[s] at the end       descending
3. mined[s]   (lifetime halite scraped)     descending
4. seat index                               ascending   (total order, always terminates)
```

Seats that are still exactly equal after rule 3 share the higher placement in `placement` (1,1,3,4)
but rule 4 still gives `results.ranking` a strict order for the ladder. `results.win[s]` is
`placement[s] == 1`; `results.winner` is the single seat with `placement == 1`, or `null` when two or
more share it.

A `deadline` episode is scored by the **same formula at the turn the clock stopped** — never zeroed,
always rankable.

### End conditions and legal `results.reason` values

The episode ends at the first of:

| `end_rule` | When |
|---|---|
| `full_time` | The state at turn **399** has been recorded. The normal path. |
| `last_fleet` | Fewer than two seats remain active after step 10 of some turn. |
| `wall_clock` | The engine's `wall_clock_budget_seconds` (**660 s**) is reached at a turn boundary. |
| `fault` | An unhandled exception in the sim or the loop (including an upstream `assert`). |

`results.reason` is a **closed enum of exactly three values**:

- **`complete`** — `end_rule` was `full_time` or `last_fleet`. The healthy value; `docker_smoke.sh`
  requires it.
- **`deadline`** — `end_rule` was `wall_clock`. The episode is settled at the stop turn by the same
  scoring ladder, results and replay are written, and the replay's `stop` record names the turn.
  **Declared acceptable** for SPEC §Definition of done check 4. The budget guard (§Decisions) means it
  should never fire; the worst modelled episode finishes 123 s early.
- **`fault`** — `end_rule` was `fault`. Settled from the last completed turn, `results.stop_detail`
  carries the exception text (≤ 200 **runes**, rune-truncated), artifacts still written. A defect:
  `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

A seat that never connects, disconnects, or fails every reply **does not end the episode**: its fleet
plays the server-side `tidewalker` fallback and the game runs to its natural end. Nothing a player
container does can stop the clock — the lobby is bounded by `player_connect_timeout_seconds` (120 s)
and the strike rule stops a silent seat from consuming the per-turn deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {tidewalker, corsair}` makes it a scripted seat. A seat that sets neither, or sets an
unrecognised name, plays **`tidewalker`** (the published default). A scripted policy seated as a
champion is a failure state (SPEC §Definition of done).

### Where the decision happens

**In the player container**, which is the moba/factorio lineage's shape and the platform's default:
the player pod gets the Bedrock sidecar, the game pod needs no LLM credential. The consequence, which
must be in `tools/ci/policies.json` from day one, is the **cogolf 2026-08-24 gotcha**: every LLM
policy's `env` carries **`USE_BEDROCK: "true"`** as well as `PLAYER_PROMPT`, or the platform never
attaches the sidecar and the seat silently plays scripted. Model
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, `max_tokens` **900** (400 truncates —
`cut off at max_tokens`), no `output_config.effort` (Haiku 4.5 rejects it).

The audit trail that makes a silent-scripted seat impossible to miss:

- Every orders message carries `source ∈ {"llm", "retry", "scripted", "fallback"}`.
- `results.llm_turns[s]` counts turns where seat `s` answered with `source` `llm` or `retry`; a
  healthy `standard` episode is `[20, 20, 0, 0]` for two champions and two fillers.
- `results.fallbacks[s]` counts server-side substitutions, by cause.
- The server **logs loudly and reports a player failure** when a seat completes the lobby without a
  `register` message (the grf-football 2026-08-27 scar: a lost register packet made a champion play
  the default script for a whole episode with `latency_ms: 0` and no error anywhere).

### One parallel batch per turn

This is a **simultaneous-decision game**, so the engine asks **all four seats at once**: one
`observe` frame is written to all four websockets before any reply is awaited, and the engine then
waits on the four replies together under **one shared deadline** (`asyncio.wait` with a single
timeout, never a per-seat loop). Sequential querying is the documented way to blow the 720 s budget.

### The wall-clock budget, out loud

`episodeTimeoutSeconds` is **1200 s** (the game container never receives it; we assume it). The pin is
to play inside **60 % = 720 s**.

| Phase | Count | Per unit | Total |
|---|---|---|---|
| Lobby (four containers connect) | 1 | ≤ 20 s | 20 s |
| Micro turns (`turn mod 20 != 0`) | 380 | ~25 ms typical / 400 ms deadline | **9.5 s** typical, 152 s worst |
| Directive turns (`turn mod 20 == 0`) | 20 | spacing floor 10 s, deadline 18 s | **200 s** typical, 360 s worst |
| Sim | 400 | ~2 ms | 0.8 s |
| Results + replay write | 1 | ≤ 5 s | 5 s |
| **Typical total** | | | **≈ 235 s (20 % of 1200)** |
| **Worst modelled total** | | | **≈ 537 s (45 % of 1200)** |

- `turn_deadline_ms` = **400** on micro turns. A local websocket round trip plus a Python micro
  compile is ~5 ms; 400 ms is an 80× margin, and it caps the worst case at 152 s.
- `directive_deadline_ms` = **18 000** on directive turns. The player itself spends at most 12 s on
  attempt 1 and 5 s on the retry, so 18 s covers both plus transport. Attempt 1 is 12 s, not 5 s, on
  purpose: the pommerman 0.1.1 finding is that a deadline below the hosted **batch** p90 manufactures
  fallbacks that are not real.
- `directive_spacing_ms` = **10 000**: the engine will not open a new directive batch until 10 s after
  the previous one opened. Four calls per batch at ≥ 10 s spacing is **24 requests/minute**, under the
  sidecar's **30 req/min per episode** cap (the raid 2026-08-23 scar). This floor, not the LLM, is
  what sets the typical episode length.
- **Budget guard.** At the top of every turn, if `elapsed > 600 s` the engine stops asking players
  anything: every seat plays the server-side `tidewalker` compile (~0.2 ms/turn), the remaining turns
  run at full speed (400 turns × 2 ms ≈ 0.8 s), and the episode still ends **`complete`**. A
  `budget_guard` event records the turn it fired.
- **Hard stop.** `wall_clock_budget_seconds` = **660 s**. Reaching it at a turn boundary ends the
  episode with `reason = "deadline"`, settled by the scoring ladder — **55 %** of 1200 s, inside the
  pin even in the pathological case.

### Degrade, never hang — the fallback ladder

Per seat, per turn, in order; every step is bounded:

1. **Attempt 1.** The player answers. On a directive turn it calls the LLM with a 12 s client-side
   timeout; on a micro turn it answers from its compiled plan.
2. **Retry once (player-side).** If the LLM call errored, timed out, or the reply did not parse into
   the directive schema after repair, the player retries **once** with a 5 s timeout and a shortened
   prompt, and logs `will retry` (never `falling back` — the phase-60 grep distinguishes them).
3. **Player-side scripted fallback.** If the retry also fails, the player keeps its previous directive
   (or the `tidewalker` defaults on turn 0), compiles orders from it, and answers **within the
   deadline** with `source: "scripted"` and a `note` naming the cause (≤ 140 runes). A seat whose LLM
   is entirely unavailable therefore plays a competent scripted game for the whole episode and never
   costs a single deadline.
4. **Server-side scripted fallback.** If the *wire* reply is late, malformed, addressed to the wrong
   turn, or the socket is gone, the engine substitutes the orders that **`tidewalker` compiles from
   the same state, in-process** (`server/cogame_halite/micro.py`, the same module the scripted player
   imports), records a `fallback` event with the cause, and steps the sim. **The sim never waits.**
5. **Strike rule.** Ten consecutive substitutions mark the seat **dead**: it is no longer awaited (so
   it cannot consume the deadline), it keeps playing `tidewalker`, and a valid reply revives it. Dead
   seats are reported once to `COGAME_PLAYER_FAILURE_URI` with the closed payload
   `{"message", "failed_policy_index"}` and land in `results.dead_seats`.

`results.fallbacks[s]` is an object with the exact keys
`{timeout, malformed, wrong_turn, disconnected, host_error}`, partitioning the substitutions.

### The observation → prompt → orders path (LLM seats)

On a directive turn the player builds the prompt from the observation (§Server) and asks for a
**directive**, not per-ship orders — one 20-turn plan the local micro layer then executes every turn.
This is the idea's own "LLM + scripted ship micro is the Kaggle-proven pattern", and it is what makes
80 LLM calls cover 1 600 asset-turns.

**System prompt (verbatim):**

```
You command a fleet in Halite IV: four fleets mine a 21x21 wrap-around board and steal each
other's cargo. You are given the whole board; nothing is hidden. Reply with ONE JSON object and
nothing else. Your reply MUST begin with the character { and end with }. No prose, no markdown,
no code fences, no explanation outside the JSON.
```

**User prompt (template; `{…}` are substitutions):**

```
TURN {turn}/{maxTurns} - DIRECTIVE TURN (this plan stands for the next {directiveEvery} turns)
YOU ARE {alias}   BANK {bank}   SHIPS {ships}   YARDS {yards}   CARGO AFLOAT {cargoAfloat}
STANDINGS (banked)  {alias0} {bank0} | {alias1} {bank1} | {alias2} {bank2} | {alias3} {bank3}
BOARD  lower-case = ship, UPPER-CASE = shipyard, digit = that cell's halite on a 0-9 scale of 500
{asciiBoard}
LEGEND  a/A={alias0}  b/B={alias1}  c/C={alias2}  d/D={alias3}
YOUR SHIPS  {id}@({x},{y}) cargo {cargo}; ...          (up to 24, then "+N more")
YOUR YARDS  {id}@({x},{y}); ...
THREATS  {n} enemy ships within 2 cells of one of your loaded ships; lightest nearby enemy cargo {c}
RULES THAT DECIDE THIS GAME
- Holding still mines 25% of the cell (rounded down). Moving is free. Cells under a ship do not regrow.
- Two ships on one cell: the LIGHTER one survives and takes the other's cargo. Equal cargo kills both.
- An enemy ship entering your shipyard destroys the shipyard and itself.
- SPAWN costs 500 from the bank. CONVERT costs 500 and turns that ship into a shipyard.
- Cargo scores only when a ship ends its move on YOUR shipyard. Most banked halite at turn {maxTurns} wins.
LAST DIRECTIVE  {lastDirectiveJsonOrNone}
YOUR STANDING ORDERS  {strategy}
Reply exactly this JSON shape:
{"stance":"expand|mine|raid|defend","spawnUntil":<int 0-400>,"yards":<int 1-4>,
 "mineFloor":<int 0-500>,"returnAt":<int 50-1500>,"focus":"NW|NE|SW|SE|CENTER",
 "avoid":"<one alias or null>","note":"<<=140 chars, spectator-facing, what you are doing>"}
```

`{strategy}` is the `PLAYER_PROMPT` env text inserted verbatim, rune-truncated to **2 000 runes**.

**Directive repair (never reject, always clamp).** Extract the first balanced `{…}` from the reply
(trailing prose tolerated); lower-case enum values; clamp `spawnUntil` to `[0, maxTurns]`, `yards` to
`[1, 4]`, `mineFloor` to `[0, 500]`, `returnAt` to `[50, 1500]`; an unknown `stance`/`focus` keeps the
previous value; `avoid` must equal one of the three opponent aliases or becomes `null`; unknown fields
are dropped; missing fields inherit the previous directive (defaults on turn 0:
`{stance: "mine", spawnUntil: 300, yards: 2, mineFloor: 100, returnAt: 500, focus: "CENTER", avoid: null}`).
`note` is truncated on a **rune** boundary to 140 runes. Only if the extraction itself fails does the
retry ladder advance.

### The micro layer — `tidewalker`

`tidewalker` is the scripted baseline **and** the executor of every LLM directive: it is one pure
function `compile_turn(state, seat, directive) -> {asset_id: ACTION}` in
`server/cogame_halite/micro.py`, imported by `players/halite_player.py` and by the server's fallback
path, so the two can never drift. It is the Kaggle-proven trio the idea names —
**mine-richest-nearby, return-when-full, avoid-heavier-collisions** — made deterministic.

Definitions used below (all torus):

- `cargo(s)` — a ship's hold. `dist(a, b)` — Manhattan distance with wrap.
- **`unsafe(cell, myCargo)`** — true iff some **enemy** ship `e` with `cargo(e) <= myCargo` is on
  `cell` or orthogonally adjacent to it. (`<=`, not `<`: an equal-cargo collision kills both.) A cell
  holding one of my own shipyards is never unsafe.
- `claimed` — cells already taken by a friendly ship decided earlier this turn (self-collision guard).
- Tie-break for any move choice, in order: lower `unsafe`, then higher target-cell halite, then the
  fixed direction order `NORTH, EAST, SOUTH, WEST`.

Per turn:

1. **Shipyard-loss guard.** If I own no shipyard and some ship has `cargo + bank >= 500`, the ship
   with the largest cargo whose cell holds no shipyard orders `CONVERT`.
2. **Second yard.** Else if `ships >= 8`, `yards < directive.yards`, `bank >= 1500`, the ship with
   `cargo + bank >= 500` that is farthest from my nearest yard (and at least 5 away) orders `CONVERT`.
3. **Ships, ascending uid:**
   - a. **Come home** if `cargo >= directive.returnAt`, or `turn + dist(ship, nearestYard) + 2 >= maxTurns`
     (end-of-game sweep), or `unsafe(ship.cell, cargo)` and the yard is nearer than 3. Step along a
     shortest path to my nearest shipyard; among the ≤ 2 shortest-path directions take the tie-break
     order above; if every shortest step is unsafe, take the safest step that does not increase the
     distance by more than 1; if standing on the yard, hold (the deposit already happened).
   - b. **Mine** if the cell holds no shipyard, `cell.halite >= directive.mineFloor`, and holding is
     not unsafe → emit **no action** for this ship (the mine order in Halite is the absence of one).
   - c. **Hunt** (only when `directive.stance == "raid"`, and always for `corsair`): if `cargo <= 100`
     and an enemy ship with `cargo >= cargo + 200` is within 3, step toward it along the tie-break
     order, never into a cell that is unsafe for me.
   - d. **Go to the best patch.** Score every cell within radius 6 that is not `claimed` and not
     unsafe as `cell.halite / (1 + 2 * dist)`, biased +15 % toward `directive.focus`'s quadrant, and
     step toward the best one. If no cell scores > 0, step to the safest adjacent cell, or hold if the
     current cell is the safest.
   - e. Record the chosen destination in `claimed`.
4. **Shipyards, ascending uid:** order `SPAWN` while `turn <= directive.spawnUntil`,
   `bank - 500 * spawnsSoFar >= 500`, `ships + spawnsSoFar < 24`, and no friendly ship is standing on
   that yard this turn (a spawn under a returning ship is a self-collision that hands cargo to nobody).

**`corsair`** is the same function with a raider's constants and one extra rule: `mineFloor` 150,
`returnAt` 350, `spawnUntil` 340, hunting always on, and it will chase a heavy enemy up to distance 4
even at `stance != "raid"`. It exists so the ladder's two fillers play visibly different games and so
the collision rule — the reason this coworld exists — is exercised in every episode, including the
all-scripted CI smoke.

**Bounded orders are a tested property**, not a hope: at most one action per owned asset, only assets
the seat owns, only enum values, at most 256 entries, never a `SPAWN` the bank cannot pay, never a
`CONVERT` onto an occupied shipyard cell (`tests/test_micro.py`).

---

## Sim module

### Layout (what phase 20 creates, forking cogame-moba's shape)

```
vendor/
  UPSTREAM.md                     commit hash + sha256 per file + the emcc/Nim pins
  PATCHES.md                      "zero patches" + the rationale (below)
  LICENSE-kaggle-environments     Apache-2.0, verbatim
  upstream/kaggle_environments/helpers.py                 byte-pristine
  upstream/kaggle_environments/envs/halite/helpers.py     byte-pristine
  upstream/kaggle_environments/envs/halite/halite.py      byte-pristine
  upstream/kaggle_environments/envs/halite/halite.json    byte-pristine
sim/
  assemble.py        vendor/upstream/** + sim/shim/** -> build/khalite/kaggle_environments/**
  shim/kaggle_environments/__init__.py        ~30 lines: re-export .helpers, provide utils.structify
  shim/kaggle_environments/envs/__init__.py   empty
  shim/kaggle_environments/envs/halite/__init__.py  empty
server/cogame_halite/
  __init__.py version.py uris.py config.py defaults.py
  sim.py       the port surface (below)
  micro.py     tidewalker/corsair compile_turn (§Decisions) - imported by server AND players
  engine.py    lockstep loop, parallel batch, deadlines, strike rule, budget guard
  server.py    aiohttp: /player /global /client/* /healthz, artifacts, closed schemas
  events.py    the replay event vocabulary and its constructors
  replay.py    the JSON replay document writer/reader + FNV-1a state hash
  results.py   scoring ladder, placement, the closed results document
players/
  client.py            websocket client (moba's, adapted)
  halite_player.py     ONE entrypoint; PLAYER_PROMPT -> LLM, PLAYER_SCRIPTED -> micro
  llm.py               Bedrock/Anthropic provider, retry ladder, directive repair, rune caps
```

### Why there are no patches, and what replaces the wasm

cogame-moba compiles C to wasm because C's `rand()` and float behaviour differ per libc. **Halite is
Python**, and Python is already the portable artefact: the sim's only randomness is
`random` (CPython's Mersenne Twister) and `numpy.random`'s **legacy** `RandomState` (`np.random.seed`
+ `gumbel`/`binomial`), both of which are contractually stable across versions and platforms; the
arithmetic is IEEE-754 doubles and `round(x, 3)`. So the port does not transcribe the rules — **it
imports the vendored upstream modules and calls `Board(obs, config, actions).next()`**. `vendor/` stays
byte-pristine; `sim/assemble.py` copies it into `build/khalite/` and adds the three `__init__.py`
shims that upstream's own heavyweight `kaggle_environments/__init__.py` would otherwise drag in
(`vendor/upstream/.../helpers.py` does `import kaggle_environments.helpers`). `vendor/PATCHES.md`
records: **zero patches; the shim adds package `__init__` files and never touches a vendored byte**,
and `tests/test_vendor.py` proves it (sha256 per file, plus a byte-comparison of the assembled tree's
non-shim files against `vendor/upstream/`).

Two upstream code paths are **not** imported and are transcribed instead, with the citation next to
each and the fidelity gate over both:

- `populate_board` is called through a 20-line adapter that builds the `state`/`env` duck types it
  expects (`config.randomSeed`, `state[0].observation`, `state[0].reward = 5000`) — the function body
  itself is upstream's.
- the elimination + last-fleet block of `interpreter()` (12 lines) lives in `sim.py`, because our
  engine owns statuses. Its constants (`spawnCost`, `turn - episodeSteps - 1`) are read from the
  vendored `halite.json`, never re-typed.

### The port surface

```python
class HaliteSim:
    def __init__(self, config: GameConfig): ...       # config.seed -> configuration.randomSeed
    def reset(self) -> None                            # populate_board; turn = 0
    def step(self, orders: list[dict[str, str]]) -> TurnResult
    def observation(self, seat: int) -> dict           # §Server
    def ascii_board(self) -> str                       # the vendored Board.__str__, not a re-write
    def state_hash(self) -> str                        # 16 hex, FNV-1a 64
    def stats(self) -> SeatStats                       # mined, stolen, collisions_won/lost, built...
```

- **Purity.** The sim reads no clock, no environment, no disk. The global RNG state is **saved and
  restored** around `populate_board`, so nothing else in the process can perturb board generation, and
  no other sim code calls a RNG at all.
- **Determinism contract.** `(seed, config, per-turn orders)` determines the entire episode. That is
  what makes the replay re-derivable (§Tests).
- **`state_hash`** is FNV-1a 64 over a canonical encoding — `turn`, then each cell's halite formatted
  `%.3f` in index order, then each seat's `bank`, sorted `(yard_id, pos)`, sorted
  `(ship_id, pos, cargo)`, then the elimination turns. Recorded per turn in the replay; the re-sim
  test asserts every one of them.
- **Guard.** `HaliteGuardError` is raised (→ `reason = "fault"`, artifacts still written) on: a
  negative bank or cell, an `AssertionError` escaping the vendored code, a ship count above 5 000, an
  order map above 256 entries reaching the sim, or an unknown action value reaching the sim (the
  server is supposed to have dropped it).
- **Cost.** One `Board.next()` on a 441-cell board with ≤ 100 ships is ~1–2 ms; 400 turns ≈ 0.8 s.

### The fidelity gate — `tests/test_fidelity.py`

The acceptance criterion for the whole port, and a permanent CI gate (`AGENTS.md` rule 2 carries over
unchanged; if it fails, the port is wrong, never the test).

1. **Vendor identity.** sha256 of each vendored file equals `vendor/UPSTREAM.md`; every constant this
   note names is re-read from the vendored `halite.json` and asserted (a re-vendor that changes
   `collectRate` fails here, loudly, instead of silently changing the game).
2. **Differential episodes.** With `kaggle-environments==1.32.7` installed from the CI-only
   `fidelity` dependency group, for **8 seeds × 400 turns**: build the same random-but-legal order
   stream, drive upstream's own `make("halite", configuration={...})` env and our `HaliteSim`, and
   assert **equality of the full observation at every turn** — the 441-entry `halite` list element for
   element (exact floats), every player's `[bank, shipyards, ships]` including **dict insertion
   order**, `step`, and each agent's `status`/`reward`. Any divergence fails.
3. **Board generation.** For 50 seeds, our populated board equals upstream's, cell for cell, and the
   four starting positions are exactly `[110, 120, 320, 330]`.
4. **Floor.** The gate asserts a minimum of `8 × 399` compared turns, so a shrunken order stream can
   never quietly weaken it.

---

## Server, player, protocol

`docs/PROTOCOL.md` (forked from cogame-moba's) is the normative copy; this is the design.

### Runtime contract (inherited, unchanged in shape)

`COGAME_CONFIG_URI` in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`
out; `COGAME_LOAD_REPLAY_URI` for replay mode; `HOST`/`PORT`. Routes: `/healthz`;
`/player?slot=&token=` (**closes the socket unless the token matches the seat** — the cogame-flatland
0.1.1 certifier probe); `GET /client/player?slot=&token=` and `GET /client/global` as real pages
registered *before* any catch-all (lantern 0.1.1), neither of which opens a player socket; a `/global`
websocket that emits a first message immediately and keeps answering pings for a **20 s shutdown
grace** after artifacts are written (lantern 0.1.3); `/client/replay` serving the same bundle locally.
Players read `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`).

### Message flow

1. **`hello`** (server → player, on connect):
   `{"type":"hello","protocol":"halite/1","seat":2,"alias":"FLEET-CHARLIE","aliases":[...4],
   "config":{…resolved game config, no tokens…},"maxTurns":400,"directiveEvery":20}`
2. **`register`** (player → server, once, within the lobby):
   `{"type":"register","policy":"llm"|"scripted:tidewalker"|"scripted:corsair","label":"…≤40 runes"}`.
   A seat that finishes the lobby without one is logged as
   `SEAT <n> HAS NO REGISTER RECORD - PLAYING tidewalker` at ERROR and reported to
   `COGAME_PLAYER_FAILURE_URI`.
3. **`observe`** (server → **all four sockets before any reply is awaited**), every turn.
4. **`orders`** (player → server), one per `observe`.
5. **`done`** (server → player) after the last turn, then a bounded flush and close. Players **exit 0
   on a dead socket** (the raid 0.1.3 scar: a receive loop that raises on a close frame exits 1 and
   fails certification).

### The observation, in full

```json
{"type":"observe","turn":137,"maxTurns":400,"directive":false,"deadlineMs":400,
 "seat":2,"alias":"FLEET-CHARLIE","aliases":["FLEET-ALPHA","FLEET-BRAVO","FLEET-CHARLIE","FLEET-DELTA"],
 "config":{"size":21,"episodeSteps":400,"startingHalite":24000,"spawnCost":500,"convertCost":500,
           "moveCost":0.0,"collectRate":0.25,"regenRate":0.02,"maxCellHalite":500},
 "halite":[<441 numbers, 3-dp floats, index = (size-y-1)*size + x>],
 "players":[[<bank>,{"<yardId>":<pos>},{"<shipId>":[<pos>,<cargo>]}], … four …],
 "player":2,
 "eliminated":[null,null,null,312],
 "board":"<21 lines of the vendored Board.__str__>",
 "budget":{"elapsedMs":41230,"wallClockBudgetMs":660000}}
```

- **`halite`, `players`, `player` and the turn index are Kaggle's `observation` object, key for key**
  (`halite.json` §observation), so a Kaggle bot's `Board(obs, config)` works unchanged and the
  hundreds of open leaderboard bots the idea points at are portable. Everything else sits alongside
  it, never inside it.
- **Asset ordering is part of the contract**: `players[p][1]` and `players[p][2]` are serialised in
  upstream's insertion order and that is the order spawns and converts are processed in (§The game,
  step 2).
- **Nothing about the board is hidden** — Halite IV is a perfect-information game and the port does
  not change that. What *is* hidden: the other seats' **identities** (aliases only, always) and the
  other seats' **orders for the current turn** (simultaneity is enforced by the engine writing all
  four `observe` frames before awaiting any reply).
- `eliminated[s]` is the turn a seat was eliminated, or `null`.

### The reply, with every cap

```json
{"type":"orders","turn":137,"source":"llm",
 "actions":{"120-3":"NORTH","0-3":"SPAWN","95-1":"CONVERT"},
 "intent":"raid",
 "note":"squeezing BRAVO off the north cluster"}
```

| Field | Type | Cap / domain | On violation |
|---|---|---|---|
| `turn` | int | must equal the current turn | counted `wrong_turn`, treated as a miss |
| `source` | string | one of `llm`, `retry`, `scripted`, `fallback` (≤ 8 chars) | defaults to `scripted` |
| `actions` | object | **≤ 256 entries**; keys ≤ **24 chars**; values ∈ `{NORTH,SOUTH,EAST,WEST,CONVERT,SPAWN}` | over 256 → first 256 by ascending uid kept, rest dropped and counted; an unknown key/value or an id the seat does not own → that entry dropped (upstream ignores it too) |
| `intent` | string | one of `mine`, `expand`, `raid`, `defend`, `hold` (≤ 8 chars) | dropped |
| `note` | string | **≤ 140 runes**, spectator-facing | **truncated on a rune boundary** |

**Every string that can reach the replay is truncated on rune boundaries, never byte boundaries** —
`note` (140), `register.label` (40), `results.stop_detail` (200), any error text in a `fallback`
event (120). A byte-boundary truncation splits a multi-byte character and produces replay bytes that
render in a browser but fail a strict UTF-8 parser; `tests/test_replay.py` feeds emoji-laden notes
through the whole path and parses the result with `bytes.decode("utf-8")` (strict) plus
`json.loads`.

### Events written to the replay

One `events` array per turn, each `{"k": <kind>, …}`, emitted in the order the resolution produced
them. This is the complete vocabulary — the viewer draws from it and `tests/test_replay.py` schema-
checks every kind:

| kind | payload | drawn as |
|---|---|---|
| `spawn` | `seat, ship, pos` | a pop at the yard, +1 on the seat's ship count |
| `convert` | `seat, ship, yard, pos` | the new dock stamps in, scrubber **beat** |
| `deposit` | `seat, ship, yard, pos, amount` | coin arc into the plate, bank ticks up |
| `mine` | `seat, ship, pos, amount` | cell dims one step, hull pip grows (aggregated: one per mining ship) |
| `collide` | `pos, survivor:{seat,ship}\|null, lost:[{seat,ship,cargo}], stolen` | flash + shards, feed line, scrubber **beat** |
| `yardraze` | `pos, yardSeat, yard, shipSeat, ship` | dock cracks, scrubber **beat** |
| `eliminate` | `seat, turn` | plate greys out, scrubber **beat** |
| `lead` | `seat, bank` | crown moves, scrubber **beat** (emitted only when the leader changes) |
| `note` | `seat, text (≤140 runes), source, latencyMs` | speech line in the feed |
| `fallback` | `seat, cause, detail (≤120 runes)` | small grey chip in the feed |
| `strike` | `seat` | plate marked "silent" |
| `budget_guard` | `turn` | feed line, scrubber **beat** |
| `stop` | `rule, turn` | the endcard's win-condition chip |

### The replay document — self-sufficient by construction

A single **UTF-8 JSON** document (extension `.replay`), written once at the end and also streamable
to disk turn by turn:

```json
{"format":"cogame-halite-replay","version":1,"gameVersion":"1.0.0","protocol":"halite/1",
 "coworld":"halite","seed":8675309,
 "config":{ …every resolved game-config field, tokens excluded… },
 "names":["daveey","daveey-1","halite-tidewalker","halite-corsair"],
 "aliases":["FLEET-ALPHA","FLEET-BRAVO","FLEET-CHARLIE","FLEET-DELTA"],
 "policySources":["llm","llm","scripted:tidewalker","scripted:corsair"],
 "colors":["#e8a33d","#3fb6b0","#c65fa8","#8fbf3f"],
 "turns":[{"t":0,
           "halite":[<441 integers, round(cell)>],
           "players":[[<bank>,{"<yardId>":<pos>},{"<shipId>":[<pos>,<cargo>]}], …4],
           "orders":[{"<assetId>":"<ACTION>"}, …4],
           "events":[…],
           "hash":"9f2a41c07be31d55"}, …],
 "results":{ …the full results document… },
 "stop":{"rule":"full_time","turn":399}}
```

- **Everything the viewer needs is in the bytes**: real player names, aliases, colours, the full
  config, the seed, and the complete per-turn state. The viewer contacts **S3 and nothing else**.
- The per-turn `halite` array is rounded to integers because that is what is drawn; the exact float
  state is pinned by `hash`, and by `orders` + `seed`, which let CI re-derive the episode exactly.
- **`stop` is one load-bearing record applied by the same code on record and on re-derive** — a
  wall-clock stop is a wall-clock fact that cannot be recomputed from sim state (the particle-worlds
  2026-08-26 scar), so it is recorded, not inferred, and `tests/test_replay.py` runs the
  record → re-derive check for **every** end reason, not just `complete`.
- Size: ~2.7 kB/turn ⇒ **≈ 1.1 MB** for a 400-turn episode, ≈ 330 kB for the 120-turn CI fixture.

### The results document (closed schema)

Exactly these keys, in `server/cogame_halite/results.py`, in the manifest's `results_schema`
(`additionalProperties: false`) and in `tools/ci/docker_smoke.sh`'s expected-key set — three places,
one list, asserted equal by `tests/test_results.py`:

```
names[4]            real policy names, seat order (spectator side only)
aliases[4]          FLEET-ALPHA … FLEET-DELTA
scores[4]           the scoring formula above; higher is better
placement[4]        1..4 with the tie-break ladder
ranking[4]          strict seat order, ladder rule 4 applied
win[4]              placement == 1
winner              seat index or null
reason              "complete" | "deadline" | "fault"
end_rule            "full_time" | "last_fleet" | "wall_clock" | "fault"
final_turn          the last recorded turn
seed                the episode seed
banked[4]           final bank
ships[4] yards[4]   assets alive at the end
mined[4] stolen[4]  lifetime halite scraped / taken in collisions
collisions_won[4]   collisions_lost[4]
eliminated_turn[4]  int or null
llm_turns[4]        turns answered with source llm|retry
fallbacks[4]        {timeout, malformed, wrong_turn, disconnected, host_error}
dead_seats[4]       strike-rule flag at the end
stop_detail         "" or ≤200 runes
```

---

## Viewer

### One starter supplies all four viewer files: **`Metta-AI/coworld-ctf`**

| File in this repo | Taken from coworld-ctf |
|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` — the emscripten link block (`-sALLOW_MEMORY_GROWTH`, `-sABORTING_MALLOC=1`, `EXPORTED_FUNCTIONS`, `--preload-file`), renamed outputs `halite_replay.{js,wasm,data}` |
| the wasm entry `.nim` | `replay-viewer/ctf_replay.nim` → `replay-viewer/halite_replay.nim` |
| `static_replay*.js` | `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js` |
| `index.html` | `client/replay_broadcast.html`, which the build turns into `index.html` (ctf's `Dockerfile.replay-viewer` does exactly this with two `sed` placeholder substitutions) |

**All four come from that one starter and from nowhere else.** Splicing one starter's shell onto
another's emscripten bootstrap (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` boot) deadlocks
the viewer silently with every file present and every request 200 — cogame-lantern, 2026-08-23. The
three adaptations we make are the ones `cogame-factorio` already made to the same four files and
documented in its `client/static_replay.js` header: (1) `start()` takes the replay bytes the page
fetched, (2) the "sim mismatch tick" attribute is dropped because **nothing is re-simulated in the
browser** — the wasm renderer draws the recorded per-turn state — and (3) the exported symbols are
renamed `_halite_*`. `client/chrome_common.js` and `client/broadcast_core.js` are copied from ctf
**byte-for-byte** (unused ctf helpers stay in the file, unreferenced; deleting from a byte-for-byte
copy is precisely what the pin forbids).

The shell sets **`data-replay-loaded="true"` on `<html>` on its first drawn frame** and
**`data-replay-error="<message>"` on failure** — ctf's `static_replay.js` already does both, and the
`coworld-replay` bridge `ready` message is posted **from the callback that runs after
`data-replay-loaded` is set**, never on rAF timing at the call site (the chorus 2026-08-24 scar, where
softmax.com sampled an unpainted shell).

Bundle: `game.replay_viewer.bundle = "static-replay-viewer"`, built by
**`tools/build_replay_viewer.sh`** (ctf's hook, with `mkdir -p` of the output parent before the
containment check — the ecos 2026-08-23 fix), which runs the Dockerfile's `wasm-builder` stage
(emsdk 4.0.15 + nimby 0.1.27 + Nim 2.2.4 + `nimby --global sync nimby.lock`) and copies out
`viewer/dist`. The hook asserts every file the page references exists:
`index.html`, `chrome_common.js`, `broadcast_core.js`, `static_replay.js`, `static_replay_worker.js`,
`halite_replay.js`, `halite_replay.wasm`, `halite_replay.data`.

### Chrome provenance — what is kept, what is removed

`client/replay_broadcast.html` is **coworld-ctf's page with one appended game block** (a
`<!-- HALITE -->` section at the end plus the CSS block for the readouts it adds). It is not a rewrite
that reuses ctf's ids — the cogame-gridlock 2026-08-23 failure. Kept verbatim, ids and CSS untouched:
`#chrome`, `#scorebug`, `#plates-l` / `#plates-r`, `#clock` / `#clock-time` / `#clock-caption`,
`#stage`, `#viewport`, `#board` (the canvas), `#status`, `#killfeed` (now the halite event feed),
`#bannerlane`, `#grain`, `#lightpool`, `#endcard` with every `#ec-*` child, and the whole `#transport`
block (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-skip`, `#btn-end`, `#btn-loop`,
`#btn-spoilers`, `#win-chip`, `#tick-clock`, `#speedchips`, `#scrub`, `#scrub-fill`, `#scrub-win`,
`#scrub-head`).

**Removed** (paintball-specific, nothing in Halite maps onto them):
`#fpv`, `#fpv-canvas`, `#fpv-cap`, `#fpv-gear`, `#fpv-grip`, `#fpv-hp`, `#fpv-hud`, `#fpv-map`,
`#fpv-map-canvas`, `#fpv-name` (the eye-level raycaster PiP); `#lockerroom`, `#lk-art`, `#lk-bg`,
`#lk-cap`, `#lk-sprites`; `#momentum`; `#lulls` with `#ffwd-chip` and `#ffwd-mini`; `#povBadge`; and
their CSS blocks.

**Zoom: dropped.** The board is a fixed 21 × 21 arena that always fits the frame, so the pin's rule
("`#viewpanel` exists only for boards larger than the frame") removes it: `#viewpanel`, `#zoombar`,
`#zoom-in`, `#zoom-out`, `#zoom-read`, `#zoom-slider`, `#minimap`, `#minimap-canvas`, `#mmwarn`, the
`body[data-noviewpanel]` rule and the `?viewpanel=0` handler all go. Consequently the wasm-viewer CI
job keeps `--strict-text-bounds` (correct for a fixed arena).

**Transport rules, inherited and non-negotiable:** `relayout()` sets **`--band`** and **`--topband`**
(the measured transport and scorebug heights) and **`--hudscale`** on `:root`, iterating to a fixed
point; the board is fitted **between** the two bands, so **no overlay ever sits in the transport
band**; the endcard is `bottom: var(--band)` and **every seek dismisses it**; scrubber beats are
**clickable labelled `<button>`s** that seek to their turn, with a CSS rule for **every kind emitted**
— `.beat-marker.convert`, `.beat-marker.collide`, `.beat-marker.yardraze`, `.beat-marker.eliminate`,
`.beat-marker.lead`, `.beat-marker.guard` (labels: `yard`, `ram`, `raze`, `out`, `lead`, `guard`).
The appended game block **must not define `markBeat`** — it uses the chrome alias
(`var markBeat = C.markBeat`); its own builder is named `haliteBeat`, and `tests/test_viewer.py`
runs a scope-duplication check over the alias list (the tandem 2026-08-23 hoisting scar).

### What it draws

- **Board.** 21 × 21 cells on the seabed tile; each cell's halite drawn as a crystal sprite at one of
  six density steps (0, 1-49, 50-149, 150-299, 300-449, 450-500) with a brightness ramp, so a
  spectator reads richness at a glance without numbers. Ships are the seat-coloured hull sprite with a
  **cargo pip** whose size and glow scale with cargo (0 → 2000+). Shipyards are the seat-coloured
  dock. Mining pulses the cell; a collision flashes white and throws shards toward the survivor;
  a raze cracks the dock.
- **Cargo-at-risk overlay (the idea's ask, in v1).** Derived per turn from recorded state: a ship is
  **at risk** iff some enemy ship with cargo **≤** its own is within torus Manhattan distance 1 — the
  exact predicate the ram rule uses next turn. At-risk ships get a pulsing red halo scaled by the
  cargo they would lose, and the ≤ 4 cells a lighter enemy could ram them from get a faint red wash.
  Always on; `r` toggles it. Total halite-at-risk per seat is a scorebug readout, so the
  "he is carrying 1 800 and BRAVO is one cell away" moment is legible before it happens.
- **Scorebug (four plates, two per column).** Alias, **real policy name**, colour swatch, **banked
  halite** (big, tabular), cargo afloat, ships, yards, at-risk halite, a crown on the leader, a grey
  wash on an eliminated seat. `.plate-name { flex: 1 1 auto; min-width: 3.2em }` and secondary labels
  hidden under 640 px — the featured-match iframe is ~360 px wide and names collapse to "…" without
  it.
- **Clock.** `TURN 137 / 400` plus the day-phase-free caption `mining` / `hauling` / `raiding` derived
  from the turn's event mix.
- **Feed** (`#killfeed`): the last ~12 events in words — *"BRAVO rams CHARLIE at (7,12) — takes 480"*,
  *"ALPHA banks 620"*, *"DELTA converts at (15,5)"*, and each LLM `note` as a speech line under its
  alias.
- **Endcard**: final standings 1–4 with alias + real name, banked, mined, stolen, collisions won/lost,
  ships built, elimination turn, and the win-condition chip from `stop.rule`.
- **Playback**: 125 ms per turn at 1× (a 400-turn episode plays in 50 s; the 120-turn CI fixture in
  15 s, which outlasts the 12 s soak — the ecos 2026-08-23 sizing rule), speeds from ctf's chrome
  (0.5/1/2/4/8).
- **Legible at 360 px wide**: this is a stated acceptance property, checked by `viewer_smoke.mjs` at
  360 × 640 as well as at desktop size, and by the renderer fixture at three canvas sizes.

### Art

Real art, committed, no placeholders and no runtime downloads. Rendered with
`playbooks/art-nanobanana.md` (`gemini-2.5-flash-image`, ≤ 10 generations, source sheets committed
under `scripts/art/source/` with the split script):

- `data/art/hulls_sheet.png` → `hull_{alpha,bravo,charlie,delta}.png` — one Softmax-cog-crewed barge
  per seat colour, top-down, 64 px.
- `data/art/yards_sheet.png` → `yard_{alpha,bravo,charlie,delta}.png` — the matching dock, 64 px.
- `data/art/halite_crystals.png` — one 6-frame density sheet, 64 px per frame.
- `data/art/seabed.png` — a 512 px tiling salt-flat floor.
- ctf's fonts and `client/art/` chrome furniture are kept as-is.

All of `data/art/` is preloaded into the wasm bundle by `--preload-file` in `config.nims`, so the
bundle is self-contained.

---

## Packaging

- **`compose.yaml`** — one service, name = the coworld name **`halite`** (the manifest image
  placeholder is derived from the compose service name: `{{HALITE_IMAGE}}`; `{{GAME_IMAGE}}` is not a
  thing — the lantern 0.1.0 scar), `platform: linux/amd64`, `build: {context: ., network: host}`,
  image `coworld-halite:latest`.
- **`Dockerfile`** — two stages. `wasm-builder` runs on `$BUILDPLATFORM` (wasm output is
  arch-independent) with emsdk 4.0.15 + nimby 0.1.27 + Nim 2.2.4 and produces `viewer/dist`. The
  runtime stage is `--platform=linux/amd64` on `python:3.12-slim`, `uv sync --frozen --no-dev`, copies
  `server/`, `players/`, `vendor/`, the assembled `build/khalite/`, `data/art/` and `viewer/dist`.
  One image, two entrypoints: game `python -m cogame_halite.server`, player
  `python -m players.halite_player`.
- **`coworld_manifest_template.json`** — `$schema`, ≥ 3 `tags`
  (`["halite","kaggle","economy","free-for-all"]`), **`episode_timeout_minutes: 20`** at the **top
  level** (the 1200 s the degrade pin assumes), and under `game`: `name: "halite"` (no underscore, so
  the secret namespace and the page slug agree), `description` (required), `owner`,
  `runnable {type: "game", image: "{{HALITE_IMAGE}}", run: ["python","-m","cogame_halite.server"], source_url}`,
  **`replay_viewer: {"bundle": "static-replay-viewer"}` under `game`** (not top level),
  `config_schema` (a real JSON Schema — the CLI validates every variant and the cert fixture against
  it and injects `tokens`, so **no `game_config` may contain a literal `tokens`**, and **every array
  property declares `minItems`/`maxItems`**), `results_schema` (closed, the key list above),
  `docs` and `protocols`.
- **`game.docs`** — `readme` → `README.md`, and **`pages`**:
  `rules.md` "Rules & bit-exactness" → `docs/RULES.md`, `replay.md` "Replay format" →
  `docs/REPLAY.md`. **`game.protocols`** carries **both** `player` and `global`, each a
  `{"type":"uri","value":".../docs/PROTOCOL.md"}` **object**, never a bare string.
- **Bundled players** (top-level `player[]`, each with `id`/`type`/`name`/`description`/`image`
  `{{HALITE_IMAGE}}`/`run`/`source_url` and `resources {requests: {cpu 250m, memory 256Mi}, limits: {cpu: "1"}}` —
  the cpu limit minimum is `"1"`):

  | id | run | env |
  |---|---|---|
  | `tidewalker` | `["python","-m","players.halite_player"]` | `PLAYER_SCRIPTED=tidewalker` |
  | `corsair` | `["python","-m","players.halite_player"]` | `PLAYER_SCRIPTED=corsair` |

- **Variants — `num_agents` = 4 inside every one's `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false`; the platform reads only
  `game_config.num_agents`, and a missing one schedules zero episodes):

  | variant | `num_agents` | `episode_steps` | `directive_every` | other |
  |---|---|---|---|---|
  | `standard` — "Standard (400 turns)" | **4** | 400 | 20 | `starting_halite` 24000 |
  | `sprint` — "Sprint (200 turns)" | **4** | 200 | 10 | ladder throughput; same rules |
  | `richfields` — "Rich fields" | **4** | 400 | 20 | `starting_halite` 32000 — denser board, more contested cells |

  Every variant's `game_config` also carries `players: [{"name":"Fleet A"},…4]`, `seed` omitted
  (fresh per episode, recorded), `turn_deadline_ms` 400, `directive_deadline_ms` 18000,
  `directive_spacing_ms` 10000, `player_connect_timeout_seconds` 120,
  `wall_clock_budget_seconds` 660.

- **Certification fixture** — `certification.game_config` carries **`num_agents`: 4** plus
  `episode_steps: 120`, `seed: 42`, `directive_every: 20`, `player_connect_timeout_seconds: 60`,
  `wall_clock_budget_seconds: 300`, and four `players` entries. `certification.players` seats
  **both** declared bundled players (`tidewalker`, `corsair`, `tidewalker`, `corsair`) — every
  declared `player[]` entry must occupy a slot or cert fails `players_missing` (raid 0.1.2). Timing:
  120 turns × ~30 ms + connect grace ≈ 15 s, comfortably inside `coworld certify`'s 60 s default; the
  resulting replay is 15 s of playback, which outlasts the viewer soak.
- **`tools/ci/policies.json`** — two LLM champions and two scripted fillers, the canonical set:

  ```json
  [{"name":"halite-tidereader","run":["python","-m","players.halite_player"],
    "env":{"PLAYER_PROMPT":"Play the bank. Mine the richest cell within three steps, come home before you are the heaviest ship on the board, and never let a loaded ship end a turn next to a lighter enemy. Build a second shipyard early on the far side of your quadrant.","USE_BEDROCK":"true"}},
   {"name":"halite-privateer","run":["python","-m","players.halite_player"],
    "env":{"PLAYER_PROMPT":"Play the collision rule. Keep your hulls light and hunt loaded enemy ships near their shipyards; take the cargo instead of mining it. Spawn aggressively while halite is cheap and raze an undefended enemy yard when the trade is even.","USE_BEDROCK":"true"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"halite-tidewalker","run":["python","-m","players.halite_player"],"env":{"PLAYER_SCRIPTED":"tidewalker"}},
   {"name":"halite-corsair","run":["python","-m","players.halite_player"],"env":{"PLAYER_SCRIPTED":"corsair"}}]
  ```

  Champion #1 (`halite-tidereader`) is owned by daveey; champion #2 (`halite-privateer`) carries the
  `player` field so it is uploaded while daveey-1 is active. Both champions are `PLAYER_PROMPT`
  policies. Filler versions must differ from champion versions.
- **Workflows** — `.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
  with `ci.yml`'s `test` job adapted to Python (`uv sync --frozen` + `uv run pytest`, plus the
  `fidelity` dependency group) and its `SLUG=halite`, `IMAGE=coworld-halite`, **`<SEATS>` = 4**.
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed **executable (0755)** —
  `coworld build` hard-requires `os.X_OK` on the hook.
- The release workflow's `secret put` uses namespace **`game.name` = `halite`** and runs **after**
  `upload-coworld`; policies upload **before** it; a "Confirm canonical" poll on
  `coworld status <cow_id> --json` sits between upload and secret put.

---

## Tests

Everything runs in `ci.yml` (the sandbox has no docker, no nim, no emsdk, no browser). Jobs: `test`
→ `docker-smoke` → `wasm-viewer` (`needs: docker-smoke`) → `upload-coworld` (gated on the first two).

**Sim and port**

1. `tests/test_vendor.py` — sha256 of each `vendor/upstream/**` file matches `vendor/UPSTREAM.md`; the
   assembled `build/khalite/` tree is byte-identical to vendor except the three shim `__init__.py`s;
   every constant this note names is re-read from the vendored `halite.json` and asserted (the
   re-vendor tripwire).
2. `tests/test_fidelity.py` — **the gate**: 8 seeds × 399 turns of differential comparison against
   `kaggle-environments==1.32.7`, exact observation equality per turn (floats, dict order, statuses,
   rewards); 50-seed board-generation equality; starting positions `[110,120,320,330]`; a tick-count
   floor so the stream cannot silently shrink.
3. `tests/test_sim.py` — one test per numbered rule in §The game: spawn ordering and the bank ceiling;
   convert funding, the `leftover_convert_halite` hold-aside, and the cell being zeroed; the ram rule
   (lighter survives and absorbs), the equal-cargo mutual kill, a three-way pile-up; friendly fire;
   yard razing; deposit-after-collision; the mining gate (moved / on a yard / `delta == 0`); regen
   skipping occupied cells, the `round(x, 3)`, the 500 cap; torus wrap in all four directions; uid
   minting `f"{turn}-{n}"` across seats; elimination and the negative score; last-fleet ending.
4. `tests/test_hash.py` — `state_hash` is stable across processes and changes on any single-field
   perturbation.

**Baseline legality (the bounded-orders assertion)**

5. `tests/test_micro.py` — over 200 randomly-generated boards × both baselines: **≤ 1 action per owned
   asset**, only ids the seat owns, only enum values, **≤ 256 entries**, never a `SPAWN` the bank
   cannot pay, never a `CONVERT` onto a cell holding a shipyard, and the safety property *"never steps
   onto a cell adjacent to a strictly lighter enemy while carrying cargo, when a safe step exists"*.
   Plus determinism: the same state and directive compile the same orders twice.
6. `tests/test_players.py` — `PLAYER_SCRIPTED` / `PLAYER_PROMPT` switching; unrecognised name →
   `tidewalker`; the directive repair table (each clamp, each dropped field, trailing prose,
   fenced JSON); **rune-boundary truncation** with 4-byte emoji at every cap; the retry ladder logs
   `will retry` and only a genuine fallback says `falling back`; the player **exits 0** when the
   socket closes mid-receive.
7. `tests/test_engine.py` — all four `observe` frames are written before any reply is awaited (the
   parallel-batch property); the shared deadline; late/malformed/wrong-turn/disconnected each produce
   the right `fallbacks` key and a `tidewalker` substitution; the strike rule at 10 and its revival;
   the budget guard at 600 s and the hard stop at 660 s (injected clock); the directive spacing floor;
   no `await` on player input without a deadline (a static scan plus a hung-player test that must
   finish).

**End to end**

8. `tests/test_replay.py` — a real 120-turn, 4-seat episode is played in-process and writes a replay;
   the bytes **decode as strict UTF-8** and `json.loads` cleanly (with emoji notes in the stream);
   `format`/`version`/`names`/`aliases`/`config`/`seed`/`colors` all present; every event validates
   against its schema; and the **re-derivation**: replaying `seed` + per-turn `orders` on a fresh
   `HaliteSim` reproduces every turn's `hash`, run once **per end reason** (`full_time`,
   `last_fleet`, `wall_clock`, `fault`) because the `stop` record is load-bearing.
9. `tests/test_results.py` — the closed key set equals the manifest `results_schema` equals
   `docker_smoke.sh`'s expected set; the scoring formula and sign; the placement tie-break ladder
   including a three-way tie; a `deadline` episode is still scored and ranked.
10. `tests/test_server.py` — `/healthz`; `GET /client/player?slot=&token=` and `/client/global` serve
    real pages and open no player socket; a **bad player token is rejected**; `/global` emits a first
    message and answers pings through the 20 s shutdown grace; the failure payload is exactly
    `{"message","failed_policy_index"}`; a seat that never registers is logged and reported.
11. `tests/test_privacy.py` — no real player name appears in any `observe` frame, prompt, `note` or
    in-board string; the replay's `names` **does** carry them.
12. `tests/test_manifest.py` — `num_agents == 4` inside **every** variant's `game_config` and in
    `certification.game_config`; **absent** at any variant's top level; both bundled players occupy
    cert slots; `episode_timeout_minutes` top-level; `game.replay_viewer` under `game`; no top-level
    `version`, no `game.display_name`, `game.owner` present, `game.description` present, no
    `game.tags`; no `tokens` in any `game_config`; every `config_schema` array has
    `minItems`/`maxItems`; docs/protocols object shapes; plain `\d+\.\d+\.\d+` version; and the
    installed `coworld` CLI's own `_load_template_manifest` + `validate_upload_manifest` run as a CI
    step.
13. `tests/test_viewer.py` — the built bundle's JS runs under node against the CI replay (factorio's
    `tests/test_viewer.py` pattern): the document parses, the turn count matches, every beat kind
    emitted by `events.py` has a `.beat-marker.<kind>` CSS rule, the chrome alias list has no
    shadowing duplicate in the appended game block, and `index.html` references every bundled file
    with relative paths only.

**Packaging and the viewer, in CI**

14. `docker-smoke` — `docker build` then `./tools/ci/docker_smoke.sh coworld-halite:ci` with
    **`SMOKE_SEATS=4`**: a real containerised 4-seat episode (no `ANTHROPIC_API_KEY`, so every seat
    plays scripted), asserting `reason == "complete"`, the exact results key set, **all four
    seat-count invariants** (`certification.game_config.num_agents` present, a positive integer, and
    equal to `len(certification.players)`, `len(certification.game_config.players)` and
    `SMOKE_SEATS`), every **player** container's exit code 0, and the replay written to
    `dist/smoke/`, uploaded as the `smoke-replay` artifact.
15. `wasm-viewer` (`needs: docker-smoke`) — asserts `tools/build_replay_viewer.sh` and
    `tools/ci/viewer_smoke.mjs` exist (the hook executable), **builds** the bundle, then **executes**
    it: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/*.replay
    --timeout 90 --strict-text-bounds --soak 12` in headless chromium pinned to Playwright 1.55.0 —
    the bundle is run against **the replay `docker-smoke` just produced**, not a hand-written fixture.
    A second run at 360 × 640 checks the featured-match width. Screenshot + `viewer-smoke.json`
    uploaded `if: always()`.
16. A third viewer step runs `viewer_smoke.mjs --strict-text-bounds` against
    **`tools/ci/renderer_fixture.html`**, which loads the shipped
    `dist/static-replay-viewer/index.html` in an iframe, shims only the wasm entry, and drives the
    page's own text path with a **full-cap 140-rune `note` on every seat** at three canvas sizes.
    Without it no CI replay ever carries LLM text (the smoke runs with no API key), so the feed and
    speech chrome would never be exercised (the cogchemists 2026-08-24 scar).

---

## Out of scope (v1)

- **Embedding Kaggle's HTML replay renderer.** Overridden by the static-viewer pin; the idea's ask is
  answered by this repo's own bundle. (The cargo-at-risk overlay the same line asks for **is** in v1.)
- **Halite seasons I, II and III.** The port is Halite IV, the season `kaggle-environments` ships.
- **1-player and 2-player agent counts.** Upstream allows `[1, 2, 4]`; every variant here is 4 seats.
- **`remainingOverageTime`**, Kaggle's per-agent time bank. Our pacing is the engine's deadlines; the
  field is present in the observation for shape compatibility and is always the config default.
- **Importing the open Kaggle bot corpus** as policies (a licensing and packaging job of its own), and
  RL-vector policies of any kind.
- **Automated alliance-pattern audit tooling.** Every order of every seat is in the replay, so the
  analysis is possible offline; the tool that runs it is not shipped in v1.
- **An in-viewer multi-step risk heatmap** (reachability beyond one turn), a spectator "what if" scrub,
  and per-ship LLM control (v1's LLM issues a 20-turn directive; the micro layer moves the ships).
- **A live spectator pod** of any kind — replays are a static file plus the wasm bundle, always.
