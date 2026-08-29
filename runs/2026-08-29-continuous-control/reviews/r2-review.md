# r2 review — continuous-control
Range: 4c1b3101..a8db2b32 (head a8db2b326b7f7b8f05f10ffdb5c1a7e85f28b2dc)   Files read: 36   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST (items 1–15)

Scope: a delta review. (1) the ten fix commits, audited against `r1-fixes.md`'s claims;
(2) the standing verdict finding B1 — the 140-rune LLM `say` render path, traced end to end;
(3) what the fix commits touched adjacent to those.

Method note. Everything below is **observed** unless labelled. Where I say "measured", I ran the
real `client/replay_broadcast.html` (served with `data/font.ttf` as `./font.ttf`, exactly as
`Dockerfile.replay-viewer:27,31-34` assembles the bundle) in headless Chromium via Playwright
1.55.0 and read `getBoundingClientRect()`; where I say "reproduced", I evaluated the page's own
verbatim source lines under jsdom 27. CI evidence is the head run's own uploaded artifacts
(run 33249877981, `viewer-smoke` and `renderer-fixture`), not the summary lines in the log.

---

## Blocking

### F1 — the `say` is never drawn: `ccFeed` hands a string to the starter's `pushFeed(row: Node)`, and the TypeError is swallowed

- Where: `client/replay_broadcast.html:3551-3553` (`ccFeed`), `:3572` (`case 'say'`),
  `:2286-2297` (the inherited `pushFeed`), `:2945-2951` (`PB_CTX`), `:3645-3653`
  (`CcChrome.event`'s try/catch); the same two lines in the generator source
  `client/cc_block.html:594-596`.
- Observed, step by step:
  1. The block's only feed entry point is
     ```js
     function ccFeed(text, cls) {
       if (ctx && ctx.pushFeed) ctx.pushFeed(text, cls || '');
     }
     ```
     (`:3551-3553`). `ctx` is `PB_CTX`, set once by `window.CcChrome.install(PB_CTX)` at `:2952`;
     `PB_CTX.pushFeed` is the page's own `pushFeed` (`:2949`).
  2. That `pushFeed` is the starter's, unmodified, and takes a **Node**:
     ```js
     function pushFeed(row) {
       feedEl.insertBefore(row, feedEl.firstChild);
       ...
       row.style.animationDuration = (250 / animFactor()) + 'ms';
     ```
     (`:2286-2293`). Byte-for-byte the starter's `coworld-ctf/client/replay_broadcast.html:3568-3579`.
  3. `Node.insertBefore(node, child)` takes `Node` (non-nullable, non-union) in WebIDL, so a string
     argument raises before any of the body runs. Reproduced in a real DOM: `TypeError: Failed to
     execute 'insertBefore' on 'Node': parameter 1 is not of type 'Node'.`
  4. The starter's own appended block never does this — it builds the row first:
     `coworld-ctf/client/replay_broadcast.html:4508-4513`,
     `function feedRow(html, cls) { var row = document.createElement('div'); row.className =
     'feed-row' + (cls ? ' ' + cls : ''); row.innerHTML = html; CTX.pushFeed(row); }`.
     The cc block has no equivalent; `ccFeed` calls `ctx.pushFeed` directly.
  5. Every `ccOnEvent` case reaches `pushFeed` through `ccFeed` (`:3559-3614`), and `ccOnEvent` is
     only ever called from `CcChrome.event`, which catches and discards:
     ```js
     } catch (err) {
       if (window.console) console.error('continuous-control chrome event:', err);
       return false;
     }
     ```
     (`:3649-3652`). `applyEvent` (`:2202-2212`) treats the `false` as "the block did not handle
     it" and falls through to the classic ctf switch, which has no case for any cc kind — so
     `beatPulse()` is skipped too. `applyEvent` runs once per event per frame (`:1759`).
  6. Reproduced against the page's verbatim source (`:2283-2298`, `:3551-3553`, `:3555-3618`,
     `:3645-3653` extracted unmodified and run under jsdom against a real `<div id="killfeed">`):
     `event()` returned `false` for `say`, `stagestart`, `milestone` and `fall`; `#killfeed` held
     **0 children**; **0 banners** fired.
  7. Confirmed at the reviewed sha from CI's own artifact — `viewer-smoke/viewer-smoke.json`,
     run 33249877981, step "Load the bundle in a real browser", `console_tail`:
     twelve consecutive
     `[error] continuous-control chrome event: TypeError: Failed to execute 'insertBefore' on
     'Node': parameter 1 is not of type 'Node'. at Object.pushFeed (http://127.0.0.1:42885/index.html…)`.
     Same JSON: `"feed_lines": 0`.
- Consequences, traced:
  - The LLM `say` — the one model-authored string this viewer draws — never enters the DOM at any
    width. Neither does any other cc feed line: `STAGE n OF 3` (`:3560`), `ORDER —` (`:3567`),
    `JOINT PEGGED` (`:3576`), `n METRES` (`:3581`), `DOWN —` (`:3584`), `LINED OUT` / `STAGE n DONE`
    (`:3595`, `:3598`), `MISSED THE CALL` (`:3605`), `BUDGET GUARD` (`:3608`), `FINAL —` (`:3611`).
  - Two **banners** are lost with them: in `case 'stagestart'` and `case 'fall'`, `ccFeed` is called
    *before* `ctx.banner(...)` (`:3560-3564`, `:3584-3591`), so the throw pre-empts the banner.
  - The `cls` argument (`'say'`, `'good'`, `'bad'`) is discarded in the same call; there is no
    `.feed-row.say` rule anywhere in the page (`grep '\.say'` over `replay_broadcast.html`: 0 hits).
  - The scrubber beat markers are unaffected: they come from `ccDrawBeats(s)` inside
    `CcChrome.frame` (`:3631`), a different path.
- What the design note says it should do: `design.md:1654-1660`, §10 **Match feed** (`#killfeed`) —
  the feed carries `STAGE 2 OF 3 — CHEETAH, 60 M OF TRACK`, `ORDER — RUN, …`, `DOWN — …`,
  `LINED OUT — …`, `Alpha: "lengthening the stride now the cheetah is up to speed"`, and
  `MISSED THE CALL — trotter order`, and: "**The `say` lines and the order lines are where a
  spectator sees the LLM playing.**" `design.md:1490-1491` requires `pushFeed` "**including its
  signature**" to be kept — the definition is kept; the call site does not match it.
- Checklist item: **15** — "*A repo whose viewer draws LLM-authored text must therefore ship a
  worst-case renderer fixture … The fixture asserts its own strings are still full-length — one
  quietly shortened remark leaves it passing while testing nothing.*" The fixture that item 15
  mandates is shipped and green (`tools/ci/renderer_fixture.html`, `ci.yml:352-388`) and it drives
  this exact path — `EVENTS[3] = { k: 'say', t: 3, text: SAY }` at `:138`, replayed through
  `chrome.event(EVENTS[i], playing, null)` at `:188` — and reports nothing, because the throw is
  caught inside `CcChrome.event` and the fixture's only assertions are five box checks on other
  elements (`:194-206`). *(category: legibility)*
- Why blocking: the string class item 15 exists to protect is not merely unmeasured (the r1
  verdict's B1) — it is not rendered at all, at every width, in the shipped bundle, with the
  evidence sitting in the head run's own uploaded artifact. The fixture is passing while testing
  nothing, which is the failure mode item 15 names in terms.

---

## Non-blocking

### F2 — test 42 asserts both halves of the signature mismatch it exists to prevent

- Where: `tests/test_cc_viewer.nim:70-78`.
- Observed: the test's docstring is "`pushFeed` keeps its SIGNATURE and its call site (the cogball
  0.1.4 latch scar: a signature drift threw mid-replay and latched static_replay.js into `failed`).
  The game block routes EVERY feed line through it." It then checks, in the same block:
  - `:73-77` — the starter's declaration prefix, sliced from
    `find("function pushFeed(")` to the next `)`, i.e. `function pushFeed(row)`, is present in the
    page; and
  - `:78` — `check "ctx.pushFeed(text, cls" in page`.
  So the definition is pinned as taking a Node named `row` and the call site is pinned as passing
  `(text, cls)`. Both assertions pass at head, and together they pin F1 in place.
- Design note: `design.md:2096-2097` (test 42) — "`broadcast_core.js`'s kept procs are
  byte-identical to the starter's, `pushFeed`'s signature included." The note describes preserving
  the *callee*; the test additionally pins the *caller*.
- Not blocking: no checklist item names call-site pinning. Recorded because it is why F1 survived
  a green suite. (No assertion here is weakened — it is a correct assertion about the wrong thing.)

### F3 — the fixture's "Exactly 140 runes" SAY is 133 runes, `slice(0, 140)` is a no-op, and nothing asserts its length

- Where: `tools/ci/renderer_fixture.html:40-45`.
- Observed:
  ```js
  // Exactly 140 runes: the server's own MaxSayRunes, so the feed row is laid
  // out at its true worst case …
  var SAY = ('lengthening the stride now the cheetah is up to speed; the front '
    + 'knee is pegged at full torque so power comes down six next turn!!!!!');
  SAY = Array.from(SAY).slice(0, 140).join('');
  ```
  I measured the literal: **133** characters, all BMP single-code-unit, so 133 runes.
  `Array.from(...).slice(0, 140)` therefore returns the whole array unchanged. The file contains no
  assertion on `SAY.length` or `Array.from(SAY).length` (grep: none), and its five box checks
  (`:194-206`) cover `cc-ribbon`, `cc-pips`, `cc-strip`, `fpv-name`, `clock-caption` — never a
  `.feed-row`. `MaxSayRunes = 140` (`src/cc/sim_types.nim:37`).
- Design note / verdict: `design.md:2131-2137` (test 51) requires the fixture to drive the real page
  "with a full-cap 140-rune `say`". The r1 verdict's B1 states the same three facts; I re-verified
  each independently and they all reproduce.
- Not blocking on its own — it is a component of F1's checklist-15 case, filed separately so the
  facts stand apart from F1's conclusion.

### F4 — `viewer_smoke.mjs` has no DOM-text capability at all, and its one DOM feed probe cannot match `#killfeed`

- Where: `tools/ci/viewer_smoke.mjs:322-416` (text bounds), `:418-442` (`READOUT_SCRIPT`), `:430`,
  `:437`, `:478`, `:567-570`, `:610-613`, `:675-676`.
- Observed:
  - The only text instrumentation is a monkey-patch of
    `CanvasRenderingContext2D.prototype.fillText` / `strokeText` (`:359-415`). There is no
    `getBoundingClientRect`, no overflow/clip check, no DOM text measurement anywhere in the file.
    Its own header says so: "Only main-thread 2D contexts are seen" (`:140-142`).
  - `grep -c 'fillText\|strokeText'` over `client/chrome_common.js`, `client/broadcast_core.js`,
    `client/replay_broadcast.html`, `client/cc_block.html`, `replay-viewer/static_replay.js`,
    `replay-viewer/static_replay_worker.js` = **0 in every file**. Every string this viewer draws is
    DOM. Hence `canvas_text.total == 0` in both `--strict-text-bounds` steps (head-run artifacts,
    both `{"total": 0, "outside": 0, "ellipsized": 0, "never_inside": 0}`), and by item 15's own
    rule "`total: 0` means the check covered nothing".
  - The single DOM feed probe is `:430`:
    `const feed = document.querySelector('#feed, .feed, #log, [id$="-feed"]');` and `:437`
    `feed_lines: feed ? feed.querySelectorAll("*").length : 0`. The page's feed container is
    `<div id="killfeed">` (`client/replay_broadcast.html:1294`). `killfeed` does not end in `-feed`,
    and the page contains no `id="feed"`, no `class="…feed…"` and no `id="log"` (regex sweep: 0 hits
    for all four). So `feed_lines` is **structurally 0 for this viewer whatever the feed does** —
    confirmed 0 in both head-run artifacts.
  - Console errors *are* captured (`:478`) into `console_tail`, but are printed only on failure
    (`:675-676`) and gate nothing. Uncaught page errors gate only inside `--soak` (`:567-569`); this
    error is caught by `CcChrome.event`, so it is not a page error.
- Not blocking: item 15 gates `never_inside` from the canvas hook and prescribes the fixture as the
  escape hatch; it does not require `viewer_smoke.mjs` to grow DOM measurement. Recorded because it
  is the precise answer to "what can and cannot the smoke see of DOM text": nothing.

### F5 — measured: the full-cap 140-rune say row *would* fit the frame at 360 / 640 / 1280 px; the standing B1's overflow arithmetic does not reproduce

- Where: `client/replay_broadcast.html:488-505` (`.feed-row`), `:470-487` (`#killfeed`), `:1201`
  (`#stage.tiny #killfeed`), `:2909-2933` (`relayout`), `:42` (`--u: calc(1px * var(--hudscale))`),
  `:48-52` (`html, body { … overflow: hidden }`).
- Observed statically, and matching the r1 verdict: `.feed-row` is `max-width: none;
  white-space: nowrap;` with the inherited justification in the file — "bounded by the small font +
  the pre-bounded 10-char name, so it can't run away" (`:499-503`) — and this fork's cap is 140,
  not 10. There is no `.feed-row.say` override in the appended block.
- Measured (real page, real `rajdhani` webfont loaded, `document.fonts.ready` awaited, the page's
  own `relayout()` arithmetic from `:2909-2933` re-run against three plausible board aspects, row
  text `Alpha: “<140 runes>”` = 142 characters):

  | viewport | boardW | `--hudscale` | font | row width | row left | row right | inside frame |
  |---|---|---|---|---|---|---|---|
  | 360×203 | 266 (A=1.874) | 0.500 | 4 px | 233 px | 74 | 307 | yes |
  | 360×203 | 355 (A=2.5)   | 0.500 | 4 px | 233 px | 119 | 352 | yes |
  | 360×203 | 129 (A=1.0)   | 0.500 | 4 px | 233 px | 6 | 239 | yes |
  | 640×360 | 517 | 0.680 | 5.44 px | 304 px | 267 | 570 | yes |
  | 1280×720 | 1034 | 1.361 | 10.89 px | 681 px | 460 | 1141 | yes |

  At 360 px `--hudscale` is clamped to its 0.5 floor (`:2925`), so 4 px is the smallest font the row
  can take and 233 px is its widest realisation there. The row **does** overflow `#killfeed`'s own
  box (114 px at 360 px, 95 px once `#stage.tiny` applies at `:1201`) leftward, as
  `align-items: flex-end` + `max-width: none` implies — but it never crosses the frame edge, so
  `html { overflow: hidden }` never clips it.
- Against the r1 verdict: B1 states "at 360 px … a ~148-character single-line nowrap row computes to
  roughly the full frame width … it clips at the left frame edge". Measured, it is 233 px of 360 —
  **that half of B1 does not reproduce**. The other half ("nothing measures it"; the fixture is not
  the fixture item 15 specifies) reproduces exactly, and F1 shows the situation is worse than
  unmeasured.
- Caveat (labelled): I measured the page standalone, not the emscripten bundle, because building
  the bundle needs Docker + emscripten. The bundle's `index.html` is this same file with three
  comment markers substituted (`Dockerfile.replay-viewer:31-34`) and `data/font.ttf` copied to
  `./font.ttf` (`:28`), so the CSS, the markup and the font are identical; the wasm module affects
  no part of this layout.

### F6 — `docs/PHYSICS.md` divergence 15 cites a replay size the head run does not produce

- Where: `docs/PHYSICS.md:135-145` (added by 04e39c93, r1-F16): "The CI smoke's own figure is
  132 082 B for a full three-stage episode."
- Observed: run 33249877981, `docker-smoke` step, 11:21:17 — `replay saved for the viewer smoke:
  … /dist/smoke/replay.json (131999 bytes)`. 83 bytes apart; the doc's figure is from an earlier
  run. The surrounding claim ("about 130 KB, not the ~32 KB the note estimated", bounded by
  `MaxOrderRecordRunes = 6000` per record) is correct.
- Not blocking: no checklist item gates a documented byte count.

### F7 — the note's fall-limit literals are not pinned by any test, and 3f4bfb64 makes the hopper's `fwHigh` branch unreachable in test 11's sample space

- Where: `tests/test_cc_sim.nim:326-353` (test 11), `src/cc/body.nim:132-141` (hopper),
  `:223-225` (walker).
- Observed: test 11 compares `body.isUnhealthy(s)` against a re-derivation from **`s.lowY` /
  `s.highY` / `s.maxPitch`** (`:346-350`), i.e. against the same spec fields it is testing — so it
  passes for any values of those fields. The note's literals (`design.md:277`, hopper `y < 0.70 m`
  or `|pitch| > 20°`; walker `y ∉ (0.80, 2.00)` or `|pitch| > 57°`; `design.md:1962-1964`, test 11)
  are not asserted anywhere. Test 11 samples `links[0].y` over `-40_000 .. 200_000` Q16
  (`-0.61 .. 3.05 m`, `:336`); with `highY = mm(20_000)` the hopper's `fwHigh` branch can no longer
  fire in that range. The walker's still can (`highY = mm(2000)` = 2.00 m, inside the range).
- No assertion was deleted or loosened by 3f4bfb64 (it touched only `src/cc/body.nim`); this is a
  coverage consequence of an intentional and correct change.
- The change itself is correct and precisely described — see "Traced and consistent" below.

### F8 — test 47b greps only the appended block, not `broadcast_core.js` as the note describes

- Where: `tests/test_cc_endcard_labels.nim:39-52`; `design.md:1554-1557`.
- Observed: the note says the test "greps the built `index.html` **and `broadcast_core.js`** for a
  forbidden-vocabulary list … outside comment blocks, and asserts **zero** matches". The test reads
  `core` at `:19` but 47b greps only `blockText` — `page[page.find("CONTINUOUS-CONTROL additions") ..
  ^1]` (`:20`, `:46`); `core` is used only in 47d (`:82-83`). I ran the note's 16 tokens over
  `broadcast_core.js` with `//` tails stripped: the only hit is `flag` (7×) — already one of the two
  tokens 47b documents as unavoidable. So widening the grep would change no outcome today.
- Not blocking: item 14 gates provenance, not the grep's file list. Recorded because b682a19b
  touched this test.

---

## Traced and consistent

Fix commits (`git log --oneline 4c1b3101..a8db2b32`, ten commits, one per r1 finding):

- **e9902cc (r1-F1)** — `src/cc/replays.nim:223-233`: `writer.body.addText(stop.detail
  .truncateRunes(MaxStopDetailRunes))`, cap in the codec so both recorders are bounded
  (`server.nim:407-409` and `tests/helpers.nim:100-102` both pass an unbounded `detail`).
  `MaxStopDetailRunes = 200` (`sim_types.nim:42`). Test 37 (`tests/test_cc_replay.nim:179-201`)
  feeds `repeat(emoji, MaxStopDetailRunes + 37)` — 237 four-byte emoji — and asserts
  `runeLen == 200` **and** equality with exactly 200 whole emoji, on top of the pre-existing
  `validateUtf8(output) == -1` / no-lone-surrogate checks. `tools/replay_summary.py:78-85` decodes
  with strict `raw.decode("utf-8")`, so a byte-truncated codepoint would fail the pipe rather than
  be replaced; `:172-177` passes `detail` through unmodified. Matches `r1-fixes.md`. Strictly
  stronger than before.
- **e92e5e8 (r1-F2)** — `src/cc/llm.nim:250-252` now reads "pitch heading toward the fall limit ->
  cut power and shorten the stride. / A brake will NOT save you: it switches the servo off.",
  consistent with the glossary at `:219-223` ("brake is how you END a stage, not how you save one").
  No contradicting line survives in the constant (`grep -n 'brake' src/cc/llm.nim`: `:213`, `:219`,
  `:223`, `:251` only).
- **282f0b6 (r1-F3)** — `src/continuous_control.nim:46-53`: randomise, then `config.update`, matching
  the module docstring at `:4-8`. I checked the regression risk the reorder creates: `seedPinned`
  (`:23-30`) has its own `try/except CatchableError: false`, so a malformed config still returns
  `false`, still falls into `config.update(parseJson(...))` at `:52`, and still exits through the
  clean `quit("continuous-control: invalid game config: …", 2)` at `:53-54`. Outcome is identical in
  both orders (pinned → JSON seed; unpinned → random); only the ordering the comment promises changed.
- **a2fb338 (r1-F4)** — `docs/PHYSICS.md:256-293` §The baseline bands. I compared every line against
  `tests/test_cc_baselines.nim:183-199`: hopper `0.3 .. 14.0`, cheetah `20.0 .. 58.0`, walker
  `8.0 .. 30.0`, trotter mean total `25.0 .. 90.0`, worst `> -10.0`, best `< 130.0`, plodder mean
  `> 5.0` and below trotter's, plodder-lower `≥ 80 %`, falls≤2 `≥ 80 %`. **All nine match exactly.**
  The doc's "means over 100 release seeds" is right: `Seeds = when defined(release): 100 else: 12`
  (`:8`) and `ci.yml:145-160` runs every test file in both debug and `-d:release`.
- **3f4bfb6 (r1-F5)** — `src/cc/body.nim:132-141`: `highY = mm(20_000)` with an eight-line
  justification. Verified the justification: `GuardMaxYQ16 = 20 * OneQ16` (`sim.nim:27`), guarded at
  `sim.nim:473`; `isUnhealthy` tests `y > spec.highY` at `body.nim:329`; and step 6 (stage
  termination, `sim.nim:566-581`) runs **before** step 8 (`assertInvariants`, `:599`), so a torso
  above 20 m resolves as `soFell` rather than faulting the episode, exactly as written. The hopper
  now has the note's two conditions (`design.md:277`) and the walker keeps its three
  (`body.nim:223-225`, `lowY = mm(800)`, `highY = mm(2000)`, `maxPitch = degQ16(57)`).
- **73b3f44 (r1-F6)** — `src/cc/report.nim:99-111`: `"joint_count": sim.spec.jointCount` (`:104`),
  `"joints": joints` (`:111`). `grep -rn joints_detail` over the whole tree: **zero hits**. The
  note's own example (`design.md:697-712`) does carry two `"joints"` keys in one object — a scalar
  `6` and the per-joint array — which is not constructible JSON; the note's prose
  (`design.md:735-736`, "`joints` and `feet` always have exactly the current morphology's counts")
  and its iteration both point at the array, which is the key the fix kept. `src/cc/llm.nim` names
  neither key, so the prompt did not need to change. `tests/test_cc_obs.nim:27,29,48,82` follow the
  rename with the same assertions.
- **b682a19 (r1-F13)** — `tests/test_cc_endcard_labels.nim:45-52`: the list grew 15 → 16 tokens and
  every substitution is *broader*: `hillchip` → `hill`, `killfeed(` → `kill`, plus a new `Cap<`.
  I verified the two documented narrowings are forced by running the test's own `stripJsComments`
  pipeline over the block in Python: on the 22 477 visible characters, `flag` hits **1**
  (`replay_broadcast.html:3311`, `ccEl('flag-alpha')` — the inherited element id) and `team` hits
  **5** (`:2997` `.plate .team-name`, `:3303` `'team-name plate-name'`, `:3523` `ec-teams`, `:3528`
  `ec-team win` ×2 — inherited chrome class names). Every other note token hits **0** at its exact
  spelling. Strictly stricter than before. Also see F8.
- **fece3c9 (r1-F14)** — `src/continuous_control_player.nim:74-88` (`ackFrame`), called at `:114`
  after every received message and after the `isNone` break — the same placement as the starter's
  `socket.send(readyBlob(), BinaryMessage)` at `coworld-ctf/src/paintball_player.nim:127`, whose
  `readyBlob` (`:48-55`) carries the same `char(0x85)` and the same justification. The send is
  wrapped in `try/except CatchableError: discard`. I checked the server side: a 1-byte `\x85` from a
  registered slot yields no `SpriteClientChatMessage` (`server.nim:642-645`), so `handled` stays
  false and `applyRegistration(slot, "\x85")` runs (`:647`) → `parseJson` raises →
  `return false` (`:576-580`), with no log and no state change. The ack is inert server-side.
- **04e39c9 (r1-F16)** — `docs/PHYSICS.md:104-145`, divergences 11–15. Spot-checked three: #11's
  crouch poses match `src/cc/gaits.nim:72-77` (hopper) and `:104` (walker) verbatim; #12's
  "a seek REWINDS AND RE-STEPS from tick 0" matches `src/cc/replay_runtime.nim:164-169`
  (`seekReplay` → `rewind` → step forward, `player.hashIndex = 0`); #13's tuning `--check` matches
  `ci.yml:114-115`; #14's "test 48 lives in `tests/test_cc_viewer.nim`" matches
  `tests/test_cc_viewer.nim:183`. See F6 for #15's byte count.
- **a8db2b3 (r1-F17)** — `src/cc/replays.nim:235-246`. The wire format is unchanged (`bytes()` at
  `:248-254` still writes `hashes.len` then the raw `u64`s positionally). The check is
  `if writer.hashes.len + 1 != tick: raise newException(CcError, …)`. I verified the invariant it
  asserts holds on both recorders and matches the reader:
  - `sim.tick` is incremented in exactly one place, `sim.nim:530`, and never reset (swept every
    `sim.tick` assignment in `sim.nim`), so the first `stepTick` of a fresh sim gives `tick == 1`
    against `hashes.len == 0`.
  - `stepTick` returns early **without** incrementing only when `phase == phGameOver or phLobby`
    (`sim.nim:527-528`); both call sites guard the loop with `phase != phGameOver`
    (`server.nim:362`, `helpers.nim:75`) and both set `phPlaying` before the loop
    (`server.nim:305`), so the early return cannot precede a `writeHash`.
  - Reader side: `replay_runtime.nim:151-157` consumes `data.hashes[player.hashIndex]` after each
    `stepTick` and increments — index 0 ↔ tick 1. Consistent with the writer's check.
  - If it ever did raise, `CcError = object of CatchableError` (`sim_types.nim:76`) is caught by
    `server.nim:401-405` → `endFault` → stop record → `finishEpisode` → bounded exit; and by
    `helpers.nim:96-99` → `endFault`, which tests 29/34 (asserting `reason == "complete"`) would
    catch. No new unbounded path.
  - Call sites updated in lockstep: `server.nim:365`, `tests/helpers.nim:78`,
    `tests/test_cc_replay.nim:173`. `grep -rn writeHash` finds no fourth caller.

Item 1 ("no test loosened"), for the delta:
- `git log -p 4c1b3101..a8db2b32 -- tests/` — every removed line is a `writeHash` call replaced by
  the two-argument form, a key rename replaced by the same assertion on the new key, the 15-token
  vocabulary list replaced by a 16-token stricter one, or a `detail` input replaced by a **longer**
  one. **Zero deleted assertions, zero `skip`/`xfail`, zero widened tolerances, zero removed files.**
  Net: 4 assertions added (`test_cc_replay.nim:199-201`, plus the vocabulary list's extra token).

Adjacent (scope item 3):
- `tests/helpers.nim:75-89` mirrors `server.nim:362-387` exactly for the hash/keyframe/stage writes;
  the only delta from the server is that helpers records order chat records with `view = nil`
  (`:71-72`), which is why the test replay is smaller than the 132 KB the smoke writes — pre-existing
  and already recorded in the r1 verdict.
- `tools/replay_summary.py` was not touched by any of the ten commits and its `stop` handling
  (`:172-177`) needs no change for the new cap; its strict decoder (`:78-85`) is what makes test 37's
  rune-boundary assertion meaningful.

---

## Could not determine

- **Whether the renderer-fixture step can see its iframes' console at all.** The head run's
  `renderer-fixture/viewer-smoke.json` has `console_tail: []` and `canvas_text.total: 0`, while the
  bundle step's has twelve captured `[error]` lines from the same code path. Since the fixture drives
  three iframes that each replay eleven events through `chrome.event` (`renderer_fixture.html:187-189`),
  I would expect ~33 identical errors if Playwright's `page.on("console")` relayed child-frame
  messages here. It reported none. Either the errors are not relayed from those iframes, or the
  iframes' `CcChrome` calls did not run in the way I read them — but `finish()` set
  `data-replay-loaded="true"` (`:222`), which requires `chrome` to have been found and the `try` at
  `:184-209` to have completed without setting `failed`, so the calls did run. Settled by: running
  `ci.yml:352-388` locally against a built bundle and reading `fixture-evidence/viewer-smoke.json`'s
  `console_tail`, or adding a `page.on("console")`-visible assertion inside the fixture.
- **The `Unknown sprite protocol message type: 97` / `: 34` warnings** in the bundle step's
  `console_tail` (3× and 15× respectively, run 33249877981). `97` is `'a'` and `34` is `'"'`, which
  looks like JSON text arriving on the sprite binary path, but I did not trace `broadcast_core.js`'s
  packet dispatch and will not guess. Settled by: reading the worker's `ingestPacket` dispatch
  against what `static_replay_worker.js` posts for a `.replay` file.
- **Whether the say row's `.feed-row.say` class would matter once F1 is addressed.** There is no
  `.say` rule in the page today (grep: 0 hits), so `cls` is inert either way; my F5 measurement used
  `class="feed-row say"` and matched the plain `.feed-row` metrics exactly. If a `.say` rule is ever
  added, F5's numbers no longer apply.
