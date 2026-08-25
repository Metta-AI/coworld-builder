blocking: 1

# r1 verdict — collab-cooking
Head: `a5ec2c8602856d21ad8ec3e4f70af7c6fab82ede` (main)   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes
CI at head: run **32816344271**, conclusion **success**, all three jobs green (`test` 200 passed / 1 skipped, `docker-smoke`, `wasm-viewer` including `Load the bundle in a real browser`). Verified with `gh run view`, not accepted from the fixer.

The review was written against `6b081b1`; the fixer pushed ten commits since. I verified every
disposition at the current head, then ran my own checklist pass. One blocking finding stands — mine,
not the reviewer's.

---

## Standing blocking findings

### B1 — the say band cannot hold a full-cap `say`: the DOM band is not sized from the 120-rune cap   (source: judge)
- Where: `client/parts/game.css:94-106` (`#saybar .say-chip`), `client/parts/game.js:95-106` (`ccSayBar` renders the full say text, no truncation, no title attribute)
- Verified at head:
  ```css
  #saybar .say-chip {
    flex: 1 1 0;
    font-size: calc(8.5 * var(--u));
    line-height: calc(11 * var(--u));
    max-height: calc(22 * var(--u));     /* exactly 2 lines */
    overflow: hidden;                    /* excess is clipped invisible */
  ```
  The comment above it (`game.css:81`: "The say band is sized from the 120-rune cap") is the only
  occurrence of "120" in the file — nothing in the sizing derives from the cap. The arithmetic:
  four chips share the board width (`flex: 1 1 0`, gap `5u`, bar padding `10u`), so a chip is
  ≈ 181 u wide at every viewport where `--hudscale` tracks board width (the clamp band,
  360 px–1216 px — `game.js:349`, `scale = clamp(boardW/760, 0.5, 1.6)`). At `font-size 8.5u`
  that is ≈ 40 characters per line; two lines ≈ 80 characters. `SAY_RUNES = 120`
  (`plans.py:28`), so a full-cap remark — the exact string `tests/test_replay_parse.py` proves
  survives the server end-to-end — loses its last ~40 runes to `overflow: hidden` at every
  realistic width, including the 360 px featured-match iframe the design names as a target.
  This is the cogchemists failure class in DOM form: LLM-authored text partially invisible while
  every gate is green, and — as checklist 15 itself predicts — no CI gate can catch it, because
  the CI replay carries zero `say` lines (`results.llm_requests: 0` in the head smoke artifact)
  and `canvas_text` is legitimately 0 (model text is DOM-only, verified below).
- Checklist item: **15** (*Every drawn string fits its frame*) — the DOM branch: "if model text is
  DOM-only, check the DOM band reservation (say band sized from the cap) instead"; and its ellipsis
  rule: a shortened **remark** means "the box is too small — widen the band, do not shorten the
  text". The band here is sized by eye (2-line clip), not from the cap measured in its font.
- What settles it: size the chip's max-height (or the band) from the 120-rune cap measured in the
  chip's font at minimum chip width (≈ 3 lines), or wrap/expand instead of clipping — plus a check
  (unit test on the CSS, or a worst-case DOM fixture with four full-cap says) that pins it.

- [legibility] client/parts/game.css:99 `#saybar .say-chip` caps at 2 lines (`max-height: calc(22*var(--u))`, `overflow: hidden`) but a 120-rune say needs ~3 lines at every width in the hudscale clamp band — the last ~third of a full-cap remark is invisible, and no gate can see it (CI replays carry no LLM text)

---

## Reviewer findings, disposition at head

None of the reviewer's findings is refuted as wrong-when-written. The three blocking ones were true
at `6b081b1` and are **fixed at head** — fixed, not refuted:

### O1 — manifest rejected by `coworld build` → FIXED at `f4c74bd`
- Evidence at head: `coworld_manifest_template.json` has `game.owner`, `game.replay_viewer =
  {"bundle": "static-replay-viewer"}`, no top-level `version`/`replay_viewer`, no
  `game.display_name` (verified by parsing the committed file). CI's own gate ran the pinned
  loader: test job log line "manifest OK: … game.replay_viewer.bundle=static-replay-viewer,
  game.owner=daveey@softmax.com" (run 32816344271, step *Validate the manifest with the pinned
  coworld's own loader*, `coworld==0.1.42` — the release pin).
- Test re-pin audit (item 1 caveat): `tests/test_manifest.py` previously asserted the WRONG shape
  (`MANIFEST["replay_viewer"]` at top level); the new assertions pin the correct shape plus more
  (no top-level `replay_viewer`, no `game.display_name`, owner present, CI pin == release pin).
  **Stronger, not weaker** — this is the sanctioned exception class, exercised legitimately.

### O2 — no frame-by-frame re-derivation test → FIXED at `9ddcbce`
- Evidence at head: `tests/test_rederivation.py` feeds the replay's recorded actions through a
  **fresh `Simulator`** seeded from the replay's own bytes and compares every tick's `c`, `st`
  (including the omit-when-unchanged rule), `sc`, `ev` (in order) and the cumulative `heat`
  (`test_rederivation.py:118-147`). Two tamper tests prove the comparison is load-bearing
  (`:150-170`); a vacuity test pins 240 ticks, >100 event-bearing ticks, >2 carried item kinds.
  All five PASSED in run 32816344271 (test job log lines 501-505).
- The viewer half: the wasm module draws the recorded `c`/`st` arrays — the design note's explicit
  §Viewer/Pipeline decision (the sim is Python on a C++ core; a Nim sim would be a second source of
  truth). The test now proves those recorded frames are **exactly** what re-derivation through the
  sim produces, frame by frame, so the display derives from data proven identical to the
  re-derivation and there is no unverified parallel channel. I rule item 2 satisfied.

### O3 — pause branch skipped the deadline guard → FIXED at `1b7c075`
- Evidence at head: `live_episode.py:415-423` — the pause branch now evaluates
  `self._deadline_reached()` and settles `"deadline"` before sleeping;
  `tests/test_episode.py::test_a_paused_episode_still_settles_at_the_deadline` PASSED in CI (log
  line 395) with a 20 s `run_timeout` that turns a regression into a failure, not a hang.

### Non-blocking findings the fixer also fixed — each verified at head
- **O4** heat keying → FIXED at `59c50aa`: `replay.py:323` keys `heat` by the tile the event
  carries; `tests/test_replay_parse.py::test_heat_is_the_cumulative_blocked_move_count` now
  compares tile-for-tile, not totals.
- **O5** ticket `expires` → FIXED at `2719860`: `replay.py:432-439` emits `expires` from
  `build_ticket_specs` (the engine's own schedule); head CI browser log reads
  `TICK 242 OF 480 3 ORDERS LIVE · 1 EXPIRING` — the readout O5 said could never fire, firing.
- **O6** two seats never connected in the smoke → FIXED at `cccdf92`: head docker-smoke log shows
  `waiting for /healthz on the game container (up to 120s)` → `game is serving /healthz; starting
  4 player containers` → `every player container exited 0` → `smoke OK: seats=4 … reason=complete`;
  the head `smoke-replay` artifact's `results.json` (downloaded, quoted): `"disconnected":
  [false,false,false,false]`, `"seat_kinds": ["prompt","scripted:brigade","scripted:passer",
  "scripted:courier"]`, `"cross_play": true`, `"dishes": 11`. `player.py:136-156`
  (`connect_with_retry`, bounded 60 s) + `tests/test_player_client.py` pin both halves of the dial.
- **O7** DIFF_ORDER → FIXED at `2af3921`: `replay.py:338-339` stable-sorts into the declared order;
  `tests/test_replay_parse.py::test_every_tick_carries_its_events_in_the_declared_order` asserts
  order and slot-ascending ties on a real episode.
- **O8** secret namespace → FIXED at `9ee8d7d`: `coworld-release.yml:342-380` reads `game.name`
  out of the manifest, asserts `ANTHROPIC_API_KEY_URI` is in that namespace, and puts/lists the
  secret under it. `$SLUG` no longer reaches `secret put`.
- **O14** stale annotation → FIXED at `80a624e`: `obs_parser.py:40` returns
  `KitchenObservationState`, the class the file defines.
- **O18** fuzz count → FIXED at `a5ec2c8`: `tests/test_baselines.py:158` asserts `fuzzed == 400`.

### Reviewer findings left unfixed — my rulings
- **O9 (page provenance — judge's call, explicitly).** Ruled **not blocking**. I regenerated the
  committed `client/replay_broadcast.html` from the mounted starter with the committed generator
  (`python3 tools/build_broadcast_page.py /workspace/starters/coworld-ctf`) — **byte-identical**.
  The CSS above the banner and the body markup are ctf's verbatim minus the note's listed removals;
  `chrome_common.js` and `broadcast_core.js` diff empty against the starter. The 2158-vs-4165 line
  difference is exactly ctf's discarded inline game script (ctf-specific FPV/POV/wire logic),
  replaced by the 370-line game block — and item 14's concrete transport rules all hold at head
  (verified individually below). The gridlock failure mode (a from-scratch lookalike) is excluded
  by the byte-level regeneration; the lantern failure mode (split bootstrap) is excluded by the
  matched non-MODULARIZE pair plus the executed browser smoke (`loaded: true`).
- **O10 (13×13 window vs the note's 11×11)** — real, note-vs-code only; visibility parity between
  prompt and scripted seats holds (both read the same window). Advisory.
- **O11 (cog PNGs vs "no PNGs")** — real, note-vs-code only; not on the checklist. Advisory.
- **O12 (heat counts station bumps)** — by construction of the note's own rule ("using a station
  is a failed move"). Advisory.
- **O13 (executor looser than the note in three places)** — verified as described; behaviour
  changes to frozen baselines, not checklist items. Advisory.
- **O15 (player-side fallback hard-coded `brigade`)** — verified at `player.py:162`; diverges only
  under a non-default `fallback_scripted`, which nothing ships. Advisory.
- **O16 (straggler worker across batch turns)** — verified; nothing unbounded follows
  (`_plan_boundary` gates on `batch.finished`, true at the deadline). The one-parallel-batch
  addendum is satisfied (below). Advisory.
- **O17 (canvas_text total 0; no fixture renders a `say`)** — the reviewer's facts are correct and
  the categorisation was left to me: see **B1**. The canvas half is clean (pin verified); the DOM
  band half fails.

## Refuted
None. Every reviewer finding reproduced at the commit it was written against; ten are fixed at
head, the rest stand as advisory exactly as filed. (The fixer's O17 claim — "the say band is
already … sized from the 120-rune cap" — is the one disposition my audit contradicts; see B1.)

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 32816344271 success on main at head (test/docker-smoke/wasm-viewer all green). `git log -p -- tests/`: suite written once (`211be3a`), re-added byte-identical (`git diff 211be3a 1f8902f -- tests/` empty), every later change an added test/assertion. The one re-pin (`test_manifest.py`, r1-O1) replaced a wrong-shape assertion with a stronger one — the sanctioned exception. The one `pytest.skip` (`test_viewer_contract.py:197`) is a mount-presence guard from the original commit; the guarded property (chrome byte-identity) I verified directly at head. No deleted assertion, no widened tolerance. |
| 2 replay re-derivation | PASS | `tests/test_rederivation.py:118-147` frame-by-frame vs a fresh `Simulator`; tamper tests `:150-170`; CI PASSED. Viewer draws the recording the test proves identical to the re-derivation (design §Viewer/Pipeline pin). |
| 3 static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer={"bundle":"static-replay-viewer"}` (loader-validated in CI); `tools/build_replay_viewer.sh` mode 100755 (`git ls-files -s`); worker's only network call is `fetch(message.replayUrl)` (`static_replay_worker.js:113`); no `/client/replay`/`WS /replay`/`create_replay_app` anywhere (`server.py` routes; `tests/test_manifest.py:138` asserts absence). |
| 4 both name spaces | PASS | wire `observation` carries no names (`live_episode.py:904-914`); aliases by seeded permutation (`:202-211`); prompts/plans/radio alias-only; real names only in `seats[].name`, `results.names`, `/global`, `final`. Head CI scorebug renders both: `"Cog-B Cog One …"`. |
| 5 degrade-never-hang | PASS | roster wait bounded at process start +120 s AND the deadline guard (`live_episode.py:453-459`); registration grace 5 s (`:461-466`); action wait 0.30 s via `asyncio.wait_for` (`:474-486`); LLM per-call `urlopen(timeout)` (`llm.py:180`), batch deadline + non-blocking `poll` (`llm.py:225-249`); pause branch now guarded (`:415-423`, r1-O3); guard = 0.6×1200 = 720 s from `PROCESS_START` (`server.py:47`); worst case ≈ 325 s (arithmetic checked); cert fixture wall clock pinned < 50 s by a passing test (`test_episode.py:169-183`). |
| 6 num_agents everywhere | PASS | 4 in all eight variants + `certification.game_config` + `config_schema {min 4, max 4}` + `len(certification.players)=4` + `len(cert.game_config.players)=4` (parsed the committed manifest); `docker_smoke.sh:106-151` enforces all four invariants with `SEAT-COUNT FAIL:` before any container starts; `SMOKE_SEATS: "4"` in `ci.yml:109` cross-checked at `docker_smoke.sh:141-149`; `grep -c 'SEAT-COUNT FAIL'` over the head docker-smoke log = **0**. |
| 7 scripted baseline full episodes | PASS | `test_episode.py::test_a_complete_episode_writes_both_artifacts` — four scripted seats, `reason == "complete"`, dish count recomputed from `serve` events equals results; `test_baselines.py` — 4 baselines × 8 kitchens × 600 ticks, every action in `action_names`, one per seat per tick, `request_id == step-<t>`, no seat parked >60 ticks (connected kitchens). Parameters are the starter's shipped brain, frozen by design (§Out of scope 8); validated in fact by the head container smoke: 11 dishes, cross-play, all four policies seated. |
| 8 LLM reply handling | PASS | balanced-brace extraction tolerant of prose (`plans.py:119-151`); retry exactly once with the hint (`llm.py:304-329`); fallback recorded as `fallback` event + `results.fallbacks` (`live_episode.py:829-837`); pinned by `tests/test_llm.py` (2 calls then fallback; successful retry used; barrier-proven parallel batch; rate budget; disabled path = 0 requests). |
| 9 rune-safe truncation | PASS | `truncate_runes` code-point slice (`plans.py:53-62`) on say/note/prompt/names/feed/beats/error details; `ensure_ascii=False` + one `.encode("utf-8")` (`replay.py:520-522`); `test_replay_parse.py:106-119` — 180-rune all-multi-byte say truncated to exactly 120, strict `decode("utf-8")` with no handler; Nim side truncates on runes too (`collab_cooking_replay.nim`, `unicode.runes`). |
| 10 manifest validates | PASS | `game.docs.readme` inline text byte-identical to README (test + my parse); 4 `pages[]` each `{id,title,content:{type:"text",value}}`; `game.protocols` carries both `player` and `global` as objects; the pinned coworld 0.1.42 loader accepts the template in CI (run 32816344271). |
| 11 legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` (`game.css:1612-1621` in the built page); `@media (max-width: 640px)` hides `.plate-policy`/`.plate-job`/`#feed` (`game.css:181-184`); asserted by `test_viewer_contract.py::test_plate_css_survives_the_360px_featured_match_iframe`. |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build (l.153) → Certify (l.167) → Upload the policies (l.206, comment pins BEFORE upload-coworld) → Upload the Coworld (l.304) → Put the Coworld secret (l.342, reads `game.name`); certify runs on the manifest built in the same job. Three workflows present; `docker_smoke.sh` 100755; `policies.json` = 2×`PLAYER_PROMPT` + 2×`PLAYER_SCRIPTED`, champion #2 carries `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; placeholder grep over the five named files: **no match** (ran it). |
| 13 viewer executes | PASS | run 32816344271 `wasm-viewer` green **including** `Load the bundle in a real browser`: `{"loaded":true,"ms":327,…}`, 10 s soak advancing `2/480 → 194/480 → 242/480`, three distinct scrub clocks; `needs: docker-smoke` (`ci.yml:140`); no `continue-on-error` in any workflow (grep). Markers: `data-replay-loaded` set in the shell's `'loaded'` branch with the bridge `ready` inside it, `data-replay-error` in `showFailure` (`static_replay.js:29,152-158`). Link flags and bootstrap the SAME starter: `config.nims` diff vs ctf = symbol rename only, **no MODULARIZE/EXPORT_NAME**; worker bootstraps `onRuntimeInitialized`; cross-pinned by `test_viewer_contract.py:146-161`. |
| 14 chrome is the starter's | PASS | `chrome_common.js` and `broadcast_core.js` **byte-identical** to `/workspace/starters/coworld-ctf` (diff empty, ran it); committed page **regenerates byte-identically** from the starter via the committed generator (ran it); CSS above the banner is ctf's head verbatim; removals are the note's list (all 26 removed ids absent, all 19 chrome ids present — test + my grep). Transport rules verified in the page: `relayout()` writes `--band`/`--hudscale` on `document.documentElement` only (`game.js:328-368`); `#endcard` keeps `bottom: var(--band,0px)` (page l.1047), shown with `#endcard.on` (l.1058, `game.js:222`); every playhead-moving control routes through `ccSeek`, which removes `.on` first (`game.js:60-65`; scrub, beats, back/fwd/restart, keyboard); beats are labelled `<button>`s with CSS for all six emitted kinds (`game.css:203-208`, cross-checked against the Nim emitter by test). `#viewpanel`/zoom/minimap: markup and ids removed, `attachMinimap` never called from the page (grep). Residue: the starter head's dead CSS rules for the removed elements remain (e.g. `#viewpanel` l.713, `#zoom-slider` l.793) — dead rules on absent markup render nothing; noted below, not blocking. |
| 15 every drawn string fits | **FAIL — B1** | Canvas half PASS: design pins no canvas text; verified — no `fillText/strokeText/measureText` in `broadcast_core.js`/`static_replay.js`/`game.js` (grep), board glyphs are baked sprite pixels (`collab_cooking_replay.nim:273`); CI: `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` with the flag ON in `ci.yml:247`. DOM half FAIL: the say band is not sized from the 120-rune cap — `#saybar .say-chip` clips at 2 lines ≈ 80 chars (`game.css:97-100`); see B1. |
| addendum: one parallel batch | PASS | `start_turn` submits every prompt seat to the pool before returning (`llm.py:288-293`); tick loop never blocks on it (`_plan_boundary`/`poll`); concurrency proven by a 4-way `threading.Barrier` in `tests/test_llm.py:137-148`. |

---

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| O1 | fixed `f4c74bd`; loader OK in CI | manifest shape at head + CI log "manifest OK: … game.owner=daveey@softmax.com"; re-pinned test is stronger | yes |
| O2 | fixed `9ddcbce`; frame-by-frame + tamper tests | read the test; all 5 PASSED in CI log | yes |
| O3 | fixed `1b7c075`; paused episode settles | guard in pause branch at head; test PASSED in CI | yes |
| O4 | fixed `59c50aa`; tile-for-tile | `replay.py:323` + per-tile assertion | yes |
| O5 | fixed `2719860`; EXPIRING fires | `expires` emitted; head browser log shows `· 1 EXPIRING` | yes |
| O6 | fixed `cccdf92`; all four seats connect | head log healthz gate + artifact `disconnected:[false×4]`, `cross_play:true`, `dishes:11` | yes |
| O7 | fixed `2af3921`; stable sort | `replay.py:338-339` + order test | yes |
| O8 | fixed `9ee8d7d`; secret under `game.name` | release step reads manifest, asserts namespace | yes |
| O14 | fixed `80a624e` | `obs_parser.py:40` names the real class | yes |
| O18 | fixed `a5ec2c8`; 400 fuzzed | `test_baselines.py:158` asserts `fuzzed == 400` | yes |
| O9/O10/O11/O12/O13/O15/O16 | not fixed, reasons given | reasons check out; none is a checklist falsification | yes |
| O17 | "the say band is already … sized from the 120-rune cap" — no change | **contradicted**: nothing in the sizing derives from the cap; a full-cap say is clipped to ~2/3 (B1) | **no** |
| "1 skipped is the pre-existing mount guard" | — | confirmed: `test_viewer_contract.py:197`, original commit; property verified directly at head | yes |

## Non-blocking observations
- Dead CSS for the removed `#viewpanel`/`#zoom-*`/`#minimap`/`#fpv`/`#lockerroom` elements survives
  in the inherited head (the generator removes markup, not head CSS). Harmless on absent markup;
  removing it would break the byte-level provenance check against the starter head, so I do not
  ask for it. (item 14 zoom bullet, letter vs. substance — substance holds: nothing is hidden, the
  panel does not exist and is not wired.)
- `__pycache__/` and `.pytest_cache/` are committed (e.g. `src/collab_cooking/coworld/__pycache__/`).
  Hygiene only.
- `static_replay.js`/`static_replay_worker.js` also drop ctf's `mismatchTick` channel — an
  undeclared (but sensible: no sim in wasm) third delta beyond the two the design note lists.
- The head viewer smoke's 0 % scrub probe read `TICK 242` (the pre-scrub clock), not ~0; the
  harness's own three-distinct-clocks criterion still held. Harness quirk, no action.
- No test asserts an all-scripted episode serves **> 0** dishes (the head container smoke did:
  11). Worth a one-line assertion when the say band is fixed.

- [legibility] client/parts/game.css:99 `#saybar .say-chip` caps at 2 lines (~80 chars) with `overflow: hidden` while `SAY_RUNES = 120` — a full-cap LLM remark is clipped invisible at every realistic width; band not sized from the cap (checklist 15, DOM branch)

BLOCKING: 1
