# r1 review — fog-of-war-boards

Range: `935a2a9..791cf71` (whole repo at `791cf71eb702cbf060812483a98d2bf6ea9b16d6`; the substantive
diff is `a15121b` + the fixture/contrast fix `791cf71`)
Files read: 41 (every `.nim`, `.js`, `.mjs`, `.html`, `.css`, `.nims`, `.sh`, `.yml`, `.json` in the
tree, plus the babel starter's four viewer files, `client/renderer.js`, `client/chrome.css` and the
three client pages for provenance diffs, plus `templates/{ci,coworld-release,coworld-submit}.yml`
and `templates/tools/ci/{docker_smoke.sh,viewer_smoke.mjs}`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15)
CI evidence: run `33031534557`, `headSha 791cf71eb702cbf060812483a98d2bf6ea9b16d6`, conclusion
`success` (`test` 31 s, `docker-smoke` 1m30s, `wasm-viewer` 1m56s); artifacts `smoke-replay`,
`viewer-smoke`, `static-replay-viewer` downloaded and read.

Method note: every "Observed" below was read at the reviewed sha. Where I reasoned from the code
rather than ran it I say **inferred**; where only a run would settle it I say **untested**.

---

## Blocking

### B1 — the worst-case renderer fixture asserts its remark is ≥ 20 runes, not full-length

- Where: `tools/ci/renderer_fixture.html:318-329` (assertion), `:82-89` (`fullSay`),
  `client/renderer.js:36` and `:667-668` (the 80-rune cap the fixture is meant to pin)
- Observed:

  ```js
  var says = doc.querySelectorAll(".plate-say");
  if (says.length !== 2) { problems.push("expected a say band on both plates …"); }
  says.forEach(function (node) {
    var text = (node.innerText || "").trim();
    if (Array.from(text).length < 20) {
      problems.push("the say band at " + width + "px carried only " +
        Array.from(text).length + " runes");
    }
  });
  ```

  `fullSay(seat)` (`:82-89`) builds exactly 80 runes; `updateScorebug` puts
  `say.slice(0, MAX_SAY_LEN)` (`renderer.js:668`, `MAX_SAY_LEN = 80` at `:36`) into `.plate-say`.
  I confirmed from the fixture screenshot (`dist/fixture/viewer-smoke.png` in the `viewer-smoke`
  artifact of run 33031534557) that both bands currently carry the whole 80-rune line on one row,
  unclipped. The **assertion floor**, however, is 20 runes. A renderer change to
  `say.slice(0, 30)`, or a fixture edit that shortened `fullSay` to 30 runes, would leave this
  fixture green while testing nothing above 30 runes.
- Checklist item: 15, fourth bullet — "The fixture asserts its own strings are still full-length —
  one quietly shortened remark leaves it passing while testing nothing."
- Why blocking: the checklist names this assertion explicitly and the shipped assertion is a
  quarter of the cap. The gate that exists solely to catch a quietly shortened remark accepts a
  remark shortened by 75 %. (The remark is full-length *today* — this is a gate-strength finding,
  not a rendering defect.)

### B2 — the fixture's `ellipsized` counter reports remarks, permanently, because the fixture pads its own remark with U+2026

- Where: `tools/ci/renderer_fixture.html:82-89`; detector at `tools/ci/viewer_smoke.mjs:367-371`;
  evidence in run 33031534557, job `wasm-viewer`, step `Load the worst-case renderer fixture`
- Observed: `fullSay` pads the base sentence to 80 runes with literal `\u2026`:

  ```js
  var runes = Array.from(base);
  while (runes.length < 80) runes.push("\u2026");
  return runes.slice(0, 80).join("");
  ```

  Base lengths are 70 and 72 runes, so the shipped remarks end in 10 and 8 consecutive `…`.
  `viewer_smoke.mjs:368` classifies any draw matching `/\u2026\s*$/` as ellipsized. The CI step
  therefore printed:

  ```
  canvas text: 33 drawn, 0 never inside the canvas (0 draws crossed an edge), 8 ellipsized (--strict-text-bounds)
    ellipsized: "fog-of-war-boards-carto…"
    ellipsized: "his chain has to cross d3 and i will sit on it until he pays"
    ellipsized: "they are bridging low so i take c2 now and let them waste a "
    …(the two remarks repeated once per width, 360 / 640 / 1280)
  ```

  Six of the eight are the two *remarks*; two are the nameplate `clampName` cut
  (`chrome_common.js:117-120`, 24 chars).
- Checklist item: 15, third bullet — "Ellipsis is a design choice for **labels** … and a defect for
  **sentences**. If `ellipsized` counts a remark rather than a nameplate, the box is too small."
- Why blocking: the named condition holds in the cited CI log, and — the concrete consequence —
  the signal is now permanently non-zero on remarks, so a *real* renderer ellipsis on a `say` can
  never again be distinguished from the fixture's own padding in this repo's CI output.
  **Stated plainly so it can be judged accurately: the box is not too small.** The fixture's own
  clip test (`renderer_fixture.html:271-274`, `scrollHeight > clientHeight + 2 &&
  overflow === "hidden"`) reported nothing at any of the three widths, `never_inside` was 0, and
  the screenshot shows the full line on one row. The mechanism is the padding character, not the
  band.

---

## Non-blocking

### N1 — a cell filled by the *opponent* silently deletes the seat's own sensed-empty record

- Where: `src/fogboards/sim.nim:425-431`
- Observed:

  ```nim
  else:
    ## 7a: the cell was empty.
    sim.board[cell] = occupantOf(seat)
    inc sim.stones[seat]
    placed = true
    for other in 0 ..< Seats:
      sim.sensedEmptyAt[other].del(cell)
  ```

  The loop runs over **both** seats. Trace, in `recon-hex-5` (the only shipped variant with
  `sense > 0`): seat 0 senses `b3` empty on ply 6, so `sensedEmptyAt[0][b3] = 6`. Seat 1 places on
  `b3` on ply 9. `applyAttempt` deletes `sensedEmptyAt[0][b3]`. On ply 10, `userPrompt`
  (`src/fogboards/llm.nim:456-460, 474-480`) classifies `b3` by
  `elif cell in sim.sensedEmptyAt[seat]: stale.add(cell) else: untouched.add(cell)`, so `b3` moves
  out of `CELLS YOU SENSED EMPTY (may be stale)` and into `CELLS YOU HAVE NEVER TOUCHED` — while
  `refereeLog` (`llm.nim:341-376`) still shows `ply 7 — you sensed b2 — … b3 empty …`.
- What the note says: design.md:47-49 — "The **only** channel through which a seat learns anything
  about the opponent is the referee's answer to the seat's own action"; step 6 (design.md:169-173)
  and step 7 (design.md:174-179) describe no deletion of the *other* seat's timestamp; the
  "Hidden from a seat, exhaustively" list (design.md:718-723) includes "every opponent action".
  **Inferred:** a model that diffs its sensed-empty list across plies learns that the opponent
  played on that cell — a fact the referee never gave it.
- Also: design.md:926-928 pins the belief-board dot as fading with staleness
  (`max(0.15, 1 − (ply − sensedAt) / 8)`, implemented at `client/renderer.js:516-529`). With the
  entry deleted, the dot vanishes on the fill rather than fading.
- Not a named checklist item, so not blocking. Untested: no shipped CI path exercises `sense > 0`
  (the cert fixture is `dark-hex-5`, `sense: 0`).

### N2 — an attempt decided by the baseline because the LLM client is disabled is recorded as `scripted: false`

- Where: `src/fogboards/server.nim:306-307` and `:320-321`; `src/fogboards/llm.nim:688-689`
- Observed: `decide` returns `scriptedDecision(...)` with `fellBack` left `false` when
  `client.disabled`; the server then records the event with `scripted = seatScripted`, i.e. the
  seat's *declared* `PLAYER_SCRIPTED` flag, not what actually decided the ply. Evidence from the
  CI smoke replay (`smoke-replay` artifact, run 33031534557): seat 0 is
  `fog-of-war-boards-player` (a prompt seat) and every one of its five attempts carries
  `"scripted": false, "fellBack": false`, although `docker_smoke.sh` runs with no
  `ANTHROPIC_API_KEY` and the log line `fogboards llm: no LLM credentials; using scripted fallback`
  fired. `results.fallbacks == [0, 0]`.
- What the note says: `types.nim:57` documents `scripted` as "decided by a scripted baseline";
  design.md:596 lists it in the `attempt` event. Checklist 8's requirement (the *parse/transport*
  fallback is recorded) **is** met — `server.nim:312-313` increments `fallbacks[mover]` on
  `decision.fellBack` and `llm.nim:711-712` prints the greppable `falling back` line.

### N3 — the wall-clock guard's worst case lands ~2–3 s past 60 % of the episode timeout

- Where: `src/fogboards/server.nim:216-217` (`worstPlySeconds = 2*llmTimeoutSeconds + 2 = 62`),
  `:276` (the guard), `:296-302` (the 4 s LLM spacing sleep, *after* the guard), `:347-348`
  (turnDelay)
- Observed, traced: the guard admits a ply only while `now + 62 ≤ playDeadline`. The spacing sleep
  (up to `DerivedPlySpacingSeconds = 4`, `llm.nim:39`) then runs, then `decide` can take
  `2 × llmTimeoutSeconds = 60 s`, then `turnDelayMs` (≤ 250 ms after `sampleEpisode`'s clamp,
  `sim.nim:80-82`). Worst case the settle happens at `playDeadline + ~2.3 s`; `finishEpisode`
  sleeps 500 ms before writing, so `results.json` lands at ≈ 723 s of 1200 (60.25 %). The spacing
  sleep is only positive when the *previous* ply finished in under 4 s, so the 4 s and the 60 s
  can only combine after a fast ply.
- What the note says: design.md:154-156 and :388-392 define the guard exactly as implemented
  (`worstPlySeconds = 2 × llmTimeoutSeconds + 2 = 62`) and do not fold the 4 s spacing floor into
  it. Checklist 5's "inside 60 %" is 720 s. Reported as arithmetic, not as a hang: every wait is
  bounded, and the shutdown grace (`ShutdownGraceMs = 20_000`, `server.nim:38, 208`) plus the
  1200 s platform kill leave ~450 s of headroom.

### N4 — `sweepCell` restarts the corridor at offset 0 after a shift

- Where: `src/fogboards/llm.nim:288-298`
- Observed: `let lane = (n div 2 + sim.probes[seat]) mod n`, then `for offset in 0 ..< n` returning
  the first cell of the lane that is in `legalAttempts`.
- What the note says: design.md:345-349 — "on `OCCUPIED`, shift the whole corridor one step … and
  **continue from the same offset**". The code restarts the walk at offset 0 of the new lane. The
  lane arithmetic and the wrap are as the note describes; only the resume point differs. Every
  produced attempt is legal (test 14, `tests/test_bot.nim:85`) and CI reports
  `probe/sweep disagreement: 1750/2450 = 0.714`, well past the note's 30 % floor.

### N5 — the reply-schema error caps are 160 in two places, not the note's 200; two error slices are byte slices

- Where: `src/fogboards/llm.nim:35` (`MaxErrorLen* = 200`), used only at `:708`; `:536-537` uses
  160; `:664-666` uses 160; `:644` `response.body[0 .. min(response.body.high, 400)]` and `:652`,
  `:657` `[0 .. min(…, 300)]` are **byte** slices of an HTTP body
- Observed: the 400/300-byte slices can cut a multi-byte rune. They become a `FogError` message,
  which reaches only `echo` at `:707-708` after `cleanText(error.msg.replace("\n", " "), 200)`;
  `cleanText` (`:161-167`) only re-cuts when `runeLen > 200`, so a shorter message keeps the
  broken tail byte on stdout.
- What the note says: design.md:748-750 — "any error text that reaches an event or the log (200)".
  **No error text reaches an event or the replay in this repo**: `GameEvent` has no error field
  (`types.nim:47-63`) and the server's exception fallback passes empty `say`/`notes`
  (`server.nim:339`). So checklist 9 is not falsified; this is stdout hygiene only.

### N6 — the replay-page `<script>` block appended under the banner registers nothing; registration lives in the game block

- Where: `client/replay_broadcast.html:74-89`, `client/global.html:52-63`,
  `client/player.html:60-71`; `client/renderer.js:844-845` and `:926-927`
- Observed: the appended block calls `FogChrome.relayout()` and binds `resize` only. `setFeedText`
  / `setEndColumns` are called from `attachLive` / `attachReplay`.
- What the note says: design.md:878-879 — "**Appended:** one `<script>` block at the end that
  registers the game's feed text and endcard columns with `FogChrome`." Functionally equivalent
  (the injections happen before the first `renderFeed`/`updateEndscreen` call, both of which run
  inside the attach path); the note's placement is wrong, not the code.

### N7 — a seventh unlisted text edit in the four copied pages: `#clock` "ROUND 0" → "PLY 0"

- Where: `replay-viewer/index.html:13`, `client/replay_broadcast.html:13`,
  `client/global.html:13`, `client/player.html:13`
- Observed: `diff` against `/workspace/starters/cogame-babel` at `d55d999` shows, for all four
  pages, exactly: `<title>`, `#wordmark` inner text, `#clock` inner text, the added
  `chrome_common.js` `<script src>`, `BabelRenderer` → `FogRenderer`, and (player.html only) the
  wordmark string inside `onFrame`. **Nothing is removed from any of the four pages.**
- What the note says: design.md:806-810 and :875-877 enumerate the title, the wordmark, the script
  list and the `bindFeedToggle` rename; the `#clock` placeholder text is not named. Consistent with
  the note's intent ("everything human-facing renders it as PLY n", design.md:604).

### N8 — the `start` event omits `round`; the `end` event's `round` is `plies − 1` for connection/line/board-full and `plies` for ply-cap/deadline

- Where: `src/fogboards/sim.nim:642-643` (`if event.round >= 0: result["round"] = …`);
  `:351-356` (`settle` sets `event.round = sim.plies`) against the call sites at `:477`, `:491`,
  `:506` (before `inc sim.plies` at `:509`) and `:512`, `:362` (after)
- Observed in the CI smoke replay: `{"kind": "start"}` with no `round`, and
  `{"kind": "end", "round": 8, …}` while `results.plies == 9`.
- What the note says: design.md:594 gives `start` as `{kind, round: -1}`. No consumer is affected:
  `eventFromJson` defaults to −1 (`sim.nim:681`), `renderFeed` and `buildScrub` special-case
  `kind === "start"` and `kind === "end"` (`chrome_common.js:155-156`, `:329-330`), and
  `markPlyBeat`'s label guards on `typeof event.round === "number" && event.round >= 0`
  (`chrome_common.js:427-428`).

### N9 — `.plate-say`'s reserved band is sized by constants, not by measuring the cap in the render font

- Where: `client/chrome.css:534-548` (`min-height: calc(13px * var(--hudscale));
  max-height: calc(40px * var(--hudscale)); overflow-wrap: anywhere; overflow: hidden;
  font-size: calc(10px * var(--hudscale))`)
- Observed: the band is emitted unconditionally, empty or not (`client/renderer.js:667-668`), so
  the scene does not jump when a remark lands — checklist 15's second bullet is met. But the
  height is a constant scaled by `--hudscale`, and an over-tall run is clipped by
  `overflow: hidden` rather than the band growing.
- What the note says: design.md:941-943 — "a **reserved band** sized from `MaxSayLen = 80`
  measured in the render font at the current `--hudscale`". The measurement is done in CI instead,
  by the fixture's `scrollHeight > clientHeight` check (`renderer_fixture.html:271-274`), which
  passed at 360 / 640 / 1280 px in run 33031534557.

### N10 — the fixture clamps every transcribed run into its scratch canvas, so `never_inside` cannot fire on DOM text

- Where: `tools/ci/renderer_fixture.html:284-293`
- Observed: `var x = Math.max(2, Math.min(box.left, scratch.width - width - 2));` and the matching
  clamp for `y`. Only a run wider than `scratch.width - 4` (1396 px) is reported, via the
  `clipped` array. So the `canvas_text.never_inside == 0` in the fixture's `viewer-smoke.json` is
  0 by construction for the transcribed DOM strings; the meaningful gates in that step are the
  `clipped` checks and the iframe's own canvas report read at `:354-361`.
- The file documents this deliberately (`:280-284`). Recorded so nobody reads the fixture's
  `never_inside: 0` as evidence about the scorebug or the feed.

### N11 — `transcribe`'s `var width` shadows its parameter, so the "text is clipped by its own box" message reports the wrong number

- Where: `tools/ci/renderer_fixture.html:254` (`function transcribe(width)`), `:284`
  (`var width = ctx.measureText(text).width;`), `:273`
  (`clipped.push(selector + " @" + width + "px")`)
- Observed: `var width` inside a function whose parameter is also `width` reassigns the parameter.
  On the first node the message reads `@undefined px`; afterwards it reports the previous node's
  measured text width instead of the viewport width. The pass/fail behaviour is unaffected — the
  entry is still pushed and still fails the fixture.

### N12 — `updateScorebug` truncates `say` on UTF-16 code units, not runes

- Where: `client/renderer.js:668` — `C.escapeHtml(say.slice(0, MAX_SAY_LEN))`
- Observed: the server already caps `say` at 80 **runes** on a rune boundary
  (`llm.nim:161-167`, `:597`), so this slice is normally a no-op. A `say` of 80 runes containing
  an astral character (e.g. an emoji, 2 UTF-16 units) would be cut mid-surrogate-pair here.
- Checklist 9 governs "every string that reaches the **replay**"; those are rune-safe and
  `tests/test_replay.nim:166-209` pins it (`validateUtf8() == -1`, strict `parseJson` round-trip,
  and an emoji sitting exactly on the cap surviving whole). This is viewer display only.

### N13 — smaller deviations from the note, each verified, none load-bearing

- `coworld-release.yml:173-181`: `coworld certify` is invoked without `--timeout-seconds 300`;
  design.md:1095-1096 says it passes it. The file is **byte-identical** to
  `templates/coworld-release.yml` after `<slug>/<IMAGE>/<SEATS>` substitution, so the note is
  describing something the template does not do. Checklist 12 does not require it.
- `src/fogboards/sim.nim:563-566` (`phaseText`): `"sensing"` whenever `config.sense > 0`, so
  `recon-hex-5` never reports `"moving"` and the other three never report `"sensing"`.
  design.md:673 only enumerates the set.
- `src/fogboards_player.nim:54`: `newWebSocket(url)` is outside the `try/except`; only the receive
  loop is wrapped (`:64-90`). design.md:420-422 asks for the receive loop, which is done.
- `src/fogboards/server.nim:470-497`: an unparseable `scripted` value makes `parseBaseline` raise
  (`llm.nim:83-84`), which the outer `except CatchableError` swallows — dropping the *prompt* for
  that slot as well as the baseline.
- `tests/test_sim.nim:296` and `:368` use 75 seeds × 2 baselines × 4 variants (600 episodes each);
  design tests 10 and 12 (design.md:1143, :1151) say "300 seeded episodes". Episode count exceeds
  the note; distinct-seed count does not.
- `client/renderer.js:773-774`: `guessAccuracy` of exactly 0 renders `"0%"`, not the `"—"` the
  code reserves for a non-number. Visible in the smoke endcard screenshot.

---

## Traced and consistent

**Resolution order (design.md §"Resolution order for ply p")**
- `sim.nim:364-369` `beginPly` returns `sim.mover`, which `applyAttempt` set at step 10.
  `sim.nim:493-496`: `if placed or sim.config.abrupt: sim.mover = 1 - seat` — a placement always
  flips, a collision flips only when abrupt. Pinned by test 6 (`tests/test_sim.nim:154-166`) for
  both values of `abrupt`, including the "seat 1 moves again" branch.
- `server.nim:271-288`: step 1 and step 2 are inside one `withLock`, **before** any observation is
  built; `epochTime() + guard > playDeadline` → `state.sim.endEarly()` → `settle("deadline",
  "wall-clock")` (`sim.nim:358-362`) and `mover = -1` → loop break. Never mid-ply.
- Steps 6–12 in order: `server.nim:315-321` applies sense then attempt; `sim.nim:397-512` does
  7a/7b (`:418-431`), 8 (`:447-459`), 9 (`:461-491`), 10 (`:493-496`), 11 (`:498-506`, gated on
  `mode == mPhantomTtt` and `placed`), 12 (`:508-512`). Step 13's `sleep(turnDelayMs)` at
  `server.nim:347-348` and the LLM spacing floor at `:296-302`.
- Step 6 `applySense` (`sim.nim:371-395`): rejects `sense <= 0`, a wrong mover and an anchor not in
  `legalAnchors`; opponent cells become permanent `known[seat]`, empty cells get
  `sensedEmptyAt[seat][cell] = sim.plies`. Test 11 (`tests/test_sim.nim:323-363`) checks the
  window is truthful, that seat 1 learns nothing from seat 0's window, that sensed-empty is not
  occupancy knowledge, that an off-board anchor raises, that `sense == 0` emits no `sense` event,
  and that `senses == recon.plies` when `sense == 2`.
- Ply bound: `sampleEpisode` clamps `maxPlies` to `2 * size * size` (`sim.nim:72-83`); test 7
  (`test_sim.nim:168-184`) runs 300 seeds × 4 variants × 2 baselines and asserts
  `plies <= maxPlies` and `reachedCap == 0` in the Hex variants.

**Decision path (checklist 8)**
- `llm.nim:678-714`: `for attempt in 0 .. 1` — one call plus exactly one retry; `:693-694` appends
  `retryHint` on the second pass only; `:668-676` prints `legalAttempts` (and `legalAnchors` when
  `sense > 0`) through the *same* procs the validator calls (`sim.nim:164-186`). On the second
  failure it falls through to `scriptedDecision(...)` with `fellBack = true` and prints
  `fogboards: seat N falling back to the probe baseline`.
- Tolerant parse: `extractJsonObject` (`llm.nim:529-540`) takes first `{` to last `}`;
  `parseCellNode` (`:542-584`) accepts `[col,row]`, case-insensitive algebraic with leading junk,
  internal separators and trailing prose. `guess` never rejects a reply (`:599-615`): capped at 6
  entries, each `cleanText(entry, 4)`, unparseable or already-known entries `continue`d.
- Legality probe on a **copy** (`llm.nim:700-704`): `var probe = sim`, sense then attempt, so an
  illegal reply never touches the live sim and the retry carries the hint.
- `client.disabled` short-circuits (`:688`, `:709-710`): no retries, no network waits. Pinned by
  `tests/test_bot.nim:194-208`.
- Fallback counter: `server.nim:312-313` on `decision.fellBack`, plus `:333-334` in the
  belt-and-braces exception path. Surfaced in `results.fallbacks` (`sim.nim:539`) and in
  `playerStateJson.seat.fallbacks` (`server.nim:117`).

**Every wait and its bound (checklist 5)**
- LLM: `client.curl.post(url, headers, $body, client.timeoutSeconds)` (`llm.nim:642`), timeout
  from `config.llmTimeoutSeconds` (default 30, schema 5..300).
- Player connect: `while epochTime() < connectDeadline` with `sleep(200)`
  (`server.nim:223-231`), `playerConnectTimeoutSeconds` default 180.
- Ply guard: `server.nim:276`, `guard = 2 * llmTimeoutSeconds + 2` (`:216-217`).
- LLM spacing floor: `server.nim:296-302`, `plySpacing` = `plySpacingSeconds` or the derived 4
  (`server.nim:212-214`, `llm.nim:39`), and it gates **LLM plies only**
  (`let usesLlm = not (seatScripted or client.disabled)`), which is why the all-scripted cert path
  is fast — CI: `cert fixture: 9 plies, ending connection, 6 ms`.
- Shutdown grace: `sleep(ShutdownGraceMs)` = 20 s then `quit(0)` (`server.nim:38, 206-210`).
- No unbounded loop: the `while true` in `runGame` exits on `sim.done` or on the guard; each
  iteration either settles or increments `plies`, which is capped. No blocking read on the game
  side.

**Truncation (checklist 9)**
- One shared `cleanText(text, cap)` at `llm.nim:161-167` using `runeLen` / `runeSubStr`, with `…`
  appended so the result is exactly `cap` runes. Applied to `say` (80, after `oneLine`,
  `llm.nim:597`), `notes` (400, `:598`), each `guess` entry (4, `:606`), the delivered prompt
  (4000, `server.nim:474`) and the echoed error (200, `llm.nim:708`).
- Test 20 (`tests/test_replay.nim:166-209`) feeds 400 × `日` + `🜁`, asserts
  `say.runeLen == 80`, `notes.runeLen == 400`, `validateUtf8() == -1` on both and on the whole
  replay payload, that a string sitting *exactly* on the cap survives whole, and that the payload
  strict-`parseJson` round-trips and re-derives.

**Replay writer (checklist 2, design §Replay bytes)**
- `sim.nim:705-736` `replayPayloadJson` emits `protocol: "fogboards.replay.v1"`, `names`,
  `policyNames`, `config{mode,size,abrupt,sense,first,seed,maxPlies,sampled}`, `events`,
  `results` — verified byte-for-byte in the `smoke-replay` artifact of run 33031534557.
- Five event kinds only (`types.nim:40-45`), each serialised at `sim.nim:640-675`; `outcome`
  serialises as `"result"` (`:653`) and deserialises from `"result"` (`:684`) — the accepted Nim
  naming deviation, confirmed in the artifact bytes.
- Cells travel as algebraic strings everywhere (`sim.nim:451`, `:456`, `:475`, `:394`); test 21
  (`test_replay.nim:238-249`) asserts every `cell`/`anchor`/`path` entry starts with a file letter.
- `finishEpisode` order (`server.nim:161-210`): final frames to players → `broadcastLocked` →
  `results.json` → `.replay` → grace → `quit(0)`.

**Viewer re-derivation (checklist 2)**
- `sim.nim:740-802` `replayMatch`: replays `evSense` (anchor) and `evAttempt` (cell) through the
  rules, re-derives `attempt.result` and compares (`:768-776`), re-derives `win.seat/how/path` and
  compares (`:777-792`), raises if a win is recorded the rules do not derive, checks the mover
  matches (`:761-765`), and applies `evEnd` through the **same** `settle` (`:793-801`).
- `settle` (`sim.nim:334-356`) is the single ending proc, called on record (via `applyAttempt`'s
  win check, `endEarly`, the board-full and ply-cap branches) **and** on playback.
- Test 18 (`test_replay.nim:97-111`) records one episode per reason/ending pair — including
  `deadline/wall-clock` on a `sense = 2` board — and asserts `frames.len == events.len + 1`,
  `$frames[i].boardStateJson() == states[i]` for **every** frame, plus equal
  `reason`/`ending`/`winner`/`resultsJson`. Test 19 (`:113-163`) asserts `replayMatch` raises on a
  flipped `result`, a stolen win seat, a mislabelled `how`, an altered `path` and an out-of-turn
  attempt.
- Wasm entry `replay-viewer/fogboards_replay.nim:23-62` runs the same `replayMatch` and emits
  `states[i] = boardStateJson` after `events[0..<i]`; `client/renderer.js:953-961, 972-980` reads
  the board, the clock, the scorebug and the endcard-visibility from `states[index]` — the
  re-derivation, not a parallel recording. (The feed's per-line text rebuilds a board from the same
  event list in `feedText`, `renderer.js:683-761`, mirroring `refereeLog`; it is derived from the
  recording's events, not a second recording.)

**Viewer bootstrap (checklist 13)**
- `replay-viewer/config.nims:38-41`: `-s MODULARIZE=1`, `-s EXPORT_NAME=FogReplayModule`,
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_fog_load_replay,_fog_payload_ptr,_fog_payload_len,_fog_error_ptr,_fog_error_len`.
  `replay-viewer/static_replay.js:141` calls the factory `FogReplayModule()` and `:94-102` calls
  `_fog_load_replay` / `_fog_payload_ptr` / `_fog_payload_len` / `_fog_error_ptr` /
  `_fog_error_len`. Same starter, matched. `diff` against
  `/workspace/starters/cogame-babel/replay-viewer/{config.nims,static_replay.js,index.html}` at
  `d55d999` shows **only** the `Babel*`→`Fog*` / `_bab_*`→`_fog_*` renames plus the one
  documented `onFirstFrame` deviation. No `onRuntimeInitialized` anywhere in the tree.
- `data-replay-loaded="true"` is set on `document.documentElement` inside the render loop, after
  `renderer.draw(...)` on the first frame (`client/renderer.js:1005-1022`), and
  `static_replay.js` posts `tell("ready")` from that same callback. `data-replay-error` is set in
  `fail()` (`static_replay.js:59-72`) and removed on retry (`:110`, `:135`).
- CI: `viewer-smoke.json` from run 33031534557 —
  `"signals": {"data_replay_loaded": "true", "data_replay_error": null, "bridge": ["loading",
  "ready"], "bridge_ready": true, "bridge_error": []}`, `"loaded": true`, `"ms": 297`.
  `wasm-viewer` has `needs: docker-smoke` (`ci.yml:212`) and the smoke step is present, not
  commented, with no `continue-on-error` (`ci.yml:293-325`). The artifact digests match
  (`83af96028fb6…` uploaded by `docker-smoke`, downloaded by `wasm-viewer`), so the replay loaded
  really is the one the smoke produced.
- Soak: `"soak": {"seconds": 10, "moved": true, "before": {"clock": "… PLY 0 / 50 …"},
  "middle": {"clock": "… PLY 6 / 50 …"}, "after": {"clock": "… PLY 8 / 50 …"},
  "page_errors": []}`. The stdout line reads `(null -> null -> null)` because it prints only the
  `tick` field, which this page has no element for; the `advanced()` test at
  `viewer_smoke.mjs:541-542` also reads `clock` and `scorebug`, both of which moved in both
  intervals. Three differing scrub readouts recorded.
- Playback length: `tests/test_bot.nim:41-52, 172-191` parses `var DWELL` straight out of
  `client/renderer.js:50-51` and sums it over the cert episode. CI:
  `cert replay playback: 12 events, 13700 ms against a 10 s soak`, `check playback >= 13_000`.
  This is the accepted dwell deviation (note values 700/1100/1500 → shipped
  900/900/1000/1500/2200/2200/600) and the test pinning it.

**Chrome provenance (checklist 14)**
- `client/chrome_common.js`: I extracted every `BEGIN/END copied cogame-babel renderer.js N-M`
  region and diffed it against the corresponding lines of
  `/workspace/starters/cogame-babel/client/renderer.js` at `d55d999`. Result:
  regions **101-124, 680-733, 735-744, 1029-1048 byte-identical**; regions 790-863, 963-970,
  972-1027, 1142-1222 differ by **exactly** the six edits the note names and nothing else —
  EDIT 1 `"ROUND " + (block+1)` → `"PLY " + (block+1)` (`:137-140`); EDIT 2 `describeEvent` →
  injected `feedText` (`:174-178`); EDIT 3 the speak/pick notes sub-line → the attempt `say`
  sub-line (`:179-188`); EDIT 4 the marker-`div` loop → `markPlyBeat(...)` for every event
  (`:351-356`); EDIT 5a/5b/5c the four hard-coded heads and cells → injected `endColumns`
  (`:256`, `:265-269`, `:281-283`); EDIT 6 `rounds`/`maxRounds` → `plies`/`maxPlies` (`:222-224`).
- The private prelude (`:25-37`) is byte-identical to babel `renderer.js` 23-31 (`COLORS`,
  `COLOR_HEX`) and 85-87 (`seatColor`), and is **not** on `window.FogChrome` (`:485-506`) — the
  accepted deviation, verified.
- Appended block in the note's order — `relayout()`, `markPlyBeat()`, `setFeedText()`,
  `setEndColumns()`, the export (`:399-506`). Nothing renamed in place.
- `client/chrome.css` first 443 lines are **byte-identical** to babel's whole file; the game block
  is appended under `/* ===== fog-of-war-boards game block ===== */` (`:445-448`).
- `client/replay_broadcast.html`, `global.html`, `player.html` are byte-identical to babel's
  `replay.html` / `global.html` / `player.html` except the edits in N7 plus one appended
  `<script>` block under the required banner comment. **No starter element removed** from any of
  the four pages. 90 lines vs the starter's 74 — an append, not a rewrite.
- Transport rules: (a) `relayout()` sets `--band` and `--hudscale` on
  `document.documentElement` (`chrome_common.js:405-419`), and runs on `load`, on `resize` and
  therefore on every feed toggle (`bindFeedToggle` dispatches a resize, `:305-307`). (b) No
  `position: fixed` anywhere in `chrome.css` or the four pages; `#transport` is a flex child of
  `#stage` (`chrome.css:128`). (c) `#endscreen` keeps babel's `position: absolute; inset: 0` and
  the appended rule sets `bottom: var(--band, 0px)` (`chrome.css:372-381`, `:552`); it is shown
  with the class its own rule uses (`#endscreen.show`, `:381`) and `updateEndscreen`'s
  unconditional `classList.toggle("show", !!show)` (`chrome_common.js:234`) is reached on **every**
  seek, because `setIndex` always calls it with `index >= events.length && events.length > 0`
  (`renderer.js:977-980`) and the scrub's `onSeek` and every beat click both route through
  `setIndex(next, true)` (`renderer.js:942-945`, `chrome_common.js:456-459`). (d) Beats are
  `<button type="button">` with `aria-label`, `title` and a click handler that seeks
  (`chrome_common.js:444-461`); CSS exists for every kind the sim emits — `.beat-start`,
  `.beat-sense`, `.beat-attempt`, `.beat-win`, `.beat-end`, `.beat-attempt.occupied`
  (`chrome.css:567-585`) — plus the seat tints via babel's `.seat0`/`.seat1` `--tc` rules
  (`chrome.css:205-206`).
- Zoom bar / minimap: no `#viewpanel`, no `zoomAt`/`setZoom`/`attachMinimap` anywhere
  (`grep` over `client/`, `replay-viewer/`); babel has none either, and every shipped board is
  3×3/4×4/5×5 and fits the frame. Correct per the checklist's "remove it unless the board is
  pannable".
- `tools/ci/chrome_scope_check.mjs` (all 108 lines read) asserts the eight region markers, the
  seven edit markers, `≥ 12` exported names, no game-block re-declaration of an exported name,
  no `markBeat` in `renderer.js`, and that the `"PLY " + (block + 1)` string survives. It is a
  required `ci.yml` step (`ci.yml:369-370`) and passed in run 33031534557. I independently listed
  `renderer.js`'s 41 top-level declarations against `FogChrome`'s 20 exports: no overlap.

**Manifest (checklists 3, 6, 10, 12)**
- `game.replay_viewer = {"bundle": "static-replay-viewer"}` inside `game`, and no top-level
  `replay_viewer` (`coworld_manifest_template.json:20`; asserted at
  `tests/test_manifest.nim:125-126`). No `path` key anywhere; the only `/client/replay` strings in
  the repo are the in-container HTTP route (`server.nim:513`, inherited from babel) and one
  descriptive clause in `game.protocols.global` that ends "Hosted replays are the STATIC wasm
  bundle (index.html?replay=<url>), never a pod."
- `tools/build_replay_viewer.sh` exists, is committed `100755`, has the `mkdir -p` fix (`:20`),
  copies exactly the files the note lists, and keeps both greps (`:65-66`). Wired as the
  `coworld build` hook via `game.replay_viewer.bundle` and exercised in `ci.yml:248-249`.
- `num_agents: 2` inside all four variants' `game_config` **and** in `certification.game_config`,
  never at a variant's top level. Verified by parsing the file and by
  `tests/test_manifest.nim:39-61`. Variant ids `["phantom-ttt-3","dark-hex-4","dark-hex-5",
  "recon-hex-5"]`, each with `description`; the four `game_config` bodies match the note's table
  exactly (mode/size/abrupt/sense/first/maxPlies/turnDelayMs/player_connect_timeout_seconds).
- `tools/ci/docker_smoke.sh:110-151` enforces all four invariants with the `SEAT-COUNT FAIL:`
  prefix — `num_agents` present, positive integer, `len(certification.players) == num_agents`,
  `len(certification.game_config.players) == num_agents` — plus the independent `SMOKE_SEATS`
  cross-check. **`grep -c "SEAT-COUNT FAIL" ci.log` over the full run-33031534557 log = 0.** The
  log carries `game=fog-of-war-boards seats=2 config={…"num_agents": 2…}` and
  `all 2 player containers exited 0`. The file is the template verbatim modulo the three
  `<slug>/<IMAGE>/<SEATS>` substitutions.
- `game.docs` = `{"readme": {"type":"text","value":…}, "pages":[{"id":"rules.md",
  "title":"rules.md","content":{"type":"text","value":<7043 chars>}}]}`; `game.protocols` carries
  **both** `player` (2004 chars) and `global` (1153 chars), each a `{"type":"text","value":…}`
  object. `game.tags` absent, top-level `tags` has 10 entries, no top-level `version`, no
  `game.display_name`, `episode_timeout_minutes: 20`, `$schema` present, `game.owner` set.
  `ANTHROPIC_API_KEY_URI = "secret://coworld/fog-of-war-boards/anthropic_api_key"` and
  `game.name == "fog-of-war-boards"` — namespace equals `game.name`
  (`tests/test_manifest.nim:136-139`).
- `config_schema`: `additionalProperties: false`, `required: ["tokens","players"]`, both arrays
  `minItems 2 / maxItems 2`, every scalar bound as the note specifies. No shipped `game_config`
  carries `tokens` (`tests/test_manifest.nim:65-69`). `results_schema`:
  `additionalProperties: false`, all 18 fields required, all ten arrays `minItems 2/maxItems 2`,
  `reason` enum `["complete","deadline"]`, `ending` enum `["connection","line","board-full",
  "ply-cap","wall-clock"]`.
- Bundled players: two entries, both `resources.limits.cpu == "1"`,
  `requests {cpu 100m, memory 64Mi}`, both `player_id`s seated in `certification.players` and
  every seated id declared (`tests/test_manifest.nim:155-169`).
- `tools/ci/policies.json`: four policies; #1 and #2 both `PLAYER_PROMPT` (texts match
  design.md:429-455 verbatim), #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, plus `PLAYER_SCRIPTED=probe` and
  `=sweep` fillers.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows,
  `docker_smoke.sh` and `policies.json` matches nothing → **exits 0**. The surviving
  angle-bracket names are the expected residue (`<cow_id>`/`<sha>` in `ci.yml:202`, `<run_id>` in
  both release/submit readback recipes, `<name>:vN` in `coworld-submit.yml:31`), plus one extra
  `<cow_id>` in a `coworld-release.yml:75` comment that is likewise template text.
- `coworld-release.yml` and `coworld-submit.yml` are **byte-identical** to
  `templates/coworld-release.yml` / `templates/coworld-submit.yml` after substitution. Step order
  is build manifest (`:159`) → certify (`:173`) → upload the policies (`:212`) → upload the
  Coworld (`:310`) → put the Coworld secret (`:348`).

**Both name spaces (checklist 4)**
- Agents: `tableNames` seeded shuffle of `CogNames` (`sim.nim:59-70`); the alias is what goes into
  `welcome.name` (`server.nim:425`), `playerStateJson.name` (`server.nim:108`), the `final` frame's
  `names` (`server.nim:175-177`), the system prompt (`llm.nim:384-385`) and the user prompt
  (`llm.nim:463`). No policy display name is reachable from any per-seat frame or prompt.
- Spectators: `policyNames` in the global snapshot (`server.nim:93`) and in the replay bytes
  (`sim.nim:713-715`); the viewer maps aliases → policy names for non-baseline seats via
  `makeNameMap`/`isBaselineFiller` (`chrome_common.js:75-107`) at `renderer.js:850, 868, 932`, and
  the scorebug renders the policy name with the alias as a sub-label (`renderer.js:654-655`,
  `.plate-name` / `.plate-alias`).
- CI evidence: the smoke replay carries `names: ["Flywheel","Bolt"]` and
  `policyNames: ["Sprocket","Gizmo"]`; the smoke `viewer-smoke.json` scorebug reads
  `"Sprocket FLYWHEEL ▶ 4 STONES 1 TO CONNECT Gizmo BOLT 2 STONES 3 TO CONNECT"`, and the fixture
  screenshot shows `fog-of-war-boards-carto…` over `SPROCKET`.

**Scripted baselines (checklist 7)**
- Test 13 (`tests/test_sim.nim:393-416`) parses the real manifest, builds a `Sim` from **all four**
  variants' `game_config` plus `certification.game_config`, plays each to the natural end and
  asserts `results.reason == "complete"`.
- Test 14 (`tests/test_bot.nim:73-104`) — 200 seeds × 4 variants × 2 baselines — asserts every
  attempt is in `legalAttempts(mover)` and every anchor in `legalAnchors(mover)` at the moment it
  is produced, that `anchor == -1` when `sense == 0`, that no baseline speaks/notes/guesses, and
  **blindness** via `shadowed()` (`:54-70`), which inverts every cell the seat cannot legitimately
  see and asserts the decision is unchanged. Test 12 (`test_sim.nim:366-390`) checks
  `believedBoard` holds no unproven stone at every prefix.
- Tuning: test 15 (`test_bot.nim:106-130`) is the grid/opponent harness —
  CI: `probe vs random: mean score 1.0 (200/200 wins)`; test 16 —
  `probe/sweep disagreement: 1750/2450 = 0.714`, floor 0.30.

**Legibility at 360 px (checklist 11)**
- `client/chrome.css:492-499`: `.plate-name { grid-area: name; flex: 1 1 auto; min-width: 3.2em;
  … }` — both declarations present as the checklist names them. (`.plate` is
  `display: grid` at `:471-481`, so `flex` is inert there; the column is `minmax(0, 1fr)` and
  `min-width: 3.2em` does apply.)
- Labels hidden under 640 px: `@media (max-width: 640px) { .plate-label { display: none; }
  .plate-alias { display: none; } }` (`:596-606`), and a further `@media (max-width: 360px)` block
  (`:610-623`) stacks the scorebug to one column. The fixture asserts no `.plate-name` collapses
  below 24 px at any of 360/640/1280 (`renderer_fixture.html:337-342`) and passed.

**Checklist 1, second half**
- `git log --oneline --all -- tests/` returns exactly one commit (`a15121b`), and
  `git diff a15121b 791cf71 -- tests/` is empty. No test file was changed, skipped, deleted or
  loosened during this run. The only files touched by `791cf71` are `ci.yml` (a readiness guard
  for the fixture server), `client/chrome.css` (`.plate-say` max-height 26 → 40 px plus
  `overflow-wrap: anywhere`), `client/renderer.js` (contrast + rank-digit placement) and
  `tools/ci/renderer_fixture.html`.

---

## Could not determine

- **Whether the fog hatch and the sense-window overlay ever render correctly under a real
  playthrough.** `renderer.js:405-423` (hatch) and `:443-483` (the 2×2 amber frame + `lens.png`)
  are not visible in either CI screenshot: the smoke screenshot is at `FINAL`, where
  `!state.gameDone` gates the hatch off, and the fixture is at PLY 2 with no opponent stones on
  the truth board. **Inferred** that the hatch path ran during the soak (the smoke replay has
  opponent stones from ply 2 onward and `page_errors` is empty), but the sense overlay cannot have
  run anywhere in CI — no shipped CI path uses `sense > 0` (`docker_smoke.sh` drives the
  `dark-hex-5` cert fixture, `sense: 0`, and the fixture payload sets `sense: 0`). What would
  settle it: a `recon-hex-5` payload in `renderer_fixture.html` (or a second fixture run with
  `sense: 2` and a `lastSense`), screenshotted.
- **Whether the LLM path itself works end to end.** `docker_smoke.sh` deliberately runs without a
  key, so `completeText`, `extractJsonObject`, `parseReply`, the retry hint and the
  `fellBack` counter are exercised only by unit-level code paths, never against a live model.
  `tests/test_bot.nim:194-208` covers the *disabled* branch only. What would settle it: a hosted
  episode with `ANTHROPIC_API_KEY_URI` resolving, or a phase-60 replay showing a non-empty `say`.
- **Whether `.plate-say` stays unclipped for a `say` that wraps to more than three lines.** The
  band is `max-height: calc(40px * var(--hudscale))` with `overflow: hidden`
  (`chrome.css:534-548`); the fixture's 80-rune remark lays out on one line at all three widths, so
  the 3-line ceiling has never been approached in CI. **Untested.** What would settle it: a fixture
  remark composed of long unbroken tokens (which `overflow-wrap: anywhere` would break) at 360 px,
  read through the existing `scrollHeight > clientHeight` check.
- **The exploitability of N1.** That the sensed-empty record is deleted is observed; that a model
  would notice and exploit the deletion is **inferred**. What would settle it: either a test
  asserting `sensedEmptyAt[1 - mover]` is untouched by `applyAttempt`, or an explicit line in the
  design note declaring the deletion intended.

---

Findings: **2 blocking** (B1, B2 — both checklist 15, category `legibility`), **13 non-blocking**
(N1–N13).
