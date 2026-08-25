# r1 fixes — cooperative-hunting

Repo: `Metta-AI/cogame-cooperative-hunting`
Head: **80e2acf36048e0ffd9deb73592580f7d3d005f5c** on `main`
CI: run **32792004269** — `success` (`test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓)
<https://github.com/Metta-AI/cogame-cooperative-hunting/actions/runs/32792004269>

Two fixer threads worked this round. The first pushed B1–B4 (`d82261a6`, `2ed3fce2`, `e0f21ff`,
`591f8f1a`; CI 32774674232 green) and died before writing this file. This thread verified those four
against their findings and then dispositioned every advisory finding. 19 of the 25 findings are
fixed, 1 is refuted, 5 are deliberately not fixed with a reason.

No test was loosened, skipped or deleted. `git log -p -- tests/` over this round is additions only
(three test files gained blocks, one file was added: `tests/test_llm_retry.nim`); the two assertion
*messages* that changed (`"the chrome label is at most 4 KB"` → `"…inside the label cap"`) still
assert `label.len <= MaxChromeLabelBytes`, the constant they always asserted.

Everything below was run locally before it was pushed: a nimby/Nim 2.2.4 toolchain (every
`tests/*.nim` in debug **and** `-d:release`), the built game + six built player binaries over a real
websocket, and the worst-case renderer fixture in headless chromium at 360/640/1280 px.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | already fixed, verified | `d82261a6` | `tools/ci/viewer_smoke.mjs`, `.github/workflows/ci.yml:317-322` |
| B2 | fixed (prior `2ed3fce2` + two this thread) | `2ed3fce2`, `34212ee`, `b55fc2f` | `tools/ci/fixtures/*`, `client/replay_broadcast.html:1418-1450`, `tools/build_replay_page.py` |
| B3 | already fixed, verified | `e0f21ff` | `src/cooperative_hunting/sim_types.nim:521-531` |
| B4 | already fixed, verified (with a stated limit) | `591f8f1a` | `src/cooperative_hunting/replay.nim:517-525`, `tests/test_replay_parse.nim:123-195` |
| N1 | not fixed — reason stated | — | `src/cooperative_hunting/sim.nim:407` |
| N2 | fixed | `e1bf3c0` | `src/cooperative_hunting/llm.nim:474-508`, `tests/test_llm_reply.nim:119-147` |
| N3 | fixed | `fe440fa` | `tools/build_replay_page.py`, `client/replay_broadcast.html:1560-1620`, `tests/test_chrome.nim:243-252`, `tools/ci/fixtures/fixture_chrome_driver.js` |
| N4 | not fixed — reason stated | — | `client/replay_broadcast.html:1640-1668` |
| N5 | fixed | `09b55a0` | `client/replay_broadcast.html:1013-1030`, `tools/ci/fixtures/fixture_chrome_driver.js` |
| N6 | fixed | `1277a4f` | `src/cooperative_hunting/sim_types.nim:195-205`, `tests/test_chrome.nim:114-141` |
| N7 | fixed | `ddbe7a8` | `tools/build_manifest.py:685-700`, `coworld_manifest_template.json:558-567` |
| N8 | **refuted** — the code is right, the note's number is off by one | — | `src/cooperative_hunting.nim:382-383` |
| N9 | fixed | `b62107d` | `src/cooperative_hunting/llm.nim:401-420`, `sim_types.nim:213-220`, `tests/test_llm_reply.nim` |
| N10 | fixed | `80e2acf` | `tests/test_llm_retry.nim` (new) |
| N11 | fixed | `354d951` | `src/cooperative_hunting_player.nim:26-38, 292-306` |
| N12 | fixed | `43ee3c0` | `src/cooperative_hunting_player.nim:48-66` |
| N13 | fixed | `85a3774` | `tools/build_replay_page.py`, `client/replay_broadcast.html:1185` |
| N13b | not fixed — reason stated | — | `client/replay_broadcast.html:583-598` |
| N14 | fixed | `1eb39de` | `src/cooperative_hunting.nim:210, 417-430, 350-356`, `tests/test_scoring.nim` |
| N15 | fixed | `195dfbe` | `src/cooperative_hunting/replay.nim:175-200`, `tests/test_replay_parse.nim:54-64` |
| N16 | fixed | `a50f4f5` | `tools/build_manifest.py:15-22`, `coworld_manifest_template.json` (all four variants + fixture) |
| N17 | not fixed — reason stated | — | `client/broadcast_core.js:196` |
| N18 | fixed | `c000024` (superseded by `fe440fa`) | `client/replay_broadcast.html` |
| N19 | not fixed — outside this repo | — | `tools/ci/viewer_smoke.mjs` (coworld-builder template) |
| N20 | fixed | `7856adf` | `src/cooperative_hunting/llm.nim:401-410` |

---

## Blocking

### B1 — `--strict-text-bounds` and the current `viewer_smoke.mjs` — already fixed in `d82261a6`

Verified, not taken on trust: `diff templates/tools/ci/viewer_smoke.mjs tools/ci/viewer_smoke.mjs` is
**empty** (the committed copy is now the 709-line template verbatim, as §Packaging requires), and
`ci.yml:317-322` invokes it with `--strict-text-bounds`. The gate now produces a number: the
`viewer-smoke` artifact of run 32792004269 carries
`canvas_text: {total: 0, outside: 0, never_inside: 0, ellipsized: 0}`.

`total: 0` is expected and is called out in the template's own header: this board is drawn by
`BroadcastCore` inside an **OffscreenCanvas in a Worker**, which the instrumentation cannot hook, and
the chrome is DOM text. That is exactly why B2's fixture measures the DOM text itself. Checklist
item 15.

### B2 — worst-case renderer fixture — fixed in `2ed3fce2`, `34212ee`, `b55fc2f`

`2ed3fce2` (prior thread) added the fixture checklist item 15 asks for:
`tools/ci/build_worst_case_fixture.sh` assembles the **real** page (spliced exactly as
`Dockerfile.replay-viewer` splices the shipped bundle, with the real starter `chrome_common.js`; only
the wasm transport is stubbed) and `ci.yml` drives it with `viewer_smoke.mjs --strict-text-bounds`
against a frame built to hurt — a full-cap 120-rune remark on all six seats at once in latin, CJK and
emoji, six 64-rune policy names, a beat list at the label cap, the end-card open — at 360, 640 and
1280 px. `tests/test_chrome.nim` asserts the fixture frame is one `buildChromeLabel` can actually
emit.

Two things were wrong with it, and both are fixed here.

**`34212ee` — the gate was machine-dependent.** The harness stacks its three sized frames in one
page, so two of them sit below the fold where chromium throttles rendering. It waited a fixed 600 ms
for a 250 ms entrance animation and measured. Reproduced locally: the 640 px frame reported all six
rows still mid-`feedin` — translated right, past the frame edge, 60 % opaque — **12 failures on a
loaded machine, green on an idle CI runner**. `settle()` now finishes every running animation before
measuring, which is what "played through to settle" means; three consecutive clean local runs after.

**`b55fc2f` — the fixture missed the defect it was built to find, and the shipped viewer had it.**
`pumpFeed` appended the frame's feed lines to a list and rebuilt the whole `#feed` host from it. The
chrome label carries only the lines new since the previous frame, but the replay re-emits the **same
frame** for as long as the playhead sits on a tick (paused, scrubbed, parked at the end), so each
line arrived again on every one of those frames and the host was rebuilt at 8 Hz. Every row was
therefore permanently mid-`feedin`. **Evidence, in the CI artifact of the sha the previous thread
reported green**: `viewer-smoke.png` of run 32774674232 shows six identical `HUNT OVER — complete`
rows drawn past the right edge of the 1280 px frame, "complete" sliced off, at ~40 % opacity. That is
cogchemists' invisible sentence, in the one element B2 is about.

The feed now dedupes on the line's own identity (tick, kind, text) and appends only what is new; a
seek clears it. The fixture gates it: it hands the page the same frame twice and fails unless the row
elements are the same nodes. Verified failing before (39 failures across all three widths) and
passing after.

Evidence at the reported head: the `worst-case-fixture` artifact of run 32792004269 reports
`360x640: 6 full-cap rows, shortest 120 runes, widest 258 px … OK`,
`640x520: … 459 px … OK`, `1280x700: … 512 px … OK`, `all frames pass`, with
`canvas_text {total: 0, never_inside: 0, ellipsized: 0}` — and `viewer-smoke.png` of the **real**
bundle now shows one settled feed row inside the frame. Checklist item 15.

### B3 — the 60 % budget — already fixed in `e0f21ff`

Verified by re-tracing every bound at the reported head:
`playerConnectTimeoutSeconds` **45** (`sim_types.nim:527`) + `sleep(500)` registration grace +
`playBudgetSeconds` **600** (`sim_types.nim:526`) + LLM-thread join ≤ 2 × `planTimeoutSeconds` 12 =
24 + `ShutdownGraceSeconds` 20 = **689.5 s = 57.5 %** of the declared `episode_timeout_minutes: 20`
(1200 s), inside the 60 % (720 s) rule. `coworld_manifest_template.json` carries the same two
defaults and `tools/build_manifest.py` regenerates it byte-identically (checked). The natural end is
unchanged: 2880 play ticks + round cards at 8 Hz ≈ 375–380 s, and this round's docker-smoke episode
ran the 1040-tick fixture to `reason=complete`. Checklist item 5.

### B4 — frame-by-frame reproduction — already fixed in `591f8f1a`, with a limit worth stating

Verified. `tests/test_replay_parse.nim` now replays the whole episode through the viewer's own path
(`parseReplayDoc` → `initSimFromDoc` → `applyTick` for every tick), re-records each tick with the
**same `ReplayWriter` the live server uses**, and asserts the re-derived tick object equals the
recorded one field for field — every tick, positions, facing, energy, score, flags, prey, items,
berries, corpses — on staghunt **and** on predator-prey (whose roles come from `rounds[].roles` and
whose tall-grass flag is recomputed from the re-derived position). Because `q` and `c` are omitted
when unchanged, it also pins the document's one compression. The test earned its keep: it found that
`applyTick` dropped `pushStep`, so every tick on which a hunter was being shoved by a moose came back
without its `FlagAlerted` bit; `591f8f1a` restores it. The display half was already the game's own
`buildGlobalFrame`.

**The limit, for the judge:** this replay records **state, not inputs** — the design note says so
(§Viewer, design.md:621-625) and `cooperative_hunting_replay.nim:207-210` says so in a comment. So
"replaying the recorded *events* through the sim" in the literal sense of `sim.step()` is not
available, and a `stateDigest` comparison is not either: the digest covers internal counters
(`moveCooldown`, `respawnIn`, prey `thinkCooldown`, `strideRemaining`, `sim.nim:1277-1302`) that the
document deliberately does not record. What is asserted is the strongest property this format admits:
every recorded field is reproduced frame by frame by the viewer's re-derivation, and the viewer draws
from that re-derivation. Recording inputs instead would be a replay-format change, i.e. a design
change — flagged, not made. Checklist item 2.

---

## Advisory — fixed

### N2 — `parsePlan`'s four byte slices — `e1bf3c0`

`intent`, `side`, a `with` entry and `target` were cut with byte slices. The reviewer is right that
none of them can reach the replay byte-cut today (each is coerced, dropped, or raises), but
rune-safety is a property of the parser, not of what happens to survive it, and the next field added
here would inherit the byte slice. All four now go through `runeCap`.
`tests/test_llm_reply.nim` feeds an emoji intent, side, ally name and target at forty times the cap
and asserts the coercions and that the rejection message is still valid UTF-8. Checklist item 9.

### N3 — the page now instantiates `chrome_common.js` — `fe440fa`

The page loaded chrome_common, guarded on it in `need()`, and then never called
`window.ChromeCommon(...)`: the transport bar, the speed chips, the scrubber geometry, the tick
clock, the lull spans, the momentum band and the spoiler toggle were all re-implemented in the game
block — the shape a lookalike has, and the reason `#lulls`, `#momentum` and `#scrub-win` were resolved
by nothing.

ChromeCommon is now constructed with its three hooks (`send`, `sendPov`, `getState`) and owns the
transport: it builds the speed chips, `renderTransport` paints the play/loop/skip glyphs, the current
chip, the scrub fill and head and `#tick-clock`, and it owns `#btn-spoilers` — its `?spoilers=` URL
default, its class and its listener. `buildSpeedChips`, the hand-rolled scrub geometry, the
hand-rolled tick clock and the local spoiler toggle are gone. The game block keeps only the half
chrome_common has no shape for: the round clock (a hunt has rounds and a round card, not a countdown
to a draw limit), the six hunter plates, the feed, the end-card, and the beat markers — ours are
**labelled `<button>`s that seek**, which is what 14(d) asks for and what the starter's `markBeat`
(an unlabelled div) cannot produce.

The momentum band is left empty on purpose: it draws a lives **lead between sides** and a hunt has no
sides; feeding it six same-coloured score lines would be a fiction.

Gated twice: `tests/test_chrome.nim` asserts the page instantiates ChromeCommon, renders the transport
through it and reads its spoiler toggle; the worst-case fixture asserts at all three widths that the
speed chips exist with one current, that `#tick-clock` reads `n / m`, that the play glyph is not the
play arrow while playback runs, and that the transport, scrubber, momentum and lull bands are inside
the frame. Visible in this round's `viewer-smoke.png`: the bar now carries chrome_common's
`1× 2× 3× 4× 8× 16×` chips and its `1039 / 1039` clock. Checklist item 14.

### N5 — a hunter plate wraps instead of being sliced — `09b55a0`

`.hplate { min-width: 0; flex: 1 1 0 }` let three plates share a 640 px half by shrinking below the
width their own furniture needs, and `#scorebug .plates { overflow: hidden }` cut the overflow off:
in run 32774674232's screenshot every 1280 px plate carried 259 px of content in a 153 px box, the
fifth seat's score sliced by the sixth seat's colour chip and the sixth's by the frame edge. The
plate now floors at the room its chip, alias, name (at the name's own 3.2em floor), energy bar, badge
and score take, and wraps when it cannot have it — the band grows and `relayout` reports the new
`--topband`, so the board follows. Names may still ellipsize, which item 15 allows for a **label**;
scores may not, and no longer do.

The fixture now measures plates too (spill out of its half of the scorebug, out of the band, overflow
of its own box, and any alias/score/energy bar drawn outside its plate or the frame), verified failing
on the old CSS at 1280 px and passing at all three widths after. This round's real
`viewer-smoke.png` shows six plates with whole names and whole scores. Checklist items 15 and 11.

### N6 — a manifest-length episode keeps every beat — `1277a4f`

`beats` ships complete on the first frame and the trim loop drops beats **from the front**, so the
4 KB cap cost the scrubber the opening of the hunt on any full-length variant (measured rate
0.042 beats/tick × 3000 ticks ≈ 127 beats ≈ 3.6 kB, plus seats and remarks). `MaxChromeLabelBytes`
4096 → 12288; the label rides in a u16 length field (`art.nim:543`), so 12 kB is well inside the wire
format, and the trim loop is untouched. `tests/test_chrome.nim` now asserts what was extrapolated:
150 beats plus six seats speaking 120 runes of CJK on one frame fit, no beat is dropped, and the beat
at tick 0 survives.

### N7 — the certification fixture carries `tokens` — `ddbe7a8`

`config_schema` lists `tokens` in `required`, so a fixture without it did not validate against the
game's own schema. Six empty strings: schema-valid (`minLength: 0`) and `tokenValid()` treats an
empty configured token as "no token for this slot", so behaviour is unchanged;
`tools/ci/docker_smoke.sh` still injects its own six over the top. Checklist items 6 and 10.

### N9 — the observation is bounded at 2000 runes — `b62107d`

Measured over 900 ticks × 6 seats: the bounded lists come to at most **1596 runes**, so the only part
that overran the note's 2000 was the `STRATEGY` block appended after them. The strategy now takes the
room left under the bound and the whole string is `runeCap`ped as a backstop; no seat loses its
strategy, because `systemPromptFor` carries it in full on the same request. The test asserts the
bound and that `LEGAL TARGETS` / `BLOCKED TILES` / `YOUR NOTE` survive the cap.

### N10 — the two-attempt retry loop is now driven — `80e2acf`

`tests/test_llm_retry.nim` runs the real path: the client's Bedrock endpoint comes from
`AWS_ENDPOINT_URL_BEDROCK_RUNTIME`, so a local mummy stub drives the real `requestFor`, the real
curly batch, the real `textOf` and the real `parsePlan` with **no seam added to the production
client**. For a target outside `LEGAL TARGETS` — the failure the note names — it asserts: one bad
reply then a good one ⇒ the seat comes back with the retry's plan, the endpoint saw **exactly two**
requests and only the second carried `RetryHint`; two bad replies ⇒ `ok == false` with
`fcIllegalTarget` and **two requests, not three**. `planTimeoutSeconds` is 5 there, so a wedged stub
fails rather than hangs. Checklist item 8.

### N11 — the player's blocking read is bounded — `354d951`

`ws.receiveMessage(-1)` blocks forever; it was bounded only by the game closing the socket. Now 5 s
per read (40 frames at 8 Hz, so it never fires during play) and 120 s of total silence before the
process exits 0 like every other give-up path here — comfortably longer than the 45 s roster wait
before the first frame. Verified outside CI: the built server and six built player binaries over a
real websocket, roster 6/6, `reason=complete`, both artifacts written, all six players exiting 0 on
the close frame. Checklist item 5.

### N12 — `PLAYER_SCRIPTED` wins on a scripted seat — `43ee3c0`

The fallback variable was read first, so a seat carrying both played the fallback bot and the
variable that names what a scripted seat plays was ignored. A seat with no `PLAYER_PROMPT` now takes
`PLAYER_SCRIPTED`; a prompt seat still takes `PLAYER_FALLBACK_SCRIPTED`. Verified against the built
binary: with both set and no prompt it logs `policy=sidekick`, not `rabbiteer`.

### N13 — `#bannerlane` is back in the markup — `85a3774`

The generator deleted the element while keeping the whole "3. BANNER LANE" CSS section, so the page
diverged from the starter by a removal the note does not list. An empty lane draws nothing
(`pointer-events: none`, reserved min-height). The page still reproduces byte for byte from the
starter and the fixture passes with the lane present. Checklist item 14.

### N14 — a skipped planning turn leaves a trace — `1eb39de`

A boundary that arrives while the previous batch is in flight still returns early — the sim never
waits for the model — but it now increments a counter reported as `results.plan_turns_skipped`, next
to `llm_requests`, so phase 60 can tell a slow endpoint from a healthy one. Present in this round's
`smoke-replay/results.json`: `plan_turns_skipped: 0`.

### N15 — the replay config carries every resolved field — `195dfbe`

`closedRoster` and `focusElephant` are in `configNode` now, and the test asserts the full 15-key list
rather than two spot checks, so the next field added to `GameConfig` and not to `configNode` is
caught.

### N16 — manifest display names are not the aliases — `a50f4f5`

All four variants and the fixture listed `players[]` as `Cog-A … Cog-F`, the in-game aliases, while a
seat's alias is an independent seeded permutation — the one place a reader compares the two name
spaces conflated them. They are `Hunter 1 … Hunter 6` now, which is what they are: the spectator-side
fallback for a seat whose real policy name did not arrive on `?name=`. In practice the player binary
always sends `?name=`, so nothing observable changes (this round's `results.names` still reads
`cooperative-hunting-prompt`, `big_game_hunter`, …). Checklist item 4.

### N18 — the play button shows the action it performs — `c000024`

The glyph was inverted (play arrow after starting playback). Fixed in `c000024`; `fe440fa` then
handed the button to chrome_common's `renderTransport`, which uses the same (correct) rule, so the
game block no longer draws it at all. The fixture asserts the play arrow is not showing while
playback runs.

### N20 — `RECENT` prints one line per entry — `7856adf`

The header promises "<=5 lines" and the entries were concatenated onto the header's own line. Each
entry starts on its own line now; the list is still capped at five and the observation is still
inside its 2000-rune bound.

---

## Advisory — refuted

### N8 — `turnsTotal` is 24 and 24 is correct

Not a code defect. Instrumented the real server loop (a temporary `echo` at the dispatch site,
`rounds: 2, ticksPerRound: 240, planIntervalTicks: 120`, six connected players, run to
`reason=complete`): the boundaries were exactly
`round=0 tickCount=0, 120; round=1 tickCount=0, 120` — **four**, and
`(2 × 240) div 120 = 4`. The formula matches the loop exactly, so a 3 × 960 variant has 24 planning
turns and the observation header `TURN n/24` is honest. The design note's "25 planning turns"
(design.md:281-282) is prose that counts the boundary at the end of the last round, which the loop
never reaches. No behaviour depends on the value; it is printed and nothing gates on it. Code left
alone.

---

## Advisory — not fixed, with reasons

### N1 — `sim.captureRule` is set and asserted but never read

Correct as observed, and left alone deliberately. Resolution dispatches on entity kind, and the
variant determines which entity kinds exist, so the two are equivalent by construction — the
reviewer says so too. Rewriting `applyAnimalCaptures`/`applyItemCaptures` to branch on the enum would
be a no-op refactor of the game's most load-bearing procs (the capture rules are what
`tests/test_capture.nim` pins across four variants) in exchange for nothing observable. The enum is
not dead in the sense that matters: it is a declared invariant per variant and
`tests/test_capture.nim:94,171` assert it. Not a checklist item.

### N4 — `relayout()` is not the starter's

Correct as observed. Not adopted, because the starter's `relayout()` is inseparable from a layout
model this game does not use: it sizes `#stage` in px to the **board's** aspect and letterboxes the
whole composition inside `#viewport`, and it iterates the bands to a fixed point precisely because
its `--hudscale` depends on the resulting board width. Ours delegates the fixed-aspect fit to
`core.setViewportFit()` (the wasm core owns the canvas) and lets the chrome span the frame — which
this game needs, because six hunter plates in a letterboxed 643 px stage would wrap into a band
taller than the board it is reserving space above (checked at 1280 × 800). The fixed-point iteration
is also unnecessary here: `--hudscale` is a function of the stage width alone and the bands do not
feed back into it, so one pass is exact.

Checklist 14(a) is met either way, and the reviewer agrees: `relayout()` measures `#transport` and
sets `--band` (and `--topband`, and `--hudscale`) on `document.documentElement`, which is what
`--u`, `#board` and `#endcard` read.

**NOTED (not fixed):** ours re-arms with `requestAnimationFrame`, so it reads `offsetHeight` every
frame. A `ResizeObserver` would be cheaper. Left alone — no finding, and the rAF loop is what
notices a board-box change and re-fits the viewport.

### N13b — the starter's own beat-marker kinds survive as dead CSS

Correct, and deliberately kept. Checklist item 14 asks that the CSS above the banner comment be the
starter's, **unmodified except for the removals the design note lists** — deleting
`.beat-marker.kill/.steal/.return/.capture` would be a new unlisted removal, i.e. a step away from
the item it would be serving. The failure mode 14(d) names is the reverse (a kind the page emits with
no rule), and `tests/test_chrome.nim` asserts every emitted kind has one.

### N17 — the literal `/client/replay` in `client/broadcast_core.js`

Correct, and it must stay. The file is **byte-identical** to the starter's
(md5 `677fe90f2be107b810c24aef02b936a3` both sides, re-checked at this head), which checklist item 14
requires; editing the line to satisfy a grep would break the item that actually protects the chrome.
The line is inside the starter's live-websocket route-derivation table and no such route exists here:
`isStaticRoute` (`src/cooperative_hunting.nim:689-696`) serves only the player/global/snappy client
routes, and `grep -rn runReplayServer src/` returns comments only. The viewer this repo ships is the
static bundle declared by `"replay_viewer": {"bundle": "static-replay-viewer"}`, whose only egress is
`fetch(replayUrl)` from `?replay=`. Checklist item 3 is met in substance.

### N19 — the 0 % scrub probe returned the pre-scrub clock

Observation about the harness, not about this repo. The probe lives in `tools/ci/viewer_smoke.mjs`,
which B1 requires to be the coworld-builder template **verbatim, no substitutions** — so any fix
belongs upstream in `templates/tools/ci/viewer_smoke.mjs`, not here. The assertion it feeds
(three distinct clocks) passed at this head, and the 50 % and 100 % probes differ. What would settle
it upstream: read the clock after an explicit `advanced` round-trip, or add a 25 % probe as a control.

---

## Verification at the reported head

- `gh run list -R Metta-AI/cogame-cooperative-hunting --branch main -w ci.yml` → run
  **32792004269**, `success`, on `main`, for `80e2acf` — `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓
  (including `Load the bundle in a real browser` **and** the two new worst-case fixture steps).
- `grep -c "SEAT-COUNT FAIL"` over the docker-smoke log → **0**; the smoke reached
  `reason=complete` with six seats.
- `diff tools/ci/viewer_smoke.mjs <coworld-builder template>` → empty.
- `md5sum client/chrome_common.js client/broadcast_core.js` → `80ea4eb19cee21cb61fb1f009f1f45ab`,
  `677fe90f2be107b810c24aef02b936a3` — both identical to `/workspace/starters/coworld-ctf`.
- `python3 tools/build_replay_page.py /workspace/starters/coworld-ctf | diff - client/replay_broadcast.html`
  → empty (the page is still provably the starter's page plus the game block).
- `python3 tools/build_manifest.py | diff - coworld_manifest_template.json` → empty.
- Local: all nine `tests/*.nim` pass in debug **and** `-d:release` (18 runs).
- Local: the worst-case fixture passes at 360 / 640 / 1280 px in headless chromium, three runs.

**Note on how these commits reached `main`.** `git push` over HTTPS stopped authenticating in this
sandbox mid-round (a `gh auth setup-git` call overwrote the sandbox's credential helper — the failure
the playbook documents; the global helper has been restored to
`/usr/local/bin/git-credential-anthropic`). The seventeen commits were replayed onto `main` through
the GitHub Git Data API, one API commit per local commit, same message, same author, same order. The
final tree sha was compared against the local `HEAD` tree before the ref was moved and they agree
(`deb5e2a1c365492dcfd46443c64f1d37b0327732`), so the pushed tree is exactly the tree that was tested
locally. The shas in the table above are the pushed ones.

FINAL SHA: 80e2acf36048e0ffd9deb73592580f7d3d005f5c
CI RUN: 32792004269 success
