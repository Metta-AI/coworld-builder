# r1 review — commons-family

Repo: `Metta-AI/cogame-commons-family` @ `5c6490440ccaf6f7db401607f52b669023af9208` (main head)
Range: `7066a18..5c64904` (three commits: `53f89cc` fork, `32a5e5c` player connect retry, `5c64904` ready bridge)
Design note: `/workspace/coworld-builder/runs/2026-08-24-commons-family/design.md` (identical to `design-r1.md`; committed copy at `docs/plans/2026-08-24-commons-family-design.md` is byte-identical to the run copy)
Files read: 58 (whole repo tree except binary art; plus `cogame-bullwhip`'s 5 counterpart files, `coworld-meadow`'s `shared/*.py` + tree listing, `coworld-builder/templates/*`, CI logs and the `smoke-replay` artifact of run 32767219248)
Checklist consulted for *where to look*: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST

**Per the coordinator's brief this is a neutral trace-and-report: I do not assign severity and do
not propose fixes.** Every observation is numbered, cites `file:line`, states what the code does
and what the note says, and names the checklist item it touches so the judge can categorise. I
label each as **observed** (I read/ran it), **inferred** (I reasoned about it), or **untested**
(would need a run to settle). Section 3 lists builder claims I verified as true so the judge can
lean on them.

---

## 1. Observations

### O1 — an unclassified LLM transport exception escapes `decide()` into `_play_game()`, which has no handler: no artifacts, no exit
- Where: `game/llm.py:168-177` (`raise` on any non-429/529 `HTTPError`), `game/llm.py:128-134`
  (`raise` on any non-throttle `ClientError`), `game/llm.py:322-328` (`list(executor.map(...))`
  re-raises), `game/server.py:383-385` (`await asyncio.to_thread(session.decider.decide, ...)`),
  `game/server.py:250` and `game/server.py:283` (`asyncio.create_task(_play_game())`, no
  done-callback, no `try/except` anywhere in `_play_game`).
- Observed: `_decide_seat` (`llm.py:338-363`) catches exactly `LlmRateBudget`, `LlmTimeout`,
  `LlmThrottled`, `LlmTransportError`. Auth/validation errors are deliberately re-raised
  (`llm.py:132-134`, "must be loud at round 0"), as are any other exception shapes the transports
  can produce (e.g. `KeyError` from `json.load(response)["content"]` at `llm.py:166`). Such an
  exception propagates out of `executor.map` → `decide` → `to_thread` → `_play_game`, whose task
  nobody awaits.
- Reproduced (I ran it): with six prompt seats and a transport raising `HTTPError 401`,
  `_play_game()` raised `HTTP Error 401: Unauthorized`; `results.json` and `replay.json` were
  **not** written and `_finish` never ran. Script: 3 rounds, `min_round_seconds=0`, registration
  grace 0.
- Note says: §Degrade, never hang (design.md:510-526) gives a response for every failure row and
  ends "Nothing in the round loop blocks on an unbounded read"; §End conditions (design.md:295-301)
  "The game never exits non-zero on a player-side problem". There is no row for "the credentials
  are present but rejected", and the note's own §The LLM policy (design.md:375) asks for exactly
  this raise-immediately discipline — so the raise is intended; what is unhandled is where it lands.
- Checklist item touched: 5 (hang/timeout). Reachable only with credentials that a provider
  rejects; CI runs without credentials, so the CI evidence cannot show it.

### O2 — the `paused` branch of the round loop has no deadline check
- Where: `game/server.py:356-359`:
  ```python
  while engine.round < CONFIG.rounds:
      if session.paused:
          await asyncio.sleep(0.1)
          continue
  ```
- Observed: `play_deadline` is only tested at `server.py:445`, after `settle_round`. While
  `session.paused` is true the loop spins indefinitely and never reaches that test. `paused` is set
  by the `/admin` websocket (`server.py:216-217`), which is unauthenticated (no token check, unlike
  `/player` at `server.py:226-230`).
- Note says: §Server (design.md:622-623) keeps meadow's `/admin` pause/resume verbatim; §Degrade
  (design.md:525) "Nothing in the round loop blocks on an unbounded read".
- Checklist item touched: 5 ("no unbounded loop"). Requires an `/admin` `pause` command to reach.

### O3 — `play_deadline` is anchored after the connect wait, so the 60 % arithmetic is `0.6 × T` **plus** the connect timeout
- Where: `game/server.py:320-322` — `start = time.monotonic()` inside `_play_game`, which is
  itself only entered after `_start_after_player_connect_timeout` sleeps
  `player_connect_timeout_seconds` (`server.py:278-283`), plus the 5 s registration grace
  (`server.py:331`).
- Observed arithmetic: worst case to a settled, scored episode is
  `180 (connect) + 5 (grace) + 0.6 × 1200 (play budget) = 905 s` = 75 % of `episodeTimeoutSeconds`,
  if the play budget were ever the binding constraint.
- Inferred: with the shipped variants it never binds — 20 rounds × `round_seconds` 20 = 400 s of
  play maximum, so the real worst case is `180 + 5 + 400 = 585 s` (48.8 %) to artifacts, and the
  linger (30 s, hard cap 90 s, `server.py:517-520`) runs *after* `write_data`
  (`server.py:486-499`). The schema permits `rounds ≤ 100` and `round_seconds ≤ 120`
  (`engine.py:95-96`), where the guard would bind and settle at 905 s.
- Note says: design.md:445-448 computes 610 s / 50.8 % by summing connect + play + linger, i.e. it
  treats 720 s as the *whole-episode* budget rather than a budget started after the connect wait.
- Checklist item touched: 5 (timeout, "settles and scores inside 60 % of episodeTimeoutSeconds").

### O4 — `client/renderer.js` is not the starter's file with four edits; roughly half of it is rewritten
- Where: `client/renderer.js` (1331 lines) vs `/workspace/starters/cogame-bullwhip/client/renderer.js`
  (1400 lines). `diff -u` = **800 lines removed, 722 added**. Extracting top-level functions and
  applying the `Bullwhip→Commons` rename:
  - byte-identical (8): `applyNames`, `assetUrl`, `ellipsize`, `hexToRgb`, `isBaselineFiller`,
    `loadImages`, `rgba`, `seatColor`;
  - present in both but changed (23): `attachLive`, `attachReplay`, `bindFeedToggle`, `blockHead`,
    `buildScrub`, `clampName`, `computeLayout`, `describeEvent`, `draw`, `drawBubble`, `drawChart`,
    `escapeHtml`, `makeEffects`, `makeNameMap`, `makeRenderer`, `matchHeader`, `reasonLine`,
    `renderFeed`, `roundRect`, `stateToView`, `updateEndscreen`, `updateScorebug`, `wrapLines`;
  - dropped from the starter (17): `drawBelt`, `drawCrate`, `drawCrateCluster`,
    `drawCustomerDelivery`, `drawCustomers`, `drawDock`, `drawProduction`, `drawShipment`,
    `drawSlip`, `drawStack`, `drawStation`, `drawTag`, `money`, `peakOrders`, `playerFrameToState`,
    `slotX`, `stageOfSeat`;
  - added (14): `beatLabel`, `chartTitle`, `cogCentre`, `drawCogRow`, `drawField`, `drawFlow`,
    `drawMushrooms`, `drawOrchard`, `drawPatches`, `maintenanceChip`, `moduleBadge`,
    `mushroomRowY`, `paint`, `score`.
- Observed: the chrome *scaffolding* (feed, scrub, scorebug, endscreen, name map, effects,
  attach/replay loop, chart) keeps the starter's names, structure and call graph; the board drawing
  is entirely new; several small hardening edits sit outside the note's list — `String()` coercions
  in `escapeHtml` (`renderer.js:862`) and `wrapLines` (`renderer.js:582`), a radius clamp in
  `roundRect` (`renderer.js:141`), `clampName`'s cut moved 24→26 (`renderer.js:787`), `money`
  renamed `score`, and a new `paint()` clamp helper (`renderer.js:109-125`).
- Note says: §Chrome provenance (design.md:773-777) — "`client/renderer.js` and `client/chrome.css`
  are copied byte-for-byte from bullwhip except for the four surgical edits listed below; the
  identifier rename … is applied to the export object and its two call sites, and **nothing else in
  those files is rewritten**". §Readouts (design.md:832) separately says the board is "bullwhip's
  `draw()` retargeted" and describes four new module boards, which the file does implement.
- Checklist item touched: 14 (static-viewer, "chrome is the starter's, not a lookalike"). The
  starter's ids, CSS sections and chrome functions are all present (see §3); the divergence is
  between the note's "byte-for-byte" sentence and the file.

### O5 — `client/chrome.css` carries three in-place edits, one of which is not in the note's list of four
- Where: `client/chrome.css:1-7` (header comment rewritten), `:268` `grid-template-columns:
  repeat(4, 1fr)` → `repeat(6, 1fr)`, `:376-381` `#endscreen` gains `bottom: var(--band, 0px)`,
  then an appended block `:472-635` under a banner comment.
- Observed: `diff` against bullwhip's `chrome.css` is exactly those three hunks plus the append.
  The `#endscreen` pin is the note's transport edit 2. The 4→6 scorebug column change is a
  necessary consequence of six seats but is not among the note's four edits, and neither is the
  header comment.
- Note says: design.md:773-777 ("byte-for-byte … except for the four surgical edits") and
  design.md:801-821 (the four edits).
- Checklist item touched: 14.

### O6 — `replay-viewer/static_replay.js` carries a fifth edit: the ready bridge now waits on `data-replay-loaded`
- Where: `replay-viewer/static_replay.js:120-147` (`whenDrawn` + `tell("ready")`), replacing
  bullwhip's double-`requestAnimationFrame` at `static_replay.js:120-124` of the starter. Added by
  commit `5c64904`, with `tests/test_viewer_contract.py:122-135` asserting it.
- Observed: the rest of the file diff is exactly the documented renames (`_bw_*`→`_cf_*`,
  `BullwhipReplayModule`→`CommonsReplayModule`, `BullwhipRenderer`→`CommonsRenderer`) plus the
  header comment. `data-replay-error` write/remove, the 20 s `AbortController`, the Retry button
  and the `{src:"coworld-replay"}` envelope are otherwise untouched.
- Note says: design.md:727 — "the `?replay=` fetch, the 20 s `AbortController` timeout, the Retry
  button, the `{src:"coworld-replay"}` parent bridge and the `data-replay-error` write are
  **untouched**".
- Checklist item touched: 13 (the bridge now fires only after the first painted frame, which is
  what the brief asks for; the divergence is from the note's "untouched", not from the checklist).

### O7 — the viewer expands recorded states; it does not replay events through a sim, and no test asserts frame-by-frame re-derivation
- Where: `replay-viewer/commons_family_replay.nim:1-12` (docstring: "It deliberately does NOT
  re-run the physics"), `:59-199` (`buildStates` reads `rounds[r].gains/scores/state_before/
  state_after/series/seat_frozen` and folds them into one state per event).
- Observed: the payload's `seats[].score/gain/extracted`, `resource` and `series` are copied out of
  the recorded round records; the only derived quantity is `public_effort`, which the wasm module
  **recomputes** from each recorded decision per module (`commons_family_replay.nim:139-149`) rather
  than reading `record["public_effort"]` — i.e. one small second implementation of
  `Module.public_effort` (`modules/cleanup.py:113`, `harvest.py:215-219`, `allelopathic.py:151`,
  `mushrooms.py:185-186`). I traced the four branches and they agree with the Python for the
  shipped `effort_budget = 3`.
- Note says: §Viewer/Pipeline (design.md:737-745) makes this an explicit design choice with a
  reason ("a Nim reimplementation of four resource modules would be a second source of truth").
- Checklist item touched: 2 ("Replaying the recorded events through the sim reproduces the recorded
  per-tick state frame by frame … A test asserts it"). What exists instead is a payload-contract
  test suite (`tests/test_viewer_contract.py:253-320`) and a determinism test
  (`tests/test_episode.py:146-156`).

### O8 — a seat's worst case is up to 8 provider requests per round, not the note's two
- Where: `game/llm.py:382-399` — `for sleep_seconds in (*THROTTLE_SLEEPS, None)` issues up to
  **four** requests per attempt, and `_decide_seat` (`llm.py:338`) runs two attempts.
  `tests/test_llm.py:183-189` asserts exactly this: `transport.calls == 8`, `decider.requests == 8`
  for one throttled seat in one round.
- Observed: every one of those requests is bounded by `timeout = min(decision_timeout_seconds,
  deadline − now)` (`llm.py:384-386`) and the loop exits with `LlmTimeout` once the round deadline
  passes, so the *time* bound holds (`tests/test_llm.py:192-200` asserts the ladder stops at the
  deadline). The *rate* consequence: six throttled seats can draw 48 requests in one round against
  `llm_max_requests_per_minute = 120`; exhaustion falls the seat back with cause `rate_budget`
  (`llm.py:387-388`, `server.py:394`) rather than waiting.
- Note says: design.md:439-441 — "Per-seat worst case inside a round: one call at 8 s, throttle
  sleeps ≤ 3.5 s, one retry at 8 s = 19.5 s"; design.md:460-461 — "6 requests per round, and a
  round is ≥ 3 s, so the game issues at most 120 requests per minute".
- Checklist item touched: 5 (bounded — it is), and the note's own arithmetic.

### O9 — `fallback` carries a fifth cause, `disabled`, which the note's enum does not list
- Where: `game/llm.py:319-320` (`return {slot: (None, "disabled") ...}` when the transport is
  `None`), `game/server.py:388-408` (writes `cause` straight into the `fallback` event and
  increments `results.fallbacks`).
- Observed in the shipped CI replay (run 32767219248 `smoke-replay` artifact): eight events
  `{"kind":"fallback","cause":"disabled","alias":"Cog-E"}`, `results.fallbacks = [8,0,0,0,0,0]`,
  `llm_requests = 0`.
- Note says: design.md:516 — "`fallback` event with `cause ∈ {timeout, parse, rate_budget,
  transport}`"; design.md:517 describes the no-credentials row without naming a cause.
- Checklist item touched: 8 ("the fallback is recorded so phase 60 can count it" — it is).

### O10 — `steward` in `open` rooms names a seat-offset patch, not the fullest
- Where: `game/baselines.py:71-89`:
  ```python
  ranked = sorted(live, key=lambda patch: (-lookup[patch]["stock"], patch))
  if obs["module_state"].get("property_rights") == "open":
      return ranked[obs["slot"] % len(ranked)]
  return ranked[0]
  ```
- Observed: the docstring at `baselines.py:72-80` gives the reason (six stewards all reading "the
  fullest patch" queue on patch 0 and strip it in one round). `closed`/`partnership` take
  `ranked[0]`, which the note requires so partners agree.
- Note says: design.md:481-484 — "`harvest`: choose the **fullest live patch it is allowed to
  name** (`open` → any; …)".
- Checklist item touched: 7 (legality is asserted separately and passes;
  `tests/test_baselines.py:222-232` also asserts six stewards leave every module standing).

### O11 — no grid harness for the baseline parameters is present in the repo
- Where: the tuned constants are `game/baselines.py:22-24`
  (`CLEAN_POLLUTION_TRIGGER = 0.35`, `CLEANUP_STOCK_FLOOR = 30.0`, `CONTRITE_ROUNDS = 5`), the
  quota rule at `baselines.py:49-52`, and the per-module rules at `baselines.py:138-186`.
- Observed: `grep -rn "grid"` over the repo returns only the design note's "no grid layer" prose and
  `numpy.meshgrid` inside the planner DPs. There is no sweep script, no harness, and no recorded
  tuning output. What exists is a behavioural test (`tests/test_baselines.py:222-232`, six stewards
  keep every module alive over 20 rounds) and the grader comparison
  (`tests/test_grader.py:119-128`, steward beats free-rider in every module).
- Note says: nothing — §Scripted baselines (design.md:466-508) derives the numbers from meadow and
  from the sustainable-aggregate arithmetic, and does not claim a harness.
- Checklist item touched: 7 ("The baseline's parameters were tuned with a grid harness, not
  guessed").

### O12 — `game.docs.readme` is a `uri`, where the checklist spells `text`
- Where: `coworld_manifest_template.json` → `game.docs.readme = {"type":"uri","value":
  "https://github.com/.../src/coworld/examples/commons_family/README.md"}`; `game.docs.pages` is a
  4-element array, each `{"id","title","content":{"type":"text","value":…}}` (rules.md 2285 chars,
  modules.md 2218, institutions.md 1556, policies.md 1604).
- Note says: design.md:891-894 specifies exactly the `uri` readme plus those four pages.
- Checklist item touched: 10 (manifest), whose text reads
  `{"readme":{"type":"text","value":…},"pages":[…]}`. `game.protocols` carries both `player` and
  `global`, each an object with `type`/`value` (verified).

### O13 — the viewer draws model-authored text on canvas; CI never exercises a full-cap remark, and there is no worst-case renderer fixture
- Where: `client/renderer.js:569-576` (`if (seat.say) drawBubble(...)`),
  `commons_family_replay.nim:107-110` (`say[slot] = event{"message"}.getStr("")` from `chat`
  events), `game/engine.py:386-398` (the `chat` event carries the seat's `message`, which for a
  prompt seat is the model's own words).
- Observed: contrary to the checklist's premise that "a scripted baseline emits no `say`", **the
  scripted baselines do speak** — `game/baselines.py:105-108` `_say()` is called by every baseline —
  so the CI replay is not text-free. In the run-32767219248 replay: 48 chat messages, seven distinct
  strings, **maximum length 40 runes** against the 140-rune cap. The smoke reported
  `canvas text: 2236 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)`.
- Observed: `.github/workflows/ci.yml` has three jobs (`test`, `docker-smoke`,
  `wasm-viewer`) and 250 lines; there is no step that loads `client/renderer.js` against a
  synthetic worst-case frame.
- Note says: §Readouts (design.md:840-851) describes the feed and the board and pins legibility at
  360 px with `viewer-smoke.png` as the evidence; it does not describe a renderer fixture.
- Checklist item touched: 15 (legibility, final bullet).

### O14 — a full-cap remark is ellipsized by design; the bubble clamps into the frame rather than reserving a band
- Where: `client/renderer.js:607-634` (`drawBubble`): `width = Math.max(40, Math.min(maxW,
  ctx.canvas.width - 12))`, `lines = wrapLines(ctx, text, width - pad*2, 2)` — a hard **2-line** cap
  with `…` (`renderer.js:595-601`); the box is then clamped, `bx = Math.max(3, Math.min(x - bw/2,
  canvas.width - bw - 3))`, `by = Math.max(3, Math.min(bottom - bh - 5*scale, canvas.height - bh -
  3))`. `maxW` is `pitch * 1.5` where `pitch = L.cogs.w / seats.length` (`renderer.js:521`, `:575`).
  Every other string goes through `paint()` (`renderer.js:109-125`), which ellipsizes to the canvas
  and clamps the box.
- Inferred (untested — would need a browser run): at a 360 px embedded width, `pitch ≈ 57 px` and
  `maxW ≈ 86 px`, so two lines of a 10.5 px font hold roughly 25–30 characters; a 140-rune remark
  would be ellipsized. At 960 px it holds roughly 90. The clamping is what keeps `never_inside = 0`
  in the smoke, and the layout reserves no band sized from `chat_max_chars` — the bubble is drawn
  over the board band above the cog row.
- Note says: design.md:840-843 describes the feed line per chat; the note does not size a bubble
  band.
- Checklist item touched: 15 ("a reserved band in the layout, sized from the cap the server
  enforces"; "ellipsis … is a defect for sentences").

### O15 — in `partnership`, a passing or disconnected seat "holds" patch 0 by virtue of the default
- Where: `game/modules/harvest.py:82-84` builds `named` from **every** seat's `decision.patch`,
  including seats whose decision is the all-zero default (`modules/base.py:45-58`, `patch=0`), which
  is what `server.py:435-437` and `headless.py:122` create for a `pass`/`no_submission` seat; the
  hold test is `all(partner in named.get(patch, set()) ...)` at `harvest.py:112-124`.
- Observed: consequence — if one member of the pair owning patches 0 and 1 never connects, patch 0
  is still counted as held every round and its partner can harvest it alone; patch 1 can never be
  held. `_pair_of(patch) = pairs[patch // 2]` (`harvest.py:62-63`).
- Note says: design.md:126-129 — "A patch yields this round only if **both** partners named it this
  round (either may demand 0 — naming it is 'holding' it)". The note does not say what an absent
  seat names.
- Checklist item touched: none directly; it is a rules-vs-note edge.

### O16 — the player container's spectate loop has no wall-clock bound and pings are disabled
- Where: `player/player.py:83-87` (`while True: message = json.loads(await websocket.recv())`) with
  `websockets.connect(url, ping_timeout=None)` at `player/player.py:56`.
- Observed: the loop ends only on a `final` frame or on the socket closing (`player.py:88-93`, both
  handled as exit 0). The *connect* phase is explicitly bounded — 150 s deadline with 0.5→2 s
  backoff (`player.py:44-64`), inside the game's 180 s connect timeout, with two tests
  (`tests/test_episode.py:269-308`).
- Note says: design.md:556 — the player "registers … then spectates until `final`"; §Degrade
  (design.md:518) covers a seat whose socket never connects, not one whose game hangs.
- Checklist item touched: 5 ("no … blocking read"). In CI all six player containers exited 0
  (docker-smoke log, run 32767219248), because the game exits and closes the sockets.

### O17 — `norm_text` reaches the prompt and the replay with no length cap
- Where: `game/engine.py:110` (`norm_text: str = ""`, no `max_length`), used at `engine.py:322`
  (observation), `llm.py:286` (system prompt), `engine.py:606` (`config.model_dump()` into the
  replay). `config_schema.properties.norm_text` in the manifest carries no `maxLength` either.
- Observed: every *model-authored* string is capped and rune-truncated (`message` at
  `engine.py:285`, `note` at `engine.py:287`, `prompt` at `server.py:259`, policy names at
  `engine.py:557` and `:588`, `scripted` at `engine.py:590`). `norm_text` comes from the manifest /
  runner, not from a policy.
- Note says: design.md:424-430 lists the strings the truncator covers: "`message`, `note`, policy
  names, and every error string that can reach the replay". No error string reaches the replay —
  the `fallback` event carries only the fixed `cause` token (`server.py:402-406`); transport errors
  are logged (`llm.py:351`, `llm.py:359`) and dropped.
- Checklist item touched: 9 (rune-safe truncation — all the strings the note names are covered).

### O18 — `mushrooms` accumulates `eaten_total` in step 5, not step 7
- Where: `game/modules/mushrooms.py:114-115` (inside `resolve`) vs the note's
  design.md:246 ("**Step 7, `mushrooms`:** `eaten_total[c] +=` this round's total per colour;
  `w[c] = 1 + eaten_total[c]` …").
- Observed: `dynamics` (`mushrooms.py:131-134`) then reads the already-updated totals, so the spawn
  weights are identical to the note's; the only difference is which hook owns the `+=`. Asserted by
  `tests/test_modules.py:330-337`.
- Checklist item touched: none; recorded for exactness of the resolution-order trace.

### O19 — `harvest` ownership is a 1:1 permutation only because `patch_count == num_agents`
- Where: `game/modules/harvest.py:33-43` — `owner = [patch_deal[patch] % config.num_agents ...]`
  over a shuffle of `range(patch_count)` (`engine.py:234-236`).
- Observed: with the shipped `patch_count = 6`, `num_agents = 6` the modulo is the identity and
  `owner` is a permutation (asserted by `tests/test_modules.py:191-196`). The schema allows
  `patch_count` 1..12 (`engine.py:124`) and `num_agents` is pinned 6..6 in the manifest, so no
  shipped variant can desynchronise them; a hand-edited `game_config` could.
- Note says: design.md:122-129 — "a seeded 1:1 permutation of the six seats onto the six patches"
  and "the six patches are dealt to three seeded pairs".
- Checklist item touched: none directly (6/num_agents is pinned everywhere else).

---

## 2. Traced and consistent

**Resolution rules (design.md:157-248 vs `game/engine.py`, `game/modules/*.py`)**
- `engine.py:373-485` executes the note's steps 4→8 in order: chat published and attached to round
  *r* (`:385-398`) and read back only from `history[-1]` in the next round's observation
  (`:327-329`, asserted `tests/test_institutions.py:126-133`); module resolve (`:403`); one
  `decision` event per seat (`:405-415`); sanctions ascending slot with cost/burn/counters
  (`:418-441`); dynamics with the collapse latch (`:443-448`); booking (`:450-456`); `round_end`
  (`:475-483`).
- `cleanup` step 5 (`modules/cleanup.py:45-70`): budget clamp reducing `clean` first, pro-rata over
  `apples`, stock decrement, `pollution = clamp(p + silt − clean_power × Σclean, 0, 1)` — matches
  design.md:194-200. Step 7 (`:72-90`): latch below `collapse_threshold` with no further regrowth,
  else `min(cap, a + rate × (1−p) × a × (1−a/cap))` — matches design.md:202-204. Exact arithmetic
  asserted at `tests/test_modules.py:26-95` including "dead means dead" over five further rounds
  and post-collapse scavenging.
- `harvest` step 5 (`modules/harvest.py:75-146`): dead→`void`/`cause:"dead"`, `closed`→`trespass`,
  `partnership`→`unheld`, then per-patch ascending pro-rata — matches design.md:206-213. Step 7
  (`:148-168`): `stock < 1.0` → 0.0 + `dead` + `patch_dead`, else logistic — matches
  design.md:215-217. Asserted `tests/test_modules.py:103-196`.
- `allelopathic` step 5 (`modules/allelopathic.py:47-107`): `plant` reduced first, per-colour
  canonical pro-rata, favourite 2.0 / base 1.0, then planting one unit at a time ascending slot
  taking from the largest *other* colour with canonical ties, void on an empty source, and the
  converted slot taking its ripe berry (`:92-93`) — matches design.md:219-229. Step 7 (`:109-125`):
  `ripe = min(planted, ripe + 0.5 × planted²/60)`, `barren` when the field's ripe total is 0 —
  matches design.md:231-234, and the 10.0/round and 30.0/round figures are asserted at
  `tests/test_modules.py:250-263`.
- `mushrooms` step 5 (`modules/mushrooms.py:49-129`): frozen seats voided with `digesting`,
  per-colour canonical pro-rata, payoffs ascending slot then canonical colour (red→eater,
  green→2/N to all, blue→3/(N−1) to everyone else), `frozen_until = r + ceil(k)` — matches
  design.md:236-244. Step 7 (`:131-155`): weights `1 + eaten_total`, largest-remainder apportionment
  with canonical ties, per-colour then total cap dropping from the largest first — matches
  design.md:246-248. Asserted `tests/test_modules.py:280-351`, including blue paying the eater
  exactly 0.
- Determinism: one `random.Random(seed)`, three draws in the note's order (`engine.py:225-236`),
  asserted `tests/test_modules.py:359-375` and by byte-identical replays modulo `generated_at`
  (`tests/test_episode.py:146-156`).

**Decision path**
- One parallel batch: `llm.py:321-328` maps every prompt slot onto a `ThreadPoolExecutor` sized to
  the batch; `tests/test_llm.py:219-233` proves concurrency with a `threading.Barrier(6)` that only
  clears if all six calls are in flight at once. The server calls it once per round
  (`server.py:382-385`).
- Per-call deadline `min(decision_timeout_seconds, remaining)` (`llm.py:384-386`); truncated
  throttle ladder `(0.5, 1.0, 2.0)` (`llm.py:46`); tolerant parse via first balanced `{...}` span
  with string/escape awareness (`llm.py:209-238`, six extraction tests at
  `tests/test_llm.py:85-109`); retry exactly once with the note's hint text
  (`llm.py:338-339`, `:48-51`, asserted `tests/test_llm.py:152-167`); fallback to
  `fallback_scripted` recorded as an event and in `results.fallbacks` (`server.py:388-408`).
- No credentials → `build_transport` returns `(None, "")` (`llm.py:198-201`), `decide` short-circuits
  before touching the transport (`llm.py:319-320`), `requests` stays 0. Two tests plus an
  `ExplodingTransport` guard (`tests/test_llm.py:58-62`, `:257-301`), and the CI episode shows
  `llm_requests: 0`.
- Rate budget: rolling 60 s deque, retries drawn from it, exhaustion → `rate_budget` fallback rather
  than a wait (`llm.py:401-415`, asserted `tests/test_llm.py:203-211`).
- Prompt: one system prompt per seat built once (`llm.py:333-335`, asserted
  `tests/test_llm.py:236-249`), standing orders truncated to 1200 runes (`llm.py:298`), user message
  = the observation minus `type`/`round_seconds` (`llm.py:303-305`, asserted
  `tests/test_llm.py:140-149`), prefill + `max_tokens` 300/4000 (`llm.py:369-380`).

**Waits and bounds**
- Round barrier = batch complete or `round_deadline = round_start + session.round_seconds`
  (`server.py:360-385`); pacing floor `min_round_seconds` applied after the batch
  (`server.py:414-416`); `play_deadline` checked between rounds only (`server.py:445-457`), so a
  deadline settle lands on a clean boundary — asserted end-to-end through the server's own loop at
  `tests/test_episode.py:185-202` (`reason == "deadline"`, `1 ≤ rounds < 20`, scores non-zero,
  `deadline` event present).
- `no_players` after the 180 s connect timeout (`server.py:278-283`, `:325-328`), artifacts written,
  all-zero scores — `tests/test_episode.py:205-213`.
- Post-game linger 30 s / hard cap 90 s / extended only while `/global` viewers are attached
  (`server.py:517-520`).
- Artifact writes on `asyncio.to_thread` (`server.py:486-499`); `write_data`'s HTTP path carries a
  60 s timeout (`shared/artifact_io.py:60`).
- `/global` sender is progress-gated and coalesced with meadow's comment kept verbatim
  (`server.py:181-203`).

**Strings**
- `truncate_runes` is a code-point slice (`engine.py:75-86`) applied to `message`, `note`, policy
  names and `scripted`; `ensure_ascii=False` on both artifact writes (`server.py:489`, `:496`) and
  in `headless.write_artifacts` (`headless.py:161-162`), encoded UTF-8 exactly once
  (`artifact_io.py:52-53`). `tests/test_replay_parse.py:113-136` feeds a 200-rune 4-byte
  emoji/CJK line, asserts the recorded message is exactly 140 runes and the whole document decodes
  with no error handler. `note` is echoed only to its own seat (`engine.py:330`, asserted
  `tests/test_institutions.py:119-123`) and is absent from `Decision.to_json`
  (`modules/base.py:71-85`) — `tests/test_replay_parse.py:104-110` asserts the substring `"note"`
  does not occur anywhere in the replay bytes.

**Replay writer**
- `replay_payload` (`engine.py:563-613`) emits `format, protocol, version, coworld, module, variant,
  generated_at, seed, config, names, policyNames, seats, rounds, events, results`; `config` is
  `CommonsConfig.model_dump()`, which structurally cannot contain `tokens` (asserted
  `tests/test_replay_parse.py:143`). Per-round records carry `state_before`, `decisions`, `gains`,
  `extracted`, `scores`, `state_after`, `total_extracted`, `public_effort`, `collapsed`, `series`,
  `seat_frozen`, `messages` — a superset of design.md:673-678, confirmed on the real CI artifact.
- Event vocabulary: `EVENT_KINDS` (`engine.py:50-69`) is exactly the note's 18 kinds in the note's
  order; `_stamp` (`engine.py:504-511`) raises on any off-vocabulary kind and stamps `alias` onto
  every per-seat event; the wasm module's `EventKinds` (`commons_family_replay.nim:26-31`) is
  asserted **tuple-equal** to the Python constant (`tests/test_viewer_contract.py:253-258`).
  `src` values emitted are `llm`, `scripted:<name>`, `fallback:<cause>`, `player`, `pass`
  (`server.py:378/391/394/421`, `engine.py:436`).
- `results` (`engine.py:528-560`) rejects any reason outside `("complete","deadline","no_players")`
  and rounds scores to 3 dp; `score = Σ gains − cost×given − burn×received` is recomputed
  independently from the round records in `tests/test_episode.py:89-122`.

**Viewer wiring**
- `config.nims:35-41`: `MODULARIZE=1` + `EXPORT_NAME=CommonsReplayModule`;
  `static_replay.js:160` calls the factory `CommonsReplayModule()`. Matched pair — no
  `onRuntimeInitialized` anywhere in the tree. `EXPORTED_FUNCTIONS` `_cf_*` matches the `exportc`
  names in the Nim (`commons_family_replay.nim:201-254`) and the `module._cf_*` calls in the shell
  (`static_replay.js:94-103`); asserted three ways at `tests/test_viewer_contract.py:57-91`,
  including "no starter symbol survived the rename".
- `data-replay-loaded="true"` is written once, at `renderer.js:1320`, after
  `setIndex(0,true)` and after the synchronous first `frame(0)` call that reaches
  `renderer.draw(...)` (`renderer.js:1296-1318`) — i.e. on the first drawn frame.
  `data-replay-error` is written and cleared only by the shell (`static_replay.js:56`, `:107`,
  `:156`). CI: `{"loaded":true,"ms":284, …}`.
- Payload contract matches design.md:750-764 key for key (`commons_family_replay.nim:161-199`,
  `:221-232`), one `states[i]` per `events[i]`, and `flow[]` is populated only by `mushrooms`
  (`modules/mushrooms.py:81-108`).
- Transport rules: `relayout()` is the single writer of `--band`/`--hudscale` on
  `document.documentElement` (`replay-viewer/index.html:62-73`, asserted
  `tests/test_viewer_contract.py:189-195`); `#endscreen` is pinned to `bottom: var(--band, 0px)`
  (`chrome.css:376-381`); every seek path funnels through the `buildScrub` callback which removes
  `.show` before `setIndex(next, true)` (`renderer.js:1258-1264`), and `updateEndscreen` toggles it
  off for any non-terminal index (`renderer.js:991`); beats are `<button type="button">` with
  `aria-label`/`title` and an `onclick` seek (`renderer.js:1195-1212`), labelled in spectator
  English (`renderer.js:1144-1158`).
- Beat kinds emitted are exactly `round, chat, sanction, collapse, patchdead, fallback, end`
  (`renderer.js:1134-1142`) and each has a CSS rule (`chrome.css:481-488`); both directions are
  asserted (`tests/test_viewer_contract.py:223-231`).
- No `#viewpanel`, zoom or minimap anywhere (bullwhip's page has none; asserted
  `tests/test_viewer_contract.py:160-162`); `computeLayout` derives everything from the frame
  (`renderer.js:156-170`), so the board is fixed, which is what makes `--strict-text-bounds`
  appropriate.
- The appended index.html block declares only `cfModuleBar` and `cfPatchGrid`, both outside
  `#transport` and `#board-wrap`, with no collision against the renderer's globals (asserted
  `tests/test_viewer_contract.py:165-186`).
- `.plate-name { min-width: 3.2em; flex: 1 1 auto; }` (`chrome.css:282-294`, inherited from
  bullwhip unmodified), `.plate-label`/`.plate-badge` hidden under 640 px (`chrome.css:465-468`,
  `:621-626`), scorebug regrids at 560/420 px.
- The bundle fetches only `?replay=<url>` plus same-directory assets
  (`static_replay.js:67-89`, `tools/build_replay_viewer.sh:56-72`); no `/client/replay` route exists
  in the server (`server.py:135-152` serves only `/healthz` and the three client pages).

**Manifest / packaging**
- Six variants, `num_agents: 6` and six `players[]` in every one, all carrying `rounds: 20`,
  `round_seconds: 20`, `min_round_seconds: 3`, `player_connect_timeout_seconds: 180`; the three
  `harvest-*` variants differ only in `property_rights` and `seed`. Cert fixture: `num_agents 6`,
  six `certification.players` seating every one of the six bundled players
  (`commons-prompt, steward, cleaner, punisher, free-rider, random`), six
  `game_config.players`. `config_schema` `additionalProperties:false` with
  `num_agents {minimum:6,maximum:6}` and `minItems/maxItems 6` on `tokens` and `players`; its
  property set is exactly `CommonsConfig`'s fields plus `tokens`/`players` (checked
  programmatically — no variant carries a key the schema rejects). `game.replay_viewer =
  {"bundle":"static-replay-viewer"}`. `results_schema.reason` enum is exactly
  `["complete","deadline","no_players"]` and covers all 16 result keys.
  `ANTHROPIC_API_KEY_URI: secret://coworld/commons-family/anthropic_api_key` on the game runnable.
- `Dockerfile` builds both `/bin/commons-family` and `/bin/commons-family-player` `chmod +x`;
  `compose.yaml` service name `commons_family` matches `{{COMMONS_FAMILY_IMAGE}}`.

**Anti-name-leak**
- `observation()` takes aliases only (`engine.py:296-346`); aliases are a seeded permutation of
  `Cog-A…Cog-F` (`engine.py:227-229`). `tests/test_institutions.py:150-164` asserts none of six real
  policy names appears in any seat's serialised observation after three played rounds, and
  `:167-176` asserts no seat can see another's favourite or the seed. Real names appear only in
  `replay.policyNames` / `seats[].name` / `results.names` (`engine.py:557`, `:588`, `:608`) and in
  the `/global` snapshot (`server.py:566`) — the latter is what design.md:655 specifies. The viewer
  maps alias→policy name for non-baseline seats (`renderer.js:746-775`); CI's scorebug readout was
  `Cog-E 0.0 COMMONS PROMPT … Cog-D 0.0 RANDOM COG`, so both name spaces are present on screen.

**Tests** — all eight files exist and cover the note's §Tests list; `PYTHONPATH=src python -m pytest
tests/ -q` → **232 passed in 33.8 s** locally at the reviewed sha. `git log --numstat -- tests/`
over the whole run shows **zero deleted lines** in `tests/` (16+0, 62+0, and the initial 2140+0);
there is no `skip`, `xfail` or `pytest.mark` other than `parametrize` anywhere in `tests/`.

**Workflows** — `docker-smoke` and `wasm-viewer` in `ci.yml` are **byte-identical** to
`coworld-builder/templates/ci.yml` from `  docker-smoke:` to EOF (`diff` exit 0); only the `test`
job was replaced with pytest and the header/env substituted. `wasm-viewer` has `needs:
docker-smoke` and runs `viewer_smoke.mjs … --strict-text-bounds`; the only `if: always()` is on the
evidence upload. `coworld-release.yml` order is build manifest (:153) → certify (:167) →
upload-policies (:206) → upload-coworld (:304) → secret put (:342), with per-policy `player`
honoured through `softmax player use` / `unset` (:246-262, :283-286). `policies.json` has two
`PLAYER_PROMPT` champions and two scripted fillers, with champion #2 carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The placeholder gate
(`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files) finds nothing; the only surviving
angle-bracket names are the four documented residues (`<cow_id>`/`<sha>` in ci.yml:114, `<run_id>`
in release:21 and submit:17, `<name>:vN` in submit:31). `docker_smoke.sh` (mode 100755) enforces the
four seat-count invariants with `SEAT-COUNT FAIL:` prefixes at lines 112-153 and adds a player-exit
check the template lacks (lines 245-267).

**CI evidence at the reviewed sha** — run **32767219248**, `head_sha
5c6490440ccaf6f7db401607f52b669023af9208`, conclusion **success**, three jobs green (`test` 50 s,
`docker-smoke` 1 m 30 s, `wasm-viewer` 1 m 46 s). `grep -c "SEAT-COUNT FAIL" ` over the full run log
= **0**. docker-smoke: `game=commons_family seats=6`, `all 6 player containers exited 0`,
`smoke OK: seats=6 results=609B replay=43856B reason=complete`. wasm-viewer's
`Load the bundle in a real browser` step ran and printed
`{"loaded":true,"ms":284,"clock":"ROUND 1 OF 8 · SETTLED","scorebug":"Cog-E 0.0 COMMONS PROMPT …","feed_lines":147}`,
`scrub readouts: 0%="ROUND 1 OF 8 · SETTLED"  50%="ROUND 5 OF 8 · WAITING ON 6"  100%="ROUND 8 OF 8 · FINAL"`,
and `canvas text: 2236 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`.

---

## 3. Builder claims I verified as true

1. `shared/artifact_io.py` and `shared/log_shipper.py` are **byte-identical** to
   `coworld-meadow`'s (`diff -q`, both silent) — design.md:559.
2. coworld-meadow really has **no wasm viewer**: `find` over the clone returns no `.nim`, and its
   `static-replay-viewer/` holds a single hand-written `index.html` — design.md:707-714.
3. `replay-viewer/config.nims` differs from bullwhip's in exactly **three lines**: the output path,
   `EXPORT_NAME`, and `EXPORTED_FUNCTIONS`. Every other flag (`MODULARIZE=1`, `ENVIRONMENT=web`,
   `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `EXPORTED_RUNTIME_METHODS=HEAPU8`, `-O2`) is
   unchanged — design.md:725.
4. `replay-viewer/index.html` is bullwhip's 53-line page with **no node removed** — every id the
   note lists is present in the same nesting — plus the banner-marked block and the `fit()`→
   `relayout()` extension. See O6 for the one further edit in `static_replay.js`.
5. `tools/ci/viewer_smoke.mjs` is **byte-identical** to `coworld-builder/templates/tools/ci/
   viewer_smoke.mjs` — design.md:959.
6. `.github/workflows/coworld-submit.yml` differs from the template in **one comment line**;
   `coworld-release.yml` in the header comment and the two `env:` values.
7. `ci.yml`'s `docker-smoke` + `wasm-viewer` jobs are byte-identical to the template's.
8. `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed **mode 100755**
   (`git ls-files -s`).
9. The wasm module imports **only `std/json`** (`commons_family_replay.nim:14-15`) — design.md:726.
10. The whole test suite passes at the reviewed sha (232 passed) and no test was deleted, skipped or
    loosened during this run.

---

## 4. Could not determine

- **Whether the viewer renders the other three modules at all.** The cert fixture is
  `module: "cleanup"`, so `docker-smoke` produces a cleanup replay and `viewer_smoke.mjs` loads
  that one. `drawPatches`, `drawField`, `drawMushrooms`, `drawFlow` and `cfPatchGrid`
  (`renderer.js:295-511`, `index.html:137-160`) are never executed in CI. Settled by: a smoke run
  against a `harvest`/`allelopathic`/`mushrooms` replay, or a second cert/smoke fixture.
- **Whether a full-cap (140-rune) remark is legible** — O14 is an arithmetic inference from
  `drawBubble`'s 2-line cap and `maxW = pitch × 1.5`. Settled by: rendering a frame with a 140-rune
  `say` on all six seats at 360/960 px and reading `canvas_text.ellipsized`.
- **Whether the live LLM path works end to end.** No credentials exist in CI
  (`docker_smoke.sh:196-201` prints "no ANTHROPIC_API_KEY"), so `BedrockTransport` and
  `AnthropicTransport` are exercised only by unit stubs. Settled by: one hosted episode, or a smoke
  run with `ANTHROPIC_API_KEY` set.
- **Whether O1's exception path is reachable in the hosted environment** — it needs a credential the
  provider rejects (401/403) or a response shape the parser does not expect. I reproduced it with a
  stub; I cannot tell how likely the hosted sidecar is to produce it.
- **`grade` values against a real bundle.** `commons_grader.run()` is only driven through
  `build_grade` in tests (`tests/test_grader.py`); the zip/bundle read path
  (`commons_grader.py:76-81`) is never executed in CI.
