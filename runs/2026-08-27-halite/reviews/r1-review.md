# r1 review — 2026-08-27-halite (`Metta-AI/cogame-halite`)

Repo read at `main` = `f403fa0e99ba4637fb2af2bcab5de61bf30cd776` (clone at `/tmp/review-halite`).
Design note: `runs/2026-08-27-halite/design.md`, byte-identical (sha256
`6ee0585e…6a28d`) to the in-repo `docs/plans/2026-08-27-halite-design.md`.
Starters read: `/workspace/starters/cogame-moba`, `/workspace/starters/coworld-ctf`.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Files read: ~55 in-repo + 5 starter files + the published
`kaggle_environments-1.32.7-py3-none-any.whl`.
Evidence beyond static reading: CI run **33133144503** (`success`, head sha
`f403fa0e…`, jobs `test`/`docker-smoke`/`wasm-viewer` all `success`), its full log and
its `viewer-smoke` artifact; two executed differential experiments against a real
`kaggle-environments==1.32.7` install (F1) and one against the shipped engine (F2).

Labels used below: **observed** = I read or executed it; **inferred** = I reasoned from
observed code; **untested** = would need a run to settle.

---

## F1 — The elimination transcription clears an eliminated seat's shipyards; upstream keeps them (executed both sides)

- Where: `server/cogame_halite/sim.py:294-303` (esp. `:301`
  `self.players[seat] = [bank, {}, {}]`) vs
  `vendor/upstream/kaggle_environments/envs/halite/halite.py:195-202`.
- Observed (code): upstream's `interpreter()` sets `agent.status = "DONE"` for a seat with
  no ships and (no shipyard or `halite < spawnCost`), and only line 201-202
  (`if agent.status != "ACTIVE" and agent.status != "DONE": obs.players[index] = [0, {}, {}]`)
  clears assets — i.e. a **DONE** agent keeps its shipyards in `obs.players`. `sim.py:301`
  clears them unconditionally.
- Observed (executed): with the real wheel installed
  (`/tmp/kev`, `kaggle-environments==1.32.7`), seat 0 = `[499, {"y0": 320}, {}]`:
  - upstream after the elimination step: `statuses ['DONE','ACTIVE','ACTIVE','ACTIVE']`,
    `players[0] = [499, {'y0': 320}, {}]` — the yard survives, and on the next step an enemy
    ship stepping onto index 320 is **destroyed** (`players[1] = [5000, {}, {}]`) and the
    yard razed.
  - this port, same state: `eliminated [1,None,None,None]`, `players[0] = [499, {}, {}]`,
    and the enemy ship stepping onto 320 **survives** (`{'b': [320, 37.0]}`).
- Note says: §The game step 9 (design.md:240-243) — "its remaining assets are cleared" — so
  the **code matches the note's prose**. But the same note frames step 9 as a transcription
  of `interpreter()` (design.md:192-197, 240), `AGENTS.md` rule 1 and `docs/PORTING.md`'s
  inherited rule are "never fix an upstream quirk", and `vendor/PATCHES.md:64-72` states the
  elimination block's constants come from upstream and that
  `tests/test_fidelity.py` "covers both transcriptions end to end".
- Also observed: the fidelity gate **cannot** see this. `tests/fidelity_stream.py:9-13`
  states the stream is built so "no seat can be eliminated", and
  `tests/test_fidelity.py:207-218` asserts exactly that
  (`sim.eliminated == [None]*4` for all 8 gate seeds). `tests/test_sim.py:337-347` asserts
  the clearing with a seat whose bank is 0, which cannot distinguish the two behaviours.
- Consequence (inferred): after any elimination that leaves an unfunded shipyard, the board
  the surviving seats play on differs from upstream's — a razing hazard and a
  mining-suppressing cell vanish. Scoring is unaffected (bank is kept, `results.scores` uses
  the same formula).

## F2 — The wire `observe` frame has no `step` and no `remainingOverageTime`; `Board(obs, config)` raises `KeyError('step')`

- Where: `server/cogame_halite/engine.py:114-135` (frame construction) vs
  `server/cogame_halite/sim.py:215-227` (`_observation_dict`, which *does* carry both keys)
  and `vendor/upstream/kaggle_environments/helpers.py:287-294`
  (`Observation.step` → `self["step"]`, `remaining_overage_time` → `self["remainingOverageTime"]`,
  both read by `Board.__init__`, `envs/halite/helpers.py:420-421`).
- Observed (executed): the frame keys are
  `['alias','aliases','board','budget','config','deadlineMs','directive','eliminated','halite','maxTurns','player','players','seat','turn','type']`;
  `Board(frame, cfg.upstream_configuration())` → `KeyError: 'step'`. The same call on
  `sim.observation(2)` (which has `step` + `remainingOverageTime`) builds a `Board` fine.
- Note says: design.md:686-689 and the normative `docs/PROTOCOL.md:70-72` —
  "**`halite`, `players`, `player` and the turn index are Kaggle's `observation` object, key
  for key** … so a Kaggle bot's `Board(obs, config)` works unchanged"; design.md:1118-1119
  (Out of scope) — "`remainingOverageTime` … the field **is present in the observation** for
  shape compatibility and is always the config default".
- Note that the note's own example frame (design.md:674-683) also uses `"turn":137` and omits
  `remainingOverageTime`, so the *shape* the code emits matches the note's example while
  contradicting the two prose claims about it.

## F3 — The 660 s hard stop starts after the lobby, so the note's 720 s pin is not bounded by it

- Where: `server/cogame_halite/engine.py:94` (`self.started_at = clock()` in `Engine.__init__`),
  `server/cogame_halite/server.py:281-284` (lobby `wait_for`, `player_connect_timeout_seconds`
  = 120 s by default), `server.py:307-317` (the Engine is constructed **after** the lobby),
  `server.py:494` (`await asyncio.sleep(SHUTDOWN_GRACE_SECONDS)` = 20 s after artifacts),
  `server/cogame_halite/uris.py:29-31` (artifact writes: 3 attempts × 30 s timeout + backoff).
- Observed: `engine.elapsed` (engine.py:104-106) is measured from Engine construction. The
  budget guard (`engine.py:199-203`, 600 s) and the hard stop (`engine.py:401-410`, 660 s) are
  therefore both relative to the post-lobby instant; the lobby, the artifact writes and the
  20 s grace all sit outside them.
- Arithmetic (inferred, untested): worst case = 120 s lobby + ≤660 s engine + up to ~2×91 s of
  bounded artifact retries + 20 s grace ≈ 800-980 s of container time; with the guard doing its
  job (episode ends shortly after 600 s + at most one 18 s directive batch) the realistic worst
  is ≈120 + 618 + 5 = **743 s**, i.e. just over the note's 720 s = 60 % pin.
- Note says: design.md:78 ("Typical 195 s, worst modelled 537 s, budget guard at 600 s, hard
  stop at 660 s = **55 %**") and design.md:370-377, whose table models the lobby at **20 s**
  (its declared *bound* elsewhere, design.md:325, is 120 s) and "Results + replay write ≤ 5 s".
  Every individual wait **is** explicitly bounded (see Traced §waits); the gap is between the
  bounds and the 720 s total, not an unbounded wait.

## F4 — `docker_smoke.sh` does not assert `reason == "complete"` or the results key set; `ci.yml` does

- Where: `tools/ci/docker_smoke.sh:299-325` — it checks `names`/`scores` lengths (and only
  *warns* if absent), then **prints** `episode end reason: …` without comparing it; there is no
  expected-key set in the script. The assertions live in `.github/workflows/ci.yml:106-123`,
  which imports `RESULTS_KEYS` from the code and fails on `doc["reason"] != "complete"`.
- Note says: design.md:1089-1095 (§Tests 14) — the smoke script asserts
  "`reason == "complete"`, the exact results key set…"; design.md:313 and :321 — "`docker_smoke.sh`
  requires it" / "fails the build if the smoke episode reports [fault]"; design.md:780-783 —
  the third copy of the closed key set is "`tools/ci/docker_smoke.sh`'s expected-key set".
  `AGENTS.md` (in-repo) instead names `ci.yml` as the third place, and
  `tests/test_results.py:58-66` checks the `ci.yml` copy.
- Consequence: the substance is enforced in CI (observed green at
  `docker-smoke → Assert the smoke results are the closed key set`, log line
  `results OK: complete full_time [256, 542, 808, 188]`), but the local invocation
  `AGENTS.md` documents (`./tools/ci/docker_smoke.sh coworld-halite:local`) checks neither.
- The four **seat-count** invariants the checklist requires of this script *are* in it
  (`docker_smoke.sh:110-151`, all prefixed `SEAT-COUNT FAIL:`); see Traced.

## F5 — A `/client/replay` route exists on the game pod

- Where: `server/cogame_halite/server.py:413-429` — `/replay-data`, `/client/replay` (302 to
  `/client/replay/index.html?replay=/replay-data`) and a static mount of `viewer/dist` at
  `/client/replay/`; registered on the **episode** app too (`server.py:165`).
- Observed: this is the cogame-moba starter's own shape
  (`/workspace/starters/cogame-moba/server/cogame_moba/server.py:793-797`), and the design note
  asks for it explicitly: design.md:652 — "`/client/replay` serving the same bundle locally".
  The shipped viewer itself contacts nothing but the replay bytes it is handed
  (`replay-viewer/static_replay.js:188-233`, `static_replay_worker.js:119-140`).
- Checklist item 3 says "No `/client/replay` pod path anywhere". Note and checklist disagree
  here; recorded as an observation, not adjudicated.

## F6 — `game.docs` / `game.protocols` use `{"type":"uri"}`, not `{"type":"text"}`

- Where: `coworld_manifest_template.json` → `game.docs.readme = {"type":"uri","value":
  "https://github.com/Metta-AI/cogame-halite/blob/main/README.md"}`, `game.docs.pages[*].content`
  likewise; `game.protocols.player` and `.global` are both `{"type":"uri","value":…/docs/PROTOCOL.md}`.
  Asserted in that shape by `tests/test_manifest.py:71-85`.
- Observed: identical in shape to the starter
  (`/workspace/starters/cogame-moba/coworld_manifest_template.json`), and the installed
  `coworld==0.1.43` CLI's own `_load_template_manifest` + `validate_upload_manifest` accept it —
  `tests/test_manifest.py:289-303` ran in CI (331 passed, 2 skipped; the 2 skips are the ctf-mount
  test and the built-bundle test, see F8).
- Note says: design.md:952-955 requires `readme`/`pages` and **both** `player` and `global` as
  objects — satisfied. Checklist item 10 spells the objects as `{"type":"text","value":…}`.

## F7 — Four ids the note lists as "Removed" are still in the DOM as hidden stubs

- Where: `client/replay_broadcast.html:1211` (`#momentum, #lulls, #ffwd-chip, #ffwd-mini
  { display: none !important; }`), `:1232` (`#ffwd-mini`), `:1255` (`#ffwd-chip`), `:1262`
  (`#momentum`), `:1266` (`#lulls`); the page's banner explains it at `:1020-1027`.
- Observed reason (verified): the byte-pinned `client/chrome_common.js` dereferences all four
  unconditionally — `chrome_common.js:455-456` (`$('ffwd-chip')`, `$('ffwd-mini')`), `:521`
  (`$('lulls')`), and the momentum block at `:621-659`. `tests/test_viewer.py:117-130` asserts
  both the stubs' presence and that every id `chrome_common.js` dereferences exists.
- Note says: design.md:858-861 lists `#momentum`, `#lulls`, `#ffwd-chip`, `#ffwd-mini` under
  **Removed** with "their CSS blocks". The tree keeps the nodes (never written to, never drawn);
  the note does not record the exception.

## F8 — The byte-for-byte chrome pin is verified only in the sandbox, never in CI

- Where: `tests/test_viewer.py:34-41` — `pytest.skip("the coworld-ctf mount is not present")`
  when `/workspace/starters/coworld-ctf` is absent, which is always true on a GitHub runner.
- Observed: CI reports `331 passed, 2 skipped`; this is one of the two skips (the other is
  `test_the_built_bundle_parses_the_ci_replay_under_node`, which needs a built bundle).
  I ran the comparison here: `client/chrome_common.js` and `client/broadcast_core.js` are
  **byte-identical** to coworld-ctf's (sha256 `7ace7287…` and `172c4680…` on both sides).
- Note says: design.md:76, :828-829 — ctf's chrome "byte-for-byte". True in the tree; the pin
  simply has no CI enforcement.

## F9 — Two of the three viewer-smoke passes measure no text at all (`canvas_text.total == 0`)

- Where: `.github/workflows/ci.yml:220-244` (bundle + replay run) and `:277-285` (360×640 run),
  both with `--strict-text-bounds`; the gate is `tools/ci/viewer_smoke.mjs:601-603`
  (`never_inside > 0` → exit 1).
- Observed (CI artifact `viewer-smoke`): the main run and the narrow run both report
  `canvas_text {total: 0, outside: 0, never_inside: 0}` — the board is drawn on an
  OffscreenCanvas inside the Worker (`replay-viewer/static_replay.js:212-228`), so the page-side
  `fillText` hook sees nothing. Only the renderer-fixture pass measures anything:
  `total 7072, outside 141, ellipsized 0, never_inside 0`, and `ci.yml:302-318` gates
  `total >= 12` and `never_inside == 0` on it.
- Note says: design.md:909-910, :1096-1108 — 360×640 "checks the featured-match width" and the
  fixture "drives the page's own text path". Both runs do exercise load + soak + layout
  (`loaded: true`, tick advanced 0→65 and 0→64), so the passes are not vacuous overall; it is
  the **text-bounds** part of the first two that measures nothing, exactly the case
  checklist item 15 calls out ("`total: 0` … is not evidence of anything").

## F10 — Over-cap action entries are dropped but never counted

- Where: `server/cogame_halite/engine.py:161-163` — `for key in sorted(raw, key=_uid_key): if
  len(actions) >= 256: break`. Nothing increments any counter for the discarded entries;
  `results.fallbacks` (results.py:150-153) only carries the five wire causes.
- Note says: design.md:712 — "over 256 → first 256 by ascending uid kept, rest **dropped and
  counted**". The keep-first-256-by-ascending-uid half is implemented and tested
  (`tests/test_engine.py:288-301`); the counting half is absent.

## F11 — The fidelity gate compares `status`/`reward` once, not "at every turn"

- Where: `tests/test_fidelity.py:111-132` (`_assert_identical` compares `step`, `halite`
  element-for-element, and each player's `[bank, shipyards, ships]` **with dict insertion
  order**) and `:158-168` (statuses/rewards compared only against the **final** state, plus
  `sim.eliminated == [None]*4`). `tests/upstream_reference.py:28-39` does record
  `status`/`reward` per turn, so the data is captured but not compared per turn.
- Note says: design.md:628-632 and `docs/RULES.md:172-179` — "equality of the full observation
  at every turn … `step`, and each agent's `status`/`reward`".
- Inferred: with no elimination in the stream every status is `ACTIVE` and `reward` tracks the
  bank, which *is* compared per turn, so the omission has no live consequence for this stream —
  but it is also why F1 is invisible to the gate.

## F12 — At most one player-failure payload is ever written per episode

- Where: `server/cogame_halite/server.py:351-363` — `_write_failure` returns early if
  `self._failure_reported`; the flag is set on the first write. The lobby path
  (`server.py:300-305`) reports the lowest-seat no-show/unregistered seat; the engine's
  per-dead-seat callback (`engine.py:502-514`, which loops over every dead seat) then finds the
  flag already set.
- Note says: design.md:417-419 — "Dead seats are reported **once** to
  `COGAME_PLAYER_FAILURE_URI` with the closed payload"; design.md:355-356 — the no-register seat
  is "reported to `COGAME_PLAYER_FAILURE_URI`". Both are satisfied for the first failure; a
  second failing seat in the same episode is silent on that channel (it is still in
  `results.dead_seats` and in the `strike` events). The payload shape is exactly
  `{"message","failed_policy_index"}` (`server.py:357` asserts it).

## F13 — The worker's `importScripts` drops a fourth item beyond the "exactly three adaptations"

- Where: `replay-viewer/static_replay_worker.js:248` —
  `importScripts('./broadcast_core.js', './halite_replay.js');` vs coworld-ctf's
  `importScripts('./wire_constants.js', './broadcast_core.js', './ctf_replay.js');`.
- Observed: `wire_constants.js` does not exist anywhere in the coworld-ctf tree (it is generated
  by ctf's own build), so it could not be copied; `tests/test_viewer.py:74` pins the new line.
- Note says: design.md:824-827 and the file's own header (`static_replay_worker.js:5-9`) claim
  "exactly the three adaptations". This is a fourth, necessary, undocumented one.

## F14 — The remote history carries nine duplicated early commits

- Where: `git log` at `f403fa0` shows two parallel chains of the same nine messages
  (`26f4ae6…6c1bcac` and `d965bc1…9024357`, plus `8f7c8a5` and `c7c0853`, both
  "vendor: initialise the repository"), all timestamped `2026-08-27 23:58`.
- Observed: the tree at HEAD is single and coherent; nothing is duplicated in the working tree.
  Reported because it is visible to anyone reading the repo's history.

## F15 — No grid-tuning harness for the baseline constants exists in the tree

- Where: `server/cogame_halite/micro.py:58-63` — `TIDEWALKER = Directive()` (mine/300/2/100/500/
  CENTER) and `CORSAIR = Directive(stance="raid", spawnUntil=340, yards=2, mineFloor=150,
  returnAt=350)`; the surrounding constants `MAX_SHIPS = 24`, `PATCH_RADIUS = 6` (`:29-30`),
  `bank >= 1500` and `far >= 5` (`:231-240`), `cargo <= 100` / `ecargo >= cargo + 200`
  (`:283-286`).
- Observed: `grep -ri grid` over the repo returns only the vendored upstream board generator and
  an art-sheet comment — there is no tuning harness, sweep script or recorded sweep output.
- Note says: the design note names the constants (design.md:497-525) and their rationale but does
  not describe a tuning harness either. Checklist item 7's second sentence ("The baseline's
  parameters were tuned with a grid harness, not guessed") has no artefact in the tree to point
  at. The first sentence of item 7 **is** satisfied (see Traced).

## F16 — `HOST`/`PORT` in the note are `COGAME_HOST`/`COGAME_PORT` in the code

- Where: `server/cogame_halite/server.py:449-450`
  (`os.environ.get("COGAME_HOST", "0.0.0.0")`, `COGAME_PORT` default `8080`);
  `docs/PROTOCOL.md:11` documents the same names; `tools/ci/docker_smoke.sh:204-205` sets them.
- Note says: design.md:646-648 lists the runtime contract as "`HOST`/`PORT`". The starter
  (`cogame-moba/server/cogame_moba/server.py:804`) uses `COGAME_HOST` too, so this is inherited
  shorthand in the note rather than a code change.

---

## Traced and consistent

**Vendor and the two transcriptions**
- `vendor/upstream/**` is byte-identical to the published
  `kaggle_environments-1.32.7-py3-none-any.whl` — I downloaded the wheel and compared sha256 for
  all four files (`131e30de…`, `44f1ddf9…`, `358c94fb…`, `29f97303…`), and those are exactly the
  digests recorded in `vendor/UPSTREAM.md`. Zero patches, confirmed.
- `sim/assemble.py:32-67` copies only the four vendor files plus three shim `__init__.py`s;
  `tests/test_vendor.py:74-89` asserts the assembled tree contains nothing else and is byte-equal.
- Transcription 1 (`populate_board` adapter, `sim.py:172-211`): calls upstream's own
  `populate_board` body through duck types; the global `random` and `numpy` RNG states are saved
  and restored around it (`sim.py:186-200`), so board generation is unperturbable. Covered by
  the 50-seed generation test.
- Transcription 2: see F1.

**Resolution rules 1-11 (design.md:201-247)**
- `sim.step()` (`sim.py:229-272`) constructs the vendored `Board(observation, configuration,
  actions)` and calls `.next()`; rules 1-8 are upstream's code, not a re-implementation.
  `tests/test_sim.py` has a test per numbered rule (spawn-before-convert and the bank ceiling,
  `leftover_convert_halite`, the zeroed cell, the ram rule, the equal-cargo mutual kill, the
  three-way pile-up, friendly fire, yard razing, deposit-after-collision, all four mining gates,
  regen skipping occupied cells with `round(x,3)` and the 500 cap, torus wrap in four directions,
  uid minting `f"{turn}-{n}"` across seats, elimination, last fleet).
- Rule 11 (record): `engine.py:402-440` appends state + accepted orders + derived events + hash
  per turn. `AssertionError` from vendored code is re-raised as `HaliteGuardError`
  (`sim.py:257-258`), and the guards at `sim.py:461-474` cover negative bank/cargo/cell and the
  5 000-ship ceiling; order-map size and unknown action values are rejected at `sim.py:236-245`.
- Turn count: `engine.py:411-426` — the loop records turn 0…`episode_steps-1` and steps
  `episode_steps-1` times, so 400 states / 399 `Board.next()` calls, matching design.md:174-177.
- Fidelity gate: 8 seeds (`GATE_SEEDS`, 8 entries) × `GATE_TURNS = 399`, 50-seed board
  generation, starting positions `[110,120,320,330]`, and a floor test
  (`test_fidelity.py:199-204`) that fails if any of those shrink. It ran in CI (the `test` job
  syncs the `fidelity` group at `ci.yml:60-61`; 331 passed in 261 s).

**Decision path**
- One parallel batch per turn: `engine.py:236-253` writes every `observe` frame, then
  `:256-279` awaits all replies in a single `asyncio.wait(..., timeout=deadline_ms/1000.0)`.
  `tests/test_engine.py:44-71` asserts the trace is four sends *then* four receives per turn,
  and `:90-101` is a static scan forbidding a bare `await state.link.receive()`.
- Player-side ladder: attempt 1 at 12 s, one retry at 5 s with a shortened prompt
  (`players/llm.py:40-41, 313-332`), logging `will retry` on attempt 1 and `falling back` only
  on the genuine fallback (`:325-327`); on double failure the previous directive stands and the
  player still answers within the deadline with `source: "scripted"` and a ≤140-rune note
  (`players/halite_player.py:71-94`).
- Repair/clamp table (`players/llm.py:191-219`) matches design.md:468-475 exactly:
  `spawnUntil→[0,maxTurns]`, `yards→[1,4]`, `mineFloor→[0,500]`, `returnAt→[50,1500]`, unknown
  `stance`/`focus` keep the previous value, `avoid` must be one of the three opponent aliases
  else `null`, unknown fields dropped, missing fields inherit, turn-0 defaults =
  `Directive()` = `mine/300/2/100/500/CENTER/None` (`micro.py:34-58`). `extract_json`
  (`llm.py:149-182`) takes the first balanced object and tolerates fences and trailing prose.
- Server-side ladder: `engine.py:281-326` maps late→`timeout`, `None`→`disconnected`,
  bad type/actions→`malformed`, wrong turn→`wrong_turn`, send failure→`host_error`; every
  substitution is `micro.compile_turn(..., TIDEWALKER)` in-process (`engine.py:137-140`) and
  emits a `fallback` event. Strike at `STRIKE_LIMIT = 10` (`defaults.py:113`,
  `engine.py:373-379`); a struck seat still receives its frame but is not awaited
  (`engine.py:219, 258`), and a valid reply revives it (`_probe_dead`, `engine.py:328-356`).
  All of this is covered by `tests/test_engine.py:104-196`.
- Env switch: `players/halite_player.py:29-52` — `PLAYER_PROMPT` → LLM, `PLAYER_SCRIPTED` ∈
  {tidewalker, corsair}, anything else → `tidewalker` with a log line. `tools/ci/policies.json`
  has two `PLAYER_PROMPT` champions (both carrying `USE_BEDROCK: "true"`) and two scripted
  fillers, with `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` on champion #2 — exactly
  design.md:987-1001. Model/`max_tokens`/no-`effort` pins match (`llm.py:38-39, 265-272`).

**Every wait and its bound**
- micro turn 400 ms, directive turn 18 000 ms (`defaults.py:100-101`, applied at
  `engine.py:192-194`); directive spacing floor 10 000 ms measured from when the previous batch
  *opened* (`engine.py:221-233`), so spacing and deadline do not stack — worst directive turn is
  `max(10, batch) ≤ 18 s`, which is what design.md:374 models; lobby 120 s
  (`server.py:281-284`); budget guard 600 s (`engine.py:199-203`, no seat is asked anything
  afterwards — asserted in `tests/test_engine.py:199-213`); hard stop 660 s at a turn boundary →
  `end_rule wall_clock` → `reason deadline`, still scored (`engine.py:401-410`,
  `tests/test_engine.py:215-227`); shutdown grace 20 s (`server.py:50, 494`); artifact writes
  3 × 30 s (`uris.py:29-31`); player connect 20 s socket timeout with ≤5 attempts
  (`players/client.py:35-36, 97-130`). The only unbounded loop I found is replay mode's
  `while True: await asyncio.sleep(3600)` (`server.py:460-461`), which runs only when
  `COGAME_LOAD_REPLAY_URI` is set and no episode is played. See F3 for the total.

**Rune truncation** — every cap goes through `defaults.truncate_runes` (`defaults.py:143-159`,
which also scrubs lone surrogates via `encode("utf-8","replace")`): `note` 140
(`events.py:54-62`, `llm.py:218`, `halite_player.py:76-79`), `register.label` 40
(`server.py:255-257`), `results.stop_detail` 200 (`results.py:155`), `fallback` detail 120
(`events.py:71`), `PLAYER_PROMPT` strategy 2 000 (`llm.py:115`).
`tests/test_players.py:182-209` feeds 4-byte emoji at every cap and asserts a lone surrogate is
scrubbed; `tests/test_replay.py:81-90` parses the whole document with strict UTF-8.

**Replay writer** — `replay.py:70-96` emits `format`/`version`/`gameVersion`/`protocol`/
`coworld`/`seed`/`config`/`names`/`aliases`/`policySources`/`colors`/`turns`/`results`/`stop`;
`to_bytes()` is `json.dumps(..., ensure_ascii=False).encode("utf-8")`; `document()` refuses to
serialise without a `stop` record (`:71-72`), and `set_stop` uses the same `events.stop()`
constructor on record and re-derive (`:65-68`). Per-turn `halite` is integers, exact floats
pinned by the hash (`sim.py:511-519`, `tests/test_replay.py:114-119`). Every event is validated
against the closed `EVENT_SCHEMA` at write time (`replay.py:52-53`, `events.py:97-107`).

**Re-derivation** — `tests/test_replay.py:131-223` replays `seed` + recorded per-turn `orders`
on a fresh `HaliteSim` and asserts **every** recorded `hash`, once per end reason:
`full_time`, `last_fleet` (a real three-way mutual kill at (10,10)), `wall_clock` (injected
clock) and `fault` (injected `HaliteGuardError`), with the `wall_clock` case also asserting the
stop record is not re-invented. `state_hash` is FNV-1a 64 over the canonical encoding the note
specifies (`sim.py:115-149`), stability covered by `tests/test_hash.py`.

**Viewer**
- `client/chrome_common.js` and `client/broadcast_core.js` are byte-identical to coworld-ctf's
  (verified here, see F8).
- `replay-viewer/static_replay.js` and `static_replay_worker.js` are ctf's with the three
  documented adaptations and nothing else beyond F13: I diffed both against
  `/workspace/starters/coworld-ctf/replay-viewer/` — the removals are exactly `setMismatchTick`
  / `mismatchTick`, `start()` now takes the bytes the page fetched, and `_ctf_*` → `_halite_*`.
- `replay-viewer/config.nims` is ctf's link block with the outputs and exports renamed; it has
  **no** `MODULARIZE`/`EXPORT_NAME`, and the worker boots on `Module.onRuntimeInitialized` —
  the matched pair checklist item 13 asks for. `tests/test_viewer.py:44-60` also cross-checks
  that every `Module._halite_*` the worker calls is in `EXPORTED_FUNCTIONS`.
- `client/replay_broadcast.html`: I diffed lines 1-999 (everything above the
  `HALITE additions to the inherited coworld-ctf chrome` banner at `:1001-1042`) against ctf's
  page. **The only changed line is the `<title>` (line 6); every other hunk is a pure deletion.**
  The deleted blocks are the fpv/lockerroom/viewpanel/minimap/povBadge/mmwarn CSS the note lists.
  The retained DOM (`:1214-1284`) is ctf's markup minus those same blocks, ids identical.
  (Structural note: because the banner sits before `</head>`, the inherited **DOM** lives below
  the banner rather than above it, so the "diff the CSS above the banner" recipe covers the CSS
  only; I compared the DOM by hand.)
- Transport rules: `relayout()` (`:1340-1358`) sets `--hudscale`, `--topband`, `--band` on
  `document.documentElement` and iterates to a fixed point; the board is fitted between the two
  bands (`:96-98`); `#endcard` is `bottom: var(--band, 0px)` (`:721`), shown with `#endcard.on`
  (`:732`, `showEndcard` at `:1631-1633`) and dismissed by `seek()` (`:1666-1669`), which every
  button, the scrub click and the keyboard path funnel through. Scrubber beats are
  `<button>`s with `title` + `aria-label` + a click handler that seeks (`:1556-1574`), built by
  `haliteBeat` (never `markBeat`, which is aliased from the chrome at `:1327`), with a CSS rule
  for every kind `events.py::BEAT_KINDS` emits — `.convert/.collide/.yardraze/.eliminate/.lead/
  .guard` at `:1157-1189`. `#viewpanel` and its whole family are absent
  (`tests/test_viewer.py:96-114`), and `chrome_common.js` never references them, so the removal
  is safe.
- `data-replay-loaded="true"` is set on the first drawn frame from the worker's `loaded` message
  (`static_replay.js:167-172`) and `data-replay-error` on every failure path (`:26-38`); the
  bridge `ready` is posted from a `MutationObserver` on `data-replay-loaded`
  (`tests/test_viewer.py:218-224`). CI observed `loaded: true` in all three passes
  (304 ms / 277 ms / 331 ms) and a soak that advanced 0 → 65 and 0 → 64 turns.
- `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` at `:1048-1059`; secondary labels hidden
  under 640 px (`:1104-1105`, driven by `stage.classList.toggle('tiny', w < 640)`).
  The CI geometry readout at 360×640 shows `tiny=1 feed=[6,355] row=[6,355]` on a 360-wide
  viewport — the feed band and its rows are inside the frame.
- **Playback opens at the game start.** The replay format records no lobby at all: `turns[0]` is
  sim turn 0 (`engine.py:402-423`), the page starts at `turnIndex = 0` (`:1305`) and the scrubber
  axis is `st: 0` (`:1639`). The lobby-dwell failure mode of checklist item 13 is structurally
  absent here rather than handled.
- The renderer draws the **recorded** per-turn state (`replay-viewer/halite_replay.nim:10-13`),
  and the cargo-at-risk predicate is the ram rule's own (`nim` + the page's `riskOf` at
  `:1327-1341` use enemy cargo ≤ mine within distance 1).

**Manifest / packaging**
- `num_agents: 4` inside `game_config` of all three variants (`standard`, `sprint`,
  `richfields`) and inside `certification.game_config`; **never** at a variant top level
  (variant keys are exactly `{id,name,description,game_config}`).
  `certification.players` and `certification.game_config.players` both have 4 entries and seat
  both declared bundled players (tidewalker, corsair, tidewalker, corsair).
- `episode_timeout_minutes: 20` at top level; `game.replay_viewer = {"bundle":
  "static-replay-viewer"}` **under `game`**; `tags` has 4 entries; no top-level `version`, no
  `game.display_name`, `game.owner` and `game.description` present.
- `results_schema` is `additionalProperties: false` and its property list is **exactly** equal,
  in order, to `results.py::RESULTS_KEYS` (23 keys) — I compared them programmatically; the
  third copy is `ci.yml:106-123`, which imports `RESULTS_KEYS` (see F4).
- Every `config_schema` array (`tokens`, `players`) declares `minItems: 4`/`maxItems: 4`; the
  seven rule constants are pinned min=max to their upstream defaults, mirrored by
  `config.py::PINNED_RULE_FIELDS`; no `game_config` carries a literal `tokens`.
- `SMOKE_SEATS: "4"` (`ci.yml:102`) cross-checks `certification.game_config.num_agents`;
  `docker_smoke.sh:110-151` implements all four invariants with `SEAT-COUNT FAIL:` prefixes.
  **I grepped the full CI log for `SEAT-COUNT FAIL`: 0 occurrences**, and the smoke printed
  `game=halite seats=4 … smoke OK: seats=4 … reason=complete`.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows,
  `docker_smoke.sh` and `policies.json` exits non-zero (no matches) — clean.
- `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both committed `100755`
  (git index mode verified). `coworld-release.yml` orders build → certify → upload policies →
  upload-coworld → canonical poll → `secret put`.

**CI (checklist item 1)**
- Run **33133144503** on `main`, head sha `f403fa0e99ba4637fb2af2bcab5de61bf30cd776`,
  conclusion `success`; `test`, `docker-smoke`, `wasm-viewer` all `success`, `wasm-viewer`
  `needs: docker-smoke` (`ci.yml:148`). Every step in every job ran (none skipped, no
  `continue-on-error`), including `Load the bundle in a real browser`, the 360×640 pass and the
  renderer-fixture pass.
- No test loosened this run: `git log -p a3a7781..HEAD -- tests/` shows three changes only —
  a **tightened** assertion in `test_viewer.py:274-283` (`"three canvas sizes" in text or …` →
  an exact `SIZES = …` match), one **added** test
  (`test_ci_gates_the_renderer_fixture_on_a_non_vacuous_text_count`), and the new
  `tests/page_dom_harness.mjs`. No deletion, no widened tolerance, no skip/xfail added, no test
  file removed.

**Other checklist properties confirmed**
- Two name spaces: the `observe` and `hello` frames carry aliases only (`engine.py:120-124`,
  `server.py:228-241`); real names appear in `results.names`, the replay header `names`, the
  scorebug plates (`replay_broadcast.html` `realName()`) and the endcard.
  `tests/test_privacy.py` asserts both directions.
- Scripted baseline plays a full legal episode: `tests/test_micro.py:71-107` checks ≤1 action per
  owned asset, only owned ids, only enum values, ≤256 entries, no unaffordable `SPAWN`, no
  `CONVERT` onto a shipyard cell over 200 random boards × both baselines, plus the safety
  property and determinism; `tests/test_replay.py:48-62` and the containerised
  `docker-smoke` (all four seats scripted, no `ANTHROPIC_API_KEY`) both end
  `reason == "complete"` (`results OK: complete full_time [256, 542, 808, 188]`).
- Scoring: `results.py:51-89` implements `banked` / `eliminated - episode_steps - 1`, higher is
  better, with the four-rule tie-break ladder and shared placements (1,1,3,4) but a strict
  `ranking`; `winner` is `null` on a shared first place. `tests/test_results.py:84-149` covers
  each rung including a three-way tie and a `deadline` episode.

## Could not determine

- **Whether the 141 `outside` text draws in the renderer fixture correspond to real clipping.**
  The fixture's samples at 900×560 and 360×640 show the full-cap note's element box extending
  past the right edge (`right` 904 vs canvas 900; `right` 413 vs canvas 360), while the same
  run's geometry readout says `feed=[6,355] row=[6,355]` on the 360-wide frame — i.e. the band
  and the row are inside. The likely explanation (inferred) is that `elementRuns`
  (`tools/ci/renderer_fixture.html:126-145`) takes the union box of a **wrapped inline** leaf and
  the transcription redraws it as one line, which cannot be right-edge-accurate. `never_inside`
  is 0 either way, which is the number checklist item 15 gates. Settling it needs a browser: run
  `viewer_smoke.mjs --url …renderer_fixture.html --strict-text-bounds` with the per-line-box
  transcription (or a screenshot at 360×640) and compare `.hal-note`'s client rects to `#stage`.
- **Whether F1's divergence can occur in a real ladder episode.** It needs a seat to lose every
  ship while holding an unfunded shipyard. The scripted baselines guard against exactly that
  (`micro.py:215-229`, the shipyard-loss guard), so it may be unreachable with the shipped
  policies but is reachable for an LLM directive that spends the bank down. A soak of N
  all-LLM episodes counting `eliminated_turn` with `yards > 0` at elimination would settle it.
- **Whether the platform's manifest validator would prefer `{"type":"text"}` docs (F6).** The
  installed `coworld==0.1.43` accepts the `uri` form (CI-verified), and the starter uses it; only
  the platform's own upload path can settle whether the rendered page differs.
- **The real wall-clock profile (F3).** The 743 s figure is arithmetic from the code's bounds, not
  a measurement. A single hosted episode with a deliberately slow lobby, timing from container
  start to `results.json`, would settle it.

---

Summary: 16 findings — 1 executed upstream-fidelity divergence (F1), 1 executed
protocol/portability mismatch (F2), 1 wall-clock budget arithmetic gap (F3), and 13
note-vs-code or coverage observations; CI is green at the reviewed sha with no test loosened.
