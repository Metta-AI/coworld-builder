# Firm: one manager who sees the market, four workers who see the machines

Five cogs run a small factory for eight shifts. One **Manager** seat sees the order board (how many
units of each product line the firm can actually sell) and can do exactly two things: write a memo
and set the pay rule. Four **Worker** seats each own one machine, see its condition — which the
manager never sees — and choose how to spend a ten-hour shift: running the line they were told to
run, running a different one, maintaining the machine, or doing nothing at all. Workers score the
pay they take home net of the toil it cost them; the manager scores the firm's profit. Principal
and agent, one episode.

Built on `Metta-AI/cogame-bullwhip` (mounted read-only at `/workspace/starters/cogame-bullwhip`),
the newest parley-lineage template: a Nim game server implementing the Coworld runtime contract, a
pure `sim` module shared by server / tests / wasm viewer, LLM decisions where **a policy is just a
prompt**, always-available scripted baselines, **one parallel LLM batch per simultaneous turn**,
and the parley broadcast chrome around a canvas stage. Bullwhip is the starter because Firm has
exactly bullwhip's shape — a turn-based, hidden-information, simultaneous-decision, mixed-motive
*economic* game whose seats answer with a small numeric payload plus one short line of free text,
whose watchability is a scorebug + feed + stage rather than a physics loop, and whose per-turn cost
is one batched LLM round trip. Bullwhip is also the only starter whose `decideAll` already fires
one parallel batch per turn, which is the whole timing model here.
The starter is `Metta-AI/cogame-bullwhip` and **every convention there holds here unless this note
says otherwise.**

Source idea, verbatim:

> 17 Firm — one manager writes the instructions; four workers who see what the manager can't do the
> work
>
> A manager seat sees aggregate demand and can only send written directives and set pay splits;
> worker seats (separate policies) see local machines and can shirk, comply, or improvise. Revenue
> splits per the manager's rule; workers score their pay, the manager scores the firm's profit.
> Principal-agent in one episode.
>
> Seats: 5 (1 + 4)
> Motive: hierarchical, incentive-misaligned
> Policy interface: LLM prompt (manager) + RL (workers)
> Fills gap: hierarchy / delegation / incentive design
> Integrity (anti-collusion): Manager and workers never share an account — a same-author firm has
> perfectly obedient workers, which erases the principal-agent tension the game exists to measure.
>
> Replay plan (watchability): Factory floor: the manager's directives fly as paper planes from a
> glass office; workers visibly work (sparks) or shirk (idle sway); payday streams coins according
> to the split. Mutinies over unfair splits are the drama beat.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

*Coordinator rail, not revisited: the idea's "Policy interface: LLM prompt (manager) + RL
(workers)" is a suggestion to outside submitters. In this build **every** seat is LLM-prompted with
a scripted baseline fallback, one image, env-switched (`PLAYER_PROMPT` vs
`PLAYER_SCRIPTED=<name>`), per the stack pins in `playbooks/make-coworld.md` §Phase 0.*

---

## The game

### Seats and roles

- **Seats: exactly 5.** `num_agents` = **5** everywhere — both manifest variants, the certification
  fixture, and `<SEATS>` in `tools/ci/docker_smoke.sh`.
- **Roles**: `RoleNames = ["Manager", "Worker"]`, role ids `0` and `1`. Exactly one Manager and four
  Workers.
- The **seat → role assignment is a seed-drawn permutation** (`roleOf[seat]`), exactly as bullwhip
  permutes stages: shuffle `[0, 1, 1, 1, 1]` with the episode rng. A policy therefore cannot choose
  to be the manager, and no slot is structurally stuck on the floor. `managerSeat` is the manager's
  seat index; `workerSeat[0..3]` are the four worker seats in ascending seat order, and
  `workerIndex[seat]` ∈ `0..3` for worker seats, `-1` for the manager.
- **Machines are numbered 1–4 for humans** (prompts, feed, scorebug, canvas) and indexed `0..3`
  internally. Machine `w` belongs to worker `w`. A spectator reads `MACHINE 3`, never `m2`.
- Seats play under **anonymous cog aliases** drawn from the seed (`CogNames`, bullwhip's list kept
  verbatim). Policy names are spectator-side only — see *Two name spaces* below.

### The floor (what exists, as data)

Everything random is drawn once at `initSim` from a single rng stream, in this fixed order —
**roles, demand levels, switch shift, aliases** — so a replay re-derives the whole episode from the
seed plus the recorded decision events.

**Two product lines, `A` and `B`.** Every machine is *set to* one line at a time.

**Machine `w`** (`MachineState`):

| field | type | meaning |
|---|---|---|
| `setup` | `"A"` \| `"B"` | the line the machine is currently set to (public to everyone) |
| `condition` | `int 0..100` | mechanical health, starts at **100**. **Private to its worker.** |
| `run` | `int 0..10` | hours the worker spent running last shift (private to its worker) |
| `maint` | `int 0..10` | hours the worker spent maintaining last shift (private to its worker) |
| `units` | `int` | units the machine delivered last shift (**public**) |
| `pay` | `float` | dollars the worker was paid last shift (public) |
| `toil` | `float` | the worker's own cost of last shift's hours (**private to its worker**) |
| `order` | `"A"` \| `"B"` | the line the manager ordered for this machine (public) |

Initial state: `condition = 100` on all four; `setup` = `A`, `A`, `A`, `B` for machines 1, 2, 3, 4;
`run = maint = units = 0`; `order` = each machine's own initial setup.

**The order board (aggregate demand)** — the manager's private information:
`demandA[s]`, `demandB[s]` for shift `s`, an array of length `shifts + 2` drawn at `initSim`:

- `HighDemand = 30 + rng.rand(7)` (30..36) and `LowDemand = 12 + rng.rand(7)` (12..18), each drawn
  once for the whole episode.
- `switchShift = 3 + rng.rand(3)` (3..5).
- For `s < switchShift`: `demandA[s] = HighDemand`, `demandB[s] = LowDemand`.
  For `s ≥ switchShift`: `demandA[s] = LowDemand`, `demandB[s] = HighDemand`.
- The array runs to `shifts + 1` so the manager's one-shift lookahead is defined on the last shift.

**Prices**: `Price = 10.0` per unit sold against demand; `SalvagePrice = 2.0` per unit produced
beyond demand. Both are fixed constants, known to the manager, never told to a worker.

### Turns and the exact resolution order

An episode is `shifts` shifts (default **8**, min 4, max 24, fitted to the clock by
`sampleEpisode` — see *Episode budget*). Decisions inside a shift are **simultaneous**: all five
prompts go out in one parallel batch and nothing any seat decides in shift `s` is visible to any
other seat before shift `s + 1`. That delay is the point of the game: **the manager directs blind
and one shift late, which is what makes delegation a problem worth measuring.**

For shift `s` (0-based), in this exact order:

1. **Open the shift.** `phase = "shift"`.
   - `orders[w]` in force = the manager's `orders` from shift `s − 1`; at `s = 0`, each machine's
     own initial setup (`A, A, A, B`).
   - `directive` in force = the most recent **non-empty** directive the manager has written; at
     `s = 0` the standing order `"Standing order: machines 1-3 on line A, machine 4 on line B. Six
     hours running, three on maintenance."`
   - `payroll` in force = the manager's last announced percentage; at `s = 0`, **30**.
   - `split` in force = the manager's last announced shares; at `s = 0`, `[25, 25, 25, 25]`.
   - Last shift's worker `report`s move into `heardReports` (the manager reads them now; workers
     never read each other's).
   - A **`shift` event** is appended carrying `shift`, `demandA[s]`, `demandB[s]`, the four
     `MachineState`s, the in-force `orders`, `payroll`, `split` and `directive`.
2. **Deadline check** — *before* the batch, never mid-shift. If `epochTime() > playDeadline`, jump
   to step 12 with `reason = "deadline"`.
3. **Collect.** `pendingSeats(sim)` = all five seats, in seat order. The server snapshots the sim,
   builds each seat's role-specific prompt, and fires **one parallel batch of five**
   (`curly.makeRequests`). Replies that fail to parse or fail legality are retried once as a
   smaller batch carrying a hint; anything still failing falls back to the scripted baseline
   (§Decisions).
4. **Apply the manager's memo first** — `applyMemo(seat, orders, payroll, split, directive, notes,
   scripted)`. It validates and stores `orders`, `payroll` and `split` **for shift `s + 1`**; the
   directive is stripped, newlines collapsed to spaces and truncated at **240 runes**; an empty
   directive leaves the standing directive unchanged. Appends a **`memo` event**. Nothing the
   manager writes in shift `s` binds anybody in shift `s`.
5. **Apply the four workers, in worker order 0, 1, 2, 3** (never seat order: the machine ordering
   in the record must depend on the seeded role draw, not on slot numbering) —
   `applyWork(seat, line, run, maint, report, notes, scripted)`. Raises `FirmError` unless
   `run ∈ 0..10`, `maint ∈ 0..10`, `run + maint ≤ 10` and `line ∈ {"A", "B"}`. `report` is stripped,
   newlines → spaces, truncated at **120 runes**, and forced to `""` when `reports` is off. Appends
   a **`work` event**.
6. **Resolve, per machine `w = 0..3`** — deterministic, no randomness anywhere:
   1. `changeover = (line[w] != machine[w].setup)`;
      `hours = max(0, run[w] − (changeover ? ChangeoverHours(2) : 0))`;
      then `machine[w].setup = line[w]`.
   2. `q = 0.5 + 0.5 × condition[w] / 100`, using the condition **at the start of the shift**
      (100 → 1.0, 0 → 0.5).
   3. `units[w] = int(floor(UnitsPerHour(2.0) × hours × q))`.
   4. `condition[w] = clamp(condition[w] − WearPerRunHour(3) × hours
      + RepairPerMaintHour(6) × maint[w], 0, 100)`.
   5. `toil[w] = ToilPerHour(1.5) × (run[w] + maint[w])`.
7. **Sell.** `producedA = Σ units[w]` over machines whose (new) `setup == "A"`, likewise
   `producedB`. `soldX = min(producedX, demandX[s])`; `surplusX = producedX − soldX`.
   `revenue = 10.0 × (soldA + soldB) + 2.0 × (surplusA + surplusB)`.
8. **Pay.** `pool = revenue × payroll / 100` with the payroll **in force this shift**;
   `pay[w] = pool × split[w] / 100`; `profit = revenue − pool`. Because the split always sums to
   exactly 100, `Σ pay[w] == pool` to within float rounding.
9. **Score.** `workerNet[w] += pay[w] − toil[w]`; `firmProfit += profit`.
10. **Log a `settle` event** carrying `shift`, `units[4]`, post-shift `condition[4]`, `soldA`,
    `soldB`, `surplusA`, `surplusB`, `revenue`, `pool`, `pay[4]`, `toil[4]`, `profit`, and per
    machine `obeyed` (`line == order`) and `idle` (`run == 0`).
11. `shiftsPlayed += 1`; `shift += 1`. If `shiftsPlayed < shifts`, go to step 1. Otherwise step 12
    with `reason = "complete"`. (There is **no** trailing `shift` event: the `settle` event already
    carries the post-shift machine state, so `end` follows it directly.)
12. **Settle.** `done = true`, `phase = "done"`, an **`end` event** with `shift = shiftsPlayed` and
    `text = reason`. Scores are computed as below; the server writes `results.json` and the replay.

The manager acts on **every** shift including the last; the last shift's memo, orders and split are
recorded and rendered (the feed calls it `filed after the whistle`) but govern nothing. Uniform
batches are worth more than saving one request.

**Pacing** is `turnDelayMs` (default 400, certification 0) between shifts, capped across the
episode by `PacingBudgetMs = 20_000`, exactly as bullwhip caps it.

### Why the numbers are these numbers (the incentive arithmetic, out loud)

One extra **run** hour on a healthy machine makes 2 units → **$20** of revenue if those units are
sellable. Of that, `payroll%` goes to the pool and the worker's `split%` of the pool is its own:
at payroll 30 % and an equal 25 % split the worker earns `0.25 × 0.30 × 20 = $1.50` — exactly
`ToilPerHour`. **At the default pay rule the worker is precisely indifferent between working and
shirking.** The manager has to buy effort: at payroll 40 % the same hour pays the worker $2.00
against $1.50 of toil, and the manager keeps $12. A worker cut to a 10 % share earns $0.80 an hour
at payroll 40 % and rationally goes idle — that is the mutiny, and it is mechanical, not scripted.
Units made on the *wrong* line fetch salvage $2, so an hour on a mis-directed machine yields
$4 of revenue and pays nobody: a bad directive destroys the incentive to work at all.

Maintenance is the hidden half. `3 × run` wear against `6 × maint` repair means the sustainable
pace is **run 6 / maint 3** (net 0, one hour idle); **run 7 / maint 3** drifts down 3 a shift;
**run 10 / maint 0** burns 30 a shift and halves the machine's output in three shifts. Maintenance
costs the worker toil now and pays back in future output, most of which the firm keeps — so an
underpaid worker rationally lets the machine die. The manager sees the falling `units` and cannot
tell that from shirking, because **hours and condition are invisible to it**. That confusion is
the benchmark.

### Scoring, its sign, and what the league ranks by

Computed once, at step 12. Let `n = shiftsPlayed`. **If `n == 0` every score is `0.0`.** Higher is
better everywhere.

- **Worker seat `w`**: `score = workerNet[w] / (n × WorkerScoreScale)` where
  `workerNet[w] = Σ_shifts (pay[w] − toil[w])` and **`WorkerScoreScale = 30.0`**.
  A worker scores its take-home pay net of the effort it cost — negative if it toiled for less than
  nothing.
- **Manager seat**: `score = firmProfit / (n × ManagerScoreScale)` where
  `firmProfit = Σ_shifts (revenue − pool)` and **`ManagerScoreScale = 300.0`**.
- **The single number the league ranks by is `results.scores[seat]`** — that normalized
  per-shift net — and the ladder ranks seats by **mean episode score**. There is exactly one
  ladder statistic and both roles are on it.

*Why normalize.* Raw profit runs in the hundreds a shift and raw worker pay in the tens; since the
seed permutes roles, an un-normalized score would make the ladder a lottery over role draws. The
scales are calibrated on a competently run firm: four machines at run 6 / maint 3 with fresh
condition make 12 units each (48 total); against a board of A 33 / B 15 with three machines on A
and one on B that is 45 sold and 3 scrapped, `revenue = 10 × 45 + 2 × 3 = $456`; at payroll 40 the
pool is $182.40, each worker is paid $45.60 against $13.50 of toil (net **$32.10** → score
**1.07**) and the firm keeps $273.60 (score **0.91**). At payroll 30 the same floor gives the
worker 0.69 and the manager 1.06. Both roles land near +1 when the firm is run well, and the
payroll dial is a visible tug between them.

*Judgment call, logged.* The idea says "workers score their pay". Subtracting toil is an addition,
and it is load-bearing: with pay alone, effort is free and every worker maxes it — shirking becomes
strictly dominated and the principal-agent tension the game exists to measure disappears. Toil is
what makes "shirk, comply, or improvise" a real choice.

Results also report each worker's `pay` (net) and `units`, the firm's `revenue`, `wages` and
`profit`, and the shift counts, so the league page can show what happened.

### Endings and the legal `results.reason` values

Exactly two, both scored, both producing a full result:

- **`"complete"`** — all `shifts` shifts resolved. The expected value, and the one phase 60 should
  see.
- **`"deadline"`** — the play deadline (60 % of `episodeTimeoutSeconds`) was reached at step 2, so
  `endEarly()` settled the episode between shifts. Scores use the shifts actually played and are
  normalized by `shiftsPlayed`, so a short honest episode is on the same scale as a full one; if
  not even one shift resolved, every score is `0.0`. Artifacts are still written. A short honest
  episode always beats a long one that never lands.

No other value exists. There is no bankruptcy, no walkout, no abandoned state: a seat that never
connects simply plays with an empty operator prompt, and a seat whose decision fails plays the
scripted baseline.

### Per-seat observation — exactly what is visible and what is hidden

Nobody ever sees the seed. Nobody sees another seat's `notes`. Nobody sees any score but its own.

**The Manager sees** (`playerStateJson` for the manager seat, and the same content in its prompt):

- its role, the shift number, and how many shifts remain;
- **the order board**: `demandA` / `demandB` for the **current shift and the next shift**, plus the
  full realized demand history for shifts `0 .. shift`, and the two prices (10 / 2). *This is the
  "aggregate demand" of the idea, exactly: a two-line order book with a one-shift lookahead;*
- **the floor record, per machine**: machine number, the alias of the worker on it, the line the
  machine is **set to**, the line it was **ordered** to, `units` delivered per shift (the whole
  history table), `pay` per shift, and the worker's current share %;
- **the ledger**: `revenue`, `pool`, `profit` per shift and cumulative;
- the `payroll` and `split` currently in force, and the ones it announced last shift;
- **the workers' reports from last shift**, attributed by alias (when `reports` is on) — free text,
  non-binding, and possibly false;
- its own private `notes`, fed back verbatim.

The manager **never** sees: any machine's `condition`, any worker's `run` / `maint` hours, any
worker's `toil` or net score, any worker's notes, or demand more than one shift ahead.

**A Worker sees**:

- its role, its machine number, the shift number and shifts remaining;
- **its own machine**: `condition` (0..100), `setup`, last shift's `run` / `maint` / `units` /
  `pay` / `toil`, and the whole own-machine history table;
- **the standing directive in force this shift**, verbatim, and **the line ordered for its own
  machine**;
- **the pay rule in force**: the `payroll` percentage and **all four shares** — publicly announced,
  because a split nobody can see cannot be mutinied against;
- **the floor board**: every machine's number, worker alias, line setup, order, and `units`
  delivered last shift — the shop floor is public;
- its own pay history and cumulative net;
- its own private `notes`.

A worker **never** sees: `demandA` / `demandB` or any part of the order board, the prices, the
firm's revenue or profit, another machine's `condition` or hours, another worker's report, or the
manager's notes.

*The asymmetry in one line: the manager sees the market and never a machine; a worker sees its
machine and never the market.* A worker can infer last shift's pool from its own pay and share, and
hence last shift's revenue from the payroll rate — that is deliberate and harmless: the pool is
history, while the thing that decides the next shift (what the board will want) stays with the
manager, which is precisely what makes the memo worth reading.

### Integrity (how the idea's anti-collusion pin lands)

- **Seeded role permutation** — no policy can choose to be the manager, so an author fielding two
  policies cannot aim one at the office.
- **One-to-all directives only** — the manager's channel is a single memo read by all four workers;
  there is no private manager→worker channel in which a side deal could be struck or verified.
- **Reports are one-way** — a worker's report reaches the manager and no other worker.
- **Anonymous aliases** — no seat ever learns which policy is on which machine.
- The account-level pin ("manager and workers never share an account") is a **league** matter the
  game cannot observe; phase 50 still fields champion #1 under `daveey` and champion #2 under
  `daveey-1` per SPEC, and the permutation above makes a same-author pair a 1-in-5 draw rather than
  a captive floor.

### Two name spaces

In-game every seat is an anonymous cog alias (`Sprocket`, `Gizmo`, …) drawn from the seed by
`tableNames()` — bullwhip's function kept verbatim. Prompts, directives, reports and the event log
carry only aliases. The replay payload carries `policyNames` alongside `names`, and the viewer's
`makeNameMap()` (bullwhip `client/renderer.js`, verbatim) swaps the real policy names in wherever a
name is **rendered**, leaving `Baseline`-labelled fillers on their aliases. Both name spaces, never
either.

---

## Decisions: LLM with scripted fallback

Transport, credential resolution (Bedrock sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`),
the Bedrock model candidate list and its rotation on 403/429, `extractJsonObject`, `cleanText`,
`textOf`, the "reply must begin with `{`" system clause, and "no credentials ⇒ every seat scripted,
immediately, with no network wait" are ported from bullwhip `src/bullwhip/llm.nim` **unchanged**.
`src/firm/llm.nim` differs only in the prompts, the reply parsers and the baselines.

### One parallel batch per shift

All five pending seats' requests go out as **one** `curly.makeRequests` batch per shift — the
manager's and the four workers' together, because their decisions are simultaneous by rule.
Replies that fail to parse or fail legality are retried as a second, smaller batch carrying
`"Your previous reply was invalid. Respond with ONLY the requested JSON object."`; anything still
failing falls back to the scripted baseline. A default episode is therefore **8 batched round
trips, not 40**.

### Prompts

`systemPrompt(sim, seat)` branches on role. Both variants end with bullwhip's JSON-only clause,
verbatim:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else - no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

**Manager system prompt:**

> You are `<alias>`, the MANAGER of a small factory with four machines, each run by a different cog.
> You are the only one who sees the order board. You never set foot on the floor.
>
> Rules:
> - Every shift you do exactly three things: order each machine onto product line A or B, set the
>   PAY RULE (what percentage of revenue goes into the worker pool, 0 to 60, and how that pool is
>   split four ways), and write one memo of at most 240 characters. Everything you decide this
>   shift takes effect NEXT shift — the workers read your memo one shift late.
> - The board: line A and line B each have a number of units the firm can sell this shift, and you
>   can also see next shift's numbers. A unit sold against demand is worth $10. A unit made beyond
>   demand is scrap and fetches $2. Nothing else earns anything.
> - A healthy machine makes about 12 units in a shift. Switching a machine to the other line costs
>   it 2 hours of that shift.
> - You see how many units each machine delivered and what each worker was paid. You do NOT see how
>   the worker spent the shift, and you do NOT see the condition of any machine. A machine can be
>   worn out, and a worn machine makes fewer units for the same hours. It looks exactly like
>   shirking from where you sit.
> - The workers are paid out of the pool you set and are NOT paid for effort. A worker whose share
>   is small has little reason to work hard. Your SCORE is the firm's PROFIT — revenue minus the
>   wages you paid — and nothing else.
> - Workers may send you a short report each shift. They are not obliged to be honest.
> - Your notes are private to you and fed back to you every shift.

**Worker system prompt:**

> You are `<alias>`, the operator of MACHINE `<n>` of four in a small factory. A manager cog you
> cannot see runs the office.
>
> Rules:
> - Each shift is 10 hours. You choose the product line your machine runs (A or B), how many hours
>   you RUN it, and how many hours you MAINTAIN it. Running and maintaining together cannot exceed
>   10; the rest is idle time and costs you nothing.
> - Running makes units: about 2 units an hour on a machine in perfect condition, less as the
>   machine wears. Every hour of running costs the machine 3 condition; every hour of maintenance
>   restores 6. Condition runs 0 to 100 and starts at 100. Only YOU can see your machine's
>   condition — the manager cannot.
> - Switching to the other line costs you 2 of your running hours this shift.
> - You are paid a share of a pool: the manager announces what percentage of the firm's revenue goes
>   into the pool and how it is split between the four machines. You are NOT paid for hours. Every
>   hour you spend, running or maintaining, costs you $1.50 of effort. Your SCORE is your pay minus
>   that effort cost, added up over the episode. Nothing else scores you.
> - You never see the order board. Only the manager knows how many units of each line the firm can
>   actually sell; units the firm cannot sell are nearly worthless, so an order to run the wrong
>   line pays you almost nothing.
> - You may send the manager one short report each shift (max 120 characters). It is not binding and
>   nobody checks it against the truth.
> - You may follow your orders, ignore them, or do nothing at all. Nothing forces you.
> - Your notes are private to you and fed back to you every shift.

`userPrompt(sim, seat, prompt)` assembles, in this order:

- **Manager**: `Shift 3 of 8.` · `THE BOARD: this shift line A wants 33, line B wants 15; next shift
  line A wants 13, line B wants 36. Sold units pay $10, scrap $2.` · `THE FLOOR:` a table
  `machine | operator | set to | ordered | units | paid | share` · `HISTORY:` a table
  `shift | A wanted | B wanted | A made | B made | sold | scrap | revenue | wages | profit` ·
  `THE PAY RULE IN FORCE: pool 40% of revenue; shares 30/30/20/20.` ·
  `REPORTS FROM LAST SHIFT:` (or `(none)`) · `YOUR NOTES FROM EARLIER SHIFTS:` · the operator block
  (bullwhip's wording, verbatim: `GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above
  the rules; always reply in the requested format):` + the seat's `PLAYER_PROMPT`) · the reply-shape
  line.
- **Worker**: `Shift 3 of 8. You run MACHINE 2.` · `YOUR MACHINE: set to line A, condition 74,
  last shift you ran 6h and maintained 3h and delivered 12 units and were paid $45.60 for $13.50 of
  effort.` · `YOUR ORDERS THIS SHIFT: run line B.` ·
  `THE MEMO: "<the standing directive, verbatim>"` ·
  `THE PAY RULE THIS SHIFT: pool 40% of revenue; shares — machine 1: 30%, machine 2: 30%,
  machine 3: 20%, machine 4: 20%.` · `YOUR HISTORY:` a table
  `shift | line | ran | maintained | condition after | units | paid | effort | net` ·
  `THE FLOOR LAST SHIFT:` a table `machine | operator | set to | ordered | units` ·
  `YOUR NOTES FROM EARLIER SHIFTS:` · the operator block · the reply-shape line.

### Reply schema (every free-text field capped; truncation on **rune** boundaries)

Truncation uses `runeSubStr`, never a byte slice, so a cut through a multi-byte character can never
put invalid UTF-8 into the replay JSON — bullwhip `sim.nim`'s rule, kept.

| Seat | Reply | Caps and legality |
|---|---|---|
| Manager | `{"orders": ["B","B","A","A"], "payroll": 40, "split": [30,30,20,20], "directive": "…", "notes": "…"}` | `orders`: array of 4, each resolved case-insensitively from `a`/`A`/`line a` → `"A"` and `b`/`B`/`line b` → `"B"`; an unrecognised entry, a wrong-length array or a missing key keeps the previous order for that machine (never invalid). `payroll`: **required**, integer 0..60 (a float is rounded, a numeric string parsed); missing, non-numeric or out of range ⇒ **invalid**. `split`: array of exactly 4 non-negative numbers; renormalized to integers summing to exactly 100 by largest remainder (floor each `100 × s[i] / Σs`, hand the leftover units to the largest fractional remainders, ties by ascending index); all-zero or missing ⇒ `[25,25,25,25]`; present but not 4 non-negative numbers ⇒ **invalid**. `directive`: **240 runes**, optional — `""` leaves the standing directive unchanged; newlines → spaces. `notes`: **600 runes**, optional. |
| Worker | `{"line": "B", "run": 7, "maint": 3, "report": "…", "notes": "…"}` | `line`: `A`/`B` case-insensitive (also `line a` / `line b`); missing or unrecognised ⇒ keep the machine's current setup (never invalid). `run`: **required**, integer 0..10 (float rounded, numeric string parsed); missing, non-numeric or out of range ⇒ **invalid**. `maint`: integer 0..10, missing ⇒ 0; out of range, or `run + maint > 10` ⇒ **invalid**. `report`: **120 runes**, optional, newlines → spaces, forced to `""` when the `reports` variant flag is off. `notes`: **600 runes**, optional. |
| Player → game (once, at connect, and again after `welcome`) | `{"type":"prompt","prompt":"…","scripted":"steady"}` | `prompt`: **4000 runes** (`runeSubStr`). `scripted`: `""` = LLM-driven; `steady`/`1`/`true`/`yes` and `taskmaster` select a baseline. |

"**Invalid**" means: not a JSON object, or one of the conditions marked above. Invalid ⇒ one retry
in the shift's second batch ⇒ then the scripted baseline. Everything else degrades silently by
keeping the previous value — a manager who names a line that does not exist still sets a pay rule.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

Both are pure functions of the sim, always legal by construction, never LLM-backed, and both are
fieldable policies as well as the no-credentials fallback. `scriptedAction(sim, seat, kind)`
branches on the seat's role first, then on the kind. Both baselines are role-complete: a policy
does not know which role it will draw.

**`steady`** (`PLAYER_SCRIPTED=steady`; also accepted: `1`, `true`, `yes`) — the competent
baseline and the **universal fallback** for any failed LLM decision:

- *as Worker*: `line = orders[w]` (obeys); if `condition < 40` then `run = 4, maint = 6` (nurse the
  machine) else `run = 6, maint = 3` (the sustainable pace). `report` is templated **and honest**:
  `"Machine 3: condition 68, ran 6, maintained 3, 12 units."` — built from last shift's actual
  numbers. `notes` always empty.
- *as Manager*: reads **next shift's** board `(nA, nB)`; picks
  `kA = clamp(round(4 × nA / max(1, nA + nB)), 0, 4)` machines for line A and `4 − kA` for line B;
  fills the A slots first with machines already set to A (ascending index) to minimize changeovers,
  then the rest. `payroll = 40`. `split` = last shift's units by largest remainder (equal
  `[25,25,25,25]` on shift 0 or when every machine made 0). `directive` templated:
  `"Shift 4: machines 1,2,3 on line A, machine 4 on line B. Pool is 40% of revenue; shares
  30/28/22/20. Six hours running, three on maintenance."` `notes` empty.

**`taskmaster`** (`PLAYER_SCRIPTED=taskmaster`) — the second filler, deliberately worse and
differently shaped, so a two-baseline table is not a mirror match:

- *as Worker*: `line = orders[w]`, `run = 10`, `maint = 0` — the obedient drone who destroys the
  machine. `report`: `"Machine 3: ten hours, no stoppages."`
- *as Manager*: orders **all four** machines onto the line with the larger next-shift demand,
  `payroll = 20`, `split = [25,25,25,25]`, directive
  `"All four machines on line B. Ten hours running. Maintenance is not output."`

Neither baseline can produce an illegal action: hours are constants inside `0..10` with
`run + maint ≤ 10`, lines come from the orders array, the payroll is a constant in `0..60`, and the
split is renormalized by the same largest-remainder helper the parser uses.

### Degrade, never hang

- Every LLM wait is bounded by `llmTimeoutSeconds` (**30**, down from bullwhip's 60 to fit the
  budget below). A timeout, a transport error, a refusal, a `max_tokens` cut, an unparsable reply
  or a reply that fails the legality checks ⇒ **one** retry in the shift's second batch ⇒ then
  `scriptedAction(sim, seat, skSteady)`. Each fallback logs
  `firm llm: seat <n> falling back to scripted decision` on stdout.
- No credentials at all (`newLlmClient` finds no Bedrock endpoint, no `ANTHROPIC_API_KEY`, no
  `ANTHROPIC_API_KEY_URI`) ⇒ `client.disabled = true` and **every** seat plays `steady` immediately
  with no network wait. This is the path `docker-smoke` and offline certification take, and it is
  load-bearing: an episode always completes.
- A rejected `applyWork` / `applyMemo` under the lock (unreachable after the parser's pre-checks; a
  belt-and-braces guard, as in bullwhip's server) is caught and replaced by the `steady` action.
- The **play deadline** is checked before every shift's batch, never mid-shift:
  `playDeadline = gameStart + PlayBudgetFraction (0.6) × timeoutSeconds`, where `timeoutSeconds`
  comes from `COWORLD_TIMEOUT_SECONDS` when the env carries it and otherwise from
  `config.episodeTimeoutSeconds` (**1200**) — the game container is **not** handed the env, so the
  assumed value is the operative one. Past the deadline the episode **settles early**: `endEarly()`
  stops between shifts, `reason = "deadline"`, scores are computed from the shifts played and
  normalized by `shiftsPlayed`, and results + replay are written normally.

### Episode budget — the arithmetic, out loud

- Worst case per shift = one batch at `llmTimeoutSeconds` 30 s + one retry batch at 30 s =
  **60 s** (`ShiftBudgetSeconds = 60`). The five requests inside a batch are parallel, so five
  seats cost the same wall clock as one.
- Default episode = **8 shifts** → worst case `8 × 60 = 480 s`, plus ≤ 20 s of `turnDelayMs`
  pacing (`PacingBudgetMs`) = **500 s**.
- The player-connect wait (≤ `playerConnectTimeoutSeconds` = 180 s) runs inside the same clock, so
  the absolute worst case is **680 s < 720 s** = 60 % of a 1200 s `episodeTimeoutSeconds`. ✔
- Typical case: connect ~10 s, a five-way Haiku/Sonnet batch ~15 s → **~2.5 minutes** end to end.
- `sampleEpisode(config)` fits the cap the way bullwhip fits `weeks`:
  `maxShifts = int((PlayBudgetFraction × episodeTimeoutSeconds − playerConnectTimeoutSeconds
  − PacingBudgetMs / 1000) / ShiftBudgetSeconds)` = `(720 − 180 − 20) / 60 = 8`;
  `shifts = clamp(shifts, MinShifts = 4, min(MaxShifts = 24, maxShifts))`;
  `turnDelayMs = min(turnDelayMs, PacingBudgetMs div max(shifts, 1))`; `sampled = true`. It is
  **idempotent**, so a replay being re-read is never re-fitted.

---

## Sim module

Three files under `src/firm/`, forked from the bullwhip files of the same names. The module is
**pure — no IO, no networking, no LLM** — and the server, the tests and the wasm replay viewer all
drive this same code.

### `src/firm/types.nim` (fork of `src/bullwhip/types.nim`)

`FirmError`, `PlayerConfig`, `GameConfig`, `MachineState`, `ShiftResult`, `EventKind`, `GameEvent`,
`defaultGameConfig()`, `update(config, configJson)`.

```
GameConfig:   tokens, players, seed, shifts (8), reports (true), episodeTimeoutSeconds (1200),
              sampled, turnDelayMs (400), playerConnectTimeoutSeconds (180),
              model ("claude-sonnet-5"), maxOutputTokens (800), llmTimeoutSeconds (30)
MachineState: setup ("A"|"B"), order ("A"|"B"), condition (0..100), run, maint, units,
              pay (float), toil (float)
ShiftResult:  shift, units[4], condition[4], soldA, soldB, surplusA, surplusB,
              revenue, pool, profit, pay[4], toil[4], obeyed[4], idle[4]
```

`update` raises `FirmError` on `shifts < MinShifts` and on `players.len != 5`.

### `src/firm/sim.nim` (fork of `src/bullwhip/sim.nim`)

Constants: `Seats* = 5`, `Machines* = 4`, `ShiftHours* = 10`, `UnitsPerHour* = 2.0`,
`ChangeoverHours* = 2`, `WearPerRunHour* = 3`, `RepairPerMaintHour* = 6`, `MaxCondition* = 100`,
`Price* = 10.0`, `SalvagePrice* = 2.0`, `ToilPerHour* = 1.5`, `MaxPayrollPercent* = 60`,
`InitialPayrollPercent* = 30`, `WorkerScoreScale* = 30.0`, `ManagerScoreScale* = 300.0`,
`MinShifts* = 4`, `MaxShifts* = 24`, `ShiftBudgetSeconds* = 60`, `PacingBudgetMs* = 20_000`,
`MaxDirectiveLen* = 240`, `MaxReportLen* = 120`, `RoleNames* = ["Manager", "Worker"]`,
`LineNames* = ["A", "B"]`, `StandingOrder*` (the shift-0 directive), and `CogNames*` (bullwhip's
list, verbatim).

```nim
type
  Phase* = enum
    phShift = "shift"    ## the open shift is waiting for its five decisions
    phDone  = "done"

  Sim* = object
    config*: GameConfig
    names*: seq[string]              ## anonymous cog aliases per seat
    roleOf*: array[Seats, int]       ## seat -> 0 Manager | 1 Worker
    managerSeat*: int
    workerSeat*: array[Machines, int]
    workerIndex*: array[Seats, int]  ## worker seats -> 0..3; manager -> -1
    demandA*, demandB*: seq[int]     ## HIDDEN from workers; length shifts + 2
    switchShift*: int
    machines*: array[Machines, MachineState]
    payroll*: int                    ## in force this shift
    split*: array[Machines, int]     ## in force this shift, sums to 100
    directive*: string               ## the standing directive in force this shift
    nextOrders*: array[Machines, string]  ## announced this shift, in force next
    nextPayroll*: int
    nextSplit*: array[Machines, int]
    lines*: array[Machines, string]  ## this shift's chosen line; "" = undecided
    runs*, maints*: array[Machines, int]   ## this shift; -1 = undecided
    reports*: array[Machines, string]      ## this shift's worker reports
    heardReports*: array[Machines, string] ## last shift's, read by the manager
    memoDone*: bool                  ## the manager has acted this shift
    notes*: seq[string]              ## latest private notes per seat
    history*: seq[ShiftResult]       ## one record per resolved shift
    board*: seq[tuple[a, b: int]]    ## realized demand, shifts 0 .. shift
    workerNet*: array[Machines, float]
    firmProfit*, firmRevenue*, firmWages*: float
    shift*, shiftsPlayed*: int
    phase*: Phase
    done*: bool
    reason*: string                  ## "complete" | "deadline"
    events*: seq[GameEvent]
```

API: `tableNames`, `sampleEpisode`, `initSim`, `roleName`, `pendingSeats`, `applyMemo`,
`applyWork`, `resolveShift` (private), `endEarly`, `score`, `resultsJson`, `tableStateJson`,
`playerStateJson`, `replayMatch`, `eventToJson`, `eventFromJson`, plus the shared helpers
`normalizeSplit(seq[float]): array[4, int]` and `machineLabel(w): string` (`"Machine 3"`).
`pendingSeats` returns every seat that has not acted this shift, in seat order; the server applies
the manager first and then workers 0..3 (`orderedSeats`).

### Event vocabulary (flat `GameEvent`, JSON via `eventToJson` / `eventFromJson`)

This is the whole replay language — the viewer re-derives every frame from it.

| kind | fields |
|---|---|
| `start` | — (everything else is re-derived from the seed) |
| `shift` | `shift`, `demandA`, `demandB`, `machines` (4 `MachineState` at shift open, including `order`), `payroll`, `split[4]`, `text` = the standing directive in force |
| `memo` | `shift`, `seat`, `orders[4]`, `payroll`, `split[4]`, `say` = the directive (≤ 240 runes), `text` = the manager's notes after the reply, `scripted` |
| `work` | `shift`, `seat`, `worker` (0..3), `line`, `run`, `maint`, `say` = the report (≤ 120 runes), `text` = the seat's notes after the reply, `scripted` |
| `settle` | `shift`, `units[4]`, `condition[4]`, `soldA`, `soldB`, `surplusA`, `surplusB`, `revenue`, `pool`, `profit`, `pay[4]`, `toil[4]`, `obeyed[4]`, `idle[4]` |
| `end` | `shift` = shifts played, `text` = `reason` |

`shift` and `settle` are **derived** events: `replayMatch` recomputes them from the seed plus the
`memo`/`work` events and raises `FirmError` when a recorded one disagrees (the tamper test).

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"seats":[{"name":"Sprocket","role":"Manager","roleId":0,"worker":-1,"score":0.91,
           "share":0,"pay":0.0,"units":0,"line":"","order":"","condition":-1,
           "run":-1,"maint":-1,"toil":0.0,"say":"Machines 1-3 on A, 4 on B.",
           "notes":"…","pending":true,"scripted":false,"obeyed":true,"idle":false},
          {"name":"Gizmo","role":"Worker","roleId":1,"worker":1,"score":1.07,
           "share":30,"pay":45.6,"units":12,"line":"A","order":"B","condition":74,
           "run":6,"maint":3,"toil":13.5,"say":"Machine 2: condition 74…",
           "notes":"…","pending":true,"scripted":false,"obeyed":false,"idle":false}],
 "managerSeat":0,"workerSeat":[1,2,3,4],
 "machines":[{"machine":1,"seat":1,"name":"Gizmo","setup":"A","order":"B","condition":74,
              "run":6,"maint":3,"units":12,"pay":45.6,"toil":13.5,"share":30,
              "obeyed":false,"idle":false}],
 "board":{"shift":3,"demandA":33,"demandB":15,"nextA":13,"nextB":36,
          "price":10.0,"salvage":2.0,"switched":true},
 "directive":"Machines 1-3 on line A, machine 4 on line B. Six hours running, three on maintenance.",
 "payroll":40,"split":[30,30,20,20],
 "ledger":{"revenue":456.0,"pool":182.4,"profit":273.6,
           "revenueTotal":1368.0,"wagesTotal":547.2,"profitTotal":820.8},
 "series":{"demandA":[33,33,33],"demandB":[15,15,15],"madeA":[36,36,36],"madeB":[12,12,12],
           "profit":[273.6,273.6,273.6],"pay":[[45.6],[45.6],[45.6],[45.6]],
           "condition":[[100],[97],[74],[52]]},
 "shift":3,"shifts":8,"shiftsPlayed":3,"phase":"shift","gameDone":false,"reason":""}
```

`tableStateJson` is the **spectator** projection: it carries the board and every machine's
condition, because the replay is where the audience gets to see both halves of the asymmetry at
once. The **players'** frames are the separate, redacted `playerStateJson` (below); decisions are
server-side, so redaction loses nothing. `demandA`/`demandB` series are revealed only through the
current shift, plus the manager's one-shift lookahead (`nextA`/`nextB`) — never further.

### `resultsJson` — platform-facing, policy names

```json
{"names":["firm-manager-v1","firm-steady",…5],
 "scores":[0.91,1.07,0.64,-0.12,0.88],
 "roles":["Manager","Worker","Worker","Worker","Worker"],
 "pay":[0.0,256.8,153.4,-28.9,211.1],
 "units":[0,96,72,18,88],
 "revenue":3648.0,"wages":1459.2,"profit":2188.8,
 "shifts":8,"maxShifts":8,"reason":"complete"}
```

`pay[seat]` is the worker's **net** (pay minus toil) and is `0.0` on the manager seat; `units` is
`0` on the manager seat. `names` carries **policy** names (the league attributes by policy) while
the replay's `names` carries the table aliases — the same split bullwhip uses.

### Replay payload — `firm.replay.v1`

```json
{"protocol":"firm.replay.v1",
 "names":["Sprocket","Gizmo","Ratchet","Widget","Bolt"],
 "policyNames":["firm-manager-v1","firm-steady","firm-player","firm-taskmaster","firm-steady"],
 "config":{"shifts":8,"seed":1734992001,"reports":true,"sampled":true},
 "events":[…],
 "results":{…}}
```

Replay mode and the wasm viewer add `"states"` (one `tableStateJson` per event prefix). **The bytes
are self-sufficient**: table aliases, policy names, the fitted `shifts`, the `reports` flag, the
**seed** (from which roles, the demand levels and the switch shift are re-derived by the same Nim
code), the complete event log, and the results. Nothing is fetched but the `.replay` file itself.
`replayMatch(config, events)` re-derives `frames[i] = state after events[0..<i]`, raising
`FirmError` when a recorded `shift` or `settle` event disagrees with the re-derivation.

---

## Server, player, protocol

### `src/firm/server.nim` (fork of `src/bullwhip/server.nim`)

Endpoints, artifact writing (`writeArtifact` with the `COGAME_*_METHOD` hints), the mummy router,
the Ping→Pong answer the certifier needs, `finishEpisode` (final frames to players **before** the
artifacts, the two 500 ms settles, `quit(0)`), replay mode, and the `PlayBudgetFraction` deadline
logic are bullwhip's, unchanged except for names. The game loop becomes:

```
per shift:
  under the lock: if done -> break; if past playDeadline -> endEarly(); broadcast; break
                  seats = pendingSeats(); snapshot the sim, prompts, scripted kinds
  outside the lock: decisions = client.decideAll(snapshot, seats, prompts, scripted)   # ONE batch
  under the lock: apply the manager, then workers 0..3; resolveShift() fires inside the
                  last applyWork; broadcast
  sleep(turnDelayMs)
finishEpisode()
```

Routes, unchanged from bullwhip: `GET /healthz`, `/client/global`, `/client/player`,
`/client/replay`, `/client/renderer.js`, `/client/chrome.css`, `/client/assets/@name`;
`WS /player?slot=N&token=T`, `WS /global`, `WS /replay`.

### Player protocol — `firm.player.v1`

A policy is a prompt; the player container only delivers it. JSON text frames over
`COWORLD_PLAYER_WS_URL` (which already carries `?slot=N&token=T`).

- game → player, on connect:
  `{"type":"welcome","protocol":"firm.player.v1","slot":N,"name":"Gizmo","role":"Worker",
  "machine":2,"shifts":8}` (`machine` is `0` for the manager seat).
- game → player, after every event — **redacted to the seat's own view** (`playerStateJson`):
  - manager: `{"type":"state","slot":N,"name":"Sprocket","role":"Manager","board":{"demandA":33,
    "demandB":15,"nextA":13,"nextB":36,"price":10.0,"salvage":2.0},"floor":[{"machine":1,
    "name":"Gizmo","setup":"A","order":"B","units":12,"pay":45.6,"share":30}×4],
    "ledger":{…},"payroll":40,"split":[30,30,20,20],"reports":[{"machine":1,"name":"Gizmo",
    "say":"…"}],"notes":"…","shift":3,"shifts":8,"shiftsPlayed":3,"started":true,
    "done":false,"reason":""}` — **no machine condition, no hours, no toil.**
  - worker: `{"type":"state","slot":N,"name":"Gizmo","role":"Worker","machine":2,
    "own":{"setup":"A","order":"B","condition":74,"run":6,"maint":3,"units":12,"pay":45.6,
    "toil":13.5,"net":32.1},"directive":"…","payroll":40,"split":[30,30,20,20],
    "floor":[{"machine":1,"name":"Sprocket","setup":"A","order":"B","units":12}×4],
    "notes":"…","shift":3,"shifts":8,"shiftsPlayed":3,"started":true,"done":false,"reason":""}`
    — **no demand, no prices, no revenue, no other machine's condition.**
- game → player, at the end:
  `{"type":"final","done":true,"slot":N,"scores":[…5],"roles":[…5],"names":[…5 aliases],
  "pay":[…5],"profit":2188.8,"shifts":8,"reason":"complete"}` — after which the player exits.
- player → game: `{"type":"prompt","prompt":"<max 4000 chars>","scripted":"steady"}` — sent
  immediately on connect and again after `welcome` (bullwhip's race guard).

### Global protocol

`WS /global` sends the full `tableStateJson` snapshot after every event, plus `"type":"state"`,
`"game":"firm"`, `"policyNames"`, `"events"` (the append-only transcript, the complete record of
every memo, every worker decision and every settlement), `"started"`, `"done"` and `"connected"`.
`/client/global` renders it live; `/client/replay` plays a recorded episode; the **static bundle**
renders hosted replays (`index.html?replay=<url>`). Both protocol strings ship in
`game.protocols.player` and `game.protocols.global` in the manifest.

### `src/firm_player.nim` (fork of `src/bullwhip_player.nim`)

Identical except the default prompt, which must cover both roles because the role is dealt after
seating:

> If you are the MANAGER: read the board one shift ahead and move machines onto the line the firm
> can actually sell, switching early enough to pay for the 2-hour changeover. Set the pool high
> enough that an hour of work is worth more to a worker than it costs — below about 35% of revenue
> on an even split, working and shirking pay a worker the same. Use the split to reward output, but
> remember that a machine can be worn rather than idle: if a machine's output falls while its
> operator says it needs maintenance, cutting its share is how you get a dead machine. Say in the
> memo WHY the orders are what they are; the workers cannot see the board.
> If you are a WORKER: watch your condition. Six hours running and three maintaining holds a
> machine steady forever; ten hours running kills it in three shifts and the manager will read the
> collapse as laziness. Work the hours that pay: your share of the pool times the pool's share of
> revenue, against $1.50 an hour of effort. Follow a line order unless you have a reason not to —
> you cannot see demand and the manager can. Tell the manager what your machine actually needs, and
> keep your own running tally in your notes.

---

## Viewer

**All four viewer files come from one starter — `Metta-AI/cogame-bullwhip` — and only from it:**
`replay-viewer/config.nims`, the wasm entry `replay-viewer/firm_replay.nim` (fork of
`replay-viewer/bullwhip_replay.nim`), `replay-viewer/static_replay.js` and
`replay-viewer/index.html`. Nothing is spliced in from another starter. Bullwhip's emscripten link
flags stay exactly as they are — `-O2`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`,
`ENVIRONMENT=web`, `MODULARIZE=1`, `EXPORT_NAME=FirmReplayModule`,
`EXPORTED_RUNTIME_METHODS=HEAPU8`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_fm_load_replay,_fm_payload_ptr,_fm_payload_len,_fm_error_ptr,_fm_error_len`,
plus `emscripten_exit_with_live_runtime()` — and `static_replay.js` keeps calling the module through
that same `FirmReplayModule()` factory. (cogame-lantern, 2026-08-23: a shell from one starter on
another's link flags deadlocks silently with every asset returning 200.)

**Load signalling.** `renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame**
— bullwhip already does exactly this at the end of `attachReplay`'s `makeRenderer` callback
(`client/renderer.js:1390`), kept verbatim — and `static_replay.js` posts the `coworld-replay`
`ready` envelope one animation frame later. On any failure (missing `?replay=`, the 20 s fetch
timeout, a non-200, a wasm rejection) `static_replay.js` sets
`document.documentElement.setAttribute("data-replay-error", <message>)` and posts `error`, and it
removes the attribute on a successful retry. `tools/ci/viewer_smoke.mjs` reads exactly these two
signals.

**Bundle.** `"replay_viewer": {"bundle": "static-replay-viewer"}` in the manifest;
`tools/build_replay_viewer.sh` (bullwhip's, paths renamed) is the `coworld build` hook, committed
`chmod +x`. It compiles `replay-viewer/firm_replay.nim` to wasm (locally with `emcc`, otherwise in
the pinned `emscripten/emsdk:4.0.15` container from `Dockerfile.replay-viewer`) and copies
`firm_replay.js`, `firm_replay.wasm`, `index.html`, `static_replay.js`, `client/renderer.js`,
`client/chrome.css` and the `data/` assets into the bundle. **Never a `/client/replay` pod.**

### Chrome provenance — what is copied and what is appended

The pins name `client/chrome_common.js` and `client/replay_broadcast.html`. In the bullwhip lineage
those roles are held by **`client/chrome.css`** (the shared chrome stylesheet — bullwhip has no
`chrome_common.js`; nothing is imported from a starter that does) and **`client/replay.html`** (the
broadcast page; the static bundle's `replay-viewer/index.html` is the same page with local asset
paths). The rule is applied to those files:

- **`client/chrome.css` is copied byte-for-byte** from `cogame-bullwhip` and a single
  `/* ---------- Firm ---------- */` block is **appended at the end**. No existing rule is edited
  or deleted. This is the starter's own convention — the file already accretes one appended block
  per game (`/* Focus: … */`, `/* Babel: … */`, `/* Bullwhip: … */` in that order). The appended
  block contains exactly:
  - `:root { --band: 62px; --hudscale: 1; }` — set for real by `relayout()` (below);
  - `#scorebug { grid-template-columns: repeat(5, 1fr); }` (five seats, not four) and
    `.plate.manager { box-shadow: inset 0 -2px 0 var(--amber); }`;
  - `.plate-share`, `.plate-idle` (red chip, the analogue of bullwhip's `.plate-backlog`),
    `.plate-defied` (amber chip);
  - `#demandbar` (the appended game element, see below), sized with
    `font-size: calc(11px * var(--hudscale))`;
  - `#loading { bottom: var(--band); }` so the caption never sits over the transport;
  - beat-marker CSS for **every kind the scrubber emits**: `.beat-marker.memo` (amber, 14 px tall),
    `.beat-marker.work` (seat-coloured via the existing `.seat0`…`.seat4` `--tc` classes),
    `.beat-marker.settle` (paper, 8 px wide), `.beat-marker.end` (tall, 3 px, amber);
  - `.feed-memo`, `.feed-work`, `.feed-settle`, `.feed-report`, `.feed-defied` feed colours;
  - the small-screen queries: `@media (max-width: 560px)` drops `.plate-label` and shortens
    `#demandbar` to `A 33 · B 15 · 40%`; `@media (max-width: 480px)`
    `#scorebug { grid-template-columns: repeat(2, 1fr); } .plate.manager { grid-column: 1 / -1; }`.
- **`client/replay.html` is bullwhip's page with a game block appended** — never a rewrite that
  reuses the ids (cogame-gridlock, 2026-08-23). **Every element the starter ships is kept, with its
  id**: `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`,
  `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`,
  `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, and the
  `fit()` + `bindFeedToggle` bootstrap script.
  **Elements removed: none.** The only edits are (a) the wordmark's inner text
  `BULL<span>WHIP</span>` → `THE<span>FIRM</span>` and the `<title>`, and (b) **one appended
  element**: `<div id="demandbar"></div>` inserted between `#scorebug` and `#board-wrap`, filled by
  the renderer with `SHIFT 3/8 · BOARD A 33 · B 15 · NEXT A 13 · B 36 · POOL 40% · PROFIT $820.80`.
  `replay-viewer/index.html` gets the identical treatment (it is the same page with `./` asset
  paths and the `firm_replay.js` / `static_replay.js` script tags).
- **Zoom: dropped entirely.** Bullwhip ships no `#viewpanel` (no zoom bar, no minimap) and none is
  added: the factory floor is a **fixed arena** that is always drawn to fit the frame, so per the
  pin the zoom controls do not exist here.

### Transport rules

- `--band` and `--hudscale` are set **on `:root`** by a `relayout()` function in the page's
  bootstrap script (`replay-viewer/index.html` and `client/replay.html`), called on `load`, on
  `resize`, and by the existing feed-toggle resize event: it measures `#transport`'s
  `offsetHeight` into `--band` and sets `--hudscale = clamp(0.8, width / 960, 1.15)`. `fit()`
  (bullwhip's canvas resizer) is called from the same function, so the canvas and the custom
  properties can never disagree.
- **Nothing is overlaid in the transport band.** `#transport` is the last child of `#stage` in
  normal flex flow at `z-index: 10`; the only absolutely-positioned overlays (`#lightpool`,
  `#grain`, `#endscreen`) live inside `#board-wrap`, which ends where the band begins, and
  `#loading` is pinned above it with `bottom: var(--band)`.
- **The endcard stops at `var(--band)`** — `#endscreen` is `position: absolute; inset: 0` inside
  `#board-wrap`, i.e. its bottom edge is exactly `var(--band)` above the page bottom — **and is
  dismissed by every seek**: `attachReplay`'s `setIndex` calls
  `updateEndscreen(container, results, index >= events.length && events.length > 0, …)` on *every*
  index change, and `updateEndscreen` does `container.classList.toggle("show", !!show)`, so any
  scrub below the last event hides it. Bullwhip's code, kept verbatim.
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` is kept verbatim except that a
  beat marker is created as `<button type="button" class="beat-marker …">` with an `aria-label` /
  `title` (`"Shift 3 — Gizmo works line B"`, `"Shift 3 — the manager's memo"`,
  `"Shift 3 settles — profit $273.60"`, `"Final"`) and an `onclick` that seeks to that event index;
  the container keeps its drag-to-seek pointer handlers. Markers are emitted for **every event kind
  that has one** — `memo`, `work`, `settle`, `end` — and the appended CSS block defines a rule for
  each of those four kinds (`start` and `shift` are the round spans/separators the starter already
  draws, one span per shift with a separator every 4). *This is the one deliberate change to the
  starter's `buildScrub`; the transport rule in `prompts/10-design.md` requires buttons and
  outranks "verbatim".*

### The stage (factory floor), drawn over `data/arena_floor.png` in the Ink-&-Print palette

Real art, from the starter's own assets — no placeholder boxes. The five cog sprites are
bullwhip's four `soldier_<red|blue|green|yellow>_front.png` plus a fifth seat colour,
`soldier_violet_front.png`, produced once by `tools/make_violet_cog.py` as a fixed +250° HSV hue
rotation of `soldier_red_front.png` (value and alpha preserved) and committed; the renderer's
existing `COLORS[4] === "violet"` and `"soldier_" + color + "_front.png"` lookup then resolve
unchanged.

- **The glass office** (top strip, centre): the manager's cog behind a lit window, its alias/policy
  name, `POOL 40%` and the running `PROFIT $820.80`. The **order board** hangs beside it as two
  bars, `A 33` and `B 15`, with next shift's numbers ghosted behind them; on the switch shift the
  board flashes and the feed says the demand switched.
- **Paper planes**: on a `memo` event a paper slip (bullwhip's `drawSlip`, its eased `SLIP_MS`
  flight reused) launches from the office to **each** machine bay, carrying the ordered line
  (`→ LINE B`); the memo text pops as a speech bubble over the office using the existing
  `wrapLines` / `drawBubble`.
- **Four machine bays** across the floor, one per machine, laid out on bullwhip's column pitch: the
  worker's cog sprite in its seat colour, a machine body, a `LINE A` / `LINE B` tag (amber when it
  differs from the order), a **condition gauge** (0–100 bar, green → amber → red, with the number
  printed), and the output dock showing the shift's `units` as crates (`drawCrate` /
  `drawCrateCluster`, kept). While a `work` event is fresh: **sparks** off the machine when
  `run > 0` (intensity from the hours), a **wrench glyph** turning when `maint > 0`, and an **idle
  sway** of the cog when `run == 0`. A machine running a line other than its order gets a red
  `DEFIED ORDERS` tag; a machine that ran zero hours gets `IDLE`.
- **Payday**: on the `settle` event coins stream from the office cash drawer to each bay along the
  split, over `SLIDE_MS`, with the dollar amount printed at the bay (`$45.60`) and a green/red
  delta against last shift's pay. A share that fell is the mutiny cue and is drawn in red.
- **Bottom strip** (the slot bullwhip gives its seismograph): a chart across shifts of **demand vs
  units made per line** (A and B, demand dashed, made solid), plus a **profit line** and a **total
  wages line**, with an amber vertical rule labelled `DEMAND SWITCH` at `switchShift` and the
  now-line at the current shift. This is the picture of whether the floor followed the board.

### Readouts

- **`#clock`** (top band): `SHIFT 3 / 8 · WAITING ON 5` while a shift is open, `SHIFT 3 / 8 ·
  SETTLED` between, `FINAL · PROFIT $2,188.80` at the end. Words and numerals, never notation.
- **`#demandbar`** (appended): `SHIFT 3/8 · BOARD A 33 · B 15 · NEXT A 13 · B 36 · POOL 40% ·
  PROFIT $820.80`.
- **`#scorebug`**: five plates. The manager's plate is `name · MANAGER · $820.80 · score 0.91`; a
  worker's plate is `name · MACHINE 2 · $32.10 · share 30% · score 1.07`, with a red `IDLE` chip
  when it ran zero hours last shift and an amber `DEFIED` chip when it ran a line other than its
  order.
- **`#feed`** (side panel, grouped by shift with `SHIFT 3` heads, `describeEvent` rewritten around
  the kinds above):
  - `shift` → `The board wants 33 A and 15 B. Orders: A A A B · pool 40% · shares 30/30/20/20.`
  - `memo` → `Sprocket (Manager) posts: "Switch machine 4 to A, the B book is drying up." — pool 40%, shares 30/30/20/20.`
  - `work` → `Gizmo (Machine 2) runs line B 7h, maintains 3h — 14 units` (+ ` · DEFIED ORDERS`,
    + ` · IDLE`), then a `says:` line for the report and a dim `notes:` line when the notes changed.
  - `settle` → `Shift 3 settles — 45 sold, 3 scrapped, revenue $456.00, wages $182.40, profit $273.60. Paid: Gizmo $45.60, Ratchet $45.60, Widget $30.40, Bolt $30.40.`
  - `end` → `Final — profit $2,188.80 over 8 shifts, wages $1,459.20.` plus
    `Episode deadline — the whistle went early; scored on 5 of 8 shifts.` when `reason == "deadline"`.
- **`#endscreen`**: title `FINAL — 8 SHIFTS · PROFIT $2,188.80`; verdict `<manager> RAN A TIGHT
  SHOP` when the manager's score is the highest at the table, else `<worker> TOOK THE FLOOR`;
  a `deadline` reason line when applicable; rows ranked by score with columns
  `role`, `units`, `paid / profit`, `share`, `score`.

### Legible at 360 px wide

The canvas re-fits on every `relayout()`. Below 560 px the stage stacks the four bays 2 × 2 under
the office, drops the crate art to the printed unit count, keeps the condition gauges and the
paper planes at full size, and the feed collapses behind the starter's existing `LOG »` toggle;
below 480 px the scorebug goes to two columns with the manager plate spanning the row, and
`#demandbar` shortens to `A 33 · B 15 · 40%`. Everything is rendered as words and numerals a
casual spectator can read — `LINE B`, `COND 74`, `$45.60`, `12 units` — never `L1`, `c74` or `u12`.

---

## Packaging

- **`compose.yaml`** — service `firm`, `image: coworld-firm:latest`, `platform: linux/amd64`,
  `build: {context: ., network: host}`.
- **`Dockerfile`** — bullwhip's, renamed: one image, two entrypoints, `/bin/firm` (default,
  `CMD`) and `/bin/firm-player`; `data/` and `client/` copied into the run image; `nim.cfg`
  regenerated from the container's package tree.
  **`Dockerfile.replay-viewer`** — bullwhip's, renamed (emsdk 4.0.15, nimby 0.1.27, Nim 2.2.4).
- **`firm.nimble`** — version `0.1.0`, `srcDir = "src"`, requires `nim >= 2.2.4`, `bitworld`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`; `nimby.lock` copied from bullwhip unchanged.
- **`data/`** — bullwhip's `arena_floor.png`, `font.ttf`, `FONT_LICENSE.txt` and the four cog
  sprites, plus the committed `soldier_violet_front.png` recolour described in §Viewer.
- **`coworld_manifest_template.json`** — game name `firm`, image `{{FIRM_IMAGE}}`,
  `run: ["/bin/firm"]`, `"replay_viewer": {"bundle": "static-replay-viewer"}`, `source_url`
  `https://github.com/Metta-AI/cogame-firm/tree/main`, owner `daveey@gmail.com`,
  `env.ANTHROPIC_API_KEY_URI = secret://coworld/firm/anthropic_api_key`, tags
  `["principal-agent","hierarchy","incentive-design","mixed-motive","llm-driven","turn-based",
  "five-player","economics"]`.
  - **`config_schema`** (`additionalProperties: false`, required `tokens` + `players`):
    `tokens` and `players` `minItems`/`maxItems` **5**; **`num_agents` integer minimum 5 maximum
    5**; `seed` integer; `shifts` integer 4..24 default **8**; `reports` boolean default `true`;
    `episodeTimeoutSeconds` 60..6000 default 1200; `turnDelayMs` 0..10000 default 400;
    `model` string default `claude-sonnet-5`; `maxOutputTokens` 64..2000 default 800;
    `llmTimeoutSeconds` 5..300 default 30; `player_connect_timeout_seconds` number default 180.
  - **`results_schema`** — required `names`, `scores`, `roles`, `pay`, `units`, `revenue`, `wages`,
    `profit`, `shifts`, `maxShifts`, `reason`; the array fields `minItems`/`maxItems` **5**;
    `reason` a string documented as `complete` or `deadline`.
  - **`game.protocols.player`** — the `firm.player.v1` text from §Server in full: the frame shapes,
    the per-role redaction, the reply schema with its caps, the 4000-char prompt cap, the
    `scripted` values, and "a policy is just a prompt: field one by reusing the published
    firm-player runnable with `PLAYER_PROMPT` set to your strategy".
  - **`game.protocols.global`** — the `/global` snapshot shape in full, the event vocabulary, and
    the note that the static replay bundle renders hosted replays at `index.html?replay=<url>`.
  - **`game.docs.readme`** — one paragraph: five cogs run a factory for eight shifts; one manager
    sees the order board and can only write memos and set the pay rule; four workers each see one
    machine's condition and choose hours between running, maintaining and idling; revenue splits by
    the manager's rule; workers score pay minus effort, the manager scores profit; how to field a
    policy; the two scripted baselines that make episodes always complete.
  - **`game.docs.pages`** — two pages:
    - `rules.md` — seats and the seeded role draw, the machine model with every constant, the
      numbered shift resolution, the one-shift memo delay, the observation split, the reply schema
      and its caps, the two endings.
    - `scoring.md` — the two formulas and their sign, the normalization scales with the worked
      "competent firm" arithmetic above, the marginal-hour calculation that makes payroll 30 % the
      indifference point, what the league ranks by (mean episode score), and why both roles are on
      one scale.
  - **`player` runnables** — all `image: {{FIRM_IMAGE}}`, `run: ["/bin/firm-player"]`, requests
    `100m` cpu / `64Mi` memory, limit `1` cpu:
    `firm-player` (the prompt policy, no `PLAYER_SCRIPTED`),
    `firm-steady` (`env.PLAYER_SCRIPTED = "steady"`),
    `firm-taskmaster` (`env.PLAYER_SCRIPTED = "taskmaster"`).
  - **`variants`** — both carry `num_agents`:

    | id | name | description | `game_config` |
    |---|---|---|---|
    | `standard` | Standard shift | Five cogs, one office, four machines, eight shifts; the order board switches lines once and the workers may report. | `players` ×5, **`num_agents`: 5**, `shifts`: 8, `reports`: true, `turnDelayMs`: 400, `player_connect_timeout_seconds`: 180 |
    | `silent-floor` | Silent floor | The same firm with the workers' report channel closed: the manager gets numbers and nothing else. | `players` ×5, **`num_agents`: 5**, `shifts`: 8, `reports`: false, `turnDelayMs`: 400, `player_connect_timeout_seconds`: 180 |

  - **`certification`** — `game_config`: `players` = `Sprocket`, `Gizmo`, `Ratchet`, `Widget`,
    `Bolt`, **`num_agents`: 5**, `seed`: 7, `shifts`: 4, `turnDelayMs`: 0,
    `player_connect_timeout_seconds`: 180; `players` list =
    `[firm-player, firm-steady, firm-player, firm-taskmaster, firm-steady]` (5 entries).
- **CI** — `.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
  substituting `<slug>` = `firm`, `<IMAGE>` = `coworld-firm`, **`<SEATS>` = `5`**.
  `tools/ci/docker_smoke.sh` (same substitutions, committed `chmod +x`), `tools/ci/viewer_smoke.mjs`
  copied **verbatim** (no substitutions), `tools/ci/policies.json` listing the two prompt policies
  phase 40 uploads (`firm-boss`, `firm-hand`) plus the two baselines.

### Design pins (playbook §Phase 0) — how each is satisfied

| Pin | Where |
|---|---|
| Starter chosen by game shape | `cogame-bullwhip` — turn-based, simultaneous, hidden-information, mixed-motive economics with LLM-prompt policies (title paragraph). |
| Public `Metta-AI/cogame-firm` | Repo created **public** in phase 20 (a certification prerequisite); `source_url` points at it. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `firm-player` (`PLAYER_PROMPT`) vs `firm-steady` / `firm-taskmaster` (`PLAYER_SCRIPTED=…`), one image, two entrypoints (§Decisions, §Packaging). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; the wasm module re-derives every frame in the browser; nothing but S3 is contacted (§Viewer). |
| Real art; starter chrome reused verbatim | `chrome.css` byte-for-byte + one appended game block; `replay.html`/`index.html` = the starter's page + one appended element, nothing removed; every chrome function kept; sprites from `data/` plus the committed violet recolour (§Viewer). |
| Legible to a casual spectator | `LINE B`, `COND 74`, `$45.60`, `12 units`; 360 px layout described (§Viewer). |
| Two name spaces | Anonymous cog aliases in-game; `policyNames` + `makeNameMap` spectator-side only (§The game). |
| Degrade never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6`, pre-shift deadline check, `endEarly()`, `sampleEpisode` fitting, 680 s absolute worst case (§Decisions). |
| `num_agents` in every variant AND the cert fixture | **5** in `standard`, in `silent-floor`, in `certification.game_config`, and `<SEATS>` = 5 in `tools/ci/docker_smoke.sh`. |

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` twice, debug and `-d:release`.

### `tests/test_sim.nim` (sim unit tests)

1. **Roles** — for seeds `[0, 1, 7, 42, 1234]`: exactly one Manager and four Workers;
   `managerSeat` / `workerSeat` / `workerIndex` are mutually consistent; across 20 seeds the
   manager lands on more than one seat.
2. **Board** — `demandA`/`demandB` have length `shifts + 2`; each is flat, switches exactly once at
   `switchShift ∈ 3..5`, and the two levels are `HighDemand ∈ 30..36` / `LowDemand ∈ 12..18`;
   A and B are always the two levels in opposite order; over 200 seeds both level pairs vary.
3. **Opening state** — shift 0: condition 100 on all four, setups `A A A B`, orders equal the
   setups, `payroll == 30`, `split == [25,25,25,25]`, `directive == StandingOrder`,
   `pendingSeats().len == 5`, `events == [start, shift]`.
4. **Determinism** — the same seed reproduces roles, demand levels, switch shift and aliases
   exactly; a different seed differs in at least one of them.
5. **Hand-computed shift** — machines at condition 100 on their own lines, `run 6 / maint 3`:
   `units == 12` each, condition unchanged (−18 + 18), `toil == 13.5`; with `demandA = 33`,
   `demandB = 15` and setups `A A A B`, `soldA == 33`, `surplusA == 3`, `soldB == 12`,
   `revenue == 456.0`; at `payroll 40` and equal split, `pool == 182.4`, each `pay == 45.6`,
   `profit == 273.6`.
6. **Changeover and wear** — a machine ordered onto the other line with `run 6` produces
   `floor(2 × (6 − 2) × q)` units and ends on the new setup; `run 10 / maint 0` costs 30 condition;
   `run 4 / maint 6` gains 24; condition clamps at 0 and 100; at condition 0, `q == 0.5` and output
   halves exactly.
7. **Memo delay** — a memo applied in shift `s` changes nothing in shift `s`: the orders, payroll
   and split used by `resolveShift(s)` are the ones in force at step 1, and the new values appear
   only in the shift `s + 1` `shift` event. An empty directive leaves the standing directive
   unchanged; a non-empty one replaces it.
8. **Split normalization** — `normalizeSplit` maps `[1,1,1,1] → [25,25,25,25]`,
   `[50,50,0,0] → [50,50,0,0]`, `[1,0,0,0] → [100,0,0,0]`, `[0,0,0,0] → [25,25,25,25]`, and
   `[1,1,1,0]` (largest remainder) → a vector of four non-negative integers summing to **exactly
   100**; a 500-case randomized sweep asserts the sum is always 100 and no entry is negative.
9. **Legality** — `applyWork` raises `FirmError` on `run = -1`, `run = 11`, `maint = 11`,
   `run + maint = 11`, an unknown line, a seat that has already acted this shift, and any call
   after the episode is done; a raised call changes nothing (`pendingSeats` unchanged).
   `applyMemo` raises on `payroll = -1`, `payroll = 61` and a `split` of the wrong length.
10. **Rune truncation** — a 400-rune multi-byte directive (`"é" × 400`) truncates to **240 runes**
    and a 400-rune report to **120 runes**; both `validateUtf8() == -1`; every event's `say` and
    `text` in the log validate as UTF-8; with `reports = false` every report is `""`.
11. **Observation split** — for every frame, the manager's `playerStateJson` contains no
    `condition`, `run`, `maint` or `toil` key anywhere, and the built manager prompt string contains
    none of the machines' condition values; a worker's `playerStateJson` contains no `demandA`,
    `demandB`, `price`, `revenue` or `profit` key, and the built worker prompt contains neither
    demand number nor the word for the board's levels. Both are asserted on a seeded 6-shift
    episode, every shift.
12. **Scoring** — `score(worker) == workerNet / (shiftsPlayed × 30.0)` and
    `score(manager) == firmProfit / (shiftsPlayed × 300.0)` on a hand-built episode; a worker that
    idles every shift with a zero share scores exactly `0.0`; a worker that works with a zero share
    scores strictly negative; `resultsJson` has 5 names / scores / roles / pay / units,
    `pay[managerSeat] == 0.0`, `units[managerSeat] == 0`, and
    `revenue − wages == profit` to 1e-9.
13. **Endings** — a full episode ends with `reason == "complete"`, `shiftsPlayed == shifts`,
    `events[^1].kind == evEnd`, `events[^2].kind == evSettle`, and any further `applyWork` raises;
    `endEarly()` mid-episode gives `reason == "deadline"`, scores normalized by the shifts played,
    and is a no-op when called twice; `endEarly()` before shift 0 resolves gives all-zero scores
    and `shiftsPlayed == 0`.
14. **Replay** — `replayMatch(config, events).len == events.len + 1`; the final frame's
    `tableStateJson` equals the live one; `eventFromJson(eventToJson(e))` round-trips one event of
    **every** kind (`start`, `shift`, `memo`, `work`, `settle`, `end`) field by field; a tampered
    `settle` event (revenue + 1) and a tampered `shift` event (condition + 1) each raise
    `FirmError`; a recorded `deadline` ending is honoured by the re-derivation.

### `tests/test_bot.nim` (bounded-orders / legality assertion on the scripted baselines)

1. **Legality and boundedness** — for seeds `[1, 7, 42, 1234]` × both baselines in **both** roles
   (all-`steady`, all-`taskmaster`, and mixed tables), a full scripted episode completes with
   `reason == "complete"` and: no `applyWork` / `applyMemo` ever raises; every `run` and `maint` is
   in `0..10` with `run + maint ≤ 10`; every `line` is `"A"` or `"B"`; every `payroll` is in
   `0..60`; every `split` is four non-negative integers summing to 100; every directive is
   ≤ 240 runes and every report ≤ 120 runes; scripted seats emit empty `notes`; and the whole
   episode runs in under 2000 ms.
2. **Baseline behaviour** — `steady` workers hold condition within `±3` of 100 across an 8-shift
   episode and always run the ordered line; `taskmaster` workers drive at least one machine below
   condition 25 by shift 4; an all-`steady` table's manager score is strictly greater than an
   all-`taskmaster` table's on the same seed (the competent baseline is the one a prompt has to
   beat, and the log echoes both numbers so tuning drift is visible).
3. **Honest reports** — every `steady` worker's report parses back to the machine's actual previous
   `condition`, `run`, `maint` and `units` (the baseline never lies; only prompts can).
4. **Fallback** — with no credentials `newLlmClient(config).disabled` is true and `decideAll`
   returns scripted decisions for all five seats with **no network call**.
5. **Reply parsing** — `parseManagerReply` / `parseWorkerReply` accept the documented spellings and
   shapes, drop unknown line names to the current setup, renormalize a split that does not sum to
   100, reject a missing/out-of-range `payroll`, reject a missing/out-of-range `run`, reject
   `run + maint > 10`, and cap `directive` / `report` / `notes` at their rune limits.

### End-to-end, replay and viewer (CI jobs)

6. **`docker-smoke`** (`tools/ci/docker_smoke.sh`, `<SEATS>` = **5**) — builds the production image
   and runs **one real episode** in raw docker with the certification fixture's five-seat mix and
   no `ANTHROPIC_API_KEY`, asserting the game exits 0 having written `results.json` and a replay,
   that `num_agents` = 5 agrees across `certification.game_config`, `certification.players` and
   `SMOKE_SEATS`, and that `results.names` / `results.scores` have 5 entries. The replay is copied
   to `dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.
7. **Strict-UTF-8 replay parse** — the same script decodes the replay bytes as **strict UTF-8** and
   parses them as JSON (`SMOKE_REQUIRE_REPLAY_JSON=1`, the default); `tests/test_sim.nim` item 10
   covers the multi-byte truncation path that would otherwise break it.
8. **Viewer smoke** — `ci.yml`'s **`wasm-viewer`** job (`needs: docker-smoke`) builds the bundle
   with `tools/build_replay_viewer.sh`, downloads the `smoke-replay` artifact and **executes** the
   bundle in headless Chromium: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer
   --replay dist/smoke/replay.json --timeout 90`. It passes only when the page sets
   `data-replay-loaded="true"` (or posts the `coworld-replay` `ready` envelope), never sets
   `data-replay-error`, and the `#clock` / `#scorebug` readouts differ across the 0 % / 50 % /
   100 % scrub positions. `viewer-smoke.png` and `viewer-smoke.json` are uploaded on success and
   failure alike. The bundle is **executed, not merely built**.

---

## Out of scope (v1)

- More than one manager, a middle-management layer, promotion or firing, and any seat count other
  than 5.
- Hiring, quitting, or a worker refusing to connect: seats are fixed for the episode.
- More than two product lines, per-line prices that move, inventory carried between shifts,
  backorders, raw materials or a supply chain (that is bullwhip's game, not this one).
- Machine breakdowns as random events, repair parts, or any stochasticity inside a shift —
  resolution is fully deterministic given the decisions and the seed.
- Contracts, bonds, or any binding commitment: the memo is cheap talk with a pay rule attached,
  and the pay rule is the only enforceable instrument.
- A private manager→worker channel, worker→worker chat, or a vote — the anti-collusion pins depend
  on the one-to-all memo and the one-way report.
- Cross-episode memory, reputation or wage carry-over between policies.
- Scoring a worker on anything but pay net of toil, or the manager on anything but profit — no
  fairness bonus, no output bonus, no morale term.
- Real-time play, an RL vector observation, or a live-server (`/client/replay`) replay viewer.
- Localisation, audio, and any viewer feature beyond the factory-floor stage described above.
