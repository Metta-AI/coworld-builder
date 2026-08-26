blocking: 0

# r1 verdict — knights-archers

Head: `d1ea75dbb2c11b7e3ff99005bd75888b5dfcbb83`   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Fresh clone at `/tmp/judge-knights-archers`, checked out at the head sha. I formed my own read of
the tree, the CI run and its artifacts before opening `r1-review.md`, and read `r1-fixes.md` last.
The review was written against `00cc62a`; 22 commits landed since. Both of its blocking findings
were true at `00cc62a` and are **fixed at head** — resolved, not standing. Nothing in my own pass
adds a blocking finding.

## Standing blocking findings

None.

## Refuted / resolved

### B1 — no test asserts `results.reason == "complete"` → RESOLVED (was true at 00cc62a)
- Evidence: `tests/test_control.nim:105-137` at `d1ea75d` (commit `6488886`) — block
  `anAllScriptedEpisodeReachesItsNaturalEndAsComplete` runs a four-seat all-scripted episode at the
  shipped values (`maxTicks = 2304, maxGames = 2`) through the sim's own phase machine and asserts
  `run.reason == ReasonComplete`, `results["reason"].getStr() == ReasonComplete`, endRule not
  `sim_fault`/`host_error`, `games == 2`, and `>1000` emitted masks all legal. `test` job green in
  run 32973353268. Checklist item 7 is now satisfied in full (the bounded-orders half and the
  `tools/tune_baselines.nim --check` CI step were already in place at review time).

### B2 — model-authored text unmeasured (`canvas_text.total: 0`, no worst-case fixture) → RESOLVED (was true at 00cc62a)
- Evidence, sprite half: `tests/test_shouts.nim` (commit `01cc35a`) drives the inherited
  `shoutBubbleRectFor`/`shoutBubbleMaxHeight` (`src/kaz/global.nim`) — which had zero callers at
  review time — with a full-cap 10-rune `say` on every cog at nine worst-case positions (top edge =
  the cogchemists case, corners, walls) and asserts the whole rect lands inside the board
  (`tests/test_shouts.nim:61-128`).
- Evidence, DOM half: `replay-viewer/text_fixture.html` exists and is the required worst-case
  renderer fixture: it loads the real `client/replay_broadcast.html` (styles, markup, and the
  appended game block), hands it a full-cap 160-rune `note` + full-cap `say` on all four seats at
  once, at four canvas sizes including 360 px, plays the entrance animation to settle, asserts every
  line is inside the frame **and still full length, never ellipsised**
  (`text_fixture.html:394-400`), mirrors every measured line into a real 2D canvas, and reports via
  `data-replay-loaded`/`data-replay-error`. It is driven by `viewer_smoke.mjs --strict-text-bounds`
  in its own `ci.yml` job `text-fixture` (`.github/workflows/ci.yml`, step "Render the worst-case
  text fixture in a real browser"). Cited CI evidence at head, run 32973353268 (job 98192033219,
  green, step ran): `text-fixture/viewer-smoke.json` →
  `canvas_text: {"total": 204, "outside": 0, "ellipsized": 0, "never_inside": 0}`, console
  `TEXT FIXTURE OK: measured 204 text line(s) across 8 case(s)`. `total` is 204, not 0.
- The defect the fixture caught (a 160-rune commander line growing out of both frame edges,
  `.feed-row { white-space: nowrap }`) was fixed in `ed7c6bc`: the game block's row classes wrap
  inside the feed column; no truncation, no ellipsis.

### N9 (reviewer: spacing floor is a blocking sleep; design says it is not) → the code stands; not blocking
- Verified at `src/kaz/decide.nim:418-421`: `sleep(min(turnSpacingMs, turnSpacingMs - since))` —
  bounded ≤ 9 000 ms, once per turn, outside any lock, with the 690 s engine stop re-checked at the
  top of every server loop iteration (`server.nim:1383-1389`) and the cert fixture at
  `turnSpacingMs: 0`. Checklist item 5 requires every wait to have an explicit bound and the episode
  to settle inside 720 s — worst case 612 s ≤ 690 s stop, asserted by `tests/test_engine.nim` and
  `tests/test_manifest.nim` (`wallClockBudgetSeconds <= 720`, all variants carry 690). The
  divergence is against the design note's prose, recorded in `AGENTS.md`'s divergence table
  (`d1ea75d`). No checklist item is falsified.

### N25 (reviewer: `/client/replay` path exists — "judge's call") → dismissed as non-blocking
- Verified: `src/kaz/server.nim:800-823` answers bitworld's inherited `ReplayClientRoute` with the
  embedded broadcast page for local inspection and the certifier's HTTP contract probe — the same
  route the starter (`/workspace/starters/coworld-ctf/src/ctf/server.nim`) ships. The manifest
  declares `game.replay_viewer = {"bundle": "static-replay-viewer"}` and nothing else, no top-level
  `replay_viewer` (asserted `tests/test_manifest.nim`), and `coworld-release.yml:200-208` hard-fails
  certification unless the log names the static bundle ("`/client/replay` viewer is not
  acceptable"). Item 3's substance — the hosted replay viewer is the static wasm bundle, never a
  pod — holds; the route is inherited framework plumbing, not viewer wiring. Not blocking.

All other review findings (N1–N8, N10–N24) were advisory (non-blocking) by the review's own
classification; I spot-verified the fixes for N1, N5, N6, N7, N8, N10, N11, N12, N14, N15, N16,
N17, N18, N19, N22, N23, N24 at head (see audit table) and the code-right/note-stale rulings for
N2/N3/N4/N13/N20/N21 against `AGENTS.md`'s divergence table.

## Checklist pass (independent)

| item | status | evidence (path:line or run url) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32973353268**, `headSha = d1ea75d…`, conclusion **success**, jobs `test`/`docker-smoke`/`text-fixture`/`wasm-viewer` all green. `git log -p --since=2026-08-26T05:02Z -- tests/`: every hunk additive or strengthening; the single deleted assertion (`test_viewer.nim`, pressure-bar `top: calc(var(--topband…) - 15…)`) pinned the N15 *defect* and was replaced by four stricter checks incl. its negation (commit `061d153`); no skip/xfail, no tolerance widened, no test file deleted. |
| 2 Replay re-derivation | PASS | `tests/test_replay.nim:172-218` re-parses a recorded 2-wave episode and replays with `initReplayRuntime(…, mismatchQuit = true)` — one `writeHash` per tick, a divergent bit raises at its tick. Viewer uses the same re-derivation: `replay-viewer/kaz_replay.nim` imports `kaz/[…replay_runtime, replays, sim]`, `kaz_frame` → `advanceReplayFrame`. CI "Native/wasm hash gate" green in 32973353268. |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, invoked by path (`ci.yml`); worker fetches only the replay URL (`static_replay_worker.js:113`). `/client/replay` is inherited local plumbing, not a pod viewer (see N25 above). |
| 4 Both name spaces | PASS | `tests/test_identity_privacy.nim` (sentinel `ply-sentinel-policy-9f3a`, 17 checks, both directions); viewer-smoke scorebug shows real names (`player-0…player-3`) while feed rows use `KNIGHT-*`/`ARCHER-*`. |
| 5 Degrade-never-hang, 60 % | PASS | Batch deadlines ceil(4500)→5 s / ceil(2000)→2 s into `curly.makeRequests` (`decide.nim:437-459`); monotonic per-turn budget re-checked per attempt (`decide.nim:431`); spacing sleep bounded ≤ 9 s (`decide.nim:418-421`); `lobbyJoinTimeoutTicks` (`server.nim:1518-1539`); 690 s engine stop (`server.nim:1383-1389`); frame limiter sleeps ≤ 2 ms slices (`server.nim:958-988`); all variants `wallClockBudgetSeconds: 690 ≤ 720`, asserted `tests/test_manifest.nim`. Worst case 612 s priced in `tests/test_engine.nim`. |
| 6 num_agents + seat invariants | PASS | `num_agents: 4` in all 4 variants and `certification.game_config`; `len(certification.players) == 4 == len(game_config.players)` (verified from the manifest directly). `tools/ci/docker_smoke.sh:106-149` enforces all four invariants with `SEAT-COUNT FAIL:` prefixes plus `SMOKE_SEATS` (`:54`, default 4 = the `<SEATS>` substitution). Grep of the head run's docker-smoke log (job 98192033429): **0** occurrences of `SEAT-COUNT FAIL`. |
| 7 Scripted baseline full episodes | PASS | `tests/test_control.nim:105-137` asserts `reason == "complete"` + legal masks (see B1); bounded-orders block (500 worlds × 2 baselines × 4 seats); tuned, not guessed: `tools/tune_baselines.nim` + `ci.yml` step "Re-check the scripted baseline's tuned parameters", green at head. |
| 8 LLM reply handling | PASS | `directives.nim:102-141 extractJsonObject` (prose/fence/bare-object tolerant, `ac843a4` added the bare order at `:189-295`); retry exactly once (`decide.nim:427-428 attempt < 2`, asserted exactly-8-requests in `tests/test_engine.nim:153` via `fake_bedrock.py` garbage mode, `de117b4`); fallback → phalanx with a recorded `fallback` record and the phase-60 grep phrase "falling back" (`decide.nim:508-523`), counted into `results.fallbackTurns`. |
| 9 Rune-safe truncation | PASS | Single primitive `truncateRunes` (`directives.nim:61-68`, `runeLen`/`runeSubStr`) on every replay-bound string (note 160, say 10, id 16, policy 48, detail 200, record 900); `tests/test_directives.nim:128-173` feeds a 4-byte emoji at the cap and asserts `validateUtf8() < 0` + JSON round-trip; `tests/test_replay.nim` runs the end-to-end fixture with non-ASCII strings through `tools/replay_summary.py` strict-UTF-8. |
| 10 Manifest validates | PASS | `game.docs.readme = {"type":"text","value":…}` (3 465 chars) + 3 pages each `{id,title,content:{type:"text",value:…}}` (verified by parsing the manifest); `game.protocols` carries both `player` and `global` in object form. |
| 11 Legible at 360 px | PASS | `client/replay_broadcast.html:3975-3980` `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`; labels hidden under `.tiny` (`:4014-4018`, threshold `boardW <= 620` — the starter's own sub-640 breakpoint); text-fixture measures the 360 px embed size, `never_inside: 0`. |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build the Coworld manifest (:153) → Certify locally (:167) → Upload the policies (:212) → Upload the Coworld (:310) → Put the Coworld secret (:348); ci.yml's smoke builds its image in-job before running. Three workflows present; `docker_smoke.sh` 100755; `policies.json` = 2×`PLAYER_PROMPT` + 2×`PLAYER_SCRIPTED`, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the placeholder gate (`<slug>|<IMAGE>|<SEATS>` over the five files) exits 0 — I ran it. |
| 13 Viewer executes | PASS | `wasm-viewer` `needs: docker-smoke`, downloads `smoke-replay`; step **"Load the bundle in a real browser"** ran and passed at head (job 98192679312, no `continue-on-error` anywhere in the workflows — grep = 0). Artifact: `loaded: true` in 1 295 ms, `data_replay_loaded: "true"`, `data_replay_error: null`, `bridge: ["ready"]`, 15 s soak advancing (tick 1→315→363), three differing scrub readouts. Bootstrap and link flags are one starter's matched pair: `config.nims` non-MODULARIZE (no `MODULARIZE`/`EXPORT_NAME`, `EXPORTED_FUNCTIONS=_kaz_*`) + `static_replay_worker.js:188 Module.onRuntimeInitialized` — identical shape to `/workspace/starters/coworld-ctf` (starter worker :188 same line). Both markers set from the shell's own paths (`static_replay.js:161` loaded-branch, `:19-20 showFailure`). |
| 14 Chrome is the starter's | PASS | `client/chrome_common.js` **byte-identical** to the starter's (diff empty — I ran it). `client/replay_broadcast.html` 4 663 lines vs starter 4 660, banner at :3940; CSS above the banner diffs only in the note-listed removals (§4b viewpanel, `.steal/.return/.capture` beat rules, `.ec-heart`/badge glyphs, the `?viewpanel=0` opt-out) — I diffed the full `<style>` block, 5 hunks, all removals. `relayout()` sets `--band`/`--topband`/`--hudscale` on `:root` (`:3907-3913`); no `position: fixed` anywhere (grep = 0); overlays live inside the board inset (`:112 inset: var(--topband) 0 var(--band) 0`); `#endcard { bottom: var(--band, 0px) }` (`:911`), shown via `#endcard.on` (`:922`), every seek removes `.on` (`:1900`); beats are labelled `<button>`s built by `kazBeat` (`:4267`) with CSS for exactly the five emitted kinds (`:4167-4187`); `#viewpanel`/`#minimap`/`#zoombar` removed — markup, CSS and wiring (the surviving `.fpv-map` is the kept first-person PIP inset, not the view panel). `broadcast_core.js` differs in the `KAZ_WIRE` identifier plus one comment path — pinned by `tests/test_viewer.nim`. |
| 15 Every drawn string fits | PASS | `viewer_smoke.mjs` reports `canvas_text` in `viewer-smoke.json`; ci.yml's smoke step carries `--strict-text-bounds` (fixed arena) — main-replay `total: 0` is correctly treated as evidence of nothing, and the required worst-case renderer fixture exists: `replay-viewer/text_fixture.html` + its own `text-fixture` ci.yml step, `canvas_text {total: 204, never_inside: 0, ellipsized: 0}` at head, asserting its own strings full-length. Sprite-side reserved band: `shoutBubbleMaxHeight`/`shoutBubbleRectFor` asserted by `tests/test_shouts.nim` from the cap, not by eye. Sentences wrap, never ellipsise (`ed7c6bc`). |
| Rider: one parallel batch | PASS | `decide.nim:439-459` builds one `RequestBatch` for all open seats and issues one `makeRequests`; `tests/test_engine.nim:61-130` measures ≥3-of-4 overlapping in-flight windows against a real localhost fake with a 150 ms delay. No sequential path exists. |

## Non-blocking observations

- `client/broadcast_core.js` differs from the starter in **two** lines (the `KAZ_WIRE` identifier
  and one comment path `src/ctf/sim.nim`→`src/kaz/sim.nim`) where the design note says "one
  identifier". Pinned by the rename-normalised digest in `tests/test_viewer.nim`; cosmetic.
- The deleted-not-disabled pin is still open (reviewer's N21): `src/kaz/paint.nim` and the
  config-gated classic mechanics remain in-tree, unreachable under every shipped variant, now
  honestly recorded in `AGENTS.md` as work still to do. No checklist item is falsified.
- The design's `hit {by, zombie, dmg, hpLeft}` broadcast event and `gate_px` on `kill` remain
  unemitted (fixer's own NOTED list). Feed copy is correct at head; note-level residue only.

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, `6488886` | `tests/test_control.nim:105-137` present at head, asserts `complete` + legal masks; CI green | yes |
| B2 | fixed, `01cc35a`+`ed7c6bc` | `tests/test_shouts.nim` (rectFor callers real, `:61-128`), `text_fixture.html` (full-length assertion `:394`), ci.yml `text-fixture` job green, artifact `total: 204, never_inside: 0`; `.feed-row` wrap fix in the game block | yes |
| N8 | fixed, `2b3c2c4` | `horde.nim:213-216` raises `SimGuardError` below `MinSpawnRows` at install | yes |
| N12 | fixed, `ac843a4` | `directives.nim:189` bare-order path; `tests/test_directives.nim:55,64` | yes |
| N14 | fixed, `de117b4` | `tests/test_engine.nim:153` asserts exactly 8 requests (4 seats × 2 attempts) | yes |
| N15 | fixed, `061d153` | `#kaz-pressure` is a scorebug grid row; `test_viewer` pins fix + negation of the defect | yes |
| N17 | fixed, `69de111` | `heroLastKill` appended at end of `SimServer` (`sim_types.nim:2222`), set in `creditZombieKill` (`sim.nim:3491-3494`); hash gate green | yes |
| N9 | DISPUTED, code stands | sleep bounded ≤ 9 s, budget arithmetic intact, item 5 satisfied; note prose wrong, recorded in AGENTS.md | yes — reviewer's reading of the note is right, but no checklist item falls |
| N2/N3/N4/N13/N20 | note stale, doc'd | AGENTS.md divergence table present at head (`d1ea75d`), each row carries file:line + reason | yes |
| N21 | NEEDS-DESIGN, doc'd | `paint.nim` present, `hordeLoadout` gate at `sim.nim:171`, AGENTS.md states removal is pending | yes |
| N25 | judge's call | ruled non-blocking (see above) | — |
| "no test weakened" | claimed | confirmed from `git log -p -- tests/`: the two moved assertions each pinned the defect under fix and were replaced by stricter ones | yes |

## Count

Zero blocking findings stand at `d1ea75d`. Both of the review's blocking findings were real at
`00cc62a` and are fixed and CI-evidenced at head; my independent checklist pass found nothing the
review missed that rises to blocking.

BLOCKING: 0
