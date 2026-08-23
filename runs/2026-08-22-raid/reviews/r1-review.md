# r1 review — raid

Repo: `Metta-AI/cogame-raid` @ `501040ded40f71756ecb5a4291490bd40a5e0806` (main, tip)
Range read: `cdc70c3..501040d` (whole tree; `cdc70c3` is the seed commit)
Files read: 58 (all of `src/`, `replay-viewer/`, `tests/`, `tools/`, `.github/workflows/`,
`client/replay_broadcast.html`, `client/broadcast_core.js`, `coworld_manifest_template.json`,
`data/foundry.mapspec.json`, `docs/{RULES,PROTOCOL}.md`, `README.md`, `AGENTS.md`,
`Dockerfile.replay-viewer`, `compose.yaml`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–12 + the
one-parallel-batch rule)
Design note: `/workspace/coworld-builder/runs/2026-08-22-raid/design.md`
(byte-identical to `docs/plans/2026-08-23-raid-design.md` — verified with `diff`)

CI evidence cited below is from `gh run list -R Metta-AI/cogame-raid --branch main -w ci.yml`
and the job logs of run **32611650222** (all three jobs `success`).

---

## Finding index (F-numbers as requested; §-ids used in the body)

| F | § | Category | Checklist item | One line |
|---|---|---|---|---|
| F1 | B1 | **blocking-candidate** | **9 rune-safe truncation** | four byte-index slices in `llm.nim` put captured error text into the replay |
| F2 | N1 | advisory (behaviour vs note) | — | `stalwartTank` overwrites its own `rxSoak`; no stalwart seat soaks a crucible while the tank is healthy |
| F3 | N2 | advisory, flagged for the judge | 7 (tuning clause) | the cited `tools/tune_baselines.nim` grid harness is not in the tree |
| F4 | N3 | advisory | — | control layer adds `planted` and `HealWasteFloor` heal gates the note does not specify |
| F5 | N4 | advisory | 5 (adjacent) | the done-broadcast 3.0 s deadline is a log line, not an enforced bound; untested |
| F6 | N5 | advisory | — | results written before the replay; note says replay first |
| F7 | N6 | advisory | — | first cleave/pour start on tick 95/191, note says 96/192 |
| F8 | N7 | advisory | — | `add_death.killer` is always `""` |
| F9 | N8 | advisory | — | `boss.nim:196`'s `damage < 40` branch is unreachable |
| F10 | N9 | advisory | 5 (adjacent) | attempt deadlines ceiling to 7 s + 3 s = exactly the 10 s turn budget |
| F11 | N10 | advisory | 5 (adjacent) | no distinct outer per-turn deadline; the bound is the two curly timeouts |
| F12 | N11 | advisory, flagged for the judge | 3 static-viewer (literal wording) | the game server still routes `/client/replay` |
| F13 | N12 | advisory | — | `/global` is JSON, not flatty (documented in-repo) |
| F14 | N13 | advisory | — | `AGENTS.md` lists a non-existent `roster.nim` |
| F15 | N14 | advisory | — | the player binary substitutes a built-in prompt instead of defaulting to `stalwart` |
| F16 | N15 | advisory | — | `avoidable_hits` skips crucible hits |
| F17 | N16 | advisory | — | Overload emits an aggregate `boss_hit` with `target: "raid"` |
| F18 | N17 | advisory | — | §Tests gaps: hung client, no-show/failure-URI, reconnect, wasm harness never runs in CI |
| F19 | N18 | advisory | — | `greenhorn` never leaves Forge, weaker than the note's description |

---

## Blocking

### B1 (F1) — four byte-index string slices in `llm.nim` put captured error text into the replay without a rune-boundary cut
- Where: `src/raid/llm.nim:207`, `:215`, `:220`, `:229`; consumed at `src/raid/llm.nim:303-304`,
  recorded at `src/raid/engine.nim:43-48`, serialised at `src/raid/replay.nim:96`
- Observed (traced, not run):
  - `llm.nim:207` `let detail = response.body[0 .. min(response.body.high, 400)]`
  - `llm.nim:215` `let detail = response.body[0 .. min(response.body.high, 300)]`
  - `llm.nim:220` `response.body[0 .. min(response.body.high, 300)]`
  - `llm.nim:229` `"JSON: " & result[0 .. min(result.high, 160)].replace("\n", " ")` — here
    `result` is the model's own concatenated `text` blocks (`llm.nim:224-226`), i.e. arbitrary
    UTF-8 the model chose.
  All four are **byte** slices. Each becomes the message of a `RaidError`; `decideAll`
  catches it at `llm.nim:298-305` and stores `detail: runeCap(error.msg, MaxDetailRunes)`;
  `engine.noteFallback` writes that string into the `fallback` event
  (`engine.nim:47`), and `replayJson` writes the event array into the replay
  (`replay.nim:96`, `:81-98`).
  `runeCap` (`src/raid/labels.nim:31-37`) is **not** a sanitiser: when
  `cleaned.runeLen <= limit` it `return cleaned` unchanged, so an already-truncated partial
  rune arriving from a byte slice is passed straight through. For the `:229` path the
  slice is ≤ ~170 bytes, far under the 200-rune cap, so `runeCap` returns it verbatim.
- Checklist item: **9. Rune-safe truncation** — "Every string that reaches the replay (`say`,
  `notes`, prompts, **captured errors**) is truncated on **rune** boundaries."
  Design note §"Reply schema and character caps": "any recorded error text (`fallback.detail`)
  ≤ 200 runes … **Truncation is on rune (Unicode codepoint) boundaries, never bytes.** In Nim
  that means … never slicing a `string` by byte index on any path that reaches the replay".
- Why blocking: a model reply or an API error body whose multi-byte character straddles byte
  160/300/400 produces a `fallback.detail` containing an invalid UTF-8 sequence, which is
  written into `raid.replay.v1`. That is exactly the failure `tests/test_replay.nim:37`
  (`validateUtf8(raw) == -1`), SPEC check 4 and `SMOKE_REQUIRE_REPLAY_JSON=1` exist to catch —
  and it only fires on the LLM path, which neither CI job exercises (the smoke runs with no
  credentials, `docker-smoke` log line "smoke OK: … reason=complete").
- Note what is *correct* here, so the fix is scoped: the other error-head truncation,
  `orders.nim:17-19`, already uses `runeSubStr` and is rune-safe; `say`/`note`/`policy`/`prompt`
  all go through `runeCap`/`runeSubStr` (`orders.nim:153-154`, `server.nim:368-369`, `:379`).
  Only the four `llm.nim` slices are byte-indexed.
- Untested: no test feeds multi-byte input at the *error-detail* cap.
  `tests/test_orders.nim:187-197` (`testDetailIsCapped`) uses `"e".repeat(900)` — pure ASCII —
  and `tests/test_orders.nim:122-147` covers the `say` path only. §Tests 8/9's multi-byte
  assertion therefore exists for `say` but not for captured errors.

---

## Non-blocking

### N1 (F2) — `stalwartTank` overwrites its own crucible-soak assignment; with a healthy tank no stalwart seat ever soaks
- Where: `src/raid/baselines.nim:180-208` (assignment at `:188`, overwrite at `:199`),
  `:123-145` (`crucibleSoakers`), `:277-280` (dps), `:230-231` (healer)
- Observed: `stalwartTank` sets `result.onTelegraph = rxSoak` at `:188` when
  `slot in crucibleSoakers(sim)`, together with `note: "tanking, and I take the crucible when
  it drops"` and `say: "crucible on me"`. Eleven lines later, `:199` executes
  `result.onTelegraph = rxDodge` **unconditionally** — the intervening comment (`:191-198`)
  justifies dodging *cleaves* and says nothing about the crucible. The `rxSoak` and the
  constructor's `rxHold` (`:183`) are therefore both dead; the misleading `note`/`say` survive
  into the `order` event and the viewer feed.
  `crucibleSoakers` (`:130-145`) returns `@[tank]` whenever the tank is alive above 60 % hp, so
  in that (normal) case `stalwartDps:277` and `stalwartHealer:230` see `slot notin soakers` and
  keep `rxDodge` too. Inferred consequence: every phase-3 Crucible Pour resolves with
  `hit.len == 0` (`telegraphs.nim:106-110`) and the boss banks a Spill stack, up to the cap of 5.
- What the note says: §Decisions → Scripted baselines: stalwart tank "In phase 3 takes `soak`
  when `hp > 0.6 × maxHp`"; "in phase 3 the highest-HP DPS takes `soak` when the tank is under
  60 %". `README.md:80-81` says "in Meltdown the raid stacks so a crucible splits three ways" —
  the stacking is real (`baselines.nim:40-44`, three spots inside one 110 px radius) but the
  three stacked DPS carry `dodge`, so they leave the circle during the 72-tick fuse.
- Why not blocking: the orders are still legal (checklist 7's legality clause holds, and
  `tests/test_baselines.nim:76-125` proves it); no checklist item names crucible soaking.
  This is a behaviour/comment contradiction, not a checklist falsification.
- Not asserted anywhere: no test covers `spillStacks` from a stalwart episode
  (`tests/test_baselines.nim:179-189` checks taunts, heals, telegraph resolves, adds killed and
  `overloadsResolved == 0` only).

### N2 (F3) — the grid harness the baseline comments cite is not in the tree
- Where: `src/raid/baselines.nim:19` ("`tools/tune_baselines.nim` sweeps them; these are what it
  kept"), `:221-222` ("the highest value the grid harness kept")
- Observed: `ls tools/` → `build_manifest.py  build_replay_viewer.sh  ci  gen_wire_constants.nim
  record_golden.nim  wasm_replay_smoke.cjs`. A repo-wide grep for `tune_baselines` matches only
  `baselines.nim:19`. There is no sweep script, no recorded sweep output, and no test that
  re-derives a tuned constant.
- Checklist item: **7**, second sentence — "The baseline's parameters were tuned with a grid
  harness, not guessed."
- Why not blocking *as I read it*: the checklist's testable clause (an all-scripted episode to
  the natural end, `reason == "complete"`, orders/actions inside legal bounds) is satisfied —
  `tests/test_engine.nim:154-160`, `tests/test_baselines.nim:76-148`, `tests/test_replay.nim:24`.
  I flag the tuning clause because a judge evaluating item 7 from the tree cannot verify it, and
  the code asserts a provenance the tree does not contain. What would settle it: the sweep script
  committed, or the comment amended to say how the numbers were chosen.

### N3 (F4) — the control layer adds two heal gates the note does not specify
- Where: `src/raid/control.nim:147-157` (`HealWasteFloor = 60`, `worthHealing`), `:352-360`
  (`planted`)
- Observed: `bit2 heal` is set only when the compiled move is `(0,0)` this tick (`:356`,
  `let planted = result.moveX == 0 and result.moveY == 0`) **and** the target is missing at
  least 60 hp (`:175-177`). Both are commented with their reasons.
- What the note says: §The control layer, 5. Action bits — "`bit2 heal` (healer) — set when a
  heal target is selected and mana ≥ 60 and no cast is running." No planted gate, no waste floor.
- Advisory: strictly fewer heals are started than the note's rule would start. Undeclared in the
  builder's delta list, but honestly commented in place.

### N4 (F5) — the done-broadcast "3.0 s per seat deadline" is a post-hoc log line, not an enforced bound
- Where: `src/raid/server.nim:129-141`
- Observed: `let deadline = epochTime() + DoneBroadcastSeconds` is computed, `socket.send(payload)`
  runs inside a `try`, and *then* `if epochTime() > deadline: echo … "exceeded its 3.0s budget;
  moving on"`. Nothing is cancelled or skipped; the deadline is measured, never applied.
- What the note says: §Decisions → Degrade, never hang — "a 3.0 s per-seat deadline on the final
  done-broadcast"; §Tests 11 — "the `done` broadcast is bounded at 3.0 s per seat".
- Why not blocking: mummy's `WebSocket.send` enqueues on the server's send queue rather than
  blocking on the socket (inferred from mummy's API, not verified here), so there is no unbounded
  *wait* to bound; checklist 5's "no blocking read" is not falsified by this line.
- Also observed: `tests/test_server.nim` contains no assertion about the done broadcast at all,
  so §Tests 11's last clause is unasserted.

### N5 (F6) — end-of-episode write order is results-then-replay, the note says replay-then-results
- Where: `src/raid/server.nim:143-162`
- Observed: `broadcastDone(results)` (`:156`) → `writeArtifact(runtimeConfig.resultsUri, …)`
  (`:159`) → `writeArtifact(runtimeConfig.replayUri, …)` (`:161`).
- What the note says: §Server — "the same **write order at the end of an episode** (broadcast
  `done` to every seat with a 3.0 s per-seat deadline → write the replay → `writeResults`,
  `src/ctf/server.nim:1940-1956`)". The code's own comment at `:154-155` gives the reason for
  broadcasting first ("the hosted worker tears player pods down as soon as results.json exists"),
  which is the same reason the replay is supposed to be written *before* results.
- Advisory: inverted relative to the note, and inverted against the stated rationale.

### N6 (F7) — the first cleave and the first pour start one tick early
- Where: `src/raid/state.nim:96` (`cleaveCd: CleaveFirstTick` = 96, `pourCd: PourFirstTick` = 192),
  `src/raid/boss.nim:8-13` (decrement), `src/raid/sim.nim:415-416` then `:432` (order within the
  tick)
- Observed: `tickBossTimers` decrements at step 7 of tick `t`, `scheduleBoss` fires at step 11 of
  the same tick when the counter is `<= 0`. After tick `t` the counter is `96 - (t + 1)`, so it
  reaches 0 at `t = 95` and the first cleave telegraph is created on **tick 95**; likewise the
  first pour on **tick 191**.
- What the note says: §SMELTER-9 — "The first cleave of an encounter starts at tick 96"; "First
  pour at tick 192."
- Advisory: 1/24 s, deterministic, pinned by the golden digests. Steady-state cadence *is* exact —
  `telegraphs.nim:92`/`:98`/`:105` re-arm at resolution and the next start lands exactly
  `CleaveCadence[phase]` ticks later (traced; `tests/test_boss.nim:26-41` asserts the re-arm value
  but not the start tick).

### N7 (F8) — `add_death.killer` is always the empty string
- Where: `src/raid/sim.nim:458-465`
- Observed: `sim.record("add_death", %*{"id": addName(...), "killer": "", "alive_after": ...})`.
  Nothing tracks who killed an add (`damageAdd`, `combat.nim:71-79`, credits
  `cogs[slot].damageToAdds` but stores no last-hitter).
- What the note says: §Event vocabulary — `add_death` carries `killer` (alias).
- Advisory: the field is present with a fixed empty value; `death.killer` for cogs *is*
  populated (`combat.nim:28-29`, `sim.nim:455`).

### N8 (F9) — `boss.nim:196`'s `if damage < 40` guard is unreachable
- Where: `src/raid/boss.nim:194-201`; complement at `src/raid/combat.nim:32-36`
- Observed: `damageCog` self-events every instance of `amount >= 40`, so `bossAndAddAttacks`
  records a landed swing only when `damage < 40`. `damage = sim.damageMultiplied(BossMeleeDamage)`
  with `BossMeleeDamage = 55` (`types.nim:90`) and every multiplier in
  `state.damageMultiplied:209-220` being ≥ 1 — the branch cannot be taken while
  `bossMeleeDamage` is a compile-time constant (it is: `config.nim:154` publishes it into the
  replay config but nothing reads it back).
- Advisory: dead code, no behavioural effect. The whiff branch (`:202-207`, `amount: 0`) is
  correct and matches the note's `boss_hit{ability:"swing", amount:0}`.

### N9 (F10) — the per-attempt LLM deadlines are ceilinged, so the worst-case turn is exactly the budget
- Where: `src/raid/llm.nim:129-141` (`ceilSeconds`), `:284-286`
- Observed: `attemptSeconds = ceilSeconds(6.5) = 7`, `retrySeconds = ceilSeconds(3.0) = 3`;
  `makeRequests(batch, timeout)` takes those ints. Worst case per turn = 7 + 3 = **10.0 s**.
  `config.validate` (`config.nim:72-75`) checks the *unrounded* `6.5 + 3.0 ≤ 10.0`, which passes.
- What the note says: §Decisions — "first attempt deadline **6.5 s** … retry with a **3.0 s**
  deadline … Worst case 6.5 + 3.0 = 9.5 s ≤ the 10.0 s turn budget."
- Advisory: the note's 54 × 10 s = 540 s line item is unchanged, so the 593 s / 720 s arithmetic
  still holds; the 0.5 s of slack the note claims does not exist.

### N10 (F11) — there is no separate outer per-turn deadline
- Where: `src/raid/engine.nim:77-102` (no per-turn timer), bound supplied by
  `src/raid/llm.nim:284-286`
- Observed: `runEncounter` calls `decide(sim, seats)` with no wrapper timeout; the only bounds on
  that call are the two `curly` timeouts inside `decideAll`.
- What the note says: §Decisions — "one outer per-turn deadline of 10.0 s".
- Advisory: checklist 5 asks that every wait have an explicit bound, and every wait does
  (7 s + 3 s). The named outer deadline is absent as a distinct mechanism.

### N11 (F12) — the game server still routes `/client/replay`
- Where: `src/raid/server.nim:406-413` (`result.get("/client/replay", replayPageHandler)`),
  asserted live by `tests/test_server.nim:141-146`
- Observed: the route exists and serves `client/replay_broadcast.html`. The manifest declares
  only `"replay_viewer": {"bundle": "static-replay-viewer"}`
  (`coworld_manifest_template.json`, `game.replay_viewer`) and never references a pod URL.
- Checklist item 3 reads "…and the viewer contacts nothing but S3. **No `/client/replay` pod path
  anywhere.**" Design note §Viewer explicitly keeps it: "The game server still serves
  `/client/replay` for local viewing off the identical `dist`." Both starters do the same
  (`/workspace/starters/coworld-ctf/src/ctf/server.nim:627,642,840`;
  `/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:470`).
- I record the tension rather than adjudicate it: the hosted viewer path is the static bundle
  (verified below), so the *intent* of item 3 is met; the literal words of item 3 are not.

### N12 (F13) — `/global` is JSON, not flatty
- Where: `src/raid/broadcast.nim:161-217` (`"protocol": "raid.global.v1"`, plain `JsonNode`);
  no `import flatty` anywhere in `src/` (grep: `flatty` appears only in `nimby.lock:14` and in
  the design note itself)
- What the note says: §Sim module — the flatty wire types are kept "(paintbot's `AGENTS.md` rule;
  it still holds — the live `/global` broadcast stream is flatty-encoded)".
- Advisory, and honestly documented: `docs/PROTOCOL.md` §`raid.global.v1` describes it as JSON,
  the manifest's `game.protocols.global` says the same, and `tests/test_server.nim:128-138`
  asserts the JSON shape. The note's flatty sentence is simply not what shipped.

### N13 (F14) — `AGENTS.md` still lists `roster.nim`; `render.nim` is gone without a note
- Where: `AGENTS.md` §Layout ("… `llm.nim`, `server.nim`, `labels.nim`, `events.nim`,
  `roster.nim`"); `ls src/raid/` has neither `roster.nim` nor `render.nim`
- Observed: join/auth/slot/token handling lives in `src/raid/server.nim:302-333`; rendering lives
  in `client/broadcast_core.js` and the wasm module. `engine.nim` — the file that *was* added — is
  correctly described in `AGENTS.md` and in `src/raid/engine.nim:1-11`.
- What the note says: §Packaging → Repo layout lists both `roster.nim` and `render.nim`.
- Advisory: the fold is defensible; the stale `AGENTS.md` line is the only inaccuracy.

### N14 (F15) — `raid_player.nim` substitutes a built-in prompt when neither env var is set
- Where: `src/raid_player.nim:22-34` (`DefaultPrompt`), `:41-44`
- Observed: if `PLAYER_PROMPT` is empty and `PLAYER_SCRIPTED` is empty, the player registers with
  `DefaultPrompt`, so the server (`server.nim:376-378`) sees a non-empty prompt and seats it as an
  **LLM** seat.
- What the note says: §Decisions — "A seat that sets neither defaults to
  `PLAYER_SCRIPTED=stalwart`"; §Server — "A seat that never registers, or registers with neither
  field, is treated as `scripted: 'stalwart'`."
- Advisory: the *server-side* rule the note states is implemented correctly
  (`server.nim:376-378`, `:208-216`); it is the player binary that never exercises it. Certification
  is unaffected — both manifest baseline players set `PLAYER_SCRIPTED`
  (`coworld_manifest_template.json` `player[0]`, `player[1]`), and the docker-smoke log shows
  `reason=complete`. Note that `game.player[2]` (`raid-player`) carries no `env` block at all and
  therefore relies on this default.

### N15 (F16) — `avoidable_hits` counts cleave and pour but not crucible
- Where: `src/raid/telegraphs.nim:96` (cleave), `:102` (pour); no increment in the `tkCrucible`
  branch `:104-115`
- What the note says: §Resolution order 17 — "`avoidable_hits` (a hit by a telegraph the cog was
  inside at resolution)".
- Advisory: arguably deliberate (a soaked crucible is not an avoidable hit) but uncommented.

### N16 (F17) — `boss_hit` for a resolved Overload uses `target: "raid"`
- Where: `src/raid/boss.nim:180-183`
- Observed: after damaging all five cogs individually (each of which self-events at
  `combat.nim:32`, since 70 ≥ 40), a sixth aggregate record is emitted with `"target": "raid"`.
- What the note says: §Event vocabulary — `boss_hit` carries `target` (alias).
- Advisory: `"raid"` is outside the alias vocabulary and the raid takes six records for one event.

### N17 (F18) — test-suite gaps against §Tests
- `tests/test_engine.nim`: §Tests 9's "the per-turn budget is enforced with a hung client" is not
  asserted — `FakeClient.hangSeconds` and `.attemptSeconds` (`test_engine.nim:19-20`) are declared
  and never read. Also absent: "a seat that never registers plays `stalwart` and is reported to
  `COGAME_PLAYER_FAILURE_URI`" and "a mid-encounter disconnect degrades to `stalwart` and revives
  on reconnect" (both behaviours exist — `server.nim:205-223`, `:394-403` — neither is tested).
- `tests/test_viewer.nim:132-153` (`testWasmHarness`) returns early unless
  `replay-viewer/dist/raid_replay.js` exists. The `test` job has no bundle and the `wasm-viewer`
  job never runs the tests (`.github/workflows/ci.yml:190-240` builds, asserts `index.html` +
  a non-empty `.wasm`, uploads). Verified in the run-32611650222 `test` log: the harness line does
  not appear. So `tools/wasm_replay_smoke.cjs` is committed but **never executed in CI**, and
  §Tests 15's tick-total / final-digest / seek assertions and its malformed-input rejection list
  (bad base64 length, truncated JSON, `tick_count`/payload mismatch) go unexercised.
  `tests/test_replay.nim:100-110` covers the wrong-`protocol` case only, natively.
- `tests/test_determinism.nim:129-144` ("a one-bit control change moves the digest") changes an
  *order* mid-run rather than flipping a recorded control byte; the docstring says "Flip one
  control byte".

### N18 (F19) — `greenhorn` is weaker than the note describes
- Where: `tests/test_baselines.nim:175-176` — `checkEq(weak.boss.phase, 1, "greenhorn never leaves
  Forge at seed " & $seed)` for seeds 42, 7, 1234, 999
- What the note says: §Decisions → `greenhorn` "reaches phase 2 reliably and almost never phase 3".
- Advisory: the ladder spread the note wants is present and stronger; the note's description of
  the floor is now wrong.

---

## Builder-declared deltas — verification

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | §Tests 7's default-variant stalwart kill replaced | **Real, implemented, partially commented** | `tests/test_baselines.nim:150-159` asserts the *cert fixture* kill (`reason=complete`, `end_rule=kill`, `tick<1200`, `aliveCount()>=1`, `simScore()>1.0`); `:161-177` asserts `stalwart > 2 × greenhorn` on 4 seeds. The test does **not** assert "all five alive" nor the 1.48 the builder reported (it asserts `>= 1` alive and `> 1.0` score). The arithmetic argument (45 hp/s healer ceiling vs ~52 hp/s intake) is written in `src/raid/baselines.nim:191-198`, but nothing in the tree records *why the note's test item was replaced* — the substitution is silent at the test site. |
| 2 | Tank at `PitCy−36`, heal targets restricted to reachable allies | **Real, implemented, honestly commented** | `baselines.nim:25` `TankStandDy* = 36` with `:22-24` naming the note's (617,180) and its 149 px gap against a 40 px melee range; `control.nim:129-145` `lowestReachableAlly` with a 6-line rationale. Traced: the boss body is `y 301..357` (`arena.nim:132-139`, `BossHalf=28`), the tank body at `(617,293)` spans `287..299`, so the stand is legal floor and inside the 40 px melee ring. |
| 3 | Dodge test asserts strictly-outward + ≥90 % full clear | **Real, honestly commented** | `tests/test_telegraphs.nim:98-141`: 64 sampled starts (16 brads × 4 distances), `check(dx*dx+dy*dy >= startDist)` for every one, `check(cleared*100 >= total*90)`. The docstring (`:99-105`) states plainly that it is weaker than "any starting point" and why (no pathfinder, pillars at radius 150). The note's "≥ 20 px of margin" is not asserted; the reaction itself targets `radius + PlayerHalf + 20` (`control.nim:33`), i.e. slightly *more* margin than the note asks. |
| 4 | `engine.nim` added; `roster.nim`/`render.nim` not built | **Real; documentation stale** | `src/raid/engine.nim:1-11` explains the split and is listed in `AGENTS.md`. But `AGENTS.md` §Layout still names `roster.nim`, which does not exist — see N13. |
| 5 | `/global` is JSON `raid.global.v1` | **Real, documented** | `broadcast.nim:195`; `docs/PROTOCOL.md` §`raid.global.v1`; manifest `game.protocols.global`; `tests/test_server.nim:132`. No in-repo note explains the departure from the design's flatty sentence — see N12. |
| 6 | Pillar spans mirror 1 px; pit exactly symmetric; test explains | **Real, honestly commented** | `tests/test_map.nim:28-67`: the docstring states the odd-centre 1 px mirror, the sweep skips pillar pixels (`:43-45`), and the four pillar centres are asserted exactly (`:56-57`) plus `dx²+dy² == 2·106²` (`:61-62`). `data/foundry.mapspec.json` pillars are `x∈{491,703}, y∈{203,415}`, so `[491,531)` mirrors to `[703,743]` against an actual `[703,743)`. |
| 7 | `data/foundry.mapspec.json` preloaded into the `.data` bundle | **Real, uncommented** | `replay-viewer/config.nims:34` `--preload-file {rootDir}/data@data`. Traced: `rederive` (`replay.nim:164-165`) always builds the arena from the replay's own `map` node and passes it to `initSim`, so `loadArena` (`arena.nim:176`) is never reached in the wasm build. The preload is what makes `raid_replay.data` exist, which `Dockerfile.replay-viewer` asserts (`test -f replay-viewer/dist/raid_replay.data`) and which the note's §Viewer bundle list requires. No comment in `config.nims` says any of that. |

---

## Traced and consistent

**Checklist items, verified item by item**

- **1 CI green / no test loosened.** `gh run list -R Metta-AI/cogame-raid --branch main -w ci.yml`:
  run **32611650222** on `501040d`, conclusion `success`, jobs `wasm-viewer` (1m40s),
  `docker-smoke` (1m2s), `test` (1m13s). `test` log shows all **17** `tests/*.nim` files run in
  **both** debug and `-d:release` (34 `::group::nim r` blocks), with `NIM_TESTS`,
  `NIM_TESTS_DEBUG_ONLY`, `NIM_TESTS_RELEASE_ONLY` all empty, so nothing was narrowed away.
  `git log -p -- tests/` over the whole run: the only post-seed change is `501040d`,
  `+3/−3` in `test_determinism.nim`, widening `seq[int]`→`seq[int64]` and `%int(...)`→`%int64(...)`.
  No assertion deleted, no tolerance widened, no skip added.
- **2 Replay re-derivation.** `replay.nim:148-188` `rederive` rebuilds the sim from
  `seed` + `map` + `config` + the recorded `order` events and recompiles the control bytes;
  `firstDigestMismatch:190-206` compares every recorded keyframe digest;
  `controlsMatch:208-215` compares the decoded `controls_b64` byte for byte.
  `tests/test_replay.nim:82-86` asserts both. The viewer uses the *same* function with
  `keyframeEvery = 1` (`replay-viewer/raid_replay.nim:54`) and renders `rebuilt.keyframes`
  (`:26-46`, `:88-98`) — the recorded keyframes are used only for the digest check, so the display
  is not a parallel recording. Mismatch surfaces as `raid_mismatch_tick` →
  `static_replay_worker.js:136` → `static_replay.js:44-48` → `data-replay-mismatch-tick` →
  `#mmwarn` (`client/replay_broadcast.html:1706`, `:2217`).
- **3 Static viewer.** `coworld_manifest_template.json` `game.replay_viewer` =
  `{"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode **100755**
  (`git ls-files -s`), keeps the absolute-path / name / symlink / in-repo guards (`:16-33`) and is
  invoked *by path* in `ci.yml:218` after an explicit `test -x` (`:205-217`). The worker fetches
  exactly one external URL — the `?replay=` argument (`static_replay_worker.js:118`) — plus
  same-origin bundle art (`:67-79`). See N11 for the `/client/replay` route.
- **4 Both name spaces.** `broadcast.seatView:64-159` emits aliases only; `tests/test_view.nim:55-76`
  greps every seat's view for the seed, other seats' notes, real names and prompt text.
  `broadcast.globalSnapshot:161-177` and `replay.namesJson:63-76` carry the real names, and the
  nameplate renderer reads `meta.names.players[i]` (`client/replay_broadcast.html:1839`).
- **5 Degrade-never-hang.** Bounds traced: connect wait `server.nim:184-191`
  (`playerConnectTimeoutSeconds`); register grace `:193-203` (≤ 3 s); LLM attempt/retry
  `llm.nim:284-286`; two-attempt cap `llm.nim:272`; budget guard `engine.nim:87-99` at
  `elapsed + 2 × turnBudget > wallClockBudget`; hard stop `engine.nim:105-110` checked every 24
  ticks; `config.validate:76-79` refuses `wallClockBudgetSeconds > 0.6 × episodeTimeoutSeconds`.
  Every loop I could find terminates: `applyCogAxis:103-126` (carry ≤ ~4 steps),
  `moveAdds`, `cogTrySlide:67-83` (radius ≤ 3), `clampIntoPit:626-631` (decrementing target),
  `intRoot:461-471` (Newton, monotone), `spawnPool:9-14` (deletes each pass),
  `extractJsonObject:25-42` (single pass). Manifest budgets: default 660, sprint 400, cert 180 —
  all ≤ 720 (`tests/test_manifest.nim:96-109`). `tests/test_engine.nim:71-117` covers the guard and
  the hard stop.
- **6 `num_agents`.** 5 in `variants[default]`, `variants[sprint]` and `certification.game_config`;
  `len(certification.players) == 5`; `len(certification.game_config.players) == 5`
  (read directly from the manifest and asserted at `tests/test_manifest.nim:10-32`).
  `tools/ci/docker_smoke.sh:98-141` carries all four invariants plus the independent
  `SMOKE_SEATS:-5` cross-check, each exiting with `SEAT-COUNT FAIL:`.
  **`grep -c 'SEAT-COUNT FAIL' <docker-smoke log> → 0`**; the job logged
  `game=raid seats=5 …` and `smoke OK: seats=5 results=1440B replay=47261B reason=complete`.
- **7 Scripted baseline plays full episodes legally.** `tests/test_engine.nim:154-160` runs an
  all-scripted episode to the natural end and asserts `reason == "complete"` with every `order`
  event `source == "scripted"`; `tests/test_baselines.nim:76-125` sweeps 500 perturbed worlds ×
  2 baselines × 3 deals, validating each order against `validateOrder` and each compiled control
  byte for range and role-bit ownership; `:127-148` asserts no ability fires on cooldown.
  (Tuning provenance: N2.)
- **8 LLM reply handling.** `orders.extractJsonObject:13-48` skips prose, matches balanced braces
  with string/escape awareness, and falls back to the last `}`; `parseOrder:134-160` repairs
  unknown enums to role defaults and only raises on a missing `intent`; `repairOrder:228-248`
  applies the note's repair table. `llm.decideAll:272-314` retries **exactly once**
  (`for attempt in 0 .. 1`) and then installs the `stalwart` order with `source = osFallback`;
  `engine.noteFallback:34-48` writes a `fallback` event with a closed `cause` enum and increments
  the per-seat counter that `scoring.resultsJson:75-79` publishes as `fallback_causes`.
  `tests/test_orders.nim:12-113`, `:149-197` cover the parse/repair/fallback paths.
- **9 (partial) Rune-safe truncation.** `labels.runeCap:31-37` uses `runeSubStr`;
  `orders.nim:153-154` caps `note`/`say`; `server.nim:368-369` caps the prompt with `runeSubStr`;
  `:379` caps the policy label; `orders.nim:17-19` caps an error head with `runeSubStr`.
  `tests/test_orders.nim:122-147` feeds a 4-byte emoji at rune 32, asserts the cut lands on the
  rune, that the result is valid UTF-8, that it round-trips `%*`/`$`/`parseJson`, and that a
  `callouts` copy is still valid UTF-8. Only the four `llm.nim` byte slices break the rule (B1).
- **10 Manifest validates.** `game.docs.readme` is
  `{"type":"text","value":…}`; `game.docs.pages` is two entries `rules.md` / `protocol.md`, each
  `{"id","title","content":{"type":"text","value":…}}` with 15 455 and 15 070 characters.
  `game.protocols` carries both `player` and `global`, each `{"type":"text","value":…}`.
  Asserted at `tests/test_manifest.nim:73-94`. `results_schema.properties` is exactly the 35 keys
  `scoring.resultsJson` emits and `scoring.resultsKeys()` lists (`:34-54`), with `reason` and
  `end_rule` closed to `state.LegalReasons`/`LegalEndRules` (`:56-71`) and `scores`
  min/maxItems 5, minimum 0.
- **11 Legible at 360 px.** `client/replay_broadcast.html:1556`
  `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; }`; `:1612-1628` `@media (max-width: 640px)` hides `#viewpanel` and
  `#speedchips .chip-label, .tbtn .label`, stacks `#nameplates` into two rows with 8 px pips,
  and keeps `#bossbar, #enrageclock, #castbar` unwrapped. `tests/test_viewer.nim:50-64` asserts
  the exact rule string and the media block.
- **12 Release order and scaffold.** `coworld-release.yml`: build manifest (`:153`) → certify
  (`:167`) → **upload the policies** (`:206`) → upload the Coworld (`:304`) → put the secret
  (`:342`). `ci.yml`'s `docker-smoke` job builds the image (`:172-173`) and runs the smoke
  (`:175-181`) in the same job, so the binary is always fresh. All three workflows present;
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` both mode **100755**.
  `tools/ci/policies.json`: four policies, all `"run": "/bin/raid-player"`; two `PLAYER_PROMPT`
  champions (`raid-anvil`, `raid-triage`) and two `PLAYER_SCRIPTED` fillers; champion #2
  carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The placeholder gate
  (`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows, the smoke script and
  policies.json) returns **no matches → exit 1 from grep → gate exits 0**.
- **Simultaneous decisions.** `llm.decideAll:275-286` builds one `RequestBatch` over every open
  seat and issues a single `client.curl.makeRequests(batch, timeout)`; the retry pass reuses the
  same shape. There is no per-seat request loop anywhere. `engine.runEncounter:77-102` calls
  `decide` at most once per turn with every living seat. `tests/test_engine.nim:48-69` asserts the
  in-flight windows intersect and that dead seats drop out.

**Design-note specifics traced and matching**

- Resolution order: `src/raid/sim.nim:367-486` runs the note's 19 steps in order —
  clock/enrage `:372-377`, control compile in seat order `:379-383`, quantise+record 4 bytes/cog
  `:385-398`, aim (cogs then boss, boss frozen under a live cleave via `boss.aimBoss:19-30` +
  `telegraphs.cleaveLive:16-20`) `:400-405`, cog then add motion `:407-412`, timers `:414-416`,
  abilities in the fixed sub-order interrupt→taunt→shield→heal-completion→attacks `:418-424`,
  threat folded in `combat.damageBoss:57-60` / `combat.addThreatFromHealing:84-88`,
  retarget on the 24-tick beat `boss.retargetBoss:32-47`, scheduling with
  Overload > Pour > Cleave `boss.scheduleBoss:136-160`, telegraph resolution in creation order
  `telegraphs.resolveTelegraphs:122-135`, pools `pools.updatePools:24-46`, boss+add attacks
  `boss.bossAndAddAttacks:185-219`, deaths `:443-466`, phase check `boss.checkPhase:239-247`,
  keyframe on `t mod 24` `:472-473`, end check in the note's order `:475-486`.
  (Two placements differ harmlessly: adds' cosmetic facing is set inside step 6 rather than
  step 4 (`sim.nim:219`), and cog–cog separation is resolved inside the per-axis step
  (`sim.nim:36-48`, `:85-95`) rather than as a separate pairwise pass.)
- Every boss number in `src/raid/types.nim:86-130` matches §SMELTER-9: cleave ±32 brads /
  180 px / 48-tick telegraph / 120 damage / cadence `[192,168,144]`; pour 90 px / 60 ticks /
  80 / `[240,216]` / pool 240 ticks biting 12 every 24, cap 6; crucible 110 px / 72 ticks /
  cadence 168 / 240 split `div k` with a Spill stack at `k == 0` capped at 5
  (`telegraphs.nim:104-115`); Overload 96-tick cast, 70 to all five, +400 boss hp
  (`boss.nim:167-183`); adds 220 hp / 640 speed / 30 px / 18 per 24 ticks / waves of 2 every 360
  in phase 2 / cap 8 / Feed at 4 (`boss.nim:77-107`, `:162-165`); enrage at 5760 with melee
  36→24 (`sim.nim:373-377`, `boss.nim:187-189`); multiplier order
  `base × feed × spill × enrage` truncated once at the end (`state.damageMultiplied:209-220`).
- Cast/fuse lengths are exact (traced tick by tick): a telegraph created on tick `T` resolves on
  `T + fuse`; a heal started at the end of tick `T` (`abilities.startHeals:191-212`) completes on
  `T + 24` (`:168-189`); Overload completes 96 ticks after `cast_start`.
- Scoring: `scoring.episodeScore:18-29` is `clamp(f · T / charged, 0, 3)` with
  `charged = elapsed` only for `"kill"` (`chargedSeconds:14-16`); `resultsJson:64` writes the
  same number into all five `scores`. `tests/test_scoring.nim:13-23` reproduces all six worked
  examples from the note's table to 3 decimals.
- Determinism: no banned float routine and no float literal in the ten integer-only modules,
  grepped by `tests/test_determinism.nim:73-98` on comment-and-string-stripped code with
  identifier-boundary matching; `-ffast-math` grepped in `Dockerfile`,
  `Dockerfile.replay-viewer`, `replay-viewer/config.nims`, `raid.nimble`. Golden fixture
  `tests/fixtures/golden_digests.json` pinned to seed 42 / 1200 ticks and checked against
  `GameVersion` (`:146-163`).
- Replay shape: `replay.replayJson:81-98` emits every documented top-level key;
  `controls_b64` is `tick_count × 5 × 4` bytes (asserted `tests/test_replay.nim:56-59`);
  keyframe encodings match the note's `[x,y,aim,hp,shield,mana,state]` /
  `[x,y,aim,hp,phase,feed,spill]` / `[id,x,y,hp]` / `[id,cx,cy,r,age]` /
  `[id,kind,cx,cy,r_or_facing,fuse,soak]` / `mtr` (`sim.appendKeyframe:272-297`);
  digests travel as `int64` on both sides after `501040d`.
- Map: `data/foundry.mapspec.json` is byte-for-byte the note's §Sim module JSON block.
- Bridge: `replay-viewer/static_replay.js:17-23` (`tell('loading')` at script entry),
  `:139-141` (`tell('ready')` inside a double `requestAnimationFrame` after `firstFrame`),
  `:41` (`tell('error', message)`), `:4` `FETCH_TIMEOUT_MS = 20000` with a Retry button
  (`:32-39`). `Dockerfile.replay-viewer` greps the built `dist/static_replay.js` for
  `coworld-replay`, and so does `tools/build_replay_viewer.sh:66`.
- Chrome: `client/chrome_common.js` is **byte-identical** to
  `/workspace/starters/coworld-ctf/client/chrome_common.js` (`diff -q`), as the note requires.
  All 56 inherited ids, the 11 added raid ids and the absence of the 11 CTF ids are asserted at
  `tests/test_viewer.nim:12-48`.

---

## Could not determine

- **Whether B1 actually fires in a hosted episode.** It needs a real Anthropic/Bedrock error body
  or a truncated model reply whose multi-byte character lands on byte 160/300/400. What would
  settle it: a unit test that raises through `textOf` with a non-ASCII body at the cap and asserts
  `validateUtf8(fallback.detail) == -1`, or a hosted episode's replay checked with `validateUtf8`.
- **The builder's quantitative claims for delta 1** — "score 1.48 with all five alive" on the cert
  fixture, "reaches Meltdown/71 % on default seed 42 but wipes". Neither is asserted in the tree
  (`tests/test_baselines.nim:150-159` asserts only `>= 1` alive and `> 1.0` score) and I have no
  Nim toolchain in this sandbox. What would settle it: a test that pins the numbers, or a CI log
  line printing them.
- **Whether N1 costs stalwart the encounter.** I traced that no seat carries `rxSoak` while the
  tank is healthy, and that a stacked DPS trio steers out of a 110 px circle inside 72 ticks at
  3.25 px/tick — but the resulting Spill count over a full episode needs a run. What would settle
  it: printing `world.boss.spillStacks` from `runScripted(testConfig(), skStalwart)`.
- **Whether `writeCogameUri` (bitworld/runtime) bounds its own wait.** `server.nim:97-109` bounds
  only the POST-to-http branch (`curl.post(..., 60)`); the default PUT path delegates to the
  dependency, whose source is not in this tree. Arithmetic if both artifact writes hit a 60 s
  ceiling after a 660 s engine stop: 780 s > 720 s. The episode has already *settled and scored*
  in memory at 660 s (`engine.nim:109`, `scoring.simScore`), so I do not read this as falsifying
  checklist 5, but the note's 30 s "board bake + results + replay writes" line item is not
  enforced anywhere. What would settle it: the timeout used by `writeCogameUri`.
- **Whether mummy's `WebSocket.send` can block** (N4). I inferred it enqueues; the dependency is
  not in this tree.
