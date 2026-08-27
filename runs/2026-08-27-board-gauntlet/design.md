# Board Gauntlet — design note (`docs/plans/2026-08-27-board-gauntlet-design.md`, `Metta-AI/cogame-board-gauntlet`, v1)

This coworld is forked from **`Metta-AI/cogame-babel`** (read at commit `d55d999`, "0.1.4: static
viewer announces loading/ready/error to its host"), the current head of the
parley → cosino → focus → babel lineage. Babel is the starter because this game's shape is babel's
shape: a **board, turn-based, native rules, decisions that are a short structured reply, and a
policy that is just a prompt** the game server sends to Claude on the acting seat's behalf — the
first row of the starter table. **Every convention there holds here unless this note says
otherwise**: the `bitworld/runtime` contract, the mummy HTTP/WS server, the
`types.nim` / `sim.nim` / `llm.nim` / `server.nim` split, `tableNames`' seeded anonymous cog
aliases, `PlayBudgetFraction = 0.6`, the `finishEpisode` artifact order (final frames → results →
replay), `replayMatch` re-derivation, the emscripten `MODULARIZE` / `EXPORT_NAME` viewer bootstrap,
and the Ink & Print broadcast chrome. Where this note deviates from babel it says so and says why.
**No file in this repo comes from any starter other than cogame-babel.** There is no OpenSpiel
dependency, no external engine and no reference bot: every rule below is re-stated in full here and
implemented natively in Nim.

### Source idea (verbatim)

> OS Board Gauntlet — Hex, Quoridor, Amazons, Breakthrough, Connect Four, Go 9×9: a rotating
> perfect-information ladder
>
> Port of OpenSpiel / PettingZoo classic perfect-information boards as one coworld with a weekly
> game rotation: Hex, Havannah, Y, TwixT (connection games), Quoridor (2-4p wall-placing maze
> race), Amazons, Breakthrough, Lines of Action, Clobber, Pentago, Connect Four, Ultimate
> Tic-Tac-Toe, Go 9×9, Othello. Deterministic, two-player, fully observed — the least 'social'
> family on this list, but the one where search-based and LLM policies diverge most sharply, and
> where game rotation tests generality rather than a single opening book.
>
> Seats: 2 (Quoridor up to 4)
> Motive: zero-sum, perfect information
> Policy interface: move per turn; time control per move is the lever (fast = LLM-hostile, slow =
> search-hostile)
> Fills gap: pure game-playing strength ladder; Cogherence is about coherence, not this
> Integrity (anti-collusion): 2-player zero-sum; rotation announced per round; anonymous aliases.
>
> Replay plan (watchability): standard board viewer; eval bar from a reference engine where one
> exists.
>
> Source: OpenSpiel hex, havannah, y, twixt, quoridor, amazons, breakthrough, lines_of_action,
> clobber, pentago, connect_four, ultimate_tic_tac_toe, go, othello.

---

## The game

Two cogs, one board, no dice and nothing hidden. Both seats see the whole position, the whole move
history and the whole legal-move set; the only thing either of them cannot see is what the other
one is *thinking*. What varies is the board itself: an episode plays **one of four classic games**,
and which one is drawn deterministically from the episode seed and announced to both seats before
their first move. A policy that only knows one opening book scores in one episode of four.

`num_agents` is **2** — a single unambiguous number, in every manifest variant's `game_config`, in
`certification.game_config`, and therefore `<SEATS>` = `2` in `tools/ci/docker_smoke.sh`. It is 2
because every shipped game is two-sided and zero-sum (Hex has exactly two pairs of edges, Connect
Four two disc colours, Breakthrough two armies, Quoridor two pawns racing to opposite rows), and
the idea pins it at 2. The idea's "Quoridor up to 4" is **out of scope (v1)**: a 4-seat variant is
not zero-sum between pairs, needs a different scoring vector and a different anti-collusion story,
and it would make `num_agents` a range — which the ladder and CI both reject.

### The four games that ship, and why these four

The selection rule is one property, stated once and applied to every candidate in the idea's list:
**the legal-move set at every position must be (a) computable by a cheap predicate with no search
and no external engine, and (b) short enough to print in full in the acting seat's prompt.** That
is what lets one sim module, one validator, one prompt builder and one viewer serve all four games
honestly, and it is what makes the "precompute the legal choice set in the observation" fix
(escrow 0.1.3, 2026-08-23) available in every game rather than in some of them.

| `game` | Board | Max legal moves at a position | `maxPlies` | `num_agents` |
|---|---|---|---|---|
| `connect-four` | 7 files × 6 ranks | 7 | 42 | **2** |
| `breakthrough` | 6 × 6, 12 pieces a side | ~48 | 80 | **2** |
| `hex` | 7 × 7 rhombus | 49 | 49 | **2** |
| `quoridor` | 9 × 9, 10 walls a side | 133 | 80 | **2** |

Everything else the idea names is in `## Out of scope (v1)` with its reason; the two headline
exclusions are worth stating here because they are the ones a reader will ask about:

- **Amazons** fails (b). The opening position of 10×10 Amazons has roughly 2 000 legal
  (move, arrow) pairs. There is no honest way to print that list in a prompt, and without the
  printed list the seat guesses and falls back.
- **Go 9×9** fails (a) in the only sense that matters here: legality is cheap, but *the game* is
  not — it needs liberties, suicide, positional superko, pass handling and Tromp-Taylor scoring
  with dead-stone resolution, which is a second sim module wearing this one's clothes, and it is
  the game where a prompt-driven policy is furthest from competent. It is named in Out of scope
  and it is not faked.

The four that ship span four different shapes on purpose — an alignment/drop game, a capture race,
a connection game and a path-blocking race — because "rotation tests generality rather than a
single opening book" is the idea's whole point.

### The rotation rule (deterministic, announced, recorded)

`config.game` is one of `rotate`, `connect-four`, `breakthrough`, `hex`, `quoridor`.

1. The **rotation order** is the fixed list `["connect-four", "breakthrough", "hex", "quoridor"]`,
   indices 0..3.
2. If `config.seed == 0` (unpinned), the **server** draws a seed once, before `initSim`, as
   `seed = int(epochTime() * 1000) xor getCurrentProcessId()` clamped to `1 .. 1_000_000_000`, echoes
   it, and writes it into the config. Every replay therefore carries a concrete seed and re-derives
   exactly. (Without this the manifest's "omit for a fresh seed" would silently mean "always seed 0",
   and the rotation would always pick `connect-four`.)
3. `sampleEpisode(config)` — idempotent, and skipped when `config.sampled` is already true —
   resolves the rotation: `config.game = RotationOrder[((seed mod 4) + 4) mod 4]`, and sets
   `config.rotated = true` so the viewer can say `GAUNTLET → HEX` rather than just `HEX`.
4. The **resolved** game id is what lands in the replay's `config`, in `results.game`, in the
   player `welcome` frame and in the first line of both seats' prompts. Nothing about the rotation
   is hidden from a seat, and nothing about it needs re-deriving from the seed in the viewer.

*Decided, with reason:* the idea says "weekly game rotation" and "rotation announced per round".
A cloud ladder has no week; the honest translation is **per episode, drawn from the seed, announced
to both seats before move one, and recorded in the bytes**. A hidden rotation would just be a
guessing game about which rules apply, which is not what the idea is testing.

### Coordinates, shared by all four games

Cells are **algebraic**: files `a`, `b`, `c`, … left to right; ranks `1`, `2`, `3`, … bottom to top.
`a1` is bottom-left. Internally a cell is `(row, col)`, `row` 0-based from rank 1 and `col` 0-based
from file `a`; `cellName(row, col)` and `cellIndex(name)` are the only two places the two
representations meet. **Nothing spectator-facing ever shows an internal index** — the feed says
`plays d4`, never `plays 24`, and Connect Four says `drops into d` and shows the disc landing on
`d3`.

**Seat 0 always moves first** (`config.first = 0`, recorded in the replay). *Decided, with reason:*
the first-move advantage is real in three of these four games, and the league's round robin seats
each policy in both slots, which balances it without a swap/pie rule (pie is out of scope).

### Rules — `connect-four` (7 files × 6 ranks)

Seat 0 plays **red** discs, seat 1 **blue**.

1. A **move** is a file letter `a`..`g`. It is legal iff that file has at least one empty cell.
2. Applying it drops the mover's disc into the **lowest empty cell** of that file.
3. The mover **wins immediately** if the placed disc completes a line of **four** of its own discs
   horizontally, vertically or on either diagonal. The four cells are the `win` event's `path`.
4. If after the move every cell is occupied and nobody has four in a row, the game is a **draw**
   (`ending = "board-full"`).
5. There is no other way for this game to end other than the ply cap or the wall clock.

### Rules — `breakthrough` (6 × 6)

Seat 0 is **red**, with 12 pieces filling ranks 1 and 2; seat 1 is **blue**, with 12 pieces filling
ranks 5 and 6. Red advances toward rank 6, blue toward rank 1. "Forward" always means *toward the
opponent's home rank*.

1. A **move** is `<from><to>`, e.g. `b2-c3`. `from` must hold one of the mover's pieces; `to` must
   be one rank forward of `from` and on the same file or one file to either side.
2. A straight-forward move is legal **only onto an empty cell**. There is no straight capture.
3. A diagonal-forward move is legal onto an empty cell **or** onto a cell holding an opponent piece,
   which is then **removed** (the event's `capture` field names that cell).
4. The mover **wins immediately** if the moved piece lands on the opponent's home rank (rank 6 for
   seat 0, rank 1 for seat 1) — `ending = "home-rank"`.
5. The mover **wins immediately** if that move removed the opponent's last piece —
   `ending = "no-pieces"`.
6. If the seat now to move has **no legal move**, it loses — `ending = "no-moves"`. (Reachable in
   Breakthrough: a fully blocked army has no moves.)
7. There are no draws by rule; the ply cap and the wall clock adjudicate (below). There is no
   repetition rule — see Out of scope.

### Rules — `hex` (7 × 7 rhombus)

Seat 0 is **red**, seat 1 **blue**.

1. Cell `(r, c)` is adjacent to `(r, c−1)`, `(r, c+1)`, `(r−1, c)`, `(r+1, c)`, `(r−1, c+1)` and
   `(r+1, c−1)` — the standard rhombus neighbourhood. So `c4` touches `b4, d4, c3, c5, b5, d3`, and
   the corner `a1` touches only `b1, a2`.
2. A **move** is a cell name. It is legal iff the cell is empty.
3. Applying it places the mover's stone there; stones never move and are never removed.
4. **Seat 0 connects the left file (`a`) to the right file (`g`); seat 1 connects the bottom rank
   (`1`) to the top rank (`7`).** The mover wins immediately when its own stones form an unbroken
   adjacency chain between its two edges — `ending = "connection"`, the chain in the `win` event's
   `path`.
5. Hex has **no draws**: a full board contains exactly one winning connection, so a filled board is
   always already a win. There is no swap (pie) rule in v1.

### Rules — `quoridor` (9 × 9, 10 walls a side)

Seat 0's pawn starts on `e1` and must reach **rank 9**; seat 1's pawn starts on `e9` and must reach
**rank 1**. Each seat holds **10 walls**.

1. A **move** is either a **pawn move** — the destination cell, e.g. `e2` — or a **wall placement**,
   `<anchor><h|v>` with `anchor` in `a1`..`h8`, e.g. `e3h`.
2. A wall's anchor names the lattice point at the **top-right corner of the anchor cell**: `xNh`
   (horizontal) blocks the two vertical steps `(x,N)↔(x,N+1)` and `(x+1,N)↔(x+1,N+1)`; `xNv`
   (vertical) blocks the two horizontal steps `(x,N)↔(x+1,N)` and `(x,N+1)↔(x+1,N+1)`.
3. A wall placement is legal iff **all** of: the mover has walls left; **no wall of either
   orientation already sits on that anchor** (this is what forbids both crossings and the
   half-overlap of two same-orientation walls); **neither of the two steps it blocks is already
   blocked**; and, after the placement, **both pawns still have some path to their own goal rank**
   (breadth-first search over cells, wall-blocked steps removed, pawns ignored).
4. A pawn move is legal to an orthogonally adjacent cell when that step is not wall-blocked and the
   cell is empty. If the adjacent cell in direction *d* holds the **opponent** pawn:
   a. the mover may **jump straight over** to the next cell in direction *d*, if that cell is on the
      board and the step from the opponent's cell in direction *d* is not wall-blocked;
   b. if and only if that straight jump is unavailable (off board or wall-blocked), the mover may
      instead move to either cell **diagonally adjacent to the opponent pawn, perpendicular to
      *d***, provided that step from the opponent's cell is not wall-blocked and the cell is on the
      board.
5. The mover **wins immediately** on moving its pawn onto any cell of its own goal rank —
   `ending = "goal-row"`.
6. Rule 3's path invariant guarantees a pawn always has at least one legal move, so `no-moves` is
   unreachable here; there are no draws by rule, and the ply cap and wall clock adjudicate.

### `standing` — one heuristic, four games, and the eval bar

`standing(sim, seat): int` is an integer, **higher is better for that seat**, computed from the
true board, defined for all four games, recomputed after every ply. It is load-bearing three times:
it drives the viewer's **eval bar**, it adjudicates the `ply-cap` and `deadline` endings, and the
`tactician` baseline maximises it.

- **`connect-four`.** Over all **69** four-cell windows (24 horizontal, 21 vertical, 24 diagonal),
  sum `w[k]` for every window that contains **no opponent disc**, where `k` is the mover's disc
  count in that window and `w = [0, 1, 4, 16, 10000]`.
- **`breakthrough`.** `100 × pieces(seat) + 10 × Σ advance(p) + 40 × max advance(p)`, where
  `advance(p)` is how many ranks the piece has travelled from its own home rank (seat 0: `row`;
  seat 1: `size − 1 − row`).
- **`hex`.** `1000 − 10 × distToWin(seat)`, where `distToWin` is a **0–1 BFS** from the seat's
  source edge to its target edge in which a cell the seat owns costs 0, an empty cell costs 1 and a
  cell the opponent owns is impassable; unreachable is the sentinel **99** (so `standing = 10`).
- **`quoridor`.** `1000 − 10 × dist(seat) + 2 × wallsLeft(seat)`, where `dist` is the BFS pawn-step
  distance from the seat's pawn to the nearest cell of its goal rank over the wall-blocked graph,
  ignoring the opponent pawn (jumps never make a route longer).

The **eval bar** the idea asks for is `clamp((standing[0] − standing[1]) / scale, −1, +1)` with
`scale` = 40 (`connect-four`), 400 (`breakthrough`), 200 (`hex`), 200 (`quoridor`). *Decided, with
reason:* the idea says "eval bar from a reference engine **where one exists**" — none exists here,
because shipping an external engine would break "no engine dependency". So the bar is this
module's own heuristic and **the viewer labels it `HEURISTIC` in the bar's own caption**, never
"engine eval". Being honest about it costs nothing and a mislabelled bar would be a lie in the
one place spectators trust most.

### Turn structure: alternating single moves

The atomic unit is a **ply** = one seat making one move. `mover = (config.first + ply) mod 2`, so
seats strictly alternate; there is no pass, no double move and no simultaneity in any shipped
game. **Simultaneous-batch LLM calls are therefore not applicable here**: exactly one seat decides
per ply, and the next observation cannot be built until this move is applied, so calls go out one
at a time by construction, not by oversight. (If a future variant ever introduces simultaneous
decisions, its calls must go out as **one parallel batch per turn** — a `curly.RequestBatch` with
one `post` per open seat issued through `client.curl.makeRequests(batch, llmTimeoutSeconds)`, the
`decideAll` shape in `cogame-bullwhip/src/bullwhip/llm.nim` — because sequential per-seat calls are
the documented way to blow the 720 s budget. Nothing in v1 uses it.)

### Resolution order for ply `p` (0-based)

**This is the order the sim executes and the order the events appear in the replay.**

1. **`beginPly`.** `mover = (config.first + p) mod 2`.
2. **Wall-clock guard.** If `now + worstPlySeconds > playDeadline` → `settle("deadline",
   "wall-clock")` and stop. Checked **here, before any observation is built**, so the episode never
   stops mid-ply. Every wait that follows the guard is inside it:
   `worstPlySeconds = 2 × llmTimeoutSeconds + 2 + plySpacing + turnDelay = 60 + 2 + 4 + 0.25 =
   66.25`; `playDeadline = gameStart + 0.6 × episodeTimeoutSeconds`.
3. **Build the mover's observation** (§`## Server, player, protocol`), including
   `legalMoves(sim)` — produced by the **same proc the validator applies** in step 5, so the printed
   set and the accepted set cannot drift.
4. **Decide.** A scripted seat (and every seat when there are no LLM credentials) is decided inline
   by its baseline. An LLM seat gets **one** call bounded by `llmTimeoutSeconds` (30 s) inside curly.
5. **Parse + legality probe.** The reply is JSON-extracted (first `{` … last `}`, fences and
   trailing prose tolerated), the `move` string is normalised (§Reply schema) and tested for
   membership in `legalMoves(sim)`; the move is then applied to a **copy** of the sim, and a raised
   `GauntletError` means the reply is invalid. Invalid, unparseable or timed-out → **one retry**
   carrying the printed legal set → the `tactician` baseline. On a fallback,
   `fallbacks[mover] += 1` and one `falling back` line goes to stdout so the hosted log is greppable.
6. **Apply the move** through the per-game rules above — drop / place / step / jump / capture /
   wall — updating the board, `walls`, `captures` and `wallsUsed`.
7. **Record and emit.** The mover's already-truncated `say` and `notes` are stored and the `move`
   event is emitted (with the re-derivable `mkind` and `capture` fields).
8. **Win check for the mover**: `connect-four` line, `hex` connection, `breakthrough` home-rank or
   no-pieces, `quoridor` goal-row. On a win, emit `win` (carrying `how` and `path`) and
   `settle("complete", how)`.
9. **Draw check** (`connect-four` only): every cell occupied and no line → `settle("complete",
   "board-full")`.
10. **Starvation check**: if the next mover has **no legal move**, the next mover **loses** —
    emit `win` for the other seat with `how = "no-moves"` and `settle("complete", "no-moves")`.
11. `plies += 1`. If `plies == maxPlies` → `settle("complete", "ply-cap")`, adjudicated by
    `standing`.
12. **Pace.** `sleep(turnDelayMs)`; and if this ply used an LLM call, do not open the next
    LLM-driven ply until `plySpacingSeconds` have elapsed since this ply's first LLM call started
    (§`## Decisions` — the Bedrock sidecar rate floor). Continue at 1.

### Scoring formula and sign

```
score_i = +1  if seat i won
           0  on a draw
          -1  if seat i lost           score_0 + score_1 = 0, always
```

**Higher is better, the array sums to zero, and the league ranks by mean episode `score`, higher
first.** No other field is a ranking metric. *Decided, with reason:* the idea pins "zero-sum", all
four games are win/lose (Connect Four adds a draw) with no natural margin, and ±1 is what Elo
consumes cleanly. Everything richer — captures, walls used, final `standing`, plies — is reported
for the audience and the audit and is deliberately **not** scored, so no policy can farm the metric
instead of winning.

**Who won, by ending:**

| `ending` | Winner |
|---|---|
| `line` | the seat that completed four in a row |
| `connection` | the seat that linked its two edges |
| `home-rank` | the seat whose piece reached the opponent's home rank |
| `no-pieces` | the seat that took the last enemy piece |
| `no-moves` | the seat **not** to move (the starved seat loses) |
| `goal-row` | the seat whose pawn reached its goal rank |
| `board-full` | **draw** (Connect Four only) |
| `ply-cap` | higher final `standing`; equal → **draw** |
| `wall-clock` | higher final `standing`; equal → **draw** |

`results` reports, for humans and the audit: `names` (**policy** names), `scores`, `outcome[]`
(1 / 0.5 / 0), `game` (the resolved id), `rotated` (bool), `size`, `walls`, `first`, `seed`,
`winner` (seat or −1), `plies`, `maxPlies`, `standing[]` (final, true board), `captures[]`,
`wallsUsed[]`, `illegalReplies[]`, `fallbacks[]`, `ending`, `reason`.

### End conditions and `results.reason`

`results.reason` has **exactly two legal values**: `"complete"` and `"deadline"`. *Decided, with
reason:* phase 60 check 4 greps a finished replay for `results.reason == "complete"` (or a
`deadline` the design declares acceptable), so promoting `"connection"` to a reason would fail
verification on a perfectly healthy episode. The finer ending rides in a **separate** field,
`results.ending`, with exactly **nine** legal values:

| `reason` | `ending` | When |
|---|---|---|
| `complete` | `line` | Connect Four: four in a row |
| `complete` | `board-full` | Connect Four: 42 discs, no line — a draw |
| `complete` | `home-rank` | Breakthrough: a piece reached the far home rank |
| `complete` | `no-pieces` | Breakthrough: the last enemy piece was captured |
| `complete` | `no-moves` | the seat to move has no legal move and loses (Breakthrough in practice) |
| `complete` | `connection` | Hex: a seat linked its two edges |
| `complete` | `goal-row` | Quoridor: a pawn reached its goal rank |
| `complete` | `ply-cap` | `maxPlies` plies played with no terminal position; adjudicated by `standing` |
| `deadline` | `wall-clock` | the play deadline stopped the episode between plies; adjudicated by `standing` |

**`deadline` is an acceptable ending for this coworld and is declared as such here**: the episode
is fully scored at the stop by `standing`, so a deadline result is a real result, not a discarded
one. It should nonetheless be rare — see the arithmetic in `## Decisions`.

The `end` event carries both `reason` and `ending`, and the **same `settle(reason, ending)` proc**
applies them on record and on playback, so a wall-clock stop — which is not derivable from the
moves — re-derives identically in the wasm viewer (particle-worlds `13c66d7`, 2026-08-26: a
deadline stop applied outside the shared proc hash-mismatches at the stop tick).

### Anti-collusion

All three mechanisms the idea names, all structural rather than advisory:

1. **Two seats, zero-sum.** There is no coalition to form: `score_0 + score_1 = 0` by construction.
2. **Rotation announced.** Both seats are told the resolved game before their first move, in the
   `welcome` frame and in every prompt, so nobody can be cheated by rules they were not shown; and
   because the draw is a pure function of the recorded seed, nobody can be *steered* into a game
   either.
3. **Anonymous aliases and no inter-seat channel.** Seats play as `Sprocket`, `Gizmo`, … (babel's
   `CogNames` pool, seeded shuffle via `tableNames`); no prompt, no player frame and no in-game
   text ever contains a policy display name. `say` is **spectator-facing only** and is never shown
   to the opponent; `notes` are private and fed back only to their author; the per-seat `/player`
   `state` frame is redacted to that seat's own tallies. Every decision is made inside the game
   server from a view the server builds, so there is no wire on which two seats could coordinate.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | How this note satisfies it |
|---|---|
| Starter by game shape | cogame-babel — turn-based board, native rules, policy = prompt (top of this note) |
| Public repo `Metta-AI/cogame-<slug>` | `gh repo create Metta-AI/cogame-board-gauntlet --public …` in phase 20; `## Packaging` |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `## Decisions` — `PLAYER_PROMPT` vs `PLAYER_SCRIPTED=tactician\|hustler`, both algorithms given in full, per game |
| Simultaneous games: one parallel batch + the 60 % budget | §Turn structure — alternating play, so a batch is n/a and says so; the 60 % arithmetic is spelled out in `## Decisions` |
| Degrade, never hang | `## Decisions` §The ladder; the ply guard at step 2; `deadline` / `wall-clock` above |
| Static wasm replay viewer, never a pod | `## Viewer`; `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` |
| Real art, starter chrome verbatim | `## Viewer` §Chrome provenance and §Art |
| Legible to a casual spectator | `drops into d`, `b2 takes c3`, `wall at e3 (horizontal)`; never internal indices; `## Viewer` §Readouts; the 360 px check |
| Two name spaces | aliases in-game, `policyNames` spectator-side, `results.names` = policy names |
| `num_agents` in every variant and the cert fixture | `## Packaging` — **2** in all five variants' `game_config` and in `certification.game_config`; `<SEATS>` = 2 |
| Tests in CI (sim, bot, e2e replay, strict UTF-8, viewer smoke) | `## Tests` |

---

## Decisions: LLM with scripted fallback

**Both policy kinds ship in the same image from day one, switched by environment**, exactly as
babel does it. `/bin/board-gauntlet-player` reads:

- **`PLAYER_PROMPT`** — an LLM policy. The string is delivered to the game server over the player
  websocket, and the server sends it to Claude with the seat's observation on every ply.
- **`PLAYER_SCRIPTED=<name>`** — a scripted policy. The server plays the named baseline for that
  seat, no LLM. `<name>` is `tactician` or `hustler`; `1`, `true` and `yes` are accepted as
  synonyms for `tactician`.

With neither set the player delivers a built-in default prompt (below). With no credentials at all
the LLM client disables itself once and every seat plays `tactician` immediately — no retries, no
network waits — which is what makes offline certification and `docker_smoke.sh` complete.

### The two scripted baselines (exact algorithms)

Both are **deterministic** given the sim state (no RNG), **always produce a move that is in
`legalMoves(sim)`**, and never produce `say` or `notes`. Both are game-agnostic shells over three
procs — `legalMoves`, `applyMove` on a copy, and `standing` — plus the per-game tie-breaks named
below, which is what keeps one baseline honest across four games.

**`tactician`** — the default filler, and the fallback every failed LLM decision lands on.

1. **Win now.** If some legal move ends the game with the mover as winner, play the first such move
   in canonical order.
2. **Block.** Otherwise, for each legal move `m`: apply `m` on a copy; if the opponent then has a
   move that wins immediately, `m` is *unsafe*. If any safe move exists, restrict the candidate set
   to the safe moves. (If none is safe, keep them all — a lost position still has to move.)
3. **Maximise the differential.** Among the candidates, play the move maximising
   `standing(self) − standing(opponent)` on the resulting position.
4. **Tie-break** by the **lowest index in canonical move order**, which is: `connect-four` — files
   ordered by distance from the centre file, then left before right (`d, c, e, b, f, a, g`);
   `hex` — row-major cell index; `breakthrough` — `from` cell row-major, then `to` straight, then
   left-diagonal, then right-diagonal; `quoridor` — pawn moves (north, east, south, west, then the
   jump/diagonal targets in that order) before wall moves, walls row-major by anchor with `h`
   before `v`.

**`hustler`** — the second filler; a deliberately different shape, so the ladder is not two copies
of one bot. It **never defends**: it maximises its own progress and ignores the opponent's.

1. **Win now**, as above (a bot that walks past a win is noise, not a style).
2. Otherwise play the move maximising `standing(self)` alone on the resulting position, tie-broken
   by the **highest** canonical index.
3. Per-game flavour, applied as a pre-filter before step 2:
   - `connect-four`: restrict to the three central files (`c, d, e`) whenever at least one of them
     is legal.
   - `breakthrough`: restrict to moves of the **most advanced** own piece (ties: lowest cell index);
     a capture by that piece always beats a non-capture.
   - `hex`: restrict to cells on the seat's current shortest 0–1 BFS route (its own straight
     corridor when several routes tie), so it builds a chain and never wanders.
   - `quoridor`: place **no wall at all** while `dist(self) ≤ dist(opponent)`; once behind, play the
     legal wall that maximises `dist(opponent)`, ties by lowest anchor index, and if no wall
     increases it, step along its own shortest route.

**Neither baseline has a tunable parameter**, which is why this repo ships no grid harness: both
are pure one-ply lookahead over `legalMoves` / `applyProbe` / `standing`, with no thresholds,
weights, temperatures or search depths to sweep. The only numbers in the loop are the four
`standing` definitions fixed verbatim above, and they are scoring rules, not knobs. What a harness
would otherwise establish is established by tests instead: the fillers beat a uniform-random legal
mover, they disagree with each other, and they never walk past an immediate win or into an
immediate loss.

A test asserts `tactician` and `hustler` disagree on **at least 30 %** of plies over 200 seeded
episodes per game — two fillers that play the same game are one filler — with **one recorded
exception: Connect Four, where the floor is 25 %**. Both baselines score from the same window
heuristic, both take the centre file first and both play a winning move on sight, and there are
only seven files to disagree about, so the measured rate sits at 28–30 % however the ply
population is drawn; Breakthrough (~72 %), Hex (~85 %) and Quoridor (~37 %) clear 30 %
comfortably. The exception is written into the test it governs
(`tests/test_bot.nim`, suite *baseline diversity*). A second test asserts
`tactician` beats a seeded uniform-random legal mover (mean score > 0 over 200 episodes per game),
so the fillers are a real opponent rather than a punching bag.

### Sequential turns, the rate floor, and the wall-clock arithmetic

Config knobs and defaults: `llmTimeoutSeconds = 30` (**this is the idea's "time control per move"
lever**; fast is LLM-hostile, slow is search-hostile, and v1 pins one value so the ladder compares
like with like — blitz/classical variants are out of scope), `maxOutputTokens = 900` (not 400 —
Haiku is `cut off at max_tokens` at 400), `model = "claude-sonnet-5"` (the hosted Bedrock path tries
`us.anthropic.claude-haiku-4-5-20251001-v1:0` first, and **the candidate list drops
`us.anthropic.claude-sonnet-4-6`**, which times out on every sidecar call — raid, 2026-08-23),
`plySpacingSeconds = 0` meaning *derive as 4*, `turnDelayMs = 250` (0 in the cert fixture).
The direct Anthropic request body also carries `output_config: {"effort": "low"}` — a board move
needs no long deliberation and low effort is the cheaper, faster setting — but **only** when the
model is neither a Haiku nor a `4-5` tier, which reject the whole request with a 400 if the field
is present. The Bedrock path never sends it.

**Rate floor.** The Bedrock sidecar caps **30 requests per minute per episode**. A ply issues at
most 2 requests (the call plus one retry), so the minimum spacing between the starts of two
LLM-driven plies is `2 × 60 / 30 = 4 s`. The loop sleeps to that floor; it gates LLM plies only, so
the all-scripted certification path is unaffected.

**The arithmetic, out loud.** The game container never receives `COWORLD_TIMEOUT_SECONDS`, so it
assumes `episodeTimeoutSeconds = 1200`; the play budget is `0.6 × 1200 = **720 s**`. Expected
per-ply wall clock is `max(4 s floor, ~3 s haiku latency) + ~0.4 s apply/broadcast ≈ **4.4 s**`.

| Variant | `maxPlies` | Worst case `maxPlies × 4.4` | % of 720 s | Expected plies | Expected play |
|---|---|---|---|---|---|
| `connect-four` | 42 | 185 s | 26 % | ~30 | 132 s |
| `breakthrough-6` | 80 | 352 s | 49 % | ~55 | 242 s |
| `hex-7` | 49 | 216 s | 30 % | ~35 | 154 s |
| `quoridor-9` | 80 | 352 s | 49 % | ~45 | 198 s |
| `gauntlet` (rotation) | ≤ 80 | ≤ 352 s | ≤ 49 % | ~40 | ~180 s |

Every variant's **full-length** game fits inside 60 % of the timeout with room to spare, which is
why `maxPlies` is 80 and not 200. The pathological case is latency, not length: worst case per ply
is `2 × llmTimeoutSeconds + 2 + plySpacing + turnDelay = 66.25 s`, and `80 × 66.25 = 5300 s` would
overrun by more than seven times. That is why **step 2 of the resolution order refuses to open a
ply unless `now + 66.25 s ≤ playDeadline`** and settles `deadline` / `wall-clock` instead, scored on
`standing`. The spacing sleep and the turn delay are counted because they run **after** the guard;
leaving them out let the settle land ~2 s past the 720 s mark. The guard, not optimism, is what
keeps the episode inside the budget.

Certification / smoke path: with no `ANTHROPIC_API_KEY` both seats play scripted, there is no LLM
call, the spacing floor does not apply, `turnDelayMs = 0`, and the `breakthrough-6` fixture
completes in well under 3 s of play — inside `coworld certify`'s 60 s default, which is the only
budget the certify step has: the shared `coworld-release.yml` template passes `--no-open-report`
and nothing else, and this repo ships that template **byte for byte**, so no `--timeout-seconds`
is added here. A test pins the fixture's scripted duration under 50 s (cogame-commons-family
0.1.0, 2026-08-24), which is what keeps it inside that default.

### The ladder — degrade, never hang

Per ply:

1. **One LLM call**, timeout `llmTimeoutSeconds` (30 s), enforced by curly, not by hope.
2. **Parse + legality probe** on a copy of the sim (step 5 of the resolution order).
3. **One retry**, with this hint appended to the user prompt: *"Your previous reply was invalid.
   Respond with ONLY the requested JSON object; `move` must be exactly one of the strings in this
   list: `<legalMoves(sim), printed>`"*. Printing the legal set, computed by the **same predicate
   the validator applies**, is what halves fallbacks in formal-output games (escrow 0.1.3,
   2026-08-23), and it is affordable here because no shipped game has more than 133 legal moves.
4. **Fallback** to `tactician`, `fallbacks[seat] += 1`, `illegalReplies[seat] += 1` when the reply
   parsed but was illegal, and a `falling back` line on stdout.
5. If credentials are missing or auth fails, the client disables itself once and every later
   decision is scripted immediately.

Episode-level: the play deadline settles the episode **between plies, never mid-ply**; results and
the replay are written in babel's `finishEpisode` order (final frames to players → `results.json`
→ `.replay`); `/healthz` and `/global` keep answering for a **20 s shutdown grace** after the
artifacts land (lantern 0.1.3 → 0.1.4: the certifier pings `/global` *after* the player pods start),
then `quit(0)`. The player binary wraps its receive loop in `try/except CatchableError` and
**exits 0 on a dead socket** (raid 0.1.3 → 0.1.4: whisky *raises* on a close frame and the player
container otherwise exits 1, intermittently).

### The two champion prompts (exact text)

`tools/ci/policies.json` mints four policies. Champion #1 and champion #2 are **both**
`PLAYER_PROMPT` policies — a scripted policy seated as a champion is a failure state.

- **`board-gauntlet-grandmaster`** (champion #1, owner daveey,
  `ply_44ae9048-3242-4654-881f-6d9d43347fa3`):

  > Read the board before you read your plan. Every ply, in your notes: (1) name the one move your
  > opponent threatens next and whether it wins on the spot, (2) name your own fastest win and how
  > many moves it needs, (3) pick the move that advances (2) without allowing (1). CONNECT FOUR:
  > take the centre file early; count both diagonals every ply; never fill a cell that hands them
  > the square directly above it. BREAKTHROUGH: pieces defend each other in diagonal pairs — never
  > push a lone runner past a supported enemy pawn; a capture that opens a straight lane to your
  > home rank is a loss, not a gain. HEX: play the cell that shortens your own chain the most, and
  > prefer one that also sits on their shortest route — a stone that builds and blocks is worth
  > two that only build; bridge with a gap (two stones a knight's step apart) because a bridge
  > cannot be cut. QUORIDOR: count both path lengths every single ply and say the two numbers out
  > loud in your notes; if you are ahead, run and save your walls; if you are behind, spend one
  > wall to add the most steps to their route, and never spend two walls on a detour they can walk
  > around. Copy the move string exactly as it appears in the legal-move list.

- **`board-gauntlet-tempo`** (champion #2, owner daveey-1,
  `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`):

  > Play for tempo: every move must either create a threat they must answer or answer one of
  > theirs. Before you choose, list the two or three moves you are actually considering and, for
  > each, write the opponent's best reply — if you cannot name their reply, you have not looked.
  > CONNECT FOUR: build two threats at once (a double threat wins; a single one is answered) and
  > watch the parity of the column heights. BREAKTHROUGH: advance as a phalanx of two or three
  > touching files rather than a single runner; trade only when the trade leaves you with more
  > pieces on the side of the board you are attacking. HEX: block first on a small board — a cut
  > through the centre is worth more than a stone at the edge; if their chain has only one route
  > left, take the cell on it. QUORIDOR: walls are ammunition, not decoration; the strongest wall
  > is the one placed just ahead of their pawn, not next to your own, and a wall that adds fewer
  > than two steps to their path is a wasted turn. Never invent a move: copy one string from the
  > legal-move list exactly.

- **`board-gauntlet-tactician`** (filler): `PLAYER_SCRIPTED=tactician`.
- **`board-gauntlet-hustler`** (filler): `PLAYER_SCRIPTED=hustler`.

The player binary's built-in default prompt (used when `PLAYER_PROMPT` is unset and the seat is not
scripted) is: *"Play to win, one move at a time. Every ply, name the opponent's strongest threat
and your fastest win, then play the legal move that best serves both. Copy your move exactly from
the legal-move list you are given, and reply with only the JSON object."*

---

## Sim module

Pure rules: no IO, no networking, no LLM. Driven identically by the server, the tests and the wasm
viewer, which is what makes the replay re-derivable. The layout mirrors babel's. The Nim package is
`gauntlet` (short); the *binaries* carry the full slug because `tools/ci/docker_smoke.sh` defaults
to `/bin/<slug>`.

```
gauntlet.nimble
src/gauntlet.nim                     entrypoint -> /bin/board-gauntlet         (fork of src/babel.nim)
src/gauntlet_player.nim              player     -> /bin/board-gauntlet-player  (fork of src/babel_player.nim)
src/gauntlet/types.nim               config, events, enums                     (fork of src/babel/types.nim)
src/gauntlet/sim.nim                 the rules above                           (fork of src/babel/sim.nim)
src/gauntlet/games/connect_four.nim  per-game rules                            (new)
src/gauntlet/games/breakthrough.nim  per-game rules                            (new)
src/gauntlet/games/hex.nim           per-game rules                            (new)
src/gauntlet/games/quoridor.nim      per-game rules                            (new)
src/gauntlet/llm.nim                 Claude client, prompts, the two baselines (fork of src/babel/llm.nim)
src/gauntlet/server.nim              mummy HTTP/WS server, replay writer       (fork of src/babel/server.nim)
replay-viewer/gauntlet_replay.nim    wasm entry                                (fork of replay-viewer/babel_replay.nim)
```

Each `games/*.nim` exports exactly four procs — `legalMoves`, `applyMove`, `terminal`, `standing` —
plus `startBoard`; `sim.nim` dispatches on `config.game` and owns everything else (events, settle,
scores, results, replay). One dispatch point, four small modules, no cross-talk.

### Types

```nim
type
  GauntletError* = object of CatchableError

  Game* = enum
    gRotate       = "rotate"          ## config only; resolved by sampleEpisode
    gConnectFour  = "connect-four"
    gBreakthrough = "breakthrough"
    gHex          = "hex"
    gQuoridor     = "quoridor"

  GameConfig* = object
    tokens*: seq[string]                # connection tokens, injected by the runner
    players*: seq[PlayerConfig]         # policy display names, by slot
    game*: Game
    rotated*: bool                      # true when the rotation resolved `game`
    size*: int                          # per-game side; connect-four is size x (size-1)
    walls*: int                         # quoridor walls per seat
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

  MoveKind* = enum
    mkDrop = "drop", mkPlace = "place", mkStep = "step",
    mkJump = "jump", mkCapture = "capture", mkWall = "wall"

  EventKind* = enum
    evStart = "start"
    evMove  = "move"
    evWin   = "win"
    evEnd   = "end"
```

`update(config, json)` applies the runtime JSON over the defaults and **raises `GauntletError`** on:
an unknown `game`; `players.len != 2`; `first` outside 0..1; `maxPlies` outside 4..200; `walls`
outside 0..20; and a `size` outside the per-game range — `connect-four` 5..9, `breakthrough` 4..8
and even, `hex` 4..11, `quoridor` 5..11 and odd (an odd side is what gives each pawn a centred
start).

`sampleEpisode(config)` is idempotent (a replay carrying `sampled: true` is untouched) and does
three things, in order: resolves the rotation (§The rotation rule), clamps
`maxPlies = clamp(maxPlies, 4, cap)` where `cap` is `size × (size − 1)` for `connect-four`,
`size × size` for `hex` and `200` for the other two, and sets
`turnDelayMs = min(turnDelayMs, 120_000 div max(maxPlies, 1))`.

### Sim state

```nim
Sim* = object
  config*: GameConfig
  names*: seq[string]             # anonymous cog aliases (babel's tableNames, seeded shuffle)
  board*: seq[Occupant]           # cols*rows, row-major from rank 1
  hWalls*, vWalls*: seq[bool]     # quoridor: (size-1)^2 anchors, per orientation
  pawns*: array[2, int]           # quoridor: cell index per seat
  wallsLeft*: array[2, int]
  wallsUsed*, captures*: array[2, int]
  fallbacks*, illegalReplies*: array[2, int]
  says*, notes*: seq[string]      # latest, per seat
  scripted*, fellBack*: array[2, bool]
  mover*: int
  ply*, plies*: int
  winner*: int                    # -1 = none yet / draw
  winPath*: seq[int]
  lastMove*: string
  lastKind*: MoveKind
  lastCapture*: int               # cell index or -1
  done*: bool
  reason*, ending*: string
  events*: seq[GameEvent]
```

### Procs the server, the tests and the viewer all call

- `initSim(config): Sim` — validates, seeds the aliases, lays out `startBoard` for the resolved
  game, `mover = config.first`, logs `evStart`.
- `cellName*(sim, cell): string` / `cellIndex*(sim, name): int` — the algebraic ↔ index pair.
- **`legalMoves*(sim): seq[string]`** — every legal move for `sim.mover` as a canonical string, in
  canonical order (§`tactician` step 4). **The prompt, the retry hint, the validator and both
  baselines all call this one proc**, so they cannot drift.
- `normalizeMove*(sim, raw: string): string` — the tolerant reader (§Reply schema); returns `""`
  when the string does not name a move of this game.
- `applyMove*(sim, move, say, notes, scripted, fellBack)` — resolution-order steps 6–11 in one
  atomic step. Raises `GauntletError` naming the seat and the move when `move` is not in
  `legalMoves(sim)`; the server probes with this on a copy before committing.
- `standing*(sim, seat): int` — the four definitions in `## The game`.
- `evalBar*(sim): float` — `clamp((standing(0) − standing(1)) / scale, −1, 1)`.
- `distToWin*(sim, seat): int` (hex) / `pathLen*(sim, seat): int` (quoridor) — the BFS pair, also
  used by the prompts and the scorebug.
- `endEarly*(sim)` — `settle("deadline", "wall-clock")`.
- **`settle*(sim, reason, ending)`** — the single proc that ends the game, decides the winner from
  the table in `## The game`, and logs `evEnd`. Called on record **and** on playback.
- `score*(sim, seat): float` — `+1 / 0 / −1`.
- `resultsJson*(sim)`, `boardStateJson*(sim)`.
- `replayMatch*(config, events): seq[Sim]` — re-derives one state per event prefix by replaying
  `evMove` through the rules and applying `evEnd`'s `reason`/`ending` through `settle`. The
  recorded `mkind` and `capture` on `evMove`, and `seat`/`how`/`path` on `evWin`, are **re-derived
  and checked** against the recording, raising `GauntletError` on a mismatch.
- `eventToJson*` / `eventFromJson*`.

### Event vocabulary written to the replay

Four kinds. Every kind has a feed line, a scrub-beat class and CSS (`## Viewer`).

| kind | fields |
|---|---|
| `start` | `{kind, round: -1}` — the episode opens (names, resolved game, config and seed ride in the replay header) |
| `move` | `{kind, round, seat, move, mkind: "drop"\|"place"\|"step"\|"jump"\|"capture"\|"wall", capture: "<cell>"\|"", say, notes, scripted, fellBack}` |
| `win` | `{kind, round, seat, how: "line"\|"connection"\|"home-rank"\|"no-pieces"\|"no-moves"\|"goal-row", path: [cell]}` |
| `end` | `{kind, round, reason, ending, scores: [float], standing: [int]}` |

`round` is the **ply index** (0-based). *Decided, with reason:* the field is named `round` — not
`ply` — because the chrome copied verbatim from babel (`roundBase`, `renderFeed`'s block grouping
and `buildScrub`'s spans) groups on `event.round`, and renaming it would force edits into copied
regions for nothing. Everything human-facing renders it as **"PLY n"** (one named edit, listed in
§Chrome provenance).

Moves and cells in events are **algebraic strings** (`"d"`, `"c4"`, `"b2-c3"`, `"e3h"`), never
indices, so the bytes are readable and a future board size cannot silently reinterpret an old
replay. `say` and `notes` are the *already-truncated* values (rune boundaries — see the reply
schema); nothing else in an event is free text.

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
WS  /player?slot=N&token=T     gauntlet.player.v1   (live mode only)
WS  /global                    spectator snapshots; answers Ping with Pong
WS  /replay                    the replay payload (replay mode only)
```

### Player protocol `gauntlet.player.v1`

JSON text frames on `COWORLD_PLAYER_WS_URL`.

game → player:

- `{"type":"welcome","protocol":"gauntlet.player.v1","slot":N,"name":"<alias>","seats":2,
   "game":"hex","rotated":true,"size":7,"walls":0,"first":0,"maxPlies":49}`
- `{"type":"state","slot":N,"name":"<alias>","game":"hex","ply":p,"maxPlies":M,
   "seat":{"score":f,"standing":s,"captures":k,"wallsLeft":w,"fallbacks":n},
   "toMove":bool,"started":b,"done":b,"reason":s,"ending":s}` after every event. Redacted to the
  seat's own tallies; it carries no board and no move list, because **decisions are server-side**,
  so this loses the policy nothing.
- `{"type":"final","done":true,"slot":N,"scores":[…],"outcome":[…],"names":[<aliases>],
   "game":"hex","plies":k,"reason":s,"ending":s}` at the end; the player exits after it.

player → game:

- `{"type":"prompt","prompt":"<≤4000 chars>","scripted":"tactician"|"hustler"|true|false}` — sent
  on connect and again after `welcome` (the first send can race slot registration). The latest
  frame wins. Over-cap prompts are truncated **on a rune boundary**.

### Global protocol

`/global` sends the whole snapshot after every event:

```
{"type":"state","game":"board-gauntlet","board_game":"quoridor","rotated":true,
 "size":9,"walls":10,
 "board":["empty","seat0",…],                   // occupants, row-major from rank 1
 "hWalls":[bool…],"vWalls":[bool…],"pawns":[36,76],"wallsLeft":[7,9],
 "seats":[{name, policy, standing, captures, wallsUsed, score, say, notes,
           scripted, fellBack, readout}, ×2],
 "mover":0,"ply":14,"maxPlies":80,"plies":14,"legalCount":37,
 "lastMove":{"seat":0,"move":"e3h","mkind":"wall","capture":""},
 "eval":0.18,"winner":-1,"winPath":[],"phase":"moving",
 "gameDone":false,"reason":"","ending":"","policyNames":[…],"events":[…],
 "started":true,"connected":[bool,bool]}
```

`phase ∈ {"moving","done"}`. `readout` is the one-line per-seat tension string the scorebug draws
(`TO CONNECT 3`, `PATH 6 · WALLS 7`, `PIECES 9 · ROW 4`, `THREATS 2`).

### The observation each seat gets (complete)

**This is a perfect-information game and the observation says so.** Every seat is given, every ply,
the entire position — there is no fog, no private card and no hidden count.

The **system prompt** (one per game, identical for both seats) states that game's rules verbatim
from `## The game` — the board, the move notation, the legality rules, the win conditions, the ply
cap and the adjudication rule — the seat's alias and colour, and the output contract, ending with:
*"reply with ONLY one JSON object, nothing else — no analysis, no explanation, no markdown fences.
Your reply must begin with the character `{` and end with `}`."* (Bedrock Haiku answers prose-first
without this.)

The **user prompt**, in this order:

1. `Ply <p+1> of <maxPlies>. You are <alias>, playing RED in HEX on a 7×7 board.` — and, when the
   episode came from the rotation, `This episode's game was drawn by the gauntlet rotation: HEX.`
2. `YOUR GOAL: link the left file (a) to the right file (g) with an unbroken chain of your own
   stones.` (per game; Connect Four: four in a row; Breakthrough: reach rank 6 or take every enemy
   piece; Quoridor: get your pawn to rank 9.)
3. **THE BOARD**, as a labelled ASCII diagram, ranks descending, files lettered along the bottom;
   `.` empty, `R`/`B` the two seats' pieces or stones or discs. Quoridor additionally draws `—` and
   `|` wall segments between cells, and prints `WALLS LEFT: you 7, opponent 9`.
4. `MOVE HISTORY (most recent last): 1. d 2. d 3. c …` — every move of the episode in canonical
   notation, both seats, numbered by ply.
5. `POSITION SUMMARY:` the two `standing` numbers and the per-game readout for **both** seats —
   e.g. `You are 3 stones from connecting; your opponent is 4.` / `Your path is 6 steps, theirs is
   9.` / `You have 9 pieces, most advanced on rank 4; they have 11, most advanced on rank 3.` /
   `You have 2 open threes; they have 1.` Nothing here is secret: both seats get both numbers.
6. `YOUR LEGAL MOVES (<n>) — copy one of these strings exactly: d c e b f a g` —
   `legalMoves(sim)`, the same proc the validator applies, printed in full.
7. `YOUR NOTES FROM EARLIER PLIES:` the seat's latest notes verbatim, or `(none)`.
8. `GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules):` the seat's
   `PLAYER_PROMPT`.
9. The reply contract (below).

**Hidden from a seat**, exhaustively: the opponent's **reasoning** — its `notes`, its `say`, its
`PLAYER_PROMPT`, and any deliberation it did — plus the mapping from anonymous aliases to policy
display names. **Nothing about the position is hidden**: the full board, the wall layout, both
`standing` values, the complete move history, the legal-move set, the ply cap, the adjudication
rule and the resolved game are all given to both seats every ply. That is the point of the family.

### Reply schema, with caps

```json
{"move": "e3h", "say": "boxing him into the left half", "notes": "his path 9, mine 6; keep 4 walls"}
```

| field | type | required | cap / legality | on violation |
|---|---|---|---|---|
| `move` | string | **yes** | **12 characters max**; after normalisation must be in `legalMoves(sim)` | retry once, then `tactician` |
| `say` | string | no | **80 characters**, single line | truncated |
| `notes` | string | no | **400 characters** | truncated |

`normalizeMove` is deliberately tolerant, and identically so in the validator and in the tests: the
string is lower-cased, trimmed, and stripped of every character outside `a-z0-9`; then, per game —
`connect-four`: the move is the **first standalone one-character token** that is a file letter
`a`..`g` or a digit `1`..`7` mapping to `a`..`g`; every byte outside `a-z0-9` in the raw reply
becomes a separator first, so multi-byte punctuation splits tokens instead of joining them, and a
reply with no such token falls back to its first character (`"d"`, `"D"`, `"4"`,
`"column d — centre"` all mean `d` — note that a literal *first character* rule would read that
last one as the `c` of "column", which is why the rule is per token).
`hex`: must match `^[a-g][1-7]$`. `breakthrough`: must match `^[a-f][1-6][a-f][1-6]$` after
stripping (so `b2-c3`, `b2c3`, `b2 x c3` all mean `b2-c3`); the canonical form written to the event
is `b2-c3`. `quoridor`: `^[a-i][1-9]$` is a pawn move, `^[a-h][1-8][hv]$` a wall. Anything else
returns `""` and is an invalid reply.

**Every truncation is on a rune boundary**, with `…` appended, via one shared `cleanText(text,
cap)` (babel's `cleanNotes`, generalised): `say` (80), `notes` (400), `move` (12), the delivered
prompt (4000), and any error text that reaches an event or the log (200). A byte-boundary cut is
exactly how a replay renders in a browser but fails a strict JSON parser; `tests/test_replay.nim`
pins it with multi-byte input at exactly the cap. Newlines in `say` are replaced by spaces (it is
drawn in a reserved band under the board, wrapped over as many lines as the cap needs).

### Replay bytes (self-sufficient)

`replayPayload` writes, and the wasm module reads, exactly:

```json
{"protocol": "gauntlet.replay.v1",
 "names": ["Sprocket", "Gizmo"],
 "policyNames": ["board-gauntlet-grandmaster", "Baseline (1)"],
 "config": {"game": "quoridor", "rotated": true, "size": 9, "walls": 10,
            "first": 0, "seed": 118829, "maxPlies": 80, "sampled": true},
 "events": [ … the four kinds above … ],
 "results": { … the results object … }}
```

Names, policy names, the resolved game, the full config, the seed, the ply cap and every event are
in the bytes; the viewer re-derives every frame in the browser and contacts nothing but S3 for the
file. There is no `/client/replay` pod viewer declared anywhere.

---

## Viewer

### The four viewer files come from cogame-babel — all four, no mixture

`replay-viewer/config.nims`, the wasm entry `replay-viewer/gauntlet_replay.nim`,
`replay-viewer/static_replay.js` and `replay-viewer/index.html` are **all four forked from
`Metta-AI/cogame-babel`** (commit `d55d999`) and from nothing else. This is not a stylistic
preference: babel's `config.nims` links with `-s MODULARIZE=1 -s EXPORT_NAME=BabelReplayModule` and
babel's `static_replay.js` bootstraps with `BabelReplayModule().then(…)`; splicing one starter's
shell onto another's link flags (an `onRuntimeInitialized` bootstrap against a `MODULARIZE` build)
leaves the factory uncalled, throws nothing, and hangs the viewer forever — cogame-lantern,
2026-08-23.

The fork renames, and renames only:

- **`replay-viewer/config.nims`** — output `dist/gauntlet_replay.js`,
  `EXPORT_NAME=GauntletReplayModule`, and
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_bg_load_replay,_bg_payload_ptr,_bg_payload_len,_bg_error_ptr,_bg_error_len`.
  Every other switch (`--mm:arc`, `--exceptions:goto`, `--define:noSignalHandler`, `-d:release`,
  `-d:useMalloc`, `-O2`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`,
  `EXPORTED_RUNTIME_METHODS=HEAPU8`) is kept byte-for-byte — the `useMalloc`/`ABORTING_MALLOC` pair
  is load-bearing and its comment travels with it.
- **`replay-viewer/gauntlet_replay.nim`** — babel's `babel_replay.nim` with `bab_*` → `bg_*`. It
  parses the replay JSON, rebuilds `GameConfig` from `replay["config"]`
  (`game, rotated, size, walls, first, seed, maxPlies`, `sampled: true`) plus `replay["names"]`,
  runs `replayMatch`, and emits `{type, protocol, names, policyNames, config, events, results,
  states}` where `states[i]` is `boardStateJson` after `events[0..<i]`. It keeps babel's
  `emscripten_exit_with_live_runtime` epilogue verbatim.
- **`replay-viewer/static_replay.js`** — babel's file with `BabelReplayModule` →
  `GauntletReplayModule`, `_bab_*` → `_bg_*`, `BabelRenderer` → `GauntletRenderer`.
  `FETCH_TIMEOUT_MS = 20000`, the caption, the Retry button and the `{src:"coworld-replay", type}`
  parent bridge are kept.
- **`replay-viewer/index.html`** — babel's static page with the script list
  `chrome_common.js, renderer.js, gauntlet_replay.js, static_replay.js`, the `<title>`, the
  `#wordmark` inner text (`BA<span>BEL</span>` → `GAUNT<span>LET</span>`), and
  `BabelRenderer.bindFeedToggle` → `GauntletRenderer.bindFeedToggle`. **Nothing is removed.**

**Load signalling.** The shell sets **`data-replay-loaded="true"`** on `document.documentElement` on
its **first drawn frame**, and **`data-replay-error="<message>"`** on `document.documentElement` on
failure (removing the error attribute on a retry). One required deviation from babel is named here:
babel sets `data-replay-loaded` inside the renderer's ready callback
(`client/renderer.js:1309`) but posts the bridge `ready` from a double-`requestAnimationFrame` at
the call site (`replay-viewer/static_replay.js:122–124`), so `ready` can precede the first painted
frame and an embedding page can sample an unpainted shell (chorus `3c11c953`, 2026-08-24). Here
`GauntletRenderer.attachReplay` takes an `onFirstFrame` callback, sets `data-replay-loaded="true"`
inside it, and `static_replay.js` posts `tell("ready")` **from that callback**, after the attribute
is set.

### Chrome provenance

- **`client/chrome.css`** — cogame-babel's `client/chrome.css` (443 lines) copied
  **byte-for-byte**. Not one starter rule is edited or deleted. The game's rules are **appended**
  below the last starter line under `/* ===== board-gauntlet game block ===== */`: the board
  frame, the eval bar, the `say` band, the four beat-kind classes and their modifiers, the
  `--band` / `--hudscale` consumers, and the ≤ 640 px / ≤ 360 px media queries. Each of those two
  media queries is written **twice** — once as `@media`, once keyed on `body.narrow-640` /
  `body.narrow-360` — declaration for declaration. A page cannot resize the viewport it is loaded
  into, so `tools/ci/renderer_fixture.html` narrows the stage in place and sets those classes;
  without the second copy the narrow-width rules would ship untested. Both copies are below the
  game-block banner, so no starter rule is touched, and they must be edited together.
- **`client/chrome_common.js`** — the chrome half of cogame-babel's `client/renderer.js`, copied
  **byte-for-byte** out of the starter file (`cp` + slice; not one line is retyped, reformatted or
  "tidied") as these contiguous regions of `d55d999`, in this order:
  **23** (`COLORS`, the seat palette), **85–87** (`seatColor`) — both are referenced by the copied
  `renderFeed` and `updateEndscreen`, so they come across with them —
  **101–124** (`ellipsize`, `hexToRgb`, `shade`, `rgba`), **680–733** (`// ---- Names ----` through
  `clampName`: `isBaselineFiller`, `makeNameMap`, `applyNames`, `clampName`), **735–744**
  (`// ---- Event feed ----`, `roundBase`), **790–863** (`blockHead`, `renderFeed`, `escapeHtml`),
  **963–970** (`reasonLine`), **972–1027** (`updateEndscreen`), **1029–1048** (`bindFeedToggle`)
  and **1142–1222** (the scrubber comment and `buildScrub`). It exports `window.GauntletChrome`.

  **Exactly seven copied lines/regions are edited**, and each is named here so a reviewer can find
  it — everything else in the file is copied bytes or appended at the end:

  | # | Starter line(s) | Edit |
  |---|---|---|
  | 1 | 791 (`blockHead`) | `"ROUND " + (block + 1)` → `"PLY " + (block + 1)` |
  | 2 | 827 (`renderFeed`) | `describeEvent(event, nameMap, ctx)` → `feedText(event, nameMap, ctx)`, injected once by `GauntletChrome.setFeedText(fn)` |
  | 3 | 829–836 (`renderFeed`) | the speak/pick notes sub-line becomes the say sub-line: the condition `event.kind === "speak" \|\| event.kind === "pick"` → `event.kind === "move"`, and the rendered string `… " notes: " …` → `… ": “" + say + "”"` |
  | 4 | 1179–1189 (`buildScrub`) | babel's marker-`div` loop → `markPlyBeat(container, event, i, events.length, onSeek)` for **every** event; `markPlyBeat` is appended at the end of the file |
  | 5 | 1004–1008 and 1020–1023 (`updateEndscreen`) | the hard-coded `end-head` labels and the `cell(...)` calls → one injected `endColumns(results)` returning `{heads:[…], cell(i)}`, injected by `GauntletChrome.setEndColumns(fn)` |
  | 6 | 966–967 (`reasonLine`) | `results.rounds` / `results.maxRounds` → `results.plies` / `results.maxPlies`, and the word `rounds` → `plies` |
  | 7 | 994–999 (`updateEndscreen`) | the endcard verdict and title, which §Readouts already specifies: `… " LEADS THE TABLE" : "ALL LEVEL"` → `escapeHtml(clampName(names[topIndex])).toUpperCase() + " WINS" : "DRAWN"` (two seats and a zero-sum result — one of them wins or the game is drawn), and `FINAL — <rounds> ROUND(S)` → `FINAL — <plies> PLY/PLIES` |

  **Appended** at the end of `chrome_common.js`, in this order: `relayout()`, `setBeatNames()`,
  `beatSeatName()`, `beatLabel()`, `markPlyBeat()`, `setFeedText()`, `setEndColumns()`, and the
  `window.GauntletChrome` export. (`setBeatNames`, `beatSeatName` and `beatLabel` are what give a
  beat button its `aria-label` / `title` — `markPlyBeat` calls `beatLabel`, which needs the name
  map the driver installs.) **Nothing is renamed in place.**

  Babel's game-specific procs are **not** copied; their replacements live in the game block: the
  palette/geometry/scene drawing at 17–100 and 126–679, `spellTokens` (746–749), `describeEvent`
  (753–781), `endText` (783–788), `makeEffects` (865–900), `phaseText` (904–914), `matchHeader`
  (916–932), `updateScorebug` (934–961), `stateToView` (1052–1063), `attachLive` (1065–1140),
  `attachReplay` (1224–1311) and the `window.BabelRenderer` export (1313–1318).

- **`client/renderer.js`** — the game block. It draws the four boards and exports
  `window.GauntletRenderer = {attachLive, attachReplay, renderFeed, bindFeedToggle}`. It declares
  **no identifier already exported by `GauntletChrome`**, and the beat builder is named
  `markPlyBeat` and lives in the chrome, not the game block — a game-block `function markBeat` is
  hoisted over a chrome alias `var markBeat = C.markBeat` and silently turns every beat into an
  unlabelled div that never seeks (tandem, 2026-08-23). A CI check asserts the non-overlap
  (`## Tests`).

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
    (`BA<span>BEL</span>` → `GAUNT<span>LET</span>`), the `#clock` placeholder text
    (`ROUND 0` → `PLY 0`, because this ladder counts plies and the placeholder is on screen until
    the first frame lands), the `<script src>` list, which gains `/client/chrome_common.js` ahead
    of `/client/renderer.js`, and the bootstrap's `BabelRenderer` → `GauntletRenderer`. The
    element itself is kept, with its id; only the text inside it changes.
  - **Appended:** one `<script>` block at the end that registers the game's feed text and endcard
    columns with `GauntletChrome`, and **one** new element — `<div id="evalbar"><i></i></div>` —
    appended **inside the existing `#scorebug`** by the game block at runtime, never spliced into
    the starter's markup by hand. The board itself is drawn inside the existing `canvas#table`,
    which is why nothing has to be inserted into `#board-wrap`.
  - `client/global.html` and `client/player.html` are copied the same way (byte-for-byte +
    wordmark/title text + the `chrome_common.js` script tag), because the certifier fetches both
    *before* the player pods start and neither may open the player socket.

- **Zoom: dropped.** Babel has no `#viewpanel`, and none is added. The largest shipped board is
  Quoridor's 9×9, which is drawn whole inside the frame at every width down to 360 px, so a zoom
  bar and a minimap would have nothing to do and would only steal height. (Pin: `#viewpanel` is
  kept **only** when the board is larger than the frame.)

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
  `<button type="button" class="beat-marker beat-<kind> …" aria-label="Ply 14 — Sprocket plays c4"
  title="…">` for **every** recorded event, and clicking one seeks to that event. **CSS exists for
  every kind emitted** — `.beat-start`, `.beat-move`, `.beat-win`, `.beat-end` — plus the modifiers
  `.beat-move.capture` (amber, taller) and `.beat-move.wall` (a short bar), and the seat tints
  `.seat0` / `.seat1` on `move` and `win` beats. `.beat-win` and `.beat-end` are the tall ones.

### Readouts — the board, the clock, the scorebug, the eval bar, the feed

The single `canvas#table` draws one board, centred, sized to the frame, with real geometry per
game: a slotted **Connect Four** frame with discs falling into place; a **Breakthrough** chequered
6×6 with pawn tokens and a capture flash; a **Hex** rhombus of hexagons with the seat-coloured edge
pairs painted along the borders it belongs to; a **Quoridor** 9×9 with grooved wall channels, two
pawns, and walls drawn as planks that snap into their groove.

- **Clock** (`#clock`): `HEX 7×7 · PLY 14 / 49 · SPROCKET TO MOVE`, or
  `GAUNTLET → QUORIDOR 9×9 · PLY 22 / 80 · FINAL`. The rotation arrow appears only when
  `config.rotated` is true.
- **Scorebug** (`#scorebug`): one plate per seat — seat colour chip; `.plate-name` carrying the
  **policy name** (spectator side) with the anonymous alias as a small sub-label; and the per-game
  readout (`TO CONNECT 3` / `PATH 6 · WALLS 7` / `PIECES 9 · ROW 4` / `THREATS 2`).
  `.plate-name` gets `flex: 1 1 auto; min-width: 3.2em` and its label is
  hidden under 640 px — the featured-match iframe on softmax.com is ~360 px wide and names
  otherwise collapse to "…".
- **Say band** (`canvas#table`, under the board): this ply's `say` for **both** seats, in a
  **reserved band** whose height is measured from the cap — `MaxSayLen = 80` runes plus a clamped
  name, wrapped in the render font at the current canvas width — so a full-cap line on both seats
  has room reserved for it whether or not anyone is speaking, and can neither be laid out at a
  negative coordinate nor cut to fit (cogchemists, 2026-08-24). A remark that does not fit on one
  line **wraps** onto the next; it is never ellipsized, because an ellipsis is a label affordance
  and a defect on a sentence (`prompts/30-review-loop.md` item 15). The band is drawn on the
  canvas rather than in the plate because the canvas is what `viewer_smoke.mjs --strict-text-bounds`
  instruments — a DOM remark is invisible to every gate that measures drawn text.
- **Eval bar** (`#evalbar`, inside `#scorebug`): a horizontal bar with a centre tick, filled from
  the centre toward the leading seat by `evalBar(sim)`, captioned **`HEURISTIC`** in 8 px caps —
  it is this repo's own heuristic, not an engine, and the caption says so.
- **Feed** (`#feed`): one block per ply — `PLY 14 · SPROCKET`, then the move in words:
  `drops into d — lands on d3`, `b2 takes c3`, `plays c4`, `pawn to e5`, `wall at e3 (horizontal)`;
  then the quoted `say`. The `win` line reads `Sprocket connects a4–g4`, `Gizmo lines up d3-e4-f5-g6`,
  `Sprocket breaks through on f6`, `Gizmo reaches rank 1`, or — for a starved opponent —
  `Gizmo wins: the opponent has no legal move`, phrased from the seat the `win` event names, which
  is the **victor** (`sim.nim:300`), so every `win` line reads about the same seat. The end
  block names the reason and the ending in words (`complete — ply cap, adjudicated on position` /
  `deadline — stopped after 21 of 80 plies, adjudicated on position`).
- **Endcard** (`#endscreen`): the verdict (`SPROCKET WINS` / `DRAWN`), a reason line, and one row
  per seat with `score`, `standing`, `captures` or `walls used`, and `fallbacks` — supplied by the
  injected `endColumns` (chrome edit #5).
- **Legibility at 360 px is a requirement.** At 360 px the feed collapses behind its toggle, the
  scorebug drops to two stacked plates with the eval bar between them, the board keeps its full
  square footprint (a 9×9 grid at ~36 px a cell), cell labels along the board edge drop to every
  other file, and the clock drops the size word. The renderer fixture in `## Tests` checks
  360 / 640 / 1280 px.

### Art (real, not placeholders)

- `data/font.ttf` + `data/FONT_LICENSE.txt` — copied from babel (Rajdhani).
- `data/arena_floor.png` — copied byte-for-byte from babel (MIT, originally coworld-ctf); the table
  surface under the board.
- `data/soldier_red_front.png`, `data/soldier_blue_front.png` — **new, authored for this repo**
  under babel's filenames (the chrome asks for those two names): 192×192 seat cogs, generated as
  one two-up sheet by `scripts/art/generate_cog_sheet.py` from
  `scripts/art/source/cog_seats_sheet.png` and keyed/split/padded by
  `scripts/art/split_cog_sheet.py`, so each seat holds this ladder's own pieces — the red cog a
  Connect Four disc and a Hex stone, the blue cog a Breakthrough pawn and a Quoridor wall plank
  — rather than babel's spellcasters. They are the two seat avatars in the scorebug plates and
  are **not** byte-copies of babel's (which are 180×192).
- **`data/board_grain.png`** — new, authored for this repo: a 64×64 seamlessly tileable printed-
  board paper grain in `--ink` on transparent, laid under every board so the four games share one
  surface.
- **`data/wall_plank.png`** — new, authored for this repo: a 96×24 lacquered wall plank with an ink
  edge, drawn for each Quoridor wall (rotated 90° for verticals).

Discs, pawns, stones, the hex tiling, the grid and the win path are drawn on canvas (not sprites)
so they stay crisp at every `--hudscale`.

The build hook **`tools/build_replay_viewer.sh`** (a fork of babel's, with the `mkdir -p` fix from
ecos 2026-08-23 so it works on a fresh CI checkout where the parent directory does not exist)
copies into the bundle: `gauntlet_replay.js`, `gauntlet_replay.wasm`, `replay-viewer/index.html`,
`replay-viewer/static_replay.js`, `client/renderer.js`, `client/chrome_common.js`,
`client/chrome.css`, and `assets/{arena_floor.png, soldier_red_front.png, soldier_blue_front.png,
board_grain.png, wall_plank.png, font.ttf}`. It keeps babel's final
`grep -q 'data-replay' static_replay.js` guard and adds `grep -q 'data-replay-loaded' renderer.js`.
It is committed mode `100755`.

---

## Packaging

- **`compose.yaml`** — one service:

  ```yaml
  services:
    board-gauntlet:
      image: coworld-board-gauntlet:latest
      platform: linux/amd64
      build: {context: ., network: host}
  ```

  The manifest image placeholder is derived from the **compose service name**, so it is
  `{{BOARD_GAUNTLET_IMAGE}}` (service name uppercased, `-` → `_`). `{{GAME_IMAGE}}` is not a thing
  (lantern 0.1.0, 2026-08-23).

- **`Dockerfile`** / **`Dockerfile.replay-viewer`** — babel's, with the binary names changed to
  `/bin/board-gauntlet` and `/bin/board-gauntlet-player`.

- **`coworld_manifest_template.json`** — babel's shape, updated to the `coworld` 0.1.42 upload
  contract: `$schema` present; ≥ 3 top-level `tags`
  (`["board-game","perfect-information","zero-sum","two-player","turn-based","llm-driven",
  "openspiel-port","hex","connect-four","quoridor","breakthrough"]`);
  `game.name = "board-gauntlet"` — **the secret namespace is `game.name`**, so
  `ANTHROPIC_API_KEY_URI = "secret://coworld/board-gauntlet/anthropic_api_key"` in the game
  runnable's `env` (without it every hosted episode silently plays scripted — hive, 2026-08-23);
  `game.description` present and `game.tags` **absent** (tags are top-level only);
  `game.owner = "daveey@gmail.com"`;
  `game.runnable = {"type":"game","image":"{{BOARD_GAUNTLET_IMAGE}}",
  "run":["/bin/board-gauntlet"],"env":{…},"source_url":…}`;
  **`game.replay_viewer = {"bundle": "static-replay-viewer"}`** (inside `game`, never top-level);
  no top-level `version`; no `game.display_name`; `episode_timeout_minutes: 20` top-level.

- **`game.config_schema`** — a real JSON Schema, `additionalProperties: false`,
  `required: ["tokens","players"]`. **Every array property carries `minItems`/`maxItems`**:
  `tokens` and `players` both `minItems 2, maxItems 2`. Scalar properties: `num_agents` (integer,
  minimum 2, maximum 2), `game` (`enum ["rotate","connect-four","breakthrough","hex","quoridor"]`,
  default `"rotate"`), `size` (4..11, default 7), `walls` (0..20, default 10), `first` (0..1,
  default 0), `maxPlies` (4..200, default 80), `seed` (integer; 0 means "draw one per episode"),
  `episodeTimeoutSeconds` (60..6000, default 1200), `plySpacingSeconds` (0..60, default 0),
  `turnDelayMs` (0..10000, default 250), `model` (string, default `"claude-sonnet-5"`),
  `maxOutputTokens` (64..2000, default 900), `llmTimeoutSeconds` (5..300, default 30),
  `player_connect_timeout_seconds` (number ≥ 0, default 180).
  **No `game_config` anywhere — variant or fixture — contains a literal `tokens` array**; the
  runner injects it and matriculate rejects "runner-managed tokens" if one is present
  (cogame-knights-archers, 2026-08-26). `config_schema` still *requires* `tokens`.

- **`game.results_schema`** — `additionalProperties: false`, every field of `results` from
  `## The game` required: `names`, `scores`, `outcome`, `game`, `rotated`, `size`, `walls`,
  `first`, `seed`, `winner`, `plies`, `maxPlies`, `standing`, `captures`, `wallsUsed`,
  `illegalReplies`, `fallbacks`, `ending`, `reason`. Every array is `minItems 2, maxItems 2`;
  `scores` items are numbers in −1..1; `reason` is `enum ["complete","deadline"]`; `ending` is
  `enum ["line","board-full","home-rank","no-pieces","no-moves","connection","goal-row","ply-cap",
  "wall-clock"]`; `game` is `enum ["connect-four","breakthrough","hex","quoridor"]` (never
  `"rotate"` — results always carry the resolved game).

- **`game.protocols`** — **both** keys, each a `{"type":"text","value":"…"}` object (bare strings
  are a platform-side validation error the repo CI does not catch — cogame-garble 0.1.0,
  2026-08-24): `player` = the `gauntlet.player.v1` text from `## Server, player, protocol`,
  including "a policy is just a prompt: reuse the published player runnable with `PLAYER_PROMPT`,
  or `PLAYER_SCRIPTED=tactician|hustler` for a baseline"; `global` = the `/global` snapshot shape
  and the three client pages.

- **`game.docs`** — `readme` = `{"type":"text","value":…}` (what the game is, the rotation, how to
  field a policy) and `pages` =
  `[{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…}}]` carrying **all four
  games' rules verbatim from `## The game`**, the rotation rule, the coordinate scheme and move
  notation, the `standing` definitions, the scoring formula, the ending table, and the statement
  that the eval bar is this repo's own heuristic rather than an engine evaluation.

- **Bundled players** — top-level `player[]`, two entries, each with `id` / `type` / `name` /
  `description` / `image` / `run` / `source_url` and
  `resources: {requests:{cpu:"100m",memory:"64Mi"}, limits:{cpu:"1"}}` (the bundled minimum for
  `cpu` is `"1"`; `500m` is rejected at upload — cogame-pistonball 0.1.1, 2026-08-26):
  - `board-gauntlet-player` — the prompt player (no `PLAYER_SCRIPTED`).
  - `board-gauntlet-scripted` — `env: {"PLAYER_SCRIPTED": "tactician"}`.

- **`variants[]` — exactly five. `num_agents` lives inside each variant's `game_config` and never
  at the variant's top level** (`CoworldVariant` is `additionalProperties: false` and the platform
  reads only `game_config.num_agents` — cogame-goofspiel-oshi-zumo 0.1.0, 2026-08-26). Every
  variant carries a `description`.

  | `id` | `name` | `game_config.num_agents` | `game_config` |
  |---|---|---|---|
  | `gauntlet` | The Gauntlet — rotating board | **2** | `{"game":"rotate","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":7,"walls":10,"first":0,"maxPlies":80,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |
  | `connect-four` | Connect Four — 7×6 | **2** | `{"game":"connect-four","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":7,"walls":0,"first":0,"maxPlies":42,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |
  | `breakthrough-6` | Breakthrough — 6×6 | **2** | `{"game":"breakthrough","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":6,"walls":0,"first":0,"maxPlies":80,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |
  | `hex-7` | Hex — 7×7 | **2** | `{"game":"hex","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":7,"walls":0,"first":0,"maxPlies":49,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |
  | `quoridor-9` | Quoridor — 9×9, 10 walls | **2** | `{"game":"quoridor","players":[{"name":"Player1"},{"name":"Player2"}],"num_agents":2,"size":9,"walls":10,"first":0,"maxPlies":80,"turnDelayMs":250,"player_connect_timeout_seconds":180}` |

  In the `gauntlet` variant `size` and `walls` are the *rotation defaults*: `sampleEpisode` resolves
  the game and then, when the resolved game's `size` is outside its own legal range, snaps it to
  that game's default (`connect-four` 7, `breakthrough` 6, `hex` 7, `quoridor` 9) and `maxPlies` to
  that game's cap. A test pins that every rotation outcome of the `gauntlet` variant constructs a
  legal `Sim`.

- **`certification`** — the `breakthrough-6` variant. *Decided, with reason:* under all-scripted
  play it produces the most events of any variant (~45–75 moves), which is what keeps the derived
  smoke replay longer than the viewer soak window (§`## Tests`), and it exercises captures, the
  `home-rank` win and the `no-moves` branch that the other games do not have.

  ```json
  {"game_config": {"game": "breakthrough",
                   "players": [{"name": "Sprocket"}, {"name": "Gizmo"}],
                   "num_agents": 2, "size": 6, "walls": 0, "first": 0,
                   "maxPlies": 80, "seed": 23,
                   "turnDelayMs": 0, "player_connect_timeout_seconds": 180},
   "players": [{"player_id": "board-gauntlet-player"},
               {"player_id": "board-gauntlet-scripted"}]}
  ```

  Both declared runnables occupy a slot — a fixture that seats only one fails cert
  `players_missing` (raid 0.1.2 → 0.1.3, 2026-08-23). `num_agents = 2` here and **2** in all five
  variants; **`<SEATS>` in `tools/ci/docker_smoke.sh` is `2`**, matching the fixture it drives.

- **`.github/workflows/`** — `ci.yml`, `coworld-release.yml` and `coworld-submit.yml` from
  `coworld-builder/templates/`, with `SLUG=board-gauntlet`, `IMAGE=coworld-board-gauntlet`,
  `<SEATS>=2`. The two coworld workflows are the substituted templates **byte for byte** — nothing
  is added to the certify step, which passes `--no-open-report` as the template does — its
  `secret put` step reads the namespace from the manifest's `game.name`, and it keeps the
  load-bearing step order build → certify → **upload-policies** → upload-coworld → secret put.

- **`tools/ci/policies.json`** — the four policies from `## Decisions`; champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` so it is uploaded while daveey-1 is the
  active player. Player-side Bedrock is **not** used (every decision is server-side), so no
  `USE_BEDROCK` is set on the policies; the *game* runnable's `env` carries `ANTHROPIC_API_KEY_URI`,
  which is the thing that must be present or every hosted episode silently plays scripted.

- **Repo** — created public: `gh repo create Metta-AI/cogame-board-gauntlet --public
  --description "A rotating perfect-information ladder: Connect Four, Breakthrough, Hex and
  Quoridor, one game drawn per episode, two cogs, zero sum."` Public is a certification
  prerequisite (`source-resolves` 404s on private).

---

## Tests

Everything below runs in `ci.yml`; the sandbox has no docker, nim, emsdk or browser, so CI is the
only harness. `NIM_TESTS` is left unset — every `tests/*.nim` runs in both debug and `-d:release`.

**`tests/test_sim.nim` — the rules.**

1. **Coordinates round-trip**: `cellIndex(cellName(i)) == i` for every cell of every shipped board;
   `a1` is `(row 0, col 0)`; `g7` on a 7×7 is `(row 6, col 6)`; an off-board name raises.
2. **Rotation**: `sampleEpisode` with `game: "rotate"` maps `seed mod 4` onto
   `["connect-four","breakthrough","hex","quoridor"]` for 400 seeds; it is **idempotent** (running
   it twice changes nothing); every rotation outcome of the `gauntlet` variant's `game_config`
   constructs a legal `Sim`; and an unpinned `seed` is replaced by a concrete non-zero seed that is
   recorded in the config.
3. **Connect Four**: a drop lands on the lowest empty cell of its file; a full file is not in
   `legalMoves`; all four line directions are detected on the completing ply and the `win.path`
   names exactly the four cells; a full board with no line ends `board-full` with `scores == [0,0]`;
   `standing` counts exactly 69 windows on a 7×6 board.
4. **Breakthrough**: straight-forward onto an occupied cell is illegal, diagonal onto an enemy is a
   capture and removes that piece, diagonal onto own piece is illegal, backwards is illegal;
   reaching the far home rank ends `home-rank`; taking the last piece ends `no-pieces`; a
   hand-built blocked position ends `no-moves` with the **starved** seat losing.
5. **Hex**: `c4` on a 7×7 has exactly the six neighbours `b4, d4, c3, c5, b5, d3`; `a1` has exactly
   `b1, a2`; adjacency is symmetric for every pair; over 300 seeded random full boards **exactly
   one** seat has a winning connection — never zero, never both; `distToWin` is 0 the moment a
   connection exists and 99 when the opponent has cut every route.
6. **Quoridor**: a wall on an occupied anchor, a wall re-blocking an already-blocked step, and a
   wall that leaves either pawn with no path are all rejected; over 200 seeded episodes **every**
   position reachable after a wall placement still has a path for both pawns; the straight jump is
   offered when legal and the two perpendicular diagonals **only** when the straight jump is
   blocked or off board; a pawn always has ≥ 1 legal move; reaching the goal rank ends `goal-row`.
7. **Turn order**: `mover` alternates strictly on every ply in every game; there is no position in
   which the same seat moves twice.
8. **Legality**: `applyMove` raises for every move not in `legalMoves(sim)`, for all four games,
   over 300 seeded positions; `normalizeMove` accepts the tolerated spellings listed in the reply
   schema and rejects everything else (including a legal-looking move of a *different* game).
9. **Termination bound**: over 300 seeded episodes × all four games × both baselines, every episode
   ends with `plies ≤ maxPlies` and a legal `(reason, ending)` pair.
10. **Scoring**: `scores` sums to exactly 0 in 300 seeded episodes across all four games; `+1`
    exactly for the seat named by the ending table; a draw gives `[0, 0]` and only ever on
    `board-full`, `ply-cap` or `wall-clock` with equal `standing`.
11. **`standing` and the eval bar**: `standing` is defined and finite for both seats in every
    reachable position of all four games; a Connect Four window containing both colours contributes
    0; a Hex seat that has just placed on its own shortest route never increases its `distToWin`;
    `evalBar` stays inside −1..1.
12. **Every variant's and the cert fixture's `game_config` constructs a `Sim`** (cogame-collab-cooking
    0.1.1, 2026-08-25 — a fixture-only test hid a defect that killed every league episode).

**`tests/test_bot.nim` — the scripted baselines (bounded orders / legality).**

13. Over 200 seeded episodes × all four games × both baselines: **every** move a baseline produces
    is in `legalMoves(sim)` at the moment it is produced, is at most 12 characters, and every
    episode terminates; no baseline ever emits `say` or `notes`.
14. `tactician` beats a seeded uniform-random legal mover over 200 episodes per game (mean score
    > 0), so the fillers are a real opponent rather than noise.
15. `tactician` and `hustler` disagree on at least 30 % of plies, per game — 25 % for Connect
    Four, the recorded exception in §*The two scripted baselines*.
16. `tactician` never walks past an immediate win and never allows an immediate loss when a safe
    move exists — asserted on hand-built positions in all four games.
17. The scripted-only cert fixture (`breakthrough-6`, 2 seats, `turnDelayMs = 0`) completes in
    **under 50 s** of wall clock, pinning it inside `coworld certify`'s 60 s default
    (cogame-commons-family 0.1.0, 2026-08-24).

**`tests/test_replay.nim` — record → re-derive, and the bytes.**

18. For **every** end reason/ending pair — all eight `complete/*` endings and `deadline/wall-clock`
    — record an episode, run `replayMatch` over its events, and assert every frame's
    `boardStateJson` is identical to the live one. A wall-clock stop must re-derive because
    `settle` is the same proc on both paths (particle-worlds `13c66d7`, 2026-08-26).
    **One recorded exception: `complete/no-moves`.** It is unreachable from the standard
    Breakthrough opening — a piece on rank 2 always has a rank-1 square to step to or capture on,
    and a piece that reached rank 1 has already won — so no recorded episode ends that way and
    `replayMatch`, which re-runs `initSim(config)` from the standard opening, cannot be handed one.
    It is covered instead from a hand-built position, applied to two copies of the sim, asserting
    `boardStateJson` and `resultsJson` are identical on both and that a second `settle` cannot
    change a settled episode. The path itself is re-derivable: `advance` emits the `win` event and
    `replayMatch`'s `evWin` branch checks seat / how / path like any other.
19. `replayMatch` **raises** when a recorded `move.mkind`, `move.capture`, `win.seat`, `win.how` or
    `win.path` disagrees with the re-derivation.
20. **Strict UTF-8**: build an episode whose every `say` and `notes` is a multi-byte string at
    exactly the cap (80 / 400 runes of `日` plus an emoji), serialise the replay, and assert
    `validateUtf8(bytes) == -1` and that a strict `parseJson` round-trips it. Rune-boundary
    truncation, not byte truncation.
21. The replay payload contains `protocol`, `names`, `policyNames`, `config.game`,
    `config.rotated`, `config.size`, `config.walls`, `config.first`, `config.seed`,
    `config.maxPlies`, every event and `results` — the fields the viewer needs, asserted by key —
    and `config.game` is never `"rotate"`.

**`tests/test_manifest.nim` — packaging invariants, parsed from the template.**

22. `num_agents` is present, a positive integer, equal to `2`, and equal to `len(players)` in **all
    five** variants and in `certification.game_config`; **no variant carries `num_agents` at its
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

26. Builds the production image, starts one game container and **2** player containers on a per-run
    network with the certification fixture, and asserts: the game exits 0; `results.json` is written
    and validates against `results_schema`; the replay is written and **parses as strict JSON**;
    `SMOKE_SEATS=2` agrees with `certification.game_config.num_agents`; and **every player
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
    throws mid-playback (cogball 0.1.4); the smoke replay is long enough for it: the
    `breakthrough-6` fixture emits ≈ 50–78 events (1 `start` + 45–75 `move` + 1 `win` + 1 `end`) at
    the renderer's dwell of 700 ms (quiet move) / 1100 ms (capture) / 1500 ms (`win`, `end`) ≈
    **40 s of playback > 10 s of soak** (ecos, 2026-08-23 — a replay shorter than the soak reads as
    frozen). Every board is fixed and fully on-frame, so `--strict-text-bounds` stays on.

28. **Renderer fixture step** (`tools/ci/renderer_fixture.html`, its own
    `viewer_smoke.mjs --url … --strict-text-bounds` run): CI replays carry **zero LLM text** —
    `docker_smoke.sh` runs without a key and the scripted baselines emit no `say` or `notes` — so
    nothing that plays a CI replay ever exercises the say band or the quoted feed lines. The fixture
    loads the **shipped** bundle's own `chrome.css`, `chrome_common.js`, `renderer.js` and
    `assets/` — it is copied **into** `dist/static-replay-viewer/` before it runs, so every relative
    path resolves to the artifact CI is about to publish — shims only the wasm entry, feeds
    `GauntletRenderer.attachReplay` a synthetic payload **for each of the four games** with a
    full-cap 80-rune `say` on both seats and the longest plausible policy names, and drives the
    page's own text path at **360, 640 and 1280 px** (particle-worlds `46cf69d`, 2026-08-26 — a
    fixture that re-implements the drawing gates nothing). It asserts its own remarks are still
    exactly `MaxSayLen` runes before it draws, and fails via `data-replay-error` if they are not.
    It runs as the **top-level document**, not in an iframe: `viewer_smoke.mjs` installs its canvas
    wrapper with an init script but reads the tally back with `page.evaluate()`, which only ever
    runs in the main frame, so an iframe fixture would report zero canvas text and gate nothing.
    It therefore retypes the shipped `index.html`'s markup (the same ids, in `#layout` / `#stage`)
    rather than reusing that file.

29. **Chrome scope check** (`tools/ci/chrome_scope_check.mjs`, same job): asserts that no identifier
    exported by `client/chrome_common.js` is re-declared as a top-level `function` or `var` in
    `client/renderer.js` (tandem, 2026-08-23), that `client/renderer.js` declares no `markBeat`,
    that every beat kind the sim can emit (`start`, `move`, `win`, `end`, plus the `capture` and
    `wall` modifiers) has a matching CSS rule in `client/chrome.css`, and that
    `client/chrome_common.js` still contains the copied-region markers listed in §Chrome
    provenance, so a future "tidy-up" that rewrites the chrome fails loudly.

---

## Out of scope (v1)

- **Amazons, Lines of Action, Pentago, Othello, Clobber, Havannah, Y, TwixT, Ultimate
  Tic-Tac-Toe.** Amazons fails the printable-legal-move rule (≈2 000 move/arrow pairs at the
  opening). The rest are each a fifth, sixth, seventh board with their own geometry, their own
  terminal test and their own art, and shipping nine mediocre games is worse than shipping four
  good ones; the sim's per-game module boundary (`games/*.nim` exporting four procs) is exactly
  what a later game plugs into.
- **Go 9×9.** Needs liberties, suicide, positional superko, pass handling and Tromp-Taylor scoring
  with dead-stone resolution — a second engine, and the game where a prompt policy is least
  competent. Deliberately excluded rather than half-implemented.
- **Quoridor with 3 or 4 seats.** `num_agents` is exactly 2 in every variant; a 4-seat Quoridor is
  not zero-sum between pairs, needs a different score vector and a different anti-collusion story.
- **The swap (pie) rule, randomised first move, and openings books.** Seat 0 always opens; the
  league's round robin, which seats each policy in both slots, is what balances the opening
  advantage.
- **Time-control variants.** The idea's "time control per move is the lever" is real, and
  `llmTimeoutSeconds` is that lever, but v1 pins it at 30 s in every variant so the ladder compares
  like with like. Blitz (5 s) and classical (120 s) variants are a v2 knob, not a v1 promise.
- **An external reference engine and a true eval bar.** No OpenSpiel, no Gnugo, no solver. The bar
  is this module's own `standing` heuristic and is labelled `HEURISTIC` on screen.
- **Repetition, fifty-move and other draw-by-cycle rules.** None of the four games needs one to
  terminate: Connect Four and Hex fill, Breakthrough and Quoridor are adjudicated by the ply cap on
  `standing`. A repetition rule would be a fifth ending with no gameplay effect.
- **Scoring anything but the outcome.** `standing`, `captures`, `wallsUsed`, `illegalReplies` and
  `plies` are reported in `results`, drawn in the viewer, and never enter `scores`.
- **Any inter-seat channel.** Seats never exchange text; `say` is spectator-facing and is never
  shown to the opponent; `notes` are fed back only to their author.
- **RL / vector policies.** Policies are prompts or the two named scripted baselines; there is no
  observation tensor and no action-space export.
- **A live spectator theatre beyond `/client/global`**, replay editing, highlight clipping, and any
  replay-viewer pod. Replays are the static wasm bundle, always.
- **Replay protocol migration.** The viewer reads `gauntlet.replay.v1` and nothing else; a future
  version bump adds a reader, it does not silently reinterpret old bytes.
