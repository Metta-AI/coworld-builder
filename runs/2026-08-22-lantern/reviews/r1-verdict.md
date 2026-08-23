blocking: 0

# r1 verdict — lantern

Head: `024144dbaefb0ea9482b0bf274f23e0eb9c45f3a` (`main`, clean checkout at
`/workspace/scratch/cogame-lantern-review`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–12 + the
simultaneous-decision batching rule)
Independent read written before reading the review: **yes** — I read the design note, all of
`src/lantern*/*.nim`, the tests, the manifest, both viewer JS shells, the three workflows,
`tools/ci/docker_smoke.sh`, `tools/ci/policies.json`, `tools/build_replay_viewer.sh`, the git
history of `tests/`, and the CI log of run 32612666063 before opening `r1-review.md`.
`r1-fixes.md` was **not read at all**, per the brief — the fixer's claims played no part in this
verdict; every fix was verified from the code and the fix commits directly.

The review was written against `06d4da7`. Seven fix commits and one tuning-harness commit have
landed since (`3a6c387` F1, `428d12b` item-7 tuning, `d3bb406` F5, `af94ca9` F6, `5d58402` F3,
`3e97c1f` F2, `1a54b43` F11, `024144d` F13). I verified each at the head, not from anyone's
disposition table.

## Standing blocking findings

**None.** The review's single blocking finding is refuted (fixed at this sha, below), and my own
independent checklist pass found no item falsified at the head.

## Refuted

### F1 — "captured LLM error text reaches the replay through byte-index string slices" → REFUTED (fixed at this sha)
- The finding was **correct at the review's sha** `06d4da7`. It no longer reproduces at head.
- Evidence: `src/lantern/llm.nim` at `024144d` — all four slices now go through `orders.clip`
  (rune-boundary `runeSubStr`):
  - `llm.nim:179` `let detail = clip(response.body, 400)` (401/403 path)
  - `llm.nim:187` `let detail = clip(response.body, 300)` (429 path)
  - `llm.nim:191-192` `"anthropic error " & $response.code & ": " & clip(response.body, 300)`
  - `llm.nim:200-201` `"any JSON: " & clip(result, 160).oneLine()` (max_tokens model-text path)
  `clip` is `orders.nim:22-28` (`runeLen`/`runeSubStr`, always valid UTF-8 output).
- The review's proposed settling test now exists: `tests/test_engine.nim:265-348`
  ("captured provider errors are rune-safe all the way to the replay") drives
  `textOf → LlmReply.error → decideAll → fallback.detail → buildReplay` with a 429 body of
  4-byte runes (`Torch.repeat(400)`), a 401 body of 3-byte runes (`Euro.repeat(500)`, byte 400
  lands inside a rune), and a `max_tokens` reply of non-ASCII model text, asserting
  `validateUtf8(bytes) == -1` on the serialised replay and `runeLen <= MaxDetailRunes` on every
  detail. Fixed in commit `3a6c387`; CI green on it and on head.

### Review §Could not determine, item 7's "tuned with a grid harness" → now SETTLED (satisfied at this sha)
- At `06d4da7` no harness existed; the reviewer correctly declined to file it as blocking.
  At head, commit `428d12b` adds the harness and its record, and it is live, not decorative:
  - `tools/tune_baselines.nim:38-45` sweeps the full 3×3×3 grid (`CoverageGates [40,60,80]`,
    `BuildLocks [1,2,3]`, `PryHotTurns [1,2,3]`) over seeds `[1,7,42,99]` at full match length
    (720/1800), head-to-head vs `moth` and vs a fixed `ReferenceWardenParams(60,2,2)`.
  - `tests/fixtures/tuning_grid.json`: 27 cells; `chosen = {60,3,3}`, `chosen_mean_milli: 656`.
  - `src/lantern/baselines.nim:38-39` `ShippedWardenParams = WardenParams(coverageGatePct: 60,
    buildLocks: 3, pryHotTurns: 3)` — equals the recorded argmax.
  - `tests/test_tuning.nim:35-46` asserts shipped == recorded argmax **and** that the argmax
    beats the hand-guessed reference; `:48-58` re-runs two grid cells against this code so the
    record cannot go stale. `docs/tuning.md` documents the sweep.

## Non-blocking review findings, checked at head (for completeness)

| finding | state at head |
|---|---|
| F2 (crate_push per tick) | fixed, `3e97c1f`: `sim.nim:429-438` — event, `cratesPushed` counter and ring all inside the 12-tick gate; manifest description regenerated ("counted at most once per crate per 12 ticks"); smoke fixture re-recorded in the same commit (controls/keyframes byte-identical, events 339→177 — confirmed by the wasm smoke log "1440 ticks, 177 events") |
| F3 (`found[]` missing `by`/`mode`, match-clock `at_s`) | fixed, `5d58402`: `render.nim:120-129` emits `by`, `mode` and per-hunt-act `at_s`; `types.nim:224-225` carries `foundBy`/`foundMode`; new test `test_vision.nim:85-105` |
| F4 (9 s + 4 s = the whole 13 s budget, no separate outer deadline) | still true; still bounded, still inside item 5 — see checklist row 5 |
| F5 (`all_found` kept querying seekers) | fixed, `d3bb406`: `server.nim:147-148` `if act == actHunt and sim.actEnded[half-1]: return @[]`; ticks still run so the denominator stays whole (`sim.nim:600` unconditional in hunt); test `test_engine.nim:147-163` |
| F6 (aim-reflex comment wrong about team vs own lit set) | fixed, `af94ca9`: `control.nim:214-231` comment now states and justifies the team-wide keying |
| F7 (pointwise visibility, 8 px LoS grid) | unchanged; a declared, determinism-safe deviation matching the note's own lit-set definition; boundary-exact tests in `test_vision.nim` |
| F8 (map differs from the note's JSON block) | unchanged; obstacle and crate 180°-symmetry hold (asserted `test_map.nim`), nook asymmetry is half-neutral because both halves share the map |
| F9 (`lantern_replay.data` in the note's list, not in the bundle) | unchanged; nothing loads it, `font.ttf` is present; the note's list is the wrong artifact |
| F10 (float in `events.nim` inside the step) | unchanged; digest covers only integer state, events are never read back — no re-derivation exposure |
| F11 (find burst dead code) | fixed, `1a54b43`: `lantern_replay.nim:28-31,87-99` records pre-teleport find positions and `packetJson` emits `"bursts"` (`:79`); `broadcast_core.js:388` reads them; scrubs suppressed (`:110`); the wasm smoke now reports "1 find bursts" |
| F12 (`chrome_common.js` rewritten, not verbatim) | unchanged; factory contract and all inherited ids asserted (`test_viewer.nim:17-47,85-90`) |
| F13 (determinism gate only 1440 ticks) | fixed, `024144d`: `test_determinism.nim:25-37` compares two independent full 5040-tick runs, 210 keyframes, identical digests and control bytes |
| F14 (some engine cases assert at results/roster layer) | unchanged; coverage note, outside the checklist |
| F15 (`test_viewer` wasm harness self-skips in the `test` job) | unchanged; the skip is a bundle-absence conditional present since the initial commit, and the real harness ran in the `wasm-viewer` job of the judged run ("wasm viewer smoke OK … digests all matched") — not a disabled/loosened test |
| F16 (`decideAll` outside `stateLock`) | unchanged; only `memo` (int array, never read by `/global`) is written outside the lock; strings assigned under it (`server.nim:262-286`) |

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1. CI green, no test loosened | **pass** | run **32612666063** on `024144d`, conclusion `success`; jobs test / docker-smoke / wasm-viewer all `success` (gh run view). All 17 `tests/*.nim` ran twice (34 invocations counted in the log), no `FAILED`. `git log -p -- tests/` over the whole history (first commit 2026-08-23 = run start): additions only, plus one 2-line replacement in `test_manifest.nim` (`06d4da7`) that *strengthened* the `episode_timeout_minutes` assertion (moved to top level + added `not game.hasKey(...)`), and fixture re-records accompanying the F2 rule change in the same commit. No assertion deleted, no tolerance widened, no skip added, no file removed |
| 2. Replay re-derivation | **pass** | `replay.nim:192-232` `rederive` re-steps the sim from `config`+`map`+`controls_b64` and compares every keyframe digest; `test_replay.nim:110-115` asserts `ok`/`mismatchTick == -1`/`checked == keyframes.len`; `:117-125` corrupted controls caught. The viewer runs the **same** `rederive` (`lantern_replay.nim:119`) and draws every frame from a sim it re-derives itself (`packetJson` reads `world.cogs`/`world.crates`, `:38-81`), not from a parallel recording; mismatch surfaces as `data-replay-mismatch-tick`/`#mmwarn` |
| 3. Static viewer | **pass** | manifest `game.replay_viewer == {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json:18-20`); `tools/build_replay_viewer.sh` committed `100755` (`git ls-files -s` → `100755 0a672e33`), wired as the `coworld build` hook and gated `test -x` in `ci.yml:205-219`. Only network call in the bundle is `fetch(message.replayUrl)` (`static_replay_worker.js:137`, bounded by AbortController) plus relative `./art` loads (`broadcast_core.js:42-47`). No pod replay path in the manifest; the server's `/client/replay` route (`server.nim:522`) is the local-viewing route the design note keeps — the hosted viewer never touches it |
| 4. Both name spaces | **pass** | `labels.nim:14-39` aliases from slot parity; `render.nim` uses `aliasOfSlot` only (no `config.players` reference); LLM user message = prompt + `seatView` (`llm.nim:254-261`). Real names only in `results.names` (`replay.nim:105`), `replay.names.players` (`:63-77`), `/global` policyNames, and the scorebug (`chrome_common.js:93-106` `teamPlayers`/`teamHeadline` off `meta.names.players`) |
| 5. Degrade-never-hang, ≤ 60 % of 1200 s | **pass** | connect wait ≤ `playerConnectTimeoutMs` (`server.nim:163-170`); LLM attempts 9 s + 4 s = 13 s = turn budget (`config.nim:22-23`, `llm.nim:298-301`, pinned `test_engine.nim:93-107`), exactly two attempts (`llm.nim:289`); budget guard at `remaining < 2×turnBudget` (`server.nim:248-255`); engine hard stop `wallClockBudgetMs = 660_000` ≤ 720 s (`server.nim:209-213`); done broadcast 3 s (`:33,338-345`); artifact POST 60 s (`:98`); player-side 12×500 ms then `exit 0` (`lantern_player.nim:36-37,61-72`). Manifest asserts all three configs' budgets ≤ 720 (`test_manifest.nim:82-87`). Main loop advances tick monotonically; every inner loop bounded by construction; no blocking read (player frames are fire-and-forget) |
| 6. `num_agents` | **pass** | `== 6` in `variants[default]`, `variants[sprint]`, `certification.game_config`; `len(certification.players) == 6 == len(certification.game_config.players)` (manifest lines 633, 689, 743, 754-773; asserted `test_manifest.nim:15-31`). `docker_smoke.sh:102-143` enforces all four invariants + the `SMOKE_SEATS=6` cross-check, each exiting via `SEAT-COUNT FAIL:`. **Grepped the full 3558-line log of run 32612666063 for `SEAT-COUNT FAIL`: 0 matches**; smoke printed `game=lantern seats=6` and `smoke OK: seats=6 … reason=complete` |
| 7. Scripted baseline full episodes, legal, tuned | **pass** | `test_replay.nim:14-58` full scripted episode to `totalTicks`, results file asserts `reason == "complete"`; `test_scoring.nim` asserts `complete`/`full_time`; `test_baselines.nim:26-53` ≥ 500 orders × `legalOrder` + ≥ 5000 controls × `boundedControl` on played (not poked) states; no fourth lock (`:55-61`); warden beats moth (`:63-73`). Grid tuning: harness + 27-cell record + live `test_tuning.nim` (see Refuted §2) |
| 8. LLM reply handling | **pass** | tolerant parse (`orders.nim:53-83` balanced-brace extraction, fences/prose/numeric-strings/int-crate accepted, `test_orders.nim:25-97`); exactly one retry with the invalid-reply hint (`llm.nim:262-265,289`); fallback to warden order recorded as `fallback` events with cause enum and counted into `results.fallback_turns`/`fallback_causes` (`server.nim:270-278`, `replay.nim:120-125`); phase-60 grep line at `llm.nim:332` |
| 9. Rune-safe truncation | **pass** | `orders.clip` (`orders.nim:22-28`) on `note`/`say`/`crate` (`:185,198-199`); `roster.nim:46-58` prompt/policy; `events.nim` `clipRunes` on `detail`; **captured errors now rune-safe** (`llm.nim:179,187,192,201`, fixed `3a6c387`). Tests feed multi-byte input at the cap: `test_orders.nim:105-118` (4-byte emoji straddling rune 32, exact rune cut + `validateUtf8 == -1` + round trip), `test_replay.nim:52-68` (non-ASCII `say` in the on-disk bytes, UTF-8-validated before parse), `test_engine.nim:315-348` (provider/model error bodies) |
| 10. Manifest validates | **pass** | `game.docs.readme = {"type":"text","value":…}` + `pages = [{id,title,content:{type:"text",value:…}} × 2]` (manifest lines 537-559, asserted `test_manifest.nim:97-108`); `game.protocols` carries both `player` and `global` as inline text (lines 527-535, asserted `:89-95`); `results_schema` keys == server emissions (`:45-59`); `episode_timeout_minutes: 20` top-level (`:76-81`) |
| 11. Viewer legible at 360 px | **pass** | `client/replay_broadcast.html:1484` `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }`; `:1563-1573` `@media (max-width: 640px)` hides `#viewpanel` (`display:none !important`) and `#speedchips .chip-label`, collapses `#heartbar` to 8 px dots, caps the feed at two lines. Statically asserted at `test_viewer.nim:49-53` |
| 12. Release order and scaffold | **pass** | `coworld-release.yml`: Build manifest (`:153`) → Certify (`:167`) → Upload policies (`:206`) → Upload Coworld (`:304`) → Secret put (`:342`); docker-smoke builds the image in the same job before smoking it (`ci.yml:172-181`); all three workflows present; `docker_smoke.sh` mode `100755`; `policies.json`: 4 policies, 2 × `PLAYER_PROMPT` champions + 2 scripted fillers, all `"run": "/bin/lantern-player"`, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (asserted `test_manifest.nim:145-171`, prompts differ). Placeholder gate: I ran the exact grep — **no matches, gate exits 0**; the four allowed runtime angle-bracket names are where the checklist says they are |
| Simultaneous batching | **pass** | one `RequestBatch` + a single `curly.makeRequests` per attempt (`llm.nim:203-214`, the only `makeRequests` call in the repo); `test_engine.nim:68-91` asserts build turns batch 3, hunt turns 6, one shared in-flight window, seat order preserved; `activeSeats` (`server.nim:137-155`) drops frozen seekers and (post-F5) everything after `all_found` |

## Fixer report audit

`r1-fixes.md` was deliberately not read (per the brief), so this audits the fix **commits**
against the review's findings instead of the fixer's own table:

| finding | fix commit claims (from `git log`) | I verified at head | agrees |
|---|---|---|---|
| F1 | `3a6c387` rune-safe clip ×4 + tests | `llm.nim:179,187,192,201` all `clip(...)`; `test_engine.nim:265-348` | yes |
| F2 | `3e97c1f` gate event+counter, fixtures re-recorded same commit | `sim.nim:429-438`; keyframes untouched, smoke shows 177 events | yes |
| F3 | `5d58402` `by`/`mode`/per-act `at_s` | `render.nim:120-129`, `test_vision.nim:85-105` | yes |
| F5 | `d3bb406` `actEnded` stops all queries | `server.nim:147-148`, `test_engine.nim:147-163` | yes |
| F6 | `af94ca9` comment corrected | `control.nim:214-231` | yes |
| F11 | `1a54b43` bursts emitted | `lantern_replay.nim:79,87-99`; wasm smoke "1 find bursts" | yes |
| F13 | `024144d` full-length determinism gate | `test_determinism.nim:25-37` | yes |
| item 7 | `428d12b` grid harness + record + live test | `tools/tune_baselines.nim`, 27-cell `tuning_grid.json`, `test_tuning.nim` | yes |

## Non-blocking observations (mine, beyond the review's)

- `orders.nim:141-148` (`repairCrate`): the `case`-expression intent degrade is immediately
  overwritten by the role-based `if` two lines later — redundant but behaviour-identical
  (push/lock are hider-only, pry seeker-only). Cosmetic.
- The worst-case artifact-write tail (660 s stop + 3 s done + up to 60 s per `curl.post`) can
  arithmetically exceed 720 s if S3 stalls at the timeout, but "settles and scores" is met at
  ≤ 660 s, the budget guard makes the 660 s stop itself nearly unreachable, and the platform
  kill is 1200 s. Not a checklist violation on any reading I can support.
- `test_viewer.nim`'s wasm-harness `skip()` (initial commit) remains the one conditional skip in
  the tree; the skipped check runs unconditionally in the `wasm-viewer` job via
  `build_replay_viewer.sh:81-83` and passed on the judged sha.

BLOCKING: 0
