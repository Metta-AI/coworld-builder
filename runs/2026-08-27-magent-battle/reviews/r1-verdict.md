blocking: 0

# r1 verdict — magent-battle

Head: `3c85c8d428f71b64771a1768107bf5d55d964a28` (main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + parallel-batch rule)
Independent read written before reading fixes: **yes** — I traced the tree, the manifest, the
starter diffs and CI run 33057473716 and completed my own checklist pass before opening
`r1-review.md`, and only opened `r1-fixes.md` after both. No contamination.

Review under judgment: `r1-review.md` (written at `95e94c9`, **zero blocking findings**, 19
non-blocking F1–F19). The head has moved 9+ commits since the review; per the brief I judged every
finding at the **current head**, where most of them have been fixed.

## Standing blocking findings

**None.** Neither the reviewer's findings nor my own independent pass produced a finding that
falsifies a checklist item at `3c85c8d`.

## Refuted / resolved-at-head (the reviewer's findings, each re-checked)

The review filed nothing as blocking, so "refuted" here means: the observation no longer reproduces
at the current head, or never touched a checklist item. Verified one by one:

### F9 — "the main viewer smoke omits `--soak`" → RESOLVED AT HEAD
- Evidence: `.github/workflows/ci.yml:427-432` at `3c85c8d` — the browser step now passes
  `--soak 10` alongside `--strict-text-bounds`. Run 33057473716, step `Load the bundle in a real
  browser`: `soak: 10s of playback kept advancing ("0 / 117" -> "59 / 117" -> "75 / 117")`.

### F19 — ".tiny at 620 px, not under 640px" → RESOLVED AT HEAD
- Evidence: `client/replay_broadcast.html:1640` / `client/page_script.js:584` —
  `stage.classList.toggle('tiny', boardW < 640)`; label-hiding rule at
  `client/replay_broadcast.html:1771-1773`; `tests/test_magent_viewer.nim:219` re-pins the literal;
  the fixture drives 630 px (`tools/ci/renderer_fixture.html:41`). Item 11 now holds verbatim.

### F18 — "`game.docs` type uri, not text" → RESOLVED AT HEAD
- Evidence: `coworld_manifest_template.json:30-52` — `docs.readme` is
  `{"type":"text","value":<inline README>}` and both pages carry
  `content: {"type":"text","value":<inline doc>}`; `tests/test_magent_manifest.nim` asserts each
  inline value equals the file it embeds. Item 10 now holds verbatim.

### F10 — "the fixture does not assert its own string lengths" → RESOLVED AT HEAD
- Evidence: `tools/ci/renderer_fixture.html:66-77` fails unless `CAP_SAY` is still exactly 120
  runes ending on the two cap-straddling 4-byte emoji and the policy name is still ≥ 40 chars;
  `:175-184` asserts the rendered feed row's `textContent` still contains the whole 120-rune remark
  at every width. Item 15's "asserts its own strings are still full-length" clause now holds.

### F7 — "reply cap enforced in runes" → RESOLVED AT HEAD
- Evidence: `src/magent/llm.nim:181-186` — `body = body.truncateBytes(MaxReplyBytes)` with
  `truncateBytes` at `src/magent/sim_types.nim:110` backing off over continuation bytes;
  `tests/test_magent_replay.nim:246-266` covers emoji past the cap and a codepoint straddling it.

### F8 — "`disconnected` never emitted" → RESOLVED AT HEAD
- Evidence: `src/magent/decide.nim:247-254` writes a `fallback` record with cause `disconnected`
  per turn for a never-joined seat; `tests/test_magent_engine.nim:65-74` parses the replay bytes
  and asserts it. `throttled` remains as a documented extension of the note's enum (nothing
  consumes the set as closed) — not a checklist matter.

### F11 / F12 / F14 — verdict cap, spoiler gate, duplicate beat, curtain-eaten click → RESOLVED AT HEAD
- Evidence: `client/replay_broadcast.html:1531-1540` (endcard feeds `setVerdict` via the chrome's
  documented fallback path, alias vocabulary), `:1914-1931` (`mgSpoilerGate` applies the chrome's
  `__tick > s.t` rule to the game block's own markers), the `if (jumped) placed = {}` reset is gone
  (grep: `placed = {}` appears only at declaration, line 1876), and `:1700-1711`
  (`#lockerroom { pointer-events: none; }` in the appended block). Run 33057473716's scrub readouts
  show a served backward seek (50 % → tick 4, both armies whole).

### F15 (sub-items) → RESOLVED AT HEAD or correctly disputed
- Caps deduplicated: `src/magent_battle_player.nim:23` imports `magent/sim_types`; no local
  re-declaration. Unreachable event kinds: all eight `SimEventKind` values now have an `emitEvent`
  call site (verified by grep: Attack, Kill, Rout, Wipe, TurnStart, Directive, Fallback,
  PhaseChange). `tune_baselines --check` runs in CI (`ci.yml:152-162`; log:
  `shipped pick ranks 7 of 27: ok`). `p0.log`/`p1.log` deleted. Failure payload asserted against
  `roster.playerFailurePayload`, the proc the server writes (`tests/test_magent_engine.nim:54-63`).
- **`nim.cfg` "committed AND ignored" — the reviewer was WRONG**: `git ls-tree 95e94c9 -- nim.cfg`
  and `git ls-tree HEAD -- nim.cfg` are both empty; the file was never tracked at either sha. The
  fixer's DISPUTED disposition is confirmed.

### F1–F6, F13, F15 (remainder), F16, F17 — stand as observations, none touch a checklist item
- F1 (30 per army at mapSize 31, not the note's 25): sound; the note's own instruction was "assert
  the number rather than trusting this paragraph"; `PATCHES.md` §7 + `test_magent_spawn.nim:83-85`.
- F2 (occupancy read at decision time): a documented, deterministic divergence from the note that
  removes a real deadlock; `PATCHES.md` §6; determinism preserved (all actions computed against the
  tick snapshot before resolution — `sim.nim`), and the re-derivation suites are green.
- F3 (8 ticks/s playback, chips [1,2,4,8]): no checklist item names a playback rate; the stale
  `TargetFps` comment is fixed at head (`sim_types.nim:45-49`, `PATCHES.md` §9).
- F4 (broadcast_core is a retargeted rewrite): item 14 pins `chrome_common.js` (byte-identical —
  verified, sha256 equal to the starter's) and `replay_broadcast.html` (provenance verified below);
  it does not pin `broadcast_core.js`, which the design note declares a fork. The overstated header
  is rewritten at head.
- F6 (`turnSpacingMs` is a bounded blocking sleep): item 5 requires explicit bounds, which hold
  (8 s cap); the note's "keeps stepping ticks" is a design-note property, not a checklist one, and
  the budget arithmetic still fits (see item 5 below). `PATCHES.md` §10 records it.
- F13 (dev-page transport axis): fixed at head anyway (`broadcast.nim:190-206`, live axis from the
  sim clock); dev-only either way.
- F16/F17: the note's stale arithmetic is not the tree's problem; the manifest description at head
  names both percentages (`coworld_manifest_template.json:114`).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1. CI green, no test loosened | PASS | Run **33057473716**, `completed success` on main at `3c85c8d` (`gh run list -R Metta-AI/cogame-magent-battle --branch main -w ci.yml`); 4 jobs ✓; test job log: 170 `[OK]`, 0 failed, both modes. `git log -p --since=2026-08-27T06:30:00Z -- tests/`: 10 commits, every hunk read — two assertion *replacements* track intentional conformance fixes (620→640 threshold re-pinned at the new value, docs-URI checks replaced by strictly stronger inline-text-equals-file checks); everything else adds assertions. No skip, no deletion, no widened tolerance, no removed file. |
| 2. Replay re-derivation | PASS | `tests/test_magent_replay.nim:28-124` record→re-derive for all four end reasons with `mismatch == -1` (per-tick hash), `:126-154` a corrupted hash is caught at its exact tick; `tests/test_magent_determinism.nim`. Viewer derives display from the same re-derivation: `replay-viewer/magent_replay.nim:13` imports `magent/sim`; `replay_runtime.nim` re-steps and checks hashes; no parallel recording. |
| 3. Static viewer | PASS | `coworld_manifest_template.json:9-11` `"replay_viewer":{"bundle":"static-replay-viewer"}` under `game`; `tools/build_replay_viewer.sh` present, mode 100755, invoked by path in ci.yml:354 and asserted executable (ci.yml:330-341, manifest job:184-189). Viewer network surface: `static_replay_worker.js:113` fetches only the replay URL; `broadcast_core.js:82` fetches co-located art relatively. No pod viewer declared anywhere in the manifest (`/client/replay` exists only as the dev-local server route, `server.nim:36,226-231`, never declared to the platform — the starter's own convention). |
| 4. Both name spaces | PASS | Observations/prompts carry aliases only (`decide.nim:60-144` via `seatAliasName`/`squadAlias`; `tests/test_magent_labels.nim` "the observation and the prompt carry NO real name"); viewer scorebug shows real policy names (`broadcast.nim` seats[].name; `#pname-*` in the page); `showPlayerLabels: false` in every shipped config (asserted). |
| 5. Degrade-never-hang | PASS | Every wait bounded at its site: attempt 1 = 9 s, retry = 4 s (`decide.nim:279-297`, curl-enforced), exactly one retry (`attempt < 2`, :270), outer `turnBudgetMs` 14 s checked per attempt (:273-277), `turnSpacingMs` sleep capped at 8 s (:260-263), lobby `lobbyJoinTimeoutTicks` (`sim_state.nim:141-142`), frame limiter `sleep(1)` bounded by frameDuration (`server.nim:520-527`), engine stop at `wallClockBudgetSeconds ≤ 660` checked at the top of every frame (`episode.nim:36-53,164`), budget guard switches LLM off from elapsed > 632 s (`decide.nim:216-223`), 20 s shutdown grace. Worst case ≈ 615 s (+ ≤ 17 s to serve a mid-turn stop) < 660 < **720 s = 60 % of 1200**; `tests/test_magent_manifest.nim` asserts `budget*100 <= timeoutSeconds*60` for every variant. No unbounded loop or blocking read found. |
| 6. num_agents | PASS | `num_agents: 2` in `variants[0].game_config` (:194), `variants[1].game_config` (:215), `certification.game_config` (:235). `tools/ci/docker_smoke.sh:106-151` enforces all four invariants with `SEAT-COUNT FAIL:` prefixes before any container starts; `SMOKE_SEATS` is the independent second declaration (script default "2", ci.yml header documents it). **Grep of the full docker-smoke log of run 33057473716: zero `SEAT-COUNT FAIL`**; the job printed `game=magent-battle seats=2` then `smoke OK: seats=2 results=588B replay=21237B reason=complete`. |
| 7. Scripted baseline full episodes | PASS | `tests/test_magent_engine.nim:15-37` runs an all-scripted two-game episode to the natural end and asserts `reason == ReasonComplete`, zero-sum scores, opposite `redSlot`; `tests/test_magent_control.nim:45-72` validates every order of both baselines over 200 randomised worlds (≤9 entries, own ids, enum verbs, on-board holds, enemy focus targets, left/right flanks). Tuning: `tools/tune_baselines.nim` grid, pick recorded in `tools/ci/baseline_tuning.json`, asserted by `tests/test_magent_tuning.nim` AND re-run in CI at the tuned horizon (`ci.yml:152-162`; log `shipped pick ranks 7 of 27: ok`). |
| 8. LLM reply handling | PASS | `directives.nim:100-138` extracts the outermost balanced `{…}` from prose/fences; retry exactly once as a second parallel batch (`decide.nim:270`); second failure → `fallbackDirective` = the pincer proc (`baselines.nim`, identity asserted by test), `fallback` record written with cause + `results.fallbackTurns` counted (`episode.nim:98-101`), `falling back` echoed in the game log for phase 60 (`decide.nim:347-349`). |
| 9. Rune-safe truncation | PASS | `truncateRunes`/`sanitizeLine`/`sanitizeSay` (`sim_types.nim:99-135`) on say 120 / notes 240 / label 64 / stopDetail 200 / fallback detail 200 / prompt 4000; the one byte budget cut on a codepoint boundary (`llm.nim:181-186`, `truncateBytes`). Tests feed 4-byte emoji at every cap and assert valid UTF-8 (`test_magent_control.nim:218-238`, `test_magent_replay.nim:186-266`, plus the strict Python `raw.decode("utf-8")` over the real smoke replay in CI). |
| 10. Manifest validates | PASS | `game.docs` = `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}` (manifest:30-52); `game.protocols` carries both `player` and `global` as `{"type","value"}` objects (:20-29). The manifest job runs the installed coworld 0.1.43's own validators — green in run 33057473716. |
| 11. Legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` (`replay_broadcast.html:1716-1720`); labels hidden under 640 px (`:1771-1773`, toggle `boardW < 640` at `:1640`); fixture measures 360 px explicitly. |
| 12. Release order & scaffold | PASS | `coworld-release.yml`: Build manifest (:159) → Certify (:173, `--timeout-seconds 300`) → Upload policies (:216) → Upload Coworld (:314) → Put secret (:352). All three workflows present; `docker_smoke.sh` 100755; smoke builds its image in the same job before running. `policies.json`: 4 distinct policies — 2 × `PLAYER_PROMPT` champions, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, 2 × `PLAYER_SCRIPTED` fillers (line, pincer). The three-name placeholder grep exits 0 (run locally: `PLACEHOLDER_GATE_CLEAN`); only the four documented runtime angle-bracket names survive. |
| 13. Viewer executes | PASS | Run **33057473716**, `wasm-viewer` ✓ with `needs: docker-smoke` (ci.yml:317), no `continue-on-error` anywhere; the `Load the bundle in a real browser` step ran and printed `{"loaded":true,"ms":326,…}` plus the soak line — against the replay docker-smoke produced in the same run. `data-replay-loaded="true"` set in the adapter's `'loaded'` branch (`static_replay.js:164`), which the worker posts only after `ingestPacket()` handed the first frame (`static_replay_worker.js:127-131`); `data-replay-error` set in `showFailure()` (`static_replay.js:14-20`). Link flags and bootstrap are the SAME starter's matching pair: `config.nims` has no MODULARIZE/EXPORT_NAME (non-modularized `magent_replay.js`) and the worker sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`) — diff against the starter is identifier renames plus the dropped asset preload. |
| 14. Chrome is the starter's | PASS | `client/chrome_common.js` **byte-identical** (sha256 equal; test pins length 40022 + SHA-1). `client/replay_broadcast.html` reproduces **byte-for-byte** from the read-only starter via the committed `tools/build_broadcast_page.py` (I re-ran it: identical), and the CSS above the `MAGENT-BATTLE additions` banner is a strict line-subset of the starter's (removals only — all from the note's list; the only non-starter lines above the banner are the note's enumerated relabels and the forked page IIFE the note declares). The size reduction is the deleted paintbot IIFE + removed panels, not a rewrite — provenance beats the size heuristic, and `tests/test_magent_viewer.nim:108-123` byte-pins the inherited prefix (60731 B, SHA-1) so a hand-edit fails in CI. Transport rules: (a) `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (:1635-1645); (b) nothing fixed-positioned in the band (zero `position: fixed` in the page; `#endcard` rides `top: var(--topband)` / `bottom: var(--band)`); (c) `#endcard { bottom: var(--band, 0px) }` (:571), shown with `#endcard.on` (:582), dismissed on scrub click (:1559-1560) and state-removed on any seek that leaves gameover (:1499-1501); (d) beats are labelled `<button>`s via `battleBeat` seeking `s:<tick>` (:1891-1911) with CSS for exactly `{firstblood, rout, wipe, fallback, end}` (:1802-1823, set-equality asserted by test). `#viewpanel`/`#fpv*`/`#povBadge` removed — markup, CSS, wiring, and asserted absent; correct for a fixed 45×45 arena. |
| 15. Every drawn string fits | PASS | Run 33057473716, both steps: `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` — `never_inside == 0` with `--strict-text-bounds` on (ci.yml:432, :470). `total: 0` is structurally truthful, not a blind instrument: `grep fillText\|strokeText` over the fork's entire client/viewer JS returns only the comment `broadcast_core.js:38` stating the renderer "calls fillText nowhere" — every spectator string is DOM inside the starter's layout, so the cogchemists canvas-bubble class cannot exist here. The LLM-text gate the checklist requires exists: `tools/ci/renderer_fixture.html` loads the SHIPPED `dist/static-replay-viewer/index.html` in an iframe, drives the real chrome with a full-cap 120-rune `say` on both seats + an over-long policy name at 360/620/630/1024 px, asserts its own strings are still full-length before rendering (:66-77) and that the rendered row still carries the whole remark (:175-184), measures the real laid-out boxes, and runs in its own ci.yml step under `viewer_smoke.mjs --strict-text-bounds` (:453-471) — `{"loaded":true,"ms":2049}`. |
| Parallel batch | PASS | `decide.nim:281-297`: one `RequestBatch` with both seats' requests, one `makeRequests` call per attempt; no per-seat request loop exists anywhere. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | no change, already asserted | PATCHES.md §7 + spawn test at head | yes |
| F2 | fixed (PATCHES title) | PATCHES.md covers both kinds | yes |
| F3 | fixed | `sim_types.nim:45-49` corrected, §9 present | yes |
| F4 | fixed (honest header, dead formatter removed) | header rewritten; no fillText anywhere | yes |
| F5 | fixed | prefix byte-pinned: len 60731 + SHA-1 `753E95A5…6395`, test green | yes |
| F6 | documented divergence, no behaviour change | sleep still there, bounded; §10 present; arithmetic checks out | yes |
| F7 | fixed | `truncateBytes` at the byte cap + test | yes |
| F8 | fixed (disconnected emitted) | `decide.nim:247-254` + engine test parses replay bytes | yes |
| F9 | fixed | `--soak 10` in ci.yml; soak line in run 33057473716 | yes |
| F10 | fixed | fixture self-asserts 120 runes + full-length rendered text | yes |
| F11 | fixed both halves | `setVerdict` from endcard; `mgSpoilerGate` | yes |
| F12 | fixed | `placed = {}` reset removed; map persists | yes |
| F13 | fixed | live axis from sim clock, series omitted (`broadcast.nim:190-206`) | yes |
| F14 | fixed | `#lockerroom { pointer-events: none }`; backward seek served in CI readouts | yes |
| F15a–f | fixed | caps imported; 8/8 event kinds emitted; exactly-once counts; `--check` in CI; logs deleted; payload asserted against server proc | yes |
| F15 nim.cfg | DISPUTED | `git ls-tree` empty at both shas — reviewer was wrong, never tracked | yes |
| F15 no-change items | argued | league_replayer unreferenced; magentReward strings consistent across schema/docs/code; MaxUnits headroom; object `orders` strictly more tolerant; no `.data` correct after preload drop; "connects then never answers" unmappable (seats send no inputs) — all check out | yes |
| F16 | no change (note stale) | tree is right; test asserts the 60 % bound | yes |
| F17 | fixed | manifest:114 names both percentages | yes |
| F18 | conformed to checklist | inline text docs + equality-to-file tests + coworld 0.1.43 validators green | yes |
| F19 | conformed to checklist | `boardW < 640` + re-pinned test + 630 px fixture width | yes |

The fixer's claim of "170 [OK], 0 FAILED" is confirmed from the run 33057473716 test-job log (the
single grep hit on `FAILED` is the workflow's own error-template line). The claim that
`replay_broadcast.html` was only regenerated, never hand-edited, is corroborated: the committed page
still reproduces byte-for-byte from the starter via the builder, and the inherited-prefix pin is
unchanged across the four regenerations.

## Non-blocking observations (residue for a future round, none checklist-relevant)

- The design note's copy in `docs/plans/` retains stale facts the tree corrected (25 vs 30 per army,
  `[0.5,1,2,4,8]` chips, `league_replayer.html`, `magent_replay.data`, the 544 s worst case); all are
  recorded in `vendor/PATCHES.md` §6–§10 instead.
- `broadcast_core.js` keeps `pushFeed`/`drainFeed` with no in-core caller (deliberate, pinned by
  test); live mode still ships `"en": true` so dev-page scrub clicks send commands the live server
  ignores — dev-only.
- The LLM leg against a live provider and real-latency wall-clock behaviour remain phase-60 items by
  construction (CI runs keyless); the bounds that guarantee settling are code facts verified above.

BLOCKING: 0
