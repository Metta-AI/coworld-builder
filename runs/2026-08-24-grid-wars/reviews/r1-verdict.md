blocking: 0

# r1 verdict — grid-wars

Head: `ae1f3ea99eb91acda05d0603847eea242bb8a98b` (main; run 32747821831, conclusion `success`)
Checklist: phase-30 brief §ACCEPTANCE CHECKLIST, items 1–14 + simultaneous-batch rule
Independent read written before reading fixes: **yes** — the repo was cloned fresh to
`/tmp/judge-grid-wars`, checked out at the sha above, and all sources, tests, workflows, tools,
the manifest and the chrome-provenance diffs against `/workspace/starters/cogame-bullwhip` were
read and noted **before** `r1-review.md` was opened. `r1-fixes.md` was **not read at any point**
(per the brief), so there is no fixer-report audit in this verdict; every disposition below is my
own verification of the head tree, the CI logs and the git history.

The review (`r1-review.md`) was written against `dbffed2`, sixteen commits behind the judged head.
Every one of its 16 findings (B1–B3, N1–N13) was re-checked **at the current head**. None stands.
A finding that was true at the reviewed sha and is false at head is refuted-as-fixed, not standing.

## Standing blocking findings

None.

## Refuted (at head ae1f3ea)

### B1 — byte-boundary cuts in captured errors → REFUTED (fixed at head)
- Evidence: `src/gridwars/gwl.nim:120-128` — `cutRunes` (`runeSubStr`, rune-counted) is now the one
  truncation; `gwl.nim:130-139` — `charAt` quotes the *whole* character (or `\xNN` for a byte that
  is not valid UTF-8) and the lexer uses it at `gwl.nim:275`
  (`"unexpected character '" & text.charAt(pos) & "'"`). Every former byte slice in `llm.nim` is
  gone: `extractJsonObject` uses `cutRunes(cleaned.strip(), 160)` (`llm.nim:360`), `textOf` uses
  `cutRunes(response.body, 400)` / `(…, 300)` / `(…, 300)` / `cutRunes(result, 160)`
  (`llm.nim:445,453,458,466`), `cleanText` delegates to `cutRunes` (`llm.nim:161-165`), and
  `sim.submit` re-cuts `rejected` with `cutRunes(rejected, 300)` (`sim.nim:949`).
- Tests now cover exactly the reviewer's two probes: `tests/test_replay.nim:79-110`
  ("captured error text reaches the replay on rune boundaries" — an em dash quoted by the lexer,
  plus a long multi-byte rejection, both asserted `validateUtf8() == -1` in the written replay) and
  `tests/test_bot.nim:235-248` ("the quoted excerpt is cut on runes at every offset" — sweeps the
  160-rune boundary across a two-byte character). Both `[OK]` in run 32747821831, debug and
  `-d:release` (test-job log lines 306/333, 501/522).

### B2 — VM numbers are platform `int` (32-bit on wasm32) → REFUTED (fixed at head)
- Evidence: `src/gridwars/gwl.nim:38-44` — `GwlValue* = int64` with the wasm32 rationale in the
  doc comment; `stack`, `globals`, `locals`, `arrays`, `consts` are all `seq[GwlValue]`
  (`gwl.nim:69,89-96`); the overflow checks compare against `high(int64)`/`low(int64)`
  (`addChecked`/`subChecked`/`mulChecked`, `gwl.nim:1093-1138`; `div`/`mod` low(int64)/−1 guards at
  `gwl.nim:1284-1295`). The seed path is int64 end to end: `GameConfig.seed*: int64`
  (`types.nim:15`), `GameEvent.seed*: int64` (`types.nim:60`), `RoundRecord.seed*: int64`
  (`sim.nim:72`), and `mixSeed` does the multiply in wrapping uint64 (`sim.nim:107-117`) so a
  league seed up to 2³¹ cannot overflow-Defect or diverge between targets.
- Tests: `tests/test_gwl.nim:332-341` — `doAssert sizeof(GwlValue) == 8` ("on every target") and
  `2000000000 + 2000000000` must **not** fault; `tests/test_replay.nim:143-184` — a >2³¹ round seed
  survives the event log, re-derives to the recorded digest, and a 32-bit truncation of it is shown
  to produce a *different* digest (the seed is load-bearing). Green at head in both build modes.

### B3 — `painter` loses to the `sentry` fallback; the note's assertion missing → REFUTED (fixed at head)
- Evidence: `data/warriors/painter.gwl` is no longer the note's first guess: turn run is 22
  (`painter.gwl:50` `if run == 22:`), the rival trigger is two cells (`painter.gwl:19` probes
  `who(2,0)` etc.), and bombing is capped at one per fuse (`painter.gwl:37`
  `tick() - last > MAXFUSE`). The grid harness the checklist requires exists and is committed:
  `tools/tune_painter.nim` (sweeps run 6..40 × reach 1..2 × cadence, seeds 1..10 and held-out
  11..40; the kept pick and both measurements are recorded in its header, lines 12-18). The design
  note's copy of the script (design §Scripted baselines) matches the shipped file.
- The assertion the note specifies is now present and strengthened:
  `tests/test_bot.nim:74-100` asserts `painter` beats `sentry` on mean score over seeds 1..10
  **with a margin > 20** and again on held-out seeds 11..20 with swapped seating — `[OK]`
  ("painter beats the sentry fallback on mean score over ten seeds") in run 32747821831, both
  modes. `tests/test_bot.nim:102-118` keeps the bomber/painter ordering honest.

### N1–N13 → all resolved at head (each was advisory; none names a violated checklist item now)
- N1 (builtin-table order): the note now orders FOG **first** (design note §Builtins,
  `docs/plans/…design.md:146` — "FOG (−3) first … a bomb outside the 9×9 window reads FOG");
  code (`gwl.nim:1147-1159`) and note agree.
- N2 (BOMBCOST): note §Constants (`design.md:154-158`) now reads "`BOMBCOST` = this episode's
  `bombCost` (default 12, config 0..60)", matching `gwl.nim:1396` / `sim.nim:369`.
- N3 (/global cadence): note §Live spectator broadcast (`design.md:807-814`) now describes exactly
  the implemented cadence (no send inside the synchronous battle) and why.
- N4 (soak): `ci.yml:323-327` now passes `--soak 10`; the head run's `Load the bundle in a real
  browser` step shows the soak executed and passed (log line 3625, "soak: 10s of playback kept
  advancing" — the `null`s in that line are the absent `#tick` element; the pass was decided on
  `clock`/`scorebug` movement per `viewer_smoke.mjs:401-403`).
- N5 (bomb timing prose): the system prompt (`llm.nim:284-288`) and the rules page
  (manifest `rules.md`) now say the fuse drops in the same tick it was planted, so a bomb planted
  on tick t detonates on t+4 — matching `sim.nim` and `tests/test_sim.nim`.
- N6 (stale notes): `sim.nim:953-958` — `banner` **and** `notes` are both overwritten
  unconditionally on every submission, with the rationale in the comment.
- N7 (/client/replay pod path): gone — no `client/replay.html` in the tree, no `/client/replay` or
  `WS /replay` route in `server.nim:445-453` (`buildRouter` registers exactly healthz, the two live
  pages, renderer/chrome/assets, and the two websockets), `src/gridwars.nim:31-34` exits non-zero
  in replay mode, and `tests/test_viewer.nim:123-134` asserts the absence across the entrypoint,
  the server, the live pages, the renderer and the manifest. `grep -r "/client/replay"` at head
  matches only the guard test, a negative sentence in `coworld-release.yml:201`, and the design
  note (see non-blocking observation below).
- N8 (smoke default entrypoints): `tools/ci/docker_smoke.sh:57-58` now defaults to `/bin/gridwars`
  and `/bin/gridwars-player` (with the compose-service naming rationale at lines 22-29); ci.yml
  still passes them explicitly.
- N9 (§Tests vs ci.yml): the note's §Tests (`design.md:1096-1103`) now describes the template
  `ci.yml` verbatim — `nim r` per file twice, `docker-smoke` building the image inside its own job,
  `wasm-viewer` `needs: docker-smoke`.
- N10 (frame-by-frame): `tests/test_replay.nim:197-223` now compares **every** re-derived frame to
  `sim.frameStates()` (`check mismatch == -1`), on top of the per-round digest over 20 seeds.
- N11 (live snapshot cost): `sim.nim:1047-1099` — `buildFrames` takes `fromRound` and
  `liveStateJson` builds only the last round's frames, folding earlier rounds' series rows in;
  asserted equal to the full tail at `tests/test_replay.nim:225-253`.
- N12 (beat colour): `client/chrome.css:594-597` adds the two-class
  `.beat-marker.submit.seatN` / `.beat-marker.roundend.seatN` rules; asserted at
  `tests/test_viewer.nim:85-95`.
- N13 (two sentries): `tests/test_bot.nim:38-45` asserts `SeedScript == warriorLines(skSentry)`.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32747821831**, conclusion `success`, headSha = judged sha; all three jobs green; all six test files executed twice (debug + `-d:release`), test-job log. `git log -p --since=2026-08-24T10:40:00Z -- tests/` read hunk by hunk: the **only** deleted assertion in the whole window is `check $replayed[^1] == $frames[^1]` (1ed9b7b), replaced in the same hunk by a frame-by-frame loop + `check mismatch == -1` — strictly stronger; the "both replay pages" test lost its `client/replay.html` half only because b4e0c5d deleted that file (as item 3 requires) and gained a new absence test; no `skip`/`xfail`/tolerance-widening anywhere; no test file removed. |
| 2 Replay re-derivation | PASS | `sim.nim:1258-1286` `replayMatch` re-runs `runBattle` from seed+spawn+scripts and raises on digest mismatch; the wasm module drives the same path (`replay-viewer/gridwars_replay.nim:43` builds its frames from `replayMatch`, never from a parallel recording); tests: digest over 20 seeds (`test_replay.nim:127-141`), tamper caught (`:186-195`), frame-by-frame equality (`:197-223`). |
| 3 Static viewer | PASS | `coworld_manifest_template.json:16-18` `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode `100755` (`git ls-files -s`), `mkdir -p` before containment (`:46`); shell contacts only the `?replay=` URL + bundled assets (`static_replay.js:67-121`, `assetBase:"./assets"`); no `/client/replay` anywhere in code/manifest (guard test `test_viewer.nim:123-134`). |
| 4 Both name spaces | PASS | Aliases only in prompts/observations (`sim.nim:119-130` `tableNames`, `sim.nim:1349-1403`; `test_prompt.nim:98-116` asserts no policy name, no seed); viewer maps alias→policy name for non-baseline seats (`renderer.js:339-367` `makeNameMap`/`isBaselineFiller`); `results.names`/`policyNames` carry policy names (`sim.nim:1004`, `sim.nim:1297-1299`). |
| 5 Degrade-never-hang | PASS | Connect wait bounded by `playerConnectTimeoutSeconds` (`server.nim:190-198`, starts regardless); LLM batch bounded by `llmTimeoutSeconds` (`llm.nim:505`), at most 2 batches; pre-batch reserve check `now + 150 > playDeadline ⇒ endEarly` (`server.nim:233-247`), play budget `0.6 × timeout` (`server.nim:216`, = 720 s of 1200); battle is bounded integer ops; pacing sleeps bounded (`sim.nim:141-142`, `server.nim:293-307`); no unbounded loop or blocking read (game loop exits on `sim.done`/deadline; player loop exits 0 on socket close, `gridwars_player.nim:58-90`). Smoke episode completed `reason=complete` (log line 2625). |
| 6 num_agents | PASS | `4` in `standard` (manifest:396), `blitz` (:423), `certification.game_config` (:448); `docker_smoke.sh:112-157` enforces all four invariants **before** any `docker run` (:197+), each exiting non-zero with `SEAT-COUNT FAIL:`; `SMOKE_SEATS` independent cross-check (:152-157); grep of the head run's docker-smoke log: **0** occurrences of `SEAT-COUNT FAIL`, and `smoke OK: seats=4 … reason=complete`. |
| 7 Scripted baseline | PASS | `test_bot.nim:47-72` — four seats of each baseline, 4 seeds, to natural end: `reason == "complete"`, `ticksPlayed == 400`, zero faults/stalls/illegal/refused (every action inside legal bounds); tuned with a grid harness — `tools/tune_painter.nim` + the shipped run-22/two-cell/one-per-fuse `painter.gwl`, asserted to beat `sentry` with margin on assertion **and** held-out seeds (`test_bot.nim:74-100`). |
| 8 LLM reply handling | PASS | Tolerant parse: BOM/fence strip, first-`{`-to-last-`}` extraction, prose tolerated, array-or-string script (`llm.nim:335-401`); one retry with the exact parser/compiler message (`llm.nim:491-525`); then `sentry` fallback recorded — `origin="fallback"`, rejection into `submit.compileError` (`llm.nim:176-178`, `sim.nim:946-949`), counted in `results.fallbacks` (`sim.nim:1018-1023`) for phase 60. |
| 9 Rune-safe truncation | PASS | One shared `cutRunes` (`gwl.nim:120-128`) used by notes/banner/compile errors/transport errors/reply excerpts; `capScript` rune-cuts lines (`sim.nim:860-875`); tests feed multi-byte at every cap and assert valid UTF-8: `test_bot.nim:211-248`, `test_replay.nim:44-110` (strict parse + `validateUtf8 == -1` of the written replay, including the captured-error path). |
| 10 Manifest validates | PASS | `game.docs` = `readme` `{"type":"text","value":…}` + `pages` `[{id,title,content:{type:"text",value}}]` (manifest:283-305); `game.protocols` carries **both** `player` and `global`, each `{"type":"text","value":…}` (:273-282). |
| 11 Viewer legible at 360 px | PASS | `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` (`client/chrome.css:290-291`); `.plate-label` hidden under 640 px (`chrome.css:460-461`), plus the game block's 1000/720/560/420 px queries (`chrome.css:598-610`); asserted at `test_viewer.nim:63-75`. |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:153) → Certify (:167, in-run `coworld build` output, requires the static-bundle liveness marker) → Upload policies (:206) → Upload coworld (:304) → secret put (:342). All three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (:15); placeholder gate run verbatim at head: `grep -n '<slug>\|<IMAGE>\|<SEATS>' …` → no matches (exit 1) ⇒ gate exits 0. ci.yml's docker-smoke builds the production image from source inside its own job (:176-177) — no stale binary. |
| 13 Viewer executes | PASS | (i) run **32747821831** `wasm-viewer` green including `Load the bundle in a real browser` (`tools/ci/viewer_smoke.mjs`, pinned Playwright chromium, against the docker-smoke replay); `needs: docker-smoke` (`ci.yml:222`); no `continue-on-error` anywhere in the workflows (grepped); step output `{"loaded":true,"ms":292,"clock":"R1 / 2 · TICK 108 / 150",…}` + 10 s soak passed. (ii) `data-replay-loaded="true"` set after the first synchronous draw (`renderer.js:976-999`), `data-replay-error` set on every failure path incl. wasm rejection (`static_replay.js:56,96-99`), shell polls the loaded attribute before posting `ready` (`static_replay.js:127-140`). (iii) `config.nims:38-39` `-s MODULARIZE=1 -s EXPORT_NAME=GridWarsReplayModule` and the shell calls the factory `GridWarsReplayModule()` (`static_replay.js:154`) — one lineage, no `Module.onRuntimeInitialized`; and the smoke's `loaded:true` is the evidence, not file presence. |
| 14 Chrome is the starter's | PASS | `client/chrome.css` bytes 0..11963 **byte-identical** to the starter (verified with `cmp` against `/workspace/starters/cogame-bullwhip/client/chrome.css`), one appended `/* ---------- Grid Wars ---------- */` block, prefix pinned by length+FNV in `test_viewer.nim:44-52`. The broadcast page role is held by `replay-viewer/index.html` (the pod page was removed per item 3): diffed against the starter's `client/replay.html` — 2280 vs 2322 bytes, all 20 starter ids kept, only edits are title/wordmark/clock text, two appended elements (`#terrbar`, `#codepane`), and the ws bootstrap swapped for the static shell + `relayout()`; not a rewrite. Transport: (a) `relayout()` measures `#transport.offsetHeight` into `--band` and sets `--hudscale` on `document.documentElement`, calls `fit()`, wired to load/resize/feed-toggle (index.html:48-66); (b) nothing fixed-positioned in the band — `#endscreen` is `absolute; inset:0` inside `#board-wrap` (chrome.css:374-377), `#loading` rides `bottom: var(--band)` (chrome.css:572), `#transport` is in normal flex flow; (c) the endcard uses the class its rule uses (`#endscreen.show`, chrome.css:383 / `renderer.js:600`) and **every** seek — scrub drag, beat click, play-restart — routes through `setIndex`, which re-evaluates `updateEndscreen(…, index >= frames.length-1 …)` (`renderer.js:945-973`); (d) beats are labelled `<button type="button">` with `aria-label`/`title`/`onclick` seeking (`renderer.js:1014-1028`), six kinds emitted, a CSS rule for each incl. seat-coloured submit/roundend (chrome.css:575-597), asserted at `test_viewer.nim:77-95,202-220`. Zoom/minimap/`#viewpanel`: removed entirely — markup, CSS, wiring and tests (`test_viewer.nim:156-163`), per the note's recorded deviation (fixed 30×30 arena). Naming divergences from the pin's literal filenames (`chrome_common.js`→`chrome.css`, `replay_broadcast.html`→the replay page, `markBeat`→`markGridWarsBeat`) are all named and justified in the design note §Chrome provenance / §Transport rules. |
| Simultaneous batch | PASS | All open seats go out as **one** `curly.makeRequests` batch per attempt, max two attempts per round (`llm.nim:491-505`); never sequential; `batchesUsed` recorded and rate-floored (`server.nim:293-306`). |

## Non-blocking observations

- **Stale design-note §Server route table (doc only).** The repo's design note still lists
  `GET /client/replay` and `WS /replay (replay mode)` in the route block
  (`docs/plans/2026-08-24-grid-wars-design.md:784,786`) and still describes `client/replay.html`
  as a kept page (`:889,912,931,1152`), although the head code removed the pod path entirely (and
  the note's own §Out of scope `:1194` and §Bundle `:881` say a pod viewer is out). No checklist
  item requires note↔code agreement here — item 3 is about the code/manifest, which are clean —
  so this is advisory: the note's §Server and §Chrome provenance should be brought up to date with
  the head the way N1/N2/N3/N9 were.
- The `test_viewer.nim` sentence in the note's §Tests (`:1152`) likewise still names
  `client/replay.html`; the actual test now covers the one existing replay page plus a pod-path
  absence guard, which is stronger.
- The soak log line prints the (absent) `#tick` readouts as `null -> null -> null`; the pass was
  decided on `clock`/`scorebug` movement (`viewer_smoke.mjs:401-403`), so the check is real — the
  log line is just uninformative for this game.
- `client/global.html` / `client/player.html` (live pages) ship no `relayout()`, so live views run
  on the appended block's `--band: 84px` default. The design note only pins `relayout()` on the
  two replay pages; live pages have no endcard-over-transport risk (endscreen sits in
  `#board-wrap`). Advisory only.

## Could not verify (and why it does not count as blocking)

- Nothing on the checklist is unverifiable from the tree or cited CI evidence. The one item that
  cannot be *executed* in this sandbox (no docker, no emcc, no nim) — that the wasm build actually
  loads and plays — is verifiable and verified from cited CI evidence, which the checklist item 13
  explicitly designates as the admissible proof (run 32747821831, `wasm-viewer` green,
  `loaded:true`, soak passed).

BLOCKING: 0
