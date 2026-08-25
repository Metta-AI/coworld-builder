# r1 review — fruit-market

Repo: `Metta-AI/cogame-fruit-market` @ `43e34e150f8871b40f6a3e86034b4bf2ce487bfd` (main)
Design note: `runs/2026-08-25-fruit-market/design.md` (byte-identical to
`docs/plans/2026-08-25-fruit-market-design.md` — verified with `diff`, no output)
Checklist read: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15)
Starter compared: `/workspace/starters/coworld-ctf` @ `44be957`
Files opened: 47 (all of `src/`, `replay-viewer/`, `tests/`, `tools/ci/`, `client/*.js|html`,
the three workflows, `Dockerfile*`, `compose.yaml`, `coworld_manifest_template.json`)
CI evidence: run **32900609480** (push, head sha `43e34e1`, conclusion `success`), full log read.

Findings are numbered F1…F23 and are **observations**, not verdicts. Each carries the
checklist item it bears on so the judge can categorise; I do not categorise or rank.
Five coordinator-accepted deviations (water 72+48, banana-tree rows, the economy retune,
the ratio form of gate (c), the hauler rendezvous) are **not** filed as findings — I checked
each was implemented consistently and report that under §Traced.

---

## Findings

### F1 — `coworld certify` is invoked without `--timeout-seconds 300`
- Where: `.github/workflows/coworld-release.yml:167-176`
- Observed: the certify step runs
  `uvx --from "$COWORLD_PKG" coworld certify dist/coworld_manifest.json --no-open-report`.
  `grep -n "timeout-seconds"` over the file returns only lines 311 (`--timeout-seconds 900`,
  on `upload-coworld`) and 313 (`--hosted-smoke-timeout-seconds 1800`). There is no
  `--timeout-seconds` on the certify invocation.
- Note says: design.md:1033-1035 — "The certify step in `coworld-release.yml` passes
  **`--timeout-seconds 300`** (cooperative-hunting, 2026-08-25) so the 60 s default can never
  truncate it."
- Bears on: checklist 12 (release order and scaffold). The *order* build → certify →
  upload-policies → upload-coworld → secret put is correct (lines 153, 167, 206, 304, 342);
  only the flag is absent.

### F2 — a seat with neither `PLAYER_PROMPT` nor `PLAYER_SCRIPTED` becomes an LLM seat, not `hauler`
- Where: `src/fruit_market_player.nim:20-30` (`DefaultPrompt`), `:43-46`
- Observed:
  ```nim
  var prompt = getEnv("PLAYER_PROMPT")
  let scripted = getEnv("PLAYER_SCRIPTED").strip()
  if prompt.len == 0 and scripted.len == 0:
    prompt = DefaultPrompt
  ```
  The frame sent is `{"type":"prompt","prompt":<DefaultPrompt>,"scripted":""}`, and
  `server.nim:376-380` maps `scripted: ""` to `skNone`, so `decideAll` opens that seat for an
  LLM call (`llm.nim:637-644`).
- Note says: design.md:359-360 — "a seat that sets neither is `PLAYER_SCRIPTED=hauler`".
- Consequence traced: offline (no credentials) `newLlmClient` disables itself
  (`llm.nim:103-106`) and the seat plays `hauler` anyway, so `docker_smoke` and offline
  certification are unaffected. With credentials, an unconfigured seat plays the broker
  prompt rather than the scripted baseline.

### F3 — `client/broadcast_core.js` is byte-identical to the starter's, not forked
- Where: `client/broadcast_core.js` (1407 lines) vs
  `/workspace/starters/coworld-ctf/client/broadcast_core.js` (1407 lines) —
  `diff` produces **zero** changed lines.
- Note says: design.md:821-825 — "`client/broadcast_core.js` is **forked** (it is paintbot's
  renderer …): the board draw becomes the tile grid, rivers, groves, stalls, fruit, cogs,
  offer bubbles and hunger bars."
- Observed instead: every game-specific pixel is produced server/wasm-side in
  `src/fruit_market/global.nim` as sprite images pushed over the sprite protocol —
  `bakeBand` (terrain, :217), `barImage` (hunger/stamina bar, :257), `bubbleImage`
  (offer bubble, :275), `aliasImage` (:318), `tagImage` (STARVING/EXHAUSTED, :337), and
  `buildPacket` (:426-539) which anchors them. `broadcast_core.js` renders them unchanged.
  So the readouts the note demands **are** drawn; the file the note names as their home is
  untouched.
- Bears on: checklist 14 only insofar as it constrains `chrome_common.js` and
  `replay_broadcast.html` (both verified — see §Traced); `broadcast_core.js` is not named there.

### F4 — the appended block's beat markers bypass `chrome_common.markBeat`, so `?spoilers=0` does not hold them back
- Where: `client/replay_broadcast.html:2461-2496` (`buildMarketBeats`) vs
  `client/chrome_common.js:537` (`var markerEls = []`), `:558` (`markerEls.push(el)`),
  `:488-495` (`applySpoilers` walks `markerEls` only).
- Observed: `buildMarketBeats` builds its own `document.createElement('button')`, sets
  `className = 'beat-marker ' + b.k`, positions it with `style.left`, and appends it to
  `#scrub` (`:2479-2491`). It never calls `C.markBeat`, so the element never enters
  `markerEls` and never gets `el.__tick`. `applySpoilers` (chrome_common.js:488) therefore
  never hides it. With `?spoilers=0`, every fruit-market beat — including `gameover` — is
  visible on the rail from the first frame.
- Note says: design.md:864-866 — "The whole beat timeline ships on the first HUD frame …
  and `?spoilers=0` still holds beats back until the playhead reaches them."
- Bears on: checklist 14(d). The markers *are* labelled `<button>`s that seek to their tick
  (`seek('s:' + b.t)`, :2489) with `aria-label` (:2485) and CSS for all five emitted kinds
  (:2406-2410 plus the inherited base rule at :603-610), which is what 14(d) requires
  literally; the spoiler gate is the note's addition.

### F5 — order-book rows omit the stall and never strike through
- Where: `src/fruit_market/broadcast.nim:104-127` (`bookJson` emits
  `s, name, give, giveN, want, wantN, unfunded` — no stall, no cleared flag);
  `client/replay_broadcast.html:2528-2536` (`renderBook` renders name + `N 🍎 → N 🍌` only);
  `client/replay_broadcast.html:2393` defines `.fm-book-row .fm-book-stall` and
  `:2316` hides it under 640 px, but nothing ever emits an element with that class.
- Note says: design.md:895-897 — "up to eight rows … `ASH  3 🍎 → 2 🍌  north` — hollow when
  unfunded, struck through when it clears."
- Observed: hollow-when-unfunded **is** implemented (`.fm-book-row.unfunded`, :2391, fed by
  `r.unfunded`, :2529). The stall column and the strike-through are not.

### F6 — the guild plates' `trades` and `volume` are hardwired to zero and unread
- Where: `src/fruit_market/broadcast.nim:59-62` declares `var total = 0; trades = 0; volume = 0`
  and `:73-74` emits `"trades": trades, "volume": volume` — neither local is ever assigned
  after initialisation. No consumer reads them: `grep` for `trades` / `volume` in
  `client/replay_broadcast.html` finds no plate reader.
- Note says: design.md:891-894 — the plate's big number is the guild total score "and
  underneath the guild's trade count and mean rate."
- Observed: the big number (`lives` = guild total score) is correct (`:66`, asserted by
  `tests/test_broadcast.nim:41-48`); the trade count and mean rate are neither computed nor drawn.

### F7 — `say` is its own feed row from the `order` event, not the quoted tail of the `offer` row
- Where: `client/replay_broadcast.html:2588-2601`
- Observed: `case 'offer'` pushes `"<ALIAS> posts N 🍎 for N 🍌"` with no tag and no quote;
  `case 'order'` pushes a separate `"<ALIAS> “say”"` row and puts the
  `<span class="badge">auto</span>` tag there when `e.source` is `fallback` or `scripted`.
- Note says: design.md:905-908 — one row per `offer` "(`DUNE posts 6 🍎 for 4 🍌`, tagged
  `auto` when `source` is `fallback` or `scripted`), … plus the seat's `say` as the quoted
  tail of its `offer` row."
- Related: the `offer` event carries no `source` field at all
  (`src/fruit_market/events.nim:89-95` emits `seat, give, giveN, want, wantN, clamped`), so the
  note's tagging of the offer row is not expressible from the recorded event as designed.
  `source` is on the `order` event (`events.nim:135`), which is where the code puts the tag.

### F8 — the live `/global` chrome frame always carries an empty `events` array; `chromeFrame` is dead code
- Where: `src/fruit_market/server.nim:110` — `chromeViewOfSim(gs.sim, newJArray(), sendLead)`
  inside `broadcastLocked`, the only path that feeds live spectators
  (`:113` `viewer.buildPacket(... buildStateJson(view))`).
- Observed: `view.events` is always a fresh empty array, so `buildStateJson`'s
  `"events"` (`broadcast.nim:148`) is `[]` on every live frame and the game block's
  `applyMarketEvent` loop (`replay_broadcast.html:2669-2673`) never runs live. The static
  replay path is unaffected: `fruit_market_replay.nim:95-99` passes `eventsBetween(before, after)`.
  Additionally `proc chromeFrame` (`server.nim:77-84`) is defined and never called
  (`grep chromeFrame src/fruit_market/*.nim` → one hit, the definition).
- Note says: design.md:738 — `WS /global` is "live spectator: paintbot's sprite protocol +
  the chrome `TextMessage`", and design.md:904-908 describes the feed's rows. The note does
  not separately promise a live feed, so this is a live-path/replay-path asymmetry rather
  than a stated-behaviour miss.

### F9 — `tests/test_baseline.nim` runs 3 seeds (note: 12) and asserts 50 ms/round (note: 1 ms)
- Where: `tests/test_baseline.nim:79` — `for seed in 1 .. 3:`; `:101` — `check worstRoundMs < 50.0`
- Note says: design.md:1080-1087 — "For **12 seeds** × 720 ticks on all four variants … and
  neither takes more than **1 ms per round**."
- Observed: everything else in that list is asserted — enums (`:31-35`), offer bounds
  (`:38-41`), the six-action vocabulary (`:141-143`), board legality/inventory/hunger/stamina/
  monotone scores/no shared cell (`:49-66`), and two opposite haulers clearing within two
  ticks on every variant (`:103-127`). The two numbers above are the only relaxations.
  `git log --all --oneline -- tests/` returns exactly one commit (`43db808`), so no test was
  loosened after the fact — this is how the file was first written.
- Bears on: checklist 1 (second half) and 7.

### F10 — `tests/test_llm.nim` omits three assertions the note's test list names, and its batch test is tautological
- Where: `tests/test_llm.nim:155-176`
- Observed, quoting the batch test:
  ```nim
  var open = 0
  for slot in 0 ..< Seats:
    scripts[slot] = skNone
    connected[slot] = true
    if scripts[slot] == skNone and connected[slot]:
      open.inc
  check open == Seats
  ```
  It counts a variable it just assigned; it never calls `decideAll` and never inspects a
  `RequestBatch`. Absent entirely from the file: (a) a stubbed transport that times out /
  429s / 403s / returns junk producing `hauler` orders marked `source: "fallback"` — the
  three "degrade, never hang" tests (`:108-153`) all set `client.disabled = true`, which
  routes through `llm.nim:640-643` and yields `source: osScripted`, so **no test asserts
  `osFallback` is ever set**; (b) the named `max_tokens` error.
- Note says: design.md:1102-1109 — "a stubbed transport that times out, 429s, 403s or returns
  junk produces `hauler` orders for those seats, never raises, and marks `source: "fallback"`;
  a `max_tokens` stop raises the named 'cut off at max_tokens' error; **one batch carries all
  open seats** (assert `RequestBatch.len == openSeats`, i.e. 8 on round 1)".
- The code itself does implement all three: `llm.nim:676-679` sets `osFallback`;
  `llm.nim:518-521` raises `"reply cut off at max_tokens mid-JSON: …"`; `llm.nim:650-659`
  builds one `RequestBatch` over `open` and calls `curl.makeRequests(batch, timeoutSeconds)`.
- Bears on: checklist 8 (which requires the behaviour, not the test) and the
  simultaneous-decision addendum.

### F11 — no test asserts the viewer's display equals the recorded state frame by frame
- Where: `tests/test_replay.nim:98-103` is the closest:
  ```nim
  let replay = parseReplay(raw)
  check replay.frames.len == sim.ticksPlayed
  check replay.board.trees.len == 48
  check replay.maxTick() == sim.ticksPlayed - 1
  check replay.rateAt(0) == CanonicalRateX100
  ```
  It checks lengths and two scalars, not per-frame equality of `frame.c` / `frame.o` / `frame.r`
  against `sim.frames`. `grep 'frames\['` over `tests/` returns one hit
  (`test_broadcast.nim:45`), which compares a replay-derived value to another replay-derived
  value.
- Structural context: the design deliberately records **state**, not inputs
  (design.md:676-679, 1178-1179 "Re-simulating playback … there is no replay-hash mismatch
  mode"), so "replay the events through the sim" is not the shape this game has. The viewer
  reads the same `Frame` records the sim wrote (`sim.nim:223-258` writes them,
  `broadcast.nim:302-312` reads them positionally through `frame.cogAt` / `frame.offerAt`), and
  the live and replay chrome frames are built by two procs with the same output shape
  (`chromeViewOfSim` :234, `chromeViewOfReplay` :278).
- Bears on: checklist 2 ("A test asserts it").

### F12 — the `exhausted` event fires only from the starvation drain, not from a move/harvest that empties stamina
- Where: `src/fruit_market/sim.nim:207-215`
  ```nim
  else:
    cog.starvingTicks.inc
    let before = cog.stamina
    cog.stamina = max(0, cog.stamina - sim.config.starveDrain)
    if cog.stamina == 0 and before > 0:
      cog.exhausted = true
      sim.emit(SimEvent(kind: evExhausted, seat: slot))
  cog.exhausted = cog.stamina == 0
  ```
  The emit sits inside the `hunger == 0` branch. A cog that reaches 0 stamina by paying a
  move cost equal to its stamina (`sim.nim:117`, the refusal at `:111` is `cost > cog.stamina`,
  so `cost == stamina` is allowed) or by a harvest at stamina 1 (`sim.nim:64`) has
  `exhausted` set at `:215` with **no** `exhausted` event and no feed row.
- Note says: design.md:663 — event table row `exhausted | t, seat | step 8, stamina reached 0`.
  design.md:247-248 attaches the emission to the starve branch, so the note is internally
  ambiguous; the code implements the narrower reading.

### F13 — the forfeit replay carries zero frames and the viewer's own parser rejects it
- Where: `src/fruit_market/server.nim:203-209` (no seat connected → `state.sim.forfeit()` →
  `finishEpisode`), `src/fruit_market/sim.nim:343-357` (`finish` appends the `end` event and
  the `gameover` beat but no frames), `src/fruit_market/replays.nim:180-182`:
  ```nim
  if frames.isNil or frames.kind != JArray or frames.len == 0:
    raise newException(FruitMarketError, "replay carries no frames")
  ```
- Observed: on the forfeit path `sim.frames` is empty (no `stepTick` ever ran), so the written
  replay has `"frames": []`. `results.json` and the replay bytes are both written
  (`server.nim:154-157`), but loading that replay in the static viewer takes the failure path
  and sets `data-replay-error`.
- Note says: design.md:323 — forfeit: "all zero; results + replay are still written."
  The note does not say the forfeit replay must be playable.

### F14 — the test-only `mirror` kernel is selectable in the shipped image
- Where: `src/fruit_market/sim_types.nim:245-252`
  ```nim
  proc parseScriptKind*(text: string): ScriptKind =
    case text.strip().toLowerAscii()
    of "": skNone
    of "homesteader", "autarky": skHomesteader
    of "mirror": skMirror
    else: skHauler
  ```
  `server.nim:380` routes the player's `scripted` field through it, so
  `PLAYER_SCRIPTED=mirror` fields `mirrorOrder` (`scripted.nim:95-128`) in production.
- Note says: design.md:346-347 — "`mirror` lives only in the test; it is not a shipped policy."
- It is not declared in `coworld_manifest_template.json` or `tools/ci/policies.json`, so
  nothing the platform seats will select it.

### F15 — policy names reach the replay and `results.names` without `cleanText`
- Where: `src/fruit_market/server.nim:413-415` (`policyNames` built from `config.players[].name`),
  `sim_state.nim:102-106` (stored verbatim), `replays.nim:50` (`policyNames.add(%sim.policyNames[slot])`),
  `sim_state.nim:183` (`names.add(%sim.policyNames[slot])` in `results.json`).
  `grep cleanText src/` returns four call sites: `llm.nim:553,554,672` and `server.nim:392`.
  None covers policy names.
- Note says: design.md:485-486 — "The same rune-safe truncation applies to **every** string
  that reaches the replay".
- Practical scope: these are platform-supplied policy identifiers; `fruit_market.nim:55-56`
  fills any missing entry with a `CogAliases` value.
- Bears on: checklist 9 (whose test requirement — multi-byte input at the cap asserted valid
  UTF-8 — is met for `say`/`notes`/error text by `tests/test_replay.nim:108-158`).

### F16 — the adaptive lobby needs **all** `numAgents` sockets, so a partial roster burns the full 180 s
- Where: `src/fruit_market/server.nim:178-192`
  ```nim
  ready = connectedCount >= config.numAgents and
    registeredCount >= connectedCount
  ```
- Observed: with 6 of 8 seats connected and registered, `ready` stays false and the loop polls
  `sleep(200)` until `connectDeadline` (gameStart + `playerConnectTimeoutSeconds` = 180 s).
  It is bounded — there is no hang — and the play deadline is measured from the same
  `gameStart` (`:172`, `:220`), so the lobby time comes out of the 720 s play budget rather
  than adding to it.
- Note says: design.md:596-598 and 750-751 — "the lobby returns as soon as every connected
  socket has registered". Taken literally that condition is true at t=0 with zero connections,
  so the code's extra `connectedCount >= numAgents` term is load-bearing; the note's phrasing
  and the code differ on the partial-roster case.
- Bears on: checklist 5 (bounded — it is).

### F17 — `minTurnSeconds` is a `sleep()` on the round loop, not a floor the sim ticks through
- Where: `src/fruit_market/server.nim:249-253`
  ```nim
  if lastBatchStart > 0.0 and config.minTurnSeconds > 0:
    let wait = config.minTurnSeconds.float - (epochTime() - lastBatchStart)
    if wait > 0.0:
      sleep(int(wait * 1000.0))
  ```
  Nothing steps the sim during the wait; `runRound` runs after `decideAll` returns (`:257-261`).
- Note says: design.md:388-389 — "It is a floor, not a sleep on the critical path — the loop
  keeps stepping sim ticks while it waits."
- Wall-clock effect traced: per-round cost is `max(minTurnSeconds, batch+retry)`, i.e. the
  note's own "typical: max(18, ~8) × 12 ≈ 216 s" and "worst: 12 × 40 = 480 s" arithmetic is
  unchanged. The `sleep` is bounded by `minTurnSeconds` (≤ 60 by the schema).

### F18 — a seat whose socket dies mid-episode keeps playing its LLM prompt, not `hauler`
- Where: `src/fruit_market/server.nim:395-403` — the `CloseEvent` branch deletes the socket
  from `socketSlots`/`playerSockets` and the global sets, but never assigns
  `state.connected[slot] = false`. `decideAll` (`llm.nim:640`) gates on `connected[slot]`, so
  the seat stays open for LLM calls with its last registered prompt.
- Note says: design.md:594-595 — "A seat that never connected, or whose socket dies
  mid-episode, plays `hauler` for every remaining round."
- The never-connected half **is** implemented (`connected[]` starts false;
  `tests/test_llm.nim:125-137` asserts it) and nothing blocks on the socket, so the
  degrade-never-hang property is intact.

### F19 — the worst-case renderer fixture re-implements the anchor arithmetic rather than loading the shipped renderer; `canvas_text.total` is 0 on the real bundle
- Where: `tools/ci/renderer_fixture.html:92-106` (`plate()`), `:108-167` (`drawBoard`)
- Observed: the fixture draws with its own `ctx.fillText` and clamps every caption into the
  canvas before drawing —
  `var y = Math.max(2, Math.min(top, ctx.canvas.height - h - 2));` (:99) and the matching `x`
  clamp (:100) — so `never_inside` is 0 by construction of the fixture, not by the shipped
  renderer's arithmetic. The shipped renderer is `src/fruit_market/global.nim` (pixie draws
  every board string into a **sprite bitmap**; there is no `fillText` on the shipped path), and
  the CI log confirms the consequence:
  `Load the bundle in a real browser … canvas text: 0 drawn, 0 never inside the canvas
  (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` — run 32900609480, log line 4547.
  The fixture step reports `canvas text: 135 drawn, 0 never inside …` (log line 4567).
- Note/checklist say: checklist 15 — `total: 0` "is not evidence of anything", and the required
  mitigation is a fixture "that loads the real `client/renderer.js`, hands it a frame built to
  hurt … and is driven by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step. The
  fixture asserts its own strings are still full-length."
- What the fixture **does** satisfy: it is its own `ci.yml` step (`ci.yml:339-353`) driven with
  `--strict-text-bounds`; it renders at five canvas sizes including 360 px (:38-42); it asserts
  its `say` is exactly at the cap (`check(SAY.length === MAX_SAY, …)`, :67) and that the feed
  line still contains it (:166); it sets `data-replay-loaded` (:184) and `data-replay-error`
  on failure (:178).
- What I separately verified about the shipped anchors, since the fixture does not exercise
  them: `global.nim:513` places the bubble at `max(0, py - 10 - BubbleH - 4)` and `:525` the
  tag at `max(0, py - 10 - TagH - BubbleH - 8)` — both clamped at 0, so the cogchemists
  negative-y failure cannot occur. Horizontal: bubble `x = cog.x*48 + (48 - w) div 2` with
  `w ≈ 114` (`:284`) gives `x ≈ 15` at the leftmost legal column (x=1) and right edge
  `≈ 1521 < BoardW 1536` at x=30, so it fits at both extremes. The board draws **no**
  LLM-authored text at all: `say`/`notes` appear only in the DOM feed
  (`replay_broadcast.html:2594-2600`), which `dom_text_smoke.mjs` covers at 13 viewports
  (log line 4578: `{"ok":true,"viewports":[{"width":360,"chips":8,"book":8,"feed":4}, …]}`).

### F20 — `+` / `-` speed keys and `f` (auto-skip) are sent by the page and ignored by the viewer
- Where: `client/replay_broadcast.html:2214-2215` sends `'+'` / `'-'`;
  `src/fruit_market/global.nim:546-561` handles `' '`, `'.'`, `'b'`, `','`, `'e'`, `'r'`,
  `'f'` (explicit `discard`, :554) and `'1','2','3','4','8','6'`, and falls through to
  `else: discard` for `'+'` / `'-'`.
- Note says: nothing about speed keys. Recorded because `#btn-skip` (`:1190`) and the two
  keys are inherited controls that now do nothing; the numeric speed keys 1/2/3/4/8/6 do work.

### F21 — nimby pin drift between the two Dockerfiles
- Where: `Dockerfile:15,19` and `.github/workflows/ci.yml:35` pin **0.1.26**;
  `Dockerfile.replay-viewer:11-12` pins **0.1.27** (with its own sha256).
  `ci.yml:34` says "Pins mirror the Dockerfile build stage; bump both together."
- Observed: both images build green in run 32900609480 (`docker-smoke` → `Build image` success;
  `wasm-viewer` → `Build the static replay viewer bundle` success).

### F22 — `docker_smoke.sh` checks the results *shape*, not `game.results_schema`
- Where: `tools/ci/docker_smoke.sh:275-325` — it asserts `results.json` exists, is UTF-8 JSON,
  is a non-empty object, that `names` and `scores` (if present) have length `seats`, prints
  `reason`, and asserts the replay parses as JSON.
- Note says: design.md:1129-1130 — "validates `results.json` **against the results schema**".
- The file is otherwise the coworld-builder template verbatim in behaviour, and the four
  seat-count invariants checklist 6 names are all present and all prefixed `SEAT-COUNT FAIL:`
  (`:110-151`) — see §Traced.

### F23 — two assertions on the note's test list are absent from the suites that own them
- `tests/test_broadcast.nim` has no "every feed row's text is ≤ the caps" check — the file's
  180 lines cover teams/roster/lead/beats/over/book/clock and the eight page-provenance
  assertions, but no feed-row length assertion. Note: design.md:1124.
- `tests/test_sim.nim:275-291` asserts the same `gameHash` "twice in one process"; the note
  asks for "twice in one process **and across a fresh server**". Note: design.md:1070-1071.

---

## Traced and consistent

**Nine-step tick order and the rules** — `src/fruit_market/sim.nim:262-278` runs exactly
regrow(1) → kernel(2) → harvest(3) → move(4) → offer book(5) → matching(6) → eat(7) →
hunger/stamina(8) → record(9), each in ascending slot order, matching design.md:206-250.
Harvest yields `yieldOwn`/`yieldOther` with the 12/96 cooldowns and a `spill` above `invCap`
(`:46-74`); moves charge `moveStaminaLand 1` / `moveStaminaWater 10` and set
`moveCooldown 2` / `waterMoveCooldown 4`, refuse when `cost > stamina`, treat a lower slot's
new cell as occupied, and emit `cross` (`:84-126`); the eat rule is exactly the note's
crave/any/none gating with `min(HungerMax, …)` and `craveScore 5`/`ownScore 1` (`:158-188`);
hunger drains at `tick mod 4 == 0 and tick > 0` and starvation drains 2/tick with regen only
above hunger 0 (`:192-219`). Scoring `S = 5·craved + 1·own` and `win[i] = (S_i == max S)` at
`sim_state.nim:178-187`.

**Accepted deviation 1 (water 72 + 48 = 120)** — `board.nim:76` makes `d == 2` and `d == 5`
water; `tests/test_map.nim:26-39` asserts outer 72, inner 48, total 120. I recomputed both
perimeters (88 − 8d): 72 and 48. Consistent everywhere; `configJson` ships the cell list
(`sim.nim:388-393`) and `parseReplay` rebuilds terrain from it (`replays.nim:143-160`).

**Accepted deviation 2 (banana rows y=7/y=10)** — `board.nim:22-32` lists exactly
x ∈ {8,9,11,12,14,15,17,18,20,21,23,24} on both rows, 24 trees, all at `d == 6`, leaving rows
8–9 as a clear corridor. `tests/test_map.nim:84-90` asserts zone connectivity without water,
which is the assertion that would have caught the note's original list.

**Accepted deviation 3 (economy retune)** — `sim_types.nim:58` `EatCooldown = 24`, `:68`
`HarvestCooldownOther = 96`; the manifest's schema defaults agree (`eatCooldown` default 24,
`harvestCooldownOther` default 96 with the max raised to 240 so 96 is legal), and
`tests/test_manifest.nim:140-161` asserts schema-default ↔ `defaultGameConfig()` equality for
both. `deep-rivers` carries `moveStaminaWater: 32` in the manifest and in both test variant
tables (`test_baseline.nim:19`, `test_feasibility.nim:18`), and `variantId()`'s
`moveStaminaWater >= 18` branch (`sim_config.nim:100`) still resolves it — asserted by
`tests/test_manifest.nim:163-168`.

**Accepted deviation 4 (gate (c) as a ratio)** — `tests/test_feasibility.nim:103-109` asserts
`deep.homesteader < open.homesteader` and `deep.hauler/deep.homesteader >
open.hauler/open.homesteader`, with the reasoning recorded in-place.

**Accepted deviation 5 (hauler rendezvous)** — `scripted.nim:35-41`
`StallId((max(1, round) - 1) div 2 mod 4)` gives N,N,E,E,S,S,W,W,N,… as claimed;
`:47-60` leaves the canonical offer standing while restocking, and
`tests/test_baseline.nim:42-47` narrows the funded-at-posting assertion to `jMarket` orders
with the reason written out.

**Offer book** — `market.nim:56` uses `mirrors()` (`sim_types.nim:257-261`, all four fields
swapped); `:59` `dist > tradeRadius` → skip (radius 3; `tests/test_market.nim:61-68` asserts
3 clears / 4 does not); `:61-64` blocks a pair that would breach `invCap` on receipt;
`candidateLess` (`:19-30`) implements volume desc → distance asc → low slot asc → high slot
asc exactly, and `tests/test_market.nim:102-123` pins the execution order on a four-pair board;
`executeTrades` (`:74-81`) enforces one trade per cog per tick **and** per round and consumes
both offers (`:89-90`); `clampOfferN` (`:126-129`) clamps to `[1, offerMax]` and flags,
asserted at `test_market.nim:169-174` and end-to-end at `test_llm.nim:71-76`.
`refreshUnfunded` runs on every tick from step 5 (`sim.nim:151-154`) and emits `unfunded` once
per transition with reason `stock`/`full` (`sim_state.nim:78-89`).

**Kernel and Dijkstra** — `kernel.nim:141-167` implements `harvest` (nearest ripe tree of the
fruit, else walk to the nearest tree and wait), `market` (named stall or `bestStall`, standing
within Chebyshev 1 via `stallTargets`, :96-104), `trek` (far grove only, `groveZoneFor(other)`)
and `rest`. `board.nim:155-192` is a weighted Dijkstra with `LandCost = 1`, `WaterCost = 8` and
N,E,S,W expansion (`StepDx/StepDy`, :141-142); it is deterministic (a strict `<` update rule
plus a fixed frontier scan). `bestStall` (:106-117) ties to north, east, south, west.
`tests/test_baseline.nim:129-144` asserts the kernel only ever emits the six actions.

**Decision path** — `llm.nim:646-674`: one `RequestBatch` per attempt over all open seats,
issued with `curl.makeRequests(batch, client.timeoutSeconds)` (curly's `makeRequests` is
`{.raises: [].}` and blocks until every request completes or the whole-second timeout fires —
verified in `~/.nimby/pkgs/curly/src/curly.nim:711-722`); `for attempt in 0 .. 1` is
retry-exactly-once with `RetryHint` appended (`:29-31`, `:653-654`), the hint text matching
design.md:586-588 word for word; anything still open lands on
`scriptedOrder(sim, slot, skHauler)` with `source = osFallback` (`:676-679`) and the log line
`fruit-market llm: seat N falling back to scripted order` (`:677`). 401/403 sets
`client.disabled` (`:502-505`) and both the batch loop (`:647`) and the seat-open loop
(`:640`) honour it; 429 raises and re-opens the seat for the next round (`:506-508`).
`bedrockModelIds()` is haiku-only with a `BEDROCK_MODEL` override (`:50-57`); no
`output_config.effort` (`:492`); `maxOutputTokens = max(1000, config.maxOutputTokens)`
(`:79`); credential order sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` → disable
(`:82-106`). `extractJsonObject` (`:462-474`) takes the first `{` to the last `}`, so fences
and prose on both sides parse — asserted at `test_llm.nim:24-37`.

**Every wait and its bound** — lobby loop bounded by `gameStart + playerConnectTimeoutSeconds`
with `sleep(200)` polls (`server.nim:173-192`); LLM batch bounded by `llmTimeoutSeconds`
(rejected below 1 s and rejected non-integral at `sim_config.nim:178-188`); the pacing sleep
bounded by `minTurnSeconds` (schema max 60); the play deadline
`gameStart + episodeTimeoutSeconds × 0.6` read from `COWORLD_TIMEOUT_SECONDS` when present and
1200 otherwise (`server.nim:213-223`), checked at each round boundary → `endEarly()` →
`finish("deadline","deadline")` (`server.nim:235-240`, `sim.nim:359-363`); `sleep(500)` then
artifact writes with curly's 60 s default timeout, then `sleep(grace*1000)` with
`shutdownGraceSeconds = 20`, then `quit(0)` (`server.nim:152-167`). Arithmetic:
worst case ≤ 180 s lobby + 12 × max(18, 20+20) = 180 + 480 = 660 s < 720 s, so the deadline is
a backstop rather than the normal exit; if it *did* fire, the check is at the top of the loop,
so settle could be one round (≤ ~41 s) later — still far inside 1200 s. Player side: whisky
`receiveMessage(200)` in a `try`, exit 0 on a dead socket, exit 0 on `final`
(`fruit_market_player.nim:62-112`). A bad player token gets `respond(401)`, never a hang
(`server.nim:307-314`). `mummy.send` is `{.raises: [].}` (verified in
`~/.nimby/pkgs/mummy/src/mummy.nim:262-266`), so the broadcast/`final` loops cannot throw out
of the game thread.

**String truncation** — `cleanText` (`sim_state.nim:42-49`) strips, folds newlines to spaces,
and cuts with `runeSubStr(0, limit-1) & "…"`, i.e. on rune boundaries, at
`MaxSayLen 80` / `MaxNotesLen 320` / `MaxErrorLen 200` (`sim_types.nim:81-83`). Applied to
`say` and `notes` at parse time (`llm.nim:553-554`), to LLM error text before logging
(`llm.nim:672`) and to bad-frame errors (`server.nim:392`). The player prompt is cut with
`runeSubStr` at 4000 (`server.nim:374-375`). `tests/test_replay.nim:108-158` feeds multi-byte
runes past both caps, asserts `validateUtf8 == -1` on the whole replay and on every recorded
`say`/`notes`, and asserts `runeLen <= cap` — checklist 9's exact test.

**Replay writer** — `replays.nim:76-91` emits `protocol: "fruit-market.replay.v1"`, `game`,
`gameVersion`, `seed`, `names` (aliases), `policyNames`, `colors`, `farmTypes`, `config`,
`frames`, `series.rate`, `beats`, `events`, `results` — the note's schema key for key
(design.md:682-709). `configJson` (`sim.nim:386-438`) carries water cells, all 48 trees, the
four stalls, the eight spawns and all 25 rule constants; `tests/test_replay.nim:71-82` lists
and checks every one. `beats` last row is `gameover` at the final tick (`sim.nim:352-357`,
asserted `test_replay.nim:84-96` and `test_broadcast.nim:69-79`). Strict UTF-8, one JSON
document, `< 8 MiB` (asserted `:29-33`, `:105-106`; the real CI replay was 169 339 B —
log line 2679). `results.json` matches design.md:765-782 field for field
(`sim_state.nim:162-214`), including `mean_rate_x100` as the banana-volume-weighted mean
(`market.nim:106-107`).

**Viewer provenance** — `client/chrome_common.js` is **byte-identical** to the starter's
(`diff` silent; md5 `80ea4eb19cee21cb61fb1f009f1f45ab` on both). `replay-viewer/config.nims`
differs from the starter's in exactly four hunks: two comment renames, the emitted name
`fruit_market_replay.js`, and the export list renamed `_fm_*` with `_ctf_mismatch_tick`
dropped — **no `-s MODULARIZE=1`, no `EXPORT_NAME`** (`grep` returns nothing), and the worker
bootstraps with `Module.onRuntimeInitialized` (`static_replay_worker.js:165`): the matched
pair checklist 13 demands. `static_replay.js` differs from the starter's in exactly two
places — the added
`document.documentElement.setAttribute('data-replay-error', …)` in `showFailure` (:15-17) and
the worker name string (:173); `data-replay-loaded='true'` is the starter's own line (:147).
`static_replay_worker.js` differs only in `ctf_*` → `fm_*` and the mismatch-tick removal.
`replay-viewer/fruit_market_replay.nim` exports `fm_load_replay`, `fm_frame`, `fm_input`,
`fm_packet_ptr/_len`, `fm_error_ptr/_len`, `fm_stage_ptr/_len`, keeps `stampStage` and the
`emscripten_exit_with_live_runtime()` epilogue, reads the load packet directly rather than
re-deriving via `packetAt(0)` (:51-61), and converges a queued seek with
`SeekTicksPerFrame = 240` (`global.nim:563-574`). `os.getAppDir` is guarded by
`when not defined(emscripten)` with the working directory tried first (`global.nim:102-116`);
that is the only `getAppDir` in the tree.

**`client/replay_broadcast.html` provenance** — I diffed lines 1–2283 (everything above the
banner at :2284) against the starter's 4165-line page. Every one of the 1898 removed lines
belongs to a family the note authorises: the `#povBadge` / `#fpv*` / `#viewpanel` / `#minimap`
/ `#zoombar` CSS block (starter lines 525-836), `#mmwarn` (1014-1036), the
`body[data-noviewpanel]` rule, the `#viewpanel`/`#mmwarn`/`#povBadge`/`#fpv` markup
(1503-1552), the eye-level PiP cog art (1638-1704), the `?viewpanel=0` param, `syncViewUi` /
`onTransform`, `renderPov` / `renderMismatch` / `ingestFpMap`, the 1130-line pov+FPV
raycaster block (2273-3402), the povBadge click handler, and the zoom/pan keyboard + minimap
+ pinch block (3802-4106). The 16 added lines are: the `#lockerroom` `pointer-events: none`
(:351-353), `APPLES PER BANANA` (:429), `Score` (:597), one comment rename, the simplified
`onFirstFrame`, and the five-line `window.FruitMarketBlock.onFrame(s, send, C)` call
(:543-547) — the coordinator-accepted single added line plus its comment. Sections 1–5 of the
starter's CSS, `#stage`, `#board`, `#chrome`, `#scorebug`, `#plates-l/r`, `#clock*`,
`#bannerlane`, `#killfeed`, `#transport` and its buttons, `#btn-spoilers`, `#scrub`,
`#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`, `#scrub-head`, `#endcard`, `#status`, the
locker-room curtain and the whole scrubber/momentum/beat/lull machinery are present and
unmodified; `tests/test_broadcast.nim:112-180` re-asserts all of that by id plus the
scope-duplication test over 35 chrome alias names and `pushFeed(row)`'s one-argument
signature.

**Transport rules** — `relayout()` sets `--hudscale`, `--topband` and `--band` on
`document.documentElement` (`replay_broadcast.html:2229-2270`, `root` is
`document.documentElement`), which is where `--u` and `#board`/`#endcard` read them
(:40-42, :96-98, :723-724). `#endcard` is `top: var(--topband); bottom: var(--band)`
(:722-724), shown with `#endcard.on` (:735) and taken down on any frame whose phase is not
`gameover` — i.e. by every seek, since `chromeViewOfReplay` sets `ph` from the playhead index
(`broadcast.nim:287`). The appended overlays ride the bands, not the transport strip:
`#fm-roster` at `top: calc(var(--topband) + 4·var(--u))` (:2326) and `#fm-book` at
`bottom: calc(var(--band) + 108·var(--u))` (:2368), both `pointer-events: none`.
Beat buttons carry `#scrub button.beat-marker { pointer-events: auto }` (:2399-2405) over the
inherited `.beat-marker` base rule (:603-610), with a colour rule for each of the five kinds
the sim emits and no rule for a kind it does not.

**360 px legibility** — `.plate-name, #scorebug .team-name { flex: 1 1 auto; min-width: 3.2em; }`
(:2311-2312) and `@media (max-width: 640px)` hiding `#scorebug .lives-label`, `.fm-chip-pol`
and `.fm-book-stall` (:2313-2317); asserted by `tests/test_broadcast.nim:140-145`. Measured in
CI at 13 widths from 360 px: `{"ok":true,"viewports":[{"width":360,"chips":8,"book":8,"feed":4},…]}`
(run 32900609480, log line 4578).

**Readouts** — offer bubbles: `global.nim:275-316` draws `N <fruit sprite> -> N <fruit sprite>`
tinted by the give fruit, hollow with a light outline when `unfunded`, and a heavier
`rgba(255,240,170)` stroke when a mirroring counterparty sits within `TradeRadius`
(`buildPacket:494-514`). Hunger bars: `barImage` (:257-273), two segments, hunger green →
amber → red over stamina blue, anchored above the cog (:481-484); `STARVING` / `EXHAUSTED`
tags at :516-526. Rate chart: `lead = {"teams":["rate"],"pts":[[t, rateX100], …]}`
(`broadcast.nim:161-166`), which is exactly the shape `ingestLeadSeries` reads
(`chrome_common.js:637-661`) — asserted `test_broadcast.nim:60-67`. Roster strip carries the
policy name in `pol` and the alias in `name` (`broadcast.nim:85-86`,
`replay_broadcast.html:2508-2516`) — checklist 4's "both name spaces", with the board, the
observation (`llm.nim:172`) and every prompt showing aliases only.

**Manifest** — `game.name` `fruit-market`; `game.replay_viewer.bundle` `static-replay-viewer`;
no top-level `replay_viewer`, no top-level `version`; `episode_timeout_minutes: 20` top-level;
6 tags; `game.owner` present. `game.runnable.env.ANTHROPIC_API_KEY_URI` =
`secret://coworld/fruit-market/anthropic_api_key`. Image placeholder `{{FRUIT_MARKET_IMAGE}}`
on the runnable and all three `player[]` entries, derived from `compose.yaml`'s
`services.fruit_market`. `num_agents: 8` in **all four** variants and in
`certification.game_config`; `certification.players` is 2 × `fruit-market-player`,
4 × `fruit-market-hauler`, 2 × `fruit-market-homesteader` — every declared `player[]` id seated
— and the fixture declares **no** `tokens`. `config_schema` has `additionalProperties: false`,
`required: ["tokens"]`, `minItems`/`maxItems` on both array properties, and 37 properties
matching design.md:970-984 (with the retuned defaults). `results_schema` bounds all twelve
slot arrays 1..8. `game.docs` is `{readme:{type:"text"}, pages:[{id,title,content:{type:"text"}}]}`
and `game.protocols` carries **both** `player` and `global` as `{"type":"text",…}` objects —
checklist 10. `tools/ci/check_manifest_loads.py` runs coworld 0.1.42's own
`_load_template_manifest` **and** `validate_upload_manifest` from a venv; that step is green
in run 32900609480.

**Seat-count enforcement** — `tools/ci/docker_smoke.sh:110-151` implements all four invariants
checklist 6 names (num_agents present; positive integer; `len(certification.players)` equal;
`len(certification.game_config.players)` equal) plus the independent `SMOKE_SEATS` cross-check,
each raising a message prefixed `SEAT-COUNT FAIL:`. The script is committed `100755`
(`git ls-files -s` → `100755 … tools/ci/docker_smoke.sh`), as is
`tools/build_replay_viewer.sh`. `grep -c "SEAT-COUNT FAIL" /tmp/ci.log` over the **full** log
of run 32900609480 returns **0**; the smoke logged
`game=fruit-market seats=8 config={… "num_agents": 8 …}` and
`smoke OK: seats=8 results=630B replay=169339B reason=complete` (log lines 2673, 2679).

**Workflows** — `ci.yml` has `test` (with the `check_manifest_loads` step, :104-116, and the
debug+release test matrix, :118-164), `docker-smoke` (exec-bit assert, build, smoke, replay
artifact), and `wasm-viewer` with `needs: docker-smoke` (:226), Playwright pinned 1.55.0 in
both places (:304-305), `viewer_smoke.mjs` run with `--soak 10 --strict-text-bounds`
(:332-337), the renderer-fixture step (:339-353) and `dom_text_smoke.mjs` (:355-359).
`tools/ci/viewer_smoke.mjs` is byte-identical to
`coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` silent).
`coworld-release.yml` runs build (:153) → certify (:167) → upload-policies (:206) →
upload-coworld (:304) → secret put (:342) and uploads `release-result.json` (:473-478);
`coworld-submit.yml` uploads `submit-result.json` (:136-141). The checklist-12 placeholder
gate — `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows, `docker_smoke.sh` and
`policies.json` — returns **no matches**, so the gate exits 0.

**`tools/ci/policies.json`** — four policies, all on `/bin/fruit-market-player`:
`fruit-market-broker` (PLAYER_PROMPT + `USE_BEDROCK: "true"`, no `player` key),
`fruit-market-ricardo` (PLAYER_PROMPT + `USE_BEDROCK: "true"` +
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` at :13), and the two scripted fillers
`fruit-market-hauler` / `fruit-market-homesteader`. Both champion prompts are the design
note's text (design.md:534-552) with typographic dashes flattened; asserted by
`tests/test_manifest.nim:178-209`.

**CI status (checklist 1)** — `gh run list -R Metta-AI/cogame-fruit-market --branch main -w ci.yml`:
run **32900609480**, head sha `43e34e150f8871b40f6a3e86034b4bf2ce487bfd`, conclusion
**success**. All three jobs green with every step green — including `wasm-viewer` →
`Load the bundle in a real browser`, which reported
`{"loaded":true,"ms":544,"clock":"ROUND 5 / 6 TICK 242 OF 359", …}`,
`soak: 10s of playback kept advancing ("2 / 359" -> "194 / 359" -> "242 / 359")` and
`scrub readouts: 0%="ROUND 5 / 6 TICK 242 OF 359"  50%="ROUND 4 / 6 TICK 196 OF 359"
100%="FINAL MARKET CLOSED"` — three distinct readouts (log lines 4546-4548). No step is
`continue-on-error` or commented out. `git log --all --oneline -- tests/` returns exactly one
commit (`43db808`, the implementation commit), so **no test file was changed, skipped,
weakened or removed after it was written** — the second half of checklist 1 is verified.

**Not a finding, recorded to pre-empt a misread** — `viewer_smoke.mjs` reports
`feed_lines: 0` for the real bundle. That is a selector artefact, not an empty feed:
`tools/ci/viewer_smoke.mjs:425` looks for `#feed, .feed, #log`, and this game's feed is the
starter's `#killfeed` (`replay_broadcast.html:2560`). The feed is exercised by
`dom_text_smoke.mjs`, which reports `feed:4` at every one of the 13 viewports.

---

## Could not determine

- **Whether `--timeout-seconds` is a valid flag on `coworld certify` 0.1.42** (F1). The
  design note asserts it and cites cooperative-hunting; the sandbox has no coworld install
  outside the CI venv. What would settle it: `uvx --from coworld==0.1.42 coworld certify --help`,
  or the cooperative-hunting release workflow.
- **Whether an artifact-write failure leaves the process alive.** `writeArtifact`
  (`server.nim:63-75`) can raise `IOError`, which would propagate out of `finishEpisode` on the
  game thread before `quit(0)` at `:167`. Whether Nim terminates the process on an unhandled
  thread exception under this build's flags is not something I can settle by reading; the
  platform's own episode timeout bounds it either way. What would settle it: a run with a
  failing `COGAME_RESULTS_URI`.
- **Whether the shipped renderer can ever push a bubble or alias plate outside the board
  viewport** (context for F19). I computed the extremes by hand (see F19) and both fit, but
  the widths depend on `readTiny5Font()`'s glyph metrics, which I did not measure. What would
  settle it: a fixture that drives `global.nim`'s `buildPacket` itself and asserts every
  overlay object's `x + sprite.width <= BoardW`.
- **Whether feasibility gates (a)–(d) still hold at the retuned constants across all 12
  seeds.** `tests/test_feasibility.nim` runs in CI and CI is green at this sha, which is the
  evidence; I could not execute Nim in the sandbox to reproduce the margins. The gate
  thresholds themselves match design.md:336-347 with the accepted ratio form for (c).
