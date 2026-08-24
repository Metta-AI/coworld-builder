# r1 fixes — grid-wars

Head: **ae1f3ea99eb91acda05d0603847eea242bb8a98b** (`main`)
CI: https://github.com/Metta-AI/cogame-grid-wars/actions/runs/32747821831 — **success**
(`test`, `docker-smoke`, `wasm-viewer` all green; run id 32747821831, head_sha
`ae1f3ea99eb91acda05d0603847eea242bb8a98b`).

Two fixer legs produced this head. Commits `67b6e28..e385a8b` (13 of them) were pushed by the
earlier leg at 13:03–13:04Z and were verified here **from `git log -p`, not from their commit
messages**; commits `b4e0c5d`, `0cfa867`, `ae1f3ea` are this leg's, covering the three findings
that had none (N7, N11, N12).

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `67b6e28` | `src/gridwars/gwl.nim:120-138,266`, `src/gridwars/llm.nim:161,358,443,451,455,465`, `src/gridwars/sim.nim` (private copy deleted), `tests/test_gwl.nim:92-111`, `tests/test_bot.nim:208-222`, `tests/test_replay.nim:79-111` |
| B2 | fixed | `32148ba` + `86b45b8` | `src/gridwars/gwl.nim:38-45,89-104,1084-1145,1187-1440`, `src/gridwars/types.nim:15,60`, `src/gridwars/sim.nim:72,107-160`, `src/gridwars/server.nim:460`, `replay-viewer/gridwars_replay.nim:35`, `tests/test_gwl.nim:332-367`, `tests/test_replay.nim:143-182` |
| B3 | fixed | `5efef8d` | `data/warriors/painter.gwl`, `tools/tune_painter.nim` (new), `tests/test_bot.nim:65-92`, `coworld_manifest_template.json:302`, `docs/plans/2026-08-24-grid-wars-design.md:424` |
| N1 | fixed (note, not code) | `765bf17` | `docs/plans/2026-08-24-grid-wars-design.md:146` |
| N2 | fixed (note, not code) | `7410b65` | `docs/plans/2026-08-24-grid-wars-design.md:154` |
| N3 | fixed (note, not code) | `7c20dd0` | `docs/plans/2026-08-24-grid-wars-design.md:780` |
| N4 | fixed | `ae7ce4b` | `.github/workflows/ci.yml:316-327` |
| N5 | fixed | `885d1cb` | `src/gridwars/llm.nim:284-287`, `coworld_manifest_template.json:294` |
| N6 | fixed | `cd1e053` | `src/gridwars/sim.nim:953-958`, `tests/test_sim.nim:404-418` |
| N7 | **fixed (this leg)** | `b4e0c5d` | `src/gridwars/server.nim:1-16,64-68,390,445-453`, `src/gridwars.nim:1-4,31-34`, `client/replay.html` (deleted), `client/renderer.js:10-14`, `coworld_manifest_template.json:280`, `README.md`, `tests/test_viewer.nim:91-134,137-144` |
| N8 | fixed | `d06c06a` | `tools/ci/docker_smoke.sh:22-29,57-58` |
| N9 | fixed (note, not code) | `e385a8b` | `docs/plans/2026-08-24-grid-wars-design.md:1064` |
| N10 | fixed | `1ed9b7b` | `tests/test_replay.nim:214-223` |
| N11 | **fixed (this leg)** | `0cfa867` | `src/gridwars/sim.nim:1047-1099` (buildFrames/liveStateJson), `tests/test_replay.nim:225-252` |
| N12 | **fixed (this leg)** | `ae1f3ea` | `client/chrome.css:588-597`, `tests/test_viewer.nim:85-95` |
| N13 | fixed | `b9bde63` | `tests/test_bot.nim:38-46` |

No finding was disputed and none needs a design change.

---

## B1 — captured error text cut on byte boundaries (checklist item 9)

**Was:** `gwl.nim:243` quoted one *byte* of the offending character (`$c`, a `char`), and
`llm.nim:362,448,456,461,470` sliced the model reply and the API error bodies at raw byte
offsets. Those strings travel `decideAll.why` → `fallbackSubmission.rejected` →
`submit.compileError` → `replayJson`, and `escapeJsonUnquoted` emits every byte ≥ 0x20 raw, so a
split character reached the `.replay` file (the reviewer measured `validateUtf8 = 845`).

**Now:** `cutRunes` lives once, in `gwl.nim:120-129`, and is the single rune-safe truncation:
`llm.nim`'s `cleanText` calls it, `sim.nim`'s private copy is gone, and the four `llm.nim` byte
slices are `cutRunes(...)` calls. The lexer quotes the **whole** character at the offending offset
(`charAt`, `gwl.nim:130-138`) and escapes `\xNN` when the byte is not valid UTF-8 at all.

**Evidence:** three new tests, all green in run 32747821831 —
`[OK] an unexpected character is quoted whole, never as a split byte` (test_gwl),
`[OK] the quoted excerpt is cut on runes at every offset` (test_bot: sweeps pad 150..170 across
the 160-rune boundary and asserts `error.msg`, `cleanText(...)` and
`fallbackSubmission(...).rejected` all `validateUtf8() == -1`), and
`[OK] captured error text reaches the replay on rune boundaries` (test_replay: plays a round whose
four submits all carry captured error text, asserts the replay bytes validate and that seat 0's
`compileError` contains the em dash whole).

## B2 — VM numbers were platform `int` (32-bit under `--cpu:wasm32`) (checklist item 2)

**Was:** `stack/globals/locals/arrays`, the literals, `GwlAction.dx/dy` and every overflow check
were Nim `int`. `replay-viewer/config.nims:13` builds `--cpu:wasm32`, where `int` is 32 bits, so a
warrior computing `2000000000 + 2000000000` ran on the server and faulted in the browser —
different board, different digest, `replayMatch` raises, `data-replay-error` on a replay the
server considers valid.

**Now:** `GwlValue* = int64` (`gwl.nim:38-45`) is the machine's one numeric type, everywhere:
consts, stack, globals, locals, arrays, `parseBiggestInt` literals, `GwlAction.dx/dy`;
`addChecked`/`subChecked`/`mulChecked`, `div`/`mod`/unary minus/`abs` compare against
`high(int64)`/`low(int64)`; `check`/`who` test the 9×9 window without `abs` (which has no answer
for `low(int64)`) and narrow to a board coordinate only after the test; `sim.nim:627-629` narrows
`move`'s dx/dy after the decision pass has bounded them to {−1,0,1}. The second commit closes the
same hole on the seed path — `GameConfig.seed`, `GameEvent.seed`, `RoundRecord.seed` and `newVm`
are `int64`, read back with `getBiggestInt` in both the server and the wasm loader — and replaces
the overflowing `seed * k + c` mixing with `mixSeed` (uint64 multiply masked into the
non-negative half), which is defined, identical on x86-64 and wasm32, and bit-identical to the old
value below the overflow point.

**Evidence:** `[OK] the machine's numbers are int64 on every target, not platform int` (a
`static: doAssert sizeof(GwlValue) == 8`, `2000000000 + 2000000000 == 4000000000`, `shl(1,40)`,
the int64 overflow boundary, and a `check()`/`move()` offset past 2³¹ that is not truncated into
range) and `[OK] a league-sized seed survives the log and stays load-bearing` (seed 2147483647,
`roundSeed > high(int32)`, survives the event round-trip and re-derivation, and cutting it to 32
bits — what the browser would have done — yields a different digest). Both green in run
32747821831; the `wasm-viewer` job in the same run built the module and played it
(`{"loaded":true,...}`).

## B3 — `painter` lost to the `sentry` fallback (checklist item 7, last sentence)

**Was:** `tests/test_bot.nim:65-92` *recorded* that painter loses (sentry +3.9 vs painter −3.9)
instead of asserting the note's claim; painter's parameters were the note's guesses.

**Now:** `tools/tune_painter.nim` is the grid harness: it sweeps the turn-run length (6..40), the
rival trigger distance (1 or 2 cells) and the bomb cadence (3/6/12 ticks), plays each candidate
four-seated against `sentry` and against `bomber` over the assertion seeds 1..10 **and** a held-out
11..40, rejects any candidate with a fault, stall, illegal action or refused bomb, and ranks by the
**worse** of the two seed sets. The kept pick (run 22, two-cell trigger, at most one bomb per fuse)
is in `data/warriors/painter.gwl`, in the manifest's `warrior-language.md` page and in the note.
`test_bot.nim` now asserts what the note claims: painter beats sentry on mean score over ten seeds
by more than 20 (measured +39.7), and again on held-out seeds 11..20 with the seats swapped. The
pre-existing bomber-beats-painter assertion is **unchanged** and still passes.

**Evidence:** `[OK] painter beats the sentry fallback on mean score over ten seeds` and
`[OK] the two shipped fillers are decisively ordered over ten seeds`, both green in run
32747821831. The rest of item 7 (`reason == "complete"`, zero faults/stalls/illegal/refused,
< 2000 ms) was already asserted and still is.

## N1, N2, N3, N9 — note↔code divergences resolved in the note

Each of these four is a case where the code is right and the design note was the stale half; the
commits change `docs/plans/2026-08-24-grid-wars-design.md` and no code. Verified from the diffs:

- **N1** `765bf17`: the builtin table now orders `FOG` before `BOMB`, which is what
  `gwl.nim:1143-1157` does, what the Deviations row already said, what the GWL reference handed to
  every model says (`llm.nim:212-216`) and what `tests/test_gwl.nim:346-353` pins. Partial
  observability winning over everything is also the rule that cannot leak information.
- **N2** `7410b65`: `BOMBCOST` is documented as the episode's configured `bombCost` (which is what
  `gwl.nim:1391` pushes and what the prompt already said), not a frozen 12 — a warrior testing
  `energy() >= BOMBCOST` stays correct at any setting of the 0..60 knob.
- **N3** `7c20dd0`: the `/global` cadence sentence now describes the sends the server actually
  makes (start, after each round's four submits, deadline check, finish). The promised
  per-elimination / per-25-tick sends cannot exist in this architecture: the battle runs
  synchronously inside the fourth `submit` and resolves 400 ticks in ~30 ms, so they would be a
  burst inside one call rather than an animation. The per-tick detail is in the replay frames.
- **N9** `e385a8b`: the note's §Tests now describes the template's `ci.yml` (each `tests/*.nim`
  run twice, debug and `-d:release`, in the job named `test`; `docker-smoke` builds the production
  image from source in its own job, which is checklist item 12's "freshly built binary in the same
  run"; `wasm-viewer` does `needs: docker-smoke`).

## N4 — viewer smoke now runs with `--soak 10` (checklist item 13)

`ae7ce4b` adds `--soak 10` to the `viewer_smoke.mjs` invocation (`ci.yml:316-327`) with the reason
in a comment (the fixture is ~310 frames ≈ 26 s of playback, so a 10 s window sits inside
uninterrupted play). **Evidence:** run 32747821831's `Load the bundle in a real browser` step
printed `soak: 10s of playback kept advancing` and
`{"loaded":true,"ms":292,"clock":"R1 / 2 · TICK 108 / 150",...}` — the clock is mid-battle, which
is the freeze check the note pins.

## N5 — the prompt now says when a bomb actually detonates

`885d1cb` rewrites the system-prompt bullet (`llm.nim:284-287`) and the manifest's `rules.md` line:
a bomb is planted with fuse `MAXFUSE` (5) and the fuse drops in the same tick, so a bomb planted at
tick t detonates at tick t+4 — which is what `sim.nim:598-599`/`:638-640` do and what
`tests/test_sim.nim:241` asserts. No sim change, so no digest moved.

## N6 — a reply with no `notes` now clears them

`cd1e053` removes the `if notes.len > 0:` guard at `sim.nim:953-958`, so `banner` and `notes` are
both overwritten by every submission ("banner/notes missing ⇒ empty", design.md:371) and a seat is
never fed prose it did not write this round. **Evidence:**
`[OK] a reply with no notes clears them; it never carries last round's` (round 1 submits notes and
banner, round 2 submits neither, both are empty in the round-2 record).

## N7 — the `/client/replay` pod path is gone (checklist item 3)

**Was:** `server.nim:453` served `client/replay.html` at `/client/replay`, `server.nim:458` served
the replay payload at `WS /replay`, `runReplayServer` started that pair as a mode of the game
container, and `coworld_manifest_template.json:280` advertised "`/client/replay` plays a recorded
episode". Item 3 reads "No `/client/replay` pod path **anywhere**", and the playbook is blunter:
"Never declare a `/client/replay` live-server viewer."

**Now (commit `b4e0c5d`):** both routes, `replayUpgradeHandler`, `replayPayloadGlobal`,
`runReplayServer` and its only caller-helper `configFromReplay` are deleted; `client/replay.html`
is deleted; `buildRouter` no longer takes a `replayMode` flag. `src/gridwars.nim` no longer starts
a replay server — a container handed a replay payload exits non-zero saying that the static bundle
plays recorded episodes. The manifest's global-protocol text, the server's endpoint list, the
renderer's header comment and the README say the same. What item 3 asks for is untouched and still
true: `game.replay_viewer = {"bundle": "static-replay-viewer"}`, `tools/build_replay_viewer.sh`
present and `100755`, and the bundle contacts nothing but the `?replay=` URL and its own assets.

**Evidence:** new test `[OK] there is no /client/replay pod path anywhere` (asserts
`client/replay.html` does not exist and that `/client/replay` appears in neither the entrypoint,
the server, the live pages, the renderer nor the manifest, and that `server.nim` mentions no
`"/replay"` route), green in run 32747821831. The `docker-smoke` job in the same run still
completes an episode against the live container (`smoke OK: seats=4 results=322B replay=9090B
reason=complete`), so removing the route did not disturb `/healthz`, `/client/global`,
`/client/player`, `/global` or `/player`; the `wasm-viewer` job still loads the bundle
(`"loaded":true`).

**Test bookkeeping (item 1, "no test loosened"):** the page-id loop used to iterate
`["client/replay.html", "replay-viewer/index.html"]`; the first file no longer exists, so the loop
now iterates the one replay page that does, and the same list in the zoom-panel test lost the same
entry. No assertion about a surviving file was deleted or weakened, and the commit adds strictly
more assertions than it drops.

## N11 — the live snapshot no longer rebuilds every played battle

**Was:** `snapshotJson` → `liveStateJson` → `frameStates` → `buildFrames` re-ran `runBattle` with
`sink.want = true` for **every** played record — ~405 JSON frames per round — and returned
`frames[^1]`, one frame. Work proportional to `rounds²`, paid on every round boundary and on every
`/global` connect.

**Now (commit `0cfa867`):** `buildFrames` takes `fromRound`. A round before it contributes only its
series row and its share of the running score — both already in the played record
(`record.stat[seat].roundScore`) — so its battle is not re-run and its frames are not built.
`liveStateJson` asks for the last round only; `frameStates` (the replay and test path) still builds
every round, so nothing about item 2's frame-by-frame re-derivation changes.

**Evidence:** new test `[OK] the live snapshot is the tail frame, built from the last round only` —
after **every** round of a three-round episode it asserts the snapshot's `series` (one row per
played round), `grid`, `bombs`, `corpses`, `blast`, `tick`, `focus`, `ticks` and every per-seat
battle field (`score`, `raw`, `tiles`, `peakTiles`, `energy`, `alive`, `x`, `y`, `kills`,
`selfKills`, `deathCause`) equal the tail frame of the **full** build. Same frame, less work.
Green in run 32747821831.

## N12 — a seat-attributed beat marker now takes its seat colour (checklist item 14(d))

**Was:** `markGridWarsBeat` (`renderer.js:1016-1018`) adds `seat<N>` to the button, but `.seatN`
(`chrome.css:205-209`) is one class and `.beat-marker.submit` (`chrome.css:581-586`) is two, so the
kind rule set `--tc` every time and the seat class coloured nothing.

**Now (commit `ae1f3ea`):** the appended chrome block carries eight two-class rules —
`.beat-marker.submit.seatN` and `.beat-marker.roundend.seatN` for N = 0..3 — so the beats that are
*about a seat* take that seat's colour (four submit marks a round are otherwise four identical
marks). `kill`, `fault` and `idle` deliberately keep their **cause** colour (red / violet / ghost),
which is the colour the kill feed uses for the same event and the only thing that tells a kill from
a fault at a glance; their geometry already differs.

**Evidence:** new test `[OK] a seat-attributed beat is coloured by its seat` (asserts the eight
rules exist and that the renderer still emits the class they match), green in run 32747821831. The
pre-existing "every beat kind the renderer emits has a rule" test still passes, so no kind became
an invisible marker. The starter-prefix pin (`test_viewer.nim:44-52`, 11964 bytes + FNV digest) is
untouched: the rules are appended inside the Grid Wars block.

## N13 — the two copies of `sentry` are tied together

`b9bde63` adds `check SeedScript == warriorLines(skSentry)` to `test_bot.nim`, so the round-1 seed
script and the fallback warrior cannot drift apart unnoticed. **Evidence:**
`[OK] the round-1 seed script IS the sentry warrior`, green in run 32747821831.

---

## Item 1 — "no test loosened", verified from the diff

`git log -p e385a8b~13..ae1f3ea -- tests/` over both legs: every change to `tests/` is an addition
or a strengthening.

- `test_gwl.nim`, `test_sim.nim`, `test_bot.nim`, `test_replay.nim`: new tests only, except
- `test_replay.nim:214-223`, where `check $replayed[^1] == $frames[^1]` (the last frame) became a
  loop over **every** frame — strictly stronger (that is N10);
- `test_bot.nim:65-92`, where the comment explaining why painter-vs-sentry was *not* asserted was
  replaced by an assertion that it holds; the file's existing
  `check bomberTotal / 20.0 - painterTotal / 20.0 > 10.0` is byte-identical to before;
- `test_viewer.nim`, where two path lists lost the entry for the file this round deleted
  (`client/replay.html`) and gained two new tests.

No `skip`, no widened tolerance, no deleted assertion, no removed test file. All six test files ran
twice (debug and `-d:release`) in run 32747821831.

## NOTED (not fixed)

- The repo's copy of the design note (`docs/plans/2026-08-24-grid-wars-design.md`) is no longer
  byte-identical to `runs/2026-08-24-grid-wars/design.md`: the first leg's four doc commits
  (N1, N2, N3, N9) and B3's parameter update edited the repo copy only. The run's `design.md` is
  the fixer's read-only input, so it was left alone.
- The repo note's route list (design.md §Server) still includes `/client/replay`, which N7 removed
  from the code. Code, manifest, README and tests agree; only that one note line is stale.
- `tools/ci/viewer_smoke.mjs` prints `soak: 10s of playback kept advancing (null -> null -> null)`
  — the soak's per-sample tick readout is `null` for this game even though the check passes on the
  clock string. Cosmetic, in the shared template (byte-identical to
  `templates/tools/ci/viewer_smoke.mjs`), and out of this round's scope.
- The N5 prompt edit left one over-long line in `llm.nim`'s system prompt (a wrapped sentence
  joined onto the next). Cosmetic; the prompt text is correct.
