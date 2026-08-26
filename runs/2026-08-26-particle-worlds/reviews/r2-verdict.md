blocking: 0

# r2 verdict — particle-worlds

Head: 238f88cc52e85c4c05b1ed1dd0ce7eece9852881   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-decision clause)   Independent read written before reading fixes: yes

Reading order followed: checklist → design note (all 1707 lines, including the r2 amendment) →
the tree at 238f88cc and CI runs 32968643250 / 32968614588 (independent notes formed, F1–F6 fix
commits read as diffs) → r1-verdict.md (context the brief supplies) → r2-review.md → r2-fixes.md
last, audited against my own read. Not contaminated.

The r2 review was written at `b6b4401`; six commits landed since (`b6b4401..238f88cc`, one per
finding). Every finding below is re-verified at 238f88cc. Local HEAD, the checkout's `main` and
`origin/main` (via `gh api repos/Metta-AI/cogame-particle-worlds/branches/main`) all agree on
238f88cc.

---

## Standing blocking findings

None. The review's one blocking finding is fixed at head and my independent checklist pass
found no new one.

---

## Refuted

### F1 — deadline stop mutates hashed state outside `sim.step`; playback cannot re-derive it (blocking, item 2)  → REFUTED at head (fixed by 13c66d75)
The finding was true at `b6b4401` (it is r1's B1, and I re-confirmed every premise from the r1
verdict's trace). At 238f88cc it no longer reproduces:
- **Live side** — `src/mpe/server.nim:1409-1424`: the stop is *recorded first, then applied*:
  `replayWriter.writeChat(tickTime(sim.tickCount), 0, sim.wallClockStopRecord())` then
  `sim.applyWallClockStop()`, at the top of the iteration, before the same iteration's step and
  its `writeHash` (`server.nim:2077`). The old in-place `bankRound`/`finishGame` block is gone.
- **One implementation, both sides** — `src/mpe/sim.nim:2998-3047`: `wallClockStopRecord`
  (`{"k":"stop","reason":…,"rule":…,"tick":…}`), `isWallClockStopRecord` (substring pre-filter,
  then a real `parseJson` check of `k == "stop"`, so a directive `note` containing the word
  cannot spoof it and a crafted record falls through to the feed), and `applyWallClockStop`
  (sets `endReason`/`endRule`, `bankRound(sim.gameTicksElapsed(), EndRuleWallClock)` if
  `Playing`, `finishGame(Red, isDraw = true)`).
- **Playback side** — `src/mpe/replays.nim:412-421`: `applyReplayEvents` routes the `stop`
  record to `sim.applyWallClockStop()` instead of `pushFeedDirective`, and `stepReplay`
  (`replays.nim:516-527`) applies chats *before* `sim.step` and checks the hash *after* — the
  exact order the live loop uses, so the stop tick's recorded hash re-derives.
- **Test** — `tests/test_replay.nim:195-265` "a DEADLINE-ended episode re-derives frame by
  frame, stop tick included": records a `wallClockBudgetSeconds = 10` episode through the real
  `openReplayWriter` with the stop written and applied exactly as `server.nim` does
  (`tests/test_replay.nim:66-71`), asserts exactly one `stop` record in the bytes, drives
  `parseReplayBytes` + `initReplayRuntime` + `advanceReplayFrame` over the whole chain, asserts
  `hashMismatchTick == -1`, **and** asserts playback ends where the recording ended
  (`phase == GameOver`, same `winner`/`isDraw`/`roundsPlayed`, same banked permille per seat,
  re-derived results doc with `reason == "deadline"` and identical `scores`/`roundScores`/
  `roundEndRules`) — which rules out a replay that passes the hash check by silently staying
  `Playing`.
- **CI** — the test ran green twice (debug + release) at head: run 32968643250 log,
  `[OK] a DEADLINE-ended episode re-derives frame by frame, stop tick included` (log lines 1349,
  1384); the F1-only commit 13c66d75 also completed green on its own run 32968614588.
- **GameVersion** — bumped 1 → 2 (`sim_types.nim:21`), with the rule change in the headline;
  the replay header carries `gameVersion: GameVersion` (`replays.nim:148`), so a GV1 viewer
  refuses a GV2 recording rather than re-simulating the stop tick wrong. `docs/PROTOCOL.md:196,
  200-205` documents `stop` as the one load-bearing chat record; the "presentation only" claim
  is corrected rather than left contradicting the code. Item 2 now passes for both endings the
  design accepts.

### F2 — `hold` steers to the round's spawn point (non-blocking)  → fixed at head (8d7da32)
`src/mpe/control.nim:363-379` adds `anchorHold` (stamps `holdX/holdY` from the particle's
current centre); `src/mpe/server.nim:1969-1970` calls it for every `hold` order as the turn's
directive is installed. `tests/test_control.nim:180-216` displaces a particle ~400 px, holds
two whole turns of real compiled masks, and asserts it brakes there (`goalFor == here`, ends
within `2 * ArriveRadius`, never returns to the spawn ring) — `[OK] hold brakes where the order
landed, not back at the round's spawn`, twice in the head run. The anchor is unhashed and feeds
mask compilation only (live side of the determinism boundary), so no GameVersion implication —
correct. Was never a checklist violation; now also not a divergence.

### F3 — docs claim a roundcard cross-check that playback does not perform (non-blocking)  → fixed at head (7b7b6f3)
`docs/PROTOCOL.md:208-212`, `decide.nim:258-266` (roundcardRecord docstring) and the design
note (`design.md:1086-1088` and the in-repo plans copy) now all say playback drops the record,
`replay_summary.py` is its only reader, and divergence is caught by `gameHash` instead. Matches
the code (`replays.nim:418-423` + `sim_state.nim` `pushFeedDirective` accepting only
`directive`; the stop is the one exception). Documentation-only, as the review said.

### F4 — budget guard reserved 2 × turnBudget, not 2 × (spacing + budget) (non-blocking)  → fixed at head (8faa552)
`src/mpe/decide.nim:391-394`: `turnSeconds = (turnSpacingMs + turnBudgetMs + 999) div 1000`,
reserve `2 * turnSeconds` → threshold moves from `elapsed ≥ 671` to `≥ 653` at the shipped
9000/10000, restoring the ~2×-worst-turn margin over the 690 s stop that the expression claims.
Test comment updated only (the fixture's floor is 0, so its arithmetic was already right);
design note §Budget guard corrected. Item 5 was never falsified (every wait bounded); now the
margin is real as well as nominal.

### F5 — landmarkMargin validator is necessary-only (non-blocking)  → documented at head (7092f9d)
`src/mpe/sim_config.nim:793-808`: the comment now states it measures the longer axis only and
why sufficiency is deliberately not attempted (every downstream outcome is bounded:
`MaxLandmarkDraws` cap, RNG-free lattice sweep, sim-guard fault). Matches the code.

### F6 — stale `DefaultTurnSpacingMs = 5000` residue (non-blocking)  → fixed at head (238f88cc)
The 5000 constant is deleted from `sim_types.nim`; `sim_config.nim:75` `defaultGameConfig` now
takes `DefaultParticleTurnSpacingMs` (9000), the value every shipped variant, the schema default
and the engine test already carried. One in-code answer remains.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run **32968643250** at 238f88cc, conclusion `success`; jobs `test` / `docker-smoke` / `wasm-viewer` all `success` (queried via `gh run view --json jobs`); intermediate run 32968614588 at 13c66d75 also `success`. `git log -p --since="2026-08-26T05:56:00Z" -- tests/` read hunk by hunk: all changes additive except the three previously adjudicated replacements (`99dcaab` whole-identifier float grep — the `check` stays, only `isqrt` exempted; `66d1099` `>= 4` → `== 4` + per-seat uniqueness — a tightening; `b6b4401` window-count → record-stream assertion — I re-verified at `decide.nim:540` that `attemptsSpent[seat] = attempt + 1` is set only inside the per-attempt `except` after `makeRequests` ran, so `attempt: 2` proves issuance) and this round's two new test cases + one comment line (`8faa552`). No skip/xfail, no deleted test file, no widened tolerance |
| 2 replay re-derivation | PASS | `tests/test_replay.nim:160-189` (complete path, every hash) and `:195-265` (deadline path, stop tick included, end-state equality) both `[OK]` in debug and release at head; viewer derives from the same re-derivation (`replay-viewer/mpe_replay.nim` imports `src/mpe/sim`; `replay_runtime.nim` builds packets from the re-simulated sim); native↔wasm gate printed `ok: loaded replay.json, advanced 300 frames` (log line 5920) |
| 3 static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}` (parsed); `tools/build_replay_viewer.sh` mode 100755, asserted `-f`/`-x` in `ci.yml:237-248` and invoked by path; worker's only network call is the replay URL fetch; `/client/replay` remains the starter-inherited live dev route, ruled non-blocking in r1 — unchanged at head |
| 4 both name spaces | PASS | `tests/test_identity_privacy.nim` sentinel from both sides, green at head; CI smoke scorebug carries real names (`"scorebug":"○ P1 GOOD 0.711 …"`, log line 5850); seat views built from `cogAlias` only (`decide.nim`) |
| 5 degrade-never-hang | PASS | whole-second transport deadlines validated (`sim_config.nim:739-757`, `attempt1Ms + retryMs <= turnBudgetMs`); monotonic `turnBudgetMs` restarted after the bounded floor sleep (`decide.nim:439-458`); guard now reserves 2 × (spacing + budget) (`decide.nim:391-394`); `lobbyJoinTimeoutTicks`; bounded sampler (`field.nim` `MaxLandmarkDraws` + lattice sweep) plus the necessary-condition config rejection (`sim_config.nim:808-815`); 690 s stop (`server.nim:1409-1424`) ≤ 720 = 60 % of 1200, asserted by `tests/test_manifest.nim:133-139`; bounded shutdown grace |
| 6 num_agents | PASS | 4 in all five variants, `certification.game_config`, `config_schema` (integer 4..4 default 4), `len(certification.players) == 4` (parsed); `docker_smoke.sh:106-152` enforces all four invariants + independent `SMOKE_SEATS` cross-check, each `SEAT-COUNT FAIL:`-prefixed, before any container starts; `grep -c "SEAT-COUNT FAIL"` over run 32968643250's full log = **0**; smoke printed `game=particle-worlds seats=4` and `smoke OK: seats=4 results=878B replay=31462B reason=complete` |
| 7 scripted baseline full episodes | PASS | `tests/test_control.nim` legality sweep (own id, enum intent, in-box target, one-rune symbol, never A/C/Up+Down/Left+Right) + all-scripted 4-round episode (`:218-279`: completes, cover ≥ 80 %, crypto Bob on goal, drifter beats beeline at the pinned seed); `tests/test_endings.nim:50-63` `reason == "complete"`; grid-harness clause ruled satisfied-in-substance in r1 (measured in-code rationales + the comparative bar) — unchanged at head, same ruling |
| 8 LLM reply handling | PASS | tolerant parse (fences, prose prefix, id-keyed cogs, numeric strings — `directives.nim` + 13 repair cases green); retry exactly once (`decide.nim:474` `attempt < 2`), throttle fail-fast skips it (`:546-553`); one authoritative `fallback` record per seat-turn stamped with attempts actually spent (`:556-575`), countable against `results.fallbackTurns` |
| 9 rune-safe truncation | PASS | single shortening primitive `truncateRunes` (`runeLen`/`runeSubStr`); caps 160/48/200/900/4000 routed through it; `tests/test_directives.nim:109-145` 4-byte emoji sitting on the cap → valid UTF-8, round-trips; end-to-end non-ASCII label + note forced through `replay_summary.py` strict-UTF-8 in `tests/test_replay.nim` |
| 10 manifest validates | PASS | parsed at head: `game.docs.readme` text (7 207 chars) + 3 pages each `{id,title,content:{type:"text",value}}` (12 036 / 13 769 / 6 595); `game.protocols` both `player` and `global` in object form (both 13 769 chars — regenerated by `build_manifest.py` after the F1/F3 doc edits; `ci.yml` runs it with `--check`, green); `results_schema` 22 keys `additionalProperties: false` |
| 11 viewer legible 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` (`replay_broadcast.html:4152-4157`); labels hidden under `.tiny` (`:4197-4198, 4254, 4290, 4323-4325`); breakpoint `boardW <= 620` is the starter's line (`:4093`); the fixture gates 360 px directly |
| 12 release order and scaffold | PASS | `coworld-release.yml`: build manifest (:153) → certify (:167, `--timeout-seconds 300` at :178) → upload-policies (:210, comment pins the ordering) → upload-coworld (:308) → secret put (:346); all three workflows present; `docker_smoke.sh` + `build_replay_viewer.sh` both 100755; `policies.json` = 2 × `PLAYER_PROMPT` champions (cipher carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) + 2 × `PLAYER_SCRIPTED` fillers; the three-name placeholder grep over the five files returns nothing → gate exits 0 (run in the sandbox, exit 1 from grep) |
| 13 viewer executes | PASS | run 32968643250 `wasm-viewer` green **including** "Load the bundle in a real browser": `{"loaded":true,"ms":1562,…}` and `soak: 12s of playback kept advancing ("0 / 1035" -> "240 / 1035" -> "288 / 1035")` (log lines 5850-5851), against the replay docker-smoke produced (`needs: docker-smoke`, `ci.yml:224`; artifact sha256 matches upload, log lines 3939/5551); no `continue-on-error` anywhere in `ci.yml`; `data-replay-loaded` set in the shell's own `'loaded'` branch (`static_replay.js:158-162`), `data-replay-error` in `showFailure()` (`:14-20`); `config.nims` non-MODULARIZE `_mpe_*` exports + worker `Module.onRuntimeInitialized` + `importScripts(...'./mpe_replay.js')` — one starter, diff-verified rename-only against `/workspace/starters/coworld-ctf` |
| 14 chrome is the starter's | PASS | `chrome_common.js` and `broadcast_core.js` each byte-identical to the starter's modulo the single `CTF_WIRE → MPE_WIRE` identifier (diffed directly; patch recorded in the design note amendment; sha256-pinned in `tests/test_viewer.nim`); `replay_broadcast.html` is the starter's 4 660-line page (fork: 4 694) with one appended block under the banner at `:4125`; pre-banner diffs are the mandated ctf→mpe rename sweep plus exactly the note's removal list (`#viewpanel`/zoom/minimap CSS, hearts/flags, the paintball block wholesale, dead beat kinds) and the in-place PB→MPE retarget of the starter's own inline game script the note describes; transport rules verified: `relayout()` writes `--band`/`--topband`/`--hudscale` on `:root` (`:4092-4098`), `#endcard { bottom: var(--band…) }` + `#endcard.on` + seek dismissal (`:1906`), beats are labelled `<button>`s via `mpeBeat` (`:4419-4430`) with CSS for exactly the five emitted kinds (`:4336-4357`) and no others; `#viewpanel`/`#minimap`/`#zoombar` ids absent (test-pinned, `tests/test_viewer.nim:42-61`) |
| 15 drawn strings fit | PASS | `--strict-text-bounds` on both smoke steps (`ci.yml:336, 371`); the worst-case renderer fixture drives the **shipped** page with a full-cap 160-rune note on all four seats + non-silent symbols + populated crypto panel at 360/620/1280 px and self-checks its strings are full-length; CI printed `fixture canvas_text: total=302 never_inside=0 outside=0` (log line 5905) with `ci.yml:375-390` asserting `total > 0` and `never_inside == 0`; the replay run's `canvas text: 0 drawn` is treated as evidence of nothing, which is exactly why the fixture exists; note rows wrap inside the killfeed's reserved band (`.mpe-note-row`, `:4377-4384`) |
| simultaneous batch | PASS | one `RequestBatch` per turn for all open seats, issued via a single `client.curl.makeRequests(batch, …)` (`decide.nim:485-506`) — no per-seat call site anywhere in `src/`; `[OK] all four seats' calls go out in ONE parallel batch` twice (debug + release) in the head run (log lines 1113, 1231) |

---

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `13c66d75`, GV 1→2, deadline test both modes, green on its own run | all confirmed from the diff, the test source, and both run logs (32968614588 + 32968643250); record→apply ordering exact on both sides; `isWallClockStopRecord` spoof-safe | yes |
| F2 | fixed, `8d7da32`, anchor stamped at install, no GV implication | confirmed (`control.nim:363-379`, `server.nim:1969-1970`, test green twice); un-hashed, playback never reads it — GV reasoning correct | yes |
| F3 | docs corrected in all three claim sites | confirmed (`PROTOCOL.md:208-212`, `decide.nim:258-266`, in-repo plans copy); manifest regenerated (`--check` green) | yes |
| F4 | reserve = 2 × (spacing + budget), threshold 671→653 | confirmed (`decide.nim:391-394`); steady state unchanged | yes |
| F5 | comment states necessary-only + why | confirmed (`sim_config.nim:793-808`) | yes |
| F6 | 5000 constant deleted, base config takes 9000 | confirmed (`sim_types.nim`, `sim_config.nim:75`) | yes |

Discrepancies found in the audit, none material: (a) the fixes file says "the pushed shas differ
from the local ones" — they do not: local HEAD, the checkout and `origin/main` all read
238f88cc, and run 32968643250's `headSha` matches it exactly; (b) the NOTED div-by-zero risk in
`applyWallClockStop` → `roundPermille` is already guarded in the code the fixer shipped
(`scoring.nim:148-149` `if ticks <= 0: return 0`; `coverPctForRound` and `tagRoundPermille`
guard likewise), so the noted hazard does not exist — the note overstates, which is the safe
direction. The "no test weakened" claim was checked against the full `git log -p -- tests/` for
the round window and holds.

---

## Non-blocking observations (judge)

- The starter's pinch/ctrl-wheel zoom gesture handlers survive in the page
  (`replay_broadcast.html:3895, 3912, 3967`) while `#viewpanel` and all its wiring are removed.
  r1 ruled this non-blocking (`broadcast_core.js` clamps `minZoom = 1`, `panBy` no-ops at fit);
  unchanged at head, same ruling. Deleting them remains a strictness option.
- `fault`-ended replays end playback without reaching `GameOver` (the fault path breaks before
  the hash write, so no unre-derivable hash exists and item 2 is not violated). A `stop`-style
  record would give a fault replay an end segment; the fixer's NOTED list records the same.
- The float-free grep covers `field/motion/scoring/beliefs`; `control.nim` sits on the live
  side of the determinism boundary (masks are recorded), and r1 verified it float-free by direct
  grep. Not a checklist item.

---

## Blocking findings, one line each

(none)

BLOCKING: 0
