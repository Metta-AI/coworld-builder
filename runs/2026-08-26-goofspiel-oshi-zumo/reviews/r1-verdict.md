blocking: 0

# r1 verdict — goofspiel-oshi-zumo

Head: `af5e9bbc3af17c6433b9b3453381332fac51aecb` (main; CI run **33020196047**, conclusion
**success**, jobs `test` 98348430231 / `docker-smoke` 98348430385 / `wasm-viewer` 98348637339 all
green).  Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
simultaneous-batch rule).  Independent read written before reading fixes: **yes** — I read the
full tree at the head sha, diffed the chrome against `/workspace/starters/cogame-babel@d55d999`,
ran the placeholder gate, read `git log -p -- tests/`, and pulled the CI logs *before* opening
`r1-review.md`, and opened `r1-fixes.md` only after disposing of every finding myself.

The review was written at `1a29c60`; the head carries nine later commits. Verification below is
at the **current head**, so several findings that were true when written are now refuted-as-fixed.

## Standing blocking findings

None.

## Refuted / resolved reviewer findings (F1–F11)

### F1 — full-cap `say` ellipsized at narrow widths → FIXED AT HEAD (was real at 1a29c60)
- Evidence: `client/renderer.js:349-381` at head — `sayBand()` reserves
  `max(2, ceil(MAX_SAY * wide / usable) + 1)` lines, measuring the full-width rune `永`
  (`WIDE_RUNE`, `:34`) in the band's own font at the current `--hudscale` (`:100-105`), capped at
  55 % of the panel; `splitToFit` (`:301-315`) breaks a space-free 80-rune run on rune boundaries
  instead of cutting it. Arithmetic at 360 px / 4 seats: contentW ≈ 80 px, usable 72 px, font at
  the 7 px floor → 8 lines reserved ≈ 576 px of run vs 560 px needed — it fits.
- Gate evidence: the renderer fixture (`tools/ci/renderer_fixture.html:227-305`) now records every
  `fillText` and **throws** if any remark fragment carries an ellipsis, if a remark that reached
  the canvas is not reassembled in full rune-for-rune, or if no full-cap remark reached the canvas
  at all; it drives both modes at 360/640/1280 px, including an 80-rune no-space Japanese run, and
  asserts its own strings are still 80 runes (`:354-361`). CI head run, step *Renderer text
  fixture*: `{"loaded":true,…}`, `canvas text: 1449 drawn, 0 never inside … 138 ellipsized` — the
  138 are nameplate `clampName` cuts, which the fixture would not have passed if any were remarks.

### F2 — score pool is "awarded so far", not the note's literal 91 → REFUTED as blocking (correct code, note-wording gap)
- Evidence: `src/gozu/sim.nim:204-209` (`awardedPool`), `:232-240` (`score`). On a complete
  episode `roundsPlayed == 13` so pool = 91 and the formula is exactly `(points−22.75)/68.25`;
  on a `deadline` stop a fixed 91 would break the zero-sum sum the note itself requires
  (design.md:154 "the array sums to 0", design.md:190-193 "fully scored at the stop … from prizes
  already awarded"). Pinned by `tests/test_sim.nim:279-305` and the 200-seed zero-sum sweep
  (`:250-277`). Documented in the shipped rules page. No checklist item is falsified; the
  reviewer claimed none.

### F3 — a/j/q/k prose prefix read as a card → FIXED AT HEAD
- Evidence: `src/gozu/llm.nim:452-468` — `rankLetter` strips quote/punctuation chars and returns a
  rank only when the remaining token is exactly one character; prose falls through to the numeric
  scan whose raise triggers the retry-with-legal-set and then the fallback. `tests/test_llm.nim`
  (new) pins `"a bid of 11"`, `"just 12"`, `"queen or king, whichever is left"`,
  `"keeping the 13 back"` all raise, and the accepted forms still parse. Green in `test` (debug
  and `-d:release`) at the head run.

### F4 — no test asserted `results.reason == "complete"` for an all-scripted episode → FIXED AT HEAD
- Evidence: `tests/test_bot.nim:62-66` — `playAll` now asserts
  `result.resultsJson()["reason"].getStr() == "complete"`, so every baseline-driven episode in
  assertions 12/14/15 (200 seeds × both modes × both baselines, plus the certification fixture)
  asserts it against the same object the platform reads. Checklist item 7, first half, satisfied.

### F5 — assertion 7 titled "both baselines" but drove synthetic bidders → FIXED AT HEAD (retitle, no weakening)
- Evidence: `tests/test_sim.nim:225-248` — retitled "for any legal bidder" with a comment pointing
  at `tests/test_bot.nim` assertion 12, which runs the real `scriptedBid` for both baselines over
  200 seeds and asserts `roundsPlayed <= 20`. `git log -p` of `af5e9bb` shows only the title and a
  comment changed; every assertion is intact. Not a weakening.

### F6 — no grid-tuning harness → FIXED AT HEAD
- Evidence: `scripts/tune_baselines.nim` (new, commit `c1208a7`) sweeps the three free constants
  (hoard's cheap/dear split, match's oshi spend rate `k`, hoard's desperation divisor `f`) over a
  grid against the shipped opponents and a random bidder, 200 seeds per point, and asserts at the
  shipped grid point that every bid equals `scriptedBid`'s; `docs/baseline-tuning.md` records the
  table with every shipped constant at its curve's peak. Checklist item 7's last sentence
  satisfied.

### F7 — game thread unguarded; a raised `writeArtifact` would leave the server up with no `quit` → FIXED AT HEAD
- Evidence: `src/gozu/server.nim:366-379` — `runGame` is now a `try/except CatchableError` wrapper
  around `playEpisode` that logs and `quit(1)`s, so the reachable artifact-POST `IOError`
  (`:150-151`) exits the container instead of hanging it until the platform timeout. Category
  `hang` closed.

### F8 — `checkReveal` skipped the points comparison on a length mismatch → FIXED AT HEAD
- Evidence: `src/gozu/sim.nim:709-712` — a length mismatch now raises
  ("points array does not match the re-derivation") instead of guarding the element loop;
  `tests/test_replay.nim:166-181` truncates a real reveal's `points` from 4 to 3 and asserts
  `replayMatch` raises. Item 2's "asserted by a test" holds.

### F9 — cert fixture policy names drawn from the alias pool → REFUTED as a finding
- Evidence: design.md:857-864 prescribes exactly `Sprocket/Gizmo/Ratchet/Widget` as the fixture's
  player names; the manifest follows the note. The two name spaces themselves work (CI
  `viewer-smoke` scorebug shows policy name + distinct alias per plate). Cosmetic confusion in one
  CI artifact, no checklist item falsified. Correctly left unchanged.

### F10 — say font scaled by canvas layout, not `--hudscale` → FIXED AT HEAD
- Evidence: `client/renderer.js:100-105` `hudScale()` reads the computed `--hudscale` off `:root`
  (the variable `chrome_common.js:493-500` `relayout()` sets); `computeLayout` carries it as
  `layout.hud` (`:129`) and `sayFontPx` applies it (`:349-351`). The band F1 sized measures in
  this same font, matching design.md:743-745.

### F11 — player receive loop was an untimed blocking read → FIXED AT HEAD
- Evidence: `src/gozu_player.nim:56-64` — the read now carries
  `timeout = max(60, COWORLD_TIMEOUT_SECONDS|1200) * 1000 + 120_000` ms; a timeout returns `none`
  and takes the same clean exit-0 path a closed socket takes. Item 5's "no blocking read" closed;
  docker-smoke at head still reports `all 4 player containers exited 0`.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1 CI green, no test loosened | PASS | `gh run list -w ci.yml --branch main`: run **33020196047**, head `af5e9bb`, conclusion `success`, 3/3 jobs green. `git log -p -- tests/`: five commits — `0819899` (adds 4 files), `8357bf1` (adds test_llm.nim), `f924c03` (adds an assertion), `1c12d06` (adds a test), `af5e9bb` (title + comment only). No deletion, no skip/xfail, no widened tolerance; F4/F8 hunks *add* assertions, F5 is a retitle. `NIM_TESTS` unset ⇒ all `tests/*.nim` run in debug **and** `-d:release` (log shows both passes, all `[OK]`). |
| 2 replay re-derivation, frame by frame, viewer uses it | PASS | `sim.nim:718-774` `replayMatch` replays bids through `applyBids`, **checks** recorded `prize`/`overbid`/`push` field-by-field and (post-F8) the points length, and applies a recorded `end` through the **same** `settle` (`:763-773`); `tests/test_replay.nim:103-135` asserts frame identity for all five reason/ending pairs incl. `deadline/wall-clock`; `:139-181` tampered prize/push/points raise. Viewer: `replay-viewer/gozu_replay.nim:47-49` builds `states[]` from `replayMatch`; server replay mode same (`server.nim:163-167`). |
| 3 static viewer | PASS | `coworld_manifest_template.json:16-18` `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, git mode **100755**, asserted executable and invoked by path in `ci.yml:236-260`; `static_replay.js` fetches only `?replay=<url>` and relative assets. The string `/client/replay` appears only as the game container's own live route (`server.nim:530`) and its prose description in `protocols.global` — no replay-viewer pod path. |
| 4 both name spaces | PASS | Prompts and `welcome`/`final` frames carry aliases only (`llm.nim:272-377`, `server.nim:447-455`, `:183-196`); `replayPayloadJson` carries `names` + `policyNames`; `chrome_common.js:105-133` maps alias→policy for non-baseline seats; CI `viewer-smoke` scorebug shows both (`Sprocket PISTON … Widget RATCHET`). |
| 5 degrade-never-hang | PASS | Connect wait bounded by `playerConnectTimeoutSeconds` (`server.nim:243-249`); LLM batch bounded by curly `makeRequests(batch, llmTimeoutSeconds)` (`llm.nim:554`); round-open guard `roundStart + 62 s <= playDeadline` else `endEarly()` (`server.nim:293-299`) with `playDeadline = start + 0.6 × 1200 = 720 s` (`:264-273`); player read bounded (F11 fix); shutdown grace 20 s then `quit(0)` (`:216-218`); thread guard `quit(1)` (F7 fix). No unbounded loop found. |
| 6 num_agents | PASS | 4 in `goofspiel-4` (variant + game_config), 2 in `oshi-zumo-2`, 4 in `certification.game_config`, 4 cert players (manifest:377-467); `tests/test_manifest.nim:17-34` asserts all. `docker_smoke.sh:106-151` enforces the four invariants with `SEAT-COUNT FAIL:` prefixes before any container starts; `SMOKE_SEATS` default 4 (`:54`). **Grepped the head docker-smoke log: no `SEAT-COUNT FAIL` anywhere**; log shows `seats=4`, `smoke OK: seats=4 … reason=complete`. |
| 7 scripted baseline full episodes, tuned | PASS | `tests/test_bot.nim:37-67` `playAll` checks every bid `in legalBids(seat)` at the moment produced, asserts `done` **and** `resultsJson()["reason"] == "complete"` (F4 fix), 200 seeds × both modes × both baselines; grid harness `scripts/tune_baselines.nim` + `docs/baseline-tuning.md` (F6 fix), shipped constants at the grid peaks, harness asserts equality with `scriptedBid` at the shipped point. |
| 8 LLM reply handling | PASS | `llm.nim:381-391` first-`{`/last-`}` extraction tolerating fences/prose; `for attempt in 0 .. 1` (`:539`) = exactly one retry, second batch carries `bidList(sim.legalBids(seat))` (`:549-551`, same proc the validator uses at `:564`); fallback to `match` with `fellBack = true` (`:573-577`), counted into `fallbacks[]` (`sim.nim:341-343`) and reported in results (`sim.nim:469`). |
| 9 rune-safe truncation | PASS | One shared `cleanText` (`types.nim:87-94`, `runeSubStr` + `…`), applied to say/notes (`llm.nim:503-504`, `sim.nim:335-337`), prompt 4000 (`server.nim:496`), every captured error at 200; `tests/test_replay.nim:185-229` feeds 80/400 runes of `日`+emoji at exactly the cap and asserts `validateUtf8 == -1` + strict `parseJson` round-trip + rune-boundary cut. |
| 10 manifest validates | PASS | `game.docs` = `{readme:{type,value}, pages:[{id,title,content:{type,value}}]}` (manifest:313-328); `game.protocols` carries **both** `player` and `global` as typed text objects (:303-311); asserted by `tests/test_manifest.nim:69-83`. |
| 11 viewer legible at 360 px | PASS | `chrome.css:493` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; `@media (max-width: 640px)` hides `.plate-label, .plate-alias` (:537-551); 360 px block present; clock drops the mode word under 420 px (`renderer.js:90-93`, `:640`); ranks always numeric (`String(rank)`, `:157`). |
| 12 release order and scaffold | PASS | `coworld-release.yml`: build (:165) → certify `--timeout-seconds 300` (:179-182) → upload policies (:213, explicitly before upload-coworld) → upload-coworld (:316) → secret put reading `game.name` (:349-370). All three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 2 `PLAYER_PROMPT` champions + `match` + `hoard` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Placeholder gate run by me at head: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files exits 1 (clean). |
| 13 viewer executes | PASS | `wasm-viewer` green at the head run **including** *Load the bundle in a real browser*: `{"loaded":true,"ms":291,…}`, `soak: 10s of playback kept advancing`, working scrub readouts; `needs: docker-smoke` (`ci.yml:212`); no `continue-on-error` anywhere in `ci.yml` (grepped). Markers: `data-replay-loaded` set on the first drawn frame (`renderer.js:1054-1059`) then `ready` posted from `onFirstFrame` (`static_replay.js:118-129`); `data-replay-error` set/removed (`static_replay.js:56`, `:107`, `:140`). Link flags and bootstrap from the **same** starter: `config.nims` `-s MODULARIZE=1 -s EXPORT_NAME=GozuReplayModule` ↔ `static_replay.js:144` `GozuReplayModule().catch(…)` — factory called, babel's own pairing. |
| 14 chrome is the starter's | PASS | `client/chrome.css`: the starter's 443 lines are a **byte-identical prefix** (verified by diff), game block appended under the banner at :445. `client/chrome_common.js`: every declared babel@d55d999 region is a byte copy (diffed 680-734, 790-864, 934-1049 myself); **exactly one** edited line, `describeEvent`→`feedText` at :201, as the note names; additions only appended. `client/replay_broadcast.html` = starter's `replay.html` + title/wordmark/`chrome_common.js` script under the banner + `BabelRenderer`→`GozuRenderer` (76 vs 74 lines; diffed, nothing removed). Transport: `relayout()` sets `--band`/`--hudscale` on `:root` (`chrome_common.js:493-502`); `#endscreen { inset: 0 0 var(--band,0px) 0 }` shown via its own `.show` rule; **every** seek routes through `setIndex`, which removes `.show` whenever `index < events.length` (`renderer.js:1015-1036`); beats are labelled `<button>`s via `markRoundBeat` with CSS for all six emitted kinds (`chrome.css:475-480`); nothing `position:fixed` in the band. `#viewpanel` absent — babel has none and the board is fixed; no `zoomAt/setZoom/attachMinimap` anywhere. `chrome_scope_check.mjs` green in CI: `31 exported names, 10 copied regions intact, no shadowing`. |
| 15 every drawn string fits its frame | PASS | Head run, real-replay smoke: `canvas text: 13356 drawn, 0 never inside … 0 ellipsized` with `--strict-text-bounds` **on** (fixed arena). Renderer fixture step: shipped bundle in an iframe, wasm entry shimmed only, full-cap 80-rune says on every seat (two worst-case shapes incl. a no-space CJK run), longest policy names, 360/640/1280 px, both modes, own strings asserted full-length, remark-ellipsis and drawn-in-full assertions in the page itself; result `loaded:true`, `never_inside: 0`, 138 ellipsized all nameplates (a remark ellipsis would have failed the page before `data-replay-loaded`). Say band reserved unconditionally, sized from `MaxSayLen` in the render font at `--hudscale` (F1/F10 fixes). |
| simultaneous batch | PASS | `llm.nim:539-554`: one `curly.RequestBatch` per attempt, one `batch.post` per open seat, one `makeRequests(batch, timeout)` — all seats' calls per round go out as one parallel batch (bullwhip `decideAll` shape); the server calls `decideAll` once per round outside the lock (`server.nim:320`). No sequential per-seat call path exists. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed `511e369` | band sized from cap at `--hudscale`, fixture gates remark integrity; CI fixture green with 0 never_inside | yes |
| F2 | no change, evidence | code correct, zero-sum requires it, no checklist bearing | yes |
| F3 | fixed `8357bf1` | bare-token rankLetter + test_llm.nim; no test weakened (file is new) | yes |
| F4 | fixed `f924c03` | reason assertion added to playAll — an *added* assertion | yes |
| F5 | fixed (label) `af5e9bb` | retitle + comment only; no assertion changed | yes |
| F6 | fixed `c1208a7` | harness + recorded table present; asserts parity with shipped code | yes |
| F7 | fixed `5241e7b` | try/except → quit(1) wrapper present | yes |
| F8 | fixed `1c12d06` | length mismatch raises; new test asserts it | yes |
| F9 | no change, evidence | fixture names are the note's own; item 4 satisfied | yes |
| F10 | fixed `4538243` | hudScale() read off :root, applied in sayFontPx | yes |
| F11 | fixed `2ebbae2` | bounded receiveMessage timeout, exit-0 both paths | yes |

No fix weakened a test: every test-file hunk this run is an addition or a retitle (verified from
`git log -p -- tests/` before reading the fixer's report).

## Non-blocking observations

- The soak line prints `(null -> null -> null)` for its progress markers while still reporting
  "kept advancing" and showing three distinct scrub readouts — the template harness's progress
  probe reads a field this page does not expose. The soak still gates (the step is not
  `continue-on-error` and the readouts moved); worth a look next time the template is touched.
- `scripts/tune_baselines.nim` is not compiled by any CI job and can rot (the fixer noted this
  too). Advisory only — item 7 requires the harness and the recorded table, both present.
- The design note's §Scoring still reads `pool = 91` flatly while the code (correctly) uses the
  awarded pool for deadline stops; a one-line note amendment would close F2's residue. The shipped
  rules page already states the code's behaviour.
- `docs/baseline-tuning.md` records that oshi-zumo `hoard` beats `match` head-to-head at every
  tested rate above 0.5 — worth remembering before reading the two fillers as a strength ordering.

BLOCKING: 0
