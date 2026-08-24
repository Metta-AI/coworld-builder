# Hanabi: four cogs who cannot see their own cards build five fireworks out of hints

Hanabi is forked from **`Metta-AI/cogame-bullwhip`** (read at `/workspace/starters/cogame-bullwhip`,
commit as mounted). Bullwhip is the starter because Hanabi has bullwhip's exact machinery — a fixed
small seat count, a policy that is *just a prompt* answered by the game container, per-seat hidden
information, a pure Nim `sim` module shared by the server, the tests and the wasm replay viewer, and
a `client/chrome.css` that already carries the 360 px scorebug rules the pins require. **Every
convention there holds here unless this note says otherwise.** Where this note says "bullwhip's X",
the builder forks the file at that path in the starter mount and renames the identifiers; where it
says "verbatim", the bytes are copied unchanged. The one structural difference from the starter is
stated up front and repeated where it bites: **bullwhip resolves a week only when all four seats have
ordered (a simultaneous batch of four); Hanabi is strictly turn-based — exactly one seat acts per
turn, so every turn is one model request, never four.**

Source idea, verbatim:

> Port of Hanabi (PettingZoo classic / Hanabi Learning Environment / OpenSpiel / JaxMARL). 2-5 players build five colour-ordered fireworks stacks from a shared deck; you hold your cards facing OUT. Actions: play a card, discard (refunds a hint token), or spend a hint token to tell one player every card of a colour or rank they hold. Three misplays end the game; score = stack heights (max 25). Fully cooperative, partially observed, and the whole skill is the theory of mind around hints — conventions ("finesse", "chop") are the meta.
>
> Seats: 2-5
> Motive: fully cooperative, hidden information
> Policy interface: discrete turn-based actions; LLM prompt is a natural fit (the state is tiny and the reasoning is explicit)
> Fills gap: the canonical ad-hoc teamwork benchmark — no coworld yet scores *reading an unfamiliar partner's conventions*
> Integrity (anti-collusion): cooperative, so the league must be cross-play: seat each champion with scripted/other-team partners (Melting Pot-style resident/visitor) and with its own copies; anonymous aliases; deck seeded.
>
> Replay plan (watchability): spectators see all hands; every hint is annotated with what the receiver can now infer; misplays get a fizzle.
>
> Source: PettingZoo hanabi_v5; github.com/google-deepmind/hanabi-learning-environment; Bard et al. 2019.

---

## The game

### Seats, aliases, shape

- **Seats: exactly 4.** `num_agents` = **4**, in every manifest variant, in the certification
  fixture, and as `<SEATS>` in `tools/ci/docker_smoke.sh`. The idea says "2-5"; 4 is chosen because
  the 4-player deal (hand size **4**) is the standard configuration of the Hanabi Learning
  Environment and of PettingZoo `hanabi_v5`, because four seats is what bullwhip's chrome, its
  `repeat(4, 1fr)` scorebug and its four `soldier_*_front.png` sprites already fit, and because four
  seats give the ad-hoc-teamwork story the most partner mixes per round. A ranged or variable seat
  count is not offered anywhere: the ladder schedules zero episodes when `num_agents` is missing or
  inconsistent.
- **Hand size is 4** (the standard 4- and 5-player deal; 2- and 3-player Hanabi deals 5). It is a
  constant, `HandSize* = 4`, not a config knob.
- **Two name spaces.** In-game every seat is an anonymous cog alias drawn from bullwhip's `CogNames`
  by `tableNames(players, seed)` (`Sprocket`, `Gizmo`, `Ratchet`, `Widget`, …). A seat's prompt,
  every other seat's observation, the move log and the player websocket use aliases only. Real
  policy names live in `results.names` and in the replay's `policyNames`, and are swapped in
  **spectator-side only** by the renderer's `makeNameMap` (kept verbatim, and applied at *every*
  render site — clock, scorebug, endcard, beat labels, feed, hint pane; cogmud 2026-08-24). No
  prompt and no player frame ever contains a policy name.
- **Seat colour** for the chrome is the renderer's `COLORS` order: seat 0 red, 1 blue, 2 green,
  3 yellow. **Card colours are a different palette** (§*Viewer*) and are never called by seat names.

### The deck, the deal, the table

- **Deck: the standard 50 cards.** Five colours — `red`, `yellow`, `green`, `blue`, `white` — each
  with ranks `1 1 1 2 2 3 3 4 4 5` (three 1s, two each of 2/3/4, one 5) = 10 cards per colour.
  Canonical build order is colour-major in that colour order, ranks ascending, then
  `rng.shuffle(deck)` with `var rng = initRand(int64(config.seed) * 7919 + 17)` — the same
  single-stream, seed-derived shuffle bullwhip uses for roles and demand, which the starter already
  proves re-derives identically in the wasm viewer.
- **Deal:** four rounds, seats 0→3, one card each. A dealt card enters at **slot 1**, shifting the
  seat's other cards one slot higher, so after the deal slot 1 is the newest card and slot 4 the
  oldest. 16 cards dealt, **34 left in the deck**.
- **Slots are 1-based, 1..4, left to right, newest at slot 1.** Every prompt, event, frame and feed
  line uses that numbering. When a card leaves slot *k*, the cards in slots 1..*k*−1 shift one slot
  higher and the drawn card (if any) enters slot 1. When the deck is empty no card is drawn and the
  hand shrinks — slots renumber, so a seat late in the game may hold 3, 2 or 1 cards.
- **Fireworks:** five stacks, `fireworks[colour]` ∈ 0..5, all starting at 0.
- **Discard pile:** a multiset of cards, public, always fully visible to every seat.
- **Tokens:** `hintTokens` starts at **8** (max 8), `fuses` starts at **3**. Both are public.
- **Turn order** is fixed: the seat acting on turn *t* (0-based) is `t mod 4`. `pendingSeats(sim)`
  returns exactly one seat — `@[sim.turn mod Seats]` — or the empty seq when the episode is done.
  That single fact is what makes the forked bullwhip loop turn-based (§*Decisions*).

### The three actions

A seat's whole move space, and nothing else:

| Action | Fields | Legal when |
|---|---|---|
| `play` | `slot` 1..handSize | always (any slot the seat holds) |
| `discard` | `slot` 1..handSize | `hintTokens <= 7` (a discard at 8 tokens is **illegal**) |
| `hint` | `target` (seat ≠ self), `hintType` ∈ {`colour`,`rank`}, `hintValue` (a colour name, or a rank 1..5) | `hintTokens >= 1` **and** the hint touches **≥ 1** card in the target's hand (an empty hint is illegal — the HLE/PettingZoo default) |

`legalMoves(sim): seq[Move]` enumerates exactly this set, in a fixed order: every `play` by ascending
slot, every `discard` by ascending slot, then every `hint` by ascending target seat, `colour` before
`rank`, colours in deck order and ranks ascending. **A legal move always exists** — `play 1` is
always legal while the seat holds a card, and a seat always holds ≥ 1 card while the episode runs
(the episode ends the moment the countdown expires, which is before any hand can empty). The same
enumeration is what the prompt shows the model (§*Decisions*) and what the validator accepts: *the
list is the legality rule*, one code path, per the escrow 2026-08-23 learning.

### Turn resolution — the exact numbered order

For turn `t = 0, 1, 2, …`, actor `a = t mod 4`:

1. **Open the turn.** `sim.turn = t`, `sim.actor = a`. Build `a`'s observation (§*Per-seat
   observation*), including the enumerated legal-move list.
2. **Decide.** One model request for seat `a` (or the scripted baseline's move if that seat is
   scripted / the client is disabled). §*Decisions* owns the retry, the fallback and the clock.
3. **Validate.** The proposed move must be an element of `legalMoves(sim)`. Anything else — bad
   JSON, unknown action, out-of-range slot, self-hint, empty hint, discard at 8 tokens — is a
   **rejection**, handled by §*Decisions*, never by mutating the sim.
4. **Apply**, exactly one of:
   - **`hint`**: `hintTokens -= 1`. Every card in the target's hand matching (`hintType`,
     `hintValue`) records **positive** knowledge for that attribute; **every other card in that hand
     records negative knowledge** for that value (in Hanabi a hint marks *all* matching cards, so
     the untouched cards are informative too). The annotation of §*The event record* is computed
     here, before anything else changes.
   - **`play`**: remove the card from `slot`. If `card.rank == fireworks[card.colour] + 1` the stack
     advances (`fireworks[card.colour] = card.rank`, `result = "stack"`); if that rank is **5**, the
     firework is complete and `hintTokens = min(8, hintTokens + 1)` (a refund **only** if below 8).
     Otherwise it is a **misplay**: the card goes to the discard pile, `fuses -= 1`,
     `result = "misplay"`, `fizzle = true`.
   - **`discard`**: remove the card from `slot` to the discard pile;
     `hintTokens = min(8, hintTokens + 1)` (which is always +1 here, since a discard is illegal at 8).
5. **Draw** (play and discard only): if the deck is non-empty, pop its top card into **slot 1**,
   shifting the rest one slot higher, with empty knowledge. If the deck is empty, no draw; the hand
   is one shorter.
6. **Countdown.** If the deck is now empty and `countdown < 0`, arm it: `countdown = Seats` = **4**.
   Else if `countdown > 0`, `countdown -= 1`. (So the seat that drew the last card arms the
   countdown on its own turn, the other three each get one more turn, and then that seat gets one
   more turn — "each player, including the one who drew the last card, takes one final turn", the
   official rule and HLE's behaviour.)
7. **End tests, in this order.** (a) `fuses == 0` → end, `endReason = "strikeout"`. (b)
   `Σ fireworks == 25` → end, `endReason = "perfect"`. (c) `countdown == 0` → end,
   `endReason = "deckout"`. (d) `t + 1 == config.maxTurns` → end, `endReason = "turnlimit"`.
8. **Log.** Append the `move` event (§*The event record*), recompute every seat's derived knowledge,
   broadcast, then `t += 1` and go to 1 — unless step 7 ended the episode, in which case
   `settle(...)` writes the `end` event.

Every quantity is an integer; there is no floating point, no hash-table iteration order and no
wall-clock input anywhere in the sim, so the episode is a pure function of (seed, config, move
sequence) and the wasm viewer re-derives it exactly.

### Knowledge: what a seat can prove about its own cards

Each card carries, per holder:

- `hintColour` (a colour or none) and `hintRank` (1..5 or none) — **positive** hints received;
- `negColours` and `negRanks` — **negative** information from hints that touched other cards;
- `hintedTurn` — the turn of the most recent hint that touched it (−1 if never touched).

From those the sim derives, for every card, a **candidate set**:

```
candidates(card) = { (c, r) :  (hintColour is none or c == hintColour)
                            and (hintRank   is none or r == hintRank)
                            and c not in negColours and r not in negRanks
                            and remainingCopies(c, r) > 0 }
```

`remainingCopies(c, r)` counts the copies of (c, r) that the holder cannot see: total copies minus
those on the fireworks, in the discard pile, in the *other* seats' hands, and in the holder's own
hand where a card's candidate set is already a **singleton by hints alone**. This is **one pass, no
fixpoint** — no multi-card constraint propagation, no reasoning about what a partner would have
hinted. That boundary is deliberate and is repeated in §*Out of scope (v1)*.

Two predicates fall out and are used by the baselines, the prompt and the annotation:

- **`knownPlayable(card)`** — every candidate is playable *right now*
  (`fireworks[c] + 1 == r` for all candidates).
- **`knownDead(card)`** — every candidate is dead: `fireworks[c] >= r` (already played), or some rank
  `q` with `fireworks[c] < q < r` has **all** its copies in the discard pile (unreachable, so nothing
  above it can ever be played).
- **`critical(card)`** (a table fact, computed on the true identity, used only for the spectator
  annotation and by the scripted baselines, which see only what a player sees of *other* hands):
  its last remaining copy, i.e. `remainingCopies == 1` counted over the whole table, and not dead.

**Chop** = the highest-numbered slot with **no** positive hint of either kind; if every slot carries
a positive hint, the chop is the highest-numbered slot whose card is `knownDead`, and failing that
the highest-numbered slot. The chop is a derived quantity, shown to the seat and drawn in the viewer;
it is *not* a rule — nothing forces a seat to discard it.

### Scoring — cooperative, higher is better

```
score = fireworks[red] + fireworks[yellow] + fireworks[green] + fireworks[blue] + fireworks[white]
        ∈ 0 .. 25
results.scores[s] = score          # the SAME number for all four seats
```

**Higher is better.** The score is the sum of the stack heights at the moment the episode ends,
**including after a strikeout** — the idea pins "Three misplays end the game; score = stack heights
(max 25)", and zeroing a strikeout (the original tabletop rule, and one HLE variant) would collapse a
whole band of episodes to a single value and destroy the league's ranking signal. A strikeout is
punished plenty by ending the game early.

**The league ranks by the mean of `results.scores[seat]` over episodes** (division leaderboard; Elo
1000/32 on top). **Say this out loud in the run's verification, because it is a known trap:** a fully
cooperative game gives every seat the same score, so head-to-head **Elo never separates the two
champions** — they will sit at 1000.0 forever (cogame-raid learning 5, 2026-08-23). What separates
them is the *mean team score across episodes*, which differs because each champion plays different
deals and different partner mixes (the round-robin seats each champion with the scripted fillers, with
the other champion, and with copies of itself — exactly the resident/visitor cross-play the idea
asks for). Phase 60 should judge check 2 on the division leaderboard's `score`/`rounds_played`
columns, not on Elo spread, and the manifest description says so too.

`results.contributions[s]` (cards this seat banked on a stack, minus its misplays) is reported for
display and endcard ordering **only**. It is never summed into `scores` and never shown as a
ranking: paying a seat for its own plays is exactly the incentive that breaks Hanabi.

### End conditions and `results.reason`

Episode-level ending, `results.reason`, has **exactly two legal values**:

- `"complete"` — the game reached a terminal state under the rules (step 7 of the resolution order).
  Which one is reported separately in `results.endReason` ∈ `"perfect"` | `"strikeout"` |
  `"deckout"` | `"turnlimit"`.
- `"deadline"` — the episode clock stopped play **between turns** (§*Decisions*). The score is the
  stacks as they stand; `results.endReason` is `"deadline"` in that case too, so the two fields are
  never contradictory.

Those are the only strings either field can hold; `tests/test_replay.nim` asserts no other value is
producible. If the deadline fires before any turn has been played (only possible if the connect wait
ate the budget) the server plays out the whole episode with all four seats on the `conventions`
baseline — no LLM, ~5 ms — so the replay is never empty, then settles with `reason = "deadline"`.

`config.maxTurns` defaults to **80** (range 20..120; certification fixture 24). The arithmetic: a
4-player episode can take at most `plays + discards ≤ 34 (deck draws) + 4 (final round) = 38` card
turns, and at most `8 + 38 + 5 = 51` hint turns (the initial tokens plus every possible refund), so
**89 turns is the hard theoretical ceiling**. 80 truncates only a game that has already spent ≥ 42
turns on hints, and when it does the truncation is visible as `endReason = "turnlimit"` rather than
being scored as a normal ending.

### Per-seat observation — what is visible, what is hidden

The acting seat's observation (identical in content to its LLM prompt and to its player-socket
`state` frame) carries, and carries **only**:

- The rules, its own alias, its seat index, the turn number and `maxTurns`, whose turn it is.
- **The other three seats' hands, face up**, in slot order, each card as `red 3` plus that holder's
  own knowledge of it (`hinted: colour red`, `not: rank 1,2`, `chop`) — this is exactly what a human
  sees across the table, including how much the partner knows.
- **Its own hand as knowledge only**: per slot, positive hints, negative information, the candidate
  set (listed if ≤ 6 candidates, otherwise counted), `knownPlayable` / `knownDead` flags, `chop`,
  and the turn it was last touched. **Never the identities.**
- Fireworks (five heights), the discard pile grouped as `red 1 ×2, white 4 ×1, …`, `hintTokens`,
  `fuses`, cards left in the deck, and the endgame countdown when armed.
- **The complete public move log**, one line per turn since turn 0 — every hint (giver, receiver,
  type, value, the slots it touched) and every play/discard with the **revealed identity** of the
  card and its outcome. This is public at a real table and it is ≤ 80 lines, so it is included whole,
  never summarised.
- **`LEGAL MOVES`** — every legal move, numbered, each printed as the exact JSON object to copy.
- Its own **private notes** from earlier turns (≤ 400 runes), verbatim.
- The operator block: this seat's `PLAYER_PROMPT`.

**Hidden from every seat, always:** the identities of its own cards; the deck (order *and* contents
beyond what card-counting gives); every other seat's notes and `banner`; the mapping alias → policy
name; the seed. There is no code path that puts any of those into a prompt or into a player frame,
and `tests/test_prompt.nim` asserts it against a crafted fixture. **There is no chat channel** — a
seat's only way to say anything to another seat is a legal hint. `banner` (§*Decisions*) is
spectator-only for exactly this reason: it must never become a side channel around the hint economy.

Decisions are made **inside the game container**, so the open `/global` spectator socket (which does
carry every hand, for the viewer) cannot leak into any policy's reasoning even if a player container
were to connect to it — the player container never decides anything.

### Deliberate deviations from the reference implementations

| PettingZoo `hanabi_v5` / HLE | This coworld | Why |
|---|---|---|
| 2–5 players, hand size 4 or 5, configurable | 4 players, hand size 4, fixed | `num_agents` must be a single number in every variant; 4 is the canonical HLE-Full config |
| Vector/one-hot observation, discrete action index | Natural-language observation with an enumerated legal-move list, JSON action | The policy is an LLM prompt; enumerating legality is what took escrow's fallbacks to zero |
| `Score()` returns 0 when life tokens run out (strict variant) | Score is the stack heights whatever the ending | Pinned by the idea; keeps the league's signal dense |
| No turn cap | `maxTurns` cap (default 80), reported as `turnlimit` | Bounds the episode clock and the replay length; above the practical maximum |
| Optional rainbow/6th colour, "life token" variants | Five colours, 8 hint tokens, 3 fuses, nothing else | v1 scope |

---

## Decisions: LLM with scripted fallback

Transport, credentials, the JSON-only output contract, `extractJsonObject`, the Bedrock candidate
list, the `output_config.effort` guard and "no credentials ⇒ every seat scripted" are ported from
bullwhip `src/bullwhip/llm.nim` unchanged in structure. The mount already carries the family fix of
2026-08-23 (`newLlmClient` logs the Bedrock model actually invoked; the entrypoint banner prints no
`model=`; `config.model` is documented as direct-Anthropic-only) — keep all of it. **One deletion:**
drop `us.anthropic.claude-sonnet-4-6` from `bedrockModelIds()`, leaving
`us.anthropic.claude-haiku-4-5-20251001-v1:0` then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
that candidate times out on every hosted sidecar call and turns one throttle into a fallback cascade
(cogame-raid, 2026-08-23).

### One request per turn — sequential by rule, not by batch

Hanabi is **turn-based**: seat `t mod 4` acts alone, and its observation depends on the move made on
turn `t − 1`, so the decisions cannot be batched. The starter's batching code is nonetheless kept
**unchanged**: `pendingSeats(sim)` returns a one-element seq, so
`decideAll(client, sim, seats, prompts, scripted)` issues `curly.makeRequests` with a **batch of
one** and the retry path, the parsing and the fallback are bullwhip's code on a shorter list. The
loop is therefore: one turn, one model request (two if the first reply is rejected), one applied
move.

- **Attempt 0:** one request for the acting seat, unless that seat is `PLAYER_SCRIPTED` or the client
  is disabled (then the baseline move, no network, no wait).
- The reply is normalised, parsed, capped and **checked against `legalMoves`**. A reply that fails to
  parse, or is not a legal move, or is missing `action`, is re-opened.
- **Attempt 1:** the same request with the failure appended verbatim to the user prompt —
  `Your previous reply was rejected: <reason, ≤ 200 chars>. Reply with ONLY one JSON object copied
  from the LEGAL MOVES list.` The reason is specific (`"discard is illegal at 8 hint tokens"`,
  `"a hint must touch at least one card: Widget holds no green"`), never a scolding.
- **Still failing ⇒ scripted fallback:** the seat plays the **`conventions`** baseline's move for
  this position, the `move` event records `origin = "fallback"` with the rejection text, the feed
  says so, and `results.fallbacks[s]` counts it. The episode always advances.

### Timing arithmetic, out loud

`PlayBudgetFraction = 0.6` of the assumed `episodeTimeoutSeconds` = 1200 ⇒ **720 s** of play,
measured from process start exactly as bullwhip does (the game container never receives
`COWORLD_TIMEOUT_SECONDS`). Per turn:

```
typical turn = 1 haiku request on a ~1.4k-token prompt   ~4.0 s
             + apply + broadcast                          ~0.01 s
             + turnDelayMs (150 ms standard, 0 in cert)    0.15 s
             = ~4.2 s
80 turns     = ~336 s          of 720 s          (47 % of the play budget)

worst turn   = attempt 0 (llmTimeoutSeconds = 20)
             + attempt 1 (20)
             + request spacing floor (2)
             + apply/broadcast/pacing (0.4)
             = 42.4 s   ->   TurnReserveSeconds = 45
```

`TurnReserveSeconds = 45` is checked **before every turn's decision**: if
`now + 45 > playDeadline`, the sim settles with `reason = "deadline"` and the stacks as they stand.
Play therefore never crosses 720 s even in the pathological case where every single request times out
and retries — that case simply produces a short episode (≈ 12–16 turns after a full 180 s connect
wait) with a valid replay, instead of an episode the platform discards. `llmTimeoutSeconds` defaults
to **20** here rather than bullwhip's 60 precisely because turns are sequential: a 60 s timeout on 80
sequential turns has no honest worst case.

**Rate-limit floor.** The hosted Bedrock sidecar caps **30 requests/minute per episode** and a
throttle cascades (raid). A turn is 1 request (2 with a retry), so the server enforces
`MinRequestSpacingSeconds = 2.0` between the **starts** of consecutive model requests: at most 30
requests a minute by construction, whatever the latency. With ~4 s replies the floor never binds.

### Reply schema and caps

Canonical reply — one flat JSON object, copied from the `LEGAL MOVES` list and optionally extended
with `note`/`banner`:

```json
{"action": "hint", "target": 2, "hintType": "rank", "hintValue": "3",
 "note": "Ratchet's slot 1 is a red 1; I am holding their chop for now",
 "banner": "telling Widget about 3s so the green 3 gets banked"}
{"action": "play", "slot": 1, "note": "…", "banner": "…"}
{"action": "discard", "slot": 4, "note": "…", "banner": "…"}
```

| Field | Type | Cap | Truncation |
|---|---|---|---|
| `action` | string, one of `play` / `discard` / `hint` | ≤ **12 runes** before matching, case-insensitive | rune boundary, then enum match; no match ⇒ rejection |
| `slot` | integer 1..handSize (`play`/`discard`) | — | out of range ⇒ rejection |
| `target` | integer seat 0..3, **or** an alias string (case-insensitive) | ≤ **24 runes** as a string | rune boundary, then alias match |
| `hintType` | `colour` / `color` / `rank` / `number` | ≤ **8 runes** | rune boundary |
| `hintValue` | colour name or first letter (`red`/`r`/…), or rank as int or numeric string | ≤ **8 runes** | rune boundary |
| `note` | string, **private to this seat**, fed back verbatim next turn | ≤ **400 runes** | rune boundary (`runeSubStr`), `…` marker |
| `banner` | string, **spectator-only**, never read by any seat | ≤ **80 runes**, newlines → spaces | rune boundary, `…` marker |

Every string that reaches the replay is cut on **rune** boundaries by bullwhip's `cleanText`: a byte
cut through a multi-byte character produces replay bytes that render in a browser and fail a strict
JSON parser (`tests/test_replay.nim` covers it with a 700-`é` note).

**Normalisation before parsing** (escrow 2026-08-23; cogmud 2026-08-24): strip a leading/trailing
markdown fence, drop a leading UTF-8 BOM, and take the **first balanced `{…}` object** so a valid
object followed by a sentence of prose parses (Nim's `parseJson` alone raises "EOF expected" on
trailing prose and would burn the retry). Also accepted, and normalised into the canonical shape
before validation:

- `{"move": "play 2"}`, `{"move": "discard 4"}`, `{"move": "hint 2 red"}`, `{"move": "hint 2 3"}` —
  a single string in the printed short form;
- `{"action": "hint", "target": "Widget", "hint": "red"}` — `hint` as an alias for
  `hintType`+`hintValue` inferred from the value's shape (a numeral ⇒ rank, otherwise colour);
- `"colour"`/`"color"` and `"rank"`/`"number"` spellings, and 1-based slots given as strings.

Anything else is a rejection and goes to the single retry.

### Prompts

`systemPrompt(sim, seat)` (fixed text, ~850 tokens): who you are (alias, seat index, turn order), the
complete rules of §*The game* — deck composition, hand size, slot numbering with newest at slot 1,
the three actions and their legality, the 8/3 tokens, refunds, the deck-out countdown, the end
conditions, the score and its sign — an explicit statement that **you cannot see your own cards and
your partners can, and that the only channel between you is a hint**, and:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }. Copy one entry from the LEGAL MOVES list exactly, and you may add "note" (at most
> 400 characters, private to you, you will see it again next turn) and "banner" (at most 80
> characters, shown to spectators only — your partners never see it).

The system prompt teaches **no convention**. It states the mechanics and stops. Reading an unfamiliar
partner's convention is the thing being measured, so baking H-group conventions into the shared
prompt would measure nothing; conventions belong in a *policy's* `PLAYER_PROMPT`.

`userPrompt(sim, seat, prompt)`, in this order: the turn header (`Turn 23 of 80 — your move.
Score 11/25, hints 5/8, fuses 2/3, deck 17`), the fireworks line, the discard pile, the three
partners' hands with their knowledge, **your own hand as knowledge only**, the full public move log,
your notes, `operatorBlock(prompt)` (bullwhip's wording), the numbered `LEGAL MOVES` block, then the
one-line format reminder with the caps.

**Champion prompts** (phase 40 `tools/ci/policies.json`; both champions are `PLAYER_PROMPT`, never
scripted):

- **`hanabi-signaler`** (champion #1, daveey) — "Play a clear, declarable convention and stick to it
  so a stranger can decode you. Treat the newest card a hint touches as the card you are being told
  to play, and treat a hint that touches only the partner's oldest unhinted card as 'that card is
  precious, do not discard it'. Give play hints when a partner has a card that goes on a stack now;
  prefer the partner who acts next. Discard your own oldest unhinted card when you have nothing to
  play and nothing worth hinting. Never spend the last hint token on information a partner already
  has, and never play a card unless every possibility you hold for it is playable right now. Use your
  note to record, in one line per partner, what you have told them and what you believe they hold."
- **`hanabi-reader`** (champion #2, daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`)
  — "Assume nothing about your partners' conventions and infer them from the log. Every turn, before
  you move, ask what the previous hint would have meant if the giver expected you to play, to save,
  or merely to know; then check what your partners actually did after earlier hints and prefer the
  reading their behaviour supports. Only play a card when every candidate you hold for it is
  playable; otherwise buy information or discard your oldest unhinted card. Count the discard pile —
  a card whose last copy is still in a hand must never be discarded, and a card whose predecessors are
  all discarded is worthless. Write down in your note the rule you think each partner is following,
  and change it the moment they contradict it."

### Scripted baselines (`PLAYER_SCRIPTED`) — no LLM, same image

Two baselines, both fieldable policies and both filler policies for the league;
`parseScriptKind` maps `"1"/"true"/"yes"/"conventions"/"convention"` → `skConventions`,
`"cautious"/"careful"` → `skCautious`, anything else → `skNone`. A scripted seat never calls the
model. **`conventions` is also the fallback move** for a failed LLM decision, and the move every seat
plays when there are no credentials at all (the offline-certification path, which is load-bearing).

**`conventions`** — the strong, convention-following partner a prompt has to beat. Its move is the
first rule that fires:

1. **Play** the lowest-numbered slot that is `knownPlayable`.
2. **Save**: if `hintTokens >= 1` and the **next seat to act** has a `critical` card on its **chop**,
   hint that card's **rank** to that seat (a rank hint always touches it, and a 5 is the canonical
   save).
3. **Play-hint**: if `hintTokens >= 1`, evaluate every legal hint and take the one that makes the
   most of the receiver's cards **newly** `knownPlayable`; require ≥ 1. Ties break by: the seat
   acting soonest, then `rank` before `colour`, then lower rank / earlier colour in deck order, then
   lower seat index.
4. **Discard** the chop, if `hintTokens <= 7`. (Prefer a `knownDead` slot when one exists — the chop
   definition already does this.)
5. **Stall hint** (only reachable at `hintTokens == 8` with nothing playable and no useful hint):
   the legal hint touching the fewest cards of the next seat to act; same tie-breaks.
6. `play 1` — unreachable, kept so the function is total.

**`cautious`** — a deliberately simpler partner, the "unfamiliar teammate" of the cross-play story.
It never misplays:

1. **Play** the lowest slot whose candidate set is a **singleton** and playable.
2. **Hint** (if `hintTokens >= 1`) the **rank** of a currently-playable card that carries no positive
   hint at all, preferring the next seat to act, then the lowest slot.
3. **Discard** the chop, if `hintTokens <= 7`.
4. **Stall hint**: the rank of the next seat's highest-numbered slot.

Both are pure functions of the sim and the acting seat, both are deterministic, and neither ever
proposes a move outside `legalMoves` — asserted for 200 seeded episodes in `tests/test_bot.nim`.

### Degrade, never hang

| Failure | Behaviour |
|---|---|
| Model reply times out (`llmTimeoutSeconds` 20), 4xx/5xx, refusal, or `max_tokens` before any `{` | attempt 1 → `conventions` fallback move |
| Reply parses but is not in `legalMoves` | same, with the specific illegality quoted in the retry prompt |
| No LLM credentials (`client.disabled`) | every seat plays its `PLAYER_SCRIPTED` baseline, or `conventions`; the whole 80-turn episode runs in ~5 ms (offline certification and `docker_smoke.sh`) |
| Auth 401/403 | `client.disabled = true`; every remaining turn scripted |
| Bedrock throttle 429 / "Model access is denied" | rotate to the next candidate model, retry on the next turn |
| A misplay, a strikeout, a wasted hint | *not* a failure — it is the game; recorded, drawn, scored |
| `now + 45 s > playDeadline` before a decision | `sim.endEarly()`, `reason = "deadline"`, artifacts written immediately |
| A turn's sim work runs long | impossible: applying a move is O(20) integer operations with no IO |
| Player socket dies / a player pod never connects | the connect wait is bounded at `player_connect_timeout_seconds` (180) and play starts regardless; a seat with no delivered prompt plays with an empty operator block |

---

## Sim module

Files (a fork of the bullwhip tree, same layout):

- `src/hanabi/types.nim` — `HanabiError`, `PlayerConfig`, `GameConfig`, `Card`, `Move`, `EventKind`,
  `GameEvent`, `SeatStat`, `defaultGameConfig()`, `update(config, json)`.
- `src/hanabi/sim.nim` — the rules and the episode state machine. Pure, no IO. Server, tests and the
  wasm viewer drive this module and nothing else.
- `src/hanabi/llm.nim` — prompts, the one-request-per-turn decision path, parsing/normalisation, and
  the two scripted baselines.
- `src/hanabi/server.nim`, `src/hanabi.nim`, `src/hanabi_player.nim` — §*Server*.

### `sim.nim`

```nim
const
  Seats* = 4
  HandSize* = 4
  Colours* = 5
  DeckSize* = 50
  ColourNames* = ["red", "yellow", "green", "blue", "white"]
  RankCounts* = [3, 2, 2, 2, 1]        ## copies of rank 1..5 per colour
  MaxHintTokens* = 8
  MaxFuses* = 3
  MinTurns* = 20
  MaxTurnsCap* = 120
  MaxNoteLen* = 400
  MaxBannerLen* = 80
  MaxLearnedLines* = 6
  MaxLearnedLen* = 90
  PacingBudgetMs* = 20_000
  CogNames* = [ ... ]                  ## bullwhip's list, verbatim

type
  Card* = object
    colour*, rank*: int                ## 0..4, 1..5; rank 0 = "no card"
  HeldCard* = object
    card*: Card
    hintColour*, hintRank*: int        ## -1 / 0 = none
    negColours*, negRanks*: set[uint8]
    hintedTurn*: int
  Hand* = object
    cards*: array[HandSize, HeldCard]
    size*: int
  ActionKind* = enum akPlay = "play", akDiscard = "discard", akHint = "hint"
  HintKind* = enum hkColour = "colour", hkRank = "rank"
  Move* = object
    kind*: ActionKind
    slot*: int                         ## 1-based, play/discard
    target*: int                       ## hint
    hintKind*: HintKind
    value*: int                        ## colour index or rank
  Phase* = enum phTurn = "turn", phDone = "done"
  SeatStat* = object
    plays*, misplays*, discards*, hints*, fallbacks*: int
  Sim* = object
    config*: GameConfig
    names*: seq[string]                ## anonymous aliases per seat
    deck*: seq[Card]                   ## index 0 = next to draw
    hands*: array[Seats, Hand]
    fireworks*: array[Colours, int]
    discards*: seq[Card]
    hintTokens*, fuses*: int
    turn*, actor*, countdown*: int     ## countdown -1 until the deck empties
    notes*: array[Seats, string]
    banners*: array[Seats, string]
    stat*: array[Seats, SeatStat]
    lastMove*: GameEvent               ## the move this state was produced by
    phase*: Phase
    done*: bool
    reason*: string                    ## "complete" | "deadline"
    endReason*: string                 ## perfect|strikeout|deckout|turnlimit|deadline
    events*: seq[GameEvent]
```

API — the whole surface the server, the tests and the wasm module use:

`initSim(config)`, `sampleEpisode(config)` (clamps `maxTurns` into `MinTurns..MaxTurnsCap` and fits
`turnDelayMs <= PacingBudgetMs div maxTurns`; idempotent via `config.sampled`),
`tableNames(players, seed)`, `pendingSeats(sim)` (one seat or none), `legalMoves(sim): seq[Move]`,
`applyMove(sim, seat, move, note, banner, origin)` (validates, applies steps 4–8 of the resolution
order, logs the `move` event and settles when a terminal condition fires), `endEarly(sim)`,
`score(sim)`, `candidates(sim, seat, slot)`, `knownPlayable`/`knownDead`/`chopSlot`,
`annotate(sim, move)` (the hint annotation, computed *before* the move mutates anything),
`seatObservation(sim, seat): string` (the exact text the prompt and the player frame share),
`resultsJson(sim)`, `frameJson(sim)`, `replayMatch(config, events)`, `eventToJson`/`eventFromJson`,
`digest(sim)` (FNV-1a 64 over fireworks, discards, tokens, fuses, turn and every hand, hex).

### The event record (what the replay carries)

Flat `GameEvent`, JSON via `eventToJson`/`eventFromJson`, exactly **three** kinds:

| kind | fields |
|---|---|
| `start` | `text` = `"hanabi"`, `seed`, `seats` = 4, `handSize` = 4, `maxTurns`; opens the log |
| `move` | see below |
| `end` | `turn` = turns played, `text` = `"complete"` \| `"deadline"`, `endReason`, `score`, `fireworks` (5 ints), `digest` |

The `move` event, one per turn:

```json
{"kind":"move","turn":23,"seat":2,"action":"hint",
 "target":3,"hintType":"rank","hintValue":"3","touched":[1,3],"untouched":[2,4],
 "slot":0,"card":null,"result":"hint","fizzle":false,
 "learned":["Widget slot 1 is a 3 (candidates: red 3, green 3)",
            "Widget slot 3 is a 3 (candidates: blue 3, white 3)",
            "Widget slots 2 and 4 are not 3s"],
 "nowPlayable":[1],"nowDead":[],"nowCritical":[3],
 "hintTokens":4,"fuses":2,"deck":17,"countdown":-1,"score":11,
 "origin":"llm","scripted":false,"text":"…the seat's note after this reply…","banner":"…"}
```

- `action` ∈ `play` | `discard` | `hint`; `origin` ∈ `llm` | `retry` | `fallback` | `scripted`
  (`scripted` is the boolean the chrome already reads, kept for the starter's feed code).
- For `play`: `slot`, `card` = `{"colour":"red","rank":3}` (the identity, now public),
  `result` ∈ `stack` | `misplay`, `fizzle` = true on a misplay, `learned` carries one line — e.g.
  `"the last white 4 — white can never pass 3"` — when the played/discarded card was the last copy of
  its kind or completes a firework.
- For `discard`: `slot`, `card`, `result` = `discarded`.
- For `hint`: `target`, `hintType`, `hintValue`, `touched`/`untouched` slot arrays, and the
  **annotation**: `learned` (≤ 6 lines, each ≤ 90 runes, one per touched slot plus one negative-info
  line), `nowPlayable` (slots whose candidate set became entirely playable and was not before),
  `nowDead` (became entirely dead), `nowCritical` (became a known single card that is the last copy).
  All four are computed by `annotate()` from the knowledge model of §*The game*, and
  `tests/test_replay.nim` asserts the re-derived annotation equals the recorded one.

**The per-turn state is not stored as events — it is re-derived.** `replayMatch(config, events)`
rebuilds the deck from the recorded `seed`, deals, and replays each `move` through the same
`sim.nim`, producing one `Sim` per event prefix (`frames[i]` = the state after `events[0..<i]`),
exactly as bullwhip re-derives its weeks. The recomputed `digest` must equal the one in the `end`
event; a mismatch raises, which the wasm module reports as `data-replay-error` instead of silently
drawing a different game.

The replay bytes are therefore **self-sufficient**: aliases, policy names, the full config **including
the seed**, every move with its revealed card and its annotation, every note and banner, and the
results — everything the viewer needs, with no server contacted except S3 for the `.replay` file.

### The frame the viewer reads

`frameJson(sim)` — one object per timeline position (`frames.len == events.len + 1`):

```json
{"seats":[{"name":"Sprocket","seat":0,"color":0,"acting":false,
           "hand":[{"colour":"red","rank":3,"hintColour":"red","hintRank":0,
                    "negColours":["blue"],"negRanks":[1,2],
                    "knownPlayable":false,"knownDead":false,"chop":false,
                    "candidates":4,"hintedTurn":19}, x handSize],
           "plays":3,"misplays":1,"discards":2,"hints":4,"contribution":2,
           "banner":"telling Widget about 3s","origin":"llm","fallbacks":0}, x4],
 "fireworks":[2,0,5,1,3],
 "discards":[{"colour":"red","rank":1,"count":2}, …],
 "hintTokens":5,"maxHintTokens":8,"fuses":2,"maxFuses":3,
 "deck":17,"countdown":-1,"turn":23,"maxTurns":80,"actor":3,"score":11,
 "move":{ …the move event that produced this state, or null on frame 0… },
 "log":["Ratchet tells Widget about 3s (slots 1, 3) — Widget can now play slot 1"],
 "phase":"turn|done","gameDone":false,"reason":"","endReason":""}
```

Fireworks are indexed by the deck's colour order (`red, yellow, green, blue, white`). Frames are
small (four hands of four cards) — an 80-turn episode is ~180 KB of replay, so there is **no
keyframe/delta scheme**: every frame is complete.

`resultsJson` (platform-facing, **policy** names):

```json
{"names":[4],"scores":[4 numbers, all equal, 0..25],"score":11,
 "fireworks":[5 ints],"contributions":[4],"plays":[4],"misplays":[4],
 "discards":[4],"hints":[4],"fallbacks":[4],
 "turns":<played>,"maxTurns":80,"deckLeft":17,
 "endReason":"perfect|strikeout|deckout|turnlimit|deadline",
 "reason":"complete|deadline"}
```

Replay payload (`hanabi.replay.v1`), written by the server:

```json
{"protocol":"hanabi.replay.v1","names":[aliases],"policyNames":[policy names],
 "config":{"maxTurns":80,"seed":123456,"sampled":true},
 "events":[…],"results":{…}}
```

Replay mode and the wasm viewer add `"frames"`.

---

## Server, player, protocol

`src/hanabi/server.nim` is bullwhip's `server.nim` with the game loop replaced. Routes, exactly
(bullwhip's set, renamed; every one registered **before** any catch-all asset route, because hosted
certification probes `/healthz`, `GET /client/player?slot=0&token=<t>`, a bad-token player websocket
and `GET /client/global` *before* player pods start — lantern 0.1.1):

```
GET /healthz                     GET /client/global    GET /client/player
GET /client/replay               GET /client/renderer.js
GET /client/chrome.css           GET /client/assets/@name
WS  /player?slot=N&token=T       WS  /global           WS  /replay   (replay mode)
```

Neither `/client/` page opens the player socket. After artifacts are written the server keeps
`/healthz` and `/global` answering for `shutdownGraceSeconds` = **20** and then `quit(0)` — the
certifier pings `/global` with a 2 s deadline *after* the pods start, and a fast scripted episode had
already exited (lantern 0.1.3 → 0.1.4). Bullwhip's `finishEpisode` quits immediately; add the grace.

**Loop** (one iteration per turn):

1. Wait up to `player_connect_timeout_seconds` (180) for all four player sockets; start regardless.
2. If `sim.done`, leave the loop. If `now + TurnReserveSeconds(45) > playDeadline` ⇒ `endEarly()`,
   broadcast, leave the loop.
3. Under the lock: `seats = pendingSeats(sim)` (exactly one), snapshot the sim, copy the prompts and
   the scripted kinds; release the lock.
4. Outside the lock: `decideAll(client, snapshot, seats, prompts, scripted)` — one request, one
   retry, then the `conventions` fallback. Only this thread mutates the sim, so the snapshot cannot
   go stale.
5. Under the lock: `applyMove(...)` for the acting seat (a rejected move never reaches here — the
   decision path already validated against `legalMoves`; `applyMove` still raises `HanabiError` on
   anything illegal and the server catches it and substitutes the baseline move, so the invariant is
   enforced twice). Broadcast.
6. Sleep `turnDelayMs` (bounded by `PacingBudgetMs`) and honour `MinRequestSpacingSeconds`.
7. On `sim.done`: send the `final` frame to the player sockets **before** writing artifacts (the
   hosted worker tears player pods down as soon as `results.json` exists), then write results and the
   replay with `writeArtifact`, then the shutdown grace, then `quit(0)`.

**Live spectator broadcast** (`/global`): the full snapshot after **every** move — 80 frames an
episode is nothing.

**Player protocol `hanabi.player.v1`** — bullwhip's frame shapes, renamed:

- game → player: `{"type":"welcome","protocol":"hanabi.player.v1","slot":N,"name":alias,"seats":4,
  "handSize":4,"maxTurns":80}`;
  `{"type":"state","slot":N,"name":alias,"yourTurn":bool,"turn":int,"maxTurns":int,
  "observation":"<the seat's observation text, §The game>","score":int,"hintTokens":int,
  "fuses":int,"deck":int,"started":bool,"done":bool,"reason":str}` after every event, **redacted to
  that seat**: its own hand appears as knowledge only, never as identities, and no other seat's note
  or banner and no policy name appears;
  `{"type":"final","done":true,"slot":N,"scores":[4],"score":int,"fireworks":[5],"names":[aliases],
  "turns":int,"endReason":str,"reason":str}` at the end, after which the player exits.
- player → game: `{"type":"prompt","prompt":"<≤ 4000 runes>","scripted":"conventions|cautious|"}`,
  sent on connect and again after `welcome`.

`src/hanabi_player.nim` is bullwhip's player with a Hanabi default prompt and **one fix that is
latent in the starter** (raid 0.1.3 → 0.1.4): the receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket, because whisky's `receiveMessage` *raises*
on a close frame and mummy's `send` only queues, so the game's `quit(0)` can outrun the flushed
`final` frame and kill the player container with status 1.

`src/hanabi.nim` is bullwhip's entrypoint: read the runtime config, randomise the seed when it is not
pinned (so the deal is not precomputable), `sampleEpisode` **after** the seed is settled, and echo a
banner with `seats=4 maxTurns=… seed=…` — **no `model=`** (the 2026-08-23 family fix).

---

## Viewer

### The four viewer files — one starter, no splicing

**All four viewer files come from one starter, `Metta-AI/cogame-bullwhip`, and only from it:**

- `replay-viewer/config.nims` — bullwhip's, with the output name and `EXPORT_NAME` renamed;
- the wasm entry `replay-viewer/hanabi_replay.nim` — a fork of `replay-viewer/bullwhip_replay.nim`;
- `replay-viewer/static_replay.js` — bullwhip's shell;
- `replay-viewer/index.html` — bullwhip's page.

Nothing is spliced in from another starter — not from babel, not from parley, not from ctf, not from
moba, not from factorio. Bullwhip's emscripten link flags stay exactly as they are (`-O2`,
`ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`, `MODULARIZE=1`,
`EXPORTED_RUNTIME_METHODS=HEAPU8`, `emscripten_exit_with_live_runtime()`), with exactly these
renames: `EXPORT_NAME=HanabiReplayModule`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_hb_load_replay,_hb_payload_ptr,_hb_payload_len,_hb_error_ptr,_hb_error_len`,
output `dist/hanabi_replay.js`. `static_replay.js` keeps calling the module through that same
`HanabiReplayModule()` factory and those same `_hb_*` exports. (cogame-lantern, 2026-08-23: one
starter's shell on another starter's link flags deadlocks silently with every asset returning 200 —
that is why the four files must share one lineage.)

**Load signalling.** `client/renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame** —
bullwhip already does this at the end of `attachReplay`'s `makeRenderer` callback
(`client/renderer.js:1390`, after the first `renderer.draw`), kept verbatim. On any failure (missing
`?replay=`, the 20 s fetch timeout, a non-200, a wasm rejection including a digest mismatch)
`static_replay.js` sets `document.documentElement.setAttribute("data-replay-error", <message>)`,
shows the Retry button and posts the `coworld-replay` `error` envelope; a successful retry removes
the attribute. `tools/ci/viewer_smoke.mjs` reads exactly these two signals.

**One deliberate change to the starter's shell** (chorus `3c11c953`, 2026-08-24): bullwhip's
`start()` posts `tell("ready")` two animation frames after `attachReplay`, which can beat the first
drawn frame, so the softmax.com embed samples an unpainted shell. The fork instead polls
`document.documentElement.getAttribute("data-replay-loaded") === "true"` on `requestAnimationFrame`
(bounded at 240 frames, then `tell("error", "renderer never drew a frame")`) and posts `ready` only
after it is set. `ready` therefore always means a picture.

**Bundle.** The manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}`;
`tools/build_replay_viewer.sh` (bullwhip's hook, paths renamed, committed `chmod +x`) is the
`coworld build` hook and **`mkdir -p`s the output parent before any containment check** (ecos,
2026-08-23). It compiles `replay-viewer/hanabi_replay.nim` to wasm (local `emcc` if present, else the
pinned `emscripten/emsdk` container from `Dockerfile.replay-viewer`) and copies `hanabi_replay.js`,
`hanabi_replay.wasm`, `index.html`, `static_replay.js`, `client/renderer.js`, `client/chrome.css` and
the `data/` assets into the bundle. **Never a `/client/replay` pod viewer.**

### Chrome provenance — copied byte-for-byte, extended by appending

The pins name `client/chrome_common.js` and `client/replay_broadcast.html`. **The bullwhip lineage
has neither** (eleusis, 2026-08-23; confirmed in this mount: `client/` holds `chrome.css`,
`renderer.js`, `replay.html`, `global.html`, `player.html`). Those two roles are held by
**`client/chrome.css`** (the shared chrome, the `chrome_common.js` analogue) and
**`client/replay.html`** (the broadcast page, the `replay_broadcast.html` analogue; the static
bundle's `replay-viewer/index.html` is the same page with `./` asset paths). Nothing is imported from
a starter that does have those filenames. The rule is applied to bullwhip's two files:

- **`client/chrome.css` is copied byte-for-byte** and a single `/* ---------- Hanabi ---------- */`
  block is **appended at the end**. No existing rule is edited or deleted — the file's own convention
  is to accrete one appended block per game. The appended block contains exactly:
  - `:root { --band: 84px; --hudscale: 1; }` — set for real by `relayout()` (below);
  - `#tokenbar`, `.tok-score`, `.tok-hint`, `.tok-fuse`, `.tok-deck`, `.tok-pip`,
    `.tok-pip.spent`, `.tok-fuse.blown`, all at `font-size: calc(12px * var(--hudscale))`;
  - `#hintpane`, `#hintpane .hp-head`, `.hp-line`, `.hp-line.playable`, `.hp-line.dead`,
    `.hp-line.critical`, `.hp-line.negative`;
  - `.plate-plays`, `.plate-misplays`, `.plate-fallback` scorebug chips;
  - `#loading { bottom: var(--band); }` so the caption never sits over the transport;
  - beat-marker CSS for **every kind the scrubber emits** — `.beat-marker.hint` (blue, 10 px),
    `.beat-marker.play` (green, 12 px), `.beat-marker.stack5` (amber, 14 px),
    `.beat-marker.misplay` (red, 14 px), `.beat-marker.discard` (ghost, 8 px),
    `.beat-marker.deckout` (paper, 12 px), `.beat-marker.end` (amber, 3 px × 14 px) — plus
    `button.beat-marker { padding: 0; border: 0; background: var(--tc, var(--paper-dim));
    cursor: pointer; }`;
  - feed colours `.feed-hint`, `.feed-play`, `.feed-misplay`, `.feed-discard`, `.feed-stack5`,
    `.feed-deckout`, `.feed-end`;
  - the small-screen queries: `@media (max-width: 720px) { #hintpane { display: none; } }`,
    `@media (max-width: 560px) { .plate-label, .plate-misplays { display: none; }
    #tokenbar .tok-label { display: none; } }`,
    `@media (max-width: 420px) { #scorebug { grid-template-columns: repeat(2, 1fr); } }`.
- **`client/replay.html` is bullwhip's page with a game block appended** — never a rewrite that
  reuses the ids (cogame-gridlock, 2026-08-23). **Every element the starter ships is kept, with its
  id:** `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`,
  `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`,
  `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, and the
  `fit()` + `bindFeedToggle` bootstrap. **Elements removed: none.** The only edits are (a) the
  wordmark text `BULL<span>WHIP</span>` → `HANA<span>BI</span>` and the `<title>`, and (b) **two
  appended elements**: `<div id="tokenbar"></div>` inserted between `#scorebug` and `#board-wrap`,
  and `<div id="hintpane"></div>` appended inside `#layout` **after** `#stage` and **before**
  `#feed`. `replay-viewer/index.html` gets the identical treatment (same page, `./` asset paths,
  plus the `hanabi_replay.js` and `static_replay.js` script tags).
- **Zoom: dropped entirely.** Bullwhip ships no `#viewpanel` (no zoom bar, no minimap) and none is
  added. The table is **fixed** — five fireworks and four hands of four, always rescaled to the
  canvas by `computeLayout`, whole table in frame at every size — so zoom controls would be dead
  weight.

### Transport rules

- `--band` and `--hudscale` are set **on `:root`** (`document.documentElement`) by a `relayout()`
  function in the page bootstrap of both `client/replay.html` and `replay-viewer/index.html`, called
  on `load`, on `resize` and from the feed-toggle handler: it measures `#transport`'s `offsetHeight`
  into `--band` and sets `--hudscale = clamp(0.8, width / 960, 1.15)`. `fit()` (the canvas resizer)
  is called from the same function, so the canvas and the custom properties can never disagree.
- **Nothing is overlaid in the transport band.** `#transport` is the last child of `#stage` in normal
  flex flow; the only absolutely-positioned overlays (`#lightpool`, `#grain`, `#endscreen`) live
  inside `#board-wrap`, which ends where the band begins, and `#loading` is pinned above it with
  `bottom: var(--band)`.
- **The endcard stops at `var(--band)`** — `#endscreen` is `position: absolute; inset: 0` inside
  `#board-wrap`, so its bottom edge is exactly `var(--band)` above the page bottom — **and is
  dismissed by every seek**: `attachReplay`'s `setIndex` calls `updateEndscreen(…, index >=
  events.length && events.length > 0, …)` on *every* index change and `updateEndscreen` toggles
  `.show`, so any scrub below the last frame hides it. Bullwhip's code, kept verbatim.
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` is kept verbatim except that each
  beat is created as `<button type="button" class="beat-marker …">` with an `aria-label`/`title` and
  an `onclick` that seeks to that frame; the container keeps its drag-to-seek pointer handlers. Beats
  are emitted for every **hint** (`"T23 · Ratchet tells Widget about 3s"`), every **play**
  (`"T24 · Widget plays the green 3"`), every **completed firework** (`"T31 · green is finished"`),
  every **misplay** (`"T18 · Gizmo misplays the blue 4 — 2 fuses left"`), every **discard**
  (`"T12 · Sprocket discards the red 1"`), the **deck-out** (`"T61 · deck out — four turns left"`)
  and the **end** (`"Final — 19 of 25"`). The appended CSS block defines a rule for each of those
  seven kinds; the round spans and the every-4th separator the starter already draws are kept, one
  span per **seat rotation** (four turns).
- **Naming guard** (tandem, 2026-08-23): the appended game-block builders are named
  `markHanabiBeat` and `buildHanabiHintPane`, never `markBeat`/`buildScrub`, so nothing can be
  shadowed by a chrome alias assignment; `tests/test_viewer.nim` asserts no top-level name in the
  appended block collides with a name the chrome defines above it.

### The stage — real art, drawn over the starter's assets

`client/renderer.js` is bullwhip's renderer (topband, scorebug, feed, scrubber, endscreen, name map,
effects, both drivers, replay pacing) with the *conveyor* stage replaced by the **table**:

- **The table** is `data/arena_floor.png` tinted to a dark felt, with the starter's `#grain` and
  `#lightpool` overlays kept. Layout, top to bottom: the **fireworks row** (five stacks, centred),
  the **discard strip**, then **four hand rows**, one per seat.
- **Cards** are drawn on canvas, not sprited: a rounded rectangle (`roundRect`, already in the
  renderer) filled in the card's colour, ink border, the **rank as a large numeral** centred, the
  **colour letter** (`R`/`Y`/`G`/`B`/`W`) in the top-left corner, all in `data/font.ttf`. Palette:
  red `#c8452f`, yellow `#e0b13a`, green `#4f9a54`, blue `#3f74b8`, white `#ece2cf` with a heavier
  ink border so it reads on the felt. Numerals plus letters mean the game is legible in greyscale and
  to a colour-blind spectator — the colour fill is never the only signal.
- **Knowledge pips** on every card (spectators see the face *and* what the holder knows): a filled
  colour dot when the holder has a positive colour hint, a small ghost numeral when they have a rank
  hint, a struck-through dot/numeral row for negative information, a `candidates: N` count, and a
  small notch on the **chop** slot. A `knownPlayable` card gets a green corner flag; a `knownDead`
  card is dimmed.
- **Fireworks stacks**: the played card face at the top of each stack with ghost outlines of the
  ranks still to come; completing a stack flashes and spawns a small burst (the only particle effect).
- **The fizzle**: a misplay burns the card — it flips, chars from the corner, drops into the discard
  strip, and one fuse marker in `#tokenbar` snuffs out with a 400 ms shake of the board. This is the
  moment the idea asks for and it is unmissable.
- **The hint beam**: an arc from the giver's row to the receiver's row carrying the hint glyph (a
  colour swatch or a numeral); the touched slots pulse, the untouched slots dim for 600 ms, and
  `#hintpane` fills with the `learned` lines, `PLAYABLE` badges for `nowPlayable`, `SAFE` for
  `nowDead` and `LAST COPY` for `nowCritical` — "what the receiver can now infer", in words.
- **Seat rows**: the seat's cog (`soldier_<red|blue|green|yellow>_front.png`) at the left, an alias
  plate (policy name spectator-side), then the four card slots. The acting seat's row is lit; a seat
  whose last move was a `fallback` shows a small `FALLBACK` chip.
- **Banner**: the acting seat's spectator-only line on a paper tag drawn in a **reserved band to the
  right of that seat's row**, whose width is computed from `MaxBannerLen` measured in the actual font
  at the current scale, wrapped to at most two lines and ellipsized on a rune boundary — never laid
  out relative to something that can slide off the canvas (cogchemists, 2026-08-24: text drawn at a
  negative coordinate passes the load signal, the soak and the screenshot).
- **`#tokenbar`**: `SCORE 11/25 · HINTS ●●●●●○○○ 5/8 · FUSES ◆◆◇ 2/3 · DECK 17`, and `DECK OUT — 3
  TURNS LEFT` once the countdown is armed.
- **Clock** (`#clock`): `TURN 23 / 80 · 11 / 25`, and `FINAL` at the end.
- **Scorebug** (`#scorebug`, 4 plates): alias/policy name, cards banked, misplays, hints given, and a
  `FALLBACK` count chip when non-zero. The **team score** lives in `#tokenbar` and the clock, because
  it is the same number for every seat.
- **Feed**: plain English, one line per turn — `Sprocket tells Ratchet about 1s (slots 2, 4) —
  Ratchet can now play slot 2.`; `Ratchet plays a red 1 — red reaches 1.`; `Gizmo misplays a blue 4 —
  fizzle, 2 fuses left.`; `Widget discards a white 4 — the last one; white can never pass 3.`;
  `Deck out — four turns left.`; `Final — 19 of 25, honourable.` Numbers as numbers, never internal
  notation.
- **Endcard**: the team score huge (`19 / 25`) with the standard verdict band — 0–5 `HORRIBLE`, 6–10
  `MEDIOCRE`, 11–15 `HONOURABLE`, 16–20 `EXCELLENT`, 21–24 `AMAZING`, 25 `LEGENDARY` — the five
  finished stacks drawn, the ending (`DECK OUT` / `THREE MISPLAYS` / `PERFECT` / `TURN LIMIT` /
  `CLOCK`), and one row per seat: policy name, cards banked, misplays, hints given, discards.

**Playback cadence** (bullwhip's `stepMs` switch, retuned): a `hint` frame dwells **1300 ms** (long
enough to read the annotation), a `play` 900 ms, a **misplay 1400 ms** (the fizzle), a `discard`
700 ms, the `start` 600 ms and the `end` 1500 ms. A standard 80-turn episode is ≈ 85 s of playback;
the certification fixture (24 turns) is ≈ 26 s, comfortably longer than the 10 s `--soak` window
(ecos, 2026-08-23: a smoke replay shorter than the soak reads as frozen).

**Legible at 360 px wide** (the softmax.com featured-match iframe): four hand rows of four cards fit
at ≈ 60 px per card with a 16 px rank numeral; `#hintpane` and `#feed` collapse behind the starter's
existing `LOG »` toggle under 720 px; `.plate-label`/`.plate-misplays` and the `#tokenbar` word
labels hide under 560 px (the pips and numbers stay); the scorebug goes 2×2 under 420 px;
`.plate-name` keeps bullwhip's `flex: 1 1 auto; min-width: 3.2em`. At 360 px a spectator still sees
every hand, the fireworks, the score, the hints/fuses and the transport.

---

## Packaging

- **`compose.yaml`** — one service, **`hanabi`** (`coworld build` derives the manifest image
  placeholder from the compose service name: `services.hanabi` → `{{HANABI_IMAGE}}`; `{{GAME_IMAGE}}`
  is not a thing — lantern 0.1.0), `image: coworld-hanabi:latest`, `platform: linux/amd64`,
  `build: {context: ., network: host}`.
- **`Dockerfile`** — bullwhip's two-stage nimby build, one image, two entrypoints: `/bin/hanabi`
  (game, `CMD`) and `/bin/hanabi-player`. Copies `data/` and `client/`.
  **`Dockerfile.replay-viewer`** — bullwhip's, same pinned emsdk tag, paths renamed.
- **`hanabi.nimble`** — bullwhip's requires (`nim >= 2.2.4`, `bitworld`, `mummy`, `curly`, `whisky`),
  `srcDir = "src"`; `nimby.lock` carried over unchanged.
- **`coworld_manifest_template.json`** — `$schema` set, **8 tags** (`card-game`, `cooperative`,
  `hidden-information`, `theory-of-mind`, `hanabi`, `llm-driven`, `turn-based`, `four-player`),
  `game.name` **`hanabi`** (the softmax.com slug), `game.runnable.type: "game"`,
  `image: "{{HANABI_IMAGE}}"`, `run: ["/bin/hanabi"]`,
  `env: {"ANTHROPIC_API_KEY_URI": "secret://coworld/hanabi/anthropic_api_key"}` (without it the
  hosted container never gets the secret and every league episode silently plays scripted — hive,
  2026-08-23), `source_url: https://github.com/Metta-AI/cogame-hanabi/tree/main`,
  `"replay_viewer": {"bundle": "static-replay-viewer"}`. The description states the co-op scoring and
  that the leaderboard to read is mean score, not Elo.
- **`game.config_schema`** — a real JSON Schema, `additionalProperties: false`,
  `required: ["tokens","players"]` (eleusis: `tokens` must stay in `required`). **Every array
  property carries `minItems`/`maxItems`** (tandem 0.1.0): `tokens` and `players` both
  `minItems: 4, maxItems: 4`. Properties: `num_agents` (integer, min 4, max 4), `seed` (integer),
  `maxTurns` (20..120, default **80**), `episodeTimeoutSeconds` (60..6000, default 1200),
  `turnDelayMs` (0..5000, default 150), `model` (string, default `claude-sonnet-5`, described as
  direct-Anthropic-only), `maxOutputTokens` (256..2000, default **800**), `llmTimeoutSeconds`
  (5..300, default **20**), `player_connect_timeout_seconds` (number, default 180).
- **`game.results_schema`** — mirrors `resultsJson`; every seat array `minItems: 4, maxItems: 4`,
  `fireworks` `minItems: 5, maxItems: 5`; `scores` items `number, minimum: 0, maximum: 25` and
  documented as "the team score, identical for every seat, higher is better"; `reason` documented as
  `complete|deadline`; `endReason` as `perfect|strikeout|deckout|turnlimit|deadline`.
- **`game.protocols`** — **both** `player` and `global`, each a `{"type": "text", "value": "…"}`
  object, never a bare string (cogame-garble 0.1.0, 2026-08-24): `player` documents
  `hanabi.player.v1` frame by frame, including that a policy is a prompt, that the `state` frame is
  redacted (own hand as knowledge only) and that `PLAYER_SCRIPTED` names a built-in baseline;
  `global` documents the `/global` snapshot, the frame shape of §*Sim module*, the three event kinds
  and where the static replay bundle renders.
- **`game.docs`** — `readme` (`{"type":"text","value":…}`) plus `pages`: **`rules.md`** (deck, deal,
  slots, the three actions and their legality, the numbered turn resolution, endings, scoring) and
  **`hints-and-knowledge.md`** (the knowledge model, candidate sets, `knownPlayable`/`knownDead`,
  chop, exactly what an observation contains and what it never contains, the reply schema, and the
  two scripted baselines' algorithms) — the page a champion author actually needs.
- **`player[]`** (top level, three entries, all on `{{HANABI_IMAGE}}` running `/bin/hanabi-player`,
  each with `id`/`type`/`name`/`description`/`source_url` and bullwhip's resource block):
  - `hanabi-player` — the prompt player (`PLAYER_PROMPT`, no `PLAYER_SCRIPTED`);
  - `hanabi-conventions` — `env: {"PLAYER_SCRIPTED": "conventions"}`;
  - `hanabi-cautious` — `env: {"PLAYER_SCRIPTED": "cautious"}`.
- **`variants[]`** — each with a `description` (required by the 0.1.42 upload contract) and
  **`num_agents: 4`**:
  - `standard` — "Four cogs, one 50-card deck, up to 80 turns of hints and fireworks." `players` ×4,
    **`num_agents: 4`**, `maxTurns: 80`, `turnDelayMs: 150`,
    `player_connect_timeout_seconds: 180`.
  - `sprint` — "The same deal with only 48 turns: bank what you can before the clock." `players` ×4,
    **`num_agents: 4`**, `maxTurns: 48`, `turnDelayMs: 80`,
    `player_connect_timeout_seconds: 180`.
- **`certification`** — `game_config`: `players` = `[Sprocket, Gizmo, Ratchet, Widget]`,
  **`num_agents: 4`**, `seed: 7`, `maxTurns: 24`, `turnDelayMs: 0`,
  `player_connect_timeout_seconds: 180`; `players`:
  `[{hanabi-player}, {hanabi-conventions}, {hanabi-player}, {hanabi-cautious}]` — **every declared
  player runnable occupies a slot** (raid 0.1.2 → 0.1.3: `players_missing` otherwise), with the
  prompt player on two seats. 24 turns ≈ 26 s of playback, longer than the `--soak` window.
- **`tools/ci/docker_smoke.sh`** — the coworld-builder template with `<slug>` = `hanabi`,
  `<IMAGE>` = `coworld-hanabi`, **`<SEATS>` = 4**; committed `chmod +x`. It also asserts **every
  player container exited 0** (cogmud, 2026-08-24 — the template still does not).
  `tools/ci/viewer_smoke.mjs` copied **verbatim**, no substitutions.
  `.github/workflows/ci.yml` and `coworld-release.yml` from `templates/`, with `<slug>`/`<IMAGE>`/
  `<SEATS>` substituted and `--soak 10` added to the browser-load step.
- **`tools/ci/policies.json`** — the four phase-40 policies: champions `hanabi-signaler` (daveey) and
  `hanabi-reader` (`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), both `PLAYER_PROMPT`;
  fillers `hanabi-conventions` and `hanabi-cautious`, both `PLAYER_SCRIPTED`. A scripted policy
  seated as a champion is a failure state. (This lineage calls the LLM from the **game** container,
  so no `USE_BEDROCK` env is needed on the policies — that is a factorio-lineage requirement,
  cogolf 2026-08-24.)

### Design pins (playbook §Phase 0) — how each is satisfied

| Pin | Where |
|---|---|
| Starter chosen by game shape | `cogame-bullwhip` — turn-based, cards, hidden information, native game logic, policy = LLM prompt, pure `sim` shared with the wasm viewer (title paragraph). |
| Public `Metta-AI/cogame-hanabi` | Repo created **public** in phase 20 (a certification prerequisite); `source_url` points at it. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `hanabi-player` (`PLAYER_PROMPT`) vs `hanabi-conventions` / `hanabi-cautious` (`PLAYER_SCRIPTED=…`), one image, two entrypoints (§Decisions, §Packaging). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; the wasm module re-derives every turn in the browser; nothing but S3 is contacted (§Viewer). |
| Real art; starter chrome reused verbatim | `chrome.css` byte-for-byte + one appended block; `replay.html`/`index.html` = the starter's page + **two** appended elements, **nothing removed**; felt, cogs and font from `data/`, cards drawn in the chrome's palette (§Viewer). |
| Legible to a casual spectator | `SCORE 11/25`, `HINTS 5/8`, rank numerals and colour letters on every card, plain-English feed, the hint pane in words; the 360 px layout is specified (§Viewer). |
| Two name spaces | Anonymous cog aliases in-game, in every prompt and in every player frame; `policyNames` + `makeNameMap` spectator-side only, applied at every render site (§The game). |
| Degrade never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6`, pre-turn deadline check with `TurnReserveSeconds = 45`, `endEarly()`, `MinRequestSpacingSeconds = 2.0`; **~336 s** typical for a full 80-turn episode (§Decisions). |
| `num_agents` in every variant AND the cert fixture | **4** in `standard`, in `sprint`, in `certification.game_config`, and `<SEATS>` = **4** in `tools/ci/docker_smoke.sh`. |
| Deck seeded and logged (idea's integrity note) | One `seed` in the config and in the `start` event; the deck is a pure function of it; `replayMatch` re-derives every card and asserts the `digest` (§Sim module). |
| Cross-play league (idea's integrity note) | Round-robin seats each champion with the two scripted fillers, the other champion and copies of itself; scores are the team's, so nothing a seat can do privately raises its own number (§The game). |

---

## Tests

`tests/` runs under `nimble test` in `ci.yml`'s test job (the sandbox cannot run any of this locally —
CI is the only harness). The smoke job **`needs:` the build job** and never reuses a cached binary.

**`tests/test_sim.nim` — the rules.** The deck is exactly 50 cards with the 3/2/2/2/1 multiset per
colour; the shuffle is seeded and reproducible and two seeds differ; the deal gives 4 seats 4 cards
with slot 1 newest and leaves 34; a draw enters slot 1 and shifts; with an empty deck the hand
shrinks and slots renumber; `play` advances a stack only on `fireworks+1`; a 5 refunds a hint token
**only** when `hintTokens < 8`; a misplay burns a fuse and discards the card; `discard` refunds and is
**illegal at 8 tokens**; a hint costs a token, is illegal at 0 tokens, on self, and when it touches
nothing; a hint marks **every** matching card and writes negative information on the rest; candidate
sets shrink correctly under counting (all three red 1s visible ⇒ red 1 eliminated) and
`knownPlayable`/`knownDead`/`chopSlot` agree with hand-built positions; the countdown arms at deck-out
and ends the game exactly 4 turns later; `perfect`, `strikeout`, `deckout`, `turnlimit` each fire on a
hand-built position and in that priority; `score` = Σ stack heights and `results.scores` are four
equal numbers; `endEarly` gives `reason = "deadline"` with the stacks as they stand; `legalMoves` is
non-empty at **every** state of 200 seeded scripted episodes and matches an independent brute-force
legality predicate; the same config twice gives an identical `digest`; `sampleEpisode` is idempotent.

**`tests/test_bot.nim` — bounded orders / legality on the scripted baselines.** `conventions` and
`cautious` each play 200 seeded whole episodes (all four seats, and mixed pairings) with **zero**
illegal proposals (every proposed move ∈ `legalMoves`), zero exceptions, every episode ending
`complete`, and each episode under 50 ms; `cautious` never misplays (0 fuses lost across all seeds);
`conventions` beats `cautious` on mean score over 50 seeds and scores ≥ 12 mean — a baseline that
cannot bank half the fireworks is not a partner worth beating; `decideAll` with no credentials
returns exactly the scripted decisions and never touches the network; the reply table parses
(canonical object, `move` string form, fenced, trailing prose, alias target, `color`/`number`
spellings, numeric strings) and rejects (unknown action, slot 0, slot 9, self-hint, empty hint,
discard at 8 tokens) — including that a 700-`é` note caps at exactly `MaxNoteLen` **runes**.

**`tests/test_prompt.nim` — redaction.** On a crafted fixture whose seat-0 hand holds identities that
appear nowhere else on the table, seat 0's observation and its player `state` frame contain **none**
of those identity strings; they do contain its own knowledge lines, the other three hands, the move
log and the `LEGAL MOVES` block; and they contain no other seat's `note` or `banner`, no policy name,
no `seed`, and nothing derived from the deck order. Every entry of the printed `LEGAL MOVES` block
parses back into an element of `legalMoves(sim)` and vice versa (the list *is* the legality rule).

**`tests/test_replay.nim` — end-to-end and strict UTF-8.** A full episode is played with scripted
seats and artifacts are written to a temp dir; the replay is re-read with a **strict** parser
(`parseJson` on the raw bytes plus `validateUtf8 == -1`) after turns whose `note` and `banner` are
multi-byte strings truncated exactly at the caps; `replayMatch(config, events)` re-derives every turn
and its `digest` equals the recorded one for 20 seeds, **and the re-derived hint annotations
(`learned`, `nowPlayable`, `nowDead`, `nowCritical`) equal the recorded ones**; `frames.len ==
events.len + 1`; the final frame equals the live `frameJson` tail; event JSON round-trips
(`eventFromJson(eventToJson(e)) == e`) for all three kinds; `results.reason` ∈ {`complete`,
`deadline`} and `results.endReason` ∈ the five documented strings, and nothing else is producible.

**`tests/test_viewer.nim` — chrome invariants.** `client/chrome.css` byte-matches the starter's file
up to the appended `/* Hanabi */` marker; `client/replay.html` and `replay-viewer/index.html` contain
**every** starter element id listed in §*Viewer* and no starter element was removed; the appended JS
block defines no top-level name that the chrome above it already defines; every `beat-marker` kind the
renderer can emit has a CSS rule; `#viewpanel` appears nowhere; the manifest's image placeholder
matches the compose service name (`{{HANABI_IMAGE}}` ← `services.hanabi`).

**`tools/ci/docker_smoke.sh` (job `docker-smoke`)** — builds the production image and runs one real
episode in raw docker with the certification fixture's seat mix (4 seats, no API key ⇒ every seat
scripted), asserting the game exits 0, `results.json` and the replay exist, the replay parses as
JSON, **every player container exited 0**, and the seat-count invariants (`SEAT-COUNT FAIL:` is
grepped, never trusted to job colour). It copies the replay to `dist/smoke/` for the next job.

**`tools/ci/viewer_smoke.mjs` (job `wasm-viewer`, `needs: docker-smoke`)** — the only gate that
**executes** the bundle rather than building it: it builds `dist/static-replay-viewer` via
`tools/build_replay_viewer.sh`, downloads the replay `docker-smoke` produced, opens the bundle in
pinned Playwright Chromium against **that** replay, and requires `data-replay-loaded="true"` (not
merely a bridge `ready`), no `data-replay-error`, non-empty `#clock`/`#scorebug`/`#feed`, a live
`#scrub`, `--strict-text-bounds` with `canvas_text.never_inside == 0`, and — with **`--soak 10`** —
that the clock keeps advancing during uninterrupted playback (cogball 0.1.4).

**`tools/ci/renderer_fixture.html` (its own `ci.yml` step, also `--strict-text-bounds`)** — the
worst-case model-text fixture. `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY`, so every seat in
every CI replay is scripted and **emits no `banner` and no `note`** — nothing that plays a CI replay
ever draws the banner tag (cogchemists, 2026-08-24). The fixture loads the real `renderer.js` with a
synthetic frame carrying a full `MaxBannerLen` banner on all four seats, a full `learned` block, and
long alias/policy names, at 360 px, 720 px and 1280 px, and self-checks that every drawn string stays
inside the canvas.

---

## Out of scope (v1)

- Any seat count other than 4, and therefore the 2-, 3- and 5-player deals (hand size 5 for 2–3
  players, the shorter 5-player hand); spectator seats; seats joining or leaving mid-episode.
- The rainbow / sixth-suit variants, the "black" suit, multicolour-as-wild, and every other HLE game
  parameter (`observation_type`, `max_information_tokens`, `max_life_tokens`, `random_start_player`)
  as a config knob — the constants of §*The game* are the game.
- Scoring variants: zero on strikeout, per-seat credit for banked cards, bonus for a perfect game.
  `contributions` is display-only and stays that way.
- Convention libraries: no H-group document, no "finesse"/"bluff"/"5-save" rules in the shared system
  prompt, no convention negotiation phase. A policy may declare its own conventions in its
  `PLAYER_PROMPT`; the game teaches none.
- Inference deeper than §*The game*'s one-pass model: no fixpoint over multiple cards, no
  "what would a rational partner have hinted" reasoning in the annotation, no automatic detection of
  finesses/bluffs, no per-seat belief distributions in the viewer beyond `learned`, `nowPlayable`,
  `nowDead` and `nowCritical`.
- Any communication channel other than a legal hint: no chat, no table talk, no notes shared between
  seats. `banner` is spectator-only precisely so it cannot become one.
- Cross-episode memory: a policy starts every episode from its prompt, with no carried-over model of
  its partners.
- Undo, takebacks, mid-episode reseeding, human-in-the-loop play, an in-viewer knowledge editor or a
  "what should I have done" analysis pane.
- An RL vector observation / discrete action index (the PettingZoo interface), and any attempt at
  bit-exact parity with HLE's internal encodings.
- A live-server (`/client/replay`) replay viewer, a zoom bar or minimap, audio, localisation, and
  animation beyond the fizzle, the hint beam and the firework burst.
