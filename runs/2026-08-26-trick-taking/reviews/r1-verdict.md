blocking: 0

# r1 verdict — trick-taking

Head: `179aa9993c4d1308b1a26945e1d758e63d16957f`   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes
(Repo cloned fresh to `/tmp/judge-cogame-trick-taking` and checked out at the head sha. The
review and `r1-fixes.md` were read only after I had formed my own read of the tree and the CI
logs; the fixer's table was then audited claim by claim, not adopted.)

CI cited throughout: run **33035205309** on `main`, `head_sha` confirmed equal to the reviewed
sha via `gh api`, conclusion **success**; jobs `test` (98396320366), `docker-smoke`
(98396320476), `wasm-viewer` (98396519279) all success.

## Standing blocking findings

None. Every r1 blocking finding is fixed at the current head, and my own independent checklist
pass found no new blocking finding.

## Refuted

All three r1 blocking findings were true at `80aeb68` and are **refuted at the current head**
(fixed since; a finding that was true and has been fixed is refuted, not standing).

### B1 — labels hidden under 400 px, not 640 px  → REFUTED (fixed at head)
- Evidence: `client/chrome.css:588-591` at `179aa99` —
  `@media (max-width: 640px) { .plate-label { display: none; } .plate-pips { display: none; } }`,
  with the 400 px query now carrying only the `#wordmark`/`#clock`/`#modulechip` font sizes
  (`:592-596`). `ci.yml`'s static-grep step additionally fails if the 640 px block lacks
  `.plate-label { display: none }` (`ci.yml:366-369`), and that step is green in run 33035205309.

### B2 — notes band not sized from the server's 400-rune cap  → REFUTED (fixed at head)
- Evidence: `client/renderer.js:237` (`var NOTES_CAP_RUNES = 400;`) and `:245-266` —
  `computeLayout` measures the mean advance of the note alphabet **in the note font**
  (`ctx.measureText(NOTE_ALPHABET).width / Array.from(NOTE_ALPHABET).length`), multiplies by the
  cap (`var capW = advance * NOTES_CAP_RUNES`) and derives `noteLines`/`noteH` from it, band
  reserved whether or not anything is written. CI now distinguishes a nameplate's ellipsis from
  a renderer-added sentence cut: run 33035205309, `wasm-viewer`, step *The notes band fits the
  server's cap, and cuts are rune-safe* — `360x640: 4500 strings drawn, no mid-string cut`,
  `960x640: … no mid-string cut`, `1440x900: … no mid-string cut`,
  `notes fit OK: 515 capped-string ellipses, all of them the server's own cap`. The smoke-replay
  invocation reports `0 ellipsized` outright.

### B3 — no grid harness or tuning record  → REFUTED (fixed at head)
- Evidence: `tools/ci/tune_baselines.nim` (the harness: candidate vs shipped, every deal played
  from both pairs of positions and averaged), `docs/tuning.md` (the committed sweep, 46 grid
  points × 96 deals × 2 orientations, plus a second independent seed set), and
  `tests/test_tuning.nim:26-40` pinning `baselineParams("follow"/"tracker")`
  (`src/tricks/llm.nim:173-179`) to the recorded table. The harness is a **gate**: it exits
  non-zero if any grid point beats the shipped configuration beyond tolerance, and `ci.yml:158-162`
  runs it on every push (green in run 33035205309, step *Baseline tuning sweep (grid harness)*).

### r1 non-blocking findings, verified at head
- **N1** (429 backoff unbounded) — fixed: `src/tricks/llm.nim:39` `MaxExtraSpacingMs* = 3000`,
  `:140-144` caps in `noteThrottled`, and `src/tricks/server.nim:327-333` re-reads the clock
  after the spacing sleep and refuses any call whose worst case
  (`worstCaseCallSeconds() = 2 × llmTimeoutSeconds`, `llm.nim:146-150`) would outrun the hard
  deadline. `tests/test_bot.nim:138-157` asserts both bounds.
- **N2** (re-derivation not frame-by-frame) — fixed: `tests/test_sim.nim:609-634` records the
  live `frameStateJson` after every applied move and compares it to
  `replayMatch(config, roundTrip(events))[n]` at the same event count, for all four modules,
  with non-vacuity checks (`live.len > 30`, `compared == live.len`).
- **N3** (`/client/replay` route) — resolved as position + gate: `ci.yml:383-388` requires
  `game.replay_viewer` to equal `{"bundle": "static-replay-viewer"}` **exactly** (no url/path/pod
  key can ride beside the bundle) and rejects a top-level `replay_viewer`. I concur with the
  reviewer's and fixer's reading: the live route is starter chrome for a running episode, the
  manifest declares only the static bundle, and the bundle fetches nothing but its `?replay=`
  URL (`replay-viewer/static_replay.js:67-88` — bounded 20 s fetch, no other network call).
  Item 3's substance holds.
- **N4** (`fit()` edited) — fixed for the three pages the review named:
  `client/replay.html:42-45`, `replay-viewer/index.html:44-47`, `client/player.html:34-37` are
  babel's two-line `fit()` verbatim (I diffed all three against
  `/workspace/starters/cogame-babel`). See non-blocking observation 1 below: `client/global.html`
  still carries the same edit.
- **N5** (claimed geometry assertion missing) — fixed: `tools/ci/chrome_geometry_check.mjs` +
  `ci.yml:475-485`; run 33035205309 logs
  `endcard geometry OK: #endscreen bottom 729.0 <= #transport top 729.0 (shown by seek: true)`.
- **N6** (up-card drawn twice) — fixed: `src/tricks/euchre.nim:172-174` removes the picked-up
  card from the kitty (`sim.kitty.delete(inKitty)`); `tests/test_sim.nim` asserts all 24 cards
  are in exactly one place after an `order` and that a passed-around up-card stays in a 4-card
  kitty.
- **N7** (`frameStateJson` carries `kitty`/`discard`) — DISPUTED by the fixer; **I side with the
  dispute**. The design sample (design.md:687-702) is abbreviated on its face (one seat object
  where four are always emitted), and design.md:397-399 mandates spectators see the kitty and
  the discard. No checklist item bears on it. Advisory, correctly left alone.
- **N8** (`bidsMade` description) — fixed in the manifest description; `reason`, the only enum
  item 10 gates, is untouched.
- **N9** (hearts worst case 224 vs 220) — fixed: `heartsWorstCase` now reads `passDirName(hand)`
  and charges 52 on a hold hand; `tests/test_sim.nim:727-753` pins euchre 232 / spades 224 /
  hearts 220 / oh-hell 188.
- **N10** (forced move increments `decisions[]`) — DISPUTED by the fixer; **I side with the
  dispute**. `results_schema.properties.decisions` declares "Decisions the slot was asked for,
  including forced and scripted ones"; `modelCalls` and `EpisodeDecisionBudget` are untouched by
  a forced move (`server.nim:290-296`). No checklist item bears on it.
- **N11** (no top-level thread guard) — fixed: `src/tricks/server.nim:373-399` — `runGame` wraps
  `runEpisode` in `try/except CatchableError`, settles with `endEarly("deadline")` (inside the
  declared enum) and runs the idempotent `finishEpisode`, so a dying game thread still writes
  artifacts.
- **N12** (`ellipsize` slices UTF-16 code units) — fixed: `client/renderer.js:117-127` pops
  runes off `Array.from(text)`; `tools/ci/notes_fit_check.mjs` fails on any lone surrogate in
  any drawn string and on the astral rune never being drawn (non-vacuous).

## The two questions the fixer flagged (decided on the checklist)

1. **B3's sweep moved `tracker`'s bidding constants off design.md:586-588** (`orderAt 12→10`,
   `aloneAt 18→16`, `spadesShade 1→0`). **Not a checklist violation.** Item 7's second clause
   demands the parameters be "tuned with a grid harness, not guessed" — which is precisely what
   happened: the design note's literals were the guess, the sweep is the evidence
   (`docs/tuning.md:142-159`: ordering up at 12 costs −0.015, shading the spades bid costs
   −0.036 and drops the win rate to 17 %), and CI would go red if the note's values were
   restored (`tools/ci/tune_baselines.nim` gate + `tests/test_tuning.nim`). No checklist item
   pins baseline constants to the design note. `tracker` remains a distinct policy from
   `follow`: the void table, the certain-winner lead, the bag avoidance and `ohHellDrop = 2` are
   all intact in the play path (`llm.nim:307-450`). The residue is a **stale design note**, noted
   below as non-blocking.
2. **`client/player.html` drops babel's `attachLive` call.** **Not a violation of item 14.** The
   change is recorded in the design note — design.md:754-755: "Both `/client/` routes serve real
   pages, registered before any catch-all asset route, and **neither opens the player socket**
   (lantern 0.1.1)" — and babel's `attachLive({... wsPath: "/player?slot=..."})` opens exactly
   that socket, so dropping it is what the recorded sentence requires (a page occupying the slot
   would break the real player container's connect). The page keeps every starter id, the game
   block sits under the banner comment, and item 14's named artifacts (chrome.css + renderer.js
   as `chrome_common`, replay.html + index.html as the broadcast page) all diff clean modulo the
   named patches.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 33035205309, `head_sha == 179aa99…` (gh api), conclusion `success`, all 3 jobs success. `git log -p 80aeb68..HEAD -- tests/`: 8 deleted lines total, of which the only non-context deletions are the 3-line `Shipped` tuple replaced by one **adding** exact expected counts (`tests/test_sim.nim:730-733`) — a tightening. No skip/xfail/tolerance change anywhere; ~216 assertion lines added. |
| 2 replay re-derivation frame by frame | PASS | `tests/test_sim.nim:609-634` (every intermediate live frame vs the re-derived frame at that tick, all four modules, JSON round-trip), `:636-680` (byte-identical re-derivation for `complete`, hard-deadline `handVoid`, `budget`). Viewer derives from the same re-derivation: `replay-viewer/trick_taking_replay.nim:38` (`"states": replayStates(config, events)`), `client/renderer.js` reads `payload.states` only — no parallel recording exists (`server.nim:115-120` broadcasts and discards). |
| 3 static viewer | PASS | Manifest: `game.replay_viewer == {"bundle": "static-replay-viewer"}` exactly (verified by loading the JSON; gated at `ci.yml:383-388`); `tools/build_replay_viewer.sh` mode 100755 and wired in `coworld-release.yml`; `static_replay.js` fetches only the `?replay=` URL. No pod viewer path declared anywhere in the manifest (the one `/client/replay` mention is descriptive text inside `protocols.global`). |
| 4 both name spaces | PASS | Aliases: `sim.nim:51-61` (`CogNames` pool, seed-shuffled, rune-capped), prompts use `sim.names` only, player `final` frame sends aliases (`server.nim:155-171`). Policy names: `results.names` = `config.players[slot].name` (`sim.nim:637-640`), `replay.policyNames` (`sim.nim:989-991`), viewer maps via `makeNameMap`/`isBaselineFiller` (`renderer.js:702-731`). `playerStateJson` deletes `tell`/`kitty`/`discard` and blanks other seats' hands/notes (`server.nim:99-113`). |
| 5 degrade-never-hang | PASS | Connect wait bounded (`server.nim:206-214`, 180 s); LLM call bounded (curl timeout 20 s × ≤2 attempts, `llm.nim:1037`, one retry only); 429 → no retry + capped backoff (`llm.nim:39,140-144,1053-1055`); spacing floor ≤ 5.2 s; post-sleep re-check refuses a call that cannot return before the hard guard (`server.nim:327-333`); soft 0.55·T scripts the rest of the hand and scores it, hard 0.56·T voids it (`server.nim:234-235,262-288`); budget 240 (`types.nim:25`); top-level thread guard (`server.nim:373-399`); bounded shutdown grace 20 s then `quit(0)`. 672 + 40 (worst call) + pacing ≤ 720 s = 60 % of 1200. `tests/test_sim.nim` pins worst-case decisions ≤ 240 and seconds ≤ 660 per shipped variant. Sequential-by-design verified in code: exactly one actor per decision (`currentCall`), no batch exists to parallelize — the design note's N/A claim is correct. |
| 6 `num_agents` | PASS | `num_agents: 4` in all four variants and in `certification.game_config` (loaded and checked); `len(certification.players) == 4 == len(game_config.players)`; `docker_smoke.sh:106-150` enforces all four invariants plus the `SMOKE_SEATS` cross-check with `SEAT-COUNT FAIL:` prefixes. `grep -c "SEAT-COUNT FAIL"` over the full docker-smoke log of run 33035205309: **0**; log shows `game=trick-taking seats=4 … "num_agents": 4` and `smoke OK: seats=4 … reason=complete`. |
| 7 scripted baseline | PASS | `tests/test_bot.nim:88-103`: 200 complete matches × 2 baselines × 4 modules, `reason == "complete"`, every move checked against `legalMoves` (`moveIsLegal`), bids in range, hooked value never bid, pass exactly 3 distinct held cards, actor walks clockwise. Tuning: grid harness + committed record + CI gate + pinning test (see B3 above). |
| 8 LLM reply handling | PASS | `extractJsonObject` (first `{` to last `}`, `llm.nim:863-873`); tolerant card/bid parsing incl. `T`/index forms (`llm.nim:875-951`, `cards.nim`); exactly one retry (`for attempt in 0 .. 1`, `llm.nim:1037`) with the invalid-reply hint and re-printed legal list (`llm.nim:855-859`); fallback to scripted recorded in `fallbacks[slot]` (`server.nim:344-345,357`), forced in `forcedMoves[slot]`, both in `results_schema`. |
| 9 rune-safe truncation | PASS | One `truncateRunes` (`types.nim:204-212`), applied to notes 400, prompt 4000 (server-side `server.nim:520` and `llm.nim:837`), aliases 16, tell 120 (`sim.nim:519`), error 200 (`llm.nim:1012`). Tests feed 4-byte/astral input at the cap: `tests/test_bot.nim:207-235` (5 kB emoji → 400 runes, whole replay `validateUtf8() == -1`, strict parse), `tests/test_sim.nim` rune suite. |
| 10 manifest validates | PASS | `game.docs = {readme:{type:"text",value}, pages:[rules.md, modules.md, scoring.md each {id,title,content:{type,value}}]}`; `game.protocols` carries **both** `player` and `global` as `{type,value}` objects (loaded and checked). |
| 11 legible at 360 px | PASS | `client/chrome.css:447` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; `:588-591` labels+pips hidden under 640 px; both greped in `ci.yml:363-369`. |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build manifest (`:159`) → Certify (`:173`) → Upload the policies (`:212`) → Upload the Coworld (`:310`) → Put the Coworld secret (`:348`, namespace read from `game.name` in the built manifest); all three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep finds nothing (I ran the gate verbatim: exit 1 from grep → clean). |
| 13 viewer executes | PASS | `wasm-viewer` has `needs: docker-smoke` (`ci.yml:246`), no `continue-on-error`; run 33035205309's *Load the bundle in a real browser* step ran against the smoke replay: `{"loaded":true,"ms":304,…}`, `soak: 12s of playback kept advancing`, three distinct scrub readouts (HAND 1/3 → 2/3 → 3/3 FINAL). Markers: `data-replay-loaded` set from the renderer's first **painted** frame (`renderer.js:1440-1446`), `data-replay-error` set/cleared by the shell (`static_replay.js:56,107,136`). Lockstep: `config.nims` links `MODULARIZE=1`, `EXPORT_NAME=TrickTakingReplayModule`; `static_replay.js:140` calls the factory `TrickTakingReplayModule()`; `_tt_*` export list matches the shell's calls; no `onRuntimeInitialized` in the tree; both greped in CI. |
| 14 chrome is the starter's | PASS | `chrome.css`: byte-identical to babel above the banner at line 435 except the removal of babel's own game tail (the exact removal the note lists); appended block only below. `renderer.js`: chrome machinery (makeNameMap, feed, effects, scorebug, endscreen, bindFeedToggle, both drivers, attachReplay) preserved with the named patches — `buildTrickBeats` (labelled `<button>` beats calling the track's `onSeek`, CSS for every emitted kind, CI-greped), `relayout()` publishing `--band`/`--hudscale` on `document.documentElement` (`renderer.js:1120-1130`), rune-safe prompt cap (`server.nim:520`). `replay.html`/`index.html`: starter's pages verbatim + banner-commented `#modulechip` and `relayout()` bootstrap. Endcard: inside `#board-wrap`, dismissed on **every** `setIndex`, geometry measured in CI (`endcard geometry OK … shown by seek: true`). No overlay in the band; no `#viewpanel` (fixed arena, babel ships none). `player.html`'s socket drop is recorded at design.md:754-755 (decided above). |
| 15 every drawn string fits | PASS | All three `viewer_smoke.mjs` invocations run with `--strict-text-bounds` and report `never_inside: 0` with `total` in the tens of thousands (41762 / 94308 / 12765 — the check covered plenty). Worst-case renderer fixture exists (`tools/ci/renderer_fixture.html`: full-cap 400-rune notes on **every** seat + full-cap 120-rune tell + an astral rune, self-asserting its own lengths at `:95-96`), driven at 360×640/960×640/1440×900 in its own `ci.yml` step. `ellipsized` is disambiguated by `notes_fit_check.mjs`: every capped-string ellipsis is the server's own tail (`no mid-string cut` at all three sizes), no lone surrogates. Notes band sized from `NOTES_CAP_RUNES = 400` measured in the drawing font (`renderer.js:230-266`). |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed `a2c8e214` | 640 px block at chrome.css:588-591 + CI grep | yes |
| B2 | fixed `004068a6` | cap-derived band, notes_fit_check green, 0 ellipsized on smoke replay | yes |
| B3 | fixed `49c52bcf` | harness + docs/tuning.md + pinning test + CI gate step green | yes |
| N1 | fixed `ef9f42c5` | MaxExtraSpacingMs 3000, post-sleep hard-deadline refusal, test | yes |
| N2 | fixed `1810581a` | frame-by-frame test with non-vacuity checks | yes |
| N3 | fixed (gate) `c1f14b85` | exact-equality manifest gate in ci.yml | yes |
| N4 | fixed `85e609a1` | 3 pages restored verbatim — but `global.html` retains the same edit (see obs. 1); the fixer's claim was scoped to the review's three pages and is true as stated | yes, with a caveat |
| N5 | fixed `215b6ef8` | chrome_geometry_check.mjs, CI log `endcard geometry OK` | yes |
| N6 | fixed `550d80ec` | euchre.nim:172-174 kitty delete + tests | yes |
| N7 | DISPUTED | design sample abbreviated; design.md:397-399 mandates the fields; no checklist item | yes — dispute upheld |
| N8 | fixed `3fe75100` | description now per-module; `reason` enum untouched | yes |
| N9 | fixed `0733f5f7` | passDirName-driven worst case; counts pinned 232/224/220/188 | yes |
| N10 | DISPUTED | schema description already declares the counting; budget untouched; no checklist item | yes — dispute upheld |
| N11 | fixed `c82c5677` | runGame try/except → endEarly("deadline") → idempotent finishEpisode | yes |
| N12 | fixed `179aa999` | rune-based ellipsize + lone-surrogate gate in notes_fit_check | yes |

## Non-blocking observations

1. **`client/global.html` still carries the non-starter `fit()`** (`global.html:34-39`: parent
   /960×640 fallback) — the same class of unrecorded chrome edit as N4, present since the first
   build commit and not restored by `85e609a1` because the review only named the other three
   pages. It is 3 lines, defensive, harmless (ids intact, page functions), and `global.html` is
   not among item 14's named artifacts (chrome_common ↔ chrome.css+renderer.js; broadcast page ↔
   replay.html+index.html), so it does not block — but by the N4 fix's own standard it should
   either be restored to babel's two lines or named in the design note next round.
2. **The design note is now stale in three places** (this round may not edit it; someone should
   decide which document moves): (a) tracker's bidding constants (design.md:586-588 vs the
   sweep's 10/16/0, recorded in `docs/tuning.md`); (b) the 400 px `.plate-label` breakpoint
   (design.md:968-969 vs the checklist-required 640 px now shipped); (c) `viewer_smoke.mjs`
   "asserts" the endcard geometry (design.md:909-910 — the assertion lives in
   `chrome_geometry_check.mjs` instead, which is better than the claim).
3. **`viewer_smoke.mjs` reports `distinct_capped: false` on the renderer fixture** — expected
   (single synthetic scene, not a scrubbable replay); not a failure.
4. The `hearts_moon` fixture invocation reports 2663 `ellipsized`; per `notes_fit_check`'s
   evidence these are the server-cap tails and nameplate ellipses, and `never_inside` is 0. Not
   gated, correctly so.

BLOCKING: 0
