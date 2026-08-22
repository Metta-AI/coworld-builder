blocking: 0

# r1 verdict — lighthouse

Head: `eeb1004f3c8adbdde1ce562b1bec7ca3d3495ebb` (current `main` of `Metta-AI/cogame-lighthouse`)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: **yes** — I read the checklist, the design note,
and the full tree (sim.nim, types.nim, llm.nim, server.nim, lighthouse.nim, lighthouse_player.nim,
all three tests, both viewer scripts, lighthouse_replay.nim, the manifest, all three workflows,
docker_smoke.sh, policies.json, chrome.css, build_replay_viewer.sh, fixtures, README), pulled the
CI run and its logs, and formed the checklist table below **before** opening `r1-review.md`, and
opened `r1-fixes.md` only after auditing every finding against head myself. No contamination.

CI evidence: ci.yml run **32602216061**, `headSha: eeb1004f…`, `conclusion: success`
(jobs: `test` ✓ 30s, `docker-smoke` ✓ 1m4s, `wasm-viewer` ✓ 1m2s) — verified via
`gh run view 32602216061 --json headSha,conclusion,status`, not accepted from anyone's summary.
`grep -c 'SEAT-COUNT FAIL'` over the full run log: **0**. docker-smoke log prints
`game=lighthouse seats=4 … num_agents: 4 …` and `smoke OK: seats=4 results=252B replay=4280B reason=timeup`.

---

## Standing blocking findings

None. Every reviewer finding is either fixed at head (with the fixing commit verified below) or
refuted/dismissed on the checklist text, and my own independent checklist pass found nothing
blocking that the reviewer missed.

## Refuted / resolved findings (all 17, audited at head)

The review was written at `a16bebc`; fifteen fix commits landed after it. **A finding that was
true at `a16bebc` and is fixed at head is resolved, not standing.** I re-verified each in the
code at `eeb1004`, not from the fixer's table.

### F1 — glyphAt masked water under a key → RESOLVED by `58e0314`
- Evidence: `src/lighthouse/sim.nim:444-462` at head — precedence is now runner → exit →
  `isWall` → `isFlooded` → key → floor (`if sim.isFlooded(x, y): return '~'` **before**
  `if (x, y) in sim.keysOnFloor: return 'K'`). New assertions in `tests/test_sim.nim:557-564`
  flood a key tile (seed-free hand board, clock 24) and check `glyphAt(4,3) == '~'`,
  `keeperView()` and `runnerWindow()` agree. The finding was real; it is fixed.

### F2 — vacuous legality assertion (`and` for `or`) → RESOLVED by `f5c5f90`
- Evidence: `tests/test_bot.nim:82-84` at head — two separate checks,
  `check not result.sim.isWall(target[0], target[1])` and
  `check not result.sim.isFlooded(target[0], target[1])`, driven over
  `LegalitySeeds = [1, 7, 42, 1234, 3, 5, 11, 13, 21, 55]` (`:16`) including seed 21, the seed
  that exercises the F1 case. This is a **tightening** of a test, not a loosening (see item 1).

### F3 — stale 17/11/4 replay-config fallbacks → RESOLVED by `654e0b0`
- Evidence: `src/lighthouse/server.nim:530-536` — every fallback is now the field
  `defaultGameConfig()` already set (`recorded{"width"}.getInt(result.width)` etc.);
  `replay-viewer/lighthouse_replay.nim:29-36` identical. New test
  `tests/test_replay.nim:120-133` deletes `width/height/tideDelay/tidePeriod/keyCount` from a
  recorded payload and asserts `lhLoadReplay` still returns 1 with a final frame identical to
  the live sim's `boardStateJson`.

### F4 — note's viewer-smoke checks absent from CI → RESOLVED by `3503bfc`
- Evidence: `.github/workflows/ci.yml` at head, `wasm-viewer` job — step *"Check the viewer
  scripts parse and keep the coworld bridge"* runs `node --check client/renderer.js`,
  `node --check replay-viewer/static_replay.js` and `grep -qF` for `data-replay`,
  `coworld-replay`, `tell("ready")`; step *"Assert the bundle is complete"* resolves every
  `src=`/`href=` in the built `index.html` against the bundle. The green run's log prints
  `viewer scripts OK` and `referenced and present: ./chrome.css | ./renderer.js |
  ./lighthouse_replay.js | ./static_replay.js` (run 32602216061).

### F5 — lantern exception (c) fixed-window tide test → RESOLVED by `34bf871`
- Evidence: `src/lighthouse/llm.nim:323-349` — `clockAtLastMessage` reads the clock off the
  `evTick` of the tick the last message was sent on, and
  `roseSinceLastWord = spokenAt < 0 or tideRowsAt(config, clock) != tideRowsAt(config, spokenAt)`
  — "since the last message" as the note says, not a fixed 2-clock window.

### F6 — undocumented `H` alias → RESOLVED (docs) by `9ed9bd7`
- Evidence: design note §Reply schema (line 289) now lists `H` with the pilot-grammar reason;
  the manifest `rules.md` carries "STAY/HOLD/H (`H` because the …)". Code unchanged, correctly:
  removing `H` would break champion #2's own `"<Alias>:<N|S|E|W|H>"` grammar through
  `orderedDirection` → `parseMoveToken`.

### F7 — newlines replaced, not collapsed → RESOLVED by `8045db5`
- Evidence: `src/lighthouse/llm.nim:171-184` `collapseNewlines` (one run of `\n`/`\r` → one
  space), applied at `:683` before `cleanText`; `tests/test_bot.nim:247-249` asserts
  `"a\r\n\nb\n\nc"` → `"a b c"`.

### F8 — dead-end filter's stated reason overstated at 11×9 → RESOLVED (docs) by `d3cc14a` (+ `1db815d`)
- Evidence: design note §The game step 5 states "**At the shipped 11 × 9 the fallback is the
  NORMAL path, not the exception**" with the measured candidate counts; the code comment at
  `sim.nim:311-317` and the manifest `rules.md` say the same and attribute the difficulty to the
  shared distance filter. Doc finding, doc fix.

### F9 — fallback key path: no board order, unconstrained top-up → RESOLVED by `7ebff3d`
- Evidence: `src/lighthouse/sim.nim:336-364` — the greedy pass now walks the separation down one
  tile at a time (`while picked.len < want and separation >= 0 … dec separation`) instead of
  topping up with no check, and the result is sorted into `(y, x)` board order like the main
  path (`:356-364`). `client/fixtures/gen_fixture.js` / `sample_replay.json` updated to the
  reordered seed-11 keys; fixture still parses (`lighthouse.replay.v1`, 61 events — checked).

### F10 — `applyTick` cleared resolved seats' `scripted` flags → RESOLVED by `2c5bba7`
- Evidence: `src/lighthouse/sim.nim:539-546` — only the keeper and runners with
  `wasActive[index]` write their flag; a resolved seat keeps the flag it played under. New test
  `tests/test_sim.nim:272-288` asserts `sim.scripted[1]`, `events[^1].scripted[1]` and
  `boardStateJson()["seats"][1]["scripted"]` all survive ticks the seat no longer plays.
  (Checklist item 8's "fallback is recorded" now holds in the last frame too.)

### F11 — `ellipsize` not rune-safe → RESOLVED by `17aec90`
- Evidence: `client/renderer.js:97-107` — pops code points off `Array.from(text)` instead of
  `slice(0, -1)` on UTF-16 units. Canvas-only; replay bytes were never affected (all replay
  strings go through `cleanText`/`runeSubStr`). Design note §Viewer now names the one change.

### F12 — chrome.css delta understated → RESOLVED (docs) by `8e29974`
- Evidence: design note §Packaging (lines 924-933) now names all four additions including the
  six lighthouse classes and the `@media (max-width: 420px)` two-column block. The css itself is
  unchanged and the item-11 rules are present (see checklist pass).

### F13 — `/client/replay` route exists → REFUTED for checklist item 3 (judge ruling, authoritative this round)
- The checklist's operative requirements are: the manifest declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}` (✓ `coworld_manifest_template.json`,
  `game.replay_viewer`), `tools/build_replay_viewer.sh` exists as the `coworld build` hook
  (✓ mode 100755 in the index, `git ls-files -s` → `100755 … tools/build_replay_viewer.sh`),
  and the viewer contacts nothing but S3 (✓ the only network in the bundle is
  `static_replay.js:76` `fetch(url)` of `?replay=<url>` under a 20 s `AbortController`;
  `renderer.js:1288`'s WebSocket lives in `attachLive`, reachable only from
  `client/global.html`, which `build_replay_viewer.sh` does not copy into the bundle).
- "No `/client/replay` pod path anywhere" I rule to mean: **the platform's replay viewing must
  not route through a pod** — no pod viewer declared in the manifest, no viewer that phones the
  game pod. Three facts force that reading: (1) the checklist governs games built on this
  starter family, and both reference starters (`cogame-babel/src/babel/server.nim:502`,
  `cogame-bullwhip/src/bullwhip/server.nim:470`) ship this identical dormant replay-mode route
  while declaring the static bundle — a literal string-grep reading would fail the checklist's
  own exemplars, which is incoherent; (2) `coworld-release.yml` hard-fails certification unless
  the certify log reports the **static** bundle, with error text naming "a pod-served
  `/client/replay` viewer is not acceptable" — the enforcement point is the declaration, not
  the server binary's route table; (3) lighthouse's manifest, unlike babel's, contains **zero**
  mention of `/client/replay` (checked: the only pod page its docs mention is `/client/global`
  for live spectating). The route is starter-inherited replay-mode plumbing used by local
  `coworld run` inspection, never by the platform. **Item 3 passes; F13 is dismissed.**

### F14 — reviewed sha not head → MOOT
- I judged at `eeb1004f…`, which `gh run view … --json headSha` confirms is the sha CI ran on
  and the brief confirms is current `main`. The commit the review flagged (`1db815d`) is
  docs-only (`git show --stat 1db815d`: 1 file, `docs/plans/…design.md`) and is an ancestor of
  head.

### F15 — drown test missed the escape leg → RESOLVED by `efab54c`
- Evidence: `tests/test_sim.nim:247-270` — a runner reaches the open exit on the exact tick its
  row floods (clock 31→32, waterLine 2→1), and the test asserts `rsEscaped` for it, `rsDrowned`
  for the other two, **and** the intra-tick event order `@[evEscape, evDrown, evDrown]`. The
  code was already correct (step 7 `sim.nim:599-611` precedes step 8 `:614` and steps 9/10
  `:617-631`); the coverage now exists.

### F16 — starts seed-independent at 11×9 → RESOLVED (accepted + documented) by `6aec2b7`
- Evidence: design note §The game step 4 now states the degeneracy outright ("`{1, 5, 9}` is the
  only triple pairwise ≥ 4 apart — which is also the fallback — so every episode starts at
  `(1,7)`, `(5,7)`, `(9,7)`") and re-grounds the anti-pre-baking argument on the maze, exit,
  keys and aliases, which do vary. Not a code/note mismatch; correctly closed as documentation.

### F17 — `evTick.notes` repeated unchanged notes → RESOLVED by `eeb1004`
- Evidence: `src/lighthouse/sim.nim:529-537, 649-650` — `noteChanged[seat]` is true only when
  the incoming text is non-empty **and** differs; the tick record carries the text on the tick
  it changed, `""` otherwise. New test `tests/test_sim.nim:435-458` asserts first-tick record,
  `""` on repeat while `sim.notes` keeps the value, re-record on change, and
  `replayMatch` frames ending with `frames[^1].notes == sim.notes`.

**Score: 17/17 findings accounted for — 14 fixed, 1 refuted on the checklist text (F13),
1 accepted-and-documented (F16), 1 moot (F14). No finding stands at head.**

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green; no test loosened | **pass** | Run 32602216061 `conclusion: success`, `headSha == eeb1004f…` (gh, cited above). `git log -p -- tests/` over the whole run: the only removed lines across all history are one comment, the vacuous `and` predicate (replaced by two **stronger** separate checks, f5c5f90) and `for seed in Seeds:` (replaced by the **wider** `LegalitySeeds`). No skip/xfail/deleted assertion/widened tolerance/removed file. Test log shows all suites `[OK]` in both debug and `-d:release`. |
| 2 Replay re-derivation, viewer draws from it, test asserts | **pass** | `sim.nim:812-858` `replayMatch` replays whole ticks through `applyTick` (say buffered, key/escape/drown re-derived, `end` settles a deadline), `frames.len == events.len + 1`. Tests: `test_sim.nim:397-433` (JSON-round-tripped event log → `$frames[^1].boardStateJson() == $sim.boardStateJson()`, notes equality, frame count), `:460-476` (one-char grid mutation raises `"the recorded maze does not match the seeded one"`), `test_replay.nim:98-118` (the same through `lhLoadReplay`, the very proc exported to wasm, natively compiled), `:135-149` (mutation rejected with the exact error string). Viewer draws from the re-derivation: `lighthouse_replay.nim:47-49` builds `states` via `replayMatch`; `renderer.js:1433,1458` `states[min(index, …)]` is the only display source — no parallel recording. |
| 3 Static viewer, no pod replay path | **pass** | `coworld_manifest_template.json` `game.replay_viewer == {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, is the build hook (`ci.yml` wasm-viewer asserts `-f` and `-x` with the `coworld build`/`os.X_OK` rationale; `coworld-release.yml` runs `coworld build --template …`); bundle's only network is the S3 `fetch` (`static_replay.js:76`) bounded at 20 s. `/client/replay` ruling: see F13 above — manifest mentions it nowhere, release hard-fails pod-declared viewers, the dormant route ships in both reference starters. |
| 4 Both name spaces | **pass** | Prompts address seats only by `sim.names[seat]` (`llm.nim:457-596`), drawn by `tableNames` (`sim.nim:124-140`); no `players[].name` reaches a prompt. Player `final` frame carries aliases (`server.nim:213-228`). `resultsJson` carries policy names (`sim.nim:679-704`). Replay carries both `names` and `policyNames` (`server.nim:176-190`); viewer `makeNameMap`/`isBaselineFiller` (`renderer.js:857-885`, regex `/^baseline(\s*\(\d+\))?$/i` verbatim babel) swaps policy names in wherever rendered, keeps aliases for baseline fillers. |
| 5 Degrade-never-hang | **pass** | Player-connect wait bounded: `server.nim:257-265` (`deadline = gameStart + playerConnectTimeoutSeconds`, default 180, `sleep(200)` poll). LLM batch bounded: `llm.nim:754` `makeRequests(batch, client.timeoutSeconds)`, default 18 s (`types.nim:92`), ≤ 2 attempts ⇒ 36 s/tick worst case. Play deadline checked **before every tick's batch**: `server.nim:304-312`, `PlayBudgetFraction = 0.6` (`:248`) of `COWORLD_TIMEOUT_SECONDS`-else-`episodeTimeoutSeconds` (1200) = **720 s**, → `endEarly()` → `reason = "deadline"` between ticks, then results+replay written. Main loop terminates on `done`/deadline; `applyTick` raise is caught and settles (`:346-350`). No credentials ⇒ scripted immediately, zero network (`llm.nim:737-739`, asserted < 1000 ms in `test_bot.nim:193-195`). Viewer fetch bounded 20 s. `sampleEpisode` caps `maxTicks ≤ 55`, `turnDelayMs ≤ 15000/maxTicks` (`sim.nim:142-153`; tested `test_sim.nim:512-529`). Budget arithmetic holds: 45×36 s can't run past the pre-tick 720 s gate. |
| 6 num_agents everywhere + smoke invariants | **pass** | `num_agents: 4` in `variants[standard]`, `variants[spring-tide]`, `certification.game_config`, and `config_schema` (`{"type":"integer","minimum":4,"maximum":4}`) — parsed from the manifest, not read from a summary. `docker_smoke.sh:98-143` enforces all four invariants (present; positive int; `len(certification.players)==n`; `len(game_config.players)==n`) **before** `docker network create` (`:183`), each exiting via `SEAT-COUNT FAIL:`-prefixed `SystemExit`; `SMOKE_SEATS` default `4` (`:47`) is the independent second declaration and is cross-checked (`:138-143`). Run 32602216061 log: `SEAT-COUNT FAIL` count **0**; `smoke OK: seats=4`. |
| 7 Scripted baseline: full legal episodes, tuned not guessed | **pass** | `test_bot.nim:97-116` drives lantern + 3×wallhug over 10 seeds to `done` with `reason ∈ {complete, timeup}` (deadline excluded), `tick ≤ maxTicks`, every reply one of the five legal tokens (`:66`), every target neither wall nor flooded (`:83-84`, real after F2), messages ≤ 160 runes valid UTF-8, no notes, `applyTick` never raises. The `== "complete"` clause is satisfied structurally and confirmed in the CI log: `allOut >= 2` (`:141`) can only pass via `escapedCount == 3` ⇒ `escaped+drowned == 3` ⇒ `settle("complete")` (`sim.nim:695-696`), and CI shows 3/4 fixture seeds all-out at ticks 25–37 < 45, i.e. ≥ 3 all-scripted episodes ending `reason == "complete"`. Tuning: the committed decision-rule test (`:127-142`, the note's oracle rule) passes with headroom (4/4 keys, 3/4 out); the note's §Tuning revision documents the oracle and the `tidePeriod {4,5,6,8,10,14} × maxTicks {45,55}` sweep; `types.nim:81-85` pins "Measured: 4 and 5 do not, 7 does"; and CI reproduces the note's measured numbers digit-for-digit (talk 0.5185/0.52/0.5143/0.5135; instruction 130/146 = 0.8904; scores 26.0–38.9) — not producible by guessing. Residue (non-blocking): the sweep harness itself is not committed. |
| 8 LLM reply handling | **pass** | Tolerant parse: `extractJsonObject` (`llm.nim:600-610`) takes `find('{')..rfind('}')`; tested on fences and chatty prose (`test_bot.nim:253-259`). Exactly one retry with a hint: `for attempt in 0 .. 1` (`:742`), `retryHint` appended on attempt 1 (`:750-751`, `:712-718` — the note's wording, keeper variant names transmit/message). Then role-appropriate scripted fallback (`:767-770`), logged `"lighthouse llm: seat N falling back to scripted decision"`, recorded via `Decision.scripted` → `evTick.scripted` (`sim.nim:649-651`), which survives seat resolution (F10 fix + test). |
| 9 Rune-safe truncation | **pass** | `cleanText` = strip + `runeSubStr(0, limit-1) & "…"` (`llm.nim:162-169`); applied to message (160, `:682-683`), keeper notes (400, `:681`), runner notes (200, `:700`), lantern's own message (`:292`), captured error heads (`:607`, `:669`); inbound prompt frames `runeSubStr(0, 4000)` (`server.nim:480-481`). Tests: `test_sim.nim:376-394` (400 é-runes → runeLen == cap, `validateUtf8 == -1` on every serialised event, results, board state); `test_replay.nim` (messages and all four seats' notes **exactly on** the 160/400/200 boundaries with `≤ → 🌊 é 水`; `validateUtf8(payload) == -1`; `parseJson` succeeds; byte-identical codec round-trip; the same bytes accepted by `lhLoadReplay`). |
| 10 Manifest validates | **pass** | Parsed the template myself: `game.docs == {"readme": {"type":"text","value":…(957 chars)}, "pages": [{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…(7967 chars)}}]}`; `game.protocols` has exactly `player` and `global`, both non-empty. |
| 11 Viewer legible at 360 px | **pass** | `client/chrome.css:280-293` `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }`; `:455-459` `@media (max-width: 640px) { .plate-label { display: none; } … }`. (Plus the 420 px two-column scorebug fallback, additive.) |
| 12 Release order and scaffold | **pass** | `coworld-release.yml` single job, steps in order: *Build the Coworld manifest* → *Certify locally* (hard-fails without the static-bundle liveness marker) → *Upload the policies* ("BEFORE upload-coworld") → *Upload the Coworld* → *Put the Coworld secret* ("AFTER upload-coworld"). The only smoke (ci.yml docker-smoke) builds `${IMAGE}:ci` in the same job before running the script. Three workflows present (`ci`, `coworld-release`, `coworld-submit`). `docker_smoke.sh` mode 100755 in the index. `policies.json`: 4 distinct policies — `lighthouse-beacon` (PLAYER_PROMPT), `lighthouse-pilot` (PLAYER_PROMPT, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `lighthouse-lantern` + `lighthouse-wallhug` (PLAYER_SCRIPTED). Placeholder gate run by me: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files → no matches, exit 0 path taken. Expected residue (`<cow_id>/<sha>`, `<run_id>`, `<name>:vN`) present and not filed. |
| + Simultaneous batch | **pass** | `decideAll` (`llm.nim:722-770`) builds one `RequestBatch` for all open seats and issues one `curl.makeRequests` per attempt; `server.nim:324` calls it once per tick, outside the lock, on a snapshot. No per-seat sequential call exists anywhere. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `58e0314` | glyph precedence + new view assertions at head | ✓ |
| F2 | fixed, `f5c5f90` | split checks + LegalitySeeds incl. 21 | ✓ |
| F3 | fixed, `654e0b0` | `getInt(result.field)` both readers + omitted-keys test | ✓ |
| F4 | fixed, `3503bfc` | both CI steps present; log prints `viewer scripts OK` + reference sweep | ✓ |
| F5 | fixed, `34bf871` | `clockAtLastMessage` comparison | ✓ |
| F6 | fixed (docs), `9ed9bd7` | `H` in note §Reply schema + manifest rules.md | ✓ |
| F7 | fixed, `8045db5` | `collapseNewlines` + crlf test | ✓ |
| F8 | fixed (docs), `d3cc14a` | rules.md/README/code comment updated | ✓ |
| F9 | fixed, `7ebff3d` | separation walk-down + (y,x) sort + fixture regen | ✓ |
| F10 | fixed, `2c5bba7` | per-seat flag write + carry test | ✓ |
| F11 | fixed, `17aec90` | `Array.from` code-point pop | ✓ |
| F12 | fixed (docs), `8e29974` | §Packaging names the full delta | ✓ |
| F13 | refuted, no change | my independent ruling agrees (see above) — reached before reading the fixer's argument, on the same evidence plus the incoherence of failing the checklist's own reference starters | ✓ |
| F14 | resolved, no change | head is `eeb1004`, `1db815d` docs-only ancestor | ✓ |
| F15 | fixed, `efab54c` | escape-leg + event-order assertions | ✓ |
| F16 | accepted + documented, `6aec2b7` | note step 4 states the degeneracy | ✓ |
| F17 | fixed, `eeb1004` | `noteChanged` logic + repeat-notes test | ✓ |

The fixer's claim "no test was disabled, skipped, weakened or deleted" checks out against
`git log -p -- tests/` (see item 1). The fixer's CI citation (run 32602216061, success, 0
`SEAT-COUNT FAIL`) matches what I pulled from gh directly.

## Non-blocking observations (judge's own; tied to no checklist item)

1. **A seat that never delivers a prompt plays LLM-with-empty-prompt, not its role's baseline,
   when credentials exist.** Design note §Decisions #6 says "any seat that never delivered a
   prompt plays its role's baseline"; in code such a seat has `prompts[slot] == ""` and
   `scripted[slot] == skNone` (`server.nim:575-576`), and `decideAll` (`llm.nim:737-741`) routes
   `skNone` + enabled client to the LLM batch with no operator block (system prompt only). No
   hang, no unbounded wait, all bounds hold — so item 5 is unaffected — but the note and the
   code disagree on which policy such a seat plays. The reviewer's wait table recorded the fact
   without flagging the mismatch. Worth one line of code or one line of note in a later round.
2. **The tuning sweep harness is not committed** (reviewer's residue #1, still true at head).
   The committed decision-rule test plus the digit-exact CI reproduction of the note's measured
   numbers verify the substance; the harness itself would make the sweep reproducible.
3. `keeperPrompt`/`runnerPrompt` glyph legends don't state the water-over-key precedence F1
   added to the map itself (fixer's NOTED #2). The map is unambiguous; the legend merely
   doesn't say why.
4. Checklist item 7's literal phrase `asserts results.reason == "complete"` is realised as
   `reason in ["complete", "timeup"]` plus the structural `allOut >= 2` guarantee (detailed in
   the checklist row). If a future round wants the literal assertion, one added line in the
   competence test (`if escaped == 3: check reason == "complete"`) would close the wording gap.

## Could not verify (and why it does not count as blocking)

Nothing on the checklist. Every item above is verified from the tree at `eeb1004`, from the gh
API/log of run 32602216061 (id and conclusion cited), or from executing the checklist's own gate
commands in this sandbox. Live-LLM behaviour (real batch latency, retry rate under load) is
phase-60 territory by the note's own definition and is not a checklist-30 item.

BLOCKING: 0
