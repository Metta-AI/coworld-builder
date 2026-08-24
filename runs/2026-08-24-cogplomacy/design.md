# cogame-cogplomacy — design note (2026-08-24)

Forked from **`Metta-AI/cogame-bullwhip`** (read at `/workspace/starters/cogame-bullwhip`), because
cogplomacy is exactly bullwhip's shape one size larger: a native-Nim turn game whose seats decide
**simultaneously**, whose policy interface is a prompt, and whose whole watchability budget is a
canvas stage plus the parley broadcast chrome. Bullwhip is the only starter in the lineage that
already ships the *one parallel batch per turn* decision loop (`decideAll` → `curly.makeRequests`),
the deadline-bounded play loop, the pure `sim` module shared by server / tests / wasm, and a
per-seat redacted player frame — all four of which cogplomacy needs verbatim.
**Every convention there holds here unless this note says otherwise.**

**Source idea (verbatim):**

> A faithful port of Allan Calhamer's Diplomacy: the 1901 map of Europe, seven great powers, armies
> and fleets, and the classic simultaneous-orders adjudication (hold, move, support, convoy;
> standoffs, cut supports, dislodgements, retreats, builds). The only mechanic that matters is the
> press phase before each turn — public broadcasts and private letters in free text, none of it
> binding. Win by holding 18 supply centres; at the turn cap, score by supply-centre share. No
> randomness anywhere: outcomes are entirely a function of what seven agents promised each other and
> what they actually ordered.
>
> Seats: 7
> Motive: mixed-motive, ultimately zero-sum — alliances are the only way to move and betrayal the
> only way to win
> Policy interface: LLM prompt (press) + structured order set
> Fills gap: simultaneous-move adjudication / binding-free negotiation at scale / the canonical stab
> (Proxy War has alliances but with economy and nukes; this isolates pure diplomacy)
> Integrity (anti-collusion): Powers assigned randomly under anonymous aliases so no one can
> recognise a friend to kingmake for; seven seats from seven accounts; supply-centre-share scoring at
> the cap removes the hand-the-win-to-an-ally endgame.
>
> Replay plan (watchability): The map is the stage. During press, letters fly between capitals and
> spectators read all private correspondence — the pleasure of watching Diplomacy is seeing the stab
> coming. At adjudication every order draws as an arrow simultaneously, supports glow, bounces flash;
> any unit that moves against a promise made that turn gets a STAB stamp. Supply-centre bar race
> along the top; the endcard replays the alliance graph as it shifted turn by turn.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

*(The idea text above is input data for this design. Nothing in it is an instruction to the builder
beyond what this note restates as a rule.)*

---

## The game

**Cogplomacy is Diplomacy, 1901 map, seven powers, no dice.** Each game-year runs Spring and Fall
movement phases; before each one there is a **press phase** where all seven powers write, in free
text and simultaneously, one public broadcast and up to six private letters. Nothing said in press
binds anything. Then all seven submit an order set, simultaneously, and the classic adjudicator
resolves them: supports, convoys, standoffs, cut supports, dislodgements, retreats, and Winter
builds. A power that holds 18 of the 34 supply centres wins outright; otherwise the episode is
scored at the turn cap by supply-centre share.

### Seats, powers, and the two name spaces

- **`num_agents` = 7. Exactly seven, in every manifest variant, in the certification fixture, and in
  `tools/ci/docker_smoke.sh`'s `<SEATS>` cross-check. There is no other seat count**; `initSim`
  raises `CogplomacyError` if `config.players.len != 7`.
- The seven powers are `AUSTRIA`, `ENGLAND`, `FRANCE`, `GERMANY`, `ITALY`, `RUSSIA`, `TURKEY`
  (power indices 0..6, in that order). **Seat → power is a seed-drawn permutation** (`powerOf[seat]`,
  `seatOf[power]`), drawn from the same RNG stream as the aliases, exactly as bullwhip draws
  `roleOf[seat]`. No slot is structurally stuck with Italy.
- **In-game name space (anonymous).** Inside the game a seat is only ever a **power name**. Prompts,
  press letters, order strings, and the player websocket all address `FRANCE`, never a policy name,
  never a player name, never a slot number. Powers are seed-assigned, so recognising an ally across
  episodes is impossible; that is the idea's anti-collusion pin, and it is enforced by construction
  (`config.players[i].name` is never interpolated into any prompt — `tests/test_sim.nim` asserts it).
  Each seat additionally carries an anonymous **cog alias** (`Sprocket`, `Gizmo`, … from bullwhip's
  `CogNames`, drawn with `tableNames` kept verbatim) which is the display name for any seat whose
  policy name is a baseline filler.
- **Spectator name space (real).** The replay carries `powers[seat]`, `names[seat]` (cog alias) and
  `policyNames[seat]` (the real policy display names from `config.players[i].name`). The viewer's
  name map renders `FRANCE · daveey`; results are attributed by policy name. Policy names never
  cross into the game. Both name spaces are recorded — never one or the other.

### The map

`src/cogplomacy/mapdata.nim` is a static, compiled-in transcription of the standard 1901 board:

- **75 provinces**: 56 land (of which 34 are supply centres) and 19 sea spaces. Each carries a
  3-letter code (`PAR`, `NTH`, `STP`), a full display name (`Paris`, `North Sea`,
  `St Petersburg` — the viewer and feed always print the full name, never the code), a kind
  (`land` / `coast` / `sea`), a supply-centre flag, and a home power (`-1` for neutrals and
  non-centres).
- **Two adjacency tables**, `armyAdj` and `fleetAdj`, because they differ: armies ignore sea spaces,
  fleets move only along coasts and seas. **Three provinces have split coasts** — `SPA/NC`,
  `SPA/SC`, `STP/NC`, `STP/SC`, `BUL/EC`, `BUL/SC` — modelled as distinct fleet nodes that share one
  province for occupancy, ownership and army movement.
- **34 supply centres.** Home centres (22): `VIE BUD TRI` (Austria), `LON EDI LVP` (England),
  `PAR MAR BRE` (France), `BER MUN KIE` (Germany), `ROM VEN NAP` (Italy),
  `MOS WAR SEV STP` (Russia), `CON SMY ANK` (Turkey). Neutrals (12): `NWY SWE DEN HOL BEL SPA POR
  TUN SER RUM BUL GRE`.
- **22 starting units** (Spring 1901): Austria `A VIE, A BUD, F TRI`; England `F LON, F EDI, A LVP`;
  France `A PAR, A MAR, F BRE`; Germany `A BER, A MUN, F KIE`; Italy `A ROM, A VEN, F NAP`; Russia
  `A MOS, A WAR, F SEV, F STP/SC`; Turkey `A CON, A SMY, F ANK`. Starting ownership = each power's
  home centres; the 12 neutrals start unowned.
- `tests/test_map.nim` pins all of it (counts, adjacency symmetry, coast legality, start units).

### The phase cycle

An episode plays `years` game-years starting at 1901 (`years` default **4**, min 1, max 12;
certification fixture 1). Each year is seven phases in this fixed order — the arithmetic that fixes
the default is in *Decisions* below:

| # | phase | who is asked | skipped when |
|---|---|---|---|
| 1 | `spring press` | all live powers | `press: false` |
| 2 | `spring orders` | all live powers | never |
| 3 | `spring retreats` | powers with a dislodged unit | nothing was dislodged |
| 4 | `fall press` | all live powers | `press: false` |
| 5 | `fall orders` | all live powers | never |
| 6 | `fall retreats` | powers with a dislodged unit | nothing was dislodged |
| 7 | `winter builds` | powers whose centre count ≠ unit count | every power is level |

Supply-centre ownership changes **only** at the end of phase 6 (after Fall retreats). There is no
press phase in Winter and none before retreats: press is exactly what the idea says it is — the
thing that happens before a *turn*, i.e. before a movement phase.

**Press is one exchange per movement phase, not a conversation.** All seven write their broadcast
and letters in one simultaneous batch; the letters are delivered before the same phase's order
batch, so a letter can be *acted on* the turn it is sent but can only be *answered* in the next
press phase. This is a budget decision (a second press round costs ~40 s/year, which would cost a
whole game-year); a second round is listed under *Out of scope (v1)*.

### Press: what a power may say, and pledges

A press reply carries a public `broadcast` (every power reads it), up to six private `letters` (one
per other power; only the addressee reads it), up to four **pledges**, and a private `notes`
notebook. **Nothing is binding: the sim never prevents an order that contradicts a pledge.** A
pledge exists only so the stab is *machine-detectable* and therefore drawable:

| pledge | JSON | broken when the pledger's orders this movement phase… |
|---|---|---|
| peace | `{"to":"ITALY","kind":"peace"}` | …move any unit into a province occupied by an Italian unit or into a supply centre Italy owns, **or** support any move into such a province |
| keep out | `{"to":"ALL","kind":"keepout","province":"BUR"}` | …order any unit to move into Burgundy, or support any move into Burgundy |
| support | `{"to":"RUSSIA","kind":"support"}` | …contain no order supporting a Russian unit (hold or move) |

`to` is a power name or `ALL`; an `ALL` pledge is shown to everyone, a targeted pledge is shown to
its addressee (and to spectators immediately). A broken pledge is recorded as a `stab` record inside
the `adjudicate` event, naming the pledge and the offending order, and the viewer stamps **STAB**
over the moving unit. Free-text promises with no pledge are legal and common — they simply cannot be
stamped, and the prompt says so.

### The movement-phase resolution, in order

This is the whole adjudicator. `src/cogplomacy/adjudicate.nim` implements steps 2–8 as a pure
function `adjudicate(board, orders): Adjudication`; the sim runs the rest.

1. **Own-unit filter.** Drop any order naming a province that does not hold a unit of the ordering
   power. If a unit is named twice, keep the first order and drop the rest. Any unit of the power
   with no order at all is given `H` (hold).
2. **Syntax and legality repair.** Each order string is parsed into `(unit, kind, target, aux)`.
   An order is **illegal** if: a fleet is ordered into an inland province or a coast it cannot
   reach; an army into a sea; a move goes to a non-adjacent province with no possible convoy path;
   a support names a destination not adjacent to the supporter; a support or convoy names a unit
   that is not in the named province; an army orders a convoy; a fleet is convoyed; a convoying
   fleet is not in a sea space; or a fleet move to `SPA`/`STP`/`BUL` names no coast **and** two
   coasts are reachable. **Every illegal order becomes `H` for that unit** and is recorded in the
   `orders` event's `illegal` list with a one-word reason (`parse`, `nonadjacent`, `wrongunit`,
   `notthere`, `noconvoy`, `ambiguouscoast`). Where exactly one coast is reachable the coast is
   filled in silently and the order stands. **An illegal order never invalidates the rest of the
   reply.**
3. **Void unmatched supports and convoys.** `X S A - B` counts only if the unit at `A` actually
   ordered a move to `B` (destination including coast must match). `X S A` (support-hold) counts
   only if a unit is at `A` and did not order a move. `F XXX C A org - dst` counts only if the army
   at `org` ordered a move to `dst`. A void support or convoy leaves its unit holding: hold strength
   1, still dislodgeable.
4. **Convoy paths.** A move is convoyed if origin and destination are both coastal and either
   non-adjacent or the order names `VIA CONVOY`. A path exists iff a chain of sea spaces whose
   fleets issued matching convoy orders connects origin to destination. **No path ⇒ the move fails
   and the army holds** (result `noconvoy`). A move between adjacent coastal provinces that also has
   a convoy path resolves as a land move unless `VIA CONVOY` was named (DATC 6.G).
5. **Resolve.** Success/failure of every move and support is computed by the recursive resolver of
   Kruijswijk's *The Math of Adjudication* (`resolve(order)` with `unresolved`/`guessing`/`resolved`
   marks and cycle detection), using the four standard strengths:
   - **hold strength** of a province: 0 if empty, or if its occupier's move succeeds; otherwise
     1 + valid supports-to-hold.
   - **attack strength** of a move: 0 if the path fails; **0 if the destination holds a unit of the
     mover's own power that does not successfully move away** (this is the self-dislodgement ban);
     otherwise 1 + valid supports, **excluding supports given by the power owning the unit standing
     in the destination** (you may not support a foreign attack that dislodges your own unit).
   - **defend strength** (head-to-head only): 1 + all valid supports.
   - **prevent strength**: 0 if the path fails or if the move loses its head-to-head; otherwise
     1 + valid supports.
   A move succeeds iff its attack strength exceeds the destination's hold strength (or, head-to-head,
   the opposing move's defend strength) **and** strictly exceeds the prevent strength of every other
   move to the same destination. Otherwise it bounces.
   Cycles are broken by exactly two backup rules: the **circular-movement rule** (a closed cycle of
   moves with no external interference all succeed) and the **Szykman rule** for convoy paradoxes
   (the convoyed move that creates the paradox fails and its army holds; the convoying fleet's
   dislodgement stands).
6. **Cut supports** (computed inside step 5; called out because it is the rule builders get wrong).
   A support is cut if the supporter's province is the destination of a move with attack strength ≥ 1
   by a unit of a **different power**, except a move originating in the province the support is
   directed *into*. A supporter that is dislodged has its support cut unconditionally. Convoyed
   attacks cut support normally, except where the Szykman rule voided the convoy.
7. **Dislodgements.** A unit is dislodged if a successful move enters its province and it did not
   successfully move away. Record, per dislodged unit, the **attacker's origin province** (barred as
   a retreat destination).
8. **Standoffs.** Every province in which two or more moves bounced is recorded; nothing enters it
   and it is barred as a retreat destination this turn.
9. **Retreat phase** (only when something was dislodged). For each dislodged unit its power orders
   either a retreat to a province that is (a) adjacent and legal for the unit type/coast, (b) empty
   after the movement phase, (c) not the attacker's origin, and (d) not a standoff province — or
   `D` (disband). A missing, unparsable or illegal retreat is a disband. **Two dislodged units
   retreating to the same province: both disband.**
10. **Supply-centre ownership** — Fall only, after retreats. Every supply centre occupied by a unit
    becomes that unit's power's; unoccupied centres keep their owner. Emit the `centres` event.
    Immediately check the solo condition (below).
11. **Winter adjustments.** `delta = centres − units`. `delta > 0`: the power may build up to `delta`
    units, each in a **vacant home supply centre it still owns** (fleets only in coastal home
    centres; `STP` requires a named coast); unbuilt entitlement is waived. `delta < 0`: the power
    must disband exactly `−delta` units. Missing or illegal builds are waived; missing or illegal
    disbands are resolved by the **civil-disorder rule** — disband the unit furthest (BFS on its own
    movement graph) from the nearest home centre the power owns, ties broken by alphabetical
    province code. Then check the end conditions.
12. **Elimination.** A power with zero units and zero centres after step 11 is eliminated: it writes
    no press, receives no order/retreat/build call, and scores 0. Its seat still receives state
    frames (with `"eliminated": true`) until the final frame.

### Scoring, its sign, and what the league ranks by

Let `c_i` be the supply centres power `i` owns when the episode ends and `TotalCentres = 34`.

- **Solo.** If any power owns **≥ 18** centres at step 10 (or is the only power still owning any
  centre), that power scores **1.0** and every other seat scores **0.0**. The episode ends there.
- **Otherwise** (turn cap or deadline): `score_i = c_i / 34`.

Higher is better; scores are in `[0, 1]` and sum to ≤ 1 (unclaimed neutrals dilute everybody
equally, so taking a neutral is worth the same to every power — that is why the denominator is the
constant 34 rather than the number of owned centres). **The league ranks by mean episode score.**
Results also report `centres`, `units`, `powers` and `soloist`.

The idea pins both halves of this ("win by holding 18 … at the turn cap, score by supply-centre
share"), so the note takes it literally: plain share, not sum-of-squares, and a discontinuous 1.0
for the solo because the idea calls 18 a *win*. Share-at-the-cap is also the anti-kingmaking pin:
handing your centres to an ally at the end lowers your own score one-for-one.

### End conditions and the legal `results.reason` values

Exactly three values are legal in `results.reason`:

| value | when |
|---|---|
| `"solo"` | a power reached ≥ 18 centres at a Fall ownership update, or is the last power owning any centre. `results.soloist` is its power name. |
| `"complete"` | the configured `years` were played out, through the final Winter adjustment. `soloist` is `""`. |
| `"deadline"` | the episode clock stopped play **between phases**. Scores use the ownership table as it stands (i.e. the last completed Fall update, or the 1901 home centres if play stopped before Fall 1901). `soloist` is `""`. |

`resultsJson` emits `""` for `reason` only while the sim is still running; a written result always
carries one of the three.

### Per-seat observation — exactly what is visible and what is hidden

Diplomacy is a game of public position and private intent. Visible to every seat, every phase:

- the **whole board**: every unit on it, with its power, kind (`A`/`F`), province and coast;
- the **ownership table**: all 34 supply centres and their owner (or `neutral`), plus every power's
  centre and unit count;
- **the last two years of history**: every power's submitted orders and every order's result
  (Diplomacy reveals all orders after adjudication), the retreats and the builds;
- **all public broadcasts** from the current press phase and the previous one;
- **the private letters and pledges addressed to this seat** in the current press phase (and the
  previous one), each labelled with its sender's power;
- in the orders phase, **the complete list of legal orders for each of this seat's own units**,
  written in the exact notation the reply must use (a unit's list is ordered hold, moves,
  support-holds, support-moves, convoys; the 1901 map never yields more than ~40 per unit and the
  builder caps the list at 64 defensively);
- **its own private notes**, fed back verbatim.

Hidden from a seat, always:

- **private letters and pledges not addressed to it** — a seat never learns that France wrote to
  Russia, nor what was in it (**spectators and the replay see every letter, immediately**; that is
  the whole point of the replay plan);
- the other powers' **pending orders for the current phase** (this is what makes the game
  simultaneous);
- other powers' **private notes**;
- the other seats' policy names, player names, slot indices and cog aliases.

There is no hidden state in the sim beyond those: no dice, no fog of war, no shuffled deck. "No
randomness anywhere" is literal — the only draw from the seed is the seat→power permutation and the
cog aliases, both fixed before Spring 1901.

### Integrity

Seven seats, seven distinct policies scheduled by the league (`num_agents: 7`). Powers are
seed-assigned and identities are power names only, so a policy cannot recognise, address, or reward
a specific counterparty across episodes. Share-at-the-cap scoring removes the endgame in which an
allied pair hands one of them the win. All three are properties of the rules above, not of
operational policy.

---

## Decisions: LLM with scripted fallback

Transport, credentials, the JSON-only output contract, `extractJsonObject`, `cleanText`, the Bedrock
model list and "no credentials ⇒ every seat scripted" are ported from bullwhip `src/bullwhip/llm.nim`
unchanged. What changes is the batch structure, the reply schemas and the baselines.

### One parallel batch per phase

All seven seats decide simultaneously by rule, so **every phase fires its requests as ONE
`curly.makeRequests` batch** — never seat by seat:

- `press` batch: all live powers (7 requests).
- `orders` batch: all live powers (7 requests).
- `retreats` batch: only powers with a dislodged unit (1–4 requests, usually 0–2).
- `builds` batch: only powers whose `delta ≠ 0` (0–7 requests).

Seats registered as scripted, and every seat when the LLM client is disabled, are answered from the
baselines without touching the network — as in bullwhip, that fallback is load-bearing for offline
certification.

### Episode budget — the arithmetic, out loud

`PlayBudgetFraction = 0.6` of the episode timeout (`COWORLD_TIMEOUT_SECONDS` when the platform sets
it; otherwise `config.episodeTimeoutSeconds`, default **1200 s**) ⇒ **720 s of play**. The deadline
is checked **before every batch**; past it the sim settles with `reason = "deadline"`.

Per batch: seven requests in flight at once, so a batch costs one model round-trip, not seven.
Measured shape for haiku-class models at `maxOutputTokens = 1200`: 8–20 s per batch, bounded above
by `llmTimeoutSeconds = 45`.

```
typical year = press(S) 20 + orders(S) 20 + retreats(S) 10×0.5
             + press(F) 20 + orders(F) 20 + retreats(F) 10×0.9
             + builds(W) 10                       ≈ 105 s
             + pacing (turnDelayMs 300 × ~12 transitions)  ≈   4 s
             ------------------------------------------------------
                                                    ≈ 110 s / year
4 years ≈ 440 s of the 720 s budget; the remaining 280 s absorbs slow batches and retries.
```

That is why **`years` defaults to 4** (1901–1904). The `gunboat` variant has no press batches
(≈ 70 s/year) and therefore runs **6** years in the same budget. Worst case — every batch hitting
the 45 s ceiling plus a retry round — the pre-batch deadline check stops play at ≤ 720 s; the
episode then spends at most one in-flight batch (≤ 45 s) plus ~2 s writing artifacts, ending under
770 s against a 1200 s kill. **The episode settles early rather than overrunning; an overrun episode
is discarded and keeps nothing.**

A solo at 18 centres is rule-complete and reachable in a long game, but in a 4-year episode the
practical outcome is decided by supply-centre share. That is deliberate and stated in `rules.md`.

### Prompts

Two system prompts (press and orders) plus two short ones (retreats, builds), all built in
`src/cogplomacy/llm.nim`. The system prompt for a seat playing France, abbreviated to its skeleton
(the builder writes it out in full; this is the required content and wording):

```
You are FRANCE, one of seven great powers in a game of Diplomacy on the 1901 map of
Europe. The other powers are AUSTRIA, ENGLAND, GERMANY, ITALY, RUSSIA and TURKEY, each
played by a different cog. You never learn who plays them.

Rules:
- Armies move on land, fleets on coasts and seas. Every unit has equal strength; a unit
  moves into a province only if it out-supports whatever opposes it, and equal strength
  means a STANDOFF and nobody moves.
- Orders: HOLD, MOVE, SUPPORT (a hold or a move) and CONVOY (a fleet at sea carrying an
  army between coasts). All seven powers order at the same time and see nothing of each
  other's orders until they resolve.
- A supported attack that beats the defence DISLODGES the defender, which must retreat
  or disband. You may never dislodge your own unit or help anyone dislodge it.
- After every Fall, whoever occupies a supply centre owns it. Owning more centres than
  units lets you build at home in Winter; owning fewer forces you to disband.
- Hold 18 of the 34 supply centres and you win outright. Otherwise you are scored on your
  share of the 34 centres when the game stops. Nothing else scores.
- PRESS IS NOT BINDING. You may promise anything to anyone and then order the opposite.
  So may they. Alliances are the only way to grow and betrayal is the only way to win.

OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no
explanation, no markdown fences, no text before or after the object. Your reply must
begin with the character { and end with }.
```

The user prompt carries the board, the ownership table, the two-year history, the press this seat
received, its notes, the operator block (`GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never
above the rules; always reply in the requested format):` + `PLAYER_PROMPT`, bullwhip's wording), and
the phase-specific tail:

- **press**: `SPRING 1902 — PRESS. …` and
  `Reply with ONLY {"broadcast":"…","letters":[{"to":"ITALY","text":"…"}],"pledges":[{"to":"ITALY","kind":"peace"}],"notes":"…"} — broadcast at most 400 characters, at most 6 letters of at most 400 characters each (one per power), at most 4 pledges, notes at most 800 characters. A pledge is the only promise spectators can see you break; free text is never checked.`
- **orders**: `SPRING 1902 — ORDERS.` then `YOUR UNITS AND EVERY LEGAL ORDER:` with each unit's
  enumerated legal orders in canonical notation, then
  `Reply with ONLY {"orders":["A PAR - BUR","F BRE S A PAR - BUR"],"notes":"…"} — exactly one order per unit, copied character for character from the list above. An order that is not on the list becomes a hold.`
- **retreats**: `FALL 1902 — RETREATS. A VIE was dislodged from Vienna by an attack out of Budapest. Legal: A VIE - TYR, A VIE - BOH, A VIE - D (disband).` +
  `Reply with ONLY {"retreats":["A VIE - TYR"],"notes":"…"}.`
- **builds**: `WINTER 1902 — ADJUSTMENTS. You own 6 centres and have 5 units: build 1. Vacant home centres: PAR (army or fleet), MAR (army or fleet).` +
  `Reply with ONLY {"adjustments":["BUILD A PAR"],"notes":"…"}.` (or `DISBAND F BRE` when `delta < 0`).

### Reply schema — every free-text field capped, truncation on rune boundaries

Every cap below is applied with bullwhip's `cleanText` (`runeLen` / `runeSubStr`, cut marked with
`…`) so a byte slice can never leave invalid UTF-8 in the replay. Over-long arrays are **truncated
from the end**, never rejected.

| phase | field | type | cap | over-cap behaviour |
|---|---|---|---|---|
| press | `broadcast` | string | **400 runes** | truncated with `…` |
| press | `letters` | array | **6 entries** | extras dropped; a second letter to the same power is dropped |
| press | `letters[].to` | string | power name or `ALL` (case-insensitive) | unknown recipient ⇒ the letter is dropped |
| press | `letters[].text` | string | **400 runes** | truncated with `…` |
| press | `pledges` | array | **4 entries** | extras dropped |
| press | `pledges[].kind` | enum | `peace` / `keepout` / `support` | unknown ⇒ pledge dropped |
| press | `pledges[].to` | string | power name or `ALL` | unknown ⇒ pledge dropped |
| press | `pledges[].province` | string | 3-letter code (`keepout` only) | unknown ⇒ pledge dropped |
| press | `notes` | string | **800 runes** | truncated with `…` |
| orders | `orders` | array of strings | **34 entries**, each **32 runes** | extras dropped; an over-long string is `parse`-illegal ⇒ hold |
| orders | `notes` | string | **800 runes** | truncated with `…` |
| retreats | `retreats` | array of strings | **12 entries**, each **32 runes** | extras dropped |
| retreats | `notes` | string | **800 runes** | truncated |
| builds | `adjustments` | array of strings | **10 entries**, each **32 runes** | extras dropped |
| builds | `notes` | string | **800 runes** | truncated |
| player→game | `prompt` | string | **4000 runes** (bullwhip's `MaxPromptLen`) | truncated |

A reply is **invalid** (and only then) if it is not a JSON object, or the phase's required key is
missing or not an array/string of the right kind. Illegal *contents* — a bad order, an unknown
recipient — are repaired per the table and never invalidate the reply.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

Two, both deterministic, both silent (no broadcast, no letters, no pledges, no notes), both
guaranteed to emit only legal orders by construction:

**`expander`** (default; the fallback for every failed decision):

1. Compute BFS distance, on the unit's own movement graph, from every province to the nearest
   supply centre the power does **not** own.
2. Rank each unit's legal moves: (a) a move into an **unowned neutral** supply centre; (b) a move
   into a supply centre owned by another power and **not** occupied by a unit; (c) a move that
   strictly reduces the BFS distance above; (d) hold. Within a rank, ties break by destination
   province code, ascending.
3. Walk units in ascending province-code order and claim destinations; a destination already claimed
   by one of the power's own units is skipped, so **the baseline never stands itself off**.
4. If a unit's own best option is rank (c) or (d) and another of the power's units has claimed a
   destination adjacent to this unit, the unit issues `S <that unit> - <that destination>` instead.
5. In Fall, ranks (a) and (b) are taken even when they leave a home centre uncovered; in Spring a
   move that vacates an owned, otherwise-unoccupied home centre drops one rank.
6. Retreats: the legal retreat destination with the smallest BFS distance to an unowned centre;
   ties by province code; disband when no legal destination exists.
7. Builds: fill vacant owned home centres in province-code order, a fleet if the centre is coastal
   and the power holds fewer fleets than armies, otherwise an army (`STP` builds `F STP/SC`).
   Disbands use the civil-disorder rule of resolution step 11.

**`hedgehog`** (the wall): every unit holds; a unit adjacent to a supply centre the power owns that
is occupied by one of its own units issues `S` for that unit's hold instead (first such neighbour by
province code); retreats go to the legal destination closest to a home centre the power owns, else
disband; builds are always armies in the lowest-code vacant home centre. It never attacks anybody
and never grows past its start — the partner that a prompt can safely ignore and the neighbour that
cannot be talked into anything.

`parseScriptKind` accepts `expander` / `1` / `true` / `yes` → `skExpander`, `hedgehog` / `turtle` →
`skHedgehog`, anything else → `skNone`.

### Degrade, never hang

- **Per seat, per batch:** a transport error, a timeout, a non-JSON reply, or a reply missing the
  phase's required key ⇒ the seat joins **one** retry batch carrying the hint
  `Your previous reply was invalid. Respond with ONLY the requested JSON object.` Still failing ⇒
  the seat is answered by **`expander`** for that phase (silence for a press phase). Logged as
  `cogplomacy: seat N falling back to scripted decision`.
- **Auth failure** (401/403) disables the client for the rest of the episode; 429 and Bedrock
  model-access denials rotate the model candidate, exactly as bullwhip does.
- **A seat that never delivers a prompt** by the time play starts (`player_connect_timeout_seconds`,
  default 180) plays `expander` for the whole episode; a seven-seat game must not stall on one late
  container.
- **Episode clock:** checked before every batch and before every phase transition. Past 60 % of the
  timeout ⇒ `endEarly()` ⇒ `reason = "deadline"`, results and replay written immediately. A short
  honest episode always beats a long one that never lands.
- **Pacing** (`turnDelayMs`, default 300, certification 0) is bounded by
  `PacingBudgetMs = 60_000` in total, spread over the phases (`sampleEpisode` divides, as bullwhip's
  does).
- Nothing in the sim can loop forever: the adjudicator's recursion is bounded by the number of
  orders (≤ 34), the resolver's cycle detection terminates on the two backup rules, and BFS is over
  a 75-node graph.

---

## Sim module

Pure rules, no IO, shared by the server, the tests and the wasm viewer — bullwhip's discipline,
one module per concern.

### `src/cogplomacy/mapdata.nim` (new)

Compiled-in constants: `Provinces` (75 records: code, name, kind, isCentre, homePower, coasts),
`ArmyAdj` / `FleetAdj` adjacency tables, `SupplyCentres` (34 ids), `HomeCentres[7]`, `StartUnits`
(the 22 above), `PowerNames = ["AUSTRIA","ENGLAND","FRANCE","GERMANY","ITALY","RUSSIA","TURKEY"]`,
`PowerAdjectives = ["Austrian","English",…]` for the feed. No procs beyond `provinceByCode`,
`isAdjacent`, and `bfsDistance`.

### `src/cogplomacy/types.nim` (fork of `src/bullwhip/types.nim`)

`CogplomacyError`; `PlayerConfig`; `GameConfig` (bullwhip's with `years` replacing `weeks` and
`press: bool` replacing `talk`); `Unit` (`power, kind: ukArmy|ukFleet, province, coast`);
`OrderKind` (`okHold, okMove, okSupportHold, okSupportMove, okConvoy`); `Order`
(`power, unit, kind, target, targetCoast, auxFrom, auxTo, viaConvoy, raw, illegal, why`);
`OrderResult` (`order, outcome: orSuccess|orBounce|orVoid|orNoConvoy|orDislodged|orCut|orIllegal`);
`Letter` (`fromPower, toPower, text`); `Pledge` (`fromPower, toPower, kind, province, broken,
brokenBy`); `Season` (`seSpring, seFall, seWinter`); `PhaseKind` (`pkPress, pkOrders, pkRetreats,
pkBuilds`); `EventKind`; `GameEvent`; `defaultGameConfig()`; `update()`.

`defaultGameConfig`: `years: 4, press: true, episodeTimeoutSeconds: 1200, turnDelayMs: 300,
playerConnectTimeoutSeconds: 180, model: "claude-sonnet-5", maxOutputTokens: 1200,
llmTimeoutSeconds: 45`.

### `src/cogplomacy/orders.nim` (new)

Canonical notation, one grammar for parsing and printing: `A PAR H`, `A PAR - BUR`,
`A PAR - BUR VIA CONVOY`, `F BRE S A PAR - PIC`, `F BRE S A PAR`, `F ENG C A LON - BRE`,
`F STP/SC - BOT`, `A VIE - D` (retreat disband), `BUILD F STP/SC`, `DISBAND A MOS`. Exports
`parseOrder`, `formatOrder`, `legalOrders(board, unit): seq[string]`, `legalRetreats`,
`legalBuilds`. Parsing is whitespace- and case-tolerant and accepts `-`, `–`, `->` for a move and
`S`/`SUPPORT`, `C`/`CONVOY`, `H`/`HOLD`/`HOLDS`; nothing else.

### `src/cogplomacy/adjudicate.nim` (new)

`adjudicate(board: Board, orders: seq[Order]): Adjudication` — steps 2–8 of the resolution order,
pure and total. `Adjudication` carries `results: seq[OrderResult]`, `dislodged: seq[Dislodgement]`
(`unit, attackerFrom`), `standoffs: seq[int]` (province ids), and `moved: seq[(unit, dest)]`.
No RNG, no IO, no exceptions on legal input.

### `src/cogplomacy/sim.nim` (fork of `src/bullwhip/sim.nim`)

Constants: `Seats = 7`, `Powers = 7`, `TotalCentres = 34`, `SoloCentres = 18`, `MinYears = 1`,
`MaxYears = 12`, `StartYear = 1901`, `PacingBudgetMs = 60_000`, `MaxBroadcastLen = 400`,
`MaxLetterLen = 400`, `MaxLetters = 6`, `MaxPledges = 4`, `MaxNotesLen = 800`,
`MaxOrderLen = 32`, `CogNames` (bullwhip's, verbatim).

`Sim` object: `config`, `names` (aliases), `powerOf[7]`, `seatOf[7]`, `units: seq[Unit]`,
`owner: array[34, int]` (power index or −1), `year`, `season`, `phase`, `pending: set[seat]`,
`press: seq[Letter]` (this phase), `pressLast: seq[Letter]`, `pledges: seq[Pledge]`,
`orders: array[7, seq[Order]]`, `lastAdjudication: Adjudication`,
`dislodged: seq[Dislodgement]`, `history: seq[TurnRecord]`, `centresHistory: seq[array[7, int]]`,
`notes: seq[string]`, `eliminated: array[7, bool]`, `done`, `reason`, `soloist`, `events`.

API mirrors bullwhip's: `initSim`, `sampleEpisode` (clamps `years`, divides `turnDelayMs` into
`PacingBudgetMs`, idempotent via `sampled`), `pendingSeats`, `applyPress(seat, broadcast, letters,
pledges, notes, scripted)`, `applyOrders(seat, orders, notes, scripted)`, `applyRetreats`,
`applyBuilds` — **the last pending seat of a phase resolves the phase and opens the next** —
`endEarly`, `centres(seat)`, `score(seat)`, `resultsJson`, `tableStateJson`, `replayMatch`,
`eventToJson`, `eventFromJson`.

### Event vocabulary (flat `GameEvent`, JSON via `eventToJson` / `eventFromJson`)

Nine kinds. Every field a viewer needs is typed on the event; no free-form `JsonNode` rides in the
log, so the wasm parse stays strict.

| kind | fields |
|---|---|
| `start` | `year` = 1901, `powers` (seat → power index), `units` (the 22 start units), `owners` (34 entries) |
| `phase` | `year`, `season`, `phaseKind`, `units`, `owners`, `counts[7]` — the derived board, **checked** against the seeded re-derivation in `replayMatch` (bullwhip's `week`-event discipline) |
| `press` | `year`, `season`, `seat`, `power`, `broadcast`, `letters` (`to`, `text`), `pledges`, `scripted`, `text` = the seat's notes after the reply |
| `orders` | `year`, `season`, `seat`, `power`, `orders` (normalised strings), `illegal` (`raw`, `why`), `scripted`, `text` = notes |
| `adjudicate` | `year`, `season`, `results` (one `OrderResult` per order of every power), `dislodged`, `standoffs`, `stabs` (`seat`, `power`, `pledgeTo`, `kind`, `province`, `order`) |
| `retreat` | `year`, `season`, `seat`, `power`, `moves` (`unit`, `to` or `"D"`), `scripted` |
| `build` | `year`, `seat`, `power`, `adjustments` (`action`, `unit`), `waived`, `scripted` |
| `centres` | `year`, `owners` (34), `counts[7]`, `gained`/`lost` per power — the bar-race frame |
| `end` | `year`, `text` = reason, `counts[7]`, `soloist` |

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"seats":[{"power":"FRANCE","name":"Sprocket","centres":6,"units":5,"score":0.176,
           "pending":true,"eliminated":false,"stabbedThisTurn":true,
           "broadcast":"…","lettersOut":[{"to":"ITALY","text":"…"}],
           "pledges":[{"to":"ITALY","kind":"peace","broken":true}],
           "notes":"…"}, ×7 by seat],
 "seatOfPower":[3,0,5,1,6,2,4],
 "units":[{"power":2,"kind":"A","province":"PAR","coast":"","dislodged":false}, …],
 "owners":[{"centre":"PAR","power":2}, … ×34],
 "arrows":[{"kind":"move|support|convoy","from":"PAR","to":"BUR","aux":"",
            "power":2,"outcome":"success|bounce|void|noconvoy|cut|illegal"}, …],
 "stabs":[{"power":2,"pledgeTo":"ITALY","kind":"peace","order":"A VEN - TRI"}],
 "standoffs":["BUR"],
 "year":1902,"season":"spring","phase":"orders",
 "years":4,"yearsPlayed":1,
 "counts":[[3,3,3,3,3,4,3],[4,4,5,4,3,5,4], …],
 "press":[{"from":"FRANCE","to":"ITALY","text":"…","public":false}, …],
 "gameDone":false,"reason":"","soloist":""}
```

`press` in the frame is **every** letter of the phase, public and private, because this is the
spectator/replay frame — the idea's "spectators read all private correspondence". The redacted
player frame (below) is a different, smaller object.

### `resultsJson` — platform-facing, policy names

```json
{"names":[7 policy names],"powers":[7 power names],"scores":[7 floats in 0..1],
 "centres":[7 ints],"units":[7 ints],"years":<played>,"maxYears":<cap>,
 "soloist":"FRANCE"|"","reason":"solo|complete|deadline"}
```

### Replay payload — `cogplomacy.replay.v1`

```json
{"protocol":"cogplomacy.replay.v1","names":[aliases],"policyNames":[real names],
 "powers":[7 power names by seat],
 "config":{"years":4,"seed":7,"press":true,"sampled":true},
 "events":[…],"results":{…}}
```

Replay mode and the wasm viewer add `"states"` (one `tableStateJson` per event prefix). **The bytes
are self-sufficient**: the seed re-derives the seat→power permutation and the aliases; the events
carry every press letter, every pledge, every order, every adjudication result, every retreat, every
build and every ownership table; the config carries the fitted year cap; `policyNames` carries the
spectator name space. The viewer contacts nothing but S3 for the `.replay` file.

---

## Server, player, protocol

### `src/cogplomacy/server.nim` (fork of `src/bullwhip/server.nim`)

Same skeleton: mummy router (`/healthz`, `/client/global`, `/client/player`, `/client/replay`,
`/client/renderer.js`, `/client/chrome.css`, `/client/assets/@name`, `WS /player`, `WS /global`,
`WS /replay`), same `stateLock` discipline, same `writeArtifact`, same "final frames to players
before the artifacts are written" ordering, same Ping→Pong answer (the certifier pings `/global`),
same `PlayBudgetFraction = 0.6`.

The game loop is replaced with the phase loop: check the deadline → snapshot the sim → collect the
phase's pending seats → run **one** `decideAll` batch outside the lock → apply each decision under
the lock (the last apply resolves the phase and opens the next) → broadcast → pace. A decision that
`applyOrders` rejects wholesale (it cannot: illegal orders are repaired, not rejected) falls back to
`expander`, matching bullwhip's belt-and-braces `try/except` around the apply.

### Player protocol — `cogplomacy.player.v1`

JSON text frames on the websocket named by `COWORLD_PLAYER_WS_URL`.

- game → player, on connect:
  `{"type":"welcome","protocol":"cogplomacy.player.v1","slot":N,"power":"FRANCE","years":4,"press":true}`
- game → player, after every event — **redacted**: the whole public board (Diplomacy hides no
  positions) plus this seat's own press inbox, and nothing of other powers' pending orders, private
  letters or notes:
  ```json
  {"type":"state","slot":N,"power":"FRANCE","year":1902,"season":"spring","phase":"orders",
   "years":4,"yearsPlayed":1,"centres":6,"units":[…own units…],
   "board":[…every unit…],"owners":[…34…],"counts":[7 ints],
   "inbox":[{"from":"ITALY","text":"…","public":false}],
   "eliminated":false,"started":true,"done":false,"reason":""}
  ```
- game → player at the end:
  `{"type":"final","done":true,"slot":N,"scores":[7],"centres":[7],"units":[7],"powers":[7],"names":[7 aliases],"years":int,"reason":str,"soloist":str}` — the final frame carries **aliases**,
  not policy names (bullwhip's rule).
- player → game: `{"type":"prompt","prompt":"…","scripted":"expander"}` — the prompt (≤ 4000 runes)
  *is* the policy; `scripted` `"expander"`/`"1"` or `"hedgehog"` registers that seat as rule-based;
  `""` means LLM-driven. The reference player sends it immediately on connect and again after
  `welcome`.

### Global protocol

`WS /global` sends the full `tableStateJson` snapshot after every event, plus `type`, `game`,
`policyNames`, `events` (the append-only transcript, including every private letter), `started`,
`done`, `connected`. `/client/global` renders the map live; `/client/replay` plays a recorded
episode; the static bundle renders hosted replays.

### `src/cogplomacy_player.nim` (fork of `src/bullwhip_player.nim`)

Reads `PLAYER_PROMPT` and `PLAYER_SCRIPTED`, delivers one `prompt` frame, then spectates until
`final` and exits. Default prompt when `PLAYER_PROMPT` is unset: *"Grow steadily. Open with an
alliance against the neighbour who threatens you most, keep your promises while they are profitable,
and take the supply centres you can hold. Never leave a home centre uncovered in Fall."*

---

## Viewer

**All four viewer files come from one starter — `Metta-AI/cogame-bullwhip` — and only from it:**
`replay-viewer/config.nims`, the wasm entry `replay-viewer/cogplomacy_replay.nim` (fork of
`replay-viewer/bullwhip_replay.nim`), `replay-viewer/static_replay.js` and
`replay-viewer/index.html`. Nothing is spliced in from any other starter. Bullwhip's emscripten link
flags are kept exactly as they are — `-O2`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`,
`ENVIRONMENT=web`, `MODULARIZE=1`, `EXPORT_NAME=CogplomacyReplayModule`,
`EXPORTED_RUNTIME_METHODS=HEAPU8`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_cp_load_replay,_cp_payload_ptr,_cp_payload_len,_cp_error_ptr,_cp_error_len`,
plus `emscripten_exit_with_live_runtime()` — and `static_replay.js` keeps calling the module through
that same `CogplomacyReplayModule()` factory with the same `_malloc` / `HEAPU8.set` /
`_cp_load_replay` handshake. (cogame-lantern, 2026-08-23: one starter's shell on another's link
flags deadlocks silently with every asset returning 200.)

**Load signalling.** `renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame** —
bullwhip already does exactly this at the end of `attachReplay`'s `makeRenderer` callback
(`client/renderer.js:1390`), kept verbatim. On any failure (missing `?replay=`, the 20 s fetch
timeout, a non-200, a wasm rejection) `static_replay.js` sets
`document.documentElement.setAttribute("data-replay-error", <message>)`, shows a Retry button and
posts the `coworld-replay` `error` envelope; it removes the attribute on a successful retry.
`tools/ci/viewer_smoke.mjs` reads exactly these two signals.

**Bundle.** The manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` — **a static
wasm bundle, never a `/client/replay` pod**. `tools/build_replay_viewer.sh` (bullwhip's, paths
renamed) is the `coworld build` hook, committed `chmod +x`; it compiles
`replay-viewer/cogplomacy_replay.nim` to wasm (locally with `emcc`, otherwise in the pinned
`emscripten/emsdk` container from `Dockerfile.replay-viewer`) and copies `cogplomacy_replay.js`,
`cogplomacy_replay.wasm`, `index.html`, `static_replay.js`, `client/renderer.js`,
`client/chrome.css`, `data/map1901.json` and the `data/` art into the bundle. The wasm module runs
the **same Nim sim and the same adjudicator** the server ran, so every frame — every arrow, every
bounce, every ownership flip — is re-derived in the browser from the replay bytes.

### Chrome provenance — what is copied and what is appended

The pins name `client/chrome_common.js` and `client/replay_broadcast.html`. **The bullwhip lineage
ships neither file**; those two roles are held by **`client/renderer.js` + `client/chrome.css`**
(the shared chrome: topband, scorebug, feed, scrubber, transport, endscreen, name map, effects, both
drivers, replay pacing) and **`client/replay.html`** (the broadcast page; `replay-viewer/index.html`
is the same page with local asset paths). Nothing is imported from a starter that does have them.
The rule is applied to those files:

- **`client/chrome.css` is copied byte-for-byte** from `cogame-bullwhip`; a single
  `/* ---------- Cogplomacy ---------- */` block is **appended at the end**. No existing rule is
  edited or deleted — the file already accretes one appended block per game in this lineage. The
  appended block contains exactly: `:root { --band: 96px; --hudscale: 1; }` (set for real by
  `relayout()`); `.plate-power`, `.plate-centres`, `.plate-units`, `.plate-stab` (a red STAB chip)
  and a seventh seat colour class `.seat6` / `.violet2` to complete bullwhip's six-colour palette;
  `#centrebar` (the appended game element) sized with `font-size: calc(11px * var(--hudscale))`;
  `.beat-label` plus a rule for **every beat kind the scrubber emits** — `.beat-marker.press`
  (paper, 8 px), `.beat-marker.orders` (seat-tinted, 10 px), `.beat-marker.adjudicate` (amber,
  14 px), `.beat-marker.stab` (red, 16 px), `.beat-marker.retreat` (dim red, 8 px),
  `.beat-marker.build` (green, 10 px), `.beat-marker.centres` (amber, 12 px), `.beat-marker.end`
  (amber, 3 × 16 px); feed colours `.feed-press`, `.feed-letter`, `.feed-broadcast`, `.feed-pledge`,
  `.feed-order`, `.feed-bounce`, `.feed-dislodge`, `.feed-stab`, `.feed-centres`, `.feed-build`,
  `.feed-illegal`, `.feed-notes`; `#loading { bottom: var(--band); }` so the caption never sits over
  the transport; and the small-screen queries (`@media (max-width: 640px)` shortens `#centrebar` to
  counts and hides `.plate-units`; `@media (max-width: 420px)` keeps bullwhip's
  `#scorebug { grid-template-columns: repeat(2, 1fr); }` — with seven plates that is four rows).
- **`client/replay.html` is bullwhip's page with a game block appended** — never a rewrite that
  reuses the ids (cogame-gridlock, 2026-08-23). **Every element the starter ships is kept, with its
  id:** `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`,
  `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`,
  `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, and the
  `fit()` + `bindFeedToggle` bootstrap. **Elements removed: none.** The only edits are (a) the
  wordmark's inner text `BULL<span>WHIP</span>` → `COG<span>PLOMACY</span>` and the `<title>`, and
  (b) **one appended element**: `<div id="centrebar"></div>` inserted between `#scorebug` and
  `#board-wrap`. `replay-viewer/index.html` gets the identical treatment (same page, `./` asset
  paths, the `cogplomacy_replay.js` / `static_replay.js` script tags).
- **Zoom: `#viewpanel` is dropped entirely.** Bullwhip ships no zoom bar and no minimap and none is
  added. The map is **always scaled to fit the canvas** (aspect-preserving, from the province
  polygon bounding box), so the board is never larger than the frame and pan/zoom controls would be
  dead weight. Legibility at small widths is handled by the automatic action box below, which takes
  no user input and therefore needs no panel.

### Transport rules

- `--band` and `--hudscale` are set **on `:root`** (`document.documentElement`) by a `relayout()`
  added to the page bootstrap (`client/replay.html` and `replay-viewer/index.html`), called on
  `load`, on `resize`, and from the existing feed-toggle resize event: it measures `#transport`'s
  `offsetHeight` into `--band` and sets `--hudscale = clamp(0.8, width / 960, 1.15)`. Bullwhip's
  `fit()` is called from the same function, so the canvas and the custom properties can never
  disagree.
- **Nothing is overlaid in the transport band.** `#transport` is the last child of `#stage` in
  normal flex flow; the only absolutely-positioned overlays (`#lightpool`, `#grain`, `#endscreen`)
  live inside `#board-wrap`, which ends where the band begins, and `#loading` is pinned above it
  with `bottom: var(--band)`.
- **The endcard stops at `var(--band)`** — `#endscreen` is `position: absolute; inset: 0` inside
  `#board-wrap`, whose bottom edge is exactly `var(--band)` above the page bottom — **and every seek
  dismisses it**: `attachReplay`'s `setIndex` calls `updateEndscreen(container, results, index >=
  events.length && events.length > 0, …)` on *every* index change and `updateEndscreen` does
  `container.classList.toggle("show", !!show)`. Bullwhip's code, kept verbatim.
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` is kept verbatim except that each
  beat is created as `<button type="button" class="beat-marker …">` carrying an `aria-label`/`title`
  and an `onclick` that seeks to that event index; the container keeps its drag-to-seek pointer
  handlers. Beats are emitted for `press`, `orders`, `adjudicate`, `retreat`, `build`, `centres`,
  `end`, and an extra `stab` beat for every stab inside an `adjudicate` — labelled in words:
  `"S1902 · PRESS · France writes to Italy"`, `"S1902 · ORDERS · France"`,
  `"S1902 · ADJUDICATION"`, `"STAB · France breaks peace with Italy"`,
  `"F1902 · RETREAT · Austria"`, `"W1902 · BUILD · France +1"`, `"F1902 · CENTRES · France 6"`,
  `"FINAL"`. The appended CSS defines a rule for **each of those eight kinds**. Season spans replace
  bullwhip's round spans: one span per phase, a separator each game-year.
- **Naming guard** (cogame-tandem, 2026-08-23): the appended game block's builders are named
  `markDiploBeat` / `buildCentreBar`, never `markBeat` / `buildScrub`, so nothing can be shadowed by
  a chrome alias assignment; `tests/test_viewer.nim` asserts no top-level name in the appended block
  collides with a name the chrome defines above it.

### The stage — the map of Europe

**Real art, not placeholders.** `data/map1901.json` is a hand-authored vector map committed with the
repo: for each of the 75 provinces a polygon (8–24 points) in a 1000 × 800 space, a label anchor, a
supply-centre dot position, and a coast anchor for each split coast. It is drawn by `renderer.js` in
bullwhip's Ink & Print palette: land in paper tones tinted toward the owning power's seat colour,
seas in muted ink-blue with the starter's `arena_floor.png` as a paper grain, supply centres as
amber stars (filled when owned, hollow when neutral), province names in `font.ttf`. Units are drawn
as tokens: an **army** is a seat-coloured block with the power's initial, a **fleet** a
seat-coloured pennant; bullwhip's four cog sprites are reused as the power portraits in the scorebug
plates (the seventh and sixth seats use the violet/orange palette entries `renderer.js` already
defines).

The phases play as the idea's replay plan asks:

- **Press phase:** letters fly. Each private letter animates as a paper envelope crossing from the
  sender's capital to the recipient's, seat-coloured, and lands in the feed; broadcasts unfurl as a
  banner across the top of the map. Pledges hang as small wax seals on the recipient's capital.
- **Orders phase:** each power's units get an amber dashed halo while the table waits on that power
  (`pending`), so the simultaneity is visible.
- **Adjudication:** **every order draws at once** — moves as arrows from province anchor to province
  anchor, supports as a short glowing brace from the supporter to the supported arrow, convoys as a
  dashed sea path. Successful arrows are solid and travel; bounced arrows flash red at the
  destination and snap back with a `STANDOFF` tag on the province; dislodged units shudder and go
  grey; a unit whose move breaks a pledge made that turn gets a red **STAB** stamp over it and its
  power's plate gets the `STAB` chip for that turn.
- **Ownership flip:** at the `centres` event, captured centres flip colour with a stamp and the bar
  race animates.
- **Small screens:** below 640 px the canvas draws an **action box** instead of the whole map — the
  bounding box of every province named in the current phase's orders, padded by one province and at
  least 40 % of the map — chosen deterministically by `computeLayout`, with no controls.

### Readouts

- **`#clock`** (top band): `SPRING 1902 · PRESS · WAITING ON 7`, `SPRING 1902 · ORDERS · ORDERS IN`,
  `FALL 1902 · ADJUDICATION`, `WINTER 1902 · BUILDS`, `FINAL · FRANCE 9 CENTRES`.
- **`#centrebar`** (appended, the supply-centre bar race along the top): one seat-coloured segment
  per power, width ∝ centres, labelled `FRANCE 6` inside the segment when it fits and above it when
  it does not, plus a grey `NEUTRAL 4` tail for unclaimed centres; it animates on every `centres`
  event and carries a thin 18-centre solo line.
- **`#scorebug`**: seven plates — `FRANCE · daveey · 6` with the centre count as the big figure, a
  small `5 units` label, `▶` while the table waits on that seat, a red `STAB` chip on the turn it
  broke a pledge, and a grey `OUT` chip once eliminated.
- **`#feed`** (the log), grouped by phase head (`SPRING 1902 · PRESS`, `SPRING 1902 · ORDERS`,
  `FALL 1902 · ADJUDICATION`, `WINTER 1902`), all in words a casual spectator can read:
  - `France broadcasts: "Burgundy is nobody's. Let us all keep out of it."`
  - `France → Italy (private): "Piedmont is yours if Trieste is mine."`
  - `France pledges peace to Italy.`
  - `France orders Paris → Burgundy; Brest supports Paris → Burgundy.`
  - `Germany's Munich → Burgundy bounces. STANDOFF in Burgundy.`
  - `Austria's Trieste is dislodged by Venice (supported by Rome) and retreats to Albania.`
  - `STAB — France promised Italy peace and ordered Marseilles → Piedmont.`
  - `Fall 1902 centres: France 6 (+1 Belgium), Italy 4, Germany 5, Austria 3 (−1 Trieste)…`
  - `Winter 1902 — France builds an army in Paris. Austria disbands a fleet in Trieste.`
  - `Final — France 9 of 34 centres (0.265) after 4 years.` and
    `Episode deadline — scored on the centres held after Fall 1903.` when `reason == "deadline"`,
    `France holds 18 centres — SOLO VICTORY.` when `reason == "solo"`.
  - Illegal orders are shown, dim: `Turkey ordered Ankara → Rumania — not adjacent; Ankara holds.`
- **`#endscreen`**: title `FINAL — 4 YEARS · 34 CENTRES`; verdict `<name> (FRANCE) LED EUROPE`, or
  `<name> (FRANCE) SOLOED ON 18` for a solo; a reason line for `deadline`; rows ranked by score with
  columns `power`, `centres`, `units`, `stabs`, `score`. Below the rows the **alliance graph
  replays**: seven nodes in a ring in seat colours, an edge for every pledge made, green while kept
  and snapping red on the turn it was broken, auto-advancing one game-year per second in a loop —
  the endcard the idea asks for. It is inside `#endscreen`, so it stops at `var(--band)` and is
  dismissed by every seek.

### Legible at 360 px wide

The canvas re-fits on every `relayout()`. **The whole viewer is legible at 360 px:** below 640 px
the map switches to the action box (above), province names drop to the current phase's provinces
only, `#centrebar` shows counts without power names, the plates drop `units` and keep `power` +
centre count, and the feed collapses behind bullwhip's existing `LOG »` toggle; below 420 px the
scorebug goes to two columns. `.plate-name` keeps bullwhip's `flex: 1 1 auto; min-width: 3.2em` so
policy names do not collapse to ellipses in the ~360 px featured-match iframe. Everything renders as
words and numerals — `Burgundy`, `STANDOFF`, `6 centres` — never internal notation like `p42`,
`u3` or `okSupportMove`.

---

## Packaging

- **`compose.yaml`** — service **`cogplomacy`** (= the coworld name), `image:
  coworld-cogplomacy:latest`, `platform: linux/amd64`, `build: {context: ., network: host}`. The
  manifest image placeholder is derived from this service name — **`{{COGPLOMACY_IMAGE}}`** —
  because `coworld build` maps compose services to placeholders and hard-fails anything else
  (cogame-lantern 0.1.0, 2026-08-23).
- **`Dockerfile`** — bullwhip's, renamed: one image, two entrypoints, `/bin/cogplomacy` (default
  `CMD`) and `/bin/cogplomacy-player`; `client/` and `data/` copied into the run image; `nim.cfg`
  regenerated from the container's package tree. **`Dockerfile.replay-viewer`** — bullwhip's,
  renamed (pinned emsdk + nimby + Nim 2.2.4).
- **`cogplomacy.nimble`**, `nimby.lock` — bullwhip's, renamed; same pinned dependency set
  (`bitworld`, `curly`, `mummy`).
- **`.github/workflows/ci.yml`** and **`coworld-release.yml`** from `coworld-builder/templates/`,
  substituting `<slug>` = `cogplomacy`, `<IMAGE>` = `coworld-cogplomacy`, **`<SEATS>` = `7`**.
  `tools/ci/docker_smoke.sh` and `tools/ci/viewer_smoke.mjs` are copied from the same templates
  (`viewer_smoke.mjs` verbatim, no substitutions), both committed executable where required.

### `coworld_manifest_template.json`

- `game.name` = `cogplomacy`; `game.runnable.image` = `{{COGPLOMACY_IMAGE}}`, `run`
  `["/bin/cogplomacy"]`, `env.ANTHROPIC_API_KEY_URI` =
  `secret://coworld/cogplomacy/anthropic_api_key`; `source_url`
  `https://github.com/Metta-AI/cogame-cogplomacy/tree/main` (repo **public** — a certification
  prerequisite).
- **`game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.**
- `config_schema` (`additionalProperties: false`, required `tokens`, `players`): `tokens` and
  `players` `minItems: 7, maxItems: 7`; **`num_agents` integer `minimum: 7, maximum: 7`**; `seed`
  integer; `years` integer 1..12 default 4; `press` boolean default true;
  `episodeTimeoutSeconds` 60..6000 default 1200; `turnDelayMs` 0..10000 default 300; `model` string
  default `claude-sonnet-5`; `maxOutputTokens` 64..2000 default 1200; `llmTimeoutSeconds` 5..300
  default 45; `player_connect_timeout_seconds` number default 180.
- `results_schema` (`additionalProperties: false`, all required): `names`, `powers`, `scores`
  (7 numbers, `minimum: 0`, `maximum: 1`), `centres`, `units` (7 integers each), `years`,
  `maxYears`, `soloist`, `reason` — all arrays `minItems: 7, maxItems: 7`.
- **`game.protocols`** carries **both** entries: `player` (the `cogplomacy.player.v1` text
  description above, including "a policy is just a prompt" and the `PLAYER_SCRIPTED` values) and
  `global` (the `/global` snapshot shape, the event vocabulary, and the note that the events array
  carries every private letter for spectators).
- **`game.docs`** carries `readme` (what the game is, that a policy is a prompt, how to field one)
  **and** `pages`: `rules.md` (phases, the twelve-step resolution order, press and pledges, scoring
  and its sign, the three end reasons) and `map.md` (the 75 provinces with codes and full names, the
  34 supply centres, the split coasts, the starting units, and the order notation grammar with
  examples).

### Player runnables

| id | name | env | purpose |
|---|---|---|---|
| `cogplomacy-player` | Cogplomacy Prompt Player | `PLAYER_PROMPT` (secret-env at upload) | the reference policy: a prompt |
| `cogplomacy-expander` | Cogplomacy Expander Baseline | `PLAYER_SCRIPTED=expander` | the scripted greedy bot |
| `cogplomacy-hedgehog` | Cogplomacy Hedgehog Baseline | `PLAYER_SCRIPTED=hedgehog` | the scripted wall |

All three run `/bin/cogplomacy-player` from the **same image** — LLM policy and scripted baseline
are one image, env-switched, from day one. `tools/ci/policies.json` seeds the league's two prompt
champions, `cogplomacy-diplomat` (alliance-first) and `cogplomacy-opportunist` (stab-timing), both
`PLAYER_PROMPT` policies; the two scripted baselines are the fillers.

### Variants — `num_agents` in every one

| id | name | game_config |
|---|---|---|
| `standard` | Standard game | `players`: 7 named entries, **`num_agents: 7`**, `years: 4`, `press: true`, `turnDelayMs: 300`, `player_connect_timeout_seconds: 180` |
| `gunboat` | Gunboat (no press) | `players`: 7 named entries, **`num_agents: 7`**, `years: 6`, `press: false`, `turnDelayMs: 300`, `player_connect_timeout_seconds: 180` |

### Certification fixture

```json
"certification": {
  "game_config": {
    "players": [{"name":"Sprocket"},{"name":"Gizmo"},{"name":"Ratchet"},{"name":"Widget"},
                {"name":"Bolt"},{"name":"Piston"},{"name":"Flywheel"}],
    "num_agents": 7, "seed": 7, "years": 1, "turnDelayMs": 0,
    "player_connect_timeout_seconds": 180
  },
  "players": [{"player_id":"cogplomacy-player"},{"player_id":"cogplomacy-expander"},
              {"player_id":"cogplomacy-player"},{"player_id":"cogplomacy-hedgehog"},
              {"player_id":"cogplomacy-expander"},{"player_id":"cogplomacy-player"},
              {"player_id":"cogplomacy-hedgehog"}]
}
```

**`num_agents: 7`** appears here and in both variants; `<SEATS>` in `tools/ci/docker_smoke.sh` is
`7`, an independent cross-check that fails CI if the manifest ever disagrees.

### Design pins (playbook §Phase 0) — how each is satisfied

| pin | how |
|---|---|
| Starter by game shape | `cogame-bullwhip` — turn-based, native rules, policy = prompt, simultaneous decisions already batched. Named at the top with the reason. |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-cogplomacy`, public; `source_url` points at `/tree/main`. |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `cogplomacy-player` (`PLAYER_PROMPT`) and `cogplomacy-expander` / `cogplomacy-hedgehog` (`PLAYER_SCRIPTED`), all `/bin/cogplomacy-player` from `{{COGPLOMACY_IMAGE}}`. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` viewer is declared. |
| Real art, starter chrome verbatim | Hand-authored `data/map1901.json` vector map in the starter's palette; `chrome.css` byte-for-byte + appended block; `replay.html` = starter page + one appended `#centrebar`; nothing removed. |
| Two name spaces | In-game: power names only (seed-assigned) + cog aliases; spectator-side: `policyNames` in the replay, rendered by the name map. Both recorded. |
| Degrade, never hang | 60 % play budget (720 s), deadline checked before every batch, retry-once → scripted fallback, `reason = "deadline"` settles early. |
| `num_agents` everywhere | 7 in `standard`, 7 in `gunboat`, 7 in the certification fixture, 7 as `<SEATS>`. |
| Replay bytes self-sufficient | names, policyNames, powers, config (years/seed/press/sampled), every press letter and pledge, every order and result, every ownership table, the results object. |

---

## Tests

CI (`ci.yml`) is the only harness; the sandbox runs none of this locally. Every `tests/*.nim` runs
twice, debug and `-d:release`.

### `tests/test_map.nim` — map integrity

75 provinces; 56 land / 19 sea; exactly 34 supply centres with the listed codes; every home centre
maps back to its power; **adjacency is symmetric** in both `armyAdj` and `fleetAdj`; no army
adjacency touches a sea; no fleet adjacency touches an inland province; the three split-coast
provinces expose exactly the documented coasts and each coast's fleet adjacency is a subset of the
province's; the 22 start units are legal for their provinces; `bfsDistance` is finite from every
land province to some supply centre.

### `tests/test_adjudicate.nim` — the classic adjudication cases

Hand-built boards, one assertion each, named after the rule (the DATC numbers in comments):

1. **Move to an empty province succeeds**; move to an occupied province with equal strength bounces.
2. **Standoff**: two unsupported moves to the same province — both bounce, both units stay.
3. **Three-way standoff**, and a standoff province is barred as a retreat destination.
4. **Supported attack dislodges**: `A BUD - VIE` + `A TRI S A BUD - VIE` beats `A VIE H`.
5. **Cut support**: `A VIE - TRI` cuts `F TRI S A ALB - GRE`, so the Greek attack fails.
6. **Support is not cut by an attack from the province it supports into** (the classic exception).
7. **Dislodging a supporter always cuts its support**, even from the supported direction.
8. **Self-dislodgement ban**: a power's supported move into its own unit's province fails; the own
   unit is not dislodged.
9. **A power may not support a foreign attack that dislodges its own unit**: the support does not
   count toward attack strength.
10. **Beleaguered garrison**: two equal supported attacks on one province — both bounce, the
    defender survives.
11. **Circular movement**: three units moving in a ring all succeed; a ring with an external attack
    that beats one link makes the whole ring fail.
12. **Convoy succeeds** with one fleet and with a chain of three.
13. **Convoy disruption**: the convoying fleet is dislodged ⇒ the army stays in its origin
    (`noconvoy`), and the army's own province is not vacated.
14. **Convoy with an alternative path** survives one fleet's dislodgement.
15. **Szykman convoy paradox** (the classic "convoy cuts the support that would save the convoy"):
    the paradoxical convoyed move fails, the convoying fleet's dislodgement stands.
16. **Support matching**: `F BRE S A PAR - PIC` is void when the army ordered `- GAS`; the fleet
    holds.
17. **Illegal-order repair**: a fleet ordered inland, an army ordered to sea, a support of a
    non-adjacent destination, a convoy by an army, and an ambiguous `F MAO - SPA` each become a hold
    with the documented `why`.
18. **Coast disambiguation**: `F BOT - STP` resolves silently to `STP/SC` (only one coast is
    reachable); `F MAO - SPA` with both coasts reachable is `ambiguouscoast` ⇒ hold.
19. **Retreat rules**: cannot retreat to the attacker's origin, to a standoff province, or to an
    occupied province; two units retreating to the same province both disband.
20. **Head-to-head**: `A PAR - BUR` vs `A BUR - PAR` bounce; with one support the stronger dislodges.

### `tests/test_sim.nim` — the episode

Phase sequencing (`press → orders → retreats? → press → orders → retreats? → builds`, retreats and
builds skipped when empty); ownership changes **only** after Fall retreats; build entitlement equals
`centres − units` and builds are only allowed in vacant owned home centres; disband count is exact
and civil disorder picks the documented unit; the solo check fires at 18 centres and at
last-power-standing; `endEarly` yields `reason = "deadline"` and scores on the standing ownership;
`resultsJson` shape and score sign (all in `[0, 1]`, sum ≤ 1, solo = 1.0 / 0.0); press caps
(`broadcast`, letter `text`, `notes`) truncate **on rune boundaries** with a multi-byte/emoji
fixture and the result is valid UTF-8; a seventh letter and a fifth pledge are dropped; a letter to
an unknown power is dropped; policy names never appear in any prompt built by `llm.nim`
(`userPrompt`/`systemPrompt` scanned for every `config.players[i].name`); event JSON round-trips
(`eventFromJson(eventToJson(e)) == e`) for all nine kinds; `replayMatch` re-derivation gives
`frames.len == events.len + 1` and a final frame equal to the live `tableStateJson`; two `initSim`
calls with the same seed give the same permutation, the same aliases, and byte-identical event logs.

### `tests/test_bot.nim` — bounded-orders / legality assertion on the scripted baselines

Seven `expander` seats play full episodes for seeds 1..8: **every submitted order parses and is
legal** (`illegal` is empty in every `orders` event), every unit is ordered exactly once, no power
ever stands itself off, every retreat is a legal destination or a disband, every build is in a
vacant owned home centre with the right unit kind, build/disband counts match `delta` exactly, and
the episode always reaches `reason = "complete"`. The same for seven `hedgehog` seats, plus a mixed
table (4 `expander`, 3 `hedgehog`). Array bounds: no reply array exceeds its cap. `decideAll` with
no credentials returns scripted decisions for all seven seats without a network call. Reply parsing:
fenced JSON, prose-wrapped JSON, a missing `orders` key (invalid ⇒ retry), an oversize order string,
and an unknown pledge kind.

### `tests/test_score.nim`

Share formula on hand-built ownership tables (including unclaimed neutrals: shares sum to
`owned/34 < 1`); a solo at exactly 18 gives `1.0` / `0.0`s; an eliminated power scores `0.0`; a
`deadline` stop before Fall 1901 scores the home centres (`3/34`, `4/34` for Russia).

### `tests/test_viewer.nim`

`tableStateJson` carries every key the renderer reads (asserted against a literal key list); the
replay payload is **strict UTF-8** (`validateUtf8($payload) == -1`) and re-parses with `parseJson`
after a press fixture full of multi-byte text; the appended viewer block defines no name that the
copied chrome already defines.

### CI jobs

- **`test`** — every `tests/*.nim`, debug and release.
- **`docker-smoke`** — builds the production image and runs one **end-to-end episode in raw docker
  with seven player containers** from the certification fixture's seat mix (no LLM credentials, so
  every seat plays a baseline), asserting `results.json` validates against `results_schema`,
  `reason == "complete"`, seven scores, and that the written `.replay` **parses as strict UTF-8
  JSON** and carries `events`, `results`, `names`, `policyNames`, `powers` and `config`. The seat
  count comes solely from `certification.game_config.num_agents` and is cross-checked against
  `SMOKE_SEATS=7`. The replay is uploaded as the `smoke-replay` artifact.
- **`wasm-viewer`** (`needs: docker-smoke`) — builds the bundle with `./tools/build_replay_viewer.sh`
  (asserting the hook is present and executable), asserts `index.html` and a non-empty `.wasm`, then
  **executes the bundle**: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer
  --replay dist/smoke/*.replay --timeout 90` in headless chromium, which fails unless
  `data-replay-loaded="true"` appears (and fails immediately on `data-replay-error`). Screenshot and
  JSON uploaded always.

---

## Out of scope (v1)

- **A second press round per movement phase** (letters that can be answered before orders) — the
  budget arithmetic above costs a whole game-year for it; revisit if batch latency drops.
- **Draws, DIAS votes and concession** — an episode ends only by solo, cap, or deadline.
- **Variant maps and other power counts** (Ancient Med, Chaos, 2–6 player variants). Seven seats,
  1901 Europe, full stop.
- **Sum-of-squares or rank-based scoring**, and any bonus for surviving — the idea pins plain
  supply-centre share.
- **Forged or anonymous press** (letters that lie about their sender), press in Winter or before
  retreats, and attachments of order sets to letters.
- **Build-anywhere / any-vacant-centre build rules**, and the "Winter 1900" opening build phase.
- **Cross-episode memory** of any kind; each episode starts from 1901 with fresh notes.
- **Zoom/pan controls and a minimap** — the map is always fitted to the frame.
- **Retreat-phase press, per-unit order timers, and partial-turn resubmission.**
