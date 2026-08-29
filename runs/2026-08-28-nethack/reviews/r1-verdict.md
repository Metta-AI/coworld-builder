blocking: 0

# r1 verdict — nethack
Head: ae95996519e51b70346499240e0845ad013b3fb8   Checklist: the r1 brief's verbatim ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-batch rider)   Independent read written before reading fixes: yes

Repo read at `/workspace/cogame-nethack` (= Metta-AI/cogame-nethack main). Starter diffed
against `/workspace/starters/coworld-ctf`. CI evidence from run **33230652674**
(`gh run view … --json headSha,conclusion,jobs`: headSha `ae95996…`, conclusion `success`,
jobs `test`/`docker-smoke`/`wasm-viewer` all `success`). I read the design note, the repo
and the full test-file history, and wrote my checklist pass **before** opening
`r1-review.md` or `r1-fixes.md`. Rails honoured as settled: the balance constants
(to-hit 15, startHp 16, regenTicks 12, `min(10, 2+depth)`, packs from DL2),
turn-ends-when-queue-empties (divergence 15), and test 29's eats-clause substitution —
judged only for code↔documentation agreement, which holds (see checklist pass, item 7 note).

## Standing blocking findings

None. Every finding in `r1-review.md` is either resolved at this head (13 findings, fixes
verified real below), an accepted rail, or an advisory divergence now recorded in
`docs/PORTING-NETHACK.md` whose code matches its documentation. My own independent pass
found no checklist item falsified at `ae95996`.

## Refuted / resolved / standing-advisory — disposition of all 22 review findings

The review itself reported **blocking: 0**, so there is no blocking claim to refute. I
attempted to reproduce each advisory finding at the current head:

### Resolved at head (fix verified real, not a test-weakening)
- **F5 → RESOLVED** — `client/broadcast_core.js:60` `const MIN_CELL_PX = 12;`, `:471`
  `fitScale = Math.max(fitScale, MIN_CELL_PX / WIRE_CELL_PX)`; `followCog` →
  `core.panTo((nh.cx + 0.5) * cell, …)` (`client/replay_broadcast.html:4809-4815`),
  forwarded to the worker (`static_replay.js:252-253`, `static_replay_worker.js:222`).
  The board is now genuinely pannable below ~600 px, which is what makes `#viewpanel`
  load-bearing (item 14's stricter reading is now satisfied outright).
- **F6 → RESOLVED** — `src/nethack/driver.nim:100-105` emits `plan`, `fallback` and `say`;
  `tests/test_nethack_replay.nim:56-122` asserts all three live **and** re-derived from the
  bytes with the hash chain clean; the page draws the `ALPHA "…"`, `PLAN` and
  `MISSED THE CALL` rows (`replay_broadcast.html:4553-4560, 4529-4531`). The `eat` event now
  carries the item's name (`sim.nim:574`).
- **F8 → RESOLVED** — `src/nethack/wire_constants.nim:19-26` ends
  `};window.CTF_WIRE=window.NETHACK_WIRE;`, so the byte-identical `chrome_common.js`
  reads real `PlaybackSpeeds [1,2,4,8]`; `tests/test_nethack_viewer.nim:159-177` pins both
  globals and drives every chip through `applyReplayCommand`.
- **F9 → RESOLVED** — the phase dispatch runs inside `try/except CatchableError`
  (`src/nethack/server.nim:446-…, 550-561`): stop record written, `sim.settleFault` sets
  `endRule = fault` and rune-truncated `stopDetail`, `writeArtifacts()` runs, exit 0.
  `tests/test_nethack_engine.nim:190-217` asserts the settlement including
  `stopDetail.runeLen == MaxStopDetailRunes` and `validateUtf8() == -1`.
- **F10 → RESOLVED** — `ParsedReply` now carries disjoint `dropped` (cap overflow →
  `actionsDropped`) and `repaired` (schema-invalid → `repliesRepaired`)
  (`directives.nim:30-40`, `decide.nim:220`); `test_nethack_driver.nim:191-212` asserts
  `repaired == 3, dropped == 0` and `dropped == 15, repaired == 0`.
- **F11 → RESOLVED** — `decide.FallbackCauses` is the note's closed seven-cause set
  (`decide.nim:44-52`); a provider 429 maps to `rate_guard` (`:229-230, 248`);
  `tests/test_nethack_events.nim:58` sweeps every cause literal `decide.nim` can write.
- **F13 → RESOLVED** — `sanitizeSay` cuts at `MaxSayRunes` on a rune boundary first, then
  filters only C0/DEL/C1 controls and the two braces (`directives.nim:45-60`);
  `test_nethack_driver.nim:222-241` asserts the 4-byte-emoji-at-cap case, non-ASCII
  survival (`"weiß 你好 {json}" → "weiß 你好 json"`) and control stripping.
- **F14 → RESOLVED** — the stuck check now measures the destination:
  `sim.cog.stuck > 0 and sim.lichenHolds(sim.cog.x, sim.cog.y) and not sim.lichenHolds(nx, ny)`
  (`sim.nim:421-426`), so only a move that breaks contact with a live lichen fails.
  Rule change carried a `GameVersion` bump to GV2 and a re-cut fixture via
  `tools/record_fixture.nim` (never a hand-made file); the fixture-version sweep test passes.
- **F15 → RESOLVED (measured)** — `tools/ci/renderer_fixture.html:194-230` reads `--band`
  off `:root`, fails any measured element whose `rect.bottom` reaches into it, and fails
  loudly if `--band` is 0 (`:328-330`). Run 33230652674:
  `dom_text: 51 boxes measured across 360px, 640px, 1280px, say=140 runes, 0 failing`.
  The starter's `#killfeed`/`#fpv` offsets clear the band at every width tested; the review's
  own "what would settle it" measurement was made and came back clean.
- **F16 → RESOLVED (the CI half)** — `ci.yml:56-68` runs `check_gameversion.sh` against
  `HEAD~1` (`fetch-depth: 2`) and `test_next_coworld_version.py`; `:176-179` runs
  `tune_baselines.nim --check`; all green in run 33230652674 (`test` job steps
  "Version discipline…" and "The shipped baseline params are the swept pick", both
  `success`). The absent "manifest loads under the installed CLI" step in ci.yml is not a
  checklist object (item 12 enumerates presence/executability/order, all verified);
  `coworld-release.yml` runs `coworld build` → certify at release time.
- **F18 → RESOLVED** — `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` at
  `replay_broadcast.html:4117-4122`; the wider desktop floor is scoped
  `#stage:not(.tiny) .plate .plate-name { min-width: 4.5em; }` (`:4129`), so at the
  embedded width the checklist's 3.2 em rule is the one that decides.
- **F19 → RESOLVED (compensated and gated)** — `canvas_text.total = 0` is structural (this
  viewer draws DOM text; the board canvas carries one server-composited sprite). The
  compensating gate is the renderer fixture: box-in-frame, band-clear, unclipped
  (`scrollWidth/scrollHeight`), full-length strings, at 360/640/1280 px; a failure sets
  `data-replay-error` (`renderer_fixture.html:412`), which `viewer_smoke.mjs` turns into a
  red step. Its own ci.yml step ("Drive the worst-case renderer fixture") ran and passed.
- **F20 → RESOLVED (the JS half)** — the `$('fpv-hp')`/`$('fpv-gear')` readers and the
  whole `fpvMap` pipeline are gone (177 lines removed, `f8b18f2`);
  `test_nethack_viewer.nim:61-68` asserts neither the ids nor `renderFpvMap`/
  `syncFpvMapShape`/`fpvMapCanvas` appear anywhere in the page. Keeping the starter's
  `.flagicon`/`.squad-pip`/`.ec-heart` CSS is correct under item 14 (their inherited
  builders remain; deleting the rules would be the half-rewrite item 14 forbids).
- **F4 → RESOLVED (the checklist-relevant part)** — after F6 the viewer draws model text,
  so item 15(iv)'s fixture condition fires, and `tools/ci/renderer_fixture.html` ships and
  is gated (`ci.yml:271-279` refuses to run without it; `:375-398` drives it). The other
  four artefacts (`wasm_replay_smoke.cjs`, shards, `league_replayer.html`, `labels.nim`)
  are named by the design note, not the checklist, and are recorded as kept divergences in
  `docs/PORTING-NETHACK.md:125`.

### Standing, advisory only (documented; code matches the documentation)
- **F1, F2, F3** — coordinator rails, recorded in `docs/PORTING-NETHACK.md` (divergence 15
  at `:76-82`; the balance table at `:93-98`; the cert-seed row at `:119`). Code matches:
  `driver.nim:110-115` (`turnDone` third exit, `emptyPlan` still burns 40 ticks),
  `mobs.nim:22` `HitThreshold* = 15`, `sim_config.nim:79-80` `startHp: 16, regenTicks: 12`,
  `dungeon.nim:492` `min(MaxMonstersPerLevel - 2, 2 + depth)` with pack gates at `:515, :530`,
  `test_nethack_engine.nim:69-89` (no eat clause; depth/kill/gold/door/≥200 ticks asserted).
- **F7, F12, F17, F21, F22** — advisory divergences from the note, none tied to a checklist
  item, each now recorded in `docs/PORTING-NETHACK.md:117-125`. On F17 I verified the
  decisive fact myself: the starter's own `coworld_manifest_paintbot.json` ships
  `"type": "uri"` for docs and protocols, so `uri` is the forked platform convention and
  item 10's `"text"` is shape illustration, not a byte pin.

### Fixer report audit
| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F4 | part fixed (fixture + gate), part refuted | fixture present, gated, green; 4 artefacts absent but not checklist objects | yes |
| F5 | fixed | MIN_CELL_PX=12 floor + followCog/panTo through the worker | yes |
| F6 | fixed | emits + record/re-derive test + feed rows | yes |
| F8 | fixed | CTF_WIRE alias + chip/transport test | yes |
| F9 | fixed | try/except + settleFault + test | yes |
| F10 | fixed | disjoint counters + tests | yes |
| F11 | fixed | closed cause set + events test | yes |
| F13 | fixed | control-only filter + at-cap emoji test | yes |
| F14 | fixed | lichenHolds destination check + GV2 + re-cut fixture | yes |
| F15 | measured, no defect | fixture band check, 0 failing at 3 widths | yes |
| F16 | part fixed | 3 guards invoked in ci.yml, steps green | yes |
| F18 | fixed | 3.2em unopposed at 360 px | yes |
| F19 | addressed | dom_text gate via data-replay-error | yes |
| F20 | part fixed | JS feeders removed + test; CSS kept deliberately | yes |
| F1–F3, F7, F12, F17, F21, F22 | rails / documented | PORTING-NETHACK.md rows match code | yes |
| history note | duplicate range is a no-op | `git diff a362c6a 4a8c81e` → empty (0 lines) | yes |

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **33230652674**, sha `ae95996…`, conclusion `success`; jobs test/docker-smoke/wasm-viewer all success, no `continue-on-error` anywhere in `.github/workflows/*.yml` (grep exit 1). Test history: I read **every** test-file hunk in `git log -p 2fccbf0..ae95996 -- tests/`. The duplicated range `a362c6a..4a8c81e` is a byte-identical no-op (`git diff a362c6a 4a8c81e` is empty), so the net history is the first fix range. No test file was ever deleted (`git log --diff-filter=D -- tests/` empty), no skip/xfail added (grep over `tests/` clean), no tolerance widened. Exactly two assertions were replaced, both by strictly stronger ones: `check reply.dropped == 3` → `repaired == 3` **and** `dropped == 0` plus a new `repaired == 0` (F10, `a9d21ec`), and `check sanitizeSay(mixed) == "ok"` — which asserted the *defective* ASCII-stripping behaviour — → five assertions on the corrected behaviour incl. rune-cap and UTF-8 validity (F13, `5022589`). All other test changes are additions. |
| 2 replay re-derivation | PASS | `tests/test_nethack_replay.nim:26-54` — record → re-derive for death/turnCap/wallClock/fault + bottom/escaped, `checkReplayHash() == -1` (compared after **every** `stepReplay`, `replays.nim`), equal tick/depth/endRule/endReason; `:180-194` seek re-simulates to identical hash. Viewer derives display from the same re-derivation: `replay-viewer/nethack_replay.nim:56` `initReplayRuntime`, `:84` `advanceReplayFrame`, packet built from the re-simulated `sim` (`replay_runtime.nim:114-142`). The wall-clock/fault stop is a load-bearing record applied by one proc on both sides (`replays.nim` `applyStop`). |
| 3 static viewer | PASS | `coworld_manifest_template.json:27-29` `"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`; `tools/build_replay_viewer.sh` mode 100755, asserted and invoked by path in ci.yml:258-288; the worker fetches only `message.replayUrl` (`static_replay_worker.js:113`); `/client/replay` exists only as the local dev route (`server.nim:50`), declared nowhere. |
| 4 both name spaces | PASS | Observation carries only `"you_are": "Alpha the Digger"` (`sim.nim:932`); real name lives in `results.names[0]` (`sim.nim:989`) and `rosterJson` (`broadcast.nim:64`); the CI smoke scorebug read `DELVER ALPHA THE DIGGER` — real policy name + alias, viewer side. `showPlayerLabels: false` in all three game_configs; register record is redacted (`decide.nim:78-89`, `test_nethack_replay.nim:151` `not record.hasKey("prompt")`). |
| 5 degrade-never-hang | PASS | Attempt 1 / retry via `makeRequests(batch, deadlineMs div 1000)` = 6 s / 3 s (`decide.nim:191-209`); outer `turnBudgetMs` 9.5 s monotonic (`:135, :187`); `turnSpacingMs` sleep bounded 2.6 s (`:175-179`); rate guard (28/60 s, `:164-172`); budget guard (`:140-147`); engine stop at 660 s top of every loop iteration (`server.nim:360-368`); lobby `lobbyJoinTimeoutTicks` (`:461`); gameOver hold bounded (`:549`); fault caught (`:555-561`). 660 s ≤ 720 s = 60 % of 1200, asserted for every variant (`test_nethack_manifest.nim:93-97`). Guarded loops carry `guard < 20_000` (`replay_runtime.nim:33`, `replays.nim` seek). |
| 6 num_agents | PASS | `num_agents: 1` in `variants[0].game_config`, `variants[1].game_config`, `certification.game_config`; `len(certification.players) == len(certification.game_config.players) == 1` (read programmatically). `docker_smoke.sh:106-150` enforces all four invariants + the `SMOKE_SEATS` cross-check (`:54`, substituted `1`), every message prefixed `SEAT-COUNT FAIL:`. `grep -c "SEAT-COUNT FAIL"` over the full run-33230652674 log = **0**; smoke line `smoke OK: seats=1 … reason=complete`. |
| 7 scripted baseline | PASS | `test_nethack_engine.nim:11-21` records a real all-scripted episode, asserts `reason == "complete"`; legality over 300 states × both baselines (`test_nethack_driver.nim:67-160`: ≤10 actions, enums, travel bounds, held letters, ≤40 primitives, corner-cut clean, empty queue → wait); tuning: `tools/tune_baselines.nim` 48-combination × 40-seed sweep, pick pinned in `tools/ci/baseline_tuning.json`, asserted by test **and** re-run in CI ("The shipped baseline params are the swept pick", success). |
| 8 LLM reply handling | PASS | `extractJsonObject` outermost-balanced-brace, fence/prose tolerant (`directives.nim`; fence test at `test_nethack_driver.nim:247`); retry exactly once (`while attempt < 2`, `decide.nim:186`) with a re-prompt nudge; fallback is the **same** `delverPlan` proc the baseline uses (`decide.nim:110-114`; identity test `test_nethack_driver.nim:162-170`); recorded three ways: `fallback` chat record (`decide.nim:69-76`), `results.fallbackTurns`, and the `will retry` / `falling back` log phrasings (`:238, :253`). |
| 9 rune-safe truncation | PASS | `truncateRunes`/`runeSubStr` applied to say/notes/prompt/label/messages/error text/stopDetail; tests feed 4-byte emoji exactly at the caps: `test_nethack_driver.nim:222-241`, `test_nethack_replay.nim:227-271` (900×U+1F480 through `replay_summary.py`, strict-UTF-8 parse), `test_nethack_engine.nim:190-213` (`stopDetail.runeLen == MaxStopDetailRunes`, `validateUtf8() == -1`). |
| 10 manifest validates | PASS | `game.docs` = readme + 3 pages each `{id, title, content:{type,value}}`; `game.protocols` carries **both** `player` and `global` as `{"type","value"}` objects (read programmatically). `"type": "uri"` matches the starter's own shipped manifest (`coworld-ctf/coworld_manifest_paintbot.json`: readme `uri`, pages `uri`, protocols `uri`) — the checklist's `"text"` is the content-object shape, not a byte pin. `results_schema`/`config_schema` closed; key-set equality asserted at runtime (`test_nethack_engine.nim:49-66`). |
| 11 legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` (`replay_broadcast.html:4117-4122`); desktop-only 4.5 em scoped `#stage:not(.tiny)` (`:4129`); labels hidden under `.tiny` (`:4387-4388`), toggled at `boardW <= 620` — the starter's threshold for the sub-640 px embed. |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build the Coworld manifest (:159) → Certify locally (:173, `--timeout-seconds 300`) → Upload the policies (:216) → Upload the Coworld (:314) → Put the Coworld secret (:410). Three workflows present; `docker_smoke.sh` and `build_replay_viewer.sh` mode 100755, bit-asserted and invoked by path; smoke uses the image built in the same run (ci.yml:206→218). `tools/ci/policies.json`: 4 distinct policies — two `PLAYER_PROMPT` champions, champion #2 `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, plus `PLAYER_SCRIPTED=delver` and `=bumbler`. Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files → **no matches, exit 1**. |
| 13 viewer executes | PASS | (i) `wasm-viewer` green at `ae95996` with `needs: docker-smoke` (ci.yml:245); step **"Load the bundle in a real browser"** ran, conclusion success, no `continue-on-error`: `{"loaded":true,"ms":345,…}`, soak `1/322 → 97/322 → 121/322`. (ii) `data-replay-loaded` set in the worker's `loaded` branch after `ingestPacket()` drew the first frame (`static_replay.js:161`, `static_replay_worker.js:126-131`); `data-replay-error` in `showFailure()` (`static_replay.js:19-20`). (iii) The replay records **no lobby ticks** — hashes are written only inside the Playing turn loop (`server.nim:504` area) — so tick 0 of the axis *is* the game start; `startTick = 0` (`replays.nim:122, :145`) and every seek clamps to `max(0, tick)`, i.e. to the game start; the bitworld codec has no `gameStarts` record to skip, and `beginTurn` flips the replay sim out of Lobby on the first command turn (`d544d55`), so no lobby chrome can show. A late-gameStart replay is unconstructible in this format. (iv) `replay-viewer/config.nims` has **no** MODULARIZE/EXPORT_NAME; the worker bootstraps on `Module.onRuntimeInitialized` (`static_replay_worker.js:188`) and imports `wire_constants → broadcast_core → nethack_replay` in order — all four viewer files from coworld-ctf, pinned by `test_nethack_viewer.nim:209-217`. |
| 14 chrome provenance | PASS | (i) `client/chrome_common.js` **byte-identical**: `diff` against the starter empty; sha256 `7ace7287…ced72f7c`, pinned by test. (ii) `replay_broadcast.html` is the starter's page (241 821 B vs 234 070 B — it **grew**) with the banner `NETHACK additions to the inherited coworld-ctf chrome` at `:4090`; I diffed the pre-banner half against the starter in full: only the note's listed removals (`#povBadge`, `#fpv-hp`/`#fpv-gear`, `#fpv-map*`, the ctf/paintball beat CSS), the note's label re-mappings, the `PaintballChrome→NethackChrome`/`CtfStaticReplay→NethackStaticReplay` renames and the plate-content retarget. CSS sections 1–5 present and otherwise unmodified. (iii)(a) `relayout()` measures the transport and sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (`:4036-4061`); (b) fixture-measured band clearance at 3 widths, 0 failing; (c) `#endcard { bottom: var(--band, 0px) }` (`:961`), shown via `.on`, removed on every non-gameover frame (`:1978`) which covers every seek; (d) beats are labelled `<button>`s that seek (`nhBeat`, `:4423-4443`, `title` + `aria-label` + `CTX.send('s:'+tick)`), CSS for exactly the ten emitted kinds (`:4285-4331`), inherited `markBeat('kill'…)` path unreachable because `nhEvent` returns true for every game kind (`:3224-3228`, `:4498-4501`). (iv) `#viewpanel` kept **and** the board is genuinely pannable (48×18 at ≥12 px/cell — `MIN_CELL_PX = 12`, camera follows the cog), exactly the case the note names. |
| 15 drawn strings | PASS | Main smoke: `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` — total 0 is structural (DOM-text viewer; board canvas carries one composited sprite) and is **not** relied on as evidence. The gate is the worst-case renderer fixture: own ci.yml step ("Drive the worst-case renderer fixture", success), loads the shipped page in an iframe, full-cap 140-rune mixed emoji/CJK/latin say, ten-verb plan, fallback, tombstone per end rule, at 360/640/1280 px; asserts in-frame, band-clear, unclipped and **full-length** (`renderer_fixture.html:291-292` fails if the say row shortens); failures set `data-replay-error` → `viewer_smoke.mjs` exits 1. Evidence line: `dom_text: 51 boxes measured across 360px, 640px, 1280px, say=140 runes, 0 failing`. Feed say/plan rows wrap inside the feed's reserved column (band sized from MaxSayRunes); ellipsis is used only on the plate-name label. |
| batch rider | PASS | Single seat: exactly one provider request per turn (plus ≤1 retry) through the starter's `RequestBatch`/`makeRequests` machinery (`decide.nim:199-209`) — the one-batch-per-turn shape carrying a batch of one; no sequential fan-out exists. |

## Non-blocking observations
- The docker-smoke replay is saved as `dist/smoke/replay.json` although it is binary
  `COWLDNET` (the viewer loads it fine and `SMOKE_REQUIRE_REPLAY_JSON=0` is set); the name
  is misleading, nothing more.
- `#zoom-read` still reads `FIT` at the embedded width where the board is now a panned
  window (already NOTED by the fixer).
- The pushed history contains a byte-identical duplicated fix range
  (`a362c6a..4a8c81e`, verified empty diff) with an in-history explanation (`d570e64`).
  Honest and harmless, but graders of `git log -p -- tests/` will see each fix's test hunk
  applied, reverted and re-applied — worth a line in any future run log.
- `docs/plans/2026-08-28-nethack-design.md` (the copied note) still describes pre-fix
  behaviour for F5/F6/F10/F11/F13/F14; `docs/PORTING-NETHACK.md` is the maintained record.

## Could not verify (and why it does not count as blocking)
Nothing on the checklist was unverifiable from the tree or the cited CI evidence. Two
facts remain outside CI's reach and are not checklist items: real-latency LLM budget
behaviour (docker-smoke runs keyless; every bound is statically verified and the budget
arithmetic closes at ≤ ~674 s < 720 s) and hosted-certifier acceptance of the manifest
(the starter's own certified manifest uses the identical `uri` docs shape).

BLOCKING: 0
