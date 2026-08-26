# r1 review — liars-dice

Range: `80e72f5..23da0888e90cc3c57ef7c901811fca488749d62e` (whole history; the repo was created
this run — `0c5587c` is the 0.1.0 drop, `23da088` only adds two `.gitignore` lines)
Repo read at: `/tmp/cogame-liars-dice` @ `23da088`
Starter diffed against: `/workspace/starters/cogame-babel`
Files read: 31 in-repo + 7 starter files diffed + 2 CI job logs + the `smoke-replay` artifact
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15)

Note on the brief's file names: this repo is the **babel lineage**, which has no
`client/chrome_common.js` and no `client/replay_broadcast.html`. The design note states the
mapping at design.md:603–611 — `chrome_common.js` → `client/renderer.js` + `client/chrome.css`,
`replay_broadcast.html` → `client/replay.html` + `replay-viewer/index.html`. I diffed those four
files against the starter instead and applied checklist 14's *rule* unchanged; results are under
"Traced and consistent".

---

## Blocking

### B1 — The viewer draws LLM-authored text (`say`, `notes`) and the repo ships no worst-case renderer fixture; the only replay CI ever loads contains zero of that text

- Where:
  - `client/renderer.js:329-332` (speech plate), `client/renderer.js:379-380` (notes parchment),
    `client/renderer.js:894-908` (feed `say` / `notes` lines)
  - `tools/ci/docker_smoke.sh:194-199` (no `ANTHROPIC_API_KEY` ⇒ scripted baselines)
  - `src/liars_dice/llm.nim:172-232` (`scriptedAction` sets neither `say` nor `notes`)
  - `.github/workflows/ci.yml:293-318` (the *only* `viewer_smoke.mjs` step, run against
    `dist/smoke/replay.json`)
- Observed, step by step:
  1. `renderer.js:329` — `if (view.talk !== false && seat.say) drawSpeech(...)`. `seat.say`
     originates in `tableStateJson`'s `"say": sim.lastSay(slot)` (`sim.nim:607`), which is the
     model's own text truncated to `MaxSayLen = 140` (`sim.nim:27`, `sim.nim:129-130`).
  2. `renderer.js:379-380` — `drawParchment(..., seat.notes || "", ...)`; `notes` is the model's
     own text capped at `MaxNotesLen = 400` (`sim.nim:28`, `sim.nim:132-133`).
  3. `docker_smoke.sh:198` prints `no ANTHROPIC_API_KEY: the game must complete on its scripted
     baselines`; the CI log confirms it (job 98262244785, line 1936). With no credentials
     `newLlmClient` latches `disabled` (`llm.nim:144-147`) and every decision is
     `scriptedAction`, which returns a `Decision` whose `say`/`notes` are the zero-value empty
     strings (`llm.nim:172-232` never assigns them).
  4. I downloaded the actual `smoke-replay` artifact of run 32994991825 and parsed it:
     13 events, **0 events with `say`, 0 events with `notes`**, `reason: complete`, 3 deals.
  5. The `wasm-viewer` job's `canvas_text` line therefore covers only nameplates, points,
     die numerals, the bid plate, the verdict banner and the `NO NOTES YET` placeholder:
     `canvas text: 2487 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`
     (job 98262880977, 2026-08-26T17:40:04Z).
  6. There is no second `viewer_smoke.mjs` step in `ci.yml`, no fixture page anywhere in the
     tree (`ls client/` → `chrome.css global.html player.html renderer.js replay.html`; the
     starter's `client/fixtures/` directory was **not** carried over), and no
     `data-replay-loaded` setter other than `renderer.js:1447`.
- Checklist item: 15, final bullet — "A repo whose viewer draws LLM-authored text must therefore
  ship a **worst-case renderer fixture**: a page that loads the real `client/renderer.js`, hands
  it a frame built to hurt (a full-cap remark on *every* seat at once, …), renders it at several
  canvas sizes, sets `data-replay-loaded`, and is driven by `viewer_smoke.mjs
  --strict-text-bounds` in its own `ci.yml` step. … a repo that draws model text and has no such
  fixture is a blocking `legibility` finding."
- Why blocking: the entire speech-plate / notes-parchment / `.feed-say` code path — the only
  chrome that exists to show what a model said — is executed by zero gates in this repo. The
  green `canvas_text` line above is evidence about a text-free replay, not about the game the
  league will actually run. This is the cogchemists 2026-08-24 shape verbatim.
- Design note position: the note does not mention a renderer fixture at all. design.md:845-858
  lists only `docker-smoke` and `wasm-viewer` as the end-to-end/viewer tests.

### B2 — The reserved speech and notes bands are sized by eye, not from the server's caps; a full-cap remark will be ellipsized to roughly half

- Where: `client/renderer.js:132-142` (`SEAT_BASE = 84`, `NOTE_LINES = 3, NOTE_LINE_H = 12`,
  `SAY_LINES = 2, SAY_LINE_H = 12`), `client/renderer.js:146-166` (`seatBlock`),
  `client/renderer.js:501-524` (`drawSpeech`), `client/renderer.js:569-590` (`wrapLines`)
- Observed: the band **is** reserved unconditionally — `seatBlock` returns
  `above: size * 0.62 + sayHeight(scale)` (`renderer.js:162`) and
  `below: … + noteHeight(scale, noteLines)` (`renderer.js:163-164`) whether or not the seat is
  speaking, and `computeLayout` clamps every seat spot so the whole block fits
  (`renderer.js:204-213`); `drawSpeech` additionally clamps its own rect inside the canvas
  (`renderer.js:506-507`). Nothing is drawn off-frame. **But** the band's *capacity* is fixed at
  `SAY_LINES = 2` lines of `block.w` and `NOTE_LINES = 3` lines, and neither constant is derived
  from `MaxSayLen`/`MaxNotesLen` — those constants appear nowhere in `renderer.js`
  (`grep -n "MaxSay\|140\|400" client/renderer.js` → no cap-derived sizing).
  When the text does not fit, `wrapLines` (`renderer.js:583-588`) truncates to `maxLines` and
  ellipsizes the last one.
- Arithmetic (**inferred** — depends on the real `rajdhani` metrics, which I cannot measure in
  this sandbox): at a 960×~500 canvas, `size ≈ 84`, `scale ≈ 1`, `die = max(11, 84*0.34) = 28.6`,
  `handW = 5*(28.6+4)+8 = 171`, so `block.w = max(159.6, 171) = 171 px`. `drawSpeech` uses
  `w - pad*2 = 161 px` at `max(9, round(10.5*scale)) = 11 px`. At a typical condensed-face
  advance of ~0.42 em that is ~35 characters per line, ~70 characters over the two lines,
  against a server cap of **140**. The notes parchment gets ~105 characters against a cap of
  **400**. Below 480 px wide the parchment drops to 1 line (`renderer.js:153`), ~35 characters.
- Checklist item: 15, bullets 2 and 3 — "Any text laid out **relative to another element** — a
  speech bubble over a cog … — gets a **reserved band in the layout**, sized from the cap the
  server enforces on that string (`MaxSayLen` and its kin) and measured in the font it will be
  drawn in. Sizing by eye … is the bug above." and "Ellipsis is a design choice for **labels** …
  and a defect for **sentences**. If `ellipsized` counts a remark rather than a nameplate, the
  box is too small — widen the band, do not shorten the text."
- Why blocking: the ellipsis is on a *sentence* (the model's remark and its notes), not on a
  label, and the band is not derived from the cap. Because of B1 nothing in CI ever draws one of
  these strings, so `ellipsized: 0` in the smoke is not counter-evidence.
- Design note position: design.md:677 explicitly specifies "a speech plate above the speaking cog
  holding its `say` (2 lines, ellipsized)" and design.md:680 "its private `notes` as a small
  parchment (3 lines, ellipsized)", and design.md:702 "notes parchments drop to 1 line there".
  The code matches the design; **the design conflicts with checklist item 15** on this point.

---

## Non-blocking

### N1 — The literal string `/client/replay` is present in the server and in the manifest's `global` protocol text

- Where: `src/liars_dice/server.nim:538` (`result.get("/client/replay", htmlHandler("replay.html"))`),
  `src/liars_dice/server.nim:543` (`result.get("/replay", replayUpgradeHandler)`),
  `coworld_manifest_template.json:383` ("… `/client/replay` plays a recorded episode …")
- Observed: `coworld_manifest_template.json:14-16` declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}` and nothing else; no manifest field, no
  workflow and no viewer file points a hosted replay at a pod. The `/client/replay` route is the
  starter's live-server debug page — `/workspace/starters/cogame-babel/src/babel/server.nim:502`
  has the identical route and the starter's manifest carries the same sentence at line 211.
  design.md:544 keeps the endpoint list verbatim, and design.md:874-875 puts a `/client/replay`
  *pod* out of scope.
- Checklist item 3 says "No `/client/replay` pod path anywhere". I am recording the literal match
  and the evidence that it is a starter-inherited live-server route rather than a hosted-replay
  pod path, and leaving the weighting to the judge.

### N2 — A mid-deal deadline falls back to the seat's registered baseline, not to `bayes`

- Where: `src/liars_dice/server.nim:339-345`
- Observed: `seatScripted = state.scripted[turn.seat] or (playDeadline > 0.0 and now + callGuard
  > playDeadline)`, then `client.decide(simCopy, turn.seat, seatPrompt, scripted = seatScripted,
  baseline = seatBaseline)`. When the guard trips for a seat registered `PLAYER_SCRIPTED=pressure`,
  `seatBaseline == "pressure"` and the `pressure` move is played.
- Design note: design.md:408 — "play deadline reached mid-deal | remaining decisions of that deal
  are `bayes` (instant) so the deal completes". Both baselines are instant and legal by
  construction (`tests/test_bot.nim:36-79`), so the bound in checklist 5 is unaffected.

### N3 — `--band` and `--hudscale` are published but never consumed

- Where: `client/renderer.js:1118-1129` (`relayout` sets both on `document.documentElement`),
  `client/chrome.css:515-521`
- Observed: `grep -rn "var(--band\|var(--hudscale" client replay-viewer` matches **only** the
  comment at `chrome.css:518`. No CSS rule and no JS reads either variable. The endscreen is kept
  off the scrubber structurally instead: `#endscreen { position: absolute; inset: 0 }`
  (`chrome.css:372-374`) inside `#board-wrap { position: relative; flex: 1 }`
  (`chrome.css:95`), which is `#transport`'s flex sibling directly above it
  (`client/replay.html:19-30`).
- Design note: design.md:634-636 and design.md:641-645 describe exactly this arrangement, so the
  code matches the note; the variables are inert. Checklist 14(a) is satisfied literally
  (they are set on `:root`, never on `#stage`).

### N4 — Canvas font floors are 8–11 px, not the 11 px the note claims, and they are driven by `layout.scale`, not `--hudscale`

- Where: `client/renderer.js:509` (speech, `max(9, …)`), `renderer.js:532` (parchment,
  `max(9, …)`), `renderer.js:562-563` (`NO NOTES YET`, `max(8, …)`), `renderer.js:704`
  (`drawTag`, `max(8, …)`), `renderer.js:364/372` (alias/points, `max(10, …)`),
  `renderer.js:685/690` (verdict, `max(11, …)` / `max(9, …)`)
- Observed: every canvas font size is `Math.max(<floor>, Math.round(<n> * scale))` where
  `scale = layout.block.scale = size / SEAT_BASE` (`renderer.js:152`), i.e. a function of the
  canvas size, not of `--hudscale`. The smallest possible drawn string is 8 px.
- Design note: design.md:700-701 — "`--hudscale` floors at **0.7** so no drawn string is smaller
  than **11 px**". Not what the code does. Checklist 11 concerns the DOM scorebug only, which is
  satisfied (see "Traced and consistent").

### N5 — `.plate-pip.hollow` was kept although the note's removal list names it

- Where: `client/chrome.css:444-447`
- Observed: the design's removal list (design.md:619-621) names the babel tail block
  "(`.feed-speak`, `.feed-round`, `.feed-pick`, `.plate-pip.hollow`)". The diff against the
  starter removes the first three and keeps `.plate-pip.hollow` byte-for-byte. It is still used:
  `renderer.js:1015-1017` emits `<span class="plate-pip hollow">` per loss.

### N6 — `.seat5` has no CSS rule while the renderer can emit `seat5`

- Where: `client/chrome.css:205-209` (`.seat0`…`.seat4` only, inherited unchanged from the
  starter), `client/renderer.js:28` (`COLORS` has six entries), `renderer.js:1300`/`1305-1306`
  (`" seat" + (event.seat % COLORS.length)`), `renderer.js:886`/`889`
- Observed: a 5th or 6th seat would get `class="beat-marker bid seat5"` with no `--tc`, falling
  back to `var(--paper-dim)`. Only 4-seat variants ship (`coworld_manifest_template.json:491`,
  `520`, `549`, `576`), so no shipped configuration reaches it. Checklist 14's "a kind with no
  rule is an invisible marker" concerns the *kind* classes, and all five kinds emitted
  (`bid`, `challenge-hit`, `challenge-miss`, `forced`, `end`) have rules at `chrome.css:460-482`.

### N7 — `.end-panel { min-width: 380px }` exceeds a 360 px frame

- Where: `client/chrome.css:382-384`
- Observed: inherited byte-for-byte from the starter (`/workspace/starters/cogame-babel/client/chrome.css:382`).
  At the 360 px featured-match width the endscreen panel is wider than the stage. Checklist 11
  gates only `.plate-name`, which is handled (`chrome.css:505`).

### N8 — The replay test asserts the **final** frame, not every intermediate frame

- Where: `tests/test_sim.nim:507-520`, `tests/test_replay.nim:135-139`
- Observed: `replayMatch` returns `frames.len == events.len + 1` and the tests assert
  `$frames[^1].tableStateJson() == $sim.tableStateJson()` and
  `$frames[^1].resultsJson() == $sim.resultsJson()`, plus `frames[0].events.len == 0` and
  `frames[1].events.len == 1`. No test compares `frames[i]` for `0 < i < n` against the live
  sim's state at step `i`.
- Reading: the live server records **no** per-tick state (only events —
  `server.nim:165-179`), so there is nothing recorded to compare intermediate frames against;
  `replayMatch` re-applies the identical `applyBid`/`applyChallenge` sequence to an `initSim`
  built from the same seed (`sim.nim:667-702`), so intermediate equality holds by construction
  and the endpoint assertion pins it. I am recording the coverage gap rather than calling
  checklist 2 falsified, because the viewer demonstrably renders from the re-derivation
  (`replay-viewer/liars_dice_replay.nim:42-44` builds `states` from `replayMatch`; the recorded
  bytes carry no `states` — confirmed on the downloaded artifact, whose top-level keys are
  `protocol, names, policyNames, config, events, results`).

### N9 — `extractJsonObject`'s error head is rune-safe here where the starter's was byte-sliced

- Where: `src/liars_dice/llm.nim:69-72` (`clipText`), `llm.nim:414`
- Observed: babel's `src/babel/llm.nim` cuts the quoted model reply with `head[0 ..< 160]`
  (a byte slice); this repo replaced it with `clipText(text.strip(), 160)` using
  `runeSubStr`. design.md:214-215 says `extractJsonObject` is "ported … unchanged". It is not
  byte-identical, but the deviation is in the direction checklist 9 asks for.

---

## Traced and consistent

**Resolution rules (design.md §"Resolution rules, in order", rules 1–11)**

- `sim.nim:352-376` `beginDeal` — `sim.deal = sim.dealsPlayed`, `hands = dealHands(config, deal)`
  (seed-only, `sim.nim:236-247`), `turn = deal mod count`, `opener = order[turn]`,
  `bidSeat = -1`, `bidsThisDeal = 0`, and a `deal` event with `deal`/`opener`/`hands`. Rule 1. ✔
  Asserted at `tests/test_sim.nim:105-117`.
- `sim.nim:249-256` `currentTurn` returns `(tkAct, order[turn])` in `phBidding` — exactly one
  seat acts. Rule 2. ✔
- `sim.nim:441-448` `applyChallenge` raises when `bidSeat < 0` ("must bid"). Rule 3. ✔
  `tests/test_sim.nim:127-128`.
- `sim.nim:266-276` `legalBid` — `1 <= q <= totalSymbols`, face in `lowFace..highFace`,
  `not mustChallenge()`, then `q > q0 or (q == q0 and f > f0)`. Ones are not wild anywhere
  (`actualCount`, `sim.nim:285-289`, counts only `symbol == face`). Rule 4. ✔ Exhaustively at
  `tests/test_sim.nim:120-161`.
- `sim.nim:429` `sim.turn = (sim.turn + 1) mod sim.seats()`; `sim.nim:421` `inc bidsThisDeal`.
  Rule 5. ✔
- `sim.nim:449-494` — `counts[slot] = ownCount(slot, face)`, `actual = actualCount(face)`,
  `bidderWins = actual >= quantity`, +1/−1 to exactly two seats, and a `challenge` event carrying
  `quantity, face, actual, counts, bidderWins, forced, seat (challenger), other (bidder)`.
  Rule 6. ✔ `tests/test_sim.nim:174-218` covers `actual >`, `==` and `<`.
- `sim.nim:478-479` `inc dealsPlayed; phase = phReveal`. Rule 7. ✔
- `sim.nim:262-264` `mustChallenge`; `server.nim:327-333` forces the challenge with
  `scripted = true, forced = true` and **no model call**; `sim.nim:406-408` raises if a bid is
  attempted past the cap. Rule 8, bound = `maxBidsPerDeal + 1 = 13` decisions per deal. ✔
  `tests/test_sim.nim:152-161`.
- `sim.nim:495-496` settles `"complete"` when `dealsPlayed >= config.deals`;
  `server.nim:308-318` settles `"deadline"` at a deal boundary past the clock;
  `server.nim:375-376` paces `turnDelayMs` after the closing challenge only. Rule 9. ✔
- `sim.nim:423-425` `say` rides the action and is appended to `dealSays`, reset by `beginDeal`
  (`sim.nim:369`); `llm.nim:385-386` renders `TABLE TALK THIS DEAL` from `dealSays` only.
  Rule 10 (no separate talk phase, no extra call, no cross-deal carry). ✔
- Rule 11: `llm.nim:536-553` — parse, `parseReply`, apply to a **probe copy** (`var probe = sim`,
  `llm.nim:540-546`), any raise is caught, `reason` recorded, one retry with the reason
  (`llm.nim:527-535`), then `scriptedAction(..., "bayes")` with `result.fallback = true`
  (`llm.nim:554-556`); `server.nim:361-371` catches a late `LiarsDiceError` and applies the
  bayes move with `scripted = true, fallback = true`. ✔

**Scoring (design.md:146-161)** — `sim.nim:312-318`: `points = wins - losses`,
`score = 0.5 + points / (2 * dealsPlayed)`, `0.5` when `dealsPlayed == 0`. Asserted, including
the zero-sum and mean-0.5 properties, at `tests/test_sim.nim:220-248`.
`pTrue` (`sim.nim:291-310`) is the exact upper binomial tail through the precomputed
`logFact` table (`sim.nim:211-214`), shared by the audit (`sim.nim:397`), the baselines
(`llm.nim:181`, `llm.nim:207`) and the tests; hand-checked to 1e-9 against tabulated values at
`tests/test_sim.nim:280-308`.
Audit (`sim.nim:387-399`, `324-329`) matches design.md:168-184 term for term and is
re-derived independently by `tests/test_sim.nim:310-385`, which also asserts
`not sim.tableStateJson().hasKey("audit")`.

**Decision path** — one call per turn, sequential, made outside the state lock on a snapshot
(`server.nim:334-345`); `decide` loops `for attempt in 0 .. 1` (`llm.nim:525`) ⇒ at most two
attempts; each HTTP call is bounded by `client.timeoutSeconds` (`llm.nim:442`, default 30 from
`types.nim:69`); a 401/403 latches `client.disabled` (`llm.nim:449`) and breaks the retry loop
(`llm.nim:552-553`); with no credentials the client is `disabled` at construction
(`llm.nim:144-147`) and `decide` returns the scripted move on the first line (`llm.nim:521-522`),
asserted with a `< 1000 ms` bound at `tests/test_bot.nim:154-177`.
Parsing is tolerant: `extractJsonObject` takes `find('{')`…`rfind('}')` (`llm.nim:409-417`),
`parseAction` accepts `bid|raise` and `challenge|call|liar|doubt` case-insensitively
(`llm.nim:471-482`), `parseNumber` accepts `JInt`/`JFloat`/numeric `JString` (`llm.nim:484-500`);
all asserted at `tests/test_bot.nim:179-243`. The fallback is recorded on the event
(`sim.nim:436`, `sim.nim:491`) and always serialised (`sim.nim:727`, `sim.nim:741`), so phase 60
can count it.

**Every wait and its bound (checklist 5)**

| wait | site | bound |
|---|---|---|
| player connect | `server.nim:253-259` | `gameStart + playerConnectTimeoutSeconds` (180 s), 200 ms poll |
| model call | `llm.nim:442` | `llmTimeoutSeconds` = 30 s |
| attempts per decision | `llm.nim:525` | 2 |
| decisions per deal | `sim.nim:262-264` + `server.nim:327-333` | `maxBidsPerDeal + 1` = 13 |
| deals per episode | `sim.nim:495` / `sampleEpisode` `sim.nim:169-181` | `min(deals, 120 div 13) = 9`, floor 2 |
| pacing | `server.nim:375-376`, `379-380` | `turnDelayMs`, itself capped to `PacingBudgetMs div deals` (`sim.nim:179-180`) ⇒ ≤ ~60 s total |
| artifact flush | `server.nim:221`, `231` | two fixed 500 ms sleeps |
| play clock | `server.nim:281-292`, `339-340` | `playDeadline = gameStart + 0.6 * episodeTimeoutSeconds`; `callGuard = 2*llmTimeoutSeconds + 5 = 65 s`; past `playDeadline - 65` every seat is scripted (instant) |

With the defaults that is `playDeadline = 720 s`, last model call starting no later than 655 s and
returning by 715 s — exactly design.md:390-396. `COWORLD_TIMEOUT_SECONDS` is read but the game
falls back to `config.episodeTimeoutSeconds` when silent (`server.nim:274-280`). There is no
unbounded loop: the `while true` at `server.nim:294` breaks on `sim.done`, on `tkNone`, and on
the deal-boundary deadline, and every iteration makes progress. No blocking read anywhere in the
game container.

**String truncation (checklist 9)** — every truncation in the tree is rune-based:
`sim.nim:120-127` `cutRunes` (`runeLen`/`runeSubStr`, cut marked `…`) behind `cleanSay` (140) and
`cleanNotes` (400); `server.nim:504-507` caps the player→game `prompt` at
`MaxPromptLen = 4000` with `runeSubStr`; `llm.nim:69-72` `clipText` for captured error heads.
`grep -rn "runeSubStr\|runeLen" src/ replay-viewer/*.nim` returns exactly these five sites and
no byte slice of text exists in `src/`. Multi-byte input at the cap is asserted valid UTF-8 at
`tests/test_sim.nim:416-437` (300× `é` say, 700× `字` notes, `validateUtf8(...) == -1`) and end
to end on the whole replay payload at `tests/test_replay.nim:120-123`.

**Replay writer** — `server.nim:165-179` emits `liarsdice.replay.v1` with `names` (aliases),
`policyNames`, `config` (mode, seats, handSize, faces, deals, talk, maxBidsPerDeal, seed,
`sampled: true`, order), `events`, `results` — the exact shape at design.md:520-531 and the
exact shape the downloaded artifact has. `finishEpisode` (`server.nim:187-233`) sends the final
frames to players first, then `results.json`, then the replay, then `quit(0)`.

**Viewer re-derivation** — `replay-viewer/liars_dice_replay.nim:21-54` `buildReplayPayload`
parses the recorded bytes, rebuilds a `GameConfig` from `config` + `names`, sets
`config.sampled = true` (never re-fits), and produces `states` **only** from
`replayMatch(config, events)` (`sim.nim:667-702`). There is no parallel recording: the artifact
I downloaded has no `states` key. A doctored `deal` event raises (`sim.nim:689-692`), asserted
both in-sim (`tests/test_sim.nim:522-541`) and through the wasm entry
(`tests/test_replay.nim:159-169`). A recorded `deadline` end is pre-seeded into `forcedReason`
before replay (`sim.nim:678-680`, `sim.nim:341-350`) and re-derives as `deadline` in all three
phases (`tests/test_sim.nim:543-571`).

**Static viewer + bootstrap coupling (checklist 3, 13)**

- `coworld_manifest_template.json:14-16` — `"replay_viewer": {"bundle": "static-replay-viewer"}`.
- `tools/build_replay_viewer.sh` present, mode `100755`, asserted present+executable at
  `ci.yml:225-236` and invoked by path at `ci.yml:249`.
- `replay-viewer/config.nims:33-46` links `-s MODULARIZE=1 -s EXPORT_NAME=LiarsDiceReplayModule`
  and `-s EXPORTED_FUNCTIONS=_main,_malloc,_free,_ld_load_replay,_ld_payload_ptr,_ld_payload_len,_ld_error_ptr,_ld_error_len`,
  output `dist/liars_dice_replay.js`.
- `replay-viewer/static_replay.js:138` calls the **factory** `LiarsDiceReplayModule()` and
  `static_replay.js:94-104` calls `_ld_load_replay` / `_ld_payload_ptr` / `_ld_payload_len` /
  `_ld_error_ptr` / `_ld_error_len` — the same names. `grep -n onRuntimeInitialized` over the
  repo returns nothing. The exports are defined at `liars_dice_replay.nim:56-82` with matching
  `exportc` names. The link flags and the bootstrap are both babel's, diffed side by side:
  the only changes are the `bab_`→`ld_` and `Babel`→`LiarsDice` renames.
- Load signals: `data-replay-loaded="true"` at `client/renderer.js:1447`, set inside the
  `makeRenderer` callback **after** the frame loop's first synchronous
  `renderer.draw(view)` at `renderer.js:1443` — i.e. on the first drawn frame; byte-identical
  placement to the starter's `renderer.js:1309`, which design.md:596-598 names. `data-replay-error`
  is set at `static_replay.js:56` on every failure (missing `?replay=`, 20 s fetch timeout at
  `static_replay.js:14`/`73-88`, non-ok status, wasm rejection) and cleared at
  `static_replay.js:107` and `static_replay.js:134`. The `coworld-replay` postMessage bridge
  (`loading`/`ready`/`error`) is kept at `static_replay.js:25-31`, `57`, `122-124`.
  `build_replay_viewer.sh:59` greps `data-replay` in the copied shell.
- Nothing but S3 is contacted: the only network call in the bundle is
  `fetch(url)` on the `?replay=` parameter (`static_replay.js:76`); assets are relative
  (`assetBase: "./assets"`, `static_replay.js:117`; `@font-face url("assets/font.ttf")`,
  `chrome.css:9-13`), and `build_replay_viewer.sh:44-56` copies them into `assets/`.
- **Executed, not merely built:** run 32994991825, `wasm-viewer` job 98262880977, step 11
  `Load the bundle in a real browser` — conclusion `success`, not `continue-on-error`, and
  `wasm-viewer` carries `needs: docker-smoke` (`ci.yml:212`). Output:
  `{"loaded":true,"ms":291,"clock":"DEAL 0 / 3","scorebug":"Sprocket 0 POINTS Gizmo 0 POINTS Ratchet 0 POINTS Widget 0 POINTS","feed_lines":17}`
  and `scrub readouts: 0%="DEAL 0 / 3"  50%="DEAL 2 / 3 · WIDGET TO ACT"  100%="DEAL 3 / 3 · FINAL"`.
  `tools/ci/viewer_smoke.mjs` is byte-identical to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff -q` → identical).

**Chrome provenance (checklist 14, via the design's name mapping)**

- `client/chrome.css` vs the starter: a **single** diff hunk, at the tail (line 432 onward). The
  whole of sections 1–5 — `:root` palette, `@font-face`, `#layout`, `#stage`, `#topband`,
  `#wordmark`, `#clock`, `#statuschip`, `#topright`, `#board-wrap`, `canvas#table`, `#lightpool`,
  `#grain`, `#transport`, `.tbar`, `.tbtn`, `.tpos`, `.scrub*`, `.beat-marker`, `.seat0..4`,
  `.round-span`, `.round-sep`, `#feed`, `.feed-*`, `#feedtoggle`, `#loading`, `#scorebug`,
  `.plate*`, `#endscreen`, `.end-*` — is byte-identical to
  `/workspace/starters/cogame-babel/client/chrome.css`. The removed block is exactly the one the
  note names (`/* Babel: speak lines in the speaker's colour … */`, minus N5). The added block is
  under the banner `liars-dice additions to the inherited cogame-babel chrome`
  (`chrome.css:12-14`).
- `client/replay.html`, `client/global.html`, `client/player.html`, `replay-viewer/index.html`:
  each is the starter's page verbatim except the wordmark/title/clock strings, the
  `BabelRenderer`→`LiarsDiceRenderer` rename, the `babel_replay.js`→`liars_dice_replay.js`
  script name, and a `relayout()` block appended under
  `<!-- liars-dice additions to the inherited cogame-babel chrome -->` — the exact banner
  design.md:610 specifies. No section was dropped; the pages are within a few lines of the
  starter's length (replay.html 84 vs 70, index.html 63 vs 48). Not a rewrite.
- `client/renderer.js`: the starter's file with (a) the named removals — `drawCard`, `drawShape`,
  `drawRibbon`, `sceneOf`, `sceneText`, `boothPairs`, `spellTokens`, `SHAPES`, `COLOURS`,
  `LETTERS`, `GLYPH_FONT` (`grep` → all absent) — (b) the game-specific `draw`/`describeEvent`
  stage swap, and (c) the two named patches: clickable labelled `<button class="beat-marker …">`
  beats that seek through the same `onSeek` (`renderer.js:1294-1329`) and `relayout()`
  (`renderer.js:1114-1129`). Everything above the stage — layout, scorebug, feed, scrubber,
  endscreen, name map, effects bookkeeping, both drivers, replay pacing — is structurally the
  starter's with field renames only; I read all 27 diff hunks.
- Transport rules: (a) `relayout()` sets both variables on `document.documentElement`
  (`renderer.js:1119-1128`), never on `#stage` — see N3; (b) `grep -n "position: fixed"
  client/chrome.css` → the appended block adds no fixed-position element; (c) `#endscreen` is
  `inset: 0` inside `#board-wrap`, the transport's sibling (`chrome.css:372-374`, `95`;
  `replay.html:19-30`), is shown with the class its rule uses — `#endscreen.show`
  (`chrome.css:381`) toggled by `container.classList.toggle("show", !!show)`
  (`renderer.js:1052`) — and **every** seek takes it down, because `setIndex` always calls
  `updateEndscreen(..., index >= events.length && events.length > 0, ...)`
  (`renderer.js:1415-1416`) and every seek path (track drag `renderer.js:1334-1353`, beat button
  `renderer.js:1324-1327`, play button `renderer.js:1384-1387`) routes through `setIndex`;
  (d) all five emitted beat kinds have CSS rules (`chrome.css:460-482`) — see N6 for the seat
  colour classes.
- Zoom bar / minimap: **absent**, as the note requires (design.md:654-656). `grep -rn
  "viewpanel\|zoomAt\|setZoom\|attachMinimap"` over `client/` and `replay-viewer/` matches only a
  comment at `renderer.js:171`. `computeLayout` re-solves the whole table into the frame each
  frame (`renderer.js:168-226`), so the arena is fixed and `--strict-text-bounds` is correctly
  kept (`ci.yml:318`).

**Manifest (checklist 6, 10)**

- `num_agents: 4` in **every** variant — `standard` (line 491), `poker` (520), `silent` (549) —
  and in `certification.game_config` (576). `config_schema.num_agents` is `integer, 4..4`
  (68-73).
- `certification.players` has 4 entries (586-599); `certification.game_config.players` has 4
  (562-575).
- `game.docs` is `{"readme": {"type":"text","value":…}, "pages":[{"id":"rules.md","title":"rules.md",
  "content":{"type":"text","value":…}}]}` (386-401) — exactly the shape checklist 10 names.
- `game.protocols` carries **both** `player` (377-380) and `global` (381-384).
- `docker_smoke.sh:110-151` enforces all four seat-count invariants before any container starts —
  `num_agents` present, positive integer (and `isinstance(..., bool)` excluded),
  `len(certification.players) == num_agents`, `len(certification.game_config.players) ==
  num_agents` — plus the independent `SMOKE_SEATS` cross-check (146-151); every failure raises a
  message prefixed `SEAT-COUNT FAIL:`. The script is `100755` and is asserted executable at
  `ci.yml:166-174`.
- **`grep -c "SEAT-COUNT FAIL"` over both CI job logs of run 32994991825 → 0.** The log shows
  `game=liars-dice seats=4 config={… "num_agents": 4 …}` and `smoke OK: seats=4 results=635B
  replay=2220B reason=complete`, `all 4 player containers exited 0`.
- `docker_smoke.sh` is the builder template with **only** the three documented substitutions
  (`<slug>`→`liars-dice`, `<IMAGE>`→`coworld-liars-dice`, `<SEATS>`→`4`) — verified by
  `diff -u templates/tools/ci/docker_smoke.sh`.

**Release order and scaffold (checklist 12)** — all three workflows present.
`coworld-release.yml` step order: `Build the Coworld manifest` (159) → `Certify locally` (173) →
`Upload the policies` (212) → `Upload the Coworld` (310) → `Put the Coworld secret` (348).
`tools/ci/policies.json` defines four distinct policies: two `PLAYER_PROMPT` champions
(`liars-dice-calibrator`, `liars-dice-needler`) and two `PLAYER_SCRIPTED` fillers
(`liars-dice-bayes`, `liars-dice-pressure`); champion #2 carries
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The placeholder gate
(`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files) matches nothing and exits 1, so
the gate exits 0. `docker_smoke.sh` and `build_replay_viewer.sh` are both `100755`.

**Both name spaces (checklist 4)** — agents see aliases only: `systemPrompt`/`userPrompt` index
`sim.names` (`llm.nim:247`, `llm.nim:371-390`) and never `config.players[].name`; the player
socket's `welcome`/`state`/`final` frames all carry the alias (`server.nim:456`, `106`,
`209-212`). Spectator side: `policyNames` rides the global snapshot (`server.nim:92`) and the
replay (`server.nim:175`), and `makeNameMap` (`renderer.js:743-767`) swaps alias→policy for the
scorebug, feed and endscreen while `isBaselineFiller` (`renderer.js:739-741`) keeps
`Baseline (N)` seats on their alias. Platform side: `results.names` = policy names,
`results.aliases` = aliases (`sim.nim:545-551`).

**Scripted baseline plays full episodes legally (checklist 7, first sentence)** —
`tests/test_bot.nim:82-112` runs `bayes` and `pressure` across 4 seeds × 2 modes × 2 talk
settings × 3 seat counts (48 episodes), asserts `sim.reason == "complete"`, `dealsPlayed == 3`,
and — inside `playBaselines` (`test_bot.nim:53-76`) — that every emitted action is inside its
legal bounds (`legalBid`, face range, quantity range, raise window `q0..q0+3`,
`bidsThisDeal <= maxBidsPerDeal`, empty `say`/`notes`) and is accepted by the sim first time.
The calibration test (`test_bot.nim:132-151`) asserts `bayesMean > 0.5` and `pressureMean < 0.5`
over 4 seeds × 30 deals.

**CI green + no test loosened (checklist 1)** — `gh run list -R Metta-AI/cogame-liars-dice
--branch main -w ci.yml`: run **32994991825**, conclusion **success**, `headSha`
`23da0888e90cc3c57ef7c901811fca488749d62e` — the reviewed sha. All three jobs (`test`,
`docker-smoke`, `wasm-viewer`) green with every step `success`.
`git log --stat -- tests/` shows a single commit (`0c5587c`) adding
`tests/test_bot.nim` (+252), `tests/test_replay.nim` (+169), `tests/test_sim.nim` (+572),
0 deletions. No test file has ever been modified, and no `skip`/`xfail`/widened tolerance exists
in the tree.

**Miscellaneous traced** — `liars_dice.nimble` version `0.1.0` with babel's requires;
`compose.yaml` service `liars-dice`, image `coworld-liars-dice:latest`, `platform: linux/amd64`;
`Dockerfile` emits `/bin/liars-dice` and `/bin/liars-dice-player` (lines 57-58);
`sampleEpisode` is applied once, after the seed settles (`liars_dice.nim:34-42`), and is
idempotent (`sim.nim:173-174`); `normalizeBaseline` coerces anything but `pressure` to `bayes`
and the server logs the coercion (`server.nim:510-513`), asserted at `test_bot.nim:114-130`;
mummy `Ping` frames are answered with `Pong` (`server.nim:490-492`); the player exits 0 on a
closed socket (`liars_dice_player.nim:64-94`), confirmed by `all 4 player containers exited 0`
in the smoke.

---

## Could not determine

- **Checklist 7, second sentence — "The baseline's parameters were tuned with a grid harness,
  not guessed."** `BayesChallenge = 0.40 / BayesSafe = 0.55` and
  `PressureChallenge = 0.25 / PressureSafe = 0.35` (`src/liars_dice/llm.nim:29-34`) match
  design.md:322-345, and `tests/test_bot.nim:132-151` demonstrates the calibrated pair beats the
  loose pair — but there is no grid harness in the tree (`tools/` contains only
  `build_replay_viewer.sh` and `ci/`), and neither the README nor the design note records a
  sweep. **What would settle it:** a committed harness (or its output table) in the repo, or a
  cited phase-20 run log showing the threshold sweep.
- **The bound on the artifact write.** `writeArtifact` uses `curl.post(..., 60)` for the POST
  path (`server.nim:141`) but delegates to `writeCogameUri` (bitworld) for PUT/file
  (`server.nim:146`); bitworld is not vendored in the repo, so I could not read its internal
  timeout. This is after `quit`-time play and is identical to the starter's code path.
  **What would settle it:** reading `bitworld/runtime`'s `writeCogameUri`.
- **The real ellipsis behaviour of B2.** My character-per-line arithmetic assumes a ~0.42 em
  advance for the bundled `rajdhani` face; I cannot run a browser here.
  **What would settle it:** the worst-case renderer fixture B1 asks for, reporting
  `canvas_text.ellipsized` with a full-cap 140-character `say` on all four seats.
