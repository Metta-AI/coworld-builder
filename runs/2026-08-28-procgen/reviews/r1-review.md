# r1 review — procgen

Range: `eedfe37..556cb50` (whole run history; HEAD `556cb50fb74e14795a1123ab37d2e1bfd92f2d6f` on `main`)
Files read: 71 (all of `src/`, `replay-viewer/`, `client/`, `tests/`, `tools/`, `.github/workflows/`,
`coworld_manifest_template.json`, `compose.yaml`, `Dockerfile*`, `docs/RULES.md`, `docs/PROTOCOL.md`,
plus the starter files at `/workspace/starters/coworld-ctf` used for provenance diffs, plus CI logs for
runs 33199610304 / jobs 98945460474, 98945460661, 98945814705)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST items 1–15

Design note: `/workspace/coworld-builder/runs/2026-08-28-procgen/design.md` (1903 lines); the repo copy
at `docs/plans/2026-08-28-procgen-design.md` is byte-identical (`diff` clean).

Convention used below: **observed** = I read the code/log; **inferred** = I reasoned from what I read;
**untested** = would need a run to settle.

---

## Blocking

**None.** I could not falsify any of checklist items 1–15 from the tree or from the cited CI evidence.
Item 1's second half ("no test loosened") has one hunk that a judge should rule on explicitly — it is
recorded below as **F25** rather than filed as blocking, because the narrowing it makes is a correction
to an assertion that was asserting something the code never did. Everything else I found is a deviation
from the *design note* that no checklist item names.

---

## Non-blocking

### F1 — The runtime/dependency stack is not coworld-ctf's; the chrome and viewer files are
*(category: other)*
- Where: `procgen.nimble:8-12`; `src/procgen/runtime.nim:1-17`; vs `/workspace/starters/coworld-ctf/ctf.nimble:8-20`
- Observed: `procgen.nimble` requires only `nim`, `mummy`, `whisky`, `curly`, `jsony`. The starter
  requires `bitworld`, `pixie`, `flatty`, `supersnappy`, `zippy`, `fluffy`, `silky`, `windy`, `paddy`
  in addition. `src/procgen/runtime.nim:1-17` carries its own copy of the Coworld contract
  (`readCogameUri` / `writeCogameUri` / `readRuntimeConfig`) and says so: *"`coworld-ctf` gets this from
  `bitworld/runtime`; this fork carries its own copy because the rest of bitworld … is a continuous-2-D
  rendering stack this grid game does not use."* `src/procgen/llm.nim:26-28` imports `runtime` where the
  starter's `src/ctf/llm.nim:23` imports `bitworld/runtime`.
- What the note says: the header (design.md:9-24) says *"Every convention there holds here unless this
  note says otherwise … the flatty wire types whose field order is sacred … the Sprite v1 mummy
  HTTP/websocket server"*. §Sim module (design.md:1055-1058) says the replay stays *"the starter's binary
  `COWLD…` format (`replays.nim`'s `CtfReplayMagic` renamed)"*. In fact `src/procgen/replays.nim:46-58`
  is a hand-written little-endian encoder (`putU32`/`putU64`/`putStr`), not flatty; the magic
  `COWLDPGN` and the layout are new but of the same shape.
- Counter-evidence for the "not inherited" reading, all verified: `client/chrome_common.js` is
  **byte-identical** to the starter's (40 022 bytes, sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` on both — `sha256sum` run in this
  sandbox); `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` diff against the
  starter's with **rename-only** changes plus the enumerated minimap/zoom removals; `src/procgen_player.nim`
  is a line-for-line fork of `src/paintball_player.nim`; `src/procgen/llm.nim` diffs against
  `src/ctf/llm.nim` with only the `SystemPrompt` const and log-prefix strings changed.
- I could not diff against `Metta-AI/cogame-snake-royale` — it is not mounted in this sandbox.

### F2 — `client/broadcast_core.js` is a rewrite, not a fork of the starter's file
*(category: static-viewer)*
- Where: `client/broadcast_core.js:1-700` vs `/workspace/starters/coworld-ctf/client/broadcast_core.js` (1407 lines, 62 123 bytes)
- Observed: 700 lines / 28 368 bytes. The longest common byte prefix with the starter's file is **25
  bytes** (`// broadcast_core.js — `). Function-name intersection is limited to `create`,
  `getTransform`, `getPaceStats`, `ingest`, `stop`, `start`; the starter's `SnappyCompressor`,
  `decodeSpritePixelsSnappy`, `composite`, `defineLayer`, `blitObject`, `attachMinimap`, `clampView`,
  `computeFit` are all gone, and `drawTiles`/`drawCog`/`drawEntities`/`drawExit`/`drawPlanTrail`/
  `drawSplitBar`/`drawBubbles` are new.
- What the note says (design.md:1234-1244): *"`client/broadcast_core.js` is **forked** … Kept and pinned
  function-by-function against the starter's text: the canvas/DPR sizing, `relayout()`, the camera, the
  feed queue and **`pushFeed` including its signature** … `banner`, the beat and lull machinery, the
  endcard builder, the speed chips, the `?embed=1` path, the shout-bubble renderer"*.
- Observed mitigations: every item that list names except the canvas sizing actually lives in
  `client/replay_broadcast.html` in **both** repos (`pushFeed` at `client/replay_broadcast.html:1400`
  here, at `:3558` in the starter per the note), and that file **is** the starter's with deletions (F3).
  `tests/test_procgen_viewer.nim:77-81` checks only method-surface needles (`window.BroadcastCore`,
  `ingest:`, `sendCommand:`, …), not byte-identity, so the note's test-40 clause *"`broadcast_core.js`'s
  kept procs are byte-identical to the starter's, `pushFeed`'s signature included"* is not implemented.
- Checklist item 14 names only `chrome_common.js` and `replay_broadcast.html` for provenance, and both
  pass; `broadcast_core.js` is not on that list.

### F3 — `client/replay_broadcast.html` IS the starter's page with deletions plus one appended block
*(category: static-viewer — verified consistent, recorded because size alone looks alarming)*
- Where: `client/replay_broadcast.html` (1991 lines / 101 151 bytes) vs starter (4660 lines / 234 070 bytes) = 43.2 %
- Observed: `diff starter procgen` = 3132 removed lines, 463 added. The first byte divergence is at
  offset 159 (`<title>Ctf —` → `<title>Procgen —`). The starter's numbered CSS sections survive in order
  and in place: `1. TOP-BAND SCOREBUG` (:150), `3. BANNER LANE` (:295), `2. KILL FEED` (:327),
  `5. TRANSPORT` (:381), `6. END-CARD` (:564), plus the `Ink & Print` palette block (:8), the
  `PRE-LOAD CURTAIN` locker room (:779), the fixed-aspect block (:928) and `EMBED MODE` (:943). The
  starter's `4b. VIEW CONTROLS (zoom + minimap)` section is the one section removed wholesale — which is
  the removal the note lists.
- The appended block starts at `client/replay_broadcast.html:1581` under the banner comment
  `PROCGEN additions to the inherited coworld-ctf chrome`, and installs through the starter's own hook:
  `if (window.ProcgenChrome) window.ProcgenChrome.install(PB_CTX);` at `:1573` (inside the inherited
  head) and `window.ProcgenChrome.frame(s, PB_CTX, jumped)` at `:1383` (inside the inherited `onFrame`).
  `PB_CTX` at `:1560-1568` carries `$, C, esc, fmt, send, pushFeed, banner, clearFeed, seekToFraction,
  getState`.
- I scripted the id checks: every id the note's "Kept" list names (`#viewport`, `#stage`, `#board`,
  `#lightpool`, `#grain`, `#lockerroom`+children, `#chrome`, `#scorebug`, `#plates-l`, `#clock`,
  `#clock-time`, `#clock-caption`, `#ffwd-mini`, `#bannerlane`, `#killfeed`, `#mmwarn`, `#transport` and
  all twelve of its children, `#scrub`+`#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/`#scrub-head`,
  `#endcard`+five children, `#status`) is present. Every id the note lists as removed
  (`#viewpanel`, `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`, `#zoom-slider`,
  `#zoom-read`, `#fpv*`, `#povBadge`, `#plates-r`) is absent from markup and from `$('…')` wiring.
  `attachMinimap` appears in neither the page nor `broadcast_core.js`. `.squad-pip` survives only inside
  a `//` comment at `:1298`.

### F4 — `climber` ships three walkable tiers, not the note's four
*(category: correctness)*
- Where: `src/procgen/gen.nim:34-35` (`ClimberWalkRows* = [7, 4, 1]`, `ClimberBandRows* = [5, 2]`);
  rationale at `src/procgen/gen.nim:12-20`; gem placement at `gen.nim:424-436`
- Observed: two platform bands at y=5 and y=2 carry three walkable rows y∈{7,4,1}. Gems are placed
  one on the ground tier, one on the top tier and two on the middle tier (`gen.nim:430`).
- What the note says (design.md:289-290): *"four platform rows (`y ∈ {7,5,3,1}`) over a pit, ladders
  between"*, *"4 `Gem`, one per platform row"*.
- Recorded as a deviation in the shipped docs: `docs/RULES.md` §Divergences item 6, inlined into
  `game.docs.pages["rules.md"]` in the manifest. The stated reason (four tiers in nine rows leaves no
  headroom, so `X` would be a no-op) is consistent with `src/procgen/levels.nim:562-567`, where the jump
  only moves the cog when `not st.grid.at(above).solid()`.

### F5 — `pathfinder.digCost` is 1, not the note's 3
*(category: correctness)*
- Where: `src/procgen/baselines.nim:44-45` (`PathfinderTunables = Tunables(lookaheadFrames: 6, digCost: 1, commitFrames: 6, detourBudget: 6, exitFirst: false)`); rationale at `baselines.nim:37-43`
- What the note says (design.md:654): `digCost` row, `pathfinder` = 3.
- Observed: the note's own rule (design.md:669-673) is that the tunables are *swept, not guessed*, and
  the sweep matrix that produces the pick is real: `tools/tune_baselines.nim:36-49` sweeps
  `lookahead ∈ {1,3,6} × digCost ∈ {1,3} × detour ∈ {0,6}` over the ladder and `ci.yml:118-121` runs
  `--sweep --check` on every push. `tools/ci/baseline_tuning.json` records the pick and the ladder.
  The claim in `baselines.nim:39-43` that digCost 3 loses the ladder by −0.010 is **untested** by me —
  it is a claim about a sweep output I did not reproduce; the sweep itself does run in CI (job 98945460474).

### F6 — the ladder margin band is `[+0.02, +0.45]`, and the "24-episode ladder" is recorded as 12
*(category: correctness)*
- Where: `tools/ci/baseline_tuning.json:31-33` (`"marginMin": 0.02`, `"marginMax": 0.45`, plus a
  `marginBandNote` that states the note asked for +0.05 and explains why the measured value is +0.038);
  the check at `tools/tune_baselines.nim:88-99`
- What the note says (design.md:673): *"a margin inside `[+0.05, +0.45]`"*; design.md:1736-1737 repeats it.
- Observed second discrepancy: `src/procgen/engine.nim:120-131` plays 3 difficulties × 4 seeds = 12
  seed/difficulty pairs, running **both** baselines on each (24 episode runs) but incrementing
  `result.episodes` once per pair (`engine.nim:131`), so `ladderMargin` (`engine.nim:133-138`) divides by
  12 and `baseline_tuning.json:24` records `"episodes": 12`. `tools/tune_baselines.nim:1-6` still calls
  it "the fixed 24-episode ladder". The arithmetic is right for a per-pair mean difference; only the
  count's name differs from the note.
- `tests/test_procgen_control.nim:194-199` deliberately does **not** re-run the ladder — it asserts only
  that `marginMin`/`marginMax` keys exist and that the shipped tunables equal the recorded pick. The band
  itself is enforced by `ci.yml`'s sweep step.

### F7 — the certification fixture plays 8 levels, not the note's 4
*(category: manifest)*
- Where: `coworld_manifest_template.json:552` (`"levelCount": 8` inside `certification.game_config`);
  asserted at `tests/test_procgen_engine.nim:75-77`; the reason at `tests/test_procgen_engine.nim:94-99`
- What the note says (design.md:1584, 1593): `"levelCount": 4` and *"Four levels is milliseconds of sim
  but ≈ 30 s of playback"*.
- Observed: the shipped `pathfinder` plays a level in ~25 frames, so 4 levels would be ~100 frames
  (~17 s at 6 sim-frames/s) rather than the note's 180-frame / 30 s estimate. The CI evidence agrees:
  the smoke replay produced `mx = 193` steps (viewer-smoke log, run 33199610304) and the soak observed
  `0 / 193` → `48 / 193` → `60 / 193`, i.e. ~32 s of playback available against a 10 s soak.
- The note's own numbered test 27 floor (≥ 180 frames) is asserted at `tests/test_procgen_engine.nim:100-102`.
- The seat-count invariants are unaffected: `certification.game_config.num_agents == 1`,
  `len(certification.players) == 1`, `len(certification.game_config.players) == 1`, `SMOKE_SEATS == 1`.

### F8 — the chrome sha256 is enforced by `ci.yml`, not by the Nim test
*(category: static-viewer)*
- Where: `tests/test_procgen_viewer.nim:20-28, 37-48` (pins length 40022 and **sha1**
  `d970ebe4eff1b0154ba604b4e9adf62d601cb3eb`, and carries the sha256 as a literal that is only
  length-checked); `.github/workflows/ci.yml:104-111` (`sha256sum -c -` on the note's sha256)
- What the note says (design.md:1218): *"`tests/test_procgen_viewer.nim` pins that sha256 as a literal"*.
- Observed: Nim's stdlib ships `std/sha1` and no sha256, which is the stated reason (test file lines
  20-24). Net effect is equivalent — I verified by hand that
  `sha256(client/chrome_common.js) == sha256(starter/client/chrome_common.js) ==
  7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` and that the files are `diff`-clean.
  The ci.yml step is unconditional and ran green in job 98945460474.

### F9 — no committed `.replay` fixtures; `wasm_replay_smoke.cjs` runs against the docker-smoke replay
*(category: static-viewer)*
- Where: `tests/fixtures/` does not exist (`tests/test_procgen_replay.nim:142-146` walks it only
  `if dirExists`); `.github/workflows/ci.yml:385-397` runs
  `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer "${replay}" 300` where `${replay}` is the
  `smoke-replay` artifact from `docker-smoke`
- What the note says (design.md:1846-1852): *"Four fixtures are committed and re-recorded on every
  `GameVersion` bump — `tests/fixtures/gauntlet-seed42`, `sprint-seed7`, `hard-seed13`,
  `deadline-seed21` — with their recipes in `tests/test_procgen_replay.nim`"*.
- Observed: the substitute is stronger in one respect and weaker in another. Stronger: the wasm smoke
  runs against a **current-format episode produced by the image under test** in the same run, and it
  fails on `Module._procgen_mismatch_tick() !== -1` both before and after 300 frames
  (`tools/wasm_replay_smoke.cjs:88-102`), so wasm/native grid identity is proved by the hash chain
  rather than by a separate cross-target case. CI log for job 98945814705:
  `ok: loaded episode.replay, advanced 300 frames (1732337 packet bytes, heap 16 MB)`. Weaker: there is
  no committed artefact to detect a *silent format change* against an older recording, and the note's
  numbered test 14 cross-target case (`design.md:1688-1691`) has no Nim implementation — I read
  `tests/test_procgen_gen.nim` end to end and it contains no wasm case.
- In-process re-derivation is asserted at `tests/test_procgen_determinism.nim:24-27` and
  `tests/test_procgen_replay.nim:32-44` (`rt.mismatchFrame < 0` for `gauntlet_complete`, `wall_clock`
  **and** `sim_fault`), which is checklist item 2's test.

### F10 — generator sweeps are 150/400 seeds, not the note's 500/5000
*(category: correctness)*
- Where: `tests/test_procgen_gen.nim:23-25` (`let wide = getEnv("SWEEP_WIDE").len > 0`,
  `pureSeeds = if wide: 500 else: 150`, `validSeeds = if wide: 5000 else: 400`); rationale at
  `tests/test_procgen_gen.nim:5-12`
- What the note says (design.md:1688, 1692-1695): 500 seeds on test 14, *"over 5000 seeds per archetype
  per difficulty"* on test 15.
- Observed: `SWEEP_WIDE` is not set anywhere in `.github/workflows/` (grep returns nothing), so CI
  always runs the narrow sweep — 150×4×3 = 1800 purity draws and 400×4×3 = 4800 validation draws per
  build, and each test file runs twice (debug + release) per `ci.yml:123-169`. The `genFallbacks == 0`
  assertion (`tests/test_procgen_gen.nim:89-91`) therefore covers 4800 seeds, not 60 000.

### F11 — the tile kit is drawn browser-side; `procgen_art.nim` is a manifest, not a bake
*(category: other)*
- Where: `src/procgen/procgen_art.nim:1-11` (*"`coworld-ctf`'s `rig_art.nim` bakes its rig segments
  server-side into the sprite protocol. This fork draws the grid in the browser, so the bake is the
  browser's: this module is the SINGLE list of the shipped sprite files"*);
  `client/broadcast_core.js:74-100` (`loadArt` / `loadKit` fetch `./<name>.png`)
- What the note says (design.md:1389-1392): the split sheets are *"fed to the starter's **existing**
  `rig_art.nim` bake plumbing (renamed `procgen_art.nim`; same masters/pivots/scale path) so every piece
  is baked once at `cellPx = 32` and composited per frame"*.
- Observed art quality (checked, because the pin is "real art, not placeholders"): `data/` carries 22
  128×128 PNGs of 10–26 KB each (`tile_bedrock.png` 23 894 B, `cog_r.png` 17 556 B, `ent_gem.png`
  13 787 B …), plus `arena_floor.png` (256×256, 67 335 B) and `pallete.png` (16×1). Three source sheets
  ~1 MB each are committed at `scripts/art/source/{tiles,entities,cog}_sheet.png` with
  `scripts/art/split_tile_sheet.py`. None of these are solid-colour squares.
- Every sprite has a procedural fallback in the same palette (`broadcast_core.js:267-313, 342-370,
  381-397, 412-423, 435-445`), so a missing asset degrades rather than blanks the board.
  `Dockerfile.replay-viewer:72-81` asserts six of the PNGs plus the starter's wall/lockerroom art land
  in the bundle.

### F12 — the `directive` chat record never carries its `view` field
*(category: correctness)*
- Where: `src/procgen/directives.nim:194-195` (`if viewJson.len > 0: result["view"] = %viewJson`);
  the two call sites pass `""`: `src/procgen/server.nim:432-433` and `src/procgen/engine.nim:68-69`
  (both `boundedDirectiveRecord(order, turnIndex, episode.levelIndex, cogAlias(0), "")`)
- What the note says (design.md:1110): the `directive` record's fields include
  *"`view` (the observation minus `your_notes`)"*.
- Consequences I traced: (a) the note's numbered test 17 clause *"no real player name … appears in …
  any `directive.view`"* (design.md:1703-1705) is vacuous — `tests/test_procgen_identity_privacy.nim:98-105`
  greps the whole record instead, which still catches the name; (b) the `MaxDirectiveRunes = 4000`
  trimming ladder in `directives.nim:205-215` is dead code, since a view-less record is ~200 bytes
  (`tests/test_procgen_control.nim:58-60` asserts ≤ 1024); (c) `tools/replay_summary.py` does not read
  `view`, so the phase-60 recipe at design.md:1070-1081 is unaffected.

### F13 — `gamestart` and `plan` are declared event kinds that nothing ever emits
*(category: correctness)*
- Where: `src/procgen/levels.nim:51` (`ekGameStart = "gamestart"`) and `:53` (`ekPlan = "plan"`);
  `src/procgen/events.nim:22-25` lists both in `AllEventKinds`. Grep across `--include=*.nim` finds no
  construction site for either: the only hits are the enum declarations, `AllEventKinds`, and the two
  `simKindOf` arms (`events.nim:71, 85`).
- What the note says (design.md:1140-1141): *"`tests/test_procgen_events.nim` asserts the **emitted** set
  equals **exactly** this list"*.
- Observed: `tests/test_procgen_events.nim:16-40` asserts the **declared** enum equals the seventeen
  names, and `:42-61` asserts a real episode emits only a *subset* of them (checking presence of
  `levelstart`, `step`, `levelend`, `gauntletend`, `end` only). So the note's "emitted set == the list"
  is not what the test checks, and two kinds are unreachable.
- Downstream effect is nil: the plan trail draws from `snap.plan`/`snap.planRun` in the frame packet
  (`src/procgen/broadcast.nim:217-218`, `client/broadcast_core.js:463-503`), not from an `ekPlan` event;
  `gamestart` makes no beat and no feed row.

### F14 — one enumerated label re-mapping was dropped at HEAD
*(category: legibility)*
- Where: commit `556cb50` removed `<span class="lvl-label">Level</span>` from `plateHtml`
  (`client/replay_broadcast.html:1838` before the commit) and its three CSS rules
- What the note says (design.md:1291): the re-mapping table requires
  `<span class="lives-label pb-lbl">Hill</span>` → `<span class="lvl-label">Level</span>`, and
  design.md:1302 says *"asserts each replacement string above is present exactly once"*.
- Observed: `lvl-label` now appears nowhere in the page. The level still reads from the chip
  (`.lvl-chip` → `L3/8 · MINER`, `client/replay_broadcast.html:1832-1837`) and from
  `#clock .level-badge` → `LEVEL 3/8` (`:1889-1897`), so the information is not lost. The forbidden-word
  test (`tests/test_procgen_endcard_labels.nim:23-32`) does not list "Level" among `Replacements`, so
  nothing failed. The CI viewer smoke's scorebug readout confirms the shipped text:
  `"Cog1 COG-alpha L3/8 · MINERSEEN 4/4 GEMS LEVEL 3/8 …"`.
- The other seven enumerated re-mappings are present: `Unseen mean` / `Seen mean`
  (`client/replay_broadcast.html:1794, 1796`), `SEEN vs UNSEEN` (`:1045`), `Generating levels&hellip;`
  (`:978`), `Before the first level` (`:997`, `:1882`), `Replay hash mismatch at frame … showing
  recorded moves` (`:1394-1395`), the seven-column endcard header (`:1795-1798`), and `Gems`
  (`:1843`).

### F15 — feed wording differs from the note's worked examples
*(category: legibility)*
- Where: `src/procgen/labels.nim:40` (`deathPhrase(...) & " — level over"`) and `:42`
  (`"plan cut short — danger alongside"`)
- What the note says (design.md:1360-1361): *"`a hunter catches COG-alpha — level over at 425`"* and
  *"`plan cut short — hunter alongside`"*.
- Observed: the return value is not appended to the death row (it appears on the `levelend` row instead,
  `labels.nim:45-48`), and the interrupt row is archetype-agnostic. `tests/label_manifest.txt` matches
  `LabelVocabulary` (`labels.nim:59-67`), so the contract test passes on the shipped strings.

### F16 — numbered test 13 asserts a 60 s budget, not the note's "< 1 s in release, no frame > 1 ms"
*(category: other)*
- Where: `tests/test_procgen_sim.nim:406-422` (`check elapsed < 60000`), with the reason at `:417-419`
  (the file runs in debug as well as release)
- What the note says (design.md:1683-1684): *"a full 8-level, all-scripted, `hard` episode completes in
  < 1 s in a release build, and no single frame exceeds 1 ms"*.
- Observed: there is no per-frame timing assertion anywhere. This was written this way in the initial
  commit `d33639d`, not loosened during the run.

### F17 — numbered test 44 asserts "present at least once", not "exactly once"
*(category: legibility)*
- Where: `tests/test_procgen_endcard_labels.nim:74-76` (`check count >= 1`), with the stated reason at
  `:26-29` (a caption that is both a markup default and a JS assignment legitimately appears twice)
- What the note says (design.md:1302): *"asserts each replacement string above is present exactly once"*.
- Observed: the load-bearing half — zero matches for the 18-word forbidden paintbot vocabulary outside
  comment blocks — is asserted at `:51-61` and does pass on `client/replay_broadcast.html` and
  `client/broadcast_core.js`.

### F18 — numbered tests 29(a) and 31 are source greps, not live exercises
*(category: other)*
- Where: `tests/test_procgen_engine.nim:207-226` (sets `played.episode.seat.dead = true` by hand, then
  greps `src/procgen/server.nim` for `playerFailureJson(0)` and the loud log line) and `:292-315`
  (greps `server.nim` for the four route registrations, their order relative to `/**`, the token check,
  the `Ping → Pong` branch and `ShutdownGraceSeconds`)
- What the note says (design.md:1754-1763): test 29 wants both seat failure modes to *"produce a finished
  episode inside the wall-clock budget"*; test 31 wants `/healthz`, `/client/player`, `/client/global`,
  the `/global` first message and a websocket `Ping → Pong` to *"all answer"*.
- Observed: test 29(b) *is* a real exercise — `tests/test_procgen_engine.nim:232-257` drives
  `decider.turn` against a live `DecisionEngine` with `isLlm = true` and no credentials, and asserts every
  turn produced a legal plan and `fallbackTurns == turns`, `llmTurns == 0`. The HTTP surface is exercised
  end to end by `tools/ci/docker_smoke.sh` against the real container (job 98945460661 →
  `smoke OK: seats=1 results=968B replay=14060B reason=complete`), just not by the Nim test.
- The routes themselves are registered before the catch-all: `src/procgen/server.nim:289-297`
  (`/healthz`, `/client/player`, `/client/global`, `/client/replay`, `/player`, `/global`, then `/**`),
  and `websocketHandler` answers Ping with Pong at `:250-252` while filtering nothing else.

### F19 — the post-artifact grace is a fixed 20 s, not the note's `gameOverFrames` grace
*(category: timeout)*
- Where: `src/procgen/server.nim:63-65` (`ShutdownGraceSeconds* = 20`) and `:493-498`
  (`let graceUntil = getMonoTime() + initDuration(seconds = ShutdownGraceSeconds)`, then a `sleep(250)`
  loop, then `httpServer.close()`)
- What the note says (design.md:883): the probes *"keep answering for the `gameOverFrames` grace after
  artifacts are written"* — `gameOverFrames = 12`.
- Observed: the display hold before artifacts *is* derived from `gameOverFrames`
  (`server.nim:474`, `sleep(max(0, config.gameOverFrames) * 20)` = 240 ms), and the 20 s is a second,
  fixed grace after them. Both are bounded, neither is a loop without an exit.
- Arithmetic (inferred, from the shipped numbers): the budget guard at `src/procgen/decide.nim:201-209`
  fires when `elapsed + 2 × turnBudgetSeconds() > wallClockBudgetSeconds`, and
  `turnBudgetSeconds()` is `ceil(7500/1000) = 8` (`src/procgen/sim_types.nim:100-101`), so the last turn
  that may still call the LLM begins at `elapsed ≤ 644`, ends by ≤ 652 s, and every later turn is
  microseconds. Results are written at ≈ 652 s worst case (+ up to 20 s per artifact PUT at
  `src/procgen/runtime.nim:35`, three of them, if the platform's URIs hang), and the process exits 20 s
  after that. The scored artifact therefore lands inside 720 s in every path I can construct; process
  exit could in principle reach ≈ 732 s only if all three artifact PUTs time out.
- Related: the note's arithmetic (design.md:589-593) assumes *"lobby ≤ 30 s"*, but the shipped
  `lobbyJoinTimeoutSeconds` is **90** in all three variants (`coworld_manifest_template.json:469, 500,
  531`). The lobby wait is bounded at `src/procgen/server.nim:307-316` and the episode clock starts
  *above* it (`:329-333`), so the 660 s stop and the guard still cover it.

### F20 — `config_schema` omits two keys `sim_config` parses
*(category: manifest)*
- Where: `src/procgen/sim_config.nim:89-91` reads `model` and `maxOutputTokens`;
  `coworld_manifest_template.json` `config_schema.properties` (22 keys) declares neither, and
  `additionalProperties` is `false` (`:` the schema block; verified by loading the JSON)
- What the code claims: `src/procgen/sim_types.nim:58-59` — *"Every field is also a `config_schema`
  property in `coworld_manifest_template.json`"* — and `sim_config.nim:3-5` says the same.
- Observed effect: a `game_config` that set `model` would be rejected by the platform validator, so the
  two knobs are compile-time only. `tests/test_procgen_manifest.nim:88-93` checks array properties and
  closure but does not cross-check the key sets. No shipped `game_config` sets either key.

### F21 — the game pod still serves `/client/replay`; the manifest declares only the static bundle
*(category: static-viewer)*
- Where: `src/procgen/server.nim:294` (`result.get("/client/replay", handleClientReplay)`) and
  `:144-148` (the handler, commented *"LOCAL developer replay mode only. This route is NEVER declared to
  the platform"*)
- Checklist item 3 says *"No `/client/replay` pod path anywhere"*. Read literally, this route is one.
- Countervailing observations: the note explicitly retains it (design.md:912-913, 1162-1163); the
  starter does the same (`/workspace/starters/coworld-ctf/src/ctf/server.nim`, several `/client/replay`
  references); and the manifest declares `game.replay_viewer = {"bundle": "static-replay-viewer"}`
  (`coworld_manifest_template.json:25-27`) and nothing else. `tools/build_replay_viewer.sh` is present,
  mode `100755`, and is the `coworld build` hook — asserted by `ci.yml:289-300` and invoked by path at
  `ci.yml:312-313`. The viewer fetches only the `?replay=` URL
  (`replay-viewer/static_replay_worker.js:110-115`, `credentials: 'omit'`) and same-origin bundle assets.

### F22 — the main viewer smoke's `canvas_text` total is 0; text bounds are covered only by the fixture
*(category: legibility)*
- Where: `.github/workflows/ci.yml:357-383` (`viewer_smoke.mjs … --soak 10 --strict-text-bounds` against
  the docker-smoke replay) vs `ci.yml:399-422` (the renderer fixture step)
- CI evidence (job 98945814705):
  - bundle step: `{"loaded":true,"ms":346,…,"feed_lines":8}`; `soak: 10s of playback kept advancing
    ("0 / 193" -> "48 / 193" -> "60 / 193")`; three distinct scrub readouts; then
    `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
    (--strict-text-bounds)`.
  - fixture step: `{"loaded":true,"ms":695,…}` then
    `canvas text: 72 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
    (--strict-text-bounds)`.
- Observed: the `total: 0` on the bundle is exactly the case checklist item 15 calls out — the shipped
  bundle renders in a Dedicated Worker on an OffscreenCanvas
  (`replay-viewer/static_replay_worker.js:83-104`), and `viewer_smoke.mjs` patches
  `CanvasRenderingContext2D` in the page. `tools/ci/renderer_fixture.html:25-42` says so in as many
  words and is the compensating gate. The fixture loads the shipped `index.html` in an iframe
  (`renderer_fixture.html:51`), loads the shipped `broadcast_core.js` on a main-thread canvas
  (`:56`), drives a full-cap 24-rune `say` on a top-row cog, and **asserts its own strings are still
  full-length** (`renderer_fixture.html:320-323`, `if (SAY.length !== CAP) failed(...)`). It also
  asserts one plate, eight labelled `<button>` beat markers with `aria-label`, a non-empty `#momentum`,
  a feed row containing the full-cap say, the level banner, an eight-row endcard with highlighted
  unseen rows and the re-labelled captions, and **that the endcard comes back down on a seek**
  (`:306-311`).
- I read this as item 15 satisfied through the fixture, with the caveat that the number the judge should
  cite is the fixture's `72 / 0`, not the bundle's `0 / 0`.

### F23 — `seat.say` / `sayFramesLeft` / `saidTurns` are written and never read; `/global` ships no split bar
*(category: other)*
- Where: `src/procgen/server.nim:428-431` sets all three; grep over `--include=*.nim` finds no reader.
  `src/procgen/global.nim:57-59` always emits `"plan": {"moves": "", …}`, `"bubbles": []`,
  `"flashes": []`, and `:86-89` always emits empty `beats`/`lulls`/`feed` with no `lead` or `splitbar`
  key at all.
- What the note says (design.md:398-401): D6 wants `say` drawn as a board bubble for
  `sayFrames = 12` and pushed to the feed; design.md:897-900 lists `bubbles` in the broadcast state.
- Observed: the **replay** path does all of this — `src/procgen/replay_runtime.nim:223-228` records
  `rt.says[absIndex]` and emits `ekSay`, `src/procgen/broadcast.nim:186-194` builds the bubble with a
  `sayFrames`-wide back-window, `client/broadcast_core.js:574-609` draws it, and
  `src/procgen/labels.nim:50-51` produces the feed row. Only the **live `/global`** stream is degraded,
  and `/global` exists here to satisfy the certifier's status probe (design.md:1897-1898 puts the live
  spectator pod out of scope), so no spectator surface loses anything.

### F24 — `test_procgen_gen`'s note-numbered cross-target case, and the "no seed leak" test, are indirect
*(category: other)*
- Where: `tests/test_procgen_gen.nim` (no wasm case anywhere in the file);
  `tests/test_procgen_identity_privacy.nim:36-44` (greps the observation string for the real name, the
  literal `"seen"` and every level seed)
- Observed: the seed/split hiding is genuinely verified. I read `src/procgen/decide.nim:89-170`
  (`seatViewJson`) key by key: the emitted keys are `level{index,of,kind,w,h,difficulty}`, `turn`,
  `turns_left_this_level`, `frame`, `frames_per_turn`, `map`, `legend`, `you`, `collected`,
  `collect_total`, `exit_open`, `exit_at`, `exit_distance`, `hunters`, `falling`, `actions`,
  `levels_done`, `your_notes`, and optionally `nearest_gem`/`nearest_gem_distance`. No seed, no split,
  no policy name, no running score. `levels_done` (`decide.nim:120-127`) iterates
  `0 ..< episode.levelIndex - 1`, so unplayed levels are never disclosed. The system prompt
  (`src/procgen/llm.nim:197-231`) is byte-identical to design.md:681-714 and contains neither "seen" nor
  "unseen" (asserted at `tests/test_procgen_llm.nim:64-66`).

### F25 — one test assertion was narrowed during this run (item 1 relevance)
*(category: other — flagged so the judge rules on it explicitly)*
- Where: commit `a086c76`, `tests/test_procgen_art.nim:46-58`
- The hunk (`git log -p -- tests/`):
  ```
  -  for file in allArtFiles():
  -    if not file.endsWith(".png"):
  -      continue
  +  var kit = tileSpriteFiles()
  +  kit.add(entitySpriteFiles())
  +  kit.add(cogSpriteFiles())
  +  for file in kit:
  ```
  It narrows the "the renderer preloads this file" assertion from all 24 committed PNGs to the 22 sprite
  PNGs, dropping `arena_floor.png` and `pallete.png`.
- Observed justification (in the same hunk's added comment): `client/broadcast_core.js:93-99`'s `loadKit`
  really does not preload those two — the floor wash and the palette are drawn procedurally
  (`broadcast_core.js:227-240`) and the font is loaded as a `FontFace` (`:113-124`). The pre-change
  assertion was asserting something the code never did; it was presumably passing only because
  `allArtFiles()` was filtered differently before `a086c76`'s companion source change. Both files are
  still asserted to *ship and be non-empty* by `tests/test_procgen_art.nim:18-22`.
- The full `git log -p -- tests/` over `d33639d..HEAD` contains exactly three commits. The only other
  assertion changes are, net at HEAD: `check config.levelCount == 4` → `== 8`
  (`tests/test_procgen_engine.nim:75`, an equality either way, tracking F7) and a **new**
  `check deaths >= 1` (`:105`). `a086c76` temporarily lowered test 27's frame floor from 180 to 90; that
  was reverted by `2c88e66` and HEAD is back at the note's 180. No test file was deleted; no
  `skip`/`xfail`/`--skip` was added anywhere (grep over `tests/` finds none).

---

## Traced and consistent

**Checklist item 1 — CI green.**
`gh run list -R Metta-AI/cogame-procgen --branch main -w ci.yml` → run **33199610304** at the reviewed
sha `556cb50`, conclusion `success`, three jobs: `test` 53 s (98945460474), `docker-smoke` 1 m 17 s
(98945460661), `wasm-viewer` 2 m 11 s (98945814705). No job is `continue-on-error`; `wasm-viewer`
declares `needs: docker-smoke` (`ci.yml:276`). Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'`
over `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`, `docker_smoke.sh`, `policies.json` returns
nothing (exit 1) — clean.

**Checklist item 2 — replay re-derivation, frame by frame.**
`src/procgen/replay_runtime.nim:154-234`: `preScan` rebuilds the `GameConfig` from the recorded config
document (`replays.nim:191-210`), rebuilds the gauntlet plan from `levelKinds`/`levelSeeds`/`levelSplit`
(`replays.nim:212-234`), **re-generates** each level with `newLevel(kind, seed, difficulty)`
(`sim.nim:149-150`), and re-runs `stepFrame` over the recorded action bytes, comparing
`foldState()` against `recorded.hash` on **every** frame including the `255` level-boundary byte
(`replay_runtime.nim:181-183, 220-222`). The viewer draws from `rt.snapshots`, which is that
re-simulation (`broadcast.nim:164-222`), not from a parallel recording. Tests:
`tests/test_procgen_determinism.nim:24-51` (three seeds, final grid tile-for-tile) and
`tests/test_procgen_replay.nim:27-44` (all three end rules). In wasm, `tools/wasm_replay_smoke.cjs:88-102`
fails on any non `-1` `procgen_mismatch_tick`.

**Checklist item 3 — static viewer.**
`coworld_manifest_template.json` `game.replay_viewer.bundle == "static-replay-viewer"` (asserted twice:
`tests/test_procgen_manifest.nim:40-42` and the coworld-CLI step at `ci.yml:194-195`).
`tools/build_replay_viewer.sh` exists, mode `100755`, builds `Dockerfile.replay-viewer`'s
`replay-viewer-builder` target and `docker cp`s `/workspace/procgen/replay-viewer/dist/.` out; it carries
the ecos `mkdir -p "$(dirname …)"` fix at line 20 and the buildx/`--platform linux/amd64` handling.

**Checklist item 4 — both name spaces.**
In-game: `cogAlias(0)` → `COG-alpha` from `src/procgen/roster.nim:21-26`, and that is the only name in
the observation, the prompt, the `directive` record and the feed
(`tests/test_procgen_identity_privacy.nim:36-49, 98-105`). Spectator: the real name rides
`results.names` (`sim.nim:288`), the replay join record (`server.nim:370`), the replay config's
`players[].name` (`replays.nim:102`), and the scorebug plate `.plate-name`
(`client/replay_broadcast.html:1828`). `showPlayerLabels: false` in all three variants and the fixture.
The CI viewer smoke drew `Cog1 COG-alpha` on the plate.

**Checklist item 5 — degrade, never hang.** Every wait I could find, with its bound:
| Wait | Bound | Where |
|---|---|---|
| lobby | `lobbyJoinTimeoutSeconds` (90 / 45 in the fixture), `sleep(100)` poll | `server.nim:307-316` |
| LLM attempt 1 | `attempt1Ms = 5000` → `CURLOPT_TIMEOUT 5` | `decide.nim:260-278` |
| LLM retry | `retryMs = 2000` → `CURLOPT_TIMEOUT 2`, exactly one retry (`while open and attempt < 2`) | `decide.nim:252, 261, 305` |
| whole turn | `turnBudgetMs = 7500` monotonic check before each attempt | `decide.nim:187, 255-259` |
| batch spacing | `turnSpacingMs = 2500` floor on batch *starts* (0 in the fixture) | `decide.nim:241-246` |
| provider 429 with no other model | retry **skipped**, straight to fallback | `decide.nim:306-311` |
| turn count | `levelCount × turnsPerLevel ≤ 80`, asserted per variant | `test_procgen_manifest.nim:62-63` |
| episode | `wallClockBudgetSeconds = 660`, checked at the top of the level loop and the turn loop | `server.nim:388-394, 404-410` |
| budget guard | `elapsed + 2×8 > 660` ⇒ scripted for the rest | `decide.nim:201-209`, `sim_types.nim:100-101` |
| generator redraw | `MaxRedrawAttempts = 40`, then a committed fallback level | `gen.nim:512-516` |
| BFS / Dijkstra | ≤ 135 nodes, `done[]`-bounded | `path.nim:40-101` |
| path walk-back | `guard < BoardCells * 2` | `path.nim:122, 148` |
| chaser/miner placement loops | `guard < 400`, climber `< 300`, maze braid `< 200` | `gen.nim:250, 350, 363, 428, 440, 474, 483` |
| artifact fetch/PUT | `FetchTimeoutSeconds = 20`, failure logged not raised | `runtime.nim:35, 65-84` |
| shutdown grace | `ShutdownGraceSeconds = 20` | `server.nim:63, 495-497` |
| player container dial | `240 × 500 ms`, then `quit(1)`; reconnects capped at 6 | `procgen_player.nim:22-24, 67-82, 116-123` |
No unbounded loop reached the episode path. The one `while true` (`procgen_player.nim:100`) is the
starter's own receive loop verbatim, exits on the game's `{"type":"final"}` or on a raised close, and
the docker smoke observed `all 1 player containers exited 0`.
The whole per-turn loop is `try`-free of raises: `decide.turn` catches `CatchableError` around the
transport (`decide.nim:294`) and the whole episode loop is wrapped (`server.nim:386, 449-456`).
**Batching:** the note calls for one batch per turn; `decide.nim:271-278` builds a `RequestBatch`,
`batch.post(...)` once, and calls `engine.client.curl.makeRequests(batch, …)` — the starter's batch path,
degenerating to a batch of one. There is no sequential-seat loop (there is one seat).

**Checklist item 6 — `num_agents`.**
`num_agents: 1` inside `game_config` for all three variants (`coworld_manifest_template.json:456`-block,
`487`-block, `518`-block) and inside `certification.game_config` (`:552`-block); **never** at a variant's
top level (asserted `tests/test_procgen_manifest.nim:51-54`). `len(certification.players) == 1`,
`len(certification.game_config.players) == 1` (`:77-83`). `tools/ci/docker_smoke.sh:106-152` enforces the
four invariants and cross-checks `SMOKE_SEATS`, all with the `SEAT-COUNT FAIL:` prefix. I grepped the
full docker-smoke job log (98945460661) for `SEAT-COUNT` — **zero hits**; the job printed
`game=procgen seats=1 config={… "num_agents": 1 …}` and `smoke OK: seats=1 … reason=complete`.

**Checklist item 7 — scripted baseline plays full episodes legally.**
`tests/test_procgen_engine.nim:22-42` runs a real scripted episode against the fixture config and asserts
`reason == "complete"`, `endRule == "gauntlet_complete"`. `:110-133` does the same for **all three**
variants. Bounded-orders: `tests/test_procgen_control.nim:45-61` runs 504 pseudo-random states × both
baselines and asserts `moves.len ∈ [1,6]`, `legalAlphabet(moves)`, empty `say`/`notes`, serialised
record ≤ 1024 B; `:62-74` seals the cog in and asserts a plan still comes back; `:76-102` asserts the
baselines' predictions agree with `stepFrame` and that a `pathfinder` plan never walks into a death it
projected. Tuning: swept by `tools/tune_baselines.nim` and re-checked in CI (F5/F6 note the two numeric
deviations).

**Checklist item 8 — LLM reply handling.**
Tolerant parse: `directives.nim:112-151` (`extractJsonObject`, byte-for-byte the starter's, balanced-brace
scan with a first-brace..last-brace fallback; markdown fences and prose survive — asserted at
`tests/test_procgen_control.nim:145-147`). Retry once: `decide.nim:252` (`attempt < 2`) with a distinct
`retryMs` deadline and a re-prompt suffix (`:263-266`). Fallback: `decide.nim:313-329` installs
`fallbackPlan`, increments `episode.seat.fallbackTurns`, writes a `fallback` chat record with a `cause`
from the closed set `{timeout, transport_error, throttled, parse_error, no_credentials, budget_guard}`,
and echoes the exact phrase `falling back` that phase 60 greps. The retry path deliberately says
`will retry` and never `falling back` (`decide.nim:301-304`). The fallback is countable in
`results.fallbackTurns` / `results.llmTurns` (`sim.nim:333-334`) and drives an `ekFallback` event
(`decide.nim:193-198`) that becomes a scrubber beat and a feed row.
Repair-never-reject: `directives.nim:84-110` (`sanitizeMoves`) uppercases, drops non-alphabet runes,
truncates to `framesPerTurn` on a rune boundary, and turns empty into `"."`;
`parsePlanOrder` (`:153-175`) raises only on a non-object payload — which is precisely what the retry and
then the scripted fallback exist for. Every repair sets `repaired`, which increments
`episode.seat.ordersRejected` (`decide.nim:288-289`). Test 24
(`tests/test_procgen_control.nim:117-174`) covers all eleven cases the note lists.
Fallback == pathfinder: `control.nim:10-17` and `tests/test_procgen_control.nim:104-115`.

**Checklist item 9 — rune-safe truncation.** Every capped path, traced:
| String | Cap | Cut |
|---|---|---|
| `moves` | 6 runes | `sanitizeMoves` → `truncateRunes` (`directives.nim:103-106`) |
| `say` | `MaxSayRunes = 24` | `truncateRunes` **first**, then the printable-ASCII/brace filter (`directives.nim:63-77`) |
| `notes` | `MaxNoteRunes = 160` | newlines collapsed, then `truncateRunes` (`directives.nim:79-82`) |
| whole reply | `MaxReplyBytes = 4096` | `boundedReply` backs off UTF-8 continuation bytes (`directives.nim:51-61`) |
| `PLAYER_PROMPT` | `MaxPromptRunes = 4000` | truncated on the player side (`procgen_player.nim:29-32, 40`) **and** on the server side (`server.nim:213-214`) |
| provider error bodies | `MaxFallbackDetailRunes = 200` | `truncateRunes` at four sites in `llm.nim:172, 180, 185-186` and again in `records.nim:19` |
| `max_tokens` cut-off text | 160 runes | `llm.nim:194` |
| `extractJsonObject` failure head | 160 runes | `directives.nim:147-148` |
| policy label | `MaxPolicyLabelRunes = 64` | `records.nim:38`, `server.nim:216-217` |
| `stopDetail` | `MaxStopDetailRunes = 200` | `cutRunes` (`sim.nim:71-78`, `sim.nim:339`) |
`truncateRunes` / `sanitizeSay` / `sanitizeNote` / `extractJsonObject` are byte-for-byte the starter's
(`diff src/ctf/directives.nim src/procgen/directives.nim` — only the doc comments differ). The
multi-byte test is `tests/test_procgen_control.nim:148-169`: 40 four-byte emoji on each of `say` and
`notes`, plus a >4096-byte all-emoji reply, asserting `bounded.len mod 4 == 0`.
End-to-end strict-UTF-8: `tests/test_procgen_replay.nim:73-118` fills every capped field to its cap with
emoji, writes a replay, runs `tools/replay_summary.py` over it and asserts the output parses as strict
JSON with `output.validateUtf8() == -1`. `tools/replay_summary.py:52-57` decodes every recorded string
with a **strict** `.decode("utf-8")`, so a byte-truncated codepoint would raise there.

**Checklist item 10 — manifest validates.**
`game.docs` = `{"readme":{"type":"text","value":…}, "pages":[…4 pages…]}` with ids `rules.md`,
`archetypes.md`, `training-seeds.md`, `protocol.md`, each `{id,title,content:{type,value}}` and each
value > 2 KB of inlined text. `tests/test_procgen_manifest.nim:126-133` additionally asserts the
training-seed page really prints all 128 published seeds. `game.protocols` carries **both** `player` and
`global`, each a `{"type":"uri","value":…}` object (`:100-105`). `$schema` present; no top-level
`version`; no `game.display_name`; `game.owner` present; `game.tags` absent; 5 top-level tags;
`episode_timeout_minutes: 20` at the top level. The platform's own reading is checked in
`ci.yml:173-202` via `coworld==0.1.43`'s `_load_template_manifest` → green in job 98945460474.

**Checklist item 11 — legible at 360 px.**
`client/replay_broadcast.html:1606-1620`: `.plate-name { … flex: 1 1 auto; min-width: 3.2em; overflow:
hidden; text-overflow: ellipsis }`. `:1747-1749`: `@media (max-width: 640px) { .plate .cog-alias,
.plate .gem-label { display: none; } }`, mirrored under `#stage.tiny` at `:1750-1751`. `relayout()`
(`:1506-1551`) iterates to a fixed point, sets `--hudscale = clamp(0.5, boardW/760, 1.6)`,
toggles `#stage.tiny` at `boardW <= 620`, and sets `--topband`/`--band`/`--hudscale` on
`document.documentElement` (`:1541, 1546-1547`) — i.e. on `:root`, which is where `--u` and
`#board`/`#endcard` read them (`:40-42, 96-98, 575-576`). `BOARD_W = 15, BOARD_H = 9` and
`BOARD_ASPECT = BOARD_W / BOARD_H` are constants (`:1321-1331`). Asserted at
`tests/test_procgen_viewer.nim:145-187`.

**Checklist item 12 — release order and scaffold.**
`coworld-release.yml`: Build the Coworld manifest (`:159`) → Certify locally (`:173`, with
`--timeout-seconds 300` at `:184`) → Upload the policies (`:216`) → Upload the Coworld (`:314`) → Put the
Coworld secret (`:410`). All three workflows present. `tools/ci/docker_smoke.sh` mode `100755`,
asserted present-and-executable at `ci.yml:221-229` and invoked by path at `:249`.
`tools/ci/policies.json` defines **four** policies on `/bin/procgen-player`: two `PLAYER_PROMPT`
champions (`procgen-cartographer`, `procgen-scrambler`) and two `PLAYER_SCRIPTED` fillers
(`procgen-pathfinder`, `procgen-scavenger`); champion #2 carries
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. I diffed both champion prompts against
design.md:718-741 and 746-767 — **byte-identical**. No `USE_BEDROCK` anywhere.
Note: `UPLOAD_REQUIRED` (design.md:1628) does not appear in the tree, but `coworld-release.yml` is
`workflow_dispatch`-only (`:24-25`) so there is no push-triggered upload job to gate.

**Checklist item 13 — viewer executes.**
- `wasm-viewer` green at the reviewed sha, `needs: docker-smoke`, and the
  `Load the bundle in a real browser` step **ran and passed** (log quoted in F22). Playwright pinned
  1.55.0 in both the npm install and the browser download (`ci.yml:351-355`).
- `data-replay-loaded="true"` is set on `<html>` in `static_replay.js:142`, in the `'loaded'` branch,
  which the Worker posts only **after** `ingestPacket()` has handed BroadcastCore the first frame
  (`static_replay_worker.js:126-131`) and `core.ingest` has synchronously called `draw()`
  (`broadcast_core.js:646-661`). `data-replay-error` is set in `showFailure()` (`static_replay.js:8-21`),
  reached from six distinct failure paths. Both markers are coworld-ctf's own — the diff against the
  starter shows them unchanged.
- **Playback opens at the game start.** This replay format records **no lobby frames at all**:
  `replay.frames` is appended only inside `applyPlan`'s frame loop (`server.nim:424-426`) and at level
  boundaries (`:444-445`), both strictly after `waitForLobby` has returned and the registration has been
  installed. `preScan` therefore has `snapshots[0]` = level 1's start state (`replay_runtime.nim:167-173`),
  `Playback.frame` initialises to 0 (`:293-295`), `seekStep` clamps `t < 0 → 0` (`:332-335`), and
  `chromeJson` emits `"st": 0` (`broadcast.nim:130`). The checklist's late-`gameStart` probe is not
  constructible here — the lobby is a wall-clock wait (`lobbyJoinTimeoutSeconds`, `server.nim:307-316`),
  not a frame count, so no `lobbyJoinTimeoutTicks` exists to inflate. Corroborated by the CI soak, which
  started at tick `0 / 193` and advanced. *(inferred from the code; the "large lobby, no seats" recording
  the checklist suggests is not expressible in this config schema.)*
- **MODULARIZE / bootstrap agree, and come from one starter.** `replay-viewer/config.nims:44-56` sets
  **no** `-s MODULARIZE` and **no** `-s EXPORT_NAME`, so the module is emitted non-modularized as
  `procgen_replay.js`; `static_replay_worker.js:8` declares `var Module = {}`, `:186-188` sets
  `Module.onRuntimeInitialized`, `:190` does `self.Module = Module`, and `:221` does
  `importScripts('./wire_constants.js', './broadcast_core.js', './procgen_replay.js')` — in that order,
  after the handlers are installed. Both files diff against `coworld-ctf`'s with **rename-only** changes.
  `-s ABORTING_MALLOC=1` and its verbatim comment survive (`config.nims:35-41, 51`).
  `tools/wasm_replay_smoke.cjs:110-113` injects `Module` as a function parameter for the same reason.
  The smoke's `loaded: true` is the positive evidence.

**Checklist item 14 — chrome provenance.** `chrome_common.js` byte-identical (F1/F8); page = starter +
appended block with only the listed removals (F3); `#viewpanel`/`#plates-r` and the six unused
`.beat-marker` kinds gone (F3, and `tests/test_procgen_viewer.nim:140-143`). Transport rules:
(a) `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement`
(`client/replay_broadcast.html:1541-1547`); (b) the appended block contains no `#transport` reference at
all (asserted `tests/test_procgen_viewer.nim:174-177`) and everything it adds rides the board region or
`#bannerlane` (the top band); (c) `#endcard { bottom: var(--band, 0px) }` (`:576`), shown with
`#endcard.on` (`:587`, added at `:1952`) and taken down whenever a frame arrives with `!s.over`
(`:1920`) — which `procgenFrame` evaluates on **every** frame (`:1959`), so scrub click, beat marker,
back/forward and keyboard all dismiss it; the renderer fixture asserts exactly this round trip
(`tools/ci/renderer_fixture.html:306-311`); (d) beats are `<button class="beat-marker <kind>">` with
`title` + `aria-label` and a click handler that calls `CTX.seekToFraction`
(`client/replay_broadcast.html:1805-1826`), built by `procgenBeat` — never `markBeat`, enforced by
`tests/test_procgen_viewer.nim:83-113`. CSS exists for exactly the seven emitted kinds
(`:1712-1719`), cross-checked against `BeatKinds` by `tests/test_procgen_viewer.nim:115-139` in **both**
directions.

**Checklist item 15 — every drawn string fits its frame.** `--strict-text-bounds` is on both smoke steps
(`ci.yml:383, 422`). The say bubble's box is sized from the **server's** cap:
`MAX_SAY_RUNES = WIRE.maxSayRunes || 24` → `SAY_CAP_SAMPLE` of that many `W`s, measured in the drawing
font (`broadcast_core.js:107-124, 563-572`); the band is **reserved whether or not anybody is speaking**
(`boardGeometry`, `:186-208`, reserves `band = sayBandFor(cell)` above the board and `barH` below it
before fitting the cell size), and the bubble is then clamped into the canvas on all four edges
(`:591-596`). The fixture drives the negative-y case explicitly and reports `72 drawn, 0 never_inside,
0 ellipsized`. See F22 for the `total: 0` on the bundle step.

**Resolution rules L1–L8 and the per-frame order.** I traced them against `src/procgen/sim.nim:142-218`
and `src/procgen/levels.nim:482-604`:
L1 `inc levelIndex` + read the pre-drawn plan (`sim.nim:147-148`, nothing drawn here — the plan comes
from `newEpisode` → `drawGauntletPlan`, `sim.nim:88`); L2 `newLevel` (`sim.nim:149-150` → `gen.nim:518-525`);
L3 initial state (`levels.nim:606-624`, `collectTotal = collectTotalFor(kind)` = 4 or 8, `lastDir = dR`);
L4 `startDist = max(1, distanceToExit())` over `progressCost` — the dig-and-push-inclusive table
(`levels.nim:180-190, 623-624`); L5 `ekLevelStart` (`sim.nim:154-157`); L6 the turn loop
(`sim.nim:184-189`); L7 outcome + `returnMilli` + `ekLevelEnd` (`sim.nim:164-182`); L8 `gauntletDone`
(`sim.nim:191-192`) then `ekGauntletEnd` + `ekEnd` (`server.nim:459-463`).
Per-frame steps 1–10 map onto `levels.nim` 1:1: `inc frame` + `lastDir` set even on a blocked move
(`:491-496`); intent via the single `applyAction` (`:295-369`); cog move with `miner`'s one-frame
dig-and-enter (`:505-511`) and horizontal-only push (`:318-326, 516-525`), `climber`'s ladder-only
vertical (`:309-314`); collect + exit unlock on the exact frame (`:375-387`); one physics hook per
archetype (`:546-577`) with hunters resting on `frame mod 3 == 0` (`:553`) and the bottom-to-top,
left-to-right fall scan (`:398-432`); hazards after physics (`:579-586`); exit (`:588-590`); progress
`bestDist` over the same BFS (`:592-597`); `foldState` per frame (`:454-480`, deliberately excluding
`levelTurn`); frame end / danger interrupt (`:599-603` + `sim.nim:213-218`).
`applyAction`, `passable`, `hunterStep`, `willFall` each have exactly one definition
(`levels.nim:143, 160, 232, 295`) and are called by the resolver, `seatViewJson` (`decide.nim:111-119`),
both baselines (`baselines.nim:63-206`), the validator (`gen.nim:151-196`) and the viewer pre-scan.

**Scoring.** `src/procgen/scoring.nim:16-43` is the note's formula verbatim, all integer `div`;
`unseenMilli` divides by the full unseen count including `unplayed` zeros (`sim.nim:224-232` +
`scoring.nim:31-40`); `scores[0] = float(unseenMilli)/1000.0` (`sim.nim:244-247`) — the only float in
the game; `win[0]` iff every unseen level ended `cleared` (`sim.nim:249-258`); `gapMilli` reported,
never scored (`sim.nim:236-237`, and it is absent from `scores`). `results.reason` and `results.endRule`
are Nim enums (`sim.nim:29-38`) whose full sets are asserted equal to the note's three/four at
`tests/test_procgen_engine.nim:181-197`, and the manifest's `results_schema` enums match
(`tests/test_procgen_manifest.nim:139-154`). The results key set is asserted **equal** to the manifest's
`results_schema` key set at `tests/test_procgen_engine.nim:58-67`; I confirmed both are the same 32 keys.

**Seed integrity.** `TrainSeeds` = 32 per archetype from bases `[1000,2000,3000,4000]`, 128 total, all
< 5000 (`seeds.nim:15-41`); `testRng = initRng(seed xor 0x7E57)` draws from `[100000, 2147483646]`
(`seeds.nim:20-21, 62, 70`), so the two sets are disjoint by construction; `drawGauntletPlan` is called
from `newEpisode` (`sim.nim:88`), which the server calls **before** `waitForLobby`
(`server.nim:320-321` then `:333`) and before any registration is installed; the play order is shuffled
but the split never is (`seeds.nim:86`); `levelCount ∉ {4,8}` raises in `sim_config.nim:93-97`. The
episode seed is randomised from `sysrand` unless the config pins one
(`src/procgen.nim:18-55`), specifically so a pinned seed cannot make the unseen half pre-computable.
Asserted at `tests/test_procgen_seeding.nim:12-108`, including "two episodes on the same seed played by
different baselines draw the same plan" (`:90-104`).

**The 49 numbered tests.** All 49 exist and are wired into `tests/shard_1..4.nim` and `tests/tests.nim`,
and `ci.yml:123-169` runs **every** `tests/*.nim` in debug and release independently of the shards. The
per-item deviations I found are F9 (49's fixtures, and 14's cross-target case), F10 (14/15 seed counts),
F13 (46's "emitted set"), F16 (13's budget), F17 (44's "exactly once"), F18 (29a/31's method) and
F24 (19's textual equality). Items 1–12, 16–18, 20–23, 25–28, 30, 32–43, 45, 47, 48 assert what the note
says they assert.

---

## Could not determine

- **Whether the runtime shape really came from `Metta-AI/cogame-snake-royale`** (builder deviation 1).
  That repo is not mounted in this sandbox. What I *can* say is in F1: it is not coworld-ctf's, and
  `src/procgen/runtime.nim` says so in its own header. What would settle it: a copy of
  `cogame-snake-royale/src/*/runtime.nim` and its `.nimble` to diff against.
- **Whether `digCost = 3` really loses the ladder by −0.010** (F5). The claim is a code comment about a
  sweep output. `ci.yml`'s `--sweep --check` step prints the whole matrix on every run, so the evidence
  exists; I did not extract the sweep table from the `test` job log. What would settle it: the
  `Sweep and verify the scripted-baseline tuning` step's stdout from job 98945460474.
- **Whether the worst-case episode tail stays inside 720 s when all three artifact PUTs time out**
  (F19). My arithmetic gives ≈ 712 s to the results write and ≈ 732 s to process exit in that
  pathological case; every path I could construct with responsive artifact URIs settles by ≈ 672 s. What
  would settle it: one hosted episode's pod-lifetime measurement, or a `wallClockBudgetSeconds` /
  `ShutdownGraceSeconds` change that makes the worst case unambiguous.
- **Whether `never_inside == 0` holds for LLM-authored text at 360 px in the real bundle**, as opposed to
  in the fixture. The bundle draws in a Worker, so `viewer_smoke.mjs` cannot instrument it (F22), and no
  CI replay can contain a `say` (docker_smoke runs without a key, and both baselines emit empty `say`
  by construction — `baselines.nim:169-172`). The fixture drives the *same* `broadcast_core.js` on a
  main-thread canvas at 360/640/1024 px and reports `0`. What would settle it directly: a recorded
  episode with a real `ANTHROPIC_API_KEY` played through the hosted bundle, which is phase 60's job.
- **`genFallbacks == 0` beyond 4800 seeds per archetype-difficulty** (F10). The wide sweep exists behind
  `SWEEP_WIDE=1` but is not run anywhere in CI. What would settle it: one
  `SWEEP_WIDE=1 nim r -d:release --path:src tests/test_procgen_gen.nim` run.
