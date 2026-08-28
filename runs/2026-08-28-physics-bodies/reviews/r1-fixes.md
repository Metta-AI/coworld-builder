# r1 fixes — physics-bodies

Head: `52379767a323c604171f76353a94eb2fb0399816` (`main`)
CI: https://github.com/Metta-AI/cogame-physics-bodies/actions/runs/33177512252 — **success**
(jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; run id `33177512252`, head sha
`52379767`). The previous head `89432702` (run `33176949006`) was **failure** in `wasm-viewer`
only — my own N16 comment inside an emcc command string; fixed forward in `5237976` and green on
the pushed head. `test` and `docker-smoke` were already green on `89432702`.

Range reviewed: `f6976bc` .. `5237976`. 20 fix commits, one per finding (two for N1, three for
N17 including a flake fix, two for N16 including the CI fix-forward).

> **History note, disclosed rather than rewritten.** `git push` over HTTPS does not work in this
> sandbox, so commits were replayed through the GitHub Git Data API. The second push run
> (carrying only the `config.nims` fix) was given the REMOTE base sha, and the script computes
> `BASE..HEAD` over LOCAL history — so it re-created all 19 earlier commits a second time
> (`e91d2d6` .. `3ebd10e`, same messages, walking the same content changes onto an already-final
> tree). `git log --oneline f6976bc..main` therefore shows each finding twice. **The tree is
> correct and verified**: `git diff HEAD origin/main` is empty, i.e. the pushed tree is
> byte-identical to the locally tested tree, and CI is green on it. I did not force-push or
> rewrite pushed history. The authoritative one-commit-per-finding chain is `d46d479` ..
> `8943270`; the shas cited below are from that chain.

| finding | disposition | commit | files |
|---|---|---|---|
| N1 | fixed (2 commits) | `d46d479`, `315e63a` | `tools/ci/renderer_fixture.html`, `client/replay_broadcast.html:2787-2802,2975`, `.github/workflows/ci.yml`, `tests/test_text_bounds.nim`, `src/bodies/global.nim:72-79` |
| N2 | fixed | `14e6998` | `src/bodies/sim.nim:501-522`, `sim_state.nim:20-29`, `sim_types.nim:312`, `server.nim:643-660`, `tests/test_engine.nim`, `tests/test_replay.nim`, `tests/helpers.nim` |
| N3 | fixed (docs) — note drift, code correct | `20e7c75` | `docs/ORDERS.md:75-95`, `coworld_manifest_template.json` |
| N4 | **note drift, code correct** — no change | — | `src/bodies/control.nim:20-22`, `tools/ci/baseline_tuning.json`, `tests/test_tuning.nim:22-32` |
| N5 | fixed (docs) | `ee536ae` | `docs/RULES.md:150-153`, `coworld_manifest_template.json` |
| N6 | documented, physics unchanged | `3f89463` | `src/bodies/sim.nim:349-362` |
| N7 | documented, counter unchanged | `eb149ce` | `src/bodies/sim.nim:389-396`, `docs/PROTOCOL.md:147-152` |
| N8 | fixed | `2d90ef0` | `src/bodies/sim.nim:195-212,242`, `sim_types.nim:63-66`, `ring.nim:3,116-119`, `docs/RULES.md:155-159` |
| N9 | fixed (both bounds tightened); (b) partly **DISPUTED** with measurements | `c729c34` | `tests/test_control.nim:128-136,166-211,330-341` |
| N10 | fixed | `ce7675c` | `tests/test_replay.nim:50-70` |
| N11 | **as-is, deliberate** + pointer added | `39bfa08` | `tests/test_manifest.nim:1-14` |
| N12 | fixed | `3e4ecbb` | `src/bodies/server.nim:601-616,628,824,913`, `tests/helpers.nim`, `tests/test_replay.nim` |
| N13 | fixed | `15eeede` | `src/bodies/replays.nim:81-86,396-412`, `tests/test_replay.nim` |
| N14 | fixed | `a268e5a` | `src/bodies/global.nim:77-81,1095-1125`, `tests/test_text_bounds.nim` |
| N15 | **as-is, deliberate** + documented + test pin | `dbdd413` | `client/replay_broadcast.html:3007-3020`, `tests/test_viewer.nim:93-101` |
| N16 (a) | **DISPUTED** — nothing under `replay-viewer/dist` is tracked | — | `.gitignore:39` |
| N16 (b) | documented | `0422b97` (+ `5237976` fix-forward) | `replay-viewer/config.nims:42-52` |
| N17 (a) | note drift, code correct | — | `src/bodies/baselines.nim:230-259` |
| N17 (b) | fixed | `1920221` (+ `3ebd10e` flake fix) | `src/bodies/decide.nim:10-14,174-188`, `tests/test_engine.nim` |
| N17 (c) | note drift, code correct | — | `src/bodies/ring.nim:53-62`, `tests/test_ring.nim:27` |
| N17 (d) | note drift, code correct | — | `client/broadcast_core.js:49,268` |
| N17 (e) | documented | `869fe4d` | `src/bodies/sim.nim:529-537` |
| CND-1 | **settled** | `315e63a` | `tests/test_text_bounds.nim` |
| CND-2 | narrowed, still needs a hosted episode | `1920221` | `src/bodies/decide.nim:174-188` |
| CND-3 | unchanged — phase 60 evidence | — | — |

---

## N1 — both `--strict-text-bounds` gates measured zero drawn strings (checklist item 15)

**What the code did.** Worse than the review found. The fixture spliced its wasm shim into
`<head>`, but the built `index.html` loads `static_replay.js` from the **body** (the
`BROADCAST_CORE` splice, `Dockerfile.replay-viewer:39-42`), and that file assigns
`window.BodiesStaticReplay = {createCore}` unconditionally — so the real core overwrote the shim,
the page ran with no replay URL, and **all three iframes died on
`data-replay-error: "Missing required replay URL"`** while the parent set `data-replay-loaded`
anyway (it called `done()` straight after `doc.write`). No full-cap text ever reached the page.
Reproduced locally in headless chromium against a marker-substituted `index.html`: `status:
"Replay failed: Missing required replay URL"`, `feedRows: 0` in every width. That also explains
the `{"loaded":true,"ms":325,...,"feed_lines":0}` line in run `33168835069`.

**What it does now.**

1. `d46d479` — the shim **replaces** `<script src="./static_replay.js"></script>` (and fails loudly
   if that tag is absent), so the page boots on the fixture core with no Worker and no wasm and the
   full-cap `say`/`note` run through the page's own chrome. `beats`/`lead`/`lulls` now ride the
   first frame only, as `replay_runtime.nim`'s `sendLead` ships them — repeating them every frame
   re-pushed their feed rows at 16 Hz and evicted the intent rows (MAX_FEED is 4).
   The fixture then **measures**: for every element carrying a full-cap string, at 360/620/1280 px,
   the box must be non-empty, inside every scroll box it sits in, and not ellipsised, using the
   harness's own `never_inside` semantics (a row slides in from off-frame, so being outside on one
   poll is normal; never once inside is the defect). `data-replay-loaded` is set **only** after
   that passes; otherwise `data-replay-error` names the width, the element and the box, which
   fails the step.
   The measurement immediately found a real defect, fixed in the same commit: the page renders
   `say || note`, so a seat that says nothing puts its **160-rune note** into a
   `white-space: nowrap; max-width: none` feed row — measured at **x = −53 px, off the left edge**
   of a 360 px frame, and past `#killfeed`'s own box at 620 and 1280 px. The game block now marks
   its commander rows `pb-intent` and gives them a wrapping band bounded by the feed's width
   (widen the band, never shorten the sentence). The starter's CSS above the banner is untouched;
   `chrome_common.js` is still byte-identical.
2. `315e63a` — `tests/test_text_bounds.nim` measures the **board** half, which no browser check can
   ever see: `grep -c fillText` over `client/*.js`, `client/*.html` and `replay-viewer/*.js` is
   **0 in every file**, so `canvas_text.total` is structurally 0 and the board's speech band is
   pixie-rasterised in Nim and blitted as sprite pixels. The test bakes the band through the real
   frame builders (seat stream at 1x, spectator at the supersampled scale) with a full-cap `say` on
   **both** seats, installed the way the server installs one (`boundedIntentRecord` →
   `pushFeedIntent`), then reads the pixels back out of the wire packet and asserts: the baked text
   is still `MaxSayRunes` long, the 160-rune note never reaches the board, the plate is exactly the
   reserved band at that scale, the whole plate is inside the board viewport at the reserved band
   top, the plate carries ink, and no ink reaches the padding edge the raster clips against. Both
   the widest possible cap string (48 `W`) and a prose one are measured.

**Evidence (CI run `33177512252`).**
- `test` job: `seat stream/wide k=1: plate (40, 20) 880x120 on 1920x1280, ink x 8..862 y 11..93
  (10219 px)` and `spectator/wide k=2: plate (80, 40) 1760x240 on 3840x2560, ink x 17..1724
  y 22..187` — the worst case fits the 8..872 / 4..116 text box. `test_text_bounds: ok` twice
  (debug + release).
- `wasm-viewer` job, fixture step, from `renderer-fixture/viewer-smoke.json`:
  `renderer fixture: three widths booted and MEASURED: say=48 runes, note=160 runes, both seats at
  once; 6 full-cap boxes, every one wholly inside its frame [w1280:note span.badge @ 787,292 97x34;
  w1280:say @ 785,309 97x15; w360:note @ 276,265 74x26; w360:say @ 277,278 74x12; w620:note @
  454,292 97x34; w620:say @ 455,309 97x15]`, `loaded: true`, no `data-replay-error`.
- `--strict-text-bounds` is kept on **both** steps. Its `canvas_text` is still 0 and now
  documented in `ci.yml` for what it is — this game draws no canvas text at all — with the two
  checks that do cover the two real text surfaces named in the same comment.

**Checklist item 15:** the substance is now verified from the tree and from cited CI evidence — the
worst-case string is measured on the real drawing surface (Nim, board) and in the real page (DOM,
three widths), and a regression in either is red.

## N2 — one missing seat left the sim in `Lobby` for the whole 660 s budget

**What the code did.** Exactly as traced: `forceStart` only set `sim.lobbyTicks =
config.startWaitTicks`, already passed, and `startRound()` is reachable only through
`lobbyIsStarting()` = `phase == Lobby and players.len >= minPlayers` with `minPlayers` 2
everywhere. One seat present ⇒ the predicate is false forever ⇒ `deadline/wall_clock`,
`rounds: 0`, `scores: [0.000, 0.000]`.

**What it does now (`14e6998`).** The force-start moved into `step`'s `Lobby` branch: when
`lobbyJoinTimedOut()` fires, the lowest missing slot is latched in `sim.lobbyNoShowSeat` and
`lobbyIsStarting()` admits it. The derivation uses only `lobbyTicks` and the recorded joins, both
of which playback reproduces, so the browser re-derives the same start tick — a server-side
force-start could not have been re-derived at all. It is a **latch**, not a predicate, because the
round starts on the very tick the budget expires: the server's next iteration sees
`phase == Playing`, so reading `lobbyJoinTimedOut()` there would have skipped
`declarePlayerFailure` entirely. The dead force-start block and the `forceStart` var are gone.

**Evidence.** `tests/test_engine.nim` now runs the **real server loop** in process with one seat
connected (§Tests 7's missing case) and asserts the `COGAME_PLAYER_FAILURE_URI` artifact names
policy index **1** and the pusher baseline, that results were written with `reason: complete` and
`rounds >= 1`, and that the loud log line survives. CI `test` log:
`t47: lobby budget expired with seat 1 missing; starting the match anyway` →
`physics-bodies: seat 1 never registered; driving BUG-1 with pusher` →
`episode over — complete/full_time ... at tick 96`. `tests/test_replay.nim` records a one-seat
episode and **re-derives every hash** (this is what pins the force-start as replay-safe), asserting
the round starts at the lobby budget (`gameStartTick == lobbyJoinTimeoutTicks - 1`) and that both
bugs were driven. `tests/helpers.nim` gained `seatsJoined` so a partial lobby can be recorded.
`test_engine.nim` now ends `quit(0)` for the same reason `test_server.nim` does (the in-process
game server leaves mummy/curly/pixie allocations shared across threads; the module teardown
segfaults on a green run — observed).

**Checklist:** item 5 stays true and item 7's "plays full episodes legally" now also holds for the
one-seat case; the design's §End conditions is satisfied rather than contradicted.

## N3 — the rim guard's two extra terms

Code kept: the velocity look-ahead (`stopping = radial² / 8 000`) and the in-band thrust floor
(`e = max(e, 3·w/100)`) are load-bearing — without the look-ahead a `high`-posture bug crosses the
last 0.6 m before the guard can turn it, and without the floor a `retreat` at aggression 2 has no
thrust to arrest a drift. The guard's own §Tests 4 claim is unreachable without them (see N9's
measurements). `20e7c75` documents both in `docs/ORDERS.md` — the page a prompt author reads —
including that the `aggression: 10` halving halves the braking too. Manifest regenerated in the
same commit (it inlines the page). **Note drift:** the design note's §The controller step 3 formula
omits both terms.

## N4 — two shipped `BaselineParams` differ from the note — note drift, code correct, no change

`RimGuardUmDefault = 600_000`, `ChargeLeadTicksDefault = 4`, `LiftEngageUmDefault = 620_000` equal
`tools/ci/baseline_tuning.json`'s recorded `pick` (verified: `{'rimGuardUm': 600000,
'chargeLeadTicks': 4, 'liftEngageUm': 620000}`), `tests/test_tuning.nim` pins that equality, and
the design note explicitly authorises the sweep to move exactly these three numbers. No in-repo doc
carries the note's stale values (`grep -rn 'chargeLeadTicks\|liftEngageUm\|rimGuardUm' --include=*.md`
finds only AGENTS.md's list of which three are tunable). Nothing to fix.

## N5 — the snap-to-rest step

`ee536ae` adds it to `docs/RULES.md`'s step 5. The step cannot be dropped: integer friction
(`v -= (v·FricNum) div 1024`) stops changing `v` once `v·FricNum < 1024`, so without the floor every
coast keeps a few µm/tick forever and `test_control.nim`'s "brace brakes to |v| = 0" is unreachable.
Hashed, applied identically on both sides.

## N6 — the contact torque's Q12 scaling

Not changed, deliberately: `delta` is clamped to ±450 and the shipped expression already saturates
that clamp for any contact with a perpendicular component above ~1 800 µm/tick at a torso-edge
lever arm, so the two readings differ only for contacts too weak to spin anything — and the
expression is hashed, so moving it invalidates every recorded replay and costs a GameVersion bump
for no behavioural gain. `3f89463` states at the call site which reading is in force and why, so the
next reader does not "fix" it. Determinism gate + golden hashes re-run green.

## N7 — `contacts` on both bodies

Hashed and reported, identical on record and playback, so the definition is documented rather than
changed: `contacts` counts **contact ticks a body took part in** — a two-sided impulse counts on
both bugs and a touch with no closing speed and no shove counts on neither. `eb149ce` says so at
the increment and in `docs/PROTOCOL.md`, where a reader of `results.contacts` looks.

## N8 — 25 disc pairs, and the dead branch

`2d90ef0`: the count is corrected in all five places that said "ten" (`ring.nim`'s module doc, the
`DiscPair` doc, `discPairs`, `resolveContacts`, `docs/RULES.md` step 6), with the real range (1 pair
when both bugs are prone, 25 when both are upright with eight feet on clay), and the array size is
now the derived `DiscPairCount`. The dead `if … : discard` branch is removed — `resolveContacts`'
own check is the real filter. `test_determinism` (including the golden fixture), `test_physics` and
`test_ring` green, which is the proof the branch was dead.

## N9 — two bounds weaker than §Tests 4 (checklist item 1: tightened, never loosened)

`c729c34`, both measured locally with a 10 000-rollout probe before changing anything:

**(a) brace → |v| = 0.** The old comment's arithmetic (197 ticks from friction alone) is wrong: a
brace also *drives* — its goal bearing is the other bug — so its own thrust works against the
residual velocity. **Measured stop: tick 121**, one tick outside the design note's 120. The bound
went from `<= 240` to `<= 132` (the measurement plus ~9 %).

**(b) "from any legal state".** Zeroing the inherited velocity stays, and this is the part I
**dispute** as a design claim: measured, **671 of 10 000** rollouts cross the rim if `randomBody`'s
random velocity is kept, and **25 still cross** with the outward component projected out — moving
tangentially at radius r puts a bug at `sqrt(r² + v²) > r`, which no controller can undo. What is
achievable is now also asserted, in a new block: 10 000 rollouts from any legal state in the
**inner half** of the ring, keeping the full ±2.9 m/s velocity, any stance, aggression ≤ 9 — **0
crossings**.

## N10 — `complete/match_won` re-derivation

`ce7675c` adds a dedicated block: `roundsToClinch = 1`, which can only end `complete/match_won`,
re-derived hash by hash through the same path the wasm viewer runs. The existing blocks are
unchanged (the first still accepts either rule, by design).

## N11 — the CLI manifest validation — as-is, deliberate

Left in `coworld-release.yml`'s "Validate the manifest template with the CLI" step, which **is** a
CI step and is the last one before "Upload the Coworld" — what §Packaging asks for. It cannot run
in the Nim suite: the `test` job installs Nim and nothing else, has no `uv`/`uvx` and no `coworld`
package, so a call from `test_manifest.nim` would find no CLI and degrade to a no-op that reports
success, and pulling a pinned Python package in would make every test run depend on a network
fetch. `39bfa08` records that at the top of the suite so the §Tests 12 item is findable rather than
apparently absent. Everything else on that list is asserted from the JSON (item 10 unaffected).

## N12 — `round` records at the final tick

`3e4ecbb`: one `flushRoundRecords` template, called after every hashed step and after the
wall-clock stop's extra tick, with a final call in the artifact block so a round banked by a step
that then faulted still gets exactly one record. `tests/helpers.nim` does the same (it is the
server's path in miniature) and `tests/test_replay.nim` asserts the stamps are strictly ascending
and that the first is not the episode's last tick. Observed on a 5-round episode: records at
**11541, 20583, 35166, 45750, 53916 ms** of a 53916 ms episode, instead of five at 53916 ms.
Re-derivation is unaffected — `applyReplayEvents` still refuses to re-apply a `round` record.

## N13 — the lull map was always empty

`15eeede`: the lull scan and the scrubber timeline now read one `BeatKinds` list (knockdown,
ring_out, round_end, match_point, round_start, gameover) — §Record and event vocabulary's
definition. The old collector took anything outside `["contact","shove","rim_slip"]`, which let
`turn_end` in every 36 ticks against a 341-tick minimum gap, so no span could ever qualify.
Observed after the fix: cert fixture `[[630, 882], [1016, 1314]]`, default match `[[579, 795]]`;
`tests/test_replay.nim` asserts at least one span, every span clearing `MinLullTicks`, inside the
playable range, with `LullLeadTicks` of context around every beat. Visible in CI too: the
`wasm-viewer` soak readout now shows the fast-forward chip — `0:11 ▸▸ ROUND CLOCK …`, tick
`0 / 1604` → `488 / 1604` — i.e. skip-lulls is doing something in the hosted bundle for the first
time.

## N14 — bubble dwell

`a268e5a`: `bubbleLines` drops a record older than `BubbleHoldTicks` (60 ticks = 2.5 s at
TargetFps), taking the record's tick from its turn boundary (the server pushes at
`tickCount mod turnTicks == 0`), so the dwell is identical on record, on playback and after a seek.
Feed text is never hashed. `tests/test_text_bounds.nim` asserts both directions and that the
reserved band does not move when the line expires.

## N15 — the round/ring caption — as-is, deliberate

Kept in `#pb-ring`, with the reason now written at the code: overwriting `#clock-caption` costs the
caption that says what the timer is, and the inherited `renderClock` rewrites that caption on lobby
and game-over frames, so the round/ring string would flicker against it. Both readouts are on
screen (CI: `ROUND CLOCK ROUND 2 OF 4 · RING 3.00 M`) and `#pb-ring` is inside `#scorebug`, so no
transport rule is touched. `dbdd413` also pins both readouts in `tests/test_viewer.nim` so neither
can quietly disappear.

## N16 — (a) DISPUTED, (b) documented

**(a) DISPUTED.** Nothing under `replay-viewer/dist` is tracked:
`git ls-tree -r HEAD --name-only | grep -c replay-viewer/dist` = **0**,
`git log --name-only c573490 | grep -c nimcache` = **0**, `.gitignore:39` is `replay-viewer/dist/`
and `git check-ignore -v replay-viewer/dist/nimcache/foo.c` confirms it. The 83 nimcache files are
untracked local build residue in a working tree that has run the emscripten build —
`git status --porcelain --ignored` lists the directory as `!!`. Nothing to remove.

**(b)** `0422b97` documents the `--preload-file client/art` flag (necessary: `global.nim:447` opens
`client/art/walls/wall_v.jpg` while baking the board plate, and under emscripten that path must
exist in MEMFS). **That commit broke CI and `5237976` fixes it forward:** `switch("passL", …)` takes
one string whose newlines become spaces, so the `#` comment lines I put *inside* it were handed to
emcc and swallowed the flags after them — `EXPORTED_FUNCTIONS` among them, so the page died with
`data-replay-error: Module._malloc is not a function` (run `33176949006`, `wasm-viewer`). The
comment now sits above the `switch` and says why nothing inside the string may be a comment; the
emitted command line is byte-identical to `f6976bc`'s again, and `wasm-viewer` is green on
`5237976`.

## N17 — the five smaller drifts

- **(a)** `pusher`'s five `say` strings vs the note's "four": note drift, code correct, no
  behavioural consequence, nothing in-repo claims four.
- **(b) fixed (`1920221`).** The per-turn budget was a pre-check only, so an attempt starting a
  millisecond inside it got its whole deadline and a turn's worst case was
  `turnSpacingMs + attempt1Ms + retryMs` (~20 s) instead of `turnBudgetMs`. Each attempt's deadline
  is now `max(1000, min(configured, budget − spent))`; the floor is curl's whole-second
  `CURLOPT_TIMEOUT` granularity, so that is the most a turn can overshoot by. The new test sets both
  attempt deadlines *larger* than the budget against a provider that never answers: with the clamp
  the turn returns in ~4 s against a 4 000 ms budget, and with the clamp reverted the same test
  reports `ran 6001 ms against a 4000 ms budget` (verified by stashing only `decide.nim`).
  The plain `os.sleep` rate floor is left as it is — bounded by `turnSpacingMs` (≤ 6 s).
- **(c)** the ring reaching 1.992 m: note drift. `radius_at_round_end_m` is `ringRadiusAt(cfg,
  roundTicks)` — the radius *at the round clock*, which is what the field name says and what
  `tests/test_ring.nim:27` pins; the last stepped tick is 395 at 1.996 m. No in-repo doc claims
  otherwise.
- **(d)** `broadcast_core.js` differing in two lines: note drift. The second line is a comment path
  (`src/ctf/sim.nim` → `src/bodies/sim.nim`) that *must* change — the ctf path does not exist in
  this repo — so the note's "exactly the `BODIES_WIRE` identifier" is the stale half. Code correct.
- **(e)** documented (`869fe4d`): step 3's leg reach reads the previous tick's posture while step 5's
  thrust uses the new one. That is the literal reading of "step 3 before steps 4–5" and it is
  hashed, so the comment now says so.
- **flake fixed forward (`3ebd10e`).** `1920221` exposed a latent race in `test_engine`'s fake
  provider: a handler that a hung-provider block walked away from appended its in-flight window
  whenever it woke up, landing in a later block's freshly cleared list (`a throttled turn issued 3
  requests`, once in two full local suite runs). The handler now stamps the epoch it started under
  and records only while that epoch is current; every block bumps the epoch where it already cleared
  the list. No assertion changed.

---

## Could not determine

- **CND-1 — whether a full-cap 48-rune `say` renders inside the reserved plate: SETTLED.**
  `tests/test_text_bounds.nim` measures the real bake. Worst case (48 `W`), 1x:
  `plate (40, 20) 880x120 on 1920x1280, ink x 8..862 y 11..93` inside the 8..872 / 4..116 text box;
  at the supersampled scale `ink x 17..1724 y 22..187` of 1760x240. Printed in the CI `test` log.
- **CND-2 — whether a live LLM episode stays inside the 660 s stop: narrowed, not settled.** The
  per-turn worst case is now `turnBudgetMs` + curl's 1 s granularity instead of ~20 s (N17b), so
  §Decisions' arithmetic holds against the code. Still needs a hosted episode; `docker_smoke.sh`
  runs with no `ANTHROPIC_API_KEY` and every CI turn falls back instantly. Phase 60's
  `replay_summary.py` check remains the settling evidence.
- **CND-3 — whether `results.reason == "complete"` on the platform for a two-champion match:
  unchanged.** Every green path in CI is all-scripted; phase 60 settles it.

## NOTED (not fixed)

- `pbFrame` re-ingests `s.beats` on **every** frame and `pbEvent` pushes an un-deduped feed row for
  `knockdown`, `round_end` and `round_start`. Harmless in production because the server ships
  `beats` on exactly one frame (`replay_runtime.nim` `sendLead`), which is why the fixture now does
  the same — but a future frame that repeats the timeline would spam the 4-row feed. Not a finding
  in this round.
- `tests/test_text_bounds.nim` is a 17th suite, one more than the design note's §Tests list names.
  It runs automatically (`NIM_TESTS` is unset; only `NIM_TESTS_RELEASE_ONLY` is set), and both
  modes are green in run `33177512252`.
