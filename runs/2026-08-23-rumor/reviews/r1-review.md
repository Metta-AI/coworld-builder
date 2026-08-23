# r1 review — rumor

Range: `b2c42ba..ed38e35` (whole repo history; 5 commits)
Repo: `/tmp/cogame-rumor` @ `ed38e35276c8ebcd052b8944795c2ec501239f7c`
Starter: `/workspace/starters/cogame-bullwhip` (read-only)
Design note: `/workspace/coworld-builder/runs/2026-08-23-rumor/design.md` (1051 lines)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST items 1–14 + the
simultaneous-decision addendum
Files read in full: 24 (`src/rumor.nim`, `src/rumor_player.nim`,
`src/rumor/{types,sim,llm,server}.nim`, `client/{renderer.js,chrome.css,global.html,
player.html,replay.html}`, `replay-viewer/{config.nims,index.html,static_replay.js,
rumor_replay.nim}`, `tests/{test_sim,test_bot}.nim`, `coworld_manifest_template.json`,
`tools/build_replay_viewer.sh`, `tools/ci/{docker_smoke.sh,policies.json}`,
`.github/workflows/{ci,coworld-release,coworld-submit}.yml`, `Dockerfile`,
`Dockerfile.replay-viewer`, `README.md`), plus byte-diffs against the starter for
11 of them and three CI artefacts/logs fetched from GitHub.

---

## Blocking

**None.** I traced every checklist item named in the brief and found nothing that
falsifies one. The observations below are all advisory; several are places where the
**code diverges from the design note** rather than from the checklist, and I have said
so explicitly in each.

---

## Non-blocking

### F1 — The event log's `scripted` flag does not mark an LLM seat that fell back to the baseline
- Where: `src/rumor/server.nim:297`; `src/rumor/llm.nim:611-614`; `src/rumor/types.nim:61`
- Observed: the server computes the flag it records on every `say`/`vote` event as
  ```nim
  let wasScripted = scripted[seat] != skNone or client.disabled
  ```
  (`server.nim:297`) — i.e. purely from the seat's registered `PLAYER_SCRIPTED` policy and
  from whether the client has no credentials at all. `Decision` (`llm.nim:43-50`) carries no
  provenance field, so when `decideAll` exhausts its retry and substitutes
  `scriptedAction(sim, seat, skGossip)` (`llm.nim:611-614`) the server has no way to know,
  and the resulting `evSay`/`evVote` is written with `scripted: false`
  (`sim.nim:584`, `sim.nim:615`). `types.nim:61` documents that field as "say/vote: decided
  by a scripted baseline", and `tableStateJson` re-exports it as `seats[i].scripted`
  (`sim.nim:740`).
- What the note says: design §Degrade, never hang (line 455) — "Each fallback logs
  `rumor llm: seat <n> falling back to scripted decision` on stdout." **That log is
  present and correct** (`llm.nim:613` emits exactly that string, for every seat still open
  after the retry batch). The belt-and-braces server-side rejection path also logs
  (`server.nim:307-308`).
- Checklist item 8: "…then falls back to the scripted move — and the fallback is recorded so
  phase 60 can count it." Observed: tolerant parse ✓ (`llm.nim:380-392`), retry exactly once
  ✓ (`llm.nim:574` `for attempt in 0 .. 1`), fallback ✓, and the fallback **is** recorded on
  stdout, which is the mechanism the design names. The gap is only that the *replay* does
  not carry it. Inference, not observation: phase 60 counting from the replay rather than
  from the container log would undercount.

### F2 — The replay re-derivation test asserts the frame count and the final frame, not every intermediate frame
- Where: `tests/test_sim.nim:461-480` (and `:531-541` for the deadline case)
- Observed:
  ```nim
  let frames = replayMatch(config, live.events)
  check frames.len == live.events.len + 1
  check $frames[^1].tableStateJson() == $live.tableStateJson()
  ```
  The intermediate frames are produced (`sim.nim:903-956`, one `result.add(sim)` per event)
  but are not individually compared against a live per-tick snapshot.
- Checklist item 2 also requires "the viewer derives its display from that same
  re-derivation — not from a parallel recording". That half is **structurally guaranteed**
  and traced: the replay payload written by the server carries only `events` and never
  `states` (`server.nim:132-156`); `states` is computed by `replayMatch` in the pod path
  (`server.nim:158-162, 514`) and by the same Nim `replayMatch` in the wasm path
  (`replay-viewer/rumor_replay.nim:36-40`); and `renderer.js:1309-1312` reads
  `states[min(index, states.length-1)]` for every drawn frame. There is no parallel
  recording anywhere in the tree to drift from.
- Also traced: `tests/test_sim.nim:512-529` proves the seeded re-derivation is *checked*
  against the record — a flipped `tally.truth` and a mutated `tally.clues[0]` both raise
  `RumorError` (`sim.nim:936-947`).

### F3 — The certification fixture ships `rounds: 3`; the design note says `rounds: 2`
- Where: `coworld_manifest_template.json:511`; design lines 831 and 904
- Observed: `"rounds": 3` in `certification.game_config`. Confirmed live in the
  docker-smoke log (`game=rumor seats=10 config={… "rounds": 3 …}`, run 32654839685,
  job 97231866292).
- What the note says: line 904 — `` `rounds`: 2 ``; line 831 — "The certification/smoke
  fixture (`rounds: 2`) logs 36 events ≈ 27 s".
- Observed contradiction inside the note itself: design line 522 specifies that `update`
  "raises `RumorError` on `rounds < 3`", and `MinRounds = 3` (design line 525). The shipped
  code implements that guard (`types.nim:122-123`, `sim.nim:323-325`), so a fixture with
  `rounds: 2` would be **rejected at config load**. The code's value is the internally
  consistent one; the note's is not. The shipped fixture logs
  `1 + 3×11 + 1 + 10 + 1 + 1 = 47` events, more playback than the note's 36, so the
  "outlasts the soak window" argument is unaffected.

### F4 — `ci.yml` invokes `viewer_smoke.mjs` without `--soak`
- Where: `.github/workflows/ci.yml:306-309`; design lines 1023-1026
- Observed: the step runs
  ```
  node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "${replay}" --timeout 90
  ```
  with no `--soak`. The uploaded `viewer-smoke.json` artefact from run 32654839685 shows
  `"soak": null`, confirming the soak assertion did not run.
- What the note says: design line 1023-1024 gives the command as `… --timeout 90 --soak 10`,
  and line 1026 says the job "passes only when … [it] keeps advancing through the 10 s soak".
- Note: `.github/workflows/ci.yml` is the coworld-builder template
  (`templates/ci.yml`) **byte-identical after the three documented substitutions** — I
  verified this by `sed`-substituting the template and diffing (empty diff). The template
  does not pass `--soak`, so this is the note describing something the scaffold does not do,
  not a repo edit. Checklist item 13 requires the step to have run and the bundle to have
  loaded, which it did (see "Traced and consistent").

### F5 — `client/chrome.css` is the starter's plus 54 appended lines; the note says "copied **unchanged**"
- Where: `client/chrome.css:469-519`; design line 782-783
- Observed: `diff` against `/workspace/starters/cogame-bullwhip/client/chrome.css` produces
  exactly one hunk, an append at the end of file. Lines 1–467 are **byte-identical** to the
  starter's. The addition sits under an explicit banner:
  ```
  /* ============================================================
     Rumor additions to the inherited cogame-bullwhip chrome.
     Everything above this banner is bullwhip's chrome.css,
     unchanged. …
  ```
  and adds five seat colours (`.seat5`–`.seat9`), a 5-column `#scorebug`, `.plate-belief`,
  `.beat-marker.vote`, a 7-column `.end-rows`, four feed classes, and two narrow-width
  media queries.
- What the note says: design line 783 — "`client/chrome.css` is copied **unchanged**."
- Against checklist item 14 this is the *blessed* shape (starter file + game block under a
  banner comment naming the starter), so I record it as a note/code mismatch only.

### F6 — Checklist §14's transport-rule identifiers do not exist in this starter lineage
- Where: `client/renderer.js`, `client/chrome.css`, `client/replay.html` (rumor);
  `/workspace/starters/cogame-bullwhip/client/*` (starter)
- Observed: `grep` for `relayout`, `--band`, `--hudscale`, `#endcard`, `markBeat`,
  `#viewpanel`, `zoomAt`, `setZoom`, `attachMinimap` returns **zero hits in both the
  starter and the repo**. There is no `client/chrome_common.js` and no
  `client/replay_broadcast.html` in cogame-bullwhip; the equivalents are
  `client/renderer.js` (the whole chrome + drivers, one file) and `client/chrome.css`.
  So §14's byte-diff target, `--band` relayout rule, `#endcard.on` rule, and
  `chrome_common.markBeat(tick, kind, team, label)` beat-buttons are written for the
  parley/hive/gridlock chrome, not for bullwhip's.
- What bullwhip has instead, and what I verified is preserved:
  - The end overlay is `#endscreen`, shown by `container.classList.toggle("show", !!show)`
    (`renderer.js:1001`), and **every seek dismisses it**: `setIndex` recomputes
    `index >= events.length && events.length > 0` and passes it to `updateEndscreen`
    (`renderer.js:1341-1342`), and the scrubber's `onSeek` calls `setIndex(next, true)`
    (`renderer.js:1298-1301`). Scrubbing back from the end therefore takes the endscreen
    down.
  - Beat markers are `<div class="beat-marker …">` created in `buildScrub`
    (`renderer.js:1237-1248`), positioned by event index; they are **not** labelled
    `<button>`s. They are children of the scrub container, whose `pointerdown` handler
    seeks by x-fraction (`renderer.js:1253-1266`), so a click on a marker does seek to its
    position. Every kind the page emits has a CSS rule: `.beat-marker`
    (`chrome.css:195`), `.beat-marker.death` for the tally (`chrome.css:204`),
    `.beat-marker.vote` (`chrome.css:503`), and `.seat0`–`.seat9`
    (`chrome.css:205-209`, `482-486`). No emitted kind is invisible.
  - No zoom bar / minimap exists in the starter, so nothing had to be removed; the graph
    stage fits the frame by construction (`renderer.js:143-171`).

### F7 — `/client/replay` exists as a pod route, page and manifest prose
- Where: `src/rumor/server.nim:477` (`result.get("/client/replay", htmlHandler("replay.html"))`);
  `client/replay.html`; `coworld_manifest_template.json:289` (the `game.protocols.global`
  text says "`/client/replay` plays a recorded episode")
- Observed: the string `/client/replay` occurs in those three places. It does **not** occur
  in `game.replay_viewer`, which is `{"bundle": "static-replay-viewer"}`
  (`coworld_manifest_template.json:16-18`).
- Starter parity: cogame-bullwhip has the identical route, the identical page, and the
  identical sentence in its own `protocols.global` value
  (`/workspace/starters/cogame-bullwhip/coworld_manifest_template.json:210`), and the design
  note lists `/client/replay` among the server's routes (design line 690) and in the global
  protocol text (design line 727).
- Checklist item 3 says "No `/client/replay` pod path anywhere." Surfacing it so the judge
  can rule on a strict versus intent reading; the operative facts are that the manifest
  declares the static bundle and that the static shell fetches nothing but the `?replay=`
  URL (`replay-viewer/static_replay.js:67-89, 127-150`).

### F8 — Captured LLM error text is byte-sliced, not rune-sliced (stdout only)
- Where: `src/rumor/llm.nim:388` (`head = head[0 ..< 160] & "..."`), `:428`, `:439`, `:442`,
  `:451` (`response.body[0 .. min(response.body.high, N)]`, `result[0 .. min(result.high, 160)]`)
- Observed: these are byte slices and can cut a multi-byte character. I traced every
  consumer: each is inside a `RumorError` message that is caught and only `echo`ed —
  `llm.nim:606-609` (`decideAll`) and `server.nim:306-308` (the belt-and-braces reject).
  **No path puts an error string into an event, a frame or the replay**: the rejection
  fallback writes the templated `scriptedAction` message and `""` notes
  (`server.nim:309-316`). Every string that *does* reach the replay goes through
  `trimRunes` (`sim.nim:478-483`, `runeSubStr`) or `cleanText` (`llm.nim:455-461`,
  `runeSubStr`).
- Starter parity: identical lines exist in
  `/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:321, 360, 369, 374, 383` —
  ported verbatim.
- Checklist item 9 names "captured errors" among the strings that must be rune-truncated.
  Observed: they are byte-truncated, but they do not reach the replay.

### F9 — `readClaim` accepts `"1"`/`"2"` for a talk `claim`, which the note only lists for `vote`
- Where: `src/rumor/llm.nim:493-496`
- Observed: `readClaim` (shared by `parseTalkReply` and `parseVoteReply`) maps
  `"a"|"1"|<optionA word>` → `A` and `"b"|"2"|<optionB word>` → `B`.
- What the note says: design line 402 lists the talk-turn `claim` spellings as
  `A`/`a`/option-A word, `B`/`b`/option-B word, and `none`/`""`/`null`/absent; line 403
  adds `1`/`2` only for the ballot `vote`. The code is a strict superset — more tolerant,
  never less. `"maybe"` still degrades to `"none"` (`llm.nim:497`, asserted at
  `tests/test_bot.nim:160-161`).

### F10 — `parseVoteReply` derives a missing `belief` as 75/25
- Where: `src/rumor/llm.nim:531-532`
- Observed: `let derived = if vote == "A": 75 else: 25` then `clamp(numberOr(…, derived), 0, 100)`.
- What the note says: design line 403's ballot row gives only "`belief`: 0–100, clamped" —
  no default is specified. The talk row's derivation rule (line 402) is implemented exactly
  (`llm.nim:505-511`, asserted at `tests/test_bot.nim:179-185`).

### F11 — The shipped baselines measure above the note's reference figures
- Where: `tests/test_bot.nim:74-91`; CI run 32654839685, job 97231866330
- Observed, from the test job's own echoes: `all-gossip honest accuracy over 500 seeds:
  0.698892857142857`, `all-herd honest accuracy over 500 seeds: 0.6571428571428574`,
  `clue accuracy over 1000 seeds: 0.6756`.
- What the note says: design lines 435 and 446 — gossip **0.682**, herd **0.621**; design
  line 141 — per-seat clue accuracy **67.6 %** (matched exactly).
- The test bands (`0.60 .. 0.78` and `0.55 .. 0.70`, `test_bot.nim:85-88`) accept both sets
  of numbers, and the qualitative claims survive: herd < gossip (`test_bot.nim:91`), and
  herd's 0.657 is still below the 0.675 ignore-the-network floor. `README.md:46-48` has been
  updated to the measured 0.69 / 0.63; the design note has not.

### F12 — `#clock` readouts differ from the note's wording
- Where: `client/renderer.js:923-957` (`matchHeader`)
- Observed the three branches: `truth` set → `"TRUTH — <word> · HONEST n/m · x <A> · y <B>"`;
  `phase == "ballot"` → `"SEALED VOTE · WAITING ON n"` / `"BALLOTS IN"`; otherwise
  `"ROUND n / m · WAITING ON k"` / `"MESSAGES IN"`. Confirmed live in the viewer-smoke
  artefact: `"ROUND 1 / 3 · WAITING ON 10"` at 0 %, `"ROUND 3 / 3 · WAITING ON 10"` at 50 %,
  `"TRUTH — BARRED · HONEST 6/8 · 3 OPEN · 7 BARRED"` at 100 %.
- What the note says: design line 808 also asks for a distinct tally-frame string
  `TALLY — 6 BROKEN · 4 SOUND`. There is no separate tally readout; the tally and final
  frames both take the `truth` branch, which carries the same vote split at the end of the
  line. Everything is words and numerals, never `"A"` (`renderer.js:129-133`).

### F13 — The truth stamp is drawn on the canvas, not via `#lightpool`
- Where: `client/renderer.js:592-612` (`drawTruthStamp`), called from `draw` at `:228-230`
- Observed: the truth word is filled onto the 2-D context in amber with a subtitle
  `"THE TRUTH · HONEST n / m"`. `#lightpool` still exists in the pages and in
  `chrome.css` but is not driven by the reveal.
- What the note says: design line 805 — "the truth word is stamped across the middle of the
  stage by the existing `#lightpool` spotlight."

### F14 — Three `Sim` fields are not in the note's type listing
- Where: `src/rumor/sim.nim:86` (`ballotBelief`), `:88` (`scriptedSeat`), `:94` (`deadlineStop`)
- Observed: all three are load-bearing for behaviour the note *does* specify —
  `ballotBelief` feeds `beliefSeries`' tally point (`sim.nim:698-699`) and the revealed
  belief (`sim.nim:711`); `scriptedSeat` feeds `seats[i].scripted` in the documented
  `tableStateJson` (design line 597); `deadlineStop` selects `reason`
  (`sim.nim:491`).
- What the note says: design lines 540-566 list the `Sim` fields without these three.

### F15 — The player container's receive loop is an unbounded blocking read
- Where: `src/rumor_player.nim:63-64` (`while true: let received = socket.receiveMessage()`)
- Observed: no timeout on `receiveMessage`. The loop exits on `isNone` (clean close), on a
  `final` frame (`:81-83`), or on any `CatchableError` (`:88-89`), after which the process
  `quit(0)` (`:94`). The game always sends `final` and then quits
  (`server.nim:194-196, 199-213`), so the wait terminates in practice.
- Starter parity: bullwhip's loop is the same read with **no** try/except; the guard and
  the explicit `quit(0)` are rumor's addition, exactly as design lines 472-476 require
  (raid 0.1.3 → 0.1.4).
- Checklist item 5 says "no unbounded loop or blocking read". This is one, in the *player*
  container, inherited from the starter and bounded in practice by the game's lifecycle;
  the game container has no such wait. Recording it rather than judging it.

### F16 — `update()` does not reject `rounds > MaxRounds`
- Where: `src/rumor/types.nim:122-123` (only `rounds < 3` raises)
- Observed: an over-large `rounds` is silently clamped later by `sampleEpisode`
  (`sim.nim:124-125`, asserted at `tests/test_sim.nim:578-580`), and the manifest's
  `config_schema` caps it at 6 (`coworld_manifest_template.json:80-86`).
- What the note says: design line 522 lists the `update` rejections and names only
  `rounds < 3`, so this matches the note; recorded because it is the one config path where
  an out-of-range value degrades rather than raising.

### F17 — An unreachable double-raise in the server's fallback path is uncaught
- Where: `src/rumor/server.nim:298-316`
- Observed: the `except RumorError` handler itself calls `applyVote`/`applyMessage`
  (`:311-316`) outside any `try`. If the *outer* rejection had been "has already spoken this
  round" (`sim.nim:561-563`) the inner call would raise the same error and escape `runGame`,
  killing the game thread while mummy keeps serving.
- Reachability (inference, not observed): `seats` is taken from `pendingSeats()` under the
  lock (`server.nim:277`), only this thread mutates the sim, and each seat appears once per
  turn, so the "already acted" precondition cannot hold. The design calls this handler
  "unreachable after the pre-checks; a belt-and-braces guard" (design line 465).
- Starter parity: identical shape at
  `/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:305-309`.

---

## Traced and consistent

**Resolution rules — `src/rumor/sim.nim`**
- `initSim` (`:319-375`) draws in exactly the note's fixed order (design lines 74-127):
  proposition `:333`, truth `:338`, saboteur count `:340`, roles `:344-355`, topology family
  `:357-360`, node order `:362-363`, edges `:364`, clues `:367`. Pinned `saboteurs` (`:341`)
  and `topology` (`:358`) override **after** their draw, so the stream never shifts —
  asserted for all four families at `tests/test_sim.nim:153-171`.
- Topology sizes match the note: `ring` 10-cycle + 3 chords = 13 (`:178-188`), `smallworld`
  1- and 2-hop = 20 with 2 connectivity-checked rewires that preserve the count
  (`:190-210`), `clusters` 2×(5-cycle + one chord) + exactly one bridge = 13 (`:212-220`),
  `hub` triangle + 7 nodes × 1-or-2 links = 10..17 (`:222-237`). `buildEdges` (`:239-256`)
  redraws up to 100 times on a disconnected result and falls back to a plain ring. Asserted
  over 200 seeds × 4 families at `tests/test_sim.nim:61-94`, and "exactly one bridge" by
  edge-removal at `:96-107`.
- `drawClues` (`:258-277`): 60 % reliability (`rng.rand(99) < SignalReliabilityPercent`),
  redrawn up to `ClueDrawAttempts = 200` until the margin is in `{2,4,6}`, with the
  deterministic 6/4 fallback. Asserted over 1000 seeds at `tests/test_sim.nim:110-129`
  (measured 0.6756 vs the note's 0.676).
- `Propositions` (`:45-54`): 8 entries, all 16 answer words disjoint from `CogNames` —
  asserted at `tests/test_sim.nim:131-136`.
- Round order: `openRound` = `deliverInboxes` → `clearSay` → `phTalk` → `evRound` with
  `text = "final round"` on the last round (`:300-308`); `applyMessage` normalises the claim,
  clamps `confidence`/`belief` to 0..100, one-lines and rune-truncates the message to 240,
  rune-truncates notes to 600, appends `evSay`, and resolves the round on the tenth
  (`:550-587`); `openBallot` (`:310-317`) emits `evRound` at `round = config.rounds`;
  `applyVote` (`:589-618`) seals, appends `evVote`, and the tenth calls `resolveBallot`.
- `deliverInboxes` (`:288-298`) delivers one entry per neighbour that spoke, one hop, one
  round later. Asserted at `tests/test_sim.nim:174-198` (neighbours only, next round only,
  no self-delivery, inbox clears).
- Sealing/masking: `tableStateJson` (`:701-788`) returns `role: "cog"`, `vote: null`,
  `sealed: true`, `truth: ""`, `verdict: ""`, `accuracy: -1.0`, `honestCorrect: -1`,
  `saboteurCount: 0` on every pre-tally frame, and fills all of them in once
  `unmasked()` (`:691-692`). Asserted frame-by-frame across a whole episode at
  `tests/test_sim.nim:230-275`.
- Scoring (`:407-427`) is the note's formula verbatim, including the
  `honestNeighbours == 0 → 1 - A` branch. `tests/test_sim.nim:302-366` reproduces the
  note's worked table at A = 1, 0.75, 0.5, 0 to 1e-9 and checks every score is in [−1, +1];
  `:389-397` checks `verdict == "split"` on 5–5; saboteur votes are excluded from `A` by
  construction (`:502-505` iterates `sim.honestSeats` only).
- Endings: exactly two `reason` values. `forceBallot` (`:628-643`) keeps cast votes and
  gives every remaining seat the scripted gossip vote, then tallies and scores normally;
  `endEarly` on a settled sim is a no-op (`:645-649`). Asserted at
  `tests/test_sim.nim:399-428`.

**Decision path — `src/rumor/llm.nim`**
- **One parallel batch per turn** (the simultaneous-decision addendum): `decideAll`
  (`:548-614`) builds a single `RequestBatch` over all open seats (`:585-593`) and issues
  one `client.curl.makeRequests(batch, client.timeoutSeconds)` (`:594`). The retry is a
  second, smaller batch over the same code path. There is no per-seat request loop anywhere
  in the file. `server.nim:289` calls it once per turn, outside the lock, on a snapshot.
  A default episode is 6 dispatches (plus at most 6 retries), not 60.
- Tolerant parse: `extractJsonObject` (`:380-392`) takes the first `{` to the last `}`,
  which accepts prose and markdown fences — asserted at `tests/test_bot.nim:222-226`.
- Retry exactly once: `for attempt in 0 .. 1` (`:574`), with the hint
  `"Your previous reply was invalid. Respond with ONLY the requested JSON object."`
  appended on attempt 1 (`:589-591`).
- "Invalid" is exactly the note's definition: `parseTalkReply` raises only when the claim is
  `none` **and** the message is empty (`:516-518`); `parseVoteReply` raises only when there
  is no parsable vote (`:522-527`). Everything else clamps or defaults
  (`:503-514`, `:528-534`). Asserted at `tests/test_bot.nim:146-220`.
- `applyProbe` (`:538-546`) legality-checks each decision against a copy of the sim before
  accepting it, so an illegal reply is retried rather than crashing the turn.

**Waits and their bounds (checklist item 5)**
- Player connect: `while epochTime() < deadline` with `sleep(200)`, `deadline = gameStart +
  playerConnectTimeoutSeconds` (120 s) and an early break once all sockets are in
  (`server.nim:219-227`).
- Rate governor: `spaceBatch` (`llm.nim:151-165`) sleeps at most
  `MinBatchSpacingSeconds = 26` s (`sim.nim:28`) and, on the first batch of the episode,
  not at all (`:158-160`). It is only reached for batches that are actually dispatched
  (`llm.nim:575, 584`), so a credential-less run never sleeps — asserted at
  `tests/test_bot.nim:112-136` (`elapsed < 500` ms for all ten seats).
- LLM call: bounded by `client.timeoutSeconds` = `llmTimeoutSeconds` = 25
  (`types.nim:81`, `llm.nim:594`).
- Turn budget: the retry is dispatched only when
  `elapsed + MinBatchSpacingSeconds + timeoutSeconds <= TurnBudgetSeconds`
  (`llm.nim:578-583`), which is the note's inequality exactly. Traced worst case: attempt 0
  costs ≤ 26 + 25 = 51 s; the retry gate admits only `elapsed ≤ 29`; the retry then costs
  ≤ 26 + 25; so a turn is bounded by 80 s.
- Round barrier: there is none — `decideAll` always returns one `Decision` per seat
  (`llm.nim:565, 611-614`), so the server never waits on a seat reply.
- Play deadline: checked **before** each batch, under the lock
  (`server.nim:271-276`), at `gameStart + PlayBudgetFraction × timeoutSeconds` with
  `PlayBudgetFraction = 0.6` (`sim.nim:30`) and `timeoutSeconds` from
  `COWORLD_TIMEOUT_SECONDS` else `config.episodeTimeoutSeconds` = 1200
  (`server.nim:243-249`). Past it: `forceBallot()`, broadcast, break.
- **The 720 s / 1200 s bound.** `sampleEpisode` (`sim.nim:114-128`) computes
  `budget = 0.6×1200 − 120 = 600`, `maxTurns = int(600/80) = 7`,
  `cap = max(3, min(6, 6)) = 6`, `rounds = max(3, min(5, 6)) = 5`; it is idempotent
  (`:119-120`) and is called once, after the seed is settled (`src/rumor.nim:42`).
  Worst case = 120 (connect) + 6 × 80 (turns) + 6 × 0.4 (pacing) + 0.5 + artifacts + 20
  (`ShutdownGraceMs`, `server.nim:40, 211`) ≈ 623 s < 720 s. The **scoring** happens at the
  tally, before `finishEpisode`, so the episode settles and scores well inside the bound.
  `tests/test_sim.nim:584-588` asserts
  `playerConnectTimeout + (rounds+1) × TurnBudgetSeconds < 0.6 × episodeTimeoutSeconds`.
  Measured in CI: the real docker-smoke episode ran 17:27:22 → 17:27:43 (≈ 21 s, of which
  20 s is the deliberate shutdown grace).
- No credentials ⇒ `client.disabled = true` (`llm.nim:146-149`) and every seat plays gossip
  with no network and no sleep (`llm.nim:568-572`).

**String truncation on rune boundaries (checklist item 9)**
- `sim.trimRunes` (`sim.nim:478-483`) and `llm.cleanText` (`llm.nim:455-461`) both use
  `runeSubStr`. Applied to: `message` 240 (`sim.nim:565`), `notes` 600 (`:575`, `:607`),
  vote `reason` 200 (`:603`), reply `message`/`notes`/`reason` (`llm.nim:512-514, 533-534`),
  and the delivered player **prompt** 4000 runes (`server.nim:446-447`, `runeSubStr`).
- `tests/test_sim.nim:430-458` feeds `"日"×400` / `"日"×900` and checks the caps, plus
  `validateUtf8() == -1` on every event's `text`, `notes` and serialised JSON and on the
  whole event array, then re-parses it. `tests/test_bot.nim:191-198, 216-220` do the same
  through the reply parsers. The docker-smoke script additionally decodes the produced
  replay as strict UTF-8 (`SMOKE_REQUIRE_REPLAY_JSON=1`) — green in run 32654839685.

**Replay writer and re-derivation**
- `replayPayload` (`server.nim:132-156`) writes `protocol: "rumor.replay.v1"`, alias `names`,
  `policyNames`, `config{rounds, seed, topology, saboteurs, sampled}`, `events`, `results` —
  exactly the note's payload (design lines 642-655). No `states` are recorded.
- `configFromReplay` (`server.nim:486-496`) sets `sampled = true` so a re-read replay is
  never re-fitted, and seats the players from the recorded aliases; `tableNames`
  (`sim.nim:101-112`) redraws the same aliases from the seed, so the re-derived table
  matches. `rumor_replay.nim:26-34` does the identical thing on the wasm side.
- `replayMatch` (`sim.nim:903-956`) replays `say`/`vote` through the real rules, validates
  each recorded `round` number against the re-derivation (`:923-927`), handles a recorded
  forced ballot (`:918-922`), and raises on a tampered `truth`, `clues` or `roles`
  (`:936-947`). `frames.len == events.len + 1`.

**Manifest (checklist items 3, 6, 10)**
- `game.replay_viewer = {"bundle": "static-replay-viewer"}` (`:16-18`).
- `num_agents: 10` in `variants[0].game_config` (`:423`), `variants[1].game_config`
  (`:467`) **and** `certification.game_config` (`:509`); `config_schema.num_agents` is
  `integer, minimum 10, maximum 10` (`:70-75`).
- `tools/ci/docker_smoke.sh` carries `seats_expected="${SMOKE_SEATS:-10}"` (`:54`) and the
  four invariants with `SEAT-COUNT FAIL:` messages at `:113, :123, :131, :138` plus the
  `SMOKE_SEATS` cross-check at `:148`. I fetched the docker-smoke job log
  (job 97231866292, 163 KB) and grepped it: **zero occurrences of `SEAT-COUNT FAIL`**; the
  log ends `smoke OK: seats=10 results=656B replay=7561B reason=complete`.
- `game.docs` is `{"readme":{"type":"text","value":…},"pages":[{"id","title",
  "content":{"type":"text","value":…}}]}` with `rules.md` and `scoring.md` (`:292-315`).
- `game.protocols` carries **both** `player` (`:283-286`) and `global` (`:287-290`).
- `$schema` (`:2`), `episode_timeout_minutes: 20` (`:3`), 8 `tags` (`:4-13`),
  `runnable.type: "game"` (`:22`), `image: {{RUMOR_IMAGE}}` matching
  `compose.yaml`'s `rumor`/`coworld-rumor:latest`, `owner: daveey@gmail.com` (`:20`),
  `env.ANTHROPIC_API_KEY_URI = "secret://coworld/rumor/anthropic_api_key"` (`:28`).
- `results_schema` requires all 19 fields with `additionalProperties: false`; `resultsJson`
  (`sim.nim:653-687`) emits exactly those 19 keys, `scores` in [−1, 1], `accuracy` ≥ 0
  (`max(sim.accuracy, 0.0)`, `:678`). Asserted at `tests/test_sim.nim:544-567`.
- Three `player` runnables (`rumor-player`, `rumor-gossip`, `rumor-herd`); `certification.players`
  is ten entries seating each of them at least once (`:517-548`).

**Static viewer, and it executes (checklist items 3, 13)**
- All four viewer files come from bullwhip and only from it. `diff` against the starter
  shows renames only: `config.nims` (5 changed lines), `index.html` (5), `static_replay.js`
  (8), `rumor_replay.nim` (rename plus the `weeks/talk` → `rounds/topology/saboteurs` config
  read).
- **MODULARIZE / EXPORT_NAME pairing.** `replay-viewer/config.nims:38-39` sets
  `-s MODULARIZE=1 -s EXPORT_NAME=RumorReplayModule`; `static_replay.js:138` calls the
  factory `RumorReplayModule()` and awaits the promise. Same starter, matched pair — not
  the lantern deadlock. `EXPORTED_FUNCTIONS` (`config.nims:41`) lists
  `_rm_load_replay,_rm_payload_ptr,_rm_payload_len,_rm_error_ptr,_rm_error_len`, and
  `rumor_replay.nim:22, 56, 61, 66, 71` exports exactly those five names, all consumed at
  `static_replay.js:94-104`.
- Load markers: `data-replay-loaded="true"` is set at `renderer.js:1373`, inside
  `attachReplay`'s `makeRenderer` callback and after the animation-frame IIFE has run its
  first `renderer.draw(view)` (`:1346-1371`) — i.e. on the first drawn frame.
  `data-replay-error=<message>` is set by `fail()` at `static_replay.js:56` and removed on a
  successful load (`:107`) and at retry (`:134`). Both markers come from the shell's own
  code. The 20 s fetch bound is `FETCH_TIMEOUT_MS` with an `AbortController`
  (`static_replay.js:14, 67-89`).
- **The bundle runs.** `ci.yml`'s `wasm-viewer` job has `needs: docker-smoke` (`:212`) and
  its step 11, `Load the bundle in a real browser`, is present, not
  `continue-on-error`, and concluded `success` (GitHub API,
  `repos/Metta-AI/cogame-rumor/actions/jobs/97232027026`). I downloaded the `viewer-smoke`
  artefact from run 32654839685:
  ```json
  {"loaded": true, "ms": 282,
   "signals": {"data_replay_loaded": "true", "data_replay_error": null,
               "bridge": ["loading","ready"], "bridge_ready": true, "bridge_error": []},
   "scrub": [{"at":"0%","clock":"ROUND 1 / 3 · WAITING ON 10"},
             {"at":"50%","clock":"ROUND 3 / 3 · WAITING ON 10"},
             {"at":"100%","clock":"TRUTH — BARRED · HONEST 6/8 · 3 OPEN · 7 BARRED"}],
   "failure": null}
  ```
  Three distinct clock readouts, no error, 83 feed lines. File presence is not what I am
  relying on here; `loaded: true` is.
- `tools/build_replay_viewer.sh` exists, is committed `100755` (`git ls-files -s`), and
  `mkdir -p`s the output parent **before** the containment check (`:23-25`, the ecos fix).
  It copies all ten cog sprites plus the floor and font (`:59-66`). `ci.yml:225-236` asserts
  the exec bit and invokes it by path.
- `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (empty `diff`).

**Chrome provenance (checklist item 14)**
- `client/chrome.css` lines 1–467 byte-identical to the starter's (single append hunk; see F5).
- `client/global.html`, `client/player.html`, `client/replay.html` differ from the starter's
  only in the title, the wordmark, the clock placeholder and the `BullwhipRenderer` →
  `RumorRenderer` global — nothing structural removed.
- `client/renderer.js` is 1383 lines against the starter's 1400 — not a fraction of it.
  Every chrome function the note lists survives with the same name and arity:
  `bindFeedToggle` (`:1062`), `renderFeed` with round-grouped `blockHead` (`:784, :793`),
  `buildScrub` with round spans, separators, per-event beat markers and pointer
  drag-to-seek (`:1204-1281`), `matchHeader` (`:923`), `updateScorebug` (`:959`),
  `updateEndscreen` (`:999`), `makeNameMap`/`applyNames` (`:699, :725`), `makeEffects`
  (`:885`), `attachLive` (`:1133`), `attachReplay` with the dwell-timed pacing loop
  (`:1283-1375`). Only the canvas stage (`:143-687`) is new, which is what the note says.
- `escapeHtml` is applied to every model-authored string before it enters `innerHTML`
  (`:820, :824, :837, :849, :968, :1050-1056`).

**Both name spaces (checklist item 4)**
- Agents see aliases only: `systemPrompt`/`userPrompt` render `sim.names[…]`
  (`llm.nim:247, 249, 329, 356`); `playerStateJson` renders neighbour, crew and inbox
  **aliases** (`sim.nim:794-817`); `tests/test_bot.nim:229-266` asserts the prompt contains
  the seat's own clue, its neighbours' aliases and its inbox, and **not** any non-neighbour's
  message, any other seat's role, or a truth marker.
- Viewer maps aliases → policy names: `makeNameMap` (`renderer.js:699-723`) builds both a
  per-seat map and a word-boundary regex that rewrites aliases **inside message text**
  (`:718-720`), leaving `Baseline`-labelled fillers on their aliases (`:695-697`). Fed from
  `payload.policyNames` in replay (`:1291`) and `latest.policyNames` live (`:1156`);
  `snapshotJson` and `replayPayload` both attach `policyNames`
  (`server.nim:94, 145`). Results attribute by policy name (`sim.nim:662`), asserted at
  `tests/test_sim.nim:565-567`.

**Legible at 360 px (checklist item 11)**
- `chrome.css:280-292`: `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` — inherited
  from the starter, unmodified.
- `chrome.css:460-464`: `@media (max-width: 640px) { .plate-label { display: none; } … }`.
- Stage compaction below 560 px: bubbles dropped and name plates cut to six characters
  (`renderer.js:64, 359, 380`), coins/meters/edges/pulses kept full size.

**Release order and scaffold (checklist item 12)**
- All three workflows present and **byte-identical to the coworld-builder templates after
  the three documented substitutions** (`<slug>`→`rumor`, `<IMAGE>`→`coworld-rumor`,
  `<SEATS>`→`10`): I `sed`-substituted each template and `diff`ed — all three empty.
  `tools/ci/docker_smoke.sh` likewise.
- `coworld-release.yml` step order: Build the Coworld manifest (`:153`) → Certify locally
  (`:167`) → Upload the policies (`:206`) → Upload the Coworld (`:304`) → Put the Coworld
  secret (`:342`).
- `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both mode `100755`.
- `tools/ci/policies.json` defines four policies: two `PLAYER_PROMPT` champions
  (`rumor-corroborate`, `rumor-skeptic`) and two `PLAYER_SCRIPTED` fillers
  (`rumor-gossip`, `rumor-herd`); champion #2, `rumor-skeptic`, carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`:24`).
- Placeholder gate run verbatim: exits 0. The only surviving angle-bracket names are the
  four documented runtime values — `<cow_id>`/`<sha>` at `ci.yml:202`, `<run_id>` at
  `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` at
  `coworld-submit.yml:31`.

**CI green, no test loosened (checklist item 1)**
- `gh run list -R Metta-AI/cogame-rumor --branch main -w ci.yml`: run **32654839685**,
  conclusion **success**, on `ed38e35`, 2m57s. Jobs: `docker-smoke` ✓ (97231866292),
  `test` ✓ (97231866330), `wasm-viewer` ✓ (97232027026).
- `git log --stat -- tests/` shows a single commit, `db9d644`, adding
  `tests/test_bot.nim` (+276) and `tests/test_sim.nim` (+588). `git log -p -- tests/`
  contains no other hunk: **no test file has been modified, weakened, skipped or removed**
  in this run. No `skip`, `t.Skip`, `xfail` or `--skip` appears in either file.
- The test job log shows all 12 `test_sim` and 10 `test_bot` cases `[OK]` in **both** the
  debug and the `-d:release` pass.

**Baseline plays full episodes legally (checklist item 7)**
- `tests/test_bot.nim:46-72`: 2 baselines × 4 topologies × 4 seeds; every episode reaches
  `sim.done`, `sim.reason == "complete"`, `roundsPlayed == config.rounds`,
  `says == rounds × 10`, `votes == 10`, in under 2000 ms, with a per-decision audit
  (`:29-37`) asserting `claim ∈ {A,B,none}`, `confidence ∈ 0..100`, `belief ∈ 0..100`,
  `vote ∈ {A,B}`, `message` non-empty and ≤ 240 runes, `notes`/`reason` empty. Both roles
  occur in every run because `initSim` always deals 2–3 saboteurs.
- `tests/test_bot.nim:93-109` proves the echo rule: five repeats of the same neighbour's
  claim move `gossipLogOdds` exactly once (`firstClaims`, `sim.nim:431-439`).

**Packaging**
- `Dockerfile`, `Dockerfile.replay-viewer`, `compose.yaml`, `rumor.nimble` are bullwhip's
  with names changed only; `nimby.lock` is **byte-identical** to the starter's.
- `data/` carries the starter's four sprites plus six committed recolours
  (`soldier_{violet,orange,teal,rose,lime,sand}_front.png`) and
  `tools/make_cog_palette.py`; `renderer.js:34-47` grows `COLORS`/`COLOR_HEX` to the ten
  hexes the note lists.

---

## Could not determine

- **"The baseline's parameters were tuned with a grid harness, not guessed"**
  (checklist item 7, second sentence). No tuning or sweep harness is committed:
  `grep -rn "grid\|harness\|tune\|sweep"` over `*.nim`, `*.py`, `*.sh`, `*.md` (excluding
  `docs/plans/`) returns nothing, and `tools/` holds only `build_replay_viewer.sh`,
  `ci/`, and `make_cog_palette.py`. What the tree *does* contain is a measurement gate —
  `tests/test_bot.nim:74-91` runs 500 seeds per baseline and asserts the band
  `0.60..0.78` / `0.55..0.70`, echoing the rate so drift shows in the log — and the design
  note's own reference figures (design lines 141-143, 435, 446). **What would settle it:**
  a committed sweep script (or a recorded transcript of one) showing the log-odds weights
  `ClueLogOdds`/`ClaimLogOdds` (`sim.nim:56, 59`) and the herd constants were selected
  across a parameter grid, rather than derived analytically from `ln(0.6/0.4)` and
  `ln(0.56/0.44)` — which is what the code comments claim they are.
- **Whether the note's 0.682 / 0.621 baseline figures or the measured 0.699 / 0.657 are
  the intended targets** (F11). The tests accept both. Settled by re-running the design's
  6,000-seed reference model against the shipped `scriptedAction`, or by the note being
  updated to the measured values as `README.md:46-48` already was.
- **The retry-once network path end to end.** No test exercises a real transport failure →
  retry batch → fallback, because it needs credentials and a fault injector. The code path
  is traced above (`llm.nim:574-614`) and the *no-credentials* branch is tested
  (`tests/test_bot.nim:112-136`), but the retry itself is untested. **What would settle
  it:** a stub `LlmClient` transport, or a hosted episode's log showing a
  `attempt 0 failed` line followed by a successful attempt 1.
- **Whether a strict reading of checklist item 3's "No `/client/replay` pod path anywhere"
  is meant to catch the starter's inherited route and the manifest prose** (F7). The
  facts are recorded; the ruling is the judge's.
