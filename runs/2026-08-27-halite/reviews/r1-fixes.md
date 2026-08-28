# r1 fixes — 2026-08-27-halite (`Metta-AI/cogame-halite`)

Head: `17fa7b5ee41f0aa74c9e165fd51bba558736928e` (was `f403fa0e…`)
CI: https://github.com/Metta-AI/cogame-halite/actions/runs/33138420080 — **success**
(run id `33138420080`, `ci.yml`, event `push`, head sha `17fa7b5ee41f0aa74c9e165fd51bba558736928e`,
jobs `test` / `docker-smoke` / `wasm-viewer` all `success`). From that run's log:
`342 passed, 2 skipped in 250.55s`; `smoke OK: seats=4 results=1068B replay=384420B reason=complete`
and the script's own new line `episode end reason: complete (end_rule=full_time)`;
`results OK: complete full_time [295, 978, 552, 789]`;
`renderer fixture: 7120 text runs measured, 137 crossed an edge, 0 never inside`;
`grep -c "SEAT-COUNT FAIL"` over the whole log = **0**. The two skips are the coworld-ctf mount test
(no starter mount on a runner — its digest half now runs there, see F8) and the built-bundle node
test.

Base for the diff: `f403fa0e99ba4637fb2af2bcab5de61bf30cd776`. Fourteen commits, one per finding,
pushed through the GitHub REST API (blobs → trees → commits → a single fast-forward ref PATCH);
`git push` over HTTPS returns "No anonymous write access" in this sandbox. Nothing was force-pushed
and no commit already on the remote was recreated: `git diff HEAD origin/main` is empty.

Findings are numbered as in `r1-review.md`.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 elimination clears shipyards | fixed | `9a4aeff` | `server/cogame_halite/sim.py:294`, `tests/fidelity_stream.py`, `tests/test_fidelity.py`, `tests/test_sim.py` |
| F2 no `step` / `remainingOverageTime` on the wire | fixed | `a4add14` | `server/cogame_halite/engine.py:107`, `docs/PROTOCOL.md:58`, `tests/test_engine.py` |
| F3 660 s starts after the lobby | fixed | `cc09a10` | `server/cogame_halite/engine.py:86`, `server/cogame_halite/server.py:48`, `tests/test_server.py`, `tests/test_engine.py`, `AGENTS.md` |
| F4 `docker_smoke.sh` asserts neither | fixed | `3df52bc` | `tools/ci/docker_smoke.sh:299`, `tests/test_results.py:58` |
| F5 `/client/replay` pod path | fixed (checklist over note) | `76caaf0` | `server/cogame_halite/server.py:410`, `tests/test_server.py`, `docs/PROTOCOL.md:25`, `viewer/build_viewer.sh` |
| F6 docs are `{"type":"uri"}` | fixed | `3cdf103` | `coworld_manifest_template.json:459`, `tests/test_manifest.py:71` |
| F7 four "Removed" ids are hidden stubs | documented (constraint is real) | `17fa7b5` | `docs/plans/2026-08-27-halite-design.md` + the run-dir copy, identical bytes |
| F8 chrome byte pin never runs in CI | fixed | `13f5314` | `tests/test_viewer.py:34` |
| F9 two smoke passes measure no text | refuted, and pinned | `123698d` | `tests/test_viewer.py`, `.github/workflows/ci.yml:240` |
| F10 over-cap drops not counted | fixed | `549b25a` | `server/cogame_halite/engine.py:162`, `server/cogame_halite/server.py:381`, `tests/test_engine.py:289`, `docs/PROTOCOL.md` |
| F11 status/reward compared once | fixed | `1620b74` | `tests/test_fidelity.py:127` |
| F12 one player-failure payload | fixed within the closed payload | `4cdd5e6` | `server/cogame_halite/engine.py:503`, `tests/test_engine.py` |
| F13 undocumented 4th ctf adaptation | documented | `64e8862` | `replay-viewer/static_replay.js:1`, `replay-viewer/static_replay_worker.js:1`, `docs/REPLAY.md:93`, `tests/test_viewer.py:94` |
| F14 nine duplicated early commits | **wontfix** | — | — |
| F15 no grid-tuning harness | fixed (harness + sweep + retuned constants) | `0b84154` | `tools/tune/grid_search.py`, `docs/tuning/2026-08-28-micro-grid.md`, `server/cogame_halite/micro.py:34`, `tests/test_tuning.py`, `tests/test_players.py:151` |
| F16 `HOST`/`PORT` vs `COGAME_HOST`/`COGAME_PORT` | **refuted** (note shorthand), documented | `17fa7b5` (appendix item 3) | `server/cogame_halite/server.py:449` |

No test was weakened, skipped or deleted. `git log -p f403fa0..HEAD -- tests/` is 8 new tests, 3
strengthened assertions and 2 assertions whose *values* moved with a code change that is itself the
fix (F15's tuned constants, F13's rename to "four adaptations"); no `skip`, `xfail`, widened
tolerance or deleted assertion anywhere. Local suite at the pushed head: **343 passed, 1 skipped**
(the skip is `test_the_built_bundle_parses_the_ci_replay_under_node` — no emsdk in the sandbox; the
`wasm-viewer` job is its gate).

---

## F1 — the elimination transcription cleared an eliminated seat's shipyards

**What it did.** `sim.py::_eliminate` ran `self.players[seat] = [bank, {}, {}]` for every seat it
eliminated. **What it does now.** Nothing: the seat's assets stay exactly where upstream leaves them.

Upstream's `interpreter()` (`vendor/upstream/…/halite.py:195-202`) sets `status = "DONE"` for a seat
with no ships and (no shipyard or `halite < spawnCost`), and clears `obs.players[index]` **only** in
the separate `if agent.status != "ACTIVE" and agent.status != "DONE"` branch — an INVALID / TIMEOUT /
ERROR agent, a status this engine never produces (a seat that stops answering is substituted for,
never invalidated). A DONE agent keeps its shipyards, so an unfunded yard stays on the board as a
razing hazard and a permanently-zeroed cell for the seats still playing. `docs/PORTING.md`'s
inherited rule is "never fix an upstream quirk"; the reviewer's executed experiment against a real
`kaggle-environments==1.32.7` is the evidence, and upstream wins over the note's step-9 prose.

**Why the gate could not see it, and what makes it see it now.** `tests/fidelity_stream.py` is built
so no seat can ever be eliminated, and the gate asserted that. This adds a second stream,
`elimination_stream_step`: seat 0 converts its opening ship, then spawns on consecutive turns so each
pair of 0-cargo ships destroys itself on the yard cell (500 halite and one ship gone per turn, none
left over), spends its last 500 on one more ship and walks that ship into an enemy shipyard — which
destroys the ship. The seat is then at **0 ships, bank 0 and its own yard standing**: eliminated,
with assets. Once it is out, a seat-1 ship walks onto the abandoned yard, so the raze is compared
too. `test_differential_episode_with_an_elimination` runs that over 3 seeds × 399 turns with the same
exact-equality comparison, and `test_the_elimination_stream_eliminates_one_seat_with_a_yard_standing`
pins the properties without needing upstream.

**Evidence.** With the fix, seed 42: identical for all 400 states; victim eliminated at turn 20 with
`players[0] = [0, {'1-1': 110}, {}]` on both sides, upstream `status[0] = DONE`, `reward[0] = -381`;
the yard is razed at turn 31. Reverting only the `sim.py` line: `FIRST DIVERGENCE at 20`, ours
`[0, {}, {}]` vs upstream `[0, {'1-1': 110}, {}]`. Also `tests/test_sim.py`'s new
`test_an_eliminated_seat_keeps_its_shipyard_and_it_stays_a_hazard`, which additionally asserts the
enemy ship that steps on the abandoned yard dies with it. Checklist item 1 (no test loosened; the
gate got stronger).

## F2 — `Board(obs, config)` raised `KeyError('step')` on the wire frame

The engine built the `observe` frame field by field and dropped the two Kaggle observation keys the
sim already carries. `Board.__init__` reads `observation.step` and
`observation.remaining_overage_time`, so `docs/PROTOCOL.md`'s "a Kaggle bot's `Board(obs, config)`
works unchanged" was false. The frame now carries `step` (always equal to `turn`) and
`remainingOverageTime` (always the config default, 60 — the design note's §Out of scope).

**Evidence.** `test_a_kaggle_bots_board_builds_from_the_wire_frame_unchanged` drives a real episode,
takes the frames the engine actually wrote to seat 2's socket (round-tripped through JSON), builds a
board with the **vendored** helpers and asserts `board.step`, `current_player_id`, the cell count and
every seat's bank / ship ids / shipyard ids. Removing the two keys makes it fail with
`KeyError: 'step'` (verified). `docs/PROTOCOL.md`'s frame and its prose were corrected with it.

## F3 — the wall-clock budget now runs from process start, and the artifact phase is capped

`Engine.started_at` was `clock()` at construction, and the server constructs the Engine **after** the
lobby, so the 600 s guard and the 660 s hard stop excluded the lobby (≤ 120 s), the artifact writes
(2 × 3 attempts × 30 s + backoff ≈ 182 s worst) and the 20 s shutdown grace. Nothing in the code
bounded the note's 720 s pin.

Now: `Engine(..., started_at=…)`, and `server.py` passes `PROCESS_STARTED_AT` (taken at import), so
the lobby is spent inside both budgets; and `_write_artifacts` runs under
`ARTIFACT_WRITE_BUDGET_SECONDS` (20 s). Worst case from process start —
660 (hard stop) + 18 (one in-flight directive turn; the stop is checked at a turn boundary) +
20 (artifacts) + 20 (grace) = **718 s < 720 s** — is asserted by
`test_the_worst_case_container_time_fits_inside_the_platform_pin`, the arithmetic is spelled out in
a comment at `server.py:56-76`, and `test_a_hanging_artifact_write_cannot_outlive_its_budget` proves
the cap by making every write hang. `results.reason` semantics are untouched: the hard stop still
ends the episode `deadline`, settled by the same ladder. Checklist item 5.

## F4 — the smoke script asserts `complete` and the closed key set itself

`docker_smoke.sh` checked two array lengths, *warned* if they were missing, and only **printed** the
end reason; the assertions lived in `ci.yml`, so the local invocation `AGENTS.md` documents checked
neither. The script now carries `RESULTS_KEYS` literally (the third of the three copies the note
names), fails on any drift with `missing=…/extra=…`, length-checks every per-seat array, and fails
on `reason != "complete"` quoting `end_rule` and `stop_detail`. `ci.yml`'s own assertions are
unchanged — they import `RESULTS_KEYS` from the code, which is what stops the literal copy drifting —
and `tests/test_results.py` now parses the script's list and compares it to `results.py`.

**Evidence.** Extracted the script's python block and ran it against a real episode's artifacts:
exit 0 on `complete`; exit 1 with "smoke episode ended reason='deadline'…"; exit 1 with
"results.json is not the closed key set: missing=['stop_detail']". Checklist item 6/7.

## F5 — the `/client/replay` pod path is gone

`server.py` served `/client/replay` (302 into a `viewer/dist` static mount) on the episode app and in
replay mode. The design note asks for it (§Runtime contract, inherited from moba); checklist item 3
says "No `/client/replay` pod path anywhere" and that the viewer contacts nothing but S3. Resolved in
favour of the checklist, because **nothing depends on the route**: `coworld certify` skips the legacy
`/client/replay` + `/replay` liveness probe when `game.replay_viewer.bundle` is declared —
`coworld/cli.py:596` prints "Replay liveness: skipped (static replay bundle declared; /client/replay
and /replay not required)" and `coworld/docs/STATIC_REPLAY_VIEWERS.md:167` says a declared static
bundle "replaces this legacy route requirement" — and `coworld-release.yml` already fails the release
unless certification reports the STATIC bundle.

`GET /replay-data` stays: it is bytes, not a viewer, and is how the built bundle is pointed at a
local episode (`index.html?replay=http://localhost:8080/replay-data`). The new test asserts 404 on
`/client/replay`, `/client/replay/` and `/client/replay/index.html`, and that the module registers no
static mount and no longer references `viewer/dist` at all.

## F6 — `game.docs` is inline text

Both forms are first class in the platform's own schema
(`coworld/coworld_manifest_schema.json` §CoworldTextDoc / §CoworldUriDoc), and the installed CLI
accepted the `uri` form — so there was nothing to trade off against checklist item 10, which spells
the docs shape as `{"type":"text","value":…}`. `game.docs` now carries `README.md`, `docs/RULES.md`
and `docs/REPLAY.md` verbatim, which also renders on the platform without following a GitHub *blob*
URL that serves HTML rather than markdown. `game.protocols` keeps the `uri` objects the design note
pins (both `player` and `global`). `test_the_inline_docs_are_the_repo_files_verbatim` asserts each
value is byte-identical to its file — and it earned its keep immediately, catching the stale copy
after F13 edited `docs/REPLAY.md`. The CLI's own `_load_template_manifest` +
`validate_upload_manifest` still pass (`tests/test_manifest.py`, run in CI).

## F7 — the stubs are a real constraint; the note now says so

`client/chrome_common.js` is pinned byte-for-byte and dereferences `#ffwd-chip`, `#ffwd-mini`,
`#lulls` and the `#momentum` block unconditionally, so removing the nodes throws on the first frame;
un-pinning the chrome to delete four `getElementById` calls is what checklist item 14 forbids. The
nodes stay hidden and never drawn, and the design note gets a **"Deviations (build)"** appendix
recording them plus every other confirmed note↔code divergence this round did not code away (F16's
env names, the removed route, the extra frame keys, the process-start budgets, inline docs, the
fourth ctf adaptation, the audit counter, the second fidelity stream, the tuned constants, the
recorded chrome digests, the canvas-text zero, and F14). The in-repo copy and the run-directory copy
are byte-identical (sha256 `fc883e34d24f36b06e105e73ee1e05f0794bf044e8352b44142990e7c631c6c3`).

## F8 — the chrome pin is enforced where CI can see it

The byte comparison skipped whenever `/workspace/starters/coworld-ctf` was absent, which is always
true on a runner. The sha256 of ctf's `client/chrome_common.js` (`7ace7287…`) and
`client/broadcast_core.js` (`172c4680…`) are now asserted unconditionally, and the mount-based
comparison — kept — additionally asserts those digests are the **starter's**, which is what proves
they were not copied from ours. Checklist item 14.

## F9 — refuted: this viewer draws no canvas text at all

`canvas_text.total == 0` in the bundle+replay and 360×640 passes is not a missed hook. The wasm
renderer emits sprites, the Worker's compositor blits pixels into an OffscreenCanvas, and every
string a spectator reads is a DOM node: there is no `fillText`/`strokeText` in
`replay_broadcast.html`, `chrome_common.js`, `broadcast_core.js`, `static_replay{,_worker}.js` or
`halite_replay.nim` — the only one in the tree is `renderer_fixture.html`'s own transcription. That
is exactly the case checklist item 15 anticipates, which is why the repo ships the worst-case
renderer fixture and `ci.yml` gates it on `total >= 12` and `never_inside == 0` (observed: 7072 runs
measured, `never_inside 0`). The new test asserts the premise so the zero cannot start hiding
something, and `ci.yml` now says it where the number is produced.

## F10 — over-cap entries are counted

`Engine._accept` now applies the cap the way the note words it — the first 256 entries by ascending
uid are validated, the rest are dropped — and tallies the discards in `SeatState.dropped_over_cap`,
logs the first occurrence per seat with the turn and count, and the server prints any nonzero tally
in the end-of-episode audit block. Deliberately **not** a `results.fallbacks` key: that set is closed
to the five wire causes in three places and an over-cap reply is not a substitution (the reply is
used). The existing over-cap test now asserts the exact count, the log line, and that no fallback
cause moved; `docs/PROTOCOL.md`'s cap table says where the count lives.

## F11 — statuses and rewards are compared at every turn

`_assert_identical` derives our status and reward per seat per turn — ACTIVE unless eliminated, DONE
once eliminated (and DONE for everyone on the last step, core's own rule); reward is the bank while
active and `eliminated_turn - episodeSteps - 1` after — and asserts upstream's per-turn `status` /
`reward` arrays equal them. It applies to both streams, so F1's elimination case now compares the
DONE transition and the frozen negative reward at the exact turn they happen, which is what the
design note §fidelity gate and `docs/RULES.md` promised.

## F12 — one payload, naming every dead seat

Reporting once per seat is not available: the platform payload is closed to
`{"message", "failed_policy_index"}` — one index — and the channel is a URI write, so a second write
would **replace** the first and lose the earlier failure. `_report_dead_seats` therefore emits a
single report whose `failed_policy_index` is the lowest dead seat (it struck out first) and whose
message names every dead seat with its alias; the single-write guard and the closed shape are
unchanged. `test_several_dead_seats_are_one_payload_that_names_them_all` kills seats 1 and 3 and
asserts both are named.

## F13 — the fourth adaptation, documented where it happens

`wire_constants.js` is not a file in the coworld-ctf tree: ctf **generates** it during its own image
build (`tools/gen_wire_constants.nim` → `replay-viewer/dist/wire_constants.js`, from
`src/ctf/wire_constants.nim`) and it carries ctf's paintball wire enums. There is nothing to copy and
nothing here reads it; importing a file the bundle does not ship would 404 the Worker's boot. Named
as adaptation (4) in `static_replay.js`'s header, at the `importScripts` call site, in
`docs/REPLAY.md` and in the design-note appendix. The viewer test is renamed to the four adaptations
and now asserts the `importScripts` **call** (not a mention in a comment) is exactly the two-file
list.

## F14 — wontfix

The nine duplicated early commits are on the remote already. Removing them requires rewriting pushed
history (`git push --force`), which the fixer rules and this repo's conventions forbid, and there is
no non-destructive alternative — the duplicates are reachable commits, not refs. The tree at `main`
is single and coherent (`git diff` between the two chains' heads is empty), nothing downstream reads
history, and the appendix records them so the next reader is not surprised. Cost of leaving them:
`git log` is 9 lines longer than it should be.

## F15 — a grid harness, a recorded sweep, and constants that are now its choice

`tools/tune/grid_search.py` sweeps `mineFloor` × `returnAt` × `spawnUntil` (48 combinations) with the
candidate at seat 0 and the shipped baselines at seats 1-3, playing real 400-turn `HaliteSim`
episodes through the shipped `micro.compile_turn`. No seat rotation is needed: `populate_board` makes
the board exactly 4-fold symmetric, so the seats are equivalent by construction. Stage 2 replays the
top five plus the incumbent on **16 fresh seeds the grid never saw**, because the maximum of a
48-cell grid measured on six episodes is overfitting.

The runoff is decisive out of sample, so the guessed constants were replaced by its winners:

| baseline | was | now | runoff wins (of 16) |
|---|---|---|---|
| `tidewalker` | `mineFloor 100, returnAt 500, spawnUntil 300` | `200 / 300 / 200` | 0 → 7 |
| `corsair` | `mineFloor 150, returnAt 350, spawnUntil 340` | `200 / 300 / 300` | 5 → 10 |

`stance`, `yards`, `focus` and `avoid` are unchanged. `TIDEWALKER` is also the turn-0 directive an
LLM seat starts from, so `test_turn_zero_defaults_…` moves with it (same assertion, tuned values,
reason in the docstring) and the design-note appendix records the new table.
`docs/tuning/2026-08-28-micro-grid.md` holds both stages' full tables and the exact commands;
`tests/test_tuning.py` asserts the shipped constants are the recorded winners, that the runoff seeds
are out of sample, and runs a tiny sweep so the harness cannot rot. Checklist item 7.

## F16 — refuted

`docs/PROTOCOL.md:11`, `server.py:449` and `tools/ci/docker_smoke.sh:204` all use `COGAME_HOST` /
`COGAME_PORT`, which is what the cogame-moba starter does
(`starters/cogame-moba/server/cogame_moba/server.py:804`) and what the platform sets. The note's
`HOST`/`PORT` in §Runtime contract is inherited shorthand, not a contract the code breaks. Recorded
as deviation 3 in the appendix rather than changed — renaming the variables would break the smoke
script and the platform's own env.

---

## The reviewer's "could not determine" items

1. **Whether F1's divergence is reachable in a real episode** — settled: **yes**, and now
   deterministically. `elimination_stream_step` reaches "0 ships, bank under the spawn cost, yard
   standing" from the opening board in 20 turns using only legal orders, on all three gate seeds. The
   shipped scripted baselines guard against it (`micro.py`'s shipyard-loss guard), but an LLM
   directive that spends the bank down does not.
2. **Whether the platform's validator prefers `{"type":"text"}` docs** — settled from the platform's
   own schema: both forms are valid (`CoworldTextDoc` / `CoworldUriDoc` under a `type` discriminator,
   in `game.docs.readme`, `pages[*].content` and both `game.protocols` entries). Fixed to `text` for
   the docs anyway (F6), since the checklist spells it and the inline form renders without following
   a blob URL.
3. **The real wall-clock profile** — still not measurable here (it needs a hosted episode with a slow
   lobby), but it is no longer only arithmetic: the budget is measured from process start, the
   artifact phase is capped, and a test asserts 660 + 18 + 20 + 20 = 718 ≤ 720 from the constants
   themselves. What would still settle the empirical question: one hosted episode timed from
   container start to `results.json`.
4. **Whether the 141 `outside` draws in the renderer fixture are real clipping** — **not settled**;
   it needs a browser, and the sandbox has none (the DOM harness under node has no layout engine, so
   `getBoundingClientRect` is not available to it). The mechanism is in the fixture's own header:
   `elementRuns` transcribes a **leaf element's box** and scales the font so the drawn width equals
   that box, so a wrapped element is redrawn as one line and its right edge is the box's, not a
   line's — per-character Range rects were tried first and produced phantom failures on right-aligned
   wrapped rows. The gated number, `never_inside`, is **0** in every pass, and the same run's
   geometry readout at 360 px shows `feed=[6,355] row=[6,355]` — inside a 360-wide frame. Settling it
   needs `viewer_smoke.mjs --url …renderer_fixture.html --strict-text-bounds` with a per-line-box
   transcription, or a screenshot diff at 360×640.

## NOTED (not fixed)

* `results.fallbacks` cannot grow a sixth key without touching four places and the note's closed
  23-key list, which is why F10's counter is an engine-side audit counter. If phase 60 wants over-cap
  drops in the results document, that is a design change, not a fix.
* `tests/test_viewer.py` is now the only place that records ctf's chrome digests. If the starter is
  re-pulled, both the files and the two constants have to move together.
* The grid harness sweeps three axes. `MAX_SHIPS` (24), `PATCH_RADIUS` (6) and the second-yard gates
  (`bank >= 1500`, `far >= 5`) are still hand-chosen; the harness can sweep them, but they are
  `micro.py` module constants rather than directive fields, so it would need a second entry point.
