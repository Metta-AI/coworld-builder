blocking: 1

# r1 verdict — lux-ai

Head: `66b5d3bb2c5c88d9b947437c1194f180681bc702` (`main`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-decision addendum)
Independent read written before reading fixes: yes (repo, design note, CI run 33090975748 log, starter diffs, and my own checklist pass were all completed before opening `r1-review.md`; `r1-fixes.md` was opened last, only to cross-check claimed commits)

CI evidence: `gh run list -R Metta-AI/cogame-lux-ai --branch main -w ci.yml` → run
**33090975748**, headSha `66b5d3bb…`, conclusion **success**; jobs `test`,
`docker-smoke`, `wasm-viewer` all green, every step green (verified per-step via
`--json jobs`, including `Load the bundle in a real browser`, `Native <-> wasm hash
gate`, `Worst-case chrome fixture`, `The commander line fits its band`). Full log
pulled; `grep 'SEAT-COUNT FAIL'` over it returns nothing (only the four green
`[OK] the four SEAT-COUNT invariants…` test names match `SEAT-COUNT`).

---

## Standing blocking findings

- [correctness] src/lux/replays.nim:125 replay playback auto-starts the game at `startWaitTicks` (48) because `simFromReplay` marks both seats joined at construction, so any episode whose seats connect later than 2 s after loop start (the design note's own "typical 12 s" connect wait) records a replay that does NOT re-derive — falsifies item 2.

### B-J1 — lobby-start divergence: recorded lobby length is ignored by playback (source: judge, elevating the reviewer's N1)

- Where:
  - `src/lux/replays.nim:119-131` — `simFromReplay` sets `seats[seat].joined = true`
    for every join record **regardless of the tick it was recorded at**:
    ```nim
    for join in data.joins:
      ...
      result.seats[seat].joined = true
    ```
  - `src/lux/sim.nim:164-172` — `sim.step()`'s `Lobby` branch auto-starts:
    ```nim
    of Lobby:
      let joined = sim.seats[0].joined and sim.seats[1].joined
      if (joined and sim.tickCount >= sim.config.startWaitTicks) or
          sim.tickCount >= sim.config.lobbyJoinTimeoutTicks:
        sim.beginPlaying()
        sim.stepPlaying()
    ```
    Playback calls `sim.step()` every tick (`replays.nim:219-227` `stepReplay`), so
    with both joins present the re-simulation begins Playing at tick 48 — always.
  - `src/lux/server.nim:484-502` — the **live** server never calls `sim.step()` in
    `Lobby`; it ticks the lobby itself at `TargetFps` 24 and emits `InputStart`
    only when `joined and tickCount >= startWaitTicks`, i.e. at tick
    `T = max(48, first tick with both seats connected)`.
  - `src/lux/sim.nim:103-105` — `beginPlaying` returns early once `phase != Lobby`,
    so the recorded `InputStart` at tick T is a no-op in a playback that already
    started at 48.
- Verified at head: if both seats connect at, say, 12 s (tick ≈ 288 — the design
  note §Decisions line 410 calls 12 s the **typical** connect wait; the 100 s
  `lobbyJoinTimeoutTicks` cap exists precisely because late joins are expected),
  the live server records lobby hashes (`sim.nim:186-191`, the `mixHash(-1,
  tickCount)` form) for ticks 48..287 while playback's world is already stepping
  turns from tick 48. `checkReplayHash` (`replays.nim:200-217`) flags the first
  divergence at tick 49. Worse than a warning: the directive **input records** are
  applied by recorded tick (`applyRecordsAt`, `replays.nim:170-197`) into a world
  that is `T-48` ticks ahead, so every directive installs at the wrong turn and the
  re-simulated game genuinely diverges from the one played — the viewer then shows
  a different game under `#mmwarn`.
- Not fixed this round: none of the five fix commits (`e673713`, `db780f6`,
  `7e8a89e`, `27d10f6`, `66b5d3b`) touches this path; `r1-fixes.md` explicitly
  declines it ("N1 … not in this round's scope").
- Not covered by any test or CI artifact: `tests/helpers.nim` sets
  `startWaitTicks = 0` for every fixture; `tests/test_lux_replay.nim:32-33` writes
  `InputStart` at tick 0; docker-smoke's players connect inside 2 s (its replay
  passed the hash gate), so CI green is not evidence against this.
- Checklist item: **2 — Replay re-derivation.** "Replaying the recorded events
  through the sim reproduces the recorded per-tick state frame by frame." At the
  current head that property holds only when both seats join inside
  `startWaitTicks` (2 s); for the design note's own typical timing it is false.
  The lobby length is recorded (`InputStart` at tick T) but playback pre-empts it.
- What would fix it: make playback honor the recorded start — e.g. gate the
  `Lobby` auto-start on join **ticks** (apply `joined` at the recorded join tick in
  `simFromReplay`/`applyRecordsAt`) or suppress the auto-start when an `InputStart`
  record exists and start only when it is applied — plus a test that records a
  fixture with `startWaitTicks = 48` and joins at tick > 48 and asserts
  `hashMismatchTick == -1`.

---

## Refuted / resolved reviewer findings

### B1 — worst-case renderer fixture produced no text-fit evidence; the 160-rune note had no band → FIXED AT THIS SHA
- Evidence at `66b5d3b`:
  - `client/replay_broadcast.html:1846` `--lux-note-runes: 160` and
    `:1868-1877` `.feed-row.lux-say { … white-space: normal; overflow-wrap:
    anywhere; min-height: var(--lux-say-band); width: 100% }` — a reserved band
    derived from `MaxNoteRunes` and the badge's own font metrics;
    `#killfeed` `min-height: calc(3 * 20 * var(--u) + var(--lux-say-band))`
    (`:1866`) holds the band whether or not anyone is speaking. The page still
    regenerates **byte-identically** from the starter mount — I ran
    `python3 scripts/fork_broadcast_page.py /workspace/starters/coworld-ctf
    /tmp/forked.html && cmp` myself: IDENTICAL.
  - `tools/ci/renderer_fixture.html` now reads each commander line back out of the
    iframe DOM (`runeCap(NOTE_A, NOTE_RUNES)` fed; `entry.runes !== NOTE_RUNES`
    → `short`; `getBoundingClientRect` vs `#stage`; throws reject into
    `data-replay-error`) and prints one `LUX-TEXTFIT {json}` line.
  - `.github/workflows/ci.yml:402-446` — new step `The commander line fits its
    band` parses that line and fails on missing measurement, `note_runes != 160`,
    `widths != 3 or notes < 6`, any `short`/`outside`/`clipped`, any
    `chrome_off_stage`, or any `failures[]`.
  - Run 33090975748 log line 5525: `text fit: {"chrome_off_stage": 0,
    "chrome_outside": 1, "clipped": 0, "failures": [], "measured": 48,
    "note_runes": 160, "notes": 12, "outside": 0, "short": 0, "widths": 3}` and
    line 5529 `commander band OK: 48 boxes measured, 12 full-cap notes inside
    #stage at 360/620/1280 px`.
  - The `canvas_text` line (same job, `Worst-case chrome fixture` step, log 5472):
    `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` — structurally
    zero because every drawn string in this viewer is DOM; the DOM text-fit step
    above is the checklist's "or equivalent text-fit" evidence and it gates.
- B1 no longer stands.

### N2 — one-entry Bedrock ladder → FIXED AT THIS SHA
- `src/lux/llm.nim:83-84` at head:
  `@["us.anthropic.claude-haiku-4-5-20251001-v1:0",
  "us.anthropic.claude-sonnet-4-5-20250929-v1:0"]` — two candidates,
  `tryNextBedrockModel` (`:86-94`) can rotate; `sonnet-4-6` still excluded;
  `BEDROCK_MODEL` still pins one. Commit `db780f6`, CI success.

### N4 — four declared config knobs not read by the sim → FIXED AT THIS SHA
- `src/lux/sim_state.nim:45-57` adds config-aware `cargoCap(world, kind)` /
  `baseCooldown(world, kind)`; `src/lux/resolve.nim:122,129,169,269,300,323` and
  `src/lux/micro.nim:315` call them; the city build charges
  `baseCooldown(world, ukWorker)` (`resolve.nim:169`) instead of the literal 20;
  the guard checks `cargoCap(world, unit.kind)` (`sim_state.nim:191`). Two new
  test cases (`tests/test_lux_resolve.nim:388-431`) fail against the constants.
  Defaults seed from the same constants, so the hash chain and GameVersion are
  untouched — confirmed by the green determinism/replay tests and the identical
  tuner pick in the head run.

### N14 — tautological 9 KB-reply test → FIXED AT THIS SHA
- `tests/test_lux_directives.nim:84-105`: `check (recovered or true)` is gone,
  replaced by `check reason.startsWith("no JSON object in reply")` (the cut-open
  remainder fails as a classified `DirectiveError`) plus
  `check parse(survivor).stance == stFuel` (an object that closes inside the cap
  parses). Strictly stronger; not a loosening (hunks read).

### N16 — timing test asserted the note's arithmetic, not the code's → FIXED AT THIS SHA
- `tests/test_lux_engine.nim:31-58`: asserts the code's worst turn
  (`turnSpacingMs + attempt1Ms == 13000`, `> turnBudgetMs`), `36 × 13 = 468 s`,
  `468 + 3 + 100 + 20 < 660`, and the new, stronger overshoot bound
  `wallClockBudgetSeconds + worstTurnMs div 1000 <= 720`. The replaced
  `<= 720` line was weaker; this is a strengthening. I verified the code
  arithmetic myself from `decide.nim:146-238` and `server.nim:475` (top-of-loop
  stop check): 660 + 13 = 673 s ≤ 720 s = 60 % of 1200. Item 5 holds.

### Reviewer non-blocking findings verified as accurate-but-advisory at head
(none falsifies a checklist item; spot-verified, not merely accepted)
- **N3** — `episodeFinished` (the `gameOverTicks` hold) is unused by
  `server.nim`; the smoke replay is ~409 ticks ⇒ ~27 s of playback, still past
  `--soak 10` (soak advanced 3→243 in the head run). Advisory.
- **N5 / N6** — micro rule-order deviations from the note (hand-off before night
  policy; `build:"city"` idles a tile before research). Real, read at
  `micro.nim`; they change scripted play, not legality — `test_lux_micro`
  legality and the full-episode `complete`/`full_time` tests pass, so items 7/8
  are unaffected. Design-note deviations, advisory.
- **N13** — `llm.nim:201-202` caps the reply at 4096 **runes** where the note
  says bytes (up to ~16 KB kept for multi-byte). Rune-safe, never splits a
  codepoint; item 9 unaffected. Advisory.
- **N15** — several note-specified engine tests are structural rather than
  behavioural (parallel batch asserted from source text; no hung-client test).
  Item 8's behaviour is present in `decide.nim:212-271` (exactly one retry,
  throttled fail-fast, fallback recorded with cause + `fallbackTurns` counted);
  the checklist does not require those specific tests. Advisory.
- **N17 / N18 / N19, N7–N12** — size estimate, `tokens` omission (safer reading,
  documented at site), speed-chip transcription, missing forensics tools, art
  substitution, byte-identical `broadcast_core.js` (a third documented
  `CTF_WIRE` site, whitelisted by the test): all confirmed as observed and all
  outside the checklist. Advisory.
- **N1** — accurate, and elevated to blocking above (B-J1): the reviewer's own
  text says "if this path is reachable it would falsify checklist item 2"; I
  verified reachability from the design note's own typical-timing arithmetic and
  the code, so it counts.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 33090975748 conclusion `success` on `main` at `66b5d3b`; `git log -p --since=2026-08-27T12:45:00Z -- tests/` read hunk-by-hunk: 3 assertion lines removed (`test_lux_engine.nim` `<=720` → stronger overshoot bound; `test_lux_directives.nim` tautology `(recovered or true)` → 2 real assertions; one `check` moved intact); no skip/xfail, no widened tolerance, no test file removed; +4 new tests |
| 2 Replay re-derivation | **FAIL (B-J1)** | test exists and is real (`tests/test_lux_replay.nim:88-133` re-derives every hash for `full_time`/`wall_clock`/`sim_fault`; viewer runs the same `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket` via `replay-viewer/lux_replay.nim`), but playback ignores the recorded lobby length — `replays.nim:125` + `sim.nim:164-172` vs `server.nim:484-502`; diverges for any join later than tick 48 |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}` (parsed); `tools/build_replay_viewer.sh` present, mode 100755, is the `coworld build` hook (CI asserts the bit, ci.yml:259-270); shell/worker fetch nothing but the replay URL (`static_replay_worker.js:113` is the only `fetch`); no pod viewer declared |
| 4 Both name spaces | PASS | `roster.nim:16-52` `cogAlias` = `RED-alpha`/`BLUE-alpha` untouched; real names only in `results.names`/joins/roster/endcard; `tests/test_lux_identity_privacy.nim` asserts both directions; head-run viewer smoke scorebug shows alias + name |
| 5 Degrade-never-hang | PASS | every wait bounded: `attempt1Ms`/`retryMs` via `CURLOPT_TIMEOUT` (`decide.nim:237-238`), turn budget checked per attempt (`:216`), spacing sleep capped (`:203-206`), rate guard (`:180`), budget guard (`:154-164`), lobby capped (`server.nim:486-487`), wall-clock stop at loop top (`:475`), bounded 20 s grace then `quit(0)` (`:538-545`); worst case 660+13 = 673 s ≤ 720 s, asserted in `test_lux_engine.nim:31-58` |
| 6 num_agents | PASS | `num_agents: 2` in `game_config` of `duel`/`skirmish`/`scarcity` and `certification.game_config` (parsed manifest); absent at variant top level; `docker_smoke.sh:106-152` enforces all four invariants + `SMOKE_SEATS` cross-check with `SEAT-COUNT FAIL:` exits; no `SEAT-COUNT FAIL` in the head-run log |
| 7 Scripted baseline full episodes | PASS | `tests/test_lux_baselines.nim:106-116` all-scripted duel to natural end, `reason == erComplete` / `erlFullTime`; legality over 300 worlds + 200 random directives + a full episode in `test_lux_micro.nim`; tuning is the swept pick (`tools/tune_baselines.nim --check` green as its own CI step); docker-smoke: `replay summary ok: complete full_time [18, 1] 360 turns` |
| 8 LLM reply handling | PASS | tolerant extraction `directives.nim:148-187` (fences, prose, first/last-brace rescue); exactly one retry (`decide.nim:213 while attempt < 2`); fallback = the forester proc (`:65-68`, pinned by test); every fallback recorded with cause + `fallbackTurns`/`llmTurns` counted (`:191,197,278,285`); "falling back"/"LLM provider is unavailable" phrases present for phase 60 |
| 9 Rune-safe truncation | PASS | single cut point `truncateRunes` (`directives.nim:75-82`, `runeLen`/`runeSubStr`); 4-byte-emoji-at-cap tests for note/policy/detail/prompt/how-it-went (`test_lux_directives.nim:107-133`) and a full replay through `replay_summary.py` under strict UTF-8 (`test_lux_replay.nim:215+`); CI step `The replay summarises as strict UTF-8 JSON` green |
| 10 Manifest validates | PASS | parsed: `game.docs.readme {type:text,value 6121 ch}` + 3 pages `{id,title,content{type:text,value}}`; `game.protocols` has both `player` and `global` |
| 11 Legible at 360 px | PASS | `replay_broadcast.html:1779-1784` `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`; `:2045-2048` `@media (max-width: 640px)` hides labels |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:159) → Certify (:173, `--timeout-seconds 300`) → Upload policies (:217) → Upload coworld (:315) → Secret put (:353); all three workflows present; `docker_smoke.sh` 100755; `policies.json` 4 distinct policies, 2 `PLAYER_PROMPT` champions, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; placeholder grep over the 5 files exits 1 (no matches) so the gate exits 0; smoke builds its image in-run (ci.yml:183) |
| 13 Viewer executes | PASS | run 33090975748 `wasm-viewer` green incl. step `Load the bundle in a real browser` (log 5427: `{"loaded":true,"ms":552,…}`, soak advanced 3→243, `Native <-> wasm hash gate` ok); `needs: docker-smoke` (ci.yml:246); no `continue-on-error` anywhere; `data-replay-loaded` set in the `'loaded'` branch (`static_replay.js:161`), `data-replay-error` in `showFailure` (`:14-20`); `config.nims` has no MODULARIZE/EXPORT_NAME and the worker waits on `Module.onRuntimeInitialized` (`static_replay_worker.js:188`) — all four viewer files diff against coworld-ctf as identifier renames only (one starter, consistent pair) |
| 14 Chrome is the starter's | PASS | `client/chrome_common.js` and `client/broadcast_core.js` byte-identical to the starter (diffed myself); `replay_broadcast.html` regenerates **byte-identically** from the starter mount via `scripts/fork_broadcast_page.py` (ran + `cmp`: IDENTICAL) — deletions are the note's named removals, one appended block under the banner at line 1753; `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (`:1698,1719-1725`); `#endcard { bottom: var(--band, 0px) }` (`:658`), dismissed by the inherited seek path (`:1540`); beats are labelled `<button>`s that seek (`luxBeat`, `:2094-2115`) with CSS for exactly `{dusk, research, citylost, end}` (`:1996-2011`); `#viewpanel`/minimap/zoom/FPV removed from markup, CSS and wiring (only prose comments survive) — correct for a fixed 16×16 arena |
| 15 Every drawn string fits | PASS | `--strict-text-bounds` on both smoke steps; main smoke `canvas_text` total 0 is structural (all text is DOM) and is therefore not the evidence — the evidence is the worst-case DOM fixture: `Worst-case chrome fixture` + `The commander line fits its band` steps (ci.yml:374-446), full-cap 160-rune notes on both seats at 360/620/1280 px, band reserved from `MaxNoteRunes` in the render font (`replay_broadcast.html:1846-1877`), fixture asserts its own strings full-length; head run: `note_runes 160, notes 12, widths 3, short 0, clipped 0, outside 0, chrome_off_stage 0, failures []` |
| addendum: one parallel batch | PASS | `decide.nim:223-238` — one `RequestBatch`, one `client.curl.makeRequests(batch, …)` for all open seats per turn; asserted structurally in `test_lux_engine.nim:170+` |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed in `e673713` (band + fixture assertions + CI gate; shim ordering bug found) | code + CI step + head-run text-fit line all confirm; page still regenerates from starter | yes |
| N2 | fixed in `db780f6` | two-model ladder at `llm.nim:83-84` | yes |
| N14 | fixed in `7e8a89e`, "no assertion weakened" | hunk read: tautology → 2 real assertions | yes |
| N16 | fixed in `27d10f6`, stronger bound added | hunk read: `<=720` → overshoot-inclusive bound; arithmetic matches the code | yes |
| N4 | fixed in `66b5d3b`, no behaviour change at defaults | config-aware procs wired at all cited sites; 2 regression tests added | yes |
| N1 et al. | "not fixed … none of them falsify a checklist item" | **disagree on N1**: it falsifies item 2 for the design note's own typical connect timing (elevated as B-J1 above); the rest verified advisory | no (N1 only) |

## Non-blocking observations (advisory, mine)

- The reported `chrome_outside: 1` in the text-fit gate is the right-hand
  `.plate-name` partially clipping at the extreme 360×203 letterbox — a direct
  tension with item 11's mandated `min-width: 3.2em`. Reported-not-gated is the
  right call; worth a look in a later pass.
- A budget-exhausted seat writes two `fallback` chat records for one turn
  (`decide.nim:218,285`); `fallbackTurns` counts once. Cosmetic replay noise.
- `wasm_replay_smoke.cjs` runs 300 frames against a ~409-tick smoke replay, so
  the settle tick is hash-checked only by the browser smoke, not the node gate.

## Could not verify (and why it does not add to the count)

- Hosted-timing reproduction of B-J1 (no docker/Nim/browser in this sandbox). The
  finding is established from the code at head plus the design note's own timing
  arithmetic, which is the tree evidence the checklist rule asks for — it is
  counted above as blocking, not as unverifiable. No checklist item was left in
  an unverifiable state: every item has tree or cited-CI evidence above.

BLOCKING: 1
