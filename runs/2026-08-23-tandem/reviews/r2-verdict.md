blocking: 0

# r2 verdict — tandem
Head: `ac662b2af8e3802b12dfc5c3e67d19feed3dc8c5` (origin/main, fresh clone)   Checklist: agent brief §ACCEPTANCE CHECKLIST (items 1–14 + simultaneous-batch rule)   Independent read written before reading fixes: yes

Reading order kept: checklist → design note → the repo at `ac662b2` (own notes formed, including
an executed page-drive in a DOM harness) → `r2-review.md` → `r2-fixes.md` (consulted last, only to
cross-check). The round-2 review was written against `668b5f5`; every finding is re-judged here at
`ac662b2`, the current head, which carries the seven r2 fix commits (`59c52f6..ac662b2`).

## Standing blocking findings

None. The review's single blocking finding (F1) is fixed at head, no r2 fix regressed an r1 fix,
and my own checklist pass found nothing new that falsifies a checklist item.

## Refuted / resolved

### B1 (reviewer's F1) — "`markBeat` shadowed by the inherited alias; every scrubber beat is an unlabeled `<div>`" → RESOLVED AT HEAD (does not stand)
- The finding was true at `668b5f5` (the review's three-way reproduction is sound). At head the
  game block's builder is renamed: `client/replay_broadcast.html:2167`
  `function markTandemBeat(tick, kind, team, label)`, with all seven call sites retargeted
  (`:2224` in `tandemIngestBeats`; `:2233,2237,2240,2244,2248,2251` in `applyEvent`). The alias
  `var markBeat = C.markBeat` (`:1477`) still exists but is never called by the game block, and a
  ten-line comment at `:2156-2163` records why the name is not `markBeat`.
- **Executed at head (this sandbox has node, no nim/chromium):** I spliced
  `client/replay_broadcast.html` with the real `chrome_common.js` and `static_replay.js`, ran it
  under the repo's own DOM-stub harness (`tools/ci/viewer_shell_check.cjs`, boots green on both
  pages), then drove frames through the Worker's `onmessage`. A frame with 6 beats produced
  **5 markers, all `<button type="button">`** (the `dmg:5` impact correctly filtered below the
  ≥ 20 floor), each with an `aria-label` ("Doorway 1 cleared — 0:05", "DROP by Cobalt — 0:11", …),
  a `title`, and an `onclick`; clicking the tick-120 doorway posted `{"type":"command","text":"s:120"}`
  to the worker — the marker's own tick, not a pointer fraction. Zero div markers (chrome_common's
  builder only fires for `steal`/`return`/`capture`/`kill`, which tandem never emits —
  `chrome_common.js:584-585`).
- **Scope re-check, both pages:** I ported `tests/test_viewer.nim`'s `noAliasIsShadowed` parse to
  node and ran it against head and against the pre-fix trees:
  `HEAD broadcast: aliases 43, declared 77, SHADOWED []`; `HEAD league: aliases 38, declared 51,
  SHADOWED []`; `59c52f6~1 broadcast: SHADOWED ["markBeat"]`. No alias-shadowing remains in either
  HTML page, and the new test is non-vacuous — it fails on the pre-fix page.
- CI at head executed the real page in real chromium: run **32674800419**, `wasm-viewer` →
  "Load the bundle in a real browser" → `{"loaded":true,"ms":2885,…}`, soak advancing
  `1 → 241 → 289 / 948`.

### Reviewer's F2 (non-blocking) — "`delivered` beat unreachable" → FIXED at head
- `src/tandem/broadcast.nim:96-98`: the beat now fires on the delivery transition
  (`if sim.delivered() and not tracker.delivered`), the same delta shape as `wrecked`, ahead of
  the same tick's `gameover` (phase diff at `:100-113`). `BroadcastTracker.delivered` added at
  `:38`/`:58`.
- **Broadcast-only, gameHash untouched:** derived events are never mixed into `gameHash`
  (design §The game step 9; `sim_state.gameHash` mixes sim fields only). Confirmed:
  `git log --oneline -- tests/data/golden_hashes.json` shows only the initial commit `68e39b0` —
  the goldens never moved — and run 32674800419's "Native/wasm determinism gate" step is
  `success` ("ok: loaded tandem-smoke.replay, advanced 240 frames").
- New test `tests/test_replay.nim` `deliveryIsABeat` is real and non-vacuous: it runs a full
  porter×porter episode through the real record path, asserts **exactly one** `delivered` event,
  at the delivery tick (±1 frame), **before** that frame's `gameover`, with
  `event["ticks"] == sim.deliveryTick`. On pre-fix `broadcast.nim` the `delivereds == 1` assert
  fails with 0. My harness run at head rendered the `delivered` button from the beats list.

### Reviewer's F3 (non-blocking) — "league_replayer.html is the CTF shell, renames only" → FIXED at head
- `20c4b28` retargets the readouts while keeping the starter's shell (wall homography
  `buildWalls`/`proj`, `layout()`, the postMessage bridge, transport drive, standings footer —
  all verified present at head, `client/league_replayer.html:443-539, 858-885`). CTF furniture is
  gone (no `flagicon`, `lives-num`, `setLivePips`, `killMarkerTeam`, kill/steal beats); tandem's
  is in place: strain gauges (`updateStrain`, `:606-611`), Name/Strain/Blame roster (`:697-744`),
  tandem beat vocabulary (`:806-811`), `ingestTandemBeats` (`:831-839`), verdict-as-ending
  (`:847-856`), and a `.beat-marker.<kind>` CSS rule per kind (`:247-254`).
- It is live on both delivery paths, as the brief flagged: served at runtime
  (`server.nim:90 LeagueReplayerPath = "/client/league"`, `EmbeddedLeagueReplayerHtml` at `:103`)
  and shipped in the static bundle as `league.html` (`Dockerfile.replay-viewer:46`, asserted at
  `:57-65`; visible in run 32674800419's build log). Both pages boot in the shell-check harness.
  New test `leagueShellReadsTandemsStream` pins both directions.

### Reviewer's F4 (non-blocking) — "verdict cap permanently inert" → FIXED at head
- The game block now drives `#scrub-win`/`#win-chip` with the **ending** vocabulary
  (`renderVerdict`, `client/replay_broadcast.html:2310-2320`; labels `:2302-2309`; one `--tc` tint
  per `endRule`, `:1289-1294`), called every frame from `renderScorebug` (`:2332`). chrome_common's
  `setVerdict` stays inert by construction (`over.winner` is `""`, `over.draw` false —
  `broadcast.nim:361-362`; `chrome_common.js:598-599` returns on empty class), so nothing fights.
- **Executed:** a game-over frame yields `#scrub-win.className == "scrub-win show delivered"`,
  chip text `DELIVERED`, endcard headline "DELIVERED in 0:38"; a seek-away frame clears the cap to
  `"scrub-win"` and drops `#endcard.on`. The `.show` class matches the inherited CSS rule
  (`.scrub-win.show`, `:640`). Semantics (ending, not an invented winner) match the cooperative
  design; test `verdictCapCarriesTheEnding` pins all six rules.

### Reviewer's F5 (non-blocking) — "the 14(d) guard cannot fail on F1" → FIXED at head
- `tests/test_viewer.nim:134-191 noAliasIsShadowed` is a static scope-duplication check over both
  HTML pages: every `var x = C.x` alias vs every top-level `function`/`var` declaration of the same
  IIFE, with vacuity floors (≥ 20 aliases, ≥ 20 declarations). Verified non-vacuous by execution
  (fails on `59c52f6~1` naming `markBeat`; passes at head — see B1 above). It would have caught
  the r2-F1 bug pre-fix.

### Reviewer's F6 (non-blocking) — "starter's `.beat-marker` height/transform still win" → FIXED at head
- The game block's rule (`client/replay_broadcast.html:1269-1274`) now overrides every conflicting
  property of the inherited rule at `:603-610`: `height: auto` (so `top: 0; bottom: 0` spans the
  track), `transform: none` (centring via `margin-left: calc(-1.5 * var(--u))`), `width: 3u`,
  `z-index: 4`. Equal specificity, later in the cascade → wins per property. The inherited rule
  above the banner is untouched (checklist 14's requirement).

### Reviewer's F7 (non-blocking) — four comment/value drifts → ALL FIXED at `ac662b2`
- `baselines.nim:411` mule note now "straight at the goal, never yielding" (matches
  `MuleEffort = 140`); `server.nim:476-477` comment now says 660 s; `SimServer.damageAtTurnStart`
  deleted from `sim_types.nim` (was never read/written/hashed — goldens unmoved);
  `tandem_player.nim:120-122` now logs the clipped rune count and the 4000-rune cap. All four
  hunks read directly from `git show ac662b2`.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | PASS | `gh run list`: run **32674800419**, `conclusion success`, `headSha ac662b2…`; jobs `test`/`docker-smoke`/`wasm-viewer` all success, no `continue-on-error` in any workflow. Whole-history `git log -p -- tests/` read: every deletion is a strengthen or an exact re-application (the r1 fix series appears twice — a linear reapply; `git diff 0d5fdc6 3a35bb5` is **empty**, so nothing was net-removed; current `tests/test_engine.nim:173-236` still carries both the no-transport and the disconnect-revive tests). One judgement call: `6ce3d67` widened `test_routes.nim`'s `/healthz` **wait bound** 60 s → 300 s after a real debug-build CI failure at `0d5fdc6` (run 32670826674, failure) — a setup-liveness bound, not an assertion tolerance; the assertions on route content/behaviour are unchanged and the test still fails a server that never listens. No `skip`/`xfail`/removed file anywhere (grep clean). |
| 2 Replay re-derivation | PASS | `tests/test_replay.nim:66-89 replayReproducesEveryHash` (full episode, re-sim from config+orders, `hashMismatchTick == -1`, state equality); viewer derives from the same re-derivation: `replay-viewer/tandem_replay.nim` imports the same `sim`/`control`, per-tick `checkReplayHash`; run 32674800419 "Native/wasm determinism gate" success. |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `replay_viewer == {"bundle":"static-replay-viewer"}` (parsed); `tools/build_replay_viewer.sh` present, mode 100755, wired as the build hook (ci.yml:233-257, coworld-release.yml certify asserts the static-bundle marker); no pod replay path in the manifest (the `/client/replay` mentions are protocol-doc text describing live-server routes; the doc itself says "never a pod"); `static_replay.js` fetches only the `replay` URL param. |
| 4 Both name spaces | PASS | `tests/test_server.nim:124-142` — LLM view carries no `player.address` even with `showPlayerLabels` forced true; chrome roster and `results.names` carry real names (`broadcast.nim:208-252`, `roster` `pol`/`name`); aliases Cobalt/Rust everywhere seat-visible (`decide.nim:177-180`). |
| 5 Degrade-never-hang | PASS | Every wait bounded: batch attempt 4.5 s / retry 2.0 s floored to whole seconds inside a monotonic 7 s turn deadline (`decide.nim:327-408`), inter-batch floor is a bounded sleep capped by remaining budget (`:299-311`), budget guard (`:334-343`), 660 s wall stop in the tick loop (`server.nim:740-743`), lobby join timeout (`server.nim:718-719`); 660 ≤ 0.6×1200 asserted in `test_manifest`; `test_engine` covers hung client (<4 s), wall_clock, sim_fault, disconnect-degrade, never-connecting seat. |
| 6 num_agents | PASS | Parsed: `num_agents == 2` in `default`, `sprint`, `certification.game_config`; `len(certification.players) == len(game_config.players) == 2`. `tools/ci/docker_smoke.sh:106-152` enforces all four invariants before any container starts, `SMOKE_SEATS` independent cross-check (ci.yml:190). `grep -c "SEAT-COUNT FAIL"` over the full downloaded run-32674800419 log: **0**; log shows `seats=2`, both player containers `exited 0`, `reason=complete`. |
| 7 Scripted baseline full episodes | PASS | `tests/test_baselines.nim`: 1000 orders schema-legal and force-bounded (`:14-45`); porter×porter delivers on all 20 seeds — delivery is `finishGame(reasonComplete, erDelivered)` (`sim.nim:648`) — mean damage < 400, worst ≤ 700; `test_engine.nim:133-150` asserts `endReason == reasonComplete` explicitly; docker-smoke ran a real containerised all-scripted episode to `reason=complete`. Grid harness committed: `tools/tune_baselines.nim` (`--eval`/`--sweep`), `docs/BASELINE-TUNING.md`. The documented porter×mule divergence (14/20 → strictly-better-than-mule×mule) was in the initial commit with measured justification, not a loosening made during the run. |
| 8 LLM reply handling | PASS | `extractJsonObject` fence/prose-tolerant (`llm.nim`), tolerant repair table in `orders.nim` (percentages, `{"x","y"}` drive, numeric strings — `tests/test_orders.nim` exercises each); exactly one batched retry then porter fallback (`decide.nim:391-459`); every fallback writes a `fallback` record with `cause` ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard} and `fallbackTurns` reaches `results` for phase 60. |
| 9 Rune-safe truncation | PASS | `clipRunes` (`orders.nim:72-86`) on note/say/policy/detail/record; `llm.nim:164-170,211-212` rune-cuts captured provider text; prompt capped at the transport (`tandem_player.nim:50-54,73`); `tests/test_orders.nim:94-116` puts a 4-byte emoji on the cap boundary and asserts `isValidUtf8` + round-trip; `test_replay` `summaryIsStrictUtf8` forces non-ASCII through `replay_summary.py` under a strict decoder. |
| 10 Manifest validates | PASS | Parsed at head: `docs.readme` text (3451 B) + 3 pages (`rules.md`/`protocol.md`/`carrying.md`, all `{"type":"text","value":…}`, non-empty); `protocols` carries both `player` (1976 B text) and `global` (1278 B text). |
| 11 Viewer legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; … }` at `client/replay_broadcast.html:1172`; `@media (max-width: 640px)` at `:1323-1328` hides `.strain-num`, `.plate-blame`, `.plate-alias`, `#arrowlegend`; `#stage.tiny` density rules present; `tests/test_viewer.nim legibleAt360` pins both. |
| 12 Release order and scaffold | PASS | `coworld-release.yml` single job, steps in order: Build the Coworld manifest (:153) → Certify locally (:167) → Upload the policies (:206, explicitly before upload) → Upload the Coworld (:304, `--wait-hosted-smoke` in the same run against the just-built manifest) → Put the Coworld secret (:342). All three workflows present; `docker_smoke.sh` mode 100755; `policies.json`: 4 policies — `tandem-anchor` (PLAYER_PROMPT), `tandem-feather` (PLAYER_PROMPT, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `tandem-porter`/`tandem-mule` (PLAYER_SCRIPTED). The three-name placeholder grep over the five named files exits 1 (nothing found); the four designed angle-bracket survivors are exactly where the checklist says. |
| 13 Viewer executes | PASS | Run **32674800419** `wasm-viewer`: `needs: docker-smoke` (ci.yml:220); "Load the bundle in a real browser" step ran (not skipped, no continue-on-error): `{"loaded":true,"ms":2885,"clock":"0:25 TIME LEFT","scorebug":"Cobalt … Rust …"}`, `soak: 12s of playback kept advancing ("1 / 948" -> "241 / 948" -> "289 / 948")`, against the replay docker-smoke produced (artifact sha256 match up/down). `static_replay.js` sets `data-replay-loaded` (:152) and `data-replay-error` in `showFailure` (:21) from its own code paths; `config.nims` has **no** MODULARIZE/EXPORT_NAME (grep 0) and the worker bootstrap is `var Module = {}` + `Module.onRuntimeInitialized` (`static_replay_worker.js:8,166`) — the matched starter pair. |
| 14 Chrome is the starter's | PASS | `chrome_common.js` sha256-identical to `/workspace/starters/coworld-ctf`'s (diff empty). `replay_broadcast.html` above-banner region vs the starter: **7 hunks total** — the title, three comment-word tweaks, and the two note-listed removals (`#povBadge`+`#fpv` CSS block, `#viewpanel` CSS block); CSS sections 1–5 otherwise byte-identical. The 2340-vs-4165 line count is the note-listed removals plus the replaced CTF game block, not a rewrite. Transport rules executed: `relayout()` measures `#transport` → `--band`/`--topband`/`--hudscale` on `documentElement` (:1963-1994); overlays ride `bottom: calc(var(--band, 0px) + 10 * var(--u))` (:1236, :1250); `#endcard` keeps `top: var(--topband)/bottom: var(--band)` (:740-741), shows via `#endcard.on` (:752) and every non-gameover frame removes it (:1820) — executed. Beats are labelled buttons that seek (executed, B1). `#viewpanel`/zoom/minimap fully removed (markup, CSS, wiring, test ids — `test_viewer` asserts, plus `core.attachMinimap`/`core.zoomAt` absent) for a fixed 1110×630 board that always fits. `broadcast_core.js` differs from the starter's in exactly the wire name (2 lines, diff shown). |
| Simultaneous batch | PASS | One `curly.makeRequests` batch per attempt for both seats (`decide.nim:244-274`); "Seats are NEVER queried sequentially" is enforced by structure — the only transport call site takes the whole `calls` seq; `tests/test_engine.nim` asserts the two seats' in-flight windows are the same window (`windows.len == 1`). |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed in `59c52f6` (rename to `markTandemBeat`, nothing above the banner changed) | rename + 7 call sites at head; scope check clean on both pages, fails pre-fix; executed: 5/5 `<button>` markers with aria-labels, click posts `s:<tick>`; all r2 hunks to the page are below the banner (`git diff` hunk offsets ≥ 1259) | yes |
| F2 | fixed in `01d73df` (delta-shaped emission, goldens unmoved) | `broadcast.nim:96-98`; `deliveryIsABeat` non-vacuous (asserts count==1, tick, ordering); goldens touched only in `68e39b0`; determinism gate green at head | yes |
| F3 | fixed in `20c4b28`; fixer self-corrected its commit message (bundle **does** ship league.html) | retargeted shell verified; served at `/client/league` and bundled as `league.html` (Dockerfile.replay-viewer:46,57); the self-correction is accurate | yes |
| F4 | fixed in `f345cd5` | `renderVerdict` + per-rule tints; executed show/clear cycle | yes |
| F5 | fixed in `f939b2f`, fails on pre-fix tree | reproduced the failure on `59c52f6~1` via a node port of the same parse | yes |
| F6 | fixed in `19d48c5` | `height: auto; transform: none; margin-left` override, inherited rule untouched | yes |
| F7 | fixed in `ac662b2`, all four | all four hunks read; `lastDamageTurn` honestly left NOTED (confirmed: declared once, never used, not hashed) | yes |
| CI claim | run 32674800419 success, loaded:true, SEAT-COUNT grep 0 | re-fetched independently: identical run id, conclusion, step evidence, grep count | yes |

## Non-blocking observations

- `src/tandem/sim_types.nim:470` — `SimServer.lastDamageTurn` is declared, never written, never
  read, not hashed (grep: one hit in the repo). Same class as the field F7 deleted; the fixer
  declared it NOTED rather than folding it into an unrelated commit. Advisory only.
- `tools/ci/viewer_smoke.mjs` reports `feed_lines: 0` structurally (it queries `#feed, .feed, #log`;
  tandem's feed is `#killfeed`). Verbatim template file; not evidence about the feed, which renders
  (executed in r2 review and reproduced here via `row.textContent`).
- `client/league_replayer.html:816` still calls chrome_common's `ingestBeats(s)` — inert for
  tandem's beat kinds (chrome's builder only fires on steal/return/capture) and deduped by
  tick|kind anyway. Harmless inherited call.
- History quirk: the r1 fix series was applied twice (`e8d0742..0d5fdc6`, then `0763453..3a35bb5`)
  in one linear history; the two end trees are identical (`git diff` empty), so the interleaved
  "deletions" in the second series are re-application artifacts, not lost tests.
- LLM-path-in-production remains unexercised by CI (everything containerised is scripted; the
  batch transport is covered by the fake in `test_engine`). That is phase 60's
  `replay_summary.py` check by design, not a checklist item here.

BLOCKING: 0
