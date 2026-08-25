blocking: 0

# r1 verdict — cogame-territory

Head: `62a31b0a52c16042830ef3324f8df16106a2000e` (branch `main`)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: **yes** (`/tmp/judge-notes-territory-r1.md`, written before opening `r1-review.md` and `r1-fixes.md`; the fixes file was opened last, only to audit its claims against the tree).
CI evidence at head: run **32846969302** (`gh run view --json headSha,conclusion` → `headSha: 62a31b0…`, `conclusion: success`; jobs `test` ✓ 3m41s, `docker-smoke` ✓ 50s, `wasm-viewer` ✓ 1m13s).

The review was written against `07f0ebc`; nine commits landed since. Findings that were true then and are fixed now are marked **FIXED**, per the brief — a fix verified in the tree, not taken on the fixer's word. Nothing stands.

## Standing blocking findings

None.

## Reviewer findings — refuted / fixed / adjudicated

### O1 (item 2, re-derivation) → FIXED at head, fix verified real
True at `07f0ebc` (viewer drew recorded snapshots; engine absent from replay-page chunks; no test). Fixed by `8c796f9` + `62a31b0`:
- `src/game/rederive.ts:104-150` replays recorded `actPrompt` events through the pure engine (`newGame`/`stepTurn`/`rejectionReason`) and compares canonical snapshots frame by frame (`canon(got) !== canon(want)` → first divergence reported).
- The viewer **adopts** it: `src/client/App.tsx:99-115` (`adoptRederivation` replaces `store.snapshots` with the re-derivation), invoked on both the fetched path (`:181`) and the injected path (`:156-158`).
- Tests: `src/game/replay.test.ts:173-206` asserts `verified === MAX_TURNS + 1` and adoption-length equality **on a real episode's bytes** (real host, nine real player processes); `src/client/client.test.tsx:242-269` mounts the page with every recorded snapshot tampered (`banked: 999`) and asserts the sim's numbers are drawn, `data-replay-rederived="mismatch"`/`"true"`.
- CI gate: ci.yml step "Assert the REPLAY PAGE carries the sim it re-derives with" walks `index.html`'s own module graph for the engine-only sentinel string `"rubble is never claimable again"`; head run log: `index.html reaches 4 chunk(s) … re-derivation OK`. Not a test-weakening: all additions.

### O2 (item 8, transport failure rethrown) → FIXED at head
True at `07f0ebc` (`if (!isCredentialsUnavailable(err)) throw err`). Fixed by `308e358`: `packages/llm/src/robust-decide.ts:81-88` now records the attempt and `continue`s the loop — retried once (maxAttempts=2 from `src/game/player.ts:38`), then `return opts.baseline()` (`:105`) = the scripted move via `fallbackMove` (`player.ts:41-44`, `fallback: true` → `src/game/game.ts:152-158` → `results.fallbacks`). Credentials path unchanged (terminal, immediate baseline, `:77-80`). New `packages/llm/tests/robust-decide.test.ts` covers throttle→success, throttle→throttle→baseline-without-throw, no-creds→1 call, parse-reject ladder. Nothing throws out of `robustDecide` anymore.

### O3 (item 9, transcript uncapped / capped note dead) → FIXED at head
True at `07f0ebc`. Fixed by `7c75813`, all three leaks:
1. `src/shared/engine/orders.ts:71,75` — `SubmissionSchema` transforms now drop lines past `MAX_LINES` and `capText` both `text` (200) and `note` (120) at the parse boundary (also closes A17).
2. `packages/coworld/src/remote-pilot.ts:157-170` — the accepted attempt records the **validated** (capped) decision.
3. `packages/core/src/runner.ts:31-47,553,559,753,827` — `capAttempt` rune-caps prompt/response/error (16 000/4 000/500) at the single choke point before every `actPrompt` frame, including the runner's own timeout/error pushes (item 9's "prompts, captured errors").
Tests: `packages/core/tests/runner-transcript.test.ts` (caps are code-point caps, no lone surrogate, fatal-TextDecoder round trip); `src/shared/engine/text.test.ts` additions (360-rune CJK+emoji note → 120 runes; short/absent note untouched). Observable: smoke replay shrank 3 593 980 B → 3 579 349 B between runs.

### O4 (item 3, fonts.googleapis.com) → FIXED at head
True at `07f0ebc`. Fixed by `a30ab47`: the `@import` is gone; both families self-hosted as committed woff2 (`src/client/fonts/*.woff2`, inlined as data URIs by `assetsInlineLimit`). `src/client/no-external-origin.test.ts` fails on any absolute http(s) URL in the two stylesheets and three shells, and asserts the wOF2 magic bytes. The viewer now contacts nothing but S3 (`packages/ui/src/replay.ts` fetch of `?replay=` is the only request; live-socket effect skipped in replay mode).

### O5 (item 7, no grid harness) → FIXED at head; the retune ADJUDICATED as satisfying item 7
True at `07f0ebc` (constants hard-coded, no harness artifact). Fixed by `640a207`: `src/game/tune.ts` sweeps the whole meaningful grid (`maxClaims 1..8` — the `MAX_ORDERS_PER_TURN` bound; `minYield 1..3` — the yield range) over five seeded full 18-turn nine-seat episodes of the certification mix; committed table `docs/baseline-sweep.md` via `scripts/sweep-baselines.ts`; `src/game/tune.test.ts` re-runs the sweep in CI and asserts the shipped constants are the harness's selection (it ran — the test job took 3m41s and reports 199/199 passed, 0 skipped).

**Adjudication of the retune (raider `maxClaims 3→4`, `minYield 2→3`, deviating from the design note's literal numbers):** SATISFIES item 7.
- Item 7's second sentence — "tuned with a grid harness, not guessed" — is exactly what changed; the note's literal numbers *were* the guess (old raider point measured 12.3 % under the grid's best, outside any tolerance).
- The sweep has a fixed point by construction: the reference field is pinned to the note's pre-tuning numbers (`tune.ts:32-33`), so the note's numbers survive as the declared baseline of comparison rather than being erased.
- Legality is unaffected: the tuned raider emits ≤ 5 orders, inside `MAX_ORDERS_PER_TURN = 8`, asserted at `tune.test.ts:68-73`; `scripted.test.ts:56-84` still proves 200+ seeded views legal, affordable and accepted by `resolve()`.
- The one touched assertion (`scripted.test.ts:130`, `yield >= 2` → `yield >= RAIDER_PARAMS.minYield`) re-points a literal at the constant it stood for and keeps the raze assertion — not a loosening. (Also: the fixer's "NOTED" worry that `tile.yield` is base yield is wrong — `src/game/redact.ts:112` sets the observation's `yield: effYield(t)`, so the raider's filter already reads effective yield, as the note specifies.)

### O6 (item 15 final bullet, fixture doesn't assert its own strings) → FIXED at head
True at `07f0ebc`. Fixed by `ea0e71d`: `src/client/fixture/main.tsx:93-118` `checkStrings()` runs inside every `__territoryFixtureCheck()` call — asserts `fullCapLine()` is exactly `MAX_SAY_LEN` runes, ≥ SEATS lines emitted, every mounted line still full-length **and present whole in the rendered DOM**, and enough `.cg-msg-body` rows laid out. `src/client/fixture/selfcheck.test.tsx` runs it in jsdom. Head run: renderer fixture green at 360/720/1280 (`59 rows checked, 0 findings` ×3, `{"ok":true}`).

### O7 (item 3 literal, `"build/static-replay-viewer"` vs `"static-replay-viewer"`) → REFUTED (no violation)
Verified myself: the basename is exactly `static-replay-viewer`; the **live, certified base** declares the identical full string (`/tmp/coworld-cogherence/coworld/coworld_manifest_template.json` → `replay_viewer.bundle: "build/static-replay-viewer"`); `scripts/build-static-replay-viewer.sh` refuses any other output path; the design note declares this exact form. Dropping `build/` would point the manifest at a directory the hook never writes. Item 3's substance — bundle declared, `tools/build_replay_viewer.sh` present and mode 100755 (`git ls-files -s` → `100755`), wired as the build hook, viewer contacts nothing but S3 (post-O4), no `/client/replay` string in the manifest (grep count 0) — all holds. The container's `/client/replay` route is the inherited platform probe surface, not a declared pod viewer; the release workflow's `LIVENESS_MARKER` gate pins "Replay liveness: skipped (static replay bundle declared".

### O8 (item 10 literal, readme `"uri"` vs `"text"`) → REFUTED (no violation)
Verified myself: the live base's certified manifest ships `docs.readme.type: "uri"` for the same field (checked in the fresh `--depth 1` clone), the lineage's manifest schema accepts `text | uri` (`packages/coworld/src/manifest.ts`), and the design note declares `uri` explicitly. The checklist's `"text"` is the other lineage's shape; "Manifest validates" is the item, and this form is the one this platform demonstrably validates. Everything else in item 10 is literal: three `pages` each `{id, title, content:{type:"text",value}}`, `protocols` carries **both** `player` and `global` (parsed the committed JSON myself).

### O9 (item 14 mechanics, `--band`/`--hudscale`/`#endcard.on`; `<base>` script not byte-for-byte) → REFUTED as a violation; one non-blocking note stands
Adjudicated per the brief's lineage mapping, verified independently:
- **Chrome provenance:** I ran `diff -rq /tmp/coworld-cogherence/packages/ui/src /tmp/cogame-territory/packages/ui/src` myself → **byte-identical**, and `src/client/chrome-manifest.test.ts` pins every SHA-256 with `base: "Metta-AI/coworld-cogherence"`. The game block is appended (`src/client/ui/{ScoreBug,WarLedger,BoardPanel}.tsx` into `.cg-stage`), not a rewrite.
- **Transport rules, structurally:** `.app` is `position: fixed; inset: 0;` flex-column with exactly three children (`src/client/styles.css:98-105`, App.tsx structure), so the transport band cannot be overlaid — the guarantee `--band` exists to provide, provided by construction. The endcard is `position: absolute` **inside `.cg-stage`** and renders only on the synthetic FINAL slot (`App.tsx:349,241`), so every seek dismisses it — asserted at `client.test.tsx:173-192`. Rail beats are real `<button>`s (`packages/ui/src/GameScrubberBar.tsx`) and every emitted kind (`elim|raze|smear|quiet`, `src/client/cg/derive.ts`) has a CSS rule (`styles.css:927-948`).
- **Zoom:** the 169-hex board is larger than the 360 px frame → `HexBoard` wheel-zoom/drag-pan/dblclick-fit kept; no `#viewpanel`/minimap exists in this lineage to remove.
- The `index.html:21` `<base>`-recovery regex change (`/cog/[^/]+` → `/seat/\d+`, plus title/comment) is a minimal functional adaptation to Territory's own routes; reverting it would break `<base>` recovery on `/seat/N`. It does contradict the note's "byte-for-byte" phrasing — recorded below as a non-blocking observation, not a chrome violation (the declared chrome, `packages/ui/src/**`, is untouched).

### A1, A10, A17 (advisory) → fixes verified real
`c044b05` (`MAX_ATTEMPTS = 2`, `remote-pilot.ts:31`), `2749fc3` (`App.tsx:186-191`: zero-snapshot decode sets `data-replay-error` + loadError), A17 inside `7c75813` (schema caps). None was blocking; all three now match the note.

### A2–A9, A11–A16 (advisory) → concur: none falsifies a checklist item
Spot-checked the ones nearest a checklist item: A8 (artifact IO timeout) — item 5 enumerates "LLM call, seat reply, round barrier", all explicitly bounded (`CONNECT_DEADLINE_MS`/`ACT_TIMEOUT_MS`/pace floor/`EPISODE_DEADLINE_MS`/`shutdownGraceMs`, `src/coworld/server.ts:8-17,67-73`; batch `Promise.all` of individually guarded decides, `runner.ts:492,540-561`); undici defaults bound the rest. A9 — `autoAdvance` always enabled in production (`server.ts:70`). A16 — worst case is one extra timed-out (bounded) turn, not a hang; untestable here, inherited. A2 — `deadline` settle still writes results + replay (`settleEarly` → `buildResults`; `results.ts:41` `reason: engine.settled ?? "deadline"`), viewer degrades via `status.ended`; no item requires an endcard frame on that path. A11 — item 1's method is this repo's history, which is clean; the fork-boundary delta is not a loosening "during this run". A12/A13 — the tests are the stricter reading in both cases.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 32846969302 `success` at headSha 62a31b0; test job: `Test Files 33 passed (33)`, `Tests 199 passed (199)`, 0 skipped/todo. `git log -p -- '*test*'` over the whole history (first commit 2026-08-25): only 44 removed lines, all imports/relocations; the single assertion edit (`scripted.test.ts:130`) re-points a literal at the tuned constant and keeps the assertion. No skip/xfail/deleted test file. |
| 2 Replay re-derivation | PASS | `src/game/rederive.ts:116-147` (frame-by-frame canon compare); viewer adopts it `App.tsx:99-115,156-158,181`; tests `replay.test.ts:173-206` (real bytes, `verified === 19`), `client.test.tsx:242-269` (tamper test); CI module-graph sentinel green ("re-derivation OK" in head run log). |
| 3 Static viewer | PASS | manifest `game.replay_viewer.bundle = "build/static-replay-viewer"` (basename exact; identical to live base's); `tools/build_replay_viewer.sh` mode 100755; no `/client/replay` in manifest; no external origin (no-external-origin.test.ts; fonts self-hosted a30ab47); release gate pins the "Replay liveness: skipped (static replay bundle declared" marker. |
| 4 Both name spaces | PASS | `src/game/game.ts:115-121` ignores `seatNames`; `redact.ts` aliases only; NO ALIAS LEAK test `client.test.tsx:202-224`; viewer maps alias→policy — head run `viewer-smoke` scorebug: `"1 Verdant Cog C 12 +6/turn …"` (alias + injected name, in a real browser). |
| 5 Degrade-never-hang, ≤ 720 s | PASS | bounds: connect 45 s / act 20 s / pace 22 s floor / episode 660 s / shutdown 20 s (`server.ts:8-17,67-73`, `constants.ts`); guarded batch `runner.ts:492,540-561`; deadline guard `runner.ts:512-520` (`spent + 2·20 000 > 660 000` → settle, artifacts written); arithmetic `45 + 18×22 + 20 ≈ 461 s` ≤ 720 s; docker-smoke episode (paceMs 0) ran in ~24 s incl. linger. |
| 6 num_agents | PASS | parsed committed manifest: all 3 variants + certification `num_agents: 9`, `players` 9/9 both places; `docker_smoke.sh:110-151` four `SEAT-COUNT FAIL:` invariants + `SMOKE_SEATS=9` cross-check; head docker-smoke log: `smoke OK: seats=9 … reason=complete`, **zero** `SEAT-COUNT FAIL` occurrences. |
| 7 Scripted baseline, tuned | PASS | `game.test.ts:37-52` full 18-turn all-scripted episode ends `"complete"`; `scripted.test.ts:56-84` 200+ seeded views legal/affordable/accepted; grid harness `tune.ts` + committed `docs/baseline-sweep.md` + `tune.test.ts` asserting shipped == harness selection. Raider retune adjudicated as satisfying the item (above). |
| 8 LLM reply handling | PASS | `extractJson` tolerant parse (`robust-decide.ts:22-38` via review trace; tool-forced primary path); retry once on parse **and** transport (`:81-102`, maxAttempts 2), then scripted move (`player.ts:41-44,74`); fallback recorded (`game.ts:152-158` → `results.fallbacks`, `actPrompt.usedFallback`); host side `RemotePlayerPilot MAX_ATTEMPTS = 2`. |
| 9 Rune-safe truncation | PASS | `text.ts:14-27` code-point slicing; applied at schema (`orders.ts:71,75`), engine (`resolve.ts:141-142`), and transcript choke point (`runner.ts:44-47 capAttempt`); `text.test.ts` 300-emoji at the cap + fatal TextDecoder round trip; `runner-transcript.test.ts` for prompt/response/error. |
| 10 Manifest validates | PASS | `docs.readme` type `uri` = the live base's certified form (verified in the clone) and the note's declaration; 3 pages `{id,title,content:{type:"text",value}}`; `protocols.player` and `.global` both present (parsed the JSON). Bounded arrays throughout (`coworld.test.ts` recursive walk; tokens/players/scores/fallbacks/razes 9/9). |
| 11 Legible at 360 px | PASS | `styles.css:291-293` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; `@media (max-width: 640px)` block at `:1157` hides /tick + policy labels; renderer fixture green at 360 px (59 rows, 0 findings). |
| 12 Release order & scaffold | PASS | coworld-release.yml: Build manifest (153) → Certify (167) → Upload policies (206) → Upload coworld (304) → Put secret (342); smoke depends on same-run build; 3 workflows present; both scripts 100755; policies.json = 2 `PLAYER_PROMPT` champions (+`USE_BEDROCK`, pinned haiku 4.5) + 2 scripted fillers, champion #2 carries `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`; placeholder grep over the five files returns nothing (gate exits 0). |
| 13 Viewer executes | PASS | `wasm-viewer` green at head **including** "Load the bundle in a real browser" (no `continue-on-error`, `needs: docker-smoke`), against the replay docker-smoke produced: `{"loaded":true,"ms":583,…}`, clock differs across scrub readouts (`Turn 4 / 11 / 13`), `soak: 15s of playback kept advancing`. Both markers from the shell's own paths (`App.tsx:75,84`). No emscripten in this lineage; the module-graph sentinel + browser execution cover the bootstrap class. |
| 14 Chrome is the starter's | PASS | `packages/ui/src` **byte-identical** to a fresh cogherence clone (my own `diff -rq`); SHA-256 manifest test pins it; game block appended in `.cg-stage`; endcard FINAL-slot-only, seek-dismissed (tested); beats are `<button>`s with CSS per kind; zoom kept, board pannable, no minimap in lineage. |
| 15 Drawn strings fit | PASS | SVG/DOM text → `canvas_text total: 0` declared meaningless (ci.yml header); `--strict-text-bounds` dropped for a pannable board per the checklist's own rule; DOM renderer fixture (real ScoreBug/WarLedger/Channels, full-cap CJK+emoji on every seat, real played scenario) gated as its own ci.yml step at 360/720/1280, green at head, and self-asserts its strings are full-length in the DOM (ea0e71d). |
| Simultaneous batch | PASS | `game.ts` `simultaneous: true` → `runner.ts:492` one `Promise.all` per turn over the identical pre-batch state; `runner-batch.test.ts` barrier proves genuine concurrency. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| O1 | fixed, 8c796f9+62a31b0 | rederive.ts + adoption + tamper test + CI sentinel all present and green | yes |
| O2 | fixed, 308e358 | continue-not-throw at robust-decide.ts:81-88; 4 new tests | yes |
| O3 | fixed, 7c75813 | schema caps, validated-response recording, capAttempt at all 4 push sites; new transcript test | yes |
| O4 | fixed, a30ab47 | @import gone, woff2 committed, origin test present | yes |
| O5 | fixed, constants changed by sweep, 640a207 | harness + committed table + CI assertion; retune adjudicated OK | yes |
| O6 | fixed, ea0e71d | checkStrings() inside checkDom + selfcheck test | yes |
| O7/O8/O9 | deferred to judge | adjudicated: no violation (above) | yes |
| A1/A10/A17 | fixed | verified at remote-pilot.ts:31, App.tsx:186-191, orders.ts:71,75 | yes |
| "no test weakened" | claimed | history audit clean; the one edit re-points a literal at its constant | yes |
| NOTED raider `tile.yield` vs effYield | fixer flags a possible drift | **wrong** — `redact.ts:112` sets obs `yield: effYield(t)`; the raider already filters on effective yield | corrected |

## Non-blocking observations (mine)

- `index.html`'s `<base>`-recovery script is minimally adapted (route regex `/cog/[^/]+` → `/seat/\d+`, title, comment) while the design note calls it "byte-for-byte". The adaptation is functionally required by Territory's routes and the declared chrome (`packages/ui/src/**`) is untouched; the note's phrasing should be softened next time it is edited.
- Viewer-smoke scrub readouts land on Turn 4/11/13 rather than the timeline's ends — the click-fraction → rail-cell mapping is coarse. The gate (clock text differing) holds; worth a look if scrub UX ever matters.
- The design note's `poolStart ≈ 149` analytic figure sits ~1.4σ under the observed seed-7 board (166); prose only (`deadweight.md`), bounded by `board.test.ts`'s (130, 170) band.
- A2 (no `endcard` frame on the `deadline` settle) and A16 (stale pilot timer under `paceMs: 0`) remain real but bounded and off-checklist; reasonable residue for phase 60 awareness.

BLOCKING: 0
