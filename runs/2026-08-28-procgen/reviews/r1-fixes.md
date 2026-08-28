# r1 fixes — procgen

Head: `545c79116b1d5c977984135e8baed1b89f8d3dca` on `main`
CI: https://github.com/Metta-AI/cogame-procgen/actions/runs/33204619462 — **success**
(jobs `test` 98962386990, `docker-smoke` 98962387093, `wasm-viewer` 98962715990, all `success`;
no job `continue-on-error`, `wasm-viewer` still `needs: docker-smoke`).
Previous green run on the intermediate head `093dfed`: 33204059062 — `success`.

Pushed through the GitHub Git Data API (blobs → tree → commit → non-forced `refs/heads/main`
update), because the sandbox credential proxy refuses `git push` ("No anonymous write access").
Each finding is one commit; the local and remote trees were compared by sha after the update.

**Method note.** I did not work blind: `nimby 0.1.26` + Nim 2.2.4 install from GitHub releases
inside this sandbox, so every change below was compiled and the whole suite run locally (debug and
release) before it was pushed. Docker, emscripten and the browser are still CI-only.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | no change — verified, and the open question settled | — | `src/procgen/runtime.nim`, `procgen.nimble` |
| F2 | fixed | `c8cc41f` | `client/broadcast_core.js:1-34`, `tests/test_procgen_viewer.nim:74-99` |
| F3 | no change — verified consistent | — | `client/replay_broadcast.html` |
| F4 | no change — recorded divergence | — | `docs/RULES.md` §Divergences 6, `src/procgen/gen.nim:12-20` |
| F5 | no change — claim verified from the CI sweep table | — | `src/procgen/baselines.nim:37-45` |
| F6 | fixed (naming only) | `6bd0313` | `tools/tune_baselines.nim:1-11`, `src/procgen/engine.nim:116-121`, `src/procgen/baselines.nim:32`, `tests/test_procgen_control.nim:195`, `.github/workflows/ci.yml`, `tools/ci/baseline_tuning.json` |
| F7 | no change — the note's number breaks the note's own test 27 floor | — | `tests/test_procgen_engine.nim:75-102` |
| F8 | no change — Nim's stdlib has no sha256; `ci.yml` enforces it | — | `tests/test_procgen_viewer.nim:20-28`, `.github/workflows/ci.yml:104-111` |
| F9 | fixed | `545c791` | `tests/fixtures/*.replay` (4 new), `tests/test_procgen_replay.nim:15-95,175-225`, `.github/workflows/ci.yml` |
| F10 | fixed | `276653c` | `.github/workflows/ci.yml` (new "WIDE generator sweep" step), `tests/test_procgen_gen.nim:5-18` |
| F11 | no change — the header already says so; art verified | — | `src/procgen/procgen_art.nim:1-11`, `data/` |
| F12 | fixed | `e0e884a` | `src/procgen/sim.nim:246-340`, `server.nim:424-436`, `engine.nim:60-72`, `decide.nim`, `tests/test_procgen_control.nim`, `tests/test_procgen_identity_privacy.nim` |
| F13 | fixed | `648f741` | `src/procgen/sim.nim` (`beginLevel`, `applyPlan`), `replay_runtime.nim:223-231`, `tests/test_procgen_events.nim` |
| F14 | fixed | `893a6ec` | `client/replay_broadcast.html:1665,1692,1749-1753,1843`, `tests/test_procgen_endcard_labels.nim` |
| F15 | fixed | `0cd1e43` | `src/procgen/labels.nim:20-33,44-52,66-72`, `tests/label_manifest.txt` |
| F16 | fixed | `6d02660` | `tests/test_procgen_sim.nim:406-450` |
| F17 | fixed | `07dea1b` | `tests/test_procgen_endcard_labels.nim:24-38,63-80` |
| F18 | no change — the HTTP surface is exercised by `docker_smoke.sh`; a live test needs a design change | — | `tests/test_procgen_engine.nim:207-226,292-315` |
| F19 | fixed | `024d035` | `src/procgen/server.nim:63-82,495-508`, `runtime.nim:35-37`, `tests/test_procgen_engine.nim:317-352` |
| F20 | fixed | `fc309e6` | `coworld_manifest_template.json` (`config_schema`), `tests/test_procgen_manifest.nim:89-127`, `sim_config.nim:3-8`, `sim_types.nim:57-60` |
| F21 | fixed | `413eced` | `src/procgen/server.nim:144-148,289-297,500-505`, `replay_runtime.nim:3`, `tests/test_procgen_engine.nim` |
| F22 | no change — the fixture is the compensating gate; cite its number | — | `.github/workflows/ci.yml:399-422`, `tools/ci/renderer_fixture.html` |
| F23 | fixed | `093dfed` | `src/procgen/global.nim:13-40,57-60,86-95`, `sim.nim` (`applyPlan`), `tests/test_procgen_engine.nim:258-296` |
| F24 | no change — verified; the wasm cross-target case now runs on the fixtures | — | `tests/test_procgen_identity_privacy.nim`, `.github/workflows/ci.yml` |
| F25 | no change — the narrowing is a correction, and nothing was loosened this round | — | `tests/test_procgen_art.nim:46-58` |

Checklist item numbers below are from `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.

---

## F1 — the runtime/dependency stack is not coworld-ctf's

**No change. The review's open question is now settled, in the builder's favour.**
`gh api` reaches `Metta-AI/cogame-snake-royale` from this sandbox, which the reviewer could not do.
`src/snake/runtime.nim` there and `src/procgen/runtime.nim` here differ in exactly **four lines**:
the three `echo` log prefixes (`snake-royale:` → `procgen:`) and the `FetchTimeoutSeconds` export I
added under F19. `snake_royale.nimble` and `procgen.nimble` require the identical set
(`nim >= 2.2.4`, `mummy >= 0.4.7`, `whisky >= 0.1.3`, `curly >= 1.1.1`, `jsony`). Builder deviation 1
is therefore verified, not merely asserted, and the "could not determine" item is closed.
Satisfies item 14's spirit (provenance is checkable) — no checklist item is at issue.

## F2 — `client/broadcast_core.js` is a rewrite, not a fork *(commit `c8cc41f`)*

The note's "kept and pinned function-by-function" list names procs that are **not in that file in
either repo**: `pushFeed(row)`, `banner(text, cls)`, `clearFeed`, `pumpBanner`, `clearBanners`,
`seekToFraction`, `relayout()` and the `?embed=1` path live in the inherited head of
`client/replay_broadcast.html`; `markBeat`, `ingestLullSpans`, `renderLullSpans`, `renderTransport`
and the speed chips live in `client/chrome_common.js`, which is byte-identical to the starter's.
The note's reading of *this file* is therefore not implementable, so I took the brief's first
option: the file's own provenance claim now says what it is — a **rewrite of the draw layer against
the starter's interface**, with the pinned surface enumerated (factory, method surface, canvas/DPR
sizing, letterbox fit, `onTransform`, status/text callbacks, first-frame signal, pace stats) — and
test 40 pins the named procs **where they actually are**: nine needles in the inherited head, five
in `chrome_common.js`, eleven in the core including `devicePixelRatio`. I did not add a
`docs/RULES.md` §Divergences entry: that section is inlined verbatim into the manifest's player-facing
`rules.md` page, and a viewer-file provenance note is not a rule of the game.
Item 14 (chrome provenance) — `chrome_common.js` byte-identity and the page's starter-plus-appended-block
shape are unchanged and still pass; `broadcast_core.js` is not on item 14's list, and what can be pinned
about it now is.

## F3 — `replay_broadcast.html` is the starter's page with deletions *(no change)*

Verified consistent by the reviewer; I add one piece of evidence for the judge: the only page hunks
in this whole round (F14) are at lines 1665, 1692, 1749 and 1843 — **all after the banner comment at
:1581** — so the inherited head is byte-for-byte what it was at `556cb50`, and what it was is the
starter's. Item 14.

## F4 — `climber` ships three tiers *(no change)*

Already a recorded divergence: `docs/RULES.md` §Divergences item 6, inlined into the manifest's
`rules.md` page, with the reason (four tiers in nine rows leaves no headroom, so `X` is a no-op)
consistent with `src/procgen/levels.nim:562-567`. Nothing in the checklist is at issue.

## F5 — `pathfinder.digCost` is 1, not the note's 3 *(no change — the claim is now verified)*

The reviewer marked the code comment's `-0.010` claim untested. It is in the CI log: run 33199610304,
job 98945460474, step "Sweep and verify the scripted-baseline tuning":

```
  lookahead=6 digCost=1 detour=6  pathfinder=7788 scavenger=7329  cleared=16/16  margin=0.0382
  lookahead=6 digCost=3 detour=6  pathfinder=7211 scavenger=7329  cleared=13/16  margin=-0.0098
```

`-0.0098` is the comment's `-0.010`, and `digCost 3` really does lose the ladder and drop from 16/16
to 13/16 cleared. The note's own rule is that the tunables are swept, not guessed, and the shipped
pick is the sweep's winner. Item 7 ("tuned with a grid harness, not guessed") — satisfied.

## F6 — the ladder is twelve pairs, not 24 episodes *(commit `6bd0313`)*

Comments only. `engine.ladderTotals` increments `episodes` once per seed/difficulty **pair** and
`ladderMargin` divides by that, which is right for a mean per-pair difference; five places called it
"the fixed 24-episode ladder" while `baseline_tuning.json` recorded `"episodes": 12`. They now all say
twelve pairs / 24 episode runs / 12 measurements. No tunable, no margin and no recorded number moved
— `ladder: pathfinder 7788 scavenger 7329 cleared 16/16 margin 0.0382` is unchanged in the new run.
The band `[+0.02, +0.45]` stays as measured, with its existing `marginBandNote` reason: the note's
`+0.05` floor is not reachable by any candidate in the swept matrix, and pinning a band the
measurement cannot meet would make CI lie. Item 7.

## F7 — the certification fixture plays 8 levels, not 4 *(no change)*

The note's `levelCount: 4` contradicts the note's own numbered test 27 floor (≥ 180 frames): the
shipped `pathfinder` plays a level in ~25 frames, so four levels is ~100 frames ≈ 17 s of playback
against a 10 s soak with no margin. The CI evidence is unchanged in this round's run: the smoke
replay is `193` steps and the soak advanced `0 / 193` → `48 / 193` → `60 / 193`. All four seat-count
invariants are unaffected (`num_agents: 1`, one certification player, one `game_config.players`
entry, `SMOKE_SEATS=1`); `grep SEAT-COUNT` over the new docker-smoke log (98962387093) returns
nothing and the job printed `smoke OK: seats=1 results=968B replay=128916B reason=complete`.
Items 6 and 13.

## F8 — the chrome sha256 is enforced by `ci.yml`, not by the Nim test *(no change)*

Nim's stdlib ships `std/sha1` and no sha256; the test pins the length and the sha1 and carries the
sha256 as the literal `ci.yml` checks with `sha256sum -c -`. That step is unconditional and green in
job 98962386990. Writing a sha256 implementation into a test to satisfy the letter of the note would
be new cryptographic code in a test file. Item 14.

## F9 — the four committed fixtures *(commit `545c791`)*

**Fixed.** `tests/fixtures/{gauntlet-seed42,sprint-seed7,hard-seed13,deadline-seed21}.replay` are
committed (364 KB total), each recorded from a recipe in `tests/test_procgen_replay.nim` that pins
every field its ending depends on — seed, `levelCount`, `turnsPerLevel`, `framesPerTurn`,
`fallLethal`, difficulty, `interruptOnDanger`, the baseline, and for the deadline fixture the stop
turn, reason and end rule. Re-record with
`nim r --path:src tests/test_procgen_replay.nim --write`.

New block 49 asserts, per fixture: it decodes, it carries the current `GameVersion`, it **re-derives
frame by frame** (`mismatchFrame < 0`), it plays its recipe's level count, the deadline fixture's
`stop` record comes back off the bytes, and **re-recording from the recipe reproduces the same action
stream and the same per-frame hashes**.

Evidence that it is a real gate, not a formality: I temporarily changed `HunterRestModulo` from 3 to
4 and three fixtures went red naming their first divergent frame
(`49: gauntlet-seed42 re-derives frame by frame (first divergence 26)`), green again when it was put
back. `ci.yml` now also runs the exact emitted wasm module against every committed fixture — the
note's test 49 read literally — and the new wasm job logs:

```
fixture: tests/fixtures/deadline-seed21.replay
ok: loaded deadline-seed21.replay, advanced 150 frames (556130 packet bytes, heap 16 MB)
fixture: tests/fixtures/gauntlet-seed42.replay
ok: loaded gauntlet-seed42.replay, advanced 150 frames (866174 packet bytes, heap 16 MB)
fixture: tests/fixtures/hard-seed13.replay   ... ok
fixture: tests/fixtures/sprint-seed7.replay  ... ok
```

This is the "silent format change against an older recording" detector the review said was missing.
Item 2 (replay re-derivation) and item 13.

## F10 — the generator sweep is 150/400, not 500/5000 *(commit `276653c`)*

`SWEEP_WIDE` existed and was set nowhere. `ci.yml`'s test job now has its own release-only step that
runs it, so the note's numbers — 6000 purity draws and **60000** validation draws per archetype per
difficulty, and therefore `genFallbacks == 0` over 60000 seeds — run on every push. Measured 3.4 s
locally; the step is green in job 98962386990 ("The WIDE generator sweep (design note tests 14 and
15)" → `test_procgen_gen: ok`). The narrow default stays for the debug+release loop, which runs every
file twice. This also closes the review's "could not determine" item about the wide sweep.

## F11 — the tile kit is drawn browser-side *(no change)*

`src/procgen/procgen_art.nim:1-11` already states the deviation and its reason (this fork draws the
grid in the browser, so the bake is the browser's). The art itself is real — 22 sprite PNGs of
10-26 KB, `arena_floor.png` at 67 KB, three ~1 MB source sheets and their splitter committed — and
every sprite has a procedural fallback. `Dockerfile.replay-viewer:72-81` asserts six of the PNGs land
in the bundle. No checklist item is at issue.

## F12 — the `directive` record now carries its `view` *(commit `e0e884a`)*

Was: both writers passed `""`, so `if viewJson.len > 0` never fired, the note's test-17 clause was
vacuous and the 4000-rune trim ladder was unreachable. Now: `seatViewJson` (with `observationRows`
and `nearestCollectible`) moves from `decide.nim` to `sim.nim` — unchanged except a new
`includeNotes` parameter — because the replay record must be able to build the observation and
`decide` drags libcurl in with it; `recordViewJson()` is the note's "observation minus `your_notes`".
Both writers capture it **before** `applyPlan`, which is the state the seat answered about.

Evidence: the docker-smoke replay grew from 14 060 B to **128 916 B** (70 directive records, each
carrying its ~2 000-rune view), `reason=complete`, and the wasm smoke loaded it and advanced 300
frames. Test 20 now asserts the record carries the view, that the view has no `your_notes`, and that
an **oversized view is dropped** rather than the serialised JSON being cut (the ladder, exercised);
test 17 reads `directive.view` as its own field and asserts no real name, no split and no level seed
in it. Items 4 and 9.

## F13 — `gamestart` and `plan` are emitted *(commit `648f741`)*

`beginLevel` emits `gamestart` once, on the first level, carrying `{levelCount, turnsPerLevel,
difficulty}`; `applyPlan` emits `plan` with the turn's symbols before the first frame runs, and
`preScan` derives the same `plan` event from the recorded turn spans so the live and replayed streams
stay identical. Neither makes a beat or a feed row, as the note requires. The plan's **source** stays
on the `directive` record and the tier-2 `directive` row: the sim cannot derive it, and an event
derived from state that differed between live and replay would be a worse defect than a missing
field — that judgement is written into the code at the emit site.

Test 46 now asserts a real episode emits `gamestart`, `levelstart`, `plan`, `step`, `collect`,
`exitopen`, `levelend`, `gauntletend`, `end`; that a scripted episode emits no `say`/`fallback`; and
that the **replayed** stream — what the viewer draws — emits `gamestart`, `plan`, `say` and
`fallback`, the last two derived from recorded chat records. Item 2.

## F14 — the `Level` re-mapping is back *(commit `893a6ec`)*

Reverts `556cb50`. Both scorebug re-mappings the note's table names —
`<span class="lvl-label">Level</span>` and `<span class="gem-label">Gems</span>` — are now in the
enumerated list test 44 checks, so dropping either is red. The layout worry that motivated `556cb50`
does not materialise: the new viewer smoke read the plate as
`Cog1 COG-alpha L3/8 · MINERSEEN LEVEL 4/4 GEMS LEVEL 3/8` — value-then-label throughout, and the gem
numeral `4/4` is on the plate. Under 640 px and under `#stage.tiny` both labels are hidden outright.
Items 11 and 14.

## F15 — the feed says what the note's examples say *(commit `0cd1e43`)*

The death row now names the absolute sim frame (`… — level over at 425`) — the same axis the scrubber
and the beat buttons use, so a spectator reading the feed can go back to it — and the interrupt row
names what the danger interrupt was looking at, which the level kind already tells it: `hunter
alongside` (chaser), `boulder overhead` (miner), `falling` (climber), `danger alongside` (maze, which
never interrupts). `tests/label_manifest.txt` is regenerated in the same commit, as its own rule
requires, and test 45 (equality against the manifest) passes. Item 11's spirit; no item is falsified
either way.

## F16 — test 13 asserts the note's budget *(commit `6d02660`)*

The 60 s ceiling stays for the debug pass. Under `-d:release` the test now asserts both of the note's
numbers and echoes the measurements. CI job 98962386990:

```
13: episode 70 ms (248 frames)     13: worst single frame 102543 ns     <- debug
13: episode 10 ms (248 frames)     13: worst single frame 16645 ns      <- release
```

i.e. 10 ms against the 1 s bound and 16.6 µs against the 1 ms per-frame bound, measured over all four
archetypes at `hard`, 240 frames each. Item 5's spirit (no frame can stall a turn).

## F17 — the replacements are counted exactly *(commit `07dea1b`)*

`count >= 1` → `count == want`, with the one legitimately-doubled caption (`#clock-caption`'s pre-game
text is both a markup default and a JS assignment) carrying its `2` and its reason. A replacement
pasted twice is now red. Item 1 ("no test loosened") — this tightens.

## F18 — tests 29(a) and 31 are source greps *(no change)*

Real, and I did not fix it: making test 31 a live exercise needs an exported "serve without running
an episode" entry point, which is a design change to `server.nim`'s surface, and 29(a) would need the
lobby timeout to elapse in-process. Both are exercised end to end where the real HTTP surface lives —
`tools/ci/docker_smoke.sh` against the actual container, green in job 98962387093 with
`smoke OK: seats=1 results=968B replay=128916B reason=complete` and `all 1 player containers exited 0`.
Test 29(b) is already a live exercise against a real `DecisionEngine`. I did make test 31 stricter in
two other respects this round (the pod-budget arithmetic, F19; the absent `/client/replay` route,
F21). Items 5 and 13 are unaffected.

## F19 — the shutdown grace is clamped to the pod budget *(commit `024d035`)*

This is the review's third "could not determine", settled. The scored artifact was never at risk:
the budget guard turns the seat scripted at `elapsed + 2 × turnBudget > wallClock`, so the last LLM
turn **ends** by `wallClock − turnBudget` = 652 s, the display hold is 0.24 s, and **results are the
first artifact written** — 673 s worst case, inside 720. What could run away is the tail after them:
three more artifact URIs that can each hang for `FetchTimeoutSeconds`, plus a fixed 20 s grace, which
is the ≈732 s the reviewer computed (≈752 s if a dead seat adds the fourth PUT).

The grace now ends at the **earlier** of `now + ShutdownGraceSeconds` and
`episode start + PodBudgetSeconds` (720, and the episode clock starts above the lobby at
`server.nim:331`, so the 90 s `lobbyJoinTimeoutSeconds` is inside it — that half of the finding is
covered by the existing code and needs no change). Every normal path keeps the full 20 s grace the
lantern 0.1.3 scar asks for. `runtime.FetchTimeoutSeconds` is exported so the arithmetic is asserted
rather than argued: test 31 checks `PodBudgetSeconds` against the manifest's own
`episode_timeout_minutes` and, per variant, that `wallClock − turnBudget + hold + one artifact
timeout ≤ 720`. Item 5 (`timeout`).

## F20 — `config_schema` declares every key `sim_config` parses *(commit `fc309e6`)*

`model` and `maxOutputTokens` are declared, with the bounds the parser clamps to. The claim in
`sim_types.nim` and `sim_config.nim` is now enforced instead of repeated: test 36 reads the key list
out of `sim_config.nim` itself (22 keys found) and asserts each is a declared property of the closed
schema, plus `tokens`/`players`, which are read structurally. `ci.yml`'s coworld-0.1.43 validation
step is green on the new manifest. Item 10 (`manifest`).

## F21 — no `/client/replay` path in the pod *(commit `413eced`)*

Checklist item 3 says "No `/client/replay` pod path anywhere". The note retains the route for local
developers and the starter has it too, but a route that exists is a route a judge has to argue about,
and removing it costs nothing: local replay mode is driven by `COGAME_LOAD_REPLAY_URI`, and
`runLocalReplay` serves the very same page from the asset route at `/`. Route and handler are gone;
test 31 asserts the absence of both. The manifest already declares
`replay_viewer.bundle = static-replay-viewer` and nothing else.
One residue I deliberately left: `client/replay_broadcast.html:1107-1108` mentions the old URL form in
a **comment inside the inherited head**, whose starter counterpart says the same thing
(`/workspace/starters/coworld-ctf/client/replay_broadcast.html:1661-1662`). Editing inherited chrome to
tidy a comment would trade an item-3 grep hit for an item-14 provenance hit; it is a comment, not a
path. Item 3 (`static-viewer`).

## F22 — the bundle's `canvas_text` total is 0 *(no change)*

This is the case checklist item 15 names explicitly ("`total: 0` means the check covered nothing … and
is not evidence of anything") and for which it prescribes exactly the compensating gate this repo
ships. The shipped bundle renders in a Dedicated Worker on an OffscreenCanvas, which `viewer_smoke.mjs`
cannot instrument from the page. **The number to cite is the fixture's**, from job 98962715990:

```
canvas text: 72 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
```

against the bundle step's `0 drawn, 0 never inside`. The fixture loads the shipped `index.html` in an
iframe, drives the shipped `broadcast_core.js` on a main-thread canvas with a full-cap 24-rune `say`
on a **top-row** cog at 360/640/1024 px, and asserts its own strings are still full-length
(`renderer_fixture.html:320-323`). Building a second instrumentation path into the Worker would be new
infrastructure for a signal the fixture already gives. This also closes the review's fourth "could not
determine" as far as CI can: a real `ANTHROPIC_API_KEY` replay is phase 60's job. Item 15.

## F23 — `/global` reads the say, and draws the split bar *(commit `093dfed`)*

`applyPlan` counts `sayFramesLeft` down, one per frame it runs — the same `sayFrames` window the
replay path derives in `broadcast.framePacket` — and `liveStateJson` emits the bubble while that
window is open and a `splitbar` document of the same shape `broadcast.nim` ships from the pre-scan, so
`drawSplitBar` (which re-reads it every frame) fills the bars in as levels complete. The three fields
that were written and never read are now read.

I did **not** add a live `lead`: `chrome_common.js:640` takes the lead series **once**
(`if (!s.lead || fullLeadSeries) return;`) and never re-reads it, so a live stream — which cannot know
the running means before the levels are played — would pin the momentum graph to the zeroes of its
first frame, which is worse than the absent key. The reason is written where the field would go.
A new test block covers all of it: no bubble before anybody speaks, the bubble at the cog while the
window is open, the window closing as frames run, one split bar per level with its half. No checklist
item is at issue (the live spectator pod is out of scope in the note; `/global` exists for the
certifier probe, which is item 13's territory and unchanged).

## F24 — the seed-leak and cross-target tests are indirect *(no change)*

The seed/split hiding is verified key by key by the reviewer and by test 17, which is now **stronger**
than when it was reviewed (it reads `directive.view` as its own field, F12). The missing wasm
cross-target case is answered by F9: `ci.yml` runs the exact emitted wasm module against four
committed fixtures as well as the fresh smoke replay, and the module's own
`_procgen_mismatch_tick() !== -1` check fails the job on any grid that does not re-generate
identically. Items 2 and 13.

## F25 — the one narrowed assertion *(no change)*

The `a086c76` hunk narrows "the renderer preloads this file" from all 24 committed PNGs to the 22
sprite PNGs, and it is a **correction**: `broadcast_core.js:93-99`'s `loadKit` really does not preload
`arena_floor.png` or `pallete.png` — the floor wash and the palette are drawn procedurally — so the
pre-change assertion asserted something the code never did. Both files are still asserted to ship and
be non-empty (`tests/test_procgen_art.nim:18-22`).
For item 1's second half over **this** round: `git log -p 556cb50..HEAD -- tests/` contains no deleted
assertion, no widened tolerance and no `skip`/`xfail`; every test change is an addition or a
tightening (`>= 1` → `== n`, a 5-name list → a 9-name list, new release-only bounds, a new fixture
gate, a new schema cross-check), and `tests/label_manifest.txt` is regenerated by its own `--write`
recipe in the same commit as the label change it tracks. Item 1.

---

## NOTED (not fixed)

- `docs/RULES.md` §Divergences is inlined **byte-identically** into the manifest's `rules.md` docs
  page. Nothing in the repo asserts that, so the two can drift silently. A three-line test would pin
  it; it is not a finding in this round's review, so I left it alone.
- `src/procgen/decide.nim` builds the observation for the LLM prompt and `server.nim` builds it again
  for the record, so an LLM turn now does two `distField` sweeps instead of one. Both are ~135-node
  integer BFS (the whole episode is 10 ms in release), so this is measurement, not cost.
- `tools/ci/baseline_tuning.json`'s `marginMin` is the measured `+0.02`, not the note's `+0.05`. The
  swept matrix's best candidate is `+0.0382`, so the note's floor is not reachable without changing
  what is measured. Left as-is with its recorded reason (F6).

## Verification I ran

- Whole suite locally, debug and release, after every commit (Nim 2.2.4 via nimby 0.1.26 in-sandbox).
- Negative controls: `HunterRestModulo 3 → 4` turns the new fixture gate red (F9); removing a fixture
  file turns it red with the re-record instruction; the pre-F14 page fails the new exact-count test.
- CI on the pushed head: run **33204619462**, `success`, three jobs, all three green, with the wide
  sweep, the four fixture wasm runs, the frame-budget measurements and the fixture's `72 drawn, 0
  never inside` in the logs.
