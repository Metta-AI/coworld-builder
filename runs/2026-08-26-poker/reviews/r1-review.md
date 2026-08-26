# r1 review — poker

Repo: `Metta-AI/cogame-poker` @ `7c7e77b977a0256df4d0b78ce79fb35f3d6b1489` (confirmed via
`git checkout` + `git rev-parse`; subject "Audit: signed showdown attribution, priced on the final board").
Starter for provenance: `Metta-AI/cogame-cosino` @ `5b63443` (read-only clone).
Design note: `runs/2026-08-26-poker/design.md`, including Addendum 1 (signed showdown attribution)
and Addendum 2 (showdown equity on the final board; MC fold-case only).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST, items 1–15.

Files read in full: `src/poker.nim`, `src/poker/{types,cards,sim,solve,audit,llm,server}.nim`,
`src/poker_player.nim`, `tests/{test_cards,test_sim,test_solve,test_audit,test_bot,test_manifest}.nim`,
`coworld_manifest_template.json`, `.github/workflows/{ci,coworld-release,coworld-submit}.yml`,
`tools/ci/{docker_smoke.sh,policies.json,viewer_smoke.mjs}`, `tools/build_replay_viewer.sh`,
`client/{chrome.css,renderer.js,replay.html}`, `replay-viewer/{index.html,static_replay.js,config.nims,poker_replay.nim}`,
`Dockerfile`, `Dockerfile.replay-viewer`, `compose.yaml`, `tools/ci/fixtures/sixmax_audit.replay`.
CI evidence: run **32992433560** (`workflow_dispatch`, branch `main`, headSha =
`7c7e77b9…`, conclusion `success`; jobs `test`, `docker-smoke`, `wasm-viewer` all `success`),
plus its downloaded artifacts (`viewer-smoke`, `smoke-replay`, `static-replay-viewer`) and its
full job log.

Legend: **FINDING** = the code diverges from the design note or from a checklist item.
**NOTE** = an observation with no divergence. Categories are the checklist's
`{hang, timeout, static-viewer, manifest, num_agents, correctness, legibility, other}`.
*Observed* = read in the tree or in a CI artifact; *inferred* = reasoned about; *untested* =
would need a run to settle.

---

## Blocking candidates

### B1 — FINDING [legibility] A full-cap 160-rune `say` does not fit the speech bubble; the reviewed run ellipsized it 537 times

- Where: `client/renderer.js:130` (`var BUBBLE_MAX_W = 220, BUBBLE_LINES = 4, BUBBLE_LINE_H = 16;`),
  `client/renderer.js:655-706` (`drawBubble`), specifically `:674-677`
  (`var overflow = lines.length > BUBBLE_LINES; lines = lines.slice(0, BUBBLE_LINES);
  if (overflow && lines.length) { lines[lines.length - 1] += "…"; }`),
  `src/poker/types.nim:11-12` (`## What the viewer's speech bubble can actually show (~4 wrapped
  lines).` / `MaxSayLen* = 160`), fixture at `tests/test_sim.nim:614-618` and
  `tools/ci/fixtures/sixmax_audit.replay`.
- Observed, traced:
  1. `tests/test_sim.nim:614-618` builds `fixtureSay(seat)` as exactly `MaxSayLen` runes of
     4-byte-heavy text, and `:643-645` emits one on **every** one of the six seats. I verified the
     committed fixture: 6 `say` events, one per seat 0–5, each `runeLen == 160`
     (`"🂡é你 seat 0 " × …`).
  2. `drawBubble` wraps on whitespace to `BUBBLE_MAX_W * scale` = 220 px at scale 1, in a 13 px
     font, and hard-clips at `BUBBLE_LINES = 4`, appending `…` to the last kept line.
  3. In the reviewed CI run, the second viewer-smoke invocation
     (`.github/workflows/ci.yml:421-434`, "Load the six-max audit fixture in the same bundle")
     reports `canvas_text: {total: 27581, outside: 0, never_inside: 0, ellipsized: 537}`
     (`viewer-smoke-sixmax.json`, and job log line
     `canvas text: 27581 drawn, 0 never inside the canvas (0 draws crossed an edge), 537 ellipsized (--strict-text-bounds)`).
     Every one of the five recorded `ellipsized` samples is the remark itself:
     `"🂡é你 seat 0 🂡é你 seat 0 🂡é你 seat 0…"` — not a nameplate, not a card label.
  4. For contrast, the cert-fixture invocation reports `ellipsized: 0` — because a scripted Kuhn
     episode emits no `say` at all (`viewer-smoke-cert.json`).
- Checklist item: 15, third bullet — *"Ellipsis is a design choice for **labels** (a card name in a
  52 px card) and a defect for **sentences**. If `ellipsized` counts a remark rather than a
  nameplate, the box is too small — widen the band, do not shorten the text."*
  Also relevant: item 15's second bullet requires the reserved band be *"sized from the cap the
  server enforces on that string (`MaxSayLen` and its kin) and measured in the font it will be
  drawn in"*. `seatExtent` (`client/renderer.js:137-152`) does reserve
  `bubbleHeight(BUBBLE_LINES) * scale` unconditionally — the band is reserved and does not jump —
  but the reservation is 4 lines × 220 px, which the measured 160-rune cap overflows.
- What the note says: `src/poker/types.nim:11` asserts 160 runes is *"what the viewer's speech
  bubble can actually show (~4 wrapped lines)"*; design §Decisions 1 caps `say` at 160 runes and
  §Viewer keeps cosino's `draw` including speech bubbles. The measurement contradicts the comment.
- Not falsified by this: the **gated** number, `never_inside`, is **0** on both invocations, and
  `--strict-text-bounds` is present on both (`ci.yml:411`, `ci.yml:432`), so item 15's first bullet
  passes. Item 15's last bullet (a worst-case renderer fixture for LLM-authored text) is answered
  by the sixmax fixture + its own `ci.yml` step, and the fixture asserts its own strings are still
  full length (`tests/test_sim.nim:874`: `check event["text"].getStr().runeLen == MaxSayLen`).
  This finding is narrowly about the third bullet: the sentence is being cut.
- Consequence (inferred, from the wrap arithmetic): at 13 px 'rajdhani' a 220 px line holds roughly
  30 characters, so ~120 of the 160 runes render and the remainder is replaced by `…`. A model's
  table talk is truncated on screen even though the server let it through.

### B2 — FINDING [timeout] Settlement is bounded at 70 % of the episode timeout, not 60 %

- Where: `src/poker/sim.nim:28-29` (`PlayBudgetFraction* = 0.60`, `HardDeadlineFraction* = 0.70`),
  `src/poker/server.nim:252-253` (`softDeadline = gameStart + timeoutSeconds * PlayBudgetFraction`,
  `hardDeadline = gameStart + timeoutSeconds * HardDeadlineFraction`),
  `src/poker/server.nim:275-283` (hard guard, before every decision),
  `src/poker/server.nim:326-339` (soft + budget guards, **only at a pair boundary after a hand
  finishes**), `src/poker/server.nim:205,217` (`sleep(500)` then `sleep(ShutdownGraceSeconds * 1000)`).
- Observed, traced: `gameStart` is taken at the top of `runGame` (`:224`), i.e. it includes the
  player-connect grace, so both guards are anchored correctly. The **soft** guard is evaluated
  inside `if handEnded:` and only when `atBoundary` (`:327-328`:
  `not config.duplicate or (state.match.handsPlayed mod 2 == 0)`). A hand that is live when the
  clock passes 720 s therefore keeps playing; if it is the base half of a duplicate pair, its
  mirror is played too. The **hard** guard at 840 s is what actually stops a live hand
  (`voidLiveHand()` + `endMatchEarly(erDeadline)`), and only then does `finishEpisode` run
  (`sleep(500)` → write results → write replay → `sleep(20 s)` → `quit(0)`).
  Worst case settle-and-score ≈ 840 s + ~0.5 s ≈ **840 s = 70 %** of 1200 s; process exit ≈ 861 s.
- Checklist item: 5 — *"the episode settles and scores inside **60 %** of `episodeTimeoutSeconds`
  (720 s of 1200)"*.
- What the note says: design §The game 9 prescribes exactly this two-guard shape — *soft* at
  `0.60·T` "checked after every completed **pair**" and *hard* at `0.70·T` "checked before every
  decision". So the implementation matches the note; the note's own numbers are what exceed the
  checklist's literal 60 %.
- I am reporting the arithmetic, not a verdict. Everything else in item 5 holds (see
  "Traced and consistent": every wait has an explicit bound; no unbounded loop; no blocking read
  in the game process).

---

## Non-blocking

### N1 — FINDING [static-viewer, cosmetic] `#endscreen`'s `inset` shorthand cancels the `top: 0` the note specifies

- Where: `client/chrome.css:478` —
  `#endscreen { bottom: var(--band); top: 0; inset: auto 0 var(--band) 0; }`
  (cosino's base rule is `client/chrome.css:372-380`, `inset: 0`, unmodified).
- Observed: `inset` is a shorthand for `top right bottom left` and is the **last** declaration in
  the block, so it wins: the computed values are `top: auto; right: 0; bottom: var(--band); left: 0`.
  The endcard is therefore bottom-anchored with content height rather than the full-height,
  dimmed overlay the note describes.
- Design §Viewer / Transport rules says: *"`#endscreen`, which is additionally re-anchored
  `#endscreen { bottom: var(--band); top: 0; }`"*.
- Checklist item 14(c) is **not** falsified: `#endcard` (here `#endscreen`) keeps
  `bottom: var(--band)`, it is shown with the class its CSS rule uses
  (`#endscreen.show`, `client/chrome.css:381`, toggled by
  `container.classList.toggle("show", !!show)`, `client/renderer.js:1111-1113`), and
  every seek dismisses it (`attachReplay`'s `setIndex` calls `updateEndscreen(... index >=
  events.length && events.length > 0 ...)` on every index change, `client/renderer.js:1514-1519`).
- Untested: whether the bottom-anchored panel reads worse than a centred one — the smoke's
  screenshots were taken mid-playback, not at the end.

### N2 — FINDING [other] The appended chrome block carries two selectors the note's "contains exactly" list does not

- Where: `client/chrome.css:441-446` — `@media (max-width: 640px) { .plate-label, .plate-pips,
  .plate-front { display: none; } }` (the note lists `.plate-label, .plate-pips` only), and
  `client/chrome.css:454-456` — `#feedtoggle, #statuschip { display: none }` inside the
  `@media (max-width: 400px)` block (`chrome.css:448-457`) (the note lists `#wordmark`, `#clock`, `.plate-score`, `#feed`).
- Observed: both additions carry an in-file rationale comment (`.plate-front` "goes with its
  neighbours: unlabelled it reads as a second net"; the 400 px rule hides the toggle for a feed
  that is already `display: none`). `.plate-front` is itself new game-block chrome
  (`client/chrome.css:544-552`), so hiding it at 640 px is internally consistent.
- Design §Chrome provenance says the appended block "contains exactly" a five-item list.
- Falsifies no checklist item. Item 11's two required rules are both present verbatim:
  `client/chrome.css:440` (`.plate-name { flex: 1 1 auto; min-width: 3.2em; }`) and the
  `max-width: 640px` label hide.

### N3 — FINDING [other] The fold-case Monte-Carlo seed is not the note's literal formula

- Where: `src/poker/audit.nim:372-373` —
  `initRand(int64(config.seed) * 1_000_003 + int64(record.hand) * 97 + int64(100 + fold.ordinal))`,
  vs the showdown path at `src/poker/audit.nim:442-443` which uses `… + int64(sliceIndex)`.
- Observed: the design §Collusion audit pins one formula,
  `initRand(seed*1_000_003 + hand*97 + sliceIndex)`. A fold has no slice index, so the code
  substitutes `100 + foldOrdinal` (the `100 +` offset keeps fold streams disjoint from slice
  streams within a hand). `audit.md` in the manifest already documents it as
  *"a seed derived from the replay's own seed, hand index and **fold ordinal**"*
  (`coworld_manifest_template.json:459`).
- Determinism and browser/server re-derivability — the properties the note actually demands — are
  preserved: `fold.ordinal` is assigned from the event stream (`src/poker/audit.nim:242,273-274`),
  so it re-derives from the replay bytes alone. Asserted by `tests/test_audit.nim:173-201`.

### N4 — FINDING [other] `Decision.error` is rune-truncated but never reaches the replay or results

- Where: `src/poker/llm.nim:36` (`error*: string  ## why, rune-truncated for the replay`),
  `src/poker/llm.nim:772` (`result.error = truncateRunes(lastError, MaxErrorLen)`).
- Observed: I grepped the whole tree for reads of `Decision.error`; there are none. `applyDecision`
  (`src/poker/llm.nim:699-729`) ignores it, `server.nim` never reads it
  (`server.nim:301-312` uses only `decision` for `applyDecision` and the counters), and no event
  kind or results field carries it. What reaches phase 60 is
  `results.fallbacks[]` / `results.forcedFolds[]` (`src/poker/sim.nim:1147-1160`).
- Design §Decisions 1 lists "error text recorded on a fallback (200)" among the strings
  `truncateRunes` protects, which reads as though it is recorded.
- Checklist item 9 is **not** falsified — it governs "every string that reaches the replay", and
  this one does not reach it. Item 8's "the fallback is recorded so phase 60 can count it" is
  satisfied by the counter.

### N5 — NOTE [correctness] The frame-by-frame re-derivation is asserted at the terminal frame and through a JSON round-trip, not against a recorded live timeline

- Where: `tests/test_sim.nim:551-554` (fuzz: `replayMatch(config, match.allEvents())`, then
  `check frames.len == match.allEvents().len + 1` and `frames[^1].seats[i].stack == seat.stack`),
  `tests/test_sim.nim:727-729` (`check $statesFromEvents(config, events) ==
  $statesFromEvents(config, back)` for all three end reasons).
- Observed: there is **no parallel recording** to diverge from. The live `/global` snapshot is
  `sim.tableStateJson()` (`src/poker/server.nim:92`) built from the live `Sim`; the replay bytes
  carry `events` only (`src/poker/server.nim:155-169`), and both consumers of a replay derive their
  states from the same `statesFromEvents` — the pod replay server at `src/poker/server.nim:522` and
  the wasm module at `replay-viewer/poker_replay.nim:46`. So item 2's "not from a parallel
  recording" half is structural. The "reproduces the recorded per-tick state frame by frame" half is
  asserted as (a) equality of the derived timeline before/after the JSON round-trip the replay bytes
  perform, and (b) equality of the final frame's stacks with the live sim's, over 200 random matches
  per variant × 5 seat counts.
- Why a literal frame-by-frame equality test would not be well defined here (inferred): the live
  snapshot is broadcast once per **decision** (`src/poker/server.nim:316`), while `replayMatch`
  produces one frame per **event**, and the two disagree on `acting` by construction —
  live is `index == sim.actingSeat` (`sim.nim:1181`), derived is "the actor of the next event, if
  it is an action" (`sim.nim:1329-1333`). The field sets are otherwise identical (`seatStates`
  `sim.nim:1164-1183` vs `frameStateJson` `sim.nim:1336-1369`: same 10 seat keys, same 10 table keys).
- I am recording this so the judge can weigh item 2 with the evidence in front of it, not asserting
  that item 2 is unmet.

### N6 — NOTE [other] No grid-tuning harness for the baselines is present in the tree

- Where: `src/poker/llm.nim:221-247` (`kuhnAction`), `:249-287` (`leducAction`), `:289-402`
  (`holdemAction`); `tests/test_solve.nim:11-13` asserts
  `exploitability(cvKuhn, nashKuhn(alpha)) < 1e-9` for α ∈ {0, 1/6, 1/3}.
- Observed: the Kuhn `house` table is *proved* optimal rather than tuned — `nashKuhn(1/6)`
  (`src/poker/solve.nim:416-440`) measures 0 exploitability, and the frequencies in `kuhnAction`
  match it exactly (bet J 1/6, Q 0, K 1/2 at position 0; call Q 1/2 after checking; at position 1
  bet J 1/3, K always; call Q 1/3). The Hold'em `house` bot is cosino's Chen-formula bot; the Leduc
  tables and `rock` are the design's hand-written rules. I found no grid-search script, no
  sweep log, and no tuning artifact anywhere in the repo.
- Checklist item 7 adds *"The baseline's parameters were tuned with a grid harness, not guessed."*
  I can neither confirm a harness (none in the tree) nor call the Kuhn table guessed (it is
  provably exact). See "Could not determine".

### N7 — NOTE [other] `decide`'s retry-once loop has no test

- Where: `src/poker/llm.nim:755-768` (`for attempt in 0 .. 1: … if client.disabled or "429" in
  error.msg: break`). Tests cover the pieces on either side: `extractJsonObject` raising on garbage
  (`tests/test_bot.nim:91-94`), the no-credentials short-circuit
  (`tests/test_bot.nim:76-89`), and fallback/forced-fold accounting
  (`tests/test_bot.nim:96-134`). Nothing drives two consecutive transport/parse failures through
  `decide` itself — that path needs credentials or an injected transport, and there is no seam for
  one (`completeText` is called directly).
- Checklist item 8 does not require a test of the retry; it requires the behaviour, which is
  present and traced.

### N8 — NOTE [manifest] `matchEnd.data` carries an extra `audit` key beyond the note's payload

- Where: `src/poker/sim.nim:1007-1017` — `data: %*{"reason": …, "handsScored": …, "seed": …,
  "audit": auditNode}`; the note's event table says `data = {reason, handsScored, seed}`.
- Observed: the extra key is load-bearing for `resultsFromEvents`
  (`src/poker/sim.nim:1074-1075`), which reads the audit back out of the recorded log rather than
  recomputing it, keeping `results` a pure function of the events. The wasm viewer independently
  recomputes when a replay's `results` has no `audit`
  (`replay-viewer/poker_replay.nim:30-38`). Byte identity of recomputed vs served audit is asserted
  at `tests/test_audit.nim:180-202`.

### N9 — NOTE [other] `contested` counts "both committed chips in the hand", not "both contributed to a common slice"

- Where: `src/poker/audit.nim:352-356` —
  `if record.committed[a] > 0 and record.committed[b] > 0: inc contested[a][b]`.
- Observed: the note's §Collusion audit says *"`contested[a][b]` counts hands in which `a` and `b`
  both contributed to a common slice."* The two definitions coincide whenever both seats put chips
  in, because the lowest commitment level always forms a slice containing both (inferred from
  `audit.nim:414-423`, which builds slices from `min(committed, level) - previous`). `audit.md`
  already states the implemented wording: *"counts hands in which a and b both put chips in the
  same pot"* (`coworld_manifest_template.json:459`).

### N10 — NOTE [other] The default direct-Anthropic model id is `claude-sonnet-5`

- Where: `src/poker/types.nim:205` (`model: "claude-sonnet-5"`),
  `coworld_manifest_template.json:139-143` (same default in `config_schema`).
- Observed: the note pins the **Bedrock** candidate list (haiku-4-5 first, sonnet-4-5 second,
  sonnet-4-6 removed) and says nothing about the direct-Anthropic model name; the code's Bedrock
  list matches the note exactly (`src/poker/llm.nim:74-85`). `claude-sonnet-5` is only used on the
  `ANTHROPIC_API_KEY` transport (`src/poker/llm.nim:633`). Hosted play uses the Bedrock sidecar, so
  this string is not on the hosted path. Recorded because I could not verify the id resolves.

---

## Traced and consistent

**Resolution rules — Kuhn** (design §The game 2)
- Deck: `src/poker/cards.nim:208-210` `@[39, 43, 47]` = J♠ Q♠ K♠. Asserted
  `tests/test_cards.nim:56-65`.
- Ante 1 both seats, pot 2, antes then zeroed as dead money:
  `src/poker/sim.nim:595-607`. Asserted `tests/test_sim.nim:290-298` (`pot == 2`,
  `currentBet == 0`, `callAmount == 0`).
- One private card each, position 0 then position 1: `src/poker/sim.nim:589-594`.
- One betting round (`rounds(vKuhn) = 1`, `lastStreet = stPreflop`, `types.nim:150-160`), bet size
  fixed at 1 (`types.nim:139`), at most one wager (`types.nim:145`, enforced by
  `wagerCapReached` `sim.nim:236-238`, `canBet` `:245-247`, `canRaise` `:240-243`, and the
  `akBet`/`akRaise` guards at `:683-684, 708-709`). Asserted `tests/test_sim.nim:278-288`.
- Position 0 acts first: `sim.nim:608` (`result.progress(result.order[n - 1])` → `nextNeeding`
  lands on position 0). Asserted `tests/test_sim.nim:291-293` with a non-identity `seatOrder`.
- All five payoff sequences: `tests/test_sim.nim:244-265` checks `pp → ±1`, `pbp → ∓1`,
  `pbb → ±2`, `bp → ±1`, `bb → ±2` — exactly the note's rule 6.
- No split (distinct cards): `showdownRank` for Kuhn is `1000 + rank` (`sim.nim:367-368`);
  higher card always wins asserted over all six orderings, `tests/test_sim.nim:267-276`.
- 60 hands: manifest variant `kuhn` `hands: 60` (`coworld_manifest_template.json:530`) and
  `handCap(kuhn) = 84 ≥ 60` (`sim.nim:102-110`, asserted `tests/test_sim.nim:815-837`).

**Resolution rules — Leduc** (design §The game 3)
- Deck: `cards.nim:212-214` `@[39,43,47,38,42,46]` = JQK spades + JQK hearts. Asserted
  `tests/test_cards.nim:67-81`.
- Ante 1, pot 2, one card each from position 0: same code path as Kuhn (`sim.nim:586-608`).
- Round 1 bet 2 / round 2 bet 4 (`types.nim:140`, selected by
  `wagerSize` `sim.nim:213-214` via `min(sim.round, 1)`), cap 2 wagers per round
  (`types.nim:146`, `wagers` reset in `dealNextStreet` `sim.nim:325`). Asserted
  `tests/test_sim.nim:303-323`.
- Board card only if both seats live: `progress` resolves before dealing when
  `liveCount() <= 1` (`sim.nim:520-521`). Asserted `tests/test_sim.nim:325-330`.
- Position 0 acts first in **both** rounds: `sim.nim:531-535`
  (`origin = sim.order[sim.seats.len - 1]` for fixed-limit). Asserted `tests/test_sim.nim:319`.
- Showdown: `leducRank` (`cards.nim:216-224`) — pair = `2000 + rank`, else `1000 + rank`.
  Pair beats unpaired K asserted `tests/test_sim.nim:332-343`; ordering and split asserted
  `tests/test_cards.nim:83-99`.
- Split with the odd chip to **position 0**: `oddChipFirst` returns `sim.order[0]` for fixed-limit
  (`sim.nim:249-253`), consumed by `payout` (`sim.nim:404-427`). Asserted
  `tests/test_sim.nim:345-357` (with `seatOrder = @[1,0]`, so it is genuinely position-based).
- A fold forfeits the whole commitment: asserted `tests/test_sim.nim:359-367`.
- 36 hands, cap 40: `coworld_manifest_template.json:555`, `tests/test_sim.nim:815-816`.

**Resolution rules — Hold'em** (design §The game 4)
- Blinds 1/2 never escalating: `types.nim:191-196`; heads-up button posts the small blind
  (`sim.nim:612-614`) and acts first preflop (`sim.nim:641` → `nextNeeding(bbSeat)` lands on
  position 0), last postflop (`sim.nim:533-535` `origin = sim.button`). Asserted
  `tests/test_sim.nim:83-88`. Multiway blinds clockwise from the button asserted
  `tests/test_sim.nim:72-81`.
- Deal order is cosino's verbatim — two cards to each seat clockwise from the small blind
  (`sim.nim:619-626`); I diffed this against `cogame-cosino/src/cosino/sim.nim:460-468`: same loop,
  same `dealIndex += 2`.
- Min-raise, short-all-in-does-not-reopen-unless-increments-accumulate, side pots by commitment
  level, split with the odd chip clockwise from the button, uncalled-bet refund:
  `sim.nim:705-744` (`akRaise`, `shortRaiseAccum`), `:337-361` (`refundUncalled`),
  `:458-497` (levels → slices → eligible → winners → `sweep`). Asserted
  `tests/test_sim.nim:140-239`.
- No-limit has no wager cap: `maxWagers(vHoldem) = high(int)` (`types.nim:148`).
- 30 hands HU / 16 hands 6-max, caps 36 and 16: `tests/test_sim.nim:815-816, 832-837`.

**Per-hand stack reset and `stackOff`**
- `initHand` gives every seat `config.startingStack` unconditionally (`sim.nim:560-567`); no
  `isOut`/`bust` field exists in `Seat` (`types.nim:105-117`). `evStackOff` is emitted only for
  Hold'em and only as a marker (`sim.nim:503-507`), and `finishHand` counts it without any game
  effect (`sim.nim:941-942`). Asserted `tests/test_sim.nim:371-402`.

**Duplicate mirror**
- `positionsFor` (`sim.nim:136-149`) implements `seatOrderMirror[p] = seatOrder[(p + n div 2) mod n]`
  exactly, for `hand mod 2 == 1` when `duplicate`.
- `pairDeck` (`sim.nim:151-162`) is `initRand(seed*104729 + pair*7919 + 13)`, matching the note.
- Asserted for (kuhn 2, leduc 2, holdem 2, holdem 6) at `tests/test_sim.nim:407-431`: same deck,
  identical cards at each position, the rotation identity, and the button staying at position 0.
  Heads-up card swap asserted `:433-440`; a new pair draws a new deck `:442-448`; invisibility to
  the seats (no cross-hand transcript, no "mirror"/"duplicate" in the prompt) `:450-474`.

**Seat randomisation**
- `seatOrderFor` (`sim.nim:125-134`) `initRand(seed*7907 + 101)` shuffle; permutation +
  determinism asserted for 2..6 seats × 4 seeds (`tests/test_sim.nim:477-486`); results arrays
  indexed by slot asserted `:488-500`.

**Scoring**
- `scores[i] = 1/n + net[i]/(n·S·H)` at `src/poker/sim.nim:1103-1108`, with `H = handsScored`
  read from the `matchEnd` event (`:1072`). `win[i] = (net[i] == max(net))` at `:1109`.
  `netPerHand`/`unitsPerHand` with `unit = bigBlind | ante` at `:1085, 1111-1112`.
- Zero-sum: enforced by the pot always being fully distributed (`payout` + the `sweep` at
  `sim.nim:496-497`) and by `voidHand` refunding every committed chip (`sim.nim:750-768`).
  Asserted `tests/test_sim.nim:504-554` (200 random matches × {kuhn, leduc, holdem 2–6},
  `Σ net == 0`, on-table chips constant), `tests/test_bot.nim:65-73`.
- Range and degeneracy asserted `tests/test_sim.nim:556-598`: `Σ scores == 1` to 1e-9, all in
  [0,1], break-even = exactly `1/n`, all-chips = exactly 1.0 / 0.0.
- H excludes voided hands: `finishHand` increments `handsScored` only if `not sim.voided`
  (`sim.nim:935-936`); asserted `tests/test_sim.nim:711-754`
  (`handsPlayed == handsScored + 1`, `Σ net == 0`, exactly one `handVoid` with a positive refund).

**Decision path**
- Transports in the note's order (Bedrock endpoint/token → `ANTHROPIC_API_KEY` →
  `ANTHROPIC_API_KEY_URI`): `src/poker/llm.nim:101-133`, `:61-72`.
- Bedrock candidates `us.anthropic.claude-haiku-4-5-20251001-v1:0` then
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`; `sonnet-4-6` absent: `src/poker/llm.nim:74-85`.
- `max_tokens = 900` (`types.nim:207`), `llmTimeoutSeconds = 20` (`types.nim:209`) passed to
  `curl.post(url, headers, body, client.timeoutSeconds)` (`llm.nim:638`); no
  `output_config.effort` anywhere (`llm.nim:619-637`, comment at `:637`).
- System prompt matches the note's exact text including the trailing
  "Your reply MUST begin with the character `{`" (`llm.nim:460-476`); per-variant rules blocks
  `:425-458`; user prompt order standings → seats → this hand's history → secret cards → board →
  pot/stack → operator guidance → legal-action instruction (`llm.nim:588-605`), with the note's
  exact guidance header at `:603-604`.
- Precomputed legal set with exact amounts, from the same predicates `applyAction` validates with
  (`llm.nim:555-586` using `callAmount`/`canBet`/`canRaise`/`minBet`/`minRaiseTo`/`maxRaiseTo`).
- Tolerant parse, first `{` to last `}`: `llm.nim:609-616` (`text.find('{')` … `text.rfind('}')`).
- Retry exactly once: `llm.nim:755` `for attempt in 0 .. 1`, with the note's exact retry suffix at
  `:758-759`.
- 429: no retry, immediate scripted move, spacing floor +500 ms for the rest of the episode —
  `llm.nim:647-652` (`client.spacingMs += ThrottleBumpMs`) and `:767` (`"429" in error.msg: break`).
- `call`→`check` normalisation and `allin`→`call`/`check` when covered or barred:
  `llm.nim:674-690`.
- Scripted fallback recorded: `llm.nim:770-772` sets `fallback = true`; `applyDecision`
  (`llm.nim:699-729`) increments `fallbacks` on a fallback decision or a rejected action and
  `forcedFolds` when even the baseline is rejected, then plays a fold, which is always legal.
  Server accumulates at `server.nim:307-312`, surfaced in
  `results.fallbacks/forcedFolds/decisions` (`sim.nim:1147-1160`). Asserted
  `tests/test_bot.nim:96-134`.
- No credentials → `disabled`, zero network wait: `llm.nim:130-133`, `:750-751`. Asserted
  `tests/test_bot.nim:76-89` (`elapsed < 500 ms`).
- Spacing floor 2100 ms from decision start to decision start: `sim.nim:34`
  (`DecisionSpacingMs* = 2100`), `llm.nim:731-737` (`waitForSpacing`, called once per decision at
  `:752`, before the retry loop).
- Sequential, one seat at a time: `server.nim:264-302` picks a single `actingSeat` per iteration.
  This is correct for poker; the checklist's parallel-batch rule applies to
  *simultaneous-decision* games and does not apply here (design §Decisions 3).

**Every wait and its bound** (item 5, apart from B2)
- Player connect: `server.nim:225-233`, bounded by `playerConnectTimeoutSeconds` (180 s), polling
  `sleep(200)`; the game starts regardless.
- LLM call: bounded by `curl.post(..., client.timeoutSeconds)` (`llm.nim:638`), 20 s.
- Spacing floor: `sleep(spacingMs - elapsed)` ≤ 2100 ms (+500 ms per observed 429) (`llm.nim:736`).
- Turn pacing: `sleep(config.turnDelayMs)` (`server.nim:318-319, 346-347`), 0 in the cert fixture.
- Hard guard before **every** decision: `server.nim:275`.
- Soft + budget guards at each pair boundary: `server.nim:326-339`;
  `EpisodeDecisionBudget = 220` (`sim.nim:24`), `spent` incremented once per decision
  (`server.nim:303`).
- Artifact write then bounded shutdown grace then `quit(0)`: `server.nim:205-219`.
- Main loop terminates: `while true` exits on `state.match.done` (`:273-274`), the hard guard
  (`:275-283`), or a missing acting seat (`:287-290`); `finishHand` sets `done` when
  `handsPlayed >= config.hands` (`sim.nim:943-945`).
- No blocking read anywhere in the game process: the websocket handler is event-driven
  (`server.nim:443-491`); the only `receiveMessage` loop is in the **player** container
  (`src/poker_player.nim:57-84`), wrapped in `try/except CatchableError` and exiting 0 on a dead
  socket, which is the raid 0.1.4 fix the note names. `docker_smoke.sh:253-270` enforces every
  player container exiting 0 within 60 s, and the reviewed run logged
  `all 2 player containers exited 0`.

**String truncation** (item 9)
- One helper: `truncateRunes` (`types.nim:119-131`) — `toRunes`, slice, append `\u2026`; never a
  byte cut.
- `say` 160: `parseDecision` (`llm.nim:665`) **and** `recordSay` (`sim.nim:645-648`).
- Operator prompt 4000: `server.nim:471`.
- Alias 16: `tableNames` (`sim.nim:98-100`).
- Error 200: `llm.nim:772` (see N4 for where it goes).
- Tests: `tests/test_cards.nim:101-115` (never splits a rune, cap-0, mixed-width text),
  `tests/test_sim.nim:841-860` (a 900-emoji `say` through the real replay JSON,
  `validateUtf8() == -1`), `tests/test_bot.nim:137-161` (5 kB emoji → exactly 160 runes, strict
  round trip).

**Replay writer and self-sufficiency**
- `replayPayload` (`server.nim:155-169`) writes
  `{protocol: "poker.replay.v1", names, policyNames, config, events, results}` — exactly the note's
  shape. Verified on the reviewed run's artifact (`smoke-replay/replay.json`): those six keys,
  `protocol == "poker.replay.v1"`, 147 events, and `config` =
  `{variant, seats, startingStack, ante, smallBlind, bigBlind, bets, maxWagers, hands, duplicate,
  seatOrder, seed: 7, sampled, gameVersion: 1}` — the **seed is in the bytes**, so the audit's MC
  re-derives in the browser.
- `names` are the aliases and `policyNames` the policy names (`server.nim:157-161, 78-84`);
  the players' `state` frames have `policyNames` deleted (`server.nim:137`).
- `replayConfigJson` at `sim.nim:1398-1421`; `configFromReplay` at `:1377-1396` sets
  `sampled = true` so a replay is never re-fitted.

**Viewer re-derivation**
- `replayMatch` produces one frame per event prefix and never re-runs the betting engine — every
  branch reads recorded `stackAfter`/`betAfter`/`potAfter`/`cards` (`sim.nim:1220-1334`).
- `matchEnd` is load-bearing: `resultsFromEvents` reads `reason`, `handsScored`, `seed` and the
  audit out of it (`sim.nim:1069-1075`), so a `deadline` replay re-derives like a `complete` one.
  Asserted for all three reasons, including full `results` key-by-key equality, at
  `tests/test_sim.nim:698-754`, and "matchEnd is last + `finishMatch` is idempotent" at `:756-770`.
- Audit reuse with recompute-if-absent in the wasm module: `replay-viewer/poker_replay.nim:30-38`.
  Byte identity of the recomputed audit against the server's asserted at
  `tests/test_audit.nim:180-202`.
- Every event kind round-trips through JSON, all 15 kinds covered (the fixture supplies `audit`):
  `tests/test_sim.nim:772-809`.

**Exploitability (`solve.nim`)**
- Exact BR by backward induction over counterfactual reach, deepest infosets first:
  `solve.nim:294-341` (`collect` at `:244-287`, ordering at `:313-319`).
- Duplicate framing: `exploitability = 0.5 * (bestResponseValue(variant, 1, σ) +
  bestResponseValue(variant, 0, σ))` (`solve.nim:357-362`). Tracing the signs:
  `bestResponseValue(1, σ)` is `u1(σ, BR1) = −u0(σ, BR1)` and `bestResponseValue(0, σ)` is
  `u0(BR0, σ) = −u1(BR0, σ)`, so the returned value is exactly `−v_i` as the note defines it,
  and it is ≥ 0 (asserted `tests/test_solve.nim:118-126`).
- Kuhn Nash fill at α = 1/6: `KuhnAlpha` (`solve.nim:53`), `fillStrategy` (`:555-560`),
  `fillName` "nash"/"uniform" (`:550-553`). The α-family table (`:416-440`) reproduces the note's
  frequencies exactly, and `gameValue == −1/18` for α ∈ {0, 1/6, 1/3} to 1e-12
  (`tests/test_solve.nim:6-13`).
- Leduc uniform fill (`solve.nim:536-539`); BR against always-fold = exactly 1 chip from either
  position (`tests/test_solve.nim:36-42`); house-Leduc exploitability finite, positive, stable
  (`:44-53`).
- Coverage = visited / reachable (`solve.nim:562-585`), asserted at ~0.5 for a half-visited tree
  (`tests/test_solve.nim:83-99`); 12 Kuhn infosets, 6 per position (`:20-27`).
- Emission: one `calib` event per seat at the tail for fixed-limit only
  (`sim.nim:985-997`, `calibFromEvents` returns `@[]` for Hold'em at `:842-843`), and
  `results.exploitability[]` is `null` per seat where no `calib` landed (`sim.nim:1039-1043,
  1079-1082`). Confirmed in the reviewed run's `results.json`: `exploitability` present for the
  Kuhn cert episode, `exploitabilityFill: "nash"`, `exploitabilityCoverage: [0.5, 0.417]` — a thin
  12-hand sample producing a nonzero *empirical* exploitability while the *table* measures 0, which
  is the note's stated intent (§7.1–7.2).

**Audit, per the addenda**
- Showdown slices priced on the **final board**, exact: `audit.nim:434-448` passes
  `record.board` (the completed board) to `equities`, which does a single exact evaluation when
  `5 - board.len <= 0` (`audit.nim:186-187`).
- Showdown attribution **signed**, no outer clamp: `audit.nim:470`
  (`let loss = equity[a] * slice.float - actual[a].float`) then `:477-479`.
- MC 2000 runouts is the **fold case only**, keeping its internal clamp: `audit.nim:360-387`,
  `let loss = max(0.0, shares[0] * fold.pot.float - fold.callCost.float)` at `:375`;
  `EquitySamples* = 2000` at `:29`.
- Thresholds 0.75 bb (mutual soft-play, `min(bias[a][b], bias[b][a])`) and 2.0 bb (directed dump),
  both at `contested ≥ 4`: `audit.nim:31-35, 527-549`.
- Pure function of events + seed: `auditEvents` takes only `(config, events)` and seeds every RNG
  from `config.seed` (`audit.nim:326-373, 442-443`). `auditFromEvents` is the single entry point
  used by the server (`sim.nim:900-904, 999`) and the wasm module
  (`replay-viewer/poker_replay.nim:34-38`).
- `netFlow` reported per pair and on every flag: `audit.nim:515, 525, 534, 541, 548`.
- Runs only where collusion is possible (`vHoldem` and `n ≥ 3`), empty otherwise:
  `audit.nim:331-332`; asserted `tests/test_audit.nim:120-133`.
- `power = {hands, contestedMin, contestedMedian, equitySamples}`: `audit.nim:556-564`.
- The addenda's measured claims are the tests: zero flags of any kind over 10 honest episodes ×
  **both** baselines at the shipped 16-hand size (`tests/test_audit.nim:82-104`); a completed hand
  books no showdown surrender (`:106-118`); synthetic dump → exactly one `dump-2-to-5`, no
  soft-play, no reverse dump (`:136-149`); synthetic mutual soft-play → exactly one `soft-play`
  plus the two correct directed dumps (`:151-170`); MC determinism and exactness on a complete
  board (`:213-242`); `eval7` agrees with the brute-force `evalBest` over 4000 random sevens
  (`:244-252`).
- The named limitation is documented in `audit.md`
  (`coworld_manifest_template.json:459`, "What this audit does NOT catch") and in the module
  header (`src/poker/audit.nim:18-21`), as the addendum requires.

**Viewer provenance and wiring** (items 3, 13, 14)
- Four files, one starter. I diffed each against cosino @ 5b63443:
  - `client/chrome.css` — the first **10 497 bytes (422 lines) are byte-identical** to cosino's
    (verified with `cmp` on the prefix); everything after is the fenced block
    `/* ==== poker game block (appended; nothing above this line is edited) ==== */`
    (`client/chrome.css:423-576`). Not one existing selector is rewritten.
  - `replay-viewer/index.html` — cosino's page; the only changes are `<title>`, the wordmark
    (`PO<span>KER</span>`), `cosino_replay.js`→`poker_replay.js`,
    `CosinoRenderer`→`PokerRenderer`, plus an appended `#rungchip`, `#auditcard` and a
    `relayout()` script block. Nothing removed.
  - `client/replay.html` — same, plus `rungchip`/`auditcard` passed into `attachReplay`.
  - `replay-viewer/config.nims` — identical to cosino's except the three renames
    (`poker_replay.js`, `EXPORT_NAME=PokerReplayModule`, `_pkr_*` exports).
  - `replay-viewer/poker_replay.nim` — cosino's `cosino_replay.nim` with `cos_*`→`pkr_*`, the same
    `emscripten_exit_with_live_runtime` epilogue (`:73-80`).
- MODULARIZE agreement (item 13's lantern check): `replay-viewer/config.nims:38-39` emits
  `-s MODULARIZE=1 -s EXPORT_NAME=PokerReplayModule`, and `static_replay.js:140` calls the
  **factory** `PokerReplayModule().catch(...)`. There is no `Module.onRuntimeInitialized`
  anywhere. `ci.yml:124-131` greps both sides plus all five `pkr_*` symbols.
- Load signalling: `data-replay-loaded="true"` is set on the **first drawn frame** inside
  `attachReplay`'s rAF loop, immediately before `options.onFirstFrame()`
  (`client/renderer.js:1549-1559`); `data-replay-error` is set in `static_replay.js:57` and cleared
  at `:108, 133`. The bridge posts `ready` **only** from `onFirstFrame`
  (`static_replay.js:122`). Confirmed in both smoke artifacts:
  `signals: {data_replay_loaded: "true", data_replay_error: null, bridge: ["loading","ready"]}`.
- Bounded fetch + Retry: `FETCH_TIMEOUT_MS = 20000` with `AbortController`
  (`static_replay.js:14, 68-90`), `RETRYING REPLAY… (attempt N)` caption (`:134`), Retry button
  reusing the compiled module (`:50-55, 136-144`).
- Contacts nothing but the `?replay=` URL and relative bundle assets (`static_replay.js:127`,
  `assetBase: "./assets"` at `:120`). No absolute origins anywhere in the bundle.
- Manifest declares `game.replay_viewer.bundle = "static-replay-viewer"` and nothing else
  (`coworld_manifest_template.json:15-17`); `ci.yml:186-189` greps for it **and** fails if
  `/client/replay` appears in the manifest. The server's `GET /client/replay` route
  (`server.nim:497`) is the parley-lineage convention — it exists identically in
  `cogame-babel/src/babel/server.nim:502`, `cogame-parley/.../server.nim:520` and
  `cogame-bullwhip/.../server.nim:470` — and is not a declared viewer path; item 3's prohibition is
  on the declared pod path, which the CI grep enforces.
- Build hook: `tools/build_replay_viewer.sh` exists, is committed `100755`
  (`git ls-files -s` → `100755`), `mkdir -p "$(dirname "${output_dir}")"` **before** the
  containment work (`:21`, the ecos fix), falls back to the pinned
  `emscripten/emsdk:4.0.15` + nimby 0.1.27 + Nim 2.2.4 image (`Dockerfile.replay-viewer:4-13`),
  and copies exactly the note's file list plus `data/*` (`:47-59`). It self-checks
  `PokerReplayModule(` and `data-replay` in the emitted shell (`:62-63`).
- `wasm-viewer` `needs: docker-smoke` (`ci.yml:301`) and its
  `Load the bundle in a real browser` step ran, not skipped, not `continue-on-error`
  (job log lines 6970–7045). `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `templates/tools/ci/viewer_smoke.mjs` (`diff -q` clean) and committed `100755`.
- No `#viewpanel`, no `zoomAt`/`setZoom`/`attachMinimap` anywhere in the tree (grepped `*.js`,
  `*.html`, `*.css`) — correct for a fixed arena, per the note and item 14's last bullet.
- Transport rules: `#transport` is a flex child of `#stage`, and `#board-wrap` is `flex: 1`
  above it (`chrome.css:95, 128-136`), so the canvas cannot overlap the band by construction.
  `relayout()` measures `#transport.offsetHeight` and publishes `--band` and
  `--hudscale = clamp(0.72, stageWidth/960, 1)` on `document.documentElement`
  (`replay-viewer/index.html:52-77`, function at `:60`; `client/replay.html:77-100`, function at `:83`) — on `load`, on `resize`, and
  immediately; `bindFeedToggle` dispatches a `resize` on every toggle
  (`client/renderer.js:1223-1241`, `window.dispatchEvent(new Event("resize"))` at `:1238`), so the feed-toggle case is covered. Both overlays the
  game adds ride the band: `#auditcard { bottom: calc(var(--band) + 10px) }`
  (`chrome.css:481-495`, the `bottom` at `:484`) and `#endscreen { bottom: var(--band) … }` (`chrome.css:478`, see N1).
- Scrubber beats are clickable, labelled `<button>`s that seek:
  `buildPokerBeats` (`client/renderer.js:1379-1400`) creates
  `<button type="button" class="beat-marker <kind> seat<N>" aria-label title>` with
  `onclick → onSeek(i + 1)`, called from `buildScrub` (`:1432`). All six kinds
  (`award, showdown, stackoff, mirror, void, audit`, `renderer.js:1345-1346`) have CSS rules
  (`chrome.css:509-540`, on top of cosino's inherited `.beat-marker` base at `chrome.css:195-203` which
  supplies the seat colour). `ci.yml:157-177` asserts kind↔CSS pairing **both ways** (declared but
  never emitted is also a failure). Hand spans/separators are cosino's, kept
  (`renderer.js:1407-1430`).
- Game-block shadowing: `CHROME_ALIASES` (`renderer.js:1567-1571`) lists `markBeat` among the
  reserved names, the builder is `buildPokerBeats`, and `ci.yml:135-154` parses the fenced blocks
  and fails on any `function <alias>` inside them.
- `"10" not "T"`: `cardLabel` (`renderer.js:48-53`) maps `"T"` → `"10"`, used for both hole cards
  and board cards (`:623`, `:778`).
- Item 11: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (`chrome.css:440`) and
  `@media (max-width: 640px) { .plate-label, .plate-pips, .plate-front { display: none } }`
  (`chrome.css:441-446`). 360 px rules at `chrome.css:448-457`.
- Item 4 (both name spaces): agents get aliases only — `tableNames` (`sim.nim:88-100`) is what
  reaches `Seat.name`, `redactCards` deletes `policyNames` from every player frame
  (`server.nim:137`) and strips `calib`/`audit` (`:121-122`); the viewer maps aliases → policy
  names for non-baseline seats via `makeNameMap`/`isBaselineFiller`
  (`renderer.js:726-753`, regex `/^baseline(\s*\(\d+\))?$/i`).

**Manifest** (items 6, 10, 12-partial)
- Four variants with `num_agents` 2/2/2/6 and `game_config.players` of matching length:
  `coworld_manifest_template.json:512-623` (kuhn `:524`, leduc `:549`, holdem-hu `:574`,
  holdem-6max `:611` with six player entries `:591-610`).
- Certification fixture: `variant "kuhn"`, `num_agents: 2`, `players` = Sprocket/Gizmo, `seed: 7`,
  `startingStack: 20`, `ante: 1`, blinds 0/0, `hands: 12`, `duplicate: true`, `turnDelayMs: 0`,
  `player_connect_timeout_seconds: 180`, no `tokens` (`:625-655`); `certification.players` =
  `poker-player`, `poker-baseline` (`:647-654`).
- `docs.readme` is `{type,value}` and `docs.pages` is the three named pages
  (`rules.md`, `ladder.md`, `audit.md`) each with `{id,title,content:{type,value}}`
  (`:432-463`). `protocols` carries **both** `player` and `global` as `{type,value}` objects
  (`:422-431`). Item 10 satisfied.
- Every `config_schema` array property declares `minItems`/`maxItems`: `tokens` (`:40-42`) and
  `players` (`:50-52`), both 2..6 — the only two arrays. Every `results_schema` array likewise,
  including `audit.pairs` (0..32) and `audit.flagged` (0..64). `results_schema.reason` is
  `enum: ["complete","deadline","budget"]` (`:411-419`).
- `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/poker/anthropic_api_key"`
  (`:24-26`) with the namespace equal to `game.name` (`:12`); image `{{POKER_IMAGE}}` (`:20`),
  derived from the compose service name `poker` (`compose.yaml`). `episode_timeout_minutes: 20`
  (`:10`), 5 top-level tags (`:3-9`), `game.description` present, no `game.tags`, no top-level
  `version`, no `game.display_name`, `game.owner` set.
- `player[]` has exactly the two declared runnables, both `limits.cpu: "1"`,
  `requests 100m/64Mi` (`:465-508`), and both occupy a certification slot.
- All of the above is asserted mechanically in `tests/test_manifest.nim` (263 lines), including
  "every declared game_config actually constructs a live match" (`:198-222`).
- `docker_smoke.sh` enforces the four seat-count invariants with `SEAT-COUNT FAIL:` prefixes —
  `num_agents` present (`:110-118`), positive integer (`:119-125`),
  `len(certification.players) == num_agents` (`:129-134`),
  `len(game_config.players) == num_agents` (`:135-140`) — plus `SMOKE_SEATS` as an independent
  second declaration (`:54` `seats_expected="${SMOKE_SEATS:-2}"`, cross-checked at `:141-151`).
  I grepped the **entire** reviewed CI log for `SEAT-COUNT FAIL`: **0 occurrences**; the job logged
  `game=poker seats=2 …` and `smoke OK: seats=2 results=680B replay=16351B reason=complete`.
  `docker_smoke.sh` differs from `templates/tools/ci/docker_smoke.sh` **only** by the three
  substitutions (`poker`, `coworld-poker`, `2`) — verified by diff.

**Workflows** (item 12)
- `coworld-release.yml` order: `Build the Coworld manifest` (`:159`) → `Certify locally` (`:173`)
  → `Upload the policies` (`:212`) → `Upload the Coworld` (`:310`) → `Put the Coworld secret`
  (`:348`). Inputs `version`, `policies`, `secret_key_name`, `put_secret`, `skip_certify`
  (`:27-52`); `release-result` artifact assembled at `:374` and uploaded; the per-policy `player`
  field is honoured with `softmax player use` / `unset` around each upload (`:239-301`).
  The certify gate hard-fails unless the log reports the **static** bundle (`:200-210`).
- `coworld-submit.yml` inputs `player_id`, `policy`, `league_id` (`:23-37`); `submit-result`
  artifact at `:136-141`.
- Both files are **template-identical apart from the slug/image substitutions** (diff run against
  `templates/coworld-release.yml` and `templates/coworld-submit.yml`: 10 and 2 changed lines, all
  substitutions). `ci.yml` diverges from the template only by **additions** (the Static-gates step
  and the second viewer-smoke invocation) — the diff contains no template line that was removed.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files returns nothing
  → exits 0. The four expected angle-bracket survivors are exactly the documented ones:
  `<cow_id>`/`<sha>` in `ci.yml:291`, `<run_id>` in `coworld-release.yml:21` and
  `coworld-submit.yml:17`, and `<name>:vN` in `coworld-submit.yml:31`.
- `tools/ci/policies.json`: four distinct policies —
  `poker-scholar` (PLAYER_PROMPT), `poker-exploiter` (PLAYER_PROMPT, with
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` on the **second** prompt champion),
  `poker-house` and `poker-rock` (PLAYER_SCRIPTED fillers). Byte-for-byte the design's block.
  Asserted `tests/test_manifest.nim:224-262`, including "no `USE_BEDROCK`" and distinct env bodies.

**Tests vs the note's §Tests list**
All six suites exist and map onto the note's list: `test_cards` (evaluator + both calibration decks
+ `leducRank` + rune truncation), `test_sim` (cosino's betting/pot suites kept, plus the eleven new
groups — I checked each of the note's numbered items 1–11 against a suite), `test_solve` (the note's
five items), `test_audit` (the note's five items **as amended by the addenda**: strict zero-FP over
both baselines, kind-counted synthetic flags), `test_bot` (the note's four items, with the caveat in
N7), `test_manifest` (every assertion the note lists). The sixmax fixture is regenerated and diffed
by `tests/test_sim.nim:862-885`, which rewrites and **fails** on drift. `ci.yml:193-239` runs every
`tests/*.nim` twice, debug and `-d:release`.

**Item 1, second half — "no test loosened"**
`git log --name-status -- tests/` at this sha shows the tests added by `59afdf2` and one later
change, `7c7e77b` (`tests/test_audit.nim`). I read that hunk in full: it **strengthens** — the
zero-false-positive test goes from `blRock` only to `for baseline in [blHouse, blRock]` and from
"no soft-play flag" to `check audit["flagged"].len == 0` (all kinds), a new invariant test is
added, and the soft-play test gains two extra assertions
(`dump-1-to-4`, `dump-4-to-1` each exactly 1). No assertion deleted, no tolerance widened, no skip
added, no test file removed. The `D`/`A` churn earlier in the log for all six test files is the
API-push replay the brief flags (duplicated subjects `d9b2889`/`59afdf2`,
`5080251`/`6d71fb7`); HEAD's tree carries all six files.

---

## Could not determine

- **Whether the baselines' parameters came from a grid harness** (checklist 7, last sentence).
  No harness script, sweep output or tuning log exists in the tree. What *is* verifiable: the Kuhn
  `house` table is exact Nash and measures 0 exploitability
  (`tests/test_solve.nim:11-13` + `src/poker/llm.nim:239-247` reproducing `nashKuhn(1/6)`'s
  frequencies), and the Hold'em bot is cosino's, inherited. The Leduc `house`/`rock` tables and the
  Hold'em `rock` thresholds are hand-written per the design note. Would be settled by: a committed
  harness, or a `log.md`/design-note record of the sweep that produced the Leduc frequencies and the
  `rock` Chen cutoffs.
- **Whether the bubble in B1 is legible in practice at the shipped canvas sizes.** `viewer_smoke`
  reports the *count* of ellipsized draws but not the on-screen result, and the uploaded
  `viewer-smoke-sixmax.png` is a single mid-playback frame. Would be settled by: a render of the
  sixmax fixture paused on a `say` event at 360 px and at desktop width, or by
  `BUBBLE_MAX_W`/`BUBBLE_LINES` arithmetic against the actual `measureText` widths the smoke already
  collects (it records the text, not the box, for `ellipsized` samples).
- **Whether `claude-sonnet-5` (N10) is a resolvable model id.** Not reachable from the sandbox and
  not on the hosted (Bedrock) path.
- **The visual effect of N1** (`top: auto` on `#endscreen`). Would be settled by a screenshot taken
  with the scrubber at 100 %.
