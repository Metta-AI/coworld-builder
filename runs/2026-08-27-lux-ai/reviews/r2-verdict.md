blocking: 0

# r2 verdict — lux-ai

Head: `88cc3f751606cb5f48bc535b349dc23b1339c4a1` (`main`; CI run **33096195543**, conclusion
**success** — verified via `gh run view --json headSha,conclusion` → `headSha 88cc3f75…`,
`conclusion success`; jobs `test` / `docker-smoke` / `wasm-viewer` all green)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
simultaneous-decision batch rule)
Independent read written before reading fixes: **yes** — I read the checklist, the design note,
the repo at head, the r2 review, and completed my own checklist pass before opening
`r2-fixes.md`. I did not read `r2-fixes.md` early.

The r2 review's blocking finding B1 was written against `66b5d3b`; four fix commits landed
after it (`c74b230`, `49ca7e5`, `47f5cf0`, `88cc3f7`). Verdicts below are at the current head.

---

## Standing blocking findings

None.

---

## Refuted / resolved

### B1 — playback ignored the recorded lobby length → **FIXED AT THIS SHA** (verified in code, not from the fixer's report)

The finding was valid at the review's sha and is genuinely fixed by `c74b230`.

- **The defect is gone from the source.** `src/lux/replays.nim:132-136` (`simFromReplay`) now
  restores only `name`/`slot` from the join records:
  ```nim
  for join in data.joins:
    let seat = int(join.player)
    if seat in 0 .. 1:
      result.seats[seat].name = join.name
      result.seats[seat].slot = join.slot
  ```
  — the two lines that set `joined = true` / `connected = true` at construction are deleted.
  `applyRecordsAt` (`replays.nim:180-184`) now seats each player at the tick its join record
  was written, *before* the input stream:
  ```nim
  for join in player.data.joins:
    let seat = int(join.player)
    if seat in 0 .. 1 and tickOfTime(join.time) == tick:
      sim.seats[seat].joined = true
      sim.seats[seat].connected = true
  ```
  With seats unjoined until their recorded tick, `sim.step`'s `Lobby` auto-start
  (`sim.nim:166-169`: `joined and sim.tickCount >= sim.config.startWaitTicks`) can no longer
  fire at tick 48 for a lobby that ran longer; it fires at `max(startWaitTicks, joinTick)` —
  the same tick the recorded `InputStart` arrives and the same tick the live loop began
  `Playing` (`server.nim:484-497`). The recorded lobby hashes (`gameHash` in `Lobby` mixes
  `(-1, tickCount)`, `sim.nim:188-193`) now match tick for tick. The wasm viewer takes the
  identical path (`replay-viewer/lux_replay.nim:69` → `initReplayRuntime` →
  `simFromReplay`/`stepReplay`), so the fix reaches the browser.

- **The new test is strong — checked against the coordinator's specific concern.**
  `tests/test_lux_replay.nim:150-180` *"a lobby LONGER than startWaitTicks re-derives frame by
  frame"* records via `recordWithLobby` (`:65-111`), a line-faithful transcription of
  `server.nim`'s own loop order — join records written at the tick the seat appears (mirroring
  `syncSeats`, `server.nim:358-372`), one lobby hash per waiting tick (`server.nim:499`),
  `InputStart` at the tick `Playing` actually began (`server.nim:496`), then
  hash-before-step during `Playing` and hash-per-tick at `GameOver`, exactly as
  `server.nim:504-518`. It does **not** zero `startWaitTicks`: it uses `defaultGameConfig()`
  and asserts `check config.startWaitTicks == 48` (`:162`) — the shipped value — with seats
  joining at ticks **0, 49 and 120**, two of which make the lobby strictly longer than 48.
  Re-derivation runs with `mismatchQuit = true` (any divergent tick raises, so the WHOLE chain
  is asserted, not just the final board) and additionally checks
  `replayStartTick() == recorded.gameStartTick`, the final `gameHash()`, turn count, end rule
  and both city-tile counts (`:170-180`). I traced the revert by hand: with the old
  construction-time seating, playback enters `Playing` at 48 while the recording holds lobby
  hashes (`mixHash(-1, tick)`) through tick 119 — first divergence at tick 49, `mismatchQuit`
  raises, the test fails. It is a real gate.
  It is not literally `runServerLoop` (that requires mummy sockets and wall-clock time), but
  every record-order property the live loop has and the defect depends on is reproduced, and
  the r2 reviewer's own executed repro used this identical recording shape to demonstrate the
  bug pre-fix — so the fixture demonstrably exercises the defect path at the shipped
  `startWaitTicks`.

- **CI corroborates**: run 33096195543 `test` job logs show
  `[OK] a lobby LONGER than startWaitTicks re-derives frame by frame` in every pass, and the
  `Native <-> wasm hash gate` re-derived docker-smoke's episode over its whole 408-tick span
  (`advancing 408 frames (the replay's whole recorded span)` … `ok: … advanced 408 frames`).

- **No recording-side change**: writer bytes are untouched, the hash mix is untouched,
  `GameVersion` stays `"1"` — correct, since the fix is playback-only.

Checklist item 2 now holds for any join timing. **Resolved; counts zero.**

### N1 — `.tiny` five-line band inert → fixed at this sha (was advisory)

`client/replay_broadcast.html:1868-1871`: the `#stage.tiny` rule now re-declares both
`--lux-note-lines: 5` **and** `--lux-say-band: calc(var(--lux-note-lines) * 1.35 * …)`, so the
band resolves with five lines inside `.tiny` (custom properties substitute at the declaring
element's computed-value time — the re-declaration is the correct mechanism).
`tests/test_lux_viewer.nim:244-257` pins both declarations inside the `#stage.tiny {` block.
The page still regenerates byte-identically from the starter mount — I ran
`python3 scripts/fork_broadcast_page.py /workspace/starters/coworld-ctf /tmp/regen.html` and
`diff` against the committed page: identical — so item 14's provenance survives the edit.

### N2 — pre-scan verdict discarded → fixed at this sha (was advisory)

`src/lux/replays.nim:340-345`: `runScan` now carries `scanner.hashValidationFailed` /
`hashMismatchTick` onto the player after the whole-episode walk. The `sim_fault` test asserts
`player.hashValidationFailed` and a non-negative mismatch tick **before** the first
presentation frame, and that playback later reports the same tick
(`tests/test_lux_replay.nim:206-220`).

### N3 — wasm gate hash-checked a prefix → fixed at this sha (was advisory)

`.github/workflows/ci.yml:358-379`: the frame budget is read from
`replay_summary.py … ["tickCount"]` instead of the pinned 300, and the step fails loudly on a
missing replay. `tools/wasm_replay_smoke.cjs:89-106` checks `lux_mismatch_tick()` both after
load and after the loop. Head-run evidence: `advancing 408 frames` / `ok: … advanced 408
frames` — the full recorded span including the settle tick.

### N4 — 429 rotates the Bedrock ladder → correctly disputed; no defect

`src/lux/llm.nim` (two candidates at `:83-84`; 429 path rotates via `tryNextBedrockModel`, and
only a 429 with nothing left to rotate to sets `throttled`, which `decide.nim:266-271` reads
as "skip the retry"). This is what the design note specifies verbatim
(design.md: "`tryNextBedrockModel` on 401/403 … and on 429"). Every wait stays bounded by
`attempt1Ms`/`retryMs`. Not a finding.

### N5 — r1's declined advisories unchanged → not on the checklist

`episodeFinished` unreferenced by the server loop, cart hand-off before the night policy,
`build:"city"` skipping the research check, whole-reply cap in runes — all re-verified present
at head, none maps to a checklist item. Advisory residue only.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run 33096195543 conclusion `success` on `main` at `88cc3f75…` (cited above). `git log -p --since=2026-08-27T12:45:00Z -- tests/`: six commits touch tests. Only two remove any line: `27d10f6` replaces `check wallClockBudgetSeconds <= 720` with the *stronger* `worst=468s<660` chain plus the overshoot bound `660+13<=720` (test_lux_engine.nim:32-58); `7e8a89e` replaces the tautology `check (recovered or true)` with `reason.startsWith("no JSON object in reply")` + a parsing survivor case (test_lux_directives.nim:84-105). No skip/xfail/disable/deleted test file anywhere in the range; `c74b230`/`49ca7e5`/`47f5cf0`/`66b5d3b` are pure additions. |
| 2 replay re-derivation | **pass** | Fix verified under B1 above. `record`/`recordWithLobby` reproduce the server's record order; `replayCleanly` uses `mismatchQuit=true` over the whole span (test_lux_replay.nim:113-130); tests cover `full_time` (:136), long lobby ×3 (:150), `wall_clock` incl. the stop turn (:182), `sim_fault` chain-catch (:191). Viewer derives from the same re-derivation: `replay-viewer/lux_replay.nim:47,69,102` → `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket` — the identical procs the native replay route uses (`server.nim:462-466`). Wasm gate covers the full span (408 frames, run log). |
| 3 static viewer | **pass** | `coworld_manifest_template.json`: `game.replay_viewer == {"bundle":"static-replay-viewer"}`, no top-level `replay_viewer`. `tools/build_replay_viewer.sh` exists, mode 100755, wired as the build hook (asserted executable in ci.yml:259-270 and test_lux_viewer.nim:332). Worker fetches only `message.replayUrl` (static_replay_worker.js:113) — no other network call in the shell/worker. No pod replay viewer declared anywhere in the manifest; `/client/replay` exists only as the starter's local-dev route in `server.nim`, exactly as the design note declares. |
| 4 both name spaces | **pass** | `roster.nim:46-52` `cogAlias` untouched (RED-alpha/BLUE-alpha); observation carries only aliases (`sim.nim:409`); `broadcast.nim:88-96` roster ships `name` (real) + `alias` (anonymous), both. CI: `[OK] the observation names only the two anonymous aliases`, `[Suite] lux identity privacy` green; smoke scorebug shows real name + alias (`Red RED-ALPHA …`). |
| 5 degrade-never-hang | **pass** | Every wait bounded: `attempt1Ms` 7 s / `retryMs` 3 s handed to `CURLOPT_TIMEOUT` (decide.nim:221-238), turn budget checked before each attempt (:216), `attempt < 2` (:213), rate guard (:180, cap 28/60 s), budget guard (:154-164), lobby capped at `lobbyJoinTimeoutTicks` 2400 (server.nim:486-487), wall-clock stop at 660 s checked top-of-loop (:475), 20 s bounded shutdown grace (:538). Arithmetic asserted by test: worst turn = 6+7 = 13 s, 36×13+3+100+20 = 591 < 660, and 660+13 ≤ 720 (test_lux_engine.nim:32-58). All three variants ship `wallClockBudgetSeconds: 660`. Player container: bounded dials (240×500 ms), bounded redials, exit 0 on dead socket (lux_ai_player.nim:68-127). |
| 6 num_agents | **pass** | `num_agents: 2` inside `game_config` of all three variants and of `certification.game_config`; absent at every variant top level; cert players == cert gc players == 2 (verified by script over the manifest). `docker_smoke.sh:107-151` enforces all four invariants pre-container with `SEAT-COUNT FAIL:` prefixes; `SMOKE_SEATS` default `2` (:57) is the scaffold-substituted second declaration and is cross-checked (:146-151). `grep 'SEAT-COUNT' over the full run-33096195543 log`: only the test job's `[OK] the four SEAT-COUNT invariants…` lines — **zero `SEAT-COUNT FAIL`**. |
| 7 scripted baseline full episodes | **pass** | test_lux_baselines.nim:106-116: full scripted `duel` at the pinned seed → `reason == erComplete`, `endRule == erlFullTime`, forester ahead, both sides alive ≥ 6 nights. Legality: test_lux_micro.nim:109-166 (both baselines over 300 worlds + 200 random valid directives + a whole scripted episode — no illegal action ever). Tuning: `tools/tune_baselines.nim --check` is its own CI step (ci.yml:104-108) and test_lux_baselines.nim:118 pins the shipped constants to `tools/ci/baseline_tuning.json`. |
| 8 LLM reply handling | **pass** | `extractJsonObject` (fence-tolerant, outermost-brace) feeds `parseDirective` (decide.nim:244-252); exactly one retry (`attempt < 2`, :213) with the throttled fail-fast (:266-271); second failure → forester via `foresterFor` — the same proc the filler uses (asserted, test_lux_baselines.nim:96) — with a `fallback` chat record and `fallbackTurns` counted (:274-289); "falling back" echoed for phase 60's grep (:288). Directive-parsing repair matrix in test_lux_directives.nim incl. capped-9 KB classified error. |
| 9 rune-safe truncation | **pass** | `directives.nim:75-82` `truncateRunes` via `runeLen`/`runeSubStr`; applied to note/policy label/detail/prompt/reply. Tests: emoji at the 160/161 boundary (test_lux_directives.nim, "cuts on the RUNE"); every cap filled with 4-byte emoji round-tripped through `replay_summary.py` under strict UTF-8 with a lone-surrogate check (test_lux_replay.nim:302-367). |
| 10 manifest validates | **pass** | `game.docs` = `readme` (`{"type":"text","value":…}`, 6121 B) + `pages` (3 × `{id,title,content:{type:"text",value}}`); `game.protocols` carries both `player` and `global` as objects (verified by script). `config_schema`: every array has minItems/maxItems, `additionalProperties:false`; `results_schema` closed with 27 keys. |
| 11 legible at 360 px | **pass** | `client/replay_broadcast.html:1779-1784`: `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`; `@media (max-width: 640px)` hides `.tiles-label`/`.lux-alias` (:2055-2058). Fixture measured at 360 px: `short 0, clipped 0, outside 0` (run log). |
| 12 release order and scaffold | **pass** | `coworld-release.yml` step order verified by line: build manifest (:159) → certify (:173, `--timeout-seconds 300`) → upload the policies (:217, with the "BEFORE upload-coworld" comment) → upload-coworld (:315) → put secret (:353, "AFTER upload-coworld") — all in one job on a manifest built the same run. Three workflows present. `docker_smoke.sh` mode 100755. `policies.json`: 4 distinct policies — 2 × `PLAYER_PROMPT` champions + `forester` + `prospector` fillers, champion #2 `lux-ai-nightwatch` carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Placeholder grep over the five files: **exit 0** (ran it; clean). |
| 13 viewer executes | **pass** | `wasm-viewer` `needs: docker-smoke` (ci.yml:246); no `continue-on-error` anywhere in the workflow; the `Load the bundle in a real browser` step ran in run 33096195543 against docker-smoke's `episode.replay`: `{"loaded":true,"ms":376,…}`, soak advanced `0/359 → 192/359 → 241/359`. Markers: `data-replay-loaded` set in the worker-`loaded` branch (static_replay.js:161), `data-replay-error` in the failure path (:14-20) — both the shell's own code paths. Link flags and bootstrap are the one starter's matched pair: `config.nims` diff vs starter = identifier renames only (no MODULARIZE; `-o lux_replay.js`, same EXPORTED_FUNCTIONS shape), worker sets `Module.onRuntimeInitialized` (static_replay_worker.js:188) with `importScripts(wire_constants, broadcast_core, lux_replay)` (:239) — internally consistent, and pinned by test "the emscripten link flags and the JS bootstrap are the matched pair" (test_lux_viewer.nim:310). |
| 14 chrome is the starter's | **pass** | `chrome_common.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js` (diff empty; sha256 `7ace7287…` both). `broadcast_core.js` also byte-identical (diff empty). `replay_broadcast.html` regenerates **byte-identically** from the starter via `scripts/fork_broadcast_page.py` (I ran it against the starter mount: identical) — the 124 KB vs 234 KB size delta is exactly the enumerated deletions (FPV pipeline ~1100 lines, viewpanel cluster, ctf scorebug internals, paintball block), each named in the script with the design-note reason; the lux block is appended under the `LUX-AI additions to the inherited coworld-ctf chrome` banner (:1753). Transport rules: `relayout()` sets `--hudscale`/`--topband`/`--band` on `document.documentElement` (:1719-1726); `#endcard` keeps `top: var(--topband)` / `bottom: var(--band)` (:657-658) and every non-gameover frame removes `.on` (:1540) so any seek dismisses it; beats are labelled `<button>`s via `luxBeat` (never chrome_common's `markBeat`; :2104-2126) with CSS for exactly `{dusk, research, citylost, end}` (:2006-2021). `#viewpanel`/`#minimap`/`#zoombar`/`#fpv*`/`#povBadge` appear only in comments; test "the dropped elements appear nowhere" pins it. |
| 15 every drawn string fits | **pass** | This viewer's text is DOM, so the canvas smoke's `canvas_text` is structurally `total: 0` (run log: `0 drawn`) and gates nothing — item 15's own rule then requires the worst-case renderer fixture, which ships: `tools/ci/renderer_fixture.html` loads the **shipped** `index.html` in iframes, shims only the wasm entry (after the script it replaces, with a throw if the anchor vanishes), feeds a full-cap 160-rune note on both seats plus fuel strip/research/citylost/deep night, at 360/620/1280 px; own ci.yml steps (`Worst-case chrome fixture` :388, `The commander line fits its band` :416) parse `LUX-TEXTFIT` and fail on `short`/`outside`/`clipped`/`chrome_off_stage`/missing measurement or `note_runes != 160` (the fixture asserts its own strings are full-length). Head-run output: `text fit: {"chrome_off_stage": 0, …, "clipped": 0, "note_runes": 160, "notes": 12, "outside": 0, "short": 0, "widths": 3}`, `commander band OK: 48 boxes measured, 12 full-cap notes inside #stage at 360/620/1280 px`. The commander band is reserved in the layout, sized from `MaxNoteRunes` (pinned to the Nim const by test_lux_viewer.nim:227), now including the `.tiny` five-line re-declaration. |
| batch rule (simultaneous decisions) | **pass** | One `RequestBatch`, every open seat posted into it, one `makeRequests` per attempt (decide.nim:223-238); the source contains exactly one `makeRequests` call site, structurally asserted by test_lux_engine.nim:170-187 ("BOTH seats go out in ONE parallel batch, never sequentially"). |

---

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, `c74b230`; test records via the server's own loop shape at shipped startWaitTicks 48; revert fails with mismatch at tick 49 | Read the source change and the test independently before opening the report; traced the revert failure by hand; CI shows the test `[OK]` | yes |
| N1 | fixed, `49ca5e5`→`49ca7e5`; page regenerated, not hand-edited | Re-declaration present at html:1868-1871; regeneration reproduced byte-identically from the starter mount by me | yes |
| N2 | fixed, `47f5cf0` | Carry present at replays.nim:340-345; test asserts pre-frame verdict | yes |
| N3 | fixed, `88cc3f7` | ci.yml reads `tickCount` from the summariser; run log shows 408 frames advanced, mismatch gate after the loop | yes |
| N4 | DISPUTED, no defect | Design note asks for 429 rotation verbatim; bounds untouched | yes — dispute is correct |
| N5 | declined, out of scope | None of the four maps to a checklist item | yes |
| NOTED: `check_gameversion.sh` reads `src/ctf/sim_types.nim` | left alone | Confirmed: `tools/ci/check_gameversion.sh:30` `CONST_FILE="src/ctf/sim_types.nim"` — the starter's path, so the documented invocation always fails. Not invoked by any workflow (only its existence/exec bit is tested), and GameVersion discipline is not an acceptance-checklist item | yes — see non-blocking observations |

---

## Non-blocking observations

- **`tools/ci/check_gameversion.sh:30` still points at the starter's `src/ctf/sim_types.nim`**,
  so the GameVersion collision guard AGENTS.md documents is inoperative (it always exits 1 with
  "could not read GameVersion"). No workflow invokes it, so CI is not weakened, and no checklist
  item names it — but the one-line retarget to `src/lux/sim_types.nim` should land before this
  script is ever relied on.
- `tests/helpers.nim` still sets `startWaitTicks = 0` in `fixtureConfig` for the other replay
  fixtures. Harmless now that the dedicated lobby test pins the shipped 48, but worth knowing
  when reading those tests.
- The r2 review's remaining "could not determine" items are settled or moot at head: the
  `.tiny` band is re-declared and measured on the shipped page (N1 fix); the 12×12 `skirmish`
  board fits wherever 16×16 does (`BOARD_ASPECT` is per-frame from the packet) though CI still
  only renders a `duel` replay; and the late-join hosted-replay question is moot because
  playback now honours any join timing.

---

No blocking findings stand at `88cc3f75…`. No `- [category] file:line` lines are required.

BLOCKING: 0
