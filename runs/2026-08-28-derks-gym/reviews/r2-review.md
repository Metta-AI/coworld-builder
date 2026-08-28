# r2 review — derks-gym

Repo: `Metta-AI/cogame-derks-gym`, read at **main HEAD `624f1cb3717833bebc68edd1ed6702f94ad74fbe`**
(clone `/tmp/cogame-derks-gym-r2`, `git rev-parse HEAD` confirmed).
Range audited for "changes since r1": `70db559..624f1cb` (the eight fix commits; `git diff --stat`
= 12 files, +278 / −50).
Files opened: 26 (`players/derk_player.py`, `players/client.py`, `players/baseline_player.py` head,
`server/cogame_derks_gym/{draft,events,server,catalog}.py`,
`tests/{test_draft,test_llm_player,test_engine,test_viewer,test_manifest,test_fidelity}.py` plus the
diffs of `tests/{test_config,test_loadout,test_server}.py`, `coworld_manifest_template.json`,
`tools/ci/{derk_viewer_checks.mjs,policies.json,docker_smoke.sh}`, `.github/workflows/ci.yml`,
`viewer/{derk_chrome.css,derk_chrome.js}`, `docs/{PORTING,DRAFT,PROTOCOL}.md`, `AGENTS.md`,
`docs/plans/2026-08-28-derks-gym-design.md`) + the full CI log of run 33167936624.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Design note: `/workspace/coworld-builder/runs/2026-08-28-derks-gym/design.md` (byte-identical to the
in-repo `docs/plans/2026-08-28-derks-gym-design.md` — `diff -q` says IDENTICAL).

**Important framing:** HEAD is the *same sha the r1 judge read* (`624f1cb`). `git log` shows no
commit after 624f1cb (2026-08-28 11:38:34Z). So the eight fix commits are the only "changes since
the r1 review" (they landed between the r1 review's sha `70db559` and the r1 verdict), and the r1
verdict's single blocking finding cannot have been addressed yet — it is re-verified independently
below as F1, not carried forward on the verdict's word.

---

## Blocking

### F1 — `legal_picks` accepts only a bare or single-fenced JSON object; prose-wrapped JSON is rejected

- Where: `players/derk_player.py:147-157` (`legal_picks`), `players/derk_player.py:132-144`
  (`strip_one_fence`), pinned by `tests/test_llm_player.py:60-87`.
- Observed (executed, not reasoned): I extracted the real `strip_one_fence` / `legal_picks` source
  from head and ran it against a catalog-shaped observation. Results:

  | reply | result |
  |---|---|
  | `{"arm":…,"tail":…,"misc":…,"note":"hi"}` | accepted |
  | ```` ```json\n{…}\n``` ```` | accepted |
  | ```` ```\n{…}\n``` ```` | accepted |
  | `"\n\n  {…}  \n"` (whitespace only) | accepted |
  | `Here is my draft: {…}` | **None** |
  | `Here you go:\n```json\n{…}\n```` | **None** |
  | `{…}\nHope that helps!` | **None** |
  | `Sure!\n{…}\nDone.` | **None** |
  | ```` ```json\n{…}\n```\nlet me know ```` | **None** |
  | `{…} {…}` (two objects) | **None** |
  | `[{…}]` (object inside an array) | **None** |

  The code path is exactly two lines of tolerance:
  ```python
  try:
      payload = json.loads(strip_one_fence(text))
  except (json.JSONDecodeError, ValueError):
      return None
  ```
  `strip_one_fence` only acts when the *stripped* text `startswith("```")`
  (`derk_player.py:136-137`), so any leading prose defeats the fence tolerance too. Nothing anywhere
  in the tree scans for a balanced `{…}` inside the reply (`grep` for brace-scanning /
  `JSONDecoder.raw_decode` / `re.search(r"\{"`: no hits in `players/`).
- Requirement: checklist item **8** — "Parsing is tolerant (**accepts surrounding prose, extracts the
  JSON object**), retries once on a parse or transport failure, then falls back to the scripted move
  — and the fallback is recorded". The retry, the fallback and the recording are present (see
  "Traced and consistent"); the tolerance clause is the only falsified half. The design note takes
  the opposite position deliberately — "the reply must be exactly one JSON object (a single
  leading/trailing code fence is stripped before parsing — one tolerance, stated, so it is testable)"
  (`design.md:322-324`) — but the checklist, not the note, defines blocking.
- Consequence traced: a prose-wrapped but otherwise legal reply returns `None` at
  `derk_player.py:157`, which is scored as a failed attempt at `derk_player.py:261`, burns the single
  retry, and on a second prose-wrapped reply ends at the scripted fallback
  (`derk_player.py:266-269`). The champion then plays `puffer-forge`'s table instead of the model's
  pick, while the server records `fallback: false` (the reply it received was legal), so the only
  trace is the player's stderr line.
- Note on test coupling (fact, not a fix): no existing test asserts that prose-wrapped *valid* JSON
  is rejected. `tests/test_llm_player.py:77-87` parametrises seven rejects, none of which contains a
  complete legal JSON object (`"sure! here you go"`, `"{broken"`, `'["arm_cleaver"]'`, and four
  objects with illegal/missing ids). An extraction-tolerant parser would still reject all seven.

---

## Non-blocking

### F2 — the champion's draft can block its websocket read loop for up to 40 s against a 30 s server ping/pong close window

- Where: `players/derk_player.py:44` (`CALL_TIMEOUT_SECONDS = 20.0`), `:243-248` (two sequential
  attempts, each `asyncio.wait_for(..., CALL_TIMEOUT_SECONDS)`); `players/client.py:191-207` and
  `:234-256` (`_answer_draft` is awaited **inline inside** `async for msg in ws`);
  `server/cogame_derks_gym/server.py:82-85` (`PLAYER_WS_HEARTBEAT_SECONDS = 20.0`) and `:456`
  (`web.WebSocketResponse(heartbeat=PLAYER_WS_HEARTBEAT_SECONDS)`).
- Observed: while `on_draft` runs, the client is not inside `ws.receive()`, so aiohttp's client-side
  autoping cannot answer a server PING (autoping is handled in `receive()`). The server sends PING
  every 20 s and closes the socket when no PONG arrives within `heartbeat/2` = 10 s.
- Reproduction (isolated, aiohttp **3.14.3** — the version pinned in `pyproject.toml:8` and
  `uv.lock:19-20`): I wrote a 60-line probe with the same shape as the repo's two sides —
  `web.WebSocketResponse(heartbeat=H)`, one `{"phase":"draft"}` send, a client
  `async for msg in ws` that `await asyncio.sleep(BLOCK)` before replying — at scaled timings
  `H = 2.0 s`, `BLOCK = 4.0 s`, deadline 10 s. Result:
  `{"outcome": ["closed", "1006"], "elapsed": 3.0, "client_send":
  "ClientConnectionResetError('Cannot write to closing transport')"}` — the socket was closed by the
  server at exactly `H + H/2`, the reply never arrived, and the client's send raised.
- Inference (labelled): at production timings the close window is 20 + 10 = **~30 s**, while the
  doubly-attempted LLM path is bounded at **2 × 20 = 40 s**. So the retry-then-succeed case — first
  call times out at 20 s, second call answers after >10 s — can lose its answer to the heartbeat
  close rather than to the 45 s draft deadline. The happy path (one call under ~30 s) is unaffected.
- What it does *not* falsify: item **5**. Every wait is still explicitly bounded, nothing hangs, and
  the failure degrades correctly — `Seat.fail_waiter` (`server.py:253-269`) resolves the pending
  draft waiter with `(None, "disconnected")`, the seat takes the neutral loadout, the cause is
  recorded, and `players/client.py:148-179` reconnects on a bounded budget (5 consecutive attempts).
  What it contradicts is the design note's stated rationale: "The 20 s + 20 s worst case fits inside
  the server's 45 s draft deadline, so a doubly-failing champion still submits a legal loadout"
  (`design.md:330-331`) — the arithmetic accounts for the draft deadline but not for the 20 s
  heartbeat the same repo sets. No checklist item names the heartbeat, so this is advisory.

### F3 — the certification fixture seats a keyed LLM champion under a 5 s draft deadline

- Where: `coworld_manifest_template.json:735` (`certification.players[2] = {"player_id":
  "drafter"}`), `:770` (`certification.game_config.draft_deadline_ms = 5000`), `:629-641` (the
  `drafter` runnable carries `PLAYER_PROMPT=derk-drafter-v1` **and**
  `ANTHROPIC_API_KEY_URI=secret://coworld/derks-gym/anthropic_api_key`), against
  `players/derk_player.py:44,243-248` (up to 40 s) and `players/derk_player.py:182-187`
  (`_prompt_payload` strips `deadline_ms`; nothing in `PromptDraftPolicy` reads the observation's
  `deadline_ms`, so the player never adapts its own budget to the server's).
- Observed: in hosted certification the secret is present, so the drafter makes a real call. The
  server resolves that seat at 5 s (`draft.py:290-294` per-seat `wait_for` against the shared
  instant) → neutral loadout, `fallback_cause: "timeout"`, `results.draft_fallbacks[2] = True`, and
  Phase C starts while the player is still inside `on_draft`, not reading its socket. The queued tick
  messages are answered late/never → NOOPs and, at 10 consecutive, the strike rule marks the seat
  dead and force-closes the socket, after which the client reconnects and revives on its first valid
  reply.
- Not covered by any gate: `tools/ci/docker_smoke.sh` runs **without** `ANTHROPIC_API_KEY`, so the
  drafter takes the no-key path (`derk_player.py:237-241`) instantly — CI run 33167936624's smoke log
  shows `picks=['arm_blaster','arm_needler','arm_blaster','arm_blaster','arm_needler','arm_needler']`
  and `noop_ticks == [0]*6`, i.e. the scripted-rule picks, never an LLM call.
- Requirement: no checklist item prescribes the certification episode config; item **6**'s four seat
  invariants and the `SMOKE_SEATS` cross-check all hold (verified below). The design note's own cert
  block is `draft_deadline_ms: 5000` with `baseline × 6` (`design.md:944-953`); commit `70db559`
  (pre-r1-review) changed the seating to include the drafter without changing the deadline. Advisory.

### F4 — an LLM→scripted fallback is recorded only in the player's stderr, never in the replay or results

- Where: `players/derk_player.py:266-269` (`print(f"draft_fallback=scripted reason={reason} …",
  file=sys.stderr)`), `players/derk_player.py:237-241` (the no-key line, which also carries
  `draft_fallback=scripted reason=no_key`); `server/cogame_derks_gym/server.py:761-769`
  (`_draft_fallbacks` = "did the **server** substitute the neutral loadout?"), `draft.py:190-212`
  (`fallback = fallback_cause != "none"`).
- Observed: when the player falls back it still sends a *legal* scripted pick, so the server records
  `fallback: false`, `fallback_cause: "none"`, and `results.draft_fallbacks[seat] = False`. The
  replay header's draft record therefore cannot distinguish "the model answered" from "the model
  failed twice and the scripted table answered". The only durable record is the stderr line, whose
  prefix `draft_fallback=scripted` is stable and greppable in player logs.
- Requirement: item **8**'s "the fallback is recorded so phase 60 can count it". The stderr line is a
  record and the r1 verdict accepted it as satisfying the clause; I record the precise scope so the
  judge can rule on its own read: phase 60 must count from player logs, not from
  `results.draft_fallbacks`.

### F5 — the fallback log vocabulary is wider than the design note's, and mislabels a prose failure

- Where: `players/derk_player.py:250` (`reason = "timeout"`), `:253`
  (`reason = f"transport:{type(exc).__name__}"`), `:261`
  (`reason = "parse" if "{" not in (text or "") else "illegal"`), `:238-240` (`reason=no_key`).
- Observed: the design note pins `draft_fallback=scripted reason=<timeout|parse|illegal>`
  (`design.md:328-330`); the code can also emit `reason=transport:IOError` and `reason=no_key`. And a
  prose-wrapped JSON reply (F1) contains `{`, so it is labelled `illegal` although it failed the
  parse. Log vocabulary only; no schema, replay field or gate reads these strings.

### F6 — `test_missing_api_key_makes_no_call_at_all` contains one vacuous assertion

- Where: `tests/test_llm_player.py:168-177`. A `Transport` is constructed at `:170-171` but the
  policy is built with `transport=None` at `:172-173`, so `assert transport.bodies == []` (`:176`) is
  true regardless of the code under test. The test's other two assertions are real and do exercise
  the no-key path: `picks == forge_picks(obs)` (`:175`) and
  `"ANTHROPIC_API_KEY is not set" in capsys.readouterr().err` (`:177`), which together pin
  `derk_player.py:237-241`. Unchanged since the initial commit `8b7e527` — not a weakening during
  this run.

### F7 — the item-15 worst-case fixture is a bespoke script, not `viewer_smoke.mjs --strict-text-bounds`, and runs at one canvas size

- Where: `.github/workflows/ci.yml:240-252` (step `Load the bundle in a real browser`:
  `node tools/ci/viewer_smoke.mjs … --strict-text-bounds`, on the plain smoke replay) and
  `:258-267` (step `Assert the derks-gym chrome`: `node tools/ci/derk_viewer_checks.mjs --bundle …
  --replay … --timeout 90`, **no** `--strict-text-bounds` — that flag is `viewer_smoke.mjs`'s and
  `derk_viewer_checks.mjs` defines no such option, `parseArgs` at `:58-79`).
  `tools/ci/derk_viewer_checks.mjs:403` creates the worst-case page at `{width: 360, height: 640}`
  only; the plain replay is checked at 1280×800 (`:204`) and 360×640 (`:358`).
- Observed: the fixture is a real gate — `check()` collects failures (`:165-167`) and `main().then`
  exits 1 with a listing (`:464-467`). CI run 33167936624, step `Assert the derks-gym chrome`:
  ```
  ok   worst case: 6 full-cap notes rendered in #derk-draft (got 6)
  ok   worst case: every note is still 120 runes long (6/6)
  ok   worst case: no note is clipped by its card (0 clipped)
  ok   worst case: #derk-draft does not overflow sideways (scrollWidth - clientWidth = 0px; vertical scroll is fine: scrollable=true)
  ok   worst case: #derk-draft still stops above the transport band (277 <= 284.609375)
  all derks-gym chrome checks passed
  ```
  The preceding `viewer_smoke.mjs` step logged `canvas text: 0 drawn, 0 never inside the canvas (0
  draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
- Requirement: item **15**'s literal wording is "renders it at several canvas sizes … and is driven
  by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step". Two literal deviations
  (different driver; one viewport for the worst case) against a substance match (the only
  model-authored string in this lineage is `note`, rendered as DOM `textContent` at
  `viewer/derk_chrome.js:194`, and the anti-shortening guard the item demands is present and green).
  `.derk-card .derk-note { … overflow-wrap: anywhere }` (`viewer/derk_chrome.css:261-265`) is the CSS
  the fixture depends on. The r1 verdict ruled item 15 pass on this evidence; recorded here for
  continuity, not re-litigated.

### F8 — two commit messages describe slightly more than their diffs

- `450c798` ("F9") says "the code, the manifest schema, both docs and AGENTS.md now all say six". The
  diff touches `AGENTS.md`, `coworld_manifest_template.json`, `server/cogame_derks_gym/draft.py`,
  `tests/test_draft.py` only — `docs/DRAFT.md:136-146` and `docs/PROTOCOL.md:93-94` already listed
  the six causes, so no doc change was needed. The end state is consistent; the sentence overstates
  the diff.
- The design note (`design.md:685`, and its identical in-repo copy) still declares the **seven**-value
  `fallback_cause` enum including `"malformed"`. The code and manifest now declare six
  (`draft.py:48-49`, `coworld_manifest_template.json:470-481`), cross-checked by
  `tests/test_manifest.py:100-104` (`enum == set(draft.FALLBACK_CAUSES)`). This is the r1 F9
  divergence resolved in the code's favour, deliberately and with the reasoning recorded in
  `draft.py:42-47`; the note is left as the historical plan. No checklist item covers it.

---

## Traced and consistent

**The eight fix commits — each does what its message says, each ships real assertions.**

- `5adc034` (F1, per-seat resolution under one shared deadline) — `draft.py:290` computes
  `deadline_at = time.monotonic() + cfg.draft_deadline_ms/1000` **once**; `:292-294` is a single
  `asyncio.gather`; `_one_seat` (`:241-259`) awaits `asyncio.wait_for(source.get_draft(observation),
  max(0.0, deadline_at - started))` and returns `(None, "timeout", …)` for that seat alone. No
  `wait_for` wraps the gather any more, so a slow seat cannot cancel finished siblings. Tests:
  `tests/test_draft.py:139-155` asserts the slow seat is `timeout`/`NEUTRAL` **and** all five fast
  seats keep `fallback_cause == "none"`, `fallback is False`, `picks == LEGAL`;
  `:201-214` still asserts six 5 s seats cost one 1 s deadline (`elapsed < 3.0`). Both are real
  assertions on real code paths. No new divergence found: the shared-deadline wall-clock property
  (item 5's basis) is preserved.
- `7a424d7` (F2, per-seat `decision_ms`) — `draft.py:255-259` returns
  `int((time.monotonic() - started) * 1000)` on the timeout branch (the `deadline_ms` parameter was
  removed from `_one_seat`, `:241-243`), and `:266`/`:267` do the same on the exception and normal
  paths. Test `tests/test_draft.py:157-171` asserts `900 <= slow["decision_ms"] < 5000` and
  `< 500` for each fast seat. House records keep `decision_ms: 0` (`draft.py:215-219`, asserted at
  `test_draft.py:89`).
- `6c44f82` (F13, player-side note trim) — `derk_player.py:171-178` slices
  `note[:MAX_NOTE_RUNES]` with `MAX_NOTE_RUNES = 120` (`:50`); Python slices Unicode scalars, so no
  codepoint split. Test `tests/test_llm_player.py:90-109` asserts `MAX_NOTE_RUNES ==
  catalog.MAX_NOTE_RUNES`, that a 3000-emoji note becomes exactly 120 rockets, that the picks
  survive, that the frame is `<= catalog.MAX_DRAFT_FRAME_BYTES`, and that `draft.truncate_note` is a
  no-op on the result. Server-side truncation stays authoritative (`draft.py:76-93`: scalar slice
  plus `Cc`/lone-surrogate stripping), tested with a straddling 4-byte emoji and combining sequences
  (`test_draft.py:218-241`). Both sides of item 9 hold.
- `450c798` (F9, six-value enum) — see F8 for the one wording overstatement; the substantive change
  is correct and reachability is now asserted (`test_draft.py:172-184`, plus `"malformed" in
  engine.NOOP_CAUSES` so the per-tick enum is not confused with the draft's). Every one of the six is
  produced by a case in `tests/test_draft.py` (`timeout` :139, `disconnected` :186, `oversize` and
  `wrong_shape` :106-134 and the websocket cases, `unknown_item` :104-118, `none` :69-90) and by real
  server code (`server.py:214-251` `deliver_raw` decides oversize before the JSON parse; `:253-269`
  `fail_waiter` supplies `disconnected`).
- `04bf732` (F10, event cap) — `events.py:56-73`: the last-resort branch now `return`s instead of
  `del self._events[self._max:]`. Traced the bound: the undroppable kinds are capped by the game (1
  `draft`, 1 `first_blood`, ≤24 `tower` for 24 map towers, ≤2 `ancient`, 1 `end`), and droppable
  `level_spike`/`kill` are still shed oldest-first, so the list cannot grow without bound and the
  `while` loop always terminates (the `for/else` either deletes one element or returns). Test
  `tests/test_engine.py:836-858` stuffs `MAX_EVENTS` towers and asserts `kinds[-1] == "end"`,
  `kinds[-2] == "ancient"`, `kinds[0] == "draft"`, `first_blood` present, `tower` count preserved.
- `a868594` (F11, PORTING.md) — the provenance paragraph is at `docs/PORTING.md:3-7`; the three plan
  references now read `docs/plans/2026-08-28-derks-gym-design.md` (`:57, :68, :91`) and that file
  exists (`ls docs/plans` → one file, exactly that name). No invented `…-implementation.md` remains
  (`:96-97` says the plan was folded into the same document). The page is manifest-published as
  `pages[1]`, so the dead links were shipped docs; they are gone.
- `651ea5d` (F7, docstring) — `tests/test_viewer.py:271-274`; comment-only, the two assertions
  (`header["loadout_digest"] == catalog.loadout_digest()`) are untouched by the diff.
- `624f1cb` (F8, worst-case fixture) — `tools/ci/derk_viewer_checks.mjs:127-151` builds the fixture
  replay from the *real* smoke replay: validates `DERK`/v2, rewrites only the six `source == "seat"`
  records' `note` to `"W".repeat(120)` (no wrap opportunity, widest ASCII glyph), throws unless
  exactly 6 seat records were found, re-emits the 9-byte prefix with the new `header_len` and the
  body verbatim. `:403-450` loads it through the real bundle, pauses, opens the overlay and asserts
  count/full-length/clipping/overflow/band. See F7 for the two literal deviations from item 15's
  wording. No entrance animation exists to "play through" (`grep animation|@keyframes
  viewer/derk_chrome.css` → one `transition: width .2s` on the Ancient bar, `:66`).

**The LLM decision path (fresh trace).**

- Request construction: `derk_player.py:271-284` — `model` = `MODEL` = `"claude-sonnet-4-5"` (`:42`),
  `max_tokens` = 400 (`:43`), `system` = the prompt, `messages` = one user turn. `temperature: 0` is
  set **only** on the retry (`:279-280`), and the reminder line `"Reply with the JSON object only."`
  (`:45`) is appended to the *system* prompt on the retry (`:275-276`). Bounds are doubled:
  `asyncio.wait_for(..., 20.0)` at `:246-248` and `aiohttp.ClientTimeout(total=20.0)` at `:294`.
  Non-200 raises with the body truncated by characters (`:302-304`) — stderr only, never the replay.
- Prompt text: I re-derived `PROMPTS["derk-drafter-v1"]` and `PROMPTS["derk-metagamer-v1"]` by
  exec'ing the constants at `derk_player.py:52-85` and compared them to the design note's two
  verbatim blocks (`design.md:289-308`, `:315-320`): **byte-identical** after strip. Pinned by
  `tests/test_llm_player.py:196-204`.
- No real player names in the body: the user message is the server's draft observation minus
  `deadline_ms` (`derk_player.py:182-187`), and the observation is built alias-only
  (`draft.py:125-163`: `SEAT_ALIASES`, roles, catalog, clamps, match constants — no
  `cfg.players[i].name` anywhere). Asserted twice: `tests/test_draft.py:287-295` (no real name in the
  observation) and `tests/test_llm_player.py:180-193` (no real name in either request body, alias and
  catalog present, `deadline_ms` absent).
- The retry is exactly one: `for attempt in (1, 2)` (`:243`), success returns inside the loop
  (`:256-260`), the "will retry once" line prints only for `attempt == 1` (`:262-265`), and the
  fallback is unconditional after the loop (`:266-269`). Covered by
  `tests/test_llm_player.py:132-141` (second body has `temperature == 0` and the reminder),
  `:143-149` (two failures → `forge_picks`, exactly two bodies, stderr line), `:152-159`
  (`__hang__` twice under a monkeypatched 0.05 s timeout still returns), `:162-165` (transport
  exceptions).
- Fallback rule: `self._fallback` defaults to `forge_picks` (`:222`), i.e. `puffer-forge`'s table
  (`:90-107`), matching `design.md:328-330`. `forge_picks` returns the neutral loadout for an unknown
  role (`:107`), and both scripted rules are asserted legal for all six seats
  (`tests/test_llm_player.py:236-243`).
- No-key path: `:237-241` — no call at all when `_api_key` is falsy and no test transport is
  injected, logged once; `policy_from_env` (`:348-358`) passes
  `os.environ.get("ANTHROPIC_API_KEY","").strip() or None`.
- Wire shape: `players/client.py:202-207` dispatches only `phase == "draft"` (everything else,
  including `draft_result`, is ignored), `:234-256` calls `on_draft` (sync or async), swallows any
  exception with a stderr line and simply does not answer, and sends
  `{"phase":"draft","picks":[picks]}` — the exact frame `draft.resolve_reply` expects
  (`draft.py:175-181`).

**Server-side draft resolution (the r1-touched paths).**

- One parallel batch, one shared deadline, per-seat resolution: `draft.py:284-294`; a fast seat keeps
  its picks when a slow seat overruns (F1 above). `Seat.get_draft` (`server.py:181-201`) returns
  `("disconnected")` for a missing/closed socket, re-raises `CancelledError` so `wait_for` converts
  cleanly to a timeout, and clears `_draft_waiter` in `finally` — so a late draft frame after the
  timeout falls through to the per-tick router and is dropped, and the turn is never re-consumed.
- Whole-seat neutral on `unknown_item`: `draft.py:184-186` — `catalog.normalized_picks` returns
  `None` on any illegal slot (`catalog.py:163-178`, partial acceptance explicitly refused) and the
  whole seat takes `NEUTRAL_PICKS`, with the note preserved. Asserted for six illegal-pick shapes
  including a right-id/wrong-slot and a wrong-case id (`tests/test_draft.py:104-134`), including
  `rec["applied"] == catalog.neutral_applied(...)` and that the other seats are unaffected.
- Six causes, all reachable; enum synced to the manifest and asserted (F8 above).
- Note truncation, both sides: `draft.py:76-93` (server, authoritative) and
  `derk_player.py:171-178` (player, pre-send). Tests as listed under `6c44f82`.
- Degrade paths keep the phase alive: a raising source becomes `wrong_shape` with a stderr line
  (`draft.py:262-266`, test `:193-198`); every fallback prints
  `seat N (Cog-…): draft fallback to the neutral loadout (cause=…)` (`draft.py:304-307`).
- Edge observed (unreachable in practice): if the deadline instant were already past,
  `max(0.0, deadline_at - started)` gives `wait_for(..., 0.0)`, so that seat's observation would
  never be sent and it would resolve as `timeout`. Requires building six observations to take longer
  than `draft_deadline_ms`, whose schema minimum is 1000 ms (`coworld_manifest_template.json:97-101`).

**Regression sweep.**

- `git log -p --since='2026-08-28T10:00Z' -- tests/` covers all ten commits of the run. Per-commit
  `--numstat` on `tests/`: every change is net-additive (`74fcfc7` 8/2, 22/4, 14/2, 5/2; `721c548`
  36/7; `70db559` 30/1; `5adc034` 12/4; `7a424d7` 15/0; `6c44f82` 27/4; `450c798` 14/0; `04bf732`
  25/0; `651ea5d` 3/2; `624f1cb` none). I read every removed line: they are (a) the two-line
  docstring replaced by `651ea5d`, (b) the weaker single-seat timeout assertion replaced by the
  six-seat one in `5adc034`, (c) `loadout_digest == 0` replaced by `== catalog.loadout_digest()`
  (a stronger cross-check against the C digest, `74fcfc7`), (d) the `drafter` env assertion widened
  to include `ANTHROPIC_API_KEY_URI` (`70db559`), (e) inline-ws-client `continue`s replaced by an
  actual draft answer (`721c548`), (f) an import line reflowed (`6c44f82`). No deleted assertion, no
  widened tolerance, no test file removed, no `skip`/`xfail` added during the run.
- Skips: the three wasm gates hard-fail under `COGAME_REQUIRE_WASM_BUILD`
  (`test_fidelity.py:40-49`, `test_loadout.py:34-42`, `test_viewer.py:51-56`), which `ci.yml` sets.
  The one skip not converted is `tests/test_viewer.py:200` `pytest.skip("node not on PATH")` — I
  re-verified it myself; the CI log shows `337 passed in 55.09s` with no skipped count, so it did not
  fire (note: the r1 verdict cited 333; the log at this sha says 337).
- CI at the reviewed sha: `gh run list -R Metta-AI/cogame-derks-gym --branch main -w ci.yml` →
  run **33167936624**, `conclusion: success`, `headSha 624f1cb3717833bebc68edd1ed6702f94ad74fbe`.
  Jobs: `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓ (steps `Load the bundle in a real browser` →
  `{"loaded":true,"ms":602,…}` and `Assert the derks-gym chrome` both ran and succeeded; no
  `continue-on-error`), `upload-coworld` ✓. `grep -c "SEAT-COUNT FAIL"` over the full run log =
  **0**; the smoke log carries `smoke OK: seats=6 … reason=tick_cap` and
  `derks-gym smoke OK: end_reason=tick_cap winner=None final_tick=1200`.
- Placeholder gate (item 12): `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files finds
  nothing → the gate exits 0. A full sweep for `<name>`-shaped tokens across the three workflows
  yields six occurrences, all of them runtime values in comments or an input description, none of
  them a gated name: `<cow_id>/<sha>` in the static-replay-route comment (`ci.yml:135`), `<run_id>`
  in the artifact-readback recipes (`coworld-release.yml:21`, `coworld-submit.yml:17`), `<cow_id>` in
  two API-route comments (`coworld-release.yml:75, :358`), and `<name>:vN` in the `policy` input
  description (`coworld-submit.yml:31`). The two `coworld-release.yml` `<cow_id>` comments are not
  named in the checklist's expected-residue list but are the same class (a route comment, not a
  substitution site). No new residue relative to `70db559` (no workflow file changed in the range).
- Manifest: `git diff 70db559 624f1cb -- coworld_manifest_template.json` is exactly one deleted line
  (`"malformed"` from the `fallback_cause` enum), i.e. only what F9 describes. `num_agents: 6` is
  present at `:681` (`variants[0].game_config`), `:716` (`variants[1].game_config`) and `:768`
  (`certification.game_config`), and absent from every variant top level;
  `len(certification.players) == 6` (`:727-746`).
  `tools/ci/policies.json` holds four distinct policies — two `PLAYER_PROMPT` champions (champion #2
  `derk-metagamer-v1` carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) and two
  `PLAYER_SCRIPTED` fillers — and their `"run": "/bin/derks-gym-player"` target really exists
  (`Dockerfile:87-88`) and is the entrypoint docker-smoke uses (`docker_smoke.sh:23`).

---

## Could not determine

- **Whether F2's heartbeat interaction has ever fired in a real hosted episode.** I reproduced the
  mechanism in isolation at scaled timings with the pinned aiohttp, and the production numbers (20 s
  ping + 10 s pong window vs a 40 s worst-case block) are arithmetic; but no CI replay exercises it,
  because docker-smoke runs keyless and never makes an LLM call. What would settle it: one keyed
  episode whose first attempt times out (or a test that drives `PromptDraftPolicy` over a real
  `web.WebSocketResponse(heartbeat=20)` with a >30 s stub), and a check for
  `fallback_cause == "disconnected"` in the resulting draft record.
- **Whether the checklist owner reads item 15's "driven by `viewer_smoke.mjs --strict-text-bounds`"
  as satisfiable by a lineage-specific DOM fixture in its own step** (F7). The r1 verdict said yes on
  the same evidence; I re-verified the evidence, not the ruling.
- **Whether item 8's "recorded" is satisfied by a player stderr line alone** (F4). The line exists
  and is stable; nothing in the replay or `results.json` distinguishes an LLM fallback. What would
  settle it: a phase-60 counting recipe naming the source it reads.
