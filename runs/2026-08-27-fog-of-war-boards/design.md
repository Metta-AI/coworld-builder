# Fog-of-War Boards — design note (`Metta-AI/cogame-fog-of-war-boards`, v1)

This coworld is forked from **`Metta-AI/cogame-babel`** (read at commit `d55d999`, "0.1.4: static
viewer announces loading/ready/error to its host"), the current head of the
parley → cosino → focus → babel lineage: a turn-based, native-rules, *a-policy-is-just-a-prompt*
game whose server makes every decision by sending the acting seat's prompt to Claude, with a
scripted baseline that plays any seat — and every seat when there are no credentials. That is
exactly this game's shape (a board, one move per seat per turn, hidden information the server
alone holds, decisions that are a short structured reply), so babel is the starter, and **every
convention there holds here unless this note says otherwise**: the `bitworld/runtime` contract,
the mummy HTTP/WS server, the `sim.nim` / `llm.nim` / `server.nim` split, `tableNames`' seeded
anonymous cog aliases, the `PlayBudgetFraction = 0.6` deadline stop, the artifact-writing order in
`finishEpisode`, the `replayMatch` re-derivation, the emscripten `MODULARIZE` / `EXPORT_NAME`
viewer bootstrap, and the Ink & Print broadcast chrome. Where this note deviates from babel it
says so and says why. **No file in this repo comes from any starter other than cogame-babel**;
the one idea borrowed from a sibling is named explicitly and only in `## Decisions` (bullwhip's
`decideAll` parallel-batch shape, named as the thing a *future* simultaneous variant would use —
no shipped variant is simultaneous, so nothing is actually copied from it in v1).

### Source idea (verbatim)

> OS Fog-of-War Boards — Kriegspiel, Dark Hex, Phantom Go, Reconnaissance Blind Chess: classic
> boards where you can't see the enemy
>
> Merged port of OpenSpiel's hidden-information board games. Kriegspiel: chess where you see only
> your own pieces and a referee tells you 'illegal', 'capture on e5', 'check'. Dark Hex / Phantom
> Go / Phantom Tic-Tac-Toe: you discover the opponent's stones only by trying to play on them.
> Reconnaissance Blind Chess (RBC): each turn you first *sense* a 3×3 window, then move.
> Perfect-info classics turned into inference games.
>
> Seats: 2
> Motive: zero-sum, imperfect information
> Policy interface: board move + (RBC) sense square per turn; LLM plausible with a board decode
> Fills gap: hidden-information versions of games cogs already 'know' — isolates belief tracking
> from rules knowledge
> Integrity (anti-collusion): 2-player, zero-sum; anonymous aliases.
>
> Replay plan (watchability): spectators see the true board plus each player's belief overlay —
> the gap between them is the show.
>
> Source: OpenSpiel kriegspiel, dark_hex, phantom_go, phantom_ttt, rbc.

---

## The game

Two cogs. One board. Each sees only its own stones. The **only** channel through which a seat
learns anything about the opponent is the referee's answer to the seat's own action: you name a
cell, and the referee says **PLACED** or **OCCUPIED**. Everything else — where the opponent's
stones are, how many it has in the abrupt variants, what it is thinking — is fog. The whole skill
is belief tracking on rules a cog already knows cold, which is exactly the gap the idea names.

`num_agents` is **2**, in every manifest variant's `game_config` and in `certification.game_config`
(and therefore `<SEATS>` = `2` in `tools/ci/docker_smoke.sh`). It is 2 because every shipped
variant is a two-sided zero-sum board game — a Hex rhombus has exactly two pairs of edges, a
tic-tac-toe grid exactly two marks — and the idea pins it at 2.

### Which of the five source games ship in v1, and why

**Shipped: Phantom Tic-Tac-Toe and Dark Hex** — two source games, **four manifest variants**, one
sim module, one viewer.

| `id` | Source | `mode` | `size` | `abrupt` | `sense` | `maxPlies` | `num_agents` |
|---|---|---|---|---|---|---|---|
| `phantom-ttt-3` | OpenSpiel `phantom_ttt` | `phantom-ttt` | 3 | `false` | 0 | 18 | **2** |
| `dark-hex-4` | OpenSpiel `dark_hex` (classical, `cdh`) | `dark-hex` | 4 | `false` | 0 | 32 | **2** |
| `dark-hex-5` | OpenSpiel `abrupt_dark_hex` (`adh`) | `dark-hex` | 5 | `true` | 0 | 50 | **2** |
| `recon-hex-5` | RBC's sense-then-move loop on Dark Hex — **not** a port of OpenSpiel `rbc` | `dark-hex` | 5 | `true` | 2 | 50 | **2** |

**Out: Kriegspiel, Reconnaissance Blind Chess, Phantom Go.** The reason is one property, and it is
the property this sim module is built around: in Phantom Tic-Tac-Toe and Dark Hex a stone, once
placed, never moves and is never removed, so **a seat's knowledge is monotone** — anything the
referee has ever told you stays true forever. That single invariant is what lets one `Sim` type,
one observation builder, one referee vocabulary, one legality predicate and one belief overlay
serve every shipped variant honestly.

- **Kriegspiel and RBC break it at the rules level.** They need a complete chess engine (legal-move
  generation, castling, en passant, promotion, check/checkmate/stalemate, threefold and 50-move),
  a *second* referee vocabulary (`illegal`, `capture on e5`, `check — long diagonal`, `no`), and,
  for RBC, a second action space (sense *then* move) and a piece-art board. That is a second sim
  module and a second viewer wearing this one's clothes. Shipping them as a wrapper over this
  module would be a lie about what the code does.
- **Phantom Go breaks it at the knowledge level.** Captures remove stones, so "I discovered a
  stone at c4" can become false; the belief overlay would mean something different in that variant
  than in every other one, and the engine needs liberties, suicide, positional superko and
  Tromp-Taylor scoring. A third engine whose overlay has different semantics is not one viewer
  honestly carrying four variants.
- **`recon-hex-5` is shipped and its provenance is stated in the manifest and the docs page**: it
  is Abrupt Dark Hex 5×5 with RBC's *reconnaissance* mechanic transplanted onto it — each ply the
  mover first names a 2×2 window and is told the truth about those four cells, then moves. It ships
  because it is the only way to carry the idea's named "first *sense*, then move" loop without a
  chess engine, it costs one extra field in the reply and one extra event kind, and it is the one
  variant where knowledge of **emptiness** goes stale (a cell you sensed empty on ply 6 may hold a
  stone by ply 14) — the closest this repo gets to RBC's real texture. It is labelled as an
  original variant, never as an OpenSpiel port.

### Coordinates and the board

Cells are named in **algebraic notation**: files `a`, `b`, `c`, … left to right; ranks `1`, `2`,
`3`, … bottom to top. A 5×5 board runs `a1`…`e5`. Internally a cell is `(row, col)` with
`row` 0-based from the bottom and `col` 0-based from the left; `cellName(row, col)` and
`cellIndex(name)` are the only two places the two representations meet. Nothing spectator-facing
ever shows an internal index: the feed says `plays c3`, never `plays 12`.

**Phantom Tic-Tac-Toe (`mode: "phantom-ttt"`, `size: 3`).** Seat 0 is **X** (red), seat 1 is **O**
(blue). A seat wins by owning all three cells of one of the eight lines (3 rows, 3 columns, 2
diagonals). A full board with no line is a draw.

**Dark Hex (`mode: "dark-hex"`, `size` 4 or 5).** The board is an `n × n` rhombus of hexagons.
Cell `(r, c)` is adjacent to `(r, c−1)`, `(r, c+1)`, `(r−1, c)`, `(r+1, c)`, `(r−1, c+1)` and
`(r+1, c−1)` — the standard rhombus neighbourhood. **Seat 0 (red) connects the left file
(`c = 0`) to the right file (`c = n−1`); seat 1 (blue) connects the bottom rank (`r = 0`) to the
top rank (`r = n−1`).** Hex has no draws: on a full board exactly one of those two connections
exists.

**Seat 0 always moves first**, and `config.first = 0` is recorded in the replay so the viewer can
say so. *Decided, with reason:* the first-move advantage is real in perfect-information Hex and
much weaker under fog, and the ladder already seats each policy in both slots across a round
robin, which balances it without a swap/pie rule (pie is out of scope — `## Out of scope (v1)`).

### Turn structure: a ply is one attempt

The atomic unit is a **ply** = one seat naming one cell (preceded, in `recon-hex-5`, by one sense
anchor). This is OpenSpiel's own decomposition — in the non-abrupt games a collision is a decision
node, not a free retry — and it is what makes the episode length provably bounded and the
wall-clock arithmetic below checkable rather than hopeful.

- **Non-abrupt** (`abrupt: false`, `phantom-ttt-3` and `dark-hex-4`): a ply that hits an opponent
  stone (a *collision*) does **not** end the mover's turn — the same seat moves again on the next
  ply, now knowing one more cell.
- **Abrupt** (`abrupt: true`, `dark-hex-5` and `recon-hex-5`): a collision **ends the turn**. The
  seat has spent its move to buy one fact.

**A seat may never attempt a cell it already knows is occupied, nor one of its own stones, nor an
off-board cell.** Those are not game actions; they are invalid replies (step 5 below), because a
seat provably knows they are forbidden and charging a ply for them would punish parse noise rather
than inference. This is also what bounds the episode: each collision by a seat permanently removes
one cell from that seat's legal set, so collisions by a seat ≤ the opponent's stone count, and

```
plies ≤ cells (placements) + cells (collisions, ≤ one per opponent stone per seat) = 2 × cells
```

— which is exactly the `maxPlies` pinned per variant (18, 32, 50, 50). In Hex the board fills
before the cap can bite, and a full Hex board always has a winner, so `ply-cap` is unreachable
there; it is kept as a belt-and-braces ending anyway.

### Resolution order for ply `p` (0-based)

**This is the order the sim executes, and the order the events appear in the replay.**

1. **`beginPly`.** `mover` = seat 0 on ply 0; thereafter the previous mover again if the previous
   ply was a collision **and** `abrupt == false`, otherwise the other seat.
2. **Wall-clock guard.** If `now + worstPlySeconds > playDeadline` →
   `settle("deadline", "wall-clock")` and stop. Checked here, **before** any observation is built,
   so the episode never stops mid-ply. (`worstPlySeconds = 2 × llmTimeoutSeconds + 2 = 62`;
   `playDeadline = gameStart + 0.6 × episodeTimeoutSeconds`.)
3. **Build the mover's observation** (§`## Server, player, protocol`). It contains
   `legalAttempts(mover)` and, when `sense > 0`, `legalAnchors(mover)` — both produced by the
   *same procs the validator applies* in step 5, so prompt and validator cannot drift.
4. **Decide.** A scripted seat (or any seat when there are no LLM credentials) is decided inline
   by its baseline. An LLM seat gets **one** call, bounded by `llmTimeoutSeconds` (30 s) inside
   curly. Turns are strictly sequential — see `## Decisions`.
5. **Parse + legality probe.** The reply is JSON-extracted (first `{` … last `}`, fences and
   trailing prose tolerated), parsed, and applied to a **copy** of the sim; if the copy rejects it,
   the reply is invalid. Invalid, unparseable or timed-out → **one retry** carrying the printed
   legal set → the `probe` baseline. On a fallback, `fallbacks[mover] += 1` and one
   `falling back` line goes to stdout so the hosted log is greppable.
6. **Sense** (only when `sense > 0`). Apply the anchor `(r, c)` with `r ≤ n − sense` and
   `c ≤ n − sense`: the referee truthfully reveals the `sense × sense` block
   `{(r+i, c+j) : 0 ≤ i,j < sense}` to the mover **only**. Each revealed cell becomes either
   `knownOpponent[mover]` (permanent) or `sensedEmptyAt[mover][cell] = p` (perishable — the cell
   may be filled later). Emit the `sense` event.
7. **Attempt.** Read the target cell.
   a. Cell empty → the mover's stone is placed. `result = "placed"`, `stones[mover] += 1`.
   b. Cell holds an opponent stone → **nothing is placed**. `knownOpponent[mover]` gains the cell,
      `probes[mover] += 1`, `result = "occupied"`.
   (7c does not exist: own stones, already-known opponent cells and off-board cells are excluded
   from `legalAttempts` and rejected in step 5.)
8. **Record and emit.** The mover's already-truncated `say`, `notes` and `guess` are stored, and
   the `attempt` event is emitted.
9. **Win check** (only after 7a). Hex: union-find over the mover's stones; if the mover's two
   edges are in one component, emit `win` (carrying the connecting path) and
   `settle("complete", "connection")`. Tic-tac-toe: if the placed cell completes one of the eight
   lines, emit `win` (carrying the three cells) and `settle("complete", "line")`.
10. **Turn transfer.** `result == "placed"` → the other seat moves next. `result == "occupied"` →
    the other seat moves next when `abrupt`, the **same** seat when not.
11. **Board-full check** (tic-tac-toe only, after 7a): no empty cell remains and no line was made
    → `settle("complete", "board-full")`.
12. `plies += 1`. If `plies == maxPlies` → `settle("complete", "ply-cap")`.
13. **Pace.** `sleep(turnDelayMs)`, and if this ply used an LLM call, do not open the next
    LLM-driven ply until `plySpacingSeconds` have elapsed since this ply's first LLM call started
    (§`## Decisions` — the Bedrock sidecar rate floor). Continue at 1.

### The tension metric: `distToWin`

One number per seat, defined for both modes, recomputed after every ply, and load-bearing (it
scores every non-terminal ending and drives the scorebug):

- **Hex.** `distToWin(seat)` = the minimum number of *additional* cells the seat must own to
  complete its connection, computed as a 0–1 BFS from the seat's source edge to its target edge
  where a cell owned by the seat costs 0, an empty cell costs 1, and a cell owned by the opponent
  is impassable. Unreachable → the sentinel **99** ("already lost").
- **Tic-tac-toe.** A line is *live* for a seat if it contains no opponent mark.
  `distToWin(seat) = min over live lines of (3 − the seat's marks in that line)`; no live line →
  **99**.

It is computed **twice**, on two different boards, and the difference is the show:

- On the **true** board, for the scorebug, the endcard, results and the `ply-cap`/`deadline`
  scoring rule.
- On the **seat's believed board** (its own stones, the opponent stones it has discovered,
  everything else treated as empty), for that seat's own prompt. A seat is never told the true
  value.

### Scoring formula and sign

```
score_i = +1  if seat i won
           0  on a draw
          -1  if seat i lost              score_0 + score_1 = 0, always
```

**Higher is better, the array sums to zero, and the league ranks by mean episode `score`, higher
first.** No other field is a ranking metric. *Decided, with reason:* the idea pins "zero-sum", both
shipped games are win/lose/draw with no natural margin, and a ±1 outcome is what Elo consumes
cleanly; every richer number (probes, discovery, guess accuracy) is reported for the audit and the
audience and is deliberately **not** scored, so no policy can farm the metric instead of winning.

**Who won, by ending:**

| `ending` | Winner |
|---|---|
| `connection` | the seat that connected its two edges |
| `line` | the seat that completed a line |
| `board-full` | lower true `distToWin`; equal (including 99 vs 99) → **draw** |
| `ply-cap` | lower true `distToWin`; equal → **draw** |
| `wall-clock` | lower true `distToWin`; equal → **draw** |

`results` also reports, for humans and the audit: `outcome[]` (1 / 0.5 / 0), `stones[]`,
`probes[]` (collisions the seat caused), `discovered[]` (opponent cells the seat knew at the end),
`guessesMade[]`, `guessAccuracy[]`, `distToWin[]` (true, final), `fallbacks[]`, `plies`,
`maxPlies`, `mode`, `size`, `abrupt`, `sense`, `ending`, `reason`, `names` (**policy** names).

### End conditions and `results.reason`

`results.reason` has **exactly two legal values**: `"complete"` and `"deadline"`. *Decided, with
reason:* phase 60 check 4 greps a finished replay for `results.reason == "complete"` (or a
`deadline` the design declares acceptable), so promoting `"connection"` to a reason would fail
verification on a perfectly healthy episode. The finer ending rides in a **separate** field,
`results.ending`, with exactly five legal values:

| `reason` | `ending` | When |
|---|---|---|
| `complete` | `connection` | Dark Hex: a seat linked its two edges |
| `complete` | `line` | Phantom Tic-Tac-Toe: a seat completed one of the eight lines |
| `complete` | `board-full` | Phantom Tic-Tac-Toe: every cell is taken and no line exists |
| `complete` | `ply-cap` | `maxPlies` plies played with no terminal position (unreachable in Hex; kept as a guard) |
| `deadline` | `wall-clock` | the play deadline stopped the episode between plies |

**`deadline` is an acceptable ending for this coworld and is declared as such here**: the episode
is fully scored at the stop by true `distToWin`, so a deadline result is a real result, not a
discarded one. It should nonetheless be rare — see the arithmetic in `## Decisions`.

The `end` event carries both `reason` and `ending`, and the **same `settle(reason, ending)` proc**
applies them on record and on playback, so a wall-clock stop — which is not derivable from the
attempts — re-derives identically in the wasm viewer (particle-worlds `13c66d7`, 2026-08-26: a
deadline stop applied outside the shared proc hash-mismatches at the stop tick).

### Anti-collusion

All three mechanisms the idea names, all structural rather than advisory:

1. **Two seats, zero-sum.** There is no coalition to form: one seat's gain is the other's loss by
   construction (`score_0 + score_1 = 0`).
2. **Anonymous aliases.** Seats play as `Sprocket`, `Gizmo`, … (babel's `CogNames` pool, seeded
   shuffle via `tableNames`); no prompt, no player frame and no in-game text ever contains a policy
   display name.
3. **No inter-seat channel at all.** `say` is spectator-facing only and is never shown to the
   other seat; `notes` are private and fed back only to their author; the per-seat `/player`
   `state` frame is redacted to that seat's own tallies and carries no board. Every decision is
   made inside the game server from a per-seat view the server builds, so there is no wire on
   which two seats could coordinate.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | How this note satisfies it |
|---|---|
| Starter by game shape | cogame-babel — turn-based board, native rules, policy = prompt (top of this note) |
| Public repo `Metta-AI/cogame-<slug>` | `gh repo create Metta-AI/cogame-fog-of-war-boards --public …` in phase 20; `## Packaging` |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `## Decisions` — `PLAYER_PROMPT` vs `PLAYER_SCRIPTED=probe\|sweep`, both algorithms given in full, per variant |
| Simultaneous games: one parallel batch + the 60 % budget | `## Decisions` §Sequential turns — no shipped variant is simultaneous; the batch shape is named for a future one, and the 60 % arithmetic is spelled out |
| Degrade, never hang | `## Decisions` §The ladder; the ply guard in step 2; `deadline` / `wall-clock` above |
| Static wasm replay viewer, never a pod | `## Viewer`; `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` |
| Real art, starter chrome verbatim | `## Viewer` §Chrome provenance and §Art |
| Legible to a casual spectator | cells drawn `c3`, results said in words ("Gizmo is already there"), never internal indices; `## Viewer` §Readouts; the 360 px check |
| Two name spaces | aliases in-game, `policyNames` spectator-side, `results.names` = policy names |
| `num_agents` in every variant and the cert fixture | `## Packaging` — **2** in all four variants' `game_config` and in `certification.game_config`; `<SEATS>` = 2 |
| Tests in CI (sim, bot, e2e replay, strict UTF-8, viewer smoke) | `## Tests` |

---

## Decisions: LLM with scripted fallback

**Both policy kinds ship in the same image from day one, switched by environment**, exactly as
babel does it. `/bin/fog-of-war-boards-player` reads:

- **`PLAYER_PROMPT`** — an LLM policy. The string is delivered to the game server over the player
  websocket, and the server sends it to Claude with the seat's observation on every ply.
- **`PLAYER_SCRIPTED=<name>`** — a scripted policy. The server plays the named baseline for that
  seat, no LLM. `<name>` is `probe` or `sweep`; `1`, `true` and `yes` are accepted as synonyms for
  `probe`.

With neither set the player delivers a built-in default prompt (below). With no credentials at all
the LLM client disables itself once and every seat plays `probe` immediately — no retries, no
network waits — which is what makes offline certification and `docker_smoke.sh` complete.

### The two scripted baselines (exact algorithms)

Both are deterministic given the sim state and the episode seed, **always produce a legal attempt
(and, where required, a legal sense anchor)**, and never produce `say`, `notes` or `guess`. Both
read only what their seat is allowed to see — they run against the seat's *believed* board
(own stones + `knownOpponent` + `sensedEmptyAt`; everything else treated as empty), never the true
one. That is asserted by a test.

**`probe`** — the default filler, and the fallback every failed LLM decision lands on.

- *Sense (when `sense > 0`):* score every legal anchor by the number of cells in its window that
  are **unknown**, plus the number that are **sensed-empty but stale** (`p − sensedEmptyAt ≥ 4`);
  take the highest score, ties broken by lowest anchor index (row-major).
- *Dark Hex:* compute `distToWin(seat)` on the believed board. For every legal attempt `x`,
  compute the same distance with `x` added to the seat's stones; play the `x` that reduces it most.
  Ties break by smaller Chebyshev distance from the board centre, then by lowest cell index. This
  is a real Hex player (a shortest-path chain builder) and it probes the opponent as a side effect,
  because the cells on its shortest path are exactly the ones the opponent wants.
- *Phantom Tic-Tac-Toe:* (1) if some legal attempt completes a line on the believed board, take it;
  (2) else if some legal attempt blocks a line on which the opponent already has two **known**
  marks, take it; (3) else take the first legal attempt in the fixed priority order
  `b2, a1, c1, a3, c3, b1, a2, c2, b3` (centre, corners, edges).

**`sweep`** — the second filler; a deliberately different shape so the ladder is not two copies of
one bot.

- *Sense:* anchors in round-robin row-major order, one per ply, wrapping.
- *Dark Hex:* walk a straight corridor. Seat 0 walks the middle rank `r = n div 2` from file `a`
  to file `n−1`; seat 1 walks the middle file `c = n div 2` from rank 1 to rank `n`. Attempt the
  next unowned cell of the corridor; on `OCCUPIED`, shift the whole corridor one step (seat 0
  `r → r+1`, wrapping modulo `n`; seat 1 `c → c+1`, wrapping) and continue from the same offset.
  If every corridor cell is exhausted, take the lowest-index legal attempt.
- *Phantom Tic-Tac-Toe:* the fixed priority order above, with no win/block search at all.

A test asserts they disagree on at least 30 % of plies over 200 seeded episodes — two fillers that
play the same game are one filler.

### Sequential turns, the rate floor, and the wall-clock arithmetic

**Every shipped variant is strictly sequential**: exactly one seat decides per ply, and the sim
cannot build the next observation until the current attempt has been applied (the next mover
depends on whether this ply collided). So LLM calls go out **one at a time**, not in a batch, and
that is a property of the rules, not an oversight. *If a future variant introduces simultaneous
decisions*, its calls must go out as **one parallel batch per turn** — a `curly.RequestBatch`
filled with one `post` per open seat and issued with `client.curl.makeRequests(batch,
llmTimeoutSeconds)`, the `decideAll` shape in `cogame-bullwhip/src/bullwhip/llm.nim` — because
sequential per-seat calls are the documented way to blow the 720 s budget. Nothing in v1 uses it.

Config knobs and defaults: `llmTimeoutSeconds = 30`, `maxOutputTokens = 900` (not 400 — Haiku is
`cut off at max_tokens` at 400), `model = "claude-sonnet-5"` (the hosted Bedrock path tries
`us.anthropic.claude-haiku-4-5-20251001-v1:0` first, and **the candidate list drops
`us.anthropic.claude-sonnet-4-6`**, which times out on every sidecar call — raid, 2026-08-23),
`plySpacingSeconds = 0` meaning *derive as 4*.

**Rate floor.** The Bedrock sidecar caps **30 requests per minute per episode**. A ply issues at
most 2 requests (the call plus one retry), so the minimum spacing between the starts of two
LLM-driven plies is `2 × 60 / 30 = 4 s`. The loop sleeps to that floor; it gates LLM plies only, so
the all-scripted certification path is unaffected.

**The arithmetic, out loud.** The game container never receives `COWORLD_TIMEOUT_SECONDS`, so it
assumes `episodeTimeoutSeconds = 1200`; play budget = `0.6 × 1200 = **720 s**`. Per-ply expected
wall clock is `max(4 s floor, ~3 s haiku latency) + ~0.4 s apply/broadcast ≈ 4.4 s`.

| Variant | `maxPlies` | Expected plies | Expected play | % of 720 s |
|---|---|---|---|---|
| `phantom-ttt-3` | 18 | ~11 | `11 × 4.4 ≈ 48 s` | 7 % |
| `dark-hex-4` | 32 | ~20 | `20 × 4.4 ≈ 88 s` | 12 % |
| `dark-hex-5` | 50 | ~30 | `30 × 4.4 ≈ 132 s` | 18 % |
| `recon-hex-5` | 50 | ~30 | `30 × 4.4 ≈ 132 s` | 18 % |

Worst case per ply is `2 × llmTimeoutSeconds + 2 = 62 s`, and `50 × 62 = 3100 s` would overrun by
four times. That is why **step 2 of the resolution order refuses to open a ply unless
`now + 62 s ≤ playDeadline`** and settles `deadline` / `wall-clock` instead. The guard, not
optimism, is what keeps the episode inside the budget; the expected path finishes at under a
fifth of it.

Certification / smoke path: with no `ANTHROPIC_API_KEY` both seats play `probe`, there is no LLM
call, the spacing floor does not apply, `turnDelayMs = 0`, and the `dark-hex-5` fixture completes
in well under 3 s of play — inside `coworld certify`'s 60 s default. The release workflow still
passes `--timeout-seconds 300`, and a test pins the fixture's scripted duration under 50 s
(cogame-commons-family 0.1.0, 2026-08-24).

### The ladder — degrade, never hang

Per ply:

1. **One LLM call**, timeout `llmTimeoutSeconds` (30 s), enforced by curly, not by hope.
2. **Parse + legality probe** on a copy of the sim (step 5 of the resolution order).
3. **One retry**, with this hint appended to the user prompt:
   *"Your previous reply was invalid. Respond with ONLY the requested JSON object; `cell` must be
   one of: `<legalAttempts(seat), printed>`"* — plus, in `recon-hex-5`, *"and `sense` must be one
   of: `<legalAnchors(seat), printed>`"*. Printing the legal set, computed by the **same predicate
   the validator applies**, is what halves fallbacks in formal-output games (escrow 0.1.3,
   2026-08-23).
4. **Fallback** to `probe`, `fallbacks[seat] += 1`, and a `falling back` line on stdout.
5. If credentials are missing or auth fails, the client disables itself once and every later
   decision is scripted immediately.

Episode-level: the play deadline settles the episode **between plies, never mid-ply**; results and
the replay are written in babel's `finishEpisode` order (final frames to players → `results.json`
→ `.replay`); `/healthz` and `/global` keep answering for a **20 s shutdown grace** after the
artifacts land (lantern 0.1.3 → 0.1.4: the certifier pings `/global` *after* the player pods
start), then `quit(0)`. The player binary wraps its receive loop in `try/except CatchableError`
and **exits 0 on a dead socket** (raid 0.1.3 → 0.1.4: whisky *raises* on a close frame and the
player container otherwise exits 1, intermittently).

### The two champion prompts (exact text)

`tools/ci/policies.json` mints four policies. Champion #1 and champion #2 are **both**
`PLAYER_PROMPT` policies — a scripted policy seated as a champion is a failure state.

- **`fog-of-war-boards-cartographer`** (champion #1, owner daveey,
  `ply_44ae9048-3242-4654-881f-6d9d43347fa3`):

  > Keep a map, and rewrite it in your notes every single ply. Your notes are the only memory you
  > have: list YOUR stones, the opponent stones you have PROVEN, and the cells you have never
  > touched, and mark each untouched cell as likely-theirs or likely-empty with a reason. HEX: play
  > the cell that shortens your own chain the most, and prefer a cell that also sits on their
  > shortest path — one stone that builds and blocks is worth two that only build. Treat a
  > collision as a gift, not a loss: you just bought a certainty, so immediately re-route your
  > chain around it and write the new route down. Never attempt a cell you have already proven is
  > theirs. TIC-TAC-TOE: take the centre if it is untouched, then build two threats at once; if
  > you have two in a line and the third cell is untouched, take it now. When you sense, point the
  > window where your route crosses ground you have never seen.

- **`fog-of-war-boards-prober`** (champion #2, owner daveey-1,
  `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`):

  > Spend moves on information early and on connection late. Count the plies: in the first third of
  > the board, deliberately attempt cells on the opponent's most natural route — a collision costs
  > you a stone but tells you exactly where they are building, and in the abrupt variants it tells
  > you they wasted nothing. In the last third, stop probing entirely and take the shortest
  > remaining route to your own edges. Model them out loud in your notes: they are trying to
  > connect the opposite pair of sides, so their stones lie near the straight line between their
  > edges — say which cells that predicts and put those cells in your `guess` list every ply so
  > your reasoning is on the record. HEX: bridge with a gap when you can — two stones a knight's
  > step apart are hard to cut. When you sense, point the window at the middle of their predicted
  > route, not at your own stones.

- **`fog-of-war-boards-probe`** (filler): `PLAYER_SCRIPTED=probe`.
- **`fog-of-war-boards-sweep`** (filler): `PLAYER_SCRIPTED=sweep`.

The player binary's built-in default prompt (used when `PLAYER_PROMPT` is unset and the seat is
not scripted) is: *"You can only see your own stones. Every ply, write down what you have proven
about the opponent and what you merely suspect, then play the cell that most shortens your own
connection while sitting on the route they most likely need. Never attempt a cell you already know
is theirs. Reply with only the JSON object."*

---

## Sim module

Pure rules: no IO, no networking, no LLM. Driven identically by the server, the tests and the wasm
viewer, which is what makes the replay re-derivable. The layout mirrors babel's. The Nim package
is `fogboards` (short); the *binaries* carry the full slug because `tools/ci/docker_smoke.sh`
defaults to `/bin/<slug>`.

```
fogboards.nimble
src/fogboards.nim                    entrypoint -> /bin/fog-of-war-boards          (fork of src/babel.nim)
src/fogboards_player.nim             player     -> /bin/fog-of-war-boards-player   (fork of src/babel_player.nim)
src/fogboards/types.nim              config, events, enums                         (fork of src/babel/types.nim)
src/fogboards/sim.nim                the rules below                               (fork of src/babel/sim.nim)
src/fogboards/llm.nim                Claude client, prompts, the two baselines      (fork of src/babel/llm.nim)
src/fogboards/server.nim             mummy HTTP/WS server, replay writer            (fork of src/babel/server.nim)
replay-viewer/fogboards_replay.nim   wasm entry                                     (fork of replay-viewer/babel_replay.nim)
```

### Types

```nim
type
  FogError* = object of CatchableError

  Mode* = enum
    mPhantomTtt = "phantom-ttt"
    mDarkHex    = "dark-hex"

  GameConfig* = object
    tokens*: seq[string]                # connection tokens, injected by the runner
    players*: seq[PlayerConfig]         # policy display names, by slot
    mode*: Mode
    size*: int                          # 3 (ttt) | 4 | 5 (hex)
    abrupt*: bool                       # true: a collision ends the turn
    sense*: int                         # 0 = no reconnaissance; 2 = a 2x2 window per ply
    first*: int                         # the seat that moves on ply 0 (always 0 in v1)
    maxPlies*: int
    seed*: int
    episodeTimeoutSeconds*: int         # 1200
    plySpacingSeconds*: int             # 0 => derive 4
    turnDelayMs*: int                   # 250 (0 in the cert fixture)
    playerConnectTimeoutSeconds*: float # 180
    model*: string
    maxOutputTokens*, llmTimeoutSeconds*: int
    sampled*: bool                      # true once the budget fit has been applied

  Occupant* = enum
    ocEmpty = "empty", ocSeat0 = "seat0", ocSeat1 = "seat1"

  EventKind* = enum
    evStart   = "start"
    evSense   = "sense"
    evAttempt = "attempt"
    evWin     = "win"
    evEnd     = "end"
```

`update(config, json)` applies the runtime JSON over the defaults and **raises `FogError`** on: an
unknown `mode`; `players.len != 2`; `size` outside 3..7; `mode == mPhantomTtt and size != 3`;
`sense` outside 0..3; `sense > 0 and sense > size - 1`; `maxPlies` outside 4..120.

`sampleEpisode(config)` is idempotent (a replay carrying `sampled: true` is untouched) and fits the
episode: `maxPlies = clamp(maxPlies, 4, 2 * size * size)` and
`turnDelayMs = min(turnDelayMs, 120_000 div max(maxPlies, 1))`.

### Sim state

```nim
Sim* = object
  config*: GameConfig
  names*: seq[string]                # anonymous cog aliases (babel's tableNames, seeded shuffle)
  board*: seq[Occupant]              # size*size, row-major from rank 1
  known*: seq[HashSet[int]]          # known[seat] = opponent cells this seat has PROVEN
  sensedEmptyAt*: seq[Table[int,int]]# per seat: cell -> the ply it was last seen empty
  stones*, probes*, fallbacks*: array[2, int]
  guessesMade*, guessHits*: array[2, int]
  says*, notes*: seq[string]         # latest, per seat
  lastGuess*: seq[seq[int]]          # latest guess cells, per seat
  scripted*, fellBack*: array[2, bool]
  mover*: int
  ply*, plies*: int
  winner*: int                       # -1 = none yet / draw
  winPath*: seq[int]
  done*: bool
  reason*, ending*: string
  events*: seq[GameEvent]
```

### Procs the server, the tests and the viewer all call

- `initSim(config): Sim` — validates, seeds the aliases, empties the board, `mover = config.first`,
  logs `evStart`.
- `cellName*(sim, cell): string` / `cellIndex*(sim, name): int` — the algebraic ↔ index pair.
- `neighbours*(sim, cell): seq[int]` — the hex rhombus neighbourhood, or the 4-neighbourhood in
  `phantom-ttt` (unused there; kept so one board walker serves both).
- **`legalAttempts*(sim, seat): seq[int]`** — every on-board cell that is neither one of `seat`'s
  own stones nor in `known[seat]`, ascending. **The prompt, the retry hint and the validator all
  call this one proc**, so they cannot drift.
- **`legalAnchors*(sim, seat): seq[int]`** — `{(r,c) : r ≤ size − sense, c ≤ size − sense}` when
  `config.sense > 0`, else empty.
- `believedBoard*(sim, seat): seq[Occupant]` — the seat's own stones + `known[seat]`, everything
  else `ocEmpty`. Every prompt number and every baseline decision is computed from this, never
  from `board`.
- `distToWin*(sim, board, seat): int` — the 0–1 BFS (hex) or live-line minimum (ttt) above; 99
  when unreachable.
- `applySense*(sim, seat, anchor)` — step 6; raises `FogError` naming the anchor if illegal.
- `applyAttempt*(sim, seat, cell, say, notes, guess, scripted, fellBack)` — steps 7–12 in one
  atomic step. Raises `FogError` naming the seat and the cell if the attempt is not in
  `legalAttempts(seat)`; the server probes with this on a copy before committing.
- `endEarly*(sim)` — `settle("deadline", "wall-clock")`.
- **`settle*(sim, reason, ending)`** — the single proc that ends the game, decides the winner from
  the table above, and logs `evEnd`. Called on record **and** on playback.
- `score*(sim, seat): float` — `+1 / 0 / −1`.
- `resultsJson*(sim)`, `boardStateJson*(sim)`.
- `replayMatch*(config, events): seq[Sim]` — re-derives one state per event prefix by replaying
  `evSense` (anchor) and `evAttempt` (cell) through the rules and applying `evEnd`'s
  `reason`/`ending` through `settle`. `result` on `evAttempt`, and `seat`/`how`/`path` on `evWin`,
  are **re-derived and checked** against the recording, raising `FogError` on a mismatch.
- `eventToJson*` / `eventFromJson*`.

### Event vocabulary written to the replay

Five kinds. Every kind has a feed line, a scrub-beat class and CSS (`## Viewer`).

| kind | fields |
|---|---|
| `start` | `{kind, round: -1}` — the episode opens (names, config and seed ride in the replay header) |
| `sense` | `{kind, round, seat, anchor}` — `recon-hex-5` only; the revealed contents are re-derived from the board at that prefix |
| `attempt` | `{kind, round, seat, cell, result: "placed"\|"occupied", say, notes, guess:[cell], scripted, fellBack}` |
| `win` | `{kind, round, seat, how: "connection"\|"line", path:[cell]}` |
| `end` | `{kind, round, reason, ending, scores:[float]}` |

`round` is the **ply index** (0-based). *Decided, with reason:* the field is named `round` — not
`ply` — because the chrome copied verbatim from babel (`roundBase`, `renderFeed`'s block grouping
and `buildScrub`'s spans) groups on `event.round`, and renaming it would force edits into copied
regions for nothing. Everything human-facing renders it as **"PLY n"** (one named edit, listed in
§Chrome provenance).

Cells in events are **algebraic strings** (`"c3"`), never indices, so the bytes are readable and a
future board size cannot silently reinterpret an old replay. `say`, `notes` and `guess` are the
*already-truncated* values (rune boundaries — see the reply schema); nothing else in an event is
free text.

---

## Server, player, protocol

Babel's server, forked. Routes, **in registration order** (all before any catch-all, per lantern
0.1.1 — the certifier probes `/healthz`, `GET /client/player?slot=0&token=<t>` and
`GET /client/global` *before* the player pods start, and neither client route may open the player
socket):

```
GET /healthz                   {"ok": true}
GET /client/global             client/global.html
GET /client/player             client/player.html
GET /client/replay             client/replay_broadcast.html
GET /client/renderer.js        the game block
GET /client/chrome_common.js   the chrome
GET /client/chrome.css
GET /client/assets/@name       data/*.png, data/font.ttf
WS  /player?slot=N&token=T     fogboards.player.v1   (live mode only)
WS  /global                    spectator snapshots; answers Ping with Pong
WS  /replay                    the replay payload (replay mode only)
```

### Player protocol `fogboards.player.v1`

JSON text frames on `COWORLD_PLAYER_WS_URL`.

game → player:

- `{"type":"welcome","protocol":"fogboards.player.v1","slot":N,"name":"<alias>","seats":2,
   "mode":"dark-hex","size":5,"abrupt":true,"sense":0,"maxPlies":50}`
- `{"type":"state","slot":N,"name":"<alias>","ply":p,"maxPlies":M,"mode":…,
   "seat":{"score":f,"stones":k,"discovered":m,"probes":q,"distToWin":d,"fallbacks":n},
   "toMove":bool,"started":b,"done":b,"reason":s,"ending":s}` after every event.
  **Redacted:** it carries no board, no cell list, and nothing about the opponent beyond what this
  seat has proven. `distToWin` here is the *believed* value. Decisions are server-side, so this
  loses the policy nothing.
- `{"type":"final","done":true,"slot":N,"scores":[…],"outcome":[…],"names":[<aliases>],
   "plies":k,"reason":s,"ending":s}` at the end; the player exits after it.

player → game:

- `{"type":"prompt","prompt":"<≤4000 chars>","scripted":"probe"|"sweep"|true|false}` — sent on
  connect and again after `welcome` (the first send can race slot registration). The latest frame
  wins. Over-cap prompts are truncated **on a rune boundary**.

### Global protocol

`/global` sends the whole snapshot after every event:

```
{"type":"state","game":"fog-of-war-boards","mode":…,"size":5,"abrupt":true,"sense":0,
 "board":["empty","seat0",…],                       // the TRUTH; spectators only
 "seats":[{name, policy, stones, probes, discovered, distToWin, score,
           known:[cell], sensedEmpty:[{cell, ply}], guess:[cell], say, notes,
           scripted, fellBack}, ×2],
 "mover":0,"ply":14,"maxPlies":50,"plies":14,"lastAttempt":{seat,cell,result},
 "lastSense":{seat,anchor},"winner":-1,"winPath":[],"phase":"moving",
 "gameDone":false,"reason":"","ending":"","policyNames":[…],"events":[…],
 "started":true,"connected":[bool,bool]}
```

`phase ∈ {"sensing","moving","done"}`.

### The observation each seat gets (complete)

The **system prompt** (one per mode, identical for both seats) states the rules verbatim from
`## The game` — the board, the neighbourhood, the seat's own goal, the fog rule, the abrupt/
non-abrupt collision rule, the ply cap — the seat's alias, and the output contract, ending with:
*"reply with ONLY one JSON object, nothing else — no analysis, no explanation, no markdown fences.
Your reply must begin with the character `{` and end with `}`."* (Bedrock Haiku answers prose-first
without this.)

The **user prompt** for Dark Hex, in this order:

1. `Ply <p+1> of <maxPlies>. You are <alias>, playing RED on a 5×5 Dark Hex board.`
2. `YOUR GOAL: link the left file (a) to the right file (e) with an unbroken chain of your own
   stones. Cells touch on six sides: a3 touches a2, a4, b3, b2 — and c4 touches b4, d4, c3, c5,
   b5, d3.` (the neighbourhood spelled out with real cell names, not a formula)
3. `THE FOG: you see only your own stones and the opponent stones you have proven. You are never
   told anything about their moves.`
4. `YOUR STONES (<k>): b2 c3 c4`
5. `OPPONENT STONES YOU HAVE PROVEN (<m>): c2 d4`
6. `CELLS YOU SENSED EMPTY (may be stale): b3 (ply 6), b4 (ply 6)` — **`recon-hex-5` only**
7. `CELLS YOU HAVE NEVER TOUCHED (<u>): a1 a2 …`
8. `YOUR LEGAL ATTEMPTS: a1 a2 …` — `legalAttempts(seat)`, the same proc the validator applies
9. `YOUR LEGAL SENSE ANCHORS: a1 a2 … (each names the bottom-left corner of a 2×2 window)` —
   **`recon-hex-5` only**, `legalAnchors(seat)`
10. `STONES ON THE BOARD: you 3.` followed by **exactly one** of:
    - non-abrupt (`phantom-ttt-3`, `dark-hex-4`): `Opponent: exactly 3 — in this variant a
      collision does not end a turn, so they have placed one stone per turn they have taken.`
    - abrupt (`dark-hex-5`, `recon-hex-5`): `Opponent: unknown. They have taken 4 turns, but in
      this variant a turn that hits one of your stones places nothing, so they hold between 0 and
      4 stones.`
11. `YOU ARE 3 STONES FROM CONNECTING, on the board as you believe it to be.`
12. `REFEREE LOG (everything you have ever been told):` one line per action this seat took —
    `ply 1 — you played c3 — PLACED.` / `ply 5 — you played c2 — OCCUPIED: an opponent stone is
    there.` / `ply 9 — you sensed b2 — b2 empty, c2 OPPONENT, b3 empty, c3 yours.`
13. `YOUR NOTES FROM EARLIER PLIES:` the seat's latest notes verbatim, or `(none)`.
14. `GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules):` the seat's
    `PLAYER_PROMPT`.
15. The reply contract (below).

Phantom Tic-Tac-Toe replaces lines 2 and 11 with `YOUR GOAL: own all three cells of one row,
column or diagonal before your opponent does.` and `YOUR BEST LINE NEEDS 2 MORE CELLS, on the
board as you believe it to be.`, and drops line 6 and 9.

**Hidden from a seat**, exhaustively: every opponent stone it has not proven; every opponent
action, collision, sense, `say`, `notes`, `guess` and `PLAYER_PROMPT`; the mapping from aliases to
policy display names; the *true* `distToWin` of either seat; and — in the abrupt variants only —
the opponent's exact stone count. **Nothing else** is hidden: the board size, the full rules, the
ply cap, its own complete history and the referee's answer to every one of its own actions are all
given.

### Reply schema, with caps

```json
{"cell": "c4", "sense": "b3", "guess": ["d3", "d4"],
 "say": "his chain has to cross d3", "notes": "proven: c2,d4. route a3-b3-c3-d3-e3."}
```

| field | type | required | cap / legality | on violation |
|---|---|---|---|---|
| `cell` | string or `[col,row]` | **yes** | must be in `legalAttempts(seat)` | retry once, then `probe` |
| `sense` | string or `[col,row]` | **yes when `sense > 0`**, ignored otherwise | must be in `legalAnchors(seat)` | retry once, then `probe` |
| `guess` | array of strings | no | **6 entries max**, each **4 characters max**; entries that are not a cell name, or that the seat already knows, are **dropped silently** | never fatal |
| `say` | string | no | **80 characters**, single line | truncated |
| `notes` | string | no | **400 characters** | truncated |

Accepted `cell` / `sense` spellings: an algebraic string, case-insensitive, with surrounding
whitespace, an internal space (`"c 4"`) or trailing prose (`"c4 — cuts his chain"`) tolerated; or a
two-element integer array `[col, row]`, 0-based. Everything else is invalid.

`guess` is **never** a reason to reject a reply — a wrong or malformed guess costs the seat
nothing but its `guessAccuracy`. *Decided, with reason:* the guess exists to put the seat's belief
on the record for the overlay and the audit; making it fatal would trade the show for a fallback.

**Every truncation is on a rune boundary**, with `…` appended, via one shared
`cleanText(text, cap)` (babel's `cleanNotes`, generalised): `say` (80), `notes` (400), each `guess`
entry (4), the delivered prompt (4000), and any error text that reaches an event or the log (200).
A byte-boundary cut is exactly how a replay renders in a browser but fails a strict JSON parser;
`tests/test_replay.nim` pins it with multi-byte input at exactly the cap.

Newlines in `say` are replaced by spaces (it is drawn on one line in a reserved band).

### Replay bytes (self-sufficient)

`replayPayload` writes, and the wasm module reads, exactly:

```json
{"protocol": "fogboards.replay.v1",
 "names": ["Sprocket", "Gizmo"],
 "policyNames": ["fog-of-war-boards-cartographer", "Baseline (1)"],
 "config": {"mode": "dark-hex", "size": 5, "abrupt": true, "sense": 0,
            "first": 0, "seed": 118829, "maxPlies": 50, "sampled": true},
 "events": [ … the five kinds above … ],
 "results": { … the results object … }}
```

Names, policy names, the full config, the seed, the ply cap and every event are in the bytes; the
viewer re-derives every frame in the browser and contacts nothing but S3 for the file. There is no
`/client/replay` pod viewer declared anywhere.

---

## Viewer

### The four viewer files come from cogame-babel — all four, no mixture

`replay-viewer/config.nims`, the wasm entry `replay-viewer/fogboards_replay.nim`,
`replay-viewer/static_replay.js` and `replay-viewer/index.html` are **all four forked from
`Metta-AI/cogame-babel`** (commit `d55d999`) and from nothing else. This is not a stylistic
preference: babel's `config.nims` links with `-s MODULARIZE=1 -s EXPORT_NAME=BabelReplayModule`
and babel's `static_replay.js` bootstraps with `BabelReplayModule().then(…)`; splicing one
starter's shell onto another's link flags (an `onRuntimeInitialized` bootstrap against a
`MODULARIZE` build) leaves the factory uncalled, throws nothing, and hangs the viewer forever —
cogame-lantern, 2026-08-23.

The fork renames, and renames only:

- **`replay-viewer/config.nims`** — output `dist/fogboards_replay.js`,
  `EXPORT_NAME=FogReplayModule`, and
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_fog_load_replay,_fog_payload_ptr,_fog_payload_len,_fog_error_ptr,_fog_error_len`.
  Every other switch (`--mm:arc`, `--exceptions:goto`, `--define:noSignalHandler`,
  `-d:release`, `-d:useMalloc`, `-O2`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`,
  `ENVIRONMENT=web`, `EXPORTED_RUNTIME_METHODS=HEAPU8`) is kept byte-for-byte — the
  `useMalloc`/`ABORTING_MALLOC` pair is load-bearing and its comment travels with it.
- **`replay-viewer/fogboards_replay.nim`** — babel's `babel_replay.nim` with `bab_*` → `fog_*`. It
  parses the replay JSON, rebuilds `GameConfig` from `replay["config"]`
  (`mode, size, abrupt, sense, first, seed, maxPlies`, `sampled: true`) plus `replay["names"]`,
  runs `replayMatch`, and emits `{type, protocol, names, policyNames, config, events, results,
  states}` where `states[i]` is `boardStateJson` after `events[0..<i]`. It keeps babel's
  `emscripten_exit_with_live_runtime` epilogue verbatim.
- **`replay-viewer/static_replay.js`** — babel's file with `BabelReplayModule` → `FogReplayModule`,
  `_bab_*` → `_fog_*`, `BabelRenderer` → `FogRenderer`. `FETCH_TIMEOUT_MS = 20000`, the caption,
  the Retry button and the `{src:"coworld-replay", type}` parent bridge are kept.
- **`replay-viewer/index.html`** — babel's static page with the script list
  `chrome_common.js, renderer.js, fogboards_replay.js, static_replay.js`, the `<title>`, the
  `#wordmark` inner text (`BA<span>BEL</span>` → `FOG<span>BOARDS</span>`), and
  `BabelRenderer.bindFeedToggle` → `FogRenderer.bindFeedToggle`. **Nothing is removed.**

**Load signalling.** The shell sets **`data-replay-loaded="true"`** on `document.documentElement`
on its **first drawn frame**, and **`data-replay-error="<message>"`** on
`document.documentElement` on failure (removing the error attribute on a retry). One required
deviation from babel is named here: babel sets `data-replay-loaded` inside the renderer's ready
callback but posts the bridge `ready` from a double-`requestAnimationFrame` at the call site, so
`ready` can precede the first painted frame and an embedding page can sample an unpainted shell
(chorus `3c11c953`, 2026-08-24). Here `FogRenderer.attachReplay` takes an `onFirstFrame` callback,
sets `data-replay-loaded="true"` inside it, and `static_replay.js` posts `tell("ready")` **from
that callback**, after the attribute is set.

### Chrome provenance

- **`client/chrome.css`** — cogame-babel's `client/chrome.css` (443 lines) copied **byte-for-byte**.
  Not one starter rule is edited or deleted. The game's rules are **appended** below the last
  starter line under `/* ===== fog-of-war-boards game block ===== */`: the three-board layout, the
  fog hatch, the belief-board frames, the `say` band, the five beat-kind classes, the
  `--band` / `--hudscale` consumers, and the ≤ 640 px / ≤ 360 px media queries.
- **`client/chrome_common.js`** — the chrome half of cogame-babel's `client/renderer.js`, copied
  from the starter file (not retyped) as these contiguous regions of `d55d999`, in this order:
  **101–124** (`ellipsize`, `hexToRgb`, `shade`, `rgba`), **680–733** (`// ---- Names ----`
  through `clampName`: `isBaselineFiller`, `makeNameMap`, `applyNames`, `clampName`), **735–744**
  (`// ---- Event feed ----`, `roundBase`), **790–863** (`blockHead`, `renderFeed`, `escapeHtml`),
  **963–970** (`reasonLine`), **972–1027** (`updateEndscreen`), **1029–1048** (`bindFeedToggle`)
  and **1142–1222** (the scrubber comment and `buildScrub`). It exports `window.FogChrome`.

  **Exactly six copied lines/regions are edited**, and each is named here so a reviewer can find
  it — everything else in the file is copied bytes or appended at the end:

  | # | Starter line(s) | Edit |
  |---|---|---|
  | 1 | 791 (`blockHead`) | `"ROUND " + (block + 1)` → `"PLY " + (block + 1)` |
  | 2 | 827 (`renderFeed`) | `describeEvent(event, nameMap, ctx)` → `feedText(event, nameMap, ctx)`, injected once by `FogChrome.setFeedText(fn)` |
  | 3 | 829–836 (`renderFeed`) | the speak/pick notes sub-line becomes the attempt sub-line: the condition `event.kind === "speak" \|\| event.kind === "pick"` → `event.kind === "attempt"`, and the rendered string `… " notes: " …` → `… ": “" + say + "”"` |
  | 4 | 1179–1189 (`buildScrub`) | babel's marker-`div` loop → `markPlyBeat(container, event, i, events.length, onSeek)` for **every** event; `markPlyBeat` is appended at the end of the file |
  | 5 | 1005–1008 and 1020–1023 (`updateEndscreen`) | the four hard-coded `end-head` labels and the four `cell(...)` calls → one injected `endColumns(results)` returning `{heads:[…], cell(i)}`, injected by `FogChrome.setEndColumns(fn)` |
  | 6 | 966–967 (`reasonLine`) | `results.rounds` / `results.maxRounds` → `results.plies` / `results.maxPlies`, and the word `rounds` → `plies` |

  **Appended** at the end of `chrome_common.js`, in this order: `relayout()`, `markPlyBeat()`,
  `setFeedText()`, `setEndColumns()`, and the `window.FogChrome` export. **Nothing is renamed in
  place.**

  Babel's game-specific procs are **not** copied; their replacements live in the game block:
  the palette/geometry/scene drawing at 17–100 and 126–679, `spellTokens` (746–749),
  `describeEvent` (753–781), `endText` (783–788), `makeEffects` (865–900), `phaseText` (904–914),
  `matchHeader` (916–932), `updateScorebug` (934–961), `stateToView` (1052–1063), `attachLive`
  (1065–1140), `attachReplay` (1224–1311) and the `window.BabelRenderer` export (1313–1318).

- **`client/renderer.js`** — the game block. It draws the three boards and exports
  `window.FogRenderer = {attachLive, attachReplay, renderFeed, bindFeedToggle}`. It declares **no
  identifier already exported by `FogChrome`**, and the beat builder is named `markPlyBeat` and
  lives in the chrome, not the game block — a game-block `function markBeat` is hoisted over a
  chrome alias `var markBeat = C.markBeat` and silently turns every beat into an unlabelled div
  that never seeks (tandem, 2026-08-23). A CI check asserts the non-overlap (`## Tests`).

- **`client/replay_broadcast.html`** — cogame-babel's `client/replay.html`, copied byte-for-byte
  and renamed, **with a game block appended**; it is not a rewrite that reuses the starter's ids
  (cogame-gridlock, 2026-08-23). Served at `/client/replay`.
  - **Kept, unchanged:** `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`,
    `#statuschip`, `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`,
    `#grain`, `#endscreen`, `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`,
    `#feed`, `#loading`, and the `/replay` websocket bootstrap.
  - **Removed from the starter page: nothing.** No starter element is deleted from any of the four
    pages.
  - **Changed:** the `<title>` text, the `#wordmark` inner text
    (`BA<span>BEL</span>` → `FOG<span>BOARDS</span>`), and the `<script src>` list, which gains
    `/client/chrome_common.js` ahead of `/client/renderer.js`.
  - **Appended:** one `<script>` block at the end that registers the game's feed text and endcard
    columns with `FogChrome`. **No DOM node is inserted into the starter's markup** — the truth
    board and both belief boards are drawn as three viewports **inside the existing
    `canvas#table`**, which is precisely why nothing has to be spliced into `#board-wrap`.
  - `client/global.html` and `client/player.html` are copied the same way (byte-for-byte +
    wordmark/title text + the `chrome_common.js` script tag), because the certifier fetches both
    *before* the player pods start and neither may open the player socket.

- **Zoom: dropped.** Babel has no `#viewpanel`, and none is added. Every shipped board is fixed and
  small (3×3, 4×4, 5×5) and always fits the frame, so a zoom bar and a minimap would have nothing
  to do and would only steal height at 360 px. (Pin: `#viewpanel` is kept **only** when the board
  is larger than the frame.)

### Transport rules

- **`relayout()`** (in `chrome_common.js`) measures `#transport` and sets **`--band`** (its height
  in px) and **`--hudscale`** (`clamp(0.72, viewportWidth / 1280, 1)`) **on `:root`**. It runs on
  `load`, on `resize`, and on every feed toggle.
- **Nothing is ever overlaid in the transport band.** `#endscreen` is
  `position:absolute; top:0; bottom: var(--band);` so the endcard **stops exactly at `var(--band)`**
  and the scrubber and play button are always clickable.
- **Every seek dismisses the endcard**: `setIndex(next, jumped)` removes `.show` from `#endscreen`
  whenever `index < events.length`, and the scrub's `onSeek` always calls it.
- **Scrubber beats are clickable, labelled buttons**: `markPlyBeat` appends
  `<button type="button" class="beat-marker beat-<kind> …" aria-label="…" title="…">` for every
  recorded event, and clicking one seeks to that event. **CSS exists for every kind emitted** —
  `.beat-start`, `.beat-sense`, `.beat-attempt`, `.beat-win`, `.beat-end` — plus the modifier
  `.beat-attempt.occupied` (the amber discovery beat, taller) and the seat tints
  `.seat0` / `.seat1` on `sense`, `attempt` and `win` beats. `.beat-win` and `.beat-end` are the
  tall ones.

### Readouts — spectators see the true board **and** each seat's belief overlay

The single `canvas#table` is laid out as three viewports. Above 640 px: the **truth board** in the
centre at full size, flanked by seat 0's and seat 1's **belief boards** at 55 % scale. At and below
640 px: the truth board on top, and the two belief boards side by side beneath it at 40 % scale
(two 5×5 boards at ~150 px each plus a gutter fit inside 360 px).

- **Truth board.** The real position. Own stones as filled seat-coloured discs (Hex) or drawn X/O
  marks (tic-tac-toe). A cell holding a stone the **seat to move has not proven** is overlaid with
  the `fog_hatch.png` tile — so the fog on the truth board is literally what the mover cannot see.
  The `win` path is stroked in amber when it lands. In `recon-hex-5` the 2×2 sense window is drawn
  as an amber frame that sweeps to the anchor and holds 700 ms.
- **Belief boards**, one per seat, drawn from the sim's own knowledge sets — not from anything the
  model claimed:
  - own stones: solid seat colour;
  - **proven** opponent stones: solid opponent colour with a hard ring (this cell was *bought*);
  - **guessed** opponent cells (the seat's latest `guess`): opponent colour at 35 % with a dashed
    ring; on the ply it resolves, a correct guess gets an amber tick and a wrong one a ghost ✗;
  - **sensed empty** (`recon-hex-5`): a faint dot whose opacity decays with staleness —
    `max(0.15, 1 − (ply − sensedAt) / 8)` — so a belief going stale is visible as it fades;
  - untouched: blank paper.
  The gap between a belief board and the truth board is the show, and it is drawn side by side so a
  spectator sees it without being told.
- **Discovery flash.** An `attempt` whose `result` is `occupied` flashes that cell on all three
  boards for 900 ms and emits its own scrub beat. It is the single most watchable moment in the
  game and it gets its own colour, its own feed line and its own beat class.
- **Clock** (`#clock`): `DARK HEX 5×5 · PLY 14 / 50 · SPROCKET TO MOVE`, or
  `PHANTOM TIC-TAC-TOE · PLY 7 / 18 · FINAL`.
- **Scorebug** (`#scorebug`): one plate per seat — seat colour chip; `.plate-name` carrying the
  **policy name** (spectator side) with the anonymous alias as a small sub-label; `STONES 6`;
  **`TO CONNECT 3`** (the true `distToWin`, `LINE IN 2` in tic-tac-toe, `—` at 99) as the live
  tension readout; a **fog bar** = the share of the opponent's stones this seat has proven; and
  this ply's `say` in a **reserved band** sized from `MaxSayLen = 80` measured in the render font
  at the current `--hudscale`, so a full-cap line can never be laid out at a negative coordinate
  (cogchemists, 2026-08-24). `.plate-name` gets `flex: 1 1 auto; min-width: 3.2em` and its label
  is hidden under 640 px — the featured-match iframe on softmax.com is ~360 px wide and names
  otherwise collapse to "…".
- **Feed** (`#feed`): one block per ply — `PLY 14 · SPROCKET`, then (recon) `senses b3 — c3 is
  GIZMO's, the rest empty`, then `plays c4 — placed` or `plays c4 — OCCUPIED: Gizmo is already
  there`, then the quoted `say`, then `guesses d3, d4` with per-cell ✔ / ✘ once resolved. The
  `win` line reads `Sprocket connects a3–e3` / `Gizmo takes the diagonal a1–b2–c3`. The end block
  names the reason and the ending in words.
- **Endcard** (`#endscreen`): the verdict (`SPROCKET CONNECTS` / `ALL LEVEL`), a reason line
  (`complete — connection` / `deadline — stopped after 21 of 50 plies, scored on distance`), and
  one row per seat with `score`, `stones`, `probes`, `discovered` and `guess accuracy` — supplied
  by the injected `endColumns` (chrome edit #5).
- **Legibility at 360 px is a requirement.** At 360 px the feed collapses behind its toggle, the
  scorebug drops to two stacked plates, the belief boards drop to 40 %, cell names stay algebraic
  (`c3`), and the clock drops the mode word. The renderer fixture in `## Tests` checks 360 / 640 /
  1280 px.

### Art (real, not placeholders)

- `data/font.ttf` + `data/FONT_LICENSE.txt` — copied from babel (Rajdhani).
- `data/arena_floor.png` — copied byte-for-byte from babel (MIT, originally coworld-ctf); the table
  surface under the three boards.
- `data/soldier_red_front.png`, `data/soldier_blue_front.png` — copied from babel; the two seat
  avatars in the scorebug plates.
- **`data/fog_hatch.png`** — new, authored for this repo: a 64×64 seamlessly tileable ink
  cross-hatch in `--ink` on transparent, drawn over any truth-board cell the mover has not proven.
- **`data/lens.png`** — new, authored for this repo: a 96×96 ink-and-amber reconnaissance lens,
  drawn at the centre of the sense window while it holds.

Stones, the hex tiling, the X/O marks, the grid and the win path are drawn on canvas (not sprites)
so they stay crisp at every `--hudscale`.

The build hook **`tools/build_replay_viewer.sh`** (a fork of babel's, with the `mkdir -p` fix from
ecos 2026-08-23 so it works on a fresh CI checkout where the parent directory does not exist)
copies into the bundle: `fogboards_replay.js`, `fogboards_replay.wasm`,
`replay-viewer/index.html`, `replay-viewer/static_replay.js`, `client/renderer.js`,
`client/chrome_common.js`, `client/chrome.css`, and
`assets/{arena_floor.png, soldier_red_front.png, soldier_blue_front.png, fog_hatch.png, lens.png,
font.ttf}`. It keeps babel's final `grep -q 'data-replay' static_replay.js` guard and adds
`grep -q 'data-replay-loaded' renderer.js`. It is committed mode `100755`.

---

## Packaging

- **`compose.yaml`** — one service:

  ```yaml
  services:
    fog-of-war-boards:
      image: coworld-fog-of-war-boards:latest
      platform: linux/amd64
      build: {context: ., network: host}
  ```

  The manifest image placeholder is derived from the **compose service name**, so it is
  `{{FOG_OF_WAR_BOARDS_IMAGE}}` (service name uppercased, `-` → `_`). `{{GAME_IMAGE}}` is not a
  thing (lantern 0.1.0, 2026-08-23).

- **`Dockerfile`** / **`Dockerfile.replay-viewer`** — babel's, with the binary names changed to
  `/bin/fog-of-war-boards` and `/bin/fog-of-war-boards-player`.

- **`coworld_manifest_template.json`** — babel's shape, updated to the `coworld` 0.1.42 upload
  contract: `$schema` present; ≥ 3 top-level `tags`
  (`["imperfect-information","board-game","zero-sum","two-player","turn-based","llm-driven",
  "openspiel-port","hex","tic-tac-toe","belief-tracking"]`);
  `game.name = "fog-of-war-boards"` — **the secret namespace is `game.name`**, so
  `ANTHROPIC_API_KEY_URI = "secret://coworld/fog-of-war-boards/anthropic_api_key"` in the game
  runnable's `env` (without it every hosted episode silently plays scripted — hive, 2026-08-23);
  `game.description` present and `game.tags` **absent** (tags are top-level only);
  `game.owner = "daveey@gmail.com"`;
  `game.runnable = {"type":"game","image":"{{FOG_OF_WAR_BOARDS_IMAGE}}",
  "run":["/bin/fog-of-war-boards"],"env":{…},"source_url":…}`;
  **`game.replay_viewer = {"bundle": "static-replay-viewer"}`** (inside `game`, never top-level);
  no top-level `version`; no `game.display_name`; `episode_timeout_minutes: 20` top-level.

- **`game.config_schema`** — a real JSON Schema, `additionalProperties: false`,
  `required: ["tokens","players"]`. **Every array property carries `minItems`/`maxItems`**:
  `tokens` and `players` both `minItems 2, maxItems 2`. Scalar properties: `num_agents`
  (integer, minimum 2, maximum 2), `mode` (`enum ["phantom-ttt","dark-hex"]`, default
  `"dark-hex"`), `size` (3..7, default 5), `abrupt` (boolean, default `true`), `sense` (0..3,
  default 0), `first` (0..1, default 0), `maxPlies` (4..120, default 50), `seed` (integer),
  `episodeTimeoutSeconds` (60..6000, default 1200), `plySpacingSeconds` (0..60, default 0),
  `turnDelayMs` (0..10000, default 250), `model` (string, default `"claude-sonnet-5"`),
  `maxOutputTokens` (64..2000, default 900), `llmTimeoutSeconds` (5..300, default 30),
  `player_connect_timeout_seconds` (number ≥ 0, default 180).
  **No `game_config` anywhere — variant or fixture — contains a literal `tokens` array**; the
  runner injects it and matriculate rejects "runner-managed tokens" if one is present
  (cogame-knights-archers, 2026-08-26). `config_schema` still *requires* `tokens`.

- **`game.results_schema`** — `additionalProperties: false`, every field of `results` from
  `## The game` required: `names`, `scores`, `outcome`, `stones`, `probes`, `discovered`,
  `guessesMade`, `guessAccuracy`, `distToWin`, `fallbacks`, `plies`, `maxPlies`, `mode`, `size`,
  `abrupt`, `sense`, `ending`, `reason`. Every array is `minItems 2, maxItems 2`; `scores` items
  are numbers in −1..1; `reason` is `enum ["complete","deadline"]`; `ending` is
  `enum ["connection","line","board-full","ply-cap","wall-clock"]`.

- **`game.protocols`** — **both** keys, each a `{"type":"text","value":"…"}` object (bare strings
  are a platform-side validation error the repo CI does not catch — cogame-garble 0.1.0,
  2026-08-24): `player` = the `fogboards.player.v1` text from `## Server, player, protocol`,
  including "a policy is just a prompt: reuse the published player runnable with `PLAYER_PROMPT`,
  or `PLAYER_SCRIPTED=probe|sweep` for a baseline"; `global` = the `/global` snapshot shape and the
  three client pages.

- **`game.docs`** — `readme` = `{"type":"text","value":…}` (what the game is, the fog rule, how to
  field a policy) and `pages` =
  `[{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…}}]` carrying the
  numbered resolution order, the coordinate scheme, the abrupt/non-abrupt distinction, the
  `distToWin` definition, the scoring formula, the ending table, and the note that `recon-hex-5` is
  an original variant carrying RBC's sense loop rather than a port of OpenSpiel `rbc`.

- **Bundled players** — top-level `player[]`, two entries, each with `id` / `type` / `name` /
  `description` / `image` / `run` / `source_url` and
  `resources: {requests:{cpu:"100m",memory:"64Mi"}, limits:{cpu:"1"}}` (the bundled minimum for
  `cpu` is `"1"`; `500m` is rejected at upload — cogame-pistonball 0.1.1, 2026-08-26):
  - `fog-of-war-boards-player` — the prompt player (no `PLAYER_SCRIPTED`).
  - `fog-of-war-boards-scripted` — `env: {"PLAYER_SCRIPTED": "probe"}`.

- **`variants[]` — exactly four. `num_agents` lives inside each variant's `game_config` and never
  at the variant's top level** (`CoworldVariant` is `additionalProperties: false` and the platform
  reads only `game_config.num_agents` — cogame-goofspiel-oshi-zumo 0.1.0, 2026-08-26). Every
  variant carries a `description`.

  | `id` | `name` | `game_config.num_agents` | `game_config` |
  |---|---|---|---|
  | `phantom-ttt-3` | Phantom Tic-Tac-Toe — 3×3 | **2** | `{"mode":"phantom-ttt","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":3,"abrupt":false,"sense":0,"first":0,"maxPlies":18,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |
  | `dark-hex-4` | Dark Hex — 4×4 | **2** | `{"mode":"dark-hex","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":4,"abrupt":false,"sense":0,"first":0,"maxPlies":32,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |
  | `dark-hex-5` | Abrupt Dark Hex — 5×5 | **2** | `{"mode":"dark-hex","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":5,"abrupt":true,"sense":0,"first":0,"maxPlies":50,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |
  | `recon-hex-5` | Reconnaissance Dark Hex — 5×5 | **2** | `{"mode":"dark-hex","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":5,"abrupt":true,"sense":2,"first":0,"maxPlies":50,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |

- **`certification`** — the `dark-hex-5` variant. *Decided, with reason:* it produces the most
  events of any variant under all-scripted play (~30 attempts), which is what keeps the derived
  smoke replay longer than the viewer soak window (§`## Tests`), and its abrupt rule exercises the
  turn-transfer branch that the non-abrupt variants do not.

  ```json
  {"game_config": {"mode": "dark-hex",
                   "players": [{"name": "Sprocket"}, {"name": "Gizmo"}],
                   "num_agents": 2, "size": 5, "abrupt": true, "sense": 0,
                   "first": 0, "maxPlies": 50, "seed": 23,
                   "turnDelayMs": 0, "player_connect_timeout_seconds": 180},
   "players": [{"player_id": "fog-of-war-boards-player"},
               {"player_id": "fog-of-war-boards-scripted"}]}
  ```

  Both declared runnables occupy a slot — a fixture that seats only one fails cert
  `players_missing` (raid 0.1.2 → 0.1.3, 2026-08-23). `num_agents = 2` here and **2** in all four
  variants; **`<SEATS>` in `tools/ci/docker_smoke.sh` is `2`**, matching the fixture it drives.

- **`.github/workflows/`** — `ci.yml`, `coworld-release.yml` and `coworld-submit.yml` from
  `coworld-builder/templates/`, with `SLUG=fog-of-war-boards`,
  `IMAGE=coworld-fog-of-war-boards`, `<SEATS>=2`. The release workflow's certify step passes
  `--timeout-seconds 300`, its `secret put` step reads the namespace from the manifest's
  `game.name`, and it keeps the load-bearing step order
  build → certify → **upload-policies** → upload-coworld → secret put.

- **`tools/ci/policies.json`** — the four policies from `## Decisions`; champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` so it is uploaded while daveey-1 is the
  active player. Player-side Bedrock is **not** used (every decision is server-side), so no
  `USE_BEDROCK` is set on the policies; the *game* runnable's `env` carries
  `ANTHROPIC_API_KEY_URI`, which is the thing that must be present or every hosted episode silently
  plays scripted.

- **Repo** — created public: `gh repo create Metta-AI/cogame-fog-of-war-boards --public
  --description "Kriegspiel's fog on boards cogs already know: Phantom Tic-Tac-Toe and Dark Hex,
  where you discover the enemy only by trying to play on him."` Public is a certification
  prerequisite (`source-resolves` 404s on private).

---

## Tests

Everything below runs in `ci.yml`; the sandbox has no docker, nim, emsdk or browser, so CI is the
only harness. `NIM_TESTS` is left unset — every `tests/*.nim` runs in both debug and `-d:release`.

**`tests/test_sim.nim` — the rules.**

1. **Coordinates round-trip**: `cellIndex(cellName(i)) == i` for every cell of every shipped size;
   `a1` is `(row 0, col 0)`; `e5` on a 5×5 is `(row 4, col 4)`; an off-board name raises.
2. **Hex neighbourhood**: `c3` on a 5×5 has exactly the six neighbours `b3, d3, c2, c4, b4, d2`;
   corner `a1` has exactly `b1, a2`; the relation is symmetric for every cell pair.
3. **Hex determinacy**: over 300 seeded random fills of a 5×5 board, **exactly one** seat has a
   winning connection — never zero, never both.
4. **Placement and collision**: an attempt on an empty cell places and sets `result == "placed"`;
   on an opponent cell it places nothing, sets `result == "occupied"`, adds the cell to
   `known[mover]` and increments `probes[mover]`.
5. **Legality**: attempting one's own stone, a cell already in `known[seat]`, or an off-board cell
   **raises**; `legalAttempts(seat)` never contains any of the three; `|legalAttempts(seat)|`
   strictly decreases on every ply.
6. **Turn transfer**: with `abrupt == false` a collision leaves `mover` unchanged; with
   `abrupt == true` it flips; a placement always flips.
7. **Termination bound**: over 300 seeded episodes × all four variants × both baselines, every
   episode ends with `plies ≤ maxPlies`, and `maxPlies == 2 × size × size` covers it — no episode
   ever reaches `ply-cap` in the Hex variants.
8. **Endings**: `connection` and `line` fire on the placing ply and name the right seat and path;
   `board-full` fires on a filled 3×3 with no line; `ply-cap` fires exactly at `maxPlies` on a
   contrived board; `wall-clock` via `endEarly`.
9. **`distToWin`**: 99 when the opponent has cut every route; 0 the moment a connection exists;
   monotone non-increasing for the seat that just placed on its own shortest path; on tic-tac-toe,
   `min(3 − own marks)` over live lines and 99 when every line is dead.
10. **Scoring**: `scores` sums to 0 (exactly) in 300 seeded episodes across all four variants;
    `+1` iff `ending ∈ {connection, line}` for that seat or it had the strictly lower true
    `distToWin`; a draw gives `[0, 0]` and only ever on `board-full`, `ply-cap` or `wall-clock`.
11. **Sense**: `applySense` reveals exactly the `sense × sense` block truthfully; opponent
    knowledge from a sense is permanent, `sensedEmptyAt` is timestamped and is **not** treated as
    knowledge of occupancy; an anchor outside `legalAnchors` raises; with `sense == 0` no `sense`
    event is ever emitted.
12. **Redaction**: `believedBoard(sim, seat)` contains no opponent stone the seat has not proven,
    for every prefix of 300 seeded episodes — the single test that proves the fog is real.
13. **Every variant's and the cert fixture's `game_config` constructs a `Sim`** (cogame-collab-cooking
    0.1.1, 2026-08-25 — a fixture-only test hid a defect that killed every league episode).

**`tests/test_bot.nim` — the scripted baselines (bounded orders / legality).**

14. Over 200 seeded episodes × all four variants × both baselines: **every** attempt a baseline
    produces is in `legalAttempts(seat)` at the moment it is produced, **every** sense anchor is in
    `legalAnchors(seat)`, no baseline ever reads `sim.board` outside its own believed view, and
    every episode terminates.
15. `probe` beats a seeded uniform-random legal attacker over 200 `dark-hex-5` episodes (mean score
    > 0), so the fillers are a real opponent rather than noise.
16. `probe` and `sweep` disagree on at least 30 % of plies — two fillers that play the same game
    are one filler.
17. The scripted-only cert fixture (`dark-hex-5`, 2 seats, `turnDelayMs = 0`) completes in **under
    50 s** of wall clock, pinning it inside `coworld certify`'s 60 s default (cogame-commons-family
    0.1.0, 2026-08-24).

**`tests/test_replay.nim` — record → re-derive, and the bytes.**

18. For **every** end reason/ending pair — `complete/connection`, `complete/line`,
    `complete/board-full`, `complete/ply-cap`, `deadline/wall-clock` — record an episode, run
    `replayMatch` over its events, and assert every frame's `boardStateJson` is identical to the
    live one. A wall-clock stop must re-derive because `settle` is the same proc on both paths
    (particle-worlds `13c66d7`, 2026-08-26).
19. `replayMatch` **raises** when a recorded `attempt.result`, `win.seat`, `win.how` or `win.path`
    disagrees with the seeded re-derivation.
20. **Strict UTF-8**: build an episode whose every `say` and `notes` is a multi-byte string at
    exactly the cap (80 / 400 runes of `日` plus an emoji), serialise the replay, and assert
    `validateUtf8(bytes) == -1` and that a strict `parseJson` round-trips it. Rune-boundary
    truncation, not byte truncation.
21. The replay payload contains `protocol`, `names`, `policyNames`, `config.mode`, `config.size`,
    `config.abrupt`, `config.sense`, `config.first`, `config.seed`, `config.maxPlies`, every event
    and `results` — the fields the viewer needs, asserted by key.

**`tests/test_manifest.nim` — packaging invariants, parsed from the template.**

22. `num_agents` is present, a positive integer, equal to `2`, and equal to `len(players)` in **all
    four** variants and in `certification.game_config`; **no variant carries `num_agents` at its
    top level**.
23. No `game_config` anywhere contains `tokens`; `config_schema` still requires it; every array
    property in `config_schema` and `results_schema` declares `minItems` and `maxItems`.
24. `game.protocols.player`, `game.protocols.global`, `game.docs.readme` and every
    `docs.pages[].content` are `{"type":"text","value":…}` objects; `game.description` exists;
    `game.tags` does not; there is no top-level `version` and no `game.display_name`;
    `game.replay_viewer.bundle == "static-replay-viewer"`; every bundled player's
    `resources.limits.cpu == "1"`; the `ANTHROPIC_API_KEY_URI` namespace equals `game.name`.
25. Every `player_id` in `certification.players` is a declared `player[].id`, and every declared
    `player[].id` occupies at least one certification slot.

**`tools/ci/docker_smoke.sh` (the `docker-smoke` job) — end to end.**

26. Builds the production image, starts one game container and **2** player containers on a
    per-run network with the certification fixture, and asserts: the game exits 0; `results.json`
    is written and validates against `results_schema`; the replay is written and **parses as strict
    JSON**; `SMOKE_SEATS=2` agrees with `certification.game_config.num_agents`; and **every player
    container's exit code is 0** (raid 0.1.4 — cert checks this, the stock starter smoke did not).
    It runs with **no** `ANTHROPIC_API_KEY`, so the whole scripted path is exercised. The replay is
    copied to `dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.

**`ci.yml` job `wasm-viewer` — the bundle is executed, not merely built.**

27. Asserts `tools/build_replay_viewer.sh` exists and is `os.X_OK`; asserts
    `tools/ci/viewer_smoke.mjs` is present; builds the bundle; asserts `index.html` and a non-empty
    `.wasm` exist. Then, `needs: docker-smoke`, it downloads the `smoke-replay` artifact and runs

    ```
    node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
      --replay dist/smoke/replay.json --timeout 90 --soak 10 --strict-text-bounds
    ```

    against **the replay `docker-smoke` produced** — the only replay in CI known to be current
    bytes. It requires `loaded: true` (via `data-replay-loaded="true"`), three differing scrub
    readouts, and `canvas_text.never_inside == 0`. `--soak 10` catches a viewer that loads and then
    throws mid-playback (cogball 0.1.4); the smoke replay is long enough for it: the `dark-hex-5`
    fixture emits ≈ 33 events (1 `start` + ~30 `attempt` + 1 `win` + 1 `end`) at the renderer's
    dwell of 700 ms (placed) / 1100 ms (occupied) / 1500 ms (`win`, `end`) ≈ **27 s of playback >
    10 s of soak** (ecos, 2026-08-23 — a replay shorter than the soak reads as frozen). The boards
    are fixed, so `--strict-text-bounds` stays on.

28. **Renderer fixture step** (`tools/ci/renderer_fixture.html`, its own
    `viewer_smoke.mjs --url … --strict-text-bounds` run): CI replays carry **zero LLM text** —
    `docker_smoke.sh` runs without a key and the scripted baselines emit no `say`, `notes` or
    `guess` — so nothing that plays a CI replay ever exercises the say band, the quoted feed lines
    or the guessed-cell overlay. The fixture loads the **shipped**
    `dist/static-replay-viewer/index.html` in an iframe, shims only the wasm entry, feeds it a
    synthetic payload with a full-cap 80-rune `say` on both seats, a full 6-entry `guess` on every
    ply and the longest plausible policy names, and drives the page's own text path at **360, 640
    and 1280 px** (particle-worlds `46cf69d`, 2026-08-26 — a fixture that re-implements the drawing
    gates nothing).

29. **Chrome scope check** (`tools/ci/chrome_scope_check.mjs`, same job): asserts that no
    identifier exported by `client/chrome_common.js` is re-declared as a top-level `function` or
    `var` in `client/renderer.js` (tandem, 2026-08-23), that `client/renderer.js` declares no
    `markBeat`, and that `client/chrome_common.js` still contains the copied-region markers listed
    in §Chrome provenance, so a future "tidy-up" that rewrites the chrome fails loudly.

---

## Out of scope (v1)

- **Kriegspiel and Reconnaissance Blind Chess.** Both need a complete chess engine, a second
  referee vocabulary (`illegal`, `capture on e5`, `check — rank`), piece art and — for RBC — a
  sense phase over an 8×8 board with a different action space. They are a second sim module and a
  second viewer, not a parameterisation of this one. `recon-hex-5` carries RBC's *sense-then-move
  loop* and says so; it is not a port of `rbc`.
- **Phantom Go.** Captures make a seat's knowledge non-monotone, which changes what a belief
  overlay means, and the engine needs liberties, suicide, positional superko and Tromp-Taylor
  scoring. Deliberately excluded so the one shipped overlay has one meaning.
- **Board sizes and rules other than the four shipped variants.** The sim tolerates `size` 3..7,
  `sense` 0..3 and either collision rule, but no manifest variant declares anything else, so the
  ladder never schedules it. In particular: Hex on 7×7 or 11×11, tic-tac-toe on 4×4, the abrupt
  phantom tic-tac-toe variant (OpenSpiel `abrupt_phantom_ttt`), and a 3×3 sense window.
- **The swap (pie) rule** and randomised first move. Seat 0 always opens; the league's own round
  robin, which seats each policy in both slots, is what balances the opening advantage.
- **Scoring anything but the outcome.** `probes`, `discovered`, `guessesMade`, `guessAccuracy` and
  `distToWin` are reported in `results`, drawn in the viewer and never enter `scores`; no policy
  can farm them.
- **The `guess` field as a game action.** A guess never changes the board, never costs a ply and
  never rejects a reply; it exists for the overlay and the audit only.
- **Any inter-seat channel.** Seats never exchange text; `say` is spectator-facing and is not shown
  to the other seat; `notes` are fed back only to their author.
- **RL / vector policies.** Policies are prompts or the two named scripted baselines; there is no
  observation tensor and no action-space export.
- **A live spectator theatre beyond `/client/global`**, replay editing, highlight clipping, and any
  replay-viewer pod. Replays are the static wasm bundle, always.
- **Replay protocol migration.** The viewer reads `fogboards.replay.v1` and nothing else; a future
  version bump adds a reader, it does not silently reinterpret old bytes.
