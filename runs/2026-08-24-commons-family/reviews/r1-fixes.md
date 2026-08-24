# r1 fixes — commons-family

Repo: `Metta-AI/cogame-commons-family`
Head: `ef8e2556638bc560061984b560d0f30b7bbccc99` (main)
CI: https://github.com/Metta-AI/cogame-commons-family/actions/runs/32773426921 — **success**
(all three jobs: `test` 270 passed, `docker-smoke` `smoke OK: seats=6 results=608B replay=44438B
reason=complete` with zero `SEAT-COUNT FAIL`, `wasm-viewer` bundle `{"loaded":true,"ms":286,…}` and
`canvas text: 2550 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`, plus the new fixture step `canvas text: 7518 drawn, 0 never inside the
canvas (0 draws crossed an edge), 0 ellipsized`).

Range: `5c64904..ef8e255`, 19 commits, one per observation, in observation order (O13 and O14 are
swapped so the renderer fix lands before the fixture that measures it). Test count 232 → 270; no
test was deleted, skipped, loosened or marked. `git log -p -- tests/` over this range shows
exactly two deleted lines, both additive edits: an `import` line reflowed into a parenthesised
import, and the round-record key list in `test_every_round_record_has_the_shape_the_viewer_expands`
replaced by a longer one (`public_effort`, `seat_public_effort` added).

| finding | disposition | commit | files |
|---|---|---|---|
| O1 | fixed | `5f4db0d` | `game/llm.py:350`, `game/server.py:320` |
| O2 | fixed | `c9efc3a` | `game/server.py:372-397` |
| O3 | fixed | `ae4e320` | `game/server.py:90-101`, `:399-411` |
| O4 | fixed (documentation) — the provenance itself is sound | `e94d9ec` | `docs/plans/…-design.md` §Chrome provenance |
| O5 | fixed (documentation) — the provenance itself is sound | `553b208` | `docs/plans/…-design.md` §Chrome provenance |
| O6 | fixed (documentation) | `c36d75c` | `docs/plans/…-design.md` §Viewer table |
| O7 | fixed | `bec5b4d` | `game/engine.py:167,184,456-475`, `replay-viewer/commons_family_replay.nim:136-143` |
| O8 | REFUTED as a bound; documentation corrected + test | `0f353ec` | `tests/test_llm.py:271`, `docs/plans/…-design.md` |
| O9 | REFUTED (working as designed); documentation corrected | `3659273` | `docs/plans/…-design.md` §Degrade |
| O10 | REFUTED (working as designed); measured, documented, pinned | `efc4b8e` | `tests/test_baselines.py:222`, `docs/plans/…-design.md` |
| O11 | fixed | `bb10814` | `tools/tune_baselines.py`, `tests/test_tuning.py`, `game/baselines.py:22-29` |
| O12 | fixed | `3e3ec60` | `coworld_manifest_template.json:482`, `tests/test_manifest.py` |
| O14 | fixed | `7ab0eae` | `client/renderer.js:59-70,156-215,600-640,671-700` |
| O13 | fixed | `fd10089` | `tools/ci/text_fixture/index.html`, `.github/workflows/ci.yml:232-278` |
| O15 | fixed | `cc82556` | `game/modules/harvest.py:75-95`, `game/modules/base.py:57` |
| O16 | fixed | `ae119aa` | `player/player.py:34-49,56-62,83-104` |
| O17 | fixed | `40d7156` | `game/engine.py:38-42,113-118`, `coworld_manifest_template.json` |
| O18 | REFUTED (behaviour identical); documentation corrected | `a81535f` | `docs/plans/…-design.md` step 7 |
| O19 | REFUTED (defined, not lucky); pinned by test | `ef8e255` | `tests/test_modules.py:236`, `game/modules/harvest.py:29-40` |

Nothing is marked fixed without a commit. Both copies of the design note (`docs/plans/2026-08-24-
commons-family-design.md` in the repo and `runs/2026-08-24-commons-family/design.md` here) were
edited identically and are byte-identical to each other; the coworld-builder repo is **not**
committed.

---

## O1 — an unclassified LLM transport exception escaped into `_play_game()`

`AnthropicTransport` re-raises any non-429/529 `HTTPError` and `BedrockTransport` any non-throttle
`ClientError`, and `_decide_seat` caught only the four classified exception types. Anything else
travelled out of `executor.map` → `decide` → `asyncio.to_thread` → `_play_game()`, a task nobody
awaits: the reviewer reproduced no `results.json`, no `replay.json`, and no exit.

Now: `_decide_seat` has a final `except Exception` that logs the traceback (`logger.exception`, so
a rejected credential is still loud) and classifies the failure as `transport`, so that seat plays
its scripted fallback for the round exactly as a classified transport error would. Independently,
`_play_game` is now a guard around `_run_episode()`: any unexpected exception is logged and the
episode still settles, writes both artifacts and exits.

Evidence: `tests/test_llm.py::test_an_unclassified_transport_exception_degrades_the_seat_rather_than_escaping`
(a stub raising `HTTPError 401`, asserting `(None, "transport")` and exactly two calls),
`::test_an_unclassified_exception_in_one_seat_does_not_stop_the_batch`, and end-to-end through the
server's own loop:
`tests/test_episode.py::test_a_transport_that_raises_settles_the_episode_with_fallbacks`
(six prompt seats, every call 401 → `reason == "complete"`, `fallbacks == [3]*6`, every recorded
`src == "fallback:transport"`) and `::test_an_unexpected_failure_in_the_round_loop_still_writes_artifacts`.
**Checklist item 5** (degrade-never-hang).

## O2 — the paused branch skipped the deadline check

`if session.paused: await asyncio.sleep(0.1); continue` never reached the `play_deadline` test,
which sat after `settle_round`. `/admin` carries no token, so a `pause` held the episode until the
platform killed the pod with nothing written. The paused branch now checks the same guard and
settles with `reason: "deadline"`; the deadline event is factored into one `note_deadline()` so
both exits write the identical event. Meadow's `/admin` surface is otherwise untouched.

Evidence: `tests/test_episode.py::test_a_pause_cannot_hold_the_episode_past_the_wall_clock_guard`
— paused before the first round with a 1 s episode budget, wrapped in `asyncio.wait_for(…, 30)`,
asserting `reason == "deadline"` and a `deadline` event in the replay. **Checklist item 5.**

## O3 — `play_deadline` anchored after the connect wait

Anchored inside `_play_game`, the worst case to a settled, scored episode was
`180 (connect) + 5 (grace) + 0.6 × 1200 = 905 s` — 75 % of `episodeTimeoutSeconds`, where the note
contracts for 60 %. `PROCESS_START` is now captured at import and the deadline is
`PROCESS_START + play_budget_fraction × EPISODE_TIMEOUT_SECONDS`, so the connect wait is inside the
budget. The guard is also checked **before** a round instead of after one
(`now + max(round_seconds, min_round_seconds) > play_deadline`), so the artifacts are written
inside the budget rather than up to one `round_seconds` past it; round 0 always plays, so a
deadline episode is still scoreable. The note's arithmetic was rewritten (585 s / 48.8 % typical
worst case, 720 s hard ceiling, linger explicitly outside the settle-and-score budget).

Evidence: `tests/test_episode.py::test_the_play_budget_is_anchored_at_process_start_not_at_the_first_round`
moves `PROCESS_START` 500 s into the past against a 600 s episode timeout and asserts the episode
settles `deadline` after exactly one round; the pre-existing deadline test still passes unchanged.
**Checklist item 5** (timeout).

## O4 — `client/renderer.js` is not "byte-for-byte"

Not a provenance violation, and I did not rewrite the renderer: every starter id, CSS section and
chrome function is present, the scaffolding keeps the starter's names and call graph, eight
functions are byte-identical, and the game block is appended — which is what item 14 asks for.
What was false was the note's sentence. §Chrome provenance now names the scaffolding functions
that are inherited, says plainly that the starter's supply-chain board functions are gone and this
game's four module boards stand in their place (which §Readouts already implied with "bullwhip's
`draw()` retargeted"), and records the three edits nobody had written down: `money` → `score`, the
added `paint()` clamp, and the `String()`/radius hardening in `escapeHtml`/`wrapLines`/`roundRect`.
**Checklist item 14.**

## O5 — `chrome.css`'s third in-place edit

Verified myself: `diff` against `/workspace/starters/cogame-bullwhip/client/chrome.css` is exactly
three hunks (header comment, `#scorebug repeat(4,1fr)` → `repeat(6,1fr)`, the `#endscreen bottom:
var(--band,0px)` pin) plus the banner-marked append — 172 changed lines, all accounted for. The
4→6 column change is forced by six seats and was undocumented. Note corrected; no CSS change.
**Checklist item 14.**

## O6 — the ready bridge is a fifth edit

The edit (waiting on `data-replay-loaded` via a `MutationObserver` instead of a double `rAF`) is
what item 13 asks for and is asserted by `tests/test_viewer_contract.py:122-135`; the note's table
still called the bridge "untouched". The table row now describes the edit and its reason, and
restates what really is untouched. **Checklist item 13.**

## O7 — `public_effort` was recomputed in Nim

The expander switched on the module name and re-derived each seat's maintenance effort from its
recorded decision — a second implementation of `Module.public_effort`. `settle_round` now computes
the per-seat effort once (step 8) and the round record carries `seat_public_effort`; the Nim reads
it. Expand-only: no key removed, no value changed.

Evidence: `tests/test_replay_parse.py::test_the_maintenance_effort_the_viewer_shows_is_recorded_per_seat`
recomputes the module's own `public_effort` from each recorded decision and asserts equality, that
the per-seat values sum to `public_effort`, and that the running totals equal
`results.public_effort`; `tests/test_viewer_contract.py::test_the_wasm_module_reads_the_recorded_effort_instead_of_recomputing_it`
asserts the Nim reads `seat_public_effort` and no longer touches `decision{"clean"}`,
`{"plant"}`, `{"harvest"}` or `{"eat_color"}`. **Checklist item 2.**

## O8 — DISPUTED as a bound; the note's arithmetic was wrong, and is fixed

The count is real (8 requests per seat per round, 48 for six throttled seats) and
`tests/test_llm.py:183-189` already asserted it. It is not unbounded, and no code change was
needed: time is bounded by the round deadline (`min(decision_timeout_seconds, deadline − now)` per
request, sleeps clamped to the same deadline) and rate by the rolling 60 s
`llm_max_requests_per_minute = 120` budget, which is shared by all six seats, drawn on by retries
and ladder steps, and refuses rather than waits. The note's "19.5 s" and "6 requests per round"
now say that.

Evidence: `tests/test_llm.py::test_six_throttled_seats_cannot_outrun_the_rolling_budget` — six
seats, a transport that throttles every call, budget 20: every seat gets an answer
(`timeout`/`rate_budget`) and `decider.requests <= 20`. **Checklist item 5.**

## O9 — REFUTED (working as designed); note corrected

`cause: "disabled"` is deliberate: `LlmDecider.decide` returns it when there are no credentials
(the decider's own docstring listed five causes), the server records it on the `fallback` event and
counts it in `results.fallbacks`, and CI's replay is full of them — which is exactly what item 8
wants for phase 60. The note's four-cause enum was the error. It now lists five and carries a row
for the unclassified-transport case from O1. **Checklist item 8.**

## O10 — REFUTED (working as designed); measured and pinned

The seat offset in `open` rooms is load-bearing, and I measured it rather than arguing: replacing
`ranked[slot % len(ranked)]` with the plain maximum makes six stewards queue on patch 0, kill it
(`dead == [True, False, …]`) and score 126 over 20 rounds, against 240 with every patch alive.
`closed`/`partnership` take the plain maximum, as the note requires, so partners can agree. No code
change; the note now records the rule and the number, and
`tests/test_baselines.py::test_open_room_stewards_spread_across_the_patches_instead_of_queueing`
pins both halves. **Checklist item 7.**

## O11 — no grid harness

`tools/tune_baselines.py` sweeps `CLEAN_POLLUTION_TRIGGER × CLEANUP_STOCK_FLOOR` over a 6×6 grid
and plays each combination through all four modules in three societies (six stewards; the mixed
room; three stewards against three free riders) — 12 episodes per combination, one seed, no
sampling, ~2 s for the whole table. A combination scores `mean(steward scores) + residual_value /
num_agents` summed over those 12 episodes, and is inadmissible if six stewards kill the resource in
any module. `tests/test_tuning.py` runs the same sweep in the `test` job.

The sweep moved a shipped value: **`CLEAN_POLLUTION_TRIGGER` 0.35 → 0.15.** The old guess scores
384.6 against the grid's best 409.3 (−6.0 %); 0.15 scores 405.0 (−1.0 %). The grid's very top
(0.05) makes the steward's clean rule unconditional, i.e. the `cleaner` baseline, whose
distinctness this coworld measures — so the enforced tolerance is 2 % and the shipped value is the
best conditional one. `CLEANUP_STOCK_FLOOR` stays at 30 (0.5 % off the best floor; it is what stops
a steward taking the last apples of a dying orchard). §Scripted baselines documents the harness,
the objective and the retune. **Checklist item 7** ("tuned with a grid harness, not guessed").

## O12 — `game.docs.readme` was a `uri`

Now `{"type":"text","value": <the whole README>}`; the four `pages[]` were already inline text.
`tests/test_manifest.py` is new and asserts the readme is `text` and byte-identical to
`src/coworld/examples/commons_family/README.md`, that every page is `{"id","title","content"}` with
inline text, that `game.protocols` carries both `player` and `global`, that
`replay_viewer == {"bundle":"static-replay-viewer"}`, and that every variant and the certification
fixture seat six. **Checklist item 10.**

## O14 — a full-cap remark was ellipsized

`drawBubble` wrapped into a hard **two** lines at `pitch × 1.5` wide (~86 px in a 360 px frame,
~25 characters of a 140-rune remark) and ellipsized the rest, and nothing reserved room for the
bubble. `sayMetrics()` now measures the server's cap (`chat_max_chars`, 140) in the bubble's own
font, turns it into a line count for one bubble per seat side by side, and returns a band height;
`computeLayout` reserves that band above the cog row **whether or not anyone is speaking**. The
bubble wraps to as many lines as the text needs (no line cap), `wrapLines` breaks an
over-wide word on **rune** boundaries instead of ellipsizing it, and when the band would take more
than 45 % of the frame the font shrinks — never the text.

Evidence, measured with the O13 fixture: against the pre-O14 renderer it fails with
`data-replay-error: cleanup @ 360x640: ellipsized ["apple this round and I…",
"supercalifragilisticexpiali…", "我们必须一起清理这条河否…"] | seat 0's remark was not drawn in
full | …`; against this renderer, 20 phases pass with `canvas text: 7518 drawn, 0 never inside the
canvas, 0 ellipsized` (CI run 32773426921). Statically,
`tests/test_viewer_contract.py::test_the_say_band_is_reserved_and_sized_from_the_servers_rune_cap`.
**Checklist item 15.**

## O13 — no worst-case renderer fixture

`tools/ci/text_fixture/index.html` loads the **real** `client/renderer.js` through
`CommonsRenderer.attachReplay` and hands it a frame built to hurt: a full-cap remark on **every**
seat at once — Latin, one unbroken 140-rune word, CJK, surrogate-pair emoji, a mixed-punctuation
line — over each of the four module boards (including the tallest states: six patches with
holders and a tombstone, three full mushroom rows with `flow[]`) at five canvas sizes
(360×640, 360×400, 480×320, 960×600, 1280×800): 20 phases. It holds the renderer's
`data-replay-loaded` write until every phase has been checked and then sets it; on any failure it
sets `data-replay-error`, which fails the smoke. It asserts **its own strings**: every remark is
still exactly 140 runes when handed to the renderer, every rune of it comes back out of a
`fillText` call, and no drawn string ends in an ellipsis.

`ci.yml`'s `wasm-viewer` job has its own step for it — `node tools/ci/viewer_smoke.mjs --bundle …
--strict-text-bounds`, no `continue-on-error` — with the png and json uploaded as
`text-fixture-smoke`. CI at the head sha: `{"loaded":true,"ms":1539}` and `canvas text: 7518 drawn,
0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
`tests/test_viewer_contract.py::test_the_worst_case_text_fixture_is_shipped_and_driven_by_ci`
asserts the fixture and the step keep existing with the flag. **Checklist item 15.**

## O15 — a passing seat "held" patch 0

`resolve` built `named` from every seat's `decision.patch`, including the all-zero default a pass,
a `no_submission` or a never-connected seat arrives with: in `partnership` an absent seat's partner
could harvest patch 0 alone every round while the pair's other patch could never be held, and in
`closed` a passing seat was recorded as a trespasser. A decision whose `src` is `pass` is now
skipped — it names nothing, cannot trespass and draws no `unheld` event. `Decision`'s default `src`
changed `"pass"` → `""` so only the engine's own pass path (`server.py`, `headless.py`, which set
it explicitly) carries the token and hand-built `Decision`s in the existing tests stay real
decisions.

Evidence: `tests/test_modules.py::test_a_seat_that_never_answered_holds_no_patch` (neither patch of
the pair pays while the partner is absent; both partners answering pays with one demanding 0) and
`::test_a_passing_seat_is_not_a_trespasser_in_a_closed_room`. Note updated.

## O16 — the spectate loop was unbounded

`websockets.connect(url, ping_timeout=None)` plus `while True: await websocket.recv()`. The socket
now carries `ping_interval = 20 s` / `ping_timeout = 30 s`, so a game that died without closing its
socket is noticed, and the loop has a wall-clock deadline (`SPECTATE_TIMEOUT_SECONDS = 1080 s`,
past the game's own worst case of the 720 s play budget plus the 90 s hard-cap linger). Every path
still exits 0.

Evidence: `tests/test_episode.py::test_the_spectate_loop_gives_up_instead_of_waiting_on_a_dead_game`
drives `main()` against a socket that never speaks and asserts it returns and closes.
**Checklist item 5.**

## O17 — `norm_text` had no cap

It is manifest-authored rather than model-authored, but it reaches the system prompt, every seat's
observation and the replay's `config`. It now goes through the same `truncate_runes`
(`NORM_MAX_RUNES = 400`, enforced by a pydantic field validator) and `config_schema.norm_text`
declares `maxLength: 400`.

Evidence: `tests/test_replay_parse.py::test_the_posted_norm_is_rune_truncated_before_it_reaches_the_prompt`
feeds a 1080-rune multi-byte norm, asserts exactly 400 runes survive and that the replay still
decodes as strict UTF-8 with no error handler. **Checklist item 9.**

## O18 — REFUTED (behaviour identical); note corrected

`eaten_total[c] +=` is the last thing `resolve` (step 5) does and `dynamics` (step 7) reads the
updated totals, so the spawn weights are identical to the note's — and
`tests/test_modules.py:330-337` already pins the totals after `resolve`. Moving the accumulator to
match the prose would change nothing but the line it sits on and would separate it from the numbers
it counts. The note now describes the code.

## O19 — REFUTED (defined, not lucky); pinned by test

`owner[p] = patch_deal[p] % num_agents` is a permutation because every shipped variant has
`patch_count == num_agents == 6` (manifest: `num_agents` 6..6, `patch_count` 6 in all six
variants). The modulo is what keeps a hand-edited `game_config` legal rather than merely lucky, and
that is now tested: `tests/test_modules.py::test_patch_ownership_stays_defined_when_the_counts_differ`
plays 3, 6 and 12 patches through `open`/`closed`/`partnership` and asserts every patch has exactly
one owner in range, every allowed set is inside the patch range with no duplicates, the 6/6 case is
a permutation, and a full eight-round episode settles with every decision inside its bounds. A
comment at the deal and a parenthesis in the note say why.

---

## NOTED (not fixed)

Out of scope for this round; recorded rather than changed.

1. **`ci.yml` is no longer byte-identical to the template from `docker-smoke:` to EOF.** The O13
   fixture step and its evidence upload were added to `wasm-viewer` (the job that already installs
   Playwright). The template's own two jobs are otherwise unchanged, and checklist item 12 does not
   require byte-identity — but the reviewer's §3 claim 7 is now "byte-identical except the two
   appended fixture steps".
2. **`harvest`'s `public_effort` for a passing seat is `effort_budget − harvest = 3`**, i.e. a seat
   that never connected is credited with three units of restraint every round. O15 fixed the
   holding semantics only; this is the same "a pass is not a choice" question in the ledger, and
   changing it would move recorded numbers.
3. **The cert fixture is `module: "cleanup"`,** so `docker-smoke` still produces a cleanup replay
   and the bundle smoke never executes `drawPatches`/`drawField`/`drawMushrooms`/`drawFlow`
   (reviewer §4). The O13 fixture now renders all four module boards through the real renderer at
   five sizes, which closes most of that gap, but the *wasm expander* is still only exercised
   against a cleanup replay. A second cert/smoke fixture would settle it.
4. **`/admin` remains unauthenticated** (meadow's surface, kept deliberately). O2 removed the
   consequence that mattered — a pause can no longer hold the episode past its budget.
