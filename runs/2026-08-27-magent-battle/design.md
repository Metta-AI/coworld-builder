# cogame-magent-battle — design note (2026-08-27)

**Starter: `Metta-AI/cogame-moba`** (read at `/workspace/starters/cogame-moba`), chosen because this
is a **bit-faithful port of an existing external RL environment** — MAgent's `battle` scenario —
and cogame-moba plus its `docs/PORTING.md` is the platform's port lineage: vendored upstream at a
pinned commit, a patch/tripwire discipline over it, a Python game server implementing the Coworld
contract (`server/cogame_moba/{config,defaults,engine,server,replay,uris}.py`), a deterministic
replay that a static browser viewer re-derives, and a closed results schema. **Every convention
there holds here unless this note says otherwise.** The two places this note says otherwise are
called out explicitly and justified: the **sim is integer Python/NumPy rather than vendored C
compiled to wasm** (§Sim module), and the **entire replay-viewer stack comes from one other
starter, `Metta-AI/coworld-ctf`** (§Viewer) — because cogame-moba ships no `client/` directory, no
`chrome_common.js`, no `static_replay*.js` and no `replay-viewer/` at all; its `viewer/index.html`
(read in full) is a bespoke raylib page with no transport band, no scrubber beats and no
`data-replay-loaded` signal, so it cannot satisfy the chrome and transport pins. All four viewer
files therefore come from coworld-ctf, one starter, never a mixture.

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

The rules being reproduced are **MAgent2's `battle_v4`**
(`Farama-Foundation/MAgent2`, `magent2/environments/battle/battle.py`), fetched and read in full
while writing this note. Every constant below is quoted from that file; §Sim module records how the
build pins it and how CI proves the port has not drifted from it.

| Upstream fact | Value |
|---|---|
| `default_map_size` | 45 (square) |
| Agents | 162 total — `red_[0-80]` and `blue_[0-80]`, i.e. **81 per army** |
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

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | Where |
|---|---|
| Starter by game shape | `cogame-moba` — external-env port (title paragraph, §Sim module) |
| Public `Metta-AI/cogame-magent-battle` | §Packaging |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=line|pincer`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance; ctf soldier art + arena floor) |
| Two name spaces | §The game (aliases `Alpha`/`Bravo` in-game; real names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (budget arithmetic: ≤ 553 s worst case, 660 s hard stop) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 2`, three times |
| Simultaneous decisions issued as one parallel batch | §Decisions |
| Replay bytes self-sufficient, strict UTF-8 JSON | §Server, player, protocol |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |

---

## The game

Two armies of infantry meet on an open 45×45 grid. Each army is 81 identical units with 10 hp that
regenerate slowly, that move up to two cells a turn or strike an adjacent enemy for 2 damage. Nobody
plays a unit. Each of the **two seats is an army commander**: once every 20 sim steps it issues one
order to each of its **nine squads**, and a deterministic squad controller turns those orders into
the MAgent actions its units actually take. The commander sees only what its own units can see. The
army with more soldiers standing at the end wins.

### Seats, armies, squads, aliases

- **`num_agents` = 2.** Exactly two seats, always, in every variant and in the certification
  fixture. Seat 0 commands the **red** army (spawned on the left), seat 1 the **blue** army (right).
  This is the idea's "2 armies (policy-per-army)" option; the N-squads seating is §Out of scope.
- **Two name spaces.** In-game, seat 0 is **`Alpha`** and seat 1 is **`Bravo`**. Those aliases are
  the only names that ever appear in an observation, in a prompt, in an order or in a `say`. The
  seats' **real policy/player names** (`daveey`, `daveey-1`, `Baseline (1)`) live only in
  `results.names` and in the replay's `seats[].name`, and only the viewer renders them. A commander
  can never learn who it is playing, which is what makes the zero-sum integrity claim hold.
- **Squads.** Each army is partitioned into **exactly 9 squads**, ids `A1`…`A9` (Alpha) and
  `B1`…`B9` (Bravo), in every variant. Assignment is by initial position: the army's spawn list is
  sorted by **distance from its own back edge** (red: ascending `x`; blue: descending `x`), ties by
  ascending `y`, then split into 9 contiguous blocks as equal as possible. At `map_size = 45` the
  spawn block is 9 columns × 9 rows, so squad `k` is exactly the `k`-th column: **`A1`/`B1` is the
  rearmost rank, `A9`/`B9` the front rank.** At `map_size = 31` the 25 units split
  `3,3,3,3,3,3,3,2,2`. Squad membership is fixed at spawn and never reassigned; a squad whose units
  are all dead is `alive: 0` and its orders are ignored.

### The grid, the units, the clock

- Board: `map_size × map_size` cells, no obstacles (this is `battle`, not `battlefield`; upstream
  `battle` has none either). Cells outside the board read as "obstacle/off-map".
- Unit: `hp` in **tenths** (`hp_max = 100` ≡ 10.0 hp), `damage = 20` ≡ 2.0, `step_recover = 1` ≡ 0.1
  per step, capped at `hp_max`. One unit per cell. Dead units are removed from the grid immediately.
- **Move offsets** (12, `CircleRange(2)` = `dx² + dy² ≤ 4`, centre excluded), in this fixed order:
  `(-2,0) (-1,-1) (-1,0) (-1,1) (0,-2) (0,-1) (0,1) (0,2) (1,-1) (1,0) (1,1) (2,0)` as `(dy,dx)`.
- **Attack offsets** (8, `CircleRange(1.5)` = the Moore neighbours), in this fixed order:
  `(-1,-1) (-1,0) (-1,1) (0,-1) (0,1) (1,-1) (1,0) (1,1)` as `(dy,dx)`.
- **Action index** (the upstream 21-way space, kept intact): `0 = do_nothing`, `1..12 = move` by the
  offsets above in order, `13..20 = attack` by the attack offsets in order.
- **Sim step** = one MAgent cycle. **Command turn** = one order round, every `order_interval = 20`
  steps, beginning with turn 1 at step 0 (before any stepping). `max_steps = 600` ⇒
  **30 command turns** in the default variant.

### Turn and tick structure — the exact resolution order

Per **command turn** `T` (at step `20·(T−1)`), in this order:

1. The engine snapshots the world and builds **both** seats' observation objects (§Decisions).
2. Both seats' LLM requests go out as **one parallel batch** (`asyncio.gather`), attempt-1 deadline
   9000 ms. Scripted seats compute their orders locally, instantly.
3. Each seat that timed out, errored, returned non-JSON or returned no usable `orders` array is
   retried **once**, again as a single batch, deadline 4000 ms.
4. A seat still without a usable reply gets the **`pincer`** scripted orders computed server-side,
   and a `fallback` record is written (§Decisions).
5. Orders are applied to squads. A squad named in the reply takes the new order; a squad not named
   keeps the order it had (turn 1's default for every squad is `advance`). An order whose fields do
   not validate is dropped individually and counted in `orders_rejected`; it does not void the reply.
6. `say` (≤ 120 runes) and the order list are written to the replay as records; `notes`
   (≤ 240 runes) is stored and echoed back **to that seat only** in the next turn's observation.
7. The engine waits, if needed, so that at least `turn_spacing_s = 8` seconds of wall clock have
   elapsed since the **start** of the previous batch (the Bedrock 30-req/min-per-episode floor).

Then, for each of the next `order_interval` **sim steps**, in this order — this is the whole physics
of the game and nothing else mutates the world:

1. `step += 1`. Snapshot positions and hp; every rule below reads the snapshot, never a partially
   updated world.
2. **Choose one action per living unit**, in ascending global unit id, from its squad's current
   order via the squad controller (§Decisions → "The squad controller").
3. **Resolve attacks**, in ascending attacker unit id. An attack at offset `o` hits the unit
   currently occupying `pos + o` iff that unit is alive and on the **other** army (an attack on an
   empty cell or on a friendly unit is *not registered* — upstream's rule — but still costs
   `attack_penalty`). A hit subtracts `damage` from the victim's hp. If the victim's hp reaches
   ≤ 0 it dies **immediately**: it is removed from the grid, its cell frees up for step 4, the
   attacker receives `kill_reward`, and a `kill` event is recorded. Overkill therefore depends on
   attacker order, which is why that order is pinned.
4. **Resolve moves**, in ascending unit id. A move to `pos + o` succeeds iff the destination is on
   the board and unoccupied **at the moment of application** (so a cell vacated in step 3 or by an
   earlier mover this step is available); otherwise the unit stays where it is. A unit that chose
   `do_nothing` does nothing.
5. **Recover**: every unit still alive gains `step_recover`, capped at `hp_max`.
6. **Reward**: every unit alive at the start of the step gets `step_reward`; every unit that
   attacked gets `attack_penalty`, plus `attack_opponent_reward` if the attack was registered
   against an enemy; every unit that died this step gets `dead_penalty`. Rewards accumulate into
   `magent_reward_sums[army]`. They are **recorded, not scored** — see below.
7. Append the tick record to the replay.
8. Evaluate the end conditions.

### Scoring formula and sign

Let `survivors[s]` be the number of living units in seat `s`'s army when the episode ends, and
`opp(s)` the other seat.

```
outcome[s] = +1 if survivors[s] >  survivors[opp]
              0 if survivors[s] == survivors[opp]
             -1 if survivors[s] <  survivors[opp]

score[s]  = 100 * outcome[s] + (survivors[s] - survivors[opp])
```

**Higher is better.** The formula is **exactly zero-sum** (`score[0] + score[1] == 0` always), which
is the idea's integrity requirement: no pair of seats can raise their joint total by cooperating.
Range at `map_size = 45`: `[-181, +181]`. The `100 *` term makes the win/loss decision dominate, and
the survivor differential is the tiebreak that rewards winning cleanly rather than by one man.
`results.scores` carries `score[s]`; `results.win` carries `outcome[s] == 1`. **The league ranks by
`scores`** (Elo 1000/32 from the head-to-head ordering, per the standard league settings).

MAgent's own per-unit rewards are summed per army into `results.magent_reward_sums` and shown on
the endcard, but they do **not** enter the score: they are the port's fidelity evidence and a
spectator readout, and scoring off them would reward attack-spam over winning.

### End conditions and legal `results.reason` values

The episode ends at the first of:

1. **Annihilation** — an army reaches 0 living units at the end of a step. If both reach 0 in the
   same step it is a draw. → `reason = "complete"`.
2. **Step cap** — `step == max_steps`. Settled by survivor count; equal counts are a draw. →
   `reason = "complete"`.
3. **Budget guard** — at the start of a command turn,
   `elapsed + 2 * turn_budget_s > wall_clock_budget_seconds`. This does **not** end the episode: it
   switches the LLM off for every remaining turn (both seats fall to `pincer`, microseconds per
   turn), the remaining steps run at full speed, and the episode still ends by rule 1 or 2 →
   `reason = "complete"`. A `budget_guard` record names the turn it fired.
4. **Hard stop** — wall clock reaches `wall_clock_budget_seconds` (default **660 s**) anyway. The
   engine stops at the current step, settles by survivor count, writes results and replay. →
   `reason = "deadline"`. This is declared **acceptable** for phase-60 check 4, but the budget guard
   exists so it should never fire.
5. **Fault** — an unexpected exception inside the sim or the engine loop. Caught; the episode is
   settled from the last completed step, `results.stop_detail` names the exception class (≤ 200
   runes, rune-truncated), artifacts are still written. → `reason = "fault"`.

**`results.reason` is a closed enum of exactly `["complete", "deadline", "fault"]`.** `complete` is
the healthy value; `deadline` is declared acceptable; `fault` is a defect and
`tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

A seat that never connects, disconnects, or fails every decision **does not end the episode** — its
army plays `pincer` and the game runs to its natural end. Nothing a player container does can stop
the clock.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {line, pincer}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=pincer`. A scripted policy seated as a champion is a failure state.

### Where the decision happens

**In the game server, not the player container** — the coworld-ctf/paintball shape
(`src/paintball_player.nim` is a thin seat registrar; `src/ctf/{llm,decide}.nim` do the work), and
the only shape that works on this platform: the `anthropic_api_key` coworld secret is injected into
the **game** pod (`game.runnable.env.ANTHROPIC_API_KEY_URI =
secret://coworld/magent-battle/anthropic_api_key` — the hive 2026-08-23 gotcha), phase 60 greps the
**game** log for `falling back` / `LLM provider is unavailable`, and `docker_smoke.sh` forwards
`ANTHROPIC_API_KEY` to the game container only.

The player container (`players/player.py`, one entrypoint for every policy) therefore does exactly
three things: dial `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`) with bounded
retries; send — and re-send for the first ~10 s of received frames, the paintball 2026-08-25
slot-sequential-join scar — a registration message

```json
{"type":"register","policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"line|pincer|null"}
```

with `prompt` rune-truncated to **4000 runes** and `policy` to **64 runes**; and then acknowledge
frames until the socket closes, **exiting 0 on a dead socket** (`try/except` around the whole
receive loop — the raid 0.1.3 close-frame race).

`server/cogame_magent_battle/llm.py` is a Python transcription of ctf's `src/ctf/llm.nim`, same
behaviour:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (read through `uris.py`) → **none**, in which case
  the client is `disabled` and every turn falls back instantly with no network wait (so offline
  certification finishes in seconds).
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`.
  Advance to the next candidate on 401/403 "Model access is denied" and on 429.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every
  sidecar call — raid round 2, 2026-08-23).
- `maxOutputTokens = 900` (not 400 — "cut off at max_tokens"). **No `output_config.effort`** when
  the model string contains `haiku` or `4-5`. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`.
- Response handling: read at most **8192 bytes**, then `extract_json_object` (outermost balanced
  `{…}`, tolerant of a code fence and of trailing prose), then schema validation.

### Cadence, batching, and the wall-clock arithmetic

One command turn every **20 sim steps**; **30 turns** in the `battle` variant, **20** in `skirmish`.
At each turn the server builds **both** seats' request bodies and issues them as **one parallel
batch** — never sequentially; this is a simultaneous-decision game and serial calls would double the
wall clock for nothing. At most 2 calls in flight, at most `2 × 30 × 2 = 120` calls per episode
including retries.

```
attempt-1 batch deadline           9.0 s
retry batch deadline               4.0 s
per-turn hard cap turn_budget_s   14.0 s   (monotonic deadline around the whole turn)
inter-batch spacing floor          8.0 s   -> 2 seats x 60/8 = 15 req/min  (sidecar cap: 30)

30 turns x max(spacing 8 s, budget 14 s), absolute worst          = 420 s
   typical (haiku answers in ~3-4 s, so spacing dominates)        = 240 s
600 sim steps, 162 units, integer NumPy                           =   3 s
connect wait (player_connect_timeout_seconds 120; typical 15 s)   =  15 s   (cap: 120 s)
results + replay write (independent, retried)                     =  10 s
                                                                  -------
typical total                                                     = 268 s   < 720 s
absolute worst case (420 + 3 + 120 + 10)                          = 553 s   < 660 s hard stop
engine hard stop wall_clock_budget_seconds                        = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                             = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wall_clock_budget_seconds` is ≤ 660 and `tests/test_manifest.py` asserts it.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turn_budget_s`, the connect timeout, the
aiohttp socket timeouts on the websocket server (which runs on its own task, so a 14 s LLM stall can
never drop a connection or stall `/healthz`), the 660 s engine stop, and a **20 s shutdown grace**
after artifacts are written during which `/healthz` and `/global` keep answering (the lantern 0.1.3
`/global` ping scar) before the process exits.

On a seat's timeout or parse failure: **retry once** in the next batch; on the second failure that
seat's orders for that turn become the **`pincer`** scripted orders computed inside the game server
(the same function the `pincer` baseline uses — imported, not duplicated), and a `fallback` record
is written with `cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard,
disconnected}`. `results.fallbacks[s]` counts them.

**No failure mode leaves a unit unactuated.** The squad controller always has an order: this turn's,
else last turn's, else `advance`. A seat that never connects at all is reported once to
`COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload — exactly
`{"message", "failed_policy_index"}`, nothing else — and its army plays `pincer` to the end.

### Per-seat observation: exactly what is visible and what is hidden

**Visible.** Everything about the seat's own army, and — this is the port's fog of war, and it is
MAgent's own `view_range` lifted to army scale — an enemy unit is visible iff **some living friendly
unit is within `CircleRange(6)` of it** (`dx² + dy² ≤ 36`). Enemy squads with no visible member are
reported as unseen, with the last turn they were seen.

**Hidden.** The positions and hp of unseen enemy units; every enemy squad's *order*; the opponent's
`notes`; the opponent's real player name and policy name; the seed's future; the opponent's
fallback/decision statistics. Nothing about the opponent's identity ever reaches a prompt.

The observation is a JSON object appended to the user message. It is also mirrored (minus
`your_notes`) into the replay's `turns[]` record, so the replay explains every decision.

```json
{
  "you": "Alpha",
  "opponent": "Bravo",
  "turn": 7, "of": 30, "step": 120, "order_interval": 20, "steps_left": 480,
  "map": {"width": 45, "height": 45},
  "unit": {"hp_max": 10.0, "damage": 2.0, "recover_per_step": 0.1,
           "move_up_to": 2, "attack_reach": 1, "view_radius": 6},
  "your_army": {
    "alive": 63, "started": 81, "lost_last_turn": 4,
    "squads": [
      {"id": "A1", "alive": 9, "x": 12, "y": 30, "hp": 9.4, "order": "advance"},
      {"id": "A2", "alive": 7, "x": 14, "y": 28, "hp": 6.1, "order": "focus B5"}
    ]
  },
  "enemy": {
    "visible_units": 22, "killed_last_turn": 6,
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

Field rules: `x`/`y` are the integer centroid of the *living, visible* members
(`sum // count`, floor); `hp` is the mean hp of those members in upstream units, rounded to one
decimal; `seen` is the count of currently-visible enemy members; `last_seen_turn` is `null` if that
squad has never been seen. `score_now` is the running `survivors[you] − survivors[them]`. All nine
squads of each side are always listed, in id order, so the array shape never changes.

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
| `orders[].squad` | string | **≤ 2 runes**; must be one of this seat's nine ids (`A1`…`A9` / `B1`…`B9`); duplicates: last one wins |
| `orders[].verb` | string | **≤ 8 runes**; enum `advance` \| `hold` \| `focus` \| `flank` \| `retreat`, lower-cased before matching |
| `orders[].x`, `.y` | integer | required iff `verb == "hold"`; `0 ≤ v < map_size`; out of range ⇒ that order dropped |
| `orders[].target` | string | required iff `verb == "focus"`; **≤ 2 runes**; must be an **enemy** squad id |
| `orders[].side` | string | required iff `verb == "flank"`; **≤ 5 runes**; enum `left` \| `right` |
| `say` | string | **≤ 120 runes** — spectator chatter, rendered in the feed |
| `notes` | string | **≤ 240 runes** — private, echoed to this seat only next turn |
| whole reply | bytes | **≤ 8192 bytes** read from the provider before parsing |
| `PLAYER_PROMPT` (registration) | string | **≤ 4000 runes** |

**Every string that lands in the replay — `say`, `notes`, the policy label, `stop_detail`, and any
recorded error text — is truncated on rune boundaries** (`str[:n]` over decoded text, never over
bytes). Byte-boundary truncation is what makes a replay that renders in a browser fail a strict JSON
parser; `tests/test_replay.py` asserts strict UTF-8 on a replay whose every capped field is filled
with 4-byte emoji at exactly the cap.

Unknown top-level keys are ignored. A missing `orders` key with a present `say` is a **usable**
reply (every squad keeps its order); a reply that is not a JSON object, or whose `orders` is not an
array, is a parse failure.

### System prompt (fixed, identical for both champions)

```
You are the field commander of one army in a large-scale grid battle. You command NINE
SQUADS, not individual soldiers. Once every 20 simulation steps you issue one order per
squad and a deterministic controller executes it.

RULES YOU ARE PLAYING UNDER
- The board is a 45x45 open grid. Your army starts on one side, the enemy on the other.
- Every soldier has 10 hp, deals 2 damage to ONE adjacent enemy per step, moves up to 2
  cells per step, and regains 0.1 hp per step. A soldier can move OR attack, never both.
- A soldier that is not attacking is healing. Nine soldiers on one enemy kill it in one
  step; one soldier on one enemy takes five steps and takes damage back the whole time.
  Local numbers are everything.
- You see an enemy only when one of your own soldiers is within 6 cells of it. Squads
  reported with "seen": 0 are somewhere you cannot see.
- The winner is whoever has more soldiers standing at the end. Trading evenly is a draw.

YOUR ORDERS, one per squad, executed every step until you change them:
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
soldier in one step.
Send the reserve in only when your mass is already engaged, and send it to the same
target id. If a squad's mean hp drops below 4.0, order it "retreat" for exactly one turn
to heal, then bring it straight back with "focus" on whatever the mass is chewing.
Never order "advance" for more than one squad at a time - it scatters them.
```

### Champion #2 — `magent-battle-marshal` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Win by attrition. Healing is 0.1 hp per step and a turn is 20 steps, so a squad that
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

Runs inside the sim, once per living unit per step. `T(u)` is the unit's target cell; `attack_ok`
says whether the unit may strike. Ties everywhere are broken by the fixed offset order above, then
by ascending unit id — there is no randomness in the controller at all.

| Order | `T(u)` | `attack_ok` | Preference among adjacent enemies |
|---|---|---|---|
| `advance` | position of the nearest living enemy to `u` (squared Euclidean; ties by lowest enemy id) | yes | lowest hp |
| `hold x y` | `(x, y)` | yes | lowest hp |
| `focus S` | integer centroid of living squad `S`; if `S` is extinct, behave as `advance` | yes | members of `S` first, then lowest hp |
| `flank left` / `flank right` | enemy-army centroid displaced by `dy = -8` (left) / `+8` (right), clamped to the board; once `u` is within 6 cells of that point, `T(u)` becomes the enemy-army centroid | yes | lowest hp |
| `retreat` | `(own_back_x, u.y)` — red `x = 1`, blue `x = map_size - 2` | **no** | — |

Given `T(u)` and `attack_ok`:

1. If `attack_ok` and at least one living enemy occupies one of the 8 attack offsets → emit the
   attack action toward the preferred enemy.
2. Else, among the 12 move offsets whose destination is on the board, choose the one minimising
   squared distance to `T(u)`; if that distance is not strictly less than the unit's current
   squared distance to `T(u)`, emit `do_nothing` (action 0).
3. Occupancy is **not** consulted here — a blocked move simply fails at resolution step 4. That is
   upstream's behaviour and it is what makes a dense formation shuffle rather than teleport.

### Scripted baselines (both shipped as fillers; `pincer` is also the server-side fallback)

**`line`** — `PLAYER_SCRIPTED=line`. Every squad gets `advance`, every turn, forever. Five lines of
code, a real opponent (mass charge beats a badly-split commander), and the control against which
"did the LLM do anything?" is measured.

**`pincer`** — `PLAYER_SCRIPTED=pincer`. Each turn, in this order:

1. Any squad with `alive > 0` and mean hp `< 4.0` → `retreat`.
2. Else, any squad with a visible enemy squad whose centroid is within 3 cells → `focus` that id
   (nearest; ties by lowest id).
3. Else, squads 1–3 → `flank left`; squads 4–6 → `advance`; squads 7–9 → `flank right`.
4. `say` is empty; `notes` is empty. It emits at most 9 orders, all with legal ids and enum values,
   which `tests/test_baselines.py` asserts over 200 randomised states (§Tests).

---

## Sim module

### What is kept from cogame-moba, by path

| cogame-moba path | Here | Treatment |
|---|---|---|
| `server/cogame_moba/uris.py` | `server/cogame_magent_battle/uris.py` | **Verbatim** (module docstring aside): `COGAME_CONFIG_URI` / `RESULTS_URI` / `SAVE_REPLAY_URI` / `PLAYER_FAILURE_URI` / `LOAD_REPLAY_URI` reading and writing, file/http/s3 schemes, independent retried writes |
| `server/cogame_moba/config.py` | `.../config.py` | Forked: same `GameConfig` dataclass + JSON-schema-mirroring validation shape, new fields |
| `server/cogame_moba/defaults.py` | `.../defaults.py` | Forked: server-contract defaults (`max_steps`, `order_interval`, deadlines, seat topology) with the upstream citation next to every physics value |
| `server/cogame_moba/engine.py` | `.../engine.py` | Forked: the lockstep loop becomes the turn/step loop of §The game; the **bounded per-decision deadline**, the degrade path and the **strike rule** (a seat silent for 3 consecutive turns is marked dead and stops consuming deadline; a valid reply revives it) are kept |
| `server/cogame_moba/server.py` | `.../server.py` | Forked: aiohttp app, `/healthz`, `/player?slot=&token=` (token-checked), `/global` websocket emitting a first message immediately, `GET /client/player?slot=&token=`, `GET /client/global`, `/client/replay`; closed `{"message","failed_policy_index"}` failure payload; fire-and-forget broadcast sends; 20 s shutdown grace |
| `server/cogame_moba/replay.py` | `.../replay.py` | **Replaced** — see "Replay format" below |
| `server/cogame_moba/sim.py` | `.../sim.py` | **Replaced** — see below |
| `players/client.py` | `players/client.py` | Forked: bounded dial, re-sent registration, exit 0 on a dead socket |
| `players/{baseline,scripted,random}_player.py` | `players/player.py` | Replaced by one env-switched entrypoint |
| `tools/ci/next_coworld_version.py` + its test | same paths | **Verbatim** |
| `docs/PROTOCOL.md` | `docs/PROTOCOL.md` | Forked to this game's messages |
| `pyproject.toml`, `uv.lock`, `.dockerignore` | same paths | Forked (drop `wasmtime`, keep `aiohttp`, `numpy`) |

### What the port keeps, and the two things it deliberately drops

cogame-moba's port discipline exists to protect **pretrained policy weights**: "RL policies are
trained against an exact environment … the port must reproduce the training environment
bit-exactly, or the policies degrade in ways that are invisible until they lose"
(`docs/PORTING.md`). **This coworld serves no MAgent-trained weights.** Its seats are LLM commanders
and scripted baselines that read squad summaries, never the 13×13×5 observation tensor. The two
things dropped are dropped for that reason, and each has a named replacement:

1. **No vendored C compiled to wasm, and no `tests/test_fidelity.py` byte-comparison gate.** MAgent's
   engine is a multi-thousand-line C++ `GridWorld` with jsoncpp and thread pools, not a single-header
   Ocean env with an upstream `build.sh --web`; emscripten-vendoring it would be the largest piece of
   this build and would buy nothing that is consumed. **Replacement:** `sim/` is
   `server/cogame_magent_battle/sim.py`, ~500 lines of **integer** NumPy, plus the four gates in
   "Proving the port" below.
2. **No binary replay.** `replay.py`'s magic + header + packed-action format is replaced by a single
   **UTF-8 JSON document** (below), because phase-60 check 4 fetches the replay bytes from S3 and
   requires **valid UTF-8 JSON**, and because a state-carrying replay lets the viewer draw without
   re-simulating.

### The sim itself

`server/cogame_magent_battle/sim.py`, pure Python + NumPy, no wasm, no C, no libc `rand`.

- State: `pos` (`int16[N,2]`, `-1` for dead), `hp` (`int16[N]`, tenths), `army` (`int8[N]`),
  `squad` (`int8[N]`), and an occupancy grid `occ` (`int32[map_size,map_size]`, `-1` empty) kept in
  sync with `pos`. `N = 2 × units_per_army`.
- **All arithmetic is integer.** `hp_max = 100`, `damage = 20`, `step_recover = 1`. Upstream's float
  `hp 10 / damage 2 / step_recover 0.1` is exactly representable in tenths, while binary floats are
  not (`0.1` drifts under accumulation), so integers are simultaneously *more* faithful to the
  intended semantics and perfectly reproducible on every platform. Rewards are accumulated as
  integer thousandths (`step −5, dead −100, attack −100, attack_opponent +200, kill +5000`) and
  divided by 1000 only when written out.
- **The only randomness in the whole game is the seed**, and in `battle` it is used for nothing at
  all: spawns are deterministic (`generate_map` is a pure function of `map_size`), the controller is
  deterministic, resolution order is by unit id. The seed is still generated, recorded in the
  replay header and in `results.seed`, and passed to a `numpy.random.Generator(PCG64(seed))` that
  the `battlefield`/`gather` variants (§Out of scope) will need. Two episodes with the same seed and
  the same orders are byte-identical.
- Cost: 600 steps × 162 units, vectorised nearest-enemy and offset selection ⇒ **< 3 s** measured
  budget, asserted by `tests/test_sim.py::test_step_budget`.

### Documented divergences from upstream (the honest-port list, mirrored into `vendor/PATCHES.md`)

1. **HP and rewards in integers** (tenths / thousandths) instead of floats. Semantics identical;
   determinism strictly better.
2. **Resolution order pinned**: all attacks in ascending unit id, then all moves in ascending unit
   id, then recovery. MAgent's engine resolves in an internal order this note cannot verify from the
   Python layer; a fixed order is required for a replay to be re-derivable.
3. **Who chooses the action changed, not what the actions are.** Per-unit RL policies are replaced
   by the squad controller under two commander seats — the idea's explicit "policy-per-army"
   seating. The 21-action space, the two `CircleRange` tables, damage, recovery, the
   no-friendly-fire rule and all five reward terms are upstream's.
4. **`max_steps` 600 (battle) / 400 (skirmish)** instead of `max_cycles = 1000`, to fit the 720 s
   budget. Recorded in the replay config so a viewer can never mistake it for the upstream default.
5. `minimap_mode = False`, `extra_features = False` — upstream defaults, unchanged.

### Proving the port (what replaces the fidelity gate)

- `vendor/upstream/battle.py` — **byte-pristine** copy of
  `Farama-Foundation/MAgent2:magent2/environments/battle/battle.py` at a pinned commit, never edited.
  `vendor/UPSTREAM.md` records the repo, the commit hash, the fetch URL and the file's sha256.
  `vendor/LICENSE-magent2` carries the upstream licence.
- `tests/test_upstream_constants.py` — the **tripwire**, the moba `tests/test_scripted.py` pattern:
  regex-parse `vendor/upstream/battle.py` and assert byte-equality against every ported constant
  (`hp`, `speed`, `damage`, `step_recover`, `view_range`, `attack_range`, `KILL_REWARD`,
  `step_reward`, `dead_penalty`, `attack_penalty`, `attack_opponent_reward`, `default_map_size`,
  `max_cycles_default`, and the `init_num`/`side`/`gap` spawn arithmetic). A re-vendor that changes
  a number **fails tests** instead of silently desyncing the game.
- `tests/test_generate_map.py` — a direct transcription of upstream's `generate_map` loop is run for
  `map_size ∈ {12, 31, 45, 64}` and asserted equal, position for position, to the sim's spawner;
  and `map_size = 45` is asserted to yield exactly **81 and 81**.
- `tests/test_determinism.py` — record an episode, re-run the sim from the replay's seed + recorded
  orders alone, and assert every tick record is byte-identical.

---

## Server, player, protocol

### The websocket contract

Unchanged in shape from cogame-moba (`docs/PROTOCOL.md` is forked, not rewritten):
`COGAME_CONFIG_URI` in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST`/`PORT`; player
sockets at `/player?slot=<i>&token=<t>`.

| Direction | Message |
|---|---|
| player → game | `{"type":"register","policy":"…","prompt":"…","scripted":"line"\|"pincer"\|null}` (re-sent for ~10 s) |
| game → player | `{"type":"turn","turn":7,"step":120,"view":{…observation…}}` at every command turn |
| player → game | `{"type":"ack","turn":7}` — the seat has nothing to send; the game does the thinking |
| game → player | `{"type":"done","reason":"complete","score":41,"survivors":[41,0]}` then close |
| global → viewer | one status frame immediately on connect, then a broadcast per command turn; fire-and-forget sends so a slow viewer can never stall the episode |

The certifier's browser probes are served for real and are registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering
for the 20 s shutdown grace.

### Results document (closed schema; `server.py::_results_doc` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":   ["daveey", "daveey-1"],
  "aliases": ["Alpha", "Bravo"],
  "armies":  ["red", "blue"],
  "scores":  [141, -141],
  "win":     [true, false],
  "winner":  0,
  "reason":  "complete",
  "final_step": 431,
  "turns_played": 22,
  "survivors": [41, 0],
  "kills":     [81, 40],
  "seed": 1734029581,
  "magent_reward_sums": [612.415, -238.09],
  "policy_kinds": ["llm", "scripted"],
  "llm_turns":   [22, 0],
  "fallbacks":   [1, 0],
  "orders_rejected": [0, 0],
  "dead_seats": [false, false],
  "stop_detail": ""
}
```

`winner` is `0`, `1` or `null` (draw). Adding a key means updating `_results_doc`, the manifest's
`results_schema`, and `tools/ci/docker_smoke.sh`'s expected-key set together — Coworld schemas are
closed and undeclared keys are dropped.

### Replay bytes (self-sufficient, strict UTF-8 JSON)

One JSON document. **Everything the viewer needs is in it** — names, aliases, policy kinds, the full
config, the seed, the spawn roster, per-tick state, every event, the orders, and the result. The
viewer contacts nothing but S3 for this file.

```json
{
  "format": "cogame-magent-battle-replay",
  "format_version": 1,
  "game_version": "1",
  "seed": 1734029581,
  "config": {
    "map_size": 45, "units_per_army": 81, "squads_per_army": 9,
    "max_steps": 600, "order_interval": 20,
    "hp_max": 100, "damage": 20, "step_recover": 1,
    "view_radius": 6, "attack_reach": 1, "move_up_to": 2,
    "move_offsets": [[-2,0],[-1,-1],[-1,0],[-1,1],[0,-2],[0,-1],[0,1],[0,2],[1,-1],[1,0],[1,1],[2,0]],
    "attack_offsets": [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]],
    "squad_sizes": {"A": [9,9,9,9,9,9,9,9,9], "B": [9,9,9,9,9,9,9,9,9]}
  },
  "rewards": {"step": -0.005, "dead": -0.1, "attack": -0.1,
              "attack_opponent": 0.2, "kill": 5},
  "seats": [
    {"slot": 0, "alias": "Alpha", "army": "red",  "name": "daveey",
     "policy": "magent-battle-vanguard", "kind": "llm",      "scripted": null},
    {"slot": 1, "alias": "Bravo", "army": "blue", "name": "Baseline (1)",
     "policy": "magent-battle-pincer",   "kind": "scripted", "scripted": "pincer"}
  ],
  "roster": [{"id": 0, "army": 0, "squad": "A1", "x": 1, "y": 13}],
  "ticks": [
    {"t": 1, "p": [0, 58, 100, 1, 103, 100], "ev": [{"k": "turn", "n": 1}]}
  ],
  "turns": [
    {"turn": 7, "step": 120, "slot": 0, "source": "llm", "latency_ms": 3120,
     "orders": [["A1","advance",null], ["A3","focus","B5"], ["A4","flank","left"],
                ["A2","hold","22,30"]],
     "say": "wrap their left", "view": {"…": "the observation, minus your_notes"}}
  ],
  "result": { "…": "byte-identical to the results document above" }
}
```

`ticks[i].p` is a flat integer array, **three ints per living unit**: `unit_id`,
`cell = y * map_size + x`, `hp` (tenths). Dead units are simply absent, so `len(p) / 3` is the alive
count and the unit-count sparkline is derivable from the file with no extra data. At 45×45 with 600
ticks the document is ≈ 1.2 MB — well inside what `std/json` parses in the wasm viewer, and
`tests/test_replay.py` asserts a ceiling of 4 MB.

### Event vocabulary (`ticks[].ev`) — a closed enum of nine kinds

| `k` | Fields | Emitted when |
|---|---|---|
| `turn` | `n` | at the first tick of each command turn |
| `order` | `slot`, `squad`, `verb`, `arg` | once per accepted order, at the turn tick |
| `say` | `slot`, `text` (≤ 120 runes) | a seat's `say` is non-empty |
| `fallback` | `slot`, `cause` | a seat's decision degraded to `pincer` |
| `firstblood` | `slot`, `unit`, `victim` | the first kill of the episode |
| `kill` | `a` (attacker id), `v` (victim id), `c` (cell) | every kill |
| `rout` | `army`, `lost` | at a turn tick, an army lost ≥ 10 units since the previous turn |
| `wipe` | `army` | an army reaches 0 living units |
| `end` | `reason`, `winner`, `survivors` | the last tick |

**Scrubber beats** are emitted for exactly five of these — `firstblood`, `rout`, `wipe`, `fallback`,
`end` — and the viewer ships CSS for exactly those five kinds and no others (`kill`, `turn`, `order`
and `say` drive the feed, not the scrubber; 40+ kills would make the scrubber unreadable).

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`, and `tools/build_replay_viewer.sh` (committed
**executable** — `coworld build` hard-requires `os.X_OK`) is coworld-ctf's hook, kept, with the
image tag and the `docker cp` source path changed; it builds `Dockerfile.replay-viewer`'s
`replay-viewer-builder` target and copies the dist out. It `mkdir -p`s the output parent **before**
its containment check (the ecos 2026-08-23 scar: `coworld build` pre-creates that directory, CI does
not). No `/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files — and why it is not the code starter

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/magent_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter:
`Metta-AI/coworld-ctf`.** Never a mixture. Splicing one starter's shell onto another's emscripten
link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer
silently — cogame-lantern, 2026-08-23.

It is not cogame-moba because **cogame-moba has none of those four files.** Read at
`/workspace/starters/cogame-moba`: there is no `client/` directory, no `chrome_common.js`, no
`static_replay*.js`, no `replay-viewer/`; the whole viewer is `viewer/index.html`, a 232-line bespoke
page whose transport is one `<input type=range>` and a speed `<select>`, with no `--band`, no
`--hudscale`, no scrubber beats, no scorebug, no endcard and no `data-replay-loaded` signal. Adopting
it would mean writing the chrome from scratch, which the playbook names as the failure mode
(cogame-gridlock, 2026-08-23). coworld-ctf's set is internally consistent and is taken as one piece:
the Worker sets `Module.onRuntimeInitialized`, the module is emitted **non-modularized** as
`magent_replay.js`, `config.nims` (55 lines, read) keeps `--os:linux --cpu:wasm32 --cc:clang` with
`emcc`, `--mm:arc --exceptions:goto -d:useMalloc`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`**
(non-negotiable: wasm32 has no memory protection and a nil write lands at address 0),
`-s ENVIRONMENT=web,worker,node` and `EXPORTED_RUNTIME_METHODS=HEAPU8`, with `EXPORTED_FUNCTIONS`
renamed to `_main,_malloc,_free,_magent_load_replay,_magent_frame,_magent_input,_magent_packet_ptr,
_magent_packet_len,_magent_mismatch_tick,_magent_error_ptr,_magent_error_len,_magent_stage_ptr,
_magent_stage_len`; and `static_replay_worker.js` does
`importScripts('./battle_core.js','./magent_replay.js')` in that order.

`magent_replay.nim` keeps ctf_replay.nim's structure exactly — the `stampStage` progress buffer, the
`bytesFromPointer` helper, the try/except that publishes `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from destroying
module globals while JS still calls in. What changes is the body: it **parses the replay JSON and
draws recorded state — it does not re-simulate.** `magent_load_replay` parses the document with
`std/json`, validates `format`/`format_version`, bakes the unit chips and the floor, and renders
frame 0; `magent_frame` advances (or seeks to `viewer.replaySeekTick`) and rebuilds the packet;
`magent_mismatch_tick` returns `-1` unless `game_version` differs from the version baked into the
bundle, which lights `#mmwarn`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch — posted by the Worker only *after* the
first packet has been handed to the draw layer and drawn, so the attribute means "a frame is on the
canvas", not "a file was fetched". On failure it sets **`data-replay-error`** on `<html>` with the
message, in `showFailure()`. Both are coworld-ctf's own signals, inherited unchanged. The
`coworld-replay` postMessage bridge's `ready` is posted **from a callback fired after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus `3c11c953`,
2026-08-24) — otherwise the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte from coworld-ctf.** Not edited, not
  reformatted; `tests/test_viewer.py` pins its sha256 against the starter's file. Everything this
  game adds lives in the appended game block.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids. The starter's CSS, markup, `relayout()`, transport, endcard,
  locker-room loader, `?embed=1` mode and `.tiny` density system are untouched; the appended block
  replaces only the *contents* of the scorebug plates, adds the heat toggle, the front-line layer and
  the unit-count sparkline, and retargets the feed rows, the beat rendering and the endcard columns.
  A test asserts the starter's byte prefix is intact and that the file only grows.
- **`client/broadcast_core.js` is forked to `client/battle_core.js`** and is the one viewer file that
  is *not* byte-identical, because it is paintbot's draw layer and this game has no flags, paint,
  hills, grenades or hearts. Kept unchanged (and pinned function-by-function by
  `tests/test_viewer.py` against the starter's text): the canvas/DPR sizing, `relayout()`, the camera,
  the feed queue and `pushFeed` **including its signature** (the cogball 0.1.4 latch scar), the beat
  and lull machinery, the endcard builder, the speed chips, the `?embed=1` path. Deleted: every
  ctf-specific draw call and the FPV pipeline. Added: `drawBattlefield`, `drawHeat`,
  `drawFrontLine`, `drawSparkline`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`. **Zoom decision: dropped.** The board is a fixed 45×45 grid that
    `relayout()` always fits whole inside the frame, so per the pin a fixed arena drops `#viewpanel`
    entirely; the page's `attachMinimap(...)` call goes with it.
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — there is no
    per-unit point of view to show; the whole board is the shot.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.pb-tags`, `.squad`
    and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.steal`, `.beat-marker.return`, `.beat-marker.capture`, `.beat-marker.hillflip`
    and `.beat-marker.hillhold` CSS rules — those kinds are never emitted here.
  - The perk and handicap badges.
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (caption text
    swapped), `#chrome`, `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/
    `#clock-caption`, `#bannerlane`, `#killfeed`, `#mmwarn`, **`#transport` in full**
    (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`,
    `#btn-spoilers`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`, `#tick-clock`, `#speedchips`),
    `#scrub` with `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/`#scrub-head`, `#endcard` with
    `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`, and `#status`.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged. **No overlay sits in the transport band**: the board is laid out between the two
bands and every addition here (the heat overlay, the front line, the sparkline, the feed, the
banners) is positioned inside the board region or in the top band. The **endcard stops at
`var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule, kept) so the scrubber
stays clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `battleBeat(tick, kind, side, label)` — named so it can never shadow
`chrome_common.js`'s `markBeat` alias, the tandem 2026-08-23 hoisting trap — appends
`<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind emitted and no others**: `.beat-marker.firstblood`, `.beat-marker.rout`,
`.beat-marker.wipe`, `.beat-marker.fallback`, `.beat-marker.end`. The game block never calls
`markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: 1 sim step per animation frame at 30 fps** (speed chips `[0.5, 1, 2, 4, 8]`,
default 1). A 600-step replay therefore plays for **20 s**, which is what lets
`viewer_smoke.mjs --soak 10` observe real advancement instead of a finished replay (the ecos
2026-08-23 scar: a smoke replay shorter than the soak window reports as frozen).

### Readouts

1. **The battlefield** — the 45×45 grid drawn edge to edge: each living unit is a baked team chip
   (see Art), its hp shown as chip brightness plus a 1 px hp pip; a unit that dies flashes white and
   fades over 6 frames, leaving a scorch mark for 60 frames so the shape of the fight persists.
2. **Army heatmaps** (the idea's first ask) — a translucent density overlay, 9×9 bins of 5×5 cells,
   red and blue additively blended, redrawn every frame. On by default, toggled by a labelled
   `HEAT` chip in the top band, never in the transport band.
3. **Front line** (the idea's second ask) — a chalk polyline: for each row `y`, the midpoint between
   the rightmost living red unit and the leftmost living blue unit within rows `y ± 2`; rows where
   one side is absent leave a gap, so a broken line literally shows a broken front. Redrawn every
   frame, with a 3-frame trail so a collapse is visible as motion.
4. **Unit-count sparkline** (the idea's third ask) — the starter's `#momentum` SVG retargeted to two
   series over the whole episode, red alive and blue alive, with the playhead marked and the `rout`
   and `wipe` ticks flagged. It is derived from `ticks[].p` lengths and **shipped once on the first
   frame**, so the graph draws its full width immediately instead of growing in.
5. **Scorebug plates** — two plates, one per side: the seat's **real policy name** (spectator side
   only), its in-game alias (`ALPHA` / `BRAVO`), the **alive count** as the big numeral and kills as
   the small one, and a `↯` glyph on the plate of any seat that has taken a fallback this episode.
6. **Clock** — `#clock-time` shows `turn 7/30`, `#clock-caption` shows `step 120/600 · 63 v 71`.
7. **Match feed** (`#killfeed`) — plain language, never internal notation:
   `ALPHA A3 → focus BRAVO B5`, `BRAVO B7 falls back to heal`,
   **`FIRST BLOOD — ALPHA`**, **`BRAVO'S RIGHT WING IS ROUTED — 14 DOWN`**,
   **`BRAVO IS WIPED OUT`**, `Alpha: "wrap their left, A2 holds the gap"`, and
   `BRAVO MISSED THE CALL — scripted orders (timeout)`. The commander `say` lines and the order
   lines are where a spectator sees the LLM playing.
8. **Endcard** — `ALPHA WINS — 41 SURVIVORS TO 0 (step 431)`, the two-seat table (survivors, kills,
   MAgent reward sum, LLM turns, fallbacks, orders rejected) and `SCORE +141 / −141`. It stops at
   `var(--band)` and any seek dismisses it.
9. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls
   (a lull = 40 consecutive steps with no `kill` event), spoilers switch, tick readout, speed chips,
   the scrubber with the five beat buttons, and `#mmwarn` for a `game_version` mismatch — all the
   starter's, verbatim.

### Art

**Real art, from coworld-ctf's shipped assets — no placeholders, no solid-colour squares, no
downloads.** The battlefield floor is `data/arena_floor.png`, tiled and darkened 18 %. Units are
**baked at load** by `magent_replay.nim`'s own compositor from ctf's `data/soldier_red.png` and
`data/soldier_blue.png`: at load it renders each sprite once into three chip sizes (6, 10 and 16 px)
with a 1 px team rim and three hp-brightness variants, giving 18 pre-baked chips total — so drawing
162 units per frame is 162 blits and never a per-unit rasterisation. The loading screen is the
starter's locker room (`client/art/lockerroom/bg.jpg` plus the red/blue cog webps) with the caption
swapped to "Forming up on the line…". Text is `data/font.ttf`. Scorch marks and the front-line chalk
are procedural, drawn with the same palette as the floor bake.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter already engineers this — `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim. Three rules are added and asserted by `tests/test_viewer.py`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps only `alias + name + alive count`; the kills numeral is hidden.
3. Under `.tiny`, the heat overlay drops to 5×5 bins and the front line is drawn 2 px wide, and the
   unit chips use the 6 px bake (45 cells across 360 px is 8 px per cell, so a 6 px chip with a 1 px
   rim reads cleanly with a 1 px gutter).

---

## Packaging

- **Repo**: `Metta-AI/cogame-magent-battle`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `magent-battle`; **`game.name` is
  `magent-battle`** (hyphenated, matching the slug) so the secret namespace
  `secret://coworld/magent-battle/anthropic_api_key`, the page slug, the league seed and the docs all
  agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — one service, **underscored**, because the manifest image placeholder is
  derived from the compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0):

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
- **`Dockerfile`** — cogame-moba's runtime stage shape, `--platform=linux/amd64`, `python:3.12-slim`
  + `uv sync --frozen`, copying `server/`, `players/`, `vendor/upstream/`, `docs/`, `config.json`.
  **The wasm-builder stage is dropped** (no C sim). Two entrypoints from one image:
  `CMD ["python","-m","cogame_magent_battle.server"]` for the game, and
  `/bin/magent-battle-player` (a two-line shim for `python -m players.player`) for every policy.
- **`Dockerfile.replay-viewer`** — coworld-ctf's, verbatim in structure (`emscripten/emsdk:4.0.15`,
  pinned nimby with its sha256 check, the marker splices, the `test -f`/`grep -q` assertion block),
  with the asset list swapped to `data/{soldier_red,soldier_blue,arena_floor}.png`, `data/font.ttf`,
  `client/art/lockerroom/*`, `magent_replay.{js,wasm,data}`, `battle_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — cogame-moba's template as the shape, with these decisions:
  - `$schema` present; top-level `tags: ["magent","battle","port","multiagent"]` (≥ 3, and `game.tags`
    must **not** exist); `episode_timeout_minutes: 20` at the **top level**, not under `game`.
  - `game.name = "magent-battle"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.replay_viewer = {"bundle":"static-replay-viewer"}`
    (under `game`, not top-level), `game.runnable.env.ANTHROPIC_API_KEY_URI =
    "secret://coworld/magent-battle/anthropic_api_key"`.
  - `game.config_schema` is a real JSON Schema, `additionalProperties: false`, `required:
    ["tokens","players"]`; **every array property carries `minItems`/`maxItems`** (`tokens` 2/2,
    `players` 2/2 — the tandem 0.1.0 scar). `tokens` is described as runner-injected and appears in
    **no** `game_config` (the knights-archers 0.1.0 scar). Properties: `tokens`, `players`, `seed`,
    `map_size` (enum `[31, 45]`, default 45), `max_steps` (default 600), `order_interval` (default
    20), `turn_budget_ms` (default 14000), `turn_spacing_ms` (default 8000),
    `player_connect_timeout_seconds` (default 120), `wall_clock_budget_seconds` (default 660),
    `num_agents` (integer, `minimum: 2`, `maximum: 2`, default 2).
  - `game.results_schema` closed and exactly the keys in §Server.
  - **`game.protocols` carries BOTH `player` and `global`**, each as
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-magent-battle/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"porting.md","title":"Porting MAgent battle","content":{"type":"uri","value":".../docs/PORTING-MAGENT.md"}}]}`.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be `"1"`**, `500m` is below the platform minimum (pistonball 0.1.1). Two entries, `line` and
    `pincer`, so that **every declared player occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 2` inside `game_config`, never at the variant top level** (`CoworldVariant`
  is `additionalProperties: false`; goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "battle", "name": "Battle (45x45, 81 v 81)",
     "description": "MAgent battle_v4 at upstream scale: two armies of 81 on a 45x45 open grid, one commander per army, 30 command turns.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}],
                     "num_agents": 2, "map_size": 45, "max_steps": 600, "order_interval": 20,
                     "turn_budget_ms": 14000, "turn_spacing_ms": 8000,
                     "player_connect_timeout_seconds": 120, "wall_clock_budget_seconds": 660}},
    {"id": "skirmish", "name": "Skirmish (31x31, 25 v 25)",
     "description": "The same rules on a 31x31 grid with 25 units per army and 20 command turns - a faster ladder round with the same nine-squad command surface.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}],
                     "num_agents": 2, "map_size": 31, "max_steps": 400, "order_interval": 20,
                     "turn_budget_ms": 14000, "turn_spacing_ms": 8000,
                     "player_connect_timeout_seconds": 120, "wall_clock_budget_seconds": 660}}
  ]
  ```

  (`map_size = 31` yields 25 units per army from upstream's own `generate_map` arithmetic:
  `init_num = 38.44`, `side = 12`, left block 5 columns × 5 rows after the `0 < x` filter, right
  block truncated to match. `tests/test_generate_map.py` asserts the number rather than trusting this
  paragraph.)

  **Certification fixture** — `num_agents: 2` again, inside `certification.game_config`, and exactly
  two players so `len(certification.players) == len(game_config.players) == num_agents == 2` (the
  four `SEAT-COUNT` invariants in `docker_smoke.sh`):

  ```json
  "certification": {
    "players": [{"player_id": "pincer"}, {"player_id": "line"}],
    "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}],
                    "num_agents": 2, "seed": 42, "map_size": 31, "max_steps": 600,
                    "order_interval": 20, "player_connect_timeout_seconds": 60,
                    "wall_clock_budget_seconds": 240}
  }
  ```

  600 steps of scripted play is ~2 s of sim, but the resulting replay is 600 ticks ⇒ **20 s of
  playback**, which the viewer soak needs. The certify step in `coworld-release.yml` passes
  **`--timeout-seconds 300`** (the default is 60 and covers start + connect grace + play + linger —
  cooperative-hunting 0.1.3).
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

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (champion #1 owned by daveey, #2 by
  daveey-1); the fillers are `line` and `pincer`. No `USE_BEDROCK` flag is needed because the LLM
  call is made by the **game** pod, not the player pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml` with the Nim `test` job
  replaced by cogame-moba's `uv sync --frozen && uv run pytest` job, and the `docker-smoke` and
  `wasm-viewer` jobs taken **unchanged** (including `<SEATS>` → `2`). `coworld-release.yml` and
  `coworld-submit.yml` are the templates, with `--timeout-seconds 300` added to the certify step.
  `tools/ci/docker_smoke.sh` is the template with `<slug>` → `magent-battle`,
  `<IMAGE>` → `coworld-magent-battle`, `<SEATS>` → `2`, committed **executable** (mode 100755), as is
  `tools/build_replay_viewer.sh`.

---

## Tests

`uv run pytest` runs everything; CI's `test` job runs the same command. Named tests, and the gate
each one is:

**Sim unit tests** (`tests/test_sim.py`)
1. `test_attack_only_hits_enemies` — an attack on an empty cell and an attack on a friendly unit both
   deal 0 damage and both still charge `attack_penalty`; only the enemy case pays
   `attack_opponent_reward`.
2. `test_damage_and_death` — five attacks kill a full-hp unit; the fifth attacker (and only it) gets
   `kill_reward`; the victim gets `dead_penalty` exactly once and vanishes from `occ`.
3. `test_overkill_order` — two attackers on a 1-damage-from-death unit: the lower unit id gets the
   kill, the higher one's attack is unregistered.
4. `test_recover_caps` — hp climbs by 1 per step and stops at 100; a dead unit never recovers.
5. `test_move_blocked` — a move into an occupied cell fails and the unit stays; a move into a cell
   vacated earlier in the same step succeeds; a move off the board fails.
6. `test_offset_tables` — the 12 move offsets are exactly `dx²+dy² ≤ 4` minus the centre and the 8
   attack offsets exactly `dx²+dy² ≤ 2.25` minus the centre, in the pinned order; the action space
   is 21.
7. `test_visibility` — an enemy at `dx²+dy² == 36` is visible, at 37 is not; visibility is the union
   over living friendlies only.
8. `test_controller_orders` — one test per verb asserting the target cell and the attack permission,
   including `focus` on an extinct squad degrading to `advance` and `retreat` never attacking.
9. `test_scoring_is_zero_sum` — over 500 randomised end states, `score[0] + score[1] == 0`, sign is
   correct, and a draw scores 0/0.
10. `test_end_conditions` — annihilation, mutual annihilation, and the step cap each produce the right
    `reason`, `winner` and `survivors`.
11. `test_step_budget` — 600 steps of a full 45×45 episode complete in < 3 s.

**Port fidelity** — `tests/test_upstream_constants.py` (the regex tripwire over
`vendor/upstream/battle.py`), `tests/test_generate_map.py` (spawn positions and the 81/81 and 25/25
counts), `tests/test_determinism.py` (re-run from the replay, byte-identical ticks). Described in
§Sim module; these are the permanent gates that a re-vendor cannot silently pass.

**Bounded orders / legality on the scripted baselines** (`tests/test_baselines.py`)
12. `test_baselines_are_bounded` — for 200 pseudo-random world states (varying alive counts, extinct
    squads, hp distributions, both map sizes) and for **both** `line` and `pincer`: the returned order
    list has **≤ 9 entries**, every `squad` is one of the seat's own nine ids with no duplicates,
    every `verb` is in the enum, every `hold` coordinate is on the board, every `focus` target is an
    **enemy** id that exists, every `flank` side is `left|right`, and the serialised reply is
    ≤ 2048 bytes. A baseline that ever proposes an illegal or unbounded order fails the build.
13. `test_fallback_is_the_pincer_function` — the engine's fallback path and the `pincer` baseline
    resolve to the same callable, so they can never drift.
14. `test_reply_validation` — the validator accepts the schema above, drops individually invalid
    orders while keeping the rest, rejects a non-object and a non-array `orders`, truncates `say` and
    `notes` on **rune** boundaries at 120/240 with 4-byte emoji at the boundary, and caps the read at
    8192 bytes.

**End-to-end episode writing a replay** (`tests/test_e2e.py`)
15. `test_episode_writes_artifacts` — run a real two-seat episode (`map_size 31`, `max_steps 200`,
    both seats scripted, no API key so the LLM client is `disabled`) through the engine against a
    temp-dir `COGAME_*` URI set; assert `results.json` and the `.replay` are written, `reason` is
    `complete`, `scores` sum to 0, and the results key set equals the manifest's `results_schema`
    key set exactly.
16. `test_no_seat_can_stall` — a seat that connects and then never answers, and a seat that never
    connects at all, both produce a finished episode inside the wall-clock budget, with `fallbacks`
    counted, `dead_seats` set, and one closed-schema `PLAYER_FAILURE_URI` payload.

**Strict-UTF-8 replay parse** (`tests/test_replay.py`)
17. `test_replay_is_strict_utf8_json` — take the replay from test 15, but with every capped field
    filled to exactly its cap with 4-byte emoji, and assert
    `json.loads(data.decode("utf-8", errors="strict"))` succeeds, the document has no lone surrogates,
    `format_version == 1`, the tick count matches `final_step`, `len(p) % 3 == 0` on every tick, and
    the file is < 4 MB.
18. `test_replay_is_self_sufficient` — the parsed document alone yields seat names, aliases, policy
    kinds, full config, seed, roster, every tick's positions and hp, every event, and the result: the
    viewer needs no other source.

**Manifest** (`tests/test_manifest.py`)
19. `test_manifest_pins` — `num_agents == 2` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; `len(players) ==
    len(certification.players) == 2`; no `tokens` in any `game_config`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level;
    `game.protocols.player` and `.global` both present as `{"type","value"}` objects; `game.docs.readme`
    + `pages`; `game.description` present and `game.tags` absent; `≥ 3` top-level tags;
    `player[].resources.limits.cpu == "1"`; every `wall_clock_budget_seconds ≤ 660`; and the manifest
    validates against the installed `coworld` CLI's own `validate_upload_manifest` /
    `_load_template_manifest` (run as a CI step — the collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_viewer.py` — static assertions, run in the `test` job)
20. `test_chrome_common_is_byte_identical` — sha256 of `client/chrome_common.js` equals the
    coworld-ctf file's sha256, pinned as a literal.
21. `test_broadcast_html_is_starter_plus_block` — the file begins with the starter's bytes up to the
    documented splice marker and only appends after it.
22. `test_battle_core_kept_functions` — the function bodies listed in §Viewer as "kept" are
    byte-identical to coworld-ctf's `broadcast_core.js`, including `pushFeed`'s signature.
23. `test_no_shadowed_chrome_aliases` — no identifier in the appended game block collides with any
    name in `chrome_common.js`'s alias list (the tandem hoisting trap); in particular the beat
    builder is `battleBeat`, not `markBeat`.
24. `test_beat_css_matches_emitted_kinds` — the set of `.beat-marker.<kind>` CSS rules equals exactly
    `{firstblood, rout, wipe, fallback, end}`.
25. `test_transport_and_360px_rules` — `#endcard { bottom: var(--band` is present, `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`, no game-block element is positioned inside the
    band, and the three 360 px rules of §"Legible at 360 px" exist.
26. `test_removed_elements_are_gone` — none of the removed ids (`#viewpanel`, `#minimap`, `#zoombar`,
    `#fpv*`, `#povBadge`, …) appears in the page or in `battle_core.js`.

**Viewer smoke — the bundle is EXECUTED, not merely built**
27. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs against **the replay `docker-smoke` produced** (downloaded as
    the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both places):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the
    bridge `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` (this is a fixed board, so `--strict-text-bounds` stays on).
28. **`tools/ci/renderer_fixture.html`** run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `say` at all**, so
    the smoke replay can never exercise the feed's text path (the cogchemists 2026-08-24 scar). The
    fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only
    the wasm entry (it does not re-implement the drawing — the particle-worlds 2026-08-26 scar),
    driving the real page with a full-cap 120-rune `say` on both seats at several canvas widths
    including 360 px.

---

## Out of scope (v1)

- **The other four MAgent scenarios.** `battlefield` (battle plus obstacles — the closest follow-up:
  it needs only an obstacle channel in the state, an obstacle layer in the replay config and a
  pathing tweak in the controller), `gather` (food resources and a mixed-motive score, which breaks
  the zero-sum integrity claim and needs a different scoring formula), `tiger_deer` (two agent types
  with a pairing kill rule and asymmetric seats), and `adversarial_pursuit` (asymmetric predator/prey
  seats). v1 ships **`battle` only**.
- **N-squad seating.** The idea's second seating option (one policy per squad, 18 seats) is not
  shipped: `num_agents` is fixed at 2 for every variant. Adding it later means a new variant with
  `num_agents: 18` and a per-squad observation, not a change to these rules.
- **Per-unit RL policies and pretrained MAgent weights.** No `.npy`/`.pt` weights are vendored, no
  inference module ships, and no seat receives the 13×13×5 observation tensor. This is why the port
  is a rules port rather than a wasm bit-exactness port (§Sim module).
- **Army sizes above 81 per side.** The idea mentions up to 1000 units; upstream's own default is 81
  per side at `map_size 45`, it is what makes the board legible at 360 px, and it is what fits the
  wall-clock budget. Larger armies are a `map_size` variant, not a v1 feature.
- **Anything derived per-unit from the LLM.** Commanders issue nine squad orders; they never name a
  unit, a cell-by-cell path or a raw action index.
- **Live spectating.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Terrain generation, elevation, ranged units, morale, reinforcements, supply** — none of these
  exist upstream in `battle` and none are invented here.
- **`minimap_mode` and `extra_features` observations.** Upstream defaults (`False`/`False`) are kept;
  the commander's fog-of-war summary replaces them.
