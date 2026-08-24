# cogame-cogiavelli — design note (2026-08-24)

*(In-repo path: `docs/plans/2026-08-24-cogiavelli-design.md`. This copy is `runs/2026-08-24-cogiavelli/design.md`.)*

Forked from **`Metta-AI/cogame-babel`** (read at `/workspace/starters/cogame-babel`), the parley
lineage's current template: a native-Nim turn game whose rules live in one pure `sim` module that
the server, the tests **and** the wasm replay viewer all drive; whose policy interface is a prompt
delivered over a websocket; whose replay is a static wasm bundle built by
`tools/build_replay_viewer.sh`; and whose chrome (`client/renderer.js`, `client/chrome.css`,
`client/replay.html`, `replay-viewer/index.html`, `replay-viewer/static_replay.js`,
`replay-viewer/config.nims`) is exactly the scorebug/feed/scrubber/endcard furniture Cogiavelli
needs. **Every convention there holds here unless this note says otherwise.** Two deliberate
imports from babel's descendant `cogame-bullwhip` (read at `/workspace/starters/cogame-bullwhip`)
are named where they occur, and only these two: the **batched decision loop**
(`decideAll` → `curly.makeRequests`, `src/bullwhip/llm.nim:425-478`, driven from
`src/bullwhip/server.nim:291`), because babel's `client.decide` asks one seat at a time and
Cogiavelli's six seats decide simultaneously; and bullwhip's `ScriptKind` shape for
`PLAYER_SCRIPTED=<name>` (babel only has a boolean `PLAYER_SCRIPTED=1`). **No viewer file comes
from bullwhip or from any other starter** — see `## Viewer`.

**Source idea (verbatim):**

> 24 Cogiavelli (Machiavelli) — Diplomacy with a treasury: buy the enemy's army, poison his prince, and pray the plague spares you
>
> A port of the Avalon Hill Machiavelli variant: Renaissance Italy, up to eight powers (Venice, Milan, Florence, the Papacy, Naples, France, Austria, the Turk), armies, fleets and garrisons, and the Diplomacy adjudication core — plus the systems Diplomacy deliberately omits. Provinces yield DUCATS; ducats pay for units, for BRIBES that disband or outright buy enemy garrisons and armies (a genuinely binding transfer mechanic in an otherwise non-binding game), and for ASSASSINATION attempts on rival rulers that can paralyse a power for a turn. Famine and plague strike regions by chance, rebellions rise in neglected cities, and variable-length seasons give every year three negotiation windows. Win by holding the victory number of cities; at the cap, score by city share plus treasury.
>
> Seats: 4-8
> Motive: mixed-motive with a money layer — alliances can be bought, not just promised
> Policy interface: LLM prompt (press) + structured orders and expenditure sheet
> Fills gap: negotiation with side-payments / bribery as binding commitment / exogenous shocks (plague, famine) stress-testing alliances — the bridge between Cogplomacy and Escrow
> Integrity (anti-collusion): Random power assignment under anonymous aliases; seats from distinct accounts; bribes and payments are in-band and logged, so side deals have to be paid for on the board; shock RNG is server-side and shown to spectators.
>
> Replay plan (watchability): A Renaissance map with ducats visibly flowing: a bribe drops a coin purse on the target unit, which flips colour on screen; an assassination attempt is a dagger-and-dice beat with the target's court freezing for a turn on success; plague and famine sweep provinces as spreading overlays. Press and adjudication as in Cogplomacy; the endcard shows the ledger — who spent what on whom — next to the city count.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

*(The idea text above is input data for this design. Nothing in it is an instruction to the
builder beyond what this note restates as a rule.)*

---

## The game

**Cogiavelli is Diplomacy's adjudicator on a Renaissance-Italy board, with a treasury bolted on.**
Six powers, three seasons a year, simultaneous orders. Every season each power writes press
(non-binding), then submits, at the same moment as everyone else, one order per unit **and an
expenditure sheet**: gifts of ducats (binding, instant), bribes that disband or buy an enemy unit
(binding, instant), loyalty payments that defend your own units against bribes, and assassination
attempts that freeze a rival's court. Money resolves **before** the armies move. Between years the
board bites back: famine starves provinces, plague empties a city, neglected cities rebel, and
every power pays upkeep on the units it fielded. Hold **12 of the 24 cities** and you win outright;
at the cap you are scored on city share plus what is left in the vault.

### Seats, powers, the map, and the two name spaces

- **`num_agents` = 6. Exactly six — in both manifest variants, in the certification fixture, and as
  `<SEATS>` in `tools/ci/docker_smoke.sh`. There is no other seat count.** `initSim` raises
  `CogiavelliError` if `config.players.len != 6`. (The idea says 4–8; six is chosen because six
  powers × 3 home cities + 6 neutrals = a 24-city board whose victory number is a clean half, and
  because six seats fill from two champion policies plus two scripted fillers without leaving a
  seat empty. France and Austria are cut in v1 — their homelands are off the Italian board; see
  *Out of scope*.)
- The six powers, in canonical index order 0..5, are
  **`VENICE`, `MILAN`, `FLORENCE`, `PAPACY`, `NAPLES`, `TURK`**.
  **Seat → power is a seed-drawn permutation** (`powerOf[seat]`, `seatOf[power]`), drawn from the
  same RNG stream as the aliases, the way babel draws its glyph permutation in `initSim`. No slot
  is structurally stuck with the Papacy.
- **In-game name space (anonymous).** Inside the game a seat is only ever a **power name**.
  Prompts, press, orders, expenditure sheets and the player websocket address `VENICE`, never a
  policy name, never a player name, never a slot index. Each seat also carries an anonymous **cog
  alias** drawn from babel's `CogNames` with babel's `tableNames` kept verbatim; the alias is the
  display name for any seat whose policy is a baseline filler.
- **Spectator name space (real).** The replay carries `powers[seat]`, `names[seat]` (cog alias) and
  `policyNames[seat]` (the real policy display names from `config.players[i].name`, exactly as
  babel's `policyNamesJson` supplies them). The viewer's name map renders `VENICE · daveey`;
  `results.json` attributes by policy name. Policy names never cross into the game
  (`tests/test_sim.nim` scans every built prompt for every `config.players[i].name`). **Both name
  spaces are recorded — never one or the other.**

### The board — `src/cogiavelli/mapdata.nim`, compiled in, pinned by `tests/test_map.nim`

**42 areas: 36 land provinces (24 of them cities) and 6 seas.** No split coasts anywhere (every
province that touches two seas touches two *adjacent* seas), which is the single largest
simplification against the real Machiavelli map and is deliberate.

| code | name | kind | city | land neighbours | seas |
|---|---|---|---|---|---|
| TUR | Turin | inland | ● neutral | SAV PAV GEN MIL | — |
| SAV | Savoy | inland | | TUR GEN PAV | — |
| COM | Como | inland | ● MILAN home | MIL TRE | — |
| MIL | Milan | inland | ● MILAN home | TUR COM PAV MAN | — |
| PAV | Pavia | inland | ● MILAN home | TUR SAV MIL GEN MAN MOD | — |
| GEN | Genoa | coastal | ● neutral | TUR SAV PAV MOD PIS | LIG |
| TRE | Trent | inland | | COM VER MAN | — |
| MAN | Mantua | inland | | MIL PAV TRE VER MOD FER | — |
| VER | Verona | inland | ● VENICE home | TRE MAN PAD FER | — |
| PAD | Padua | inland | ● VENICE home | VER VEN FER FRI | — |
| VEN | Venice | coastal | ● VENICE home | PAD FRI FER | UAD |
| FRI | Friuli | coastal | | PAD VEN TRI | UAD |
| TRI | Trieste | coastal | ● neutral | FRI BOS | UAD |
| FER | Ferrara | coastal | ● neutral | MAN VER PAD VEN BOL RMG | UAD |
| MOD | Modena | inland | | GEN PAV MAN BOL PIS | — |
| BOL | Bologna | inland | ● neutral | FER MOD RMG FLO | — |
| RMG | Romagna | coastal | | FER BOL FLO URB | UAD |
| PIS | Pisa | coastal | ● FLORENCE home | GEN MOD FLO SIE | LIG UTS |
| FLO | Florence | inland | ● FLORENCE home | BOL RMG PIS SIE URB | — |
| SIE | Siena | inland | ● FLORENCE home | PIS FLO PER ROM | — |
| URB | Urbino | inland | | RMG FLO PER ANC | — |
| ANC | Ancona | coastal | ● PAPACY home | URB PER ABR | LAD |
| PER | Perugia | inland | ● PAPACY home | SIE URB ANC ROM ABR | — |
| ROM | Rome | coastal | ● PAPACY home | SIE PER ABR NAP | UTS LTS |
| ABR | Abruzzi | coastal | | ANC PER ROM NAP APU | LAD |
| NAP | Naples | coastal | ● NAPLES home | ROM ABR APU CAL | LTS |
| APU | Apulia | coastal | | ABR NAP BAR CAL | LAD |
| BAR | Bari | coastal | ● NAPLES home | APU CAL | LAD |
| CAL | Calabria | coastal | | NAP APU BAR | LTS ION |
| MES | Messina | coastal | ● neutral | PAL | LTS ION |
| PAL | Palermo | coastal | ● NAPLES home | MES | LTS |
| BOS | Bosnia | inland | | TRI RAG ALB | — |
| RAG | Ragusa | coastal | ● TURK home | BOS ALB | LAD |
| ALB | Albania | inland | | BOS RAG DUR AVL | — |
| DUR | Durazzo | coastal | ● TURK home | ALB AVL | LAD |
| AVL | Avlona | coastal | ● TURK home | ALB DUR | LAD ION |

Seas and their sea-to-sea neighbours: **LIG** Ligurian Sea (UTS) · **UTS** Upper Tyrrhenian Sea
(LIG, LTS) · **LTS** Lower Tyrrhenian Sea (UTS, ION) · **ION** Ionian Sea (LTS, LAD) · **LAD**
Lower Adriatic Sea (ION, UAD) · **UAD** Upper Adriatic Sea (LAD). A sea is adjacent to exactly the
coastal provinces that list it in the table above.

Movement graphs, generated from that table by `mapdata.nim` and asserted symmetric by
`tests/test_map.nim`:

- **`armyAdj`** = the land-neighbour column, land provinces only. Armies never enter a sea and are
  never adjacent to one.
- **`fleetAdj`** = (a) sea↔sea edges, (b) sea↔its coastal provinces, (c) coast-hops: two coastal
  provinces that are land-adjacent **and** share at least one sea (e.g. `GEN–PIS` on LIG,
  `DUR–AVL` on LAD; `BAR–CAL` is **not** a coast-hop — no shared sea), and (d) exactly one
  fleet-only edge, **`CAL–MES`, the Strait of Messina.** A fleet never enters an inland province.
  **An army reaches Sicily (`MES`, `PAL`) only by convoy.**

**24 cities.** Home cities (18): `VEN PAD VER` (Venice), `MIL PAV COM` (Milan), `FLO PIS SIE`
(Florence), `ROM ANC PER` (Papacy), `NAP BAR PAL` (Naples), `RAG DUR AVL` (Turk). Neutral at
start (6): `TUR GEN TRI FER BOL MES`.

**18 starting units,** each power in its own three home cities:
Venice `A VER, A PAD, F VEN`; Milan `A MIL, A PAV, A COM`; Florence `A FLO, A SIE, F PIS`;
Papacy `A ROM, A PER, F ANC`; Naples `A NAP, A BAR, F PAL`; Turk `A DUR, A AVL, F RAG`.
**Every power starts with 12 ducats.**

### The calendar

An episode plays `years` years starting at **1499** (`years` default **4**, min 1, max 10;
certification fixture 1 — the arithmetic behind the default is in *Decisions* below). Each year is
**three seasons — Spring, Summer, Autumn — and then Winter**. Every season is one whole turn: a
press window, a simultaneous orders-and-expenditure submission, and a resolution. Winter takes no
decision from anybody: it executes the plans already written on the Autumn expenditure sheet. That
is the idea's "variable-length seasons give every year three negotiation windows", made fixed at
three so the budget is predictable.

### The resolution order — numbered, complete

Everything below happens in exactly this order. Steps 1–12 are one season; steps W1–W5 run once,
after Autumn.

1. **Famine draw (Spring only).** The server draws **2 distinct land provinces** from the shock
   stream (below) and announces them to every power at once. A famine province is marked for the
   whole year. `famine` event, carrying the two province codes and the draw index.
2. **Press window.** All six powers write **simultaneously, in one batch**: one public
   `broadcast`, up to five private `letters` (at most one per other power), up to four `pledges`,
   and private `notes`. Nothing said here binds anything. A power paralysed by an assassination
   (step 5 of the previous season) writes nothing this window; letters addressed **to** it are
   still delivered. Skipped entirely when `press: false`. `press` event per power.
3. **Orders and expenditure.** All six powers write **simultaneously, in one batch**: one order per
   unit they own, an `spend` sheet of up to 6 entries, and (Autumn only) a `builds` list of up to 6
   entries that Winter will execute. Nobody sees anybody else's submission before it resolves.
   `orders` event per power (normalised orders + the illegal ones with reasons).
4. **Payment.** For each power in power-index order, its `spend` entries are validated **in the
   order it listed them** against its live treasury: an entry it cannot afford is dropped with
   reason `insufficient`; an entry naming a nonexistent unit/power is dropped with reason
   `notarget`; a bribe on one's own unit or an assassination on oneself is dropped with reason
   `illegal`. **Every surviving entry is paid immediately — the ducats leave the vault whether or
   not the entry works.** A `gift` credits the recipient's treasury at this moment and is
   irrevocable: that is the game's binding transfer. One `spend` event per power carries the whole
   ledger line, including the dropped entries and their reasons.
5. **Assassination.** For each surviving `assassinate` entry, in power-index order of the payer:
   the server draws `roll` uniformly from **1..36** (rendered as two dice, `roll = 6*(d1-1)+d2`).
   The attempt **succeeds iff `roll ≤ amount`**, where `amount` is the ducats paid, clamped to
   6..30 at parse time — so 18 ducats is an even chance and 30 is the 30/36 ceiling. On success the
   target power is **paralysed**: (a) every one of its units is ordered to hold in **this** season's
   movement, overriding whatever it submitted, and (b) it writes no press in the **next** season's
   press window. Its treasury is untouched and its already-paid spend entries still stand.
   Simultaneous successful attempts on the same target are idempotent. `assassin` event per
   attempt, carrying payer, target, amount, `d1`, `d2`, `roll`, `success`.
6. **Bribes.** All bribes resolve at once against the amounts paid in step 4. For a targeted unit
   `U` owned by power `P`: let `defence` be the total `defend` ducats `P` paid on `U` this season.
   A bribe of `amount` with kind `k` **takes effect iff `amount ≥ Cost(k) + defence`**, where
   `Cost(bribe_disband) = 9` and `Cost(bribe_buy) = 15`. If two or more bribes on the same unit
   qualify, the **strictly largest amount** wins; an exact tie means **all of them fail** (rival
   paymasters cancel) and none of the money comes back. Effects, applied before any movement:
   `bribe_disband` removes `U` from the board; `bribe_buy` transfers `U` to the briber where it
   stands **and forces it to hold this season**. `bribe` event per attempt, with payer, target
   unit, kind, amount, defence, and outcome (`bought` / `disbanded` / `outbid` / `defended`).
7. **Order repair.** In this order: drop orders naming a unit the power does not own **after step
   6's transfers**; where one unit is ordered twice keep the first and drop the rest; replace every
   order of a paralysed power with a hold; give any unordered unit a hold. Then check legality: a
   fleet ordered inland or to a non-`fleetAdj` area; an army into a sea or across the Strait
   without a convoy; a move to a non-adjacent area with no possible convoy path; a support whose
   destination is not adjacent to the supporter; a support or convoy naming a unit that is not in
   the named province; an army ordering a convoy; a fleet being convoyed; a convoying fleet not in
   a sea. **Every illegal order becomes a hold for that unit** and is recorded in the `orders`
   event's `illegal` list with a one-word reason (`parse`, `nonadjacent`, `wrongunit`, `notthere`,
   `noconvoy`, `notowned`). **An illegal order never invalidates the rest of the reply.**
8. **Movement adjudication** — `src/cogiavelli/adjudicate.nim`, a pure total function
   `adjudicate(board, orders): Adjudication`. This is the Diplomacy core, unchanged:
   1. **Void unmatched supports and convoys.** `X S A - B` counts only if the unit at `A` ordered a
      move to `B`; `X S A` (support-hold) counts only if a unit is at `A` and did not order a move;
      `F XXX C A - B` counts only if the army at `A` ordered that move. A void support or convoy
      leaves its unit holding at strength 1, still dislodgeable.
   2. **Convoy paths.** A move between two coastal provinces that are not `armyAdj`-adjacent, or
      that names `VIA CONVOY`, needs a chain of sea spaces whose fleets all issued matching convoy
      orders. **No path ⇒ the move fails and the army holds** (`noconvoy`). Adjacent coastal moves
      that also have a convoy path resolve as land moves unless `VIA CONVOY` was named.
   3. **Resolve** with the four standard strengths, by the recursive resolver of Kruijswijk's *The
      Math of Adjudication* (`unresolved`/`guessing`/`resolved` marks, cycle detection):
      **hold strength** = 0 if the province is empty or its occupier moves away successfully, else
      1 + valid supports-to-hold; **attack strength** = 0 if the path fails, 0 if the destination
      holds a unit of the mover's **own** power that does not move away (self-dislodgement ban),
      else 1 + valid supports **excluding** any support given by the power owning the unit standing
      in the destination; **defend strength** (head-to-head) = 1 + all valid supports; **prevent
      strength** = 0 if the path fails or the head-to-head is lost, else 1 + valid supports. A move
      succeeds iff its attack strength exceeds the destination's hold strength (or, head-to-head,
      the opposing move's defend strength) **and** strictly exceeds every other move's prevent
      strength for that destination. Otherwise it **bounces**.
   4. **Cut supports.** A support is cut if the supporter's province is the destination of a move
      with attack strength ≥ 1 by a unit of a **different power**, except a move originating in the
      province the support is directed *into*. A dislodged supporter's support is cut
      unconditionally. Convoyed attacks cut support normally except where the Szykman rule voided
      the convoy.
   5. **Backup rules, exactly two:** the **circular-movement rule** (a closed cycle of moves with no
      external interference all succeed) and the **Szykman rule** for convoy paradoxes (the
      paradoxical convoyed move fails and its army holds; the convoying fleet's dislodgement
      stands).
   6. **Dislodgements and standoffs.** A unit is dislodged if a successful move enters its province
      and it did not successfully move away; record the attacker's origin. Every province in which
      two or more moves bounced is a standoff province: nothing enters it and it is barred as a
      retreat destination this season.
9. **Retreats — decided by rule, not by a decision call.** Each dislodged unit retreats to the
   legal destination (adjacent on its own movement graph, empty after movement, not the attacker's
   origin, not a standoff province) with the **smallest BFS distance to the nearest city its owner
   owns**, ties broken by ascending province code; if there is none it **disbands**. If two
   dislodged units would take the same province, the one whose province code sorts first takes it
   and the other re-picks, disbanding if nothing is left. This costs a whole LLM batch per season
   if it is a decision, and is worth less than a third of a game-year of play; it is a deliberate
   simplification. Retreats are recorded inside the `battle` event.
10. **City ownership.** Every city occupied by a unit becomes that unit's power's, **immediately,
    every season** (this is Machiavelli, not Diplomacy — the bar race moves three times a year).
    Unoccupied cities keep their owner. Emit `cities` (owner table + per-power counts + the cities
    gained and lost). **Check the conquest condition now** (below).
11. **Plague (Summer only).** The server draws **1 city province** uniformly from the 24 and
    resolves it immediately: **every unit standing in it is destroyed** (no retreat, no
    compensation), and that city **yields no income this year**. `plague` event with the province
    and the draw. If the province is empty, only the income effect applies.
12. **Season advance.** Spring → Summer → Autumn → Winter. `season` event opens each one.

**Winter**, once per year, after Autumn's step 12:

- **W1 — Rebellions.** For each power, for each **non-home city it owns with no unit standing in
  it**, in ascending power index then ascending province code, the server rolls a d6; **on a 1 the
  city rebels** and reverts to unowned. Every roll is recorded.
- **W2 — Famine strikes.** Every unit standing in one of this year's two famine provinces
  **disbands**.
- **W3 — Income.** Each power collects **3 ducats per city it owns**, excluding any city that was
  a famine province or the plague province this year, **plus a variable draw of 0..3** ducats from
  the shock stream (one draw per power, ascending power index).
- **W4 — Upkeep.** Each power pays **1 ducat per unit it owns**. If it cannot pay for all of them
  it disbands units until it can — the unit with the **largest BFS distance to the nearest city it
  owns** first, ties by ascending province code — and pays 1 ducat for each survivor.
- **W5 — Builds.** The `builds` list written on the Autumn expenditure sheet executes in the order
  written: each entry costs **3 ducats** and places a new unit in a **vacant city the power owns**
  (any owned city, not only home cities — Machiavelli, not Diplomacy); a fleet may only be built
  in a **coastal** city. Entries that are unaffordable, illegal, or duplicated are skipped with a
  reason. Then the end conditions are checked.

W1–W5 are one `winter` event carrying every rebellion roll, every famine casualty, every power's
income and variable draw, every upkeep disband, and every build with its outcome.

A power with **zero units and zero cities** after W5 is **eliminated**: it writes no press,
receives no orders call, keeps whatever ducats it has (they still count for score), and its seat
still receives state frames with `"eliminated": true` until the final frame.

### The shock RNG — server-side, seeded, recorded, verifiable

Every random draw in the game comes from **one stream**,
`shockRng = initRand(int64(config.seed) * 104729 + 7)`, advanced in exactly this order and nowhere
else: (1) Spring famine, 2 draws; (2) each season's assassination rolls, in ascending power index
of the payer; (3) Summer plague, 1 draw; (4) Winter rebellion rolls, ascending power index then
ascending province code; (5) Winter income draws, ascending power index. **Every draw is written
into the event that consumed it** (`famine.provinces`, `assassin.d1/d2/roll`, `plague.province`,
`winter.rebellionRolls[]`, `winter.incomeDraws[]`), so a spectator can check the dice against the
outcome, and `replayMatch` re-derives the same stream from the seed and **raises if a recorded draw
disagrees with the re-derived one** (babel's `replayMatch` does the same check on its round
schedule). No other part of the game is random: the seat→power permutation and the cog aliases are
drawn once at `initSim` from a separate stream, as babel does.

### Scoring, its sign, and what the league ranks by

Let `c_i` be the cities power `i` owns when the episode ends, `d_i` its ducats, and
`TotalCities = 24`.

- **Conquest.** If any power owns **≥ 12** cities at a step-10 ownership update (or is the only
  power still owning a city), it scores **1.0**, every other seat scores **0.0**, and the episode
  ends there.
- **Otherwise** (cap or deadline):
  **`score_i = (c_i + min(d_i, 24) / 24) / 24`.**

Higher is better; every score is in `[0, 1]`; the denominator is the constant 24 so an unclaimed
neutral dilutes everybody equally and taking a city is worth the same to every power. The treasury
term is worth **at most one city** (24 ducats), which is exactly the idea's "city share plus
treasury" without letting a miser out-score a conqueror. **The league ranks by mean episode
score.** Results also report `cities`, `ducats`, `units`, `powers`, `spent`, `received` and
`conqueror`.

### End conditions and the legal `results.reason` values

Exactly three values are legal in `results.reason`:

| value | when |
|---|---|
| `"conquest"` | a power reached ≥ 12 cities at a step-10 ownership update, or is the last power owning any city. `results.conqueror` is its power name. |
| `"complete"` | the configured `years` were played out through the final Winter. `conqueror` is `""`. |
| `"deadline"` | the episode clock stopped play **between batches**. Scores use the board and treasuries as they stand at that moment. `conqueror` is `""`. |

`resultsJson` emits `""` for `reason` only while the sim is still running; a written result always
carries one of the three. A `deadline` result is a legitimate, scoreable episode — the platform
keeps **nothing** from an episode that overruns, so a short honest episode always beats a long one
that never lands.

### Per-seat observation — exactly what is visible and what is hidden

**Visible to every seat, every season:**

- the **whole board** — every unit, with its power, kind (`A`/`F`) and province;
- the **city table** — all 24 cities with owner (or `neutral`), plus every power's city count and
  unit count;
- **every power's treasury balance, exactly.** The ledger is the point of this game; income is a
  public function of a public city table and a published draw, and every resolved expenditure is
  published, so hiding balances would only make seats do arithmetic. Treasuries are public.
- **the resolved ledger of the last two years** — who paid whom, how much, for what, and whether it
  worked, including every failed bribe and every missed assassination with its dice;
- **the last two years of orders** and each order's result, the retreats, the ownership changes;
- **the shocks**: this year's famine provinces from the moment they are drawn, past plague
  provinces, past rebellions, and every power's income draw;
- **all public broadcasts** of the current and previous press window;
- **the private letters and pledges addressed to this seat** in the current and previous press
  window, each labelled with its sender's power;
- in the orders phase, **the complete list of legal orders for each of its own units**, in the exact
  notation the reply must use, and **the complete list of bribable enemy units with the exact
  minimum ducats each would cost** (the same predicates the validator applies, precomputed — the
  escrow 2026-08-23 lesson: a formal-output game must hand the model the legal set, not just the
  grammar);
- **its own private notes**, fed back verbatim.

**Hidden from a seat, always:**

- **the current season's submissions of every other power** — their orders *and* their expenditure
  sheets. A bribe in flight is invisible until step 6 resolves it. This is what keeps the game
  simultaneous and the stab possible;
- **private letters and pledges not addressed to it** — a seat never learns that Milan wrote to the
  Turk, nor what was in it. **Spectators and the replay see every letter immediately**; that is the
  whole point of the replay plan;
- other powers' **private notes**;
- **future shock draws** — the plague province is not known before Summer resolves, rebellion and
  income rolls not before Winter;
- the other seats' policy names, player names, slot indices and cog aliases.

### Press and pledges

Press is **one exchange per season, not a conversation**: all six write at once, letters are
delivered before the same season's orders batch, so a letter can be *acted on* the season it is
sent but only *answered* the next one. A second press round per season costs a whole game-year of
budget (see the arithmetic below) and is out of scope.

Nothing said in press binds anything — **only the expenditure sheet binds.** A pledge exists only
so that a betrayal is machine-detectable and therefore drawable:

| pledge | JSON | broken when the pledger's orders this season… |
|---|---|---|
| peace | `{"to":"MILAN","kind":"peace"}` | …move any unit into a province occupied by a Milanese unit or into a city Milan owns, **or** support any such move, **or** bribe or assassinate Milan |
| keep out | `{"to":"ALL","kind":"keepout","province":"BOL"}` | …order any unit into Bologna, or support any move into Bologna |
| support | `{"to":"NAPLES","kind":"support"}` | …contain no order supporting a Neapolitan unit (hold or move) |

`to` is a power name or `ALL`; an `ALL` pledge is shown to everyone, a targeted pledge to its
addressee (and to spectators immediately). A broken pledge is recorded as a `stab` record inside
the `battle` event, naming the pledge and the offending order or ledger entry, and the viewer
stamps **STAB** over the offender. Free-text promises with no pledge are legal and common — they
simply cannot be stamped, and the prompt says so.

### Integrity

Six seats, six distinct policies scheduled by the league (`num_agents: 6`). Powers are
seed-assigned and identities are power names only, so a policy cannot recognise, address or reward
a specific counterparty across episodes. **Every side payment is in-band**: a gift, a bribe and an
assassination all cost ducats that came from cities on the board and all appear in the replay
ledger, so a deal that was struck can be seen being paid for. The shock RNG is server-side, seeded
and published draw-by-draw. City-share-plus-treasury scoring at the cap removes the endgame in
which an allied pair hands one of them the win — handing your cities away lowers your own score
one for one, and handing your ducats away costs you up to a full city of score.

---

## Decisions: LLM with scripted fallback

Transport, credentials, the JSON-only output contract, `extractJsonObject`, the rune-safe
`cleanNotes`, the Bedrock model candidate list with its 401/403/429 handling, and "no credentials
⇒ every seat scripted, immediately, with no network wait" are ported from babel
`src/babel/llm.nim` unchanged. What changes: the decision loop becomes **batched**, the reply
schemas are Cogiavelli's, and there are two named baselines instead of one boolean.

### One parallel batch per phase

All six seats decide simultaneously by rule, so **every phase fires its requests as ONE
`curly.makeRequests` batch** — never seat by seat. The loop is bullwhip's `decideAll`
(`src/bullwhip/llm.nim:425-478`) with Cogiavelli's parsers: build one `RequestBatch` over the
still-open seats, one `makeRequests` call bounded by `llmTimeoutSeconds`, parse each response,
re-batch the failures **once** with an invalid-reply hint, then fall back to the scripted baseline
for whatever is still open. Two batches per season:

- **press batch** — every live, non-paralysed power (≤ 6 requests); skipped when `press: false`;
- **orders batch** — every live power (≤ 6 requests); a paralysed power is still asked (its
  expenditure sheet still works) but its movement orders are overwritten with holds at step 7.

Retreats, rebellions, income, upkeep and builds take **no** batch: retreats and disbands are
decided by rule (step 9, W4) and builds ride on the Autumn expenditure sheet. Seats registered as
scripted, and every seat when the LLM client is disabled, are answered from the baselines without
touching the network — that fallback is load-bearing for offline certification, exactly as in
babel.

### Episode budget — the arithmetic, out loud

`PlayBudgetFraction = 0.6` (babel `src/babel/server.nim:234`) of the episode timeout —
`COWORLD_TIMEOUT_SECONDS` when the platform sets it, otherwise `config.episodeTimeoutSeconds`,
default **1200 s** — ⇒ **720 s of play**. The deadline is checked **before every batch and before
every season transition**; past it the sim settles with `reason = "deadline"`.

A batch is one model round-trip for all six seats, not six. Measured shape for haiku-class models
at `maxOutputTokens = 1200`: 8–20 s per batch, hard-bounded by `llmTimeoutSeconds = 45`.

```
one season = press batch      ~18 s
           + orders batch     ~18 s
           + pacing (turnDelayMs 300 × ~4 transitions)  ~1 s
                              ------------------------------
                              ≈ 37 s
one year   = 3 seasons        ≈ 111 s   (Winter takes no batch, ~1 s of pacing)
4 years                       ≈ 450 s  of the 720 s budget
```

That is why **`years` defaults to 4** (1499–1502, twelve movement phases). The remaining ~270 s
absorbs slow batches and retry rounds. Worst case — every batch at the 45 s ceiling plus its retry
— the pre-batch deadline check stops play at ≤ 720 s, after which the episode spends at most one
in-flight batch and its retry (≤ 90 s) plus ~2 s writing artifacts: **≤ 812 s against a 1200 s
kill.** The `gunboat` variant has no press batches (≈ 57 s/year) and therefore runs **6** years in
the same budget.

A 12-city conquest is rule-complete and reachable from a strong opening, but a 4-year episode is
usually decided on city share plus treasury. That is deliberate and stated in `rules.md`.

### Prompts

Two system prompts (press, orders) built in `src/cogiavelli/llm.nim`. The system prompt for a seat
playing Venice — the builder writes it out in full; this is the required content and wording:

```
You are VENICE, one of six powers contending for Renaissance Italy. The others are
MILAN, FLORENCE, the PAPACY, NAPLES and the TURK, each played by a different cog.
You never learn who plays them.

Rules:
- Armies move on land, fleets on seas and along coasts. Every unit has equal strength; a
  unit takes a province only if it out-supports whatever opposes it, and equal strength
  means a STANDOFF and nobody moves. All six powers order at the same time and see
  nothing of each other's orders until they resolve.
- Orders: HOLD, MOVE, SUPPORT (a hold or a move) and CONVOY (a fleet at sea carrying an
  army between coasts). A supported attack that beats the defence DISLODGES the defender,
  which retreats to the nearest friendly ground or disbands. You may never dislodge your
  own unit or help anyone dislodge it.
- Whoever occupies a city owns it, from that moment. Cities pay 3 ducats each every
  Winter; every unit costs 1 ducat of upkeep; a new unit costs 3 ducats and appears in a
  vacant city you own.
- DUCATS ARE THE OTHER ARMY. In the same submission as your orders you may: GIFT ducats
  to another power (they arrive, always — this is the only promise in the game that
  cannot be broken); BRIBE an enemy unit to disband (9 ducats) or to change sides and
  serve you (15 ducats); DEFEND one of your own units against bribery (every ducat you
  pay raises what a briber must beat); or ASSASSINATE a rival, paying 6 to 30 ducats for
  a roll of two dice — beat the roll and that power's whole court freezes: every one of
  its units holds this season and it sends no letters the next. Money resolves BEFORE the
  armies move, and it is spent whether or not it works. Everything you pay is published.
- Italy bites back: famine marks two provinces each Spring and starves whatever still
  stands there at Winter, plague empties one city every Summer, and a city you own with
  no unit in it may rebel and be lost.
- Hold 12 of the 24 cities and you win outright. Otherwise you are scored on your share
  of the 24 cities plus what is left in your treasury. Nothing else scores.
- LETTERS ARE NOT BINDING. You may promise anything to anyone and then do the opposite.
  So may they. Only ducats that have actually changed hands are real.

OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no
explanation, no markdown fences, no text before or after the object. Your reply must
begin with the character { and end with }.
```

The user prompt carries the board, the city table, every treasury, the two-year ledger and order
history, the shocks in force, the press this seat received, its notes, babel's operator block
verbatim (`GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply
in the requested format):` + `PLAYER_PROMPT`), and the phase tail:

- **press** — `SPRING 1500 — LETTERS.` then
  `Reply with ONLY {"broadcast":"…","letters":[{"to":"MILAN","text":"…"}],"pledges":[{"to":"MILAN","kind":"peace"}],"notes":"…"} — broadcast at most 400 characters, at most 5 letters of at most 400 characters each (one per power), at most 4 pledges, notes at most 800 characters. A pledge is the only promise spectators can watch you break; free text is never checked.`
- **orders** — `SPRING 1500 — ORDERS AND EXPENDITURE.`, then `YOUR TREASURY: 14 ducats.`, then
  `YOUR UNITS AND EVERY LEGAL ORDER:` with each unit's enumerated legal orders in canonical
  notation (capped at 64 per unit), then `UNITS YOU COULD BRIBE THIS SEASON:` with each enemy
  unit and its minimum cost (`A ROM (PAPACY) — disband 9, buy 15`), then
  `Reply with ONLY {"orders":["A VER - MAN","F VEN S A VER - MAN"],"spend":[{"action":"bribe_buy","target":"A ROM","amount":15}],"notes":"…"} — exactly one order per unit, copied character for character from the list above; an order that is not on the list becomes a hold. spend is at most 6 entries; action is one of gift, bribe_disband, bribe_buy, defend, assassinate; target is a power name for gift and assassinate and a unit like "A ROM" for the others; amount is a whole number of ducats you actually have. Anything you cannot afford is dropped, in the order you wrote it.`
  In Autumn the tail adds
  `You may also send "builds":["A VEN","F PAL"] — up to 6 entries, 3 ducats each, executed this Winter in a vacant city you own; a fleet only in a coastal city.`

### Reply schema — every free-text field capped, truncation on rune boundaries

Every cap is applied with babel's rune-safe `cleanNotes` (`runeLen` / `runeSubStr`, cut marked with
`…`, `src/babel/llm.nim:393-398`) so a byte slice can never leave invalid UTF-8 in the replay
(playbook gotcha: *"Replay bytes fail a strict JSON parser but render in a browser"*). Over-long
arrays are **truncated from the end**, never rejected.

| phase | field | type | cap | over-cap behaviour |
|---|---|---|---|---|
| press | `broadcast` | string | **400 runes** | truncated with `…` |
| press | `letters` | array | **5 entries** | extras dropped; a second letter to the same power dropped |
| press | `letters[].to` | string | power name or `ALL`, case-insensitive, **24 runes** | unknown recipient ⇒ letter dropped |
| press | `letters[].text` | string | **400 runes** | truncated with `…` |
| press | `pledges` | array | **4 entries** | extras dropped |
| press | `pledges[].kind` | enum | `peace` / `keepout` / `support` | unknown ⇒ pledge dropped |
| press | `pledges[].to` | string | power name or `ALL`, **24 runes** | unknown ⇒ pledge dropped |
| press | `pledges[].province` | string | 3-letter code, **8 runes** (`keepout` only) | unknown ⇒ pledge dropped |
| press | `notes` | string | **800 runes** | truncated with `…` |
| orders | `orders` | array of strings | **24 entries**, each **40 runes** | extras dropped; over-long string ⇒ `parse`-illegal ⇒ hold |
| orders | `spend` | array of objects | **6 entries** | extras dropped |
| orders | `spend[].action` | enum | `gift` / `bribe_disband` / `bribe_buy` / `defend` / `assassinate` | unknown ⇒ entry dropped |
| orders | `spend[].target` | string | **24 runes** | unresolvable ⇒ dropped, reason `notarget` |
| orders | `spend[].amount` | integer | 1..999; `assassinate` clamped to 6..30 | non-integer ⇒ dropped; unaffordable ⇒ dropped, reason `insufficient` |
| orders (Autumn) | `builds` | array of strings | **6 entries**, each **24 runes** | extras dropped |
| orders | `notes` | string | **800 runes** | truncated with `…` |
| player→game | `prompt` | string | **4000 runes** (babel's `MaxPromptLen`) | truncated |

A reply is **invalid** — and only then — if it is not a JSON object, or the phase's required key
(`broadcast`/`letters` for press; `orders` for orders) is missing or of the wrong JSON kind.
Illegal *contents* — a bad order, an unknown recipient, an unaffordable bribe — are repaired per the
table and never invalidate the reply.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

Two, both deterministic, both silent (no broadcast, no letters, no pledges, no notes), both legal
by construction. `parseScriptKind` accepts `condottiere` / `1` / `true` / `yes` → `skCondottiere`,
`banker` / `miser` → `skBanker`, anything else → `skNone`.

**`condottiere`** (the default, and the fallback for every failed decision):

1. Compute, on each unit's own movement graph, the BFS distance from every area to the nearest city
   the power does **not** own.
2. Rank each unit's legal moves: (a) into an **unowned neutral** city; (b) into a city owned by
   another power and **not occupied**; (c) a move that strictly reduces the BFS distance in step 1;
   (d) hold. Ties inside a rank break by ascending destination code.
3. Walk units in ascending province code and claim destinations; a destination already claimed by
   one of its own units is skipped, so **the baseline never stands itself off**.
4. If a unit's best option is rank (c) or (d) and another of its own units has claimed an adjacent
   destination, it issues `S <that unit> - <that destination>` instead.
5. A move that would vacate an owned, otherwise-unoccupied city drops one rank (two in Autumn,
   because Winter rebellions punish empty cities).
6. **Expenditure:** if treasury ≥ 12 and any adjacent enemy unit stands in or next to a city this
   power owns, `bribe_disband` the one with the lowest province code for exactly 9 + 0 defence;
   else if treasury ≥ 20, `bribe_buy` the nearest enemy unit standing in an unowned or
   enemy-owned city for exactly 15; else nothing. It never gifts, never defends, never assassinates.
7. **Autumn builds:** while `treasury − 3 ≥ unitCount` (keep upkeep covered), build in the vacant
   owned city with the lowest province code — a fleet if the city is coastal and the power holds
   fewer fleets than armies, otherwise an army.

**`banker`** (the wall with a vault): every unit holds; a unit adjacent to an owned city occupied
by one of its own units issues `S` for that unit's hold instead (first such neighbour by province
code). Expenditure: `defend` 4 ducats on each of its own units standing in a city, cheapest first,
while treasury ≥ 15. Builds only when treasury ≥ 30, one per Winter. It never attacks, never
bribes, never assassinates, and ends most episodes rich, small and un-bribable — the neighbour that
cannot be talked into anything and the reason a prompt has to learn that money is not always the
answer.

### Degrade, never hang

- **Per seat, per batch:** a transport error, a timeout, a non-JSON reply, or a reply missing the
  phase's required key ⇒ the seat joins **one** retry batch carrying the hint
  `Your previous reply was invalid. Respond with ONLY the requested JSON object.` Still failing ⇒
  the seat is answered by **`condottiere`** for that phase (silence for a press phase), logged
  `cogiavelli: seat N falling back to scripted decision` and flagged `scripted: true` on the event.
- **Auth failure** (401/403) disables the client for the rest of the episode; 429 and Bedrock
  model-access denials rotate the model candidate — babel's `tryNextBedrockModel`, unchanged.
- **A seat that never delivers a prompt** by `player_connect_timeout_seconds` (default 180) plays
  `condottiere` for the whole episode; six seats must not stall on one late container.
- **Episode clock:** checked before every batch and every season transition. Past 60 % of the
  timeout ⇒ `endEarly()` ⇒ `reason = "deadline"`, results and replay written immediately; the
  final frames go to the player sockets **before** the artifacts are written (babel
  `finishEpisode`, kept verbatim).
- **Pacing** (`turnDelayMs`, default 300, certification 0) is bounded in total by
  `PacingBudgetMs = 60_000`, divided across the season count by `sampleEpisode` — babel's
  idempotent `sampled` discipline, unchanged.
- **Nothing in the sim can loop forever:** the adjudicator's recursion is bounded by the order count
  (≤ 24), the resolver's cycle detection terminates on the two backup rules, bribe resolution is a
  single pass over ≤ 36 entries, and BFS is over a 42-node graph.

---

## Sim module

Pure rules, no IO, shared by the server, the tests and the wasm viewer — babel's discipline
(`src/babel/sim.nim` has no `os`, no `curly`, no `mummy`), one module per concern.

### `src/cogiavelli/mapdata.nim` (new)

Compiled-in constants: `Provinces` (the 42 records of the table above: code, display name, kind
`pkInland`/`pkCoastal`/`pkSea`, `isCity`, `homePower` (−1 for neutrals and non-cities), `seas`),
`ArmyAdj` / `FleetAdj` (generated from the table, symmetric), `Cities` (the 24 ids),
`HomeCities[6]`, `StartUnits` (the 18 above),
`PowerNames = ["VENICE","MILAN","FLORENCE","PAPACY","NAPLES","TURK"]`,
`PowerAdjectives = ["Venetian","Milanese","Florentine","Papal","Neapolitan","Turkish"]` for the
feed. Procs: `provinceByCode`, `isAdjacent`, `bfsDistance`. Nothing else.

### `src/cogiavelli/types.nim` (fork of `src/babel/types.nim`)

`CogiavelliError`; `PlayerConfig`; `GameConfig` (babel's, with `years` replacing `rounds` and
`press: bool` added); `Unit` (`power, kind: ukArmy|ukFleet, province`); `OrderKind`
(`okHold, okMove, okSupportHold, okSupportMove, okConvoy`); `Order`
(`power, unit, kind, target, auxFrom, auxTo, viaConvoy, raw, illegal, why`); `OrderOutcome`
(`ooSuccess, ooBounce, ooVoid, ooNoConvoy, ooDislodged, ooCut, ooIllegal, ooHeld`); `SpendKind`
(`spGift, spBribeDisband, spBribeBuy, spDefend, spAssassinate`); `SpendEntry`
(`power, kind, targetPower, targetUnit, amount, applied, why`); `Letter`
(`fromPower, toPower, text, public`); `Pledge` (`fromPower, toPower, kind, province, broken,
brokenBy`); `Season` (`seSpring, seSummer, seAutumn, seWinter`); `PhaseKind`
(`pkPress, pkOrders, pkResolve, pkWinter`); `EventKind`; `GameEvent`; `defaultGameConfig()`;
`update()`.

`defaultGameConfig`: `years: 4, press: true, seed: 0, episodeTimeoutSeconds: 1200,
turnDelayMs: 300, playerConnectTimeoutSeconds: 180, model: "claude-sonnet-5",
maxOutputTokens: 1200, llmTimeoutSeconds: 45`.

### `src/cogiavelli/orders.nim` (new)

One grammar for parsing and printing: `A VER H`, `A VER - MAN`, `A BAR - PAL VIA CONVOY`,
`F VEN S A PAD - FER`, `F VEN S A PAD`, `F LAD C A BAR - RAG`. Exports `parseOrder`, `formatOrder`,
`legalOrders(board, unit): seq[string]`, `parseUnitRef` (`"A ROM"` → the unit standing in Rome).
Parsing is whitespace- and case-tolerant, accepts `-`, `–`, `->` for a move and
`S`/`SUPPORT`, `C`/`CONVOY`, `H`/`HOLD`/`HOLDS`; nothing else.

### `src/cogiavelli/adjudicate.nim` (new)

`adjudicate(board: Board, orders: seq[Order]): Adjudication` — resolution step 8, pure and total.
`Adjudication` carries `results: seq[OrderResult]`, `dislodged: seq[Dislodgement]`
(`unit, attackerFrom`), `standoffs: seq[int]`, `moved: seq[(unit, dest)]`. No RNG, no IO, no
exceptions on legal input.

### `src/cogiavelli/money.nim` (new)

`validateSpend` (step 4), `resolveAssassinations` (step 5), `resolveBribes` (step 6),
`collectIncome` / `payUpkeep` / `runRebellions` / `strikeFamine` / `runBuilds` (W1–W5). Every proc
takes the shock `Rand` by `var` where it draws, and returns the drawn values so the caller can
record them. Constants: `BribeDisbandCost = 9`, `BribeBuyCost = 15`, `BuildCost = 3`,
`UpkeepPerUnit = 1`, `CityIncome = 3`, `IncomeDrawMax = 3`, `AssassinMin = 6`, `AssassinMax = 30`,
`AssassinFaces = 36`, `RebellionFace = 1`, `FamineProvinces = 2`, `StartTreasury = 12`.

### `src/cogiavelli/sim.nim` (fork of `src/babel/sim.nim`)

Constants: `Seats = 6`, `Powers = 6`, `TotalCities = 24`, `VictoryCities = 12`, `MinYears = 1`,
`MaxYears = 10`, `StartYear = 1499`, `SeasonsPerYear = 3`, `PacingBudgetMs = 60_000`,
`MaxBroadcastLen = 400`, `MaxLetterLen = 400`, `MaxLetters = 5`, `MaxPledges = 4`,
`MaxNotesLen = 800`, `MaxOrderLen = 40`, `MaxSpendEntries = 6`, `MaxBuilds = 6`,
`CogNames` (babel's, verbatim).

`Sim` object: `config`, `names` (aliases), `powerOf[6]`, `seatOf[6]`, `units: seq[Unit]`,
`owner: array[24, int]`, `treasury: array[6, int]`, `year`, `season`, `phase`, `pending: set[seat]`,
`famine: seq[int]`, `plagueCity: int`, `paralysed: array[6, bool]`, `pressBlocked: array[6, bool]`,
`press: seq[Letter]`, `pressLast: seq[Letter]`, `pledges: seq[Pledge]`,
`orders: array[6, seq[Order]]`, `spends: array[6, seq[SpendEntry]]`, `builds: array[6, seq[string]]`,
`lastAdjudication: Adjudication`, `ledger: seq[SpendEntry]` (whole-episode, for the endcard),
`spent: array[6, int]`, `received: array[6, int]`, `history: seq[TurnRecord]`,
`cityHistory: seq[array[6, int]]`, `notes: seq[string]`, `eliminated: array[6, bool]`,
`shockRng: Rand`, `done`, `reason`, `conqueror`, `events`.

API mirrors babel's: `initSim`, `sampleEpisode` (clamps `years`, divides `turnDelayMs` into
`PacingBudgetMs`, idempotent via `sampled`), `pendingSeats`, `beginSeason`,
`applyPress(seat, broadcast, letters, pledges, notes, scripted)`,
`applyOrders(seat, orders, spend, builds, notes, scripted)` — **the last pending seat of a phase
resolves the phase and opens the next**, exactly as babel's `applyPick` closes a round —
`endEarly`, `cities(seat)`, `score(seat)`, `resultsJson`, `tableStateJson`, `replayMatch`,
`eventToJson`, `eventFromJson`.

### Event vocabulary — 13 flat kinds, JSON via `eventToJson` / `eventFromJson`

Every field a viewer needs is typed on the event; no free-form `JsonNode` rides in the log, so the
wasm parse stays strict.

| kind | fields |
|---|---|
| `start` | `year` = 1499, `powers` (seat → power index), `units` (the 18), `owners` (24), `treasury[6]`, `seed` |
| `season` | `year`, `season`, `phaseKind`, `units`, `owners`, `treasury[6]`, `cityCounts[6]` — the derived board, **checked** against the seeded re-derivation in `replayMatch` |
| `famine` | `year`, `provinces` (2 codes) |
| `press` | `year`, `season`, `seat`, `power`, `broadcast`, `letters` (`to`, `text`), `pledges`, `scripted`, `text` = notes |
| `orders` | `year`, `season`, `seat`, `power`, `orders` (normalised), `illegal` (`raw`, `why`), `scripted`, `text` = notes |
| `spend` | `year`, `season`, `seat`, `power`, `entries` (`kind`, `targetPower`, `targetUnit`, `amount`, `applied`, `why`), `treasuryAfter` |
| `assassin` | `year`, `season`, `power`, `target`, `amount`, `d1`, `d2`, `roll`, `success` |
| `bribe` | `year`, `season`, `power`, `targetUnit`, `targetPower`, `kind`, `amount`, `defence`, `outcome` (`bought`/`disbanded`/`outbid`/`defended`) |
| `battle` | `year`, `season`, `results` (one `OrderResult` per order of every power), `dislodged`, `retreats` (`unit`, `to` or `"D"`), `standoffs`, `stabs` (`power`, `pledgeTo`, `kind`, `province`, `order`) |
| `cities` | `year`, `season`, `owners` (24), `counts[6]`, `gained`/`lost` per power — the bar-race frame |
| `plague` | `year`, `province`, `killed` (units destroyed) |
| `winter` | `year`, `rebellions` (`city`, `power`, `roll`), `famineKills`, `income[6]`, `incomeDraws[6]`, `upkeep[6]`, `upkeepDisbands`, `builds` (`power`, `entry`, `applied`, `why`), `treasury[6]` |
| `end` | `year`, `text` = reason, `cities[6]`, `treasury[6]`, `conqueror` |

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"seats":[{"power":"VENICE","name":"Sprocket","cities":5,"units":4,"ducats":17,
           "score":0.212,"pending":true,"eliminated":false,"paralysed":false,
           "stabbedThisTurn":false,"spentTotal":24,"receivedTotal":6,
           "broadcast":"…","lettersOut":[{"to":"MILAN","text":"…"}],
           "pledges":[{"to":"MILAN","kind":"peace","broken":false}],
           "notes":"…"}, ×6 by seat],
 "seatOfPower":[3,0,5,1,4,2],
 "units":[{"power":0,"kind":"A","province":"VER","dislodged":false,"bought":false}, …],
 "owners":[{"city":"VEN","power":0}, … ×24],
 "arrows":[{"kind":"move|support|convoy","from":"VER","to":"MAN","aux":"",
            "power":0,"outcome":"success|bounce|void|noconvoy|cut|illegal"}, …],
 "purses":[{"from":1,"to":"A ROM","kind":"bribe_buy","amount":15,"outcome":"bought"}, …],
 "daggers":[{"from":4,"target":2,"amount":18,"d1":3,"d2":5,"roll":17,"success":true}],
 "gifts":[{"from":0,"to":3,"amount":6}],
 "famine":["MOD","APU"],"plague":"BOL",
 "rebellions":[{"city":"TUR","power":1,"roll":1}],
 "stabs":[{"power":0,"pledgeTo":"MILAN","kind":"peace","order":"A VER - MAN"}],
 "standoffs":["BOL"],
 "year":1500,"season":"summer","phase":"orders","years":4,"yearsPlayed":1,
 "counts":[[3,3,3,3,3,3],[4,3,4,3,3,3], …],
 "treasuries":[[12,12,12,12,12,12],[17,9,14,12,20,11], …],
 "press":[{"from":"VENICE","to":"MILAN","text":"…","public":false}, …],
 "gameDone":false,"reason":"","conqueror":""}
```

`press` in the frame is **every** letter of the window, public and private, because this is the
spectator/replay frame — the idea's "spectators read all private correspondence". The redacted
player frame (below) is a different, smaller object.

### `resultsJson` — platform-facing, policy names

```json
{"names":[6 policy names],"powers":[6 power names],"scores":[6 floats in 0..1],
 "cities":[6 ints],"ducats":[6 ints],"units":[6 ints],
 "spent":[6 ints],"received":[6 ints],
 "years":<played>,"maxYears":<cap>,"conqueror":"VENICE"|"",
 "reason":"conquest|complete|deadline"}
```

### Replay payload — `cogiavelli.replay.v1`

```json
{"protocol":"cogiavelli.replay.v1","names":[aliases],"policyNames":[real names],
 "powers":[6 power names by seat],
 "config":{"years":4,"seed":7,"press":true,"sampled":true,
           "victoryCities":12,"totalCities":24,"map":"italy1499"},
 "events":[…],"results":{…}}
```

Replay mode and the wasm viewer add `"states"` (one `tableStateJson` per event prefix), exactly as
babel's `statesFromEvents` / `runReplayServer` do. **The bytes are self-sufficient:** the seed
re-derives the seat→power permutation, the aliases and the whole shock stream; the events carry
every letter, pledge, order, expenditure entry, bribe, dagger roll, adjudication result, retreat,
ownership table, plague, famine, rebellion, income and build; `config` carries the fitted year cap
and the map id; `policyNames` carries the spectator name space. The viewer contacts nothing but S3
for the `.replay` file.

---

## Server, player, protocol

### `src/cogiavelli/server.nim` (fork of `src/babel/server.nim`)

Same skeleton and the same load-bearing details, kept verbatim: the mummy router
(`GET /healthz`, `/client/global`, `/client/player`, `/client/replay`, `/client/renderer.js`,
`/client/chrome.css`, `/client/assets/@name`, `WS /player?slot=N&token=T`, `WS /global`,
`WS /replay`), the `stateLock` discipline, `writeArtifact` with the PUT/POST env hint, the
**Ping→Pong answer in `websocketHandler`** (the certifier pings `/global`; an unanswered ping fails
certification), the "final frames to players **before** the artifacts are written" ordering in
`finishEpisode`, and `PlayBudgetFraction = 0.6`. Both `/client/` routes serve real pages and
neither opens the player socket (lantern 0.1.1); `/healthz` and `/global` keep answering for a
bounded ~20 s shutdown grace after the artifacts are written (lantern 0.1.3).

The game loop is replaced with the season loop: check the deadline → snapshot the sim → collect the
phase's pending seats → run **one** `decideAll` batch outside the lock → apply each decision under
the lock (the last apply resolves the phase and opens the next) → broadcast → pace. Every apply is
wrapped in babel's belt-and-braces `try/except CogiavelliError` that falls back to `condottiere`,
even though `applyOrders` repairs rather than rejects.

### Player protocol — `cogiavelli.player.v1`

JSON text frames on the websocket named by `COWORLD_PLAYER_WS_URL`.

- game → player, on connect:
  `{"type":"welcome","protocol":"cogiavelli.player.v1","slot":N,"power":"VENICE","name":"Sprocket","years":4,"press":true}`
- game → player, after every event — **redacted**: the whole public board, the public city table,
  every treasury, this seat's own inbox and units, and nothing of any other power's pending orders,
  pending expenditure, private letters or notes:
  ```json
  {"type":"state","slot":N,"power":"VENICE","year":1500,"season":"summer","phase":"orders",
   "years":4,"yearsPlayed":1,"cities":5,"ducats":17,"units":[…own units…],
   "board":[…every unit…],"owners":[…24…],"counts":[6],"treasuries":[6],
   "famine":["MOD","APU"],"plague":"BOL","paralysed":false,
   "inbox":[{"from":"MILAN","text":"…","public":false}],
   "eliminated":false,"started":true,"done":false,"reason":""}
  ```
- game → player at the end:
  `{"type":"final","done":true,"slot":N,"scores":[6],"cities":[6],"ducats":[6],"units":[6],"powers":[6],"names":[6 aliases],"years":int,"reason":str,"conqueror":str}` — the final frame carries
  **aliases**, not policy names (babel's rule, `finishEpisode`).
- player → game: `{"type":"prompt","prompt":"…","scripted":"condottiere"}` — the prompt (≤ 4000
  runes) *is* the policy; `scripted` is `"condottiere"`/`"1"`/`"true"`/`"yes"` or `"banker"` to
  register the seat as rule-based, `""` for LLM-driven. The reference player sends it immediately
  on connect and again after `welcome` (babel's race guard).

### Global protocol

`WS /global` sends the full `tableStateJson` snapshot after every event, plus `type`, `game`,
`policyNames`, `events` (the append-only transcript, **including every private letter and every
ledger entry**), `started`, `done`, `connected` — babel's `snapshotJson`, field for field.
`/client/global` renders the live board; `/client/replay` plays a recorded episode; the static
bundle renders hosted replays.

### `src/cogiavelli_player.nim` (fork of `src/babel_player.nim`)

Reads `PLAYER_PROMPT` and `PLAYER_SCRIPTED`, delivers one `prompt` frame, then spectates until
`final` and exits. Default prompt when `PLAYER_PROMPT` is unset: *"Take the neutral cities first and
hold them with a unit inside, because an empty city rebels. Keep a reserve of at least fifteen
ducats: a bribe that buys a neighbour's army at the right moment is worth two campaigns, and a
defended unit is cheaper than a lost one. Promise peace to the strongest power and mean it until
you can afford not to."*

---

## Viewer

**All four viewer files come from one starter — `Metta-AI/cogame-babel` — and only from it:**
`replay-viewer/config.nims`, the wasm entry `replay-viewer/cogiavelli_replay.nim` (fork of
`replay-viewer/babel_replay.nim`), `replay-viewer/static_replay.js` and
`replay-viewer/index.html`. **Nothing is spliced in from any other starter** — not from bullwhip,
not from coworld-ctf. Babel's emscripten link flags are kept exactly as they are (`config.nims`:
`-O2`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`, `MODULARIZE=1`,
`EXPORT_NAME=CogiavelliReplayModule`, `EXPORTED_RUNTIME_METHODS=HEAPU8`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_cog_load_replay,_cog_payload_ptr,_cog_payload_len,_cog_error_ptr,_cog_error_len`)
plus babel's `emscripten_exit_with_live_runtime()` epilogue, and `static_replay.js` keeps calling
the module through that **same `CogiavelliReplayModule()` factory** with the same
`_malloc` / `HEAPU8.set` / `_cog_load_replay` / `_cog_payload_ptr` handshake babel's
`static_replay.js:91-125` performs. (cogame-lantern, 2026-08-23: one starter's shell on another's
link flags — `MODULARIZE`/`EXPORT_NAME` versus an `onRuntimeInitialized` bootstrap — deadlocks the
viewer silently with every asset returning 200.)

**Load signalling.** `client/renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame** —
babel already does exactly this at the end of `attachReplay`'s `makeRenderer` callback
(`client/renderer.js:1309`), kept verbatim, together with the `coworld-replay` `loading`/`ready`
postMessage bridge. On any failure (missing `?replay=`, the 20 s fetch timeout, a non-200, a wasm
rejection) `static_replay.js`'s `fail()` sets
`document.documentElement.setAttribute("data-replay-error", message)`, shows the Retry button and
posts the `error` envelope; a successful retry removes the attribute (`static_replay.js:56,107`).
`tools/ci/viewer_smoke.mjs` reads exactly these two signals.

**Bundle.** The manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` — **a
static wasm bundle, never a `/client/replay` pod.** `tools/build_replay_viewer.sh` (babel's, paths
renamed, committed `chmod +x`) is the `coworld build` hook: it compiles
`replay-viewer/cogiavelli_replay.nim` to wasm (locally with `emcc`, otherwise in the pinned
`emscripten/emsdk` container from `Dockerfile.replay-viewer`) and copies `cogiavelli_replay.js`,
`cogiavelli_replay.wasm`, `index.html`, `static_replay.js`, `client/renderer.js`,
`client/chrome.css`, `data/italy1499.json` and the `data/` art into the bundle, then re-asserts
`index.html` exists and `static_replay.js` mentions `data-replay`. It **`mkdir -p`s the output
directory's parent before the containment check** (ecos, 2026-08-23: babel's hook `cd`s into a
parent that CI has not created). The wasm module runs the **same Nim sim and the same adjudicator**
the server ran, so every arrow, every bounce, every coin purse and every ownership flip is
re-derived in the browser from the replay bytes.

### Chrome provenance — what is copied and what is appended

The pins name `client/chrome_common.js` and `client/replay_broadcast.html`. **The parley/babel
lineage ships neither file** (verified: `/workspace/starters/cogame-babel/client` contains exactly
`chrome.css`, `global.html`, `player.html`, `renderer.js`, `replay.html`, `fixtures/`). Those two
roles are held here by **`client/renderer.js` + `client/chrome.css`** (the shared chrome: topband,
scorebug, feed, scrubber, transport, endscreen, name map, effects, both drivers, replay pacing) and
**`client/replay.html`** (the broadcast page; `replay-viewer/index.html` is the same page with `./`
asset paths and the wasm script tags). Nothing is imported from a starter that does have those
filenames. The rule is applied to the files that exist:

- **`client/renderer.js` and `client/chrome.css` are copied byte-for-byte** from `cogame-babel`.
  `renderer.js` gains a **new appended section only** (`// ---------- Cogiavelli ----------`), and
  the two game-specific hooks it must replace — `describeEvent` and the canvas `draw` — are
  extended by adding Cogiavelli's kinds to their existing switches, never by rewriting the file
  around them. `chrome.css` gains **one appended block at the end**; no existing rule is edited or
  deleted (the file already accretes one appended block per game in this lineage). The appended CSS
  contains exactly:
  - `:root { --band: 96px; --hudscale: 1; }` (set for real by `relayout()`);
  - `.seat5 { --tc: var(--amber); }` — babel's palette stops at `.seat4`
    (`chrome.css:205-209`) and there are six powers;
  - `.plate-power`, `.plate-cities`, `.plate-ducats`, `.plate-stab` (red chip), `.plate-frozen`
    (ice-blue chip for a paralysed court), `.plate-out` (grey), and the override
    `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` — babel ships `flex: 0 1 auto`, which
    collapses policy names to `…` in the ~360 px featured-match iframe;
  - `#ducatbar` (the appended game element) sized with `font-size: calc(11px * var(--hudscale))`;
  - `.beat-label` plus a rule for **every beat kind the scrubber emits** — `.beat-marker.press`
    (paper, 8 px), `.beat-marker.orders` (seat-tinted, 10 px), `.beat-marker.spend` (gold, 10 px),
    `.beat-marker.bribe` (gold, 14 px), `.beat-marker.assassin` (crimson, 16 px),
    `.beat-marker.battle` (amber, 14 px), `.beat-marker.stab` (red, 16 px),
    `.beat-marker.cities` (amber, 12 px), `.beat-marker.plague` (green-grey, 14 px),
    `.beat-marker.famine` (brown, 12 px), `.beat-marker.winter` (pale blue, 12 px),
    `.beat-marker.end` (amber, 3 × 16 px);
  - feed colours `.feed-broadcast`, `.feed-letter`, `.feed-pledge`, `.feed-order`, `.feed-bounce`,
    `.feed-dislodge`, `.feed-stab`, `.feed-gift`, `.feed-bribe`, `.feed-dagger`, `.feed-cities`,
    `.feed-plague`, `.feed-famine`, `.feed-rebel`, `.feed-winter`, `.feed-illegal`, `.feed-notes`;
  - `#loading { bottom: var(--band); }` so the caption never sits over the transport;
  - the small-screen queries: `@media (max-width: 640px)` shortens `#ducatbar` to counts and hides
    `.plate-ducats` labels; `@media (max-width: 420px)` sets
    `#scorebug { grid-template-columns: repeat(2, 1fr); }` (six plates ⇒ three rows).
- **`client/replay.html` is babel's page with a game block appended** — never a rewrite that reuses
  the ids (cogame-gridlock, 2026-08-23). **Every element babel ships is kept, with its id:**
  `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`, `#feedtoggle`,
  `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`, `#transport`,
  `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, and the `fit()` +
  `bindFeedToggle` bootstrap. **Elements removed: none.** The only edits are (a) the wordmark's
  inner text `BA<span>BEL</span>` → `COGIA<span>VELLI</span>` and the `<title>`, and (b) **one
  appended element**, `<div id="ducatbar"></div>`, inserted between `#scorebug` and `#board-wrap`.
  `replay-viewer/index.html` gets the identical treatment (same page, `./` asset paths, the
  `cogiavelli_replay.js` / `static_replay.js` script tags babel's `index.html:37-39` already has).
- **Zoom: `#viewpanel` is dropped entirely.** Babel ships no zoom bar and no minimap and none is
  added. The Italy map is **always scaled to fit the canvas** (aspect-preserving, from the province
  polygon bounding box), so the board is never larger than the frame and pan/zoom controls would be
  dead weight. Small-screen legibility is handled by the automatic action box below, which takes no
  user input and therefore needs no panel.

### Transport rules

- `--band` and `--hudscale` are set **on `:root`** (`document.documentElement`) by a `relayout()`
  added to the page bootstrap of `client/replay.html` and `replay-viewer/index.html`, called on
  `load`, on `resize`, and from the existing feed-toggle resize path: it measures `#transport`'s
  `offsetHeight` into `--band` and sets `--hudscale = clamp(0.8, width / 960, 1.15)`. Babel's
  `fit()` is called from inside `relayout()`, so the canvas and the custom properties can never
  disagree.
- **Nothing is overlaid in the transport band.** `#transport` is the last child of `#stage` in
  normal flex flow; the only absolutely-positioned overlays (`#lightpool`, `#grain`, `#endscreen`)
  live inside `#board-wrap`, which ends where the band begins, and `#loading` is pinned above it
  with `bottom: var(--band)`.
- **The endcard stops at `var(--band)`** — `#endscreen` is `position: absolute; inset: 0` inside
  `#board-wrap`, whose bottom edge is exactly `var(--band)` above the page bottom — **and every
  seek dismisses it**: babel's `setIndex` calls `updateEndscreen(options.endscreen,
  payload.results, index >= events.length && events.length > 0, nameMap)` on *every* index change
  (`renderer.js:1277-1278`) and `updateEndscreen` toggles the `show` class. Babel's code, verbatim.
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` (`renderer.js:1145-1222`) is kept
  verbatim except that each beat is created as `<button type="button" class="beat-marker …">` with
  an `aria-label`/`title` and an `onclick` that seeks to that event index; the container keeps its
  drag-to-seek pointer handlers and the `scrub-head`/`scrub-fill` update. Beats are emitted for
  `press`, `orders`, `spend`, `bribe`, `assassin`, `battle`, `cities`, `plague`, `famine`,
  `winter`, `end`, plus a derived `stab` beat for every stab inside a `battle` — labelled in words:
  `"SPRING 1500 · LETTERS · Venice writes to Milan"`, `"SPRING 1500 · ORDERS · Venice"`,
  `"SPRING 1500 · PAYMENTS · Venice spends 15đ"`,
  `"BRIBE · Venice buys the Papal army in Rome for 15đ"`,
  `"DAGGER · Naples pays 18đ against Florence — 17, it lands"`,
  `"SPRING 1500 · BATTLE"`, `"STAB · Venice breaks peace with Milan"`,
  `"SPRING 1500 · CITIES · Venice 5"`, `"PLAGUE · Bologna"`, `"FAMINE · Modena, Apulia"`,
  `"WINTER 1500 · Turin rebels · Venice builds a fleet"`, `"FINAL"`. The appended CSS defines a
  rule for **each of those twelve kinds**. Babel's `round-span`/`round-sep` blocks become one span
  per season with a separator at each year boundary.
- **Naming guard** (cogame-tandem, 2026-08-23): the appended block's builders are named
  `markDucatBeat` and `buildDucatBar`, never `markBeat` or `buildScrub`, so nothing can be shadowed
  by a hoisted chrome alias assignment; `tests/test_viewer.nim` asserts that no top-level name in
  the appended block collides with a name the copied chrome defines above it.

### The stage — Renaissance Italy

**Real art, not placeholders.** `data/italy1499.json` is a hand-authored vector map committed with
the repo: for each of the 42 areas a polygon (8–24 points) in a 1000 × 900 space, a label anchor, a
city-dot position, and a unit anchor. It is drawn by `renderer.js` in babel's Ink & Print palette
(`chrome.css:1-31`): land in paper tones tinted toward the owning power's seat colour, seas in
muted ink-blue over babel's `arena_floor.png` as a paper grain, cities as amber stars (filled when
owned, hollow when neutral), province names in babel's `font.ttf`. Units are canvas tokens — an
**army** is a seat-coloured block bearing the power's initial, a **fleet** a seat-coloured pennant.
Three new committed sprites: `data/purse.png` (a coin purse), `data/dagger.png`, `data/die.png`.

The season plays as the idea's replay plan asks:

- **Letters:** each private letter animates as a paper envelope crossing from the sender's capital
  to the recipient's, seat-coloured, landing in the feed; broadcasts unfurl as a banner across the
  top; pledges hang as wax seals on the recipient's capital.
- **Payments (step 4–6), before any arrow moves:** a **coin purse** drops from the payer's capital
  onto the target. A successful `bribe_buy` **flips the unit's colour to the briber's** with a
  stamp; a successful `bribe_disband` burns the unit off the board; an outbid or defended bribe
  bounces off a shield with the defence number. Gifts fly as a purse from capital to capital and
  raise the recipient's `#ducatbar` segment.
- **The dagger beat:** an assassination draws a dagger over the target's capital and **rolls two
  dice on screen** next to the amount paid (`18đ needs 18 or less — 17`). On success the target's
  plate gets the `FROZEN` chip and its units grey out for the season; on failure the dagger snaps.
- **Battle:** every order draws **at once** — moves as arrows anchor to anchor, supports as a short
  glowing brace, convoys as a dashed sea path. Successful arrows travel; bounced arrows flash red
  and snap back with a `STANDOFF` tag; dislodged units shudder and retreat; a unit whose move or
  bribe breaks a pledge made that season gets a red **STAB** stamp.
- **Shocks:** famine provinces carry a spreading brown hatch from the moment they are drawn until
  Winter; the plague province blooms a spreading grey-green overlay and the units inside it fall;
  a rebelling city cracks its star and goes neutral.
- **Ownership flip:** at every `cities` event captured cities flip colour with a stamp and the bar
  race animates.
- **Small screens:** below 640 px the canvas draws an **action box** instead of the whole map — the
  bounding box of every area named in this season's orders and payments, padded by one province and
  at least 40 % of the map — chosen deterministically by `computeLayout`, with no controls.

### Readouts

- **`#clock`** (top band): `SPRING 1500 · LETTERS · WAITING ON 6`, `SPRING 1500 · ORDERS IN`,
  `SUMMER 1500 · BATTLE`, `WINTER 1500 · ACCOUNTS`, `FINAL · VENICE 9 CITIES`.
- **`#ducatbar`** (appended): the city bar race — one seat-coloured segment per power, width ∝
  cities, labelled `VENICE 5` inside the segment when it fits and above it when it does not, a grey
  `NEUTRAL 3` tail for unclaimed cities, a thin **12-city victory line**, and under each segment a
  small coin figure with that power's treasury (`17đ`) that ticks whenever money moves.
- **`#scorebug`**: six plates — `VENICE · daveey · 5` with the city count as the big figure, a small
  `4 units · 17đ` label, `▶` while the table waits on that seat, a red `STAB` chip on the season it
  broke a pledge, an ice `FROZEN` chip while paralysed, a grey `OUT` chip once eliminated.
- **`#feed`** (the log), grouped by season head (`SPRING 1500 · LETTERS`, `SPRING 1500 · ORDERS`,
  `SPRING 1500 · BATTLE`, `WINTER 1500`), all in words a casual spectator can read — never internal
  notation like `p17`, `u3` or `okSupportMove`:
  - `Venice broadcasts: "Bologna belongs to nobody. Let it stay that way."`
  - `Venice → Milan (private): "Take Turin and I will not cross the Po."`
  - `Venice pledges peace to Milan.`
  - `Venice gives Naples 6 ducats.` *(binding — the money has moved)*
  - `Venice pays 15 ducats to buy the Papal army in Rome. It changes sides.`
  - `Florence pays 9 ducats to disband the Turkish fleet in Ragusa — the Turk had paid 4 to keep it loyal, and the bribe fails.`
  - `Naples pays 18 ducats for a dagger against Florence. The dice show 3 and 5 — 17. Florence's court is frozen.`
  - `Venice orders Verona → Mantua; the fleet at Venice supports it.`
  - `Milan's Pavia → Mantua bounces. STANDOFF in Mantua.`
  - `The Papal army in Ancona is dislodged by Urbino (supported by Perugia) and retreats to Abruzzi.`
  - `STAB — Venice promised Milan peace and took Mantua.`
  - `Summer 1500 cities: Venice 5 (+1 Ferrara), Milan 4, Florence 3, Papacy 3 (−1 Ancona)…`
  - `PLAGUE strikes Bologna. Two units are lost and it pays nothing this year.`
  - `FAMINE this year: Modena and Apulia.`
  - `Winter 1500 — Turin rebels against Milan. Venice collects 17 ducats, pays 4 in upkeep, and builds a fleet at Venice.`
  - `Final — Venice 9 of 24 cities and 21 ducats (0.411) after 4 years.`;
    `Episode deadline — scored on the board as it stood in Summer 1502.` when
    `reason == "deadline"`; `Venice holds 12 cities — ITALY IS HERS.` when `reason == "conquest"`.
  - Illegal orders show dim: `The Turk ordered Ragusa → Bari — not adjacent; Ragusa holds.`
  - Dropped payments show dim: `Naples tried to bribe the Venetian army in Verona but had 7 ducats.`
- **`#endscreen`**: title `FINAL — 4 YEARS · 24 CITIES`; verdict `<name> (VENICE) LED ITALY`, or
  `<name> (VENICE) TOOK ITALY` on a conquest; a reason line for `deadline`; rows ranked by score
  with columns `power`, `cities`, `ducats`, `spent`, `stabs`, `score`. Beside the rows the
  **ledger** the idea asks for: a six-by-six matrix of who paid what to whom over the episode
  (gifts, bribes and daggers in separate glyphs, totals in ducats), animating one year per second
  in a loop. It is inside `#endscreen`, so it stops at `var(--band)` and every seek dismisses it.

### Legible at 360 px wide

The canvas re-fits on every `relayout()`. **The whole viewer is legible at 360 px:** below 640 px
the map switches to the action box, province names drop to the areas named this season,
`#ducatbar` shows counts and coin figures without power names, the plates keep `power` + city count
and drop the unit/ducat labels, and the feed collapses behind babel's existing `LOG »` toggle;
below 420 px the scorebug goes to two columns (three rows). `.plate-name` is overridden to
`flex: 1 1 auto; min-width: 3.2em` so policy names do not collapse to ellipses in the featured-match
iframe. Everything renders as words and numerals — `Bologna`, `STANDOFF`, `5 cities`, `17đ` — and
the scorebug is checked at 360 px, not at desktop width.

---

## Packaging

- **`compose.yaml`** — service **`cogiavelli`** (= the coworld name), `image:
  coworld-cogiavelli:latest`, `platform: linux/amd64`, `build: {context: ., network: host}`. The
  manifest image placeholder is derived from the compose service name — **`{{COGIAVELLI_IMAGE}}`** —
  because `coworld build` maps compose services to placeholders and hard-fails anything else
  (cogame-lantern 0.1.0, 2026-08-23).
- **`Dockerfile`** — babel's, renamed: one image, two entrypoints, `/bin/cogiavelli` (default `CMD`)
  and `/bin/cogiavelli-player`; `client/` and `data/` copied into the run image; `nim.cfg`
  regenerated from the container's synced package tree.
  **`Dockerfile.replay-viewer`** — babel's, renamed (pinned emsdk + nimby 0.1.26 + Nim 2.2.4).
- **`cogiavelli.nimble`**, `nimby.lock` — babel's, renamed; same pinned dependency set
  (`bitworld`, `mummy`, `curly`, `whisky`).
- **`.github/workflows/ci.yml`** and **`coworld-release.yml`** from `coworld-builder/templates/`,
  substituting `<slug>` = `cogiavelli`, `<IMAGE>` = `coworld-cogiavelli`, **`<SEATS>` = `6`**.
  `tools/ci/docker_smoke.sh` (substituted, `chmod +x`) and `tools/ci/viewer_smoke.mjs` (verbatim, no
  substitutions) are copied from the same templates.

### `coworld_manifest_template.json`

- `$schema` + **≥ 3 tags**: `diplomacy`, `negotiation`, `bribery`, `llm-driven`, `turn-based`,
  `six-player`, `mixed-motive`.
- `game.name` = `cogiavelli`; `game.runnable.type` = `"game"`; `game.runnable.image` =
  `{{COGIAVELLI_IMAGE}}`, `run` `["/bin/cogiavelli"]`, **`env.ANTHROPIC_API_KEY_URI` =
  `secret://coworld/cogiavelli/anthropic_api_key`** (without it the hosted container never receives
  the secret and every league episode silently plays scripted — hive, 2026-08-23); `source_url`
  `https://github.com/Metta-AI/cogame-cogiavelli/tree/main` (repo **public** — a certification
  prerequisite); `episode_timeout_minutes` top-level = 20.
- **`game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.**
- `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
  `["tokens","players"]`. **Every array property carries `minItems` and `maxItems`** (tandem 0.1.0):
  `tokens` and `players` both `minItems: 6, maxItems: 6`; **`num_agents` integer `minimum: 6,
  maximum: 6`**; `seed` integer; `years` integer 1..10 default 4; `press` boolean default true;
  `episodeTimeoutSeconds` integer 60..6000 default 1200; `turnDelayMs` integer 0..10000 default 300;
  `model` string default `claude-sonnet-5`; `maxOutputTokens` integer 64..2000 default 1200;
  `llmTimeoutSeconds` integer 5..300 default 45; `player_connect_timeout_seconds` number ≥ 0
  default 180.
- `game.results_schema` — `additionalProperties: false`, all keys required: `names`, `powers`,
  `scores` (6 numbers, `minimum: 0`, `maximum: 1`), `cities`, `ducats`, `units`, `spent`,
  `received` (6 integers each, all arrays `minItems: 6, maxItems: 6`), `years`, `maxYears`,
  `conqueror`, `reason`.
- **`game.protocols`** carries **both** entries, each as `{"type":"text","value":"…"}` (bare strings
  fail the platform validator — cogame-garble, 2026-08-24): `player` (the `cogiavelli.player.v1`
  description above, including "a policy is just a prompt" and the `PLAYER_SCRIPTED` values) and
  `global` (the `/global` snapshot shape, the 13 event kinds, and the note that the events array
  carries every private letter and every ledger entry for spectators).
- **`game.docs`** carries `readme` **and** `pages`, all `{"type":"text","value":"…"}`:
  - `readme` — what the game is, that a policy is a prompt, how to field one with `PLAYER_PROMPT`.
  - `pages[0]` `rules.md` — the calendar, the numbered resolution order, press and pledges, the
    money rules with every cost, the shocks with their exact probabilities, scoring and its sign,
    the three end reasons.
  - `pages[1]` `map.md` — the 42 areas with codes and full names, the 24 cities, the home
    assignments, the two movement graphs including the Strait of Messina rule, the 18 starting
    units, and the order-notation grammar with worked examples.

### Player runnables

| id | name | env | purpose |
|---|---|---|---|
| `cogiavelli-player` | Cogiavelli Prompt Player | `PLAYER_PROMPT` (secret-env at upload) | the reference policy: a prompt |
| `cogiavelli-condottiere` | Cogiavelli Condottiere Baseline | `PLAYER_SCRIPTED=condottiere` | the scripted expander |
| `cogiavelli-banker` | Cogiavelli Banker Baseline | `PLAYER_SCRIPTED=banker` | the scripted hoarder |

All three run `/bin/cogiavelli-player` from the **same image** — LLM policy and scripted baseline
are one image, env-switched, from day one. `tools/ci/policies.json` seeds two **`PLAYER_PROMPT`**
champions, `cogiavelli-medici` (money-first: buy alliances, defend units, build late) and
`cogiavelli-borgia` (steel-first: early stabs, daggers when a rival leads), plus the two scripted
baselines as fillers; every policy entry also carries **`"USE_BEDROCK": "true"`** in its `env`
(cogolf, 2026-08-24: without it the platform gives the player pod no Bedrock sidecar and the seat
silently plays scripted).

### Variants — `num_agents` in every one

| id | name | description | game_config |
|---|---|---|---|
| `standard` | Standard game | Six powers, three seasons a year, four years, letters and ledgers. | `players`: 6 named entries, **`num_agents: 6`**, `years: 4`, `press: true`, `turnDelayMs: 300`, `player_connect_timeout_seconds: 180` |
| `gunboat` | Gunboat (no letters) | No press: only ducats and orders speak. Six years in the same budget. | `players`: 6 named entries, **`num_agents: 6`**, `years: 6`, `press: false`, `turnDelayMs: 300`, `player_connect_timeout_seconds: 180` |

### Certification fixture

```json
"certification": {
  "game_config": {
    "players": [{"name":"Sprocket"},{"name":"Gizmo"},{"name":"Ratchet"},
                {"name":"Widget"},{"name":"Bolt"},{"name":"Piston"}],
    "num_agents": 6, "seed": 7, "years": 1, "press": true, "turnDelayMs": 0,
    "player_connect_timeout_seconds": 180
  },
  "players": [{"player_id":"cogiavelli-player"},{"player_id":"cogiavelli-condottiere"},
              {"player_id":"cogiavelli-player"},{"player_id":"cogiavelli-banker"},
              {"player_id":"cogiavelli-condottiere"},{"player_id":"cogiavelli-player"}]
}
```

**`num_agents: 6`** appears here and in both variants; `<SEATS>` in `tools/ci/docker_smoke.sh` is
`6`, an independent cross-check that fails CI if the manifest ever disagrees. **Every declared
player runnable occupies at least one certification slot** (raid 0.1.2 → 0.1.3, 2026-08-23).

### Design pins (playbook §Phase 0 / SPEC §Design) — how each is satisfied

| pin | how |
|---|---|
| Starter by game shape | `cogame-babel` — turn-based board game, rules native in Nim, policy = LLM prompt. Named at the top with the reason; the only two imports from bullwhip (`decideAll` batching, named `ScriptKind`) are named there too. |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-cogiavelli`, public; `source_url` points at `/tree/main`. |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `cogiavelli-player` (`PLAYER_PROMPT`) and `cogiavelli-condottiere` / `cogiavelli-banker` (`PLAYER_SCRIPTED=<name>`), all `/bin/cogiavelli-player` from `{{COGIAVELLI_IMAGE}}`. Both champions are prompt policies; both fillers are scripted. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` viewer is declared in the manifest. |
| Real art, starter chrome verbatim | Hand-authored `data/italy1499.json` in babel's Ink & Print palette plus three new sprites; `renderer.js`/`chrome.css` copied byte-for-byte with appended sections only; `replay.html` = babel's page + one appended `#ducatbar`; nothing removed. |
| Two name spaces | In-game: power names only (seed-assigned) + cog aliases; spectator-side: `policyNames` in the replay and in `results.json`. Both recorded. |
| Degrade, never hang | 60 % play budget (720 s), deadline checked before every batch and season transition, retry-once → scripted fallback, `reason = "deadline"` settles early, bounded shutdown grace. |
| `num_agents` everywhere | 6 in `standard`, 6 in `gunboat`, 6 in the certification fixture, 6 as `<SEATS>`. |
| Replay bytes self-sufficient | names, policyNames, powers, config (years/seed/press/sampled/victoryCities/map), every letter, pledge, order, ledger entry, dice roll, battle result, ownership table, shock draw, and the results object. |

---

## Tests

CI (`ci.yml`) is the only harness; the sandbox runs none of this locally. Every `tests/*.nim` runs
twice, debug and `-d:release`.

### `tests/test_map.nim` — map integrity

42 areas; 36 land / 6 sea; exactly 24 cities with the listed codes; 18 home cities mapping back to
the right power and 6 neutrals; **both adjacency graphs symmetric**; no army adjacency touches a
sea; no fleet adjacency touches an inland province; every coast-hop shares a sea and `BAR–CAL` is
**not** one; `CAL–MES` exists in `fleetAdj` and not in `armyAdj`; the land graph is connected and
the fleet graph is connected; every one of the 18 start units is legal for its province; `PIS`,
`ROM`, `CAL`, `MES`, `AVL` each touch only mutually adjacent seas (the no-split-coast invariant);
`bfsDistance` is finite from every land province to some city.

### `tests/test_adjudicate.nim` — the classic cases, one assertion each

1. Move to an empty province succeeds; to an occupied one at equal strength it bounces.
2. Standoff: two unsupported moves to the same province — both bounce, both units stay.
3. Three-way standoff; a standoff province is barred as a retreat destination.
4. Supported attack dislodges: `A URB - ANC` + `A PER S A URB - ANC` beats `F ANC H`.
5. Cut support: `A MAN - VER` cuts `A VER S A PAD - FER`, so the attack on Ferrara fails.
6. Support is **not** cut by an attack out of the province it supports into.
7. Dislodging a supporter always cuts its support, even from the supported direction.
8. Self-dislodgement ban: a power's supported move into its own unit's province fails and the own
   unit is not dislodged.
9. A power may not support a foreign attack that dislodges its own unit.
10. Beleaguered garrison: two equal supported attacks — both bounce, the defender survives.
11. Circular movement: three units in a ring all succeed; an external attack that beats one link
    fails the whole ring.
12. Convoy succeeds with one fleet (`A BAR - PAL` via `F LTS`… through `ION`,`LTS`) and with a
    three-fleet chain.
13. Convoy disruption: the convoying fleet is dislodged ⇒ the army holds in its origin
    (`noconvoy`), and its province is not vacated.
14. Convoy with an alternative path survives one fleet's dislodgement.
15. Szykman paradox: the paradoxical convoyed move fails; the convoying fleet's dislodgement stands.
16. Support matching: `F VEN S A PAD - FER` is void when the army ordered `- FRI`; the fleet holds.
17. Illegal-order repair: a fleet ordered inland, an army ordered to sea, an army ordered `CAL - MES`
    without a convoy, a support of a non-adjacent destination and a convoy ordered by an army each
    become a hold with the documented `why`.
18. Head-to-head: `A VER - MAN` vs `A MAN - VER` bounce; with one support the stronger dislodges.
19. Retreat rules: never to the attacker's origin, a standoff province, or an occupied province;
    two dislodged units contesting one destination — the lower province code takes it, the other
    re-picks or disbands.

### `tests/test_money.nim` — the ducat layer

Payment order (entries validated in the order written; the third of three unaffordable entries is
the one dropped); a `gift` credits the recipient in the same step and can never be reversed; a
`bribe_disband` at exactly 9 succeeds against 0 defence and fails against 1; a `bribe_buy` at 15
transfers the unit and forces it to hold that season; **equal competing bribes both fail and both
payers still lose the money**; the larger of two qualifying bribes wins; a bribe on one's own unit
and an assassination on oneself are dropped as `illegal`; assassination `amount` clamps to 6..30 and
`roll ≤ amount` decides, with a fixed-seed table pinning ten outcomes; paralysis holds every unit
of the target this season and blocks its next press window and nothing else; income = 3 × cities
minus famine/plague cities plus the recorded draw; upkeep disbands the furthest unit first and ties
break by province code; a rebellion fires only on a d6 of 1, only on a non-home owned city, and only
when no unit stands in it; a build costs 3, needs a vacant owned city, and a fleet needs a coastal
one; **the same seed reproduces every famine, dagger, plague, rebellion and income draw
byte-for-byte, and `replayMatch` raises when a recorded draw is altered.**

### `tests/test_sim.nim` — the episode

Season sequencing (`press → orders → resolve` × 3, then Winter, then the next year) and that Winter
takes no decision; ownership flips every season, not only in Autumn; the conquest check fires at 12
cities and at last-power-standing; `endEarly` yields `reason = "deadline"` and scores the standing
board; `resultsJson` shape and score sign (every score in `[0, 1]`, conquest = 1.0/0.0, treasury
term capped at one city); press caps (`broadcast`, `letters[].text`, `notes`) truncate **on rune
boundaries** with a multi-byte/emoji fixture and the result is valid UTF-8; a sixth letter, a fifth
pledge and a seventh spend entry are dropped; a letter to an unknown power is dropped; **policy
names never appear in any prompt built by `llm.nim`** (every `config.players[i].name` scanned
against `systemPrompt`/`userPrompt`); event JSON round-trips (`eventFromJson(eventToJson(e)) == e`)
for all 13 kinds; `replayMatch` gives `frames.len == events.len + 1` and a final frame equal to the
live `tableStateJson`; two `initSim` calls with the same seed give the same power permutation, the
same aliases and byte-identical event logs.

### `tests/test_bot.nim` — bounded-orders / legality assertion on the scripted baselines

Six `condottiere` seats play full episodes for seeds 1..8: **every submitted order parses and is
legal** (`illegal` is empty in every `orders` event), every unit is ordered exactly once, no power
ever stands itself off, **every spend entry is affordable at the moment it is validated and no
`spend` array exceeds 6 entries**, every build is in a vacant owned city with a legal unit kind, no
treasury ever goes negative, and the episode always reaches `reason = "complete"`. The same for six
`banker` seats, plus a mixed table (3 `condottiere`, 3 `banker`) and a table of five `banker` seats
and one `condottiere` (the condottiere must end with more cities — a baseline that cannot beat a
wall is no baseline). `decideAll` with no credentials returns scripted decisions for all six seats
with **no network call**, and an episode of six scripted seats finishes in under
`years × 3 × 1000` ms. Reply parsing: fenced JSON, prose-wrapped JSON, a missing `orders` key
(invalid ⇒ retry), an oversize order string, a non-integer `amount`, and an unknown `spend.action`.

### `tests/test_score.nim`

The share-plus-treasury formula on hand-built boards (unclaimed neutrals dilute everyone; 24 ducats
is worth exactly one city and 48 is still worth one); conquest at exactly 12 gives `1.0` / `0.0`s;
an eliminated power scores its treasury term only; a `deadline` stop in the first Spring scores the
home cities (`3/24` plus the starting-treasury term).

### `tests/test_viewer.nim`

`tableStateJson` carries every key the renderer reads (asserted against a literal key list); the
replay payload is **strict UTF-8** (`validateUtf8($payload) == -1`) and re-parses with `parseJson`
after a press fixture stuffed with multi-byte text; the appended viewer block defines no top-level
name that the copied chrome already defines.

### CI jobs

- **`test`** — every `tests/*.nim`, debug and release.
- **`docker-smoke`** — builds the production image and runs one **end-to-end episode in raw docker
  with six player containers** from the certification fixture's seat mix (no LLM credentials, so
  every seat plays a baseline), asserting the game exits 0, `results.json` validates against
  `results_schema`, `reason == "complete"`, six scores, and that the written `.replay` **parses as
  strict UTF-8 JSON** and carries `events`, `results`, `names`, `policyNames`, `powers` and
  `config`. The seat count comes solely from `certification.game_config.num_agents` and is
  cross-checked against `SMOKE_SEATS=6` (a `SEAT-COUNT FAIL:` line is a hard failure). The replay is
  copied to `dist/smoke/` and uploaded as the `smoke-replay` artifact.
- **`wasm-viewer`** (`needs: docker-smoke`) — builds the bundle with `./tools/build_replay_viewer.sh`
  (asserting the hook exists and is executable), asserts `index.html` and a non-empty `.wasm`, then
  **executes the bundle**:
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json --timeout 90 --soak 10`
  in headless chromium. It fails unless `data-replay-loaded="true"` appears, fails immediately on
  `data-replay-error`, and the `--soak` window fails a replay that stops advancing mid-playback
  (cogball 0.1.4). The certification-fixture episode is 1 year × 3 seasons ≈ 40+ events, comfortably
  longer than the soak window. Screenshot and JSON are uploaded always.

---

## Out of scope (v1)

- **Garrisons** — Machiavelli's third unit type, sieges, garrison conversion, and bribing a garrison
  out of a fortress. Bribes here target field armies and fleets only. This is the single biggest cut
  against the Avalon Hill rules and it is deliberate: garrisons would add a third movement graph, a
  siege clock and a fourth decision phase to a budget that has room for none of them.
- **France and Austria** — the idea's other two powers. Their homelands are off the Italian board,
  which would need an off-map income abstraction; six on-board powers instead.
- **Split coasts** — no province on this map touches two non-adjacent seas, so `SPA/NC`-style coast
  notation does not exist and never has to be disambiguated.
- **A retreat or a build decision call.** Retreats and forced disbands are decided by rule (steps 9,
  W4) and builds ride on the Autumn expenditure sheet. Each would cost a batch per season.
- **A second press round per season**, retreat-phase press, forged or anonymous letters, and
  attaching an order set to a letter.
- **Loans, interest, bank failures, mercenary contracts with expiry (condotta), and famine/plague
  spreading to neighbouring provinces.** Shocks are single-province events drawn once.
- **Special characters** (Machiavelli's expansions), papal interdiction, excommunication, and
  the Turkish "invasion" special rules.
- **Draws, concessions and DIAS votes** — an episode ends only by conquest, cap, or deadline.
- **Variant maps, other power counts, and other victory numbers.** Six seats, 24 cities, 12 to win.
- **Cross-episode memory** of any kind; every episode starts in 1499 with 12 ducats and fresh notes.
- **Zoom/pan controls and a minimap** — the map is always fitted to the frame.
