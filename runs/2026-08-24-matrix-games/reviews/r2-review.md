# r2 review — matrix-games

Repo: `Metta-AI/cogame-matrix-games` at `af5c7043d4a4fbca3eb5f4c230901f6d9fb4dfe7`
(fresh clone at `/tmp/r2-matrix-games`; `git log --oneline -1` → `af5c704 F66: validate
results.json against game.results_schema in docker_smoke.sh`). Round 1 reviewed `7b7d586`;
the 15 commits in `7b7d586..af5c704` are the subject of this round.
Design note: `/workspace/coworld-builder/runs/2026-08-24-matrix-games/design.md`.
Starters mounted for provenance: `/workspace/starters/coworld-ctf`,
`/workspace/starters/cogame-bullwhip`.
Prior round: `reviews/r1-review.md` (71 findings), `reviews/r1-verdict.md` (`BLOCKING: 1`).

Every finding is marked **match**, **gap** or **unclear** and cites `file:line`.
*Observed* = I read it. *Inferred* = I reasoned from code I read. *Ran* = I compiled and ran it
locally at this sha (Nim 2.2.4 from `/root/.nimby`, `nim.cfg` regenerated exactly as `ci.yml`
does; the probe file was deleted afterwards and nothing was committed or pushed).
No fixes are proposed. I did not read `r1-fixes.md`.

**Counts: 17 match · 11 gap · 8 unclear (36 findings).**

---

## A. The fifteen fix commits

### F1 — F8 (`1e1593a`): the tick-0 `leadchange` is gone — **match**
- Where: `src/matrix_games/sim_state.nim:120-126` (`result.lastLeader = 0`, with the reason in
  the doc comment).
- Observed + **ran**. The seed is now the opening leader (all scores 0 → `leader()`
  ties to slot 0, `sim_state.nim:236-240`), so rule 9 (`sim.nim:148-154`) no longer fires at
  `t = 0`. I played a 6-beat PD episode at seed 7 with the cert seat mix and counted the
  `leadchange` records: **0 at tick 0, 4 in total** — the fix removes the spurious marker without
  suppressing real lead changes.
- No consumer regresses: the viewer's own timeline fold starts from `lastLeader = -1`
  (`src/matrix_games/global.nim:141`) and falls back to `max(0, lastLeader)` for the terminal
  `over` row (`global.nim:163-165`), so a replay with no `leadchange` at all still emits a legal
  `over` row. Nothing reads a tick-0 lead change (`grep leadchange` over `src/` and
  `client/replay_broadcast.html`).
- No regression test was added for this one; the property is verified only by the run above.

### F2 — F34 (`b178474`): the echoed prose head is cut on runes — **match**
- Where: `src/matrix_games/llm.nim:335-340` — the byte slice is replaced by
  `cleanText(text, 160)`; `cleanText` is the rune-boundary cut at
  `src/matrix_games/sim_types.nim:228-238`.
- Observed. Test at `tests/test_llm.nim:34-42` feeds `repeat("\u4e2d", 300) & " sorry, no
  object"` and asserts `validateUtf8(error.msg) == -1` and `error.msg.runeLen <= 200`
  (160 runes + the 27-char prefix). CI log line `[OK] the echoed head of a prose reply is cut on
  runes, not bytes`. This was the one non-rune truncation r1 found; the tree now has none.

### F3 — F23 (`8cf9ffb`): a 401/403 disabling the client is now tested — **match**
- Where: `tests/test_llm.nim:223-245`; the behaviour under test is
  `src/matrix_games/llm.nim:444-448` (`client.disabled = true` then raise).
- Observed. The test hands `Response(code: 401)` and `Response(code: 403)` straight to
  `client.textOf` — the path the batch hook short-circuits — asserts the raise, asserts
  `client.disabled`, then calls `decideAll` and asserts `client.batchSizes.len == 0` and
  `source == osFallback` for all eight seats. `skNone` is the zero value of `ScriptKind`
  (`sim_types.nim:112-118`), so `newSeq[ScriptKind](Seats)` really does mean "eight LLM seats".
  CI log: `[OK] a 401 or a 403 disables the client for the rest of the episode`.
- The production wrapper is still correct: `runBatch` calls `textOf` inside a `try/except`
  (`llm.nim:494-500`), so the flag is set before the error is turned into a `BatchReply`.

### F4 — F29 (`220aa5c`): the connect wait is counted in the deadline arithmetic — **match**
- Where: `src/matrix_games/sim_config.nim:91-103`, the new constant at
  `src/matrix_games/sim_types.nim:91-94` (`RegistrationGraceSeconds* = 3`), its use at
  `src/matrix_games/server.nim:179-180`, and the stamp comment at `server.nim:162-167`.
- Observed. `validate()` now requires
  `playerConnectTimeoutSeconds + RegistrationGraceSeconds + beats × 2 × llmTimeoutSeconds ≤
  0.6 × episodeTimeoutSeconds`: 180 + 3 + 480 = **663 ≤ 720** at the shipped defaults, and
  180 + 3 + 240 = 423 for the certification fixture (`beats: 6`), which is why the smoke still
  starts (CI log line `game=matrix-games seats=8 config={… "beats": 6 …}`). The `gameStart`
  stamp stays before the connect wait, which is the stronger reading of the note's
  "settles inside 60 % of `episodeTimeoutSeconds`" (design.md:279, 317-319).
- Residue (not a separate finding): the raise message hardcodes the literal `+ 3`
  (`sim_config.nim:101`) while the value comes from the constant, so a change to
  `RegistrationGraceSeconds` would leave the message stale.

### F5 — F29 side effect: schema-legal configs now fail at startup — **unclear**
- Where: `src/matrix_games/sim_config.nim:97-99` vs `coworld_manifest_template.json`
  `game.config_schema.properties.beats` (`minimum: 1, maximum: 24`) and
  `playerConnectTimeoutSeconds` (`minimum: 0, maximum: 600`); the consequence is
  `src/matrix_games.nim:45-48` (`quit("matrix-games: invalid game config: …", 2)`).
- Observed + inferred. The tightened bound rejects configs the old one accepted: at the other
  defaults, `beats` in **14…18** (`beats × 40` ∈ (537, 720]) used to validate and now exits 2
  before the server starts. No shipped variant is affected — all seven use `beats: 12`
  (`variants[*].game_config`) and the cert fixture uses 6 — so this is latent, not live.
  Whether `validate()` is required to accept every config the published `config_schema` permits
  is not settled by the design note; the note only pins the 12-beat arithmetic
  (design.md:307-313).

### F6 — F32 (`f082554`): the beat loop is guarded and settles as `deadline` — **match**
- Where: `src/matrix_games/server.nim:238-264` (the `try` opened above the beat loop, the
  `except CatchableError` at `:262-264` calling `gameSim.finish("deadline", "deadline")`).
- Observed. On a caught raise the code falls through to `if not gameSim.done` (`:265`),
  `pushStateFrames()` (`:267-270`) and `finishEpisode` (`:271`), so both artifacts are written
  and `quit(0)` (`:278`) is reached. `deadline` is one of the three legal reasons
  (`sim_types.nim:89`, design.md:282), so `results.json` stays schema-valid. Note that an
  internal failure is therefore indistinguishable in `results.reason` from a slow-LLM deadline —
  the log line at `:263` is the only discriminator.

### F7 — the F32 guard catches `CatchableError`, not Defects — **gap**
- Where: `src/matrix_games/server.nim:262` (`except CatchableError as error:`); build flags at
  `Dockerfile:43` and `:46` (`nim c -d:release …`, no `--panics:on`).
- Observed + **ran**. In Nim 2.2.4 a `Defect` (`IndexDefect`, `RangeDefect`, `NilAccessDefect`)
  derives from `Exception`, not `CatchableError`. I compiled two probes with `-d:release`: an
  out-of-range index is **not** caught by `except CatchableError` (`Error: unhandled exception:
  index 7 not in 0 .. 2 [IndexDefect]`, exit 1), and the same defect raised inside a
  `createThread` worker terminates the **whole process** (exit 1; the main thread's later
  `echo` never runs).
- So the guard covers the raise class the commit message names, but a defect on the beat thread
  still ends the episode with no artifacts. The failure mode differs from the one r1's F32
  described: the container exits non-zero rather than sitting healthy-looking forever. I have no
  concrete defect-raising path on the live beat path to name — the arithmetic is integer and the
  indices are bounded by `Seats`/`k` — so this is a statement about the guard's scope, not a
  claim that it fires.

### F8 — `finishEpisode` sits outside the F32 guard, though the commit names `resultsJson` — **gap**
- Where: the `try` block ends at `src/matrix_games/server.nim:264`; `finishEpisode` is called at
  `:271`, and it calls `resultsJson` (`:138`), `replayBytes` (`:139`) and `writeArtifact`
  (`:153-156`). `writeArtifact` can raise: `raise newException(IOError, "artifact POST failed: "
  & $response.code)` at `server.nim:92`.
- Observed. The commit message for `f082554` states the loop is guarded because "a raise out of
  installOrders, runBeat, buildObservation **or resultsJson** would have killed the thread"; the
  guard as written does not cover `resultsJson`, `replayBytes` or the artifact POST, all of
  which run after the `except`. A non-2xx artifact POST therefore still terminates the game
  thread (and, per F7's experiment, the process) before `quit(0)`. Behaviour here is unchanged
  from `7b7d586` — this is an incompleteness of the fix relative to its stated scope, not a
  regression it introduced.

### F9 — F59 (`839653d`): the `/client/replay` route is gone — **match**
- Where: `src/matrix_games/server.nim:437-446` — the router now registers `/healthz`,
  `/client/player`, `/client/global`, `/client/@name`, `/replay-data`, `/global` and (live mode
  only) `/player`. `replayPageHandler` is deleted; the header route table at `server.nim:8-18`
  no longer lists it. The two links are rewritten: `client/global.html:36-41`,
  `client/player.html:37-41`.
- Observed. `grep -rn "/client/replay"` over the tree returns only:
  `.github/workflows/coworld-release.yml:201` (an error message),
  `coworld_manifest_template.json:414` and `docs/GLOBAL.md:32` (both saying there is none),
  `tests/test_manifest.nim:65` (asserting its absence), and the stale comment in F11.
  The route list now matches the design note's own table (design.md:638-646).

### F10 — the same page is still served by the pod under its filename — **unclear**
- Where: `src/matrix_games/server.nim:305-320` (`clientAssetHandler`, which serves any
  non-traversing name out of `clientDir()` and maps `.html` to `text/html`), registered at
  `:444`; `Dockerfile:62` copies the whole `client/` directory into the runtime image.
- Observed + inferred. `GET /client/replay_broadcast.html` off the game container still returns
  the broadcast page (and the page's own loader at `client/replay_broadcast.html:1586` resolves
  its scripts against `/client/` in exactly that case). The literal path checklist item 3 names
  is gone; whether serving the same document under its asset name counts as "a `/client/replay`
  pod path" is not settled by the note, which lists `/client/<asset>` as a legitimate route
  (design.md:645-647). Recorded as observed; I am not adjudicating it.

### F11 — dead `/client/replay` reference left in the page — **gap**
- Where: `client/replay_broadcast.html:1574-1576`:
  `// … A raw /client/replay open off the game server has no splice, so pull the same // files
  in by src and re-enter once they are up.`
- Observed. The comment names a route that no longer exists. The code it explains
  (`:1577-1596`, the `mgMissing` script-loading fallback and its `location.pathname.indexOf(
  '/client/') === 0` base-path branch) is now reachable only through the asset path of F10.

### F12 — F50 (`786db23`): the foreign `.ev-lane` CSS is gone and the inherited region is clean — **match**
- Where: `client/replay_broadcast.html` lines 1-1324 (everything above the CSS banner at
  `:1325`).
- Observed. `grep -n 'ev-lane\|\.ev\.\|ev-tip'` over the page returns nothing. I diffed the
  whole inherited CSS region against the starter's (`/workspace/starters/coworld-ctf/client/
  replay_broadcast.html` lines 1-1459): the only remaining deltas are the `<title>`, the
  `#killfeed` band fix (`:476`, `bottom: calc(var(--band, 0px) + 40 * var(--u))`, the direction
  checklist rule 14(b) wants), the `#viewpanel`/`#minimap`/`#zoombar`/`#zoom-*` removal the note
  lists (design.md:757-760), and the appended banner. cogame-raid's vocabulary is fully removed.

### F13 — F51 (`3c0aa54`): feed rows and banner chips use styled classes — **match**
- Where: `client/replay_broadcast.html:1871` (`row.className = 'feed-row'`) and `:1893`
  (`chip.className = 'banner-chip'`); the rules they now hit are the inherited
  `.feed-row` (`:489-523`) and `.banner-chip` (`:448-465`).
- Observed. Both selectors exist and neither requires child structure the game block omits
  (`.feed-row .who/.glyph/.badge` are optional refinements), so a `textContent`-only row gets
  the tinted plate, the pixel font and the size. Test at `tests/test_viewer.nim:228-236` checks
  both rules and both call sites. CI log: `[OK] feed rows and banner chips use classes the
  stylesheet actually styles`.

### F14 — the feed's legibility is still unverified by any gate — **unclear**
- Where: `client/replay_broadcast.html:489-503` (`.feed-row` is `white-space: nowrap`,
  `max-width: none`) inside `#killfeed { width: calc(228 * var(--u)) }` (`:470-488`); the row
  text is built at `:1824-1856` and can carry a 64-rune `say` (`ASH: gather cooperate  "…"`).
  Harness side: `tools/ci/viewer_smoke.mjs:286` selects the feed as `#feed, .feed, #log`.
- Observed + inferred. This page's feed is `#killfeed`, which none of those selectors match, so
  the smoke's `"feed_lines": 0` in run 32755082249 is a selector miss, not evidence the feed was
  empty — no CI artifact shows a populated feed at any width. A nowrap row wider than 228 `--u`
  grows leftward inside a right-anchored column; at 360 px `--hudscale` clamps to 0.5
  (`:2163-2164`), so the row draws at ~4 px type, which I cannot measure by reading. r1 recorded
  the same question about the then-unstyled rows; the styling is fixed, the measurement is not.

### F15 — F54 (`6e0178a`): `.tiny` now fires under 640 px — **match**
- Where: `client/replay_broadcast.html:2168` (`stage.classList.toggle('tiny', width < 640)`),
  the rules it drives at `:1455-1465` (`#stage.tiny .plate.mg .plate-enc/.plate-name/
  .plate-camp { display: none }` and the `#mg-matrix`/`#mg-indices`/`#mg-legend` reductions),
  and `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow:
  ellipsis; }` at `:1353`.
- Observed. `--hudscale`, `--band` and `--topband` are still set on `document.documentElement`
  (`:2164-2172`). The comment above `mgRelayout` (`:2149-2160`) now states plainly that this is
  a single pass delegating the board fit to `mgCore.setViewportFit()`, not the starter's
  four-pass letterbox — the claim r1's F54 contradicted.

### F16 — a stale `620` comment survives the F54 change — **gap**
- Where: `client/replay_broadcast.html:1451-1454`: `/* … relayout() toggles #stage.tiny at
  boardW <= 620; these are the three rules the game block adds on top. */`
- Observed. The threshold is 640 (`:2168`). The fix updated the comment above `mgRelayout` but
  not this one, so the stylesheet now documents the old number.

### F17 — F64 (`cb2430a`): the soak runs — **match**
- Where: `.github/workflows/ci.yml:305-317` (`--soak 10` between `--replay` and `--timeout 90`),
  gate at `tools/ci/viewer_smoke.mjs:387` (`if (loaded && args.soak > 0)`), three-sample logic at
  `:389-414`.
- Observed. CI run **32755082249** (`gh run list -R Metta-AI/cogame-matrix-games --branch main
  -w ci.yml`, push, headSha `af5c704…`, conclusion `success`) prints
  `{"loaded":true,"ms":559,…}` and `soak: 10s of playback kept advancing ("5 / 300" -> "197 /
  300" -> "245 / 300")` in the `Load the bundle in a real browser` step. `wasm-viewer` still has
  `needs: docker-smoke` (`ci.yml:212`) and no step carries `continue-on-error`.

### F18 — the three scrub readouts are printed, never gated — **gap**
- Where: `tools/ci/viewer_smoke.mjs:430-446` (the `scrub` array; the `0%` entry at `:432` is the
  **current** readout, not a seek) and the exit condition at `:483`
  (`if (!loaded || playFailure || boundsFailure)`).
- Observed. design.md:1065-1067 makes "three different clock readouts at 0 %, 50 % and 100 %"
  half of the pass condition; the harness collects them and prints them, and nothing compares
  them. With `--soak 10` now on, the `0%` sample is the post-soak playback position, which is
  why the run log reads `0%="BEAT 5 / 6 TICK 245 OF 300"  50%="… TICK 167 …"  100%="… TICK 299
  …"` where the pre-soak run read `TICK 5`. In this run the three do differ, so the note's
  property holds empirically — it is simply not enforced. The file is the coworld-builder
  template's, not this repo's authorship (see F19).

### F19 — `viewer_smoke.mjs` no longer matches the template; no text-bounds instrumentation — **gap**
- Where: `tools/ci/viewer_smoke.mjs` (this repo) vs
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs`. `diff` shows the template
  has since gained the canvas text-bounds hook (`--strict-text-bounds`, the `canvas_text:
  {total, outside, never_inside, ellipsized}` summary and the `fillText`/`strokeText` wrappers);
  the repo's copy has none of it, and `ci.yml:313-317` passes no `--strict-text-bounds`.
- Observed. The template change is coworld-builder commit `4709caa` ("viewer smoke: measure text
  against the canvas it is drawn on"), dated **2026-08-24T17:23:09Z** — about 13 minutes after
  this head's CI run (17:10Z) and after the fifteen fixes landed. The same commit is the one
  that added checklist item 15 to `prompts/30-review-loop.md`. design.md:985 says
  `tools/ci/viewer_smoke.mjs` is "copied with no substitutions", which was true when it was
  copied and is now stale.
- Relevant context, observed: `grep -rn 'fillText\|strokeText' client/ replay-viewer/` returns
  **nothing** — this viewer draws no text on the canvas at all. The board canvas draws sprites
  (`client/broadcast_core.js:5`, "this file draws the WORLD"); every string a spectator reads —
  the scorebug plates, `#mg-matrix`, `#mg-indices`, and the feed rows that carry the model's
  `say` (`client/replay_broadcast.html:1851`) — is DOM text laid out by CSS. So the template's
  instrumentation would report `total: 0` on this page.

### F20 — F47 (`8a1b119`): the viewer packet is compared to the sim state, tick by tick — **match**
- Where: `tests/support/helpers.nim:38-51` (`tickSnapshot`), `:53-75`
  (`runScriptedRecording`), `tests/test_viewer.nim:123-167`.
- Observed + **ran**. For every tick and all eight seats the test compares the wasm packet's
  board block (`c` quad, `inv`, `sc`), the chrome `seats[]` (position, facing, `frozen`,
  `scoreCp`, `inv`, and the event-folded `interactions`) and the per-spawner `tok` map against
  the sim's own state captured after that tick. The path under test is the one the wasm entry
  calls (`replay-viewer/matrix_games_replay.nim` → `global.nim:viewerPacket`). I replayed its
  episode (PD, seed 57, 3 beats) locally: **150 ticks, 10 resolutions** — so the comparison
  covers real movement, freezes, resets and score changes rather than a static board. CI log:
  `[OK] every tick of the packet is the sim's own state at that tick`.
- Scope, stated plainly: `live[t]` and the recorded `frames[t]` are both taken from the same
  in-memory `Sim` at the same instant, so what is proved is record → replay-bytes → viewer
  fidelity. There is no input-replay in this game to re-simulate against (design.md:562-564).

### F21 — the F47 helper is a second copy of the beat loop — **gap**
- Where: `tests/support/helpers.nim:64-73` vs `src/matrix_games/sim.nim:170-176`.
- Observed. `runScriptedRecording` inlines `runBeat`'s body (`ticksPerBeat × stepOnce` then
  `closeBeat`) so it can snapshot between ticks, but drops `runBeat`'s `if sim.done: return`
  guard. Equivalent for this harness — nothing sets `done` mid-episode — but it is a duplicate
  of the production loop that can drift from it silently.

### F22 — F40 (`74e0572`): the two index derivations are cross-checked — **match**
- Where: `tests/test_viewer.nim:188-214`.
- Observed + **ran**. The test compares the viewer's event-folded `conventionCounts`
  (`global.nim:103-135`) cell for cell against `replay.indices.conventionCounts` (written by the
  sim's accumulator, `indices.nim:42-63` via `replays.nim:67`), checks the cells sum to
  `state.idx.interactions`, and compares `coopRate` including the `JNull` case for a variant
  with no coop token. I ran the same two episodes: PD seed 58 / 3 beats → **8** resolutions,
  RWS seed 58 / 3 beats → **9** — so the comparison is not vacuous today. CI log: `[OK] the
  viewer's re-derived indices agree with the recorded ones`.

### F23 — the F40 test has no non-emptiness guard, and the `over`-row divergence is untouched — **gap**
- Where: `tests/test_viewer.nim:198-207` (no `check state.idx.interactions > 0`);
  `src/matrix_games/broadcast.nim:62-65` vs `src/matrix_games/global.nim:163-165`.
- Observed. If a future constant change emptied the room, both histograms would be all-zero and
  the cross-check would pass while testing nothing (the ≥ 12-resolution gate at
  `tests/test_indices.nim:60-67` is the separate guard for that, at 12 beats). And the one place
  the two derivations genuinely disagree is still uncovered: the terminal `over` beat row is
  built from `sim.leader()` with the real `scoreCp` on the broadcast side and from the last
  `leadchange` seat with `cp: 0` on the viewer side.

### F24 — F65 (`e47b6c8`): the chicken half of gate (b) is asserted — **match**
- Where: `tests/test_indices.nim:113-130`, with the restatement documented at `:23-31`.
- Observed + **ran** + inferred (arithmetic). The test walks every `interact` record of a
  seven-dove/one-hawk room over seeds 1..8 and requires the hawk side to out-earn the dove side
  in every mixed cell, with `check checked >= 8`. I ran the same sweep: **28** mixed-cell
  resolutions, so the floor has margin. The assertion is a theorem, not luck: with
  `colPay = transpose(rowPay)` and chicken's `[[3,1],[4,0]]`, the mixture payoffs are
  `u(x,y) = 3 + x − 2y − 2xy` and `u(y,x) = 3 + y − 2x − 2xy`, so `rowCp − colCp = 300·(x − y)`
  centipoints; `cellRow = 1` forces `x > ½` and `cellCol = 0` forces `y ≤ ½`, and the gap is
  ≥ 16 cp at the largest inventories, well clear of `div`'s ±1 truncation.

### F25 — the note's literal chicken claim is false in this build — **gap**
- Where: design.md:623 ("In `chicken`, one `always-second` in a room of `always-first` tops the
  table") vs the implementation.
- **Ran.** Seven `always-first` plus one `always-second` (slot 3), seeds 1..8, 12 beats: the
  hawk tops the table on **0 of 8** seeds (top slot is 0 on seven seeds and 1 on the eighth),
  scoring 0.00–25.12 against tops of 32.11–48.03, with 5–11 resolutions to the doves' 11–19.
  The positional reason the test header gives (`tests/test_indices.nim:26-31`) is exactly what
  the encounter counts show. The fix's substitution is therefore justified rather than a
  weakening — but the design note still states the property as a feasibility gate, so the note
  and the build disagree.

### F26 — F67 (`72b0cf6`): determinism is checked across processes — **match**
- Where: `tests/test_sim.nim:10-20` (child mode on `MATRIX_GAMES_HASH_SEED`), `:254-263`
  (`hashInFreshProcess`, `execCmdEx(quoteShell(getAppFilename()), env = env)`), `:274-280` (same
  seed → same hash, different seed → different).
- Observed. The in-process pair at `:265-273` is unchanged, so this is additive. CI log:
  `[OK] a fresh process reproduces the same hash from the same seed`.

### F27 — the F67 child mode is an env-gated skip of the whole sim suite — **gap**
- Where: `tests/test_sim.nim:16-20` (`if getEnv(HashSeedEnv).len > 0: … quit(0)`) runs at module
  scope, before any `suite`; the CI runner at `.github/workflows/ci.yml:125-148` only checks
  `nim r`'s exit code.
- Observed + inferred. If `MATRIX_GAMES_HASH_SEED` were ever present in the job environment,
  `tests/test_sim.nim` would print one hash, exit 0, and every sim assertion — the payoff
  formula, the cooldowns, the reset, the BoS row rule, determinism — would silently not run,
  with the job still green. Nothing in the tree sets the variable (`grep -rn
  MATRIX_GAMES_HASH_SEED` finds only `tests/test_sim.nim`), so this is a latent property of the
  mechanism, not a live skip.

### F28 — F66 (`af5c704`): the smoke validates `results.json` against `game.results_schema` — **match**
- Where: `tools/ci/docker_smoke.sh:271` (the manifest path is passed into the artifact check),
  `:303-360` (the recursive validator), `:362-367` (load the schema, fail if absent, validate,
  print).
- Observed + **ran**. I extracted `check_schema` and exercised it against the schema in
  `coworld_manifest_template.json`: the design note's example results object (design.md:674-689)
  **passes**, and each mutation is caught with the `RESULTS-SCHEMA FAIL:` prefix — a bad `reason`
  enum value, 7-element `scores` (`minItems`), an undeclared key
  (`additionalProperties: false`), integers in `win` (boolean type), `coopRate: 1.5`
  (`maximum`), a string in `exploitability` (the `["number","null"]` union), and a null
  `reason`. `null` items and a null `coopRate` are accepted, which the schema requires.
  CI log: `results.json validates against game.results_schema (17 keys)`; grep of the full run
  log gives **0** occurrences of `RESULTS-SCHEMA FAIL` and **0** of `SEAT-COUNT FAIL`.

---

## B. The item round 1's verdict left blocking

### F29 — nothing asserts `results.reason == "complete"`; B1 stands at `af5c704` — **gap**
- Where: `tools/ci/docker_smoke.sh:369-371`:
  ```
  reason = results.get("reason") or results.get("end_reason")
  if reason is not None:
      print(f"episode end reason: {reason}")
  ```
  plus `tests/support/helpers.nim:35` and `:74` (`state.finish("complete", "full_match")`,
  stamped by the harness), and `tests/test_replay.nim:72`
  (`check replay{"results"}{"reason"}.getStr() in LegalReasons` — membership only).
- **Confirmed**, not refuted. The reason is still printed and never checked. The new F66
  validator does not close the hole: `game.results_schema.properties.reason` is
  `{"type":"string","enum":["complete","deadline","forfeit"]}`, and I ran the extracted
  validator against a results object with `reason: "deadline"` — it is **accepted**. So an
  episode that settled as `deadline` (including via the new F32 except branch,
  `server.nim:262-264`) would pass the smoke, pass the schema check, and print a line nobody
  reads. `grep -rn complete tests/ tools/ci/docker_smoke.sh .github/workflows/` finds no
  assertion anywhere.
- The behaviour itself is correct at head: the real containerized 8-seat episode in run
  32755082249 logged `episode end reason: complete` and `smoke OK: seats=8 results=709B
  replay=118908B reason=complete`. What is absent is the gate, exactly as r1's verdict recorded.

---

## C. CI and test hygiene at this sha

### F30 — CI is green on `main` at `af5c704`, with the executed viewer smoke — **match**
- Evidence: run **32755082249**, event `push`, `headSha
  af5c7043d4a4fbca3eb5f4c230901f6d9fb4dfe7`, conclusion **success**; jobs `test`,
  `docker-smoke`, `wasm-viewer` all `success` (`gh run view … --json jobs`). Every step in
  `wasm-viewer` succeeded, including `Load the bundle in a real browser`; no step is
  `continue-on-error` and `wasm-viewer` has `needs: docker-smoke` (`ci.yml:212`). Full-log grep:
  0 × `SEAT-COUNT FAIL`, 0 × `RESULTS-SCHEMA FAIL`. Every new test from the fifteen commits
  appears as an `[OK]` line in the `test` job (chicken, rune head, 401/403, fresh process,
  per-tick packet, re-derived indices, feed classes), in both the debug and the `-d:release`
  passes.

### F31 — no test was disabled, skipped or loosened by these fifteen commits — **match**
- Evidence: `git diff 7b7d586..af5c704 -- tests/` removes exactly three lines — two comment
  lines in `tests/test_indices.nim`'s header (replaced by a longer, more specific header) and
  one `import std/[json, unittest]` line in `tests/test_sim.nim` (replaced by a wider import).
  Every other change is an addition. No assertion deleted, no tolerance widened, no `skip`,
  no file removed.

---

## D. Round-1 `unclear` items the fixes did not touch

Each re-verified at `af5c704`; none of the four source files was in the diff
(`git diff --name-only 7b7d586..af5c704`).

### F32 — the kernel's `gather`/`deny` read the full spawner list — **unclear**
- Where: `src/matrix_games/kernel.nim:124-141` (`nearestTokenCell` iterates `sim.spawners` with
  no `viewRadius` or line-of-sight filter), `:156-175` (`denyTokenCell`). Tie-breaks (lowest
  `y`, then `x`) match design.md:175-176. Whether "from the seat's own observation"
  (design.md:175) names the metric or an information restriction is still unsettled by the note.

### F33 — exploitability picks the row/column side by majority — **unclear**
- Where: `src/matrix_games/indices.nim:74` (`let asRow = idx.rowSides[slot] * 2 >= count`).
  design.md:269 says "the matrix that seat faced (row or column side)" without saying what a
  mixed-side seat gets. Unchanged.

### F34 — a blocked cog still turns — **unclear**
- Where: `src/matrix_games/sim.nim:87-94`: `sim.cogs[slot].facing = micro.dir` at `:90`
  precedes the `isFloor(nx, ny) and sim.occupant(nx, ny) < 0` test at `:91`. design.md:199-202
  does not say whether the facing change is conditional on the move. Deterministic either way.
  Unchanged.

### F35 — a 429 is retried inside the same beat — **unclear**
- Where: `src/matrix_games/llm.nim:449-451` (429 → raise), `:544-560` (any errored reply goes
  into `stillOpen` and is retried in attempt 2 of the same beat). The note is internally split
  (design.md:492-497 vs :501); the code satisfies the first reading and reopens the seat next
  beat as well. Unchanged.

### F36 — the cert fixture names seats with the aliases, so the two name spaces coincide offline — **unclear**
- Where: `coworld_manifest_template.json` `certification.game_config.players` =
  `[{"name":"Ash"},…,{"name":"Holly"}]`, consumed at `src/matrix_games/server.nim:203-205`
  (`gameSim.names[slot] = shared.policies[slot]` only when a policy label arrives). The CI
  viewer smoke's scorebug still reads `Ash 7.59 4 enc Birch 6.65 3 enc …`. Pinned by the note
  (design.md:967-978); the mechanism for two name spaces is present. Unchanged.

---

## Traced and unchanged (verified at this sha, no finding)

- `client/chrome_common.js` — `diff` against `/workspace/starters/coworld-ctf/client/
  chrome_common.js` produces no output. Still byte-identical; untouched by all fifteen commits.
- The placeholder gate of checklist item 12 still exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'`
  over `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`, `tools/ci/docker_smoke.sh`,
  `tools/ci/policies.json` returns nothing (rc 1). `tools/ci/docker_smoke.sh` and
  `tools/build_replay_viewer.sh` are both `-rwxr-xr-x`.
- `src/matrix_games/server.nim:132-158` — the shutdown order is unchanged by the fifteen
  commits: `final` frames → `sleep 500` → **replay** → `results.json` → grace → `quit(0)`, with
  the deviation from design.md:665-667 still stated in the comment at `:145-152` (r1's F71).
- The r1 gaps in files no commit touched are unchanged and were not re-traced beyond confirming
  the files are absent from the diff: `kernel.nim` (F10/F11 sidestep and hunt sweep),
  `sim.nim:112` (F9 `updateSight`), `sim.nim:328` (F17 `fixedType`),
  `client/broadcast_core.js` (F56), `replay-viewer/static_replay.js` (F55),
  `scripts/art/gen_matrix_art.py` (F70).
- `tests/test_indices.nim` gates (a) and (c), the two null rules, and the PD / stag-hunt / RWS /
  BoS clauses are as r1 read them; only the chicken test was added.

---

## Could not determine

- **Whether the feed and banner lane are legible at 360 px now that they are styled.** The one
  CI artifact that could show it reports `feed_lines: 0` because of the harness's selector
  (F14). What would settle it: a screenshot taken mid-episode at 360 px, or a
  `viewer-smoke.json` from a harness that reads `#killfeed`.
- **Whether anything on the live beat path can raise a `Defect`.** F7 establishes the guard does
  not catch one and that a thread defect kills the process; I found no concrete raising path by
  reading. What would settle it: a fuzzed `installOrders`/`buildObservation` test, or
  `--panics:on` plus an observed run.
- **Whether checklist item 15 (canvas text bounds) is in scope for this repo.** The item and the
  instrumented harness landed in coworld-builder 13 minutes after this head's CI run (F19); this
  viewer draws no canvas text at all, so the instrumentation would report `total: 0`, and the
  model-authored `say` string is DOM text. What would settle it: a coordinator/judge ruling on
  whether a DOM-text viewer needs the `--strict-text-bounds` step and the worst-case fixture.
- **Whether `validate()` must accept every config the published `config_schema` permits** (F5).
  What would settle it: a ruling, or a `config_schema` `beats` maximum lowered to what the
  deadline arithmetic can actually carry.
- **Runtime behaviour of the LLM path.** Still unexercised with credentials: the smoke logs
  `no ANTHROPIC_API_KEY: the game must complete on its scripted baselines`
  (`tools/ci/docker_smoke.sh:198`). What would settle it: a phase-60 league episode.
