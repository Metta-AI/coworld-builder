# r2 fixes — 2026-08-27-halite (`Metta-AI/cogame-halite`)

Head: `cb6dd64cb2c09be25e6b1dc47896d4e7bba87c8b` (was `17fa7b5ee41f0aa74c9e165fd51bba558736928e`)
CI: https://github.com/Metta-AI/cogame-halite/actions/runs/33143385643 — **success**
(run id `33143385643`, `ci.yml`, event `push`, branch `main`, head sha
`cb6dd64cb2c09be25e6b1dc47896d4e7bba87c8b`; jobs `test` / `docker-smoke` / `wasm-viewer` all
`success`). Every step of every job concluded `success` — no skip, no `continue-on-error`
(`gh api /repos/Metta-AI/cogame-halite/actions/runs/33143385643/jobs`: each job's step
conclusions are `["success"]`, the "not success" list is empty for all three).

From that run's logs (fetched per job through
`gh api /repos/.../actions/jobs/<id>/logs`):

- `test` (job `98759022654`): `+ kaggle-environments==1.32.7` installed, then
  **`354 passed, 2 skipped in 285.25s`** — up from `342 passed, 2 skipped` at `17fa7b5`, i.e.
  **+12 tests**, no new skip. The two skips are the same pre-existing pair (the coworld-ctf
  mount comparison, no starter mount on a runner; and the built-bundle node test, whose gate is
  the `wasm-viewer` job).
- `docker-smoke` (job `98759022571`): `episode end reason: complete (end_rule=full_time)`;
  `smoke OK: seats=4 results=1068B replay=384420B reason=complete`;
  `results OK: complete full_time [295, 978, 552, 789]`.
- `wasm-viewer` (job `98759346829`): `{"loaded":true,"ms":292,"clock":"TURN 97 / 119 HAULING",…}`
  in a real browser, all three canvas passes, and the gated renderer fixture
  `renderer fixture: 7124 text runs measured, 136 crossed an edge, 0 never inside`.
- `grep -c "SEAT-COUNT FAIL"` over all three job logs = **0**.

Local re-verification at this head (my own runs, in a fresh clone `/tmp/fix2-halite`):

- `pytest tests/test_server.py tests/test_engine.py` → **49 passed in 57 s**.
- `pytest tests/test_fidelity.py` with the CI-only fidelity group installed
  (`kaggle-environments==1.32.7`) → **15 passed in 110 s** — the differential gate, including the
  three elimination seeds, still bit-exact after the engine change in F2.
- Full suite with the fidelity group → **355 passed, 1 skipped** (the extra pass vs CI is the
  ctf-mount test, which runs in this sandbox; the one skip is the built-bundle node test, no
  emsdk here).

Five commits, one per finding. Pushed to `main` as fast-forwards; nothing was force-pushed and no
commit already on the remote was recreated (`git diff HEAD origin/main` empty in a fresh clone).
Findings are numbered as in `r2-review.md`.

| finding | disposition | commit | checklist item | files |
|---|---|---|---|---|
| F1 eight green tests still deleted | **fixed** | `064d914` | 1 | `tests/test_server.py` (+179) |
| F2 unbounded per-turn `observe` write | **fixed** | `a786a18` | 5 (hang) | `server/cogame_halite/engine.py:286-330`, `tests/test_engine.py`, `tests/test_server.py:368`, `docs/PROTOCOL.md:136` |
| F3 note claims a test that did not exist | **fixed** (test restored + assumptions pinned) | `cb6dd64` | 5, 1 | `tests/test_server.py:297-344`, `server/cogame_halite/server.py:59-77`, `docs/plans/2026-08-27-halite-design.md:1169` |
| F4 deleted shutdown-grace assertion | **fixed** | `5491e0c` | 1 | `tests/test_server.py:124-133` |
| F5 one widened manifest assertion | **refuted** (forced, coverage net higher) | — | 1 | evidence below |
| F6 wholesale test deletion/re-add in history | **refuted** (history artefact; no non-destructive fix) | — | 1 | evidence below |
| F7 budgets anchored at module import | **fixed** (hardened) | `d13af52` | 5 | `server/cogame_halite/server.py:52,188,327`, `tests/test_server.py:245-295`, `AGENTS.md:52-61`, design note appendix item 5 |

No test was weakened, skipped or deleted by these five commits.
`git log -p 17fa7b5..HEAD -- tests/` removes exactly eleven lines, and every one of them is
replaced in the same commit by a stronger form:

- the docstring and two assertions of `test_the_engine_budget_is_measured_from_process_start`
  (renamed to `test_the_engine_budget_opens_before_the_lobby_and_not_at_import`, +3 assertions,
  and joined by a second test that reproduces the F7 repro) — `d13af52`;
- two docstring lines of `test_the_worst_case_container_time_fits_inside_the_platform_pin`
  (+`assert worst == 718` and the two assumption blocks) — `cb6dd64`;
- the static-scan line `assert "asyncio.wait(" in source and "timeout=deadline_ms / 1000.0" in
  source`, replaced by four assertions including
  `asyncio.wait_for(state.link.send(frame), budget)`, `timeout=budget`,
  `budget = deadline_ms / 1000.0` and a per-await rejection of `await state.link.send` —
  `a786a18`.

No `skip`, `xfail`, `skipif` or widened tolerance was added:
`git log -p 17fa7b5..HEAD -- tests/ | grep -cE "^\+.*(skip|xfail)"` = **0**.

---

## F1 — the eight deleted tests are back

**Commit `064d914`** — `fix(tests): r2-F1 — restore the eight tests 76caaf0 deleted`,
`tests/test_server.py` **+179, −0**.

`76caaf0` (the r1-F5 route removal) had deleted eight test functions from `tests/test_server.py`
while removing a route none of them touched. They are restored from
`git show 3df52bc:tests/test_server.py` — the file as it stood one commit before the deletion —
verbatim: `diff` of `3df52bc:tests/test_server.py` against `064d914:tests/test_server.py` is a
**single hunk**, the shutdown-grace assertion that `76caaf0` swapped for the three route greps
(which are kept, and the assertion comes back in F4's commit). Nothing needed adaptation to the
removed route.

Restored, with their line numbers at head:

| test | line at head |
|---|---|
| `test_the_player_failure_payload_is_exactly_two_keys` | `tests/test_server.py:136` |
| `test_a_seat_that_never_registers_is_logged_and_reported` | `:153` |
| `test_a_full_episode_writes_results_and_a_replay` | `:181` |
| `test_done_is_broadcast_before_the_artifacts_are_written` | `:205` |
| `test_replay_mode_serves_the_recorded_bytes` | `:230` |
| `test_the_engine_budget_is_measured_from_process_start` → `test_the_engine_budget_opens_before_the_lobby_and_not_at_import` (renamed by F7, +3 assertions, +1 new test) | `:245`, `:280` |
| `test_the_worst_case_container_time_fits_inside_the_platform_pin` | `:297` |
| `test_a_hanging_artifact_write_cannot_outlive_its_budget` | `:347` |

**Evidence.** `pytest tests/test_server.py` at head: **19 passed** (17 restored/surviving + F2's
and F7's new ones); the whole file, and the whole suite, green in CI run `33143385643`
(`354 passed`, +12 over the reviewed sha). The three greps `76caaf0` added are still there
(`tests/test_server.py:130-133`). Checklist item **1**.

## F2 — the per-turn `observe` write is bounded by the turn's own deadline

**Commit `a786a18`** — `fix(engine): r2-F2 — the per-turn observe write is bounded by the turn
deadline`.

**What it did.** `engine.py` wrote each seat's frame with a bare `await state.link.send(frame)`,
and `WsSeat.send` is a bare `await ws.send_str(...)`. A peer that holds its socket open but stops
reading it applies flow control back to aiohttp's `WebSocketWriter.send_frame`, which awaits
`protocol._drain_helper()` — a waiter resolved only when the peer reads, with no timeout on that
path. The episode parks there forever: the strike rule cannot help (a dead seat is deliberately
still *sent* its frame) and the budget guard and hard stop are only evaluated at the top of
`_collect`, which is never reached again.

**What it does now** (`server/cogame_halite/engine.py:286-330`):

```python
budget = deadline_ms / 1000.0
blocked_write = False
for state in reachable:
    frame = self._observation(...)
    try:
        await asyncio.wait_for(state.link.send(frame), budget)
```

The writes share **one** budget with the replies — the turn's own `deadlineMs`, which is also the
`asyncio.wait` timeout at `:346` (`timeout=budget`). On timeout the offending seat's link is
dropped (`state.link = None`), it is substituted as `disconnected` with the log line
`SEAT <n> (<alias>) STOPPED READING its socket on turn <t>; the write was cut off at <d>ms…`, and
`budget` drops to 0 so the rest of the batch is not asked twice for the same turn: seats the block
deprived of their window are substituted `host_error` (nothing is wrong with *their* peers) and
keep their links. The closed five-cause `fallbacks` key set is unchanged, and the worst a blocked
socket can add to a turn is **one** deadline, which is the number the 718 ≤ 720 s pin is computed
from (F3).

**Evidence.** Three new tests, and I verified all three are load-bearing by reverting only the
bound (`await asyncio.wait_for(state.link.send(frame), budget)` → `await state.link.send(frame)`)
in a scratch worktree at head:

```
FAILED tests/test_engine.py::test_no_await_on_player_input_escapes_a_deadline
FAILED tests/test_engine.py::test_a_seat_that_stops_reading_its_socket_cannot_stall_the_batch
FAILED tests/test_engine.py::test_a_blocked_write_costs_the_batch_one_deadline_not_two
3 failed, 27 deselected in 60.27s        # the two behavioural ones fail as TimeoutError:
                                         # the engine never returns, exactly as the review reported
```

At head the same three pass, plus `tests/test_server.py:368`
`test_a_player_that_stops_reading_its_socket_cannot_stall_run_episode`, which drives a **real**
websocket whose `send_str` never drains through `run_episode()` and asserts the episode settles
`complete`, `fallbacks[0]["disconnected"] > 0`, `results.json` written, and the whole call under
20 s. `test_a_blocked_write_costs_the_batch_one_deadline_not_two` asserts the batch spends < 0.45 s
with a 0.3 s deadline — one deadline, not two. `docs/PROTOCOL.md:136-143` and the engine module
docstring now say the write shares the deadline. Checklist item **5** (hang).

## F3 — the 718 s worst case is asserted again, and the two assumptions under it with it

**Commit `cb6dd64`** — `fix(tests): r2-F3 — the 718 s worst case is asserted, and its assumptions
with it`.

The note's appendix item 5 claimed the sum was "asserted by a test"; that test was one of the
eight `76caaf0` deleted, so at head the ≤ 60 % pin was verifiable only by reading four constants
in two files. F1 restored it (`tests/test_server.py:297`
`test_the_worst_case_container_time_fits_inside_the_platform_pin`), so the note's claim is true
again — I verified the named test exists, runs and passes, and the note's appendix now names it by
its full node id rather than saying "a test".

This commit then re-checked the arithmetic after F2 and F7 and turned the two things the sum
silently rested on into assertions:

- **the in-flight turn is ONE deadline** — a static cross-check that the engine gives the writes
  and the replies a single `budget` (`budget = deadline_ms / 1000.0`,
  `asyncio.wait_for(state.link.send(frame), budget)`, `timeout=budget`);
- **the directive spacing floor cannot add to it** — it is only slept while the budget guard is
  off, and `guard 600 + spacing 10 + deadline 18 = 628 s` is inside the 660 s hard stop, so a
  spaced turn can never still be open when the stop trips.

plus `assert worst == 718` on the sum itself. The sum is unchanged: F2's bound shares the turn's
deadline rather than taking one of its own, and F7 moved the window's start without changing its
length.

**Evidence.** The test passes at head and in CI; the note's appendix item 5 (`design.md:1169-1181`)
now names the test and both assumptions, and `server.py:59-77`'s arithmetic comment says the same.
The in-repo copy `docs/plans/2026-08-27-halite-design.md` and the run-dir copy
`runs/2026-08-27-halite/design.md` are **byte-identical** after this round's two note edits
(F7's and F3's): sha256 `795ceedb54d73299d2a842040a7efa77a3b4dce4e707cc08a1af3415359e480f`, both
copies (the run-dir copy is re-synced in the coworld-builder commit that carries this file).
Checklist items **5** and **1**.

## F4 — the shutdown grace is asserted as behaviour again, not as a constant

**Commit `5491e0c`** — `fix(tests): r2-F4 — assert the server AWAITS the shutdown grace, not just
the constant`.

`76caaf0` had replaced this test's one behavioural assertion with three route greps, leaving a
test named "the shutdown grace is twenty seconds" that only checked the constant was ≥ 20. The
deleted line is back at `tests/test_server.py:127-129`, with the reason in its message; the route
greps stay (`:130-133`).

**Evidence.** Load-bearing, verified: replacing `await asyncio.sleep(SHUTDOWN_GRACE_SECONDS)` with
`await asyncio.sleep(0.0)` in `server.py` in a scratch worktree gives
`FAILED tests/test_server.py::test_the_shutdown_grace_is_twenty_seconds`
(`tests/test_server.py:127: AssertionError`). Before this commit that mutation kept the suite
green while the certifier's post-episode `/global` ping would have started failing. Checklist item
**1**.

## F5 — refuted: the widening is forced by the fix it rides on, and net coverage went up

No code change. The r2 review already labels it "forced, coverage-net-positive"; the evidence, run
here at head:

- The pre-fix assertion was `assert path in blob` where `blob = json.dumps(MANIFEST)`. At head
  that is **false for `README.md`** — I checked directly:
  ```
  README.md in serialised manifest: False
  docs/RULES.md in serialised manifest: True      # the string appears inside the inline text
  docs/REPLAY.md in serialised manifest: True
  ```
  Once `game.docs` carries the documents as inline text (`readme.type == "text"`, both pages
  `content.type == "text"`), the manifest no longer contains the *path* `README.md` at all. The
  old assertion cannot be kept alongside the r1-F6 fix; the disjunction
  (`… or path in DOC_SOURCES.values()`) is the minimum that survives it, and the assertion that
  the file **exists** (`assert (REPO / path).is_file()`) is untouched.
- The coverage the old form gave is replaced by something strictly stronger in the same commit:
  `tests/test_manifest.py:101-124` `test_the_inline_docs_are_the_repo_files_verbatim` asserts each
  inline value is **byte-identical** to its repo file — which caught the stale `docs/REPLAY.md`
  copy after `64e8862`, something `path in blob` could never have caught.

So the `tests/` hunk is a widened assertion in form, but it is entailed by the code change it
accompanies and the round ends with more coverage of `game.docs`, not less. Checklist item 1 is
not falsified.

## F6 — refuted: a history artefact, and no non-destructive fix exists

No code change is possible. Evidence, re-derived here:

- `c7c0853` ("vendor: initialise the repository") sits on the second of the two duplicated
  phase-20 chains (r1-F14, appendix item 13). Its tree contains only `vendor/`, which is why
  `git log -p -- tests/` shows all 17 test files "deleted" there.
- Nothing was lost: `git ls-tree -r f192576 -- tests/` and `git ls-tree -r a3a7781 -- tests/` are
  **identical blob hashes for all 17 files** — `diff` of the two listings is empty (verified at
  head).
- Removing the artefact means rewriting pushed history (`git push --force`), which the fixer rules
  forbid outright. The duplicates are reachable commits, not refs; there is no non-destructive
  alternative. `git diff` between the two chain heads is empty and the tree at `main` is single
  and coherent.

Recorded, as r1-F14 was, as a `git log` cosmetic: the audit recipe of checklist item 1 shows a
2 900-line deletion that is not a weakening.

## F7 — the budget window opens with the episode, not at module import

**Commit `d13af52`** — `fix(server): r2-F7 — the budget window opens with the episode, not at
import`.

The review left the disposition to my judgement ("in-model per the design note … prefer the
smallest correct change or a reasoned refutation"). I judged a fix warranted rather than a note
sentence, because the observed behaviour is a *silent wrong outcome*, not a slow one: with the
anchor at import, a process older than the 660 s hard stop settles its first episode at
`reason=deadline end_rule=wall_clock turn=0` with every `fallbacks` counter at 0 — no seat is ever
asked, so nothing in `results.json` says why the scores are the opening banks. Container start,
the certifier's probe phase and any scheduling delay between process start and the episode are all
inside that window and none of them is the episode's to spend; the note's table accounts for none
of them.

**The change is one line of behaviour**: `run_episode` takes the anchor at its own top
(`server/cogame_halite/server.py:327`, `self.started_at = time.monotonic()`), **before** the lobby
wait, and hands that to the Engine (`:362`, `started_at=self.started_at`). That keeps the whole
point of r1-F3 — the ≤ 120 s lobby, every turn, the 20 s artifact phase and the 20 s grace are all
inside the guard and the hard stop, so the 718 ≤ 720 s pin is unchanged and still covers
everything externally visible about the episode — while dropping only the part of the window that
was never the episode's. `PROCESS_STARTED_AT` stays (`:52`, `:188`) as the pre-episode default and
is now printed as the container's age in the settle line, which is what a hosted run needs to
answer the review's "could not determine" question about pre-episode time:
`episode settled 12.3s after the episode began (hard stop 660s; this container has been up 41.7s)`.

This also removes the review's second-order concern (F7's last bullet) **without a conftest
override**: because the anchor is now taken per episode, a pytest session older than 600 s can no
longer take the guard path in later server/lobby/replay tests. No test-only shim was needed.

**Evidence.** Two tests, both verified load-bearing — deleting only the anchor line
(`self.started_at = time.monotonic()`) in a scratch worktree at head reproduces the review's
observation exactly and fails both:

```
episode end: reason=deadline end_rule=wall_clock turn=0 scores=[5000, 5000, 5000, 5000] …
episode settled 701.0s after the episode began (hard stop 660s; this container has been up 701.0s)
FAILED tests/test_server.py::test_the_engine_budget_opens_before_the_lobby_and_not_at_import
FAILED tests/test_server.py::test_an_episode_in_an_old_process_still_starts_with_a_full_budget
```

At head, `test_an_episode_in_an_old_process_still_starts_with_a_full_budget`
(`tests/test_server.py:280`) sets `PROCESS_STARTED_AT` 700 s in the past and asserts the episode
plays **all six turns** and ends `complete` / `full_time`;
`test_the_engine_budget_opens_before_the_lobby_and_not_at_import` (`:245`) asserts the Engine gets
the server's anchor, that the anchor is this episode's (not the process's, monkeypatched an hour
back) and that it was taken before the 1 s lobby. `AGENTS.md:52-61` and the design note's appendix
item 5 (both copies, identical bytes) record the anchor. Checklist item **5**.

---

## The r1 judge's blocking finding

The r1 verdict's single blocking item was `76caaf0`'s deletion of the eight tests. It is closed by
`064d914` (F1) plus `5491e0c` (F4) for the assertion the same commit swapped out. Diffing the
pre-deletion file against head, **nine** lines are gone and every one is accounted for by a
stronger replacement in the same commit — nothing is uncovered:

```
$ diff <(git show 3df52bc:tests/test_server.py) <(git show HEAD:tests/test_server.py) | grep '^<'
<     assert "await asyncio.sleep(SHUTDOWN_GRACE_SECONDS)" in source
<   ^ same assertion at head (:127-129), re-added by 5491e0c with a failure message
< async def test_the_engine_budget_is_measured_from_process_start(monkeypatch):
<     the engine exists. A budget that starts when the engine is constructed …   (3 docstring lines)
<     assert captured["started_at"] == server_module.PROCESS_STARTED_AT
<     assert captured["started_at"] < time.monotonic(), "process start is in the past"
<   ^ renamed by d13af52 to …_opens_before_the_lobby_and_not_at_import, 2 assertions → 3
<     (the anchor is the server's, is this episode's, and precedes the lobby), plus a new
<     second test that reproduces the F7 repro end to end
<     process start: the hard stop, one in-flight …   (2 docstring lines of the worst-case test,
<     rewritten by cb6dd64, which adds `assert worst == 718` and the two assumption blocks)
```

and the suite went from `342 passed, 2 skipped` at the reviewed sha to `354 passed, 2 skipped` at
head, in the same CI workflow with the same steps and no new skips.

## NOTED (not fixed)

* The review's "could not determine" items are unchanged by this round and still need a hosted
  run: whether a shipped `players/halite_player.py` container can actually enter the
  stopped-reading state (the code path is now bounded either way), and how much pre-episode time a
  hosted run really spends — the new settle-line container age is the instrumentation for the
  second one.
* `engine.py`'s blocked-write path counts the offending seat `disconnected` and its collateral
  `host_error`. Both are existing members of the closed five-cause `fallbacks` set; a dedicated
  sixth cause (`would_not_drain`) would be more legible but touches the closed 23-key results
  schema in four places, which is a design change, not a fix.
* `tests/test_engine.py`'s static scan is now the guard that no future `await state.link.send` goes
  out unbounded. It is a source grep; a new link method (`send_bytes`, say) would not be covered by
  it.
