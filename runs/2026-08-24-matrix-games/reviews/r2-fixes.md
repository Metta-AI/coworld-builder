# r2 fixes — matrix-games

Repo: `Metta-AI/cogame-matrix-games`. Reviewed sha `af5c704`; **head after fixes
`a301f70483700ea7ca3031564bdfb381f4ca149a`**. 14 commits, one per finding (plus one
housekeeping commit that removes two scratch files I committed by mistake).

**CI: run [32761793533](https://github.com/Metta-AI/cogame-matrix-games/actions/runs/32761793533)
— `ci.yml`, event `push`, headSha `a301f70483700ea7ca3031564bdfb381f4ca149a`, conclusion
`success`.** Jobs `test`, `docker-smoke`, `wasm-viewer` all `success`; 214 `[OK]` lines across the
debug and `-d:release` passes; full-log grep: 0 × `SEAT-COUNT FAIL`, 0 × `RESULTS-SCHEMA FAIL`,
0 × `EPISODE-REASON FAIL`.

Every fix was compiled and every test file was run locally in both modes before each push (Nim
2.2.4 + the nimby package tree are present in the sandbox; docker and emsdk are not, so the
docker-smoke and wasm-viewer halves are proved only by CI). **No test was disabled, skipped,
loosened or deleted** — `git diff af5c704..a301f70 -- tests/` removes no `check`, no `skip`, no
tolerance; the only removed lines are the harness's own `finish("complete", …)` stamp (replaced by
the production settle), the inlined beat loop (replaced by the production one), an import line and
a comment header.

Pushes went through the GitHub Data API (git-over-HTTPS writes still fail auth; a plain
`git push` was tried first and returned "Password authentication is not supported").

## Disposition table

| finding | kind | disposition | commit | files | checklist item |
|---|---|---|---|---|---|
| F1–F4 | match | no action | — | — | — |
| **F5** | unclear | **fixed** | `5c8ba4c` | `src/matrix_games/sim_config.nim:66-127`, `server.nim:161-266`, `tests/test_manifest.nim:141-171` | 5 (timeout) |
| F6 | match | no action | — | — | — |
| **F7** | gap | **fixed** | `be6f66e` | `src/matrix_games/server.nim:292-302` | 5 (hang) |
| **F8** | gap | **fixed** | `3925fe0` | `src/matrix_games/server.nim:135-177, 244-250, 303-316` | 5 (hang) |
| F9 | match | no action | — | — | — |
| **F10** | unclear | **fixed** | `0095d95` | `src/matrix_games/server.nim:55-56, 350-366`, `tests/test_manifest.nim:62-74` | **3 (static-viewer)** |
| **F11** | gap | **fixed** | `86dfffb` | `client/replay_broadcast.html:1597-1601` | — |
| F12, F13 | match | no action | — | — | — |
| **F14** | unclear | **fixed** | `a301f70` | `client/replay_broadcast.html:1531-1537`, `tests/test_worst_case_text.nim:104-110` | 11 / **15** |
| F15 | match | no action | — | — | — |
| **F16** | gap | **fixed** | `0abf485` | `client/replay_broadcast.html:1480-1483` | — |
| F17 | match | no action | — | — | — |
| **F18** | gap | no change (reasoned) | — | `tools/ci/viewer_smoke.mjs:483` | 13 |
| **F19** | gap | **fixed** | `ad913b3` | `tools/ci/viewer_smoke.mjs` (template, verbatim), `.github/workflows/ci.yml:305-331` | **15** |
| F20 | match | no action | — | — | — |
| **F21** | gap | **fixed** | `b25609d` | `src/matrix_games/sim.nim:170-181`, `tests/support/helpers.nim:63-75` | 2 |
| F22 | match | no action | — | — | — |
| **F23** | gap | **fixed** | `d38a9cc` | `src/matrix_games/global.nim:140-173`, `tests/test_viewer.nim:207-240` | 2 |
| F24 | match | no action | — | — | — |
| **F25** | gap | no change (**out of my hands** — see below) | — | `design.md:623` | 7 |
| F26 | match | no action | — | — | — |
| **F27** | gap | **fixed** | `cd4ef58` | `tests/test_sim.nim:10-36, 296-320` | **1** / 7 |
| F28 | match | no action | — | — | — |
| **F29 (B1)** | gap | **fixed** | `2835f33` | `tools/ci/docker_smoke.sh:369-384`, `src/matrix_games/sim.nim:195-203`, `server.nim:303`, `tests/test_baseline.nim:53-79`, `tests/support/helpers.nim` | **7** |
| F30, F31 | match | no action | — | — | — |
| F32–F36 | unclear | no change (reasoned, unchanged from r1) | — | `kernel.nim:124-175`, `indices.nim:74`, `sim.nim:87-94`, `llm.nim:449-451`, cert fixture | — |
| **checklist 15(c)** | coordinator ruling | **fixed** | `4d82f28` | `tests/support/worst_case.nim`, `tools/gen_worst_case_replay.nim`, `tests/fixtures/worst_case_text.replay`, `tests/test_worst_case_text.nim`, `.github/workflows/ci.yml:332-372`, `client/replay_broadcast.html:1425-1454` | **15 (legibility)** |
| — | housekeeping | `832a162` removes two scratch probe files a `git add -A` swept into `4d82f28` | | | |

---

## F29 (B1) — nothing asserted `results.reason == "complete"` — `2835f33`

**What it did.** `tools/ci/docker_smoke.sh:369-371` read the reason and printed it. The F66
schema validator could not close the hole: `game.results_schema.properties.reason` is an enum of
`complete`/`deadline`/`forfeit`, so a `deadline` settle is schema-legal. No test asserted it
either — `tests/test_replay.nim:72` checks membership in `LegalReasons`, and the only "complete"
in the tree was a string the test harness stamped on the sim itself
(`helpers.nim:35`, `:74`).

**What it does now.** Both halves the brief asked for:

1. `docker_smoke.sh` asserts it. The all-scripted smoke episode must report
   `reason == "complete"`; anything else raises `EPISODE-REASON FAIL: …` and the job is red,
   prefixed like `SEAT-COUNT FAIL` and `RESULTS-SCHEMA FAIL`.
2. The **server's own settle** is now a named proc — `sim.settleComplete()`
   (`src/matrix_games/sim.nim:195-203`) — called by `server.runGame` where the beat loop falls out
   (`server.nim:303`) and by the test harness, so there is one stamp and a test can exercise it.
   `tests/test_baseline.nim:53-79` plays an all-scripted episode of **every** variant to its
   natural end, bounds-checks every order on the way in (`checkOrder`), asserts
   `not state.done` before the settle, then `reason == "complete"`, `ending == "full_match"`,
   `beats == config.beats` and `ticks == beats × ticksPerBeat`.

**Evidence.** I extracted the smoke's python block and ran it against a synthetic results object:
`complete` → rc 0 and `smoke OK: … reason=complete`; `deadline` → rc 1 with
`EPISODE-REASON FAIL: results.reason is 'deadline', expected 'complete'`; `forfeit` → same.
In CI at the head sha, `docker-smoke` → `episode end reason: complete` /
`smoke OK: seats=8 results=709B replay=118908B reason=complete`, with the gate live, and the
`test` job prints `[OK] an all-scripted episode reaches its natural end and reports complete`
in both modes.

## Checklist item 15 — the worst-case model-text fixture — `4d82f28` (with `ad913b3` for 15a/15b)

**(a) `viewer_smoke.mjs` is the current template, verbatim.** `ad913b3` replaces it with
`/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` byte for byte (`diff` is empty);
the repo copy had no `--strict-text-bounds`, no `fillText`/`strokeText` wrappers and no
`canvas_text` summary. No substitutions, as design.md:985 requires.

**(b) `--strict-text-bounds` is on.** `ci.yml`'s smoke step now carries it. The yard is a fixed
24 × 14 arena that always fits the frame, so `never_inside` is gated at 0. CI log, both viewer
steps: `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`.

**Stated plainly, because the number matters:** `total: 0` here is *correct*, not a miss.
`grep -rn 'fillText\|strokeText\|measureText' client/ replay-viewer/ src/` returns **nothing** —
this viewer draws no canvas text at all. The board canvas draws sprites, and every string a
spectator reads (scorebug plates, `#mg-matrix`, `#mg-indices`, the feed rows that carry the
model's `say`) is DOM text laid out by CSS. A second limit worth naming for the judge: the board
is rendered in a Worker on an **OffscreenCanvas** (`replay-viewer/static_replay_worker.js:2`), and
the template's hook only sees main-thread 2D contexts — so the flag guards the page's own
main-thread canvas draws, and the real bound on this game's model text is the CSS rule below plus
the fixture load.

**(c) The fixture.**

- `tests/support/worst_case.nim` builds a **real episode** (`prisoners-dilemma`, seed 10, a mixed
  baseline table) in which **every seat's every order event** carries a full-cap 64-rune `say` and
  a 400-rune `notes` — padded with an unbroken alphabetic run (no soft wrap can break it) and
  carrying multi-byte runes, so the cap is a rune cap. `source` is `llm`, so the feed renders them
  as model text rather than `[auto]` fallbacks. The seat mix is chosen because it produces **all
  four** beat-marker kinds: 21 `interact`, 1 `bigpay`, 4 `leadchange`, 1 `over`.
- `tools/gen_worst_case_replay.nim` writes it; `tests/fixtures/worst_case_text.replay` (141 486 B)
  is the committed result.
- `tests/test_worst_case_text.nim` reads the **committed bytes** and asserts the fixture is still
  worst-case: 48 order events (8 seats × 6 beats), `say.runeLen == MaxSayRunes` and
  `notes.runeLen == MaxNotesRunes` on every one, no ellipsis in either, `say.len > say.runeLen`
  (multi-byte), `results.reason == "complete"`, 300 ticks (longer than the 10 s soak), every seat
  in the first viewer packet still carrying a 64-rune `say`, all four marker kinds present, and
  that the file is what the generator produces. One quietly shortened remark fails it.
- `ci.yml` loads it **through the real bundle** in its own step, "Load the worst-case model-text
  fixture in the same bundle": `viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
  tests/fixtures/worst_case_text.replay --soak 10 --strict-text-bounds --out dist/worst-case-text
  --timeout 90`, and the JSON/PNG are uploaded with the other smoke evidence.
- **The DOM that renders `say` now bounds it.** The starter's `.feed-row` is a one-line kill
  notice (`white-space: nowrap`, `max-width: none`, sized to content); a 64-rune remark on top of
  `ASH: gather cooperate` grew leftward out of the 228-unit feed column. Per item 15's rule
  — remarks wrap, labels ellipsize — `#killfeed .feed-row` is now `max-width: 100%;
  white-space: normal; overflow-wrap: anywhere` and never ellipsizes, and
  `#bannerlane .banner-chip` (which carries only `BIG PAY — ASH 4.35` style labels, never model
  text) ellipsizes. `#killfeed` is bottom-anchored `column-reverse`, so a taller row grows upward
  into empty stage, never over the transport band.

**Evidence.** CI, the fixture step: `{"loaded":true,"ms":332,"clock":"BEAT 5 / 6 TICK 240 OF
300","scorebug":"worst-case-always-first 19.68 7 enc …","feed_lines":6}`,
`soak: 10s of playback kept advancing ("0 / 300" -> "192 / 300" -> "240 / 300")`,
`scrub readouts: 0%="BEAT 5 / 6 TICK 240 OF 300"  50%="… TICK 167 …"  100%="… TICK 299 …"`,
`canvas text: 0 drawn, 0 never inside the canvas … (--strict-text-bounds)`.

## F5 — `validate()` rejected schema-legal beats — `5c8ba4c`

**What it did.** `validate()` required the FULL worst case
(`connect + grace + beats × 2 × llmTimeoutSeconds`) to fit inside 60 % of
`episodeTimeoutSeconds`, so `beats` 14…24 — which `game.config_schema` publishes — exited 2 in
`src/matrix_games.nim:45-48` before the server started.

**What it does now.** The arithmetic moved, because the schema cannot: a cross-field budget is not
expressible in JSON Schema. `validate()` now enforces the **floor** — startup plus ONE beat's
attempt-and-retry (`startupBudgetSeconds() + beatBudgetSeconds()`, 223 s at the defaults) — and
the beat loop refuses to **open** a beat whose worst case would run past the deadline
(`server.nim:256`, `elapsed + beatBudget > deadline`), settling with the legal reason `deadline`.
So a long config truncates as designed instead of failing to start, and — this is the part that
keeps checklist item 5 true — the episode now settles *inside* the 60 % budget rather than up to
one beat (40 s) past it, which the old `elapsed > deadline` check allowed. A config with no room
for even one beat is still a hard error; there is nothing to degrade to.

**Evidence.** `tests/test_manifest.nim`: every `beats` from the schema's `minimum` to its
`maximum` validates, `playerConnectTimeoutSeconds` and `llmTimeoutSeconds` validate at their
published maxima, and a 300 s-episode config still raises. CI `[OK] every beats value the config
schema publishes starts the game`, `[OK] a config with no room for a single beat is still
refused`. The shipped path is unchanged: 12 beats at the defaults is 663 s of budget against a
720 s deadline, so no beat is ever refused and the smoke still reports `complete`.

**Residue, stated:** full schema ⊆ validate() agreement is impossible — `episodeTimeoutSeconds`
may be 60 while `playerConnectTimeoutSeconds` may be 600. The floor is the game's to keep and the
raise message now names the real arithmetic (it also no longer hardcodes the literal `+ 3`, which
was the F4 residue).

## F7 — the guard caught `CatchableError`, not Defects — `be6f66e`

`except CatchableError` → `except Exception` on the beat loop. In Nim 2.2.4 a `Defect` derives
from `Exception` and not from `CatchableError`, and the image builds `-d:release` without
`--panics:on` (Dockerfile:43, :46), so a defect on the beat thread was raised, uncaught, and took
the whole process down with no artifacts. I verified both halves locally: an `IndexDefect` under
`-d:release` is **not** caught by `except CatchableError`, **is** caught by `except Exception`
(exit 0, execution continues), and the same holds inside a `createThread` worker. The note's pin
is that a raise settles as `deadline`; it now covers every raise.

## F8 — `finishEpisode` sat outside the guard — `3925fe0`

Two changes. `finishEpisode` writes the replay and `results.json` **independently** — each in its
own `try`, logged on failure — so a non-2xx replay POST no longer takes down the artifact the
platform scores from. And the settle path (last observation + `finishEpisode`) runs inside the
same `Exception` guard as the beat loop, as does the `connectedCount == 0` forfeit settle, so a
raise anywhere in it still reaches the shutdown grace and `quit(0)` instead of killing the
process. `resultsJson`/`replayBytes` — the two the `f082554` commit message claimed were covered
and were not — are inside that guard.

## F10 — the broadcast page was still served under its asset name — `0095d95`

I did **not** take the reasoned-no-change route. The manifest declares no pod viewer
(`replay_viewer.bundle = static-replay-viewer`, no `url`, `tests/test_manifest.nim:62`), and
`client/replay_broadcast.html` is a **build input**: `Dockerfile.replay-viewer:42` splices it into
`replay-viewer/dist/index.html` and the platform serves the bundle from S3. Nothing on the pod
references it — `client/global.html` says so in as many words. Serving the same document at
`/client/replay_broadcast.html` was the route F59 removed, with a longer name (the page even
carries a `/client/` base-path branch for exactly that case).

The asset route's policy is now one testable proc, `servableClientAsset` (`server.nim:350-360`):
no traversal, no dotfiles, never `replay_broadcast.html`. `tests/test_manifest.nim` asserts both
directions — the page and a traversal are refused, `chrome_common.js`, `broadcast_core.js`,
`global.html` and `player.html` are still served.

## F11, F16 — stale comments — `86dfffb`, `0abf485`

Comment-only. The script-loading fallback no longer explains itself in terms of the deleted
`/client/replay` route (it now names the case that exists: an unspliced copy of the page), and the
360 px stylesheet header names 640, the threshold `mgRelayout` actually uses, instead of the
starter's 620.

## F14 — the feed's legibility was unverified — `a301f70`

Two of the three parts are now real. `viewer_smoke.mjs` selects the feed as `#feed, .feed, #log`
and this page's feed is `#killfeed`, so `feed_lines: 0` in every previous run was a **selector
miss**, not an empty feed. `<div id="killfeed" class="feed">` fixes that with no styling effect
(every rule is `.feed-row`; there is no `.feed` rule). CI at the head sha now reports
`"feed_lines":6` in both viewer steps — the first CI evidence that the feed draws rows at all.
The row is also now bounded and wrapping (see item 15(c)), and the worst-case fixture drives it
with eight full-cap remarks.

**Not closed:** the harness's viewport is fixed at 1280 × 800 in the template
(`viewer_smoke.mjs:460`) and takes no width flag, so **no gate measures the feed at 360 px**. What
would settle it: a template that accepts a viewport size, or a screenshot diff at 360 px. I did
not fork the template to add one — see F18.

## F18 — the three scrub readouts are printed, never gated — no change (reasoned)

Real, and I am deliberately not fixing it here. The exit condition
(`!loaded || playFailure || boundsFailure`) is the **template's**, and design.md:985 plus
checklist item 15 both require this file to be the coworld-builder template copied with no
substitutions — which `ad913b3` has just made true again after F19. Gating the readouts means
editing the template, which is coworld-builder's file and not this repo's to fork. The property
holds empirically in the run cited above (`0%="… TICK 240 …" 50%="… TICK 167 …"
100%="… TICK 299 …"`), and the `--soak 10` gate (`playFailure`) already fails a viewer whose clock
stops advancing, which is the failure the readouts were watching for. **What would settle it:** a
template change in coworld-builder that compares the three readouts.

## F21 — the recording harness duplicated the beat loop — `b25609d`

`runBeat` now takes an optional per-tick hook (`onTick`, nil at every production call site) and
`runScriptedRecording` passes one instead of inlining `ticksPerBeat × stepOnce` + `closeBeat` and
dropping the `if sim.done: return` guard. There is one beat loop in the tree, and the F47 per-tick
comparison now runs against the loop the server runs.

## F23 — the two timelines disagreed about the `over` row — `d38a9cc`

The reviewer's second half was a real divergence, so I fixed the code and not just the test.
`initViewer` built the terminal `over` row from the **last `leadchange` seat** with `cp: 0`;
`broadcast.buildBeats` builds it from `sim.leader()` with that seat's real score. An episode with
no lead change put the marker on seat 0, and even a correct one showed 0 cp in the label. The
viewer now reads the final frame's `sc` array with the same argmax-lowest rule. A new test,
`[OK] the live timeline and the replay timeline are the same rows`, compares the two arrays row by
row for two variants and checks the `over` row's `seat` and `cp` against `sim.leader()`. The
indices cross-check also gained the non-emptiness guard (`state.idx.interactions > 0`,
`total > 0`) so a future constant change that empties the room cannot leave it passing on
all-zero histograms.

## F25 — the note's chicken claim is false in this build — no change (**not mine to make**)

Confirmed, and I cannot fix it: the fixer brief forbids editing `design.md`, which is where the
false statement lives (design.md:623, "In `chicken`, one `always-second` in a room of
`always-first` tops the table" — it tops the table on 0 of 8 seeds). The code and the test are
right; `tests/test_indices.nim:23-31` documents the positional reason and `e47b6c8` asserts the
property that *is* true (the hawk out-earns the dove in every mixed cell). **Action for the
coordinator:** design.md:623 needs the same substitution the test made. The repo's own copy at
`docs/plans/2026-08-24-matrix-games-design.md:623` carries the same sentence and I left it alone
so the two copies stay identical.

## F27 — the child mode was an env-gated skip of the whole sim suite — `cd4ef58`

Child mode now needs a **second** variable carrying a token the file owns
(`MATRIX_GAMES_HASH_CHILD = "test_sim determinism child"`), and either variable present without it
`quit`s **2** with a message. An inherited `MATRIX_GAMES_HASH_SEED` used to make the file print one
hash, exit 0 and run none of its assertions with the job green; it is now a red job. The
determinism suite asserts all three refusal cases (seed alone, wrong token, token without a seed)
by spawning the binary with each environment. CI: `[OK] a stray child-mode variable fails loudly
instead of skipping the file`, both modes.

## F32–F36 — no change (reasoned)

Unchanged from `af5c704` and unchanged from r1's dispositions, which I re-read and still agree
with: each is a design-note ambiguity, not a defect. `kernel.nim`'s `gather`/`deny` reading the
full spawner list is the game's executor rather than a policy and is identical for every seat
(F32); `indices.nim:74`'s majority rule for a mixed-side seat is a choice the note does not
constrain (F33); a blocked cog turning before the move test is deterministic either way (F34); the
429 retry inside the beat satisfies the note's first reading and reopens the seat next beat as
well (F35); the cert fixture naming seats with the aliases is pinned by the note (F36).

---

## NOTED (not fixed)

- **`tests/test_baseline.nim`'s "no baseline takes longer than 1 ms per beat" is flaky in this
  sandbox** — it fails roughly 2 runs in 10 at 1.00–1.04 ms against its 1.0 ms bound. I checked
  it at the **base** sha `af5c704` in a separate worktree and it flakes there too (2/10), so this
  is sandbox CPU noise and not a regression from these commits. It passed in both modes in CI at
  the head sha. I did not touch the bound — loosening it would be exactly the thing the fixer
  brief forbids. If it ever flakes on a runner, the right fix is a per-order budget measured in
  iterations, not a bigger number.
- **`viewer_smoke.mjs` cannot measure at 360 px** (F14) and **cannot gate the scrub readouts**
  (F18). Both are template concerns; a repo-local fork would break "copied with no
  substitutions".
- **`canvas_text` can only ever see main-thread draws**, and this bundle renders the board in a
  Worker on an OffscreenCanvas. Today the number is honestly 0 of 0 because nothing draws canvas
  text anywhere; a future in-worker caption would need instrumentation the template does not have.
- **The design note's route table** (design.md:644) still says `/client/global` serves
  `client/replay_broadcast.html`; the pod serves `client/global.html`, a docs page that points at
  the S3 bundle. That is the shipped and correct behaviour after F59 and F10 — the note is what is
  stale.
