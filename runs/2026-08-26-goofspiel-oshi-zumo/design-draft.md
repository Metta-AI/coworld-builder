# Goofspiel / Oshi-Zumo — design note (`Metta-AI/cogame-goofspiel-oshi-zumo`, v1)

This coworld is forked from **`Metta-AI/cogame-babel`** (read at commit `d55d999`, "0.1.4: static
viewer announces loading/ready/error to its host"), the current head of the parley → cosino →
focus → babel lineage: a turn-based, native-rules, *a-policy-is-just-a-prompt* game whose server
makes every decision by sending the seat's prompt to Claude, with a scripted baseline that plays
any seat and every seat when there are no credentials. That is exactly this game's shape — cards,
sealed bids, one number per seat per round — so babel is the starter, and
every convention there holds here unless this note says otherwise: the `bitworld/runtime` contract, the mummy
HTTP/WS server, the `sim.nim` / `llm.nim` / `server.nim` split, the seeded anonymous cog aliases,
the `PlayBudgetFraction = 0.6` deadline stop, the artifact-writing order in `finishEpisode`, the
`replayMatch` re-derivation, the emscripten `MODULARIZE`/`EXPORT_NAME` viewer, and the Ink & Print
chrome. Where this note deviates from babel it says so and says why. One deliberate borrow from a
sibling is named explicitly and only in `## Decisions`: the **parallel LLM batch**
(`curly.RequestBatch` + `makeRequests`) is ported from `cogame-bullwhip/src/bullwhip/llm.nim`
`decideAll`, because babel is a sequential game and has no batch; no viewer file comes from
bullwhip or from anywhere but babel.

### Source idea (verbatim)

> Port of OpenSpiel's goofspiel and oshi_zumo. Goofspiel (Game of Pure Strategy): each player holds
> cards 1-13; a prize card is revealed each round and everyone simultaneously bids one card;
> highest bid takes the prize, bid cards are spent. Oshi-Zumo: two players with a coin budget
> repeatedly bid to push a sumo token one step toward the opponent's edge. Both are
> simultaneous-move, perfect-information-about-the-past, resource-depletion games — the strategy is
> budget pacing and opponent modelling.
>
> Seats: 2-10 (goofspiel) / 2 (oshi-zumo)
> Motive: zero-sum, simultaneous bidding
> Policy interface: one number per round; LLM trivial to interface; episodes seconds long
> Fills gap: auction/bidding dynamics with no hidden cards — pure pacing; 11 Escrow and 21 Garble
> are about commitment and noise, not budget
> Integrity (anti-collusion): simultaneous sealed bids server-side; anonymous aliases; multi-seat
> goofspiel collusion monitored via bid-pattern audit.
>
> Replay plan (watchability): bids revealed side by side each round; remaining-budget bars;
> 'overbid' gasp when a 13 beats a 1.
>
> Source: OpenSpiel goofspiel, oshi_zumo.

---

## The game

One sim module, one image, one protocol, **two modes** selected by the `mode` field of
`game_config` and shipped as two manifest variants:

| Mode | `mode` | `num_agents` | Resource | Rounds |
|---|---|---|---|---|
| Goofspiel (GOPS) | `"goofspiel"` | **4** | a hand of cards 1..13, one spent per round | exactly 13 |
| Oshi-Zumo | `"oshizumo"` | **2** | a purse of 20 coins, spent per round | at most 20 |

Both are zero-sum, simultaneous-move, and carry **no hidden state about the past**: every bid ever
made is public the instant the round resolves, so the only thing a seat does not know is what the
others will do *this* round (and, in goofspiel, which prize comes next). The whole skill is budget
pacing and opponent modelling — the gap the idea names.

**Seat counts, decided.** Goofspiel is fixed at **4** and oshi-zumo at **2**. Four for goofspiel
because the idea's range (2–10) is a range and CI needs one number: 4 makes "highest bid takes the
prize" genuinely multi-way (concession, tie-splits and stand-asides all exist, none of which exist
at 2), it matches babel's four-seat table so the scorebug, alias pool and art all carry over
unchanged, and it keeps the per-round LLM batch small enough to live inside the Bedrock sidecar's
30-requests-per-minute-per-episode cap (see `## Decisions`). Two for oshi-zumo because the game is
definitionally two-sided — a token has exactly two edges.

### Goofspiel rules

- Seats: 4, indexed 0..3, each holding an identical hand of the cards **1..13**.
- The **prize deck** is the cards 1..13, shuffled once at `initSim` from the episode seed and
  recorded in the replay config as `prizeOrder` (OpenSpiel's `points_order=random`, its default).
  Total prize pool = `1+…+13 = 91`.
- A prize's value is its rank (Ace 1 … King 13). The viewer renders "10", "11", "12", "13" — never
  "T/J/Q/K" — per the legibility pin.
- 13 rounds, one per prize. Every seat spends exactly one card per round, so all hands empty
  together.

**Resolution order for goofspiel round `r` (0-based). This is the order the sim executes, and the
order the events appear in the replay.**

1. `beginRound`: reveal `prize = prizeOrder[r]`. Emit the `prize` event.
2. Build every seat's observation (§`## Server, player, protocol`). Scripted seats are decided
   inline; every LLM seat's request goes out in **one parallel batch** (§`## Decisions`).
3. Each seat returns one integer `bid`. **Legal iff `bid` is still in that seat's hand.** Illegal,
   unparseable or timed-out → one retry in a second batch carrying the legal set → the `match`
   scripted baseline. The seat's `fallbacks` counter increments.
4. All bids are locked server-side, then revealed **simultaneously**. No seat, no spectator socket
   and no player socket sees any bid of round `r` before every bid of round `r` is in
   (§ anti-collusion below).
5. `top = max(bids)`; `winners = { i : bids[i] == top }`.
6. Award: if `|winners| == 1`, that seat's `points` increases by `prize`. Otherwise **each tied
   seat's `points` increases by `prize / |winners|`** — fractional scores are legal.
   *Decided, with reason:* the split is OpenSpiel's goofspiel convention (its returns are computed
   from a point total in which "ties result in a split"; the folk rules also allow discard or
   carry-over). Split is chosen over discard because it keeps the pool constant at 91, which keeps
   the score formula below exactly zero-sum, and over carry-over because carry-over changes the
   strategic game (deliberate tying to build a pot) into something that is no longer the pacing
   game the idea asked for.
7. Every seat removes its bid card from its hand — **spent whether it won or not**.
8. Compute `margin = top − max(bids excluding one instance of top)` (for `|winners| > 1`,
   `margin = 0`). Emit the `reveal` event. If `margin >= 6`, emit an `overbid` event immediately
   after it (§ the gasp).
9. `roundsPlayed += 1`. If `roundsPlayed == 13` → settle `complete` / `prizes-exhausted`.

### Oshi-Zumo rules

Buro's `[N, K, M]` parameterisation, pinned to **`N = 20` coins, `K = 3`, `M = 1`**.

- The field is `2K + 1 = 7` cells indexed 0..6. The token starts at cell `K = 3` (the centre).
- Seat 0 pushes the token **up** (toward cell 6, seat 1's edge); seat 1 pushes it **down** (toward
  cell 0, seat 0's edge). The token is off the field at `> 6` (seat 0 wins) or `< 0` (seat 1 wins).
- Each seat starts with 20 coins. A bid is an integer in `[minBid_i, coins_i]` where
  `minBid_i = min(M, coins_i)` — i.e. normally ≥ 1, but a seat holding 0 coins must bid 0.
- *Decided, with reason:* `M = 1` (rather than OpenSpiel's `min_bid=0` default) because it makes
  the episode length **provably bounded by `N = 20` rounds** — every seat spends at least one coin
  per round while it has one — and a provable round bound is what makes the wall-clock budget in
  `## Decisions` checkable rather than hopeful. Buro 2004 analyses both `M = 0` and `M = 1`;
  `[50,3,1]` is the classic Japanese setting. 20 coins rather than 50 keeps the episode at
  goofspiel's cadence and inside the LLM budget.
- `maxRounds = 20` is also enforced explicitly as a belt-and-braces round cap.

**Resolution order for oshi-zumo round `r`.**

1. `beginRound`: publish `position` and `coins[0..1]`. (No `prize` event in this mode.)
2. Observations built; scripted seats inline; LLM seats in one parallel batch.
3. Each seat returns one integer `bid`, legal iff `minBid_i <= bid <= coins_i`. Same
   retry-then-fallback ladder as goofspiel.
4. Bids locked, then revealed simultaneously.
5. **Both seats pay**: `coins[i] -= bids[i]`, unconditionally.
6. Push: `bids[0] > bids[1]` → `position += 1`; `bids[1] > bids[0]` → `position -= 1`;
   **equal bids → the token does not move** (Buro 2004: "If the bids are equal, the wrestler does
   not move. Both bids are deducted."). *Decided, with reason:* this is the canonical rule and it
   is what makes minimum-bid stalling a real strategy; it is also the only reading under which the
   game stays zero-sum without a tie-breaker that would inject randomness into a
   perfect-information game.
7. Emit `reveal`, then `push` (carrying `delta ∈ {-1, 0, +1}` and `positionAfter`). If
   `margin = |bids[0] − bids[1]| >= 6`, emit `overbid` after `reveal`.
8. End checks, in this order:
   a. `position > 6` → settle `complete` / `pushout`, seat 0 wins.
   b. `position < 0` → settle `complete` / `pushout`, seat 1 wins.
   c. `coins[0] == 0 and coins[1] == 0` → settle `complete` / `coins-exhausted`, scored by
      position.
   d. `roundsPlayed == maxRounds` → settle `complete` / `round-cap`, scored by position.
9. Otherwise `roundsPlayed += 1` and continue.

**Scoring by position** (used for every non-pushout oshi-zumo ending, including `deadline`):
`position > 3` → seat 0 wins; `position < 3` → seat 1 wins; `position == 3` → draw. This is Buro's
rule ("the player in whose half the wrestler is located loses"; centre is a draw) restated in this
note's index convention.

### Scoring formula and sign

One `scores` array, same meaning in both modes, **higher is better, and the array sums to 0**.

- **Goofspiel** (`N` seats, `pool = 91`): let `share_i = points_i / pool`. Then

  ```
  score_i = (N * share_i - 1) / (N - 1)
  ```

  At `N = 4`: `score_i = (points_i - 22.75) / 68.25`. Sum over seats = 0 exactly. Range
  `[-1/3, +1]`; `+1` means "won every prize", `0` means "exactly the equal share".
- **Oshi-Zumo**: `score = +1` for the winner, `-1` for the loser, `0/0` on a draw. Sum = 0.

Both scales top out at `+1`, deliberately, so a seat that dominates one variant and a seat that
dominates the other look the same to the ladder. **The league ranks by mean episode `score`,
higher first.** No other field is a ranking metric.

`results` also reports, for humans and for the audit: `points[]` (goofspiel prize points won;
oshi-zumo the final outcome points `1 / 0.5 / 0`), `spent[]` (total card ranks / coins spent),
`bidsMade[]`, `fallbacks[]` (decisions that fell back to the scripted baseline), `finalPosition`
(oshi-zumo token cell; `-1` in goofspiel), `collusionIndex[]` (below), `rounds`, `maxRounds`,
`mode`, `ending`, `reason`.

### End conditions and `results.reason`

`results.reason` has **exactly two legal values**: `"complete"` and `"deadline"`. *Decided, with
reason:* phase 60 check 5 greps a finished replay for `results.reason == "complete"` (or a
`deadline` the design declares acceptable), so inventing `"pushout"` as a reason would fail
verification on a perfectly healthy episode. The finer ending rides in a **separate** field,
`results.ending`, with exactly five legal values:

| `reason` | `ending` | When |
|---|---|---|
| `complete` | `prizes-exhausted` | goofspiel: the 13th prize resolved |
| `complete` | `pushout` | oshi-zumo: the token left the field |
| `complete` | `coins-exhausted` | oshi-zumo: both purses are 0 after a round |
| `complete` | `round-cap` | oshi-zumo: `maxRounds` rounds played, token still on the field |
| `deadline` | `wall-clock` | the play deadline stopped the episode between rounds |

`deadline` is an **acceptable** ending for this coworld and is declared as such here: the game is
still fully scored at the stop (goofspiel from prizes already awarded; oshi-zumo by token
position), so a deadline episode is a real result, not a discarded one. It should nonetheless be
rare — see the arithmetic in `## Decisions`.

The `end` event carries both `reason` and `ending`, and the **same `settle(reason, ending)` proc**
applies them on record and on playback, so a wall-clock stop — which is not derivable from the
bids — re-derives identically in the wasm viewer (particle-worlds `13c66d7`, 2026-08-26: a
deadline stop applied outside the shared proc hash-mismatches at the stop tick).

### The 'overbid' gasp

One predicate, both modes, emitted as its own event and drawn as its own beat:

```
overbid  ⇔  margin >= 6
margin   =  top bid − highest bid strictly below it (0 when the top is tied)
```

*Decided, with reason:* the idea asks for a gasp "when a 13 beats a 1". A margin of 6 on a 1..13
scale is the smallest gap that cannot be a one-rank duel and reads unambiguously as a blow-out; the
same number works on 20 coins. One predicate for both modes means one CSS class, one feed line and
one scrub-beat kind, instead of two that drift.

### Anti-collusion

Three mechanisms, all from the idea, all structural rather than advisory:

1. **Sealed bids, server-side.** Every decision is made *inside the game server*; a player
   container only delivers a prompt string. There is no channel through which one seat could learn
   another's bid before the reveal: the per-seat `state` frame is redacted to that seat's own
   tallies and hand until the round resolves, and `broadcastLocked` is called for round `r` only
   after `applyBids(r)` has run.
2. **Anonymous aliases.** Seats are `Sprocket`, `Gizmo`, … (babel's `CogNames` pool, seeded
   shuffle); no prompt ever contains a policy name, so no seat can identify a confederate.
3. **Bid-pattern audit, reported not enforced.** `results.collusionIndex[i]` = the share of
   goofspiel rounds in which seat `i` bid its **lowest remaining card** while the round's `margin`
   was ≥ 6 — i.e. it stood aside for someone else's blow-out. Range 0..1, `0.0` for both seats in
   oshi-zumo. It is written to results and to the `end` event; nothing in the episode acts on it.
   0.5 is the threshold at which a human should look.

### Design pins, and where each is satisfied

| Pin (playbook §Phase 0 / SPEC §Design pins) | How this note satisfies it |
|---|---|
| Starter by game shape | cogame-babel — turn-based cards + sealed bids, native rules, policy = prompt (top of this note) |
| Public repo `Metta-AI/cogame-<slug>` | `gh repo create Metta-AI/cogame-goofspiel-oshi-zumo --public` in phase 20; `## Packaging` |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `## Decisions` — `PLAYER_PROMPT` vs `PLAYER_SCRIPTED=match|hoard`, both algorithms given in full |
| Parallel batch + 60 % budget for simultaneous games | `## Decisions` §Batching and the wall-clock budget, with the arithmetic |
| Degrade, never hang | `## Decisions` §The ladder; `deadline` / `wall-clock` ending above |
| Static wasm replay viewer, never a pod | `## Viewer`; `replay_viewer.bundle = static-replay-viewer`; `tools/build_replay_viewer.sh` |
| Real art, starter chrome verbatim | `## Viewer` §Art and §Chrome provenance |
| Legible to a casual spectator | ranks rendered `10/11/12/13`, never `T/J/Q/K`; `## Viewer` §Readouts; 360 px check |
| Two name spaces | aliases in-game, `policyNames` spectator-side, `results.names` = policy names (§ Anti-collusion, `## Server`, `## Viewer`) |
| `num_agents` in every variant and the cert fixture | `## Packaging` — 4 in `goofspiel-4`, 2 in `oshi-zumo-2`, 4 in `certification.game_config` |
| Tests in CI (sim, bot, e2e replay, viewer smoke) | `## Tests` |

---

## Decisions: LLM with scripted fallback

**Both policy kinds ship in the same image from day one, switched by environment**, exactly as
babel does it: `/bin/goofspiel-oshi-zumo-player` reads `PLAYER_PROMPT` (an LLM policy: the string
is delivered to the game server, which sends it to Claude with the seat's observation every round)
or `PLAYER_SCRIPTED=<baseline name>` (a scripted policy: the server plays the named baseline for
that seat, no LLM). `PLAYER_SCRIPTED` accepts `match` and `hoard`; `1`/`true`/`yes` are accepted as
synonyms for `match`. With neither set, the player delivers a built-in default prompt.

### The two scripted baselines (exact algorithms)

Both are deterministic given the sim state, always produce a legal bid, and never produce `say` or
`notes`.

**`match`** — the default, and the fallback every failed LLM decision lands on.

- *Goofspiel.* Let `H` be the seat's remaining hand and `p` the prize.
  1. If `p ∈ H`, bid `p`.
  2. Else bid `min { c ∈ H : c > p }` if that set is non-empty.
  3. Else bid `max(H)`.
  (Ross 1971 showed "match the upturned card" is optimal against a uniformly random bidder, which
  makes this the right reference opponent for a pacing game.)
- *Oshi-Zumo.* Let `d` be the pushes still needed to win: `d = 7 - position` for seat 0,
  `d = position + 1` for seat 1. Bid `clamp(ceil(coins / max(1, d)), minBid_i, coins)`. It spends
  exactly the even rate that would carry the token off the edge with the purse it has.

**`hoard`** — the second filler; a deliberately different pacing shape so the ladder is not two
copies of one bot.

- *Goofspiel.* If `p <= 7`, bid `min(H)`. If `p >= 8`, bid `max(H)`.
- *Oshi-Zumo.* If the seat is one loss from defeat (`position == 6` for seat 1, `position == 0`
  for seat 0), bid `clamp(ceil(coins / 2), minBid_i, coins)`. Otherwise bid `minBid_i`.

### Batching and the wall-clock budget

All seats decide **simultaneously**, so all LLM calls for a round go out as **one parallel batch**:
a `curly.RequestBatch` filled with one `post` per open seat and issued with
`client.curl.makeRequests(batch, llmTimeoutSeconds)` — the `decideAll` shape ported from
`cogame-bullwhip/src/bullwhip/llm.nim`. Sequential per-seat calls are the documented way to blow
the 720 s budget and are not used here.

Config knobs and defaults: `llmTimeoutSeconds = 30`, `maxOutputTokens = 900` (not 400 — Haiku is
cut off at 400), `model = "claude-sonnet-5"` (the hosted Bedrock path tries
`us.anthropic.claude-haiku-4-5-20251001-v1:0` first, and **the candidate list drops
`us.anthropic.claude-sonnet-4-6`**, which times out on every sidecar call — raid, 2026-08-23),
`batchSpacingSeconds = 0` meaning *derive as `4 × num_agents`*.

**Rate limit.** The Bedrock sidecar caps **30 requests per minute per episode**. A round can issue
up to `2 × num_agents` calls (the batch plus one retry batch), so the minimum spacing between round
starts is `2 × num_agents × 60 / 30 = 4 × num_agents` seconds. The loop sleeps to that floor.

**The arithmetic, out loud.** `episodeTimeoutSeconds` defaults to 1200 (the game container never
receives `COWORLD_TIMEOUT_SECONDS`); play budget = `0.6 × 1200 = 720 s`.

| Variant | Rounds | Spacing floor | Expected batch | Expected play | % of 720 s |
|---|---|---|---|---|---|
| `goofspiel-4` | 13 | `4 × 4 = 16 s` | ~3 s (haiku, ~900 input tokens) | `13 × 16.4 ≈ 213 s` | 30 % |
| `oshi-zumo-2` | ≤ 20 | `4 × 2 = 8 s` | ~3 s | `20 × 8.4 ≈ 168 s` | 23 % |

Worst case per round is `llmTimeoutSeconds × 2 attempts + 2 s = 62 s`. `13 × 62 = 806 s` would
overrun, so the loop **refuses to open a round unless `now + 62 s <= playDeadline`** and settles
`deadline` / `wall-clock` instead. That guard, not optimism, is what keeps the episode inside the
budget; the expected path finishes at ~30 % of it.

Certification/smoke path: with no `ANTHROPIC_API_KEY` every seat plays `match`, there is no LLM
call, the spacing floor does not apply (it gates LLM batches only), and the 13-round fixture
completes in well under 5 s of play — inside `coworld certify`'s 60 s default. The release workflow
still passes `--timeout-seconds 300`, and a test pins the fixture's scripted duration under 50 s
(cogame-commons-family, 2026-08-24).

### The ladder — degrade, never hang

Per seat, per round:

1. **Batch call.** Timeout `llmTimeoutSeconds` (30 s), enforced by curly, not by hope.
2. **Parse + legality probe.** The reply is JSON-extracted (first `{` … last `}`, fences and
   trailing prose tolerated), parsed, and then *applied to a copy of the sim* — if `applyBids`
   would reject the bid, the reply is invalid.
3. **One retry**, in a second batch containing only the still-open seats, with the hint appended:
   `"Your previous reply was invalid. Respond with ONLY the requested JSON object; \"bid\" must be
   one of: <the seat's legal set, printed>."` Printing the legal set (computed by the same
   predicate the validator applies) is what halves fallbacks in formal-output games — escrow 0.1.3,
   2026-08-23.
4. **Fallback** to `match`, `fallbacks[seat] += 1`, and a `falling back` line on stdout so the
   hosted log is greppable.
5. If credentials are missing or auth fails, the client disables itself once and every later
   decision is scripted immediately — no network waits.

Episode-level: the play deadline settles the episode between rounds (never mid-round), results and
the replay are written, `/healthz` and `/global` keep answering for a **20 s shutdown grace** after
the artifacts land (lantern 0.1.3 → 0.1.4: the certifier pings `/global` after the player pods
start), then `quit(0)`. The player binary wraps its receive loop in `try/except CatchableError` and
**exits 0 on a dead socket** (raid 0.1.3 → 0.1.4: whisky raises on a close frame and the player
container exits 1).

### The two champion prompts (exact text)

`tools/ci/policies.json` mints four policies. Champion #1 and #2 are both `PLAYER_PROMPT`
policies — a scripted policy seated as a champion is a failure state.

- **`goofspiel-oshi-zumo-tempo`** (champion #1, owner daveey):

  > Pace the budget; do not chase every prize. GOOFSPIEL: price each prize against what it costs
  > you. By default bid the card of the same rank as the prize; bid one rank higher when a rival
  > has already spent that rank; dump your lowest remaining card on any prize of 4 or less. Every
  > rival's remaining cards are public — track them, and take the biggest prize uncontested on the
  > round you are the only seat still holding a high card. OSHI-ZUMO: never outbid by more than one
  > coin. Win cheap pushes and keep a reserve at least as large as the number of pushes you still
  > need. Spend your whole purse only when a single loss would push the token off your own edge.

- **`goofspiel-oshi-zumo-reader`** (champion #2, owner daveey-1,
  `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`):

  > Model the opponents first, then price the prize. Keep a running note of every rival's bid
  > relative to the prize — over, level, under — and reuse it: rivals who overpay early run out of
  > high cards, so from mid-game bid one rank above their observed average on big prizes and the
  > minimum on small ones. GOOFSPIEL: concede any prize two rivals are both likely to fight for —
  > let them burn cards against each other and take the next one. OSHI-ZUMO: alternate a cheap
  > probe with a decisive strike. If the opponent's last three bids were each above half their
  > remaining purse, bid one coin and let them bleed; if they have been minimum-bidding, spend
  > enough to take two pushes in a row.

- **`goofspiel-oshi-zumo-match`** (filler): `PLAYER_SCRIPTED=match`.
- **`goofspiel-oshi-zumo-hoard`** (filler): `PLAYER_SCRIPTED=hoard`.

The player binary's built-in default prompt (used when `PLAYER_PROMPT` is unset and the seat is not
scripted) is: *"Bid to win the prizes that are worth winning and no others. Spend in proportion to
value, keep your high cards for the high prizes, and watch what every rival has already spent —
their remaining resources are public. Reply with only the JSON object."*

---

## Sim module

Pure rules, no IO, no networking, no LLM — driven identically by the server, the tests and the wasm
viewer, which is what makes the replay re-derivable. Layout mirrors babel's; the Nim package is
`gozu` (short for goofspiel-oshi-zumo; the *binaries* carry the full slug because
`tools/ci/docker_smoke.sh` defaults to `/bin/<slug>`).

```
gozu.nimble
src/gozu.nim                 entrypoint  -> /bin/goofspiel-oshi-zumo         (fork of src/babel.nim)
src/gozu_player.nim          player      -> /bin/goofspiel-oshi-zumo-player  (fork of src/babel_player.nim)
src/gozu/types.nim           config, events, enums                          (fork of src/babel/types.nim)
src/gozu/sim.nim             the rules below                                (fork of src/babel/sim.nim)
src/gozu/llm.nim             Claude client, batch, prompts, baselines       (fork of src/babel/llm.nim
                                                                             + bullwhip's decideAll)
src/gozu/server.nim          mummy HTTP/WS server, replay writer            (fork of src/babel/server.nim)
replay-viewer/gozu_replay.nim  wasm entry                                   (fork of replay-viewer/babel_replay.nim)
```

### Types

```nim
type
  Mode* = enum
    mGoofspiel = "goofspiel"
    mOshiZumo  = "oshizumo"

  GameConfig* = object
    tokens*: seq[string]                # connection tokens, injected by the runner
    players*: seq[PlayerConfig]         # policy display names, by slot
    mode*: Mode
    seed*: int
    cards*: int                         # goofspiel: 13
    coins*: int                         # oshizumo: 20
    size*: int                          # oshizumo: K = 3  (field is 2K+1 = 7 cells)
    minBid*: int                        # oshizumo: M = 1
    maxRounds*: int                     # goofspiel: = cards; oshizumo: = coins
    episodeTimeoutSeconds*: int         # 1200
    batchSpacingSeconds*: int           # 0 => derive 4 * seats
    turnDelayMs*: int                   # 400 (0 in the cert fixture)
    playerConnectTimeoutSeconds*: float # 180
    model*: string
    maxOutputTokens*, llmTimeoutSeconds*: int
    sampled*: bool                      # true once the budget fit has been applied

  EventKind* = enum
    evStart = "start", evPrize = "prize", evReveal = "reveal",
    evOverbid = "overbid", evPush = "push", evEnd = "end"
```

`update(config, json)` applies the runtime JSON over the defaults and **raises** on: an unknown
`mode`, `cards` outside 4..13, `coins` outside 4..50, `size` outside 1..5, `minBid` outside 0..2,
`players.len` outside 2..10, `mode == mOshiZumo and players.len != 2`.

`sampleEpisode(config)` is idempotent (a replay carrying `sampled: true` is untouched) and fits the
round count: `maxRounds = min(maxRounds, cards)` for goofspiel and `min(maxRounds, coins)` for
oshi-zumo, plus `turnDelayMs = min(turnDelayMs, 120_000 div max(maxRounds,1))`.

### Sim state

```nim
Sim* = object
  config*: GameConfig
  names*: seq[string]            # anonymous cog aliases, seeded shuffle of babel's CogNames
  prizeOrder*: seq[int]          # goofspiel: the shuffled deck, drawn at initSim
  hands*: seq[seq[int]]          # goofspiel: each seat's remaining cards, ascending
  coins*: seq[int]               # oshizumo: each seat's purse
  position*: int                 # oshizumo: token cell 0..2K; -1 in goofspiel
  points*: seq[float]            # goofspiel prize points (fractional on splits)
  outcome*: seq[float]           # oshizumo 1/0.5/0; goofspiel unused
  spent*: seq[int]
  bids*: seq[int]                # this round; -1 before the reveal
  bidsShown*: bool
  says*, notes*: seq[string]
  scripted*, fellBack*: seq[bool]  # per seat, this round
  fallbacks*: seq[int]
  lowBidStandAside*: seq[int]    # numerator of collusionIndex
  round*, roundsPlayed*: int
  done*: bool
  reason*, ending*: string
  events*: seq[GameEvent]
```

### Procs the server, tests and viewer all call

- `initSim(config): Sim` — seeds aliases, the prize deck, hands/purse, `position = size`; logs
  `evStart`.
- `legalBids*(sim, seat): seq[int]` — the seat's legal set (its hand; or `minBid_i .. coins_i`).
  **The prompt, the retry hint and the validator all call this same proc**, so they cannot drift.
- `beginRound*(sim)` — advances the round, logs `evPrize` in goofspiel.
- `applyBids*(sim, bids: seq[int], says, notes: seq[string], scripted: seq[bool])` — the numbered
  resolution above, in one atomic step. Raises `GozuError` naming the offending seat and bid if any
  bid is illegal (the server probes with this on a copy before committing).
- `endEarly*(sim)` — `settle("deadline", "wall-clock")`.
- `settle*(sim, reason, ending)` — the single proc that ends the game, on record **and** on
  playback.
- `score*(sim, seat): float`, `resultsJson*(sim)`, `tableStateJson*(sim)`.
- `replayMatch*(config, events): seq[Sim]` — re-derives one state per event prefix by replaying
  `evReveal` (bids) and `evEnd` (reason/ending) through the same rules; `evPrize`, `evOverbid` and
  `evPush` are re-derived and **checked** against the recording, raising on a mismatch.
- `eventToJson*` / `eventFromJson*`.

### Event vocabulary written to the replay

Six kinds. Every kind has a feed line, a scrub-beat class and CSS (`## Viewer`).

| kind | fields |
|---|---|
| `start` | `{kind}` — episode opens (config and names ride in the replay header) |
| `prize` | `{kind, round, prize, prizesLeft:[int]}` — goofspiel only |
| `reveal` | `{kind, round, bids:[int], winners:[int], award:[float], margin:int, coinsAfter:[int], handsAfter:[[int]], points:[float], says:[str], notes:[str], scripted:[bool], fellBack:[bool]}` |
| `overbid` | `{kind, round, seat, bid, margin, over:int}` — `over` is the highest bid it beat |
| `push` | `{kind, round, delta:int, positionAfter:int}` — oshi-zumo only |
| `end` | `{kind, round, reason, ending, scores:[float], collusionIndex:[float]}` |

`says` and `notes` are the *already-truncated* strings (rune boundaries — see the reply schema);
nothing else in an event is free text. `handsAfter` is recorded rather than re-derived only so that
a viewer frame is complete without walking the prefix; `replayMatch` asserts it against the
re-derivation, which is how a drift becomes a test failure instead of a silent divergence.

---

## Server, player, protocol

Babel's server, forked. Routes, in registration order (all before any catch-all, per lantern
0.1.1 — the certifier probes `/healthz`, `GET /client/player?slot=0&token=…` and
`GET /client/global` *before* the player pods start, and neither client route may open the player
socket):

```
GET /healthz                 {"ok": true}
GET /client/global           client/global.html
GET /client/player           client/player.html
GET /client/replay           client/replay_broadcast.html
GET /client/renderer.js      the game block
GET /client/chrome_common.js the chrome
GET /client/chrome.css
GET /client/assets/@name     data/*.png, data/font.ttf
WS  /player?slot=N&token=T   gozu.player.v1   (live mode only)
WS  /global                  spectator snapshots; answers Ping with Pong
WS  /replay                  the replay payload (replay mode only)
```

### Player protocol `gozu.player.v1`

JSON text frames on `COWORLD_PLAYER_WS_URL`.

game → player:

- `{"type":"welcome","protocol":"gozu.player.v1","slot":N,"name":"<alias>","mode":"goofspiel","seats":4,"maxRounds":13}`
- `{"type":"state","slot":N,"name":"<alias>","round":r,"maxRounds":M,"roundsPlayed":k,"mode":…,"seat":{"score":f,"points":f,"spent":i,"hand":[…],"coins":i},"position":i,"started":b,"done":b,"reason":s,"ending":s}` after every event, **redacted to the seat's own resources until the round resolves** (nothing else is hidden — the past is public — but the current round's bids are not in the frame before the reveal).
- `{"type":"final","done":true,"slot":N,"scores":[…],"points":[…],"names":[<aliases>],"rounds":k,"reason":s,"ending":s}` at the end; the player exits after it.

player → game:

- `{"type":"prompt","prompt":"<≤4000 chars>","scripted":"match"|"hoard"|true|false}` — sent on
  connect and again after `welcome` (the first send can race slot registration). The latest frame
  wins. Over-cap prompts are truncated **on a rune boundary**.

### Global protocol

`/global` sends the whole snapshot after every event:
`{"type":"state","game":"goofspiel-oshi-zumo","mode":…,"seats":[{name,policy,points,score,hand,coins,bid,say,notes,spent}],"round","maxRounds","roundsPlayed","prize","prizesLeft","position","push","overbid","margin","phase","gameDone","reason","ending","policyNames","events":[…],"started","connected":[bool]}`.
`phase ∈ {"bidding","reveal","between","done"}`.

### The observation each seat gets (complete)

The system prompt (identical for every seat, per mode) states the rules verbatim from `## The
game`, the seat's alias, and the output contract, ending with: *"reply with ONLY one JSON object,
nothing else — no analysis, no explanation, no markdown fences. Your reply must begin with the
character `{` and end with `}`."* (Bedrock Haiku answers prose-first without this.)

The user prompt, goofspiel:

1. `Round <r+1> of 13. You are <alias>. Seats: <alias list, in seat order>.`
2. `THE PRIZE THIS ROUND: <p>` and `PRIZES STILL TO COME (order unknown): <sorted list>`.
3. `YOUR HAND: <ascending list>` and `YOUR LEGAL BIDS: <legalBids(seat)>` — the same proc the
   validator uses.
4. `EVERY SEAT'S REMAINING HAND:` one line per seat — public, this game has no hidden cards.
5. `POINTS SO FAR:` one line per seat (`<alias>: 24.5`), plus `EQUAL SHARE WOULD BE 22.75`.
6. `HISTORY:` one line per resolved round — `Round 3 — prize 11 — Sprocket 12, Gizmo 4, Ratchet 12,
   Widget 1 — Sprocket and Ratchet split 5.5 each.` Every bid ever made, every round.
7. `YOUR NOTES FROM EARLIER ROUNDS:` the seat's latest notes verbatim, or `(none)`.
8. `GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules):` the seat's
   `PLAYER_PROMPT`.
9. The reply contract (below).

Oshi-zumo replaces lines 2–5 with: `THE FIELD: cells 0..6, token at 4. You push toward cell 6.
Pushing it past cell 6 wins; if the round cap or your purses run out first, whoever's half the
token is NOT in wins, and cell 3 is a draw.` / `YOUR PURSE: 12 coins. OPPONENT'S PURSE: 9 coins.` /
`YOUR LEGAL BIDS: 1..12 (minimum bid 1).` / `PUSHES YOU STILL NEED: 3.` History lines read
`Round 5 — you 4, Gizmo 4 — equal, no push — token 4.`

**Hidden from a seat:** the other seats' *current-round* bids (until the reveal), the other seats'
private notes and `say` drafts before the reveal, every seat's `PLAYER_PROMPT` including its own
operator's competitors, all policy display names, and — in goofspiel — the **order** of the
remaining prizes. Nothing else.

### Reply schema, with caps

```json
{"bid": 11, "say": "burning a king on a four", "notes": "Gizmo overpays on 8+; save my 13"}
```

| field | type | required | cap | on violation |
|---|---|---|---|---|
| `bid` | integer | **yes** | must be in `legalBids(seat)` | retry once, then `match` |
| `say` | string | no | **80 characters**, single line | truncated |
| `notes` | string | no | **400 characters** | truncated |

Accepted `bid` spellings: a JSON integer; a JSON float (rounded half-up); a numeric string with
surrounding whitespace or trailing prose (`"11 — the king"`); and, in goofspiel only, the letters
`A/J/Q/K` (any case) mapped to `1/11/12/13`. Everything else is invalid.

**Every truncation is on a rune boundary**, with `…` appended, via one shared
`cleanText(text, cap)` (babel's `cleanNotes`, generalised): `say` (80), `notes` (400), the delivered
prompt (4000), and any error text that reaches an event or the log (200). A byte-boundary cut is
how a replay renders in a browser but fails a strict JSON parser; `tests/test_replay.nim` pins it
with multi-byte input at exactly the cap.

Newlines in `say` are replaced by spaces (it is drawn on one line in a reserved band).

### Replay bytes (self-sufficient)

`replayPayload` writes, and the wasm module reads, exactly:

```json
{"protocol": "gozu.replay.v1",
 "names": ["Sprocket","Gizmo","Ratchet","Widget"],
 "policyNames": ["gozu-tempo","Baseline (1)","gozu-reader","Baseline (2)"],
 "config": {"mode":"goofspiel","seats":4,"seed":874421,"cards":13,
            "prizeOrder":[7,13,2,9,…],"coins":0,"size":0,"minBid":0,
            "maxRounds":13,"sampled":true},
 "events": [ … the six kinds above … ],
 "results": { … the results object … }}
```

Names, policy names, the full config, the seed, the prize order and every event are in the bytes;
the viewer contacts nothing but S3 for the file.

---

## Viewer

### The four viewer files come from cogame-babel — all four, no mixture

`replay-viewer/config.nims`, the wasm entry `replay-viewer/gozu_replay.nim`,
`replay-viewer/static_replay.js` and `replay-viewer/index.html` are **all four forked from
`cogame-babel`** and from nothing else. This is not a stylistic preference: babel's `config.nims`
links with `-s MODULARIZE=1 -s EXPORT_NAME=BabelReplayModule` and babel's `static_replay.js`
bootstraps with `BabelReplayModule().then(…)`; splicing one starter's shell onto another's link
flags (an `onRuntimeInitialized` bootstrap against a `MODULARIZE` build) leaves the factory
uncalled, throws nothing, and hangs the viewer forever — cogame-lantern, 2026-08-23.

The fork renames, and renames only:

- `config.nims`: output `dist/gozu_replay.js`, `EXPORT_NAME=GozuReplayModule`,
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_gzu_load_replay,_gzu_payload_ptr,_gzu_payload_len,_gzu_error_ptr,_gzu_error_len`.
  Every other switch (`--mm:arc`, `--exceptions:goto`, `-d:useMalloc`, `ALLOW_MEMORY_GROWTH`,
  `ABORTING_MALLOC=1`, `ENVIRONMENT=web`, `EXPORTED_RUNTIME_METHODS=HEAPU8`) is kept byte-for-byte
  — the `useMalloc`/`ABORTING_MALLOC` pair is load-bearing and its comment travels with it.
- `gozu_replay.nim`: babel's entry with `bab_*` → `gzu_*`; it parses the replay JSON, runs
  `replayMatch`, and emits `{protocol, names, policyNames, config, events, results, states}` where
  `states[i]` is `tableStateJson` after `events[0..<i]`.
- `static_replay.js`: babel's file with `BabelReplayModule` → `GozuReplayModule`, `_bab_*` →
  `_gzu_*`, `BabelRenderer` → `GozuRenderer`. `FETCH_TIMEOUT_MS = 20000`, the Retry button and the
  `{src:"coworld-replay", type}` parent bridge are kept.
- `index.html`: babel's static page with the script list
  `chrome_common.js, renderer.js, gozu_replay.js, static_replay.js` and the game's wordmark.

**Load signalling.** The shell sets `data-replay-loaded="true"` on `document.documentElement` on
its **first drawn frame** and `data-replay-error="<message>"` on failure (and removes the error
attribute on a retry). One required deviation from babel: babel sets `data-replay-loaded` inside
the renderer's ready callback but posts the bridge `ready` from a double-`requestAnimationFrame` at
the call site, so `ready` can precede the first painted frame and an embedding page can sample an
unpainted shell (chorus `3c11c953`, 2026-08-24). Here `attachReplay` takes an `onFirstFrame`
callback, sets `data-replay-loaded="true"` inside it, and the shell posts `ready` **from that
callback**, after the attribute.

### Chrome provenance

- **`client/chrome.css`** — cogame-babel's `client/chrome.css` (443 lines) copied byte-for-byte.
  Not one starter rule is edited or deleted. The game's rules are **appended** below the last
  starter line under `/* ===== goofspiel-oshi-zumo game block ===== */`: the bid table, the budget
  bars, the token track, the `say` band, the six beat-kind classes, the `--band`/`--hudscale`
  consumers and the ≤ 640 px / ≤ 360 px media queries.
- **`client/chrome_common.js`** — the chrome half of cogame-babel's `client/renderer.js`, copied
  from the starter file (not retyped) as these contiguous regions of `d55d999`, in this order:
  lines **101–127** (`ellipsize`, `hexToRgb`, `shade`, `rgba`), **680–734** (`// ---- Names ----`
  through `clampName`: `isBaselineFiller`, `makeNameMap`, `applyNames`), **735–745** and
  **790–864** (the feed block: `roundBase`, `blockHead`, `renderFeed`, `escapeHtml`), **865–901**
  (`// ---- Animation bookkeeping ----`), **934–1049** (`updateScorebug`, `reasonLine`,
  `updateEndscreen`, `bindFeedToggle`) and **1145–1222** (`buildScrub`). It exports
  `window.GozuChrome`. **Exactly one copied line is edited**, and it is named here so a reviewer
  can find it: inside `renderFeed`, the direct call to babel's `describeEvent(event, nameMap, ctx)`
  becomes `feedText(event, nameMap, ctx)`, where `feedText` is injected once by
  `GozuChrome.setFeedText(fn)` from the game block. Everything else in the file is copied bytes or
  **appended** at the end: `relayout()`, `markRoundBeat()` (the labelled-button beat builder) and
  `setFeedText`. Nothing is renamed in place.
  Babel's game-specific procs (`describeEvent`, `spellTokens`, `endText`, `phaseText`,
  `matchHeader`, `stateToView`, `attachLive`, `attachReplay`, the scene/glyph/ribbon drawing at
  128–679) are **not** copied; their replacements live in the game block.
- **`client/renderer.js`** — the game block. Draws the bid table and exports
  `window.GozuRenderer = {attachLive, attachReplay, renderFeed, bindFeedToggle}`. It declares **no
  identifier already exported by `GozuChrome`**, and its beat builder is named `markRoundBeat`, not
  `markBeat` — a game-block `function markBeat` is hoisted over the chrome alias
  `var markBeat = C.markBeat` and silently turns every beat into an unlabelled div that never seeks
  (tandem, 2026-08-23). A CI check asserts the non-overlap (`## Tests`).
- **`client/replay_broadcast.html`** — cogame-babel's `client/replay.html`, copied byte-for-byte
  and renamed, **with a game block appended**; it is not a rewrite that reuses the starter's ids
  (cogame-gridlock, 2026-08-23). Served at `/client/replay`.
  **Kept, unchanged:** `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`,
  `#statuschip`, `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`,
  `#endscreen`, `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`,
  `#loading`, and the `/replay` websocket bootstrap.
  **Removed from the starter page: nothing.** Changed: the `<title>` text, the `#wordmark` inner
  text (`BA<span>BEL</span>` → `GO<span>ZU</span>`), and the `<script src>` list (which gains
  `chrome_common.js`).
  `client/global.html` and `client/player.html` are copied the same way (byte-for-byte + wordmark
  text), because the certifier fetches both before the player pods start.
- **Zoom: dropped.** Babel has no `#viewpanel`, and none is added. The board here is a fixed
  bidding table — four bid cards, a prize, a seven-cell track — that always fits the frame, so the
  zoom bar and minimap have nothing to do and would only steal height at 360 px. (Pin: `#viewpanel`
  is kept only when the board is larger than the frame.)

### Transport rules

- `relayout()` (in `chrome_common.js`) measures `#transport` and sets **`--band`** (its height in
  px) and **`--hudscale`** (`clamp(0.72, viewportWidth / 1280, 1)`) **on `:root`**. It runs on
  `load`, on `resize`, and on every feed toggle.
- **Nothing is ever overlaid in the transport band.** `#endscreen` is `position:absolute; top:0;
  bottom: var(--band);` so the endcard stops exactly at the band, and the scrubber and play button
  are always clickable.
- **Every seek dismisses the endcard**: `setIndex(next, jumped)` removes `.show` from `#endscreen`
  whenever `index < events.length`, and the scrub's `onSeek` always calls it.
- **Scrubber beats are clickable, labelled buttons**: `markRoundBeat` appends
  `<button type="button" class="beat-marker beat-<kind>" aria-label="…" title="…">` for every
  recorded event, and clicking one seeks to that event. CSS exists for **every kind emitted** —
  `.beat-start`, `.beat-prize`, `.beat-reveal`, `.beat-overbid`, `.beat-push`, `.beat-end` — with
  `.beat-overbid` the tall amber one and `.beat-end` the tall paper one, plus the seat-tinted
  `.seat0….seat3` modifier on `reveal` beats (winner's colour).

### Readouts

- **Clock** (`#clock`): `GOOFSPIEL · ROUND 4 / 13 · PRIZE 11` or
  `OSHI-ZUMO · ROUND 7 / 20 · TOKEN 4`.
- **Scorebug** (`#scorebug`): one plate per seat — seat colour chip, `.plate-name` carrying the
  **policy name** (spectator side; the anonymous alias is the small sub-label), the running total
  (`24.5 pts` / `12 coins`), a **remaining-budget bar** (goofspiel: the sum of the ranks still in
  hand, out of 91; oshi-zumo: coins out of 20), and this round's bid card once revealed.
  `.plate-name` gets `flex: 1 1 auto; min-width: 3.2em` and its label is hidden under 640 px — the
  featured-match iframe on softmax.com is ~360 px wide and names otherwise collapse to "…".
- **Board** (`canvas#table`):
  - *Goofspiel* — the prize card face-up in the centre with its rank drawn large; the four seats
    arranged around it; on `reveal`, all four bid cards flip face-up **side by side** in seat
    order, the winner's card lifts and tints, split winners both lift. A spent-cards strip under
    each seat shows what is gone.
  - *Oshi-Zumo* — a seven-cell track drawn as a dohyō strip with the sumo token on it; both bids
    appear side by side as coin stacks; the token slides one cell on `push` and shakes on an equal
    bid.
  - `overbid` throws a full-width **OVERBID** banner across the board for 900 ms, above the board
    only, never into the transport band.
  - Each seat's `say` is drawn in a **reserved band** under its plate, sized from `MaxSayLen = 80`
    measured in the render font at the current `--hudscale`, so a full-cap line can never be laid
    out at a negative coordinate (cogchemists, 2026-08-24).
- **Feed** (`#feed`): one block per round — `ROUND 4 · PRIZE 11`, then one line per seat
  (`Sprocket bids 12 — "burning a king on a four"`), then the verdict
  (`Sprocket takes 11` / `Sprocket and Ratchet split 5.5 each` / `equal bids — no push`), and an
  amber `OVERBID` line when the event fired. The end block names the reason and ending.
- **Endcard** (`#endscreen`): final standings sorted by `score`, each with points/coins and the
  policy name; one reason line (`complete — token pushed off cell 6` /
  `deadline — stopped after 9 of 13 rounds`).
- **Legibility at 360 px is a requirement**: at 360 px the feed collapses (toggle), the scorebug
  drops to two rows of two plates, ranks stay numeric (`11`, `13` — never `J`/`K`), and the clock
  drops the mode word. The renderer fixture in `## Tests` checks 360 / 640 / 1280 px.

### Art (real, not placeholders)

- `data/font.ttf` + `data/FONT_LICENSE.txt` — copied from babel (Rajdhani).
- `data/arena_floor.png` — copied byte-for-byte from babel (MIT, originally coworld-ctf); the table
  surface.
- `data/soldier_red_front.png`, `_blue_`, `_green_`, `_yellow_` — copied from babel; the four seat
  avatars in the scorebug (oshi-zumo uses red and blue).
- **`data/sumo_token.png`** — new, authored for this repo: a 96×96 ink-on-paper sumo wrestler in
  the chrome palette (`--ink` on transparent, `--amber` mawashi), drawn facing the direction of the
  last push (the renderer mirrors it).
- **`data/card_back.png`** — new, 120×168, the prize deck's back in the same palette.
  Card *faces* are drawn on canvas (rounded rect, `--paper` field, rank in two corners and large in
  the centre, seat-tinted edge) so they stay crisp at every `--hudscale`.

The build hook `tools/build_replay_viewer.sh` (fork of babel's, with the `mkdir -p` fix from ecos
2026-08-23 so it works on a fresh CI checkout) copies into the bundle: `gozu_replay.js`,
`gozu_replay.wasm`, `replay-viewer/index.html`, `replay-viewer/static_replay.js`,
`client/renderer.js`, `client/chrome_common.js`, `client/chrome.css`, and
`assets/{arena_floor.png, soldier_*_front.png, sumo_token.png, card_back.png, font.ttf}`. It is
committed mode `100755`.

---

## Packaging

- **`compose.yaml`** — one service:

  ```yaml
  services:
    goofspiel-oshi-zumo:
      image: coworld-goofspiel-oshi-zumo:latest
      platform: linux/amd64
      build: {context: ., network: host}
  ```

  The manifest image placeholder is derived from the **compose service name**, so it is
  `{{GOOFSPIEL_OSHI_ZUMO_IMAGE}}` (service name uppercased, `-` → `_`). `{{GAME_IMAGE}}` is not a
  thing (lantern 0.1.0, 2026-08-23).

- **`Dockerfile`** / **`Dockerfile.replay-viewer`** — babel's, with the binary names changed to
  `/bin/goofspiel-oshi-zumo` and `/bin/goofspiel-oshi-zumo-player`.

- **`coworld_manifest_template.json`** — babel's shape, updated to the 0.1.42 upload contract:
  `$schema` present; ≥ 3 top-level `tags`
  (`["bidding","simultaneous-move","zero-sum","cards","llm-driven","two-player","four-player","openspiel-port"]`);
  `game.name = "goofspiel-oshi-zumo"` (**the secret namespace is `game.name`**, so
  `ANTHROPIC_API_KEY_URI = secret://coworld/goofspiel-oshi-zumo/anthropic_api_key`);
  `game.description` present (`game.tags` absent — tags are top-level only); `game.owner =
  "daveey@gmail.com"`; `game.runnable = {"type":"game", "image":"{{GOOFSPIEL_OSHI_ZUMO_IMAGE}}",
  "run":["/bin/goofspiel-oshi-zumo"], "env":{…}, "source_url":…}`;
  **`game.replay_viewer = {"bundle": "static-replay-viewer"}`** (inside `game`, not top-level); no
  top-level `version`; no `game.display_name`; `episode_timeout_minutes: 20` top-level.

- **`game.config_schema`** — a real JSON Schema, `additionalProperties: false`,
  `required: ["tokens","players"]`. **Every array property carries `minItems`/`maxItems`**:
  `tokens` and `players` `minItems 2, maxItems 10`. Scalar properties: `mode`
  (`enum ["goofspiel","oshizumo"]`, default `"goofspiel"`), `num_agents` (integer 2..10), `seed`,
  `cards` (4..13, default 13), `coins` (4..50, default 20), `size` (1..5, default 3), `minBid`
  (0..2, default 1), `maxRounds` (2..60), `episodeTimeoutSeconds` (60..6000, default 1200),
  `batchSpacingSeconds` (0..60, default 0), `turnDelayMs` (0..10000, default 400), `model`,
  `maxOutputTokens` (64..2000, default 900), `llmTimeoutSeconds` (5..300, default 30),
  `player_connect_timeout_seconds` (number ≥ 0, default 180).
  **No `game_config` anywhere — variant or fixture — contains a literal `tokens` array**; the
  runner injects it, and matriculate rejects "runner-managed tokens" if one is present
  (cogame-knights-archers, 2026-08-26). `config_schema` still *requires* `tokens`.

- **`game.results_schema`** — the fields listed in `## The game`, with `reason`
  `enum ["complete","deadline"]` and `ending` `enum ["prizes-exhausted","pushout",
  "coins-exhausted","round-cap","wall-clock"]`; all arrays `minItems 2, maxItems 10`.

- **`game.protocols`** — **both** keys, each a `{"type":"text","value":"…"}` object (bare strings
  are a platform-side validation error the repo CI does not catch — cogame-garble 0.1.0):
  `player` = the `gozu.player.v1` text from `## Server, player, protocol`, including "a policy is
  just a prompt: reuse the published player runnable with `PLAYER_PROMPT`"; `global` = the `/global`
  snapshot shape and the three client pages.

- **`game.docs`** — `readme` = `{"type":"text","value":…}` (what the game is, how to field a
  policy) and `pages` = `[{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…}}]`
  carrying the numbered resolution orders, the tie rules, the scoring formula and the ending table
  verbatim from this note.

- **Bundled players** — top-level `player[]`, two entries, each with `id`/`type`/`name`/
  `description`/`image`/`run`/`source_url` and
  `resources: {requests:{cpu:"100m",memory:"64Mi"}, limits:{cpu:"1"}}` (the bundled minimum for
  `cpu` is `"1"`; `500m` is rejected at upload — cogame-pistonball 0.1.1):
  - `goofspiel-oshi-zumo-player` — the prompt player (no `PLAYER_SCRIPTED`).
  - `goofspiel-oshi-zumo-scripted` — `env: {"PLAYER_SCRIPTED": "match"}`.

- **`variants[]` — exactly two, each with a `description` and `num_agents`:**

  | `id` | `name` | `num_agents` | `game_config` |
  |---|---|---|---|
  | `goofspiel-4` | Goofspiel — four cogs | **4** | `{"mode":"goofspiel","players":[{"name":"Player1"},…×4],"num_agents":4,"cards":13,"maxRounds":13,"turnDelayMs":400,"player_connect_timeout_seconds":180}` |
  | `oshi-zumo-2` | Oshi-Zumo — head to head | **2** | `{"mode":"oshizumo","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"coins":20,"size":3,"minBid":1,"maxRounds":20,"turnDelayMs":400,"player_connect_timeout_seconds":180}` |

- **`certification`** — the goofspiel variant, because it is the multi-seat one and therefore the
  stronger cross-check:

  ```json
  {"game_config": {"mode":"goofspiel",
                   "players":[{"name":"Sprocket"},{"name":"Gizmo"},
                              {"name":"Ratchet"},{"name":"Widget"}],
                   "num_agents": 4, "seed": 11, "cards": 13, "maxRounds": 13,
                   "turnDelayMs": 0, "player_connect_timeout_seconds": 180},
   "players": [{"player_id":"goofspiel-oshi-zumo-player"},
               {"player_id":"goofspiel-oshi-zumo-scripted"},
               {"player_id":"goofspiel-oshi-zumo-player"},
               {"player_id":"goofspiel-oshi-zumo-scripted"}]}
  ```

  Both declared runnables occupy a slot — a fixture that seats only one fails cert
  `players_missing` (raid 0.1.2 → 0.1.3). `num_agents = 4` here, `4` in `goofspiel-4`, `2` in
  `oshi-zumo-2`; **`<SEATS>` in `tools/ci/docker_smoke.sh` is `4`**, matching the fixture it drives.

- **`.github/workflows/`** — `ci.yml`, `coworld-release.yml`, `coworld-submit.yml` from
  `coworld-builder/templates/`, with `SLUG=goofspiel-oshi-zumo`,
  `IMAGE=coworld-goofspiel-oshi-zumo`, `<SEATS>=4`. The release workflow's certify step passes
  `--timeout-seconds 300`, and its `secret put` step reads the namespace from the manifest's
  `game.name`.

- **`tools/ci/policies.json`** — the four policies from `## Decisions`; champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Player-side Bedrock is not used (all
  decisions are server-side), so no `USE_BEDROCK` is set on the policies; the *game* runnable's
  `env` carries `ANTHROPIC_API_KEY_URI`, which is the thing that must be present or every hosted
  episode silently plays scripted (hive, 2026-08-23).

---

## Tests

Everything below runs in `ci.yml`; the sandbox has no docker, nim, emsdk or browser, so CI is the
only harness. `NIM_TESTS` is left unset — every `tests/*.nim` runs in both debug and `-d:release`.

**`tests/test_sim.nim` — the rules.**

1. Goofspiel: a single winner takes the whole prize; the pool over 13 rounds is exactly 91.
2. Goofspiel tie: two seats bidding the top value each gain `prize/2`; three seats `prize/3`; a
   four-way tie gains `prize/4` each and `margin == 0`, so no `overbid` fires.
3. Goofspiel legality: a bid not in hand raises; each card can be spent once; after 13 rounds every
   hand is empty; `legalBids` shrinks by exactly one element per round.
4. Prize order is a permutation of 1..13, is a pure function of the seed, and is reproduced from
   `config.prizeOrder` alone.
5. Oshi-zumo: higher bid pushes one cell toward the opponent; **equal bids do not move the token**;
   both purses are debited in all three cases; a bid above the purse or below `minBid_i` raises;
   with `coins < minBid` the only legal bid is `coins`.
6. Oshi-zumo endings: `pushout` from cell 6 with a win for seat 0; `coins-exhausted` scored by
   position; `round-cap` at `maxRounds`; a token resting on cell 3 is a draw with `scores == [0,0]`.
7. Oshi-zumo termination: with `minBid = 1` and `coins = 20`, **every** seeded episode ends within
   20 rounds (200 seeds × both baselines).
8. `scores` sums to 0 (within 1e-9) in both modes, for 200 seeded episodes; `score == +1` iff a
   seat took all 91 points / pushed the token off.
9. `overbid` boundary: `margin == 5` emits nothing, `margin == 6` emits exactly one `overbid`
   naming the right seat and the bid it beat.
10. `collusionIndex` is 0 when nobody bid its lowest card into a blow-out, and exactly `k/13` when
    `k` such rounds are constructed.
11. Every variant's and the cert fixture's `game_config` constructs a `Sim` (cogame-collab-cooking
    0.1.1 — a fixture-only test hid a defect that killed every league episode).

**`tests/test_bot.nim` — the scripted baselines (bounded orders / legality).**

12. Over 200 seeded episodes × both modes × both baselines: **every** bid the baseline produces is
    in `legalBids(seat)` at the moment it is produced; no purse goes negative; no card is spent
    twice; the episode always terminates.
13. `match` beats a seeded uniform-random legal bidder over 200 goofspiel episodes (mean score
    > 0), so the fillers are a real opponent rather than noise.
14. `match` and `hoard` disagree on at least 30 % of rounds — two fillers that play the same game
    are one filler.
15. The scripted-only cert fixture (4 seats, 13 rounds, `turnDelayMs = 0`) completes in **under
    50 s** of wall clock, pinning it inside `coworld certify`'s 60 s default (commons-family
    0.1.0).

**`tests/test_replay.nim` — record → re-derive, and the bytes.**

16. For **every** end reason/ending pair — `complete/prizes-exhausted`, `complete/pushout`,
    `complete/coins-exhausted`, `complete/round-cap`, `deadline/wall-clock` — record an episode,
    run `replayMatch` over its events, and assert every frame's `tableStateJson` is identical to
    the live one. A wall-clock stop must re-derive because `settle` is the same proc on both paths
    (particle-worlds `13c66d7`).
17. `replayMatch` raises when a recorded `prize`/`push` disagrees with the seeded re-derivation.
18. **Strict UTF-8**: build an episode whose every `say` and `notes` is a multi-byte string at
    exactly the cap (80 / 400 runes of `日`+emoji), serialise the replay, and assert
    `validateUtf8(bytes) == -1` and that a strict `parseJson` round-trips it. Rune-boundary
    truncation, not byte truncation.
19. The replay payload contains `names`, `policyNames`, `config.seed`, `config.prizeOrder`,
    `config.mode`, every event and `results` — the fields the viewer needs, asserted by key.

**`tests/test_manifest.nim` — packaging invariants, parsed from the template.**

20. `num_agents` is present, a positive integer, and equal to `len(players)` in **both** variants
    and the cert fixture; the fixture's value is 4 (the number `docker_smoke.sh` cross-checks).
21. No `game_config` anywhere contains `tokens`; `config_schema` still requires it; every array
    property in `config_schema` declares `minItems` and `maxItems`.
22. `game.protocols.player`, `game.protocols.global`, `game.docs.readme` and every
    `docs.pages[].content` are `{"type":"text","value":…}` objects; `game.description` exists;
    `game.tags` does not; there is no top-level `version` and no `game.display_name`;
    `game.replay_viewer.bundle == "static-replay-viewer"`; every bundled player's
    `resources.limits.cpu == "1"`; the secret URI namespace equals `game.name`.
23. Every `player_id` in `certification.players` is a declared `player[].id`, and every declared
    `player[].id` occupies at least one certification slot.

**`tools/ci/docker_smoke.sh` (the `docker-smoke` job) — end to end.**

24. Builds the production image, starts one game container and **4** player containers on a
    per-run network with the certification fixture, and asserts: the game exits 0; `results.json`
    is written and validates against `results_schema`; the replay is written and **parses as strict
    JSON**; `SMOKE_SEATS=4` agrees with `certification.game_config.num_agents`; and **every player
    container's exit code is 0** (raid 0.1.4 — cert checks this, the stock starter smoke did not).
    It runs with no `ANTHROPIC_API_KEY`, so the whole scripted path is exercised. The replay is
    copied to `dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.

**`ci.yml` job `wasm-viewer` — the bundle is executed, not merely built.**

25. Asserts `tools/build_replay_viewer.sh` exists and is `os.X_OK`; asserts
    `tools/ci/viewer_smoke.mjs` is present; builds the bundle; asserts `index.html` and a non-empty
    `.wasm` exist. Then, `needs: docker-smoke`, it downloads the `smoke-replay` artifact and runs

    ```
    node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
      --replay dist/smoke/replay.json --timeout 90 --soak 10 --strict-text-bounds
    ```

    against **the replay `docker-smoke` produced** — the only replay in CI known to be current
    bytes. `--soak 10` catches a viewer that loads and then throws mid-playback (cogball 0.1.4);
    the smoke replay is long enough for it: 13 rounds × (`prize` + `reveal` + occasional `overbid`)
    ≈ 29 events at the renderer's ~900 ms dwell ≈ **26 s of playback > 10 s of soak** (ecos,
    2026-08-23 — a replay shorter than the soak reads as frozen). `--strict-text-bounds` requires
    `canvas_text.never_inside == 0`; the board is fixed, so it stays on.

26. **Renderer fixture step** (`tools/ci/renderer_fixture.html`, its own
    `viewer_smoke.mjs --url … --strict-text-bounds` run): CI replays carry **zero LLM text** —
    `docker_smoke.sh` runs without a key and the scripted baselines emit no `say` — so nothing that
    plays a CI replay ever exercises the say band or the feed's quoted lines. The fixture loads the
    **shipped** `dist/static-replay-viewer/index.html` in an iframe, shims only the wasm entry,
    feeds it a synthetic payload with a full-cap 80-rune `say` on every seat and the longest
    plausible policy names, and drives the page's own text path at **360, 640 and 1280 px**
    (particle-worlds `46cf69d` — a fixture that re-implements the drawing gates nothing).

27. **Chrome scope check** (`tools/ci/chrome_scope_check.mjs`, run in the same job): asserts that no
    identifier exported by `client/chrome_common.js` is re-declared as a top-level `function` or
    `var` in `client/renderer.js` (tandem, 2026-08-23), and that `client/chrome_common.js` still
    contains the copied region markers, so a future "tidy-up" that rewrites the chrome fails loudly.

---

## Out of scope (v1)

- **Goofspiel variants**: `imp_info` (limited-information goofspiel, where bids are not revealed —
  it deletes the "no hidden cards" property the idea is built on), `points_order`
  `ascending`/`descending`, `returns_type` `win_loss`/`total_points`, and the discard and
  carry-over tie rules. v1 ships random prize order, point-difference scoring and the split tie.
- **Seat counts other than 4 (goofspiel) and 2 (oshi-zumo).** The 5–10-seat goofspiel the idea
  mentions (and the extra-deck dealing it needs) is a later variant; the sim tolerates 2..10 but no
  manifest variant declares it, so the ladder never schedules it.
- **Oshi-zumo variants**: `min_bid = 0` (unbounded episode length), the `alesp` payment rule, field
  sizes other than `K = 3`, purse sizes other than 20, and asymmetric purses.
- **Cross-variant Elo weighting.** Both variants feed one league and one leaderboard, ranked on
  mean `score`; no per-variant division or handicap in v1.
- **The bid-pattern audit as enforcement.** `collusionIndex` is reported in results and the `end`
  event and is never acted on in-episode: no seat is penalised, no bid is rejected.
- **Human seats, chat between seats, and any inter-seat channel.** Seats never exchange text; `say`
  is spectator-facing only and is not shown to other seats.
- **RL / vector policies.** Policies are prompts or the two named scripted baselines; there is no
  observation tensor and no action-space export.
- **A live spectator theatre beyond `/client/global`**, replay editing, highlight clipping, and any
  replay-viewer pod. Replays are the static wasm bundle, always.
- **Replay protocol migration.** The viewer reads `gozu.replay.v1` and nothing else; a future
  `GameVersion` bump adds a reader, it does not silently reinterpret old bytes.
