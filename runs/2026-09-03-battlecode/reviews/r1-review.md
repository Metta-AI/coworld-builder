# r1 review — battlecode

Repo: `Metta-AI/cogame-battlecode` @ `3eb79159ad5164efae88c71397f47303dd28b20b` (green-CI main),
cloned to `/tmp/review-cogame-battlecode`.
Design note: `/workspace/coworld-builder/runs/2026-09-03-battlecode/design.md` (v2, Nim-port).
Starter: `/workspace/starters/coworld-ctf` (read-only).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Files read: 58 (every `src/**`, `replay-viewer/**`, `tests/**`, `tools/ci/**`, both chrome files,
`client/replay_broadcast.html` in full, all three workflows, the manifest, `docs/RULES.md`,
`docs/PARITY.md` headers) plus CI run 33818291222 job logs and the `viewer-smoke` artifact.

Labels used below: **observed** = I read the lines quoted; **inferred** = reasoned from what I read;
**untested** = would need a run to settle. Severity is a *guess*; the judge decides.

---

## Blocking

### B1 — `#endcard` is shown with class `show`; the CSS rule is `#endcard.on`, so the endcard never becomes visible
- Where: `client/replay_broadcast.html:2997` (add), `:2956` (remove), against `:1849` and `:1859`
- Observed:
  - `client/replay_broadcast.html:1837-1849` — the inherited rule is
    `#endcard { position: absolute; … top: var(--topband,0px); bottom: var(--band,0px); display: none; … }`
  - `client/replay_broadcast.html:1859` — `#endcard.on { display: flex; animation: ec-shake 160ms ease-out; }`
  - The appended game block's endcard code uses a *different* class:
    - `:2997` `$('endcard').classList.add('show');` (inside `renderEndcard`, `:2959-2998`)
    - `:2956` `$('endcard').classList.remove('show');` (inside `dismissEndcard`, `:2953-2957`)
  - I grepped every `.show` rule in the page (`:645, 792, 997, 1038, 1107, 1734, 1743, 1784, 2350`).
    There is no `#endcard.show` rule and no bare `.show` rule. The element therefore stays
    `display: none` for the whole replay.
  - The rest of the endcard wiring is correct and would work with `.on`: `renderEndcard` fills
    `#ec-headline`, `#ec-wincond`, `#ec-how`, `#ec-teams` (`:2965-2996`), and every seek path calls
    `dismissEndcard()` (`seek()` at `:2822-2825`, transport buttons at `:3030`, keyboard at `:3051`).
- Checklist item: 14(c) — "`#endcard` keeps `bottom: var(--band, 0px)`, **is shown with the class its
  CSS rule uses (`#endcard.on`)**, and every seek … takes it down".
- Why blocking: the score screen — winner alias + real name, the win condition in words, the per-game
  score line, the economic story, who betrayed whom — is drawn into the DOM and then never displayed.
  Nothing in CI catches it: `docker_smoke`'s replay never reaches `ph:'gameover'` inside the viewer
  smoke's 10 s soak (evidence: `viewer-smoke.json` `soak.after.tick = "round 244 / 400"`), and
  `tests/test_viewer.nim:159` only asserts the string `dismissEndcard` is present in the page.
- Severity guess: **blocking, category `static-viewer`**.

---

## Non-blocking

### N1 — the same `.show`/`.on` mismatch on `#mmwarn`: the hash-mismatch banner can never render
- Where: `client/replay_broadcast.html:3125`, against `:1806-1821`
- Observed: `:1806-1820` `#mmwarn { … display: none; … }`; `:1821` `#mmwarn.on { display: block; }`.
  The game block does `mm.classList.add('show')` at `:3125` when
  `data-replay-mismatch-round >= 0`. No `#mmwarn.show` rule exists.
- Note says: §Determinism — "the viewer re-derives each round and compares, exposing
  `bc_mismatch_round` exactly as ctf exposes `ctf_mismatch_tick`". The value *is* exposed on `<html>`
  (`replay-viewer/static_replay.js:29-34`); only the on-screen banner is dead.
- Severity guess: non-blocking (`correctness`/`legibility`); not named by any checklist item.

### N2 — `viewer_smoke.mjs`'s scrub gate clicks the zoom slider, not the scrubber, so no seek is exercised
- Where: `tools/ci/viewer_smoke.mjs:446` + `:582-587`, against `client/replay_broadcast.html:2673` and `:2725`
- Observed:
  - `tools/ci/viewer_smoke.mjs:446` — `const SCRUB_SELECTOR = '#scrub, #seek, input[type="range"]';`
  - `:583` — `await page.locator(SCRUB_SELECTOR).first().boundingBox();` then `page.mouse.click(...)`.
  - In this page the `#viewpanel` zoom slider is an `input type="range"` at
    `client/replay_broadcast.html:2673`, and `#scrub` is at `:2725`. A Playwright CSS selector list
    resolves in **document order**, so `.first()` is the zoom slider (inferred from Playwright's
    `querySelectorAll` semantics; observed from the line ordering).
  - The recorded evidence agrees: `viewer-smoke.json` (run 33818291222, `viewer-smoke` artifact)
    reports `scrub: [{0%, "0:07"}, {50%, "0:06"}, {100%, "0:05"}]` — a clock decreasing by ~1 s per
    700 ms sleep, i.e. free-running playback. A real 100 % seek would set
    `ended = deriver.frame >= totalFrames - 1` (`replay-viewer/bc_replay.nim:69`) → `ph:'gameover'`
    (`src/battlecode/broadcast.nim:180`) → `chrome_common.js:424-426` renders `FINAL`, not `0:05`.
- Note says: §Tests `wasm-viewer` — "requiring … three **differing** clock/scorebug readouts at
  0 % / 50 % / 100 %". The readouts differ, so the gate passes; it just does not test seeking.
- Consequence (inferred): the transport-seek path — including the `dismissEndcard()` in `seek()` that
  B1 breaks — has no CI coverage.
- Severity guess: non-blocking (`static-viewer` coverage gap). The design note keeps `#viewpanel`
  deliberately, so this is an interaction between a note-sanctioned decision and the template harness.

### N3 — the doctrine-budget timeout emits a second `doctrine_fallback` and overwrites the recorded cause
- Where: `src/battlecode/decide.nim:164-169` and `:220-231`
- Observed: when the monotonic budget is already spent at the top of an attempt,
  ```
  164  if getMonoTime() - started >= budget:
  165    for slot in open:
  166      result.fallback[slot] = "timeout"
  167      result.events.add(ev("doctrine_fallback", … "cause": "timeout"))
  169    break
  ```
  `open` is **not** cleared before the `break`, so the tail loop at `:220` runs over the same slots:
  ```
  220  for slot in open:
  222    let cause = if client.disabled or client.transport == ltNone: "no_credentials"
  224                elif client.throttled: "throttled"
  225                else: "parse"
  226    result.fallback[slot] = cause
  227    result.events.add(ev("doctrine_fallback", … "cause": cause))
  ```
  A budget timeout therefore records **two** `doctrine_fallback` events for one seat and the surviving
  `results`/replay cause is `"parse"`, not `"timeout"`. (The `client.throttled` break at `:213-218`
  and the no-credentials path at `:155-159` do not have this problem — the latter never adds the slot
  to `open`.)
- Note says: §Degrade-never-hang — "a `doctrine_fallback` event **names the cause**"; §Event
  vocabulary — `doctrine_fallback` carries `slot`, `cause`.
- Note: this does **not** break the fallback itself. `result.sheets[slot]` is set to
  `baselineSheet(...)` at `:221` and `results.fallbacks[slot]` is 1 either way
  (`src/battlecode/results.nim:72`), so checklist item 8's "fallback is recorded" holds.
- Severity guess: non-blocking, `correctness`.

### N4 — `plan.abandon_after` is written and parsed but never read by the deriver; a real `deadline` replay drops the abandoned game entirely
- Where: `src/battlecode/match.nim:126-132`, `src/battlecode/server.nim:306-309`,
  `src/battlecode/replay.nim:105-110`, `:195`, `:207-241`
- Observed, step by step:
  1. `match.nim:128` records the stop: `plan.abandonAfter[g] = outcome.roundsPlayed`, then `:130`
     emits `game_abandoned`, then `:132` `break` — **before** `outcomes.add(outcome)` at `:133`.
     The abandoned game is therefore not in the returned `outcomes`.
  2. `server.nim:306-309` builds `doc.games` only from those returned outcomes, so the abandoned
     game has **no `GameHeader`** in the replay.
  3. `replay.nim:105-110` writes `plan.abandon_after` into the document and `:195` parses it back.
  4. `newDeriver` (`:207-216`) builds its frame list purely from `doc.games[].rounds`;
     `advance` (`:224-241`) and `seek` (`:243-251`) never reference `abandonAfter`. Grep confirms
     `abandonAfter` has no other reader in `src/` or `replay-viewer/`.
- Note says: §Determinism — "Any wall-clock-driven fact (the `deadline` stop) is recorded as **one
  load-bearing record applied by the same proc on record and on playback**".
- What the code actually does is self-consistent (the abandoned game is discarded on both sides, and
  `scoresFor` scores only finished games — `match.nim:147-161`), so I found no re-derivation
  divergence. The divergence is that `abandon_after` is dead data, not a load-bearing record.
- The `deadline` block in `tests/test_determinism.nim:111-139` hand-builds a document with a
  `GameHeader` for the abandoned game (`:129-131`) — a shape the recorder never writes — and then
  asserts `totalFrames == 200`, which is driven by `GameHeader.rounds`, not by `abandon_after`.
- Severity guess: non-blocking, `correctness`. Checklist item 2 is still satisfied (see T3).

### N5 — the hash chain is compared once per game (at its last round), not per round
- Where: `src/battlecode/replay.nim:236-240`, `src/battlecode/years/bc26/world.nim:590-594`, `:1531-1538`
- Observed:
  ```
  236  if d.roundInGame == d.doc.games[wantGame].rounds:
  237    let recorded = d.doc.games[wantGame].hashChain
  238    if recorded.len > 0 and toHex(d.world.hashChain) != recorded and d.mismatchRound < 0:
  240      d.mismatchRound = d.roundInGame
  ```
  Only the final chain value of each game is stored (`replay.nim:88` writes one
  `hash_chain_sha256` per game), so `bc_mismatch_round` reports the game's **last** round, never the
  first divergent one. `tests/test_replay.nim:96-101` corroborates: it corrupts the chain and only
  asserts `mismatchRound > 0`.
- Also observed: `processEndOfRound` (`world.nim:1533-1537`) folds four stats per team —
  `cheeseTransferred`, `damageToCats`, `numRatKings + 10*globalCheese`, `numBabyRats`. The note's
  step 7 lists **seven**: "cheese transferred, cat damage, the packed `kings + 10 × teamCheese` stat,
  baby rats, **dirt, rat traps, cat traps**". A re-derivation that diverged only in dirt or trap
  counts would not be detected by the chain (inferred).
- Note says: §Determinism — "the viewer re-derives **each round** and compares".
- Severity guess: non-blocking, `correctness`. Item 2's substance (the display comes from the
  re-derivation, and a test asserts the re-derivation reproduces the recording) holds — see T3.

### N6 — `test_knob_sensitivity.nim`'s seed loop is inert: each pair plays 3 distinct games, counted twice
- Where: `tests/test_knob_sensitivity.nim:31`, `:42-53`
- Observed:
  ```
  31  Seeds = [1, 2]
  42  for mapName in Maps:
  43    for seed in Seeds:
  44      let (w, o) = playGame(loadMap(mapName), sheets, 0, 0, Rounds, 0)
  ```
  `seed` is never passed to `playGame` (whose parameters are
  `spec, sheets, index, sideAslot, maxRounds, budgetSeconds` — `src/battlecode/years/bc26/rules.nim:140-142`)
  and the world RNG is seeded from `spec.randomSeed` (`world.nim:1558-1559`). The two iterations play
  the byte-identical game, so every total is exactly doubled and there are 3 independent samples,
  not 6.
  - Consequence for the `chassis` gate at `:122-124`: `games = Maps.len * Seeds.len = 6` and the
    assertion is `t.wins[1] >= 4`; with each game counted twice this is really "awu wins ≥ 2 of the
    3 distinct games".
- Note says: §Tests item 10 — "play a paired set of seeded games (identical seed, map and opponent
  … **3 seeds each**)".
- Declared deviations that I confirmed and am *not* filing as defects: the `cat_trap_budget` gate is
  `+12` not `+20` (`:87`, documented in the shard's own table at `:17`), and the `chassis` gate is
  "≥ 4 of 6" plus three dominance checks rather than "5 of 6" (`:117-130`, table row `:22`).
- Severity guess: non-blocking, `correctness` (test strength).

### N7 — `backstab_policy` values `never` and `retaliate_only` are behaviourally identical
- Where: `src/battlecode/years/bc26/chassis/kit.nim:74-96`
- Observed:
  ```
  76  if not w.isCooperation:
  80    return true                      # every doctrine fights back once flipped
  82  case clan.doctrine.backstabPolicy
  83  of bpNever, bpRetaliateOnly:
  84    false
  ```
  Both arms return `false` while the alliance holds and `true` after it breaks, so no observable
  behaviour distinguishes them. `sheet.plainWords` (`src/battlecode/sheet.nim:330-331`) still prints
  two different strings.
- Note says: §The doctrine sheet lists five distinct `backstab_policy` values; §Tests item 10
  deliberately exempts `backstab_policy` from the knob-teeth gate, so nothing tests this.
- Also observed and not in the note: `bpWhenAhead` carries an extra `w.currentRound >= 200` floor
  (`kit.nim:94`), and `traps.nim:38` gates rat-trap laying on `clan.hostilitiesOpen(w)`, so the
  default `retaliate_only` doctrine lays zero rat traps while cooperating — the note's knob table
  (`rat_trap_budget` → "same for rat traps") describes no such gate.
- Severity guess: non-blocking, `correctness`.

### N8 — the renderer fixture duplicates the page's CSS rather than loading it, and adds three properties the page does not ship
- Where: `tools/ci/renderer_fixture.html:31-62` vs `client/replay_broadcast.html:2560-2621`;
  driven by `.github/workflows/ci.yml:529-555`
- Observed — the fixture's own comment at `:31` says "The same rules the appended game block ships",
  but three declarations exist only in the fixture:
  | rule | fixture | page |
  |---|---|---|
  | `#scorebug .plate` | `max-width: 46%; overflow: hidden` (`:33-34`) | `display:flex; align-items:center; gap:6px` only (`:2560`) |
  | `#scorebug .plate-sub` | `white-space: nowrap; overflow: hidden; text-overflow: ellipsis` (`:36-38`) | `opacity:.72; font-size:11px` only (`:2562`) |
  | `#doctrines` | `overflow: hidden` (`:44`) | no overflow property (`:2600-2604`) |
  The fixture's verdict (`overflows()`, `:143-154`) compares element bounding boxes against `#frame`;
  with `overflow:hidden` and ellipsis on the elements under test, a box cannot report overflow.
  (Inferred: the fixture's green result does not transfer to the real page.)
  The page *does* have the checklist-11 rules — `:2561` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`
  and `:2617-2621` `@media (max-width:640px){ … #scorebug .plate-sub { display:none } }` — so the
  ≥640 px case is the only one that differs.
- Also observed: ci.yml drives the fixture with an inline Playwright script (`:533-555`), **not**
  `node tools/ci/viewer_smoke.mjs … --strict-text-bounds`. It does not produce a `canvas_text` line.
- Note says: §Tests `wasm-viewer` — "a separate step runs `tools/ci/renderer_fixture.html` … **through
  the same harness**". Checklist 15's last bullet asks for a fixture "that loads the real
  `client/renderer.js` … and is driven by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml`
  step".
- Countervailing observation (why I am not calling this blocking myself): this viewer draws **no**
  model text on the canvas. `src/battlecode/render.nim:170-257` emits only terrain/dirt/cheese/trap/
  robot sprites plus one 1×1 chrome sprite whose *label* carries the JSON, which
  `client/broadcast_core.js` routes to `onText` and never draws (`render.nim:26-29, 255-257`). All
  `notes`/`motto` text lands in DOM nodes (`#doctrines`, `.plate-sub`). `viewer-smoke.json` confirms
  `canvas_text: {total: 0, …}`. The cogchemists failure mode (canvas text at a negative coordinate)
  is therefore not reachable here.
- Severity guess: non-blocking `legibility` on my reading; I flag that a judge reading checklist 15's
  fixture bullet literally could call it blocking. Both readings are stated so the judge can pick.

### N9 — the design note's round-loop steps 4/5/6 and the code's steps 4/5/6 differ (and `docs/RULES.md` documents the code's order, not the note's)
- Where: `src/battlecode/years/bc26/rules.nim:66-100`, `src/battlecode/years/bc26/world.nim:1477-1520`,
  `docs/RULES.md:12-30`
- Observed:
  - Note step 4 puts "king cheese consumption and starvation damage" in *beginning of turn*.
    `world.nim:processBeginningOfTurn` (`:1477-1520`) does message reset, cheese mines, carried-rat
    bookkeeping, throw travel, cooldown decay and the ops budget — **no king consumption**.
  - Note step 5 says "for a cat, the ported cat state machine". `rules.nim:58-64` `runControllerFor`
    returns immediately for `utCat` (`:59`).
  - `rules.nim:66-81` `endOfTurnFor` (the note's step 6, "apply the actions the controller committed,
    resolve deaths, emit this turn's replay actions") instead does king consumption/starvation
    (`:70-75`) and then `runCatTurn` (`:77-79`). There is no commit/apply phase: chassis actions
    mutate the world immediately, and deaths resolve inside `addHealth`/`destroyRobot`
    (`world.nim:741-747`).
  - Note step 8 puts the end-of-match check at end of round. `world.nim:792-795` calls `checkWin()`
    **inside `destroyRobot`** for the zero-kings and all-cats-dead cases; `processEndOfRound`
    (`:1531-1541`) only runs the round-limit ladder via `checkEndOfMatch` (`:1524-1529`) and then
    stops the world.
  - `docs/RULES.md:24-27` states the code's order ("6. *End of turn*: king cheese consumption and
    starvation damage, then the cat state machine"), i.e. the repo documents the divergence but the
    note was not updated.
- Note says: §Round loop — "a re-ordering is a rules change and bumps `GameVersion`".
- I have no evidence either order is *wrong* against the Java engine (`InternalRobot.processEndOfTurn`
  is where the engine runs both); I am reporting only the divergence from the authoritative note.
- Severity guess: non-blocking, `correctness`/documentation.

### N10 — the LLM prompt payload is not recorded in the replay, and its shape differs from the note's
- Where: `src/battlecode/decide.nim:91-133`, `src/battlecode/replay.nim:51-72`
- Observed:
  - `briefFor` emits `protocol, game_version, year, slot, alias, opponent_alias, team, seed, games[],
    scoring, budget`. The note's §The doctrine exchange payload also carries `rules_digest` and
    `sheet_schema`; the code carries their content in the shared `SystemPreamble`
    (`decide.nim:36-89`) instead, so the *recorded per-seat observation* has no such keys.
  - `seatJson` (`replay.nim:51-72`) writes `slot, alias, name, policy, sheet, sheet_submitted,
    sheet_defaults_applied, sheet_unknown_fields, notes, motto, decision_ms, fallback`. There is no
    `prompt`/`brief` field anywhere in `ReplayDoc.toJson` (`:74-113`).
- Note says: §The doctrine exchange — "the 'observation' is the prompt payload the server composes
  per seat and **records verbatim in the replay**".
- Related, same section: the note's cap table lists "provider error text stored in the replay — 200
  runes". `MaxFallbackDetailRunes` (200) is applied to log lines (`decide.nim:209`) and to raised
  `LlmError` messages (`llm.nim:169, 177, 183`), but the only thing that reaches the replay is the
  one-word cause in `seat.fallback` (`replay.nim:69-72`). No provider text is stored.
- Severity guess: non-blocking, `correctness`. Checklist 9's requirement (every string that reaches
  the replay is rune-truncated, with a test) is satisfied — see T7.

### N11 — `NOTICE` does not exist, and `README.md` links to it
- Where: `README.md:77`, repo root
- Observed: `README.md:73-77` — "The rule set, the constants, the maps and the sprite art derive from
  `battlecode/battlecode26` … and `awu7/battlecode-2026` … See [`NOTICE`](NOTICE)." `ls NOTICE` →
  no such file. `LICENSE` is AGPL-3.0 as the note requires.
- Note says: §Packaging §Licensing — "`NOTICE` credits `battlecode/battlecode26` … and
  `awu7/battlecode-2026` …, naming the pinned commits"; §Viewer §Art — "Credited in `NOTICE`".
- Severity guess: non-blocking, `other`. (Both upstreams *are* credited, in `README.md:73-78` and
  `docs/RULES.md`, and the code files carry attribution headers — e.g.
  `src/battlecode/years/bc26/chassis/awu.nim:1-4`.)

### N12 — `#btn-skip` was not relabelled; `#btn-fwd` was
- Where: `client/replay_broadcast.html:3036-3038`, `:2714`, `:2717`
- Observed: `:3036-3037` `$('btn-fwd').textContent = '+25'; $('btn-fwd').title = 'Forward 25 rounds (.)';`
  `:3038` only re-titles `#btn-skip` ("Auto-skip quiet stretches (f)"); its label stays `▸▸`
  (markup `:2717`). The `.` command does map to +25 rounds
  (`src/battlecode/broadcast.nim:51`, `replay-viewer/bc_replay.nim:113-115`).
- Note says: §Transport rules — "`#btn-skip` (relabelled **+25 rounds**)".
- Severity guess: non-blocking, cosmetic. The note names the wrong button for this lineage
  (`#btn-fwd` is ctf's "+5s"); the behaviour the note wants exists.

### N13 — three test-suite items the note specifies are not present as written
- Where: `tests/test_manifest.nim` (whole file), `tests/test_determinism.nim:74-115`,
  `.github/workflows/ci.yml:124-170`
- Observed:
  - a. The note's shard 12 asks test_manifest to assert "the installed `coworld` CLI's own
    `validate_upload_manifest`/`_load_template_manifest` accepts the template". No such call exists
    (`grep validate_upload_manifest tests/` → nothing), and the `test` job installs no `coworld` CLI.
    (`coworld build` + `coworld certify` do run in `coworld-release.yml:159-215`.)
  - b. The note's shard 8 asks for "record → re-derive for **every** end reason". The shard has four
    blocks: `round_limit` (`:75-84`) and `kings_destroyed` (`:86-95`) both re-derive but assert only
    `r.reason == epComplete`, never the per-game `endReason`; `cats_cleared` (`:97-109`) is a
    world-level check with **no** record→re-derive; the `deadline` block (`:111-139`) re-derives a
    hand-built document (see N4). `var seenReasons: seq[EndReason]` at `:74` is declared and never
    used.
  - c. `tests/test_manifest.nim:238-241`'s "no JVM anywhere in the image" check is
    `banned notin dockerfile… or "no jdk" in dockerfile.toLowerAscii()`. `Dockerfile:7` contains
    "NO JDK, NO JRE, NO JAVA, NO NODE", so the right-hand disjunct is always true and the check
    passes vacuously for every banned word. (I read the whole `Dockerfile`; it is in fact clean —
    no java/jdk/jre/node install.)
  - d. `tests/test_viewer.nim:154-155` asserts "the endcard stops at the transport band" via
    `"bottom: calc(var(--band" in page`. The only `calc(var(--band` occurrences are `#econ` (`:2585`)
    and `#doctrines` (`:2601`); the endcard's own rule is `bottom: var(--band, 0px)` (`:1848`,
    inherited, and correct). The assertion passes for an unrelated reason.
- Note says: §Tests, shards 8 and 12.
- Severity guess: non-blocking, test strength. Checklist item 1's "no test loosened" is unaffected —
  see T1.

### N14 — `parseReply` caps the reply in runes where the note's cap is bytes
- Where: `src/battlecode/sheet.nim:306-308`, `src/battlecode/sim_types.nim:44`, `:107-114`
- Observed: `MaxReplyBytes* = 16 * 1024`; `parseReply` does
  `if text.len > MaxReplyBytes: text.truncateRunes(MaxReplyBytes)`, and `truncateRunes(text, limit)`
  counts **runes** (`sim_types.nim:112-114`). A 16 KB-byte reply of astral-plane text is therefore cut
  at 16384 runes ≈ 64 KB, not 16 KB.
- Note says: reply-schema cap table — "whole reply | 16 KB".
- The truncation is still on a rune boundary, so nothing unsafe results.
- Severity guess: non-blocking, cosmetic.

### N15 — the `#killfeed` spoiler gate in the game block is dead code, and the game block's beat buttons are outside `chrome_common`'s spoiler layer
- Where: `client/replay_broadcast.html:2935-2949`, `:2801-2820`; `client/chrome_common.js:506-514`
- Observed:
  - `:2940` `if (feedShown[key] || b.t > s.t) return;` already excludes future beats, so `:2941`
    `if (!C.getSpoilers() && b.t > s.t) return;` can never fire. Net effect: feed lines are always
    spoiler-safe (never revealed early) — the *conservative* direction.
  - `buildBeatButtons` (`:2801-2820`) appends its buttons directly to `#scrub`; it does not go
    through `chrome_common.markBeat`/`renderBeatMarkers`, so `applySpoilers`
    (`chrome_common.js:506-514`, which iterates `markerEls`) never hides them. With spoilers off, the
    markers for a future BACKSTAB are visible from frame 0.
  - `C.renderTransport` calls `renderBeatMarkers` (`chrome_common.js:491`) but `pendingMarkers` is
    always empty, so the game block's buttons are not wiped each frame; `resetEpisode` (which would
    sweep `.beat-marker`) is never called. Traced and correct on that axis.
- Note says: §Transport rules — beats "placed through `chrome_common.js`'s marker layer"; §Readouts —
  `#killfeed` "revealed as the playhead reaches them (spoiler gate honoured)".
- Severity guess: non-blocking, `correctness`.

### N16 — the `scaffold` baseline is examplefuncsplayer verbatim, not what the note's §Scripted baselines describes
- Where: `src/battlecode/years/bc26/chassis/scaffold.nim:26-33`
- Observed: the whole bot is `if canMove(dir) move(dir) else turn(Directions[rng.nextInt(8)])`. No
  bite, no cheese pickup.
- Note says: §Scripted baselines — "`scaffold` … the ported examplefuncsplayer behaviour: **random
  legal move, bite whatever is adjacent, pick up cheese underfoot**, no traps, no dirt, no
  formations."
- This is the builder's declared deviation and it is load-bearing for the parity oracle (the file's
  own header at `:8-12` says so, and `docs/PARITY.md` depends on it). Recording it because the note
  is authoritative.
- Severity guess: non-blocking, declared.

---

## Traced and consistent

- **T1 — CI green, no test loosened (checklist 1).** `gh run list -R Metta-AI/cogame-battlecode
  --branch main -w ci.yml`: run **33818291222**, conclusion **success**, head commit
  `3eb7915` = the reviewed sha. Jobs: `test` ✓ 2m52s, `docker-smoke` ✓ 1m27s, `parity-oracle` ✓ 33s,
  `wasm-viewer` ✓ 2m50s. `git log -p -- tests/` across the three post-scaffold commits
  (`80ef66e`, `f28cf84`, `acd7aed`) shows **only additions and mechanical relocations**: `80ef66e`
  moves `game["variants"]` → `manifest["variants"]` and `p["runnable"]["run"]` → `p["run"]` to match
  the manifest reshape and *adds* three assertions; `f28cf84` adds 13 lines; `acd7aed` adds 12 lines
  (the export-name cross-check). No deleted assertion, no widened tolerance, no `skip`, no removed
  test file.
- **T2 — one parallel batch for both seats (checklist "additionally").** `src/battlecode/decide.nim:172-185`:
  a single `RequestBatch` is filled for every `slot in open` (`:173-180`) and issued with one
  `client.curl.makeRequests(batch, max(1, deadlineMs div 1000))` (`:185`). No per-seat call site
  exists. Tolerant parse: `sheet.extractJsonObject` (`sheet.nim:130-166`) walks balanced braces with
  string/escape tracking and falls back to first-brace..last-brace; fence tolerance is covered by
  `tests/test_sheet.nim:132-140`. Exactly one retry: `while open.len > 0 and attempt < 2`
  (`decide.nim:162`). Scripted fallback recorded: `results.nim:72`
  `fallbacks.add(%(if seats[slot].fallback.len > 0: 1 else: 0))`.
- **T3 — replay re-derivation (checklist 2).** The viewer's display is derived, not recorded:
  `replay-viewer/bc_replay.nim:64-72` `renderCurrent` builds every packet from `deriver.world` after
  `deriver.advance()` (`replay.nim:224-241`) re-runs `runRound(d.world, d.clans)` with the sim's own
  code. The recorded event list is used only for scrubber beats
  (`src/battlecode/broadcast.nim:113-155`) — never for board state. `tests/test_replay.nim:83-93`
  asserts `deriver.mismatchRound == -1` and that the re-derived `cheeseTransferred` equals the
  recorded outcome; `:95-101` asserts a corrupted chain is detected; `tests/test_determinism.nim:149-174`
  asserts the re-derived chain equals the recorded one across a serialise/parse round trip and twice
  from the same bytes.
- **T4 — static viewer (checklist 3).** `coworld_manifest_template.json` →
  `game.replay_viewer = {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` exists,
  is `0755`, does the containment checks + `docker build --target replay-viewer-builder` +
  `docker create` + `docker cp`, and is asserted present-and-executable at `ci.yml:421-432`. The
  worker fetches only `message.replayUrl` (`static_replay_worker.js:127-130`, `credentials:'omit'`);
  no other network call exists in the bundle. `server.nim:328-336` registers `/healthz`, `/health`,
  `/global`, `/client/global`, `/client/player`, `/player` — there is **no** `/client/replay` route,
  and `/client/*` returns a static "no live viewer pod" page (`:111-118`).
- **T5 — both name spaces (checklist 4).** `decide.briefFor` (`decide.nim:111-133`) sends
  `alias`/`opponent_alias` only — no `names` key anywhere in the payload, and no opponent sheet.
  `aliasFor` (`sim_types.nim:121-122`) returns `Clan Ash`/`Clan Basil`. Real names appear only in
  `results` (`results.nim:79`), the replay (`replay.nim:102`) and the chrome document
  (`broadcast.nim:208` `"names": [doc.names[0], doc.names[1]]`), and are drawn by the viewer at
  `client/replay_broadcast.html:2850` and `:2966`. `tests/test_replay.nim:148-150` asserts both.
- **T6 — every wait and its bound (checklist 5).** Enumerated:
  | wait | bound | site |
  |---|---|---|
  | seat connect | `connectTimeoutMs` (25 000; cert 15 000), monotonic deadline + `sleep(100)` poll | `server.nim:156-169` |
  | doctrine phase | `doctrineBudgetMs` (45 000) checked at each attempt | `decide.nim:142`, `:164` |
  | attempt 1 / retry | `attempt1Ms` 20 000 / `retryMs` 12 000 → `CURLOPT_TIMEOUT` seconds | `decide.nim:170-171`, `:185` |
  | per game | `perGameBudgetSeconds` 90, monotonic, sampled every 32 rounds | `rules.nim:153-162` |
  | match | `matchBudgetSeconds` 330, checked before each game; per-game budget clamped to the remainder | `match.nim:104-115` |
  | shutdown grace | `BATTLECODE_SHUTDOWN_GRACE_MS` default 20 000 | `server.nim:350-352` |
  | player dial | 240 × 500 ms + ≤ 6 re-dials | `battlecode_player.nim:25-29`, `:80-91` |
  Arithmetic: 25 + 45 + 330 + (write + 20 s grace) ≈ **420–435 s ≤ 720 s** — matches the note's
  §Match shape table. No unbounded loop: every `while` I read has a monotonic or counted exit
  (`decide.nim:162`, `match.nim:107`, `rules.nim:155`, `server.nim:162`, `replay.nim:250`).
  `playMatch` clamps the last game with `perGame = max(1, min(perGameBudgetSeconds, remaining))`
  (`match.nim:114-115`), so the match cannot overrun its own guard. Untested at runtime by me.
- **T7 — rune-safe truncation (checklist 9).** `truncateRunes` (`sim_types.nim:107-114`) is the
  single cut, via `runeLen`/`runeSubStr`. Call sites: `notes`/`motto` through `sanitizeLine`
  (`sheet.nim:299-300`), unknown sheet keys (`sheet.nim:194`, cap 40 runes, ≤ 16 keys via
  `MaxUnknownFields`), the operator prompt (`llm.nim:204`, 4000 runes), every provider error body
  (`llm.nim:169, 177, 183, 195`) and the retry log line (`decide.nim:209`). Tests:
  `tests/test_sheet.nim:156-174` feeds 400 × U+1F400 and asserts `runeLen == 280`, `notes.len == 280*4`
  and `validateUtf8() < 0`; `tests/test_replay.nim:63-80` asserts the **written replay bytes** parse
  as strict UTF-8 (`text.validateUtf8() == -1`) with astral text at the cap.
- **T8 — `num_agents` (checklist 6).** `coworld_manifest_template.json`: the single `bc26` variant has
  `game_config.num_agents = 2` and **no** variant-level `num_agents`; `certification.game_config`
  has `num_agents: 2`, `players` of length 2, and `certification.players` seats both declared player
  entries (`awu`, `scaffold`). `tools/ci/docker_smoke.sh:110-151` enforces all four invariants plus
  the `SMOKE_SEATS` cross-check, every failure prefixed `SEAT-COUNT FAIL:`. `SMOKE_SLUG`/`SMOKE_SEATS`
  are passed from `ci.yml:32-33, 379-381`. I grepped the `docker-smoke` job log of run 33818291222
  for `SEAT-COUNT FAIL` — **no occurrence**; the job is green in 1m27s.
  `server.parseConfig:221-223` additionally rejects any `num_agents != 2` with `ConfigError` (exit 2).
- **T9 — scripted baseline plays full episodes legally (checklist 7).** `docker_smoke.sh:323-329`
  asserts `results.reason == "complete"` and `fallbacks == [0,0]` on an all-scripted episode with no
  `ANTHROPIC_API_KEY` (`:194-199`), and the job is green. `tests/test_determinism.nim:82-84` asserts
  `epComplete` for a scripted match. `tests/test_baselines.nim:44-91` walks three maps × 400 rounds
  and asserts no robot leaves the map / stands in a wall or dirt / holds a negative cooldown, no
  team goes into cheese debt or over the trap/king caps. Both baselines go through the same
  `sheet.validate()` as the LLM path (`baselines.nim:36` `parseReply(baselineReply(kind))`), which is
  what `tests/test_baselines.nim:13-31` checks. The knob thresholds are tuned from a measured table
  (`tests/test_knob_sensitivity.nim:13-22`) rather than guessed — see N6 for its sampling.
- **T10 — manifest validates (checklist 10).** `game.docs.readme` and each of the three
  `pages[].content` are `{type,value}` objects; `game.protocols` carries both `player` and `global`
  as `{type,value}` objects. `game.config_schema` is `additionalProperties: false`, has no `tokens`
  property, and its only array (`players`) carries `minItems: 2`/`maxItems: 2`;
  `tests/test_manifest.nim:100-116` walks both schemas and requires every `"type":"array"` node to
  carry both bounds. `results_schema.required` == `results.nim:97-101 ResultsKeys` ==
  `docker_smoke.sh:312-316 CLOSED_KEYS` (I diffed all three by hand: identical 16-key sets);
  `results_schema.properties.reason.enum == ["complete","deadline","fault"] == EpisodeReasons`;
  `results_schema.properties.games.items.required == GameKeys` (16 keys, identical). Top-level
  `tags` has 4 entries and there is no `game.tags`. `episode_timeout_minutes: 20`.
- **T11 — 360 px legibility (checklist 11).** `client/replay_broadcast.html:2561`
  `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }` — byte-exact against the checklist
  string, and `tests/test_viewer.nim:156-157` pins that exact literal. `:2617-2621`
  `@media (max-width: 640px) { #econ, #doctrines { font-size: 9px; } #scorebug .plate-sub { display: none; } #bars .barset { min-width: 44px; } }`.
  The inherited scorebug grid already uses `minmax(0,1fr)` tracks (`:163`) and `.plate { min-width: 0 }`
  (`:197`), so the plates can shrink.
- **T12 — release order and scaffold (checklist 12).** `coworld-release.yml` step order:
  "Build the Coworld manifest" (`:159`) → "Certify locally" (`:173`) → "Upload the policies"
  (`:216`, with the comment "BEFORE upload-coworld") → "Upload the Coworld" (`:314`) → "Put the
  Coworld secret" (`:410`). All three workflows present. `tools/ci/docker_smoke.sh` is `0755`.
  `tools/ci/policies.json` has exactly four entries: two `PLAYER_PROMPT` champions
  (`battlecode-loyalist`, `battlecode-opportunist`) and two `PLAYER_SCRIPTED` fillers
  (`battlecode-awu`, `battlecode-scaffold`); champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The placeholder gate
  `grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/{ci,coworld-release,coworld-submit}.yml
  tools/ci/docker_smoke.sh tools/ci/policies.json` returns **no matches** (exit 1), so the gate
  exits 0. `coworld-submit.yml` inputs: `player_id` (required string, description naming both
  `ply_…` ids), `policy` (`<name>:vN`), `league_id` — all three required, concurrency group
  `coworld-submit`, `cancel-in-progress: false`.
- **T13 — viewer executes (checklist 13).** `wasm-viewer` `needs: docker-smoke` (`ci.yml:408`); the
  step "Load the bundle in a real browser" (`:489-515`) runs `node tools/ci/viewer_smoke.mjs --bundle
  dist/static-replay-viewer --replay dist/smoke/replay.json --timeout 90 --soak 10` with **no**
  `continue-on-error`, and the job is green in run 33818291222. Downloaded `viewer-smoke.json`:
  `loaded: true`, `ms: 286`, `signals.data_replay_loaded: "true"`, `signals.data_replay_error: null`,
  `signals.bridge_ready: true`, `soak.moved: true` (round 4 → 244 of 400), `soak.page_errors: []`,
  three differing `scrub` clock readouts (see N2 for what those readouts actually measure).
  Markers: `replay-viewer/static_replay.js:180` sets `data-replay-loaded` on the worker's `loaded`
  message, which the worker posts only after `ingestPacket()` of the first board frame
  (`static_replay_worker.js:141-150`); `:19-20` sets `data-replay-error="<message>"` on `<html>` for
  every failure path (fetch, empty body, load failure, worker `onerror`, `onmessageerror`, abort).
  The `coworld-replay` bridge posts `ready` only after that attribute is observed
  (`client/replay_broadcast.html:3151-3164`). **No recorded lobby**: `chromeJson` emits `"st": 0`
  (`broadcast.nim:183`) and frame 0 is round 1 of game 0 (`replay.nim:209-213`); doctrine events
  carry `ms`, not `game`/`round`, and `beatsFor` skips them (`broadcast.nim:118`), so there are no
  frozen pre-game frames to dwell through.
- **T14 — link flags vs bootstrap are the same starter's pairing (checklist 13, last bullet).**
  `replay-viewer/config.nims:42-54` has **no** `MODULARIZE` and **no** `EXPORT_NAME`; it is ctf's
  file with only `ctf_* → bc_*` renames (`diff` against
  `/workspace/starters/coworld-ctf/replay-viewer/config.nims` shows exactly four hunks, all renames).
  `replay-viewer/static_replay_worker.js:8` `var Module = {};`, `:209-222`
  `Module.locateFile` / `Module.onAbort` / `Module.onRuntimeInitialized = function(){…start()}` /
  `self.Module = Module`, and `:274`
  `importScripts('./wire_constants.js', './broadcast_core.js', './bc_replay.js');` as the last line —
  the non-MODULARIZE global-`Module` bootstrap, matched to the flags.
  `tools/wasm_replay_smoke.cjs:33-38` uses the same shape and says so explicitly. `tests/test_viewer.nim:34-59`
  pins all of it, including a check that every `Module._bc_*` the worker calls appears in the export
  list. `ci.yml:519-520` runs the node wasm smoke, which asserts `loaded`, ≥ 50 frames, non-empty
  packets and `bc_mismatch_round < 0`.
- **T15 — chrome provenance (checklist 14, first two bullets).**
  `client/chrome_common.js` and `client/broadcast_core.js` are **byte-identical** to the starter's:
  sha256 `f7860b4c…5465` and `226aea03…b098b` on both sides (`diff` reports no differences), and
  `tests/test_viewer.nim:26-31` pins those exact hashes.
  `client/replay_broadcast.html` **is** the starter's page: `diff` of bc lines 1–2543 against ctf
  lines 1–2543 is **empty** — the whole CSS (sections 1–5: stage, scorebug, banner lane, kill feed,
  transport, scrubber + momentum + beat markers + lulls, endcard, locker-room curtain) is unmodified
  byte for byte. The only structural edits are (a) the banner-comment CSS block at `:2545-2621`, (b)
  the game markup block at `:2700-2705`, (c) the appended `<script>` at `:2758-3166`, and (d) the
  removals the note lists, verified individually: `#commsdock`/`#commsFeed`/`#commsLive` (gone),
  `#lockerroom`/`#lk-*` (gone), `#fpv*` (gone), `#voteStage`/`#voteNote`/`#voteGrid` (gone),
  `#huddleStage`/`#huddlePanel`/`#huddleFeed`/`#huddleChip`/`#huddleLines` (gone), `#gloryPops`
  (gone), `#lulls` and the `.momentum-label` span (gone), `#cell-*` (absent). `#viewpanel` is KEPT
  with all eight ids and `?viewpanel=0` still honoured (`:3099-3101`). The page is 3168 lines /
  153 KB against the starter's 7181 / 349 KB, and the whole difference is the ctf per-view script
  (starter lines 2731–7181) being replaced — the deviation the builder declared. `#momentum` is kept
  hidden (`:2555-2558`) with the reason written down; `chrome_common.renderMomentum` writes to it
  unconditionally (`chrome_common.js:695-696`), and `renderLullSpans` guards on `!lullSpans`
  (`:536`) and `chromeJson` never emits `lulls`, so the removed `#lulls` node is never touched.
- **T16 — transport rules (checklist 14(a),(b),(d)).**
  (a) `relayout()` (`client/replay_broadcast.html:3004-3015`) writes `--hudscale`, `--topband` and
  `--band` on `document.documentElement.style` — i.e. `:root`, which is what `--u`, `#board` and
  `#endcard` read (`:1847-1848`). It iterates three passes, re-measuring `$('transport').offsetHeight`
  each time. Re-run on `resize` (`:3016-3019`).
  (b) Nothing fixed-positioned sits inside the band: the two added overlays ride
  `bottom: calc(var(--band, 0px) + 8px)` (`#econ` `:2585`, `#doctrines` `:2601`).
  (d) Beats are real labelled `<button>`s with `aria-label` and `title`
  (`:2806-2819`), each seeking to its own tick (`:2814-2817`), and the builder is deliberately named
  `buildBeatButtons`, not `markBeat` (`:2796-2801`; `tests/test_viewer.nim:141-143`). CSS exists for
  every kind the sim emits: `broadcast.nim:119-127` emits exactly
  `backstab|king|cat|game|end`, and `client/replay_broadcast.html:2609-2615` styles
  `.doctrine, .king, .backstab, .cat, .game, .end` plus `button.beat-marker`, on top of the
  inherited `.beat-marker` base rule at `:1697`. Seek fractions are consistent because `st = 0`
  (`broadcast.nim:183`), so the marker's `left` = `(b.t - st)/span` and its click `b.t/span` agree.
- **T17 — scoring implementation vs the note's §Scoring.**
  `world.nim:651-672 gamePoints` computes each share as `float32(x) / float32(total)` with an
  explicit `0.0'f32` zero-total guard, widens to `float64` for the weighted sum, and truncates with
  `int(...)` — no rounding. Weights `(0.5, 0.3, 0.2)` when `w.isCooperation`, `(0.3, 0.5, 0.2)`
  otherwise (`:657-658`). `cooperation_at_end` is taken from the live flag
  (`rules.nim:132 outcome.cooperationAtEnd = w.isCooperation`), never from `domination`.
  `scoresFor` (`match.nim:147-161`) = `100 * gamesWon + mean(points over games actually played)`,
  `[0.0, 0.0]` for zero games. `tests/test_scoring.nim:23-35` pins the `peaceinourtime` vector
  (catDamage 4000/4000, cheese 1590/2940, packed 17231/19732 → 1 and 2 kings → **42 / 57**, B ahead);
  `:37-45` pins truncation (16/33, not 17/33); `:72-83` proves the float32 width is the one used;
  `:85-95` proves `cooperation_at_end` comes from the flag with `domination == dfKillAllRatKings`;
  `:97-129` walks the whole tiebreak ladder including the reproducible seeded coin flip.
- **T18 — end conditions and the deadline partial-scoring rule.**
  `EndReason` = `kings_destroyed | cats_cleared | round_limit | abandoned`
  (`sim_types.nim:55-60`); `abandoned` can never reach `results.games[]` because
  `match.nim:126-132` breaks before `outcomes.add`. `EpisodeReason` = `complete | deadline | fault`
  (`:62-67`), matching the manifest enum and `docker_smoke.sh`. `deadline`: unfinished game
  discarded, finished games scored (`match.nim:128-133`, `results.nim:53-59`), `[0,0]` when none
  finished (`match.nim:151-152`). `fault`: `server.nim:275-280` catches any `CatchableError` from
  `playMatch`, sets `epFault`, clears `games` (→ `[0,0]`), and still writes both artifacts
  (`:316-323`). Container exit: the `runServer` path never `quit`s non-zero after the episode;
  `parseConfig` raises `ConfigError` for an unknown year, `num_agents != 2` or an unknown pool
  (`:218-225`).
- **T19 — parity oracle.** `ci.yml:180-346`: `parity-oracle` fetches the pinned `engine.1.2.5`
  sources + `battlecode26-java-1.2.5.jar` + the scala jar, `javac`s the real `examplefuncsplayer`,
  runs it against itself headless on the five `small`-pool pairs, and diffs
  `tools/parity_trace.py` (flatbuffer reader) against `tools/parity_trace.nim`. Tier A (rounds 1–50)
  and Tier B (round 200) `exit "$fail"` — blocking; Tier C only writes `$GITHUB_STEP_SUMMARY`.
  Run 33818291222's job log shows real, map-distinct engine output ("DefaultSmall: examplefuncsplayer
  (B) wins (round 1310)", "arrows: … (A) wins (round 1115)", …), Tier A and Tier B "bit-exact" on all
  five, Tier C `none (identical)` on four maps and `915` on `arrows`.
- **T20 — the 13 test shards.** All present and non-empty: `test_rng.nim` (Java vectors +
  `IDGenerator`), `test_constants.nim` (regenerate-and-diff when `BC_ENGINE_DIR` is set, with spot
  values otherwise), `test_maps.nim` (re-convert-and-diff + the note's size/symmetry table),
  `test_rules_motion/economy/combat.nim` (the rule families), `test_scoring.nim`, `test_sheet.nim`,
  `test_baselines.nim`, `test_determinism.nim`, `test_replay.nim`, `test_knob_sensitivity.nim`,
  `test_perf.nim` (≤ 45 s gate, `Budget = 45.0`, largest map in the shipped pool),
  `test_manifest.nim`, `test_viewer.nim` + `tools/wasm_replay_smoke.cjs`. `ci.yml:135-170` runs every
  `tests/*.nim` in **both** debug and `-d:release`. Caveats in N13.
- **T21 — sheet per-field default repair (checklist 8 / note §The doctrine sheet).**
  `sheet.validate` (`sheet.nim:168-300`) never raises: a non-object payload takes every default
  (`:173-175`); each knob is repaired individually with the field name pushed into `defaultsApplied`;
  unknown keys are recorded (≤ 16, ≤ 40 runes) and ignored; `MaxSheetKeys = 32` bounds the loop.
  `tests/test_sheet.nim:54-94` covers out-of-range and mistyped for every knob and counts the repairs.
- **T22 — anonymity of the map draw and side assignment.** `drawMaps` (`maps.nim:118-128`) picks
  `count` **distinct** maps by successive seed-derived indices; `sideAslotFor` (`:130-133`) is
  `((seed shr 8) and 1) xor (gameIndex and 1)` — sides alternate. Seed, maps and side assignment are
  recorded in `results` (`results.nim:85-86`) and the replay (`replay.nim:105-110`). A zero
  `game_config.seed` draws 31 bits from `/dev/urandom` (`server.nim:228-239`).

---

## Could not determine

- **Whether the `parity-oracle` job's Java runs are as thorough as they look.** The whole job
  completed in 33 s and the five headless matches took ~1.5 s total (job 100855120444,
  23:36:23.1 → 23:36:28.4), which is fast for five 1100–1310-round Battlecode games plus the
  flatbuffer trace extraction at 50/200/2000 rounds. Everything I can check from the log is
  internally consistent (distinct per-map winners and round numbers; a Tier C divergence at round 915
  on `arrows` only; a 10-file `parity-traces` artifact). **What would settle it:** the
  `parity-traces` artifact contents plus the byte size of `/tmp/oracle/*.bc26`, or a re-run with the
  per-map `java` wall clock echoed.
- **Whether the game block's endcard would re-show itself after a seek even with B1 fixed.**
  `renderEndcard` returns early on `endcardShown` (`:2960`) and `dismissEndcard` clears the flag
  (`:2955`); if a state frame carrying `ph:'gameover'` arrives after a dismissal that did not move
  the playhead off the last frame, the card would re-arm on the next `onText`. I could not settle
  this from the code alone because the ordering of the seek's `inputApplied` frame against the
  in-flight `advanced` frame is a runtime property. **What would settle it:** a browser run that
  scrubs back from `FINAL` and reads `#endcard`'s computed `display` twice.
- **Whether `#scorebug .plate-sub` (real player name + up-to-48-rune motto) overflows the scorebug at
  ≥ 640 px.** The page has no `overflow`/ellipsis on `.plate` or `.plate-sub` (`:2560-2562`) and the
  fixture that would test it ships different CSS (N8). The `viewer-smoke.json` scorebug string
  ("CLAN ASH Clan Ash · Cheese first. 92 …") is the *scripted* motto, 13 runes. **What would settle
  it:** the fixture run against the page's actual rules, or a browser screenshot at 640–900 px with a
  48-rune motto.
- **Whether `data-replay-loaded` is set on the first *drawn* frame or on the first *ingested* one.**
  The worker posts `loaded` immediately after `ingestPacket()` (`static_replay_worker.js:141-150`),
  and `core.ingest` is documented as parsing synchronously; the separate `onFirstFrame` callback
  exists and is wired (`:109-111`, `client/replay_broadcast.html:3139-3142`) but is not what gates
  the attribute. This is the starter's behaviour verbatim (the only diffs in that file are export
  renames), so it is inherited, not introduced. **What would settle it:** whether ctf's own
  `onFirstFrame` fires before or after `postMessage({type:'loaded'})` inside `broadcast_core.ingest`.

---

## Summary

1 blocking finding (B1, `static-viewer`: `#endcard` shown with `.show` against a `#endcard.on` rule)
and 16 non-blocking observations. Checklist items 1–13 and 15 traced and satisfied from the tree and
cited CI evidence; item 14 satisfied on provenance and transport rules (a), (b), (d), and falsified
on (c)'s "shown with the class its CSS rule uses".
