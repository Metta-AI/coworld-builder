# Trick-Taking — one engine, four rule modules, no talking allowed (Euchre · Spades · Hearts · Oh Hell)

**Starter: `Metta-AI/cogame-babel`** (`/workspace/starters/cogame-babel`, v0.1.4, commit `d55d999`;
lineage parley → cosino → focus → babel → bullwhip). Babel is the current best parley-stack
template and it is already this game's shape: a **four-seat, turn-based, hidden-information game
whose policy IS a prompt**, with a pure Nim `sim` module driven identically by the server, the
tests and the wasm replay viewer; anonymous cog aliases in-game with policy names spectator-side;
a scripted baseline that is a fieldable policy; per-seat **private notes** carried between rounds
(exactly the "count the cards and remember" affordance a trick-taking cog needs); and all four
static-replay-viewer files in one consistent set. **Every convention there holds here unless this
note says otherwise.** Every babel file named below was read at that commit; where babel's own
chrome lags the current template pins (clickable beats, `--band`/`--hudscale`, the postMessage
ordering) this note names the exact patch and the scar it comes from.

**Source idea (verbatim):**

> EXTENSION of Metta-AI/coworld-euchre — a four-player trick-taking Euchre coworld on MettaGrid, currently an incomplete scaffold (template manifest, no Dockerfile). Rather than a second card-game engine, finish Euchre with a pluggable rule module and ship the family through it:
>     Euchre (4p partnerships) — the scaffold's own game; first to certify.
>     Spades (4p partnerships, bidding tricks), Hearts and Oh Hell (3-7p individual; avoid / predict tricks).
>     Bridge (4p; bidding as a constrained signalling language, then play — the headline variant).
>     Dou Dizhu (1 landlord vs 2 peasants — asymmetric teams).
>
> Hidden hands, inference from play, and in partnership games a pure test of implicit communication under rules that forbid talking. Partners are server-assigned.
>
> Seats: 3-7 by module
> Motive: team zero-sum (partnerships) or individual
> Policy interface: discrete card/bid per turn; LLM natural
> Integrity (anti-collusion): server-assigned partners; anonymous aliases; Oh Hell/Hearts soft-play audit.
> Replay plan: all hands visible; 'what partner just told you' annotation on each bid/lead.
>
> Source: OpenSpiel bridge, spades, hearts, euchre, oh_hell, dou_dizhu; RLCard; github.com/Metta-AI/coworld-euchre.

**Coordinator ruling (binding, already logged):** the fork base is `cogame-babel`, **not**
`coworld-euchre`. `Metta-AI/coworld-euchre` is a **private** Python/MettaGrid scaffold — verified
by reading its HEAD tree over the API on 2026-08-26: `coworld_manifest_template.json`,
`src/cogame_euchre/{game.py,cli.py,framework/,missions/,variants/}` (an empty `variants/__init__.py`),
card sprites under `src/cogame_euchre/assets/objects/`, four `tests/`, and **no Dockerfile, no
compose.yaml, no replay viewer**. It is a rules-and-art reference only; a private repo cannot be
certified at all (`source-resolves` 404s on private). This run ships a new public repo
**`Metta-AI/cogame-trick-taking`** on babel conventions. The idea's "pluggable rule module" is
honoured as the **internal engine architecture**: one trick-taking engine, per-game rule modules,
each exposed as a manifest variant.

---

## The game

Four cogs sit at one card table and play a **family** of trick-taking games. One engine deals,
enforces follow-suit, decides who takes the trick and rotates the deal; a **rule module** supplies
the deck, the bidding, the trump rule, the hand scoring and the "what your partner just told you"
annotation. Nothing crosses the table but cards: **there is no chat channel, no `say` field, no
table talk of any kind.** Everything a partner knows about your hand, it inferred from what you
bid and what you led. That is the whole game.

### 1. Seats, teams, and the pins that never move

1. **`num_agents` is 4. Exactly 4, in every shipped variant and in the certification fixture.**
   No variant is 3-seat or 5-seat. (The idea's "3–7 by module" is honoured by the *choice* of
   modules: Euchre, Spades, 4-player Hearts and 4-player Oh Hell are all natural 4-seat games.
   Other seat counts are §Out of scope.)
2. **Table positions** are `0, 1, 2, 3` clockwise. **Partnerships are by table position:
   positions 0 & 2 versus 1 & 3** in the partnership modules (`euchre`, `spades`); the individual
   modules (`hearts`, `oh-hell`) have no teams.
3. **Partners are server-assigned and the assignment is re-drawn every episode.** At `initSim` a
   seed-derived permutation `seatOrder` maps **table positions → policy slots**:
   `seatOrder[pos] = slot`. The league seats policies into slots; the game decides where those
   slots sit at the table. A policy therefore has a different partner from episode to episode and
   can never arrange to be partnered with itself. Every results array and every event is indexed
   by **slot**; only the renderer converts to position.
4. **Anonymous aliases in-game.** Seats play as Sprocket, Gizmo, Ratchet, Widget, Bolt, Piston, …
   (babel's `CogNames` pool, seed-shuffled by `tableNames`). **No policy name ever enters a
   prompt.** Real policy names live in `results.names`, `replay.policyNames`, the scorebug and
   the endcard — spectator side only.
5. **Sequential decisions.** Exactly one seat is on decision at any instant; one decision costs
   one model call. Budgeting is therefore **per decision**, not per turn (§Decisions).
6. **Private notes, no public channel.** Every reply may carry `notes` (≤ 400 runes), fed back to
   that seat only, on every later decision. Notes are a card-counting scratchpad. They are shown
   in the **replay** (spectators see everything) and never to another seat.

### 2. Cards

One encoding for every module, taken from cosino's and used unchanged:
`card ∈ 0..51`, `rank = card div 4` (0 = deuce … 8 = 10, 9 = J, 10 = Q, 11 = K, 12 = A),
`suit = card mod 4` (0 = ♣ clubs, 1 = ♦ diamonds, 2 = ♥ hearts, 3 = ♠ spades).

- **Prompt form** (`cardCode`): rank then suit letter — `2C`, `9D`, `10H`, `JS`, `QD`, `KH`, `AS`.
  **Rank ten is written `10`, never `T`**, in prompts *and* on the canvas (playbook pin:
  "render 10 not T").
- **Viewer form** (`cardGlyph`): `10♥`, `J♠`, `A♦`, suits coloured red (♦♥) / ink (♣♠).
- Euchre's deck is the 24-card subset `rank ≥ 7` (9, 10, J, Q, K, A of every suit).

### 3. The shared engine — exact resolution order

Every hand of every module runs exactly this sequence. Steps 2 and 5 dispatch into the rule
module; everything else is the engine.

1. **Deal.** `dealer = hand mod 4` (a table position; Hearts ignores it for the lead). A fresh
   deck is shuffled from `initRand(seed * 104729 + hand * 7919 + 13)`; `cardsPerHand(module, hand)`
   cards are dealt to each position **clockwise starting from the position left of the dealer**,
   one at a time. Any module-specific extra (Euchre's 4-card kitty and up-card, Oh Hell's turn-up)
   is taken from the top of the remainder, in that order. **The full deal is written to the
   replay** (`hand` event carries all four hands) — spectators see every card; seats do not.
2. **Bidding / trump-making.** The module's bidding phases run, one decision at a time, in the
   stated order. Every bid is **public the instant it is made**.
3. **Trick play.** `tricks = cardsPerHand`. The leader of trick 0 is set by the module. For each
   trick, seats play one card each, **clockwise from the leader**, skipping any seat sitting out
   (Euchre "alone").
4. **Legality of a follow** — one rule, engine-wide:
   `legalMoves(sim)` returns the acting seat's playable cards. If the seat holds ≥ 1 card of the
   **led suit**, its legal set is exactly those cards; otherwise its legal set is its whole
   remaining hand. Two module overlays sit on top, and *only* these two:
   (a) **Euchre**: the left bower (the jack of the other suit of the trump's colour) **is a trump
   card and is not a card of its printed suit** — for leading, for following and for winning.
   (b) **Lead restrictions**: Spades — a spade may not be *led* until spades are broken (a spade
   has been played by a seat void in the led suit) unless the leader holds nothing but spades;
   Hearts — a heart may not be *led* until hearts are broken (a heart or Q♠ has been discarded)
   unless the leader holds nothing but hearts, and on **trick 0** no heart and not the Q♠ may be
   played at all unless the seat holds nothing else.
   The legal set is **never empty** (a seat on turn always holds a card), it is computed by the
   same predicate `applyPlay` validates with, and it is **given to the model verbatim** in the
   prompt (escrow 0.1.3: precomputing the legal set is what stops formal-output fallbacks).
5. **Trick winner.** If any **trump** was played (Euchre: the named suit plus both bowers; Spades:
   ♠; Oh Hell: the turn-up's suit; Hearts: none), the highest trump wins. Otherwise the highest
   card of the **led** suit wins. Rank order is `2 < 3 < … < 9 < 10 < J < Q < K < A`, except that
   in Euchre the trump suit ranks `9 < 10 < Q < K < A < left bower < right bower`. The winner
   leads the next trick.
6. **Hand scoring.** The module converts the trick record into per-position points and into a
   **zero-sum per-slot `net`** (§4). A `handEnd` event records both.
7. **Rotate and repeat** until `hands` hands are complete or an end condition fires (§9).

### 4. Scoring — one formula, all four modules, higher is better

Each module defines, per hand `h`, a **zero-sum** per-slot quantity `net_h[i]` with
`Σ_i net_h[i] = 0`, and a **swing cap** `swingCap(module, h) ≥ max_i |net_h[i]|` proven for that
module's rules. Then, over the hands actually **scored** (`H` of them — a hand voided by the hard
deadline is not scored):

```
net[i] = Σ_{h scored} net_h[i]                            # zero-sum: Σ_i net[i] == 0
NORM   = Σ_{h scored} swingCap(module, h)                 # > 0 whenever H > 0
scores[i] = 0.5 + net[i] / (2 * NORM)                     # ∈ [0, 1]; NO clamp is needed
win[i]    = (net[i] == max(net))                          # ties: every tied slot true
```

- **Sign: higher is better.** A seat that breaks even scores exactly **0.5**. `Σ scores == 2.0`
  (= `n/2`) exactly, in every module. `H == 0` ⇒ every `scores[i] = 0.5`.
- `|net[i]| ≤ NORM` by construction, so `scores ∈ [0, 1]` with no clamping and no special cases.
- **What the league ranks by:** the platform's **Elo over `scores`**, in **one league across all
  four variants, equally weighted, round-robin**. *Reason:* the score is unit-free — a share of
  the same normalised swing whatever the module — so a Euchre episode and a Hearts episode move
  Elo by the same amount, and one leaderboard is what makes this a *family* rather than four
  unrelated boards. `results` also carries the raw legible numbers (`points[]`, `teamPoints[]`,
  `tricks[]`, `bidsMade[]`) for the endcard; the audit (§8) is a **diagnostic and never an input
  to the ranking**.
- **Known and accepted:** Spades' proven swing cap (460) is far above typical play, so Spades
  `scores` cluster nearer 0.5 than Euchre's do. Elo ranks by ordering, `win[]` is reported
  alongside, and the endcard shows raw points — so the compression costs legibility nothing. A
  tighter, tuned normaliser would be a free parameter with no principled value; a proven bound is
  not.

### 5. Module `euchre` — 4 seats, partnerships (positions 0&2 vs 1&3). **First to certify.**

1. **Deck** 24 cards (9, 10, J, Q, K, A × 4 suits). Deal **5 each** clockwise from the position
   left of the dealer in a 3-2 / 2-3 alternating pattern (positions get 3,2,3,2 then 2,3,2,3), the
   remaining **4 cards are the kitty**, and the kitty's **top card is turned face up** — the
   *up-card*, public.
2. **Bidding round 1.** Starting left of the dealer, each position in turn plays one of:
   `pass`; `order` (make the up-card's suit trump); `alone` (make it trump **and** play without
   your partner). The first non-pass ends round 1 and its position is the **maker**.
3. If round 1 was made, the **dealer picks up the up-card and discards one card face down**
   (a decision; the discard is recorded in the replay but is **hidden from the seats**, including
   from the dealer's partner).
4. **Bidding round 2** (only if all four passed). The up-card is turned down. Starting left of the
   dealer, each position may `pass`, or `name <suit>` / `alone <suit>` for any suit **other than
   the up-card's suit**. **Stick the dealer is ON:** if the first three pass, the dealer *must*
   name a suit. There is never a throw-in and never a re-deal — that keeps the hand count, and
   therefore the decision budget, exact.
5. **Bowers.** The jack of the trump suit is the **right bower**, the highest trump. The jack of
   the other suit of the same colour (♣↔♠, ♦↔♥) is the **left bower**, the second-highest trump,
   and for every purpose — following suit, leading, winning — **it is a trump and not a card of
   its printed suit**.
6. **Lead.** The position left of the dealer leads trick 0; if the maker went `alone`, the maker's
   partner sits out the whole hand (its 5 cards are dead, shown greyed in the replay) and is
   skipped in turn order — 3 seats play 5 tricks.
7. **Follow / winner:** engine rules (§3.4, §3.5) with the bower overlay.
8. **Hand scoring** (points to one side, 0 to the other; `mk` = the makers' trick count):
   - `mk ∈ {3, 4}` → **makers 1**; alone and `mk ∈ {3, 4}` → **makers 1**.
   - `mk == 5` → **makers 2**; alone and `mk == 5` → **makers 4** (a lone march).
   - `mk ≤ 2` (**euchred**) → **defenders 2**.
9. `net_h[i] = ptsTeam(i) − ptsOther(i)` (both partners share it); values lie in
   `{±1, ±2, ±4}`. **`swingCap(euchre, h) = 4`** — tight and proven by 8.
10. **`hands` = 8** by default (every position deals twice).

### 6. Module `spades` — 4 seats, partnerships (positions 0&2 vs 1&3)

1. **Deck** 52, **13 each**, dealt clockwise from left of the dealer. **Trump is always ♠.**
2. **Bidding.** Starting left of the dealer, each position bids an integer **0…13**, seeing every
   earlier bid. **A bid of 0 is *nil***. Team contract = the sum of the two partners' **non-nil**
   bids.
3. **Lead.** The position left of the dealer leads trick 0. **Spades may not be led until broken**
   (§3.4b).
4. **Follow / winner:** engine rules; highest spade wins, else highest of the led suit.
5. **Hand scoring**, per team: let `C` = team contract and `T` = tricks won by the team's
   **non-nil** members.
   - `T ≥ C` → `10·C + (T − C)` (each overtrick, a *bag*, is +1).
   - `T < C` → `−10·C`.
   - Each nil member: **+100** if it won 0 tricks, **−100** otherwise. A failed nil's tricks count
     towards `T` for bags but never towards the contract.
   - **No sandbag rollover in v1** (§Out of scope). This makes `|teamScore| ≤ 230` provable:
     the maximum is `130 + 100` (a 13-contract made with a partner's successful nil) and the
     minimum is `−130 − 100`.
6. `net_h[i] = teamScore(i) − teamScore(other)`; `|net_h| ≤ 460`. **`swingCap(spades, h) = 460`.**
7. **`hands` = 4** (one full dealer rotation).

### 7. Module `hearts` — 4 seats, individual, avoid tricks

1. **Deck** 52, **13 each**. **No trump.**
2. **The pass.** Direction by hand index: `0` → left, `1` → right, `2` → across, `3` → **hold**
   (no pass), repeating mod 4. On a passing hand, each position in turn (positions 0,1,2,3 —
   the order is immaterial, nothing is revealed until all four have chosen) selects **exactly 3
   cards** from its 13. Only after all four have chosen are the received cards delivered. A seat
   **never learns** what any other seat passed, except by inference from play; the replay shows
   every pass.
3. **Lead.** The holder of **2♣** leads it to trick 0 (a forced move, no decision spent).
4. **Trick 0 restriction:** no heart and not the Q♠ may be played on trick 0 unless the seat holds
   nothing else. **Hearts may not be led** until broken (§3.4b).
5. **Follow / winner:** engine rules; highest card of the led suit takes it.
6. **Hand scoring.** Penalty `p[i]` = (hearts taken × 1) + (13 if the seat took Q♠). Total is
   always 26. **Shooting the moon:** a seat that takes *all 26* scores `p = 0` and every other
   seat scores `p = 26`.
7. `net_h[i] = mean_h(p) − p_h[i]` (lower penalty is better, so the sign flips here). Normal hand:
   `mean = 6.5`, `net ∈ [−19.5, 6.5]`. Moon hand: `mean = 19.5`, `net ∈ {19.5, −6.5}`.
   **`swingCap(hearts, h) = 19.5`** — tight and proven.
8. **`hands` = 4** (one full cycle of pass directions: left, right, across, hold).

### 8. Module `oh-hell` — 4 seats, individual, predict tricks exactly

1. **Deal schedule.** `dealSchedule` (config; default **`[1,2,3,4,5,6,5,4,3,2,1]`**, 11 hands).
   Hand `h` deals `dealSchedule[h]` cards each from a fresh 52-card shuffle, then turns the next
   card face up: **its suit is trump for that hand** (the turn-up itself is out of play).
   `4 × 6 + 1 = 25 ≤ 52`, so a turn-up always exists.
2. **Bidding.** Starting left of the dealer, each position bids **0…`dealSchedule[h]`**, seeing
   every earlier bid. **The hook (a.k.a. "screw the dealer") is ON:** the dealer may not bid the
   value that would make the four bids sum to exactly the number of tricks. Total bids therefore
   never equal the tricks available and somebody always misses.
3. **Lead.** The position left of the dealer leads trick 0. No lead restriction.
4. **Follow / winner:** engine rules; highest trump else highest of the led suit.
5. **Hand scoring.** `s[i] = 10 + bid[i]` if `tricks[i] == bid[i]`, else **0**.
6. `net_h[i] = s_h[i] − mean_h(s)`; with `c = dealSchedule[h]`,
   **`swingCap(oh-hell, h) = 0.75 · (10 + c)`** — the extreme is one seat scoring `10+c` while the
   other three score 0 (or the reverse), and `0.75` is `(n−1)/n`.
7. **`hands` = 11** (the schedule's length).

### 9. Soft-play audit (individual modules only)

`results.audit` is non-null for **`hearts` and `oh-hell`** and `null` for `euchre` and `spades` —
in a partnership game, letting your partner win *is the correct play* and there is nothing to
audit. It is a **pure function of the recorded event log**, `auditFromEvents(config, events)`,
living in the sim module and called identically by the server and by the wasm viewer (a test
asserts byte-identical JSON from both paths). Every `play` event records the acting seat's
**legal set**, so the audit needs no re-derivation and cannot drift.

For each ordered pair of slots `(a, b)`, `a ≠ b`:

- `chance[a][b]` = tricks in which, at the moment `a` played, **`b`'s card was the current best on
  the table** and `a`'s legal set contained at least one card that would have beaten it.
- `yield[a][b]` = those tricks in which `a` **declined** to beat it.
- `yieldRate[a][b] = yield / max(chance, 1)`.
- `field[a] = Σ_{c≠a} yield[a][c] / max(Σ_{c≠a} chance[a][c], 1)` — the same rate against everyone.
- **Hearts only:** `discards[a][b]` = tricks won by `b` on which `a` was **void in the led suit**
  (a free throw); `gift[a][b]` = the penalty points `a`'s thrown card carried into those tricks;
  `giftRate[a][b] = gift / max(discards, 1)`.

**No flags, no thresholds, no penalties in v1.** The audit reports the matrices, the per-seat
field rate, and `power = {hands, chanceMin, chanceMedian}` so a 4-hand episode's numbers are read
as the weak evidence they are. *Reason (logged here so it is not re-litigated):* cogame-poker,
2026-08-26, burned four coordinator addenda tuning a flag threshold that kept firing on honest
scripted play. The interesting signal — `yieldRate[a][b]` versus `field[a]` — is visible in the
reported matrix, and turning it into an accusation is §Out of scope until there is league-level
aggregation to power it.

### 10. "What your partner just told you" — the replay annotation

Every `bid` event and every **lead** (`play` with `trickPos == 0`) carries a `tell` string
(≤ 120 runes) produced by the pure function `partnerTell(module, event, publicState)`. It is
computed from **public information only** and is **spectator-side only: it never enters any seat's
prompt.** Feeding it to a seat would be exactly the private channel this game exists to forbid.
The tables are fixed and exhaustive — the first matching row wins; if nothing matches, `tell` is
the empty string and nothing is drawn.

**`euchre` bids**
| condition | tell |
|---|---|
| `order`/`alone` by the dealer's **partner** | "Giving the dealer the up-card: side strength, wants that trump in partner's hand." |
| `order`/`alone` by an **opponent** of the dealer | "Taking the up-card away: likely the right bower, or two trumps and an ace." |
| `alone` (any seat) | "Alone: right bower plus at least two more trumps. Partner, stay out." |
| `pass` in round 1 | "No ordering hand in <suit>." |
| `name <suit>` in round 2, not stuck | "Strength is in <suit>, not <up-card suit>." |
| the stuck dealer's forced `name` | "Forced by stick-the-dealer — read nothing into this suit." |

**`euchre` leads**
| condition | tell |
|---|---|
| leads a trump, is the maker or the maker's partner | "Drawing trumps to protect the march." |
| leads a trump, is a defender | "Drawing the maker's trumps early." |
| leads an off-suit ace | "Cashing a certain winner; probably void in <suit> next trick." |
| leads a 9 or 10 off-suit | "Probing: weak in <suit> and hoping partner is not." |
| any other lead | "" |

**`spades`**
| condition | tell |
|---|---|
| `bid 0` | "Nil: not one card that can win a trick. Partner, cover." |
| `bid ≥ 5` | "<n> near-certain winners — long spades." |
| `bid ≤ 2` | "A weak hand; the contract is partner's." |
| leads a spade after the break, partner bid nil | "Pulling trumps to protect the nil." |
| leads an ace | "Banking the contract early." |
| other lead | "" |

**`hearts`** (a table *read*, not a partner tell — there are no partners)
| condition | tell |
|---|---|
| leads a low club or diamond before hearts break | "Flushing out the queen." |
| leads a spade below the queen | "Hunting the queen." |
| leads a heart the trick after the break | "Hearts are running." |
| the seat has taken ≥ 20 penalty points this hand | "This looks like a moon attempt." |
| other lead | "" |

**`oh-hell`**
| condition | tell |
|---|---|
| `bid 0` | "Bidding nothing: will duck every trick." |
| `bid == cards this hand` | "Claiming every trick." |
| the dealer's hooked bid | "Hooked off the balanced number — the table is over/under by <k>." |
| leads a trump on trick 0 | "Cashing the bid immediately." |
| other lead | "" |

### 11. End conditions and `results.reason`

The episode **always** writes `results.json` and a replay, and ends in exactly one of three ways.
`results.reason` is one of **`complete`**, **`deadline`**, **`budget`**; no other value is legal
and `game.results_schema` declares that enum.

1. **`complete`** — the variant's `hands` hands have all been scored.
2. **`deadline`** — wall clock. `T` = `COWORLD_TIMEOUT_SECONDS` when present, else
   `config.episodeTimeoutSeconds` (default **1200**; the game container is not given the env var,
   which is exactly why the default exists). Two guards:
   - **Soft, `0.55·T` (660 s)**, checked *before every decision*: past it, **every remaining
     decision of the hand in progress is played by the scripted baseline** (instant, no network),
     the hand finishes and **is scored**, and the episode then stops. This is babel's
     `seatScripted = state.scripted[seat] or pastDeadline` behaviour, kept.
   - **Hard, `0.56·T` (672 s)**, checked before every decision: the hand in progress is
     **abandoned** — a `handVoid` event is recorded, that hand is excluded from `H` and from
     `NORM`, and the episode stops. The threshold nets off one worst-case decision: 672 s plus one
     worst case (2.2 s spacing + two 20 s LLM attempts + trick pacing + settle ≈ 45 s) ≤ **720 s =
     60 % of 1200 s** (the pin). The hard guard should be unreachable, because past the soft guard
     play is scripted and costs microseconds; it exists so a wedged transport cannot outrun the
     budget.
3. **`budget`** — `EpisodeDecisionBudget = 240` model calls exhausted. Same settle path as the
   soft guard: finish the current hand scripted, score it, stop.

A seat that never connects is **not** an end condition: after `player_connect_timeout_seconds`
(180 s) the game starts anyway and every unconnected slot plays the scripted baseline (babel's
behaviour, kept). Phase 60 check 4 accepts `complete`; `deadline` is declared acceptable here and
`budget` is too, both because the scored hands are honest completed hands.

### 12. Per-seat observation — exactly what is visible and what is hidden

Rebuilt fresh for every decision by `userPrompt`. **Visible to the acting seat:**

- The **module's rules**, verbatim, and the current phase's legal options.
- **Its own hand**, as card codes, sorted by suit then rank; and, on a Euchre `alone` hand, the
  fact that its partner is sitting out.
- Hand number and `hands`, the **dealer**, its own table position, **who its partner is (alias)**
  in the partnership modules, and the seating order clockwise.
- **Trump**: the up-card (Euchre round 1), the named suit once made, the turn-up (Oh Hell), ♠
  (Spades), none (Hearts); and whether spades/hearts are **broken**.
- **Every bid made this hand, by alias, in order** — bids are public.
- **The current trick**: every card played to it so far, in order, with who played it.
- **Every completed trick of the current hand**: the four cards in play order and who took it.
- **Which seats are known void in which suits** this hand (derived from failures to follow —
  public information, precomputed so a cog does not have to).
- **Standings**: every seat's cumulative `points` (module-native), `net`, tricks this hand, and
  bid-vs-made where the module bids.
- **Its own private `notes`** from its last decision.
- **The precomputed legal move set**, exactly — card codes for a play, the integer range for a
  bid, the enum for a call — computed by the same predicate the applier validates with.

**Hidden from the acting seat:** every other seat's cards; the kitty and the dealer's Euchre
discard; every other seat's Hearts pass, until the received cards arrive (and even then only its
own three); every other seat's `notes`; **completed hands' card-by-card transcripts** (only the
running standings survive a hand boundary — the memory a cog wants must live in its own `notes`,
which is the point); the seed; `seatOrder`; the `tell` annotations; the audit; and **every policy's
real name**. There is **no chat, no signalling channel, no side band** — the only thing a seat can
send its partner is a bid or a card.

**Spectators** (`/global`, the replay, the static viewer) see **everything**: all four hands, the
kitty, the discard, every pass, every note, the tells and the audit. That is the idea's "all hands
visible" replay plan.

---

## Decisions: LLM with scripted fallback

Babel's model, unchanged in shape: **the game server owns every decision; a policy is just a
prompt.** The player container's only job is to deliver its prompt over the websocket.

### 1. The LLM path

- One model call per decision, issued by `src/tricks/llm.nim` (babel's `llm.nim`, extended).
  Transports in babel's order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` /
  `AWS_BEARER_TOKEN_BEDROCK`) first, then `ANTHROPIC_API_KEY`, then `ANTHROPIC_API_KEY_URI`.
- Bedrock model candidates, in order: `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. **`us.anthropic.claude-sonnet-4-6` is removed
  from babel's list** (raid, 2026-08-23: it times out on every sidecar call).
- `maxOutputTokens: 900` (babel 0.1.2's fix for `cut off at max_tokens`), **`llmTimeoutSeconds: 20`**
  (not babel's 45 — at 240 sequential decisions a 45 s stall is 7 % of the whole play budget),
  `output_config.effort` is **not** sent (Haiku 4.5 rejects it — babel's guard, kept).
- **System prompt** (exact text; `<ALIAS>`, `<MODULE NAME>` and `<RULES BLOCK>` substituted;
  `<RULES BLOCK>` is `rulesText()` of the active module — the numbered rules of §5–§8, 10–16
  lines):

  > You are `<ALIAS>`, a cog at a four-seat card table playing `<MODULE NAME>`.
  >
  > `<RULES BLOCK>`
  >
  > - You never see another cog's cards. Everything you know about them, you inferred from what
  >   they bid and what they played.
  > - **There is no talking at this table.** No chat, no signals, no side deals. In the partnership
  >   games the ONLY thing you can tell your partner is which card you play and what you bid — so
  >   bid and lead as if your partner is reading you, because they are.
  > - Your notes are private to you and are handed back to you before every decision. Keep your
  >   card count, the voids you have spotted, and your read on each cog in them.
  > - Pick exactly one option from the legal list you are given. An illegal answer is replaced by a
  >   house baseline move, which is never what you want.
  >
  > OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
  > markdown fences, no text before or after the object. Your reply must begin with the character
  > `{` and end with `}`.

- **User prompt**, in this order: standings → seating and partnership → this hand's public record
  (bidding, completed tricks, the current trick, known voids) → **YOUR HAND** → trump / broken
  state → **YOUR NOTES** → `GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the
  rules; always pick a legal option):\n<PLAYER_PROMPT>` → the phase's legal-option instruction.
- **Reply schema** — the only fields ever read, with the phase that reads them:

  | field | type | cap | read in phase | notes |
  |---|---|---|---|---|
  | `action` | string | **≤ 16 runes** | euchre bid 1 / bid 2 | bid 1: `pass`\|`order`\|`alone`; bid 2: `pass`\|`name`\|`alone` |
  | `suit` | string | **≤ 8 runes** | euchre bid 2 | `C`\|`D`\|`H`\|`S`, or `clubs`\|`diamonds`\|`hearts`\|`spades`, any case |
  | `bid` | integer | 0…13 | spades bid, oh-hell bid | out-of-range = parse failure |
  | `card` | string | **≤ 3 runes** | play, euchre discard | a card code, e.g. `10H`, `AS` |
  | `cards` | array, **≤ 3 entries**, each **≤ 3 runes** | hearts pass | exactly 3 distinct codes from the hand |
  | `notes` | string | **≤ 400 runes**, rune-truncated with `…` appended | every phase | private; may be empty |

  **Every string that can reach the replay is truncated on rune boundaries** by one shared helper
  `truncateRunes(s, n)` in `src/tricks/types.nim`: `notes` (400), the operator prompt (4000),
  aliases (16), `tell` (120), the error text recorded on a fallback (200). Babel's `cleanNotes`
  already truncates notes on runes; babel's **server-side prompt cap is a byte slice**
  (`prompt[0 ..< MaxPromptLen]`, server.nim:478) — that is replaced by `truncateRunes` too. A
  byte-boundary cut is exactly how a replay renders in a browser and fails a strict UTF-8 parser
  (playbook gotcha).
  **Parsing tolerance** (babel's `extractJsonObject` — first `{` to last `}`, fences and trailing
  prose tolerated — kept, plus): card codes are upper-cased and stripped of spaces; `T`/`t` is
  accepted for rank ten (canonical output is always `10`); `10H`, `HT`, `H10` and `ten of hearts`
  all resolve; a bare integer `1..k` is accepted as a 1-based index into the printed legal list;
  `{"card": …}` and `{"action":"play","card": …}` are both accepted.

### 2. Degrade, never hang

1. Decision times out (20 s), the transport errors, the JSON does not parse, the move is not in
   the legal set, or a Hearts pass is not exactly 3 distinct held cards → **one retry**, same
   prompt plus
   `"\nYour previous reply was invalid. Respond with ONLY the requested JSON object, choosing one
   option from the legal list."`
   (For a play, the retry also re-prints the legal card list.)
2. Retry fails → the seat's **scripted baseline move** for this phase is played and
   `results.fallbacks[slot]` is incremented.
3. The baseline move is somehow rejected by the applier → the **lowest legal option** is forced
   (lowest card by `(suit, rank)`; lowest legal bid; `pass`), and `results.forcedMoves[slot]` is
   incremented. `legalMoves` is never empty, so the hand always advances. There is no path in
   which the engine waits on anything.
4. **No credentials at all** → `client.disabled` at construction; every seat plays scripted with
   zero network wait, so offline certification and `docker_smoke.sh` (which runs with no
   `ANTHROPIC_API_KEY`) always complete.
5. HTTP 429 → no retry; scripted move immediately, and the inter-decision spacing floor rises by
   500 ms for the rest of the episode.
6. **A deadline mid-hand settles as §The game 11.2 states**: soft guard → the rest of the hand is
   played scripted and *is scored*; hard guard → `handVoid`, the hand is dropped from `H` and
   `NORM`, and the episode stops. Either way players get their `final` frame **before** the
   artifacts are written (babel's ordering, kept — the hosted worker tears player pods down as
   soon as `results.json` exists), and `/healthz` + `/global` keep answering (and answering Ping
   with Pong) for a bounded ~20 s shutdown grace before `quit(0)` (lantern 0.1.4).

### 3. Wall-clock budget — sequential game, per-decision

Trick-taking is **sequential**: exactly one seat is on decision, so there is no parallel batch to
issue and the budget is per decision. (The checklist's parallel-batch clause is for
simultaneous-decision games; it does not apply, and this note says so rather than leaving it
unanswered.)

- **Per decision: 2.6 s budgeted** — Haiku p95 ≈ 2.2 s at these prompt sizes plus `turnDelayMs`
  pacing amortised over the trick. A **spacing floor of 2.2 s from decision start to decision
  start** holds the episode at ≤ 27 requests/minute, inside the Bedrock sidecar's ~30 rpm
  per-episode cap (raid, 2026-08-23).
- **Play budget:** `0.55 × 1200 s = 660 s` at the soft guard, and the true worst-case settle is
  `0.56·T + one worst-case decision ≈ 717 s ≤ 720 s = 60 % of T`.
  **`EpisodeDecisionBudget = 240`** → `240 × 2.6 s = 624 s`, 36 s under the soft guard.
- Per variant, decisions per hand and the arithmetic (worst case, then expected):

  | variant | bids/calls | plays | passes/discards | decisions per hand | hands | worst-case decisions | worst-case seconds |
  |---|---|---|---|---|---|---|---|
  | `euchre` | ≤ 8 | 20 (15 if alone) | ≤ 1 discard | ≤ 29 (expected ≈ 25) | **8** | 232 | 232 × 2.6 = **603 s** |
  | `spades` | 4 | 52 | 0 | 56 exactly | **4** | 224 | **582 s** |
  | `hearts` | 0 | 52 | 4 (3 of 4 hands) | 56 / 52 | **4** | 220 | **572 s** |
  | `oh-hell` | 4 | 4 × cards | 0 | 4 + 4·cards | **11** (Σcards = 36) | 188 | **489 s** |

  Every row is **under the 660 s soft guard** (margin 57–171 s) and **under the 240-call budget**,
  so in normal play neither backstop fires and `results.reason` is `complete`.
- `sampleEpisode(config)` (babel's idempotent budget fit, kept) re-caps at sample time:
  `hands = max(MinHands, min(config.hands, EpisodeDecisionBudget div worstCaseDecisionsPerHand))`,
  and for `oh-hell` it trims `dealSchedule` from the **tail** until the total fits. It is a no-op
  when `config.sampled` is already true, so a replay is never re-fitted.
- **Certification / docker smoke:** no credentials → zero LLM latency, `turnDelayMs = 0`; the
  3-hand Euchre fixture completes in well under a second plus the connect grace, comfortably
  inside `coworld certify`'s default 60 s (no `--timeout-seconds` override needed), while the
  ~100-event replay it produces **plays for ≈ 90 s** in the viewer — far longer than the 12 s
  soak (ecos, 2026-08-23: size the fixture so the replay outlasts the soak).

### 4. Scripted baselines — same image, env-switched

Two named baselines, **both always legal in every module**, both fieldable policies:
`PLAYER_SCRIPTED=follow` and `PLAYER_SCRIPTED=tracker` (any other non-empty value means `follow`).
LLM policies set `PLAYER_PROMPT` instead. **One image**, `/bin/trick-taking-player`, chooses by
env — never two images. Both baselines select **only from `legalMoves(sim)`**; wherever a rule
below points at a card that is not legal, the **lowest legal card** is taken instead.

**`follow`** — the default, and the move played whenever an LLM decision fails.

*Hand strength helper (euchre, for a candidate trump suit `s`):*
`right bower 5, left bower 4, A of s 4, K of s 3, Q of s 2, 10 or 9 of s 1, each off-suit ace 2,
each non-trump suit in which the hand is void +1`.

- **Euchre bid 1:** compute strength for the up-card's suit, counting the up-card as **gained** if
  the seat is the dealer, as **gained by partner** (+2) if the seat is the dealer's partner, and
  as **lost to the opponents** (−2) otherwise. `order` iff strength ≥ 10; `alone` iff ≥ 16;
  else `pass`.
- **Euchre discard:** discard the **lowest-ranked card of the non-trump suit in which the hand is
  shortest**; ties by lowest rank, then by `(suit, rank)`.
- **Euchre bid 2:** score every suit except the up-card's; `name` the best iff its strength ≥ 10
  (`alone` iff ≥ 16); else `pass`. A **stuck dealer** always names its best-scoring suit.
- **Spades bid:** `winners` = (#aces) + (#kings that are not singletons) + (Q♠ if ≥ 3 spades) +
  `max(0, spades − 3)`. **Nil** iff `winners == 0` and no spade above 9 and spades ≤ 3. Else
  `bid = min(13, winners)`.
- **Hearts pass:** take exactly 3 in this priority — (1) Q♠ if spades < 4; (2) A♠ then K♠ if
  spades < 4; (3) highest hearts; (4) highest cards of the shortest non-heart suit.
- **Oh Hell bid:** `winners` = (#trumps ranked ≥ Q) + (#non-trump aces), clamped to `[0, cards]`.
  If the seat is the dealer and that value is forbidden by the hook, move to the nearest legal
  value, **downward first**, else upward.
- **Leading:** if the module has trump and the seat is on the bidding/making side and holds ≥ 3
  trumps → lead the **highest trump** (draw). Else if the seat holds an ace of a non-trump suit →
  lead it. Else lead the **lowest card of the shortest non-trump suit**. In Hearts: never lead a
  heart or the Q♠ while a legal alternative exists; otherwise lead the lowest card of the shortest
  non-heart suit.
- **Following:**
  - Partnership modules — if the **partner** currently holds the trick, play the **lowest legal
    card**. Otherwise play the **lowest legal card that beats the current best**; if none, the
    lowest legal card.
  - Hearts — play the **highest legal card that does not take the trick**; if every legal card
    takes it, play the highest legal card (get it over with). When void in the led suit, throw the
    Q♠ first if held, else the highest heart, else the highest card of the shortest suit.
  - Oh Hell — if the seat still needs tricks (`tricks < bid`), play the lowest legal card that
    beats the current best, else the lowest legal card; if the seat has already made its bid, play
    the highest legal card that does not take the trick, else the lowest legal card.

**`tracker`** — the second baseline and the second filler. **Identical to `follow` except for
these four overrides**, each computed from the public event log (so it is re-derivable in a test):

1. **Void table.** It maintains `known[seat][suit]` = "that seat failed to follow that suit this
   hand". It never leads a suit in which **both opponents** are known void while its partner is
   not (partnership modules), and in Hearts it prefers leading a suit in which the seat holding
   the Q♠-risk is known void.
2. **Certain winners.** When leading, if it holds the **highest outstanding card of any suit**
   (every higher card of that suit has been played or is in its own hand), it leads that card
   before applying `follow`'s lead rules.
3. **Tighter bidding.** Euchre `order` at strength ≥ 12 and `alone` at ≥ 18; Spades
   `bid = max(0, winners − 1)` (never nil unless `follow`'s nil test also passes); Oh Hell
   `winners` counts non-trump aces as 0 when the seat is short in that suit (≤ 2 cards).
4. **Bag avoidance (Spades only).** Once the team has met its contract it plays the **lowest legal
   card** in every remaining trick unless a nil needs covering.

Both are the **fillers** in the league (§Packaging); **both champions are `PLAYER_PROMPT`
policies**.

---

## Sim module

Pure Nim, no IO, no networking — driven identically by the server, the tests and the wasm replay
viewer. Forked from babel's `src/babel/*`, renamed to `src/tricks/*`.

| file | provenance | change |
|---|---|---|
| `src/trick_taking.nim` | babel `src/babel.nim` | rename only: runtime contract, random-seed-if-unpinned, `sampleEpisode` after the seed is settled, live vs replay mode |
| `src/tricks/types.nim` | babel `types.nim` | `GameConfig` (below), `GameEvent`, `EventKind`, `TricksError`, **`truncateRunes`** |
| `src/tricks/cards.nim` | **new** (encoding taken from cosino, described §The game 2) | deck builders, `cardCode`/`cardGlyph`/`parseCard`, `suitOf`/`rankOf`, `euchreEffectiveSuit`, `beats(a, b, led, trump, module)` |
| `src/tricks/rules.nim` | **new** | the `RuleModule` record and the registry |
| `src/tricks/euchre.nim`, `spades.nim`, `hearts.nim`, `ohhell.nim` | **new** | one `RuleModule` each |
| `src/tricks/sim.nim` | babel `sim.nim` | the engine: deal, phases, `legalMoves`, `applyMove`, trick resolution, scoring, `endEarly`, `resultsJson`, `tableStateJson`, `replayMatch`, `eventToJson`/`eventFromJson` |
| `src/tricks/audit.nim` | **new** | `auditFromEvents(config, events)` (§The game 9) |
| `src/tricks/llm.nim` | babel `llm.nim` | prompts per module, the two named baselines, `truncateRunes`, the model-list and timeout fixes |
| `src/tricks/server.nim` | babel `server.nim` | reason/end-guard plumbing, per-slot redaction, new replay fields |
| `src/trick_taking_player.nim` | babel `src/babel_player.nim` | `PLAYER_SCRIPTED=<name>`, **plus the raid 0.1.4 receive-loop fix** |

### The pluggable rule module

```nim
type RuleModule* = object
  id*: string                 ## "euchre" | "spades" | "hearts" | "oh-hell"
  displayName*: string
  partnership*: bool          ## true => positions 0&2 vs 1&3
  deck*: proc(): seq[int] {.nimcall.}
  cardsPerHand*: proc(cfg: GameConfig, hand: int): int {.nimcall.}
  setupHand*: proc(sim: var Sim) {.nimcall.}      ## kitty / up-card / turn-up, first phase
  legalMoves*: proc(sim: Sim): seq[Move] {.nimcall.}
  applyMove*: proc(sim: var Sim, move: Move) {.nimcall.}
  trumpOf*: proc(sim: Sim): int {.nimcall.}       ## -1 = no trump
  leadRestricted*: proc(sim: Sim, card: int): bool {.nimcall.}
  scoreHand*: proc(sim: var Sim): array[Seats, float] {.nimcall.}  ## net_h per SLOT, sums to 0
  swingCap*: proc(cfg: GameConfig, hand: int): float {.nimcall.}
  tell*: proc(sim: Sim, ev: GameEvent): string {.nimcall.}
  rulesText*: proc(): string {.nimcall.}          ## pasted into the system prompt
  audited*: bool                                  ## individual modules only
const Modules* = {"euchre": Euchre, "spades": Spades,
                  "hearts": Hearts, "oh-hell": OhHell}.toTable
```

`Seats = 4` is a compile-time constant, as in babel. Adding a fifth module is one new file plus one
registry line plus one manifest variant — which is what the idea asked for.

### Config (`GameConfig`)

`tokens[]`, `players[{name}]`, `num_agents`, `seed`, **`module`** (`"euchre"|"spades"|"hearts"|"oh-hell"`),
`hands`, `dealSchedule[]` (oh-hell only), `episodeTimeoutSeconds` (1200), `sampled`, `turnDelayMs`
(250; slept **after each completed trick**, not after each card), `player_connect_timeout_seconds`
(180), `model`, `maxOutputTokens` (900), `llmTimeoutSeconds` (20).
Validation, per module: `players.len == 4`; `hands ≥ MinHands = 2`; `module` in the registry;
`oh-hell` requires `1 ≤ dealSchedule[i] ≤ 6` and `dealSchedule.len == hands`; other modules ignore
`dealSchedule`.

### Event vocabulary — the replay's whole language

Every event carries `kind`, `hand` (−1 before the first), `slot` (−1 for table events) and the
optional fields below. `GameVersion = 1`.

| kind | when | payload |
|---|---|---|
| `start` | once, first | `text` = module id |
| `hand` | each hand | `dealer` (position), `hands[4]` = **every slot's dealt cards**, `kitty[]` (euchre), `upcard` (euchre) / `turnup` (oh-hell), `cards` = tricks this hand, `passDir` (hearts: `left`\|`right`\|`across`\|`hold`) |
| `pass` | hearts, per seat | `slot`, `cards[3]`, `other` = receiving slot, `text` = notes |
| `bid` | any bidding decision | `slot`, `action` (`pass`\|`order`\|`alone`\|`name`\|`bid`), `value` (int bid), `suit` (−1 when none), `scripted`, `tell`, `text` = notes |
| `trump` | when trump is settled | `suit`, `slot` = maker (−1 in hearts), `alone` (bool), `text` = e.g. `"stuck dealer"` |
| `discard` | euchre dealer pick-up | `slot`, `card`, `scripted`, `text` = notes |
| `play` | every card played | `slot`, `card`, `trick` (index), `trickPos` (0–3), `legal[]` (the legal set, ≤ 13 ints), `scripted`, `tell` (leads only), `text` = notes |
| `trick` | trick complete | `trick`, `slot` = winner, `cards[]` in play order, `points` (hearts penalty taken) |
| `broken` | spades/hearts, once per hand | `suit` |
| `handEnd` | end of a scored hand | `points[4]` (module-native, per slot), `teamPoints[2]` (null in individual modules), `tricks[4]`, `net[4]`, `text` = e.g. `"march"`, `"euchred"`, `"lone march"`, `"shot the moon"`, `"nil made"` |
| `handVoid` | hard deadline abandoned a live hand | `hand` — not scored, excluded from `H` and `NORM` |
| `audit` | tail, individual modules only | `data` = the §9 matrices |
| `end` | always, last | `text` = `reason`, `data = {handsScored, hands, seed, norm}` |

The wall-clock stop is therefore a **load-bearing recorded event**, applied by the same proc on
record and on playback, so a `deadline` replay re-derives bit-identically to a `complete` one
(particle-worlds, 2026-08-26).

`replayMatch(config, events)` re-derives one frame per event prefix by replaying `bid`/`discard`/
`pass`/`play` through the rules (the deal comes from the recorded `hand` event, not from the seed
— unlike babel, where the schedule is seed-derived, because the audit and the "all hands visible"
replay both need the literal deal). `frames[i]` = the table after `events[0..<i]`.

### The exact state JSON the viewer reads

`frameStateJson(frame)` serialises each frame into exactly this object — the same shape the live
`/global` snapshot carries, so `renderer.js` has one input format for all three views:

```json
{"module": "euchre", "displayName": "Euchre",
 "hand": 3, "hands": 8, "dealer": 2, "seatOrder": [2, 0, 3, 1],
 "trump": 3, "trumpName": "spades", "upcard": 47, "turnup": -1,
 "maker": 1, "alone": false, "broken": true, "passDir": "",
 "phase": "play", "actor": 0, "leader": 1, "trick": 2, "tricks": 5,
 "table": [{"slot": 1, "card": 47}, {"slot": 2, "card": 19}],
 "seats": [{"slot": 0, "pos": 0, "name": "Sprocket", "team": 0,
            "hand": [3, 17, 44], "bid": 4, "made": 2, "tricks": 2,
            "points": 7, "net": 3.0, "score": 0.59, "penalty": 0,
            "void": [false, true, false, false], "notes": "…",
            "acting": false, "sittingOut": false, "dealer": false}],
 "teams": [{"points": 7, "bid": 8, "tricks": 5},
           {"points": 3, "bid": 5, "tricks": 3}],
 "tell": "Cashing a certain winner; probably void in hearts next trick.",
 "handDone": false, "gameDone": false, "reason": ""}
```

`seats[].hand` is the seat's **remaining** cards; an empty array means "redacted or exhausted".
`teams` is `null` in the individual modules. `points` is module-native and legible; `net`/`score`
are §4's numbers. The wasm module wraps the timeline as
`{"type":"replay","protocol":…,"names":…,"policyNames":…,"config":…,"events":…,"results":…,
"states":[<the objects above>]}` — byte-identical to what the live `/replay` websocket sends, which
is why one renderer drives all three views (babel's invariant, kept).

### Replay bytes are self-sufficient

```json
{"protocol": "tricks.replay.v1",
 "names": ["Sprocket", "Gizmo", "Ratchet", "Widget"],
 "policyNames": ["trick-taking-signaller", "trick-taking-follow", "…", "…"],
 "config": {"module": "euchre", "displayName": "Euchre", "seats": 4,
            "hands": 8, "dealSchedule": [], "seatOrder": [2, 0, 3, 1],
            "partnership": true, "swingCaps": [4, 4, 4, 4, 4, 4, 4, 4],
            "norm": 32.0, "seed": 1234567, "sampled": true, "gameVersion": 1},
 "events": [...],
 "results": {...}}
```

Names, policy names, config, seed, the whole event log (including every dealt card) and the results
are all in the bytes. **Nothing else is ever fetched** — no server, no API, only the `.replay` file
from S3. Per-tick state is re-derived in the browser by the same Nim `replayMatch` the server runs.

### Results (`results.json`)

`names[]` (**policy** names, by slot), `scores[]`, `win[]`, `net[]`, `points[]`, `teamPoints[]`
(or `null`), `tricks[]`, `bids[]`, `bidsMade[]`, `penalties[]` (hearts), `moons[]` (hearts),
`marches[]`/`euchres[]` (euchre), `nilsMade[]`/`nilsFailed[]`/`bags[]` (spades), `decisions[]`,
`fallbacks[]`, `forcedMoves[]`, `audit` (object or `null`), `module`, `seats` (4), `seatOrder[]`,
`handsPlayed`, `handsScored`, `hands`, `norm`, `seed`, `reason`
(enum `complete|deadline|budget`).

---

## Server, player, protocol

Babel's `server.nim` with the same routes, the same threading model (one game thread mutating the
match under `stateLock`; the slow model call made **outside** the lock on a snapshot, which is safe
because only that thread mutates), and the same artifact ordering. Routes, unchanged and all
required by the certifier:

```
GET /healthz                 GET /client/global      GET /client/player
GET /client/replay           GET /client/renderer.js GET /client/chrome.css
GET /client/assets/<name>    WS  /player?slot=N&token=T
WS  /global                  WS  /replay
```

Both `/client/` routes serve real pages, registered before any catch-all asset route, and neither
opens the player socket (lantern 0.1.1). `/healthz` and `/global` keep answering — and keep
answering a WebSocket **Ping** with a **Pong**, which mummy hands to the application — for a
bounded ~20 s shutdown grace after the artifacts are written, then the process exits 0
(lantern 0.1.3 → 0.1.4).

**Player protocol `tricks.player.v1`** — babel's frames, unchanged in shape:

- **player → game:** `{"type":"prompt","prompt":str,"scripted":bool,"baseline":"follow"|"tracker"}`.
  `prompt` is capped at **4000 characters, rune-truncated**, server-side. Sent on connect and again
  after `welcome` (the re-send covers a race with slot registration). The latest frame wins for all
  later decisions.
- **game → player:**
  `{"type":"welcome","protocol":"tricks.player.v1","slot":N,"name":<alias>,"module":str,
  "displayName":str,"hands":int,"pos":int,"partner":<alias or null>}`;
  `{"type":"state", …}` after every event batch — **redacted**: every other slot's `hand`,
  `pass` cards and `notes` are removed, the euchre `kitty`/`discard` are removed, `tell` is
  deleted, `audit` is deleted, and `policyNames` is deleted (babel already sends players a
  reduced `playerStateJson`; this extends it to the card fields);
  `{"type":"final","done":true,"scores":[…],"win":[…],"names":[<aliases>],"points":[…],
  "net":[…],"handsScored":N,"reason":str}` at the end, after which the player exits 0.

**Player runnable `/bin/trick-taking-player`:** reads `PLAYER_PROMPT` (or a built-in default
trick-taking personality) and `PLAYER_SCRIPTED`; delivers the prompt; idles until `final`.
**Fix inherited from raid 0.1.4 and NOT present in babel:** the receive loop is wrapped in
`try/except CatchableError` and exits **0** on a dead socket — whisky's `receiveMessage` *raises*
on a close frame, and mummy's `send` only queues, so the game's `quit(0)` can outrun the flushed
`final` frame and the player container exits 1 intermittently.

**Two name spaces, both.** The table (canvas, prompts, feed event text, player frames) uses
anonymous aliases. The spectator layer (replay `policyNames`, the scorebug, the endcard,
`results.names`) maps back to policy names, except that a name matching
`/^baseline(\s*\(\d+\))?$/i` keeps its alias — babel's `makeNameMap` / `isBaselineFiller`
(renderer.js:688–720), kept verbatim.

---

## Viewer

**All four viewer files come from ONE starter — `Metta-AI/cogame-babel` — and from no other.**

| file | from (babel) | into |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | same emscripten link line, three names changed |
| wasm entry `replay-viewer/trick_taking_replay.nim` | `replay-viewer/babel_replay.nim` | same structure, `bab_*` → `tt_*`, same `emscripten_exit_with_live_runtime` epilogue |
| `replay-viewer/static_replay.js` | `replay-viewer/static_replay.js` | the **MODULARIZE factory bootstrap**, matching the link line |
| `replay-viewer/index.html` | `replay-viewer/index.html` | same shell, same ids, wordmark + `<title>` changed, one appended game block |

`client/renderer.js` and `client/chrome.css` come from babel too. **No file is spliced in from
paintbot/ctf, moba, factorio, cosino or bullwhip** — splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks
the viewer silently, with a complete all-200 bundle and no error (cogame-lantern, 2026-08-23). The
coupling that must stay in lockstep:

- `config.nims` links `-s MODULARIZE=1 -s EXPORT_NAME=TrickTakingReplayModule
  -s EXPORTED_RUNTIME_METHODS=HEAPU8
  -s EXPORTED_FUNCTIONS=_main,_malloc,_free,_tt_load_replay,_tt_payload_ptr,_tt_payload_len,_tt_error_ptr,_tt_error_len
  -O2 -s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s ENVIRONMENT=web`, with
  `--mm:arc --exceptions:goto -d:useMalloc -d:release`, output
  `replay-viewer/dist/trick_taking_replay.js` (+ `.wasm`).
- `static_replay.js` calls the **factory** `TrickTakingReplayModule()` and the `_tt_*` exports —
  the same names, byte for byte.
- `index.html` loads `./renderer.js`, `./trick_taking_replay.js`, `./static_replay.js`, in that
  order.

**Load signalling.** `client/renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame**
— babel already does this (renderer.js:1309, after the synchronous first `frame()` draw) and it is
kept — and `static_replay.js` sets `document.documentElement.setAttribute("data-replay-error",
<message>)` **on any failure** (missing `?replay=`, the 20 s `AbortController` fetch timeout, a wasm
rejection) and clears it on retry. `tools/ci/viewer_smoke.mjs` gates on exactly these two
attributes. Babel's 20 s bounded fetch, its `RETRYING REPLAY… (attempt N)` caption and its Retry
button are kept. **One patch to babel's `coworld-replay` postMessage bridge:** babel posts `ready`
from a bare `requestAnimationFrame` pair (static_replay.js:122–124), which can beat the first
painted frame (chorus `3c11c953`, 2026-08-24). `attachReplay` gains an `onFirstFrame` callback,
invoked **immediately after** it sets `data-replay-loaded`, and the shell posts `ready` **only**
from that callback — so the attribute and the bridge can never disagree.

### Chrome provenance

The parley lineage names its chrome differently from the ctf lineage. The mapping is stated once,
and the **rule** is applied unchanged:

| checklist name (ctf lineage) | this repo (babel lineage) | treatment |
|---|---|---|
| `client/chrome_common.js` | `client/chrome.css` + `client/renderer.js` | **copied byte-for-byte** from `/workspace/starters/cogame-babel`, then extended **only** by an appended game block and the named patches below |
| `client/replay_broadcast.html` | `client/replay.html` (live) and `replay-viewer/index.html` (static bundle) | the **starter's page kept whole with a game block appended**, under the banner `<!-- trick-taking additions to the inherited cogame-babel chrome -->` — **never a rewrite that reuses the ids** (cogame-gridlock, 2026-08-23) |

- **`client/chrome.css`** is byte-for-byte babel's, extended only by an appended block fenced
  `/* ==== trick-taking game block (appended; nothing above this line is edited) ==== */`.
  **Kept unmodified:** `@font-face`, the `:root` palette, `#layout`, `#stage`, `#topband`,
  `#wordmark`, `#clock`, `#statuschip`, `#topright`, `#feedtoggle`, `#scorebug`, `.plate*`,
  `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`, `.end-*`, `#transport`,
  `.tbar`, `.tbtn`, `.tpos`, `.scrub*`, `.beat-marker`, `.round-span`, `.round-sep`, `.seat0..4`,
  `#feed`, `.feed-*`, `#loading`.
  **Removed — exactly this and nothing else:** babel's game-specific tail, the final block
  commented `/* Babel: speak lines in the speaker's colour; … */` (`.feed-speak`, `.feed-round`,
  `.feed-pick`, `.plate-pip.hollow`), which the appended block replaces.
  **Appended:** `:root { --orange: #e08a3a; } .seat5 { --tc: var(--orange); }` (babel defines seat
  colours only to `.seat4` while `COLORS` has six entries); `#scorebug { grid-template-columns:
  repeat(4, 1fr); }` (babel hard-codes `repeat(5, 1fr)` for a 4-seat game, leaving a dead column);
  `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (babel's `flex: 0 1 auto` collapses names to
  "…" in the ~360 px featured-match iframe); the new feed classes; the new beat kinds; and the
  `--band`/`--hudscale` consumers.
- **`replay-viewer/index.html` and `client/replay.html`** are babel's pages with a game block
  appended. **Kept verbatim:** `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`,
  `#statuschip`, `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`,
  `#endscreen`, `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`,
  `#loading`, and the trailing `fit()` + `bindFeedToggle` script.
  **Changed:** the wordmark text becomes `TRICK<span>·TAKING</span>` and the `<title>`.
  **Removed from the starter's page: nothing** — every element babel ships is used by this game.
  **Appended:** one `<div id="modulechip">` inside `#topright` (the module badge — `EUCHRE`,
  `SPADES`, `HEARTS`, `OH HELL`) and the `relayout()` bootstrap. The `tell` ribbon and the trump
  indicator are **drawn on the canvas**, not added as DOM overlays.
- **Zoom: dropped. There is no `#viewpanel`.** The card table is a fixed arena that always fits the
  frame; a zoom bar and minimap exist only for boards larger than the frame. Babel ships none and
  none is added.
- **Real art, no placeholders.** Babel's `data/` ships verbatim: `arena_floor.png` (the table
  texture), the four `soldier_{red,blue,green,yellow}_front.png` cog sprites (one per seat), and
  `font.ttf` + `FONT_LICENSE.txt`. Cards are drawn by `drawCardFace` / `drawCardBack` as rounded
  rects with real rank and suit glyphs in the shipped font — **`10`, never `T`**, suits ♣ ♦ ♥ ♠
  with red/ink colouring. No card-image assets are needed and none are invented.

### Named minimal patches to the inherited chrome

Recorded here so the phase-30 diff has them, and so nothing else is touched:

1. **Clickable, labelled beat markers.** Babel's `buildScrub` appends inert
   `<div class="beat-marker">` elements (renderer.js:1182–1188) and seeks only from a click on the
   track. Patch: each beat becomes
   `<button type="button" class="beat-marker <kind> seat<N>" aria-label="Hand 3 · Gizmo takes the trick with J♠" title="…">`
   whose `onclick` calls the same `onSeek` the track uses (so a beat click also dismisses the
   endcard). Drag-to-seek on the track is untouched. The game block's builder is named
   **`buildTrickBeats`, not `markBeat`** — a game-block function named like a chrome alias gets
   shadowed by the hoisted `var markBeat = C.markBeat` (tandem, 2026-08-23), and a
   scope-duplication test covers the alias list.
2. **`relayout()`.** A short function in `renderer.js`, called on `load`, on `resize` and from
   `bindFeedToggle`, measures `#transport` and publishes **on `document.documentElement`
   (`:root`)** — never on `#stage`, where a `:root`-scoped consumer would never see them —
   **`--band`** = `#transport.offsetHeight` in px, and **`--hudscale`** =
   `clamp(0.72, stageWidth / 960, 1.25)`. The appended CSS scales the top band, the scorebug and
   the module chip by `--hudscale`; that is what makes the 360 px case legible.
3. **Rune-safe prompt cap** in `server.nim` (byte slice → `truncateRunes`), §Decisions 1.

### Transport rules

- `#transport` is a **laid-out flex row of `#stage`**, not an overlay, and `#board-wrap` — which
  contains the canvas *and* `#endscreen` — is its sibling directly above. The band's top edge **is**
  the board's bottom edge, by construction.
- `--band` and `--hudscale` are set on `:root` by `relayout()` (patch 2).
- **No overlay sits in the transport band.** The appended game block adds **no** fixed- or
  absolute-positioned element at all (the tell ribbon and the trump indicator are canvas draws);
  any future one must ride `bottom: calc(var(--band, 0px) + …)`.
- **The endcard stops at `var(--band)`.** `#endscreen` keeps babel's `inset: 0` *inside*
  `#board-wrap`, which resolves to exactly `bottom: var(--band)` measured from the stage floor, so
  it can never cover the scrubber; `viewer_smoke.mjs` asserts `#endscreen`'s rendered bottom is
  ≥ `#transport`'s rendered top.
- **The endcard is dismissed by every seek.** `setIndex` calls
  `updateEndscreen(container, results, index >= events.length && events.length > 0, nameMap)` on
  **every** index change (babel renderer.js:1277 — kept), and `updateEndscreen` toggles the `show`
  class every call, so any scrub away from the end takes it down. A test covers it.
- **Scrubber beats are clickable labelled buttons, and every kind emitted has a CSS rule** in the
  appended block:
  `trick` (8 px tick, the trick winner's seat colour) · `bid` (2 px tick, paper-dim; `.bid.nil`
  hollow) · `trump` (amber flag above the track, on the `trump` event) · `march` (tall, the maker's
  seat colour, glowing — a march or a made nil) · `euchred` (tall, red — a set contract or a
  failed nil) · `moon` (violet flag — hearts shot the moon) · `void` (grey X — `handVoid`) ·
  `end` (14 px, amber). One `.round-span` per **hand**, alternating `.alt`, with a `.round-sep`
  between hands. A CI grep asserts every kind `buildTrickBeats` emits has a matching rule in
  `chrome.css`.

### What the viewer draws

- **Canvas** (babel's `draw` replaced by a card-table stage; everything above the stage — layout,
  scorebug, feed, scrubber, endscreen, name map, effects bookkeeping, both drivers, replay pacing
  — is kept): a felt table over `arena_floor.png`, four cogs at N/E/S/W **in table order** (so the
  seeded seating is visible), each seat's hand fanned **face-up** (spectators see everything — the
  idea's "all hands visible"), the current trick's cards laid toward the centre in play order, a
  trump indicator card in the corner, the dealer button, the up-card or turn-up beside the kitty,
  a bid chip and trick pips per seat, a greyed-out fan for a Euchre seat sitting out, and each
  seat's private `notes` on a small parchment beneath it (babel already draws notes parchments —
  kept). The trick winner's cards sweep to the winner with a 420 ms slide, and the verdict tint
  holds ~2 s then fades to a resting level so a paused frame still reads (babel's
  `PICK_HOLD_MS`/`PICK_FADE_MS` mechanism, kept).
- **The `tell` ribbon**: on a `bid` or a lead carrying a `tell`, a paper ribbon unrolls under the
  acting cog with that text, in the acting seat's colour, held for the event's dwell. This is the
  idea's "what your partner just told you" annotation, and it is drawn **downward from the cog with
  the ribbon clamped inside the canvas** — text drawn at a negative coordinate is accepted silently
  by a canvas and reads as a sliver (cogchemists, 2026-08-24). A layout band sized from the
  **server's own caps** (`tell` 120 runes, `notes` 400 runes), measured in the drawing font, is
  reserved for every seat simultaneously; `--strict-text-bounds` is on in CI and
  `canvas_text.never_inside` must be **0**.
- **Top band:** wordmark `TRICK`+`·TAKING`, the module chip, and `#clock` reading e.g.
  `HAND 3 / 8 · ♠ TRUMP · TRICK 2 / 5 · SPROCKET TO PLAY` (hearts: `HAND 2 / 4 · PASS RIGHT ·
  TRICK 4 / 13 · HEARTS BROKEN`; final: `… · FINAL`).
- **Scorebug** (one `.plate` per seat, `repeat(4, 1fr)`): display name (policy name spectator-side,
  alias for baselines), a `D` chip on the dealer and a `▶` chip on the acting seat, the
  module-native **points** as the big number with the label `points`, `bid/made` where the module
  bids, and one pip per trick taken this hand. Partnership modules tint the two partners' plates
  with a shared underline.
- **Feed** (right rail, collapsible, starts collapsed): one block per hand headed
  `HAND 3 — DEALER RATCHET · ♠ TRUMP`, then the hand in words — `Gizmo orders it up`,
  *(dim italic)* `Taking the up-card away: likely the right bower…`, `Bolt leads 10♥`,
  `Sprocket takes trick 2 with J♠`, `Sprocket notes: Gizmo void in ♦ since trick 1`,
  `Makers take 5 — a march, +2` — plus, at the tail, the audit lines for the individual modules
  (`Bolt declined a winnable trick against Gizmo 6/9 times (field 3/11)`) and
  `Final — Sprocket & Ratchet +7 (0.61)`.
- **Endcard** (`#endscreen`, stops at `var(--band)`): `FINAL — 8 HANDS`, the verdict
  (`SPROCKET & RATCHET TAKE THE TABLE`, or the top seat's name in an individual module, or
  `ALL LEVEL`), then ranked rows with `score`, `points`, `tricks`, `bid/made`, and a
  `.end-reason` line when `reason != "complete"`.
- **Legible at 360 px wide** — a requirement, checked at 360 px, not at desktop width. The replay
  page starts feed-collapsed (`bindFeedToggle(…, true)`); the appended block adds
  `@media (max-width: 720px) { #feed { display: none } }` and
  `@media (max-width: 400px) { #wordmark { font-size: 15px } #clock { font-size: 12px }
  .plate-label { display: none } .plate-pips { display: none } }`; `--hudscale` floors at **0.72**
  so no drawn string falls below 11 px; notes parchments drop to one line below 480 px. The three
  things guaranteed readable at 360 px are the trick in the middle of the table, the scorebug
  points, and the endcard.

### Bundle and build hook

The manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` — a **static wasm
bundle, never a pod**; a `/client/replay` live-server viewer is never declared.
`tools/build_replay_viewer.sh` (babel's hook, renamed paths) is the `coworld build` hook: it
compiles `replay-viewer/trick_taking_replay.nim` to wasm with the local `emcc`+`nim` or, failing
that, the pinned `Dockerfile.replay-viewer` emsdk container, asserts
`dist/trick_taking_replay.{js,wasm}` are non-empty, then copies them plus
`replay-viewer/index.html`, `replay-viewer/static_replay.js`, `client/renderer.js`,
`client/chrome.css` and `data/{soldier_*_front.png,arena_floor.png,font.ttf}` into the output dir,
and greps `data-replay` in the copied `static_replay.js`. **It `mkdir -p`s the output's parent
*before* the containment check** — the parent does not exist on a fresh CI checkout (ecos,
2026-08-23). Committed mode 100755.

---

## Packaging

- **`compose.yaml`** — one service, name = coworld name:

  ```yaml
  services:
    trick-taking:
      image: coworld-trick-taking:latest
      platform: linux/amd64
      build: {context: ., network: host}
  ```

  The service name derives the manifest placeholder by uppercasing and replacing `-` with `_`:
  **`{{TRICK_TAKING_IMAGE}}`** — never `{{GAME_IMAGE}}`, which is not a thing (lantern 0.1.0). This
  is the same shape `cogame-liars-dice` (`{{LIARS_DICE_IMAGE}}`) certified with on 2026-08-26.
- **`Dockerfile`** — babel's two-stage nimby build (`nimby 0.1.26`, Nim 2.2.4, `nimby.lock` carried
  over: bitworld, mummy, curly, whisky; `nim.cfg` regenerated inside the image), producing **one
  image with two entrypoints**: `/bin/trick-taking` (game, `CMD`) and `/bin/trick-taking-player`.
  `data/` and `client/` are copied into the run image.
- **`coworld_manifest_template.json`** — babel's, with:
  `$schema`; **≥ 3 top-level `tags`**: `cards`, `trick-taking`, `partnerships`,
  `hidden-information`, `llm-driven`; `game.name: "trick-taking"`; **`game.description` present and
  `game.tags` absent**, **no** top-level `version`, **no** `game.display_name` (pistonball 0.1.0 /
  collab-cooking); `game.owner: "daveey@gmail.com"`;
  `game.replay_viewer: {"bundle": "static-replay-viewer"}` **nested under `game`**;
  `game.runnable: {type: "game", image: "{{TRICK_TAKING_IMAGE}}", run: ["/bin/trick-taking"],
  env: {ANTHROPIC_API_KEY_URI: "secret://coworld/trick-taking/anthropic_api_key"}, source_url}` —
  **the secret namespace is `game.name`**, which here equals the slug, and the release workflow's
  `secret put` step must read it from `game.name`, not from a slug variable (commons-family 0.1.1);
  `episode_timeout_minutes: 20` top-level; `game.config_schema` a real JSON Schema in which
  **every array property declares `minItems` and `maxItems`** (`tokens` 4…4, `players` 4…4,
  `dealSchedule` 1…16 — tandem 0.1.0); `game.results_schema` covering every field in §Sim module
  with `reason` as `enum: ["complete","deadline","budget"]`. **No runner-managed `tokens` appear in
  any `game_config`** (knights-archers 0.1.0) even though `config_schema` still *requires* them.
- **`game.docs`** — `readme: {"type":"text","value":…}` plus
  `pages: [{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…}},
  {"id":"modules.md",…}, {"id":"scoring.md",…}]`: the engine's shared rules; the four modules'
  numbered rules verbatim from §5–§8; how `scores` is computed, its sign, and what the audit does
  and does not claim.
- **`game.protocols`** — **both `player` and `global`**, each a `{"type":"text","value":…}` object
  (bare strings fail the platform validator — garble v0.1.0): `player` = the `tricks.player.v1`
  frames above with the 4000-char prompt cap and the `PLAYER_PROMPT` / `PLAYER_SCRIPTED` recipe;
  `global` = the `/global` snapshot shape, the event vocabulary, and the note that spectators see
  every card, every pass and every note.
- **`player[]`** — three declared runnables, **each seated at least once in the cert fixture**
  (a declared player with no certification slot fails `players_missing` — raid 0.1.3):

  | id | name | run | env | resources |
  |---|---|---|---|---|
  | `trick-taking-player` | Trick-Taking Prompt Player | `/bin/trick-taking-player` | (`PLAYER_PROMPT` at policy-upload time) | requests 100m/64Mi, **limits.cpu `"1"`** |
  | `trick-taking-follow` | Trick-Taking Follow Baseline | `/bin/trick-taking-player` | `PLAYER_SCRIPTED: "follow"` | same |
  | `trick-taking-tracker` | Trick-Taking Tracker Baseline | `/bin/trick-taking-player` | `PLAYER_SCRIPTED: "tracker"` | same |

  `limits.cpu` must be `"1"`; `500m` is below the platform minimum (pistonball 0.1.1).

### Variants — `num_agents` is stated for every one

| variant `id` | name | **`num_agents`** | `players[]` | `game_config` |
|---|---|---|---|---|
| `euchre` | Euchre (partnerships) | **4** | 4 entries | `module: "euchre"`, `hands: 8`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180`, `episodeTimeoutSeconds: 1200` |
| `spades` | Spades (partnerships, bid your tricks) | **4** | 4 entries | `module: "spades"`, `hands: 4`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180`, `episodeTimeoutSeconds: 1200` |
| `hearts` | Hearts (avoid the points) | **4** | 4 entries | `module: "hearts"`, `hands: 4`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180`, `episodeTimeoutSeconds: 1200` |
| `oh-hell` | Oh Hell (predict exactly) | **4** | 4 entries | `module: "oh-hell"`, `hands: 11`, `dealSchedule: [1,2,3,4,5,6,5,4,3,2,1]`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180`, `episodeTimeoutSeconds: 1200` |

Every variant carries a `description` (required by the upload contract) and **`num_agents: 4`
inside `game_config`**. The ladder schedules zero episodes for a variant missing `num_agents`.
Every variant's `game_config` is constructed in a test, not just the fixture's
(collab-cooking 0.1.1).

### Certification fixture

```
certification.game_config: module "euchre", num_agents 4,
  players ["Sprocket","Gizmo","Ratchet","Widget"], seed 7, hands 3,
  turnDelayMs 0, player_connect_timeout_seconds 180
certification.players: [{"player_id":"trick-taking-player"},
                        {"player_id":"trick-taking-player"},
                        {"player_id":"trick-taking-follow"},
                        {"player_id":"trick-taking-tracker"}]
```

**The fixture uses the `euchre` module** — the idea names Euchre "first to certify".
**`num_agents` = 4**, `len(certification.players)` = 4, `len(game_config.players)` = 4, and
`SMOKE_SEATS` / `<SEATS>` in `ci.yml` = **4** — the four independent declarations
`tools/ci/docker_smoke.sh` cross-checks (a `SEAT-COUNT FAIL:` line names which one broke). No
runner-managed `tokens` in the fixture. Three scripted Euchre hands finish in well under a second,
so `coworld certify`'s default 60 s needs no override, while the ~100-event replay they produce
plays for ≈ 90 s — comfortably longer than the 12 s viewer soak.

### Policies (`tools/ci/policies.json`)

Four distinct versions. **Both champions are `PLAYER_PROMPT` policies; both fillers are scripted.**

```json
[{"name":"trick-taking-signaller","run":"/bin/trick-taking-player","env":{"PLAYER_PROMPT":
  "You cannot talk, so your bids and your leads ARE your language. Bid honestly and consistently so your partner can read your strength from the number alone, and lead the suit that tells your partner what you want back: lead a singleton when you want a ruff, lead your longest suit when you want it established, cash an ace when you are about to be void. Track every card played and every void you see, and write both into your notes each turn. When your partner is winning a trick, feed them your lowest card; when an opponent is winning, take it as cheaply as you can. In Hearts, duck everything early and count the queen. In Oh Hell, treat your bid as a contract and steer toward it exactly, over or under."}},
 {"name":"trick-taking-counter","run":"/bin/trick-taking-player","player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","env":{"PLAYER_PROMPT":
  "Play like a card counter. Before every decision, reconstruct from the history exactly which cards of each suit are still out and who can still hold them; a seat that failed to follow a suit can never hold it again, so mark that void and use it. Bid the number your certain winners support and not one more. Lead a card only when you know it wins or when it forces out a card you need gone. Read the other cogs' bids and leads as evidence about their hands and say so in your notes so you still have it next turn. Punish anyone who leads a suit they are known to be short in."}},
 {"name":"trick-taking-follow","run":"/bin/trick-taking-player","env":{"PLAYER_SCRIPTED":"follow"}},
 {"name":"trick-taking-tracker","run":"/bin/trick-taking-player","env":{"PLAYER_SCRIPTED":"tracker"}}]
```

Champion #1 (`trick-taking-signaller`) is submitted for **daveey**; champion #2
(`trick-taking-counter`) is uploaded **while daveey-1 is the active player** (the `"player"` field
above) and submitted for **daveey-1**. `trick-taking-follow` and `trick-taking-tracker` are the
fillers, registered **before** the first `trigger-round`, with UUIDs resolved from
`GET /policy-versions` filtered **client-side** on `policy_name` and matched on the exact `<name>:vN`
from the **last successful** `release-result.json`. The LLM runs **game-side**, so the *game*
runnable needs `ANTHROPIC_API_KEY_URI` in its manifest `env` (above) and the player policies need
**no** `USE_BEDROCK` (that gate is for player-side-LLM lineages — cogolf, 2026-08-24).

### Phase-0 pins, and how each is satisfied

| pin (`playbooks/make-coworld.md` §Phase 0) | how |
|---|---|
| Starter by game shape | Turn-based / cards / hidden information / policy = LLM prompt → `cogame-babel`, row 1 of the starter table (§title paragraph) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-trick-taking`, **public** (private 404s `source-resolves`); the private `coworld-euchre` is reference only |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `trick-taking-signaller` / `trick-taking-counter` (`PLAYER_PROMPT`) and `trick-taking-follow` / `trick-taking-tracker` (`PLAYER_SCRIPTED=<name>`), all `/bin/trick-taking-player` from `{{TRICK_TAKING_IMAGE}}` |
| Starter chrome **verbatim** | §Viewer "Chrome provenance": byte-for-byte `chrome.css`/`renderer.js`, pages kept whole with a game block appended, exactly one CSS block removed, three named patches |
| Transport / endcard / beats | §Viewer "Transport rules": `--band`/`--hudscale` on `:root`, no overlay in the band, endcard stops at `var(--band)` and every seek dismisses it, beats are labelled buttons with CSS for every kind |
| Zoom | `#viewpanel` **dropped** — fixed card table |
| Real art, not placeholders | babel's `arena_floor.png`, four cog sprites and `font.ttf` ship verbatim; cards drawn with real rank/suit glyphs, `10` not `T` |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`, `tools/build_replay_viewer.sh`, all four viewer files from babel; no `/client/replay` viewer declared |
| Replay bytes self-sufficient | §Sim module "Replay bytes": names, policy names, config, seed, every dealt card, events, results — nothing else fetched |
| Two name spaces | anonymous aliases in prompts/table/player frames; policy names in `results.names`, `replay.policyNames`, scorebug and endcard, via babel's `makeNameMap`/`isBaselineFiller` |
| Degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | soft guard 0.55·T = 660 s, hard guard 0.56·T = 672 s, worst-case settle ≈ 717 s ≤ 720 s; retry-once → scripted → lowest-legal; no unbounded wait anywhere |
| `num_agents` in every variant AND the cert fixture | **4** in all four variants, in `certification.game_config`, in `certification.players` (4 entries), and as `SMOKE_SEATS`/`<SEATS>` = 4 |
| Prove it in CI | §Tests: sim units, baseline legality, end-to-end episode + replay, strict-UTF-8 parse, executed viewer smoke |

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` **twice**, debug and `-d:release`.

**`tests/test_cards.nim`** — encoding and comparison:
1. `cardCode`/`parseCard` round-trip over all 52 cards; ten always renders `10`, never `T`; `TH`,
   `10h`, `H10` and `ten of hearts` all parse to the same card; a code outside the deck raises.
2. `beats()` orders every suit `2 < … < 10 < J < Q < K < A`; a trump beats any non-trump; a
   non-trump off the led suit never wins.
3. **Euchre bowers**: the left bower's effective suit is trump, not its printed suit, for
   following, for leading and for winning; the right bower beats the left; the left beats the ace
   of trump; the 9 of trump beats the ace of a side suit.

**`tests/test_sim.nim`** — the engine and the four modules:
1. *Deal*: every module deals `cardsPerHand` to each of 4 seats, from a 52- (24- for euchre) card
   deck, with no card dealt twice and no card missing; `dealer == hand mod 4`.
2. *Follow-suit legality*: over 500 random legal matches per module, `legalMoves` is never empty,
   never contains a card the seat does not hold, and equals "cards of the led suit" exactly
   whenever the seat holds one; `applyMove` raises on every card outside `legalMoves`.
3. *Lead restrictions*: a spade cannot be led before the break unless the hand is all spades; a
   heart likewise; no heart and no Q♠ on trick 0 unless forced.
4. *Euchre rules*: all four scoring outcomes produce the documented points (3–4 → 1, 5 → 2, alone
   5 → 4, ≤ 2 → defenders 2); stick-the-dealer forces a named suit and never a re-deal; the alone
   partner plays no card and is skipped in turn order; the dealer's discard leaves 5 cards.
5. *Spades rules*: contract = the sum of non-nil bids; made → `10·C + bags`; set → `−10·C`; a made
   nil is +100 and a failed nil −100 with its tricks counted as bags; `|teamScore| ≤ 230` over
   10 000 random hands.
6. *Hearts rules*: pass directions cycle left/right/across/hold; a pass is exactly 3 distinct held
   cards; total penalty is always 26; a shot moon gives the shooter 0 and everyone else 26.
7. *Oh Hell rules*: the hook forbids exactly the balanced bid and only for the dealer; exact →
   `10 + bid`, missed → 0; the turn-up sets trump and is never played.
8. *Scoring*: `Σ net == 0` per hand **and** per episode for every module; `Σ scores == 2.0` to
   1e-9; `scores ∈ [0,1]` with no clamp over 2000 random matches per module; a seat that breaks
   even scores exactly 0.5; every module's `swingCap` is never exceeded by any realised `net_h`.
9. *Record → re-derive, for EVERY end reason*: an episode ended `complete`, one ended `deadline`
   (hard guard, with a `handVoid`) and one ended `budget` each re-derive from their event log to a
   **byte-identical** state timeline and identical results — the wall-clock stop is a recorded
   event, not an out-of-band fact (particle-worlds, 2026-08-26).
10. *Events round-trip through JSON* for every kind in the vocabulary, including `handVoid`,
    `audit` and `end`.
11. *Budget fit*: `sampleEpisode` is idempotent, never returns fewer than `MinHands`, caps each
    module's hands at `EpisodeDecisionBudget div worstCaseDecisionsPerHand`, and trims `oh-hell`'s
    `dealSchedule` from the tail; the four shipped variants' worst-case decision counts are
    asserted to be **≤ 240** and their worst-case seconds **≤ 660**.
12. *Rune truncation*: `truncateRunes` never splits a multi-byte rune; a 400-cap applied to a
    string of 4-byte emoji yields valid UTF-8; the resulting replay JSON parses under a **strict**
    UTF-8 decoder.
13. *Manifest cross-check* (`tests/test_manifest.nim`): `game.description` present, `game.tags`
    absent, ≥ 3 top-level tags, **`num_agents` present in every variant and in the certification
    fixture and equal to that variant's `players` length and to 4**, `game.protocols.player` and
    `.global` and `game.docs.readme` are `{type,value}` objects,
    `game.replay_viewer.bundle == "static-replay-viewer"`, every `config_schema` array property
    declares `minItems`/`maxItems`, no `tokens` in any `game_config`,
    `player[].resources.limits.cpu == "1"`, every declared `player[]` id appears in
    `certification.players`, and **every variant's `game_config` constructs a valid `Sim`**.

**`tests/test_audit.nim`**:
1. `auditFromEvents` is a **pure function**: called twice on the same events it returns identical
   JSON; called on the events **after** a JSON round-trip it matches the server's `results.audit`
   byte for byte.
2. A synthetic Hearts hand in which seat 2 holds a winning card and ducks every time seat 5 leads
   raises `yieldRate[2][5]` above `field[2]`; an honest scripted episode leaves them within noise.
3. `results.audit` is `null` for `euchre` and `spades` and non-null for `hearts` and `oh-hell`.
4. `chance`/`yield` are computed from the recorded `legal[]` field only — deleting the hands from
   the event log does not change the output.

**`tests/test_bot.nim`** — the **bounded-orders / legality assertion** on the scripted baselines:
1. `follow` and `tracker` each play **200 complete matches in every module** (euchre, spades,
   hearts, oh-hell) at 4 seats without `applyMove` ever raising: every move is drawn from
   `legalMoves`, every bid is inside the module's range, the Oh Hell dealer never bids the hooked
   value, a Hearts pass is always exactly 3 distinct held cards, and no seat ever acts out of turn.
2. `decide` with no credentials returns the scripted move **immediately**, with no network call.
3. An LLM reply that is unparseable twice yields the scripted move and increments `fallbacks`; a
   baseline move rejected by the engine yields the **lowest legal** move and increments
   `forcedMoves`; the episode still reaches `complete`.
4. `notes` from a hostile reply (5 kB of emoji) is capped at 400 runes and the replay containing it
   parses as **strict UTF-8**.
5. `tell` is produced for every `bid` and every lead in every module, is ≤ 120 runes, and **never
   appears** in any string returned by `systemPrompt`/`userPrompt` for any seat (the no-private-
   channel assertion).

**End-to-end (`docker-smoke` job)** — `tools/ci/docker_smoke.sh` (from coworld-builder
`templates/tools/ci/`, substituted `<slug>=trick-taking`, `<IMAGE>=coworld-trick-taking`,
`<SEATS>=4`, committed **mode 100755**) builds the production image and runs **one real episode of
the certification fixture in raw docker** — one game container plus one player container per seat,
with **no `ANTHROPIC_API_KEY`**, so all four seats play scripted. The game must exit 0, **every
player container must exit 0** (raid 0.1.3), `results.json` must be non-empty valid UTF-8 JSON with
`names`/`scores` of length **4**, and the replay must be non-empty and parse as **strict UTF-8
JSON** (`SMOKE_REQUIRE_REPLAY_JSON=1`). The replay is copied to `dist/smoke/` and uploaded as the
`smoke-replay` artifact.

**Viewer smoke (`wasm-viewer` job, `needs: docker-smoke`)** — **the bundle is EXECUTED, not merely
built.** After `./tools/build_replay_viewer.sh` and the "bundle is complete" assertions
(`index.html` present, a non-empty `.wasm`), the job **downloads the `smoke-replay` artifact** — the
only replay in CI known to be a real, current-format episode of this game — and runs, in headless
Chromium via **Playwright pinned 1.55.0**:

```
node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
  --replay dist/smoke/replay.json --timeout 90 --soak 12 --strict-text-bounds
```

`tools/ci/viewer_smoke.mjs` is copied **byte-for-byte** from coworld-builder
`templates/tools/ci/viewer_smoke.mjs` — no substitutions. It must report `loaded: true`
(`data-replay-loaded="true"` on `<html>`, i.e. a frame was drawn — an all-200 bundle is **not**
evidence; cogame-lantern deadlocked with one), the three scrub readouts (0 %, 50 %, 100 %) must
differ, and `--soak 12` requires uninterrupted playback still to be advancing at the end (cogball
0.1.4 loaded, drew one frame and froze). The 3-hand fixture replay plays for ≈ 90 s, so the soak
window is affordable. `--strict-text-bounds` requires `canvas_text.never_inside == 0` — the card
table is a fixed arena, and this is the gate on the `tell` ribbon, the nameplates and the notes
parchments having somewhere to go.

**A second invocation in the same job** runs the bundle against
`tools/ci/fixtures/hearts_moon.replay` — a committed 4-seat **Hearts** episode carrying a shot
moon, a full-cap 400-rune `notes` on every seat, a full-cap 120-rune `tell`, and a non-null audit —
regenerated and **diffed** by `tests/test_sim.nim` so it can never drift from the format. Reason:
the cert fixture is a scripted Euchre episode and a scripted baseline emits **no notes at all**, so
without this fixture nothing in CI ever draws the LLM-text chrome (cogchemists, 2026-08-24). Both
invocations must exit 0; `viewer-smoke.png` / `viewer-smoke.json` are uploaded **always**.

**Renderer fixture step** — `tools/ci/renderer_fixture.html` loads the real `renderer.js` with a
synthetic state carrying a full-cap `notes` and `tell` on **every** seat at three canvas sizes
(360 × 640, 960 × 640, 1440 × 900) and self-checks its own string lengths; `viewer_smoke.mjs
--strict-text-bounds` runs against it in its own `ci.yml` step.

**Static greps in `ci.yml`** (cheap, and they catch the known silent failures):
`tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` present and **mode 100755**;
`tools/ci/viewer_smoke.mjs` non-empty; `static_replay.js` calls `TrickTakingReplayModule(` **and**
`config.nims` declares `EXPORT_NAME=TrickTakingReplayModule` (the lantern splice); the `_tt_*`
export list in `config.nims` matches the calls in `static_replay.js`; no game-block function name
collides with the chrome alias list (the tandem shadowing); **every beat kind emitted by
`buildTrickBeats` has a matching CSS rule in `chrome.css`**.

---

## Out of scope (v1)

- **Bridge.** The idea calls it the headline variant and it is the right next module — but its
  auction alone (35 contract calls plus pass/double/redouble, a legality lattice, dummy exposure,
  declarer play, vulnerability, part-score/game/slam/rubber scoring, honours) is a larger rule
  surface than all four shipped modules combined, and one run must ship *and certify*. It is the
  first thing the engine's `RuleModule` interface exists for: a `bridge.nim`, one registry line and
  one manifest variant, on top of an engine that will already have been certified in the league.
- **Dou Dizhu.** Asymmetric 1-vs-2 teams at **3 seats**; it breaks the single fixed
  `num_agents: 4` that keeps this run's packaging and cert fixture unambiguous, and it is a
  shedding game, not a trick-taking game — a different engine, not a different rule module.
- **Seat counts other than 4**: 3-, 5-, 6- and 7-player Hearts and Oh Hell, 3-handed Euchre, and
  any variable-seat manifest variant.
- **Audit flags, thresholds, penalties and league-level aggregation.** v1 reports the soft-play
  matrices and nothing more (§The game 9); it never flags a pair, never adjusts a score and never
  disqualifies a seat.
- **Any communication channel.** No chat, no `say` field, no alerts, no announced conventions, no
  pre-episode partnership agreement, no signalling system beyond bids and cards. This is a
  permanent exclusion, not a deferral — it is the game.
- **Spades sandbag rollover** (−100 per 10 accumulated bags), Spades blind nil, Euchre "farmer's
  hand"/throw-in, no-trump and misère contracts, and Hearts' Jack-of-Diamonds and
  no-Q♠-on-the-first-round house rules.
- **Duplicate deals / mirrored seatings** to cancel deal luck across an episode, and cross-episode
  duplicate scoring.
- **Cross-module episodes** (one episode is one module) and per-module leaderboards (one Elo ladder
  over all four variants).
- **Any external dependency**: no OpenSpiel, RLCard or PettingZoo import, and no reuse of
  `coworld-euchre`'s Python/MettaGrid code — the rules are reimplemented natively in Nim per module,
  with those repos as references only.
- **Live `/client/replay` pod viewers**, card-image art assets, a `#viewpanel` zoom bar/minimap,
  per-seat time banks, and any second model call per decision.
