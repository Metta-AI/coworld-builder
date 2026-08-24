# r1 review — grid-wars

Repo: `Metta-AI/cogame-grid-wars` at `main` = **dbffed23da0d4f001151d6c7a3a2c0654fcb6955**
("ci: keep the placeholder gate clean"), cloned to `/tmp/review-grid-wars`.
Range: whole tree (7 commits, `29c9537..dbffed2`); diffed against the starter mount
`/workspace/starters/cogame-bullwhip` @ `a87cf75` for provenance.
Design note: `/workspace/coworld-builder/runs/2026-08-24-grid-wars/design.md` — byte-identical to
the repo copy `docs/plans/2026-08-24-grid-wars-design.md` (verified with `diff -q`).
Files read: 36. Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14).

**Evidence note.** Contrary to the design note's assumption (§Tests, design.md:1064 — "the sandbox
cannot run any of this locally"), this sandbox *does* have Nim 2.2.4 at `/root/.nimby/nim/bin/nim`
and the full package tree at `/root/.nimby/pkgs`. Findings B1, B2 and B3 below therefore carry
**executed** evidence, not just read code; every probe is quoted with its output. Nothing in the
repo was modified.

---

## Blocking

### B1 — Captured error text is cut on **byte** boundaries and reaches the replay as invalid UTF-8

- Where (the cuts):
  - `src/gridwars/gwl.nim:243` — `compileError(lineNo, "unexpected character '" & $c & "'")`.
    `c` is a `char`, i.e. **one byte**. Any non-ASCII character outside a comment (an em dash, a
    curly quote, `≥`) fails every lexer branch at `gwl.nim:213-243` (`isIdentStart` is
    `{'a'..'z','A'..'Z','_'}`, `gwl.nim:158`), so the message embeds a lone lead byte.
  - `src/gridwars/llm.nim:362` — `head = head[0 ..< 160] & "..."` in `extractJsonObject`: a raw
    160-**byte** slice of the model's reply.
  - `src/gridwars/llm.nim:448`, `:456`, `:461`, `:470` — `response.body[0 .. min(response.body.high,
    400)]`, `[… 300]`, `[… 300]`, `result[0 .. min(result.high, 160)]`: byte slices of API error
    bodies and of the model's text into the raised message.
- Where (the path from message to replay bytes), traced step by step:
  `llm.nim:518-527` (`why[index] = error.msg` on either a `GwlCompileError` or any
  `CatchableError`) → `llm.nim:529-532` (`fallbackSubmission(why[index])`) → `llm.nim:179-181`
  (`rejected: cleanText(compileError, 300)` — `cleanText`, `llm.nim:161-168`, only strips and
  *rune*-truncates when it is over the cap; it does not repair an already-split character) →
  `src/gridwars/server.nim:272-273` (`state.sim.submit(seat, …, decision.rejected)`) →
  `src/gridwars/sim.nim:939-942` (`compileError = cutRunes(rejected, 300)` — same no-op below the
  cap) → `sim.nim:956` (`event.compileError`) → `sim.nim:1131` (`result["compileError"] =
  %event.compileError`) → `sim.nim:1269-1283` (`replayJson`, the bytes the server writes with
  `writeArtifact`, `server.nim:174`). Nim's `escapeJsonUnquoted`
  (`/root/.nimby/nim/lib/pure/json.nim:674-689`) escapes only `"`, `\` and `<0x20`; every byte
  ≥ 0x20 is emitted raw, so the split byte survives into the `.replay` file.
- Observed (executed, not inferred). Probe 1, compiling a line with an em dash and recording the
  resulting message as a fallback's `rejected`:
  ```
  msg bytes: 32  validateUtf8: 30
  msg repr: "line 2: unexpected character '<0xE2>'"
  replay bytes: 3918  validateUtf8: 845      # -1 means valid; 845 is the first bad byte
  nim parseJson: OK (it does not validate utf8)
  ```
  Probe 2, the `extractJsonObject` cut, sweeping the padding so the 160-byte boundary lands inside
  a two-byte character:
  ```
  pad=158 msg.validateUtf8=-1  cleanText=-1
  pad=159 msg.validateUtf8=187 cleanText=187   <-- cut through 'é'
  pad=160 msg.validateUtf8=-1  cleanText=-1
  ```
  (`pad=159` is a refusal-style prose reply with no `{` in it — exactly the case
  `extractJsonObject` is written to report.)
- Checklist item: **9. Rune-safe truncation** — "Every string that reaches the replay (`say`,
  `notes`, prompts, **captured errors**) is truncated on **rune** boundaries." Also design.md:363-365
  ("Every string that reaches the replay is cut on rune boundaries (`cleanText`, ported): a byte cut
  through a multi-byte character produces replay bytes that render in a browser and fail a strict
  JSON parser").
- Why blocking: the produced `.replay` bytes are not valid UTF-8. `tests/test_replay.nim:58`
  (`check raw.validateUtf8() == -1`) is the assertion the design note points at, and it passes only
  because the fixture (`test_replay.nim:36-42`) feeds *valid* multi-byte text through the
  notes/banner/script caps — no test exercises the captured-error path. In the browser the bytes are
  decoded as UTF-8 by `fetch`/`TextDecoder` before `JSON.parse`, so the replayed string is silently
  corrupted, and a strict parser on the platform side rejects the artifact.
- Not affected (checked): `notes`, `banner` and `script` lines are all rune-cut
  (`sim.nim:844-851`, `sim.nim:863-864`, `llm.nim:161-168`); `faultText` is never truncated
  (`sim.nim:573-574` → `types.nim:37` → `statJson`) but can only contain ASCII, because the lexer
  admits no non-ASCII byte into an identifier or a literal.

### B2 — The GWL VM's numbers are Nim `int`, which is 64-bit on the server and **32-bit** in the wasm viewer

- Where: `src/gridwars/gwl.nim:81-88` (`stack*, globals*, locals*, arrays*: seq[int]`),
  `gwl.nim:1061-1106` (`addChecked`/`subChecked`/`mulChecked` compare against `high(int)` /
  `low(int)`), `gwl.nim:1243-1258` (`low(int) div -1`), `gwl.nim:1381-1390` (`shl`/`shr` accept a
  shift of 0..62). Nowhere in `gwl.nim` is a value typed `int64`.
- Where (the other target): `replay-viewer/config.nims:13` — `--cpu:wasm32`. Nim's own platform
  table gives that CPU `intSize: 32`
  (`/root/.nimby/nim/compiler/platform.nim:249`: `(name: "wasm32", intSize: 32, …, bit: 32)`), so
  `int`, `high(int)` and every overflow check in the VM are 32-bit inside the bundle and 64-bit in
  the game container.
- What the note says: design.md:117 — "**Integers only. No floats anywhere in the VM**, so the
  native server and the wasm viewer cannot diverge"; design.md:292 — "Floats … | Integers only | The
  wasm viewer re-derives every battle; float drift between x86 and wasm32 would desync the replay";
  design.md:1143 — "Numbers are int64 and that is the whole type system besides bool and int arrays."
  The pin is int64 precisely so the two targets agree.
- Observed (server side, executed). A warrior computing `2000000000 + 2000000000`:
  ```
  sizeof(int) = 8  high(int) = 9223372036854775807
  action = place  fault = 0
  ```
  *Inferred* (not executed — no emcc in this sandbox): on `--cpu:wasm32` the same expression trips
  `addChecked` (`gwl.nim:1062`), the VM faults with "integer overflow", the sim kills that warrior
  at the fault pass (`sim.nim:734-744`), the board diverges, `runBattle` produces a different
  `digest`, and `replayMatch` raises at `sim.nim:1247-1250` → `gridwars_replay.nim:56-58` sets
  `lastError` → `static_replay.js:96-99` calls `fail()` → `data-replay-error`. The viewer shows an
  error instead of the match, for a replay the server considers valid.
- Checklist item: **2. Replay re-derivation** — "Replaying the recorded events through the sim
  reproduces the recorded per-tick state frame by frame, and the viewer derives its display from
  that same re-derivation."
- Why blocking: the equality of server and viewer arithmetic is a *precondition* of item 2 and is
  what the note's int64 pin exists to guarantee; today it holds only for programs that stay inside
  ±2³¹. The GWL reference the model is handed advertises `xor`, `shl(a,b)`, `shr(a,b)` and
  `rand(n)` (llm.nim:220-221), i.e. exactly the operations a model reaches for when it writes a
  hash or a PRNG, so the range is reachable by an ordinary champion reply. Nothing in CI can catch
  it: the wasm smoke replays the docker-smoke episode, which is all-scripted (painter/bomber/sentry
  never exceed 32-bit).
- What would settle it either way: type the VM's values `int64` (and `high(int64)` in the checks),
  or add a test that runs the same program through the wasm build and the native build and compares
  the digest.

### B3 — `painter`, the note's "strong baseline", loses to the `sentry` fallback; `test_bot.nim` records this instead of the assertion the note specifies

- Where: `tests/test_bot.nim:65-92`. The test is titled "the two shipped fillers are decisively
  ordered over ten seeds" and asserts `bomberTotal/20 > painterTotal/20` and a gap `> 10.0`. Its
  comment (lines 74-82) states: "NOT asserted, deliberately: the design note claims painter is the
  strong baseline and beats `sentry`. With the note's VERBATIM scripts it does not, and cannot …
  Measured over ten seeds: sentry +3.9 vs painter −3.9".
- Observed (executed). Reproducing the measurement independently, four seats
  `[painter, sentry, painter, sentry]`, 10 seeds, 1 round of 400 ticks:
  ```
  painter vs sentry, mean over 10 seeds: painter=-3.9 sentry=3.9
  bomber (vs painter) mean=30.8
  ```
  The cause is visible in the shipped sources: `data/warriors/painter.gwl:32` turns after `run == 6`
  (a 24-cell box) where `data/warriors/sentry.gwl:16` turns after `run == 8` (a 32-cell box), and
  painter's extra clause (`rival()` → `bomb()`, painter.gwl:20-21) never fires because nothing comes
  within one cell. Both files are the design note's listings **verbatim** (design.md:426-463 and
  490-511 — I diffed them line by line).
- What the note says: design.md:424 — "**`painter`** (the strong baseline; a prompt has to beat
  it)"; design.md:513-515 — "`tests/test_bot.nim` asserts … that `painter` beats `sentry` on mean
  `score` over ten seeds — a baseline that cannot beat the fallback is not a partner worth beating."
  Neither statement holds at this sha.
- Checklist item: **7. Scripted baseline plays full episodes legally** — specifically its last
  sentence, "**The baseline's parameters were tuned with a grid harness, not guessed.**" The
  parameters (`run == 6`, `mod(step,3)`, the one-cell rival test) are the note's guesses carried
  over unchanged; the harness was run (the numbers in the test comment, which I reproduced) and its
  result was *reported* rather than used to tune.
- Why blocking: `painter` is one of the two fillers a champion is seated against in
  `tools/ci/policies.json:17-23` and one of the two published player runnables
  (`coworld_manifest_template.json:330-350`), and it occupies a certification seat
  (manifest:459-461). A filler weaker than the never-seated fallback makes the ladder's "beat the
  baseline" signal weaker than intended.
- The rest of item 7 **is** satisfied: `test_bot.nim:38-63` runs four seats of each baseline over
  four seeds to the natural end and asserts `reason == "complete"`, zero faults, zero stalls, zero
  illegal actions, zero refused bombs, and `< 2000 ms`.

---

## Non-blocking

### N1 — `check()` evaluates FOG **before** BOMB/CORPSE, so a bomb outside the 9×9 window reads `FOG`
- Where: `src/gridwars/gwl.nim:1111-1123`. `if abs(dx) > FogRadius or abs(dy) > FogRadius: return
  ValFog` comes first; bomb, then corpse, then owner.
- The note's builtin table (design.md:146) orders it the other way: "`BOMB` (−1) if the cell holds a
  live bomb; else `CORPSE` (−2) …; else `FOG` (−3) if `abs(dx) > 4 or abs(dy) > 4`". Inside the
  window the two orders are identical; outside it they differ.
- The code's own comment (gwl.nim:1112-1115) cites the note's Deviations row (design.md:291,
  "`check`/`who` see a 9×9 window; beyond is `FOG`") as the authority, the reference the model is
  given documents the implemented behaviour (llm.nim:212-216), and `tests/test_gwl.nim:346-353`
  locks it in with a bomb ten cells east. So the note is internally inconsistent and the code
  follows the partial-observability half of it. Reporting the divergence, not a preference.

### N2 — `BOMBCOST` is the episode's configured `bombCost`, not the constant 12 the note pins
- Where: `gwl.nim:1359` (`of fBombCost: vm.push(view.bombCost, kInt)`), fed from
  `sim.nim:355` (`result.bombCost = state.bombCost`).
- design.md:154-155 lists `BOMBCOST` = 12 under **Constants**, while `bombCost` is a 0..60 config
  knob (design.md:96-97, manifest:94-100). The prompt text documents the implemented behaviour
  ("BOMBCOST (the energy a bomb costs this episode)", llm.nim:225).

### N3 — The live `/global` broadcast is once per round, not per elimination / every 25 ticks
- Where: `server.nim:110-117` (`broadcastLocked`) is called at `server.nim:168` (finish),
  `:202` (start), `:238`/`:285` (deadline) and `:280` (after a round's four submits). There is no
  call inside the battle, because the battle runs synchronously inside `sim.submit`
  (`sim.nim:961-962` → `runRound` → `runBattle`).
- design.md:780-782 says: "the full snapshot after every `submit`, at the start and end of every
  battle, on **every elimination**, and every 25 ticks". A live spectator on `/global` sees one
  snapshot per round; the per-tick detail exists only in the replay/frames path.

### N4 — `viewer_smoke.mjs` is run without `--soak`, so the freeze check the note pins is not exercised
- Where: `.github/workflows/ci.yml:316-319` passes `--bundle`, `--replay`, `--timeout 90` and
  nothing else; `tools/ci/viewer_smoke.mjs:115` defaults `soak: 0` and `:387` gates the whole soak
  block on `args.soak > 0`.
- design.md:1126-1132 pins "with **`--soak 10`** — that the clock keeps advancing during
  uninterrupted playback (cogball 0.1.4: a mid-replay exception that scrubbing hides)".
- Checklist item 13 is nonetheless satisfied by the run cited below: the step ran, was not
  `continue-on-error`, and reported `"loaded":true`.

### N5 — The prompt says a bomb "detonates 5 ticks after it is planted"; the sim detonates it during tick t+4
- Where: `sim.nim:598-599` plants with `fuse: BombFuse` (5) in the *bomb pass* of tick t, and
  `sim.nim:638-640` (fuse pass) decrements it in the **same** tick, so the fuse is 0 at tick t+4.
  `tests/test_sim.nim:241` asserts exactly that (`record.stat[0].deathTick == 4` for a bomb planted
  at tick 0).
- The system prompt (llm.nim:287) and the docs page (manifest:294) say "5 ticks after it is
  planted"; design.md:100-101 says only "detonates when its fuse reaches 0. `BombFuse` = 5 ticks",
  which the code matches on the "five ticks of life including the planting tick" reading.

### N6 — A reply with no `notes` leaves the previous round's notes in place
- Where: `sim.nim:947-948` — `if notes.len > 0: sim.notes[seat] = cutRunes(...)`. `parseSubmission`
  already normalises a missing `notes` to `""` (llm.nim:407), so an omitted field silently keeps the
  older text, which `seatObservation` then feeds back (`sim.nim:1371-1372`).
- design.md:371 says "`banner`/`notes` missing ⇒ empty". `banner` *is* overwritten unconditionally
  (`sim.nim:946`), so the two fields behave differently.

### N7 — The `/client/replay` pod page and route still exist (inherited from the starter)
- Where: `server.nim:453` (`result.get("/client/replay", htmlHandler("replay.html"))`),
  `server.nim:458` (`WS /replay`), `client/replay.html`, and a mention in the manifest's global
  protocol text (`coworld_manifest_template.json:280`, "…`/client/replay` plays a recorded
  episode…").
- Checklist item 3 says "No `/client/replay` pod path **anywhere**", and that phrase is literally
  matched by those lines. Against that: `game.replay_viewer` declares only
  `{"bundle": "static-replay-viewer"}` (manifest:16-18), the build hook exists and is executable
  (`tools/build_replay_viewer.sh`, mode 100755), the bundle contacts nothing but the `?replay=` URL
  (`static_replay.js:67-89`) and its own assets, and the design note explicitly keeps the starter's
  route list including `/client/replay` (design.md:756-759). Recording the observation so the judge
  can decide which reading item 3 intends; the pod path is not what the platform is pointed at.

### N8 — `docker_smoke.sh`'s slug-derived default entrypoints do not match the shipped binaries
- Where: `tools/ci/docker_smoke.sh:22-23` documents defaults `/bin/grid-wars` and
  `/bin/grid-wars-player`; the image installs `/bin/gridwars` and `/bin/gridwars-player`
  (`Dockerfile:57-58`), because the compose service has no hyphen (`compose.yaml:4`).
- `ci.yml:191-195` passes `SMOKE_GAME_BIN` / `SMOKE_PLAYER_BIN` explicitly and comments why, so CI
  is correct; a bare `./tools/ci/docker_smoke.sh <image>` outside the workflow would not be.

### N9 — CI runs `nim r` per test file, not `nimble test`, and `docker-smoke` has no `needs:`
- Where: `ci.yml:104-150` (each of `tests/*.nim` compiled and run twice, debug and `-d:release`),
  `ci.yml:156-158` (`docker-smoke` declares no `needs`), `ci.yml:217-222` (`wasm-viewer` declares
  `needs: docker-smoke`).
- design.md:1064-1066 says "`tests/` runs under `nimble test` in `ci.yml`'s `build-test` job … The
  smoke job **`needs:` the build job** and never reuses a cached binary." The job is named `test`,
  and the smoke instead builds the production image from source inside its own job
  (`ci.yml:176-177`), which satisfies checklist item 12's "freshly built binary in the same run"
  by a different route. Recording the note↔code difference only.

### N10 — Replay re-derivation is asserted per-round-digest plus the *last* frame, not frame by frame
- Where: `tests/test_replay.nim:94-108` (digest equality per round over 20 seeds),
  `:121-138` (`replayed.len == frames.len` and `$replayed[^1] == $frames[^1]`).
- The recorded artefact carries no per-tick state at all (by design: design.md:683-689), so there is
  nothing to compare tick-by-tick against; the digest (`sim.nim:293-313`, FNV-1a over the whole
  board, both flags, every bomb and every warrior number) is the per-round proof. A loop comparing
  all ~2000 re-derived frames to `sim.frameStates()` would close the remaining gap cheaply.

### N11 — Every live snapshot recomputes every played battle
- Where: `server.nim:101` (`snapshotJson` → `sim.liveStateJson()`) → `sim.nim:1066`
  (`sim.frameStates()`) → `sim.nim:1037-1047` (`buildFrames` re-runs `runBattle` with
  `sink.want = true` for **every** record, building ~405 JSON frames per round) and returns only
  `frames[^1]`. This runs on every round boundary and on every `/global` connect
  (`server.nim:388`). Bounded (`rounds × ticks`, integer-only, no IO), so not a hang; it is
  work proportional to `rounds²` for a value that is one frame.

### N12 — Beat markers never take their seat colour
- Where: `client/renderer.js:1016-1018` adds `seat<N>` to the button's class list, but the appended
  chrome sets `--tc` on the kind rules at higher specificity
  (`client/chrome.css:581-586`, `.beat-marker.submit` … versus `client/chrome.css:205-209`,
  `.seat0 { --tc: var(--red); }`). Cosmetic; every kind still has a rule and is visible, which is
  what checklist item 14(d) requires.

### N13 — `sentry` exists twice, with nothing tying the copies together
- Where: `sim.nim:171-192` (`SeedScript`, a literal used as round 1's seed script) and
  `data/warriors/sentry.gwl` (`staticRead` at `llm.nim:36`, the fallback warrior). They are
  identical today — verified by running `SeedScript == warriorLines(skSentry)` → `true` — but no
  test asserts it, and design.md:487 makes them the same object ("the always-legal **fallback**, and
  the round-1 seed script").

---

## Traced and consistent

**Tick resolution order (design.md:180-218) against `sim.nim:547-780`, step by step**

- **1 Priority** — `sim.nim:270-276` `tickPriority(tick)[k] = (k + tick) mod 4`; it is the only
  ordering used in steps 3, 4 and 5 (`sim.nim:587`, `:606`, `:622`). Asserted at
  `tests/test_sim.nim:127-136` and, behaviourally, at `:138-166` (both contestants accumulate
  `blocked`, which a fixed order could not produce).
- **2 Decision pass, read-only snapshot** — `sim.nim:559-584`. `viewFor` (`sim.nim:337-355`) copies
  `board.owner`/`board.corpse` (Nim value arrays) and rebuilds bomb/occupant/alive from the current
  state; the VM receives it as an immutable `BoardView` parameter (`gwl.nim:1134`) and has no other
  route to the board (`gwl.nim:1111-1128`). Nothing in the pass writes to `state.board`. Asserted at
  `tests/test_sim.nim:168-192`.
- **2 Illegal move** — `sim.nim:579-584`: any `dx`/`dy` outside {−1,0,1} or (0,0) increments
  `illegal`, rewrites the intent to `akWait`, logs a feed line, and is explicitly *not* a fault.
  Asserted at `tests/test_sim.nim:200-209`.
- **2 Stall** — `gwl.nim:1446-1451` returns `akWait` with `stalled = true` and leaves `vm.pc`
  untouched; `sim.nim:577-578` increments `stalls`. Resumption at the same pc asserted at
  `tests/test_gwl.nim:381-401`.
- **2 Halt** — `gwl.nim:1443-1445` / `sim.nim:575-576`: running off the end sets `halted`, the
  warrior is skipped for the rest of the round (`sim.nim:561`) and dies to the idle rule.
- **3 Bomb pass** — `sim.nim:587-603`: alive, `energy >= bombCost`, no live bomb on the cell; else
  `refused`. Bomb list kept sorted by cell index (`sortBombs`, `sim.nim:373-384`). Asserted at
  `tests/test_sim.nim:211-221`.
- **4 Place pass** — `sim.nim:606-611`, overwrites the owner; counts recomputed at step 10.
- **5 Move pass** — `sim.nim:614-636`: occupancy and bomb maps built before the pass, `occupant`
  updated as each warrior moves, so a cell taken earlier *in the same pass* blocks; wrap via
  `wrap()` (`sim.nim:279`). Asserted at `tests/test_sim.nim:194-198`.
- **6 Fuse / 7 Detonation** — `sim.nim:638-715`. The closure grows to a fixpoint over cells and
  bombs (`sim.nim:650-666`; it terminates because `growing` is set only when a new cell or a new
  bomb is added). Attribution runs over the **pre-blast**, cell-index-sorted bomb list and takes the
  first covering detonating bomb (`sim.nim:667-688`) = the note's "lowest-cell-index detonating
  bomb". Scorching clears owner and consumes bombs (`sim.nim:689-697`); kills/self-kills at
  `:698-715`. Asserted at `tests/test_sim.nim:224-269` (fuse, wrapping plus, chain to closure at the
  same tick, kill vs self-kill).
- **8 Idle** — `sim.nim:717-732` compares against the position captured at the top of the tick
  (`sim.nim:551-554`); `idle >= IdleLimit` (50, `sim.nim:21`) kills. `tests/test_sim.nim:287-294`
  asserts death at `deathTick == IdleLimit - 1`, i.e. the 50th consecutive stationary tick.
- **9 Fault pass** — `sim.nim:734-744`, only for warriors flagged in step 2, corpse left, line and
  message recorded. Asserted at `tests/test_sim.nim:296-302` (line 5, "division by zero").
- **10 Bookkeeping** — `sim.nim:746-758`: `unpaint` every warrior that died **this tick**
  (`sim.nim:368-371`), `recount` (`sim.nim:357-366`, also updates `peakTiles`), then
  `energy = min(60, energy + 1 + tiles div 60)` for survivors. Un-painting asserted at
  `tests/test_sim.nim:271-284` (`'3' notin record.ascii`).
- **11 Round end** — `sim.nim:771-780`, horizon first, then `lastStanding`, then `wipeout`, matching
  the note's precedence. Asserted at `tests/test_sim.nim:304-319`.

**GWL VM (design.md:111-176) against `gwl.nim`**

- Every statement form in the note's table is parsed (`gwl.nim:439-589`); both infix and call forms
  of `div`/`mod` (`gwl.nim:344-350`, `gwl.nim:1391-1404`); `and`/`or` short-circuit with a boolean
  assertion (`gwl.nim:746-763`); booleans are a distinct tag so `if 1:` faults
  (`gwl.nim:1408-1412`).
- Builtins and constants match the note's tables (`gwl.nim:129-140`, `:688-691`, `:1346-1405`), with
  the two divergences at N1 and N2. `rand` is xorshift64 seeded `seed + seat` where `seed` is the
  round seed `config.seed*1000003 + round*97` (`gwl.nim:1022-1046`, `sim.nim:133-136`) — the note's
  `seed*1000003 + round*97 + seat`, exactly.
- Compile caps: 120 lines / 100 runes a line / 4000 runes (`gwl.nim:977-991`, rune-counted),
  4000 nodes (`:311-316`), 32 procs (`:524-526`), nesting 8 (`:591-593`); runtime caps: 2000
  instructions (`sim.nim:24` → `gwl.nim:1143`), call depth 64 (`gwl.nim:1295-1297`), 4096 array
  elements (`gwl.nim:1325-1328`). Each has a test in `tests/test_gwl.nim:433-468` and
  `:255-286`.
- Every fault kind in the note's list is produced with a line number, and an action suspends the VM
  and resumes after it (`gwl.nim:1431-1442`); `tests/test_gwl.nim:287-329`, `:364-380`.

**Decision path (design.md:299-347) against `llm.nim`**

- One parallel batch per attempt, never sequential: `llm.nim:494-508` builds a single
  `RequestBatch` over all still-open seats and issues `client.curl.makeRequests(batch,
  client.timeoutSeconds)` once per attempt; the attempt loop is `for attempt in 0 .. 1`, so at most
  two batches per round and `client.batchesUsed` records it (`llm.nim:497`).
- Tolerant parse: BOM and fences stripped (`llm.nim:336-352`), first `{`…last `}` extracted with
  trailing prose tolerated (`:354-366`), `script` accepted as array **or** string with a fence
  inside the value stripped either way (`:368-404`), tabs→2 spaces, trailing blanks dropped, empty
  script rejected. Each has a test (`tests/test_bot.nim:117-211`).
- Compile before submit, so the retry carries the compiler's own `line N: message`
  (`llm.nim:414`, `:503-505`).
- Retry once, then fall back: `llm.nim:518-532`; the fallback is the `sentry` warrior with
  `origin = "fallback"` and the rejection recorded (`llm.nim:179-181`, `sim.nim:939-942`), counted
  into `results.fallbacks` (`sim.nim:1007-1009`).
- No credentials ⇒ every seat scripted, no network, no batch: `llm.nim:154-157`, `:487-492`;
  asserted at `tests/test_bot.nim:94-114` (`client.batchesUsed == 0`, `< 500 ms`).

**Every wait and its bound**

| wait | where | bound |
|---|---|---|
| player connect | `server.nim:190-196` | `playerConnectTimeoutSeconds` (180 default, manifest:133-137); `sleep(200)` poll, starts regardless |
| LLM batch | `llm.nim:508` | `client.timeoutSeconds` = `llmTimeoutSeconds` (60, capped 5..300 by the schema) |
| pre-batch deadline check | `server.nim:231-245` | `now + RoundReserveSeconds (150.0, server.nim:39) > playDeadline` ⇒ `endEarly()` (or one all-fallback round if nothing has been played) |
| play budget | `server.nim:206-219` | `gameStart + timeout * PlayBudgetFraction (0.6)` = 720 s of 1200; `COWORLD_TIMEOUT_SECONDS` honoured when present, `episodeTimeoutSeconds` assumed otherwise |
| round pacing | `server.nim:291-305` | `roundDelayMs` (itself capped by `PacingBudgetMs / rounds`, `sim.nim:129-130`) |
| rate-limit floor | `server.nim:292-304` | 8 s, doubled to 16 s when the round used two batches |
| shutdown grace | `server.nim:176-182` | 20 s after the artifacts are written, then `quit(0)` |
| player receive loop | `gridwars_player.nim:58-85` | wrapped in `try/except CatchableError`, exits 0 on a dead socket (the starter fix the note names) |

Worst case per round is 60 + 60 + 16 + ~0.03 = ~136 s; the reserve check means the last batch can
start no later than `playDeadline − 150`, so play settles by ~706 s < 720 s, and the artifacts are
written before the grace. No unbounded loop: the game loop (`server.nim:222-305`) exits on
`sim.done` or the deadline, and `pendingSeats()` is non-empty whenever the sim is not done.

**Replay writer and re-derivation**

- Five event kinds only (`types.nim:46-51`), with the fields the note lists (`sim.nim:1109-1152`);
  `eventFromJson(eventToJson(e)) == e` for all five, asserted at `tests/test_replay.nim:213-221`.
- The per-tick history is not recorded: `recordsFromEvents` (`sim.nim:1189-1225`) rebuilds each
  round from the logged seed, spawn permutation and scripts, `replayMatch` re-runs `runBattle` and
  raises on a digest mismatch (`sim.nim:1227-1250`). The wasm module does exactly the same
  (`gridwars_replay.nim:26-58`) and reports the raise as `data-replay-error`.
- Self-sufficiency: `replayJson` (`sim.nim:1257-1285`) carries protocol, aliases, `policyNames`, the
  config (rounds/ticks/bombCost/seed/`sampled: true`), every event and the results.
  `configFromReplay` (`server.nim:462-471`) and the wasm loader rebuild `config.players` from
  `names`, and `tableNames` (`sim.nim:107-118`) reproduces the same aliases from `players.len` and
  `seed`, so the viewer needs nothing but the file.
- Frame contract: `Seats + ticksPlayed + 1` frames per round, keyframe `grid` on submit/roundEnd/
  every 25th tick/frame 0 and `gridDelta` otherwise (`sim.nim:436-494`), and the delta stream and a
  keyframe seek reconstruct the same board and agree with each seat's `tiles`
  (`tests/test_replay.nim:140-210`). The renderer's reader implements exactly that walk-back
  (`client/renderer.js:679-712`).

**Viewer**

- All four viewer files are bullwhip's, and only bullwhip's: `config.nims` differs from the starter
  by three renames (output name, `EXPORT_NAME`, `EXPORTED_FUNCTIONS`) and nothing else;
  `gridwars_replay.nim` is a rename-only fork of `bullwhip_replay.nim`; `static_replay.js` differs
  by the `_gw_*`/`GridWars*` renames, the two new element handles and the documented `ready`-polling
  change; `index.html` is the starter page plus `#terrbar`, `#codepane`, `relayout()` and the two
  script tags. (All four `diff -u`ed against the mount.)
- MODULARIZE/EXPORT_NAME pair agrees: `config.nims:38-39` `-s MODULARIZE=1 -s
  EXPORT_NAME=GridWarsReplayModule` and `static_replay.js:154` `GridWarsReplayModule().catch(...)` —
  a factory call against a factory build. No `Module.onRuntimeInitialized` anywhere.
- `data-replay-loaded="true"` is set from the shell's own lineage at `client/renderer.js:998`, after
  the first synchronous `renderer.draw(view)` of the rAF loop (`:975-996`); `data-replay-error` is
  set in `static_replay.js:56` and cleared on load and on retry (`:107`, `:150`).
- `client/chrome.css` bytes 0..11963 are **byte-identical** to the starter's file (verified with
  `cmp`), followed by one `/* ---------- Grid Wars ---------- */` block; `tests/test_viewer.nim:44-52`
  pins the same prefix by length and FNV digest.
- `client/replay.html` = the starter's page + `#terrbar` + `#codepane` + the wordmark/title/
  `relayout()` edits; **nothing removed** (diffed; `tests/test_viewer.nim:92-107` re-checks all 20
  starter ids on both pages).
- Transport rules: `relayout()` sets `--band` and `--hudscale` on `document.documentElement`
  (`replay.html:50-57`, `index.html:48-58`) and calls `fit()` from the same function, on `load`,
  `resize` and the feed toggle; `#transport` is the last flex child of `#stage` at `z-index: 10`
  (`chrome.css:128-136`), `#endscreen` is `position:absolute; inset:0` **inside** `#board-wrap`
  (`chrome.css:374-383`) so it stops at the band, `#loading` rides `bottom: var(--band)`
  (`chrome.css:572`); `updateEndscreen(..., index >= frames.length - 1 && frames.length > 0, ...)`
  is called from **every** `setIndex` (`renderer.js:944-972`), so every scrub click, beat click and
  play-restart takes the endcard down, and it is toggled with the `.show` class its CSS rule uses
  (`renderer.js:599`, `chrome.css:383`).
- Beats are labelled `<button type="button">` with `aria-label`/`title` and an `onclick` that seeks
  (`renderer.js:1013-1027`, wired at `:870-874`); the six kinds emitted (`submit`, `roundend`,
  `fault`, `idle`, `kill`, `end`, `renderer.js:1029-1078`) each have a CSS rule
  (`chrome.css:581-586`), and `tests/test_viewer.nim:175-193` asserts the emitted set is a subset of
  the styled set.
- `#viewpanel` / zoom / minimap appear nowhere (`grep` across `client/`, `replay-viewer/`; asserted
  at `tests/test_viewer.nim:129-136`), consistent with design.md:891-894 (fixed 30×30 arena).
- 360 px legibility: `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }`
  (`chrome.css:280-291`), `.plate-label` hidden at 640 px in the inherited block
  (`chrome.css:460-461`), plus the game block's 1000/720/560/420 px queries
  (`chrome.css:598-610`). The scorebug renders `214 tiles`, `23 energy`, `+38.5`, `2 kills`,
  `DEAD`/`FAULT` as words and numbers (`renderer.js:550-585`).
- Both name spaces: prompts and the board use aliases only (`sim.nim:1318-1372`,
  `tests/test_prompt.nim:98-116`); `makeNameMap` swaps policy names in spectator-side, keeping
  baseline fillers on their alias (`renderer.js:338-366`), and `results.names` carries policy names
  (`sim.nim:994`).

**Manifest** — `num_agents: 4` in `standard` (:396), `blitz` (:423) **and**
`certification.game_config` (:448); `replay_viewer.bundle = static-replay-viewer` (:16-18);
`game.docs` is `readme` + two `pages` with the `{id,title,content:{type,value}}` shape (:283-305);
`game.protocols` carries **both** `player` and `global` as `{"type":"text","value":…}` objects
(:273-282); the secret URI is `secret://coworld/grid-wars/anthropic_api_key` (:28); three `player[]`
entries, all on `{{GRIDWARS_IMAGE}}` running `/bin/gridwars-player` (:308-375); every fixed-width
array in both schemas carries `minItems: 4, maxItems: 4`; `certification.players` seats all three
runnables across four slots (:455-468).

**Seat-count enforcement** — `tools/ci/docker_smoke.sh:107-152` implements all four invariants
(`num_agents` present; a positive integer; `len(certification.players) == it`;
`len(certification.game_config.players) == it`) plus the independent `SMOKE_SEATS` cross-check, each
exiting non-zero with a `SEAT-COUNT FAIL:` prefix. The docker-smoke log for the reviewed sha
contains **no** `SEAT-COUNT FAIL` (grepped) and reports
`game=grid-wars seats=4 …` and `smoke OK: seats=4 results=323B replay=7989B reason=complete`.

**Policies** — `tools/ci/policies.json` has four entries: `grid-wars-tactician` (`PLAYER_PROMPT`),
`grid-wars-cartographer` (`PLAYER_PROMPT`, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` at
line 15), and the two scripted fillers. No scripted policy is seated as a champion.

**Placeholder gate (item 12)** — run verbatim:
`grep -n '<slug>\|<IMAGE>\|<SEATS>' ci.yml coworld-release.yml coworld-submit.yml docker_smoke.sh
policies.json` → no matches, exit 1 ⇒ the gate exits 0. Release order in `coworld-release.yml` is
build manifest (:153) → certify (:167) → **upload-policies (:206)** → upload-coworld (:304) → secret
put (:342). All three workflows present; `docker_smoke.sh` and `build_replay_viewer.sh` are
committed `100755`.

**CI (item 1 and item 13)** — `gh run list -R Metta-AI/cogame-grid-wars --branch main -w ci.yml`:
run **32725270946**, conclusion **success**, `head_sha dbffed23da0d4f001151d6c7a3a2c0654fcb6955`, all
three jobs green (`test` 11 s, `docker-smoke` 1 m 23 s, `wasm-viewer` 1 m 28 s). The `test` job's log
shows all six test files actually executed, twice each (debug and `-d:release`) — the 11 s is a warm
`~/.cache/nim`, not a skip. `wasm-viewer` declares `needs: docker-smoke` (`ci.yml:222`) and its
`Load the bundle in a real browser` step ran and printed
`{"loaded":true,"ms":289,"clock":"R1 / 2 · SUBMITTING","scorebug":"Sprocket 0.0 0 TILES 12 ENERGY …",
"feed_lines":13}` with `scrub readouts: 0%="R1 / 2 · SUBMITTING" 50%="R2 / 2 · SUBMITTING"
100%="R2 / 2 · FINAL"`. No test was disabled, skipped or loosened this run:
`git log --name-only c942f8a..HEAD` shows the only files touched after the tests landed are
`.github/workflows/*.yml`; `tests/` has exactly one commit in the repo's history (c942f8a, all six
files added).

**`tools/ci/viewer_smoke.mjs`** is byte-identical to
`/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff -q`).

---

## Could not determine

- **The wasm half of B2.** No `emcc` in this sandbox, so I could not build the module and run a
  >2³¹ warrior through it. Settled by: building `replay-viewer/gridwars_replay.nim` and either
  printing `sizeof(int)` from the module, or re-deriving an episode whose warrior computes
  `2000000000 + 2000000000` and comparing the digest to the server's.
- **Whether item 3's "No `/client/replay` pod path anywhere" is meant literally** (N7). Settled by
  the judge's reading; the code facts are cited above and are not in dispute.
- **Real-transport behaviour of `decideAll`.** Every LLM path was read, not executed (CI runs with
  no credentials, so `client.disabled` is true and no batch is issued). The 429/401 branches
  (`llm.nim:447-458`) and `tryNextBedrockModel` are untested by anything in `tests/`. Settled by a
  phase-60 verify round with credentials, or a fake-transport test.
- **Whether the note's `painter`-beats-`sentry` claim was ever true** (B3). The shipped scripts are
  the note's verbatim listings, so either the note's claim was never measured or it was measured
  under different constants. Settled by tuning `painter` and re-running the ten-seed harness.
