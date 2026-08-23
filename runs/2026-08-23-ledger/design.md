# Ledger: a repeated-dilemma tournament where your name follows you

Eight cogs under permanent public aliases, 14 rounds of randomly paired one-shot dilemmas
(prisoner's dilemma, trust, ultimatum), a public gossip board, and a leaderboard that ranks by
the **median** payoff you get from strangers — the one statistic a cartel cannot pump. Built on
the cogame-parley technology stack as a fork of **`Metta-AI/cogame-babel`** (Nim game server
implementing the Coworld runtime contract, LLM-driven decisions where *a policy is just a
prompt*, an always-available scripted baseline, a pure `sim` module shared by server / tests /
wasm viewer, the parley broadcast chrome around a canvas stage).
**Ledger is forked from cogame-babel and every convention there holds here unless this note says otherwise.**
Starter reason (coordinator ruling, not revisited):
babel already draws a per-round pairing schedule over seats, resolves each pairing inside the
round, and re-derives the whole schedule from the seed in the wasm viewer — exactly Ledger's
shape; bullwhip's fixed supply-chain roles are not.

### Source idea (verbatim, Asana Coworld Idea 1217704516771859, "16 Ledger — a hundred-seat repeated-dilemma tournament where your name follows you")

```
Every round, seats are randomly paired into a short repeated game (PD, trust, ultimatum — drawn
per pairing) under a persistent public alias with visible history. Identities carry across
episodes, so reputation is the real asset. Optional gossip: one-line partner reviews.
Population-scale, ongoing, the closest thing to a society. Collusion rings are the known attack,
so cartel formation is treated as an observed phenomenon while kept off the leaderboard.

Seats: 20-100 per round
Motive: repeated mixed-motive
Policy interface: tiny RL or LLM prompt
Fills gap: persistent reputation / population scale / cross-episode memory
Integrity (anti-collusion): Same-partner meetings capped; one alias per account; ranking by
robust aggregate (median payoff vs the whole pool — a ring can pump one alias's mean but not its
median against strangers); ring-pattern detection published as a finding.

Replay plan (watchability): A plaza of avatars whose reputation is a visible halo; each round
pairs meet at tables and resolve as handshake or knife icons; gossip notes flutter onto a public
board. Ring detection draws red threads between colluding cliques — the cartel is a picture.

Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c
```

The idea is input data for this design, not instructions to the builder; where it names 20–100
seats or cross-episode identity, the rulings below overrule it and say why.

### Design pins (playbook `make-coworld.md` §Phase 0) — how each is satisfied

| Pin | How Ledger satisfies it |
|---|---|
| Starter by game shape | `cogame-babel` (per-round pairing scheduler + per-round resolution + seeded schedule re-derived in wasm). |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-ledger`, public at creation (certification's `source-resolves` 404s on private). |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `/bin/ledger-player` with `PLAYER_PROMPT=<strategy>` (champions) vs `PLAYER_SCRIPTED=mirror` / `PLAYER_SCRIPTED=shark` (fillers). Both baselines specified in `## Decisions`. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` compiles `replay-viewer/ledger_replay.nim` (the same `sim` module) to wasm. No `/client/replay` viewer is ever declared. |
| Real art, starter chrome verbatim | babel's `client/renderer.js` chrome half + `client/chrome.css` reused; babel's sprite/floor/font assets shipped; plaza furniture drawn with canvas primitives (no placeholder boxes). |
| Two name spaces | Anonymous cog aliases in-game (`CogNames`, 8 drawn from the seed); policy names ride in `policyNames` for spectators and in `resultsJson.names` for the platform only. |
| Degrade-never-hang, inside 60 % of 1200 s | `PlayBudgetFraction = 0.6` ⇒ 720 s play deadline; a round is only *started* if 70 s of reserve remain; typical episode is 280 s. Arithmetic in `## Decisions`. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 8** in `variants[standard]`, `variants[quickfire]` and `certification.game_config`; `<SEATS>` in `tools/ci/docker_smoke.sh` is substituted with `8`. |

## The game

**Seats.** Exactly **8** (`num_agents` = 8), fixed: `config_schema` pins `tokens`/`players`
`minItems = maxItems = 8` and `num_agents` `minimum = maximum = 8`. Coordinator ruling: the
idea's 20–100 is infeasible for one parallel LLM batch per turn inside the wall-clock budget;
8 seats = 4 meetings per round keeps stranger-meetings frequent and makes a median-against-the-
pool meaningful. Seats play under anonymous aliases drawn from babel's `CogNames` pool (10 names,
8 drawn, kept verbatim): Sprocket, Gizmo, Ratchet, Widget, Bolt, Piston, Flywheel, Rivet, Tinker,
Gasket. "Identities carry across episodes" is satisfied *within* an episode: an alias is
permanent for the whole episode and its complete meeting record is public to every seat from
round 1. Cross-episode persistence is out of scope (v1).

**Rounds.** `rounds` — default **14**, min 4, max 28, certification fixture **6**. Every seat
plays in every round, so a seat's meeting count equals the rounds played.

**Pairing schedule** (drawn once at `initSim` from the seed, so the wasm viewer re-derives it):

1. Take the standard circle-method 1-factorization of the 8 seats. With positions `0..7` and
   position `7` fixed, matching `M[k]` for `k in 0..6` is:
   `(7, k)` and, for `i in 1..3`, `((k + i) mod 7, (k - i + 7) mod 7)` — four pairs covering all
   eight positions. Across `k = 0..6` every unordered pair of positions occurs **exactly once**.
2. Draw a seeded permutation `pi` of `[0..7]` and relabel: a scheduled position pair `(x, y)`
   becomes the seat pair `(pi[x], pi[y])`. This makes the partner sequence look different every
   episode while keeping the exact-cover property.
3. Rounds are generated in **passes** of 7. Pass `p` uses a seeded shuffle `sigma_p` of `[0..6]`:
   round `r = 7*p + j` uses `M[sigma_p[j]]`. For `p >= 1`, resample `sigma_p` (at most 16
   attempts, then accept) until `sigma_p[0] != sigma_(p-1)[6]`, so no pair meets in two
   consecutive rounds.
4. Generate `ceil(rounds / 7)` passes and keep the first `rounds` rounds.

**Same-partner cap.** The cap the idea asks for is structural, not a filter: with the schedule
above, over `rounds` rounds any two aliases meet **at most `ceil(rounds / 7)`** times — at the
default 14 rounds, **exactly twice each**, a perfect double round robin. `MaxMeetings =
ceil(rounds / 7)` is a derived constant asserted by a test, not an enforcement branch.

**Subgame draw.** Per pairing, per round, from the same seeded stream: `rng.rand(99)` →
`0..49` **DILEMMA** (prisoner's dilemma, p = 0.50), `50..79` **TRUST** (p = 0.30), `80..99`
**ULTIMATUM** (p = 0.20). The dilemma leads because it is the most legible on screen; trust and
ultimatum supply the asymmetric-role texture the idea asks for.

**Roles.** DILEMMA is symmetric (both members have role `either`). TRUST and ULTIMATUM have a
**first mover** (investor / proposer) and a **second mover** (trustee / responder). The first
mover is the pair member with fewer first-mover assignments so far in the schedule being built;
a tie is broken by the seeded RNG. Assignment happens in pair order 0..3 while the schedule is
drawn, so the guarantee is **local, not global**: at every asymmetric meeting the seat that goes
first has no *more* first-mover assignments than its partner at that point, and no seat is ever
first more often than it plays asymmetric subgames. A global "±1 across the episode" balance is
**not** available and is not claimed: how many asymmetric meetings a seat draws is itself random
(the subgame is drawn per pairing), so a seat drawn into few of them ends below another by more
than one. Measured over 10 000 seeds × `rounds` in `{4, 7, 14, 28}`, 58 % of episodes have a
spread above 1 and the worst spread is 5.

**One move per seat per round — the strategy method.** Trust and ultimatum are sequential games.
Ledger resolves them with the standard experimental-economics **strategy method**: the second
mover commits a *contingent* rule before seeing the first mover's move, so all 8 seats decide
simultaneously and the whole round is one parallel LLM batch. Concretely, the trustee commits a
return *percentage* of whatever arrives, and the responder commits a *minimum acceptable offer*.
This is a real mechanism, not a shortcut, and it is stated in the prompt.

**Payoff tables** (all payoffs are whole **coins**; a seat's payoff from a meeting is always in
`[0, 14]`). The three subgames are deliberately calibrated so that **fair play pays 6 in all
three**, exploitation pays 10–12 and being exploited pays 0 — that is what makes a median across
a mixed bag of subgames meaningful.

*DILEMMA* — both choose `cooperate` or `defect` simultaneously:

| | partner cooperates | partner defects |
|---|---|---|
| **you cooperate** | 6 / 6 | 0 / 10 |
| **you defect** | 10 / 0 | 2 / 2 |

*TRUST* — investor endowment 6 coins, trustee endowment 2 coins, multiplier 2.
Investor sends `s` (integer 0..6); the trustee receives `2*s`; the trustee's committed return
percent is `p` (integer 0..100). `returned = (2*s*p + 50) div 100` (round half up), clamped to
`0 .. 2*s`. Payoffs: **investor = `6 - s + returned`**, **trustee = `2 + 2*s - returned`**.
Landmarks: an even split of the pot (`s = 4, p = 50`) → 6 / 6 — the coin invariant below fixes
the pot at `8 + s`, so 6 / 6 is reachable only at `s = 4`; full trust with a fair split
(`s = 6, p = 50`) → 6 / 8; full trust betrayed (`s = 6, p = 0`) → 0 / 14; no trust (`s = 0`)
→ 6 / 2. Coin invariant for tests: `investor + trustee == 8 + s`.

*ULTIMATUM* — pie 12 coins. Proposer offers `o` (integer 0..12) to the responder; the responder's
committed minimum acceptable offer is `m` (integer 0..12). If `o >= m`: **proposer = `12 - o`,
responder = `o`**. Otherwise the deal breaks: **0 / 0**. Landmarks: `o = 6` → 6 / 6; `o = 2,
m = 0` → 10 / 2; `o = 2, m = 5` → 0 / 0. Coin invariant for tests: total is 12 or 0.

**Conduct** (the reputation halo; a display and observation statistic, never a score input).
Each meeting classifies each seat as **kind** or **harsh**:

- DILEMMA: `cooperate` → kind, `defect` → harsh.
- TRUST investor: `s >= 3` → kind, else harsh. Trustee: `p >= 50` → kind, else harsh.
- ULTIMATUM proposer: `o >= 5` → kind, else harsh. Responder: `m <= 5` → kind, else harsh.

`halo = kind / (kind + harsh)` in `0..1`, and exactly `0.5` before a seat's first meeting.

**Gossip.** Every reply may carry `note` (≤ 120 characters, see the reply schema). A note is a
review of **the partner from the seat's previous round's meeting** — the last partner whose
outcome the seat has actually seen. The observation names that alias explicitly as
`NOTE TARGET`; in round 1 there is no target and any `note` is discarded. Accepted notes are
appended to a single **public gossip board** visible to all 8 seats, attributed by alias
(`R6 Gizmo on Bolt: "…"`). The observation shows the last **12** notes, newest last; the viewer
shows the last 5 as cards. Gossip is cheap talk: it never changes a payoff or a score.

**Resolution order** — round `r` executes exactly these steps, in this order:

1. The sim opens round `r`: it reads the four pairs from the precomputed schedule with each
   pair's subgame and first mover, sets `phase = "deal"`, and appends a `round` event.
2. The server builds 8 observations (one per seat) and issues **one parallel batch of 8 LLM
   calls** (`curly.makeRequests`). Scripted seats never enter the batch; their moves are computed
   inline.
3. Replies are parsed. A seat whose reply is missing, unparseable, or non-numeric where a number
   is required goes into a **single retry sub-batch** with a corrective hint; a seat still
   failing after that is decided by the scripted `mirror` baseline and marked `scripted: true`.
   Numeric moves outside their legal range are **clamped** to the range (logged, not retried).
4. The sim applies the four meetings in pair order 0, 1, 2, 3. For each: compute both payoffs
   with the subgame's formula, append each payoff to that seat's payoff list, update each seat's
   `kind` / `harsh` counters and `total`, and append one `meeting` event.
5. Gossip: in seat order 0..7, each seat with a non-empty `note` **and** a defined note target
   appends `{round, author, subject, text}` to the board and emits one `gossip` event.
6. Each seat's `memo` is overwritten when the reply carried one and kept otherwise (babel's notes
   rule); the latest memo per seat rides on the `meeting` event of the seat that wrote it.
7. Every seat's live median is recomputed from its payoff list; ring statistics are recomputed
   from the meeting history. Neither writes an event — both are derived state in
   `tableStateJson`.
8. `roundsPlayed += 1`. If `roundsPlayed >= rounds`, settle `complete` (append `end`) and stop.
9. Otherwise, if any LLM call was issued this round, sleep until
   `roundStart + minRoundIntervalMs` (the API rate-limit floor; a fully scripted round does not
   sleep).
10. Deadline check: if `now + RoundReserveSeconds > playDeadline`, `endEarly()` → settle
    `deadline` (append `end`) and stop. Otherwise go to 1 for round `r + 1`.

**Scoring.** A seat's score is its **median per-meeting payoff in coins**, and it is
**maximized** (higher is better; payoffs are non-negative, so the score is `>= 0`). Precisely:
take the seat's meeting payoffs `p_1..p_k` in round order, sort ascending; if `k` is odd the
score is the middle element; if `k` is even it is the mean of the two middle elements (so an
even `k` can produce a `.5`); if `k == 0` the score is `0.0`. At the default 14 rounds `k = 14`
and the score is `(sorted[6] + sorted[7]) / 2`. `resultsJson.scores` carries this number and
**the league ranks seats by mean episode score.** Nothing else is ranked: mean payoff, total
coins, kind/harsh counts and ring flags are all reported for the record and none of them enters
`scores`. This is the idea's anti-collusion ranking: a ring can pump the mean of an alias it
feeds, but with at most 2 of 14 meetings inside the ring it cannot move that alias's median,
which is set by its meetings with strangers.

**Ring detection** (published as a finding; never a score input). For every unordered pair
`(a, b)` that met at least twice:

- `inMean(a, b)` = mean over their mutual meetings of `(payoff_a + payoff_b) / 2`;
- `outMean(a, b)` = mean of the two members' own payoffs over all of their meetings that were
  *not* with each other; `0.0` when there are none, which the schedule makes unreachable in play
  (a pair that has met twice is at least 7 rounds apart, so each member carries at least 6 other
  meetings) and which only a hand-built history can reach;
- `delta = inMean - outMean` (coins, reported to one decimal).

The pair is **flagged** when it met `>= 2` times, `inMean >= 6.0` and `delta >= 3.0`. A **ring**
is a connected component of size `>= 3` in the flagged graph. `tableStateJson.rings` carries the
flagged pairs (`{a, b, delta}`); `resultsJson.ringPairs` carries their count; the viewer draws
the red threads. Nothing here touches `scores`.

**Observation — exactly what a seat sees.** Visible:

- its own alias, its live median, meeting count, `total` coins, `kind`/`harsh`;
- **this round's four pairings and their subgames** (the plaza is public), including its own
  partner alias, the drawn subgame with its full numeric rules, and its own role;
- the **partner record**: the partner's median, meeting count, kind/harsh, and their last 8
  meetings in full (round, opponent alias, subgame, role, the move they made, both payoffs);
- the **table**: one summary line per alias (median, meetings, kind/harsh) for all 8;
- its **own last 8 meetings** in the same line format;
- the **gossip board**: the last 12 notes with author and subject aliases;
- its own **private memo** verbatim, and the `NOTE TARGET` alias for this round's review.

Hidden: real player/policy names (the alias↔policy map exists spectator-side only); the current
round's moves of every seat including its partner (all decisions are simultaneous); every other
seat's private memo; the future schedule (which subgame or partner comes next round); the
per-seat operator prompts; and the seeded RNG state.

**End conditions.** `results.reason` has exactly two legal values:

- `"complete"` — `roundsPlayed == rounds`.
- `"deadline"` — step 10 fired: the 720 s play deadline was within `RoundReserveSeconds` of the
  next round's start. Scores use the rounds actually played (the median is over `k < rounds`
  meetings). A `deadline` ending is a legitimate, scored episode, and phase 60 accepts it.

There is no resignation, no elimination and no draw state: every seat plays every round.

## Decisions: LLM with scripted fallback

Transport, credential resolution (Bedrock sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`),
the Bedrock model candidate list (haiku first; **drop `us.anthropic.claude-sonnet-4-6`** — it
times out on every sidecar call), `extractJsonObject`, the JSON-only output contract, and the
"no credentials ⇒ every seat scripted, instantly" rule are ported from babel's
`src/babel/llm.nim` unchanged. The **batched** decision path is ported from
`cogame-bullwhip/src/bullwhip/llm.nim` — `requestFor`, `textOf`, `cleanText`, and `decideAll`
(which builds a `RequestBatch`, calls `client.curl.makeRequests(batch, timeoutSeconds)`, and
indexes replies by batch position) — because babel's `decide` is one call at a time and Ledger
has 8 simultaneous deciders. `src/ledger/llm.nim` therefore exposes
`decideAll(client, sim, seats, prompts, scripted): seq[Decision]`, not babel's `decide`.

**One parallel batch per round.** All 8 seats' calls go out in a single `makeRequests` batch per
round; there is no per-seat sequencing anywhere in the loop. The retry sub-batch is a second
`makeRequests` over only the seats that failed.

**System prompt** (identical for every seat, alias substituted):

```
You are <Alias>, one of eight cogs in Ledger. Your alias is permanent and public:
everything you do is on the record and every other cog can read it.

Rules:
- Every round you are paired with one other cog for ONE meeting. Pairings are drawn
  from a fixed rotation: over the episode you meet each of the other seven cogs the
  same number of times, at most twice each in a 14-round game.
- A meeting is one of three games, drawn per pairing: DILEMMA, TRUST, or ULTIMATUM.
  The exact numbers for your meeting are in the message below.
- Everyone decides at the same time, so you never see your partner's move for this
  meeting before you make yours. In TRUST and ULTIMATUM the second mover commits a
  RULE in advance (a return percentage, or a minimum acceptable offer) which is then
  applied to whatever the first mover did.
- Every meeting's moves and payoffs become public immediately, attached to both
  aliases forever.
- You may attach a one-line public review of your PREVIOUS round's partner. Reviews
  are signed with your alias and everyone reads them. They change no payoff.
- YOUR SCORE IS THE MEDIAN OF YOUR PER-MEETING PAYOFFS, not the total and not the
  mean. One huge score against a friend cannot lift a median; being reliably worth
  meeting can. Coins are only ever paid by the game, never transferred between cogs.

OUTPUT FORMAT: reply with ONLY one JSON object, nothing else - no analysis, no
explanation, no markdown fences, no text before or after the object. Your reply must
begin with the character { and end with }.
```

**User prompt**, blocks in this exact order (a block whose data is empty prints `(none)`):

1. `Round 4 of 14. You are Sprocket. Your median so far: 6.0 coins over 3 meetings (kind 2 / harsh 1).`
2. `THIS MEETING: Gizmo — TRUST.` then `YOUR ROLE: TRUSTEE (second mover).` then
   `THE RULES OF THIS MEETING:` with the drawn subgame's numbers spelled out, e.g. for a
   trustee: `Gizmo starts with 6 coins and sends you some number s of them (0-6). Whatever
   is sent DOUBLES on the way: you receive 2s. You start with 2 coins. You commit now to a
   return percentage p (0-100): you will return round(2s * p / 100) coins. Gizmo ends with
   6 - s + returned; you end with 2 + 2s - returned.`
3. `PARTNER RECORD — Gizmo: median 6.0 coins over 3 meetings, kind 3 / harsh 0.` then
   `THEIR LAST 8 MEETINGS:` lines like
   `R3 vs Bolt — TRUST as INVESTOR: sent 5 (Gizmo +7, Bolt +2)`.
4. `THE TABLE:` one line per alias, seat order:
   `Sprocket — median 6.0, 3 meetings, kind 2 / harsh 1`.
5. `THIS ROUND'S TABLES:` `Sprocket & Gizmo — TRUST · Ratchet & Widget — DILEMMA · …`.
6. `YOUR LAST 8 MEETINGS:` same line format, from this seat's side.
7. `THE GOSSIP BOARD (last 12 notes):` `R3 Bolt on Rivet: "took the whole pot, avoid"`.
8. `YOUR PRIVATE MEMO:` the seat's stored memo verbatim.
9. `NOTE TARGET: Widget (your partner last round) — your "note" is a public review of Widget.`
   or `NOTE TARGET: (none this round — any "note" you send is discarded).`
10. `GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in
    the requested format):` + the seat's `PLAYER_PROMPT` (block omitted when empty) — babel's
    `operatorBlock` verbatim.
11. The reply line, which names the one legal form of `move` for this seat's role:
    - DILEMMA: `Reply with ONLY {"move": "cooperate", "note": "…", "memo": "…"} — "move" is
      "cooperate" or "defect"; note at most 120 characters; memo at most 400 characters.`
    - TRUST investor: `… "move" is a whole number 0 to 6, the coins you send.`
    - TRUST trustee: `… "move" is a whole number 0 to 100, the percentage of what arrives that
      you return.`
    - ULTIMATUM proposer: `… "move" is a whole number 0 to 12, the coins you offer out of 12.`
    - ULTIMATUM responder: `… "move" is a whole number 0 to 12, the smallest offer you will
      accept.`

**Reply schema.** One JSON object, always the same three keys — one `move` field for all five
role cases, because a single always-present field is the cheapest thing for a small model to get
right (escrow, 2026-08-23: precompute the legal choice set in the observation and keep the
structured field singular):

| field | type | required | cap / range | on violation |
|---|---|---|---|---|
| `move` | string or number | yes | DILEMMA: `cooperate` / `defect`; TRUST investor 0..6; TRUST trustee 0..100; ULTIMATUM proposer 0..12; ULTIMATUM responder 0..12 | non-numeric where a number is required, or an unrecognised word → retry once → `mirror` fallback. Numeric but out of range → clamped into range, logged |
| `note` | string | no | **≤ 120 characters** | over-length is truncated |
| `memo` | string | no | **≤ 400 characters** | over-length is truncated |

Parse tolerances: `move` accepts `"cooperate"`, `"COOPERATE"`, `"c"`, `"defect"`, `"d"`
(case-insensitive, leading/trailing space stripped) and, for the dilemma only, integer `0`
(cooperate) / `1` (defect); numeric moves accept `JInt`, `JFloat` (rounded half up), and numeric
strings including a trailing `%` or `" coins"`.

**Truncation is on rune boundaries.** `note` and `memo` are cut by `cleanText(text, limit)`
(bullwhip's, ported verbatim): `strip()`, then if `runeLen > limit`,
`runeSubStr(0, limit - 1) & "…"`. `note` additionally maps `\n` and `\r` to spaces and drops
other control characters. The same rune-safe cut applies to `PLAYER_PROMPT` at
`MaxPromptLen = 4000` in the server (babel slices bytes there — that is a latent strict-UTF-8
bug and the fork fixes it) and to every error string quoted into a log or an event. Every string
that can reach the replay is rune-cut; that is what keeps the replay bytes strict-UTF-8
parseable.

**Degrade, never hang.**

- Per call: `llmTimeoutSeconds` (default **30**) bounds every HTTP request; `curly.makeRequests`
  applies it to the whole batch.
- Per seat: attempt 1 → on transport error, non-2xx, refusal, `max_tokens` cut-off, missing JSON
  object, or an unparseable `move`, the seat joins the retry sub-batch with the corrective hint
  `Your previous reply was invalid. Respond with ONLY the requested JSON object, with "move"
  <role-specific legal form>.` Attempt 2 failing → the **`mirror` scripted move** for that seat,
  recorded with `scripted: true` on the meeting event and logged as
  `ledger: seat N falling back to scripted decision`.
- 401/403 disables the client for the rest of the episode (every later round is scripted and
  instant); 429 rotates the Bedrock model and doubles the round-interval floor (below).
- No credentials at all ⇒ `client.disabled` at construction, every seat scripted, no network
  waits: offline certification and CI complete in seconds.
- The sim never blocks on a player socket: prompts are delivered before play and a seat with no
  prompt simply has an empty operator block.
- **Settling early:** the pre-round deadline check (resolution step 10) ends the episode between
  rounds with `reason = "deadline"`, then `finishEpisode` writes results and the replay exactly
  as babel does (final frames to players first, then artifacts, then a bounded shutdown grace
  before `quit(0)`).

**Scripted baselines** (both fieldable policies and the internal fallback).

`mirror` — reciprocal with forgiveness; the default fallback for a failed LLM reply and for a
seat that registers scripted without naming a baseline:

- DILEMMA: cooperate if the partner has no public DILEMMA move yet. Otherwise play the
  partner's most recent public DILEMMA move (their last move against *this* seat if they have
  one, else their last against anyone) — i.e. tit-for-tat over public history — **except**
  forgive: if the partner has defected exactly once in their whole public record and the seeded
  RNG draws `< 0.20`, cooperate anyway.
- TRUST investor: send **4** when the partner's `halo >= 0.5` or the partner has no record, else
  send **1**. TRUST trustee: return **50** when the partner's `halo >= 0.5` or has no record,
  else **25**.
- ULTIMATUM proposer: offer **5**. Responder: minimum acceptable offer **4**.
- Never writes `note` or `memo`.

`shark` — the greedy foil that reputation is supposed to punish:

- DILEMMA: always `defect`.
- TRUST: investor sends **0**; trustee returns **0**.
- ULTIMATUM: proposer offers **1**; responder's minimum acceptable offer is **1** (it accepts
  nearly everything).
- Never writes `note` or `memo`.

Both are pure functions of the sim's public state plus the seeded RNG, so a scripted episode is
deterministic for a given seed. `scriptedAction(sim, seat, kind)` is the single entry point and
is always legal for every (subgame, role) combination — the test suite asserts exactly that.

**Env switching (same image).** `/bin/ledger-player` reads `PLAYER_PROMPT` (LLM policy) or
`PLAYER_SCRIPTED` (`mirror` | `shark`; any other non-empty value means `mirror`) and sends
`{"type":"prompt","prompt":"…","scripted":"mirror"|"shark"|""}` on connect. `PLAYER_SCRIPTED`
wins if both are set. Champions are `PLAYER_PROMPT` policies; fillers are `PLAYER_SCRIPTED`.

**Episode budget arithmetic** (this is the whole wall-clock argument, out loud):

- `PlayBudgetFraction = 0.6`; `COWORLD_TIMEOUT_SECONDS` is not given to the game container, so
  the game assumes `episodeTimeoutSeconds = 1200` ⇒ **`playDeadline` = gameStart + 720 s**.
- LLM calls per round: **8** (one batch). Retries add at most 8 more.
- Rate-limit floor: the hosted Bedrock sidecar caps **30 requests/minute per episode**. At 8
  calls per round plus ~10 % retries (~8.8 calls), a round interval of **20 s**
  (`minRoundIntervalMs`, default 20000, cert 0) holds the steady state at ≈ 26 req/min. On any
  429 the floor doubles to 40 s for the remainder of the episode.
- Typical round: batch latency 6–10 s (haiku 4.5, `maxOutputTokens` 900), paced to the 20 s
  floor. **14 rounds × 20 s = 280 s**, which is 39 % of the 720 s play budget and 23 % of the
  1200 s episode timeout.
- Worst realistic round: 30 s (first attempt hits `llmTimeoutSeconds`) + 2 s retry pause + 30 s
  (retry hits it too) ≈ **62 s**. `RoundReserveSeconds = 70` (2 s when the LLM client is
  disabled, since scripted rounds are instant): a round is only started when
  `now + 70 s < playDeadline`, so play always stops by 720 s and the remaining 480 s covers
  artifact writes with enormous margin. 14 pathological rounds (14 × 62 = 868 s) would trip the
  reserve at round ~11 and end with `reason = "deadline"` — scored, written, not discarded.
- Certification / CI: no credentials ⇒ all-scripted, `minRoundIntervalMs = 0`, 6 rounds ⇒ the
  episode finishes in about 2 s.

## Sim module

`src/ledger/types.nim` — `LedgerError`, `PlayerConfig`, `GameConfig`
(babel's fields with `rounds` kept and `turnDelayMs` replaced by `minRoundIntervalMs`),
`SubGame`, `EventKind`, `GameEvent`, `defaultGameConfig`, `update`.

```nim
type
  SubGame* = enum
    sgDilemma = "pd"
    sgTrust = "trust"
    sgUltimatum = "ultimatum"

  EventKind* = enum
    evStart = "start"
    evRound = "round"
    evMeeting = "meeting"
    evGossip = "gossip"
    evEnd = "end"
```

`GameConfig` fields: `tokens`, `players`, `seed`, `rounds` (default 14),
`episodeTimeoutSeconds` (1200), `sampled`, `minRoundIntervalMs` (20000),
`playerConnectTimeoutSeconds` (180), `model` (`claude-sonnet-5`), `maxOutputTokens` (900),
`llmTimeoutSeconds` (30).

`src/ledger/sim.nim` — pure rules, no IO, no networking; the server, the tests and the wasm
viewer all drive this one module.

- Constants: `Seats* = 8`, `Meetings* = 4` (pairs per round), `RoundsPerPass* = 7`,
  `MinRounds* = 4`, `MaxRounds* = 28`, `EpisodeCallBudget* = 240` (`CallsPerRound* = 8` ⇒
  `sampleEpisode` caps `rounds` at `min(rounds, 30, MaxRounds)`), `InvestorEndowment* = 6`,
  `TrusteeEndowment* = 2`, `TrustMultiplier* = 2`, `Pie* = 12`, `PdReward* = 6`,
  `PdTemptation* = 10`, `PdPunishment* = 2`, `PdSucker* = 0`, `GossipWindow* = 12`,
  `HistoryWindow* = 8`, `MaxNoteLen* = 120`, `MaxMemoLen* = 400`, `RingMinMeetings* = 2`,
  `RingInThreshold* = 6.0`, `RingDeltaThreshold* = 3.0`, `CogNames*` (babel's list, verbatim).
- `MeetingPlan* = object`: `a*, b*: int` (seat ids, `a` is the first mover for asymmetric
  subgames and the lower seat id for the dilemma), `game*: SubGame`.
- `RoundPlan* = object`: `pairs*: array[Meetings, MeetingPlan]`.
- `Sim* = object`: `config`, `names: seq[string]`, `schedule: seq[RoundPlan]`,
  `round: int` (-1 before the first), `phase: Phase` (`phDeal`, `phResolve`, `phBetween`,
  `phDone`), `moves: array[Meetings, array[2, int]]` (live round; `int.low` = unmade),
  `scriptedFlags: array[Meetings, array[2, bool]]`, `payoffs: array[Seats, seq[int]]`,
  `kind: array[Seats, int]`, `harsh: array[Seats, int]`, `total: array[Seats, int]`,
  `memos: seq[string]`, `board: seq[Gossip]` (`{round, author, subject, text}`),
  `roundsPlayed: int`, `done: bool`, `reason: string`, `events: seq[GameEvent]`.
- Setup: `tableNames(players, seed)` (babel's, verbatim — aliases from the seed),
  `sampleEpisode(config)` (idempotent; clamps `rounds` into `MinRounds..MaxRounds` and into the
  call budget), `initSim(config)` (raises `LedgerError` unless `players.len == Seats`; draws
  `pi`, the pass orders, the subgames and the first-mover assignment; appends the `start` event).
- Rules: `beginRound(sim)`; `applyRound(sim, moves: array[Meetings, array[2, int]], notes,
  memos: seq[string], scripted: array[Meetings, array[2, bool]])` — the single transactional
  apply that performs resolution steps 4–8 and appends the `meeting` and `gossip` events;
  `endEarly(sim)` (settles `deadline`).
- Payoff kernels (pure, individually testable):
  `pdPayoffs(moveA, moveB): (int, int)`, `trustPayoffs(sent, percent): (int, int)`,
  `ultimatumPayoffs(offer, floorValue): (int, int)`, and
  `meetingPayoffs(game, moveA, moveB): (int, int)` dispatching over `SubGame`.
- Queries: `median(sim, seat): float`, `meanPay(sim, seat): float`, `halo(sim, seat): float`,
  `metCount(sim, a, b): int`, `partnerOf(sim, seat): int`, `roleName(game, first): string`,
  `subGameName(game): string` (`"DILEMMA"`, `"TRUST"`, `"ULTIMATUM"` — words, never notation),
  `moveText(game, first, move): string` (e.g. `sent 5`, `returned 25%`, `offered 3`,
  `floor 5`, `cooperate`), `ringThreads(sim): seq[(int, int, float)]`,
  `legalMoveRange(game, first): (int, int)`, `clampMove(game, first, move): int`.
- Illegal operations raise `LedgerError`: applying a round when `done`, applying out of phase,
  a move that is not an integer in range *after* clamping (i.e. a programming error),
  a gossip note whose subject is not last round's partner, `rounds` below `MinRounds`, a player
  count other than 8.

**Event vocabulary** (flat `GameEvent`, JSON through `eventToJson` / `eventFromJson`, unset
fields omitted — babel's pattern):

| kind | fields |
|---|---|
| `start` | — (everything seeded is re-derivable; the replay `config` also carries the seed) |
| `round` | `round`; `pairs: [{a, b, game, first}]` × 4 (`first` = seat id of the first mover, `= a`) |
| `meeting` | `round`, `pair` (0..3), `seat` (= `a`), `other` (= `b`), `game` (`"pd"`/`"trust"`/`"ultimatum"`), `moveA`, `moveB` (raw ints as defined per subgame), `payA`, `payB`, `scriptedA`, `scriptedB`, `memoA`, `memoB` (each seat's memo after this round's reply, possibly empty) |
| `gossip` | `round`, `seat` (author), `other` (subject), `text` (the ≤ 120-rune note) |
| `end` | `round` = rounds played, `text` = `"complete"` \| `"deadline"` |

**`tableStateJson`** — one frame; **this is exactly what the viewer draws**:

```json
{"seats":[{"name":"Sprocket","score":6.0,"mean":6.3,"total":19,"meetings":3,
           "kind":2,"harsh":1,"halo":0.67,"partner":4,"game":"trust",
           "role":"trustee","move":null,"lastPay":6,"memo":"…","scripted":false}, ×8],
 "round":3,"rounds":14,"roundsPlayed":3,
 "pairs":[{"a":0,"b":4,"game":"trust","first":0,
           "moveA":null,"moveB":null,"payA":null,"payB":null,"resolved":false}, ×4],
 "gossip":[{"round":2,"author":5,"subject":1,"text":"took the whole pot, avoid"}],
 "rings":[{"a":1,"b":5,"delta":3.5}],
 "phase":"deal|resolve|between|done",
 "gameDone":false,"reason":""}
```

`pairs` describes the round in progress (or the last completed round once `done`); `moveA` /
`moveB` / `payA` / `payB` are `null` until the round resolves. `gossip` carries the last
`GossipWindow` notes. `role` is `"either"` for a dilemma. `score` is the median defined above.

**`resultsJson`** (platform-facing; `names` are POLICY names, not aliases):

```json
{"names":[8],"scores":[8 floats],"mean":[8 floats],"total":[8 ints],"meetings":[8 ints],
 "kind":[8 ints],"harsh":[8 ints],"rounds":<played>,"maxRounds":<cap>,
 "ringPairs":<int>,"reason":"complete|deadline"}
```

**Replay payload** (`ledger.replay.v1`) — self-sufficient, nothing else is fetched:

```json
{"protocol":"ledger.replay.v1",
 "names":[8 aliases],"policyNames":[8 policy names],
 "config":{"rounds":14,"seed":12345,"sampled":true,"schedule":[…]},
 "events":[…],"results":{…}}
```

`config.schedule` is the fully expanded pairing/subgame/first-mover schedule. It is derivable
from the seed, and it is written anyway so the viewer never has to trust a re-derivation to draw
the plaza; `replayMatch` cross-checks it against the seeded derivation and raises if they
disagree (babel's `round`-event check, generalised). Replay mode and the wasm viewer add
`"states"`: one `tableStateJson` per event prefix.

`replayMatch(config, events): seq[Sim]` re-derives the whole timeline by replaying `meeting` and
`gossip` events through the same rules (`frames[i]` = state after `events[0 ..< i]`), settling on
`end`. `frames.len == events.len + 1`.

## Server, player, protocol

`src/ledger/server.nim` — babel's `src/babel/server.nim` with the game loop replaced by the
round loop of resolution steps 1–10 (snapshot the sim under the lock, run `decideAll` outside the
lock, apply under the lock, broadcast). Everything else is babel's, verbatim: `clientDir` /
`dataDir` resolution, `writeArtifact`, `finishEpisode` (final frames to players → results →
replay → bounded shutdown grace → `quit(0)`), the mummy router, the Ping→Pong handler (the
certifier pings `/global` and mummy hands pings to the application), and the
`playerConnectTimeoutSeconds` wait.

Endpoints (identical set): `GET /healthz`, `GET /client/global`, `GET /client/player`,
`GET /client/replay`, `GET /client/renderer.js`, `GET /client/chrome.css`,
`GET /client/assets/<name>`, `WS /player?slot=N&token=T`, `WS /global`, `WS /replay`. Both
`/client/` routes serve real pages and neither opens a player socket (lantern 0.1.1): the
certifier probes them before player pods exist.

**Player protocol `ledger.player.v1`** (JSON text frames):

- game → player: `{"type":"welcome","protocol":"ledger.player.v1","slot":N,"name":"<alias>","rounds":14}`;
  `{"type":"state","slot":N,"name":"<alias>","seat":{"score":6.0,"mean":6.3,"total":19,"meetings":3,"kind":2,"harsh":1},"round":3,"rounds":14,"roundsPlayed":3,"started":true,"done":false,"reason":""}`
  after every round; `{"type":"final","done":true,"scores":[…],"mean":[…],"meetings":[…],"names":[8 aliases],"rounds":N,"reason":"complete"}`.
- player → game: `{"type":"prompt","prompt":"…","scripted":"mirror"|"shark"|""}` (prompt ≤ 4000
  characters, rune-safe truncation server-side; the latest frame applies to all later rounds).

The player socket is **redacted** exactly as babel's is: a seat sees only its own tallies and the
round counter, never pairings, moves or other seats' state. Decisions are server-side, so nothing
is lost — the seat's real view is the observation the server composes for its LLM call.

**Global socket** carries the full `tableStateJson` plus `type`, `game: "ledger"`, `policyNames`,
`events`, `started`, `done`, `connected` — babel's `snapshotJson`, field for field.

`src/ledger_player.nim` — babel's `src/babel_player.nim` with the default prompt replaced by a
sound Ledger strategy and `PLAYER_SCRIPTED` read as a **name** rather than a flag. It also fixes
the latent bullwhip/raid crash: the receive loop is wrapped in `try / except CatchableError` and
exits **0** on a dead or closed socket (whisky raises on a close frame; mummy's `send` only
queues, so the game's `quit(0)` can outrun the final frame and a raising player container fails
certification with `player_error`).

`src/ledger.nim` — babel's entry point with the renames (`runGameServer` / `runReplayServer`,
`ledger` slug in log lines).

## Viewer

**All four viewer files come from ONE starter — `cogame-babel`** — and nothing is spliced from
another lineage: `replay-viewer/config.nims` (babel's, with the output renamed to
`ledger_replay.js`, `EXPORT_NAME=LedgerReplayModule`, and the exported-function list renamed to
`_led_load_replay,_led_payload_ptr,_led_payload_len,_led_error_ptr,_led_error_len`), the wasm
entry `replay-viewer/ledger_replay.nim` (babel's `babel_replay.nim` with those renames and the
`emscripten_exit_with_live_runtime` epilogue kept), `replay-viewer/static_replay.js` (babel's,
with `BabelReplayModule` → `LedgerReplayModule`, `_bab_*` → `_led_*`, `BabelRenderer` →
`LedgerRenderer`), and `replay-viewer/index.html` (babel's, with the wordmark and script names
changed). babel's `MODULARIZE=1` + `EXPORT_NAME` link flags and its factory-call bootstrap are
kept **together**; mixing one starter's shell with another's link flags silently deadlocks the
viewer (cogame-lantern, 2026-08-23).

**Readiness contract.** `client/renderer.js` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` at the end of
`attachReplay`, on the first drawn frame — babel's line, kept. `replay-viewer/static_replay.js`
sets `data-replay-error` (and posts `{src:"coworld-replay",type:"error"}` to the parent) on any
failure, and removes it on a successful load. `tools/ci/viewer_smoke.mjs` gates on exactly these.

**Chrome provenance.** The parley/babel lineage's two chrome artifacts are
`client/renderer.js` (the chrome module — the checklist's `chrome_common.js`) and
`client/replay.html` (the broadcast page — the checklist's `replay_broadcast.html`); Ledger keeps
babel's names because the whole stack, including `tools/build_replay_viewer.sh` and the server's
`/client/renderer.js` route, refers to them.

- `client/renderer.js` is **copied byte-for-byte from cogame-babel** and then edited only in the
  scene and in the event vocabulary. Function by function, against
  `/workspace/starters/cogame-babel/client/renderer.js`:
  - **Untouched babel code, byte-identical (22):** `makeRenderer`, `loadImages`, `assetUrl`,
    `ellipsize`, `hexToRgb`, `shade`, `rgba`, `roundRect`, `wrapLines`, `drawParchment`,
    `drawTag`, `seatBlock`, `noteHeight`, `seatColor`, `makeNameMap`, `applyNames`, `clampName`,
    `isBaselineFiller`, `roundBase`, `blockHead`, `escapeHtml`, `reasonLine`.
  - **Removed with babel's card-and-booth scene (9):** `sceneOf`, `sceneText`, `boothPairs`,
    `pendingSeat`, `drawSeat`, `drawCard`, `drawShape`, `drawRibbon`, `spellTokens`.
  - **New, all of them the plaza scene, the two DOM overlays or the transport measurement (26):**
    `gameName`, `roleName`, `moveText`, `isKind`, `seatBlockAbove`, `seatBlockBelow`, `seatAngle`,
    `seatHome`, `tableSpot`, `plazaPairs`, `eased`, `drawPlaza`, `drawTable`, `drawVerdict`,
    `drawHandshake`, `drawKnife`, `drawSnappedCoin`, `drawCoins`, `drawThreads`, `drawAvatar`,
    `drawHalo`, `ringGroups`, `syncRail`, `meetingText`, `medianOf`, `relayout`.
  - **Changed babel functions (15)**, each edit confined to Ledger's five event kinds, the two
    new state fields (`gossip`, `rings`) or the plaza geometry — no starter behaviour is dropped:
    `computeLayout` and `draw` (the plaza instead of the booths); `describeEvent`, `endText` and
    `phaseText`, `matchHeader`, `updateScorebug` (the event vocabulary and the median readouts);
    `buildScrub` (Ledger's beat-marker classes, and a `nameMap` argument for the labels);
    `renderFeed` (the new event kinds, the per-seat payoff ctx, the `RING` lines and the memo
    say-lines, plus the `rings` argument of "Readouts" above); `updateEndscreen` (the median /
    mean / meetings / kind / harsh columns and the ring rows, plus the same `rings` argument);
    `makeEffects` (`speakAt`/`pickAt` → `roundAt`/`meetAt`/`gossipAt`); `stateToView` (`glyphs` →
    `gossip`/`rings`/`round`/`nameOf`); `attachLive` and `attachReplay` (they pass the frame's
    `rings` into the feed and the endcard, and `attachReplay` passes `nameMap` into `buildScrub`);
    `bindFeedToggle` (the two `relayout()` calls of "Transport rules" below).
- `client/chrome.css` is copied byte-for-byte and only **appended** to (the new beat-marker
  classes, the plaza-specific plate rules, the `--band` rules below). No existing rule is
  rewritten.
- `client/replay.html` (and `client/global.html`, `client/player.html`) is **babel's page with a
  Ledger game block appended** — the same `#layout` / `#stage` / `#topband` / `#wordmark` /
  `#clock` / `#topright` / `#statuschip` / `#feedtoggle` / `#scorebug` / `#board-wrap` /
  `#table` / `#lightpool` / `#grain` / `#endscreen` / `#transport` / `#scrub` / `#play` / `#pos`
  / `#feed` / `#loading` elements in the same nesting, never a from-scratch page that reuses the
  ids (cogame-gridlock, 2026-08-23). The appended block is a `<div id="gossip-rail">` inside
  `#board-wrap` for the gossip cards and a `<div id="ringnote">` for the ring caption.
- **Removed from the starter's pages:** nothing structural, and nothing at all from
  `chrome.css` — it is strictly append-only (one hunk after babel's last line, zero deletions,
  zero modifications), so babel's `@font-face` for `rajdhani` at `chrome.css:9` stays, because
  `data/font.ttf` still ships and `renderer.js`'s `GLYPH_FONT` still names it. The only starter
  element deleted anywhere is the wordmark's inner text in the pages
  (`BA<span>BEL</span>` → `LED<span>GER</span>`).
- **Zoom:** the plaza is a **fixed arena** that always fits the frame, so `#viewpanel` (zoom bar
  + minimap) is **dropped entirely** — babel has none to begin with and none is added.

**Transport rules.** `relayout()` is added to the chrome section of `client/renderer.js` and
called on `load`, on `resize`, and from `bindFeedToggle`: it measures `#transport` and sets
`--band` (its height in px) and `--hudscale` (`clamp(0.75, width / 960, 1.25)`) on
`document.documentElement` (`:root`). `#endscreen` gets `bottom: var(--band)` so the endcard
**stops at the transport band** and never covers the scrubber; all HUD layers (`#lightpool`,
`#grain`, `#endscreen`, `#gossip-rail`) live inside `#board-wrap`, which is a grid row above
`#transport`, so **no overlay ever sits in the transport band**. Every seek dismisses the
endcard: `buildScrub`'s `onSeek` calls `setIndex(next, true)`, which calls
`updateEndscreen(..., show = index >= events.length && events.length > 0, ...)` — false for any
seek that is not to the very end.

**Scrubber beats are clickable, labelled buttons.** In `buildScrub`, each beat marker is a
`<button type="button" class="beat-marker …" aria-label="…" title="…">` whose click seeks to that
event index (in addition to babel's click/drag-to-seek on the track). Emitted classes, all with
CSS in `chrome.css`:

| class | emitted for | label example | look |
|---|---|---|---|
| `beat-meet kind seatN` | a meeting where both seats acted kind | `Round 4 — Sprocket and Gizmo settle kindly` | filled, seat colour |
| `beat-meet harsh seatN` | a meeting with exactly one harsh seat | `Round 4 — Gizmo takes from Sprocket` | filled, red |
| `beat-meet mutual` | both harsh | `Round 4 — Sprocket and Gizmo both take` | hollow red |
| `beat-meet broken` | a rejected ultimatum (0 / 0) | `Round 4 — deal broken` | grey X tick |
| `beat-gossip` | a gossip event | `Round 4 — Gizmo reviews Bolt` | thin amber tick |
| `beat-end death` | the `end` event | `Final` | taller, tall neutral bar |

Round spans (`.round-span`, `.round-span.alt`, `.round-sep`) are babel's, unchanged.

**The plaza scene** (real art, canvas primitives, no placeholders):

- A ring of **8 avatar posts** around the octagonal plaza, drawn on babel's `arena_floor.png`
  with babel's four `soldier_*_front.png` sprites (each used twice, disambiguated by an
  8-entry `COLORS` seat palette, the alias plate and the halo).
- **Halo:** a ring around each avatar whose radius and alpha come from `seats[i].halo` — gold
  above 0.7, pale above 0.4, cold grey below. This is the reputation the idea asks to be
  visible at a glance.
- **Four tables** in the inner ring. When a round opens (`phase = "deal"`) the paired avatars
  slide to their table and the table shows the subgame in **words** (`DILEMMA`, `TRUST`,
  `ULTIMATUM`) plus a role tag (`INVESTOR` / `TRUSTEE`, `PROPOSER` / `RESPONDER`).
- **Resolution icons** (`phase = "resolve"`, held ~1200 ms then faded, timed like babel's
  last-move arrow): both kind → a drawn **handshake**; one harsh → a **knife** pointing at the
  victim; both harsh → **crossed knives**; a rejected ultimatum → a **snapped coin**. Coins fly
  from the table to each avatar with a `+N` in the seat colour.
- **Gossip rail:** the last 5 notes flutter in as small parchment cards on the right
  (`drawParchment`, babel's), each two lines, ellipsized, captioned `Gizmo on Bolt`.
- **Red threads:** for each entry in `rings`, a red line drawn *under* the avatars between the
  two seats, thickness `1 + delta / 2` px, with a `RING` tag at the midpoint. The `#ringnote`
  caption `RING: Bolt · Rivet · Piston` names each connected component of size `>= 3` — a
  **ring** as defined above, the same size filter the sim's `ringComponents` applies. A lone
  flagged pair is a thread, not a ring: it gets its line and its feed entry, and no caption.
  The caption is absent when there is no such component.
- **Memo parchment:** under each avatar, a three-line ellipsized card with the seat's latest
  `memo` — the reasoning in public, babel's notes idea kept.
- Idle before round 1: avatars in place, halos at the neutral 0.5 ring, tables dark.

**Readouts.**

- Wordmark `LED<span>GER</span>`. Clock: `ROUND 4 / 14 · TABLES MEET` / `· SETTLING` /
  `FINAL — 14 ROUNDS`.
- **Scorebug:** 8 plates (two rows of four under 640 px), each: alias, **median coins** as the
  big number (one decimal), the label `median`, a pip strip (filled = `kind`, hollow = `harsh`),
  and a small subgame tag for this round's meeting.
- **Feed** (`renderFeed`, babel's, new `describeEvent` cases): `ROUND 4` heads;
  `Sprocket ⇄ Gizmo — DILEMMA: both cooperate (+6 / +6)`;
  `Widget → Bolt — TRUST: sent 6, returned 25% (+3 / +11)`;
  `Rivet → Tinker — ULTIMATUM: offered 3, floor 5 — BROKEN (0 / 0)`;
  `Gizmo on Bolt: "took the whole pot, avoid"` (say-styled);
  `RING: Bolt · Rivet (+3.5 coins between them)`; `Final — Sprocket, median 7.0 coins`.
  Kind outcomes carry `feed-score seatN`.
- **Endcard:** columns `median`, `mean`, `meetings`, `kind`, `harsh`; verdict = the top seat's
  alias + `TOPS THE LEDGER` (or `ALL LEVEL`); title `FINAL — n ROUNDS`; a reason line when
  `reason == "deadline"`; and the ring findings, one line per flagged pair. `results` carries
  only `ringPairs` (a count), so the feed's and the endcard's `RING` lines take their pair list
  from the flagged pairs of **the frame being shown** — `renderFeed` and `updateEndscreen` are
  passed `currentState().rings`, the same state the canvas is drawn from, never a value left
  behind by whatever frame was drawn last.
- **360 px legibility is a hard requirement** (the softmax.com featured-match iframe is ~360 px):
  `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`, plate labels hidden under `640px`, the
  plaza's alias plates drawn at `--hudscale`-scaled sizes with a minimum 11 px font, and the
  gossip rail collapsed below 480 px so the tables stay readable. Numbers are rendered as words
  and digits (`DILEMMA`, `+6`), never as internal notation.

**Bundle and hook.** The manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}`
— a static wasm bundle, **never a pod**, and `/client/replay` is never declared as the platform
viewer. `tools/build_replay_viewer.sh` is babel's hook with the renames, plus the ecos fix:
`mkdir -p` the output's parent **before** the containment check (babel's hook resolves the path
by `cd`-ing into a parent that does not exist on a fresh CI checkout). It compiles
`replay-viewer/ledger_replay.nim` with the pinned emsdk container (`Dockerfile.replay-viewer`)
when `emcc` is absent, then copies `ledger_replay.js`, `ledger_replay.wasm`,
`replay-viewer/index.html`, `replay-viewer/static_replay.js`, `client/renderer.js`,
`client/chrome.css` and the `data/` assets (four soldier sprites, `arena_floor.png`, `font.ttf`)
into the bundle directory, and asserts `index.html` exists and `static_replay.js` mentions
`data-replay`.

**Replay bytes are self-sufficient:** aliases (`names`), policy names (`policyNames`), the whole
config including `seed`, `rounds` and the expanded `schedule`, every event, and `results` all
live in the replay file. The viewer contacts nothing but S3 for those bytes; per-tick state is
re-derived in the browser by the same Nim `sim` module the server ran.

## Packaging

- `ledger.nimble` — babel's, renamed; binaries `ledger` and `ledger_player`.
- `compose.yaml` — service **`ledger`** (so the manifest placeholder is `{{LEDGER_IMAGE}}`;
  placeholders are derived from compose service names, lantern 0.1.0), `platform: linux/amd64`,
  `build: {context: ., network: host}`, image `coworld-ledger`.
- `Dockerfile` — babel's multi-stage build; binaries at `/bin/ledger` and `/bin/ledger-player`;
  `client/` and `data/` copied next to them. `Dockerfile.replay-viewer` — babel's, renamed.
- `tools/build_replay_viewer.sh` (mode **100755**) and `tools/ci/docker_smoke.sh` (mode
  **100755**, scaffolded from `coworld-builder/templates/tools/ci/docker_smoke.sh` with
  `<slug>` = `ledger`, `<IMAGE>` = `coworld-ledger`, `<SEATS>` = **8**),
  `tools/ci/viewer_smoke.mjs` (copied verbatim, no substitutions),
  `tools/ci/policies.json`.
- `.github/workflows/ci.yml` and `.github/workflows/coworld-release.yml` from
  `coworld-builder/templates/` with `SLUG: ledger`, `IMAGE: coworld-ledger`.

**`coworld_manifest_template.json`:**

- `$schema` set, tags (≥ 3): `["social-dilemma","reputation","llm-driven","turn-based",
  "eight-player","mixed-motive","game-theory"]`.
- `episode_timeout_minutes: 20` at the top level; `game.runnable.type: "game"`,
  `image: "{{LEDGER_IMAGE}}"`, `run: ["/bin/ledger"]`,
  `env: {"ANTHROPIC_API_KEY_URI": "secret://coworld/ledger/anthropic_api_key"}` (without this the
  hosted container never receives the secret and every league episode plays scripted — hive,
  2026-08-23), `source_url: "https://github.com/Metta-AI/cogame-ledger/tree/main"`,
  `owner: "daveey@gmail.com"`.
- `game.config_schema` — a real JSON Schema, `additionalProperties: false`:
  `tokens` (array, minItems = maxItems = **8**), `players` (array of `{name}`, minItems =
  maxItems = **8**), `num_agents` (integer, minimum = maximum = **8**), `seed` (integer),
  `rounds` (integer 4..28, default 14), `episodeTimeoutSeconds` (integer 60..6000, default 1200),
  `minRoundIntervalMs` (integer 0..120000, default 20000), `model` (string, default
  `claude-sonnet-5`), `maxOutputTokens` (integer 64..2000, default 900), `llmTimeoutSeconds`
  (integer 5..300, default 30), `player_connect_timeout_seconds` (number, default 180).
- `game.results_schema` — matches `resultsJson` exactly: `names`, `scores`, `mean`, `total`,
  `meetings`, `kind`, `harsh` (each an 8-element array), `rounds`, `maxRounds`, `ringPairs`,
  `reason` (`"complete"` | `"deadline"`). `scores` items are numbers with `minimum: 0`.
- `game.protocols` — **both** keys. `player`: the full `ledger.player.v1` text above, including
  that a policy is just a prompt, the `PLAYER_PROMPT` / `PLAYER_SCRIPTED` env switch, the 4000-
  character prompt cap and the redaction rationale. `global`: the `/global` snapshot shape
  (`tableStateJson` + `policyNames` + `events` + `connected`), the meaning of `score` (median
  coins), the event vocabulary, and where the static viewer lives
  (`index.html?replay=<url>`).
- `game.docs` — `readme` (`{"type":"text","value":"…"}`, one paragraph: eight aliases, 14 rounds
  of drawn dilemmas, public record, gossip, median ranking, how to field a policy) and `pages`:
  `rules.md` (the full rules: schedule, cap, three payoff tables with their numbers, conduct
  thresholds, gossip, the median score and why it is the median, `reason` values) and
  `strategy.md` (what a good prompt does: read the partner record before trusting, punish sharks
  by refusing to invest, keep a memo, remember that the median rewards being reliably worth
  meeting; and that ring behaviour is measured and published but never scored).
- `player[]` — three bundled runnables, each with `id`, `type: "player"`, `name`, `description`,
  `image: "{{LEDGER_IMAGE}}"`, `run: ["/bin/ledger-player"]`, resources and `source_url`:
  `ledger-player` (prompt policy; no env), `ledger-mirror` (`PLAYER_SCRIPTED=mirror`),
  `ledger-shark` (`PLAYER_SCRIPTED=shark`).
- `variants[]` — both carry `num_agents: 8` and a `description`:
  1. **`standard`** — "Eight aliases, 14 rounds, a full double round robin: every cog meets every
     other exactly twice." `game_config`: 8 `players` (`Player1`…`Player8`), **`num_agents`: 8**,
     `rounds: 14`, `minRoundIntervalMs: 20000`, `player_connect_timeout_seconds: 180`.
  2. **`quickfire`** — "One pass of the rotation: every cog meets every other exactly once, with
     no second chance to repair a reputation." `game_config`: 8 `players`, **`num_agents`: 8**,
     `rounds: 7`, `minRoundIntervalMs: 20000`, `player_connect_timeout_seconds: 180`.
- `certification` — `game_config`: 8 `players` (the alias names `Sprocket`…`Rivet`),
  **`num_agents`: 8**, `seed: 7`, `rounds: 6`, `minRoundIntervalMs: 0`,
  `player_connect_timeout_seconds: 180`. `players` (every declared runnable must occupy at least
  one slot, raid 0.1.3): `ledger-player`, `ledger-mirror`, `ledger-shark`, `ledger-player`,
  `ledger-mirror`, `ledger-player`, `ledger-mirror`, `ledger-shark`.
- `tools/ci/policies.json` — four distinct versions (champions are LLM prompts; fillers are the
  baselines):

```json
[{"name":"ledger-reputation","run":"/bin/ledger-player","env":{"PLAYER_PROMPT":
  "Your score is the MEDIAN of your per-meeting payoffs, so aim to be reliably worth meeting rather than spectacularly lucky once. Read the partner record before every meeting: if their halo is 0.5 or better and their last meetings show returns and fair offers, cooperate, send 5-6, return 50%, and offer 6. If their record shows defections or zero returns, defect, send 0-1, return 0-25%, and set your floor at 5. Never accept a 0/0 ultimatum you could have taken: as responder set your floor at 3-4, high enough to deter lowballs and low enough that most offers clear it. Write a short honest public note about your previous partner every round - your notes are your reputation too. Keep a memo listing each alias and what they did to you."}},
 {"name":"ledger-broker","run":"/bin/ledger-player","env":{"PLAYER_PROMPT":
  "Play the long game of a public record. Open generous with every alias you have not met (cooperate, send 6, return 50%, offer 6) because the first meeting is an advertisement the whole table reads. After that, mirror: reward anyone whose public record shows they returned or cooperated, and cut off anyone who took. Do not chase a big one-off payoff - the leaderboard reads your median, so a single 12 you gained by defecting costs you the meetings it scares away. As responder in ULTIMATUM set your floor at 4. Use your public note to praise cogs who dealt fairly with you by name and to warn about the ones who did not; use your memo to track every alias's halo yourself."},
  "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
 {"name":"ledger-mirror","run":"/bin/ledger-player","env":{"PLAYER_SCRIPTED":"mirror"}},
 {"name":"ledger-shark","run":"/bin/ledger-player","env":{"PLAYER_SCRIPTED":"shark"}}]
```

## Tests

`tests/test_sim.nim` (pure rules; runs in both debug and `-d:release`):

1. **Schedule.** For seeds `[1, 7, 42, 1234]` and `rounds` in `{4, 7, 14, 28}`: every round is a
   perfect matching of all 8 seats (each seat appears exactly once across the 4 pairs); at
   `rounds = 14` every unordered pair meets **exactly twice**; for any `rounds`, no pair meets
   more than `ceil(rounds / 7)` times; no pair meets in consecutive rounds; and the greedy
   first-mover rule holds, re-derived from the stored schedule — at every asymmetric meeting the
   seat that goes first has no more prior first-mover assignments than its partner, no seat is
   first more often than it plays asymmetric subgames, and the first-mover counts sum to the
   number of asymmetric meetings. (Not a global ±1 balance; see "Roles" above.)
2. **Payoff kernels.** The full 2×2 dilemma matrix; `trustPayoffs` over all
   `s in 0..6 × p in {0, 25, 33, 50, 66, 75, 100}` with the invariant `investor + trustee ==
   8 + s`, `returned` never exceeding `2*s`, and half-up rounding at `p = 25, s = 1`;
   `ultimatumPayoffs` at the acceptance boundary (`o == m` accepts, `o == m - 1` breaks) with the
   invariant total `in {0, 12}`; every payoff in `[0, 14]`.
3. **Score.** `median` for odd `k` (middle), even `k` (mean of the two middles, including a `.5`
   case), `k == 0` → `0.0`; a constructed history where a seat's mean is high and its median is
   low proves the ranking statistic is the median.
4. **Conduct.** Each threshold at its boundary (`s = 2/3`, `p = 49/50`, `o = 4/5`, `m = 5/6`,
   both dilemma moves); `halo == 0.5` before the first meeting.
5. **Gossip.** A note is attributed to last round's partner and discarded in round 1; the board
   keeps insertion order; a 500-rune multi-byte note is cut to ≤ 120 runes, is still valid UTF-8,
   and ends with `…`; a note containing `\n` becomes single-line; `memo` cut at 400 runes.
6. **Rings.** A constructed history in which seats 1 and 5 pay each other 10 twice and earn 2
   elsewhere flags exactly `(1, 5)` with `delta` computed as specified; a history of uniform 6s
   flags nothing; `ringPairs` in `resultsJson` matches `rings.len`; **`scores` is identical with
   and without the ring pattern** (the assertion that ring detection never scores).
7. **Legality.** `LedgerError` on: a player count other than 8, `rounds < MinRounds`, applying a
   round when `done`, applying twice, a move outside range reaching `applyRound` unclamped.
8. **Endings.** `endEarly` sets `reason == "deadline"` and `done`; a full run sets
   `"complete"`; `resultsJson.reason` is only ever one of those two.
9. **Replay, frame by frame.** `replayMatch(config, events).len == events.len + 1`; the final
   frame equals the live sim's `tableStateJson` and `resultsJson`; and then, for **every** `i` in
   `0 .. events.len`: (a) `frames[i].events == events[0 ..< i]` — every event in the frame was
   rebuilt by the rules (`beginRound` / `applyMeeting` / `applyGossip` / `settle` each append
   their own derived event, which `replayMatch` never overwrites with the recorded one), so this
   compares both payoffs, both moves, both memos, both `scripted` flags, the pairings and the
   first movers of every tick; (b) `replayMatch(config, events[0 ..< i])` ends on exactly
   `frames[i]`, so no frame borrows state from an event that has not been played yet; (c) every
   tick at which the LIVE sim published a state — each round's open, and the settlement — equals
   the frame with that event count. The round-*close* tick is not a shared tick: the recorded log
   has no "round closed" event, so `replayMatch` deliberately keeps the round open until the next
   `round` event arrives. A tampered `round` event (a swapped pair) raises; `eventToJson` /
   `eventFromJson` round-trips every one of the five event kinds with every field.
10. **Determinism.** The same seed yields identical schedules, subgames, aliases and scripted
    play; different seeds differ.

`tests/test_bot.nim` (the **bounded-orders / legality assertion on the scripted baseline**, plus
the LLM plumbing that can be tested offline):

1. For seeds `[1, 7, 42, 1234]` and seat mixes (8× `mirror`, 8× `shark`, and 4/4), a full episode
   plays out with **every scripted move inside `legalMoveRange(game, first)` for its role**,
   `applyRound` never raising, every recorded payoff in `[0, 14]`, and `reason == "complete"`.
2. `mirror` reciprocates: against an all-`shark` table its dilemma cooperation rate after the
   first pass is below 0.25, and against an all-`mirror` table above 0.9.
3. `decideAll` with no credentials returns scripted decisions for all 8 seats, issues zero HTTP
   requests, and completes in under a second.
4. Reply parsing: `"cooperate"`, `"C"`, `"defect"`, `0`, `1`, `"5"`, `5.4`, `"50%"`,
   `"6 coins"` all parse to the documented moves; `"maybe"` raises; an out-of-range `9` for a
   0..6 investor clamps to 6; a reply with prose before the object still yields the object
   (`extractJsonObject`).
5. **Batch mapping:** a stubbed batch whose responses are returned out of order still assigns
   each reply to the seat that asked for it (the failure mode that a batched rewrite invites).

**CI (`.github/workflows/ci.yml`, the only harness — the sandbox has no Nim, docker or emsdk):**

- `test` — every `tests/*.nim` in debug and `-d:release`.
- `docker-smoke` — builds `coworld-ledger:ci` and runs `tools/ci/docker_smoke.sh`, which plays
  **one real end-to-end episode in raw docker with the certification fixture's seat mix** (8
  seats, no credentials ⇒ scripted), asserts the game exits 0 having written `results.json` and
  the replay, asserts every **player** container also exited 0 (raid 0.1.4), cross-checks
  `certification.game_config.num_agents == 8` against `len(certification.players)`,
  `len(certification.game_config.players)` and `SMOKE_SEATS = 8`, and **parses the replay as
  strict UTF-8 JSON** (`json.loads(replay.read_bytes().decode("utf-8"))`,
  `SMOKE_REQUIRE_REPLAY_JSON=1`). The replay is uploaded as the `smoke-replay` artifact.
- `wasm-viewer` — `needs: docker-smoke`. Asserts `tools/build_replay_viewer.sh` and
  `tools/ci/viewer_smoke.mjs` are present and executable, builds the bundle, asserts a non-empty
  `.wasm` and an `index.html`, downloads the smoke replay, and **executes the bundle** in
  headless chromium:
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <the docker-smoke
  replay> --timeout 90 --soak 15`. The soak is safe because the cert fixture's replay outlasts
  it: 6 rounds × (1 `round` + 4 `meeting`) + `end` = 31 events at the renderer's per-kind dwell
  (round 700 ms, meeting 1400 ms, gossip 900 ms, end 1500 ms) ≈ 38 s of playback.

## Out of scope (v1)

- **Cross-episode identity persistence.** An alias is permanent within an episode only; there is
  no store that carries a cog's reputation from one episode to the next. (The idea's headline
  feature; it needs platform-side state the coworld contract does not offer, so v1 buys the same
  dynamics with 14 within-episode rounds of public record.)
- **Population scale (20–100 seats).** Fixed at 8 (coordinator ruling): one parallel LLM batch of
  8 per round is what fits the wall-clock budget.
- **Multi-move subgames.** Every meeting resolves in exactly one simultaneous decision via the
  strategy method; no back-and-forth bargaining, no repeated PD *within* a single meeting.
- **Directed messages, side payments, contracts, coalitions as a game mechanic.** Gossip is the
  only channel and it is public, one line, and payoff-free; coins are never transferred between
  cogs.
- **Ring detection as an integrity action.** Rings are measured, drawn and published as a
  finding; nothing is disqualified, penalised or rescored. "One alias per account" is a platform
  concern, not a game rule.
- **RL-vector policies.** The policy interface is a prompt (or a named scripted baseline); there
  is no observation tensor and no action space export.
- **Subgames beyond the three named**, tunable payoff tables in the config schema, seat counts
  other than 8, a live spectator pod for replays, and any viewer zoom/minimap (`#viewpanel`).
