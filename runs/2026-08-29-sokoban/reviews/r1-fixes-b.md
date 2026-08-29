# r1 fixes (B) — sokoban

Second review: `runs/2026-08-29-sokoban/reviews/r1-review-b.md` (22 findings, B-F1…B-F22, its own
numbering). Evaluated against **current `main`**, which already carried the r1 fix series produced
against `r1-review.md`.

Repo: `Metta-AI/cogame-sokoban`, branch `main`.
Head: **`a72dbac2f84fce4c58ec9402ac299c3d42abc700`**
CI: **https://github.com/Metta-AI/cogame-sokoban/actions/runs/33247581241** — conclusion **success**
(run id `33247581241`, event `push`, branch `main`, headSha `a72dbac2…`; jobs `test` ✅,
`docker-smoke` ✅ including the new `Assert the smoke episode did not fault`, `wasm-viewer` ✅
including the new `Run the emitted wasm module headlessly`, `Load the bundle in a real browser` and
`Drive the shipped chrome with a worst-case frame`).

Twelve findings fixed here (one commit each), six were already fixed by the r1 series, four are
refuted with evidence.

| # | disposition | commit | what changed | checklist item |
|---|---|---|---|---|
| B-F1 `last_turn.dropped` hard-coded 0 | already fixed | `1dd3edb` (r1 F1) | `endTurn` reports `sim.turnDropped`; `directiveRecord` reads the same field | 8 (reply handling) |
| B-F2 `fallback` event's constant cause | **fixed** | `c50a0ae` | one `noteChatRecord` sink on both paths carries the turn's real cause onto the event and the feed line | 2 (live ≡ replay), watchability |
| B-F3 `throttled` outside the cause set | already fixed | `cfe9d10` (r1 F5) | a 429 records `transport_error`; a test scans every cause literal | 8 |
| B-F4 `turnBudgetMs` gates attempt starts | **fixed** | `01adc41` | the deadline is taken after the rate floor and named for the decision; the budget guard reserves `turnSpacingMs + turnBudgetMs` per turn | **5 (degrade-never-hang)** |
| B-F5 server does not refuse to start | refuted | — | the note contradicts itself; the code takes the half that keeps the episode scoreable | 5 (would be violated by the other reading) |
| B-F6 `.tiny` inset has no `var(--band)` | **fixed** | `f356da2` | `#fpv`, `#stage.tiny #fpv` and `#killfeed` ride the band; the fixture measures all four overlays against `#transport` | **14(b) (transport band)** |
| B-F7 `.tiny` inset collides with the pips | **fixed** | `3adc9d3` | inset at `band+22u` (top `band+106u`) under pips at `band+112u`; the left-column placement is documented | none — note only |
| B-F8 full-cap `say` in a nowrap row | already fixed + **fixed** | `c9f9d4d` (r1 F9) + `78c5553` | the say row's reserved band was r1's; the unstyled `bad`/`good` rows are now styled | **15 (drawn strings fit)** |
| B-F9 both text-bounds gates measured 0 | already fixed | `c9f9d4d` + `f31307a` (r1 F9) | the fixture mirrors the page's own text into a main-thread canvas: `canvas text: 25 drawn, 0 never inside` | **15** |
| B-F10 smoke never fails on `fault` | **fixed** | `2c7aec6` | a `ci.yml` step compares `results.reason`/`endRule`, leaving the shared script template-identical | 1 (CI means something) |
| B-F11 two harnesses wired to nothing | **fixed** (wasm) / refuted (page) | `8885041` | `wasm_replay_smoke.cjs` runs the emitted module in CI; `page_smoke.mjs` is a documented local gate | 13 (viewer executes) |
| B-F12 tuning sweep not re-run in CI | refuted | — | the harness exists, its pick is recorded and asserted; re-running the sweep is runtime cost, not coverage | 7 — satisfied |
| B-F13 tests drive a re-implemented loop | **fixed** (parity) | `e44b769` | the harness now matches the server's stop-record and end-rule rules; the artifact path stays docker-smoke's | 2, 7 |
| B-F14 sweep sizes / band widened | already dispositioned | `dee96a4` (r1 F11) | the `/` half of the grep was fixed; the sample sizes are a documented divergence | 1 — satisfied |
| B-F15 entrypoint docstring inverted | **fixed** | `1cb9416` | the docstring states the order the code uses | none — note only |
| B-F16 `plan` event field set | refuted | — | `pushes`/`blocked` cannot exist at `beginTurn`, and the only place they could be added is one playback never reaches | none — note only |
| B-F17 private `notes` in the replay bytes | **fixed** | `eb31ee8` | the plan record writes an empty `notes`; the field (and `GameVersion`) stay | none — note only |
| B-F18 `/client/replay` route exists | refuted | — | nothing declares a pod viewer; the starter serves the same route; the note says so explicitly | 3 (wording vs declared surface) |
| B-F19 `game.docs` `"type":"uri"` | already fixed | `7a5c370` (r1 F17) | `text`, with the committed documents inline, pinned to the files by a test | **10 (manifest)** |
| B-F20 relaxed pick + player-cell draw | already fixed + **fixed** | `7843231` (r1 F7) + `a72dbac` | closest-to-`bandMin` was r1's; the player cell now uses the winning attempt's hash word | none — note only |
| B-F21 macros expand on an advanced snapshot | refuted | — | the reviewer's own trace: the literal reading cannot execute, and the box-index half of the pin is honoured | none — note only |
| B-F22 records-exhausted replay settles wrong | **fixed** | `c6dae61` | playback settles when the records run out, deriving `turnCap` the way the server does | **2 (replay re-derivation)** |

---

## The twelve fixes

### B-F2 — the `fallback` event carries the turn's real cause (`c50a0ae`)
`beginTurn` emitted the literal `"cause": "fallback"`, so every fallback looked alike in the feed and
on the scrubber while the real cause sat in a chat record the renderer never read. The hard part is
that the cause must be identical live and re-derived, and the replay runtime rebuilds the directive
from the *plan* record, which does not carry it. Both paths now file chat records through one proc,
`sim.noteChatRecord` — the live server where it used to `feed.add(parseJson(record))`, the runtime's
`applyChat` for the same two kinds — which remembers a `fallback` record's cause for the plan that
follows it at the same tick. `beginTurn` puts it on the event and clears it. Test: a `fallback`
record with `cause: "timeout"` produces `"timeout"` on the event, and the next turn without one
produces the neutral default.

### B-F4 — the budget guard reserves the rate floor (`01adc41`)
`turnStart` was taken before the `turnSpacingMs` sleep, so `turnBudgetMs` was described as a deadline
around the whole turn while it gated only attempt *starts*: 2.6 + 6 + 3 = 11.6 s against a 9 s
budget. Clamping the attempts to the remaining budget would have silently cut the retry on exactly
the turns that waited for the rate floor, so instead the deadline is taken after the floor and named
for what it bounds — the decision, which is the invariant `sim_config.validate` enforces
(`attempt1Ms + retryMs ≤ turnBudgetMs`) — and the bound that matters is made explicit where it is
used: the budget guard now reserves `turnSpacingMs + turnBudgetMs` per remaining turn (23.2 s for
two, not 18 s). Test: at 670 s elapsed the old reserve still thought two turns fit inside the 690 s
stop; the new one fires. Item 5 was already satisfied in aggregate — a turn that burns 9 s leaves the
next with no floor to pay, so the episode total is ≈ 60 × 9 s + 2.6 s — but the guard's own reserve
was the optimistic figure, and now is not.

### B-F6 — the inset rides `var(--band)`, and CI measures it (`f356da2`)
`#stage.tiny #fpv { bottom: calc(30 * var(--u)) }` had no band term, and the starter's base rule uses
a hard-coded 64u. The transport is built from `--u` units too (16u padding + a 34u scrub + a 26u-min
button row ⇒ `--band` ≥ 76u before wrapping), so the repurposed panel sat inside the band and paints
above it in z-order. Checklist item 14(b) is explicit. `#fpv`, the `.tiny` override and `#killfeed`
(the starter's other hard-coded guess, and where this game's `say` lines land) now ride the measured
variable. The claim is no longer CSS-only: `tools/ci/renderer_fixture.html` measures `#fpv`,
`#sk-ribbon`, `#sk-pips` and `#killfeed` against `#transport`'s own rect at 360, 640 and 1280 px and
fails the viewer smoke on any intersection > 1 px — green in run 33247581241, which is the
measurement the reviewer listed under "Could not determine".

### B-F7 — the `.tiny` inset clears the pips (`3adc9d3`)
With the band term added, the left column reads inset (`band+22 … band+106`), pips (`band+112`),
ribbon (`band+124`) — a 6u gap that cannot close, where before the two were measured from different
origins. It stays in the left column rather than the note's "right gutter" because `relayout()` sets
`#stage`'s width to the board's, so no gutter exists *inside* the stage, and the stage's right edge
at this density belongs to the inherited `#killfeed`. The reviewer traced the same constraint; the
reasoning is now in the CSS.

### B-F8 (remainder) — the feed's `bad`/`good` rows are styled (`78c5553`)
The say-row half was r1's `c9f9d4d`. The block also tags deadlock/lost rows `bad` and solves `good`,
and neither class had a rule, so `DEADLOCK CREATED — CRATE 2 CORNERED AT (7,1)` read like a routine
turn line. Two rules each, in the palette's red and green, matching the beat colours for the same
events.

### B-F10 — a faulting smoke fails the build (`2c7aec6`)
`docker_smoke.sh` prints `results.reason` and never compares it. The comparison is a new `ci.yml`
step rather than a local edit to the shared script — that script is byte-identical to the template
apart from its three placeholders, which is itself evidence a reviewer checks, and it already copies
`results.json` next to the replay. It fails on `reason == "fault"` or `endRule == "fault"` and on any
reason outside the closed set. Evidence, run 33247581241:
`smoke episode: reason=complete endRule=ladderComplete stopDetail=''`.

### B-F11 — the emitted wasm module runs in CI (`8885041`)
`tools/wasm_replay_smoke.cjs` is the note's test 51 and was wired to nothing. The `wasm-viewer` job
now runs it against the bundle it just built and the replay `docker-smoke` just produced, before the
Playwright download so it fails fast. Evidence:
`ok: loaded replay.json, advanced 300 frames (3627422 packet bytes, heap 16 MB)` — 300 frames with
`sokoban_mismatch_tick()` checked before and after, i.e. the wasm32 build re-deriving the recording
without divergence.
`tools/ci/page_smoke.mjs` is left unwired **on purpose**: its own header says it is "a LOCAL
developer gate, not a CI job", it stubs the wasm runtime rather than running it, and it needs a
`wire_constants.js` at the repo root that only a local build writes. The note does not list it.

### B-F13 — the harness matches the server (`e44b769`)
Two divergences fixed: `runEpisode` wrote a `rkStop` record for every forced stop, including a
`complete`/`turnCap` one that the server never writes; and it settled every natural end
`ladderComplete`, where the server derives `turnCap` when the loop ends with the ladder unfinished.
The third strand — nothing in `tests/` drives `runGame`/`finishEpisode`/`writeArtifact` — is left as
recorded coverage: `docker_smoke.sh` runs the real binary end to end and validates the real
`results.json` and the real replay bytes (`smoke OK: seats=1 results=924B replay=53113B
reason=complete`), which is the only place that path can be exercised without sockets.

### B-F15 — the entrypoint docstring (`1cb9416`)
Documentation only, as the reviewer traced: the code reads the runner's config first and randomises
only when no seed was pinned, which is what makes a pinned seed win. The docstring said the reverse.

### B-F17 — the private scratchpad stays out of the replay (`eb31ee8`)
`writePlan` serialised `directive.notes` into every plan record, so the policy's private scratchpad —
excluded by name from the `directive` chat record and stripped from the mirrored observation — shipped
in an artefact anyone with the URL can decode. Nothing at playback needs it: the sim reads `notes`
only through `endTurn`, which the replay runtime never calls. The field stays in the format and is
written empty, so the byte layout, the reader and `GameVersion` are unchanged. Test: a plan record
with a distinctive scratchpad string — the `say` reaches the bytes, the notes do not.

### B-F20 (remainder) — the relaxed player cell (`a72dbac`)
The "deepest vs closest to `bandMin`" half was r1's `7843231`. The relaxed path also drew the player
start with `hashAt(seed, levelIndex, 0, 500)` — attempt 0 — while the board and the state came from
whichever attempt won; it now uses the winning attempt's index, so every draw for a level comes from
that level's own room. Pure either way, so the purity assertions are unaffected.

### B-F22 — a records-exhausted replay settles on the turn cap (`c6dae61`)
`stepReplay` settled only on a finished ladder or a stop record. A `turnCap` episode carries no stop
record, so playback would run past the last recorded plan on `wait` primitives until the step budget
fired — changing that level's `levelOutcome` and inventing ticks beyond the recorded hash chain,
which the index-guarded hash comparison would not even flag. Playback now settles when the records
run out with the current turn fully played, deriving `ladderComplete`/`turnCap` exactly as the server
does. The round-trip test could not reach this before (`stopAtTurn = 60` against `maxTurns = 60`
never fired, making the `turnCap` scenario a second copy of `ladderComplete`); it now caps a real
episode at three turns, asserts the recording carries **no** stop record, and re-derives it hash for
hash. This is checklist item 2, latent until now.

---

## The four refutations

### B-F5 — "the server does not refuse to start" — **refuted (the note contradicts itself)**
The note says both "the server logs loudly and refuses to start the game when the joined seat has no
register record" (§named edits 2, §Tests 32) **and** "A silent seat does not end the episode … the
ladder runs to its natural end with `deadSeats[0] = true`" (§Decisions), and the two cannot both
hold. The code takes the second: it logs the exact loud error, declares the player failure with the
platform's closed payload, seats `pusher`, sets `dead = true`, and plays the ladder out. That is the
half checklist item 5 needs — an episode that refused to start would produce no `results.json` and no
replay, i.e. a hang from the platform's point of view, which is the failure mode the whole
degrade-never-hang rule exists to prevent. Changing it to match the other sentence would trade a
checklist item for a note sentence. `src/sokoban/server.nim:229-252`.

### B-F12 — "the tuning sweep is not re-run in CI" — **refuted (item 7 is satisfied)**
Checklist item 7's second sentence is "The baseline's parameters were tuned with a grid harness, not
guessed". The harness is committed and is a real sweep (10 node caps × greedy-match × tie-break over
40 cached seeds — the reviewer verified this), its pick is recorded in `tools/ci/baseline_tuning.json`
and `tests/test_sokoban_events.nim:143-160` asserts the shipped `DefaultSearchParams`, the manifest's
three `game_config` blocks and that file all agree. The independent re-measurement of *strength* is
`tests/test_sokoban_baselines.nim`, which plays real episodes and gates the solve rate per tier. What
is missing is re-running the sweep itself in CI, which is minutes of level generation to re-derive a
pick nothing can silently change — a runtime cost, not a coverage gap. Recorded as residue, same as
in `r1-fixes.md` (F6).

### B-F16 — "the `plan` event's field set differs from the note's" — **refuted (unbuildable there)**
`pushes` and `blocked` do not exist when `plan` is emitted: `beginTurn` installs the plan and the
ticks run afterwards, which is the note's own numbered resolution order. The only place they exist is
`endTurn` — and the replay runtime never calls `endTurn` (`replay_runtime.nim`'s `stepReplay` applies
plan records through `beginTurn` only), so an event emitted there would exist live and be missing in
playback, breaking the property that makes the broadcast stream re-derivable at all (checklist item
2). The two extra fields (`actions`, `source`) are what the shipped feed line is built from, and
`tests/test_sokoban_events.nim` pins the emitted **kinds**, which are the closed vocabulary the note
declares. Recorded as a note-vs-code divergence where the code is the coherent half.

### B-F18 — "`/client/replay` is a registered route" — **refuted (nothing is declared to the platform)**
Checklist item 3's subject is the declared viewer: the manifest carries
`game.replay_viewer = {"bundle": "static-replay-viewer"}` and no pod viewer, `coworld-release.yml`
carries the guard string, and the bundle's only network call is `fetch(replayUrl)`. The route serves
the same page locally for developers, exactly as the starter does
(`coworld-ctf/src/ctf/server.nim:631,646,844` — and coworld-ctf ships a `static-replay-viewer`
manifest), and the design note says so in as many words: "No `/client/replay` live-server viewer is
ever declared to the platform; the game still serves `/client/replay` locally for developers."
Removing it would diverge from the starter and break local development to satisfy a word, not a
property. Both reviewers traced this to the same place independently.

### B-F21 — "macros expand against a forward-advanced snapshot" — **refuted (by the reviewer's own trace)**
The reviewer traced it as coherent and I agree: expanding macro *k+1* from the original player cell
would produce a walk that cannot execute, so a two-macro turn would be systematically broken. The
half of the pin that is load-bearing — `push.box` indexing the **turn-start** order the observation
handed the policy — is honoured (`driver.nim:122-125`'s `live[]` array), and expansion mirrors
execution primitive for primitive, which is what "expansion and replay identical" is for. Documented
in the code at `driver.nim:48-52` and `:104-106`. No change.

---

## Already fixed by the r1 series (evidence)

* **B-F1** = r1 F1, `1dd3edb`: `endTurn` reports `sim.turnDropped` (validation failures + over-cap),
  `directiveRecord` reads `sim.lastReport.dropped`, and `tests/test_sokoban_obs.nim` asserts
  `last_turn.dropped == 3` for a directive with two invalid entries and one past the cap.
* **B-F3** = r1 F5, `cfe9d10`: a 429 records `transport_error`; a test scans `decide.nim` for every
  cause literal it can write and asserts each is in the declared seven.
* **B-F8** (say row) and **B-F9** = r1 F9, `c9f9d4d` + `f31307a`: the say row has a reserved band, the
  fixture asserts the rendered row still carries all 140 runes and sits inside the frame, and it
  mirrors every line the page laid out into a main-thread 2D canvas so the gate measures something.
  The reviewer's diagnosis — "`viewer_smoke.mjs` reads the bounds report on the **top** frame only, so
  the iframes' own `__coworldTextBounds` are never collected" — is exactly what the mirror answers.
  Run 33247581241: `canvas text: 25 drawn, 0 never inside the canvas (0 draws crossed an edge)`.
* **B-F14** = r1 F11, `dee96a4`: the no-float grep now also rejects `/`; the sample sizes remain a
  divergence recorded in `tests/helpers.nim` with its reason.
* **B-F19** = r1 F17, `7a5c370`: `game.docs` is `{"type":"text"}` with the committed documents
  inline, pinned to `README.md` and `docs/{RULES,ACTIONS,LEVELS}.md` by the manifest test.
* **B-F20** (relaxed pick) = r1 F7, `7843231`.

## NOTED (not fixed)

* The tuning sweep is not re-run in CI (B-F12) — residue, as in `r1-fixes.md`.
* Nothing in `tests/` drives the real artifact path (B-F13's third strand); `docker-smoke` covers it
  with the real binary.
* `disconnected` remains a declared `fallback.cause` that nothing produces.
* Sub-tick interpolation of the cog and the pushed crate is still absent (r1 F14).

## Push mechanism

Unchanged from the r1 round and recorded again for the judge: git-over-HTTPS Basic auth is unusable
in this sandbox (the token is base64-encoded inside the `Authorization` header, so the egress swap
never sees it and GitHub answers `Invalid username or token`; the REST API works and
`gh api repos/... --jq .permissions` reports `push: true`). These twelve commits were recreated
through `git/blobs` → `git/trees` → `git/commits` → `PATCH git/refs/heads/main`, in order, one commit
per finding, onto the existing `main` tip. `git rev-parse main^{tree}` equals the local tree exactly.
No ref was force-updated. The duplicated r1 series noted at the end of `r1-fixes.md` is still below
these commits in the history; `git diff 464b2ab..main` remains exactly the intended change.
