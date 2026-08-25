# r1 fixes — fruit-market

Repo: `Metta-AI/cogame-fruit-market`
Head: **`3f1bab0f6886db7718c864fc0bcf3c8d58bcc10f`** (main), 20 commits on top of the reviewed
`43e34e150f8871b40f6a3e86034b4bf2ce487bfd`, one per finding.
CI: `ci.yml` run **32907164596** — <https://github.com/Metta-AI/cogame-fruit-market/actions/runs/32907164596>
— conclusion **`success`** on `main` at `3f1bab0`, all three jobs (`test`, `docker-smoke`,
`wasm-viewer`) green with every step green. `grep -c "SEAT-COUNT FAIL"` over the full log: **0**.

Fixed: **19**. No change (rebutted, with evidence): **4** (F3, F16, F17, and the `f`/auto-skip half
of F20). Every fix is its own commit; no two findings share one, and no commit carries anything
that is not the finding it names.

| finding | commit | what changed | checklist item |
|---|---|---|---|
| F1 certify has no `--timeout-seconds 300` | `f8f3394` | `--timeout-seconds 300` added to the certify step in `coworld-release.yml` | 12 |
| F2 unset seat becomes an LLM seat | `62fbfd4` | `src/fruit_market_player.nim` registers `scripted="hauler"` when neither env var is set; the now-dead `DefaultPrompt` deleted | 7, 8 |
| F3 `broadcast_core.js` not forked | — (no change) | the note's readouts are all drawn, server/wasm-side; see below | — |
| F4 beat markers bypass the spoiler gate | `1727860` | the block stamps `__tick` on its markers and runs `C.getSpoilers()` over them every frame | 14(d) |
| F5 book rows lack the stall / never strike | `fa4c89f` | `bookJson` emits `stall` (derived from the recorded cell); a traded seat's row is kept struck through for 48 ticks | 11 |
| F6 plate `trades`/`volume` hardwired to 0 | `8683c6d` | both paths tally the guild from the trade events; the block draws `N trades · rate` under each plate | 4, 14 |
| F7 `say` is its own feed row | `8f83ec7` | the block joins the frame's events by seat: the offer row carries the `auto` tag and the quoted `say` | 15 |
| F8 live `/global` events always empty | `eb37171` | `broadcastLocked` ships the events emitted since the last broadcast; dead `chromeFrame` deleted | 14 |
| F9 3 seeds / 50 ms in `test_baseline` | `2755c45` | 12 seeds and a 1 ms per-round budget, the note's numbers | 1, 7 |
| F10 `test_llm` gaps + tautological batch test | `e2188d2` | a stub HTTP transport (junk/429/403/timeout) asserts `source: "fallback"`; `buildBatch(...).len == openSeats`; the named `max_tokens` error | 8, addendum |
| F11 no frame-by-frame viewer/state test | `f2bf7ce` | three assertions: parsed frames == `sim.frames`; the chrome frame == the frame; the recorded **events re-derive** every frame's inventories and scores | 2 |
| F12 `exhausted` only from the starve drain | `b38cf37` | step 8 fires the event on the 0-stamina transition wherever it came from | 2 |
| F13 forfeit replay unloadable | `ce0f065` | `forfeit` records the opening frame first, so the replay parses, seeks and shows the FORFEIT endcard | 13, 5 |
| F14 `mirror` selectable in production | `68696ae` | `parseScriptKind` no longer maps `"mirror"`; the test uses `skMirror` directly | 12, 7 |
| F15 policy names skip `cleanText` | `9352498` | truncated on rune boundaries at `MaxPolicyNameLen = 64` before they reach the replay | 9 |
| F16 lobby needs all `numAgents` sockets | — (no change) | bounded, inside budget, and the note's literal reading is degenerate; see below | 5 (satisfied) |
| F17 `minTurnSeconds` is a sleep | — (no change) | wall-clock arithmetic unchanged and bounded; the note's phrasing is not implementable without changing tick semantics; see below | 5 (satisfied) |
| F18 dead socket keeps its LLM prompt | `4698c93` | `CloseEvent` clears `state.connected[slot]` | 5, 8 |
| F19 fixture re-implements the anchors | `0768736` | `tests/test_global.nim` drives the **shipped** `buildPacket` and asserts every object fits the board; overlay anchors clamped on both axes | 15 |
| F20 `+` / `-` keys ignored | `9cf75e4` | both keys walk the `PlaybackSpeeds` ladder (`f` deliberately still inert — see below) | 14 |
| F21 nimby pin drift | `dd2aceb` | `Dockerfile.replay-viewer` pinned to 0.1.26 with the matching sha256 | 12, 13 |
| F22 smoke checks shape, not schema | `4b122a9` | `docker_smoke.sh` validates `results.json` against `game.results_schema` from the manifest | 6, 10 |
| F23 two assertions absent | `3f1bab0` | feed-row length budget in `test_broadcast.nim`; determinism **across a fresh process** in `test_sim.nim` | 1, 11 |

---

## F1 — `coworld certify` without `--timeout-seconds 300`

`coworld-release.yml:167-176` ran certify on the CLI's 60 s default. It now passes
`--timeout-seconds 300`, the value design.md:1033-1035 pins.

The reviewer could not determine whether the flag exists on 0.1.42. It does — run in this
sandbox against the pinned package:

```
$ uvx --from "coworld[auth]==0.1.42" coworld certify --help
  --timeout-seconds   <float range>   [default: 60.0]  [x>=1.0]
```

Phase 40 depends on this pin, so it was the first commit.

## F2 — a seat with neither env var

`fruit_market_player.nim` sent `{"prompt": <DefaultPrompt>, "scripted": ""}`, `server.nim:376-380`
mapped `""` to `skNone`, and `decideAll` opened the seat for an LLM call. It now sends
`{"prompt": "", "scripted": "hauler"}`, which is design.md:359-360 exactly. `DefaultPrompt` had no
other reader and is deleted.

Evidence, a real local episode with the built binaries (game + 8 players, no env set):

```
fruit-market player: prompt delivered (0 chars, scripted hauler)
fruit-market: slot 0 registered (0 chars, scripted hauler)
```

## F3 — `client/broadcast_core.js` is the starter's — **no change, with evidence**

The note says the file is "forked … the board draw becomes the tile grid, rivers, groves, stalls,
fruit, cogs, offer bubbles and hunger bars". Every one of those readouts **is** drawn — from
`src/fruit_market/global.nim`, as sprite bitmaps pushed over the sprite protocol
(`bakeBand` :217, `barImage` :257, `bubbleImage` :275, `aliasImage` :318, `tagImage` :337,
`buildPacket` :426-539), which `broadcast_core.js` renders unchanged. That is paintbot's own
division of labour: `broadcast_core.js` is the *ingest and letterbox* layer, and the note's own
next sentence ("its ingest/packet plumbing, letterboxing and layer pooling are untouched") is what
the file actually is. Forking it to re-draw the board in JS would mean drawing the board twice, in
two languages, from two sources — and it would put the LLM-authored strings on a canvas that
`--strict-text-bounds` still could not gate any better than `tests/test_global.nim` now does
(F19). The reviewer records the same trace and files it against no checklist item.

Verified in CI at this head: `Load the bundle in a real browser` reports
`{"loaded":true,"ms":552,"clock":"ROUND 5 / 6 TICK 242 OF 359", "scorebug":"APPLE FARMERS SCORE 110
10 trades · 1.50 🍎/🍌 … BANANA FARMERS SCORE 123 10 trades · 1.50 🍎/🍌"}` — the board, the clock
and the plates all drawing through the inherited renderer.

## F4 — `?spoilers=0` did not hold the market beats back

`buildMarketBeats` appends its own `<button>` markers to `#scrub`, so they never entered
`chrome_common.js`'s private `markerEls` and `applySpoilers` never hid them. `chrome_common.js`
must stay byte-identical (checklist 14), so the block now stamps `el.__tick` on each marker and
runs the same gate itself, from the chrome's own exported `C.getSpoilers()`, on every frame.
`tests/test_broadcast.nim` asserts `applyMarketSpoilers`, `C.getSpoilers()` and `el.__tick = b.t`
are all in the page. The markers stay labelled, clickable `<button>`s that seek — 14(d) is
unchanged.

## F5 — the stall column and the strike-through

`bookJson` now emits `"stall"`, derived from the recorded cell: the stall within Chebyshev 1,
which is exactly where the kernel's `market` job parks. It is derived identically on the live and
replay paths, so the two agree. `tests/test_broadcast.nim` walks **every frame** of a real episode
and re-checks each emitted stall against the frame's own cog cell.

A cleared offer is consumed on both sides and leaves the book on the next frame; the block keeps
the row for 48 ticks with `.fm-book-row.cleared` (line-through) driven by the `trade` event. A
struck row only appears for a seat with no live row, so the panel can never exceed 8 rows — CI's
`dom_text_smoke` reports `book: 8` at all 13 viewports from 360 px.

## F6 — the guild plates' trade count and mean rate

`teamsJson` declared `trades`/`volume` and emitted them unassigned; nothing read them. Both are now
tallied from the trade events themselves — the live frame from `sim.events`, the replay frame from
the recorded events **up to the playhead**, so a backward seek shows the market as it stood then —
along with the guild's mean rate. The block appends `.fm-plate-sub` under each plate's big number.

Evidence in CI (`viewer_smoke.mjs` reading the real bundle):
`"scorebug":"APPLE FARMERS SCORE 110 10 trades · 1.50 🍎/🍌 … BANANA FARMERS SCORE 123 10 trades ·
1.50 🍎/🍌"`. `tests/test_broadcast.nim` re-derives the three numbers from the replay's events and
compares them to the plate.

## F7 — the `say` as the quoted tail of the offer row

The `offer` event carries no `source` and the `order` event carries no offer, so the two rows could
not be composed event-by-event. The sim emits both at the same tick (order first, from
`setRoundOrders`; offer in step 5), and the chrome ships a frame's events as one batch — so the
block joins the batch by seat before drawing any of it. The offer row now reads
`DUNE posts 6 🍎 for 4 🍌 [auto] "…"`, which is design.md:905-908. A seat that says something
without posting still gets its own row, so no model text is dropped (that is the class of chrome
checklist 15 cares about).

## F8 — the live `/global` frame's events

`broadcastLocked` passed `newJArray()`, so `"events"` was `[]` on every live frame and the game
block's feed never ran live. It now ships the events emitted since the previous broadcast
(`GameState.eventsSent`). The dead `proc chromeFrame` went with it.

Evidence — a local episode with a real spectator socket on `/global` (whisky client, sprite packets
decoded, chrome sprite 4090's label parsed):

```
chrome frames: 4  with events: 2
kinds: ["order","harvest","offer","unfunded","spill","round","cross","trade","eat","end"]
```

Measured against the binary built from the reviewed sha `43e34e1`, the same client on the same
config reports `chrome frames: 4  with events: 0  kinds: []` — so the fix is what put the live feed
on the wire.

## F9 — 12 seeds, 1 ms per round

`for seed in 1 .. 3` → `1 .. 12`, and `check worstRoundMs < 50.0` → `< 1.0`. The unittest `check`
calls that police each order moved **out** of the timed region: what the note budgets at 1 ms is the
baseline's decision (eight Dijkstras), not the harness's assertions. Measured worst round here:
**0.007 ms** debug, **0.002 ms** release. The file runs in 31 s release, which is how CI runs it
(repo variable `NIM_TESTS_RELEASE_ONLY`); it also passes in debug — verified locally, several minutes.
Nothing was loosened: this is the only direction either number moved.

## F10 — the fallback, the `max_tokens` error and the batch

Three things the note's test list names were missing or fake. Now:

* **A stub transport.** `tests/test_llm.nim` binds a loopback HTTP server and points
  `newLlmClient`'s Bedrock branch at it (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME=http://127.0.0.1:<port>`),
  then runs the real `decideAll` through curly against it in four modes: junk (200, no JSON), 429,
  403, and a reply that outlasts `llmTimeoutSeconds = 1`. Every seat comes back with the hauler
  order and `source == osFallback` — the record phase 60 counts, which **no** test asserted before.
  429 leaves the client enabled (retried next round), 403 disables it. Nothing raises. The timeout
  case is asserted bounded.
* **The batch.** `buildBatch` was extracted from `decideAll` (same loop, no behaviour change) so the
  test can assert `batch.len == openSeats == 8`, one `POST` per seat tagged with the slot, and that
  the retry batch carries the hint and only the seats still open.
* **`max_tokens`.** `textOfBody` was split out of `textOf` (again no behaviour change); the test
  asserts the raise is the **named** "cut off at max_tokens" error and that a `max_tokens` stop
  which still carried the whole object is not an error at all.

## F11 — the viewer's display is the recorded state

This game records **state**, not inputs, by design (design.md:676-679, 1178-1179: playback never
re-simulates), so "replay the inputs through the sim" is not the shape it has. What checklist 2
demands of *this* design is asserted instead, in three parts, in `tests/test_replay.nim`:

1. every parsed frame equals `sim.frames` field for field (`c`, `o` and `r`, all 720 frames);
2. `chromeViewOfReplay` — the only source the static bundle draws from — reports the frame's own
   numbers for all 8 seats, sampled across the whole episode;
3. **the recorded events re-derive the recorded frames**: walking `events` tick by tick and keeping
   the books they imply (harvest adds, eat subtracts and scores, trade swaps both sides)
   reproduces every frame's `apples`, `bananas` and `score`, for every tick and every seat, and the
   replay's own `results.scores` again at the end.

Part 3 is the re-derivation with teeth: a trade recorded on one side only, a harvest that never
landed or an eat scored to the wrong seat all fail it. The determinism test (F23) covers the other
half — same seed and same orders, same `gameHash`, in-process and in a fresh process.

## F12 — `exhausted` wherever stamina reached 0

The emit sat inside the `hunger == 0` branch. A cog that paid its last stamina on a move (a cost
exactly equal to what it holds is legal, `sim.nim:111`) or on a harvest at stamina 1 got
`exhausted = true` with no event and no feed row. Step 8 now fires on the transition itself,
against the flag carried from the previous tick, so it is still exactly once per collapse.
`tests/test_sim.nim` covers the move case on an **odd** tick, where step 8's +1 regen cannot paper
over it.

## F13 — the forfeit replay

`server.nim:203-209` → `sim.forfeit()` → `finish` appended the `end` event and the `gameover` beat
but no frames, so the written replay had `"frames": []` and `replays.nim:180-182` refuses that:
the static viewer would set `data-replay-error` on a file the platform had accepted. `forfeit` now
records the opening state frame first.

Evidence — the real game binary, `playerConnectTimeoutSeconds: 3`, nothing connecting:

```
fruit-market: starting with 0/8 players connected
fruit-market: writing results and replay
→ results.json  reason=forfeit ending=forfeit scores=[0,0,0,0,0,0,0,0]
→ replay.json   frames=1  last beat {"t":0,"k":"gameover"}
```

`tests/test_replay.nim` parses that replay with the viewer's own parser and builds its chrome frame:
`ph == "gameover"`, `over.ending == "FORFEIT"`, roster of 8.

## F14 — `mirror` is not shippable

`parseScriptKind` no longer maps `"mirror"`; a seat asking for it gets `hauler`, like any other
unknown value. `tests/test_feasibility.nim` uses `skMirror` directly, which is where gate (d)'s
book reader belongs. `tests/test_sim.nim` pins the whole mapping.

## F15 — policy names through `cleanText`

`config.players[].name` reached `sim.policyNames`, the replay's `policyNames[]` and
`results.names` verbatim. They now go through the same rune-safe `cleanText` every other recorded
string goes through, at a new `MaxPolicyNameLen = 64`. `tests/test_replay.nim` feeds eight
multi-byte names past the cap and asserts the replay bytes are strict UTF-8, every recorded name is
inside the cap on a rune boundary, newlines are folded, and `results.names` matches.

## F16 — the adaptive lobby — **no change, with evidence**

The code requires `connectedCount >= config.numAgents and registeredCount >= connectedCount`
(`server.nim:188-189`). The note's phrasing ("returns as soon as every connected socket has
registered") is, read literally, true at t=0 with **zero** connections — the reviewer says so too.
So the extra term is load-bearing and removing it would make the lobby exit before anyone connects
and forfeit every episode. What is left is the partial-roster case, and it is bounded and inside
budget:

* the loop cannot outlive `gameStart + playerConnectTimeoutSeconds` (180 s), polling `sleep(200)`;
* the play deadline is measured from the same `gameStart` (`server.nim:172`, `:220`), so lobby time
  comes **out of** the 720 s play budget, not on top of it;
* worst case 180 s lobby + 12 × max(18, 20+20) = 660 s < 720 s.

Checklist 5 asks for an explicit bound on every wait; it has one. A fix that returned early on a
partial roster needs a new grace constant (how long is "long enough for the stragglers"?), which is
a design-note change rather than a fixer's call — so if the judge wants the behaviour changed, this
is `NEEDS-DESIGN`, not a defect left standing. Nothing about it is a hang.

## F17 — `minTurnSeconds` is a sleep — **no change, with evidence**

The note says "It is a floor, not a sleep on the critical path — the loop keeps stepping sim ticks
while it waits." The loop **cannot** step sim ticks while it waits: a round is exactly
`ticksPerRound = 60` ticks and those ticks are the ones the round's orders drive, so there is
nothing to step before the batch returns. Stepping during the wait would mean either running ticks
without that round's standing orders or making a round longer than 60 ticks — a rules change.

The property the note is protecting is the wall clock, and it holds unchanged: per-round cost is
`max(minTurnSeconds, batch+retry)`, which is the note's own "typical: max(18, ~8) × 12 ≈ 216 s" and
"worst: 12 × 40 = 480 s" arithmetic. The sleep is bounded by `minTurnSeconds`, whose schema maximum
is 60. `tests/test_llm.nim` asserts the request rate stays under 30/min and that the whole budget
fits 60 % of the episode timeout. Changing it would be a design change for no wall-clock gain, so
it is recorded here rather than made.

## F18 — a socket that dies mid-episode

The `CloseEvent` branch cleaned every table but left `state.connected[slot]` true, and
`decideAll` gates on exactly that flag, so the seat kept being sent to the model with its last
registered prompt. It now clears the flag and logs it. A reconnect on the same slot sets it again in
`playerUpgradeHandler`.

Evidence, local episode:

```
fruit-market: player slot 0 disconnected; playing hauler for the rest of the episode
```

## F19 — the worst-case fixture, and the anchors it does not exercise

The finding is right: `tools/ci/renderer_fixture.html` clamps every caption into the canvas before
drawing it (`:99-100`), so its `never_inside: 0` is a property of the fixture; and the real bundle
reports `canvas text: 0 drawn` because the shipped renderer is `global.nim` drawing into **sprite
bitmaps** with pixie — there is no `fillText` on that path for `--strict-text-bounds` to hook, and
checklist 15 says `total: 0` "is not evidence of anything".

So the shipped arithmetic is now tested directly, in Nim, in the `test` job:
`tests/test_global.nim` builds a real `buildPacket` frame with a full offer bubble, a
STARVING/EXHAUSTED tag, a hunger bar and an alias plate on **all eight seats** at the board's
extreme cells (four placements, including the widest offer the config schema allows — 12 for 12),
decodes the packet with the sprite protocol's own `parseSpritePacket`, and fails if any object's
sprite leaves the 1536 × 864 board. That is precisely the fixture the reviewer's third
"could not determine" item asked for ("assert every overlay object's `x + sprite.width <= BoardW`"),
and it settles it: **every overlay fits, at every extreme.**

The overlay anchors are also now clamped on both axes (`overlayX` / `overlayY`) instead of only
downward, so the property is structural rather than a lucky font metric. The fixture stays (it is
checklist 15's required `ci.yml` step and it covers the DOM-side worst case), with a header saying
which file holds which half; the DOM feed at 360 px stays covered by `dom_text_smoke.mjs`
(`{"ok":true,…}` at 13 viewports in this run).

## F20 — `+` / `-` fixed, `f` deliberately inert

`advanceReplay` fell through to `else: discard` for `'+'` and `'-'`, which the page sends. They now
walk the same `PlaybackSpeeds` ladder the number keys select from — paintbot's own
`applySpeedCommand` behaviour. `tests/test_global.nim` drives the ladder in both directions,
including its ends, and checks a numeric key still selects directly.

`'f'` (skip-lulls) stays an explicit `discard`, **not fixed**: it toggles the starter's lull-skip,
and this game emits no `lulls` spans for it to skip (`buildStateJson` ships no `lulls` key). The
honest options are to implement lull detection (a design addition) or to delete an inherited
transport button (which checklist 14 reads as chrome the starter owns). Recorded, not changed.

## F21 — the nimby pin

`Dockerfile.replay-viewer` pinned 0.1.27 while `Dockerfile` and `ci.yml` pin 0.1.26, against
`ci.yml:34`'s own "Pins mirror the Dockerfile build stage; bump both together". The viewer image now
takes 0.1.26 with the matching sha256
`8e1e5c2769c657f599fb15dc4eef1bd861cdee898c6293d2a62df300c2f654c5` (computed from the released
asset), and its header names the three places that move together. The `wasm-viewer` job builds and
executes the bundle green at this head on that pin.

## F22 — `results.json` against the results **schema**

`docker_smoke.sh` checked the results *shape*. It now loads `game.results_schema` out of the
manifest — the same schema the platform applies — and validates `results.json` against it: required
keys, `additionalProperties: false`, array `minItems`/`maxItems`, item types and every `enum`. A
schema keyword the checker has not been taught is a hard `RESULTS-SCHEMA FAIL`, never a silent skip,
so the check cannot weaken as the schema grows.

Exercised locally against a real episode's `results.json` and against five mutations — bad `reason`
enum, an 11-entry `scores`, an undeclared key, a missing required key, a string in
`mean_rate_x100` — each of which fails with the right message. In CI at this head:

```
results.json validates against game.results_schema
smoke OK: seats=8 results=630B replay=169339B reason=complete
```

## F23 — the two missing assertions

* **Feed-row caps** (`tests/test_broadcast.nim`): the test now *builds* every feed row the way the
  page builds it — trade, offer with the seat's `say` quoted on the end, starve, exhausted — over a
  real episode's recorded events, and asserts each composed row is valid UTF-8 and inside a declared
  200-rune budget, plus the `say`/`notes`/policy-name caps its parts come from.
* **Determinism across a fresh server** (`tests/test_sim.nim`): the test binary re-execs itself with
  `--emit-game-hash <seed>`, plays the episode from a cold process and compares the `gameHash` with
  the in-process one — which is what would catch a sim depending on something a warm process carried
  in. A different seed is asserted to give a different hash, so the comparison proves something.

---

## The reviewer's four "could not determine" items

1. **Is `--timeout-seconds` valid on `coworld certify` 0.1.42?** **Yes** — `certify --help` from the
   pinned package prints `--timeout-seconds <float range> [default: 60.0] [x>=1.0]`. Fixed in F1.
2. **Does an artifact-write failure leave the process alive?** **No.** Under this build's exact
   flags (`-d:release -d:useMalloc --opt:speed --stackTrace:on`, the Dockerfile's `NimFlags`), an
   unhandled exception on a spawned thread terminates the whole process — reproduced in the sandbox
   with a thread that raises `IOError` mid-run: the process prints
   `Error: unhandled exception: … [IOError]` and exits; the main loop's remaining output never
   appears. So a failed `writeArtifact` kills the container rather than hanging it, and the platform
   sees a dead game, not a stuck one. No code change.
3. **Can the shipped renderer push an overlay outside the viewport?** **No** — settled by
   `tests/test_global.nim` (F19), which asserts it against the real `buildPacket` at every extreme
   cell and the widest legal offer, and by the anchors now being clamped on both axes.
4. **Do feasibility gates (a)–(d) hold at the retuned constants over 12 seeds?** Yes —
   `tests/test_feasibility.nim` is green in run 32907164596 (and locally: 13 checks, 53 s release).
   It was also re-run locally after every sim change in this round (F12 adds an event, not state;
   F13 only touches the forfeit path; F14 only touches parsing).

## NOTED (not fixed)

* `src/fruit_market/scripted.nim:13` imports `board` and `src/fruit_market/broadcast.nim:9` imports
  `strutils` without using them (compiler `UnusedImport` warnings, pre-existing at the reviewed sha).
  Not a finding in this round.
* `viewer_smoke.mjs` reports `feed_lines: 0` against the real bundle because it looks for
  `#feed, .feed, #log` and this game's feed is the starter's `#killfeed`. The reviewer records the
  same; `viewer_smoke.mjs` must stay byte-identical to the template, so this is not fixable here.
  `dom_text_smoke.mjs` covers the feed (`feed: 4` at all 13 viewports).
* The heavy suites (`test_baseline`, `test_feasibility`) run release-only in CI through the repo
  variable `NIM_TESTS_RELEASE_ONLY` — a workflow-supported narrowing that predates this round. Both
  also pass in debug locally; `test_baseline` debug takes ~4 minutes, `test_feasibility` debug well
  over 15.
