# r2 fixes — lux-ai
Head: `88cc3f751606cb5f48bc535b349dc23b1339c4a1` (`main`)
CI: https://github.com/Metta-AI/cogame-lux-ai/actions/runs/33096195543 — **success**
(`headSha 88cc3f75…`, jobs `test` / `docker-smoke` / `wasm-viewer` all success).

| finding | disposition | commit | files |
|---|---|---|---|
| B1 — playback ignores the recorded lobby length | fixed | `c74b230` | `src/lux/replays.nim:125-137,177-183`, `tests/test_lux_replay.nim:65-110,150-179` |
| N1 — the `.tiny` five-line commander band is inert | fixed | `49ca7e5` | `scripts/lux_block.html:109-121`, `client/replay_broadcast.html:1860-1872` (regenerated), `tests/test_lux_viewer.nim:246-257` |
| N2 — the load-time pre-scan discards its hash verdict | fixed | `47f5cf0` | `src/lux/replays.nim:333-338`, `tests/test_lux_replay.nim:206-221` |
| N3 — the node gate hash-checks a prefix (tick 348 of 408) | fixed | `88cc3f7` | `.github/workflows/ci.yml:365-379` |
| N4 — `db780f6` changes 429 behaviour as well as 403 | DISPUTED (no defect) | — | `src/lux/llm.nim:181-187` |
| N5 — r1's declined advisories are unchanged at head | declined again (out of scope) | — | — |

Each commit was published to `main` through the GitHub API (blobs → tree →
commit → non-forced ref update), one API commit per finding, and each remote
tree sha was compared against the local `git rev-parse <commit>^{tree}` before
the ref moved — all four matched.

## B1 — playback honours the recorded lobby, not `startWaitTicks` (`c74b230`)

**Reproduced first, at the review's head sha.** I built the reviewer's
`/tmp/lobbyrepro.nim` against `66b5d3b` and got its table exactly:

```
joinTick=0   | live start 48  || playback startTick 48 mismatchTick -1  cityTiles [18, 1]
joinTick=48  | live start 48  || playback startTick 48 mismatchTick -1
joinTick=49  | live start 49  || playback startTick 48 mismatchTick 49  cityTiles [14, 1]  (live [18, 1])
joinTick=120 | live start 120 || playback startTick 48 mismatchTick 49  cityTiles [17, 3]  (live [18, 1])
joinTick=288 | live start 288 || playback startTick 48 mismatchTick 49  cityTiles [ 7, 2]  (live [18, 1])
joinTick=10, one seat only | live start 2400 || playback startTick 2400 mismatchTick -1
```

**What the code did.** `simFromReplay` (`replays.nim:125-131` at `66b5d3b`) set
`seats[seat].joined = true` for every join record without reading `join.time`,
so the `Lobby` branch of `sim.step` (`sim.nim:162-173`) — which playback, unlike
the live loop, does execute — always fired at `startWaitTicks` (48). The
recorded `InputStart` was then a no-op (`beginPlaying` returns early once
`phase != Lobby`), and every directive landed `T - 48` turns late.

**What it does now.** The seats are seated at the tick their join record was
written: `simFromReplay` restores only `name`/`slot` (neither is hashed, and the
pre-start frames still show the names), and `applyRecordsAt` marks
`joined`/`connected` for every join whose `tickOfTime(join.time)` is the tick
being applied — before the input stream, mirroring the live loop's
`syncSeats()`-then-lobby-test order (`server.nim:358-372`, `:484-502`). This is
the starter's semantics: coworld-ctf re-applies joins at their recorded time
(`/workspace/starters/coworld-ctf/src/ctf/replays.nim:383-390`) and builds the
playback sim with no seats seated (`replay_runtime.nim:22`).

Playback's start is therefore the recorded `InputStart` tick in every case, and
the auto-start branch can no longer pre-empt it: at tick `T` the join records
and `InputStart` are applied *before* the hash comparison, which is the same
instant the writer recorded the hash (`server.nim:496-510` vs
`replays.nim:225-228`).

**Evidence.**
- The same repro against the fixed tree: `mismatchTick -1` and `cityTiles
  [18, 1]` at join ticks 0, 47, 48, 49, 120, 288 and on the one-seat timeout
  path, with `playback startTick` equal to the live start tick in all seven
  rows.
- The join tick survives the codec exactly: `tickOfTime(tickTime(t, ReplayFps))
  == t` for every `t` in `0 .. 5000` (checked by execution — well past
  `lobbyJoinTimeoutTicks = 2400`).
- New test, `tests/test_lux_replay.nim` — *"a lobby LONGER than startWaitTicks
  re-derives frame by frame"*: `recordWithLobby` records through `server.nim`'s
  own loop (join records at the tick the sockets appear, one lobby hash per
  waiting tick, `InputStart` at the tick `Playing` began) for seats connecting
  at ticks **0, 49 and 120**, with `startWaitTicks` at its **shipped 48** — the
  test asserts `config.startWaitTicks == 48` so it cannot be neutered the way
  `tests/helpers.nim`'s `startWaitTicks = 0` masked this. Each episode is
  re-derived through `initReplayRuntime` with `mismatchQuit = true`, so *any*
  divergent tick raises; it then asserts `hashMismatchTick == -1`,
  `replayStartTick() == max(48, joinTick)`, the final `gameHash()`, the turn
  count, the end rule and both city-tile counts against the recording.
- The test is a real gate: reverting only the two-line source change fails it
  with `Unhandled exception: replay hash mismatch at tick 49 [LuxError]`.
- CI (this run) shows it green in all four shard passes, debug and release, e.g.
  log line 522 `[OK] a lobby LONGER than startWaitTicks re-derives frame by
  frame`. The wasm path is the same code (`replay-viewer/lux_replay.nim:69-83` →
  `initReplayRuntime` → `simFromReplay`/`stepReplay`): the wasm gate re-derived
  the docker-smoke episode with `lux_mismatch_tick == -1` (log 5460), and
  docker-smoke's own summary is unchanged at `complete full_time [18, 1] 360
  turns` (log 3592).

**Checklist item 2 — replay re-derivation.** The property now holds for any
join timing, not only for seats that connect inside 48 ticks.

No `GameVersion` bump: nothing in the rules, the hash mix order or the record
vocabulary changed — this is playback-side only, the recorded bytes are
identical, and every committed `.replay` fixture still re-derives
(`test_lux_gameversion`, `test_lux_replay` green).

## N1 — the `.tiny` band re-declares `--lux-say-band` (`49ca7e5`)

`#stage.tiny` overrode `--lux-note-lines: 5`, but `--lux-say-band` is declared
at `:root`, and a custom property is substituted at the computed-value time of
the element it is *declared* on — descendants inherit the already-resolved
four-line token. The override was inert, exactly as the review measured.

Fixed by re-declaring `--lux-say-band` inside the `#stage.tiny` rule, where
`--lux-note-lines` is 5. The source of truth is `scripts/lux_block.html`;
`client/replay_broadcast.html` was **regenerated** with
`python3 scripts/fork_broadcast_page.py /workspace/starters/coworld-ctf
client/replay_broadcast.html`, not hand-edited, so item 14's provenance is
intact (the viewer test's byte-identity pins on `chrome_common.js` /
`broadcast_core.js` and the "page is the starter's, with ONE appended game
block" test are green).

Evidence — measured on the **shipped page** in headless chromium at a 360 px
viewport, reading `#killfeed` with `#stage` toggled to `.tiny`:

| | `--lux-note-lines` | `--lux-say-band` | `min-height` |
|---|---|---|---|
| before | 5 | `calc(4 * 1.35 * 7 * 1px + 18 * 1px)` | 115.8 px |
| after | 5 | `calc(5 * 1.35 * 7 * 1px + 18 * 1px)` | 125.25 px |

(the non-`.tiny` band is unchanged at 115.8 px in both.) The CI text-fit gate is
still green with the same numbers as the r1 head: `text fit: {"clipped": 0,
"failures": [], "measured": 48, "note_runes": 160, "notes": 12, "outside": 0,
"short": 0, "widths": 3}` and `commander band OK: 48 boxes measured, 12 full-cap
notes inside #stage at 360/620/1280 px` (log 5539, 5543). Regression guard:
`tests/test_lux_viewer.nim`'s "the commander band is sized from the server's own
note cap" now pins `--lux-note-lines: 5` **and** the `--lux-say-band`
re-declaration inside the `#stage.tiny {` block. Checklist item 15.

## N2 — the pre-scan's verdict reaches the player (`47f5cf0`)

`runScan` hash-checked the whole episode through a throwaway `scanner`
`ReplayPlayer`; `checkReplayHash` wrote `hashValidationFailed` /
`hashMismatchTick` onto that scanner and nothing copied them out. Three lines
now carry the verdict onto the player after the walk. Nothing else changes:
`mismatchQuit` is still applied only to the presentation player (so a corrupt
replay still *plays*, as the wasm host wants), the scan is the same `stepReplay`
the presentation runs, and a clean episode still reports `-1`.

Evidence: the `sim_fault` test now asserts `player.hashValidationFailed` and a
non-negative `hashMismatchTick` **before the first presentation frame**, and
that playback later reports the same tick; removing the three-line carry fails
it (`Check failed: player.hashValidationFailed`). Green in CI (log 524).

A useful side effect for N3: the wasm smoke's `lux_mismatch_tick()` check made
immediately after `lux_load_replay` now covers the whole recorded chain, because
`initReplayRuntime`'s pre-scan walks the whole episode.

## N3 — the wasm gate advances the whole episode (`88cc3f7`)

`node tools/wasm_replay_smoke.cjs … 300` advanced a 408-tick duel to tick 348,
leaving the last sixty ticks and the settle tick outside the node gate, and the
constant would go stale the moment the lobby is longer or `maxTurns` moves. The
budget is now read from the replay itself — `python3 tools/replay_summary.py
"${replay}" | … ["tickCount"]`, the same summariser the docker-smoke job already
runs on this file — which is always at least `maxTick - startTick`, so the walk
reaches the final tick and the post-loop `lux_mismatch_tick` check covers the
full span. The step also now fails loudly when the artifact contains no replay
instead of invoking the smoke with an empty path.

Evidence, this run's `Native <-> wasm hash gate` step: `advancing 408 frames
(the replay's whole recorded span)` (log 5459) and `ok: loaded episode.replay,
advanced 408 frames (779066 packet bytes, heap 16 MB)` (log 5460) — previously
300 frames / tick 348. No script change was needed; `wasm_replay_smoke.cjs`
already takes the frame count as `argv[4]`.

## N4 — DISPUTED (nothing to fix)

The review's own text says this "matches the note; recorded so it is not
re-filed". Confirmed independently: the design note asks for exactly this
behaviour — `docs/plans/2026-08-27-lux-ai-design.md:382` "`tryNextBedrockModel`
on 401/403 'Model access is denied' **and on 429**" — and `llm.nim:181-187`
implements precisely that: a 429 rotates to the next candidate, and only a 429
with nothing left to rotate to sets `client.throttled`, which `decide.nim:266-271`
reads as "skip the retry". Every wait remains bounded by `attempt1Ms` /
`retryMs`, so the item-5 arithmetic pinned by `tests/test_lux_engine.nim:31-58`
is untouched. Changing it would move the code *away* from the note. No commit.

## N5 — declined again (not this round's scope)

N5 records that four r1 advisories (`episodeFinished` unreferenced by the
server; the cart hand-off before the night policy; `build: "city"` skipping the
research check; the whole-reply cap in runes) are unchanged at head. They were
declined in r1, none is on the acceptance checklist, and none is named in this
round's brief; changing rule order or the reply cap now would be a behaviour
change outside the review's blocking scope. No commit.

## NOTED (not fixed)

- `tools/ci/check_gameversion.sh:31` still reads `CONST_FILE="src/ctf/sim_types.nim"`
  — the starter's path. The command AGENTS.md documents therefore always fails:
  `tools/ci/check_gameversion.sh origin/main` → `::error::could not read
  GameVersion from src/ctf/sim_types.nim … exit 1`. Nothing in `ci.yml` invokes
  it (only `tests/test_lux_gameversion.nim:42` asserts it exists and is
  executable), so it is not a CI hole, but the GameVersion collision guard the
  script exists to provide is inoperative. Not in this round's review; left
  alone.
