# r1 review — board-gauntlet

Repo: `Metta-AI/cogame-board-gauntlet`, cloned to `/workspace/cogame-board-gauntlet`
Range: whole tree at `ad8054c3207ee0ff3c5ff5ec90185a57215d3f82` (`main` head; 4 commits from
`95e9ad2` "Initialise the repository")
Starter for provenance: `/workspace/starters/cogame-babel` @ `d55d999`
Design note: `/workspace/coworld-builder/runs/2026-08-27-board-gauntlet/design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15)
Files read: 40 of 55 in the tree (all Nim, all client/, all replay-viewer/, all tests/, all
`.github/workflows/`, all `tools/`, the manifest, `compose.yaml`, `Dockerfile`, `README.md`,
`gauntlet.nimble`); plus CI logs and artifacts for run `33035395418`.

CI evidence used: `gh run list -R Metta-AI/cogame-board-gauntlet --branch main -w ci.yml` →
`completed success … 33035395418`; `gh run view 33035395418` → `docker-smoke 1m21s`,
`test 7m20s`, `wasm-viewer 2m42s`, all ✓; full log pulled to `/tmp/ci.log` (3686 lines);
artifact `renderer-fixture` downloaded and its `viewer-smoke.json` read.

Counts: **2 blocking (my read)**, **20 advisory**.

---

## Blocking

### B1 — The canvas `say` band ellipsizes a full-cap remark; the renderer fixture reports `ellipsized: 7106`, and every sample is a remark, not a nameplate
- Where: `client/renderer.js:470-497` (`drawSayBand`), specifically
  `client/renderer.js:480` and `client/renderer.js:494`.
  Evidence: CI run `33035395418`, job `wasm-viewer`, step *"Renderer fixture at 360 / 640 /
  1280 px"*, log line
  `canvas text: 66544 drawn, 0 never inside the canvas (0 draws crossed an edge), 7106
  ellipsized (--strict-text-bounds)`; and artifact `renderer-fixture/viewer-smoke.json`
  `canvas_text.samples`, all twelve of which are
  `{"kind":"ellipsized","text":"Sprocket: “centre file, then count both diagonals — 日日日日日日日日"}`
  / `{"kind":"ellipsized","text":"Flywheel: “their path is nine and mine is six, so I run — 日日"}`.
- Observed, traced step by step:
  1. `layoutOf` (`client/renderer.js:123-158`) reserves the band **vertically**:
     `var sayBand = lineH * 2 + Math.round(12 * scale);` (line 131) and
     `sayTop: h - sayBand` (line 149). That part works — `never_inside` is `0` and
     `outside` is `0`, so nothing lands at a negative coordinate.
  2. `drawSayBand` then computes the **horizontal** budget as the whole canvas width, not
     from the cap: `var width = Math.max(40, layout.w - pad * 2);` (line 480), directly
     under the comment *"The band is measured from the CAP, not from the current text"*
     (lines 478-479). Nothing in the proc measures `MAX_SAY_LEN` (declared at line 44) in
     the render font.
  3. The string is assembled as
     `C.clampName(info.name) + ": “" + say.slice(0, 80) + "”"` (lines 485-492) — one line
     per seat, two seats, so ~92 runes on one line.
  4. It is then **cut to fit**: `ctx.fillText(C.ellipsize(ctx, text, width), pad, y);`
     (line 494). `C.ellipsize` is `client/chrome_common.js:55-62` (babel's, byte-identical),
     which appends `…` — which is exactly the marker `viewer_smoke.mjs:368`
     (`/\u2026\s*$/.test(str)`) counts as `ellipsized`.
- Checklist item: **15**, third bullet — *"Ellipsis is a design choice for labels (a card
  name in a 52 px card) and a defect for sentences. If `ellipsized` counts a remark rather
  than a nameplate, the box is too small — widen the band, do not shorten the text."*
- What the note says it should do: `design.md:1016-1018` — *"this ply's `say` in a **reserved
  band** sized from `MaxSayLen = 80` measured in the render font at the current `--hudscale`,
  so a full-cap line can never be laid out at a negative coordinate"*. The code satisfies the
  *negative-coordinate* half (vertical reservation) and does not satisfy the *sized from the
  cap* half horizontally.
- Why blocking: the gate the checklist installs for exactly this case fires. `ellipsized`
  counts remarks; the scorebug plate-name ellipsis (`board-gauntlet-grandmas…`, visible in
  the same step's `scorebug:` readout) is the legitimate *label* case, and it is a DOM
  ellipsis that this counter never sees. The 7106 canvas ellipsis events are all sentence
  truncations of the model-authored `say`.
- Inference (labelled): the counter does not break down by width. From the draw mix
  (~10–18 board-label draws + 2 say draws per frame) I estimate say draws at roughly 12 % of
  66544 ≈ 8000, of which 7106 (~89 %) were ellipsized; at 1/3 of cycles per width that ratio
  is only reachable if it also happens at 640 px and probably at 1280 px. I did **not**
  confirm the per-width split — see *Could not determine*.

### B2 — `client/chrome_common.js` carries a **seventh** edit to the copied chrome; the design note records exactly six
- Where: `client/chrome_common.js:263-269`
  (`// BOARD-GAUNTLET EDIT 7 (starter lines 994-999)` … `"DRAWN";`), also declared in the
  file header at `client/chrome_common.js:19` (*"Exactly six copied lines/regions are
  edited"*) and enforced by `tools/ci/chrome_scope_check.mjs:126`
  (`for (let edit = 1; edit <= 7; edit += 1)`).
- Observed: I diffed `sed -n '230,327p' client/chrome_common.js` against
  `sed -n '963,1048p' /workspace/starters/cogame-babel/client/renderer.js`. The hunks are:
  - EDIT 6 (`reasonLine`, rounds → plies) — recorded in the note (row 6).
  - EDIT 7 (`updateEndscreen` verdict + title):
    `escapeHtml(names[topIndex]) + " LEADS THE TABLE" : "ALL LEVEL"` →
    `escapeHtml(clampName(names[topIndex])).toUpperCase() + " WINS" : "DRAWN"`, and
    `FINAL — <rounds> ROUND(S)` → `FINAL — <plies> PLY/PLIES`. **Not in the note's table.**
  - EDIT 5a / 5b (`endColumns` injection) — recorded in the note (row 5).
  I separately confirmed the other six edits match the note's table exactly (edits 1, 2, 3 in
  `renderFeed`/`blockHead`; edit 4 in `buildScrub`; edits 5a/5b; edit 6), and that every other
  copied region is byte-identical to `d55d999` (regions 101-124, 680-733, 735-744, the
  unedited parts of 790-863, 972-1027, 1029-1048, 1142-1222).
- Checklist item: **14**, first bullet — *"`client/chrome_common.js` is byte-identical to the
  starter's …; the only admissible change is a named, minimal patch **recorded in the design
  note**."*
- What the note says: `design.md:929` — *"**Exactly six copied lines/regions are edited**, and
  each is named here so a reviewer can find it — everything else in the file is copied bytes
  or appended at the end"*; the table at `design.md:933-939` lists six rows and does not
  include the endcard verdict/title.
- Why blocking: the checklist's admissibility test for a chrome edit is "recorded in the
  design note", and this one is not. **Counter-reading I am obliged to state:** the edit *is*
  named in place, *is* minimal (six lines), is asserted by CI
  (`tools/ci/chrome_scope_check.mjs:126-131` requires markers 1–7), and implements a
  requirement the note *does* state elsewhere — `design.md:1030-1032`, *"the verdict
  (`SPROCKET WINS` / `DRAWN`)"*. A judge could reasonably rule that the substance is recorded
  and only the provenance table is stale. I report it as blocking because the checklist names
  the design note as the register; I do not rank it.

---

## Non-blocking

### N1 — The renderer fixture never asserts that its own `say` strings are still full length
- Where: `tools/ci/renderer_fixture.html:86-94` (`fullCapSay`, `SAYS`).
- Observed: `fullCapSay` appends `日` until `Array.from(text).length < 79` is false, then
  appends `✨` — so the string is 80 runes **by construction**. There is no `if`/`throw`/
  console-error anywhere in the page, and `viewer_smoke.mjs` has no full-length check.
- Checklist item 15, last bullet: *"The fixture asserts its own strings are still full-length
  — one quietly shortened remark leaves it passing while testing nothing."* Literally unmet.
  My read: advisory rather than blocking, because the construction is deterministic and I
  verified from the code that the strings are 80 runes; a judge may read the "asserts"
  requirement literally and disagree.

### N2 — Connect Four bot-diversity threshold is 25 %, the note says 30 % (builder deviation #1, verified)
- Where: `tests/test_bot.nim:140-143`
  (`if game == gConnectFour: check share >= 0.25 else: check share >= 0.30`), with the
  deviation written out at `tests/test_bot.nim:106-115`.
- Note: `design.md:434` and `design.md:1255` both say *at least 30 %*, per game.
- My read of the deviation-as-described: it matches the code exactly. It is **not** a
  loosened test — `git log --oneline --stat -- tests/` shows the four test files were added
  in a single commit (`cee5659`) and never touched since; `git log -p -- tests/test_bot.nim`
  shows `check share >= 0.25` present in the original hunk. Checklist item 1's "no test
  loosened" is therefore verified as satisfied. It falsifies no checklist item.

### N3 — `complete/no-moves` is the one ending never run through `replayMatch` (builder deviation #2, verified)
- Where: `tests/test_replay.nim:269-293` (`"no-moves settles the starved seat identically on
  both paths"`). The test hand-builds a board (`sim.board[cellIndex(...)] = …`, lines
  277-282), copies it to `twin`, applies `c4-c5` on both, and compares
  `twin.boardStateJson() == sim.boardStateJson()`. That is two **live** runs; `replayMatch`
  is never called, and `checkReDerives` (line 112) is not used here.
- The other eight endings are covered with full frame-by-frame `checkReDerives`:
  `tests/test_replay.nim:141-240` (line, board-full, home-rank, no-pieces, connection,
  goal-row, ply-cap, asserted by `check covered == @[…]` at line 239) and
  `tests/test_replay.nim:242-267` (deadline/wall-clock, all four games).
- Note: `design.md:1264-1267` — *"For **every** end reason/ending pair — all eight
  `complete/*` endings and `deadline/wall-clock` — record an episode, run `replayMatch` over
  its events, and assert every frame's `boardStateJson` is identical to the live one."*
- My read: the deviation is as the builder described (unreachable from the standard opening,
  so hand-built). Checklist item **2** requires *"a test asserts it"* — one does, for eight of
  nine endings — so this does not falsify item 2. Note that the `no-moves` path itself *is*
  re-derivable: `sim.nim:295-303` emits the `win` inside `advance`, and `replayMatch`'s
  `evWin` branch (`sim.nim:573-589`) compares seat/how/path; nothing in the path is
  recording-only.

### N4 — Two byte-copied regions the note's provenance list does not mention (builder deviation #4, verified)
- Where: `client/chrome_common.js:46-47` (`COPIED-REGION 23`, `COLORS`) and
  `client/chrome_common.js:49-52` (`COPIED-REGION 85-87`, `seatColor`).
- I diffed both against `sed -n '23p;85,87p' /workspace/starters/cogame-babel/client/renderer.js`:
  byte-identical. `design.md:925-927` lists eight regions and omits these two.
- My read: they are copied bytes, so they cannot violate "byte-identical"; they are needed
  because the copied `renderFeed` (line 181) and `updateEndscreen` (line 262) reference
  `COLORS`/`seatColor`. Advisory. `tools/ci/chrome_scope_check.mjs:113-116` does list all ten
  regions, so the file and its guard agree even though the note does not.

### N5 — `say` is drawn in a reserved **canvas** band, not in the scorebug plate (builder deviation #5, verified)
- Where: `client/renderer.js:470-497` draws it on `canvas#table`; `scorebugHtml`
  (`client/renderer.js:657-691`) emits `.plate-name`, `.plate-alias`, `.plate-readout`,
  `.plate-score`, `#evalbar` and **no** say element.
- Note: `design.md:1013-1018` puts the say in the scorebug plate.
- My read: the deviation matches the code. It is what makes B1 measurable at all (a DOM say
  would be invisible to `canvas_text`), so it is not itself a defect; it is the *width* of
  the band that B1 is about.

### N6 — The renderer fixture runs as the main frame, not in an iframe (builder deviation #6, verified)
- Where: `tools/ci/renderer_fixture.html:26-31` states the deviation; the page itself loads
  `./chrome_common.js` and `./renderer.js` at lines 76-77 and drives
  `GauntletRenderer.attachReplay` at line 307, with no `<iframe>` anywhere in the file.
- Note: `design.md:1328-1329` — *"loads the **shipped** `dist/static-replay-viewer/index.html`
  in an iframe, shims only the wasm entry"*.
- My read: the stated reason checks out — `viewer_smoke.mjs` installs its canvas wrapper via
  an init script and reads it back with `page.evaluate()`
  (`tools/ci/viewer_smoke.mjs:340-358`, `:601`), which only sees the main frame. The fixture
  is copied into `dist/static-replay-viewer/` before it runs (`ci.yml:348`), so every relative
  path (`./chrome.css`, `./chrome_common.js`, `./renderer.js`, `./assets`) resolves to the
  shipped bundle. It does load the shipped code; it does not reuse the shipped `index.html`
  markup via an iframe, it retypes the markup (lines 47-75). Falsifies no checklist item —
  item 15 asks for *"a page that loads the real `client/renderer.js`"*, which it does.

### N7 — Narrow-viewport rules duplicated as `body.narrow-*` classes (builder deviation #7, verified)
- Where: `client/chrome.css:599-616` (the `@media (max-width: 640px)` and
  `@media (max-width: 360px)` blocks) and `client/chrome.css:619-636` (the same declarations
  keyed on `body.narrow-640` / `body.narrow-360`); driven from
  `tools/ci/renderer_fixture.html:294-296`.
- The duplication is entirely below the `===== board-gauntlet game block =====` banner
  (`client/chrome.css:445-450`). I verified `head -443 client/chrome.css` is byte-identical to
  `/workspace/starters/cogame-babel/client/chrome.css` — not one starter rule edited or
  deleted, as `design.md:915-919` requires. Checklist item **14** and item **11** both hold:
  `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` is at `client/chrome.css:484-487` and
  `.plate-label { display: none; }` at `client/chrome.css:600`.
- My read: advisory only; the duplication is a fixture affordance, not a starter edit. The
  two copies are currently identical declaration-for-declaration (I compared them line by
  line); they can silently drift, which is what a reviewer should note.

### N8 — The release workflow's certify step does not pass `--timeout-seconds 300`
- Where: `.github/workflows/coworld-release.yml:173-181` — the only flag is
  `--no-open-report`. The only `--timeout-seconds` in the file is `900` on `upload-coworld`
  (`:317`).
- Note: `design.md:476` and `design.md:1183` both say the certify step passes
  `--timeout-seconds 300`.
- My read: `diff` of `templates/coworld-release.yml` (with `<slug>`/`<IMAGE>`/`<SEATS>`
  substituted) against the repo's copy is **empty** — the workflow is the scaffold verbatim,
  and the scaffold has no such flag. So this is a design-note claim the template never
  supported, not a regression. Checklist item **12** asks for the *order*
  (build → certify → upload-policies → upload-coworld → secret put), which I verified at
  `:159`, `:173`, `:212`, `:310`, `:348`. Item 12 holds.

### N9 — `soldier_red_front.png` / `soldier_blue_front.png` are not byte-copies of babel's
- Where: `data/soldier_red_front.png`, `data/soldier_blue_front.png`. `cmp` against
  `/workspace/starters/cogame-babel/data/` differs; dimensions are 192×192 here vs 180×192 in
  babel. `data/arena_floor.png`, `data/font.ttf` and `data/FONT_LICENSE.txt` **are**
  byte-identical.
- Note: `design.md:1044-1045` — *"copied from babel; the two seat avatars in the scorebug
  plates."*
- Observed cause (inference): the repo ships `scripts/art/generate_cog_sheet.py`,
  `scripts/art/split_cog_sheet.py` and `scripts/art/source/cog_seats_sheet.png`, so the
  avatars appear to have been regenerated rather than copied. Not a checklist item (item 14
  covers chrome files, not art). Advisory; the note's §Art is inaccurate as written.

### N10 — Three appended chrome helpers the note's appended-list omits
- Where: `client/chrome_common.js:431-433` (`setBeatNames`), `:435-439` (`beatSeatName`),
  `:441-460` (`beatLabel`).
- Note: `design.md:941-943` — *"**Appended** at the end of `chrome_common.js`, in this order:
  `relayout()`, `markPlyBeat()`, `setFeedText()`, `setEndColumns()`, and the
  `window.GauntletChrome` export."*
- My read: all three are appended below the `BOARD-GAUNTLET additions` banner
  (`client/chrome_common.js:408-410`), so no copied byte is touched. Advisory.

### N11 — A fourth change to the three inherited pages the note's "three changes" does not list
- Where: `client/replay_broadcast.html:14`, `client/global.html:14`, `client/player.html:14` —
  `<div id="clock">ROUND 0</div>` → `<div id="clock">PLY 0</div>`.
- Note: `design.md:968-970` — *"**Changed:** the `<title>` text, the `#wordmark` inner text …
  and the `<script src>` list"*.
- Observed from full `diff` against babel's `client/replay.html` / `global.html` /
  `player.html`: the diffs are title, wordmark, `#clock` placeholder text, the added
  `chrome_common.js` script tag, `BabelRenderer` → `GauntletRenderer`, and the appended
  `<script>` block under the named banner. **Nothing is removed** — item 14's rewrite test
  passes cleanly (93 lines here vs 74 in the starter, i.e. the starter plus an appended
  block, not a fraction of it).

### N12 — Connect Four `normalizeMove` reads the first standalone one-character token, not "the first character"
- Where: `src/gauntlet/games/connect_four.nim:157-183`. The proc replaces every non-`a-z0-9`
  byte with a space (lines 173-176), splits on whitespace, and returns the first token that
  is a single legal file letter or digit (lines 177-180), falling back to `cleaned[0]`
  (line 183).
- Note: `design.md:831-832` — *"the first character must be a file letter `a`..`g`, or a digit
  `1`..`7` … anything after it is ignored (`"d"`, `"D"`, `"4"`, `"column d — centre"` all mean
  `d`)."*
- My read: the note is self-inconsistent — a literal "first character" rule reads
  `"column d — centre"` as `c`, which contradicts the note's own example. The code
  implements the example. `tests/test_sim.nim:494-497` pins both readings
  (`"column d — centre"` → `d`; `"b2-c3"` → `b`, *"first standalone token"*). Advisory.

### N13 — The play-deadline guard can be overshot by ~2 s because the spacing sleep and turn delay sit outside it
- Where: `src/gauntlet/server.nim:295-302` (the guard),
  `:308-316` (spacing sleep), `:320` (the call), `:338-339` (turn delay).
- Observed: the guard refuses to open a ply unless
  `epochTime() + worstPlySeconds <= playDeadline` with
  `worstPlySeconds = float(2 * config.llmTimeoutSeconds + 2)` = 62 (`:276`). After the guard
  passes, the loop may sleep up to `plySpacing` (4 s, `:277-279`, `llm.nim:34`), then spend
  up to 2 × 30 s in `decide`, then `turnDelayMs` (0.25 s). Worst case the settle lands at
  `playDeadline − 62 + 4 + 60 + 0.25 ≈ playDeadline + 2.25`.
- Checklist item **5** — *"the episode settles and scores inside 60 % of
  `episodeTimeoutSeconds` (720 s of 1200)"*. My read: **not** falsified in substance — 722 s
  of a 1200 s budget, with `finishEpisode`'s 0.5 s + artifact write + 20 s grace
  (`server.nim:217-232`, `ShutdownGraceSeconds = 20` at `:41`) landing at ≈ 743 s. Every wait
  in the file is bounded; there is no unbounded loop and no blocking read. Reported so the
  judge sees the arithmetic rather than the design note's version of it.

### N14 — An `output_config: {"effort": "low"}` field on non-Haiku Anthropic requests, unmentioned in the note
- Where: `src/gauntlet/llm.nim:544-547`. Guarded by
  `if "haiku" notin client.model and "4-5" notin client.model`. The default model is
  `"claude-sonnet-5"` (`src/gauntlet/types.nim:207`), so it *is* sent on the default
  Anthropic path.
- The note (`design.md:441-446`) names `model`, `maxOutputTokens` and the Bedrock candidate
  list but not this field. Advisory; the Bedrock path (`llm.nim:537-541`) never sends it.

### N15 — Two log lines emit untruncated error text
- Where: `src/gauntlet/server.nim:329` (`echo "board-gauntlet: move rejected (", error.msg`)
  and `src/gauntlet/server.nim:483` (`"ignoring bad player frame: ", error.msg`).
- Note: `design.md:840-842` — *"any error text that reaches an event or the log (200)"*.
- My read: neither reaches an event or the replay. `llm.nim:622` and `llm.nim:625` (the
  fallback lines) *do* use `cleanText(error.msg, MaxErrorLen)`, and
  `extractJsonObject`/`completeText` cap the model text they quote (`llm.nim:525`, `:553`,
  `:562`, `:567`, `:576`). Checklist item **9** is about strings that reach the replay, and
  those are all capped. Advisory.

### N16 — The `no-moves` feed line differs from the note's wording
- Where: `client/renderer.js:574-575` — `case "no-moves": return "wins: the opponent has no
  legal move";`
- Note: `design.md:1027` — *"`Gizmo has no legal move`"* (i.e. the note phrases it as the
  **starved** seat's line; the code phrases it as the **winner's**). The event's `seat` is the
  victor (`sim.nim:300`), so the code's phrasing is the one that is factually right for the
  seat it names. Advisory.

### N17 — `headerText` gates the size word on `window.innerWidth`, which the fixture cannot narrow
- Where: `client/renderer.js:645` — `if (window.innerWidth >= 640) head += " " + size;`
- The fixture narrows `#layout`/`document.body` in place (`renderer_fixture.html:286-300`)
  because a page cannot resize its own viewport; `window.innerWidth` stays at the browser
  width. So the "clock drops the size word at 360 px" behaviour (`design.md:1036`) is present
  in the code but is **not** exercised by any CI gate. Consistent with the fixture's own
  `body.narrow-*` workaround for the CSS, which was not extended to this JS branch.

### N18 — The fixture stacks `attachReplay` drivers, inflating the `canvas_text` totals
- Where: `tools/ci/renderer_fixture.html:302-322`. `cycle()` calls
  `GauntletRenderer.attachReplay(...)` every 1200 ms and never tears down the previous call's
  `requestAnimationFrame` loop (`client/renderer.js:825-852` starts a fresh self-scheduling
  loop each time). Over the 16 s soak that is ~13 concurrent draw loops on one canvas.
- Consequence for reading the evidence: `total: 66544` and `ellipsized: 7106` are both
  inflated by the same factor, so the *ratio* in B1 stands but the absolute counts are not a
  per-frame figure. Advisory.

### N19 — A `/client/replay` HTTP route exists on the game container
- Where: `src/gauntlet/server.nim:499` — `result.get("/client/replay",
  htmlHandler("replay_broadcast.html"))`, registered in both live and replay mode
  (`buildRouter`, `:495-507`).
- Checklist item **3** says *"No `/client/replay` pod path anywhere."* My read: this does not
  falsify item 3, and I state my reasoning rather than assert it. (a) The route is inherited
  verbatim — `/workspace/starters/cogame-babel/src/babel/server.nim:502` has the identical
  line. (b) The design note declares it (`design.md:728`, `design.md:961`). (c) The manifest
  declares only the static bundle: `coworld_manifest_template.json:18-20`
  `"replay_viewer": {"bundle": "static-replay-viewer"}` **inside** `game`, and the global
  protocol text at `:351` ends *"hosted replays are served by the STATIC wasm bundle
  (index.html?replay=<url>), **never by a pod**"*. (d) The release workflow hard-fails if
  certification does not report the static bundle
  (`.github/workflows/coworld-release.yml:198-207`). Flagged because it is a literal
  text match for the checklist's phrase.

### N20 — No grid harness exists for the baselines
- Checklist item **7**, second sentence: *"The baseline's parameters were tuned with a grid
  harness, not guessed."* There is no harness in the tree (`tools/` holds
  `build_replay_viewer.sh` and `ci/{chrome_scope_check.mjs, docker_smoke.sh, policies.json,
  renderer_fixture.html, viewer_smoke.mjs}`; `scripts/` holds three art scripts).
- Observed: the baselines have **no numeric parameters**. `tacticianMove`
  (`src/gauntlet/llm.nim:154-184`) and `hustlerMove` (`:261-287`) are pure one-ply lookahead
  over `legalMoves` / `applyProbe` / `standing`, with no thresholds, weights or constants.
  The only tunable numbers are the four `standing` definitions
  (`connect_four.nim:13`, `breakthrough.nim:161`, `hex.nim:152`, `quoridor.nim:402`), all of
  which are fixed verbatim by `design.md:212-223`.
- My read: item 7's first sentence is satisfied (see *Traced and consistent*); the "grid
  harness" clause has nothing to bind to here. Advisory, flagged so the judge can rule.

---

## Traced and consistent

**Resolution rules — the 12-step ply order** (`src/gauntlet/sim.nim:249-305`,
`src/gauntlet/server.nim:287-343`)
- Step 1 `beginPly` / `mover = (first + p) mod 2` — `sim.nim:294`, and `initSim` seeds
  `result.mover = config.first` (`sim.nim:67`). Asserted by `tests/test_sim.nim:450-463`.
- Step 2 wall-clock guard **before** any observation is built — `server.nim:295-302`, inside
  the same `withLock` block that reads `state.sim.mover`, before `simCopy = state.sim`
  (`:304`). `worstPlySeconds = 2 × llmTimeoutSeconds + 2` (`:276`);
  `playDeadline = gameStart + timeoutSeconds × PlayBudgetFraction` (`:270-272`) with
  `PlayBudgetFraction* = 0.6` (`:38`) and the 1200 s assumption when
  `COWORLD_TIMEOUT_SECONDS` is absent (`:263-269`). 0.6 × 1200 = 720 s, as the note says.
- Step 3 observation uses the same `legalMoves` the validator applies —
  `llm.nim:501-503` calls `sim.legalMoves()`; `sim.applyMove` gates on `sim.isLegalMove`
  (`sim.nim:314`), which dispatches to the same per-game predicate the `legalMoves` scan uses
  (`sim.nim:89-97`).
- Step 4 one LLM call bounded by `llmTimeoutSeconds` —
  `client.curl.post(url, headers, $body, client.timeoutSeconds)` (`llm.nim:551`);
  `timeoutSeconds: config.llmTimeoutSeconds` (`llm.nim:119`).
- Step 5 parse + legality probe on a **copy** — `llm.nim:611-617`:
  `extractJsonObject(client.completeText(...))` → `sim.parseReply(...)` →
  `var probe = sim; probe.applyMove(decision.move, …)`. `fallbacks[mover] += 1` happens in
  `sim.nim:261-262`; `illegalReplies[mover] += 1` in `server.nim:323-324`; the
  `falling back` stdout line at `llm.nim:625-626`.
- Steps 6–7 apply + record — `sim.nim:257-272`; `mkind` from `sim.lastKind`, `capture` from
  `sim.lastCapture` via `cellName`, both re-derivable.
- Step 8 win check for the mover — `sim.nim:273-286`.
- Step 9 draw check, Connect Four only — `sim.nim:287-291`, correctly **after** the win check.
- Step 10 starvation — `sim.nim:292-303`; the mover is advanced first (`:294`) so
  `settle`'s `of "no-moves": sim.winner = 1 - sim.mover` (`sim.nim:220-221`) names the seat
  **not** to move, matching `design.md:305`. Asserted by `tests/test_sim.nim:301-323`.
- Step 11 ply cap — `sim.nim:304-305`.
- Step 12 pacing — `server.nim:338-339` (`turnDelayMs`) and `:308-316` (the 4 s LLM-only
  spacing floor, gated on `usesLlm` so the all-scripted cert path is unaffected).

**Per-game legality and win detection**
- `connect-four`: `dropRow` returns the lowest empty rank (`connect_four.nim:31-36`);
  `columnOrder` gives `d c e b f a g` on 7 files (`:18-29`); `windows` yields 24 + 21 + 12 + 12
  = 69 on 7×6 and `standing` skips any window holding an opponent disc (`:104-119`) — the 69
  count is pinned by `tests/test_sim.nim:216-228` (`total == 4 * 69`).
- `breakthrough`: `stepLegal` allows a straight step only onto empty and a diagonal onto
  anything not one's own (`breakthrough.nim:31-44`); `homeRankOf` is `rows-1` / `0`
  (`:14-16`); `terminal` returns `home-rank` then `no-pieces` (`:124-134`).
  Canonical order is `from` row-major then straight / left / right (`:53-64`,
  `moveOffsets` yields `0, -1, 1`), exactly `design.md:413-414`.
- `hex`: `HexNeighbours = [(0,-1),(0,1),(-1,0),(1,0),(-1,1),(1,-1)]` (`hex.nim:13`) is the
  note's neighbourhood verbatim; I hand-checked `c4` → `{b4,d4,c3,c5,b5,d3}` and `a1` →
  `{b1,a2}`, matching `tests/test_sim.nim:328-336`. Seat 0 links col 0 → col `cols-1`, seat 1
  row 0 → row `rows-1` (`hex.nim:50-55`), i.e. file `a`→`g` and rank `1`→`7`.
  `distToWin` is a real 0–1 BFS with `Unreachable = 99` (`:104-149`).
- `quoridor`: I checked the wall algebra by hand. `wallEdges(row,col,horizontal=true)` =
  `[(true,row,col),(true,row,col+1)]` (`quoridor.nim:180-185`) = the two vertical steps
  `(x,N)↔(x,N+1)` and `(x+1,N)↔(x+1,N+1)`; the vertical case gives the note's two horizontal
  steps. `blockedVertical`/`blockedHorizontal` (`:47-57`) correctly consult the two anchors
  that can block a given step, and `stepBlocked`'s four directions (`:59-64`) map onto
  `Dirs = [(1,0),(0,1),(-1,0),(0,-1)]` (`:14`). `wallSlotFree` (`:195-213`) enforces walls
  left, anchor free of **either** orientation, and neither blocked step already blocked —
  all three of `design.md:187-191`. `wallKeepsRoutes` (`:266-278`) falls back to a fresh BFS
  for both pawns whenever the candidate touches either stored shortest route, so the path
  invariant is exact, not approximate. `pawnMoves` (`:283-316`) offers the straight jump when
  on-board and unblocked and **only then** falls through to the two perpendicular diagonals —
  `design.md:194-199` — pinned by `tests/test_sim.nim:409-430`.

**Decision path** (`src/gauntlet/llm.nim:592-628`) — Checklist item 8
- Tolerant parse: `extractJsonObject` takes `text.find('{')` … `text.rfind('}')`
  (`llm.nim:518-526`), so fences and prose either side are tolerated.
- Exactly one retry: `for attempt in 0 .. 1` (`:604`), with the hint appended on `attempt > 0`
  (`:606-609`) carrying `sim.legalMoves().join(" ")` — the same proc the validator applies.
- Fallback: `Decision(move: scriptedMove(sim, blTactician), scripted: false, fellBack: true,
  illegal: illegal)` (`:627-628`); `illegal` is set from the two error shapes at `:619-620`.
- Recorded for phase 60: `results.fallbacks[]` and `results.illegalReplies[]`
  (`sim.nim:390-391`, `:408-409`), both declared in `results_schema`
  (`coworld_manifest_template.json:299-318`), plus per-event `fellBack`
  (`sim.nim:272`, `:494`).
- No-credential path: `newLlmClient` sets `disabled = true` and echoes once (`llm.nim:141-145`);
  `decide` short-circuits to `tactician` at `:599-600`. Auth failure sets `client.disabled`
  (`:558`) and the loop `break`s at `:623-624`, so there is no second network wait.
- `decide` **never raises** (every failure path is inside `except CatchableError` at `:618`),
  and the server has a second belt at `server.nim:325-332`.

**Every wait and its bound** — Checklist item 5
- Player connect: `while epochTime() < connectDeadline` with
  `connectDeadline = gameStart + config.playerConnectTimeoutSeconds` (`server.nim:241-249`),
  default 180 (`types.nim:206`).
- LLM: curly timeout, above.
- Spacing floor: `sleep(int(wait * 1000))` where `wait ≤ plySpacing` (4 s) and only when
  `usesLlm` (`server.nim:309-316`).
- Turn delay: `sleep(config.turnDelayMs)`, clamped by
  `min(turnDelayMs, 120_000 div maxPlies)` in `sampleEpisode` (`types.nim:337-338`).
- Shutdown grace: `sleep(ShutdownGraceSeconds * 1000)` then `quit(0)`
  (`server.nim:230-232`), `ShutdownGraceSeconds = 20` (`:41`).
- Main loop termination: every iteration either settles, or calls `advance`, which
  unconditionally `inc sim.plies` (`sim.nim:283`, `:289`, `:292`) and settles at
  `plies >= maxPlies` (`:304`). `maxPlies` is bounded 4..200 (`types.nim:303-304`).
- No round barrier exists (alternating play); no blocking read anywhere — the only reads are
  websocket callbacks in mummy's own threads.
- Simultaneous batch: n/a and correctly documented as such at `server.nim:18-21` and
  `design.md:235-243`. One seat decides per ply by construction.

**String truncation** — Checklist item 9
- One shared `cleanText(text, cap)` (`types.nim:121-131`): strips, collapses `\r\n`/`\n`/`\t`
  to spaces, and on overflow does `result.runeSubStr(0, cap - 1) & "\u2026"` — a **rune**
  cut, not a byte cut.
- Caps: `MaxMoveLen* = 12`, `MaxSayLen* = 80`, `MaxNotesLen* = 400`, `MaxPromptLen* = 4000`,
  `MaxErrorLen* = 200` (`types.nim:21-25`). Applied at `llm.nim:584-585` (say/notes),
  `sim.nim:184` (move, inside `normalizeMove`), `server.nim:464` (prompt).
- Test at exactly the cap with multi-byte input: `tests/test_replay.nim:354-400` builds
  `MaxSayLen + 20` × `日` plus `✨`, asserts `cutSay.runeLen == MaxSayLen`,
  `validateUtf8(cutSay) == -1`, `validateUtf8(bytes) == -1` on the whole serialised replay,
  and that a strict `parseJson` round-trips it; `:374-378` asserts the exactly-at-cap case is
  untouched.

**Replay writer** (`src/gauntlet/server.nim:150-176`) — self-sufficiency
- `protocol: "gauntlet.replay.v1"` (`:33`, `:170`), `names` (aliases, `:163-165`),
  `policyNames` (`:77-82`, `:172`), `config` with
  `game, rotated, size, walls, first, seed, maxPlies, sampled:true` (`:150-160`), `events`,
  `results`. Exactly the shape at `design.md:850-856`. Asserted key-by-key by
  `tests/test_replay.nim:417-441`, including `config.game != "rotate"` (`:429`).
- The seed is always concrete: `drawSeed()` runs **before** `sampleEpisode`
  (`src/gauntlet.nim:26-31`), so a replay never carries `seed: 0`. Pinned by
  `tests/test_sim.nim:121-132`.
- Rotation resolved before recording: `sampleEpisode` sets
  `game = RotationOrder[((seed mod 4) + 4) mod 4]` and `rotated = true`
  (`types.nim:323-326`), is idempotent on `sampled` (`:321-322`). Pinned by
  `tests/test_sim.nim:86-103`.
- `finishEpisode` order — final frames to players (`server.nim:198-215`), then `results.json`
  (`:219-222`), then the replay (`:223-226`) — matches `design.md:495-497`.

**Viewer re-derivation** — Checklist item 2
- `replayMatch(config, events)` (`sim.nim:544-598`) re-runs `initSim` + `applyMove` per
  recorded move and applies `evEnd` through the **same** `settle` (`:590-593`), and it
  *checks* the recording against the derivation: `mkind` (`:565-568`), `capture` (`:569-572`),
  `win.seat`/`how`/`path` (`:584-589`), and end reason/ending (`:594-597`), raising
  `GauntletError` on any mismatch. `tests/test_replay.nim:298-349` doctors each of those five
  fields plus an illegal recorded move and expects a raise each time.
- The wasm entry uses that same proc and emits `states[i] = boardStateJson` after
  `events[0..<i]` — `replay-viewer/gauntlet_replay.nim:49-51`. The pod page's server does the
  same via `statesFromEvents` (`server.nim:178-182`).
- The renderer draws **only** `states[...]`, never a parallel recording:
  `currentState()` at `client/renderer.js:800-802`, used by `setIndex` (`:815-818`) and by the
  frame loop (`:843`). Nothing in `attachReplay` recomputes board state.
- Frame-by-frame equality is asserted with a per-key diff by
  `tests/test_replay.nim:112-133` and exercised for all eight endings other than `no-moves`
  (see N3), including `deadline/wall-clock` for all four games (`:242-267`).

**Viewer executes** — Checklist item 13
- `ci.yml`'s `wasm-viewer` has `needs: docker-smoke` (`.github/workflows/ci.yml:218`); the
  step *"Load the bundle in a real browser"* (`:305-337`) is a plain `run:` with no
  `continue-on-error` and no `if:` (the only two `if:` in the file are `always()` on
  artifact uploads, `:369`, `:379`). It passes `--soak 10 --strict-text-bounds` against
  `dist/smoke/replay.json`, the artifact `docker-smoke` produced.
- Run `33035395418` log, line 3509:
  `{"loaded":true,"ms":337,"clock":"BREAKTHROUGH 6×6 · PLY 11 / 80 · GIZMO TO MOVE",…}`;
  line 3511 shows three differing scrub readouts (PLY 11 / PLY 23 / PLY 44 FINAL);
  line 3512 `canvas text: 5600 drawn, 0 never inside the canvas (0 draws crossed an edge),
  0 ellipsized`. `never_inside == 0`, so item 15's gated number is clean on the bundle path.
- MODULARIZE / EXPORT_NAME pairing: `replay-viewer/config.nims:37-38`
  `-s MODULARIZE=1 -s EXPORT_NAME=GauntletReplayModule`, and the bootstrap calls the factory:
  `replay-viewer/static_replay.js:140` `modulePromise = GauntletReplayModule().catch(...)`.
  No `onRuntimeInitialized` anywhere in the tree. Both files are `diff`-verified forks of
  babel's (only `babel`→`gauntlet` / `bab_`→`bg_` renames plus the `onFirstFrame` change).
  Exported functions in `config.nims:40` match the `exportc` names in
  `replay-viewer/gauntlet_replay.nim:22,67,73,76,82`.
- Both load markers set from the shell's own code:
  `data-replay-loaded="true"` at `client/renderer.js:848`, inside the rAF loop **after**
  `renderer.draw(...)` on line 843, and `tell("ready")` is posted from `onFirstFrame`
  (`:849` ← `static_replay.js:126`), which is the chorus fix the note names.
  `data-replay-error` set at `static_replay.js:56` and removed at `:107` and `:136`.
  `tools/build_replay_viewer.sh:65-66` greps for both before declaring the bundle built.

**Manifest** — Checklist items 6, 10, 12
- `num_agents: 2` in all five variants' `game_config`
  (`coworld_manifest_template.json:431, 454, 477, 500, 523`) and in
  `certification.game_config` (`:545`); no variant carries it at top level. Asserted by
  `tests/test_manifest.nim:28-49`.
- `docker_smoke.sh` is a byte-identical substitution of
  `coworld-builder/templates/tools/ci/docker_smoke.sh` (`diff` empty) and carries all four
  seat-count invariants plus the `SMOKE_SEATS` cross-check
  (`tools/ci/docker_smoke.sh:106-151`), each prefixed `SEAT-COUNT FAIL:`. **`grep -c
  "SEAT-COUNT" /tmp/ci.log` → `0`**; the smoke printed
  `smoke OK: seats=2 results=321B replay=6616B reason=complete` (log line 1946) and the
  fixture config it fed the container carries `"num_agents": 2` (log line 1940).
  Committed mode `100755` (`git ls-files -s`).
- `game.replay_viewer = {"bundle": "static-replay-viewer"}` **inside** `game` (`:18-20`).
  `tools/build_replay_viewer.sh` present, mode `100755`, and wired as the `coworld build`
  hook (it is the file `coworld build` requires `os.X_OK` on; `ci.yml:231-255` asserts and
  invokes it by path).
- `game.docs` is `{readme:{type,value}, pages:[{id,title,content:{type,value}}]}`
  (`:354-369`); `game.protocols` carries **both** `player` and `global` as `{type,value}`
  objects (`:344-353`). Asserted by `tests/test_manifest.nim:109-132`.
- Image placeholder is `{{BOARD_GAUNTLET_IMAGE}}` (`:25`, `:377`, `:397`), derived from the
  compose service name `board-gauntlet` (`compose.yaml:2`). No `{{GAME_IMAGE}}`.
- No top-level `version`, no `game.display_name`, no `game.tags`, 11 top-level `tags`,
  `episode_timeout_minutes: 20`, `game.name == "board-gauntlet"` and
  `ANTHROPIC_API_KEY_URI = "secret://coworld/board-gauntlet/anthropic_api_key"` (`:30`) —
  namespace equals `game.name`. All asserted at `tests/test_manifest.nim:134-155`.
- No `game_config` anywhere carries `tokens`; `config_schema.required` still lists it
  (`:38-41`); every array property in both schemas has `minItems: 2, maxItems: 2`
  (checked by `tests/test_manifest.nim:67-76`).
- The item-12 placeholder gate exits 0: I ran the exact grep from the checklist over
  `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`, `docker_smoke.sh`, `policies.json` —
  no match. The four expected residue names (`<cow_id>`/`<sha>` in `ci.yml:208`,
  `<run_id>` in `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` in
  `coworld-submit.yml:31`) are present as documented residue.
- `tools/ci/policies.json` has four policies: two `PLAYER_PROMPT` champions
  (`board-gauntlet-grandmaster`, `board-gauntlet-tempo`) and two `PLAYER_SCRIPTED` fillers;
  champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`:15`). The
  two prompt texts are verbatim `design.md:513-539`. Asserted by
  `tests/test_manifest.nim:204-230`.
- `coworld-release.yml` and `coworld-submit.yml` are byte-identical to the substituted
  templates (`diff` empty both ways); order is build (`:159`) → certify (`:173`) →
  upload-policies (`:212`) → upload-coworld (`:310`) → secret put (`:348`).

**Both name spaces** — Checklist item 4
- Agents see aliases only: `tableNames` draws from `CogNames` with a seeded shuffle
  (`sim.nim:35-46`, `types.nim:27-30`); `systemPrompt`/`userPrompt` use `sim.names[seat]`
  (`llm.nim:461`, `:486`); `welcome`/`state`/`final` frames all carry `sim.names[...]`
  (`server.nim:415`, `:109`, `:198-200`). I grepped the prompt builders and the player frames
  for `config.players[...].name` — no hit.
- The viewer maps aliases → policy names for non-baseline seats:
  `makeNameMap` (`chrome_common.js:93-121`, babel's byte-identical) with
  `isBaselineFiller` (`:89-91`); called with `payload.policyNames` at
  `client/renderer.js:778`. `results.names` carries **policy** names (`sim.nim:384`).

**Viewer legible at 360 px** — Checklist item 11
- `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` — `client/chrome.css:484-491`.
- `.plate-label { display: none; }` under `@media (max-width: 640px)` —
  `client/chrome.css:599-600`.

**Chrome provenance** — Checklist item 14 (other than B2)
- `head -443 client/chrome.css` is **byte-identical** to babel's 443-line `chrome.css`;
  everything else is appended under the named banner (`:445-450`).
- `client/replay_broadcast.html` is babel's `client/replay.html` with title / wordmark /
  `#clock` text changed, `chrome_common.js` added to the script list, `BabelRenderer` →
  `GauntletRenderer`, and one `<script>` block appended under the banner comment
  *"BOARD-GAUNTLET additions to the inherited cogame-babel chrome"* (`:74-90`). **Nothing is
  removed**: every id the checklist names (`#layout`, `#stage`, `#topband`, `#wordmark`,
  `#clock`, `#topright`, `#statuschip`, `#feedtoggle`, `#scorebug`, `#board-wrap`,
  `canvas#table`, `#lightpool`, `#grain`, `#endscreen`, `#transport`, `.scrub#scrub`,
  `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, the `/replay` bootstrap) survives.
  93 lines vs the starter's 74 — a superset, not a rewrite.
- Transport rules:
  (a) `relayout()` measures `#transport` and sets `--band` and `--hudscale` on
      `document.documentElement` (`chrome_common.js:416-426`); it is bound to `load`, to
      `resize` (`:522-524`), and reached on every feed toggle because `bindFeedToggle`
      dispatches a `resize` event (`:313`, `:324`). `:root { --band: 0px; --hudscale: 1 }`
      declares the fallbacks (`chrome.css:452-459`).
  (b) Nothing fixed-positioned sits in the band — `grep "position: *fixed"` over
      `client/*.css`, `client/*.html`, `client/*.js` returns nothing.
  (c) `#endscreen { top: 0; bottom: var(--band, 0px); }` (`chrome.css:582-585`); the class its
      CSS uses is `.show` (`chrome.css:381`, babel's) and `updateEndscreen` toggles exactly
      that (`chrome_common.js:244`). Every seek takes it down: `setIndex` unconditionally
      calls `C.updateEndscreen(…, index >= events.length && events.length > 0, …)`
      (`client/renderer.js:820-821`), and the scrub's `onSeek` and every beat button route
      through `setIndex` (`:789-792`, `chrome_common.js:483`).
  (d) Beats are labelled `<button type="button">`s that seek —
      `markPlyBeat` (`chrome_common.js:465-486`), `aria-label`/`title` from `beatLabel`
      (`:441-460`), `onclick → onSeek(index + 1)` (`:481-484`). CSS exists for every kind the
      builder can stamp: `.beat-start`, `.beat-move`, `.beat-win`, `.beat-end`,
      `.beat-move.capture`, `.beat-move.wall` (`chrome.css:571-576`) plus the `.seat0` /
      `.seat1` tints from babel's copied block; `tools/ci/chrome_scope_check.mjs:92-110`
      asserts the list and the job is green.
- Zoom bar / minimap correctly **absent**: `grep viewpanel|zoomAt|setZoom|attachMinimap` over
  `client/` and `replay-viewer/` returns nothing, matching `design.md:980-983` (the 9×9
  Quoridor board is drawn whole).

**Tests — the note's 29 items are all present**
`tests/test_sim.nim` carries 12 suites matching items 1–12; `tests/test_bot.nim` 5 suites
matching 13–17; `tests/test_replay.nim` 4 suites matching 18–21; `tests/test_manifest.nim`
4 suites matching 22–25 plus a `policies` suite; item 26 is `tools/ci/docker_smoke.sh`;
item 27 the `wasm-viewer` job's smoke step; item 28 the renderer-fixture step
(`ci.yml:345-366`); item 29 `tools/ci/chrome_scope_check.mjs` (`ci.yml:302-303`).
`NIM_TESTS` is unset in the repo, so `ci.yml:123-155` runs every `tests/*.nim` in **both**
debug and `-d:release` — the log shows each suite twice (e.g. lines 2375 and 2393 for the
same `no-moves` test). **No test was disabled, skipped or loosened during this run**:
`git log --oneline --stat -- tests/` shows one commit (`cee5659`) adding all four files, and
no later commit touches `tests/`; `grep -n "skip\|xfail"` over `tests/` returns nothing.

**Scripted baselines** — Checklist item 7 (first half)
- `tests/test_bot.nim:37-71` runs 200 seeded episodes × 4 games × 2 baselines and asserts
  every produced move is in `legalMoves`, is ≤ `MaxMoveLen`, and that `say`/`notes` stay
  empty; every episode terminates with `plies <= maxPlies`.
- `tests/test_bot.nim:259-279` runs the **cert fixture** (breakthrough-6, seed 23,
  `turnDelayMs = 0`) all-scripted to its natural end and asserts
  `sim.reason == "complete"` and `elapsed < 50.0`.
- `tests/test_bot.nim:76-98` asserts `tactician` beats a seeded uniform-random legal mover
  over 200 episodes (100 seeds × both sides) per game, mean score > 0.
- `docker-smoke` corroborates end-to-end: `reason=complete`, both player containers exit 0.

**Scoring against `design.md` §Scoring formula and sign**
`score* = +1 / 0 / −1` (`sim.nim:198-202`), `outcome = (score+1)/2` (`:204-205`), sum zero by
construction. `settle` implements the ending→winner table verbatim: `board-full` → −1
(draw), `ply-cap`/`wall-clock` → higher `standing`, ties → draw, `no-moves` → `1 - mover`,
everything else already named by the win check (`sim.nim:213-223`). `EvalScale = [40, 400,
200, 200]` (`sim.nim:22`) matches `design.md:226-227`; `evalBar` clamps to −1..1
(`:160-163`). All pinned by `tests/test_sim.nim:537-586`.

---

## Could not determine

- **Which widths B1's 7106 ellipsized draws come from.** `viewer_smoke.mjs` reports one
  aggregate per run and the fixture cycles 360 / 640 / 1280 px in one page
  (`renderer_fixture.html:302-305`). What would settle it: a per-width `--out` run, or a hand
  measurement of `ctx.measureText("Sprocket: “" + 80-rune say + "”")` at
  `font = 12px rajdhani` against `canvas.width - 20`. My arithmetic estimate (N18 caveat
  applies) suggests it fires at all three, but I did not confirm 1280 px.
- **Whether `complete/no-moves` is genuinely unreachable from the standard Breakthrough
  opening**, as `tests/test_replay.nim:270-275` claims. I did not construct a proof or a
  counter-example; the claim is plausible (a rank-2 piece always has a rank-1 target) but the
  general case with captures is not obviously closed. What would settle it: an exhaustive or
  long random sweep of `breakthrough` from `startBoard` recording every ending seen (the
  existing sweep at `tests/test_sim.nim:521-533` covers 2400 episodes but does not report the
  ending histogram).
- **Whether the hex 0–1 BFS deque can overrun its backing array.** `hex.nim:114` sizes it
  `2 * MaxCells + 2` with `head` starting at `MaxCells`. I reasoned that each cell can be
  front-pushed at most once (a later pop's `base` is never smaller, so no second strict
  improvement at cost 0) and back-pushed at most once, bounding `head ≥ 0` and `tail ≤ 242`
  — so it is safe. That is an **inference**, not a test; what would settle it is a bounds
  assertion or a debug-build fuzz over adversarial boards. Note the debug CI pass would have
  raised `IndexDefect` on any overrun across 300 seeded hex episodes × 2 baselines, and it
  did not.
- **Whether `renderFeed`'s DOM say line is also clipped at 360 px.** `.feed-say` has no
  explicit width rule in the game block and `#feed` is `display: none` under 360 px
  (`chrome.css:610`), so there is nothing to measure; `viewer_smoke.mjs` only instruments the
  canvas. What would settle it: a DOM `scrollWidth > clientWidth` probe in the fixture.
