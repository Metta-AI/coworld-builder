# r1 review — negotiation-games

Repo: `Metta-AI/cogame-negotiation-games` @ `5f23877d0066763e52d695be02ffe88d5133e2b4` (main, cloned to `/tmp/cogame-negotiation-games`)
Range: `50e62ff..5f23877` (7 commits; starter baseline `/workspace/starters/cogame-babel`)
Files read: 34 (all of `src/`, `client/`, `replay-viewer/`, `tools/`, `tests/`, `.github/workflows/`, `coworld_manifest_template.json`, `Dockerfile`, `compose.yaml`, `negotiation.nimble`) + babel's `client/renderer.js`, `client/{replay,global,player}.html`, `client/chrome.css`, `replay-viewer/*`, `src/babel/server.nim`, `src/babel_player.nim` for provenance, + CI run 33022161451 logs and its `viewer-smoke` / `renderer-fixture` artifacts.
Design note: `/workspace/coworld-builder/runs/2026-08-26-negotiation-games/design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15).

Accepted deviations ruled on by the coordinator were verified as described and are **not** filed as
findings; they are recorded in "Traced and consistent" below.

---

## Blocking candidates (the judge makes the call)

### F1 — the 4000-char player-prompt cap is a **byte** slice, not a rune cut
- Where: `src/negotiation/server.nim:492-493`
  ```nim
  var prompt = payload{"prompt"}.getStr()
  if prompt.len > MaxPromptLen:
    prompt = prompt[0 ..< MaxPromptLen]
  ```
- Observed: `prompt.len` is the **byte** length in Nim and `prompt[0 ..< MaxPromptLen]` is a **byte**
  slice, so a prompt whose first 4000 bytes end inside a multi-byte rune is cut mid-rune. The
  truncated value is stored at `server.nim:503` (`state.prompts[slot] = prompt`) and is later
  interpolated verbatim into the user prompt by `llm.nim:295-299` / `llm.nim:329`
  (`operatorBlock(prompt)`), which is serialised into the request body at `llm.nim:412-415`. Every
  other string in the tree *is* rune-cut: `capRunes` (`sim.nim:107-114`, `runeLen`/`runeSubStr`),
  `cleanMessage` (`sim.nim:119-132`), `cleanNotes` (`sim.nim:116-117`), the error heads quoted into
  log lines (`llm.nim:407`, `llm.nim:436`, `llm.nim:445`, `llm.nim:450`, `llm.nim:459`).
- What the note says: §Server, `player → game` frame — "`prompt` capped at 4000 chars server-side";
  §Reply schema and its caps — "Both are measured and cut in **runes**, never bytes … the cap
  applies to every string that reaches the replay".
- Checklist item: 9 — "Every string that reaches the replay (`say`, `notes`, **prompts**, captured
  errors) is truncated on **rune** boundaries."
- Scope of the consequence, traced: the operator prompt does **not** reach the replay
  (`server.nim:143-167` writes only `names`, `policyNames`, `config`, `events`, `results`; events
  carry only `cleanMessage`/`cleanNotes` output), and it does not reach `results.json`
  (`sim.nim:535-564`). Its only consumer is the Anthropic/Bedrock request body, where an invalid
  UTF-8 fragment would ride into `$body` (`llm.nim:434`). No test covers this cap (the note's test
  12 and `tests/test_sim.nim:422-457` cover `message` and `notes` only).
- Provenance: byte-identical to the starter (`cogame-babel/src/babel/server.nim:477-478`), i.e.
  inherited, not introduced by this fork.

### F2 — the full-cap remark is drawn on the canvas as one ellipsized line, sized by eye
- Where: `client/renderer.js:307-313` (the draw), `client/renderer.js:46-68` (`negLabel`, which calls
  `C.ellipsize` at 55-57), `client/chrome_common.js:85-92` (`ellipsize`)
  ```js
  var talk = (table.messages || [])[s] || "";
  if (talk) {
    negLabel(ctx, "“" + talk + "”", xs[s], cogY + cog * 0.72 + 30 * scale, {
      font: negFont(10.5 * scale), color: GHOST, maxWidth: w * 0.3
    });
  }
  ```
- Observed: the seat's public message — capped server-side at 200 runes (`sim.nim:41`,
  `sim.nim:119-132`) — is drawn as a **single line** clamped to `maxWidth = w * 0.3` and cut with
  `…` by `ellipsize`. The box is a fraction of the canvas width, not derived from `MaxMessageLen`
  or measured in the font it is drawn in; nothing wraps, and no band is reserved. CI corroborates:
  the renderer fixture at 360/720/1280 px reports `canvas_text: {total: 1696, outside: 0,
  never_inside: 0, ellipsized: 265}` (`dist/fixture/viewer-smoke.json`, run 33022161451), and the
  fixture's own caption in the uploaded screenshot reads "1579 canvas strings drawn, 239 ellipsized,
  **longest 66 chars**" — i.e. no string longer than 66 characters ever reached `fillText`, against
  a 200-rune cap. The screenshot shows both seats' remarks rendered as
  `"négocions—jé négocions—jé négocions—jé négocions—jé…"`.
- The fixture is built to *require* this: `tools/ci/renderer_fixture.html:305-309` fails if
  `totals.ellipsized === 0` ("no drawn string was ellipsized: the full-cap table talk never reached
  the canvas"), so ellipsis of the remark is the fixture's success condition rather than its
  failure condition. The fixture does correctly assert the *payload* strings are full length
  (`renderer_fixture.html:256-287`: `message !== 200` / `notes !== 400` throw).
- Where the full text does exist: the DOM feed line (`client/renderer.js:583-589`, `feed-say`),
  which wraps. But both shells start the feed collapsed —
  `replay-viewer/index.html:57` and `client/replay_broadcast.html:55` call
  `bindFeedToggle(document.getElementById("feedtoggle"), true)`, and
  `chrome_common.js:270-278` adds `body.feed-collapsed`, which babel's
  `client/chrome.css` hides — so on first paint the remark is visible only in its ellipsized canvas
  form.
- What the note says: §Viewer "What the viewer draws" describes no on-stage speech element at all
  (the message appears only in the Feed list: `Sprocket: "I only need the books."`). §Legibility at
  360 px lists what collapses under 420 px and does not mention the remark line.
- Checklist item: 15 — "Any text laid out **relative to another element** … gets a **reserved band
  in the layout**, sized from the cap the server enforces on that string (`MaxSayLen` and its kin)
  and measured in the font it will be drawn in. Sizing by eye … is the bug above." and "Ellipsis is
  a design choice for **labels** and a defect for **sentences**. If `ellipsized` counts a remark
  rather than a nameplate, the box is too small."
- What is *not* wrong here, traced: nothing is drawn out of frame (`never_inside: 0`, `outside: 0`
  on both the smoke replay and the fixture), the remark's y position is static so the scene does not
  jump when a remark lands, and `negLabel` (`renderer.js:57-59`) additionally clamps the centre
  point inside the canvas.

---

## Non-blocking observations

### N1 — the seed feeds **two** RNG streams, not the "single stream" the note describes
- Where: `src/negotiation/sim.nim:181-187` (`tableNames`: `initRand(int64(seed) * 6779 + 31)`) and
  `sim.nim:284-288` (`initSim`: `initRand(int64(config.seed) * 7919 + 17)`, immediately under the
  comment "One stream for everything the seed decides: the aliases above, then the whole schedule").
- Observed: the aliases are drawn from one `Rand`, the schedule from a second, independently seeded
  one. The comment at `sim.nim:285-286` states the opposite of what the code does.
- What the note says: §Resolution order step 1 — "`initSim(config)` draws, from `seed`: the seat
  aliases (babel's `tableNames`), then for each match … the pairing, the opener, the counts, and
  both seats' values", and §The pool — "draws, in this exact order, from the **single seeded RNG
  stream**".
- No functional consequence traced: both streams are pure functions of `seed`, so determinism and
  replay re-derivation (`replayMatch` → `initSim`, `sim.nim:747`) are unaffected; `tests/test_sim.nim:55-70`
  passes.

### N2 — the offer entrance animation and the stamp fade the note describes are not implemented
- Where: `client/renderer.js:635-639` (the registered painter is `negStage` only),
  `client/renderer.js:255-363` (`negStage` reads `view.seats` and `view.table`; it never reads
  `view.effects`), `client/renderer.js:634` (`effectResetKinds: ["match"]` is registered),
  `client/chrome_common.js:165-183` + `391-398` (the chrome computes `view.effects.at` every frame).
- Observed: `makeEffects` state is computed and handed to the painter and then discarded. Every
  frame is a static redraw.
- What the note says: §What the viewer draws — "A new offer slides in and holds like babel's
  last-move arrow; the standing offer stays lit while the other seat thinks"; "[the stamp] holds for
  the pacing delay and fades as the next match's `match` event lands".

### N3 — three stage/feed strings differ from the note's copy
- Where: `client/renderer.js:243-252` (stamp), `client/renderer.js:560-562` (`end` feed line).
- Observed: the no-deal stamp prints `NO DEAL` + `<maxTurns> TURNS, NO AGREEMENT` with no `0 – 0`
  line; the deal stamp prints `DEAL` + `7 – 3` with no final item split; the `end` feed line is
  `Final — N matches played.` with no per-seat total.
- What the note says: §What the viewer draws — "green `DEAL` with `7 – 3` **and the final item
  split**, or red `NO DEAL` with **`0 – 0`** and `10 TURNS, NO AGREEMENT`"; Feed — "`Final —
  Sprocket 25 pts (0.62)`". (The per-seat totals do appear on the endcard,
  `client/renderer.js:489-519`.)

### N4 — `#matchbar` chips are derived from emitted `match` events, not from the schedule
- Where: `client/renderer.js:604-616`
  ```js
  if (event.kind === "match") total = Math.max(total, event.match + 1);
  ```
- Observed: `total` counts matches that actually started. In a `deadline` replay the unstarted
  matches emit no `match` event (`server.nim:301-311` breaks out before `beginMatch`), so the bar
  shows fewer chips than `config.matches`, and the "pending" chip class
  (`renderer.js:619`, `chrome.css:487-497`) is only ever used for a started-but-unsettled match.
- What the note says: §Viewer — "`#matchbar` is one chip per **scheduled** match … filled as
  matches settle".

### N5 — `chrome_common.js` carries four defensive edits beyond the note's three named changes
- Where: `client/chrome_common.js:53` (`if (!pending) { done(images); return; }` in `loadImages`),
  `:105` (`String(text)` in `escapeHtml`), `:201` (`if (!element) return;` in `renderFeed`), `:296`
  (`if (!container) return { update: … };` in `buildScrub`).
- Observed: a function-by-function diff against babel's `client/renderer.js` chrome half shows every
  other change is either a hook redirection, the `<button>` beat markers, `relayout()`/`onFirstFrame`,
  or the `makeNameMap` third-parameter removal — i.e. the note's three changes plus the two
  coordinator-accepted deviations. These four are additional small behaviour changes to inherited
  bodies.
- What the note says: §Chrome provenance — "The function bodies are not edited except for these
  **three** changes, which are the whole diff".
- Checklist item 14 admits "a named, minimal patch recorded in the design note"; these four are
  minimal but not named.

### N6 — "every chrome font size and pad is expressed in `calc(… * var(--hudscale))`" holds only for the appended rules
- Where: `client/chrome.css:452-588` (appended block: `.plate-score`, `.plate-sub`, `.mb-chip`,
  `#valuestrip` use `calc(… * var(--hudscale))`) vs `client/chrome.css:1-441` (babel's rules,
  byte-identical to the starter, with literal `px` font sizes, e.g. `.tpos` at `:155-162`).
- Observed: `relayout()` (`chrome_common.js:257-268`) does write `--band` and `--hudscale` on
  `document.documentElement`, and the appended rules consume `--hudscale`; the inherited sections do
  not. Leaving them untouched is what checklist item 14 requires, so this is a note-vs-code wording
  mismatch, not a defect.

### N7 — the player container's receive loop is a blocking read with no timeout
- Where: `src/negotiation_player.nim:55-56` (`while true: let received = socket.receiveMessage()`).
- Observed: whisky's `receiveMessage*(ws, timeout = -1)` blocks indefinitely by default (vendored
  copy read at `/workspace/cogamer/cogames/zero-sum/policies/zs-scavenger/vendor/whisky/src/whisky.nim:73`).
  The loop ends on the `final` frame (`negotiation_player.nim:72-74`), on `none` (`:57-59`), or on
  the raise that a close frame produces, which is caught at `:79-80` and exits 0. The game always
  sends `final` before writing artifacts (`server.nim:193-205`) and then `quit(0)`
  (`server.nim:227`), so the wait is bounded by the game's own bounded lifetime; CI observed "all 3
  player containers exited 0" (docker-smoke, run 33022161451). Identical in shape to the starter
  (`cogame-babel/src/babel_player.nim:51-52`).
- What the note says: §Server, player — the loop "is wrapped in `try/except CatchableError` and
  **exits 0** on a dead socket" (implemented exactly).

### N8 — three declarations are dead
- Where: `src/negotiation/sim.nim:28` (`MaxMatchesCap* = 6`, never referenced),
  `src/negotiation/llm.nim:204-206` (`scriptedAction`, never called),
  `client/renderer.js:704` (`phaseText: negPhase` is registered but `chrome_common.js` never reads
  `H.phaseText`; `negPhase` is reached only via `negHeader`, `renderer.js:397`).
- The note lists `MaxMatchesCap` among §Sim module constants and `phaseText` among the redirected
  hooks, so all three are declared as designed; none is reachable.

---

## Traced and consistent

**Resolution order (§The game, numbered).**
- 1. `initSim` (`sim.nim:275-294`) validates 3 players / `matches ≥ 3` / even `maxTurns ≥ 2`, draws
  aliases then the whole schedule before any decision (`drawSchedule`, `sim.nim:242-253`) and emits
  `start` (`sim.nim:294`). Pairing = `Pairings[m mod 3]`, opener = `(m div 3) mod 2 == 0 ? 0 : 1`
  (`sim.nim:247-250`) — exactly the note. Verified by `tests/test_sim.nim:72-91` (4 plays / 2 opens /
  each pairing twice).
- Pool draw `1 + rng.rand(3)`, redraw while total ∉ [5,7], ≤ 32 attempts, then `FallbackPool
  [3,2,2]` (`sim.nim:194-206`); value table exhaustive lexicographic over `{0..10}³` with
  `pool·v == 10` (`sim.nim:208-215`); B redrawn ≤ 16 times for `vA[i]+vB[i] > 0`, then a scan of the
  table, then the last draw (`sim.nim:223-240`). Matches the note's three numbered draws exactly,
  including the bounds. Tests 3/4 (`test_sim.nim:92-134`).
- 2. Connect wait: `while epochTime() < connectDeadline` polling every 200 ms
  (`server.nim:249-255`), `playerConnectTimeoutSeconds` default 180 (`types.nim:65`), then starts
  regardless (`server.nim:257-261`). A seat that never connects keeps `prompts[slot] == ""`, and
  `operatorBlock` returns `""` (`llm.nim:295-297`) — the note's "empty operator block".
- 3.1 Deadline honoured **between** matches only: `ckMatch` + `pastDeadline` → `endEarly()` +
  broadcast + break (`server.nim:301-311`).
- 3.2 `beginMatch` emits `match` with index, kind, seats, opener (as a seat id), pool, both value
  rows, `maxTurns` (`sim.nim:406-414`).
- 3.3.1–3.3.6: snapshot + prompt + baseline + `pastDeadline` under the lock (`server.nim:294-322`);
  scripted-or-model decision (`server.nim:324-337`); apply under the lock with the fallback path
  (`server.nim:341-366`); accept → `matchEnd`/`deal`/`payoff`/`turns = t` (`sim.nim:522`,
  `sim.nim:416-434`); turn cliff at `sim.turn >= maxTurns` → `no_deal` / `[0,0]` / `turns = maxTurns`
  (`sim.nim:486-490`); broadcast after every applied action (`server.nim:366`).
- 3.4 pacing sleeps only when a match settled and only inside `PacingBudgetMs`
  (`server.nim:370-373`).
- 4. `settle("complete")` fires from `endMatch` when `matchesSettled >= config.matches`
  (`sim.nim:435-436`); `end` carries `match = matchesSettled`, `text = reason` (`sim.nim:384-387`).
- 5. `finishEpisode` (`server.nim:175-227`): final frames to players (with **aliases**, not policy
  names, `server.nim:190-205`) → results → replay → 20 s grace → `quit(0)`.
- Invariant "every `match` event has exactly one `matchEnd`": enforced structurally (the deadline
  cannot fire mid-match) and tested at `test_sim.nim:271-285` over `stopAfter ∈ [-1,0,2,4]` and at
  `replay_check.py:78-82` on the CI replay (6 started / 6 settled, run 33022161451).

**Scoring (§Scoring).** `u(s)` per side from each side's own values (`sim.nim:464-465`,
`sim.nim:502-505`); `points/matchesPlayed/deals/given/taken` in `endMatch` (`sim.nim:421-428`);
`score = points / (10 · matchesPlayed)`, 0.0 at zero matches (`sim.nim:361-364`); `giveaway =
(given − taken)/matchesPlayed` (`sim.nim:366-371`). `results.reason` can only ever be `""`,
`"complete"` or `"deadline"` — `settle` is called with a literal at `sim.nim:436` and `sim.nim:528`,
and nowhere else (`replayMatch` re-applies the recorded string, `sim.nim:795`). Tests 6/7
(`test_sim.nim:189-269`).

**Decision path.** `decide` (`llm.nim:461-504`): a registered scripted seat returns its baseline
with `fallback = false` (`:473-475`); `forceScripted`/`disabled` returns the baseline with
`fallback = true` and no network (`:476-479`); otherwise `for attempt in 0 .. 1` — exactly one retry
— with `RetryHint` appended on the second pass (`:481-484`), the hint text byte-matching the note's
§Degrade item 1 (`llm.nim:31-34`). Legality is enforced on a **probe copy** of the sim before
returning (`:489-494`; `var probe = sim` is a value copy in Nim). `decide` catches
`CatchableError` (`:496-500`) and always returns a scripted decision on give-up (`:501-504`), so it
never raises. Parse tolerance matches the note's table item for item: synonyms and casing
(`llm.nim:371-378`), `action` absent + `take` present → offer (`:375-379`), object with defaulted
keys or a 3-element array (`:382-394`), integer-valued strings (`:340-355`), everything else raises.
`extractJsonObject` tolerates fences and trailing prose (`llm.nim:398-409`). Tests 17/18
(`test_bot.nim:196-308`), all `[OK]` in run 33022161451.

**Fallback counting.** `results.fallbacks` is incremented at `server.nim:363-364` when
`decision.fallback` and at `server.nim:358` when an apply is rejected. Only one of the two can fire
in practice: a `fallback` decision is produced by `scriptedDecision` on the live-turn sim, which
returns `accept` only when `acceptLegal` (`llm.nim:198`) and otherwise a `take ≤ pool`
(`llm.nim:167-189`), so it cannot be rejected by `applyOffer`/`applyAccept`. Past-deadline turns are
counted as fallbacks (via `forceScripted` → `fallback = true`), which the note's §Degrade item 2
does not list but which is consistent with phase 60 counting degraded turns; seats that *registered*
a baseline are never counted (`llm.nim:473-475`, asserted at `test_bot.nim:218-222`).

**Waits and bounds.**
| wait | bound | where |
|---|---|---|
| player connect | `playerConnectTimeoutSeconds` (180), 200 ms poll | `server.nim:247-255` |
| model call | `client.timeoutSeconds` = `llmTimeoutSeconds` = 30 passed to `curly.post` | `llm.nim:434`, `types.nim:68` |
| retries | exactly 2 attempts | `llm.nim:481` |
| inter-call spacing | `≤ MinCallSpacingMs` = 2200 ms | `server.nim:328-332`, `sim.nim:36` |
| play deadline | `gameStart + timeout × 0.6` (720 s of 1200), re-tested every loop iteration under the lock and consumed both by the `ckMatch` branch and by `forceScripted` on every model call | `server.nim:229`, `:270-283`, `:298`, `:324`, `:336-337` |
| pacing | `PacingBudgetMs` = 20 000 ms per episode | `server.nim:370-373`, `sim.nim:33` |
| artifact flush | fixed `sleep(500)` | `server.nim:208` |
| shutdown grace | fixed `ShutdownGraceSeconds` = 20 s then `quit(0)` | `server.nim:223-227`, `sim.nim:40` |
| replay fetch (viewer) | `FETCH_TIMEOUT_MS` = 20 000 via `AbortController` | `replay-viewer/static_replay.js:14`, `:67-89` |

The game loop (`server.nim:288-374`) has no unbounded iteration: every pass either breaks
(`:290-311`), begins a match, or applies exactly one action that advances `turn` or settles the
match. Worst case past the deadline is one in-flight turn (2.2 s spacing + 2 × 30 s) plus scripted
settles — the note's ≤ 780 s. `EpisodeCallBudget` arithmetic holds: `sampleEpisode`
(`sim.nim:255-267`) gives `matches = 6` at `maxTurns = 10` (60 ≤ 72 calls) and is idempotent via
`config.sampled`; tested at `test_sim.nim:405-420`. There is no top-level `try` around the game
thread (`server.nim:243-375`), exactly as in the starter (`cogame-babel/src/babel/server.nim:250`);
I could not construct a reachable raise there (see "Could not determine").

**Truncation.** `capRunes` cuts at `limit - 1` runes plus `…` (`sim.nim:107-114`); `cleanMessage`
maps TAB/LF/CR to space, drops other C0 and DEL, then caps at 200 (`sim.nim:119-132`); `cleanNotes`
caps at 400 (`sim.nim:116-117`). Every string that reaches an event goes through them:
`applyOffer` (`sim.nim:466-467`, event `text`/`notes` at `:483-484`), `applyAccept`
(`sim.nim:506-507`, `:519-520`), and `parseAction` also cleans on the way in (`llm.nim:367-368`).
Error heads quoted into logs are rune-cut (`llm.nim:407`, `:436`, `:445`, `:450`, `:459`).
Test 12 (`test_sim.nim:422-457`) feeds 500 `é` and 900 `ñ` and asserts `runeLen == 200/400`,
`validateUtf8 == -1`, trailing `…`, byte length > rune cap, and `validateUtf8($tableStateJson) == -1`.
The strict-UTF-8 replay parse is a second gate (`replay_check.py:41-42`, green in CI). F1 is the one
exception.

**Replay writer.** `replayPayload` (`server.nim:143-167`) emits `protocol`
(`negotiation.replay.v1`, `sim.nim:53`), `names` (aliases), `policyNames`, `config` with `seed`,
`matches`, `maxTurns`, `sampled`, `itemNames` and the full `schedule` including **both** seats'
private values (`scheduleJson`, `sim.nim:647-662`), `events`, `results` — self-sufficient, and
`replay_check.py:44-69` asserts each of them plus `pool·v == 10` per schedule entry. Event
vocabulary (`eventToJson`, `sim.nim:666-706`) matches the note's table field for field, with the
accepted `kind`→`matchKind` rename (`types.nim:41-44`, `sim.nim:674`, asserted at
`test_sim.nim:345`); unset `text`/`notes` are omitted (`:703-706`) and restored as `""`
(`:708-722`), tested at `test_sim.nim:331-403`.

**Re-derivation.** `replayMatch` (`sim.nim:743-796`) re-runs `initSim` from the seed, replays only
`offer`/`accept` through the same `apply*` procs, treats `matchEnd` as a checkpoint (`:788-791`) and
applies `end` through the same `settle` the live server calls (`:792-795`), so a `deadline` replay
re-derives like a `complete` one. It cross-checks the whole `match` event against the seeded plan
and raises "does not match the seeded schedule" (`:757-765`), and cross-checks `worth` on offers and
`take`/`payoff` on accepts against the re-derived values (`:766-787`) — reading the re-derived event
**by recorded index** (`let at = sim.events.len`, `:771`, `:780`), which is the fix in `1973f80`.
`frames.len == events.len + 1` and the final frame is byte-equal to the live `tableStateJson()` for
both end reasons (`test_sim.nim:287-302`); tampering is rejected (`:304-329`). The viewer derives
its display from that same re-derivation and from nothing else: the wasm entry
(`replay-viewer/negotiation_replay.nim:22-53`) builds `states` from `replayMatch`, and
`attachReplay` reads `payload.states` only (`chrome_common.js:481`, `:501-504`).

**Static viewer.** `game.replay_viewer.bundle == "static-replay-viewer"`
(`coworld_manifest_template.json:15-18`); `tools/build_replay_viewer.sh` exists, is mode 100755, is
the `coworld build` hook (asserted in `ci.yml:256-267`), `mkdir -p`s the parent before the
containment check (`build_replay_viewer.sh:21`), copies `chrome_common.js` beside the rest
(`:51-56`), and keeps babel's assertions plus `grep -q 'data-replay-loaded'` (`:63-65`). The bundle
contacts only the `?replay=` URL (`static_replay.js:131`, `:146-149`). `/client/replay` exists only
as the **live** broadcast page route (`server.nim:525`) and is not declared anywhere in the manifest
(no `replay_viewer` key other than the bundle; grep of the manifest confirms).

**Viewer executes.** CI run **33022161451** on `main` at `5f23877`: `test`, `docker-smoke`,
`wasm-viewer` all green; `wasm-viewer` `needs: docker-smoke` (`ci.yml:243`) and its
`Load the bundle in a real browser` step ran with `--soak 8 --strict-text-bounds`
(`ci.yml:351-356`), reporting `{"loaded":true,"ms":288,…,"feed_lines":54}` and
`canvas text: 4211 drawn, 0 never inside … 0 ellipsized`. The artifact `viewer-smoke.json` shows
`signals.bridge: ["loading","ready"]`, `bridge_ready: true`, `soak.moved: true`
(tick `0/46 → 9/46 → 12/46`), `page_errors: []`, and three scrub seeks that changed the clock.
No step is `continue-on-error`.

**MODULARIZE / bootstrap pairing.** `replay-viewer/config.nims:32-45` links `-s MODULARIZE=1
-s EXPORT_NAME=NegotiationReplayModule` and exports `_neg_load_replay/_neg_payload_ptr/_neg_payload_len/
_neg_error_ptr/_neg_error_len`; `static_replay.js:141` calls the factory
`NegotiationReplayModule()` and `:94-104` calls exactly those symbols. Both files are babel's, from
the same starter, with only the renames (diffed against
`/workspace/starters/cogame-babel/replay-viewer/`). No `onRuntimeInitialized` anywhere in the tree.

**Load signal.** `data-replay-loaded="true"` is set in `static_replay.js:123-126`, from
`attachReplay`'s `onFirstFrame`, which `chrome_common.js:556-563` invokes **after**
`renderer.draw(view)` on the first painted frame, and `tell("ready")` is posted after the attribute
(order gated by `chrome_check.py:92-100`). `data-replay-error` is set in `fail()`
(`static_replay.js:56`) on a missing `?replay=`, a wasm rejection, a fetch failure or a fetch
timeout. Babel's unconditional `setAttribute` after `makeRenderer` was removed
(`cogame-babel/client/renderer.js:1310`), so the marker cannot be set without a painted frame.

**Chrome provenance.** `client/replay_broadcast.html` is babel's `client/replay.html` with **nothing
removed**: the diff is the title, wordmark, clock text, the appended `#gameblock` under a banner
comment (`:20-25`), the `tick-clock` class on `#pos` (`:36`), the `chrome_common.js` script tag
(`:43`), `relayout()` inside `fit()` (`:50`), and the `Babel`→`Negotiation` renames — all 82 lines
against the starter's 80. `client/chrome.css` is babel's 441 lines byte-identical followed by an
appended block under a banner (`:444-588`); nothing above it is edited. `client/chrome_common.js`
is babel's chrome half function-for-function (verified by extracting and diffing each of the 20
named functions), see N5. `#viewpanel` is absent everywhere, and `chrome_check.py:54-55` asserts it
stays absent. The frozen id set is present in both pages and gated by `chrome_check.py:47-58`.

**Transport rules.** (a) `relayout()` measures `#transport` and writes `--band`/`--hudscale` on
`document.documentElement` (`chrome_common.js:257-268`), bound to load/resize (`:569-570`) and to the
feed toggle (`:274-289`). (b) No overlay sits in the band: `#loading` is re-anchored to
`bottom: var(--band, 0px)` (`chrome.css:523`), `#gameblock` is in normal flow above the board
(`chrome.css:483-492`), `#endscreen`'s containing block is `#board-wrap`, which already stops above
`#transport` (`chrome.css:526`, accepted deviation). (c) `#endscreen` is shown with the class its
inherited rule uses — `container.classList.toggle("show", …)` (`renderer.js:462`) against babel's
`#endscreen.show { display: flex; }` (`cogame-babel/client/chrome.css:381`) — and **every** seek
takes it down: `setIndex(next, true)` calls the endcard painter with `show = false` before
repainting (`chrome_common.js:509-516`), and the only seek entry points are the scrub
pointer-down/move (`:360-367`), the beat buttons (`:341-344`), and the play button's restart
(`:496-498`). Neither this page nor the starter's binds keyboard or back/forward seeks. (d) Beats
are `<button type="button" aria-label=…>` that call `onSeek(i + 1)` (`chrome_common.js:328-346`);
the game emits `offer|accept|deal|nodeal|end` (`renderer.js:661-682`) and `chrome.css:546-583` has a
rule for each of the five, gated by `chrome_check.py:78-89`. `.round-span`/`.round-sep` per match are
babel's, unchanged (`chrome_common.js:313-327`).

**360 px legibility.** `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (`chrome.css:462`),
`.plate-label { display: none }` under `640px` (`chrome.css:476-480`), pool row wraps under 420 px
(`renderer.js:259` `narrow`, `:200-224` `wrap`), value strips collapse to `2·1·2`
(`renderer.js:300-303`), item icons floored at 10 px (`renderer.js:209`), scorebug is 3 columns
(`chrome.css:459`). `chrome_check.py:107-118` gates the first two. The fixture renders at 360/720/
1280 px with `never_inside: 0`.

**Manifest.** `num_agents: 3` in variant `standard` (`:358`), variant `sprint` (`:381`) and
`certification.game_config` (`:402`); `certification.players` names the three declared runnables one
each (`:410-419`); `game.docs = {readme, pages[rules.md, writing-a-policy.md]}` in the
`{"type":"text","value":…}` shape; `game.protocols` carries both `player` and `global` as text
objects (`:238-247`); every array property in `config_schema` has `minItems`+`maxItems`;
`results_schema` bounds all seven arrays to 3 and documents `complete | deadline`; the secret URI is
`secret://coworld/negotiation-games/anthropic_api_key` (`:28`), whose namespace equals
`game.name`; no `game.tags`, no top-level `version`, no `display_name`, `episode_timeout_minutes: 20`
at the top level. `manifest_check.py` re-asserts all of this **and** runs the installed CLI's
`_load_template_manifest` + `validate_coworld_manifest_game_configs` (`:181-206`); the `test` job is
green.

**Seat invariants in the smoke.** `docker_smoke.sh:130-171` enforces the four invariants
(`num_agents` present; a positive non-bool int; `len(certification.players) == it`;
`len(certification.game_config.players) == it`) plus the independent `SMOKE_SEATS=3` cross-check
(`:56`, `:166-171`), each exiting non-zero with a `SEAT-COUNT FAIL:` prefix, before any container
starts. Grepping the docker-smoke log of run 33022161451 for `SEAT-COUNT FAIL` returns nothing; the
job printed `game=negotiation-games seats=3 …` and `smoke OK: seats=3 … reason=complete`. The
accepted `SMOKE_CONFIG_JSON` delta strips `num_agents`/`players`/`tokens` before merging
(`:116-124`), so the seat count still comes only from the fixture — the diff against
`templates/tools/ci/docker_smoke.sh` is that block plus the three substitutions and their comments.

**Release order and scaffold.** `coworld-release.yml` is the template with only the slug/image
substitutions; its steps run Build (`:159`) → Certify (`:173`) → Upload the policies (`:212`) →
Upload the Coworld (`:310`) → Put the Coworld secret (`:348`). All three workflows are present;
`tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both mode 100755.
`tools/ci/policies.json` declares four policies on `/bin/negotiation-player`: two `PLAYER_PROMPT`
champions (the second carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) and two
`PLAYER_SCRIPTED` fillers; both prompt bodies match the note's §Decisions text. The checklist's
placeholder gate (`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files) matches nothing and
exits 0.

**Both name spaces.** Agents see aliases only: `tableNames` (`sim.nim:181-192`), prompts composed
from `sim.names` (`llm.nim:237-244`, `:301-336`); the player frames carry the alias
(`server.nim:96-117`, `:443-450`) and never `policyNames` (only `snapshotJson` adds it,
`server.nim:90`); the final frame to players swaps in aliases deliberately
(`server.nim:187-199`). `resultsJson` uses policy names (`sim.nim:546`). The viewer maps aliases to
policy names for non-baseline seats (`chrome_common.js:116-149`). Test 13
(`test_sim.nim:459-490`) greps every composed system and user prompt of a whole episode for three
distinctive policy names.

**Scripted baseline plays full episodes legally.** `test_bot.nim:53-89` runs 5 seeds × 3 pairings to
the natural end, asserting `reason == "complete"`, `started == settled == matches`, `0 ≤ take[i] ≤
pool[i]` on every offer, `turn ≥ 2` on every accept, `matchEnd.turn ≤ maxTurns`, and
`fallbacks == 0`. `reservationFor`/`bestOffer` (`llm.nim:151-189`) implement the note's haggler and
hardliner formulas literally, including the tie-breaks. The grid measurements are printed by the
tests themselves in CI: `haggler-vs-haggler: 102/102 deals, mean joint 14.89`,
`haggler vs hardliner behaviour differs in 96/102 matches`,
`mixed matches: 100, hardliner mean 8.08 vs haggler mean 6.7`.

**Accepted deviations, verified as described (not filed as findings).**
1. `tests/test_bot.nim:141-171` replaces the note's "≥ 10 no-deals" clause with a
   non-interchangeability property over the same seeded matches (≥ 40 of ≥ 100 matchEnds differ);
   `reservationFor` and `bestOffer` still implement the note's pinned algorithms exactly, and the
   no-deal path itself is still tested (`test_sim.nim:250-269`).
2. `match` event field `kind` → `matchKind` (`types.nim:41-44`, `sim.nim:408`, `:674`, `:715`),
   because the JSON key `kind` already carries the event kind.
3. `docker_smoke.sh:108-124` `SMOKE_CONFIG_JSON` merging with `num_agents`/`players`/`tokens`
   stripped; every seat-count check downstream is unchanged.
4. `tools/ci/renderer_fixture.html` drives the real `dist/static-replay-viewer/index.html` in an
   iframe on a rewritten real smoke replay (`make_fixture_replay.py`) instead of a synthetic
   payload; it self-checks the payload's 200/400-rune strings and both stamps (`:256-287`), installs
   its own `fillText` hook in the iframe (`:91-120`), fails if it counted < 40 draws (`:300-304`),
   and only then sets `data-replay-loaded` (`:315`). The rewritten last match is legal input to the
   wasm: every rewritten offer takes the whole pool with `worth = [10, 0]`, which is what
   `applyOffer` recomputes (`sim.nim:464-465`), so `replayMatch`'s cross-check passes — and CI
   confirms `loaded: true`.
5. `#endscreen { bottom: 0 }` inside `#board-wrap` (`chrome.css:524-526`); `#pos` gained
   `tick-clock` (`replay_broadcast.html:36`, `index.html:36`), which is the selector
   `viewer_smoke.mjs:428` reads for the playback tick; the hook object carries more redirected call
   sites than the note's three-change list names; `makeNameMap` dropped babel's `glyphs` parameter
   (`chrome_common.js:125`).

**No test was loosened this run.** `git log -p -- tests/` over the run's commits shows two commits
touching `tests/`: the initial import (`35a427b`) and `1973f80`, whose only test change is
`-import std/[json, math, monotimes, os, strutils, times, unittest]` →
`+import std/[json, monotimes, os, times, unittest]` (two unused modules dropped). No assertion
deleted, no tolerance widened, no skip added, no test file removed.

---

## Could not determine

- **Whether all 265 `ellipsized` canvas draws in the fixture are remarks** (F2). The harness reports
  only a count; `renderer_fixture.html:122-144` returns `samples: []`. I inferred it from the code
  (only the table-talk label at `renderer.js:307-313` can exceed its box; names, value strips, pool
  label, chips and stamp text all fit at all three widths under their own `maxWidth`s) and from the
  fixture caption "longest 66 chars" in the uploaded screenshot. What would settle it: having the
  fixture's `report()` return the ellipsized strings, or a per-width screenshot diff.
- **Whether the game thread can raise and leave the container serving with no artifacts.**
  `runGame` (`server.nim:243-375`) has no top-level `try`, so an escaping exception would kill the
  thread and leave mummy serving until the platform's own timeout. I could not construct a
  reachable path: `client.decide` catches `CatchableError` (`llm.nim:496`), and the
  `except NegotiationError` branch's own fallback (`server.nim:357-362`) is computed from the live
  sim in `phOffer` and is legal by construction. Only a non-`CatchableError` defect (e.g. an
  `IndexDefect`) would escape. What would settle it: a fault-injection test, or wrapping the loop —
  neither exists, and the starter has the same shape.
- **Hosted behaviour of the LLM path.** `docker_smoke.sh` runs without `ANTHROPIC_API_KEY`
  (log line "no ANTHROPIC_API_KEY: the game must complete on its scripted baselines"), so the
  retry/hint/transport branches of `llm.nim:411-504` are exercised only by unit tests
  (`test_bot.nim:196-308`), never end to end. What would settle it: a keyed smoke or the phase-60
  hosted episode's `results.fallbacks`.
- **Whether the byte-cut prompt (F1) can actually produce a rejected model request.** It needs a
  prompt over 4000 bytes whose 4000th byte falls inside a rune, and the provider's tolerance of
  invalid UTF-8 in the request body is not observable from the tree. What would settle it: a unit
  test on the cap, or a hosted episode with a long multibyte `PLAYER_PROMPT`.

---

## Summary of findings

| # | Finding | Severity |
|---|---|---|
| F1 | `server.nim:492-493` cuts the 4000-char player prompt on a **byte** boundary (`prompt[0 ..< MaxPromptLen]`), while the note and checklist item 9 require rune-safe truncation for prompts; the prompt does not reach the replay, and the code is byte-identical to babel's. | blocking-candidate (checklist 9) |
| F2 | `renderer.js:307-313` draws the 200-rune table talk as one `ellipsize`d line in a `w * 0.3` box sized by eye rather than from `MaxMessageLen`; CI's renderer fixture reports 265 ellipsized draws, "longest 66 chars", and `renderer_fixture.html:305-309` treats that ellipsis as its pass condition. | blocking-candidate (checklist 15) |
| F3 | `sim.nim:181-187` + `:284-288` use two independently seeded RNG streams (aliases, schedule) under a comment claiming one; determinism and re-derivation are unaffected. | advisory |
| F4 | `renderer.js:635-639` / `:255-363` never read `view.effects`, so the note's offer slide-in and stamp fade are not implemented. | advisory |
| F5 | `renderer.js:243-252` and `:560-562` omit the note's `0 – 0` on the no-deal stamp, the final item split on the deal stamp, and the per-seat `Final — Sprocket 25 pts (0.62)` feed line. | advisory |
| F6 | `renderer.js:604-616` builds `#matchbar` from emitted `match` events, so a `deadline` replay shows fewer chips than the note's "one chip per scheduled match". | advisory |
| F7 | `chrome_common.js:53, 105, 201, 296` carry four defensive edits to inherited bodies beyond the note's three named changes. | advisory |
| F8 | `chrome.css:1-441` (inherited, correctly unmodified) uses literal px, so the note's "every chrome font size and pad is `calc(… * var(--hudscale))`" holds only for the appended block. | advisory |
| F9 | `negotiation_player.nim:55-56` blocks in whisky's `receiveMessage` with the default `timeout = -1`; bounded in practice by the game's `final` frame and `quit(0)`, and identical to the starter. | advisory |
| F10 | `sim.nim:28` (`MaxMatchesCap`), `llm.nim:204-206` (`scriptedAction`) and the registered `phaseText` hook (`renderer.js:704`) are unreachable. | advisory |

No finding was identified against checklist items 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13 or 14; the
evidence I traced for each is in "Traced and consistent" above.
