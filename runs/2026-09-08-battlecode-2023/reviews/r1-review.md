# r1 review — 2026-09-08-battlecode-2023

Repo: Metta-AI/cogame-battlecode
Range: 6885a0625687c7caec19b879e0ea09613ebd74f0..f9b292a25 (merge of PR #6)
Checklist: /workspace/coworld-builder/prompts/30-review-loop.md (acceptance items 1–15)
Design note: runs/2026-09-08-battlecode-2023/design.md

**Verdict of this review: 1 blocking finding (F18 — checklist item 15, `legibility`); 10 non-blocking (F19-F28); 16 checklist areas traced and consistent (F1-F3, F5-F17); 1 note-level claim not checkable from the tree (F4).** Findings are numbered F1…F28; the `## Summary` at the end lists them by number.

## Method

Tree read at `f9b292a21d64a8253a32d671d94f292924dd3e88` (`git clone` + `git checkout f9b292a2`;
HTTPS clone worked in this sandbox). Diff read with
`git diff 6885a062..f9b292a2` (109 files: 1 add of the whole `years/bc23/` module, 22 maps,
20 new test shards, plus 14 modified shared files). Every quoted line is from that checked-out
tree; line numbers are the landed file's.

Findings are numbered F1…; each carries a category — **BLOCKING** only if it falsifies a named
item of `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15), otherwise
**non-blocking** (advisory) or **observation** (traced, consistent, recorded for the judge's
coverage).

---

## Item 1 evidence — CI green, and no test loosened

**CI.** `gh run view 34224289835 -R Metta-AI/cogame-battlecode --json ...`:

```
sha    f9b292a21d64a8253a32d671d94f292924dd3e88
branch main       workflow CI       status completed       conclusion success
jobs   test, parity-oracle, parity-oracle-bc20, parity-oracle-bc21,
       parity-oracle-bc23, parity-oracle-bc24, parity-oracle-bc25,
       docker-smoke, wasm-viewer  — all conclusion "success" (9/9)
```

**Test-file changes this run** (`git diff 6885a062..f9b292a2 -- tests/`): 22 files added, 5
modified (`test_bc25_replay.nim`, `test_constants.nim`, `test_determinism.nim`,
`test_manifest.nim`, `test_viewer.nim`). No test file deleted. Total `-15` deleted lines across
all five, every one of them traced below.

### F1 — `test_bc25_replay.nim`'s `game_version` assertion was relaxed; the relaxation matches the form bc20/bc21/bc24 already use and the re-derivation assertion is untouched (observation, not a loosening)

- Where: `tests/test_bc25_replay.nim:308-324`; comparators at `tests/test_bc20_replay.nim:337`,
  `tests/test_bc21_replay.nim:397`, `tests/test_bc24_replay.nim:380`.
- Observed. The hunk replaces
  `checkEq("at the current GameVersion", doc.gameVersion, GameVersion)` with
  ```nim
  check("at a GameVersion this build still loads",
    doc.gameVersion in ReplayCompatibleGameVersions)
  ```
  and leaves line 324 `checkEq("and it re-derives clean", rederives(text), -1)` exactly as it
  was. The three older year fixtures assert the same predicate against the same list
  (`node["game_version"].getStr() in ReplayCompatibleGameVersions`), so the bc25 fixture now
  matches its three siblings rather than being singular. `ReplayCompatibleGameVersions`
  (`src/battlecode/sim_types.nim:158-159`) is `["GV04","GV05","GV06","GV07","GV08", GameVersion]`
  with `GameVersion = "GV09"` (line 16) — extended, not reset, so the widened set is bounded by
  the compatibility list and not by "anything".
- Checklist item: 1 ("no test disabled, skipped, or loosened").
- Reading: the *stronger* assertion in that block — a full re-simulation of the committed bc25
  fixture against today's bc25 rules (`rederives(text) == -1`) — is byte-identical before and
  after. What was dropped is an equality against a string the year bump necessarily changed.
  I record it as an observation rather than a blocking loosening because the predicate is the
  repo's own pre-existing form for the same check on three other fixtures, but the judge should
  be told a `checkEq` became a `check` on a set membership: the diff *is* a widening, and the
  reason it is not a hole is external (the sibling files), not internal to the hunk.

### F2 — no other assertion was deleted, no tolerance widened, no skip added

- Where: the other four modified test files, in full.
- Observed, hunk by hunk:
  - `tests/test_manifest.nim` — every deletion is a count being raised beside a same-shaped
    assertion: `variants.len 5 → 6` (:147), `yearEnum` `[bc26,bc20,bc21,bc24,bc25]` →
    `+bc23` (:128-129), `docs["pages"].len 7 → 8` (:275-276), `policies.len 20 → 24` (:338),
    `prompts 10 → 12` / `scripted 10 → 12` / `owned 5 → 6` (:361-363), and the `end_reason`
    message text "all four years" → "all SIX years" (:116). Nothing became weaker: 6 new
    assertions were *added* at :427-447 naming the bc23 champions, their poles, their fillers
    and champion #2's owning player.
  - `tests/test_constants.nim` — +99 lines, 0 removals.
  - `tests/test_determinism.nim` — +24 lines, 0 removals.
  - `tests/test_viewer.nim` — one deletion, `"if (!isBc20 && !isBc21 && !isBc24 && !isBc25) {"`
    → `"if (!isBc20 && !isBc21 && !isBc23 && !isBc24 && !isBc25) {"` (:817-818): the asserted
    string got *longer*, i.e. the guard the page must carry got stricter.
  - No `skip`, `xfail`, `when false`, `--skip` or commented-out `check` appears in any hunk.
    `git diff ... -- tests/ | grep -nE '^\+.*(skip|xfail|when false|disable)'` returns three
    hits and all three are prose in a doc comment about the engine's own `existsRobot` skip
    (`tests/test_bc23_execorder.nim:1018,1083,1085` of the diff) — no test-runner skip.
- Checklist item: 1. **Not falsified** by anything I could find in the diff.

---

## Manifest, version stamp, policies

### F3 — manifest: every claim in the note's §Packaging table is present in the file (observation, consistent)

- Where: `coworld_manifest_template.json` (read whole via `json.load`).
- Observed:
  - Six variants, `["bc26","bc20","bc21","bc24","bc25","bc23"]`; **every one** carries
    `game_config.num_agents = 2` and **none** carries `num_agents` at variant top level.
  - `variants[bc23].game_config` = `year bc23, pool mixed, gamesPerMatch 3, seed 0,
    maxRounds 2000, num_agents 2, attempt1Ms 20000, retryMs 12000, doctrineBudgetMs 45000,
    perGameBudgetSeconds 110, matchBudgetSeconds 340, connectTimeoutMs 25000,
    players [Clan Ash, Clan Basil]` — field for field the note's variant row (design.md:1677).
  - `certification.game_config.year == "bc26"`, `num_agents == 2`,
    `certification.players == [awu, scaffold]` (len 2 == num_agents),
    `certification.game_config.players` len 2. The cert block is **unchanged** by the diff
    (`git diff` shows no hunk inside `"certification"`).
  - `player[]` is still exactly `[awu, scaffold]`; only the two `description` strings were
    extended with ", lemonade on bc23" / ", examplefuncsplayer23 on bc23" — which is precisely
    what design.md:1648-1650 asks for, and no year-specific runnable was added.
  - `game.replay_viewer == {"bundle": "static-replay-viewer"}`; `game.protocols` has **both**
    `player` and `global`; `game.docs.readme` is a `{type,value}` object and `pages` is eight
    entries with `rules-bc23.md` inserted before `replay.md` — matching design.md:1643-1647.
  - `config_schema.properties.year.enum == ["bc26","bc20","bc21","bc24","bc25","bc23"]`
    (appended, no index moved); `end_reason` enum gained exactly the six bc23 values and neither
    `resignation` nor `destroy_all_units`.
- Checklist items: 3, 6, 10 — **all satisfied as read**.
- Untested from the sandbox: `coworld validate_upload_manifest` (the CLI is not installed here);
  `tests/test_manifest.nim:...` calls it and the `test` job is green.

### F4 — the coworld version 0.5.0 → 0.6.0 is not a tree fact and cannot be verified here

- Where: `.github/workflows/coworld-release.yml:28-29,114-123` — `version` is a
  `workflow_dispatch` **input** validated against `MAJOR.MINOR.PATCH` at release time and
  written to `release-result/version`; there is no version constant in
  `coworld_manifest_template.json` (`json.load(...)["version"]` is absent) and
  `grep -rn '0\.6\.0'` over the tree matches only `docs/plans/*-design.md`.
- Design note: design.md:79,146,1707-1708 ("This run ships 0.6.0").
- Reading: this is a phase-40 dispatch value, not something the reviewed sha can carry. Not a
  checklist item; recorded so the judge does not look for it in the tree.

### F5 — `tools/ci/policies.json`: 24 entries, 12 `PLAYER_PROMPT`, 12 `PLAYER_SCRIPTED`, bc23 champion #2 carries the required player id (observation, consistent)

- Where: `tools/ci/policies.json` entries 20-23.
- Observed: `20 battlecode-bc23-duel` (PLAYER_PROMPT, no `player`),
  `21 battlecode-bc23-alchemist` (PLAYER_PROMPT, `"player":
  "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `22 battlecode-lemonade`
  (`PLAYER_SCRIPTED=lemonade`), `23 battlecode-examplefuncsplayer23`
  (`PLAYER_SCRIPTED=examplefuncsplayer23`). Every entry's `image` is
  `cogame-battlecode-player:latest` (the **player** service's image) and `run` is
  `/bin/battlecode-player`. Champion #2 is the second `PLAYER_PROMPT` entry of the bc23 block,
  which is the position checklist 12 names.
- Placeholder gate (checklist 12, run verbatim):
  `grep -n '<slug>\|<IMAGE>\|<SEATS>' ci.yml coworld-release.yml coworld-submit.yml
  docker_smoke.sh policies.json` → **no match, exit 0**.
- Release order (checklist 12), read from the unchanged `coworld-release.yml`:
  `Build the Coworld manifest` (:168) → `Certify locally` (:182) → `Upload the policies` (:225)
  → `Upload the Coworld` (:323) → `Put the Coworld secret` (:419). In that order.
  `tools/ci/docker_smoke.sh`, `tools/build_replay_viewer.sh`, `tools/ci/viewer_smoke.mjs` are
  all present and `-rwxr-xr-x`.

### F6 — `GameVersion` GV08 → GV09 with `ReplayCompatibleGameVersions` extended, never reset (observation, consistent)

- Where: `src/battlecode/sim_types.nim:16` (`GameVersion* = "GV09"`), `:158-159`
  (`ReplayCompatibleGameVersions* = ["GV04","GV05","GV06","GV07","GV08", GameVersion]`),
  `:18-45` (the prepended GV09 changelog entry, above the untouched GV08 entry).
- Observed: before the diff the list was `["GV04","GV05","GV06","GV07", GameVersion]` with
  `GameVersion = "GV08"`, i.e. GV08 was carried *by* the `GameVersion` slot. The diff writes
  `"GV08"` in literally and leaves `GameVersion` (now GV09) in the last slot — the set strictly
  grows from `{GV04..GV08}` to `{GV04..GV09}`. `ScriptedChassis` gains `scLemonade` and
  `scExamplefuncsplayer23` (:203-204); `registry.nim:41-43` adds the one `YearSpec` row
  (`bc23`, maxRounds 2000, pools small/mixed/large, atlas `atlas_bc23`).
- Design note: design.md:78, 900, 1018-1024. Matches.

---

## The decision path, the waits, and the truncation

### F7 — the doctrine path is one parallel batch, one retry, bounded, with the fallback recorded (observation, consistent)

- Where: `src/battlecode/decide.nim:799-925` (year-neutral, **unchanged** by this diff — the
  diff only adds `Bc23Preamble` at :439-521, its `preambleFor` arm at :523, and the
  `of yBc23:` brief arm at :695-788).
- Traced, step by step:
  - `:806` `let budget = initDuration(milliseconds = max(1, config.doctrineBudgetMs))` —
    45 000 from the bc23 variant.
  - `:809-829` both seats are seeded with the year's baseline sheet **first**, so a sheet
    exists before any network call; an LLM seat with no credentials is recorded as
    `fallback = "no_credentials"` plus a `doctrine_fallback` event (checklist 8's "the
    fallback is recorded").
  - `:826 while open.len > 0 and attempt < 2` — **exactly one retry**, structurally.
  - `:828-841` the budget is re-checked before each attempt; on expiry every still-open seat
    takes `fallback = "timeout"`, gets a `doctrine_fallback`, and `open` is cleared.
  - `:845-846` `deadlineMs = if attempt == 0: config.attempt1Ms else: config.retryMs`
    (20 000 / 12 000).
  - `:847-858` **one** `RequestBatch` is built over all open seats and `:864`
    `client.curl.makeRequests(batch, max(1, deadlineMs div 1000))` issues it — one parallel
    batch per turn, not per seat. Worst case 20 s + 12 s = 32 s ≤ 45 s ≤ 720 s.
  - `:869-899` a reply is parsed through `parseReply(text, config.year)`; a failure records
    `doctrine_retry` with a cause in `{timeout, transport, throttled, parse}`, logs
    `will retry`, and re-opens the seat.
  - `:905-910` throttle fast-fail; `:912-925` the tail loop writes the fallback sheet plus a
    `doctrine_fallback` per still-open seat and logs `falling back`.
- The fallback sheet for a bc23 LLM seat is `baselineSheet("bc23",
  defaultBaselineFor("bc23"))` = `blLemonade` (`baselines.nim:41`), whose reply
  (`baselines.nim:179-190`) is the all-defaults sheet **character for character** the note
  prints at design.md:865-872. `tests/test_bc23_baselines.nim:27-33` asserts
  `baselineSheet == defaultSheet("bc23")`.
- Checklist items: 5 (bounded waits), 8 (tolerant parse, one retry, recorded fallback), and
  the "one parallel batch per turn" rider. Satisfied as read. One decision turn per episode
  (design.md:548), so there is no per-turn sequencing to get wrong.

### F8 — every wait in the match loop has an explicit bound (observation, consistent)

- Where: `src/battlecode/match.nim:378-406`; `src/battlecode/years/bc23/rules.nim:509-544`.
- Traced: `playMatch` takes `matchBudget = matchBudgetSeconds` (340) at `:379`, checks it
  before each game at `:384-388`, and passes
  `perGame = max(1, min(perGameBudgetSeconds, remaining))` into `playGameFor`. `rules23.playGame`
  loops `while w.running and w.currentRound < maxRounds` (`:527`) — bounded by 2000 — and
  tests the monotonic budget every 32 rounds (`:532` `(w.currentRound and 0x1F) == 0`),
  setting `aborted` and breaking. An aborted game is discarded, `plan.abandonAfter[g]` records
  the stop round (`match.nim:400`), `reason = deadline`, and `game_abandoned` is emitted.
  Inside a round, each robot's turn is bounded by `Robot.opsLeft`
  (`world.nim:91`, `world.nim:380-389 proc spend`: charged **before** each primitive, refuses
  when short, never resumed) with budgets 2000/1250/1000 (`constants.nim`, cross-checked in
  `tests/test_constants.nim:319-323` against `bytecodeLimit div 10`).
- I found no unbounded loop and no blocking read on the bc23 path. Arithmetic: 25 (connect)
  + 45 (doctrine) + 340 (match) + ~30 (write) ≈ 440 s ≤ 720 s, which is the note's 445 s
  (design.md:502-511).
- Checklist item: 5. Satisfied as read. **Untested**: that a real hosted episode lands inside
  720 s — that needs a run; the CI smoke runs a 1-game 800-round episode.

### F9 — rune-boundary truncation: the caps and the test are both present (observation, consistent)

- Where: `src/battlecode/sim_types.nim:168-176` (caps), `:268-276 truncateRunes`,
  `:277-295 truncateBytes`, `:297 sanitizeLine`; `tests/test_bc23_sheet.nim:156-176`.
- Traced: `truncateRunes` cuts with `runeSubStr`; `truncateBytes` walks `text.runes`
  accumulating `r.size` and stops **before** exceeding the byte limit — so the 16 KB reply cap
  is a byte cap landing on a rune boundary, which is what design.md:1275-1279 asks for.
  `MaxNoteRunes 280`, `MaxMottoRunes 48`, `MaxUnknownFieldRunes 40`, `MaxUnknownFields 16`,
  `MaxSheetKeys 32`, `MaxFallbackDetailRunes 200`, `MaxReplyBytes 16*1024` — every number the
  note's cap table lists (design.md:1263-1273).
  The test feeds `"\u{1F680}".repeat(400)` (4-byte astral runes) and asserts
  `notes.runeLen == 280` **and** `notes.validateUtf8() == -1`, same for `motto` at 48, and
  `truncateBytes(reply, MaxReplyBytes).len <= 16384` with `validateUtf8() == -1`.
  `decide.nim:896` runs the provider's error text through
  `sanitizeLine(error.msg, MaxFallbackDetailRunes)` before recording it.
- Checklist item: 9. Satisfied as read.

### F10 — replay re-derivation is frame-by-frame against the recorded chain, and the viewer uses the same deriver (observation, consistent)

- Where: `src/battlecode/replay.nim:285-311` (`Deriver.advance`); `replay-viewer/bc_replay.nim:22,88,99,133,152`;
  `tests/test_bc23_replay.nim:93-128, 205-219`.
- Traced: `advance()` steps the **sim** one round and compares
  `d.session.hashChainHex()` against the recorded `rounds_chains` slice for that round,
  latching the **first** divergent round into `mismatchRound`; the final chain is checked
  separately for recordings that carry only that. `bc_replay.nim` holds one `Deriver`
  (`:22`), builds it from the parsed document (`:88`), advances it for every frame
  (`:99,133-136`) and exports `bc_mismatch_round` (`:152`) — so the browser's display comes
  from the same re-derivation, not a parallel recording.
  `tests/test_bc23_replay.nim:100-128` records four bc23 games (`Quiet` 2000, `Spin` 400,
  `Barcode` 600, `Sneaky` 300), asserts `mismatch == -1` on each, asserts the written bytes
  are strict UTF-8 (`validateUtf8() == -1`), asserts `result` is singular and `results` absent,
  and asserts the replay stores **no** `robots`/`tiles`/`islands_state`/`wells_state`/`board`
  key — i.e. nothing per-round is recorded, so the re-derivation is the only source.
  `:129-142` covers the `deadline`/`abandoned` path re-deriving to the same round with
  `plan.abandon_after` as the one load-bearing record. `:205-219` re-derives the committed
  fixture with `mismatchRound == -1` over >100 frames.
- Checklist item: 2. Satisfied as read.

### F11 — the all-scripted episode ends `complete`, and every emitted order is re-checked for legality (observation, consistent)

- Where: `tests/test_bc23_replay.nim:147-173`; `tests/test_bc23_baselines.nim:48-69`.
- Traced: the clinch block plays a `gamesPerMatch: 3`, `maxRounds: 400`, all-scripted
  (`policyKind: "scripted"`) episode and asserts `games.len == 2` **and**
  `$reason == "complete"` — a clinched best-of-three, which design.md:636-640 says is correct
  rather than truncated — plus `plan.maps` len 3 against `result.games` len 2.
  `test_bc23_baselines.nim:49-69` plays 600-round games over two maps × three chassis pairings
  and asserts `w.refusedActions == 0` ("every `do*` re-checked its own `can*`"),
  `w.opsUsedPeak <= DecisionOpsHeadquarters`, and that no headquarters ever left its initial
  tile. `(d)` plays 6 games and asserts `lemonade` wins 6/6.
- Checklist item: 7, first half. Satisfied as read.

---

## The viewer chrome

### F12 — `client/replay_broadcast.html` is the starter's page with an appended block: 486 added lines, 3 removed, and all three removals are list extensions the note names (observation, consistent)

- Where: `git diff --numstat 6885a062..f9b292a2 -- client/replay_broadcast.html` → `486  3`.
  The file goes 5234 → 5717 lines. The three `-` lines are:
  - `:5507-5511` the `--statrail` id list, `…'bc25-towers','bc25-econ']` →
    `…'bc25-econ',\n 'bc23-econ','bc23-units']`;
  - `:5652` `if (!isBc20 && !isBc21 && !isBc24 && !isBc25) {` →
    `if (!isBc20 && !isBc21 && !isBc23 && !isBc24 && !isBc25) {`;
  - `:5662` the same guard on the `applyBeatSpoilers(s)` line.
  Nothing else above the banner changed, so sections 1–5 of the inherited CSS are unmodified
  by construction. `client/chrome_common.js` and `client/broadcast_core.js` are **not in the
  diff at all** (109-file list), so their sha256 assertions in `tests/test_viewer.nim` still
  bind unchanged.
- The banner exists at `:3224-3236` (`BC23 additions to the inherited cogame-battlecode
  chrome`) for the CSS and `:4837-4849` for the script block, exactly the shape checklist 14
  asks for.
- Checklist item: 14, first two bullets. Satisfied as read.

### F13 — transport rules (a)–(d), traced in the page (observation, consistent)

- (a) `relayout()` at `:5493-5522`: `var root = document.documentElement.style` and
  `root.setProperty('--hudscale' | '--topband' | '--band' | '--statrail', …)` inside a
  three-pass fixed-point loop — set on `:root`, not on `#stage`. `--band` is
  `$('transport').offsetHeight || 76`. The two bc23 boxes were added to the measured
  `--statrail` set (`:5509-5511`).
- (b) nothing bc23 ships is fixed-positioned inside the band: `#bc23-islands` is
  `top: calc(var(--topband,0px) + 6px)` (`:3278-3286`), `#bc23-units`
  `bottom: calc(var(--band,0px) + 76px)` (`:3307`), `#bc23-econ`
  `bottom: calc(var(--band,0px) + 8px)` (`:3308`), `#bc23-doctrines`
  `max-height: calc(100% - var(--topband,0px) - var(--band,0px) - 46px)` (`:3331`),
  `#bc23-tempest` lives inside `#endcard` (`:3590`). All `position: absolute` inside the
  stage, all measured off the band variables.
- (c) `#endcard` (inherited, `:1847-1869`) is `top: var(--topband,0px); bottom:
  var(--band,0px); display: none`, shown by `#endcard.on { display: flex }` — and
  `renderEndcard` adds exactly that class (`:5487` `$('endcard').classList.add('on')`).
  Every seek path dismisses it: `seek()` calls `dismissEndcard()` as its **first** statement
  (`:5265-5268`), the transport buttons call it for every id except `btn-loop`/`btn-skip`
  (`:5538`), the keyboard handler for every key except `r`/`f` (`:5566`), and the bc23 block's
  beat buttons go through `api.seek` (`:4927`) which is the same `seek` (`:5172`… wiring at
  `:5206-5214`). So the scrubber can always pull the match back from the score screen.
- (d) the bc23 beat markers are `<button type="button">` with `aria-label` and `title` from
  `b.label`, `el.__tick = b.t`, and a click handler calling `api.seek(b.t / span)`
  (`:4910-4930`) — the builder is `buildBc23BeatButtons`, defined once, and
  `applyBc23BeatSpoilers` once (`tests/test_viewer.nim:826-830` counts both, and counts
  `function markBeat` at **0**). Twelve `html[data-year="bc23"] .beat-marker.<kind>` rules at
  `:3361-3372`, one per kind in the vocabulary.
- One inherited quirk, recorded because I traced it and it is not bc23's: the marker's
  *position* is `(b.t - s.st)/span` while its *seek* is `b.t / span` — the two disagree when
  `s.st != 0`. This is byte-identical in the bc26 builder (`:5232-5239`) and in all four
  earlier year blocks (`:3683-3690`, `:3985-3992`, `:4289-4296`, `:4633-4640`), and in this
  repo every year's frame sets `"st": 0` (`src/battlecode/broadcast.nim:457, 585, 778, 995,
  1177, 1226`), so the two expressions coincide. Not introduced by this diff.
- Checklist item: 14, third bullet. Satisfied as read.

### F14 — the beat contract is asserted from the committed fixture, and the fixture really emits all twelve kinds (observation, consistent)

- Where: `tests/fixtures/replay-bc23.json` (146 events); `tests/test_bc23_beats.nim:1-145`.
- Observed: the fixture's event-kind census is `anchor_built 40, boost_field 18,
  conquest_progress 4, destabilize_hit 20, doctrine_received 2, duel 20, first_action 2,
  first_elixir_unit 2, game_end 1, game_start 1, island_captured 19, island_lost 13, rout 2,
  well_transformed 2` — which maps onto exactly the twelve beat kinds through
  `broadcast.nim:158-187`. The test asserts ≥24 beats, ≥8 kinds, **and** that all twelve are
  present (`:60-64`), every label non-empty, ≤120 runes and valid UTF-8 (`:67-71`), the note's
  own feed wording spot-checked (`:73-88`), a bc23-scoped CSS rule for **every emitted kind**
  (`:91-95`), and — the r1-F26 inverse — that the page declares *exactly* the twelve and
  nothing outside the vocabulary (`:98-112`). It also re-runs `beatsFor` with the year forced
  to `bc24` and asserts `first_action` then maps to nothing (`:115-129`), which is the
  three-way discriminator working.
- `broadcast.nim:143-144` is the discriminator: `let isBc25 = doc.year == "bc25"` and
  `let isBc23 = doc.year == "bc23"`, used at `:172` (`first_action` → `build` for bc25 **or**
  bc23) and `:180` (`rout`). Checklist item 14(d). Satisfied as read.

### F15 — `#viewpanel` is kept, and the 360 px rules are present (observation, consistent)

- Where: banner comment `:3232-3235` states the keep-decision and its arithmetic; the media
  query at `:3376-3381` drops `#bc23-islands .towin`/`.neutral` and `#bc23-econ .prog` /
  `#bc23-units .lbl` under 640 px and shrinks the fonts; `#bc23-econ .who, #bc23-units .who`
  carry `flex: 0 0 auto; min-width: 3.2em` (`:3313-3315`).
- Checklist item 11 asks specifically for `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`.
  That rule is in the **inherited** part of the page and is untouched by this diff (no `-` line
  near it); the bc23 block adds the analogous rule for its own two stat boxes. Checklist 14's
  last bullet (`#viewpanel` kept only when the note says the board is larger than the
  viewport) is satisfied: the note says exactly that at design.md:1503-1512, and the pool tops
  out at 60×30.

---

## CI evidence read from the run's own logs (checklist items 6, 13, 15)

### F16 — `SEAT-COUNT FAIL` appears **nowhere** in the docker-smoke log, and the bc23 episode ran with `seats=2` and `reason=complete` (observation, consistent)

- Evidence: job `102054508996` of run `34224289835`,
  `gh run view --job 102054508996 -R Metta-AI/cogame-battlecode --log` (2696 lines).
  `grep -c "SEAT-COUNT FAIL"` → **0**; `grep -n "SEAT-COUNT"` → no line at all.
- Every one of the six episodes logs `game=battlecode seats=2 config={… "num_agents": 2 …}`
  and then `smoke OK: seats=2 … reason=complete`. The bc23 line (log :2372, :2380):
  ```
  game=battlecode seats=2 config={… "num_agents": 2, "year": "bc23", "pool": "small",
    "seed": 1009, "gamesPerMatch": 1, "maxRounds": 800, … }
  smoke OK: seats=2 results=1661B replay=17945B reason=complete
  ```
- The across-the-pair substance step (log :2444):
  `across the two seats: units=79 banked=3480 anchors built=5 placed=3 islands captured=3`
  against floors 60/200/1/1/1 — so an anchor really was built, ferried and planted, and an
  island really changed hands, in an episode with **no** `ANTHROPIC_API_KEY`.
  Pacing step (log :2468): `bc23 smoke: sim_seconds=0.409 rounds=755 wall=0.51s` — 755 of 800
  rounds, i.e. the game ended early by conquest.
- `seed: 1009` is pinned in `ci.yml` and `tests/test_bc23_maps.nim:184-192` asserts
  `drawMaps("small", 1009, 1) == @["Quiet"]`, so the smoke's map cannot drift.
- Checklist item: 6. Satisfied, by grep and not by colour.

### F17 — the `wasm-viewer` job `needs: docker-smoke`, executed the bundle on the bc23 replay, and the smoke step really ran (observation, consistent)

- Where: `.github/workflows/ci.yml:2350-2355` (`wasm-viewer:` … `needs: docker-smoke`), the
  `Load the bundle in a real browser (ALL SIX years' replays)` step at :2436-2505 (no
  `continue-on-error` anywhere in the job).
- Evidence: job `102055521000`, log line 2177 — the sixth (bc23) iteration:
  ```
  {"loaded":true,"ms":310,"clock":"0:16 GAME 1 OF 1 — QUIET doctrines",
   "scorebug":"CLAN ASH Clan Ash · Anchor the sky. 49 … CLAN BASIL Clan Basil · Anchor the sky. 50",
   "feed_lines":4}
  scrub selector: #scrub
  ```
  and the wasm-under-node smoke (log :2247-2255+) reporting
  `{"loaded":true,"game_version":"GV09","sim_sources_stamp":"1435a430…","frames":200,
  "mismatch_round":-1}` for each replay — the in-browser re-derivation matches the recording.
  The bc23 run used `--timeout 120 --soak 15 --killfeed-overlap`, which is the pacing decision
  at design.md:1533-1545.
- Checklist item: 13, first two bullets. Satisfied with cited evidence.
- On item 13's third bullet (playback must open at `gameStarts[0].tick`, never the lobby):
  this coworld's replay carries no lobby frames — every year's chrome frame sets `"st": 0`
  (`src/battlecode/broadcast.nim:457, 585, 778, 995, 1177, 1226`) and a frame **is** a sim
  round (`replay.nim:285` "One frame == one round"), with the pre-match doctrine events carried
  as `ms`-stamped records outside the frame axis. bc23 follows the five shipped years exactly.
  I could not construct the note's "late gameStart" counter-example from this tree because the
  format has no `lobbyJoinTimeoutTicks` concept; **labelled as inference**, and the settling
  evidence is the CI clock reading `0:16` at 0 % rather than a frozen first tick.

### F18 — BLOCKING (item 15) — the full-cap doctrine-text fixture has **no bc23 row**, and `canvas_text.total` is 0 on every replay, so bc23's LLM-authored text is drawn by nothing any gate looks at

- Where: `tools/ci/renderer_fixture.html:70` —
  ```js
  var YEARS = ['bc26', 'bc20', 'bc21', 'bc24', 'bc25'];
  ```
  and `:86-89` — `var year = (yearParam === 'bc20' || yearParam === 'bc21' ||
  yearParam === 'bc24' || yearParam === 'bc25') ? yearParam : 'bc26';`
  The file is **not in the base…head diff** (109 files; `tools/ci/renderer_fixture.html`
  absent), so no bc23 row was added and `?year=bc23` falls through to `'bc26'`.
- The fixture's own comment states the rationale this violates (`:63-69`): *"ONE ROW PER YEAR,
  because each year's readouts are different elements under different CSS and a fixture that
  only lays out bc26 says nothing about bc20's flood, soup, unit and doctrine panels…"*.
- What bc23 draws from LLM text: `client/replay_broadcast.html:5028-5042` renders
  `seat.notes` (the 280-rune cap) into `#bc23-doctrines-body`, inside `#bc23-doctrines`
  (`:3328-3346`, a `max-height`-bounded scrolling box) — a **bc23-only** element under
  bc23-only CSS that the fixture never instantiates. Being precise about the other string:
  `motto` (48 runes) goes through the **shared** scorebug `#pl-sub-<slot>`
  (`:5286-5295`, `.plate-sub`), which the fixture's five existing rows do exercise, so the
  motto path is covered and the `notes` path is not.
- Why the other gates do not cover it, from the run's own logs (job `102055521000`):
  - all six bundle smokes report `canvas text: 0 drawn, 0 never inside …, 0 ellipsized`
    (log :2102, 2120, 2137, 2151, 2165, 2180). Checklist item 15 says in terms:
    *"`total: 0` means the check covered nothing … and is not evidence of anything."*
  - the fixture step itself reports `canvas text: 0 drawn … (--strict-text-bounds)`
    (log :2313) — so `--strict-text-bounds` is gating a zero here too; the fixture's real
    assertions are its own DOM-overflow verdict, and that verdict was computed for five years'
    readouts at 360/720/1280 px, not bc23's.
  - `docker_smoke.sh` runs without `ANTHROPIC_API_KEY` (checklist 15's own point), so the
    bc23 replay the browser loaded carries `notes = "default lemonade doctrine"` and
    `motto = "Anchor the sky."` — the scorebug in the log shows exactly that string. Nothing
    in CI has ever rendered a 280-rune `notes` through `#bc23-doctrines`.
- Design note: design.md:2311-2315 — *"the separate `tools/ci/renderer_fixture.html` step —
  full-cap `notes` and `motto` on both seats at three widths including **360 px** … runs
  through the same harness with `--strict-text-bounds` … **The fixture gains a bc23 row.**"*
  It did not.
- Checklist item: **15**, last bullet ("A repo whose viewer draws LLM-authored text must
  therefore ship a **worst-case renderer fixture** … Cite the step and its `canvas_text` line;
  a repo that draws model text and has no such fixture is a blocking `legibility` finding").
- Why blocking: bc23's doctrine overlay is the one element that carries model text, it is
  scoped `html[data-year="bc23"]`, and no gate in this repo has rendered it with a full-cap
  string at any width. The counter-argument the judge should weigh: the repo **does** ship the
  fixture and the step, so the item's literal words are met at repo level — it is the bc23
  *coverage* that is missing, and the design note is the thing that names it as required.
  Category: `legibility` (item 15 names it) — arguably `static-viewer` if the judge reads it
  under item 14 instead.

---

## Design-note deviations (none of these falsifies a named checklist item, so all are non-blocking under `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST — reported because the note is the binding spec and the brief names each of them in scope)

### F19 — non-blocking — Tier A′ of the parity oracle is **not shipped**: the Java scenario twin does not exist and the job runs one bot

- Where: `tools/ci/parity_tiers_bc23.py:20-33` — the docstring's own words:
  `Tier A' (NOT SHIPPED IN THIS LANDING) the scenario packages.` …
  `Its bit-exact Java twin is a phase-30 item`.
  `.github/workflows/ci.yml` (Tier A/C step) passes `--bots examplefuncsplayer23` only.
  `tools/oracle/bc23/` contains `Bc23Trace.java`, `build_oracle.sh`, `jar.lock` and
  `examplefuncsplayer23/RobotPlayer.java` — **no `bc23scenario/RobotPlayer.java`**, which
  design.md:915 lists as a new CI-only file. The Nim half **is** committed
  (`src/battlecode/years/bc23/chassis/scenario23.nim`, 204 lines, behind `-d:bc23Scenario`).
- Design note: design.md:2147-2182 makes Tier A′ **BLOCKING**; design.md:2211 states *"the
  phase-30 exit condition is that Tiers A, A′ and B pass with an EMPTY ledger"*;
  design.md:2228 *"Tiers A, A′, B and C are the phase-30 gate."*
- What this means concretely, in the note's own measurement (design.md:2148-2154): the example
  bot that Tier A does compare *never* takes an anchor, places one, captures an island, builds
  an amplifier/destabilizer/booster, transfers a resource to a headquarters, upgrades or
  transforms a well, or writes the shared array. So the anchor/island subsystem, the elixir
  tree, the tempo fields, the comms paths and `CONQUEST` are compared against the Java engine
  by **nothing**; they are covered only by the repo's own unit shards.
- It is recorded, not hidden: `docs/PARITY.md` (bc23 section, the "The tiers" bullet list)
  says *"Tier A′ — NOT SHIPPED IN THIS LANDING, and this is the one tier of the four that is
  open"*. One nuance: design.md:2179-2182 permits dropping a scenario item only when it is
  *"added to `docs/PARITY.md` §What is NOT compared with the reason"*, and that section
  (which the diff also adds) lists the bytecode counter, indicator strings, `.bc23` files and
  `Math.random()` — **not** Tier A′. The disclosure is in the tiers bullet instead.
- Checklist: no item names the parity tiers, so by the categorisation rule this cannot be
  blocking. It is the largest gap between the note and the tree.

### F20 — non-blocking — the `-d:bc23BrokenChassis` negative control is never executed: nothing runs it

- Where: `tests/test_bc23_survival.nim:84-104`. The file is
  `when defined(bc23BrokenChassis): <assert g.passed == 0> else: <assert g.passed == 6>`.
  Nothing compiles it with that define: `grep -rn "BrokenChassis" --include=*.yml` → **no
  hit**, and `ci.yml`'s `Run tests` step (:298-338) invokes
  `nim r [--hints:off | --hints:off -d:release] --path:src <file>` for every `tests/*.nim`.
- Compare the two years that do it: `tests/test_bc24_survival.nim:118-136` and
  `tests/test_bc25_survival.nim:106-133` both spawn **themselves** as a subprocess with
  `-d:bc24BrokenChassis` / `-d:bc25BrokenChassis` from the normal (non-broken) run and assert
  the child comes back red. bc23's shard has no such block, so its `when defined(...)` arm is
  dead code in every CI run and the gate is never demonstrated to be capable of failing.
- The broken chassis itself **is** implemented: `world.nim:216-218` (`brokenChassis*: bool`),
  `world.nim:1117-1118` (`when defined(bc23BrokenChassis): w.brokenChassis = true`),
  `chassis/carrier.nim:145` (`if w.brokenChassis: return false` on the deposit path). So the
  control exists and only the invocation is missing.
- Design note: design.md:1986-1992 — *"The same gate is then run as a **subprocess** against a
  known-broken chassis compiled behind `-d:bc23BrokenChassis` … and **must come back red**. …
  A gate that cannot fail is not a gate."*
- Checklist: item 7 requires the all-scripted-episode test and grid-tuned baseline parameters
  (both present, F11 and F21); it does not name the negative control. Non-blocking by the
  rule, and I flag it as the finding a judge is most likely to want to re-read item 1 against
  ("a gate that cannot fail"), since the effect is that a gate the note treats as load-bearing
  is inert.
- Second, smaller observation in the same file: `tests/test_bc23_survival.nim:79` is
  `if w.refusedActions != 0: ok = false`, placed **after** `:74 if ok: result.passed += 1`,
  so the illegal-order check cannot affect the gate's verdict. (Legality is separately and
  effectively asserted in `tests/test_bc23_baselines.nim:55-57`, so nothing is untested — the
  line is simply dead.)

### F21 — non-blocking — the competence gate's elixir clause is `>= 1 of 6`, where the note says `>= 4 of 6`; the deviation is measured and documented in the shard's header

- Where: `tests/test_bc23_survival.nim:56` `MinElixirGames = 1  ## measured healthy 3 of 6;
  BROKEN 0 of 6`, asserted at `:100-102`; the reasoning at `:28-41`: the `lemonade` mirror
  *ends by conquest at round 800-1100 on five of the six `small` maps* and the 600 kg
  transformation needs ~500 rounds from the moment the programme opens, so 3 of 6 flip a well.
- Design note: design.md:1983-1985 asks for `>= 1 well transformed to elixir` in **≥ 4 of the
  6** games. All the other committed floors sit at or above the note's numbers
  (`MinCarriersBuilt 12`, `MinLaunchersBuilt 8`, `MinDeposited 400`, `MinAnchorsBuilt 1`,
  `MinAnchorsPlaced 1`, `MinHoldStreak 100`, `MinAliveAtEnd 8` — design.md:1979-1982), each
  with its measured healthy range beside it, which is what design.md:1993-1996 asks for.
- Checklist: item 7's "tuned with a grid harness, not guessed" is satisfied by the measured
  ranges in the header (`carriers 27..96`, `launchers 30..112`, `deposited 1881..4840`,
  `anchors 2..8`, `placed 2..4`, `hold 537..661`, `alive 18..76`, and the broken control's
  `0..0` deposits). The one lowered clause is a note deviation, not a checklist violation.

### F22 — non-blocking — the docker-smoke per-seat floors are committed **below** the note's numbers for two of the four statistics

- Where: `.github/workflows/ci.yml`, the bc23 episode's
  `SMOKE_REQUIRE_STATS: {"units_built":20,"adamantium_mined":60,"mana_mined":12,
  "damage_dealt":1}`, with a 20-line comment above it recording the measurement:
  `units_built [37, 42], adamantium_mined [3617, 118], mana_mined [203, 25],
  damage_dealt [5340, 2]`.
- Design note: design.md:2267 gives `{"units_built":20,"adamantium_mined":60,
  "mana_mined":40,"damage_dealt":20}`, and design.md:2286-2288 gives **two** constraints —
  "never below this note's numbers, and never above what a correct episode produces". The
  measurement makes them unsatisfiable for `mana_mined` (weak seat 25 < note's 40) and
  `damage_dealt` (weak seat 2 < note's 20, because the upstream example bot's launcher attacks
  the square one step EAST of itself — design.md:832-834, which may not be "fixed" because
  that bot is one side of the oracle). The builder chose the second constraint and wrote the
  reasoning inline.
- The stronger, year-specific assertion is the across-the-pair one, and it is **above** the
  note's floors, not below: `units>=60, banked>=200, anchors_built>=1, anchors_placed>=1,
  islands_captured>=1` (design.md:2276-2280), measured 79/3480/5/3/3 (F16).
- Checklist: not a named item. Non-blocking.

### F23 — non-blocking — `tests/test_bc23_knobs.nim` retunes or drops parts of the note's knob-teeth table

- Where: `tests/test_bc23_knobs.nim:115-272`. Read against design.md:2002-2015:

  | knob | note asks | committed |
  |---|---|---|
  | `opening` | launchers by 400 up **≥ 60 %**; carriers by 400 down ≥ 30 % | `:115-118` up ≥ 25 % (`125`); `:119-122` down ≥ 30 % (`70`) |
  | `launcher_ratio` | launchers built up **≥ 2×**; carriers down ≥ 40 % | `:132-134` `launchersBuiltBy400` up ≥ 15 % (`115`); `:135-137` down ≥ 40 % (`60`) |
  | `well_priority` | mana up ≥ 50 %; adamantium down ≥ 30 % | `:140-147` `150` / `70` — as asked |
  | `elixir_tech` | wells transformed up ≥ 1; elixir mined up ≥ 300 | `:150-157` both expressed as ≥ 2× relative, not absolute |
  | `elixir_spend` | destabilizers built up ≥ 2; destabilize damage up ≥ 100 | `:159-208` replaced by a deterministic `nextBuild`/`sinkUnit` assertion on a stocked headquarters |
  | `anchor_round` | first anchor placed earlier by ≥ 800 **and** rounds holding up ≥ 400 | `:211-214` only `roundsHoldingAnyIsland` up ≥ 40 %; the first-anchor row is **absent** (though `first_anchor_round` is recorded in `statsJson23`) |
  | `anchor_budget` | anchors placed up ≥ 3; launchers down **≥ 25 %** | `:216-221` up ≥ 2× (`200`); down ≥ 10 % (`90`) |
  | `island_priority` | mean distance up **≥ 30 %** **and** islands lost down ≥ 1 | `:228-231` distance up ≥ 5 % (`105`); the islands-lost row is **absent** |
  | `amplifier_use` | amplifiers up ≥ 2; array writes up **≥ 3×** | `:234-241` up ≥ 2× (`200`); writes up ≥ 20 % (`120`) |
  | `destabilizer_use` | strike distance up ≥ 40 %; carrier damage up **≥ 30 %** | `:244-251` `140` as asked; damage up ≥ 15 % (`115`) |
  | `retreat_on_launcher_loss` | launchers lost down ≥ 20 % **and** anchor healing up ≥ 50 | `:254-257` only `anchorHeals` up ≥ 10 %; the launchers-lost row is **absent** |
  | `carrier_throw` | resources thrown up ≥ 200; resources deposited down ≥ 15 % | `:260-272` thrown up ≥ 2× (`200`); **banked share** down ≥ 10 % (`90`) |
- The **substitutions** are documented in the header exactly as design.md:1999-2000 requires
  (`:9-30`: the Chebyshev distance metrics, the `anchor_heals` stand-in, and the
  `carrier_throw` banked-share substitution with both measurements — raw deposits moved only
  −1.3 % (15 545 → 15 350) while the share moved −23.7 % (5 313 → 4 052 permille-sum), gated
  at −10 %), plus two more inline (`:126-131` for `launcher_ratio`, `:160-178` for
  `elixir_spend`). What is **not** documented anywhere I could find is the *reduction of five
  margins* and the *dropping of three of the note's twelve second-halves*.
- The debug/release split (`:32-41`, `:99-112`) gates every signed delta in `-d:release` only;
  the debug pass asserts `lo > 0 or hi > 0`. Since CI runs each file in both modes, the signed
  assertions still run once per CI run. This is the arrangement `tests/test_bc24_knobs.nim`
  already uses and the build report records the reason (debug cost >6 min).
- Checklist: not a named item. Non-blocking.

### F24 — non-blocking — `tests/test_viewer.nim`'s "no unscoped bc23 CSS rule" check is vacuous

- Where: `tests/test_viewer.nim:881-893`:
  ```nim
  for line in page.splitLines():
    let t = line.strip()
    if not t.startsWith("#bc23-"): continue        # :885
    if "display: none" in t: continue
    if not t.startsWith("#bc23-"): unscoped.add(t) # :891  — unreachable
  checkEq("no bc23 CSS rule can reach another year's element", unscoped.len, 0)
  ```
  Line 885's `continue` makes line 891's condition false for every surviving line, so
  `unscoped` is always empty and the `checkEq` is true by construction. This block is new in
  this diff (no `unscoped` symbol exists in `test_viewer.nim` at `6885a062`), so it is not an
  inherited pattern.
- The property it means to assert does hold as read: every bc23 selector in the page begins
  with `#bc23-` or `html[data-year="bc23"]` (F13, and `tests/test_bc23_beats.nim:98-112`
  independently asserts the beat-marker rules are exactly the twelve and all year-scoped).
  So this is a test that proves nothing, not a page that misbehaves.
- Checklist: item 1's "no test loosened" concerns tests *changed during this run* — this is a
  newly added test that is weaker than its own message, which is not the same thing as
  loosening an existing one. Non-blocking; recorded because the judge will otherwise read the
  green check as evidence.

### F25 — non-blocking — the `first_action` event field is `action`, not the note's `kind`, and the code says why

- Where: `src/battlecode/match.nim:232-249`; `src/battlecode/years/bc23/world.nim:260-262`;
  `src/battlecode/years/dispatch.nim:138-146`.
- Observed: `match.nim:236-241` states it outright — *"THE FIELD IS `action`, NOT THE DESIGN
  NOTE'S `kind`. `MatchEvent` flattens `fields` into the same object as the event's own `kind`
  key, so a field called `kind` SILENTLY OVERWRITES THE EVENT KIND and the replay comes back
  carrying events of kind "move" and "spawn"."* bc24 and bc25 already use `action`;
  `broadcast.nim:233-237` reads `e.fields{"action"}` when building the label, so emitter and
  reader agree.
- Design note: design.md:1354 (`first_action` … `kind` (from `Bc23ActionNames`)) and
  design.md:899. The vocabulary itself is present and documented
  (`dispatch.nim:138-142`, 15 names).
- Checklist: not a named item, and the divergence is the safe direction. Non-blocking.

### F26 — non-blocking — inherited: `first_divergence()` can miss a Java trace that is exactly one line longer

- Where: `tools/ci/parity_tiers_bc23.py:116-134`. `zip(jf, nf)` pulls from `jf` first; when
  `nf` is exhausted the already-pulled `jf` line is discarded, and the tail check
  (`:127-133 jrest = jf.readline()`) then reads the line *after* the discarded one. So a Java
  trace with exactly one extra final line reports `None` → "bit-exact". The asymmetric case
  (Nim one line longer) is detected, because `next(jf)` raises before any Nim line is
  consumed.
- This is byte-identical to `tools/ci/parity_tiers_bc25.py` (`diff -u` shows the only changes
  in that function are the two `strip_bc(nl…)` lines) — inherited, **not introduced here**.
- Checklist: not a named item. Non-blocking.

### F27 — non-blocking — a doc comment in `results.nim` was left interleaved by the edit

- Where: `src/battlecode/results.nim:195-206`. The `EndReasons` doc comment now reads
  *"The union of all SIX years' `DominationFactor` renderings plus our own wall-clock
  `abandoned`. bc23's six are the last row: …item 7)."* immediately followed by the surviving
  old continuation line *"## wall-clock `abandoned`. bc24's `MORE_FLAGS_PICKED` and
  `RESIGNATION` are…"* — so "wall-clock `abandoned`" appears twice and one sentence starts
  mid-clause. Comment text only; no code effect.
- Checklist: not a named item. Non-blocking.

### F28 — non-blocking — the note's named float64 vector is asserted to be **wrong**, and the code corrects it with a measurement (observation)

- Where: `tests/test_bc23_tempo.nim:14-33` and `docs/RULES-BC23.md:297-310` (divergence
  item 16).
- Observed: the note pins `base = 5, hundredths = 70 → 3` as a named vector (design.md:992-994
  and again at design.md:1901-1902, *"an integer `(5*70+50) div 100` would give 4"*). The test
  asserts the opposite — `checkEq("base 5 at 0.70 is 4 in Java, not the note's 3",
  applyMultiplier(5, 70), 4)` — on the reasoning that `5 * (70/100.0)` is *exactly* 3.5 in
  float64 and Java's `Math.round` is `floor(x+0.5)` → 4. It then supplies replacement vectors
  that do show the note's point (`base 45 × 0.70`: Java 31, integer form 32; `base 50 × 1.15`:
  57 vs 58) and states that over the *reachable* base set the two forms agree, so the float64
  reproduction is defensive.
- The arbiter is Tier B, and Tier B is green: `data/bc23/tables.json` is byte-diffed against
  what the jar's own classes emit under Temurin 8 (parity job `102054509029`, log :549
  `Tier B: the committed arithmetic table IS the jar's own output`), and the same step
  cross-checked 52 `GameConstants` fields against the jar (log :516). So the correction is
  backed by the JVM rather than by argument. `docs/RULES-BC23.md` has **17** divergence items
  against the note's 15 — 16 is this one and 17 is *"`transferResource` to an ENEMY
  headquarters is legal in the engine for a positive amount"*, both new findings recorded
  rather than silently ported.
- Checklist: not a named item. Non-blocking, and reported as a note-vs-code disagreement the
  judge should know was resolved *against the note* with evidence.

---

## Traced and consistent (verified, no finding)

- `tools/ci/parity_tiers_bc23.py:101-119` — the `cd58a9cd` fix is exactly two lines
  (`n = nl.rstrip("\n")` → `n = strip_bc(nl.rstrip("\n"))`, in the loop and in the tail
  check; `diff -u tools/ci/parity_tiers_bc25.py tools/ci/parity_tiers_bc23.py` isolates them).
  It is **not** a weakening: the `bc=` column is the one field the Nim emitter cannot produce
  (it writes a constant 0), every other field on the line is still compared byte for byte, and
  the bytecode values are still enforced separately by `peak_bytecode()` (`:137-151`) off the
  **Java** trace against `LIMITS` (`:82-89`) — bc23's own `BL` column
  (HEADQUARTERS 20 000, CARRIER 12 500, rest 10 000), replacing bc25's
  `{"ROBOT": 17500, "TOWER": 20000}`, with `limit_for` raising `SystemExit` on an unknown type
  instead of guessing (`:92-98`). Tier C's clause (d) still fails any divergence found under
  the 50 % headroom (`:240-244`).
- Parity job `102054509029` (green): all six maps `rounds=2000`, `built=190…509`,
  `peak_bytecode=5…7 %` (log :668-673), and `bc23 parity: 6 pairs, all bit-exact for whole
  2000-round games, ledger empty` (log :712). `tools/ci/parity_ledger_bc23.json` is a 4-line
  empty list. The JDK-8 guard really runs: the job asserts `1.8.` in `java -version` **and**
  that `javac` *rejects* `--release`.
- `src/battlecode/years/dispatch.nim` — one arm added to each of
  `yearIdOf`, `strongChassisFor`, `poolNamesFor`, `drawMapsFor`, `sideAslotFor`, `mapPathFor`,
  `mapCardFor`, `newSession`, `stepRound`, `currentRound`, `running`, `hashChainHex`,
  `mapWidth`, `mapHeight`, `playGameFor`, plus `statsJson23` and the `yBc23` `Session` branch
  (`w23`, `sides23`, `chassis23`). `Session` is an object variant, so a half-added year would
  not compile. No existing arm was edited.
- `src/battlecode/sheet.nim` — the four-line shape the note describes (`YearBc23`,
  `doctrine23`, a `knownKeysFor` arm, a `defaultSheet` field), plus `validate`/`toJson`/
  `plainWords` arms. `src/battlecode/baselines.nim` — `blLemonade`/`blExamplefuncsplayer23`,
  the `yBc23` arms of `defaultBaselineFor` (:41) and `baselineFor` (:68-72, resolving
  `scaffold|examplefuncsplayer|examplefuncsplayer23|example` → weak floor and **everything
  else** → `lemonade`), `baselineChassis` and `baselineReply`.
- `src/battlecode/match.nim:432-437` — `winBonusFor` returns 200.0 for `{yBc25, yBc23}`, which
  is the `results.scores = 200 × wins + mean(points)` the note's scoring section requires
  (design.md:596).
- `tests/test_bc23_scoring.nim` (128 lines) exists and, per its header, covers the float32
  narrowing, the truncating `int()`, the 0-0 `share = 0.5`, the super-increasing property and
  the scores-vs-wins agreement on random finals. I read the file's structure but did not
  re-derive its 500-sample assertion by hand; the `test` job is green.
- `data/maps/bc23/` holds exactly **22** committed maps; `data/bc23/tables.json` and
  `data/atlas_bc23.{png,json}` are committed (17 067 B + 1 118 B). `ci.yml` regenerates all
  three artefact families from the pinned checkout and byte-diffs them
  (`gen_year_constants.py --check`, `convert_maps_bc23.py --check`,
  `build_sprite_atlas_bc23.py --check`) and asserts `--parse-all` reads **103** `.map23`
  files. `tests/test_constants.nim:230-268` runs the same three `--check` calls when
  `BC23_DIR` is set and falls back to spot values otherwise.
- `docs/RULES-BC23.md` (340 lines) with `## Divergences` (17 items) and
  `## What this year measures, for the next one`; `NOTICE` gains the five sections the note's
  §Licensing lists (engine AGPL-3.0 at `af42086e`, client sprites, `awesomelemonade`,
  `vrangr1`, `jmerle` MIT) plus an explicit "cited, never used" section for the two
  unpublished bots. `docs/PROTOCOL.md` and `README.md` gain bc23 sections.
- `replay-viewer/config.nims` and both `static_replay*.js` are **not in the diff**, so the
  emscripten link flags and the worker bootstrap are the same starter's by construction — the
  cogame-lantern splice checklist 13's fourth bullet warns about cannot have happened here.
  The bundle's `loaded: true` on all six replays is the positive evidence (F17).
- `src/battlecode/render.nim` (+179 lines) adds the bc23 terrain/well/island/unit/tempo
  drawing behind the `YearSpec.atlas` mapping; `src/battlecode/broadcast.nim` (+253) adds the
  bc23 frame record (`:1169-1217`, `"st": 0`) and the `beatsFor` arms. No other year's frame
  builder was edited.

## Could not determine

- **Whether the coworld version really ships as 0.6.0** — it is a release-time workflow input,
  not a tree fact (F4). Settled by the phase-40 `release-result.json`.
- **Whether a hosted (LLM-credentialed) episode settles inside 720 s.** The arithmetic and
  every bound check out (F8), and the CI episode is 755 rounds in 0.51 s wall — but CI has no
  API key, so the 45 s doctrine phase is never actually exercised end to end. Settled by a
  phase-60 run's `wall_clock_seconds`.
- **Whether `#bc23-doctrines` and `#bc23-tempest` hold a full-cap 280-rune `notes` without
  clipping at 360 px.** No gate in the repo renders it (F18). Settled by adding the bc23 row
  to `tools/ci/renderer_fixture.html` and reading its verdict, which is what design.md:2315
  asks for.
- **Whether the bc23 sim agrees with the Java engine on the anchor/island subsystem, the
  elixir tree, the tempo fields, the comms paths and `CONQUEST`.** Tier A compares a bot that
  reaches none of them and Tier A′ is not shipped (F19). Settled by the scenario twin, or by
  an explicit decision to accept the unit shards as the only evidence for those paths.
- **`coworld validate_upload_manifest` acceptance of the template** — the CLI is not installed
  in this sandbox; `tests/test_manifest.nim` calls it and the `test` job is green, which I
  cite rather than reproduce.
- I did **not** audit the 6 089 lines of new sim/chassis Nim rule-by-rule against the pinned
  engine sources; the engine checkout was not fetched here. What I traced is the structure, the
  bounds, the budget enforcement, the dispatch wiring and the tests' own assertions. The
  rule-level evidence is Tier A/B (green, cited above) plus the twenty unit shards.

## Summary

Blocking (falsifies a named acceptance-checklist item):

- **F18** — item **15** (`legibility`): `tools/ci/renderer_fixture.html:70` has no `bc23` row
  and the file is not in the diff, so the only chrome that draws LLM-authored text for this
  year (`#bc23-doctrines-body`, the 280-rune `notes`) is rendered by no gate; every
  `canvas_text.total` in the run is 0, which item 15 says "is not evidence of anything", and
  the design note promised the row (design.md:2315).

Non-blocking (design-note deviations and observations; none maps onto a checklist item):

- **F19** parity **Tier A′ not shipped** — no `tools/oracle/bc23/bc23scenario/RobotPlayer.java`,
  job runs `--bots examplefuncsplayer23` only; the note makes A′ blocking and part of the
  phase-30 gate. Disclosed in `docs/PARITY.md`.
- **F20** the `-d:bc23BrokenChassis` negative control is **never executed** — no subprocess
  invocation (bc24/bc25 both have one) and no CI define; plus a dead `refusedActions` check at
  `tests/test_bc23_survival.nim:79`.
- **F21** competence-gate elixir clause `≥1 of 6` vs the note's `≥4 of 6` (measured 3 of 6,
  documented).
- **F22** two of four docker-smoke per-seat floors committed below the note's numbers
  (`mana_mined` 12 vs 40, `damage_dealt` 1 vs 20), measured and documented; the across-the-pair
  assertions are at the note's values.
- **F23** knob-teeth margins retuned downward on five rows and **three** of the note's twelve
  second-half assertions dropped (`anchor_round` first-anchor, `island_priority` islands-lost,
  `retreat_on_launcher_loss` launchers-lost); substitutions documented, reductions not.
- **F24** `tests/test_viewer.nim:881-893`'s "no unscoped bc23 CSS" check is vacuous
  (`continue` at :885 makes :891 unreachable).
- **F25** `first_action`'s field is `action`, not the note's `kind`, with the reason in the code.
- **F26** inherited off-by-one in `first_divergence()`'s tail check (one extra Java line reads
  as bit-exact).
- **F27** interleaved doc comment in `src/battlecode/results.nim:195-206`.
- **F28** the note's `base 5 × 0.70 → 3` vector is wrong; the code asserts 4 and supplies
  replacement vectors, backed by a green Tier B byte-diff against the jar.

Traced and consistent, with no finding: **F1, F2** (item 1 — CI green at `f9b292a2`, run
`34224289835`, 9/9 jobs `success`; no assertion deleted, no tolerance widened, no skip added —
the one relaxation, `test_bc25_replay.nim:323`, adopts the form bc20/bc21/bc24 already use and
leaves `rederives(text) == -1` untouched), **F3, F5, F6** (items 3, 6, 10, 12 — manifest,
policies, placeholders, release order, `GameVersion`), **F7, F8, F9** (items 5, 8, 9 — one
parallel batch, one retry, bounded waits, rune-safe truncation), **F10, F11** (items 2, 7 —
frame-by-frame re-derivation and `reason == "complete"`), **F12–F15** (items 11, 14 — the page
is the starter's plus an appended block, transport rules (a)–(d), twelve styled beat kinds,
`#viewpanel` kept for a stated reason), **F16, F17** (items 6, 13 — zero `SEAT-COUNT FAIL` in
the docker-smoke log, `wasm-viewer needs: docker-smoke` and `loaded: true` on the bc23 replay
with `scrub_selector == "#scrub"`).

_Total: 28 numbered observations; 1 categorised blocking._
