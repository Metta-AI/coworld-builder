# r1 review — vizdoom-deathmatch

Repo: `Metta-AI/cogame-vizdoom-deathmatch` @ `3e49fa4201137a71614f001d72549f1a2c8379b1` (main)
Starter lens: `/workspace/starters/coworld-ctf` @ `e356bdd` (read-only)
Design note: `runs/2026-08-27-vizdoom-deathmatch/design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
CI evidence: run **33126418568** (`gh api .../actions/runs/33126418568` → `conclusion: success`,
`head_sha: 3e49fa42…`, `head_branch: main`); jobs `test` 98705620625, `docker-smoke` 98705621059,
`wasm-viewer` 98706075047, all `success`. Artifacts `smoke-replay` (results.json, replay.json,
summary.json) downloaded and read.

Files read: 41 source/test/config files in the fork, 24 in the starter (diffed after a
`ctf→vzd` rename normalisation), 3 workflow files, 2 CI job logs, 3 CI artifacts.

Findings are numbered F1…F29 as the brief asks. **Blocking** = falsifies a named checklist item.
Everything else is advisory no matter how consequential I think it is; where a non-blocking
finding is high-impact I say so and let the judge decide.

---

## Blocking

### F1 — No test records a replay and re-derives it from the bytes
- Where: `tests/test_vzd_replay.nim:1-9`; `tests/test_vzd_engine.nim:95-106`; grep over `tests/`
- Observed: `tests/test_vzd_replay.nim`'s own header says *"The record-then-re-derive proof is the
  hash chain, and it is asserted two ways: `tests/test_vzd_engine.nim` re-runs the episode in
  process and compares `gameHash` at every tick, and CI's `docker-smoke` job writes a real
  `.replay` … which the `wasm-viewer` job then re-simulates."* Tracing the first: the
  `determinism` suite at `test_vzd_engine.nim:96-106` calls `runEpisode(480, CertSeats)` **twice**
  and compares the two live hash chains. `runEpisode` (`:11-52`) drives `sim.step` directly from
  freshly compiled masks; it never constructs a `ReplayWriter`, never serialises bytes and never
  parses them back. A grep of the whole `tests/` tree for `ReplayWriter`, `parseReplayBytes`,
  `initReplayRuntime`, `advanceReplayFrame`, `checkReplayHash`, `writeInputMaskChange` returns
  **one hit, and it is a prose comment** (`test_vzd_replay.nim:8`). So what is asserted is
  *determinism of the live sim*, not *re-derivation from the recorded stream*.
  Tracing the second: `wasm-viewer` does re-simulate the smoke replay
  (`replay-viewer/vzd_replay.nim` → `src/vzd/replays.nim:457 checkReplayHash`), but
  `tools/ci/viewer_smoke.mjs` gates only on `data-replay-loaded`, on the clock/tick readouts
  advancing and on `canvas_text.never_inside`; a hash divergence surfaces as `#mmwarn` text and
  `vzd_mismatch_tick`, neither of which the harness reads. The job is green either way.
- Checklist item: **2 — Replay re-derivation.** "Replaying the recorded events through the sim
  reproduces the recorded per-tick state frame by frame … **A test asserts it.**"
- Why blocking: the property the whole static-viewer story rests on is untested in the repo and
  ungated in CI. The design's own test 26 (`design.md:1728-1730`, "record then re-derive, every end
  reason — `full_time`, `wall_clock` **and** `sim_fault` … identical hashes at every tick
  **including the stop tick**") is absent, and F7 below shows a concrete record type (`stop`) that
  is written but never re-applied — exactly the class of defect item 2 exists to catch.
- Category: correctness.

### F2 — The viewer draws model-authored text, and nothing measures it: `canvas_text.total == 0` and no renderer fixture
- Where: CI log job 98706075047 line "canvas text: 0 drawn…"; `client/replay_broadcast.html:4598-4602`;
  `src/vzd/global.nim:370-396`; `.github/workflows/ci.yml:317-347`; `tools/ci/` listing
- Observed: two classes of LLM-authored string reach the viewer.
  (a) `radio` — `dmDirectives` pushes a feed row per directive record carrying `d.radio`
  (`replay_broadcast.html:4598-4602`), capped at `MaxRadioRunes = 96`.
  (b) `say` — the shout is rendered as an in-world speech bubble, but **server-side**: the bubble
  is a sprite family in `src/vzd/global.nim:370-396` (`ShoutSpriteBase`, `ShoutObjectBase`,
  `ShoutBubbleZ`, `ShoutPadX`) composited into the board bitmap, not drawn by the page.
  Neither path uses canvas text: `grep -c fillText` is **0** in all three of
  `client/broadcast_core.js`, `client/chrome_common.js`, `client/replay_broadcast.html`.
  `tools/ci/viewer_smoke.mjs` is byte-identical to `templates/tools/ci/viewer_smoke.mjs` (`diff`
  clean) and instruments `CanvasRenderingContext2D.prototype.fillText/strokeText`
  (`viewer_smoke.mjs:358-362`), so on this renderer it can only ever report zero. The CI log
  confirms it: `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0
  ellipsized (--strict-text-bounds)`.
  `ci.yml` has exactly one `viewer_smoke.mjs` invocation (lines 342-347) and no second step;
  `tools/ci/` contains `check_gameversion.sh`, `docker_smoke.sh`, `next_coworld_version.py`,
  `policies.json`, `test_next_coworld_version.py`, `viewer_smoke.mjs` — there is **no
  `renderer_fixture.html`**. The design specifies one at `design.md:1803-1811` (test 43).
  Independently: `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY` (smoke log:
  "no ANTHROPIC_API_KEY: the game must complete on its scripted baselines"), and the resulting
  `summary.json` has `"radio": []` and `policyKinds` all `scripted` — so the one replay CI can
  produce carries zero radio lines, exactly the gap the checklist names.
- Checklist item: **15 — Every drawn string fits its frame.** "`total: 0` means the check covered
  nothing … and is not evidence of anything." and "A repo whose viewer draws LLM-authored text must
  therefore ship a **worst-case renderer fixture** … **a repo that draws model text and has no such
  fixture is a blocking `legibility` finding.**"
- Why blocking: the checklist states the consequence as a rule, and the tree matches its
  antecedent. There is no evidence in the repo or in CI that a full-cap 96-rune radio line, or
  eight simultaneous 10-rune bubbles, land inside their boxes at any width — least of all at 360 px.
- Category: legibility.

### F3 — The baseline tunables were not tuned by a working grid harness; the harness in the tree is the starter's and does not compile here
- Where: `src/vzd/baselines.nim:28-50`; `tools/tune_baselines.nim:1-45` (esp. `:29`); `tools/ci/` listing;
  `.github/workflows/ci.yml`
- Observed: `DefaultBaselineParams` (`baselines.nim:41-50`) ships `rusherHuntPx: 520,
  sentryHuntPx: 260, medPx: 360, postRotation: 2` with the comment *"The grid harness's pick, not a
  guess … `tools/ci/baseline_tuning.json` records the whole grid"* and the type doc
  (`baselines.nim:30-35`) points at `tools/tune_baselines.nim` and `tests/test_vzd_tuning.nim`.
  None of the three artefacts exists as described:
  * `tools/ci/baseline_tuning.json` — **absent** (`ls tools/ci/`).
  * `tests/test_vzd_tuning.nim` — **absent** (`ls tests/`).
  * `tools/tune_baselines.nim` — present but **byte-identical to the starter's**
    (`diff -q /workspace/starters/coworld-ctf/tools/tune_baselines.nim tools/tune_baselines.nim`
    → identical). It imports `ctf/[sim, control, directives, baselines]` at `:29` — a module path
    that does not exist in this repo — sweeps `holdline`/`sprayer` (`:3`), scores cells on
    hill-tick margin (`:20-24`), and writes `tools/ci/baseline_tuning.json` (`:33`). It cannot
    compile against `src/vzd`, and nothing compiles it: `ci.yml`'s `test` job runs `tests/*.nim`
    only (`ci.yml:117-119`), and no job invokes `tune_baselines --check`.
- Checklist item: **7 — Scripted baseline plays full episodes legally.** Second sentence: "The
  baseline's parameters were tuned with a grid harness, not guessed."
- Why blocking: the claim cannot be verified from the tree or from cited CI evidence; the only
  harness present is the starter's, sweeping different bots against a different objective.
  (The *first* half of item 7 is satisfied — see "Traced and consistent".)
- Category: correctness.

### F4 — `client/chrome_common.js` is not byte-identical to the starter's, and the change is not recorded in the design note
- Where: `client/chrome_common.js:14`, `:72`; `tests/test_vzd_viewer.nim:20-32`;
  `design.md:845`, `design.md:1225`
- Observed:
  ```
  $ diff /workspace/starters/coworld-ctf/client/chrome_common.js client/chrome_common.js
  14c14
  < //    both embedded pages (src/ctf/server.nim);
  ---
  > //    both embedded pages (src/vzd/server.nim);
  72c72
  <   var WIRE = window.CTF_WIRE || {};
  ---
  >   var WIRE = window.VZD_WIRE || {};
  ```
  Both files are 40 022 bytes; sha256 `5b243c5b…` (fork) vs `7ace7287…` (starter).
  The design note says the file is **"byte-for-byte (40 022 bytes)"** (`design.md:845`) and
  **"copied byte-for-byte … `tests/test_vzd_viewer.nim` pins its sha256 against the starter's
  file"** (`design.md:1225`). No named patch is recorded anywhere in the note.
  The shipped test does not pin the starter either: `test_vzd_viewer.nim:26-27` pins
  `secureHash` (SHA-**1**, `833a6d61…`) of the **fork's own** file and then asserts
  `"window.VZD_WIRE" in chromeCommon` / `"window.CTF_WIRE" notin chromeCommon` — i.e. it locks in
  the divergence rather than detecting it.
- Checklist item: **14 — Chrome is the starter's, not a lookalike.** "`client/chrome_common.js` is
  **byte-identical** to the starter's (`diff` it …); the only admissible change is a named,
  minimal patch recorded in the design note."
- Why blocking: the literal condition of the checklist item is false and the escape hatch ("a
  named, minimal patch recorded in the design note") is not taken — the note asserts the opposite.
  I record what is there; the patch is objectively minimal and is functionally required by
  `tools/gen_wire_constants.nim` emitting `window.VZD_WIRE`
  (`Dockerfile.replay-viewer:55` asserts `^window.VZD_WIRE={`), so whether it is a real defect or a
  design-note omission is the judge's call — but as written the item is falsified.
- Category: static-viewer.

---

## Non-blocking

Ordered roughly by consequence, not by checklist proximity.

### F5 — `results.frags` counts team kills, so `net` is `enemyKills − deaths` and a team kill is free for the killer
- Where: `src/vzd/roster.nim:613-631`; `src/vzd/sim.nim:1663-1666`; `src/vzd/deathmatch.nim:17-26`;
  `src/vzd/roster.nim:735`; `tests/test_vzd_sim.nim:160-166`; CI artifact `results.json`
- Observed, step by step:
  1. On any lethal hit `sim.nim:1665-1666` calls `sim.recordKill(shooterIndex)` **and then**
     `sim.recordTeamKill(shooterIndex, targetIndex)`. This is the starter's line pair, kept verbatim.
  2. `recordKill` (`roster.nim:613-619`) unconditionally does `inc sim.players[playerIndex].kills`.
     `recordTeamKill` (`roster.nim:621-631`) does `inc …teamKills` only when the two teams match.
     So `p.kills` = **enemy kills + team kills**.
  3. `netFor` (`deathmatch.nim:26`) returns `player.kills - player.teamKills - player.deaths`,
     which algebraically equals `enemyKills - deaths`. The `- teamKills` term cancels the team kill
     that step 2 already added; it is not a penalty.
  4. `deathmatchResultsJson` (`roster.nim:727,735`) publishes `frags = p.kills` and
     `net = p.kills - p.teamKills - p.deaths`.
- What the note says: `design.md:288-291` — `frags[c] = kills of ENEMY cogs by c (roster.nim
  recordKill)`, `net[c] = frags[c] - teamFrags[c] - deaths[c]`; `design.md:294-295` — "with a team
  kill charged to the killer as a lost frag … the only thing that stops friendly fire from being a
  free way to deny an enemy a frag"; `design.md:1640-1642` (test 4) — "a team kill calls
  `recordTeamKill` and **not** `recordKill`".
- Live evidence (CI artifact `results.json` from run 33126418568, seed 42, 1084 ticks):
  `frags = [3,2,0,0,2,3,1,0]` (Σ 11), `teamFrags = [0,1,0,0,1,0,0,0]` (Σ 2),
  `deaths = [2,3,0,0,2,3,1,0]` (Σ 11). Σdeaths (11) ≠ Σfrags + ΣteamFrags (13), and seat 1's
  reported `frags: 2` includes one team kill. Under the note's definition seat 1's `net` would be
  `1 − 1 − 3 = −3`; the shipped value is `−2`.
- Latent test failure: `tests/test_vzd_sim.nim:160-166` asserts
  `deaths == kills + teamKills` — the design's test 9 invariant. That assertion is **false whenever
  a team kill occurs**. It passes in CI only because the episode it runs is 240 ticks
  (`:153-155`) and produced no team kill; the 1080-tick certification episode produced two.
  Nothing here was loosened during this run — the assertion has been in the tree since the fork
  commit — so this is not a checklist-item-1 finding; it is a test that is green by luck.
- Consequence (inferred, not run): scores stay exactly zero-sum (`gameScorePermille` is
  antisymmetric and the margin is computed from the same counters both ways), so nothing about
  ranking breaks. What changes is the sign incentive the system prompt advertises
  (`src/vzd/llm.nim`, "FRIENDLY FIRE IS ON and killing a teammate costs you a frag") — in the
  shipped arithmetic it costs the killer nothing and the team one point, via the victim's death.

### F6 — The `directive` record's `view` block is dropped from every record by the 900-rune cap, and it carries `your_notes` while it exists
- Where: `src/vzd/directives.nim:398-412`; `src/vzd/server.nim:1965-1969`; `src/vzd/decide.nim:193-194`
- Observed: `server.nim:1965-1968` builds each turn's record with
  `directive.boundedDirectiveRecord(…, engine.seatViewNode(sim, seat, turnIndex, turnsPerGame))`.
  `boundedDirectiveRecord` (`directives.nim:398-412`) loops while the serialisation exceeds
  `MaxDirectiveRunes = 900`, and its shrink order is: shrink `note` while non-empty
  (`:400-402`), **else drop the view whole** (`:403-404`), else shrink `radio` (`:405-407`), else
  shrink `say` (`:409-411`). A seat view is a JSON object with 16 rays, a contact list, a
  three-mate block, a score block and (on a seat's first turn) fifteen zones — comfortably over
  900 runes on its own — so the first or second iteration always reaches `carried = nil`.
  Live evidence: of the **80** directive records in the CI replay's
  `summary.json` (8 seats × 10 turns), **0** carry a `view` key.
  Separately, `seatViewNode` always sets `result["your_notes"]` (`decide.nim:193-194`) and
  `server.nim:1968` passes that same node, so on any record small enough to keep the view the
  private note would ride along.
- What the note says: `design.md:1131` — the `directive` record carries
  `view` (the observation minus `your_notes`); `design.md:550-551` — "mirrored (minus
  `your_notes`) into the replay's `directive` record, so the replay explains every decision".
  The note also pins `MaxDirectiveRunes = 900` for the whole record (`design.md:617`); the two
  requirements are in tension in the note itself, and the code resolves it by always dropping the
  view.

### F7 — The `stop` record is written but is not applied on playback
- Where: `src/vzd/server.nim:1433-1434`, `:2068-2072`; `src/vzd/replays.nim:402-416`;
  `src/vzd/sim_state.nim:317-332`
- Observed: on the wall-clock stop the server writes
  `{"k":"stop","tick":…,"endRule":"wall_clock"}` (`server.nim:1433-1434`) and on a fault
  `{"k":"stop","tick":…,"endRule":<sim_fault|host_error>}` (`server.nim:2068-2072`).
  On playback, `replays.nim:411-415` routes **every** chat record whose first byte is `{` to
  `sim.pushFeedDirective(chat.message)`. `pushFeedDirective` (`sim_state.nim:317-332`) parses the
  record and returns early unless `node{"k"}.getStr() == "directive"` (`:326`). No other consumer
  of a `stop` record exists in `src/vzd` (grep: the only hits are the two write sites).
- What the note says: `design.md:936-940` — "The wall-clock stop is recorded as a load-bearing
  record, not inferred … written as one `stop` record **applied by the same proc on record and on
  playback**, and `tests/test_vzd_replay.nim` runs the record→re-derive check for every end reason".
- Inferred consequence (untested — see F1): a `deadline` or `fault` replay re-derives its masks and
  hashes up to the stop tick and then simply runs out of recorded data; the sim never enters
  `GameOver` at that tick, so the `gameover` event and the endcard would not fire in playback.
  `tools/replay_summary.py` does surface the record (`stops` array, `:132-133`), so the forensic
  path is intact; the viewer path is not.

### F8 — The pre-scan beat timeline can only ever contain `gameover`
- Where: `src/vzd/replays.nim:664-670`; `src/vzd/broadcast.nim:1017-1022`;
  `client/replay_broadcast.html:4702-4724`
- Observed: `replays.nim:664-668` is the starter's, unchanged:
  ```nim
  let scrubberBeats =
    if scan.sim.config.hill: @["gamestart", "hillflip", "tagout", "gameover"]
    else:                    @["steal", "return", "capture", "gameover"]
  if event["k"].getStr() in scrubberBeats: replay.beatEvents.add(event)
  ```
  `config.hill` defaults to `false` (`sim_config.nim:61`) and is not exposed by `config_schema`,
  so the `else` branch is taken. Of `steal`/`return`/`capture`/`gameover`, this game emits only
  `gameover` (F19). `beatEvents` is shipped once as `state["beats"]`
  (`broadcast.nim:1021-1022`), which is what `dmFrame` reads at
  `replay_broadcast.html:4704-4723` to place `kill`/`streak`/`lead`/`gamestart`/`gameover` markers
  up front.
- What the note says: `design.md:1205-1210` — the load-time pre-scan "records the per-tick frag
  margin series …, the kill/streak/lead/fallback beat ticks, and the lull spans … That is what lets
  the momentum graph and the scrubber beats draw at **full width on the first frame** instead of
  growing in."
- Consequence (inferred): beats still appear, but only through the live `dmEvent` path
  (`replay_broadcast.html:4489,4498,4516,4527,4555`) as playback passes each tick — i.e. exactly
  the "growing in" behaviour the pre-scan was specified to remove. Also affects the spoilers
  switch, which shows beats ahead of the playhead.

### F9 — The momentum graph plots remaining lives, not the frag margin, under a `FRAG LEAD` label
- Where: `src/vzd/replays.nim:543-562`; `client/replay_broadcast.html:1412`
- Observed: `scanTeamLead` is byte-identical to the starter's (`diff` of `replays.nim:535-700`
  after rename → identical). Its `else` branch (hill off, i.e. this game) is
  `result.add(sim.teamLivesRemaining(team))` (`:560-562`). The momentum series `leadSeries` is
  built from it (`:604, :656, :684`) and shipped as `state["lead"]` (`broadcast.nim:999-1009`).
  With `lives = 60` the plotted difference is `deaths(other) − deaths(you)`, not
  `teamNet[you] − teamNet[them]`. The label was re-mapped to `FRAG LEAD`
  (`replay_broadcast.html:1412`).
- What the note says: `design.md:1364-1366` — "Momentum graph — the starter's `#momentum` SVG
  **retargeted to the cumulative frag margin** across the game".

### F10 — The endcard's re-mapped 5-column header is fed 4-column rows, and the 4th column is a deleted mechanic's counter
- Where: `client/replay_broadcast.html:3610-3620` (header), `:3552-3570` (rows), `:1009-1013` (grid)
- Observed: the header emitted for both branches is now
  `<span>Cog</span><span>Frags</span><span>Deaths</span><span>Net</span><span>Acc</span>`
  (`:3619`) and the CSS grid is five columns
  (`grid-template-columns: 1fr … … … …`, `:1012`). The row builder `rowHtml` is the starter's: in
  `PB_MODE` (which is the mode this game runs in, F11) it emits **four** cells — `pcell`,
  `p.k`, `p.d`, and `<span class="n clstr">(tr.paint || 0)</span>` (`:3560-3568`).
  `tr.paint` is the team's painted-tile count, which is 0 in every deathmatch episode.
- Consequence: the "Net" column shows `0` for every row and the "Acc" column is never filled.
- What the note says: `design.md:1290` and `design.md:1367-1369` — the eight-row table sits under
  `Cog | Frags | Deaths | Net | Acc`.

### F11 — The scorebug is two team plates, not eight per-seat plates
- Where: `client/replay_broadcast.html:2033-2076`, `:4617-4655`; CI log job 98706075047 line 1822
- Observed: `ensureScorebug` iterates `activeTeams(s)` and appends **one plate per team**
  (`:2037-2076`). The game block's `renderPlates` (`:4617-4655`) then overwrites, per team,
  `#hill-<team>` with the team's net frags, `#lives-<team>` with the team's frag total and
  `#tags-<team>` with `<deaths> deaths · <n> up` plus a `↯` glyph if any seat on that side has
  fallen back. The viewer smoke's scorebug readout confirms two plates:
  `"-1 RED FRAGS 1 2 DEATHS · 3 UP … +1 BLUE FRAGS 2 1 DEATHS · 4 UP"`.
- What the note says: `design.md:1352-1354` — "**four plates in `#plates-l` (RED) and four in
  `#plates-r` (BLUE)**: each carries the seat's **real policy name** …, its in-game alias, a team
  colour chip, its `frags−deaths`, and a `↯` glyph on any seat that has taken a fallback";
  `design.md:1410-1411` (360 px rule 2) — "each plate keeps only `alias + name + net`".
- Note for the judge on checklist item 4: real player names **are** still reachable in the viewer
  through the inherited chrome — `teamName`/`teamHeadline` (`chrome_common.js:145-167`) headline
  the plate with the team's policy name(s), `#povBadge` shows
  `shortName(rosterName(s, s.pov))` (`replay_broadcast.html:2179`), and the endcard groups rows
  under `teamHeadline(pol)` (`:3585`). Item 4 is satisfied; the *shape* is not the note's.

### F12 — Vision cones are broadcast for every cog but nothing draws them on the board
- Where: `src/vzd/broadcast.nim:485-498`; `src/vzd/global.nim` (unchanged);
  `client/replay_broadcast.html:3212-3243`
- Observed: `broadcast.nim:485-498` adds `aim`, `cone`, `rng`, `bub` (plus `net`, `strk`, `dd`,
  `sf`, `sh`) to **every** roster row on every frame, with the comment naming it "the named edit …
  #2". No consumer draws them: `src/vzd/global.nim` — the board compositor — is byte-identical to
  the starter's after the rename sweep (`diff` → identical), so it has no cone draw family; and
  `client/broadcast_core.js` is likewise the starter's file with two rename lines (F16). The only
  cone actually painted is the **single POV** wedge inside the `#fpv-map` inset
  (`replay_broadcast.html:3212-3243`, `var here = m.here`), which is the starter's behaviour.
- What the note says: `design.md:1334-1336` (readout 2) — "every cog's 90° cone drawn as a
  translucent wedge, clipped by walls exactly as the sim clips it … This is the game made visible;
  without it a spectator sees eight dots wander"; `design.md:1010-1012` — the cones are broadcast
  "because the eight cones are the spectator's whole understanding of who can see whom";
  `design.md:1414-1415` (360 px rule 4) — "cone wedges drop to 45 % alpha".

### F13 — Deleted mechanics are gated off by a third loadout, not removed
- Where: `src/vzd/sim_types.nim:519-525`; `src/vzd/sim.nim:169-176`, `:206`, `:236-260`,
  `:4089-4093`, `:4112-4130`, `:4142-4156`; `src/vzd/paint.nim`; `src/vzd/global.nim`;
  `src/vzd/labels.nim`; `data/`; `src/vzd/sim_config.nim:58`, `:652-657`, `:824`
- Observed: `LoadoutDeathmatch = "deathmatch"` is added as a **third** loadout
  (`sim_types.nim:521-525`), `LoadoutCtf` stays, and `deathmatchLoadout()` (`sim.nim:169-176`)
  gates every deleted mechanic at its use site: pickup placement (`:206, :236-260`), grenade and
  barrier input (`:4089-4093`), the pickup/flag update block (`:4112-4130`), and the end-condition
  block (`:4142-4156`). Nothing was removed:
  * `src/vzd/paint.nim` is present and byte-identical to the starter's after rename.
  * `src/vzd/global.nim` is byte-identical after rename — the spray-cone, grenade, heart,
    pedestal and puddle draw families are all still there (`global.nim:304-334, 2224-2321,
    5363-5416`).
  * `src/vzd/labels.nim` differs by one comment line and still declares `"shield"`,
    `"shield carried"`, `"spray can"`, `"grenade"`, `"barrier"`, `"grenade barrage depth "`
    (`labels.nim:47-71, 183, 210`).
  * `data/` is the starter's directory **plus** three files. Every asset the note lists as deleted
    is present: `heart_{red,blue,green,yellow}.png`, `ped_*.png`, `paintgun*.png`,
    `paintbomb.png`, `shield.png`, `spraycan*.png`, `crew.png`, `soldier_*_crown.png`,
    `soldier_{green,yellow}*`, `rig_real/`.
  * `sim_config.nim:824` still reads a `loadout` key from the config JSON and `:652-657` accepts
    `ctf` / `paintball` / `deathmatch`. `config_schema` is `additionalProperties: false` and does
    not declare `loadout`, so the platform cannot reach the other two; a locally-supplied
    `COGAME_CONFIG_URI` could.
  Also unsplit: `src/vzd/{vision,combat,motion}.nim` do not exist; `src/vzd/sim.nim` is 4187 lines
  (starter 4102). And the `resident`/`visitor` regime field survives and is load-bearing —
  `broadcast.nim:921` ships `state["regime"]`, which is the only thing that turns `PB_MODE` on in
  the page (`replay_broadcast.html:1850`), and `PB_MODE` gates the whole appended game block
  (`:1903, :3308-3309`).
- What the note says: `design.md:855-865` — these mechanics and their art are "**deleted, not
  disabled**"; `design.md:828-830` — `sim.nim` splits into `vision.nim` / `combat.nim` /
  `motion.nim`; `design.md:857` — `paint.nim` deleted.
- The gating itself is sound: the smoke episode ran `complete` with the deathmatch branch taken
  and no pickup other than med kits. Two side effects worth naming: `sim.armSprayCans()`,
  `sim.updatePackTicks()`, `sim.updatePuddles()` and `sim.updateBarrage()` still execute every tick
  in the deathmatch path (`sim.nim:4133-4138`) — no-ops given the emptied spawn lists, but they run.

### F14 — The inherited page keeps all the deleted mechanics' chrome the note says to remove
- Where: `client/replay_broadcast.html:301-351` (`.squad-pip`, `.flagicon`), `:1083-1095`
  (`.ec-heart` incl. embedded green/yellow heart PNGs), `:2046-2058` (`.hillchip`, `.hcap`,
  `.pb-tags`, `.pb-sub`), `:3367-3375` (`onSteal`/`onReturn`/`onCapture` and their
  `… HEART TAKEN` banners), plus 13 `perk` and 1 `handicap` occurrences
- Observed occurrence counts in the shipped page: `hillchip` 4, `hcap` 4, `pb-tags` 3, `pb-sub` 3,
  `flagicon` 7, `ec-heart` 8, `squad-pip` 13, `.squad` 16, `perk` 13, `handicap` 1.
  They are unreachable — `dmEvent` swallows `steal`/`return`/`capture`/`hillflip`/`tagout`/`paint`/
  `spray`/`tag`/`heal` by returning `true` before the inherited switch sees them
  (`:4560-4570`) — but they are present.
- What the note says: `design.md:1251-1268` — "**Elements removed** (exactly these, and the JS that
  feeds them)", naming `.hillchip`, `.hcap`, `#pb-regime`, `.pb-tags`, `.pb-sub`, `.flagicon`,
  `.ec-heart`, `.squad-pip`, `.squad`, and the perk/handicap badges. Only `#pb-regime` is gone.
- Against checklist item 14 this is over-inclusion, not a rewrite: the page **is** the starter's
  page (`test_vzd_viewer.nim:34-47` asserts the banner sits past byte 200 000 and the tail contains
  exactly one `<style>` and one `<script>`), and every diff above the banner corresponds to a
  removal or re-mapping the note lists. So item 14's *page* clause holds.

### F15 — The endcard-label test is an enumerated allow-list, not the note's zero-match forbidden-vocabulary grep, and it never reads the built bundle
- Where: `tests/test_vzd_endcard_labels.nim:24-97`
- Observed: the test asserts eight specific replacement strings appear exactly once
  (`:25-58`) and that a hand-picked list of ~14 old strings is absent (`:61-83`). It reads only
  `client/replay_broadcast.html` (`:13`).
- What the note says: `design.md:1300-1303` (and test 39, `design.md:1781-1782`) — greps **the
  built `index.html` and `broadcast_core.js`** for the vocabulary list `Lives`, `LIVES`, `Clstr`,
  `Cap<`, `flag`, `heart`, `paint`, `hopper`, `hill`, `spray`, `grenade`, `Tags`, `tagout` outside
  comment blocks and asserts **zero** matches. The shipped page would not pass that grep (F14).

### F16 — `broadcast_core.js` is the starter's file, and `drawStreakGlow` does not exist anywhere
- Where: `client/broadcast_core.js:49`, `:268`; `client/replay_broadcast.html:4431-4460`
- Observed:
  ```
  $ diff /workspace/starters/coworld-ctf/client/broadcast_core.js client/broadcast_core.js
  49c49  <   (window.CTF_WIRE && …)   >   (window.VZD_WIRE && …)
  268c268 <   … src/ctf/sim.nim) …     >   … src/vzd/sim.nim) …
  ```
  Both files are 62 123 bytes. `drawEyesStrip` exists, but in the appended HTML block
  (`replay_broadcast.html:4431-4460`); there is no `drawFragbug` (the fragbug is DOM,
  `:4374-4392`); and `grep -rn drawStreakGlow` over the repo returns **zero hits**.
- What the note says: `design.md:1240-1250` — `broadcast_core.js` "is forked … Deleted: every flag,
  paint, hill, spray and grenade draw call. **Added: `drawEyesStrip`, `drawFragbug`,
  `drawStreakGlow`**"; `design.md:1330-1332` (readout 1) — "a cog on a streak of ≥ 3 gets a soft
  amber halo". No halo is drawn; `#eyes .dm-eye.pov` (`:4191`) is the only amber outline added,
  and it marks the POV seat, not a streak.

### F17 — The nano-banana helmet is a viewer-side `<img>` overlay, not a `rig_art.nim` composite
- Where: `client/replay_broadcast.html:4301-4304`, `:4477`; `src/vzd/rig_art.nim`; `data/`
- Observed: `helmImg(team)` emits `<img class="dm-helm" src="<DM_BASE>/helm_<team>.png">`
  (`:4301-4304`) and it is used only in the `#eyes` thumbnail caption (`:4477`). `skullImg()`
  (`:4297-4300`) is used only in the kill-feed badge (`:4511`). `src/vzd/rig_art.nim` differs from
  the starter's by 8 lines of rename only, and neither `helm_` nor `glyph_frag` appears in it
  (grep). The board cogs are the starter's kits, uncomposited.
  The art itself is real: `data/helm_red.png` and `helm_blue.png` are 128×128 8-bit RGBA PNGs
  (24 483 / 24 486 bytes) and `data/glyph_frag.png` is 64×64 RGBA (6 235 bytes); all three are
  copied into the bundle and asserted present by `Dockerfile.replay-viewer:40-41, 70-72`.
  `scripts/art/source/marines_sheet.png` and `scripts/art/split_cog_sheet.py` are both committed.
- What the note says: `design.md:1391-1395` — "the helmets are composited by the **existing**
  `rig_art.nim` plumbing (same masters, pivots, scale, `SoldierRotations` facings)".

### F18 — `MaxReplyBytes = 4096` is enforced as a rune cap, after the whole body is read
- Where: `src/vzd/decide.nim:534`; `src/vzd/sim_types.nim:538`
- Observed: `extractJsonObject(text.truncateRunes(MaxReplyBytes))`. `truncateRunes` cuts on rune
  boundaries, so the effective cap is 4096 **runes** — up to 16 384 bytes for 4-byte code points.
  `text` is the full decoded provider response; nothing bounds the read itself.
- What the note says: `design.md:615` — "whole reply | **bytes** | ≤ 4096 read from the provider
  before parsing"; `design.md:1699` (test 19) — "caps the read at 4096 bytes". No test covers it
  (`tests/test_vzd_control.nim:237-274` covers `say`/`radio`/`notes`/record caps only).

### F19 — The broadcast event vocabulary is nine kinds, not the note's sixteen-plus-`end`
- Where: `src/vzd/broadcast.nim` (`grep '"k": "'`); `tests/test_vzd_events.nim:15-40`
- Observed: `stepEvents` can emit, in a deathmatch, `phase`, `gamestart`, `gameover`, `kill`,
  `respawn`, `hit`, `pickup`, `streak`, `lead` — nine. `turn`, `order`, `say`, `radio`,
  `fallback`, `shot`, `spot`, `lost` and `end` are **never** emitted as broadcast events
  (`turn_start`/`fallback`/`streak`/`lead` were added to the *tier-2* `SimEventKind` enum instead,
  `events.nim:40-43`, which is the `COGAME_EVENTS_URI` stream, not the viewer's). The page's
  fallback feed row and fallback beat are derived from the replay's `directive` records instead
  (`replay_broadcast.html:4580-4596`), and the `#killfeed` shout/radio rows come from the same
  place — so the effect is largely covered, by a different mechanism.
  `tests/test_vzd_events.nim:29-32` asserts each of the nine is emitted; it never asserts the
  emitted set is exactly a closed list.
- What the note says: `design.md:1138-1152` — "**A closed enum of sixteen kinds**" plus `end`;
  `design.md:1786-1788` (test 41) — "the set of kinds `stepEvents` can emit **equals exactly** the
  sixteen listed".

### F20 — Driver details that differ from the note's table
- Where: `src/vzd/control.nim:467-503`, `:507-535`, `:582-614`
- Observed:
  * No aim sweep. The note's `hunt` "on arrival … sweeps ±32 brads around the approach bearing" and
    `hold` "sweep ±32 brads around the bearing to the map centre" (`design.md:753-754`). The code's
    aim chain (`:582-607`) is: known enemy in range → `face` → `retreat`→centre → standing-on-goal
    → centre, then anchor. There is no oscillation term anywhere in `compileMask`.
  * `driverResult` (`:507-535`) can return `unknown_target`, `dead`, `firing`, `chasing`,
    `holding`, `arrived`, `no_route`, `moving` — **never `respawned`**, which the note lists in the
    `result` enum (`design.md:593-594`).
  * `teammateInCorridor` (`:467-503`) is a newly written perpendicular-distance test comparing
    `cross²` against `PlayerHalf² · lenSq`; the note says it reuses "the starter's own corridor
    test" (`design.md:768`). The predicate is correct for a `PlayerHalf`-radius disc and
    `tests/test_vzd_control.nim:99-131` exercises it over 500 geometries; only the provenance
    claim is wrong.
  * `driverResult` reports `firing` on a known, in-range, `ticks_ago == 0` enemy without checking
    line of sight or aim error (`:527-529`), so the seat can be told `firing` on a turn where the
    trigger rule (`:624-645`) refuses to press `A`.

### F21 — `contacts` lists all teammates unconditionally and carries at most one memory row
- Where: `src/vzd/egoview.nim:151-183`
- Observed: the contact loop skips a target only when `not sameTeam and not
  sim.playerVisibleTo(cogIndex, other)` (`:158-159`). A living **teammate** is therefore emitted as
  a `clAlly` row regardless of cone, bubble, wall or distance. That is consistent with documented
  divergence 3 ("teammates are not fogged", `design.md:953-957`) but not with the note's own
  sentence for `contacts` (`design.md:525-527`): "one row per entity the cog can legitimately see
  right now (inside the cone with a clear line, or inside the 90 px bubble)".
  The memory block (`:175-183`) adds **one** row, from the single `ControlState.knownEnemy`;
  the note says "**every** enemy this cog saw within the last `HuntMemoryTicks = 72` ticks"
  (`design.md:525-527`).
  Med-kit rows are correctly fog-filtered through `fovVisibleAt` (`:187`).

### F22 — `rusher` shouts "on it" every hunting turn, not only on the change
- Where: `src/vzd/baselines.nim:181-191`
- Observed: `order.say = "on it"` is set unconditionally inside the `if huntable:` branch — there
  is no comparison against the previous turn's intent. The sim's `ShoutCooldownTicks = 24`
  throttles the in-world bubble, but the string is re-emitted into every directive record.
  Live evidence: the CI replay's `summary.json` carries 21 shouts, all `"on it"`.
- What the note says: `design.md:785-786` — "`say` = `"on it"` **on the turn the intent changes to
  `hunt`**".

### F23 — The map block is re-sent every turn to any seat whose LLM reply has not yet parsed, and the terrain word is recomputed per call
- Where: `src/vzd/decide.nim:180-183`, `:550`; `src/vzd/server.nim:1965-1968`;
  `src/vzd/zones.nim:93-121`
- Observed: `seatViewNode` includes `sim.mapJson(cogIndex)` when
  `not engine.mapSent[seat]` (`decide.nim:180-183`). `mapSent[seat] = true` is set **only** in the
  successful-parse branch (`decide.nim:550`), so a seat that times out, or a scripted seat (which
  never enters that branch), keeps `mapSent = false` forever. `server.nim:1968` calls
  `seatViewNode` for **every** seat each turn to build the directive record, so `mapJson` — and
  with it `zoneTerrain` → `zoneWallPermille`, an 8 px lattice scan of `sim.wallMask` per zone
  (`zones.nim:93-112`), 15 zones per call — runs 8×/turn for the whole episode.
- What the note says: `design.md:513-517` — "**The map, once, at its first turn**";
  `design.md:880-882` — "the **load-time** terrain word per zone". No caching exists; the value is
  a pure function of the installed map, so correctness is unaffected. ~12 k lattice reads per call,
  ~2.4 M per episode: not a timing risk.

### F24 — `results.map` reports the config's `mapPath`, not the resolved map
- Where: `src/vzd/roster.nim:779`
- Observed: `results["map"] = %sim.config.mapPath`. For the `pool` variant that is the literal
  string `"pool"`, not the pool entry the seed drew. (CI's arena episode reports `"arena"`, which
  happens to be both.) The resolved geometry is still pinned into the replay as `mapSpec`
  (`test_vzd_replay.nim:106-108` asserts it is a non-empty JSON object).
- What the note says: `design.md:911-912` — "`results.map` records the **resolved** map name".

### F25 — `replay_summary.py`'s `tickCount` is the file's byte length
- Where: `tools/replay_summary.py:165`
- Observed: `"tickCount": len(data)`, where `data` is the whole file's bytes. CI evidence: the
  summary reports `tickCount: 40874` for a replay of exactly 40 874 bytes and 1 084 ticks
  (`results.finalTick: 1084`). The line is inherited verbatim from the starter
  (`diff` shows this line unchanged).
- What the note says: `design.md:1092-1095` lists `"tickCount":…` in the summary contract. Nothing
  in CI or the phase-60 recipe reads it, so nothing catches it.

### F26 — The player registrar is byte-identical to the starter's, so its docs and log line still say `holdline | sprayer`
- Where: `src/vizdoom_deathmatch_player.nim:11`, `:14`, `:69`, `:72`
- Observed: `diff /workspace/starters/coworld-ctf/src/paintball_player.nim
  src/vizdoom_deathmatch_player.nim` → **identical**. Lines 11/14 document
  `PLAYER_SCRIPTED  holdline | sprayer` and "A seat that sets neither is `holdline`"; the startup
  echo at `:69-72` prints `baseline=holdline`.
  Behaviour is nonetheless correct: `PLAYER_SCRIPTED` is passed through verbatim in the
  registration blob (`:42-45, :116`), and the server's `parseBaseline`
  (`src/vzd/baselines.nim:52-58`) maps `"sentry"|"post"|"guard"` → `blSentry` and **everything
  else, including `"holdline"` and the empty string, → `blRusher`**, which is what
  `tests/test_vzd_control.nim:150-154` asserts. The re-send window and the exit-0-on-dead-socket
  behaviour the note calls for are inherited intact.
- What the note says: `design.md:392-404` — the player is `paintball_player.nim` "forked with **no
  behaviour change**", sending `"scripted":"rusher"|"sentry"|null`.

### F27 — `llm.nim` keeps the starter's single haiku candidate
- Where: `src/vzd/llm.nim:71-87`
- Observed: `BedrockModels = @["us.anthropic.claude-haiku-4-5-20251001-v1:0"]` with the starter's
  comment explaining that sonnet-4-5 was removed after every call timed out. `tryNextBedrockModel`
  (`:89`) therefore always fails over to nothing, which is what makes the "429 with no other
  candidate skips the retry" path (`decide.nim:566-572`) fire for every throttle.
- What the note says: `design.md:413-417` — candidates in order are haiku-4-5 **then**
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. The behaviour of the fork matches the starter,
  not the note.

### F28 — `wasm_replay_smoke.cjs` ships without fixtures and is never invoked; `label_manifest.txt` and the label-contract test are absent
- Where: `tools/wasm_replay_smoke.cjs:20-22`; `tests/` listing; `.github/workflows/ci.yml`
- Observed: the script takes `argv[3]` as a replay path (`:21`); there is no `tests/replays/`, no
  `tests/fixtures/` and no `*.bitreplay` anywhere in the repo (the starter ships both directories).
  `ci.yml` never mentions `wasm_replay_smoke`. `tests/label_manifest.txt` is absent while
  `src/vzd/labels.nim` still declares the full ctf/paintball vocabulary (F13).
- What the note says: `design.md:1812-1814` (test 44) — "the starter's headless-node run of the
  *exact emitted* wasm module **against the committed fixtures**, kept"; `design.md:1738-1739`
  (test 29) — every committed fixture carries the current `GameVersion` (vacuous with no
  fixtures); `design.md:1783-1785` (test 40) — the label manifest.

### F29 — Tests named in the design note that are absent, plus one that is a tautology
- Where: `tests/` listing; `tests/test_vzd_sim.nim:124-136`, `:168-184`
- Observed. Present and substantive: `test_vzd_sim`, `test_vzd_scoring`, `test_vzd_control`,
  `test_vzd_engine`, `test_vzd_replay`, `test_vzd_manifest`, `test_vzd_viewer`,
  `test_vzd_endcard_labels`, `test_vzd_events`. Absent: `test_vzd_determinism.nim` (note test 12),
  `test_vzd_tuning.nim` (20). Absent as behaviours: the stall test (23), the budget-guard and
  rate-guard **episode** tests (24, 25 — only the `effectiveSpacingMs` unit checks exist,
  `test_vzd_control.nim:276-290`), the record→re-derive test (26, see F1), the
  `replay_summary.py`-over-a-real-replay UTF-8 test (28 — CI does run the script on the smoke
  replay, `ci.yml:196-209`, which covers most of it), and the `coworld validate_upload_manifest`
  CI step (32).
  Partially covered: the float grep (12) survives as `test_vzd_sim.nim:168-184` but covers only
  `deathmatch.nim` and `zones.nim` — **not `motion.nim`** (which does not exist, F13) — and there
  is no byte-identity assertion on `vision.nim`/`combat.nim`'s inherited float maths and no
  assertion that `egoview.nim`'s output never reaches `gameHash`.
  **Tautology:** `test_vzd_sim.nim:124-136` ("the model and the viewer read the SAME walls")
  computes
  ```nim
  narrow = sim.marchRays(cogIndex, 3, sim.visionRange())
  wide   = sim.marchRays(cogIndex, 3, sim.visionRange())
  ```
  — identical arguments — and then asserts they agree. It never calls `firstPersonJson` and never
  compares 16 columns against 96, which is what the note's test 7 asks
  (`design.md:1650-1653`). The *code* does share one march (`broadcast.nim:609-613` calls
  `sim.marchRays`), so the property holds by construction; the test does not demonstrate it.

---

## Traced and consistent

- **Checklist 1 — CI green, no test loosened.** `gh run list -R Metta-AI/cogame-vizdoom-deathmatch
  --branch main -w ci.yml` → run **33126418568**, `success`, on `3e49fa42…`; all three jobs green.
  `git log -p 02f0851..HEAD -- tests/` (the fork commit onward) shows four test hunks: an unused
  `strutils` import removed; a fixture join-name fix (`vzd_helpers.nim:78-83`, joining as `Cog<N>`
  because `closedRoster` validates the slot's configured name); a `mapSpec` assertion **tightened**
  from `getStr().len > 0` to `kind == JObject and len > 0`; and two new viewer assertions. No
  deleted assertion, no `skip`/`xfail`, no widened tolerance, no test file removed.
  One scope change: `test_vzd_manifest.nim:143-157` narrowed the rate-floor budget assertion from
  `allGameConfigs()` (variants + cert fixture) to variants only, with a compensating test added at
  `:159-163`. The design's own wording is "for every **variant**" (`design.md:1752`), and the cert
  fixture at `turnSpacingMs: 0` / `wallClockBudgetSeconds: 240` genuinely cannot satisfy the
  variant formula, so this reads as a correction rather than a loosening — flagging it so the judge
  can decide.
- **Checklist 3 — Static viewer.** `coworld_manifest_template.json` →
  `game.replay_viewer = {"bundle": "static-replay-viewer"}` under `game`, with no top-level
  `replay_viewer` (`test_vzd_manifest.nim:85-88` asserts both). `tools/build_replay_viewer.sh`
  exists, is mode **100755**, and `ci.yml:249-273` asserts the exec bit and invokes it by path.
  The bundle contacts nothing but its own origin: `static_replay.js` and `static_replay_worker.js`
  are byte-identical to the starter's after rename. No `/client/replay` path is declared to the
  platform; the only occurrences are the local dev-server chrome (`broadcast_core.js:196`,
  `league_replayer.html:402-447`) and a `coworld-release.yml:211` error message.
- **Checklist 4 — Both name spaces.** Agent side: `seatViewNode` (`decide.nim:108-204`) names cogs
  only through `sim.cogAlias` — `you`, `contacts[].id`, `team_net[].id`, `score.your_team[].id`;
  no `players[].name` reaches it. `showPlayerLabels: false` in all three game_configs. Alias
  derivation is the named edit at `sim.nim:297-310` (`slotIdentityIndex` at `cogsPerTeam <= 1`),
  asserted distinct 8-ways by `test_vzd_sim.nim:12-29`; the CI artifact confirms
  `RED-alpha…BLUE-delta`. Viewer side: real names come back through
  `chrome_common.js:129-167` (`teamPolicies`/`teamName`/`teamHeadline`), `rosterName` (`:371-377`),
  `#povBadge` (`replay_broadcast.html:2179`) and the endcard's `ec-pol` headline (`:3585`), and
  `results.names` carries them (CI artifact). Shape differs from the note — see F11.
- **Checklist 5 — Degrade never hang.** Every wait in the decision path is bounded and I traced
  each: the rate-floor sleep is `sleep(min(spacingMs, spacingMs - since))`
  (`decide.nim:472-475`), bounded by `effectiveSpacingMs ≤ 17 143 ms`; the batch is
  `engine.client.curl.makeRequests(batch, max(1, deadlineMs div 1000))` (`:517-518`) with
  `deadlineMs ∈ {attempt1Ms 8000, retryMs 3000}`; the attempt loop is `while open.len > 0 and
  attempt < 2` (`:489`) with a monotonic budget check *before* each attempt
  (`:492-497`, `turnBudgetMs = 12 000`); the throttle path breaks out (`:566-572`); the rate guard
  never sleeps, it converts the excess seats to `rusher` (`:423-434, :457-466`). Outside the turn:
  `wallClockBudgetSeconds = 660` hard stop at `server.nim:1415-1436`, `lobbyJoinTimeoutTicks`
  2400/600, and the frame limiter (`server.nim:1932`). No unbounded loop and no blocking read in
  the fork's new code.
  Arithmetic, worst case: the sleep holds batch *starts* `spacingMs` apart, so the turn period is
  `max(17.143 s, ≤ 11 s of calls)` = 17.143 s → 24 × 17.143 = 411 s, plus ≤ 100 s lobby cap, ~4 s
  sim, ~15 s settle = **530 s** < 660 s stop < 720 s (60 % of 1200). The budget guard
  (`decide.nim:409-417`) uses `max(turnBudgetMs, spacingMs)` — the design's one named edit — so it
  fires at `elapsed > 624 s`, before the stop.
  `tests/test_vzd_manifest.nim:139-163` pins `wallClockBudgetSeconds ≤ 660` for all three configs
  and `24 · effectiveSpacingMs(8)/1000 + 134 ≤ 660` for both variants; the CI episode finished in
  46 s wall clock (smoke log 23:30:41 → 23:31:27).
  **One parallel batch per turn:** `decide.nim:500-518` builds one `RequestBatch` over all open
  seats and issues `makeRequests` once; there is no per-seat request loop.
- **Checklist 6 — `num_agents`.** Present in `variants[arena].game_config`,
  `variants[pool].game_config` and `certification.game_config`, all `8`; absent at every variant
  top level; `config_schema.num_agents` is `{integer, minimum 8, maximum 8, default 8}`.
  `tools/ci/docker_smoke.sh` is the template with only the three substitutions applied
  (`diff` vs `templates/tools/ci/docker_smoke.sh` shows six lines, all substitution) and carries
  the four `SEAT-COUNT FAIL:` invariants at `:106-152` plus the `SMOKE_SEATS` second declaration
  (`:54, :141-152`). **`grep -n "SEAT-COUNT" <docker-smoke job log>` → zero hits**; the log reads
  `game=vizdoom-deathmatch seats=8 …"num_agents": 8…` and `smoke OK: seats=8 … reason=complete`.
  `tests/test_vzd_manifest.nim:19-54` re-asserts all four in-process.
- **Checklist 8 — LLM reply handling.** Tolerant parse: `extractJsonObject` (inherited,
  fence- and prose-tolerant) then `parseSeatDirective` (`directives.nim:256-344`), which repairs
  rather than rejects — unknown intent → `intHunt` (`:113-127`, plus a synonym table), unresolvable
  `at` → keep `to` and set `unresolved` (`:319-325`), `to` clamped (`readPoint`), the starter's
  `cogs:[…]` single-entry form accepted (`flatOrderNode`, `:215-232`), a `say`-only reply usable
  (`fromReply` stays false so the caller keeps the standing order, `repairMissingOrder`
  `:289-311`). Raises only on a non-object (`:284-285`). **Retries exactly once**: `while open.len
  > 0 and attempt < 2`. **Fallback recorded**: `fallbackRecord` on every failure
  (`decide.nim:494-496, 559-560, 586-587`) with `cause ∈ {timeout, transport_error, parse_error,
  throttled, no_credentials, budget_guard, rate_guard}`, a `Fallback` tier-2 event, the phrase
  `falling back` echoed to the **game** log (`:590`), and `results.fallbackTurns` /
  `results.ordersRejected` (`server.nim:1963`, `decide.nim:541-544`). All of it asserted by
  `tests/test_vzd_control.nim:156-274`.
- **Checklist 9 — Rune-safe truncation.** `sanitizeSay` / `sanitizeRadio` (`directives.nim:104-110`)
  / `sanitizeNote` all end in `truncateRunes`; `fallbackRecord` truncates `detail` at
  `MaxFallbackDetailRunes` (`decide.nim:219`); `results.stopDetail` uses `runeSubStr`
  (`roster.nim:788-790`); `registerRecord` truncates `policy` (`decide.nim:232`);
  `boundedDirectiveRecord` only ever cuts *fields*, never the serialised string
  (`directives.nim:398-412`). Tests feed a 4-byte emoji sitting exactly on every cap and assert
  `validateUtf8(...) == -1`: `test_vzd_control.nim:237-274` and `test_vzd_replay.nim:34-79`.
  CI additionally re-parses the real replay's summary under a strict UTF-8 loader
  (`ci.yml:196-209`, green).
- **Checklist 10 — Manifest validates.** `game.docs` is
  `{"readme":{"type":"text","value":…6189 chars}, "pages":[rules.md, observation.md, protocol.md]}`
  with every `content.value` > 5 000 chars; `game.protocols` carries **both** `player` and `global`
  as `{"type":"uri","value":"https://…"}` objects. `game.config_schema` is
  `additionalProperties: false`, `required: ["tokens","players"]`, and all three array properties
  carry `minItems`/`maxItems` 8/8; no `game_config` contains a literal `tokens`.
  `game.results_schema` is closed and its 30 property names **exactly** match the 30 keys
  `deathmatchResultsJson` emits — verified two ways: `test_vzd_scoring.nim:68-83` sorts and compares
  both key sets, and the CI `results.json` artifact has exactly those 30 keys.
  `reason` enum `[complete, deadline, fault]`, `endRule` enum
  `[full_time, wall_clock, sim_fault, host_error]`. `game.tags` absent, top-level `tags` has 5,
  `episode_timeout_minutes: 20` at top level.
- **Checklist 11 — Legible at 360 px.** `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow:
  hidden; text-overflow: ellipsis }` at `replay_broadcast.html:4092-4097`, applied to the plate
  the game actually renders (`:2050`, the `PB_MODE` branch). Labels hidden under `.tiny`
  (`#stage.tiny` at `boardW <= 620`): `:4134-4136` hides `.pb-tags` and the frag/lives labels,
  `:4211-4213` collapses `#eyes` to chips, `:4156-4158` shrinks `#fragbug` and drops the margin.
  `tests/test_vzd_viewer.nim:140-165` asserts each.
- **Checklist 12 — Release order and scaffold.** `coworld-release.yml` runs
  "Build the Coworld manifest" (`:159`) → "Certify locally" (`:173`, with `--timeout-seconds 300`
  at `:184`) → "Upload the policies" (`:216`) → "Upload the Coworld" (`:314`) → "Put the Coworld
  secret" (`:410`), in that order. All three workflows present; both
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are mode 100755.
  `tools/ci/policies.json` has **four** entries — two `PLAYER_PROMPT` champions (`vzd-pointman`
  1 498 chars, `vzd-crossfire` 1 418 chars, different texts) and two `PLAYER_SCRIPTED` fillers
  (`rusher`, `sentry`) — all on `/bin/vizdoom-deathmatch-player`, all carrying
  `PLAYER_POLICY_LABEL`, with champion #2 carrying
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` and champion #1 carrying none.
  The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files
  returns nothing. `tests/test_vzd_manifest.nim:182-217` re-asserts both.
- **Checklist 13 — Viewer executes.** `wasm-viewer` `needs: docker-smoke` (`ci.yml:236`) and its
  **"Load the bundle in a real browser"** step ran and passed in run 33126418568 — not skipped, not
  `continue-on-error`. Its stdout: `{"loaded":true,"ms":1295,"clock":"tick 239/1080 · turn 3/10 …"}`
  and `soak: 10s of playback kept advancing ("1 / 1080" -> "191 / 1080" -> "239 / 1080")`, plus
  three scrub readouts at 0 %/50 %/100 % showing distinct ticks. Markers: `data-replay-loaded` set
  in the worker `'loaded'` branch (`static_replay.js:161`), `data-replay-error` in
  `showFailure()` (`:20`); both files byte-identical to the starter's after rename.
  Link flags vs bootstrap agree and come from one starter: `replay-viewer/config.nims` is
  byte-identical to the starter's after rename and contains **no `MODULARIZE` and no
  `EXPORT_NAME`** (`:35-53`), while `static_replay_worker.js:188` sets
  `Module.onRuntimeInitialized` — the non-modularised pairing. `-s ABORTING_MALLOC=1` present
  (`config.nims:49`); the `EXPORTED_FUNCTIONS` list is the renamed starter list (`:53`).
  **Playback opens at the game start:** `initReplayRuntime` seeks to `replay.replayStartTick()`
  (`replay_runtime.nim:47`), `replayStartTick` clamps `startTick` (set from
  `sim.gameStartTick` at `replays.nim:613-614, 648-649`) into range (`:267-270`), and **every**
  seek clamps to it — `seekReplay` (`:793`), restart (`:854`), step-back (`:857`), the transport
  paths (`:917, :936`). All inherited unchanged.
- **Checklist 14 — the page is the starter's plus a block.** `client/replay_broadcast.html`
  is 4 736 lines against the starter's 4 573; the banner
  `VIZDOOM-DEATHMATCH additions to the inherited coworld-ctf chrome` sits at line 4061 and
  everything after it is one `<style>` + one `<script>` (asserted `test_vzd_viewer.nim:34-47`).
  Every diff hunk above the banner corresponds to a removal or re-mapping the note enumerates:
  the `#viewpanel` CSS/markup/wiring (`:705-833, 1452-1459, 1506-1524, 4132-4244` of the starter),
  the `.beat-marker.steal/.return/.capture` rules (`:920-934`), the eight label re-mappings, the
  `Ctf*` → `Vzd*` identifier renames, the green/yellow kit fetch dropped to red/blue, and the
  z/x/arrow pan keys. Transport rules: `relayout()` sets `--band`/`--topband`/`--hudscale` on
  `document.documentElement`; `#endcard { bottom: var(--band, 0px) }` and
  `$('endcard').classList.remove('on')` on seek, both inherited; the game block's two elements are
  appended inside `#chrome` (`:4407`) and inside `#clock` (`:4366`), neither reaching the band;
  beats are `<button class="beat-marker …">` with `title`, `aria-label` and a
  `CTX.send('s:'+tick)` click (`:4321-4333`), named `dmBeat` so it cannot shadow
  `chrome_common.js`'s hoisted `var markBeat` (`test_vzd_viewer.nim:49-57` asserts
  `markBeat(` appears nowhere in the tail), with CSS for exactly the six emitted kinds and no
  others (`test_vzd_events.nim:64-84`). `#viewpanel` is **removed**, not hidden — markup, CSS,
  `core.attachMinimap` call, `ZOOM_STEP`, `panCellBoardPx` and every id, asserted at
  `test_vzd_viewer.nim:104-113` — which is right for a board whose aspect is a constant
  `1235/659` in every variant (`test_vzd_engine.nim:125-132`).
- **Scoring implementation vs §Scoring (sign, antisymmetry, zero sum).**
  `gameScorePermille(margin, DecisiveMargin=12)` is the starter's helper reused unchanged;
  `deathmatch.nim:34-55` gives `marginFor(T) = teamNet[T] − teamNet[other]`, exactly antisymmetric;
  `roster.nim:707-724` scores each seat from its own team's margin and sets
  `win = not faulted and permille > 500`; a `fault` forces 500/500 (`:711-713`).
  CI artifact check: `net = [1,-2,0,0,-1,0,0,0]` → `teamNet = [0,-2]`, `margin = 2`,
  `scores = [0.583, 0.417, …]`, and `0.583 + 0.417 = 1.000` exactly.
  `test_vzd_scoring.nim:8-36` covers 500 random margins for the exact-1000 sum, the formula, the
  ±12 clamp and the 0-margin draw. (What `frags` *means* is F5.)
- **End conditions.** `checkDeathmatchEnd` (`sim.nim:3397-3417`) is full-time only; `mercy` and
  `wipe` are unreachable — `EndRuleWipe`'s precondition `lives > maxTicks div (respawnTicks+1)`
  holds for every shipped config (60 > 52 and 60 > 22), asserted at `test_vzd_sim.nim:52-57` and
  `test_vzd_manifest.nim:180`, and `test_vzd_engine.nim:72-77` sweeps five seeds asserting
  `endRule ∉ {mercy, wipe}`. The three legal `reason` values and four `endRule` values are pinned
  in `results_schema` and exercised by `test_vzd_scoring.nim:85-96` (fault) and
  `test_vzd_replay.nim:65-79` (deadline).
- **Checklist 7, first half.** `test_vzd_engine.nim:55-70` runs a full 1 080-tick all-scripted
  eight-seat episode to its natural end and asserts `reason == "complete"`, `endRule ==
  "full_time"`, `games == 1`, eight-long arrays and an exact zero sum;
  `test_vzd_control.nim:23-56` asserts every baseline order is in bounds over 200 randomised worlds
  on both maps, and `:58-97` that every compiled mask is legal (never `C`, never both axes, zero
  when dead). The production binary independently ran the same shape in `docker-smoke`
  (`reason=complete`).
- **`egoview.marchRays` is genuinely the single ray march.** `broadcast.nim:609-613`'s
  `firstPersonJson` now iterates `sim.marchRays(playerIndex, columns, int(maxRange))` (the starter's
  inline 96-column march at `broadcast.nim:551-583` is gone), and the `#eyes` strip calls the same
  proc with `FpThumbColumns = 32` / `FpThumbRange = 600` (`broadcast.nim:975-990`, every 4th tick).
  The LLM strip calls it with `EgoRayColumns = 16` and `visionRange()`
  (`decide.nim:169-170`). 16 columns over a 90° cone is the note's 6° step.
- **Determinism additions are integer-only where they must be.** `deathmatch.nim` and `zones.nim`
  contain no float literal, no `/` and no `sqrt` (asserted by a source grep at
  `test_vzd_sim.nim:168-184`); `egoview.nim` uses floats freely and its outputs never reach
  `gameHash`. The new hashed fields (`medkitsTaken`, `leadTeam`, `lastLeadTick`, and the frag
  counters) are **appended** at the end of their types (`sim_types.nim:1378-1381, 1801-1812`) with
  the flatty-positional rule spelled out, and `GameVersion` restarts at `"1"` with the
  prepend-only changelog discipline (`sim_types.nim:21-31`), `tools/ci/check_gameversion.sh` kept
  byte-identical.

---

## Could not determine

- **Whether a `deadline` or `fault` episode replays correctly.** No such replay exists in the tree
  or in CI, and no test records one (F1, F7). What would settle it: a test that forces
  `wallClockBudgetSeconds` low, records the bytes, re-derives them through `initReplayRuntime` /
  `advanceReplayFrame` and asserts the hash chain **and** the resulting `phase`/`endRule` at the
  stop tick — i.e. the design's test 26.
- **Whether the LLM decision path behaves as traced at runtime.** `docker_smoke.sh` deliberately
  runs with no `ANTHROPIC_API_KEY`, so the only artifact available has `policyKinds` all
  `scripted`, `llmTurns` all 0, `fallbackTurns` all 0, `radio: []`. Everything in F18/F6 and the
  parse/retry/rate-guard tracing is read from source plus unit tests, never from a live episode.
  What would settle it: a phase-60 run with a real key, or a test that stubs the transport.
- **Whether `#eyes`, `#fragbug` and the radio feed are legible at 360 px.** `viewer_smoke.mjs` ran
  at its default viewport only, and `canvas_text` is structurally 0 on this renderer (F2). What
  would settle it: the renderer fixture the note specifies, driven at 360/640/1280 px.
- **Whether the `pool` variant's `mapSpec` renders faithfully from a real replay.** Only the
  `arena` fixture exists in CI. `test_vzd_engine.nim:114-123` shows the map is a pure function of
  the seed and `test_vzd_replay.nim:88-112` shows the spec is echoed as a JSON object; neither
  round-trips it through the wasm viewer.
- **Whether the two nano-banana assets read as a helmet and a skull.** I verified format, size and
  that both are shipped and referenced through `DM_BASE` (never root-absolute); I did not inspect
  the pixels.
- **The `feed_lines: 0` in the viewer smoke's payload.** The harness reported zero feed rows at the
  1.3 s load sample. `state["directives"]` *is* shipped (`broadcast.nim:929-936`) and
  `dmDirectives` does render a row per scripted directive (`replay_broadcast.html:4603-4607`), so
  this is most likely a sampling artefact rather than a dead feed — but I could not confirm it
  without running the page.
