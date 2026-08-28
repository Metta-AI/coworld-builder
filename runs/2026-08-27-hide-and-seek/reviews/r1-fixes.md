# r1 fixes — hide-and-seek

Repo: `Metta-AI/cogame-hide-and-seek` @ `main`
Reviewed sha: `a6d3a86cd1f545b6a031bc43d166c758d424776c`
Head after fixes: `5c819abc2b95b7a12ac49e3ebc8272321c5b027e`
CI: run **33131110037** (`ci.yml`, `main`, head `5c819abc`) — conclusion **success**
(all four jobs: `test` 6m16s, `docker-smoke` 1m49s, `wasm-viewer` 3m2s,
`renderer-fixture` 32s).

One commit per finding, in finding order within each push. Sixteen findings changed code
(F11 in two: the fix, then a fix-forward on the frame cost it introduced); four (F5, F9, F10,
F16) are refuted with evidence and left alone, as are three named sub-clauses inside F13, F14
and F20.

Every gate added this round reports evidence in run 33131110037:
`page_smoke: ok` · `manifest OK under the installed coworld CLI: hide-and-seek` ·
`pick: panelReach=200 chaseRadius=440 margin=-178` + `baseline tuning matches
tools/ci/baseline_tuning.json` · `ok: loaded replay.json, advanced 300 frames (66630361
packet bytes, heap 30 MB)` · renderer-fixture `{"loaded":true,…}` with
`canvas text: 0 drawn, 0 never inside the canvas … (--strict-text-bounds)`.

The sandbox has no `git push` over HTTPS (`Invalid username or token` for every credential
shape, while `git fetch` and `gh api` both work), so the commits were replayed onto
`refs/heads/main` through the GitHub Git Data API. Trees were compared after each push:
local `HEAD^{tree}` equals `origin/main^{tree}` at `f66cc7d4`.

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F1 | fixed | `5bb64f19` | `src/hns/control.nim:340`, `tests/test_hns_control.nim` | 7 |
| F2 | fixed | `c2fa7d01` | `src/hns/global.nim:507-533,700-712`, `tests/test_hns_viewer.nim` | 15 |
| F3 | fixed | `8323ede8` | `tools/ci/renderer_fixture.html`, `tools/ci/renderer_fixture_state.json`, `tests/test_hns_renderer_fixture.nim`, `.github/workflows/ci.yml`, `client/replay_broadcast.html` | 15 |
| F4 | fixed | `f1fa02a7` | `src/hns/sim.nim:629`, `tests/test_hns_sim.nim` | 9 |
| F5 | **no change — refuted** | — | `src/hns/decide.nim:474` | 9 |
| F6 | fixed | `b7ad7320` | `tools/tune_baselines.nim`, `tools/ci/baseline_tuning.json`, `src/hns/baselines.nim:49`, `tests/test_hns_control.nim`, `.github/workflows/ci.yml` | 7 |
| F7 | fixed | `5b651af3` | `src/hns/sim.nim:333-346,349,544`, `tests/test_hns_sim.nim` | — (note tick step 4) |
| F8 | fixed | `2e4bdf3b` | `src/hns/motion.nim:218-232,269-276`, `tools/ci/baseline_tuning.json`, `tools/ci/renderer_fixture_state.json` | — (note tick step 6) |
| F9 | **no change — refuted** | — | `client/broadcast_core.js` | 14 |
| F10 | **no change — refuted** | — | `client/replay_broadcast.html` | 14 |
| F11 | fixed (both halves) | `f66cc7d4` + `5c819abc` | `src/hns/global.nim:431-482,634-641`, `tests/test_hns_viewer.nim` | — (note readout 2) |
| F12 | fixed | `7d3c736d` | `tests/test_hns_determinism.nim` | — (note §determinism) |
| F13 | fixed (content); layout half refuted | `554b34f9` | `tests/test_hns_sim.nim` | — (note test 12) |
| F14 | fixed (reachability asserted); word-list half refuted | `630701db` | `tests/test_hns_events.nim` | 14 |
| F15 | fixed | `0a76325c` | `.github/workflows/ci.yml`, `tools/ci/validate_manifest.py` | 1, 10 |
| F16 | **no change — refuted** | — | `tools/ci/docker_smoke.sh` | 6 |
| F17 | fixed | `b540a9a6` | `src/hns/sim.nim:632-648`, `src/hns/decide.nim:187-199`, `src/hns/sim_types.nim:214`, `tests/test_hns_control.nim` | — (note §observation) |
| F18 | fixed | `4751a5c4` | `tests/test_hns_engine_support.nim`, `tests/test_hns_replay.nim` | 2 |
| F19 | fixed | `ad72ed50` | `tests/test_hns_sim.nim` | 1, 7 |
| F20 | fixed (three of four); bridge-wording half refuted | `04965da4` | `src/hns/decide.nim`, `src/hns/server.nim` | — (cosmetic) |

---

## Blocking

### F1 — `knownEnemy` had no success path (`5bb64f19`)

**Was:** the proc returned early on both failure branches and then fell off the end, so Nim
returned the zero-initialised implicit `result` — `known: false` — whenever an enemy *was*
known. **Is:** the starter's two closing lines are back
(`/workspace/starters/coworld-ctf/src/ctf/control.nim:307-308`), verbatim.

**Consequence removed:** `seen_enemies` was `[]` in every prompt of every episode; `intChase`
resolved its goal to the cog's own feet (a stand-still); burrow's flinch and chase rules and
scatter's flinch and chase rules could never fire.

**Evidence:** `tests/test_hns_control.nim`'s new `knownEnemyReportsASighting` block fails on
the pre-fix proc — run against a stashed `control.nim`:
`test_hns_control.nim:159: knownEnemy reported no enemy for a cog looking at one`. It puts a
hider and a seeker inside the vision bubble, refreshes the fog through the sim's own
`refreshPlayerFov`, and asserts the sighting is reported with the seen position and
`ticksAgo == 0`; that `burrow`'s seeker turns it into `intChase`; that `ctl.goalFor` resolves
that chase to the **enemy**, not the seeker; and that the memory expires after
`HuntMemoryTicks`.

**Blast radius, re-measured (the coordinator's follow-up):** the tuning sweep was re-run —
see F6. `flinchRadius` is still flat after the fix, `chaseRadius` is not, and the recorded
grid moved from a flat `[-99, -300, -250]` to a real surface.

### F2 — the shout bubble was placed unclamped (`c2fa7d01`)

**Was:** `packet.addBoardObject(objectId, shout.x - art.w div 2, shout.y - SoldierBodyPx -
art.h, …)` with no clamp on either axis. **Is:** `shoutBubblePlacement`, ported from the
starter's proc for exactly this (`src/ctf/global.nim:3950-3972`): flip below the tail tip
when the bubble does not fit above, then clamp both axes into the board rect.

**Measured, not inferred.** A probe built the real bubble art for a full-cap 10-rune say and
printed the naive placement at every pocket anchor of `warren`:

```
art 67x19
pocket 40,40   naive y=-13  naive x=7   placed=(x: 7, y: 12)
pocket 680,40  naive y=-13  naive x=647 placed=(x: 647, y: 12)
pocket 288,40  naive y=-13  naive x=255 placed=(x: 255, y: 12)
```

Three of the room's eight pockets — the anchors the `hide` intent parks hiders on — put the
bubble body 13 px above the top of the board, where the map layer canvas clips it to a sliver.

**Evidence:** `tests/test_hns_viewer.nim`'s `shoutBubblesStayInsideTheBoard` asserts a
full-cap say at every board corner **and at every pocket anchor of the room** lands wholly
inside the board.

### F3 — no worst-case renderer fixture (`8323ede8`)

**Added** `tools/ci/renderer_fixture.html`, driven by
`node tools/ci/viewer_smoke.mjs --url … --strict-text-bounds` in its own `ci.yml` job
(`renderer-fixture`).

* It loads the **real** `client/replay_broadcast.html` — the bytes the bundle's `index.html`
  is spliced from — into an iframe with the three splice markers substituted, and shims
  **only the wasm entry** (`window.HnsStaticReplay.createCore`, the slot where
  `static_replay.js` installs the Worker that owns the board's OffscreenCanvas). Nothing here
  re-implements a draw: every row on screen is rendered by the page's own
  `hnsEvent`/`hnsDirectives`/`pushFeed`.
* The frame it hands the page is `tools/ci/renderer_fixture_state.json`, built by the
  **shipped** `src/hns/broadcast.nim` off a real sim and regenerated by
  `tests/test_hns_renderer_fixture.nim`, which fails the build when the committed copy drifts
  from what `buildStateJson` produces. It carries a full-cap 10-rune `say` on **all six
  seats**, a full-cap 96-rune `radio` on all six directives, three locked objects, a sealed
  fort, a vault in flight and a full exposure ribbon.
* It asserts its own strings are full-length (in Nim, at build time, and again in the browser
  before it pushes the frame — a fixture whose remark was quietly shortened would otherwise
  pass while testing nothing), that every row carrying one is wholly inside the frame at
  **360, 720 and 1280 px**, and that none is clipped by its box; then sets
  `data-replay-loaded="true"`, or `data-replay-error="<what failed>"` on the first failure.

**It found a real defect on its first run, and this commit fixes that too.** The inherited
kill-row rule is `white-space: nowrap; max-width: none`, sized for a 10-char name, and
`#killfeed` is `align-items: flex-end` — so a full-cap radio row grew *leftward* off the
board:

```
VIEWER SMOKE FAILED: data-replay-error: at 360px a feed row crossed the left edge
of the 360x203 frame: [-64,139,307,146] "SEEKER-beta:“seat 3 radio WMWMWM…"
```

A remark row now carries `.hns-remark` and gets a reserved band — the feed's own width, which
`#stage.tiny` already narrows — and wraps inside it. The band is widened; the text is never
shortened (item 15's rule for sentences).

**CI evidence:** job `renderer-fixture` green (29 s) in run 33130098943 and again in
33130525081. Its `canvas_text` line reads `0 drawn, 0 never inside the canvas … 0 ellipsized
(--strict-text-bounds)`, and that is **expected and stated in the fixture's header**: this
game draws no `fillText`/`strokeText` anywhere — the board's speech bubble is a sprite
rasterised in Nim (`buildShoutBubble`) and composited with `drawImage`, and the feed is DOM.
The fixture's own DOM assertions are the gate that measures this game's model text; the
bubble's placement is measured where it is computed (F2's unit test).

### F4 — `results.stopDetail` reached the replay untruncated (`f1fa02a7`)

**Was:** `forceFaultStop` stored the caught exception's `msg` raw and `roster.nim:520` put it
into the results document, which `resultRecord` embeds in the replay's `result` record.
**Is:** `sanitizeLine(detail, MaxFallbackDetailRunes)` inside `forceFaultStop`, so the cut
happens in the one proc that **both** the recording and the playback apply — the two cannot
disagree — and the stop record's existing cut (`server.nim:2019`) is unchanged.

**Evidence:** `tests/test_hns_sim.nim`'s `faultStopDetailIsRuneTruncated` feeds 240 4-byte
emoji and asserts `sim.stopDetail` and the emitted results document are both exactly 200
runes and valid UTF-8. On the old code it fails:
`test_hns_sim.nim:385: stopDetail was not cut to the rune cap: 240`.

---

## Non-blocking, fixed

### F6 — the tuning record (`b7ad7320`)

Three defects in one finding:

1. **Measured with F1 broken.** Re-run with F1 and F7 in place; `tools/ci/baseline_tuning.json`
   now records what the harness measures (and is re-recorded again in F8, where a sim change
   moved it).
2. **The second axis measured nothing.** `flinchRadius` is *still* flat after F1 — a hider
   only flinches from a seeker it can **see**, and one parked in a pocket facing its own door
   sees one inside 220 px too rarely to move six episodes. The swept axis is now
   `chaseRadius`, which moves the margin by ~170 permille across the same nine cells;
   `flinchRadius` is still **measured**, as a three-point probe at the pick, and the flat
   result is written into the record (`"flinchProbe"`) instead of being implied. The pick
   moves `chaseRadius` 340 → 440 in `DefaultBaselineParams`.
3. **The test checked the file against itself.** It now reads `MarginLo`/`MarginHi` from the
   harness, asserts the recorded band **is** the harness's band, and asserts the grid measured
   at least three distinct margins — which the pre-F1 record (three margins, each repeated
   three times) fails.

Plus the `ci.yml` step the note names and the review found missing: the `test` job runs
`tools/tune_baselines.nim --check` (~15 s in release).

**Not fixed, stated plainly:** the margin is still **negative** (−178 after F8), so `burrow`
does not beat `scatter` as a hider and the note's `[+80, +400]` target is unmet. No cell of
the grid reaches the band. The harness comment records the measured range and names the cause
(the push driver stalling against wall corners and 56 px doorways); closing it is a design
change to the baseline, not a fix, and is flagged below under NEEDS-DESIGN.

### F7 — a held object was not dropped at the phase change (`5b651af3`)

`resolveGrabs` dropped on `C` released, on `pushBlockedTicks >= GrabBreakTicks` and on
`airborne`; the note's tick step 4 also names "or the phase changed, or the game ended".
Adds `dropAllHeld`, called at the prep→hunt transition and at the top of `finishGame`, inside
the sim so record and playback drop on the same tick. `tests/test_hns_sim.nim`'s
`aPhaseChangeAndAGameEndDropTheHeldObject` covers both triggers and fails on the old sim:
`the release did not drop the held crate: a hider carried it into the hunt`.

### F8 — the blocked-push velocity rule and `accel` (`2e4bdf3b`)

Both divergences the finding names are now the note's rule: the velocity on the blocked axis
is zeroed **for the held pair only** (a plain wall bump keeps the starter's behaviour, which
is what the note describes), and `carrySpeedPct` scales the speed cap only, not the
acceleration. Both are hashed sim state, so the tuning record is re-recorded from the same
harness in the same commit: the pick is unchanged (panelReach 200 / chaseRadius 440) and the
grid moves from `[-467, -276]` to `[-445, -178]` permille — the push completing more often is
exactly what the harness comment says the margin is dominated by. The renderer fixture frame
is re-recorded in the same commit for the same reason.

### F11 — the cone was drawn unclipped, and cost a frame (`f66cc7d4`, `5c819abc`)

The wedge is now masked by `fovVisibleAt` — the cog's own fov cache, refreshed by the sim
this tick — so the drawn cone **is** the sim's answer rather than a second implementation of
it, and an unrefreshed cache degrades to exactly the old unclipped wedge. The sprite's dedup
key gains the cog's position and the geometry epoch, which the clipped pixels now depend on.
I rendered the room, the objects and all six cones to a PNG and looked at it: beams stop at
masonry and are cut by crates and panels. `theVisionConeStopsAtAWall` asserts alpha > 0 on
the near side of warren's r3/r2 wall, 0 beyond it, 0 two rooms away.

**NOTED (not fixed):** the per-frame rasterisation cost (a 682×682×4 buffer per cog per
frame). The clip changes which pixels are filled, not the allocation. Cutting it needs a
tight bounding box and a per-aim sprite offset — a renderer change, not a fix. The one
measurement in hand is still CI run 33125685503's soak: ~19.8 ticks/s on the 900-tick fixture
against a 24 fps target.

### F12 — vision.nim was outside the determinism grep (`7d3c736d`)

`vision.nim` cannot join the integer-only list — it *is* the starter's float cone filter, kept
because it is already the mechanism the native↔wasm chain survives. So the fix pins **where**
the floats are: a per-proc float-bearing line count for `castFovOctant`,
`computeFovShadowcast`, `applyFovCone` and `playerVisibleTo`, with any float-bearing proc
outside those four failing the build. Verified to bite: a two-line `bogusFloat` proc added to
`vision.nim` fails with `is a NEW float-bearing proc (2 lines) on the hashed path`.

It also asserts what the note's test 14 is really after and no test stated: the airborne cone
test and `applyFovCone`'s are the **same expression** — the same
`cos(float(sim.config.visionConeDeg) * PI / 180.0)` and the same `coneCos * sqrt(…)`
comparison, twice each — so the airborne path cannot drift onto a different libm call from
the one the starter's chain survives. No sim code changed: rewriting the airborne cone in
integers is a change to hashed math, a bigger risk than the finding.

### F13 — two clauses of test 12 (`554b34f9`)

`win == (scorePermille > 0)` and "an all-zero margin leaves every `win` false" were
implemented at `roster.nim:490` and asserted nowhere. Both are now asserted **off the emitted
results document** — the thing the league reads — inside the existing 500-state randomised
scoring block and in a new all-zero-margin block. The finding's structural half is refuted
below.

### F14 — the dead paintbot chrome (`630701db`)

The review calls the surviving `buildFlag`, `.ec-heart`, `.squad-pip` and `ACH_FOCUS`
unreachable **by inference**. This commit turns the inference into an assertion rather than
deleting inherited code in the region checklist 14 diffs for provenance: over the full
worst-case frame (six seats, every readout populated) the broadcast state carries no `ach`,
`flags`, `hearts`, `lives`, `caps`, `hills` or `paint`; no roster row carries
`lives`/`alive`/`kills`/`hp`/`perks`/`carry`; no beat is a `capture`. That is exactly the set
of fields those four pieces of chrome are gated on. Verified to bite: adding `lives` to one
roster row fails the build. The word-list half is refuted below.

### F15 — three CI gates the note names and CI did not run (`0a76325c`)

* `tools/ci/page_smoke.mjs` was reachable only through `tests/test_hns_viewer.nim`, which
  **skips itself** when `node` is absent — its coverage depended on a runner detail. Now its
  own step in the `test` job.
* The note's test 34 (the installed CLI's own `validate_upload_manifest` /
  `_load_template_manifest`) did not exist anywhere in `ci.yml`. Adds
  `tools/ci/validate_manifest.py`, which installs the pinned `coworld==0.1.43` and calls
  `_load_template_manifest` with the compose image placeholders (read with PyYAML, so it needs
  no docker and runs in the `test` job). Run locally against the shipped template:
  `manifest OK under the installed coworld CLI: hide-and-seek`.
* The note's test 45 (`tools/wasm_replay_smoke.cjs`) was committed and invoked by no workflow.
  It now runs in `wasm-viewer` against the emitted bundle and the smoke replay — the only
  place wasm32-only failures (32-bit `int` traps, 2 GB address-space exhaustion) are visible.

The finding's fourth item, the tuning `--check`, is in the F6 commit.

### F17 — the shout jitter (`b540a9a6`)

`decide.nim` put `shout.x, shout.y` — the shouter's exact pixel — into `heard[]`. Ports the
starter's `shoutOffset` (`src/ctf/global.nim:3946-3957`) as `shoutHeardAt`: a deterministic
hash of the shout's own `(tick, x, y)`, bounded by the starter's 20 px and clamped to the
board. A pure function rather than an RNG draw, deliberately — it needs no stream of its own,
is identical on every target and in every replay, and so cannot desynchronise a hash chain
(the note calls it "draw 4"; a function of already-hashed values is strictly stronger than a
fourth stream, and adds no hashed state). The test asserts the offset is bounded, on the
board, pure, that it actually moves the point, and — through the real `seatViewJson` — that
no seat is handed a shouter's exact pixel.

### F18 — no shout in the re-derived recording (`4751a5c4`)

`recordEpisode` never called `applyShout`, so the replay the re-derivation test consumes
carried only `{`-prefixed control records — and a shout is the **one** chat record that moves
hashed state (`recentShouts` is in `gameHash`). The recorder now writes it exactly as
`server.nim:1938-1941` does, in the same order relative to the directive record and the step,
and forces one per cog on turn 1 so a recording cannot silently fall back to zero shouts.
`recordThenReDeriveFullTime` asserts the recording really carried them.

### F19 — three weak assertions (`ad72ed50`)

* **keep-clear**: the old loop asserted a property `canPlaceObject` makes true by
  construction. 200 randomised attempts now walk an object one pixel at a time straight at a
  seeker pad through the guard the push path uses, asserting after every accepted step that it
  is outside every disc **and that it ends outside** — the disc really stops it — and a real
  driven push (a cog holding the nearest object and walking it at the pad for 200 ticks)
  agrees.
* **vault**: every launch/airborne/landing assertion sat inside `if game.vaultSpanClear(...)`.
  The block now searches all three rooms for a ramp with a clear span, **fails if none has
  one**, and asserts the launch, the airborne duration and the landing unconditionally.
* **sealed scan**: the walled-in positive case, the same wall unlocked, the cog-sized gap and
  "only at turn boundaries" are all asserted now, by laying a hider-locked panel over
  `warren`'s one door into r1.

### F20 — cosmetics (`04965da4`)

`installOrder`'s two `discard`ed parameters are gone from the proc and its five call sites
(provenance travels in `sources[]`/`latencies[]`, and the doc comment now says so); the stray
`discard index` is gone; the four "holdline baseline" mentions are `burrow` — one of them
(`server.nim:1503`) was not a comment at all but the text of the `declarePlayerFailure`
payload the platform receives, so it named a policy this game does not ship.

---

## No change — refuted

### F5 — the byte-index slice on the model reply path

**Agreed as reported, and it is not a defect.** The review itself traces both paths the cut
string can take and finds neither carries the broken tail, and the slice is the design's own
rule (§Reply schema: "≤ 4096 **bytes** read from the provider before parsing"). Changing it to
a rune cut would violate the note. `decide.nim:474` unchanged.

### F9 — `client/broadcast_core.js` is the starter's file

**Refuted as a code defect; it is a doc-vs-code mismatch, and the code is right.** The
review's own words: "nothing is missing functionally". The board drawing this game needs is
server/wasm-side in `src/hns/global.nim` (objects, padlocks, cones, tethers, the spotted
ring), which is where it has to be — the same module compiles natively for the server and to
wasm for the viewer, which is the whole reason this starter was chosen. Adding `drawRoom`,
`drawObjects`, `drawCones` … to `broadcast_core.js` would be a **second** renderer in JS, the
particle-worlds 2026-08-26 scar. For checklist 14, a 4-changed-line diff from the starter's
file is the strongest provenance available; making the code match the note's prose would
weaken item 14, not strengthen it. I cannot edit the design note (fixer scope), so this is
recorded here.

### F10 — `replay_broadcast.html` is not "starter bytes then an append"

**Refuted as a defect.** Item 14 asks for "the starter's page with a game block appended under
a banner comment … present and unmodified **except for the removals the note lists**" — which
is exactly what the file is: 165 843 B against the starter's 234 070 B (71 %, consistent with
the enumerated deletions), `chrome_common.js` byte-identical, all 41 inherited ids present,
`#viewpanel`/`#minimap*`/`#zoom*`/`#fpv*`/`#povBadge` gone. The note's test 36 states a
stronger property ("begins with the starter's bytes up to the splice marker") that the
*required deletions above the banner* make unsatisfiable: you cannot both delete `#viewpanel`
and keep every preceding byte. The shipped test asserts the achievable property. Nothing in
the tree is weaker than checklist 14 requires. (This round's one edit above the banner is the
`.hns-remark` rule in F3 — a *rule added below the removals*, in the feed section, to give a
model sentence a band; it is documented in place.)

### F16 — `docker_smoke.sh` does not fail on `reason == "fault"`

**Refuted: changing it would break checklist 6.** Item 6 requires `tools/ci/docker_smoke.sh`
to be the shared template with the three documented substitutions, and the review confirms it
is (`diff` against the template: 5 hunks, all `<slug>`/`<IMAGE>`/`<SEATS>`). Adding a
fault check or an expected-key set would fork the template — the note over-claims, and the
right place for that claim to be fixed is the note. The smoke does print the reason
(`smoke OK: seats=6 results=931B replay=34421B reason=complete` in every run cited here), and
the four seat-count invariants it *does* enforce are the ones item 6 names.

### F13 (structural half) — missing test FILES

**Refuted.** `tests/shard_1..4.nim`, `test_hns_scoring.nim` and `test_hns_tuning.nim` do not
exist because `ci.yml:115-150` runs **every** `tests/*.nim` individually in debug *and*
release, which is strictly more coverage than four shards, and the asserted content is
located (the review found all of it). Nothing is lost and nothing is skipped. The clauses that
really were missing are fixed in `554b34f9`.

### F14 (word-list half) — the endcard vocabulary test

**Refuted: the note's word list is unsatisfiable while checklist 14 holds.** `kill` occurs in
`#killfeed`, `flag` in the inherited core's `ZoomableFlag`/`layer.flags`, `POV` in
`togglePov`, `Lives` in `.lives-num` — all inherited chrome the viewer test and item 14
require to be *present*. The shipped phrase-level test is the achievable form of the same
rule, documents its narrowing in-file, and `git log -p -- tests/` shows it was **tightened**
during this run (`c7e4020`: four forbidden phrases and one required string added), never
loosened.

### F20 (fourth item) — the embed bridge posts `boot`/`frame`/`esc`, not `ready`

**Refuted: wording only, and the page is the starter's.** The same three messages are posted
by the starter at `src/ctf/client/replay_broadcast.html:1917, 1987, 2040, 3993`. The load
marker checklist 13 actually requires — `data-replay-loaded="true"` on `<html>` — is set by
`static_replay.js:158-162` and is what the smoke reads (`loaded: true` in every cited run).
`viewer_smoke.mjs` accepts a bridge `ready` only as a legacy fallback.

---

## NEEDS-DESIGN (recorded, not done)

* **`burrow` does not beat `scatter` as a hider.** The note's target is a `[+80, +400]`
  permille margin; the harness measures −178 at the pick and no cell of the nine-cell grid
  reaches the band. This is not a constant to re-tune — the swept axis moves the margin by
  ~170 permille and every cell is still negative — it is the shape of the two baselines and
  the push driver stalling in doorways. Changing it means changing what `burrow` does, which
  is a design decision, so it is recorded rather than made. The harness's own comment carries
  the measurement and names the cause.

## NOTED (not fixed)

* **`GameVersion`** was not bumped this round. Nothing changed `data/rooms/*.json`, the replay
  wire format or the `gameHash` field order; F7, F8 and F17 change sim *behaviour*, so replays
  recorded before this round replay to different states — but they also carry the old masks
  and the old hashes, and the version gate exists for format compatibility, not behaviour.
  Flagging it because it is a judgement call a judge may want to re-make.
