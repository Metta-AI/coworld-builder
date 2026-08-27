blocking: 0

# r1 verdict — negotiation-games

Head: `04f7a60c32db9e361249218080ef2ef2c992a406` (main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15)
Independent read written before reading fixes: **yes** (repo cloned to `/tmp/judge-neg`, all of
`src/`, `tests/`, `client/`, `replay-viewer/`, `tools/`, workflows and the manifest read, diffed
against `/workspace/starters/cogame-babel`, CI run 33024746218 logs pulled — before opening
`r1-review.md`; `r1-fixes.md` opened last, only to attribute dispositions).

The review was written at `5f23877`; this verdict is at `04f7a60`, eight commits later (F1–F6, F10
fix commits in between). Per the brief: a finding true at the review sha and gone at head is
**fixed**, not refuted.

## Standing blocking findings

None. Both of the review's blocking candidates are fixed at head; my own independent checklist
pass found no additional finding tied to a checklist item.

## Review findings — disposition at head

### F1 (checklist 9, byte-slice prompt cap) → FIXED at head
- Was real at `5f23877` (starter-inherited `prompt[0 ..< MaxPromptLen]` byte slice).
- At head: `src/negotiation/server.nim:493` — `let prompt = cleanPrompt(payload{"prompt"}.getStr())`;
  `src/negotiation/sim.nim:46` `MaxPromptLen* = 4000`, `sim.nim:123-124`
  `cleanPrompt = capRunes(text, MaxPromptLen)` (rune-safe: `runeLen`/`runeSubStr`, `sim.nim:111-118`).
  Test added: `tests/test_sim.nim:459-477` feeds `MaxPromptLen + 500` × `é`, asserts
  `runeLen == MaxPromptLen`, `validateUtf8 == -1`, trailing `…`, byte length > rune count, and an
  at-cap prompt returned whole. `[OK]` in run 33024746218 (debug and `-d:release`).

### F2 (checklist 15, remark ellipsized in a box sized by eye) → FIXED at head
- Was real at `5f23877` (single `negLabel` at `maxWidth: w*0.3`, fixture *required* `ellipsized > 0`).
- At head: `client/renderer.js:79-135` — the remark band is reserved in the layout
  (`negTalkBand` wraps a 200-rune worst-case sample `TALK_SAMPLE` in the draw font and sizes the
  band from it), `renderer.js:404-410` reserves it before anything is drawn and places the pool
  row below it (`rowY = min(h*0.72, max(h*0.66, talkTop + band.height + 20*scale))`) whether or
  not anyone speaks, and `renderer.js:433-444` wraps the message into the band with
  `negWrapLines` — never through `ellipsize` as a single line.
  `tools/ci/renderer_fixture.html:60-97, 336-347` now fails on any ellipsized remark fragment
  (`remark.cut > 0`) and fails unless the full 200 runes reached the canvas
  (`remark.best < remark.runes`); it still self-checks the payload carries the 200/400-rune caps
  and both stamps (`:302-311`).
  CI at head: browser-load step `canvas text: 4154 drawn, 0 never inside … 0 ellipsized
  (--strict-text-bounds)`; fixture step `canvas text: 2742 drawn, 0 never inside … 0 ellipsized
  (--strict-text-bounds)` (run 33024746218). Note: the fixer legitimately INVERTED the fixture's
  ellipsis assertion (require → forbid) — a strengthening, judged on its hunk content.

### F3 (two RNG streams) → FIXED at head (was advisory)
- `sim.nim:290-294`: one `Rand` (`initRand(int64(config.seed) * 7919 + 17)`) now feeds
  `tableNames(rng, …)` then `drawSchedule(rng, …)`, matching the note's single-stream order.

### F4 (view.effects computed and discarded) → FIXED at head (was advisory)
- `renderer.js:300-313` (`negAge`/`negEntrance`), `:459-477` (offer slide-in over 320 ms),
  `:499-501` + `:315-364` (stamp entrance over 260 ms, holds until the next match's `match` event
  via `effectResetKinds: ["match"]`). Only the pool row's x and the stamp's alpha animate, so the
  text-bounds gate is unaffected (0 never_inside at head).

### F5 (stamp/feed strings differ from the note) → FIXED at head (was advisory)
- `renderer.js:336-363`: no-deal stamp prints `0 – 0` + `N TURNS, NO AGREEMENT`; deal stamp prints
  the payoff and the final item split. `renderer.js:679-690, 723-725`: the `end` feed line prints
  per-seat `Final — <name> <pts> pts (<score>)`, accumulated from the feed's own matchEnd payoffs
  with the same `points / (10 · matches played)` arithmetic as `sim.score`.

### F6 (matchbar counted started, not scheduled, matches) → FIXED at head (was advisory)
- `renderer.js:769, 813-814, 522-523`: `negScheduled` is fed from `state.matches`
  (= `config.matches`, carried by every state) and from the clock's config; the event-derived
  count remains as a floor (`:779-780`). A `deadline` replay now shows one chip per scheduled
  match, unstarted ones pending.

### F7 (four defensive guards in chrome_common.js) → covered by an accepted deviation
- `chrome_common.js:53, 105, 201, 296` are guards on missing/empty inputs, unreachable on the
  shipped pages (ids frozen and gated by `chrome_check.py:47-58`). The coordinator's accepted
  deviation list explicitly rules "chrome_common.js carries … plus defensive guards" as accepted.
  Not a finding at head.

## Refuted

### F8 — "inherited chrome.css uses literal px, the note says every size is calc(--hudscale)" → REFUTED (as a defect)
- Evidence: `client/chrome.css:1-443` at `04f7a60` is byte-identical to
  `/workspace/starters/cogame-babel/client/chrome.css` (diff shows additions only, all below the
  banner at `:445`). Checklist item 14 requires the inherited sections unmodified; the appended
  block (`:452-588`) does use `calc(… * var(--hudscale))`. This is a note-wording mismatch, not a
  checklist violation — the reviewer themselves traced it to that conclusion.

### F9 — "player receive loop blocks with no timeout" → REFUTED (as a checklist-5 finding)
- Evidence: `src/negotiation_player.nim:54-80` at `04f7a60`. The read has a guaranteed
  terminating event: the game sends `final` before writing artifacts (`server.nim:192-204`) and
  `quit(0)` after the fixed 20 s grace (`server.nim:224-226`), which closes the socket; whisky's
  raise on the close frame is caught and the player exits 0 (`:79-80`) — the cogame-raid 0.1.4
  pattern the design note pins. Checklist 5 governs the episode settling and scoring, which never
  waits on this read (prompt delivery is opportunistic; the game starts regardless after the
  bounded connect wait, `server.nim:248-254`). docker-smoke at head enforces every player exits 0
  within 60 s of the game and reports `all 3 player containers exited 0` (run 33024746218).

### F10 — three dead declarations → partly fixed, remainder non-blocking
- `scriptedAction` deleted at `07b09aa` (grep at head: absent). `MaxMatchesCap` (`sim.nim:28`) and
  the registered-but-unread `phaseText` hook (`renderer.js:877`; `H.phaseText` never read in
  `chrome_common.js`) remain — both are declared by the design note, both dead code, neither tied
  to any checklist item. Non-blocking observation, stands as residue of zero weight.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | PASS | `gh run list`: run **33024746218**, workflow CI, branch main, headSha `04f7a60c…`, conclusion **success**; all 3 jobs, no skipped/continue-on-error steps. `git log -p --since=2026-08-26T21:52Z -- tests/`: 3 commits — initial import (`35a427b`), `1973f80` drops an unused `strutils` import from test_bot, `3fd0517` ADDS a test-12 case (strengthening). No assertion deleted, no tolerance widened, no skip/xfail, no file removed. |
| 2 replay re-derivation | PASS | `sim.nim:749-802` `replayMatch` re-derives from the seed through the same `apply*`/`settle` procs, validates each `match` event against the seeded schedule (`:764-771`) and each offer/accept's `worth`/`take`/`payoff` against re-derived values by recorded index (`:777-793`); viewer states come only from it (`replay-viewer/negotiation_replay.nim:37-39`, `chrome_common.js:479-503` reads `payload.states`). Test: `test_sim.nim:287-329` — frames.len == events.len+1, final frame byte-equal `tableStateJson()` for BOTH `complete` and `deadline`, tamper rejected. |
| 3 static viewer | PASS | manifest `:16-18` `game.replay_viewer.bundle == "static-replay-viewer"`; `tools/build_replay_viewer.sh` mode 100755 in git (`git ls-files -s`), asserted + invoked by path in ci.yml `:256-286`; `static_replay.js` fetches only `?replay=` (`:131, :146`), bundle assets all relative. `/client/replay` exists only as the live-server route (`server.nim:525`, note-pinned); no pod viewer declared anywhere in the manifest. |
| 4 both name spaces | PASS | aliases seeded (`sim.nim:188-198`), prompts composed from aliases only (test 13, `test_sim.nim:479-510` greps every composed prompt); player frames never carry policyNames (`server.nim:95-116`), final frame swaps in aliases (`:189-199`); viewer maps aliases→policy names for non-baseline seats (`chrome_common.js:116-149`); `resultsJson` carries policy names (`sim.nim:552`). |
| 5 degrade-never-hang | PASS | connect ≤ `playerConnectTimeoutSeconds` (`server.nim:246-254`); LLM call ≤ 30 s via curly timeout (`llm.nim:430`), exactly one retry (`:477`); spacing sleep ≤ 2200 ms (`server.nim:326-331`); play deadline `gameStart + 0.6 × timeout` = 720 s of 1200 (`server.nim:228, 269-282`), tested before every model call (`forceScripted = pastDeadline`, `:335-336`) and between matches (`:300-309`); pacing ≤ `PacingBudgetMs` (`:369-372`); shutdown grace fixed 20 s then `quit(0)` (`:222-226`). `decide` never raises (`llm.nim:492-500`); a rejected apply falls back to a legal scripted move (`server.nim:353-361`), so the turn always advances and the loop is bounded. Sequential calls are correct here per the brief (strictly turn-based v1). |
| 6 num_agents | PASS | `num_agents: 3` in variant `standard` (manifest:358), `sprint` (:381), certification (:402); `docker_smoke.sh:130-171` enforces all four invariants + the independent `SMOKE_SEATS=3` cross-check (:56, :166-171), each exiting with `SEAT-COUNT FAIL:` before any container starts; grep of the full run-33024746218 log for `SEAT-COUNT FAIL`: **0 hits**; job printed `smoke OK: seats=3 … reason=complete`. The accepted SMOKE_CONFIG_JSON merge strips num_agents/players/tokens (:121-123). |
| 7 scripted baseline full legal episodes | PASS | `test_bot.nim:53-89`: 5 seeds × 3 pairings to natural end, `reason == "complete"`, `started == settled == matches`, `0 ≤ take[i] ≤ pool[i]`, no accept on turn 1, `turn ≤ maxTurns`, `fallbacks == 0`. Parameters pinned by the note's algorithms (`llm.nim:151-189` implement them literally) and behaviour asserted over a 100+-match seeded grid in CI (suite 16: 102/102 deals, joint 14.79; 97/102 differ; hardliner 8.11 vs haggler 6.26 — printed in run 33024746218). |
| 8 LLM reply handling | PASS | `extractJsonObject` tolerates fences/prose (`llm.nim:394-405`); parse tolerance per the note (`:353-390`); exactly one retry with the hint (`:477-484`); fallback to the seat's baseline recorded via `decision.fallback` → `recordFallback` → `results.fallbacks` (`server.nim:362-363`, `sim.nim:536-537`, schema manifest:212-221). Tests 17/18 `[OK]` at head. |
| 9 rune-safe truncation | PASS | `capRunes` (`sim.nim:111-118`) used by `cleanMessage`/`cleanNotes`/`cleanPrompt` and on every quoted error head (`llm.nim:403, 432, 441, 446, 455`); events only carry cleaned strings (`sim.nim:472-473, 512-513`). Tests 12 (multibyte at cap, `validateUtf8 == -1`, `…`) incl. the new prompt case; strict-UTF-8 replay parse green (`replay_check.py:41-42`, `replay_check: OK — 47 events`). F1 was the one gap and is fixed. |
| 10 manifest validates | PASS | `game.docs` = readme + 2 pages, all `{"type":"text","value":…}` (manifest:248-271); `game.protocols.player` and `.global` both text objects (:238-247). Gated by `manifest_check.py:153-179` plus the installed coworld CLI's own `_load_template_manifest`/`validate_coworld_manifest_game_configs` (:181-206); `Manifest checks` step green at head. |
| 11 legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (`chrome.css:463`); `.plate-label { display: none }` under 640 px (:476-480); gated by `chrome_check.py:107-118`; fixture renders 360/720/1280 px with 0 never_inside. |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:159) → Certify (:173) → Upload the policies (:212) → Upload the Coworld (:310) → Put the Coworld secret (:348). All three workflows present; smoke builds its own image in-job (ci.yml:189-209) and wasm-viewer builds its bundle in-job. `docker_smoke.sh` mode 100755 in git. `policies.json`: 4 policies, 2 `PLAYER_PROMPT` champions with champion #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, 2 `PLAYER_SCRIPTED` fillers, all `/bin/negotiation-player`. Placeholder gate run by me at head: `grep '<slug>\|<IMAGE>\|<SEATS>'` over the five files → no matches, exit as required. |
| 13 viewer executes | PASS | run **33024746218**, `wasm-viewer` job success incl. step `Load the bundle in a real browser` (conclusion success, not absent/commented/continue-on-error), `needs: docker-smoke` (ci.yml:243). Log: `{"loaded":true,"ms":298,…}`, `soak: 8s of playback kept advancing ("0 / 47" -> "10 / 47" -> "12 / 47")`, scrub readouts moved. Both markers from the shell's own paths: `data-replay-loaded` set in `attachReplay`'s `onFirstFrame` after the first `renderer.draw` (`static_replay.js:123-126`, `chrome_common.js:556-563`), `data-replay-error` in `fail()` (`static_replay.js:56`). `config.nims:43-46` `MODULARIZE=1` + `EXPORT_NAME=NegotiationReplayModule` matches the factory call `NegotiationReplayModule()` (`static_replay.js:141`); both files diffed against the same starter (renames + onFirstFrame only); no `onRuntimeInitialized` in the tree. |
| 14 chrome is the starter's | PASS | `chrome_common.js` is babel's `renderer.js` chrome half function-for-function; the whole diff is the note's three named changes + the coordinator-accepted deviations (hook object with extra redirected call sites, defensive guards, `makeNameMap` third-param drop). `replay_broadcast.html` diffed against babel's `replay.html`: title/wordmark/clock text, the banner-commented `#gameblock`, `tick-clock` on `#pos` (accepted), the chrome_common script tag, `relayout()` in `fit()` — nothing removed (82 vs 74 lines). `chrome.css` = starter byte-identical + banner-separated additions. Transport: (a) `relayout()` measures `#transport`, writes `--band`/`--hudscale` on `document.documentElement` (`chrome_common.js:257-268`); (b) `#loading` re-anchored `bottom: var(--band)` (`chrome.css:525`), `#gameblock` in normal flow, `#endscreen` inside `#board-wrap` which stops above the transport (accepted deviation); (c) endcard shown via `classList.toggle("show", …)` (`renderer.js:602`) against `#endscreen.show` (`chrome.css:381`), and every seek entry point (scrub pointer events, beat buttons, play-restart) goes through `setIndex(next, true)` which calls the endcard painter with `show = false` (`chrome_common.js:506-517`) — the page binds no keyboard/back-forward seeks, same as the starter; (d) beats are `<button type="button" aria-label=…>` seeking `onSeek(i+1)` (`chrome_common.js:333-344`) with a CSS rule for every emitted kind (offer/accept/deal/nodeal/end, `chrome.css:551-583`, gated by `chrome_check.py:78-89`). No `#viewpanel`/zoom/minimap anywhere (grep clean; board is fixed). |
| 15 every drawn string fits | PASS | ci.yml `:351-356` carries `--strict-text-bounds` on the smoke-replay run: `canvas text: 4154 drawn, 0 never inside … 0 ellipsized` (never_inside = 0, total ≠ 0). Renderer fixture in its own step (`Renderer text fixture at 360 / 720 / 1280 px`, ci.yml:365-386) drives the SHIPPED page + real wasm on a rewritten real smoke replay (accepted deviation) with full-cap 200-rune messages / 400-rune notes on every action + both stamps (`make_fixture_replay.py`), at 360/720/1280 px, with `--strict-text-bounds`: `canvas text: 2742 drawn, 0 never inside … 0 ellipsized`. The fixture asserts its own strings are full-length (`selfCheck` :302-311) AND that the full 200-rune remark reached the canvas unellipsized (`:336-347`), and only then sets `data-replay-loaded` — harness reported `loaded: true`. The remark band is reserved in the layout, sized from the server cap, measured in the draw font (`renderer.js:79-135, 404-410`). |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `3fd0517` | `cleanPrompt` at `server.nim:493`, `sim.nim:46,123-124`, new test-12 case, `[OK]` in run 33024746218 | yes |
| F2 | fixed, `362f623`+`04f7a60` | reserved band from the cap in the draw font, fixture forbids ellipsized remark and requires 200/200 runes drawn, CI `0 ellipsized` on both steps | yes |
| F3 | fixed, `f39a734` | one RNG stream, aliases then schedule (`sim.nim:290-294`) | yes |
| F4 | fixed, `f706bb0` | `negEntrance`/`negAge` read `view.effects`; slide-in + stamp entrance implemented | yes |
| F5 | fixed, `b14a236` | `0 – 0`, item split, per-seat `Final — … pts (…)` all present | yes |
| F6 | fixed, `1f3c2a3` | matchbar sized by `negScheduled` from `state.matches`/config | yes |
| F7 | refuted | covered by the coordinator's accepted-deviation list ("defensive guards") | yes |
| F8 | refuted | inherited CSS untouched is what item 14 requires; note-side wording issue | yes |
| F9 | refuted | wait bounded by the game's `final` + `quit(0)`; starter shape; players exit 0 in CI | yes |
| F10 | partly fixed (`07b09aa`) | `scriptedAction` gone; `MaxMatchesCap` + `phaseText` hook remain, note-declared, dead, tied to no checklist item | yes |

## Non-blocking observations

- `MaxMatchesCap` (`sim.nim:28`) and the registered-but-never-read `phaseText` hook
  (`renderer.js:877`) are dead declarations the design note itself pins (F10 residue).
- The manifest's player-protocol prose still says "prompt max 4000 chars"; the cap is now measured
  in runes at the same number. Human prose, no validator reads it.
- The design note needs three owner-side corrections the fixer listed (chrome "three changes",
  the `--hudscale` wording, `MaxMatchesCap`).
- Could not verify from the sandbox: hosted behaviour of the live LLM path (docker-smoke runs
  keyless by design; the retry/transport branches are covered by unit tests 17/18 only). This is
  the checklist's intended gate design — phase 60's hosted episode counts `results.fallbacks` —
  and no checklist item requires a keyed CI episode, so it is not counted as blocking.

Verdict: the review's two blocking candidates were real at the review sha and are fixed at head;
the advisory findings are fixed, accepted-deviation-covered, or refuted; my independent checklist
pass finds all fifteen items satisfied at `04f7a60` with CI run 33024746218 as the executing
evidence.

BLOCKING: 0
