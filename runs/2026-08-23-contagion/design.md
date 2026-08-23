# Contagion: six governors, one epidemic, nine roads — design note (2026-08-23)

`Metta-AI/cogame-contagion`. Six LLM-piloted governors each run one region of a six-node road
network for twenty weeks. Every week each governor sets three dials — **lockdown**, **testing**,
**border gates** (one per road) — talks to the table, and may wire **aid** to any other region. The
infection then crosses the roads whether or not the road was closed, the economy pays for the dials
and the sickness, and the dead are counted. A governor's score is its region's accumulated GDP minus
two credits per death.

It is forked from **`Metta-AI/cogame-bullwhip`**, read at its read-only mount
`/workspace/starters/cogame-bullwhip`, and **every convention there holds here unless this note says
otherwise.** The starter is pinned by game shape: Contagion is a turn-based game with simultaneous
numeric decisions, free-text talk between seats, hidden information, and an economic score — the
first row of the starter table in `prompts/10-design.md`. Bullwhip is the newest member of the
parley → cosino → focus → babel → bullwhip lineage and it is a *closer structural match than babel*:
bullwhip already has (a) a **weekly simultaneous tick** where every seat submits one numeric decision
and the last submission resolves the week (`src/bullwhip/sim.nim:246-284`), (b) **one parallel LLM
batch per week** for all seats (`src/bullwhip/llm.nim:419-472`, `curly.makeRequests`), (c) short
non-binding neighbour messages with a one-week delay and rune-boundary truncation
(`src/bullwhip/sim.nim:262-268`), (d) **per-seat private notes** fed back verbatim, (e) a per-week
economic ledger with a scoring sign, (f) a `deadline` early-settle wired to 60 % of the episode
timeout (`src/bullwhip/server.nim:215-280`), and (g) a **static wasm replay viewer** whose four files
are internally consistent (`replay-viewer/`). Contagion changes the payload of the weekly decision
and the resolution rules; it changes almost nothing else.

**There is no `OPEN` section.** Every choice the idea leaves loose (seat count is pinned at 6 by the
idea; scoring formula is pinned in shape by the idea and its constants are settled here; graph shape,
dial ranges, observation redaction, viewer composition and policy prompts) is a rail the designer
settles. Each is decided below with one sentence of reasoning.

**Source idea, verbatim:**

> Regions on a graph; each governor sets weekly dials (lockdown level, testing, border closure) with
> an economy cost, and may talk and transfer aid. Infection crosses edges regardless of who paid for
> restrictions. Score = regional GDP minus deaths x penalty. Your neighbour's looseness is your
> problem.
>
> Seats: 6
> Motive: mixed-motive with spillovers
> Policy interface: LLM prompt (parley stack)
> Fills gap: policy externalities / aid bargaining / epidemiology
> Integrity (anti-collusion): Aid coalitions are the gameplay, not collusion; governor aliases
> anonymous per episode, one seat per account.
>
> Replay plan (watchability): The outbreak is an animated red stain crossing borders; lockdown dials
> appear as shutters slamming on regions, aid transfers arc as gold packets, GDP and death tickers
> run per governor. Leaky-border moments are instantly visible.

**Design pins (`playbooks/make-coworld.md` §Phase 0, SPEC §"Design pins every coworld inherits") and
where each is satisfied:**

| Pin | How Contagion satisfies it |
|---|---|
| Starter by game shape | `cogame-bullwhip` — turn-based, simultaneous numeric decisions, talk, LLM-prompt policies (reasoning above). |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-contagion`, **created public** — public is a certification prerequisite (`source-resolves` 404s on private). §Packaging. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (two champion prompts, given verbatim) vs `PLAYER_SCRIPTED=sentinel` / `PLAYER_SCRIPTED=laggard`; one image `coworld-contagion:latest`, both entrypoints in it. §Decisions, §Packaging. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`, built by `tools/build_replay_viewer.sh`; the wasm module re-derives every frame from the replay bytes. §Viewer, §Packaging. |
| Real art, starter chrome verbatim | Bullwhip's `client/chrome.css` + the `client/renderer.js` chrome half kept verbatim (id-for-id list in §Viewer); an authored painted map plate, painted region tiles, shutter/gate/aid-packet sprites, six governor portraits. No placeholder rectangles. §Viewer. |
| Two name spaces | Agents see only **region aliases** (`Harborlea`…`Saltmarch`), and the seat→region assignment is a seeded permutation re-drawn every episode; real policy names appear only in `results.names`, `replay.policyNames`, and the viewer's scorebug/endscreen/feed. §Server, §Viewer. |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | 720 s play budget; hard worst case 707 s, typical ≈ 330 s; arithmetic spelled out in §Decisions; every wait bounded; LLM timeout or parse failure → one retry inside the same week budget → the `sentinel` scripted move. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 6** in variant `standard`, variant `sprint`, and `certification.game_config`; `SMOKE_SEATS=6` in `tools/ci/docker_smoke.sh` as an independent cross-check. §Packaging. |
| Upload policies before `upload-coworld`, secret after | Inherited from `templates/coworld-release.yml` unchanged; `tools/ci/policies.json` lists the four policies. §Packaging. |

---

## The game

**Six regions, nine roads, one virus.** Each seat is the governor of exactly one region. Regions are
identical in size and structure; what differs is where the outbreak started and what the other five
governors do. A governor's only levers are three dials, a microphone and a chequebook. The virus does
not care which of those a governor paid for: it walks the roads.

### Seats and the map

- **Seats: exactly 6 (`num_agents` = 6).** Pinned by the idea; it appears in every manifest variant
  and in the certification fixture (§Packaging).
- **Regions (positions 0..5, fixed names, fixed art):** `0 Harborlea`, `1 Kestrel Flats`,
  `2 Riverbend`, `3 Ash Hollow`, `4 Wintermoor`, `5 Saltmarch`. Position `p` is always the same
  region name and always the same place on the map plate, so the art and the labels are stable.
- **Seat → position is a seeded permutation** (`posOf[seat]`, `seatOf[pos]`), exactly as bullwhip
  deals stages (`src/bullwhip/sim.nim:147-152`). This is the anonymity mechanism *and* the fairness
  mechanism: no policy slot is structurally stuck anywhere.
- **The graph is the 6-cycle plus its three long diagonals** (`K₃,₃`): edges
  `(0,1) (1,2) (2,3) (3,4) (4,5) (5,0)` as **main roads** and `(0,3) (1,4) (2,5)` as **back roads** —
  nine edges, every region with exactly two main roads and one back road. Chosen because it is
  *vertex-transitive*: every region's structural situation is byte-for-byte identical, so seat
  fairness needs no argument. Mobility weight `MobilityPpm`: main road `250_000`, back road
  `150_000`.
- **Population:** every region starts with exactly `Pop = 1_000_000` people. Equal populations keep
  the map exactly fair; the asymmetry that makes an episode interesting is the seeded outbreak, not a
  seeded handicap.

### State per region (all integers — no floats anywhere in the rules)

`susceptible`, `infected`, `recovered`, `dead` (people), `gdp` (credits, the running ledger, may go
negative), `lockdown` 0..4, `testing` 0..3, `gate[3]` 0..2 (one per incident edge, in the region's
fixed neighbour order), plus per-week derived numbers recorded for the replay: `newInfections`,
`deathsWeek`, `confirmed`, `confirmedNew`, `grossGdp`, `spendWeek`, `aidIn`, `aidOut`, `hospital`
(band 0..3). `alive = Pop − dead`.

**Every rate is an integer in parts per million (ppm) and every update is integer arithmetic with
truncating division.** This is deliberate and load-bearing: the wasm replay viewer re-runs the *same*
Nim rules in the browser and its re-derivation is checked against the recorded per-week state
(bullwhip's `sameStages` discipline, `src/bullwhip/sim.nim:403-449`). With floats that check would be
a coin flip between native x86 and wasm; with integers it is exact.

### The constant tables (public knowledge — printed in every prompt, in the rules page, and in the viewer's help)

| Table | Index | Values |
|---|---|---|
| `BetaPpm` (weekly transmission) | `lockdown` 0..4 | `1_150_000, 900_000, 640_000, 400_000, 220_000` |
| `TestFactorPpm` (multiplies Beta: found cases isolate) | `testing` 0..3 | `1_000_000, 900_000, 780_000, 640_000` |
| `DetectPpm` (share of true infections you can see) | `testing` 0..3 | `150_000, 350_000, 650_000, 900_000` |
| `GatePassPpm` (road pass-through before leak) | effective gate 0..2 | `1_000_000, 400_000, 0` |
| `LockdownGdpPpm` (output factor) | `lockdown` 0..4 | `1_000_000, 920_000, 800_000, 620_000, 400_000` |
| `TestCost` (credits/week) | `testing` 0..3 | `0, 20, 55, 110` |
| `BorderOwnCost` (credits/week per road, paid by the closer) | `gate` 0..2 | `0, 10, 30` |
| `BorderNeighbourCost` (credits/week per road, paid by the region at the far end) | `gate` 0..2 | `0, 5, 15` |

| Scalar | Value | Meaning |
|---|---|---|
| `LeakPpm` | `120_000` | A sealed road still passes 12 % of its traffic. This is the idea's sentence, as a number. |
| `CrossBetaPpm` | `700_000` | Imported contacts transmit at 70 % of local ones. |
| `ForceCapPpm` | `900_000` | Ceiling on one week's total force of infection. |
| `ResolvePpm` | `350_000` | Share of the infectious cohort that resolves each week (mean ≈ 2.9 weeks). |
| `BaseIfrPpm` | `8_000` | 0.8 % of resolved cases die when hospitals are not overloaded. |
| `HospitalCap` | `25_000` | Infectious people a region's hospitals can carry. |
| `MaxOverloadPpm` | `3_000_000` | Overload multiplies IFR by at most 4×. |
| `BaseGdp` | `1_000` | Credits a fully open, fully healthy region produces per week. |
| `SickDragMultPpm` | `1_500_000` | Output lost = 1.5 × prevalence, capped at `SickDragCapPpm = 600_000`. |
| `DeathPenalty` | `2` | Credits deducted per death. |
| `MaxAidPerWeek` | `200` | Credits one region may send per week, over at most `MaxAidEntries = 3` transfers. |
| `SeedInfected` | `40` | Every region starts here. |
| `OutbreakInfected` | `1_200` | Added to one seeded position at week 0. |
| `VariantMultPpm` | `1_250_000` | From `variantWeek` on, every `BetaPpm` entry is multiplied by 1.25. |
| `Weeks` | default `20`, range `4..40` | `MinWeeks = 4`, `MaxWeeks = 40`. |
| `PacingBudgetMs` | `90_000` | Total spectator pacing sleep allowed in an episode. |

Seeded per episode (one `initRand(int64(seed) * 7919 + 17)` stream, drawn in this order, exactly as
bullwhip does): the seat→position permutation; `outbreakPos ∈ 0..5`; `variantWeek ∈ 8..12`; then the
region aliases are *not* drawn (region names are fixed to positions — the permutation is what
anonymises). A second stream `initRand(int64(seed) * 6779 + 31)` is unused here; bullwhip's
`tableNames` is replaced by `regionNames`, which returns the fixed six names in position order.

### Initial state (week 0, already observed)

Every region: `susceptible = 999_960`, `infected = 40`, `recovered = 0`, `dead = 0`, `gdp = 0`,
`lockdown = 0`, `testing = 0`, all three gates `0` (open). The seeded outbreak position instead has
`susceptible = 998_800`, `infected = 1_200`. Week 0 is observed and takes decisions; the first
resolution produces week 1.

### The weekly tick

Week `w` is *observed*: each governor reads its view (below) and submits one decision. Decisions are
**simultaneous** — every governor's view is a snapshot of the state at the start of week `w`, and no
governor sees another's week-`w` decision before submitting. When all six decisions are in, the week
**resolves** into week `w+1`.

### Resolution order (exact, numbered, no exceptions)

Let `L[r]`, `T[r]`, `G[r][e]` be the dials submitted this week, and let `I0[r]`, `S0[r]`, `A0[r]`
(`alive`) be the pre-resolution state of region `r`.

1. **Dials latch.** For every region: `lockdown[r] = L[r]`, `testing[r] = T[r]`, and for each incident
   edge `e`, `gate[r][e] = G[r][e]`. A gate the governor did not mention keeps last week's value.
   Both ends of every road are now known, so each edge `e = (r,q)` gets its **effective gate**
   `eff(e) = max(gate[r][e], gate[q][e])` — the tighter end governs the road.
2. **Talk queues.** Each decision's `say` (≤ 160 runes, truncated on a rune boundary) is moved into
   `heard[]` and delivered to **all six governors** at the start of week `w+1`. Public, one week
   late, non-binding, and *not* delivered at all when `talk` is false. Public rather than
   neighbour-only because the idea's gameplay is aid **coalitions**, which need a table.
3. **Aid settles.** For each region `r`, in seat order, the validated aid entries (§Reply schema) are
   settled against `gdp[r]` **as it stood at the start of this step**: running total `out`, each
   entry clamped so `out ≤ min(MaxAidPerWeek, gdp_at_step_start[r])`, then
   `gdp[r] −= out`, `gdp[recipient] += amount` for each entry. Because every sender's clamp reads
   only its own pre-step ledger, the outcome is independent of the order senders are visited; the
   order only fixes the feed. `aidOut[r] = out`; `aidIn[q]` accumulates. Aid received this week
   cannot be re-sent this week.
4. **Infection crosses the roads.** All forces are computed from the pre-resolution `I0`/`A0` of
   *every* region first, then applied — a simultaneous update, so nobody's spread depends on the
   order regions are visited.
   - `beta[r] = BetaPpm[lockdown[r]]`, multiplied by `VariantMultPpm` and divided by `1_000_000`
     once `w ≥ variantWeek`.
   - `prev[r] = (I0[r] * 1_000_000) div A0[r]`  (prevalence, ppm)
   - `local[r] = ((beta[r] * TestFactorPpm[testing[r]]) div 1_000_000) * prev[r] div 1_000_000`
   - for each incident edge `e = (r,q)`:
     `pass(e) = LeakPpm + ((1_000_000 - LeakPpm) * GatePassPpm[eff(e)]) div 1_000_000`
     `imp(r,e) = (((MobilityPpm[e] * pass(e)) div 1_000_000) * ((CrossBetaPpm * prev[q]) div 1_000_000)) div 1_000_000`
   - `force[r] = min(ForceCapPpm, local[r] + Σ_e imp(r,e))`
   - `newInfections[r] = min(S0[r], (S0[r] * force[r]) div 1_000_000)`
   - apply: `susceptible[r] -= newInfections[r]`, `infected[r] = I0[r] + newInfections[r]`.

   Two roads sealed at both ends still pass 12 % of their traffic, so `pass = 120_000` is the floor
   for every edge in the game. **That is the idea's "infection crosses edges regardless of who paid
   for restrictions", written as arithmetic.**
5. **Economy and GDP.** Using the post-spread `infected[r]` and the pre-death `A0[r]`:
   - `aliveShare = (A0[r] * 1_000_000) div Pop`
   - `sick = min(SickDragCapPpm, ((infected[r] * 1_000_000 div A0[r]) * SickDragMultPpm) div 1_000_000)`
   - `outputPpm = (((LockdownGdpPpm[lockdown[r]] * aliveShare) div 1_000_000) * (1_000_000 - sick)) div 1_000_000`
   - `grossGdp[r] = (BaseGdp * outputPpm) div 1_000_000`
   - `spendWeek[r] = TestCost[testing[r]] + Σ_e BorderOwnCost[gate[r][e]] + Σ_e BorderNeighbourCost[gate[q][e]]`
     — the second sum is the **spillover**: a road your neighbour shut costs you trade too.
   - `gdp[r] += grossGdp[r] - spendWeek[r]` (aid was already settled in step 3).
6. **Deaths and recoveries.** Only the cohort that was already infectious can resolve this week:
   - `hospitalLoad = (infected[r] * 1_000_000) div HospitalCap`;
     `over = min(MaxOverloadPpm, max(0, hospitalLoad - 1_000_000))`;
     `ifr = BaseIfrPpm + (BaseIfrPpm * over) div 1_000_000`  (0.8 % → at most 3.2 %)
   - `resolved[r] = (I0[r] * ResolvePpm) div 1_000_000`;
     `deathsWeek[r] = (resolved[r] * ifr) div 1_000_000`;
     `recoveredWeek[r] = resolved[r] - deathsWeek[r]`
   - `infected[r] -= resolved[r]`; `recovered[r] += recoveredWeek[r]`;
     `dead[r] += deathsWeek[r]`; `alive[r] = Pop - dead[r]`.
   - `hospital[r]` band for the observation: `0 normal` (`load < 400_000`), `1 strained`
     (`< 1_000_000`), `2 overloaded` (`< 2_000_000`), `3 critical` (`≥ 2_000_000`).
7. **Report.** `confirmed[r] = (infected[r] * DetectPpm[testing[r]]) div 1_000_000`,
   `confirmedNew[r] = (newInfections[r] * DetectPpm[testing[r]]) div 1_000_000`. These, not the true
   numbers, are what governors see (§Observation).
8. **Log and advance.** Append the `week` event carrying every region's full post-resolution state
   (§Sim module), `weeksPlayed += 1`, `week += 1`. If `weeksPlayed >= weeks`, the final week is
   observed (its state is logged and its costs count) but takes no decisions, and the episode settles
   `complete`. Otherwise the next week opens.

Note the deliberate ordering choice in steps 5 and 6: this week's output is computed on this week's
sickness, and this week's dead reduce *next* week's workforce. It matches the idea's stated order
(dials, talk, aid, spread, economy, deaths) and it is internally consistent.

### Scoring, sign, and what the league ranks by

```
score(seat) = gdp[posOf[seat]] - DeathPenalty * dead[posOf[seat]]        DeathPenalty = 2
```

Integer. **Higher is better**, and it can be negative — an uncontrolled epidemic loses more to the
death penalty than the region ever earned. `results.scores` therefore has **no `maximum`** in the
schema (bullwhip's `maximum: 0` was a consequence of `score = −cost` and does not carry over).
**The league ranks seats by mean episode score.** Results also report per-seat `gdp`, `deaths` and
`region`, plus episode aggregates `totalDeaths` and `totalGdp`.

Calibration, so the builder can check the constants produce a real trade-off over 20 weeks
(R₀ = `Beta/Resolve` = 1.15/0.35 ≈ 3.3 wide open, ≈ 0.63 at lockdown 4):

| Strategy | GDP | Deaths | Score |
|---|---|---|---|
| Never touch a dial | ≈ 15 000 | ≈ 21 000 (hospitals 10× over) | **≈ −27 000** |
| Lockdown 4 for the whole episode | ≈ 8 000 | ≈ 500 | **≈ +7 000** |
| Suppress hard while hot (L3/T2), open up after, gates keyed to neighbours | ≈ 14 400 | ≈ 1 500 | **≈ +11 400** |

Doing nothing is catastrophic, panicking is mediocre, and the top of the table needs *timing* and
*coordination* — which is the game the idea asked for.

### End conditions and the legal `results.reason` values

Exactly two values are legal, and the manifest's `results_schema` declares them as an enum:

- **`complete`** — `weeks` weeks resolved. The normal ending.
- **`deadline`** — the episode clock stopped play between two weeks (§Decisions). Scores use the
  weeks actually played; `results.weeks < results.maxWeeks` records it.

There is **no early-out on eradication.** If every region reaches zero infections the episode keeps
running, because banking GDP in the clean weeks is precisely the reward for having eradicated;
stopping early would confiscate it. There is no `fault` reason: a sim exception is a bug and CI's
end-to-end test fails on it rather than the game inventing a third ending.

---

## Decisions: LLM with scripted fallback

Transport, credentials, the JSON-only output contract, `extractJsonObject`, the Bedrock model
fallback list, `cleanText`'s rune-boundary truncation, and "no credentials ⇒ every seat scripted" are
ported from bullwhip `src/bullwhip/llm.nim` unchanged. Four things change.

**1. One parallel batch per week, for all six seats.** Decisions are simultaneous by rule, so the
server snapshots the sim outside the lock and fires all six model requests as a single
`client.curl.makeRequests(batch, timeout)` — bullwhip's `decideAll`
(`src/bullwhip/llm.nim:419-472`) with `Seats = 6`. Six round trips per week, not thirty-six. Seats
registered as scripted, and every seat when the client is disabled, are decided locally without
touching the network.

**2. Wall-clock budget, stated as arithmetic.** The game container never receives
`COWORLD_TIMEOUT_SECONDS`, so it assumes `episodeTimeoutSeconds` (1200) and plays inside
`PlayBudgetFraction = 0.6` of it — **720 s**.

```
per week:  first batch  llmTimeoutSeconds        = 25 s   (hard curl timeout)
         + retry batch  max(5, turnBudgetSeconds - elapsed) ≤ 10 s
         + apply/broadcast                       ≈ 0.05 s
         + turnDelayMs                           = 0.3 s
         --------------------------------------------------
         turnBudgetSeconds                       = 35 s   (hard ceiling per week)

20 weeks x 35.35 s = 707 s   <=  720 s budget.       Hard worst case.
20 weeks x 16.3 s  = 326 s                            Typical (Haiku ~13-16 s/batch).
pacing:  turnDelayMs = min(300, PacingBudgetMs div weeks) = min(300, 4500) = 300 ms -> 6 s total.
sprint variant: 12 weeks x 35.35 s = 424 s.
certification:  6 weeks, all seats scripted, no network -> < 1 s.
```

The retry batch is explicitly bounded by *what is left of the week's 35 s*, not by a second full
timeout — that is what keeps the per-week ceiling a real ceiling. The remaining 480 s of the 1200 s
episode covers container start, the ≤ 180 s player-connect wait, and writing results + replay.
Because the connect wait is inside the same clock (bullwhip's `gameStart` is taken before it,
`src/bullwhip/server.nim:223-256`), a pathological 180 s connect simply causes the deadline check to
end the episode a few weeks early with `reason = "deadline"` — which is the correct trade, since an
overrun episode is discarded whole.

**3. Degrade, never hang.** In order, per seat, per week:

1. The batch reply is parsed. A transport error, a non-2xx, a refusal, a `max_tokens` cut, missing
   JSON, or a **hard-invalid** decision (§Reply schema) marks the seat still-open and logs *what* the
   model actually sent (first 160 chars, newlines flattened).
2. Still-open seats go into **one** retry batch, with the hint
   `Your previous reply was invalid. Respond with ONLY the requested JSON object.` appended, bounded
   by the remaining week budget.
3. Anything still open falls back to **`scriptedDecision(sim, seat, skSentinel)`** — always legal,
   never talks, never sends aid. The `dial` event records `scripted: true` so the feed can say
   `Riverbend falls back (timeout)`.
4. Before every week's batch the server checks `epochTime() > playDeadline`; past it, `sim.endEarly()`
   settles `deadline` **between weeks**, the final frames go to the players, and results + replay are
   written. Play is never abandoned mid-week, so no half-resolved week can reach the replay.
5. A seat whose player container never connects still plays: after
   `player_connect_timeout_seconds` (180) the game starts with whoever is there, and unconnected
   seats are treated as `PLAYER_SCRIPTED=sentinel`. An episode with zero connected players still
   completes and still writes a replay — this is the offline-certification path and it is
   load-bearing.
6. `newLlmClient` with no Bedrock endpoint, no bearer token, no `ANTHROPIC_API_KEY` and no
   `ANTHROPIC_API_KEY_URI` sets `disabled = true` immediately; every seat is then scripted with no
   network waits at all.

**4. Two name spaces.** The prompts, the observation JSON and the player websocket carry only region
aliases (`Harborlea`, `Kestrel Flats`, …) and the seat→region map is re-permuted from the seed every
episode, so no prompt can ever learn "seat 3 is the champion". Real policy display names exist in
exactly three places: `results.names`, `replay.policyNames`, and the spectator/replay renderer, which
maps aliases back for the scorebug, the feed and the endscreen (bullwhip `client/renderer.js:778-810`
`makeNameMap` / `applyNames`, kept verbatim).

### The two champion prompts (both `PLAYER_PROMPT`, fielded in phase 50)

`contagion-warden` (champion #1, owner `daveey`):

> Suppress early and cheaply, then reopen. Every week convert your reported cases into a true
> estimate by dividing by the detection rate for your CURRENT testing level, and do the same for
> every other region using THEIR testing level - a neighbour reporting 400 cases at testing 0 really
> has about 2700. Buy information first: testing 2 is cheap and it both slows spread and stops you
> flying blind. Raise lockdown one step before your estimated prevalence doubles again, not after;
> hospitals overloaded means your deaths triple, and deaths cost 2 credits each. Close a road only
> against a region whose estimated prevalence is above 2%, and remember a closed road still leaks
> 12%, so closure buys time, never safety. Reopen the moment your own estimate falls under 0.5% -
> idle lockdown is pure loss. Say your real numbers out loud every week; a table that trusts your
> figures will close its own roads against the actual hotspot instead of against you. Send aid to
> whichever region is both hottest and poorest: their outbreak is arriving at your door in two weeks
> whatever your gates say, and 150 credits spent there is cheaper than a lockdown here.

`contagion-broker` (champion #2, owner `daveey-1`):

> Keep the lights on and buy your safety from other people's lockdowns. Stay at lockdown 0 or 1 while
> your own estimated prevalence is under 1%, run testing 2 so you can see trouble a week early, and
> keep your roads open to clean regions - trade you give up is never refunded. When a neighbour's
> de-biased estimate crosses 1.5%, close that one road and offer them aid, explicitly and publicly:
> tell them the amount and the lockdown level you want in return, and pay only while they hold it.
> Build a two- or three-region bloc that all lock together, because a bloc that suppresses at the
> same time ends the wave in half the weeks. If you are the one on fire, take the money, lock to 3,
> and say exactly when you will reopen so the payments continue. Never go above lockdown 3 - the last
> step costs more output than it saves lives - and never let your ledger fund aid you cannot afford.

### Scripted baselines (`PLAYER_SCRIPTED`)

Both baselines see **only what a seat sees** (reported cases and published dials, never the true
infection counts), both are deterministic, both are always legal, and neither ever talks, takes
notes, or sends aid.

- **`sentinel`** (`PLAYER_SCRIPTED=sentinel`, also accepted: `1`, `true`, `yes`) — the threshold
  dial policy, and the universal fallback move. Let
  `est = confirmed_own * 1_000_000 div DetectPpm[testing_now]` and
  `rate = est * 1_000_000 div alive_own` (ppm).
  - `lockdown`: `rate < 2_000 → 0`; `< 8_000 → 1`; `< 25_000 → 2`; `< 60_000 → 3`; else `4`.
  - `testing`: `rate < 2_000 → 1`; `< 25_000 → 2`; else `3`.
  - per road to neighbour `q`: de-bias `q`'s reported cases by `DetectPpm[testing_q]`, giving
    `rate_q`; `rate_q < 4_000 → gate 0`; `< 20_000 → gate 1`; else `gate 2`.
  - Once the variant is confirmed, every threshold is multiplied by `800_000/1_000_000` (it reacts
    one step earlier).
- **`laggard`** (`PLAYER_SCRIPTED=laggard`) — the leaky neighbour, which is the whole point of the
  game and therefore has to be in the box. `testing` is always `0` (so it both under-reports by 6.7×
  and never isolates), all gates are always `0`, and `lockdown` is `0` until its own de-biased
  estimate first crosses `40_000` ppm (4 %), then `3` for three consecutive weeks, then back to `0`
  permanently. Late, blind, and expensive for everyone downwind — exactly the pressure the other five
  seats are playing against.

---

## Sim module

`src/contagion/types.nim` — `ContagionError`, `PlayerConfig`, `GameConfig` (bullwhip's, with `weeks`,
`talk`, `turnBudgetSeconds` added and `llmTimeoutSeconds` defaulted to 25), `RegionState`,
`Decision`, `AidEntry`, `EventKind`, `GameEvent`, `defaultGameConfig`, `update`.

`src/contagion/sim.nim` — pure rules, no IO, no networking; shared verbatim by the server, the tests
and the wasm viewer (bullwhip's `src/bullwhip/sim.nim` is the exact template):

- Constants: everything in the two tables above, plus `Seats* = 6`, `Regions* = 6`, `Degree* = 3`,
  `RegionNames*`, `Edges*` (the nine `(a, b, mobility)` triples, in a fixed order),
  `NeighboursOf*[6][3]` (each region's incident edges, in a fixed order — the order the reply's
  `borders` keys and the observation's neighbour list use), `RulesVersion* = "contagion.rules.v1"`.
- `Sim*` = `config`, `names` (region alias per **seat**), `posOf[6]`, `seatOf[6]`, `outbreakPos`,
  `variantWeek`, `week`, `regions: array[6, RegionState]`, live-week `pending: array[6, bool]`,
  `pendingDecision: array[6, Decision]`, `says[6]`, `heard[6]`, `notes: seq[string]`,
  `history: seq[WeekRecord]` (one per observed week: the six region states + the six decisions),
  `weeksPlayed`, `phase` (`dials` | `done`), `done`, `reason`, `events`.
- API mirroring bullwhip one-for-one:
  `initSim(config)`, `sampleEpisode(config)` (clamps `weeks` to 4..40 and `turnDelayMs` to
  `PacingBudgetMs div weeks`, idempotent via `sampled`), `regionNames(config)`, `pendingSeats(sim)`,
  `regionOf(sim, seat)`, `score(sim, seat)`, `neighbours(pos)`,
  **`applyDecision(sim, seat, decision, scripted)`** (validates, latches; the sixth call resolves the
  week and logs the next `week` event or the `end` event; raises `ContagionError` on a hard-invalid
  decision so the server can fall back), `endEarly(sim)`, `resultsJson(sim)`, `tableStateJson(sim)`,
  `playerViewJson(sim, seat)`, `replayMatch(config, events)`, `eventToJson`, `eventFromJson`.
- `applyDecision` is the only mutation path, and **the apply order across seats cannot change the
  outcome**: it only latches, and the whole resolution runs once, from all six latched decisions.
  Seat order fixes the feed, nothing else.

### Event vocabulary written to the replay

Four kinds, a single flat `GameEvent` object, JSON via `eventToJson`/`eventFromJson` (bullwhip's
shape):

| kind | fields |
|---|---|
| `start` | none beyond `kind` (the config block carries the seed and the week count). |
| `week` | `week`, `variant` (bool, true from `variantWeek` on), `regions` — an array of six objects **in position order**, each `{susceptible, infected, recovered, dead, gdp, lockdown, testing, gates:[3], newInfections, deathsWeek, confirmed, confirmedNew, grossGdp, spendWeek, aidIn, aidOut, hospital}`. This is the **true** state — spectators see the virus, governors do not. |
| `dial` | `week`, `seat`, `pos`, `region` (alias string), `lockdown`, `testing`, `borders` — `[{"to": <region alias>, "gate": 0..2} × 3]` in the region's fixed neighbour order, `aid` — `[{"to": <alias>, "amount": int} × ≤3]` **after** validation and clamping, `say` (omitted when empty), `scripted` (bool), `corrected` (bool — a soft correction was applied), `text` (the seat's notes after this reply). |
| `end` | `week` = weeks played, `text` = the reason (`complete` \| `deadline`). |

`replayMatch(config, events)` re-derives the whole timeline: `initSim` re-draws the permutation, the
outbreak position and `variantWeek` from the seed, then each `dial` event is replayed through
`applyDecision` and each `week` event is **checked** field-for-field against the re-derivation (all
integers, so the check is exact); a mismatch raises. `frames[i]` = the state after `events[0..<i]`,
so `frames.len == events.len + 1`. A recorded `end` with `deadline` is not derivable from the dials
and is applied as `settle(text)`, exactly as bullwhip does (`src/bullwhip/sim.nim:446-448`).

### `tableStateJson` — the exact frame the viewer draws

```json
{"seats":[{"seat":0,"pos":2,"region":"Riverbend","name":"Riverbend","score":11402,
           "gdp":14402,"deaths":1500,"deathsWeek":37,"infected":8210,"confirmed":5337,
           "confirmedNew":812,"newInfections":1249,"susceptible":803110,"recovered":187180,
           "alive":998500,"lockdown":3,"testing":2,"hospital":1,
           "gates":[{"to":"Kestrel Flats","pos":1,"gate":2,"eff":2,"road":"main"},
                    {"to":"Ash Hollow","pos":3,"gate":0,"eff":1,"road":"main"},
                    {"to":"Harborlea","pos":0,"gate":0,"eff":0,"road":"back"}],
           "grossGdp":540,"spendWeek":95,"aidIn":150,"aidOut":0,
           "aid":[{"to":"Ash Hollow","amount":120}],
           "say":"holding L3 two more weeks if the money keeps coming",
           "heard":[{"region":"Harborlea","say":"…"}, …],
           "notes":"…","pending":false} × 6 by SEAT],
 "posSeat":[3,0,5,1,4,2],
 "regions":["Harborlea","Kestrel Flats","Riverbend","Ash Hollow","Wintermoor","Saltmarch"],
 "edges":[{"a":0,"b":1,"road":"main","eff":1,"flow":  8123}, … 9 entries],
 "week":7,"weeks":20,"weeksPlayed":7,"variant":false,
 "curves":{"infected":[[…] × 6 by POSITION],"deaths":[[…] × 6],"gdp":[[…] × 6]},
 "hospitalCap":25000,
 "phase":"dials|done","gameDone":false,"reason":""}
```

`edges[].flow` is that week's imported-infection contribution across the road (`Σ imp` in people),
which is what the viewer animates as the red stain crossing the border. `curves` are revealed only up
to the current week, never ahead.

### `resultsJson` — platform-facing, policy names, closed key set

```json
{"names":["daveey-warden","Baseline (1)", … 6],
 "scores":[11402, -8210, … 6 integers, higher is better, may be negative],
 "gdp":[14402, …6],  "deaths":[1500, …6],  "regions":["Riverbend", …6 aliases by seat],
 "weeks":20, "maxWeeks":20, "totalDeaths":24118, "totalGdp":61204,
 "reason":"complete"}
```

### Replay payload — `contagion.replay.v1`, self-sufficient

```json
{"protocol":"contagion.replay.v1",
 "rules":"contagion.rules.v1",
 "names":["Riverbend", …6 region aliases BY SEAT],
 "policyNames":["daveey-warden", …6 real policy display names BY SEAT],
 "config":{"weeks":20,"seed":91237,"talk":true,"sampled":true},
 "events":[…],
 "results":{…}}
```

Everything the viewer needs is in those bytes: the **seed** (which re-derives the permutation, the
outbreak position and the variant week), the **config**, the **names in both name spaces**, the
**per-tick state** (every `week` event carries all six regions in full), and the **results**. The
replay-mode server and the wasm module add a derived `"states"` array; nothing else is ever fetched
except the `.replay` file itself. `rules` lets a future viewer refuse a replay written under
different constants instead of drawing nonsense.

The replay is written as **strict UTF-8 JSON** (`SMOKE_REQUIRE_REPLAY_JSON=1` in
`tools/ci/docker_smoke.sh` parses it). Every free-text field is truncated on **rune** boundaries
before it reaches the event log, so no byte slice can leave a partial code point in the file.

---

## Server, player, protocol

`src/contagion.nim` — bullwhip's entrypoint verbatim in structure: read `COGAME_*` runtime config,
choose live vs replay mode, start the server (`src/bullwhip.nim`, 46 lines, is the template).

`src/contagion/server.nim` — bullwhip's mummy HTTP/WS server with the game loop's payload swapped:

- Wait up to `player_connect_timeout_seconds` for six sockets, then start regardless.
- Per week: snapshot the sim under the lock; decide all pending seats in **one batch outside the
  lock** (only this thread mutates the sim, so the snapshot cannot go stale); apply each decision
  under the lock, falling back to `sentinel` on a rejection; broadcast; sleep `turnDelayMs`.
- Routes, unchanged in shape: `/player` (per-seat websocket), `/global` (spectator websocket),
  `/replay`, `/client/global`, `/client/player`, `/client/replay`, `/client/renderer.js`,
  `/client/chrome.css`, `/assets/<file>`, `/healthz`.
- `finishEpisode` unchanged: final frames to the players **before** the artifacts are written (the
  hosted worker tears player pods down as soon as `results.json` exists), then results
  (`application/json`) and the replay (`application/octet-stream`), then `quit(0)`.

### The per-seat observation — exactly what is visible and what is hidden

The `state` frame a player receives, and the prompt the server builds for that seat, carry **the same
information**. Nothing the prompt sees is absent from the player frame.

**Visible to the governor of region `r`:**

- `week`, `weeks`, its own region alias, and the **whole map**: all six region names, all nine roads,
  which are main and which are back roads, and its own three neighbours in the fixed order.
- **Its own region:** `confirmed` and `confirmedNew` (its *reported* case numbers, biased by its own
  testing level), exact cumulative `deaths` and `deathsWeek`, exact `gdp` ledger, `grossGdp`,
  `spendWeek` broken into testing / own borders / neighbours' borders, `aidIn` and `aidOut` last week,
  its current `lockdown`, `testing` and three `gate` values, the **effective** gate of each of its
  roads (you can see the barrier at the far end), and a `hospital` **band** — `normal` / `strained` /
  `overloaded` / `critical` — rather than a number.
- **Every other region:** its alias, its **reported** `confirmed` and `confirmedNew`, exact
  cumulative `deaths`, its `gdp` ledger and current `score`, and its published `lockdown`, `testing`
  and gate settings on all of its roads.
- **The public aid ledger:** every transfer settled last week (`from`, `to`, `amount`) and the
  cumulative sent/received totals per region.
- **Last week's `say` from all six governors** (when `talk` is true), attributed by region alias.
- **Its own private notes**, fed back verbatim.
- **Its own 20-row history table**: week, incoming reported cases, new reported cases, deaths that
  week, lockdown, testing, gates, gross GDP, spend, net, ledger.
- **Every constant in the tables above**, printed in the system prompt — including `DetectPpm`, so a
  governor can de-bias any region's reported number by its published testing level. That inference is
  intended play, not a leak.
- `variant`: false until the week after the variant is confirmed, then true (with the note that all
  transmission rose 25 %).

**Hidden from every governor:**

- The **true** `infected`, `susceptible` and `recovered` of every region **including its own**. A
  governor only ever sees `confirmed`, and at testing 0 that is 15 % of the truth.
- Other regions' hospital bands (only your own health service reports to you).
- Other regions' private notes.
- The seeded `outbreakPos` and `variantWeek` as such (both are inferable from the numbers, which is
  the point).
- Every seat's **policy display name** — the two-name-space pin. Governors know regions, never
  players.
- Anything about a future week, and any other governor's decision for the current week.

Spectators and the replay see all of it, including true infection counts — that asymmetry is what
makes the red stain worth watching.

### Reply schema and character caps

The model answers with **one JSON object and nothing else** (system prompt demands the reply begins
with `{` — the Bedrock/Haiku prose-first gotcha from the playbook):

```json
{"lockdown": 3,
 "testing": 2,
 "borders": {"Kestrel Flats": 2, "Ash Hollow": 0},
 "aid": [{"to": "Ash Hollow", "amount": 120}],
 "say": "holding L3 two more weeks if the money keeps coming",
 "notes": "Ash Hollow reported 400 at testing 0 = ~2700 real. Paid them 120."}
```

| Field | Type | Cap / legality |
|---|---|---|
| `lockdown` | integer 0..4 | Required. Accepts an int, a numeric string, or a float (rounded), like bullwhip's `parseDecision`. Out of range or unparseable ⇒ **hard-invalid**. |
| `testing` | integer 0..3 | Required, same coercions. Out of range ⇒ **hard-invalid**. |
| `borders` | object, ≤ 3 keys | Keys are neighbour **region aliases**; values 0/1/2. Not an object ⇒ hard-invalid. Unknown key ⇒ ignored (`corrected`). Value outside 0..2 ⇒ clamped (`corrected`). **A neighbour left out keeps last week's gate** — a governor need not restate a standing closure. |
| `aid` | array, ≤ 3 entries | Not an array ⇒ hard-invalid. Each entry `{"to": <alias ≤ 24 runes>, "amount": integer ≥ 0}`. Unknown or self `to` ⇒ entry dropped (`corrected`). Negative or non-numeric amount ⇒ dropped. Entries beyond the third ⇒ dropped. Amounts clamped cumulatively so the week's total is ≤ `MaxAidPerWeek` = 200 and ≤ the sender's ledger. |
| `say` | string | **≤ 160 runes.** Longer is truncated to 159 runes + `…`. Newlines flattened to spaces. Dropped entirely when `talk` is false. |
| `notes` | string | **≤ 700 runes.** Longer is truncated to 699 runes + `…`. Never shown to any other seat; recorded in the event log and shown to spectators. |

**All truncation is on rune boundaries** (`unicode.runeLen` / `runeSubStr`, bullwhip's
`cleanText`, `src/bullwhip/llm.nim:385-390`): a byte slice through a multi-byte character would leave
invalid UTF-8 in the replay and break its JSON. Unknown top-level keys are ignored.

**Hard-invalid ⇒ retry once ⇒ `sentinel`.** **Soft corrections are accepted**, logged, and marked
`corrected: true` on the `dial` event so the feed can show `Riverbend — aid clamped to ledger`.

### Protocol `contagion.player.v1`

A policy is a prompt; the player container's only job is to deliver it. JSON text frames over
`COWORLD_PLAYER_WS_URL` (already carrying `?slot=N&token=T`).

- game → player: `{"type":"welcome","protocol":"contagion.player.v1","slot":N,"name":"<region
  alias>","pos":P,"neighbours":[…],"weeks":20}` on connect;
  `{"type":"state", …}` after every event — the per-seat view above, redacted exactly as described;
  `{"type":"final","done":true,"scores":[…],"gdp":[…],"deaths":[…],"regions":[…],"names":[6 region
  **aliases**],"weeks":N,"reason":"complete|deadline"}` at the end, after which the player exits.
- player → game: `{"type":"prompt","prompt":"<≤ 4000 chars>","scripted":"<≤ 32 chars>"}`, sent
  immediately on connect and again after `welcome` (the re-send covers the slot-registration race).
  `scripted` of `sentinel`/`1`/`true`/`yes` registers the threshold baseline, `laggard` the leaky
  one, `""` means LLM-driven.

`src/contagion_player.nim` — bullwhip's `src/bullwhip_player.nim` with a Contagion default prompt (the
`contagion-warden` text above), reading `PLAYER_PROMPT` and `PLAYER_SCRIPTED` from the environment.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` (bullwhip's,
committed mode **100755** — `coworld build` hard-requires `os.X_OK` on the hook) compiles the same
Nim sim to wasm and assembles the bundle; the browser re-derives every frame from the replay bytes
and contacts nothing but S3 for the `.replay` file.

**All four viewer files come from `cogame-bullwhip`, and from no other starter.** This is stated
explicitly because splicing one starter's shell onto another's emscripten link flags deadlocks the
viewer silently (cogame-lantern, 2026-08-23):

| File | Forked from (bullwhip) | Changes |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | Output `contagion_replay.js`; `-s MODULARIZE=1 -s EXPORT_NAME=ContagionReplayModule`; `EXPORTED_FUNCTIONS=_main,_malloc,_free,_cg_load_replay,_cg_payload_ptr,_cg_payload_len,_cg_error_ptr,_cg_error_len`. `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`, `EXPORTED_RUNTIME_METHODS=HEAPU8`, `--mm:arc --exceptions:goto -d:useMalloc` all kept — each exists because of a bug bullwhip already paid for. |
| the wasm entry `.nim` — `replay-viewer/contagion_replay.nim` | `replay-viewer/bullwhip_replay.nim` | Same 82-line shape: parse the replay JSON, rebuild `GameConfig` from `config` (+ `sampled: true`), `eventFromJson` every event, `replayMatch`, emit `{"type":"replay","protocol","rules","names","policyNames","config","events","results","states"}`. Same `emscripten_exit_with_live_runtime()` epilogue skip. Exports renamed `cg_*`. |
| `replay-viewer/static_replay.js` | `replay-viewer/static_replay.js` | Calls `ContagionReplayModule()` — the **factory promise that `config.nims` above actually exports**, which is the whole point of taking both files from one starter. Keeps the 20 s `AbortController` fetch bound, the Retry button, the `coworld-replay` postMessage bridge (`tell("loading")` on script entry, `tell("ready")` after the first drawn frame, `tell("error", msg)` on failure), and the `data-replay-error` attribute set on failure / removed on each attempt. |
| `replay-viewer/index.html` | `replay-viewer/index.html` | Same markup, same script order (`renderer.js` → `contagion_replay.js` → `static_replay.js`), same canvas-fit block, same `bindFeedToggle`. Wordmark becomes `CONTA<span>GION</span>`; `#clock` reads `WEEK 0 / 20`. |

**Readiness signals.** `document.documentElement` gets **`data-replay-loaded="true"` on the shell's
first drawn frame** and **`data-replay-error="<message>"` on failure**. One deliberate improvement
over bullwhip: bullwhip sets `data-replay-loaded` immediately after starting the rAF loop
(`client/renderer.js:1390`), which can be true before a pixel exists; Contagion moves that single
line **inside the first `frame()` iteration, after `renderer.draw(view)` returns**, so the attribute
means a picture. `tools/ci/viewer_smoke.mjs` polls exactly this attribute (and the bridge's `ready`),
and treats `data-replay-error` as an immediate failure.

**Bundle contents** (every file must return 200 with a non-trivial size): `index.html`,
`static_replay.js`, `renderer.js`, `chrome.css`, `contagion_replay.js`, `contagion_replay.wasm`, and
`assets/` — `map_board.png`, `region_tile.png`, `shutter.png`, `gate_arm.png`, `aid_packet.png`,
`governor_red_front.png`, `governor_blue_front.png`, `governor_green_front.png`,
`governor_yellow_front.png`, `governor_violet_front.png`, `governor_orange_front.png`, `font.ttf`.

**Chrome kept verbatim.** `client/chrome.css` is bullwhip's file with **two additions and nothing
else**: `.seat5 { --tc: var(--orange); }` (bullwhip stops at `.seat4`, `client/chrome.css:205-209`,
and `renderer.js`'s `COLORS` array already has six entries, `client/renderer.js:29`), and
`#scorebug { grid-template-columns: repeat(6, 1fr); }` with `repeat(3, 1fr)` at `max-width: 640px`
and `repeat(2, 1fr)` at `max-width: 420px`. The `.plate-backlog` rule is renamed `.plate-dead`
(red, uppercase, `flex: none`) and carries the death count. Every id and class is kept: `#layout`,
`#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`, `#feedtoggle`, `#scorebug`,
`#board-wrap`, `#table`, `#lightpool`, `#grain`, `#endscreen`, `#transport`, `#scrub`, `#play`,
`#pos`, `#feed`, `#loading`, `.plate`, `.plate-name`, `.plate-score`, `.plate-label`, `.plate-pip`,
`.plate-it`, `.scrub-track`, `.scrub-fill`, `.scrub-head`, `.beat-marker`, `.round-span`,
`.round-sep`, `.feed-turn`, `.feed-turn-head`, `.feed-line`, `.feed-say`, `.feed-end`,
`.feed-death`, `.feed-notes`, `.feed-week`, `.feed-future`, `.seat0`…`.seat5`.
`client/renderer.js` keeps its whole chrome half unchanged — `makeNameMap`, `applyNames`,
`clampName`, `renderFeed`, `bindFeedToggle`, `makeEffects`, `matchHeader`, `updateScorebug`,
`updateEndscreen`, `buildScrub`, `attachLive`, `attachReplay`, the drivers and the replay pacing —
and replaces only the canvas scene (`draw`, `computeLayout` and the bullwhip conveyor helpers).

### What the viewer draws — the readouts

1. **The map.** The six regions sit at the vertices of a hexagon on an authored painted map plate
   (`map_board.png`), with the nine roads drawn between them: the six ring roads thick, the three
   back roads thin. Each region is a painted tile with its **name**, its governor portrait in the
   seat colour, and its two tickers.
2. **The outbreak is an animated red stain.** Each region's tile is washed with a red stain whose
   coverage and opacity track *true* prevalence (`infected / alive`), rendered as an organic blotch
   that grows and recedes between weeks. On every road, `edges[].flow` drives a **crawling red seep**
   from the hotter end toward the colder one, thickness proportional to the imported case count. A
   road that is shut and still seeping — the leak — is drawn as red beading *through* a closed
   barrier, which is the single most important picture in the game.
3. **Shutters slam.** `lockdown` is drawn as 0–4 wooden shutters descending over a region's tile;
   a change from level `a` to `b` animates the shutters slamming down (or rolling up) over 500 ms with
   a dust puff. Level 4 is a fully boarded tile. **`testing` is a lantern** on the tile: dark at 0,
   brightening through 3, and its glow is literally how far into that region a spectator can see
   the reported-vs-true gap (§7).
4. **Gates.** Each road carries a barrier arm at each end: raised (open), striped/half (screened),
   dropped and chained (closed). The **effective** gate — the tighter of the two — is what the seep
   animation obeys, and the tighter end's arm is drawn solid while the looser end's is drawn ghosted,
   so "who paid for this closure" is visible at a glance.
5. **Aid arcs as gold packets.** Every settled transfer flies a gold packet along a bezier from the
   sender's tile to the recipient's over 700 ms, with the amount stamped on it, and both ledgers tick
   as it lands. Three packets in one week from three regions to one is the coalition, drawn.
6. **Tickers.** Every tile shows `GDP 14,402` and `DEAD 1,500` in the seat colour, and the death
   ticker flashes red and bumps scale on any week with `deathsWeek > 0`. The **scorebug**
   (`#scorebug`, six plates, seat colours, real player names) shows `name · SCORE · DEAD`, leader
   plate brightened.
7. **The epi strip** under the map replaces bullwhip's seismograph: six seat-coloured curves of
   **true** infections per week with the `HospitalCap` line drawn as a ghost across it, and — this is
   the joke the game is built on — each region's **reported** curve drawn as a dotted line under its
   true one. When a `laggard` region runs testing 0 you can watch the dotted line stay flat while the
   solid one goes vertical.
8. **Clock and status.** `#clock` reads `WEEK 7 / 20`; `#statuschip` reads `replay` or `live`;
   `matchHeader` appends `WAITING ON 2` / `DIALS IN` / `FINAL`. From `variantWeek` a persistent
   `VARIANT +25%` chip sits beside the clock.
9. **Feed** (`#feed`, plain language, one block per week, spectator names): `WEEK 7` heads the block,
   then `Riverbend — lockdown 3, testing 2, closes Kestrel Flats`,
   `Riverbend says: "holding L3 two more weeks if the money keeps coming"`,
   `Harborlea sends 150 to Riverbend`, `Ash Hollow — 412 dead this week, hospitals CRITICAL`,
   `Saltmarch falls back (timeout)`, `Riverbend — aid clamped to ledger`, and
   `Final — Wintermoor 14,208 (1,207 dead)`.
10. **Transport, verbatim from bullwhip:** the scrubber with a per-week `.round-span` block, a
    `.beat-marker` per `dial` event in the seat colour and a `.death` marker at the end, click and
    drag seek, play/pause, `pos` readout, and the collapsible feed toggle. Playback pacing keeps
    bullwhip's event-kind timing (a `dial` with a `say` holds longer than one without).
11. **Endscreen:** ranked rows with columns `SCORE`, `GDP`, `DEAD`, `REGION`, spectator names,
    verdict = the top scorer + `KEPT THE LIGHTS ON`, and, when `reason == "deadline"`,
    `episode deadline: scored on 14 of 20 weeks`.

**Real art, not placeholders.** `data/map_board.png` is an authored painted parchment map with the
six region plates and the nine roads inked on it; `region_tile.png`, `shutter.png`, `gate_arm.png`
and `aid_packet.png` are authored props in the same Ink-&-Print palette as bullwhip's chrome
(`#f2e8d8` paper, `#2a1f16` ink, `#e8a33d` amber). The six governor portraits are the four
coworld-ctf soldier sprites bullwhip already ships (`data/soldier_{red,blue,green,yellow}_front.png`,
MIT) plus two recolours (violet, orange) produced by a committed `scripts/art/recolor_sprite.py`;
`data/font.ttf` and `data/FONT_LICENSE.txt` are carried over unchanged. No solid-colour rectangle
stands in for anything.

**Legible at 360 px.** The embedded featured-match iframe on softmax.com is ≈ 360 px wide, so the
composition is designed and checked at that width, not at desktop width. Bullwhip's `@media
(max-width: 640px)` and `@media (max-width: 420px)` blocks are inherited, and on top of them:
`#scorebug` goes to two columns × three rows; `.plate-label` (the region word) is hidden and
`.plate-dead` is kept, because the death count is the drama; `.plate-name` keeps
`min-width: 3.2em; flex: 1 1 auto; overflow: hidden; text-overflow: ellipsis` so a player name never
collapses to `…` (playbook gotcha); the map's region labels drop to the first word
(`Kestrel Flats` → `Kestrel`); the epi strip collapses to true-infection curves only, no dotted
reported lines; the feed collapses under the board to three lines; and every canvas label is drawn at
`max(9, 11 * scale)` px, where `scale = min(width/960, height/640)`. A static test asserts the
`.plate-name` rule and both media blocks survive any future edit (§Tests).

---

## Packaging

- **Repo:** `Metta-AI/cogame-contagion`, **created public** (a certification prerequisite —
  `source-resolves` 404s on private). Slug `contagion`.
- **`compose.yaml`** — bullwhip's shape exactly; the manifest's image placeholder is derived from the
  **compose service name** (`service contagion` → `{{CONTAGION_IMAGE}}`; `{{GAME_IMAGE}}` is not a
  thing — playbook gotcha, lantern 0.1.0):

  ```yaml
  services:
    contagion:
      image: coworld-contagion:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — bullwhip's two-stage build verbatim in structure: `debian:bookworm-slim`,
  nimby 0.1.26 (arch-switched download), `nimby use 2.2.4`, `nimby --global sync nimby.lock`,
  regenerate `nim.cfg` from the container's package tree, then two binaries with
  `-d:release -d:useMalloc --opt:speed --stackTrace:on` — `/bin/contagion` from `src/contagion.nim`
  and `/bin/contagion-player` from `src/contagion_player.nim`. Run stage `debian:bookworm-slim` with
  `ca-certificates` + `libcurl4`, copying both binaries, `./data` and `./client`.
  `CMD ["/bin/contagion"]`.
- **`Dockerfile.replay-viewer`** — bullwhip's verbatim with the file names changed:
  `emscripten/emsdk:4.0.15`, nimby 0.1.27, `nimby use 2.2.4`,
  `nim c --hints:off -d:emscripten replay-viewer/contagion_replay.nim`,
  `test -s replay-viewer/dist/contagion_replay.wasm`.
- **`tools/build_replay_viewer.sh`** — bullwhip's verbatim with the names changed; asserts the output
  dir is absolute, builds locally when `emcc` and `nim` are both present else via the pinned emsdk
  container, copies `contagion_replay.{js,wasm}`, `index.html`, `static_replay.js`,
  `client/renderer.js`, `client/chrome.css` and the twelve assets, then
  `test -f "${output_dir}/index.html"` and `grep -q 'data-replay' static_replay.js`. Committed
  **mode 100755**.
- **`contagion.nimble`** — `requires "nim >= 2.2.4"`, `bitworld >= 0.1.0`, `mummy >= 0.4.7`,
  `curly >= 1.1.1`, `whisky`; `nimby.lock` copied from bullwhip.
- **`coworld_manifest_template.json`:**
  - `game.name` `contagion`; `game.runnable.image` `{{CONTAGION_IMAGE}}`, `run` `["/bin/contagion"]`,
    `env.ANTHROPIC_API_KEY_URI` `secret://coworld/contagion/anthropic_api_key`, `source_url`
    `https://github.com/Metta-AI/cogame-contagion/tree/main`; `owner` `daveey@gmail.com`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `tags`: `epidemiology`, `mixed-motive`, `externalities`, `negotiation`, `aid`, `llm-driven`,
    `turn-based`, `six-player`, `economics`.
  - `game.config_schema` (`additionalProperties: false`, required `tokens` + `players`):
    `tokens` (6..6), `players` (6..6 objects with `name`), **`num_agents`** (integer,
    `minimum: 6, maximum: 6`), `seed`, `weeks` (4..40, default 20), `talk` (bool, default true),
    `episodeTimeoutSeconds` (60..6000, default 1200), `turnBudgetSeconds` (5..120, default 35),
    `turnDelayMs` (0..10000, default 300), `model` (default `claude-sonnet-5`), `maxOutputTokens`
    (64..2000, default 900), `llmTimeoutSeconds` (5..300, default 25),
    `player_connect_timeout_seconds` (default 180). The epidemiology and economy constants are
    **not** configurable: they are compile-time in `sim.nim` under `RulesVersion`, so every league
    episode is comparable and the wasm viewer needs nothing but the seed to re-derive.
  - `game.results_schema`: the closed key set from §Sim module — `names`, `scores` (6 numbers, **no
    `maximum`**), `gdp`, `deaths`, `regions`, `weeks`, `maxWeeks`, `totalDeaths`, `totalGdp`,
    `reason` with `"enum": ["complete", "deadline"]`. All six arrays `minItems: 6, maxItems: 6`.
  - **`game.protocols` — both `player` and `global`**, each `{"type": "text", "value": "…"}` (text,
    never a URI, or the docs go missing on the coworld page): `player` = the
    `contagion.player.v1` text from §Server (welcome / state / final frames, the redaction rule, the
    `prompt` frame with its 4000-char cap and the `scripted` values); `global` = the `/global`
    snapshot shape (`tableStateJson` above), the position/region mapping, the nine edges, the
    append-only `events` array, and a pointer to `/client/global`, `/client/replay` and the static
    bundle (`index.html?replay=<url>`).
  - **`game.docs`**: `readme` = `{"type": "text", "value": "<README body inlined>"}`; `pages` = two
    entries — `{"id": "rules.md", "title": "rules.md", "content": {"type":"text","value": "<the full
    rules: the map, the dials, the eight numbered resolution steps, both constant tables, the
    observation redaction, the reply schema with its caps, the scoring formula and the two
    endings>"}}` and `{"id": "protocol.md", "title": "protocol.md", "content": {"type":"text",
    "value": "<the player and global wire protocols, the replay payload, and how to field a policy
    with PLAYER_PROMPT>"}}`. A test asserts all three values are non-empty.
  - **`game.player` runnables** (one image, `run: ["/bin/contagion-player"]`, `resources.requests`
    `cpu 100m` / `memory 64Mi`, `limits.cpu 1`, same `source_url`):
    `contagion-player` (the prompt player, no env — carries the default prompt),
    `contagion-sentinel` (`env.PLAYER_SCRIPTED = "sentinel"`),
    `contagion-laggard` (`env.PLAYER_SCRIPTED = "laggard"`).
  - **Variants — `num_agents` is 6 in every one:**

    | id | name | `num_agents` | `weeks` | `talk` | `turnDelayMs` | worst-case play |
    |---|---|---|---|---|---|---|
    | `standard` | Standard outbreak (six governors, 20 weeks) | **6** | 20 | true | 300 | 707 s |
    | `sprint` | Sprint outbreak (six governors, 12 weeks) | **6** | 12 | true | 200 | 424 s |

    Both list six `players` entries (`Player1`…`Player6`) and
    `player_connect_timeout_seconds: 180`. `sprint` exists for cheap ladder rounds; it changes the
    length only — **never the seat count**.
  - **Certification fixture** (`certification`):
    `game_config` = `{"players": [{"name":"Sprocket"},{"name":"Gizmo"},{"name":"Ratchet"},
    {"name":"Widget"},{"name":"Bolt"},{"name":"Piston"}], "num_agents": 6, "seed": 7, "weeks": 6,
    "talk": true, "turnDelayMs": 0, "player_connect_timeout_seconds": 180}`;
    `players` = `[{"player_id":"contagion-sentinel"} × 3, {"player_id":"contagion-laggard"} × 3]` —
    six seats, all scripted, no LLM, sub-second. (`variantWeek` ∈ 8..12 never arrives in a six-week
    episode; that is intentional — certification exercises the base rules.)
- **Scaffold from `coworld-builder/templates/`** with `<slug>` = `contagion`, `<IMAGE>` =
  `coworld-contagion`, `<SEATS>` = **6**: `.github/workflows/{ci.yml,coworld-release.yml,
  coworld-submit.yml}`, `tools/ci/docker_smoke.sh` (committed **100755**), `tools/ci/viewer_smoke.mjs`
  (verbatim), `tools/ci/policies.json`. `SMOKE_REQUIRE_REPLAY_JSON` stays `1`; `SMOKE_SEATS` is `6`
  and is an independent second declaration of the seat count, cross-checked against
  `certification.game_config.num_agents` (a mismatch prints `SEAT-COUNT FAIL:`).
- **`tools/ci/policies.json`** — all four `"run": "/bin/contagion-player"`, one image, env-switched:

  | name | env | role |
  |---|---|---|
  | `contagion-warden` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `contagion-broker` | `PLAYER_PROMPT` = champion #2 prompt, uploaded while `daveey-1` is active | champion #2, owner daveey-1 |
  | `contagion-sentinel` | `PLAYER_SCRIPTED=sentinel` | filler |
  | `contagion-laggard` | `PLAYER_SCRIPTED=laggard` | filler |

- **Repo layout:** `src/contagion.nim`, `src/contagion_player.nim`,
  `src/contagion/{types,sim,llm,server}.nim`, `replay-viewer/{contagion_replay.nim,config.nims,
  static_replay.js,index.html}`, `client/{renderer.js,chrome.css,global.html,player.html,
  replay.html}`, `data/`, `tests/`, `tools/`, `scripts/art/`, `docs/plans/`, `README.md`,
  `nimby.lock`, `contagion.nimble`, `Dockerfile`, `Dockerfile.replay-viewer`, `compose.yaml`,
  `coworld_manifest_template.json`.

---

## Tests

CI is the only harness — the sandbox has no Docker, no Nim and no emsdk. The template `ci.yml` runs
**every `tests/*.nim` individually, twice (debug and `-d:release`)**, so each test file is a
standalone program; shared helpers live in `tests/support/helpers.nim` (a subdirectory, so the
`tests/*.nim` glob never executes a helper).

1. **`tests/test_sim.nim` — sim unit tests.**
   - The graph: nine edges, every region degree 3 with exactly two main roads and one back road; the
     adjacency is symmetric; `NeighboursOf` is a fixed total order.
   - Seeded setup: the seat→position map is a permutation (a bijection) and is stable for a given
     seed and different for different seeds; `outbreakPos ∈ 0..5`; `variantWeek ∈ 8..12`; initial
     compartments sum to `Pop` in every region.
   - **Resolution arithmetic on a hand-computed week**: a fixture with pinned dials and pinned
     compartments, with `local`, `pass`, `imp`, `force`, `newInfections`, `resolved`, `ifr`,
     `deathsWeek`, `grossGdp`, `spendWeek` each asserted against numbers computed by hand in the
     test's comments. Integer arithmetic makes these exact equalities, not tolerances.
   - The leak: with both ends closed, `pass == LeakPpm` (120 000) exactly, and a region bordering a
     20 %-prevalence neighbour still gains a strictly positive `newInfections` — the idea's central
     rule, asserted.
   - `eff(e) == max(gate[a], gate[b])`; the tighter end governs and the looser end's setting cannot
     re-open the road.
   - Spillover cost: a region pays `BorderNeighbourCost` for a road **its neighbour** closed.
   - Aid: total per sender clamped to `min(200, ledger)`; a sender cannot forward aid received the
     same week; entries beyond the third dropped; self-aid dropped; the six ledgers' sum is invariant
     under any aid pattern.
   - Overload: `ifr` at `infected == HospitalCap` equals `BaseIfrPpm`; at `4 × HospitalCap` it is
     capped at `4 × BaseIfrPpm`.
   - Scoring: `score == gdp − 2 × dead`, sign asserted both ways (a devastated region scores
     negative, a clean one positive); `resultsJson` key set is exactly the schema's.
   - Simultaneity: applying the six decisions in a shuffled seat order produces a byte-identical
     `tableStateJson` — the apply order cannot change the outcome.
   - Endings: `weeks` weeks → `reason == "complete"`; `endEarly()` mid-episode → `"deadline"` with
     `weeks < maxWeeks`; no other reason is reachable.
   - Determinism: two `initSim` runs on the same seed, driven by the same decisions, produce
     identical event logs.
   - `replayMatch`: `frames.len == events.len + 1`, the final frame equals the live
     `tableStateJson`, and a **corrupted** `week` event raises `ContagionError`.
   - `eventToJson`/`eventFromJson` round-trip for all four kinds, including a `dial` with three
     border entries, three aid entries, a 160-rune `say` and a 700-rune `notes`.
2. **`tests/test_bot.nim` — bounded-orders / legality assertion on the scripted baselines.**
   - Six `sentinel` seats, and six `laggard` seats, and a 3/3 mix, each play full episodes for seeds
     `[1, 7, 42, 1234]` **without `applyDecision` ever raising** — i.e. every dial the baselines
     emit is in range, every gate key names a real neighbour, aid is empty, `say` and `notes` are
     empty, and no ledger goes negative through aid.
   - Both baselines are pure functions of the seat's *observable* view: a test feeds two sims that
     differ only in hidden true-infection counts (same reported numbers) and asserts the baselines
     emit identical decisions. This is what stops a baseline cheating.
   - The game rewards suppression: a six-`laggard` episode records strictly more total deaths and a
     strictly lower mean score than a six-`sentinel` episode, on every one of the four seeds.
   - Runtime: a 40-week six-seat scripted episode resolves in under 50 ms (the offline-certification
     path must never be the slow thing).
   - Reply parsing: `parseDecision` accepts int / numeric-string / float `lockdown`; rejects 5, −1
     and `"soon"` as hard-invalid; ignores an unknown `borders` key with `corrected = true`; clamps a
     gate of 7 to 2; drops a self-aid entry; truncates a 400-rune `say` to 160 runes; and
     `decideAll` with a disabled client returns `sentinel` moves for all six seats with no network
     call.
3. **`tests/test_replay.nim` — strict UTF-8 replay parse.**
   - Build a full replay payload whose `say` and `notes` contain 4-byte emoji and combining marks and
     are exactly at the cap, serialise it, and assert `unicode.validateUtf8(bytes) == -1` (no invalid
     sequence anywhere) and that `parseJson` round-trips it byte-stable.
   - Truncation lands on a rune boundary: a `say` cut at the cap mid-emoji never produces a partial
     code point.
   - Feed the bytes through the wasm module's Nim path (`replayMatch` + `states`) and assert
     `states.len == events.len + 1` and that `states[^1]` equals the live final frame.
   - Assert the payload carries every field the viewer needs: `protocol`, `rules`, `names`,
     `policyNames`, `config.seed`, `config.weeks`, `config.talk`, `config.sampled`, a `week` event
     for every played week, and `results`.
4. **`tests/test_manifest.nim` — packaging invariants.** Parse
   `coworld_manifest_template.json` and assert: `game.replay_viewer.bundle == "static-replay-viewer"`;
   **`num_agents == 6` in every `variants[].game_config` and in `certification.game_config`**;
   `tokens`/`players` bounds are 6..6; `game.protocols` has **both** `player` and `global`, each a
   non-empty `type: "text"` value; `game.docs.readme` and both `game.docs.pages[]` values are
   non-empty text; `results_schema.properties.reason.enum == ["complete","deadline"]`;
   `results_schema.properties.scores` has no `maximum`; and the certification `players` list has six
   entries all referencing declared `game.player` ids. Also greps `client/chrome.css` for the
   `.plate-name { … min-width: 3.2em … }` rule and for both the `640px` and `420px` media blocks
   (the 360 px legibility guard).
5. **End-to-end episode writing a replay — `tools/ci/docker_smoke.sh`, run by `ci.yml`'s
   `docker-smoke` job.** Builds the production image, brings up the game plus **six** player
   containers from that one image on a raw docker network with the certification fixture's seat mix,
   waits for the episode, and asserts results and a replay were written. `SMOKE_SEATS=6` is checked
   against the manifest's `num_agents`. `SMOKE_REQUIRE_REPLAY_JSON=1` makes the smoke parse the
   replay as strict JSON. The replay is copied to `dist/smoke/replay.json` and uploaded as the
   `smoke-replay` artifact.
6. **Viewer smoke — `tools/ci/viewer_smoke.mjs`, run by `ci.yml`'s `wasm-viewer` job, `needs:
   docker-smoke`.** The job asserts `tools/build_replay_viewer.sh` and `tools/ci/viewer_smoke.mjs`
   exist and that the hook is mode 100755, builds the bundle into `dist/static-replay-viewer`,
   asserts `index.html` and a non-empty `.wasm` are present, downloads the `smoke-replay` artifact,
   installs Playwright 1.55.0 + chromium, and then **executes the bundle in headless chromium against
   the replay `docker-smoke` actually produced** — `node tools/ci/viewer_smoke.mjs --bundle
   dist/static-replay-viewer --replay dist/smoke/replay.json --timeout 90`. It passes only on
   `data-replay-loaded="true"` (or the `coworld-replay` `ready` bridge message) with no
   `data-replay-error` and no post-load exception; `viewer-smoke.png` and `viewer-smoke.json` are
   uploaded on every run. **The bundle is executed, not merely built** — a viewer that deadlocks
   silently (cogame-lantern, 2026-08-23) is exactly what this catches.

---

## Out of scope (v1)

- **Vaccines, treatments and variants beyond the single seeded 25 % transmissibility step.** One
  hidden shock is enough adaptivity for v1; a vaccine race is a second game.
- **Stochastic epidemiology.** The rules are deterministic integer arithmetic on purpose: it is what
  makes the wasm re-derivation bit-exact and the replay bytes self-sufficient. Noise, if ever, comes
  as a seeded integer stream in v0.2.
- **Enforceable contracts.** Aid is settled immediately and unconditionally; there is no escrow, no
  conditional payment and no way to bind a governor to the lockdown they promised. Promises are
  cheap talk, which is the interesting version.
- **Age structure, care homes, ICU triage, super-spreader events, seasonality, waning immunity and
  reinfection.** One SIR-with-mitigation compartment set per region.
- **A changing graph.** The nine roads and their mobility weights are fixed for the episode; no new
  routes, no air travel, no smuggling channel that reroutes around a closed border.
- **Unequal regions.** Populations, `BaseGdp` and hospital capacity are identical across the six
  seats. Asymmetric regions (a rich port, a poor interior) are a v0.2 variant, not a v1 rule.
- **A raw numeric/RL policy interface.** The idea pins the parley LLM-prompt stack; exposing the
  dial vector to an external RL policy is a protocol addition later.
- **Cross-episode memory.** Notes live inside one episode; nothing carries between episodes.
- **More or fewer than six seats.** `num_agents` is 6 everywhere, full stop; the map is built for six
  and the vertex-transitivity argument only holds at six.
