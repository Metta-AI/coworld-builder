# r1 review — trick-taking

Range: `53ab652..80aeb68` (the whole diff against the bootstrap commit; reviewed sha
`80aeb68c22a1df867c7f2fcf9cf4b12c26104099`, cloned fresh to `/tmp/cogame-trick-taking`)
Files read: 43 (all of `src/`, `tests/`, `client/`, `replay-viewer/`, `tools/`, the three
workflows, the manifest, `Dockerfile`, `compose.yaml`, plus `/workspace/starters/cogame-babel`
counterparts for `client/{chrome.css,renderer.js,replay.html,player.html}` and
`replay-viewer/{config.nims,static_replay.js,index.html}`, and
`coworld-builder/templates/tools/ci/{docker_smoke.sh,viewer_smoke.mjs}`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Design note: `runs/2026-08-26-trick-taking/design.md` (byte-identical to the in-repo
`docs/plans/2026-08-26-trick-taking-design.md` — `diff` returns clean)
CI evidence: run **33027812959**, `main`, conclusion **success** at the reviewed sha;
jobs `test` (98373173401), `docker-smoke` (98373173737), `wasm-viewer` (98373384147) all green.

---

## Blocking

### B1 — the scorebug's labels are hidden under 400 px, not under 640 px
- Where: `client/chrome.css:581-591` (the only media queries in the file); `client/chrome.css:447`
- Observed: the appended block ends with exactly two media queries —
  ```css
  @media (max-width: 720px) { #feed { display: none; } }
  @media (max-width: 400px) {
    #wordmark { font-size: 15px; }
    #clock { font-size: 12px; }
    .plate-label { display: none; }
    .plate-pips { display: none; }
    #modulechip { font-size: 9px; padding: 1px 4px; }
  }
  ```
  There is no `640px` breakpoint anywhere in `client/chrome.css` (grep for `max-width` returns
  lines 582 and 585 only), and the inherited babel CSS above the banner at line 435 carries none
  either (`/workspace/starters/cogame-babel/client/chrome.css` has no media query at all). So
  between 401 px and 640 px each `.plate` still renders `<span class="plate-label">points</span>`
  and up to 13 `.plate-pip`s (emitted unconditionally by `client/renderer.js:911-928`) alongside
  the name and the score.
- Checklist item: 11 — "**Viewer legible at 360 px.** … `.plate-name { flex: 1 1 auto;
  min-width: 3.2em; }`, labels hidden under `640px`." *(category: legibility)*
- Why blocking: the item names two prescriptions and one of them is not met. The other half **is**
  met verbatim (`client/chrome.css:447` — `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`,
  overriding babel's `flex: 0 1 auto` at line 280-289), and `ci.yml:350-352` greps for exactly that
  rule. At the 360 px featured-match width the labels are in fact hidden (360 < 400), so the
  headline "legible at 360 px" case is covered; the gap is the 401-640 px band. The design note
  (line 966-971) specifies the 400 px breakpoint explicitly, so the code matches the design and
  the design departs from the checklist.

### B2 — the notes parchment ellipsizes the full-cap 400-rune `notes`; the band is not sized from the server's cap
- Where: `client/renderer.js:204-205`, `client/renderer.js:294-325`, `client/renderer.js:167-196`,
  `client/renderer.js:410-416`
- Observed, traced: `computeLayout` reserves `noteLines = h < 480 ? 1 : 2` lines and
  `noteH = noteLines * 11 * scale + 8 * scale` px (renderer.js:204-205). `drawSeat` gives the
  parchment a width of `Math.min(layout.w * 0.3, size * 3.2)` (renderer.js:411). `drawParchment`
  then calls `wrapLines(ctx, text, w - pad*2, layout.noteLines)` (renderer.js:301), and
  `wrapLines` (renderer.js:167-196) does
  ```js
  var overflow = lines.length > maxLines;
  lines = lines.slice(0, maxLines);
  if (overflow && lines.length) lines[lines.length-1] = ellipsize(ctx, lines[lines.length-1] + "…", maxWidth);
  ```
  — i.e. a `notes` string longer than one or two ~100 px lines is cut and marked. Nothing in the
  layout is derived from `MaxNotesLen` (400); `grep -n "400" client/renderer.js` returns nothing.
  The reserved band *is* drawn whether or not a seat has notes (renderer.js:303-322 draws a dashed
  "NO NOTES YET" placeholder), so the scene does not jump — that half of item 15 holds.
- CI evidence (run 33027812959, job `wasm-viewer`):
  - "Load the committed hearts_moon fixture": `canvas text: 87053 drawn, 0 never inside the canvas
    (0 draws crossed an edge), 2659 ellipsized (--strict-text-bounds)`, with sampled string
    `ellipsized: "two high hearts left — ♠♥♦♣ count: queen still out,…"`.
  - "Renderer fixture at three canvas sizes": `11490 drawn, 0 never inside …, 520 ellipsized`, with
    sampled string `ellipsized: "trick 1, two high hearts left — ♠♥♦♣ count:…"` — a **mid-string**
    cut (the fixture's own 400-rune `NOTES` ends `"… queen o…"`, `tools/ci/renderer_fixture.html:72-73`),
    so the ellipsis was added by the renderer, not carried in from the server's cap.
- Checklist item: 15 — "Any text laid out **relative to another element** … gets a **reserved band
  in the layout**, sized from the cap the server enforces on that string (`MaxSayLen` and its kin)
  and measured in the font it will be drawn in"; and "Ellipsis is a design choice for **labels** …
  and a defect for **sentences**. If `ellipsized` counts a remark rather than a nameplate, the box
  is too small." *(category: legibility)*
- Why blocking: `notes` is a model-authored sentence (≤ 400 runes, `src/tricks/types.nim:18`,
  `MaxNotesLen`), not a label, and the CI counter attributes thousands of ellipsized draws to it.
  Stated plainly, and against the item: the design's own claim (design.md:942-945 — "A layout band
  sized from the **server's own caps** (`tell` 120 runes, `notes` 400 runes), measured in the
  drawing font, is reserved for every seat simultaneously") is true for the tell and not for the
  notes.
  **Mitigations I verified rather than assumed:** (a) the *gated* number, `never_inside`, is **0**
  on all three invocations, so the job is legitimately green; (b) the `tell` ribbon **does** fit its
  120-rune cap — the only tell sample in the log, `"all I can say. Nil: not one c…"`, is the exact
  tail of the fixture's own capped `TELL` (`tools/ci/renderer_fixture.html:74-75`; reproduced
  byte-for-byte in python), so its trailing "…" came from the fixture, not from `wrapLines`;
  `drawTell` (renderer.js:442-451) sizes its box from `maxLines = layout.w < 520 ? 3 : 2` and
  `maxW = min(layout.w - 20, 640 * scale)` and the string fits at all three canvas sizes.

### B3 — no grid harness or tuning record exists for the scripted baselines' parameters
- Where: `src/tricks/llm.nim:412-510` (the tuned constants: `orderAt = tracker ? 12 : 10`,
  `aloneAt = tracker ? 18 : 16`, the spades `winners` formula, the oh-hell `winners` formula);
  whole tree
- Observed: `grep -rniE "grid|tune|harness|sweep"` over `*.nim`, `*.md`, `*.sh`, `*.yml`
  (excluding the copied design note) returns three unrelated hits only —
  `src/tricks/types.nim:314` ("sweeps them"), `.github/workflows/ci.yml:416` ("before the harness
  ever runs", about `viewer_smoke.mjs`) and `README.md:118` ("CI is the harness"). There is no
  tuning script, no sweep output, no committed result table, and the design note never claims one:
  its only use of "tuned" (design.md:158) is about the score normaliser, arguing *against* a tuned
  free parameter. The thresholds in §Scripted baselines (design.md:546-551, 586-588) are stated as
  literals with no provenance.
- Checklist item: 7 — "**Scripted baseline plays full episodes legally.** … The baseline's
  parameters were tuned with a grid harness, not guessed."
- Why blocking: the first sentence of item 7 is fully satisfied and I verified it (see *Traced and
  consistent*); the last sentence has no artifact in the tree or in cited CI evidence, so it cannot
  be verified. What would settle it: a committed harness (e.g. `tools/tune_baseline.nim`) with the
  swept grid and the head-to-head result that selected 10/16 and 12/18, or a design-note section
  recording the sweep.

---

## Non-blocking

### N1 — the post-guard settle bound is not derived from the deadline: `extraSpacingMs` grows without a cap and `llmTimeoutSeconds` is schema-capped at 300
- Where: `src/tricks/llm.nim:945-949`, `src/tricks/server.nim:254-266` and `:315-327`,
  `coworld_manifest_template.json` `config_schema.llmTimeoutSeconds` (`"maximum": 300`)
- Observed: the guards are read once per loop iteration inside the lock
  (`server.nim:259-266`: `pastSoft`, `pastHard`, `budgetOut`), and *then*, outside the lock, the
  decision path sleeps the spacing floor and issues up to two LLM attempts:
  ```nim
  let spacing = (DecisionSpacingMs + client.extraSpacingMs).float / 1000.0   # server.nim:318
  let wait = lastDecisionAt + spacing - epochTime()
  if wait > 0: sleep(int(wait * 1000))                                       # server.nim:320-321
  ```
  `client.extraSpacingMs` is incremented by `ThrottleExtraMs` (500 ms) on **every** HTTP 429
  (`llm.nim:947`) with no ceiling, and the design (design.md:487) intends exactly that. Both waits
  are individually finite, so there is no unbounded loop and no blocking read; what is unbounded is
  the *growth* of one of them. Arithmetic (inference, untested): if every call is throttled,
  cumulative wall clock to the *n*-th decision is `Σ(2.2 + 0.5k) = 2.2n + 0.25n(n-1)`, which
  reaches the 660 s soft guard at n ≈ 47, where the spacing is ≈ 25.7 s. A decision that begins at
  659 s therefore sleeps to ≈ 685 s and, if that attempt then times out twice at
  `llmTimeoutSeconds = 20`, returns at ≈ 725 s — past the 720 s pin, after which the settle itself
  is instant. Separately, `config_schema` permits `llmTimeoutSeconds` up to 300, and nothing in
  `server.nim` clamps `2 × llmTimeoutSeconds + spacing` against the remaining budget; the shipped
  variants do not set the field, so the platform default of 20 applies (`types.nim:230`).
- Checklist item: 5 (*category: timeout*) — "Every wait … has an explicit bound; the episode
  settles and scores inside **60 %** of `episodeTimeoutSeconds`".
- Why non-blocking: every wait *is* explicitly bounded and the guards are checked before every
  decision; in the shipped configuration with a functioning transport (or with none at all — the
  docker smoke, where `client.disabled` skips both the spacing and the call, `server.nim:315`) the
  episode settles far inside 720 s. The overshoot I can construct requires ~47 consecutive 429s and
  is ~5 s. Labelled: **inferred**, not observed; it would take a throttled live episode to settle.

### N2 — the re-derivation test compares the event log and the final frame, not each intermediate live frame
- Where: `tests/test_sim.nim:526-582`, `src/tricks/sim.nim:890-955`
- Observed: `rederives()` asserts (a) `eventsJson(again.events) == eventsJson(sim.events)`,
  (b) `$again.resultsJson() == $sim.resultsJson()`, (c) `$replayStates(config, events) ==
  $replayStates(config, sim.events)` — re-derivation vs re-derivation of the round-tripped log,
  (d) `frames.len == events.len + 1`, (e) `$frames[^1].frameStateJson() == $sim.frameStateJson()`.
  It is run for all four modules and for all three end reasons (`complete`, hard-deadline `handVoid`,
  `budget`). What it does not do is compare frame *i* to a live per-tick state for i < last — the
  live server never records a per-tick timeline (it broadcasts `frameStateJson` and discards it,
  `server.nim:115-120`), so there is no parallel recording to drift from, which is the substance of
  item 2. The viewer's display comes from `payload.states` (`client/renderer.js:1281`,
  `1307-1310`), and `states` is produced only by `replayStates(config, events)` — in the wasm path
  at `replay-viewer/trick_taking_replay.nim:36` and in the live replay path at `server.nim:531`.
- Checklist item: 2 — bears on "reproduces the recorded per-tick state **frame by frame** … A test
  asserts it".

### N3 — `GET /client/replay` and `client/replay.html` exist as routes/pages, inherited from the starter
- Where: `src/tricks/server.nim:508`, `client/replay.html` (86 lines),
  `/workspace/starters/cogame-babel/src/babel/server.nim:502` (identical route)
- Observed: the router registers `/client/replay` → `replay.html`, which drives the shared renderer
  from the `/replay` websocket (`client/replay.html:52-77`). The manifest declares **only**
  `game.replay_viewer: {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json`,
  asserted by `tests/test_manifest.nim:44-46` and re-checked by `ci.yml:355-358`); no pod viewer is
  declared anywhere, `tools/build_replay_viewer.sh` is present, mode 100755, and is the
  `coworld build` hook (`.github/workflows/coworld-release.yml:159-172` plus the
  `LIVENESS_MARKER` assertion at `:186-208` that certification reported the STATIC bundle).
- Checklist item: 3 — "No `/client/replay` pod path anywhere" *(category: static-viewer)*.
- Why non-blocking as I read it: the substance of item 3 — the declared viewer is the static bundle
  and the bundle contacts nothing but the `?replay=` URL — holds. The literal path exists because it
  is starter chrome that the design states the certifier requires (design.md:746-757), and it is
  byte-for-byte the same route babel ships. Flagging it here because the item's wording is literal
  and a judge should see the line rather than infer its absence.

### N4 — `fit()` was edited in all three pages: a fourth change to inherited chrome, not among the three named patches
- Where: `client/replay.html:42-49`, `replay-viewer/index.html:43-49`, `client/player.html:34-39`
- Observed: babel's two-line `fit()` (`canvas.width = canvas.clientWidth; canvas.height =
  canvas.clientHeight;`) became
  ```js
  var parent = canvas.parentElement;
  canvas.width = canvas.clientWidth || (parent && parent.clientWidth) || 960;
  canvas.height = canvas.clientHeight || (parent && parent.clientHeight) || 640;
  ```
  The design note names exactly three patches to the inherited chrome (design.md:879-896:
  `buildTrickBeats` buttons, `relayout()`, the rune-safe prompt cap) and says of the pages
  "**Removed from the starter's page: nothing**" and "**Appended:** one `<div id="modulechip">` …
  and the `relayout()` bootstrap" (design.md:858-867). This edit is neither an append nor a listed
  removal. It is small, defensive (a zero-sized canvas would make `draw` bail at
  `renderer.js:553`), and identical in all three pages.
- Checklist item: 14 — chrome provenance. Everything else in the three pages diffs clean against
  babel modulo the wordmark, `<title>`, the `#modulechip` element under the banner comment, the
  `BabelRenderer` → `TrickTakingRenderer` rename, and the appended `relayout()` bootstrap.

### N5 — the design says `viewer_smoke.mjs` asserts the endcard/transport geometry; the harness contains no such assertion
- Where: design.md:908-910 vs `tools/ci/viewer_smoke.mjs`
- Observed: `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` clean), as the design requires
  (design.md:1223-1224). Grepping that file for `endscreen`, `endcard` or `transport` returns
  nothing, so the claim "`viewer_smoke.mjs` asserts `#endscreen`'s rendered bottom is ≥
  `#transport`'s rendered top" is not implemented by anything in this repo. The structural
  guarantee itself is real and I verified it in the markup: `#endscreen` is a child of
  `#board-wrap` (`replay-viewer/index.html:22-27`), `#transport` is `#board-wrap`'s next sibling
  inside `#stage` (`:28-34`), and the appended CSS pins `#endscreen { bottom: 0 }` within that box
  (`client/chrome.css:487-491`: `#endscreen { bottom: 0; max-height: calc(100% - 0px); }`).
- Checklist item: 14(c) — bears on "`#endcard` keeps `bottom: var(--band, 0px)`".

### N6 — the euchre kitty keeps the up-card after the dealer picks it up, so the card is drawn twice
- Where: `src/tricks/euchre.nim:17-19`, `src/tricks/euchre.nim:162-168`,
  `src/tricks/sim.nim:757-772`, `client/renderer.js:526-543`
- Observed: `euchreSetup` sets `sim.kitty = rest[0 ..< 4]` and `sim.upcard = sim.kitty[0]`. When a
  seat orders it up, `euchreApply` adds `sim.upcard` to the dealer's hand and sets
  `upcardLive = false`, but never removes it from `sim.kitty` and never clears `sim.upcard`.
  `frameStateJson` therefore still ships `kitty` (4 entries) and `upcard` (a card now in the
  dealer's hand), and `drawTableFurniture` draws `kitty.length - 1 = 3` card backs plus the
  up-card's **face** in the corner (renderer.js:536-542) while `drawFan` also draws it in the
  dealer's fan. Re-derivation is unaffected: `beginHandFrom` feeds `event.kitty` straight back into
  `setupHand` and then asserts `sim.upcard == event.upcard` (`sim.nim:284-291`), which holds.
  Redaction is unaffected: `playerStateJson` deletes `kitty` and `discard` for every seat
  (`server.nim:105-107`).
- Checklist item: advisory (spectator-side display only; spectators are meant to see everything).

### N7 — `frameStateJson` carries two fields the design's "exact state JSON" sample does not list
- Where: `src/tricks/sim.nim:771-772` (`"kitty"`, `"discard"`) vs design.md:686-702
- Observed: the design says `frameStateJson(frame)` "serialises each frame into **exactly** this
  object" and the sample has no `kitty` and no `discard`. The implementation adds both; the
  renderer consumes `kitty` (renderer.js:536) and the manifest's `game.protocols.global` documents
  both. Nothing reads `discard` in `renderer.js` (grep: only `"discard": -1` in the fixture).
- Checklist item: advisory.

### N8 — `bidsMade` for spades counts "at least the bid", which is not what `results_schema` says
- Where: `src/tricks/spades.nim:134-138`, `src/tricks/ohhell.nim:128-130`,
  `coworld_manifest_template.json` (`results_schema.properties.bidsMade.description`)
- Observed: spades increments `bidsMade` when `tricksWon >= bids and bids > 0`, or on a made nil;
  oh-hell increments only on `tricksWon == bids`. The schema description reads "Hands in which the
  slot made its bid **exactly** (or a made nil)". For spades "making the bid" is `≥` by the rules,
  so the code is right for the game and the description is imprecise.
- Checklist item: advisory (`reason` is the only enum item 10/`results_schema` gates, and it is
  correct).

### N9 — hearts' `worstCaseDecisions` is a flat 56/hand where the design's table says 220 for four hands
- Where: `src/tricks/hearts.nim:67` (`heartsWorstCase = 56`) vs design.md:515
- Observed: the design's table computes 56 + 56 + 56 + 52 = 220 (the fourth hand is "hold", so it
  spends no pass decisions); the code charges 56 for every hand → 224 worst-case, 582 s at 2.6 s.
  It is a conservative over-estimate; both are under the 240-call budget and the 660 s soft guard,
  and `tests/test_sim.nim:631-643` asserts both bounds for all four shipped variants.
- Checklist item: advisory.

### N10 — the auto-applied forced move increments `decisions[]` though it spends no model call
- Where: `src/tricks/sim.nim:567-573`, `src/tricks/server.nim:289-296`
- Observed: when `legalCards` has exactly one entry (hearts' opening 2♣, the last card of a hand),
  the server applies it as a scripted play and does `inc state.sim.decisions[call.slot]` without
  touching `modelCalls`. The design calls this "a forced move, no decision spent" (design.md:224),
  which is true of the model-call budget; `results.decisions[]` counts it as a decision.
- Checklist item: advisory (this is one of the pre-logged builder deviations; verified correct in
  substance — no model call, no fallback, and `EpisodeDecisionBudget` is untouched).

### N11 — the game thread has no top-level exception guard
- Where: `src/tricks/server.nim:202-358`, specifically `:277` (`state.sim.beginHand()`) and `:348`
  (`state.sim.applyMove(fallback.move, "", true)`)
- Observed: `runGame` is `createThread`ed at `:555` and contains one `try` (`:338-348`, catching
  `TricksError` around the model move). The deal at `:277` and the fallback apply at `:348` are
  unguarded; if either raised, the thread would die, `finishEpisode` would never run, no
  `results.json` would be written, and the mummy server would keep serving `/healthz` until the
  platform killed the pod. I traced the raise sites and found none reachable: `beginHand` raises
  only on `done`/wrong phase or a short remainder (euchre leaves exactly 4, oh-hell at most
  `52 - 24 = 28`, both guarded by `validate` at `sim.nim:108-128`), and `baselineDecision`
  (`llm.nim:963-975`) probes its own move on a copy and falls back to `lowestLegal`, which cannot
  be empty in a decision phase. Labelled: **inferred**; I found no reachable path.
- Checklist item: 5 (*hang*) — reported as an unguarded shape, not as a demonstrated hang.

### N12 — `client/renderer.js`'s `ellipsize` slices UTF-16 code units
- Where: `client/renderer.js:111-118` (byte-identical to
  `/workspace/starters/cogame-babel/client/renderer.js:101-108`)
- Observed: `cut = cut.slice(0, -1)` can split a surrogate pair when it trims an astral character,
  producing a lone surrogate on the canvas. This is viewer-side cosmetic truncation of an
  already-valid string; every string that reaches the **replay** goes through
  `truncateRunes` (`src/tricks/types.nim:204-212`), which is what item 9 gates.
- Checklist item: advisory (inherited starter code, unmodified).

---

## Traced and consistent

**Rules — shared engine**
- `src/tricks/sim.nim:299-324` — `legalCards`: cards of the led suit if any are held, else the whole
  hand, then the module's `restricted` overlay, then "if the overlay emptied it, fall back to base",
  so the set is never empty. `applyPlay` (`:476-482`) re-computes the *same* `legalCards` and
  rejects anything outside it, so the advertised set and the validating predicate are literally the
  same call. Asserted over 500 random matches per module in `tests/test_sim.nim:105-141`, including
  "holding the led suit means the legal set IS the led suit" (`:132`).
- `src/tricks/sim.nim:443-474` — `resolveTrick` picks the best by `beats(card, best, ledSuit,
  trumpOf(sim), isEuchre)`, credits the winner, records the `trick` event with the cards in play
  order and the hearts penalty, and calls `finishHand` when the trick count is complete.
- `src/tricks/cards.nim:98-116` — `beats`: trump beats non-trump; two trumps compare by
  `euchreTrumpRank` in euchre and by rank elsewhere; off-led-suit never wins. Covered by
  `tests/test_cards.nim:46-99`.
- `src/tricks/sim.nim:217-266` — deal: `dealer = hand mod 4` (`:227`), a fresh shuffle from
  `initRand(seed*104729 + hand*7919 + 13)` (`:229-230`), clockwise from `dealer+1`, module packets
  (`euchre.nim:10-12` → `@[3,2,3,2,2,3,2,3]`) or one-at-a-time, remainder to `setupHand`, and the
  full deal written to the `hand` event (`:204-215`). `tests/test_sim.nim:74-102` checks no card
  twice, none lost, and the up-card/turn-up out of the dealt set.

**Rules — euchre** (`src/tricks/euchre.nim`)
- Bowers: `euchreEffectiveSuit` (`cards.nim:83-87`) makes the left bower trump for following,
  leading and winning; `euchreTrumpRank` (`:92-96`) ranks right 100 > left 99 > A > K > Q > 10 > 9.
  `tests/test_cards.nim:66-99`.
- Round 1 offers `pass|order|alone` on the up-card's suit (`:42-46`); the first non-pass makes trump,
  the dealer picks the up-card up and moves to `phDiscard` (`:162-168`), which lists all six cards
  (`:56-58`) and leaves five (`tests/test_sim.nim:307-309`).
- Round 2 bans the up-card suit (`:48-55`) and **stick-the-dealer** removes `pass` at `bidStep == 3`
  — which is the dealer, since round 2 restarts at `dealer+1` (`:143`) — with `sim.stuck` set at
  `:147-148`. No re-deal path exists. `tests/test_sim.nim:278-298`.
- Alone: `finishEuchreBidding` (`:104-114`) seats the maker's partner out and picks the first
  playing position left of the dealer; `nextPos` (`types.nim:303-310`) skips it and
  `seatsInPlay` returns 3, so three seats play five tricks.
  `tests/test_sim.nim:300-319` asserts the sitting-out seat never acts and keeps its five cards.
- Scoring (`:189-209`): 3-4 → 1, 5 → 2, alone 5 → 4, ≤ 2 → defenders 2; `net = mine - theirs`
  ∈ {±1, ±2, ±4}; `swingCap = 4`. `tests/test_sim.nim:259-276`.

**Rules — spades** (`src/tricks/spades.nim`)
- Trump always ♠ (`:20`); a spade may not be led until broken (`:22-24`) unless the fallback in
  `legalCards` fires (all-spades hand); `breaks` fires on a spade led or a spade played off-suit
  (`:26-28`). `tests/test_sim.nim:168-192`.
- Bids 0…13 inclusive, 0 = nil (`:36-39`, `:68-69`).
- Scoring (`:91-138`): contract = sum of non-nil partner bids **capped at 13** (`:117`, the logged
  deviation — verified correct and load-bearing); made → `10C + bags` where
  `bags = nonNilTricks + failedNilTricks - contract`; set → `-10C`; nil ±100. I re-derived the
  bound by hand: `base ≤ 9C + 13 ≤ 130`, `|nilBonus| ≤ 200` but a ±200 case forces `C = 0` and
  `base ∈ [0,13]`, so `|teamScore| ≤ 230` and `|net| ≤ 460 = swingCap`. Asserted over 10 000 random
  hands at `tests/test_sim.nim:331-347` and by the worked examples at `:349-375`.

**Rules — hearts** (`src/tricks/hearts.nim`)
- Pass cycle left/right/across/hold by `hand mod 4` (`:11-24`), all four seats choose before
  anything is delivered (`:117-136`); the per-card `legalMoves` pool with triple validation in
  `applyMove` is the logged deviation and is handled correctly — `sim.applyMove`'s `moveAllowed`
  falls through for `phPass` (`sim.nim:534-548`) and `heartsApply:97-105` enforces "exactly three
  distinct held cards". `lowestLegal` returns three cards for `phPass` (`sim.nim:590-595`).
  `tests/test_sim.nim:378-404`.
- Trick 0: only the 2♣ may be led and nothing penalty-bearing may be played, unless the seat holds
  nothing else (`:47-55` + the `legalCards` fallback); hearts may not be led until broken; a heart
  or the Q♠ **discarded** (led, or played while void) breaks them (`:57-59`).
  `tests/test_sim.nim:194-232` asserts all four opening leads are exactly `[2♣]`.
- Moon (`:138-156`): a seat on 26 scores 0 and the others 26; `net = mean - p`, so a normal hand is
  `[-19.5, 6.5]` and a moon is `{19.5, -6.5}`, both inside `swingCap = 19.5`.
  `tests/test_sim.nim:406-426`.

**Rules — oh-hell** (`src/tricks/ohhell.nim`)
- Turn-up sets trump and stays out of play (`:18-25`; `tests/test_sim.nim:457`).
- The hook (`:43-56`, `:58-64`, `:99-102`) removes exactly the balanced value and only at
  `bidStep == Seats-1`, i.e. the dealer; `hookedBid` returns -1 when the balanced value is out of
  range. `tests/test_sim.nim:429-461` checks the legal-move counts on both sides of it.
- Scoring `s = 10 + bid` on exact, else 0; `net = s - mean`; `swingCap = 0.75·(10+c)` — I checked
  the extremes both ways (one scorer, three scorers) and neither exceeds it.
  `tests/test_sim.nim:463-483`.

**Scoring formula and caps**
- `src/tricks/sim.nim:348-364` — `scores[i] = 0.5 + net[i]/(2·norm)`, `0.5` for every seat when
  `handsScored == 0`; `winsOf` marks every tied maximum. `norm` accumulates `swingCap` per **scored**
  hand only (`finishHand:409-412`), and `voidHand` (`:420-432`) adds neither, so a voided hand is
  outside `H` and `NORM`. `tests/test_sim.nim:485-524` runs 2000 random matches per module and
  asserts `Σnet == 0`, `Σscores == 2.0`, `scores ∈ [0,1]` with no clamp, break-even == exactly 0.5,
  and that no realised `net_h` exceeds its module's cap.

**Decision path**
- `src/tricks/llm.nim:977-1012` — `decide`: scripted or `client.disabled` returns the baseline
  immediately with no network (`:987-988`); otherwise `for attempt in 0 .. 1` — **exactly one
  retry** — with `userPrompt(..., retry = attempt > 0)` adding the "previous reply was invalid"
  line and re-printing the legal cards (`:810-814`); each attempt parses tolerantly
  (`extractJsonObject:818-828` — first `{` to last `}`), then **probes the move against a copy of
  the sim** (`:997-999`) so an illegal-but-parseable reply also triggers the retry; a 429 breaks out
  without retrying (`:1008-1010`); the tail is `baselineDecision(sim, baseline, lastError)`.
- `src/tricks/llm.nim:963-975` — `baselineDecision` probes the scripted move and, if the engine
  rejects it, forces `lowestLegal` and sets `forced = true`.
- `src/tricks/server.nim:329-350` — the fallback is **recorded**: `fallbacks[slot]` on a scripted
  decision taken on the model path, `forcedMoves[slot]` on a forced one, plus a second
  `fallbacks`/`forcedMoves` increment if the applier rejects the model's move. Both arrays reach
  `results.json` (`sim.nim:688-690`) and `results_schema`.
- Tolerance verified in `parseCard` (`cards.nim:161-203`): `10H`, `TH`, `HT`, `H10`,
  `ten of hearts`, `9♦` and lower case all resolve; a bare 1..k integer is a 1-based index into the
  printed legal list (`llm.nim:830-838` and `:849-856`). `tests/test_cards.nim:6-44`.
- Transports in babel's order (`llm.nim:110-133`): Bedrock endpoint/token, then
  `ANTHROPIC_API_KEY`, then `ANTHROPIC_API_KEY_URI`; `us.anthropic.claude-sonnet-4-6` is **absent**
  from `bedrockModelIds` (`:84-87`) as the note requires; `maxOutputTokens` 900 and
  `llmTimeoutSeconds` 20 are the defaults (`types.nim:229-230`); the `output_config.effort` guard at
  `:930` is babel's line verbatim (`cogame-babel/src/babel/llm.nim:361-362`).

**Waits and their bounds**
- Connect: `server.nim:206-214`, a `sleep(200)` poll bounded by
  `gameStart + playerConnectTimeoutSeconds` (180 s in every variant), then the episode starts
  regardless.
- Soft guard: `server.nim:234` `gameStart + T*0.55`; past it `stopReason = "deadline"` and
  `seatScripted = state.scripted[slot] or stopReason.len > 0` (`:300`), so the rest of the hand is
  scripted and instant, the hand is scored by `finishHand`, and the next `ckDeal` iteration calls
  `endEarly(stopReason)` (`:269-275`) — the hand in progress **is** scored, exactly as design §11.2
  says.
- Hard guard: `server.nim:235`, `:281-288` — `voidHand()` records `handVoid`, excludes the hand from
  `H`/`NORM` and settles `"deadline"`.
- `T` = `COWORLD_TIMEOUT_SECONDS` when present, else `config.episodeTimeoutSeconds` (default 1200,
  `types.nim:229`; `server.nim:227-233`).
- Budget: `modelCalls >= EpisodeDecisionBudget` (240, `types.nim:25`) → `stopReason = "budget"`,
  same settle path (`:262-266`).
- Spacing: 2200 ms decision-start to decision-start, applied only on the model path
  (`server.nim:315-322`), so the credential-less smoke costs nothing (docker-smoke ran the whole
  three-hand episode in ~21 s).
- Pacing: `turnDelayMs` slept only after a **completed trick** (`server.nim:295`, `:349`, `:352-354`).
- Shutdown: players get `final` before the artifacts are written (`server.nim:153-172`), then
  `sleep(500)`, then the results and replay are written, then a bounded
  `ShutdownGraceSeconds = 20` (`:36`, `:184`) during which `/healthz` and `/global` keep answering
  and mummy Pings are answered with Pongs (`:463-466`), then `quit(0)`.

**String truncation**
- `src/tricks/types.nim:204-212` — one `truncateRunes(text, limit)` using `runeLen`/`runeSubStr`
  and appending U+2026. Used for notes 400 (`cleanNotes:214-215`), tell 120
  (`sim.nim:519`, `euchre.nim:131`, `spades.nim:83`, `ohhell.nim:113`), the operator prompt 4000
  (`llm.nim:792` **and** `server.nim:479`, the byte-slice → rune-slice patch the design names),
  aliases 16 (`sim.nim:59`), the recorded error 200 (`llm.nim:967`), and the euchre `action`/`suit`
  fields (`llm.nim:871-877`). `tests/test_sim.nim:645-676` and `tests/test_bot.nim:186-214` feed
  4-byte astral input at the cap and assert `validateUtf8() == -1` on the whole replay.

**Replay writer and event vocabulary**
- `src/tricks/sim.nim:806-886` — `eventToJson`/`eventFromJson` for all 13 kinds; every kind is
  produced and round-tripped in `tests/test_sim.nim:584-603` (including `handVoid`, `audit`, `end`).
- `src/tricks/sim.nim:982-1002` — `replayJson` carries protocol, alias `names`, `policyNames`,
  config (module, hands, dealSchedule, seatOrder, partnership, swingCaps, norm, seed, sampled,
  gameVersion), the whole event log with every dealt card, and the results. Nothing else is fetched
  by the viewer.
- `src/tricks/sim.nim:890-940` — `replayRun` re-applies only `bid`/`pass`/`discard`/`play`, takes the
  deal from the recorded `hand` event (`beginHandFrom:268-292`, which cross-checks the up-card and
  turn-up), applies `handVoid` through the **same** `voidHand` proc used on record, and settles
  `evEnd` with the recorded reason — so a `deadline` replay re-derives like a `complete` one.
- The pre-logged fixture deviation is correct: `tools/ci/gen_fixture.nim:168-177` pads one lead's
  `tell` to the 120-rune cap *after* generation, and `sim.nim:926-929` re-applies the recorded tell
  (`if event.trickPos == 0: sim.tell = event.tell`) so the pad survives re-derivation.
  `tests/test_sim.nim:678-716` diffs the committed fixture against a fresh generation and asserts
  the moon, the four full-cap notes, the single full-cap tell and the non-null audit.

**Viewer re-derivation and the two name spaces**
- `replay-viewer/trick_taking_replay.nim:20-40` and `server.nim:517-533` build the identical
  `{type, protocol, names, policyNames, config, events, results, states}` envelope, `states` from
  `replayStates` in both.
- `client/renderer.js:1276-1330` — `attachReplay` reads `payload.states`, never re-simulating in JS.
- Aliases: `tableNames` (`sim.nim:51-61`) draws from `CogNames`; prompts use `sim.names` only
  (`llm.nim:597-628`, `766-768`); the player `final` frame sends aliases (`server.nim:157-165`).
  Policy names: `results.names` (`sim.nim:640`), `replay.policyNames` (`:990`), `/global`'s
  `policyNames` (`server.nim:93`) — and `playerStateJson` never adds it. `makeNameMap` +
  `isBaselineFiller` (`renderer.js:611-639`) map aliases → policy names except for
  `/^baseline(\s*\(\d+\))?$/i`. `tests/test_bot.nim:216-247` asserts no `tell` ever appears in
  `systemPrompt`/`userPrompt`, and `:249-263` that a prompt carries its own legal set and no other
  seat's hand.
- Redaction: `server.nim:99-113` blanks every other slot's `hand` and `notes` and deletes `tell`,
  `kitty` and `discard`; the player state carries no `events` array at all, so no pass, deal or
  note can leak that way.

**Manifest**
- `num_agents: 4` in all four variants **and** in `certification.game_config`;
  `len(certification.players) == 4`; `len(certification.game_config.players) == 4`;
  `SMOKE_SEATS` = `4` (`ci.yml:206` passes `SMOKE_SLUG`, `docker_smoke.sh:54`
  `seats_expected="${SMOKE_SEATS:-4}"`). CI log line: `game=trick-taking seats=4 …
  "num_agents": 4 …` and `smoke OK: seats=4 results=660B replay=11128B reason=complete`.
  `grep -c "SEAT-COUNT FAIL"` over the whole docker-smoke log: **0**.
- `game.replay_viewer.bundle == "static-replay-viewer"` nested under `game`; no top-level
  `replay_viewer`, no top-level `version`, no `game.tags`, no `game.display_name`;
  `game.description` present; 7 top-level tags; `episode_timeout_minutes: 20`;
  `game.owner == daveey@gmail.com`.
- `game.docs = {readme:{type,value}, pages:[rules.md, modules.md, scoring.md]}` each
  `{id,title,content:{type,value}}`; `game.protocols` carries **both** `player` and `global` as
  `{type,value}` objects.
- `config_schema`: `tokens` 4…4, `players` 4…4, `dealSchedule` 1…16 — every array property declares
  `minItems`/`maxItems`; `additionalProperties: false`. No `tokens` key in any `game_config`
  (variants or certification).
- `results_schema.properties` has exactly the 29 keys `resultsJson` emits (I diffed both lists),
  with `reason` as `enum ["complete","deadline","budget"]`.
- Three `player[]` runnables, all `/bin/trick-taking-player` from `{{TRICK_TAKING_IMAGE}}`, all
  `limits.cpu == "1"`, all seated in the certification fixture.
- Secret namespace is `game.name`: `secret://coworld/trick-taking/anthropic_api_key`, and
  `coworld-release.yml:362-369` reads the coworld name from
  `dist/coworld_manifest.json["game"]["name"]`, not from a slug variable.
- `compose.yaml` service `trick-taking` → placeholder `{{TRICK_TAKING_IMAGE}}` ✔.
- All of the above is re-asserted in `tests/test_manifest.nim` (220 lines), including "EVERY
  variant's `game_config` constructs a valid `Sim`" and plays its first hand (`:164-174`).

**Static viewer and the MODULARIZE lockstep**
- `replay-viewer/config.nims:38-48` links `-s MODULARIZE=1 -s EXPORT_NAME=TrickTakingReplayModule
  -s EXPORTED_RUNTIME_METHODS=HEAPU8 -s EXPORTED_FUNCTIONS=_main,_malloc,_free,_tt_load_replay,
  _tt_payload_ptr,_tt_payload_len,_tt_error_ptr,_tt_error_len`, and
  `replay-viewer/static_replay.js:140` calls the **factory** `TrickTakingReplayModule()` and only
  the `_tt_*` exports (`:94-103`). There is no `onRuntimeInitialized` anywhere in the tree. Both
  sides are greped in `ci.yml:296-317`, including set-equality of the export list against the
  shell's calls.
- `data-replay-loaded="true"` is set on `<html>` from the renderer's own first painted frame
  (`renderer.js:1348-1354`, inside the `requestAnimationFrame` body after `renderer.draw`), and the
  `ready` postMessage fires **only** from the `onFirstFrame` callback (`static_replay.js:125`) — the
  chorus patch, correctly applied. `data-replay-error` is set from the shell's own `fail()`
  (`static_replay.js:44-58`) and cleared on retry (`:107`, `:136`); the 20 s `AbortController`
  fetch bound is at `:14`, `:71-88`.
- `tools/build_replay_viewer.sh` — mode 100755, `mkdir -p "$(dirname "$output_dir")"` **before**
  anything else (line 23), local `emcc`+`nim` or the pinned `Dockerfile.replay-viewer`, asserts both
  dist artefacts non-empty, copies `index.html`, `static_replay.js`, `client/renderer.js`,
  `client/chrome.css` and the six data assets, then greps `data-replay` in the copied shell.
- **The bundle is executed, not merely built.** `ci.yml`'s `wasm-viewer` job has
  `needs: docker-smoke` (`:234`), downloads the `smoke-replay` artifact (`:396-400`), and runs
  `viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json --timeout 90
  --soak 12 --strict-text-bounds` (`:433-438`) with no `continue-on-error`. Run 33027812959:
  `{"loaded":true,"ms":309,…,"feed_lines":118}`, `soak: 12s of playback kept advancing`,
  three distinct scrub readouts (`HAND 1 / 3 · ♦ TRUMP …` / `HAND 2 / 3 …` / `HAND 3 / 3 · ♣ TRUMP ·
  TRICK 5 / 5 · FINAL`), `43003 drawn, 0 never inside the canvas`.
- The **second** invocation against the committed `tools/ci/fixtures/hearts_moon.replay` ran in the
  same job (`ci.yml:446-456`): `{"loaded":true,"ms":296,…}`, soak advancing, `0 never inside`.
- The **renderer fixture** step ran (`ci.yml:462-479`), loading the shipped `client/renderer.js`
  with a full-cap notes on every seat and a full-cap tell at 360×640, 960×640 and 1440×900, with
  `--strict-text-bounds`: `{"loaded":true,"ms":286,…}`, `0 never inside`. The fixture self-asserts
  its own string lengths (`renderer_fixture.html:87-88`: `runes(NOTES) !== 400` /
  `runes(TELL) !== 120` → `data-replay-error`), so a quietly shortened remark fails it.

**Chrome provenance**
- `client/chrome.css` — `diff` against babel is empty above line 435; the only removal is babel's
  named game tail (`.feed-speak`, `.feed-round`, `.feed-pick`, `.plate-pip.hollow`), exactly the
  removal the note lists (design.md:849-851); everything after the banner
  `/* ==== trick-taking game block (appended; nothing above this line is edited) ==== */`
  (line 435) is additive. Sections 1-5 of the starter chrome (stage, scorebug, banner lane, feed,
  transport, scrubber + `.round-span`/`.round-sep`/`.beat-marker`, endscreen, `#loading`) are
  present and unmodified.
- `client/renderer.js` — the game-specific `draw` is rewritten (as the note prescribes,
  design.md:928-937) while the chrome above it is kept: `isBaselineFiller`/`makeNameMap`
  (`:611-639`), the feed (`:765-844`), `makeEffects` (`:848-872`), `matchHeader`/`updateScorebug`
  (`:876-935`), `updateEndscreen` (`:950-1022`), `bindFeedToggle` (`:1041-1065`), both drivers, and
  the replay pacing table (`:1270-1274`).
- Named patch 1 — the beat builder is `buildTrickBeats` (`:1152`), **not** `markBeat`; each beat is
  a `<button type="button" class="beat-marker <kind> seat<N>">` with `aria-label`/`title` and an
  `onclick` that calls the same `onSeek` the track uses (`:1225-1236`); drag-to-seek is untouched
  (`:1243-1259`). `ci.yml:319-331` fails on a `function markBeat`, on a missing `buildTrickBeats`
  and on any name declared as both a `function` and a `var`.
- Named patch 2 — `relayout()` (`:1029-1039`) measures `#transport.offsetHeight` and sets `--band`
  and `--hudscale` on `document.documentElement`, never on `#stage`; it is called on `load`, on
  `resize`, from `bindFeedToggle` (`:1045-1064`) and from each page's appended bootstrap.
- Named patch 3 — the rune-safe prompt cap at `server.nim:479`.
- Beat kinds: `BEAT_KINDS = ["trick","bid","nil","trump","march","euchred","moon","void","end"]`
  (`:56-57`); `beatFor` emits exactly those (`:1187-1220`, with `"bid" + " nil"` for a nil bid); each
  has a rule in `client/chrome.css:518-580`, and the base `.beat-marker` rule inherited from babel
  (line 195-203) gives every kind a background. `ci.yml:333-347` greps both directions.
- Endcard: `#endscreen` lives inside `#board-wrap` above `#transport` in every page; `setIndex`
  calls `updateEndscreen(..., index >= events.length && events.length > 0, ...)` on **every** index
  change (`:1327-1328`) and `updateEndscreen` toggles the `show` class on every call before its
  `dataset.built` early return (`:954-955`), so both seek paths that exist — scrub click/drag and a
  beat button — take the endcard down. There are no back/forward buttons and no keyboard handler in
  this (inherited) transport: `grep keydown` over `client/` and `replay-viewer/` returns nothing.
- No overlay in the band: the appended game block adds no fixed- or absolute-positioned element
  (the tell ribbon and the trump indicator are canvas draws, `renderer.js:421-467`, `:504-545`);
  `#modulechip` is a static child of `#topright`.
- **No `#viewpanel`**: `grep -rn viewpanel` over the repo returns nothing, and babel ships none —
  the card table is a fixed arena, which is also what licenses `--strict-text-bounds`.
- Real art: `data/` carries babel's `arena_floor.png`, the four `soldier_*_front.png` sprites and
  `font.ttf` + `FONT_LICENSE.txt`; cards are drawn as rounded rects with real rank/suit glyphs
  (`renderer.js:240-262`) and `RANKS[8] === "10"` (`:50-51`) — never `T`, asserted in
  `tests/test_cards.nim:12-17`.

**Tests, CI and release**
- `ci.yml:104-150` runs every `tests/*.nim` twice, debug and `-d:release`; the run log shows all
  five suites executed in both modes. `git log -p -- tests/` in the repo shows a single commit that
  **adds** 1496 lines of tests and deletes none, so nothing was disabled, skipped, widened or
  removed during this run (item 1's second half).
- `tools/ci/viewer_smoke.mjs` is byte-identical to the coworld-builder template; `docker_smoke.sh`
  differs from the template only in the three substitutions (`trick-taking`,
  `coworld-trick-taking`, `4`); both are committed 100755, as is
  `tools/build_replay_viewer.sh`.
- Placeholder gate: `grep -n 'trick-taking\|<IMAGE>\|<SEATS>' … | grep -E '<slug>|<IMAGE>|<SEATS>'`
  finds nothing, so the gate exits 0. The only surviving angle-bracket names are the four documented
  runtime values (`<cow_id>`/`<sha>` in `ci.yml:224`, `<run_id>` in
  `coworld-release.yml:21`/`coworld-submit.yml:17`, `<name>:vN` in `coworld-submit.yml:31`).
- `tools/ci/policies.json`: four distinct policies — `trick-taking-signaller` and
  `trick-taking-counter` with `PLAYER_PROMPT`, champion #2 carrying
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, plus `trick-taking-follow` and
  `trick-taking-tracker` with `PLAYER_SCRIPTED`. Asserted in `tests/test_manifest.nim:191-219`.
- `coworld-release.yml` order: build (`:159`) → certify (`:173`) → **upload-policies** (`:212`) →
  upload-coworld (`:310`) → secret put (`:348`); all three workflows are present.
- Item 7's legality half: `tests/test_bot.nim:88-103` plays **200 complete matches per baseline per
  module** (1600 episodes), asserting `reason == "complete"`, `handsScored == config.hands`, every
  move drawn from `legalMoves`, every bid in range, the oh-hell dealer never on the hooked value, a
  hearts pass always three distinct held cards, no seat acting out of turn and the actor walking
  clockwise inside a trick (`:69-74`).

---

## Could not determine

- **Whether the platform's upload contract wants a `players` array on each variant.** The design's
  variant table (design.md:1047-1052) has a `players[]` column reading "4 entries"; the shipped
  variants carry `game_config.players` with four entries and no variant-level `players` key. Every
  seat-count invariant item 6 names is about `certification.*`, and those are all present and
  correct. Settled by: a `coworld upload-coworld` dry run, or the platform's variant schema.
- **The real-world timing of the 429 cascade in N1.** The arithmetic is deterministic given the
  code, but the wall clock depends on how fast a throttled Bedrock call returns. Settled by: a live
  episode against a throttling endpoint, or a cap on `extraSpacingMs` making the question moot.
- **Whether `coworld certify` actually requires the `GET /client/replay` route** (N3). The design
  asserts it (design.md:746-757) and babel ships it, but I could not run the certifier from the
  sandbox. Settled by: the certifier's route list, or a certify run with the route removed.
