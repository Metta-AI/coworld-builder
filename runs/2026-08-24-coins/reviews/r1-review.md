# r1 review — coins

Range: `f4ff1d1..3bc93c3` (bootstrap → `coins: the endcard table and the 360 px compact forms`, `main`)
Files read: 48 (whole repo tree except binary art; plus the coworld-ctf starter counterparts for the provenance diffs)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision addendum)
Design note: `/workspace/coworld-builder/runs/2026-08-24-coins/design.md` (byte-identical to the in-repo copy `docs/plans/2026-08-24-coins-design.md` — verified with `diff -q`)
CI evidence: run **32791042255** on `main` at `3bc93c3`, conclusion `success`; jobs `test` (97632502872), `docker-smoke` (97632503086), `wasm-viewer` (97632780459) all green.

---

## Blocking

### B1 — the viewer draws LLM-authored `say` text in an unbounded, never-exercised feed row, and no worst-case renderer fixture exists

- Where:
  - `client/replay_broadcast.html:2336-2342` — the game block's `order` feed row:
    ```js
    case 'order':
      var say = e.say ? ' <span class="glyph">\u201c' + cnEsc(e.say) +
        '\u201d</span>' : '';
      cnPushRow(who + ' <span class="glyph">' + cnEsc(e.intent) + '</span>' +
        say + (e.source === 'fallback'
          ? ' <span class="badge tk">auto</span>' : ''), team);
    ```
  - `client/replay_broadcast.html:488-505` — the row's CSS, inherited verbatim from the starter:
    `.feed-row { … max-width: none; white-space: nowrap; }` (`max-width: none` at :502, `white-space: nowrap` at :503)
  - `client/replay_broadcast.html:470-483` — `#killfeed { bottom: calc(76 * var(--u)); right: calc(12 * var(--u)); width: calc(228 * var(--u)); min-height: calc(4 * 22 * var(--u)); }`
  - `src/coins/sim_types.nim:61-64` — `MaxSayLen* = 48`, `MaxNotesLen* = 300`
  - `.github/workflows/ci.yml:318-323` — the only viewer gate: `viewer_smoke.mjs … --strict-text-bounds`
- Observed, step by step:
  1. `say` is LLM-authored, capped at 48 runes (`sim_types.nim:61`), recorded on the `order` event (`events.nim:37-40`) and drawn by the game block into a `#killfeed` row (`:2337-2341`).
  2. The row it lands in is `white-space: nowrap` with `max-width: none` (`:502-503`). The starter's own comment on those two lines states the justification: *"Size to content so full names never truncate; rows are right-anchored … bounded by the small font + the pre-bounded 10-char name, so it can't run away."* The starter's rows carry a ≤10-char name and a glyph; Coins' row adds a 48-rune quoted remark that the starter's geometry was never sized for. There is no `max-width`, no wrap, no ellipsis on this row, and `#killfeed`'s `width: calc(228 * var(--u))` (`:481`) does not clamp it because `max-width: none` overrides the box for the flex row's content.
  3. The vertical band **is** reserved (`#killfeed`'s `min-height: calc(4 * 22 * var(--u))` fixed 4-row reserve, `:482`, inherited), so the scene does not jump; the unreserved axis is horizontal.
  4. Nothing in CI ever renders that row with content. `docker_smoke.sh` runs without `ANTHROPIC_API_KEY` (docker-smoke log: `no ANTHROPIC_API_KEY: the game must complete on its scripted baselines`); a scripted seat's `Decision` carries no `say`/`notes` (`src/coins/llm.nim:332-346` — `fallbackDecision`/`scriptedDecision` set only `intent` and `source`), so the smoke replay contains zero LLM text. The wasm-viewer log confirms it: `{"loaded":true,…,"feed_lines":0}` and `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
  5. `src/coins/global.nim:10-13` states, and I confirmed by grep, that **the board draws no canvas text at all** — there is no `fillText`/`strokeText`/`measureText` anywhere in `client/broadcast_core.js`, `client/chrome_common.js` or `client/replay_broadcast.html`. So `canvas_text.total` is structurally 0 and the `--strict-text-bounds` gate can never see this text even if a replay carried it.
  6. There is no worst-case renderer fixture anywhere in the tree: no fixture page, no extra `ci.yml` step, no `viewer_smoke.mjs` invocation other than the one at `.github/workflows/ci.yml:318-323`. `tests/test_viewer.nim` asserts CSS *presence* (`:86-96`) but never renders a string.
- Checklist item: item 15, final bullet — *"**The CI replay cannot talk.** … Every replay CI can produce carries zero LLM text, so `viewer_smoke.mjs` on that replay never draws a speech bubble, a remark feed line, or a notes panel … A repo whose viewer draws LLM-authored text must therefore ship a **worst-case renderer fixture** … a repo that draws model text and has no such fixture is a blocking `legibility` finding."* Also engages item 15's second bullet (*"Any text laid out relative to another element … gets a reserved band in the layout, sized from the cap the server enforces on that string (`MaxSayLen` and its kin) and measured in the font it will be drawn in"*) on the horizontal axis.
- Why blocking: the checklist sentence is unconditional — the viewer draws model text, CI can never produce model text, and no fixture substitutes for it. Concretely, the row width at a full 48-rune cap is untested at every board width, and the one gate that could have caught a clipped string (`--strict-text-bounds`) reports `total: 0`, which item 15 itself says "means the check covered nothing … and is not evidence of anything."
- **Counter-evidence I am obliged to record, so the judge can refute this if it disagrees with my reading:** the text is DOM, not canvas — it is laid out by the browser inside `#chrome` (`inset: 0` on `#stage`), so it is clipped by the stage rather than drawn at a negative coordinate the way cogchemists' canvas bubbles were. My own arithmetic on the inherited rule set suggests a full-cap row is roughly 400 `--u` wide against a stage of ~720–760 `--u`, i.e. it probably fits — but that is an estimate from CSS, not a measurement, and nothing in the repo or CI measures it. See "Could not determine".

---

## Non-blocking

### N1 — no test asserts the recorded frames element-by-element against the sim's frames

- Where: `tests/test_replay.nim:179-196`, `src/coins/replays.nim:139-148`, `replay-viewer/coins_replay.nim:56-80`
- Observed: Coins records **state frames**, not inputs (`replays.nim:1-6`), so there is no re-simulation path and no parallel recording — the viewer's `coins_load_replay` parses the same bytes and feeds them to the same `broadcast.buildStateJson` the live server uses (`coins_replay.nim:51-54`, `:61-63`). The round-trip is asserted at `test_replay.nim:181` (`data.frames.len == ticksPlayed`), `:182` (config recovered), `:188-189` (the last frame's `sc[]` equals the sim's final scores) and `:196` (playback advances); `tests/test_viewer.nim:166-186` walks every frame of a parsed replay through `buildStateJson`. What is *not* asserted anywhere is `parseReplayBytes(replayBytes(sim)).frames[i] == sim.frames[i]` for all `i` — only the count, the config and the terminal frame.
- Checklist item 2 reads *"Replaying the recorded events through the sim reproduces the recorded per-tick state frame by frame … A test asserts it."* The property item 2 guards against (a display fed by a parallel recording) does not arise here — the recorded state **is** the record and the viewer reads it — which is why I file this as non-blocking rather than blocking. The design note puts re-simulating playback explicitly out of scope (`design.md:1078-1079`).

### N2 — `compose.yaml`'s service is `coins`, not `game`; the placeholder is `{{COINS_IMAGE}}`, not `{{GAME_IMAGE}}`

- Where: `compose.yaml:10-11`, `coworld_manifest_template.json` `game.runnable.image`, `tests/test_manifest.nim:39-45`
- Observed: the compose service is named `coins` (`compose.yaml:11`) and the manifest carries `"image": "{{COINS_IMAGE}}"`. `test_manifest.nim:39` pins `serviceName == "coins"` and `:41-45` derives and asserts `{{COINS_IMAGE}}`, so the repo is internally consistent and the derivation rule (`placeholder == service.toUpperAscii() & "_IMAGE"`) holds.
- What the note says: `design.md:865-876` shows `services: game:` and states *"`services.game` → **`{{GAME_IMAGE}}`**"*, and that `tests/test_manifest.nim` asserts that derivation. Code is a deliberate rename away from the note; the invariant the note actually cares about (derivation from the service name) is preserved. Not a named checklist item.

### N3 — a cog can emit two `blocked` events in one tick

- Where: `src/coins/sim.nim:290-301`
- Observed: `if refused[slot]` (`:296`) emits a `blocked`/`restraint` event at the refused coin's cell, and `if blockedSeen[slot] and blockedWhy[slot] != brRestraint` (`:299`) emits a second `blocked` event at the cog's own cell. A cog that first refuses a coin and then loses the same-target contest emits both `restraint` and `contested`. A cog that refuses a coin and then successfully sidesteps emits a `restraint` event **while moving**.
- What the note says: `design.md:200-201` (step 3's last bullet) — *"A cog that was blocked emits **one** `blocked` event with `why` ∈ …"*. `design.md:278-281` (§The five intents) says the opposite for the moving case — *"the cog walks around the coin it will not take, and the sim emits a `blocked` `why: "restraint"` event when it does"* — so the note is internally inconsistent and the code follows the §five-intents reading. The commit message on `2e3c462` records this as a deliberate choice. The viewer's hand-off glyph is anchored to that cell (`src/coins/global.nim:152-155`).

### N4 — step 3b's literal sidestep rule is not applied when a cog already stands on its target

- Where: `src/coins/sim.nim:224-228`
- Observed: `if not kernels[slot].hasTarget or (kernels[slot].tx == startX[slot] and kernels[slot].ty == startY[slot]): continue` — a cog standing on its own target waits.
- What the note says: `design.md:187-190` step 3b would, read literally, have such a cog take *"the first legal cell among **all** of `N, E, S, W`"* (its reducing-direction list is empty), i.e. wander off the centre and back. The code is stricter than the note and implements `design.md:272`'s *"walk to the room centre (4, 4) and wait there"*. `tests/test_sim.nim:124-126` asserts the parking behaviour.

### N5 — the play deadline clock starts before the connect wait

- Where: `src/coins/server.nim:176` (`let gameStart = epochTime()`), `:177-196` (connect + register waits), `:233` (`proc now(): float = epochTime() - gameStart`), `src/coins/sim.nim:643-645`
- Observed: `gameStart` is taken at the top of the episode thread, i.e. **before** the up-to-`playerConnectTimeoutSeconds = 180` connect wait, so the 720 s play deadline is measured from process start, not from first tick. In the worst case (both seats connecting at t=180 s, every beat paying batch+retry) the deadline fires and the episode settles with `reason: "deadline"` — a legal reason (`sim_types.nim:101-105`), so nothing hangs; it just ends short.
- What the note says: `design.md:295-299` budgets `576 s + ~30 s = 606 s < 720 s` and parenthesises *"connect wait already elapsed"* — ambiguous about whether the connect wait is inside or outside the 720 s. Reporting the code's actual choice.

### N6 — the deadline is checked *before* the next batch, so the last beat can overrun 720 s by one beat

- Where: `src/coins/sim.nim:632-647`
- Observed: the loop plays `ticksPerBeat` ticks, closes the beat, then tests `if now() >= sim.config.playDeadlineSeconds()`. A beat that starts at `now() = 719.9` may take a full `2 × llmTimeoutSeconds = 24 s` before the next check, so settlement can land at ~744 s. That is still far inside `episodeTimeoutSeconds = 1200`, and it is exactly the behaviour `design.md:234` describes (*"checked **at beat closes only**"*). No unbounded wait: `maxBeats` bounds the loop count and `llmTimeoutSeconds` bounds each batch.

### N7 — three call sites in the LLM batch sit outside the per-seat `try`

- Where: `src/coins/llm.nim:388-395`
- Observed: `decideAll`'s per-seat `try/except CatchableError` starts at `:400`. `view.buildObservation(seat)` (`:389`), `userPrompt(...)` (`:390`), `client.requestFor(systemPrompt(obs), user)` (`:393`) and `client.curl.makeRequests(batch, client.timeoutSeconds)` (`:395`) are outside it. If `makeRequests` raises rather than returning per-request `.error` strings, `decideAll` propagates and `runEpisode` → `runGame` has no `try/except` around it (`server.nim:259`), so the episode thread would not reach `finishEpisode()`.
- What the note says: `design.md:475-476` — *"`decideAll` never raises; the episode always advances."* Everything that Coins itself can raise (parse, transport-status, refusal, unknown intent) **is** inside the `try` and the note's claim holds for those; this is about the curl call itself. Untested — I have no way to make `makeRequests` raise in the sandbox. See "Could not determine".

### N8 — `/global` reads sim state from a mummy worker thread while the episode thread mutates it

- Where: `src/coins/server.nim:379-385` (`globalUpgradeHandler` → `pushGlobalLocked` under `stateLock`), `:101-116` (`pushGlobalLocked` reads `gameSim.currentFrame()` and `liveChromeJson(gameSim, …)`), `:259` (`runEpisode(gameSim, …)` runs **without** `stateLock`)
- Observed: `runGame` calls `runEpisode` outside any lock; `stepTick` appends to `sim.frames`, `sim.scoreSeries` and `sim.coins` (`sim.nim:144-157`, `:343`). A spectator connecting to `WS /global` mid-episode enters `pushGlobalLocked` on a mummy worker thread, which reads `sim.frames[^1]` and iterates `sim.beatThefts`. `stateLock` is held on the reader side only — the writer never takes it. `onBeat` (`server.nim:250-253`) does take the lock, but the ticks between beat closes do not.
- Not a named checklist item. Inferred from the code; no run in the sandbox can exercise it (the docker-smoke episode opens no `/global` socket).

### N9 — a `forfeit` episode writes a replay whose `frames` array is empty, which the parser then rejects

- Where: `src/coins/server.nim:216-226`, `src/coins/replays.nim:166-167`
- Observed: on `connectedCount == 0` the server zeroes both scores, calls `endEpisode(erForfeit)` and `finishEpisode()` **without ever calling `stepTick`**, so `sim.frames` is empty and `replayJson` emits `"frames": []`. `parseReplayBytes` raises `"replay carries no frames"` at `replays.nim:166-167`, so the static bundle loading such a replay would set `data-replay-error` rather than render.
- What the note says: `design.md:235` — *"both `0.0`; `results.json` and the replay are still written."* Both are written; the replay is simply not loadable. Unreachable in CI (docker-smoke always connects both seats).

### N10 — the LLM batch/cadence and retry assertions never execute in CI

- Where: `tests/test_llm.nim:139-151`, `:114-119`
- Observed: `newLlmClient` disables itself when no credentials are present (`src/coins/llm.nim:113-116`). CI has neither `ANTHROPIC_API_KEY` nor the Bedrock sidecar vars, so `client.disabled` is true and the tests take the `if client.disabled:` branch (`test_llm.nim:143-145`) — `check(client.batchStarts.len == 3, "one batch per beat, not one per seat")` and the `minBeatSeconds` spacing check at `:147-151` are dead in every CI run. Separately, **there is no stubbed transport anywhere in the tree**, so the retry loop (`llm.nim:382-411`, `for attempt in 0 .. 1`) and the `osRetry` source are never exercised by a test; only `fallbackDecision` is tested directly (`test_llm.nim:83-93`).
- What the note says: `design.md:1006-1011` (§Tests item 5) promises *"an unknown `intent` → invalid → **one** retry → `reciprocator` fallback recorded with `source: "fallback"`; a stubbed transport that times out, 429s, 403s or returns junk never raises and always yields a legal intent; and **one batch carries every open seat** (assert `RequestBatch.len == openSeats` …)"*. The code implements all of it (`llm.nim:382-415`); the tests do not reach it. Checklist item 8 does not require a test, which is why this is non-blocking.

### N11 — `tests/test_dilemma.nim`'s gates (a)–(d) are weaker and more aggregate than the note's

- Where: `tests/test_dilemma.nim:73-77`, `:138-148`
- Observed vs `design.md:597-608`:
  - (a) note: *"both scores strictly positive, both `thefts == 0`, **mean ≥ 10**"*. Code asserts positive and `thefts == 0` per seed (`:73-77`) and `R > 0.0` (`:144`) — no `≥ 10` gate. (CI reports `R = 14.9375`.)
  - (b) note: *"both scores strictly below the `honest`/`honest` mean, and **the mean is below 5**"*. Code asserts `P < R * 0.6` on means only (`:145-147`) — no per-seed check and no absolute floor. (CI: `P = -0.1875`.)
  - (c) note: *"the greedy seat **strictly outscores** the `honest`/`honest` mean"* per seed. Code asserts `T > R` on means (`:138`); only the sucker half is per-seed (`:100-102`).
  - (d) note: *"the reciprocator's score is strictly greater than the honest seat's score against `greedy` **on the same seed**"*. Code asserts `D > S` on means (`:148`). CI reports `D = -6.625` vs `S = -7.0` — a margin of 0.375 across 8 seeds, so the shipped gate passes on a thin aggregate margin and would not catch a per-seed inversion.
  - (e), (f) match the note (`:150-159`, `:161-170`).

### N12 — no grid-tuning harness ships in the repo

- Where: repository tree; `tests/test_dilemma.nim`, `tests/test_baseline.nim`
- Observed: checklist item 7 ends *"The baseline's parameters were tuned with a grid harness, not guessed."* There is no harness script or tool in the tree. What exists is a sweep in test form: `test_baseline.nim:120-122` runs 5 variants × 4 baselines × 8 seeds = 160 episodes (CI: `played 160 scripted episodes`), and `test_dilemma.nim:70-119` sweeps 4 pairings × 8 seeds at cert length and prints the payoff table. `punishThreshold = 2` / `punishBeats = 4` / `truceBeats = 3` are asserted for shape, not searched over.

### N13 — the endcard covers the reciprocity strip instead of showing it

- Where: `client/replay_broadcast.html:2360-2415` (`cnEndcard`), `:730` (`#endcard { z-index: 30 }`), `:1872` (`#cn-recip { z-index: 8 }`)
- Observed: `cnEndcard` fills `#ec-headline`, `#ec-wincond`, `#ec-how` and `#ec-teams` (a two-row table) and nothing else. `#endcard` and `#cn-recip` are both children of `#chrome` (`:1211`, and `cnEnsureOverlays` appends to `#chrome` at `:2185`), so at `z-index` 30 vs 8 the endcard covers the strip.
- What the note says: `design.md:816-818` — *"a two-row table (policy name · score · coins taken · thefts · stolen from · restraint) **and the final reciprocity strip at full width**."* The table is present; the full-width strip is not built.

### N14 — `notes` is recorded but never drawn

- Where: `src/coins/events.nim:37-40` (`notes` on the `order` event), `client/replay_broadcast.html:2336-2342`
- Observed: the game block's `order` handler renders `intent`, `say` and the `auto` badge; `e.notes` is never read anywhere in the page (grep confirms `notes` appears nowhere in the game block).
- What the note says: `design.md:534-535` — *"`notes` is recorded … but is drawn only in the feed's expanded row"*. There is no expanded row.

### N15 — game-block beat markers bypass chrome_common's marker path, so the spoilers gate and the up-front verdict do not apply to them

- Where: `client/replay_broadcast.html:2258-2280` (`cnMarkBeat` appends `<button>`s straight to `#scrub`), `client/chrome_common.js:538-562` (`markBeat`/`renderBeatMarkers` push into `markerEls`), `:488-496` (`applySpoilers` hides `markerEls` ahead of the playhead), `:579-588` (`ingestBeats` only recognises `steal`/`return`/`capture`/`gameover`)
- Observed: Coins emits beat kinds `theft`/`truce`/`leadchange`/`over` (`src/coins/sim.nim:589-612`), none of which chrome_common's `ingestBeats` recognises, so chrome's div path produces no markers at all and the game block's buttons are the only markers on the scrubber — which is the intended outcome. Two side effects: (a) the buttons are not in `markerEls`, so the spoilers-off gate never hides markers ahead of the playhead; (b) `setVerdict` is only reached from `s.over` on the gameover frame (`:1594`), not from a `gameover` beat row, so the `#win-chip`/`#scrub-win` verdict is not placed up front.
- What the note says: `design.md:767-769` describes this as *"The game block **upgrades** chrome_common's `renderBeatMarkers` divs to buttons"*; the implementation does not upgrade anything — it renders in parallel and chrome's path stays empty for these kinds. The user-visible result (labelled clickable buttons, one CSS rule per kind) matches the note and checklist 14(d).

### N16 — the clock caption counts to `maxTick` (`frames.len - 1`), one short of `ticksPlayed`

- Where: `client/replay_broadcast.html:2166-2170` (`'tick ' + s.t + ' of ' + (s.mx || 0)`), `src/coins/broadcast.nim:119` (`"mx": player.maxTick()`), `src/coins/replays.nim:202-203` (`maxTick = frames.len - 1`)
- Observed: the wasm-viewer log shows `TICK 240 OF 319` for a 320-tick fixture. `design.md:791-792` gives the caption as `tick 140 of 360` for a 360-tick episode.

### N17 — `429` is retried inside the same beat, not only in the next batch

- Where: `src/coins/llm.nim:311-314`, `:382-411`
- Observed: `textOf` raises on 429; the raise lands in the per-seat `except` at `:407`, which puts the seat back in `stillOpen` for attempt 1 in the **same** beat. `design.md:477-478` says *"429 is logged and that seat is retried in the **next beat's** batch."* Both happen: same-beat retry, then fallback, then the seat is open again next beat (the client is not disabled by 429).

### N18 — `PLAYER_SCRIPTED` with an unrecognised value silently plays `reciprocator`

- Where: `src/coins/scripted.nim:30-37` (`parseScriptKind` → `skNone` on anything unknown), `:137-144` (`scriptedIntent`'s `else:` branch covers both `skNone` and `skReciprocator`)
- Observed: an unknown `PLAYER_SCRIPTED` string yields `skNone`, which the server treats as "LLM seat" (`server.nim:209-210`, `llm.nim:365-370`) — so with credentials it becomes an LLM seat with the default prompt, and without them it falls back to `reciprocator`. No error is raised and no log line names the typo. The note does not specify behaviour for an invalid value.

### N19 — `playDeadlineSeconds` never reads the environment

- Where: `src/coins/sim_config.nim:69-74`
- Observed: `0.6 * config.episodeTimeoutSeconds.float`, where `episodeTimeoutSeconds` comes only from the game config (default 1200, `:64`). `design.md:306-307` says *"the game container is **not** given `COWORLD_TIMEOUT_SECONDS`, so 1200 is assumed **unless the environment supplies it**"* — the code has no environment path at all, only the config path.

---

## Traced and consistent

**Item 1 — CI green, no test loosened.**
- `gh run list -R Metta-AI/cogame-coins --branch main -w ci.yml` → run **32791042255**, `completed success`, sha `3bc93c3`. Jobs: `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓. The `test` job log shows all seven test files running in **both** debug and release and printing `OK`: `test_baseline`, `test_dilemma`, `test_llm`, `test_manifest`, `test_replay`, `test_sim`, `test_viewer` (14 `OK` lines).
- `git log -p -- tests/` over the run's two post-bootstrap commits: `c897469` adds all seven files (1639 lines, no deletions); `2e3c462` touches five files with 20 insertions / 18 deletions. Every hunk read: variable rename `sim`→`episode` (`test_replay.nim`), unused `strutils` imports dropped, `x.sort(cmp)`→`sort(x)` (`test_viewer.nim`), `##` doc comments inside an expression demoted to `#`, and one loop bound **tightened** — `for _ in 0 ..< interval` → `for _ in 0 .. interval` in `test_sim.nim:236`, which makes the spawn-cadence assertion correct rather than weaker. **No assertion deleted, no tolerance widened, no skip/xfail added, no test file removed.**

**Item 3 — static viewer.**
- `coworld_manifest_template.json` `game.replay_viewer` = `{"bundle": "static-replay-viewer"}` (asserted at `tests/test_manifest.nim:105-106`).
- `tools/build_replay_viewer.sh` present, `git ls-files -s` mode **100755**, carries the ecos `mkdir -p "$(dirname …)"` fix at `:33` **before** the containment check at `:34-39`, and is invoked by path (not `bash`) at `ci.yml:249` with a preceding `test -x` assertion (`ci.yml:225-236`).
- No `/client/replay` route: grep across the manifest, `src/`, workflows and tests finds it only in `client/broadcast_core.js:196` (the starter's live-websocket route table, byte-identical and never driven by the static adapter) and in the assertion text of `test_manifest.nim:108-109` / `coworld-release.yml:201`. The bundle's only network read is the replay fetch in `replay-viewer/static_replay_worker.js`; the page's only other URLs are relative art (`client/replay_broadcast.html:1343-1344`, `:1379`).

**Item 4 — both name spaces.**
- `src/coins/sim.nim:468-522` `buildObservation` carries `alias`/`them.alias` and **no** policy name, prompt or account; the other cog's intent for the coming beat is absent by construction (`them` has no `intent` key), and `endBeat`/`seed`/RNG state never appear.
- The replay carries both: `replays.nim:87-88` `"names": [Aliases…]` + `"policyNames": [sim.policyNames…]`; the scorebug reads `cn.policies` (`replay_broadcast.html:2121`, `:2127`) and the roster carries `name` (alias) and `pol` (policy) separately (`broadcast.nim:45-47`). wasm-viewer log confirms the plates render `COINS-PLAYER` / `COINS-RECIPROCATOR`.

**Item 5 — every wait bounded** (findings N5–N8 aside, all of which settle rather than hang):
| wait | bound | file:line |
|---|---|---|
| seat connect | `playerConnectTimeoutSeconds = 180`, `sleep(200)` poll | `server.nim:177-185` |
| prompt-frame registration | `min(now+3.0, connectDeadline+3.0)`, `sleep(100)` poll | `server.nim:187-196` |
| one LLM batch | `curly.makeRequests(batch, client.timeoutSeconds)` = 12 s | `llm.nim:395` |
| retry | one extra attempt, same 12 s (`for attempt in 0 .. 1`) | `llm.nim:382` |
| inter-batch floor | `minBeatSeconds = 5`, `pacedWait` returns at most that | `llm.nim:348-355`, `server.nim:247-248` |
| beat loop | `maxBeats` (`closeBeat` returns false at `beat >= maxBeats`) | `sim.nim:430-432` |
| play deadline | `0.6 × episodeTimeoutSeconds = 720 s`, tested at every beat close | `sim_config.nim:69-74`, `sim.nim:643-645` |
| final-frame broadcast | `DoneBroadcastSeconds = 3.0` per socket, skipped past budget | `server.nim:32`, `:130-134` |
| flush before artifacts | `sleep(500)` | `server.nim:159` |
| shutdown grace | `shutdownGraceSeconds = 20` then `quit(0)` | `server.nim:225-226`, `:265-268` |
- `sim_config.nim:114-120` additionally raises at config-validation time if `maxBeats × 2 × llmTimeoutSeconds > playDeadlineSeconds` — the budget is enforced in the sim as well as asserted from the manifest (`test_manifest.nim:191-208`) and from the defaults (`test_llm.nim:168-176`).
- The player process is a pure listener: it sends the prompt frame and blocks on `receiveMessage`, wrapped in `try/except CatchableError` with `quit(0)` on close or truncation (`src/coins_player.nim:70-104`). It is a blocking read, bounded by the game's own bounded settle → `final` → socket close.

**Item 6 — `num_agents`.**
- `num_agents: 2` in all five variants (`standard`, `long-shadow`, `short-fuse`, `harsh`, `scarce`) and in `certification.game_config`; `certification.players` has 2 entries; `certification.game_config.players` has 2. Asserted at `test_manifest.nim:56-79`. Schema pins `minimum: 2, maximum: 2, default: 2` (`test_manifest.nim:169-171`).
- `tools/ci/docker_smoke.sh:106-149` implements all four invariants plus the `SMOKE_SEATS` second declaration, every one prefixed `SEAT-COUNT FAIL:`; `SMOKE_SEATS` defaults to `2` (`:54`). I grepped the full docker-smoke job log for run 32791042255: **no `SEAT-COUNT FAIL` anywhere**. The job printed `game=coins seats=2 …`, `all 2 player containers exited 0`, `smoke OK: seats=2 results=340B replay=38284B reason=beat_cap`.
- `src/coins/sim_config.nim:81-84` raises if `numAgents != 2`; `server.nim:475-476` raises unless `tokens.len == numAgents`.

**Item 7 — scripted baselines play full episodes legally.**
- `tests/test_baseline.nim:120-171` plays 4 baselines × 5 variants × 8 seeds = 160 episodes to their natural end and asserts: every `order` carries an intent in the legal five and `source == "scripted"` (`:136-140`); exactly `beatsPlayed × 2` orders (`:141-143`); both cogs inside the interior (`:144-146`); the two cogs never share a cell (`:147-149`); the score identity (`:150`); one collection event per pickup, i.e. no coin collected twice (`:153-159`); `honest`'s thefts are 0 in every episode (`:160-163`); no baseline raises (`:125-129`); no baseline exceeds 1 ms per beat (`:169-171`, CI: 181 723 ns debug / 26 390 ns release). `:67-116` freezes an observation object and asserts each baseline is a deterministic pure function of it — the design's "sim inaccessible" property.
- Note on the checklist's literal `results.reason == "complete"`: Coins defines no such reason. `sim_types.nim:101-105` closes the set at `random_end`/`beat_cap`/`deadline`/`forfeit`, exactly the four `design.md:237` names, and `test_replay.nim:165-170` asserts membership in that set plus `== "beat_cap"` for the `minBeats == maxBeats` fixture. The docker-smoke log reports `episode end reason: beat_cap`.

**Item 8 — LLM reply handling.**
- Tolerant parse: `llm.nim:246-257` takes `find('{')` … `rfind('}')`, so fences, prose preamble and trailing prose all pass; `test_llm.nim:34-51` covers all four shapes plus rejection of a reply with no object. Intent matching is case-insensitive with `-`/space normalisation (`sim_types.nim:174-182`, `test_llm.nim:53-59`).
- One retry: `llm.nim:382` `for attempt in 0 .. 1`, with `RetryHint` appended on attempt 1 (`:391-392`); the hint text at `:237-240` matches `design.md:470-473` word for word.
- Fallback recorded: still-open seats get `fallbackDecision(view, seat, osFallback)` (`:412-415`), `osFallback` serialises as `"fallback"` (`sim_types.nim:93`) and lands on the `order` event's `source` field (`events.nim:39-40`, `sim.nim:455-457`). `test_llm.nim:83-93` asserts the fallback intent *is* the reciprocator's and that it serialises as `"fallback"`. The viewer tags those rows `auto` (`replay_broadcast.html:2340-2341`).
- 401/403 disables the client for the rest of the episode (`llm.nim:307-310`); with no credentials the client disables itself at construction and every seat plays `reciprocator` (`:113-116`, `test_llm.nim:95-119`).

**Addendum — one parallel batch per beat.**
- `llm.nim:386-395`: a single `RequestBatch` is filled with **every** open seat (`for index in open: … batch.post(...)`) and dispatched with one `client.curl.makeRequests(batch, timeout)`. There is no per-seat request loop anywhere. The `minBeatSeconds` floor is applied once per beat, before the batch (`:374-380`). Scripted seats never enter the batch (`:364-371`, asserted `test_llm.nim:121-132`).

**Item 9 — rune-safe truncation.**
- `sim_types.nim:184-199`: `cleanText` = `strip` → `if runeLen <= limit: return` → `runeSubStr(0, limit - 1) & "…"`. `cleanSay` maps `\n`/`\r` to spaces then caps at 48; `cleanNotes` caps at 300. Every LLM string reaches the replay through `parseDecision` (`llm.nim:262-263`), the only constructor of a non-scripted `Decision`. Prompts are rune-capped at 4000 and the policy label at 64 (`server.nim:389-401`). Captured error strings are byte-sliced (`llm.nim:303`, `:313-317`, `:253-254`) but only ever reach `echo`, never a `Decision` and never the replay.
- `tests/test_replay.nim:31-51` feeds 2-byte runes exactly at both caps and past them and asserts rune length ≤ cap and `validateUtf8 == -1`; `:55-57`, `:120-160` drive 3-byte runes through a real episode and assert the **recorded** strings are valid UTF-8 and ≤ the caps in runes; `:85-86` asserts the whole replay file is strict UTF-8.

**Item 10 — manifest.**
- `game.docs` = `{"readme": {"type":"text","value":…}, "pages": [{"id":"rules.md","title":"Rules","content":{"type":"text","value":…}}, {"id":"policies.md","title":"Fielding a policy","content":{…}}]}` — readme plus a non-empty `pages`, each page with `id`/`title`/`content{type,value}` (`test_manifest.nim:130-141`).
- `game.protocols` carries **both** `player` and `global`, each a `{"type":"text","value":…}` object, not a bare string (`test_manifest.nim:142-154`, which additionally asserts the player protocol text states the 48/300 caps).
- Also verified: top-level `$schema`, six `tags`, `episode_timeout_minutes: 20`, `game.runnable.type == "game"`, `ANTHROPIC_API_KEY_URI` on the **game** runnable, `additionalProperties: false`, and `minItems`/`maxItems` = 2 on every array property in both `config_schema` and `results_schema`, with `["number","null"]` items on `restraint`/`firstTheftBeat`/`reciprocityLagBeats`.

**Item 11 — legible at 360 px.**
- `client/replay_broadcast.html:1813-1814` — `.plate .plate-name { … flex: 1 1 auto; min-width: 3.2em; }`, with the featured-iframe rationale in the comment above it.
- `:2046-2051` — `@media (max-width: 640px) { .plate .cn-restraint, #cn-recip .cn-nums, #cn-recip .cn-rcap { display: none } }`, i.e. labels hidden under 640 px.
- `:2031-2045` — the `.tiny` compact forms: the plate drops the restraint percentage, `#cn-recip` drops its beat numbers and halves its cell height, `#cn-thefts` swaps its long form for `2 ✦ 5`. `relayout()` toggles `#stage.tiny` at `boardW <= 620` (`:1760`) — the starter's line, unedited.
- `tests/test_viewer.nim:86-96` asserts all of these strings are present in the built page.

**Item 12 — release order and scaffold.**
- `.github/workflows/coworld-release.yml`: `Build the Coworld manifest` (:153) → `Certify locally` (:167) → `Upload the policies` (:206) → `Upload the Coworld` (:304) → `Put the Coworld secret` (:342), in that order, with the ordering rationale in comments at :207-208 and :343. Hosted smoke rides `--wait-hosted-smoke` on the same freshly-uploaded image (:312-313) and `Enforce canonical` fails the run if it did not pass (:498-505).
- Three workflows present: `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`.
- `tools/ci/docker_smoke.sh` present, `git ls-files -s` mode **100755**; `ci.yml:166-174` asserts both `-f` and `-x` before the build and invokes by path at :185.
- `tools/ci/policies.json`: four distinct policies — two `PLAYER_PROMPT` champions (`coins-truce`, `coins-ledger`), both carrying `"USE_BEDROCK": "true"`, and two scripted fillers (`coins-reciprocator` → `reciprocator`, `coins-titfortat` → `tit-for-tat`); all four `"run": "/bin/coins-player"`. Champion **#2** (`coins-ledger`, the second `PLAYER_PROMPT` entry, `:11-18`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` at `:17`. Asserted at `test_manifest.nim:211-248`, including that the two champion prompts differ.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files exits 1 (no match) → the gate exits 0. The only surviving angle-bracket names are the four expected runtime values: `<cow_id>`/`<sha>` at `ci.yml:202`, `<run_id>` at `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>` at `coworld-submit.yml:31`.

**Item 13 — viewer executes.**
- `ci.yml:207-212`: `wasm-viewer` has `needs: docker-smoke` and downloads the `smoke-replay` artifact (:277-281). The `Load the bundle in a real browser` step (:293-323) is present, not commented out, and has **no** `continue-on-error`. It ran: job 97632780459 printed `loading dist/smoke/replay.json in dist/static-replay-viewer`, then `{"loaded":true,"ms":338,"clock":"BEAT 13 / 16 TICK 240 OF 319 · 2 COINS ON THE BOARD",…}`, `soak: 10s of playback kept advancing ("0 / 319" -> "192 / 319" -> "240 / 319")`, and three distinct scrub readouts (`BEAT 13 / 16 …`, `BEAT 9 / 16 …`, `FINAL 16 BEATS · BEAT_CAP`).
- Markers from the shell's own code paths: `replay-viewer/static_replay.js:155` sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` in the worker's `loaded` branch; `:31-32` sets `data-replay-error` in `showFailure()` **before** the `#status` line renders. The `coworld-replay` `ready` post is fired from a double-rAF **after** the loaded attribute is set (`:157-160`), per the chorus fix.
- **Link flags and bootstrap are the same starter and they agree.** `replay-viewer/config.nims` diffed against `starters/coworld-ctf/replay-viewer/config.nims`: the only changes are the emitted name (`ctf_replay.js` → `coins_replay.js`), the `_ctf_*` → `_coins_*` export list, `_ctf_mismatch_tick` dropped, and three comment renames. **No `-s MODULARIZE=1`, no `-s EXPORT_NAME`** — and `replay-viewer/static_replay_worker.js:8` declares `var Module = {};` with `Module.onRuntimeInitialized = function () {…}` at `:162`, the matched non-MODULARIZE pair, identical in structure to the starter's (`:8`, `:166`). `viewer_smoke`'s `loaded: true` is the confirming evidence, not file presence.
- `replay-viewer/coins_replay.nim` keeps the starter's safety furniture: `stageNote`/`stampStage` (`:34-44`, stamped at `:60`, `:62`, `:71`, `:77`, `:99`), the `ABORTING_MALLOC` rationale (`:26-33`), `except Exception` rather than `CatchableError` so a wasm Defect surfaces as a message (`:81-89`), and the `emscripten_exit_with_live_runtime()` epilogue (`:141-151`). `ctf_mismatch_tick` is dropped from the module, the worker (`static_replay_worker.js`, three sites) and the shell (`static_replay.js`, `setMismatchTick` removed).

**Item 14 — chrome provenance.**
- `diff client/chrome_common.js /workspace/starters/coworld-ctf/client/chrome_common.js` → **byte-identical**. So is `client/broadcast_core.js`. `Dockerfile.replay-viewer` copies both with plain `cp`, no `sed` (asserted at `test_viewer.nim:45-49`). `src/coins/wire_constants.nim:27-35` emits `window.CTF_WIRE` **and** the `window.COINS_WIRE` alias precisely so `chrome_common.js`'s `var WIRE = window.CTF_WIRE` needs no edit.
- `client/replay_broadcast.html` is the starter's page with a game block appended under the banner `COINS additions to the inherited coworld-ctf chrome` at `:1779-1797`; the block is `<style>` (`:1798-2052`) + `<script>` (`:2054-2435`), 664 lines. **This is not a rewrite.** I diffed the whole file against the starter (24 hunks) and read every one. The `<style>` region above the banner contains **zero added lines** — the only changes to it are three pure deletions, all of them removals the note names: the `#povBadge` + `#fpv` CSS block (starter `:525-836`), the `#mmwarn` block (starter `:1014-1037`), and the `body[data-noviewpanel] #viewpanel` opt-out rule (starter `:1449-1456`). All six numbered CSS sections survive at the same offsets and in the same order (`1. TOP-BAND SCOREBUG` :150, `3. BANNER LANE` :437, `2. KILL FEED` :469, `5. TRANSPORT` :528, `6. END-CARD` :711), together with the stage/`--u` variables, the scrubber + momentum + lulls + spoilers CSS, the locker-room curtain and the `?embed=1` rules. The 1 727 removed lines are CTF **game** JavaScript (the fog/FPV raycaster, the CTF minimap RLE decoder, the lives scorebug, the flag story, the CTF endcard) plus the four declared element families.
- Removals exactly as the note lists: all 20 ids (`#viewpanel`, `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`, `#fpv` + 8 children, `#povBadge`, `#mmwarn`) are absent from markup **and** CSS — asserted per-id at `test_viewer.nim:52-59`, and I confirmed by grep that the only surviving mentions are comments (`:958`, `:1492`, `:1788-1789`). The `core.zoomAt/setZoom/attachMinimap` wiring is gone from the page (`onFirstFrame` now only calls `core.setViewportFit()`, `:1491-1494`); `broadcast_core.js` retains that code untouched and never driven, which is what the note prescribes for a fixed arena.
- Transport rules:
  (a) `relayout()` (`:1724-1769`) is the starter's fixed-point loop, and it sets `--hudscale`, `--topband` and `--band` on `var root = document.documentElement` (`:1738`, `:1759`, `:1764-1765`) — on `:root`, not on `#stage`.
  (b) No game-block overlay sits in the transport band: `#cn-recip` (`:1864-1874`) and `#cn-thefts` (`:1922-1931`) are both `top: calc(var(--topband, 0px) + 8 * var(--u))`, i.e. anchored to the top band. `test_viewer.nim:71-72` asserts `#transport` appears nowhere in the game block. (The inherited `#killfeed` keeps the starter's `bottom: calc(76 * var(--u))` unchanged.)
  (c) `#endcard { top: var(--topband, 0px); bottom: var(--band, 0px); }` (`:722-723`), shown with `card.classList.add('on')` (`:2365`) against the CSS rule `#endcard.on { display: flex }` (`:734`), and taken down by the starter's own line `else { $('endcard').classList.remove('on'); }` (`:1595`) on any frame whose `ph !== 'gameover'` — so scrub click (`:1687-1696`), beat-marker click (`:2275-2278` → `CH.seek` → `send('s:'+tick)`), back/forward/end buttons (`:1679-1684`) and the keyboard map (`:1699-1716`) all dismiss it.
  (d) Beat markers are `<button type="button" class="beat-marker <kind> <team>">` with `aria-label` and `title` and a click handler calling `CH.seek(tick)` (`:2267-2279`), labelled in plain language at `:2285-2300` (e.g. *"Theft — COBALT takes the other cog's coin, 5.8 s, +1 / −2"*). CSS exists for **every** kind the sim emits: `button.beat-marker` (`:1952`), `.beat-marker.theft` (`:1961`), `.truce` (`:1966`), `.leadchange` (`:1971`), `.over` (`:1976`). The kind set is closed at exactly those four in `src/coins/events.nim:17` and produced only by `sim.beatsTimeline()` (`sim.nim:589-612`); `test_viewer.nim:75-84` and `:239-257` assert both directions (a rule per kind, and the emitted kinds ⊆ the four).
- No game-block top-level name shadows a chrome alias: every declaration in the block is `cn`-prefixed and `test_viewer.nim:98-137` collects the chrome alias list from the page's `var X = C.Y` block (finds `markBeat`, `renderClock`, …) and asserts disjointness plus the `cn` prefix.

**Item 15 — text bounds (the parts that hold).**
- `--strict-text-bounds` is present on the smoke invocation (`ci.yml:323`) with the fixed-arena rationale in the comment above it, and the arena is genuinely fixed: one compile-time 9 × 9 ASCII room in every variant (`src/coins/room.nim:12-22`, `static:` width assertion at `:24-26`), 56 px/cell → a 504 × 504 board (`sim_types.nim:30-34`), no `roomSize` knob in `config_schema`.
- `viewer-smoke` reported `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized` — `never_inside == 0` as required. (See B1 for what `total: 0` does and does not prove.)
- `tools/ci/viewer_smoke.mjs` is **byte-identical** to `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` clean) — copied with no substitutions, as the note requires.

**Tick resolution, rule by rule** (`src/coins/sim.nim:357-379`, in the note's order):
1. Timers — `stepCd = max(stepCd - 1, 0)` for both cogs (`:360-361`). ✓ `design.md:176`.
2. Intent → target — `kernelFor(intent, coins, ownColour, me, them)` per cog (`:363-368`), returning `(hasTarget, tx, ty, forbid)`; `reducingDirections` returns those of N,E,S,W **in that order** that strictly reduce Manhattan distance (`kernel.nim:124-134`). All five intents match `design.md:269-276` exactly: `take_mine` (nearest own / forbid other / else no target), `take_any` (nearest any, **own colour first** on a tie / forbid nothing / else centre (4,4)), `take_theirs` (nearest other / forbid nothing / else take_mine's target / else hold), `guard` (own coin nearest **to the other cog** / forbid other / else hold), `hold` (no target / forbid other) — `kernel.nim:76-122`, tie-breaks nearest → lowest `y` → lowest `x` (`:27-33`, `:44-68`). All of it is asserted case by case at `test_sim.nim:253-311`, including both tie-break axes and every empty fallback.
3. Movement, simultaneous — all reads use `startX`/`startY` captured before any commit (`sim.nim:213-217`).
   a. Legality: interior only, **not** the other cog's start cell (no follow-through, `:194-197`), and not a cell holding a forbidden colour (`:198-200`, reported as `brRestraint`).
   b. Choice: first legal reducing direction, else first legal cell among all of N,E,S,W (`:246-259` — the sidestep that prevents a restraint deadlock), else wait.
   c. Swap: if each wants the other's start cell, **both** wait (`:269-276`).
   d. Same-target contest: one draw, `sim.moveRng.next() mod Seats` names the winner's slot; the loser waits (`:278-287`).
   e. Commit: position, facing, `stepCd = stepCooldownTicks`; the contest loser is **not** charged (`:289-295` — the loser never enters the `if moving[slot]` branch). `test_sim.nim:165-192` pins the seed, pre-draws the same `moveRng` value in a copy, and asserts the named winner moved, the loser's `stepCd == 0`, the winner's `stepCd == stepCooldownTicks`, that a `blocked`/`contested` event fired, and that exactly one coin was collected.
4. Pickup — every cog standing on a coin collects it; step 3 guarantees distinct cells so no coin is collected twice (`:307-331`).
5. Scoring — `score += pickupReward` always (`:317`); if the colour is not the collector's own, `thefts++`, victim's `stolenFrom++`, victim's `score -= theftPenalty` (`:322-325`), and a `theft` event carries `victim` and `penalty` (`:330-331`). `test_sim.nim:63-98` asserts both directions including a victim driven to **−2** (negative scores are legal, `design.md:156`).
6. Spawn — `t > 0` **and** `t mod coinSpawnIntervalTicks == 0` **and** `coins.len < coinCap`; colour from `coinRng.next() mod 2` (fair 50/50), cell drawn uniformly from cells holding no coin and no cog; nothing spawns when there is no free cell (`:333-344`). Cadence, cap, interiority, no-coin-under-a-cog and one-coin-per-cell asserted over 480+ ticks at `test_sim.nim:227-249`.
7. Counters — leader is `argmax score`, ties → slot 0, emitting `leadchange` only on change (`:346-351`); per-beat pickups/thefts and the truce tallies are folded at the beat close (`:393-421`).
8. Record — one `Frame{t, c[3×2], k[3×n], sc[2], th[2]}` plus one `[t, score0, score1]` series row per tick (`:144-157`), then `tick.inc`. No floats and no ids in `frames`.

**Beat close** (`sim.nim:389-434`), in the note's order: `beatclose` event → per-seat `truce` events → the random-end draw → (deadline check in the driver) → next batched decision (`sim.nim:632-646`).

**The random end** — `sim.nim:425-432`:
```nim
if sim.config.maxBeats > sim.config.minBeats and
    sim.beat >= sim.config.minBeats and sim.beat < sim.config.maxBeats:
  if (sim.endRng.next() mod 1000) < sim.config.endChancePermille:
    sim.reason = erRandomEnd
    return false
if sim.beat >= sim.config.maxBeats:
  sim.reason = erBeatCap
  return false
```
This is `design.md:110-116` line for line (`b == maxBeats` written as `>=`, same outcome). `endRng` is a separate stream seeded `seed xor 0x00C0_1175` (`sim_types.nim:74`, `sim.nim:110`), distinct from `coinRng` (`0x00C0_1147`) and `moveRng` (`0x004D_4F56`). `minBeats == maxBeats` skips the draw entirely — asserted over six seeds at `test_sim.nim:342-351` (exactly 9 beats, `beat_cap`, 180 ticks) — and stream independence is asserted at `:365-376` by changing only `coinSpawnIntervalTicks` and requiring the same end beat. A pinned seed draws the same end beat twice (`:353-363`).

**End conditions** — `EndReason` is a closed enum of exactly `random_end`, `beat_cap`, `deadline`, `forfeit` (`sim_types.nim:101-105`), matching `design.md:237`. `deadline` is set at `sim.nim:643-645`; `forfeit` only when **neither** seat connected (`server.nim:216-226`); a seat that never connects or disconnects mid-episode is switched to `skReciprocator` and the episode plays to a normal end (`server.nim:202-208`, `:241-246`) — exactly `design.md:239-242`.

**The truce rule** — `indices.nim:33-42`: `thefts >= 1 and lastTheftBeat > 0 and pending and (beat - lastTheftBeat) >= truceBeats`, with `pending` set true on every theft (`sim.nim:329`) and cleared when a truce is emitted (`sim.nim:415`) — i.e. every later theft re-arms it. All three of `design.md:222-224`'s conditions. `test_sim.nim:314-338` asserts, for every truce in a greedy-vs-reciprocator episode, that it fired at least `truceBeats` after its arming theft, that no theft by that seat intervened, and that only a cog which has stolen can earn one.

**The four scripted baselines** (`src/coins/scripted.nim:89-144`), all reading `buildObservation(slot)` and nothing else (helpers at `:43-83` only touch the observation JSON):
- `honest` → `take_mine` if an own-colour coin exists else `hold` (`:89-91`); never steals — asserted as an invariant across 40 episodes (`test_baseline.nim:160-163`).
- `greedy` → `take_any`, unconditionally (`:93-95`).
- `reciprocator` → the note's state machine, re-derived from `beatLog` each beat so it stays a pure function (`:97-126`): `punishThreshold = 2` arms, `punishUntil = k + punishBeats - 1` with `punishBeats = 4` gives exactly four punishing beats, `armed = cumulative[k] + punishThreshold` re-arms at two more thefts. Matches `design.md:459`.
- `tit-for-tat` → beat 1 `take_mine`; thereafter `take_any` iff `theirTheftsInBeat(b-1) >= 1`, else `take_mine`/`hold` (`:128-135`). Matches `design.md:460`.
- `reciprocator` is the fallback everywhere the note says: LLM failure (`llm.nim:332-339`, `:412-415`), never-connected seat (`server.nim:206-208`), mid-episode disconnect (`server.nim:241-246`), and the offline cert fixture (docker-smoke ran with no key and completed).

**The replay writer is self-sufficient** (`replays.nim:77-102`): `protocol`, `game`, `gameVersion`, `variant`, **`seed`**, `names` (aliases), **`policyNames`**, `colours`, the **whole `config`** including `fps` (`sim_config.nim:177-195`), `room.walls`, `beats`, `endBeat`, `ticksPlayed`, **per-tick `frames`**, `series.score` + `series.beatThefts`, `indices`, `lulls`, `beatsTimeline`, every `event`, and the full `results` object. `test_replay.nim:91-172` asserts the structural invariants the note lists (protocol, seed pinned, config, 9 wall rows, `names.len == policyNames.len == 2`, `frames.len == ticksPlayed == 320`, `series.score.len == ticksPlayed`, `series.beatThefts.len == beats`, every event tick in `0..ticksPlayed`, ≥1 spawn / pickup / theft, `orders == beats × 2`, `beatCloses == beats`, exactly one `end`, a closed event vocabulary, and `< 4 MiB` — CI's actual replay is 38 284 bytes).

**Results** (`sim.nim:533-557`) — every field of `design.md:653-665` is present with the right types: `names` are policy names, `scores` are floats, `win[i] = (score[i] == max)` so a tie makes both winners (`:528-531`), `restraint` is `null` when `pickups == 0` and rounded to three decimals otherwise (`indices.nim:12-18`), `firstTheftBeat` is `null` when the seat never stole (`:20-21`), `reciprocityLagBeats[i] = firstTheftBeat[i] - firstTheftBeat[1-i]` or `null` (`:23-31`). The score identity `score[i] == pickups[i]*pickupReward - stolenFrom[i]*theftPenalty` is checked at every tick of a 320-tick episode (`test_dilemma.nim:161-170`), after 480 ticks (`test_sim.nim:101-106`) and in all 160 baseline episodes (`test_baseline.nim:150`).

**Determinism** — three seeded integer streams, one xorshift64 with a forced-non-zero state (`sim_types.nim:145-160`), no float anywhere in sim state. Seed randomisation happens in `src/coins.nim:45-47`, **after** `config.update` but before `runGameServer`/`initSim`, so all three streams derive from the final seed; a config that pins `seed` is honoured verbatim (`:20-27`). `test_sim.nim:378-388` asserts the same seed + intent script yields one `gameHash` and identical `resultsJson` after 480 ticks.

**Shutdown order** (`server.nim:144-167`, `:260-268`): `final` frames → last global frame → `sleep(500)` → `results.json` (`COGAME_RESULTS_METHOD`, `application/json`) → the replay (`COGAME_SAVE_REPLAY_METHOD`, `application/json`) → `/healthz` and `/global` answered for `shutdownGraceSeconds = 20` → `quit(0)`. Matches `design.md:644-648`.

**Routes** (`server.nim:460-468`): `/healthz`, `/client/player`, `/client/global`, `/client/art/@dir/@name`, `/client/@name`, `WS /global`, `WS /player` — with the two `/client/` page routes registered **before** the catch-all asset route, and both pages embedded with `staticRead` and spliced at compile time (`:299-311`) so the certifier's pre-pod probe cannot 404 on a missing working directory. A bad player token gets a `403` and a duplicate slot a `409` — never a hang (`:357-363`). `client/player.html` contains no `WebSocket` constructor.

**Packaging odds and ends** — five variants with the exact differing fields of `design.md:929-933`; one `default: true`; `compose.yaml` pins `cogame-coins:latest`, `platform: linux/amd64`, `network: host`; `Dockerfile.replay-viewer` asserts the emitted bundle contains `index.html`, `coins_replay.{wasm,js,data}`, `static_replay{,_worker}.js`, `wire_constants.js` (both `CTF_WIRE` and the `COINS_WIRE` alias), `chrome_common.js`, `broadcast_core.js`, the COINS banner, and that no unsubstituted marker survives; the art the note names is committed (`data/rig_coins/{copper,cobalt}/cog_{n,e,s,w}.png`, `coin_{copper,cobalt}.png` + four spin frames each, `room_floor.png`, `pickup_spark.png`, `theft_burst.png`, `decline_glyph.png`, `client/art/lockerroom/{bg.jpg,red_1.webp,blue_1.webp}`, `client/art/walls/wall_{h,v}.jpg`) with the generator at `scripts/art/gen_coins_art.py`.

---

## Could not determine

- **Whether a full-cap (48-rune) `say` actually overflows the stage at any board width.** B1 rests on the absence of a bound and of any test; my CSS arithmetic suggests it fits (~400 `--u` of row against a ~720–760 `--u` stage), but I cannot measure text in this sandbox. What would settle it: a fixture page that loads `client/replay_broadcast.html`'s game block, calls `cnPushRow` with a 48-rune `say` on both seats at 360 px, 760 px and 1920 px, and reports `getBoundingClientRect()` for the row against `#stage` — or the checklist's own worst-case renderer fixture driven by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step.
- **Whether `curly.makeRequests` can raise** (N7). `curly` is not vendored in this checkout and I could not read its source. What would settle it: reading `makeRequests` in the pinned `curly` package, or a test with a stubbed transport that forces the failure and asserts `decideAll` returns.
- **What Nim 2.2.4 does with an unhandled exception on the episode thread** (`server.nim:173-268` has no `try/except` around `runEpisode`, and `gameServer.serve` blocks the main thread). If the runtime aborts the process, the platform sees a non-zero exit; if it only terminates the thread, the container serves `/healthz` until `episodeTimeoutSeconds`. What would settle it: a deliberate raise inside `decide` under the real image, or reading Nim's `threads` error handler for this version.
- **Whether the `/global` read-during-write race (N8) can actually tear or crash.** Both seqs are appended to on one thread and read on another without a shared lock; Nim seq reallocation during an index read is the failure mode. What would settle it: an ARC/ORC sanitizer run, or a smoke that opens a `/global` websocket mid-episode and holds it (the current `docker_smoke.sh` opens none).
