# r1 review — 2026-08-23-firm (Metta-AI/cogame-firm)

Repo: `/tmp/cogame-firm` at `10fbf89660a896ec5fbd6fccee8618434ae2f193` (main, 4 commits).
Design note: `/workspace/coworld-builder/runs/2026-08-23-firm/design.md` (byte-identical to
`docs/plans/2026-08-23-firm-design.md` in the repo — verified with `diff`).
Starter: `/workspace/starters/cogame-bullwhip`.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + the
simultaneous-batch rule).
Files opened and read in full: `src/firm.nim`, `src/firm_player.nim`, `src/firm/types.nim`,
`src/firm/sim.nim`, `src/firm/llm.nim`, `src/firm/server.nim`, `replay-viewer/firm_replay.nim`,
`replay-viewer/config.nims`, `replay-viewer/index.html`, `replay-viewer/static_replay.js`,
`client/replay.html`, `client/chrome.css`, `client/renderer.js` (§§900–1692 + 1–100),
`tests/test_sim.nim`, `tests/test_bot.nim`, `coworld_manifest_template.json`,
`tools/ci/docker_smoke.sh`, `tools/ci/policies.json`, `tools/build_replay_viewer.sh`,
`.github/workflows/ci.yml`, `.github/workflows/coworld-release.yml`, `Dockerfile*`,
`compose.yaml`, `firm.nimble`, `README.md`. Files read: 26. Plus the CI logs for run
32672093025 (three jobs) via `gh api`.

No previous round exists (`runs/2026-08-23-firm/reviews/` was empty).

---

## Blocking

### F1 — No grid-tuning harness for the scripted baselines exists anywhere in the tree

- Where: absent — searched the whole repo
  (`grep -rni "grid" --include='*.nim' --include='*.md' --include='*.sh' --include='*.py' .`
  returns nothing outside `docs/plans/`); `tools/` contains only `build_replay_viewer.sh`
  and `tools/ci/{docker_smoke.sh,policies.json,viewer_smoke.mjs}`.
- Observed: the baseline constants are hard-coded literals in `src/firm/llm.nim:33-41`
  (`SteadyRun = 6`, `SteadyMaint = 3`, `NurseRun = 4`, `NurseMaint = 6`, `NurseBelow = 40`,
  `SteadyPayroll = 40`, `TaskmasterPayroll = 20`). Their justification in the design note is
  **analytic, not empirical**: design.md:193-196 derives run 6 / maint 3 from
  `3 × run` wear against `6 × maint` repair, and design.md:184-192 derives payroll 40 from the
  marginal-hour arithmetic. The design note never mentions a grid harness or a parameter sweep
  (searched: no occurrence of "grid", "sweep" or "harness" in design.md).
  What the repo *does* have is drift visibility, not tuning: `tests/test_bot.nim:128-138`
  echoes both baselines' manager/worker scores and surplus for four seeds each run, and
  `tests/test_bot.nim:89-107` asserts the behavioural envelope (`steady` holds condition
  within ±3 of 100; `taskmaster` drives a machine under 25 by shift 4).
- Checklist item: item 7 — "Scripted baseline plays full episodes legally. … **The baseline's
  parameters were tuned with a grid harness, not guessed.**"
- Why blocking: the first half of item 7 is satisfied (see *Traced and consistent*), but the
  second half cannot be verified from the tree or from CI evidence. There is no harness file,
  no sweep output committed, and no citation in the design note. Under the judge rule in
  `prompts/30-review-loop.md:59-61` ("A checklist item you cannot verify from the tree or from
  cited CI evidence counts as blocking"), the tuning half of item 7 is unverifiable as the tree
  stands.
- What would settle it: a committed harness (e.g. `tools/tune_baseline.nim` or a test that
  sweeps `SteadyRun × SteadyMaint × SteadyPayroll` over seeds and asserts the shipped tuple is
  the argmax), or a recorded sweep result in the design note / a `docs/` file that the
  constants can be traced back to.
- Note for the judge, in fairness: the starter `cogame-bullwhip` ships no grid harness either
  (`grep -rni grid` over `/workspace/starters/cogame-bullwhip` returns nothing), so this is an
  inherited gap rather than a regression introduced by this build.

**Nothing else in the diff falsifies a named checklist item.** Items 1–6 and 8–14 and the
simultaneous-batch rule are all verified affirmatively below.

---

## Non-blocking

### F2 — A per-seat LLM fallback is recorded on stdout but is **not** flagged in the replay's `scripted` field

- Where: `src/firm/server.nim:283`; `src/firm/llm.nim:681-684`; `src/firm/types.nim:75`.
- Observed: `decideAll` returns a bare `Decision` with no provenance field. When an LLM seat
  fails both attempts, `llm.nim:681-684` substitutes `scriptedAction(sim, seat, skSteady)` and
  logs `firm llm: seat <n> falling back to scripted decision` on stdout. Back in the server,
  `server.nim:283` computes
  `let wasScripted = scripted[seat] != skNone or client.disabled` — true only when the *seat*
  registered as a scripted policy or when the client is globally disabled — and passes that as
  the `scripted` argument to `applyMemo`/`applyWork` (`server.nim:297-301`). So a seat whose
  LLM decision fell back mid-episode is recorded in its `memo`/`work` event with
  `scripted: false`, even though `types.nim:75` documents the field as "memo/work: decided by a
  scripted baseline".
  The *other* fallback path — a decision rejected under the lock — **is** flagged: the
  belt-and-braces `except` at `server.nim:302-314` passes `true`.
- Design note: design.md:474 specifies exactly the stdout line the code emits ("Each fallback
  logs `firm llm: seat <n> falling back to scripted decision` on stdout"), so the *stdout*
  record is the design's stated mechanism and it is present and greppable.
- Checklist item 8 requires "the fallback is recorded so phase 60 can count it" — the stdout
  line does satisfy that literally, which is why I am not filing this as blocking. Recorded
  here because the replay-side flag disagrees with its own docstring, and phase 60 counting
  from the replay rather than the container log would undercount.
- Provenance: `server.nim:283` and `llm.nim`'s fallback shape are verbatim from the starter
  (`/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:296` is the identical line).

### F3 — `tests/test_bot.nim` documents a deliberate deviation from the design note's baseline assertion

- Where: `tests/test_bot.nim:109-139`.
- Observed: design.md:1086-1088 (Tests §2) requires "an all-`steady` table's manager score is
  strictly greater than an all-`taskmaster` table's on the same seed". The shipped test instead
  carries a signed NOTE at `test_bot.nim:110-117` stating the claim "does not, and cannot" hold
  (taskmaster's workers obey at run 10 regardless of pay, so its 20 % payroll keeps more
  revenue than steady's 40 %), and asserts two different things: every steady worker outscores
  its taskmaster counterpart (`test_bot.nim:126-127`), and total surplus
  `firmProfit + Σ workerNet` is strictly greater under steady (`test_bot.nim:139`).
- This is *not* a test loosened during this run: `git log --stat -- tests/` shows both test
  files were added in a single commit (`75efe8b`) and have not been touched since, so
  checklist item 1's "no test disabled, skipped or loosened during this run" is satisfied
  (see *Traced and consistent*). Recorded as a code-vs-design divergence, disclosed in-code.

### F4 — The stage sprites are not the ones the design note names

- Where: `data/` listing; `client/renderer.js:82-91`; `tools/build_replay_viewer.sh:51-55`;
  `scripts/art/generate_cog_sheet.py`.
- Observed: design.md:859-866 specifies bullwhip's four `soldier_<color>_front.png` plus a
  fifth `soldier_violet_front.png` produced by `tools/make_violet_cog.py` as a +250° HSV
  rotation, and states the renderer's existing `"soldier_" + color + "_front.png"` lookup
  resolves unchanged. The repo instead ships `data/cog_manager.png` and
  `data/cog_worker_{red,blue,green,yellow}.png` (128×128 RGBA, generated by
  `scripts/art/generate_cog_sheet.py` / `split_cog_sheet.py` from
  `scripts/art/source/cogs_sheet.png`); `renderer.js:82-85` looks up
  `cog_manager.png` / `cog_worker_<color>.png`, and `build_replay_viewer.sh:51-55` copies
  exactly that set. There is no `tools/make_violet_cog.py` and no
  `data/soldier_violet_front.png`.
- Consistency: the substitution is internally consistent — renderer, bundle hook and `data/`
  all name the same five files, and the CI viewer smoke drew the scene
  (`{"loaded":true,...,"feed_lines":51}`, run 32672093025 wasm-viewer log). Not a checklist
  item (item 14 covers `chrome_common.js`/`replay_broadcast.html` provenance, not sprites).
- Residue: `data/soldier_{red,blue,green,yellow}_front.png` (≈196 KB) are still committed but
  are referenced by nothing — not by `renderer.js:89-91`, not by
  `build_replay_viewer.sh:51-55`.

### F5 — The `defied` chip lights before the worker has acted whenever the manager ordered a changeover

- Where: `src/firm/sim.nim:604` and `:629`; `client/renderer.js:1224-1225`.
- Observed: `tableStateJson` computes `"obeyed": machine.setup == machine.order`. At shift
  open, `openShift` (`sim.nim:192-193`) installs the manager's *new* order while `setup` still
  holds last shift's line, so `obeyed` is false for any machine the manager just ordered to
  switch. `renderer.js:1224` renders the amber `DEFIED` chip on `!seat.obeyed` with no guard,
  unlike the `IDLE` chip which is gated on `state.shiftsPlayed > 0` (`renderer.js:1222`). The
  spectator therefore reads "defied" on a machine that has not yet made a decision this shift.
  (The feed's own defiance line is computed correctly, from the recorded order vs the recorded
  `work` line — `renderer.js:981-984` / `:1045-1049`.)
- Design note: design.md:899-901 says the chip means "an amber `DEFIED` chip when it ran a line
  other than its order" — i.e. a post-hoc fact, not a pre-decision one.
- Not a checklist item: item 11 is confined to `.plate-name` collapse and the 640 px label
  rule, both of which are satisfied (see F-traced list).

### F6 — Captured error text is truncated on **byte** boundaries, but never reaches the replay

- Where: `src/firm/llm.nim:470` (`head[0 ..< 160]`), `:509` (`response.body[0 .. min(…, 400)]`),
  `:517-519`, `:522`, `:531`.
- Observed: five error-message constructions slice raw bytes, so a multi-byte character can be
  cut in half. I traced every consumer of these strings: they are raised as `FirmError` and
  land only on stdout — `llm.nim:677-678` and `server.nim:306-307`. Nothing writes an error
  message into a `GameEvent`: `applyMemo`/`applyWork` take `say`/`notes` from the decision
  only (`sim.nim:439-455`, `:484-503`), and `replayPayload` (`server.nim:130-149`) serialises
  only `sim.names`, `policyNames`, `config`, `events` and `results`.
- Checklist item 9 lists "captured errors" among the strings that reach the replay; in this
  build they do not, so the byte slicing is a log-legibility issue, not a replay-JSON hazard.
- Provenance: all five slices are verbatim from the starter
  (`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:321,360,369,374,383`).

### F7 — `notes` is capped only in the parser, not at the sim boundary

- Where: `src/firm/llm.nim:562` and `:600` (`cleanText(payload{"notes"}.getStr(), MaxNotesLen)`,
  600 runes, rune-safe); `src/firm/sim.nim:442-443` and `:491-492`.
- Observed: `applyMemo`/`applyWork` store `notes` verbatim (`if notes.len > 0: sim.notes[seat] = notes`)
  with no `trimText`, and the value is copied into `event.text` (`sim.nim:453`, `:501`), which
  reaches the replay. Every production caller passes an already-capped string
  (`server.nim:298`/`:301` pass `decision.notes`; the fallback paths pass `""`;
  `replayMatch` at `sim.nim:889`/`:891` passes `event.text`, already capped when recorded), so
  no path today exceeds 600 runes or emits a broken rune — `say` *is* trimmed at the sim
  boundary (`sim.nim:439`, `:484`) but `notes` is not. Inference, not observation: a future
  caller that bypasses the parser could put an uncapped string into the replay.

### F8 — No wall-clock floor between LLM batches (bedrock 30-req/min sidecar cap)

- Where: `src/firm/server.nim:318-319`; `src/firm/types.nim:97` (`turnDelayMs: 400`);
  `src/firm/sim.nim:164-165`.
- Observed: the only spacing between batches is `sleep(config.turnDelayMs)` (400 ms default,
  and `sampleEpisode` only ever *lowers* it). A five-request batch that returns in ~3 s
  therefore issues 5 requests every ~3.4 s ≈ 88 req/min. `playbooks/make-coworld.md:364`
  records that the hosted Bedrock sidecar caps 30 requests/minute *per episode* and that
  exceeding it cascades into scripted fallbacks on fast episodes only. The design note's
  §Episode budget (design.md:490-505) reasons about the timeout ceiling but not about a rate
  floor. Not a checklist item; flagged because it is the phase-60 fallback-rate risk.

### F9 — `docker_smoke.sh` asserts the game container's exit code but not the players'

- Where: `tools/ci/docker_smoke.sh:237-242` (game exit code), `:256-258`
  (`player_failure.json`).
- Observed: no `docker inspect` of `${prefix}-p${slot}`. `playbooks/make-coworld.md:363`
  names this gap explicitly. Mitigating: the player-side fix that gap protects against *is*
  applied here — `src/firm_player.nim:66-97` wraps the whole receive loop in
  `try/except CatchableError` and exits 0 on a dead socket (verified by diffing against
  `/workspace/starters/cogame-bullwhip/src/bullwhip_player.nim`, which lacks it).
- The script is byte-identical to `coworld-builder/templates/tools/ci/docker_smoke.sh` after
  the three substitutions (verified by `diff` against a `sed`-substituted template), so this
  is template state, not a repo edit.

### F10 — `viewer_smoke.mjs` is run without `--soak`

- Where: `.github/workflows/ci.yml:306-309`.
- Observed: the step passes `--bundle`, `--replay`, `--timeout 90` only.
  `tools/ci/viewer_smoke.mjs:38,92,376-392` supports `--soak <s>`, which
  `playbooks/make-coworld.md:328` recommends for the cogball 0.1.4 class of defect (loads,
  then freezes mid-playback). The shipped `viewer_smoke.mjs` is **byte-identical** to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` and `ci.yml` is identical to the
  substituted template, so the omission is inherited from the template, not introduced here.
  Not a checklist item (item 13 requires the smoke step to run, which it does).

### F11 — `player_connect_timeout_seconds` has no schema maximum, and `MinShifts` floors the fit

- Where: `coworld_manifest_template.json` `game.config_schema.properties.player_connect_timeout_seconds`
  (`{"type":"number","minimum":0,"default":180}`, no `maximum`); `src/firm/sim.nim:160-165`.
- Observed: `sampleEpisode` computes
  `budget = 0.6 × episodeTimeoutSeconds − playerConnectTimeoutSeconds − 20`, then
  `shifts = max(MinShifts, min(config.shifts, min(MaxShifts, fitted)))`. Because of the
  `max(MinShifts=4, …)` floor, a large connect timeout cannot be compensated: with
  `player_connect_timeout_seconds = 700` and the default 1200 s timeout, `fitted = 0` but
  `shifts` still clamps up to 4, so the arithmetic worst case is `700 + 4×60 + 20 = 960 s`,
  past the 720 s play budget. The episode still *settles* — `server.nim:255-263` checks the
  deadline before each batch and calls `endEarly()` — but the settle lands up to one
  `ShiftBudgetSeconds` (60 s) after `playDeadline`, because the check is pre-batch by design
  (design.md:482-483). With the shipped defaults (180 / 1200 / 8 shifts) the deadline is never
  reached: 180 + 480 + 20 = 680 s < 720 s. Inference from the arithmetic; the shipped
  variants and cert fixture all set `player_connect_timeout_seconds: 180`, so item 5 is
  satisfied as configured.

### F12 — The spectator frame always reports `"scripted": false`

- Where: `src/firm/sim.nim:609` (`node["scripted"] = %false`).
- Observed: the `Sim` carries no per-seat scripted flag, so `tableStateJson` hard-codes
  `false` for every seat on every frame. The design's `tableStateJson` example (design.md:611,
  :615) also shows `false`, and nothing in the viewer reads the field
  (`grep -n "scripted" client/renderer.js` → no hits), so the display is unaffected. Recorded
  only because the key is present and always lies about a scripted-policy seat.

---

## Traced and consistent

**Resolution rules (design.md:117-181, the 12 steps) — `src/firm/sim.nim:188-392`**

- Step 1 `openShift` — `sim.nim:188-204`: installs `nextOrders` into each machine's `order`,
  `nextPayroll` → `payroll`, `nextSplit` → `split`, moves `reports` → `heardReports`, clears
  the shift's decisions, appends the `shift` event with `shift`, `demandA[s]`, `demandB[s]`,
  the four `MachineState`s, `payroll`, `split[4]` and `text` = the in-force directive
  (`logShift`, `sim.nim:176-186`). Shift-0 opening values match design.md:121-126:
  `condition = 100`, setups `A A A B`, orders = setups, `payroll = 30`
  (`InitialPayrollPercent`, `sim.nim:26`, `:248`), split `[25,25,25,25]` (`sim.nim:249`),
  directive `StandingOrder` (`sim.nim:42-43`, `:250`). Asserted at `tests/test_sim.nim:94-113`.
- Step 2 deadline-before-batch — `server.nim:255-263`, inside the lock, before
  `orderedSeats()`/`decideAll`. Matches design.md:482-483.
- Step 3 one batch of five — `server.nim:266-278` + `llm.nim:647-680`; see the batch section
  below.
- Step 4 manager first — `orderedSeats` (`sim.nim:276-287`) emits the manager then workers
  0..3; `applyMemo` (`sim.nim:398-456`) stores into `nextOrders`/`nextPayroll`/`nextSplit`
  ("for shift s+1"), strips + collapses newlines + cuts the directive at 240 runes
  (`trimText`, `sim.nim:93-99`, `:439`), leaves the standing directive when the memo is empty
  (`sim.nim:440-441`), appends the `memo` event. The "binds nobody this shift" property is
  asserted at `tests/test_sim.nim:183-205`.
- Step 5 workers, in worker order — `applyWork` (`sim.nim:458-504`) raises `FirmError` unless
  `run ∈ 0..10` (`:476-477`), `maint ∈ 0..10` (`:478-480`), `run + maint ≤ 10` (`:481-483`) and
  the line normalises (`:473-475`); `report` is `trimText`-ed at 120 runes and forced to `""`
  when `config.reports` is off (`:484-486`). Asserted at `tests/test_sim.nim:232-291`.
- Step 6 per-machine resolution — `sim.nim:318-346`, matched line for line against
  design.md:150-158: `changeover = line != setup` (`:323`);
  `hours = max(0, run − 2·changeover)` (`:324`); `setup = line` (`:325`);
  `q = 0.5 + 0.5 · startCondition/100` using the condition captured **before** mutation
  (`:319`, `:326`); `units = floor(2.0 · hours · q)` (`:327`);
  `condition = clamp(start − 3·hours + 6·maint, 0, 100)` (`:328-330`);
  `toil = 1.5 · (run + maint)` on the **raw** run hours (`:331`). Hand-computed against
  design.md:1028-1036 at `tests/test_sim.nim:128-181` (12 units at run 6/maint 3; 8 units on a
  changeover; condition 70 after run 10; clamp at 0 and 100; `q = 0.5` halving output exactly).
- Step 7 sell — `sim.nim:345`, `:348-353`: `producedX` accumulates on the *new* setup,
  `soldX = min(produced, demand[s])`, `revenue = 10·(soldA+soldB) + 2·(surplusA+surplusB)`.
- Step 8 pay — `sim.nim:355-360`: `pool = revenue · payroll/100` with the payroll in force
  **this** shift, `pay[w] = pool · split[w]/100`, `profit = revenue − pool`.
- Step 9 score accumulation — `sim.nim:361-364`: `workerNet[w] += pay − toil`,
  `firmProfit += profit`.
- Step 10 `settle` event — `sim.nim:367-383`: carries `shift`, `units[4]`, post-shift
  `condition[4]`, `soldA/B`, `surplusA/B`, `revenue`, `pool`, `profit`, `pay[4]`, `toil[4]`,
  `obeyed[4]` (`line == order`, `:343`), `idle[4]` (`run == 0`, `:344`).
- Step 11 no trailing `shift` event — `sim.nim:385-392`: after the last shift, `settle("complete")`
  follows the settle event directly. Asserted at `tests/test_sim.nim:366-367`
  (`events[^1] == evEnd`, `events[^2] == evSettle`).
- Step 12 — `settle` (`sim.nim:303-310`) sets `done`, `reason`, `phase = phDone`, appends `end`
  with `shift = shiftsPlayed` and `text = reason`.
- Scoring (design.md:206-215) — `sim.nim:289-299`: `0.0` when `shiftsPlayed == 0`;
  manager `firmProfit / (n · 300.0)`, worker `workerNet[w] / (n · 30.0)`. Scales at
  `sim.nim:27-28`. Asserted at `tests/test_sim.nim:313-357`, including the strictly-negative
  zero-share worker and the all-zero idle firm.
- Exactly two `reason` values — `"complete"` (`sim.nim:390`) and `"deadline"`
  (`endEarly`, `sim.nim:506-513`). No other literal exists.

**Decision path — `src/firm/llm.nim`**

- Tolerant parse: `extractJsonObject` (`llm.nim:461-473`) takes the first `{` to the last `}`,
  so surrounding prose and fences are accepted. `parseManagerReply` (`:557-595`) resolves
  orders case-insensitively via `normalizeLine` (`sim.nim:130-136`, accepts `a`/`A`/`line a`/
  `linea`), falls back to the machine's current order on an unrecognised entry, a wrong-length
  array or a missing key, and treats a missing/non-numeric/out-of-range `payroll` as invalid
  (`:574-577`); `split` renormalises by largest remainder (`normalizeSplit`, `sim.nim:101-128`),
  `[25,25,25,25]` when missing or all-zero, invalid when present-but-malformed (`:583-591`).
  `parseWorkerReply` (`:597-619`) is tolerant on `line`, strict on `run`, defaults `maint` to
  0, rejects `run + maint > 10`. All of this is asserted case by case at
  `tests/test_bot.nim:179-263`. `wholeNumber` (`:541-555`) accepts int, float (rounded) and
  numeric string, exactly as design.md:426-427 specifies.
- **One parallel batch per turn** (the simultaneous-decision rule at the foot of the
  checklist): `decideAll` builds a single `RequestBatch` over *all* still-open seats
  (`llm.nim:650-658`) and fires one `client.curl.makeRequests(batch, client.timeoutSeconds)`
  (`:659`). There is no per-seat request loop anywhere. The server passes all five seats in one
  call (`server.nim:266`, `:278`) with the batch happening **outside** the lock on a snapshot,
  so every seat decides from the same pre-shift picture.
- Retry once: `for attempt in 0 .. 1` (`llm.nim:647`) — at most two batches per shift; the
  second carries the hint `"Your previous reply was invalid. Respond with ONLY the requested
  JSON object."` (`:654-656`), which is the design's exact string (design.md:334-335).
- Legality pre-check before accepting a reply: `var probe = sim` then
  `probe.applyMemo`/`probe.applyWork` (`llm.nim:667-674`) — an illegal-but-parseable reply is
  pushed into the retry rather than into the sim.
- Fallback: seats still open after attempt 1 get `scriptedAction(sim, seat, skSteady)`
  (`llm.nim:681-684`) with the stdout line. See F2 for the recording nuance.
- No credentials ⇒ every seat scripted immediately, no network: `newLlmClient` sets
  `disabled = true` when no Bedrock endpoint/token and no key/URI (`llm.nim:152-155`), and
  `decideAll:643` short-circuits every seat to `scriptedAction` before any batch is built.
  Asserted with a wall-clock bound at `tests/test_bot.nim:154-176` (< 500 ms for five seats).
- Belt-and-braces rejection under the lock: `server.nim:302-314` catches `FirmError` and
  applies `steady` with `scripted = true`.

**Every wait and its bound (checklist item 5)**

| wait | where | bound |
|---|---|---|
| player connect | `server.nim:211-217` | `config.playerConnectTimeoutSeconds` (180), 200 ms poll |
| LLM batch | `llm.nim:659` | `client.timeoutSeconds` = `llmTimeoutSeconds` (30, `types.nim:101`) |
| batches per shift | `llm.nim:647` | 2 (`for attempt in 0 .. 1`) |
| game loop | `server.nim:247-319` | breaks on `sim.done` or `epochTime() > playDeadline`; each iteration necessarily resolves one shift (see below) |
| inter-shift pacing | `server.nim:318-319`, `sim.nim:164-165` | `turnDelayMs ≤ PacingBudgetMs div shifts`, total ≤ 20 s |
| shutdown settles | `server.nim:191`, `:201` | two fixed 500 ms sleeps |
| artifact POST | `server.nim:124` | `curl.post(…, 60)` |
| viewer replay fetch | `static_replay.js:14`, `:71-88` | `FETCH_TIMEOUT_MS = 20000` via `AbortController` |
| player receive loop | `firm_player.nim:66-93` | wrapped in `try/except`; exits 0 on `final` or a dead socket |

No unbounded loop: `server.nim:247`'s `while true` cannot spin without progress —
`seats = orderedSeats()` covers every pending seat (`sim.nim:276-287` iterates `pendingSeats`),
`decideAll` returns exactly `seats.len` decisions (`llm.nim:639`) and never raises
(`llm.nim:676` catches everything), and each seat is applied either from its decision or from
the `except`-path fallback, so `pendingSeats()` empties and `maybeResolve` (`sim.nim:394-396`)
fires `resolveShift`.

Budget arithmetic, from the shipped constants: `PlayBudgetFraction = 0.6` (`sim.nim:37`),
`ShiftBudgetSeconds = 60` (`sim.nim:33`), `PacingBudgetMs = 20_000` (`sim.nim:35`),
`sampleEpisode` (`sim.nim:153-166`) gives `fitted = (720 − 180 − 20)/60 = 8`, so
`shifts = 8` for the standard variant. Worst case `180 + 8×60 + 20 = 680 s < 720 s`. ✔
`sampleEpisode` is idempotent (`:157-158` early-returns on `sampled`), is called once after the
seed is settled (`src/firm.nim:41`), and replay paths force `sampled = true`
(`server.nim:489`, `firm_replay.nim:30`) so a replay is never re-fitted.
`playDeadline` is taken from `COWORLD_TIMEOUT_SECONDS` when present and otherwise from
`config.episodeTimeoutSeconds` (`server.nim:232-241`), exactly as design.md:483-486 requires.
The CI smoke settled in ~4 s wall clock (`22:56:57` → `22:57:01`, docker-smoke log) — but that
is the no-credential path; the 680 s LLM figure is arithmetic, untested end to end (see
*Could not determine*).

**Rune-safe truncation (checklist item 9)**

- `trimText` (`sim.nim:93-99`) strips, replaces `\r`/`\n` with spaces, and cuts with
  `runeSubStr(0, limit)`. Applied to the directive at 240 (`sim.nim:439`) and the report at 120
  (`sim.nim:484`).
- `cleanText` (`llm.nim:533-539`) does the same for parser output, cutting to `limit − 1` runes
  plus `…` so the result is exactly `limit` runes.
- Player prompt: capped server-side at 4000 **runes** with `runeSubStr`
  (`server.nim:443-444`).
- Test at the cap, multi-byte: `tests/test_sim.nim:271-291` feeds `"é" × 400` and asserts
  `directive.runeLen == 240`, every `heardReports[w].runeLen == 120`, and
  `validateUtf8() == -1` on the directive, on every report, and on **every event's `say` and
  `text`** in the log. `tests/test_bot.nim:265-282` covers the parser side at all three caps
  (600 / 240 / 120) plus `validateUtf8`.
- CI enforces the consequence: `docker_smoke.sh:285-292` decodes the replay bytes as strict
  UTF-8 before parsing them as JSON (`SMOKE_REQUIRE_REPLAY_JSON=1` default); it passed
  (`smoke OK: seats=5 results=374B replay=7789B reason=complete`).

**Replay writer and re-derivation (checklist item 2)**

- Writer: `replayPayload` (`server.nim:130-149`) emits `protocol: "firm.replay.v1"`,
  `names` = table aliases, `policyNames` = policy names, `config{shifts,seed,reports,sampled}`,
  `events`, `results` — matching design.md:656-663. Nothing but the seed and the event log is
  needed to re-derive.
- Re-derivation: `replayMatch` (`sim.nim:868-901`) calls `initSim(config)` (roles, demand
  levels, switch shift and aliases re-drawn from the seed), clears the event log, then replays
  **only** `memo` and `work` events through `applyMemo`/`applyWork`. `shift` and `settle`
  events are never applied — they are recomputed by the sim and the recorded ones are only
  *checked*: `checkShift` (`sim.nim:826-836`) compares shift index, `demandA`, `demandB`,
  `payroll`, `split`, the directive and all four machines; `checkSettle` (`sim.nim:838-866`)
  compares shift, `units[4]`, `condition[4]`, `soldA/B`, `surplusA/B`, `obeyed[4]`, `idle[4]`
  exactly and revenue/pool/profit/`pay[4]`/`toil[4]` to 1e-6. A mismatch raises `FirmError`.
  That is the frame-by-frame agreement: **every** recorded derived event is re-checked, not
  just the last one.
- Viewer derives from that same code, not from a parallel recording:
  `replay-viewer/firm_replay.nim:36-38` builds `states` by iterating
  `replayMatch(config, events)` and calling `frame.tableStateJson()`, and
  `attachReplay` reads `payload.states` (`renderer.js:1607`, `:1627-1630`). The
  live-server replay mode does the same (`server.nim:151-155`, `:509`). There is no second
  state recording anywhere in the tree.
- Tests: `tests/test_sim.nim:440-462` (`frames.len == events.len + 1`; final frame's
  `tableStateJson` equals the live one; a recorded `deadline` ending honoured) and
  `:464-481` (a `settle` with `revenue + 1` and a `shift` with `condition + 1` each raise).
  `:394-438` round-trips one event of all six kinds field by field.

**Manifest (checklist items 3, 6, 10)**

- `game.replay_viewer = {"bundle": "static-replay-viewer"}` — same placement as the starter's
  manifest (`bullwhip` also puts it under `game`, verified). `tools/build_replay_viewer.sh`
  exists and is committed `0755` (`ls -l`), asserted by `ci.yml:225-236`. The viewer fetches
  only the `?replay=` URL (`static_replay.js:129`, `:144`) — no other network call in the
  bundle. No pod-served replay viewer is declared; the `/client/replay` mention in the manifest
  is inside the `game.protocols.global` prose describing the live server page, and the starter
  carries the same sentence.
- `num_agents: 5` present in **both** variants (`variants[0].game_config`,
  `variants[1].game_config`) and in `certification.game_config`; also declared in
  `config_schema` with `minimum: 5, maximum: 5`. `len(certification.players) == 5` and
  `len(certification.game_config.players) == 5`.
- `tools/ci/docker_smoke.sh:106-151` enforces all four invariants with `SEAT-COUNT FAIL:`
  prefixes, plus the `SMOKE_SEATS` cross-check (default `5`, `:54`). Grepped the full
  docker-smoke job log for run 32672093025: **no `SEAT-COUNT FAIL` anywhere**; the log shows
  `game=firm seats=5 config={… "num_agents": 5 …}`.
- `game.docs` is exactly `{"readme":{"type","value"},"pages":[{"id","title","content":{"type","value"}}×2]}`
  (pages `rules.md`, `scoring.md`). `game.protocols` carries **both** `player` and `global`.
- `results_schema` requires all eleven fields with `minItems/maxItems: 5` on the five array
  fields; `resultsJson` (`sim.nim:517-547`) emits exactly those keys.
- Every declared `player[]` entry (`firm-player`, `firm-steady`, `firm-taskmaster`) occupies at
  least one certification slot, avoiding the raid `players_missing` failure.

**Chrome provenance (checklist item 14)**

The bullwhip lineage has no `client/chrome_common.js`; design.md:788-796 names
`client/chrome.css` and `client/replay.html` as the files holding those roles, so I applied
the rule to those.

- `diff /workspace/starters/cogame-bullwhip/client/chrome.css client/chrome.css` →
  **a single hunk, `467a468,559`**: 92 appended lines under a banner comment
  (`client/chrome.css:469-472`). Lines 1–467 are byte-identical; no starter rule edited or
  deleted.
- `diff …/client/replay.html client/replay.html` → title + wordmark text, one appended
  `<div id="demandbar">` under the banner
  `FIRM additions to the inherited cogame-bullwhip chrome` (`client/replay.html:20-23`),
  `BullwhipRenderer` → `FirmRenderer`, one added `demandbar:` option, and one appended
  `<script>` block (`:78-99`). **Nothing removed.** Every starter id survives: `#layout`,
  `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`, `#feedtoggle`,
  `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`,
  `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, plus
  `fit()` + `bindFeedToggle`. `replay-viewer/index.html` gets the identical treatment
  (same diff, `./` paths, `firm_replay.js`). `global.html` and `player.html` likewise.
- Transport rule (a): `relayout()` (`client/replay.html:87-95`, `replay-viewer/index.html:57-72`)
  measures `#transport.offsetHeight` and sets `--band` **and** `--hudscale` on
  `document.documentElement`, then calls the starter's `fit()` from the same function. Bound to
  `load` and `resize`; `bindFeedToggle` dispatches a `resize` (`renderer.js:1314`, `:1325`) so
  the toggle re-lays out too.
- Transport rule (b): `grep -n "position: fixed" client/chrome.css` → **no hits**. `#stage` is
  a flex column (`chrome.css:47-52`), `#board-wrap` is `flex: 1` (`:95`), `#transport` is the
  last child in normal flow at `z-index: 10` (`:128-136`). The only absolutely-positioned
  overlays (`#lightpool` `:104`, `#grain` `:112`, `#endscreen` `:374`) live inside
  `#board-wrap`. `#loading` is pinned above the band by the appended
  `#loading { bottom: var(--band); }` (`chrome.css:535`), which wins over the inherited
  `inset: 0` (`:251`) by source order.
- Transport rule (c): `#endscreen` is `position: absolute; inset: 0` inside `#board-wrap`
  (`chrome.css:374-376`), so its bottom edge *is* `var(--band)` above the page bottom; shown
  with the class its own rule uses — `#endscreen.show` (`:383`) toggled by
  `updateEndscreen`'s `container.classList.toggle("show", !!show)` (`renderer.js:1248`).
  Every seek routes through `setIndex` (`renderer.js:1632-1652`), whose last act is
  `updateEndscreen(…, index >= events.length && events.length > 0, …)` (`:1650-1651`) — so
  scrub click/drag (`:1581-1588` → `onSeek` → `:1616-1619`), a beat-marker click
  (`:1500-1503`) and the play button (`:1623`) all dismiss it. The starter binds no keyboard or
  back/forward transport controls (`grep -n "keydown\|ArrowLeft"` on both the starter's and
  firm's `renderer.js` → no hits), so there is no unhandled seek path.
- Transport rule (d): `markBeat` (`renderer.js:1492-1506`) creates a
  `<button type="button" class="beat-marker …">` with `title` **and** `aria-label` from
  `beatLabel` (`:1508-1523`, e.g. `"Shift 3 — the manager's memo"`, `"Shift 3 settles — profit
  $273.60"`, `"Final"`) and an `onclick` that seeks to that index; the container keeps its
  pointer drag handlers (`:1581-1591`). `buildScrub` emits markers for exactly four kinds —
  `memo`, `work`, `settle`, `end` (`:1558-1567`) — and the appended CSS defines a rule for
  **each** of those four (`chrome.css:521-525`), plus the base `.beat-marker` button reset and
  `:focus-visible` (`:519-520`). No emitted kind is ruleless.
- `#viewpanel`: `grep -rn "viewpanel\|zoomAt\|setZoom\|attachMinimap"` over `client/`,
  `replay-viewer/` and `tools/` → **no hits**, and the starter ships none either, so nothing
  had to be removed. Consistent with design.md:826-828 (fixed arena, always drawn to fit).

**Viewer executes (checklist item 13)**

- `replay-viewer/config.nims` link flags vs the JS bootstrap come from the **same** starter —
  the only diff against bullwhip's `config.nims` is the `bw_` → `fm_` and
  `BullwhipReplayModule` → `FirmReplayModule` renames. `-s MODULARIZE=1` +
  `-s EXPORT_NAME=FirmReplayModule` (`config.nims:37-38`) is matched by
  `static_replay.js:139` calling the factory `FirmReplayModule()` and awaiting the promise.
  There is **no** `onRuntimeInitialized` anywhere in the tree. The exported symbols
  `_fm_load_replay/_fm_payload_ptr/_fm_payload_len/_fm_error_ptr/_fm_error_len`
  (`config.nims:41`) match the `exportc` names in `firm_replay.nim:22,54,60,63,69` and the JS
  call sites (`static_replay.js:94-103`), and `emscripten_exit_with_live_runtime()` keeps the
  globals alive (`firm_replay.nim:72-81`).
- `data-replay-loaded="true"` is set on `<html>` at the end of `attachReplay`'s `makeRenderer`
  callback (`renderer.js:1682`), after the frame IIFE has run its first synchronous
  `renderer.draw(view)` (`:1678`) — first drawn frame, not payload parse.
  `data-replay-error` is set by `fail()` (`static_replay.js:56`) on a missing `?replay=`, a
  fetch timeout, a non-200, a wasm rejection or a JSON failure, and removed on a successful
  retry (`:107`, `:135`). Both markers, both from the shell's own paths.
- `ci.yml`'s `wasm-viewer` job has `needs: docker-smoke` (`ci.yml:212`) and runs
  `node tools/ci/viewer_smoke.mjs --bundle … --replay … --timeout 90` (`:306-309`) with no
  `continue-on-error`. `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs`.
- CI evidence, run **32672093025** on `main`: job `wasm-viewer` (id 97274475645), step
  `Load the bundle in a real browser` ran and passed, emitting
  `{"loaded":true,"ms":287,"clock":"SHIFT 0 / 4 · WAITING ON 5","scorebug":"Sprocket ▶ $0.00 MACHINE 1 25% 0.00 Gizmo ▶ $0.00 MACHINE 2 25% 0.00 Ratchet ▶ $0.00 MANAGER 0.00 Widget ▶ $0.00 MACHINE 3 25% 0.00 Bolt ▶ $0.00 MACHINE 4 25% 0.00","feed_lines":51}`
  and `scrub readouts: 0%="SHIFT 0 / 4 · WAITING ON 5"  50%="SHIFT 2 / 4 · WAITING ON 5"  100%="FINAL · PROFIT $1,080.40"`.
  Artifacts `viewer-smoke` and `static-replay-viewer` uploaded.

**Legibility at 360 px (checklist item 11)**

- `client/chrome.css:280-292`: `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` — exactly
  the required declarations, inherited byte-identical from the starter.
- `client/chrome.css:460-464`: `@media (max-width: 640px) { .plate-label { display: none; } … }`
  — labels hidden under 640 px. The appended block adds a second `.plate-label { display: none }`
  at 560 px (`:552-555`) and a two-column scorebug with a spanning manager plate at 480 px
  (`:556-559`). The canvas re-stacks to 2×2 bays under 560 px (`renderer.js:144`, `:151-152`)
  and `#demandbar` shortens (`renderer.js:1189-1197`).

**CI green + no test loosened (checklist item 1)**

- `gh run list -R Metta-AI/cogame-firm --branch main -w ci.yml` →
  `completed  success  "Firm: packaging, manifest and the CI scaffold"  CI  main  push  32672093025`
  — the reviewed sha. Jobs: `test` ✓ 49 s, `docker-smoke` ✓ 1 m 1 s, `wasm-viewer` ✓ 1 m 35 s.
  The `test` job ran four invocations (`tests/test_bot.nim` and `tests/test_sim.nim`, each in
  debug and `-d:release`); no `skip` and no narrowing repo variables in effect.
- `git log -p --stat -- tests/` in `/tmp/cogame-firm` shows a single commit touching `tests/`
  (`75efe8b`, +792 lines, both files created) and nothing since. No assertion deleted, no
  tolerance widened, no `skip` added, no test file removed. The only in-code weakening
  *relative to the design note* is the disclosed one at `test_bot.nim:109-139` (see F3), which
  was written that way at creation, not loosened during this run.

**Release order and scaffold (checklist item 12)**

- `coworld-release.yml`: `Build the Coworld manifest` (`:153`) → `Certify locally` (`:167`) →
  `Upload the policies` (`:206`) → `Upload the Coworld` (`:304`) → `Put the Coworld secret`
  (`:342`). Correct order; `:207-208` carries the explanatory comment. No smoke step in the
  release workflow, so the "freshly built binary" clause is vacuous there; `ci.yml`'s
  `docker-smoke` builds the image in the same job (`ci.yml:176-177`) before running it.
- All three workflows present; `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh`
  both `0755`.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files returns
  **nothing** (exit 1 ⇒ the `if grep … then error; exit 1; fi` gate exits 0).
- `tools/ci/policies.json` defines four policies: two `PLAYER_PROMPT` champions
  (`firm-boss` `:3-8`, `firm-hand` `:10-16`) and two scripted fillers (`firm-steady` `:18-23`,
  `firm-taskmaster` `:25-30`). Champion **#2** — the second `PLAYER_PROMPT` entry,
  `firm-hand` — carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`
  (`policies.json:15`). ✔
- All four scaffold files are byte-identical to `coworld-builder/templates/` after substituting
  `<slug>`→`firm`, `<IMAGE>`→`coworld-firm`, `<SEATS>`→`5` (verified by `diff` against a
  `sed`-substituted template: `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`,
  `tools/ci/docker_smoke.sh` — all identical; `viewer_smoke.mjs` identical unsubstituted).

**Both name spaces (checklist item 4)**

- Agents see aliases only: `tableNames` (`sim.nim:140-151`) draws from `CogNames` on the seed;
  the welcome frame (`server.nim:397`), every `playerStateJson` (`sim.nim:735`, `:781`, and
  the `floor`/`reports` name fields), every prompt (`llm.nim:273`, `:345`, `:388`, `:409`) and
  the final frame (`server.nim:172-180`, `aliasNames`) carry aliases. `resultsJson`
  (`sim.nim:526`) is the only place policy names appear, and it is platform-facing.
- Viewer maps aliases → policy names for non-baseline seats: `makeNameMap`
  (`renderer.js:907-931`) builds `display[i] = policyNames[i]` unless
  `isBaselineFiller(policyNames[i])` (`:903-905`, matching `Baseline` / `Baseline (3)`), and
  substitutes inside free text via a word-boundary regex (`:918-929`). The replay payload
  carries `policyNames` alongside `names` (`server.nim:139-140`, `firm_replay.nim:42-43`).

**Packaging**

`compose.yaml` service `firm`, `image: coworld-firm:latest`, `platform: linux/amd64`;
`Dockerfile` and `Dockerfile.replay-viewer` diff against the starter's only on the slug/paths;
`nimby.lock` byte-identical to the starter's; `firm.nimble` 0.1.0 with the four required
requires. `ci.yml`'s `NIMBY_VERSION: "0.1.26"` matches `Dockerfile:17,21`; the wasm image pins
0.1.27 (`Dockerfile.replay-viewer:11`), which is what design.md:934 specifies.

---

## Could not determine

- **Whether `curly.makeRequests(batch, timeoutSeconds)` bounds the *batch* wall clock or only
  each request.** `curly` is not vendored and no Nim package tree exists in this sandbox
  (`find / -name curly.nim` → nothing). Item 5's per-shift 60 s ceiling assumes a batch-level
  bound. What would settle it: the `curly` source for `makeRequests`, or a hosted episode log
  showing a shift's elapsed time when a request stalls. Note this is inherited unchanged from
  the starter, which has been run in production.
- **Whether `readCogameUri` (`llm.nim:92`, `bitworld/runtime`) bounds its fetch.** Called once
  at `newLlmClient` when `ANTHROPIC_API_KEY_URI` is set — i.e. on the hosted path — and its
  wait sits *outside* the per-shift accounting. `bitworld` is not present in the sandbox
  (`find / -type d -name bitworld` → nothing). What would settle it: the `bitworld/runtime`
  source, or a hosted log with a timestamp between "starting with N/5 players connected" and
  the first shift line.
- **The LLM-driven wall clock end to end.** The only executed episode in CI ran with no
  credentials (`no ANTHROPIC_API_KEY: the game must complete on its scripted baselines`,
  docker-smoke log), settling in ~4 s. The 680 s worst case is arithmetic from the shipped
  constants, not measured. What would settle it: a phase-60 hosted episode's elapsed time and
  fallback count.
- **Whether the `steady` baseline's constants are in fact optimal / tuned** — see F1. I can
  confirm the constants are internally coherent with the wear/repair arithmetic and that the
  behavioural envelope is asserted, but not that a sweep was run.
