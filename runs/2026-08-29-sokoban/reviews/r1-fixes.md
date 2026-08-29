# r1 fixes — sokoban

Repo: `Metta-AI/cogame-sokoban`, branch `main`.
Head: **`f31307a90ca5c3f3e1adc0efa199c5140981a605`**
CI: **https://github.com/Metta-AI/cogame-sokoban/actions/runs/33246336750** — conclusion **success**
(run id `33246336750`, event `push`, branch `main`, headSha `f31307a9…`; jobs `test` ✅,
`docker-smoke` ✅, `wasm-viewer` ✅ **including** `Load the bundle in a real browser` and
`Drive the shipped chrome with a worst-case frame`).

Range reviewed: `464b2ab` (the reviewed sha) → `f31307a9`.

| finding | disposition | commit | files | checklist item it serves |
|---|---|---|---|---|
| F1 dropped hard-coded to 0 | fixed | `1dd3edb` | `src/sokoban/sim.nim:76,276,394`, `src/sokoban/decide.nim:107`, `tests/test_sokoban_obs.nim:79` | 8 (reply handling), correctness |
| F2 settle zeroes the in-play level | fixed | `7da6c2e` | `src/sokoban/sim.nim:645-670`, `tests/test_sokoban_sim.nim:462` | 5 (settles and scores), correctness |
| F3 byte-truncated provider reply | fixed | `4929332` | `src/sokoban/sim_types.nim:195`, `src/sokoban/llm.nim:197-213`, `tests/test_sokoban_baselines.nim:200` | **9 (rune-safe truncation)** |
| F4 actionsDropped double-counts | fixed | `f8dbcb5` | `src/sokoban/sim.nim:278-285` | correctness (phase-60 counters) |
| F5 `throttled` outside the cause set | fixed | `cfe9d10` | `src/sokoban/decide.nim:269-276`, `tests/test_sokoban_events.nim:110` | 8 (fallback recorded for phase 60) |
| F6 `baselineNodeCap` 8 vs the note's 20 000 | **no change** (note stale, code coherent + tested) | — | `src/sokoban/search.nim:29-36`, `tools/ci/baseline_tuning.json` | 7 (tuned, not guessed) — satisfied |
| F7 relaxed pick is the deepest | fixed | `7843231` | `src/sokoban/levelgen.nim:238,300-313` | correctness (level sourcing step 11) |
| F8 provenance script does not run | fixed | `6291c9f` | `scripts/build_broadcast_page.py`, `README.md:122`, `tests/test_sokoban_viewer.nim:59` | **14 (chrome is the starter's)** |
| F9 `--strict-text-bounds` measured 0 strings | fixed | `c9f9d4d` + `f31307a` | `tools/ci/renderer_fixture.html`, `client/sokoban_block.html`, `client/replay_broadcast.html`, `.github/workflows/ci.yml:334`, `tests/test_sokoban_viewer.nim:250` | **15 (every drawn string fits its frame)** |
| F10 artefacts the note names are absent | **no change** (assertions all exist elsewhere; nothing is skipped) | — | — | 1 (no test skipped) — satisfied |
| F11 sweep sizes / band / no-`/` grep | **partly fixed** (`/` grep) | `dee96a4` | `tests/test_sokoban_sim.nim:472-500` | 1 (no test loosened) |
| F12 unvalidated byte→enum in the parser | fixed | `05ecd4c` | `src/sokoban/replays.nim:126-138,260-270`, `tests/test_sokoban_replay.nim:96` | 2 (replay re-derivation), static-viewer |
| F13 3 of 11 event kinds emitted | fixed | `0f60d90` (+ `14fd919`) | `src/sokoban/server.nim:327-360`, `tests/test_sokoban_events.nim:102` | correctness (tier-2 stream) |
| F14 cadence / speed chips / interpolation | **no change** (code self-consistent; interpolation is residue) | — | `src/sokoban/replay_runtime.nim:12-20`, `src/sokoban/sim_types.nim:53` | 13 (viewer executes) — satisfied |
| F15 deadlock flash is only a banner | fixed | `92a91fc` | `client/sokoban_block.html:263,430,505`, `client/replay_broadcast.html`, `tests/test_sokoban_viewer.nim:283` | 14/15 (watchability) |
| F16 `results.names` is the policy label | fixed | `1da5c62` + `9c1ab66` | `src/sokoban/server.nim:511-525,559-570,668`, `tests/test_sokoban_engine.nim:181` | 4 (both name spaces) |
| F17 `game.docs` `"type":"uri"` | fixed | `7a5c370` | `coworld_manifest_template.json`, `tests/test_sokoban_manifest.nim:70` | **10 (manifest validates)** |
| F18 `do` accepts spellings outside the enum | fixed | `09129e5` | `src/sokoban/directives.nim:134-148`, `tests/test_sokoban_baselines.nim:145` | 8 (drop, never rewrite) |
| F19 settle/finishEpisode outside the guard | fixed | `4d2d685` | `src/sokoban/server.nim:178-196,386-403`, `tests/test_sokoban_engine.nim:158` | 5 (degrade, never hang) |

Every fix is its own commit; no commit carries two findings and no unrelated cleanup rides along.
Sixteen findings fixed, three dispositioned with evidence (F6, F10, F14) and one fixed in part
(F11).

---

## F1 — the `dropped` count reported to the seat

**Was:** `endTurn` built `TurnReport(... dropped: 0 ...)` (`sim.nim:393`) while the replay's
`directive` record wrote the real `directive.dropped + directive.overCap` (`decide.nim:107`). The
two disagreed by construction and nothing ever wrote a non-zero `last_turn.dropped`, so the
self-correction loop both champion prompts steer on ("If `last_turn` says …") never fired for a
dropped entry.
**Is:** `beginTurn` records `sim.turnDropped = directive.dropped + directive.overCap`, `endTurn`
reports it, and `directiveRecord` now reads `sim.lastReport.dropped`, so the observation and the
replay have one source and cannot drift again.
**Evidence:** new test `tests/test_sokoban_obs.nim` "dropped counts the entries the reply lost, and
matches the replay" — two invalid entries plus one past a cap of two ⇒ `last_turn.dropped == 3`.
Green in the `test` job of run 33246336750 (debug and `-d:release`).

## F2 — a deadline or fault stop no longer zeroes the level in play

**Was:** `settle` finished an in-flight level as `loUnreached` and then zeroed every record whose
outcome was `loRunning`/`loUnreached` — which matched the record it had just written. The level
under the cog lost its crates (up to 40 000 points of `boxCredit`), its moves, its turns and its
pushes, and `finalTick` under-reported the episode.
**Is:** the in-play level is finished `loOutOfSteps` — it was reached, it was neither solved nor
deadlocked, and its budget ended under it — and keeps its real numbers. Only the levels *past*
`levelIndex` are zeroed and marked `unreached`; levels start strictly in order, so that set is
exactly "never started", which is what the note's deadline rule says to zero. `unreached` is now
reserved for that meaning alone.
**Evidence:** new test "a wall-clock stop never zeroes the level that was in play" — a deterministic
fixture parks one crate on a marked square, forces `endDeadline/erWallClock`, and asserts the
record, `boxCredit`, `finalTick` and `episodeScore` all survive; the pre-existing test that every
`unreached` record carries zeroes is unchanged and still passes.
**On the related half of F2** (the `endComplete` + level-active branch marking `loOutOfSteps`): that
branch is unreachable in every shipped config and I did not change it. Trace: `turnComplete` is
`turnEnded or queueIndex >= turnMoves`, and `stepTick` increments `queueIndex` on every path, so a
turn that does not end a level always consumes exactly `turnMoves = 20` moves; ten turns of a level
therefore reach `levelMove == stepBudget == 200` and `stepTick` fires `loOutOfSteps` itself
(`sim.nim:371-373`) before the episode's `turnsPlayed >= maxTurns` can fire with a level still
active. `maxTurns = levelCount × levelTurnCap` is asserted in `test_sokoban_manifest.nim`.

## F3 — the provider reply is cut on a rune boundary (checklist item 9)

**Was:** `llm.nim:198-199` and `:207-208` sliced by byte index. The second slice cuts the
concatenated assistant text, which goes to `extractJsonObject` → `parseDirective` → `say`/`notes` →
the replay. `std/json` does not validate UTF-8, so a cut that lands mid-codepoint parses and the
broken byte reaches the replay, where `truncateRunes` can only shorten it, never repair it.
**Is:** `truncateUtf8Bytes` (new, `sim_types.nim`) cuts at ≤ N **bytes** and backs up off a UTF-8
continuation byte to the start of the sequence, so the note's "≤ 4096 bytes read from the provider
before parsing" still holds *and* the cut is rune-safe. Both caps use it.
**Evidence:** new test "the 4096-byte provider cap cuts on a rune boundary, not a byte" builds a
reply whose 4-byte emoji straddles byte 4096, asserts the **old** byte slice yields
`validateUtf8() != -1`, asserts the new cut yields `-1`, and asserts the resulting `directive.say`
is valid UTF-8 at `MaxSayRunes`. It also pins the call sites in `llm.nim` (two uses, no
`MaxReplyBytes]` slice left). This closes the reviewer's "Could not determine" item — the reviewer
could not construct the input; the test now does.

## F4 — the two counters are disjoint

`actionsDropped += directive.overCap` only; `repliesRepaired += directive.dropped` unchanged. The
note's turn steps 6a/6b describe them as disjoint and both are in `results`, so a phase-60 reader
adding them no longer double-counts. The seat's `last_turn.dropped` and the replay's
`directive.dropped` still carry the total, which is the number a policy needs.

## F5 — `transport_error`, not an eighth cause

A 429 is the provider refusing the call, so it is recorded as `transport_error`, which is in the
note's closed set; `rate_guard` stays reserved for this engine's own rolling 60 s counter, a
different fact about a different actor. New test scans `decide.nim` for every cause literal it can
write and asserts each is in the declared seven.

## F6 — `baselineNodeCap = 8` — **no change, the note is the stale half**

Not changed, and I do not think it should be. Evidence: the repo is internally consistent at 8 and
asserts it (`tests/test_sokoban_events.nim:143-160` ties `tools/ci/baseline_tuning.json` ≡
`DefaultSearchParams` ≡ all three manifest `game_config` blocks); `search.nim:31-36` records the
measurement that produced it — "a 20 000-node cap measured 1.00 / 1.00 / 0.99 across the tiers,
which is precisely the superhuman floor the design note's test 25 exists to keep out of the image";
and `test_sokoban_baselines.nim`'s strength gate (the note's own test 25) is what a 20 000-node cap
would fail. Checklist item 7 asks that the baseline's parameters were **tuned with a grid harness,
not guessed** — `tools/tune_baselines.nim` is committed, its sweep is recorded, and the shipped
defaults are asserted equal to it. Changing 8 → 20 000 to match the prose would ship a superhuman
filler and break the item the note wrote the test for.
The note's `ci.yml` "re-runs the sweep with `--check`" is indeed absent; I did not add it (a full
sweep in CI is minutes of runtime for an assertion the `test` job already makes against the
recorded sweep). Residue, recorded here.

## F7 — the relaxed attempt closest to `bandMin`

`if bfs.reached > bestReached` became "smallest `abs(bfs.reached - bandMin)`", the note's step 11.
`optPushes` was exact either way (BFS first-discovery depth), so this changes which relaxed level
ships, not its honesty. Integer-only, so the no-float grep still passes.

## F8 — the page-provenance script runs again, and the starter revision is recorded

**Was:** the documented command failed at `build_broadcast_page.py:40` (`anchor not found:
'<div class="ec-thead">…'`) — coworld-ctf added a `TK` column in `ed3bd67` after this fork was
taken, so the one mechanical check that `client/replay_broadcast.html` is the starter's page and not
a lookalike could not be run at all.
**Is:** the endcard-header anchor is matched by shape (`swap_re`), since every column is replaced
wholesale anyway, and the starter revision the page was derived from is recorded as
`STARTER_SHA = a7484eb47b14bde20678ff106c684a633b4f294c` in the script, in the README and asserted
by `tests/test_sokoban_viewer.nim`.
**Evidence, run in this sandbox:**

```
git -C /workspace/starters/coworld-ctf show a7484eb:client/replay_broadcast.html > /tmp/p.html
python3 scripts/build_broadcast_page.py /tmp/p.html /tmp/rebuilt.html client/sokoban_block.html
diff /tmp/rebuilt.html client/replay_broadcast.html      # EMPTY — byte-identical
python3 scripts/build_broadcast_page.py \
  /workspace/starters/coworld-ctf/client/replay_broadcast.html /tmp/new.html \
  client/sokoban_block.html                              # also runs clean now
```

The shipped page in this round was in fact **regenerated by the script** from that pinned starter
revision plus the edited block (F9, F15), so the provenance is not a claim about the past — it is
how the file was produced.

## F9 — the fixture now covers the class it exists for (checklist item 15)

Two commits, both this finding.

`c9f9d4d`:
* **A reserved band for the `say` row.** The inherited `.feed-row` is `white-space: nowrap` and
  sized to content — right for a pre-bounded 10-character name, wrong for the one string whose
  length the server caps. Right-anchored in `#killfeed`, 140 runes grow leftward past the stage and
  off the frame at 360 px, where the whole composition is ~270 px wide. The say row now wraps
  inside the column `#killfeed` already reserves (its four-row `min-height` means nothing jumps
  when a remark lands).
* **Assertions.** The fixture reads the row the real page rendered and fails unless it contains all
  140 runes, unshortened and un-ellipsized, and unless every text line the page laid out in the
  feed, the banner lane and the level ribbon is inside the frame — at 360, 640 and 1280 px.
* **A mirror canvas.** Every one of those lines is re-drawn, per rendered line and in the page's own
  font and box, into a main-thread 2D canvas the size of the frame, so `--strict-text-bounds` has
  the real layout to measure instead of a worker's invisible OffscreenCanvas.

`f31307a` — **found by the first CI run, 33245823236**, which failed with
`data-replay-error: at 360px the say row never reached #killfeed`. The cause is structural and is
exactly why the old fixture passed while testing nothing: the page's
`if (window.SokobanChrome) window.SokobanChrome.install(PB_CTX)` runs while the appended block is
still unparsed, so the block never receives its context from `install` — it gets `PB_CTX` on the
page's **first drawn frame**, through `frame(s, PB_CTX, jumped)`. The old fixture polled only for
`window.SokobanChrome` (present as soon as the block parses) and drove the chrome with `ctx` null:
every `ctx.pushFeed` and `ctx.banner` was a silent no-op. The evidence screenshot from that run
shows all three frames still on the locker-room curtain with only the ribbon in the mirror. The
fixture now waits for the shell's own `data-replay-loaded="true"` (and fails immediately on
`data-replay-error`, naming it).

**Evidence — the two `canvas_text` lines from run 33246336750, job `99084495740`:**

```
Load the bundle in a real browser:
  {"loaded":true,"ms":281,"clock":"SOLVED 1/6 WEIGHT 1/12 · MOVE 63/200 · SCORE 1050143", …}
  soak: 10s of playback kept advancing ("0 / 430" -> "96 / 430" -> "120 / 430")
  canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
Drive the shipped chrome with a worst-case frame:
  {"loaded":true,"ms":545, …}
  canvas text: 25 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
```

The first line is still `0` and always will be — that step plays the real replay, whose board is
drawn in a Worker's OffscreenCanvas. The **fixture** step is now `25 drawn, 0 never inside`, and the
uploaded `fixture-evidence/viewer-smoke.png` shows the mirrored text beside each frame: the level
ribbon, the plan and deadlock feed lines, and the 140-rune remark wrapped over four lines at 360 px,
all inside the frame. That is the number checklist item 15 asks to read.

## F10 — artefacts the note names that are not in the tree — **no change**

Nothing is uncovered: the endcard-label assertions live in `tests/test_sokoban_viewer.nim:221-248`,
the tuning assertion in `tests/test_sokoban_events.nim:143-160`, `seatAlias`/`ladderResultsJson` in
`src/sokoban/sim.nim`. `ci.yml:117-119` runs `ls tests/*.nim`, so the absent shard files skip
nothing — every committed test file runs twice. Renaming files to match the note would move
assertions without adding one. Recorded as note-vs-tree divergence.

## F11 — the no-float grep now rejects `/` too; the sweep sizes stand

Fixed half: the grep the note's test 12 describes now also rejects `/`, with string literals
stripped and the two non-arithmetic spellings named explicitly (a module path in an `import`, and
`os`'s path-join on `FallbackLevelDir`) rather than ignored blindly. The seven modules pass as they
stand, so this closes the hole for the next line of code.
Unchanged half: `SweepSeeds`, `SampleStates` and the widened strength band. They are divergences
already recorded **in the code**, with the reason (`helpers.nim:11-17`: the note's 5 000-seed sweeps
are hours of CI, and `ci.yml` runs every test file in both debug and release). Checklist item 1's
"no test loosened" is about this run: `git log -p 464b2ab..HEAD -- tests/` contains no deleted
assertion, no widened tolerance and no skip — every test-file hunk in this round **adds** assertions
(F1, F2, F3, F5, F8, F9, F11, F12, F13, F15, F16, F17, F18, F19 all ship one).

## F12 — the replay parser range-checks its byte→enum reads

`DirectiveSource`, `ActionKind` and `Dir` now go through `readEnumU8`, which raises `SokobanError`
on an out-of-range byte exactly as the tier field already did. In a `-d:release` viewer build
(checks off) the old code produced an out-of-range enum that reached a `case` no branch covers.
The other half of F12 — that `replays.nim`/`replay_runtime.nim` are new implementations rather than
the note's "magic + game name only" fork — is **no change**: the note is internally inconsistent
there (it demands per-level XSB records and per-turn plan records that the starter's codec has no
place for), the module header documents the rewrite honestly, and checklist item 2 is satisfied and
tested (`test_sokoban_replay.nim:96-113` re-derives every tick's hash from the bytes).

## F13 — the tier-2 stream emits all eleven kinds

`Directive` and `Fallback` at the turn boundary; `Push` and the sim's own
`boxon`/`boxoff`/`deadlock`/`solved`/`failed` at the tick they happen, read from `sim.events` past a
per-tick mark before the broadcast drains them and copied so the broadcast still sees them
unchanged. New test asserts every declared `SimEventKind` has a `log.add` call site.

## F14 — cadence, speed chips and interpolation — **no change**

`ReplayFps = 24` / `FramesPerTick = 2` (12 ticks/s) is self-consistent across the code, its own
comment and `ci.yml`, and the CI replay (430 ticks ⇒ ~36 s) comfortably outlasts `--soak 10` —
confirmed again this run ("0 / 430" → "96 / 430" → "120 / 430"). `PlaybackSpeeds = [1, 2, 4, 8]` is
constrained by the inherited `chrome_common.js`, which maps a speed to a transport command char
through a fixed table over `{1,2,3,4,8,16}`: `0.5` is not expressible without editing the
byte-identical file that checklist item 14 forbids editing. Sub-tick interpolation is genuinely
absent; it is a presentation nicety, it touches the wasm render path that item 13 gates, and I would
not spend a viewer regression on it in a fix round. Residue, recorded.

## F15 — the deadlock is drawn, not only announced

The offending crate is now ringed in red and flashes twice on the **dead-square inset** — this
block's own canvas, and the panel this game repurposed for exactly this geometry — for 24 ticks
(~2 s at 12 ticks/s, two six-tick blinks), keyed to the event's own tick so it is identical live and
in replay, and cleared by every seek. The main board could not carry it: it is composited in the
Worker from the sim's sprite packet, and a deadlock **ends the level on the tick it fires**, so the
board is already the next level a frame later and a board-side flash cannot be held without a
presentation hold the compositor does not have. The banner, the feed line and the tallest, reddest
scrubber beat are unchanged.

## F16 — `results.names` carries a real name when the platform supplies one

The shipped player's registration blob has no `name` key, so the server now reads the name the
platform puts on the player socket URL — `/player?slot&token&name=`, the starter's own route
(`coworld-ctf`'s `playerIdentity`, `src/ctf/server.nim:471-475`) — and resolves in order:
registration blob → socket name → policy label. The alias stays in its own name space. Note this
does not change the CI scorebug (`ALPHA pusher SCORE …`): `docker_smoke.sh` dials without a `name`,
so the label fallback is correct there. The second commit (`9c1ab66`) is the same fix reading the
query param through `request.queryParams["name"]`, the accessor this file already uses, rather than
a `getOrDefault` overload the pinned mummy may not export.

## F17 — `game.docs` is `{"type":"text"}` with the real documents

Changed, deliberately, against the design note's §Packaging. Reasoning: checklist item 10 spells the
shape literally and the checklist is the definition of blocking; three shipped coworlds in this
fleet (babel, bullwhip, parley) use `text`; and the value is now the committed document itself, byte
for byte, pinned by `tests/test_sokoban_manifest.nim` to `README.md` and
`docs/{RULES,ACTIONS,LEVELS}.md`, so the manifest and the docs cannot drift. The URLs the `uri` form
carried are still in `game.runnable.source_url` and throughout the README. The starter's own `uri`
form is not wrong — it is simply not what the checklist names, and this is the cheaper side of that
disagreement to be on.

## F18 — `do` is exactly the four declared verbs

`move`, `seq` and `go` are gone, and an absent or empty `do` is **dropped** rather than becoming a
`wait`: that case invented an action out of an entry that failed to name one, which is precisely
what "invalid actions are dropped, never rewritten" exists to prevent in a game where one wrong push
is fatal. Still lower-cased before matching. New test drives all four rejected spellings.

## F19 — the settle and the artifact write are inside the fault guard

The tail (`writeStop` → `settle` → `finishEpisode`) is inside its own `try/except` that logs and
falls through to the shutdown grace and `quit(0)`, and the two `writeArtifact` calls inside
`finishEpisode` are now independent, so a failed replay upload no longer costs `results.json` — the
document the platform scores the episode from. New test pins the ordering and both failure logs.

---

## NOTED (not fixed)

* **The `ci.yml` baseline sweep with `--check`** the note describes (F6) is not wired; the `test`
  job asserts the shipped defaults against the recorded sweep instead.
* **Sub-tick interpolation** of the cog and the pushed crate (F14).
* **`disconnected`** is a legal `fallback.cause` that nothing produces. It is a permitted value, not
  a required one; a seat that drops mid-episode currently reports `timeout` or `transport_error`,
  which is what actually happened.
* **The inherited dead branches** `case 'kill'/'steal'/'return'/'capture'` in
  `replay_broadcast.html:2203-2206` still call `markBeat` for kinds this game's closed enum cannot
  emit. Unreachable inherited code; deleting it would edit the starter's prefix for no behavioural
  gain.
* **The CI scorebug still reads `ALPHA pusher`** (F16) because `docker_smoke.sh` dials the player
  socket without a `name`. That is the honest fallback, not a defect.

## A note on the pushed history

git-over-HTTPS is not usable from this sandbox — the token is base64-encoded inside the
`Authorization: Basic` header, so the egress swap never sees it and GitHub answers
`Invalid username or token` (the REST API works; `gh api repos/... --jq .permissions` reports
`push: true`). The commits were therefore recreated through the REST API
(`git/blobs` → `git/trees` → `git/commits` → `PATCH git/refs/heads/main`), one commit per finding,
in order.

The second push (the two follow-up commits) was given `origin/main` as its range base, and because
the API-created commits carry different shas from the local ones, `rev-list origin/main..HEAD`
replayed **the whole series a second time** on top of itself. The result: `main` carries two copies
of the fix series. The tip series (`1dd3edb … f31307a`, the shas in the table above) is the
authoritative one, `git rev-parse main^{tree}` equals the local tree exactly, the cumulative diff
`464b2ab..f31307a9` is exactly the intended change, and CI is green on that tip. I did **not**
force-update the ref to tidy it: rewriting pushed history is off-limits, and the duplicate is
cosmetic. Reading `git diff 464b2ab..main` or the top 20 commits gives the intended story.
