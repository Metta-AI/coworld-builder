# r1 fixes — vizdoom-deathmatch

Repo: `Metta-AI/cogame-vizdoom-deathmatch` (main)
Head: `7e2d1d0aed87e8ef603fc59a2b54eea753a9443e`
CI: https://github.com/Metta-AI/cogame-vizdoom-deathmatch/actions/runs/33132259050 — **success**
(run id `33132259050`, `head_sha 7e2d1d0aed87e8ef603fc59a2b54eea753a9443e`, `head_branch main`;
jobs `test` 98724254977, `docker-smoke` 98724255161, `wasm-viewer` 98724586701, all `success`.
`grep -c SEAT-COUNT` over the docker-smoke log: **0**.)

Review: `runs/2026-08-27-vizdoom-deathmatch/reviews/r1-review.md` (29 findings; F1–F4
blocking, F5 flagged).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.

Every commit names its finding and touches nothing else. The shas below are the shas on
`main` (the push helper replays commits through the Git Data API, so they differ from the
local ones; the trees are identical).

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F1 | fixed | `d9c563e` | `tests/test_vzd_replay.nim:216-397` | **2 — replay re-derivation** |
| F2 | fixed | `f420b57` | `tools/ci/renderer_fixture.html`, `tools/gen_renderer_fixture_frame.nim`, `tools/ci/renderer_fixture_frame.json`, `.github/workflows/ci.yml:361-386`, `client/replay_broadcast.html:4275-4292,4612` | **15 — every drawn string fits its frame** |
| F3 | fixed | `20374b8` | `tools/tune_baselines.nim`, `tools/ci/baseline_tuning.json`, `tests/test_vzd_tuning.nim`, `src/vzd/baselines.nim:41-60`, `.github/workflows/ci.yml:127-137` | **7 — baseline tuned with a grid harness** |
| F4 | fixed | `b99caec` | `docs/plans/2026-08-27-vizdoom-deathmatch-design.md:845,1225-1247,1764` (+ the run copy) | **14 — chrome is the starter's** |
| F5 | fixed | `13ef7af` | `src/vzd/sim.nim:1663-1671`, `tests/test_vzd_sim.nim:168-192` | correctness (advisory) |
| F6 | fixed | `8489a8d` | `src/vzd/server.nim:1963-1977` | — |
| F7 | fixed | `7420580`, `a78b75f` | `src/vzd/sim.nim:3401-3446`, `src/vzd/replays.nim:405-420,513-541,955-961`, `src/vzd/server.nim:1418-1436,2063-2071` | — |
| F8 | NOT FIXED (noted) | — | `src/vzd/replays.nim:664-670` | — |
| F9 | fixed | `8302feb` | `src/vzd/replays.nim:565-590` | — |
| F10 | fixed | `656514e` | `client/replay_broadcast.html:3552-3580` | — |
| F11 | NOT FIXED (noted) | — | `client/replay_broadcast.html:2033-2076` | — |
| F12 | NOT FIXED (noted) | — | `src/vzd/global.nim` | — |
| F13 | NOT FIXED (noted) | — | `src/vzd/sim_types.nim:519-525` | — |
| F14 | NOT FIXED (noted) | — | `client/replay_broadcast.html` | — |
| F15 | NOT FIXED (noted, blocked by F14) | — | `tests/test_vzd_endcard_labels.nim` | — |
| F16 | NOT FIXED (noted) | — | `client/broadcast_core.js` | — |
| F17 | NOT FIXED (noted) | — | `src/vzd/rig_art.nim` | — |
| F18 | fixed | `bf88b09` | `src/vzd/directives.nim:82-98`, `src/vzd/decide.nim:534`, `tests/test_vzd_control.nim:264-283` | — |
| F19 | NOT FIXED (noted) | — | `src/vzd/broadcast.nim` | — |
| F20 | PARTLY DISPUTED / noted | — | `src/vzd/control.nim:467-503` | — |
| F21 | NEEDS-DESIGN | — | `src/vzd/egoview.nim:151-183` | — |
| F22 | fixed | `7e2d1d0` | `src/vzd/baselines.nim:141-215`, `src/vzd/decide.nim:256-275`, `src/vzd/server.nim:2009`, `tests/test_vzd_control.nim:290-315` | — |
| F23 | fixed | `8489a8d` | `src/vzd/server.nim:1963-1977`, `src/vzd/decide.nim:483-495,550` | — |
| F24 | fixed | `c0880ff` | `src/vzd/roster.nim:779-784`, `tests/test_vzd_engine.nim:69-71,114-122` | — |
| F25 | fixed | `eb1121c` | `tools/replay_summary.py:157-170` | — |
| F26 | fixed | `86b3f63` | `src/vizdoom_deathmatch_player.nim` | — |
| F27 | NOT FIXED (noted, deliberate) | — | `src/vzd/llm.nim:71-87` | — |
| F28 | NOT FIXED (noted) | — | `tools/wasm_replay_smoke.cjs` | — |
| F29 | fixed (the tautology) / partly noted | `fb18bcf` | `tests/test_vzd_sim.nim:124-160` | — |

---

## F1 — no test records a replay and re-derives it from the bytes

**What the code did.** The only "re-derivation" in the tree was `test_vzd_engine.nim`'s
determinism suite, which calls the same live loop twice and compares two live hash chains.
No test in `tests/` ever constructed a `ReplayWriter`, serialised bytes or parsed them back
— the reviewer's grep found one hit and it was a prose comment.

**What it does now.** `tests/test_vzd_replay.nim` gained `recordEpisode` and `rederive`.
`recordEpisode` writes a real `.replay` through exactly the `ReplayWriter` calls
`server.nim` makes — eight joins into the lobby, one `writeInputMaskChange` per cog per
tick from the same control layer, one `writeHash` per stepped tick, and, for the two stops
the sim cannot reach, the load-bearing `stop` chat record at the same point in the frame
the server writes it. `rederive` reads the file back with `parseReplayBytes`, builds the
runtime with `initReplayRuntime` (the viewer's own entry point, the one
`replay-viewer/vzd_replay.nim` calls) and steps it with `stepReplay` until the recorded
chain is spent. It asserts four things: `hashValidationFailed` is false, `hashMismatchTick`
is -1, every recorded hash was consumed and matched (`hashIndex == data.hashes.len`), and —
independently of `checkReplayHash` — that each recorded tick's hash equals the re-derived
`gameHash` at that tick, so a silently skipped tick cannot pass.

Three tests, one per end reason, which is design.md test 26: `full_time`, `wall_clock` and
`sim_fault`. Each also asserts the phase and `endRule` playback ends on.

**Evidence that it is a real gate, not a green rubber stamp.** With the F7 fix reverted
locally, the `wall_clock` case fails on the recorded bytes:

```
Replay hash mismatch at tick 121; expected 16888553309173770394, got 6355354787581450103.
  Check failed: not back.failed          back.failed was true
  Check failed: back.mismatchTick < 0    back.mismatchTick was 121
  Check failed: back.phase == GameOver   back.phase was Playing
  Check failed: back.endRule == EndRuleWallClock   back.endRule was full_time
```

`ord(sim.phase)` is in `gameHash` (`sim_state.nim:161`), which is why the stop tick is a
hash-level assertion and not just a state one. Passing, in CI's `test` job, in both debug
and `-d:release`.

## F2 — the viewer draws model text and nothing measured it

**What the code did.** Two classes of model string reach the viewer: the `radio` line
(DOM, `#killfeed`) and the `say` shout (server-composited sprite). `viewer_smoke.mjs` hooks
`CanvasRenderingContext2D.fillText/strokeText`; this renderer paints its board in an
OffscreenCanvas worker and its chrome in the DOM, so `canvas_text.total` was structurally
0 — "not evidence of anything", in the checklist's words — and there was no
`tools/ci/renderer_fixture.html`. The replay CI can produce carries `"radio": []`, because
`docker_smoke.sh` runs with no `ANTHROPIC_API_KEY`.

**What it does now.**

* `tools/ci/renderer_fixture.html` fetches the SHIPPED `index.html` out of the built
  bundle, injects one script that shims **only** the wasm entry
  (`window.VzdStaticReplay.createCore`, via a `defineProperty` getter, returning a core
  whose methods are no-ops), writes it into an iframe at 360, 640 and 1280 px, and hands
  the page's own `coreConfig.onText` a worst-case frame. Nothing about the drawing is
  re-implemented: the CSS, `chrome_common.js`, the game block and the feed's own row
  builder are the shipped ones.
* `tools/gen_renderer_fixture_frame.nim` emits that frame through **`buildStateJson`
  itself**, so it cannot drift into a shape the page never sees;
  `tools/ci/renderer_fixture_frame.json` is its committed output. Every string is at the
  cap the server enforces and deliberately WIDE (capital `M`s with a 4-byte emoji every
  eighth rune): 96-rune `radio` on **all eight seats at once**, 10-rune `say`, 160-rune
  `note`, the widest policy names, a `fallback` row, eight eyes thumbnails, a 13-point
  momentum series, 14 beats.
* Measurement is per **line box**, through the Range API, so a wrapped remark is judged on
  where its lines actually are rather than on the measuring script's font metrics. Each
  line is then mirrored onto a 2D canvas the size of the viewport at the box the layout
  gave it (font scaled so the mirrored advance is exactly the real one), which is what
  gives `--strict-text-bounds` something real to gate on a DOM renderer. The fixture also
  asserts its own strings are still full length.
* `ci.yml`'s `wasm-viewer` job runs it in **its own step**, `--strict-text-bounds`, against
  a copy of the bundle it just built.

**What the fixture found, and the layout fix that answers it.** At full cap the remark ran
936 px along one nowrap line where the feed column gives it 852 (1280 px board) and 316 px
where it gives 95 (360 px board) — painting across the board instead of reading against the
feed's own background. Per checklist item 15 the answer is a wider band, never a shorter
remark, so `.dm-radio` now wraps inside a row stretched to the feed's column
(`dm-radio-row`) and `#killfeed` reserves the taller band whether or not anyone is
speaking.

**Evidence.** In CI on the final head (run 33132259050, job `wasm-viewer` 98724586701,
step "Worst-case renderer fixture (model text at full cap)"), against the real
emscripten-built bundle:

```
{"loaded":true,"ms":3629,"clock":null,"scorebug":null,"feed_lines":15}
canvas text: 198 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
```

and locally, with the band removed, the same fixture goes red:

```
VIEWER SMOKE FAILED: data-replay-error: 9 layout failure(s): at 360px a model remark
spills 221px out of the killfeed band (95px wide): no room was reserved for a full-cap remark
```

**What it does not cover, stated plainly:** the `say` bubble is composited server-side in
`global.nim` and never reaches a browser, so no browser fixture can measure it; its bound
is `MaxSayRunes = 10` enforced in `sanitizeSay`. Noted, not fixed.

## F3 — the baseline tunables were not tuned by a working grid harness

**What the code did.** `baselines.nim` claimed its four tunables were "the grid harness's
pick, not a guess" and named three artefacts. `tools/ci/baseline_tuning.json` and
`tests/test_vzd_tuning.nim` did not exist; `tools/tune_baselines.nim` was byte-identical to
the starter's, importing `ctf/[sim, control, directives, baselines]` and sweeping
`holdline`/`sprayer` on hill-tick margin. It cannot compile here and nothing compiled it.

**What it does now.** `tools/tune_baselines.nim` is this game's harness: 36 cells
(`rusherHuntPx` × `sentryHuntPx` × `medPx` × `postRotation`), each cell three seeds played
from **both** sides through the real control layer on the real 108-tick turn cadence, 216
episodes of 1080 ticks in about 60 s of release build. It scores cells on the
rusher-vs-sentry team frag margin, picks the cell with the most episode wins (margin breaks
ties), writes the whole grid with `--write`, and with `--check` re-runs the sweep and exits
non-zero unless its winner is still what `baselines.nim` ships and what
`tools/ci/baseline_tuning.json` records. `ci.yml`'s `test` job runs `--check`.
`tests/test_vzd_tuning.nim` asserts the cheap half on every test run (shipped constants ==
recorded pick, the pick is the grid's own winner, the recorded head-to-head is the note's
target, the harness is this game's and sweeps all four knobs).

**The sweep moved two of the four numbers, and this is the substantive part of the fix.**
The note's own first guesses lose, and lose everywhere: at `rusherHuntPx: 520,
postRotation: 2` the rusher side takes **0 of 6** episodes at −52 frags. A long chase leash
walks four rushers into posted guns in the sentries' own half and converges them on the
same contact often enough to shoot each other — and after F5 a team kill costs the killer a
frag. The winning cell is `rusherHuntPx: 120, sentryHuntPx: 260, medPx: 360,
postRotation: 1` at **4 of 6 and +6 frags**, which is inside the note's stated target band
of [+2, +10]. Both first guesses are in the table, so the rows they lost are on the record.

**Evidence.** CI run 33132259050, job `test` 98724254977, step "The baseline tunables are
still the grid harness's pick":

```
baseline grid harness: rusher vs sentry, 1080 ticks, seeds [42, 7, 4711], each seed played from both sides
sweep pick: rusherHuntPx=120 sentryHuntPx=260 medPx=360 postRotation=1 (4/6 episodes, margin 6)
tune_baselines: OK — the shipped defaults are this sweep's pick
```

identical to the local run, on a different toolchain — so the sweep is reproducible, which
is what makes `--check` a gate rather than a coin flip.

**Consequence the judge should weigh:** §Scripted baselines of the design note still prints
`rusherHuntPx = 520` and `post index (seat div 2) mod 4` in its prose. I did not edit that
(the brief authorised design-note edits for F4's chrome patch only). The note also says
these numbers ARE the harness's pick and names the [+2, +10] target the new numbers hit and
the old ones miss, so the code and the note's *intent* now agree while the note's *prose
constants* are stale by two values. It is a one-line note edit if the coordinator wants it.

## F4 — `chrome_common.js` is not byte-identical, and the change was not recorded

**Not disputed.** The diff is real (line 14, a module-path comment; line 72,
`window.CTF_WIRE` → `window.VZD_WIRE`), and the note asserted the opposite in two places,
so checklist item 14's literal condition was false and its escape hatch was not taken.

**What changed.** The escape hatch is now taken properly: §Viewer → Chrome provenance
carries the patch as a diff, with why it is required rather than cosmetic
(`tools/gen_wire_constants.nim` emits `window.VZD_WIRE={…}` and
`Dockerfile.replay-viewer:55` hard-asserts `grep -q '^window.VZD_WIRE={'` on the bundled
`wire_constants.js`; a chrome reading `window.CTF_WIRE` would find an empty object and
silently default every wire constant), that it is length-preserving (three characters
twice — both files are 40 022 bytes), and that `tests/test_vzd_viewer.nim` pins the length,
the hash and the namespace both ways. The "kept byte-for-byte" table row and the test-33
entry now say the same thing. Both the repo copy
(`docs/plans/2026-08-27-vizdoom-deathmatch-design.md`) and the run copy
(`runs/2026-08-27-vizdoom-deathmatch/design.md`) carry it, as the brief allows.

The same commit drops `tools/tune_baselines.nim` from the note's "kept byte-for-byte apart
from names/paths" row, because F3 replaced it with this game's harness — which the note's
own test 20 asks for. That is the only other note edit in this round.

## F5 — `results.frags` counted team kills

**What the code did.** `applyFire` called `recordKill(shooter)` unconditionally and then
`recordTeamKill(shooter, target)`, so `p.kills` was enemy kills **plus** team kills and the
`- teamKills` term of `net = kills - teamKills - deaths` merely cancelled the frag it had
just added. A team kill cost its killer nothing, `results.frags` over-reported (seat 1's
`frags: 2` in the CI artifact included one team kill), and the design's test-9 invariant
`sum(deaths) == sum(frags) + sum(teamFrags)` — asserted in the tree at
`test_vzd_sim.nim:160-166` — was false whenever friendly fire killed. It was green only
because the 240-tick test episode happened to produce no team kill.

**What it does now.** `recordKill` fires only when the victim is on the other team, which
is design.md test 4 verbatim ("a team kill calls `recordTeamKill` and **not**
`recordKill`"). The new test in `tests/test_vzd_sim.nim` stands two RED cogs 40 px apart,
shoots one dead, and asserts `kills == 0`, `teamKills == 1`, `deaths == 1`, `net == -1`.
The existing `deaths == kills + teamKills` assertion is now true by construction rather
than by luck. This is also what makes the F3 sweep's finding real: with friendly fire
free, a rusher pile-up cost nothing.

## F6, F23 — a seat view no record can carry, rebuilt eight times a turn

`boundedDirectiveRecord`'s shrink order drops the view whole on the first pass, because a
seat view (sixteen rays, contacts, a three-mate block, a score block, and fifteen zones on
a first turn) is far past `MaxDirectiveRunes = 900` — 0 of the 80 records in the CI replay
carry a `view` key. `server.nim` nevertheless called `seatViewNode` for **every** seat on
**every** turn to build it, and each call re-scanned the wall mask for all fifteen zones
(~12 k reads a call, ~2.4 M an episode); while the block existed it also carried
`your_notes`, which the note defines as excluded. The record is now built without a view.

The note's two requirements here (a record that carries the observation; a 900-rune cap on
the whole record) are in tension **in the note itself** — the code had already resolved it
by always dropping the view, and this commit stops paying for the dropped block and closes
the private-note path. If the judge wants the view in the replay, that is a cap change or a
second record kind, i.e. a design change, not a fixer's call.

F23's other half: `engine.mapSent[seat]` is now set where the map is SENT (the prompt
build) rather than where a reply successfully parses. A seat that timed out kept
`mapSent = false` forever and re-sent fifteen zones every turn for the rest of the episode;
the note pins "the map, once, at its first turn".

## F7 — the `stop` record was written but never applied on playback

`sim.applyStopRecord` (`sim.nim`) is now the one proc that ends a game from a stop record,
and the server's two write sites and `replays.applyReplayEvents` all call it — the note's
"applied by the same proc on record and on playback". A second commit adds
`applyTrailingStop`: the two fault rules write their record one tick PAST the last hash (the
tick that raised never completed, so no hash was written) and playback stops stepping the
moment the chain is spent, so `advanceReplayPlayback` applies any trailing stop on the
frame playback ends, followed by one `onStep` so the `gameover` event still reaches the
chrome. It returns immediately once the game is over, so the wall-clock path — which
applies its stop inline, inside a hashed tick — is untouched. Both are covered by F1's
tests.

## F9 — the momentum graph plotted lives under a FRAG LEAD label

`scanTeamLead`'s hill-off branch was the starter's `teamLivesRemaining`. With `lives: 60`
the plotted difference is `deaths(other) - deaths(you)`: a graph that ignores every frag.
It now adds `sim.teamNet(team)` — the cumulative net frags, the same counter the scorebug,
the endcard and `results.teamNet` read.

## F10 — the endcard's five columns were fed four cells

The header emits `Cog | Frags | Deaths | Net | Acc` and the grid is five columns, but
`rowHtml`'s `PB_MODE` branch (the branch this game runs in) emitted four, the fourth being
`tr.paint` — a deleted mechanic's counter, 0 in every deathmatch. The row now emits the
five cells the header names: signed net (from the roster row's own `net`) and accuracy
(`sh / sf`, an em dash when the cog never fired). Both already ride every roster row.

## F18 — `MaxReplyBytes` was enforced as a rune cap

`truncateRunes(MaxReplyBytes)` admitted up to 16 KiB. `directives.truncateBytes` cuts at
the byte cap and backs up off any UTF-8 continuation byte, so the cut never splits a code
point. The new test feeds 4096 four-byte emoji and asserts ≤ 4096 bytes, still valid UTF-8,
and an ASCII reply passed through unchanged.

## F22 — `rusher` shouted "on it" every hunting turn

`scriptedDirective` now takes the seat's previous directive (an optional parameter, so the
tuning harness and the bounded-orders tests are unaffected) and stays silent when the cog
was already hunting; the decision engine threads it through `standingDirective(seat)` on
the scripted path and all five fallback sites. New test asserts shout-on-change,
silence-while-hunting, shout-again-after-hold.

## F24, F25, F26, F29 — the small true ones

* **F24** `results["map"]` now reports `sim.gameMap.name` (the resolved map: `gen-1004` for
  pool seed 42) rather than the config's `mapPath` ("pool"). New test pins the pool case,
  where the two differ; `arena` is unchanged.
* **F25** `replay_summary.py`'s `"tickCount"` was `len(data)` — the file's byte length.
  It now comes from the `result` record's `finalTick`, else the `stop` record's tick; the
  byte length keeps its own key. Checked against the CI smoke replay: `tickCount 1084`
  (`finalTick 1084`), `byteCount 40874`.
* **F26** the seat registrar's docs, startup echo and default `PLAYER_POLICY_LABEL` said
  `holdline | sprayer`; they now say `rusher | sentry`. Behaviour was already right
  (`parseBaseline` maps everything unrecognised to `rusher`) but the label rode into the
  replay's `register` record.
* **F29 (the tautology)** "the model and the viewer read the SAME walls" called `marchRays`
  twice with identical arguments. It now compares the model's 16-ray strip against the
  viewer's 96-column `fp` strip taken off `buildStateJson` — the wire the viewer reads — at
  their six shared bearings (column i of 16 and column 19i/3 of 96 are the same bearing).

---

## Findings NOT fixed, with reasons

These are advisory. None of them falsifies a checklist item, and each is a real scope call
rather than an oversight.

* **F8 — the pre-scan beat timeline can only contain `gameover`.** Real. The fix is to
  re-target `scrubberBeats` in `replays.nim:664` from the starter's flag vocabulary to this
  game's `{gamestart, kill, streak, lead, gameover}`. I left it because the beat markers do
  appear through the live `dmEvent` path and the change interacts with the momentum/lull
  pre-scan I already touched for F9; a second edit to the same scan in the same round is
  exactly the "while I was in here" the fixer brief forbids. **First candidate for r2.**
* **F11 — two team plates, not eight seat plates.** Real, and a viewer-shape change of some
  size (`ensureScorebug` iterates `activeTeams`). Checklist item 4 is satisfied either way
  (real names reach the viewer through `teamHeadline`, `#povBadge` and the endcard), which
  the reviewer says too. Deferred as a design-shape question, not a defect.
* **F12 — cones broadcast, nothing draws them.** Real. The board is composited in
  `global.nim` and rendered in the wasm worker; adding a cone family there is a new draw
  path plus its own legibility question. Out of a fix round's scope.
* **F13, F14, F15 — deleted mechanics gated rather than removed; their chrome still
  present; the label test is an allow-list.** Real and consequential, and all three are one
  piece of work: the vocabulary grep the note asks for (F15) cannot pass until the
  unreachable chrome (F14) is gone, and the label manifest cannot be regenerated until
  `labels.nim` loses the ctf vocabulary (F13). The gating itself is sound and CI green; the
  reviewer records that the page IS the starter's page, so item 14's page clause holds.
  A deletion pass of that size in a fix round would swamp the diff the judge has to read.
* **F16 — `drawStreakGlow` does not exist.** Real (the note names it). A streak halo on a
  worker-drawn board is the same new draw path as F12.
* **F17 — the helmet is an `<img>` overlay, not a `rig_art` composite.** Real. Compositing
  through `rig_art.nim` means new masters, pivots and `SoldierRotations` facings — an art
  pipeline change.
* **F19 — nine broadcast event kinds, not sixteen.** Real against the note. Seven new event
  kinds is a wire change plus a viewer change plus `test_vzd_events`'s closed-set assertion;
  the note's own effect (fallback rows, shouts, radio) is already delivered through the
  `directive` records, which the reviewer notes.
* **F20 — driver details.** Mixed. The `respawned` result and the ±32-brad aim sweep are
  genuinely absent (a behaviour change to `compileMask`, which the tuning record in F3 now
  depends on — changing both in one round would invalidate the sweep I just recorded).
  The `teammateInCorridor` half is a **provenance** claim in the note, not a defect: the
  reviewer confirms the predicate is correct and exercised over 500 geometries. The
  `firing` result on a seat whose trigger rule then refuses to press `A` is a report-vs-act
  mismatch worth a line in r2.
* **F21 — `contacts` lists all teammates and carries one memory row.** The teammate half is
  documented divergence 3 in the note ("teammates are not fogged"), which the reviewer
  acknowledges; the note's `contacts` sentence contradicts its own divergence list. The
  memory half is **NEEDS-DESIGN**: `ControlState` keeps ONE `knownEnemy` per cog, so "every
  enemy seen in the last 72 ticks" needs a per-cog memory list — a new structure in the
  control layer, and the control layer is what the F3 tuning record was measured against.
* **F27 — `llm.nim` keeps one haiku candidate.** Deliberate, and I recommend keeping it.
  The starter's own comment records that `sonnet-4-5` was removed after every call timed
  out; re-adding it as the failover would reintroduce a known timeout on the retry path,
  which is a checklist item 5 (`timeout`) risk taken to satisfy a note sentence. The note
  is authoritative on design, but this is the note asking for a behaviour the starter
  measured as broken. Flagging for the coordinator rather than shipping it.
* **F28 — `wasm_replay_smoke.cjs` has no fixtures; no `label_manifest.txt`.** Real. Both
  need a committed `.bitreplay` (recordable now that F1's helper exists) plus a CI step;
  worth doing, but it adds CI surface in the same round as two new gates (the sweep and the
  renderer fixture) and I would rather those two be judged on their own.
* **F29 (the other half) — the note's line-of-sight cross-check.** Not added, deliberately:
  `lineOfSightClear` is the BULLET predicate (glass blocks a bullet while the ray march
  sees straight through it) and the fog cache is cell-coarse, so neither is the right
  comparison for a per-pixel ray. I tried both locally; both fail on correct code. The
  cross-resolution check that IS meaningful is the one now shipped. The float-grep's
  missing `motion.nim` is F13 (the file does not exist).

## NOTED (not fixed), outside the review

* `tests/test_vzd_manifest.nim`'s rate-floor scope change is the reviewer's own
  "traced and consistent" note; nothing was done to it.
* The design note's §Scripted baselines prose still prints the pre-sweep constants (see
  F3). One line to correct if the coordinator wants the note to match the code exactly.
