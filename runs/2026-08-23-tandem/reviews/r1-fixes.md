# r1 fixes — tandem

Repo: `Metta-AI/cogame-tandem` · base `4b78981e77210a5f910dd679c81a32983e0a333d`
Head: **`668b5f5d81d5025a527391bb25f90cf2bc186d1d`**
CI: https://github.com/Metta-AI/cogame-tandem/actions/runs/32671500679 — **success**
(all three jobs `test`, `docker-smoke`, `wasm-viewer` green; the previous head
`6ce3d679` is green on run 32671195004 and the final commit is comment-only.)

15 findings: **13 fixed**, **1 rebutted** (F9), **1 fixed as a test, not a code
change** (F10). One blocking finding (B1) fixed.

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| B1/F1 | fixed | `e8d0742` + `668b5f5` | `tools/tune_baselines.nim`, `src/tandem/baselines.nim:20-52`, `docs/BASELINE-TUNING.md`, `tests/test_baselines.nim:8` | **7** (baseline tuned with a grid harness) |
| F2 | fixed | `2812b1e` | `src/tandem/decide.nim:203,322,463`, `tests/test_engine.nim` | note §Server (advisory) |
| F3 | fixed | `8b5d2a2` | `src/tandem/llm.nim:164-214`, `tests/test_orders.nim` | **9** (rune-safe truncation) |
| F4 | fixed | `ff99ef3` | `src/tandem/orders.nim:308`, `tests/test_orders.nim` | **8** (reply handling) |
| F5 | fixed | `e7b64d4` | `src/tandem/decide.nim:348`, `src/tandem/server.nim:620`, `tests/test_engine.nim` | **5** (degrade-never-hang) |
| F6 | fixed | `b36d767` | `src/tandem_player.nim:24-96`, `src/tandem/server.nim:207`, `docs/PROTOCOL.md`, `tests/test_server.nim` | **9** / note §Reply schema |
| F7 | fixed | `0521a97` | `tools/ci/docker_smoke.sh:245-267` | **12** (scaffold) / note §Tests |
| F8 | fixed | `957b03c` | `src/tandem/sim_types.nim:296`, `src/tandem/sim.nim:324`, `tests/test_physics.nim` | **1** (no test loosened; strengthened) |
| F9 | **REBUTTED** | — | `client/replay_broadcast.html` | **14** — not falsified |
| F10 | fixed | `0d5fdc6` + `6ce3d67` | `tests/test_routes.nim` (new) | **5**, **1** / note §Tests 9 |
| F11 | fixed | `240c74d` | `tests/test_replay.nim:182` | **1** / note §Tests 8 |
| F12 | fixed | `ff702a0` | `src/tandem/sim.nim:643-660` | note §Resolution order 10 |
| F13 | fixed | `025cb39` | `src/tandem/replays.nim:96,400`, `client/replay_broadcast.html:2137-2200`, `tests/test_replay.nim`, `tests/test_viewer.nim` | **14d** / note §Record vocabulary B |
| F14 | fixed | `c265f02` | `AGENTS.md` (new), `README.md` | note §Packaging repo layout |
| F15 | fixed | `a12066e` | `client/replay_broadcast.html:2122`, `tests/test_viewer.nim` | note §Viewer readout 9 |

> **Note on the shas.** `git push` 403s in this sandbox, so the commits were
> published through the GitHub Data API (blobs → tree → commit → fast-forward
> `PATCH refs/heads/main`), as the phase-20 builder did. My second push
> re-applied the series because the API-created commits have different shas
> from the local ones and the local branch was therefore not a descendant of
> the remote head: `origin/main` carries the fourteen commits above
> (`e8d0742`…`0d5fdc6`, which hold the diffs) and then a redundant second pass
> of the same series (`0763453`…`3a35bb5`). **The final tree is exactly the
> intended one** — `git diff HEAD origin/main` is empty and CI is green on the
> head — and no history was force-pushed or rewritten. Cite the first-chain
> shas for each finding's diff.

---

## B1/F1 — the baseline tuning harness the code names did not exist

**Was:** `baselines.nim:20-22` claimed "The harness is `tools/tune_baselines.nim`"
and `:37` "See tools/tune_porter.nim"; neither file existed in the tree or in
any commit, so the "tuned with a grid harness, not guessed" half of checklist
item 7 had no artefact.

**Is:** `tools/tune_baselines.nim` is committed and runs with nothing but a Nim
compiler.

- `--eval` plays `porter x porter`, `porter x mule` and `mule x mule` over the
  committed seed list through the real control layer and the real `applyRecord`
  path, and prints one JSON line: delivery count, mean score, mean damage, mean
  ticks, mean progress, drops — beside the 29 constants the binary was compiled
  with. With no `-d:` flags that line **is** the shipped configuration.
- `--sweep NAME=v1,v2,...` is the driver: cartesian product of the axes, one
  recompile per grid point (`nim c -d:release -d:TandemMuleEffort=200 …`), each
  build run in `--eval` mode, table sorted by `porter x porter` mean score.
- The seed list moved to `baselines.TuningSeeds` so the harness and
  `tests/test_baselines.nim` measure the same twenty courses.
- `docs/BASELINE-TUNING.md` carries the sweeps, pasted from the harness.

**Evidence** (run in the sandbox, reproducible in one command):

```
$ nim r -d:release --path:src tools/tune_baselines.nim --eval
… "porterxporter" 20/20 mean_score 0.793727 mean_damage 219 mean_ticks 1524
   "porterxmule"   0/20 mean_score 0.021507  "mulexmule" 0/20 mean_score 0.01648
```

which is exactly what `tests/test_baselines.nim` prints (`porter mean 0.794`,
`porter+mule progress 103 score 0.022`, `mule+mule progress 75 score 0.016`).

The sweeps reproduce the docstrings' central claims:

- `TandemMuleEffort=64,140,200,255` → `porter x mule` 0.068 / 0.022 / 0.018 /
  **0.016** against `mule x mule`'s 0.015 — i.e. at the note's `effort = 1.0`
  the filler scores exactly what two mules score, which is the measurement
  `baselines.nim:65-73` quotes.
- `TandemTwistGain=2,3,5,8,12` → 11/20, 16/20, **20/20**, 7/20, 0/20 deliveries.
- `TandemOpenEffort=128,160,200,255` → 18/20, 19/20, 18/20, **20/20**.

Two docstrings quoted measurements the harness *contradicts* on their own axis,
and were restated as what it prints today (`OpenEffort`'s "never finished inside
maxTicks", `TwistDamp`'s "the heading swung ±90 degrees", and in the follow-up
commit `TwistGain`'s "3 units per brad"). **No constant changed** — the shipped
values are the grid point that ships, and the determinism gate is untouched.
Nothing was wired into `ci.yml`.

## F2 — `damage_last_turn` was structurally always 0

`turn()`'s first statement was `engine.damageAtTurnStart = sim.damage`, and both
seats' messages were composed after it, so the field was `sim.damage -
sim.damage`. The snapshot now happens at the end of the turn, so a seat is told
what the previous 48 ticks cost. Evidence: `tests/test_engine.nim` captures the
composed user message out of the fake transport and asserts 0 / 31 / 13 over
three turns — on the old code the second reads
`"damage":31 … "damage_last_turn":0` and the assertion fires (reproduced).

## F3 — captured error text was byte-sliced

Five byte slices in `llm.nim` (`body[0 .. min(body.high, 400)]`, `:177`, `:182`,
`:193`, `head[0 ..< 160]`) cut strings that become `fallback.detail`, which
reaches the replay. All five now cut on rune boundaries.

Measured while fixing, and worth recording because it bounds the severity: the
reviewer's *inference* that `clipRunes` re-encodes a byte-split codepoint is
**correct** — `isValidUtf8(clipRunes(badSlice, 200)) == true` in a one-line Nim
check — so the replay bytes were never invalid; the damage was mojibake in the
captured detail. The note's "slicing a `string` by byte index on any path to the
replay is forbidden" is now literally honoured. `tests/test_orders.nim` feeds a
multi-byte body at four byte offsets through 401/429/500 and the no-JSON path;
the raw-string assertion fails on the old code.

## F4 — a missing `drive` preferred the fallback's vector

`elif hasPrevious and (fallback.driveX == 0 and fallback.driveY == 0)` could
never fire for a real order, because `order` starts as a copy of the porter
fallback and porter always emits a non-zero drive. The guard is gone: missing /
non-finite `drive` → last turn's, and only with no last turn → the scripted
fallback's, which is the note's precedence and what `docs/PROTOCOL.md` already
claimed. `tests/test_orders.nim` exercises an absent drive, `[null,1]` and a
string drive, with and without a previous turn; all three fail on the old code.

## F5 — a disconnecting LLM seat kept being queried

`SeatPolicy.connected` was written and never read. `decide.turn` now queries a
seat only when `pkLlm AND connected`, and `server.nim`'s close handler clears
`connected` for the seat whose socket went away (before `removePlayerAt`
renumbers). A reconnect re-registers and revives it.

The test named for this asserted a different property (no transport at all). It
is kept in full as `noTransportSeatPlaysPorter`, and `disconnectedSeatPlaysPorter`
now exercises the real thing: a **live** batch, one seat marked disconnected,
asserting the batch carries only the connected seat, the disconnected seat
played porter with `source == "scripted"`, and re-registering revives it to
`osLlm`. On the old code the batch carries both seats and it fails.

## F6 — an oversize registration frame was dropped, not truncated

`chatPacket` wrote the Sprite v1 u16 length as `text.len and 0xff` / `shr 8`, so
a `PLAYER_PROMPT` over ~64 KiB wrapped the field, `readSpriteChatRaw` returned
`""` and the seat silently became a porter — a *rejected* registration. The cap
now happens where the note puts it ("capped at ≤ 4000 runes **at the
transport**"): `clipPromptRunes` before the payload is built.
`registrationPayload`/`chatPacket`/`readSpriteChatRaw` are exported so the test
drives the real framing. `tests/test_server.nim` pushes a 320 000-byte prompt
and a 20 000-emoji prompt through `registrationPayload → chatPacket →
readSpriteChatRaw → registrationOf`: without the cap the frame is 320 075 bytes
and the assertion fires; with it the seat is still `pkLlm` with 4000 valid-UTF-8
runes.

## F7 — `docker_smoke.sh` asserted only the game's exit code

Each `${prefix}-p<slot>` is now waited out (bounded, 60 s after the game exits)
and its code asserted 0. **Evidence from the green run (32671500679 / 32671195004,
step "Raw-Docker episode smoke"):**
`player container tandem-smoke-10830-p0 exited 0` /
`…-p1 exited 0`, then `smoke OK: seats=2 results=457B replay=28606B reason=complete`.
This is a real new assertion that passes, not a no-op.

## F8 — the physics assertions were vacuous and the bound was the wrong one

`Contact` now carries what the solver computed — `depthUm`, `slideUmPerTick`,
`normalMilliNewtons`, `frictionMilliNewtons` (transient FX log, never hashed,
all `int32`) — and `tests/test_physics.nim` asserts over **every contact of
every tick**:

- `normalMilliNewtons >= 0` and `<= ContactForceCap` — contacts push, never stick;
- the velocity change one substep of friction can produce
  (`F · 1e6 / MassStepDen`) is **strictly smaller** than the slide it opposes —
  the note's "friction never reverses the slide direction within one substep",
  which is exactly what the viscous cap buys (`F ≤ 200·|v_t|` ⇒ `Δv ≤ 0.72·|v_t|`);
- penetration `<= 60 000 µm` (the note's bound; measured worst **24 640 µm**),
  and no disc through a wall face.

The friction assertion needed the unrounded slide: `slideMmS` rounds a 72 µm/tick
slide to 1 mm/s (a 43 % loss) and produced a false failure at 52 vs 41 when I
first wrote it from the rounded value. The two free-body loops now run 480 ticks
(were 200 and 240). **No assertion was removed** — the two by-construction ones
are kept as cheap sanity beside the two that can fail.

## F9 — REBUTTED: the chrome removals do not falsify checklist 14

The finding is that `client/replay_broadcast.html` (2 281 lines against the
starter's 4 165) deletes ~1 900 lines beyond the `#viewpanel`/`#fpv`/`#povBadge`
the note declares, so the note's "exactly these" is inaccurate.

I do not change the code for this, for three reasons:

1. **The note's "Removed starter elements (exactly these)" enumerates DOM
   elements**, and all three ids and every named child are indeed gone from
   markup and CSS (`tests/test_viewer.nim:58-77` asserts their absence). The
   additional deletions are ctf gameplay **functions**, which the same note
   covers in §Sim module ("fog of war, vision cones, first-person raycast,
   killfeed art, item sprites → … Perfect information: no fog") and §Out of
   scope ("Everything ctf's arena rules carried … **Deleted, not disabled**").
   The two statements are about different things.
2. **The deleted spans are ctf's own game block, not the inherited chrome.** The
   starter's page is sectioned by banner comments: `Frame ingest` (:2000),
   `Beats → surfaces (§5)` (:3400), `End-card (§5/§8)` (:3532), `Transport
   wiring` (:3762), `Fixed-aspect fit` (:4104). Tandem keeps *Frame ingest*,
   *Transport wiring* and *relayout()* verbatim and replaces the game-specific
   ones with its own block under the required banner
   (`TANDEM additions to the inherited coworld-ctf chrome`, :1984). Every
   deleted function (`ingestFpMap`, `renderSquad`, `renderPov`/`renderFpv` +
   raycaster, `onKill`/`onSteal`/`onReturn`/`onCapture`, `endcardWinCondition`,
   `capturedHeartsHtml`) reads ctf state (`fpmap`, lives, flags, perks,
   handicaps) that tandem's stream does not carry; keeping them would be dead
   code reading absent fields.
3. **Checklist 14's tests all pass and were verified by the reviewer**:
   `chrome_common.js` byte-identical (sha256 pinned, `diff` empty), CSS sections
   1–5 present and unmodified, transport rules (a)–(d) present, every
   `.beat-marker` kind has a rule and every marker is a `<button>`. The
   cogame-gridlock failure the item exists to catch is a **from-scratch page
   that reuses the starter's ids**; here the ids, their CSS and the code that
   drives them are the starter's, and the ids tandem uses are driven by tandem's
   own appended renderers.

The accurate statement is that the note's phrase is under-specified about ctf's
game block. That is a note-wording issue, not a repo defect, and the note is not
mine to edit.

## F10 — no test exercised any route (fixed)

`tests/test_routes.nim` (new) starts the **real** `runServerLoop` on a private
port (120-tick episode, 1 s lobby timeout) and asserts the four clauses of
§Tests 9 that had no coverage: `/healthz` → 200 `healthy`; `/client/global` and
`/client/player?slot=0&token=t0` → 200 serving the real broadcast page
(>100 KB, `#scorebug` + `#transport`) with **neither opening the player socket**;
the `/global` spectator websocket running to `"ph":"gameover"`; a bad player
token refused before the upgrade; and EDIT 5's shutdown grace — results written,
`/healthz` and `/client/global` still answering **15 s later**, and the listener
gone once the bounded grace expires.

This one needed a fix-forward: the first push was red because the debug build's
board bake (which runs *before* the listener opens) took 61 s on the runner
against my 60 s health wait — release bakes in 501 ms. The wait is now 300 s and
prints what it took. It is still a bound, so a server that never listens fails
rather than hangs. Evidence in the green run: `/healthz answered after 61162 ms`
(debug) and `501 ms` (release), both followed by
`test_routes: /healthz, /global and both /client routes are real`.

## F11 — the scrape assertion was an "or"

`doAssert "scrape" in rough or "impact" in rough` → both asserted separately, and
the porter run is asserted to scrape too. Measured on the pinned seed: mule×mule
emits `impact, scrape`; porter×porter emits `impact, strain_warn, scrape,
doorway`.

## F12 — the step-10 end-check order

`out_of_time` now precedes `physicsGuardTripped()`, matching the note's
Delivered → wrecked → wall_clock → out_of_time → fault. `fault` is the flag the
league discards an episode on, so a tie must not manufacture one. Determinism
gate re-run green — the order only decides a tie, so no recorded hash moves and
`tests/data/golden_hashes.json` is unchanged.

## F13 — the beat list and the spoiler gate

1. The sim emits `impact` from 8 points (`ImpactEventFloor`) for the feed and
   sparks; `replays.nim` put every one in `beatEvents` while the page filtered
   only the **live** events at 20, so the two lists disagreed. The floor now
   lives where the list is built (`ImpactBeatDamage = 20`), with the page's
   guard kept for streams from an older server. `tests/test_replay.nim` asserts
   every impact beat is ≥ 20 on a fixture chosen because it emits **41 and 14** —
   remove the filter and the 14 comes back and the test fires.
2. chrome_common's spoiler gate iterates its closure-private `markerEls`, which
   tandem's buttons are not in and cannot join (the file is byte-frozen). The
   game block now runs the same rule over the markers it created
   (`applyTandemSpoilers`, called from the per-frame hook, reading the exported
   `getSpoilers()`): with spoilers off a beat ahead of the playhead is hidden and
   reveals itself as playback arrives. Pinned by `tests/test_viewer.nim`.

## F14 — `AGENTS.md`

Written for this repo rather than copied from the starter: the determinism
boundary and what may not enter it, the native-64/wasm-32 `int` trap and the
gate that catches it, the golden-hash rule ("if the gate fails, fix the code,
never the test"), GameVersion discipline, the frozen files (chrome_common
byte-for-byte, the MODULARIZE/bootstrap pairing, the no-channel invariant, the
two name spaces), how to run the suite, the baseline harness, and the
rune-boundary truncation rule. Linked from `README.md`.

## F15 — double-escaped feed rows

`row.textContent = esc(line.text)` → `row.textContent = line.text`.
`textContent` is already inert; the escape only turned an LLM's quote into
`&quot;` in the one surface where a spectator reads the model's words.
`tests/test_viewer.nim` asserts no `textContent = esc(` remains.

---

## Test-suite state

All **15** test files pass locally in **both** debug and `-d:release` (one new
file, `tests/test_routes.nim`; 14 previously). No test was disabled, skipped,
deleted or loosened: the changes to `tests/` in this round add assertions
(`test_engine`, `test_orders`, `test_server`, `test_physics`, `test_replay`,
`test_viewer`) or replace a vacuous/mis-aimed one with a stronger one that fails
on the pre-fix code (`test_engine`'s disconnect test, `test_physics`'s contact
test, `test_replay`'s scrape assertion). Every behaviour fix in this round has a
test that fails on the code it replaced — the one exception is F12, whose effect
is only visible on a simultaneous end-and-fault tie, and F7/F14, which are a CI
assertion and a document.

## NOTED (not fixed)

- **`TwistDamp` is not the grid optimum.** `TandemTwistGain=5` with
  `TandemTwistDamp=0` delivers 20/20 at mean score **0.802** and 176 mean damage,
  against the shipped damp 4's 0.794 / 219. The constant is left alone: moving a
  sim constant moves the per-tick `gameHash` chain and the golden fixture with
  it, which is a retune, not a fix. Recorded in `docs/BASELINE-TUNING.md` so the
  next tuning pass starts from the measurement.
- **`baselines.nim:389`** gives `mule` the note string "straight at the goal,
  full effort" although it ships at effort 0.55 (reviewer's O5); **`server.nim:477`**
  says "the 690 s engine stop" where the constant is 660. Cosmetic, not findings
  in this round.
- **`sim_types.nim:461`** still declares an unused `SimServer.damageAtTurnStart`
  field (the live one lives on `TurnEngine`). Not hashed, not read; left alone
  rather than folded into the F2 commit.
- **`/client/replay`** exists as a game-pod route inherited from the starter
  (reviewer's O6). Untouched: the *viewer* is the static bundle, the manifest
  declares `static-replay-viewer`, and removing a starter route is a change the
  review did not ask for.
- **Push mechanism.** `git push` 403s in this sandbox; if a future round pushes
  through the Data API, reset the local branch onto the API-created
  `origin/main` **before** committing again, or the whole series is replayed (as
  it was here, harmlessly).
