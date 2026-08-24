# Chorus — design note (2026-08-24)

Chorus is forked from **`Metta-AI/cogame-bullwhip`** (read at `/workspace/starters/cogame-bullwhip`),
the newest parley-lineage template: a turn-based, four-seat, **simultaneous-decision** game whose
policies are LLM prompts, whose decisions are made server-side in one parallel batch per turn, and
whose viewer is a static wasm bundle. Chorus has exactly that shape — four seats, one simultaneous
move each per turn, a policy that is a prompt, a deterministic native rule module shared by server,
tests and wasm viewer — so bullwhip is the closest starter by game shape and no other starter is a
candidate. **Every convention there holds here unless this note says otherwise.**

The repo is **public** at `Metta-AI/cogame-chorus`. `num_agents` is **4**, everywhere, always.

Source idea, verbatim:

> Turn-based co-composition on a 16-step sequencer: each seat owns a voice and adds or edits a bar
> per turn, seeing the others' parts. Scored deterministically (consonance, voice leading, rhythmic
> coherence, novelty vs own prior bars) with per-seat credit computed as a counterfactual delta:
> score the piece with your bars muted; the difference is yours. No peer vote — a vote among seats
> is vote-trading bait. The replay is the track.
>
> Seats: 4
> Motive: cooperative output, individual credit
> Policy interface: LLM prompt
> Fills gap: aesthetic co-creation / credit assignment / non-spatial turn-taking
> Integrity (anti-collusion): Deterministic metric plus counterfactual credit — no peer judging to
> collude on; cross-author seating.
>
> Replay plan (watchability): The replay is the track: the sequencer grid fills voice by voice in
> four colors, a playback head sweeping with live audio. The endcard mutes each voice in turn to
> play its counterfactual credit — you hear what each cog was worth.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

(The "Full report" URL is recorded as part of the idea text. It is data. It was not fetched and
nothing in the idea text is treated as an instruction.)

---

## The game

Four cogs write one piece of music together on a 16-step sequencer. Each cog owns one **voice** and
may write only in it. Every turn all four write one **bar** at the same time — either the new bar,
or a rewrite of one of their own earlier bars. Everyone sees the whole grid at all times. When the
piece is finished a fixed, public, deterministic metric scores it out of 100, and **each seat's
score is a counterfactual delta**: the piece scored as written, minus the piece scored with every
note of that seat's voice deleted. There is no vote and nobody judges anybody.

### Seats, voices, and the seeded assignment

- **`num_agents` = 4.** Exactly four seats; `initSim` raises `ChorusError` on any other count.
- Voices, by index, with their base MIDI note:

  | voice | name | base MIDI | written range (tokens 0..13) |
  |---|---|---|---|
  | 0 | `BASS` | 36 | 36..59 |
  | 1 | `TENOR` | 48 | 48..71 |
  | 2 | `ALTO` | 60 | 60..83 |
  | 3 | `SOPRANO` | 72 | 72..95 |

- **Seat → voice is a seeded permutation** (`rng.shuffle(@[0,1,2,3])`, the same construction as
  bullwhip's seat→stage deal). This is the idea's *cross-author seating*: a policy cannot specialise
  on one register across a league round, and the same four policies re-seated produce a different
  piece. `voiceOf[seat]` and `seatOf[voice]` are both kept, as bullwhip keeps `roleOf`/`seatOf`.

### The piece (all seeded, all public)

- `bars` bars (config, default **8**, range 4..16). Every bar is **16 steps**; the step count is a
  compile-time constant `Steps = 16` (the idea pins it) and is not configurable.
- **Key**: root pitch class drawn from `[0, 2, 3, 5, 7, 9]` (`C, D, E♭, F, G, A`).
- **Mode**, drawn from four: `ionian [0,2,4,5,7,9,11]`, `dorian [0,2,3,5,7,9,10]`,
  `aeolian [0,2,3,5,7,8,10]`, `mixolydian [0,2,4,5,7,9,10]`.
- **Tempo**: `bpm = 84 + 6 * rng.rand(4)` → one of 84, 90, 96, 102, 108.
- **Chord plan**: one chord per bar, from one of four progressions tiled across the piece —
  `P0 = [0,3,4,0]` (I IV V I), `P1 = [0,5,3,4]` (I vi IV V), `P2 = [0,4,5,3]` (I V vi IV),
  `P3 = [5,3,0,4]` (vi IV I V). `chords[b] = P[b mod 4]`, a **scale degree** (0 = tonic). The chord
  tones of a chord rooted on degree `r` are `r`, `r+2`, `r+4`. **The whole plan is revealed to every
  seat and to spectators from turn 0** — it is the shared score sheet that makes coordination
  legible and the metric attainable.
- All of the above are drawn from **one** RNG stream at `initSim`, in this order: voices, root,
  mode, bpm, progression. A replay re-derives all of it from `seed` alone.

### Notation — what a seat actually writes

A bar is **16 integer tokens**, one per step:

- `-1` = **rest**.
- `0..13` = **scale degree**: `midi(v, d) = BaseMidi[v] + root + 12 * (d div 7) + Scale[d mod 7]`.
  So `0` is the tonic in the voice's register, `6` the seventh, `7` the tonic an octave up, `13`
  the seventh two octaves up. Every legal token maps to a MIDI note in 36..104.
- **Every note lasts exactly one step.** There are no ties, sustains, velocities or rests-of-length
  in v1 (see *Out of scope*). A step is an **onset** iff its token is ≥ 0.

`grid[voice][bar][step]` is the whole piece: `4 × bars × 16` integers.

### Turns and the exact resolution order

There are exactly `bars` turns, one per bar. Turn `t` runs 0 … `bars-1`:

0. **Deadline check.** Before opening turn `t`, if `epochTime() > playDeadline`
   (§*Decisions* → *Episode budget*), append the final `turn` event scored over bars `0 .. t-1` and
   settle with `reason = "deadline"`. Nothing below runs.
1. **Open.** For every voice `v`: `grid[v][t] := grid[v][t-1]` — a **hold** — or 16 rests when
   `t = 0`. `heard := says`; `says := ["","","",""]`; `orders`-equivalent `barIn := [false]*4`;
   `phase := phBars`. Append a **`turn`** event carrying `t`, `chords[t]`, and the running score of
   bars `0 .. t-1` (`piece`, `parts`, `credits`); at `t = 0` that score is `0.0` with all-zero
   parts and credits.
2. **Observe.** Build one observation per seat from the state at open (§*Server, player, protocol*
   → *Observation*). All four observations describe the same public grid; only the credit line, the
   notes and the operator prompt differ.
3. **Decide.** All non-scripted seats' LLM calls go out as **ONE parallel batch**
   (`curly.makeRequests`), one request per seat, timeout `llmTimeoutSeconds` (default **30 s**).
   Scripted seats are decided locally with no network call. Consecutive batch **starts** are floored
   at least `minTurnSpacingMs` (default **20 000 ms**) apart.
4. **Validate → retry → fall back.** A reply that times out, fails to parse, or is illegal is
   retried **once** in a smaller batch carrying an explicit hint; a seat still open after that plays
   the **`arpeggio`** scripted move, which is legal by construction.
5. **Apply, in seat order 0, 1, 2, 3.** For seat `s`, voice `v = voiceOf[s]`, reply
   `{target, steps, say, notes}`:
   - reject unless `0 ≤ target ≤ t`;
   - reject unless `steps.len == 16` and every token is `-1` or in `0..13`;
   - `grid[v][target] := steps`. If `target < t` this is an **edit** and the hold at `grid[v][t]`
     stands unchanged — spending the turn on the past costs you the new bar;
   - `says[v] := say` (rune-truncated to 100; `""` when `talk` is off);
     `notes[s] := notes` when non-empty;
   - append a **`bar`** event (`turn`, `seat`, `voice`, `target`, `steps`, `edit`, `say`,
     `scripted`, `text` = the seat's notes after the reply).

   Seat order fixes only the order of events in the replay: each seat writes only its own voice, so
   the resulting grid is order-independent. Applying is done under the state lock; the LLM batch
   runs outside it on a snapshot, exactly as bullwhip does.
6. **Resolve.** When all four `bar` events for turn `t` are in, `turnsPlayed := t + 1`.
7. **Pace.** Sleep `turnDelayMs` (default 400 ms) so a spectator can read the bar that just landed.
8. **Continue or settle.** If `turnsPlayed == bars`, append the final **`turn`** event carrying the
   complete piece score over all `bars` bars and settle `reason = "complete"`. Otherwise `t += 1`
   and go to 0.

### Scoring — the deterministic metric, exact

One function, `pieceScore(grid, n) -> tuple[piece: float, consonance, leading, rhythm, novelty:
float]`, scores the first `n` bars of a grid. It is pure, has no seed dependence beyond the key
(needed only to turn tokens into MIDI), and is the **only** scoring path in the game — the live
scoreboard, the results, the replay check and the counterfactual all call it.

Let `M(v,b,k)` be the MIDI note at voice `v`, bar `b`, step `k` (undefined when the token is `-1`).

**1. Consonance `C` (weight 0.35).** Over every *sounding pair*: every `(b, k)` and every voice pair
`u < v` with both tokens ≥ 0. Interval class `ic = |M(u,b,k) - M(v,b,k)| mod 12`. Weight:

| `ic` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `w` | 0.6 | 0.0 | 0.3 | 1.0 | 1.0 | 0.7 | 0.1 | 1.0 | 0.9 | 0.9 | 0.3 | 0.0 |

`C = mean(w)` over all sounding pairs; **`C = 0` when there are none** (silence is not consonant).

**2. Voice leading `V` (weight 0.25).** For each voice, take its sounding notes in time order across
the whole `n`-bar span (rests skipped, bars concatenated). For each consecutive pair, `L =
|Δmidi|`:

| `L` | 0–2 | 3–4 | 5–7 | 8–12 | >12 |
|---|---|---|---|---|---|
| motion score | 1.00 | 0.85 | 0.60 | 0.30 | 0.00 |

`Vraw = mean(motion score)` over all motions in all voices; `Vraw = 0` when there are none.
**Parallel-perfect penalty:** for each voice pair `u < v` and each consecutive global step index
`i, i+1` where all four of `(u,i) (v,i) (u,i+1) (v,i+1)` sound and both voices move
(`Δ ≠ 0` for each), the pair is *eligible*; it is *parallel* when `ic(i) == ic(i+1)` and
`ic(i) ∈ {0, 7}`. `p = parallel / eligible` (0 when `eligible == 0`).
**`V = Vraw × (1 - 0.5 × p)`.**

**3. Rhythmic coherence `R` (weight 0.25).** Three parts.
- **Pulse `Ra`** — per onset, by its step index `k` within the bar: `k ∈ {0,4,8,12}` → 1.0;
  `k ∈ {2,6,10,14}` → 0.7; odd `k` → 0.4. `Ra = mean` over all onsets; 0 when there are none.
- **Density `Rb`** — `density = onsets / (n * 16 * 4)`. **The denominator is always four voices,
  in the counterfactual too.** `Rb = 1` for `density ∈ [0.20, 0.55]`; rises linearly 0 → 1 across
  `[0.05, 0.20]`; falls linearly 1 → 0 across `[0.55, 0.85]`; 0 outside `[0.05, 0.85]`.
- **Interlock `Rc`** — fraction of the `n * 16` step-columns in which the number of simultaneous
  onsets is **1, 2 or 3** (not 0, not 4).

  **`R = 0.40·Ra + 0.35·Rb + 0.25·Rc`.**

**4. Novelty vs own prior bars `N` (weight 0.15).** For each voice `v` and each bar `b` in
`1 .. n-1`: `sim(v,b) = max over a < b of (positions where grid[v][b][k] == grid[v][a][k]) / 16`,
rests matching rests. `d = 1 - sim`. `raw = mean(d)` over all `v` and all `b ≥ 1`; when `n < 2`,
`raw = 0.5`.
**`N = max(0, 1 - 2·|raw - 0.5|)`** — the target is that about **half** of a bar differs from its
closest earlier sibling. Pure repetition (`raw = 0`) scores 0 and so does never repeating anything
(`raw = 1`). *Reason:* the idea asks for "novelty vs own prior bars" as a virtue, but unbounded
novelty is noise; a peak at half-change is the musically honest reading and it is the one this
game implements.

**Piece score, and its sign.** Every component is clamped to `[0, 1]` individually.

> **`S = 100 × (0.35·C + 0.25·V + 0.25·R + 0.15·N)`, in `[0, 100]`. Higher is better.**

An all-rest grid scores exactly `0.0` (`C=0`, `V=0`, `Ra=0`, `Rb=0`, `Rc=0`, `raw=0 → N=0`).

### Per-seat credit — the counterfactual, exact

`mute(grid, v)` returns the grid with **every** token of voice `v` replaced by `-1`.

> **`credit(seat) = pieceScore(grid, n).piece − pieceScore(mute(grid, voiceOf[seat]), n).piece`**

Both sides call the **identical** function with no special cases: a muted voice's bars are still
bars (they count in the novelty mean, where 16 rests repeated match perfectly and pull `raw` down),
still columns (where they lower the interlock count), and still four voices in the density
denominator. That uniformity is the whole rule; there is nothing else to implement.

- **Sign: higher is better.** `credit` is a *difference of two scores in `[0,100]`*, so it lies in
  `[-100, +100]`; in practice it sits in roughly `[-25, +25]`.
- **Credit is genuinely signed.** `C` is a *mean* over sounding pairs, so a voice that is less
  consonant than the piece's running average *lowers* `C` and can earn a negative credit — deleting
  it would improve the piece. A voice that hammers every step pushes the interlock term toward the
  4-voice case and the density term past 0.55, and can also go negative. This is the point of the
  idea and it must be preserved: prompts have to earn their seat.
- Credits do **not** sum to `S` (leave-one-out is not an exact decomposition). No test asserts that
  they do; the docs say so plainly.
- **`results.scores[i] = credit(i)`**, rounded to 6 decimals. **The league ranks on that** — mean
  episode score across a division's episodes, higher is better. `piece` is reported alongside as the
  shared, cooperative number, but it is not what ranks anybody.

### Endings and `results.reason`

Exactly two values are legal. Anything else is a defect.

| `reason` | when | scoring |
|---|---|---|
| `complete` | all `bars` turns resolved | over all `bars` bars |
| `deadline` | the play deadline was crossed **between turns** (step 0 above) | over `turnsPlayed` bars, which is always a well-formed piece (possibly 0 bars → `piece = 0`, all credits `0`) |

`deadline` is an **acceptable** ending for phase-60 verification: the piece is honestly scored on
what was written, the replay is complete, and the results are valid. There is no third path: an
episode never ends because a seat disconnected (its bars simply hold), never because the LLM is
unavailable (the scripted fallback plays), and never mid-turn (`endEarly` only settles between
turns).

### Integrity — how the idea's anti-collusion pins land

- **No peer vote anywhere.** No seat ever rates, ranks or scores another seat. There is nothing to
  trade.
- **The metric is deterministic, public and re-derivable** from the replay bytes by anyone.
- **Credit is counterfactual**, so the only way to raise your own score is to raise the piece by
  more than your absence would.
- **Cross-author seating**: seat→voice is a seeded permutation, redrawn every episode.
- The one coordination channel (`say`, 100 characters, read by all three others next turn) carries
  *musical* coordination — "I'm holding the tonic on 0 and 8, leave the low register alone". It
  cannot carry a vote because there is no vote, and it cannot buy score because score is a
  mechanical function of the grid.

### Two name spaces

- **In-game**, every seat is an anonymous cog alias (`Sprocket`, `Gizmo`, `Ratchet`, `Widget`, …)
  drawn from the seed by `tableNames(players, seed)` — bullwhip's function, kept verbatim. **No
  policy display name ever appears in a prompt**, in an observation, or in a `say`. A sim unit test
  asserts it.
- **Spectator-side**, the snapshot and the replay carry `policyNames[]` alongside `names[]`, and
  the viewer's `makeNameMap` swaps them in wherever a name is *rendered* (fillers labelled
  `Baseline (N)` keep their alias). `results.names` is the **policy** names, for the platform.

---

## Decisions: LLM with scripted fallback

**A policy is just a prompt.** The player container's only job is to deliver its prompt over the
websocket; every decision is made by the game server, which sends that prompt plus the seat's
observation to Claude. Same image, two env switches:

| policy kind | env | behaviour |
|---|---|---|
| LLM prompt | `PLAYER_PROMPT=<strategy text>` | server asks Claude every turn with that text as the operator block |
| scripted | `PLAYER_SCRIPTED=arpeggio` (also `1`/`true`/`yes`) | server plays the `arpeggio` baseline for that seat, no network |
| scripted | `PLAYER_SCRIPTED=pedal` | server plays the `pedal` baseline for that seat, no network |

Both champions are `PLAYER_PROMPT` policies; both fillers are `PLAYER_SCRIPTED` policies
(§*Packaging*). A scripted policy seated as a champion is a failure state.

### One parallel batch per turn

Decisions within a turn are **simultaneous by rule**, so all seats' LLM calls go out as **one
parallel batch per turn** via `curly.makeRequests` (bullwhip's `decideAll`, kept structurally
identical). Sequential per-seat calls are the single biggest way to blow the budget and are
forbidden here.

**Rate-limit floor.** The hosted Bedrock sidecar caps **30 requests/minute per episode** (raid,
2026-08-23). Worst case a turn issues 4 + 4 = 8 requests (batch + retry). `minTurnSpacingMs` =
**20 000 ms** between consecutive batch *starts* bounds this at 8 requests / 20 s = **24 req/min**,
under the cap. The floor is a sleep only when the turn was faster than 20 s, so it never adds to
the worst case.

### Episode budget — the arithmetic, out loud

`episodeTimeoutSeconds` is assumed **1200** when `COWORLD_TIMEOUT_SECONDS` is absent from the game
container's environment (it always is — only the worker sidecar gets it). `PlayBudgetFraction =
0.6`, so **`playDeadline = gameStart + 720 s`**.

- Worst case per turn = attempt 0 + attempt 1 = `2 × llmTimeoutSeconds` = `2 × 30 = 60 s`, plus
  `turnDelayMs` 0.4 s.
- `standard` (`bars = 8`): **8 × 60.4 ≈ 483 s** worst case, inside 720 s with 237 s of headroom.
- `long-form` (`bars = 10`): **10 × 60.4 ≈ 604 s**, inside 720 s.
- Typical (haiku answering in ~4–8 s): the 20 s spacing floor dominates → `8 × 20 = 160 s`.
- The `bars = 16` ceiling is `16 × 60.4 ≈ 966 s` > 720 s. That is *why* the deadline path exists and
  why it is scored rather than discarded; the shipped variants stay under the budget by design.
- Container start, the 180 s player-connect wait and artifact writing all live in the other 40 %
  (480 s).

### Degrade, never hang

| failure | what happens |
|---|---|
| a seat's reply times out (30 s) | that seat is retried **once** in the next batch of the same turn, with the hint text appended |
| a seat's reply is unparseable or illegal (bad `target`, wrong `steps` length, out-of-range token) | same: rejected before it touches the sim, retried once with the hint |
| still failing after the retry | the seat plays **`arpeggio`**, which is legal by construction; the `bar` event records `scripted: true` |
| no LLM credentials at all | `newLlmClient().disabled = true` from the first turn: **every** seat plays its scripted baseline (`arpeggio` when none is registered) with **no network call and no retries**, so offline certification completes in seconds |
| auth 401/403 mid-episode | client disables itself; the rest of the episode plays scripted; the episode still completes and writes artifacts |
| Bedrock 429 / model-access denial | rotate to the next Bedrock model id (haiku first — bullwhip's `bedrockModelIds()` kept verbatim), then fall back |
| a player never connects | the game starts anyway after `player_connect_timeout_seconds` (180 s) with whoever connected; a seat with no delivered prompt gets an empty operator block |
| a player socket dies | the player process wraps its receive loop in `try/except CatchableError` and **exits 0** on a dead socket (bullwhip's `src/bullwhip_player.nim` is latently buggy here — raid 0.1.3→0.1.4; chorus fixes it in the fork) |
| the 720 s play deadline is crossed | `endEarly()` between turns → `reason = "deadline"`, results and replay written normally |
| shutdown | after `results.json` and the replay are written, `/healthz` and `/global` keep answering for a bounded **20 s** grace before `quit(0)` (lantern 0.1.3→0.1.4), so a short cert episode cannot outrun the runner's post-start ping |

The episode **settles early rather than overruns**: an overrun episode is silently discarded and
keeps nothing, so a short honest piece always beats a long one that never lands.

### Prompts

**System prompt** (built by `systemPrompt(sim, seat)`, aliases only, never a policy name):

> You are `<alias>`, the `<VOICE>` voice in a four-cog studio writing one piece of music together on
> a 16-step sequencer. The other voices are `<alias> (<VOICE>)`, `<alias> (<VOICE>)`,
> `<alias> (<VOICE>)`. Each cog owns one voice; nobody else can write a note in yours and you cannot
> write a note in theirs.
>
> THE PIECE: `<bars>` bars of 16 steps, key `<ROOT> <MODE>`, `<BPM>` BPM. Every step is one note or
> a rest, and a note lasts exactly one step.
>
> NOTATION: a bar is 16 tokens. `-1` is a rest. `0..13` are scale degrees: 0 is the tonic, 6 the
> seventh, 7 the tonic an octave up, 13 the seventh two octaves up. Your voice sounds in the
> `<VOICE>` register (MIDI `<base>`..`<base+23>`).
>
> THE CHORD PLAN is fixed, shared and public: `<bar-by-bar list>`. The chord tones of a chord rooted
> on degree r are r, r+2 and r+4.
>
> EACH TURN every cog writes one bar, all four at the same time, and nobody sees the others' choice
> until the turn resolves. You may WRITE the new bar (target = this turn's index) or REWRITE one of
> your own earlier bars (target < this turn's index); if you rewrite, your new bar automatically
> holds a copy of your previous bar.
>
> THE PIECE IS SCORED 0–100 by a fixed, public, deterministic metric:
> CONSONANCE (35%) — the mean quality of every simultaneous interval between two sounding voices;
> fifths, thirds and sixths score high, seconds, sevenths and tritones score low, unisons and
> octaves 0.6.
> VOICE LEADING (25%) — the mean quality of each voice's motion between its consecutive notes; steps
> of 1–2 semitones score 1.0, leaps score less, leaps over an octave score 0; parallel fifths and
> octaves cut this term.
> RHYTHM (25%) — onsets on steps 0/4/8/12 score best, 2/6/10/14 next, odd steps least; total note
> density should sit between 20% and 55% of the whole grid; and the best steps are those where 1 to
> 3 voices sound, not 0 and not 4.
> NOVELTY (15%) — each bar is compared with the same voice's earlier bars; the target is that about
> HALF of a bar differs from the closest earlier one. Pure repetition scores 0 and so does never
> repeating anything.
>
> YOUR SCORE IS A COUNTERFACTUAL: the piece is scored once as written and once with every note of
> YOUR voice deleted; your score is the difference. Nothing else scores. There is no vote and nobody
> judges you. A voice that is rougher than the piece's average, or that fills the grid until all
> four voices sound at once, can score BELOW ZERO — deleting it would improve the piece.
>
> *(talk variant only)* Each turn you may SAY one short line (max 100 characters) that all three
> other cogs read next turn. It is not binding and may or may not be honest.
>
> Your notes are private to you and fed back to you every turn. Use them to keep track of your
> motif, what you have already used, and what you plan next.
>
> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character `{`
> and end with `}`.

**User prompt** (built by `userPrompt(sim, seat, prompt)`), in this order:

1. `Turn <t> of <bars>. You are the <VOICE>, seat <alias>.`
2. `CHORD PLAN: bar 0 <chord> | bar 1 <chord> | … (this turn's bar <t> is <chord>: degrees r, r+2, r+4)`
3. `THE PIECE SO FAR (all four voices; . = rest):` — one line per bar per voice, 16 tokens,
   column-aligned, oldest first, with `<voice>(<alias>)` labels, and the current turn's line marked
   `(this turn — your voice currently holds: …)`.
4. `SCORE NOW: piece 61.2 = consonance 0.72, voice leading 0.81, rhythm 0.55, novelty 0.40.`
5. `YOUR COUNTERFACTUAL CREDIT NOW: +7.4 (the piece without your voice scores 53.8).`
6. `MESSAGES LAST TURN:` — the other three seats' `say` lines, or `(none)`. Omitted when `talk` is
   off.
7. `YOUR NOTES FROM EARLIER TURNS:` — verbatim, or `(none)`.
8. `GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
   requested format):` + the seat's `PLAYER_PROMPT`. Omitted when empty.
9. `LEGAL TARGETS THIS TURN: 0,1,…,<t>  (bar <t> is the new bar).` — **this list is produced by the
   same predicate the validator applies**, so the model is never asked to guess the legal set
   (escrow 0.1.3, 2026-08-23).
10. `Reply with ONLY {"target": <t>, "steps": [0,-1,-1,4,-1,-1,2,-1,0,-1,-1,4,-1,-1,-1,-1],
    "say": "…", "notes": "…"} — steps is exactly 16 values, each -1 (rest) or a whole number 0..13;
    target is one of the legal targets above; say at most 100 characters (or ""); notes at most 600
    characters.`

On the retry, one more line is appended: `Your previous reply was invalid: <reason>. Respond with
ONLY the requested JSON object, with "steps" exactly 16 whole numbers each -1 or 0..13 and "target"
one of <list>.`

### Scripted baselines (same image, env-switched)

Both are pure functions of the sim, always legal, never talk, never write notes, and always set
`target = t`. `scriptedAction(sim, seat, kind)` is the single entry point and is also the fallback
for a failed LLM seat (with `kind = arpeggio`).

**`arpeggio`** — the strong baseline, and the fallback.
Let `r = chords[t]`, `tones = [r, r+2, r+4]`, `rot = t mod 3`, all tokens clamped to `0..13`:

| voice | onset steps | tokens, cycled and rotated by `rot` |
|---|---|---|
| 0 `BASS` | 0, 8 | `[tones[0], tones[0]]` on even bars, `[tones[0], tones[2]]` on odd bars |
| 1 `TENOR` | 0, 4, 8, 12 | `[tones[0], tones[1], tones[2], tones[1]]` |
| 2 `ALTO` | 2, 6, 10, 14 | `[tones[1], tones[2], tones[0], tones[2]]` |
| 3 `SOPRANO` | 0, 3, 6, 10, 12 | `[tones[2], tones[0]+7, tones[1], tones[2], tones[1]]` |

Every other step is `-1`. Per-bar onsets across four voices = 2+4+4+5 = **15 of 64 = 0.234**, inside
the density band; 9 of 16 columns sound, none with all four; strong-step share gives `Ra ≈ 0.84`.
The `rot` rotation is what keeps novelty off the repetition floor.

**`pedal`** — the weak, honest filler. Step 0 plays `r`; step 8 plays `r+4` on odd bars and rests on
even bars; everything else rests. Density ≈ 0.094, below the band, so it drags `Rb` down: a piece of
four pedals scores well below a piece of four arpeggios. It never edits and never fails.

### Reply schema, and the caps

```json
{"target": 3,
 "steps": [0,-1,-1,4,-1,-1,2,-1,0,-1,-1,4,-1,-1,-1,-1],
 "say": "holding the tonic on 0 and 8 — leave the low register to me",
 "notes": "motif A = 0 . . 4 . . 2 . ; rotate a third up next bar"}
```

| field | type | rule | cap |
|---|---|---|---|
| `target` | integer | `0 ≤ target ≤ t`; **missing → `t`** (documented default); out of range → invalid | — |
| `steps` | array of 16 integers | each `-1` or `0..13`; length exactly 16 | 16 elements |
| `say` | string | newlines collapsed to spaces; forced to `""` when `talk` is off | **100 runes** |
| `notes` | string | private, fed back verbatim next turn | **600 runes** |

**Normalisation before validation** (escrow, 2026-08-23 — normalising the structured field pre-parse
is what halves the fallback rate in a formal-output game): `steps` is also accepted as a **string**
of 16 whitespace- or comma-separated tokens where `.`, `-`, `r`, `R` and `rest` all mean a rest and
everything else must parse as an integer; a float token is rounded; a JSON array containing numeric
strings is accepted. Both spellings are documented in the prompt's example and in `rules.md`.
Trailing prose after the closing `}` is tolerated by `extractJsonObject` (bullwhip's, kept).

`PLAYER_PROMPT` delivered over the player socket is capped at **4000 runes**. Any error text that
reaches the replay is capped at **200 runes**.

> **Every string that lands in the replay — `say`, `notes`, the end reason, error text — is
> truncated on RUNE boundaries** (`runeSubStr`, bullwhip's `cleanText`), never on byte boundaries.
> A byte-boundary cut through a multi-byte character leaves invalid UTF-8 that renders in a browser
> and fails a strict JSON parser, which is exactly what phase-60 check 4 tests.

---

## Sim module

`src/chorus/sim.nim` is a fork of `src/bullwhip/sim.nim`: pure rules, no IO, no networking, no LLM.
The server, the tests and the **wasm replay viewer all drive this same module** — that is what makes
the static viewer possible.

### `src/chorus/types.nim` (fork of `src/bullwhip/types.nim`)

```nim
type
  ChorusError* = object of CatchableError
  PlayerConfig* = object
    name*: string
  GameConfig* = object
    tokens*: seq[string]
    players*: seq[PlayerConfig]
    seed*: int
    bars*: int                       ## turns in the episode (4..16, default 8)
    talk*: bool                      ## seats may send one 100-char line a turn
    episodeTimeoutSeconds*: int      ## assumed platform kill time (1200)
    sampled*: bool                   ## true once the budget cap is applied
    turnDelayMs*: int
    minTurnSpacingMs*: int           ## floor between LLM batch starts (20000)
    playerConnectTimeoutSeconds*: float
    model*: string
    maxOutputTokens*: int
    llmTimeoutSeconds*: int
```

`defaultGameConfig()`: `bars 8`, `talk true`, `episodeTimeoutSeconds 1200`, `turnDelayMs 400`,
`minTurnSpacingMs 20000`, `playerConnectTimeoutSeconds 180`, `model "claude-sonnet-5"`,
`maxOutputTokens 900`, `llmTimeoutSeconds 30`. `update(config, json)` applies a runtime JSON config
and raises `ChorusError` when `bars < 4` or `bars > 16`.

`sampleEpisode(config)` clamps `bars` into `4..16` and caps `turnDelayMs` at
`PacingBudgetMs div bars` (`PacingBudgetMs = 60_000`); idempotent via `sampled`, exactly as
bullwhip's.

### `src/chorus/sim.nim`

Constants: `Voices* = 4`, `Seats* = 4`, `Steps* = 16`, `Rest* = -1`, `MaxToken* = 13`,
`MinBars* = 4`, `MaxBars* = 16`, `MaxSayLen* = 100`, `PacingBudgetMs* = 60_000`,
`VoiceNames* = ["Bass","Tenor","Alto","Soprano"]`, `BaseMidi* = [36, 48, 60, 72]`,
`RootPitches* = [0,2,3,5,7,9]`, `RootNames* = ["C","D","E♭","F","G","A"]`,
`ModeNames* = ["ionian","dorian","aeolian","mixolydian"]`, the four `Scales`, the four
`Progressions`, the consonance weight table `ConsonanceW[12]`, the strong-step table `PulseW[16]`,
and `CogNames*` copied verbatim from bullwhip.

```nim
type
  Phase* = enum
    phBars = "bars"
    phDone = "done"

  Bar* = array[Steps, int]

  Sim* = object
    config*: GameConfig
    names*: seq[string]                       ## anonymous aliases per seat
    voiceOf*: array[Seats, int]
    seatOf*: array[Voices, int]
    root*: int
    rootName*: string
    mode*: int
    bpm*: int
    chords*: seq[int]                         ## one chord-root degree per bar
    grid*: array[Voices, seq[Bar]]            ## [voice][bar][step]
    turn*: int
    barIn*: array[Voices, bool]               ## this turn's bar submitted?
    lastTarget*: array[Voices, int]
    lastEdit*: array[Voices, bool]
    says*: array[Voices, string]
    heard*: array[Voices, string]
    notes*: seq[string]
    turnsPlayed*: int
    phase*: Phase
    done*: bool
    reason*: string                           ## "complete" | "deadline"
    events*: seq[GameEvent]
```

Public procs (the whole surface the server, tests and viewer use):

| proc | contract |
|---|---|
| `tableNames(players, seed)` | bullwhip's, verbatim: seeded shuffle of `CogNames` |
| `sampleEpisode(config)` | idempotent budget fit |
| `initSim(config)` | raises `ChorusError` unless `players.len == 4`; draws voices, root, mode, bpm, progression from one seeded stream; logs `start` then opens turn 0 |
| `pendingSeats(sim)` | seats whose bar for the live turn is not in, in seat order; empty when done |
| `midiOf(sim, voice, token)` | token → MIDI; `-1` → `-1` |
| `pieceScore(sim, grid, n)` | the metric above; returns `(piece, consonance, leading, rhythm, novelty)` |
| `mutedGrid(grid, voice)` | every token of `voice` → `-1` |
| `credits(sim, n)` | `array[Seats, float]`, `piece − piece(mute(voiceOf[seat]))` |
| `score(sim, seat)` | `credits(sim, sim.turnsPlayed)[seat]` |
| `applyBar(sim, seat, target, steps, say, notes, scripted)` | validates, writes, logs the `bar` event, resolves the turn when the fourth lands; raises `ChorusError` on anything illegal **without mutating** |
| `endEarly(sim)` | settles `deadline` between turns; no-op when already done |
| `resultsJson(sim)` | platform-facing results (policy names) |
| `tableStateJson(sim)` | one viewer frame |
| `replayMatch(config, events)` | re-derives the frame timeline from the recorded events |
| `eventToJson` / `eventFromJson` | event codec |

### Event vocabulary

One flat `GameEvent` object, as in bullwhip, so the codec stays trivial:

```nim
type
  EventKind* = enum
    evStart = "start"
    evTurn  = "turn"
    evBar   = "bar"
    evEnd   = "end"

  GameEvent* = object
    kind*: EventKind
    turn*: int            ## turn/bar: the live turn; end: turnsPlayed; start: -1
    seat*: int            ## bar: the seat; -1 otherwise
    voice*: int           ## bar: the seat's voice; -1 otherwise
    target*: int          ## bar: the bar index written; -1 otherwise
    edit*: bool           ## bar: true when target < turn
    steps*: seq[int]      ## bar: the 16 tokens
    say*: string          ## bar: the seat's line ("" when silent)
    scripted*: bool       ## bar: decided by a scripted baseline / fallback
    text*: string         ## bar: the seat's notes after the reply; end: reason
    chord*: int           ## turn: this bar's chord-root degree; -1 otherwise
    piece*: float         ## turn: running piece score over bars 0..turn-1
    parts*: array[4, float]   ## turn: consonance, leading, rhythm, novelty
    credits*: seq[float]      ## turn: running per-seat credit, by seat
```

JSON, written by `eventToJson`, floats rounded to 6 decimals:

| kind | keys |
|---|---|
| `start` | `kind` |
| `turn` | `kind`, `turn`, `chord`, `piece`, `parts` (4 floats), `credits` (4 floats) |
| `bar` | `kind`, `turn`, `seat`, `voice`, `target`, `edit`, `steps` (16 ints), `say` (omitted when empty), `scripted`, `text` (omitted when empty) |
| `end` | `kind`, `turn`, `text` (the reason) |

`replayMatch(config, events)` re-derives the whole timeline by replaying **`bar` events only**
through the rules — voices, key, mode, bpm and the chord plan all come from the seed. A `turn`
event is a **check**, not a source: its `chord`, `piece`, `parts` and `credits` must match the
re-derivation (floats within `1e-4`) or `ChorusError` is raised. An `end` event settles a `deadline`
that the bar events alone cannot express. `frames[i]` = the state after `events[0 ..< i]`, so
`replayMatch(...).len == events.len + 1`.

Event count for a `complete` episode of `B` bars: `1 + (B + 1) + 4B + 1 = 5B + 3` (43 for `B = 8`).

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"seats": [{"name": "Sprocket", "seat": 0, "voice": 2, "voiceName": "Alto",
            "base": 60, "score": 7.412, "onsets": 21,
            "bars": [[0,-1,...],[...]], "say": "…",
            "heard": [{"seat": 1, "say": "…"}], "notes": "…",
            "pending": false, "lastTarget": 3, "lastEdit": false} , … ×4 by SEAT],
 "voiceSeat": [2, 0, 3, 1],
 "grid": [[[...16],…], … ×4 by VOICE],
 "chords": [0, 3, 4, 0, 0, 3, 4, 0],
 "chordNames": ["I","IV","V","I","I","IV","V","I"],
 "key": "C", "mode": "dorian", "bpm": 96, "steps": 16,
 "turn": 3, "turns": 8, "turnsPlayed": 3,
 "piece": 61.203, "parts": {"consonance": 0.72, "leading": 0.81,
                            "rhythm": 0.55, "novelty": 0.40},
 "credits": [7.412, -1.030, 3.884, 5.219],
 "history": [{"turn": 0, "piece": 0.0, "credits": [0,0,0,0]}, …],
 "phase": "bars", "gameDone": false, "reason": ""}
```

`history` is one row per resolved turn and is what the score strip charts. The server adds `type`,
`game`, `policyNames`, `events`, `started`, `done` and `connected` on top for `/global`, exactly as
bullwhip does.

### `resultsJson` — platform-facing, policy names

```json
{"names": ["chorus-cantor", "chorus-arpeggio", "chorus-weaver", "chorus-pedal"],
 "scores": [7.412, -1.030, 3.884, 5.219],
 "voices": ["Alto", "Bass", "Soprano", "Tenor"],
 "onsets": [21, 12, 27, 8],
 "piece": 61.203,
 "consonance": 0.72, "leading": 0.81, "rhythm": 0.55, "novelty": 0.40,
 "key": "C dorian", "bpm": 96,
 "bars": 8, "maxBars": 8, "reason": "complete"}
```

`scores` is the **counterfactual credit**, higher is better; that is what the league ranks on.

### Replay payload — `chorus.replay.v1`

**The replay bytes are self-sufficient**: everything the viewer needs is in them, and no server is
contacted except S3 for the file itself.

```json
{"protocol": "chorus.replay.v1",
 "names": ["Sprocket","Gizmo","Ratchet","Widget"],
 "policyNames": ["chorus-cantor","chorus-arpeggio","chorus-weaver","chorus-pedal"],
 "config": {"bars": 8, "steps": 16, "seed": 918273, "talk": true, "sampled": true},
 "events": [ … every event, in order … ],
 "results": { … resultsJson … }}
```

`seed` re-derives the seat→voice permutation, the key, the mode, the bpm, the chord plan and the
aliases; `names` gives the in-game aliases and `policyNames` the spectator-side names; `events`
gives every per-turn state via `replayMatch`; `results` gives the endcard. Nothing else is needed
and nothing else is fetched.

---

## Server, player, protocol

### `src/chorus/server.nim` (fork of `src/bullwhip/server.nim`)

Routes, unchanged in shape from bullwhip and **registered before any catch-all asset route**
(lantern 0.1.1 — the certifier probes `/client/player` and `/client/global` *before* player pods
start, and a 404 there is a `game_contract_violation`):

```
GET /healthz                     -> {"ok": true}
GET /client/global               -> client/global.html
GET /client/player               -> client/player.html
GET /client/replay               -> client/replay_broadcast.html
GET /client/renderer.js          -> client/renderer.js
GET /client/chrome_common.js     -> client/chrome_common.js
GET /client/chrome.css           -> client/chrome.css
GET /client/assets/@name         -> data/<name>   (no "/", "\", or leading ".")
WS  /player?slot=N&token=T       -> chorus.player.v1     (live mode only)
WS  /global                      -> spectator snapshots
WS  /replay                      -> the enriched replay payload (replay mode)
```

Neither `/client/` HTML route opens a player socket. `mummy` hands `Ping` frames to the application,
so the websocket handler answers a `Ping` with a `Pong` (bullwhip's code, kept verbatim — the
certifier pings `/global`).

The game thread is bullwhip's `runGame` with the turn loop of §*The game*: connect wait →
`newLlmClient` → per-turn `{deadline check, snapshot under lock, decideAll outside the lock, apply
under the lock, broadcast, pace}` → `finishEpisode`. `finishEpisode` sends the `final` frames to the
players **before** writing artifacts (the worker tears player pods down as soon as `results.json`
exists), writes results and the replay, then holds the server up for the 20 s shutdown grace.

### Observation — exactly what each seat sees, and what is hidden

**Visible to a seat** (all of it inside the prompt built server-side):

- Its own alias, its voice name, its base MIDI and its written range.
- The other three seats' aliases and voices.
- Key, mode, bpm, `bars`, the current turn index, `Steps = 16`.
- **The complete grid so far — all four voices, every bar, every step.** Nothing about the music is
  hidden; that is what "seeing the others' parts" means.
- The full chord plan for every bar, from turn 0.
- The current piece score and all four components.
- **Its own** counterfactual credit, and the piece score without its voice.
- The other three seats' `say` lines from **last** turn (`talk` on).
- Its own private notes.
- The legal `target` list for this turn, computed by the validator's own predicate.

**Hidden from a seat:**

- **The other seats' credits** and the other seats' notes. *Reason:* the piece score is the shared
  signal and your own credit is your private one; publishing all four credits in-prompt would invite
  explicit credit-trading talk, which is what the idea's integrity note is guarding against.
  Spectators see all four, and the endcard reveals them.
- **The other seats' move for the current turn** — decisions are simultaneous; a seat sees another
  seat's bar only after the turn resolves.
- **Every policy display name.** Seats know each other only as aliases.
- Nothing else. The metric, its weights, the chord plan and the whole grid are public by design:
  the game is co-composition against a known ruler, not a guessing game.

### Player protocol — `chorus.player.v1`

All JSON text frames over the socket named by `COWORLD_PLAYER_WS_URL` (which already carries
`?slot=N&token=T`).

`game -> player`:

```json
{"type":"welcome","protocol":"chorus.player.v1","slot":0,"name":"Sprocket",
 "voice":"Alto","base":60,"bars":8,"steps":16,"key":"C","mode":"dorian","bpm":96}
{"type":"state","slot":0,"name":"Sprocket","voice":"Alto",
 "seat":{"voice":2,"voiceName":"Alto","base":60,"score":7.412,"onsets":21,
         "bars":[[…16…],…],"notes":"…"},
 "piece":61.203,"turn":3,"turns":8,"turnsPlayed":3,
 "started":true,"done":false,"reason":""}
{"type":"final","done":true,"scores":[…],"voices":[…],"names":[aliases],
 "piece":61.203,"bars":8,"reason":"complete","slot":0}
```

The `state` frame is **redacted to the seat's own voice, its own credit and the shared piece
score** — the other seats' credits and notes are not in it. Decisions are server-side, so this
costs the policy nothing. `final` carries the table **aliases**, not policy names (results carry
policy names, for the platform).

`player -> game`:

```json
{"type":"prompt","prompt":"<your strategy, max 4000 runes>","scripted":"arpeggio"}
```

Sent immediately on connect and again after `welcome` (in case the first send raced slot
registration). `scripted` is `""` for an LLM policy, `"arpeggio"` (or `"1"`/`"true"`/`"yes"`) or
`"pedal"`. Anything else parses to `skNone`. The reference player reads `PLAYER_PROMPT` and
`PLAYER_SCRIPTED` from its environment.

### Global protocol

A spectator websocket to `/global` receives the full snapshot as JSON after **every** event:
`tableStateJson` plus `type`, `game: "chorus"`, `policyNames[]`, the append-only `events[]`
transcript, `started`, `done` and `connected[]`. Voices are `0 Bass, 1 Tenor, 2 Alto, 3 Soprano`;
seats are indexed by slot and mapped through `voiceSeat`. The browser page at `/client/global`
renders the sequencer live; `/client/replay` plays a recorded episode; the static bundle renders
hosted replays at `index.html?replay=<url>`.

### `src/chorus_player.nim` (fork of `src/bullwhip_player.nim`)

Connect → send the prompt frame → re-send on `welcome` → idle until `final` → close → exit 0. Two
changes from the starter:

1. The receive loop is wrapped in `try/except CatchableError` and **exits 0** on a dead socket
   (whisky's `receiveMessage` raises on a close frame or truncated read, and mummy's `send` only
   queues, so the game's `quit(0)` can outrun the flushed `done` frame — raid 0.1.3→0.1.4).
2. The `DefaultPrompt` is a chorus strategy in words, used when `PLAYER_PROMPT` is empty:

> Write musically and earn your seat. Your score is the piece with your voice minus the piece
> without it, so every bar has to pay for itself. Land your onsets on steps 0, 4, 8 and 12 first and
> use the odd steps sparingly. Play the chord tones of this bar's chord (r, r+2, r+4) on the strong
> steps and pass through neighbours on the weak ones. Move by step wherever you can and never leap
> more than an octave. Watch the other voices: if a step already has three voices sounding, rest;
> if the grid is thin, add. Keep a motif in your notes and vary about half of it each bar — repeat
> nothing exactly and never start from scratch either. Spend a turn rewriting an early bar only when
> the score strip says that bar is the weak one.

---

## Viewer

### The four viewer files — one starter, no splicing

**All four viewer files come from one starter, `Metta-AI/cogame-bullwhip`, and only from it:**

| file | source |
|---|---|
| `replay-viewer/config.nims` | `cogame-bullwhip/replay-viewer/config.nims` |
| `replay-viewer/chorus_replay.nim` (the wasm entry) | `cogame-bullwhip/replay-viewer/bullwhip_replay.nim` |
| `replay-viewer/static_replay.js` | `cogame-bullwhip/replay-viewer/static_replay.js` |
| `replay-viewer/index.html` | `cogame-bullwhip/replay-viewer/index.html` |

Nothing is spliced in from another starter. Bullwhip's emscripten link flags are kept exactly as
they are, with only the names substituted: `-O2`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`,
`ENVIRONMENT=web`, `MODULARIZE=1`, **`EXPORT_NAME=ChorusReplayModule`**,
`EXPORTED_RUNTIME_METHODS=HEAPU8`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_ch_load_replay,_ch_payload_ptr,_ch_payload_len,_ch_error_ptr,_ch_error_len`,
`--mm:arc`, `--exceptions:goto`, `-d:useMalloc`, plus
`emscripten_exit_with_live_runtime()` in `isMainModule`. `static_replay.js` keeps calling the module
through that same `ChorusReplayModule()` **factory** — the `MODULARIZE`/`EXPORT_NAME` contract and
the JS bootstrap must stay from the same starter. (cogame-lantern, 2026-08-23: one starter's shell
on another's link flags deadlocks the viewer silently, with every asset returning 200.)

The wasm module parses the replay bytes with the **same `src/chorus/sim.nim`** the game server runs,
re-derives every frame with `replayMatch`, and exposes the enriched payload (identical shape to the
`/replay` websocket message) for `renderer.js` to draw.

### Load signalling

- `renderer.js`'s `attachReplay` sets
  `document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame**
  — bullwhip already does exactly this at the end of `attachReplay`'s `makeRenderer` callback, and
  it is kept. `static_replay.js` additionally posts the `coworld-replay` `{type:"ready"}` envelope
  one animation frame later.
- `static_replay.js` sets **`data-replay-error="<message>"`** on `<html>` and posts
  `{type:"error"}` on any failure — missing `?replay=`, the 20 s fetch timeout, a non-200, a wasm
  rejection — and removes the attribute on a successful retry. The Retry button re-fetches without
  a page reload.
- Nothing about audio ever gates these signals.
- `tools/ci/viewer_smoke.mjs` reads exactly these two signals.

### Bundle and build hook

`"replay_viewer": {"bundle": "static-replay-viewer"}` in the manifest. **Never a `/client/replay`
pod URL.** `tools/build_replay_viewer.sh` (bullwhip's hook, paths renamed, committed **`chmod +x`**)
is the `coworld build` hook: it compiles `replay-viewer/chorus_replay.nim` to wasm with local
`emcc`+`nim` when both exist, otherwise inside the pinned `emscripten/emsdk` container from
`Dockerfile.replay-viewer`, then copies `chorus_replay.js`, `chorus_replay.wasm`,
`replay-viewer/index.html`, `replay-viewer/static_replay.js`, `client/chrome_common.js`,
`client/renderer.js`, `client/chrome.css` and `data/*` into the bundle. It **`mkdir -p`s the output
parent before the containment check** (ecos, 2026-08-23: paintbot's hook exits 1 on a fresh CI
checkout because `coworld build` pre-creates that directory and CI does not).

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte from the starter.** Every function in it is
  `cogame-bullwhip/client/renderer.js`'s function, character for character, with no edits:
  `assetUrl`, `loadImages`, `seatColor`, `ellipsize`, `hexToRgb`, `rgba`, `roundRect`, `wrapLines`,
  `escapeHtml`, `clampName`, `isBaselineFiller`, `makeNameMap`, `applyNames`, `makeEffects`,
  `bindFeedToggle`, and the palette constants `COLORS`, `COLOR_HEX`, `PAPER`, `PAPER_DIM`, `INK`,
  `AMBER`, `GHOST`, `STRIP`. The only non-copied lines are the IIFE wrapper, the
  `window.ChorusChrome = {…}` export, and **one clearly-marked added function**, `relayout()`
  (below). Nothing transplanted is rewritten, reindented or renamed.
- **`client/chrome.css` is copied unchanged** from `cogame-bullwhip/client/chrome.css`. Chorus's
  additions live in one appended block at the end of the file, marked
  `/* ---------- chorus additions ---------- */`; no existing rule is edited.
- **`client/replay_broadcast.html` is the starter's page with a game block appended.** It *is*
  `cogame-bullwhip/client/replay.html`, with (a) the identifier renames a fork requires —
  `BullwhipRenderer` → `ChorusRenderer`, the `<title>`, and the `#wordmark` text `BULL<span>WHIP` →
  `CHO<span>RUS` — (b) **one inserted line**, `<script src="/client/chrome_common.js"></script>`
  immediately *before* the starter's `<script src="/client/renderer.js">` (load order: the game
  block reads `window.ChorusChrome` lazily inside functions, but the chrome module must exist before
  the inline bootstrap calls `bindFeedToggle`), and (c) the chorus **game block appended before
  `</body>`** — the `♪ AUDIO` button inside the existing `.tbar`, and the grid legend strip. It is
  **not** a from-scratch page that reuses the starter's ids (cogame-gridlock, 2026-08-23).
  `client/global.html` and `client/player.html` are forked the same way.
- **Elements removed from the starter page: none.** `#layout`, `#stage`, `#topband`, `#wordmark`,
  `#clock`, `#topright`, `#statuschip`, `#feedtoggle`, `#scorebug`, `#board-wrap`, `#table`,
  `#lightpool`, `#grain`, `#endscreen`, `#transport`, `#scrub`, `.tbar`, `#play`, `#pos`, `#feed`
  and `#loading` are all kept, with their ids and their CSS. `#lightpool` and `#grain` are pure
  atmosphere and stay.
- **Zoom: dropped entirely.** There is no `#viewpanel`, no zoom bar and no minimap. The board is a
  fixed `bars × 16` grid that is always rendered to fit the frame — it is never larger than the
  frame, so the zoom chrome would be dead weight. (The starter has none either; none is added.)

### Transport rules

- **`--band` and `--hudscale` are set on `:root` by `relayout()`** — the one added function in
  `chrome_common.js`. It measures `#topband` and `#transport` with `getBoundingClientRect()` and
  writes `--topband`, `--band` and `--hudscale` (`clamp(0.7, stageWidth / 960, 1.6)`) on
  `document.documentElement`. It runs on `load`, on every `resize`, and after every `bindFeedToggle`
  toggle. All chorus-added chrome measures derive from `--hudscale`, never from the viewport.
- **No overlay sits in the transport band.** `#transport` is the last flex row of `#stage`;
  `#endscreen` is `position: absolute; inset: 0` **inside `#board-wrap`**, which is a *sibling above*
  `#transport`, so it structurally cannot cover the band. Chorus additionally pins
  `#endscreen { bottom: var(--band, 0px); }` in its appended CSS block so the rule still holds if
  the endcard is ever repositioned against `#stage`. `#loading` is the only full-frame overlay and
  it is `display: none`d the instant the payload attaches, before playback starts.
- **The endcard is dismissed by every seek.** `attachReplay`'s `setIndex` calls
  `updateEndscreen(container, results, index >= events.length && events.length > 0, …)` on **every**
  index change, and `updateEndscreen`'s first statement is
  `container.classList.toggle("show", !!show)` — so any seek below the last event hides it
  immediately. This is bullwhip's behaviour, kept.
- **Scrubber beats are clickable, labelled buttons.** `buildChorusScrub` (in the game block, *not*
  in `chrome_common.js`) builds one `<button class="beat-marker …">` per emitted beat, each with
  `type="button"`, an `aria-label` and a `title` (`"Bar 3 — Sprocket (Alto) writes 6 notes"`), and an
  `onclick` that seeks to that event index. Drag-to-seek on the track is kept alongside. **CSS for
  every kind emitted**, in the appended block:

  | kind emitted | class | CSS |
  |---|---|---|
  | `bar`, write | `.beat-marker.bar.seat<i>` | 2 px tick, seat colour via `--tc` |
  | `bar`, edit | `.beat-marker.edit.seat<i>` | 3 px tick with a notch, seat colour |
  | `turn` | `.beat-marker.turn` | 1 px amber hairline, full height |
  | `end` | `.beat-marker.end` | 3 px × 14 px amber block (reuses the starter's `.death` geometry) |
  | `start` | `.beat-marker.start` | 2 px ghost tick |

  The builder is named `buildChorusScrub` and the marker helper `chorusMarkBeat` — **no game-block
  function may share a name with any key of `ChorusChrome`**, because a `var markBeat = C.markBeat`
  alias block plus a hoisted `function markBeat` silently shadows the chrome one (tandem,
  2026-08-23). A CI check asserts the disjointness (§*Tests*).

### The stage — what the viewer draws

Canvas scene, over `data/arena_floor.png` in the starter's Ink & Print palette, seat colours
`red / blue / green / yellow` from `COLORS`:

- **The sequencer grid** (top ~62 %). `bars × 16` columns, four lanes, one lane per **voice**
  (labelled `BASS / TENOR / ALTO / SOPRANO` with the owning seat's alias-or-policy name). Within a
  lane every onset is a small block whose **vertical position encodes its pitch** (a mini piano
  roll, token 0 at the lane floor, token 13 at the lane ceiling) and whose **colour is the owning
  seat's colour** — so the grid literally "fills voice by voice in four colours". Bar boundaries are
  drawn as brighter verticals; steps 0/4/8/12 get a ghost gridline. A bar written this turn glows
  for `SLIDE_MS`; a bar that was **edited** flashes its outline amber and shows a small `EDIT` tag,
  reusing the starter's eased-timer effects (`makeEffects`, `SLIDE_MS`/`SLIP_MS`).
- **The playhead**: a vertical amber sweep. During playback it advances step by step at
  `60 / bpm / 4` seconds per step through the bar being read; between events it rests on the live
  bar. It is the same line whether audio is on or off.
- **The chord ribbon**, directly above the grid: one chip per bar, `I / IV / V / vi`, the live bar's
  chip amber.
- **The score strip** (bottom ~24 %, the slot bullwhip gives its seismograph): the piece score per
  resolved turn as a paper line against a 0–100 axis, plus four seat-coloured **credit** lines on a
  signed axis with a zero rule. This is credit assignment, drawn: a seat whose line sits below zero
  is visibly costing the piece.
- **`#lightpool`** sweeps to the leading seat on the final frame.

### Readouts

- **`#clock`** — `BAR 3 / 8 · C DORIAN · 96 BPM` while writing, with `· WAITING ON 2` or
  `· BARS IN` appended; `FINAL — PIECE 68.4` once done; `FINAL — PIECE 41.0 · DEADLINE` on a
  deadline ending.
- **`#scorebug`** — one plate per seat: name (policy name spectator-side, alias for fillers), voice
  tag (`BASS` / `TENOR` / `ALTO` / `SOPRANO`), **credit signed to one decimal** (`+7.4`, `−1.0`),
  and `▶` while the seat is pending. `.plate-name` keeps the starter's
  `flex: 1 1 auto; min-width: 3.2em`.
- **`#feed`** (side panel, `LOG »` toggle, grouped one section per turn under a `BAR 3` head):
  `Sprocket (Alto) writes bar 3 — 6 notes, starts on the third`;
  `Gizmo (Bass) edits bar 1 — 4 notes ·` (the `·` marks a scripted decision, as bullwhip does);
  `Sprocket says: "…"`; dim `Sprocket notes: "…"` only when a seat's notes change;
  `BAR 3 — piece 61.2 (cons .72 · lead .81 · rhy .55 · nov .40)`;
  `FINAL — piece 68.4 · credits Sprocket +9.1, Gizmo −1.0, Ratchet +3.9, Widget +5.2`;
  `Episode deadline — the piece was scored on 5 of 8 bars.`
- **`#pos`** — `17 / 43` (event index), the starter's.
- **`#endscreen`** — title `FINAL — 8 BARS · PIECE 68.4`; verdict
  `SPROCKET CARRIED THE PIECE` (or `ALL LEVEL`); a `deadline` sub-line when applicable; ranked rows
  by credit with columns `rank`, `name`, `voice`, `credit`, `notes played`, `piece without you`.
  Each row carries a **`PLAY WITHOUT <name>`** button (below).

### Audio — what v1 actually ships

The idea's "live audio" and "the endcard mutes each voice in turn" are shipped, in the smallest form
that is honest:

- **WebAudio synthesis, in-bundle, no assets.** Four `OscillatorNode` timbres — bass `triangle`,
  tenor `sawtooth`, alto `square`, soprano `sine` — each note through its own `GainNode` with a
  5 ms attack / 120 ms decay, into a shared `DynamicsCompressorNode` and a master gain of 0.25.
  A step is `60 / bpm / 4` seconds. *Reason for shipping it:* it is ~80 lines, needs no assets, no
  new build step and no network, and it is the idea's whole payoff.
- **Off by default, behind one `♪ AUDIO` button** in the transport bar (`.tbtn`, inside the band,
  never overlaid on it). The `AudioContext` is constructed only on that button's first click, which
  is the user gesture browser autoplay policy requires. Never more than one bar is scheduled ahead;
  a seek cancels every scheduled node.
- **Fully fenced.** Every AudioContext call is inside `try/catch`; on any failure the button becomes
  `♪ AUDIO N/A`, is disabled, and the viewer continues visual-only. **Audio never gates
  `data-replay-loaded` and never touches the render loop**, so the headless CI smoke is unaffected.
- **The counterfactual endcard**: each endcard row's `PLAY WITHOUT <name>` button re-plays the whole
  finished piece with that voice's notes muted, so a spectator *hears* what the cog was worth; a
  `STOP` button cancels. The buttons are hidden when audio is off or unavailable. The credit numbers
  are always shown, audio or not.

### Legible at 360 px wide

The featured-match iframe on softmax.com is about **360 px** wide, and the viewer is checked there,
not at desktop width.

- The canvas re-fits on `resize` (`fit()` in `index.html` and in `replay_broadcast.html`, kept
  verbatim), and `relayout()` re-derives `--hudscale`.
- **Below 560 px** the stage switches to a compact composition: the **current bar full-width** (16
  columns × 4 lanes, blocks large enough to count) plus a one-line thumbnail of the whole piece
  underneath with the playhead on it. The chord ribbon shrinks to the live chip only. The score
  strip keeps the piece line and the four credit lines but drops the axis labels.
- **Below 640 px** the scorebug hides the `.plate-label` voice tags and keeps name + credit;
  `.plate-name` shrinks last and never below 3.2 em.
- The feed collapses behind the existing `LOG »` toggle.
- Words are words and numbers are numerals: `BASS`, not `B`; `piece 61.2`, not `p61`; `+7.4`, not
  `7.4↑`.

---

## Packaging

- **`compose.yaml`** — one service named **`chorus`** (the manifest image placeholder is derived
  from the compose service name, so it must be `{{CHORUS_IMAGE}}`; `{{GAME_IMAGE}}` is not a thing —
  lantern 0.1.0), `image: coworld-chorus:latest`, `platform: linux/amd64`,
  `build: {context: ., network: host}`.
- **`Dockerfile`** — bullwhip's, renamed: one image, two entrypoints `/bin/chorus` (default `CMD`)
  and `/bin/chorus-player`; `data/` and `client/` copied into the run image.
  **`Dockerfile.replay-viewer`** — bullwhip's, renamed.
- **`chorus.nimble`** — version `0.1.0`, `srcDir = "src"`, `requires "nim >= 2.2.4"`, `bitworld`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`; `nimby.lock` copied from bullwhip.
- **`data/`** — bullwhip's `arena_floor.png`, `font.ttf`, `FONT_LICENSE.txt` and the four
  `soldier_<red|blue|green|yellow>_front.png` cog sprites, used as the four seat portraits beside
  their lane labels. Real art from the starter, no placeholder boxes.
- **`README.md`** — the game in a paragraph, the layout list, the local loop, how to field a policy.

### `coworld_manifest_template.json`

Top level: `$schema`, **≥3 `tags`** (`music`, `co-creation`, `credit-assignment`, `turn-based`,
`four-player`, `llm-driven`, `cooperative`, `sequencer`), `game`, top-level `player[]`, `variants[]`,
`certification`, `episode_timeout_minutes: 20`.

`game`: `name: "chorus"`, `runnable.type: "game"`, `image: "{{CHORUS_IMAGE}}"`,
`run: ["/bin/chorus"]`, `env.ANTHROPIC_API_KEY_URI:
"secret://coworld/chorus/anthropic_api_key"` (**without this the hosted container never receives the
secret and every league episode plays scripted while local certify still passes** — hive,
2026-08-23), `source_url: "https://github.com/Metta-AI/cogame-chorus/tree/main"`,
`owner: "daveey@gmail.com"`, and `"replay_viewer": {"bundle": "static-replay-viewer"}`.

**`game.config_schema`** — a real JSON Schema, `additionalProperties: false`,
`required: ["tokens","players"]`. **Every array property carries `minItems` and `maxItems`** (tandem
0.1.0, 2026-08-23):

| property | type | bounds |
|---|---|---|
| `tokens` | array of non-empty strings | `minItems: 4`, `maxItems: 4` |
| `players` | array of `{name}` objects | `minItems: 4`, `maxItems: 4` |
| `num_agents` | integer | `minimum: 4`, `maximum: 4` |
| `seed` | integer | — |
| `bars` | integer | `4..16`, default `8` |
| `talk` | boolean | default `true` |
| `episodeTimeoutSeconds` | integer | `60..6000`, default `1200` |
| `turnDelayMs` | integer | `0..10000`, default `400` |
| `minTurnSpacingMs` | integer | `0..60000`, default `20000` |
| `model` | string | default `claude-sonnet-5` |
| `maxOutputTokens` | integer | `64..2000`, default `900` |
| `llmTimeoutSeconds` | integer | `5..300`, default `30` |
| `player_connect_timeout_seconds` | number | `minimum: 0`, default `180` |

**`game.results_schema`** — `additionalProperties: false`; required `names`, `scores`, `voices`,
`onsets`, `piece`, `consonance`, `leading`, `rhythm`, `novelty`, `key`, `bpm`, `bars`, `maxBars`,
`reason`. `names`/`scores`/`voices`/`onsets` all `minItems: 4, maxItems: 4`; `scores` items
`minimum: -100, maximum: 100`; `piece` `0..100`; the four component fields `0..1`; `bars` integer
`≥ 0`; `maxBars` integer `≥ 4`; `reason` string.

**`game.protocols`** — **both** keys:
- **`player`**: the full `chorus.player.v1` text of §*Server, player, protocol* — every frame shape,
  the 4000-rune prompt cap, the `scripted` values, and "a Chorus policy is a prompt: the player
  container's only job is to deliver it".
- **`global`**: the full `/global` snapshot shape, the voice indexing (`0 Bass, 1 Tenor, 2 Alto,
  3 Soprano`), the note that the events array is the complete append-only transcript, the note that
  a seat's own credit is the only credit in its own frames while spectators see all four, and the
  static-bundle note (`index.html?replay=<url>`).

**`game.docs`** — **both** keys:
- **`readme`**: one paragraph — four cogs, one voice each, `bars` bars of a 16-step sequencer, a
  fixed public metric, counterfactual credit, no vote; how to field a policy (`PLAYER_PROMPT`); the
  two scripted baselines.
- **`pages`**: two entries.
  - `rules.md` — voices and the seeded assignment, notation and the token table, the chord plan, the
    numbered resolution order, the hold-versus-edit trade, the caps, the observation split, the two
    `reason` values.
  - `scoring.md` — the four component formulas with their tables and weights, worked examples, the
    counterfactual definition, the explicit statement that **credits do not sum to the piece score**
    and that a credit can be negative, and what the league ranks by.

**`player[]`** — three runnables, all `image: {{CHORUS_IMAGE}}`, `run: ["/bin/chorus-player"]`,
`resources.requests {cpu: "100m", memory: "64Mi"}`, `resources.limits {cpu: "1"}`, `source_url` the
repo:

| id | name | env |
|---|---|---|
| `chorus-player` | Chorus Prompt Player | *(none — LLM, `PLAYER_PROMPT` at upload time)* |
| `chorus-arpeggio` | Chorus Arpeggio Baseline | `PLAYER_SCRIPTED: "arpeggio"` |
| `chorus-pedal` | Chorus Pedal Baseline | `PLAYER_SCRIPTED: "pedal"` |

**`variants[]`** — every variant carries `players` ×4 **and `num_agents: 4`**, and every variant has
a `description`:

| id | description | `game_config` |
|---|---|---|
| `standard` | Four cogs, eight bars, talk on. | `players` ×4, **`num_agents`: 4**, `bars`: 8, `talk`: true, `turnDelayMs`: 400, `minTurnSpacingMs`: 20000, `player_connect_timeout_seconds`: 180 |
| `long-form` | Ten bars — more room to develop a motif. | `players` ×4, **`num_agents`: 4**, `bars`: 10, `talk`: true, `turnDelayMs`: 400, `minTurnSpacingMs`: 20000, `player_connect_timeout_seconds`: 180 |
| `no-talk` | Eight bars, no messages — coordinate through the grid alone. | `players` ×4, **`num_agents`: 4**, `bars`: 8, `talk`: false, `turnDelayMs`: 400, `minTurnSpacingMs`: 20000, `player_connect_timeout_seconds`: 180 |

**`certification`** —
`game_config`: `players` = `[{"name":"Sprocket"},{"name":"Gizmo"},{"name":"Ratchet"},{"name":"Widget"}]`,
**`num_agents`: 4**, `seed`: 5, `bars`: **6**, `talk`: true, `turnDelayMs`: 0,
`minTurnSpacingMs`: 0, `player_connect_timeout_seconds`: 180.
`certification.players` = `[{"player_id":"chorus-player"}, {"player_id":"chorus-arpeggio"},
{"player_id":"chorus-player"}, {"player_id":"chorus-pedal"}]` — four slots, and **every declared
player runnable occupies at least one** (raid 0.1.2→0.1.3: a fixture of `baseline × N` fails
`players_missing` the moment the manifest declares other runnables).

`bars: 6` is chosen for the fixture so the smoke replay **outlasts the viewer soak window**: 6 bars
= `5·6 + 3 = 33` events, and `attachReplay`'s dwell times (start 600 ms, `turn` 1200 ms, `bar`
600 ms, `end` 1500 ms) give `600 + 7·1200 + 24·600 + 1500 ≈ 24.9 s` of playback against a 10 s soak
(ecos, 2026-08-23).

### CI files

- `.github/workflows/ci.yml` and `.github/workflows/coworld-release.yml` from
  `coworld-builder/templates/`, substituting `<slug>` = **`chorus`**, `<IMAGE>` =
  **`coworld-chorus`**, **`<SEATS>` = `4`**. The `wasm-viewer` job's browser step is invoked with
  **`--soak 10`** added to the pinned command.
- `tools/ci/docker_smoke.sh` from the template with the same substitutions, committed **`chmod +x`**,
  plus one appended assertion: **every player container's exit code must be 0**, not just the
  game's (raid 0.1.3→0.1.4; the template checks only `${prefix}-game`).
- `tools/ci/viewer_smoke.mjs` copied **verbatim**, no substitutions.
- `tools/ci/policies.json`:

  | name | run | env | owner |
  |---|---|---|---|
  | `chorus-cantor` | `/bin/chorus-player` | `PLAYER_PROMPT` = a chord-tone / strong-beat / motif-discipline strategy | champion #1 (daveey, the CI token's own player) |
  | `chorus-weaver` | `/bin/chorus-player` | `PLAYER_PROMPT` = a **different** strategy: watch the interlock, rest when three voices already sound, spend turns rewriting the weakest bar | champion #2, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` |
  | `chorus-arpeggio` | `/bin/chorus-player` | `PLAYER_SCRIPTED=arpeggio` | filler |
  | `chorus-pedal` | `/bin/chorus-player` | `PLAYER_SCRIPTED=pedal` | filler |

  Both champions are `PLAYER_PROMPT` policies; the two fillers are the scripted baselines. The two
  champion prompts must differ materially — identical content dedupes to the same version.

### Design pins (playbook §Phase 0) — how each is satisfied

| Pin | Where |
|---|---|
| Starter by game shape | `cogame-bullwhip` — turn-based, four seats, simultaneous decisions, LLM-prompt policies, native rules, static wasm viewer (title paragraph). |
| Public `Metta-AI/cogame-chorus` | Created public in phase 20; `source_url` points at it. |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `chorus-player` (`PLAYER_PROMPT`) vs `chorus-arpeggio` / `chorus-pedal` (`PLAYER_SCRIPTED=…`), one image (§*Decisions*, §*Packaging*). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh` (§*Viewer*). |
| Real art, starter chrome verbatim | `chrome.css` unchanged, `chrome_common.js` byte-for-byte, `replay_broadcast.html` = the starter's page with a block appended, sprites and floor from `data/` (§*Viewer*, §*Packaging*). |
| Two name spaces | Cog aliases in-game and in every prompt; `policyNames` + `makeNameMap` spectator-side; `results.names` are policy names (§*The game*). |
| Degrade, never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6`; deadline checked before every turn; retry-once-then-scripted; 483 s worst case at `bars = 8` (§*Decisions*). |
| `num_agents` in every variant and the cert fixture | 4 in `standard`, `long-form`, `no-talk` and `certification.game_config`; `<SEATS>` = 4 in `docker_smoke.sh` as the independent cross-check. |
| Upload policies before `upload-coworld`; secret put after | The release workflow template's step order, unchanged. |

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` twice, debug and `-d:release`.

### `tests/test_sim.nim` — sim unit tests

1. **Seeded setup** — for seeds `[0,1,5,42,1234]`: `voiceOf` is a permutation of `0..3` and
   `seatOf[voiceOf[s]] == s`; `root ∈ RootPitches`, `mode ∈ 0..3`, `bpm ∈ {84,90,96,102,108}`;
   `chords.len == bars` and `chords[b] == P[b mod 4]` for one of the four progressions. Across 20
   seeds the bass lands on more than one seat, and both the root and the mode take more than one
   value. The same seed reproduces everything exactly; a different seed differs.
2. **Token → MIDI** — `midiOf` maps `0..13` into `[base, base+23]` for every voice, is strictly
   increasing in the token, and returns `-1` for `-1`.
3. **Hold semantics** — after `initSim`, bar 0 of every voice is 16 rests; after turn `t` opens,
   `grid[v][t] == grid[v][t-1]` for every voice that did not write.
4. **Legality** — `applyBar` raises `ChorusError` and **leaves the sim unchanged** for: `target = -1`,
   `target = t+1`, `steps.len` 15 and 17, a token of `-2`, a token of `14`, a second bar from the
   same seat in one turn, and any call after `done`.
5. **Edit semantics** — with `target < t` the earlier bar is overwritten, `grid[v][t]` still equals
   the hold, and the `bar` event carries `edit: true`; with `target == t`, `edit: false`.
6. **Component values on hand-built grids** — an all-fifths dyad grid gives `consonance == 1.0`; an
   all-minor-second grid gives `0.0`; a purely stepwise single voice gives `leading == 1.0`; a grid
   whose every onset is on `{0,4,8,12}` gives `Ra == 1.0`; two voices in parallel fifths through a
   whole bar cut `leading` by exactly the documented factor; a grid with every voice identical in
   every bar gives `novelty == 0`; a grid where every bar differs in every step gives `novelty == 0`;
   a grid where exactly 8 of 16 steps differ from the closest earlier bar gives `novelty == 1.0`.
7. **Range and totality** — over 200 pseudo-random grids, `piece ∈ [0, 100]` and every component is
   in `[0, 1]`; an all-rest grid scores exactly `0.0`; no grid raises.
8. **Counterfactual** — `credits(sim, n)[s] == pieceScore(grid, n).piece −
   pieceScore(mutedGrid(grid, voiceOf[s]), n).piece` exactly, for 50 random grids; muting an already
   silent voice gives credit `0.0` exactly; a voice built entirely of minor seconds against the
   others gives a **negative** credit; the density denominator stays `n*16*4` in the muted call
   (asserted by constructing a grid where a mute must lower `Rb`).
9. **Rune truncation** — a 400-rune multi-byte `say` (`"音"` ×400) truncates to ≤ 100 **runes**;
   a 900-rune `notes` truncates to ≤ 600 runes; the resulting event JSON round-trips and its bytes
   decode as **strict UTF-8**.
10. **Replay derivation** — `replayMatch(config, events).len == events.len + 1`; the final frame
    equals the live `tableStateJson`; `eventFromJson(eventToJson(e)) == e` for one event of every
    kind; a tampered `turn` event (`piece` moved by 1.0, or `chord` changed) raises `ChorusError`;
    a `deadline` `end` event settles the replayed sim.
11. **Endings** — a full run gives `reason == "complete"` and `turnsPlayed == bars`; `endEarly()`
    mid-episode gives `reason == "deadline"`, scores over `turnsPlayed` bars, `done == true`, and a
    second `endEarly()` is a no-op; `reason` is always one of exactly `{"complete","deadline"}`.
12. **Results shape** — 4 names / scores / voices / onsets; `piece ∈ [0,100]`; the four component
    fields in `[0,1]`; `bars ≤ maxBars`; `onsets[i]` equals the count of non-rest tokens in seat
    `i`'s voice.
13. **Name spaces** — for every seat, `systemPrompt` and `userPrompt` contain the seat's alias and
    contain **none** of the four policy display names; `tableNames` is deterministic in the seed.

### `tests/test_bot.nim` — bounded-orders / legality on the scripted baselines

1. **Legality and boundedness** — for seeds `[1,5,42,1234]` × both baselines in every voice, a full
   scripted episode completes with `reason == "complete"`: `applyBar` never raises, every submitted
   bar is exactly 16 tokens each in `{-1} ∪ [0,13]`, `target == t` on every turn, `say` and `notes`
   are always empty, and the whole episode runs in **< 2000 ms**.
2. **Baseline quality band** — an all-`arpeggio` table over 200 seeds yields a piece score inside
   **[40, 92]**, and the measured mean is echoed to the log so a tuning drift is visible. An
   all-`pedal` table scores **lower than** the all-`arpeggio` table on **≥ 90 %** of those seeds.
   (Below the floor the baseline is noise; above the ceiling a prompt has nothing to beat.)
3. **Fallback path** — with no credentials, `newLlmClient(config).disabled` is true and `decideAll`
   returns scripted decisions for all four seats **with no network call**; the returned decisions
   are all legal.
4. **Reply parsing** — `parseDecision` accepts the array form and the space-/comma-separated string
   form, accepts `.`, `-`, `r`, `R`, `rest` as rests, rounds float tokens, accepts numeric strings,
   defaults a missing `target` to `t`, tolerates trailing prose after `}`, and rejects lengths 15
   and 17, token `14`, token `-2`, and `target = t+1`; `say` and `notes` are capped at their rune
   limits.

### End-to-end, replay and viewer (CI jobs)

5. **`docker-smoke`** (`tools/ci/docker_smoke.sh`, `SMOKE_SEATS = 4`) — builds the production image
   and runs **one real episode** in raw docker with the certification fixture's four-seat mix and no
   `ANTHROPIC_API_KEY`, asserting the game container exits 0 having written `results.json` and a
   replay, that **every player container also exits 0**, that `num_agents` = 4 agrees across
   `certification.game_config`, `len(certification.players)`, `len(game_config.players)` and
   `SMOKE_SEATS`, and that `results.names` / `results.scores` have 4 entries. The replay is copied
   to `dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.
6. **Strict-UTF-8 replay parse** — the same script decodes the replay bytes as UTF-8 and parses them
   as JSON (`SMOKE_REQUIRE_REPLAY_JSON=1`, the default). Sim test 9 covers the multi-byte truncation
   path that would otherwise break it.
7. **Viewer smoke — the bundle is EXECUTED, not merely built.** `ci.yml`'s **`wasm-viewer`** job
   (`needs: docker-smoke`) builds the bundle with `tools/build_replay_viewer.sh`, downloads the
   `smoke-replay` artifact, and runs
   `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
   dist/smoke/replay.json --timeout 90 --soak 10` in headless chromium (Playwright pinned 1.55.0).
   It passes only when the page sets `data-replay-loaded="true"` (or posts the `coworld-replay`
   `ready` envelope), **never** sets `data-replay-error`, keeps advancing through the uninterrupted
   10 s soak, and shows differing `#clock` / `#scorebug` readouts at the 0 % / 50 % / 100 % scrub
   positions. `viewer-smoke.png` and `viewer-smoke.json` are uploaded on success and failure alike.
8. **Chrome scope-duplication check** — a step in the `wasm-viewer` job asserts that no identifier
   exported by `window.ChorusChrome` is re-declared as a top-level `function` or `var` in
   `client/renderer.js`, and that `client/chrome.css` is byte-identical to
   `cogame-bullwhip/client/chrome.css` outside the single appended `chorus additions` block
   (tandem, 2026-08-23: a hoisted game-block `markBeat` silently shadowed the chrome alias and every
   static grep stayed green).

---

## Out of scope (v1)

- Note durations, ties, sustains, velocity, dynamics, articulation and swing — every note is exactly
  one step at one volume.
- Any grid other than 16 steps, any voice count other than 4, and any seat count other than 4.
- Percussion, drum lanes, unpitched voices, chromatic notes outside the mode, and key or tempo
  changes mid-piece.
- Choosing your own voice, trading voices, or writing in another seat's voice.
- A seat editing more than one bar in a turn, or writing a bar and editing one in the same turn.
- Any peer rating, peer vote, veto, or per-seat judgement of another seat — permanently out of
  scope; it is what the idea's integrity note forbids.
- Weight tuning of the metric at runtime, per-variant metric weights, or a hidden metric. The
  weights are constants and are published in `scoring.md` and in the system prompt.
- Exact credit decomposition (Shapley values over all 16 subsets): v1 ships leave-one-out only.
- Sampled or recorded instruments, a mixer, reverb, stereo placement, MIDI export, audio export or
  a downloadable track. v1 audio is four oscillators, toggle-gated, in the viewer only.
- Audio in the live `/client/global` spectator page — audio ships in the replay viewer only.
- Cross-episode memory, motif libraries, or reputation between policies.
- Localisation, and any viewer feature beyond the sequencer stage, the score strip and the endcard
  described above.
