# r1 fixes — minecraft

Repo: `Metta-AI/cogame-minecraft`. Reviewed sha `c1acf2182d80287a3c4e6c7ab773bcce928f8038`.
Head after fixes: **`6b4ac8afa3c53bdb32b187ac4e7cc9da4cb51266`**
CI: <https://github.com/Metta-AI/cogame-minecraft/actions/runs/33245676171> — **success** (see the
CI section at the end; run **33245571607** at `729eb929` was also green, one commit earlier).

Every commit was pushed through the GitHub Git Data API (raw `git push` over HTTPS is refused in
this sandbox), so the shas below are the shas on `main`. One commit per finding, in finding order,
plus one fix-forward on a flaky assertion (F6).

The whole Nim test suite was run locally, in **both** debug and `-d:release`, after every commit
(`nimby`'s package tree and Nim 2.2.4 were available in the sandbox); Docker, emsdk and the browser
were not, so `docker-smoke` and `wasm-viewer` are verified only by CI.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | fixed | `dde652f8` | `tests/test_minecraft_viewer.nim:142-153`, `docs/PORTING-MINECRAFT.md` §I |
| F2 | fixed | `631a3139` | `src/minecraft/replays.nim:104-146`, `src/minecraft/server.nim:619-628`, `tests/test_minecraft_replay.nim` (new test 31b) |
| F3 | fixed | `ae1a720a` | `src/minecraft/directives.nim:52-53,224-231`, `src/minecraft/server.nim:617-620`, `tests/test_minecraft_driver.nim:188-244` |
| F4 | fixed | `9d7e2ec3` | `src/minecraft/world.nim:74-79,250`, `src/minecraft/baselines.nim`, `src/minecraft/sim_types.nim:18`, `coworld_manifest_template.json`, fixtures, `docs/PORTING-MINECRAFT.md` §C/§G |
| F5 | fixed (24 kept, docs corrected) | `284a77a6` | `src/minecraft/replays.nim:356-368`, `.github/workflows/ci.yml:353-357`, `docs/PORTING-MINECRAFT.md` §J |
| F6 | fixed | `ca591621` + `6b4ac8af` | `.github/workflows/ci.yml`, `tools/ci/renderer_fixture.html`, `client/replay_broadcast.html:4360-4378,4894`, `tests/test_minecraft_viewer.nim`, `tools/ci/fixture_smoke.mjs` (deleted) |
| F7 | fixed | `a9113e66` | `client/replay_broadcast.html:873-877`, `tests/test_minecraft_viewer.nim:129-160` |
| F8 | fixed (differently — see below) | `17f5fe3e` | `tests/test_minecraft_viewer.nim:44-70` |
| F9 | no change, recorded | `f3603e31` | `docs/PORTING-MINECRAFT.md` §L |
| F10 | no production change; test strengthened | `982707f5` | `tests/test_minecraft_replay.nim:151-160` |
| F11 | fixed | `c1d913ee` | `tests/test_minecraft_replay.nim:111-137` |
| F12 | no change, recorded | `fd68c354` | `docs/PORTING-MINECRAFT.md` §M |
| F13 | fixed | `f7e67710` | `src/minecraft/sim_types.nim:339-352`, `src/minecraft/llm.nim:204-209`, `tests/test_minecraft_driver.nim:255-268` |
| F14 | fixed | `c5aa1838` | `src/minecraft/decide.nim:204-213` |
| F15 | fixed | `9ec9a3e2` | `src/minecraft/broadcast.nim:34-57,102-127`, `src/minecraft/sim_state.nim:78-81,349-352`, `tests/test_minecraft_events.nim` |
| F16 | 2 fixed, 2 documented in place, 1 DISPUTED | `31f72222` | `src/minecraft/driver.nim:40-52`, `src/minecraft/agent.nim`, `src/minecraft/world.nim`, `tests/test_minecraft_driver.nim` |
| F17 | no change, recorded | `daf0a591` | `docs/PORTING-MINECRAFT.md` §N |
| F18 | resolved by F4 + F21 (seed is the note's 42 again) | `9d7e2ec3`, `729eb929` | `coworld_manifest_template.json`, `docs/PORTING-MINECRAFT.md` §G |
| F19 | no change (`uri` is correct); test strengthened | `d3e7987f` | `tests/test_minecraft_manifest.nim:38-58` |
| F20 | fixed | `5da07713` | `src/minecraft/roster.nim:15-22`, `src/minecraft/server.nim:187-199`, `tests/test_minecraft_engine.nim:267-277` |
| F21 | fixed — and it found a generator defect | `729eb929` | `tests/test_minecraft_world.nim` (reference solver), `src/minecraft/world.nim` (post-pass 2b), `sim_types.nim`, fixtures, `baseline_tuning.json`, `docs/PORTING-MINECRAFT.md` §O |

---

## F1 — a test assertion was deleted and replaced with a weaker one (BLOCKING, checklist item 1)

`tests/test_minecraft_viewer.nim:143` had `doAssert "core.setZoom(" in block1`, which any `setZoom`
call anywhere in the 867-line block satisfies. It replaced `doAssert "core.setZoom(32 /
CAMERA_CELLS)"`, an exact-expression pin.

The camera mechanism did change in the same commit, so the old string cannot come back. What is
asserted now is the *current* mechanism, pinned as three exact strings — the read-back, the guard
and the call:

```nim
doAssert "var cellsNow = t.visW > 0 ? t.visW / 24 : CAMERA_CELLS;" in block1
doAssert "if (followArmed && Math.abs(cellsNow - CAMERA_CELLS) > 0.5) {" in block1
doAssert "core.setZoom((t.zoom || 1) * (cellsNow / CAMERA_CELLS));" in block1
```

plus the kept `CAMERA_CELLS = 15`, `core.panTo(` and `followArmed`. That is strictly stronger than
the deleted predicate: the old one pinned one expression, this pins the whole three-line loop, and
no edit to the follow-cam can pass it unnoticed. `docs/PORTING-MINECRAFT.md` §I records why the
note's closed form `32 / cameraCells` is not what the page does (it is only correct when the board
is letterboxed on its width; the shipped screenshot came back at ~4 cells across).
**Evidence:** `nim r --path:src tests/test_minecraft_viewer.nim` passes; reverting either
`replay_broadcast.html:4662` or `:4664` fails it.
**Checklist item 1** — no test is disabled, skipped or loosened at the head.

## F2 — LLM text never reached the static viewer on playback

`applyControlRecord` (`replays.nim:104-130`) handled `start` / `turnend` / `stop` and `discard`ed
everything else, so on playback `sim.feedDirectives` stayed empty and `sim.fallbackTurns[0]` stayed
0: `broadcast.nim:273` never emitted `state["directives"]`, and the block's say row, its
`MISSED THE CALL — miner plan` row and the plate's `↯` glyph could not render from replay bytes.

`applyControlRecord` now also applies `directive`: it pushes the record onto the feed and derives
the per-seat `llm` / `fallback` counts from the record's own `source` field. `server.nim` and both
test harnesses call that proc instead of counting by hand, so record and playback derive the same
numbers from the same bytes. Nothing here enters `gameHash` (`sim_state.nim:210-225` mixes tick,
cog, inventory, tools, ladder, world digest), so the hash chain is untouched.

**Evidence:** new test 31b (`tests/test_minecraft_replay.nim`) records an episode whose every turn
is a no-credentials fallback carrying a `say`, re-derives it from the bytes and asserts
`feedDirectives.len > 0`, `fallbackTurns[0] == recorded.fallbackTurns`, the say text is in the
re-derived feed, and `buildStateJson` carries `directives[0].say` and `mc.fallbacks`. The end-rule
round-trips still report `hashMismatchTick == -1`.
**Checklist item 2** — the viewer's display, including the narration, is derived from the
re-derivation.

## F3 — `actionsDropped` and `repliesRepaired` were the same number

`Plan` gains `repaired`. `parsePlan` counts over-cap entries in `dropped` (note 5a → `actionsDropped`)
and invalid entries in `repaired` (note 5b → `repliesRepaired`); the server adds each to its own
counter. What the model is told next turn is unchanged: `last_plan.dropped` is the sum, which is the
note's "reported back as `dropped` next turn".
**Evidence:** `tests/test_minecraft_driver.nim` asserts both counters on both causes — two invalid
entries give `repaired == 2, dropped == 0`; thirty entries against a cap of twelve give
`dropped == 18, repaired == 0`.

## F4 — lava was effectively absent

Measured with the repo's own generator, 300 seeds of each variant: at the note's `C < 120`,
`standard` held **0.11** lava cells on `z=2` and **0.38** on `z=3`, and 97/300 seeds had any lava —
the reviewer's numbers reproduce exactly. `world.nim` gains a named `LavaCaveGate = 300`:

| gate | | `z=2` | `z=3` | seeds with any lava |
|---|---|---|---|---|
| 120 | standard | 0.11 | 0.38 | 97/300 |
| 300 | standard | 1.56 | 4.21 | **295/300** |
| 300 | deepcut | 2.41 | 6.37 | 298/300 |

Everything else in rule 2 is the note's. The change is a difficulty change and carries its
consequences, all in the one commit: `GameVersion` 1 → 2 (prepend-only changelog), both fixtures
re-cut, `tools/tune_baselines.nim` re-run and `baseline_tuning.json` + `DefaultBaselineParams`
re-pinned to the new sweep, and `docs/PORTING-MINECRAFT.md` §C rewritten with the measurements and
the difficulty note (the scripted miner now dies in lava on ~1 standard seed in 10; it died on 0 of
100 before).

The sweep also exposed a **real baseline defect** that no seed had reached before: `safestStep`
returned a default `fcNorth` when the cog had **no** traversable neighbour, which walked it into the
lava it was fleeing. `tests/test_minecraft_driver.nim`'s test 19 ("baselines never suicide") caught
it; the miner now mines its way out instead. I did not weaken that test to get past it.

Test 26's dropped lava clause is **asserted again** rather than documented away: the certification
seed was re-probed with the committed `tools/probe_seeds.nim` (whose filter now carries the note's
lava clause) and the fixture regenerated. See F18/F21 — after F21's re-sweep the seed is the note's
own 42 again.
**Evidence:** `test_minecraft_engine` prints `ok: the cert seed reaches 11 rungs, z=3, 532 ticks,
1 lava events`; `test_minecraft_world`'s 200-seed invariants and 60-seed completability still pass;
`tune_baselines --check` is green.

## F5 — playback rate

Chosen: **keep 24 ticks/s**, fix the documentation. `ReplayFps` *is* `TargetFps` (`sim_types.nim`),
so a recorded time and a tick are the same clock and `tickTime`/`tickOfTime` round-trip exactly only
at one tick per frame; the note's 10 ticks/s (5 ticks per 12 frames here) needs a sub-tick
accumulator on both sides, and the speed chips are integer step counts per frame, so its `0.5` chip
is a skipped frame rather than a slower step. The soak requirement is met with a 4× margin either
way: 960 ticks = 40 s of playback against `--soak 10`.
The stale doc comment in `advanceReplayFrame`, `ci.yml`'s soak comment (which also said 96 s) and
`docs/PORTING-MINECRAFT.md` §J now all carry 24.

## F6 — the renderer fixture: the real gate, and its own strings

Two halves.

**The harness.** The fixture is now driven by `viewer_smoke.mjs --url … --strict-text-bounds`, the
same binary the main smoke uses, in its own `ci.yml` step, against the shipped bundle served out of
`dist/static-replay-viewer`. The fixture sets `data-replay-loaded="true"` only after every scenario
drew *and* every assertion held, and `data-replay-error="<message>"` otherwise.
`tools/ci/fixture_smoke.mjs` is deleted rather than left as a second, weaker gate.

**The strings — stated explicitly, as the brief asks.** `canvas_text.total` is **0** for this viewer
and always will be: there is no `fillText`/`strokeText` in `client/replay_broadcast.html` or
`client/broadcast_core.js` (asserted by test 44), so every string it draws is DOM and
`--strict-text-bounds` is vacuous on its own. The fixture therefore asserts the **DOM** strings: after
each of its 21 draws it reads the narration row back out of the iframe and fails unless the drawn
say is the full 160-rune string character for character, its row is unclipped
(`scrollWidth`/`scrollHeight` vs `clientWidth`/`clientHeight`), and its box is inside the frame —
measured after the row's 250 ms entrance animation has settled, so a slide-in is not read as a
clipped row. Its own `FULL_SAY` was 152 runes, not the 160-rune cap; it is now exactly 160 and the
fixture asserts that first.

That assertion immediately found the defect it exists to find: the block's
`.feed-row { white-space: nowrap; text-overflow: ellipsis }` applied to the `say` row too, so the
only LLM-authored sentence this viewer draws was **ellipsised to one line** in a 228u feed. The say
row now carries an `mc-narration` class with a wrapping, four-line **reserved band** sized from
`MaxSayRunes` (item 15's "reserved band … sized from the cap the server enforces"), and
`tests/test_minecraft_viewer.nim` pins the rule (`white-space: normal`, `text-overflow: clip`,
`min-height`, and the `'mc-narration'` class at the call site).

`6b4ac8af` is a fix-forward: the first CI run of this change (33244896048) failed on a *transient*
degenerate box read immediately after the iframe resize. The check now waits for the stage to come
back with a real box, retries a degenerate measurement up to four times (the feed is a queue with a
2600 ms dwell), and reports display/opacity/offsetParent/feed width/stage class/`--hudscale` when it
does fail. A wrong or clipped string still fails on the first read — those are never transient.
**Checklist item 15.**

## F7 — ctf's four surviving beat rules

`.beat-marker.kill`, `.steal` (+ `::after`), `.return` and `.capture` are removed from the inherited
prefix (the shared `.beat-marker` geometry is kept — this game's five kinds are drawn on it). Test 41
now sweeps the **whole page** instead of the appended block: none of ctf's eight kinds anywhere, and
the set of `.beat-marker.<kind>` rules in the page equals exactly
`{death, end, fallback, milestone, newdepth}`.

## F8 — the prefix is not byte-identical to the starter

The finding is right on both halves, but byte identity is not achievable: every hunk above the
banner is one of the note's **own** enumerated removals (FPV HUD/map CSS and JS, `#povBadge` markup
and JS, the four-team art loops, the spectator relabels, the `PB_` → `MC_` rename), and the starter
is in neither the repo nor CI, so a diff against it cannot run as a test here.

What the finding is really protecting — the prefix not moving again unannounced — is now tested:
test 39 pins the prefix's exact length (`211999`) and its SHA-1, the same discipline as
`chrome_common.js`'s sha256 pin, with a failure message telling the author to re-pin in the same
commit and name the removal; and it asserts the note's enumerated JS removals absent by name
(`renderFpvHud`, `renderFpvMap`, `fpvMap(`, `$('povBadge')`).
**Checklist item 14** (provenance) — unchanged and still satisfied.

## F9 — `broadcast_core.js` has none of the note's eight draw functions

**No change.** The board is composited into the starter's own sprite protocol by `global.nim`
(`buildBoardPacket`) and drawn by the starter's unmodified compositor; the four panels are DOM in
the appended block. That is why `client/broadcast_core.js` is one line from the starter's, and it is
also why this viewer has no canvas text at all — which is what makes item 15's DOM-side check the
meaningful one (F6). Recorded as `docs/PORTING-MINECRAFT.md` §L.

## F10 — `tickCap` is unreachable in a real episode

**No production change.** The note itself says the tick cap is "kept as an independent guard" and
"coincides with the turn cap"; deleting it would delete the guard. What was weak was the test:
`endRuleText() in [tickCap, turnCap]` for a loop that never calls `noteTurnEnd`, where the answer is
determined. It now asserts `== EndRuleTickCap` and `turnsPlayed == 0`, so the guard's own branch is
covered exactly.

## F11 — record → re-derive for four of six end rules, one of them mislabelled

Each case now carries the rule it **must** produce and asserts it before the re-derivation, so a
seed that drifts off its rule fails loudly instead of silently testing `turnCap` five times (which
is exactly what the case labelled "diamond" on seed 8 was doing). The table is `turnCap` (seed 8),
`diamond` (seed 42), `death` (seed 4 — a seed the miner genuinely walks into lava on; a hand-placed
lava cell cannot be used, because a replay re-generates its world from the recorded config),
`wallClock` and `fault`. That is **five of six** rules through record → re-derive with the hash chain
asserted tick by tick; the sixth, `tickCap`, is unreachable from a recording by construction (F10)
and stays covered in-sim in the same test.
**Checklist item 2.**

## F12 — the server starts the episode when the joined seat never registers

**No change.** The note asks for both "refuses to start the game" (named edit 2) and "produce a
finished episode inside the wall-clock budget" (test 27) for the same scenario; those cannot both
hold. The shipped behaviour keeps what the grf-football scar is about — a loud `ERROR:` line, a
declared closed-payload failure, `deadSeats[0]`, and the **published** `miner` baseline rather than a
hidden default — while still producing a scored episode. Recorded as §M.
**Checklist item 5** is unaffected: every wait on that path is bounded.

## F13 — `MaxReplyBytes` was enforced in runes

`sim_types` gains `truncateBytes`, which walks back off any UTF-8 continuation byte before cutting;
`llm.nim` uses it for the provider's reply. The bound is now the documented 4096 **bytes** instead of
up to 16 KiB, and item 9's rune discipline is untouched — the cut still lands on a codepoint
boundary.
**Evidence:** `tests/test_minecraft_driver.nim` feeds 4000 4-byte emoji and asserts the result is
≤ 4096 bytes, within one codepoint of the cap, and `validateUtf8() == -1`.

## F14 — attempt 2 also logged "will retry"

The echo is now conditional: attempt 1 says `will retry`, attempt 2 says `attempt 2 failed:`. The
`falling back` line phase 60 greps for is unchanged, and no replay record changed.

## F15 — `stepEvents` could emit ten of sixteen declared kinds

Two of the six missing kinds were state-derived facts the proc simply never built — `bridge` (the
note's `BRIDGED OVER THE LAVA` row, which had no event to fire it) and `blocked` — so the game
block's cases for them could never fire. Both are emitted now, from a bridge-counter delta and a new
monotonic `blockedActs` counter carrying the act and the reason. The other four (`turn`, `plan`,
`say`, `fallback`) are decision-layer facts the sim never sees; they reach the chrome through the
directive/fallback records, which F2 made re-derivable. So the constant is split: `BroadcastEventKinds`
(16, the broadcast vocabulary the page may handle) and `StepEventKinds` (12, what `stepEvents` can
emit), with the difference asserted to be exactly those four.
Test 47 now asserts **equality**, exhibiting every one of the twelve — hand-driving the five the
miner never produces (ascend, bridge, smelt, a blocked act, the lava interrupt, plus a death) — so a
declared kind nothing can emit fails the build.

## F16 — five small divergences

- **`goto` to the cog's own cell counted as `unreachable`** — fixed (`driver.nim`). It now yields
  zero primitives and counts nothing; a target the driver genuinely cannot path to still counts.
  Both asserted.
- **`craftedItem` unset for pickaxes** — the field was **write-only**: the tier-2 `Craft` event
  carries `what = $primitive` (`sim_state.nim:331`), and nothing in the repo reads `craftedItem`
  (verified by grep). No consumer could see the enum default. The dead field and its two assignments
  are deleted.
- **`floorCells = 702` vs the note's 700** — the note says "700" and "78 %" in one sentence and 78 %
  of 900 is 702, which satisfies both readings. A comment now says so in place. No behaviour change.
- **the tree scatter's `chebyshev <= 1` skip** — it protects post-pass 1's forced grass 3×3, which
  the note states one paragraph earlier and `test_minecraft_world.nim` asserts. Comment added.
- **`gameHash` mixes `cog.alive`** — **DISPUTED**. It is not in the note's listed mix order, but it
  is mixed identically on both paths (`sim_state.nim:224`, the only `gameHash`), it is deterministic,
  and it makes the one state change that is otherwise invisible to the chain — death — hash-visible.
  Removing it would weaken the chain and invalidate every committed fixture for nothing. Not changed.

## F17 — `llmTurns` / `fallbackTurns` are arrays

**No change.** Every other per-seat key in the results document is an array of length `num_agents`,
the manifest's `results_schema` declares these two the same way, and test 25 asserts the written key
set equals the declared key set exactly. Recorded as §N.

## F18 — the certification fixture's seed

Resolved rather than argued: after F4's live lava and F21's re-swept baseline, **seed 42 — the
note's own seed — satisfies every clause of test 26**: eleven rungs, `z = 3`, 532 ticks, ≥1 craft,
≥1 place, ≥1 ore mine, ≥1 dig-down, ≥1 blocked and **≥1 `lava` event**. The manifest is back on 42,
the fixture is `tests/fixtures/cert_seed_42.replay`, and `docs/PORTING-MINECRAFT.md` §G records the
round trip (42 → 8 → 674 → 42) and why each step happened. `tools/probe_seeds.nim` is the committed
probe and its filter is now exactly the note's list of clauses.

## F19 — `game.docs` / `game.protocols` typed `uri`

**No manifest change**, and the evidence the brief asked for: the starter's shipped, certified
manifest `/workspace/starters/coworld-ctf/coworld_manifest_paintbot.json` types **every one** of
these entries `uri` —
`docs.readme = {"type":"uri","value":"https://github.com/Metta-AI/coworld-ctf/blob/master/README.md"}`,
`docs.pages[].content` the same, and both `protocols.player` and `protocols.global`
`{"type":"uri","value":".../docs/PROTOCOL.md"}`. The design note prescribes the same. The checklist's
literal `"type":"text"` is spelling the **structure** (readme + pages with `id`/`title`/`content`,
both protocol keys as objects), which is present and asserted. `tests/test_minecraft_manifest.nim`
now carries that reasoning at the assertion and additionally asserts every `uri` value is an
`https://` URL.
**Checklist item 10.**

## F20 — test 27's closed-payload assertion was tautological

The payload builder moved to `roster.playerFailurePayload`, next to the results document;
`server.declarePlayerFailure` calls it, and the test asserts **that proc's** output is a closed
two-key object carrying the slot and the message it was given. The bytes the platform receives are
unchanged.

## F21 — the reference solver, its tick bound, and the dead seeds it found

`tests/test_minecraft_world.nim` now carries a real solver, test-only and not shipped: omniscient (it
reads `sim.world` directly, which no policy can) and free of the turn budget, but every action is a
real primitive through the real `sim.step` — chop two trees, craft, place a table, cut down, mine
eleven cobblestone and three coal, place a table, cut down, mine three iron, place a furnace, smelt,
place a table, cut down, take the diamond. Over the note's 60 seeds of both variants it reaches the
diamond every time, in at most **176** ticks on `standard` (bound 500) and **182** on `deepcut`
(bound 420). The deadlines are honest with a factor of three to spare, and that is now asserted.

Writing it found something first. On **35 of 300** `standard` seeds the spawn is ringed by **water**.
Water is neither walkable nor mineable; the only way across is `place_block`, which costs a
cobblestone, which needs a wooden pickaxe, planks and a log — and wood exists only on the surface.
Those seeds score **zero for every policy that will ever play them**, while the note's conclusion is
"every seed is completable". `world.nim`'s new post-pass 2b (`openSurfaceRoute`) does nothing on a
seed that already has a walkable route from spawn to a tree; on a sealed one it opens the cheapest
route to the nearest tree — fewest blocking cells, ties by cell index, so it is deterministic and
seed-pure — turning its water to sand and its rock to grass. 0 of 400 seeds of either variant are
sealed now, and the bedrock ring, the forced grass 3×3, the tree count and the ore minima are
untouched.

That is a generator change, so it carries the rest: `GameVersion` 2 → 3 with the changelog prepended,
the baseline sweep re-run and re-pinned (`woodPlanks: 16`, `stoneCobble: 16`), both fixtures re-cut
(`cert_seed_42.replay`, `turncap_seed_8.replay`), and §O. Test 24's battery also goes from 50 seeds
to the note's **100** — the miner clears rung 9 on 79 of them.

---

## NOTED (not fixed)

- `#povBadge`'s **CSS** survives in the inherited prefix at `client/replay_broadcast.html:529-547`,
  though its markup and its JS are gone (asserted absent by test 42). It is unreachable dead CSS of
  the same class as F7's beat rules, but no finding names it and the prefix is now digest-pinned
  (F8), so removing it would be an unannounced prefix edit. Worth a line in the next round.
- `seekReplay` clamps to `[0, maxTick]`, not `[startTick, maxTick]` (the reviewer's own "could not
  determine" note). With a zero-tick lobby this is at most one frozen frame, and no finding raised
  it; it is a two-character change if round 2 wants it.
- The **interrupt** rule is still rare even with live lava: it fires only on lava that becomes newly
  known while already within Chebyshev 1, and the 5×5 underground window usually reveals a lava cell
  two steps before the cog can stand next to it. Most lava deaths are a stale plan walking into a
  cell the cog learned about mid-turn. Recorded in §C; changing the rule would be a design change.

## CI

- Failed once, mine, and fixed forward: run
  <https://github.com/Metta-AI/cogame-minecraft/actions/runs/33244896048> (`wasm-viewer`, the
  renderer-fixture step, transient degenerate box at 640 px) → `6b4ac8af`.
- Green at `729eb929` (all 21 findings, one commit before the fix-forward):
  <https://github.com/Metta-AI/cogame-minecraft/actions/runs/33245571607> — **success**,
  `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓.
- Green at the head `6b4ac8afa3c53bdb32b187ac4e7cc9da4cb51266`: run **33245676171**,
  <https://github.com/Metta-AI/cogame-minecraft/actions/runs/33245676171> — **success**.
  `test` ✓ (12 steps), `docker-smoke` ✓ (10), `wasm-viewer` ✓ (19, `needs: docker-smoke`), no
  `continue-on-error`, no `SEAT-COUNT FAIL` in the log. The lines that matter, literally:

  - `test` — `ok: the reference solver reaches the diamond on 60 seeds of both variants in at most
    176 ticks (standard, cap 500) and 182 (deepcut, cap 420)`;
    `ok: the cert seed reaches 11 rungs, z=3, 532 ticks, 1 lava events`;
    `ok: miner 95466 beats scrounger 31012 and clears rung 9 on 79/100 standard seeds`;
    `ok: 2 committed replay fixtures carry GameVersion 3`;
    `swept 216 candidates; best score 35528` then `ok: the pinned tuning is still the swept pick`.
  - `docker-smoke` — `smoke OK: seats=1 results=1312B replay=118180B reason=complete`.
  - `wasm-viewer`, step "Load the bundle in a real browser" —
    `{"loaded":true,"ms":374,...}`,
    `soak: 10s of playback kept advancing ("0 / 531" -> "191 / 531" -> "240 / 531")`,
    `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
    (--strict-text-bounds)`.
  - `wasm-viewer`, step "Drive the renderer fixture" (now `viewer_smoke.mjs --strict-text-bounds`
    against the fixture page) — `{"loaded":true,"ms":8340,...}` and
    `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
    (--strict-text-bounds)`. `loaded:true` here is the fixture's own verdict: it sets
    `data-replay-loaded` only after all 21 draws and all of its string assertions passed. The
    `canvas text: 0` is expected and is why the fixture asserts the DOM strings (F6).
