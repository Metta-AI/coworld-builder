# Gift Refinements — a beam that trebles what you give away, and nothing at all that makes you give

**Starter: `Metta-AI/coworld-ctf` (paintbot/paintball), mounted read-only at
`/workspace/starters/coworld-ctf`.** Gift Refinements is a real-time grid loop with rules written
for this coworld — per-tick grid actions (`collect`, gift-beam, `consume`), a per-tick replay, a
fixed board, six bodies walking around — which is the first row of the starter table ("any
real-time game loop, grid OR continuous physics, new rules written for this coworld"). Melting
Pot's `gift_refinements` is the *inspiration*, not a binary we reproduce bit-exactly, so this is
paintbot and not `cogame-moba`. Paintbot supplies the tick loop, the sprite-protocol board
renderer, the broadcast chrome, the static wasm replay bundle, the `Dockerfile` pair, the CI shape
**and** — since the paintball layer landed in it — the batched LLM decision layer
(`src/ctf/llm.nim`, `src/ctf/decide.nim`, `src/ctf/directives.nim`, `src/ctf/baselines.nim`) and
the thin prompt-carrying player process (`src/paintball_player.nim`). **Every convention there
holds here unless this note says otherwise.** Nothing is borrowed from any other starter: **all
four viewer files come from coworld-ctf only** (see `## Viewer`), and so does every forked source
file. There is no `OPEN` section — every rule the idea leaves loose is decided below, with the
reason.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins), each answered:**

| pin | how Gift Refinements satisfies it |
|---|---|
| starter by game shape | `Metta-AI/coworld-ctf` (paintbot) — real-time grid loop, new rules; nothing external is reproduced bit-exactly. |
| public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-gift-refinements`, **public** — a certification prerequisite (`source-resolves` 404s on private). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | one image; `PLAYER_PROMPT="<strategy>"` vs `PLAYER_SCRIPTED=reciprocator\|hoarder` (`## Decisions`). Champions #1 `gift-refinements-mirror` (daveey) and #2 `gift-refinements-patron` (daveey-1) are both prompt policies; the two fillers are the two scripted baselines — the idea's "background bots (never-gift, always-return)". |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` viewer is declared (`## Viewer`, `## Packaging`). |
| real art, starter chrome verbatim | `scripts/art/gen_gift_art.py` commits floor/pillar/seep/token/beam/cog art; `client/chrome_common.js` ships **byte-for-byte** and `client/replay_broadcast.html` is the starter's page with a game block appended (`## Viewer`). |
| legible to a casual spectator | `ROUND 5 / 12`, beams that fly three glowing tokens from giver to receiver, an inventory badge with three sheens, a live **trust graph**, `TOKENS IN PLAY` chart; checked at 360 px. |
| two name spaces | anonymous cog aliases `Aro … Fay` in-game and in every prompt; policy names only spectator-side (`roster[].pol`, the roster strip, `results.names`) — `## The game` §Seats. |
| degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | ≤ 459 s worst case against a 720 s budget, deadline checked between rounds, retry-once-then-scripted, `shutdownGraceSeconds = 20` (`## Decisions`, `## Server`). |
| `num_agents` in every variant AND the cert fixture | **6**, in all four variants, in `certification.game_config`, and as `<SEATS>` in `tools/ci/docker_smoke.sh` (`## Packaging`, `## Tests`). |
| prove it in CI | sim tests, a bounded-orders/legality test on both baselines, a feasibility oracle, an end-to-end episode writing a replay, a strict-UTF-8 parse, an **executed** viewer smoke (`## Tests`). |

**Source idea (verbatim, Asana idea task 1217747861545996):**

> Port of Melting Pot's gift_refinements. Raw tokens spawn; consuming turns every token in your
> inventory into +1 each regardless of refinement. Gifting (a beam) costs you one of your rawest
> tokens and gives the target THREE of the next refinement level (max two refinements; maxed
> tokens pass through as-is). Inventory caps at 15 per type. The Trust Game made spatial: a pair
> that bounces one raw token back and forth can turn it into nine and split it — but every step is
> a chance for the holder to consume and walk. Nobody has to give anything; all the upside requires
> it.
>
> Seats: 6
> Motive: trust / reciprocity
> Policy interface: per-tick grid actions (collect, gift-beam, consume)
> Fills gap: 11 Escrow is trust with contracts; this is trust with nothing but reciprocity and a beam
> Integrity (anti-collusion): anonymous aliases per episode; background bots (never-gift,
> always-return) in scoring.
>
> Replay plan (watchability): gift beams draw value flowing between cogs; refinement level shown as
> token sheen; a 'trust graph' of who gifted whom and who defected.
>
> Source: substrate gift_refinements. Video https://youtu.be/C1C2CJ__mhQ

---

## The game

### Seats, aliases, names

**`num_agents = 6`.** One unambiguous number — the idea pins it — in every manifest variant and in
the certification fixture. Six is also what the mechanic wants: enough cogs that partner *choice*
exists (a defected-on cog can go find someone else), few enough that one round's decisions are six
parallel LLM calls, which sits far inside the Bedrock sidecar's 30-requests-per-minute per-episode
ceiling with the pacing floor in `## Decisions`. **No variant changes `num_agents`.**

| slot | in-game cog alias | body colour (paintbot `slots[].color`) | spawn cell |
|---|---|---|---|
| 0 | `Aro` | `red` | `(2, 2)` |
| 1 | `Bex` | `orange` | `(21, 2)` |
| 2 | `Cyr` | `yellow` | `(2, 11)` |
| 3 | `Dov` | `lime` | `(21, 11)` |
| 4 | `Eno` | `blue` | `(2, 6)` |
| 5 | `Fay` | `pink` | `(21, 7)` |

Aliases are fixed to slots, never rotate, and carry no hint of policy, model or account. They are
the idea's "anonymous aliases per episode".

**Two name spaces (pin).** A seat sees only aliases — its own and the other five — in every
observation and every prompt. No policy name, player name, account or model name ever reaches a
seat. The replay carries `policyNames[]` alongside `names[]`; the viewer's roster strip shows the
**policy** name for non-baseline seats (paintbot's `roster[].pol` path in
`client/chrome_common.js`), and `results.names[]` carries policy names for the platform. Both, not
either.

### The board

A **fixed** grid, `cols = 24` × `rows = 14`, cell size 48 board-px → a 1152 × 672 board. **The
whole board always fits the frame**, which is why the viewer drops `#viewpanel` (zoom bar +
minimap) entirely (`## Viewer`). Cells are `(col, row)` = `(x, y)`, origin top-left. Every sim
quantity is an integer; the RNG (paintbot's seeded stream) is used for nothing but the tie-free
jitter-free bookkeeping described below, so a seed reproduces a replay bit-exactly.

- **Border wall ring** — `x == 0`, `x == 23`, `y == 0`, `y == 13` (72 cells). Impassable, blocks
  beams.
- **Five interior pillars**, each a 2 × 2 block (20 cells): `A (6..7, 4..5)`, `B (16..17, 4..5)`,
  `C (6..7, 8..9)`, `D (16..17, 8..9)`, `E (11..12, 6..7)`. Impassable, blocks beams. They exist so
  that "consume and walk away" is a real move: a cog can break every beam line to it in three
  steps. The `open-floor` variant deletes them and nothing else.
- **Passable interior**: 264 − 20 = **244 cells**.

**Seep pads (18, fixed).** A pad is a passable, drawn floor vent that grows raw tokens:

`y = 2`: `x ∈ {4, 9, 14, 19}` · `y = 11`: `x ∈ {4, 9, 14, 19}` · `y = 6`: `x ∈ {3, 9, 14, 20}` ·
`y = 7`: `x ∈ {3, 20}` · `y = 4`: `x ∈ {11, 12}` · `y = 9`: `x ∈ {11, 12}`.

That is 4 + 4 + 4 + 2 + 2 + 2 = **18** pads, none on a wall, a pillar or a spawn cell (asserted at
init and by `tests/test_board.nim`). A pad holds **at most one** loose raw token. At `tick 0` every
pad carries one. A pad emptied by a `collect` regrows after `spawnTicks = 30` ticks
(`spawn` event). Supply ceiling: 18 × (720 / 30) = **432 raw tokens per episode**, so scarcity is
real but never absolute.

### Tokens, refinement, and the gift beam

A token has a **level**: `0 = raw`, `1 = refined`, `2 = super` (`maxLevel = 2`). Every cog's
inventory is three integers, `t0`, `t1`, `t2`, each capped at **`invCap = 15` per level** (the
idea's "caps at 15 per type"). Tokens are not dropped, stolen, traded or destroyed by anything but
`consume` and the cap.

**Consuming** converts **every** token the cog holds, at every level, into **+1 score each**, and
empties the inventory (`consume` event, `consumeCooldown = 10` ticks). That is the idea's rule
verbatim: refinement buys nothing at the till; it only multiplies *how many* tokens exist.

**Gifting** is a beam. A `gift_<dir>` action traces cells straight out from the shooter in one of
the four cardinal directions, cells 1..`beamRange = 4` ahead; the trace stops at the first wall or
pillar; the **first cog** found in it is the target. Then:

1. The shooter spends **one token of its LOWEST held level** — "one of your rawest tokens". A cog
   holding any raw token can therefore only ever send a raw token; to hand back refined stock you
   must first spend or bank your raw. (This is the whole specialisation mechanic and it is stated
   twice in the prompt.)
2. If that token's level `L < 2`, the target receives **`giftMultiplier = 3` tokens of level
   `L + 1`**. If `L == 2` the target receives **1 token of level 2** — "maxed tokens pass through
   as-is". This is how a pair splits a pile.
3. Any part of the receipt that would push the target's `t[L']` over `invCap = 15` is **lost**
   (`spill` event, `cause: "gift"`).
4. A beam that finds no cog is a **miss**: it costs **no token**, only the cooldown
   (`giftmiss` event). A shooter holding zero tokens does not fire at all.
5. A cog cannot gift itself (the trace starts at the next cell) and cannot gift through a wall,
   a pillar or another cog.

`giftCooldown = 4` ticks between a cog's beams; a standing order may schedule at most
`maxBeamsPerRound = 10` of them.

**The ladder, in numbers** (this is the idea's "one raw token into nine"): A collects 1 raw and
beams it to B — B now holds 3 refined. B beams those three back, one at a time (3 beams) — A now
holds 9 super. A beams 4 of them back at 1:1 — A banks 5, B banks 4. **One raw token, 8 beams, 9
points, split by consent at every single step**, and at every step the holder can simply
`consume` and walk behind a pillar.

### Scoring — banked tokens, higher is better

- **Seat score `S_i` = the number of tokens seat *i* has consumed over the episode**, each worth
  exactly +1 regardless of level. An integer ≥ 0. Nothing is ever subtracted; there is no penalty
  term and no negative score.
- **Sign: higher is better.** `results.win[i] = (S_i == max(S))`; ties mark multiple winners, which
  is correct for a mixed-motive trust game and needs no tiebreak.
- **The league ranks by `results.scores`** (the platform's mean over episodes). Nothing else is
  ranked: gifts sent, gifts received, defections and the reciprocity index are reported for the
  viewer and for analysis and are **not** in the score.
- **Tokens still in inventory score nothing** — with one deliberate exception: at the **final tick
  of the episode** (`tick == rounds × ticksPerRound − 1`) every cog automatically consumes whatever
  it still holds (`autobank` event, counted into `S_i` exactly like a `consume`). The market closes
  and everyone cashes out. This removes the one boring failure mode (a seat that forgets to bank
  and scores 0) while removing **no** trust decision at all: every mid-game choice — gift or hold,
  return or consume — is untouched.

**Why cooperating wins, in arithmetic the builder can check.** With `moveCooldown = 2` a cog makes
30 moves per 60-tick round; a `collect` costs a tick plus `collectCooldown = 3`; a beam costs a
tick plus `giftCooldown = 4`.

- **Pure hoarding** (the `hoarder` filler): pads sit ~4 cells apart, so ~11 ticks per token →
  ~5 raw per round → **~60 points over 12 rounds**.
- **A reciprocating pair**: each cog spends ~22 ticks collecting (2 raw) and ~36 ticks beaming
  (9 beams). The pair therefore brings in 4 raw and fires 18 beams per round; fully processing
  4 raw costs 16 beams and mints 36 tokens → **~18 points per cog per round → ~200 over 12
  rounds**, minus a round or two of warm-up.
- So reciprocity pays roughly **three times** what hoarding pays — "all the upside requires it" —
  and the exploit (accept, never return) pays best of all *for one round*, which is precisely the
  drama the trust graph is there to show.

### The exact tick resolution order

One episode = `rounds = 12` × `ticksPerRound = 60` (= paintbot's `turnTicks`) = **720 ticks**.
Playback is 24 fps, so a full replay is 30 s of video (comfortably longer than the viewer soak
gate).

Every tick runs these **seven** steps in this order. Within a step, seats resolve in **ascending
slot order** unless the step names another order. All reads inside a step use the state as it stood
at the start of that step unless the step says otherwise.

1. **Regrow.** Every empty pad's `bareFor` counter decrements by 1; at 0 a raw token appears on it
   (`spawn` event).
2. **Kernel intent.** Each cog's kernel (below) derives this tick's single action from its standing
   order and the live state: `move_n | move_s | move_e | move_w | collect | gift_n | gift_e |
   gift_s | gift_w | consume | wait`. A cog whose relevant cooldown is still running emits `wait`.
3. **Consume** (slot order). A cog whose action is `consume` scores `t0 + t1 + t2`, zeroes all
   three counters, emits `consume` with the per-level breakdown, and sets `consumeCooldown = 10`.
   Consuming resolves **before** gifting, so a token beamed at you on the same tick lands *after*
   your cash-out and survives it.
4. **Gift beams** (slot order), each resolved against the **live** state (a token spent by a lower
   slot this tick is already gone; a cog that has already moved this tick has not — movement is
   step 6). Rules 1–5 of §Tokens apply. Emits `gift`, `giftmiss` or `spill`.
5. **Collect** (slot order). A cog whose action is `collect` and whose own cell carries a loose raw
   token takes it (`t0 += 1`, `collect` event, `collectCooldown = 3`) and the pad starts its
   `spawnTicks = 30` regrow. If `t0` is already at `invCap`, the token stays on the pad and a
   `spill` event with `cause: "collect"` is emitted.
6. **Move** (slot order), against the live board. A move is legal into a non-wall, non-pillar cell
   not occupied by another cog (a cell a lower-numbered seat already moved into this tick counts as
   occupied). It sets `moveCooldown = 2`. An illegal move degrades to `wait`.
7. **Record.** Append this tick's state frame, its events and the `TOKENS IN PLAY` series row to the
   replay. On the final tick of the episode, **before** recording, every cog autobanks (§Scoring).

At a round boundary (`tick mod ticksPerRound == 0`, `tick > 0`) the sim additionally closes the
round accounting, emits `round`, checks the end conditions, and — if the episode continues — blocks
for the next batched decision (`## Decisions`).

### Where per-tick actions come from: the standing order and the kernel

The sim's policy interface is per-tick grid actions, exactly as the idea says. No LLM can emit 720
actions per seat, so once per **round** (60 ticks) each seat submits a **standing order** and a
deterministic **kernel** turns it into that round's per-tick action stream — paintbot's own
`directives.nim` / `control.nim` shape, and the batched cadence that worked in cogame-hive,
cogame-chemistry and cogame-fruit-market: **72 LLM calls per episode instead of 4 320**.

An order is `{job, target, gift, consume, say, notes}` (schema and caps in `## Decisions`). Given
the order and the current tick's state the kernel picks, in this priority:

1. **Scheduled consume.** `consume: "now"` fires on the round's **first** tick; `consume: "end"`
   fires on the round's **last** tick; `consume: "never"` never fires. (The episode-final autobank
   is not an order and cannot be declined.)
2. **A beam**, if `gift > 0` beams remain for this round, `giftCooldown` has expired, the cog holds
   at least one token, and `target` is currently hittable — same row or column, distance
   ≤ `beamRange`, no wall, pillar or third cog in between. Direction is the one pointing at the
   target.
3. **The job's movement**:
   - `collect` — Dijkstra to the nearest cell holding a loose raw token, `collect` on arrival. If
     no token is loose anywhere, walk to the nearest pad and `wait` on it.
   - `meet` — Dijkstra to the nearest cell from which `target` is hittable (rule 2's predicate),
     then `wait` there. A cog that is already in line stays in line, so its partner can beam it
     back. `meet` with no legal `target` degrades to `collect`.
   - `hold` — `wait` in place. Beams still fire when someone walks into line.
   - `evade` — Dijkstra to the reachable cell that maximises the Chebyshev distance to the nearest
     other cog, ties broken by lowest `(y, x)`. This is "consume and walk" made expressible, and
     the pillars are what make it work.

Dijkstra is over passable cells with unit cost, neighbour expansion in N, E, S, W order, ties
resolved by that expansion order — paths are unique and deterministic. Other cogs are not obstacles
for path *planning*, only for the move itself.

### End conditions and `results.reason`

The episode ends at the FIRST of these, all checked at a **round boundary**:

| condition | `results.reason` | `results.ending` | scores |
|---|---|---|---|
| 12 rounds played | `complete` | `round_limit` | as computed (including the final-tick autobank) |
| wall clock passes the play deadline (0.6 × `episodeTimeoutSeconds` = **720 s**) | `deadline` | `deadline` | rounds played are scored; every cog autobanks at the settling tick; unplayed rounds add nothing |
| no seat connected within `playerConnectTimeoutSeconds = 180` | `forfeit` | `forfeit` | all zero; results + replay are still written |

Those three — **`complete`, `deadline`, `forfeit`** — are the only legal `results.reason` values.
A room where nobody ever gifts is a *completed game of Gift Refinements*, not an error: it reports
`complete` and the flat trust graph tells the story, so phase 60's check 4 passes on a miserly room
as it should. `deadline` is admissible (it means the LLM was slow, not that the game broke), but
the arithmetic in `## Decisions` is sized so it should not fire.

### Feasibility gates (the oracle, not the table above)

The numbers in §Scoring are **design targets derived from the constants, not measurements**. The
enforcement is `tests/test_feasibility.nim`, over seeds 1..12 on all four variants:

- **(a) The baselines play the game.** All-`reciprocator`: ≥ 11/12 seeds end `complete` /
  `round_limit`, ≥ 200 beams connect, every seat scores ≥ 60, and at least 30 % of all banked
  tokens are level ≥ 1. This is what makes certification, `docker-smoke` and all-filler league
  episodes end `complete` **and** watchable.
- **(b) Reciprocity beats hoarding.** In a 3 × `reciprocator` + 3 × `hoarder` room the
  reciprocators' mean score is ≥ **1.8 ×** the hoarders' mean.
- **(c) Free-riding is punished.** One test-only `leech` (accepts everything, never gifts; lives
  only in the test, never shipped) among 5 `reciprocator`s finishes with a score strictly **below**
  the reciprocators' mean, because a reciprocator only ever returns to its best net partner.
- **(d) The ladder actually runs.** In a 6 × `reciprocator` room the number of banked tokens at
  level 2 is ≥ the number banked at level 0.

**If a gate fails, repair constants in this order and re-run — no design bounce is needed:**
(a) `spawnTicks 30 → 20`, then `giftCooldown 4 → 3`; (b) `maxBeamsPerRound 10 → 12`, then
`spawnTicks 30 → 45` (raw scarcer, chains relatively better); (c) tighten the `reciprocator`
partner rule to require `net > 0` for two consecutive rounds; (d) `beamRange 4 → 5`. Any change to
a constant in this note re-runs the whole oracle.

### Constants (one table, the config defaults)

| constant | value | meaning |
|---|---|---|
| `rounds` | 12 | one episode |
| `ticksPerRound` / `turnTicks` | 60 | one round; one decision per seat per round |
| `maxLevel` | 2 | raw → refined → super |
| `giftMultiplier` | 3 | tokens minted per sub-max gift |
| `invCap` | 15 | per level, per cog |
| `beamRange` | 4 | cells, cardinal, walls and pillars block |
| `giftCooldown` | 4 | ticks between one cog's beams |
| `maxBeamsPerRound` | 10 | beams a standing order may schedule |
| `collectCooldown` | 3 | ticks between pick-ups |
| `moveCooldown` | 2 | ticks between moves |
| `consumeCooldown` | 10 | ticks between cash-outs |
| `spawnTicks` | 30 | pad regrow |
| `pads` | 18 | fixed cells listed above |
| `attempt1Ms` / `retryMs` / `turnBudgetMs` | 20000 / 12000 / 34000 | whole seconds, `sim_config` enforced |
| `minTurnSeconds` | 25 | floor between batch starts |
| `playerConnectTimeoutSeconds` | 180 | lobby bound |
| `shutdownGraceSeconds` | 20 | post-artifact grace |

---

## Decisions: LLM with scripted fallback

Both policies ship in the **same image** from day one, env-switched:
`PLAYER_PROMPT="<strategy text>"` makes a seat an LLM seat; `PLAYER_SCRIPTED=reciprocator|hoarder`
makes it a scripted seat; a seat that sets neither is `PLAYER_SCRIPTED=reciprocator`. A scripted
policy seated as a champion is a failure state. **A policy is a prompt.**
`src/gift_refinements_player.nim` (a fork of coworld-ctf's `src/paintball_player.nim`) is one thin
process that connects, sends `{"type":"prompt","prompt":…,"scripted":…}` and then only listens.
All decision-making happens in the **game** container (`src/gift_refinements/llm.nim` and
`decide.nim`, forked from `src/ctf/llm.nim` and `src/ctf/decide.nim`) — which is what makes one
parallel batch per turn possible, and is why the coworld secret must be on the *game* runnable
(hive, 2026-08-23).

### Cadence, batching, and the wall-clock budget

One **turn = one round = 60 ticks**. At each round boundary the game builds all six seats' request
bodies and issues them as **ONE parallel batch** (`curly.makeRequests`, paintbot's `decide.turn`) —
never sequentially, never one seat at a time. The single retry is likewise **one batch** of only
the seats that failed, and it is issued only after the first batch has resolved.

```
per round:     1 batch of 6 requests, attempt1Ms = 20 s
               + at most 1 retry batch of the failed seats, retryMs = 12 s
               turnBudgetMs = 34 s caps the whole turn (sim_config asserts
               attempt1Ms + retryMs <= turnBudgetMs, whole seconds only)
worst case:    12 rounds x 34 s                                = 408 s
+ sim:         720 ticks x ~0.5 ms (6 Dijkstra/tick, 244 cells) =   0.4 s
+ connect:     player connect grace (typical)                  <=  30 s
+ shutdown:    shutdownGraceSeconds                            =   20 s
total worst:   ~459 s   <   720 s  ( = 0.6 x episodeTimeoutSeconds 1200 )
typical:       max(minTurnSeconds 25, ~7 s batch) x 12          ~ 300 s
```

`minTurnSeconds = 25` floors the spacing between **batch starts**. Requests per minute, worst case:
a round issues at most 12 requests (6 + 6 retries) and the next batch cannot start before 25 s, so
the ceiling is 12 / 25 s = **28.8 rpm**, under the Bedrock sidecar's 30 rpm per-episode limit that
bit cogame-raid; the normal case is 6 / 25 s = 14.4 rpm. Requests per episode: 72, plus ≤ 72
retries. The floor is applied **after** the round's ticks are simulated and the next `state` frame
is sent, so it never delays a decision the sim is waiting on. All LLM deadlines are **whole
seconds** — curly's `CURLOPT_TIMEOUT` floors sub-second deadlines (paintball, 2026-08-25), and the
starter's `sim_config` already rejects `attempt1Ms mod 1000 != 0`; that check is kept. The play
deadline (0.6 × `episodeTimeoutSeconds`; the game container is **not** given
`COWORLD_TIMEOUT_SECONDS`, so 1200 is assumed unless that env var is present) is tested **between
rounds**; hitting it calls `endEarly()` and settles with `reason: "deadline"`.

### The observation each seat gets

Sent as the `state` frame at every round boundary and rendered into the user prompt. Every number
below is visible to that seat; **nothing else is**. The information design is the whole game:
**positions, scores, consumptions and every gift ever fired are public** (the beam is a bright
public act and the till is a public flash), **inventories are private**. You know what someone
banked; you do not know what they are holding, and that is what makes a promise-free trust game
playable at all.

```json
{"type":"state","protocol":"gift-refinements.player.v1","slot":2,"name":"Cyr",
 "round":5,"rounds":12,"roundsLeft":7,"ticksPerRound":60,"tick":300,
 "board":{"cols":24,"rows":14,"variant":"refinery","pads":18,"beamRange":4},
 "you":{"cell":[9,6],"tokens":{"raw":0,"refined":4,"super":2},"held":6,
        "rawestLevel":1,"score":38,"beamsPerRound":10,
        "lastOrder":{"job":"meet","target":"Aro","gift":6,"consume":"never","source":"llm"}},
 "cogs":[{"alias":"Aro","slot":0,"cell":[7,6],"dist":2,"hittable":true,"dir":"west",
          "score":41,"youGave":6,"gaveYou":9,"net":3,"lastGaveYouRound":4,
          "bankedLastRound":0},
         {"alias":"Bex","slot":1,"cell":[18,3],"dist":11,"hittable":false,"dir":null,
          "score":57,"youGave":0,"gaveYou":0,"net":0,"lastGaveYouRound":null,
          "bankedLastRound":7},
         "… all five other cogs, always, in slot order …"],
 "loose":[{"cell":[11,4],"dist":4},{"cell":[9,2],"dist":4},
          "… every loose raw token on the board, nearest first …"],
 "ledger":[{"r":4,"from":"Aro","to":"Cyr","sent":"raw","got":"refined","n":3},
           {"r":4,"from":"Cyr","to":"Aro","sent":"refined","got":"super","n":3},
           "… the last 16 gifts on the whole board, most recent last …"],
 "banks":[{"r":4,"who":"Bex","n":7},"… the last 8 consumes on the whole board …"],
 "history":[{"round":4,"collected":2,"sent":6,"received":9,"banked":0,"held":6,"score":38},
            "… one row per round played …"],
 "notes":"…your own notes from last round…",
 "rules":{"scoring":"+1 for every token you consume, whatever its refinement; higher is better",
          "gift":"a beam spends ONE token of your LOWEST level and gives the target THREE of the next level; a super token passes through as one super token",
          "rawestFirst":"while you hold any raw token, every beam you fire sends a raw token — bank or spend your raw before you can hand back refined stock",
          "beam":"range 4 cells, straight N/E/S/W, blocked by walls, pillars and other cogs; a miss costs nothing",
          "cap":"15 tokens per level; anything over is lost",
          "close":"at the last tick of round 12 everything you still hold is banked automatically",
          "budget":{"beamsPerRound":10,"giftCooldown":4,"collectCooldown":3,"moveCooldown":2},
          "silence":"there is no talk channel; the only signal you can send is a beam and where you stand"}}
```

- **Visible:** your cell, your three token counts, your lowest held level, your score, your beam
  budget and your last order; for **every** other cog (always, no fog) its alias, slot, cell,
  distance, whether it is hittable right now and in which direction, its **score**, the running
  `youGave` / `gaveYou` / `net` token counts between you and it, the round it last gave to you, and
  what it banked last round; every loose raw token on the board; the global **gift ledger** (last
  16 gifts, any pair) and the global **bank tape** (last 8 consumes); your own per-round history;
  your private notes; and the full rule/constant block for this variant.
- **Hidden:** every other cog's **inventory** (raw/refined/super counts), its standing order, its
  `notes`, its prompt, its policy name, its player name and account; the RNG seed; pad regrow
  timers you are not standing on; anything about the league.
- **There is no talk channel.** The idea's line is "trust with nothing but reciprocity and a beam",
  so the reply's `say` field is **spectator-only**: it is drawn in the viewer feed and recorded in
  the replay, and is *never* delivered to another seat. The beam is the message.

### The reply schema

The model must answer with exactly one JSON object whose first character is `{`:

```json
{"job":"meet","target":"Aro","gift":6,"consume":"never",
 "say":"three refined back to Aro, then I hold",
 "notes":"Aro returned 3/3 in rounds 3 and 4 - keep the chain. Bex banks every round, never gives."}
```

| field | type | cap / range | on violation |
|---|---|---|---|
| `job` | string enum | `collect` \| `meet` \| `hold` \| `evade` | missing or not in the enum → **invalid reply** |
| `target` | string or `null` | one of the **five other aliases**, case-insensitive | required when `job == "meet"` or `gift > 0`; own alias, unknown alias or a non-string → **invalid reply**. `null` with `gift > 0` → **invalid reply** |
| `gift` | integer | **0..10** | absent → `0`. Outside the range is **clamped** and the `order` event records `"clamped":true`. Non-integer → **invalid reply** |
| `consume` | string enum | `now` \| `end` \| `never` | absent → `end`. Unknown value → **invalid reply** |
| `say` | string | **80 characters** | truncated |
| `notes` | string | **320 characters** | truncated |

Extra keys are ignored. **Truncation is on rune boundaries**, never bytes: `cleanText(text, limit)`
= `strip` → if `runeLen > limit`, `runeSubStr(0, limit-1) & "…"` (the starter's `directives.nim`
rune discipline; a byte cut put invalid UTF-8 into a replay and only a strict parser found it —
bullwhip, 2026-08-22). Newlines in `say` and `notes` become spaces. Both are recorded in the
replay. The same rune-safe truncation applies to **every** string that reaches the replay,
including LLM error text (capped at 200 characters).

### Prompts

**System prompt** (composed by the game, per seat, per round): the seat's alias in capitals; the
board described in words (24 × 14, a wall ring, five pillars, 18 seep pads that grow raw tokens);
the constants table above; the standing-order model ("you choose one order for the next 60 ticks; a
kernel walks and beams it for you"); the gift rule stated **three** times — once as the rule, once
as the rawest-first warning, once as the worked ladder ("one raw beamed to a partner becomes three
refined in their hands; three beams back makes nine super in yours; a super beam moves one token,
which is how you split") — the +1-per-token-consumed scoring rule verbatim; the automatic close at
the final tick; the statement that the other five cogs are other policies deciding
**simultaneously**, that **nobody can hear anything you say** and the only signals you can send are
a beam and where you stand; that `notes` is private; and the output contract, ending:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

(Bedrock/Haiku answers prose-first without that sentence — playbook §Phase 1.)

**User prompt:** the observation rendered compactly — a `YOU` block, a cogs table
(`alias | cell | dist | hittable | score | you gave | gave you | net`), the loose-token list, the
gift ledger as `r4  ARO → CYR  raw → 3 refined`, the bank tape as `r4  BEX banked 7`, the per-round
history table, `YOUR NOTES FROM LAST ROUND`, then the operator block:

> GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
> requested format):
> `<PLAYER_PROMPT>`

then a one-line restatement of the reply shape with the **legal enum values for this variant**,
including the five alias strings this seat may target (precomputing the legal choice set in the
observation is what halved formal-output fallbacks in escrow).

**Transport:** the starter's ladder, haiku-only (raid 2026-08-23, reconfirmed paintball
2026-08-25 — the sonnet fallback times out on every sidecar call and turns one throttle into a
cascade): `bedrockModelIds() = ["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`, `BEDROCK_MODEL`
overrides. `maxOutputTokens = 1000` (hanabi, 2026-08-24: budget ≥ 1000 or truncation shows up as
the misleading "unbalanced JSON object" signature; on `stop_reason == "max_tokens"` the extractor
raises "reply cut off at max_tokens mid-JSON" by name). No `output_config.effort` — Haiku 4.5 400s
on it. Credentials in order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` /
`AWS_BEARER_TOKEN_BEDROCK`) → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`. With none, the client
disables itself immediately and every seat plays `reciprocator` — which is what keeps offline
certification green and deterministic.

**Champion prompts** (phase 40 uploads these; both are `PLAYER_PROMPT` policies):

- `gift-refinements-mirror` (champion #1, daveey): *"You play strict, generous tit-for-tat. Open
  round one by collecting two raw tokens and beaming ONE of them to the nearest cog — one, not
  more, and remember who it was. From then on your rule is simple: for each cog, return exactly as
  many beams as it sent you last round, and one extra beam every third round to keep the chain
  growing. Never send a second gift to a cog that has taken from you and returned nothing for two
  full rounds; walk away from it and open with someone else instead. Watch your lowest level: while
  you hold raw tokens every beam you fire sends raw, so if you are sitting on refined stock and
  want to send it back, stop collecting and spend or bank your raw first. Bank only when you are
  holding more than ten tokens or when there are two rounds left; a token in your hands can still
  be trebled, a token in the bank cannot."*
- `gift-refinements-patron` (champion #2, daveey-1): *"You are a patron: you build one deep
  refining chain and defend it. In the first two rounds probe by sending a single raw token to two
  different cogs and note who returns anything at all. Then pick the ONE cog with the best return
  and commit — meet it every round, feed it every raw token you collect, and let it feed you refined
  stock; a pair that keeps one token moving turns it into nine, and nine split is better than one
  hoarded. Never split your beams across three partners; a half-fed chain mints nothing. If your
  partner takes two rounds in a row without returning, cut it off permanently, say so, and adopt the
  cog with the highest net given to you. Hold your super tokens until the last two rounds and then
  spend beams returning half of them — the close banks whatever is left, so the only tokens you
  waste are the ones you never minted."*

### Scripted baselines (both fieldable, both league fillers)

These are the idea's "background bots (never-gift, always-return) in scoring".

`reciprocator` — the always-return bot, the league's first filler, and the fallback every failed
LLM decision lands on. At each round boundary, purely from the observation:

1. Let `P` = the cog with the largest `net = gaveYou − youGave`, ties by lowest slot; `P` counts
   only if `net > 0`.
2. If `P` exists → `{"job":"meet","target":P,"gift":min(gaveYouLastRound(P) + 1, held, 10)}`.
3. Else if no cog has ever given to it and it holds ≥ 2 tokens → the **seed gift**:
   `{"job":"meet","target":<nearest cog>,"gift":1}`.
4. Else → `{"job":"collect","target":null,"gift":0}`.
5. `consume` = `"end"` if `held ≥ 10` or `roundsLeft ≤ 1`, else `"never"`.
6. `say` = `"returning N to <ALIAS>"` / `"collecting"`; `notes` = `""`.

`hoarder` — the never-gift bot, the second filler, and the foil that makes cooperation legible. It
never gifts (`gift` is always `0`, `target` always `null`):

1. If a loose token exists → `{"job":"collect"}`; else `{"job":"evade"}` (it walks away from
   everyone, which is exactly the behaviour the audience should learn to recognise).
2. `consume` = `"end"` if `held ≥ 6` or `roundsLeft ≤ 1`, else `"never"`.
3. `say` = `"mine"`; `notes` = `""`.

Every field either baseline emits is inside its declared enum by construction, `gift` is always in
0..10 and never exceeds `held`, and `target` is never its own alias; all of that is asserted in
`tests/test_baseline.nim`.

### Degrade, never hang

- Attempt 1 gets `attempt1Ms = 20 s`; the single retry batch gets `retryMs = 12 s`; the whole turn
  is wrapped in a monotonic `turnBudgetMs = 34 s` deadline (the starter's own three-clock shape).
- On transport error, non-2xx, refusal, `max_tokens` before any `{`, unparseable JSON, or any
  **invalid reply** in the table above, that seat alone joins the round's **retry batch**, with the
  appended hint *"Your previous reply was invalid. Respond with ONLY the requested JSON object,
  using one of the listed job values, one of the listed target aliases, a gift count between 0 and
  10, and one of now/end/never."* A provider throttle with no other candidate model **skips the
  retry outright** (it cannot land) and fails fast to the scripted layer for that turn.
- Still failing → that seat plays the **`reciprocator` order** for that round, logged as
  `gift-refinements llm: seat N falling back to scripted order` and recorded on the `order` event as
  `"source":"fallback"`. `decide.turn` never raises; the episode always advances. No tick is ever
  left unactuated: the kernel always has an order — this round's, else last round's, else
  `reciprocator`'s.
- 401/403 disables the client for the rest of the episode (all seats scripted from then on); 429 is
  logged and the seat is retried in the next round's batch.
- A seat that never connected, or whose socket dies mid-episode, plays `reciprocator` for every
  remaining round. The episode never waits on a socket beyond `playerConnectTimeoutSeconds = 180`
  at the start and never blocks on one mid-episode. Registration is **adaptive**: the lobby returns
  as soon as every connected socket has registered (commons-family, 2026-08-24), and an
  unappliable registration is **held and re-sent by the player for ~10 s** rather than dropped
  (paintball, 2026-08-25 — a dropped registration silently made a champion seat play scripted).
- **How the episode settles early:** the play deadline is checked at every round boundary; hitting
  it calls `endEarly()`, which stops the round loop, autobanks every cog's held tokens, scores the
  rounds actually played, emits `end` with `reason: "deadline"`, writes `results.json` and the
  replay, and then — as cogame-lantern taught — keeps `/healthz` and `/global` answering for
  `shutdownGraceSeconds = 20` before `quit(0)`, because hosted certification pings the global
  websocket **after** the player pods start.

---

## Sim module

New code lives in `src/gift_refinements/`, mirroring paintbot's split (`src/ctf/`). What is forked,
what is kept, and what is deleted — by path:

| coworld-ctf path | gift-refinements | note |
|---|---|---|
| `src/ctf/sim_types.nim` | `src/gift_refinements/sim_types.nim` | fork: `GameVersion`, the flatty wire types, the constants table above. Field order is sacred, same as paintbot. |
| `src/ctf/sim.nim` | `src/gift_refinements/sim.nim` | fork: the tick loop and the seven numbered steps replace the CTF gameplay core. |
| `src/ctf/sim_config.nim` | `src/gift_refinements/sim_config.nim` | fork: `GameConfig` lifecycle + `config.update`; fields = the config schema in `## Packaging`. **Keep** the `attempt1Ms mod 1000` / `attempt1Ms + retryMs <= turnBudgetMs` guards verbatim. |
| `src/ctf/sim_state.nim` | `src/gift_refinements/sim_state.nim` | fork: logging, `gameHash`, event emission, spawn placement, pad state. |
| `src/ctf/arena.nim` | `src/gift_refinements/board.nim` | heavily reduced fork: the **fixed** 24 × 14 grid (wall ring, five pillars, 18 pads, 6 spawns), the beam trace, and the unit-cost Dijkstra the kernel uses. The terrain generator, `mapSpec`, symmetry, validators, pixel queries and `map_pool` are **deleted** — Gift Refinements has one authored board per variant. |
| `src/ctf/llm.nim` | `src/gift_refinements/llm.nim` | fork, nearly verbatim: credential ladder, haiku-only `bedrockModelIds()`, `requestFor`, `curly.makeRequests`. Log prefix `gift-refinements llm:`. |
| `src/ctf/decide.nim` | `src/gift_refinements/decide.nim` | fork: `seatViewJson` becomes the observation above, one batch per round, the retry batch, `fallbackRecord`, `budgetGuardRecord`, `repairMissingOrders`. |
| `src/ctf/directives.nim` | `src/gift_refinements/orders.nim` | fork: the order schema, the tolerant parser, the rune-safe `cleanText`, the clamp-and-flag rules. |
| `src/ctf/baselines.nim` | `src/gift_refinements/scripted.nim` | fork: the two baselines above; same "both kinds emit the SAME object" property, which is what makes the bounded-orders test meaningful. |
| `src/ctf/control.nim` | `src/gift_refinements/kernel.nim` | fork: order → per-tick action, the four jobs, the beam scheduler, the consume schedule. |
| `src/ctf/global.nim` | `src/gift_refinements/global.nim` | fork, heavily reduced: keep the sprite-protocol emitter, layer/object pooling, the chrome `TextMessage` smuggling and `boardRenderScaleFor`. **Delete** fog-of-war/FOV, first-person PiP, rig art, grenade/spray/shield/barrier families, endzone bakes, perks and handicaps. |
| `src/ctf/broadcast.nim` | `src/gift_refinements/broadcast.nim` | fork: `BroadcastTracker` + `buildStateJson` keep their shape; `teams` becomes the two headline plates, `roster` the six cogs, `lead` the tokens-in-play series, plus the appended `trust` block. |
| `src/ctf/events.nim` | `src/gift_refinements/events.nim` | fork: the event vocabulary below (same `jsonRow` / `eventsJsonl` shape and the same "live emission and re-simulation must be byte-identical" rule). |
| `src/ctf/replays.nim`, `src/ctf/replay_runtime.nim` | `src/gift_refinements/replays.nim` | rewritten: Gift Refinements records **state frames**, not inputs (below). |
| `src/ctf/server.nim` | `src/gift_refinements/server.nim` | fork of the route/artifact/shutdown skeleton; the player protocol becomes the JSON frames in `## Server`. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | kept, forked | still emits `window.CTF_WIRE={…}`. **The global keeps its name**: `client/chrome_common.js` reads `window.CTF_WIRE` at its line 72 and that file ships byte-for-byte, so renaming it would force a byte change in a file that must not change. `Dockerfile.replay-viewer`'s `grep -q '^window.CTF_WIRE={'` assertion is kept for the same reason. |
| `src/ctf/labels.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `paint.nim`, `rig_art.nim`, `roster.nim` | — | deleted. No articulated rigs, no perk roster, no paint, no generated terrain. |
| `tools/` probes, `caos*`, `arena/` wit bindings, `client/league_replayer.html`, `tools/map_editor*`, `tools/record_*.sh`, `scripts/` campaign map generators | — | deleted. Keep `tools/build_replay_viewer.sh` and `tools/gen_wire_constants.nim`, add `tools/ci/` and `scripts/art/gen_gift_art.py`. |

New files: `src/gift_refinements/ledger.nim` (the public gift ledger, the `net` matrix, the
defection rule), `src/gift_refinements.nim` (entrypoint, forked from `src/ctf.nim`: seed
randomisation **before** `config.update`, same sentinel handling),
`src/gift_refinements_player.nim` (from `src/paintball_player.nim`).

`tools/build_replay_viewer.sh` is the starter's with the image tag renamed
(`cogame-gift-refinements-replay-viewer-build`) and the `docker cp` source path changed to
`/workspace/gift-refinements/replay-viewer/dist/.`. The starter's copy **already carries the ecos
`mkdir -p` fix** (it creates the output parent before the containment check) — keep those lines
verbatim.

**Emscripten guard (chemistry, 2026-08-25):** `os.getAppDir` has no emscripten implementation and
dies with `value out of range: -1` *before* any fallback runs. Every `gameDir()`-style lookup in the
forked code is wrapped in `when not defined(emscripten)` and tries the working directory first.

### Event vocabulary (the replay's `events[]`)

One JSON row per event; `t` = tick, `seat` = slot, levels are integers `0|1|2`.

| `k` | fields | when |
|---|---|---|
| `spawn` | `t, x, y` | step 1, a pad regrew a raw token |
| `consume` | `t, seat, n, l0, l1, l2, score` | step 3, a cash-out (`n = l0+l1+l2`) |
| `gift` | `t, from, to, sent, got, n, fx, fy, tx, ty, dist` | step 4, a connected beam (`sent` = level spent, `got` = level received, `n` = 3 or 1) |
| `giftmiss` | `t, seat, dir` | step 4, a beam that found no cog |
| `spill` | `t, seat, lvl, lost, cause ("gift"\|"collect")` | steps 4/5, tokens lost to `invCap` |
| `collect` | `t, seat, x, y` | step 5, a pick-up |
| `defect` | `t, seat, on` | step 3, the first `consume` by `seat` while `gaveYou[seat][on] >= 3` and `youGave[seat][on] == 0`; at most one row per ordered pair per episode |
| `autobank` | `t, seat, n, score` | final tick / early settle |
| `order` | `t, seat, round, job, target, gift, consume, clamped, source ("llm"\|"retry"\|"fallback"\|"scripted"), say, notes, latencyMs` | one per seat per round boundary |
| `round` | `t, round, scores[6], held[6], gifts, minted, banked` | at each round close |
| `end` | `t, reason, ending, scores[6]` | terminal |

Volume per episode: ~400 `spawn`, ~350 `collect`, ~600 `gift`, ~90 `consume`, 72 `order`, 12
`round`, plus incidentals — under 2 000 rows. `notes` is recorded (it makes an LLM seat's reasoning
auditable) and drawn only in the feed's expanded row; `say` is the headline. Both are already
rune-truncated. Every gift, every consume and every defection being an event is what discharges the
idea's integrity clause: the trust graph is reconstructible from the bytes alone.

### The replay file (`gift-refinements.replay.v1`)

**Strict UTF-8 JSON, one document.** Gift Refinements records *state*, not inputs, so playback never
re-simulates, a seek is an array index, and there is no native/wasm divergence to chase (which is
also why `#mmwarn` and `ctf_mismatch_tick` are dropped).

```json
{"protocol":"gift-refinements.replay.v1","game":"gift-refinements","gameVersion":"1",
 "seed":1234567,
 "names":["Aro","Bex","Cyr","Dov","Eno","Fay"],
 "policyNames":["gift-refinements-mirror","gift-refinements-hoarder","gift-refinements-patron",
                "gift-refinements-reciprocator","gift-refinements-reciprocator",
                "gift-refinements-hoarder"],
 "colors":["red","orange","yellow","lime","blue","pink"],
 "config":{"variant":"refinery","cols":24,"rows":14,"cell":48,
           "rounds":12,"ticksPerRound":60,
           "walls":[[0,0],[1,0],"…every wall and pillar cell…"],
           "pads":[[4,2],[9,2],"…18, in the listed order…"],
           "spawns":[[2,2],[21,2],[2,11],[21,11],[2,6],[21,7]],
           "maxLevel":2,"giftMultiplier":3,"invCap":15,"beamRange":4,"giftCooldown":4,
           "maxBeamsPerRound":10,"collectCooldown":3,"moveCooldown":2,"consumeCooldown":10,
           "spawnTicks":30},
 "frames":[{"t":0,
            "c":[2,2,0,0,0,0,0, "…6 septets x,y,t0,t1,t2,score,flags…"],
            "p":[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]},
           "…720 frames…"],
 "series":{"pool":[[0,0],[1,0],"…one row per tick: tick, total tokens held by all cogs…"]},
 "beats":[{"t":60,"k":"round","n":1},{"t":97,"k":"firstgift"},{"t":214,"k":"super"},
          {"t":455,"k":"defect","seat":1},{"t":719,"k":"gameover"}],
 "events":[ "… the rows above …" ],
 "results":{ "… the results.json object verbatim …" }}
```

- **Self-sufficient by construction.** Aliases, policy names, body colours, the full board geometry
  (walls, pillars, pads, spawns), every rule constant, the seed, per-tick state, the pad occupancy
  bitmap, the tokens-in-play series, the beat timeline, every event and the final results all live
  in these bytes. The viewer contacts **no** server except S3 for the `.replay` file, and
  `results.reason` is inside the replay as well as in the hosted artifact (paintball, 2026-08-25 —
  a replay that carries its own result is byte-reconcilable with the artifact).
- The `flags` byte packs `consumedThisTick` (bit 0), `firedThisTick` (bit 1), `collectedThisTick`
  (bit 2). Beams themselves are drawn from the `gift`/`giftmiss` events, which the wasm module
  indexes into a tick → events map at load; the trust graph is accumulated from the same rows, so
  a seek to tick *n* rebuilds the graph as of *n*.
- Size arithmetic: 720 frames × ~60 integers ≈ **0.35 MB**, plus ~2 000 events ≈ 0.35 MB.
  `tests/test_replay.nim` asserts `< 8 MiB`.

---

## Server, player, protocol

### Game container (`/bin/gift-refinements`)

Routes, kept from the starter's `src/ctf/server.nim` because hosted certification probes exactly
these **before** the player pods start (lantern, 2026-08-23):

| route | behaviour |
|---|---|
| `GET /healthz` | `200 ok`, from process start until `shutdownGraceSeconds` after the artifacts are written |
| `GET /client/player?slot=N&token=T` | the seat's HTML shell (the starter's, trimmed); it never opens the player socket |
| `WS /player?slot=N&token=T` | the seat socket; a bad token is refused with a close, never a hang |
| `GET /client/global` | the broadcast client (`client/replay_broadcast.html`, embedded with `staticRead`) |
| `WS /global` | live spectator: the starter's sprite protocol + the chrome `TextMessage` |

`gift-refinements.player.v1` frames, JSON text:

- game → player:
  `{"type":"welcome","protocol":"gift-refinements.player.v1","slot":N,"name":"Cyr","rounds":12,"ticksPerRound":60,"variant":"refinery","aliases":["Aro","Bex","Cyr","Dov","Eno","Fay"]}`
  on connect; the `state` frame from `## Decisions` at every round boundary and at episode end;
  `{"type":"final","done":true,"slot":N,"scores":[…6…],"names":[…aliases…],"rounds":R,"reason":…,"ending":…}`,
  after which the player exits **0**.
- player → game: `{"type":"prompt","prompt":"<= 4000 chars","scripted":"reciprocator|hoarder|"}`,
  sent immediately on connect, again after `welcome`, and re-sent every 2 s for up to 10 s until the
  game acknowledges the registration (the paintball slot-admission race). Any other frame is ignored
  with a log line.

Startup: `src/gift_refinements.nim` randomises the seed **before** `config.update` (the starter's
rule — every seed-derived draw must follow the final seed), waits up to
`playerConnectTimeoutSeconds = 180` for six sockets but returns as soon as every connected socket
has registered, starts with whoever is there (missing seats play `reciprocator`), then runs the
round loop.

Shutdown, in this order (the starter's `finishEpisode` plus lantern's grace): send `final` to every
player socket → broadcast the last global frame → `sleep 500 ms` → write `results.json`
(`COGAME_RESULTS_METHOD`, `application/json`) → write the replay (`COGAME_SAVE_REPLAY_METHOD`,
`application/json`) → keep `/healthz` and `/global` answering for `shutdownGraceSeconds = 20` →
`quit(0)`. The player's receive loop wraps `receiveMessage` in `try/except CatchableError` and exits
**0** on a closed or truncated frame (raid, 2026-08-23 — otherwise `docker_smoke` passes and
certification fails intermittently).

### `results.json`

```json
{"names":["gift-refinements-mirror","gift-refinements-hoarder","gift-refinements-patron",
          "gift-refinements-reciprocator","gift-refinements-reciprocator","gift-refinements-hoarder"],
 "aliases":["Aro","Bex","Cyr","Dov","Eno","Fay"],
 "scores":[186,74,203,151,144,68],
 "win":[false,false,true,false,false,false],
 "collected":[41,63,38,44,46,61],
 "gifts_sent":[57,0,61,48,44,0],
 "gifts_received":[54,6,59,45,41,4],
 "tokens_given":[57,0,61,48,44,0],
 "tokens_received":[148,14,157,121,110,10],
 "banked_raw":[22,74,19,28,31,68],
 "banked_refined":[61,0,58,49,47,0],
 "banked_super":[103,0,126,74,66,0],
 "defections":[0,2,0,0,0,2],
 "reciprocity_x100":[38,0,38,39,40,0],
 "total_gifts":210,
 "total_minted":486,
 "rounds":12,
 "reason":"complete",
 "ending":"round_limit"}
```

`names` are **policy** names (platform side); aliases go to the players and into the replay's
`names[]`. Arrays are indexed by slot and always length 6. Field definitions, so nothing is guessed:
`scores[i] == banked_raw[i] + banked_refined[i] + banked_super[i]` (the score, higher better);
`collected[i]` = raw tokens picked up; `gifts_sent[i]` / `gifts_received[i]` = **beams** that
connected; `tokens_given[i]` = tokens spent gifting (one per connected beam);
`tokens_received[i]` = tokens landed in that seat's inventory by gift, after `invCap` losses;
`defections[i]` = `defect` events with `seat == i`;
`reciprocity_x100[i] = (100 * min(tokens_given[i], tokens_received[i])) div max(tokens_given[i], tokens_received[i], 1)`;
`total_minted` = tokens created by all gifts; `rounds` = rounds completed.

---

## Viewer

**All four viewer files come from ONE starter: `Metta-AI/coworld-ctf`.** Named explicitly, because
splicing two starters' halves (one's `MODULARIZE`/`EXPORT_NAME` link flags onto the other's
`onRuntimeInitialized` bootstrap) is what left cogame-lantern with a permanently blank theater:

| file | source (coworld-ctf, one starter for all four) | change |
|---|---|---|
| `replay-viewer/config.nims` | coworld-ctf `replay-viewer/config.nims` | verbatim except the emitted name (`gift_refinements_replay.js`) and the export list renamed `_gr_*`. **Keep the non-`MODULARIZE` link flags exactly as they are** — no `-s MODULARIZE=1`, no `EXPORT_NAME` — because the worker bootstraps with `Module.onRuntimeInitialized`. Keep `-O2 -s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--preload-file <root>/data@data`, `--mm:arc`, `--exceptions:goto`, `-d:noSignalHandler`, `-d:useMalloc`. |
| the wasm entry `.nim` | coworld-ctf `replay-viewer/ctf_replay.nim` → `replay-viewer/gift_refinements_replay.nim` | same structure: `stampStage`, `gr_load_replay`, `gr_frame`, `gr_input`, `gr_packet_ptr/_len`, `gr_error_ptr/_len`, `gr_stage_ptr/_len`, and the `emscripten_exit_with_live_runtime()` epilogue (without it Nim's `main` destroys every global while JS keeps calling in). `gr_load_replay` parses the JSON replay, hydrates the frame array and builds the tick → events index; `gr_frame` advances/seeks and rebuilds the viewer packet. `ctf_mismatch_tick` is **dropped** — there is no re-simulation to mismatch. **The packet built by `gr_load_replay` is the only one carrying `meta`**; read it directly and never re-derive it via `packetAt(0)` (matrix-games, 2026-08-24). A mid-seek click that arrives before the first chrome frame is **queued** and converged with a bounded per-frame tick walk (`SeekTicksPerFrame = 240`), never dropped (paintball, 2026-08-25). |
| `static_replay*.js` | coworld-ctf `replay-viewer/static_replay.js` + `replay-viewer/static_replay_worker.js` | verbatim apart from the `ctf_*` → `gr_*` export names, the worker name string (`gift-refinements-static-replay`), and **one added line** in `showFailure`: `document.documentElement.setAttribute('data-replay-error', error.message \|\| String(error))`. The worker keeps `importScripts('./wire_constants.js','./broadcast_core.js','./gift_refinements_replay.js')` and `Module.onRuntimeInitialized` — the matched pair for the link flags above. |
| `index.html` | coworld-ctf `client/replay_broadcast.html`, spliced by `Dockerfile.replay-viewer`'s `sed` into `replay-viewer/dist/index.html` | the starter's page with a game block appended (below). |

**The shell sets `data-replay-loaded="true"` on its first drawn frame and `data-replay-error` on
failure.** `static_replay.js` already does the first half: its `onWorkerMessage` `'loaded'` branch
(line 161) fires when the worker has parsed the replay and rendered frame 0, and sets
`data-replay-loaded="true"` on `<html>`; with the added `showFailure` line it sets
**`data-replay-error`** (to the error message) on any failure — worker crash, unreadable message,
missing replay URL, or a `gr_load_replay` error surfaced through `gr_error_ptr/_len`. Those are the two signals `tools/ci/viewer_smoke.mjs` and
phase 60's `viewer-check.yml` read. If a `coworld-replay` bridge `ready` message is posted at all,
it is posted from a callback that fires **after** `data-replay-loaded="true"` is set, never on rAF
timing at the call site (chorus, 2026-08-24). The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and `tools/build_replay_viewer.sh` is the
`coworld build` hook that produces the bundle. **Never a `/client/replay` pod.**

### Chrome provenance (exact)

- `client/chrome_common.js` is copied **byte-for-byte**. Nothing in it is edited — which is why the
  wire-constants global keeps the name `window.CTF_WIRE` and why the two headline plates ride the
  starter's own `teams` / `roster` machinery rather than a new one.
- `client/broadcast_core.js` is **forked** (it is paintbot's renderer — the playbook's "treat the
  starter's renderer as the exact template"): the board draw becomes the tile grid, pillars, seep
  pads, loose tokens, cogs, inventory badges and gift beams. Its ingest/packet plumbing,
  letterboxing and layer pooling are untouched.
- `client/replay_broadcast.html` is **the starter's page with a game block appended**, never a
  rewrite that reuses its ids. The only edits inside the starter's own markup/script are these
  three, and no others:
  1. **Removed elements** (with their CSS blocks and the JS branches that touch them):
     `#viewpanel` and its children `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`,
     `#zoom-slider`, `#zoom-in`, `#zoom-read`; `#fpv` and its children `#fpv-canvas`, `#fpv-hud`,
     `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`;
     `#povBadge`; `#mmwarn`.
     **Zoom decision: `#viewpanel` is dropped entirely.** The 24 × 14 board is fixed and always fits
     the frame, so there is nothing to pan to and nothing a minimap could add; the zoom bar +
     minimap exist only for boards larger than the frame.
  2. **Two re-lettered literals**: the scorebug's `Lives` label becomes `Tokens`, and the momentum
     strip's label becomes `TOKENS IN PLAY`.
  3. `#lockerroom` gains `pointer-events: none` so its ~1.5 s overlay stops swallowing transport
     clicks (ecos, 2026-08-23).
  Everything else — `#stage`, `#board`, `#chrome`, `#scorebug`, `#plates-l`, `#plates-r`, `#clock`,
  `#clock-time`, `#clock-caption`, `#bannerlane`, `#killfeed`, `#transport` and all its buttons plus
  `#btn-spoilers`, `#scrub`, `#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`, `#scrub-head`,
  `#endcard`, `#status` — is the starter's, unchanged.
- **The appended game block** owns: the two headline plates' totals, the roster strip, the **trust
  graph** panel, the feed row builders, the beat-marker CSS, and the plate colours
  (`.plate.gifts{--tc:#57c98a}`, `.plate.banked{--tc:#e2b23c}` — unknown team keys fall back to the
  starter's `AMBER` constant in `buildFlag`, so nothing breaks if a key is missed). Its beat builder
  is named **`buildGiftBeats`**, never `markBeat`: a game-block `function markBeat` is hoisted over
  the chrome alias block's `var markBeat = C.markBeat` and silently kills every scrubber beat
  (tandem, 2026-08-23). A scope-duplication test over the alias list enforces it. `pushFeed(row)`
  keeps the starter's **one-argument** signature (changing it is what broke cogball 0.1.4).

### Transport rules

`relayout()` sets `--band` and `--hudscale` on `:root` (and `--topband` for the scorebug strip);
every chrome measure derives from `--u = 1px * var(--hudscale)`. **No overlay sits in the transport
band**: the trust-graph panel, the roster strip, the feed and the banner lane are all clipped to the
board region between `var(--topband)` and `var(--band)`. The **endcard stops at `var(--band)`** (it
is `inset: var(--topband) 0 var(--band) 0`, the starter's own rule) and is **dismissed by every
seek**. Scrubber beats are clickable, **labelled buttons** — one per emitted kind, with CSS for
**every** kind the game emits: `round`, `firstgift`, `super`, `defect`, `gameover`. The whole beat
timeline ships on the first HUD frame (the starter's `beats` field), so the scrubber is complete
before playback starts and `?spoilers=0` still holds beats back until the playhead reaches them.
The **last beat is `gameover` at the final tick**, so the rail's right edge always reaches the
endcard (territory, 2026-08-25).

### What it draws

- **Board.** Foundry-floor tiles, five stone pillars, the wall ring, 18 seep pads drawn as glowing
  vents (dim while regrowing, bright with a loose raw token sitting on them), and six cogs as 36 px
  bodies in their slot colour with the alias under the feet.
- **Token sheen (the idea's headline readout).** Every token — loose, held or in flight — is drawn
  at its level: **raw** = dull grey ore, **refined** = polished bronze with a rim highlight,
  **super** = white-gold with a slow four-point sparkle. Each cog carries a three-slot inventory
  badge above its head, `●3 ◆4 ✦2`, each slot in its sheen, hidden when the count is 0.
- **Gift beams (the idea's headline readout).** A connected beam draws a bright lane from giver to
  receiver in the giver's colour, with **three** token sprites of the received level flying along it
  and landing in the receiver's badge with a pop; a super pass-through flies **one**. A miss draws a
  short grey fizzle. A `spill` drops the excess tokens off the badge and fades them out.
- **Trust graph (the idea's headline readout).** An appended panel, right side above the feed: the
  six cogs on a hexagon, an arc between every pair that has ever gifted, thickness = tokens moved,
  arrowheads both ways. An edge is **green** when the two directions are within 2× of each other,
  **amber** when one-sided but young, **red** once a `defect` event has fired on it, and a red skull
  pip sits on the defector's node. Under the hexagon, the three heaviest edges as text rows
  (`ARO ⇄ CYR  57 ↔ 54`). The graph is rebuilt on seek from the events up to the playhead, so
  scrubbing back un-draws a defection.
- **Scorebug** (`#scorebug` / `#plates-l` / `#plates-r`, the starter's plate machinery): two plates
  keyed `gifts` and `banked` — `GIFTS GIVEN` (total connected beams) and `TOKENS BANKED` (total
  consumed by all six), headline via `teams[k].policies`, the big number via `lives-<k>` with the
  label re-lettered `Tokens`. Underneath each: tokens minted this episode, and the count of
  defections.
- **Roster strip** (appended, under the scorebug): six chips in score order —
  `CYR · gift-refinements-patron · 203` — tinted with the seat's body colour, each with its
  three-slot inventory badge and a small ⇄ reciprocity pip. The **policy** name appears here and
  only here (plus `results.names`); the board and every prompt show the alias.
- **Tokens-in-play chart.** `#momentum`, the SVG under the scrub track, label `TOKENS IN PLAY`: one
  stepped line from `series.pool`, on the same tick axis as the playhead — it climbs while a chain
  is running and drops off a cliff every time somebody cashes out. Fed exactly like paintbot's lives
  series — `state.lead = {"teams":["pool"], "pts":[[t, tokensHeld], …]}` — so `ingestLeadSeries` /
  `renderMomentum` in `client/chrome_common.js` need **no change**.
- **Clock** (`#clock-time`, `#clock-caption`): `ROUND 5 / 12`, caption `tick 300 of 720`. Spelled
  out, never `R5`.
- **Feed** (`#killfeed`, the starter's `pushFeed(row)`): one row per `gift`
  (`ARO → CYR · 1 raw becomes 3 REFINED`), per `consume`
  (`BEX BANKS 7 — 3 raw, 4 refined`), per `defect`
  (`BEX TOOK 9 FROM DOV AND GAVE NOTHING BACK`), per `spill`
  (`CYR OVERFLOWS — 2 super lost`), and the seat's `say` as the quoted tail of its `order` row,
  tagged `auto` when `source` is `fallback` or `scripted`.
- **Endcard**: the ending in words (`ROUND LIMIT` / `TIME`), the winner's alias and policy, the six
  scores, and the line `210 gifts · 486 tokens minted from 293 raw · 2 defections`.

**Legibility at 360 px is a requirement** — the featured-match iframe is ~360 px wide.
`#stage.tiny` (already switched on at `boardW <= 620`) shrinks the feed and pips; carry bullwhip's
`.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and hide chip labels under 640 px so the roster
chips degrade to `CYR 203`. Under 480 px the trust hexagon collapses to its three text rows and the
inventory badge drops to a single total with the sheen of the highest level held. Check at 360 px:
both headline plates with their numbers, the `ROUND 5 / 12` clock, the tokens-in-play chart, at
least one beam mid-flight and the top three roster chips readable.

**Real art, not placeholders.** `scripts/art/gen_gift_art.py` (Pillow, committed, deterministic)
renders and commits into `data/`: foundry floor and pillar tiles, the wall ring, the seep pad in lit
and dark states, token sprites at three sheens × two sizes (board and badge), the beam lane and its
flying-token frames, the consume burst, the spill puff, six cog bodies
(`cog_<colour>_front.png`, `_beam.png`, `_bank.png`), the inventory-badge frame, the trust-graph
node and arc art, and the loading screens the `#lockerroom` markup expects
(`client/art/lockerroom/bg.jpg` = a refinery floor at shift change, plus six portraits replacing the
soldier `.webp`s). `Dockerfile.replay-viewer`'s copy list and its `test -f` assertions are updated to
those file names; the `league.html` sed step and `client/league_replayer.html` are dropped with it.

---

## Packaging

**`compose.yaml`** — one service, one image (game + player binaries):

```yaml
services:
  gift_refinements:
    image: coworld-gift-refinements:latest
    platform: linux/amd64
    build: {context: ., dockerfile: Dockerfile, network: host}
```

The service name is the single source of the manifest placeholder: `services.gift_refinements` →
**`{{GIFT_REFINEMENTS_IMAGE}}`** (lantern, 2026-08-23 — `coworld build` hard-fails anything else and
`{{GAME_IMAGE}}` is not a thing; the underscored service name is the collab-cooking precedent that
released canonical). `tests/test_manifest.nim` asserts the derivation.

**Names.** `game.name` is **`gift-refinements`** — identical to the repo slug, the softmax.com page
slug, the secret namespace and the league-seed key, so the three name spaces that bit commons-family
and cooperative-hunting cannot diverge here. The secret ref is
`secret://coworld/gift-refinements/anthropic_api_key`, and the release workflow reads the namespace
out of `game.name` rather than hardcoding `$SLUG`.

**`coworld_manifest_template.json`** — the current strict shape (hive + collab-cooking): top-level
`$schema`, ≥ 3 `tags` (`gift-refinements`, `trust`, `reciprocity`, `grid`, `llm-driven`,
`melting-pot`, `six-player`), top-level `episode_timeout_minutes: 20`, top-level `player[]`,
`variants[].description` on every variant, `game.owner` present, **no** top-level `replay_viewer`,
**no** top-level `version`, **no** `game.display_name`, and a real JSON-Schema `game.config_schema`
with `required: ["tokens"]` and `minItems`/`maxItems` on **every** array property (tandem,
2026-08-23).

- `game.name`: `gift-refinements`; `game.replay_viewer.bundle`: `static-replay-viewer`.
- `game.runnable`: `{"type":"game","image":"{{GIFT_REFINEMENTS_IMAGE}}","run":["/bin/gift-refinements"],
  "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/gift-refinements/anthropic_api_key"},
  "source_url":"https://github.com/Metta-AI/cogame-gift-refinements/tree/main"}` — the `env` entry is
  mandatory: without it the hosted game container never sees the coworld secret and every league
  episode silently plays scripted (hive, 2026-08-23), which surfaces only at phase 60 check 4.
- `game.config_schema` properties: `tokens` (string array, `minItems 1`, `maxItems 6`, required),
  `players` (array of `{name}`, `minItems 1`, `maxItems 6`), **`num_agents` (integer, 1..6, default
  6)**, `seed`, `rounds` (1..24, default 12), `ticksPerRound` (10..120, default 60), `pillars`
  (integer 0..5, default 5), `spawnTicks` (5..240, default 30), `beamRange` (1..16, default 4),
  `giftCooldown` (1..30, default 4), `maxBeamsPerRound` (0..30, default 10), `giftMultiplier` (1..6,
  default 3), `maxLevel` (1..4, default 2), `invCap` (1..64, default 15), `collectCooldown` (1..30,
  default 3), `moveCooldown` (1..8, default 2), `consumeCooldown` (1..60, default 10),
  `attempt1Ms` (5000..60000, default 20000), `retryMs` (1000..60000, default 12000),
  `turnBudgetMs` (6000..120000, default 34000), `minTurnSeconds` (0..60, default 25),
  `maxOutputTokens` (200..2000, default 1000), `model` (string), `episodeTimeoutSeconds` (default
  1200), `playerConnectTimeoutSeconds` (default 180), `shutdownGraceSeconds` (default 20),
  `showPlayerLabels` (bool, default true). `additionalProperties: false`.
- `game.results_schema`: the `results.json` object above (slot arrays `minItems 1`, `maxItems 6`).
- `game.docs` (**text**, not uri): `{"readme":{"type":"text","value":"<what it is: six cogs on a
  foundry floor; a beam that costs you one raw token and hands somebody else three refined ones;
  consuming pays +1 a token whatever its grade, so the only way anything is worth more than it
  started is to give it away and hope it comes back>"},
  "pages":[{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<the board, the
  seven-step tick order, the rawest-token gift rule, the 3× refinement ladder and the super
  pass-through, the 15-per-level cap, consuming and the final-tick close, scoring, end
  conditions>"}},
  {"id":"policies.md","title":"Fielding a policy","content":{"type":"text","value":"<the
  standing-order schema, the caps, the observation, PLAYER_PROMPT / PLAYER_SCRIPTED how-to>"}}]}`.
- `game.protocols` — **both**, as `{"type":"text","value":…}` objects (the platform validator
  rejects bare strings): **`player`** (the `gift-refinements.player.v1` frames, the observation, the
  reply schema and its caps, and the explicit note that `say` is spectator-only and never reaches
  another seat) and **`global`** (the `/global` sprite + chrome frame, and the static bundle's
  `index.html?replay=<url>`).
- `player[]` — three entries, all on `{{GIFT_REFINEMENTS_IMAGE}}` with
  `run: ["/bin/gift-refinements-player"]`: `gift-refinements-player` (no env — a prompt policy;
  `PLAYER_PROMPT` is supplied at upload time), `gift-refinements-reciprocator`
  (`env: {"PLAYER_SCRIPTED":"reciprocator"}`), `gift-refinements-hoarder`
  (`env: {"PLAYER_SCRIPTED":"hoarder"}`).
- **`variants[]` — four; `num_agents: 6` in every one**, and `players` is the six aliases in slot
  order in every one:

  | id | name | changed knob | `num_agents` |
  |---|---|---|---|
  | `refinery` | Refinery (default) | the constants table as written | **6** |
  | `scarce` | Scarce seams | `spawnTicks: 75` — raw is rare, so a chain is worth far more than a pick-up | **6** |
  | `long-beam` | Long beams | `beamRange: 8` — reciprocating at distance is easy, walking away is hard | **6** |
  | `open-floor` | Open floor | `pillars: 0` — no cover, every cog is always hittable from somewhere | **6** |

  All four share `rounds: 12, ticksPerRound: 60` and every other constant in the table. **The league
  default variant is `refinery`** — it is the balanced configuration the oracle gates against and
  the one where reading the trust graph beats hoarding; phase 50 passes it as `default_variant_id`
  at seed time (chemistry, 2026-08-25: the seed body accepts it at the top level, and gridlock's 409
  shows it cannot be re-seeded later).
- `certification`: `game_config` =
  `{num_agents: 6, seed: 7, rounds: 6, ticksPerRound: 60, minTurnSeconds: 0,
  playerConnectTimeoutSeconds: 180, players: [ …the six aliases… ]}` — and **no runner-managed
  `tokens`** (collab-cooking, 2026-08-25: `manifest_invalid` otherwise) — with `players` =
  2 × `gift-refinements-player`, 2 × `gift-refinements-reciprocator`, 2 × `gift-refinements-hoarder`:
  **every declared player entry seated at least once**, because `players-run` seats the whole roster
  and a `baseline × N` fixture fails `players_missing` (raid, 2026-08-23). Offline the
  `gift-refinements-player` seats fall back to `reciprocator`, so the fixture is deterministic.
  **6 × 60 = 360 ticks = 15 s of video**, which outlasts the 10 s viewer soak, and with
  `minTurnSeconds: 0` and no credentials it runs in a few seconds. The certify step in
  `coworld-release.yml` passes **`--timeout-seconds 300`** (cooperative-hunting, 2026-08-25) so the
  60 s default can never truncate it.

**Other packaging files:** `Dockerfile` (the starter's two-stage nimby build; produces
`/bin/gift-refinements` and `/bin/gift-refinements-player`), `Dockerfile.replay-viewer` (the
starter's, with the gift-refinements file list and the same `test -f` / `grep -q` assertions, minus
`league.html`), `tools/build_replay_viewer.sh` (the starter's, image tag and `docker cp` path
renamed), `.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
`tools/ci/docker_smoke.sh` with `<SEATS>` substituted to **6** and `<slug>` to `gift-refinements`,
`tools/ci/viewer_smoke.mjs` copied verbatim, `tools/ci/dom_text_smoke.mjs`,
`tools/ci/renderer_fixture.html`, `tools/ci/check_manifest_loads.py` (runs the installed coworld's
own `_load_template_manifest` — collab-cooking, 2026-08-25), and `tools/ci/policies.json` naming
`gift-refinements-mirror` and `gift-refinements-patron` (both `PLAYER_PROMPT`, each with
`env: {"USE_BEDROCK":"true"}` — without it the platform gives the player pod no Bedrock sidecar and
the seat silently plays scripted, cogolf 2026-08-24) plus the fillers
`gift-refinements-reciprocator` and `gift-refinements-hoarder`.

---

## Tests

All run in `ci.yml`; the sandbox cannot run any of them locally.

1. **`tests/test_board.nim` — the board.** Exactly 72 wall-ring cells and 20 pillar cells; exactly
   18 pads at the listed cells, none on a wall, pillar or spawn, no duplicates; the six spawn cells
   are distinct, passable and pad-free; every passable cell is reachable from every spawn; the beam
   trace stops at walls, pillars and the first cog, and never leaves the board; `pillars: 0` removes
   exactly 20 cells and changes nothing else.
2. **`tests/test_sim.nim` — sim units.** A gift spends the **lowest** held level (a cog holding
   `{1 raw, 5 refined}` sends raw); level 0 → 3 × level 1; level 1 → 3 × level 2; level 2 → **1** ×
   level 2 (pass-through); receipt above `invCap = 15` is lost with `spill`; a beam with an empty
   inventory does not fire; a miss costs no token but sets the cooldown; a cog cannot gift itself;
   `collect` at `t0 == 15` refuses and spills; `consume` scores `t0+t1+t2` and zeroes all three;
   `consume` resolves **before** gifts on the same tick; the final-tick `autobank` banks every cog
   and is counted in `scores`; cooldowns (`move 2`, `collect 3`, `gift 4`, `consume 10`) gate
   exactly; two cogs cannot share a cell and the lower slot wins; pad regrow at exactly
   `spawnTicks = 30`; **determinism** — the same seed and the same order script produce an identical
   `gameHash` after 720 ticks, twice in one process and across a fresh server.
3. **`tests/test_ledger.nim` — the trust bookkeeping.** `youGave` / `gaveYou` / `net` are exact over
   a scripted beam sequence; a `defect` row fires exactly once per ordered pair and only when
   `gaveYou >= 3` and `youGave == 0` at a `consume`; `reciprocity_x100` matches its integer formula
   on hand-built totals including the both-zero case; the ledger rebuilt from `events[]` alone
   equals the live ledger at every round boundary (this is what makes the viewer's seek-accurate
   trust graph correct).
4. **`tests/test_baseline.nim` — bounded orders / legality.** For 12 seeds × 720 ticks on all four
   variants, with all-`reciprocator`, all-`hoarder` and a 3/3 mix: every emitted order's `job` and
   `consume` is inside its enum, `target` is `null` or one of the five *other* aliases, `gift` is in
   0..10 and never exceeds tokens held; every per-tick action is one of the eleven vocabulary
   values; no cog is ever outside the board, in a wall or a pillar, or sharing a cell; no level
   count exceeds `invCap` or goes negative; scores never decrease; `hoarder` fires **zero** beams
   across every seed; two `reciprocator`s that have exchanged once keep exchanging; neither baseline
   raises, and neither takes more than 1 ms per round.
5. **`tests/test_feasibility.nim` — the oracle, as a CI precondition.** Gates (a)–(d) of
   `## The game`, over seeds 1..12 on all four variants, including the test-only `leech` bot for
   gate (c). Any constant change that breaks the economy fails here rather than in a dead replay.
6. **`tests/test_replay.nim` — end-to-end + strict UTF-8.** Plays a full scripted episode headless,
   writes `results.json` and the replay, then re-reads the replay **bytes**: `validateUtf8 == -1`
   (strict), parses as JSON, `protocol == "gift-refinements.replay.v1"`,
   `frames.len == ticksPlayed`, `series.pool.len == ticksPlayed`, every event tick in
   `0..ticksPlayed`, at least one `collect`, `gift`, `consume` and `autobank`, exactly `rounds`
   `round` events and exactly one `end`, `results.scores.len == 6`, `results.reason` in
   `{complete, deadline, forfeit}`, `results.ending` in `{round_limit, deadline, forfeit}`,
   `config` carries every constant the viewer reads, `sum(results.scores)` equals the total of all
   `consume.n` + `autobank.n`, file size `< 8 MiB`. A seat is fed a `say`/`notes` of multi-byte
   runes exactly at the 80/320 caps and the recorded strings are asserted valid UTF-8 and ≤ the cap
   (the bullwhip byte-truncation bug).
7. **`tests/test_llm.nim` — decision layer.** `extractJsonObject` on fenced and prose-prefixed
   replies; unknown `job` → invalid; own alias as `target` → invalid; `gift: 0` with
   `job: "meet"` and a valid target → legal; `gift: 40` → clamped to 10 with `clamped: true`;
   `gift > 0` with `target: null` → invalid; a stubbed transport that times out, 429s, 403s or
   returns junk produces `reciprocator` orders for those seats, never raises, and marks
   `source: "fallback"`; a `max_tokens` stop raises the named "cut off at max_tokens" error;
   **one batch carries all open seats** (assert `RequestBatch.len == openSeats`, i.e. 6 on round 1,
   and that the retry batch carries only the failed seats); `minTurnSeconds` holds the worst-case
   request rate under 30/min.
8. **`tests/test_manifest.nim` — packaging.** `num_agents == 6` in **all four** variants and in
   `certification.game_config`; the image placeholder equals the one derived from `compose.yaml`'s
   service name (`{{GIFT_REFINEMENTS_IMAGE}}`); `replay_viewer.bundle == "static-replay-viewer"`;
   `game.name == "gift-refinements"` and the `secret://coworld/<ns>/…` namespace equals it;
   `game.docs.readme` + non-empty `pages`; `game.protocols.player` **and** `global` present and both
   `{"type":"text",…}` objects; `ANTHROPIC_API_KEY_URI` in `game.runnable.env`; every `player[]` id
   appears at least once in `certification.players`; the cert fixture declares no `tokens`;
   `episode_timeout_minutes` top-level; every array property in `config_schema` carries `minItems`
   and `maxItems`.
9. **`tests/test_broadcast.nim` — chrome frame.** `teams` keys are exactly `gifts` and `banked`,
   each carrying `policies: [<label>]` and `lives` = its total; `roster[]` has 6 entries carrying
   the alias in `name` and the **policy** name in `pol`; `lead.teams == ["pool"]` and `lead.pts`
   rows are `[t, tokensHeld]`, the shape `ingestLeadSeries` expects; `beats` carries only the five
   declared kinds and the last beat is `gameover` at the final tick; `over` is present on the
   terminal frame with the ending string; every feed row's text is ≤ the caps; and a
   **scope-duplication test** asserts no game-block function name collides with the chrome alias
   list (`markBeat` et al., tandem).
10. **`docker-smoke` (`tools/ci/docker_smoke.sh`, `<SEATS>` = 6).** Builds the image, runs a real
    6-seat episode in containers off the cert fixture, asserts the **player** containers each exit 0
    (raid, 2026-08-23) as well as the game, validates `results.json` against the results schema, and
    copies the replay to `SMOKE_REPLAY_OUT` (`dist/smoke/replay.json`), uploaded as the
    `smoke-replay` artifact.
11. **`wasm-viewer` job — the bundle is EXECUTED, not merely built.** `needs: docker-smoke`,
    downloads `smoke-replay`, builds the bundle via `tools/build_replay_viewer.sh`, installs
    Playwright pinned **1.55.0**, and runs **`tools/ci/viewer_smoke.mjs`** against that replay over
    local HTTP with `--strict-text-bounds` (fixed arena → `canvas_text.never_inside` must be 0) and
    `--soak 10` (the 15 s cert replay outlasts the window). Pass requires
    `data-replay-loaded="true"` **and** three different clock readouts at 0 %, 50 % and 100 %;
    `data-replay-error` or silence fails the job. Evidence (`viewer-smoke.png`, `viewer-smoke.json`)
    uploads on success and failure. Two further steps in the same job: `viewer_smoke.mjs
    --strict-text-bounds` against **`tools/ci/renderer_fixture.html`** (the real renderer with
    full-cap 80-char `say` strings, a beam in flight and a full inventory badge on **every** seat at
    several canvas sizes, because `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY` and therefore
    produces a replay with zero LLM text — cogchemists, 2026-08-24), and
    **`tools/ci/dom_text_smoke.mjs`** over the real page at 13 viewports down to 360 px, asserting
    the feed rows, trust-graph rows and roster chips are not clipped and their strings are still
    full length (collab-cooking, 2026-08-25).
12. **`check_manifest_loads`** — a `ci.yml` step that runs the installed coworld package's own
    `_load_template_manifest` against `coworld_manifest_template.json`, so a template phase 40 would
    reject fails in repo CI instead.

---

## Out of scope (v1)

- **Per-tick policy sockets.** A seat submits one standing order per round; the kernel emits the
  per-tick grid, beam and consume actions. A direct per-tick action channel for RL/vector policies
  is not shipped.
- **A talk channel between cogs.** "Trust with nothing but reciprocity and a beam" is taken
  literally: `say` is spectator-only, and the only signals a cog can send are a beam and where it
  stands. No contracts, no escrow, no promises — that is coworld #11's job.
- **Partial or targeted consumption.** `consume` takes everything, at every level, exactly as the
  idea states. No "bank the raw, keep the super" order.
- **Stealing, zapping, blocking or damage.** A cog can never remove a token from another cog, and
  there is no combat beam. The only involuntary loss is the `invCap` spill.
- **More than two refinements, or level-dependent payouts.** `maxLevel = 2` and every consumed token
  is worth exactly +1, per the idea. `maxLevel` is a config knob but no shipped variant moves it.
- **Trading, offers and prices.** Gifts are unilateral; there is no matched-offer machinery (that is
  cogame-fruit-market).
- **Fog of war.** Positions, scores, consumes and the whole gift ledger are public; only inventories
  are private. Paintbot's FOV, first-person PiP and POV lens are deleted, not repurposed.
- **Procedural boards, map generation, the map editor and the league replayer page** — inherited
  paintbot machinery, all deleted rather than carried dark. One authored board; four variants that
  only change constants and the pillar list.
- **Cross-episode reputation.** Every episode starts from the seeded opening state with an empty
  ledger; nothing carries over except the league rating.
- **Re-simulating playback.** The viewer decodes recorded state; there is no replay-hash mismatch
  mode, no `--mismatch-quit`, and no `#mmwarn`.
