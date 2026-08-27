# r1 fixes — pommerman

Repo: `Metta-AI/cogame-pommerman`, branch `main`
Head: `9fa80f8db7288a9031962e446019b3fe430e1691`
CI: https://github.com/Metta-AI/cogame-pommerman/actions/runs/33108749059 — **success**
(all four jobs green: `test`, `manifest`, `docker-smoke`, `wasm-viewer`; run event `push`,
`headSha` == the head above, which is `refs/heads/main` at the time of writing).

Every commit was pushed through the Git Data API (blobs → tree → commit → fast-forward ref
update), preserving `100755` on `tools/ci/docker_smoke.sh`. No force-push, no history rewrite.
Nim 2.2.4 + `nimby.lock` were installed in the sandbox, so every test below was also run locally
in **both** debug and `-d:release` before pushing; the final sweep over all 15 `tests/*.nim` in
both modes is clean.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 say/view dropped from every directive record | fixed | `34e3bfa` | `src/pommerman/sim_types.nim:32`, `src/pommerman/directives.nim:314-339`, `tests/test_pom_control.nim`, `tests/test_pom_replay.nim` |
| F2 `canvas_text: total 0` — fixture measures DOM, not canvas | fixed | `deca701` | `tools/ci/renderer_fixture.html`, `.github/workflows/ci.yml:450`, `tests/test_pom_viewer.nim` |
| F3 `kick` with nothing to kick behaves as `stay`, not `hide` | **refuted** (test added) | `2c5fb05` | `tests/test_pom_control.nim` |
| F4 `turnSpacingMs` sleep inside the `turnBudgetMs` window | fixed | `02b45f4` | `src/pommerman/decide.nim:205,257-271` |
| F5 no errata section in the committed note | fixed | `76d1078` + `9fa80f8` | `docs/plans/2026-08-27-pommerman-design.md` |
| F6 `--preload-file data@data` dropped | advisory, recorded | (errata 11) | — |
| F7 five listed files absent | advisory, recorded | (errata 14) | — |
| F8 state JSON shape differs from the note's illustration | advisory, recorded | (errata 12) | — |
| F9 `.tiny` at 640, not 620 | advisory, recorded | (errata 10) | — |
| F10 tick-budget test asserts < 4000 ms | fixed | `66350e6` | `tests/test_pom_sim.nim:583-600` |
| F11 live `/global` feed never gets directive events | fixed | `98cd1e3` | `src/pommerman/episode.nim`, `src/pommerman/server.nim:462`, `tests/test_pom_engine.nim` |
| F12 `camper` reads `params.dodgeHorizon` | fixed | `04e1026` | `src/pommerman/baselines.nim:208-216` |
| F13 `docker_smoke.sh` does not fail on `fault` | fixed | `05f987d` | `tools/ci/docker_smoke.sh:306-318` |
| F14 a seat that never joins yields `fallbackTurns == 0` | **refuted** (behaviour pinned) | `66350e6` | `tests/test_pom_engine.nim:93-108` |
| F15 only two capped fields filled with emoji | fixed | `a6b722c` | `tests/test_pom_replay.nim` |
| F16 `game.docs` uses `"type":"uri"` | **refuted** | — | `coworld_manifest_template.json:38-60` |
| F17 the game server still serves `/client/replay` | **refuted** (assertion added) | `5761285` | `tests/test_pom_manifest.nim:91-97` |
| F18 `showPlayerLabels` carried everywhere, read nowhere | advisory, documented | `2b28c5c` | `src/pommerman/sim_types.nim:128-137` |
| F19 replay ~34 KB, hashes per frame | advisory, recorded | (errata 6) | — |

Note on commit discipline: F10 and F14 share one commit (`66350e6`) — both are test-only and the
message names both findings; F5 took two commits (`76d1078` writes the errata, `9fa80f8` adds the
three remaining declared deltas the brief asked for). Everything else is one commit per finding.

---

## F1 — every `say` stripped, and the view always dropped — fixed, `34e3bfa`

**What the code did.** `MaxDirectiveRunes = 900`, and `boundedDirectiveRecord` shrank `say` by 16
runes at a time until empty and only then dropped the view. Measured against the repo's own
modules: a seat view is **1005 runes** at tick 0 and **3224 runes** with the bomb pool full, so no
`say` length could ever make the record fit. Every directive record on every turn came out with
`"say": ""` and `"view": null` — no `say` event could reach `#killfeed`
(`broadcast.nim:101-103` gates on `say.len > 0`), `tools/replay_summary.py`'s `directives[].say`
was always `""`, and the replay explained no decision.

**What it does now.** The cap is sized from the worst case the rules can produce — 4000 runes,
against a measured worst case of **3493** (full-pool view + the record's own fields + a full-cap
100-rune `say`) — and the trim order is inverted: if a record ever does overrun, the **view** is
shed first, because it is re-derivable from the replay's order records while the `say` exists
nowhere else. `say` is still capped at `MaxSayRunes = 100`; `notes` still never reaches the
replay.

**Wire/replay compatibility, and why no `GameVersion` bump.** The `view` key was already in
`directiveRecord`'s schema (it was emitted as `null`), the binary record kinds and their field
order in `replays.nim` are untouched, chat records are length-prefixed `u32` strings, and nothing
in the record feeds `gameHash`. `tools/ci/check_gameversion.sh` gates on a changed *rule
headline*, and no rule changed; bumping GV1→GV2 would additionally invalidate the committed
`tests/replays/pommerman.replay` that the "every committed fixture carries the current
GameVersion" test checks. So GameVersion stays `"1"`.

**Consequence to be aware of:** a recorded episode grows from 32 881 B to 189 260 B (CI:
`smoke OK: seats=4 results=756B replay=189260B reason=complete`), because all 144 directive
records now carry their observation. Recorded in the errata (item 6) against the note's ~20 KB
estimate.

**Evidence.** Local probe before/after (1005-rune view; `say in bounded: 0 runes` → `100 runes`,
`view kind: JNull` → `JObject`). New test `fullCapSaySurvivesWithARealView`
(`tests/test_pom_control.nim`): a 100-emoji `say` plus a real `engine.seatView(...)` comes back at
exactly `MaxSayRunes` with `view.kind == JObject` and `view.you == "RED-1"`, and again with the
bomb pool full. `tests/test_pom_replay.nim`'s summary fixture no longer passes `newJNull()` for
the view — it writes `radioInJson` + a real `seatView` per seat, exactly as `episode.nim` does —
and asserts every `directives[].say` in the Python summary is exactly 100 runes and valid UTF-8.
Satisfies checklist item 9 (rune-safe truncation, now on the path that actually runs) and repairs
the premise of item 15 (there is LLM text in the replay to draw).

## F2 — `canvas_text: total 0` — fixed, `deca701`

**What the code did.** `replay-viewer/static_replay.js:91-95` transfers `#board` with
`transferControlToOffscreen()` and all board drawing happens in `static_replay_worker.js`, so
`viewer_smoke.mjs`'s main-thread `CanvasRenderingContext2D.prototype` patch measured nothing:
both steps printed `canvas text: 0 drawn`. The fixture's assertions were all DOM ones — real, but
the number `--strict-text-bounds` gates was vacuous, which item 15 calls "not evidence of
anything".

**What it does now.** `tools/ci/renderer_fixture.html` keeps every DOM assertion it had (full-cap
100-rune `say` on all four seats, driven through the shipped page's own
`PommermanChrome.frame`, at 360/640/1280 px, with the fixture's own strings asserted to still be
exactly 100 runes and emoji-terminated) and adds a canvas half:

- it loads the bundle's own `./wire_constants.js` and `./broadcast_core.js` — the same file the
  Worker imports — and runs `BroadcastCore` on a canvas the fixture document owns, so the draws
  happen where a main-thread measurer can see them. Nothing is re-implemented: `ingest()` →
  `draw()` is the Worker's own path;
- the frame is built to hurt: bombers on the **top and bottom rows** (where the radio badge has no
  room above the chip and `drawRadioGlyphs` must flip it below), bombs in all four corners plus
  the whole fuse ladder, and a **distinct radio pair per (width, seat)** — without that, one badge
  landing inside at 1280 px masks the same string landing off-frame at 360 px in the per-string
  `never_inside` tally;
- it installs its own `fillText`/`strokeText` measurer (on top of the harness's, which it calls
  through) and **fails itself** via `data-replay-error` if it ever measures zero text draws, no
  fuse numeral, no radio badge, a draw that crossed the board edge, or a string that never landed
  inside;
- it publishes the merged main-frame + iframe report as top-level `window.__coworldTextBounds`, so
  `viewer_smoke.mjs --strict-text-bounds` gates a real number.

**Evidence.** CI run 33108749059, job `wasm-viewer`, step *Worst-case renderer fixture (full-cap
seat lines)*:
`canvas text: 110 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
Non-vacuity was proven by breaking the renderer on purpose: with `drawRadioGlyphs`' "flip the
badge below the chip" guard deleted, the same run reports `20 draws crossed the edge`, six strings
`never inside`, the fixture sets `data-replay-error` and `viewer_smoke.mjs` exits 1
(reproduced locally under the pinned Playwright 1.55.0 + chromium).

**The other step legitimately stays at `total: 0`.** `Load the bundle in a real browser` runs
against the docker-smoke replay in the shipped page, whose board is an OffscreenCanvas in a
Worker; there is no way to make that number non-zero without moving the board's drawing back onto
the main thread, which would be a worse viewer. That is stated in the errata (item 8) and in the
`ci.yml` step comment. The fixture is where the gate bites.

A new test (`tests/test_pom_viewer.nim`, "the renderer fixture measures REAL canvas text, not just
DOM") pins the fixture's script tags, its `BroadcastCore.create`/`ingest` drive, its own measurer,
both of its self-gates and the three widths, so the canvas half cannot be quietly removed again.

**On the note's §Tests item 40.** It describes the measurer as living on the *iframe's*
`CanvasRenderingContext2D` and says the fixture "re-points the iframe's `window.parent`". The
measurer now sits where the draws are (the fixture's own frame) and the merged report is published
at top level as the note requires. `window.parent` needs no shim: the shipped page posts
`{src: 'pommerman-replay'}` and only under `?embed=1`, while `viewer_smoke.mjs`'s bridge relays
only `src: 'coworld-replay'`, so the iframe cannot end the harness early. Recorded in errata 8.

## F3 — `kick` with nothing to kick — **refuted**, `2c5fb05` (test only)

`hide` and `stay` are the same action in every state `targetCell` can be reached from, so
`of okKick: result = (me.x, me.y, 0)` **is** `hide`:

- `chooseAction` returns the escape step before Step C whenever
  `danger.firstDangerAt(me.x, me.y) >= 0` (`control.nim:455-457`), so `targetCell` only ever runs
  from a cell that is *not* dangerous within the horizon;
- `hideTarget` (`control.nim:308-365`) scores the bomber's own cell at `high(int) div 4` in that
  case, which is the same value every other never-dangerous cell gets, and breaks ties by **fewest
  steps** — which the own cell wins at zero. No reachable cell can beat it.

**Measured:** over 200 randomised states (varied ammo, kick flags, bombs, ticks, both variants),
**1469 of 1469** degraded kicks — every `(seat, dir)` where the kick cannot fire — chose exactly
what `hide` chose, and `hide` was `stay` in all 1469. The reviewer's "hide would walk to the safest
reachable cell" does not hold from a safe cell. No code change; the equivalence the note's Step C
table asserts is now a test, which also closes the "no test covers the degraded kick path" gap.

## F4 — the spacing sleep inside the turn budget — fixed, `02b45f4`

`turnStart` was taken at the top of `decide.turn`, so the `turnSpacingMs` wait was spent inside the
same `turnBudgetMs` window the two attempts share: 10 s spacing + 8 s attempt 1 = 18 s ≥ 12 s, so
`getMonoTime() - turnStart >= budget` fired and the promised single retry was skipped on exactly
the turns that had waited. `turnStart` now starts when the batch does.

Bounds unchanged and re-checked: the wait is still clamped to ≤ 60 000 ms (`sim_config.nim:66`),
it only runs when the previous batch started less than `turnSpacingMs` ago — so a turn cannot both
wait the full spacing and burn the full budget, and the period between batch starts stays
`max(turnSpacingMs, turnBudgetMs)` plus loop overhead — the budget guard still latches at
`elapsed + 2*turnSeconds > wallClockBudgetSeconds`, and the 640 s engine stop is untouched
(checklist item 5). The remaining deviation from the note — ticks do **not** advance during the
wait — is a mechanism difference that would need an async turn to remove; it is recorded in the
errata (item 4) rather than redesigned. No test: exercising the retry path needs a live provider,
which is why the reviewer's own F4 was `[inferred]`; `tests/test_pom_engine.nim`'s budget-guard and
wall-clock-stop tests still pass unchanged.

## F5 — errata — fixed, `76d1078` + `9fa80f8`

`docs/plans/2026-08-27-pommerman-design.md` now ends with an **Errata — what shipped, where it
differs from the note above** section, 22 numbered entries, each with what the note claims, what
the code does and why. It covers everything three code comments and
`tools/ci/baseline_tuning.json` were pointing at, plus every delta this round: 56 rigid / 36 wood /
29 passage; the swept `(3, 4, 8, 2)` and `dodgeHorizon = 8` everywhere; camper's horizon (F12); the
spacing wait and the per-turn deadline (F4); `MaxDirectiveRunes = 4000` with the view shed before
the say and no GV bump (F1); the ~190 KB replay and per-frame hashes (F19); the disconnected seat's
counters (F14); the OffscreenCanvas / `total: 0` explanation and what the fixture measures instead
(F2); no canvas speech bubble; `.tiny` at 640 (F9); the dropped `--preload-file` (F6); the state
envelope (F8); the page-builder provenance; the five files not carried over (F7);
`showPlayerLabels` (F18); the docker-smoke fault gate (F13); the tick budget in both build modes
(F10); the live feed's records (F11); `PlaybackSpeeds [1,2,4,8]`; the art filenames with the
starter's cogs as fallback; and the fuse that does not tick on its placing tick.

The copy at `/workspace/coworld-builder/runs/2026-08-27-pommerman/design.md` was updated to be
byte-identical (`diff -q` clean). It is **not** committed — the coworld-builder repo is left to the
coordinator.

## F6 — `--preload-file data@data` — advisory, not fixed

Adding it back would emit a `pommerman_replay.data` payload that nothing reads:
`replay-viewer/pommerman_replay.nim` imports only the sim modules (no pixie, no `readFile`), and
`Dockerfile.replay-viewer` asserts the bundle ships `pommerman_replay.{wasm,js}` and **no** `.data`
while copying the art as plain files the page fetches. `-s FILESYSTEM=1` is kept. Errata 11.

## F7 — five listed files absent — advisory, not fixed

`tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `flake.nix`,
`client/league_replayer.html`. Nothing in `.github/`, `tools/`, `tests/` or `docs/` references
them, and `tools/replay_summary.py` (stdlib-only, no Nim, no Docker) covers the forensics they were
listed for. Adding four unused files to satisfy a list would be worse than recording the fact.
Errata 14.

## F8 — the state JSON shape — advisory, not fixed

The note prints a flat illustrative object; the shipped envelope is the starter's, with every
pommerman field under `pm`, which is exactly what lets `chrome_common.js` drive the clock,
transport, scrubber and momentum graph unchanged. The viewer reads the shipped shape and
`tests/test_pom_engine.nim:228-249` pins it. Errata 12.

## F9 — `.tiny` at 640 — advisory, not fixed

Checklist item 11 asks for "labels hidden under `640px`", so 640 is the correct boundary; the
starter's 620 would leave the 620-639 px band unlabelled but not `.tiny`. `page_script.js:601-605`
already carries the reason as a comment; asserted at `tests/test_pom_viewer.nim:223`. Errata 10.

## F10 — the tick budget — fixed, `66350e6`

`check elapsed < 4000` became `when defined(release): check elapsed < 1000 else: check elapsed <
4000`, which is the note's "< 1 s in a release build" where it applies while keeping a debug bound
(ci.yml runs every test in both modes). Measured on this machine: **1-3 ms** release, **~20 ms**
debug — both bounds keep two to three orders of magnitude of headroom, so neither is a tolerance
anyone can lean on. This is a tightening, not a loosening.

## F11 — the live feed — fixed, `98cd1e3`

`server.nim` declared `var frameChats: seq[ChatRecord]` and filled it only in the replay branch, so
live `stepEvents` saw nothing and emitted no `turn`, `order`, `radio`, `say` or `fallback` event;
`EpisodeFrame.records`, the field that exists for this, was never filled either.
`runTurnIfDue` now records every chat record it writes, `runEpisodeFrame` returns them, and the
live branch passes them — the same records the replay reader hands `stepEvents` during playback,
so both delivery modes build the feed from one vocabulary. Recorded bytes and the replay path are
untouched. New test: a live episode's frames each carry one `directive` record per seat and
`stepEvents` turns them into `turn`/`order`/`radio` feed events.

## F12 — `camper`'s dodge horizon — fixed, `04e1026`

`sim.dangerNow(params.dodgeHorizon)` → `sim.dangerNow()` (the config horizon the observation, the
controller and the viewer already share), so a hosted `game_config` that moved `dodgeHorizon`
cannot leave camper judging its exits over a different number of ticks than the controller that
executes the order. The sweep is unaffected — `tools/tune_baselines.nim:48` assigns
`config.dodgeHorizon` from the candidate params before every episode — and
`tune_baselines --check` still ranks the shipped pick **0 of 54**.

## F13 — `docker_smoke.sh` and `fault` — fixed, `05f987d`

A `fault` is a host error that still writes every artifact, so all the script's other checks passed
and the job went green on a broken build. It now exits non-zero naming `stopDetail`. This is the
only edit to the coworld-builder template beyond its three substitutions; ci.yml's adjacent
`reason in ('complete','deadline')` assertion stays as the second gate. Exercised both ways against
the extracted python block: `reason=fault` → `SystemExit: episode ended with reason=fault: boom`;
`reason=complete` → `smoke OK`. Mode `100755` preserved through the API push (CI's
`test -x tools/ci/docker_smoke.sh` is green).

## F14 — `fallbackTurns == 0` for a seat that never joins — **refuted**, behaviour pinned in `66350e6`

`fallbackTurns` counts a **policy that failed to answer**. A seat that never joined never had one:
it plays the scripted baseline from the first tick, so its directives are `scripted`. Counting them
would make an absent seat indistinguishable, in `results.fallbackTurns` — the number phase 60
reads — from an LLM that timed out on all 36 turns. The absence is carried by `deadSeats[3]`, the
closed failure payload, and one `disconnected` record per turn played; the test now asserts all of
those **and** `fallbackTurns[3] == 0` / `llmTurns[3] == 0`, so the split is pinned rather than
incidental.

## F15 — "every capped field" — fixed, `a6b722c`

The strict-UTF-8 fixture now registers each seat under a 200-emoji policy label
(→ `MaxPolicyLabelRunes`), writes a 500-emoji `fallback.detail` (→ `MaxFallbackDetailRunes`) and
settles the episode with a 500-emoji stop detail (→ `MaxStopDetailRunes`), on top of the existing
emoji `say` and `notes`. It asserts, out of the Python view of the bytes, that every
registration's `policy` is exactly `MaxPolicyLabelRunes` runes and valid UTF-8, that
`results.stopDetail` is exactly `MaxStopDetailRunes`, and that the fallback records decoded at all
(`replay_summary.py`'s reader decodes every record with strict UTF-8, so a byte-truncated detail
raises there). Checklist item 9.

## F16 — `game.docs` `"type":"uri"` — **refuted**

Two shipped starters in the sandbox declare their docs the same way —
`/workspace/starters/cogame-factorio` and `/workspace/starters/cogame-moba` both use
`{"readme":{"type":"uri","value":"https://github.com/.../README.md"}, "pages":[{…"content":
{"type":"uri",…}}]}` — so `uri` is a shape the platform accepts; `text` and `uri` are two values of
the same `{type, value}` object the checklist item is really about. What item 10 states as the
requirement is present: `readme` and `pages` are objects with `{type, value}`, every page has
`id`/`title`/`content` and its target file exists (`docs/RULES.md`, `docs/RADIO.md`), and
`game.protocols` carries **both** `player` and `global` as `{type, value}`
(`coworld_manifest_template.json:28-60`, asserted in `tests/test_pom_manifest.nim:99-125`). The
design note pins `uri` deliberately (lines 1401-1403), and `ci.yml`'s `manifest` job runs the
installed `coworld==0.1.43` loader over the substituted manifest — green in run 33108749059.
Changing to inline `text` would inline two documents that then drift from the repo copies. Not
changed.

## F17 — the server still serves `/client/replay` — **refuted**, assertion added in `5761285`

The route exists (`server.nim:237-242`) and is inherited: the starter this repo forks serves it
(`/workspace/starters/coworld-ctf/src/ctf/server.nim`), as do babel, bullwhip and parley. What
checklist item 3 is about is what the **platform** is pointed at, and nothing points it there:
`game.replay_viewer.bundle == "static-replay-viewer"`, there is no top-level `replay_viewer`, the
`coworld build` hook `tools/build_replay_viewer.sh` exists and is `100755`, the viewer contacts
nothing but the replay URL it is given, and `coworld-release.yml:206-213` hard-fails the release
if certification does not report the static bundle ("`/client/replay` viewer is not acceptable").
That was asserted for the two manifest keys but not for the manifest as a whole, so
`tests/test_pom_manifest.nim` now also asserts the string `"/client/replay"` appears **nowhere** in
the declared manifest. Removing the developer route would diverge from the starter and lose the
local page the design note sanctions, for no change to anything the platform sees.

## F18 — `showPlayerLabels` — advisory, documented in `2b28c5c`

Correct that nothing branches on it. Deleting it would make a hosted `game_config` that carries it
fail validation; wiring it up would put a real policy name on the board, which the two-name-spaces
rule forbids. So it is accepted, pinned `false` by `tests/test_pom_labels.nim`, and inert by design
— it can only fail closed. The type now says exactly that at the field instead of leaving the next
reader to grep. Errata 15.

## F19 — replay size and per-frame hashes — advisory, recorded

Now larger, not smaller: 189 260 B in CI, because F1 puts the observation back in all 144 directive
records, on top of the hash written on every frame (lobby and the 90-frame game-over hold
included). Harmless — the chain is still strictly increasing in frame, playback re-derives it frame
for frame (`hashMismatchTick == -1` in every replay test), and 190 KB is a static S3 object the
viewer already streams. The note's ~20 KB estimate is corrected in errata 6.

---

## NOTED (not fixed)

- `tools/ci/viewer_smoke.mjs` reads `window.__coworldTextBounds` in the **top frame only**, so any
  fixture that draws in an iframe or a Worker must merge its own report up (this repo's fixture now
  does). Worth carrying back into the coworld-builder template as a comment; the harness file
  itself is left byte-identical to the template.
- `EpisodeFrame.records` existed unused before F11; `EpisodeState.turnRecords` is still only read
  inside `episode.nim`. Left as is.
- The `wasm-viewer` job copies the fixture into the bundle at run time (`cp
  tools/ci/renderer_fixture.html dist/static-replay-viewer/`). The fixture's `<script src>`s
  therefore depend on `wire_constants.js` and `broadcast_core.js` sitting at the bundle root, which
  `Dockerfile.replay-viewer` already asserts. If the bundle layout ever changes, the fixture fails
  loudly (`broadcast_core.js did not publish window.BroadcastCore`) rather than silently measuring
  nothing.
