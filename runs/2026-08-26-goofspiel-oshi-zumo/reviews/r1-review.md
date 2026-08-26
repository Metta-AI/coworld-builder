# r1 review — cogame-goofspiel-oshi-zumo

Repo: `Metta-AI/cogame-goofspiel-oshi-zumo` at `1a29c60e88af98dbd3cca00c26366d22c12d4cd1`
(clone read at `/tmp/cogame-goofspiel-oshi-zumo`; `main` head at review time = same sha).
Design note: `runs/2026-08-26-goofspiel-oshi-zumo/design.md` (byte-identical to
`docs/plans/2026-08-26-goofspiel-oshi-zumo-design.md` in the repo — verified with `diff`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Starter for provenance: `/workspace/starters/cogame-babel` @ `d55d999`.
Files read: 41 (all of `src/`, `client/`, `replay-viewer/`, `tests/`, `tools/`,
`.github/workflows/`, the manifest, `compose.yaml`, `Dockerfile`), plus CI run
`33016530966` (jobs `test` 98336084398, `docker-smoke` 98336084293, `wasm-viewer` 98336470903)
and its `smoke-replay`, `viewer-smoke` and `renderer-fixture` artifacts.

Observation labels: **[observed]** = read in the code / in a CI log; **[computed]** = derived
by arithmetic from code I read; **[inferred]** = reasoned, not directly witnessed.

---

## Findings

### F1 — a full-cap `say` is drawn ellipsized at narrow widths; the reserved band cannot hold 80 runes below ~640 px
- Where: `client/renderer.js:32-33`, `:283-317` (`wrapLines`, `sayFontPx`, `sayBandHeight`),
  `:442-467` (the band); CI evidence: `wasm-viewer` step *Renderer text fixture*,
  `canvas text: 3190 drawn, 0 never inside …, 374 ellipsized`.
- Observed: the band is genuinely *reserved* — `bandH = sayBandHeight(layout)` is subtracted
  from the panel body (`:364-365`) whether or not a seat is speaking, and the empty band is
  stroked dashed (`:459-466`). `never_inside == 0` in both CI smoke runs, so nothing is drawn
  at a negative coordinate. The font is floored: `sayFontPx` returns
  `max(7, min(11 * layout.scale, (contentW - 12) / (40 * 0.47)))` (`:308-313`), and the text is
  laid out by `wrapLines(..., contentW - 8, SAY_LINES=2)`, which appends `…` to the last line
  when the text needs more than two lines (`:297-301`).
- Computed: at a 360 px frame with four seats, `computeLayout` gives `panelW ≈ (344 − 16)/4 ≈ 82 px`
  (`:100-117`), so `contentW ≈ 76 px` and `sayFontPx` hits its 7 px floor (the width-derived value
  is ≈ 3.2 px). Two lines of ≈ 68 px usable width = ≈ 136 px of run length, while an 80-rune
  mixed CJK/latin remark at 7 px needs ≥ 280 px. The remark is therefore cut and `…` appended —
  a *sentence*, not a label. At 640 px/4 seats the width-derived font is ≈ 6.97 px, i.e. exactly
  at the floor, so it is marginal there; at 1280 px it fits (visible in the fixture screenshot,
  where the full 80-rune line wraps into two lines with no ellipsis).
- Note's requirement: design.md:743-745 — the band is "sized from `MaxSayLen = 80` … so a
  full-cap line can never be laid out at a negative coordinate". That property holds.
- Checklist bearing: item 15, third bullet — "Ellipsis is a design choice for **labels** … and a
  defect for **sentences**. If `ellipsized` counts a remark rather than a nameplate, the box is
  too small". The gated number (`never_inside`) is 0 and `--strict-text-bounds` is on, so nothing
  here is red in CI.
- Evidence limit: the fixture's `viewer-smoke.json` caps `samples` at 12 (first-come, see
  `tools/ci/viewer_smoke.mjs:336-338`) and all 12 are nameplates
  (`"goofspiel-oshi-zumo-rea…"` — the chrome's own 24-char `clampName` cut, `chrome_common.js:143-146`),
  so the artifact neither confirms nor refutes that remark draws are among the other 362. The
  geometry above is what I am asserting, not the artifact.

### F2 — the goofspiel score pool is "awarded so far", not the note's literal `pool = 91`
- Where: `src/gozu/sim.nim:204-210` (`awardedPool`), `:232-243` (`score`).
- Observed: `awardedPool` sums `prizeOrder[0 ..< min(roundsPlayed, prizeOrder.len)]`;
  `score` = `(N * points_i/pool − 1)/(N − 1)`, returning `0.0` when `pool <= 0`.
- Computed: on a `complete` episode `roundsPlayed == 13`, so `pool == 91` and the formula is
  exactly the note's `(points_i − 22.75)/68.25` — confirmed by the CI smoke `results.json`
  (`points [22.75×4]`, `scores [0.0×4]`) and by `tests/test_sim.nim:48-79`. On a `deadline` stop
  the pool is what was awarded, and since every round distributes its whole prize,
  `Σ points_i = pool`, so `Σ score_i = (N·1 − N)/(N−1) = 0`. Pinned by
  `tests/test_sim.nim:274-300` (six clean wins + `endEarly`: `score[0] == 1.0`,
  `score[1..3] == −1/3`, sum 0).
- Note's requirement: design.md:154 states `pool = 91` flatly; design.md:190-193 says a deadline
  episode is "fully scored at the stop (goofspiel from prizes already awarded)". The code
  implements the second sentence; with a fixed 91 the deadline array would not sum to 0. The
  deviation is documented in the shipped rules page
  (`coworld_manifest_template.json` `game.docs.pages[0]`: "`pool` = the prize value awarded so far
  (91 for a complete episode)") and in the code comment at `sim.nim:205-207`, but the design
  note's §Scoring section still reads `pool = 91`.
- Checklist bearing: none directly; the results contract (item 10 / results_schema) is satisfied.

### F3 — in goofspiel, any `bid` **string** whose first character is a/j/q/k is read as a card letter
- Where: `src/gozu/llm.nim:452-464` (`parseBidText`), called from `parseDecision` (`:496`).
- Observed: for `mode == mGoofspiel` the proc switches on `trimmed[0].toUpperAscii()` and returns
  1/11/12/13 for `A`/`J`/`Q`/`K` before any numeric scan. It does not require the token to be a
  lone letter, so `{"bid": "a bid of 11"}` yields `1`, and `{"bid": "just 12"}` yields `11`
  (`J`). Because the result is usually a legal card, the validator at `llm.nim:549` and the
  server's re-check at `server.nim:330` both accept it: no retry fires and `fallbacks` is not
  incremented; the seat silently bids a card it did not ask for.
- Note's requirement: design.md:591-593 — "a numeric string with surrounding whitespace or
  trailing prose (`"11 — the king"`); and, in goofspiel only, the letters `A/J/Q/K` (any case)
  mapped to `1/11/12/13`". The note describes a letter *token*, not a prefix rule.
- Checklist bearing: item 8 concerns tolerance/retry/fallback, all of which are present
  (`llm.nim:524-561`); this is a value-correctness observation, not a parse failure.

### F4 — no test asserts `results.reason == "complete"` for an **all-scripted** episode
- Where: `tests/test_bot.nim:37-63` (`playAll`, which asserts `check result.done` at `:62` and
  per-bid legality at `:48`), `:64-78` (assertion 12), `:136-157` (assertion 15).
- Observed: the only `reason == "complete"` assertions are on hand-driven episodes
  (`tests/test_sim.nim:78`, `:198`) and on the recorded fixtures in
  `tests/test_replay.nim:106`, `:233`. The baseline-driven episodes assert `done`,
  `roundsPlayed == 13`, empty hands and `coins >= 0`, but never read `reason`/`resultsJson`.
- CI evidence (not an assertion): `docker-smoke` ran a four-seat, no-key, fully scripted episode
  and printed `episode end reason: complete` / `smoke OK: seats=4 … reason=complete`
  (run 33016530966, job 98336084293), and `results.json` validated against `results_schema`.
- Note's requirement: design.md §Tests assertion 12/15 do not name `reason`; the *checklist*
  item 7 does: "A test runs an all-scripted episode to the natural end, **asserts
  `results.reason == "complete"`**, and asserts every order/action is inside its legal bounds".
  The second half is asserted (`test_bot.nim:48`); the first half is only shown in the CI log.

### F5 — assertion 7's "200 seeds × both baselines" is driven by synthetic bidders, not by `match`/`hoard`
- Where: `tests/test_sim.nim:225-243`.
- Observed: the loop iterates `for hoard in [false, true]` but the bids are
  `legal[0]` (always the minimum) and `legal[min(legal.high, seat + rounds mod 3)]` — neither
  calls `scriptedBid`/`scriptedAction`. It does assert `sim.done` and `rounds <= 20` over
  200 seeds.
- Note's requirement: design.md:904-906 (assertion 7) — "with `minBid = 1` and `coins = 20`,
  **every** seeded episode ends within 20 rounds (200 seeds × both baselines)".
- Mitigation observed: `tests/test_bot.nim:64-78` (assertion 12) runs the real `skMatch` and
  `skHoard` over 200 seeds in both modes and asserts `oshi.roundsPlayed <= 20` and termination,
  so the property the note wants is covered — by a different test than the note names.

### F6 — no grid-tuning harness for the baselines is present in the tree
- Where: `src/gozu/llm.nim:158-199` (`matchBid`, `hoardBid`, `scriptedBid`); repo contains only
  `scripts/art/{generate_gozu_art.py,split_gozu_sheet.py}` — no tuning script anywhere
  (`grep -rl grid` matches only the design note and two chrome files, on unrelated `grid-template`).
- Observed: both baselines are parameter-free rules (match the prize / first card above it;
  low-on-cheap, high-on-dear at the `(cards+1) div 2` split; `ceil(coins/pushesNeeded)`;
  `ceil(coins/2)` when one loss from defeat). There is nothing to tune, and the note prescribes
  these exact algorithms (design.md:263-280). The quality evidence that exists is
  `tests/test_bot.nim:80-100` (`match` beats a uniform-random legal bidder, mean score > 0 over
  200 episodes) and `:102-134` (`match` and `hoard` differ on ≥ 30 % of rounds).
- Checklist bearing: item 7's last sentence ("The baseline's parameters were tuned with a grid
  harness, not guessed"). Stating what I found, not how it should be categorised.

### F7 — the game thread has no exception guard; a raised `writeArtifact` would leave the server running with no `quit`
- Where: `src/gozu/server.nim:140-153` (`writeArtifact`, raises `IOError` on a non-2xx artifact
  POST), `:169-218` (`finishEpisode`, ending in `quit(0)` at `:218`), `:237-364` (`runGame`,
  no `try`/`except` anywhere), `:580` (`createThread(gameThread, runGame, …)`).
- Observed: if `runGame`/`finishEpisode` raises, the game thread dies and the mummy server keeps
  serving (`:581-582`), so the container never exits on its own; the platform's own episode
  timeout is the only bound. The bid path itself cannot raise: every bid is checked against
  `state.sim.legalBids(seat)` and replaced by `scriptedAction(..., skMatch)` before `applyBids`
  (`:330-344`), `bids.len == config.players.len` by construction, and `roundOpen` holds because
  `beginRound` ran in the same iteration — I could not construct a reachable raise from
  `applyBids`. The reachable raise is the artifact POST at `:150-151`.
- Provenance: `writeArtifact` is byte-equivalent to babel's
  (`/workspace/starters/cogame-babel/src/babel/server.nim:127-141`), and babel likewise runs
  `runGame` unguarded. Babel *does* wrap its apply step in `try/except BabelError`
  (babel `server.nim:334-348`); this repo achieves the same protection by pre-validating instead.
- Checklist bearing: item 5 ("no unbounded loop or blocking read"). The play loop itself is
  bounded (see *Traced and consistent*); this is the failure mode outside it.

### F8 — `checkReveal` silently skips the points comparison when the arrays differ in length
- Where: `src/gozu/sim.nim:703-713`.
- Observed: `if event.points.len == logged.points.len:` guards the per-element `nearly()`
  comparison; a recorded `reveal` carrying a shorter/longer `points` array passes that check
  (the bids/winners/margin/coinsAfter/handsAfter comparison at `:704-708` is unconditional, and
  `handsAfter` would normally catch a truncated payload).
- Note's requirement: design.md:498-499 — "`replayMatch` asserts it against the re-derivation,
  which is how a drift becomes a test failure instead of a silent divergence."

### F9 — the certification fixture's policy names are drawn from the alias pool, so the viewer maps aliases onto other aliases
- Where: `coworld_manifest_template.json` `certification.game_config.players` =
  `Sprocket/Gizmo/Ratchet/Widget`; alias pool `CogNames` at `src/gozu/sim.nim:17-20`;
  mapping in `client/chrome_common.js:105-133` (`makeNameMap`, which also builds a whole-word
  regex that rewrites those names inside feed text).
- Observed in CI: the smoke replay's `names` (aliases) are
  `["Piston","Gizmo","Sprocket","Ratchet"]` while `policyNames` are
  `["Sprocket","Gizmo","Ratchet","Widget"]`, and `viewer-smoke.json` records the scorebug as
  `"Sprocket PISTON 5.8 pts 4 Gizmo 5.8 pts 4 Ratchet SPROCKET 5.8 pts 4 Widget RATCHET 5.8 pts 4"`.
  The two name spaces are working exactly as designed (policy name in `.plate-name`, alias in
  `.plate-alias`); the collision only makes the cert/smoke replay confusing to read.
- Note's requirement: design.md:857-864 prescribes those four fixture names, so the code and the
  manifest follow the note. Reported as an observation about the resulting display, nothing more.

### F10 — the say band's font scale comes from the canvas layout, not from `--hudscale`
- Where: `client/renderer.js:308-313` uses `layout.scale`
  (`max(0.55, min(1, min(w/960, h/620)))`, `:115`); `--hudscale` is set on `:root` by
  `client/chrome_common.js:493-500` and consumed only by CSS (`client/chrome.css:487`,
  `.plate { font-size: calc(1em * var(--hudscale, 1)) }`).
- Note's requirement: design.md:743-745 — the band is "sized from `MaxSayLen = 80` measured in
  the render font **at the current `--hudscale`**". The substance (sized from the cap) holds;
  the scale factor is the canvas one.

### F11 — the player's receive loop is an untimed blocking read (starter behaviour, guarded)
- Where: `src/gozu_player.nim:50-76`; `whisky.receiveMessage(ws, timeout = -1)`
  (`/root/.nimby/pkgs/whisky/src/whisky.nim:73`).
- Observed: the loop blocks indefinitely on each frame; it exits on `final` (`:68-70`), on
  `none` (`:53-55`), and on any `CatchableError` from a dead socket (`:75-76`), always with
  exit status 0. Bound in practice: the game sends `final` before writing artifacts
  (`server.nim:179-199`) and then `quit(0)` after the 20 s grace (`:216-218`), which closes the
  socket. Identical in shape to the starter (`cogame-babel/src/babel_player.nim:50-73`), plus the
  try/except the note asks for (design.md:340-342).
- CI evidence: `all 4 player containers exited 0` (job 98336084293), enforced by
  `tools/ci/docker_smoke.sh:253-270`.
- Checklist bearing: item 5's "no … blocking read" wording.

---

## Traced and consistent

**Resolution rules — goofspiel** (`src/gozu/sim.nim`)
- `:286-309` `beginRound` sets `round = roundsPlayed`, clears per-round state and emits `evPrize`
  with `prize = prizeOrder[round]` and the sorted remaining deck (`prizesLeft`, `:197-202`) —
  note step 1.
- `:325-328` legality: `bids[seat] notin legalBids(seat)` raises `GozuError` naming seat and bid —
  note step 3 / §Procs.
- `:345-351` `top` and `winners`; `:352-361` `margin = top − (highest bid strictly below)`, and
  `0` whenever the top is tied — note step 8 and the §gasp predicate.
- `:373-378` award: single winner takes `prize`, ties take `prize / |winners|` as `float`
  (fractional points) — note step 6.
- `:379-386` every seat's bid card is removed from its hand, won or not — note step 7;
  the audit reads `hands[seat][0]` *before* the delete (`:382-384`).
- `:411-419` `evOverbid` is emitted immediately after `evReveal` when `winners.len == 1 and
  margin >= 6`, carrying `seat`, `bid = top`, `margin`, and `over = top − margin` (the bid it
  beat) — note step 8 and the event table.
- `:429-431` settle `complete`/`prizes-exhausted` at `roundsPlayed >= maxRounds` — note step 9.
- Tests: `tests/test_sim.nim:47-79` (single winner, pool 91, ending), `:81-110` (2/3/4-way splits,
  four-way tie ⇒ `margin == 0`, no overbid), `:112-139` (illegal bid raises, card spent once,
  `legalBids` shrinks by one, all hands empty at 13), `:141-155` (deck is a seeded permutation and
  is reproducible from `config.prizeOrder`), `:302-319` (margin 5 silent / margin 6 exactly one
  overbid with the right seat, bid and `over`), `:329-363` (collusion index 0 and `4/13`).

**Resolution rules — oshi-zumo** (`src/gozu/sim.nim`)
- `:155-159` `initSim` seats 20 coins each and puts the token at `position = size` (cell 3);
  `:69` `fieldCells = 2K+1 = 7`.
- `:164-177` `minBidOf = min(M, coins)` and `legalBids = minBid_i .. coins_i` — note's bid rule,
  including "a seat holding 0 coins must bid 0" (`tests/test_sim.nim:184-189`).
- `:389-396` **both** seats pay unconditionally, then `delta = +1 / −1 / 0` with **equal bids not
  moving the token** — note step 5-6 (`tests/test_sim.nim:157-173` checks all three cases and both
  purses).
- `:421-426` `evPush` carries `delta` and `positionAfter`, emitted after `evReveal`
  (and after `evOverbid` when it fires) — the shipped rules page states this same order.
- `:432-440` end checks in the note's order: `position > 6` → pushout, `position < 0` → pushout,
  both purses 0 → coins-exhausted, `roundsPlayed >= maxRounds` → round-cap
  (`tests/test_sim.nim:191-223` covers all four plus the cell-3 draw).
- `:260-273` `settle` scores by position for every non-pushout ending — `> size` seat 0,
  `< size` seat 1, `== size` a 0.5/0.5 draw — and by direction for a pushout. Applied on the
  `deadline` path too, since `endEarly` (`:442-447`) routes through the same proc.
- Termination: with `minBid = 1` each seat spends ≥ 1 while it holds coins, so purses reach 0 and
  `coins-exhausted` fires; `maxRounds = 20` is a second bound (`:439`).
  `tests/test_bot.nim:64-78` asserts `roundsPlayed <= 20` for both real baselines over 200 seeds.

**Scores and results**
- `sim.nim:241-243` oshi score = `2 * outcome − 1` ⇒ `+1 / 0 / −1`, and `0.0` while not done.
- `sim.nim:451-485` `resultsJson` emits exactly the note's fields, with `points` = prize points
  (goofspiel) or the 1/0.5/0 outcome (oshi-zumo), `finalPosition = −1` in goofspiel, plus
  `spent`, `bidsMade`, `fallbacks`, `collusionIndex`, `rounds`, `maxRounds`, `mode`, `ending`,
  `reason`, and `names` = **policy** names (`:463`).
- `reason` only ever takes `"complete"` (`:431`, `:434`, `:436`, `:438`, `:440`) or `"deadline"`
  (`:447`); `ending` only the five values in the note's table. `results_schema` pins both enums
  and `tests/test_manifest.nim:55-66` asserts them verbatim.
- Zero-sum: `tests/test_sim.nim:245-272` over 200 seeded episodes in both modes (`abs(total) < 1e-9`).

**Decision path** (`src/gozu/llm.nim`, `src/gozu/server.nim`)
- `llm.nim:515-523` scripted seats (and every seat once `client.disabled`) are decided inline;
  the rest go into `open`.
- `:524-539` one `curly.RequestBatch` per attempt, `batch.post(...)` per open seat, issued with
  `client.curl.makeRequests(batch, client.timeoutSeconds)` — one parallel batch per round, the
  bullwhip `decideAll` shape (`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:443-475`
  is the same loop). `makeRequests` blocks until every request completes and returns results in
  batch order (`/root/.nimby/pkgs/curly/src/curly.nim:711-760`), with the timeout applied per
  request (`:290`, `:416`), so the batch is bounded by `llmTimeoutSeconds`.
- `:381-391` tolerant extraction: first `{` … last `}`, fences and trailing prose tolerated,
  quoting the head of a non-JSON reply into a 200-char capped error.
- `:524` `for attempt in 0 .. 1` — exactly **one** retry, in a batch containing only the seats
  still open (`:540-557`), with the note's hint plus `bidList(sim.legalBids(seat))` appended
  (`:533-536`) — the same proc the validator uses (`:549`).
- `:558-561` fallback to `scriptedAction(sim, seat, skMatch)`, `fellBack = true`, and a
  `"gozu llm: seat N falling back to scripted decision"` line on stdout.
- `server.nim:328-344` re-checks each returned bid against `legalBids` and substitutes `match`
  with `fellBack = true` if it fails; `sim.nim:341-343` increments `fallbacks[seat]` for every
  `fellBack`, and `resultsJson` reports it.
- `:427-434` a 401/403 sets `client.disabled = true` once; every later `decideAll` short-circuits
  to the baseline with no network wait (`:519`). With no credentials at all,
  `newLlmClient` disables the client up front (`:138-141`) — the CI smoke ran that path
  (`no ANTHROPIC_API_KEY: the game must complete on its scripted baselines`).

**Waits and bounds**
- `server.nim:241-249` player-connect wait: `while epochTime() < gameStart +
  playerConnectTimeoutSeconds` polling at 200 ms; play starts regardless of who connected.
- `:264-273` `playDeadline = gameStart + timeoutSeconds * 0.6`, with `timeoutSeconds` from
  `COWORLD_TIMEOUT_SECONDS` or the configured 1200 default ⇒ 720 s.
- `:225-228` `roundReserveSeconds = 2 * llmTimeoutSeconds + 2 = 62 s`; `:293-299` a round is not
  **opened** unless `roundStart + reserve <= playDeadline`, otherwise `endEarly()` +
  `broadcastLocked()` + `break` — the note's `now + 62 s <= playDeadline` guard, applied between
  rounds only. [computed] worst case: the last round can open at `playDeadline − 62` and take at
  most 62 s, so the settle lands at ≈ 720 s; `finishEpisode` then writes artifacts and sleeps the
  20 s grace (`:216`) before `quit(0)`, all inside the 1200 s episode timeout.
- `:230-236` batch spacing floor `4 × seats` when `batchSpacingSeconds == 0`, applied only when at
  least one seat actually used the LLM (`:312-318`, `:356-359`) and measured from `roundStart`, so
  a slow round pays nothing extra.
- `:352-353` `turnDelayMs` pacing (fitted to `120_000 div maxRounds` by
  `sampleEpisode`, `sim.nim:87-99`; 0 in the cert fixture).
- The play loop is `while true` with `break` on `sim.done` or the deadline; each iteration calls
  `applyBids`, which increments `roundsPlayed` and settles at `maxRounds`.

**Truncation**
- `src/gozu/types.nim:13-16` caps: `MaxSayLen 80`, `MaxNotesLen 400`, `MaxPromptLen 4000`,
  `MaxErrorLen 200` — exactly the note's numbers.
- `:87-94` `cleanText` strips, returns unchanged at `runeLen <= limit`, else
  `runeSubStr(0, limit - 1) & "…"` — a rune cut, output length exactly `limit` runes.
- Applied at: `llm.nim:488-489` (`notes` 400, `say` 80 + newline→space), `sim.nim:335-337`
  (again on the way into the event, so replayed strings are idempotent),
  `server.nim:481` (delivered prompt, 4000), and every captured error string
  (`llm.nim:80`, `:390`, `:426`, `:428`, `:437`, `:441`, `:450`, `:475`, `:499`, `:555`;
  `server.nim:496`). No un-capped free text reaches an event: `says`/`notes` are the only string
  fields in the event vocabulary (`types.nim:56-85`).
- `tests/test_replay.nim:168-212` feeds 80-rune and 400-rune multi-byte strings at exactly the cap
  through a whole episode, asserts the recorded strings are still exactly at the cap, and asserts
  `validateUtf8(payload) == -1` plus a strict `parseJson` round-trip; the second case cuts 500
  emoji down and asserts the result ends in `…`, is at the cap in runes, and is valid UTF-8.

**Replay writer and re-derivation**
- `sim.nim:659-697`: `replayConfigJson` carries `mode`, `seats`, `seed`, `cards`, `prizeOrder`,
  `coins`, `size`, `minBid`, `maxRounds`, `sampled:true`; `replayPayloadJson` wraps it with
  `protocol: "gozu.replay.v1"`, `names` (aliases), `policyNames`, `events`, `results` — the
  note's §Replay bytes, confirmed on the real CI artifact (`smoke-replay/replay.json`:
  protocol `gozu.replay.v1`, 28 events = 1 start + 13 prize + 13 reveal + 1 end,
  `prizeOrder` of 13, full `results`).
- `:542-653` all six event kinds serialise and parse symmetrically.
- `:715-771` `replayMatch`: replays `evReveal` bids through `applyBids`, opens the round lazily for
  oshi-zumo, **checks** the recorded `evPrize` against the seeded deck (`:731-736`), the
  `evReveal` against the re-derivation including `handsAfter`, `coinsAfter`, `winners`, `margin`
  (`:703-713`), and `evOverbid`/`evPush` field by field (`:746-759`); a recorded `evEnd` that the
  rules did not produce is applied through the **same** `settle` (`:760-770`), which is what makes
  a wall-clock stop re-derive.
- `tests/test_replay.nim:62-135` records one episode per reason/ending pair and asserts every
  snapshot's `tableStateJson` string is identical to the live one, including the deadline case;
  `:139-164` asserts a tampered `prize` and a tampered `push` both raise; `:216-254` asserts the
  payload keys and then re-derives the whole episode from the bytes alone with a **deliberately
  wrong seed**, relying on `config.prizeOrder`.
- The viewer uses that same re-derivation: `replay-viewer/gozu_replay.nim:44-59` builds
  `states[]` from `replayMatch` and hands it to the renderer; the server's replay mode does the
  same via `statesFromEvents` (`server.nim:163-167`).

**Viewer**
- Provenance, all four files diffed against `cogame-babel@d55d999`:
  `replay-viewer/config.nims` differs only in the output name and the three `gzu_`/`GozuReplayModule`
  renames; `index.html` in title, wordmark, the added `chrome_common.js` script and the module
  name; `static_replay.js` in the renames plus the one documented `onFirstFrame` deviation;
  `gozu_replay.nim` in the `bab_*`→`gzu_*` renames and the mode/deck-aware config read.
- MODULARIZE pairing: `config.nims:38-39` (`-s MODULARIZE=1 -s EXPORT_NAME=GozuReplayModule`)
  against `static_replay.js:144` (`GozuReplayModule().catch(...)`) — same starter, factory called.
  Every other emscripten switch (`--mm:arc`, `--exceptions:goto`, `-d:useMalloc`,
  `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`, `EXPORTED_RUNTIME_METHODS=HEAPU8`)
  is unchanged with its comment.
- Load signalling: `client/renderer.js:990-996` sets `data-replay-loaded="true"` on the **first
  drawn frame** and only then calls `options.onFirstFrame`; `static_replay.js:126-129` sets the
  attribute and posts `ready` from that callback — the attribute precedes `ready`.
  `static_replay.js:56` sets `data-replay-error`, `:107` and `:140` remove it on success/retry.
  CI: `viewer-smoke.json` `signals: {data_replay_loaded:"true", bridge:["loading","ready"],
  bridge_ready:true}`.
- Chrome provenance: `client/chrome.css` — the first 11142 bytes are **byte-identical** to babel's
  443-line file (`cmp`), with the game block appended from line 445.
  `client/chrome_common.js` — every one of the ten declared regions (lines 20-37, 85-87, 101-127,
  327-334, 680-734, 735-745, 790-864, 865-901, 934-1049, 1145-1222 of babel's `client/renderer.js`)
  is byte-identical line for line, the only difference across the whole copy being a dropped
  trailing blank line per region and **exactly one edited line** —
  `chrome_common.js:201` `escapeHtml(feedText(event, nameMap, ctx))` where babel had
  `describeEvent(...)` — which is the edit the note names. Everything else is appended after the
  banner at `:477` (`setFeedText`, `relayout`, `markRoundBeat`).
  `client/replay_broadcast.html` is babel's `client/replay.html` with only the title, the wordmark,
  the `chrome_common.js` script line under the banner comment, and `BabelRenderer`→`GozuRenderer`;
  every id the note lists is present and nothing is removed (76 lines vs the starter's 74).
  `client/global.html` and `client/player.html` differ from the starter in the same four ways.
- Transport rules: `chrome_common.js:493-502` `relayout()` measures `#transport` and sets
  `--band` and `--hudscale` on `document.documentElement` (`:root`), on `load`, on `resize`, and
  via the resize `bindFeedToggle` dispatches (`:379-392`); `renderer.js:974` calls it once on
  attach. `chrome.css:457-458` `:root { --band: 0px; --hudscale: 1 }` and
  `#endscreen { inset: 0 0 var(--band, 0px) 0 }` over the starter's
  `#endscreen { position:absolute; inset:0; display:none }` / `#endscreen.show { display:flex }`
  (`chrome.css:372-381`) — the endcard is shown with the class its own CSS rule uses, and stops at
  the band. There is **no** `position: fixed` rule anywhere in `chrome.css`, and `#transport` is a
  laid-out flex child of `#stage` (`:128-136`), so nothing is overlaid in the band.
  `renderer.js:951-972` `setIndex` removes `.show` whenever `index < events.length`, and every
  seek path routes through it: scrub drag/click (`:930-933`), beat click (`:934-937`),
  play-from-end restart (`:938-943`). Beats: `renderer.js:776-787` calls
  `C.markRoundBeat(container, index, total, event.kind, label, seatClass, onSeek)` for **every**
  recorded event; `chrome_common.js:509-531` builds a `<button type="button"
  class="beat-marker beat-<kind> [seatN]" aria-label title>` that seeks to `index + 1`; CSS exists
  for all six kinds (`chrome.css:475-481`), and the copied `buildScrub`'s own unlabelled `end`
  div is hidden by `.scrub .beat-marker.death { display:none }` (`:474`).
- `#viewpanel`: absent from the whole tree (`grep viewpanel` matches only the explanatory comment
  at `renderer.js:98`); babel has none either, so nothing was hidden rather than removed. No
  `zoomAt`/`setZoom`/`attachMinimap` anywhere.
- 360 px legibility: `chrome.css:487` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`;
  `:531-543` `@media (max-width: 640px) { … .plate-label, .plate-alias { display: none } … }`;
  `:544-551` a 360 px block; `renderer.js:89-92`, `:576` drop the mode word from the clock under
  420 px; ranks are always numeric (`drawCardFace` prints `String(rank)`, `:143`).
- Scorebug: `renderer.js:589-620` paints one plate per seat with the **policy** name in
  `.plate-name`, the alias in `.plate-alias`, the running total, the budget bar and the revealed
  bid; `#scorebug.seats2` handles the two-seat variant (`chrome.css:483-484`).
- Say band: reserved unconditionally, drawn last, inside the panel (see F1 for the sizing).
- CI execution evidence (run 33016530966, job `wasm-viewer` 98336470903, `needs: docker-smoke`):
  step *Load the bundle in a real browser* ran
  `viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json
  --timeout 90 --soak 10 --strict-text-bounds` against the docker-smoke replay and reported
  `{"loaded":true,"ms":282,…}`, `soak: 10s of playback kept advancing`,
  `canvas text: 13361 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`,
  three working scrub positions and `bridge_ready: true`. No `continue-on-error` anywhere in
  `ci.yml`. [computed] the replay's 28 events at the renderer's dwell table
  (`renderer.js:38-40`: 13×700 + 13×1200 + 600 + 1500) ≈ 26.8 s of playback > the 10 s soak.
- Renderer fixture (`tools/ci/renderer_fixture.html`, its own step at `ci.yml:342-362`): loads the
  **shipped** `dist/static-replay-viewer/index.html` in an iframe, shims only the wasm entry
  (`:194-230`), drives both modes at 360/640/1280 px with a full-cap 80-rune `say` on every seat
  and 32-35-char policy names, asserts its own strings are still 80 runes before running
  (`:235-239`), and sets `data-replay-loaded` only at the end (`:252`); run with
  `--strict-text-bounds`; result `loaded:true`, `never_inside: 0`. See F1 for `ellipsized: 374`.

**Manifest** (`coworld_manifest_template.json`)
- `num_agents`: 4 in `goofspiel-4`, 2 in `oshi-zumo-2` (both at the variant level *and* inside
  `game_config`), 4 in `certification.game_config`, and `certification.players` has 4 entries —
  asserted by `tests/test_manifest.nim:17-34`.
- `game.replay_viewer = {"bundle": "static-replay-viewer"}` inside `game` (`:16-18`);
  `tools/build_replay_viewer.sh` exists, is mode **100755** in git, and is the `coworld build`
  hook (asserted executable at `ci.yml:236-247` and invoked by path at `:260`).
  `tools/ci/docker_smoke.sh` is also **100755**. No `/client/replay` pod path in the manifest —
  the only occurrence of that string is prose in `game.protocols.global` describing the three
  browser pages the game container serves (`server.nim:515`, as the design note's route list
  prescribes at design.md:514).
- `game.docs` is `{readme:{type:text,value}, pages:[{id,title,content:{type:text,value}}]}` and
  `game.protocols` carries **both** `player` and `global`, each a typed text object
  (`tests/test_manifest.nim:69-83`).
- `config_schema`: `additionalProperties:false`, `required:["tokens","players"]`, both array
  properties carry `minItems 2 / maxItems 10`; every scalar bound matches the note
  (`cards 4..13`, `coins 4..50`, `size 1..5`, `minBid 0..2`, `maxRounds 2..60`,
  `episodeTimeoutSeconds 60..6000`, `batchSpacingSeconds 0..60`, `turnDelayMs 0..10000`,
  `maxOutputTokens 64..2000 default 900`, `llmTimeoutSeconds 5..300 default 30`,
  `player_connect_timeout_seconds` number ≥ 0 default 180, `model` default `claude-sonnet-5`).
  **No `game_config` anywhere contains `tokens`** (checked programmatically over the whole
  document, and by `tests/test_manifest.nim:37-42`).
- `results_schema`: every array `minItems 2 / maxItems 10`; `reason` enum `["complete","deadline"]`;
  `ending` enum of the five values. `docker_smoke.sh:286-367` validates the produced
  `results.json` against it (CI: `results.json validates against game.results_schema`).
- Both bundled players carry `resources.limits.cpu == "1"` and `requests.cpu == "100m"`;
  the secret URI is `secret://coworld/goofspiel-oshi-zumo/anthropic_api_key` = `game.name`;
  8 top-level tags; `$schema` present; no top-level `version`, no `game.display_name`,
  no `game.tags`; `episode_timeout_minutes: 20`; the image placeholder is
  `{{GOOFSPIEL_OSHI_ZUMO_IMAGE}}`, matching the compose service `goofspiel-oshi-zumo`.
- `tests/test_sim.nim:365-386` constructs a `Sim` from **every** shipped `game_config`
  (both variants and the fixture).

**Workflows and CI**
- `ci.yml` jobs: `test` (every `tests/*.nim` in debug **and** `-d:release`), `docker-smoke`,
  `wasm-viewer` with `needs: docker-smoke` (`:212`), the chrome scope check (`:225-226`), the
  bundle build and completeness checks, the browser load test, the renderer-fixture step, and
  three evidence artifacts.
- Run **33016530966** on `main`, head sha `1a29c60e88af98dbd3cca00c26366d22c12d4cd1`,
  conclusion **success**; all three jobs green. `gh run list -R … --branch main -w ci.yml` shows
  it as the latest run.
- "No test loosened": `git log -p -- tests/` in the clone shows a single commit touching
  `tests/` (`0819899`, adding all four files); no later edit, deletion, `skip` or widened
  tolerance exists. The scaffold commit added no test files.
- `docker-smoke` log (job 98336084293): `game=goofspiel-oshi-zumo seats=4`,
  `no ANTHROPIC_API_KEY`, `all 4 player containers exited 0`, `episode end reason: complete`,
  `results.json validates against game.results_schema`,
  `smoke OK: seats=4 results=328B replay=6306B reason=complete`. **No `SEAT-COUNT FAIL` anywhere
  in the log.** The four seat-count invariants are enforced before any container starts
  (`docker_smoke.sh:110-151`), and `SMOKE_SEATS` defaults to the substituted `4` (`:54`) as the
  independent second declaration.
- `coworld-release.yml` order: build (`:165`) → certify with `--timeout-seconds 300`
  (`:179-182`) → **upload the policies** (`:213`) → `upload-coworld` (`:316`) →
  `secret put` reading the namespace from the built manifest's `game.name` (`:363-370`) →
  `release-result.json` assembled and uploaded. Per-policy `"player"` handling is present
  (`softmax player use` / `unset` around each upload, `:240-302`).
- `coworld-submit.yml` takes `player_id`, `policy`, `league_id` inputs (`:23-34`) and uploads a
  `submit-result` artifact (`:136-141`).
- `tools/ci/policies.json`: four policies — two `PLAYER_PROMPT` champions carrying the note's
  exact prompt text, plus `PLAYER_SCRIPTED=match` and `PLAYER_SCRIPTED=hoard`; champion #2
  (`goofspiel-oshi-zumo-reader`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows,
  `docker_smoke.sh` and `policies.json` matches nothing (exit 0). The surviving angle-bracket
  names are exactly the expected residue: `<cow_id>`/`<sha>` in `ci.yml:202`, `<run_id>` in
  `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` in
  `coworld-submit.yml:31` (plus a second `<cow_id>` in a `coworld-release.yml:75` comment).
- `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs`; `tools/ci/docker_smoke.sh` is the
  template with the three substitutions plus an **added** `results_schema` validator (an
  addition, not a weakening).
- `tools/ci/chrome_scope_check.mjs` implements assertion 27: no chrome export re-declared in the
  game block, all ten region markers present, the one `feedText` edit present, `markRoundBeat`
  present, no `function markBeat` in the game block, `relayout` present. CI:
  `chrome scope OK: 31 exported names, 10 copied regions intact, no shadowing`.

**Two name spaces**
- Agents see aliases only: `systemPrompt`/`userPrompt` use `sim.names` (`llm.nim:272-377`), the
  `welcome` frame sends the alias (`server.nim:432-440`), `playerStateJson` has no policy names
  (`:100-129`), and the `final` frame deliberately swaps in the aliases (`server.nim:183-192`).
  Spectator side gets `policyNames` (`snapshotJson:94`, `replayPayloadJson`), and the viewer maps
  aliases→policy names for non-baseline seats (`chrome_common.js:101-133`, used at
  `renderer.js:920`, `:596`).

**Assertions 1-27 of the note's §Tests**: all 27 are present and were executed green in run
33016530966 — 1-11 in `tests/test_sim.nim`, 12-15 in `tests/test_bot.nim`, 16-19 in
`tests/test_replay.nim`, 20-23 in `tests/test_manifest.nim`, 24 in `tools/ci/docker_smoke.sh`,
25 and 26 as `ci.yml` steps, 27 as `tools/ci/chrome_scope_check.mjs`. Two carry deviations from
the note's wording (F4/F5 above and the substitute in test 8 below); none is weakened relative to
an earlier version, because there is no earlier version.

**Test 8's documented substitute** (`tests/test_sim.nim:274-300`): the note asks for
"`score == +1` iff a seat took all 91 points". The test instead plays six rounds in which seat 0
bids its highest card and the others their lowest (asserting `winners == @[0]` each round), then
calls `endEarly()`, and asserts `points[0] == pool`, `score(0) == 1.0`, `score(1..3) == −1/3`, and
that the four scores sum to 0. [computed] the substitute is sound and the unreachability claim is
true: with four identical 1..13 hands, some opponent holds the 13 in every permutation, so seat 0
cannot strictly outbid all three in all 13 rounds (the test's comment gives the specific forced
four-way tie at round 7 under this strategy). The substitute does pin the formula — `score = +1`
requires `points_i == awardedPool`, i.e. `(N·1 − 1)/(N − 1)` — and it exercises the deadline
scoring path at the same time. It does **not** exercise the converse ("+1 only if"), and the
oshi-zumo half of the note's clause ("pushed the token off" ⇒ +1) is covered separately at
`tests/test_sim.nim:200-201`.

---

## Could not determine

- **Whether the fixture's 374 `ellipsized` draws include remark lines** as well as nameplates.
  The harness records only the first 12 samples (`tools/ci/viewer_smoke.mjs:336-338`) and all 12
  are the 24-char `clampName` nameplate cut. What would settle it: a run with `SAMPLE_CAP` raised
  (or a distinct-string dump of ellipsized text), or a screenshot taken at the 360 px stage rather
  than after the last 1280 px stage. The *geometric* claim in F1 does not depend on this.
- **Whether the hosted LLM path stays inside the batch budget in practice.** The bounds are
  explicit and checkable in code (F-free, see *Waits and bounds*), but no CI run exercises the LLM
  path — `docker_smoke.sh` runs without a key by design. Only a hosted episode would settle the
  real per-round latency and the fallback rate.
- **Whether `coworld certify` / `upload-coworld` accept this manifest.** `coworld-release.yml`
  has not been dispatched at this sha (no release run exists on the repo), so the platform-side
  validation of `docs`/`protocols`/`player.resources` is unverified beyond the local
  `tests/test_manifest.nim` assertions.
- **The exact reachability of F7's artifact-POST raise.** It depends on
  `COGAME_RESULTS_METHOD`/`COGAME_SAVE_REPLAY_METHOD` being `POST` with an `http(s)` URI on the
  hosted platform and the endpoint returning a non-2xx; I have no visibility into which method
  the platform sets.
