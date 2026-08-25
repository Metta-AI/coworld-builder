# r1 review — hanabi

Repo: `Metta-AI/cogame-hanabi` @ `b06d9feeee38ffef3788f26b804995e47cf7ae4c` (clone at `/tmp/cogame-hanabi`)
Starter: `Metta-AI/cogame-bullwhip` @ `/workspace/starters/cogame-bullwhip` (read-only mount)
Range: starter tree .. `b06d9fe` (7 commits: `1d03231`, `a2c06b2`, `5cfeaab`, `bf46521`, `501a8eb`, `1bc2a9b`, `b06d9fe`)
Files read: 38 (whole `src/`, whole `tests/`, `client/`, `replay-viewer/`, `tools/`, `.github/workflows/`, the manifest, plus the starter counterpart of every forked file)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-game rule)
CI evidence: run **32780954392** (`gh run list -R Metta-AI/cogame-hanabi --branch main -w ci.yml`), headSha `b06d9fe…`, conclusion `success`, jobs `test` / `docker-smoke` / `wasm-viewer` all `success`; artifacts `viewer-smoke`, `renderer-fixture` downloaded and read.

Design note read: `/workspace/coworld-builder/runs/2026-08-24-hanabi/design.md` (byte-identical to `docs/plans/2026-08-24-hanabi-design.md` in the repo — verified with `diff`).

---

## Blocking

### F1 — a full-cap `banner` (LLM-authored sentence) is drawn ellipsized to roughly a third of its length; the fixture's `ellipsized` count is 1668

- **Where:** `client/renderer.js:149-155` (band width), `client/renderer.js:541-562` (`wrapLines`), `client/renderer.js:564-586` (`drawBanner`), `client/renderer.js:517-521` (call site); CI run 32780954392, `wasm-viewer` → *Load the worst-case renderer fixture*; artifact `renderer-fixture/viewer-smoke.png` + `.json`.
- **Observed.** The banner band is sized as a fraction of the canvas, not from the server's cap:

  ```js
  // client/renderer.js:149-152
  // The banner is laid out in a RESERVED band, never relative to something
  // that can slide off the canvas: its width is computed from the server's
  // own cap on the string, so a full-length banner always has room.
  var bannerW = compact ? 0 : Math.max(96, Math.min(width * 0.22, 210));
  ```

  `MaxBannerLen` (80 runes, `src/hanabi/sim.nim:32`) appears nowhere in `renderer.js` — I grepped; the only inputs to `bannerW` are the canvas width and the two constants 96/210. `drawBanner` then calls `wrapLines(ctx, text, w - pad*2, 2)` (`renderer.js:570`) with `maxLines = 2`, and `wrapLines` ellipsizes the last line when the text overflows (`renderer.js:555-561`).

  Arithmetic at the widest fixture size (1280 px page, canvas ≈ 710 px because `#feed` is expanded): `bannerW = max(96, min(710*0.22 = 156, 210)) = 156`; `size = min(rowH*0.17, 13)`; usable text width ≈ 143 px per line × 2 lines ≈ 286 px. The fixture's banner is 80–81 runes, ≈ 440 px in that font. So ~⅓ fits.

  This is not inference — the CI screenshot shows it. In `renderer-fixture/viewer-smoke.png` the four seat-row banner tags read

  ```
  holding
  Widget-of-the-Long-…
  ```

  where the string handed to the renderer is `"holding Widget-of-the-Long-Name's chop while the green four comes back around now"` (`tools/ci/renderer_fixture.html:68-69`). 27 of 81 runes are drawn. The gated step's own line: `canvas text: 31602 drawn, 0 never inside the canvas (24 draws crossed an edge), 1668 ellipsized (--strict-text-bounds)`.
- **Checklist item:** 15, third bullet — *"Ellipsis is a design choice for **labels** (a card name in a 52 px card) and a defect for **sentences**. If `ellipsized` counts a remark rather than a nameplate, the box is too small — widen the band, do not shorten the text."*
- **Design note says:** `design.md:887-891` — *"a paper tag drawn in a **reserved band to the right of that seat's row**, whose width is computed from `MaxBannerLen` measured in the actual font at the current scale, wrapped to at most two lines and ellipsized on a rune boundary"*. The code's band width is not computed from `MaxBannerLen` and is not measured in the font.
- **Why blocking:** the whole point of the worst-case fixture is the class of chrome that exists only to show what a model said. `never_inside` is 0 and the job is green, but the remark itself is unreadable at every width where it is drawn at all (under 560 px `bannerW` is 0 and the banner is not drawn — `renderer.js:152` — so there is no width at which a full banner is legible on the canvas).
- **Context that cuts the other way, stated plainly:** the *full* banner is visible in the HTML feed — `renderer.js:797-802` emits a `.feed-say` line with the untruncated text, and the same screenshot shows the complete sentence in the right-hand feed. So the remark is not lost from the page, only from the canvas tag.

### F2 — the worst-case fixture does not assert its own strings are full-length, and one of them is 13 runes short of the cap it claims

- **Where:** `tools/ci/renderer_fixture.html:66-74` and the whole file (234 lines) — there is no length assertion anywhere in it.
- **Observed.**

  ```js
  // tools/ci/renderer_fixture.html:68-71
  var BANNER = "holding Widget-of-the-Long-Name's chop while the green four " +
    "comes back around now";          // 80 runes exactly
  var NOTE_LINE = "Ratchet slot 1 is a 3 (candidates: red 3, green 3, blue 3, " +
    "white 3) — hold it";              // 90 runes
  ```

  Measured (`python3 len()` on the exact literals): `BANNER` is **81** runes (comment says 80; `MaxBannerLen` is 80, `sim.nim:32`); `NOTE_LINE` is **77** runes (comment says 90; `MaxLearnedLen` is 90, `sim.nim:34`). The `learned` block is fed six copies of `NOTE_LINE` (`renderer_fixture.html:141-142`), so the six-line block is exercised at 77/90 of the cap the server enforces. No runtime check ties either literal to the Nim constants, and nothing fails if a future edit shortens them.
- **Checklist item:** 15, last bullet — *"The fixture asserts its own strings are still full-length — one quietly shortened remark leaves it passing while testing nothing."*
- **Design note says:** `design.md:1088-1091` — *"a synthetic frame carrying a full `MaxBannerLen` banner on all four seats, a full `learned` block, and long alias/policy names … and self-checks that every drawn string stays inside the canvas."* The self-check that exists is `viewer_smoke.mjs --strict-text-bounds` (external); the "still full-length" assertion is absent.

### F3 — a `/client/replay` pod route is registered, and the container has a replay-server mode

- **Where:** `src/hanabi/server.nim:473` (`result.get("/client/replay", htmlHandler("replay.html"))`), `src/hanabi/server.nim:478` (`result.get("/replay", replayUpgradeHandler)`), `src/hanabi/server.nim:409-413` (`replayUpgradeHandler`), `src/hanabi/server.nim:492-515` (`runReplayServer`), `src/hanabi.nim:29-30` (`if runtimeConfig.replayMode: runReplayServer(runtimeConfig)`).
- **Observed.** `buildRouter` unconditionally registers `GET /client/replay` serving `client/replay.html`, and `GET /replay` upgrading to a websocket that ships `replayPayloadGlobal`. In replay mode `runReplayServer` parses the recorded replay, precomputes frames via `framesFromEvents` → `replayMatch` (`server.nim:148-152, 500-510`) and serves the page until torn down. This is byte-for-byte the starter's arrangement (`/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:470,475,490,510`).
- **Checklist item:** 3 — *"`coworld_manifest_template.json` declares `"replay_viewer": {"bundle": "static-replay-viewer"}`, `tools/build_replay_viewer.sh` exists and is wired as the `coworld build` hook, and the viewer contacts nothing but S3. **No `/client/replay` pod path anywhere.**"*
- **Design note says:** the note contradicts itself here. `design.md:673` lists `GET /client/replay` and `WS /replay (replay mode)` in the exact route table the server is supposed to implement; `design.md:775` says *"**Never a `/client/replay` pod viewer.**"*; `design.md:1119` puts *"A live-server (`/client/replay`) replay viewer"* in Out of scope. The code follows line 673.
- **Counter-evidence the judge should weigh:** the other three clauses of item 3 are satisfied — the manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json:15-17`), `tools/build_replay_viewer.sh` exists at mode `100755` (`git ls-files -s`) and is what `coworld build` invokes (`.github/workflows/coworld-release.yml:153-165`), and `coworld-release.yml:191-201` hard-fails certification unless the log reports the STATIC bundle. The static bundle itself contacts only the `?replay=` URL (`replay-viewer/static_replay.js:69-91, 150-173`) — no other network call. Nothing in the manifest points the platform at the pod route. I am filing this because the checklist wording is absolute ("anywhere") and the route is present; whether removing an inherited starter route is the right remedy is the judge's call.

---

## Non-blocking

### F4 — the "deadline before any turn" path settles as `complete`, not `deadline`

- **Where:** `src/hanabi/server.nim:262-282`, `src/hanabi/sim.nim:818-824`.
- **Observed.** When the pre-turn deadline check fires at `state.sim.turn == 0`, the server plays the whole episode on the `conventions` baseline and then calls `endEarly()`:

  ```nim
  # server.nim:270-280
  if state.sim.turn == 0:
    ...
    while not state.sim.done:
      let seat = state.sim.pendingSeats()[0]
      let decision = scriptedAction(state.sim, seat, skConventions)
      state.sim.applyMove(seat, decision.move, "", "", "scripted")
  state.sim.endEarly()
  ```

  The catch-up loop runs to a terminal condition, so `applyMove` has already called `settle("complete", …)` (`sim.nim:809-816`); `endEarly` then returns immediately (`sim.nim:822-823: if sim.done: return`). `results.reason` is therefore `"complete"` and `results.endReason` one of `perfect|strikeout|deckout|turnlimit`.
- **Design note says:** `design.md:217-219` — *"the server plays out the whole episode with all four seats on the `conventions` baseline … so the replay is never empty, **then settles with `reason = "deadline"`**."*
- Not a checklist violation: item 5 asks that the episode settle and score inside the budget, which it does (the catch-up is pure integer work, ~5 ms per `test_bot.nim:36-51`), and both values are inside the documented enums that `test_replay.nim:199-221` polices.

### F5 — the fallback's rejection text is logged but never recorded on the `move` event

- **Where:** `src/hanabi/llm.nim:702-707` (`result[index].reject = cleanText(rejects[index], MaxRejectLen)`), `src/hanabi/server.nim:299-305`.
- **Observed.** The server prints `decision.reject` to stdout (`server.nim:301-302`) and then calls `applyMove(seat, decision.move, decision.note, decision.banner, decision.origin)`. `decision.reject` is not passed and `GameEvent` has no field for it (`src/hanabi/types.nim:50-86`). For a fallback, `decision.note` is `""` (`llm.nim:301-306` never sets one), so `event.text` carries the seat's *previous* note (`sim.nim:794`).
- **Design note says:** `design.md:303-305` — *"the `move` event records `origin = "fallback"` with the rejection text"*.
- Checklist item 8 is nevertheless satisfied: `origin = "fallback"` is recorded (`sim.nim:714`), `event.scripted` is set (`sim.nim:715`), and `results.fallbacks[s]` counts it (`sim.nim:792-793, 855`) so phase 60 can count fallbacks.

### F6 — the re-derivation compares the final frame, the annotations and the final digest; it does not compare the per-move recorded scalars

- **Where:** `src/hanabi/sim.nim:1289-1307`, `tests/test_replay.nim:91-120`.
- **Observed.** `replayMatch` re-applies each `move` event and compares `outcome`, `touched`, `untouched`, `learned`, `nowPlayable`, `nowDead`, `nowCritical` per event, then the `digest` on the `end` event. The recorded per-move scalars — `hintTokens`, `fuses`, `deck`, `countdown`, `score` (written at `sim.nim:796-800`, serialised at `sim.nim:1186-1190`) — are read back by `eventFromJson` but never compared. The test asserts `frames.len == live.events.len + 1`, `$frames[^1].frameJson() == $live.frameJson()` (the **tail** frame only), `frames[^1].digest() == live.digest()`, and the per-hint annotation equality; it does not walk intermediate frames against the recorded scalars.
- **Relative to checklist 2** (*"reproduces the recorded per-tick state **frame by frame**"*): the viewer half is unambiguously satisfied — `replay-viewer/hanabi_replay.nim:37-49` builds `frames` from `replayMatch` and hands *those* to the renderer, and `client/renderer.js:1344-1347, 1397-1400` draws from `payload.frames`; there is no parallel recording. `test_replay.nim:122-138` also proves a tampered annotation or digest raises rather than silently redrawing. What is not asserted is a per-event scalar comparison. I report the scope; I do not claim it falsifies the item.

### F7 — the canvas banner is not passed through the name map, while the feed banner is

- **Where:** `client/renderer.js:518-521` (`data.banner` used raw) vs `client/renderer.js:797-802` (`nameMap.text(event.banner)`).
- **Observed.** In the fixture screenshot the canvas tag reads `holding Widget-of-the-Long-…` (alias kept) while the feed line for the same banner reads `holding hanabi-cautious-filler-of-the-Long-Name's chop …` (alias substituted).
- **Design note says:** `design.md:49-51` lists the render sites where `makeNameMap` is applied — *"clock, scorebug, endcard, beat labels, feed, hint pane"*. The canvas banner is not on that list. Checklist 4 ("both present") is satisfied: aliases are what the seats see, and `makeNameMap` is applied at every site the note names (verified below).

### F8 — HTTP error bodies and reply heads are sliced by byte, not by rune

- **Where:** `src/hanabi/llm.nim:612`, `:621`, `:626`, `:635`, `:407-411`.
- **Observed.** e.g. `response.body[0 .. min(response.body.high, 400)]` — a byte slice that can cut a multi-byte character. The resulting `error.msg` becomes `rejects[index]` (`llm.nim:699`) and is appended to the retry prompt after `cleanText(…, MaxRejectLen)` (`llm.nim:674-676`); `cleanText` (`llm.nim:380-387`) only truncates when `runeLen > limit`, so a short-but-invalid string passes through unchanged.
- **Scope:** this text reaches the outbound retry prompt and stdout. It does **not** reach the replay: `decision.reject` is never written to a `GameEvent` (see F5), so checklist 9's "every string that reaches the replay" is not falsified. Every string that *does* reach the replay goes through `cleanText`/`capLine` (`llm.nim:532-534`, `sim.nim:117-122`, `sim.nim:601-609, 755, 775`), all `runeSubStr`-based.

### F9 — `#endscreen` stops at the band structurally rather than via `bottom: var(--band)`

- **Where:** `client/chrome.css:374-383` (`#endscreen { position: absolute; inset: 0; … } #endscreen.show { display: flex; }`), `client/chrome.css:95` (`#board-wrap { position: relative; flex: 1; min-height: 0; }`), `client/replay.html:21-33` (`#board-wrap` then `#transport` as flex siblings of `#stage`).
- **Observed.** `#endscreen` is `inset: 0` inside `#board-wrap`, and `#board-wrap` is a `flex: 1` sibling that ends exactly where `#transport` begins. Its bottom edge is therefore the top of the band, with no `bottom: var(--band)` declaration. `#loading` *does* carry the declaration (`client/chrome.css:587`).
- **Checklist 14(c)** names `#endcard` and `bottom: var(--band, 0px)`; this lineage has no `#endcard`. `design.md:836-840` states the substitution explicitly. The other two clauses of 14(c) hold: the class the CSS rule uses is `show` and that is exactly what `updateEndscreen` toggles (`renderer.js:1022`), and every seek re-evaluates it (below).

### F10 — the `belt-and-braces` fallback `applyMove` is not itself guarded

- **Where:** `src/hanabi/server.nim:303-312`.
- **Observed.** The first `applyMove` is wrapped in `try/except HanabiError`; the substitute `state.sim.applyMove(seat, fallback.move, "", "", "fallback")` at `:312` is inside the `except` block and is not guarded. If it raised, the exception would leave `runGame`.
- **Inferred, untested:** unreachable in practice — `conventionsMove` returns `moves[0]` or an element of `legalMoves()` (`llm.nim:179-249`), `legalMoves` is non-empty at every state of 200 seeded episodes (`tests/test_sim.nim:321-357`), and the loop only reaches this point after checking `sim.done` under the lock with a single writer thread.

---

## Traced and consistent

**Turn-based rule (the brief's explicit ask).**
- `design.md:11-13` states it up front: *"bullwhip resolves a week only when all four seats have ordered (a simultaneous batch of four); Hanabi is strictly turn-based — exactly one seat acts per turn, so every turn is one model request, never four."* `design.md:285-294` repeats it.
- `src/hanabi/sim.nim:421-427` — `pendingSeats` returns `@[sim.turn mod Seats]` or the empty seq when done.
- `src/hanabi/server.nim:283-294` — one `pendingSeats()` per loop iteration, one `decideAll` call on that list.
- `src/hanabi/llm.nim:666-681` — `for attempt in 0 .. 1`, one `batch.post` per open seat, i.e. a batch of one. `tests/test_bot.nim:86-92` asserts `seats.len == 1` and `decisions.len == 1`.
- The checklist's simultaneous-game addendum therefore does not apply; sequential calls here are the rule, not a defect.

**Resolution rules** (`sim.nim:694-816` against `design.md:97-136`): validate → apply → draw → countdown → end tests → log, in that order. Hint marks every match and writes the negative on the rest (`sim.nim:537-557`); a 5 refunds only below 8 (`sim.nim:750-755`); discard is illegal at 8 (`sim.nim:446-447`) and refunds via `min(8, +1)` (`sim.nim:764`); countdown arms at `Seats` on the turn the deck empties and decrements thereafter (`sim.nim:784-787`), giving exactly four further turns — asserted at `tests/test_sim.nim:232-248`; end tests fire in the order strikeout → perfect → deckout → turnlimit (`sim.nim:809-816`), priority asserted at `tests/test_sim.nim:288-295`. Score is Σ stack heights including after a strikeout (`sim.nim:417-419`, `tests/test_sim.nim:258`), and `results.scores` is the same number for all four seats (`sim.nim:844-850`).

**Legality is one code path.** `illegalReason` (`sim.nim:432-467`) is the single predicate; `legalMoves` (`sim.nim:469-496`) enumerates exactly the moves for which it returns `""`; the decision path checks the same predicate (`llm.nim:691-693`); `applyMove` checks it again (`sim.nim:706-708`); the prompt prints `moveJson` for each entry (`sim.nim:1080-1082`). `tests/test_sim.nim:321-357` cross-checks the enumeration against an independent brute-force predicate at every state of 200 seeded episodes and asserts it is never empty; `tests/test_prompt.nim:118-142` asserts the printed block round-trips both ways.

**Decision path.** Normalisation tolerates a BOM, a markdown fence and trailing prose, and takes the first balanced object (`llm.nim:389-438`); `{"move":"play 2"}`, alias targets, `color`/`number`, numeric strings and `hint` as a value alias all normalise (`llm.nim:483-574`), asserted at `tests/test_bot.nim:104-137`. Exactly one retry with the specific reason quoted (`llm.nim:666-701`), then the `conventions` fallback with `origin="fallback"` (`llm.nim:702-707`). `decideAll` never raises. No credentials ⇒ `client.disabled` and every seat scripted with no network (`llm.nim:159-162, 659-665`), asserted at `tests/test_bot.nim:77-98`. Sonnet-4-6 is absent from `bedrockModelIds()` (`llm.nim:112-115`) as `design.md:279-283` requires; the entrypoint banner prints no `model=` (`src/hanabi.nim:42-44`).

**Every wait and its bound** (checklist 5).
- player connect: `while epochTime() < deadline` with `deadline = gameStart + playerConnectTimeoutSeconds` (180) — `server.nim:215-223`.
- per-request: `client.curl.makeRequests(batch, client.timeoutSeconds)` with `llmTimeoutSeconds` default **20** (`llm.nim:681`, `types.nim:97`).
- request spacing: `MinRequestSpacingSeconds = 2.0`, a sleep of at most 2 s (`llm.nim:37, 637-642`).
- turn pacing: `turnDelayMs` clamped to `PacingBudgetMs div maxTurns` (`sim.nim:146-147`), asserted idempotent at `tests/test_sim.nim:375-385`.
- pre-turn reserve: `TurnReserveSeconds = 45.0` checked before every decision against `playDeadline = gameStart + timeout * 0.6` (`server.nim:38-42, 206, 246-248, 262-264`). Worst turn traced: attempt 0 spacing ≤ 2 s + 20 s, attempt 1 spacing 0 (20 s already elapsed) + 20 s = 42 s < 45 s.
- assumed timeout when `COWORLD_TIMEOUT_SECONDS` is absent: `config.episodeTimeoutSeconds` default 1200 (`types.nim:92`, `server.nim:239-245`) ⇒ 720 s of play, 60 % exactly.
- shutdown: `sleep(500)` + artifact writes + `ShutdownGraceSeconds = 20` + `quit(0)` (`server.nim:43-46, 188-204`).
- No unbounded loop found: the main loop's only exits are `sim.done` and the deadline, and every iteration increments `sim.turn` toward `maxTurns ≤ 120`.

**Rune-safe truncation** (checklist 9). `cleanText` (`llm.nim:380-387`) and `capLine` (`sim.nim:117-122`) both use `runeLen`/`runeSubStr`; the player prompt uses `runeSubStr` too (`server.nim:442-443`). `tests/test_bot.nim:139-155` feeds 700 `é` and asserts `note.runeLen == MaxNoteLen`, `banner.runeLen == MaxBannerLen`, `validateUtf8() == -1`, and that newlines never survive a banner. `tests/test_replay.nim:42-88` writes a whole episode whose every turn carries those capped multi-byte strings, re-reads the raw bytes with `validateUtf8() == -1` **and** `parseJson`, and asserts every recorded `text`/`banner` is exactly at the cap in runes.

**Replay writer.** `replayJson` (`sim.nim:1085-1111`) emits `protocol`, alias `names`, `policyNames`, `config` including the seed, every event and the results — self-sufficient. `finishEpisode` (`server.nim:154-204`) sends the `final` player frames **before** writing artifacts, then writes results and the replay, then the grace. `eventToJson`/`eventFromJson` round-trip all three kinds field by field (`tests/test_replay.nim:156-197`).

**Viewer re-derivation.** `replay-viewer/hanabi_replay.nim:23-53` parses the replay, rebuilds the config from the recorded seed, runs `replayMatch`, and publishes `frames` alongside the raw events; a raised `HanabiError` returns 0 and the shell surfaces it as `data-replay-error` (`static_replay.js:119-125, 46-60`). The live-server replay mode uses the same `framesFromEvents` (`server.nim:148-152`). No parallel per-tick recording exists anywhere in the tree.

**Load signalling / bundle lineage** (checklist 13). `replay-viewer/config.nims:38-41` carries `-s MODULARIZE=1`, `-s EXPORT_NAME=HanabiReplayModule`, `EXPORTED_FUNCTIONS=…_hb_*`; `static_replay.js:161` calls `HanabiReplayModule()` as a factory and `:119-128` calls `_hb_load_replay`/`_hb_payload_ptr`/`_hb_error_ptr`. `diff` against the starter shows both files are bullwhip's with only the `bw_`→`hb_`/`Bullwhip`→`Hanabi` renames plus the documented chorus change (`static_replay.js:93-114`, polling `data-replay-loaded` before posting `ready`, bounded at 240 frames). `data-replay-loaded` is set by `renderer.js:1404`, immediately after the first synchronous `renderer.draw` in `attachReplay`'s frame loop (`:1374-1402`); `data-replay-error` is set only by the shell (`static_replay.js:58`) and cleared on retry (`:132, :157`). CI proves it executes: `viewer-smoke.json` reports `{"loaded":true,"ms":292,…,"signals":{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"]}}` and `wasm-viewer` `needs: docker-smoke` (`ci.yml:212`) with the smoke step present and not `continue-on-error` (`ci.yml:293-322`).

**Text bounds.** Real-replay smoke: `canvas_text {total: 52752, outside: 0, never_inside: 0, ellipsized: 0}` with `--strict-text-bounds` (`ci.yml:317-322`). Fixture: `never_inside: 0`, `outside: 24` (samples are the hint-beam numeral `"3"` sliding off the left edge of a 150 px canvas — an animation, exactly the case the checklist says not to gate).

**Manifest** (checklists 3, 6, 10). `replay_viewer.bundle = "static-replay-viewer"` (`:15-17`); `num_agents: 4` in `variants[0]` (`:384`), `variants[1]` (`:409`) and `certification.game_config` (`:432`); both variants carry `description` (`:368`, `:393`); `game.protocols.player` and `.global` are both `{"type":"text","value":…}` (`:262-269`); `game.docs.readme` is `{"type":"text","value":…}` and `pages` are `{id,title,content:{type,value}}` (`:271-294`); `config_schema` is `additionalProperties:false` with `required:["tokens","players"]` and `minItems/maxItems: 4` on both arrays (`:34-68`); `results_schema` arrays are 4/4 and `fireworks` 5/5 (`:139-259`); `env.ANTHROPIC_API_KEY_URI` present (`:26-28`); all four `certification.players` slots filled by declared runnables (`:438-451`). `tests/test_viewer.nim:131-160` re-asserts all of this.

**Seat-count invariants** (checklist 6). `tools/ci/docker_smoke.sh:106-151` enforces the four invariants — present, positive integer, `len(certification.players) == it`, `len(certification.game_config.players) == it` — plus the independent `SMOKE_SEATS` cross-check (`:54, :146-151`), each exiting with a `SEAT-COUNT FAIL:` prefix. I grepped both job logs of run 32780954392: **0 occurrences** of `SEAT-COUNT FAIL`. The smoke log line is `game=hanabi seats=4 config={… "num_agents": 4 …}` and `smoke OK: seats=4 results=311B replay=8867B reason=complete`, plus `every player container exited 0` (the cogmud addition at `docker_smoke.sh:244-265`, which the template does not have — verified by diffing against `templates/tools/ci/docker_smoke.sh`).

**Workflows and scaffold** (checklist 12). `coworld-release.yml` and `coworld-submit.yml` are **byte-identical** to `templates/` after substituting `hanabi`/`coworld-hanabi` (verified with `sed | diff`); `ci.yml` is the template plus the documented `--soak 10` and the renderer-fixture step. Order in `coworld-release.yml`: *Build the Coworld manifest* (`:153`) → *Certify locally* (`:167`) → *Upload the policies* (`:206`) → *Upload the Coworld* (`:304`) → *Put the Coworld secret* (`:342`). `docker_smoke.sh` and `build_replay_viewer.sh` are both mode `100755` in the index. The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files returns nothing; the only surviving angle-bracket names are the four documented runtime values (`ci.yml:202` `<cow_id>`/`<sha>`, `coworld-release.yml:21` and `coworld-submit.yml:17` `<run_id>`, `coworld-submit.yml:31` `<name>:vN`). `tools/ci/policies.json` has four policies: two `PLAYER_PROMPT` champions (`hanabi-signaler`, `hanabi-reader`) and two `PLAYER_SCRIPTED` fillers, with champion #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`:15`). `tools/ci/viewer_smoke.mjs` is **verbatim** from `templates/tools/ci/viewer_smoke.mjs` (`diff` clean).

**Chrome provenance** (checklist 14). I verified the pinned hash myself rather than trusting the test: `sha1(/workspace/starters/cogame-bullwhip/client/chrome.css) = 8f0d16397cb227a427ec1112d39c180f1aef1bfd`, 11 964 bytes — identical to `InheritedChromeSha1`/`InheritedChromeBytes` in `tests/test_viewer.nim:17-18`, and the fork's prefix up to `/* ---------- Hanabi ---------- */` is byte-for-byte that file (Python byte comparison: `True`). `diff` of the whole file shows a single hunk, `467a468,623` — a pure append, no rule above it edited or deleted. `client/replay.html` diff vs the starter: `<title>`, `#wordmark` text, `#clock` placeholder text (`WEEK 0`→`TURN 0` — a third textual edit the note's list at `design.md:815-819` does not name), two appended elements `#tokenbar` and `#hintpane`, `fit()`→`relayout()`, and the `HanabiRenderer` rename. **Nothing removed** — all 20 starter ids present (`tests/test_viewer.nim:22-25, 61-77`). `replay-viewer/index.html` gets the identical treatment plus the two script tags.

**Transport rules** (checklist 14). (a) `relayout()` measures `#transport.offsetHeight` and sets `--band` and `--hudscale` on `document.documentElement` — `client/replay.html:46-61`, `replay-viewer/index.html:51-62`, `tools/ci/renderer_fixture.html:199-207`, and `client/global.html`/`player.html` get the same; `fit()` is called from inside `relayout` so the canvas and the variables cannot drift. It runs on `load`, on `resize`, and from the feed toggle indirectly — `bindFeedToggle` dispatches a synthetic `resize` (`renderer.js:1069-1071, 1081`), which `relayout` listens for. (b) Nothing is fixed-positioned: `grep 'position: *fixed'` over every CSS/HTML file returns nothing; the only absolute overlays (`#lightpool`, `#grain`, `#endscreen`) live inside `#board-wrap`, and `#loading` is pinned above the band by `client/chrome.css:587`. (c) Every seek dismisses the endcard: `setIndex` calls `updateEndscreen(…, index >= events.length && events.length > 0, …)` on **every** index change (`renderer.js:1367-1370`), and every seek path — scrub pointer drag (`:1298-1305`), beat-marker click (`:1199-1202, 1277-1283`), play-button restart (`:1337-1341`) — goes through it. There is no keyboard handler and no back/forward button anywhere (`grep keydown` empty), so there is no seek path that bypasses it. (d) Beats are labelled `<button type="button">` with `title` + `aria-label` and an `onclick` that seeks (`renderer.js:1192-1205`), and every one of the seven kinds the renderer emits — `hint`, `play`, `stack5`, `misplay`, `discard`, `deckout`, `end` (`renderer.js:1207-1234, 1275-1283`) — has a CSS rule (`client/chrome.css:590-602`), asserted by extraction rather than by list at `tests/test_viewer.nim:111-129`. `buildScrub` is the starter's function with a minimal edit (I diffed the two bodies: signature gains `nameMap`, the block key becomes `turn/4`, the marker `<div>` becomes `markHanabiBeat`), and `makeNameMap`/`isBaselineFiller`/`applyNames`/`clampName`/`ellipsize`/`bindFeedToggle` are byte-identical to the starter's. (e) `#viewpanel`, zoom and minimap appear nowhere: `grep 'viewpanel\|zoomAt\|setZoom\|attachMinimap\|minimap'` over all JS/CSS/HTML returns nothing.

**Legibility at 360 px** (checklist 11). `client/chrome.css:280-291` — `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` (the starter's rule, inside the byte-identical prefix). `client/chrome.css:460-464` — `@media (max-width: 640px) { .plate-label { display: none; } … }`. The appended block adds `@media (max-width: 720px) { #hintpane { display: none } }`, `@media (max-width: 560px) { .plate-label, .plate-misplays, #tokenbar .tok-label { display: none } }` and `@media (max-width: 420px) { #scorebug { grid-template-columns: repeat(2, 1fr) } }` (`:614-623`).

**Both name spaces** (checklist 4). Aliases come from `tableNames` (`sim.nim:126-137`) and are what every prompt, observation, player frame and `move` event carries; `results.names` and `replayJson.policyNames` carry the policy names (`sim.nim:848, 1094-1096`, `server.nim:83-88, 140-146`). `makeNameMap` is verbatim and applied at the scorebug (`renderer.js:900`), endcard (`:1026-1028`), feed (`:790, 800`), beat labels (`:1208`), hint pane (`:972, 993`) and the canvas seat rows (`:1090` via `applyNames`). `tests/test_prompt.nim:102-116` asserts no policy name, seed, token, or other seat's note/banner reaches a seat's observation or its player frame, against a crafted fixture whose seat-0 identities exist nowhere else on the table.

**Scripted baselines** (checklist 7). `tests/test_bot.nim:36-51` runs 200 seeds × 3 seat mixes to the natural end, asserting `sim.reason == "complete"`, and `playScripted` (`:19-33`) checks **every** proposed move against both `illegalReason` and membership in `legalMoves` before applying it. `tests/test_sim.nim:342-357` repeats the legality sweep with an independent predicate. `cautious` loses zero fuses over 200 seeds (`:53-60`); `conventions` beats `cautious` and scores ≥ 12 mean over 50 seeds (`:62-75`).

**CI green, no test loosened** (checklist 1). `gh run list` → run 32780954392, `success` on `main` at `b06d9fe`, all three jobs and all steps `success` (enumerated above; the smoke step and the fixture step both ran). `git log --stat -- tests/` shows a single commit `501a8eb` adding all five test files (+1160 lines) and `git log -p 501a8eb..HEAD -- tests/` is **empty** — no test file was touched after it was written, so nothing was deleted, widened, skipped or removed.

---

## Could not determine

- **What the fixture's other 1668 ellipsized draws are.** `viewer_smoke.mjs` caps `samples` at 12 (`tools/ci/viewer_smoke.mjs:335, 337-339`) and all 12 slots were taken by `outside` entries, so no `ellipsized` sample survived into `renderer-fixture/viewer-smoke.json`. The banner is confirmed ellipsized from the screenshot (F1); the seat-row alias plate and the `"N banked · M burnt"` line also route through `ellipsize` (`renderer.js:467, 471`) and are visibly cut in the same screenshot, but those are labels. **Would settle it:** logging the ellipsized samples separately, or raising `SAMPLE_CAP`.
- **Whether the `conventions`/`cautious` parameters were "tuned with a grid harness"** (checklist 7, last sentence). Neither baseline has a numeric parameter — both are ordered rule cascades (`llm.nim:179-299`) — and there is no tuning script anywhere in the tree (`grep -rn 'grid\|tune\|harness'` finds only prose). The design note does not claim a harness either. **Would settle it:** a statement from the builder on whether the clause is applicable to a parameterless baseline, or a committed sweep.
- **Whether `readCogameUri` (`llm.nim:92`) is internally bounded.** It comes from `bitworld/runtime`, which is not vendored in this tree and not fetchable from the sandbox. It is the starter's call, unchanged, and only runs when `ANTHROPIC_API_KEY_URI` is set and `ANTHROPIC_API_KEY` is not. **Would settle it:** reading `bitworld/runtime`'s source or a CI log showing the URI path exercised.
- **Whether any intermediate re-derived frame differs from the live one** (see F6). Only the tail frame is compared. The digest and the annotations make a silent divergence unlikely, but it is not asserted. **Would settle it:** a test comparing `frameJson()` at every index against the live sim's snapshot at that index, or comparing each `move` event's recorded `hintTokens`/`fuses`/`deck`/`countdown`/`score` inside `replayMatch`.
