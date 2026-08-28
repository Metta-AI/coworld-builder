# cogame-derks-gym — design note (2026-08-28)

Forked from **`Metta-AI/cogame-moba`**, read at its read-only mount `/workspace/starters/cogame-moba`.
**Every convention there holds here unless this note says otherwise.** This coworld is a *mod* of
that repo, not a green field: the vendored PufferLib Ocean MOBA sim (`vendor/upstream/moba.h`
@ PufferAI/PufferLib `c5d3c637`), the four-patch set, the wasmtime sim host, the lockstep engine,
the aiohttp Coworld-contract server, the binary replay, the emscripten/raylib static replay viewer
and the `tools/build_replay_viewer.sh` bundle hook are all **inherited unchanged in shape**. What
this note *adds* is a one-turn, simultaneous, hidden **pre-match loadout draft** and everything
that must follow it (protocol step, loadout application, replay records, draft-reveal viewer
screen, variants, tests). Starter choice needs no argument: the game shape is "bit-exact port of an
existing external C/RL env" and this repo *is* that port — `playbooks/make-coworld.md` §Phase 0 row
3, and the idea itself names cogame-moba as the parent.

**Source idea (verbatim):**

```
DERK Derk's Gym (mod of cogame-moba) — add a pre-match loadout draft to the existing Puffer MOBA

EXTENSION of Metta-AI/cogame-moba — PufferLib's Ocean MOBA already runs as a bit-exact wasm coworld (lockstep websocket, static replay viewer). Derk's Gym's distinguishing idea is the draft phase: each creature picks a weapon / ability / tail item from a catalog before the fight, so the policy is metagame + micro. Add that as a variant of cogame-moba: a draft protocol step (LLM-friendly) feeding item stats into the existing sim, with a draft-reveal screen in the viewer. Keep the Puffer fidelity gate for the un-drafted mode.

Seats: 3v3 (as Puffer MOBA)
Motive: team zero-sum with a pre-game draft
Policy interface: draft choice (once) + cogame-moba's per-tick protocol
Integrity: server-assigned teams; anonymous aliases.

Source: gym.derkgame.com; PufferLib Ocean MOBA; github.com/Metta-AI/cogame-moba.
```

---

## The game

### Shape and seats

`num_agents` = **6**. Six policy seats, three per team, one hero each. Fixed for both variants, the
certification fixture, and `<SEATS>` in `tools/ci/docker_smoke.sh`.

**Factual correction the builder must not "fix" back:** the idea says "Seats: 3v3 (as Puffer MOBA)".
Puffer MOBA is **5v5** — `#define NUM_PLAYERS 10` (`vendor/upstream/moba.h:19`), and `init_moba`
spawns exactly five heroes per team in the fixed role order support, assassin, burst, tank, carry
(`moba.h:1636-1749`). The idea's seat count is the binding requirement; the sim's hero count is
inviolable (touching it destroys the fidelity gate and every pretrained weight). Both are satisfied
by seating **six of the ten heroes** and running the other four in-process off the vendored
pretrained network:

| seat | alias (in-game) | pid | team | role | lane | base_health / base_mana / base_damage / hp_gain / mana_gain / dmg_gain |
|---|---|---|---|---|---|---|
| 0 | `Cog-Alpha`   | 0 | radiant | support  | 2 | 500 / 250 / 50 / 100 / 50 / 10 |
| 1 | `Cog-Bravo`   | 1 | radiant | assassin | 1 | 400 / 300 / 50 / 100 / 65 / 10 |
| 2 | `Cog-Charlie` | 2 | radiant | burst    | 1 | 400 / 300 / 50 /  75 / 90 / 10 |
| 3 | `Cog-Delta`   | 5 | dire    | support  | 5 | 500 / 250 / 50 / 100 / 50 / 10 |
| 4 | `Cog-Echo`    | 6 | dire    | assassin | 4 | 400 / 300 / 50 / 100 / 65 / 10 |
| 5 | `Cog-Foxtrot` | 7 | dire    | burst    | 4 | 400 / 300 / 50 /  75 / 90 / 10 |

(Stats and lanes are verbatim from `moba.h:1666-1716`; dire lanes are `+3`.)

**House heroes** — pids 3, 4 (radiant tank, carry) and 8, 9 (dire tank, carry) — are not seats.
The game server drives them itself, in-process, through `build/moba_brain.wasm` (the vendored
`puffernet.h` + `moba_weights.bin` compiled to wasm — the starter's `players/baseline_player.py`
`MobaBrain`, reused as a library). They are cosmetically named `House-Tank-R`, `House-Carry-R`,
`House-Tank-D`, `House-Carry-D` and always run the **neutral loadout** (all-zero deltas).

Why this mapping and not "give two seats two heroes each": ten heroes do not divide into six equal
seats, and asymmetric seats (one hero for some seats, two for others) make league ranking unfair
and the draft incoherent. Every seat here is identical in kind: one hero, one loadout, one lane
role. Symmetry across teams is exact (support/assassin/burst vs support/assassin/burst), and the
two house roles are the same on both sides, so the episode stays zero-sum and mirror-fair. All ten
heroes stay alive, so the map still plays like a MOBA (creep waves, tower sieges, jungle) instead
of a four-hole skirmish. The sim is untouched: `num_agents` inside the wasm stays **10** and
`env->script_opponents` stays **0**, exactly as in the starter — so `compute_observations` writes
all ten 510-byte rows and the replay body stays 60 bytes per tick.

### Arena and rules (inherited, stated in full so the note is implementable alone)

- **Map**: the upstream 128×128 Dota-shaped map (`vendor/upstream/game_map.h`), three lanes per
  side (six creep lanes), 24 towers, 18 neutral camps of 4.
- **Towers**: `TOWER_HEALTH` 1800–2100 for lane towers, **4500 for each Ancient**
  (`moba.h:66`, indices 22 = dire Ancient, 23 = radiant Ancient); `TOWER_DAMAGE` 110–175 per shot
  for lane towers and **0 for both Ancients** (`moba.h:65`), scan radius `TOWER_VISION` 5
  (`moba.h:45`). A tower out-damages any hero basic attack by an order of magnitude and cannot be
  out-ranged; Ancients cannot shoot at all.
- **Creeps**: a wave of 5 creeps per lane × 6 lanes spawns every **150 ticks**
  (`moba.h:1366`); creeps push waypoints and auto-attack.
- **Neutrals**: 18 camps × 4 respawn every **600 ticks** (`moba.h:1392`).
- **Heroes**: vision range 5 → an 11×11 crop observation; `agent_speed` 1.0; passive regeneration
  **+2 health and +2 mana per tick** (`moba.h:1462-1471`); `basic_attack_cd` 8 ticks;
  `base_damage` 50 (`moba.h:1654-1656`). Level from cumulative xp via `XP_FOR_LEVEL`
  (`moba.h:56`); on level-up and on every respawn the sim re-derives
  `max_health = base_health + level*hp_gain_per_level`,
  `max_mana = base_mana + level*mana_gain_per_level`,
  `damage = base_damage + level*damage_gain_per_level` (`moba.h:648-650`, `moba.h:791-793`).
  **This is the hook the whole draft rides on** — see §Sim module.
- **Skills**: three per role, on cooldown and mana, tried in order Q → W → E then basic attack
  (`moba.h:1533-1541`). support = hook / aoe-heal / stun; assassin = aoe-minions / tp-damage /
  move-buff; burst = nuke / aoe / aoe-stun; tank = aoe-dot / self-heal / engage-aoe; carry =
  retreat-slow / slow-damage / aoe (`moba.h:1670-1748`).
- **Actions**: upstream MultiDiscrete `[7,7,3,2,2,2]` = `vel_y`, `vel_x` (0–6, 3 = zero velocity),
  target filter (0 = all hostiles, 2 = heroes+towers only), and Q/W/E flags. NOOP `[3,3,0,0,0,0]`.
- **Observations**: 510 opaque bytes per hero (11·11·4 crop + 26 self bytes). Transported verbatim,
  never re-encoded.

### The draft (the new part)

One turn, before tick 0. **Simultaneous and hidden**: all six seats decide at the same time and no
seat sees any other seat's pick before committing (that hiding is the metagame — a counter-draft
must be a *prediction*, not a reaction). There is **no shared pool and no exclusivity**: two heroes,
even on the same team, may take the same item, so there is nothing to contend for and therefore no
pick-order tie-break to define. This is the deliberate simplification that lets the phase be one
parallel batch instead of a six-round snake draft.

Each seat fills **three slots — ARM, TAIL, MISC — with exactly one item each**. Catalog v1
(`catalog_version: "v1"`, 12 items). Deltas are **additive** to the hero's own base stats above.

**Slot ARM (weapon)**

| id | display name | deltas |
|---|---|---|
| `arm_none` | Bare Claws | *(none — all deltas 0)* |
| `arm_blaster` | Blaster | `base_damage +15` |
| `arm_cleaver` | Cleaver | `base_damage +35`, `basic_attack_cd +3` |
| `arm_needler` | Needler | `basic_attack_cd −3`, `base_damage −10` |

**Slot TAIL**

| id | display name | deltas |
|---|---|---|
| `tail_none` | Stub Tail | *(none)* |
| `tail_plate` | Iron Plate | `base_health +200`, `basic_attack_cd +2` |
| `tail_stinger` | Stinger | `damage_gain_per_level +8` |
| `tail_rotor` | Rotor Tail | `move_speed +0.15`, `base_health −100` |

**Slot MISC (ability)**

| id | display name | deltas |
|---|---|---|
| `misc_none` | Nothing | *(none)* |
| `misc_regen` | Regen Cell | `hp_gain_per_level +60` |
| `misc_battery` | Mana Battery | `base_mana +150`, `mana_gain_per_level +30` |
| `misc_focus` | Focus Chip | `base_damage +10`, `hp_gain_per_level −25` |

The `*_none` items exist and are zero-delta on purpose: the **neutral loadout**
`{arm_none, tail_none, misc_none}` is both the house heroes' loadout and the server's fallback, and
it makes the un-drafted variant bit-identical to upstream by construction rather than by a code
path.

**Application order and clamps.** Deltas are summed in the fixed order ARM → TAIL → MISC (addition
is commutative, but the order is pinned so `applied` values are reproducible bit-for-bit), then each
field is clamped:

| field | default | clamp |
|---|---|---|
| `base_health` | 300–700 by role | `[150, 1200]` |
| `base_mana` | 200–300 by role | `[100, 600]` |
| `base_damage` | 50 | `[20, 120]` |
| `basic_attack_cd` | 8 | `[3, 16]` (integer ticks) |
| `move_speed` | 1.0 | `[1.0, 1.5]` |
| `hp_gain_per_level` | 50–150 by role | `[0, 300]` |
| `mana_gain_per_level` | 50–90 by role | `[0, 200]` |
| `damage_gain_per_level` | 10–25 by role | `[0, 60]` |

`move_speed` is clamped at a **floor of 1.0** and no item lowers it, for a fidelity reason the
builder must preserve: `compute_observations` writes `obs_extra[6] = player->move_speed` as an
`unsigned char` (`moba.h:486`), so a speed of 0.9 would emit a `0` the pretrained policies never
saw in training, whereas 1.15 still casts to `1`. For the same reason no item can push
`base_damage/50` (`obs_extra[5]`) or `basic_attack_cd` (`obs_extra[14]`) outside the small-integer
band those bytes already occupy: at level 0, `damage/50` ranges 0–2 (default 1) and
`basic_attack_cd` ranges 3–16 (default 8). Loadouts are therefore **physically real but only weakly
encoded in the obs bytes**: the trained networks keep consuming in-distribution observations and
feel the items through the physics, which is exactly the property that makes the mod safe.

Nothing else changes: no cost, no budget, no per-team uniqueness, no in-match item purchases.

### Turn/tick structure and exact resolution order

**Phase A — connect** (before the wall-clock timer starts). The server waits for all six seats or
`player_connect_timeout_seconds` (default 60), whichever comes first. Never-connected seats are
reported to `COGAME_PLAYER_FAILURE_URI` (lowest slot only, closed schema
`{"message","failed_policy_index"}`) and play the neutral loadout + NOOP.

**Phase B — draft** (one turn, engine wall-clock timer starts here):

1. Server builds the six per-seat draft observations (§Server, player, protocol) and sends them as
   **one parallel batch** — a single `asyncio.gather` over all six seats with one shared deadline
   `draft_deadline_ms` (default 45 000 ms).
2. Each seat replies at most one `{"phase":"draft", "picks":[…]}` message. Later messages for the
   draft phase are ignored.
3. Resolution, per seat, in this order:
   1. No reply by the deadline → neutral loadout, `fallback_cause: "timeout"`.
   2. Seat never connected / socket closed → neutral loadout, `fallback_cause: "disconnected"`.
   3. Frame larger than 4096 bytes → neutral loadout, `fallback_cause: "oversize"` (frame dropped
      before JSON parse).
   4. Not valid JSON, not an object, `phase != "draft"`, or `picks` not a 1-element array of
      objects → neutral loadout, `fallback_cause: "wrong_shape"`.
   5. Any of `arm`/`tail`/`misc` missing, not a string, longer than 24 characters, or not an id of
      the **matching slot** in catalog v1 (case-sensitive, exact match after stripping leading and
      trailing ASCII spaces) → neutral loadout **for the whole seat**, `fallback_cause:
      "unknown_item"`. Partial acceptance is deliberately not allowed: it would let a seat launder
      a typo into a free reroll of one slot.
   6. Otherwise → accepted, `fallback_cause: "none"`, `fallback: false`.
   7. `note`, if present and a string, is truncated to **120 characters on Unicode-scalar (rune)
      boundaries** — never mid-codepoint, never splitting a surrogate pair — and stripped of C0/C1
      control characters. Absent/non-string → `""`. A bad `note` never invalidates the picks.
4. House heroes 3, 4, 8, 9 get the neutral loadout with `source: "house"`.
5. Deltas summed and clamped (§The draft) → the ten `applied` stat blocks.
6. `apply_loadout` is called once per pid, in ascending pid order, on the freshly initialised sim
   (§Sim module). The un-drafted variant skips steps 1–6 entirely.
7. The draft-reveal record for all ten pids is written to the replay header, to `results.draft`,
   and pushed to every seat as `{"phase":"draft_result", …}` (no reply expected) and to the
   `/global` feed.

**Phase C — play**, per tick, in this order:

1. Engine checks, in this order: `sim.done()` (patch-0003 flag) → tick counter ≥ `max_ticks` →
   elapsed ≥ `wall_clock_budget_seconds`. Any of them breaks the loop.
2. `tick = sim.tick()`, `obs = sim.observations()` — a fresh (10, 510) uint8 copy.
3. **House actions first, deterministically**: four `MobaBrain.forward` calls in ascending pid
   order 3, 4, 8, 9, each fed that pid's 510 obs bytes. Ascending order is load-bearing — the brain
   module has one shared `rand()` stream and puffernet *samples* from the softmax.
4. All six seats' `get_actions(tick, obs_row)` are awaited as **one parallel batch** under
   `tick_deadline_ms` (default 100 ms).
5. Missing / late / wrong-tick / malformed / non-finite / wrong-shape replies become NOOP
   `[3,3,0,0,0,0]`, counted per seat in `noop_ticks` and `noop_causes`
   (`timeout|malformed|wrong_tick|disconnected|host_error`). Strike rule unchanged: 10 consecutive
   fallbacks mark a seat dead (its websocket is force-closed, it is probed non-blockingly every
   tick, and the first valid reply revives it).
6. Finite values are truncated toward zero and clamped per column to `0..ACT_HIGH[col]-1`, then the
   full (10, 6) matrix is written to the sim.
7. `sim.step()` → the vendored `c_step`, whose internal order is: clear per-entity transients
   (`target_pid`, `attack_aoe`, `last_x/y`, `is_hit`) → `step_neutrals` → `step_creeps` (wave spawn
   when `tick % 150 == 0`) → `step_towers` → `step_players` (regen, status, cooldowns, action
   decode, Q→W→E→basic) → `tick += 1` → Ancient check sets `done`/`winner` and skips upstream's
   auto-reset (patch 0003).
8. Rewards accumulated per seat; the tick's post-clamp 60 action bytes appended to the replay.
9. Event extraction: the engine reads `agent_stat(pid, which)` for `which ∈ {0 level, 1 kills,
   2 deaths, 3 towers_killed}` for all 10 pids (40 wasm calls/tick) and emits an event on every
   increase (§Server, player, protocol — event vocabulary).
10. Patch-0004 fault flag polled; nonzero ends the episode as `sim_fault`.

### End conditions, scoring, and `end_reason`

`end_reason` is a **closed 4-value enum**, unchanged from the starter (triple-synced: the engine
literals, the manifest `results_schema`, and `tools/ci/docker_smoke.sh`). No new value is added —
a draft failure is never fatal, it degrades to the neutral loadout.

| `end_reason` | condition | winner |
|---|---|---|
| `ancient` | an Ancient reached 0 health | the sim's `winner` (0 radiant, 1 dire; simultaneous double-kill goes to dire, patch 0003) |
| `tick_cap` | tick counter reached `max_ticks` (6000) | more remaining Ancient health; equal health → `null` (draw) |
| `wall_clock` | **the deadline case** — elapsed since the draft started reached `wall_clock_budget_seconds` (645 s) | same Ancient-health tiebreak as `tick_cap` |
| `sim_fault` | patch-0004 guard tripped or a wasmtime trap | `null`; draw scores; partial replay + schema-complete results still written |

**Scoring.** `scores[seat] = 1.0` on a win, `0.5` on a draw, `0.0` on a loss — **higher is better**,
per seat, zero-sum across the six seats (a win + loss pair sums to 1.0 per opposing pair, and the
whole array sums to 3.0). The league ranks by mean `scores`. Identical to the starter; the draft is
*not* separately scored, because the whole point is that draft quality shows up as match wins. The
sim's own training rewards ride alongside as `reward_sums` (observability only, never ranked).

---

## Decisions: LLM with scripted fallback

**The split, decided:** an LLM makes the **draft** decision; per-tick micro is always local. A MOBA
tick is 100 ms and an episode is 6000 ticks — no LLM plays that, and pretending otherwise would
produce a coworld whose champions are 6000 NOOPs. The idea says so itself ("the policy is metagame +
micro"), and the metagame is where a prompt policy has real leverage: 4³ = 64 loadouts per hero,
counter-drafting against an unseen opponent, one decision that shapes 6000 ticks.

One entrypoint, one image, env-switched:

```
python -m players.derk_player
  PLAYER_PROMPT=<prompt name>       -> LLM draft  + puffernet micro   (champion)
  PLAYER_SCRIPTED=<baseline name>   -> scripted draft + its micro     (filler / cert fixture)
```

Both unset → `PLAYER_SCRIPTED=puffer-forge`, so a bare `docker run` plays. Both set →
`PLAYER_PROMPT` wins and the choice is logged to stderr. An unknown `PLAYER_SCRIPTED` value exits 2
with the list of legal names (a typo must fail loudly, not silently ship a different policy).

### LLM prompt policies (champions)

Two prompts, both `PLAYER_PROMPT`, both Anthropic Messages API, model `claude-sonnet-4-5`,
`max_tokens: 400`, one call per episode, per-call timeout **20 s**. Key from `ANTHROPIC_API_KEY`
(put after `upload-coworld` as secret `anthropic_api_key`).

**`derk-drafter-v1`** — system prompt, verbatim:

```
You are drafting the loadout for one cog in Derk's Gym, a 3v3 MOBA skirmish on the
Puffer MOBA map. You pick exactly one ARM, one TAIL and one MISC item from the catalog
you are given. The items change your cog's physical stats for the whole match; you do
not control the cog after the draft, a trained network does.

Radiant and Dire each field three drafted cogs (support, assassin, burst) plus two
house-controlled cogs (tank, carry) that always run the neutral all-zero loadout.
The match is won by destroying the enemy Ancient (4500 HP, deals no damage); if
neither Ancient falls by the tick cap the team with more Ancient health wins.
Lane towers hit for 110-175 per shot with the same scan radius as a cog, so diving
one without a creep wave is death. Cogs regenerate 2 health and 2 mana per tick and
gain stats per level from their per-level gain values.

All six drafts are simultaneous and hidden: you cannot see what anyone else picked.

Answer with a single JSON object and nothing else:
{"arm":"<id>","tail":"<id>","misc":"<id>","note":"<=120 chars"}
Use only ids from the catalog you were given. No prose, no code fences, no markdown.
```

User message: the server's draft observation object serialised as compact JSON, minus
`deadline_ms`.

**`derk-metagamer-v1`** — same system prompt with this paragraph appended before the answer format:

```
Think about the metagame before you answer. Assume opponents over-value raw damage
and under-value the per-level gain values, which compound: a cog that survives to
level 8 with a high hp_gain_per_level out-trades a cog that bought flat damage.
Your note field must name, in a few words, the enemy build you are countering.
```

Parsing: the reply must be exactly one JSON object (a single leading/trailing code fence is
stripped before parsing — one tolerance, stated, so it is testable). Then the same legality check
the server applies.

**Degrade, never hang (player side):** timeout, transport error, non-JSON, or an id outside the
catalog → **one retry** with `temperature: 0` and the reminder line `Reply with the JSON object
only.` → on second failure, `puffer-forge`'s draft rule, logged as
`draft_fallback=scripted reason=<timeout|parse|illegal>`. `ANTHROPIC_API_KEY` unset → no call at
all, straight to the scripted rule, logged once. The 20 s + 20 s worst case fits inside the server's
45 s draft deadline, so a doubly-failing champion still submits a legal loadout.

**Micro layer for both prompts:** `MobaBrain` on `build/moba_brain.wasm` — the vendored pretrained
network, brain instance 0 for the seat's single hero, seeded by `COGAME_PLAYER_SEED` (default 1).
Byte-identical to the starter's `BaselinePolicy`.

### Scripted baselines (fillers, cert fixture)

**`puffer-forge`** — the certification-fixture player and the default.
*Draft rule* (deterministic, no RNG, from `hero.role` in the draft observation):

| role | arm | tail | misc |
|---|---|---|---|
| support | `arm_blaster` | `tail_plate` | `misc_battery` |
| assassin | `arm_needler` | `tail_rotor` | `misc_focus` |
| burst | `arm_blaster` | `tail_stinger` | `misc_battery` |
| anything else | `arm_none` | `tail_none` | `misc_none` |

`note` omitted. *Micro*: `MobaBrain`, as above.

**`lane-brawler`** — the second filler.
*Draft rule* (deterministic, derived from the observed base stats, so it adapts if the role table
ever changes):

```
arm  = arm_cleaver  if hero.base_health >= 500 else arm_needler
tail = tail_plate   if hero.hp_gain_per_level >= 100 else tail_rotor
misc = misc_regen   if hero.base_health < 500 else misc_focus
note = "brawl build"
```

*Micro*: the starter's `players/scripted_player.py` `ScriptedPolicy` unchanged — the per-hero
finite-state lane-push bot (tile-id-only crop decode, static BFS nav grid, PUSH / SIEGE-HOLD /
RETREAT modes, retreat at health ≤ 3/10, skill flags by mode).

Both baselines are **bounded by construction**: three catalog ids from a fixed table, and six
integers per tick already inside `0..ACT_HIGH-1`. A test asserts it (§Tests).

### Wall-clock arithmetic (must fit inside 60 % of `episodeTimeoutSeconds` = 720 s)

```
connect          player_connect_timeout_seconds  =  60 s   (before the engine timer)
draft            1 turn x draft_deadline_ms 45 s  =  45 s   (one parallel batch of 6)
play             max_ticks 6000 x tick_deadline_ms 100 ms = 600 s   (absolute worst case:
                 every seat burning its full deadline every tick)
                 ------------------------------------------------
worst case total 60 + 45 + 600                    = 705 s   <  720 s  (0.60 x 1200 s)
engine hard stop wall_clock_budget_seconds        = 645 s   (draft 45 + play 600), so the
                 episode ends itself with artifacts written even if the clock is eaten
```

Realistically play is far faster: a local puffernet forward is sub-millisecond and the sim step is
a few milliseconds, so the six seats answer in ~1–3 ms and the 100 ms deadline is never reached;
6000 ticks at the strike-bounded pace lands in tens of seconds. The 705 s figure is the *ceiling*,
and it is the number that matters — the container never overruns and the episode is never silently
discarded. The strike rule additionally caps a silent seat at `10 × 100 ms = 1 s` of wall clock for
the whole episode instead of `6000 × 100 ms`.

Playback length for a spectator: 6000 ticks at the upstream cadence of 5 ticks/s = 1200 s at 1×,
which is why the viewer keeps the starter's 1×/4×/16×/64× speed select (64× → 18.75 s).

Whether 6000 ticks is enough for an Ancient to fall: 6000 ticks = 40 creep waves and 10 neutral
respawns, and heroes reach level ~8–12 on `XP_FOR_LEVEL`. Many episodes will still end at
`tick_cap` with the Ancient-health tiebreak; that is an accepted, certified outcome (the starter
documents the same for its 2000-tick cert fixture) and it is the price of the 720 s pin. The
tiebreak is decisive far more often than a draw, because Ancient chip damage is common.

---

## Sim module

**No new patch.** The patch set stays at exactly four —
`0001-render-guard`, `0002-seed`, `0003-done-flag`, `0004-fault-flag` — and
`vendor/upstream/` stays byte-pristine at commit `c5d3c637`. The draft needs no upstream change
because every stat it touches is already a field of `struct Entity` (`moba.h:162-204`) that
`spawn_player` (`moba.h:641-680`) and the level-up path (`moba.h:791-793`) re-read on **every
respawn and every level-up**. Writing the base fields once, before tick 0, therefore makes the
loadout permanent for the whole match for free. This is the single most important implementation
fact in this note.

### Files forked from the starter

Kept **verbatim** (path unchanged unless noted):

- `vendor/upstream/*`, `vendor/UPSTREAM.md`, `vendor/LICENSE-pufferlib` — byte-pristine.
- `sim/patches/0001..0004`, `sim/apply_patches.sh`, `sim/build_sim.sh`, `sim/build_brain.sh`,
  `sim/brain_shim.c`.
- `sim/shim_common.h` — `moba_configure` (the trained-on env values) and `moba_state_digest`
  unchanged. Loadouts are **not** put here: they are per-hero and per-episode, not env config.
- `server/cogame_moba/{engine,uris,replay,sim}.py` structure, `players/{client,scripted_player,
  random_player}.py`, `tools/build_replay_viewer.sh`, `tools/ci/next_coworld_version.py`.

Renamed: the Python package `server/cogame_moba/` → **`server/cogame_derks_gym/`** (module names
inside unchanged); `build/moba_sim.wasm` → `build/derk_sim.wasm`, `build/moba_brain.wasm` →
`build/derk_brain.wasm`, `viewer/dist/moba_viewer.js` → `viewer/dist/derk_viewer.js`
(one rename pass in `sim/build_*.sh`, `Dockerfile`, `sim.py`, `viewer/index.html`).

### Additions to `sim/shim.c`

```c
// Absolute, post-clamp stat block for one hero. Called AFTER moba_init
// (allocate_moba + c_reset) and BEFORE the first moba_step, once per pid,
// ascending pid order. Touches no RNG, no map cell, no allocation.
apply_loadout(int pid, float base_health, float base_mana, float base_damage,
              int basic_attack_cd, float move_speed,
              int hp_gain_per_level, int mana_gain_per_level,
              int damage_gain_per_level)
hero_stat(int pid, int which) -> float   // read-back for tests; which codes:
   // 0 base_health 1 base_mana 2 base_damage 3 basic_attack_cd 4 move_speed
   // 5 hp_gain_per_level 6 mana_gain_per_level 7 damage_gain_per_level
   // 8 max_health 9 max_mana 10 damage 11 health 12 mana 13 level
loadout_digest(void) -> unsigned int     // FNV-1a over the 10x8 applied float32 table
```

`apply_loadout` body, in this exact order (it must reproduce `spawn_player`'s derivation without
re-spawning, because a re-spawn would draw `rand()` and desync the seeded stream):

1. Bounds-check `pid` in `[0, NUM_PLAYERS)`; return on failure.
2. Write the eight base fields.
3. `max_health = base_health + level*hp_gain_per_level`;
   `max_mana = base_mana + level*mana_gain_per_level`;
   `damage = base_damage + level*damage_gain_per_level`.
4. `health = max_health`; `mana = max_mana` (the hero is at full health at tick 0 anyway, so with a
   zero-delta block this is a byte-identical no-op — asserted by a test).
5. Record the block in the module-level `g_applied[pid][8]` table that `loadout_digest` hashes.

The Python host `sim.py` gains `apply_loadout(pid, block)`, `hero_stat(pid, which)` and
`loadout_digest()` wrappers with the same argument validation discipline as `set_actions`: raise on
non-finite or out-of-range values at the wasm boundary; the graceful degrade lives one layer up.

`applied` values crossing the JSON boundary are serialised as the **exact float32** value
(`struct.unpack("<f", struct.pack("<f", v))[0]`), so the float32 → double → float32 round trip
through the replay header into the viewer is lossless.

### Additions to `sim/viewer_main.c`

The viewer re-simulates, so it must apply the same loadouts after every `sim_fresh()` (which
`viewer_seek` calls on every seek). C never parses the replay header JSON, so JS pushes the table
in:

```c
viewer_set_loadout(int pid, float bh, float bm, float bd, int cd, float ms,
                   int hpg, int mng, int dmg)   // fills g_loadout[pid][8], marks it set
viewer_loadout_digest(void) -> unsigned int      // must equal the header's loadout_digest
viewer_ancient_health(int team) -> float         // scorebug health bars
viewer_agent_stat(int pid, int which) -> int     // scorebug K/D/level/towers (shim.c codes)
viewer_hero_positions(float* out) -> int         // 10 x (x, y, team, alive) for the minimap
```

`sim_fresh()` applies `g_loadout[pid]` for every pid whose flag is set, immediately after
`c_reset(&env)` — identical placement to the server's Phase-B step 6. With no flags set (an
un-drafted replay, or the starter's own replays) nothing is applied and re-simulation is exactly
today's behaviour. All new exports are added to `VIEWER_EXPORTS` in `sim/build_viewer.sh`; the
**link flags are not touched** (see §Viewer).

### The fidelity gate stays the gate

`tests/test_fidelity.py` is inherited **unchanged and inviolable**: pristine build (render guard
only) vs fully patched build, same seed, the same multi-thousand-tick random action log,
byte-identical obs and reward streams, with the tick-count floor assertion. Since no patch is
added, it cannot regress. It is joined by a second, mod-specific gate:

**zero-loadout identity** — the production sim run for 500 ticks *with* an all-neutral
`apply_loadout` call for all ten pids must produce byte-identical obs, rewards and
`state_digest()` to the same run *without* any `apply_loadout` call. This is what "keep the Puffer
fidelity gate for the un-drafted mode" means operationally, and it is the test that would catch a
future `apply_loadout` that accidentally spawns, allocates or draws RNG.

---

## Server, player, protocol

### Config (`COGAME_CONFIG_URI`, `config_schema`)

Inherited fields: `players` (exactly 6), `tokens` (exactly 6), `seed` (optional; derived from
`secrets.randbits(32)`, masked to u32, and recorded), `max_ticks`, `tick_deadline_ms`,
`player_connect_timeout_seconds`, `wall_clock_budget_seconds`, `num_agents`.

Removed: **`heroes_per_seat`** — the seat→pid map is now the fixed tuple `SEAT_HERO_PIDS =
(0, 1, 2, 5, 6, 7)` in `defaults.py`, with `HOUSE_HERO_PIDS = (3, 4, 8, 9)`. `num_agents` is
constrained to `6` exactly (min 6, max 6, default 6) and validated against `len(players)`.

Added:

| field | type | default | meaning |
|---|---|---|---|
| `draft_enabled` | boolean | `true` | `false` = the Puffer-fidelity mode: no draft turn, no `apply_loadout` call at all |
| `draft_deadline_ms` | integer ≥ 1000 | `45000` | the single draft turn's shared wall-clock deadline |
| `catalog_version` | string enum `["v1"]` | `"v1"` | pinned so a future catalog cannot silently re-interpret an old replay |

`config.to_dict()` (which is what lands in the replay header and must exclude tokens) gains all
three.

### Draft-phase messages

**server → player** (one per seat, sent as one parallel batch):

```json
{"phase": "draft",
 "seat": 2,
 "alias": "Cog-Charlie",
 "team": "radiant",
 "hero": {"pid": 2, "role": "burst", "lane": 1,
          "skills": ["burst_nuke", "burst_aoe", "burst_aoe_stun"],
          "base_health": 400, "base_mana": 300, "base_damage": 50,
          "basic_attack_cd": 8, "move_speed": 1.0,
          "hp_gain_per_level": 75, "mana_gain_per_level": 90,
          "damage_gain_per_level": 10},
 "teammates":  [{"alias": "Cog-Alpha", "role": "support"},
                {"alias": "Cog-Bravo", "role": "assassin"}],
 "opponents":  [{"alias": "Cog-Delta", "role": "support"},
                {"alias": "Cog-Echo", "role": "assassin"},
                {"alias": "Cog-Foxtrot", "role": "burst"}],
 "house_heroes": [{"team": "radiant", "role": "tank"}, {"team": "radiant", "role": "carry"},
                  {"team": "dire", "role": "tank"}, {"team": "dire", "role": "carry"}],
 "catalog": {"version": "v1",
             "arm":  [{"id": "arm_none", "name": "Bare Claws", "deltas": {}},
                      {"id": "arm_blaster", "name": "Blaster", "deltas": {"base_damage": 15}},
                      {"id": "arm_cleaver", "name": "Cleaver",
                       "deltas": {"base_damage": 35, "basic_attack_cd": 3}},
                      {"id": "arm_needler", "name": "Needler",
                       "deltas": {"basic_attack_cd": -3, "base_damage": -10}}],
             "tail": [ ... 4 items ... ],
             "misc": [ ... 4 items ... ]},
 "clamps": {"base_health": [150, 1200], "base_mana": [100, 600], "base_damage": [20, 120],
            "basic_attack_cd": [3, 16], "move_speed": [1.0, 1.5],
            "hp_gain_per_level": [0, 300], "mana_gain_per_level": [0, 200],
            "damage_gain_per_level": [0, 60]},
 "match": {"max_ticks": 6000, "tick_deadline_ms": 100, "ancient_health": 4500,
           "creep_wave_every": 150, "tower_damage": [110, 175], "regen_per_tick": 2},
 "deadline_ms": 45000}
```

**Visible to a seat in the draft:** its own hero's identity, role, lane, skills and exact base
stats; the roles and aliases of all five other seats and the four house heroes; the entire catalog
with exact deltas; the clamp table; the match constants; its own deadline.
**Hidden:** every other seat's pick (this is the simultaneity), the sim `seed`, real player names
of any seat including its own, the identity of the policies behind the aliases, and everything the
per-tick obs already hides (fog outside the 11×11 crop).

**player → server:**

```json
{"phase": "draft",
 "picks": [{"arm": "arm_cleaver", "tail": "tail_plate",
            "misc": "misc_regen", "note": "tanky mid, out-scale the carry"}]}
```

Field caps: `phase` ≤ 16 chars (must equal `"draft"`); `picks` array length exactly 1;
`arm`/`tail`/`misc` ≤ 24 chars each; **`note` ≤ 120 characters, truncated on rune boundaries**;
whole frame ≤ 4096 bytes. `note` is the only free-text field in the entire protocol.

**server → player** after resolution (informational, no reply):

```json
{"phase": "draft_result",
 "loadouts": [ <the ten draft records, alias-only, in pid order> ]}
```

The records here carry `alias`, `role`, `team`, `picks`, `note`, `source`, `fallback` and
`applied` — never real player names.

### Per-tick messages: unchanged, byte-for-byte

```
server -> player   {"tick": t, "obs": ["<base64 510B>"]}
player -> server   {"tick": t, "actions": [[a0..a5]]}
server -> player   {"done": true, "result": {...}}
```

Deliberate compatibility property: an **existing cogame-moba policy container plays
cogame-derks-gym unmodified**. It ignores the `phase` messages, eats one 45 s draft timeout, gets
the neutral loadout, and then plays every tick normally. Messages with an unrecognised `phase` are
ignored by both sides; a `{"tick": …}` reply arriving during the draft turn is ignored and counted
as `draft_wrong_phase` in the log (it does not consume the draft turn).

Auth, reconnects and errors are the starter's: `GET /player?slot=N&token=T`, 403 fatal on bad
slot/token, 409 retryable on an occupied slot, ~20 s websocket heartbeat, reconnect resumes at
whatever tick the server sends next.

### Two name spaces

- **In-game, everywhere a policy can see it**: anonymous aliases only — `Cog-Alpha`, `Cog-Bravo`,
  `Cog-Charlie`, `Cog-Delta`, `Cog-Echo`, `Cog-Foxtrot` by seat index, and `House-Tank-R`,
  `House-Carry-R`, `House-Tank-D`, `House-Carry-D`. Teams are **server-assigned** (seats 0–2
  radiant, 3–5 dire, fixed by the seat→pid table); a policy cannot choose or infer its opponents'
  identities.
- **Spectator side only**: the real policy names from `config.players[i].name` live in
  `results.names` and in the replay header's `config.players`, and the viewer shows them next to
  the alias (`Cog-Charlie · derk-metagamer-v1`). The LLM request body is asserted by test never to
  contain a real player name.

### Event vocabulary carried by the replay

A **closed** seven-value enum, extracted server-side during Phase C step 9 and stored in the replay
header (and hence available to the viewer without re-deriving anything):

| `kind` | when | payload |
|---|---|---|
| `draft` | always, at tick 0 | `{"tick":0,"kind":"draft","pids":[0,1,2,5,6,7]}` |
| `first_blood` | the first hero death of the episode | `{"tick":312,"kind":"first_blood","pid":6,"victim_pid":1}` |
| `kill` | any later hero kill (`kills[pid]` increased) | `{"tick":1580,"kind":"kill","pid":0,"victim_pid":5}` |
| `tower` | `towers_killed[pid]` increased | `{"tick":740,"kind":"tower","pid":2,"team":0}` |
| `level_spike` | `level[pid]` increased | `{"tick":905,"kind":"level_spike","pid":2,"level":6}` |
| `ancient` | an Ancient fell | `{"tick":4412,"kind":"ancient","team":0}` |
| `end` | always, last | `{"tick":6000,"kind":"end","reason":"tick_cap"}` |

`victim_pid` is the pid whose `deaths` counter increased on the same tick; if several did, the
lowest pid (deterministic). Cap: **400 events**. On overflow, drop oldest `level_spike` first, then
oldest `kill`; `draft`, `first_blood`, `tower`, `ancient` and `end` are never dropped.

### Replay format v2 — self-sufficient bytes

Magic **`DERK`**, version u8 = **2**, `u32le header_len`, header JSON (utf-8), then
`tick_count × 60` bytes of post-clamp actions (10 heroes × 6 uint8), exactly the starter's body
layout. Ground truth stays `server/cogame_derks_gym/replay.py`.

Header JSON keys:

```json
{"format_version": 2,
 "sim_wasm_sha256": "…",
 "catalog_version": "v1",
 "catalog": { <the full catalog object, same shape as in the draft observation> },
 "config": {"seed": 305419896, "max_ticks": 6000, "tick_deadline_ms": 100,
            "draft_enabled": true, "draft_deadline_ms": 45000, "catalog_version": "v1",
            "player_connect_timeout_seconds": 60, "wall_clock_budget_seconds": 645,
            "players": [{"name": "derk-drafter-v1"}, … 6 …]},
 "aliases": ["Cog-Alpha", "Cog-Bravo", "Cog-Charlie", "Cog-Delta", "Cog-Echo", "Cog-Foxtrot"],
 "seat_hero_pids": [0, 1, 2, 5, 6, 7],
 "house_hero_pids": [3, 4, 8, 9],
 "draft": [ <10 draft records, pid order — the draft-reveal record> ],
 "loadout_digest": 2463534242,
 "events": [ <= 400 events ],
 "result": { <the full results.json document> },
 "tick_count": 6000,
 "final_state_digest": 1103515245}
```

One draft record (the **draft-reveal record**):

```json
{"pid": 2, "seat": 2, "alias": "Cog-Charlie", "player_name": "derk-metagamer-v1",
 "team": "radiant", "role": "burst",
 "picks": {"arm": "arm_cleaver", "tail": "tail_plate", "misc": "misc_regen"},
 "note": "tanky mid, out-scale the carry",
 "source": "seat", "fallback": false, "fallback_cause": "none", "decision_ms": 8123,
 "applied": {"base_health": 600.0, "base_mana": 300.0, "base_damage": 85.0,
             "basic_attack_cd": 13, "move_speed": 1.0,
             "hp_gain_per_level": 135, "mana_gain_per_level": 90,
             "damage_gain_per_level": 10}}
```

`source` ∈ `{"seat", "house"}`; `fallback_cause` ∈
`{"none","timeout","malformed","wrong_shape","unknown_item","disconnected","oversize"}`.
House records carry `player_name: null`, `seat: null`, the neutral picks and `decision_ms: 0`.

**Why this is self-sufficient**: the viewer needs (a) names — real names in `config.players` and
aliases in `aliases`; (b) config incl. `seed`; (c) per-tick state — re-derived exactly by
re-simulating the recorded action body from the recorded seed with the same wasm, which is why the
starter records actions rather than states, and the equality is *proved*, not assumed, by the
`final_state_digest` / `loadout_digest` cross-checks; (d) draft picks and their applied stat
blocks; (e) the event list for the feed and the scrubber beats; (f) the catalog, so item names and
deltas render without contacting the repo. Nothing but the S3 `.replay` fetch is ever contacted.

### `results.json`

The starter's 14 keys — `names`, `scores`, `win`, `team`, `winner`, `end_reason`, `final_tick`,
`seed`, `reward_sums`, `ancient_healths`, `agent_stats`, `noop_ticks`, `dead_seats`, `noop_causes`
— plus exactly **two** new ones:

- `draft` — the ten draft records (identical shape to the replay header's, real names included).
- `draft_fallbacks` — one boolean per seat, `true` when the server substituted the neutral loadout.

The schema is **closed**: `_results_doc`, the manifest `results_schema`, and
`tools/ci/docker_smoke.sh`'s expected-key set are updated together (AGENTS.md triple-sync rule) and
a test asserts all three agree.

### `/global` spectator feed

Unchanged shape. The connect snapshot gains `"phase": "draft" | "play" | "done"` and, once the
draft resolves, `"loadouts"` (alias-only records). Still broadcast-only, fire-and-forget, throttled
to every 50 ticks; a slow spectator can never stall the episode.

---

## Viewer

Static wasm bundle, **never a pod**: the manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and the repo ships
`tools/build_replay_viewer.sh` (the `coworld build` hook), inherited from the starter unchanged
except for the image tag — it builds the Dockerfile's `wasm-builder` target and copies
`/src/viewer/dist/.` into the bundle directory, asserting `index.html` exists.

### One starter supplies all four viewer files: `cogame-moba`

All four viewer files come from **cogame-moba and only cogame-moba**. No file is spliced from
another starter. The starter is the C/emscripten lineage, not the Nim/parley lineage, so the
checklist's four canonical filenames map onto these actual paths (verified present at
`/workspace/starters/cogame-moba`):

| checklist role | cogame-moba file (the one true source) |
|---|---|
| `replay-viewer/config.nims` — owns the emscripten link flags | `sim/build_viewer.sh` |
| the wasm entry `.nim` | `sim/viewer_main.c` |
| `static_replay*.js` — the replay-loading/transport script | the inline `<script>` inside `viewer/index.html` (this starter has no separate JS file; it is **not** extracted) |
| `index.html` — the shell | `viewer/index.html` |

The failure this pin exists to prevent (cogame-lantern, 2026-08-23: a `MODULARIZE`/`EXPORT_NAME`
link line spliced under an `onRuntimeInitialized` shell, deadlocking silently) is avoided by
keeping the starter's pairing exactly: the browser build stays
`-sENVIRONMENT=web` with **no `MODULARIZE`, no `EXPORT_NAME`**, `-sEXPORTED_FUNCTIONS=_main,$VIEWER_EXPORTS`,
`-sEXPORTED_RUNTIME_METHODS=ccall,cwrap,HEAPU8`, `-sUSE_GLFW=3 -sUSE_WEBGL2=1`,
`--preload-file vendor/upstream/resources@resources`, memory flags
`-sALLOW_MEMORY_GROWTH=1 -sMAXIMUM_MEMORY=1gb -sABORTING_MALLOC=1 -sINITIAL_MEMORY=512MB
-sSTACK_SIZE=512KB`; and the shell keeps the matching `var Module = { canvas, onRuntimeInitialized,
printErr, onAbort, onExit }` bootstrap with `<script src="derk_viewer.js">` last. The only edits to
the link line are new names in `VIEWER_EXPORTS` and the output filename. The headless node build
(`-sENVIRONMENT=node -sMODULARIZE=1 -sEXPORT_NAME=createViewerCore`, `build/viewer_core.js`) is a
**separate artifact for tests only** and is never loaded by the browser shell — that separation is
the starter's and is preserved.

**Load signalling (new, required):** on the first drawn frame after `viewer_load` succeeds
(`viewer_tick()` readable and `Module.canvas.width > 0`), the shell sets
`document.documentElement.dataset.replayLoaded = "true"` → `<html data-replay-loaded="true">`. On
any failure — fetch error, bad magic/version, `viewer_load` returning −1, a tick-count mismatch, an
`onAbort`/`onExit` — it sets `document.documentElement.dataset.replayError = "<message>"` and
mirrors the message into the starter's `#status` overlay. These two attributes are what
`tools/ci/viewer_smoke.mjs` polls.

### Chrome provenance: the starter's page plus an appended game block

**Honest statement about the pin's filenames:** cogame-moba has **no `client/` directory** — no
`client/chrome_common.js`, no `client/replay_broadcast.html`, no `client/renderer.js`. Its chrome is
the inline `<style>` + `<script>` of `viewer/index.html`. Inventing those paths here would mean
writing a page from scratch, which is precisely the failure the pin forbids (cogame-gridlock,
2026-08-23). So the pin is satisfied in the starter's own terms, and the builder must do exactly
this:

- **`viewer/index.html` starts as a byte-for-byte copy** of
  `/workspace/starters/cogame-moba/viewer/index.html`. Its inline transport script — `$`,
  `parseHeader`, `fillNames`, `winnerText`, `refreshUi`, `loadReplay`, the playpause / speed / seek
  handlers with the `seekGen` guard and the drag-preview logic, and the `Module` bootstrap — is the
  moba lineage's `chrome_common.js` and is kept **verbatim**, with additive hooks only (a
  `derkOnLoad(header)` call at the end of `loadReplay`, a `derkOnFrame(tick)` call at the end of
  `refreshUi`, and a `derkDismissEndcard()` call in each of the three seek handlers). Two literal
  string edits are allowed: the `<title>` and the `<header>` text (`cogame-derks-gym replay
  viewer`), and `moba_viewer.js` → `derk_viewer.js`.
- The whole game block is **appended**: one new `<div id="derk">…</div>` after the starter's
  `#teams`, one `<link rel="stylesheet" href="derk_chrome.css">` in `<head>`, and one
  `<script src="derk_chrome.js"></script>` before the `Module` script. **No starter id is reused,
  redefined or re-styled**; every new id is `derk-`-prefixed.
- **Removed starter elements: none.** `header`, `#stage`, `#canvas`, `#status`, `#controls`
  (`#playpause`, `#speed`, `#seek`, `#tickinfo`), `#endcard`, `#warn`, `#teams` and every starter
  CSS rule survive untouched. `#endcard` keeps its meaning (the starter's one-line winner text);
  the new full-stage endcard is the separate `#derk-endcard`. `#warn` keeps its sim-sha mismatch
  message and gains one more line on a `loadout_digest` mismatch (same pattern, same element).
- New files: `viewer/derk_chrome.css`, `viewer/derk_chrome.js`, `viewer/derk_items.svg`
  (an SVG sprite sheet: twelve hand-authored 24×24 `<symbol id="item-<catalog id>">` glyphs —
  blaster barrel, cleaver blade, needler spike, iron plate, stinger, rotor, regen cell, battery,
  focus chip, and three thin-outline "none" marks — referenced by `<use>`; real art, no
  placeholders, no external fetch). All three are copied into `viewer/dist/` by
  `sim/build_viewer.sh` next to `index.html`, and added to the Dockerfile's `wasm-builder` COPY
  list.

### Zoom: `#viewpanel` is kept, because the board is larger than the frame

The upstream renderer is a **camera view**, not a whole-board draw:
`init_game_renderer(32, 41, 23)` (`moba.h:2161`) opens a 41×23-cell, 1312×736-px canvas with a
`Camera2D` that follows `renderer->human_player` across a 128×128 map. 41×23 of 128×128 is 5.8 % of
the board, so the pin's condition is met and `#viewpanel` stays:

- `#derk-viewpanel` holds seven labelled `<button>`s — `Cog-Alpha` … `Cog-Foxtrot` and `auto` —
  which call a new export `viewer_set_camera(pid)` (writes `renderer->human_player`; `auto` follows
  the hero with the most recent event). The active button carries `aria-pressed="true"`.
- Minimap: a 128×128 `<canvas id="derk-minimap">` displayed at 128×128 (96×96 below 720 px,
  `image-rendering: pixelated`), redrawn each frame from `viewer_hero_positions()` — ten dots in
  the starter's palette (`#4cf` radiant, `#f66` dire, hollow when dead) plus a rectangle outlining
  the camera's 41×23 window. Clicking a dot selects that hero's camera.
- No pixel-zoom slider: the raylib canvas has a fixed 32-px cell size and rescaling it would
  desync the renderer's `GetScreenWidth()/ts` arithmetic. Camera selection is the zoom affordance
  this renderer actually supports, and the note says so rather than bolting on a slider that
  would break the render path.

### Readouts

1. **`#derk-scorebug`** (above `#stage`): `RADIANT  4500 ━━━━━━  ·  2 towers  ·  7 kills` vs the
   dire mirror, from `viewer_ancient_health(team)` and summed `viewer_agent_stat`. Ancient health
   bars are `width: calc(health / 4500 * 100%)`.
2. **`#derk-clock`**: `tick 1480 / 6000 · 04:56` — game time is `tick / 5` seconds at the upstream
   cadence of 5 ticks/s (tick 6000 → 1200 s → `20:00`), rendered `m:ss`.
3. **`#derk-roster`**: six rows, one per seat — item glyph badges (three `<use>` refs), alias,
   **real player name** (spectator side), role, level, K/D, and the drafted stat deltas as `+35` in
   green / `−10` in red. Two extra dimmed rows per team for the house heroes, labelled `house`.
4. **`#derk-draft`** — the **draft-reveal screen**: `position: fixed; inset: 0 0 var(--band) 0`,
   two columns (Radiant / Dire, single column below 720 px), one card per drafted cog with alias,
   real name, role, the three item names + glyphs, the full `applied` stat block against the base
   values, and the `note` (via `textContent` — it is player-controlled data). Auto-shown for the
   first 6 s of playback (ticks 0–29) with a countdown, then dismissed; re-openable by a labelled
   `draft` button appended to `#controls`; dismissed by any click on it, by the button, and by
   **every seek**. It never covers the transport band.
5. **`#derk-feed`**: the last six header events with `tick ≤ current`, one line each, coloured per
   kind, `textContent` only.
6. **`#derk-beats`** — scrubber beats: one absolutely-positioned `<button class="beat beat-<kind>">`
   per header event, at `left: calc(<tick>/<total>*100%)` over the `#seek` track, with a visible
   one-word label and `aria-label="<kind> at tick <n>"`; clicking sets `#seek.value` and dispatches
   `change`, reusing the starter's seek path. CSS exists for **all seven kinds** the server can
   emit: `.beat-draft`, `.beat-first_blood`, `.beat-kill`, `.beat-tower`, `.beat-level_spike`,
   `.beat-ancient`, `.beat-end`.
7. **`#derk-endcard`**: `position: fixed; inset: 0 0 var(--band) 0` — winner, `end_reason`, final
   Ancient healths, the winning team's three loadouts. **Stops at `var(--band)`** and is dismissed
   by every seek and by play.

### Transport rules

`relayout()` in `derk_chrome.js` runs on `load`, on `resize`, and after the draft overlay opens or
closes. It sets, on `:root` (`document.documentElement.style`):

- `--band` = `#controls`'s measured height + 8 px — 48 px when the controls fit one row (≥ 720 px)
  and 84 px when they wrap to two (< 720 px). Every fixed overlay uses `bottom: var(--band)`, so
  **nothing is ever overlaid on the transport band**. The starter's `#status` overlay is
  `inset: 0` within `#stage`, which is a sibling *above* `#controls`, so it also never reaches the
  band.
- `--hudscale` = `clamp(0.8, 100vw / 1100, 1)`.

### Legible at 360 px — the arithmetic

- The canvas is intrinsically 1312×736 (41 × 23 cells × 32 px). The starter's
  `canvas { max-width: 100vw; height: auto }` scales it to **360 × 202 px** at a 360 px viewport
  (scale 0.274), so one map cell is 8.8 px — heroes, creeps and towers stay distinguishable as
  team-tinted blobs (radiant `#0ff` accents, dire `#f00`, the starter's own palette), which is the
  correct level of detail at that width.
- **No text is ever read off the canvas.** The upstream renderer's in-canvas `DrawText` labels are
  20 px in a 1312 px frame and would shrink to 5.5 px, so every readout above lives in DOM chrome:
  scorebug/roster base 14 px × `--hudscale`; at 360 px `--hudscale` = `clamp(0.8, 360/1100, 1)` =
  **0.8** → 14 × 0.8 = **11.2 px**; the feed's 13 px base → **10.4 px**. Both are above the 10 px
  floor, and `--hudscale` is clamped at 0.8 precisely so it cannot go below it.
- Below 720 px the layout stacks: scorebug (32 px) → canvas (202 px) → transport band
  (`--band` 84 px) → feed (3 lines, 42 px) → roster (6 rows × 22 px) → `#derk-viewpanel` with the
  96 px minimap. The draft overlay collapses to one column, six 44 px cards = 264 px, scrollable
  inside `inset: 0 0 var(--band) 0`. The scrubber beats keep a 12 px minimum hit target and
  collapse to a shared `+n` chip when two beats land within 12 px of each other.

---

## Packaging

- **`compose.yaml`** — the starter's file with the service images renamed: services `game` and
  `player` (both `platform: linux/amd64`, `build: {context: ., dockerfile: Dockerfile,
  network: host}`), images `cogame-derks-gym-game:latest` and `cogame-derks-gym-player:latest`.
  Game and players ship in **one image**; the manifest `run` command selects the role.
- **`Dockerfile`** — the starter's two stages unchanged in shape. Stage 1
  `FROM --platform=$BUILDPLATFORM emscripten/emsdk:6.0.5 AS wasm-builder` (wasm is
  arch-independent; only the runtime is amd64), with the sha256-pinned
  `raylib-5.5_webassembly.zip` prefetch as its own layer; `COPY` list extended with
  `viewer/derk_chrome.css`, `viewer/derk_chrome.js`, `viewer/derk_items.svg`. Stage 2
  `python:3.11-slim`, `uv sync --frozen --no-dev --no-install-project`,
  `PYTHONPATH=/workspace/server:/workspace`, copies `build/derk_sim.wasm`,
  `build/derk_brain.wasm` and `viewer/dist/`. `CMD ["python","-m","cogame_derks_gym.server"]`.
- **`coworld_manifest_template.json`**:
  - `game.name`: `"derks-gym"`; `tags`: `["moba","team","draft","pufferlib"]`;
    `episode_timeout_minutes`: **20** (matching the 1200 s platform budget this note sizes against,
    and mirrored in `defaults.PLATFORM_EPISODE_TIMEOUT_MINUTES`); note the field lives at the
    manifest **top level**, not under `game`.
  - `game.replay_viewer`: `{"bundle": "static-replay-viewer"}`.
  - `game.runnable`: `{"type":"game","image":"{{GAME_IMAGE}}","run":["python","-m",
    "cogame_derks_gym.server"],"source_url":
    "https://github.com/Metta-AI/cogame-derks-gym/tree/main"}`.
  - `game.config_schema` — closed, `players`/`tokens` `minItems: 6, maxItems: 6`, plus
    `draft_enabled`, `draft_deadline_ms`, `catalog_version`, `num_agents` (min 6, max 6, default 6);
    `heroes_per_seat` removed.
  - `game.results_schema` — closed, the starter's 14 keys with array bounds changed to
    `minItems: 6, maxItems: 6` (and `agent_stats` staying `minItems: 10, maxItems: 10`), plus
    `draft` (10 records) and `draft_fallbacks` (6 booleans).
  - `game.protocols` — **both** entries, each `{"type":"uri","value":
    "https://github.com/Metta-AI/cogame-derks-gym/blob/main/docs/PROTOCOL.md"}`:
    `protocols.player` and `protocols.global`.
  - `game.docs` — `readme` → `.../blob/main/README.md`; `pages` → two entries:
    `{"id":"draft.md","title":"The loadout draft","content":{"type":"uri","value":
    ".../blob/main/docs/DRAFT.md"}}` and
    `{"id":"porting.md","title":"Porting PufferLib envs","content":{"type":"uri","value":
    ".../blob/main/docs/PORTING.md"}}`.
  - `player` — three entries, all `"image": "{{PLAYER_IMAGE}}"`,
    `run: ["python","-m","players.derk_player"]`, `source_url` `.../tree/main/players`,
    resources `requests {cpu 500m, memory 512Mi} / limits {cpu 2}`:
    `baseline` (env `PLAYER_SCRIPTED=puffer-forge`), `lane-brawler`
    (env `PLAYER_SCRIPTED=lane-brawler`), `drafter` (env `PLAYER_PROMPT=derk-drafter-v1`).
  - **Variants — `num_agents` is inside each variant's `game_config`, never at the variant top
    level** (`CoworldVariant` is `additionalProperties: false` and rejects it —
    cogame-goofspiel-oshi-zumo 0.1.0, 2026-08-26):

  ```json
  "variants": [
    {"id": "draft", "name": "Draft (3v3)",
     "description": "Six seats, one hero each, three per team. Each seat drafts one arm, one tail and one misc item before tick 0; the two remaining heroes per team run the vendored pretrained network on the neutral loadout.",
     "game_config": {
       "players": [{"name": "Cog1"}, {"name": "Cog2"}, {"name": "Cog3"},
                   {"name": "Cog4"}, {"name": "Cog5"}, {"name": "Cog6"}],
       "num_agents": 6,
       "draft_enabled": true, "draft_deadline_ms": 45000, "catalog_version": "v1",
       "max_ticks": 6000, "tick_deadline_ms": 100,
       "player_connect_timeout_seconds": 60, "wall_clock_budget_seconds": 645}},

    {"id": "nodraft", "name": "No draft (Puffer fidelity)",
     "description": "The same 3v3 seating with the draft turn disabled: no loadout is applied, so the sim is byte-identical to the upstream PufferLib Ocean MOBA the pretrained policies were trained on.",
     "game_config": {
       "players": [{"name": "Cog1"}, {"name": "Cog2"}, {"name": "Cog3"},
                   {"name": "Cog4"}, {"name": "Cog5"}, {"name": "Cog6"}],
       "num_agents": 6,
       "draft_enabled": false, "catalog_version": "v1",
       "max_ticks": 6000, "tick_deadline_ms": 100,
       "player_connect_timeout_seconds": 60, "wall_clock_budget_seconds": 600}}
  ],
  "certification": {
    "players": [{"player_id": "baseline"}, {"player_id": "baseline"}, {"player_id": "baseline"},
                {"player_id": "baseline"}, {"player_id": "baseline"}, {"player_id": "baseline"}],
    "game_config": {
      "players": [{"name": "Cog1"}, {"name": "Cog2"}, {"name": "Cog3"},
                  {"name": "Cog4"}, {"name": "Cog5"}, {"name": "Cog6"}],
      "num_agents": 6,
      "draft_enabled": true, "draft_deadline_ms": 5000, "catalog_version": "v1",
      "seed": 42, "max_ticks": 1200, "tick_deadline_ms": 250,
      "player_connect_timeout_seconds": 60, "wall_clock_budget_seconds": 400}}
  ```

  Cert arithmetic: `60 + 5 + 1200 × 0.25 = 365 s`, hard-stopped at 400 s. `max_ticks` is capped
  modestly on purpose — a six-way self-play mirror can stalemate, and a tick-cap draw with the
  Ancient-health tiebreak is a valid certified outcome.
- **`.github/workflows/`** — `ci.yml` (jobs `test`, `docker-smoke`, **`wasm-viewer`**,
  `upload-coworld`) and `coworld-release.yml` from `coworld-builder/templates/`.
- **Docs** — `README.md`; `docs/PROTOCOL.md` (the starter's, extended with the two draft messages,
  the caps table and the resolution order); `docs/DRAFT.md` (the catalog, the deltas, the clamps,
  the fallback table); `docs/PORTING.md` kept verbatim from the starter; `AGENTS.md` kept with the
  two inviolable rules and a third added: *the catalog and its deltas are a closed contract —
  `catalog.py`, the manifest `config_schema` enum, `docs/DRAFT.md` and `viewer/derk_items.svg`
  change together or the tripwire test fails*; `docs/plans/2026-08-28-derks-gym-design.md` (this
  note).

---

## Tests

`ci.yml` is the only harness — the sandbox runs none of this locally.

**Job `test`** (emsdk 6.0.5, node 22, `uv sync --frozen`, wasm artifacts built, `pytest -v` with
`COGAME_REQUIRE_WASM_BUILD=1` so no gate can silently skip):

1. `tests/test_fidelity.py` — **inherited, unchanged, inviolable.** Pristine vs patched build,
   identical seed and multi-thousand-tick random action log, byte-identical obs + rewards, tick
   floor asserted.
2. `tests/test_loadout.py` (new) — (a) **zero-loadout identity**: 500 ticks with an all-neutral
   `apply_loadout` for all ten pids vs no call at all → identical obs bytes, rewards and
   `state_digest()` every tick (this is the "Puffer fidelity gate for the un-drafted mode");
   (b) each of the 12 items applies exactly its documented deltas, read back through
   `hero_stat(pid, which)`; (c) the clamp table holds for all 64 arm×tail×misc combinations on all
   five roles; (d) deltas **survive death and level-up**: drive the sim until a drafted hero dies
   and until it levels, assert `max_health == applied.base_health + level *
   applied.hp_gain_per_level` and the same for mana and damage; (e) `apply_loadout` draws no RNG —
   the spawn positions and `state_digest` after a non-neutral loadout match a run where the same
   stats were injected before `c_reset`.
3. `tests/test_catalog.py` — the id set is exactly the 12 documented ids; every stat name in every
   delta is a real `struct Entity` field (regex tripwire over `vendor/upstream/moba.h`, the
   starter's `test_scripted.py` pattern); every id has an `item-<id>` symbol in
   `viewer/derk_items.svg`; the catalog sha256 constant matches the value baked into the manifest
   `config_schema` and `docs/DRAFT.md`.
4. `tests/test_draft.py` — the resolution order of §The game, case by case: legal picks applied;
   unknown id → neutral + `unknown_item`; wrong shape → `wrong_shape`; >4096-byte frame →
   `oversize`; no reply → `timeout`; closed socket → `disconnected`; `note` truncated to 120 runes
   **on a rune boundary** (asserted with a 4-byte emoji straddling index 120, and with a combining
   sequence); no seat's draft observation contains any other seat's pick (simultaneity); no draft
   observation contains a real player name (two-name-space assertion).
5. `tests/test_baseline.py` — the **bounded-orders / legality** assertion. For both `puffer-forge`
   and `lane-brawler`, against a live sim for 300 ticks: every returned row is exactly six ints in
   `0..ACT_HIGH[col]-1`, `engine._sanitize` returns non-`None` on every tick (never a NOOP
   fallback), and the draft pick for each of the ten role/hero combinations is a legal id of the
   matching slot.
6. `tests/test_llm_player.py` — stubbed transport: valid JSON accepted; fenced JSON accepted;
   malformed → one retry → scripted fallback; timeout → scripted fallback; missing API key → no
   call, scripted fallback; the request body never contains a `config.players[i].name`.
7. `tests/test_replay.py` — **end-to-end episode writing a replay**: run a real 400-tick episode
   with six scripted seats through the server, write the replay, then re-simulate from the replay
   bytes alone on a fresh sim and assert identical final tick, winner, obs bytes,
   `state_digest()` and `loadout_digest()`. Header completeness: real names, aliases, seed, config,
   catalog, ten draft records, `events`, `final_state_digest`. **Strict-UTF-8 replay parse**: the
   header slice decodes with `errors="strict"` and `json.loads` round-trips; a negative test flips
   a header byte to `0x80` and requires `ReplayError`; another sets `header_len` to `0xFFFFFFFF`
   and requires `ReplayError` (no wrap).
8. `tests/test_viewer.py` + `tests/viewer_core_harness.js` — inherited and extended: `viewer_load`
   accepts a v2 `DERK` replay and rejects bad magic, bad version, too-short, truncated header,
   wrapping `header_len` and a ragged (non-multiple-of-60) body; frame cadence, pause, seek,
   phase-lock; `viewer_state_digest()` equals the recorded live digest at the same tick **after**
   `viewer_set_loadout` is applied for all ten pids; `viewer_ancient_health`, `viewer_agent_stat`
   and `viewer_hero_positions` match the server sim's values at the same tick; the bundle files
   (`index.html`, `derk_viewer.js/.wasm/.data`, `derk_chrome.css`, `derk_chrome.js`,
   `derk_items.svg`, `sim_sha.js`) exist.
9. Inherited suites, updated for six seats and the draft phase: `test_sim.py`, `test_engine.py`,
   `test_server.py`, `test_config.py`, `test_players.py`, `test_scripted.py`, `test_startup.py`,
   `test_vendor.py`, `test_replay.py`.
10. `tests/test_manifest.py` — `num_agents == 6` **inside `game_config`** for every variant and for
    `certification.game_config`, and absent from every variant top level;
    `episode_timeout_minutes == 20`; every variant's `wall_clock_budget_seconds ≤ 645`;
    `replay_viewer.bundle == "static-replay-viewer"`; `results_schema` key set ==
    `_results_doc` key set == `docker_smoke.sh`'s expected set; `end_reason` enum == the engine's
    four literals; `protocols` has both `player` and `global`; `docs` has `readme` and `pages`;
    version strings match `^\d+\.\d+\.\d+$`.

**Job `docker-smoke`** — `docker build --platform=linux/amd64 -t cogame-derks-gym:ci .` then
`bash tools/ci/docker_smoke.sh cogame-derks-gym:ci`: one game container + **`<SEATS>` = 6** player
containers (`python -m players.derk_player` with `PLAYER_SCRIPTED=puffer-forge`) on the
`coworld-local` network with `file://` artifact URIs; config `{"seed": 7, "max_ticks": 200,
"tick_deadline_ms": 1000, "draft_enabled": true, "draft_deadline_ms": 5000,
"player_connect_timeout_seconds": 120, 6 players, 6 tokens}`. Asserts: exit 0; the exact 16-key
results set; `len(scores) == 6` and `sum(scores) == 3.0`; `noop_ticks == [0]*6`;
`dead_seats == [False]*6`; `draft_fallbacks == [False]*6`; ten `draft` records with
`fallback: false` for the six seats and `source: "house"` for the four house heroes; replay magic
`DERK` and version 2. Dumps game + all six player logs on failure. **Uploads the replay as
artifact `smoke-replay`.**

**Job `wasm-viewer`** — `needs: [docker-smoke]`. Downloads the `smoke-replay` artifact and the
`static-replay-viewer` bundle (built in this job by `bash tools/build_replay_viewer.sh`), serves
both over `http://127.0.0.1:8081`, then runs **`node tools/ci/viewer_smoke.mjs`** — Playwright
chromium, headless, `--enable-unsafe-swiftshader` for WebGL. The script:

1. opens `index.html?replay=/smoke.replay` at 1280×800;
2. waits ≤ 60 s for `document.documentElement.dataset.replayLoaded === "true"` and asserts
   `data-replay-error` is absent (a viewer that fails to boot fails the job — this is why the
   bundle is **executed**, not merely built);
3. asserts `#derk-draft` holds six alias rows × three item names, and that each row's real player
   name differs from its alias;
4. asserts `#derk-clock` reads `tick 0 / 200 · 0:00` at load and that the scorebug shows
   `4500` for both Ancients;
5. clicks the last `#derk-beats` button and asserts `#tickinfo` changed and `#derk-endcard` is not
   visible above `var(--band)` (bounding box check against the `#controls` box);
6. reloads at 360×640 and asserts the computed font size of `#derk-scorebug` is ≥ 10 px and that
   no element overlaps the transport band;
7. screenshots both widths into the job artifacts; exits non-zero on any failure.

**Job `upload-coworld`** — inherited: `needs: [test, docker-smoke, wasm-viewer]`,
main-only, `concurrency: upload-coworld`, version from
`tools/ci/next_coworld_version.py derks-gym` (never `coworld next-version`), warn-and-skip while
`SOFTMAX_TOKEN` is absent unless the `UPLOAD_REQUIRED` repo variable is `true`.

---

## Out of scope (v1)

- **Item costs, budgets, tiers and mid-match purchases.** One free item per slot, chosen once. A
  gold economy is the obvious v2 and would need a new sim-side income model.
- **Multi-round / snake / ban-phase drafts.** One simultaneous hidden turn only. A pick-order
  draft would need turn ordering, exclusivity and tie-breaks — deliberately excluded so v1 needs no
  contention rules.
- **Hero-role selection.** Roles are fixed by pid, as in upstream; a seat drafts items, not a hero.
- **Seating the tank and carry.** The four house heroes stay on the vendored pretrained network;
  a 10-seat drafted variant is a later addition (it changes `num_agents` and therefore the ladder's
  block seating).
- **LLM micro control.** The prompt policies decide the draft only; per-tick actions always come
  from the local pretrained network or the scripted bot.
- **Items that touch skills, cooldowns, mana costs, vision range or `agent_speed`.** Only the eight
  per-hero base stat fields listed above. Skill tables are function pointers set in `init_moba` and
  changing them is a physics change, not a stat change.
- **Sub-1.0 `move_speed` and any item that moves an obs byte out of its trained band.** Explicitly
  forbidden (see §The draft).
- **A live spectator viewer.** `/global` stays a broadcast status feed and `/client/global` a
  minimal page; watching means the static wasm replay bundle.
- **Pixel zoom, camera panning by drag, and a fog-of-war spectator mode.** `#derk-viewpanel`
  offers camera selection and a minimap; the raylib canvas keeps its fixed 32-px cell size.
- **Draft-phase reconnection semantics beyond the single turn.** A seat that misses the draft gets
  the neutral loadout and cannot re-draft, even if it reconnects at tick 1.
- **Replay v1 (`MOBA`) backwards compatibility.** The new viewer reads `DERK` v2 only; old
  cogame-moba replays are watched in cogame-moba.
