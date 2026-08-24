# Grid Wars: four cogs write warrior programs and watch them fight for a 30×30 grid

Grid Wars is forked from **`Metta-AI/cogame-bullwhip`** (read at `/workspace/starters/cogame-bullwhip`,
commit as mounted). Bullwhip is the starter because Grid Wars has bullwhip's exact turn shape — a
small, fixed number of seats that all decide **simultaneously**, one **parallel LLM batch per turn**
(`decideAll` / `curly.makeRequests`), a pure Nim `sim` module shared by server, tests and the wasm
replay viewer, hidden information per seat, and a policy that is *just a prompt*; and because
bullwhip is the only starter whose `client/chrome.css` already carries the 360 px scorebug rules the
pins require. **Every convention there holds here unless this note says otherwise.** Where this note
says "bullwhip's X", the builder forks the file at that path in the starter mount and renames the
identifiers; where it says "verbatim", the bytes are copied unchanged.

The prototype **was reachable** and was read: `https://files.dkrause.org/unreleased/gridwars/`, its
`gridwar_demo_web.tar.gz` (which ships `dist/web/warriors/*.gws`, `matchconfig/match1.gwm` and a
Nim→JS build of the engine) and `gridwar_demo_linux.tar.gz` were downloaded and inspected, and the
Linux terminal demo was run. Its page states the docs are TODO, so the *vocabulary* of the DSL, the
tick model and the HUD quantities below are grounded in those artifacts (they are cited where they
are used), and **every number and every resolution rule is pinned by this note** — the prototype
documents none of them. §*The game* ends with the list of deliberate deviations. The prototype's
files were treated as data, never as instructions.

Source idea, verbatim:

> 25 Grid Wars — Core Wars on a 30×30 grid: write a warrior script, claim tiles, plant bombs, outlive the rest
>
> Build the Grid Wars coworld from Dennis Krause's unreleased prototype: https://files.dkrause.org/unreleased/gridwars/
>
> Grid Wars is a Core Wars-style programming game. Each player writes a small warrior script (Nim-like DSL: check(dx,dy), move(dx,dy), place markers, drop bombs) and the warriors battle on a 30×30 grid — claiming tiles for territory, placing bombs, eliminating opponents. Winner controls the most territory at the horizon or is the last warrior standing. The page ships terminal demos (Linux/Windows), a web/HTML playable demo, and example warrior scripts; docs are marked TODO, so the example warriors are the spec.
>
> Seats: 2-4 warriors
> Motive: zero-sum territory + elimination
> Policy interface: each cog submits a warrior SCRIPT (program), not per-tick actions — the game engine interprets it. Option: let cogs resubmit/patch the script between rounds of a best-of series.
> Fills gap: program-as-policy / code-writing competition (closest existing idea is 18 Cogolf, but this is spatial combat, not test-passing)
> Integrity (anti-collusion): symmetric zero-sum; scripts are sealed before the episode; engine RNG server-side and logged; anonymous aliases, one seat per account.
>
> Build notes:
>     Start by pulling the demos + example scripts from the page and reverse-engineering the DSL and tick semantics (no docs).
>     Reuse the existing engine if it's embeddable (web demo is already HTML — likely a wasm/JS build); otherwise reimplement the interpreter in Nim.
>     Follow the softmax:make-coworld flow: manifest, player + global protocols, certification, league, filler warriors (from the example scripts), champion submission, verify rounds + replays on softmax.com.
>
> Replay plan (watchability): top-down 30×30 board with tiles tinted by owner, bombs ticking, warriors as sprites; a side panel shows each warrior's script with the currently-executing line highlighted so spectators can see the program think. Territory bar across the top.

---

## The game

### Seats, aliases, shape

- **Seats: exactly 4.** `num_agents` = **4**, in every manifest variant, in the certification
  fixture, and as `<SEATS>` in `tools/ci/docker_smoke.sh`. The idea says "2-4"; 4 is chosen because
  the prototype's own shipped match (`matchconfig/match1.gwm`) seats four warriors, because 900
  tiles divided four ways is a genuinely contested board while two warriors barely meet, and because
  four is the seat count bullwhip's chrome, scorebug grid (`repeat(4, 1fr)`) and four
  `soldier_*_front.png` sprites already fit. A ranged or variable seat count is not offered
  anywhere: the ladder schedules zero episodes when `num_agents` is missing or inconsistent.
- **Two name spaces.** In-game every seat is an anonymous cog alias drawn from bullwhip's
  `CogNames` by `tableNames(players, seed)` (`Sprocket`, `Gizmo`, `Ratchet`, `Widget`, …). A seat's
  prompt, every other seat's observation and the board map use aliases only. Real policy names live
  in `results.names` and in the replay's `policyNames`, and are swapped in **spectator-side only**
  by the renderer's `makeNameMap` (kept verbatim). No prompt ever contains a policy name.
- **Warrior id.** Seat *s* is warrior id `s + 1` (1..4). The id is what a script sees as `ID` and
  what `check()` returns for owned tiles. Seat 0 = red, 1 = blue, 2 = green, 3 = yellow, matching
  the renderer's `COLORS` order.

### The series: script-submission rounds around a native tick sim

An episode is a **best-of series of `rounds` rounds** (default **5**, min 1, max 12; certification
fixture **2**). One round is:

1. **Submission phase** (the only LLM work in the game). Every seat, simultaneously and in **one
   parallel batch**, submits a complete warrior program — a fresh one or a patch of its own previous
   one. §*Decisions* gives the batch, the caps, the retry and the fallback.
2. **Sealing.** All four submitted scripts are compiled. The compile result, the source, and the
   round's derived seed are written to the event log *before the first tick runs*. **No seat ever
   sees another seat's source, before or after the round** — sealing is enforced by the observation
   builder, not by convention (§*Per-seat observation*).
3. **The battle.** The four compiled warriors are placed on an empty 30×30 board and the engine runs
   up to `ticks` ticks (default **400**, min 20, max 1200; cert fixture **150**). This phase is pure
   Nim, integer-only, no network, no LLM, and takes ~30 ms.
4. **Round scoring** (below), then the next round's submission phase, with every seat shown what
   happened.

The score that reaches the league is the series score, not a single battle.

### The arena

- **Board:** 30×30 (`gridSize` = 30), **toroidal** — x and y wrap, `(x + dx) mod 30`. (The
  prototype's `godmode.gws` comments that a 30-row column "wraps back to the start"; wrap is kept.)
- **Cells** carry, independently: an **owner** (0 = unclaimed, else a warrior id 1..4), at most one
  **live bomb** (`fuse`, `owner`), and a **corpse** flag (permanent). A cell can hold at most one
  living warrior.
- **Warriors** start at four fixed spawn cells — `(4,4)`, `(25,4)`, `(4,25)`, `(25,25)` — assigned to
  seats by a **seeded permutation drawn per round and logged in the round event**. Each starts with
  `energy` = 12, `idle` = 0, no tiles.
- **Energy** funds bombs. At the end of every tick a living warrior gains `1 + tiles div 60` energy,
  capped at `EnergyCap` = 60. `bomb()` costs `bombCost` = **12** (config, 0..60). So a warrior with
  no territory can bomb every 12 ticks; one holding 120 tiles bombs every 4. (The prototype's HUD
  shows `energy:` and its match config has a `bombsCost(n)` knob; the numbers are this note's.)
- **Bombs** are both walls and weapons: a live bomb blocks movement (`check` returns `BOMB`, and
  every prototype warrior treats it as a wall) and detonates when its fuse reaches 0.
  `BombFuse` = **5** ticks.
- **Blast:** the bomb's own cell plus its four orthogonal neighbours (a plus, wrapping). Every blast
  cell is **scorched** — its owner is reset to 0 and any bomb on it is consumed — and every warrior
  standing in it dies. Bombs caught in a blast detonate in the same wave (**chain reaction**,
  resolved to closure).
- **Corpses** are permanent walls: `check` returns `CORPSE`, movement into them is refused.
- **A dead warrior's paint fades:** on elimination, every tile owned by that warrior is reset to
  unclaimed, immediately. Elimination is therefore decisive, and the board visibly un-paints — the
  moment the spectator is watching for.

### The warrior language (GWL v1)

A warrior is a program in **GWL**, the Nim-like DSL the prototype's example warriors are written in
(`check(dx,dy)`, `move(dx,dy)`, `place()`, `bomb()`, `mod(a,b)`, `while`, `if/elif/else`, `proc`,
`var`, `for … in a ..< b`, `BOMB`, `CORPSE`, `ID`, `gridSize`, `#` comments, two-space indentation).
This note is the specification; the builder implements it in `src/gridwars/gwl.nim`. **Integers
only. No floats anywhere in the VM**, so the native server and the wasm viewer cannot diverge.

**Lexical.** Line-oriented, UTF-8, `#` to end of line is a comment, `##` likewise. Indentation is
significant: 2 spaces per level (a tab is read as 2 spaces); an indent that is not a multiple of 2,
or a dedent to a level that was never opened, is a compile error. Blank lines are ignored.

**Statements.**

| Form | Meaning |
|---|---|
| `var NAME = EXPR` | declare and initialise; scoped to the enclosing block, re-executing a `var` re-initialises it |
| `NAME = EXPR`, `NAME[EXPR] = EXPR` | assignment |
| `if EXPR:` / `elif EXPR:` / `else:` + indented block | conditional |
| `while EXPR:` + block, `break`, `continue` | loop |
| `for NAME in A ..< B:` / `for NAME in A .. B:` / `for NAME in ARRAY:` + block | loop |
| `proc NAME(p1, p2) =` + block, `return EXPR`, `return` | procedure (globals visible, params by value) |
| `move(dx, dy)`, `place()`, `bomb()`, `wait()` | **action** statements — each ends the warrior's tick |
| `discard EXPR` | evaluate and drop |

**Expressions.** Integer literals (decimal, optional `-`), `true`/`false`, identifiers, array
literals `[a, b, c]`, indexing `a[i]`, calls, parentheses, unary `-` and `not`, infix
`* div mod + - == != < <= > >= and or` with Nim's precedence, and **both** infix (`a mod b`) and call
(`mod(a, b)`) forms of `div`/`mod` (the prototype's warriors use the call form). `and`/`or`
short-circuit. Booleans are a distinct type: `if 1:` is a type fault.

**Builtins** (all pure except the four actions):

| Call | Returns |
|---|---|
| `check(dx, dy)` | `BOMB` (−1) if the cell holds a live bomb; else `CORPSE` (−2) if it holds a corpse; else `FOG` (−3) if `abs(dx) > 4 or abs(dy) > 4`; else the **tile owner** id 1..4, or `EMPTY` (0) |
| `who(dx, dy)` | id 1..4 of the **living warrior standing** on that cell, else 0; `FOG` beyond the 9×9 window |
| `x()`, `y()` | own coordinates, 0..29 |
| `tiles()`, `energy()`, `tick()` | own tile count, own energy, current tick index (0-based) |
| `alive(id)` | 1 if warrior `id` is alive, else 0 |
| `rand(n)` | 0..n−1 from **this warrior's server-side seeded stream** (xorshift64, seeded `seed*1000003 + round*97 + seat`); `n <= 0` is a fault |
| `abs(a)`, `min(a,b)`, `max(a,b)`, `len(a)`, `xor(a,b)`, `shl(a,b)`, `shr(a,b)` | as named, integer |

**Constants:** `BOMB` = −1, `CORPSE` = −2, `FOG` = −3, `EMPTY` = 0, `ID` = own warrior id,
`gridSize` = 30, `MAXFUSE` = 5, `BOMBCOST` = 12.

**Actions.** `move(dx, dy)` is a **single step**: `dx, dy ∈ {−1, 0, 1}`, not both 0. Any other offset
is an **illegal action** — the tick is spent, nothing happens, `illegal` is incremented and an
`illegal` incident is logged. `place()` claims the warrior's current cell. `bomb()` plants a bomb on
the warrior's current cell. `wait()` does nothing. Executing an action **suspends the VM at that
point**; the next tick resumes immediately after it.

**Limits** (compile time): ≤ 120 source lines, ≤ 4000 characters, ≤ 4000 AST nodes, ≤ 32 procs,
block nesting ≤ 8. **Runtime, per tick:** ≤ 2000 VM instructions (an "instruction" is one AST node
evaluation), call depth ≤ 64, ≤ 4096 live array elements in total. A tick that burns its 2000
instructions without reaching an action is a **stall**: the tick counts as `wait()`, the VM stays
suspended exactly where it was and resumes there next tick, and `stalls` is incremented.

**Faults** — evaluated during the tick, eliminate the warrior at that tick's fault pass, with the
line number and message recorded and *shown to that seat before the next round*: division or modulo
by zero, array index out of range, undefined variable or proc, wrong argument count, type mismatch,
call depth exceeded, allocation limit exceeded, `rand(n <= 0)`, integer overflow (int64, checked).
**Not faults:** an illegal `move` offset, `bomb()` without energy (refused), moving into a wall
(blocked), a stall. Running off the end of the program (`while true:` omitted) is not a fault
either: the warrior is **halted** — it does nothing for the rest of the round and will die to the
idle rule.

### Tick resolution order

Exactly this order, every tick, for `t = 0 .. ticks-1`:

1. **Priority.** The tick's priority order is seats `(0 + t) mod 4, (1 + t) mod 4, (2 + t) mod 4,
   (3 + t) mod 4` — it rotates every tick, so no seat has a structural first-mover advantage. All
   ties in steps 3–5 are broken by this order, and only by it.
2. **Decision pass.** For each living, non-halted warrior in priority order, resume its VM and run
   until it reaches an action or spends 2000 instructions. **The board is not mutated in this pass**:
   every `check`/`who` in tick `t` reads the board exactly as it stood at the end of tick `t−1`, for
   every seat. The result is one recorded *intent* per warrior (`move`/`place`/`bomb`/`wait`, plus
   the source line of the action, plus a fault flag).
3. **Bomb pass**, priority order: if the warrior is alive, `energy >= bombCost`, and there is no live
   bomb already on its cell, plant a bomb (`fuse = 5`, owner = this warrior) and subtract
   `bombCost`; otherwise the action is **refused** (`refused` incremented, incident logged).
4. **Place pass**, priority order: set the owner of the warrior's current cell to its id (overwriting
   any previous owner; `tiles` recomputed at step 10).
5. **Move pass**, priority order: target = `((x + dx) mod 30, (y + dy) mod 30)`. The move is
   **blocked** (warrior stays, `blocked` incremented) if the target holds a live bomb, a corpse, or a
   living warrior — *including one that moved there earlier in this same pass*. Otherwise the warrior
   moves. An illegal offset was already resolved in step 2 and never reaches here.
6. **Fuse pass.** Every live bomb's fuse decrements by 1.
7. **Detonation pass.** Collect every bomb at fuse 0; compute the closure of their blasts (each blast
   is the plus of 5 cells; any bomb inside the closure joins it, at any fuse, and contributes its own
   blast, until the set stops growing — the set is grown in ascending cell index `y*30 + x`, which
   makes the closure and the kill attribution deterministic). Then, in one wave: every cell in the
   closure loses its owner and its bomb; every warrior standing in the closure is **eliminated**
   (cause `bomb`, `killedBy` = the owner of the lowest-cell-index detonating bomb whose plus covers
   that warrior's cell) and leaves a corpse on its cell. A kill on oneself counts as a `selfKill`, a
   kill on another warrior as a `kill` for `killedBy`.
8. **Idle pass.** For each living warrior: if its position equals its position at the end of the
   previous tick, `idle += 1`, else `idle = 0`. `idle >= 50` ⇒ eliminated, cause `idle`, corpse left.
   (50 is the prototype's own `Idle: n/50` HUD limit.)
9. **Fault pass.** Every warrior flagged in step 2 is eliminated, cause `fault`, corpse left, with
   `faultLine` and `faultText` recorded.
10. **Bookkeeping.** For every warrior eliminated in this tick (steps 7–9), reset every tile it owns
    to unclaimed. Recount `tiles[seat]` over the board. For each living warrior,
    `energy = min(60, energy + 1 + tiles div 60)`.
11. **Round end test.** The round ends after this tick if: `t + 1 == ticks` ⇒ round reason
    `horizon`; exactly one warrior alive ⇒ `lastStanding` (the round stops immediately — there is
    nothing left to contest); zero alive ⇒ `wipeout`.

Every quantity above is an integer. No hash-table iteration order, no floating point, no wall-clock
input: the battle is a pure function of (scripts, round seed, config).

### Scoring — zero-sum, higher is better

Per round, per seat:

```
raw[s]        = tiles[s] + 100 * (1 if alive at round end else 0)
                        + 50 * kills[s] - 50 * selfKills[s]
roundScore[s] = raw[s] - (raw[0] + raw[1] + raw[2] + raw[3]) / 4      # float; Σ over seats = 0
```

Per episode:

```
score[s] = ( Σ over played rounds of roundScore[s] ) / roundsPlayed    # float; Σ over seats = 0
```

`score` is what goes in `results.scores[s]`. **The sign is "higher is better"** — a seat that
out-paints and outlives the field is positive, the field is negative, and the four scores sum to
exactly zero every episode (symmetric zero-sum, as the idea's integrity note requires). **The league
ranks by the mean of `results.scores[seat]` over episodes** (division leaderboard; Elo 1000/32 on
top). `roundsWon[s]` (rounds where `raw[s]` was the *unique* maximum) and total `tiles` are reported
for display and used only as endcard tie-breaks — series winner is the highest `score`, ties broken
by `roundsWon`, then total `tiles`, then lowest seat index.

### End conditions and `results.reason`

- `"complete"` — all `rounds` rounds were played (every round itself ends by `horizon`,
  `lastStanding` or `wipeout`; those are *round* reasons, reported per round in
  `results.roundReasons`, never in `results.reason`).
- `"deadline"` — the episode clock stopped play **between rounds**. Scores use the rounds actually
  played, divided by `roundsPlayed`.

**Those two strings are the only legal values of `results.reason`.** If the deadline fires before
any round has been played (only possible if the connect wait ate the budget), the server plays one
round with all four fallback scripts — no LLM, ~30 ms — so the replay is never empty, then settles
with `reason = "deadline"`.

### Per-seat observation — what is visible, what is hidden

Each seat's submission prompt carries, and carries **only**:

- The rules and the complete GWL reference (system prompt), its alias, its warrior id and colour.
- The round number and the total (`Round 3 of 5`), `ticks` per round, `bombCost`, `BombFuse`, the
  idle limit, the per-tick instruction budget.
- **Its own current script, verbatim, with line numbers** (round 1: the `sentry` seed script below).
- **Its own diagnostics from the previous round**: compile error text if any; fault line and message
  if it faulted; ticks survived; death cause; final and peak `tiles`; `kills`, `selfKills`,
  `illegal`, `blocked`, `refused`, `stalls`; its tile count sampled every 25 ticks (the curve).
- **The series table**: for every round played, every seat's `tiles`, `kills`, `alive`, `raw` and
  `roundScore`, **by alias**, plus the running `score`.
- **The previous round's final board**, as a 30×30 ASCII map: `.` unclaimed, `1`–`4` tile owner,
  `*` live bomb, `x` corpse — plus a line per warrior giving its alias, id, final position and
  whether it lived. (Grounded: this is what the prototype's terminal HUD shows a human.)
- Its own **private notes** (≤ 600 chars) fed back verbatim.
- The operator block: this seat's `PLAYER_PROMPT`.

**Hidden from every seat, always:** every other seat's **script source** (sealed — before, during and
after the round; there is no code path that puts another seat's source into a prompt, and
`tests/test_prompt.nim` asserts it), every other seat's notes and banner, the mapping alias → policy
name, the round seed and spawn permutation before the round runs, and the per-tick trace of anyone
else's warrior (a seat sees the *board*, and can infer behaviour from it, but never the code).

### Deviations from the prototype, and why

| Prototype (as read) | Grid Wars coworld | Why |
|---|---|---|
| One *statement* per step; a proc called inside an expression runs whole (the `godmode.gws` loophole: ten move/place pairs in one step) | One **action** per tick; pure computation is free inside a 2000-instruction budget | The loophole makes the game about interpreter trivia, not tactics; the new rule is fair, is what every honest example warrior already assumes, and gives the viewer a well-defined "currently-executing line" |
| `move(dx, dy)` with arbitrary offsets (`move(15,15)`) | `move` is one of the 8 neighbours; anything else is an illegal, wasted tick | Teleporting is not spatial combat, and it is what made the loophole profitable |
| `check` at any distance | `check`/`who` see a 9×9 window; beyond is `FOG` | Partial observability; cheap; keeps scripts local |
| Floats (`sqrt`, `sin`, …) in the VM | Integers only | The wasm viewer re-derives every battle; float drift between x86 and wasm32 would desync the replay |
| Bombs as static mines | Bombs are walls **and** detonate after a 5-tick fuse in a plus-shaped, chaining blast that scorches tiles | The idea's replay plan asks for "bombs ticking"; scorching makes bombing a *territory* weapon, not just an assassination |
| `maxSteps(5000)` | `ticks` = 400 per round, 5 rounds | Keeps the replay watchable and the payload small (§*Viewer*), and puts the drama in the *series* |
| Warrior scripts loaded from files | Warrior scripts submitted by an LLM each round | This is the game |

---

## Decisions: LLM with scripted fallback

Transport, credentials, the JSON-only output contract, `extractJsonObject`, the Bedrock model list
(haiku first), the `output_config.effort` guard, and "no credentials ⇒ every seat scripted" are
ported from bullwhip `src/bullwhip/llm.nim` unchanged in structure. What changes:

### One parallel batch per submission round

All four seats decide **simultaneously by rule**, so the server issues the four model requests as a
single `curly.makeRequests` batch per round — never sequentially (the playbook's "LLM game blows the
720 s play budget" row). `decideAll(client, sim, seats, prompts, scripted)` keeps bullwhip's
signature and its two-attempt loop:

- **Attempt 0:** one batch of the seats that are neither `PLAYER_SCRIPTED` nor already fallen back.
- Each reply is parsed, normalised, capped and **compiled**. A reply that fails to parse, or whose
  script fails to compile, or that is missing `script`, is re-opened.
- **Attempt 1:** one smaller batch containing only the re-opened seats, with the failure appended to
  the user prompt verbatim — `Your previous reply was rejected: <parser or compiler message, ≤ 300
  chars, including the line number>. Reply with ONLY the JSON object.` This is the single most
  valuable feedback in the game and it is *specific*, not a scolding.
- **Still failing ⇒ scripted fallback:** the seat plays the **`sentry`** script this round, the
  `submit` event records `origin = "fallback"` and the compile error, the feed says so, and
  `results.fallbacks[s]` counts it. The episode always advances.

**Timing arithmetic, out loud.** `PlayBudgetFraction = 0.6` of the assumed
`episodeTimeoutSeconds` = 1200 ⇒ **720 s** of play, measured from process start exactly as bullwhip
does (the game container never receives `COWORLD_TIMEOUT_SECONDS`). Per round:

```
worst case  = attempt 0 (llmTimeoutSeconds = 60)
            + attempt 1 (60)
            + inter-batch spacing (8 s)
            + battle 400 ticks x 4 warriors x <=2000 ops  (~30 ms)
            + broadcast + roundDelayMs (250 ms, cert 0)
            = 128.3 s
5 rounds    = 641.5 s   <  720 s          typical: 5 x (28 + 8) = 180 s
```

`RoundReserveSeconds = 150` is checked **before every submission batch**: if
`now + 150 > playDeadline`, the sim settles with `reason = "deadline"` and the rounds already played
are scored. In the pathological case where player connect eats its full 180 s cap, round 4 or 5 is
given up rather than the whole episode — that is the point of the check.

**Rate-limit floor.** The hosted Bedrock sidecar caps **30 requests/minute per episode**. A batch is
4 requests, and `RoundSpacingSeconds = 8` is enforced between the end of one round's last batch and
the start of the next, so even with instant replies and one retry per round the rate is
`8 requests / 8 s` = 60/min → the floor is raised to **16 s** whenever a round used two batches, and
the server logs the spacing it applied. Keep haiku; never add `us.anthropic.claude-sonnet-4-6` to the
candidate list (it times out on every sidecar call — raid, 2026-08-23).

### Reply schema and caps

```json
{"script": ["var dx = 1", "var dy = 0", "while true:", "  place()", "  move(dx, dy)"],
 "notes": "spiral works; watch for Gizmo's wall on the east side",
 "banner": "painting east, bombing anyone who leans in"}
```

| Field | Type | Cap | Truncation |
|---|---|---|---|
| `script` | array of strings (**canonical**), or one string with newlines (accepted) | ≤ **120 lines**, each ≤ **100 runes**, joined source ≤ **4000 runes** | line-wise, then **rune** boundaries (`runeSubStr`) — never a byte cut |
| `notes` | string, private, fed back to this seat next round | ≤ **600 runes** | rune boundary, `…` marker |
| `banner` | string, **spectator-only** | ≤ **80 runes**, newlines → spaces | rune boundary |

Every string that reaches the replay is cut on rune boundaries (`cleanText`, ported): a byte cut
through a multi-byte character produces replay bytes that render in a browser and fail a strict JSON
parser (playbook row; `tests/test_replay.nim` covers it).

**Normalisation before parsing** (escrow, 2026-08-23 — "normalize the structured field pre-parse"):
strip a leading/trailing markdown fence (```` ```nim ````/```` ``` ````) from the whole reply and
from inside the `script` value; accept trailing prose after the closing `}` (`extractJsonObject`
already does); if `script` arrived as a bare string, split it on `\n`; convert tabs to two spaces;
strip trailing whitespace per line; drop a leading UTF-8 BOM. `banner`/`notes` missing ⇒ empty. A
missing or empty `script` is a rejection (it goes to the retry).

The array-of-lines form is canonical **because it removes the single most common JSON failure**: a
model emitting a literal newline inside a JSON string. The system prompt demands it, shows it, and
the parser still accepts the string form.

### Prompts

`systemPrompt(sim, seat)` (fixed text, built by the server, ~1100 tokens): who you are (alias, id,
colour), the arena rules of §*The game* in eight bullets, the **full GWL reference** (statement
table, builtin table, constants, action semantics, limits, fault list), the tick resolution order in
its numbered form, the scoring formula with its sign, and:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }. "script" must be an ARRAY OF LINES (each element one source line, indentation
> preserved as leading spaces), at most 120 lines of at most 100 characters. Your program must be a
> complete warrior: if it runs off the end it stops acting and dies to the idle rule, so wrap your
> behaviour in `while true:`.

`userPrompt(sim, seat, prompt)`: the round header, the series table, the ASCII board of the previous
round, this seat's diagnostics, this seat's numbered current script, its notes, then
`operatorBlock(prompt)` (bullwhip's wording), then the one-line format reminder with the caps.

**Champion prompts** (phase 40 `tools/ci/policies.json`; both champions are `PLAYER_PROMPT`, never
scripted):

- `grid-wars-tactician` — "Territory is the score, but a dead warrior owns nothing: write a warrior
  that paints every tile it stands on, never walks into a bomb or a corpse, and turns rather than
  stalls. Keep a wall of your own bombs between you and the nearest rival, and only spend energy on
  a bomb when a rival is within two cells or when a bomb seals a gap. Change one thing per round and
  read your diagnostics: a fault line, an idle death or a high `blocked` count tells you exactly what
  to fix. Prefer a short program that always runs to a clever one that faults on line 40."
- `grid-wars-cartographer` — "Play the board, not the opponent. Each round, read the final map you
  are given: find the largest region no one held and write a warrior that walks a spiral or a
  boustrophedon sweep through it, claiming as it goes, using bombs only to fence the region off.
  Count your instruction budget — 2000 per tick — and keep loops short. If your last warrior died to
  idle, add a rule that guarantees a move every tick; if it died to a bomb, add a check before every
  move."

### Scripted baselines (`PLAYER_SCRIPTED`) — fixed warrior scripts, no LLM

A scripted seat submits the **same fixed GWL program every round** and never calls the model. All
three are the idea's "filler warriors (from the example scripts)": they are adaptations of the
prototype's `claude.gws`/`grok.gws` (spiral painter + first-strike bomber) and
`borderPatrol.gws`/`justBombs.gws` (bomb wall) to this note's DSL. They are shipped verbatim in
`data/warriors/*.gwl`, compiled into the binary with `staticRead`, and are the *only* scripts the
server can produce without a model.

`parseScriptKind` maps `"1"/"true"/"yes"/"painter"` → `skPainter`, `"bomber"` → `skBomber`,
`"sentry"` → `skSentry`, anything else → `skNone`.

**`painter`** (the strong baseline; a prompt has to beat it):

```
# painter - claim ground, turn away from walls, bomb a rival that leans in.
var dx = 1
var dy = 0
var t = 0
var run = 0
proc wall(ax, ay) =
  var c = check(ax, ay)
  return c == BOMB or c == CORPSE or who(ax, ay) != 0
proc rival() =
  if who(1, 0) != 0 and who(1, 0) != ID:
    return 1
  if who(-1, 0) != 0 and who(-1, 0) != ID:
    return 1
  if who(0, 1) != 0 and who(0, 1) != ID:
    return 1
  if who(0, -1) != 0 and who(0, -1) != ID:
    return 1
  return 0
while true:
  if rival() == 1 and energy() >= BOMBCOST:
    bomb()
  else:
    place()
  if wall(dx, dy):
    t = dx
    dx = 0 - dy
    dy = t
    run = 0
  else:
    move(dx, dy)
    run = run + 1
    if run == 6:
      run = 0
      t = dx
      dx = 0 - dy
      dy = t
```

**`bomber`** (the aggressive filler): mines the ground it leaves and fences itself in.

```
# bomber - mine the ground you leave, fence yourself in, paint inside the fence.
var dx = 1
var dy = 0
var t = 0
var step = 0
while true:
  step = step + 1
  if energy() >= BOMBCOST and mod(step, 3) == 0:
    bomb()
  else:
    place()
  if check(dx, dy) == BOMB or check(dx, dy) == CORPSE or who(dx, dy) != 0:
    t = dx
    dx = 0 - dy
    dy = t
  else:
    move(dx, dy)
```

**`sentry`** (the always-legal **fallback**, and the round-1 seed script every LLM seat is shown):
never bombs, never faults, always moves.

```
# sentry - the fallback warrior: walk a box and paint it.
var dx = 1
var dy = 0
var t = 0
var run = 0
while true:
  place()
  if check(dx, dy) == BOMB or check(dx, dy) == CORPSE or who(dx, dy) != 0:
    t = dx
    dx = 0 - dy
    dy = t
    run = 0
  else:
    move(dx, dy)
    run = run + 1
    if run == 8:
      run = 0
      t = dx
      dx = 0 - dy
      dy = t
```

`tests/test_bot.nim` asserts all three compile, run 400 ticks without a fault, a stall, an illegal
action or a refused-with-energy bomb, and that `painter` beats `sentry` on mean `score` over ten
seeds — a baseline that cannot beat the fallback is not a partner worth beating.

### Degrade, never hang

| Failure | Behaviour |
|---|---|
| Model reply times out (`llmTimeoutSeconds` 60), 4xx/5xx, refusal, or `max_tokens` before any `{` | seat re-opened → attempt 1 → `sentry` fallback |
| Reply parses but the script does not compile | same, with the compiler's `line N: message` in the retry prompt |
| No LLM credentials at all (`client.disabled`) | every seat plays its `PLAYER_SCRIPTED` baseline, or `sentry`; the whole episode runs in ~1 s (this is the offline-certification path and is load-bearing) |
| Auth 401/403 | `client.disabled = true`; all remaining rounds scripted |
| Bedrock throttle 429 / "Model access is denied" | rotate to the next candidate model, retry next round |
| A warrior faults, stalls, idles out or is bombed | *not* a failure — it is the game; recorded, shown, scored |
| `now + 150 s > playDeadline` before a batch | `sim.endEarly()`, `reason = "deadline"`, artifacts written immediately |
| Round battle runs long | impossible: it is bounded by `ticks × 4 × 2000` integer ops with no IO |

---

## Sim module

Files (fork of the bullwhip tree, same layout):

- `src/gridwars/types.nim` — `GridWarsError`, `PlayerConfig`, `GameConfig`, `EventKind`,
  `GameEvent`, `SeatStat`, `defaultGameConfig()`, `update(config, json)`.
- `src/gridwars/gwl.nim` — the **warrior language**: lexer, parser, compiler to a flat op array, and
  the resumable VM. Pure, no IO. The only file that knows about syntax.
- `src/gridwars/sim.nim` — the arena rules and the episode state machine. Pure, no IO. Imports
  `gwl`. Server, tests and the wasm viewer all drive this module and nothing else.
- `src/gridwars/llm.nim` — prompts, batching, parsing, the three baselines (as `staticRead` sources).
- `src/gridwars/server.nim`, `src/gridwars.nim`, `src/gridwars_player.nim` — §*Server*.

### `gwl.nim`

```nim
type
  GwlOpKind* = enum opPush, opLoad, opStore, opIndex, opBin, opUn, opCall,
                    opJump, opJumpFalse, opEnter, opLeave, opReturn,
                    opAction, opHalt
  GwlOp* = object
    kind*: GwlOpKind
    a*, b*: int            ## operand slots (constant index, name id, arg count, target pc)
    line*: int             ## 1-based source line, for the highlight and for faults
  GwlProgram* = object
    ops*: seq[GwlOp]
    names*: seq[string]
    consts*: seq[int]
    source*: seq[string]   ## the submitted lines, verbatim, for the viewer's code pane
  GwlFault* = object
    line*: int
    message*: string
  GwlVm* = object          ## one warrior's resumable machine
    program*: GwlProgram
    pc*: int
    stack*: seq[int]
    frames*: seq[Frame]
    globals*: seq[int]
    arrays*: seq[seq[int]]
    halted*: bool
    fault*: GwlFault       ## line 0 = none
  GwlAction* = object
    kind*: ActionKind      ## akNone, akMove, akPlace, akBomb, akWait
    dx*, dy*: int
    line*: int
```

API: `compile(lines: seq[string]): GwlProgram` (raises `GwlCompileError` with a line number),
`newVm(program, seat, seed): GwlVm`, `step(vm: var GwlVm, view: BoardView, budget: int): GwlAction`
(runs until an action, a fault, a halt or the budget; `akNone` + `vm.fault.line > 0` = fault,
`akWait` = stall). `BoardView` is a read-only snapshot passed by the sim — the VM never touches the
board directly, which is what makes step 2 of the resolution order true by construction.

### `sim.nim`

```nim
const
  Seats* = 4
  Grid* = 30
  Cells* = 900               ## Grid * Grid
  SpawnCells* = [(4, 4), (25, 4), (4, 25), (25, 25)]
  BombFuse* = 5
  IdleLimit* = 50
  EnergyStart* = 12
  EnergyCap* = 60
  StepInstructions* = 2000
  MaxScriptLines* = 120
  MaxLineChars* = 100
  MaxScriptChars* = 4000
  MaxNotesLen* = 600
  MaxBannerLen* = 80
  SurviveBonus* = 100
  KillBonus* = 50
  MinRounds* = 1
  MaxRounds* = 12
  MinTicks* = 20
  MaxTicks* = 1200
  KeyframeEvery* = 25        ## viewer grid keyframe cadence
  PacingBudgetMs* = 20_000
  CogNames* = [ ... ]        ## bullwhip's list, verbatim

type
  Phase* = enum phSubmit = "submit", phBattle = "battle", phDone = "done"
  Warrior* = object
    alive*: bool
    x*, y*, energy*, idle*, tiles*, kills*, selfKills*: int
    illegal*, blocked*, refused*, stalls*, peakTiles*, ticksLived*: int
    deathTick*: int          ## -1 while alive
    deathCause*: string      ## "" | "bomb" | "idle" | "fault"
    faultLine*: int
    faultText*: string
    line*: int               ## the source line it executed this tick (viewer)
    vm*: GwlVm
  Bomb* = object
    x*, y*, fuse*, seat*: int
  Board* = object
    owner*: array[Cells, int8]     ## 0 = unclaimed, 1..4
    corpse*: array[Cells, bool]
    bombs*: seq[Bomb]              ## kept sorted by y*30+x
  RoundRecord* = object
    seed*: int
    spawn*: array[Seats, int]      ## seat -> spawn cell index
    scripts*: array[Seats, seq[string]]
    origin*: array[Seats, string]  ## "llm" | "retry" | "fallback" | "scripted"
    compileError*: array[Seats, string]
    banner*, notes*: array[Seats, string]
    stat*: array[Seats, SeatStat]  ## tiles/kills/alive/raw/roundScore/...
    ticksPlayed*: int
    reason*: string                ## "horizon" | "lastStanding" | "wipeout"
    digest*: string                ## FNV-1a 64 of the final board + warriors, hex
  Sim* = object
    config*: GameConfig
    names*: seq[string]
    round*: int
    roundsPlayed*: int
    phase*: Phase
    pending*: array[Seats, bool]   ## submission still due this round
    scripts*: array[Seats, seq[string]]   ## the live round's sources
    notes*: array[Seats, string]
    history*: seq[RoundRecord]
    board*: Board
    warriors*: array[Seats, Warrior]
    tick*, ticks*: int
    done*: bool
    reason*: string                ## "complete" | "deadline"
    events*: seq[GameEvent]
```

API — the surface the server, the tests and the wasm module use:

`initSim(config)`, `sampleEpisode(config)` (fits `rounds`/`ticks`/`roundDelayMs` into the budget,
idempotent via `config.sampled`), `tableNames(players, seed)`, `pendingSeats(sim)`,
`submit(sim, seat, lines, notes, banner, origin)` (compiles, caps, logs the `submit` event; the
fourth submission **seals the round and runs the whole battle**, logging the `battle` event and
either opening the next round or settling), `endEarly(sim)`, `roundSeed(sim, round)`,
`resultsJson(sim)`, `frameStates(sim)` / `framesJson`, `replayMatch(config, events)`,
`eventToJson` / `eventFromJson`, `boardAscii(sim, round)` (the observation map),
`seatObservation(sim, seat)`.

### Event vocabulary (what the replay carries)

Flat `GameEvent`, JSON via `eventToJson`/`eventFromJson`, exactly five kinds:

| kind | fields |
|---|---|
| `start` | `text` = `"grid-wars"`; opens the log |
| `round` | `round`, `seed` (the round's derived seed — **the server-side RNG, logged**), `spawn` (4 cell indexes by seat), `ticks` |
| `submit` | `round`, `seat`, `script` (array of source lines, capped), `lines`, `origin` (`llm`/`retry`/`fallback`/`scripted`), `compileError` (`""` when clean), `banner`, `text` = the seat's notes after this reply, `scripted` (bool) |
| `battle` | `round`, `ticksPlayed`, `reason` (`horizon`/`lastStanding`/`wipeout`), `stats` = 4 × `{tiles, peakTiles, kills, selfKills, alive, deathTick, deathCause, faultLine, faultText, illegal, blocked, refused, stalls, ticksLived, raw, roundScore}` by seat, `curve` = 4 × tile counts sampled every 25 ticks, `digest` |
| `end` | `round` = rounds played, `text` = `"complete"` or `"deadline"` |

**The per-tick history is not stored as events — it is re-derived**, exactly as bullwhip re-derives
its weeks: `replayMatch(config, events)` re-runs the compiled scripts from the logged round seed and
spawn permutation through the same `sim.nim`, producing every tick's board, and asserts the
recomputed `digest` equals the recorded one. A mismatch raises, which the wasm module reports as
`data-replay-error` rather than silently drawing a different game. Determinism is guaranteed by
construction (integer-only VM, no hashing order, priority rotation from the tick index, `rand`
from the logged seed), and `tests/test_replay.nim` asserts digest equality over 20 seeds.

The replay bytes are therefore **self-sufficient**: aliases, policy names, full config, the seed and
every derived round seed, the spawn permutation, every script, and the results — everything the
viewer needs, with no server contacted except S3 for the `.replay` file.

### The frame the viewer reads

`framesJson(sim)` produces one frame per timeline position. A frame is:

```json
{"seats":[{"name":"Sprocket","seat":0,"color":0,"id":1,"score":38.5,"raw":214,
           "tiles":137,"peakTiles":151,"energy":23,"alive":true,"x":14,"y":7,
           "idle":3,"kills":1,"selfKills":0,"line":12,"action":"place",
           "banner":"painting east","deathCause":"","faultLine":0,"faultText":"",
           "origin":"llm","scriptLines":42,"pending":false}, x4 by seat],
 "grid":"...1111..2222....",          // 900 chars, row-major: '.' unclaimed, '1'..'4' owner
 "gridDelta":[[437,"2"],[438,"."]],   // present instead of "grid" on non-keyframe frames
 "bombs":[{"x":4,"y":9,"fuse":3,"seat":0}],
 "corpses":[[11,4]],
 "blast":[[4,9],[3,9],[5,9],[4,8],[4,10]],   // cells detonating on THIS frame (the flash)
 "round":2,"rounds":5,"tick":143,"ticks":400,"roundsPlayed":1,
 "phase":"submit|battle|roundEnd|done",
 "focus":0,                                   // seat whose script the code pane shows
 "scripts":[["var dx = 1","..."], x4],        // this round's source per seat, as lines
 "series":[[{"raw":214,"tiles":137,"kills":1,"alive":true,"roundScore":61.5}, x4], xroundsPlayed],
 "log":["Sprocket's bomb kills Ratchet at (14,7)"],
 "gameDone":false,"reason":""}
```

`grid` is written **in full on keyframes only** — every 25th tick, every `submit` frame, every
`roundEnd` frame, and frame 0 — and as `gridDelta` (changed cells) otherwise. The renderer keeps a
running grid and, on a seek, walks back to the nearest keyframe (≤ 25 frames) and replays the
deltas. At 5 × (4 submit + 400 tick + 1 roundEnd) = **2025 frames** the payload is ~200 KB rather
than ~2 MB. (`phase` here is the *frame's* phase, one of `submit`/`battle`/`roundEnd`/`done`; the
sim's own `Phase` enum has three values because `roundEnd` is a single derived frame, not a state
the sim waits in.)

`resultsJson` (platform-facing, **policy** names):

```json
{"names":[4],"scores":[4 floats, sum = 0],"tiles":[4],"roundsWon":[4],"kills":[4],
 "deaths":[4],"faults":[4],"fallbacks":[4],"rounds":<played>,"maxRounds":<cap>,
 "ticks":<per round>,"roundReasons":["horizon","lastStanding"],
 "winner":"<policy name>","reason":"complete|deadline"}
```

Replay payload (`gridwars.replay.v1`), written by the server:

```json
{"protocol":"gridwars.replay.v1","names":[aliases],"policyNames":[policy names],
 "config":{"rounds":5,"ticks":400,"bombCost":12,"seed":123456,"sampled":true},
 "events":[...],"results":{...}}
```

Replay mode and the wasm viewer add `"frames"`.

---

## Server, player, protocol

`src/gridwars/server.nim` is bullwhip's `server.nim` with the game loop replaced. Routes, exactly
(bullwhip's set, renamed; every one of them registered **before** any catch-all asset route, because
hosted certification probes `/healthz`, `GET /client/player?slot=0&token=<t>`, a bad-token player
websocket and `GET /client/global` *before* player pods start — lantern 0.1.1):

```
GET /healthz                     GET /client/global    GET /client/player
GET /client/replay               GET /client/renderer.js
GET /client/chrome.css           GET /client/assets/@name
WS  /player?slot=N&token=T       WS  /global           WS  /replay   (replay mode)
```

Neither `/client/` page opens the player socket. After artifacts are written the server keeps
`/healthz` and `/global` answering for `shutdownGraceSeconds` = 20 and then `quit(0)` (lantern 0.1.3
→ 0.1.4: the certifier pings `/global` with a 2 s deadline *after* the pods start, and a fast
scripted episode had already exited).

**Loop** (one iteration per round, mirroring bullwhip's per-week loop):

1. Wait up to `player_connect_timeout_seconds` (180) for all four player sockets; start regardless.
2. Check the deadline (`now + RoundReserveSeconds > playDeadline` ⇒ `endEarly`, break).
3. Snapshot the sim under the lock; release the lock; run `decideAll` (one parallel batch) **outside
   the lock** — only this thread mutates the sim, so the snapshot cannot go stale.
4. Under the lock, `submit(...)` each seat in seat order. The fourth `submit` seals the round and
   runs the battle synchronously. Broadcast.
5. Sleep `roundDelayMs` (bounded by `PacingBudgetMs`), and the rate-limit floor of §*Decisions*.
6. On `sim.done`: send the `final` frame to the player sockets **before** writing artifacts (the
   hosted worker tears player pods down as soon as `results.json` exists), then write results and
   the replay with `writeArtifact`, then the shutdown grace, then `quit(0)`.

**Live spectator broadcast** (`/global`): the full snapshot after every `submit`, at the start and
end of every battle, on **every elimination**, and every 25 ticks — not every tick, which would
flood the socket with 1600 frames for no gain.

**Player protocol `gridwars.player.v1`** — bullwhip's frame shapes, renamed:

- game → player: `{"type":"welcome","protocol":"gridwars.player.v1","slot":N,"name":alias,"id":1..4,
  "rounds":R,"ticks":T}`; `{"type":"state", ...}` after every event, **redacted to this seat**: its
  own warrior's stats, its own script, its own notes, the round/tick counters, the public board
  summary (`tiles` per seat), `started`, `done`, `reason` — never another seat's source;
  `{"type":"final","done":true,"scores":[...],"tiles":[...],"roundsWon":[...],"names":[aliases],
  "rounds":R,"reason":str}` at the end, after which the player exits.
- player → game: `{"type":"prompt","prompt":"<≤ 4000 runes>","scripted":"painter|bomber|sentry|"}`,
  sent on connect and again after `welcome`.

`src/gridwars_player.nim` is bullwhip's player with a Grid Wars default prompt and **one fix that is
latent in the starter** (raid 0.1.3 → 0.1.4): the receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket, because whisky's `receiveMessage` *raises*
on a close frame and mummy's `send` only queues, so the game's `quit(0)` can outrun the flushed
`done` frame and kill the player container with status 1.

---

## Viewer

### The four viewer files — one starter, no splicing

**All four viewer files come from one starter, `Metta-AI/cogame-bullwhip`, and only from it:**

- `replay-viewer/config.nims` — bullwhip's, with the output name and `EXPORT_NAME` renamed;
- the wasm entry `replay-viewer/gridwars_replay.nim` — fork of `replay-viewer/bullwhip_replay.nim`;
- `replay-viewer/static_replay.js` — bullwhip's shell;
- `replay-viewer/index.html` — bullwhip's page.

Nothing is spliced in from another starter — not from babel, not from parley, not from ctf, not from
factorio. Bullwhip's emscripten link flags stay exactly as they are (`-O2`,
`ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`, `MODULARIZE=1`, plus
`EXPORTED_RUNTIME_METHODS=HEAPU8` and `emscripten_exit_with_live_runtime()`), with exactly these
renames: `EXPORT_NAME=GridWarsReplayModule`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_gw_load_replay,_gw_payload_ptr,_gw_payload_len,_gw_error_ptr,_gw_error_len`,
output `dist/gridwars_replay.js`. `static_replay.js` keeps calling the module through that same
`GridWarsReplayModule()` factory and those same `_gw_*` exports. (cogame-lantern, 2026-08-23: a
shell from one starter on another starter's link flags deadlocks silently with every asset
returning 200 — that is why the four files must share one lineage.)

**Load signalling.** `renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame** —
bullwhip already does this at the end of `attachReplay`'s `makeRenderer` callback
(`client/renderer.js:1390`), kept verbatim. On any failure (missing `?replay=`, the 20 s fetch
timeout, a non-200, a wasm rejection including a digest mismatch) `static_replay.js` sets
`document.documentElement.setAttribute("data-replay-error", <message>)`, shows the Retry button and
posts the `coworld-replay` `error` envelope; a successful retry removes the attribute.
`tools/ci/viewer_smoke.mjs` reads exactly these two signals.

**One deliberate change to the starter's shell** (chorus `3c11c953`, 2026-08-24): bullwhip's
`start()` posts `tell("ready")` two animation frames after `attachReplay`, which can beat the first
drawn frame, so the softmax.com embed samples an unpainted shell. The fork instead polls
`document.documentElement.getAttribute("data-replay-loaded") === "true"` on `requestAnimationFrame`
(bounded at 240 frames, then `tell("error", "renderer never drew a frame")`) and posts `ready` only
after it is set. `ready` therefore always means a picture.

**Bundle.** The manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}`;
`tools/build_replay_viewer.sh` (bullwhip's hook, paths renamed, committed `chmod +x`) is the
`coworld build` hook and **`mkdir -p`s the output parent before the containment check** (ecos,
2026-08-23 — every fork of that hook exits 1 on a fresh CI checkout otherwise). It compiles
`replay-viewer/gridwars_replay.nim` to wasm (with local `emcc` if present, else in the pinned
`emscripten/emsdk:4.0.15` container from `Dockerfile.replay-viewer`) and copies
`gridwars_replay.js`, `gridwars_replay.wasm`, `index.html`, `static_replay.js`,
`client/renderer.js`, `client/chrome.css` and the `data/` assets into the bundle. **Never a
`/client/replay` pod viewer.**

### Chrome provenance — copied byte-for-byte, extended by appending

The pins name `client/chrome_common.js` and `client/replay_broadcast.html`. **The bullwhip lineage
has neither** (eleusis, 2026-08-23; confirmed in this mount: `client/` holds `chrome.css`,
`renderer.js`, `replay.html`, `global.html`, `player.html`). Those two roles are held by
**`client/chrome.css`** (the shared chrome, the `chrome_common.js` analogue) and
**`client/replay.html`** (the broadcast page, the `replay_broadcast.html` analogue; the static
bundle's `replay-viewer/index.html` is the same page with `./` asset paths). Nothing is imported
from a starter that does have those filenames. The rule is applied to bullwhip's two files:

- **`client/chrome.css` is copied byte-for-byte** and a single `/* ---------- Grid Wars ---------- */`
  block is **appended at the end**. No existing rule is edited or deleted — this is the file's own
  convention, it already accretes one appended block per game. The appended block contains exactly:
  - `:root { --band: 84px; --hudscale: 1; }` — set for real by `relayout()` (below);
  - `#terrbar` (the territory bar) and `.terrseg` segments, `font-size: calc(11px * var(--hudscale))`;
  - `#codepane`, `.codeline`, `.codeline.now` (the executing line: amber background, ink text),
    `.codeline .ln` (gutter), `#codehead` (alias + `origin` chip + fault chip);
  - `.plate-tiles`, `.plate-energy`, `.plate-dead`, `.plate-fault` scorebug chips;
  - `#loading { bottom: var(--band); }` so the caption never sits over the transport;
  - beat-marker CSS for **every kind the scrubber emits** — `.beat-marker.submit` (paper, 10 px),
    `.beat-marker.kill` (red, 14 px), `.beat-marker.fault` (violet, 14 px),
    `.beat-marker.idle` (ghost, 10 px), `.beat-marker.roundend` (amber, 12 px),
    `.beat-marker.end` (amber, 3 px × 14 px) — plus `button.beat-marker { padding:0; border:0;
    background: var(--tc, var(--paper-dim)); cursor: pointer; }`;
  - feed colours `.feed-submit`, `.feed-kill`, `.feed-fault`, `.feed-idle`, `.feed-round`,
    `.feed-end`;
  - the small-screen queries: `@media (max-width: 720px) { #codepane { display: none; } }`,
    `@media (max-width: 560px) { .plate-label, .plate-energy { display: none; } }`,
    `@media (max-width: 420px) { #scorebug { grid-template-columns: repeat(2, 1fr); } }`.
- **`client/replay.html` is bullwhip's page with a game block appended** — never a rewrite that
  reuses the ids (cogame-gridlock, 2026-08-23). **Every element the starter ships is kept, with its
  id:** `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`,
  `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`,
  `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, and the
  `fit()` + `bindFeedToggle` bootstrap. **Elements removed: none.** The only edits are (a) the
  wordmark text `BULL<span>WHIP</span>` → `GRID<span>WARS</span>` and the `<title>`, and (b) **two
  appended elements**: `<div id="terrbar"></div>` inserted between `#scorebug` and `#board-wrap`,
  and `<div id="codepane"></div>` appended inside `#layout` **after** `#stage` and **before**
  `#feed`. `replay-viewer/index.html` gets the identical treatment (same page, `./` asset paths,
  plus the `gridwars_replay.js` and `static_replay.js` script tags).
- **Zoom: dropped entirely.** Bullwhip ships no `#viewpanel` (no zoom bar, no minimap) and none is
  added. The arena is **fixed** — 30×30, always rescaled to the canvas by `computeLayout`, whole
  board in frame at every size — so zoom controls would be dead weight (operator review,
  2026-08-23).

### Transport rules

- `--band` and `--hudscale` are set **on `:root`** (`document.documentElement`) by a `relayout()`
  function in the page bootstrap of both `client/replay.html` and `replay-viewer/index.html`, called
  on `load`, on `resize`, and from the feed-toggle handler: it measures `#transport`'s
  `offsetHeight` into `--band` and sets `--hudscale = clamp(0.8, width / 960, 1.15)`. `fit()` (the
  canvas resizer) is called from the same function, so the canvas and the custom properties can
  never disagree.
- **Nothing is overlaid in the transport band.** `#transport` is the last child of `#stage` in
  normal flex flow at `z-index: 10`; the only absolutely-positioned overlays (`#lightpool`,
  `#grain`, `#endscreen`) live inside `#board-wrap`, which ends where the band begins, and
  `#loading` is pinned above it with `bottom: var(--band)`.
- **The endcard stops at `var(--band)`** — `#endscreen` is `position: absolute; inset: 0` inside
  `#board-wrap`, so its bottom edge is exactly `var(--band)` above the page bottom — **and is
  dismissed by every seek**: `attachReplay`'s `setIndex` calls `updateEndscreen(..., index >=
  events.length && events.length > 0, ...)` on *every* index change and `updateEndscreen` toggles
  `.show`, so any scrub below the last frame hides it. Bullwhip's code, kept verbatim.
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` is kept verbatim except that each
  beat is created as `<button type="button" class="beat-marker …">` with an `aria-label`/`title` and
  an `onclick` that seeks to that frame; the container keeps its drag-to-seek pointer handlers.
  Beats are emitted for: every **submission** (`"R2 · Sprocket submits 62 lines"`), every **kill**
  (`"R2 t143 · Sprocket's bomb kills Ratchet"`), every **fault** (`"R2 t51 · Gizmo faults at line
  12"`), every **idle death** (`"R2 t210 · Widget idles out"`), every **round end**
  (`"R2 · Sprocket 214 tiles"`) and the **end** (`"Final"`). The appended CSS block defines a rule
  for each of those six kinds; round spans and the every-4th separator the starter already draws are
  kept, with one span per round.
- **Naming guard** (tandem, 2026-08-23): the appended game-block builders are named
  `markGridWarsBeat` and `buildGridWarsCode`, never `markBeat`/`buildScrub`, so nothing can be
  shadowed by a chrome alias assignment; `tests/test_viewer.nim` asserts no top-level name in the
  appended block collides with a name the chrome defines above it.

### The stage — real art, drawn over the starter's assets

`client/renderer.js` is bullwhip's renderer (topband, scorebug, feed, scrubber, endscreen, name map,
effects, both drivers, replay pacing) with the *conveyor* stage replaced by the **arena**:

- **The board.** A 30×30 grid drawn over `data/arena_floor.png`, each cell tinted by its owner in
  that seat's colour (the renderer's existing `COLOR_HEX`), unclaimed cells left as bare floor with
  a faint ink grid. Freshly claimed cells flash for 200 ms. Scorched cells (a blast) flash white and
  fade back to bare floor.
- **Warriors** are bullwhip's four `soldier_<red|blue|green|yellow>_front.png` sprites, one per
  seat, standing on their cell, with a small alias plate (policy name spectator-side) and, when the
  seat has one, the `banner` on a paper tag. A dead warrior is replaced by a dark ink cross (the
  corpse) and its plate goes ghost + strikethrough (`.plate.dead`, already in the chrome).
- **Bombs** are ink discs in the planter's colour with the **fuse number drawn on them**, pulsing
  faster as the fuse drops; a detonation draws the 5-cell plus in white for 250 ms.
- **Territory bar** (`#terrbar`), across the top under the scorebug: one stacked segment per seat,
  width proportional to `tiles`, plus a grey remainder for unclaimed — the whole game in one line.
- **Code pane** (`#codepane`), the idea's "see the program think": the focused seat's script for the
  current round, one `<div class="codeline">` per line with a line-number gutter, the line the
  warrior is executing **this frame** carrying `.now` (from `seats[focus].line`), auto-scrolled to
  keep `.now` in view. `#codehead` shows the alias, the `origin` chip (`LLM` / `RETRY` / `FALLBACK`
  / `SCRIPTED`) and, after a fault, a red chip with `line N: message`. Focus defaults to the seat
  with the most tiles and follows a click on any scorebug plate.
- **Clock** (`#clock`): `R2 / 5 · TICK 143 / 400`, and `SUBMITTING` during a submission phase,
  `FINAL` at the end.
- **Scorebug** (`#scorebug`, 4 plates): alias/policy name, signed series `score` (`+38.5`), `tiles`
  now, `energy`, kill count, and a `DEAD`/`FAULT` chip.
- **Feed**: one section head per round; `Sprocket submits a 62-line warrior`; `Gizmo's warrior
  faulted at line 12: undefined variable 'dirx'`; `Sprocket's bomb kills Ratchet at (14,7)`;
  `Widget idles out at tick 210`; `Round 2 — Sprocket 214 tiles, +61.5`; `Final — Sprocket takes the
  series`. Legible English, never internal notation.
- **Endcard**: columns `score`, `rounds won`, `tiles`, `kills`; verdict `OUTPAINTED THE FIELD`, or
  `LAST WARRIOR STANDING` when the final round ended `lastStanding`.

**Playback cadence** (bullwhip's `stepMs` switch, retuned): a **tick** frame dwells 40 ms, a
**submit** frame 1200 ms (long enough to read the new program in the code pane), a **roundEnd**
frame 1500 ms, the **end** frame 1500 ms. A `standard` episode is
`2000 × 0.04 + 20 × 1.2 + 5 × 1.5 ≈ 112 s` of replay; the certification fixture is ≈ 25 s.

**Legible at 360 px wide** (the softmax.com featured-match iframe): the board keeps its aspect and
fills the frame; `.plate-name` keeps bullwhip's `flex: 1 1 auto; min-width: 3.2em`; `.plate-label`
and `.plate-energy` hide under 560 px; the scorebug goes 2×2 under 420 px; `#codepane` and `#feed`
collapse behind the existing `LOG »` toggle under 720 px, leaving board + scorebug + territory bar +
transport — all four readable at 360 px. Numbers are rendered as numbers (`214 tiles`, `+61.5`,
`fuse 3`), never as codes.

---

## Packaging

- **`compose.yaml`** — one service, **`gridwars`** (no hyphen: `coworld build` derives the manifest
  image placeholder from the compose service name, `services.gridwars` → `{{GRIDWARS_IMAGE}}`;
  `{{GAME_IMAGE}}` is not a thing — lantern 0.1.0), `image: coworld-grid-wars:latest`,
  `platform: linux/amd64`, `build: {context: ., network: host}`.
- **`Dockerfile`** — bullwhip's two-stage nimby build, one image, two entrypoints: `/bin/gridwars`
  (game, `CMD`) and `/bin/gridwars-player`. Copies `data/` (sprites, font, `warriors/*.gwl`) and
  `client/`. **`Dockerfile.replay-viewer`** — bullwhip's, `emscripten/emsdk:4.0.15`, path renamed.
- **`gridwars.nimble`** — bullwhip's requires (`nim >= 2.2.4`, `bitworld`, `mummy`, `curly`,
  `whisky`), `srcDir = "src"`; `nimby.lock` carried over.
- **`coworld_manifest_template.json`** — `$schema` set, **8 tags** (`programming-game`, `core-wars`,
  `grid`, `territory`, `zero-sum`, `llm-driven`, `four-player`, `code-generation`),
  `episode_timeout_minutes: 20`, `game.name` **`grid-wars`** (this is the softmax.com slug),
  `game.runnable.type: "game"`, `image: "{{GRIDWARS_IMAGE}}"`, `run: ["/bin/gridwars"]`,
  `env: {"ANTHROPIC_API_KEY_URI": "secret://coworld/grid-wars/anthropic_api_key"}` (without it the
  hosted container never gets the secret and every league episode silently plays scripted — hive,
  2026-08-23), `source_url: https://github.com/Metta-AI/cogame-grid-wars/tree/main`,
  `"replay_viewer": {"bundle": "static-replay-viewer"}`.
- **`game.config_schema`** — a real JSON Schema, `additionalProperties: false`, `required:
  ["tokens","players"]`. **Every array property carries `minItems`/`maxItems`** (tandem 0.1.0):
  `tokens` and `players` both `minItems: 4, maxItems: 4`. Properties: `num_agents`
  (integer, min 4, max 4), `seed` (integer), `rounds` (1..12, default 5), `ticks` (20..1200,
  default 400), `bombCost` (0..60, default 12), `episodeTimeoutSeconds` (60..6000, default 1200),
  `roundDelayMs` (0..10000, default 250), `model` (default `claude-sonnet-5`), `maxOutputTokens`
  (256..4000, default **2400** — a warrior program is long; 900 truncates it),
  `llmTimeoutSeconds` (5..300, default 60), `player_connect_timeout_seconds` (number, default 180).
- **`game.results_schema`** — mirrors `resultsJson`; every array `minItems: 4, maxItems: 4`;
  `scores` items are plain numbers (they are signed and sum to zero, so **no `maximum: 0`**);
  `reason` a string documented as `complete|deadline`.
- **`game.protocols`** — **both** `player` and `global`, each
  `{"type": "text", "value": "…"}` objects, never bare strings (cogame-garble 0.1.0, 2026-08-24):
  `player` documents `gridwars.player.v1` frame by frame, including that a policy is a prompt and
  that `PLAYER_SCRIPTED` names a built-in warrior; `global` documents the `/global` snapshot, the
  frame shape of §*Sim module*, the event kinds, and where the static replay bundle renders.
- **`game.docs`** — `readme` (`{"type":"text","value":…}`) plus `pages`: `rules.md` (the arena,
  the tick resolution order, scoring) and **`warrior-language.md`** (the complete GWL reference plus
  the three shipped warriors) — the page a champion author actually needs.
- **`player[]`** (top level, three entries, all on `{{GRIDWARS_IMAGE}}` running
  `/bin/gridwars-player`, each with `id`/`type`/`name`/`description`/`source_url` and bullwhip's
  resource block):
  - `grid-wars-player` — the prompt player (`PLAYER_PROMPT`, no `PLAYER_SCRIPTED`);
  - `grid-wars-painter` — `env: {"PLAYER_SCRIPTED": "painter"}`;
  - `grid-wars-bomber` — `env: {"PLAYER_SCRIPTED": "bomber"}`.
- **`variants[]`** — each with a `description` (required by the 0.1.42 upload contract) and
  **`num_agents: 4`**:
  - `standard` — "Four cogs, five rounds of 400 ticks on a 30×30 grid." `players` ×4,
    **`num_agents: 4`**, `rounds: 5`, `ticks: 400`, `bombCost: 12`, `roundDelayMs: 250`,
    `player_connect_timeout_seconds: 180`.
  - `blitz` — "Three fast rounds of 250 ticks; less time to iterate, more to lose." `players` ×4,
    **`num_agents: 4`**, `rounds: 3`, `ticks: 250`, `bombCost: 12`, `roundDelayMs: 150`,
    `player_connect_timeout_seconds: 180`.
- **`certification`** — `game_config`: `players` = `[Sprocket, Gizmo, Ratchet, Widget]`,
  **`num_agents: 4`**, `seed: 7`, `rounds: 2`, `ticks: 150`, `roundDelayMs: 0`,
  `player_connect_timeout_seconds: 180`; `players`:
  `[{grid-wars-player}, {grid-wars-painter}, {grid-wars-player}, {grid-wars-bomber}]` — **every
  declared player runnable occupies a slot** (raid 0.1.2 → 0.1.3: `players_missing` otherwise), with
  the prompt player on the two seats that decide the fixture. 2 × (4 submit + 150 tick + 1 roundEnd)
  = **310 frames ≈ 25 s of playback** at the cadence of §*Viewer*, which comfortably outlasts the
  10 s `--soak` window (ecos, 2026-08-23: a smoke replay shorter than the soak reads as frozen).
- **`tools/ci/docker_smoke.sh`** — the coworld-builder template with `<slug>` = `grid-wars`,
  `<IMAGE>` = `coworld-grid-wars`, **`<SEATS>` = 4**; committed `chmod +x`.
  `tools/ci/viewer_smoke.mjs` copied **verbatim**, no substitutions.
  `.github/workflows/ci.yml` and `coworld-release.yml` from `templates/`.
- **`tools/ci/policies.json`** — the four phase-40 policies: champions `grid-wars-tactician`
  (daveey) and `grid-wars-cartographer` (`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`),
  both `PLAYER_PROMPT`; fillers `grid-wars-painter` and `grid-wars-bomber`, both `PLAYER_SCRIPTED`.
  A scripted policy seated as a champion is a failure state.

### Design pins (playbook §Phase 0) — how each is satisfied

| Pin | Where |
|---|---|
| Starter chosen by game shape | `cogame-bullwhip` — simultaneous, turn-based, hidden-information, LLM-prompt policies, one parallel batch per turn, pure `sim` shared with the wasm viewer (title paragraph). |
| Public `Metta-AI/cogame-grid-wars` | Repo created **public** in phase 20 (a certification prerequisite); `source_url` points at it. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `grid-wars-player` (`PLAYER_PROMPT`) vs `grid-wars-painter` / `grid-wars-bomber` (`PLAYER_SCRIPTED=…`), one image, two entrypoints (§Decisions, §Packaging). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; the wasm module re-derives every tick in the browser; nothing but S3 is contacted (§Viewer). |
| Real art; starter chrome reused verbatim | `chrome.css` byte-for-byte + one appended block; `replay.html`/`index.html` = the starter's page + **two** appended elements, **nothing removed**; sprites, floor and font from `data/` (§Viewer). |
| Legible to a casual spectator | `214 tiles`, `+61.5`, `fuse 3`, `TICK 143 / 400`, plain-English feed lines, the code pane; 360 px layout described (§Viewer). |
| Two name spaces | Anonymous cog aliases in-game and in every prompt; `policyNames` + `makeNameMap` spectator-side only (§The game). |
| Degrade never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6`, pre-batch deadline check with `RoundReserveSeconds = 150`, `endEarly()`, `sampleEpisode` fitting; **641.5 s** absolute worst case (§Decisions). |
| `num_agents` in every variant AND the cert fixture | **4** in `standard`, in `blitz`, in `certification.game_config`, and `<SEATS>` = **4** in `tools/ci/docker_smoke.sh`. |
| Engine RNG server-side and logged (idea's integrity note) | One `seed`; per-round seed and spawn permutation derived from it and written into the `round` event; `rand()` streams derived from it; the replay re-derives every tick (§Sim module). |
| Scripts sealed before the episode (idea's integrity note) | A seat's observation is built by `seatObservation`, which never reads another seat's `scripts[]`; asserted by `tests/test_prompt.nim` (§The game). |

---

## Tests

`tests/` runs under `nimble test` in `ci.yml`'s `build-test` job (the sandbox cannot run any of this
locally — CI is the only harness). The smoke job **`needs:` the build job** and never reuses a
cached binary: a stale binary cost bullwhip an hour on 2026-08-22.

**`tests/test_gwl.nim` — the language.** Lexing and indentation errors (odd indent, unopened
dedent) report the right line; every statement form parses and runs; `and`/`or` short-circuit;
`mod`/`div` in both infix and call form agree; unary minus; arrays, `len`, index-out-of-range is a
fault at the right line; `proc` params are by value, globals are visible, recursion to depth 64
works and 65 faults; the per-tick instruction budget stalls rather than faults and the VM **resumes
at the same pc** next tick; a program that runs off the end halts and never acts again; every fault
kind (`div 0`, `mod 0`, undefined name, wrong arg count, type mismatch, overflow, `rand(0)`) reports
`line` and `message`; `check`/`who` return the documented values including `FOG` past the 9×9 window;
the compile caps (120 lines, 100 chars, 4000 chars, 4000 nodes, 32 procs, nesting 8) each reject
with a message naming the limit.

**`tests/test_sim.nim` — the arena.** Spawn permutation is seeded and reproducible; the tick
resolution order on a hand-built board (a contested cell goes to the higher-priority seat, and the
priority rotation flips it next tick); `check` in tick *t* sees the board of tick *t−1* for every
seat; a move into a bomb/corpse/warrior is blocked and increments `blocked`; an illegal offset
wastes the tick and increments `illegal`; `bomb()` without energy is refused; fuse countdown,
plus-shaped blast, **chain reaction to closure**, scorching, kill attribution and `selfKills`;
elimination un-paints the dead warrior's tiles; the idle counter kills at exactly 50; a fault kills
at the fault pass with the line recorded; round reasons `horizon`/`lastStanding`/`wipeout`; the
scoring formula on hand-computed numbers, including that `Σ roundScore = 0` and `Σ scores = 0` to
1e-9; `endEarly` produces `reason = "deadline"` and divides by `roundsPlayed`; seed determinism (the
same config twice gives an identical digest); `sampleEpisode` is idempotent.

**`tests/test_bot.nim` — bounded orders / legality on the scripted baselines.** `painter`, `bomber`
and `sentry` each compile; four seats of each play whole episodes (several seeds) with **zero**
faults, zero stalls, zero illegal actions, zero refused bombs while energy ≥ `bombCost`, every action
legal as submitted, and every episode ending `complete` in under 2 s; `painter` beats `sentry` on
mean `score` over ten seeds; `decideAll` with no credentials returns exactly the scripted decisions
and never touches the network; reply parsing (array form, string form, fenced form, trailing prose,
missing `script`, over-long lines, 120-line and 4000-char truncation, `notes`/`banner` caps) —
including that a 700-`é` string caps at exactly `MaxNotesLen` **runes**.

**`tests/test_prompt.nim` — sealing and redaction.** A seat's system+user prompt contains its own
script and its own diagnostics, contains the board map and the series table, and **does not contain
any substring of any other seat's script**, any other seat's notes/banner, any policy name, or the
round seed. The player-socket `state` frame is likewise redacted.

**`tests/test_replay.nim` — end-to-end and strict UTF-8.** A full episode is played with scripted
seats, artifacts written to a temp dir; the replay is re-read with a **strict** JSON parser
(`parseJson` on the raw bytes plus a `validateUtf8` == −1 assertion) after a round where every seat
submitted a script, notes and banner full of multi-byte characters truncated at the caps;
`replayMatch(config, events)` re-derives every round and its `digest` equals the recorded one for 20
seeds; `frames.len` equals `Σ over played rounds of (Seats + ticksPlayed[r] + 1)`; the final frame
equals the live `framesJson` tail; event JSON round-trips (`eventFromJson(eventToJson(e)) == e`) for all five
kinds; `results.reason` ∈ {`complete`, `deadline`} and nothing else can be produced.

**`tests/test_viewer.nim` — chrome invariants.** `client/chrome.css` byte-matches the starter's file
up to the appended `/* Grid Wars */` marker; `client/replay.html` and `replay-viewer/index.html`
contain **every** starter element id listed in §*Viewer* and no starter element was removed; the
appended JS block defines no top-level name that the chrome above it already defines; every
`beat-marker` kind the renderer can emit has a CSS rule; `#viewpanel` appears nowhere.

**`tools/ci/docker_smoke.sh` (job `docker-smoke`)** — builds the production image and runs one real
episode in raw docker with the certification fixture's seat mix (4 seats), asserting the game exits
0, `results.json` and the replay exist, the replay parses as JSON, **every player container exited
0**, and the four seat-count invariants (`SEAT-COUNT FAIL:` is grepped, never trusted to job colour).
It copies the replay to `dist/smoke/` for the next job.

**`tools/ci/viewer_smoke.mjs` (job `wasm-viewer`, `needs: docker-smoke`)** — the only gate that
**executes** the bundle rather than building it: it builds `dist/static-replay-viewer` via
`tools/build_replay_viewer.sh`, downloads the replay `docker-smoke` produced, opens the bundle in
pinned Playwright Chromium against **that** replay, and requires `data-replay-loaded="true"` (not
merely a `ready` message), no `data-replay-error`, non-empty `#clock`/`#scorebug`/`#feed`, a live
`#scrub`, and — with **`--soak 10`** — that the clock keeps advancing during uninterrupted playback
(cogball 0.1.4: a mid-replay exception that scrubbing hides).

---

## Out of scope (v1)

- Any seat count other than 4; spectator seats; seats joining or leaving mid-episode; a human-in-
  the-loop warrior editor.
- Boards other than 30×30, non-toroidal boards, walls/obstacles placed at spawn, terrain, or
  asymmetric spawns beyond the seeded permutation of the four fixed corners.
- Floats, strings, tables, sets, objects, closures, `import`, user-defined types, `echo`, or any IO
  in GWL. Numbers are int64 and that is the whole type system besides bool and int arrays.
- Reusing the prototype's own engine (its web build is a minified Nim→JS bundle with no embeddable
  API and no source, and it cannot compile into the Nim wasm module the static viewer needs), and
  bit-exact fidelity to the prototype's undocumented constants.
- Warrior-to-warrior communication of any kind: no shared memory, no message ops, no reading another
  warrior's code or registers. `banner` is spectator-only, precisely so it cannot become a
  coordination channel.
- Cross-episode memory: a policy starts every episode from its prompt, with no carried-over warrior.
- Mid-round patching, hot-reloading a script, or a warrior that spawns another warrior; multiple
  warriors per seat.
- Bomb variants (remote detonation, blast radius upgrades, defusing), power-ups, items, health
  points, or any resource other than `energy`.
- Scoring on anything but tiles, survival and kills — no style points, no code-length bonus, no
  penalty for stalls or illegal actions beyond the tick they waste.
- A live-server (`/client/replay`) replay viewer, a zoom bar or minimap, an RL vector observation,
  real-time play, localisation and audio.
- An in-viewer editor, a diff view between rounds, or syntax highlighting beyond the executing-line
  marker in `#codepane`.
