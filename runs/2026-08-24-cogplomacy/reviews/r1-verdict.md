blocking: 0

# r1 verdict — 2026-08-24-cogplomacy

Head: `9711b80ccc28aa711872ca007b7d0ccba0134279` (main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + simultaneous-decision rider)
Independent read written before reading fixes: **yes** — I read the tree, the starter diffs, the
manifest, and the CI logs of run 32728438824, and verified every review finding's status at head
from the code and `git log -p`, before opening `r1-fixes.md`. The fixes file was consulted only
afterwards, to cross-check dispositions (audit table below).

The review was written against `1b9ddad`; fourteen fix commits (`35b766d..9711b80`) landed after
it. The review itself declared **zero blocking** findings and 14 non-blocking ones. My job was
(a) to refute or confirm those 14 at the current head, and (b) to run the checklist myself.
Result: all 14 are resolved at head (13 fixed, one no-change with a sound rationale), and every
checklist item passes on cited evidence. **Blocking count: 0.**

## Standing blocking findings

None.

## Refuted / resolved review findings

None of the 14 findings was blocking (the reviewer said so, and I agree — each was checked against
the checklist item it could have engaged). All are resolved at the current head:

### N1 — expander never builds a fleet → RESOLVED (fixed at `35b766d`)
- Evidence: `src/cogplomacy/llm.nim:399-415` at head — `if kind != skHedgehog and fleets < armies:`
  picks the fleet site with the most water (`FleetAdj[...].len` comparison ⇒ `STP` builds
  `F STP/SC`). Head smoke replay (run 32728438824) shows `"kind":"F"` builds where the old run had
  `"kind":"A"`; `tests/test_bot.nim` pins `BUILD F STP/SC`.

### N2 — support rule fired only with no move at all → RESOLVED (fixed at `96df449`)
- Evidence: `llm.nim:286-306` — `moving.add(entry.dest >= 0 and entry.rank < tuning.supportFromRank)`
  with `DefaultExpanderTuning(supportFromRank: 2)` (llm.nim:201-202): a unit whose best is rank (c)
  or (d) supports a really-moving neighbour, per the note's step 4.

### N3 — illegal order did not consume its unit's slot → RESOLVED (fixed at `9f0fe87`)
- Evidence: `sim.nim:612-622` — on an illegal order the unit's province is claimed and an `H` order
  added (`claimed.add(order.unit.province); result.orders.add(Order(... kind: okHold ...))`), so a
  later order for the same unit is dropped. Test "an illegal order holds its unit and a later order
  for it is dropped" added in `tests/test_sim.nim`.

### N4 — replayMatch checked too few fields → RESOLVED (fixed at `ff2f6da`)
- Evidence: `sim.nim:1278-1319` — `start` and `phase` events compare `units`, `owners` and
  `counts` (`sameUnits`/`sameOwners`/`event.counts != sim.counts()`); `adjudicate` compares every
  `OrderResult` outcome and canonical order, the dislodged units and the standoff list; `centres`
  compares all 34 owner slots. `tests/test_sim.nim:500-521` asserts tampered boards and flipped
  outcomes raise `CogplomacyError`.

### N5 — 5 s prompt grace, late prompt takes over → RESOLVED (fixed at `abae9fe`)
- Evidence: `server.nim:288-299` — the prompt wait runs to the same `deadline`
  (`gameStart + playerConnectTimeoutSeconds`), and `server.nim:521-526` ignores a prompt frame when
  `state.started and not state.promptSeen[slot]` ("delivered a prompt after play started; ignoring
  it"). Matches the note: expander for the whole episode, bound = 180 s.

### N6 — feed printed raw notation / unnamed provinces → RESOLVED (fixed at `20b9d10`)
- Evidence: `client/renderer.js:1542-1596` — orders render through `diploOrderWords`, bounces
  through `diploMoveWords`, dislodgements and standoffs name provinces via `diploProvinceWords`
  ("STANDOFF in " + full name); `data/map1901.json` gained `"id"` per province, pinned by
  `tests/test_viewer.nim`.

### N7 — retreat into a province a dislodged unit still stands in → RESOLVED (fixed at `a14365c`)
- Evidence: `orders.nim:465-499` — `heldByDislodged` bars provinces holding another still-unretreated
  dislodged unit; `retreatDestinations`/`legalRetreats` take the dislodged list; four call sites
  updated (`llm.nim:333, 553`, `sim.nim`, tests). Test "a province another dislodged unit still
  stands in is barred" added.

### N8 — a letter to ALL was dropped → RESOLVED (fixed at `b7fa634`)
- Evidence: `llm.nim:663-671` — `if toText != "ALL": to = powerByName(...)` (ALL keeps `to = -1`
  and the letter is added); `sim.nim:411-425` publishes `toPower < 0` letters to everybody, dropping
  only a duplicate of the broadcast (which keeps `replayMatch` byte-identical). Tests in
  `test_sim.nim` (every power reads the ALL letter; `ATLANTIS` still dropped) and `test_bot.nim`.

### N9 — docker_smoke.sh asserted less than §CI jobs describes → RESOLVED (fixed at `8c1ed92`)
- Evidence: `ci.yml` "Assert the smoke artifacts against the manifest" step runs
  `tools/ci/assert_smoke_artifacts.py` (results validated against `game.results_schema`,
  `reason == "complete"`, seven scores, replay carries the six keys) while `tools/ci/docker_smoke.sh`
  stays template-verbatim. Head run log: `smoke artifacts OK: reason=complete scores=7 events=40
  replay keys=['config','events','names','policyNames','powers','protocol','results']`.

### N10 — byte-sliced error text → RESOLVED (fixed at `d871fb6`)
- Evidence: `llm.nim:636, 771, 780, 785, 794` — every model/HTTP snippet in an error message goes
  through `cleanText(oneLine(...), N)` (rune-safe). `tests/test_bot.nim:328-329` asserts
  `validateUtf8(error.msg) == -1` on a 400-dove reply.

### N11 — non-positive timeout would disable the play deadline → RESOLVED (fixed at `555c5e7`)
- Evidence: `server.nim:327-333` — `timeoutSeconds <= 0.0` falls back to
  `defaultGameConfig().episodeTimeoutSeconds`; the pre-batch check at `server.nim:348` is now
  unconditional (`if epochTime() > playDeadline:`).

### N12 — two event kinds not required by the round-trip test → RESOLVED (fixed at `ac58396`)
- Evidence: `tests/test_sim.nim:479-490` — a forced-dislodgement episode is added and the presence
  assertion is `for kind in EventKind: check kind in kinds` (all nine, retreat and build included).

### N13 — "tuned with a grid harness" had no artefact → RESOLVED (fixed at `586a768`)
- Evidence: `tools/tune_baselines.nim` (93 lines) sweeps `springHomePenalty 0..2 ×
  supportFromRank 1..3` on a mixed 4-expander/3-hedgehog table; `tests/test_bot.nim` imports the
  same module, so the grid prints in every CI run. Head test log shows the 9-cell table with
  `springHomePenalty=1 supportFromRank=2 … <- shipped` on the grid maximum (41, `illegal=0`,
  `complete=true`). Item 7's second sentence is now satisfied by an artefact, not a claim.

### N14a — vacuous split-coast assertion → RESOLVED (fixed at `d20c543`)
- Evidence: `tests/test_map.nim` — each coast now must reach some water and a **proper subset**
  (`check part.len > 0; check part < whole`) of the province's union. Strictly stronger.

### N14b — `pkDone` not in the note's PhaseKind list → NO CHANGE, correctly disputed
- Evidence: `types.nim` `pkDone` is a terminal marker letting `case` statements stay exhaustive;
  nothing is pending in it and every decision path `discard`s it. Engages no checklist item; the
  note's type list is a design sketch, not a schema. I agree with leaving it.

### N14c — stabs persisted into the next turn's frames → RESOLVED (fixed at `9711b80`)
- Evidence: `sim.nim` frame-stab scan now stops at the first `press`/`orders` event;
  `tests/test_sim.nim:440-448` asserts `stabs.len == 1` on the adjudication frame and `0` after the
  next press event.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32728438824** on main at `9711b80`, conclusion **success**; jobs `test` (all six `tests/*.nim` run twice — six `nim r --hints:off` + six `-d:release` invocations counted in the job log), `docker-smoke`, `wasm-viewer` all green. `git log -p 1b9ddad..9711b80 -- tests/` read hunk by hunk: no skip/xfail/tolerance anywhere; the only removals are the four `retreatDestinations` call sites gaining the dislodged argument (N7), the vacuous split-coast assertion replaced by a proper-subset one (N14a, stronger), the seven-kind list replaced by `for kind in EventKind` (N12, stronger), and the ALL-letter drop assertion (`letters.len == 0`) replaced by the publish assertion (`== 1` + all-powers delivery, N8 — a re-pin of corrected behaviour, not a loosening). Net +270/−23 across test files. |
| 2 Replay re-derivation | PASS | `sim.nim:1268-1343` `replayMatch` replays decisions through the rules and **checks** every derived event (`start`/`phase` units+owners+counts, `adjudicate` outcomes, `centres` owners); `tests/test_sim.nim:492-529` asserts `frames.len == events.len + 1`, final-frame equality with live `tableStateJson`, and tamper rejection. The viewer derives from the same path: `replay-viewer/cogplomacy_replay.nim:39-41` runs `replayMatch` in wasm and `renderer.js:1225-1249` draws only `payload.states`. |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer = {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755 (CI asserts the exec bit); `static_replay.js` fetches only the `?replay=` URL with a bounded AbortController fetch — no other network. The `/client/replay` string in the manifest is descriptive protocol text about the live server route (identical pattern to the bullwhip starter's manifest, line 210); no pod path is declared as the replay viewer. |
| 4 Both name spaces | PASS | `tests/test_sim.nim:451-476` — policy names and aliases scanned out of every system/user prompt over a whole episode; replay carries `names` (aliases) + `policyNames` (server writer, and the wasm payload at `cogplomacy_replay.nim:45-46`); `renderer.js:649-669` `makeNameMap` swaps real policy names in for non-baseline seats and rewrites aliases in text. |
| 5 Degrade-never-hang | PASS | Connect wait bounded by `playerConnectTimeoutSeconds` (server.nim:278-299, both loops share one deadline); LLM batch bounded by `llmTimeoutSeconds` via `curly.makeRequests(batch, client.timeoutSeconds)` (llm.nim:829), max two attempts; `PlayBudgetFraction = 0.6` (server.nim:254) checked before **every** batch (server.nim:348-354) with `endEarly` ⇒ `reason="deadline"`; deadline always set even for a non-positive config timeout (server.nim:327-333); pacing clamped by `PacingBudgetMs` in `sampleEpisode`; the play loop cannot spin — every apply removes a pending seat, and exception fallbacks apply the expander; shutdown = 0.5 s + 20 s grace then `quit(0)`. Worst case ≈ 720 + 90 + 21 s ≪ 1200 s. |
| 6 num_agents | PASS | `num_agents: 7` in `standard`, `gunboat`, and `certification.game_config`; `config_schema` pins `minimum: 7, maximum: 7`. `docker_smoke.sh:106-151` enforces all four invariants before any container starts, every violation prefixed `SEAT-COUNT FAIL:`; `SMOKE_SEATS` default `7` (line 57) is the independent second declaration. Head docker-smoke log greps **0** occurrences of `SEAT-COUNT FAIL`; positive line: `game=cogplomacy seats=7`. |
| 7 Scripted baseline full legal episodes | PASS | `tests/test_bot.nim:92-98` — seeds 1..8, all-expander, `check sim.reason == "complete"` + `auditLegality` (`illegal.len == 0` per orders event, one order per unit, no self-standoff, builds in vacant owned home centres) + `auditCaps`; same for all-hedgehog and a mixed table. Grid harness: `tools/tune_baselines.nim`, compiled and printed by every CI run (9-cell table in head test log, shipped cell on the maximum). |
| 8 LLM reply handling | PASS | `extractJsonObject` (llm.nim:627-637) takes first `{`…last `}` (fenced/prose fixtures in test_bot); reply invalid only for non-object or missing required key (llm.nim:722-733); exactly one retry with the hint (`for attempt in 0 .. 1`, llm.nim:817-828); still-failing seats answered by expander and logged `cogplomacy: seat N falling back to scripted decision` (llm.nim:842-845), which phase 60's log grep (`falling back`) counts. See non-blocking observation below on the event flag. |
| 9 Rune-safe truncation | PASS | `cleanText` = `runeLen`/`runeSubStr` + `…`; applied to broadcast/letters/pledges/notes/orders/retreats/adjustments/prompt (llm.nim:646-720, sim.nim caps, server.nim:512-513 `runeSubStr(0, MaxPromptLen)`); error snippets rune-cut since `d871fb6`. `tests/test_sim.nim:351-366` feeds 600×🕊️ and asserts `runeLen <= cap` + `validateUtf8 == -1`; `tests/test_viewer.nim:123,133` asserts the whole payload and derived states are strict UTF-8. |
| 10 Manifest validates | PASS | `game.docs` = `readme {"type":"text","value":…}` + `pages[{id,title,content{type,value}}]` (rules.md 6713 chars, map.md 3418 chars); `game.protocols` carries both `player` and `global` (verified by parsing the manifest). |
| 11 Legible at 360 px | PASS | `client/chrome.css:496` appended block: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; `@media (max-width: 640px)` hides `.plate-units` and the centrebar names; `@media (max-width: 420px)` two-column scorebug. Feed reads in words with full province names since `20b9d10`. |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (line 153) → Certify (167) → Upload policies (206) → Upload coworld (304) → Put secret (342); all three workflows present; `docker_smoke.sh` 100755; `policies.json` = 2 `PLAYER_PROMPT` champions (`cogplomacy-diplomat`, `cogplomacy-opportunist`) + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The three-name placeholder gate run over the five files returns no match (verified: `GATE PASSES`). |
| 13 Viewer executes | PASS | Run **32728438824**, `wasm-viewer` job (ID 97435981947) green with `needs: docker-smoke` (ci.yml), `Load the bundle in a real browser` step ran (✓ in job view, no `continue-on-error` anywhere in the workflows) and printed `{"loaded":true,"ms":289,"clock":"SPRING 1901 · PRESS · WAITING ON 7",…,"feed_lines":36}` against the replay docker-smoke produced in the same run. `config.nims` `MODULARIZE=1` + `EXPORT_NAME=CogplomacyReplayModule` and `static_replay.js:140` `CogplomacyReplayModule()` factory come from the same starter (rename-only diffs); no `onRuntimeInitialized` anywhere. `data-replay-loaded` set at the end of `attachReplay`'s makeRenderer callback (renderer.js:1281) after the frame loop starts drawing; `data-replay-error` set/removed in the shell's own `fail()`/retry paths (static_replay.js:56, 107, 136). |
| 14 Chrome is the starter's | PASS | `diff` against `/workspace/starters/cogame-bullwhip`: `client/chrome.css` byte-identical for all 467 starter lines + one appended `/* ---------- Cogplomacy ---------- */` block; `client/replay.html` and `replay-viewer/index.html` are the starter page with only title/wordmark/clock-placeholder text changed, `relayout()` added to the bootstrap, and one appended element (`#centrebar`) — every starter id survives, none removed; `tests/test_viewer.nim` asserts the id list and `viewpanel` **absent** (board always fits the frame, per the note). Transport: `relayout()` measures `#transport` and sets `--band`/`--hudscale` on `document.documentElement`; `#loading { bottom: var(--band); }`; `#endscreen` is inside `#board-wrap` (ends at the band), shown via `classList.toggle("show")` matching `#endscreen.show` (chrome.css:383), and every `setIndex` — beat click, scrub drag, play wrap — calls `updateEndscreen` (renderer.js:1246-1249); beats are labelled `<button type="button">`s with onclick seeks (renderer.js:1372-1391) and all eight emitted kinds have CSS rules (chrome.css appended block). Naming guard: `markDiploBeat`/`buildCentreBar`, disjointness asserted by `tests/test_viewer.nim`. |
| Rider: one parallel batch per turn | PASS | `decideAll` (llm.nim:796-845) builds ONE `RequestBatch` per attempt for every open seat and fires a single `curl.makeRequests`; the server calls it once per phase outside the lock (server.nim:368). No per-seat serial network path exists. |

## Non-blocking observations

- **Item 8's "recorded" is stdout-only for the retry-exhausted path.** A seat whose two LLM
  attempts both fail is answered by the expander inside `decideAll`, but the server applies it with
  `wasScripted = scripted[seat] != skNone or client.disabled` (server.nim:372), so the event's
  `scripted` flag stays `false` for that decision. The fallback **is** countable by phase 60 — the
  sim logs the exact line its log grep looks for (`falling back`, llm.nim:844), and auth-disable
  fallbacks are flagged in events — and this matches the starter byte for byte
  (bullwhip server.nim:296), so I do not count it as blocking; a `fallback: true` field on the
  event would make the replay-side count exact. The reviewer noted the same nuance.
- `pkDone` (N14b) is a benign deviation from the note's type list; the rationale for keeping it is
  sound.
- Dead code retained: starter `describeEvent` (renderer.js), `orderWords`/`powerAdjective` on the
  Nim side, now that the feed wording lives in JS. Harmless; noted by the fixer.
- The `centres` feed line gives counts and deltas but not which centre changed hands (the note's
  example names `+1 Belgium`); needs a new event field, out of scope for this round, engages no
  checklist item.

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| N1 | fixed `35b766d` | llm.nim:399-415 fleet choice + head smoke replay `"kind":"F"` builds | yes |
| N2 | fixed `96df449` | llm.nim:286-306 + `supportFromRank: 2` default | yes |
| N3 | fixed `9f0fe87` | sim.nim:612-622 claims the slot, adds `H` | yes |
| N4 | fixed `ff2f6da` | sim.nim:1278-1319 full field checks + tamper tests | yes |
| N5 | fixed `abae9fe` | server.nim:288-299 shared deadline; :521-526 late prompt ignored | yes |
| N6 | fixed `20b9d10` | renderer.js:1542-1596 words + province names | yes |
| N7 | fixed `a14365c` | orders.nim:465-499 `heldByDislodged`, 4 call sites | yes |
| N8 | fixed `b7fa634` | llm.nim:663-671 + sim.nim:411-425 publish ALL letters | yes |
| N9 | fixed `8c1ed92` | ci.yml step + assert_smoke_artifacts.py; head log `smoke artifacts OK` | yes |
| N10 | fixed `d871fb6` | llm.nim rune-cut error snippets + test_bot:328-329 | yes |
| N11 | fixed `555c5e7` | server.nim:327-333 default fallback, :348 unconditional check | yes |
| N12 | fixed `ac58396` | test_sim: `for kind in EventKind` + dislodgementEpisode | yes |
| N13 | fixed `586a768` | tools/tune_baselines.nim + grid table in head test log | yes |
| N14a | fixed `d20c543` | test_map proper-subset assertion | yes |
| N14b | no change, disputed | types.nim `pkDone` terminal marker; no checklist item engaged | yes |
| N14c | fixed `9711b80` | sim.nim stab scan stops at press/orders + test_sim:440-448 | yes |
| CI claim | run 32728438824 success, 0 × SEAT-COUNT FAIL | confirmed from `gh run view` + full job-log grep | yes |

## Could not verify (and why it does not block)

- **Live LLM behaviour** (auth disable, Bedrock rotation, the retry batch under real transport):
  no credentials in CI or this sandbox. No checklist item requires a live-credential run in phase
  30 — item 8 requires the parse/retry/fallback *code path with tests*, which is present and tested
  (test_bot.nim fixtures for fenced/prose/missing-key/oversize/unknown-pledge); the credential-less
  branch is exercised end-to-end by docker-smoke. Phase 60 is where live behaviour is measured.
  Not counted as blocking because the items as written are verified from the tree and cited CI.

BLOCKING: 0
