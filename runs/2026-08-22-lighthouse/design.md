# Lighthouse: one cog sees the maze, three cogs are blind

Fork of **`Metta-AI/cogame-babel`** (read at `/workspace/starters/cogame-babel`, version
0.1.4) — the current best parley-stack template: a Nim game server implementing the Coworld
runtime contract, a pure `sim` module shared by server / tests / wasm viewer, LLM-driven
decisions where **a policy is just a prompt**, an always-available scripted baseline, and the
parley broadcast chrome around a canvas stage. Chosen because Lighthouse is a discrete-tick
game whose one channel between the seats is *text*, and the parley-stack `PLAYER_PROMPT` vs
`PLAYER_SCRIPTED=<baseline>` policy interface covers all four seats. **Every convention there
holds here unless this note says otherwise.** Two pieces come from babel's descendant
`Metta-AI/cogame-bullwhip` (`/workspace/starters/cogame-bullwhip`), which babel predates: the
simultaneous-decision parallel batch (`src/bullwhip/llm.nim:419-472`, `decideAll` over
`curly.makeRequests`) and its tick-shaped game loop (`src/bullwhip/server.nim:262-318`).
Repo: **public** `Metta-AI/cogame-lighthouse` (public is a certification prerequisite —
`source-resolves` 404s on a private repo).

Source idea, verbatim:

> 02 Lighthouse — one cog sees the whole maze and cannot move; the others move blind
>
> A keeper has the map and a text channel; three runners have a 3x3 view and must collect keys
> and exit before the tide. The keeper's words are the only bridge from global to local; every
> message costs a tick. Scored as a team; keeper and runner seats are separate policy slots.
>
> Seats: 4 (1 keeper + 3 runners)
> Motive: cooperative, asymmetric roles
> Policy interface: LLM prompt (keeper) + RL vector (runners)
> Fills gap: structural info asymmetry / grounded instruction-following
> Integrity (anti-collusion): Keeper and runners never share an account; keeper ranked by
> cross-play mean over stranger runner pools, so a private keeper-runner protocol can't be
> pre-baked.
>
> Replay plan (watchability): God-view maze with each runner's little fog cone overlaid; the
> keeper's words run as radio subtitles with a visible per-message tick cost; the tide rises on
> screen as creeping water. Corner thumbnails show each runner's cramped 3x3 view — dramatic
> irony is the engine.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

**Rebinding of the idea's "RL vector (runners)".** All four seats are LLM-prompt policies with
a scripted fallback, in the same image, env-switched (`PLAYER_PROMPT` vs
`PLAYER_SCRIPTED=<baseline>`). Reason: the platform's policy contract on this stack is a
prompt, there is no RL-vector transport in the parley stack, and the interesting research
content — grounded instruction-following across an information asymmetry — is fully expressed
with a token-move reply schema. No RL-vector interface is designed anywhere in this note.

There is **no OPEN section**: every rule the idea leaves loose is one the rails say the designer
settles (seat count, scoring formula, parameter tuning, viewer composition, policy prompts), and
each such call is decided below with its reason.

---

## The game

**Seats: `num_agents` = 4, fixed.** Slot 0 is the **Keeper**; slots 1, 2 and 3 are **Runners**
(the idea's "keeper and runner seats are separate policy slots" — a fixed slot mapping is what
lets the league seat a keeper policy deliberately). Seats play under anonymous cog aliases;
policy names are spectator-side only (§Two name spaces, below).

**Board.** A rectangular grid, `width` × `height`, default **11 × 9**, both odd. `x` runs
0..10 left→right, `y` runs 0..8 **top→bottom** (y = 0 is the top). Tiles are `wall` or `floor`.
(The default was 17 × 11 when this note was accepted; see §Tuning revision.)

**Maze generation** (all from `config.seed`, one `Rand` stream initialised
`initRand(int64(seed) * 7919 + 17)` exactly as babel `sim.nim:202`, drawn in this order so a
pinned seed reproduces the episode bit-for-bit):

1. Every tile starts as `wall`. **Rooms** are the tiles with odd `x` and odd `y`
   (5 × 4 = 20 rooms at the default size).
2. **Randomised-DFS (recursive backtracker)** over rooms: start at room `(1, height - 2)`
   (= `(1, 7)`); at each step shuffle the four neighbouring rooms (`±2` in x or y), recurse into
   the first unvisited one, carving both it and the wall tile between. The result is a
   **perfect maze** — exactly one path between any two floor tiles, no loops. Reason: a perfect
   maze makes the keeper's global view genuinely load-bearing (a blind runner cannot solve it by
   luck) and makes the wall-following runner baseline mediocre-but-not-useless, which is exactly
   the competence floor a champion prompt should beat.
3. **Exit.** `exitX` = a seed-drawn odd x in `1 .. width - 2`. The tile `(exitX, 0)` is carved to
   `floor`; it is the **exit tile**, the only gap in the outer border.
4. **Runner starts.** Three distinct rooms on the bottom room row `y = height - 2` (= 7), drawn
   from the seed subject to pairwise `|Δx| ≥ 4`; retry the draw up to 50 times, then fall back to
   the leftmost, middle and rightmost bottom rooms. Runner 1 → the leftmost of the three drawn,
   runner 2 → the middle, runner 3 → the rightmost.
   **At the shipped 11 × 9 this draw is degenerate and the starts are the same on every seed:**
   the bottom room row is `{1, 3, 5, 7, 9}` and `{1, 5, 9}` is the only triple pairwise ≥ 4
   apart — which is also the fallback — so every episode starts at `(1,7)`, `(5,7)`, `(9,7)`
   (verified over 13 seeds). That is a consequence of the pinned separation at this width, not a
   broken draw; the anti-pre-baking argument in §Two name spaces rests on the maze, the exit, the
   key set and the aliases, all of which do vary per seed. The draw binds again on a wider board.
5. **Keys.** `keyCount` = **3**. Candidates are the **dead-end rooms** (rooms with exactly one
   open neighbour) that are not a start room, not the exit tile, not adjacent to the exit tile,
   and have `y ≤ height - 4` (= 5 at the default size — keys in the bottom two rows would drown
   before anyone could reach them). Sort candidates by BFS distance from the exit tile,
   **ascending**; seed-draw 3 of the top 8 subject to pairwise BFS distance ≥ 6, retrying up to 50
   times; on failure take the 3 nearest candidates outright. (Ascending, not descending: on a
   *perfect* maze the far dead ends cannot be reached and returned from inside the tick budget —
   see §Tuning revision.) If fewer than 3 candidates exist at all, fall back to the floor tiles
   with `y ≤ height - 4` of greatest exit distance, taking the farthest that are pairwise ≥ 6
   apart before topping up. The fallback applies the same "not the exit tile, not adjacent to it,
   not a start" exclusions as the dead-end candidates, so every key placement satisfies the same
   invariants however it was drawn.
   **At the shipped 11 × 9 the fallback is the NORMAL path, not the exception.** A 5 × 4-room maze
   yields 0–2 eligible dead ends (measured on the fixture seeds: 2, 2, 0, 1), always fewer than
   `keyCount`, so keys are in practice the farthest floor tiles above the drowning rows, pairwise
   ≥ 6 apart. That still places them deep in corridors a blind runner cannot search, so the
   keeper's map stays load-bearing and the measured competence numbers in §Tuning revision hold;
   but the dead-end rule above should be read as the preference, not the usual outcome. A board
   large enough for the dead-end draw to bind (13 × 9 yields 1–4, 17 × 11 yields 3–7) is also large
   enough for the path-length problem §Tuning revision documents, which is the trade this board
   size settles.
6. **The keeper occupies no tile.** It is in the lantern room, off-board. It cannot move; it has
   no position; there is no keeper action other than speaking or staying silent.

**The one channel.** The keeper may transmit one text message per tick, broadcast to all three
runners, delivered at the **start of the next tick**. Nothing else crosses from keeper to
runners. Runners have **no channel at all** — not to the keeper, not to each other. The bridge
is one-way by design; that is the asymmetry the game is about.

**"Every message costs a tick", made precise.** There is one monotone counter, the **`clock`**,
and the tide is a pure function of it. At the end of each tick the clock advances by
`1 + (the keeper transmitted this tick ? 1 : 0)`. So a tick on which the keeper speaks costs the
team **two** clock units of tide instead of one. Runners always move; talking never freezes
them. This is a single-valued rule, is visible on screen (the water jumps a beat), and puts the
whole verbosity trade-off on one number.

**Tide.** `tideDelay` = **10**, `tidePeriod` = **7** (`spring-tide` uses 5).

```
tideRows(clock) = clamp((clock - tideDelay) div tidePeriod, 0, height)
waterLine       = height - tideRows          # y of the topmost flooded row; == height when dry
a tile (x, y) is flooded  ⇔  y >= waterLine
floodClock      = tideDelay + height * tidePeriod = 10 + 9 * 7 = 73
```

Water rises from the bottom row upward and never recedes. Row `y` floods at
`clock = tideDelay + tidePeriod * (height - y)`. At the default settings: the bottom row
(`y = 8`) floods at clock 17, the runners' start row (`y = 7`) at clock 24, then rows 6, 5, 4, 3,
2 and 1 at clocks 31, 38, 45, 52, 59 and 66, and the exit row (`y = 0`) at clock 73, which is
`floodClock`. Under `spring-tide` (`tidePeriod` 5) the same milestones are 15, 20, 25, 30, 35, 40,
45, 50 and 55 — strictly harsher on every row.

**Ticks.** `maxTicks` = **45** (cert fixture 10). Because `clock ≥ tick` always, a fully silent
keeper leaves the team 45 ticks with the water at `waterLine = 4` by the end; a keeper who speaks
every single tick floods the entire board by tick 37. That spread — 37 to 45 usable ticks,
bought with silence — is the game.

**Resolution order.** Tick `t` (0-based) resolves in exactly these twelve numbered steps:

1. **Observe.** The server builds each seat's observation from the state as it stands at the
   *start* of tick `t` (§Per-seat observation). Runners whose status is `escaped` or `drowned`
   are not observed and not queried.
2. **Decide.** All active seats' LLM calls go out as **one parallel batch**
   (`curly.makeRequests`) — see §Decisions. Each active runner returns a `move`; the keeper
   returns `transmit` + `message`. Every seat may return `notes`.
3. **Keeper transmit.** If the keeper's reply has `transmit == true` **and** a non-empty
   `message` after truncation, set `spoke = true`, record an `evSay` event, and queue the
   message for delivery at the start of tick `t + 1`. Otherwise `spoke = false` and no `evSay`
   is written (silence leaves no event; the feed shows the gap).
4. **Runner moves**, in seat order 1, 2, 3 (order is immaterial — runners do not block each
   other — but is fixed for determinism). For runner `r` with move `m`:
   a. `target = pos(r) + delta(m)`; `delta(WAIT) = (0, 0)`, `N = (0, -1)`, `S = (0, +1)`,
      `E = (+1, 0)`, `W = (-1, 0)`.
   b. If `target` is out of bounds, is a `wall`, or is currently **flooded**, then
      `target = pos(r)` and the move is recorded with `blocked = true`. A blocked move is a bump,
      **not** an illegal reply: no retry, no scripted fallback, the runner simply loses the tick.
      Runners may not walk into water; the water has to catch them.
   c. `pos(r) = target`.
5. **Key pickup**, in seat order 1, 2, 3. If runner `r`'s tile holds an uncollected key, the key
   is collected: remove it from the floor, `keysCollected += 1`, `keysHeld(r) += 1`, record
   `evKey`. A runner carries any number of keys; keys are never dropped.
6. **Gate.** If `keysCollected == keyCount`, `gateOpen = true`, permanently. The tick on which it
   flips records `gateOpen: true` on its `evTick`; the viewer and the feed announce it.
7. **Exit**, in seat order 1, 2, 3. If runner `r` stands on the exit tile **and** `gateOpen`,
   it escapes: status `escaped`, removed from the board, `escapedCount += 1`, record `evEscape`.
   On a closed gate a runner standing on the exit tile simply waits there (and drowns with
   everyone else if the water reaches row 0).
8. **Clock.** `clock += 1 + (spoke ? 1 : 0)`.
9. **Tide.** Recompute `tideRows` and `waterLine` from the new `clock`.
10. **Drown.** Every still-active runner whose tile is now flooded gets status `drowned`, is
    removed from the board, `drownedCount += 1`, and records `evDrown`.
11. **Tick record.** Append `evTick` carrying the post-resolution board (§Event vocabulary),
    then `tick += 1`.
12. **End check**, in this order:
    a. `escapedCount + drownedCount == 3` → settle, `reason = "complete"`.
    b. `clock >= floodClock` → settle, `reason = "complete"` (step 10 has already drowned
       everyone still on the board; this is a guard, not a separate outcome).
    c. `tick >= maxTicks` → settle, `reason = "timeup"`.
    d. Otherwise continue to tick `t + 1`.

**Collisions.** Runners **do not collide** — any number may stand on one tile, and two runners
may swap tiles in one step. Reason: in a maze of one-wide corridors, blocking creates deadlocks
and swap-conflict rules that add bookkeeping and remove drama; letting runners pass through each
other costs nothing the audience can see and removes an entire class of resolution-order bugs.

**Scoring.** Fully cooperative and identical for every seat:

```
K = keysCollected                            (0 .. keyCount)
E = escapedCount                             (0 .. 3)
B = if E == 3: clamp(1 - clock / floodClock, 0, 1) else 0

teamScore = 6 * (K / keyCount) + 10 * E + 6 * B          # range [0, 42]
```

**The sign is positive: higher is better.** `results.scores[i] = teamScore` for **all four
seats**, keeper included. Nothing is subtracted for drowning — an escape is worth 10 and a
drowned runner earns nothing, which is penalty enough, and a floor of 0 keeps the ladder's
arithmetic simple. `B` is charged against the **clock**, not the tick count, so a chatty keeper
pays for its words in the time bonus as well as in tide. **The league ranks by mean episode
score, descending.** Because every seat carries the same number, a keeper's rank is exactly the
mean of the teams it made work — which is what makes the idea's integrity plan (cross-play mean
over stranger runner pools) meaningful at the league layer.

**Endings and `results.reason`.** Exactly three legal values, and no others:

| `reason` | when | scores |
|---|---|---|
| `complete` | every runner resolved (escaped or drowned), or the whole board flooded | as reached |
| `timeup` | `tick == maxTicks` with at least one runner still active | as reached |
| `deadline` | the wall-clock play budget (60 % of `episodeTimeoutSeconds`) expired before either | as reached |

`deadline` is the degrade-never-hang path (§Decisions) and is declared **acceptable** for
phase-60 verification, but should be rare: the arithmetic below leaves ~160 s of headroom.

**Per-seat observation — exactly what is visible and what is hidden.**

*The keeper (slot 0) sees, every tick:*

- The **whole grid**, rendered as `height` lines of `width` characters, using this glyph set:
  `#` wall · `.` floor · `~` flooded · `K` uncollected key · `E` exit, gate closed ·
  `O` exit, gate open · `1` `2` `3` a runner, by runner number. Precedence is runner over exit
  over wall over water over key over floor: in particular an uncollected key on a **flooded**
  tile renders `~`, not `K`, because nobody may step onto it — the glyph is the only thing a
  blind runner has to go on, and the `wallhug` baseline reads legality straight off it.
- Per runner: alias, `(x, y)`, status, the move it made last tick and whether it was blocked,
  and how many keys it is carrying.
- Tide: `tideRows`, `waterLine`, and — stated explicitly in the prompt, because it is the whole
  decision — **`ticksUntilNextFlood` computed both ways**: "the next row floods in N ticks if you
  stay silent, in M ticks if you transmit."
- `tick`, `maxTicks`, `clock`, `floodClock`, `keysCollected`/`keyCount`, `gateOpen`.
- Its own private notes, and a transcript of its last 5 transmitted messages with the tick each
  was sent on.

*The keeper does NOT see:* any runner's private notes.

*Each runner (slots 1–3) sees, every tick:*

- Its **3 × 3 window** centred on itself: 3 lines of 3 characters, same glyph set, with `@` for
  itself and `1`/`2`/`3` for another runner in view. Anything off-grid renders as `#`.
- `keysIHold`, the team's `keysCollected`/`keyCount`, and `gateOpen` (the gate opening is a
  physical event — a horn — heard by everyone).
- `tick` and `maxTicks`.
- `inbox` — the keeper's message transmitted last tick, verbatim, or `(silence)`.
- `standing` — the most recent non-empty keeper message and its age in ticks, so a runner under
  a standing order is not amnesiac between transmissions.
- Its own private notes and its own last 6 moves with their `blocked` flags.

*A runner does NOT see:* the map, its own coordinates, its own heading in absolute terms, the
other runners' positions or statuses (except what falls inside its 3 × 3 window), the keeper's
view, any other seat's notes, `clock`, `tideRows`, or `waterLine`. It learns about the water only
by seeing `~` in its window. A runner knows the clock is running (`tick` / `maxTicks`) but not how
much water is behind it.

**Reply schema.** Every free-text field has a rune cap and is truncated on **rune boundaries**
(never byte boundaries — a byte-cut multi-byte rune produces replay bytes that render in a
browser and fail a strict JSON parser; see `playbooks/make-coworld.md` §Common mistakes). The
truncator is bullwhip's `cleanText(text, limit)` (`src/bullwhip/llm.nim:385-390`): strip, and if
`runeLen > limit`, `runeSubStr(0, limit - 1) & "…"`.

*Keeper reply:*

```json
{"transmit": true, "message": "Sprocket N; Gizmo E; Ratchet hold", "notes": "…"}
```

- `transmit` — boolean. Absent ⇒ inferred as `message` non-empty after truncation.
- `message` — free text, cap **160 runes**. Newlines are collapsed to single spaces before
  truncation. Empty or whitespace-only ⇒ `transmit = false` regardless of the flag.
- `notes` — free text, cap **400 runes**, private, fed back next tick. Absent or empty ⇒ the
  previous notes are kept.

*Runner reply:*

```json
{"move": "N", "notes": "…"}
```

- `move` — one of `N`, `S`, `E`, `W`, `WAIT`. Accepted case-insensitively, with surrounding
  whitespace stripped, and with the aliases `NORTH`/`UP`, `SOUTH`/`DOWN`, `EAST`/`RIGHT`,
  `WEST`/`LEFT`, `STAY`/`HOLD`/`H`/`WAIT`. `H` is on the list because champion #2
  `lighthouse-pilot` is specified with the grammar `"<Alias>:<N|S|E|W|H>"`, and the same
  `parseMoveToken` reads both a runner's reply and the direction a keeper's message gives a
  `wallhug` runner: without `H` the pilot keeper's own hold order would not parse. Anything
  else (`"NE"`, `42`, missing) is a **parse failure** and takes the retry-then-fallback path.
- `notes` — free text, cap **200 runes**, private, fed back next tick.

`{"type":"prompt","prompt":…}` frames from the player container are capped at **4000 chars**
(babel `server.nim:33`, `MaxPromptLen`), truncated on rune boundaries here too.

### Tuning revision (2026-08-22, build phase)

The constants this note was accepted with made its own §Tests `test_bot` thresholds unreachable.
The coordinator approved a retune as a rails parameter-tuning call; the sections above are written
with the shipped values, and this block records what changed and why.

**Originally pinned:** board **17 × 11**; §The game step 5 sorted key candidates by exit distance
**descending** (the farthest dead ends); `tidePeriod` **4** (`spring-tide` **3**), giving
`floodClock` 54; `lantern` step 4 ordered the first step of the shortest path **from the runner's
current tile**; `lantern` step 6 transmitted on `tick mod 2 == 0` **or** any of three exceptions,
with no repeat-suppression and no not-twice-in-a-row rule.

**The measurement.** An oracle over the real seeded boards computed, for each seed, the minimum
over key→runner assignments of the maximum over runners of `dist(start, key) + dist(key, exit)` —
the tick count a *perfect* keeper with *perfect* runners, no message lag and no tide would need
before all three can be at the exit, since the gate needs all three keys before anyone can leave.
On the original 17 × 11 board that is **55 / 47 / 53 / 81** ticks for the fixture seeds
`[1, 7, 42, 1234]`; over sixty seeds the best is 47 and the worst 93. `maxTicks` is 45, and
`sampleEpisode` caps it at `EpisodeCallBudget div CallsPerTick` = **55**. So `escaped == 3` was
unreachable **by any policy at all**, LLM or scripted, on every seed. The note's own escape hatch
(§Tests `test_bot` #4: raise `tidePeriod` from 4 to 5) only moves water and cannot fix a path
that is longer than the tick budget: a sweep of `tidePeriod` 4, 5, 6, 8, 10 and 14 against
`maxTicks` 45 and 55 never produced more than 2 escapes on 1 of the 4 seeds. Separately, with
three runners the original transmit condition (b) fires whenever *any* of them turns a corner,
which measured a **64–68 %** talk rate against this note's own ≤ 60 % bar.

**Shipped instead:** board **11 × 9** (still odd × odd and ≥ 9, and inside this note's own
`config_schema` ranges, so the schema is unchanged); key candidates sorted **ascending** (the
nearest dead ends), every other placement filter unchanged; `tidePeriod` **7** (`spring-tide`
**5**), giving `floodClock` 73; `lantern` step 4 aims one step ahead, at the tile the runner will
occupy when the words land; `lantern` step 6 never transmits twice in a row and lets an exception
break the rhythm only to say something new.

**Measured outcome** with `lantern` + three `wallhug` over the fixture seeds `[1, 7, 42, 1234]`:
all three keys collected on **4 of 4** seeds, all three runners out on **3 of 4**, talk rate
**51–52 %**, instruction-following **89 %**, team scores **26–39** of a possible 42, episodes
25–37 ticks with the tide still drowning a runner on one seed. Every threshold in §Tests passes
as written; none was weakened. Everything else in this note — the twelve numbered resolution
steps, the tide formula, the scoring formula and its sign, the event vocabulary, both protocols,
the observation split, the reply schema and its rune caps, `maxTicks` 45, `keyCount` 3,
`num_agents` 4, the viewer composition, the champion prompts and the policy set — is unchanged.

---

## Decisions: LLM with scripted fallback

Transport, credential resolution (Bedrock sidecar bearer → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI`), the Bedrock model candidate list with Haiku first, `extractJsonObject`,
the "no credentials ⇒ every seat scripted, immediately, no retries, no network waits" rule, the
`output_config.effort` guard for Haiku 4.5, `maxOutputTokens` = 900 and the system prompt's
"your reply must begin with `{` and end with `}`" demand are all ported **verbatim** from babel
`src/babel/llm.nim:16-126, 327-391`. Model default `claude-sonnet-5`; `llmTimeoutSeconds`
default **18**.

**One parallel batch per tick.** Decisions are simultaneous by rule, so the server fires *all
active seats' requests as a single `curly.makeRequests` batch* — grafting bullwhip's `decideAll`
(`src/bullwhip/llm.nim:419-472`) in place of babel's one-seat-at-a-time `decide`. Four
round-trips per tick issued in parallel, not in series; 45 ticks is ~45 sequential waits, not
180. Querying seats sequentially is the documented way to blow the 720 s play budget.

**Degrade, never hang.** In order:

1. A seat whose reply fails to parse, or whose `move` is not one of the five tokens, is put in a
   **second, smaller batch** carrying the hint `"Your previous reply was invalid. Respond with
   ONLY the requested JSON object, with \"move\" one of N, S, E, W, WAIT."` (keeper variant names
   `transmit` and `message`). That is **one retry**, no more.
2. Anything still failing after the retry falls back to the **role-appropriate scripted action**
   for that tick (`wallhug` for a runner seat, `lantern` for the keeper seat), logged
   `scripted: true` on that seat's slot in the tick event and printed as
   `lighthouse llm: seat N falling back to scripted decision`.
3. A **blocked move** (walked into a wall or water) is never a fallback — the reply was legal,
   the world said no.
4. Each batch is bounded by `llmTimeoutSeconds` (18 s), so a tick's worst case is 2 × 18 = 36 s
   of network.
5. The **play deadline is checked before every tick's batch**: `PlayBudgetFraction = 0.6` of
   `COWORLD_TIMEOUT_SECONDS` if the env carries it, else of `config.episodeTimeoutSeconds`
   (default 1200) — 720 s measured from `gameStart`, exactly as babel `server.nim:234, 278-292`.
   Past it the sim calls `endEarly()` → `reason = "deadline"`, breaks out **between ticks**, and
   writes results and the replay. A short honest episode always beats a long one that is
   discarded.
6. The player-connect wait is bounded by `player_connect_timeout_seconds` (default 180); the
   episode starts with whoever connected, and any seat that never delivered a prompt plays its
   role's baseline.

**Budget arithmetic, out loud.** One parallel batch of ≤ 4 Claude calls at 900 max output
tokens measures 6–12 s on this stack. Worst realistic case:

```
45 ticks × 12 s/tick            = 540 s   (LLM, parallel batches)
45 ticks × 250 ms turnDelayMs   =  11 s   (spectator pacing)
player connect (observed ~5 s)  =   5 s
artifact write (results+replay) =   2 s
                                  ------
                                   558 s   <  720 s  (60 % of 1200 s)
```

Headroom ≈ 162 s ≈ 13 slow ticks; and if even that is eaten, the pre-tick deadline check settles
the episode at 720 s, so the absolute ceiling is 720 + 36 (one in-flight tick) + 2 ≈ 758 s,
comfortably inside the platform's 1200 s kill. `sampleEpisode(config)` enforces the cap in code
(idempotent, exactly as babel `sim.nim:134-146`):

```
EpisodeCallBudget = 220 ; CallsPerTick = 4  ⇒  maxTicks ≤ 55
MinTicks          = 4
PacingBudgetMs    = 15_000                  ⇒  turnDelayMs ≤ 15_000 div maxTicks
```

The certification fixture (`maxTicks: 10`, `turnDelayMs: 0`, no credentials ⇒ all scripted)
completes in well under 5 s.

**Both policies exist for every seat, in the same image, env-switched.**

| env | behaviour |
|---|---|
| `PLAYER_PROMPT=<text>` | the LLM policy: the server sends this prompt plus the seat's observation to Claude every tick |
| `PLAYER_SCRIPTED=lantern` | the scripted **keeper** baseline |
| `PLAYER_SCRIPTED=wallhug` | the scripted **runner** baseline |
| `PLAYER_SCRIPTED=1` (or `true`/`yes`) | the role-appropriate baseline for whatever slot the seat lands in |
| neither | the LLM policy with the built-in default prompt in `src/lighthouse_player.nim` |

**Role substitution is mandatory.** The league seats fillers arbitrarily, so a seat that
registers `PLAYER_SCRIPTED=lantern` but is dealt a runner slot plays `wallhug` instead (and vice
versa), with one log line `lighthouse: slot N registered <name>; playing <other> for its role`.
A baseline that raised or idled in the wrong slot would strand episodes.

**Scripted baseline `lantern` (keeper).** Deterministic, no RNG, no notes:

1. BFS from the exit tile over floor tiles that are not currently flooded → distance field
   `dExit`.
2. BFS from each uncollected key over the same tiles → `dKey[k]`.
3. Assign targets. If `keysCollected < keyCount`: build every (active runner, uncollected key)
   pair, sort ascending by `dKey[k][pos(r)]` (ties broken by runner index then key index), and
   greedily assign each key to the first unassigned runner; runners left over target the exit
   tile. If all keys are in: every active runner targets the exit tile.
4. For each active runner, take the first step of the shortest path to its target (BFS parent
   pointers, neighbour order N, E, S, W for determinism) **from the tile the runner will be
   standing on when the words land** — that is, from `pos(r) + delta(firstStep(pos(r)))`, one
   step along the path — and map it to `N`/`E`/`S`/`W`. A transmission sent on tick `t` is not
   read until the start of tick `t + 1`, by which time the runner has already moved; ordering the
   step for the tile it occupies *now* is permanently one tile stale and makes the pair oscillate
   at every corner (see §Tuning revision). If the runner is already on its target, or the
   one-step-ahead tile is the target, or no path exists over unflooded tiles, the step is `hold`.
5. Compose `"<Alias1> <step1>; <Alias2> <step2>; <Alias3> <step3>"` over the active runners, then
   `cleanText(msg, 160)`.
6. **Transmit policy** (this is where the baseline pays the tick cost on purpose). The keeper
   **never transmits twice in a row** — a runner needs the tick in between to act on what it was
   told, and a back-to-back pair costs the team two extra units of tide for one instruction. Given
   that, transmit if `tick mod 2 == 0`; **or**, to say something the runners do not already have,
   if the composed message differs from the last transmitted one **and** any of — (a) a runner has
   no order in the last transmitted message, (b) a runner **bumped** last tick and its step differs
   from what it was told, (c) the tide rose since the last message and a runner is within 2 tiles
   of the water, or (d) `gateOpen` flipped this tick. Otherwise `transmit = false`.
   Not-twice-in-a-row is what bounds the rate structurally at about half the ticks; measured over
   the fixture seeds it speaks on **51–52 %** of the ticks it plays, and the tests assert ≤ 60 %.
   (The accepted note had (b) as "any runner's step differs from the last message" with no
   repeat-suppression and no not-twice rule; with three runners someone turns a corner almost every
   tick, which measured 64–68 % against its own 60 % bar. See §Tuning revision.)

**Scripted baseline `wallhug` (runner).** Blind: reads only its 3 × 3 window, its inbox/standing
order and its own memory. No RNG, no notes:

1. **Obey.** If the inbox (or, failing that, the standing order if its age ≤ 3 ticks) contains
   this runner's own alias followed by a direction token (`N`/`S`/`E`/`W`/`hold`, or the words
   `north`/`south`/`east`/`west`/`hold`/`wait`/`stay`, case-insensitive, `:` or whitespace
   between), and that direction's neighbour in the window is floor and not `~`, take it and set
   `heading` to it. This is the grounded-instruction-following floor: the baseline **obeys**.
2. If the ordered direction is blocked, take the open, unflooded neighbour whose compass angle is
   nearest the ordered one (ties → clockwise).
3. **Else left-hand wall-following.** With `heading` (initialised `N`), try `left(heading)`, then
   `heading`, then `right(heading)`, then `back(heading)`; take the first neighbour that is floor
   and not flooded, and set `heading` to it.
4. If every neighbour is wall or water, `WAIT`.

A `lantern` keeper with three `wallhug` runners is a competent, watchable filler team that a
good prompt can beat — which is the point of a baseline.

**The two champion prompts** (both `PLAYER_PROMPT`, both must work in either role because the
platform may seat them anywhere):

`lighthouse-beacon` (champion #1, owner daveey):

> As KEEPER: you are the only one who can see. Spend ticks on words only when the words change
> what a runner will do — every transmit costs one extra tick of tide. Batch all three runners
> into one line in the grounded form "<Alias> <N|S|E|W|hold>", semicolon separated, plus at most
> one short reason. Give the NEXT SINGLE STEP, never a route: a blind runner cannot hold a route.
> Re-issue a runner's step only when it changed, when it bumped, or when water is within two
> tiles of it; otherwise stay silent and let the standing order run. Send runners at the nearest
> uncollected key first, and the instant all keys are in, drive everyone at the exit. Keep one
> line per runner in your notes: alias, last order, whether it obeyed.
> As RUNNER: you are blind. Obey the keeper's last order for your alias as long as that direction
> is open in your 3x3 window. If it is blocked, take the open direction closest to the ordered
> one. With no order, hug the left wall consistently so the keeper can predict you. Never step
> into water. Keep your last few moves and bumps in your notes so the keeper's corrections make
> sense.

`lighthouse-pilot` (champion #2, owner daveey-1 — a materially different strategy: rigid grammar,
rationed speech):

> As KEEPER: silence is a resource and so is the tide. Solve the whole team's route first —
> nearest key per runner, then the exit — then transmit on a fixed rhythm of one message every
> three ticks, breaking the rhythm only when a runner is one tile from water or one tile from a
> key. Address runners in the same order every time and use exactly this grammar:
> "<Alias>:<N|S|E|W|H>" joined by spaces, nothing else — a rigid grammar is easier for a blind
> runner to parse than prose. When a runner has a long straight corridor ahead, say the direction
> once and do not repeat it; count the corridor's length in your notes and stay silent for that
> many ticks.
> As RUNNER: parse the keeper's line for your alias and follow that letter until it is blocked or
> a new line arrives; a repeated letter means keep going. If blocked, turn to the open direction
> nearest the ordered one; if you are boxed in, WAIT rather than backtrack — the keeper will
> re-aim you. Never enter water. Note the last letter you were given and how many ticks you have
> held it.

`src/lighthouse_player.nim`'s built-in `DefaultPrompt` is a two-paragraph condensation of
`beacon`, so a seat with no `PLAYER_PROMPT` still plays the game rather than flailing.

**Two name spaces.** In-game every seat is an **anonymous cog alias**, drawn deterministically
from the seed by `tableNames()` (babel `sim.nim:121-132`, kept): the keeper's alias comes from
`KeeperNames = ["Fresnel", "Beacon", "Lantern", "Halyard", "Pharos", "Argand"]`, the runners'
from babel's `CogNames = ["Sprocket", "Gizmo", "Ratchet", "Widget", "Bolt", "Piston",
"Flywheel", "Rivet", "Tinker", "Gasket"]`. No prompt ever sees a policy name, so no seat can
meta-game who it is playing with. **Spectator-side only**, the replay carries `policyNames[]`
alongside `names[]`, and the viewer's `makeNameMap` (babel `client/renderer.js:692-720`, kept
verbatim including the `isBaselineFiller` regex) swaps real player names in wherever a name is
*rendered* — in the scorebug, the feed, the thumbnails and the endscreen — while the recorded
events keep the aliases. `resultsJson` reports **policy** names, because the league attributes by
policy. Aliases are re-drawn from the seed every episode and the maze is fresh every episode
(§Packaging: an unpinned seed is randomised), so no keeper–runner protocol can be pre-baked on a
board or on a name; the remaining half of the idea's integrity plan — ranking the keeper by
cross-play mean over stranger runner pools — is a league setting, not game code.

---

## Sim module

`src/lighthouse/types.nim` — forked from `src/babel/types.nim`:

- `LighthouseError* = object of CatchableError`; `PlayerConfig* = object (name: string)`.
- `GameConfig*` = babel's with the game fields replaced: `tokens`, `players`, `seed`,
  `maxTicks` (default 45), `width` (11), `height` (9), `tideDelay` (10), `tidePeriod` (7),
  `keyCount` (3), `episodeTimeoutSeconds` (1200), `sampled` (bool), `turnDelayMs` (250),
  `playerConnectTimeoutSeconds` (180.0), `model` (`"claude-sonnet-5"`), `maxOutputTokens` (900),
  `llmTimeoutSeconds` (18).
- `defaultGameConfig*()` and `update*(config, configJson)` — same shape as babel's, validating
  `width`/`height` odd and ≥ 9, `maxTicks ≥ 4`, `keyCount ≥ 1`, `tidePeriod ≥ 1`.
- `Move* = enum mvWait = "WAIT", mvNorth = "N", mvSouth = "S", mvEast = "E", mvWest = "W"`.
- `RunnerStatus* = enum rsActive = "active", rsEscaped = "escaped", rsDrowned = "drowned"`.
- `EventKind* = enum evStart = "start", evTick = "tick", evSay = "say", evKey = "key",
  evEscape = "escape", evDrown = "drown", evEnd = "end"`.
- `GameEvent*` — one flat object (babel's design, so `eventToJson`/`eventFromJson` stay simple):
  `kind`, `tick`, `clock`, `tideRows`, `seat`, `x`, `y`, `positions: seq[seq[int]]`,
  `alive: seq[bool]`, `moves: seq[string]`, `blocked: seq[bool]`, `keysOnFloor: seq[seq[int]]`,
  `keysCollected`, `gateOpen`, `escaped`, `drowned`, `cost`, `notes: seq[string]`,
  `scripted: seq[bool]`, `text: string`.

`src/lighthouse/sim.nim` — pure rules, no IO, no networking; the server, the tests **and** the
wasm replay viewer all drive this one module (babel's cardinal convention). Constants:
`Seats* = 4`, `Runners* = 3`, `KeeperSeat* = 0`, `EpisodeCallBudget* = 220`, `CallsPerTick* = 4`,
`MinTicks* = 4`, `PacingBudgetMs* = 15_000`, `MaxMessageLen* = 160`, `MaxKeeperNotes* = 400`,
`MaxRunnerNotes* = 200`, `KeeperNames*`, `CogNames*`.

`Sim* = object`: `config`, `names: seq[string]` (4 aliases), `grid: seq[string]` (`height`
strings of `width` chars, `#`/`.`), `exitAt: (int, int)`, `starts: array[3, (int, int)]`,
`keysAt: seq[(int, int)]` (initial), `keysOnFloor: seq[(int, int)]` (live),
`pos: array[3, (int, int)]`, `status: array[3, RunnerStatus]`, `keysHeld: array[3, int]`,
`lastMove: array[3, Move]`, `blocked: array[3, bool]`, `moveHistory: array[3, seq[string]]`,
`keysCollected`, `gateOpen`, `escapedCount`, `drownedCount`, `tick`, `clock`, `messages:
seq[(int, string)]` (tick, text), `inbox: string`, `standing: string`, `standingTick: int`,
`notes: array[4, string]`, `scripted: array[4, bool]`, `done`, `reason`, `events: seq[GameEvent]`.

API (mirrors babel's surface so the server, tests and viewer keep their shapes):

- `initSim*(config): Sim` — validates `config.players.len == Seats`, draws aliases, carves the
  maze, places exit / starts / keys, logs `evStart`.
- `sampleEpisode*(config): GameConfig` — idempotent budget fit (above).
- `tableNames*(players, seed): seq[string]`.
- `isWall*(sim, x, y)`, `isFlooded*(sim, x, y)`, `tideRows*(sim)`, `waterLine*(sim)`,
  `floodClock*(sim)`.
- `pendingSeats*(sim): seq[int]` — slot 0 plus every runner with `rsActive`.
- `keeperView*(sim): string`, `runnerWindow*(sim, runner): array[3, string]`.
- `applyTick*(sim, spoke, message, moves: array[3, Move], notes: array[4, string], scripted:
  array[4, bool])` — steps 3–12 of the resolution order, in that order, in one call. Raises
  `LighthouseError` only on a genuinely impossible argument (a move for a resolved runner, a call
  after `done`); a blocked move is not an error.
- `endEarly*(sim)` — `settle("deadline")`.
- `teamScore*(sim): float`, `resultsJson*(sim): JsonNode`, `boardStateJson*(sim): JsonNode`.
- `replayMatch*(config, events, recorded = nil): seq[Sim]` — re-derives the whole state timeline
  from the recorded events, exactly as babel `sim.nim:505-535`. `frames[i]` is the state after
  `events[0 ..< i]`, so `frames.len == events.len + 1`. The third argument is the **recorded
  `config` JSON node** from the replay payload; `replayMatch` **cross-checks** its `grid`, `exit`,
  `starts` and `keys` against what the seed re-derives and raises `"the recorded maze does not
  match the seeded one"` on any disagreement — so a wasm/native RNG divergence fails loudly
  instead of drawing a wrong maze. It is a third argument rather than a field lookup because
  `GameConfig` (above) carries no `grid`/`exit`/`starts`/`keys`: those are derived from the seed,
  not configured, and putting them in `GameConfig` would make the runtime config schema lie. Both
  call sites — `server.nim`'s `statesFromEvents` and `replay-viewer/lighthouse_replay.nim` — pass
  it, and `tests/test_replay.nim` proves a one-character grid edit raises.
  Note that the per-tick sub-events (`say`, `key`, `escape`, `drown`) are **derived** by
  `applyTick` from the `tick` event that follows them, so `replayMatch` buffers the `say` text and
  replays whole ticks; the frames for the sub-events repeat the pre-tick state and the `tick`
  event's frame is the post-resolution snapshot the scrubber steps through.
- `eventToJson*(event)`, `eventFromJson*(node)`.

**Event vocabulary written to the replay** (the complete list; the viewer re-derives every frame
from these plus `config`):

| kind | fields |
|---|---|
| `start` | — |
| `say` | `tick`, `seat` (always 0), `text` (the message, ≤ 160 runes), `cost` (always 1 — the *extra* clock unit this message cost) |
| `key` | `tick`, `seat` (1–3), `x`, `y`, `keysCollected` (running total) |
| `escape` | `tick`, `seat`, `escaped` (running total) |
| `drown` | `tick`, `seat`, `x`, `y`, `drowned` (running total) |
| `tick` | `tick`, `clock`, `tideRows`, `positions` (`[[x,y] × 3]`, `[-1,-1]` for a resolved runner), `alive` (`[bool × 3]`), `moves` (`["N","WAIT","E"]`), `blocked` (`[bool × 3]`), `keysOnFloor` (`[[x,y], …]`), `keysCollected`, `gateOpen`, `escaped`, `drowned`, `notes` (`[string × 4]`, `""` where unchanged this tick), `scripted` (`[bool × 4]`) |
| `end` | `tick` = ticks played, `text` = `reason` |

Order within a tick: `say` (if any) → `key`* → `escape`* → `drown`* → `tick`. The `tick` event
is the post-resolution snapshot and is what the scrubber steps through.

**`boardStateJson`** — one frame; the viewer draws exactly this and nothing else:

```json
{"seats": [
   {"name":"Fresnel","role":"keeper","status":"keeper","pos":null,"keys":0,
    "notes":"…","messages":9,"scripted":false,"pending":true},
   {"name":"Sprocket","role":"runner","status":"active","pos":[3,7],"keys":1,
    "lastMove":"N","blocked":false,"window":["#.#","#@.","###"],
    "notes":"…","scripted":false,"pending":true}
 ],
 "grid": ["#########.#", "#.........#", "…9 strings…"],
 "exit": [9,0], "gateOpen": false,
 "keysOnFloor": [[7,5],[9,5]], "keysCollected": 1, "keyCount": 3,
 "tick": 12, "maxTicks": 45, "clock": 19, "tideRows": 1, "waterLine": 8,
 "message": "Sprocket N; Gizmo E; Ratchet hold", "messageAge": 0, "messageCost": 1,
 "escaped": 0, "drowned": 0, "score": 12.0,
 "phase": "running", "gameDone": false, "reason": ""}
```

`phase` ∈ `running` | `done`. `messageAge` counts ticks since the message was transmitted;
`message` is `""` before the first transmission.

**`resultsJson`** — platform-facing, **policy** names:

```json
{"names": ["lighthouse-beacon","lighthouse-pilot","Baseline (1)","Baseline (2)"],
 "scores": [26.0, 26.0, 26.0, 26.0],
 "roles": ["keeper","runner","runner","runner"],
 "teamScore": 26.0, "keys": 3, "keyCount": 3, "escaped": 2, "drowned": 1,
 "messages": 14, "ticks": 31, "maxTicks": 45, "clock": 45,
 "reason": "complete"}
```

**Replay payload** (`lighthouse.replay.v1`) — self-sufficient: everything the viewer needs is in
these bytes, and the only network the viewer does is the S3 `GET` of this file:

```json
{"protocol": "lighthouse.replay.v1",
 "names": ["Fresnel","Sprocket","Gizmo","Ratchet"],
 "policyNames": ["lighthouse-beacon","lighthouse-pilot","Baseline (1)","Baseline (2)"],
 "config": {"seed": 7, "maxTicks": 45, "width": 11, "height": 9,
            "tideDelay": 10, "tidePeriod": 7, "keyCount": 3,
            "messageCap": 160, "sampled": true,
            "grid": ["#########.#", "#.........#", "…9 strings…"],
            "exit": [9,0], "starts": [[1,7],[5,7],[9,7]],
            "keys": [[3,5],[7,5],[9,5]]},
 "events": [ … ],
 "results": { … }}
```

Replay mode and the wasm module add `"states"`: `boardStateJson()` for every prefix from
`replayMatch`, so `states.len == events.len + 1`.

---

## Server, player, protocol

`src/lighthouse.nim` — babel's entrypoint (`src/babel.nim`) verbatim in shape:
`readRuntimeConfig()`; replay mode → `runReplayServer`; otherwise `defaultGameConfig()`,
`config.update(runtimeConfig.config)`, **randomise the seed when it is not pinned** (so the maze,
the key placement and the aliases are not precomputable), then `sampleEpisode`, then
`runGameServer`.

`src/lighthouse/server.nim` — babel `src/babel/server.nim` with the game loop replaced by
bullwhip's tick loop (`src/bullwhip/server.nim:262-318`). Kept **unchanged**: the routes
(`GET /healthz`, `/client/global`, `/client/player`, `/client/replay`, `/client/renderer.js`,
`/client/chrome.css`, `/client/assets/@name`; `WS /player?slot=N&token=T`, `WS /global`,
`WS /replay`), the asset-path traversal guard, the **Ping → Pong reply in `websocketHandler`**
(the certifier pings `/global`; an unanswered ping fails certification), `writeArtifact` with the
`COGAME_RESULTS_METHOD` / `COGAME_SAVE_REPLAY_METHOD` hints, and `finishEpisode`'s ordering —
send the `final` frames to players **first**, `sleep(500)`, write results, write the replay,
`sleep(500)`, `quit(0)`.

The loop, per tick: check the play deadline → snapshot the sim under the lock → `decideAll` for
`pendingSeats()` **outside** the lock (only this thread mutates the sim, so the snapshot cannot go
stale) → `applyTick` under the lock → `broadcastLocked()` → `sleep(turnDelayMs)`.

Protocol **`lighthouse.player.v1`**, JSON text frames, on the websocket named by
`COWORLD_PLAYER_WS_URL`:

- game → player, on connect:
  `{"type":"welcome","protocol":"lighthouse.player.v1","slot":N,"name":alias,
  "role":"keeper"|"runner","maxTicks":int}`
- game → player, after every tick — **redacted**, because Lighthouse's whole point is hidden
  information and decisions are server-side so nothing is lost:
  `{"type":"state","slot":N,"name":alias,"role":str,
  "seat":{"status":str,"keys":int,"lastMove":str,"blocked":bool,"messages":int},
  "tick":int,"maxTicks":int,"keysCollected":int,"keyCount":int,"gateOpen":bool,
  "escaped":int,"drowned":int,"teamScore":float,"started":bool,"done":bool,"reason":str}`.
  A runner's frame never carries the grid, any coordinates, or the tide. The keeper's frame never
  carries a runner's notes.
- game → player, at the end:
  `{"type":"final","done":true,"scores":[4],"roles":[4],"names":[4 aliases],"keys":int,
  "escaped":int,"drowned":int,"ticks":int,"reason":str}` — after which the player exits. The
  `final` frame carries **aliases**, not policy names (only `results.json` carries policy names).
- player → game: `{"type":"prompt","prompt":str,"scripted":str}`. `prompt` ≤ 4000 chars.
  `scripted` is `""` (LLM), `"lantern"`, `"wallhug"`, or `"1"`/`"true"`/`"yes"` (role-appropriate).
  The latest frame wins for all later ticks; the player sends it on connect and again after the
  `welcome` (babel's race guard, kept).

`src/lighthouse_player.nim` — babel `src/babel_player.nim` verbatim except: the default prompt,
and `PLAYER_SCRIPTED` read as a **string** (passed straight through) rather than a boolean.

---

## Viewer

**Static wasm bundle, never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` (committed
mode 100755 — `coworld build` hard-requires `os.X_OK` on the hook) is babel's script with the
names swapped: it compiles `replay-viewer/lighthouse_replay.nim` to wasm with
`nim c -d:emscripten` (local `emcc` if present, otherwise the pinned
`emscripten/emsdk:4.0.15` container from `Dockerfile.replay-viewer`), asserts
`dist/lighthouse_replay.{js,wasm}` are non-empty, and copies into the output directory:
`lighthouse_replay.js`, `lighthouse_replay.wasm`, `replay-viewer/index.html`,
`replay-viewer/static_replay.js`, `client/renderer.js`, `client/chrome.css`, and into
`assets/`: `arena_floor.png`, `soldier_red_front.png`, `soldier_blue_front.png`,
`soldier_green_front.png`, `soldier_yellow_front.png`, `font.ttf`. The wasm module re-derives
every frame in the browser from the recorded events with the **same Nim sim** the server ran; no
server is contacted except S3 for the `.replay` file.

**Chrome reused verbatim.** From `/workspace/starters/cogame-babel`:
`client/chrome.css` byte-for-byte **except** the scorebug legibility rules below, which babel's
copy does not contain — `.plate-name { min-width: 3.2em; flex: 1 1 auto }` and the
`@media (max-width: 640px) { .plate-label { display: none } }` block are taken verbatim from
`cogame-bullwhip`'s `chrome.css`, which is where they were added; `grid-template-columns` becomes
`repeat(4, 1fr)` for four plates instead of babel's five; `replay-viewer/index.html`'s structure (`#layout`, `#stage`,
`#topband` with `#wordmark`/`#clock`/`#statuschip`/`#feedtoggle`, `#scorebug`, `#board-wrap` with
`#table`/`#lightpool`/`#grain`/`#endscreen`, `#transport` with `#scrub`/`.tbar`/`#play`/`#pos`,
`#feed`, `#loading`) with only the wordmark text (`LIGHT<span>HOUSE</span>`) and the module/global
names changed; `replay-viewer/static_replay.js` unchanged apart from
`BabelReplayModule → LighthouseReplayModule`, `bab_* → lh_*`, `BabelRenderer →
LighthouseRenderer` — **the `coworld-replay` postMessage bridge, including `tell("loading")`,
`tell("ready")` and `tell("error")`, and the 20 s `AbortController` fetch bound, stay exactly as
they are** (phase-60 check 8c greps for the bridge). From `client/renderer.js` these helpers are
copied unchanged: `makeNameMap`, `applyNames`, `clampName`, `isBaselineFiller`, `renderFeed`,
`roundBase`, `escapeHtml`, `wrapLines`, `roundRect`, `hexToRgb`/`shade`/`rgba`,
`drawTag`, `drawParchment`, `buildScrub`, `bindFeedToggle`, `makeEffects`, `attachLive`,
`attachReplay`, `updateEndscreen`'s shell, and the Ink & Print palette
(`COLORS`/`COLOR_HEX`/`PAPER`/`INK`/`AMBER`/`GHOST`, `PICK_HOLD_MS` 2500, `PICK_FADE_MS` 700).
`ellipsize` is babel's with exactly one change: it cuts the string by **code point**
(`Array.from`) rather than by UTF-16 code unit, because babel's `slice(0, -1)` can cut an astral
rune between its surrogates and *Legible at 360 px* below asks for a rune-safe boundary. The
keeper's message is arbitrary model text and does reach this plate.
Only `draw`, `computeLayout`, `describeEvent`, `updateScorebug` and the endscreen columns are
rewritten.

**Seat colours map 1:1 onto the four sprites**: seat 0 keeper = red
(`soldier_red_front.png`), runners 1/2/3 = blue / green / yellow.

**Readouts** (the whole list; the stage is one canvas):

1. **God-view maze**, centre stage. Floor tiles are the flagstone pattern from
   `data/arena_floor.png`; walls are chiselled stone blocks — a two-tone fill with a 1 px lit
   bevel on the top and left edges, a darker mortar line on the bottom and right, and a
   per-tile jitter drawn from the tile coordinates so the wall reads as masonry rather than a
   grey rectangle. The board is letterboxed and integer-scaled to fill the stage.
2. **Exit**, on the top wall: a portcullis. Closed = dark arch behind vertical iron bars with a
   keyhole plate showing `n/3`. Open = the bars retract upward, an amber light spills down the
   corridor below it, and a 600 ms flare plays on the tick the gate flips.
3. **Keys**: small amber keys (round bow, shaft, two wards) with a slow bob and a soft glow, on
   their floor tiles. Collected keys fly to the collecting runner and dock as a pip under it.
4. **Fog cones** — the dramatic-irony device. Everything outside every runner's 3 × 3 window is
   covered by a dark scrim (`rgba(12,10,8,0.62)`); each active runner's 3 × 3 window is a clear
   square with a soft radial falloff at the edge and a 1 px rim in the runner's seat colour. The
   audience sees the whole maze **and** exactly how little each runner does.
5. **Rising tide**: flooded rows are translucent teal (`rgba(58,124,140,0.55)`) over the floor,
   with a bright crest line at `waterLine`, two sine ripples at different phases and speeds, and
   foam speckles along the crest. When `tideRows` steps, the surface **eases** to its new y over
   500 ms, so the water visibly creeps rather than teleporting. A drowning runner gets a 700 ms
   bubble burst and then a sunken, desaturated sprite under the surface.
6. **Radio subtitles**: the keeper's message runs as a subtitle plate across the bottom of the
   stage, keeper-red on paper, with a **`◉ +1 TICK` cost badge** pinned to its right that pulses
   when the message lands. The plate holds at full opacity for `PICK_HOLD_MS` (2500 ms), fades
   over `PICK_FADE_MS` (700 ms) to a resting 0.4, and stays there — so a paused frame still shows
   the standing order and what it cost. Silence draws the empty plate with `— silence —`.
7. **Corner thumbnails**: three 3 × 3 mini-views stacked in the right gutter of the stage, one per
   runner, each drawn from that seat's `window` with the same tile art, framed in the runner's
   colour, captioned with its (mapped) name, its key pips and its status glyph. This is where the
   cramped view lives.
8. **Lighthouse**: a tower silhouette in the top-left of the stage with a slowly rotating beam;
   the beam flares on every transmit. The show's logo moment, and a second read on "the keeper
   spoke".
9. **Scorebug** (`#scorebug`, the starter's `.plate` markup unchanged): four plates. Keeper plate
   — name, `◉` + message count, `MSGS` label, and the running **team score** as its big number.
   Runner plates — name, key pips (filled per key that runner collected), status glyph
   `▲` active / `✔` escaped / `≈` drowned, and `▶` on the seat whose decision is pending.
10. **Clock** (`#clock`): `TICK 12 / 45 · TIDE ROW 9 · KEYS 1/3`, and `FINAL` once done.
11. **Feed** (`#feed`, `renderFeed` verbatim, one section head per tick — `TICK 12`):
    `Fresnel: "Sprocket N; Gizmo E; Ratchet hold" (+1 tick)` · `Sprocket moves north` ·
    `Gizmo bumps a wall` · `Ratchet takes a key (2/3)` · `THE GATE OPENS` ·
    `Sprocket escapes` · `Gizmo is taken by the tide` ·
    `Final — 2 of 3 out, 3 keys, score 26.0`. Notes lines are `say`-styled, printed only when a
    seat's notes changed, exactly as babel does.
12. **Endscreen**: verdict `ALL THREE OUT` / `TWO OF THREE OUT` / `ONE OF THREE OUT` /
    `THE TIDE TOOK THEM`, with a reason line on `timeup` ("the clock ran out with 1 still in the
    maze") and on `deadline` ("episode deadline: scored on 22 of 45 ticks"). Columns: `role`,
    `status`, `keys`, `messages`, `score`.

**Legible at 360 px wide.** The embedded featured-match iframe on softmax.com is ~360 px, and the
scorebug is checked at that width, not at desktop width: `.plate-name` keeps
`flex: 1 1 auto; min-width: 3.2em` and the `.plate-label` text hides under 640 px (the starter's
rule, kept). Below a 520 px stage the three corner thumbnails collapse from the right gutter into
a single row under the maze; below 420 px they hide entirely and the subtitle plate wraps to at
most two lines, ellipsised on a rune-safe boundary. At 360 px the 11 × 9 board gives 17–23 px
cells depending on the stage height (21 px at 360 × 240, against 17 px for the 17 × 11 board this
note originally specified), so walls, water, keys and the four sprites all read. Nothing is rendered as internal
notation: the feed says "moves north", not "N"; the clock says "TICK 12 / 45", not "t=12".

**Real art, not placeholders.** The five PNGs and `font.ttf` are the starter's real assets,
copied byte-for-byte with `data/FONT_LICENSE.txt`. Everything else — masonry, water, keys,
portcullis, lighthouse, subtitle plate — is drawn on canvas with the Ink & Print palette and the
shading rules named above, the same way babel draws its scene cards and shapes. No grey boxes, no
`TODO` sprites.

---

## Packaging

- **`compose.yaml`** — service name = the coworld name:
  ```yaml
  services:
    lighthouse:
      image: coworld-lighthouse:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```
- **`lighthouse.nimble`** — babel's, renamed; `requires "nim >= 2.2.4"`, `bitworld >= 0.1.0`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`. `nimby.lock` copied verbatim.
- **`Dockerfile`** — babel's, two entrypoints in one image: `/bin/lighthouse` (the game server,
  `CMD`) and `/bin/lighthouse-player`. `Dockerfile.replay-viewer` — babel's, building
  `replay-viewer/lighthouse_replay.nim`.
- **`replay-viewer/config.nims`** — babel's with `EXPORT_NAME=LighthouseReplayModule`, output
  `lighthouse_replay.js`, and
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_lh_load_replay,_lh_payload_ptr,_lh_payload_len,_lh_error_ptr,_lh_error_len`.
- **`coworld_manifest_template.json`** — game `name: "lighthouse"`, image
  `"{{LIGHTHOUSE_IMAGE}}"`, `run: ["/bin/lighthouse"]`,
  `env: {"ANTHROPIC_API_KEY_URI": "secret://coworld/lighthouse/anthropic_api_key"}`,
  `source_url: "https://github.com/Metta-AI/cogame-lighthouse/tree/main"`,
  `"replay_viewer": {"bundle": "static-replay-viewer"}`,
  tags `["cooperative","asymmetric-information","instruction-following","llm-driven",
  "turn-based","four-player","maze"]`.
  - `config_schema` (`additionalProperties: false`, required `tokens` + `players`): `tokens` and
    `players` `minItems: 4, maxItems: 4`; **`num_agents` integer, minimum 4, maximum 4**; `seed`;
    `maxTicks` 4..55 default 45; `width` 9..25 default 11 (odd); `height` 9..15 default 9 (odd);
    `tideDelay` 0..40 default 10; `tidePeriod` 1..12 default 7; `keyCount` 1..5 default 3;
    `episodeTimeoutSeconds` 60..6000 default 1200; `turnDelayMs` 0..2000 default 250; `model`;
    `maxOutputTokens` 64..2000 default 900; `llmTimeoutSeconds` 5..300 default 18;
    `player_connect_timeout_seconds` default 180.
  - `results_schema` — the `resultsJson` above, with `reason` enumerated
    `["complete","timeup","deadline"]` and `scores` 4 numbers in `[0, 42]`.
  - **`game.protocols` carries BOTH keys**: `player` (the full `lighthouse.player.v1` frame
    catalogue from §Server, player, protocol, including "a policy is just a prompt" and the
    `PLAYER_PROMPT` / `PLAYER_SCRIPTED` recipe) and `global` (the `/global` websocket snapshot:
    `boardStateJson` plus `type`, `game`, `policyNames`, `events`, `started`, `done`,
    `connected`, and the note that `/client/global` renders the stage live while the static
    bundle renders hosted replays as `index.html?replay=<url>`).
  - **`game.docs`** = `{"readme": {"type":"text","value":"…"},
    "pages": [{"id":"rules.md","title":"rules.md","content":{"type":"text","value":"…"}}]}`.
    The readme is a one-paragraph pitch; `rules.md` reproduces §The game's twelve numbered
    resolution steps, the tide formula, the scoring formula, the observation split and the two
    baselines.
  - **`player[]`** — three runnables, all `"image": "{{LIGHTHOUSE_IMAGE}}"`,
    `"run": ["/bin/lighthouse-player"]`, resources `requests {cpu 100m, memory 64Mi}, limits
    {cpu 1}`:
    | id | env |
    |---|---|
    | `lighthouse-player` | — (prompt policy; `PLAYER_PROMPT` supplied per policy upload) |
    | `lighthouse-lantern` | `PLAYER_SCRIPTED=lantern` |
    | `lighthouse-wallhug` | `PLAYER_SCRIPTED=wallhug` |
  - **`variants[]` — `num_agents: 4` in every one**:
    | id | game_config |
    |---|---|
    | `standard` | `players` [Player1..Player4], **`num_agents: 4`**, `maxTicks: 45`, `width: 11`, `height: 9`, `tideDelay: 10`, `tidePeriod: 7`, `keyCount: 3`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |
    | `spring-tide` | `players` [Player1..Player4], **`num_agents: 4`**, `maxTicks: 45`, `width: 11`, `height: 9`, `tideDelay: 10`, **`tidePeriod: 5`**, `keyCount: 3`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |
  - **`certification`** — `game_config`: `players` `[{"name":"Fresnel"},{"name":"Sprocket"},
    {"name":"Gizmo"},{"name":"Ratchet"}]`, **`num_agents: 4`**, `seed: 11`, `maxTicks: 10`,
    `turnDelayMs: 0`, `player_connect_timeout_seconds: 180`; `players`:
    `[{"player_id":"lighthouse-player"},{"player_id":"lighthouse-lantern"},
    {"player_id":"lighthouse-wallhug"},{"player_id":"lighthouse-wallhug"}]` — four entries, so
    `len(certification.players) == len(certification.game_config.players) ==
    certification.game_config.num_agents == 4`.
- **`.github/workflows/`** — `ci.yml`, `coworld-release.yml`, `coworld-submit.yml` from
  `coworld-builder/templates/`, with `<slug>` = `lighthouse`, `<IMAGE>` = `coworld-lighthouse`,
  **`<SEATS>` = `4`**.
- **`tools/ci/docker_smoke.sh`** from the template, mode 100755, `<slug>` = `lighthouse`,
  `<IMAGE>` = `coworld-lighthouse`, **`<SEATS>` = `4`**. That value is an independent cross-check
  against `certification.game_config.num_agents`; both are 4 and must stay so.
- **`tools/ci/policies.json`** — the canonical set (two LLM champions, two scripted fillers):
  ```json
  [{"name":"lighthouse-beacon","run":"/bin/lighthouse-player",
    "env":{"PLAYER_PROMPT":"<beacon prompt above>"}},
   {"name":"lighthouse-pilot","run":"/bin/lighthouse-player",
    "env":{"PLAYER_PROMPT":"<pilot prompt above>"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"lighthouse-lantern","run":"/bin/lighthouse-player",
    "env":{"PLAYER_SCRIPTED":"lantern"}},
   {"name":"lighthouse-wallhug","run":"/bin/lighthouse-player",
    "env":{"PLAYER_SCRIPTED":"wallhug"}}]
  ```
  Champion #1 `lighthouse-beacon` → daveey; champion #2 `lighthouse-pilot` → daveey-1 (uploaded
  while daveey-1 is the active player, hence the `player` field); fillers are the two scripted
  baselines, whose versions must differ from both champions'.
- **Kept byte-for-byte from the starter**: `data/arena_floor.png`,
  `data/soldier_{red,blue,green,yellow}_front.png`, `data/font.ttf`, `data/FONT_LICENSE.txt`,
  `nimby.lock`, `LICENSE`, `.gitignore`. `client/chrome.css` is babel's byte-for-byte except for
  four additions, all of them additive and none of them touching babel's own rules: `#scorebug`
  becomes `repeat(4, 1fr)` for four plates; `.plate-name` takes bullwhip's
  `min-width: 3.2em; flex: 1 1 auto` (§Viewer, *Legible at 360 px*); bullwhip's
  `@media (max-width: 640px)` block arrives whole — `.plate-label { display: none }` plus the
  `.plate-score` size and the `#scorebug` gap/padding that ship with it; and lighthouse adds six
  classes of its own for the chrome §Viewer describes (`.plate-status`, `.plate-msg`,
  `.plate.drowned .plate-name`, `.plate.escaped .plate-name`, `.feed-notes`, `.feed-tick`) with a
  `@media (max-width: 420px)` block that drops the scorebug to two columns so four plates still
  read on the narrowest embed.

---

## Tests

CI (`ci.yml`) runs every `tests/*.nim` twice — debug and `-d:release` — then the docker smoke,
then the wasm-viewer job. The sandbox cannot run any of this locally; CI is the only harness.

**`tests/test_sim.nim` — sim unit tests** (fixture seeds `[1, 7, 42, 1234]` throughout):

1. **Maze is perfect**: the floor-tile graph is a tree (`edges == floorTiles - 1`, connected), and
   the outer border is wall everywhere except the exit tile.
2. **Reachability**: BFS from the exit reaches every runner start and every key tile.
3. **Placement**: exactly `keyCount` keys, all distinct, none on a start tile, the exit tile or a
   tile adjacent to the exit, all with `y ≤ height - 4`, pairwise BFS distance ≥ 6 (or the
   documented fallback); the three starts are on row `height - 2` with pairwise `|Δx| ≥ 4`.
4. **Tide schedule**: `tideRows(clock)` is monotone non-decreasing, 0 for `clock < tideDelay`,
   `height` at `clock == floodClock`; `waterLine == height - tideRows`; a tile is flooded iff
   `y >= waterLine`.
5. **Resolution order**, on a hand-built **9 × 9** fixture (the note's own `width`/`height`
   validation rejects anything below 9, so 5 × 5 cannot be constructed), one assertion per
   numbered step: a wall
   bump leaves the position unchanged and sets `blocked`; a move into water is a bump, not a
   drowning; a key is taken on entry and `keysCollected` increments; the gate opens exactly when
   the last key is taken and never closes; a runner on the **open** exit escapes and one on a
   **closed** exit does not; the clock advances by 1 on silence and by 2 on a transmit; a runner
   standing on a row that floods this tick drowns *after* it has had its move, its pickup and its
   escape chance.
6. **No collision**: two runners ordered into the same tile both occupy it; two runners swapping
   tiles both succeed.
7. **Scoring**: `teamScore` hand-computed for three episodes (all three out early, two out, total
   wipeout); positive sign; identical across all four `results.scores` entries; bounded to
   `[0, 42]`.
8. **Endings**: constructed episodes yield exactly `complete`, `timeup` and `deadline`; nothing
   else is ever written to `reason`; `endEarly()` gives `deadline` and scores the state reached.
9. **Rune truncation**: a 400-rune message of multi-byte runes truncates to 160 runes + `…`,
   `runeLen == 160`, and `validateUtf8` of the serialised event is `-1`. Same for 400/200-rune
   notes.
10. **Replay re-derivation**: `replayMatch(config, events, recorded).len == events.len + 1`; the
    final frame's `boardStateJson` equals the live sim's; a replay whose recorded `config.grid` is
    mutated by one character raises `"the recorded maze does not match the seeded one"`.
11. **Event JSON round-trip**: `eventFromJson(eventToJson(e)) == e` for every one of the seven
    kinds.
12. **Seed determinism**: two `initSim`s with the same seed give identical grid, exit, starts,
    keys and aliases; different seeds give different mazes.

**`tests/test_bot.nim` — bounded-orders / legality on the scripted baselines**:

1. **Legality (the load-bearing assertion)**: for every seed, drive full episodes with `lantern`
   + three `wallhug`. Every `wallhug` reply is one of the five legal move tokens; no move ever
   passes through a wall, off the grid, or into a flooded tile; every `lantern` message is
   ≤ 160 runes and valid UTF-8; neither baseline ever emits notes; `applyTick` never raises.
2. **Termination and speed**: every episode ends with `reason` ∈ `{complete, timeup}` and
   `tick ≤ maxTicks`, in under `maxTicks × 50 ms` of wall clock (no network is touched).
3. **Talk budget**: `lantern` transmits on ≤ 60 % of the ticks it plays.
4. **Competence floor / tuning oracle**: `lantern` + three `wallhug` gets `keysCollected == 3` on
   at least 3 of the 4 seeds and `escaped == 3` on at least 2 of the 4. If this fails, the fix is
   to raise `standard`'s `tidePeriod` (and `spring-tide`'s with it) rather than to weaken the maze
   — this test is the parameter-tuning decision rule, not a flaky check. **Check the oracle first:**
   if the minimum over key→runner assignments of the maximum over runners of
   `dist(start, key) + dist(key, exit)` exceeds `maxTicks`, no tide setting can help and the board
   or the key draw is what has to move (§Tuning revision). Currently measured: keys on 4 of 4
   seeds, all three out on 3 of 4.
5. **Instruction following**: counting only ticks on which a fresh message named a given runner,
   that runner moved in the ordered direction on ≥ 80 % of them.
6. **Role substitution**: a seat registered `lantern` in a runner slot plays `wallhug`, a seat
   registered `wallhug` in slot 0 plays `lantern`, and `PLAYER_SCRIPTED=1` picks the
   role-appropriate baseline in both.
7. **No-credentials fallback**: with no LLM env vars, `newLlmClient` reports `disabled` and
   `decideAll` returns pure scripted decisions with zero HTTP requests — the offline
   certification path.
8. **Reply parsing**: `{"move":"north"}`, `{"move":"n"}`, `{"move":" E "}`, `{"move":"WAIT"}`,
   `{"move":"left"}` all parse; `{"move":"NE"}`, `{"move":42}`, `{}` are rejected;
   `{"transmit":true,"message":"   "}` is silence; `{"message":"go N"}` with no `transmit` flag
   transmits.

**`tests/test_replay.nim` — strict-UTF-8 replay parse**: build an episode whose keeper messages
and all four seats' notes contain multi-byte runes (`≤`, `→`, `🌊`) positioned exactly on the 160 /
400 / 200-rune truncation boundaries; serialise the full `lighthouse.replay.v1` payload; assert
`validateUtf8(payload) == -1`, `parseJson(payload)` succeeds, and the payload round-trips
byte-identically through `eventFromJson`/`eventToJson`. Then feed the same bytes to
`lhLoadReplay` — the *same proc* `replay-viewer/lighthouse_replay.nim` exports to wasm, compiled
natively here — and assert it returns 1 and produces `states.len == events.len + 1`.

**End-to-end episode writing a replay**: `tools/ci/docker_smoke.sh` runs one game container plus
four player containers in the production image on a per-run docker network, driven by the
certification fixture, with **no** `ANTHROPIC_API_KEY` so the all-scripted completion path is
exercised. It asserts: the game exits 0, `results.json` and the replay were written, the replay
parses as JSON (`SMOKE_REQUIRE_REPLAY_JSON=1`), and `certification.game_config.num_agents` is a
positive integer equal to `len(certification.players)`, `len(certification.game_config.players)`
and `SMOKE_SEATS` — all **4**.

**Viewer smoke** (the `wasm-viewer` CI job plus repo-side checks): `tools/build_replay_viewer.sh`
is present and mode 100755; it builds a bundle containing a non-empty `index.html` and a non-empty
`.wasm`; every file `index.html` references exists in the bundle; `node --check
client/renderer.js` and `node --check replay-viewer/static_replay.js` pass; and
`replay-viewer/static_replay.js` contains `data-replay`, `coworld-replay` and `tell("ready")`.
`client/fixtures/gen_fixture.js` is ported to emit a hand-consistent
`client/fixtures/sample_replay.json` for `lighthouse.replay.v1`, and
`client/fixtures/dev_shell.html` loads it, so the stage can be eyeballed without a live episode.

---

## Out of scope (v1)

- **Runner→keeper and runner→runner channels.** The bridge is one-way; a back-channel is a
  different (and much larger) game.
- **RL-vector policies for the runner seats.** Rebound to LLM prompts, as stated above.
- **Runner collision, pushing, doors, keys that can be dropped or handed over, and per-runner
  key requirements.** Keys are collected once, by anyone, and the gate is a single global latch.
- **Non-rectangular boards, multiple floors, moving hazards, or a receding tide.** The water rises
  monotonically from the bottom and never goes back.
- **A keeper that can move, look away, or lose its map.** The keeper is omniscient and immobile;
  its only scarce resource is the tick a message costs.
- **Per-runner private channels or addressed messages at the transport level.** The keeper
  broadcasts one message to all three; addressing is a convention inside the text, which is
  exactly the grounding problem the game studies.
- **Cross-episode memory or persistent keeper–runner dictionaries.** Every episode starts cold,
  with a fresh maze and freshly drawn aliases.
- **League-side integrity mechanics** (cross-play pools, stranger matching, account separation).
  Those are league settings; the game's contribution is a single team score identical for all
  four seats and a per-episode-random board and alias set.
- **A live `/client/replay` pod viewer.** Replays are the static wasm bundle, always.
