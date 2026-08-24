blocking: 0

# r1 verdict — cogolf

Head: `529c0f8b0e9b7942a543401aca02ee872a8da0aa` (`main` of `Metta-AI/cogame-cogolf`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + the
simultaneous-batch rule)
Independent read written before reading fixes: **yes** — I read the design note, the full
tree at head, the CI run and job logs, and wrote my own checklist notes before opening
`r1-review.md`, and only opened `r1-fixes.md` after refuting the review's findings.

The review was written against `a60233b`; the head is three commits later
(`9a63d64`, `46eecce`, `529c0f8`). Both of the review's blocking findings were true at
`a60233b` and are **fixed at the current head**, so they are refuted as *standing* findings
(a finding that was true and has since been fixed is refuted, not standing). My own
independent pass over all fourteen checklist items found no further blocking finding.

## Standing blocking findings

None.

## Refuted

### B1 — "the page's own failure paths never set `data-replay-error`" → REFUTED (fixed at head)
- Reviewer's claim (checklist 13, static-viewer): only `client/static_replay.js:33` wrote
  `data-replay-error`; the page's boot catch, no-data card and stuck card wrote nothing
  machine readable. True at `a60233b`.
- Evidence at head `529c0f8` — `client/replay_broadcast.html:556-559`:
  ```js
  function setReplayError(message) {
    document.documentElement.setAttribute("data-replay-error",
      String(message || "replay failed"));
  }
  ```
  called from both funnels: `showError` (`:562` `setReplayError(\`${prefix}: ...\`)`) and
  `showFailCard` (`:572` `setReplayError([title, ...lines].join(" — "))`), and cleared on
  recovery (`:645` `removeAttribute("data-replay-error")` inside `clearFailCard`).
  `tests/test_viewer.py:167-190`
  (`test_the_pages_own_failure_paths_set_data_replay_error`) asserts the writer, both
  callers, the boot-catch / `noDataCard` / `armStuckTimer` / `startCore` / window-listener
  routing, and the clear. CI run **32683809005** (headSha `529c0f8…`, conclusion
  `success`): that test `PASSED` in the `test` job (log timestamp 02:40:45) and again in
  `wasm-viewer` → "Viewer tests against the built bundle".
- Checklist item: 13(ii) — now satisfied. Not standing.

### B2 — "no test asserts the event-fold reproduces the recorded per-hole state" → REFUTED (fixed at head)
- Reviewer's claim (checklist 2, correctness): the viewer derives from the fold
  (`client/replay_doc.js stateAt`) but no test compared the fold of `events[]` with the
  recorded `holes[]`. True at `a60233b`.
- Evidence at head — commit `46eecce` adds to `tests/test_replay.py` (verified in the tree
  and in `git log -p --since="2026-08-24T00:39:06Z" -- tests/`):
  - `test_folding_the_events_reproduces_the_recorded_per_hole_state`
    (`tests/test_replay.py:220-282`): folds every beat of a real episode with a line-for-line
    transcription of `stateAt()` and asserts, **at every beat**, that accumulated shots are a
    field-for-field prefix of `holes[k].seats[i].tests`
    (`idx/name/args/expect/why/legal/legal_reason/outcome/observed`), that `par`/`fallback`
    are unseen-or-equal, that `cumulative` stays the previous hole's until the `hole_score`
    beat, and that each hole is re-derived exactly at its `hole_score` beat, ending
    `done` with `cumulative == results["scores"] == holes[-1]["cumulative"]`.
  - `test_the_viewers_own_fold_agrees_with_the_recorded_holes`
    (`tests/test_replay.py:285-337`): runs the page's actual `client/replay_doc.js`
    `stateAt()` under node over the same episode and compares state at every hole boundary
    against `holes[]`.
  - Both `PASSED` (not skipped — node 22 is set up in the `test` job) in CI run 32683809005,
    log timestamps 02:40:40.
- Checklist item: 2 — "a test asserts it" is now met. The chrome derivation path
  (`replay_broadcast.html:712` `state() { return RD.stateAt(replay, beatIdx); }`) is the
  re-derivation the display uses, and it is now pinned to the record. Not standing.
  (The Nim `sceneAt` fold remains untested against `holes[]` — see non-blocking
  observations; item 2's test requirement is satisfied by the fold the viewer's readouts
  actually run.)

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | `gh run view 32683809005 --json headSha,conclusion` → `529c0f8…` / `success`; jobs `test`, `docker-smoke`, `wasm-viewer` all ✓. `git log -p --since="2026-08-24T00:39:06Z" -- tests/` shows only **added** tests/imports across `9a63d64`/`46eecce`/`529c0f8` (and `c6eb4e2` created the suite): no deleted assertion, no widened tolerance, no skip/xfail added, no test file removed. Prior run 32683696535 (`46eecce`) was `cancelled` by the concurrency group, not failed; its content is in the green head run. |
| 2 replay re-derivation + test | PASS | `tests/test_replay.py:220-337` (two fold tests, both PASSED in CI); display derives from `RD.stateAt` (`client/replay_broadcast.html:712`, readouts at `:815-816`, `:951-961`); the only `holes[]` reads on the page are static per-hole data no event carries in full (impl source, spec prompt, `par_total`). |
| 3 static viewer | PASS | `coworld_manifest_template.json:12-14` `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode `100755` (`git ls-files -s`), wired as the `coworld build` hook and gated in `coworld-release.yml:178-204` (`LIVENESS_MARKER` = static bundle). Viewer fetches only `?replay=`/`/replay-data` and relative assets (`tests/test_viewer.py:127-150`). `/client/replay` routes exist only inside `make_replay_app` (`server.py:732-784`), constructed solely when `COGAME_LOAD_REPLAY_URI` is set (`:793-808`) — byte-for-byte the starter's own replay-debug mode (`/workspace/starters/cogame-factorio/server/cogame_factorio/server.py:767-770`); the episode app (`server.py:337-344`) has no replay route and the manifest declares no pod viewer. |
| 4 both name spaces | PASS | Aliases only to policies: `contract.ALIASES`, `server.py:379-380`, `engine.py:595-598`; `tests/test_server.py:66` (welcome carries no real name), `tests/test_engine.py` (observation carries none). Viewer maps alias→name: `replay_broadcast.html:698-700` (`seatAlias`/`seatName`), chips render alias big + real name small (`:866-872`); both arrays in replay (`replay.py:78-79`) and results (`results_schema` `names`+`aliases`). CI scorebug readout shows both: `#1 BASIL PEDANT +1 #2 ASH LITERALIST -1`. |
| 5 degrade-never-hang | PASS | Connect: `asyncio.wait_for` (`server.py:230-237`) clamped by wall (`engine.py:258-262`); hole + retry deadlines `min`-clamped (`engine.py:363-364`, `:372-374`) and enforced with `wait_for` (`server.py:249`); sandbox per-call `setitimer` + per-batch `subprocess.run(timeout=…)` + kill semantics (`sandbox.py:117-124`); wall hard stop 700 s + 80 s reserve (`engine.py:222-233`); done send bounded 3 s (`server.py:55`, `:659`); LLM call bounded 32 s inside the 37 s policy deadline (`llm_player.py:49`, `client.py:109`, `:427`). Settle-and-score worst case ≈ 691 s < 720 s (60 % of 1200); `tests/test_manifest.py:96-110` pins the arithmetic; smoke episode `reason=complete`. The one `asyncio.Event().wait()` (`server.py:807`) is replay-serving mode, never an episode pod. |
| 6 num_agents | PASS | Manifest: `num_agents: 2` in `duel` (:480), `blitz` (:502), certification (:530), schema pins min=max=2 (:70-76). `tools/ci/docker_smoke.sh:106-151` enforces all four invariants (present / positive int / `len(certification.players)` / `len(game_config.players)`) with `SEAT-COUNT FAIL:` prefixes, and `SMOKE_SEATS=2` (:54) is the independent cross-check. `grep "SEAT-COUNT" ` over the head run's docker-smoke log (job 97305103020) → **0 matches**; log shows `smoke OK: seats=2 … reason=complete`. |
| 7 scripted baseline plays full episodes legally | PASS | `tests/test_e2e.py:36-53` (`reason == "complete"`, 3 holes, zero-sum, artifacts) and `:56-70` (real contest: both seats breach, audit bites, `fallbacks == [0,0]`); `tests/test_baselines.py` asserts every order bounded and legal for all 12 specs × both baselines (caps, arity, no duplicates, no sandbox timeout, every literalist shot passes the reference gate). The "grid harness" clause has no target: the baselines carry **no numeric parameters** — they are fixed per-spec data (`LITERAL_IMPL`/`NAIVE_IMPL`, `SAFE_TESTS`/`EDGE_TESTS`, `baseline.py:73-90`), and what plays tuning's role is `tests/test_specs.py:87-133` (the two impls diverge from the reference on different clauses; the pedant's edge shots include illegal ones), proven end-to-end by `test_the_match_is_a_real_contest_not_a_null_match`. Verified from the tree; nothing left unverifiable. |
| 8 LLM reply handling | PASS | Tolerant parse, three paths (`llm_player.py:120-157`: whole reply, balanced `{...}` span, fenced python+json), tested at `tests/test_players.py:87-121`. Retry-once: transport — SDK `with_options(max_retries=1)` (`llm_player.py:275-276`); wire-level parse/transport failure — the engine re-sends the identical observation once with `retry: true` then plays the literalist fallback (`engine.py:367-395`), recorded in `results.fallbacks`/`fallback_causes` and in the replay's `submission.fallback` (`tests/test_engine.py:59-73`). Player-internal unparseable reply → scripted substitution, never a noop (`llm_player.py:376-379`), recorded via the fixed stderr marker `llm_player: falling back (unparseable reply)` and the telemetry zip's `harness_fallback` events for raise/overrun (`client.py:251-263`). Advisory residue noted below (sidecar transport has no policy-level retry; player-internal fallbacks are not in results.json) — neither makes a call unbounded or invisible. |
| 9 rune-safe truncation | PASS | `clean_text` (`engine.py:57-67`): surrogatepass→replace, control strip, `str`-slice cap (code points by construction); `tests/test_submission.py:72-98` (4-byte emoji exactly on each cap, strict UTF-8 round trip; lone surrogate → U+FFFD); `tests/test_replay.py:37-80` (whole replay from hostile strings, `json.loads(blob.decode("utf-8"))` with no error handler). The last gap (`broken_reason`) was closed at head (`529c0f8`, `engine.py:646-648` + `test_the_broken_reason_is_sanitised_like_every_other_replay_string`, PASSED in CI). |
| 10 manifest validates | PASS | `game.docs` has the required shape — `readme` + `pages[{id,title,content}]` (`coworld_manifest_template.json:393-416`) — with `"type":"uri"`, which the platform's own upload contract admits: coworld 0.1.42 `types.py:231` `CoworldDoc = Annotated[CoworldTextDoc | CoworldUriDoc, Field(discriminator="type")]`. `game.protocols` carries both `player` and `global` (`:383-392`). `tests/test_manifest.py:162-169` runs `coworld.manifest.validate_upload_manifest` on the substituted manifest (coworld==0.1.42 pinned in `uv.lock`, so it runs in CI, not skipped) and `:172-180` validates every variant + the fixture against `config_schema`. |
| 11 viewer legible at 360 px | PASS | `.plate-name{flex:1 1 auto; min-width:3.2em}` (`client/replay_broadcast.html:416`), applied to the chip name (`"nm plate-name"`, `:849`); labels hidden under 640 px (`@media (max-width: 640px){ .ro .k, .wallsub, .scrub-key, #stepro .who, .seatchip .rk, .seatchip .sub{display:none} … }`, `:423-427`); right plaque collapses under 720 px (`:422`). `tests/test_viewer.py:321-330` pins the exact strings. |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:153) → Certify (:167) → Upload policies (:206, "BEFORE upload-coworld") → Upload Coworld (:304) → Put secret (:342, "AFTER upload-coworld"). All three workflows present; `tools/ci/docker_smoke.sh` mode 100755; `tools/ci/policies.json` = 4 policies, 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 (`cogolf-sniper`, the second `PLAYER_PROMPT`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`policies.json:14`). Placeholder gate run by me at head: `grep -n '<slug>\|<IMAGE>\|<SEATS>' …` over the five files → no matches, exit 0 path taken. In ci.yml the smoke runs against `${IMAGE}:ci` built in the same job (`ci.yml:80-89`) and `wasm-viewer` `needs: docker-smoke` and builds its own bundle. |
| 13 viewer executes | PASS | (i) `wasm-viewer` green at head run 32683809005 incl. "Load the bundle in a real browser" (job 97305364094): `{"loaded":true,"ms":303,…,"feed_lines":4}` and `soak: 12s of playback kept advancing ("beat 1 / 49" -> "beat 14 / 49" -> "beat 17 / 49")` against the replay docker-smoke produced (`needs: docker-smoke`, `ci.yml:116`); no `continue-on-error` anywhere in ci.yml. (ii) `data-replay-loaded` set in the `firstFrame` branch (`static_replay.js:145-147`) and `data-replay-error` set from both the worker shell (`static_replay.js:33`) and the page's own paths (`replay_broadcast.html:556-572`, head fix). (iii) `config.nims` diffs against the starter's only in the output name and `_factorio_*`→`_cogolf_*` exports — no MODULARIZE/EXPORT_NAME — and the worker bootstrap is `Module.onRuntimeInitialized` + `importScripts` (`static_replay_worker.js:265`), the matched non-modularized pair; `tests/test_viewer.py:193-208` guards it. |
| 14 chrome is the starter's | PASS | (i) `diff client/chrome_common.js /workspace/starters/cogame-factorio/client/chrome_common.js` → **identical**; `broadcast_core.js` identical too. (ii) `replay_broadcast.html` is 1408 lines / 103,401 B vs the starter's 1528 / 111,234 — the starter's page with the note's listed removals and an appended block under the banner comment `cogolf additions to the inherited cogame-factorio chrome` (`:340-342`, `<style id="cogolf-css">` `:343`); the CSS above the banner diffs only by the listed removals (`#maptools`, `#charmark`, `#legend`, the starter's dead `.beat-marker.error/.noop/.dead` rules). (iii) `relayout()` measures `#transport` and sets `--band` + `--hudscale` on `document.documentElement` (`:1306-1311`), rerun from a `ResizeObserver` on `#transport` (`:1314`); every overlay (`#scroll`, `#feed`, `#tooltip`, `#status`, `#loader`, `#failcard`, `#endcard`) lives inside `#stage` (grid row 3) — `grep position:fixed` → nothing; `#endcard{inset:0 0 var(--band) 0}` (`:409`, bottom = `var(--band)`, shown with the starter's `#endcard.on` rule) and `selectBeat` (`:1199-1203`) calls `hideEndCard()` on every seek off the final beat, with every input path (buttons `:1224-1228`, keys `:1246-1251`, scrub drag via `ctx.seek`, beat buttons `:795`) routing through it; scrubber beats are labelled `<button>`s with `title`/`aria-label`/click-seek (`:770-800`) and CSS for all five emitted kinds (`.beat-marker.hole/.breach/.illegal/.fallback/.killer`, `:401-406`) matching `replay_doc.js markerKind`. (iv) Fixed 40×22 arena: no `#viewpanel`, no zoom bar, no minimap — removed, not hidden (`grep viewpanel|minimap|setZoom|panTo` → comments only; `tests/test_viewer.py:264-276`). |
| simultaneous batch | PASS | One parallel batch per hole: both payloads built first, then `asyncio.gather` over per-seat sends (`engine.py:359-419`); LLM calls happen inside each player container concurrently. `tests/test_engine.py:44-56` asserts both observations go out within 0.2 s while a seat thinks for 0.3 s. Not sequential. |

## Fixer report audit

(Read only after my own pass and after refuting the review.)

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed in `9a63d64` (`setReplayError` from both funnels, cleared on recovery, new test) | `replay_broadcast.html:556-572,645` + `tests/test_viewer.py:167-190`; test PASSED in head CI (both jobs) | yes |
| B2 | fixed in `46eecce` (two fold tests, bite verified) | both tests in tree, both PASSED (not skipped) in head CI `test` job at 02:40:40; the Python fold matches `stateAt` and the node test runs the page's own code | yes |
| N7 | fixed in `529c0f8` (one line + test) | `engine.py:646-648` `clean_text(broken[slot], MAX_BROKEN_REASON_CHARS)`; test PASSED in head CI | yes |
| N1 | deferred (recorded on stderr; countable change = four-surface protocol change) | stderr markers exist (`llm_player.py:363,371,378`); telemetry counts harness fallbacks only; results.json cannot count LLM-internal fallbacks — accurately described | yes |
| N2 | NEEDS-DESIGN (sidecar transport has no policy-level retry) | `_BedrockHttpClient.with_options` returns self (`llm_player.py:189-190`), single `urlopen` (`:204`); engine-level retry exists and is tested; matches design.md:253/281-282 | yes |
| N3 | refuted as blocking (replay-mode only; starter-identical) | routes only in `make_replay_app`, gated on `COGAME_LOAD_REPLAY_URI`; byte-comparable block exists in the starter's own server.py:767-770; episode app has no replay route | yes |
| N4 | refuted (`uri` accepted by the platform validator) | coworld 0.1.42 `types.py:231` discriminated union `text\|uri`; `validate_upload_manifest` passes in CI | yes |
| N5, N6, N8, N9, N10 | not fixed, with reasoning | each traces to real code; none touches a checklist item (N6: settle-and-score ≤ ~691 s < 720 s stands up to my own re-trace; the 20 s grace is process lifetime, after done + artifacts) | yes |

No disposition in the fixer's table misstates the tree; the claimed per-test CI evidence checked out against the raw job logs.

## Non-blocking observations (mine, advisory)

- **Item 8 residue** (also the reviewer's N1/N2): on the hosted sidecar transport
  (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME`/`AWS_BEARER_TOKEN_BEDROCK`), a transport failure is
  not retried at the policy level before the scripted substitution
  (`llm_player.py:189-213`), and an LLM-internal fallback is countable only from pod
  stderr/telemetry, not from `results.json`. The bound and the visibility exist; the
  wire-level retry-once + recorded-fallback path is the engine's. Worth a design decision in
  a later round, not blocking here.
- **The Nim fold** (`replay-viewer/cogolf_replay.nim` `sceneAt`) is a third implementation
  of the event reduction and is compared to nothing; the JS fold that drives every chrome
  readout is now pinned. Settling it needs a scene-state export the renderer does not have.
- `welcome.episode.seed` + the published draw formula lets a seat precompute later specs
  (reviewer's N5). Symmetric, reference/par/ambiguity still hidden, mandated by the note's
  t=0-disclosure rule; the note contradicts itself and no checklist item is touched.
- `replay.config.seed` echoes the unresolved config value; the resolved seed is at
  `doc.seed` and `doc.result.seed`, which is what the viewer validates and reads.

BLOCKING: 0
