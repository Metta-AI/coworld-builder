# r1 review — lux-ai

Range: `1c36d56b1bc71b06acd32857f9637bedf1e72fc4` (current `main`, 5 commits from
`ed10d38` bootstrap), diffed against the read-only starter mount
`/workspace/starters/coworld-ctf` where provenance matters.
Files read: 58 (all of `src/lux/*.nim`, `src/lux_ai*.nim`, `replay-viewer/*`,
`client/*.js` + `client/replay_broadcast.html`, `scripts/*`, all 19 `tests/*.nim`,
`tools/**`, `.github/workflows/*`, `coworld_manifest_template.json`, `docs/RULES.md`,
`AGENTS.md`, `Dockerfile*`, `compose.yaml`, `config.json`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
simultaneous-decision addendum).

CI evidence used throughout: `gh run list -R Metta-AI/cogame-lux-ai --branch main -w ci.yml`
→ run **33085620073**, `headSha 1c36d56b1bc71b06acd32857f9637bedf1e72fc4`,
conclusion **success**, jobs `test` / `docker-smoke` / `wasm-viewer` all green with
every step green (including `Load the bundle in a real browser`, `Native <-> wasm hash
gate` and `Worst-case chrome fixture`). Full log pulled with `gh run view … --log`.

---

## Blocking

### B1 — the worst-case renderer fixture runs, but produces no text-fit evidence, and does not assert its own strings are full-length

- Where: `tools/ci/renderer_fixture.html:174-217`; `tools/ci/viewer_smoke.mjs:81-82`,
  `:305-408`, `:409-437`; `.github/workflows/ci.yml:374-391`; CI run 33085620073,
  step `Worst-case chrome fixture`.
- Observed:
  - The fixture exists, is wired into its own `ci.yml` step with
    `--strict-text-bounds`, loads the *shipped* `dist/static-replay-viewer/index.html`
    in three iframes at 360 / 620 / 1280 px (`renderer_fixture.html:37`, `:174-192`),
    shims only the wasm entry (`:132-172`), feeds a frame with a full-cap 160-rune
    `note` on **both** seats (`:38-43`, `:93-98`), eight cities, a research rail past
    200, a deep-night frame and a `citylost` event (`:49-61`, `:122-130`), and sets
    `data-replay-loaded` on the top document (`:213-214`).
  - It contains **no assertion that its strings are still full-length**. `runeCap(NOTE_A, 160)`
    (`:45-47`, `:95`) caps the string, but nothing reads back what the page rendered
    and nothing compares lengths. The only failure path is a *synchronous* throw
    inside the first `feed(...)` call (`:205`) rejecting the promise into
    `data-replay-error` (`:215-216`); the second frame is fed from a `setTimeout`
    (`:206`) and a throw there is not caught at all.
  - The harness measures nothing inside those iframes. `viewer_smoke.mjs:81-82` states
    it "loads the viewer as the TOP-LEVEL document, not in an iframe", and the text
    tally `window.__coworldTextBounds` (`:305-408`) plus `READOUT_SCRIPT` (`:409-437`)
    are per-document values read from the main frame only.
  - The CI evidence bears this out. Both smoke invocations report a **zero** tally:
    - bundle run: `{"loaded":true,"ms":605,…}` then
      `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`
    - fixture run: `{"loaded":true,"ms":286,"clock":null,"scorebug":null,"feed_lines":0}` then
      `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`
  - `total: 0` is structurally correct for this repo: all lux-ai chrome text is DOM,
    not canvas. The board is a sprite blit stream (`src/lux/global.nim:325-436`,
    rendered by the inherited `client/broadcast_core.js`), and the commander line is
    a DOM feed row (`client/replay_broadcast.html:2342-2355`, `luxDirectives` →
    `luxFeed` → `CTX.pushFeed`). So `--strict-text-bounds` is present and green but
    covers zero draws.
  - The band the note lands in is **not** sized from `MaxNoteRunes`. `luxDirectives`
    writes the whole 160-rune note into `<span class="badge">`
    (`client/replay_broadcast.html:2350-2353`) inside a `.feed-row`. The governing CSS
    is the starter's, unmodified — `scripts/lux_block.html` adds no `#killfeed`,
    `.feed-row` or `.badge` rule (grep: only the `row.className = 'feed-row'`
    assignment at `:311`):
    - `client/replay_broadcast.html:356-372` — `#killfeed { width: calc(228 * var(--u));
      right: calc(12 * var(--u)); align-items: flex-end; }`
    - `:374-390` — `.feed-row { max-width: none; white-space: nowrap; }` with the
      starter's own comment: *"bounded by the small font + the pre-bounded 10-char
      name, so it can't run away"* — an assumption about a 10-character name, not a
      160-rune sentence.
    - `:398-406` — `.feed-row .badge { font-size: calc(7 * var(--u)); letter-spacing:
      0.1em; text-transform: uppercase; }`
    - `:75-85` — `#stage { overflow: hidden; }`
- Checklist item: item 15, third and fourth bullets —
  *"Any text laid out relative to another element … gets a **reserved band in the
  layout**, sized from the cap the server enforces on that string (`MaxSayLen` and its
  kin) and measured in the font it will be drawn in"*, and
  *"The fixture **asserts its own strings are still full-length** — one quietly
  shortened remark leaves it passing while testing nothing. Cite the step and its
  `canvas_text` line."*
- Why blocking: the two gates item 15 names are both inert here. The cited
  `canvas_text` line is `0 drawn`, which item 15 itself says "means the check covered
  nothing … and is not evidence of anything"; and the fixture that is supposed to
  substitute for it asserts nothing about the text it renders. Nothing in CI can
  distinguish "the 160-rune note rendered legibly at 360 px" from "the note was
  clipped away entirely".
  - **Inferred (arithmetic, not measured):** at the 360 px featured-match width
    `relayout()` clamps `--hudscale` to `0.5` (`client/replay_broadcast.html:~1490`,
    `Math.max(0.5, Math.min(1.6, boardW / 760))`), so `--u = 0.5px`, `#killfeed` is
    114 px wide anchored 6 px from the right edge, and the badge font is 3.5 px with
    0.1em tracking. A 160-character uppercase run at that metric is roughly 390 px
    wide on a `white-space: nowrap; max-width: none` row that grows leftward from
    x≈354, i.e. it starts around x≈-38 inside a `#stage { overflow: hidden }` of width
    360. The leading characters of every commander line would be clipped off the left
    edge. This is a computation from the CSS, not a browser measurement — see
    "Could not determine" for what would settle it.

---

## Non-blocking

### N1 — the replay's lobby length is recorded as an `InputStart` record, but playback can auto-start the game *before* that record is reached

- Where: `src/lux/sim.nim:162-173`; `src/lux/replays.nim:119-131`, `:170-197`;
  `src/lux/server.nim:484-502`.
- Observed: the live server never calls `sim.step()` while in `Lobby` — it handles the
  lobby itself and `continue`s (`server.nim:484-502`), writing a lobby-shaped hash each
  tick (`sim.gameHash()` returns the `(-1, tickCount)` mix while `phase == Lobby`,
  `sim.nim:188-194`) and emitting `InputStart` only on the tick both seats are joined
  **and** `tickCount >= startWaitTicks` (`server.nim:486-497`). Playback does call
  `sim.step()` every tick (`replays.nim:220-229`), and `sim.step()`'s own `Lobby`
  branch (`sim.nim:165-170`) begins the game as soon as
  `(joined and tickCount >= startWaitTicks)`. `simFromReplay` marks **both seats joined
  at construction** from the join records regardless of the tick they were recorded at
  (`replays.nim:125-131`). So if the seats connect after `startWaitTicks` (48 ticks ≈
  2 s at `TargetFps = 24`), the server starts at tick T > 48 while playback starts at
  tick 48; the recorded hash at tick 49 is the lobby hash and the re-simulated one is a
  world hash, and `checkReplayHash` (`replays.nim:199-218`) diverges from tick 49 on.
  The `InputStart` record arriving later is a no-op because `beginPlaying` returns early
  once `phase != Lobby` (`sim.nim:103-105`).
- What the note says: §Sim module → "Determinism, native ↔ wasm" and the `InputStart`
  comment in `replays.nim:44-47` both make the lobby length a load-bearing wall-clock
  fact recorded in the input stream. The note's re-derivation claim is unconditional.
- Not exercised by anything in the tree: `tests/helpers.nim:22-27` sets
  `startWaitTicks = 0` and `lobbyJoinTimeoutTicks = 2` for every fixture, and
  `tests/test_lux_replay.nim:32-33` writes `InputStart` at tick 0 before
  `beginPlaying()`, so no test ever records a non-zero lobby. In CI's `docker-smoke`
  the player containers are launched immediately after the game container
  (`tools/ci/docker_smoke.sh:202-222`) and the run was clean — the `Native <-> wasm hash
  gate` step reported `ok: loaded episode.replay, advanced 300 frames` — so the seats
  evidently joined inside 48 ticks there. In the hosted platform the player pods are
  scheduled independently. If this path is reachable it would falsify checklist item 2.

### N2 — the Bedrock model ladder has one entry, not the note's two, so `tryNextBedrockModel` can never rotate

- Where: `src/lux/llm.nim:71-80`, `:82-90`, `:167-184`.
- Observed: `bedrockModelIds()` returns `@["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`
  (`llm.nim:80`). With one candidate, `tryNextBedrockModel` always returns `false`
  (`:83-85`). Consequences that follow in the same file: a 403 carrying
  `"Model access is denied"` falls through to `client.disabled = true` (`:172-177`),
  disabling the LLM for the rest of the episode rather than rotating; every 429 sets
  `client.throttled = true` (`:180-183`), which `decide.turn` treats as
  "fail fast, skip the retry" (`src/lux/decide.nim:266-271`).
- What the note says: §Decisions → "Bedrock model candidates **in order**,
  `BEDROCK_MODEL` pins one: `us.anthropic.claude-haiku-4-5-20251001-v1:0`, **then**
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`; `tryNextBedrockModel` on 401/403
  'Model access is denied' and on 429." The code comment at `:73-76` only documents the
  exclusion of `sonnet-4-6` (which the note also excludes); the removal of
  `sonnet-4-5` is undocumented.

### N3 — the server does not hold `gameOverTicks`; the replay carries one GameOver tick, not 72

- Where: `src/lux/server.nim:516-540`; `src/lux/sim.nim:184-186`.
- Observed: `episodeFinished()` (which is the `gameOverTicks` hold) is defined at
  `sim.nim:184-186` and is used by four tests and `tools/tune_baselines.nim`, but is
  **never referenced in `src/lux/server.nim`** (grep over `src/`). The server writes the
  artifacts on the first `GameOver` iteration (`server.nim:530-532`) and then breaks out
  of the loop after the 20 s `ShutdownGraceSeconds` sleep (`:533-540`), so exactly one
  tick is recorded after the settle tick.
- What the note says: §Decisions → "ctf's `gameOverTicks` hold before exit"; §Viewer →
  "48 lobby ticks + 360 turns + 72 `gameOverTicks` = 480 ticks ⇒ 32 s of playback",
  and `sim_types.nim:34-37` repeats that arithmetic in a comment. The actual replay is
  ~409 ticks ⇒ ~27 s at `ReplayFps = 15`, still comfortably past `--soak 10`; the
  endcard is held by `advanceReplayPlayback`'s `endHoldFrames = ReplayFps * 10`
  (`replays.nim:410-413`) rather than by recorded ticks. `gameOverTicks` remains a
  declared, defaulted, schema'd config knob that the server ignores.

### N4 — four declared config knobs are not read by the sim

- Where: `src/lux/sim_config.nim:43-45`, `:53-54`, `:172-173`, `:186-187`;
  `src/lux/sim_types.nim:193-197`; `src/lux/resolve.nim:266`, `:297`, `:319-320`, `:167`.
- Observed: `workerCargo`, `cartCargo`, `workerCooldown` and `cartCooldown` are parsed by
  `config.update` and echoed into the replay config JSON and the manifest
  `config_schema`, but every consumer uses the compile-time constant instead:
  `cargoCap(kind)` and `baseCooldown(kind)` read `WorkerCargo` / `CartCargo` /
  `WorkerCooldown` / `CartCooldown` from `sim_types.nim:193-197`. `applyCityBuilds`
  additionally hardcodes the build cooldown as the literal `20`
  (`resolve.nim:167`) rather than `config.workerCooldown`. `regrowWood` uses the const
  `WoodRegrowCap` (`resolve.nim:430-433`) and `tickCooldowns` the literal `10`
  (`resolve.nim:405`, `:410`).
- What the note says: §Packaging lists all four in `config_schema` as settable
  ("every rule constant … all overridable", `sim_config.nim:40`). The manifest test
  (`tests/test_lux_manifest.nim:129`) only checks that `config_schema` covers what
  `update` *reads*, which these are, so nothing catches the inertness.

### N5 — the micro evaluates the cart hand-off *before* the night policy, where the note puts it after

- Where: `src/lux/micro.nim:296-336` (hand-off) vs `:338-349` (night policy).
- Observed: for a worker with `cooldownTenths == 0` the compiler adjusts `stance` for
  `npHaul` (`:296-298`), then runs the `block handoff` transfer rule (`:300-336`), and
  only then the `npShelter` night rule (`:339-349`). A worker at night under
  `night: "shelter"` that is > 4 cells from home, carrying ≥ 40, and orthogonally
  adjacent to a cart with free space, therefore emits a `transfer` instead of stepping
  home — and then pays night upkeep in the open.
- What the note says: §Decisions → "The micro layer": the worker rules are numbered
  1 Night policy, 2 Full, 3 Mining, 4 Transfer, with rule 4 explicitly *"Before steps 2
  and 3"* — i.e. after rule 1, not before it. Undocumented reordering (`docs/RULES.md`
  §"Two amendments" names only the city-tile order and `prospector`).

### N6 — `build: "city"` makes a city tile idle even when its research target is unmet

- Where: `src/lux/micro.nim:406-407`, `:439-441`.
- Observed: the tile loop `continue`s on `directive.build == boCity` before any
  research check, so a tile never researches while `build == "city"`.
- What the note says: §Decisions → per city tile, rule 1 is research
  (`researchPoints < researchTarget` → `research`) and rule 2 is
  "Else if `build == "city"` → no action". Under the note, research wins. This is
  adjacent to, but wider than, the documented "production before research" amendment
  (`docs/RULES.md:90-97`, `micro.nim:408-417`), which is only about the ordering of
  production against research.

### N7 — deviation (a) "production before research": documented and self-consistent

- Where: `src/lux/micro.nim:408-441`; `docs/RULES.md:85-97`; `AGENTS.md` §"Two
  amendments".
- Observed: the tile loop places `build_worker`/`build_cart` ahead of `research`, gated
  on `headroom = unitTotal < tileTotal` (`:418`), with local counters incremented so
  one turn's tile actions do not over-commit the unit cap. Research still fires when
  the side is capped or at its target (`:439-441`), and `rtAlways` still overrides.
  `applyTileActions` re-checks the cap independently (`resolve.nim:85-86`), so a stale
  micro decision is discarded rather than breaking the invariant. The reason given
  (S1's `units < cityTiles` cap starves a one-tile opening) is consistent with the
  system prompt's own framing (`src/lux/llm.nim:216-217`).

### N8 — deviation (b) `prospector`'s night guard + seed blob: documented and self-consistent

- Where: `src/lux/baselines.nim:148-186`; `docs/RULES.md:98-104`.
- Observed: `prospectorDirective` adds a `starving` branch reusing
  `tuning.foresterFuelNights * bill` (`:148-165`) and an `elif` that plays `stExpand`
  until `tiles >= tuning.prospectorSeedTiles` (`:166-176`). Both are named in
  `docs/RULES.md` and both are inline-commented at the site. The mine ladder, `carts = 2`
  and `night = shelter` are the note's (`:181-189`). The `prospectorSeedTiles` knob is a
  new fifth swept parameter and is present in `tools/ci/baseline_tuning.json`.

### N9 — deviation (c) `broadcast_core.js` inherited byte-for-byte: documented, and a third `CTF_WIRE` site

- Where: `client/broadcast_core.js` (sha256
  `172c4680129d608fd687cfd86436b675eef32c8652be6afe5f3189dd20c5aa9c`, identical to the
  starter's); `src/lux/wire_constants.nim:6-12`, `:32`; `tests/test_lux_viewer.nim:95-110`,
  `:227-243`.
- Observed: `diff` against `/workspace/starters/coworld-ctf/client/broadcast_core.js`
  is empty. The design note said this file would be forked with `drawBoard`,
  `drawResources`, `drawCities`, `drawUnits`, `drawNight`, `drawCycleBar` added and the
  ctf draw calls deleted. Instead the board is emitted as a sprite stream by
  `src/lux/global.nim` (baked chips at `:325-436`) and the inherited compositor draws it
  unchanged; the reason is written down in `tests/test_lux_viewer.nim:96-100`. The note
  said `CTF_WIRE` would survive in exactly **two** places; it survives in three
  (`chrome_common.js:72`, `broadcast_core.js:49`, `wire_constants.nim:32`), and
  `wire_constants.nim:6-12` says so and the test whitelists exactly those.

### N10 — deviation (d) swept baseline parameters: documented, gated, and not the note's numbers

- Where: `src/lux/baselines.nim:37-50`; `tools/ci/baseline_tuning.json`;
  `tools/tune_baselines.nim:1-60`; `.github/workflows/ci.yml:104-108`;
  `tests/test_lux_baselines.nim:117-127`.
- Observed: shipped values are `foresterWorkers = 6`, `foresterFuelNights = 18`,
  `prospectorEarlyWorkers = 6`, `prospectorLateWorkers = 10`, `prospectorSeedTiles = 8`.
  The note's literals are `forester workers = 8`, an `11 * upkeep` threshold and
  `prospector workers = 5 / 10`. The written objective, the seed set and the `--check`
  gate exist and run in CI (`test` job step "The scripted baselines are the swept
  pick", green in run 33085620073). Checklist item 7's "tuned with a grid harness, not
  guessed" is satisfied.

### N11 — deviation (e) the forensics helpers are absent and the omission is undocumented

- Where: absent — `tools/expand_replay.nim`, `tools/extract_events.nim`,
  `tools/record_fixture.sh`, `flake.nix`, `client/league_replayer.html`,
  `src/lux/events.nim`, `src/lux/labels.nim`, `src/lux/rig_art.nim`.
- Observed: the note lists all of these (§Sim module "Kept, by path" table lines
  853/858/862/865, §Packaging repo layout lines 1628-1638, `Dockerfile.replay-viewer`
  asset list line 1469 naming `league.html`). `tools/replay_summary.py`,
  `tools/wasm_replay_smoke.cjs` and `tools/tune_baselines.nim` are present; the other
  three tools are not, and nothing in `README.md`, `AGENTS.md` or `docs/` records the
  omission (`README.md:63` still says "tools/ … the forensics"). The absorbed modules
  are fine functionally: `eventsJsonl` + `SimEventKind` live in
  `src/lux/sim_state.nim:227-272`, the label-vocabulary contract lives in
  `tests/label_manifest.txt` + `tests/test_lux_label_contract.nim`, and the unit chips
  are baked in `src/lux/global.nim`. Two stale references survive:
  `scripts/art/split_cog_sheet.py:13` points at `src/lux/rig_art.nim` and
  `client/replay_broadcast.html:1197` (inherited) mentions `league_replayer.html`.
  `Dockerfile.replay-viewer` does **not** try to copy `league.html`, so the bundle build
  is unaffected.

### N12 — the art sources are not the ones the note names

- Where: `data/cogs/{red,blue}_{worker,cart}.png`, `data/rock_tile.png`,
  `data/wall_tile.png`, `scripts/art/source/cogs_sheet.png`,
  `scripts/art/split_cog_sheet.py`; `src/lux/global.nim:1-20`.
- Observed: there is no `data/soldier_*.png` in the tree. Units are four committed
  "nano-banana Softmax-cog renders" split from a committed sheet; resource chips and
  city buildings are baked from committed crops of `client/art/walls/*.jpg`. The floor
  is `data/arena_floor.png` and the palette `data/pallete.png`, as the note says, and
  the locker room ships only the red and blue webps (the green/yellow carousels are
  removed in `scripts/fork_broadcast_page.py:181-194`, which is why they cannot 404).
- What the note says: §Sim module edit 3 and §Viewer → Art both specify
  `data/soldier_{red,blue}.png` baked by `rig_art.nim`. The substitution is committed,
  reproducible (`tests/test_lux_scaffold.nim:98-103`) and involves no download, but it
  is not recorded as a deviation anywhere in the repo.

### N13 — the whole-reply cap is applied in runes, not bytes

- Where: `src/lux/llm.nim:197-198`; `src/lux/sim_types.nim:46-48`.
- Observed: `if result.len > MaxReplyBytes: result = result.truncateRunes(MaxReplyBytes)`
  — the test is on bytes, the cut is on 4096 **runes**, so a multi-byte reply can be
  kept at up to ~16 KB. Rune-safe (it can never split a codepoint), just looser than
  the declared bound.
- What the note says: reply-schema table — "whole reply | **bytes** | ≤ 4096 read from
  the provider before parsing".

### N14 — the "9 KB reply is capped and then parsed" test asserts nothing about parsing

- Where: `tests/test_lux_directives.nim:82-96`.
- Observed: the test ends `check capped.runeLen == MaxReplyBytes` and
  `check (recovered or true)` — the second is a tautology, so the `recovered` flag is
  computed and discarded. (Written this way in the original commit; nothing was
  loosened during this run.)

### N15 — several tests the note specifies for the decision layer are not present

- Where: `tests/test_lux_engine.nim` (whole file); `tests/test_lux_directives.nim`
  (whole file); grep for `fake`/`hung`/`PLAYER_FAILURE` across `tests/` returns nothing.
- Observed, against the note's test 13 and test 16:
  - "one parallel batch" is asserted **structurally, from the source text** —
    `source.count("makeRequests") == 1` plus an ordering check on
    `var batch: RequestBatch` / `batch.post(` / `makeRequests(`
    (`test_lux_engine.nim:157-174`). The note specified a fake client recording
    in-flight windows and asserting they intersect. The code itself does issue one
    `curl.makeRequests(batch, …)` for all open seats (`src/lux/decide.nim:223-238`), so
    the addendum ("all seats' LLM calls go out as one parallel batch per turn") holds
    on the code; only the *form* of the test differs.
  - No test drives a hung client against `turnBudgetMs`.
  - No test asserts "timeout on attempt 1 ⇒ exactly one retry", "two consecutive
    failures ⇒ the forester directive plus a fallback record", or "a `throttled`
    attempt 1 with no other candidate ⇒ no retry". Those paths are readable at
    `decide.nim:212-271` and are correct on inspection, but nothing executes them.
  - No test asserts the `COGAME_PLAYER_FAILURE_URI` closed payload
    (`src/lux/server.nim:237-246` builds exactly `{"failed_policy_index","message"}`
    and is called once behind `failureDeclared` at `:488-494`).
  - No test asserts `turnSpacingMs` holds the rate at ≤ 30 req/min (only the rolling
    counter, `test_lux_engine.nim:114-128`).

### N16 — the worst-case per-directive-turn wall clock is ~13 s, not the note's 11 s

- Where: `src/lux/decide.nim:146-152`, `:203-209`, `:213-238`.
- Observed: `turnStart` is taken at the top of `turn` (`:150`), the rate-floor sleep of
  up to `turnSpacingMs` (6 s) happens after it (`:203-206`), and the budget check
  `getMonoTime() - turnStart >= budget` runs **before** each attempt (`:216-220`) rather
  than bounding the attempt itself. Worst path: 6 s sleep → check (6 < 11, proceed) →
  attempt 1 with a 7 s `CURLOPT_TIMEOUT` → 13 s → check (13 ≥ 11) → timeout records and
  break. Every wait is still explicitly bounded and nothing blocks unbounded; the
  arithmetic still closes: 36 × 13 = 468 s + 100 s lobby cap + 20 s artifacts + 3 s sim
  = 591 s < the 660 s engine stop < 720 s (60 % of 1200). The wall-clock stop is checked
  at the top of the loop (`server.nim:475-482`), so it can overshoot 660 s by one
  iteration (~13 s) → ~673 s, still inside 720 s.
- What the note says: "36 directive turns × max(spacing 6 s, budget 11 s), absolute
  worst = 396 s". `tests/test_lux_engine.nim:39-44` asserts the note's 396 s arithmetic,
  not the code's.
- Also observed: when the budget check fires, the seat gets **two** fallback records
  for the same turn — one `cause: "timeout"` at `:218-219` and one from the
  "anything still open" loop at `:285-286`. `results.fallbackTurns` is incremented once
  (`:278`), so only the record count doubles.

### N17 — the replay is ~4× the note's size estimate

- Where: `src/lux/decide.nim:292-294`; `src/lux/directives.nim:370-384`.
- Observed: every directive chat record embeds the seat's whole observation object
  verbatim as `view` (`directives.nim:384`), for **both** seats on every directive turn,
  including scripted seats. CI's smoke replay is 241 926 bytes
  (`docker-smoke` log: `smoke OK: seats=2 results=585B replay=241926B reason=complete`).
- What the note says: §Server → "360 hashes + 72 directive input records + 72 directive
  chat records + the config ≈ **60 KB**". The `view` mirroring is itself the note's
  own requirement ("mirrored (verbatim) into the replay's `directive` chat record"), so
  the estimate, not the behaviour, is what is off.

### N18 — `tokens[]` is deliberately not written into the replay config, against the note's table

- Where: `src/lux/sim_config.nim:325-326`; `tests/test_lux_replay.nim:147`.
- Observed: `configJson` omits `tokens` with the comment "matriculate rejects a
  game_config that carries one, and a replay is a public artifact", and the test asserts
  `"tokens" notin config`. The note's "Replay bytes" table lists `tokens[]` as config
  content. `slots[]`, `players[].name` and `fastMode`/`fullyObservable` are present
  (`:317-324`). The omission is the safer reading of the note's own §Packaging rule and
  is documented at the site. `model` is also absent from `configJson` though it is in
  `config_schema`.

### N19 — small transcription differences from the note, each self-consistent

- `PlaybackSpeeds = [1, 2, 4, 8, 16]` (`src/lux/sim_types.nim:38`) where the note says
  speed chips `[0.5, 1, 2, 4, 8]`. Default index 0 gives 1 tick/frame at
  `ReplayFps = 15` = the note's "15 turns per second".
- The player container re-dials at most 3 times (`ReceiveRetries = 2`,
  `src/lux_ai_player.nim:35`, `:86`); the note says "up to 6 times". Both exit 0 on a
  dead socket, which is the load-bearing part (`:116-127`).
- `city.upkeep` is floored at 0 (`src/lux/cities.nim:73-77`); the note's formula has no
  floor. Unreachable for any orthogonally-connected blob (an n×n block pays
  `13n² + 10n > 0`).
- `tests/test_lux_board.nim:9-18` sweeps 5 000 seeds × 2 map sizes and its docstring
  calls that "10 000 seeds"; the note asks for 10 000 seeds *and* both sizes.
- `tools/ci/policies.json` adds a `PLAYER_POLICY_LABEL` env var to all four policies;
  the note's listing has only `PLAYER_PROMPT` / `PLAYER_SCRIPTED`. Harmless — the label
  is read at `src/lux_ai_player.nim:48`.
- `runServerLoop`'s replay-mode branch is an unbounded `while true … continue`
  (`src/lux/server.nim:444-469`) with no wall-clock stop. This is the local developer
  `/client/replay` route entered only when `COGAME_LOAD_REPLAY_URI` is set; it is not an
  episode path, so no episode wait is unbounded.

---

## Traced and consistent

**Resolution rules (the note's 13-step order)**

- `src/lux/sim.nim:138-160` — `stepPlaying` runs step 1/2 (`compileBothSeats`), then
  `resolveTurn`, then `checkLuxInvariants` (step 12), then the turn increment and the
  `full_time` / `eliminated` end checks (step 13). `src/lux/server.nim:506-515` supplies
  step 1's directive install and `writeHash` before the step.
- `src/lux/resolve.nim:435-452` — `resolveTurn` calls steps 3→11 in the note's exact
  order, with the night burn gated on `isNight`.
- Step 3 `resolve.nim:57-92` — ascending cell index within seat 0 then seat 1;
  `cooldownTenths += cityCooldown` on any accepted action; the unit cap re-checked at
  `:85-86`; the new unit spawns with `cooldownTenths = 0` and cannot act this turn
  because the order list was fixed in step 2.
- Step 4 `resolve.nim:94-129` — ascending giver id, orthogonal adjacency and same team
  enforced, `moved = min(amount, stock, receiverFreeCargo)`, evaluated against the
  already-updated cargo, cooldown only on a successful transfer.
- Step 5 `resolve.nim:131-174` — `empty` terrain, no tile, `totalCargo >= cityCost`;
  contested build (both teams → neither builds and neither spends, `:150-162`);
  same-team → lowest id; `spendCheapestFirst` (`units.nim:52-66`) spends wood→coal→
  uranium; `road = maxRoad`; `cities.addTile` merges into the lowest adjacent same-team
  id with fuels summing (`cities.nim:91-134`, and `keepIndex` is stable because `keep`
  is the minimum id so every deleted index is greater).
- Step 6 `resolve.nim:176-270` — (a) off-board and opponent-tile targets discarded at
  no cooldown; (b)+(c) run as **one** monotone fixed point (`blocked` only ever goes
  true, bounded by `guard <= 2*count+2`), with the reason for merging the two passes
  written down at `:208-215`; every occupant of a cell is considered, not just the last
  (`:219-221`); friendly city tiles exempt from both blocking and contention; (d)
  simultaneous application, cart paving `min(maxRoad, road+1)` on `tEmpty` only,
  `blockedMoves[team]` incremented for cancelled moves.
- Step 7 `resolve.nim:272-330` — workers only; kind order wood→coal→uranium; ascending
  tile index; research gates from config (`:284-287`, `:295`); the even split with the
  first `amount mod |M|` miners taking one extra (`:313-318`); each take clamped to free
  cargo; `Depleted` emitted on the 0 crossing.
- Step 8 `resolve.nim:332-346` — every unit on a friendly tile empties into that tile's
  city at 1/10/40 (`units.nim:26-28`), every turn.
- Step 9 `resolve.nim:348-399` — cities first in id order, `upkeep = 23*tiles -
  5*adjacentPairs` (`cities.nim:61-77`, east/south only so each pair counts once),
  under-fuelled cities destroyed whole with `cityTilesLost += tiles` and a `CityLost`
  event, surviving cities then debited; units second, sheltered units checked against
  the *post-destruction* tile map (`:379`) so a unit in a city that just burned pays;
  `burnForFuel` spends cheapest-first and overpay is lost (`units.nim:68-83`).
- Step 10 `resolve.nim:401-410` — `max(0, cd - (10 + 2*road))` for units, `-10` for
  tiles. Step 11 `resolve.nim:422-433` — `+max(1, amount div 50)` capped at 500, and a
  tile at exactly 0 is skipped forever.
- `src/lux/board.nim:118-186` reproduces the note's `place()` pseudo-code including the
  `attempts mod 200` separation relaxation and the eight-neighbour BFS in the fixed
  order; `:188-219` the start-cell scan; `:245-251` the mirror. `mirrorSymmetric`
  (`:253-258`) checks kind only, as the note says.
- `src/lux/scoring.nim:33-63` — the ladder in order cityTiles → units → fuel → tie, with
  `points ∈ {0,1,2}` integer and the 0.0/0.5/1.0 produced only in `scoreOf`. `settle`
  in `sim.nim:112-125` scores from the standing at the stop turn, so a `deadline`
  episode is never zeroed.
- `src/lux/sim_state.nim:160-221` — the guard covers every clause the note lists
  (on-board, not on an opponent tile, non-negative and capped cargo, one unit per
  non-city cell, resource range, road range, city tiles fully paved, fuel range,
  connected component, tile bookkeeping, tile counts, non-negative research, turn
  bound, mirror symmetry). The one addition is `burntStack` (`:33-39`, `:181-182`),
  which tolerates a stack stranded when a city burns under it and is cleared the moment
  the cell is back to one occupant (`resolve.nim:412-420`) — deterministic on both
  sides and never hashed.

**Decision path**

- `src/lux/decide.nim:138-297` — one `turn` per directive turn. Both open seats are
  posted into one `RequestBatch` and handed to a single
  `client.curl.makeRequests(batch, max(1, deadlineMs div 1000))` (`:223-238`); the
  addendum's "one parallel batch per turn, never sequential" holds. Attempt 0 uses
  `attempt1Ms`, attempt 1 `retryMs` (`:221-222`), `while … attempt < 2` gives exactly
  one retry. A `throttled` client breaks before the retry (`:266-271`). Every failure
  writes a `fallback` record with a cause drawn from the note's closed set
  {timeout, parse_error, transport_error, throttled, no_credentials, rate_guard,
  budget_guard, disconnected} (`:192-198`, `:254-263`, `:279-286`) and increments
  `sim.fallbackTurns` (`:191`, `:278`), which reaches `results.fallbackTurns`
  (`sim.nim:494`). The phrase phase 60 greps for ("falling back") is emitted at `:199`
  and `:288`, and "the LLM provider is unavailable" at `llm.nim:128`.
- Budget guard `decide.nim:153-164` implements the note's inequality verbatim
  (`elapsed + 2*(spacing + budget) > wallClockBudgetSeconds`, a 34 s reserve at 6/11)
  and writes a `budget_guard` record. Rate guard `:130-136`, `:180`, `RollingRequestCap
  = 28` at `:49-54`, matching the note.
- The fallback directive is `scriptedDirective(world, blForester, seat)`
  (`decide.nim:65-68`), the same proc the filler calls
  (`baselines.nim:200-208`); `tests/test_lux_baselines.nim:93-100` pins the equality.
- Tolerant parsing `directives.nim:148-187` (balanced-brace scan, fence tolerance,
  first-brace..last-brace rescue) and `:212-349` (per-field repair matching the note's
  repair column, unknown keys ignored, a note-only reply usable, `repaired` counted into
  `results.directivesRejected`).
- `llm.nim:200-261` is the note's system prompt verbatim; `:263-275` the
  `operatorBlock` + observation user message; `:149-152` suppresses `output_config.effort`
  for haiku/4-5; `:96-129` is the note's credential ladder with the disabled-client
  fast path.

**Waits and bounds** — `attempt1Ms 7000` / `retryMs 3000` / `turnBudgetMs 11000` /
`turnSpacingMs 6000` / `wallClockBudgetSeconds 660` are the shipped defaults
(`sim_config.nim:114-118`), asserted at `tests/test_lux_engine.nim:32-45`, and repeated
in all three manifest variants (checked below). `validate` enforces whole seconds and
`attempt1Ms + retryMs <= turnBudgetMs` and `wallClockBudgetSeconds <= 720`
(`sim_config.nim:250-264`). The lobby wait is bounded by `lobbyJoinTimeoutTicks`
(`server.nim:486-487`), the post-artifact grace by `ShutdownGraceSeconds = 20`
(`server.nim:31-35`, `:538-540`), and `broadcast()` is fire-and-forget with a
`try/except discard` per socket (`server.nim:374-392`). No blocking read on the game
loop: the mummy serve thread is separate (`server.nim:299-305`).

**String truncation** — `truncateRunes` (`directives.nim:75-82`) is `runeLen` /
`runeSubStr` and is the single cut point; used for `note` via `sanitizeNote`
(`:84-89`), `register.policy` (`roster.nim:63`), `fallback.detail`
(`decide.nim:81`), `results.stopDetail` (`sim.nim:498`), `how_it_went`
(`sim.nim:444`, `decide.nim:124`), the prompt (`server.nim:334`,
`llm.nim:270`, `lux_ai_player.nim:56-57`), captured provider bodies
(`llm.nim:171`, `:179`, `:187`, `:196`) and the parse-error head
(`directives.nim:182-186`). Caps match the note's table
(`sim_types.nim:41-49`). `tests/test_lux_directives.nim:97-121` feeds a 4-byte emoji at
`MaxNoteRunes`, `MaxPolicyLabelRunes`, `MaxFallbackDetailRunes`, `MaxPromptRunes` and
`MaxHowItWentRunes` and asserts `runeLen == cap`, `len == cap*4` and
`validateUtf8() == -1`; `tests/test_lux_replay.nim:215-280` fills every cap with emoji
in a real replay and round-trips it through `tools/replay_summary.py` under strict
`utf-8`, asserting no lone surrogates.

**Replay writer and re-derivation** — `replays.nim:24-33` sets magic `COWLDLUX`,
`gameName lux-ai`, `gameVersion 1`, `joinKind rjkNameSlotToken`, `allowChat`;
`:94-110` writes the 13 directive bytes as consecutive one-byte input records;
`server.nim:295-296` writes the resolved config header; `:371-372` the joins;
`:399` the `result` record; `:499`, `:514`, `:517` one `writeHash` per tick, taken
**after** the tick's inputs are installed and **before** the step, which is exactly the
instant playback compares at (`replays.nim:220-229`, comment at `:226-227`).
`gameHash` (`sim_state.nim:110-154`) mixes the note's fixed sequence and excludes
`note`/`source`/`latency`/labels; `tests/test_lux_determinism.nim:86` pins that. The
wall-clock stop rides **both** the input stream (`InputWallClockStop`,
`server.nim:476-477`, applied at `replays.nim:190-191`) and a `stop` chat record, and is
applied on both sides by the one proc `sim.applyWallClockStop`
(`sim.nim:127-136`). `tests/test_lux_replay.nim:88-133` asserts frame-by-frame hash
re-derivation for `full_time`, for `wall_clock` **including the stop turn**, and that an
out-of-band corruption is caught at its tick.

**Viewer re-derivation and provenance** —
- `replay-viewer/lux_replay.nim` imports `lux/sim` and re-steps the same modules; the
  load-time pre-scan lives in `initReplayPlayer` → `runScan`
  (`replays.nim:270-346`), and `lux_mismatch_tick` returns
  `checkReplayHash`'s tick or -1 (`lux_replay.nim:124-128`).
- `client/chrome_common.js` is **byte-identical** to the starter's
  (`sha256 7ace7287…`, `diff` empty), pinned at `tests/test_lux_viewer.nim:11-12`.
- `client/replay_broadcast.html` regenerates **exactly** from the starter mount:
  `python3 scripts/fork_broadcast_page.py /workspace/starters/coworld-ctf /tmp/regen.html`
  followed by `diff` against the committed file is empty. The script takes the starter's
  head up to its `PAINTBALL` banner, deletes nine named line regions plus three markup
  blocks plus a CSS-prefix list that is exactly the note's removals, applies the note's
  relabel table, and appends `scripts/lux_block.html` under the banner
  `LUX-AI additions to the inherited coworld-ctf chrome`. 2 452 committed lines against
  a ~4 340-line inherited head minus ~2 100 deleted lines plus a 701-line block — a
  fork, not a rewrite.
- Transport rules: `relayout()` sets `--hudscale`, `--topband`, `--band` on
  `document.documentElement` (`client/replay_broadcast.html:~1485-1520`);
  `#endcard { … bottom: var(--band, 0px) }` (`:647-658`) and is taken down by the
  inherited `else { $('endcard').classList.remove('on'); }` on every non-gameover frame,
  i.e. on every seek; the game block shows it with `card.classList.add('on')`
  (`:2359`, matching the `#endcard.on` rule). Beats are `<button>`s with `title`,
  `aria-label` and a click that sends `s:<tick>` (`:2036-2056`), built by `luxBeat`
  (never `chrome_common`'s `markBeat`), and CSS exists for exactly
  `{dusk, research, citylost, end}` (`:1938-1953`) — the same four kinds `runScan`
  emits (`replays.nim:304-326`) and the only four the block draws (`:2432-2438`).
- `#viewpanel` and every zoom/minimap/FPV id is gone from markup, CSS and JS
  (`fork_broadcast_page.py:45-52`, `:56-71`, `:150-219`), asserted at
  `tests/test_lux_viewer.nim:132-145`. Correct per the pin: the board is a fixed
  16×16 grid that `relayout()` fits whole.
- `data-replay-loaded="true"` on `<html>` in the `'loaded'` branch and
  `data-replay-error` in `showFailure` are both the starter's, inherited unchanged
  (`replay-viewer/static_replay.js:14-20`, `:161`), pinned at
  `tests/test_lux_viewer.nim:251-259`.
- Bootstrap/link-flag pairing: `replay-viewer/config.nims` has **no** `MODULARIZE` and
  **no** `EXPORT_NAME`, emits `lux_replay.js` non-modularized, and the Worker waits on
  `Module.onRuntimeInitialized` (`static_replay_worker.js:8`, `:188`, `:192`) and does
  `importScripts('./wire_constants.js', './broadcast_core.js', './lux_replay.js')`
  (`:239`). The `diff` against the starter's four viewer files is identifiers and the
  output name only. `-s ABORTING_MALLOC=1` present. Pinned at
  `tests/test_lux_viewer.nim:261-281`.
- CI proof it *runs*: run 33085620073's `wasm-viewer` job `needs: docker-smoke`
  (`ci.yml:246`), downloads the smoke replay, and its `Load the bundle in a real
  browser` step is green with `{"loaded":true,"ms":605,"clock":"TURN 245 / 360 …"}` —
  a real drawn frame with a real scorebug. `Native <-> wasm hash gate` reported
  `ok: loaded episode.replay, advanced 300 frames (577957 packet bytes, heap 16 MB)`.

**Manifest** — `num_agents: 2` inside `game_config` of all three variants
(`duel`, `skirmish`, `scarcity`) **and** inside `certification.game_config`, and
**absent** at every variant top level (verified by parsing the JSON).
`certification.players == [forester, prospector]`, `len(certification.game_config.players) == 2`.
`game.replay_viewer == {"bundle": "static-replay-viewer"}` under `game`.
`game.docs.readme` is `{"type":"text","value":…}` (6 121 chars) and `game.docs.pages`
is three `{"id","title","content":{"type":"text","value":…}}` entries
(`rules.md`/`protocol.md`/`commanding.md`, 6 475 / 5 172 / 3 282 chars).
`game.protocols` carries both `player` and `global` as objects. `tags` has 6 entries at
the top level and `game.tags` does not exist. `episode_timeout_minutes: 20` at the top
level. `player[].resources.limits.cpu == "1"`. `game.runnable.env.ANTHROPIC_API_KEY_URI ==
secret://coworld/lux-ai/anthropic_api_key` matching `game.name == "lux-ai"`. Every
variant's `wallClockBudgetSeconds == 660`. `tools/build_replay_viewer.sh`,
`tools/ci/docker_smoke.sh` and `tools/ci/check_gameversion.sh` are all mode 100755.
`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows, `docker_smoke.sh` and
`policies.json` returns nothing. No `SEAT-COUNT FAIL` anywhere in the run-33085620073
log (the only `SEAT-COUNT` hits are the four green test names).

**`tools/ci/policies.json`** — four entries, one image, all
`"run": "/bin/lux-ai-player"`: `lux-ai-lumberjack` (`PLAYER_PROMPT`, 1 602 chars),
`lux-ai-nightwatch` (`PLAYER_PROMPT`, 1 730 chars, **distinct**, carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `lux-ai-forester`
(`PLAYER_SCRIPTED=forester`) and `lux-ai-prospector` (`PLAYER_SCRIPTED=prospector`).
`coworld-release.yml` runs Build manifest (`:159`) → Certify locally (`:173`, with
`--timeout-seconds 300` at `:185`) → Upload the policies (`:217`) → Upload the Coworld
(`:315`) → Put the Coworld secret (`:353`), in that order.

**Two name spaces** — `cogAlias` / `slotIdentityIndex` / `IdentityNames` are the
starter's, untouched (`src/lux/roster.nim:16-52`); seats see only `RED-alpha` /
`BLUE-alpha` (`sim.nim:405-449` builds the observation from `cogAlias` alone), while
real names reach `results.names` (`sim.nim:470`), the join records
(`server.nim:371-372`), `roster[].name` (`broadcast.nim:84-100`) and the endcard
(`client/replay_broadcast.html:2364-2370`). `registerRecord` writes the policy label and
kind but never the prompt (`roster.nim:54-66`). `showPlayerLabels` defaults false
(`sim_config.nim:125`). Asserted from both sides in
`tests/test_lux_identity_privacy.nim:11-58` and `tests/test_lux_observation.nim:89-112`.

**Tests** — item 7: `tests/test_lux_baselines.nim:66-79` bounds both baselines over 300
pseudo-random worlds × 2 map sizes × 2 seats against the reply schema and the 512-byte
serialised cap; `tests/test_lux_micro.nim:107-168` asserts full legality (one action per
unit/tile, never for a cooling unit, no off-board or opponent-tile move, no illegal
`build_city`, no unit left undecided) over the same worlds, over 200 random valid
directives, and over a whole 360-turn scripted episode; `test_lux_baselines.nim:101-114`
runs the all-scripted `duel` at the pinned seed to the natural end and asserts
`reason == complete`, `endRule == full_time`, `forester` ahead, and both sides surviving
≥ 6 nights. Item 1's second half: `git log -p -- tests/` shows every test file added in
a single commit (`583e3d6`, 2 759 insertions, 0 deletions) with no `skip`/`xfail`, no
widened tolerance and no deleted assertion anywhere in the run.

**Determinism** — one RNG stream consumed only by the generator
(`board.nim:9-12`, `:234`, asserted at `tests/test_lux_board.nim:64-76`); the float grep
over `{sim,board,units,cities,resolve,scoring,micro,baselines}.nim` runs as a test
(`tests/test_lux_determinism.nim:18-47`) with `scoring.scoreOf` the one documented
boundary; `mixHash64` casts rather than converts, with the wasm32 `RangeDefect` reason
written down (`sim_state.nim:103-108`); `city.fuel`, `resourcesMined` and the episode
totals are `int64` (`cities.nim:15`, `sim_state.nim:27`).

**Design-note copy** — `docs/plans/2026-08-27-lux-ai-design.md` is byte-identical to
`runs/2026-08-27-lux-ai/design.md`.

---

## Could not determine

- **Whether N1 (the lobby-start divergence) is reachable in production.** It needs a
  recorded episode in which both seats' sockets connect after tick 48 (2 s at
  `TargetFps = 24`). What would settle it: run the game with a deliberately delayed
  player start — e.g. `docker_smoke.sh` with a `sleep 5` before the player `docker run`
  loop, or a Nim test that records lobby ticks with `startWaitTicks = 48` and a join at
  tick 60 — then re-derive with `mismatchQuit = true`. I have no docker, no Nim and no
  browser in this sandbox, so I could not run it.
- **The exact rendered width of a 160-rune commander line at 360 px (B1).** My figure
  (~390 px in a 114 px container inside a 360 px `overflow: hidden` stage) is computed
  from `--u = 0.5px`, `font-size: calc(7 * var(--u))`, `letter-spacing: 0.1em` and
  `text-transform: uppercase`; it is not a browser measurement. What would settle it: a
  `getBoundingClientRect()` readout of a `.feed-row` carrying a full-cap note in the
  360 px fixture iframe, compared against `#stage`'s box — which is precisely the
  assertion the fixture does not make.
- **Whether `#viewpanel` was correctly dropped for the `skirmish` 12×12 variant too.**
  Both shipped board sizes are square and `relayout()` letterboxes them whole, so the
  pin's "fixed arena" reading holds for both, but I could not observe the fitted board
  at either size without a browser.
- **Whether the `wasm_replay_smoke.cjs` 300-frame budget covers the whole smoke
  replay.** `ci.yml:365` passes `300`; the smoke episode is ~409 ticks, so the last
  ~100 ticks (including the settle tick and the endcard frame) are not hash-checked by
  that gate. `viewer_smoke.mjs` reached turn 245 in its soak. What would settle it:
  raising the frame budget past `maxTick`, or printing `maxTick` from the smoke.
