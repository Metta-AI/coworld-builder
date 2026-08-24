blocking: 0

# r1 verdict — cogchemists
Head: `11aa1a1d819fdef2ddf110c0694818b0a3be17d8`   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + simultaneous-decision rule)   Independent read written before reading fixes: **yes** (repo, design note, starter diffs, CI logs and the review were all read and my notes formed before `r1-fixes.md` was opened; the fixes file was read last, for the audit table only).

Verified `git -C /workspace/build/cogchemists rev-parse HEAD` = `11aa1a1d819fdef2ddf110c0694818b0a3be17d8`, tree clean. CI run **32705845919** on `main` at exactly this sha: conclusion **success** (verified via `gh run list` + `gh run view --json jobs`).

## Standing blocking findings

None. Every finding of the r1 review is either fixed at head (verified against the code, not the fixer's table) or was never a checklist violation, and my own independent checklist pass found nothing the review missed that blocks.

## Refuted / resolved review findings

### B1 — LLM fallback recorded `scripted: false` → FIXED at head (was real at 5a82157)
- The review's trace was correct at its sha: `decideAll` returned only `seq[Action]` and the server recomputed the flag from pre-batch knowledge.
- Evidence at head (commit `e916f30`): `src/cogchemists/llm.nim:741` — `decideAll` now takes `fromScript: var seq[bool]`; set `true` at `llm.nim:760` (configured-scripted / disabled) and `llm.nim:799` (post-retry fallback: `result[index] = scriptedAction(sim, seat, skAssayer); fromScript[index] = true`). Server records it verbatim: `server.nim:321` `let wasScripted = fromScript[position]` → `server.nim:323` `state.sim.applyAct(seat, decision, wasScripted)`. Test `tests/test_bot.nim:172-200` ("a seat whose reply fails twice is recorded as scripted") builds a **live** client pointed at `http://127.0.0.1:1` and asserts `fromScript == @[true, true, true, true]`. Not reproducible at this sha → fixed, not standing.
- Checklist item: 8.

### N1 (byte-sliced error text) → FIXED (`2e48a55`)
- All five sites now go through rune-safe `cleanText`: `llm.nim:662` (no-JSON message), `:699` (auth detail, 400), `:708`/`:713` (429/other, 300), `:722` (max_tokens head, 160). Was non-blocking anyway (checklist 9 scopes to strings reaching the replay; none of these do).

### N2 (smoke printed but did not assert the end reason) → FIXED (`10cffb4`)
- `tools/ci/docker_smoke.sh:315-316`: `if reason != "complete": raise SystemExit(...)`. Confirmed in the head run's log: `episode end reason: complete` / `smoke OK: seats=4 results=281B replay=10742B reason=complete`.

### N3 (guarantees claimed over a truncated 3000-chemistry sample) → FIXED (`11aa1a1`)
- `chem.nim`: `truncated(sample)` = `sample.len >= BotSampleCap`; `certainPotion` → `poNone`, `alwaysExposes` → `false`, `canBeNegative` → `true` when truncated. New test in `tests/test_chem.nim` compares the predicates against an independent lexicographic enumeration. Baseline means unchanged across all four seeds (commit message records before/after).

### N4 (`applyAct` vs a separate step machine) → REFUTED as a defect
- Verified: the event stream is exactly the note's (`start, round, phase, act×4, …, exhibition, end`), and the one-structural-event-per-`advance` split is precisely what lets `replayMatch` hold `frames.len == events.len + 1` (checklist 2). API wording difference only; no checklist item names the internal API. Agree with the fixer's disposition — reached independently.

### N5 (endcard verdicts / truth row absent from the canvas) → FIXED (`7184ee2`)
- `client/renderer.js:524-530` computes `verdict = chemistry[seal.ingredient] === seal.claim` per standing seal (gated `revealed = chemistry.length === 8`); `:645-649` draws `TRUE +5` (amber) / `FALSE −6` (red); `:536-573` `truthRowH`/`drawTruthRow` draw the eight true signatures under the board; `:216` wires it into `draw()`. Was non-blocking (stage decoration, no checklist item) and is now the note's shape.

### N6 (Press royalty doubling missing from the system prompt) → FIXED (`a5a7191`)
- `llm.nim:449-451`: "buy mortar (-4 coin) or buy press (-5 coin), once each. The Magic Mortar spares the second card of every test; the Printing Press pays +3 instead of +2 for a publish AND doubles your royalties to 2 coin a round."

### N7 (two bootstrap variable renames in the replay pages) → REFUTED as a defect
- Verified independently: `renderer.js` itself declares `var scheme`/`var socket` inside `attachLive`, and `tests/test_viewer.nim:54-67,141-142` collects renderer names **at any depth** and forbids page-level collisions — keeping the starter's names would fail the anti-shadowing test. Nothing removed: my full `diff` of both pages against the starter shows only title, wordmark, `#clock` text, the appended `#labbar`, the sanctioned `relayout()`/`buildLabBar()` bootstrap, the `labbar:` option, and the two renames.

### N8 (missing endorse sub-assertions) → FIXED (`f38bd37`)
- `tests/test_sim.nim:288-293` (burned seal → `no_such_theory` for previous endorser and a fresh seat), `:434-441` (recorded `rejected:already_endorsed` event with the +1 stipend). Tests only; strengthens.

### N9 (test 16's "no signature the facts do not imply" unasserted) → FIXED (`ac6a1c1`)
- `tests/test_sim.nim:577-597`: per ingredient, the frame's grid length equals an independent `solveGrid(sim.knownFacts(seat))`, the truth stays among candidates, and an unsolved ingredient is never printed pinned in the prompt.

### N10 (replay grid equality final-frame-only, on a fact-free episode) → FIXED (`fe91cb5`)
- `tests/test_sim.nim:627-680`: the episode now mints facts (`test_self`/`sell`), live grids are recorded after **every** event (with a one-event-per-step `doAssert`), all four grids are compared on **every** re-derived frame, plus a non-vacuity check (`narrowed > 0`) and the final full `tableStateJson` equality.

### N11 (release-only perf budgets) → REFUTED as a defect
- Verified: `tests/test_chem.nim:9-10` gates 25/400 ms on `-d:release`; ci.yml runs both modes on every push, so the note's "native" bound is exercised per commit. No test loosened.

### N12 (deadline once per phase, not before the retry batch) → REFUTED as a defect
- Verified: `server.nim:289-296` tests the deadline immediately before `decideAll` — matching the note's own "checked before every LLM batch, i.e. only ever between phases". Bound: every wait inside a phase is explicit (curl timeout 20 s ×2, spacing floor 10 s), so worst-case overshoot past the deadline is one phase ≈ 50 s; the shipped configs (cert 4 rounds, variants 6 rounds) have a full-play ceiling ≈ 663 s < 720 s so the deadline path is a safety net, and even when it fires the episode settles with ≥ 400 s of margin before the 1200 s platform kill. Item 5 is not falsified.

### N13 (`you.facts` in the player frame) → REFUTED as a defect
- Verified: §Per-seat observation item 6 requires the seat's own facts; the manifest's `game.protocols.player` documents `facts` in the frame; code, note (normative list) and manifest agree. The protocol sketch elsewhere in the note is the abbreviation.

### Review's "could not determine" items, adjudicated
- **Checklist 7, "tuned with a grid harness"**: verifiable from the tree. The grid harness is `tests/test_bot.nim:69-131` — a seeds × compositions grid (`[1,7,11,42]` × {all-assayer, all-quack, mixed}) run in CI both modes, echoing both baselines' mean scores per seed so drift is visible (the note's own test 20 defines exactly this as the tuning instrument), and commit `11aa1a1`'s message records the harness's numbers before/after a parameter-affecting change (assayer 11.9/10.95/10.95/10.6 unchanged; quack echoed too). Parameters are measured against that grid, not guessed. Verified — not blocking.
- **`/client/replay` route vs checklist 3**: the manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json:16-18`) and contains no pod path; the live `GET /client/replay` server route and its docs mention are the starter's own inherited spectator infrastructure (the starter's manifest text mentions the same route), and the release workflow hard-fails certification unless the **static** bundle is reported (`coworld-release.yml:195-204`: "a pod-served /client/replay viewer is not acceptable"). Item 3's target — the replay *viewer* declaration — is satisfied. Not blocking.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run **32705845919**, `main`, headSha `11aa1a1…`, conclusion `success`; `test`/`docker-smoke`/`wasm-viewer` all success. `git log -p --since=2026-08-24T06:19Z -- tests/`: 8 commits; the only removed `check` lines were replaced by `doAssert` with messages (5a82157), everything else adds assertions/tests; no skip/xfail/tolerance widening/file removal. |
| 2 Replay re-derivation, frame by frame, viewer uses it | PASS | `sim.nim` `replayMatch` raises on tampered chemistry/hands/demands/draws/potions; `tests/test_sim.nim:627-680` compares all four grids on **every** frame + final full `tableStateJson`; replay bytes carry no `states` (server writes protocol/names/policyNames/config/events/results) — `states` are produced by re-derivation in `replay-viewer/cogchemists_replay.nim:38-40` (`replayMatch` + `tableStateJson`) and `attachReplay` draws `states[index]`. |
| 3 Static viewer | PASS | `coworld_manifest_template.json:16-18` `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, is the `coworld build` hook (invoked by `coworld build`, gated in `coworld-release.yml:195-204`); shell fetches only `?replay=<url>`; no pod path in the manifest. |
| 4 Both name spaces | PASS | aliases from seeded `tableNames` (`sim.nim:240`); policy names only in `resultsJson` (`sim.nim:791`) and spectator `policyNames` (`server.nim:72-89`); `makeNameMap`/`applyNames`/`isBaselineFiller` at `renderer.js:893-931`. |
| 5 Degrade-never-hang | PASS | connect wait bounded (`server.nim:221-229`, 180 s); `PlayBudgetFraction = 0.6` deadline tested before every batch (`server.nim:289-296`); LLM `makeRequests(batch, 20 s)` (`llm.nim:777`); spacing floor bounded (`llm.nim:724-733`); `endEarly` runs the exhibition then settles `deadline` (idempotent, tested); pacing clamped by `sampleEpisode`; player loop `try/except` exits 0; ceiling ≈ 663 s < 720 s for shipped configs. |
| 6 num_agents | PASS | `num_agents: 4` in `standard`, `silent-academy`, `certification.game_config`; config_schema pins integer min 4 max 4; `docker_smoke.sh:106-151` enforces all four invariants + independent `SMOKE_SEATS` cross-check before any container; grepped the full head-run log: `SEAT-COUNT FAIL` occurs **0** times. |
| 7 Scripted baseline full legal episodes | PASS | `tests/test_bot.nim:41-46` `doAssert showAct(decision) in legalMoves` at the moment played; `:82` `reason == "complete"` for seeds × compositions; coin/hand-cap doAsserts; tuning harness = the seeds×compositions grid echoing both means (`:110-131`) + `11aa1a1`'s recorded before/after numbers. |
| 8 LLM reply handling | PASS | `extractJsonObject` = `find('{')`..`rfind('}')` (prose tolerated, asserted `test_bot`); `for attempt in 0 .. 1` = one retry with the invalid-reply hint (`llm.nim:763-772`); fallback recorded via `fromScript` → `event.scripted` (`llm.nim:795-799`, `server.nim:321-323`), tested with a live failing client. |
| 9 Rune-safe truncation | PASS | `cleanSay`/notes `runeSubStr` (`sim.nim:479-491`); reply fields via `cleanText` (`llm.nim:292-298`); prompt 4000 runes both ends; error text now `cleanText` everywhere; `tests/test_sim.nim:491-517` feeds `é×400`/`ø×800` at the caps, asserts `validateUtf8() == -1` and a strict re-parse of the serialised events. |
| 10 Manifest validates | PASS | `game.docs.readme = {type:"text",value:…}` + 3 pages each `{id,title,content:{type:"text",value:…}}`; `game.protocols` carries both `player` and `global` (verified by JSON parse, not grep). |
| 11 Legible at 360 px | PASS | `chrome.css:280-292` `.plate-name { flex: 1 1 auto; … min-width: 3.2em; }` (starter's, byte-identical prefix); `.plate-label { display: none; }` under `@media (max-width: 640px)` in both the starter block (`:460-461`) and the appended block (`:603-604`); 420 px two-column scorebug kept. |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: build (`:153`) → certify (`:167`) → upload-policies (`:206`, comment pins "BEFORE upload-coworld") → upload-coworld (`:309`) → secret put (`:342`, "AFTER"); three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep over the five files returns nothing (exit 1 from grep → gate exits 0); the four documented runtime `<…>` names are the expected residue. |
| 13 Viewer executes | PASS | run 32705845919 `wasm-viewer` success **including** step "Load the bundle in a real browser" (ran, succeeded, no `continue-on-error` anywhere in the workflows), `needs: docker-smoke` (`ci.yml:212`); smoke output `{"loaded":true,"ms":277,…}`, scrub readouts differ (`ROUND 2/4 · LAB…` / `ROUND 3/4 · MARKET…` / `FINAL · SPROCKET 10.4`), soak kept advancing, `data-replay-error` never set; markers: `data-replay-loaded` set at `renderer.js:1770` after the first `renderer.draw(view)` of the frame IIFE, `data-replay-error` set in `static_replay.js:56` and cleared on retry (`:107,:149`); `config.nims:38-39` `MODULARIZE=1` + `EXPORT_NAME=CogchemistsReplayModule` matched by the shell's factory call `CogchemistsReplayModule()` (`static_replay.js:153`), no `onRuntimeInitialized` anywhere — same starter both sides (my own diffs against bullwhip confirm shell and flags are the starter's, renamed). |
| 14 Chrome provenance | PASS | `client/chrome.css` prefix before the single `/* ---------- Cogchemists ---------- */` banner is sha1 `8f0d16397cb227a427ec1112d39c180f1aef1bfd` = the starter file exactly (computed myself); both replay pages are the starter's, my full diff shows zero removals, every starter id present, `#labbar` the one appended element under a banner comment; `relayout()` measures `#transport.offsetHeight` into `--band` + `--hudscale` on `document.documentElement` and calls `fit()` from the same function (`replay.html:52-66`, `index.html` identical); overlays (`#lightpool`/`#grain`/`#endscreen`) absolute inside `#board-wrap`, `#loading { bottom: var(--band); }` (`chrome.css:600`); endcard uses `#endscreen.show` (`chrome.css:383`) and **every** seek goes through `setIndex` → `updateEndscreen(…, index >= events.length …)` (`renderer.js:1718-1739`); beats are `<button type="button">` with `title`/`aria-label`/`onclick` seek (`markChemBeat`, `renderer.js:1548-1563`), `beatKind` emits exactly the seven kinds styled in the appended CSS (`chrome.css:548-580`), asserted by `tests/test_viewer.nim`; no `#viewpanel`/`zoomAt`/`setZoom`/`attachMinimap` anywhere (grep: zero hits) — fixed arena, correctly absent. |
| Simultaneous batch rule | PASS | one `RequestBatch` per attempt, one `curly.makeRequests` for all open seats (`llm.nim:766-777`); no per-seat sequential call exists; retry is a second smaller batch, not a loop of calls. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed `e916f30` | `fromScript` out-param wired llm→server→event; live-client fallback test present, green in CI | yes |
| N1 | fixed `2e48a55` | all five slices now `cleanText`; rune test added | yes |
| N2 | fixed `10cffb4` | `docker_smoke.sh:315-316` asserts `complete`; head-run log shows the path executed | yes |
| N3 | fixed `11aa1a1` | `truncated()` guard on all three guarantee predicates; brute-force test added; means unchanged | yes |
| N4 | refuted, no change | event stream matches the note; split is what item 2 needs | yes |
| N5 | fixed `7184ee2` | verdict tags + truth row on canvas, gated on `chemistry.length === 8` | yes |
| N6 | fixed `a5a7191` | Press royalty doubling now in the prompt text (`llm.nim:449-451`) | yes |
| N7 | refuted, no change | renames required by the anti-shadowing test; nothing removed | yes |
| N8 | fixed `f38bd37` | both sub-assertions present (`test_sim.nim:288-293`, `:434-441`) | yes |
| N9 | fixed `ac6a1c1` | independent `solveGrid` cross-check per ingredient in the split test | yes |
| N10 | fixed `fe91cb5` | per-frame grid comparison + non-vacuity; fact-minting episode | yes |
| N11 | refuted, no change | release = native; both modes run in CI | yes |
| N12 | refuted, no change | code matches the note's operative phrasing; bounds hold | yes |
| N13 | refuted, no change | note's normative list + manifest both name `facts` | yes |

No disposition in the fixer's table disagrees with my own verification; the fixer changed no production behaviour under a "refuted" label and loosened no test anywhere.

## Non-blocking observations (mine, new this round)

- `stExhibition` (`sim.nim` step enum) remains an unreachable branch (also noted by the fixer). Dead vocabulary, no behaviour; advisory only.
- The viewer smoke's soak line prints `(null -> null -> null)` because the harness's optional `#tick` selector has no element on this page; the pass came from clock/scorebug moving in both intervals (`viewer_smoke.mjs:400-403`, `.some()` over `["clock","tick","scorebug"]`). Cosmetic; the check is not vacuous.
- The extra blank line before the chrome.css banner is inside the appended block's leading `"\n"` as the provenance test defines it; the prefix is byte-exact to the starter. No action.

BLOCKING: 0
