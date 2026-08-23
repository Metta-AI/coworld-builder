blocking: 0

# r1 verdict — 2026-08-23-eleusis
Head: 244401dcbba70a7bb73a519a59e2b7c7267878e9   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Judged fresh: repo read in full (sim, llm, server, player, both test files, all four viewer
files, all client files, all three workflows, docker_smoke.sh, policies.json, manifest,
build hook), diffed against `/workspace/starters/cogame-bullwhip`, CI cited from
`gh` for Metta-AI/cogame-eleusis. Independent notes were written before opening
`r1-review.md` or `r1-fixes.md` (archived at /tmp/judge-independent-notes.md).

## Standing blocking findings

**None.** Neither the reviewer's findings (all twelve were filed non-blocking, and all were
addressed on main before this verdict) nor my own independent checklist pass produces a
finding that falsifies a checklist item at head 244401d.

## Refuted

**None refuted.** The review contained zero blocking findings, so there was nothing to refute
at the blocking level. I attempted to refute each of the twelve non-blocking observations
anyway, by reproducing the "was" state at the reviewed sha 529eb68 and re-reading the head:

| finding | at 529eb68 (reviewed sha) | at head 244401d |
|---|---|---|
| N1 fallback not on event | CONFIRMED — `Decision` had no `fallback` field; `wasScripted = scripted[seat] != skNone or client.disabled` | MOOT — `llm.nim:45-47,597-599` sets `Decision.fallback`; `server.nim:335-338` ORs it in and passes it through; `eventToJson` emits it; `tests/test_sim.nim:489-519` asserts it survives `replayMatch` |
| N2 empty-prompt seat called the LLM | CONFIRMED — short-circuit was `kind != skNone or client.disabled` | MOOT — `llm.nim:526-534` `playsScripted` adds `prompt.strip().len == 0`; `tests/test_bot.nim:145-163` proves no request is built |
| N3 note over-claimed "kept verbatim" | CONFIRMED (prose defect) | MOOT — note amended (69c6066); code unchanged; I verified `isBaselineFiller`/`makeNameMap`/`applyNames`/`clampName` byte-identical to the starter and chrome.css prefix byte-identical |
| N4 fixtures failed config_schema (`tokens` required) | CONFIRMED | MOOT — `required: ["players"]` (manifest:36-38); docker_smoke preflight walks all 4 fixtures; CI log: `config_schema OK: 4 game_config fixtures validate` |
| N5 smoke printed reason, no assert | CONFIRMED | MOOT — `docker_smoke.sh:341-353` exits non-zero outside `{complete,deadline}`; log: `episode end reason: complete` |
| N6 capText cut unmarked | CONFIRMED — `runeSubStr(0, limit)` | MOOT — `sim.nim:649-658` `runeSubStr(0, limit-1) & "…"`; test asserts `endsWith("…")` + valid UTF-8 |
| N7 endEarly left pending pending | CONFIRMED | MOOT — `sim.nim:839-841` discloses every pending as hoard; test pins `hoarded+1`, strip in `secrets`, replay equality |
| N8 discarded test shown settled | CONFIRMED — panel keyed on `!test.open` | MOOT — `TestState.discarded` (`sim.nim:110,857,1005`); `renderer.js:861` keys `!open && !discarded` |
| N9 top-up could seat a used/repeated strip | CONFIRMED — spare pool omitted `sim.used`; last resort filtered nothing | MOOT — `sim.nim:513-531`; test crafts both degenerate branches |
| N10 deadline off when timeout ≤ 0 | CONFIRMED — `playDeadline > 0.0 and …` guard | MOOT — `playTimeoutSeconds` (`server.nim:246-260`) can never return ≤ 0; guard gone; test pins the whole chain incl. 0 and −5 |
| N11 note's worst-case omitted retry batch | CONFIRMED (prose defect) | MOOT — note amended (0987302); code bound is 2 × 40 s per turn, deadline checked before every batch |
| N12 note's example frame stale | CONFIRMED (prose defect) | MOOT — note amended (244401d, docs-only commit) |

Every "was" claim reproduced from `git show 529eb68:…`; every fix verified in the head tree,
not from the fixer's table.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1 CI green, no test loosened | PASS | `gh run list -R Metta-AI/cogame-eleusis --branch main -w ci.yml`: run **32661283184**, headSha 244401d…, conclusion **success**; all 3 jobs + all steps success. `git log -p --since="2026-08-23T17:35Z" -- tests/`: 8 commits, additions only — the only deleted lines are two import lines replaced to add modules (`test_bot.nim:7-8`); no assertion removed, no tolerance widened, no skip/xfail, no file removed |
| 2 replay re-derivation | PASS | `sim.nim:1188-1260` `replayMatch` replays decision events, checks `test`/`settle`/`end`/verdicts against re-derivation; wasm module (`eleusis_replay.nim:50-51`) emits `states[i] = benchStateJson(frames[i])` from the same sim, plus seed→ruleId assertion (:40-45 → hard `data-replay-error` via `static_replay.js:56`); tests: `frames.len == events.len+1`, final-frame string equality live vs replay (both complete and deadline), tampered `test` event raises (`test_sim.nim:521-564`) |
| 3 static viewer | PASS | manifest:16-18 `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755 (`git ls-files -s`), ci.yml:225-249 asserts + runs it; shell fetches only the `?replay=` URL (20 s AbortController) and same-origin assets; no pod viewer declared — the server's `GET /client/replay` debug route is starter parity (`bullwhip/server.nim:470` has the identical route) and is pinned by the design note |
| 4 both name spaces | PASS | `tableNames` seeded CogNames shuffle (`sim.nim:358-369`); prompts and player frames carry aliases only (`llm.nim:269`, `server.nim:453,111-113,208-217`); `policyNames` ride replay+/global; viewer `makeNameMap`/`applyNames`/`isBaselineFiller` byte-identical to starter (`renderer.js:573-609`); `resultsJson.names` = policy names |
| 5 degrade-never-hang | PASS | connect wait ≤ `playerConnectTimeoutSeconds` 180 s (`server.nim:266-274`); play deadline = 60 % of timeout, checked before **every** batch (`server.nim:291,308-314`), and `playTimeoutSeconds` can never be ≤ 0 (:246-260, tested); LLM batch bounded `llmTimeoutSeconds` 40 (`llm.nim:569`), exactly one retry; spacing sleeps bounded; artifact POST 60 s; 20 s grace then `quit(0)`; only unconditional loop exits on `done` or deadline |
| 6 num_agents | PASS | `num_agents: 5` in standard/open-science/closed-shop and certification.game_config; `docker_smoke.sh:106-151` enforces all four invariants + independent `SMOKE_SEATS` cross-check, every violation prefixed `SEAT-COUNT FAIL:`; grep of the full run-32661283184 log: **0 occurrences of `SEAT-COUNT FAIL`**; `smoke OK: seats=5 … reason=complete` |
| 7 scripted baseline full legal episodes | PASS | `test_bot.nim:73-91`: 5 seeds, mixed openbook/hoarder, `reason == "complete"`, `checkLegal` on every decision **before** apply; `:93-107` ≥ 70 % final-test accuracy over 10 seeds. Grid harness: the baseline is parameterless (version-space argmin + majority vote, seeded sweep) — nothing to grid; the ≥ 70 % gate is the quality evidence. Not counted as blocking: the clause's target ("not guessed") is vacuous for a parameter-free baseline, and the legality/completion halves are directly asserted |
| 8 LLM reply handling | PASS | `extractJsonObject` tolerates prose/fences (`llm.nim:389-401`, tested); `for attempt in 0 .. 1` with invalid-reply hint (:557-566); probe-sim legality pre-check (:580-586); fallback = openbook recorded as `fallback: true` on the event and re-derived by `replayMatch` (tested, `test_sim.nim:489-519`) plus the stdout line phase 60 greps |
| 9 rune-safe truncation | PASS | `capText`/`cleanText` `runeSubStr` with `…` marker; prompt cap `runeSubStr(0, 4000)` (`server.nim:500-501`); byte-sliced error snippets go to stdout only, never into a GameEvent; tests feed 200/900 multi-byte runes at the caps and assert runeLen, `endsWith("…")`, `validateUtf8() == -1` on fields, events and serialised payload (`test_sim.nim:566-597`, `test_bot.nim:203-209`) |
| 10 manifest validates | PASS | `game.docs` = `{readme:{type,value}, pages:[{id,title,content:{type,value}}×2]}` exactly; `game.protocols` carries both `player` and `global` |
| 11 legible at 360 px | PASS | `chrome.css:280-292` `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }`; `:460-461` `.plate-label { display: none }` under 640 px; appended 3/2-column scorebug wraps all five plates |
| 12 release order + scaffold | PASS | `coworld-release.yml`: Build (:153) → Certify (:167) → Upload the policies (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342); docker-smoke builds its own image in-run; 3 workflows present; docker_smoke.sh 100755; policies.json = 2 × PLAYER_PROMPT champions + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep matches nothing (gate exits 0); only the four documented residue names survive |
| 13 viewer executes | PASS | run **32661283184** `wasm-viewer` success incl. step `Load the bundle in a real browser` (ran, success, no `continue-on-error` in ci.yml); `needs: docker-smoke` at ci.yml:212; smoke printed `{"loaded":true,"ms":291,…}`, 3 differing scrub clocks (`ROUND 2/6` → `ROUND 4/6` → `ROUND 6/6 · FINAL`), soak moved; `data-replay-loaded` set after the first synchronous `renderer.draw` (`renderer.js:1336-1369`), `data-replay-error` from the shell's `fail()` (`static_replay.js:56`); `config.nims` `-s MODULARIZE=1 -s EXPORT_NAME=EleusisReplayModule` paired with the factory call `EleusisReplayModule()` (`static_replay.js:138`) — both files byte-identical to bullwhip's modulo the name substitutions (diff verified); no `onRuntimeInitialized` anywhere |
| 14 chrome provenance | PASS | `chrome.css`: starter's 467 lines byte-identical prefix (diff = single append), one banner-commented eleusis block appended; `replay.html` = starter page + banner-commented `#testpanel`/`#drawer` inside `#board-wrap` (80 vs 74 lines; only text edits title/wordmark/clock placeholder); transport: `relayout()` writes `--band`/`--hudscale` on `document.documentElement` (`renderer.js:1018-1028`), sole writer, bound to load/resize/ResizeObserver; nothing `position: fixed` anywhere; `#endscreen` shown via `.show` (matches `#endscreen.show`), `inset: 0 0 var(--band) 0`, and **every** seek path (track drag/click, beat button) routes through `setIndex` → `updateEndscreen(show = index ≥ events.length)`; beats are labelled `<button type="button">` with aria-label seeking to their tick, and CSS rules exist for all five emitted kinds (`.beat-experiment/.beat-publish/.beat-hoard/.beat-test/.beat-end` + base `.beat-marker` background `var(--tc)`); no `#viewpanel` in starter or fork (grep empty) |
| batch rule | PASS | one `curly.makeRequests` batch per turn for all open seats (`llm.nim:558-569`); the retry is a second parallel batch, never per-seat sequential calls |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| N1 | fixed f783ba3 | `Decision.fallback` + server OR + eventToJson/FromJson + replayMatch carry-through + new test, all present at head | yes |
| N2 | fixed b5e9f8c | `playsScripted` three-way predicate, single definition read by both `decideAll` and the server's `wasScripted`; test builds no request | yes |
| N3 | note corrected 69c6066 | docs-only diff; function-level comparison against starter matches the amended prose (7 byte-identical, rest shape-kept, 3 removed, relayout added) | yes |
| N4 | fixed 1bcd192 | `required: ["players"]`; smoke preflight in docker_smoke.sh:161-184; CI log `config_schema OK: 4` | yes |
| N5 | fixed 7ee8ac0 | reason asserted against the enum, docker_smoke.sh:341-353 | yes |
| N6 | fixed 22718fe | `capText` = marker + rune boundary; tests assert both | yes |
| N7 | fixed dff8233 | `endEarly` hoards every pending via `discloseNow`; recorded on transcript; deadline-replay equality tested | yes |
| N8 | fixed 1193f9b | `discarded` field end-to-end (type, endEarly, benchStateJson, renderer, protocol text, tests) | yes |
| N9 | fixed bc1a7a9 | spare pool excludes `used`; last resort skips `chosen`; both crafted-branch tests present | yes |
| N10 | fixed af22e08 | `playTimeoutSeconds` never ≤ 0; guard removed; chain tested incl. 0/−5 | yes |
| N11 | note corrected 0987302 | docs-only diff; code bound (2 × 40 s/turn) is as the amended note states | yes |
| N12 | note corrected 244401d | docs-only diff (verified `--stat`) | yes |

CI on the fixer's head is a fact I checked myself: run 32661283184, conclusion success, at
244401d, all jobs and steps success, `SEAT-COUNT FAIL` and `CONFIG-SCHEMA FAIL` absent from the
log, viewer smoke `loaded: true`.

## Non-blocking observations (advisory, not counted)

- The run directory's copy of the design note (`runs/2026-08-23-eleusis/design.md`) still
  carries the pre-N3/N11/N12 prose; only the repo's `docs/plans/…` copy was amended. Cosmetic —
  the repo copy is the one that ships.
- `replay.html`'s clock placeholder text (`WEEK 0` → `ROUND 1`) is a third markup text edit the
  design note's "two text changes" sentence does not list. Trivial; the renderer overwrites it
  on the first frame.
- The item-2 test asserts final-frame string equality plus per-event re-derivation checks rather
  than comparing every intermediate frame — there is no recorded per-tick state to compare
  against (the events are the recording), so this is the strongest assertion the artifact shape
  admits.
- `results.json` carries no per-seat fallback total (fixer's own NOTED item); phase 60 counts
  fallbacks from the replay events, which now carry the flag.

BLOCKING: 0
