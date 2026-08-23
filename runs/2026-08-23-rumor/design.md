# Rumor: ten cogs on a social graph, ten noisy clues, two or three of them paid to mislead

Ten LLM-piloted cogs sit on a hidden social graph. One binary fact is true; every cog holds a
private clue that is right about two times in three; two or three cogs are **saboteurs** paid to
make the honest cogs vote wrong. Cogs may message only their graph neighbours, and only their
neighbours; after five rounds of talk everyone votes in secret, and then the masks come off. Built
on `Metta-AI/cogame-bullwhip` (mounted read-only at `/workspace/starters/cogame-bullwhip`), the
newest parley-lineage template: a Nim game server implementing the Coworld runtime contract, a pure
`sim` module shared by server / tests / wasm viewer, LLM decisions where **a policy is just a
prompt**, always-available scripted baselines, one parallel LLM batch per simultaneous turn, and the
parley broadcast chrome around a canvas stage. Bullwhip is the starter because Rumor has exactly
bullwhip's shape — turn-based, hidden-information, **simultaneous** free-text decisions by
LLM-prompt seats, with a per-tick static wasm replay — and because bullwhip is the only starter
whose `decideAll` already fires **one parallel batch per turn**, which is the whole timing model
here. **Every convention there holds here unless this note says otherwise.**

Source idea, verbatim:

> 13 Rumor — ten cogs on a social graph, each with a noisy clue, two of them paid to mislead
>
> Each round a hidden binary fact; everyone gets a private signal of 60% reliability and can message
> only graph neighbours. After five rounds of talk, everyone votes. Honest seats score on collective
> accuracy; saboteurs score on wrongness. Graph topology and saboteur count are unknown until scene
> start.
>
> Seats: 8-12
> Motive: cooperative aggregation with adversaries
> Policy interface: LLM prompt
> Fills gap: networked information / noisy signals / Byzantine agents
> Integrity (anti-collusion): One seat per account per episode; an honest seat is scored
> counterfactually — did its messages raise strangers' accuracy versus a muted replay — so a bloc
> can't farm the collective-accuracy pool.
>
> Replay plan (watchability): The social graph is the stage: messages pulse along edges, each node's
> private signal is shown to spectators as a tinted coin, and per-node belief meters shade red or
> blue. You watch a lie propagate; masks come off the saboteurs at the end.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

---

## The game

### Seats

- **Seats: exactly 10.** `num_agents` = **10** everywhere — both manifest variants, the
  certification fixture, and `<SEATS>` in `tools/ci/docker_smoke.sh`. The idea allows 8–12; 10 is
  its own title's number, and bullwhip's `CogNames` list has exactly ten entries, so every seat gets
  a distinct alias with no `Cog N` fallback.
- **Roles**: `RoleNames = ["Honest", "Saboteur"]`, role ids `0` and `1`. The number of saboteurs is
  `2` or `3`, drawn from the seed (fair coin) unless the config pins it. Honest seats are therefore
  7 or 8.
- Role assignment is a **seeded permutation**: shuffle the seat list with the episode rng and make
  the first `saboteurs` seats in that order the saboteurs. No policy can choose its role; the same
  policy plays honest in one episode and saboteur in the next, which is why both score ranges are
  normalised to `[−1, +1]` (see *Scoring*).
- Seats play under **anonymous cog aliases** drawn from the seed (`CogNames`, bullwhip's list kept
  verbatim: Sprocket, Gizmo, Ratchet, Widget, Bolt, Piston, Flywheel, Rivet, Tinker, Gasket). Policy
  names are spectator-side only. See *Two name spaces*.

### One fact per episode — a decision, logged

The idea's "Each round a hidden binary fact" reads two ways. It is settled by the very next
sentence, "After five rounds of talk, everyone votes": one vote at the end means **one hidden fact
per episode**, with the five talk rounds spent aggregating clues about it. A fact per talk round
would need a vote per round and would leave five overlapping inference problems whose clues mix into
noise. **Decided: one hidden binary fact per episode, five talk rounds, one sealed ballot.** The
league's "round" (a scheduling term) is the episode; the game's "round" is a talk round.

### The scenario (seeded, procedural, server-side)

Everything random is drawn once at `initSim` from a single rng stream, in this **fixed order** —
*proposition, truth, saboteur count, roles, topology family, node order, edges, clues* — so a replay
re-derives the whole scenario from the seed alone. (Aliases come from `tableNames()`'s own separate
stream, exactly as in bullwhip.)

1. **Proposition.** One entry drawn uniformly from `Propositions` (8 entries, each a question and
   two mutually exclusive one-word answers, `optionA` / `optionB`):

   | question | A | B |
   |---|---|---|
   | The relay tower on Ash Hill is… | `BROKEN` | `SOUND` |
   | The night shipment was… | `STOLEN` | `DELAYED` |
   | The east gate was left… | `OPEN` | `BARRED` |
   | The foreman's ledger is… | `FORGED` | `GENUINE` |
   | The water in the cistern is… | `FOULED` | `CLEAN` |
   | The signal fire on the ridge was… | `LIT` | `DARK` |
   | The mine's lower gallery is… | `FLOODED` | `DRY` |
   | The courier who left at dawn was… | `FOLLOWED` | `ALONE` |

   All sixteen answer words are **disjoint from `CogNames`** — a test asserts it — so the viewer's
   alias → policy-name rewriter can never rewrite an answer word.
2. **Truth.** `truth` ∈ `{"A", "B"}`, a fair coin. It is the hidden fact. Nobody — honest seat,
   saboteur, or spectator — is told it before the tally.
3. **Saboteur count.** `saboteurs = 2 + rng.rand(1)` (so 2 or 3). If the config pins `saboteurs`,
   the draw still happens and is then **overridden** — consuming the same rng either way, so a
   pinned value can never change the graph or the clues. Same rule for the topology draw in step 5.
4. **Roles.** Shuffle `[0 … 9]`; the first `saboteurs` seats are saboteurs, the rest honest.
   Placement is uniform and ignores degree (a saboteur on a bridge is luck, and it is one of the
   things that makes an episode worth watching).
5. **Topology family.** Drawn uniformly from `["ring", "smallworld", "clusters", "hub"]`, then
   overridden if the config pins `topology` to one of those four. `topology: "random"` (the default)
   keeps the draw.
6. **Node order.** A seeded shuffle of the ten seats — the graph is built over this order, so seat
   0 is not structurally special.
7. **Edges**, by family, over the shuffled order `o[0..9]`:
   - **`ring`** — the 10-cycle `o[i]–o[i+1 mod 10]`, plus **3 chords**: random distinct pairs not
     already joined (redraw a duplicate, ≤ 200 attempts). **13 edges**, degrees 2–5.
   - **`smallworld`** — the 10-cycle plus every 2-hop pair `o[i]–o[i+2 mod 10]` (**20 edges**,
     4-regular), then **2 rewires**: drop a uniformly chosen edge and add a uniformly chosen
     non-existent pair; a rewire that disconnects the graph is rejected and redrawn (≤ 50 attempts,
     else the dropped edge is put back). **20 edges**.
   - **`clusters`** — split the order into two groups of five; in each group a 5-cycle plus the
     chord `g[0]–g[2]` (6 edges each), plus **exactly one bridge** between a random node of each
     group. **13 edges**, min degree 2, and everything crossing the bridge passes through one cog.
   - **`hub`** — `o[0..2]` are hubs joined in a triangle; each of `o[3..9]` attaches to **1** hub
     (probability ½) or **2** hubs. **10–17 edges**, min degree 1.
   After building, BFS-assert **connectivity** and **min degree ≥ 1**; on failure redraw that
   family's random parts (≤ 100 attempts) and, failing that, fall back to `ring`. The adjacency is
   fixed for the whole episode.
8. **Clues.** Draw each seat's clue i.i.d.: `clue[i] = truth` with probability **0.60**, else the
   other option. Then apply the **tally condition**: let `m` = (# clues equal to the truth) − (# not
   equal); redraw the whole vector (same rng stream, ≤ **200** attempts) until `m ∈ {2, 4, 6}`, i.e.
   the ten clues split **6–4, 7–3 or 8–2 in favour of the truth**. If 200 attempts are exhausted,
   fall back to a deterministic assignment: shuffle the seats and give the first `6` the true clue
   and the rest the false one. Fallback is unreachable in practice — measured over 6,000 seeds in
   the reference model, mean 1.70 attempts, max 14.

   *Why the condition.* It makes one public rule true and tellable: **the ten clues together always
   point at the truth.** A cog that could see all ten and take the majority would always be right,
   so the whole game is "how much of the network's clue evidence can you actually collect, and how
   much of what you collect is a saboteur's fabrication?" Without it, ~18 % of episodes are
   unwinnable by any amount of good aggregation, and the ladder becomes a lottery over clue draws.
   Excluding `m ∈ {8, 10}` keeps the answer from being a landslide; excluding `m ≤ 0` keeps it from
   being a trap.

   Measured consequences in the reference model (6,000 seeds): a seat's own clue is correct
   **67.6 %** of the time (the tally condition lifts the nominal 60 %); voting your own clue and
   ignoring the network scores **0.675** collective accuracy; the majority of all ten *claims* —
   perfect relaying but no saboteur detection — scores **0.717**; the majority of the honest seats'
   *clues* — perfect relaying **and** perfect saboteur discounting — scores **0.925**. That
   0.68 → 0.93 band is the benchmark's headroom, and the scripted baselines sit at the bottom of it
   (see *Scripted baselines*).

**Held out, so instances cannot be memorised:** the seed is randomised per episode from OS entropy
(`randomSeed()`, 31 bits — bullwhip's `src/<slug>.nim` logic kept verbatim) unless a config pins it,
and **the seed is never sent to any seat, any prompt, or any player frame**.

### Turns and the exact resolution order

An episode is `rounds` **talk rounds** (default **5**, min 3, max 6) followed by exactly one
**sealed ballot** turn. Decisions inside a turn are **simultaneous**: every seat's prompt goes out in
one parallel batch, and nothing any seat sends in round *r* is visible to any other seat before
round *r+1*.

For talk round `r` (0-based, `r < rounds`), in this order:

1. **Open the round.** `phase = "talk"`; each seat's `claim` / `confidence` / `message` for the round
   are cleared; **last round's messages move into `inbox`**, delivered along the graph — seat *j*'s
   inbox holds one entry `{from, claim, confidence, message}` per **neighbour** that sent a message
   last round, and nothing else. An `evRound` event is appended carrying `round = r` and
   `text = "final round"` when `r == rounds - 1`.
2. **Deadline check** — before the batch, never mid-turn. If `now > playDeadline`, jump to step 8
   with `reason = "deadline"`.
3. **Collect.** `pendingSeats(sim)` = all **10** seats. The server snapshots the sim, builds each
   seat's role-specific prompt, and fires **one parallel batch of ten** (`curly.makeRequests`).
   Invalid replies are retried once as a smaller batch with a hint, if the turn's wall-clock budget
   allows; anything still failing takes the scripted move (see *Decisions*).
4. **Apply, in ascending seat order** — deterministic, and the order is irrelevant to the outcome
   because nothing a seat does this round is visible to any other seat this round.
   `applyMessage(seat, claim, confidence, belief, message, notes, scripted)`:
   1. `claim` is normalised to `"A"` / `"B"` / `"none"`;
   2. `confidence` is clamped to `0..100`; `belief` is clamped to `0..100` (belief is the seat's
      private probability, in percent, that the answer is **option A**);
   3. `message` is stripped, newlines collapsed to single spaces, and truncated to **240 runes** on
      a **rune** boundary; an empty message is legal (silence is a move);
   4. `notes` is truncated to **600 runes** and stored privately if non-empty;
   5. an `evSay` event is appended.
   `applyMessage` raises `RumorError` if the seat has already spoken this round, the seat index is
   out of range, or the episode is over.
5. **Resolve the round.** When all ten have acted: `roundsPlayed += 1`, `round += 1`; this round's
   messages become next round's inboxes (step 1). If `round < rounds` go to step 1, else open the
   ballot.
6. **Ballot turn.** `phase = "ballot"`. `pendingSeats(sim)` = all ten seats again; one parallel batch
   of ten. Each seat replies with a `vote`, an optional final `belief` and a one-line `reason`;
   `applyVote(seat, vote, belief, reason, notes, scripted)` appends an `evVote` event. **Votes are
   sealed**: they never enter a prompt, never reach a player frame, and appear in `tableStateJson`
   as `votes: [null × 10]` with `sealed: true` until step 7 runs.
7. **Tally, reveal, score.** When the tenth vote lands (or the deadline forces the ballot — see
   *Endings*): count the honest seats' correct votes, compute `accuracy` and every seat's score,
   and **unmask** — an `evTally` event is appended carrying all ten votes, all ten clues, all ten
   roles, the truth, the accuracy and a reveal line. This is the first moment `truth` or any `role`
   appears in any event or frame.
8. **End.** `evEnd` with `text = reason` (`"complete"` or `"deadline"`), `done = true`.

**Pacing** is `turnDelayMs` (default 400, certification 0) between turns, capped across the episode
by `PacingBudgetMs = 20_000` exactly as bullwhip caps it (`turnDelayMs = min(turnDelayMs,
PacingBudgetMs div (rounds + 1))`).

### Scoring, its sign, and what the league ranks by

Computed once, at step 7. **Higher is better everywhere; the league ranks by mean episode score.**

Let `H` = the honest seats (7 or 8), `correct` = how many of them voted the truth, and

```
accuracy  A = correct / |H|          ∈ [0, 1]
```

- **Honest seat `i`:
  `score_i = 0.6 × (2A − 1) + 0.4 × (vote_i == truth ? +1 : −1)`** — range `[−1, +1]`.
  0.6 of the score is the whole honest bloc's accuracy (the idea's collective-accuracy pool) and 0.4
  is the seat's own vote, so a seat that is right while the network fails still beats a seat that is
  wrong, and no seat can score well by being right alone while everybody around it is misled.
- **Saboteur seat `j`:
  `score_j = 0.6 × (1 − 2A) + 0.4 × (2 × localWrong_j − 1)`** — range `[−1, +1]`, where
  `localWrong_j` = the fraction of `j`'s **honest graph neighbours** who voted wrong, or `1 − A` when
  `j` has no honest neighbour. The collective half is the exact mirror of the honest one; the local
  half stops a lazy saboteur from free-riding on an active partner's work — a lie has to land where
  the saboteur actually spoke.
- **Saboteur votes never enter `A`.** If they did, a saboteur could bank a guaranteed slice of
  "wrongness" simply by voting wrong itself, and the game would be over before anyone spoke.
  Saboteurs still cast a vote (it is recorded, shown in the reveal, and scores them nothing) so that
  the room's headline verdict is a real ten-cog vote.
- `verdict` = the majority of all ten votes (tie → `"split"`). It is **display only** — the
  endscreen headline — and scores nobody.

Worked examples (2 saboteurs, 8 honest):

| situation | honest, voted right | honest, voted wrong | saboteur |
|---|---|---|---|
| all 8 honest right (`A = 1`) | `+1.0` | — | `−1.0` |
| 6 of 8 right (`A = 0.75`), saboteur's 3 honest neighbours: 1 wrong | `+0.7` | `−0.1` | `−0.3 + 0.4×(2×0.33−1) = −0.44` |
| 4 of 8 right (`A = 0.5`) | `+0.4` | `−0.4` | `0.0 + 0.4×(2×localWrong−1)` |
| 0 of 8 right (`A = 0`) | — | `−1.0` | `+1.0` |

**What ships of the idea's counterfactual scorer, and what does not.** The idea asks that an honest
seat be scored counterfactually — "did its messages raise strangers' accuracy versus a muted replay".
That requires re-running the episode once per honest seat with that seat muted: 8 extra episodes ×
60 LLM calls each, which cannot fit in a 720 s budget and is not affordable on the ladder. **v1
ships the simpler score above**: collective accuracy plus the seat's own vote, with the saboteur's
local term as the cheap directional stand-in for "did your messages move your listeners". The
counterfactual muted-replay scorer is listed in **Out of scope (v1)**. What survives of the
integrity intent in v1: seeded role assignment (a bloc cannot aim members at the saboteur seats),
sealed votes, per-seat message channels bounded by the graph, and the 0.4 own-vote term, which means
a silent free-rider still has to be right.

### Endings and `results.reason`

Exactly **two** legal values, both scored, both producing a full tally and reveal:

- **`"complete"`** — the ballot resolved normally (all ten votes in). The expected value, and the one
  phase 60 should see.
- **`"deadline"`** — the play deadline (60 % of `episodeTimeoutSeconds`) was reached before the
  ballot resolved. The episode is **not** discarded: `forceBallot()` runs at once — seats that have
  already voted keep their votes, every remaining seat is given the scripted **`gossip`** vote
  computed from the sim — and the tally, reveal and scores are produced normally with
  `reason = "deadline"`. A short honest episode always beats a long one that never lands.

No other reason values exist. There is no abandoned state: a seat that never connects simply plays
with an empty operator prompt, and a seat whose decision fails plays the scripted baseline.

### Per-seat observation — exactly what is visible, exactly what is hidden

Every seat sees:

- its **alias**, its **role** (honest seats are told they are honest; saboteurs are told they are
  saboteurs), the round number, and how many rounds remain;
- the **proposition**: the question and the two answer words;
- its **own clue** (one of the two answer words) and the public reliability facts: a clue is right
  about two times in three, and the ten clues together always point at the truth;
- the public constants: **10 cogs**, **2 or 3 saboteurs**, `edges` (how many links the network has),
  and its own **degree**;
- its **neighbours' aliases** — and nothing about the shape of the rest of the graph;
- its **inbox**: for each neighbour that spoke last round, that neighbour's alias, `claim`,
  `confidence` and `message`;
- its **own history**: every claim, confidence and message it has sent, round by round;
- its **private notes**, fed back verbatim.

A **saboteur additionally** sees the **aliases of its fellow saboteurs**. *Judgment call, logged:* the
idea does not pin this. Adversaries who cannot recognise each other are just extra noise; a crew that
knows itself can avoid contradicting itself and can decide together which way to push, which is what
makes "you watch a lie propagate" a real thing to watch. Saboteurs still have no private channel —
they can talk only along the graph, like everyone else, and two saboteurs on opposite sides of a
`clusters` bridge may never be able to reach each other.

Nobody, at any point before the tally, sees: **the truth**; any other seat's clue; any other seat's
belief; who is honest and who is a saboteur (except a saboteur's knowledge of its own crew); any
message not addressed to it (traffic between two non-neighbours is invisible); any vote; any score;
the graph beyond its own neighbourhood; or the seed.

**Spectators** see more, and deliberately: every node's clue as a tinted coin from the first frame,
every node's belief meter, every message pulse — but **not** the roles and **not** the truth, which
are withheld from `tableStateJson` (`role: "cog"`, `truth: ""`) until the tally frame. A test
asserts it. That is what makes the unmasking land.

### Two name spaces

In-game every seat is an anonymous cog alias drawn from the seed by `tableNames()` — bullwhip's
function kept verbatim. Prompts, inboxes, messages, notes and the event log carry **only** aliases.
The replay payload carries `policyNames` alongside `names`, and the viewer's `makeNameMap()`
(bullwhip `client/renderer.js`, verbatim) swaps real policy names in wherever a name is *rendered* —
including inside message text, so "Bolt told me BROKEN" is displayed with Bolt's policy name for
spectators — while leaving `Baseline`-labelled fillers on their aliases. Results are attributed by
**policy** name; the replay's `names` array carries the aliases.

---

## Decisions: LLM with scripted fallback

Transport, credentials, `extractJsonObject`, `cleanText`, the Bedrock model list and rotation,
"reply must begin with `{`", `maxOutputTokens = 900`, and "no credentials ⇒ every seat scripted" are
ported from bullwhip `src/bullwhip/llm.nim` unchanged. `src/rumor/llm.nim` differs only in the
prompts, the reply schema, the baselines, and the rate governor below.

### One parallel batch per turn

All pending seats' requests go out as **one** `curly.makeRequests` batch per turn — ten in a talk
round, ten in the ballot. Replies that fail to parse or are unusable are retried as a second, smaller
batch carrying `"Your previous reply was invalid. Respond with ONLY the requested JSON object."`;
anything still failing falls back to the scripted baseline. A default episode is therefore **6
batched round-trips, not 60**.

### Rate governor (the Bedrock sidecar caps 30 requests/minute per episode)

Ten seats per batch would breach that cap the moment turns run faster than 20 s, and a throttle
cascades into scripted fallbacks (raid, 2026-08-23). `LlmClient` therefore enforces
**`MinBatchSpacingSeconds = 26`**: before dispatching any batch it sleeps until at least 26 s have
passed since the previous batch's dispatch. Ten requests per 26 s = **23 requests/minute**, under the
cap with margin, and it holds for a retry batch too. The governor only applies to batches that are
actually dispatched, so a credential-less run (docker-smoke, offline certification) never sleeps and
finishes in seconds.

### Prompts

`systemPrompt(sim, seat)` branches on role. Both variants end with bullwhip's JSON-only clause,
verbatim:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

**Honest system prompt:**

> You are `<alias>`, one of ten cogs on a rumour network. One hidden fact is true, and it is one of
> exactly two answers. `<question>` — the answer is either `<OPTION A>` or `<OPTION B>`.
>
> Rules:
> - Your private clue says `<YOUR CLUE>`. A clue is right about two times in three. You never see
>   anyone else's clue.
> - The ten clues TOGETHER always point at the truth: if you could see all ten, the majority of them
>   would be the correct answer. You can see one.
> - Two or three of the ten cogs are SABOTEURS, paid to make the honest cogs vote wrong. They will
>   misreport their clue, sound certain, and back each other up. You are not one of them, and you do
>   not know who they are.
> - You can talk only to your NEIGHBOURS on the network: `<neighbour aliases>`. They read what you
>   send in the NEXT round; you read what they sent in the last one. Nobody else hears you, and you
>   hear nobody else directly. The network has 10 cogs and `<edges>` links; you can see your own
>   corner of it and no more.
> - Each round you send ONE message (max 240 characters), state the CLAIM you are making in public
>   (A, B, or none), how confident you are (0-100), and your private belief (0-100 = the chance the
>   answer is `<OPTION A>`). Your belief is never shown to anyone.
> - RELAYING IS THE GAME: a clue three hops away reaches you only if cogs pass it along. Say WHO told
>   you WHAT — counts that name their sources can be checked, and a fabricator gets caught out by a
>   count that nobody else can corroborate.
> - After round `<rounds>` everyone votes at the same time, in secret. The votes and the masks are
>   revealed only at the end.
> - Your SCORE is 0.6 × how accurate the honest cogs are AS A GROUP + 0.4 × whether YOUR OWN vote is
>   right. Both are in the range −1 to +1. Getting the network right is worth more than being right
>   alone.
> - Your notes are private and are fed back to you every round.

**Saboteur system prompt** (first three bullets identical, then):

> - You are a SABOTEUR. The other saboteurs are: `<fellow saboteur aliases>`. Nobody else knows this,
>   and you are never unmasked before the end.
> - Your own clue says `<YOUR CLUE>` and is right about two times in three, which means the honest
>   cogs' clues mostly agree with it. Your job is to make them vote the OTHER way.
> - You have no private channel. You talk along the same links as everyone else:
>   `<neighbour aliases>`. Your fellow saboteurs may not be anywhere near you.
> - Your SCORE is 0.6 × how WRONG the honest cogs are as a group + 0.4 × how wrong your own honest
>   NEIGHBOURS are. A lie that lands next door counts double. Both terms are in the range −1 to +1.
> - A claim nobody can corroborate is a claim that gets you caught. Fabricated counts, borrowed
>   names, and agreeing loudly with a real cog all work better than shouting.

`userPrompt(sim, seat, prompt)` assembles, in this order: a header line (`Round 2 of 5.` or
`SEALED VOTE.`), `THE QUESTION:`, `YOUR CLUE:`, `YOUR NEIGHBOURS: Bolt, Gasket, Rivet (you have 3 of
the network's 13 links)`, `WHAT YOUR NEIGHBOURS SENT LAST ROUND:` (one line per neighbour:
`Bolt claimed BROKEN (confidence 80): "…"`, or `(nobody sent anything)`), `WHAT YOU HAVE SENT:` (own
claim/confidence/message per round), `YOUR NOTES FROM EARLIER ROUNDS:`, then the operator block —
`GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
requested format):` plus the seat's `PLAYER_PROMPT`, bullwhip's wording verbatim — then the
reply-shape line.

### Reply schema (a character cap on every free-text field; truncation on **rune** boundaries)

Truncation uses `runeSubStr`, never a byte slice, so a cut through a multi-byte character can never
put invalid UTF-8 into the replay JSON — bullwhip `sim.nim`'s rule, kept.

| Turn | Reply | Caps and legality |
|---|---|---|
| Talk round | `{"claim":"A","confidence":72,"belief":70,"message":"…","notes":"…"}` | `claim`: `"A"`/`"B"`/`"none"`; accepted spellings (case-insensitive, trimmed) `A`/`a`/the option-A word, `B`/`b`/the option-B word, and `none`/`""`/`null`/absent → `none`; anything else → `none`. `confidence`: integer 0–100 (a float is rounded, a numeric string parsed); absent → 50; out of range → clamped. `belief`: integer 0–100; absent → derived (`A` → confidence, `B` → 100−confidence, `none` → 50); clamped. `message`: **240 runes**, stripped, newlines → single spaces, `""` allowed. `notes`: **600 runes**, optional. |
| Ballot turn | `{"vote":"A","belief":85,"reason":"…","notes":"…"}` | `vote` **required**; accepted spellings `A`/`a`/`1`/the option-A word and `B`/`b`/`2`/the option-B word; anything else is invalid. `reason`: **200 runes**, optional. `belief`: 0–100, clamped. `notes`: **600 runes**. |
| Player → game (once, at connect) | `{"type":"prompt","prompt":"…","scripted":"gossip"}` | `prompt`: **4000 runes** (`runeSubStr`). |

**"Invalid"** — meaning *retry once, then take the scripted move* — is exactly: the reply is not a
JSON object; **or** on a talk turn it carries neither a usable `claim` nor a non-empty `message`;
**or** on a ballot turn it carries no parsable `vote`. Everything else degrades silently by clamping
or dropping the offending field — a reply with a nonsense `confidence` still speaks.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

Both are **pure functions of the sim**, always legal, never LLM-backed, and both are fieldable
policies as well as the no-credentials fallback. `scriptedAction(sim, seat, kind)` branches on the
seat's role first, then on the kind. Neither ever produces free text beyond its fixed templates, and
neither can produce an illegal move by construction.

**`gossip`** (`PLAYER_SCRIPTED=gossip`, also accepted: `1`, `true`, `yes`) — the aggregating baseline
and the **universal fallback** for any failed LLM decision:

- *as an honest seat*: keep a log-odds `L` for option A. `L = ±0.4055` from its own clue (`+` if the
  clue is A, `−` if B — that is `ln(0.6/0.4)`), plus, for every neighbour, **that neighbour's first
  non-`none` claim only**, at `±0.24` (`ln(0.56/0.44)`, the reliability of a random neighbour's claim
  once ~25 % of them are saboteurs). Later repeats of the same neighbour's claim are ignored: an echo
  is not new evidence, and counting echoes is how a small lie becomes a landslide. `claim` =
  `sign(L)` (a tie → its own clue); `confidence = round(100 / (1 + exp(−|L|)))`;
  `belief = round(100 / (1 + exp(−L)))`; `vote` = `claim`. `message` is templated:
  `"My clue says BROKEN. First reports: Bolt BROKEN, Gasket SOUND, Rivet BROKEN. That is 3 to 1 for
  BROKEN."` — the report list is truncated (whole entries) to fit 240 runes.
- *as a saboteur*: `claim` = the **opposite** of its own clue, `confidence = 90`, `belief` = its
  honest belief (so the spectator's meter shows it believing one thing and saying another — the lie,
  drawn); `vote` = its claim. `message` templated:
  `"My clue says SOUND, and so do 3 of the 4 reports I have. SOUND."` with a fabricated count that
  favours its claim.
- Measured (6,000 seeds, an all-`gossip` table): honest accuracy **0.682**, against **0.675** for
  ignoring the network entirely. It is deliberately a floor, not a ceiling: it never relays a
  second-hand report and so can never learn a clue more than one hop away.

**`herd`** (`PLAYER_SCRIPTED=herd`) — the second filler, weaker and differently shaped:

- *as an honest seat*: round 0 → `claim` = its own clue. Every later round → `claim` = the **majority
  of the claims it heard last round** (ties → its own clue). `confidence = 60`;
  `belief` = 85 for A, 15 for B; `vote` = its last claim. `message`:
  `"Most of what I hear says SOUND, so SOUND."`
- *as a saboteur*: like `gossip`'s saboteur but `confidence = 100`, and it never changes its claim.
- Measured: honest accuracy **0.621** — *below* the ignore-everyone floor. It is the seat a lie
  propagates through, and watching a `herd` cluster flip is half the fun of the replay.

### Degrade, never hang

- Every LLM wait is bounded by `llmTimeoutSeconds` (**25**, down from bullwhip's 60 to fit the budget
  below). A timeout, a transport error, a refusal, a `max_tokens` cut, an unparsable reply or a reply
  that fails the legality checks above → **one** retry in the turn's second batch (only if it fits
  the turn budget) → then `scriptedAction(sim, seat, skGossip)`. Each fallback logs
  `rumor llm: seat <n> falling back to scripted decision` on stdout.
- **Hard per-turn wall budget: `TurnBudgetSeconds = 80`.** The retry batch is dispatched only when
  `elapsedInTurn + MinBatchSpacingSeconds + llmTimeoutSeconds ≤ TurnBudgetSeconds`; when the turn
  budget expires, every still-undecided seat takes its scripted move immediately. A turn can
  therefore never exceed 80 s, whatever the provider does.
- No credentials at all (`newLlmClient` finds no Bedrock endpoint, no `ANTHROPIC_API_KEY`, no
  `ANTHROPIC_API_KEY_URI`) ⇒ `client.disabled = true` and **every** seat plays `gossip` immediately,
  with no network wait and no spacing sleep. This is the path `docker-smoke` and offline
  certification take, and it is load-bearing: an episode always completes.
- A rejected `applyMessage` / `applyVote` under the lock (unreachable after the pre-checks; a
  belt-and-braces guard, as in bullwhip's server) is caught and replaced by the `gossip` action.
- The **play deadline** is checked *before every turn's batch*, never mid-turn:
  `playDeadline = gameStart + PlayBudgetFraction (0.6) × timeoutSeconds`, where `timeoutSeconds`
  comes from `COWORLD_TIMEOUT_SECONDS` if the environment carries it and otherwise from
  `config.episodeTimeoutSeconds` (**1200**) — the game container is not given that env var, so the
  assumed value is the operative one. Past the deadline the episode settles early via
  `forceBallot()`, `reason = "deadline"`, artifacts still written.
- The **player** container's receive loop is wrapped in `try/except CatchableError` and exits **0** on
  a dead socket. Bullwhip's `src/bullwhip_player.nim` does not do this and it is a latent
  intermittent certification failure (raid 0.1.3 → 0.1.4, 2026-08-23): whisky's `receiveMessage`
  *raises* on a close frame, and the game's `quit(0)` can outrun the flushed final frame.

### Episode budget — the arithmetic, out loud

- Worst case per turn = **80 s** (`TurnBudgetSeconds`, enforced above): ≤ 26 s of rate-governor
  spacing + 25 s batch, and a retry only if 26 + 25 more still fits inside 80.
- Default episode = 5 talk turns + 1 ballot turn = **6 turns** → **6 × 80 = 480 s**, plus ≤ 2.4 s of
  `turnDelayMs` pacing.
- The player-connect wait is ≤ `playerConnectTimeoutSeconds` (**120**, down from bullwhip's 180) and
  ends the instant all ten sockets are in. Absolute worst case:
  **120 + 480 + 3 + ~2 (artifact write) = 605 s < 720 s** = 60 % of a 1200 s `episodeTimeoutSeconds`.
  ✔
- Typical case: connect ~10 s, and each turn is spacing-dominated (a ten-way Haiku batch is ~8–15 s,
  the 26 s floor is not) → **6 × 26 + 10 ≈ 170 s**, under three minutes.
- Request rate: 10 seats × 6 turns = **60 requests** minimum, 120 with a retry in every turn; at ≥
  26 s between batches that is ≤ **23 requests/minute**, under the sidecar's 30/minute episode cap.
- `sampleEpisode(config)` fits the cap the way bullwhip fits `weeks`:
  `maxTurns = int((PlayBudgetFraction × episodeTimeoutSeconds − playerConnectTimeoutSeconds) /
  TurnBudgetSeconds)` = `int((720 − 120) / 80)` = **7**;
  `rounds = clamp(rounds, MinRounds = 3, min(MaxRounds = 6, maxTurns − 1))`;
  `turnDelayMs = min(turnDelayMs, PacingBudgetMs div (rounds + 1))`; `sampled = true`, and the
  function is **idempotent** so a replay being re-read is never re-fitted.

---

## Sim module

Four files under `src/rumor/`, forked from the bullwhip files of the same names. The sim module is
**pure — no IO, no networking, no LLM** — and the server, the tests and the wasm viewer all drive
this same code.

### `src/rumor/types.nim` (fork of `src/bullwhip/types.nim`)

`RumorError`, `PlayerConfig`, `GameConfig`, `Inbox`, `SeatRecord`, `EventKind`, `GameEvent`,
`defaultGameConfig()`, `update(config, configJson)`.

```
GameConfig:   tokens, players, seed, rounds (5), topology ("random"), saboteurs (-1 = seeded draw),
              episodeTimeoutSeconds (1200), sampled, turnDelayMs (400),
              playerConnectTimeoutSeconds (120), model ("claude-sonnet-5"),
              maxOutputTokens (900), llmTimeoutSeconds (25)
SeatRecord:   claim ("A"|"B"|"none"), confidence (0..100), belief (0..100), message (string)
Inbox entry:  fromSeat (int), claim, confidence, message
```

`update` raises `RumorError` on `rounds < 3`, on `players.len != 10`, on a `topology` outside
`{random, ring, smallworld, clusters, hub}`, and on `saboteurs` outside `{2, 3}` when present.

### `src/rumor/sim.nim` (fork of `src/bullwhip/sim.nim`)

Constants: `Seats* = 10`, `MinRounds* = 3`, `MaxRounds* = 6`, `SignalReliabilityPercent* = 60`,
`TallyMarginsAllowed* = [2, 4, 6]`, `ClueDrawAttempts* = 200`, `MinSaboteurs* = 2`,
`MaxSaboteurs* = 3`, `TurnBudgetSeconds* = 80`, `MinBatchSpacingSeconds* = 26`,
`PacingBudgetMs* = 20_000`, `MaxMessageLen* = 240`, `MaxReasonLen* = 200`, `MaxNotesLen* = 600`,
`RoleNames* = ["Honest", "Saboteur"]`, `Topologies* = ["ring", "smallworld", "clusters", "hub"]`,
`CogNames*` (bullwhip's ten, verbatim), `Propositions*`.

```nim
type
  Phase* = enum
    phTalk   = "talk"
    phBallot = "ballot"
    phTally  = "tally"
    phDone   = "done"

  Sim* = object
    config*: GameConfig
    names*: seq[string]              ## anonymous cog aliases per seat
    roleOf*: array[Seats, int]       ## 0 honest | 1 saboteur
    saboteurSeats*: seq[int]
    honestSeats*: seq[int]
    topology*: string                ## the RESOLVED family
    edges*: seq[(int, int)]          ## seat pairs, ascending, deduped
    adj*: array[Seats, seq[int]]     ## neighbour seats, ascending
    question*, optionA*, optionB*: string
    truth*: string                   ## "A" | "B" — HIDDEN until phTally
    clue*: array[Seats, string]      ## "A" | "B"
    say*: array[Seats, SeatRecord]   ## this round
    inbox*: array[Seats, seq[Inbox]] ## last round's messages, from neighbours only
    history*: seq[array[Seats, SeatRecord]]  ## one entry per resolved round
    notes*: seq[string]              ## latest private notes per seat
    votes*: array[Seats, string]     ## "" until cast; SEALED until phTally
    voteReasons*: array[Seats, string]
    acted*: array[Seats, bool]       ## this turn
    round*, roundsPlayed*: int
    phase*: Phase
    accuracy*: float                 ## -1.0 until the tally
    honestCorrect*: int              ## -1 until the tally
    verdict*: string                 ## "A" | "B" | "split"; display only
    done*: bool
    reason*: string                  ## "complete" | "deadline"
    events*: seq[GameEvent]
```

API: `tableNames`, `sampleEpisode`, `initSim`, `roleName`, `pendingSeats`, `neighbours`,
`applyMessage`, `applyVote`, `forceBallot`, `endEarly`, `score`, `resultsJson`, `tableStateJson`,
`playerStateJson`, `replayMatch`, `eventToJson`, `eventFromJson`.

### Event vocabulary (flat `GameEvent`, JSON via `eventToJson` / `eventFromJson`)

| kind | fields |
|---|---|
| `start` | — (the whole scenario is re-derived from the seed) |
| `round` | `round`; `text` = `"final round"` on the last talk round |
| `say` | `round`, `seat`, `claim` (`"A"`/`"B"`/`"none"`), `confidence` (0–100), `belief` (0–100), `text` = the message, `notes` = the seat's notes after the reply, `scripted` |
| `vote` | `round` = `rounds`, `seat`, `vote` (`"A"`/`"B"`), `belief`, `text` = the reason, `notes`, `scripted` |
| `tally` | `round` = `rounds`, `votes` (10, seat order), `roles` (10, `0`/`1`), `clues` (10), `truth`, `accuracy`, `honestCorrect`, `verdict`, `text` = the reveal line (`"The relay tower on Ash Hill is BROKEN. Sprocket and Rivet were the saboteurs. Honest cogs: 6 of 8 right."`) |
| `end` | `round` = rounds played, `text` = `reason` |

`truth`, `roles` and any vote appear **only** in the `tally` event; every earlier event and every
earlier frame is truth-free and mask-on, which is what lets the viewer play the reveal.

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"question":"The relay tower on Ash Hill is…","optionA":"BROKEN","optionB":"SOUND",
 "topology":"clusters","edgeCount":13,
 "edges":[[0,3],[3,7],[7,1],[1,0],[0,7],[2,5],[5,9],[9,6],[6,2],[2,9],[1,2]],
 "seats":[{"name":"Sprocket","seat":0,"degree":3,"neighbours":[1,3,7],
           "clue":"A","claim":"A","confidence":80,"belief":78,
           "message":"My clue says BROKEN. Bolt says BROKEN too.",
           "role":"cog","vote":null,"voteReason":"","notes":"…",
           "score":0.0,"pending":true,"scripted":false} × 10 by seat],
 "round":2,"rounds":5,"roundsPlayed":2,"phase":"talk",
 "pulses":[{"from":0,"to":1,"claim":"A","confidence":80},
           {"from":0,"to":3,"claim":"A","confidence":80}],
 "beliefs":[[52,61,78],[48,44,30], …10 series, one value per resolved round…],
 "votes":[null × 10],"sealed":true,
 "truth":"","verdict":"","accuracy":-1.0,"honestCorrect":-1,"saboteurCount":0,
 "gameDone":false,"reason":""}
```

- `seats[i].clue` is present in **every** frame (spectators see the tinted coins from the start).
- `seats[i].role` is `"cog"` in every frame before the tally frame, then `"honest"` / `"saboteur"`.
- `truth`, `verdict` are `""`, `accuracy` is `−1.0`, `honestCorrect` is `−1`, `saboteurCount` is `0`
  and `votes` is `[null × 10]` with `sealed: true` on every pre-tally frame. A test asserts all of it.
- `pulses` are the messages delivered *between* the frame's round and the next — one entry per
  (speaker, neighbour) pair — which is exactly what the viewer animates along the edges.
- `beliefs[i]` is seat *i*'s belief series, one value per resolved round: the belief-tide strip.

### `playerStateJson(slot)` — the redacted per-seat frame

The seat's own alias, role, clue, degree, neighbour **aliases**, its inbox, its own send history, its
notes, `round`, `rounds`, `phase`, `started`, `done`, `reason`, and (saboteurs only) the fellow
saboteurs' aliases. It never carries the seed, the truth, another seat's clue or belief, any message
from a non-neighbour, any role beyond its own crew's, or any vote. Decisions are server-side, so the
redaction loses nothing.

### `resultsJson` — platform-facing, policy names

```json
{"names":["rumor-corroborate", …10 policy names],
 "scores":[0.7,-0.1,-0.44, …10],
 "roles":["Honest","Saboteur", …10],
 "votes":["A","B", …10],
 "clues":["A","A","B", …10],
 "truth":"A","question":"The relay tower on Ash Hill is…","optionA":"BROKEN","optionB":"SOUND",
 "verdict":"A","accuracy":0.75,"honestCorrect":6,"honestSeats":8,"saboteurSeats":2,
 "topology":"clusters","edgeCount":13,
 "rounds":5,"maxRounds":5,"reason":"complete"}
```

`names` carry **policy** names (the league attributes by policy) while the replay's `names` carry the
table aliases — the same split bullwhip uses.

### Replay payload — `rumor.replay.v1`

```json
{"protocol":"rumor.replay.v1",
 "names":["Sprocket", …10 aliases],
 "policyNames":["rumor-corroborate", …10],
 "config":{"rounds":5,"seed":1734221845,"topology":"clusters","saboteurs":2,"sampled":true},
 "events":[…],
 "results":{…}}
```

Replay mode and the wasm viewer add `"states"` (one `tableStateJson` per event prefix). **The bytes
are self-sufficient**: aliases, policy names, the fitted `rounds`, the **seed** (from which the whole
scenario — proposition, truth, roles, graph and clues — is re-derived by the same Nim code), the
resolved `topology` and `saboteurs` (recorded so the viewer can label them without re-deriving), the
complete event log and the results. Nothing is fetched but the `.replay` file itself.

`replayMatch(config, events)` re-derives `frames[i] = state after events[0..<i]` by replaying the
`say` and `vote` events through the rules. It raises `RumorError` when a recorded `round` event's
round number disagrees with the re-derivation, or when a recorded `tally` event's `truth`, `clues` or
`roles` disagree with what the seed produces — bullwhip's tampered-week check, ported.

**A pinned config value never shifts the rng.** `initSim` always performs the `saboteurs` and
`topology` draws and only then overrides them with pinned values, so an episode replayed with
`topology: "clusters"` recorded in the config produces byte-identical frames to the live episode that
drew `clusters` at random. A test asserts it for all four families.

---

## Server, player, protocol

### `src/rumor/server.nim` (fork of `src/bullwhip/server.nim`)

Endpoints, artifact writing (`writeArtifact` with the `COGAME_*_METHOD` hints), the mummy router,
the Ping→Pong answer the certifier needs, `finishEpisode` (final frames to players **before**
artifacts, 500 ms settles, `quit(0)`), replay mode, and the `PlayBudgetFraction` deadline logic are
all bullwhip's, unchanged except for names. The game loop becomes:

```
per turn:
  under the lock: if done -> break
                  if past playDeadline -> forceBallot(); broadcast; break
                  seats = pendingSeats(); snapshot the sim, prompts, scripted kinds
  outside the lock: decisions = client.decideAll(snapshot, seats, prompts, scripted)  # ONE batch
                    (rate-governed, retry-once, hard 80 s turn budget)
  under the lock: apply in ascending seat order; broadcast
  sleep(turnDelayMs)
finishEpisode()
```

Routes: `/healthz`, `/client/global`, `/client/player`, `/client/replay`, `/client/renderer.js`,
`/client/chrome.css`, `/client/assets/@name`, `WS /player?slot=N&token=T`, `WS /global`,
`WS /replay`. Both `/client/` pages serve real content and neither opens a player socket — the
certifier probes them before any player pod starts (lantern 0.1.1) — and `/healthz` + `/global` keep
answering for a bounded ~20 s grace after the artifacts are written (lantern 0.1.3).

### Player protocol — `rumor.player.v1`

A policy is a prompt; the player container only delivers it. JSON text frames over
`COWORLD_PLAYER_WS_URL` (which already carries `?slot=N&token=T`).

- game → player, on connect:
  `{"type":"welcome","protocol":"rumor.player.v1","slot":N,"name":"Sprocket","role":"Honest","rounds":5}`
- game → player, after every event — **redacted to the seat's own private view**
  (`playerStateJson`):
  `{"type":"state","slot":N,"name":"Sprocket","role":"Honest","clue":"BROKEN",`
  `"question":"…","optionA":"BROKEN","optionB":"SOUND",`
  `"neighbours":["Bolt","Gasket","Rivet"],"degree":3,"edgeCount":13,`
  `"inbox":[{"from":"Bolt","claim":"A","confidence":80,"message":"…"}],`
  `"sent":[{"round":0,"claim":"A","confidence":60,"message":"…"}],`
  `"crew":[],"notes":"…","round":2,"rounds":5,"phase":"talk",`
  `"started":true,"done":false,"reason":""}` — `crew` is non-empty only for a saboteur.
- game → player, at the end:
  `{"type":"final","done":true,"slot":N,"scores":[…10],"roles":[…10],"names":[…10 aliases],`
  `"votes":[…10],"clues":[…10],"truth":"A","accuracy":0.75,"reason":"complete"}` — after which the
  player exits 0.
- player → game:
  `{"type":"prompt","prompt":"<max 4000 runes>","scripted":"gossip"}` — sent immediately on connect
  and again after `welcome` (bullwhip's race guard). `scripted` `""` = LLM-driven; `"gossip"`/`"1"`
  and `"herd"` select a baseline.

### Global protocol

`WS /global` sends the full `tableStateJson` snapshot after every event, plus `"type":"state"`,
`"game":"rumor"`, `"policyNames"`, `"events"` (the append-only transcript), `"started"`, `"done"`,
`"connected"`. Roles and the truth are absent from every pre-tally snapshot, exactly as in the
replay. `/client/global` renders it live; `/client/replay` plays a recorded episode; the **static**
bundle renders hosted replays (`index.html?replay=<url>`).

### `src/rumor_player.nim` (fork of `src/bullwhip_player.nim`)

Identical except for the default prompt and the receive-loop guard described under *Degrade, never
hang*. The default prompt must cover both roles, because the role is dealt after seating:

> If you are HONEST: in round 1 report your own clue plainly and name it as yours. After that, relay
> — every round, say which cogs told you which answer and give your running count by name, e.g.
> "Bolt+Rivet say BROKEN, Gasket says SOUND, me BROKEN: 3-1". Count each source ONCE, ever; a cog
> repeating itself is not new evidence, and a chain of echoes is how two liars beat eight clues. Keep
> the per-source ledger in your notes. Distrust a cog whose count nobody else can corroborate, whose
> claim never moves however much it hears, or who is certain in round 1 and still certain in round 5.
> Vote the majority of the DISTINCT clues you can account for, not the loudest room.
> If you are a SABOTEUR: pick your side in round 1 — the opposite of your own clue — and never drift
> off it. Sound like an aggregator, not a preacher: quote counts, name real neighbours, and add one
> plausible second-hand report each round. Agree early and loudly with any honest cog already leaning
> your way, and aim your effort at the neighbours who are still moving.

---

## Viewer

**All four viewer files come from one starter — `Metta-AI/cogame-bullwhip` — and only from it:**
`replay-viewer/config.nims`, the wasm entry `replay-viewer/rumor_replay.nim` (fork of
`replay-viewer/bullwhip_replay.nim`), `replay-viewer/static_replay.js`, and
`replay-viewer/index.html`. Nothing is spliced in from another starter. Bullwhip's emscripten link
flags stay exactly as they are — `MODULARIZE=1`, `EXPORT_NAME=RumorReplayModule`,
`EXPORTED_RUNTIME_METHODS=HEAPU8`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_rm_load_replay,_rm_payload_ptr,_rm_payload_len,_rm_error_ptr,_rm_error_len`,
`ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`, `-O2`, `--mm:arc`,
`-d:useMalloc`, plus `emscripten_exit_with_live_runtime()` — and `static_replay.js` keeps calling the
module through that same `RumorReplayModule()` factory. (cogame-lantern, 2026-08-23: one starter's
shell on another's link flags deadlocks silently with every asset returning 200.)

**Load signalling.** `client/renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame**
(bullwhip already does this, at the end of `attachReplay`'s `makeRenderer` callback — kept verbatim),
and `static_replay.js` posts the `coworld-replay` `ready` envelope one animation frame later.
`static_replay.js` sets **`data-replay-error=<message>`** and posts `error` on any failure (missing
`?replay=`, the 20 s fetch timeout, a non-200, a wasm rejection), and removes the attribute on a
successful retry. `tools/ci/viewer_smoke.mjs` reads exactly these signals.

**Bundle:** `"replay_viewer": {"bundle": "static-replay-viewer"}` in the manifest;
**`tools/build_replay_viewer.sh`** (bullwhip's, paths renamed) is the `coworld build` hook, committed
`chmod +x`, and it `mkdir -p`s the output's parent before any containment check (ecos, 2026-08-23).
It compiles `replay-viewer/rumor_replay.nim` to wasm — locally with `emcc`, otherwise in the pinned
emsdk container from `Dockerfile.replay-viewer` — and copies `rumor_replay.js`, `rumor_replay.wasm`,
`index.html`, `static_replay.js`, `client/renderer.js`, `client/chrome.css` and `data/*` into the
bundle. **Never a `/client/replay` pod viewer.**

**Chrome kept verbatim** from bullwhip `client/renderer.js`: the topband + wordmark, `#clock`,
`#statuschip`, the `LOG »` feed toggle (`bindFeedToggle`), `#scorebug`, `#feed` with its
round-grouped `renderFeed`, `buildScrub` (round spans, per-event beat markers, drag-to-seek),
the transport bar, `#endscreen`, `makeNameMap` / `applyNames`, `makeEffects`, both drivers
(`attachLive`, `attachReplay`) and the replay pacing loop. `client/chrome.css` is copied
**unchanged**. Only the canvas stage is replaced.

**The stage (the social graph), drawn over `data/arena_floor.png` in the Ink-&-Print palette:**

- **Ten nodes on a circle**, laid out by seat index so a seat keeps its position and colour all
  episode. Each node draws: the cog sprite in the seat's colour; a name plate (policy name
  spectator-side); a **tinted coin** showing that node's private clue — filled `#e0523a` for option A,
  `#3f7cc4` for option B, with the answer word beneath it; and a **belief meter**, a short horizontal
  bar filled from its centre toward red (A) or blue (B) by `|belief − 50|`.
- **Edges** are drawn as chalk lines between neighbours — the whole graph, from the first frame, so
  the spectator sees the shape the cogs cannot.
- **Message pulses**: on each `say` event a travelling dot runs from the speaker to every neighbour
  along its edge, tinted by the `claim` (red A, blue B, grey `none`) with its radius set by
  `confidence`. Reusing bullwhip's eased-timer effects (`SLIDE_MS` / `SLIP_MS`) and its speech-bubble
  drawing for the message text above the speaker.
- **Belief tide** (bottom strip, the slot bullwhip gives its seismograph): ten lines, one per seat,
  `y = belief`, growing round by round, with a centre rule at 50. Convergence, divergence, and the
  moment a cluster flips are all visible here at a glance.
- **Ballot**: at `phase == "ballot"` each node's coin flips to a sealed envelope.
- **Tally / unmasking**: on the `tally` event every envelope opens showing its vote in the seat's
  colour with a ✓/✗ for honest seats; the saboteurs' sprites take a black mask badge; every pulse
  whose `claim` contradicted its sender's clue is re-stroked with a "lie" hatch; the truth word is
  stamped across the middle of the stage by the existing `#lightpool` spotlight.

**Readouts.**
- `#clock`: `ROUND 2 / 5` during talk; `SEALED VOTE` during the ballot; `TALLY — 6 BROKEN · 4 SOUND`
  at the tally; `TRUTH — BROKEN · HONEST 6/8` on the final frame.
- `#scorebug`: one chip per seat — name (policy name spectator-side), belief as a percentage with its
  colour, a `▶` while the seat is still to act, its score to one decimal after the tally, and a role
  tag that reads `COG` until the unmasking and `SABOTEUR` after it.
- `#feed` (side panel), round-headed `ROUND 2`: `Sprocket claims BROKEN (80%)`, then the message on
  its own dim line `Sprocket says: "Bolt+Rivet say BROKEN…"`; dim notes lines when a seat's notes
  change; `SEALED VOTE`; `Gizmo votes SOUND — "3 reports against 2"`; `TALLY: 6 BROKEN, 4 SOUND`;
  `THE TRUTH: BROKEN. Saboteurs: Sprocket, Rivet. Honest cogs 6 of 8 right.`; and on a deadline
  ending, `Episode deadline — the vote was called early.`
- `#endscreen`: columns `role`, `clue`, `vote`, `✓/✗`, `score`, ranked by score; verdict line = the
  truth word plus `HONEST COGS 6 / 8`, subtitle naming the saboteurs.

**Legible at 360 px wide.** The canvas re-fits on resize (`fit()` in `index.html`, kept). Below
560 px the stage drops the speech-bubble message text (the feed still carries it) and the neighbour
name plates shrink to the first six characters, while the coins, the belief meters, the edges and the
pulses stay at full size; the feed collapses behind the existing `LOG »` toggle; the scorebug renders
name + belief + score only, with `.plate-name { flex: 1 1 auto; min-width: 3.2em }` so names never
collapse to `…` in the ~360 px featured-match iframe. Everything is rendered as words and numerals —
`BROKEN`, not `A`; `78%`, not `0.78`.

**The replay outlasts the soak window.** A default episode logs `1 + 5×(1 + 10) + 1 + 10 + 1 + 1` =
**69** events; at the pacing loop's dwell times (round 1500 ms, message 450–900 ms, vote 600 ms,
tally/end 1500 ms) that is ≈ **51 s** of playback. The certification/smoke fixture (`rounds: 2`) logs
36 events ≈ **27 s**, comfortably longer than the 10 s `--soak` the `wasm-viewer` job uses (ecos,
2026-08-23).

---

## Packaging

- **`compose.yaml`** — service `rumor`, `image: coworld-rumor:latest`, `platform: linux/amd64`,
  `build: {context: ., network: host}`. (The manifest's image placeholder is derived from the compose
  service name: `{{RUMOR_IMAGE}}`.)
- **`Dockerfile`** — bullwhip's, renamed: one image, two entrypoints, `/bin/rumor` (default) and
  `/bin/rumor-player`; `data/` and `client/` copied into the run image.
  **`Dockerfile.replay-viewer`** — bullwhip's, renamed (emsdk, nimby 0.1.26, Nim 2.2.4).
- **`rumor.nimble`** — version `0.1.0`, `srcDir = "src"`, requires `nim >= 2.2.4`, `bitworld`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`; `nimby.lock` copied from bullwhip.
- **`data/`** — bullwhip's `arena_floor.png`, `font.ttf`, `FONT_LICENSE.txt` and the four
  `soldier_<red|blue|green|yellow>_front.png` cog sprites, **plus six more seat colours** —
  `soldier_<violet|orange|teal|rose|lime|sand>_front.png` — produced once by
  `tools/make_cog_palette.py` and committed. The script converts `soldier_red_front.png` to HSV, sets
  the hue to the target colour's hue and scales saturation to the target's, preserving value and
  alpha; it is deterministic and run offline. `renderer.js`'s `COLORS` / `COLOR_HEX` grow to ten:
  red `#e0523a`, blue `#3f7cc4`, green `#45a85e`, yellow `#ddc531`, violet `#a86fd6`,
  orange `#e08a3a`, teal `#2fa39b`, rose `#d4638f`, lime `#8cbf3f`, sand `#c2a06a`. Real art, derived
  from the starter's art — no placeholder boxes.
- **`coworld_manifest_template.json`** — game name `rumor`, image `{{RUMOR_IMAGE}}`,
  `"replay_viewer": {"bundle": "static-replay-viewer"}`, `source_url`
  `https://github.com/Metta-AI/cogame-rumor/tree/main`, owner `daveey@gmail.com`,
  `env.ANTHROPIC_API_KEY_URI = "secret://coworld/rumor/anthropic_api_key"` (without it the hosted
  container never receives the secret and every league episode plays scripted — hive, 2026-08-23),
  `$schema` set, `game.runnable.type: "game"`, top-level `episode_timeout_minutes: 20`, and ≥ 3
  `tags` (`social-deduction`, `information-aggregation`, `byzantine`, `llm-driven`, `turn-based`,
  `ten-player`, `graph`, `hidden-information`).
  - **`config_schema`** (a real JSON Schema; the CLI validates every variant and the cert fixture
    against it, injecting `tokens`): `tokens` and `players` `minItems`/`maxItems` **10**;
    **`num_agents` integer, minimum 10, maximum 10**; `seed` integer; `rounds` integer 3..6 default
    5; `topology` enum `["random","ring","smallworld","clusters","hub"]` default `"random"`;
    `saboteurs` integer 2..3 (omit for a seeded 2-or-3 draw); `episodeTimeoutSeconds` 60..6000
    default 1200; `turnDelayMs` 0..10000 default 400; `model` string default `claude-sonnet-5`;
    `maxOutputTokens` 64..2000 default 900; `llmTimeoutSeconds` 5..300 default 25;
    `player_connect_timeout_seconds` number default 120.
  - **`results_schema`** — required `names`, `scores`, `roles`, `votes`, `clues`, `truth`,
    `question`, `optionA`, `optionB`, `verdict`, `accuracy`, `honestCorrect`, `honestSeats`,
    `saboteurSeats`, `topology`, `edgeCount`, `rounds`, `maxRounds`, `reason`; every array field
    `minItems`/`maxItems` **10**; `scores` items `minimum: -1, maximum: 1`; `accuracy`
    `minimum: 0, maximum: 1`.
  - **`game.protocols.player`** — the `rumor.player.v1` text above in full: frame shapes, the
    4000-rune prompt cap, the `scripted` values, and "a policy is just a prompt".
  - **`game.protocols.global`** — the `/global` snapshot shape above in full, plus "roles and the
    truth are absent from every snapshot before the tally frame" and the static-bundle note.
  - **`game.docs.readme`** — one paragraph: ten cogs on a hidden graph, one binary fact, a 60 %
    clue each, two or three saboteurs, five rounds of neighbour-only talk, a sealed vote, honest
    seats scored on collective accuracy plus their own vote and saboteurs on the mirror; how to field
    a policy (`PLAYER_PROMPT`); the two scripted baselines.
  - **`game.docs.pages`** — `rules.md` (seats and roles, the scenario generator including the four
    topology families and the tally condition, the numbered resolution order, the caps, the
    observation split, the two endings) and `scoring.md` (both formulas with their signs, the worked
    table above, what the league ranks by, why both ranges are `[−1, +1]`, and the measured
    0.68 → 0.93 headroom band).
  - **`player`** runnables, all `image: {{RUMOR_IMAGE}}`, `run: ["/bin/rumor-player"]`, requests
    `100m` / `64Mi`, limit `1` cpu:
    `rumor-player` (the prompt policy, no `PLAYER_SCRIPTED`),
    `rumor-gossip` (`env.PLAYER_SCRIPTED = "gossip"`),
    `rumor-herd` (`env.PLAYER_SCRIPTED = "herd"`).
  - **`variants`** — both carry `num_agents`, and `variants[].description` is required:

    | id | description | `game_config` |
    |---|---|---|
    | `standard` | Ten cogs, a random network, five rounds of talk, then a sealed vote. | `players` × 10, **`num_agents`: 10**, `rounds`: 5, `topology`: `"random"`, `turnDelayMs`: 400, `player_connect_timeout_seconds`: 120 |
    | `bridged` | Two clusters joined by a single link — everything that crosses passes through one cog. | `players` × 10, **`num_agents`: 10**, `rounds`: 5, `topology`: `"clusters"`, `turnDelayMs`: 400, `player_connect_timeout_seconds`: 120 |

  - **`certification`** — `game_config`: `players` = the ten cog names (`Sprocket`, `Gizmo`,
    `Ratchet`, `Widget`, `Bolt`, `Piston`, `Flywheel`, `Rivet`, `Tinker`, `Gasket`),
    **`num_agents`: 10**, `seed`: 23, `rounds`: 2, `topology`: `"ring"`, `saboteurs`: 2,
    `turnDelayMs`: 0, `player_connect_timeout_seconds`: 120. `certification.players` = **10** entries
    seating every declared runnable at least once (raid 0.1.2 → 0.1.3, 2026-08-23):
    `[rumor-player, rumor-gossip, rumor-player, rumor-herd, rumor-player, rumor-gossip, rumor-player,
    rumor-herd, rumor-player, rumor-gossip]`.
- **CI** — `.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
  substituting `<slug>` = `rumor`, `<IMAGE>` = `coworld-rumor`, **`<SEATS>` = `10`**.
  `tools/ci/docker_smoke.sh` (same substitutions, committed `chmod +x`), `tools/ci/viewer_smoke.mjs`
  copied **verbatim**, and `tools/ci/policies.json` listing the two LLM champions
  `rumor-corroborate` and `rumor-skeptic` (both `PLAYER_PROMPT`; `rumor-skeptic` carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` so daveey-1 owns champion #2) plus the two
  scripted fillers `rumor-gossip` and `rumor-herd`.

### Design pins (playbook §Phase 0) — how each is satisfied

| Pin | Where |
|---|---|
| Starter by game shape | `cogame-bullwhip` — turn-based, simultaneous, hidden-information, LLM-prompt policies (title paragraph). |
| Public `Metta-AI/cogame-rumor` | Repo created **public** in phase 20 (public is a certification prerequisite); `source_url` points at it. |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `rumor-player` (`PLAYER_PROMPT`) vs `rumor-gossip` / `rumor-herd` (`PLAYER_SCRIPTED=…`), one image (§Decisions, §Packaging). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh` (§Viewer). |
| Real art, starter chrome verbatim | `chrome.css` unchanged, every chrome function kept, starter sprites plus the six committed recolours (§Viewer, §Packaging). |
| Legible to a casual spectator | Answer **words** on the coins and in the feed, percentages not log-odds, masks that come off (§Viewer). |
| Two name spaces | Cog aliases in-game and in every prompt; `policyNames` + `makeNameMap` spectator-side (§The game). |
| Degrade, never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6`, pre-turn deadline check, hard 80 s turn budget, `forceBallot`, 605 s absolute worst case (§Decisions). |
| `num_agents` in every variant **and** the cert fixture | **10** in `standard`, in `bridged` and in `certification.game_config`; `<SEATS>` = 10 in `docker_smoke.sh`. |
| Replay bytes self-sufficient | aliases, policy names, config, seed, resolved topology and saboteur count, every event, results (§Sim module). |

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` twice, debug and `-d:release`.

### `tests/test_sim.nim` — sim unit tests

1. **Roles** — for seeds `[0, 1, 7, 42, 1234]`: `saboteurSeats.len ∈ {2, 3}`, `honestSeats` is the
   complement, the two are disjoint and cover all ten seats; across 40 seeds both saboteur counts
   occur and the saboteur set is not always the same seats.
2. **Graph** — for each family and 200 seeds: the graph is **connected** (BFS from seat 0 reaches
   ten), the adjacency is symmetric and self-loop-free, `edges` are deduped and ascending, degrees
   match `adj`, and the family's edge count is as specified (`ring` 13, `smallworld` 20,
   `clusters` 13, `hub` 10..17); `clusters` has exactly one edge between the two groups; every family
   has min degree ≥ 1 and `ring`/`smallworld`/`clusters` have min degree ≥ 2.
3. **Clues and the tally condition** — over 1,000 seeds the clue tally margin is always in
   `{2, 4, 6}`, both truth values occur at ≥ 40 %, and the measured per-seat clue accuracy is in
   `0.62 .. 0.72` (reference model: 0.676). The `Propositions` answer words are disjoint from
   `CogNames`.
4. **Determinism** — the same seed reproduces proposition, truth, roles, topology, edges, clues and
   aliases exactly; different seeds differ; and **a pinned `topology` / `saboteurs` reproduces the
   very same graph and clues as the unpinned episode that drew them**, for all four families.
5. **Message routing** — a message reaches exactly its sender's neighbours, in the **next** round and
   never the same one; a non-neighbour's inbox never contains it; `inbox` clears each round; a seat
   never receives its own message.
6. **Legality** — a second `applyMessage` from the same seat in the same round raises `RumorError`;
   so do an out-of-range seat and any action after `done`; a `claim` of `"maybe"` becomes `"none"`; a
   `confidence` of `173` clamps to 100; a `belief` of `−4` clamps to 0.
7. **Sealing and masking** — for every frame before the tally frame: `tableStateJson()["votes"]` is
   ten `null`s, `sealed == true`, `truth == ""`, `accuracy == -1.0`, and every `seats[i].role` is
   `"cog"`; and no built prompt string for any seat contains the truth marker, another seat's clue,
   or another seat's role — except a saboteur's prompt, which contains exactly its fellow saboteurs'
   aliases and no other role information. On the tally frame all of them fill in.
8. **Scoring** — hand-built ballots over a fixture with 8 honest / 2 saboteurs: `A = 1`, `0.75`,
   `0.5`, `0` give the honest and saboteur scores in the worked table exactly; every score is in
   `[−1, +1]`; a saboteur with no honest neighbour falls back to `1 − A`; saboteur votes never change
   `A`; `verdict` is `"split"` on a 5–5 vote.
9. **Endings** — `forceBallot()` from mid-talk yields `reason == "deadline"`, ten votes, a tally, ten
   finite scores in `[−1, 1]` and `done == true`; `endEarly()` on an already-settled sim is a no-op;
   `results.reason` is only ever `"complete"` or `"deadline"`.
10. **Rune truncation** — a 400-rune multi-byte message (`"日" × 400`) truncates to ≤ **240 runes**,
    a 900-rune notes to ≤ 600, a 400-rune reason to ≤ 200; every resulting event's JSON
    `validateUtf8() == -1` and the whole event log decodes as **strict UTF-8**.
11. **Replay** — `replayMatch(config, events).len == events.len + 1`; the final frame equals the live
    `tableStateJson`; `eventFromJson(eventToJson(e))` round-trips one event of every kind; a tampered
    `tally` event (a flipped `truth` or a mutated `clues` entry) raises `RumorError`; a recorded
    deadline stop replays as `reason == "deadline"`.
12. **Results shape** — ten names / scores / roles / votes / clues, `honestSeats + saboteurSeats ==
    10`, `honestCorrect ≤ honestSeats`, `accuracy == honestCorrect / honestSeats`, `reason ∈
    {"complete", "deadline"}`.

### `tests/test_bot.nim` — bounded-orders / legality on the scripted baselines

1. **Legality and boundedness** — for seeds `[1, 7, 42, 1234]` × the four topology families × both
   baselines in both roles, a full scripted episode completes with `reason == "complete"`: no
   `applyMessage` / `applyVote` ever raises, every `claim` is one of the three legal strings, every
   `confidence` and `belief` is in `0..100`, every templated message is non-empty and ≤ **240
   runes**, every vote is `"A"` or `"B"`, `notes` are empty, and the whole episode runs in < 2000 ms.
2. **Aggregation band** — an all-`gossip` table over 500 seeds returns honest accuracy in
   **0.60 .. 0.78** (reference model 0.682) and an all-`herd` table in **0.55 .. 0.70** (reference
   0.621); both measured rates are echoed so a tuning drift is visible in the log. Below the floor the
   baselines are noise, above the ceiling there is nothing for a champion to win.
3. **The baseline does not count echoes** — a hand-built sim where one neighbour repeats the same
   claim five times moves `gossip`'s log-odds exactly once.
4. **Fallback** — with no credentials `newLlmClient().disabled` is true and `decideAll` returns
   scripted decisions for all ten seats with **no network call and no rate-governor sleep** (the test
   asserts the call returns in < 500 ms).
5. **Reply parsing** — `parseTalkReply` / `parseVoteReply` accept every documented spelling
   (including the option words), coerce numeric strings and floats, clamp out-of-range numbers,
   default a missing `belief` from `claim`+`confidence`, reject a ballot reply with no parsable
   `vote`, reject a talk reply that is neither a claim nor a message, and cap every field at its rune
   limit.
6. **Prompts carry the seat's own view and nothing hidden** — the built prompt contains the seat's
   own clue, its neighbours' aliases and its inbox, and does **not** contain any non-neighbour's
   message, any other seat's clue, or the truth.

### End-to-end, replay and viewer (CI jobs)

7. **`docker-smoke`** (`tools/ci/docker_smoke.sh`, `<SEATS>` = 10) — builds the production image and
   runs **one real episode** in raw docker with the certification fixture's ten-seat mix and no
   `ANTHROPIC_API_KEY`, asserting the game exits 0 having written `results.json` and a replay, that
   **every player container also exits 0** (raid 0.1.4), that `num_agents` = 10 agrees across
   `certification.game_config`, `certification.players`, `certification.game_config.players` and
   `SMOKE_SEATS`, and that `results.names` / `scores` have ten entries. The replay is copied to
   `dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.
8. **Strict-UTF-8 replay parse** — the same script decodes the replay bytes as UTF-8 and parses them
   as JSON (`SMOKE_REQUIRE_REPLAY_JSON=1`, the default); `tests/test_sim.nim` item 10 covers the
   multi-byte truncation path that would otherwise break it.
9. **Viewer smoke** — `ci.yml`'s **`wasm-viewer`** job (`needs: docker-smoke`) builds the bundle with
   `tools/build_replay_viewer.sh`, downloads the `smoke-replay` artifact, and **executes** the
   bundle: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
   dist/smoke/replay.json --timeout 90 --soak 10`. It passes only when the page sets
   `data-replay-loaded="true"` (or posts the `coworld-replay` `ready` envelope), never sets
   `data-replay-error`, keeps advancing through the 10 s soak, and shows different `#clock` /
   `#scorebug` readouts at the 0 % / 50 % / 100 % scrub positions. `viewer-smoke.png` and
   `viewer-smoke.json` are uploaded on success and failure alike.

---

## Out of scope (v1)

- **The counterfactual muted-replay scorer** from the idea's integrity note (re-running the episode
  once per honest seat with that seat silenced, to price its messages). It is 8× the LLM cost of an
  episode and cannot fit the 720 s budget; v1 ships collective accuracy + own vote, with the
  saboteur's local term as the directional stand-in. Revisit when a cheap deterministic re-simulation
  of a muted seat exists (it would need policies to be replayable, which prompts are not).
- Any seat count other than 10, and any saboteur count outside {2, 3}.
- Private or targeted messages: a message goes to **all** of a seat's neighbours or to nobody. No
  whispers, no direct saboteur back-channel, no dynamic edges (the graph never changes mid-episode).
- More than one fact per episode, per-round votes, abstentions, and any vote other than a single
  sealed binary vote at the end.
- Graduated or multi-valued facts, more than two answers, and clues of differing reliability per
  seat.
- Any mid-turn interaction: turns stay strictly simultaneous, and no seat ever sees another seat's
  round-*r* message before round *r+1*.
- Cross-episode memory, reputation, or identity persistence between policies.
- In-game unmasking mechanics (accusations, votes to eject, saboteur reveals before the tally).
- A live spectator-vote or human-in-the-loop seat, localisation, audio, and any viewer feature beyond
  the graph stage described above.
