# r1 review — pistonball

Range: `db98eef..ce20047` (whole repo history; `ce20047d66736a61bc772c52e05ffb82b38ccedf` = `main`)
Repo: `/workspace/cogame-pistonball` · Starter mount: `/workspace/starters/coworld-ctf`
Files read: 58 (all of `src/`, `tests/`, `replay-viewer/*.nim|*.js|config.nims`, `client/*`,
`tools/`, `.github/workflows/*`, `coworld_manifest_template.json`, `docs/RULES.md`,
`docs/SCRIPTS.md`, `AGENTS.md`) + starter diffs + CI logs for run 32923038675.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
one-parallel-batch rule).

Method note: everything below marked **observed** was read in the file at the cited line;
**inferred** means I reasoned from what I read; **CI** means it comes from the logs of run
32923038675 (jobs 98040246962 / 98040247110 / 98040721047), which I fetched with `gh`.

---

## Blocking

**None.** I could not falsify any of checklist items 1–15 or the one-parallel-batch rule from
the tree or from the CI logs of the reviewed sha. Every item I could reach is recorded under
"Traced and consistent" with the evidence I used. The thirteen findings below are code↔note
disagreements and coverage gaps; none of them maps cleanly to a named checklist item, with two
exceptions whose tension with the checklist's wording I spell out in place rather than resolve:
N10 (item 15's "loads the real `client/renderer.js`") and N13 (item 3's "no `/client/replay`
pod path anywhere").

---

## Non-blocking

### N1 — `docs/RULES.md`, which is inlined verbatim into the shipped manifest, still documents the pre-deviation physics
- Where: `docs/RULES.md:76`, `:79-81`, `:85`, `:106`, `:112` vs
  `src/pistonball/sim_types.nim:27-36`, `:67`, `:92-95`, `src/pistonball/bank.nim:104`,
  `src/pistonball/sim.nim:71`; the same text is
  `coworld_manifest_template.json` → `game.docs.pages[0].content.value`
- Observed: the builder made three deliberate deviations from the note and documented each of
  them in code and in the commit body of `8978f91`:
  - `SubSteps* = 16` with a nine-line rationale (`sim_types.nim:27-36`) and
    `GravityPerSubstep* = 1_064` rescaled for 384 Hz (`sim_types.nim:67`);
  - the containment guard widened to `GuardMinY = 200_000` / `GuardMaxY = 4_300_000` with a
    rationale (`sim_types.nim:85-95`) — the note's step 4.5 says `y ∈ [400_000, 4_000_000]`
    (`design.md:250-252`);
  - a **third** seeded draw, `startOffsetUm = 20_000 + 10_000·rand(18)`
    (`bank.nim:104`, rationale `bank.nim:84-91`), applied at `sim.nim:71`
    (`result.ballX = BallStartX - draws.startOffsetUm`) — the note says the ball is placed at
    `(BallStartX, BallStartY)` and that "these two draws plus `perm` are the only random
    numbers the sim ever takes" (`design.md:186-190`).

  `docs/RULES.md` — the player-facing rules page — was not updated with any of them. It still
  states `GravityPerSubstep = 4 257 … at 96 substeps/s` (`:76`), "the ball is placed at
  (BallStartX, BallStartY) … Those two draws plus perm are the only random numbers"
  (`:79-81`), "Each tick integrates 4 substeps of 1/96 s" (`:85`), "Four substeps of 1/96 s"
  (`:106`) and the guard box `y in [400 000, 4 000 000]` (`:112`). I confirmed by parsing the
  manifest that `game.docs.pages[0].content.value` contains the strings `"4 substeps"`,
  `"4 257"` and `"400 000], y in"`, i.e. the stale numbers ship to the platform.
- Note says: §The game steps 1–8 and the constants table (`design.md:169-254`); the note's own
  numbers are the ones RULES.md still carries, so RULES.md is consistent with the note and
  inconsistent with the code it documents.
- Not blocking because: no checklist item covers doc accuracy; item 10 constrains the *shape*
  of `game.docs`, which is correct (N-see "Traced").
- Counter-evidence in the code's favour: the replay's own config JSON reports the true value
  (`bank.nim:141` `"substeps": $SubSteps`), and `AGENTS.md` §1 documents the third draw.

### N2 — three per-substep constants were not rescaled when `SubSteps` went 4 → 16
- Where: `src/pistonball/sim.nim:323` (angle), `:307-308` with
  `sim_types.nim:82-83` (torque), `:305-306`/`:309` with `sim_types.nim:76-79` (drags)
- Observed: the 4→16 change rescaled some per-substep quantities and not others.
  - Rescaled: gravity `4_257 → 1_064` (`sim_types.nim:67`); the force→velocity denominator,
    which multiplies by `SubSteps` (`sim.nim:298-299`); the pose translation
    `pos += v div SubSteps` (`sim.nim:321-322`).
  - Not rescaled: the angle integration is hard-coded `sim.angleQ = (angleQ + spin div 4 …)`
    (`sim.nim:323`) and runs 16 times per tick; `TorqueScale/TorqueDen = 28_294/100_000`
    (`sim_types.nim:82-83`, docstring "mN*m -> 1/16 brad per tick per substep") is applied 16
    times per tick; `AirDragNum/Den = 8/4096` and `SpinDragNum/Den = 12/4096`
    (`sim_types.nim:76-79`) are applied 16 times per tick.
- Note says: step 4.4 `angleQ = (angleQ + spin div 4 + 4096) mod 4096` **per substep at 4
  substeps** — i.e. the angle advances by exactly `spin` per tick — and step 4.3 gives the same
  torque and drag expressions per substep at 1/96 s (`design.md:243-249`).
- Consequence (inferred, arithmetic): per tick the drawn angle now advances by `≈4·spin`
  rather than `spin`; the torque→spin gain is 4× the note's (equivalent to an effective inertia
  of 120 rather than the `BallInertia = 480` that `tests/test_physics.nim:26-30` asserts is
  `½mR²`); per-tick air and spin drag lose ≈4× as much (`(1−8/4096)^16 = 0.969` vs the note's
  `(1−8/4096)^4 = 0.992`).
- Why this is not caught: `angleQ` feeds only the rendered ball highlight
  (`global.nim:495`) and the hash (`sim_state.nim:32`), never the dynamics — I grepped every
  use. The rolling test (`tests/test_physics.nim:76-80`) asserts the *relation*
  `spin ≈ −vx·652/R` that friction drives the contact to, not the gain that gets it there, so a
  4× torque gain passes it.
- Not blocking because: no checklist item pins the physics constants; determinism (item 2)
  is unaffected — both builds run the same code.

### N3 — the seeded drop offset moves the score floor below the note's "exactly −18.000"
- Where: `src/pistonball/sim.nim:71`, `src/pistonball/bank.nim:104`,
  `src/pistonball/sim_types.nim:93`, `src/pistonball/sim.nim:445-447`
- Observed: the episode starts the ball at `BallStartX − startOffsetUm` (2–20 cm left of
  8 400 000 µm) while the containment guard still clamps `x ≤ GuardMaxX = BallStartX`. Progress
  is the telescoping sum `progressMilli += 1000·100·(prevX − x) div TravelDistance`
  (`sim.nim:446`), so a ball that drifts back to the right wall ends right of where it started
  and `progressMilli` goes negative by up to `200_000·100_000 / 7_200_000 ≈ 2 778` milli
  (−2.778 points), putting the floor at ≈ −20.78 rather than −18.000.
- Note says: "the ball can never end right of where it started, because the containment clamp
  of step 4.5 is `x ≤ BallStartX` … so `progress ≥ 0` always and the worst case is … −18.000"
  and "Range: score ∈ [−18.000, +100.000)" (`design.md:306-310`).
- Why the tests don't see it: `tests/test_scoring.nim:8-14, 94-97` computes the floor
  analytically from `BallStartX` rather than from a played episode, so the offset never enters.
- Not blocking because: no checklist item bounds the score; `results_schema` puts no range on
  `sharedScore`/`progress` (verified in the manifest).

### N4 — the release workflow's certify step does not pass `--timeout-seconds 300`
- Where: `.github/workflows/coworld-release.yml:167-175`
- Observed: the step runs
  `uvx --from "$COWORLD_PKG" coworld certify dist/coworld_manifest.json --no-open-report`
  with no timeout flag. (`--timeout-seconds 900` at `:311` belongs to the *upload-coworld*
  step, not certify.)
- Note says: "Because 35 s is close to `coworld certify`'s 60 s default, the release
  workflow's certify step passes **`--timeout-seconds 300`** (cooperative-hunting 0.1.2 →
  0.1.3); the fixture is **not** shrunk" (`design.md:1284-1286`).
- Relevance (inferred): the fixture is now longer than the note assumed — see N5 — so the
  margin the note was worried about is smaller, not larger. CI cannot show this: the certify
  step only runs in `coworld-release.yml`, which has not run on this sha.

### N5 — the certification fixture and the bundled `player[]` list differ from the note
- Where: `coworld_manifest_template.json` → `player[0..1]`, `certification.players`
- Observed: two bundled player entries (`baseline` → `PLAYER_SCRIPTED=wavebot`, `metronome` →
  `PLAYER_SCRIPTED=metronome`), and `certification.players` is **1 × baseline + 19 ×
  metronome** (counted with `json`), not twenty baselines.
- Note says: `player[0]` is "the only top-level bundled player entry" and "occupies **all
  twenty** certification slots"; `certification.players` = "twenty `{"player_id":"baseline"}`
  entries" (`design.md:1256-1263, 1274-1277`).
- Why the deviation exists: commit `844697a` records it — twenty wavebots deliver in ~120
  ticks, so the fixture replay was 194 ticks / 8 s and the viewer smoke's 12 s soak read it as
  frozen. The metronome-heavy fixture runs the full 900 ticks.
- Checked consequences: both declared ids occupy ≥ 1 cert slot (raid 0.1.2→0.1.3 scar) —
  asserted at `tests/test_manifest.nim:30-38`; all four seat-count invariants still read 20
  (`tests/test_manifest.nim:15-28`); CI's docker-smoke log shows `seats=20`,
  `all 20 player containers exited 0`, `reason=complete`, and no `SEAT-COUNT FAIL` anywhere.
  Not blocking; recorded only because the note says otherwise.

### N6 — the certification fixture's `seed: 4417231` is the sentinel the entrypoint refuses to honour
- Where: `src/pistonball.nim:7-23, 60-69` vs `coworld_manifest_template.json` →
  `certification.game_config.seed`
- Observed: `LegacyFixedSeed = 4417231` and `seedPinned()` returns true only when the config
  carries a seed **other than** that value; otherwise the entrypoint injects a fresh
  `randomSeed()` and strips the config's seed (`stripUnpinnedSeed`). The cert fixture's seed
  is exactly 4417231, so certification and `docker_smoke.sh` episodes run on a random seed and
  are not reproducible run-to-run.
- Note says: the fixture pins `"seed": 4417231` (`design.md:1277`); test 14 wants "the seed …
  honoured when pinned" (`design.md:1440-1441`), which `tests/test_startup.nim:164-174`
  exercises with 20260825 — a value that is not the sentinel, so the collision is untested.
- Rationale for the sentinel is documented at `src/pistonball.nim:8-11` (a public fixed seed
  would make `perm` pre-computable). The finding is the collision with the fixture value, not
  the randomisation.

### N7 — `game.protocols.player` and `game.protocols.global` are the same 5147-character string
- Where: `coworld_manifest_template.json` → `game.protocols`
- Observed: `protocols.player.value == protocols.global.value` (byte-equal; both are
  `docs/PROTOCOL.md`, which is also `game.docs.pages[1].content.value`). Both are objects of
  `{"type":"text","value":…}`.
- Note says: `player` describes the registration frame, the window-filtered per-tick frames,
  that seats send no inputs and the script schema; `global` describes the `/global` snapshot,
  the state JSON and the static replay bundle (`design.md:1245-1249`).
- Checklist item 10 is satisfied (both keys present, both the right shape) —
  `tests/test_manifest.nim:119-123` asserts exactly that and nothing about the two differing.
  The single document does cover both sockets, so the content is not wrong, only undivided.

### N8 — the shipped system prompt inverts the note's `wave`/`catch` wording (and is the one that matches the controller)
- Where: `src/pistonball/llm.nim:228-236` vs `design.md:520-527`
- Observed: the note's prompt says wave lifts when the ball is "at-or-right-of me" and catch
  fires when it is "at-or-right-of me"; the code says "at-or-**LEFT**-of me (I am BEHIND it …)"
  for both. The controller implements `dxp <= 0 → up_m` (`control.nim:65` and `:75`), i.e.
  ball at-or-left of my centre, which agrees with the code's prompt, with the note's own
  controller table (`design.md:602, 607`), with the note's phase rule (`design.md:268`,
  "UP when `centreX_i ≥ ballX`") and with `docs/SCRIPTS.md:28-36`. The note's prompt block is
  the internally inconsistent one.
- Nothing in the repo records this as a deviation; a reader diffing the note's prompt against
  `llm.nim` sees an unexplained change. Everything else in the prompt is verbatim (I compared
  line by line), including "Reply with a single JSON object … MUST begin with '{'".

### N9 — several assertions the note's §Tests names are absent or assert something weaker
Each sub-item is code-to-note only; no checklist item requires any of them.
- a. **No fake LLM client anywhere.** `tests/test_engine.nim` runs the credential-less client
  (`:22-25` deletes the env vars, `:31` asserts `client.disabled`). So the note's test 7
  claims — "all twenty seats' calls go out in one parallel batch (the fake records in-flight
  windows; the test asserts all twenty intersect)", "consecutive batches are ≥
  `minBatchSpacingMs` apart", "the per-turn budget is enforced with a hung client"
  (`design.md:1376-1379`) — are not asserted at all. The behaviour is present in the code
  (`decide.nim:391-405` one `RequestBatch` per attempt; `:369-373` the floor; `:383-388` the
  budget), but nothing tests it.
- b. **Retry/throttle untested.** The note's test 6 wants "a timeout on attempt 1 ⇒ exactly one
  retry; a `throttled` client ⇒ **zero** retries" (`design.md:1373-1375`).
  `tests/test_scripts.nim` has no retry or throttle case; the code paths are `decide.nim:380`
  (`attempt < 2`) and `:437-443` (break on `throttled`).
- c. **"One-unit change".** `tests/test_determinism.nim:38-40` mutates a byte by **±40** and
  checks the chain diverges from that tick, where the note (`design.md:1337`) says "a one-unit
  change in any command byte changes the final hash".
- d. **A tautological ripple check.** `tests/test_control.nim:100-107` builds
  `float(piston)/float(PistonCount)` and asserts it increases — it never calls
  `rippleHeight`, so the note's "its per-column phase offset is monotone in `i`"
  (`design.md:1355-1356`) is not exercised. (The periodicity half, `:96-98`, is real.)
- e. **No sha256 pin on the chrome.** `tests/test_viewer.nim:18-24` asserts
  `chrome_common.js` identity with `len > 30_000`, two marker substrings and
  `"pistonball" notin chrome`, where the note says "byte-identical to the starter's copy
  (sha256 pinned)" (`design.md:1427-1428`); "differs in **exactly** the `PISTONBALL_WIRE`
  identifier" is likewise two substring tests (`:92-94`). I verified both properties hold
  against the starter mount by `diff` — see "Traced and consistent" — so the properties are
  true; only the guard against future drift is weaker than the note describes.
- f. **Resting penetration.** `tests/test_physics.nim:44-46` asserts
  `0 ≤ penetration < 5 000 µm`, where the note pins "between 200 and 600 µm"
  (`design.md:1327-1328`) and `sim_types.nim:34-35` claims the design pins "a 392 um resting
  penetration". The note's "friction never reverses the slide direction within one substep"
  has no assertion in the file.
- g. `tests/test_replay.nim:92-117` does not assert "at least one `handoff` and one `launch`"
  (`design.md:1404-1405`); everything else in test 10 is there.
- h. `tests/test_server.nim` covers the socket contract by unit-testing the parsers and
  grepping `server.nim` for route names (`:107-119`). The note's test 11 items "/global
  snapshot → ticks → game over", "an input mask from a player ignored", "`/healthz` and
  `/global` still answer 15 s after the artifacts are written" and "artifact writes to
  `file://` URIs" (`design.md:1406-1413`) are not exercised against a running server.
  (docker-smoke covers the artifact writes end-to-end in a container.)

### N10 — the "renderer fixture" does not load this repo's renderer, and the bundle run's `canvas_text.total` is 0
- Where: `tools/ci/renderer_fixture.html:85-177`, `.github/workflows/ci.yml:335-350`,
  `src/pistonball/global.nim:369-397, 698-732`; CI job 98040721047
- Observed: pistonball has no `client/renderer.js` — the board is drawn by
  `src/pistonball/global.nim` compiled to wasm and blitted as sprite objects. The fixture
  therefore re-implements the arena and the reserved band in page JS with
  `system-ui, sans-serif` (`:142`, `:146`, `:157`) and draws its own strings; it does
  self-check that they are full-cap first (`:182-187`, 48 runes / 160 runes, ending on a
  4-byte codepoint) and it is driven by `viewer_smoke.mjs --strict-text-bounds` in its own step.
- CI evidence: the bundle run reports `canvas text: 0 drawn, 0 never inside` — total 0, which
  the checklist itself says "means the check covered nothing … and is not evidence of
  anything". The fixture run reports `canvas text: 66 drawn, 0 never inside … 0 ellipsized`.
  So the only non-zero `canvas_text` in CI comes from the fixture's own drawing code, not from
  `bakeBubble`.
- Note says: the fixture "loads the real renderer with a full-cap 48-rune `say` and 160-rune
  `note` on all twenty seats at once, at 360, 620 and 1280 px, self-checks its own string
  lengths" (`design.md:1464-1469`) — which the fixture does except for "the real renderer".
- Checklist tension, stated rather than resolved: item 15 requires "a page that loads the real
  `client/renderer.js`", and its gate sentence is "a repo that draws model text and has no such
  fixture is a blocking `legibility` finding". This repo *has* a fixture, full-cap,
  multi-size, self-checking, `--strict-text-bounds`-gated in its own step. The literal clause
  is unsatisfiable here (there is no JS renderer to load). I read that as satisfying the item;
  a stricter reading is available to the judge, and what would settle it is a fixture that
  drives the wasm module's own `bakeBubble` path.
- Related, bounded by construction (inferred): `bakeBubble` sizes the plate
  `width = min(MapWidth-40, max(60, ceil(textWidth)+26))` (`global.nim:380-382`) and pixie
  clips at the image edge, so a `say` whose rendered advance exceeds ~1134 px at font size 20
  would clip silently; at `MaxSayRunes = 48` that needs >23 px per glyph, which
  `data/font.ttf` at size 20 will not reach. I could not measure the font in the sandbox.
- Band arithmetic: `BubbleBandTop = 19`, `BubbleBandBottom = 106` board rows
  (`global.nim:32-33`, = `Y ∈ [3.55, 4.25] m`), slot `y = 19 + slot·29` (`:730`) and plate
  height 34 (`:383`), so slot 2 occupies rows 77…111 — four rows below the stated band bottom,
  still 489 rows above the frame edge. Reserved-band requirement (item 15's second bullet) is
  met; the stated bottom is 4 cm optimistic.

### N11 — the perf test (and the first determinism test) measure ~120 ticks, not 1800
- Where: `tests/test_perf.nim:9-16`, `tests/helpers.nim:42-53`,
  `tests/test_determinism.nim:23-28`; CI job 98040246962
- Observed: `runScripted` stops at `phase == GameOver`, and twenty wavebots deliver in about
  120 ticks (commit `844697a` measured it; CI's baseline test prints `wavebot: 20/20
  delivered, mean 97.053`). So `tests/test_perf.nim` echoes "1800-tick episode + 36000
  controller evaluations" while timing roughly 120 ticks — the CI log line is
  `1800-tick episode + 36000 controller evaluations: 0 ms`, which is the tell.
  `tests/test_determinism.nim:23-28` ("over a full 1800-tick run" per `design.md:1336-1338`)
  is likewise a ~120-tick chain.
- Mitigation already in the tree: the golden fixture test deliberately uses `metronome`
  precisely so it runs the full episode (`tests/test_determinism.nim:50-54`), and
  `tests/data/golden_hashes.json` pins `ticks: 1800` with 36 samples — so the note's full-length
  determinism pin does exist, in test (c) rather than test (a).

### N12 — small residue (cosmetic; each observed, none load-bearing)
- `src/pistonball/bank.nim:70-72`: the docstring says "The episode's only **two** random draws"
  and then lists three bullets (`perm`, `restHeights`, `startOffsetUm`).
- `src/pistonball/sim.nim:436`: the section comment still reads `--- 4. four substeps ---`
  while the loop below runs `SubSteps` = 16 (`:441`).
- `src/pistonball/control.nim:25`: `RippleColumnTicks* = 24` is declared and never referenced
  anywhere in `src/`, `tests/` or `tools/` (grepped).
- `client/replay_broadcast.html:4420` and `:4452` declare `var head` twice in
  `pbRenderEndcard`; legal JS, the element use completes before the string assignment, and the
  declaration re-initialises on every call.
- The identifier sweep substituted "pistonball" into inherited comments that describe features
  this game does not have: `client/replay_broadcast.html:975` "pistonball markers", `:1312`
  "pistonball marker", `:2129` "pistonball comet tracers", `:2143`, `:2516`, `:2689`, `:2785`.
  These sit in the starter's `#fpv` code, which is retained behind null guards and never runs.
- `game.protocols`/`docs` duplication aside, `replay-viewer/config.nims` adds one line the note
  does not mention: `--preload-file {rootDir/"client"/"art"}@client/art` (`config.nims:47`),
  needed for the wall/locker art the wasm renderer bakes. Everything else in that file is the
  starter's, renamed (diffed).

### N13 — `/client/replay` is still served by the game pod (starter behaviour, note-mandated)
- Where: `src/pistonball/server.nim:201-216`; `ReplayClientRoute = "/client/replay"` and
  `CoworldReplayClientRoute = "/clients/replay"` (`~/.nimby/pkgs/bitworld/src/bitworld/client.nim:21,26`)
- Observed: the HTTP handler answers `/client/replay`, `/clients/replay`, `/client/global`,
  `/client/player`, `/clients/…` and `/client/league` with the embedded broadcast page. No
  manifest key points the platform at any of them; `game.replay_viewer` is
  `{"bundle": "static-replay-viewer"}` and the static bundle fetches only its `?replay=` URL
  (`replay-viewer/static_replay_worker.js:113-121`).
- Checklist item 3 says "No `/client/replay` pod path anywhere", read literally; the design
  note requires these routes ("**both `/client/` routes serve real pages** … the certifier
  probes them before starting player pods", `design.md:780-783`) and they are the starter's own
  route table, unmodified. I record the tension rather than resolving it: what settles it is
  whether item 3 means "the manifest must not declare a pod replay viewer" (satisfied) or
  "the binary must not serve that route" (not satisfied, and not satisfiable while keeping the
  starter's certifier-probe contract).

---

## Traced and consistent

**Resolution rules (§The game steps 1–8)**
- `src/pistonball/server.nim:586-621` — turn boundary keyed on the *turn index changing*, not
  `elapsed mod turnTicks == 0`, with the reason recorded at `:591-595` (the phase flips inside
  a step, so the modulo test would skip turn 0). Scripts installed, one `script` chat record
  per seat written (`:613-615`), `llmTurns`/`fallbackTurns` incremented by source (`:608-612`),
  `say` parked for 60 ticks = 2.5 s (`:620`). `activeScript` never enters the hash — I checked
  every `mixHash` call in `sim_state.nim:25-42`.
- `server.nim:622-635` — the controller is compiled in **piston index order** `0..19`
  (`for piston in 0 ..< PistonCount`), written into a seat-indexed array through
  `seatOfPiston`, exactly as `design.md:213-221` requires; the byte is handed to
  `writeInputMaskChange`, which drops it unless it differs from `lastMasks[seat]`
  (`replays.nim:113-119`), and `lastMasks` is seeded to 127 for every seat
  (`server.nim:375-377`).
- `sim.nim:424-434` — kinematics: `h := clamp(h + u, 0, Stroke)` then
  `pistonVel = h − h_prev` (the *achieved* velocity), pistons kinematic. Matches step 3.
- `sim.nim:200-236` — contact order ceiling → left wall → right wall → broadphase heads
  ascending. There is **no floor surface**, documented at `:204-207` and, unlike the other
  deviations, correctly carried into `docs/RULES.md:106-109`.
- `sim.nim:238-344` — substep body in the note's order: gravity, contacts
  (`Fn = 150·δ + 28·max(0,−v_n)` clamped ≥0 and ≤60 000 000; Coulomb `614/1024` with a
  `150·|v_t|` viscous cap; `τ += (t_x·r_y − t_y·r_x) div 1e6`), semi-implicit Euler, drag,
  clamps `|v| ≤ 250_000` / `|spin| ≤ 300`, pose, containment guard. Every product is computed
  in `int64` and narrowed with `div`, as `AGENTS.md` requires.
- `GuardEpsilonUm = 50_000` (`sim.nim:19-23`) — a guard correction under 5 cm does not count
  toward `guardClamps`, with the reason (a bank that never moves the ball would otherwise end
  `fault` instead of scoring −18). Not in the note; documented in code.
- Progress/phase accounting `sim.nim:444-476` matches steps 5 and 6 exactly: telescoping
  `progressMilli`, `penaltyMilli += config.stepPenaltyMilli` (default 10, `sim_config.nim:43`),
  `bestX`, `stallCount` re-arming every `StallTicks = 240`, one `bounce_back` per improvement
  window (`lastBounceBackBest` latch, `:458-462`), `EngagedHalfWidth = 1_200_000`,
  in-phase at `≥ 800_000` up / `≤ 600_000` down, `touches` on contact rising edge.
- Hash (`sim_state.nim:18-42`) mixes tick, phase, ball pose+motion, all 20 heights, all 20
  achieved velocities, `bestX`, both accumulators, `guardClamps`, `permDigest` — the note's
  step 7 list, in that order, and nothing presentational.
- End checks `sim.nim:496-505`: delivered → `complete/delivered`; `maxTicks` →
  `complete/out_of_time`; `checkInvariants` raising `SimGuardError`, caught at
  `server.nim:639-648` → `fault/sim_fault` (and any other exception → `fault/host_error`),
  with the partial replay still closed and the `result` record written (`:745-746`). The
  wall-clock stop is applied before the step at `server.nim:444-451` → `deadline/wall_clock`.
- Scoring: `roster.nim:51-117` emits one shared score copied into twenty slots, built from
  integer text (`pointsText`) so the twenty values are textually identical;
  `tests/test_scoring.nim:51-61` asserts that.

**Decision path**
- Server-side, in the game pod (`decide.nim`, `llm.nim`); the player binary only registers
  (`src/pistonball_player.nim:110-124`).
- Credential ladder `llm.nim:98-131`: Bedrock (endpoint or token) → `ANTHROPIC_API_KEY` →
  `ANTHROPIC_API_KEY_URI` via `readCogameUri` → `disabled = true` and the exact phrase phase 60
  greps (`:130-131`). Single haiku candidate `us.anthropic.claude-haiku-4-5-20251001-v1:0`
  (`:71-82`); `max_tokens` from config (default 900, `sim_config.nim:37`); no `temperature`;
  `output_config.effort` suppressed for haiku (`:151-154`); Bedrock body carries
  `anthropic_version: bedrock-2023-05-31` (`:145`).
- **ONE parallel batch per turn**: `decide.nim:391-399` fills a single `RequestBatch` with every
  open seat and `:404-405` issues `client.curl.makeRequests(batch, …)` once. There is no
  per-seat request call anywhere in the tree (grepped for `makeRequest`/`post` outside this
  block). Satisfies the checklist's simultaneous-decision rule.
- Deadlines: `attempt1Ms = 12000`, `retryMs = 6000`, `turnBudgetMs = 20000`,
  `minBatchSpacingMs = 45000` (`sim_config.nim:24-27`), validated with
  `attempt1 + retry ≤ turnBudget` and both ≥ 1000 ms because curl's timeout granularity is
  whole seconds (`sim_config.nim:100-107`; `tests/test_engine.nim:70-79`).
- Retry once: the loop is `while open.len > 0 and attempt < 2` (`:380`); `throttled` is cleared
  per turn (`:330`) and breaks before the retry batch (`:437-443`); the retry adds an explicit
  "reply with ONLY the JSON object" suffix (`:394-396`).
- Tolerant parse: `extractJsonObject` (balanced scan, then first-`{`…last-`}`,
  `scripts.nim:138-177`), `parsePistonScript` repairs every field to the note's default table
  (`:258-288`), percentages and centimetres accepted (`:203-233`), unknown `mode` → last turn's
  → `wave`, unknown `blind` → `hold`; `ScriptError` only when no usable field exists
  (`:269-275`) — which is what the retry and the fallback exist for.
- Fallback recorded: `fallbackRecord` with `cause ∈ {timeout, transport_error, throttled,
  parse_error, no_credentials, budget_guard}` (`decide.nim:269-279, 348-359, 422-434,
  446-458`), written into the replay chat stream at `server.nim:600-601`, and counted into
  `results.fallbackTurns` (`server.nim:610-611`, `roster.nim:89-90`).

**Every wait and its bound**
| Wait | Where | Bound |
|---|---|---|
| Lobby / seat join | `sim.nim:393-413`, `sim_state.nim:85-92` | `lobbyJoinTimeoutTicks` 1800 ticks ≈ 75 s at the 24 Hz frame limiter; the match starts anyway and the missing piston plays `wavebot` |
| No-show declaration | `server.nim:563-573` | once, best-effort, `declarePlayerFailure` wrapped in try/except (`:262-273`) |
| Inter-batch floor | `decide.nim:369-373` | `sleep(min(spacing, spacing − since))` ≤ 45 s, and **skipped entirely when no seat needs a call** (`open.len > 0` guard) — which is what makes the budget guard effective |
| Attempt 1 batch | `decide.nim:389-405` | `attempt1Ms div 1000` s handed to curl |
| Retry batch | same | `retryMs div 1000` s |
| Per-turn outer | `decide.nim:324-325, 383-388` | monotonic `turnBudgetMs`, checked before each attempt; worst case 12 + 6 = 18 s < 20 s |
| Budget guard | `decide.nim:333-342` | `elapsed + 2·(turnBudget + spacing) > wallClockBudget` → LLM off for the rest of the run, `budget_guard` record; with the defaults it fires by t = 530 s, so no batch can start later than that and the last one ends ≈ 595 s |
| Engine hard stop | `server.nim:444-451` | `wallClockBudgetSeconds` 660 → `deadline/wall_clock` |
| Frame limiter | `server.nim:316-335` | `sleep(1..2 ms)` per pass, bounded by the frame duration |
| Game-over hold | `sim.nim:414-418`, `gameOverTicks` 72 | 3 s |
| Shutdown grace | `server.nim:770-776` | fixed 20 s of `sleep(200)`, then `httpServer.close()` + `joinThread` |
| Player dial / receive | `src/pistonball_player.nim:26-31, 75-91, 110-139` | 240 × 500 ms first dial; ≤ 6 reconnects × 6 dials; receive loop exits on the socket raising, `quit(0)` |
| Viewer seek / scan | `replays.nim:34-37, 379-431, 473-487` | `SeekTicksPerFrame = 240`, scan 96 ticks per frame |
The note's arithmetic (`design.md:457-469`) reproduces: 7 × 45 s + 20 s + lobby + write ≈ 376 s
expected, worst case ≈ 455 s, both inside 660 s and inside 720 s (60 % of 1200).
`tests/test_engine.nim:81-90` asserts the same sum and `wallClockBudgetSeconds ≤ 720`;
`tests/test_manifest.nim:144-152` asserts it per variant.

**String truncation (rune boundaries)**
`truncateRunes` is the single cut (`scripts.nim:69-76`, `runeLen`/`runeSubStr`).
`note` ≤ 160 (`sanitizeNote`, strip *then* cut, with the reason for the order at `:82-86`),
`say` ≤ 48 (`sanitizeSay`, cut then filter controls/braces), `register.policy` ≤ 48
(`decide.nim:264`), `fallback.detail` ≤ 200 (`decide.nim:278`, and at the source in
`llm.nim:175, 184, 192, 201`), the serialized `script` record ≤ 700 runes by shrinking the
`note` and never the JSON (`scripts.nim:343-359`), `register.prompt` ≤ 4000 runes **at the
transport** (`server.nim:523`) and never written to the replay (`registerRecord` has no prompt
field; `tests/test_server.nim:43-50` asserts `"prompt" notin record`). The 4-byte-emoji-on-the-
boundary case is `tests/test_scripts.nim:63-77`, which also round-trips the record through
`parseJson` and asserts `validateUtf8() == -1`. Checklist item 9 satisfied.

**Replay writer**
`PistonballReplayMagic = "COWLDPST"`, format version 1, `GameName`/`GameVersion` in the spec
(`replays.nim:38-49`); resolved config JSON with seed, `perm`, `restHeightsUm`, the whole
geometry/physics table and the **real** player names (`sim_config.nim:205-256`,
`bank.nim:107-141`); per-tick command-byte change records with the starter's press/release
wrapper deleted and the reason recorded (`replays.nim:100-119`); one `gameHash` per tick
(`server.nim:649`); chat records `register` / `script` / `fallback` / `budget_guard` / `result`
(`decide.nim:253-291`, `server.nim:600-615, 745`). Control records are re-applied at playback
into non-hashed fields only, keyed on a leading `{` (`replays.nim:247-266`).
`tests/test_replay.nim:53-117` writes an episode through the same writer and re-simulates it to
every recorded hash with `mismatchQuit = true`.

**Viewer re-derivation**
`replay-viewer/pistonball_replay.nim:3` imports the same `pistonball/sim`; `stepReplay` calls
`checkReplayHash` after **every** tick (`replays.nim:308-313, 274-306`), surfacing
`mismatchTick`. `static_replay.js:161` sets `data-replay-loaded="true"` on the Worker's
`loaded` message, which the Worker posts after `ingestPacket()` of the first rendered packet
(`static_replay_worker.js:126-131`); `showFailure` sets `data-replay-error`
(`static_replay.js:14-20`) and `data-replay-mismatch-tick` (`:32`). `config.nims` carries **no**
`MODULARIZE` and no `EXPORT_NAME` (grepped), and the Worker bootstrap is the matching
non-modularized `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts`
(`static_replay_worker.js:8, 188-191, 239`). Both files are the starter's with only the
`ctf_*`→`pistonball_*` and Worker-name renames (diffed line by line against the mount).
CI: `{"loaded":true,"ms":575,…}`, soak `"4 / 898" → "245 / 898" → "293 / 898"`, no
`data-replay-error`, no mismatch — job 98040721047.

**Chrome provenance**
- `diff /workspace/starters/coworld-ctf/client/chrome_common.js …/client/chrome_common.js` →
  identical; sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` on both.
- `client/broadcast_core.js`: one hunk, line 49, `CTF_WIRE` → `PISTONBALL_WIRE`. Nothing else.
- `client/replay_broadcast.html`: 4522 lines vs the starter's 4660. Everything above the
  `PISTONBALL additions…` banner (`:4018`) is the starter's; the diff of `head -4017` against
  the starter is exactly: the `#povBadge`/`#fpv`/`#viewpanel` CSS and markup removals
  (one 311-line CSS block and one 43-line markup block), the matching null guards
  (`:2009-2010`, `:2032`, `:2197`, `:2950`, `:2994`, `:3009`, `:3623`, `:3844-3872`, `:3918`),
  the `PB_MODE` latch now keying on `s.pb` (`:1682`), the `ctf-replay`/`ctf-shell` postMessage
  ids becoming `coworld-replay`/`coworld-shell` (`:1579`, `:1658`), the `CtfStaticReplay` →
  `PistonballStaticReplay` and `PaintballChrome` → `PistonballChrome` renames, the two
  removed sprite-preload loops that would have been guaranteed 404s (`:1325-1337`, `:1446-1451`),
  and comment renames. Sections 1–5 (stage, scorebug, banner lane, kill feed, transport,
  scrubber + momentum + beats + lulls + spoilers, endcard, locker room) are present and
  unmodified.
- Removed ids are exactly the note's list — `tests/test_viewer.nim:51-60` enumerates all
  nineteen and I confirmed `id="…"` is absent for each.
- Transport rules: `relayout()` (`:3950-3993`) measures `#transport`/`#scorebug` and sets
  `--hudscale`, `--topband`, `--band` on `document.documentElement` (`:3985, 3990-3991`);
  `#endcard { … bottom: var(--band, 0px) }` (`:737-748`); the endcard is taken down on every
  frame whose phase is not `gameover` (`:1732`), which is what a seek produces; the game
  block's overlays live inside the plates and `#plates-r`, none of them fixed-positioned in the
  band (`:4089-4142`). Beats are `<button class="beat-marker <kind>">` with `aria-label`,
  `title` and a click that sends `s:<tick>` (`:4249-4270`), placed both from live events and
  from the up-front `s.beats` timeline (`:4488-4510`), and CSS exists for every kind the sim
  emits — `launch`, `bounce_back`, `stall`, `delivered`, `over` (plus `gameover`) at
  `:4158-4163`. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow:hidden;
  text-overflow:ellipsis }` at `:4043-4048`; `#stage.tiny` rules at `:4189-4192`; the starter's
  `stage.classList.toggle('tiny', boardW <= 620)` kept (`:3987`). Checklist items 11 and 14
  satisfied.

**Manifest**
`num_agents: 20` in variant `default`, variant `sprint` and `certification.game_config`;
`certification.players` = 20; `certification.game_config.players` = 20 and `slots` = 20
(parsed). `results_schema` has exactly the 25 keys `playerResultsJson` emits, with
`additionalProperties: false` and every per-seat array `minItems: 20, maxItems: 20`
(`tests/test_manifest.nim:40-63` asserts the set equality against a real episode). Every
`config_schema` array (`tokens` 1..20, `players` 1..20, `slots` 0..20) carries min/max.
`game.docs.readme` + three pages (`rules.md`, `protocol.md`, `scripts.md`), all non-empty text
of the right shape. `game.protocols` has both `player` and `global` as `{"type":"text",…}`
(see N7 for their content). `game.replay_viewer.bundle == "static-replay-viewer"`; no top-level
`version`, no `game.display_name`; `game.owner: daveey`; secret namespace
`secret://coworld/pistonball/anthropic_api_key` == `game.name`; compose service `pistonball`
and image `coworld-pistonball:latest` agree with `{{PISTONBALL_IMAGE}}`. Checklist items 6 and
10 satisfied.

**Tests present** — all fifteen files the note names exist, and CI ran every one of them in
**both** debug and release except `test_perf.nim`/`test_baselines.nim`, which ran release-only
(job 98040246962 log: 15 debug invocations, 17 release invocations). Item 1's "no test
loosened" is verifiable from the repo: `git log --stat -- tests/` shows a single commit
(`8978f91`), 1848 insertions, 0 deletions — nothing weakened during this run.

**Scaffold**
`ci.yml`: `test` (debug+release), `docker-smoke` with `SMOKE_SEATS: "20"` and
`SMOKE_REQUIRE_REPLAY_JSON: "0"` (`:183-191`), `wasm-viewer` with `needs: docker-smoke`
(`:218`) executing `viewer_smoke.mjs --timeout 90 --soak 12 --strict-text-bounds` (`:320-325`)
plus the renderer-fixture step (`:335-350`). `tools/ci/viewer_smoke.mjs` is byte-identical to
`coworld-builder/templates/tools/ci/viewer_smoke.mjs` (diffed). `docker_smoke.sh` enforces all
four seat invariants before any container starts (`:110-151`, every message prefixed
`SEAT-COUNT FAIL:`), asserts the game's exit code (`:239-245`) **and** each of the twenty
players' (`:254-273`, log: `all 20 player containers exited 0`), and copies the replay out for
the viewer job (`:333-343`). No `SEAT-COUNT FAIL` anywhere in the docker-smoke log; end reason
`complete`; replay 54 880 B. `coworld-release.yml` order: build manifest (`:153`) → certify
(`:167`) → **upload-policies** (`:206`) → upload-coworld (`:304`) → secret put (`:342`).
`tools/ci/policies.json` has four policies, two `PLAYER_PROMPT` champions (`pistonball-swell`,
`pistonball-cascade` with `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` at `:13`) and
two `PLAYER_SCRIPTED` fillers; both prompt bodies match the note's champion text word for word.
`tools/build_replay_viewer.sh` and `tools/ci/docker_smoke.sh` are mode 100755 in the index
(`git ls-files -s`), and the build script differs from the starter's in exactly two lines
(image tag, `docker cp` path). The checklist's placeholder gate exits 0; the only
angle-bracket names left are the four documented runtime ones (`<cow_id>`/`<sha>` in
`ci.yml:208`, `<run_id>` in `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN`
in `coworld-submit.yml:31`). Checklist items 3, 12, 13 satisfied.

**Both name spaces** — agents see `PST-nn` only: `windowView` composes aliases and piston
indices and no names (`decide.nim:206-247`), the per-seat sprite frame is filtered by the same
`inWindow`/`windowColumns` predicate (`global.nim:584-612`), and
`tests/test_locality.nim:74-83` and `tests/test_server.nim:70-95` assert no real name reaches
either. The viewer maps aliases to real names in `roster` (`broadcast.nim:136-155`), the
endcard (`replay_broadcast.html:4449-4472`), each bank cell's `title` (`:4394-4397`) and
`results.names` (`roster.nim:74`). Checklist item 4 satisfied.

**Baseline legality and tuning** — `tests/test_baselines.nim:14-29` validates 500 random states
× both baselines against `validScript` plus the rune caps and the command range;
`:37-63` is the tuning pin (≥18/20 delivered, mean > 60, metronome < wavebot, mix ≥ 12/20) and
CI printed `wavebot: 20/20 delivered, mean 97.053 · metronome: mean -10.067 · 10/10 mix: 20/20`.
The three tunables are a `BaselineParams` object swept by `tools/tune_baselines.nim`, recorded
in `tools/ci/baseline_tuning.json` and re-asserted by `tests/test_tuning.nim:8-14`.
An all-scripted episode reaching `complete`/`delivered` is asserted at
`tests/test_scoring.nim:63-71` and `tests/test_physics.nim:114-117`. Checklist item 7 satisfied.

---

## Could not determine

- **Whether `canvas_text` can ever be non-zero for the shipped board renderer.** The bundle
  run reports `total: 0` (CI), consistent with the board being wasm-baked sprites blitted into
  an OffscreenCanvas, but I cannot rule out a code path in `chrome_common.js` that would draw
  2D text under other data. What would settle it: a `viewer-smoke.json` from a replay carrying
  LLM `say`/`note` strings (i.e. a run with `ANTHROPIC_API_KEY` set), or a fixture that drives
  `global.nim`'s own `bakeBubble` through the wasm module.
- **Whether a full-cap 48-rune `say` fits `bakeBubble`'s plate in `data/font.ttf` at size 20.**
  The width formula bounds it at `MapWidth − 40 = 1160 px` and pixie clips at the image edge;
  48 runes would need >23 px per glyph to overflow, which I judge impossible for this face but
  could not measure without Nim/pixie in the sandbox.
- **Whether `coworld certify`'s default timeout is enough for the current fixture** (N4). The
  fixture now runs 900 ticks with 20 containers; the note's 35 s estimate predates the
  metronome-heavy fixture. Settled by one `coworld-release.yml` run, which has not happened on
  this sha.
- **`NIM_TESTS_RELEASE_ONLY`'s value** is a repo variable, not in the tree; I read its effect
  from the CI log (only `test_perf` and `test_baselines` ran release-only), which is the note's
  intent.
- **Whether the note's `ready` post to the embed shell exists.** `design.md:1030-1032` says the
  `coworld-replay` bridge fires `ready` after `data-replay-loaded`; the page posts `boot`
  (`replay_broadcast.html:1647`) and `frame` (`:1700`) and no `ready` — and so does the
  starter's page (same lines, only the `src` id renamed). So this is inherited, not introduced
  here; what would settle whether it matters is the embed shell's own contract, which is not in
  either repo.
