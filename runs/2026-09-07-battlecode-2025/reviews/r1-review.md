# r1 review — 2026-09-07-battlecode-2025 (bc25 "Chromatic Conflict")

Range: `5e7c8b78..eb33a8d2` (PR #5, merged to main)
Repo: Metta-AI/cogame-battlecode, checkout `/tmp/cbc`
Checklist: `prompts/30-review-loop.md` § ACCEPTANCE CHECKLIST
Design note: `runs/2026-09-07-battlecode-2025/design.md` (mirrored in-repo at `docs/plans/2026-09-07-battlecode-2025-design.md`)

## Diff stat (summary)

```
106 files changed, 18201 insertions(+), 65 deletions(-)
```

Principal areas:
- `src/battlecode/years/bc25/**` (rules, world, units, towers, paint, patterns, maps, comms, constants, knobs) — the new year module
- `src/battlecode/years/bc25/chassis/**` — scripted baseline
- `src/battlecode/{decide,match,broadcast,render,results,sheet,sim_types,baselines,server}.nim` — shared plumbing touched by bc25
- `client/replay_broadcast.html`, `replay-viewer/`, `tools/ci/renderer_fixture.html` — viewer
- `coworld_manifest_template.json`, `tools/ci/policies.json`, `.github/workflows/ci.yml`
- `tests/test_bc25_*.nim` (20 files), `tools/oracle/bc25/**`, `tools/ci/parity_tiers_bc25.py`

Findings follow, numbered F1.. ; each cites `file:line`, observed behaviour, the design-note
expectation, and a severity guess. The judge decides finality.

---

## A. Manifest, `num_agents`, policies, release order

### F1 — `game.docs` uses `{"type":"uri",...}`, the checklist's literal shape says `"text"`; the design note says `uri`
- `coworld_manifest_template.json:27-36` (`readme`), `:37-100` (`pages`)
- Observed: `game.docs.readme = {"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/README.md"}`; each of the seven `pages` entries is `{"id","title","content":{"type":"uri","value":…}}`. All are `{type,value}` objects with the required `id`/`title`/`content` structure.
- Design note §Packaging (line 1443-1446): "`game.docs` — `readme` = `{"type":"uri","value":".../blob/main/README.md"}`; `pages` gains one entry and keeps the six it has". Seven pages observed: `rules.md`, `rules-bc20.md`, `rules-bc21.md`, `rules-bc24.md`, `rules-bc25.md`, `replay.md`, `parity.md` — exactly the note's list.
- Note: `prompts/30-review-loop.md` item 10 writes the shape with `"type":"text"`. The value here is `"uri"`, which the design note explicitly requires and which is **pre-existing** (unchanged by the bc25 diff for `readme` and the six inherited pages). Recorded as an observed difference between the checklist's literal illustration and the accepted design, not as a bc25 regression.
- Severity guess: **advisory** (shape is `{type,value}`, both `readme` and `pages` present; pre-existing across all five years).

### F2 — `num_agents` present in every variant's `game_config` and in the certification fixture
- `coworld_manifest_template.json:1437,1464,1491,1518,1545` (the five variants) and `:1581` (`certification.game_config`)
- Observed: all five variants (`bc26`, `bc20`, `bc21`, `bc24`, `bc25`) carry `game_config.num_agents = 2`; none carries `num_agents` at the variant top level; `certification.game_config.num_agents = 2`; `certification.players` = `[{"player_id":"awu"},{"player_id":"scaffold"}]` (length 2 == `num_agents`); `player[]` == exactly `["awu","scaffold"]`.
- Design note §Packaging (lines 1467-1493): matches — `num_agents` inside each variant's `game_config`, never at variant top level; certification unchanged and on `bc26`.
- Severity guess: **no finding** (traced and consistent; recorded here because the checklist names it).

### F3 — bc25 variant `game_config` matches the note's table exactly
- `coworld_manifest_template.json:1531-1560` (bc25 variant object)
- Observed: `year:"bc25"`, `pool:"mixed"`, `gamesPerMatch:3`, `seed:0`, `maxRounds:2000`, `num_agents:2`, `attempt1Ms:20000`, `retryMs:12000`, `doctrineBudgetMs:45000`, `perGameBudgetSeconds:110`, `matchBudgetSeconds:340`, `connectTimeoutMs:25000`, `players:[{"name":"Clan Ash"},{"name":"Clan Basil"}]`.
- Design note §Packaging line 1475: identical field-for-field.
- Severity guess: **no finding**.

### F4 — `config_schema.year.enum`, `results_schema` bc25 keys and `end_reason` enum all extended as specified
- `coworld_manifest_template.json` — `year.enum` (`["bc26","bc20","bc21","bc24","bc25"]`), `games.items.properties` (all 40 bc25 keys present: checked programmatically against the note's list at §Results document lines 1134-1142 — zero missing), `end_reason.enum` extended with `paint_enough_area`, `destroy_all_units`, `more_squares_painted`, `more_towers_alive`, `more_money`, `more_paint_in_units`, `more_robots_alive` (`coin_flip`, `abandoned` already present)
- `games.items.required` is unchanged at the five year-neutral keys `["map","side","rounds_played","winner","end_reason"]`; `reason.enum` unchanged `["complete","deadline","fault"]`.
- Design note §Packaging lines 1429-1440 and §Results document lines 1129-1146: matches.
- Severity guess: **no finding**.

### F5 — `tools/ci/policies.json`: four bc25 entries, champion #2 carries the pinned player id
- `tools/ci/policies.json` — entries `battlecode-bc25-coverage` (`PLAYER_PROMPT`, label `coverage`), `battlecode-bc25-siege` (`PLAYER_PROMPT`, label `siege`, `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `battlecode-spaark` (`PLAYER_SCRIPTED=spaark`), `battlecode-examplefuncsplayer25` (`PLAYER_SCRIPTED=examplefuncsplayer25`). All four use `"image":"cogame-battlecode-player:latest"` (the player service image) and `"run":"/bin/battlecode-player"`.
- Design note §Packaging lines 1519-1538: matches, including champion #2's player id and the player-image rule.
- File total is 20 policies (4 per year × 5 years); ≥ 4 distinct with 2 `PLAYER_PROMPT` + 2 scripted for bc25.
- Severity guess: **no finding**.

### F6 — placeholder gate exits 0
- Ran the checklist's own gate over `.github/workflows/{ci,coworld-release,coworld-submit}.yml`, `tools/ci/docker_smoke.sh`, `tools/ci/policies.json` for the three names `battlecode`-slug / `<IMAGE>` / `<SEATS>`: no match, gate exits 0.
- Severity guess: **no finding**.

### F7 — release step order
- `.github/workflows/coworld-release.yml:168` "Build the Coworld manifest" → `:182` "Certify locally" → `:225` "Upload the policies" → `:323` "Upload the Coworld" → `:419` "Put the Coworld secret".
- Design note §Packaging line 1502 and checklist item 12: build → certify → upload-policies → upload-coworld → secret put. Order matches. (This file is **not** touched by the bc25 diff.)
- Severity guess: **no finding**.

## B. Decision path (LLM call, parse, retry, fallback), waits and their bounds

### F8 — One parallel batch, one retry, monotonic phase budget; all three waits bounded
- `src/battlecode/decide.nim:626-751`
- Observed, traced step by step:
  - `:631-633` `budget = initDuration(ms = max(1, config.doctrineBudgetMs))` (45 000 for bc25), `started = getMonoTime()`.
  - `:636-643` both seats are seeded with the **baseline sheet first**, so a sheet always exists; LLM seats are added to `open`.
  - `:644-651` an LLM seat with a disabled client is recorded immediately as `fallback = "no_credentials"` plus a `doctrine_fallback` event and a log line containing `falling back`.
  - `:654` `while open.len > 0 and attempt < 2` — **exactly one retry**, no unbounded loop.
  - `:656-671` the monotonic budget is re-checked at the top of each attempt; on expiry every still-open seat is marked `timeout`, gets a `doctrine_fallback` event, and `open` is cleared before `break`.
  - `:672-673` `deadlineMs = attempt1Ms` (20 000) on attempt 0, `retryMs` (12 000) on attempt 1.
  - `:674-691` **one** `RequestBatch` built over all open seats and dispatched with a single `client.curl.makeRequests(batch, max(1, deadlineMs div 1000))`. No per-seat sequential call anywhere in the loop.
  - `:717-729` parse/transport failure → `doctrine_retry` event with a `cause` in `{timeout, transport, throttled, parse}`, log line `will retry`, seat stays open.
  - `:732-737` `client.throttled and open.len > 0` breaks out of the loop rather than issuing a retry that cannot land.
  - `:739-751` the tail loop replaces the sheet with `baselineSheet(...)`, sets `result.fallback[slot]`, emits `doctrine_fallback`, and logs `falling back`.
- Design note §Degrade-never-hang (lines 761-782) and §Decisions (594-599): matches — attempt1 20 000, retry 12 000, hard cap 45 000, one parallel batch, at most 2 provider calls per seat.
- The bc25 diff to this file is additive only: a `yBc25` arm in `chassisNameFor` (`:63`), `Bc25Preamble` (`:345-441`), a `preambleFor` arm (`:446`), and a `briefFor` `of yBc25:` payload block (`:545-615`). The control flow of `decide` is untouched by this diff (`git diff 5e7c8b78..eb33a8d2 -- src/battlecode/decide.nim` shows no hunk inside `proc decide`).
- Severity guess: **no finding**.

### F9 — Fallback is recorded so phase 60 can count it
- `src/battlecode/decide.nim:38-42` (`fallback*: array[2, string]`, `fallbackDetail*`), `:647,664,746` (cause set), `:648,665,747` (`doctrine_fallback` event), `:651,668,750` (log line containing the literal `falling back`).
- Design note §Degrade-never-hang line 766: "`results.fallbacks[seat] = 1`, a `doctrine_fallback` event names the cause, the log line says `falling back`". All three present.
- Severity guess: **no finding**.

### F10 — Rune-safe truncation, with a multi-byte test at the cap
- `src/battlecode/sim_types.nim:237-244` `truncateRunes` uses `runeLen`/`runeSubStr`; `:246-261` `truncateBytes` walks `text.runes` accumulating `r.size` and stops **before** exceeding the byte limit, so the cut is on a rune boundary; `:263-266` `sanitizeLine` collapses newlines then `truncateRunes`.
- Call sites reaching the replay: `sheet.nim:116-117` (`notes` → `MaxNoteRunes=280`, `motto` → `MaxMottoRunes=48`), `sheet.nim:101` (unknown keys → 40 runes, ≤ 16 of them), `sheet.nim:125` (whole reply → `truncateBytes(MaxReplyBytes=16384)`), `decide.nim:724,728` (captured provider error → `MaxFallbackDetailRunes=200`), `llm.nim:169,177,183,195,204` (provider body / prompt).
- Test: `tests/test_bc25_sheet.nim:147-156` feeds 500 × `\u00e9` as `notes` and 100 × `\U0001F3A8` (4-byte astral) as `motto` and asserts `runeLen == 280` / `48` **and** `validateUtf8() < 0` on both; `:158-176` builds a 20 001-astral-rune reply, caps it with `truncateBytes`, asserts `len <= 16384` and `validateUtf8() < 0`, and asserts the mid-string cut raises out of `parseReply` (the fallback trigger).
- Design note §Reply schema and caps lines 1110-1125: matches exactly, including the byte-vs-rune distinction for the 16 KB cap.
- Severity guess: **no finding**.

### F11 — Event field names diverge from the note's event table in three places
- `src/battlecode/match.nim:165-180` — `first_action` emits the field **`action`**, not the note's `kind`. The code comment at `:170-175` states the reason: `MatchEvent` flattens `fields` into the same object as the event's own `kind` key, so a field named `kind` would overwrite the event kind. `tests/test_bc25_replay.nim:185-197` asserts the field is `action` and that `e.kind` survives.
- `src/battlecode/match.nim:235-239` — `tower_lost` emits `alias, tower, x, y`. The note's table (line 1199) also lists **`remaining`**; it is not emitted.
- `src/battlecode/match.nim:244-248` — `srp_active` emits `alias, x, y, income_bonus`. The note's table (line 1201) also lists **`active_total`**; it is not emitted.
- `src/battlecode/match.nim:253-256` — `coverage` emits `permille` **plus** `tiles_from_win`, which the note's table does not list (though the note's example feed line, "79 tiles from the win", implies it).
- Design note §Event vocabulary carried by the replay, lines 1188-1208.
- Observed consequence: none of the four is read by a consumer that then fails — see §D for what the viewer's bc25 block actually reads.
- Severity guess: **advisory** (field-name drift from the note; the `kind`→`action` case is a deliberate, documented, tested correction of the note).

### F12 — Pre-match event bounds are stated in the note but not asserted, and `doctrine_retry`'s stated bound is below what the code can emit
- `tests/test_bc25_replay.nim:163-183` — the `Bounds` table covers only in-game kinds; `:172` `if e.game < 0: continue` skips every pre-match event, so `episode_start`, `doctrine_requested`, `doctrine_received`, `doctrine_retry`, `doctrine_fallback` and `episode_end` are not bound-checked.
- `src/battlecode/decide.nim:642` emits `doctrine_requested` **once per LLM seat** (in the seeding loop, not per attempt), so its ceiling is 2 against the note's bound of 4 — under-emitting relative to the note.
- `src/battlecode/decide.nim:725` emits `doctrine_retry` **once per failed seat per attempt**, so with 2 seats failing both attempts the ceiling is **4**, against the note's stated bound of **2** (line 1193).
- Design note §Event vocabulary lines 1191-1193 and §Tests item 20 line 1776 ("every event kind respects its per-game bound"). The note's per-kind bound column for pre-match events is not enforced by any test I found.
- Observed consequence: at most two extra small JSON records per episode; no growth risk (the loop is `attempt < 2`).
- Severity guess: **advisory**.

## C. Resolution rules — bc25 movement / paint / attack / tower / SRP order

### F13 — The six-step round loop matches the note's step list
- `src/battlecode/years/bc25/rules.nim:234-337` (`processBeginningOfRound`, `runRound`)
- Observed:
  - `:238` `inc w.currentRound`; `:239` `w.updateResourcePatterns()`; `:240-247` a sweep over `w.execOrder` **sorted ascending** (`ids.sort()`), `cleanMessages` for every unit and `mine` for towers only. The ascending-id sweep is the note's §Determinism divergence item 3 (design lines 431-435), documented in the file header at `rules.nim:22-27`.
  - `:273-280` the turn sweep iterates `let snapshot = w.execOrder` — a copy taken **before** the sweep — with `if not w.existsRobot(id): continue`, then `processBeginningOfTurn` → controller → `if w.existsRobot(id): processEndOfTurn`. A unit built this round is appended to `w.execOrder` and therefore **not** in `snapshot`, so it takes no turn this round (note rule 2, line 289-297).
  - `:285-296` rule 6a (coverage beats, peak coverage, starved/rout beats, the round-1000 snapshots); `:299` rule 6c/6d `checkEndOfMatch`; `:304-337` the round hash chain.
- Design note §The 2025 rule set (lines 279-413): matches step for step.
- Severity guess: **no finding**.

### F14 — The hash chain folds exactly the values the note lists
- `src/battlecode/years/bc25/rules.nim:304-337`
- Observed: per team — `livePainted`, `money`, `towers`, a packed tower-by-kind number, `robotsAlive`, `paintInUnits`, `numActiveResourcePatterns`, summed SRP lifetimes (8 values); globally — `currentRound`, an FNV-1a-64 of the colour array (`for y … for x`, y outer / x inner, `:305-308`), an FNV-1a-64 of both marker arrays (`:309-313`), `hpSum` (`:314-316`) and `w.execOrder.len` (`:337`).
- Design note §Determinism lines 871-876: the same eight per-team values and the same five globals, including the `y ascending outer, x ascending inner` colour-array order. Matches.
- Severity guess: **no finding**.

### F15 — End ladder, `timeLimitReached`, and the mid-action wins
- `rules.nim:175-190` — `timeLimitReached` is `currentRound >= w.maxRounds`, so round 2000 **is** played; `checkEndOfMatch` runs the five rungs in the engine's order (`more_squares_painted` → `more_towers_alive` → `more_money` → `more_paint_in_units` → `more_robots_alive`) and falls through to `setWinnerArbitrary` (`:167-173`), which draws from the **world RNG** (`w.rand.nextDouble()`) rather than `Math.random()` — the note's §Determinism divergence 2 (line 852). `running` is cleared only at `:189-190`.
- `src/battlecode/years/bc25/world.nim:424-431` — `addPaintedSquares` runs the 70 % check on **every** recolour (`livePainted >= tilesToWin(areaWithoutWalls)`), setting the winner mid-action but **not** stopping the round.
- `world.nim:628-653` — `destroyRobot` decrements `unitCount` and, at 0, `w.setWinner(r.team.other(), dfDestroyAllUnits)` immediately, mid-sweep.
- Design note lines 405, 417-421, 175-190: matches.
- Severity guess: **no finding**.

### F16 — The 70 % denominator is the engine's `areaWithoutWalls`, and `tilesToWin` is `ceil(0.70 × area)`
- `src/battlecode/years/bc25/units.nim:296-…` — `tilesToWin(area) = (area * PaintPercentToWin + 99) div 100`. For `DefaultSmall`'s area 372 this is `(26040+99) div 100 = 261`, the note's number (design line 233).
- `world.nim:1058` — `areaWithoutWalls: n - walls` where `n = width*height`, so ruin and tower tiles are counted, exactly the note's divergence #1 (design lines 229-234).
- `units.nim:291-294` — `coveragePermille = javaRound(painted * 1000.0 / areaWithoutWalls)`.
- Severity guess: **no finding**.

### F17 — Action preconditions and effect order, traced against the note's rule 4
- `world.nim:695-715` **move** — movement-ready, not `dCenter`, not a tower, on the map, unoccupied, passable; then move, **then** `addMovementCooldownTurns()` (surcharge from the post-move stash). Note rule 4.1 (line 309-312). ✓
- `world.nim:719-724, 746-765, 816-828` **soldier** — `r² ≤ 9` via `UnitSpecs[utSoldier].actionRadiusSquared`, `paint >= 5`, target not a wall; `doAttackRobot` charges the cooldown **before** `soldierAttack` deducts the 5 (note rule 4.2's pre-cost ordering, line 314-316); a tower of the other team takes 50 and the paint branch is skipped; otherwise the tile is repainted only if `existing == PaintNone or paintIsTeam(existing, r.team)` — a soldier can never overpaint the enemy and never damages a robot. ✓
- `world.nim:726-730, 767-796` **splasher** — `r² ≤ 4`, `paint >= 50`; charge 50 (pre-cost); iterate `locationsWithinRadiusSquared(l, 4)` in engine scan order; enemy towers take 100 with **no `else`** before the paint branch, so one splash both damages and recolours; the enemy-paint branch is gated on `l.isWithinDistanceSquared(newLoc, 2)`. ✓ (note rule 4.3, line 320-325)
- `world.nim:732-737, 798-814` **mopper single** — `r² ≤ 2`, target passable (no wall, no ruin); charge 30; an enemy **robot** on the tile loses 10 and the mopper gains 5; the tile becomes **bare** (`PaintNone`) if it does not carry this team's colour. ✓ (rule 4.4)
- `world.nim:832-857` **mop swing** — action-ready, mopper, one of N/S/E/W, the adjacent tile on the map; charge 20; six offsets from `MopSwingDx/Dy[dirIdx]`, off-map skipped, only enemy **robots** (`target.kind.isRobotType()`) lose 5; nothing repainted. ✓ (rule 4.5)
- `towers.nim:51-107` **tower attack** — `canTowerAttackSingle`/`canTowerAttackArea` check **only** the per-turn flags and range; there is **no** `isActionReady` call and **no** cooldown is charged, matching the note's rule 4.6 (line 335-337). Single damage is `attackStrength + w.damageIncrease[team]`; AoE is `aoeAttackStrength + javaRound(damageIncrease * DefenseAttackBuffAoeEffectiveness / 100.0)` — the constant is 0, so +0, and the expression is retained as the engine's. `attackMoneyBonus` is paid once per landing shot on **both** paths (`:76-77` and `:104-105`), so a defense tower that lands both earns twice. ✓
  - *Observed implementation detail, not a divergence*: `doTowerAttackArea` collects victim ids in one pass (`:88-95`) and applies damage in a second (`:96-103`) with an `existsRobot` guard, where the engine damages inside the scan. Because each tile is scanned once and no unit moves during the scan, the set of victims and the damage each takes is identical; the guard only protects against a double-destroy. **Inference**, not a traced difference in outcome.
- `towers.nim:112-…` **build robot** — `r² ≤ 4`, action-ready, actor is a tower, type is a robot, **tower's own** paint ≥ `paintCost`, **team** chips ≥ `moneyCost`, tile unoccupied and passable. ✓ (rule 4.7)
- `world.nim:861-874` **mark** — robot, `r² ≤ 2`, paintable; **no cooldown, no paint cost** (note rule 4.8, divergence-from-prose #4). ✓
- Severity guess: **no finding**.

### F18 — SRP lifecycle: list order, lifetime reset on break, activation at ≥ 50, bonus per mining tower
- `world.nim:553-585` `updateResourcePatterns` walks `w.srpCentres` **in list order**, re-checks `checkResourcePattern`, drops a broken centre and sets `srpLifetimes[i] = 0` (a repaint restarts the whole 50-round clock), otherwise keeps it and increments; `srp_active` fires when the lifetime **becomes exactly** `ResourcePatternActiveDelay`.
- `world.nim:538-548` — a centre counts as active at `lifetime >= 50`; `extraResourcesFromPatterns = activeCount * 3`.
- `towers.nim:32-44` `mine` — `bonus = w.extraResourcesFromPatterns(r.team)` is added **per mining tower**: a paint tower adds `paintPerTurn + bonus` to **its own** stash (`r.addPaint`, clamped at the type's 1000 capacity), a money tower adds `moneyPerTurn + bonus` to the **team** pool.
- Design note rule 1b (lines 279-288) and §Tests item 6 (line 1665-1670): matches.
- Severity guess: **no finding**.

### F19 — Pattern tables decode to the note's four pictures
- `src/battlecode/years/bc25/constants.nim:58-61` — `ResourcePattern = 28873275`, `PaintTowerPattern = 18157905`, `MoneyTowerPattern = 15583086`, `DefenseTowerPattern = 4685252`.
- `src/battlecode/years/bc25/patterns.nim:59-71` — `getPatternBit(pattern, ddx, ddy) = (pattern shr (5*(ddx+2) + ddy+2)) and 1`; `PatternTables` is a compile-time `block:` regeneration from the ints; bit 1 → secondary (`wantedPaint`, `:85-88`).
- I decoded the four ints independently: RESOURCE `SSPSS/SPPPS/PPSPP/SPPPS/SSPSS`, PAINT `SPPPS/PSPSP/PPSPP/PSPSP/SPPPS`, MONEY `PSSSP/SSPSS/SPPPS/SSPSS/PSSSP`, DEFENSE `PPSPP/PSSSP/SSSSS/PSSSP/PPSPP` — **identical** to the note's table at design lines 253-259.
- `world.nim:501-521` — `checkPattern` skips the centre only when `isTowerPattern` (`:508`); `checkResourcePattern` passes `false` so the SRP check includes the centre. `world.nim:496-499` `isValidPatternCenter` requires `centreIsInsideBox` (2 tiles from every edge) and, for SRPs only, `areaIsPaintable` over all 25 tiles.
- Severity guess: **no finding**.

### F20 — Engine scan order and the precomputed `ceil(√r²)` table
- `world.nim:302-317` (`locationsWithinRadiusSquared`) — `x` ascending outer, `y` ascending inner, over the box `[max(cx − (ceil√r² + 1), 0) … min(cx + (ceil√r² + 1), w−1)]`, keeping tiles with `distanceSquared ≤ r²`. `CeilSqrtTable` (`units.nim:107`) is an 81-entry compile-time table, so no `sqrt` call exists in the round loop.
- Design note §Determinism lines 855-862: matches, including the +1 box padding and the finite radius set (max 80 = `BROADCAST_RADIUS_SQUARED`, and the index is clamped at `CeilSqrtTable.high` = 80).
- Severity guess: **no finding**.

### F21 — End-of-turn bill: territory, crowding (towers counted), the 20 HP at zero
- `world.nim:1006-1037` — for robots only: `mopperMultiplier = 2` for `utMopper`; `allies` counts every unit within `r² ≤ 2` of the same team excluding itself using `w.getRobot(l)`, and towers **do** occupy `w.occupant` (`spawnRobotWithId` calls `w.addRobotAt(l, r)` unconditionally at `world.nim:611`), so towers are counted. Bare ground: `−1 × mult` then `−allies`; enemy ground: `−2 × mult` then `−2 × allies`; own ground: `−allies` only. Then `if r.paint == 0: addHealth(r, −20)` in the same turn; `roundsAlive += 1` only `if r.alive`.
- Design note rule 5 (lines 397-402) and §The game divergence 3 (lines 240-243): matches.
- *Observed*: the bill is applied as two separate `addPaint` calls rather than one. Because `addPaint` clamps at 0 (`world.nim:398-408`), the resulting stash is identical either way.
- Severity guess: **no finding**.

### F22 — `DecisionOps` is checked before a primitive and never inside one
- `world.nim:363-375` — `budgetFor` returns 1750 (robots) / 2000 (towers) from `constants.nim:119-120`; `spend(n)` returns `false` and charges nothing when `opsLeft < n`.
- `world.nim:452-481` `connectedByPaint` — the BFS charges 1 credit per node expanded when an `actor` is supplied (`:478`), but the charge is `discard`ed: the loop's continuation does **not** depend on the budget, so the BFS runs to completion and the answer is the engine's either way. The BFS terminates: each tile is marked in `seen` before expansion, so at most `w*h` expansions and at most `4*w*h` queue pushes.
- `world.nim:501-513` `checkPattern` — same pattern: `discard actor.spend(1)` per tile, never a break.
- Design note §The chassis, and the bytecode divergence (lines 896-902): matches the stated property exactly.
- Severity guess: **no finding**.

### F23 — Every wall-clock wait in the match path is bounded
- `rules.nim:416-426` (`playGame`) — `while w.running and w.currentRound < maxRounds`, with a monotonic `budgetSeconds` guard tested every 32 rounds (`(w.currentRound and 0x1F) == 0`); on expiry the game is marked `aborted` and `break`s, `endReason = "abandoned"`, `winnerSlot = -1`.
- `decide.nim:633,656,691` — the doctrine phase's three bounds (see F8).
- `src/battlecode/server.nim` — `connectTimeoutMs` (25 000 for bc25) is the seat-connect bound; unchanged by this diff (the only bc25 hunk in `server.nim` is `scoresFor(games, config.year)` at `:426`).
- I found no unbounded `while true` in `src/battlecode/years/bc25/`: `grep -n 'while true' src/battlecode/years/bc25/**` returns nothing.
- Worst case per the note (§Match shape, lines 451-461): 30 + 45 + 340 + 30 = 445 s ≤ 720 s (60 % of 1200). The configured values in the manifest (`perGameBudgetSeconds 110`, `matchBudgetSeconds 340`, `doctrineBudgetMs 45000`, `connectTimeoutMs 25000`) reproduce that arithmetic.
- Severity guess: **no finding**.

## D. Replay writer and re-derivation

### F24 — Nothing per-round is stored; the viewer's readouts come from the same re-derivation
- `tests/test_bc25_replay.nim:122-133` — asserts the written document contains none of `paint_array`, `marker_array`, `colour_array`, `board`, `grid`, `towers_by_round`, `per_round`, `tile_array`; asserts `text.len < 200_000`; asserts the only per-round bytes are `games[0].hash_chain_rounds` of length exactly `rounds × 16`.
- `tests/test_bc25_replay.nim:135-157` — builds a `newDeriver(parseReplay(text))`, advances every frame, asserts `frames == 300` and `d.mismatchRound == -1` (frame-by-frame hash agreement), then builds the chrome document **off `d.session`** and asserts `bc25_coverage`, `bc25_towers`, `bc25_econ`, `bc25_war` are present, that `bc25_coverage.clans[0].tiles > 0` ("coverage is re-derived, not stored") and that `bc25_coverage.area_without_walls` equals a freshly constructed `newWorld(loadMap("Filter"), 300).areaWithoutWalls`.
- `tests/test_bc25_replay.nim:83-97` — record → re-derive over four configurations, asserting `rederives(text) == -1` for each and that ≥ 2 distinct `end_reason` values were exercised.
- `tests/test_bc25_replay.nim:99-105` — the wall-clock stop rides one record, `plan.abandonAfter`, and survives the round trip.
- Checklist item 2 ("replaying the recorded events through the sim reproduces the recorded per-tick state frame by frame, and the viewer derives its display from that same re-derivation; a test asserts it"): satisfied by the code above.
- Severity guess: **no finding**.

### F25 — `GameVersion` bumped to GV08 and the compatibility list extended, not reset
- `src/battlecode/sim_types.nim:16` `GameVersion* = "GV08"`; `:22-42` a prepend-only changelog entry naming bc25 and stating bc26/bc20/bc21/bc24 semantics are unchanged; `:129-130` `ReplayCompatibleGameVersions* = ["GV04","GV05","GV06","GV07", GameVersion]`.
- Design note §Determinism lines 880-884 and §Packaging line 1498: matches.
- Severity guess: **no finding**.

## E. Viewer — the bc25 block, chrome provenance, transport rules

### F26 — Nine of the eleven bc25 scrubber-beat kinds can never be emitted; the killfeed carries two lines a match
- `src/battlecode/broadcast.nim:129-203` (`beatsFor`) — the **only** producer of `s.beats`. Its `case e.kind` at `:135-151` has arms for `backstab`, `king_built`, `cat_fed`, `game_start`, `game_end`, `game_abandoned`, `flood_stage`, `first_build`, `wall_closed`, `rush_launched`, `drone_water_drop`, `hq_buried`, `hq_drowned`, `doctrine_received`, `doctrine_fallback`, and `else: ""` at `:151`; `:152` `if kind.len == 0: continue`. **No arm exists for any bc25 event kind** — `first_action`, `tower_built`, `tower_upgraded`, `tower_lost`, `srp_completed`, `srp_active`, `srp_broken`, `coverage`, `starved`, `rout`. (`doctrine_*` are mapped but then filtered out by `:134` `if e.game < 0 … continue`, because pre-match events carry `game = -1`.)
- Evidence from the committed fixture: `tests/fixtures/replay-bc25.json` carries 32 events — `coverage`×6, `tower_built`×5, `tower_upgraded`×5, `srp_completed`×5, `starved`×4, `srp_active`×3, `first_action`×2, `game_start`×1, `game_end`×1. Through `beatsFor` exactly **two** of those 32 produce a beat (`game_start` → `game`, `game_end` → `end`).
- Downstream: `client/replay_broadcast.html:4445-4466` `buildBc25BeatButtons` builds one `<button>` per entry of `s.beats`; `:4579-4593` `renderFeed` builds the `#killfeed` lines **from the same `s.beats`** and slices the last 8. With two beats, a whole bc25 match draws two scrubber markers and a two-line killfeed.
- `client/replay_broadcast.html:3193-3203` ships CSS for all eleven kinds (`doctrine`, `game`, `build`, `tower`, `upgrade`, `siege`, `srp`, `coverage`, `starve`, `rout`, `end`), each scoped to `html[data-year="bc25"]`; `tests/test_viewer.nim:837-846` asserts the eleven CSS rules exist but does **not** assert that a bc25 replay emits any of them.
- Design note §Event vocabulary (lines 1188-1208) assigns a `beat` column to `first_action` (`build`), `tower_built` (`tower`), `tower_upgraded` (`upgrade`), `tower_lost` (`siege`), `srp_completed`/`srp_active`/`srp_broken` (`srp`), `coverage` (`coverage`), `starved` (`starve`), `rout` (`rout`), `game_end`/`game_abandoned` (`end`), `game_start` (`game`), `doctrine_received`/`doctrine_fallback` (`doctrine`), and says each is "drawn as … beat + feed". §Transport rules (lines 1324-1332) says the scrubber beats are labelled buttons "with CSS for **every kind emitted** … all eleven". §Readouts (line 1400) says `#killfeed` shows "the event beats, revealed as the playhead reaches them".
- Scope note: `beatsFor` itself is **not modified** by the bc25 diff (`git diff 5e7c8b78..eb33a8d2 -- src/battlecode/broadcast.nim` has hunks only at `@@ -23,6 +23,11 @@`, `@@ -675,6 +680,220 @@` and `@@ -742,3 +961,6 @@`, all outside `beatsFor`). The bc25 change added the eleven CSS rules, the beat builder and a test asserting the CSS is present, but no emission path. I did not check whether bc24 has the same gap.
- Severity guess: **blocking-candidate** (category: static-viewer / legibility — the design note's beat + feed vocabulary is unreachable). I did not run the viewer; this is traced from the code and the committed fixture, not from a browser run.

### F27 — Chrome provenance: `chrome_common.js` and `broadcast_core.js` are byte-identical to the starter; the page is the starter's with a banner-marked append
- `diff client/chrome_common.js /workspace/starters/coworld-ctf/client/chrome_common.js` → no output (byte-identical). Same for `client/broadcast_core.js`. Neither file appears in the bc25 diff.
- `client/replay_broadcast.html` gains **501 lines** on a base of ~4 700 (`git diff --stat`: `504 ++++++++++++++++++++++++++++++++++++++++++-`, 501 insertions / 3 deletions). This is an append, not a rewrite; the three deleted lines are the three guard-condition edits at `:5031`, `:5164`, `:5179` (`isBc25` added to the `!isBc20 && !isBc21 && !isBc24` guards and `bc25-towers`/`bc25-econ` added to the `--statrail` id list).
- The block sits under the banner comment `BC25 additions to the inherited cogame-battlecode chrome` (`client/replay_broadcast.html:4371-4383`), asserted by `tests/test_viewer.nim:786-788`.
- `tests/test_viewer.nim:793-800` asserts all twenty earlier-year ids (`coopchip`, `bars`, `gamechips`, `econ`, `doctrines`, the five bc20, five bc21 and five bc24 ids) are still present.
- Design note §All four viewer files come from ONE starter (lines 1226-1243): matches.
- Severity guess: **no finding**.

### F28 — Transport rules (a)–(d)
- (a) `client/replay_broadcast.html:5015-5042` — `relayout()` takes `var root = document.documentElement.style` and sets `--hudscale`, `--topband`, `--band` (from `$('transport').offsetHeight`) and `--statrail` on it, iterating a three-pass fixed point. All four land on `:root`, not on `#stage`.
- (b) The bc25 boxes ride the band: `:3129` `#bc25-towers { bottom: calc(var(--band, 0px) + 76px); }`, `:3130` `#bc25-econ { bottom: calc(var(--band, 0px) + 8px); }`, `:3220` the 640 px override `calc(var(--band, 0px) + 66px)`; `#bc25-coverage` is top-anchored (`:3089` `top: 6px`), `#bc25-doctrines` is anchored to the **top** band (`:3153` `top: calc(var(--topband, 0px) + 10px); bottom: auto`). Nothing fixed-positioned sits inside the band.
- (c) `:1847-1869` `#endcard { top: var(--topband, 0px); bottom: var(--band, 0px); display: none }` and `:1870` `#endcard.on { display: flex }` — shown with the class its own rule uses. `:4786-4789` `function seek(frac) { dismissEndcard(); send('s:' + …) }` — **every** seek dismisses it, and `client/replay_broadcast.html:4728-4736` hands `dismissEndcard` and `seek` to the bc25 block through `Bc25Block.attach`, so the bc25 beat buttons seek through the same `api.seek` (`:4459-4462`).
- (d) Beats are `<button type="button">` with `aria-label` and `title` (`:4450-4459`), and CSS exists for all eleven kinds scoped to `html[data-year="bc25"]` (`:3193-3203`). See F26 for which of those kinds are reachable.
- `:4445` `buildBc25BeatButtons` is a distinct name; `tests/test_viewer.nim:806-814` asserts each of `buildBeatButtons`, `buildBc20BeatButtons`, `buildBc21BeatButtons`, `buildBc24BeatButtons` occurs exactly once and that `buildBc25BeatButtons` is defined exactly once.
- Design note §Transport rules lines 1316-1335: matches, with the F26 caveat.
- Severity guess: **no finding** (beyond F26).

### F29 — `#viewpanel` kept, as the note requires
- `tests/test_viewer.nim:801-803` asserts `"viewpanel"` is in the page; the id and its zoom/minimap wiring are inherited unchanged.
- Design note §Zoom: KEEP `#viewpanel` (lines 1304-1312): the bc25 pool tops out at 50×30 at 16 px a tile = 800 px, wider than the 360 px frame, so the panel stays. Consistent — and this is why `--strict-text-bounds` is legitimately dropped on the bc25 replay run (checklist item 15's pannable-board case).
- Severity guess: **no finding**.

### F30 — 360 px legibility
- `client/replay_broadcast.html:2571` `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }` — the exact rule checklist item 11 names, unchanged from the starter.
- `:2647` and `:3205` are the two `@media (max-width: 640px)` blocks; the bc25 one (`:3205-3222`) drops `.towin`, `.lbl` and `.pending` to glyphs, shrinks the coverage bar to 74 px and re-anchors `#bc25-towers`, with a measured comment ("316 px inside the 344 px the frame leaves it").
- Design note §Readouts, and 360 px (lines 1382-1387): matches.
- Severity guess: **no finding**.

### F31 — Load signalling, emscripten link flags and the bootstrap agree; no lobby to skip
- `replay-viewer/config.nims:42-54` — the `passL` block carries `-O2`, `-s ALLOW_MEMORY_GROWTH`, `-s ABORTING_MALLOC=1`, `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `--preload-file {rootDir}/data@data` and an unchanged `EXPORTED_FUNCTIONS` list. **No `-s MODULARIZE=1` and no `-s EXPORT_NAME`.**
- `replay-viewer/static_replay_worker.js:209-221` — `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = function () { runtimeReady = true; start(); }`, `self.Module = Module`. A global-`Module` + `onRuntimeInitialized` bootstrap against a **non**-`MODULARIZE` build: the two agree, which is the cogame-lantern case not being reproduced here.
- `replay-viewer/static_replay.js:180` sets `data-replay-loaded` on `document.documentElement`; `:14-20` sets `data-replay-error` with the message on failure.
- **No file under `replay-viewer/` is touched by the bc25 diff** (`git diff --stat` lists only `client/replay_broadcast.html` under the viewer paths). `replay-viewer/bc_replay.nim:17,70-71,90` already dispatches on the replay header's `year` through `years/dispatch.nim` and picks the atlas from `yearSpec(doc.year).atlas`, so bc25 needs no edit there — consistent with the note (design line 1236).
- Lobby: this replay format has no lobby frames. `src/battlecode/broadcast.nim:861-862` (and the four sibling year builders at `:323`, `:451`, `:644`, `:910`) emit `"st": 0` and `"lob": 0`, and `tests/test_bc25_replay.nim:141-143` asserts a 300-round recording yields exactly 300 frames, so frame 0 is round 1. The checklist's "playback opens at `gameStarts[0].tick`" case cannot arise here. **Observed** from the code; I did not run the viewer.
- Severity guess: **no finding**.

## F. CI, docker-smoke, the parity oracle, and the tests

### F32 — CI is green on `main` at the reviewed sha, with every job succeeding
- `gh run list -R Metta-AI/cogame-battlecode --branch main -w ci.yml`: run **34181338414**, "Merge pull request #5 from Metta-AI/bc25-year-module", conclusion **success**, 24m40s, 2026-09-08T02:48:39Z.
- Job conclusions on that run: `test` success, `docker-smoke` success, `wasm-viewer` success, `parity-oracle` success, `parity-oracle-bc20/bc21/bc24/bc25` all success.
- `wasm-viewer` step list on that run includes `Load the bundle in a real browser (ALL FIVE years' replays)` = **success**, `Smoke the emitted wasm module under node (all five years)` = success, `Render the full-cap doctrine-text fixture` = success. The browser step is present, not commented out, and `.github/workflows/ci.yml:1895` has `needs: docker-smoke`. No `continue-on-error` on it.
- `grep -c 'SEAT-COUNT FAIL' <docker-smoke job log>` → **0** over 2 503 log lines.
- No test was disabled, skipped, or loosened: `git diff 5e7c8b78..eb33a8d2 -- tests/` removes eleven lines, all of them four-year counter assertions replaced by five-year ones (`year.enum` 4→5 entries, `variants.len` 4→5, `docs["pages"].len` 6→7, `policies.len` 16→20, `prompts` 8→10, `scripted` 8→10, `owned` 4→5, the replay list and `YEARS` array). No `skip`/`xfail`/`--skip` added, no test file removed, no tolerance widened.
- Severity guess: **no finding**.

### F33 — bc25 viewer smoke ran and loaded; the CI replay's feed is one line
- `wasm-viewer` log, bc25 replay: `{"loaded":true,"ms":309,"clock":"0:10 GAME 1 OF 1 — DEFAULTSMALL doctrines","scorebug":"CLAN ASH Clan Ash · Paint it and hold it. 84 … CLAN BASIL … 15","feed_lines":1}`, `scrub selector: #scrub`, `endcard after the 100% seek: shown=true text=CLAN ASH — CLAN ASH`, at `--timeout 120 --soak 15 --killfeed-overlap`.
- `Smoke the emitted wasm module under node`: `{"loaded":true,"game_version":"GV08","sim_sources_stamp":"f536d704…","frames":200,"mismatch_round":-1}` for each of the five replays (and the committed bc25 fixture).
- `feed_lines: 1` on the bc25 replay is consistent with F26 (bc24 also reports 1; bc26/bc20/bc21 report 3/8/7). It is corroborating evidence, not the proof — the proof is the `beatsFor` case at `broadcast.nim:135-151`.
- Severity guess: **no finding** on its own; feeds into F26.

### F34 — `docker-smoke`'s bc25 `tiles_painted` floor is **below** the design note's stated minimum
- `.github/workflows/ci.yml:1752-1754` — `SMOKE_REQUIRE_STATS: {"robots_built":20,"tiles_painted":15,"chips_spent":8000,"paint_spent":3000}`.
- Design note §docker-smoke job (line 1987): `{"robots_built":4,"tiles_painted":150,"chips_spent":500,"paint_spent":400}`, and line 2003: "sets the committed floors at roughly half the weak seat's measured value — **never below this note's numbers**".
- Observed: three of the four floors are **above** the note (20 > 4, 8000 > 500, 3000 > 400). `tiles_painted: 15` is **ten times below** the note's 150. `ci.yml:1722-1738` documents the reason at length and cites the measurement (run 34172749340: seat 0 spaark 254 tiles, seat 1 examplefuncsplayer25 **37** tiles over the 600-round smoke; the note's 150 was derived from whole 2000-round games where the mirror paints 46-218).
- Same shape in the across-the-pair step: `.github/workflows/ci.yml:1793` `test "${painted}" -ge 120`, where the note (line 1996) says `>= 200`. The measured value on the run was **241**. `towers_built >= 1` and `towers_upgraded >= 1` match the note exactly, and the run reported `towers built=6 towers upgraded=9 squares painted=241`.
- Severity guess: **advisory** — a documented, measured deviation from a note clause that says "never below", not a loosened test (the value was never higher in this repo's history).

### F35 — The parity oracle job: four bots × six maps, empty ledger, all tiers present
- `.github/workflows/ci.yml:1192` `parity-oracle-bc25:`; `:1252-1261` the jar is fetched from `jar.lock`'s URL and `build_oracle.sh` sha256-verifies it; `:1266-1281` no `SPEC_VERSION` assertion (the note's line 1821-1824 reason, and the workflow's own comment says so); `:1301` the constants cross-check against the jar's classes; `:1331-1342` `data/bc25/tables.json` is byte-diffed against `/tmp/oracle25/tables.json` (Tier B); `:1348-1356` four Nim trace binaries built (`-d:bc25Scenario`, `+ScenarioPaint`, `+ScenarioWipe`); `:1365-1371` the four bots (`examplefuncsplayer`, `bc25scenario`, `bc25scenariopaint`, `bc25scenariowipe`); `:1412-1417` `parity_tiers_bc25.py --ledger tools/ci/parity_ledger_bc25.json`; `:1437-1449` the "the paths really fired" assertions off the **Java** trace.
- `tools/ci/parity_ledger_bc25.json` is 4 lines. Its content:
`{"note": "THE ACCEPTED-DIVERGENCE LEDGER FOR bc25, AND IT IS EMPTY. …", "entries": []}` — `entries` is an **empty array**. The note field records the measurement: all eighteen trace pairs bit-exact for whole 2000-round games, bytecode peak 14 % (example bot) / 35 % (scenario bot), zero mid-turn cut-offs.
- Design note §parity-oracle-bc25 (lines 1802-1954) and line 1936 ("the phase-30 exit condition is that Tiers A, A′ and B pass with an EMPTY ledger"). The job is green on the reviewed sha (F32).
- Severity guess: **no finding**.

### F36 — Renderer fixture: bc25 row present and self-checking, but `canvas_text` is 0 on it
- `tools/ci/renderer_fixture.html:70` `var YEARS = ['bc26', 'bc20', 'bc21', 'bc24', 'bc25'];`; `:309-345` the bc25 row builds `#bc25-towers`, `#bc25-econ` and `#bc25-doctrines-body` rows with full-cap `notes` and `motto`; `:506-517` the fixture asserts its own strings are still at their caps (`.plate-sub` rune length `== len(NAMES[0]) + 3 + MAX_MOTTO_RUNES`, and `#<year>-doctrines .dline i` text `=== notes`) — the "one quietly shortened remark leaves this fixture passing while testing nothing" guard.
- `tests/test_viewer.nim:404-414` closes the vacuity hole for bc25 specifically: it asserts the bc25 doctrine rows use `.dline`/`.dname` (the diff's own comment records that bc25 first shipped `.clan`/`<b>`, which made the fixture's `.dline i` selector find nothing).
- `.github/workflows/ci.yml:2139-2165` runs it under `viewer_smoke.mjs --strict-text-bounds` against a served copy with the page's own CSS extracted at run time.
- **Observed limit**: the CI log for that step reads `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`. Checklist item 15 states "`total: 0` means the check covered nothing … and is not evidence of anything." The fixture is a **DOM** page — it has no canvas and does not load a `client/renderer.js` (this repo has none; the board renderer is `src/battlecode/render.nim`, compiled to wasm). Its actual gate is its own `problem()` DOM-rect measurement, which sets `data-replay-error` (`renderer_fixture.html:79-81, 143-146, 526-533`) and so does fail the harness. So the fixture *does* gate, but not via `canvas_text`, and `--strict-text-bounds` on that step measures nothing.
- Design note §wasm-viewer job (lines 2023-2026) describes the fixture exactly as shipped ("in the page's own CSS extracted from `client/replay_broadcast.html` at run time"). The divergence is from the **checklist's** wording ("loads the real `client/renderer.js`"), not from the note.
- Severity guess: **advisory** (I am reporting the observed `total: 0`; whether the DOM-rect gate satisfies checklist item 15 is the judge's call).

### F37 — Test coverage against the note's §Tests list
Traced by opening each file and matching it to the note's numbered item:
- `tests/test_bc25_cooldown.nim` (151 lines) — item 1. `tests/test_bc25_paint.nim` (103) — item 2. `tests/test_bc25_units.nim` (175) — item 3. `tests/test_bc25_towers.nim` (171) — item 4. `tests/test_bc25_patterns.nim` (148) — item 5. `tests/test_bc25_srp.nim` (134) — item 6. `tests/test_bc25_penalties.nim` (113) — item 7. `tests/test_bc25_comms.nim` (130) — item 8. `tests/test_bc25_execorder.nim` (102) — item 9. `tests/test_bc25_endladder.nim` (133) — item 10. `tests/test_bc25_scoring.nim` (179) — item 11. `tests/test_bc25_sheet.nim` (197) — item 12. `tests/test_bc25_sensing.nim` (109) — item 13. `tests/test_bc25_maps.nim` (188) — item 14. `tests/test_bc25_survival.nim` (135) — item 15. `tests/test_bc25_knobs.nim` (250) — item 16. `tests/test_bc25_baselines.nim` (127) — item 17. `tests/test_bc25_perf.nim` (42) — item 18. `tests/test_determinism.nim` (+16) — item 19. `tests/test_bc25_replay.nim` (207) — item 20. `tests/test_manifest.nim` (+40/-…) — item 21. `tests/test_viewer.nim` (+107) — item 22. `tests/test_constants.nim` (141, new) — item 23.
- All 23 numbered items have a file. Every one of the twenty new test files is an addition; none replaces an existing file.
- Severity guess: **no finding**.

## G. Baselines, knobs, name spaces, docs and licensing

### F38 — Scripted baselines: legality asserted, weak floor pinned, strong chassis wins 6/6
- `tests/test_bc25_baselines.nim:12-28` — the `PLAYER_SCRIPTED` resolution table: `awu`/`spaark`/`nonsense`/`""` → `blSpaark`; `scaffold`/`examplefuncsplayer`/`examplefuncsplayer25`/`example` → `blExamplefuncsplayer25`; `defaultBaselineFor("bc25") == blSpaark`; a chassis name belonging to another year (`scGoneSharkin`) maps to `ckSpaark`.
- `:53-86` (b) — three chassis pairings × two maps × 600 rounds, asserting `w.refusedActions == 0` ("NO illegal order was ever emitted" — every `do*` re-checks its own `can*` and increments `refusedActions` on a no-op, e.g. `world.nim:707-709, 820-822, 843-845`), `w.opsUsedPeak <= DecisionOpsRobot`, no unit out of paint/HP bounds, chips never negative, neither clan over the 25-tower cap.
- `:88-104` (c) — `examplefuncsplayer25` builds robots, paints tiles and mop-swings, and is pinned to **never** build a splasher, complete an SRP or upgrade a tower ("it may not gain behaviour").
- `:106-126` (d) — `spaark` beats `examplefuncsplayer25` 6/6 over 2 maps × 3 seeds, playing from both engine sides.
- `tests/test_bc25_survival.nim:52-119` — the competence gate, with committed thresholds (`MinRobotsBuilt 8`, `MinTowersBuilt 2`, `MinTowersUpgraded 2`, `MinCoveragePermille 120`, `MinChipsEarned 90 000`, `MinPaintMined 40 000`, `MaxStarvedPercent 25`, `MinSrpRoundsActive 50`), each annotated with the note's floor and the measured healthy/broken ranges (`:23-32`). Every committed threshold is **at or above** the note's floor.
- `:106-131` — the inverted control: the same file compiled `-d:bc25BrokenChassis` is run as a subprocess and the parent asserts it exits 0 only when the gate came back **red**; if `nim` is not on PATH the test **fails** rather than skipping.
- Design note §Tests items 15 and 17 (lines 1715-1765): matches, including the note's own allowance that phase 20 measures and re-tunes.
- Severity guess: **no finding**.

### F39 — No test asserts `results.reason == "complete"` for a bc25 episode in the Nim suite; `docker_smoke.sh` does
- Searching `tests/` for `"complete"` / `epComplete`: `tests/test_determinism.nim:93,108,140` assert `epComplete` for bc26 episodes; **no bc25 test asserts the episode reason**. `tests/test_bc25_baselines.nim:70-75` asserts the *game* ended on a real end condition (`roundsPlayed >= 600 or paint_enough_area or destroy_all_units`), which is the equivalent claim at game level, not episode level.
- `tools/ci/docker_smoke.sh:443-446` — `if results["reason"] != "complete": … f"reason was {results['reason']!r}"` and exits non-zero. The bc25 episode runs through it (`.github/workflows/ci.yml:1739-1758`) and the job is green (F32).
- Checklist item 7 asks for "a test [that] runs an all-scripted episode to the natural end, asserts `results.reason == "complete"`". The `docker-smoke` script does exactly this against the real image; no in-tree Nim test does.
- Severity guess: **advisory** (the assertion exists, in `docker_smoke.sh` rather than in `tests/`).

### F40 — No committed grid harness; the baseline's tuning evidence is measurement comments in the test headers
- Searched `tools/` (43 entries listed) and `tests/` for a tuning/grid harness: none exists. The tuning record is `tests/test_bc25_survival.nim:23-32` (healthy-mirror and broken-control ranges, dated 2026-09-07, `-d:release`) and `tests/test_bc25_knobs.nim:8-62` (per-knob measured deltas over "the SUM over both seats of six games: `Justice`, `Filter` (small) and `Portal` (mixed) × seeds 1 and 2, `-d:release`").
- Checklist item 7's second half: "The baseline's parameters were tuned with a grid harness, not guessed." The measurements are recorded and dated but the harness that produced them is not committed, so I cannot re-run them from the tree.
- Severity guess: **advisory** — and see "Could not determine" below.

### F41 — Six of the ten knob-teeth assertions substitute a different statistic than the note's table
- `tests/test_bc25_knobs.nim:8-62` — the header records, per knob, the note's asked-for statistic, the measured value, and the substitute:
  - `opening` — the note's "robots built by round 400 UP ≥ 40 %" measured **down**; substituted with chips-spent-on-towers-down. The note's second statistic (towers built by round 400 down ≥ 2) is kept and "holds hugely (34 → 8)".
  - `srp_priority` — note ≥ 25 % down on tower chips; measured −20.4 %; **committed threshold 10 %**.
  - `ruin_claim_radius` — note ≥ 50 % mean-distance up; measured +19 %; **committed threshold 10 %**.
  - `paint_reserve_floor` — note's "tiles painted DOWN ≥ 10 %" measured **up**; substituted with paint-transferred-up. The note's first statistic (robot-rounds at zero paint down) holds at −58 %.
  - `mop_enemy_paint` — note's "paint transferred DOWN ≥ 50 %" measured −5 %; substituted with mop-swings-down.
  - `defense_tower_chokes` — note's "enemy robots killed by towers UP ≥ 20 %" measured **down**; substituted with the clan's own tower-damage ledger. The note's first statistic (defense towers built up ≥ 2, from a provable zero on `never`) is kept.
  - `splash_targets` — note's +40 % measured +190 %, so the note's number is kept.
- Design note §Tests item 16 (lines 1735-1751): the note explicitly says "Thresholds live in one table so tuning is a one-line change, and the header records every substituted statistic (the bc21 r1-F6 fix)". The recording obligation is met in full; two thresholds (`srp_priority` 25 %→10 %, `ruin_claim_radius` 50 %→10 %) are **numerically below the note's table** with the measurement given as the reason.
- Severity guess: **advisory**.

### F42 — Both name spaces present
- `src/battlecode/decide.nim:447-473` (`briefFor`) — the observation payload carries `"alias": aliasFor(slot)` and `"opponent_alias": aliasFor(1 - slot)` and **no** `names` key; the docstring at `:450-453` states real player names are never in it. `mapCardFor` supplies only map facts.
- `src/battlecode/broadcast.nim:881-882` (bc25 chrome) — `"aliases": [AliasA, AliasB]` **and** `"names": [doc.names[0], doc.names[1]]`, so the viewer has both. `client/replay_broadcast.html:4562-4576` `renderDoctrines` prints `esc(seat.alias) — esc(seat.name)`; the CI viewer smoke log shows the scorebug reading `CLAN ASH Clan Ash · Paint it and hold it.` (the plate name / sub pair).
- Design note §Replay (line 1156) — `"names":["daveey","daveey-1"], // spectator-side only; agents never see these`. Matches.
- Severity guess: **no finding**.

### F43 — `docs/RULES-BC25.md`, `NOTICE` and `knobs.nim` point at the shipped layout; one arithmetic slip in a doc comment
- `src/battlecode/years/bc25/chassis/` contains exactly eleven files: `kit`, `econ`, `tower`, `soldier`, `splasher`, `mopper`, `siege`, `comms`, `spaark`, `scaffold25`, `scenario25` — the note's list at design line 806 plus `scenario25.nim`.
- `NOTICE:290-362` names `src/battlecode/years/bc25/{world,rules,units,paint,patterns,towers,comms,maps}.nim`, `constants.nim`, `data/maps/bc25/*.json`, `data/bc25/tables.json`, `chassis/scaffold25.nim` (AGPL, battlecode25 `28975a48`), `data/atlas_bc25.*` (GPL-3.0 sprites), `chassis/{spaark,kit,econ,tower,soldier,siege,comms}.nim` (erikji), `chassis/{mopper,splasher}.nim` (ecoArcGaming). Every named path exists.
- `src/battlecode/years/bc25/knobs.nim:28-35` lists the same eleven chassis files and then says "**All thirteen exist**". Eleven are listed and eleven exist; the count word is wrong.
- Design note §New and changed files, "A layout rule" (lines 832-837): no module was merged, so the three pointers are consistent; only the count word in `knobs.nim:34` is off.
- Severity guess: **advisory** (a one-word doc-comment error, no path is wrong).

## Could not determine

- **Whether `beatsFor`'s missing bc25 arms (F26) are a bc25 regression or a pre-existing gap that bc25 inherited.** `beatsFor` is untouched by this diff, and the CI `feed_lines` numbers (bc26 3, bc20 8, bc21 7, bc24 1, bc25 1) suggest bc24 is in the same position. Settling it would need the bc24 design note and its round-1 verdict, which I was not given. What is settled: on the reviewed tree, a bc25 replay emits scrubber/feed entries for `game_start` and `game_end` only, and nine of the eleven bc25 beat kinds with committed CSS are unreachable.
- **Whether the baseline was tuned with a grid harness (F40).** The measured ranges are recorded and dated in two test headers, but no harness is committed, so I could not reproduce the sweep. What would settle it: a committed tuning script, or a CI/run artefact showing the sweep's output.
- **Whether the DOM-based renderer fixture satisfies checklist item 15's "loads the real `client/renderer.js`" (F36).** This repo has no `client/renderer.js` — the board renderer is `src/battlecode/render.nim`, compiled to wasm — and the fixture's `canvas_text` is `total: 0`, which the checklist says "is not evidence of anything". The fixture does gate, via its own DOM-rect `problem()` check setting `data-replay-error`. This is a checklist-interpretation question, not a code question.
- **The `--killfeed-overlap` gate's negative control.** Design note §killfeed rule item 3 (lines 1300-1302) requires the gate's own self-test to break the rule and assert the gate goes red. `tools/ci/viewer_smoke.mjs` is not part of the bc25 diff and I did not read it end to end; I did not locate the self-test. Settling it: read `tools/ci/viewer_smoke.mjs`'s `--killfeed-overlap` implementation and its self-test, and cite the CI step that runs it.
- **Runtime behaviour of the viewer beyond what CI reported.** I did not launch a browser. All viewer findings are traced from source plus the cited CI log lines from run 34181338414.

FINDINGS: 43
