blocking: 0

# r1 verdict — rumor

Head: `5ac1631a1f1fdd5ecb63a6fe729281cb1181e760` (main; review was written at `ed38e35`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + simultaneous-decision addendum)
Independent read written before reading fixes: **yes** — and per the brief I did **not** read
`runs/2026-08-23-rumor/reviews/r1-fixes.md` at all; every disposition below was verified from
the tree at `5ac1631`, the git history, and the CI logs directly.

CI evidence used: run **32664881692** (ci.yml, main, sha `5ac1631`, conclusion **success**;
jobs test / docker-smoke / wasm-viewer all success) and the earlier green run 32654839685 @
`ed38e35`, both from `gh run list -R Metta-AI/cogame-rumor --branch main -w ci.yml`.

## Standing blocking findings

**None.** The review reported zero blocking findings; my attempt to overturn that — an
independent pass over all 14 checklist items plus the addendum — found nothing standing
either.

## Refuted / resolved review findings

The review at `ed38e35` filed everything as non-blocking. Five of its findings described real
gaps at that sha which are **resolved at the current head** (a finding true at review time and
fixed since is resolved, not standing); the rest are confirmed-advisory design-note mismatches
or informational notes. Verified one by one:

### F1 — fallback not recorded in the replay → RESOLVED at `b084458`
- Evidence: `src/rumor/llm.nim:51` — `Decision` now carries `scripted*: bool`;
  `llm.nim:243` — `scriptedAction` sets `result.scripted = true` ("Provenance, carried to the
  server, into the event and into the replay"); `src/rumor/server.nim:300-301` —
  `let wasScripted = decision.scripted or scripted[seat] != skNone or client.disabled`.
  `tests/test_bot.nim:133-143` asserts the flag reaches the event and
  `eventToJson()["scripted"]`; `tests/test_bot.nim:304-349` (added `b3ca7b7`) proves it end to
  end through a real failed transport. Checklist item 8's "the fallback is recorded so phase 60
  can count it" is now satisfied from the replay bytes, not just stdout.

### F2 — replay test compared only count + final frame → RESOLVED at `eed4a10` (+ `5ac1631` rename)
- Evidence: `tests/test_sim.nim:461-493` — `liveFrames` snapshots the live
  `tableStateJson()` after **every** seat action (41 checkpoints = 4×Seats+1, asserted), and
  `check $frames[point.index].tableStateJson() == point.state` compares each against the
  re-derivation at that exact event index. `5ac1631` is a pure variable rename
  (`checkpoints` → `liveFrames`); I read the hunk — no assertion changed.

### F4 — viewer smoke ran without `--soak` → RESOLVED at `0219ea0`
- Evidence: `.github/workflows/ci.yml:310-314` — `node tools/ci/viewer_smoke.mjs … --timeout 90
  --soak 10`. Run 32664881692's `Load the bundle in a real browser` step log:
  `{"loaded":true,"ms":290,…}`, then `soak: 10s of playback kept advancing`, then three
  distinct scrub readouts (`ROUND 1 / 3…` / `ROUND 3 / 3…` / `TRUTH — BARRED · HONEST 6/8…`).

### F8 — captured LLM error text byte-sliced → RESOLVED at `708e4b7`
- Evidence: `src/rumor/llm.nim:386-392` — `errorHead` uses `runeSubStr`, applied at every
  capture site (`:402`, `:438`, `:443`, `:448`, `:452`, `:462`).
  `tests/test_bot.nim:239-252` feeds `"日"×300` and asserts `runeLen == 163` and
  `validateUtf8() == -1`. (These strings never reached the replay even before the fix — the
  review's own trace of that stands — so this also closes the strict reading of item 9's
  "captured errors".)

### F15 — player receive loop was an unbounded blocking read → RESOLVED at `7a26b72`
- Evidence: `src/rumor_player.nim:67-87` — `socket.receiveMessage(ReadTimeoutMs)` with
  `ReadTimeoutMs = 5_000`, inside `while epochTime() < deadline` where
  `deadline = epochTime() + budgetSeconds + 300.0` (budget from `COWORLD_TIMEOUT_SECONDS`,
  else 1200). Every read is bounded and the loop as a whole is bounded; item 5's "no unbounded
  loop or blocking read" holds at head.

### F17 — uncaught double-raise in the server fallback path → RESOLVED at `ef2b6de`
- Evidence: `src/rumor/server.nim:319-330` — the scripted fallback is now applied inside its
  own `try/except RumorError`, so an (unreachable) second rejection logs and skips the seat
  instead of killing the game thread. The play deadline still bounds the episode.

### Review "could not determine" items — all three settled at head
- **Grid harness (item 7).** `tests/test_sweep.nim` (added `e763a6a`, 117 lines) sweeps the
  claim weight over an 8-cell grid × 300 seeds, proves the parameterised baseline reproduces
  the shipped one episode-for-episode, asserts the shipped weight sits on the plateau
  (`rates[best] - rates[ShippedCell] <= 0.03`) and beats the ignore-the-network cell, and
  verifies both constants are the derivations they claim (`ln(0.6/0.4)`, `ln(0.56/0.44)`).
  It ran in CI run 32664881692, debug and release; log shows the full table
  (`best cell 0.75x at 0.6945; shipped 1.0x at 0.6833` — within the plateau tolerance).
- **Retry-once path end to end.** `tests/test_bot.nim:304-349` (added `b3ca7b7`) points a
  non-disabled Bedrock client at a closed port: both batches fail at the transport, the test
  asserts two dispatches with one rate-governor spacing between them
  (`elapsed >= MinBatchSpacingSeconds * 1000`), the whole turn inside `TurnBudgetSeconds`,
  and every decision scripted and recorded as such in the event JSON.
- **`/client/replay` strict-vs-intent (F7) — my ruling: not blocking.** The manifest's
  `game.replay_viewer` is `{"bundle": "static-replay-viewer"}`
  (`coworld_manifest_template.json:16-18`); the static shell fetches nothing but the
  `?replay=` URL (`replay-viewer/static_replay.js:67-89, 127-150`); the release gate
  hard-requires the `Replay liveness: skipped (static replay bundle declared` marker
  (`coworld-release.yml`), so a pod-served viewer cannot ship. The `/client/replay` route
  (`server.nim:491`) and the sentence in `protocols.global` are byte-for-byte the bullwhip
  starter's own inherited local-debug surface
  (`/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:470` and its manifest's
  identical prose). Item 3's target is the platform replay path being a pod; that is
  falsified nowhere. Blocking the starter's own inherited chrome on a literal reading would
  make every bullwhip-lineage repo unshippable, which cannot be the item's meaning.

### Confirmed-advisory findings (correct observations, no checklist item falsified)
F3 (cert fixture `rounds: 3` vs the note's self-contradictory `rounds: 2` — the note also
pins `MinRounds = 3`, so the code's value is the only consistent one; smoke replay still
outlasts the 10 s soak at ~47 events), F5 (chrome.css append under a banner — the exact shape
item 14 blesses), F6 (item-14 identifier list is another lineage's; the checklist NOTE
covers it and the starter's equivalents are verified preserved), F9/F10 (parser strictly more
tolerant than the note — the note's own "everything else degrades silently" rule), F11
(measured baseline rates 0.699/0.657 vs note's reference 0.682/0.621 — inside the test bands,
ordering preserved, README updated), F12 (`#clock` tally wording), F13 (truth stamp drawn on
canvas rather than `#lightpool`), F14 (three extra `Sim` fields, all load-bearing for
documented behaviour), F16 (`update()` clamps rather than rejects `rounds > 6` — exactly what
the note specifies). All verified against the head tree; none maps to a checklist item.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 32664881692, conclusion success, sha `5ac1631` (`gh run list`). `git log -p -- tests/`: `db9d644` adds the two suites; `b084458`/`eed4a10`/`708e4b7`/`e763a6a`/`b3ca7b7` only **add** assertions; `5ac1631` is a pure rename (hunk read). No skip/xfail/deleted assertion/widened tolerance anywhere; no test file removed. |
| 2 Replay re-derivation | PASS | `sim.nim:903-956` `replayMatch` replays say/vote through the rules and raises on tampered round/truth/clues/roles; test `test_sim.nim:461-493` compares every checkpointed frame; viewer derives display from the same code — `replay-viewer/rumor_replay.nim:38-40` calls `replayMatch` and `renderer.js:1310-1311` reads only those `states`. The written replay carries events, never states (`server.nim:132-156`). |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer = {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, `mkdir -p` before containment; shell fetches only the `?replay=` URL. `/client/replay` ruling above. |
| 4 Both name spaces | PASS | Prompts/inboxes/player frames carry aliases only (`llm.nim:252-324`, `sim.nim:790-839`; asserted `test_bot.nim:254-292`); viewer maps alias→policy name incl. inside message text, baseline fillers stay aliased (`renderer.js:695-723`). |
| 5 Degrade-never-hang | PASS | Connect wait ≤120 s (`server.nim:221-227`); governor sleep ≤26 s (`llm.nim:152-166`); batch ≤25 s (`llm.nim:605`); retry gated by the 80 s turn budget (`llm.nim:589-594`); pre-turn deadline check → `forceBallot` (`server.nim:271-276`, `sim.nim:628-643`); player reads bounded 5 s inside a deadline (`rumor_player.nim:67-87`). `sampleEpisode` caps rounds so 120 + 7×80 = 680 s < 720 s, asserted at `test_sim.nim:597-601`. |
| 6 num_agents | PASS | `num_agents: 10` in both variants and `certification.game_config`; `docker_smoke.sh:106-151` enforces all four invariants + the `SMOKE_SEATS` cross-check with `SEAT-COUNT FAIL:` prefixes. I grepped the full head-run log: **zero** occurrences of `SEAT-COUNT FAIL`; `smoke OK: seats=10 … reason=complete`. |
| 7 Scripted baseline | PASS | `test_bot.nim:46-72`: 2 baselines × 4 topologies × 4 seeds, `reason == "complete"`, per-decision legality audit (`:29-37`). Grid harness: `tests/test_sweep.nim`, ran green in CI (evidence above). |
| 8 LLM reply handling | PASS | `extractJsonObject` (`llm.nim:394-403`) tolerates prose/fences; retry exactly once (`for attempt in 0 .. 1`, `llm.nim:585`) with the hint; fallback to `scriptedAction` (`llm.nim:622-625`); recorded via `Decision.scripted` → event → replay (`llm.nim:243`, `server.nim:300-301`, `sim.nim:584/615`), tested at `test_bot.nim:304-349`. |
| 9 Rune-safe truncation | PASS | `trimRunes` (`sim.nim:478-483`), `cleanText` (`llm.nim:466-472`), prompt cap (`server.nim:460-461`), `errorHead` (`llm.nim:386-392`) — all `runeSubStr`. Multi-byte-at-cap tests: `test_sim.nim:430-458`, `test_bot.nim:201-208, 227-231, 239-252`; smoke decodes the replay as strict UTF-8. |
| 10 Manifest validates | PASS | `game.docs.readme = {"type":"text","value":…}`, `pages` = rules.md + scoring.md each `{id,title,content:{type,value}}`; `game.protocols` carries both `player` and `global` (verified by parsing the JSON). |
| 11 Legible at 360 px | PASS | `chrome.css:280-292` `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` (starter's, unmodified); `:460-464` hides `.plate-label` under 640 px. |
| 12 Release order & scaffold | PASS | `coworld-release.yml`: Build manifest → Certify → Upload the policies → Upload the Coworld → Put the Coworld secret, in that order. All three workflows present; `docker_smoke.sh` 100755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 `rumor-skeptic` carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. I ran the three-name placeholder grep verbatim: no hits (gate exits 0). |
| 13 Viewer executes | PASS | `wasm-viewer` `needs: docker-smoke` (`ci.yml:212`); no `continue-on-error` anywhere in the workflows (grepped); the `Load the bundle in a real browser` step ran and succeeded in run 32664881692 with `loaded: true`, `data-replay-error` never set, 10 s soak advancing, three distinct scrub readouts. `config.nims` `MODULARIZE=1` + `EXPORT_NAME=RumorReplayModule` and the shell's `RumorReplayModule()` factory are the same starter's pair (3-line rename diff); exported `_rm_*` functions match `rumor_replay.nim`'s exports exactly. Markers: loaded at `renderer.js:1373` on the first drawn frame, error at `static_replay.js:56`. |
| 14 Chrome is the starter's | PASS | Bullwhip has no `chrome_common.js`/`replay_broadcast.html`; per the checklist NOTE I judged its equivalents. `chrome.css` lines 1–467 byte-identical, one banner-commented game block appended. `global/player/replay.html` differ only in title/wordmark/clock text/renderer global. `renderer.js` 1383 lines vs starter's 1400 — the chrome (bindFeedToggle, renderFeed, buildScrub, makeNameMap/applyNames, makeEffects, attachLive, attachReplay, scrub drag-to-seek, endscreen) all present at same names/arity; only the canvas stage is new, which is the design note's declared change. Endscreen comes down on every seek (`setIndex` recomputes the `show` flag; scrub `onSeek` → `setIndex`). No zoom/minimap existed in the starter to remove; the graph stage fits the frame. |
| addendum: one parallel batch | PASS | `decideAll` builds one `RequestBatch` over all open seats and issues a single `client.curl.makeRequests(batch, timeout)` (`llm.nim:596-605`); the retry is one smaller batch. No per-seat request loop exists in the file; `server.nim:289` calls it once per turn. |

## Non-blocking observations (judge)

- `tools/ci/docker_smoke.sh` does **not** assert that every player container exits 0, though
  the design note (§Tests item 7) claims it does ("every player container also exits 0, raid
  0.1.4"). It checks the game's exit code, `player_failure.json`, and the artifacts only.
  No checklist item requires the player-exit assertion, so this is advisory — but it is a
  real note/code mismatch the review did not list, worth a line in a future round or a note
  correction.
- Design note §Viewer says the smoke fixture is `rounds: 2` / 36 events; the shipped fixture
  is `rounds: 3` (forced by the note's own `MinRounds = 3`) — the note should be corrected
  (same root as review F3).

## Fixer report audit

`r1-fixes.md` was off-limits to this verdict per the brief, so there is no claim-by-claim
audit of the fixer's self-report. In its place, every post-review commit was verified
directly against the head tree and the head CI run:

| commit | claims to address | I verified at `5ac1631` | agrees |
|---|---|---|---|
| `b084458` | F1 | `Decision.scripted` → event/replay; tests assert it | yes |
| `eed4a10` | F2 | frame-by-frame replay comparison in `test_sim.nim` | yes |
| `708e4b7` | F8 | `errorHead` rune-safe + tests | yes |
| `7a26b72` | F15 | bounded player receive loop | yes |
| `ef2b6de` | F17 | guarded fallback apply | yes |
| `0219ea0` | F4 | `--soak 10` in ci.yml; soak ran green in 32664881692 | yes |
| `e763a6a` | CD1 (grid harness) | `tests/test_sweep.nim`, ran green | yes |
| `b3ca7b7` | CD3 (retry path) | end-to-end transport-failure test | yes |
| `5ac1631` | F2 follow-up | pure rename, no assertion changed | yes |

BLOCKING: 0
