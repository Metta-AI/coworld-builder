# r2 fixes — derks-gym

Head: `7c87e98d332223a37103f474ca0a4d7a4f90d92e` (main)
CI: run **33172526475** — https://github.com/Metta-AI/cogame-derks-gym/actions/runs/33172526475 —
conclusion **`success`**, `headSha 7c87e98d332223a37103f474ca0a4d7a4f90d92e`.
Jobs: `test` ✓ (**360 passed**, up from 337; no skipped count reported), `docker-smoke` ✓
(`smoke OK: seats=6 … reason=tick_cap`; `grep -c "SEAT-COUNT FAIL"` over the full run log = **0**),
`wasm-viewer` ✓ (both `Load the bundle in a real browser` and `Assert the derks-gym chrome` ran and
passed), `upload-coworld` ✓ (documented bootstrap warn-and-skip).

Seven commits, `624f1cb..7c87e98`, one per finding (F4 and F5 share one: the review's F5 *is* F4's
vocabulary clause, and the brief scoped them together). No test was deleted, skipped, loosened, or
weakened; every commit is net-additive on `tests/`.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking, item 8) | **fixed** | `6373057` | `players/derk_player.py:168-215`, `tests/test_llm_player.py:90-145`, `docs/plans/…-design.md:322-330` |
| F2 | fixed | `6a43ba1` | `players/client.py:189-215,239-291`, `tests/test_players.py:382-436` |
| F3 | fixed | `636e747` | `players/derk_player.py:44-52,239-260`, `tests/test_llm_player.py:213-271` |
| F4 | fixed (documentation, in-protocol widening refused) | `3b1f78e` | `docs/DRAFT.md:161-200`, `docs/PROTOCOL.md:93-106`, `players/derk_player.py:57-66,308-316` |
| F5 | fixed (same commit) | `3b1f78e` | `players/derk_player.py:308-372`, `tests/test_llm_player.py:296-372` |
| F6 | fixed | `8b1fa2a` | `tests/test_llm_player.py:276-294` |
| F7 | fixed | `eb077ee` | `tools/ci/derk_viewer_checks.mjs:394-464`, `.github/workflows/ci.yml:280-281` |
| F8 | fixed (in-repo doc copy); past commit message: no change, by policy | `7c87e98` | `docs/plans/…-design.md:703-711` |

---

## F1 — `legal_picks` rejected prose-wrapped JSON (BLOCKING; checklist item **8**; = r1 verdict B1)

**Was:** `legal_picks` stripped one code fence and then required the whole remainder to be a single
JSON document (`json.loads(strip_one_fence(text))`). `Here is my draft: {…}` — an otherwise legal
draft — returned `None`, was scored as a failed attempt, burned the single retry, and on a second
prose-wrapped reply ended at the scripted fallback while the server recorded `fallback: false`.

**Is:** `first_json_object(text)` scans for candidate `{` positions and lets
`json.JSONDecoder().raw_decode` parse one value at each, so nesting, quoted strings and escapes are
the JSON parser's problem (not a brace counter's) and trailing prose is simply ignored.
`legal_picks` now runs `first_json_object(strip_one_fence(text))`; the legality check after it is
byte-for-byte the old one. Two behaviours are chosen and documented in the function's docstring and
pinned by tests: **two objects in one reply → the first one that parses wins** (never a merge), and
**an object inside an array (`[{…}]`) is accepted** (it is found at its own `{`). The fence
tolerance is kept as the cheap normalisation before the scan.

**Evidence:** `tests/test_llm_player.py` — a 6-case parametrisation covering exactly the reviewer's
rejected table rows (prose before, prose after, prose both sides, prose+fence, fence+trailing
prose, object-in-array) asserting the full picks dict; `…two_objects_in_one_reply_the_first…`;
`…not_confused_by_braces_inside_a_string` (a note containing `}` and `{` survives intact);
`first_json_object` returns `None` for `"sure! here you go"`, `"{broken"`, `'["arm_cleaver"]'`. The
seven pre-existing rejects in `test_legal_picks_rejects` were **not touched** and still reject.
Garbage → retry → scripted fallback is pinned by the pre-existing
`test_two_failures_fall_back_to_the_scripted_rule` and, with the exact reason token, by F5's
`test_every_fallback_logs_its_own_reason[parse]`. CI run 33172526475 `test` job green.

The in-repo design-note copy's contrary sentence ("the reply must be exactly one JSON object")
carries an editor's note in the same commit recording that the code is now tolerant and why.

## F2 — a slow draft lost the socket to the ws heartbeat

**Was:** `_play_connection` awaited `_answer_draft` inline inside `async for msg in ws`. aiohttp
answers a peer PING only from inside `receive()`, so while `on_draft` ran (LLM path bounded at
2 × 20 s) the client could not PONG; the server's `PLAYER_WS_HEARTBEAT_SECONDS = 20.0` closed the
socket at ping + ping/2 ≈ 30 s, the drafted reply was lost and the seat degraded to
`disconnected` + the neutral loadout — bounded, but it silently defeats the champion's draft.

**Is:** the draft decision is started as its own task (`asyncio.create_task`) and the read loop
keeps going, so ping/pong keeps flowing; the task sends `{"phase":"draft","picks":[…]}` when the
decision resolves. A send onto a socket that went away is logged, not raised (a draft failure must
never end the episode); a decision still in flight when the connection ends is cancelled and
awaited in the `finally`. A second `draft` message is ignored (`draft_task is None` guard), matching
`docs/PROTOCOL.md`. **No bound changed** — the server's 45 s draft deadline stays authoritative, and
concurrent `send_str` is safe here (aiohttp 3.14.3 writes non-compressed frames synchronously in
`WebSocketWriter.send_frame`, no await points, so frames cannot interleave).

**Evidence:** `tests/test_players.py::test_a_slow_draft_keeps_answering_the_ws_heartbeat` — the
reviewer's probe as a repo test at scaled timings (server `web.WebSocketResponse(heartbeat=0.4)`, a
1.2 s `on_draft`, i.e. block > ping × 1.5): asserts the draft reply arrived with the exact picks,
that the client never saw a non-TEXT frame (the socket was not closed on us), that a tick was still
played afterwards, and that the done result came back — with `max_connect_attempts=1` so a
reconnect cannot paper over a regression. **Verified failing before the fix**: `PlayerError: giving
up after 1 consecutive failed connection attempts: connection closed before the done message`.

## F3 — the player ignored `deadline_ms` under the 5 s certification deadline

**Was:** `_prompt_payload` stripped `deadline_ms` and nothing else read it, so the keyed drafter
seated in `certification` (`draft_deadline_ms: 5000`) could spend 2 × 20 s: the server resolves that
seat at 5 s (neutral, `fallback_cause: "timeout"`) and Phase C starts while the player is still
inside `on_draft`.

**Is:** `call_timeout(observation, elapsed)` returns
`min(CALL_TIMEOUT_SECONDS, deadline_ms/1000 − DEADLINE_SAFETY_SECONDS − elapsed)`, or `None` when
less than `MIN_CALL_SECONDS` (1.0 s) is left. Under a 5 s deadline that is **one ~3.5 s call** and
then the scripted rule; under the default 45 s deadline it is 20 + 20 s exactly as before
(43.5 s of budget). An observation with no usable `deadline_ms` keeps the full 20 s. A deadline too
short for any call at all skips the LLM entirely and logs `reason=no_time` — the one addition to the
fallback vocabulary the brief listed (documented and tested with the other five; see F5).

**Evidence:** `test_call_timeout_is_capped_by_the_servers_draft_deadline` (45 000 → 20.0; absent →
20.0; non-numeric → 20.0; 5000 → 3.5; 5000 with 3.4 s elapsed → `None`; the 1000 ms schema minimum
→ `None`; and `2 × 20 + 1.5 ≤ 45`), the end-to-end
`test_under_the_certification_deadline_one_short_call_then_scripted` (`deadline_ms=5000`, hanging
transport: exactly **one** request body, returns `forge_picks`, elapsed < 5.0 s, stderr
`reason=timeout`), `test_a_deadline_too_short_for_any_call_skips_the_llm` (zero bodies,
`reason=no_time`), and `test_the_default_deadline_leaves_both_attempts_intact` (two bodies).

## F4 — the player-side fallback is only in stderr

Disposition: **fixed as documentation + an exact, tested log vocabulary** — the reply schema was
*not* widened. Considered and rejected: a conventional prefix inside `note` (the one free-text
field) would be player-controlled data smuggling a control channel into the replay, and it would
put a machine marker into the string the viewer renders and the 120-rune cap governs. Recorded here
as the alternative I chose against, per the brief.

**What changed:** `docs/DRAFT.md` gains §"Two kinds of fallback (and where each one is counted)",
which states in the doc itself that (a) `fallback`, `fallback_cause` and `results.draft_fallbacks`
mean *server-side* neutral substitution and count exactly that; (b) a champion whose model fails
sends its scripted rule's **legal** pick, so the server necessarily records `fallback: false`; (c)
the durable record of an LLM→scripted fallback is the player's stderr line
`draft_fallback=scripted reason=<reason> picks={…}`, with the closed reason table; (d) **phase 60
counts LLM usage from the player logs, not from `results.draft_fallbacks`**. `docs/PROTOCOL.md`'s
draft-turn section says the reply schema is closed and points at that section. The line itself is
now emitted from exactly one place (`PromptDraftPolicy._scripted_fallback`, which asserts the token
is in `FALLBACK_REASONS`), so it has one shape.

**Evidence:** `test_the_fallback_vocabulary_is_closed_and_documented` asserts the tuple's exact
contents, that every token appears in `docs/DRAFT.md`, and that the page names both
`draft_fallback=scripted` and `results.draft_fallbacks` — the doc cannot drift from the code
silently. Satisfies item **8**'s "the fallback is recorded so phase 60 can count it" by naming the
source phase 60 reads (the "Could not determine" the reviewer left open).

## F5 — the log vocabulary was wider than the note's and mislabelled a prose failure

**Was:** `reason` could be `transport:IOError` (an open-ended token), the no-key line carried the
marker inside a parenthetical, and `reason = "parse" if "{" not in text else "illegal"` labelled any
reply containing a `{` as an illegal *pick* even when nothing parsed.

**Is:** `FALLBACK_REASONS = ("no_key", "no_time", "timeout", "parse", "illegal", "transport")`, a
closed set asserted at the single emit site. `transport` is the token; the exception type and
message are logged on their own line, so nothing is lost. The no-key path prints the informational
line and then the same `draft_fallback=…` grammar as every other cause. `parse` now means "no JSON
object could be extracted", `illegal` means "an object was extracted, an id was not in this seat's
catalog" — the mislabel is gone from both directions.

**Evidence:** `test_every_fallback_logs_its_own_reason` is parametrised over all six reasons, drives
`on_draft` into each, and asserts **exactly one** stderr line starting
`draft_fallback=scripted reason=<that reason> picks=`;
`test_a_broken_object_is_parse_not_illegal` (`"{broken"`, `'{"arm":'` → `parse`);
`test_a_prose_wrapped_legal_reply_never_reaches_the_fallback` (the other half: it is a draft, not a
failure, and logs `attempt=1`).

## F6 — vacuous assertion in `test_missing_api_key_makes_no_call_at_all`

**Was:** a `Transport` was constructed and then not passed to the policy, so
`assert transport.bodies == []` held whatever the code did.

**Is:** the test monkeypatches the real transport (`derk_player._anthropic_call`) with a spy that
records and raises, and asserts the spy was never called **and** that `policy.last_request is None`
(so `_call` never even built a body). The other two assertions (scripted picks, the stderr line) are
untouched.

**Evidence:** non-vacuity verified by disabling the no-key guard locally — the test then fails
(`draft_fallback=scripted reason=transport`, spy entered). Restored before committing; the commit
touches only the test.

## F7 — the worst-case note fixture ran at one viewport

**Was:** `derk_viewer_checks.mjs` built the full-cap-note page at `{360, 640}` only, while the plain
replay is checked at 1280×800 and 360×640; item 15 asks for "several canvas sizes".

**Is:** the worst-case block is a loop over `[{1280,800},{360,640}]` — the same five checks, each
label carrying its size, `summary.worst_case_notes` keyed by size, one screenshot per size (both
added to the `viewer-smoke` artifact list). The failure modes genuinely differ: wide is where a
120-rune unbreakable note has room to push its card sideways, narrow is where it can overflow the
card downward.

**Evidence:** CI run 33172526475, step `Assert the derks-gym chrome` — ten `ok` lines, e.g.
`ok worst case 1280x800: every note is still 120 runes long (6/6)`,
`ok worst case 1280x800: #derk-draft still stops above the transport band (761 <= 807.640625)`,
`ok worst case 360x640: every note is still 120 runes long (6/6)`,
`ok worst case 360x640: … (277 <= 284.609375)`, then `all derks-gym chrome checks passed`.
(The driver stays `derk_viewer_checks.mjs`: this viewer draws no model text on the canvas, so
`viewer_smoke.mjs --strict-text-bounds` measures nothing here — the r1 verdict ruled item 15 pass on
that substance and the review recorded it for continuity, not re-litigation.)

## F8 — doc/commit-message drift

**In-repo design note: fixed.** `docs/plans/2026-08-28-derks-gym-design.md` §Replay format v2 now
lists the six-value `fallback_cause` enum, with a one-line editor's note recording that the planned
seventh value `"malformed"` is unreachable (a frame failing the JSON parse is `wrong_shape`; the
per-tick loop's `malformed` belongs to `NOOP_CAUSES`), that the divergence was resolved in the
code's favour in `450c798`, and where it is cross-checked (`tests/test_manifest.py`,
`tests/test_draft.py`). The run-directory master copy is the coordinator's and was not touched.

**Past commit message `450c798`: no change, deliberately.** Pushed history is not rewritten. The
sentence ("the code, the manifest schema, both docs and AGENTS.md now all say six") overstates a
diff that did not need to touch `docs/DRAFT.md` / `docs/PROTOCOL.md` because both already listed the
six causes; the end state it claims is correct and verified. Recorded in `7c87e98`'s body.

---

## Also changed by these commits (declared, so it is not a surprise in the diff)

- Three editor's notes in the **in-repo** design-note copy, each in the commit that made the note's
  text stale: F1's parsing sentence (`6373057`), the player-side degrade paragraph — reason
  vocabulary, deadline-derived budget, and the heartbeat the original arithmetic omitted
  (`3b1f78e`), and the `fallback_cause` enum (`7c87e98`). The run-directory copy in
  `/workspace/coworld-builder/runs/` was not touched.
- `players/derk_player.py`'s module docstring (F3 commit): the "20 + 20 s fits inside 45 s"
  paragraph now also states the `deadline_ms` cap and that the decision runs off the read loop.
- `.github/workflows/ci.yml` (F7 commit): two lines adding the two worst-case screenshots to the
  `viewer-smoke` artifact list, so the new evidence is retrievable. No job, gate, step or
  dependency changed.

## NOTED (not fixed — outside this round's findings)

- `tests/test_viewer.py:200` `pytest.skip("node not on PATH")` is still the one skip not converted
  to a hard failure under `COGAME_REQUIRE_WASM_BUILD` (r1 verdict's own non-blocking observation).
  It did not fire in run 33172526475 (`360 passed`, no skip count).
- The certification fixture's `draft_deadline_ms: 5000` is unchanged (F3 was fixed on the player
  side, which is where the overrun was). A keyed cert episode now costs that seat ≤ ~3.5 s of LLM
  time instead of up to 40 s, but the fixture still gives a champion less thinking room than the
  variants' 45 s. Changing the fixture is a manifest/design decision, not a fixer's.
- `docker_smoke.sh` still runs keyless, so no CI gate exercises a real LLM call (the reviewer's
  "could not determine" #1). F2's and F3's tests now cover the two mechanisms at scaled timings with
  stubs, which is as far as a sandbox gate can go.

Final: main `7c87e98d332223a37103f474ca0a4d7a4f90d92e`, CI run **33172526475** — `success`.
