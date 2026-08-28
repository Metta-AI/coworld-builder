# r2 review — 2026-08-27-halite (`Metta-AI/cogame-halite`)

Repo read at `main` = `17fa7b5ee41f0aa74c9e165fd51bba558736928e` (fresh clone at
`/tmp/review2-halite`). Design note: `runs/2026-08-27-halite/design.md`, **byte-identical**
to the in-repo `docs/plans/2026-08-27-halite-design.md` (sha256
`fc883e34d24f36b06e105e73ee1e05f0794bf044e8352b44142990e7c631c6c3`, both copies), appendix
`## Deviations (build)` present at line 1130 of both.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Starters read: `/workspace/starters/cogame-moba`, `/workspace/starters/coworld-ctf`.
Files read: ~50 in-repo + 4 starter files + the three r1 artefacts.

**Evidence beyond static reading (all executed here):**

- Full local suite at head with the CI-only fidelity group installed
  (`kaggle-environments==1.32.7`): **343 passed, 1 skipped in 269 s** — the differential gate,
  including the three elimination seeds, ran green against a real upstream install.
- CI run **33138420080** (`gh run list/view`): `push`, `main`, headSha `17fa7b5e…`, conclusion
  **success**; jobs `test`/`docker-smoke`/`wasm-viewer` all `success`; **every step ran**
  (no skip, no `continue-on-error`), including `Load the bundle in a real browser`,
  the 360×640 pass and the renderer fixture. Full log grepped: `SEAT-COUNT FAIL` = **0**
  occurrences; `342 passed, 2 skipped`; `smoke OK: seats=4 … reason=complete`;
  `renderer fixture: 7120 text runs measured, 137 crossed an edge, 0 never inside`.
- Restored `tests/test_server.py` as it stood before commit `76caaf0`
  (`git show 3df52bc:tests/test_server.py`) and ran it against head: **17 passed** (F1).
- A socket-backpressure experiment against the real `GameServer` (F2): `run_episode()` never
  returns.
- Re-ran the recorded tuning runoff with the harness and the pre-`0b84154` opponents: the
  recorded numbers reproduce **exactly** (F-none; see Traced).
- A process-age experiment on `PROCESS_STARTED_AT` (F7).

Labels: **observed** = I read or executed it; **inferred** = reasoned from observed code;
**untested** = would need a run I could not do here.

---

## F1 — Eight green tests are still deleted from `tests/test_server.py` at head, with no replacement, and the fixes ledger still denies it

- Where: commit `76caaf0` ("fix(server): r1-F5 — remove the /client/replay pod path"),
  `tests/test_server.py` — `3 insertions, 180 deletions` (183 lines changed). Head's file is
  129 lines and ends at `tests/test_server.py:124-129`.
- Observed (`git show 76caaf0 -- tests/test_server.py`): the commit deletes, wholesale, eight
  test functions. I re-derived the complete "existed in history, absent at head" list
  mechanically (every `def test_*` in every `tests/*.py` blob at every commit vs. head:
  245 names ever, 235 at head). Every one of the eight is absent at head:

  | deleted test | what it covered | equivalent at head? |
  |---|---|---|
  | `test_the_player_failure_payload_is_exactly_two_keys` | the closed `{"message","failed_policy_index"}` written to `COGAME_PLAYER_FAILURE_URI` by a real `GameServer` episode | partial — `tests/test_lobby.py:81-83` asserts the payload for a *connected-but-unregistered* seat; the never-connected path is gone |
  | `test_a_seat_that_never_registers_is_logged_and_reported` | the grf-football scar: the `SEAT <n> HAS NO REGISTER RECORD` **ERROR log** | **no** — `grep -rn "HAS NO REGISTER" tests/` at head finds only the *negative* assertion `tests/test_lobby.py:56` |
  | `test_a_full_episode_writes_results_and_a_replay` | `results.json` + `.replay` actually written through `COGAME_RESULTS_URI`/`COGAME_SAVE_REPLAY_URI`, keys == `RESULTS_KEYS`, `parse()` of the bytes | **no** — `grep -rn "results_uri\|replay_uri" tests/` at head: 0 hits. Artifact writing is untested in-process (only the containerised smoke covers it) |
  | `test_done_is_broadcast_before_the_artifacts_are_written` | the `done` broadcast ordering on `/global` | **no** — `grep -rn '"done"' tests/`: 0 hits |
  | `test_replay_mode_serves_the_recorded_bytes` | `server.make_replay_app` + `GET /replay-data` | **no** — `grep -rn "make_replay_app" tests/`: 0 hits; `server.py:492-503` is untested |
  | `test_the_engine_budget_is_measured_from_process_start` | that `server.py` hands the Engine `PROCESS_STARTED_AT` (the r1-F3 **wiring**) | **no** — `grep -rn "PROCESS_STARTED_AT" tests/`: 0 hits. `tests/test_engine.py:457-486` only proves the Engine *accepts* a caller-supplied instant |
  | `test_the_worst_case_container_time_fits_inside_the_platform_pin` | 660 + 18 + 20 + 20 = 718 ≤ 720 s from the constants themselves | **no** — `grep -rn "720\|PLATFORM_EPISODE_TIMEOUT" tests/`: only `test_manifest.py:30` (`episode_timeout_minutes == 20`) |
  | `test_a_hanging_artifact_write_cannot_outlive_its_budget` | `ARTIFACT_WRITE_BUDGET_SECONDS` actually caps a hanging write | **no** — `grep -rn "ARTIFACT_WRITE_BUDGET" tests/`: 0 hits |

- Observed (executed): I wrote `git show 3df52bc:tests/test_server.py` (the file as it stood
  one commit before the deletion) into the head tree and ran it: **17 passed in 25.5 s**. No
  deleted test needed the `/client/replay` route, and none was made obsolete by the route's
  removal — the deletion was not forced by the change it rode in on.
- Observed: the three tests the commit *added* are grep-over-source assertions inside a
  surviving test (`tests/test_server.py:127-129`: `'add_get("/client/replay' not in source`,
  `"add_static" not in source`, `"VIEWER_DIST" not in source`). `76caaf0`'s own commit message
  says "the new test asserts 404 on all three spellings and that the module registers no static
  mount" — **no HTTP assertion of any kind exists at head**; the route's absence is checked by
  reading `server.py` as text.
- What the ledger says: `r1-fixes.md:41-44` — "No test was weakened, skipped or deleted.
  `git log -p f403fa0..HEAD -- tests/` is 8 new tests, 3 strengthened assertions and 2
  assertions whose *values* moved … no `skip`, `xfail`, widened tolerance or deleted assertion
  anywhere." False on its face for `76caaf0`. `r1-fixes.md:108-111` additionally cites
  `test_the_worst_case_container_time_fits_inside_the_platform_pin` and
  `test_a_hanging_artifact_write_cannot_outlive_its_budget` as the F3 fix's evidence; neither
  exists at head.
- Checklist item: **1** — "no test disabled, skipped, or loosened during this run … a deleted
  assertion, a widened tolerance, a `skip`… added, or a test file removed is a blocking
  finding", verified from `git log -p -- tests/` over the repo's whole history (the repo was
  created this run). This re-verification is my own, not carried forward from the r1 verdict.

## F2 — The per-turn `observe` write has no bound: a seat that stops reading its socket stalls the episode forever (reproduced)

- Where: `server/cogame_halite/engine.py:276-282` — the frame-write loop
  ```python
  for state in reachable:
      frame = self._observation(state.seat, turn, directive, deadline_ms)
      try:
          await state.link.send(frame)
  ```
  and `server/cogame_halite/server.py:133-137` —
  ```python
  async def send(self, message: dict) -> None:
      ws = self.ws
      if ws is None or ws.closed:
          raise ConnectionError(...)
      await ws.send_str(json.dumps(message))
  ```
- Observed (code): the shared deadline (`engine.py:302-303`,
  `asyncio.wait(tasks.keys(), timeout=deadline_ms / 1000.0)`) covers **replies only**. The
  writes happen before it, in a plain `for` loop, under no `wait_for`. `aiohttp` 3.14.3's
  `WebSocketWriter.send_frame` awaits `self.protocol._drain_helper()` once `_output_size >
  _limit` (verified by reading the installed
  `aiohttp/_websocket/writer.py`), and `_drain_helper` awaits a waiter that is only resolved
  when the transport resumes — i.e. when the peer reads. There is no timeout on that path.
- Observed (executed): `/tmp/backpressure_probe.py` — a raw socket completes the websocket
  handshake on `/player?slot=0&token=token-0`, then never reads another byte (receive buffer
  set to 2 KB so the transport pauses promptly). `run_episode()` **never returns**; after 60 s
  I cancelled it and printed the stack:
  ```
  STALLED: run_episode still running after 60 s; last recorded turn 0
  cancelled at:   File "server/cogame_halite/server.py", line 137, in send
      await ws.send_str(json.dumps(message))
    File "aiohttp/_websocket/writer.py", line 121, in send_frame
      await self.protocol._drain_helper()
    File "aiohttp/base_protocol.py", line 140, in _drain_helper
      await waiter
  ```
  The engine had already marked all four seats dead (`MARKED DEAD after 10 consecutive
  substitutions`) — the strike rule does not help, because `engine.py:243-247` deliberately
  keeps sending a dead seat its frame ("A DEAD seat still receives its observe frame"), and it
  is the **send** that blocks. The budget guard and the hard stop are both evaluated at the top
  of `_collect`, which is never reached again.
- With the loopback default receive buffer the same probe finished normally in 8.4 s (400
  turns × ~5–6 KB frames ≈ 2.4 MB fits in an autotuned loopback buffer, `tcp_rmem` max 32 MB
  here). Measured frame size: 4 994 B at turn 0, 6 192 B at turn 60. **Inferred**: over a real
  pod-to-pod link with a default ~128 KB receive buffer, a player process that stops reading
  while holding its socket open (SIGSTOP, OOM-frozen, a blocked event loop) stalls the engine
  after roughly 20 frames.
- The codebase bounds the *other* broadcast on the same object:
  `server.py:423-424` and `:428-429` both use `await asyncio.wait_for(ws.send_str(message), 5.0)`
  in `_broadcast_done`. The per-turn seat write does not.
- What the note says: design.md:325-326 — "**Nothing a player container does can stop the
  clock** — the lobby is bounded by `player_connect_timeout_seconds` (120 s) and the strike rule
  stops a silent seat from consuming the per-turn deadline"; design.md:415 — "**The sim never
  waits**"; `AGENTS.md:52-58` — "Every wait is bounded". Checklist item **5** — "Every wait …
  has an explicit bound … there is no unbounded loop or **blocking read**" (categories: hang,
  timeout).
- Observed: the starter does not have this shape — `cogame-moba`'s
  `server/cogame_moba/server.py:140-157` performs its `ws.send_str` *inside* `get_actions()`,
  which the moba engine awaits under the per-tick deadline, so a stalled write there is bounded
  by the tick timeout.

## F3 — The design note's appendix claims the 718 s worst case is "asserted by a test"; no such test exists at head

- Where: design.md:1160-1167 (appendix item 5, both copies) — "Worst case from process start:
  660 (hard stop) + 18 (one in-flight directive turn) + 20 (artifacts) + 20 (shutdown grace) =
  **718 s**, asserted by a test."
- Observed: the code half is intact — `server/cogame_halite/server.py:49`
  (`PROCESS_STARTED_AT = time.monotonic()`), `:73` (`ARTIFACT_WRITE_BUDGET_SECONDS = 20.0`),
  `:176` (`self.started_at = PROCESS_STARTED_AT`), `:341` (`started_at=self.started_at`),
  `:357-359` (`asyncio.wait_for(self._write_artifacts(outcome), ARTIFACT_WRITE_BUDGET_SECONDS)`),
  `engine.py:105` and `:117` (`elapsed = clock() - started_at`), and the arithmetic is spelled
  out in a comment at `server.py:55-72`. The **test** the sentence names was deleted with the
  other seven (F1): no test at head mentions `PROCESS_STARTED_AT`,
  `ARTIFACT_WRITE_BUDGET_SECONDS`, `PLATFORM_EPISODE_TIMEOUT_MINUTES * 0.6` or the number 720.
- `AGENTS.md:52-58` repeats the arithmetic without claiming a test, so it is accurate as
  written.
- Consequence (observed): checklist item 5's ≤60 % pin is verifiable at head only by reading
  four constants in two files, not from anything the suite runs. The claim in the note is false
  at head; it becomes true again the moment the deleted tests come back.

## F4 — A surviving test lost the one assertion that the shutdown grace is actually awaited

- Where: `tests/test_server.py:124-129` at head:
  ```python
  def test_the_shutdown_grace_is_twenty_seconds():
      assert SHUTDOWN_GRACE_SECONDS >= 20.0
      source = (REPO / "server" / "cogame_halite" / "server.py").read_text()
      assert 'add_get("/client/replay' not in source, "no /client/replay route"
      assert "add_static" not in source, "the pod never serves the viewer bundle"
      assert "VIEWER_DIST" not in source, "the pod never reaches for viewer/dist"
  ```
- Observed: `76caaf0` replaced the line `assert "await asyncio.sleep(SHUTDOWN_GRACE_SECONDS)"
  in source` with the three route greps. The code still does it
  (`server.py:553 await asyncio.sleep(SHUTDOWN_GRACE_SECONDS)`), but nothing at head asserts
  it: the test now named "the shutdown grace is twenty seconds" only checks that the *constant*
  is ≥ 20 and that three route strings are absent. `grep -rn "SHUTDOWN_GRACE" tests/` finds
  only this file.
- What the note says: design.md:652 and design.md:1069-1070 (§Tests 10) — `/global` "keeps
  answering pings for a **20 s shutdown grace** after artifacts are written", `tests/test_server.py`
  covers it. Checklist item 1's "a deleted assertion".

## F5 — One assertion was widened (not deleted) by the r1-F6 fix, in a way the fix compensates for

- Where: `tests/test_manifest.py:126-134` at head (commit `3cdf103`):
  ```python
  assert (REPO / path).is_file(), f"the manifest names {path}, which is missing"
  assert path in json.dumps(MANIFEST) or path in DOC_SOURCES.values()
  ```
  The pre-fix form was `assert path in blob` (a plain containment check against the serialised
  manifest).
- Observed: the disjunction is forced — once the docs are inline text the manifest no longer
  contains the *path* strings `README.md` / `docs/RULES.md` / `docs/REPLAY.md`. The coverage is
  replaced, and strengthened, by the new `test_the_inline_docs_are_the_repo_files_verbatim`
  (`tests/test_manifest.py:101-124`), which asserts each inline value is byte-identical to the
  file — I confirmed it passes and that it is what caught the stale `docs/REPLAY.md` copy after
  `64e8862`. Recorded here because it is literally a widened assertion in a `tests/` hunk of
  this run, which is what checklist item 1's audit recipe looks for; net coverage is higher.

## F6 — `git log -p -- tests/` shows a wholesale deletion and re-add of all 17 test files, from the duplicated phase-20 chains

- Where: commit `c7c0853` ("vendor: initialise the repository") — `git show --numstat` reports
  `0 112 tests/conftest.py`, `0 360 tests/test_engine.py`, … every test file deleted
  (2 923 lines); commit `a3a7781` ("tests: the fidelity gate and the fifteen suites around it")
  re-adds all 17.
- Observed: `c7c0853`'s tree contains **only** `vendor/` (`git ls-tree c7c0853`), and it sits
  on the second of the two parallel phase-20 chains the design note's appendix item 13 records
  (`git log --graph`: `8f7c8a5…6c1bcac` and `c7c0853…9024357`, same nine messages). I compared
  the two chains' `tests/` blobs: `git ls-tree -r f192576 -- tests/` and
  `git ls-tree -r a3a7781 -- tests/` are **identical blob hashes for all 17 files**. Nothing was
  lost; the hunk is a history artefact, not a weakening.
- Reported because item 1's stated audit recipe is `git log -p -- tests/`, and this is the one
  place in the history where that command shows a 2 900-line deletion of test files that is
  *not* a finding.

## F7 — Both budgets run from module-import time, so a process older than the hard stop settles its first episode at turn 0

- Where: `server/cogame_halite/server.py:46-49` (`PROCESS_STARTED_AT = time.monotonic()`, taken
  at import), `:176` (`self.started_at = PROCESS_STARTED_AT`), `engine.py:237`
  (`guard = self.elapsed >= self.config.budget_guard_seconds`) and `engine.py:433-442` (the
  hard stop at a turn boundary).
- Observed (executed): with `server.PROCESS_STARTED_AT` set 700 s in the past and a fresh
  `GameServer(episode_steps=6)`, the very first episode ends before a single turn is played:
  ```
  episode end: reason=deadline end_rule=wall_clock turn=0 scores=[5000, 5000, 5000, 5000]
  episode settled 701.0s after process start (hard stop 660s)
  ```
  and every `fallbacks` counter stays 0 (with the guard on, `engine.py:248-253` makes
  `reachable` empty, so no seat is asked and no substitution is counted — `engine.py:325-338`).
- What the note says: this is the *intended* shape of the r1-F3 fix (appendix item 5,
  design.md:1160-1167: "the lobby is spent inside the guard and the hard stop"), and the note
  models pre-episode time at 20 s with a 120 s bound (design.md:325, :372). So the behaviour is
  in-model **as long as everything before `run_episode()` fits inside 660 s** — the lobby does
  (120 s bound), but the budget now also absorbs container start, the certifier's probe phase
  and any platform delay between process start and the episode, none of which the note's table
  accounts for. Untested here whether any of those can approach the bound.
- Second-order (observed): the same coupling reaches the suite. `tests/conftest.py:24-31` never
  overrides `budget_guard_seconds` (600) or `wall_clock_budget_seconds` (660), so a pytest
  session older than 600 s would take the guard path in every later server/lobby/replay test.
  The full suite is 269 s locally and 250 s in CI, so it does not fire today; on a ~2.5× slower
  runner it would, and it would show up as a red suite (e.g. `tests/test_lobby.py:102`'s
  `fallbacks[3]["disconnected"] > 0`), not a silent pass.

---

## The fourteen r1 fix commits — scope audit (brief item 2)

Read every commit's full diff. "In scope" = only files the finding names, and only changes the
fix requires.

| commit | finding | files touched | verdict |
|---|---|---|---|
| `9a4aeff` | F1 | `sim.py` (one deleted line + a docstring citation), `tests/fidelity_stream.py`, `tests/test_fidelity.py`, `tests/test_sim.py` | in scope; the only code change is deleting `self.players[seat] = [bank, {}, {}]` |
| `a4add14` | F2 | `engine.py` (+2 frame keys +comment), `docs/PROTOCOL.md`, `tests/test_engine.py` | in scope |
| `cc09a10` | F3 | `engine.py`, `server.py`, `AGENTS.md`, `tests/test_engine.py`, `tests/test_server.py` (+70) | in scope (`AGENTS.md` records the new bound) |
| `3df52bc` | F4 | `tools/ci/docker_smoke.sh`, `tests/test_results.py` | in scope |
| `76caaf0` | F5 | `server.py`, `docs/PROTOCOL.md`, `viewer/build_viewer.sh` (a comment), **`tests/test_server.py` −180** | **out of scope: F1 above.** The source changes themselves are minimal and correct |
| `3cdf103` | F6 | `coworld_manifest_template.json`, `tests/test_manifest.py` | in scope (see F5 for the one widened assertion) |
| `13f5314` | F8 | `tests/test_viewer.py` | in scope |
| `123698d` | F9 | `.github/workflows/ci.yml` (a comment), `tests/test_viewer.py` (+23) | in scope |
| `549b25a` | F10 | `engine.py`, `server.py` (audit print), `docs/PROTOCOL.md`, `tests/test_engine.py` | in scope |
| `1620b74` | F11 | `tests/test_fidelity.py` only | in scope |
| `4cdd5e6` | F12 | `engine.py`, `tests/test_engine.py` | in scope |
| `64e8862` | F13 | `static_replay{,_worker}.js` headers, `docs/REPLAY.md`, `tests/test_viewer.py`, **`coworld_manifest_template.json` (2 lines)** | in scope: the manifest touch is the inline `docs/REPLAY.md` copy that `3cdf103`'s byte-identity test forces |
| `0b84154` | F15 | `micro.py` (3 constants + comments), `tools/tune/grid_search.py`, `docs/tuning/…md`, `tests/test_tuning.py`, `tests/test_players.py` | in scope |
| `17fa7b5` | F7/F16 | `docs/plans/2026-08-27-halite-design.md` only | in scope |

**No `skip`, `xfail`, `pytest.mark.skipif` or widened tolerance was added to `tests/` by any
commit in the repo's history** — I grepped every added line in every `tests/` hunk. The two
`skipif`s at head (`requires_upstream`, the ctf-mount comparison, the node/built-bundle guards)
all date from the phase-20 suite or from `e6a4eb9`'s new harness, none from this round. Two
tests were **renamed** and both got stronger:
`test_the_three_documented_adaptations_and_no_others` → `…four…` (`64e8862`, +4 assertions
including an exact `importScripts` call match) and
`test_turn_zero_defaults_are_the_design_note_table` → `…tuned_baseline_table` (`0b84154`, same
assertion with the tuned values plus `micro.Directive() == d`).

## Traced and consistent

**The r1 fixes, spot-checked at head (brief item 3)**

- **F1 elimination fidelity.** `server/cogame_halite/sim.py:294-330` — `_eliminate` sets
  `self.eliminated[seat]`, appends the event, and **does not** clear `self.players[seat]`; the
  upstream citation is inline. `tests/fidelity_stream.py:99-174`
  (`elimination_stream_step`, `VICTIM_SEAT`/`RAIDER_SEAT`) and `tests/test_fidelity.py:61`
  (`ELIMINATION_SEEDS = (42, 2718, 999983)`), `:189-250` compare 3 seeds × 399 turns against a
  real upstream install, assert the victim is DONE with a standing yard at the elimination turn
  and that the abandoned yard is later razed. `tests/test_fidelity.py:294-298` extends the
  floor test to `len(ELIMINATION_SEEDS) >= 3`. `tests/test_sim.py:351-375` pins the same rule
  without upstream. **I ran the whole fidelity gate locally against
  `kaggle-environments==1.32.7`: green.**
- **F2 wire frame.** `engine.py:139-148` carries `"step": obs["step"]` and
  `"remainingOverageTime": obs["remainingOverageTime"]`;
  `tests/test_engine.py:422-455` (`test_a_kaggle_bots_board_builds_from_the_wire_frame_unchanged`)
  round-trips real frames through JSON and builds the **vendored** `Board` from them.
  `docs/PROTOCOL.md:56-79` documents both keys and the `turn == step` identity.
- **F3 process-start budget.** Code present and wired (see F3 above for the citations); its
  three evidence tests are gone (F1), the fourth (`tests/test_engine.py:457-486`) survives and
  proves only that the Engine honours a caller-supplied instant.
- **F4 smoke assertions.** `tools/ci/docker_smoke.sh:304-309` carries the literal 23-key
  `RESULTS_KEYS`; `:310-316` fails with `missing=…/extra=…`; `:318-321` length-checks twelve
  per-seat arrays against `seats`; `:327-333` fails on `reason != "complete"` quoting `end_rule`
  and `stop_detail`. `tests/test_results.py:59-83` parses the script's literal list and compares
  it to `results.py::RESULTS_KEYS` and asserts the script *asserts* it. CI log:
  `episode end reason: complete (end_rule=full_time)`.
- **F5 route removal.** `server.py:186-190` registers exactly
  `/healthz /client/global /client/player /global /player`; `:488` and `:497` register
  `/replay-data` + `/healthz` in replay mode. No `add_static`, no `VIEWER_DIST`, no
  `Path` import for it. The only `/client/replay` strings left are prose
  (`server.py:24`, `:468-477`, `docs/PROTOCOL.md`) plus **`client/broadcast_core.js:192-207`**,
  which is the byte-pinned ctf file: its `websocketPathForClientPage` is unreachable here — the
  file exports only `{create: BroadcastCore}` (`:1406`) and the worker calls only
  `self.BroadcastCore.create` (`static_replay_worker.js:100`).
- **F8 chrome pin.** `tests/test_viewer.py:37-57` asserts the two recorded starter digests
  **unconditionally**; `:61-73` keeps the mount comparison (skipped off-mount) and additionally
  asserts the digests are the *starter's*. I re-diffed: `client/chrome_common.js`
  (`7ace7287…`) and `client/broadcast_core.js` (`172c4680…`) are byte-identical to
  `/workspace/starters/coworld-ctf/client/*`.
- **F10 over-cap counting.** `engine.py:61-65` (`dropped_over_cap: int = 0`), `:180-199` (sort
  by ascending uid, count the overflow, log the first occurrence per seat), `server.py:383-389`
  (the end-of-episode audit block). `tests/test_engine.py:318-346` asserts the exact count, the
  log line, that seat 1's counter stays 0 and that **no `fallbacks` cause moved**. Consistent
  with appendix item 8 (`results.fallbacks` stays closed to the five wire causes).
- **F11 per-turn status/reward.** `tests/test_fidelity.py:163-185` derives our status
  (ACTIVE / DONE, plus core's last-step rule) and reward (bank, or
  `eliminated - episodeSteps - 1`) for every seat at every turn and compares upstream's arrays;
  it runs for **both** streams. The end-only block it replaced was re-expressed as two
  assertions at `:198-199`, so nothing was dropped.
- **F12 dead-seat report.** `engine.py:540-563` — one write, `failed_policy_index` = lowest dead
  seat, message names every dead seat, `reported_dead` guard; `tests/test_engine.py:199-221`.
- **F13 fourth adaptation.** `static_replay.js:6-24` header, `static_replay_worker.js:5-21` at
  the call site, `docs/REPLAY.md`, appendix item 7; `tests/test_viewer.py:106-116` pins the
  `importScripts` **call** to exactly `('./broadcast_core.js', './halite_replay.js')`.
- **F15 tuning harness — reproduced.** `tools/tune/grid_search.py` (48-combination grid over
  `SEEDS`, 16-seed out-of-sample `RUNOFF_SEEDS`, seat 0 = candidate, seats 1-3 = shipped
  baselines, real 400-turn `HaliteSim` episodes through the shipped `micro.compile_turn`);
  `micro.py:41-45` ships `tidewalker` 200/300/200 and `:71` `corsair` 200/300/300;
  `tests/test_tuning.py:48-89` ties the shipped constants to the record's `## Chosen` block,
  asserts the runoff seeds are disjoint from the grid seeds, and re-runs a miniature sweep.
  **I re-ran the recorded runoff with the pre-`0b84154` opponents and reproduced the doc's rows
  exactly**: tidewalker `200/300/200` → `wins 7/16 mean 1681 margin -909`
  (docs/tuning/2026-08-28-micro-grid.md:75), tidewalker `100/500/300` → `0/16, 171, -5742`
  (`:80`), corsair `200/300/300` → `10/16, 11074, +7470` (`:88`). The record is genuine and
  reproducible.
- **Design-note appendix.** Present in both copies at line 1130, thirteen items, sha256 equal
  (`fc883e34…c6c3`). Items 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13 all check out against head; item
  5's "asserted by a test" does not (F3); item 3 (`COGAME_HOST`/`COGAME_PORT`) matches
  `server.py:508-509` and `docs/PROTOCOL.md:11`.

**Checklist properties re-verified independently at head**

- **Item 1 (CI).** Run 33138420080, headSha `17fa7b5e…`, `success`, all three jobs, all steps
  ran. The "no test loosened" half is F1.
- **Item 2 (re-derivation).** `tests/test_replay.py:147-224` — `test_rederivation_full_time`,
  `…_last_fleet`, `…_wall_clock`, `…_fault` each replay `seed` + recorded per-turn `orders` on a
  fresh `HaliteSim` and assert **every** recorded `hash`; `replay.py:71-72` refuses to serialise
  without a `stop` record and `:65-68` applies it through the same constructor on record and
  re-derive. The viewer draws that same recorded per-turn state
  (`replay-viewer/halite_replay.nim`, page `render()`).
- **Item 3 (static viewer).** Manifest `game.replay_viewer = {"bundle": "static-replay-viewer"}`
  under `game`; `tools/build_replay_viewer.sh` committed `100755` (git index mode);
  no `/client/replay` pod path (above).
- **Item 4 (both name spaces).** `engine.py:134-135` and `server.py:228-241` write aliases only;
  real names live in `results.names`, the replay header and the page's `realName()`;
  `tests/test_privacy.py` enforces both directions.
- **Item 5 (waits).** micro 400 ms / directive 18 000 ms (`defaults.py`, applied at
  `engine.py:230-232`); one shared `asyncio.wait(timeout=…)` per turn (`:302-303`); spacing floor
  measured from when the previous batch opened (`:259-270`); lobby `wait_for`
  (`server.py:308`); guard 600 s (`engine.py:237`); hard stop 660 s at a turn boundary
  (`:433-442`); artifacts capped 20 s (`server.py:357`); grace 20 s (`:553`); artifact writes
  3 × 30 s (`uris.py:29-31`); `_broadcast_done` sends bounded at 5 s (`server.py:423-429`).
  The exception is F2.
- **Item 6 (`num_agents`).** 4 inside `game_config` of `standard`/`sprint`/`richfields` and
  inside `certification.game_config`; variant keys are exactly `{id,name,description,game_config}`;
  `len(certification.players) == len(certification.game_config.players) == 4`; `SMOKE_SEATS: "4"`
  (`ci.yml:102`); all four invariants in `docker_smoke.sh` with `SEAT-COUNT FAIL:` prefixes;
  **0 occurrences in the full CI log**.
- **Item 7 (baseline).** All-scripted 120-turn episode ends `complete`
  (`tests/test_replay.py:48-62`) and the containerised smoke ends
  `complete full_time [295, 978, 552, 789]`; legality over 200 random boards × both baselines
  (`tests/test_micro.py`); tuned by the harness above.
- **Items 8, 9 (LLM ladder, rune truncation).** `players/llm.py:149-182` balanced-brace
  extraction, one retry (12 s → 5 s), `will retry` vs `falling back`; every cap routed through
  `defaults.truncate_runes` (`events.py:59`, `:71`, `results.py:155`, `server.py:281`,
  `llm.py:115`, `:218`, `halite_player.py:41`, `:76`).
- **Item 10 (manifest).** `game.docs.readme.type == "text"`, both pages `content.type == "text"`,
  each byte-identical to its repo file (`tests/test_manifest.py:101-124`); `game.protocols`
  carries both `player` and `global` as `{"type":"uri"}` objects.
- **Item 12 (scaffold).** Placeholder gate `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five
  files exits 1 (no matches); `docker_smoke.sh` and `tools/build_replay_viewer.sh` both `100755`;
  `policies.json` has two `PLAYER_PROMPT` champions (both `USE_BEDROCK`) + two scripted fillers
  with `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` on champion #2.
- **Item 13 (viewer executes).** `wasm-viewer needs: docker-smoke` (`ci.yml:148`); the browser
  step logged `{"loaded":true,"ms":287,…}` with the soak advancing to `TURN 97 / 119`;
  `config.nims` has **no** `MODULARIZE`/`EXPORT_NAME` and the worker boots on
  `Module.onRuntimeInitialized` (`static_replay_worker.js:206`) — the matched ctf pair, verified
  by diffing both against the starter; the replay records no lobby frames, so playback opens at
  the game start structurally.
- **Item 14 (chrome provenance).** Full `diff` of `client/replay_broadcast.html` against ctf's
  page: above the `HALITE additions to the inherited coworld-ctf chrome` banner (line 1001)
  there is exactly **one** added line — the `<title>` at line 6 — and every other hunk is a pure
  deletion of the fpv/lockerroom/viewpanel/minimap blocks the note lists. `#endcard` is
  byte-identical to ctf's including `bottom: var(--band, 0px)` (`:710-731`), shown via
  `#endcard.on` (`:732`), dismissed by `seek()` (`:1666-1669`); `relayout()` sets
  `--band`/`--topband`/`--hudscale` on `documentElement`; the four "removed" ids survive as
  `display:none` stubs, pinned by `tests/test_viewer.py:150-170` and recorded as appendix item 1.
- **Item 15 (drawn strings).** No `fillText`/`strokeText` in any shipped viewer file, asserted
  at `tests/test_viewer.py:429-449`; the renderer fixture is the gate and `ci.yml:308-320` fails
  on `total < 12` or `never_inside > 0`; CI: `7120 / 137 / 0`.
- **Parallel batch.** `engine.py:273-291` writes every frame before any await; `:296-304` is one
  `asyncio.wait` with one timeout; `tests/test_engine.py` has both the trace test and the static
  scan.

## Could not determine

- **Whether F2 is reachable with the shipped player image in production.** The stall is proved
  against the real server with a peer that never reads; whether a `players/halite_player.py`
  container can enter that state (rather than closing its socket) needs a hosted run or a
  fault-injection episode — e.g. `SIGSTOP` the player container mid-episode and watch whether
  `results.json` is ever written. The code path itself is unbounded either way.
- **How much pre-episode time a hosted run actually spends before `run_episode()` (F7).**
  Settling it needs one hosted episode timed from container start to the first `observe`.
- **Whether the 137 `outside` text draws in the renderer fixture are real clipping.** Unchanged
  from r1: the gated number `never_inside` is 0 in all three passes, `outside` is
  reported-only per item 15's own rule, and the wrapped-leaf union-box mechanism is documented in
  the fixture header. Still needs a browser (none in this sandbox).

---

Summary: 7 findings — 1 confirmed checklist item-1 violation still open at head (F1: eight
green tests deleted, no replacement, ledger denies it), 1 new reproduced unbounded blocking
write in the per-turn batch (F2, checklist item 5 / hang), and 5 note-vs-code or
test-integrity observations (F3-F7); CI is green at the reviewed sha, the local suite passes
343/1-skipped with the real fidelity gate, and the other thirteen r1 fix commits are in scope
and hold at head.
