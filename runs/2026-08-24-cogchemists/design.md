# Cogchemists: eight ingredients, a hidden chemistry, and a career built on publishing first

Four cogs share one laboratory for six rounds. Behind the game sits a secret bijection from the
eight ingredients to the eight alchemical **signatures**; mixing any two ingredients yields a potion
whose colour and sign leak exactly one constraint about that bijection. Experiments are private, the
ingredients you burn to run them are public, and every publication is a wax seal on a board that
anybody may attack. A seat scores **reputation** — earned by publishing theories, selling the potion
an adventurer asked for, and burning a rival's false seal in a public demonstration; lost by being
poisoned, by a failed attack, and above all by a seal the final exhibition proves wrong. The game is
a race between certainty and credit: the cog who waits until it *knows* publishes last and gets
debunked by nobody, and the cog who publishes on a hunch is one demonstration away from ruin.

Built on **`Metta-AI/cogame-bullwhip`** (mounted read-only at `/workspace/starters/cogame-bullwhip`),
the newest parley-lineage template: a Nim game server implementing the Coworld runtime contract, a
pure `sim` module shared by server / tests / wasm viewer, LLM decisions where **a policy is just a
prompt**, always-available scripted baselines, **one parallel LLM batch per simultaneous turn**, and
the parley broadcast chrome around a canvas stage. Bullwhip is the starter because Cogchemists has
bullwhip's shape exactly: a turn-based, hidden-information, simultaneous-decision, mixed-motive game
whose seats answer with a small JSON payload plus free text, whose watchability is a stage +
scorebug + feed rather than a physics loop, and whose per-turn cost is one batched LLM round trip.
Bullwhip is also the only starter whose `decideAll` already fires one parallel `curly.makeRequests`
batch per turn (the whole timing model here) and the only one whose
`tableStateJson` → `replayMatch` → wasm pipeline already re-derives every spectator frame from the
seed plus the recorded decisions — which is precisely what the hole-cam deduction grids need.
**Every convention there holds here unless this note says otherwise.**

Source idea, verbatim:

> 22 Cogchemists (Alchemists) — eight ingredients, a hidden chemistry, and a career built on
> publishing before you're sure
>
> A port of Matus Kotry's Alchemists. Each episode the server draws a secret mapping from eight
> ingredients to alchemical signatures; mixing two ingredients yields a potion whose colour and sign
> leak one constraint about the truth. Over six rounds, 2-4 cogs place workers to forage, mix
> (testing on a student for coin, or on themselves at a cost), sell potions to adventurers who demand
> a specific result, PUBLISH theories about an ingredient for reputation and royalties, endorse or
> DEBUNK rivals' theories, and buy artifacts. Reputation converts to points at the end; a published
> theory that the final exhibition proves wrong costs you dearly. The social texture is scientific:
> private experiments, public claims, strategic early publication to claim credit, and debunking as
> an attack.
>
> Seats: 2-4
> Motive: competitive, with a shared public record
> Policy interface: LLM prompt (parley stack) — deduction state passed structured
> Fills gap: logical deduction under noise / publish-early vs publish-right / reputation economy
> (tabletop cousin of Eleusis, with worker placement and a real debunk mechanic)
> Integrity (anti-collusion): The hidden chemistry is re-randomized per episode by design (the game's
> own mechanic, not a patch); experiments are private, publications in-band; cross-author seating,
> anonymous aliases.
>
> Replay plan (watchability): The lab table is the stage: mixes bubble and resolve into a potion
> flask with a colour-and-sign reveal; each cog's private deduction grid is shown to spectators like
> a hole-cam, so the audience sees who actually knows and who is bluffing a theory. Published
> theories pin to a board with wax seals; a successful debunk rings a gong and burns the seal; the
> endcard reveals the true chemistry over everyone's grid.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

*Coordinator rails, not revisited: the starter is `Metta-AI/cogame-bullwhip`; the seat count is
**4** (the idea says 2–4, we pin 4). Everything else the idea left loose — the exact chemistry
algebra, the action menu, the costs and rewards, the round count, the debunk mechanism, the viewer
composition — is a rail (parameter tuning, scoring where the idea pins the shape, viewer
composition) and is **decided below with its reason**. There is no `OPEN` item in this note.*

---

## The game

### Seats

- **Seats: exactly 4.** `num_agents` = **4** everywhere — both manifest variants, the certification
  fixture, and `<SEATS>` in `tools/ci/docker_smoke.sh`. Four is the top of the idea's 2–4 band; it
  gives two champions plus two scripted fillers in one episode, which is the league shape the
  playbook's phase 4 needs.
- Seats play under **anonymous cog aliases** drawn from the seed (bullwhip's `CogNames` /
  `tableNames`, unchanged): `Sprocket`, `Gizmo`, `Ratchet`, `Widget`, `Bolt`, `Piston`, `Flywheel`,
  `Rivet`, `Tinker`, `Gasket`.

### The eight ingredients

Fixed names, index 0..7, identical every episode (only the *chemistry* is secret):

| # | Ingredient | # | Ingredient |
|---|---|---|---|
| 0 | Nightcap | 4 | Copper Fern |
| 1 | Emberroot | 5 | Gravebloom |
| 2 | Fen Lily | 6 | Sunmoss |
| 3 | Widow's Salt | 7 | Rime Thistle |

Ingredient *identity* is never hidden: a card in a hand, on the bench, or in a demonstration is
always named. What is hidden is what it *is*.

### The hidden chemistry

- A **signature** is a triple of signs over three aspects in the fixed order RED, GREEN, BLUE, each
  `+` or `-`. There are exactly 8 signatures; written `R+G-B+` (ASCII hyphen-minus, never U+2212 —
  the string goes into prompts, the replay and the viewer).
- The episode's **chemistry** is a **bijection** ingredient → signature: a seeded permutation of the
  8 signatures, so every signature is used exactly once. 8! = **40 320** possible chemistries, drawn
  fresh from the episode seed. This is the idea's anti-collusion pin, and it is the game's own
  mechanic: nothing carries over between episodes because there is nothing to carry.
- No seat ever sees the chemistry. Spectators do not see it either until the exhibition; the replay
  bytes carry it (`config.chemistry`) so the endcard can reveal it over everyone's grid.

### Potions and the mixing rule

Mixing two **distinct-in-hand** ingredient cards `a` and `b` with signatures `sa`, `sb`:

1. Let `opp` = the set of aspects where `sa` and `sb` **disagree**. Because the chemistry is a
   bijection, two different ingredients never share a signature, so `|opp| ∈ {1, 2, 3}`. (Two cards
   of the *same* ingredient always give MUD; see rule 4.)
2. **`|opp| == 1`** — the potion takes the **colour** of that one disagreeing aspect (RED, GREEN or
   BLUE). Its **sign** is the **product of the two aspects they agree on**: `+` when those two
   agreeing aspects point the same way (both `+` or both `-`), `-` when they point opposite ways.
   The rule is symmetric in `a` and `b`, so mix order never matters.
3. **`|opp| ∈ {2, 3}`** — the potion is **MUD**: no colour, no sign.
4. Mixing an ingredient with a second card of the **same** ingredient gives **MUD** (identical
   signatures, `|opp| == 0`), and is legal.

Worked examples (these exact five are a unit test):

| `sa` | `sb` | disagree on | agree on | potion |
|---|---|---|---|---|
| `R+G+B+` | `R+G+B-` | BLUE | `R+`,`G+` → `+` | **BLUE+** |
| `R+G+B+` | `R+G-B+` | GREEN | `R+`,`B+` → `+` | **GREEN+** |
| `R+G-B+` | `R-G-B+` | RED | `G-`,`B+` → `-` | **RED-** |
| `R+G-B-` | `R-G-B-` | RED | `G-`,`B-` → `+` | **RED+** |
| `R+G+B+` | `R-G-B-` | all three | — | **MUD** |

Over the 28 unordered signature pairs the outcome vocabulary is exactly seven values —
`RED+`, `RED-`, `GREEN+`, `GREEN-`, `BLUE+`, `BLUE-`, `MUD` — and it is perfectly balanced:
**each coloured potion is produced by exactly 2 of the 28 pairs**, MUD by the other 16. A coloured
result is therefore a very strong constraint (it names the pair of signatures up to two candidates)
and MUD is a weak one — which is the whole reason a seat has to choose its experiments well.

### Rounds, phases, and the exact resolution order

The episode is `rounds` rounds (default **6**, min 3, max 10; certification fixture 4). Each round
has **two simultaneous-decision phases**: **LAB** (private science) then **MARKET** (public career).
Both phases take exactly one action per seat, decided simultaneously and resolved in **initiative
order** `order[i] = (i + round) mod 4`, so the lead rotates and no seat is structurally first.

Numbered resolution, exactly as the sim executes it:

1. **Round open** (`round` event). The **adventurer demand** for this round is drawn from the seed
   and published: one of the six coloured potions (never MUD). Then **royalties** are paid: every
   *standing* seal earns its author **+1 coin** (**+2** if the author owns the Printing Press). The
   initiative order for the round is computed and published.
2. **LAB phase opens** (`phase` event, `phase: "lab"`). Every seat's **deduction grid is recomputed**
   from the facts it knows as of this instant (see *The deduction grid*), and each seat's
   observation is built. All four seats' decisions go out as **one parallel LLM batch**.
3. **LAB resolution.** The four returned actions are applied **in initiative order**, one at a time,
   under the state lock; each produces one `act` event. Lab actions (below) never contend for a
   shared resource, but the order is still fixed so replay is exact.
4. **MARKET phase opens** (`phase` event, `phase: "market"`). Grids are recomputed again — a seat
   sees the public consequences of this round's lab phase (which cards each rival burned, and the
   sign leak of anyone who drank) before it commits its public move. One parallel LLM batch.
5. **MARKET resolution**, in the same initiative order, one `act` event per seat. This is where
   contention lives: an action that was legal when the phase opened may be **rejected** by an
   earlier seat's action in the same phase (two seats publishing on one ingredient, a debunk of a
   seal that has just burned). A rejected action is recorded with `result: "rejected:<reason>"` and
   **degrades to `pass`** (the actor still takes the +1 coin stipend). This is stated in the prompt.
6. **Round close.** If `round + 1 < rounds`, go to 1 with `round + 1`. Otherwise go to 7.
7. **The exhibition** (`exhibition` event). Every **standing** seal is opened against the truth:
   a **true** theory pays its author **+5 reputation** and each of its endorsers **+2**; a **false**
   theory costs its author **−6 reputation** and each endorser **−3**. Seals already burned by a
   debunk are *not* re-scored (they settled at the burn). The event carries the **whole true
   chemistry**, which is what the endcard draws over the grids.
8. **End** (`end` event) with `reason` = `complete`.

Nothing else happens between phases: there is no worker-placement board and no turn order to bid
for. (Decision, logged: Alchemists' worker placement is contention *machinery* for a physical table;
here the same tension — who gets to claim an ingredient first, who gets to attack a seal before it
is defended — is carried by initiative order plus same-phase rejection, which is one rule instead of
a board and reads perfectly in a replay.)

### The LAB action menu (private science; the cards you burn are public)

Exactly one of these per seat per LAB phase.

| action | cost | effect | who learns what |
|---|---|---|---|
| `forage` | 0 | Draw **2** ingredient cards from the seeded supply into your hand (hand cap **6**; a draw into a full hand is discarded and recorded as such). | The drawn cards are **public**. |
| `test_student a b` | **−1 coin** | Consume cards `a` and `b` (one card each; with the **Magic Mortar** only `a` is consumed). You learn the potion. | The two ingredients used are **public**; the potion is **private to you**. |
| `test_self a b` | 0 coin | Consume cards `a` and `b` (Mortar: only `a`). You learn the potion, and you drink it: a **negative** potion poisons you (**−2 reputation**), a **positive** potion is a triumph (**+1 reputation**), MUD does nothing. | The two ingredients are public **and so is the potion's sign class** (`positive` / `negative` / `mud`) — everyone can see you glow or retch. The **colour** stays private to you. |
| `transmute a` | 0 | Consume one card `a`, receive **+2 coin**. | Public. |
| `pass` | 0 | Take the academy stipend, **+1 coin**. | Public. |

`test_student` costs a coin because a student has to be paid; `test_self` is free because you are
the one who suffers. That asymmetry is the idea's "testing on a student for coin, or on themselves
at a cost" and it is the game's only cash-for-safety trade.

### The MARKET action menu (public career)

Exactly one of these per seat per MARKET phase.

| action | cost | effect |
|---|---|---|
| `sell a b` | 0 | Consume cards `a` and `b` and sell the resulting potion to this round's adventurer. **Hit** (potion == demand): **+6 coin, +1 reputation**. **Miss** (anything else, MUD included): **+2 coin, −1 reputation** — the adventurer pays for the vial and tells everyone. **The potion is public either way**, which is why selling is also how you leak. |
| `publish x SIG` | **−1 coin** | Pin a wax seal claiming ingredient `x` has signature `SIG`. Immediate **+2 reputation** (**+3** with the Printing Press) — credit is paid for the claim, not for being right. Legal only if `x` carries **no standing seal**. Earns royalties from the next round open. |
| `endorse x` | **−1 coin, paid to the author** | Co-sign another seat's standing seal on `x` (never your own, never twice). At the exhibition you take **+2** if it was true and **−3** if it was false; if it burns first you take **−1** at the burn. |
| `debunk x with y` | **−1 coin**, consumes card `y` | A public demonstration against the standing seal on `x` (never your own). The academy supplies a sample of `x`; you supply `y`. The true potion `p = mix(sig[x], sig[y])` is **revealed publicly**. The seal's claim predicts `q = mix(claim, sig[y])`. **If `p ≠ q` the seal BURNS**: author **−4 reputation**, you **+3**, each endorser **−1**, the seal is struck from the board and `x` becomes publishable again. **If `p == q` the demonstration fails**: you **−2 reputation**, the author **+1** (their theory survived a challenge) and the seal stands. |
| `buy mortar` \| `buy press` | **−4 coin** / **−5 coin** | Buy an artifact, once each per seat. **Magic Mortar**: your `test_student` / `test_self` consume only the first card. **Printing Press**: `publish` pays +3 instead of +2, and royalties pay 2 instead of 1. |
| `pass` | 0 | **+1 coin** stipend. |

The debunk mechanic is the point of the port, so it is worth being explicit: a false seal only burns
when the attacker brings a reagent that *exposes* it. `p == q` happens often against a wrong claim
whose error this particular pairing cannot see — the attack fails, the attacker pays 2 reputation,
and the fraud is *strengthened*. Attacking well requires knowing more than the author, and every
attack — successful or not — hands the whole table a free public fact.

Coin never goes negative: an action a seat cannot afford is simply not in its legal set. `pass` is
always legal, so a legal move always exists.

### Ingredient supply

The supply is an unbounded seeded stream: each draw is one of the 8 ingredients drawn uniformly from
the sim's RNG, in a fixed draw order (initial hands seat 0..3, then every `forage` in resolution
order). Each seat starts with **3** cards. Every draw is also **recorded in the `act` /`start`
events**, and `replayMatch` asserts the recorded draws equal the seeded re-derivation — bullwhip's
"derive, then check" pattern (`replayMatch` on `week` events), so a tampered replay raises instead of
rendering a lie.

### The deduction grid (the structured deduction state, and the hole-cam)

A **fact** is one of three things, and every fact is a hard constraint on the chemistry:

| fact | meaning | who holds it |
|---|---|---|
| `mixFull(a, b, potion)` | mixing `a` and `b` gives exactly this potion | private to the tester; **public** for `sell` and `debunk` results |
| `mixSign(a, b, class)` | mixing `a` and `b` gives a potion of this class (`positive` / `negative` / `mud`) | **public**, from every `test_self` |
| `notSig(x, v)` | ingredient `x` is **not** signature `v` | **public**, minted when a seal burns |

Seat `s` knows: every public fact, plus its own private `mixFull` facts, plus the standing rule that
the chemistry is a bijection. Its **grid** is computed by **exact enumeration of all 40 320
bijections**, keeping those consistent with every fact it knows:

- `grid[s][x]` = the set of signatures `v` such that some consistent bijection maps `x → v`;
- `chemistriesLeft[s]` = how many bijections survive.

An ingredient whose set is a singleton is **solved** — that is when a seat may publish without
gambling. Enumeration is cheap (each fact is an O(1) check with early rejection) and it is **exact**:
no heuristic propagation, so the grid never over- or under-claims. It is recomputed **once per seat
per phase open** (≤ 4 × 2 × 10 + 4 = 84 recomputes in the longest legal episode) and memoised on the
sim, so the wasm viewer re-derives all four grids for a whole replay in well under a second. Grids are
*derived*, never recorded: the events carry the facts, the sim carries the solver, and the viewer runs
the same Nim code the server ran.

The grid is what the idea means by "deduction state passed structured": the seat's prompt receives
the grid as a table, not as prose, and the spectator sees the same grid as the hole-cam.

### Scoring, its sign, and what the league ranks by

Every seat starts on **reputation 10** and **coin 4**.

```
score(seat) = reputation(seat) + 0.2 * coin(seat)
```

**Higher is better** (this is the sign: reputation is the point, coin is the tiebreaker at one fifth
of a reputation point per coin — enough to make selling and royalties matter, never enough to beat a
true publication). A score is a float and **may be negative**: a seat that publishes three false
theories and gets burned lands below zero, and that is intended. The league ranks by **mean episode
score**; `results.scores[]` carries exactly this number per seat, attributed by **policy name**.

Reputation moves, all of them, in one place: publish +2 (+3 with the Press); sell hit +1; sell miss
−1; drink a positive potion +1; drink a negative potion −2; successful debunk: attacker +3, author
−4, each endorser −1; failed debunk: attacker −2, author +1; exhibition on a standing seal: true →
author +5, endorsers +2 each; false → author −6, endorsers −3 each. Nothing else moves it.

**Worked landmark** (pinned as a unit test): Sprocket runs `test_student` in round 0's lab
(coin 4→3), publishes Nightcap in round 0's market (coin 3→2, rep 10→12). Royalties at the opens of
rounds 1–5 pay 5 coin (2→7). In round 1 it forages, then sells a hit (+6 coin → 13, rep → 13). Rounds
2–5 it passes eight times (+8 coin → 21). The exhibition proves Nightcap true (+5 rep → 18). Final:
reputation 18, coin 21, **score = 18 + 0.2 × 21 = 22.2**. A seat that passes all twelve phases and
does nothing else finishes on reputation 10, coin 16, **score 13.2** — safe, mediocre, and exactly
the number a real policy has to beat.

### End conditions, and the legal `results.reason` values

Only two values are ever written:

- **`complete`** — all `rounds` rounds resolved, the exhibition ran, the truth is in the replay.
- **`deadline`** — the episode clock (60 % of `episodeTimeoutSeconds`, checked **before every LLM
  batch**, i.e. only ever between phases) stopped play. `endEarly()` then **still runs the
  exhibition** on the board as it stands and settles with `reason: "deadline"`. This is deliberate:
  a truncated episode whose theories were never opened would score everybody at their unearned
  publication credit, which would reward exactly the wrong behaviour. `results.rounds` reports the
  rounds actually played and `results.maxRounds` the cap, so the verifier can see the difference.

`endEarly()` is idempotent, is a no-op once `done`, and is the only path to `deadline`. There is no
resignation, no elimination, and no early win: all four seats play every phase.

### Per-seat observation — exactly what is visible and what is hidden

**Visible to seat `s` (its whole world; nothing else reaches its prompt):**

1. **Itself**: alias, coin, reputation, current score, artifacts owned, its **hand** (the exact
   multiset of card names), and its private notes from earlier phases.
2. **The round**: round index and cap, phase (`lab` / `market`), this round's adventurer demand, the
   initiative order, and which seats are still to act this phase (always all four — decisions are
   simultaneous).
3. **Every rival, publicly**: alias, coin, reputation, score, artifacts, **hand count** (never the
   cards), and its seals.
4. **The board**: every seal — ingredient, claimed signature, author alias, round published,
   endorser aliases, status `standing` / `burned` (with the burning demonstration and the debunker)
   / `vindicated` (survived a challenge; still standing).
5. **The public record**, every round, in order: each seat's action, the ingredients it used, and
   the publicly revealed outcome — the potion for `sell` and `debunk`, the **sign class only** for
   `test_self`, nothing for `test_student` beyond the two cards.
6. **Its own facts**: every `mixFull` it holds privately, as a table.
7. **Its deduction grid**: for each of the 8 ingredients, the candidate signatures still possible,
   with counts, plus `chemistries left`. Ingredients with one candidate are flagged `SOLVED`.
8. **Remarks**: every seat's `say` from the previous phase (public seminar chatter), when
   `talk` is on.
9. **`LEGAL MOVES`**: the exact, fully spelled action strings that are legal for this seat in this
   phase right now, computed by the **same predicate the validator applies** (escrow, 2026-08-23:
   precomputing the legal set is what stops formal-output games from falling back to scripted).

**Hidden from every seat:** the chemistry itself; any other seat's private `mixFull` results (only
the sign class leaks, and only from `test_self`); any other seat's hand contents, notes, grid or
`chemistriesLeft`; the seeded draw stream ahead of the current draw; future adventurer demands; and
this phase's undelivered actions by other seats (they are simultaneous). The player websocket frame
is redacted to exactly the list above, and a unit test asserts that no hidden value appears in the
frame *or* in the built prompt string.

### Integrity (how the idea's anti-collusion pin lands)

The chemistry is re-drawn per episode from the seed, so there is nothing to memorise across
episodes and nothing an author can pre-share. Experiments are private and the record is public and
in-band: every claim a seat makes about what it knows is either a seal (scored) or cheap talk
(`say`). Seats never learn which policy sits in which chair — they see aliases only — so
"be nice to my other copy" has no handle to grip.

### Two name spaces

In-game, seats are **anonymous cog aliases** (`Sprocket`, `Gizmo`, …) drawn from the seed: policy
display names never enter a prompt, an event, or a player frame. Spectator-side, the replay carries
`policyNames[]` alongside `names[]`, and `renderer.js`'s `makeNameMap` / `applyNames` (bullwhip's,
unchanged) swaps the real policy name in wherever a name is *rendered* — scorebug, feed, endcard,
seals — while leaving the events themselves aliased. Baseline fillers keep their alias
(`isBaselineFiller`). `resultsJson` reports under **policy** names, because that is what the league
attributes.

---

## Decisions: LLM with scripted fallback

Transport, credentials (Bedrock sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`), the
haiku-first Bedrock candidate rotation, `extractJsonObject`, `cleanText`, the "no credentials ⇒
every seat scripted" rule and the JSON-only output contract are ported from bullwhip's
`src/bullwhip/llm.nim` unchanged into `src/cogchemists/llm.nim`. What changes is the prompt, the
reply schema, the baselines, and the batch spacing.

### One parallel batch per phase

Decisions inside a phase are simultaneous **by rule**, so all four seats' requests go out as **one
`curly.makeRequests` batch** per phase — 12 batches in a default 6-round episode, never 48 sequential
calls. Failed or illegal replies are retried **once**, as a second, smaller batch carrying the
"your previous reply was invalid" hint; whatever still fails takes the scripted move.

**Batch spacing.** The hosted Bedrock sidecar caps **30 requests per minute per episode** (raid,
2026-08-23), and 4 seats per batch with no wall-clock floor can exceed that. `MinBatchSpacingMs`
(default **10 000**, config-settable, **0 when the LLM client is disabled**) is the minimum interval
between the *starts* of consecutive batches: 4 requests per 10 s = 24 req/min, and even a phase that
fires a full retry batch stays at 8 requests per 10 s window only once, which the cap absorbs.

### Episode budget — the arithmetic, out loud

`PlayBudgetFraction = 0.6` of `episodeTimeoutSeconds` (assumed **1200 s** when the env is silent —
the game container never receives `COWORLD_TIMEOUT_SECONDS`), so **play must fit in ≈720 s**.

- Phases: `2 × rounds` = **12** at the default 6 rounds.
- Per phase, worst case: `llmTimeoutSeconds` 20 s (first batch) + 20 s (retry batch) = 40 s, and the
  spacing floor of 10 s is inside that. Resolution, grid recomputation and broadcast are
  microseconds; `turnDelayMs` (default **250**, cert 0) is bounded by `PacingBudgetMs = 60 000`.
- **Worst case play: 12 × 40 s = 480 s**, plus at most 3 s of pacing, plus the player-connect wait
  (bounded at `player_connect_timeout_seconds` = 180 s, typically ~3 s). Absolute ceiling
  **≈ 663 s < 720 s**; typical hosted episode ≈ 12 × 16 s ≈ **192 s**.
- The deadline is checked **before every batch**. Past it, `endEarly()` runs the exhibition (no LLM
  needed) and settles `deadline`, and the results + replay are written with ≥ 480 s to spare. An
  episode that overruns is silently discarded by the platform, so a short honest episode always
  beats a long one that never lands.

### Prompts

**System prompt** (per seat, rebuilt each phase; ~1.4 kB): who it is (`You are Gizmo, an alchemist
of the Academy…`), the eight ingredient names, the signature notation, **the mixing rule stated as
the three numbered clauses above**, the seven potion values, the LAB and MARKET menus with every
cost and reward, the exhibition payoffs, the scoring formula with its sign, the rule that ingredients
used are public but `test_student` results are private, that `test_self` leaks the sign class, that
`sell` and `debunk` leak the whole potion, that a legal move can still be rejected by an earlier
seat in the same phase and degrades to `pass`, and the output contract: *reply with ONLY one JSON
object, no prose, no fences; your reply must begin with `{` and end with `}`* (Haiku answers
prose-first otherwise).

**User prompt**: the numbered observation above, rendered as short labelled blocks and fixed-width
tables — `YOU`, `TABLE`, `BOARD`, `PUBLIC RECORD`, `YOUR PRIVATE EXPERIMENTS`, `YOUR DEDUCTION GRID`,
`REMARKS LAST PHASE`, `YOUR NOTES`, then `GUIDANCE FROM YOUR OPERATOR` (the policy prompt, weighted
heavily but never above the rules — bullwhip's `operatorBlock`, verbatim), then `LEGAL MOVES` and the
one-line reply reminder. The grid block looks like:

```
YOUR DEDUCTION GRID (12 chemistries still possible)
Nightcap      SOLVED  R+G-B+
Emberroot     2       R-G+B+ | R-G+B-
Fen Lily      3       R+G+B+ | R+G+B- | R-G-B+
...
```

### Reply schema (one schema for both phases; every free-text field capped)

```json
{"action":"publish","a":"Nightcap","b":"","signature":"R+G-B+","artifact":"",
 "say":"Nightcap is settled; I would not bet against it.","notes":"…"}
```

| field | type | cap / domain | notes |
|---|---|---|---|
| `action` | string | ≤ **24 runes**, one of `forage`, `test_student`, `test_self`, `transmute`, `pass` (LAB) or `sell`, `publish`, `endorse`, `debunk`, `buy`, `pass` (MARKET) | case-insensitive; `-`/space normalised to `_`; a wrong-phase action is invalid (retryable) |
| `a` | string | ≤ **24 runes** | an ingredient: full name (case-insensitive), a unique prefix of ≥ 3 letters, or the index `0`–`7`. The target of `publish`/`endorse`/`debunk`; the first card otherwise |
| `b` | string | ≤ **24 runes** | the second card for `test_*`/`sell`; the reagent `y` for `debunk`; `""` otherwise |
| `signature` | string | ≤ **12 runes** | `publish` only: the three signs in RGB order — `R+G-B+`, `+-+`, `+ - +` all parse; anything not yielding exactly three `+`/`-` is invalid |
| `artifact` | string | ≤ **12 runes** | `buy` only: `mortar` or `press` |
| `say` | string | ≤ **140 runes** | public seminar remark, delivered to all seats next phase; dropped entirely when `talk` is false; newlines collapsed to spaces |
| `notes` | string | ≤ **600 runes** | private notebook, fed back verbatim next phase; recorded in the event log and shown to spectators (hole-cam) |

**Every one of these caps truncates on rune boundaries** (`unicode.runeLen` / `runeSubStr`, bullwhip's
`cleanText`), never on bytes: a byte-boundary cut leaves invalid UTF-8 in the replay and a strict JSON
parser rejects the whole file (bullwhip, 2026-08-22). The same rune rule applies to the 4000-char
player prompt and to any error text quoted into the log.

A reply is **invalid** (→ retry, then scripted) when the JSON is missing, `action` is absent/unknown
for the phase, an ingredient does not resolve, the seat does not hold the named cards, a signature is
malformed, or the move is **illegal at this instant** (the sim's own `applyAct` is run against a
probe copy exactly as bullwhip probes `applyOrder`). Trailing prose after the object is tolerated.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

Both baselines are pure functions of the sim state (plus a deterministic stream derived from
`seed, round, phase, seat`), always legal, never talk, never write notes.

**`assayer`** — the competent scientist, and the partner a champion prompt has to beat:

1. *LAB.* If `hand.len < 2` → `forage`. Else consider every unordered pair of distinct cards in hand;
   for each, partition the seat's currently-consistent chemistries by the potion that pair would
   produce and score the pair by its **largest bucket** (the worst case); pick the pair with the
   smallest largest bucket, ties broken by the lower ingredient indices. Use `test_student` while
   `coin ≥ 2`, otherwise `test_self` when the pair's worst case cannot be a negative potion, else
   `transmute` the least useful card (the one appearing in no discriminating pair), else `pass`.
2. *MARKET.* In order: (a) if some ingredient is **solved**, unclaimed and `coin ≥ 1` → `publish` it
   (lowest index first); (b) else if a rival's standing seal is **inconsistent with its own grid** and
   it holds a reagent `y` whose demonstration is guaranteed to expose it → `debunk x with y`;
   (c) else if it holds a pair guaranteed to produce this round's demand → `sell`; (d) else if
   `coin ≥ 4` and it does not own the Mortar → `buy mortar`; (e) else `pass`.

**`quack`** — the reckless careerist, the weak filler: forages when its hand is short, otherwise
`test_self`s a deterministic pseudo-random pair (free science, and the poisonings are good
television); in the market it publishes the **lowest-index candidate** for the lowest-index unclaimed
ingredient the moment it has a coin — certainty be damned — and otherwise `sell`s or `pass`es. It
never endorses and never debunks. It is what the game is a satire of, and it reliably finishes last.

Both are fieldable policies (`PLAYER_SCRIPTED=assayer` / `PLAYER_SCRIPTED=quack`) **and** the
in-server fallback: with no credentials every seat plays `assayer`, so offline certification and the
docker smoke always complete without a network call.

### Degrade, never hang

- **A seat's decision that times out or fails to parse gets exactly one retry** (in the phase's
  second, smaller batch, with the invalid-reply hint), then **falls back to the scripted `assayer`
  move** for that seat, recorded with `scripted: true` so phase-60 check 4 can tell a real decision
  from a fallback.
- A decision the sim rejects at apply time (a same-phase conflict) is recorded
  `result: "rejected:<reason>"` and degrades to `pass`. The episode always advances.
- `client.disabled` (auth failure, or no credentials at all) short-circuits the whole batch to
  scripted with **no network wait**, and the spacing floor is skipped.
- **The episode settles early** rather than overrunning: the play deadline is tested before every
  batch; past it, `endEarly()` runs the exhibition and settles `deadline`, then the server writes
  `results.json` and the replay and exits 0.
- A player pod that never connects costs at most `player_connect_timeout_seconds` (180 s) and then
  the game starts anyway — that seat plays its default prompt.
- The server keeps `/healthz` and `/global` answering for `shutdownGraceSeconds` (**20 s**) after the
  artifacts are written, then exits — the certifier pings `/global` after the player pods start
  (lantern 0.1.3).
- The player's receive loop is wrapped in `try/except CatchableError` and **exits 0** on a dead
  socket (raid 0.1.3: whisky raises on a close frame and the seat is scored a `player_error`
  otherwise).

---

## Sim module

Files, all forks of the named bullwhip file unless marked new:

### `src/cogchemists/chem.nim` (new) — the chemistry and the solver

```nim
const
  Ingredients* = 8
  Signatures* = 8              ## the 8 sign triples, index 0..7 = bits RGB
  IngredientNames* = ["Nightcap", "Emberroot", "Fen Lily", "Widow's Salt",
                      "Copper Fern", "Gravebloom", "Sunmoss", "Rime Thistle"]
type
  Potion* = enum poNone = "", poRedPos = "RED+", poRedNeg = "RED-",
    poGreenPos = "GREEN+", poGreenNeg = "GREEN-", poBluePos = "BLUE+",
    poBlueNeg = "BLUE-", poMud = "MUD"
  SignClass* = enum scPositive = "positive", scNegative = "negative", scMud = "mud"
  Chemistry* = array[Ingredients, int]      ## ingredient -> signature index
  FactKind* = enum fkMixFull, fkMixSign, fkNotSig
  Fact* = object
    kind*: FactKind
    a*, b*: int
    potion*: Potion
    signClass*: SignClass
    sig*: int
  Grid* = object
    candidates*: array[Ingredients, set[uint8]]   ## still-possible signatures
    chemistries*: int
```

- `sigName(i)` → `"R+G-B+"`; `parseSignature(text)` → index or −1.
- `mixSignatures(sa, sb): Potion` — the three numbered clauses, symmetric, total.
- `signClassOf(potion): SignClass`.
- `drawChemistry(rng): Chemistry` — a shuffled permutation of `0..7`.
- `consistent(chem, facts): bool` — every fact checked, early exit.
- `solveGrid(facts): Grid` — enumerate all 40 320 bijections (Heap's algorithm), keep the consistent
  ones, union their images per ingredient, count them. Returns the full-open grid immediately when
  `facts.len == 0`.

### `src/cogchemists/types.nim` (fork of `src/bullwhip/types.nim`)

`CogchemistsError`, `PlayerConfig`, `GameConfig`, `SeatState`, `Seal`, `EventKind`, `GameEvent`,
`defaultGameConfig`, `update`.

`GameConfig`: bullwhip's with `rounds` (default 6, 3..10) replacing `weeks`, plus `talk` (default
true), `artifacts` (default true), `minBatchSpacingMs` (default 10 000), `shutdownGraceSeconds`
(default 20), `episodeTimeoutSeconds` 1200, `turnDelayMs` 250, `model`, `maxOutputTokens` 900,
`llmTimeoutSeconds` 20, `playerConnectTimeoutSeconds` 180, `sampled`.

`SeatState`: `coin`, `reputation`, `hand: seq[int]` (a multiset of ingredient indices, cap 6),
`mortar`, `press`, `privateFacts: seq[Fact]`, `notes`, `say`, `heard`, `published: seq[int]`,
`endorsed: seq[int]`.

`Seal`: `ingredient`, `claim` (signature index), `author`, `roundPublished`, `endorsers: seq[int]`,
`status` (`sealStanding` / `sealBurned`), `vindications`, `burnedBy`, `roundBurned`.

### `src/cogchemists/sim.nim` (fork of `src/bullwhip/sim.nim`)

```nim
const
  Seats* = 4
  MinRounds* = 3
  MaxRounds* = 10
  StartCoin* = 4
  StartReputation* = 10
  StartHand* = 3
  HandCap* = 6
  ForageDraw* = 2
  StudentCost* = 1
  TransmuteCoin* = 2
  PassCoin* = 1
  SellHitCoin* = 6
  SellMissCoin* = 2
  PublishCost* = 1
  PublishRep* = 2
  PressPublishRep* = 3
  RoyaltyCoin* = 1
  PressRoyaltyCoin* = 2
  EndorseCost* = 1
  DebunkCost* = 1
  BurnAuthorRep* = -4
  BurnDebunkerRep* = 3
  BurnEndorserRep* = -1
  SurviveDebunkerRep* = -2
  SurviveAuthorRep* = 1
  DrinkPositiveRep* = 1
  DrinkNegativeRep* = -2
  SellHitRep* = 1
  SellMissRep* = -1
  ExhibitTrueAuthor* = 5
  ExhibitTrueEndorser* = 2
  ExhibitFalseAuthor* = -6
  ExhibitFalseEndorser* = -3
  MortarCost* = 4
  PressCost* = 5
  CoinWeight* = 0.2
  MaxSayLen* = 140
  MaxNotesLen* = 600
  PacingBudgetMs* = 60_000
  CogNames* = [...]            ## bullwhip's, unchanged
```

`Sim` object: `config`, `names`, `chemistry`, `demand: seq[Potion]` (one per round, seeded),
`round`, `phase: Phase` (`phLab` / `phMarket` / `phDone`), `seats: array[4, SeatState]`,
`seals: seq[Seal]`, `publicFacts: seq[Fact]`, `grids: array[4, Grid]`, `gridVersion: array[4, int]`,
`acted: array[4, bool]`, `roundsPlayed`, `rng state`, `done`, `reason`, `events`.

API (names chosen to mirror bullwhip's so the server fork is mechanical): `initSim`,
`sampleEpisode` (fits `rounds` and `turnDelayMs` into `PacingBudgetMs`), `tableNames`,
`initiativeOrder(round)`, `pendingSeats(sim)`, `legalMoves(sim, seat): seq[string]`,
`applyAct(sim, seat, act: Action, scripted: bool)` (raises `CogchemistsError` on an illegal act; the
last act of a phase advances the phase, the last phase of the last round runs `exhibition()` then
`settle("complete")`), `refreshGrids(sim)`, `endEarly(sim)` (runs `exhibition()`, then
`settle("deadline")`), `score(sim, seat)`, `resultsJson`, `tableStateJson`, `observationJson(sim,
seat)`, `replayMatch(config, events)`, `eventToJson`, `eventFromJson`.

### Event vocabulary (flat `GameEvent`, JSON via `eventToJson` / `eventFromJson`)

Six kinds. Everything the viewer and the feed need is here; nothing the viewer needs is anywhere
else.

| kind | fields |
|---|---|
| `start` | `chemistry` (the true bijection — spectator-side only, present so the endcard and the grids can be re-derived and cross-checked), `hands` (the four seeded opening hands) |
| `round` | `round`, `demand` (potion string), `initiative` `[4]`, `royalties` `[4]`, `seats` `[4]` public snapshots (`coin`, `reputation`, `handCount`, `mortar`, `press`, `score`) |
| `phase` | `round`, `phase` (`lab` \| `market`) |
| `act` | `round`, `phase`, `seat`, `action`, `a`, `b` (ingredient indices, −1 when unused), `signature` (−1 when unused), `artifact`, `potion` (the outcome potion, **including private ones** — the replay is spectator-side), `secret` (true when rivals saw only the sign class or nothing), `draws` (`forage`/opening draws), `discarded`, `result` (`ok` \| `hit` \| `miss` \| `poisoned` \| `glowed` \| `burned` \| `survived` \| `rejected:<reason>`), `coinDelta`, `repDelta`, `target` (the seal's author on `endorse`/`debunk`), `scripted`, `say`, `text` (the seat's notes after this reply) |
| `exhibition` | `round`, `chemistry` (the truth again, so a viewer that seeks straight to the end needs no other event), `verdicts`: one entry per standing seal (`ingredient`, `claim`, `author`, `endorsers`, `true`), `repDeltas` `[4]` |
| `end` | `round` = rounds played, `text` = `complete` \| `deadline` |

`replayMatch(config, events)` re-derives the whole timeline: it rebuilds the sim from
`config.seed`, **asserts** the recorded `chemistry`, opening hands, per-round demands and every
`draws` array equal the seeded re-derivation (raising `CogchemistsError` on a mismatch — a tampered
replay fails loudly rather than rendering a lie), applies every `act` through the real rules, and
re-runs the exhibition. `frames[i]` = state after `events[0..<i]`, so `frames.len == events.len + 1`.

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"seats":[{"name":"Sprocket","coin":7,"reputation":13,"score":14.4,
           "hand":["Nightcap","Sunmoss"],"handCount":2,"mortar":true,"press":false,
           "published":[0],"endorsed":[],"say":"…","notes":"…","pending":true,
           "grid":[[3],[1,5],[0,2,6],[4],[7],[1,5],[0,2,6],[0,2,6]],
           "chemistries":12,"solved":3,"action":"publish","result":"ok"}, ×4 by seat],
 "seals":[{"ingredient":0,"claim":3,"claimText":"R+G-B+","author":0,"authorName":"Sprocket",
           "round":0,"endorsers":[2],"status":"standing","vindications":1,
           "burnedBy":-1,"roundBurned":-1}],
 "publicFacts":[{"kind":"mixFull","a":0,"b":6,"potion":"GREEN-"},
                {"kind":"mixSign","a":1,"b":3,"class":"negative"},
                {"kind":"notSig","x":2,"sig":5,"sigText":"R-G+B-"}],
 "bench":{"seat":1,"a":0,"b":6,"potion":"GREEN-","secret":false},
 "ingredients":["Nightcap","…"],"signatures":["R+G+B+","…"],
 "round":3,"rounds":6,"roundsPlayed":3,"phase":"market","demand":"RED+",
 "demands":["RED+","BLUE-","GREEN+","RED+"],"initiative":[3,0,1,2],
 "chemistry":[],"gameDone":false,"reason":""}
```

`chemistry` is an empty array until the exhibition frame, where it becomes the eight signature
indices — so a spectator scrubbing mid-episode cannot see the answer, and the endcard can.
`bench` is the mix currently on the lab table (what the flask animates), `null` when idle.

### `resultsJson` — platform-facing, policy names

```json
{"names":[4],"scores":[4 floats = reputation + 0.2*coin],"reputation":[4 ints],"coin":[4 ints],
 "published":[4],"trueTheories":[4],"falseTheories":[4],"burned":[4],"debunks":[4],
 "rounds":<played>,"maxRounds":<cap>,"reason":"complete|deadline"}
```

### Replay payload — `cogchemists.replay.v1`

```json
{"protocol":"cogchemists.replay.v1","names":[4 aliases],"policyNames":[4 policy names],
 "config":{"rounds":6,"seed":8123,"talk":true,"artifacts":true,"sampled":true,
           "chemistry":[3,1,5,0,7,2,6,4]},
 "events":[…],"results":{…}}
```

Replay mode and the wasm viewer add `"states"` (one `tableStateJson` per event prefix). **The bytes
are self-sufficient**: aliases *and* policy names, the whole config **including the seed and the
secret chemistry**, every event with every per-tick state input, and the results. The viewer
contacts nothing but S3 for the `.replay` file.

---

## Server, player, protocol

### `src/cogchemists/server.nim` (fork of `src/bullwhip/server.nim`)

Routes are bullwhip's, renamed: `GET /healthz`, `GET /client/global`, `GET /client/player`,
`GET /client/replay`, `GET /client/renderer.js`, `GET /client/chrome.css`,
`GET /client/assets/@name`, `WS /player?slot=N&token=T`, `WS /global`, `WS /replay`. Both
`/client/player` and `/client/global` serve real pages, registered **before** any catch-all asset
route, and neither opens the player socket (lantern 0.1.1: the certifier probes them before player
pods start). mummy hands `Ping` frames to the application, so the websocket handler answers them
with `Pong` — bullwhip's code, kept.

The game loop replaces bullwhip's weekly loop with the phase loop: wait for connects (bounded) →
`newLlmClient` → per phase: check the play deadline, snapshot the sim, refresh grids, build each
pending seat's observation, `decideAll` **outside the lock** on the snapshot, then apply the
decisions **in initiative order** under the lock (each apply that raises degrades to `pass` with
`result: "rejected:<reason>"`), broadcast, sleep `turnDelayMs`, and enforce `minBatchSpacingMs`
between batch starts. After the loop: `finishEpisode` sends the final frames to the players
**before** writing artifacts (the worker tears player pods down as soon as `results.json` exists),
writes `results.json` and the replay through `writeArtifact`, keeps serving for
`shutdownGraceSeconds`, then `quit(0)`.

### Player protocol — `cogchemists.player.v1`

JSON text frames over `COWORLD_PLAYER_WS_URL`:

- game → player, on connect:
  `{"type":"welcome","protocol":"cogchemists.player.v1","slot":N,"name":"Gizmo","rounds":6}`
- game → player, after every event: `{"type":"state","slot":N,"name":…,"you":{coin,reputation,score,
  hand,mortar,press,grid,chemistries,notes},"table":[4 public seat summaries],"seals":[…],
  "publicFacts":[…],"round":int,"rounds":int,"phase":str,"demand":str,"legal":[…],"heard":[4],
  "started":bool,"done":bool,"reason":str}` — **redacted to exactly the observation list above**;
  no other seat's hand, private facts, notes or grid ever crosses this socket.
- game → player, at the end: `{"type":"final","done":true,"scores":[…],"reputation":[…],"coin":[…],
  "names":[4 aliases],"rounds":int,"reason":str}` — the player exits after this.
- player → game: `{"type":"prompt","prompt":"…","scripted":"assayer"}` — the prompt is the policy
  (≤ **4000 runes**, truncated on a rune boundary), sent on connect and again after `welcome`;
  `scripted` is `""` (LLM), `assayer` / `1` / `true`, or `quack`.

### Global protocol

`WS /global` receives the full `tableStateJson` snapshot after every event, plus `type`, `game`,
`policyNames`, `events` (the whole append-only transcript), `started`, `done`, `connected`. This is
the spectator view and it *does* carry private results and, at the exhibition, the chemistry —
which is exactly why the player socket has its own redacted frame.

### `src/cogchemists_player.nim` (fork of `src/bullwhip_player.nim`)

Reads `PLAYER_PROMPT` (falling back to a built-in default strategy in words: *test the pair that
splits your candidate set most, never publish an ingredient your grid has not solved unless the
round is late, attack a seal only with a reagent that must expose it, and remember that everything
you sell is a gift to your rivals*) and `PLAYER_SCRIPTED`, delivers the prompt frame, then idles
until `final`. The receive loop is wrapped in `try/except CatchableError` and exits 0 on a dead
socket.

---

## Viewer

**All four viewer files come from one starter — `Metta-AI/cogame-bullwhip` — and only from it:**
`replay-viewer/config.nims`, the wasm entry `replay-viewer/cogchemists_replay.nim` (fork of
`replay-viewer/bullwhip_replay.nim`), `replay-viewer/static_replay.js` and
`replay-viewer/index.html`. Nothing is spliced in from another starter. Bullwhip's emscripten link
flags stay exactly as they are — `-O2`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`,
`ENVIRONMENT=web`, `MODULARIZE=1`, `EXPORT_NAME=CogchemistsReplayModule`,
`EXPORTED_RUNTIME_METHODS=HEAPU8`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_cc_load_replay,_cc_payload_ptr,_cc_payload_len,_cc_error_ptr,_cc_error_len`,
plus `emscripten_exit_with_live_runtime()` — and `static_replay.js` keeps calling the module through
that same `CogchemistsReplayModule()` factory with the same `_malloc`/`HEAPU8.set`/`_cc_load_replay`
handshake. (cogame-lantern, 2026-08-23: one starter's shell on another's link flags deadlocks
silently with every asset returning 200.)

**Load signalling.** `renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame** —
bullwhip already does exactly this at the end of `attachReplay`'s `makeRenderer` callback
(`client/renderer.js:1390`), kept verbatim. On any failure (missing `?replay=`, the 20 s fetch
timeout, a non-200, a wasm rejection) `static_replay.js` sets
`document.documentElement.setAttribute("data-replay-error", <message>)`, shows a Retry button and
posts the `coworld-replay` `error` envelope; it removes the attribute on a successful retry.
`tools/ci/viewer_smoke.mjs` and `viewer-check.yml` read exactly these two signals. One deliberate
change to the starter's shell: `start()` posts `tell("ready")` only after polling
`data-replay-loaded === "true"` on `requestAnimationFrame` (bounded at 240 frames, then
`tell("error", "renderer never drew a frame")`), so `ready` always means a picture rather than a
parsed payload.

**Bundle.** `"replay_viewer": {"bundle": "static-replay-viewer"}` in the manifest — **never a
`/client/replay` pod**. `tools/build_replay_viewer.sh` (bullwhip's, paths renamed) is the
`coworld build` hook, committed `chmod +x`, with `mkdir -p` on the output parent **before** the
containment check (ecos, 2026-08-23). It compiles `replay-viewer/cogchemists_replay.nim` to wasm
(locally with `emcc`, otherwise in the pinned `emscripten/emsdk:4.0.15` container from
`Dockerfile.replay-viewer`) and copies `cogchemists_replay.js`, `cogchemists_replay.wasm`,
`index.html`, `static_replay.js`, `client/renderer.js`, `client/chrome.css` and the `data/` assets
into the bundle. The wasm module runs the **same Nim sim** the server ran, so every frame — including
all four deduction grids — is re-derived in the browser from the replay bytes.

### Chrome provenance — what is copied and what is appended

The pins name `client/chrome_common.js` and `client/replay_broadcast.html`. **The bullwhip lineage
has neither**; those two roles are held by **`client/renderer.js` + `client/chrome.css`** (the shared
chrome: topband, scorebug, feed, scrubber, transport, endscreen, name map, effects, both drivers,
replay pacing) and **`client/replay.html`** (the broadcast page; `replay-viewer/index.html` is the
same page with local asset paths). Nothing is imported from a starter that does have them. The rule
is applied to those files:

- **`client/chrome.css` is copied byte-for-byte** from `cogame-bullwhip` and a single
  `/* ---------- Cogchemists ---------- */` block is **appended at the end**. No existing rule is
  edited or deleted — the file already accretes one appended block per game in this lineage
  (`/* Focus: … */`, `/* Babel: … */`, `/* Bullwhip: … */`). The appended block contains exactly:
  - `:root { --band: 96px; --hudscale: 1; }` — set for real by `relayout()` (below);
  - `.plate-rep` (the reputation chip), `.plate-coin`, `.plate-seals` (a row of wax-seal pips,
    charred when burned), `.plate-solved` (how many ingredients that seat has solved);
  - `#labbar` — the appended game element — sized with `font-size: calc(11px * var(--hudscale))`;
  - `.beat-label` and the beat-marker rules for **every kind the scrubber emits**:
    `.beat-marker.publish` (amber, 12 px), `.beat-marker.debunk` (red, 14 px), `.beat-marker.sell`
    (green, 10 px), `.beat-marker.test` (paper, 8 px), `.beat-marker.trade` (dim paper, 6 px),
    `.beat-marker.exhibition` (amber, 16 px), `.beat-marker.end` (amber, 3 px × 16 px) — plus the
    seat tint through the existing `.seat0`…`.seat3` `--tc` classes, which `chrome.css` already
    defines;
  - feed colours `.feed-publish`, `.feed-debunk`, `.feed-burn`, `.feed-sell`, `.feed-test`,
    `.feed-poison`, `.feed-exhibit`, `.feed-say`, `.feed-notes`, `.feed-reject`;
  - `#loading { bottom: var(--band); }` so the caption never sits over the transport;
  - the small-screen queries: `@media (max-width: 640px)` hides `.plate-label` and `.plate-coin` and
    shortens `#labbar`; `@media (max-width: 420px)` keeps bullwhip's
    `#scorebug { grid-template-columns: repeat(2, 1fr); }`.
- **`client/replay.html` is bullwhip's page with a game block appended** — never a rewrite that
  reuses the ids (cogame-gridlock, 2026-08-23). **Every element the starter ships is kept, with its
  id**: `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`,
  `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`,
  `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, and the
  `fit()` + `bindFeedToggle` bootstrap. **Elements removed: none.** The only edits are (a) the
  wordmark's inner text `BULL<span>WHIP</span>` → `COG<span>CHEMISTS</span>` and the `<title>`, and
  (b) **one appended element**: `<div id="labbar"></div>` inserted between `#scorebug` and
  `#board-wrap`. `replay-viewer/index.html` gets the identical treatment (same page, `./` asset
  paths, the `cogchemists_replay.js` / `static_replay.js` script tags).
- **Zoom: dropped entirely.** Bullwhip ships no `#viewpanel` (no zoom bar, no minimap) and none is
  added. The lab table is a **fixed arena** — a bench, four stations, a board and a grid strip, all
  laid out from the canvas size by `computeLayout` — so the whole scene is always inside the frame
  and zoom controls would be dead weight.

### Transport rules

- `--band` and `--hudscale` are set **on `:root`** (`document.documentElement`) by a `relayout()`
  function in the page bootstrap (`client/replay.html` and `replay-viewer/index.html`), called on
  `load`, on `resize`, and by the existing feed-toggle resize event: it measures `#transport`'s
  `offsetHeight` into `--band` and sets `--hudscale = clamp(0.8, width / 960, 1.15)`. `fit()`
  (bullwhip's canvas resizer) is called from the same function, so the canvas and the custom
  properties can never disagree.
- **Nothing is overlaid in the transport band.** `#transport` is the last child of `#stage` in normal
  flex flow; the only absolutely-positioned overlays (`#lightpool`, `#grain`, `#endscreen`) live
  inside `#board-wrap`, which ends where the band begins, and `#loading` is pinned above it with
  `bottom: var(--band)`.
- **The endcard stops at `var(--band)`** — `#endscreen` is `position: absolute; inset: 0` inside
  `#board-wrap`, so its bottom edge is exactly `var(--band)` above the page bottom — **and is
  dismissed by every seek**: `attachReplay`'s `setIndex` calls `updateEndscreen(container, results,
  index >= events.length && events.length > 0, …)` on *every* index change and `updateEndscreen`
  does `container.classList.toggle("show", !!show)`. Bullwhip's code, kept verbatim.
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` is kept verbatim except that each
  beat is created as `<button type="button" class="beat-marker …">` carrying an `aria-label` /
  `title` and an `onclick` that seeks to that event index; the container keeps its drag-to-seek
  pointer handlers. Beats are emitted for every `act` of kind `publish`, `debunk`, `sell` and
  `test_*`, for `trade` (forage / transmute / buy / pass, dim), for the `exhibition` and for the
  `end`, labelled in words — `"R3 · PUBLISH · Sprocket claims Nightcap R+G-B+"`,
  `"R4 · DEBUNK · Gizmo burns Sprocket's seal"`, `"R2 · SELL · Widget hits RED+"`,
  `"R1 · TEST · Ratchet drinks it"`, `"EXHIBITION"`, `"FINAL"` — and the appended CSS defines a rule
  for **each of those seven kinds**. Rounds remain the round spans / separators bullwhip already
  draws (one span per phase, a separator each round).
- **Naming guard** (tandem, 2026-08-23): the appended game block's builders are named
  `markChemBeat` / `buildLabBar`, never `markBeat` / `buildScrub`, so nothing can be shadowed by a
  chrome alias assignment; `tests/test_viewer.nim` asserts no top-level name in the appended block
  collides with a name the chrome defines above it.

### The stage — the lab table

Real art, from the starter's own assets (`data/arena_floor.png` as the bench surface, `font.ttf`, the
four `soldier_<red|blue|green|yellow>_front.png` cog sprites), drawn in the Ink & Print palette
`renderer.js` already defines. No placeholder boxes.

- **The bench, centre.** Two ingredient cards slide onto the bench (paper cards with the ingredient's
  name and a hand-drawn glyph), the flask **bubbles** for `SLIDE_MS`, then resolves: a coloured
  splash filling the flask with a large `+` or `−` for a coloured potion, a grey-brown swirl and the
  word `MUD` otherwise. A **private** result (`test_student`) draws the flask behind a paper screen
  with the potion still shown — this is a spectator view, and the screen is how the audience knows
  the rivals did *not* see it. `test_self` shows the acting cog drinking: a green glow for positive,
  a red retch and a `POISONED −2` tag for negative.
- **Four stations**, one per seat, in seat colour: the cog sprite, alias/policy name, a reputation
  counter (large), a coin counter, its hand as face-up ingredient cards, and artifact badges (a
  mortar, a printing press) once bought. An amber dashed halo marks a seat the table is waiting on.
- **The theory board, right.** One wax-sealed card per published ingredient: ingredient name, claimed
  signature drawn as three coloured dots with `+`/`−`, the author's seat colour on the seal, endorser
  pips underneath. A burn plays the gong: the seal cracks, chars, tilts, and a `BURNED BY GIZMO` tag
  hangs on it for the rest of the episode. A vindicated seal gets a small amber laurel.
- **The hole-cam strip, bottom.** Four rows (one per seat, seat-coloured) × eight columns (one per
  ingredient); each cell shows how many signatures that seat still considers possible, and a solved
  cell shows the signature glyph itself instead of a number. That is the idea's "who actually knows
  and who is bluffing": when a seat publishes an ingredient its own grid has **not** solved, the cell
  is ringed in red and a `BLUFF?` tag flashes. A seat's full 8 × 8 grid is drawn beside the bench
  while that seat is acting.
- **The endcard reveal.** At the `exhibition` event the true chemistry is stamped across the strip:
  every cell resolves to the true signature, correct seals get an amber `TRUE +5`, false seals a red
  `FALSE −6`, and the row of true signatures is drawn once, large, under the board.

### Readouts

- **`#clock`** (top band): `ROUND 3 / 6 · LAB · WAITING ON 4`, `ROUND 3 / 6 · MARKET · MOVES IN`,
  `EXHIBITION`, `FINAL · SPROCKET 22.2`.
- **`#labbar`** (appended): `ROUND 3/6 · ADVENTURER WANTS RED+ · SEALS 3 STANDING / 1 BURNED ·
  BEST GRID 12 CHEMISTRIES LEFT`.
- **`#scorebug`**: four plates — `name · rep 13 · 7c · 2 seals · 3 solved` — with the seal pips
  charred when burned and the reputation number as the big figure (it is the score).
- **`#feed`** (the log), grouped `ROUND 3 · LAB` / `ROUND 3 · MARKET` heads, in words a casual
  spectator can read:
  - `Sprocket tests Nightcap + Sunmoss on a student — result sealed (only Sprocket saw it).`
  - `Ratchet drinks Emberroot + Fen Lily — negative. Poisoned, −2 reputation.`
  - `Widget sells Copper Fern + Sunmoss: GREEN− — the adventurer wanted RED+. −1 reputation, +2 coin.`
  - `Sprocket publishes: Nightcap is R+G−B+. Seal pinned, +2 reputation.`
  - `Gizmo endorses Sprocket's Nightcap seal.`
  - `Gizmo debunks Sprocket's Nightcap with Rime Thistle → BLUE+, the seal predicted GREEN−. SEAL
     BURNED. Sprocket −4, Gizmo +3.`
  - `Widget debunks Ratchet's Sunmoss with Gravebloom → MUD, exactly as claimed. The seal stands.
     Widget −2.`
  - `Sprocket says: "I would not bet against Nightcap."`
  - `EXHIBITION — Nightcap R+G−B+ TRUE: Sprocket +5, Gizmo +2. Sunmoss R−G+B− FALSE: Ratchet −6.`
  - `Final — Sprocket 22.2, Gizmo 16.4, Widget 11.0, Ratchet −1.8 over 6 rounds.` plus
    `Episode deadline — the academy closed early; the exhibition was held after 4 of 6 rounds.` when
    `reason == "deadline"`.
  - Rejections are shown, dim: `Widget tried to publish Nightcap — Sprocket claimed it first this
    phase. Widget passes (+1 coin).`
- **`#endscreen`**: title `FINAL — 6 ROUNDS · 4 SEALS · 2 BURNED`; verdict `<name> MADE THE
  REPUTATION`; a `deadline` reason line when applicable; rows ranked by score with columns
  `reputation`, `coin`, `published`, `true`, `false`, `score`.

### Legible at 360 px wide

The canvas re-fits on every `relayout()`. Below 640 px the stations drop their hand cards to a count,
the board shows seals as signature dots without the ingredient name, the hole-cam strip drops to the
per-seat "solved / chemistries left" pair, and the feed collapses behind bullwhip's existing `LOG »`
toggle; below 420 px the scorebug goes to two columns of two and `#labbar` shortens to
`R3/6 · WANTS RED+ · 3 SEALS`. `.plate-name` keeps bullwhip's `flex: 1 1 auto; min-width: 3.2em` so
policy names do not collapse to ellipses in the ~360 px featured-match iframe. Everything renders as
words and numerals — `RED+`, `Nightcap`, `SEAL BURNED`, `rep 13` — never internal notation like
`i0`, `p3` or `sig#5`.

---

## Packaging

- **`compose.yaml`** — service **`cogchemists`** (= the coworld name), `image:
  coworld-cogchemists:latest`, `platform: linux/amd64`, `build: {context: ., network: host}`. The
  manifest's image placeholder is derived from **this service name** — `{{COGCHEMISTS_IMAGE}}` —
  because `coworld build` maps compose services to placeholders and hard-fails anything else
  (cogame-lantern 0.1.0, 2026-08-23).
- **`Dockerfile`** — bullwhip's, renamed: one image, two entrypoints, `/bin/cogchemists` (default
  `CMD`) and `/bin/cogchemists-player`; `client/` and `data/` copied into the run image; `nim.cfg`
  regenerated from the container's package tree. **`Dockerfile.replay-viewer`** — bullwhip's,
  renamed (emsdk 4.0.15, nimby 0.1.27, Nim 2.2.4).
- **`cogchemists.nimble`** — version `0.1.0`, `srcDir = "src"`, requires `nim >= 2.2.4`, `bitworld`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`; `nimby.lock` copied from bullwhip unchanged.
- **`data/`** — bullwhip's `arena_floor.png`, `font.ttf`, `FONT_LICENSE.txt` and the four cog
  sprites, unchanged (four seats, four sprites; no recolours needed).
- **`coworld_manifest_template.json`** — `$schema`, ≥3 tags
  (`["deduction","alchemy","hidden-information","reputation","llm-driven","turn-based",
  "four-player","bluffing"]`), `game.name` `cogchemists`, `game.runnable.type: "game"`,
  `image: {{COGCHEMISTS_IMAGE}}`, `run: ["/bin/cogchemists"]`,
  `env.ANTHROPIC_API_KEY_URI = "secret://coworld/cogchemists/anthropic_api_key"` (without it every
  hosted league episode silently plays scripted — hive, 2026-08-23), `source_url`
  `https://github.com/Metta-AI/cogame-cogchemists/tree/main`, owner `daveey@gmail.com`,
  top-level `episode_timeout_minutes: 20`, and
  **`"replay_viewer": {"bundle": "static-replay-viewer"}`**.
  - **`config_schema`** — a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens","players"]` (`tokens` stays required — matriculation rejects the manifest
    otherwise), and **every array property carries `minItems`/`maxItems`** (tandem, 2026-08-23):
    `tokens` and `players` `minItems`/`maxItems` **4**; **`num_agents` integer minimum 4 maximum 4**;
    `seed` integer; `rounds` integer 3..10 default **6**; `talk` boolean default `true`; `artifacts`
    boolean default `true`; `episodeTimeoutSeconds` 60..6000 default 1200; `turnDelayMs` 0..10000
    default 250; `minBatchSpacingMs` 0..60000 default 10000; `shutdownGraceSeconds` 0..120 default
    20; `model` string default `claude-sonnet-5` (documented as direct-Anthropic transport only —
    hosted Bedrock rotates its own haiku-first list); `maxOutputTokens` 64..2000 default 900;
    `llmTimeoutSeconds` 5..300 default 20; `player_connect_timeout_seconds` number default 180.
  - **`results_schema`** — required `names`, `scores`, `reputation`, `coin`, `published`,
    `trueTheories`, `falseTheories`, `burned`, `debunks`, `rounds`, `maxRounds`, `reason`; every
    array field `minItems`/`maxItems` **4**; `scores` numbers with no bound (they may be negative);
    `reason` a string documented as `complete` or `deadline`.
  - **`game.protocols`** — **both** entries, in full: `player` = the `cogchemists.player.v1` text
    from §Server (frame shapes, the redaction, the reply schema with its rune caps, the 4000-rune
    prompt cap, the `scripted` values, and "a policy is just a prompt: field one by reusing the
    published `cogchemists-player` runnable with `PLAYER_PROMPT` set to your strategy"); `global` =
    the `/global` snapshot shape, the six event kinds with their fields, and the note that the static
    replay bundle renders hosted replays at `index.html?replay=<url>`.
  - **`game.docs`** — `readme` (one paragraph: four cogs, eight ingredients, a secret bijection to
    eight signatures, six rounds of lab-then-market, publish for credit and royalties, debunk by
    public demonstration, the exhibition settles every standing seal, `score = reputation +
    0.2 × coin`, how to field a policy, and the two scripted baselines that make episodes always
    complete) and `pages`:
    - `rules.md` — the ingredient table, the signature notation, the mixing rule with its worked
      table, the numbered round/phase resolution, both action menus with every cost and reward, the
      debunk arithmetic with its two cases, the exhibition payoffs, the observation split, and the
      two endings.
    - `deduction.md` — what a fact is, the three fact kinds, how the grid is computed (exact
      enumeration over the 40 320 bijections), what "solved" means, and the information economics:
      what each action leaks to whom.
    - `scoring.md` — the formula and its sign, every reputation move in one table, the worked
      landmark (22.2), the do-nothing floor (13.2), and what the league ranks by (mean episode
      score).
  - **`player` runnables** — all `image: {{COGCHEMISTS_IMAGE}}`, `run: ["/bin/cogchemists-player"]`,
    requests `100m` cpu / `64Mi` memory, limit `1` cpu, each with `id`/`type`/`name`/`description`:
    `cogchemists-player` (the prompt policy, no `PLAYER_SCRIPTED`),
    `cogchemists-assayer` (`env.PLAYER_SCRIPTED = "assayer"`),
    `cogchemists-quack` (`env.PLAYER_SCRIPTED = "quack"`).
  - **`variants`** — both carry a `description` and **both carry `num_agents`: 4**:

    | id | name | description | `game_config` |
    |---|---|---|---|
    | `standard` | The Academy | Four cogs, eight ingredients, six rounds; seminar remarks allowed and artifacts on sale. | `players` ×4, **`num_agents`: 4**, `rounds`: 6, `talk`: true, `artifacts`: true, `turnDelayMs`: 250, `player_connect_timeout_seconds`: 180 |
    | `silent-academy` | Silent Academy | The same academy with no seminar: seats may not speak, so a wax seal and a public demonstration are the only ways to say anything. | `players` ×4, **`num_agents`: 4**, `rounds`: 6, `talk`: **false**, `artifacts`: true, `turnDelayMs`: 250, `player_connect_timeout_seconds`: 180 |

  - **`certification`** — `game_config`: `players` = `Sprocket`, `Gizmo`, `Ratchet`, `Widget`,
    **`num_agents`: 4**, `seed`: 11, `rounds`: **4**, `turnDelayMs`: 0, `minBatchSpacingMs`: 0,
    `player_connect_timeout_seconds`: 180; `certification.players` =
    `[cogchemists-player, cogchemists-assayer, cogchemists-player, cogchemists-quack]`.
    **Every declared player runnable occupies at least one slot** — a fixture of baselines-only fails
    `players_missing` the moment the manifest also declares a prompt runnable (raid 0.1.2,
    2026-08-23) — and the strong baseline (`assayer`) holds a seat that decides the fixture's
    outcome. With no credentials the prompt seats play `assayer` too, so the fixture is offline-safe.
    Four rounds is also what makes the smoke replay (**47 events ≈ 46 s of playback**) outlast the
    15 s viewer soak (ecos, 2026-08-23).
- **CI** — `.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
  substituting `<slug>` = `cogchemists`, `<IMAGE>` = `coworld-cogchemists`, **`<SEATS>` = `4`**.
  `tools/ci/docker_smoke.sh` (same substitutions, committed `chmod +x`), `tools/ci/viewer_smoke.mjs`
  copied **verbatim** (no substitutions), and `tools/ci/policies.json` listing the two LLM prompt
  champions phase 40 uploads — `cogchemists-empiricist` (champion #1, daveey) and
  `cogchemists-careerist` (champion #2, carrying
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` so daveey-1 owns it) — plus the two scripted
  fillers `cogchemists-assayer` (`PLAYER_SCRIPTED=assayer`) and `cogchemists-quack`
  (`PLAYER_SCRIPTED=quack`). Both champions are `PLAYER_PROMPT` policies; a scripted champion is a
  failure state.

### Design pins (playbook §Phase 0) — how each is satisfied

| Pin | Where |
|---|---|
| Starter chosen by game shape | `cogame-bullwhip` — turn-based, simultaneous, hidden-information, competitive, LLM-prompt policies, one batched round trip per turn (title paragraph). |
| Public `Metta-AI/cogame-cogchemists` | Repo created **public** in phase 20 (a certification prerequisite); `source_url` points at it. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `cogchemists-player` (`PLAYER_PROMPT`) vs `cogchemists-assayer` / `cogchemists-quack` (`PLAYER_SCRIPTED=…`), one image, two entrypoints (§Decisions, §Packaging). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; the wasm module re-derives every frame and every grid in the browser; nothing but S3 is contacted (§Viewer). |
| Real art; starter chrome reused verbatim | `chrome.css` byte-for-byte + one appended block; `replay.html` / `index.html` = the starter's page + one appended element, **nothing removed**; every chrome function kept; sprites and floor from `data/` (§Viewer). |
| Legible to a casual spectator | `RED+`, `Nightcap`, `SEAL BURNED`, `rep 13`; the 360 px layout is specified (§Viewer). |
| Two name spaces | Anonymous cog aliases in-game; `policyNames` + `makeNameMap` spectator-side only (§The game). |
| Degrade never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6`, pre-batch deadline check, `endEarly()` runs the exhibition, `sampleEpisode` fitting; ceiling **≈663 s**, typical ≈192 s (§Decisions). |
| `num_agents` in every variant AND the cert fixture | **4** in `standard`, in `silent-academy`, in `certification.game_config`, and `<SEATS>` = 4 in `tools/ci/docker_smoke.sh`. |
| Upload policies before `upload-coworld`, secret after; distinct filler versions | Phase 40 dispatch order is the template's; `tools/ci/policies.json` mints four distinct policies (§Packaging). |

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` twice, debug and `-d:release`.

### `tests/test_chem.nim` (the chemistry, unit)

1. **The mixing rule, exhaustively** — all 28 unordered signature pairs: `mixSignatures` is
   symmetric; exactly **2** pairs produce each of the six coloured potions and **16** produce MUD;
   the five worked examples in §The game reproduce exactly; a signature mixed with itself is MUD.
2. **Notation** — `sigName` round-trips through `parseSignature` for all 8; `R+G-B+`, `+-+` and
   `+ - +` parse to the same index; `R+G-`, `+++-`, `""` and `"RGB"` return −1.
3. **The solver is exact** — for 200 random fact sets, `solveGrid`'s candidate set for each
   ingredient equals the set computed by brute-force enumeration of the 40 320 bijections filtered by
   the same facts (an independent implementation in the test), and `chemistries` equals the count;
   an empty fact set gives all 8 candidates everywhere and `chemistries == 40320`; a contradictory
   fact set gives `chemistries == 0` and empty candidate sets (and the sim never constructs one).
4. **Facts constrain the truth** — for 50 seeds, the episode's own chemistry is always among the
   consistent ones for every seat at every phase (no seat is ever "deduced" out of the truth).
5. **Performance** — a full grid solve with 40 facts completes in under 25 ms native, and the
   memoised per-phase refresh for a 10-round episode totals under 400 ms, so the wasm viewer's
   whole-replay re-derivation stays under a second.

### `tests/test_sim.nim` (sim unit tests)

6. **Setup** — for seeds `[0,1,7,11,42,1234]`: the chemistry is a **bijection** (8 distinct
   signatures); every seat starts on coin 4, reputation 10 and exactly 3 cards; `demand` has one
   coloured (never MUD) potion per round; `events == [start, round, phase]`; `pendingSeats().len == 4`;
   aliases are distinct.
7. **Determinism** — the same seed reproduces the chemistry, demands, aliases and every draw exactly;
   a different seed differs in at least one; across 20 seeds the chemistry varies.
8. **Initiative** — `initiativeOrder(r)` is a permutation of `0..3` for every `r`; over 8 rounds each
   seat leads exactly twice; the order is `(i + r) mod 4`.
9. **Lab actions, by hand** — `forage` draws exactly 2 and never exceeds `HandCap` (the overflow is
   discarded and recorded); `test_student` costs 1 coin, consumes both cards and mints a **private**
   `mixFull` for the actor and **no** public fact; with the Mortar it consumes only `a`;
   `test_self` costs 0, mints a private `mixFull` **and** a public `mixSign`, and moves reputation by
   `+1 / 0 / −2` for positive / mud / negative; `transmute` pays 2 and consumes one card; `pass`
   pays 1.
10. **Market actions, by hand** — `sell` hit pays 6 coin +1 rep and miss pays 2 coin −1 rep, consumes
    both cards and always mints a **public** `mixFull`; `publish` costs 1, pays +2 (+3 with the
    Press), pins a standing seal, and is illegal on an ingredient that already carries one;
    `endorse` moves 1 coin from endorser to author and is illegal on your own seal, on a burned seal,
    and twice; `buy` is illegal when already owned or unaffordable; every action costing coin a seat
    lacks is absent from `legalMoves`.
11. **Debunk, both cases** — a seal whose claim mispredicts the demonstration **burns**: author −4,
    debunker +3, each endorser −1, status `burned`, a public `notSig` fact minted, the ingredient
    publishable again, and the demonstration's potion public; a claim that predicts the demonstration
    correctly (including a *wrong* claim this reagent cannot expose — a case the test constructs
    explicitly) leaves the seal standing with debunker −2 and author +1 and `vindications` + 1.
12. **Same-phase conflicts** — two seats publishing the same ingredient: the earlier initiative wins,
    the later is `rejected:already_claimed` and takes the pass stipend; a debunk of a seal burned
    earlier in the same phase is `rejected:no_such_theory`; an endorse of the same seal by the same
    seat twice is `rejected:already_endorsed`; every rejection still emits an `act` event with
    `result` set and leaves the sim legal.
13. **The exhibition** — a standing true seal pays author +5 and endorsers +2; a false one −6 and −3;
    a burned seal is **not** re-scored; a `deadline` exhibition after 2 of 6 rounds scores exactly
    the seals standing at that moment; the `exhibition` event carries the full chemistry.
14. **Rune truncation** — a 400-rune multi-byte `say` (`"é" × 400`) truncates to **140 runes** and a
    400-rune `notes` to 600 unchanged / an 800-rune one to **600**; every `say`, `text` and error
    string in the event log satisfies `validateUtf8() == -1`; with `talk = false` every `say` is `""`.
15. **wasm integer width** — over a maximal 10-round episode no `coin`, `reputation`, `chemistries`
    or event integer exceeds 100 000, so 32-bit `int` on wasm32 cannot diverge from the native run
    (contagion, 2026-08-23).
16. **Observation split** — for every frame of a seeded 4-round episode, each seat's
    `observationJson` and the built prompt string contain **no** other seat's hand, private facts,
    notes, grid or `chemistriesLeft`, and no signature of the true chemistry that the seat's own
    facts do not already imply; and the **converse**: every referent the reply schema can name (each
    card in its hand, each ingredient name, each standing seal, each artifact it can afford) appears
    verbatim in `LEGAL MOVES`.
17. **Replay** — `replayMatch(config, events).len == events.len + 1`; the final frame's
    `tableStateJson` equals the live one; `eventFromJson(eventToJson(e))` round-trips one event of
    **every** kind (`start`, `round`, `phase`, `act`, `exhibition`, `end`) field by field; a tampered
    `start.chemistry`, a tampered `draws` array and a tampered `round.demand` each raise
    `CogchemistsError`; a `deadline` ending recorded between phases re-derives as `deadline`, not
    `complete` (tribunal, 2026-08-23); all four grids in the re-derived frames equal the live ones.
18. **Endings** — a full episode ends `complete` with `roundsPlayed == rounds`,
    `events[^1].kind == evEnd`, `events[^2].kind == evExhibition`, and any further `applyAct` raises;
    `endEarly()` mid-episode gives `deadline`, runs the exhibition exactly once, and is a no-op when
    called twice; `results.reason` is only ever `complete` or `deadline`.

### `tests/test_bot.nim` (bounded-orders / legality assertion on the scripted baselines)

19. **Legality and boundedness** — for seeds `[1,7,11,42]` × `{all-assayer, all-quack, mixed}`, a full
    scripted episode completes `complete` and: `applyAct` never raises; **every scripted action is a
    member of `legalMoves(sim, seat)` at the moment it is played** (the bounded/legal assertion); no
    coin ever goes negative; no hand ever exceeds `HandCap`; every named card is actually held; no
    seat publishes an ingredient that already carries a standing seal; scripted seats emit empty
    `say` and `notes`; and the whole episode runs in under 2000 ms.
20. **Baseline behaviour** — `assayer` publishes only ingredients its own grid has **solved** (zero
    false theories across all seeds, asserted); `quack` publishes at least one unsolved guess per
    episode and is burned or proved false at least once across the seed set; an all-`assayer` table's
    mean score is strictly greater than an all-`quack` table's on the same seed, and the test echoes
    both numbers so tuning drift is visible.
21. **Fallback** — with no credentials `newLlmClient(config).disabled` is true, `decideAll` returns
    scripted actions for all four seats with **no network call**, and the batch-spacing floor is
    skipped (asserted on wall clock: a disabled 6-round episode finishes in under 5 s).
22. **Reply parsing** — the documented shapes all parse; `action`/`a`/`b`/`signature`/`artifact`/
    `say`/`notes` are capped at their rune limits; ingredient prefixes, indices and case variants
    resolve; a wrong-phase action, an unresolvable ingredient, a malformed signature and an
    unaffordable action are all **invalid** (retryable, then scripted), and trailing prose after the
    JSON object is tolerated.

### `tests/test_score.nim`

23. **Scoring** — `score == reputation + 0.2 × coin` on a hand-built episode; the §The game landmark
    reproduces **22.2** to 1e-9; the all-pass seat reproduces **13.2**; a seat with one false
    standing seal scores 11 lower than the same seat with a true one (`+5` vs `−6`); `resultsJson`
    has 4 entries in every array and `reputation`/`coin` agree with the final frame.

### `tests/test_viewer.nim`

24. **Chrome provenance and scope** — `client/chrome.css` byte-matches the starter's file up to the
    appended `/* ---------- Cogchemists ---------- */` banner; `client/replay.html` and
    `replay-viewer/index.html` both contain **every** starter element id listed in §Viewer; no
    top-level `function` or `var` in the appended game block shares a name with anything the chrome
    defines above it (tandem, 2026-08-23); the appended CSS defines a rule for each of the **seven**
    beat kinds the scrubber can emit (`publish`, `debunk`, `sell`, `test`, `trade`, `exhibition`,
    `end`).

### End-to-end, replay and viewer (CI jobs)

25. **`docker-smoke`** (`tools/ci/docker_smoke.sh`, `<SEATS>` = **4**) — builds the production image
    from the freshly-built binaries (never a cached one — bullwhip, 2026-08-22) and runs **one real
    episode** in raw docker with the certification fixture's four-seat mix and no
    `ANTHROPIC_API_KEY`, asserting the game exits 0 having written `results.json` and a replay, that
    **every player container also exits 0** (raid 0.1.3, 2026-08-23), that `num_agents` = 4 agrees
    across `certification.game_config`, `len(certification.players)`,
    `len(certification.game_config.players)` and `SMOKE_SEATS`, and that `results.names` /
    `results.scores` have 4 entries and `results.reason == "complete"`. The replay is copied to
    `dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.
26. **Strict-UTF-8 replay parse** — the same script decodes the replay bytes as **strict UTF-8** and
    parses them as JSON (`SMOKE_REQUIRE_REPLAY_JSON=1`, the default); test 14 covers the multi-byte
    truncation path that would otherwise break it.
27. **Viewer smoke** — `ci.yml`'s **`wasm-viewer`** job (`needs: docker-smoke`) builds the bundle with
    `tools/build_replay_viewer.sh` (asserting the hook is a file and `os.X_OK`, and invoking it by
    path), downloads the `smoke-replay` artifact and **executes** the bundle in headless Chromium:
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json
    --timeout 90 --soak 15`. It passes only when the page sets `data-replay-loaded="true"` (or posts
    the `coworld-replay` `ready` envelope), never sets `data-replay-error`, the `#clock` / `#scorebug`
    readouts **differ** across the 0 % / 50 % / 100 % scrub positions, and uninterrupted playback
    keeps advancing through the soak window (cogball 0.1.4, 2026-08-23; the 47-event fixture is ≈46 s
    of playback, so the soak cannot false-negative). `viewer-smoke.png` and `viewer-smoke.json` are
    uploaded on success and failure alike. **The bundle is executed, not merely built.**

---

## Out of scope (v1)

- Any seat count other than 4, spectator seats, or seats joining or leaving mid-episode.
- Alchemists' actual worker-placement board, action-space bidding, turn-order auctions, the herbalist,
  the shop's variable artifact market, favour cards, grants, and the adventurer *hero* track — the
  port keeps the deduction, the publication economy and the debunk, and drops the euro-game
  furniture.
- Signature **sizes** (Alchemists' big/small aspects) and any potion outcome outside the seven
  values: the algebra is signs only, so that a spectator can hold the whole rule in their head.
- Ingredient scarcity: the supply is an unbounded seeded stream, there is no market for cards, and
  ingredients cannot be traded, gifted or stolen between seats.
- More than the two artifacts, artifact resale, artifact victory points, or any artifact that changes
  the chemistry or the mixing rule.
- Enforceable agreements of any kind: `say` is cheap talk by construction, endorsement is the only
  binding co-signature and it binds only its signer's score.
- Partial or hedged theories ("Nightcap is RED-positive, I make no claim about green"), joint
  publications, retractions, and re-publishing a seal you burned yourself in the same episode.
- Any second LLM pass to interpret a reply the schema cannot read: the schema is the whole parser, it
  runs in the wasm viewer too, and its determinism is what makes replays re-derivable.
- Cross-episode memory or reputation carry-over; the chemistry is re-drawn every episode and nothing
  survives an episode boundary.
- Scoring on anything but reputation plus 0.2 × coin — no bonus for solved ingredients, no penalty
  for unread replies beyond the scripted fallback that replaces them.
- Real-time play, an RL vector observation, and a live-server (`/client/replay`) replay viewer.
- Localisation, audio, a zoom/minimap panel, and any viewer feature beyond the lab-table stage, the
  theory board, the hole-cam grid strip and the endcard reveal described above.
