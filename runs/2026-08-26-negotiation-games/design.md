# Negotiation Games: a three-seat bargaining table

Built on **`cogame-babel`** (`Metta-AI/cogame-babel`, read at `/workspace/starters/cogame-babel`,
version 0.1.4) — the parley→cosino→focus→babel lineage: a Nim game server implementing the
Coworld runtime contract, **a policy is just a prompt**, an always-available scripted baseline,
one pure `sim` module shared by server / tests / wasm viewer, and the parley broadcast chrome
around a canvas stage. Babel is chosen by game shape: this is a turn-based, hidden-information,
talk-and-offer game whose logic is native and whose policies are LLM prompts — row 1 of the
starter table, and babel is the newest full member of that lineage that ships every piece this
game needs (per-seat hidden info, private notes fed back verbatim, redacted player frames, a
static wasm replay viewer). **Every convention there holds here unless this note says
otherwise.**

Source idea, verbatim:

```
Merged port of OpenSpiel's negotiation family. Bargaining (Lewis et al. 2017 / DeepMind): split a pool of books/hats/balls; each side has private values; alternating offers, ten turns, agree or both get zero. Colored Trails: 3 players on a coloured board need chips of matching colours to reach goals; one round of proposals to trade chips. Trade Comm: two players each hold an item and can send a message then propose a trade that only works if both want it. Sheriff: a smuggler chooses how much contraband to bring and bribes the sheriff over several rounds of cheap talk — a correlated-equilibrium testbed.

Seats: 2-3
Motive: mixed-motive negotiation with private information
Policy interface: structured offers (+ optional free text); LLM prompt natural — but the STRUCTURED offers are the graded channel
Fills gap: 21 Garble is noisy trade, MP Fruit Market is spatial trade; these are the clean textbook negotiation benchmarks with known equilibria — good for calibrating 'how well do cogs bargain'
Integrity (anti-collusion): valuations seeded per episode; anonymous aliases; 3-seat Colored Trails softplay audited.

Replay plan (watchability): both sides' hidden valuations visible to spectators so every offer reads as generous or greedy; deal/no-deal stamp.

Source: OpenSpiel bargaining, colored_trails, trade_comm, sheriff.
```

**Phase 0 pins, answered** (`playbooks/make-coworld.md` §Phase 0):

| Pin | How this design satisfies it |
|---|---|
| Starter by game shape | `cogame-babel` — turn-based hidden-information game, native rules, policy = prompt (§The game, first paragraph). |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-negotiation-games`, public at creation (phase 20). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (two champion prompts, given verbatim in §Decisions) and `PLAYER_SCRIPTED=haggler` / `PLAYER_SCRIPTED=hardliner` (two baselines, algorithms given in §Decisions). One image, two binaries. |
| Static wasm replay viewer, never a pod | `game.replay_viewer.bundle = "static-replay-viewer"`, hook `tools/build_replay_viewer.sh`, all four viewer files from cogame-babel (§Viewer, §Packaging). No `/client/replay` live-server viewer is ever declared. |
| Real art, starter chrome verbatim | babel's `data/` sprites, floor and font shipped unchanged; items drawn with canvas primitives, never text labels; `client/chrome_common.js` copied byte-for-byte from babel's chrome half with three named exceptions; `client/replay_broadcast.html` is babel's page with a game block appended (§Viewer). |
| Two name spaces | anonymous cog aliases in-game (`CogNames`, seeded); policy names only in `results.names`, `replay.policyNames` and the spectator/replay name map. A test greps every composed prompt for every policy name (§Tests). |
| Degrade, never hang; play inside 60 % of 1200 s | play deadline = `0.6 × episodeTimeoutSeconds` = 720 s, checked before every model call; past it the current match is finished by the scripted baseline and the episode settles `deadline`. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant AND the cert fixture | **`num_agents` = 3**, literally in variant `standard`, variant `sprint`, and `certification.game_config` (§Packaging). `SMOKE_SEATS=3`. |

No item is left OPEN: every rule the idea leaves loose (seat count, which games ship in v1,
scoring normalisation, turn cap, caps on free text) is decided below.

## The game

**Three cogs at a negotiation table. In each match two of them split a pool of books, hats and
balls that is worth exactly 10 points to each of them — under private, different per-item
values — by alternating offers. Agree and you both bank what you took; run out of turns and
you both bank nothing.**

**Seats: exactly 3 (`num_agents` = 3).** One number, everywhere. Reason: 3 is the largest seat
count in the idea's `Seats: 2-3` range, it lets every episode run a full round-robin of
pairings (each seat meets both opponents, which halves the variance of a single head-to-head
league episode), and it is the seat count Colored Trails needs — fixing it at 3 now means the
v1.1 Colored Trails match kind lands without a manifest seat-count change (a seat-count change
invalidates cert fixtures, `SMOKE_SEATS`, and every uploaded variant).

**Which games ship in v1: Bargaining only** (Lewis et al. 2017 / DeepMind; OpenSpiel
`bargaining`). Colored Trails, Trade Comm and Sheriff are listed in §Out of scope (v1) with the
exact shape each will take. Reason: the idea names Bargaining first and it is the anchor
benchmark; one negotiation game specified to the last integer beats four specified loosely, and
the schedule record already carries a `kind` field (v1 value: `"bargaining"`) so a second match
kind is an additive change, not a replay-protocol bump.

### Structure

- An episode is a sequence of **matches** (`matches`, default 6, legal values 3 or 6; cert
  fixture 3). Matches are played one at a time, in order — never concurrently — so a spectator
  always has exactly one table to watch.
- Match `m` (0-based) is played by the pairing `P[m mod 3]` where
  `P = [(0,1), (0,2), (1,2)]`. The **opener** (the seat that moves on turn 1) is the first seat
  of the pairing when `(m div 3) mod 2 == 0`, otherwise the second. Over 6 matches every seat
  plays exactly 4 matches and opens exactly 2 of them. The third seat **sits out** that match:
  it is never queried (zero model calls), never sees the match's pool, values, offers or
  messages, and its tallies do not move.
- A match lasts at most `maxTurns` turns (default 10, legal 2..12, even so both seats get the
  same number of turns; cert fixture 6). Turn `t` (1-based) is taken by the opener when `t` is
  odd, by the other seat when `t` is even.

### The pool and the valuations (drawn from the seed, per match)

Item types are fixed and ordered: **`["books", "hats", "balls"]`** (indices 0, 1, 2).

For each match, `initSim` draws, in this exact order, from the single seeded RNG stream:

1. **Counts** `c[0..2]`, each `1 + rng.rand(3)` (so 1..4). Redraw the whole triple until
   `c[0]+c[1]+c[2] ∈ [5, 7]`, at most 32 attempts; on the 33rd, use `c = [3, 2, 2]`. (Bounded:
   generation can never spin.)
2. **The value table** `V(c)` = every `v ∈ {0..10}³` with `c[0]·v[0] + c[1]·v[1] + c[2]·v[2] == 10`,
   enumerated in lexicographic order (≤ 1331 candidates; the enumeration is exhaustive and
   deterministic, so no rejection loop exists).
3. Seat A's values `vA = V[rng.rand(V.high)]`; then seat B's values `vB = V[rng.rand(V.high)]`,
   redrawn at most 16 times until `vA[t] + vB[t] > 0` for every `t` (no item is worthless to
   both). If 16 redraws fail, take the first element of `V` satisfying the condition; if none
   exists, keep the last draw. (Bounded, and always yields a legal table.)

Consequences pinned by construction: the whole pool is worth exactly **10** to each seat; the
two seats' values differ in general (integrative trades exist) but may coincide (a purely
distributive match is legal); no item type is worthless to both seats. Values are **redrawn
every match**, so nothing a seat learns about one opponent's values transfers to the next
match — that is the anti-collusion pin the idea asks for, together with the anonymous aliases.

### Actions — the graded channel

On its turn a seat takes exactly one of two actions:

- **`offer`** — a `take` vector: how many of each item **this seat** takes. Legal iff
  `0 ≤ take[t] ≤ c[t]` for every `t`. The opponent gets the complement `c[t] − take[t]`.
- **`accept`** — accept the standing offer (the offer made on the previous turn). Legal iff a
  standing offer exists, i.e. `t ≥ 2`. `accept` on turn 1 is illegal.

Both actions may carry an optional free-text `message` (cheap talk, seen by the opponent) and
optional private `notes`. **Only the structured `take`/`accept` is graded**; the message is
flavour and is never enforced by the rules.

### Resolution order (exact, numbered)

Per episode:

1. `initSim(config)` draws, from `seed`: the seat aliases (babel's `tableNames`), then for each
   match in order the pairing, the opener, the counts, and both seats' values. The whole
   schedule is fixed before a single decision is made, so a replay re-derives it from the seed.
   Emit `start`.
2. The server waits up to `player_connect_timeout_seconds` (default 180) for all 3 player
   sockets, then starts regardless (a missing seat plays with an empty operator block).
3. For each match `m` in `0 ..< matches`:
   1. If `now > playDeadline`: call `endEarly()` (reason `deadline`) and go to step 4. The
      deadline is only honoured **between** matches and **before each model call**, never
      mid-application.
   2. Emit `match` (index, kind `"bargaining"`, the two seats, opener, `pool`, both seats'
      `values`, `maxTurns`). Broadcast.
   3. For `t` in `1 .. maxTurns`, with `actor` = opener if `t` is odd else the other seat:
      1. Snapshot the sim under the lock; read the actor's prompt and its scripted-baseline
         name; compute `pastDeadline = now > playDeadline`.
      2. If the seat is registered scripted **or** `pastDeadline` **or** the LLM client is
         disabled: take the scripted action (§Decisions) — instant, no network. Otherwise sleep
         until at least `MinCallSpacingMs` (2200 ms) has elapsed since the previous model call
         began, then ask the model (one call; on an invalid reply, one retry with a hint; on a
         second failure, the scripted action for that seat).
      3. Apply under the lock. `applyOffer(match, take, message, notes, scripted)` records the
         offer as the standing offer and emits `offer`. `applyAccept(match, message, notes,
         scripted)` computes both payoffs and emits `accept`.
      4. If the action was `accept`: emit `matchEnd` with `outcome: "deal"`, `payoff: [uA, uB]`,
         `turns: t`; add the payoffs to both seats' tallies; leave the turn loop.
      5. If `t == maxTurns` and the action was an `offer`: emit `matchEnd` with
         `outcome: "no_deal"`, `payoff: [0, 0]`, `turns: maxTurns`; both seats bank 0 for this
         match; leave the turn loop.
      6. Broadcast after every applied action.
   4. Sleep `turnDelayMs` (default 900, cert 0) for spectator pacing, bounded by
      `PacingBudgetMs` = 20 000 ms across the episode.
4. When the last scheduled match has a `matchEnd`, `settle("complete")`; emit `end` with
   `text = reason` and `match = matchesPlayed`.
5. `finishEpisode`: final frames to the player sockets first, then `results.json`, then the
   replay, then a **20 s shutdown grace** during which `/healthz`, `/global` and the
   `/client/*` routes keep answering (the certifier pings `/global` after the player pods
   start — cogame-lantern 0.1.3), then `quit(0)`.

**Invariant, tested:** every match that emitted a `match` event also emits exactly one
`matchEnd` event. The deadline never abandons a match half-played — past the deadline the
remaining turns are decided by the scripted baseline, which costs microseconds.

### Scoring — formula, sign, what the league ranks

For a settled match, seat `s` receives `recv[t] = ` its share of each item type and banks

```
u(s) = Σ_t recv[t] · v_s[t]          integer, 0..10        (0 for a no-deal)
```

Over the episode:

```
points[s]        = Σ over the matches s played of u(s)                 integer, 0..10·matches
matchesPlayed[s] = number of matches s played that reached a matchEnd  (4 of 6 in the default)
deals[s]         = those that ended "deal"
score[s]         = points[s] / (10 · matchesPlayed[s])                 float in [0, 1]
                 = 0.0 when matchesPlayed[s] == 0
giveaway[s]      = mean over settled matches of (opponent's u − s's u)  float in [-10, 10]
```

**Sign: higher is better.** `score` is a share of the pie, so 1.0 = took the whole pool in every
match, 0.0 = no deal in every match (or every deal worth nothing to it). **The league ranks
seats by mean episode `score`, descending** (Elo 1000/32 over that). `giveaway` is not ranked —
it is the mechanical softplay audit the idea asks for: a seat that systematically hands the pool
to a partner shows a large positive `giveaway` with a low `score`, which is visible in results
without any human watching.

There is no discount for stalling. The only pressure is the `maxTurns` cliff, exactly as in the
source (`agree or both get zero`).

### End conditions and `results.reason`

Exactly two values are legal in `results.reason`, and nothing else may ever be written there:

- **`complete`** — all `matches` scheduled matches reached a `matchEnd`.
- **`deadline`** — the play clock (60 % of `episodeTimeoutSeconds`, or of
  `COWORLD_TIMEOUT_SECONDS` when the platform provides it) stopped play between matches. Scores
  use the matches actually settled; unstarted matches are simply absent.

A match-level outcome is a separate enum carried by the `matchEnd` event: **`deal`** or
**`no_deal`**. It never appears in `results.reason`.

### Per-seat observation — visible vs hidden

Visible to the acting seat, in its prompt (§Decisions has the literal text):

- its own alias, the opponent's alias, `match m of M`, `turn t of maxTurns`;
- the pool counts per item type, and **its own** private values per item type, with the reminder
  that the whole pool is worth 10 to it;
- the standing offer against it, rendered from its own side (`they take …, you get …`) **with
  the worth to itself computed for it**, plus the explicit line `ACCEPT IS LEGAL NOW: yes|no`
  and the explicit per-type bounds `0..c[t]` (precomputing the legal set in the observation is
  the escrow 0.1.3 fix for formal-output fallback rates);
- the full offer history of **this** match, both sides, each with its worth to this seat, and
  each side's messages;
- its own record so far this episode (per settled match: opponent alias, deal/no-deal, `u/10`);
- its own private notes, fed back verbatim.

Hidden from the acting seat, always:

- the **opponent's private values** (and any function of them);
- the opponent's notes;
- everything about matches the seat is not in — including, for the sitting-out seat, that a
  match is even in progress beyond its index;
- the seed, the schedule of future matches, the policy names of any seat (including its own).

Hidden in-game but **written to the replay for spectators**: both seats' private values (the
idea's watchability plan — every offer reads as generous or greedy), every seat's notes, and the
`scripted` flag on every action.

## Decisions: LLM with scripted fallback

Transport, credential resolution (Bedrock sidecar → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI`), the "no credentials ⇒ every seat scripted, immediately, no network
wait" rule, `bedrockModelIds()` (haiku first), `extractJsonObject`, `completeText`, the
`max_tokens` / refusal / 401 / 403 / 429 handling, `cleanNotes`' rune-safe truncation and the
retry-once-then-fallback shape of `decide` are ported from `cogame-babel/src/babel/llm.nim`
**unchanged**. `maxOutputTokens` stays 900; `llmTimeoutSeconds` drops from 45 to **30** (tail
control, see the budget below).

### The model call

**System prompt** (one per seat per match; `<>` are substitutions):

```
You are <alias>, a cog at a three-seat negotiation table. Right now you are bargaining
one-on-one with <opponent alias>.

Rules:
- A pool of items sits between you: <c0> books, <c1> hats, <c2> balls. The whole pool is
  worth exactly 10 points to you, and exactly 10 points to your opponent - but the
  per-item values are DIFFERENT and PRIVATE. You know yours. You will never be told
  theirs, and they are never told yours.
- You take turns. On your turn you either make an OFFER - exactly how many of each item
  YOU take, your opponent getting the rest - or ACCEPT the offer standing against you.
- The match is at most <maxTurns> turns long, yours and theirs together. If nobody has
  accepted when the turns run out, the deal fails and BOTH of you score zero for this
  match.
- Your score for this match is the value TO YOU of the items you end up with, out of 10.
  No deal is 0. Waiting costs nothing except turns, and turns are the only thing you
  cannot get back.
- You may attach a short message of at most 200 characters. Your opponent reads it. It is
  cheap talk: nothing you say is enforced. The OFFER is the only binding channel, and it
  is the only thing you are graded on.
- Your notes are private, are handed back to you on your next turn, and are never shown
  to your opponent.

OUTPUT FORMAT: reply with ONLY one JSON object, nothing else - no analysis, no
explanation, no markdown fences, no text before or after the object. Your reply must
begin with the character { and end with }.
```

**User prompt** (blocks in this order; blocks in brackets are omitted when empty):

```
MATCH <m+1> of <M>. TURN <t> of <maxTurns>. You are <alias>; your opponent is <opponent>.

THE POOL: <c0> books, <c1> hats, <c2> balls
YOUR PRIVATE VALUES: books <v0> each, hats <v1> each, balls <v2> each (the whole pool = 10 to you)

THE OFFER STANDING AGAINST YOU: <opponent> takes 2 books, 0 hats, 1 ball; you get
1 book, 2 hats, 0 balls - worth 4 to you.
     [or, on turn 1:]  NO OFFER YET - you open.
ACCEPT IS LEGAL NOW: yes
[TABLE TALK FROM <opponent>: "..."]

THIS MATCH SO FAR:
  Turn 1 - you offered: you take 3 books, 2 hats, 1 ball (worth 10 to you). "..."
  Turn 2 - <opponent> offered: you get 1 book, 2 hats, 0 balls (worth 4 to you). "..."
     [or:]  (nothing yet)

YOUR RECORD THIS EPISODE:
  Match 1 vs Ratchet - DEAL, you scored 6/10.
  Match 2 vs Gizmo - NO DEAL, 0/10.
     [or:]  (no matches settled yet)

YOUR NOTES FROM EARLIER TURNS:
<notes, or "(none)">

GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply
in the requested format):
<PLAYER_PROMPT>

Reply with ONLY {"action":"offer","take":{"books":0,"hats":0,"balls":0},"message":"...",
"notes":"..."} or {"action":"accept","message":"...","notes":"..."} - books 0..<c0>,
hats 0..<c1>, balls 0..<c2>, whole numbers only; message at most 200 characters; notes
at most 400 characters.
```

### Reply schema and its caps

```json
{"action": "offer",  "take": {"books": 2, "hats": 0, "balls": 1},
 "message": "≤ 200 characters", "notes": "≤ 400 characters"}
{"action": "accept", "message": "≤ 200 characters", "notes": "≤ 400 characters"}
```

Parsing (`parseAction`), tolerant in exactly these ways and no others:

- `action` is matched case-insensitively after trimming: `accept | agree | deal` → accept;
  `offer | propose | counter` → offer. If `action` is absent but `take` is present → offer.
- `take` may be the object above (missing keys default to 0) **or** a 3-element array
  `[books, hats, balls]`. Entries may be JSON integers or integer-valued strings.
- Anything else — a non-integer count, an out-of-range count, `accept` on turn 1, an unknown
  action, no JSON object in the reply — is an **invalid reply**.
- Legality is checked by applying the decision to a probe copy of the sim before returning it
  (babel's pattern), so an out-of-bounds `take` is caught in `decide`, not in the game loop.

**Character caps.** `message` ≤ **200** characters, `notes` ≤ **400** characters. Both are
measured and cut in **runes**, never bytes (`runeLen` / `runeSubStr`, babel's `cleanNotes`), with
a trailing `…` marking the cut; the cap applies to every string that reaches the replay
(`message`, `notes`, and any error text quoted into a log line). A byte-boundary cut is what
makes replay bytes fail a strict JSON parser while still rendering in a browser — §Tests pins
it. ASCII control characters other than space are stripped from `message` before the cap.

### Degrade, never hang

1. Invalid or illegal reply → **retry once**, same prompts plus one appended line:
   `Your previous reply was invalid. Respond with ONLY the requested JSON object: either
   {"action":"accept",...} or {"action":"offer","take":{...}} with every count inside the
   bounds shown.`
2. Second failure, a transport error, a timeout (`llmTimeoutSeconds` = 30), a refusal, or
   disabled credentials → the seat's **scripted action**, applied with `scripted: true`, and
   `results.fallbacks[seat]` incremented. The scripted action is always legal, so the turn
   always advances.
3. The fallback baseline for a seat is the one named by its `PLAYER_SCRIPTED` value; a seat that
   registered a prompt (or nothing) falls back to **`haggler`**.
4. Past the play deadline every remaining turn of the current match is scripted (instant), the
   match settles, and the episode ends `deadline`. No wait anywhere in the game loop is
   unbounded: the connect wait is capped, the model call is capped, the pacing sleeps are capped
   by `PacingBudgetMs`, and the shutdown grace is a fixed 20 s.

### Both policies, same image, env-switched

`/bin/negotiation-player` is the only player binary. `PLAYER_PROMPT="<strategy>"` makes the seat
LLM-driven; `PLAYER_SCRIPTED=haggler` or `PLAYER_SCRIPTED=hardliner` makes it scripted
(`1|true|yes` is accepted and means `haggler`, for compatibility with the lineage). The two
**champions are prompts**, the two **fillers are scripted** (SPEC §Design pins).

**Champion #1 — `negotiation-games-anchor`** (owner daveey), `PLAYER_PROMPT`:

```
Open by taking everything and say why: name the one item you claim to need most. Concede
in small steps, one item at a time, and always concede the item that is worth least to you
per unit - never the item you value most. Track what your opponent keeps asking for; that
is what they value, so charge them for it and take the rest. Accept when the standing offer
is worth 6 or more to you, or when three or fewer turns remain and it is worth 4 or more.
On the last turn available to you, accept anything worth 1 or more: a deal you dislike
still beats the zero that both of you get when the turns run out.
```

**Champion #2 — `negotiation-games-integrative`** (owner daveey-1), `PLAYER_PROMPT`:

```
The pool is worth 10 to each of you, but you value different things, so there is almost
always a split that beats a 50/50 hack. Say plainly and honestly, in your first message,
which item type matters most to you and which you barely care about, and ask them for the
same - truthful cheap talk is how you find the trade. Then offer: take all of the item you
value most, give away all of the item you value least, and split the rest. If their counter
contradicts what they said, believe the counter. Accept the standing offer when it is worth
7 or more, or when it is worth 5 or more and fewer than four turns remain. Never let a match
end with no deal: on your final turn accept anything worth 1 or more.
```

**Filler #1 — the `haggler` baseline** (a monotone concession bot; also the universal fallback):

Let `t` be the current turn, `T = maxTurns`, `worth(x) = Σ x[i]·v[i]` for this seat's values.

1. Reservation: `R(t) = clamp(round(10.0 - 6.0 · (t - 1) / max(T - 1, 1)), 4, 10)` — 10 on turn
   1, decaying linearly to 4 on turn `T`.
2. Endgame override: if `t > T - 2` (this seat's last turn of the match), `R(t) = 1`.
3. If a standing offer exists and `worth(complement of the standing take) ≥ R(t)` → **accept**.
4. Otherwise build an offer: enumerate every `take ∈ {0..c0}×{0..c1}×{0..c2}` (≤ 125 candidates),
   keep those with `worth(take) ≥ R(t)`, and choose the one with the **smallest** `worth(take)`;
   ties broken by the **fewest total items taken**, then by lexicographically smallest vector.
   (Taking the whole pool always satisfies the filter, so the set is never empty.)
5. Never emits a message; never emits notes; uses no RNG (fully deterministic given the sim).

**Filler #2 — the `hardliner` baseline** (a stubborn bot, so the league has a real spread):

Identical to `haggler` except for the reservation: `R(t) = 8` while `t ≤ T - 2`, and `R(t) = 3`
on this seat's last turn of the match. It therefore refuses most splits, gets its way against a
conceder, and drives genuine no-deals against another hardliner — the two baselines are not
interchangeable, and §Tests asserts the gap.

### Episode budget, arithmetic out loud

- No turn in v1 is simultaneous: Bargaining alternates strictly, so exactly one seat is queried
  at a time and there is nothing to batch. (When Colored Trails lands, its one proposal round
  **is** simultaneous for all three seats and must go out as **one parallel batch per turn**
  via `curly.makeRequests`, on a single 45 s wall budget for the whole batch — the sequential
  loop must not be reused there. See §Out of scope.)
- Assumed timeout: `COWORLD_TIMEOUT_SECONDS` when the env carries it, else
  `episodeTimeoutSeconds` (default 1200). Play budget = `0.6 × 1200` = **720 s**.
- Scheduled model calls, worst case: `matches × maxTurns` = `6 × 10` = **60**. A match that
  deals early uses fewer.
- Measured haiku latency for a prompt of this size (~1.4 kB) is 3–6 s; at 6 s that is
  `60 × 6 = 360 s`. The 2.2 s inter-call spacing floor only binds when calls return faster, in
  which case the total is `60 × 2.2 = 132 s`. Pacing adds `6 × 0.9 = 5.4 s`. Expected total
  **≈ 366 s**, i.e. 30 % of the episode timeout and 51 % of the play budget.
- Tail: a stalled provider costs at most `30 s + 30 s` (call + one retry) per turn, but the
  deadline is tested **before every call**, so play stops at 720 s plus at most one in-flight
  turn (≤ 60 s) plus a scripted settle (< 50 ms) — **≤ 780 s = 65 %** of 1200 s, leaving 420 s
  for artifacts and teardown.
- Rate limit: the Bedrock sidecar caps 30 requests/minute per episode. 60 calls over ≥ 366 s is
  ~10 rpm; the 2.2 s spacing floor caps the pathological fast case at ~27 rpm (cogame-raid,
  2026-08-23).
- `EpisodeCallBudget = 72`. `sampleEpisode` caps `matches` to
  `max(3, floor(72 / maxTurns / 3) · 3)` and clamps `turnDelayMs` to
  `PacingBudgetMs / max(matches, 1)`; it is idempotent (`config.sampled`), so a replay being
  re-read is never re-fitted.

## Sim module

`src/negotiation/types.nim` — `NegotiationError`, `PlayerConfig`, `GameConfig`
(babel's fields with `matches` and `maxTurns` replacing `rounds`), `EventKind`, `GameEvent`,
`defaultGameConfig()`, `update(config, json)`.

```nim
GameConfig = object
  tokens: seq[string]; players: seq[PlayerConfig]
  seed: int
  matches: int                    # default 6, legal 3 or 6
  maxTurns: int                   # default 10, legal even 2..12
  episodeTimeoutSeconds: int      # default 1200
  sampled: bool
  turnDelayMs: int                # default 900
  playerConnectTimeoutSeconds: float   # default 180
  model: string                   # default "claude-sonnet-5"
  maxOutputTokens: int            # default 900
  llmTimeoutSeconds: int          # default 30
```

`src/negotiation/sim.nim` — pure rules, no IO, shared by server, tests and the wasm viewer.

Constants: `Seats = 3`, `Items = 3`, `ItemNames = ["books", "hats", "balls"]`,
`ItemSingular = ["book", "hat", "ball"]`, `PoolValue = 10`, `MinMatches = 3`, `MaxMatchesCap = 6`,
`EpisodeCallBudget = 72`, `PacingBudgetMs = 20_000`, `MinCallSpacingMs = 2200`,
`ShutdownGraceSeconds = 20`, `MaxMessageLen = 200`, `MaxNotesLen = 400`,
`Pairings = [[0,1],[0,2],[1,2]]`, and babel's `CogNames` list verbatim.

```nim
MatchPlan = object
  kind: string                 # "bargaining" in v1
  seats: array[2, int]         # [a, b]; index 0/1 is the "side" used by payoff arrays
  opener: int                  # 0 or 1, an index into seats
  pool: array[Items, int]
  values: array[2, array[Items, int]]

Phase = enum phOffer = "offer", phBetween = "between", phDone = "done"

Sim = object
  config: GameConfig
  names: seq[string]                    # anonymous aliases, seeded
  schedule: seq[MatchPlan]              # drawn at initSim from the seed
  match: int                            # match in progress / last shown; -1 before the first
  turn: int                             # 1-based turn in the live match; 0 between matches
  phase: Phase
  standing: array[Items, int]           # the standing take, from `standingSide`'s side
  standingSide: int                     # -1 when no offer stands
  offers: seq[OfferRecord]              # the live match's offers, for the viewer and prompts
  lastMessage: array[2, string]
  outcome: string                       # "" | "deal" | "no_deal" for the shown match
  payoff: array[2, int]
  points, matchesPlayed, deals: array[Seats, int]
  given, taken: array[Seats, int]       # for giveaway: opponent's u and own u, summed
  fallbacks: array[Seats, int]
  notes: seq[string]                    # latest private notes per seat
  done: bool
  reason: string                        # "complete" | "deadline"
  events: seq[GameEvent]
```

API: `initSim`, `sampleEpisode`, `tableNames`, `currentCall(sim): (kind, match, seat)`,
`beginMatch`, `applyOffer(match, take, message, notes, scripted)`,
`applyAccept(match, message, notes, scripted)`, `endEarly`, `settle`, `worthTo(sim, side, take)`,
`standingWorthTo(sim, side)`, `acceptLegal(sim)`, `score(sim, seat)`, `resultsJson`,
`tableStateJson`, `replayMatch(config, events)`, `eventToJson`, `eventFromJson`, plus text
helpers `poolText`, `takeText(take, pool)`, `valuesText(values, pool)`.

Every illegal operation raises `NegotiationError`: acting out of turn, acting on the wrong
match, `take[i]` outside `0..pool[i]`, `accept` with no standing offer, any action after the
match settled or the episode ended.

### Event vocabulary (what the replay carries)

`GameEvent` is flat (babel's shape) and unset fields are omitted by `eventToJson`.

| kind | fields |
|---|---|
| `start` | — |
| `match` | `match`, `kind` (`"bargaining"`), `seats: [a, b]`, `opener` (seat id), `pool: [3]`, `values: [[3],[3]]`, `maxTurns` |
| `offer` | `match`, `turn`, `seat` (actor), `other`, `take: [3]` (the actor's take), `worth: [uActor, uOther]` (what this offer would pay each side, in their own values), `scripted: bool`, `text` (the public message, may be absent), `notes` (the actor's notes after the reply, may be absent) |
| `accept` | `match`, `turn`, `seat` (accepter), `other`, `take: [3]` (what the **accepter** receives), `payoff: [uA, uB]` in the match's seat order, `scripted`, `text`, `notes` |
| `matchEnd` | `match`, `outcome` (`"deal"` \| `"no_deal"`), `payoff: [uA, uB]`, `turn` (turns used) |
| `end` | `match` = matches played, `text` = `reason` (`"complete"` \| `"deadline"`) |

`worth` on `offer` is derived, but it is recorded so the viewer can label an offer generous or
greedy without re-deriving valuations from the schedule; `replayMatch` re-computes it and raises
on a mismatch, so it cannot rot.

The `end` event is the **single load-bearing record of a wall-clock stop**: `replayMatch` applies
it through the same `settle(reason)` proc the live server calls, so a `deadline` replay re-derives
frame-for-frame identically to a `complete` one (particle-worlds, 2026-08-26). Any change to the
rules bumps the protocol string `negotiation.replay.v1`.

### `tableStateJson` — the exact state a viewer reads (one frame)

```json
{"seats": [{"name": "Sprocket", "score": 0.62, "points": 25, "matches": 4, "deals": 3,
            "giveaway": -1.5, "fallbacks": 0, "role": "actor|waiting|idle", "notes": "…"},
           {"…"}, {"…"}],
 "match": 2, "matches": 6, "matchesPlayed": 2, "kind": "bargaining",
 "itemNames": ["books", "hats", "balls"],
 "table": {"a": 0, "b": 1, "opener": 0, "pool": [3, 2, 1],
           "values": [[2, 1, 2], [1, 3, 1]],
           "turn": 4, "maxTurns": 10, "actor": 1,
           "standing": {"side": 0, "take": [2, 0, 1], "worth": [7, 3]},
           "offers": [{"turn": 1, "side": 0, "take": [3, 2, 1], "worth": [10, 0],
                       "text": "…", "scripted": false}],
           "messages": ["…", "…"],
           "outcome": "open|deal|no_deal", "payoff": [7, 3]},
 "phase": "offer|between|done", "gameDone": false, "reason": ""}
```

`table` is null before the first match and holds the last completed match once `done`.
`standing` is null when no offer stands. `seats[].role` is `actor` for the seat to move,
`waiting` for its opponent, `idle` for the seat sitting out. Scene-free: the viewer decodes
nothing but item indices.

### `resultsJson` — platform-facing, policy names

```json
{"names": ["neg-anchor", "Baseline (1)", "neg-integrative"],
 "scores": [0.62, 0.41, 0.55], "points": [25, 16, 22],
 "matches": [4, 4, 4], "deals": [3, 2, 3],
 "giveaway": [-1.5, 2.0, -0.5], "fallbacks": [0, 0, 1],
 "matchesPlayed": 6, "maxMatches": 6, "reason": "complete"}
```

### Replay payload — self-sufficient bytes

```json
{"protocol": "negotiation.replay.v1",
 "names": ["Sprocket", "Gizmo", "Ratchet"],
 "policyNames": ["neg-anchor", "neg-integrative", "Baseline (1)"],
 "config": {"seed": 20260826, "matches": 6, "maxTurns": 10, "sampled": true,
            "itemNames": ["books", "hats", "balls"],
            "schedule": [{"kind": "bargaining", "seats": [0, 1], "opener": 0,
                          "pool": [3, 2, 1], "values": [[2, 1, 2], [1, 3, 1]]}, "…"]},
 "events": [ … ], "results": { … }}
```

Everything the viewer needs — aliases, policy names, seed, the whole schedule with both seats'
private valuations, every event, the results — is in the bytes. The wasm module and replay mode
add `"states"`: one `tableStateJson` per event prefix, produced by `replayMatch`. `schedule` is
also re-derivable from `seed`; `replayMatch` re-derives it and raises
`"match <m> does not match the seeded schedule"` on any disagreement, so the two can never drift.
No server other than S3 is contacted.

## Server, player, protocol

`src/negotiation/server.nim` — babel's `server.nim` with the game loop replaced by §The game's
resolution order. Kept unchanged: the endpoint table, `writeArtifact`, `finishEpisode`'s ordering
(final frames to players → results → replay), the mummy Ping→Pong handler (the certifier pings
`/global`), the lock discipline (the model call happens **outside** the lock on a snapshot; only
the game thread mutates the sim), and the redacted player frame. Added:

- `MinCallSpacingMs` enforcement around the model call;
- the `ShutdownGraceSeconds = 20` window after artifacts are written, during which `/healthz`,
  `/global` and `/client/*` keep answering before `quit(0)` (cogame-lantern 0.1.3);
- a `/client/chrome_common.js` route beside `/client/renderer.js` and `/client/chrome.css`;
- `/client/replay` serves `client/replay_broadcast.html`.

Endpoints (unchanged from babel except the rename): `GET /healthz`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /client/renderer.js`,
`GET /client/chrome_common.js`, `GET /client/chrome.css`, `GET /client/assets/@name`,
`WS /player?slot=N&token=T`, `WS /global`, `WS /replay`. Both `/client/player` and
`/client/global` serve real pages and neither opens the player socket (the runner probes them
before the player pods start).

**Player protocol `negotiation.player.v1`** — JSON text frames, babel's shapes:

- game → player `{"type":"welcome","protocol":"negotiation.player.v1","slot":N,"name":"<alias>",
  "matches":M,"maxTurns":T}` on connect.
- game → player `{"type":"state","slot":N,"name":"<alias>","seat":{"score":f,"points":i,
  "matches":i,"deals":i},"match":i,"matches":M,"matchesPlayed":i,"started":bool,"done":bool,
  "reason":str}` after every event. **Redacted**: the seat's own tallies and the match counter,
  nothing else — the game is hidden-information and every decision is server-side, so the player
  container loses nothing.
- game → player `{"type":"final","done":true,"scores":[…],"points":[…],"deals":[…],
  "names":[aliases],"matchesPlayed":i,"reason":str,"slot":N}` at the end; the player exits.
- player → game `{"type":"prompt","prompt":str,"scripted":str|bool}` — `prompt` capped at 4000
  chars server-side; `scripted` is `"haggler"`, `"hardliner"`, or a boolean (`true` ⇒
  `haggler`). Sent on connect and re-sent after `welcome` (the first send can race slot
  registration). The latest frame applies to all later turns.

Spectator frames (`/global`) carry the full `tableStateJson` plus `type`, `game`, `policyNames`,
`events`, `started`, `done`, `connected` — exactly babel's `snapshotJson`. **Player frames never
carry `policyNames`.**

`src/negotiation_player.nim` — babel's player with the default prompt replaced by a sound
bargaining strategy (open high, concede the item you value least, read what they keep asking for,
accept ≥ 6, never end at zero on your last turn) and one fix carried from cogame-raid 0.1.4: the
receive loop is wrapped in `try/except CatchableError` and **exits 0** on a dead socket — whisky's
`receiveMessage` raises on a close frame, and the game's `quit(0)` can outrun the flushed final
frame, which fails certification with `player_error` on a coin flip.

## Viewer

**All four viewer files come from the single starter `cogame-babel` — no other starter
contributes any of them.** From `/workspace/starters/cogame-babel`:

- `replay-viewer/config.nims` → this repo's `replay-viewer/config.nims`, edited only for the
  renames: output `negotiation_replay.js`, `EXPORT_NAME=NegotiationReplayModule`,
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_neg_load_replay,_neg_payload_ptr,_neg_payload_len,_neg_error_ptr,_neg_error_len`.
  Every other flag (`MODULARIZE=1`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`,
  `ENVIRONMENT=web`, `EXPORTED_RUNTIME_METHODS=HEAPU8`, `-d:useMalloc`, `--mm:arc`,
  `--exceptions:goto`) is copied verbatim.
- the wasm entry `replay-viewer/babel_replay.nim` → `replay-viewer/negotiation_replay.nim`, same
  body with `bab_*` renamed `neg_*`, the same `emscripten_exit_with_live_runtime()` epilogue, and
  `negotiation/sim` in place of `babel/sim`.
- `replay-viewer/static_replay.js` → `replay-viewer/static_replay.js`, same file
  (`FETCH_TIMEOUT_MS = 20000`, the AbortController-bounded fetch, the `coworld-replay`
  postMessage bridge, the Retry button, `data-replay-error`) with the module factory renamed to
  `NegotiationReplayModule` and the renderer entry to `NegotiationRenderer.attachReplay`.
- `replay-viewer/index.html` → `replay-viewer/index.html`, babel's shell with the same appended
  game block as the broadcast page (below) and one extra `<script src="./chrome_common.js">`
  before `./renderer.js`.

Mixing one starter's shell with another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME`
against an `onRuntimeInitialized` bootstrap) deadlocks the viewer silently with every file
present and 200 (cogame-lantern, 2026-08-23) — hence the single source for all four.

**Load signal.** `static_replay.js` sets `document.documentElement.dataset.replayLoaded = "true"`
from the renderer's first-drawn-frame callback (`attachReplay({ …, onFirstFrame })`, a new option
on the chrome driver) and posts the bridge's `{type:"ready"}` **from inside that same callback,
after the attribute is set** — never on a bare `requestAnimationFrame` at the call site, which is
what let softmax.com sample an unpainted shell (chorus, 2026-08-24). On any failure it sets
`data-replay-error="<message>"` and posts `{type:"error"}`.

### Chrome provenance

- **`client/chrome_common.js` is created by copying the chrome half of babel's
  `client/renderer.js` byte-for-byte** — `assetUrl`, `loadImages`, `seatColor`, `hexToRgb`,
  `shade`, `rgba`, `ellipsize`, `roundRect`, `escapeHtml`, `clampName`, `isBaselineFiller`,
  `makeNameMap`, `applyNames`, `makeEffects`, `blockHead`, `renderFeed`, `buildScrub`,
  `bindFeedToggle`, `attachLive`, `attachReplay` — into an IIFE exporting
  `window.NegChrome`. The function bodies are not edited except for these **three** changes,
  which are the whole diff and are listed here so a reviewer can check it:
  1. the game-specific call sites inside `renderFeed`, `buildScrub`, `attachLive` and
     `attachReplay` (`describeEvent`, `stateToView`, `draw`, `updateScorebug`,
     `updateEndscreen`, `phaseText`, `matchHeader`) are redirected to a hook object registered by
     the game block via `NegChrome.register({...})`;
  2. `buildScrub` emits **`<button class="beat-marker …" type="button" aria-label="…">`** instead
     of `<div>`, each with a click handler that seeks to that event (unlabelled divs that never
     seek passed every static grep on cogame-tandem, 2026-08-23);
  3. a new `relayout()` is added (below), plus the `onFirstFrame` option on `attachReplay`.
  After creation the file is frozen: game code never edits it.
- **`client/renderer.js` is the game block only** — the negotiation stage, the feed lines, the
  scorebug and endcard painters, `phaseText`/`matchHeader`, and the `NegChrome.register` call.
  It must not declare any identifier that appears in `NegChrome`'s export list; a hoisted
  `function markBeat` in the game block shadowed the chrome alias on cogame-tandem, and §Tests
  keeps a CI grep for it.
- **`client/replay_broadcast.html` is babel's `client/replay.html`, copied, with a game block
  appended** — never a rewrite that reuses the starter's ids (cogame-gridlock, 2026-08-23).
  Preserved verbatim: `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`,
  `#statuschip`, `#feedtoggle`, `#scorebug`, `#board-wrap`, `#table`, `#lightpool`, `#grain`,
  `#endscreen`, `#transport`, `#scrub`, `.tbar`, `#play`, `#pos`, `#feed`, `#loading`, and
  babel's trailing `fit()` + `bindFeedToggle` script lines.
  **Elements removed from the starter page: none** — the id set is preserved in full, and a CI
  step asserts every id above is present in both `client/replay_broadcast.html` and
  `replay-viewer/index.html`.
  **Appended** (after `#scorebug`, inside `#stage`): a single new block
  `<div id="gameblock"><div id="matchbar"></div><div id="valuestrip"></div></div>` — `#matchbar`
  is one chip per scheduled match (`DEAL 7–3` / `NO DEAL` / pending), `#valuestrip` is the
  spectator-only readout of both live seats' private per-item values. Only the wordmark's text
  changes (`NEGO<span>TIATE</span>`).
- **Zoom: `#viewpanel` is dropped entirely.** The stage is one fixed table that always fits the
  frame; babel ships no zoom bar or minimap and this fork adds none.
- `client/global.html` and `client/player.html` are babel's, with the same appended game block
  and the wordmark change; `client/chrome.css` is babel's with the game block's rules and the
  new beat classes appended (nothing removed).

### Transport rules

- `relayout()` (in `chrome_common.js`) runs on load, on every `resize`, and after
  `bindFeedToggle` toggles the feed. It measures `#transport` and writes on `:root`:
  `--band` = the transport band's height in px, and `--hudscale` =
  `clamp(0.72, stageWidth / 960, 1.25)`. Every chrome font size and pad is expressed in
  `calc(… * var(--hudscale))`.
- **No overlay may sit in the transport band.** `#endscreen`, `#loading` and `#gameblock` are all
  `bottom: var(--band)`; the endcard stops at `var(--band)` and is **dismissed by every seek**
  (`attachReplay`'s seek path calls the endcard painter with `show = false` before repainting).
- **Scrubber beats are clickable labelled buttons.** Kinds emitted, each with its own CSS rule in
  `client/chrome.css`: `.beat-marker.offer` (thin tick in the actor's seat colour),
  `.beat-marker.accept` (taller, actor's seat colour), `.beat-marker.deal` (green diamond),
  `.beat-marker.nodeal` (red ghost), `.beat-marker.end` (tall amber). One `.round-span` per match
  (alternating tint) with a `.round-sep` between matches, exactly as babel builds them.
  aria-labels read e.g. `Match 3, turn 4 — Sprocket offers` / `Match 3 — no deal`.

### What the viewer draws

Stage (canvas `#table`, felt-and-lamp palette from babel's `chrome.css`):

- The two negotiating cogs face each other across the table, drawn with babel's
  `data/soldier_red_front.png` / `soldier_blue_front.png` / `soldier_green_front.png` sprites in
  their seat colours over `data/arena_floor.png`; the seat sitting out is a dimmed plate at the
  side reading `SITTING OUT`.
- **The pool** sits between them: the actual items, drawn with canvas primitives at ≥ 14 px —
  books as stacked spines with a coloured cover, hats as brim-and-crown silhouettes, balls as
  shaded spheres, one icon per item in the pool (never "3 books" as bare text; the count label
  rides under the row).
- **The valuation strips** (spectator-only): under each cog, `books ×2 · hats ×1 · balls ×2 = 10`
  in that seat's colour. This is the idea's watchability plan — with both value sets on screen,
  every offer reads instantly as generous or greedy.
- **The offer split**: the live offer splits the pool row into a left share and a right share,
  each tinted to the seat that would receive it, with `worth 7` / `worth 3` chips under each
  share (each computed in that seat's own values). A new offer slides in and holds like babel's
  last-move arrow; the standing offer stays lit while the other seat thinks.
- **The stamp**: on `matchEnd`, a large angled stamp across the stage — green `DEAL` with
  `7 – 3` and the final item split, or red `NO DEAL` with `0 – 0` and `10 TURNS, NO AGREEMENT`.
  It holds for the pacing delay and fades as the next match's `match` event lands.
- Idle before the first match: the empty table with the wordmark.

Readouts:

- **Scorebug** (`#scorebug`, 3 plates): alias — the policy name spectator-side — big `points`,
  label `pts`, sub-line `score` to two decimals, pips = `deals` filled out of `matches` played,
  a `▶` on the seat to move, and the sitting-out plate dimmed.
- **Clock** (`#clock`): `MATCH 3 / 6 · TURN 4 / 10 · SPROCKET TO MOVE`; at a settlement
  `MATCH 3 / 6 · DEAL 7–3`; at the end `FINAL · 6 MATCHES`.
- **Feed** (`#feed`): `MATCH 3 — SPROCKET vs GIZMO` heads (`blockHead`);
  `Sprocket offers: takes 2 books, 1 ball — worth 7 to Sprocket, 3 to Gizmo` (actor's colour);
  `Sprocket: "I only need the books."` (say-styled, only when the message is non-empty);
  `Gizmo ACCEPTS — DEAL 3–7` (`feed-score seatN`); `NO DEAL — 10 turns, 0–0`;
  `Sprocket notes: …` (only when the notes changed); `Final — Sprocket 25 pts (0.62)`.
  A `⚙` glyph marks any action taken by the scripted baseline.
- **Endcard** (`#endscreen`): title `FINAL — 6 MATCHES`, columns `score`, `pts`, `deals`,
  `giveaway`; verdict = top seat's name + `TAKES THE TABLE` (or `ALL LEVEL` on a tie); a reason
  line when `reason == "deadline"`.
- **`#matchbar`**: one chip per scheduled match, filled as matches settle.

**Legibility at 360 px** is a requirement, not a nicety (the softmax.com featured-match iframe is
~360 px wide): `.plate-name { flex: 1 1 auto; min-width: 3.2em }`, plate labels hidden under
640 px, the pool row wraps to two lines under 420 px, the valuation strips collapse to
`2·1·2` numerals under 420 px, and the item icons never shrink below 10 px. The viewer smoke
screenshots at 360 px as well as at desktop width.

## Packaging

- **`compose.yaml`** — one service named `game` (so the manifest placeholder is the proven
  `{{GAME_IMAGE}}`; placeholders are derived from compose service names, and a hyphenated
  service name is not worth the risk — cogame-lantern 0.1.0):

  ```yaml
  services:
    game:
      image: coworld-negotiation-games:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — babel's, renamed: one image, two entrypoints `/bin/negotiation` (default
  `CMD`) and `/bin/negotiation-player`; `data/` and `client/` copied into the run image.
  **`Dockerfile.replay-viewer`** — babel's pinned `emscripten/emsdk:4.0.15` + nimby 0.1.27 stage,
  building `replay-viewer/negotiation_replay.nim`.
- **`tools/build_replay_viewer.sh`** (mode 100755, the `coworld build` hook) — babel's, with:
  the renames; **`mkdir -p` on the output dir's parent before the containment check** (paintbot's
  hook fails on a fresh CI checkout without it — ecos, 2026-08-23); and `client/chrome_common.js`
  added to the copy list beside `index.html`, `static_replay.js`, `renderer.js`, `chrome.css`,
  the wasm pair and the `data/` assets. It keeps babel's final assertions
  (`test -f index.html`, `grep -q 'data-replay' static_replay.js`) and adds
  `grep -q 'data-replay-loaded' static_replay.js`.
- **`coworld_manifest_template.json`**:
  - `$schema` + top-level `tags` (≥ 3): `["negotiation", "bargaining", "mixed-motive",
    "hidden-information", "llm-driven", "turn-based", "three-player", "openspiel-port"]`.
  - `game.name` = **`negotiation-games`** — the same string as the repo slug, the page slug, the
    secret namespace and the league seed's `game.name` (a `game.name` that differs from the slug
    is what broke cogame-commons-family's upload).
  - `game.description` present (required by the validator); **no `game.tags`** (forbidden there).
  - `game.replay_viewer = {"bundle": "static-replay-viewer"}` — nested under `game`, not
    top-level; no top-level `version`; no `game.display_name`; `game.owner` = `daveey@gmail.com`;
    `game.runnable.type = "game"`; `episode_timeout_minutes` top-level.
  - `game.runnable`: image `{{GAME_IMAGE}}`, run `["/bin/negotiation"]`, env
    `{"ANTHROPIC_API_KEY_URI": "secret://coworld/negotiation-games/anthropic_api_key"}` —
    without that env the hosted container never sees the key and every league episode silently
    plays scripted (hive, 2026-08-23) — and `source_url`
    `https://github.com/Metta-AI/cogame-negotiation-games/tree/main`.
  - `game.config_schema`: a real JSON Schema, `additionalProperties: false`, required
    `["tokens", "players"]`. `tokens` and `players` are arrays with **`minItems: 3, maxItems: 3`**
    (every array property needs both bounds — tandem 0.1.0). `num_agents` integer
    `minimum: 3, maximum: 3`. `seed` integer. `matches` integer `minimum: 3, maximum: 6,
    multipleOf: 3, default: 6`. `maxTurns` integer `minimum: 2, maximum: 12, multipleOf: 2,
    default: 10`. `episodeTimeoutSeconds` 60..6000 default 1200. `turnDelayMs` 0..10000 default
    900. `model` default `claude-sonnet-5`. `maxOutputTokens` 64..2000 default 900.
    `llmTimeoutSeconds` 5..300 default 30. `player_connect_timeout_seconds` number ≥ 0 default
    180.
  - `game.results_schema`: exactly the `resultsJson` above; `names`/`scores`/`points`/`matches`/
    `deals`/`giveaway`/`fallbacks` all `minItems: 3, maxItems: 3`; `reason` a string documented as
    `complete | deadline`.
  - **`game.protocols` carries BOTH** `player` and `global`, each as
    `{"type": "text", "value": "…"}` objects (bare strings fail the platform validator, not repo
    CI — cogame-garble). `player` = the `negotiation.player.v1` frame table from §Server plus
    "a policy is just a prompt: `PLAYER_PROMPT` / `PLAYER_SCRIPTED=haggler|hardliner`".
    `global` = the `/global` snapshot shape (the full `tableStateJson` plus `policyNames`,
    `events`, `started`, `done`, `connected`), the event vocabulary table, and the note that
    `/client/global` renders the stage while the static bundle plays hosted replays.
  - **`game.docs`** = `{"readme": {"type": "text", "value": "…"}, "pages": [ … ]}` with two
    pages: `rules.md` (the pool/valuation draw, the two actions, the turn cliff, the scoring
    formula and its sign, the two `results.reason` values) and `writing-a-policy.md` (what the
    prompt sees, the reply schema with both caps, the fallback rule, and the two baselines'
    algorithms).
  - **`player`** (top-level, three runnables — all three are seated by the cert fixture, because
    a declared runnable with no certification slot fails `players_missing`, cogame-raid 0.1.3):
    `negotiation-player` (prompt player, no `PLAYER_*` env), `negotiation-haggler`
    (`PLAYER_SCRIPTED: "haggler"`), `negotiation-hardliner` (`PLAYER_SCRIPTED: "hardliner"`).
    Each carries `id`, `type: "player"`, `name`, `description`, image `{{GAME_IMAGE}}`,
    `run: ["/bin/negotiation-player"]`, `source_url`, and resources
    `{requests: {cpu: 100m, memory: 64Mi}, limits: {cpu: "1"}}` (a `500m` limit is rejected at
    upload — cogame-pistonball 0.1.1).
  - **Variants — `num_agents: 3` in every one**, and no literal `tokens` in any `game_config`
    (the runner injects them; a literal fails matriculation — cogame-knights-archers 0.1.0):

    | id | description | `game_config` |
    |---|---|---|
    | `standard` | Three cogs, six matches, ten turns each: every pairing twice, every seat opening twice. | `players: [Player1, Player2, Player3]`, `num_agents: 3`, `matches: 6`, `maxTurns: 10`, `turnDelayMs: 900`, `player_connect_timeout_seconds: 180` |
    | `sprint` | Six short matches — six turns each, so a concession that comes late comes too late. | `players: [Player1, Player2, Player3]`, `num_agents: 3`, `matches: 6`, `maxTurns: 6`, `turnDelayMs: 400`, `player_connect_timeout_seconds: 180` |

  - **Certification fixture** (`certification.game_config`): `players: [Sprocket, Gizmo,
    Ratchet]`, **`num_agents: 3`**, `seed: 7`, `matches: 3`, `maxTurns: 6`, `turnDelayMs: 0`,
    `player_connect_timeout_seconds: 180`. `certification.players`:
    `[{"player_id": "negotiation-player"}, {"player_id": "negotiation-haggler"},
    {"player_id": "negotiation-hardliner"}]` — three slots, three declared runnables, one each.
    Timing: certify runs with no API key, so all 18 turns are scripted (< 100 ms total);
    connect ≈ 2 s + play ≈ 0 s + the 20 s shutdown grace ≈ **25 s**, inside `coworld certify`'s
    60 s default, so no `--timeout-seconds` override is needed. A test pins
    `grace + play + linger < 50 s`.
- **`negotiation.nimble`** — babel's, renamed, same requires (`nim >= 2.2.4`, `bitworld`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`); `nimby.lock` copied verbatim.
- **Static viewer bundle**: `game.replay_viewer.bundle = "static-replay-viewer"`, produced by
  `tools/build_replay_viewer.sh`. **No `/client/replay` live-server viewer is declared anywhere.**
  Expect `certify.replay_liveness` to read
  `skipped (static replay bundle declared…)` in `release-result.json`.
- **Workflows** come from `coworld-builder/templates/`, not from babel (which ships none):
  `.github/workflows/ci.yml` (with `SLUG: negotiation-games`, `IMAGE: coworld-negotiation-games`),
  `coworld-release.yml`, `coworld-submit.yml`, `tools/ci/docker_smoke.sh` (with `<SEATS>`
  substituted to **3**) and `tools/ci/viewer_smoke.mjs`, all copied unmodified except for those
  substitutions.
- **`tools/ci/policies.json`** — four policies, all on the same image: champions
  `negotiation-games-anchor` (`PLAYER_PROMPT`, champion #1) and `negotiation-games-integrative`
  (`PLAYER_PROMPT`, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, champion #2);
  fillers `negotiation-games-haggler` (`PLAYER_SCRIPTED: "haggler"`) and
  `negotiation-games-hardliner` (`PLAYER_SCRIPTED: "hardliner"`). All four `run`
  `/bin/negotiation-player`.

## Tests

Everything below runs in `ci.yml`; the sandbox cannot run any of it locally.

**`tests/test_sim.nim` (sim unit tests, job `test`)**

1. Seed determinism: two `initSim`s with seed 7 produce identical aliases, pairings, openers,
   pools and value tables; seed 8 differs in at least the pools or the values.
2. Schedule balance: with `matches = 6`, each seat plays exactly 4 matches and opens exactly 2;
   each pairing occurs exactly twice.
3. Pool invariants: every `pool[i] ∈ 1..4` and `Σ pool ∈ [5, 7]`; the bounded redraw path
   (forced by a stub RNG) yields `[3, 2, 2]`.
4. Valuation invariants, over 200 seeds: `Σ pool[i]·v[i] == 10` for both seats of every match;
   every `v[i] ∈ 0..10`; for every item type `vA[i] + vB[i] > 0`.
5. Legality: `take` out of bounds, a negative count, `accept` on turn 1, a seat acting out of
   turn, any action on a settled match, and any action after `end` each raise
   `NegotiationError`.
6. Payoff math: an accept at turn `t` gives the accepter the complement of the standing take;
   `uA + uB` equals the two seats' own valuations of their shares; a no-deal pays `[0, 0]`;
   `score = points / (10 · matchesPlayed)`; `giveaway` is the mean of `(opponent u − own u)`.
7. The turn cliff: `maxTurns` offers with no accept produce exactly one `matchEnd` with
   `outcome == "no_deal"` and `turn == maxTurns`.
8. Every started match emits exactly one `matchEnd`, including when `endEarly()` fires
   mid-match after the baseline finishes it.
9. **Record → re-derive for EVERY end reason** (not just `complete` — particle-worlds,
   2026-08-26): for `complete` and for `deadline`, `replayMatch(config, events)` gives
   `frames.len == events.len + 1` and a final frame byte-equal to the live sim's
   `tableStateJson()`; a tampered `match` event raises "does not match the seeded schedule".
10. `eventToJson` → `eventFromJson` round-trips every `EventKind`, with empty `text`/`notes`
    omitted and restored as `""`.
11. `sampleEpisode` caps `matches` to the call budget, floors to a multiple of 3, clamps
    `turnDelayMs`, and is idempotent when `sampled` is already true.
12. Rune-safe caps: a 500-rune multibyte message and a 900-rune multibyte note cap to 200 and
    400 **runes**; the results are valid UTF-8 (`validateUtf8 == -1`) and end in `…`.
13. Name spaces: for every seat and every turn, neither the composed system prompt nor the
    composed user prompt contains any policy display name (checked against a fixture whose
    policy names are distinctive strings), while `resultsJson().names` contains exactly them.

**`tests/test_bot.nim` (bounded-orders / legality on the scripted baselines, job `test`)**

14. **Bounded orders:** for seeds `[1, 7, 42, 1234, 20260826]` × every baseline pairing
    (haggler/haggler, hardliner/hardliner, haggler/hardliner), full episodes play with no
    exception; every emitted `take` satisfies `0 ≤ take[i] ≤ pool[i]`; no match exceeds
    `maxTurns` turns; `accept` is never emitted on turn 1; every match settles.
15. `haggler`'s reservation `R(t)` is non-increasing in `t`, and the own-worth of its successive
    offers is non-increasing.
16. Over 100 seeded matches: haggler-vs-haggler deals ≥ 90 % with mean joint utility ≥ 12 of 20;
    hardliner-vs-hardliner produces at least 10 no-deals (the baselines are genuinely
    different); in haggler-vs-hardliner the hardliner's mean utility is strictly greater.
17. `decide` with no credentials returns the scripted action immediately and makes no HTTP call.
18. Reply parsing: `take` as object and as array; integer-valued strings; `action` synonyms and
    casing; a fenced reply with trailing prose; a reply with no `action` but a `take`. Rejected:
    a fractional count, an out-of-range count, `accept` on turn 1, `{"action":"burn"}`, prose
    with no JSON object.
19. Cert-fixture timing pin: the fixture's `matches × maxTurns` scripted turns plus the connect
    grace plus `ShutdownGraceSeconds` is `< 50 s`.

**Manifest checks (job `test`, `tools/ci/manifest_check.py`)**

20. `num_agents == 3` in **every** variant's `game_config` and in `certification.game_config`;
    `len(certification.players) == 3`; every declared `player[].id` is seated at least once; no
    `tokens` key in any `game_config`; `game.description` present and `game.tags` absent; every
    array property in `config_schema` has `minItems` and `maxItems`; `game.protocols.player` and
    `.global` are both `{"type","value"}` objects; `game.docs.readme` + `pages` well-formed;
    `game.replay_viewer.bundle == "static-replay-viewer"`; the secret URI namespace equals
    `game.name`. It also runs the installed `coworld` CLI's own
    `_load_template_manifest` / `validate_upload_manifest` offline, so a manifest that repo CI
    likes but phase 40 rejects fails here instead (cogame-collab-cooking, 2026-08-25).

**End-to-end episode + strict-UTF-8 replay parse (job `docker-smoke`)**

21. `tools/ci/docker_smoke.sh` with `SMOKE_SEATS=3` builds the image and runs one **real
    episode** — three seats, no `ANTHROPIC_API_KEY`, so every seat plays its baseline (the
    prompt seat falls back to `haggler`) — with `seed: 20260826`, `matches: 6`, `maxTurns: 10`,
    `turnDelayMs: 0`, and asserts: exit 0 for the game **and for every player container**
    (cogame-raid 0.1.4), `results.json` present, `results.reason == "complete"`,
    `len(scores) == 3`, at least one `matchEnd` with `outcome == "deal"`, and the four
    seat-count invariants the script owns. The replay is uploaded as artifact `smoke-replay`.
22. **Strict-UTF-8 replay parse** (same job, on the produced bytes):
    `json.loads(open(replay, encoding="utf-8", errors="strict").read())` must succeed, and the
    parsed object must carry `protocol == "negotiation.replay.v1"`, three `names`, three
    `policyNames`, `config.seed`, `config.schedule` of length `matches`, a non-empty `events`
    array whose first event is `start` and last is `end`, and `results.reason ∈
    {"complete", "deadline"}`. A byte-boundary truncation renders fine in a browser and fails
    exactly here — that is the point of the test.
23. Replay length pin: `events.len × 320 ms ≥ soak + 2 s`, so the viewer soak cannot mistake a
    finished replay for a frozen one (ecos, 2026-08-23).

**Viewer smoke (job `wasm-viewer`, `needs: docker-smoke`)**

24. The job asserts `tools/build_replay_viewer.sh` exists and is mode 100755, builds the bundle,
    asserts `index.html` and a non-empty `.wasm` are present, downloads the `smoke-replay`
    artifact, and then **executes** the bundle:
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <the
    docker-smoke replay> --timeout 90 --soak 8 --strict-text-bounds`. The bundle is run, not
    merely built (cogame-lantern), against the bytes the platform will actually serve. `--soak`
    catches a mid-replay exception that latches the shell into `failed` (cogball 0.1.4);
    `--strict-text-bounds` requires `canvas_text.never_inside == 0` for this fixed stage
    (cogchemists, 2026-08-24).
25. Renderer text fixture: `tools/ci/renderer_fixture.html` loads the real
    `dist/static-replay-viewer/index.html` **in an iframe** and shims only the wasm entry with a
    synthetic payload — full-cap 200-rune messages and 400-rune notes on every seat, a `deal` and
    a `no_deal` stamp, the widest possible pool — at 360, 720 and 1280 px, and
    `viewer_smoke.mjs --strict-text-bounds` runs against it in its own step. Scripted replays
    carry no LLM text at all, so this is the only gate on the message/notes chrome, and it must
    execute the shipped page rather than re-implement it (particle-worlds, 2026-08-26).
26. Static chrome greps in the same job: every frozen id from §Viewer is present in both
    `client/replay_broadcast.html` and `replay-viewer/index.html`; the game block declares no
    identifier from `NegChrome`'s export list (cogame-tandem); `client/chrome.css` has a rule for
    every beat class the scrubber emits (`offer`, `accept`, `deal`, `nodeal`, `end`);
    `static_replay.js` sets `data-replay-loaded` and posts `ready` after it, not before
    (chorus).

## Out of scope (v1)

- **Colored Trails** — the idea's 3-seat game. Deferred because it needs a coloured board, chip
  inventories, goal-distance scoring and a board renderer, and because its one proposal round is
  **simultaneous for all three seats**, which needs the parallel-batch call path
  (`curly.makeRequests`, one batch per turn) that v1's strictly alternating loop does not
  exercise. It lands as a second `MatchPlan.kind` (`"colored_trails"`) into the same
  `num_agents: 3` manifest — no seat-count change, no replay-protocol bump.
- **Sheriff** — smuggler/sheriff bribery over several rounds of cheap talk. Same alternating
  machinery as Bargaining but a different payoff table and a final inspect decision; lands as
  `kind: "sheriff"` with its own baseline pair.
- **Trade Comm** — two seats, one message then a mutual-trade proposal. Cheap to add later as
  `kind: "trade_comm"`; omitted now because a 0/1 payoff carries almost no ranking signal on its
  own.
- **A `walk away` action.** v1's action set is exactly `offer | accept`; the only route to a
  zero-zero outcome is the turn cliff, as in the source text.
- **Discounting / time pressure inside a match.** No per-turn decay; the `maxTurns` cliff is the
  whole pressure.
- **More than three item types, pools larger than 7 items, or values outside 0..10.**
- **Multi-issue side payments, contracts, or any enforcement of the free-text channel.** Messages
  are cheap talk and stay cheap talk.
- **Cross-episode memory or reputation.** Valuations are redrawn every match and aliases are
  reshuffled every episode, on purpose.
- **A live-server (`/client/replay`) hosted viewer.** Replays are the static wasm bundle, always.
- **More than three seats**, and any variant whose `matches` is not a multiple of 3 (it would
  give seats unequal match counts within one episode).
