# cogame-magent-battle — design note (2026-08-27)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout, the `src/<game>/` module split with `sim.nim` re-exporting the sim modules and
`sim_types.nim` owning `GameVersion` and the flatty wire format; the mummy server implementing the
Coworld contract; the `decide.nim`/`directives.nim`/`llm.nim`/`baselines.nim` commander layer with its
parallel batch, rune caps and fallback ladder; the binary `COWLD…` replay of *inputs plus a per-tick
`gameHash`*, re-simulated by **the same sim module** compiled to wasm by
`replay-viewer/config.nims`; the `client/` broadcast chrome; nimby + `Dockerfile` +
`Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh`; and the four-shard Nim test suite.
The precedent for forking it for an external-env port is six deep (knights-archers, pistonball,
atari-cabinet, walker-waterworld, particle-worlds, smac-starcraft-micro).

Where this note departs from coworld-ctf it says so and gives the reason. The departures are: the
game's rules are MAgent's, not paintbot's (§Sim module lists what is deleted); the arena is a
45×45 integer **grid**, so ctf's pixel geometry, procedural map generator, map pool, map editor and
mapkit are deleted; and the port carries four upstream-fidelity gates ctf has no equivalent of
(§Sim module → "Proving the port").

### Source idea (verbatim)

> Port of MAgent (Zheng et al. 2018; MAgent2 in PettingZoo-style API). Scenarios: battle (two armies
> of 64-1000 units, each with a local view, attack neighbours for reward; kills win), battlefield
> (same with obstacles), gather (agents compete for food, can attack each other), tiger_deer
> (predators must pair up to kill prey), adversarial_pursuit. The scale is the point: policies are
> per-unit but hundreds of instances run, so the league seats a *policy* that controls a whole army
> (closest to our NMMO/Hive posture) OR seats individual squads.
>
> Seats: 2 armies (policy-per-army) or N squads
> Motive: zero-sum army battle / mixed gather
> Policy interface: per-unit local-obs → action, vectorised; neural/scripted coworld
> Fills gap: mass combat with emergent formations — 06 Hive is non-combat swarm; nothing on the site
> has two swarms fighting
> Integrity (anti-collusion): zero-sum; map seeded; anonymous aliases.
>
> Replay plan (watchability): army heatmaps, front line visualisation, unit-count sparkline — it's
> already a spectacle in the original demos.
>
> Source: github.com/geek-ai/MAgent; Farama MAgent2.

### Upstream, pinned

The rules being reproduced are **MAgent2's `battle_v4`** (`Farama-Foundation/MAgent2`,
`magent2/environments/battle/battle.py`), fetched and read in full while writing this note. Every
constant below is quoted from that file; §Sim module records how the build pins it and how CI proves
the port has not drifted.

| Upstream fact | Value |
|---|---|
| `default_map_size` | 45 (square) |
| Agents | 162 total — `red_[0-80]` / `blue_[0-80]`, i.e. **81 per army** |
| Agent type `small` | `width 1, length 1, hp 10, speed 2, damage 2, step_recover 0.1` |
| `view_range` | `CircleRange(6)` → a 13×13 local view |
| `attack_range` | `CircleRange(1.5)` → the 8 Moore neighbours |
| Action space | `Discrete(21)` = `[do_nothing, move_12, attack_8]` |
| Observation | `(13,13,5)`: obstacle/off-map, my presence, my hp, other presence, other hp |
| `max_cycles` | 1000 |
| Rewards | `step_reward -0.005`, `dead_penalty -0.1`, `attack_penalty -0.1`, `attack_opponent_reward +0.2`, `KILL_REWARD 5` |
| Friendly fire | "An attack against another agent on their own team will not be registered." |
| Kill reward | granted by the engine to the killer when an attack drops a victim to 0 hp — **not** a reward rule (no double payment) |
| Spawn | `generate_map`: two blocks, `init_num = map_size² × 0.04`, `side = int(sqrt(init_num)) × 2`, `gap = 3`, stride 2, right block truncated to the left block's size |
| Defaults kept | `minimap_mode = False`, `extra_features = False` |

**An upstream asymmetry this note has to handle.** At `map_size = 45`, `generate_map` puts red on
columns `{1,3,…,17}` and blue on `{25,27,…,41}`. The mirror of red about the centre column 22 would be
`{27,…,43}`, so **blue starts two columns closer to contact and three cells off its own wall where red
is one.** It is small and it is upstream's, so the port keeps it byte-for-byte — and neutralises it the
way the starter already neutralises seat asymmetry in `paintball` (`maxGames: 2`, "the two halves are
averaged"): **every episode is two games with the sides swapped**, and the score is their sum.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time loop, RL-vector sim, external-env port (title paragraph, §Sim module) |
| Public `Metta-AI/cogame-magent-battle` | §Packaging |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=line\|pincer`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance; ctf soldier art + arena floor) |
| Two name spaces | §The game (aliases `Alpha`/`Bravo` in-game; real names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (worst case 553 s, hard stop 660 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 2`, three times |
| Simultaneous decisions issued as one parallel batch | §Decisions |
| Replay bytes self-sufficient | §Server (plus `tools/replay_summary.py`, the strict-UTF-8 JSON view of them) |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |

---

## The game

Two armies of infantry meet on an open 45×45 grid. Each army is 81 identical soldiers with 10 hp that
regenerate slowly, that move up to two cells a turn or strike an adjacent enemy for 2 damage. Nobody
plays a soldier. Each of the **two seats is an army commander**: once every 20 sim ticks it issues one
order to each of its **nine squads**, and a deterministic squad controller turns those orders into the
MAgent actions its soldiers actually take. A commander sees only what its own soldiers can see. The
army with more soldiers standing when the game ends wins it; an episode is two games with the sides
swapped, and the seat that wins the pair wins the episode.

### Seats, armies, squads, aliases

- **`num_agents` = 2.** Exactly two seats, always, in every variant and in the certification fixture.
  This is the idea's "2 armies (policy-per-army)" option; the N-squads seating is §Out of scope.
- **Sides swap between the two games.** Seat 0 is **red** (left) in game 1 and **blue** (right) in
  game 2; seat 1 the reverse. Both games use the same seed, so both seats play the identical starting
  position from both sides.
- **Two name spaces.** In-game, seat 0 is **`Alpha`** and seat 1 is **`Bravo`**. Those aliases are the
  only names that appear in an observation, a prompt, an order, a `say` or a sprite label. The seats'
  **real policy/player names** (`daveey`, `daveey-1`, `Baseline (1)`) live only in `results.names`, in
  the replay's join records and in the viewer's scorebug. `showPlayerLabels` is **false**, as in the
  starter's paintball variant, so no in-board sprite can leak an identity. A commander can never learn
  who it is playing — the idea's anti-collusion requirement.
- **Squads.** Each army is partitioned into **exactly 9 squads**, ids `A1`…`A9` (Alpha's) and
  `B1`…`B9` (Bravo's), in every variant and both games. Assignment is by initial position: the army's
  spawn list is sorted by **distance from its own back edge** (red: ascending `x`; blue: descending
  `x`), ties by ascending `y`, then split into 9 contiguous blocks as equal as possible. At
  `mapSize = 45` the spawn block is 9 columns × 9 rows, so squad `k` is exactly the `k`-th column:
  **`A1`/`B1` is the rearmost rank, `A9`/`B9` the front rank.** At `mapSize = 31` the 25 soldiers
  split `3,3,3,3,3,3,3,2,2`. Membership is fixed at spawn; a squad with no living soldier reports
  `alive: 0` and its orders are ignored.

### The grid, the soldiers, the clock

- Board: `mapSize × mapSize` cells, no obstacles (this is `battle`, not `battlefield`; upstream
  `battle` has none either). Cells outside the board read as "obstacle/off-map".
- Soldier: `hp` in **tenths** (`HpMax = 100` ≡ 10.0), `Damage = 20` ≡ 2.0, `StepRecover = 1` ≡ 0.1 per
  tick, capped at `HpMax`. One soldier per cell. The dead are removed from the grid immediately.
- **Move offsets** (12, `CircleRange(2)` = `dx² + dy² ≤ 4`, centre excluded), in this fixed order:
  `(-2,0) (-1,-1) (-1,0) (-1,1) (0,-2) (0,-1) (0,1) (0,2) (1,-1) (1,0) (1,1) (2,0)` as `(dy,dx)`.
- **Attack offsets** (8, `CircleRange(1.5)` = the Moore neighbours), in this fixed order:
  `(-1,-1) (-1,0) (-1,1) (0,-1) (0,1) (1,-1) (1,0) (1,1)` as `(dy,dx)`.
- **Action index**, the upstream 21-way space kept intact: `0 = do_nothing`, `1..12 = move` by the
  move offsets in order, `13..20 = attack` by the attack offsets in order.
- **Tick** = one MAgent cycle. **Command turn** = one order round, every `turnTicks = 20` ticks,
  beginning with turn 1 at tick 0 before any stepping. `maxTicks = 300` per game, `maxGames = 2` ⇒
  **15 command turns per game, 30 per episode, 600 ticks of play** — the same totals the timing
  budget was sized for.

### Turn and tick structure — the exact resolution order

Per **command turn** `T` (at tick `20·(T−1)` of the current game), in this order:

1. The engine snapshots the world and builds **both** seats' observation objects (§Decisions).
2. Both seats' LLM requests go out as **one parallel batch** (`curly.makeRequests`, the starter's
   `decideAll` shape), attempt-1 deadline `attempt1Ms = 9000`. Scripted seats compute locally, instantly.
3. Each seat that timed out, errored, returned non-JSON or returned no usable `orders` array is
   retried **once**, again as a single batch, `retryMs = 4000`.
4. A seat still without a usable reply gets the **`pincer`** scripted orders computed server-side, and
   a `fallback` record is written (§Decisions).
5. Orders are applied to squads. A squad named in the reply takes the new order; a squad not named
   keeps the order it had (turn 1's default for every squad is `advance`). An order whose fields do not
   validate is **repaired to the squad's previous order**, never dropped into "unactuated", and counted
   in `ordersRejected` — the starter's `directives.nim` repair-don't-reject discipline.
6. `say` (≤ 120 runes) and the accepted order list become replay chat records; `notes` (≤ 240 runes) is
   stored and echoed back **to that seat only** in the next turn's observation.
7. `turnSpacingMs = 8000` is a floor on the wall clock between consecutive **batch starts**, not a
   sleep on the critical path: the loop keeps stepping ticks while it waits.

Then, for each of the next `turnTicks` ticks, in this order — this is the whole physics of the game
and nothing else mutates the world:

1. `tick += 1`. Snapshot positions and hp; every rule below reads the snapshot, never a partially
   updated world.
2. **Choose one action per living soldier**, in ascending unit id, from its squad's current order via
   the squad controller (§Decisions → "The squad controller").
3. **Resolve attacks**, in ascending attacker id. An attack at offset `o` hits whoever occupies
   `pos + o` iff that soldier is alive and on the **other** army; an attack on an empty cell or on a
   friendly is *not registered* (upstream's rule) but still costs `attack_penalty`. A hit subtracts
   `Damage`. At hp ≤ 0 the victim dies **immediately**: removed from the grid, its cell freed for
   step 4, the attacker paid `kill_reward`, a `kill` event recorded. Overkill therefore depends on
   attacker order, which is why that order is pinned.
4. **Resolve moves**, in ascending unit id. A move to `pos + o` succeeds iff the destination is on the
   board and unoccupied **at the moment of application** (so a cell vacated in step 3 or by an earlier
   mover this tick is available); otherwise the soldier stays. `do_nothing` does nothing.
5. **Recover**: every living soldier gains `StepRecover`, capped at `HpMax`.
6. **Reward**: every soldier alive at the start of the tick gets `step_reward`; every attacker gets
   `attack_penalty`, plus `attack_opponent_reward` if the attack was registered against an enemy; every
   soldier that died this tick gets `dead_penalty`. Accumulated into `magentReward[army]`, **recorded,
   not scored** (see below).
7. Mix the tick into `gameHash` and append it to the replay's hash chain.
8. Evaluate the game-end conditions.

### Scoring formula and sign

Per game `g`, with `survivors[s][g]` the seat's living soldiers when that game ends:

```
outcome[s][g] = +1 if survivors[s][g] >  survivors[opp][g]
                 0 if equal
                -1 if less

score[s] = sum over g in {1,2} of ( 100 * outcome[s][g]
                                    + survivors[s][g] - survivors[opp][g] )
```

**Higher is better.** The formula is **exactly zero-sum** (`score[0] + score[1] == 0` always), which is
the idea's integrity requirement: no pair of seats can raise their joint total by cooperating. Range at
`mapSize 45`: `[-362, +362]`. The `100 ×` term makes winning the two games dominate; the survivor
differential is the tiebreak that rewards winning cleanly rather than by one soldier. `results.scores`
carries `score[s]`, `results.win` carries `score[s] > 0`, and **the league ranks by `scores`** (Elo
1000/32 from the head-to-head ordering).

MAgent's own per-soldier rewards are summed per seat into `results.magentReward` and shown on the
endcard, but do **not** enter the score: they are the port's fidelity evidence and a spectator readout,
and scoring off them would reward attack-spam over winning.

### End conditions and legal `results.reason` values

A **game** ends at the first of: **annihilation** (an army reaches 0 living soldiers at the end of a
tick; both at once is a draw) → `endRule = "wipe"`; or **tick cap** (`tick == maxTicks`), settled by
survivor count, equal counts a draw → `endRule = "tickCap"`; or the **wall-clock stop** below →
`endRule = "wallClock"`.

An **episode** ends when both games have ended, or when the wall-clock stop fires. `results.reason` is
the starter's closed enum, and the values are the ones ctf's own manifest already declares:

- **`complete`** — both games ended by `wipe` or `tickCap`. The healthy value.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (default **660 s**). The engine
  stops at the current tick, settles the games played so far by survivor count, and writes results and
  replay. **Declared acceptable** for SPEC §Definition of done check 4. The budget guard below exists so
  it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop. Caught; the episode is settled from the
  last completed tick, `results.stopDetail` names it (≤ 200 runes, rune-truncated), artifacts are still
  written. A defect: `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × turnBudgetMs > wallClockBudgetSeconds`, the LLM is switched off for every remaining turn
(both seats fall to `pincer`, microseconds per turn), the remaining ticks run at full speed, and the
episode still ends `complete`. A `budget_guard` record names the turn it fired.

A seat that never connects, disconnects, or fails every decision **does not end the episode** — its army
plays `pincer` and the episode runs to its natural end. Nothing a player container does can stop the
clock: the starter's `lobbyJoinTimeoutTicks` bounds the lobby and its strike rule stops a silent seat
from consuming the per-turn deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {line, pincer}` makes it a scripted seat. A seat that sets neither is `PLAYER_SCRIPTED=pincer`
(the starter's "anything unrecognised is the published default" rule in `baselines.nim`). A scripted
policy seated as a champion is a failure state.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/magent-battle/anthropic_api_key` — the
hive 2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` /
`LLM provider is unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container
only. No `USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/magent_battle_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join scar:
joins are slot-sequential and a first registration can land before the seat has an index) — the
registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"line"|"pincer"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at 64 runes, then acknowledge
frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3 close-frame race:
whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/magent/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

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
- `maxOutputTokens = 900` (not 400 — "cut off at max_tokens"). **No `output_config.effort`** when the
  model string contains `haiku` or `4-5`. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (outermost balanced
  `{…}`, fence-tolerant, tolerant of trailing prose) and `truncateRunes`/`sanitizeSay` kept unchanged.

### Cadence, batching, and the wall-clock arithmetic

One command turn every **20 ticks**; **15 turns per game, 30 per episode**. At each turn the server
builds **both** seats' request bodies and issues them as **one parallel batch** — never sequentially;
this is a simultaneous-decision game and serial calls would double the wall clock for nothing. At most
2 calls in flight, at most `2 × 30 × 2 = 120` calls per episode including retries.

```
attempt1Ms                          9.0 s
retryMs                             4.0 s
turnBudgetMs                       14.0 s   (monotonic deadline around the whole turn)
turnSpacingMs                       8.0 s   -> 2 seats x 60/8 = 15 req/min  (sidecar cap: 30)

30 turns x max(spacing 8 s, budget 14 s), absolute worst          = 420 s
   typical (haiku answers in ~3-4 s, so spacing dominates)        = 240 s
2 x 300 ticks, 162 soldiers, integer Nim, fastMode                =   4 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400; typical 15 s)   =  15 s   (cap: 100 s)
gameOverTicks holds + results + replay write (retried uploader)   =  20 s
                                                                  -------
typical total                                                     = 279 s   < 720 s
absolute worst case (420 + 4 + 100 + 20)                          = 544 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                           = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                             = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_magent_manifest.nim` asserts it. `fastMode: true` in
every variant, as in the starter's paintball variant: seats send no inputs (the server computes every
action), so the Sprite v1 Ready packet's dead-reckoning hazard cannot arise.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turnBudgetMs`, `lobbyJoinTimeoutTicks`,
mummy's socket timeouts on the serve thread (which runs independently of the game loop, so a 14 s LLM
stall cannot drop a connection or stall `/healthz`), the 660 s engine stop, and ctf's `gameOverTicks`
hold before exit — kept so `/healthz` and `/global` keep answering for a bounded grace after artifacts
are written (the lantern 0.1.3 `/global` ping scar).

On a seat's timeout or parse failure: **retry once** in the next batch; on the second failure that
seat's orders for that turn become the **`pincer`** scripted orders computed inside the game (the same
proc the `pincer` baseline uses — imported, never duplicated), and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard, disconnected}`.
`results.fallbackTurns[s]` counts them.

**No failure mode leaves a soldier unactuated.** The control layer always has a directive: this turn's,
else last turn's, else `pincer`'s. A seat that never connects is reported once to
`COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload — exactly
`{"message", "failed_policy_index"}`, nothing else.

### Per-seat observation: exactly what is visible and what is hidden

**Visible.** Everything about the seat's own army, and — this is the port's fog of war, and it is
MAgent's own `view_range` lifted to army scale — an enemy soldier is visible iff **some living friendly
soldier is within `CircleRange(6)` of it** (`dx² + dy² ≤ 36`). Enemy squads with no visible member are
reported as unseen, with the last turn they were seen.

**Hidden.** The positions and hp of unseen enemy soldiers; every enemy squad's *order*; the opponent's
`notes`; the opponent's real player name and policy name; the opponent's fallback and decision
statistics; the other game's result while a game is in progress. Nothing about the opponent's identity
ever reaches a prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `your_notes`)
into the replay's `directive` record so the replay explains every decision.

```json
{
  "you": "Alpha",
  "opponent": "Bravo",
  "game": 1, "of_games": 2, "your_side": "red",
  "turn": 7, "of": 15, "tick": 120, "turn_ticks": 20, "ticks_left": 180,
  "map": {"width": 45, "height": 45},
  "soldier": {"hp_max": 10.0, "damage": 2.0, "recover_per_tick": 0.1,
              "move_up_to": 2, "attack_reach": 1, "view_radius": 6},
  "your_army": {
    "alive": 63, "started": 81, "lost_last_turn": 4,
    "squads": [
      {"id": "A1", "alive": 9, "x": 12, "y": 30, "hp": 9.4, "order": "advance"},
      {"id": "A2", "alive": 7, "x": 14, "y": 28, "hp": 6.1, "order": "focus B5"}
    ]
  },
  "enemy": {
    "visible_soldiers": 22, "killed_last_turn": 6,
    "squads": [
      {"id": "B1", "seen": 6, "x": 30, "y": 28, "hp": 6.1, "last_seen_turn": 7},
      {"id": "B4", "seen": 0, "x": null, "y": null, "hp": null, "last_seen_turn": 4},
      {"id": "B7", "seen": 0, "x": null, "y": null, "hp": null, "last_seen_turn": null}
    ]
  },
  "score_now": 3,
  "your_notes": "wrapping their left with A7-A9; A2 healing behind the line"
}
```

Field rules: `x`/`y` are the integer centroid of the *living, visible* members (`sum div count`); `hp`
is their mean hp in upstream units to one decimal; `seen` is the count of currently-visible enemy
members; `last_seen_turn` is `null` if that squad has never been seen. `score_now` is the running
`survivors[you] − survivors[them]` in the current game. All nine squads of each side are always listed,
in id order, so the array shape never changes.

### Reply schema and per-field caps

```json
{
  "orders": [
    {"squad": "A1", "verb": "advance"},
    {"squad": "A2", "verb": "hold", "x": 22, "y": 30},
    {"squad": "A3", "verb": "focus", "target": "B5"},
    {"squad": "A4", "verb": "flank", "side": "left"},
    {"squad": "A5", "verb": "retreat"}
  ],
  "say": "wrap their left, A2 holds the gap",
  "notes": "A7-A9 going wide; pull A2 back if it drops under 5 hp"
}
```

| Field | Type | Cap / domain |
|---|---|---|
| `orders` | array | **≤ 9 entries**; entries beyond the 9th are dropped |
| `orders[].squad` | string | **≤ 2 runes**; one of this seat's nine ids (`A1`…`A9` / `B1`…`B9`); duplicates: last wins |
| `orders[].verb` | string | **≤ 8 runes**; enum `advance` \| `hold` \| `focus` \| `flank` \| `retreat`, lower-cased before matching |
| `orders[].x`, `.y` | integer | required iff `verb == "hold"`; clamped into `[0, mapSize)` (the starter's clamp-don't-reject rule) |
| `orders[].target` | string | required iff `verb == "focus"`; **≤ 2 runes**; must be an **enemy** squad id |
| `orders[].side` | string | required iff `verb == "flank"`; **≤ 5 runes**; enum `left` \| `right` |
| `say` | string | **≤ 120 runes** (`MaxSayRunes`) — spectator chatter, rendered in the feed |
| `notes` | string | **≤ 240 runes** (`MaxNoteRunes`) — private, echoed to this seat only next turn |
| whole reply | bytes | **≤ 8192** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded error
text — is truncated on RUNE boundaries** via the starter's `truncateRunes`/`runeSubStr`, never by byte
index. Byte truncation is what makes a replay that renders in a browser fail a strict UTF-8 parser;
`tests/test_magent_replay.nim` asserts it with 4-byte emoji sitting exactly on every cap.

Unknown top-level keys are ignored. A missing `orders` with a present `say` is a **usable** reply (every
squad keeps its order). A reply that is not a JSON object, or whose `orders` is not an array, is a parse
failure. An individual malformed order is **repaired to that squad's previous order**, not dropped —
`directives.nim`'s rule, kept.

### System prompt (fixed, identical for both champions)

```
You are the field commander of one army in a large-scale grid battle. You command NINE
SQUADS, not individual soldiers. Once every 20 simulation ticks you issue one order per
squad and a deterministic controller executes it.

RULES YOU ARE PLAYING UNDER
- The board is a 45x45 open grid. Your army starts on one side, the enemy on the other.
- Every soldier has 10 hp, deals 2 damage to ONE adjacent enemy per tick, moves up to 2
  cells per tick, and regains 0.1 hp per tick. A soldier can move OR attack, never both.
- A soldier that is not attacking is healing. Nine soldiers on one enemy kill it in one
  tick; one soldier on one enemy takes five ticks and takes damage back the whole time.
  Local numbers are everything.
- You see an enemy only when one of your own soldiers is within 6 cells of it. Squads
  reported with "seen": 0 are somewhere you cannot see.
- The winner is whoever has more soldiers standing at the end. Trading evenly is a draw.
- You will play this position twice, once from each side. Both halves count.

YOUR ORDERS, one per squad, executed every tick until you change them:
- {"squad":"A1","verb":"advance"}                 close on the nearest enemy, attack in reach
- {"squad":"A1","verb":"hold","x":22,"y":30}      march to that cell and stand, attack in reach
- {"squad":"A1","verb":"focus","target":"B5"}     close on enemy squad B5, attack its weakest
- {"squad":"A1","verb":"flank","side":"left"}     swing 8 cells wide, then close
- {"squad":"A1","verb":"retreat"}                 fall back toward your own edge and NEVER
                                                  attack, so every soldier heals

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the character {
and end with }. No prose, no markdown, no code fences.
{"orders":[{"squad":"A1","verb":"advance"}],"say":"<=120 chars","notes":"<=240 chars"}
Squads you do not mention keep their current order. "say" is shown to spectators.
"notes" comes back to you next turn and to nobody else.
```

### Champion #1 — `magent-battle-vanguard` (owner **daveey**), `PLAYER_PROMPT`

```
Win by concentration. Pick ONE wing at turn 1 and put at least six squads on it, ordered
"flank" to that side, and keep them together: a squad that arrives alone dies alone.
Leave at most two squads as a screen with "hold" on your own half, roughly level with
your starting line, so the enemy cannot walk through the middle unpunished; the last
squad is your reserve, kept two ranks behind the mass with "hold".
Once your mass is within about ten cells of enemy contact, switch every squad in it to
"focus" on the SAME enemy squad - the one with the highest "seen" count nearest your
mass - and keep focusing that id until it is gone, then move to the next nearest. Do not
spread focus across two ids at once; the whole point is that nine attackers kill a
soldier in one tick.
Send the reserve in only when your mass is already engaged, and send it to the same
target id. If a squad's mean hp drops below 4.0, order it "retreat" for exactly one turn
to heal, then bring it straight back with "focus" on whatever the mass is chewing.
Never order "advance" for more than one squad at a time - it scatters them.
```

### Champion #2 — `magent-battle-marshal` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Win by attrition. Healing is 0.1 hp per tick and a turn is 20 ticks, so a squad that
spends one turn out of contact comes back with 2 hp per soldier. That is a free soldier
for every five you pull out, and it is how you win a long fight.
Turn 1: order all nine squads "hold" on a straight line about six cells in front of your
own edge, spread evenly across the board in y, and make the enemy cross the open ground.
Do not advance into them.
Every turn, read your own squads first: any squad with mean hp below 5.5 gets "retreat"
this turn, no exceptions, and goes back to "hold" on the line when it is above 8.0.
Any squad reporting a visible enemy squad adjacent to it gets "focus" on that id.
Only when your total alive count is HIGHER than the count of enemies you can see, and no
squad of yours is retreating, do you push: order the three squads nearest the enemy mass
to "focus" the weakest visible enemy squad (lowest hp), keep the rest on "hold", and go
back to holding the moment your alive count stops climbing relative to theirs.
Use "flank" only to close a gap in your own line, never to go around.
```

### The squad controller (deterministic, shared by every policy)

`src/magent/control.nim` — the starter's directive→actuator-mask module, retargeted from pixel steering
to grid actions. Runs once per living soldier per tick. `T(u)` is the target cell; `attackOk` says
whether the soldier may strike. Ties everywhere break by the fixed offset order, then by ascending unit
id. **There is no randomness in the controller at all.**

| Order | `T(u)` | `attackOk` | Preference among adjacent enemies |
|---|---|---|---|
| `advance` | the nearest living enemy to `u` (squared Euclidean; ties by lowest enemy id) | yes | lowest hp |
| `hold x y` | `(x, y)` | yes | lowest hp |
| `focus S` | integer centroid of living squad `S`; if `S` is extinct, behave as `advance` | yes | members of `S` first, then lowest hp |
| `flank left` / `right` | enemy-army centroid displaced `dy = −8` / `+8`, clamped to the board; once `u` is within 6 cells of that point, `T(u)` becomes the enemy-army centroid | yes | lowest hp |
| `retreat` | `(ownBackX, u.y)` — red `x = 1`, blue `x = mapSize − 2` | **no** | — |

Given `T(u)` and `attackOk`:

1. If `attackOk` and a living enemy occupies one of the 8 attack offsets → emit the attack action
   toward the preferred enemy.
2. Else, among the 12 move offsets whose destination is on the board, choose the one minimising squared
   distance to `T(u)`; if that distance is not strictly less than the soldier's current squared distance
   to `T(u)`, emit `do_nothing`.
3. Occupancy is **not** consulted here — a blocked move simply fails at resolution step 4. That is
   upstream's behaviour and it is what makes a dense formation shuffle rather than teleport.

### Scripted baselines (both shipped as fillers; `pincer` is also the server-side fallback)

`src/magent/baselines.nim`, the starter's module retargeted. Both emit the **same** directive object an
LLM does, through the same validator, which is what makes the bounded-orders test meaningful.

**`line`** — `PLAYER_SCRIPTED=line`. Every squad gets `advance`, every turn, forever. Five lines, a real
opponent (a mass charge beats a badly-split commander), and the control against which "did the LLM do
anything?" is measured.

**`pincer`** — `PLAYER_SCRIPTED=pincer`, and the fallback. Each turn, in order:

1. Any squad with `alive > 0` and mean hp `< 4.0` → `retreat`.
2. Else, any squad with a visible enemy squad whose centroid is within 3 cells → `focus` that id
   (nearest; ties by lowest id).
3. Else, squads 1–3 → `flank left`; 4–6 → `advance`; 7–9 → `flank right`.
4. `say` and `notes` are empty.

Like the starter's `DefaultBaselineParams`, the three tunables (`retreatHp = 4.0`, `focusRadius = 3`,
`flankOffset = 8`) are a parameter object chosen by `tools/tune_baselines.nim`'s head-to-head sweep, not
guessed; `tools/ci/baseline_tuning.json` records the sweep's pick and `tests/test_magent_tuning.nim`
asserts the shipped defaults still equal it.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/magent/`. The fork is a rename sweep
(`ctf` → `magent`, `CTF_WIRE` → `MAGENT_WIRE`; a CI grep asserts no `ctf_`/`CTF_` identifier survives
outside comment history) plus the changes below. **The same modules compile twice**: natively into
`/bin/magent-battle` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the port lives in the
starter's language.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/magent/server.nim` | **fork**, four named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `gamesPlayed` loop, the `wallClockBudgetSeconds` stop |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/magent/` | **fork** (magic + game name only) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/magent/` | **fork**, retargeted not rewritten | the per-turn parallel batch, the two deadlines, `turnSpacingMs`, the budget guard, tolerant parsing, the rune caps, the repair-don't-reject rule, the fallback ladder |
| `src/ctf/sim_state.nim` → `src/magent/sim_state.nim` | **fork** | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/magent/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames`, the results JSON builder |
| `src/ctf/events.nim` → `src/magent/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/magent/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/magent/global.nim` | **fork**, three named edits below | the sprite/object pools, the soldier compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the rig compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/magent/sim_types.nim` | **fork** | `GameVersion` (starts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), the flatty wire types (field order sacred), `MaxSayRunes`/`MaxNoteRunes`/`MaxPromptRunes` |
| `src/ctf/sim_config.nim` → `src/magent/sim_config.nim` | **fork** | `GameConfig` lifecycle and `config.update` |
| `src/ctf.nim` → `src/magent_battle.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/magent_battle_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags (`ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`, `useMalloc`, `EXPORTED_RUNTIME_METHODS=HEAPU8`, the `EXPORTED_FUNCTIONS` list), the OffscreenCanvas Worker, the stage-note diagnostics, the `data-replay-loaded`/`data-replay-error` signalling |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/magent_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p` fix and the buildx/`--platform linux/amd64` handling |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/soldier_red.png`, `data/soldier_blue.png`, `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/atlas/*`, `client/art/lockerroom/{bg.jpg,red_*.webp,blue_*.webp}` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, fog-of-war raycasting
and the first-person PIP, spray cans, floor paint and the paint grid, the paint buff, King of the Hill
and `hillTicks`, the `resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the
barrage, med kits, shields, cardboard barriers, trenches, perks, handicaps, four-team free-for-all,
shouts-as-cog-speech, achievements, campaign mode, and **all of the pixel-space map machinery**:
`arena.nim`'s wall masks and pixel queries, `map_art.nim`, `mapgen_styles.nim`, `map_pool.nim`,
`tools/mapkit.nim`, `tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`,
`docs/pool-review.html`. The board here is a 45×45 integer grid with no obstacles; every one of those
is a config surface the MAgent rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `crew`, all green/yellow soldier art and `rig_real/`), since units are
drawn as baked chips (§Viewer → Art) and the 128 px rig is never used at 8 px per cell.

### New modules

- `src/magent/arena.nim` — the grid: `mapSize`, the two offset tables, the **transcription of upstream's
  `generate_map`**, the squad partition, cell↔index helpers, the occupancy grid. Pure integer; no pixie,
  no pixel queries.
- `src/magent/sim.nim` — the step loop of §The game: action selection, attacks, moves, recovery,
  rewards, `gameHash`, game-end evaluation. Imports and re-exports the sim modules, as the starter's
  does, so `import magent/sim` sees everything.
- `src/magent/units.nim` — the soldier arrays (`pos`, `hp`, `army`, `squad`, `alive`), visibility
  (`dx² + dy² ≤ 36` against living friendlies), squad centroids and mean hp.
- `src/magent/upstream.nim` — every ported constant, each with the upstream citation comment beside it,
  in exactly the style the starter uses for `config/moba.ini`-derived values. This is the one file
  `tests/test_magent_upstream.nim` regex-checks against `vendor/upstream/battle.py`.

### Integer arithmetic (the determinism pin)

**All new sim arithmetic is integer only.** `HpMax = 100`, `Damage = 20`, `StepRecover = 1` (hp in
**tenths**); rewards accumulate in **thousandths** (`step −5`, `dead −100`, `attack −100`,
`attackOpponent +200`, `kill +5000`) and are divided by 1000 only when written out. Distances are
squared-integer, centroids are `sum div count`, and there is no floating point anywhere in `sim.nim`,
`units.nim`, `arena.nim`, `control.nim` or `baselines.nim`. This is simultaneously *more* faithful than
upstream (its float `hp 10 / step_recover 0.1` drifts under accumulation, because `0.1` is not binary
exact, while tenths are exactly the intended semantics) and the precondition for the native ↔ wasm
hash chain below.

**The only randomness in `battle` is the seed, and it is used for nothing**: spawns are a pure function
of `mapSize`, the controller is deterministic, resolution order is by unit id. The seed is still
randomised in `src/magent_battle.nim` before `config.update` (the starter's rule), recorded in the
replay config and `results.seed`, and threaded to the sim RNG that the `battlefield` and `gather`
variants (§Out of scope) will need. Two episodes with the same seed and the same orders are
byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDMAG`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `num_agents`, `mapSize`, `maxTicks`, `maxGames`, `turnTicks`, every
   upstream constant, `players[].name`, `slots[]`), then the record stream — joins (name, slot, token),
   leaves, **per-turn order records** (the only inputs this game has), chat records
   (`register`/`directive`/`fallback`/`budget_guard`/`result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/magent_replay.nim` — which imports the **same**
   `src/magent/sim.nim` — through the pinned `emscripten/emsdk` + nimby container in
   `Dockerfile.replay-viewer`.
3. In the browser, `magent_load_replay` runs `parseReplayBytes` + `initReplayRuntime`; `magent_frame`
   re-steps the sim from the recorded orders and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens and surfaced
   as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order (appended after the starter's existing mixes so ordering
   stays stable): per soldier `(id, x, y, hp, alive)`; per army `(aliveCount, killsDealt,
   magentRewardMilli)`; per squad `(order kind, targetX, targetY, targetSquad)`; then `tick`,
   `gameIndex` and `redSlot`.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact cannot
   be re-derived from sim state, so the stop is written as one record applied by the *same proc* on
   record and on playback, and `tests/test_magent_replay.nim` runs the record→re-derive check for
   **every** end reason (`wipe`, `tickCap`, `wallClock`, `fault`), not just the healthy one
   (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 600 hashes + 60 order records + ~10 chat records ≈ **25 KB**. Everything else is re-derived.

### Documented divergences from upstream (mirrored into `vendor/PATCHES.md`)

1. **HP and rewards in integers** (tenths / thousandths) instead of floats. Semantics identical;
   determinism strictly better, and required by the hash chain.
2. **Resolution order pinned**: all attacks in ascending unit id, then all moves in ascending unit id,
   then recovery. MAgent's C++ engine resolves in an internal order that cannot be verified from the
   Python layer; a fixed order is required for a replay to be re-derivable.
3. **Who chooses the action changed, not what the actions are.** Per-unit RL policies are replaced by
   the squad controller under two commander seats — the idea's explicit "policy-per-army" seating. The
   21-action space, both `CircleRange` tables, damage, recovery, the no-friendly-fire rule and all five
   reward terms are upstream's.
4. **`maxTicks` 300 × `maxGames` 2 (battle) / 200 × 2 (skirmish)** instead of `max_cycles = 1000` in one
   game, to fit the 720 s budget and to neutralise the spawn asymmetry by swapping sides. Recorded in the
   replay config so a viewer can never mistake it for the upstream default.
5. `minimap_mode = False`, `extra_features = False` — upstream defaults, unchanged.

### Proving the port (the four fidelity gates)

- `vendor/upstream/battle.py` — **byte-pristine** copy of
  `Farama-Foundation/MAgent2:magent2/environments/battle/battle.py` at a pinned commit, never edited.
  `vendor/UPSTREAM.md` records the repo, commit hash, fetch URL and the file's sha256;
  `vendor/LICENSE-magent2` carries the upstream licence.
- `tests/test_magent_upstream.nim` — the **tripwire** (the moba/ctf embedded-constants pattern):
  regex-parse `vendor/upstream/battle.py` and assert byte-equality against every constant in
  `src/magent/upstream.nim` — `hp`, `speed`, `damage`, `step_recover`, `view_range`, `attack_range`,
  `KILL_REWARD`, `step_reward`, `dead_penalty`, `attack_penalty`, `attack_opponent_reward`,
  `default_map_size`, `max_cycles_default`, and the `init_num`/`side`/`gap` spawn arithmetic. A
  re-vendor that changes a number **fails tests** instead of silently desyncing the game.
- `tests/test_magent_spawn.nim` — a direct transcription of upstream's `generate_map` loop is run for
  `mapSize ∈ {12, 31, 45, 64}` and asserted equal, position for position, to `arena.nim`'s spawner;
  `mapSize 45` is asserted to yield exactly **81 and 81** and `mapSize 31` exactly **25 and 25**; and
  the two-column asymmetry is asserted to be *present* (so a future "tidy-up" that mirrors the spawn
  fails the gate loudly).
- `tests/test_magent_determinism.nim` — record an episode, re-simulate from the replay's seed and order
  records alone on a fresh sim, and assert identical final tick, winner, survivor counts and per-tick
  `gameHash`.

### The four named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with `turnTicks = 20` and two seats in the batch.
2. **Registration interception** — a player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration, **not** applied as a shout and **not** written to the replay chat stream; the server
   writes a redacted `register` record instead (policy label and kind, never the prompt). The starter's
   "hold an unappliable registration and re-read it when the slot lands" behaviour is kept verbatim.
   Any other chat text from a seat is dropped — commanders speak through `say`, seats do not shout.
3. **Side swap** — when `gamesPlayed` increments, the loop flips `redSlot`, archives
   `(ticks, endRule, survivors, kills)` into `gameLog`, and calls `resetToLobby()`.
4. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration, kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wallClock`, and written
   as the load-bearing stop record of point 5 above.

### The two named edits to `roster.nim`

1. **Aliases are army-anonymous.** `seatAlias(slot)` returns `IdentityNames[slot]` → `Alpha`, `Bravo`,
   independent of which side that seat holds in the current game; `squadAlias(slot, k)` returns
   `A1`…`A9` for slot 0 and `B1`…`B9` for slot 1. Sprite labels and the label manifest inherit the
   two-name-space rule with no further change, and `showPlayerLabels` is false.
2. **`squadResultsJson` → `armyResultsJson`** — one entry per seat, two entries in every seat-indexed
   array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a grid, not a pixel arena.** `buildSpriteProtocolPlayerUpdates` emits cell-space
   coordinates; the fov cache and shadowcasting are deleted (spectators see everything; the *commanders'*
   fog lives in the observation builder, not the renderer).
2. **Soldier chip pools.** New pools `UnitSpriteBase`/`UnitObjectBase` sized to `MaxUnits = 200`, filled
   in unit-id order and emitted incrementally like the starter's other object families.
3. **Baked battlefield.** `arena_floor.png` is tiled and darkened at map install with pixie, exactly the
   way the starter bakes endzone paint, plus a 1 px chalk border and faint 5-cell gridlines so the scale
   of the board reads with the HUD off.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI` in;
`COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI` out;
`COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST`/`PORT`; player sockets at
`/player?slot=<i>&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset route:
`GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering for
the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). Global
broadcasts are fire-and-forget so a slow viewer can never stall the episode.

### Results document (closed schema; `armyResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":        ["daveey", "daveey-1"],
  "aliases":      ["Alpha", "Bravo"],
  "scores":       [222, -222],
  "win":          [true, false],
  "winner":       0,
  "reason":       "complete",
  "games":        2,
  "gameWins":     [2, 0],
  "survivors":    [63, 12],
  "kills":        [150, 99],
  "finalTick":    287,
  "turnsPlayed":  28,
  "seed":         1734029581,
  "magentReward": [612.415, -238.09],
  "policyKinds":  ["llm", "scripted"],
  "llmTurns":     [28, 0],
  "fallbackTurns":[1, 0],
  "ordersRejected":[0, 0],
  "deadSeats":    [false, false],
  "gameResults": [
    {"game": 1, "redSlot": 0, "survivors": [41, 0],  "kills": [81, 40], "ticks": 287, "endRule": "wipe"},
    {"game": 2, "redSlot": 1, "survivors": [22, 12], "kills": [69, 59], "ticks": 300, "endRule": "tickCap"}
  ],
  "stopDetail": ""
}
```

`winner` is `0`, `1` or `null` (draw). `survivors`/`kills` are summed over the two games; the per-game
split is in `gameResults`. Adding a key means updating `armyResultsJson`, the manifest's
`results_schema` and `tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld schemas
are closed and undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDMAG`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker),
  retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"magent-battle/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "policyKinds":[…],"games":2,"tickCount":…,"directives":[…],"fallbacks":N,"results":{…}}` — by
  brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md` documents
  for prod forensics) and decoding the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.kills[0]' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "magent-battle/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.kills` non-zero on both sides, and the champion seats' directives with
  `source == "llm"`, non-empty `say`/orders and real verbs — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDMAG`, format version, `gameName` `magent-battle`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `mapSize`, `maxTicks`, `maxGames`, `turnTicks`, every upstream constant, `players[].name` (real names), `slots[]`, `fastMode` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| orders | per turn, per seat: the nine accepted squad orders — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `game`, `turn`, `slot`, `alias`, `side`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `say` (≤ 120 runes), `orders`:[{`squad`,`verb`,`arg`}], `view` (the observation minus `your_notes`) |
| `fallback` | `game`, `turn`, `slot`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of nine kinds:**

`turn` `{n, game}`; `order` `{slot, squad, verb, arg}`; `say` `{slot, text}`;
`fallback` `{slot, cause}`; `firstblood` `{slot, unit, victim}`; `kill` `{a, v, cell}`;
`rout` `{army, lost}` (an army lost ≥ 10 soldiers since the previous turn); `wipe` `{army}`;
`end` `{reason, winner, survivors}`.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`firstblood`,
`rout`, `wipe`, `fallback`, `end`.** `kill`, `turn`, `order` and `say` drive the feed, not the scrubber
(40+ kill markers would make it unreadable).

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `Attack, Kill, Rout, Wipe, TurnStart, Directive, Fallback, PhaseChange` and
the mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already carries
the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx/`--platform linux/amd64` handling. It
stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No `/client/replay` live-server
viewer is ever declared to the platform; the game still serves `/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/magent_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
which is now simply the repo's own starter. Never a mixture. Splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the
viewer silently (cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one piece:
the Worker sets `Module.onRuntimeInitialized`, the module is emitted **non-modularized** as
`magent_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang` through `emcc`,
`--mm:arc --exceptions:goto -d:useMalloc -d:release`, `-O2`, `-s ALLOW_MEMORY_GROWTH`,
**`-s ABORTING_MALLOC=1`** (non-negotiable: wasm32 has no memory protection, so a failed malloc would
otherwise write through nil into address 0 and corrupt the module's own globals),
`-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_magent_load_replay,_magent_frame,_magent_input,
_magent_packet_ptr,_magent_packet_len,_magent_mismatch_tick,_magent_error_ptr,_magent_error_len,
_magent_stage_ptr,_magent_stage_len`; and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './magent_replay.js')` in that order.

`magent_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress buffer
that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `magent_load_replay` re-simulates the whole episode once headlessly
  (600 ticks × 162 soldiers of integer work — measured in single-digit milliseconds in wasm), records the
  per-tick alive counts, the lull spans and the beat ticks, then resets and renders frame 0. That is what
  lets the unit-count sparkline and the scrubber beats draw at **full width on the first frame** instead
  of growing in.
- `magent_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch — posted by the Worker only *after*
`ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute means "a
frame is on the canvas", not "a file was fetched". On failure it sets **`data-replay-error`** on `<html>`
with the message, in `showFailure()`. Both are coworld-ctf's own signals, inherited unchanged — this fork
adds neither and removes neither. The `coworld-replay` postMessage bridge's `ready` is posted **from a
callback fired after** `data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus
`3c11c953`, 2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte.** Not edited, not reformatted;
  `tests/test_magent_viewer.nim` pins its sha256 against the starter's file. Everything this game adds
  lives in the appended game block. Its `markBeat`/`renderBeatMarkers`/`ingestBeats` remain;
  `ingestBeats` ignores kinds it does not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`, transport,
  endcard, locker-room loader, `?embed=1` mode and `.tiny` density system are untouched; the appended
  block replaces only the *contents* of the scorebug plates, adds the heat toggle and the front-line
  layer, and retargets the feed rows, the beat rendering, the momentum series and the endcard columns. A
  test asserts the starter's byte prefix is intact up to the documented splice marker and that the file
  only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text by
  `tests/test_magent_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  `pushFeed` **including its signature** (the cogball 0.1.4 latch scar: a signature drift threw
  mid-replay and latched `static_replay.js` into `failed`), the beat and lull machinery, the endcard
  builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` → `window.MAGENT_WIRE`
  rename emitted by `tools/gen_wire_constants.nim`. Deleted: every ctf-specific draw call and the FPV
  pipeline. Added: `drawBattlefield`, `drawHeat`, `drawFrontLine`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `attachMinimap(...)` call. **Zoom decision: dropped.**
    The board is a fixed 45 × 45 grid with a 1 : 1 aspect and no off-frame area; `relayout()` fits it
    whole at every width, and at the 360 px embed each cell is 8 px (see "Legible at 360 px"), so per the
    pin a fixed arena drops `#viewpanel` entirely. `broadcast_core.js` tolerates a missing minimap
    (`pendingMinimap` stays null).
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — there is no per-soldier
    point of view worth showing; the whole board is the shot.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.steal`, `.beat-marker.return`, `.beat-marker.capture`, `.beat-marker.hillflip`
    and `.beat-marker.hillhold` CSS rules — those kinds are never emitted here.
  - The perk and handicap badges.
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom`, `#chrome`,
    `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#bannerlane`,
    `#killfeed`, `#mmwarn`, **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`,
    `#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#ffwd-mini`,
    `#win-chip`, `#tick-clock`, `#speedchips`), `#scrub` with `#momentum`/`#scrub-fill`/`#lulls`/
    `#scrub-win`/`#scrub-head`, `#endcard` with `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/
    `#ec-replay`, and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here and
enforced by a test:

| Starter string (file:where) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` | `<span>Commander</span><span>Kills</span><span>Lost</span><span>Alive</span><span>Reward</span>` |
| `<span class="fl-cap">Lives left</span>` (endcard team block) | `<span class="fl-cap">Troops left</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (scrub graph) | `<span class="momentum-label">TROOPS LEAD</span>` |
| `<span class="lives-label">Lives</span>` (scorebug plate) | `<span class="alive-label">Alive</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (locker room) | "Forming up on the line…" |
| `#clock-caption` "In the locker room" | "Mustering" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" | "Replay hash mismatch at tick N — showing recorded orders" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline" | "kills / routs / winner on the timeline" |
| `#lockerroom` `aria-label` "Loading replay" | unchanged (generic) |
| team words `RED`/`BLUE` in `ec-tname`/plates | the seat's **alias** (`ALPHA`/`BRAVO`) plus a small `red`/`blue` side chip, because the sides swap between games |

**`tests/test_magent_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `spray`, `grenade`, `med kit` — outside comment blocks, and asserts **zero** matches; and
asserts each replacement string above is present exactly once. A rename that reintroduces paintbot
vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged. **No overlay sits in the transport band**: the board is laid out between the two
bands and every addition here (the heat overlay, the front line, the feed, the banners, the heat toggle)
is positioned inside the board region or in the top band. The **endcard stops at `var(--band)`**
(`#endcard { bottom: var(--band, 0px) }`, the starter's rule, kept) so the scrubber stays clickable
underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `battleBeat(tick, kind, side, label)` — named so it can never shadow
`chrome_common.js`'s `markBeat` alias, the tandem 2026-08-23 hoisting trap — appends
`<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind emitted and no others**: `.beat-marker.firstblood`, `.beat-marker.rout`,
`.beat-marker.wipe`, `.beat-marker.fallback`, `.beat-marker.end`. The game block never calls `markBeat`,
so an unlabelled div marker cannot appear.

**Playback rate: 1 tick per animation frame at 30 fps** (speed chips `[0.5, 1, 2, 4, 8]`, default 1).
A 600-tick episode therefore plays for **20 s**, which is what lets `viewer_smoke.mjs --soak 10` observe
real advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar).

### Readouts

1. **The battlefield** — the grid drawn edge to edge: each living soldier is a baked team chip (see Art),
   hp shown as chip brightness plus a 1 px pip; a soldier that dies flashes white and fades over 6
   frames, leaving a scorch mark for 60 frames so the shape of the fight persists.
2. **Army heatmaps** (the idea's first ask) — a translucent density overlay, 9 × 9 bins of 5 × 5 cells,
   red and blue additively blended, redrawn every frame. On by default, toggled by a labelled `HEAT`
   chip in the **top** band, never in the transport band.
3. **Front line** (the idea's second ask) — a chalk polyline: for each row `y`, the midpoint between the
   rightmost living red soldier and the leftmost living blue soldier within rows `y ± 2`; rows where one
   side is absent leave a gap, so a broken line literally shows a broken front. A 3-frame trail makes a
   collapse read as motion.
4. **Unit-count sparkline** (the idea's third ask) — the starter's `#momentum` SVG retargeted to two
   series over the whole episode, red alive and blue alive, with the playhead marked, the game boundary
   ruled, and the `rout`/`wipe` ticks flagged. Filled from the load-time pre-scan, so it draws at full
   width on the first frame.
5. **Scorebug plates** — two plates: the seat's **real policy name** (spectator side only), its in-game
   alias (`ALPHA` / `BRAVO`), a small side chip showing which colour it holds this game, the **alive
   count** as the big numeral and kills as the small one, and a `↯` glyph on any seat that has taken a
   fallback.
6. **Clock** — `#clock-time` shows `game 1/2 · turn 7/15`, `#clock-caption` shows
   `tick 120/300 · 63 v 71`.
7. **Match feed** (`#killfeed`) — plain language, never internal notation: `ALPHA A3 → focus BRAVO B5`,
   `BRAVO B7 falls back to heal`, **`FIRST BLOOD — ALPHA`**,
   **`BRAVO'S RIGHT WING IS ROUTED — 14 DOWN`**, **`BRAVO IS WIPED OUT`**,
   `Alpha: "wrap their left, A2 holds the gap"`, and
   `BRAVO MISSED THE CALL — scripted orders (timeout)`. The commander `say` lines and the order lines are
   where a spectator sees the LLM playing.
8. **Endcard** — `ALPHA TAKES THE PAIR 2–0 — 63 SURVIVORS TO 12`, the two-seat table under the re-mapped
   header (`Commander | Kills | Lost | Alive | Reward`), a row per game with its `endRule`, and
   `SCORE +222 / −222`. It stops at `var(--band)` and any seek dismisses it.
9. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull = 40
   consecutive ticks with no `kill` event, from the pre-scan), spoilers switch, tick readout, speed
   chips, the scrubber with the five beat buttons, and `#mmwarn` on a hash mismatch — all the starter's,
   verbatim.

### Art

**Real art, from the starter's shipped assets — no placeholders, no solid-colour squares, no downloads.**
The battlefield floor is `data/arena_floor.png`, tiled and darkened 18 % with faint 5-cell gridlines,
baked once at map install by pixie (the way the starter bakes endzone paint). Soldiers are **baked at
load** by `rig_art.nim`'s compositor from `data/soldier_red.png` and `data/soldier_blue.png`: each sprite
is rendered once into three chip sizes (6, 10 and 16 px) with a 1 px team rim and three hp-brightness
variants — 18 pre-baked chips — so drawing 162 soldiers a frame is 162 blits, never a per-soldier
rasterisation. The loading screen is the starter's locker room (`client/art/lockerroom/bg.jpg` plus the
red/blue cog webps) with the caption re-labelled. Text is `data/font.ttf`. Scorch marks and the
front-line chalk are procedural, in the floor bake's palette.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim. At 360 px the 45 × 45 board renders at 360 px square: **8 px per cell**, a 6 px chip with a
1 px rim and a 1 px gutter — legible, and the whole board is in frame, which is why `#viewpanel` is
dropped. Three rules are added and asserted by `tests/test_magent_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps only `alias + name + alive count`; the kills numeral is hidden.
3. Under `.tiny`, the heat overlay drops to 5 × 5 bins and the front line draws 2 px wide.

---

## Packaging

- **Repo**: `Metta-AI/cogame-magent-battle`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `magent-battle`; **`game.name` is
  `magent-battle`** (hyphenated, matching the slug) so the secret namespace
  `secret://coworld/magent-battle/anthropic_api_key`, the page slug, the `POST /coworld-league-seeds`
  body and the docs all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, underscored, because the manifest image placeholder is derived
  from the compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two
  services/two images; this fork uses the one-image / two-entrypoints shape because the shared
  `docker_smoke.sh` and `policies.json` assume a single image (the knights-archers precedent):

  ```yaml
  services:
    magent_battle:
      image: coworld-magent-battle:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{MAGENT_BATTLE_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:magent-battle src/magent_battle.nim`
  → `/bin/magent-battle`, and the same for `src/magent_battle_player.nim` → `/bin/magent-battle-player`.
  The runtime stage copies both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/magent-battle"]`,
  runtime `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk`, pinned nimby with
  its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block) with the asset
  list swapped to `data/{soldier_red,soldier_blue,arena_floor}.png`, `data/font.ttf`, `data/ascii.png`,
  `client/art/lockerroom/*`, `magent_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`,
  `chrome_common.js`, `static_replay.js`, `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["magent", "battle", "port", "multiagent"]` (≥ 3; `game.tags` must
    **not** exist — pistonball 0.1.0); **`episode_timeout_minutes: 20` at the top level**, not under
    `game`.
  - `game.name = "magent-battle"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/magent-battle"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/magent-battle/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`** (`tokens`
    2/2, `players` 2/2, `slots` 0/2 — the tandem 0.1.0 scar). `tokens` is described as runner-injected;
    **no `game_config` anywhere in this manifest contains a literal `tokens` array** (matriculate rejects
    "game_config must not include runner-managed tokens" — knights-archers 0.1.0), while `config_schema`
    keeps *requiring* it because the runner injects it. Properties: `tokens`, `players`, `slots`, `seed`,
    `mapSize` (enum `[31, 45]`, default 45), `maxTicks`, `maxGames`, `turnTicks`, `turnBudgetMs`,
    `turnSpacingMs`, `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `gameOverTicks`, `minPlayers`,
    `fastMode`, `showPlayerLabels`, and `num_agents` (integer, `minimum: 2`, `maximum: 2`, default 2).
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}` — the starter's own enum.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-magent-battle/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"porting.md","title":"Porting MAgent battle","content":{"type":"uri","value":".../docs/PORTING-MAGENT.md"}}]}`.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must be
    at least `"1"`** (pistonball 0.1.1). Two entries, `line` and `pincer`, so **every declared player
    occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 2` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "battle", "name": "Battle (45x45, 81 v 81)",
     "description": "MAgent battle_v4 at upstream scale: two armies of 81 on a 45x45 open grid, one commander per army, two games with the sides swapped, 15 command turns each.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}],
                     "slots": [{"team": "red"}, {"team": "blue"}],
                     "num_agents": 2, "minPlayers": 2,
                     "mapSize": 45, "maxTicks": 300, "maxGames": 2, "turnTicks": 20,
                     "turnBudgetMs": 14000, "turnSpacingMs": 8000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "skirmish", "name": "Skirmish (31x31, 25 v 25)",
     "description": "The same rules on a 31x31 grid with 25 soldiers per army and 10 command turns a game - a faster ladder round with the identical nine-squad command surface.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}],
                     "slots": [{"team": "red"}, {"team": "blue"}],
                     "num_agents": 2, "minPlayers": 2,
                     "mapSize": 31, "maxTicks": 200, "maxGames": 2, "turnTicks": 20,
                     "turnBudgetMs": 14000, "turnSpacingMs": 8000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  (`mapSize = 31` yields 25 soldiers per army from upstream's own `generate_map` arithmetic:
  `init_num = 38.44`, `side = 12`, left block 5 columns × 5 rows after the `0 < x` filter, right block
  truncated to match. `tests/test_magent_spawn.nim` asserts the number rather than trusting this
  paragraph — and it asserts it for **every** variant's `game_config`, not just the fixture's, because a
  config-scaled construct that fits the small fixture and breaks the big variant is exactly the
  collab-cooking 0.1.1 failure.)

  **Certification fixture** — `num_agents: 2` again, inside `certification.game_config`, and exactly two
  players so that `len(certification.players) == len(game_config.players) == num_agents == SMOKE_SEATS
  == 2` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks):

  ```json
  "certification": {
    "players": [{"player_id": "pincer"}, {"player_id": "line"}],
    "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}],
                    "slots": [{"team": "red"}, {"team": "blue"}],
                    "num_agents": 2, "minPlayers": 2, "seed": 42,
                    "mapSize": 31, "maxTicks": 300, "maxGames": 2, "turnTicks": 20,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  600 ticks of scripted play is ~2 s of sim, but the replay is 600 ticks ⇒ **20 s of playback**, which the
  viewer soak needs. The certify step in `coworld-release.yml` passes **`--timeout-seconds 300`** (the
  default 60 covers start + connect grace + play + linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/magent-battle-player"`:

  ```json
  [{"name":"magent-battle-vanguard","run":"/bin/magent-battle-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>"}},
   {"name":"magent-battle-marshal","run":"/bin/magent-battle-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"magent-battle-line","run":"/bin/magent-battle-player","env":{"PLAYER_SCRIPTED":"line"}},
   {"name":"magent-battle-pincer","run":"/bin/magent-battle-player","env":{"PLAYER_SCRIPTED":"pincer"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1, uploaded
  while daveey-1 is the active player); the fillers are `line` and `pincer`, and their versions must
  differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps the
  template's nimby/Nim toolchain and runs the four shards, and the `docker-smoke` and `wasm-viewer` jobs
  are taken **unchanged** with `<slug>` → `magent-battle`, `<IMAGE>` → `coworld-magent-battle`,
  `<SEATS>` → `2`, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server). `coworld-release.yml` and
  `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on the certify step.
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed **executable** (mode
  100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_magent_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and as four shard binaries in `ci.yml`'s `test` job.
`tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_magent_sim.nim`)
1. `attack only hits enemies` — an attack on an empty cell and on a friendly both deal 0 damage and both
   still charge `attack_penalty`; only the enemy case pays `attack_opponent_reward`.
2. `damage and death` — five attacks kill a full-hp soldier; the fifth attacker (and only it) gets
   `kill_reward`; the victim gets `dead_penalty` exactly once and vanishes from the occupancy grid.
3. `overkill order` — two attackers on a soldier one hit from death: the lower unit id takes the kill,
   the higher one's attack is unregistered.
4. `recover caps` — hp climbs 1 per tick and stops at `HpMax`; the dead never recover.
5. `move blocked` — a move into an occupied cell fails and the soldier stays; a move into a cell vacated
   earlier in the same tick succeeds; a move off the board fails.
6. `offset tables` — the 12 move offsets are exactly `dx²+dy² ≤ 4` minus the centre, the 8 attack offsets
   exactly `dx²+dy² ≤ 2.25` minus the centre, in the pinned order; the action space is 21.
7. `visibility` — an enemy at `dx²+dy² == 36` is visible, at 37 is not; visibility unions over living
   friendlies only.
8. `controller orders` — one case per verb asserting the target cell and the attack permission, including
   `focus` on an extinct squad degrading to `advance` and `retreat` never attacking.
9. `scoring is zero-sum` — over 500 randomised two-game end states, `scores[0] + scores[1] == 0`, the sign
   is right, and a 1–1 split with an equal survivor differential is a draw.
10. `end conditions` — annihilation, mutual annihilation, tick cap and the wall-clock stop each produce
    the right `endRule`, `winner` and `survivors`, and the right episode `reason`.
11. `no floating point in the sim` — a source grep over `src/magent/{sim,units,arena,control,baselines}.nim`
    finds no `float`, `/`, `sqrt` or float literal (the integer-determinism pin, mechanically enforced).
12. `tick budget` — 2 × 300 ticks of a full 45 × 45 episode complete in < 4 s in a release build.

**Port fidelity** — `tests/test_magent_upstream.nim` (the regex tripwire over `vendor/upstream/battle.py`),
`tests/test_magent_spawn.nim` (spawn positions, the 81/81 and 25/25 counts, and the preserved two-column
asymmetry), `tests/test_magent_determinism.nim` (re-simulate from the replay; identical tick, winner,
survivors and per-tick `gameHash`). Described in §Sim module; these are the permanent gates a re-vendor
cannot silently pass.

**Bounded orders / legality on the scripted baselines** (`tests/test_magent_control.nim`)
13. `baselines are bounded` — for 200 pseudo-random world states (varying alive counts, extinct squads, hp
    distributions, both map sizes, both sides) and for **both** `line` and `pincer`: the returned order
    list has **≤ 9 entries**, every `squad` is one of the seat's own nine ids with no duplicates, every
    `verb` is in the enum, every `hold` coordinate is on the board, every `focus` target is an **enemy**
    id that exists, every `flank` side is `left|right`, and the serialised directive is ≤ 2048 bytes. A
    baseline that ever proposes an illegal or unbounded order fails the build.
14. `fallback is the pincer proc` — the decision engine's fallback path and the `pincer` baseline resolve
    to the same proc, so they cannot drift.
15. `reply validation` — the validator accepts the schema, **repairs** an individually invalid order to the
    squad's previous order while keeping the rest, rejects a non-object and a non-array `orders`, truncates
    `say`/`notes` on **rune** boundaries at 120/240 with 4-byte emoji sitting on the boundary, caps the
    read at 8192 bytes, and never leaves a squad unactuated.
16. `baseline tuning is the swept pick` — the shipped `retreatHp`/`focusRadius`/`flankOffset` equal
    `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern; `ci.yml` re-runs the sweep with
    `--check`).

**End-to-end episode writing a replay** (`tests/test_magent_engine.nim`)
17. `episode writes artifacts` — run a real two-seat, two-game episode (`mapSize 31`, `maxTicks 100`, both
    seats scripted, no API key so the LLM client is `disabled`) against a temp-dir `COGAME_*` URI set;
    assert `results.json` and the `.replay` are written, `reason == "complete"`, `scores` sum to 0, both
    games appear in `gameResults` with opposite `redSlot`, and the results key set equals the manifest's
    `results_schema` key set **exactly**.
18. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at all,
    both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure payload.
19. `budget guard settles early` — with the guard forced, the episode finishes `complete`, not `deadline`,
    and a `budget_guard` record names the turn.

**Replay** (`tests/test_magent_replay.nim`)
20. `record then re-derive, every end reason` — for `wipe`, `tickCap`, `wallClock` **and** `fault`, record
    an episode and re-derive it from the bytes; assert identical hashes at every tick including the stop
    tick (the particle-worlds scar: a wall-clock stop applied outside the stepping proc hash-mismatches at
    the stop tick on every slow-LLM episode).
21. `replay is self-sufficient` — the bytes alone yield seat names, aliases, policy kinds, the full config,
    the seed, every order record, every chat record and the result.
22. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every capped
    field is filled to exactly its cap with 4-byte emoji; assert the output parses under a **strict** UTF-8
    JSON parser, contains no lone surrogates, and reports `protocol == "magent-battle/v1"`.
23. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`, kept.

**Manifest** (`tests/test_magent_manifest.nim`)
24. `manifest pins` — `num_agents == 2` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens` in any
    `game_config`; `len(player) == 2` and every declared player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 2`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 660`; **and every variant's
    `game_config` actually constructs a valid `GameConfig` and spawns the right army size**.
25. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no top-level
    `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` — the
    collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_magent_viewer.nim`, static assertions in the `test` job)
26. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals the starter's, pinned as
    a literal.
27. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the documented
    splice marker and only appends after it; `broadcast_core.js`'s kept procs are byte-identical to the
    starter's, `pushFeed`'s signature included.
28. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap); the beat builder is `battleBeat`, never
    `markBeat`.
29. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{firstblood, rout, wipe, fallback, end}`.
30. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band; the
    three 360 px rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`, `#fpv*`, `#povBadge`,
    …) appear nowhere.
31. `endcard labels` — `tests/test_magent_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
32. `label manifest` — the starter's `test_label_contract` pattern: the emitted sprite-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.

**Viewer smoke — the bundle is EXECUTED, not merely built**
33. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced** (downloaded as
    the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both the npm module and
    the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays on.
34. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `say` at all**, so the
    smoke replay can never exercise the feed's text path (the cogchemists 2026-08-24 scar). The fixture
    **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only the wasm entry
    — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) — driving the real page
    with a full-cap 120-rune `say` on both seats at several canvas widths including 360 px.
35. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm module
    against the committed fixtures, kept: wasm32-only failures (integer traps, address-space exhaustion)
    are invisible to the native shards.

---

## Out of scope (v1)

- **The other four MAgent scenarios.** `battlefield` (battle plus obstacles — the closest follow-up: an
  obstacle mask in `arena.nim`, an obstacle layer in the replay config, and a pathing tweak in the
  controller), `gather` (food resources and a mixed-motive score, which breaks the zero-sum integrity claim
  and needs a different formula), `tiger_deer` (two agent types with a pairing kill rule and asymmetric
  seats), and `adversarial_pursuit` (asymmetric predator/prey seats). v1 ships **`battle` only**.
- **N-squad seating.** The idea's second option (one policy per squad, 18 seats) is not shipped:
  `num_agents` is fixed at 2 in every variant. Adding it later means a new variant with `num_agents: 18`
  and a per-squad observation, not a change to these rules.
- **Per-unit RL policies and pretrained MAgent weights.** No weights are vendored, no inference module
  ships, and no seat receives the 13 × 13 × 5 observation tensor. That is why the port's gates are the four
  in §Sim module rather than an obs-byte fidelity comparison — there is no trained policy whose bytes must
  be protected.
- **Army sizes above 81 per side.** The idea mentions up to 1000; upstream's own default is 81 per side at
  `map_size 45`, it is what stays legible at 360 px, and it is what fits the wall-clock budget. Larger
  armies are a `mapSize` variant, not a v1 feature.
- **Anything per-soldier from the LLM.** Commanders issue nine squad orders; they never name a soldier, a
  cell-by-cell path or a raw action index.
- **Live spectating.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, fog-of-war rendering, the first-person
  PIP, paint, hills, hearts, grenades, med kits, shields, barriers, perks, handicaps, four-team play,
  achievements, campaign mode, the procedural map generator, the map pool, the map editor and mapkit — all
  deleted, not disabled (§Sim module), and none of them return in v1.
- **Terrain, elevation, ranged units, morale, reinforcements, supply** — none exist upstream in `battle`
  and none are invented here.
- **`minimap_mode` and `extra_features` observations.** Upstream defaults (`False`/`False`) are kept; the
  commander's fog-of-war summary replaces them.
