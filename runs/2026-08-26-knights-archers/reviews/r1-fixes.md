# r1 fixes — knights-archers

Head: `d1ea75dbb2c11b7e3ff99005bd75888b5dfcbb83`
CI: https://github.com/Metta-AI/cogame-knights-archers/actions/runs/32973353268 — **success**
(previous head `6508ce81`, the whole code stack, is green independently:
https://github.com/Metta-AI/cogame-knights-archers/actions/runs/32972352143 — **success**,
all four jobs `test` / `docker-smoke` / `text-fixture` / `wasm-viewer`)

Repo: `Metta-AI/cogame-knights-archers`, base reviewed `00cc62a`. 22 commits, one per finding
(three exceptions, each stated below). No test was weakened, skipped or deleted; every test change
in this round is additive except two assertions that had to move because the thing they pinned was
the defect (`test_viewer`'s pressure-bar rule, `test_observation`'s key list).

Pushes were made through the GitHub Git Data API, not `git push`: HTTP Basic auth hides the token
from this sandbox's egress swap, so `git push` returns "Invalid username or token" while the API
works. Content, messages and parents are identical; the local shas were rewritten by the API, which
is why the shas below are the remote ones.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `6488886` | tests/test_control.nim:105 |
| B2 | fixed (2 commits) | `01cc35a`, `ed7c6bc` | tests/test_shouts.nim, replay-viewer/text_fixture.html, .github/workflows/ci.yml:223, tests/test_viewer.nim:200, client/replay_broadcast.html:4072 |
| N1 | fixed | `f414e98` | src/kaz/llm.nim:209, src/kaz/sim_types.nim:856, docs/RULES.md:29, coworld_manifest_template.json:630, tests/test_combat.nim:120 |
| N2 | not fixed — code is right, note is stale | `d1ea75d` (doc) | src/kaz/sim_types.nim:827, src/kaz/control.nim:24 |
| N3 | not fixed — code is right, note is stale | `d1ea75d` (doc) | src/kaz/control.nim:358 |
| N4 | not fixed — code is right, note is stale | `d1ea75d` (doc) | src/kaz/baselines.nim:149 |
| N5 | fixed (behaviour pinned) | `f15b38d` | tests/test_combat.nim:15 |
| N6 | fixed (row 2); row 1 deliberately unchanged | `6d4cc44` | src/kaz/sim.nim:3727 |
| N7 | fixed (the duplicate reset); rest not fixed | `ee5397e` | src/kaz/sim.nim:425 |
| N8 | fixed | `2b3c2c4` | src/kaz/horde.nim:203 |
| N9 | **DISPUTED** | — | src/kaz/decide.nim:368 |
| N10 | fixed | `9a5aaac` | src/kaz/decide.nim:188, tests/test_observation.nim:67 |
| N11 | fixed | `384ee82` | src/kaz/decide.nim:44,72,196, tests/test_observation.nim:81 |
| N12 | fixed | `ac843a4` | src/kaz/directives.nim:188, tests/test_directives.nim:50 |
| N13 | not fixed — code is right, note is stale | `d1ea75d` (doc) | src/kaz/decide.nim:444 |
| N14 | fixed | `de117b4` | tests/test_engine.nim:135, tests/fixtures/fake_bedrock.py |
| N15 | fixed | `061d153` | client/replay_broadcast.html:4032,4380, tests/test_viewer.nim:97 |
| N16 | fixed | `cdc9175` | client/replay_broadcast.html:4117, tests/test_viewer.nim:207 |
| N17 | fixed | `69de111` | src/kaz/sim_types.nim:2218, src/kaz/sim.nim:3489, src/kaz/broadcast.nim:235, client/replay_broadcast.html:4451, tests/test_combat.nim:70 |
| N18 | fixed | `6f8b057` | src/kaz/replays.nim:544, src/kaz/broadcast.nim:922, client/replay_broadcast.html:1895,4383, tests/test_viewer.nim:200 |
| N19 | fixed (comment) | `d8eafb1` | client/replay_broadcast.html:3945 |
| N20 | not fixed — code is right, note is stale | `d1ea75d` (doc) | Dockerfile.replay-viewer |
| N21 | **NEEDS-DESIGN**, recorded in-repo | `d1ea75d` (doc) | src/kaz/paint.nim, src/kaz/sim.nim:171 |
| N22 | fixed | `7d1da07` | src/kaz/decide.nim:451, src/kaz/llm.nim:1,10, src/kaz/server.nim:1898, src/kaz/sim.nim:4240 |
| N23 | fixed | `6829951` | tests/test_horde.nim:186 |
| N24 | fixed | `a9dd4fd` | tests/test_control.nim:150 |
| N25 | not fixed — judge's call, evidence below | — | src/kaz/server.nim:800 |

One extra commit is not a finding: `6508ce8` "a doc comment inside a `%*{}` literal does not
compile" — my own break, caught by CI on the N10/N17 push and fixed forward in the next one.

---

## B1 — no test asserted `results.reason == "complete"` (checklist item 7)

**What it did:** nothing anywhere compared a reason to `complete`. `test_replay:152` asserts enum
*membership* (passes on `fault` and `deadline`); `test_endings` pins the `deadline` and `fault`
cases; `docker_smoke.sh:306` *prints* the smoke's reason and never compares it. So a rules change
that turned every scripted episode into `sim_fault` — the guard at `sim.nim:3685` raises on any
invariant trip — would have left the whole Nim suite green, because `test_control`'s head-to-head
only compares two baselines to each other and both would degrade together.

**What it does now:** `tests/test_control.nim`'s new `anAllScriptedEpisodeReachesItsNaturalEndAsComplete`
plays a four-seat all-scripted episode (`maxTicks 2304`, `maxGames 2`, the shipped values) to its
natural end through the sim's own phase machine and asserts `run.reason == ReasonComplete`,
`results["reason"] == "complete"`, `results["games"] == 2`, that the endRule is neither `sim_fault`
nor `host_error`, and — item 7's other half — that every one of the >1000 masks the run emitted is
inside its legal bounds.

**Evidence:** CI run 32972352143, `test` job, `test_control: ok` in both debug and release. Checklist
item 7.

## B2 — the viewer drew model text and nothing measured it (checklist item 15, last bullet)

Two commits, both finding B2: the gate, then the defect the gate found. I split them because the
second is a behaviour change to the chrome that has to be reviewable on its own.

**`01cc35a` — the two gates that were missing.**

*The sprite half.* A `say` is LLM-authored and becomes a real in-game shout whose bubble is
rasterised into sprite pixels inside the sim (`global.nim:4066 buildShoutBubble` →
`blitFontText`), so the browser never calls `fillText` for it and `viewer_smoke.mjs`'s instrument
is structurally blind: the reviewed run's artifact said `canvas_text {"total": 0}`. The starter
ships the gate that *can* see it, and this fork inherited `shoutBubbleMaxHeight` /
`shoutBubbleRectFor` with **zero callers**. `tests/test_shouts.nim` is that gate, adapted: a
full-cap `"WWWWWWWWWW"` on **every** cog at nine worst-case positions (top edge — the cogchemists
case — four corners, side walls, centre) asserted through the draw pass's own geometry, plus the
flip-below-the-tail case, the pure-clamp case, the four says the scripted baselines actually emit,
and that the reserved band is a function of the cap rather than of what happens to be said.
CI prints `worst-case bubble top y = 0 (reserved band 19 px, board 1235x659)` and `test_shouts: ok`.

*The DOM half.* `replay-viewer/text_fixture.html` is the worst-case renderer fixture the checklist
requires. It is not a mock: it fetches the real `client/replay_broadcast.html`, injects every
`<style>` block and the real body markup, evaluates the real appended KNIGHTS-ARCHERS game block
(the page's last `<script>`) and drives it through its own public entry points —
`buildPlates` / `plates` / `frame` / `event` — with a frame built to hurt: a full-cap 160-rune
`note` and a full-cap `say` on **all four seats at once** (twice: the widest glyph with no break
opportunity, and a full-cap sentence with spaces), plus the worst-case kill/lunge/casualty/breach
rows, at four canvas sizes including the 360 px featured embed, with the inherited `feedin`
entrance animation **played through to settle** (measuring mid-flight read 12 px of settling
transform as 12 px off-frame). It mirrors relayout()'s own sizing loop, measures every drawn string
**line by line** (per-character Range rects grouped into line boxes, so a text node that overflows
its own element is caught), asserts every line is inside the frame, asserts its own strings are
still full length (`the full 160-rune note survived on 4 of 4 rows` — one shortened remark would
leave it passing while testing nothing), asserts no sentence was ellipsised, and additionally
asserts the two viewer defects below cannot come back (pressure strip vs plates, chalk caption on
the board). It draws every measured line into a real 2D canvas at the position and font the DOM
used, so `--strict-text-bounds` gates a real number, and it reports through
`data-replay-loaded` / `data-replay-error`, which is what `viewer_smoke.mjs` fails on.
`ci.yml` gains its own `text-fixture` job/step driving it, and `tests/test_viewer.nim` asserts both
the page and the step still exist.

**Evidence:** CI run 32972352143, `text-fixture` job, step "Render the worst-case text fixture in a
real browser": `{"loaded":true,...}` and
`canvas text: 204 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
`total` is 204, not 0. The fixture's own report reads `OK — measured 204 text line(s) across 8
case(s)` with `4 feed rows` in every case.

**`ed7c6bc` — what the fixture found on its first run, at every canvas size.** The inherited
`.feed-row` is sized to its content (`max-width: none; white-space: nowrap`) because every string
the *starter* puts in the feed is a pre-bounded 10-char name. A commander line is a sentence of up
to 160 runes: measured at full cap it was 1829 px of text in a 365 px column, so the row grew out
of **both** sides of the frame — 803 px past the left edge at 1280×800 and 267 px past it in the
360 px embed. The model's words were partly unreadable in every replay that carries them, and
nothing could see it. Item 15 says widen the band rather than shorten the text, so the game block's
own four row classes now wrap inside the feed column (border-box, `max-width: 100%`,
`overflow-wrap: anywhere`, right-aligned) and the feed grows upward into the four-row reserve
`#killfeed` already keeps. No text is truncated and no ellipsis is introduced; the fixture goes from
64 failures to 0. Verified locally against the committed page and in CI.

## N1 — the system prompt told the model 0.75 s where the sim gives 0.92 s

`sim.nim:3470` sets `fireCooldown = knightCooldown + swingTicks` = 18 + 4 = 22 ticks and
`test_combat` already pinned that, so the swing *period* is 0.92 s. `llm.nim:209` promised every
model "once every 0.75 seconds" — a 23 % faster mace than exists. `baselines.nim:151` and
`docs/COMMANDING.md` already used the true figure; the prompt, `docs/RULES.md` and the manifest's
rules page did not. All three now quote the period, the constant's doc comment says it is the tail
cooldown rather than the period, and `test_combat` asserts the period is 22 ticks **and** that the
prompt and RULES.md quote it. No rule changed. Evidence: `test_combat: ok`.

## N5 — the wedge's shape, pinned

The code is what stands (it is the starter's arc-cone machinery and what `tune_baselines` tuned
`phalanx` against), so the fix is a test that says which reading it is: dead ahead in at the reach
and out one pixel past it, a 45° body at 68 px of true distance **inside** (its forward projection
is 48 px), a 60° body outside at any distance, and the sim itself killing the 45° body its geometry
claims to reach. A future change to either reading is now a decision instead of an accident.

## N6 — the guard's last row

`zombiesKilled - (zombiesKilled - waveKillsSoFar) + aliveZombies > zombiesSpawned` is
`waveKillsSoFar + aliveZombies > zombiesSpawned` reached through a no-op subtraction; it is written
directly now, with the reason the terms must be per-wave. Identical arithmetic.
**Row 1 (the arrow bounds) is deliberately unchanged:** an arrow is pruned by range, not geometry,
and tightening a guard whose only action is to fault the episode would trade documented slack for a
new way to lose a match. Recorded rather than silently skipped.

## N7 — one of two `resetHorde()` calls in `startGame` removed

It is idempotent and consumes no RNG, so the second call did the work and the first did nothing —
but two calls read as if one of them mattered. The remaining call is the one carrying the comment
about why the RNG stream is not re-seeded. The rest of N7 (the extra `pushZombiesOutOfWalls` /
`pruneDeadZombies` passes, `arcTicksLeft`'s decrement site) is documented behaviour the note does
not describe and is left alone; the replay hash gate in CI covers it.

## N8 — the spawn-row floor is a map-install assertion now

`MinSpawnRows` existed and was read only by a test, so the invariant held for the arena and said
nothing about a variant installing a different map, where too few clear gate-reachable rows means
the horde arrives in single file or `spawnOneZombie` has nowhere to put a body.
`installHordeField` now raises `SimGuardError`. It runs once per map install on a pure function of
the mapSpec. Evidence: `test_horde: ok` and every other test (all of which install the arena).

## N9 — DISPUTED: the turn-spacing floor is a bounded wait, and the note's own arithmetic requires it

The finding is that `decide.nim:368` is a blocking `sleep` on the game loop where design.md:413-415
says "It is a floor, not a sleep on the critical path: the loop keeps stepping sim ticks while it
waits." I did not change the code, because the note contradicts itself and the code follows the half
that the tests and the budget depend on:

- The note's own arithmetic three lines later is `48 turns x 9.0 s spacing floor = 432 s`, and
  `tests/test_engine.nim:218-255` prices the episode that way (`432 + 100 + 60 + 20 = 612 <= 690`).
  That figure is only true if the spacing is **wall time per turn**.
- Turns are keyed to sim ticks (`turnTicks` 96, `server.nim:1911`), and every shipped variant sets
  `fastMode: true`, so the loop steps a whole 2304-tick wave in a few CPU seconds. If the loop kept
  stepping ticks through a 9 s wait, the wave would end after a handful of turns and the LLM would
  issue a fraction of the 24 turns per wave the design is built around. That is a behaviour change
  to the game, not a fix.
- The wait is bounded by construction — `sleep(min(turnSpacingMs, turnSpacingMs - since))`, so
  ≤ 9 000 ms once per turn — it is not inside any lock (the loop's `withLock appState.lock` blocks
  are closed before the decision section at `server.nim:1899`), the engine's own 690 s stop is
  re-checked at the top of every iteration, and the certification fixture sets `turnSpacingMs: 0`
  so no CI path pays it. Checklist item 5 ("every wait has an explicit bound") is satisfied.

The divergence is real but it is in the note's *prose*, which is why it is recorded in `AGENTS.md`'s
divergence table (`d1ea75d`) rather than fixed in code. If the operator wants the note's prose to
be literally true, that is a design change (pace the tick loop between turns instead of blocking
once per turn, which changes every timing number in §Engine) and should be decided, not smuggled
into a review round.

## N10 — `spawn_rate_per_s` was per-mille per second

`spawnRatePerMille` is per-mille of a zombie per *tick*, so `* TargetFps` handed every seat **288**
where the docs quote 0.29/s rising to 1.20/s. Wrong since the first commit because nothing asserted
it. Division restored; `test_observation` pins the unit (0 < rate ≤ 2.0) and the derivation.

## N11 — the `last_turn` block exists

The engine marks the per-cog and team counters once per turn, after every view for that turn is
built and while the sim is still on the turn's own tick, and the view reports the difference. Every
field is a non-negative delta (`zombiesSpawned` is per wave). `you.kills` stays the episode total.
The new test asserts turn 0 is all zeroes and that a credited kill/hit/shot appears as a delta
rather than a total; the key-list assertion was extended to include it (an addition, not a
loosening).

## N12 — a bare order object parses

`cogEntries` read only `payload{"cogs"}`, so `{"intent":"hold","target":[500,240]}` — the obvious
reply for a seat that commands exactly one cog, and a shape the note lists as tolerated — matched no
cog, raised, spent the retry and then played a fallback turn. It is now read as the single order it
is (assigned by position, exactly like a wrong-id entry), while a payload with only a `note` still
raises. The note's other named case is covered too: a target inside a wall is passed through for the
control layer to snap, an off-map target is clamped.

## N14 — the retry-once bound is asserted

`while open.len > 0 and attempt < 2` made checklist item 8's "retries once" a property of a loop
condition no test measured. `fake_bedrock.py` gains a `garbage` mode (prose with no JSON object), so
both attempts complete fast and the fake's request log counts them: the test asserts **exactly 8
requests** (four seats × two attempts), that the highest `attempt` in any recorded fallback is 2,
that every parse failure was recorded, and that every seat ends the turn actuated. Evidence:
`test_engine: ok` in both modes.

## N15 — the pressure strip is inside the top band, not over the plates

`top: calc(var(--topband, 0px) - 15 * var(--u))` measured fifteen units *up* from the band's bottom
edge, and `--topband` **is** relayout()'s measurement of `#scorebug.offsetHeight` — so the strip and
its `22 DEAD WALKING · LEADER 552PX` readout were drawn over the second row of plates and the TIME
LEFT caption, exactly as the reviewed run's screenshot shows. The strip is now the scorebug's own
last grid row (`grid-column: 1 / -1`, in the flow, no z-index, no absolute positioning), so
relayout() measures it into `--topband` and the band grows to hold it; the block dispatches one
synthetic `resize` when it appends the strip, because relayout() observes `#viewport` and would not
otherwise re-measure the band the strip just changed. `test_viewer`'s old assertion pinned the
defect (`top: calc(var(--topband, 0px) - 15 * var(--u))`) and now pins the fix plus its negation.
Evidence: the fixture's plate-overlap assertion at four canvas sizes, green in CI; `wasm-viewer`
green on the real replay.

## N16 — the closest-call caption is on the board

`#kaz-chalk` is a child of `#stage`, which spans both bands, and it was `top: 0; bottom: 0` with its
label at `top: calc(8 * var(--u))` — so the label landed inside the opaque scorebug band, under
`#chrome` (z-index 10 vs 6), and no `CLOSEST CALL — n PX` caption appeared anywhere in the reviewed
screenshot. It now spans exactly the board region (`top: var(--topband); bottom: var(--band)` — the
same two variables `#board` is sized from). It stays a child of `#stage` deliberately: `#board` is a
`<canvas>`, and a div appended to a canvas is fallback content that never renders. Evidence: the
fixture asserts the caption's box is inside `#board`'s at four sizes; visible in the fixture
screenshot artifact.

## N17 — the kill feed names the body that fell

The row printed `'cuts down Z-' + (e.teamKills || 0)`, so every kill named a zombie that never
existed and the number climbed by one per kill. The `kill` beat is derived from a kill-count delta
and carried no id. The sim now records which body each hero last killed (`heroLastKill`, set in
`creditZombieKill` beside the kill credit), the beat carries it as `zombie`, and the row reads
"KNIGHT-alpha cuts down Z-118 · 42 down". The field is not hashed and not recorded, and it is
appended at the **end** of `SimServer` because that struct rides the flatty replay keyframe
positionally. `test_combat` asserts the whole chain, and the native↔wasm hash gate is green.
Not shipped, and recorded as remaining: the design's `gate_px` on `kill`, and its `hit` event.

## N18 — the momentum graph's presentation, and the co-op verdict

Half of this finding was already done and the review missed it: `scanTeamLead` (`replays.nim:539`)
has always shipped the horde's two series rather than a per-team lives lead. What was **not**
retargeted is real: the series shipped under the team names `["red","blue"]`, so chrome_common's
two-entry renderer plotted them as a tug of war between teams that do not exist; the two values were
on different scales (a raw kill count against a percentage), so the difference the renderer plots
meant nothing; the caption still read LIVES LEAD; and the inherited verdict chip read "RED WINS"
whatever happened, because `sim.winner` is always Red here — including on a breach that lost the
wave. Now: both series are percentages (kills against the episode's own scoring ceiling), shipped
named `kills` and `pressure` (the names only pick the shading colours), the game block relabels the
caption `KILLS vs HORDE PRESSURE`, and KAZ_MODE no longer calls the inherited `setVerdict`.
`chrome_common.js` is untouched and still byte-identical (its md5 pin is green).

## N19 — the banner comment claimed removals it does not make

The perk/handicap badges are still there, in the classic non-KAZ_MODE branch a coworld-ctf replay
still renders. The **code** matches the note (design.md:1055-1057 lists only the CSS rules as
removed); the comment overstated. The banner now says what is removed and, separately, what is
deliberately kept and why. Comment only.

## N22 — the contradictory deadline comment is gone

`decide.nim` carried two blocks about the same conversion, one saying it FLOORS and the next saying
it CEILS. The code ceils (`(deadlineMs + 999) div 1000`: 4500 → 5 s, 2000 → 2 s, summing to exactly
`turnBudgetMs` 7000); the pre-fix block is deleted along with its stale "10 s turnBudgetMs cap".
Also corrected: `llm.nim`'s "next 4.5 seconds" (that is `attempt1Ms`; the cadence is 4.0 s),
"Paintball is a SIMULTANEOUS-decision game … both seats … 40 turns" (four seats, 48 turns),
`server.nim`'s PAINTBALL decision-turn header, and `sim.nim`'s "a paintball EPISODE is two games".
The remaining paintball references sit on the config-gated mechanics — that is N21.

## N23 — the integer-only grep

`control.nim` is added (it is clean). `sim.nim`, `sim_types.nim` and `sim_state.nim` are documented
in the test as deliberately out of scope with the reason for each: `sim_types` owns
`aimVector`/`bradsOfVector`, the float trig the render path reads and the sim never calls;
`sim_state`'s floats are `emitEvent` payloads bound for the tier-2 JSON stream, not the hash;
`sim.nim` carries the inherited render helpers. The rule the block enforces — no float on a hashed
path — is now stated rather than implied.

## N24 — the head-to-head compares per wave

An episode total can hide a wave `phalanx` lost. The test now prints both per-wave rows and asserts
`phalanx > stand` on each wave. Measured in CI: `per-wave kills: phalanx=@[48, 55] stand=@[43, 32]`,
so the assertion holds at the pinned seed with margin.

## N2 / N3 / N4 / N13 / N20 — code right, note stale (documentation only, `d1ea75d`)

I did not change code for these, and I did not edit the design note (it is the run's artifact, and
the fixer brief forbids it). Each already carried its reason in a code comment, but nothing
collected them, so `AGENTS.md` gains a "Where the code and the design note differ" table naming, for
each: what the note says, what the code does with a file:line, and the measurement or test that
decided it — the nav cell (12 px, because a 34 px cell leaves no node inside a ~26 px corridor and a
zombie stood in a wall for 2000 ticks), the intercept standoff (44 px, because walking onto the
leader crosses its 26 px kill radius and a measured episode ended `casualty`), `phalanx`'s
`fall_back` cell (chosen by `tools/tune_baselines.nim`, re-checked by CI every push),
`fallback.cause`'s sixth value (`throttled`, because reporting a 429 as `parse_error` made a hosted
log unreadable), and the removed `league_replayer.html` (the platform serves the static bundle;
`Dockerfile.replay-viewer` drops every reference consistently).

**This is the one commit that touches more than one finding.** It is documentation with no
behaviour, and splitting one table across five commits would have made it less readable, not more.

## N21 — NEEDS-DESIGN

`src/kaz/paint.nim` (286 lines) and the grenade / med-kit / shield / spray-can / barrier / heart /
hill machinery in `sim.nim` and `global.nim` are still in the tree, config-gated off
(`sim.nim:171 hordeLoadout`) and unreachable under every shipped variant — the horde step body calls
none of them and `checkHordeEnd` replaces the classic end checks. Deleting them is a large
mechanical excision across the inherited engine, touching the same files the replay hash chain and
the byte-identical chrome depend on, and it would be indistinguishable in the diff from a real
behaviour change. That is a decision for the operator, not a review-round fix. What I did instead:
`AGENTS.md` now says plainly that the removal is work still to do rather than implying it is done,
so the next reader does not "revive" a mechanic on the strength of the old wording.

## N25 — not fixed; the evidence for the judge

`server.nim:800` answers bitworld's `ReplayClientRoute` / `CoworldReplayClientRoute` with the
embedded broadcast page, and its own comment says why: local inspection and the certifier's HTTP
contract probe. Checklist item 3's wording is "No `/client/replay` pod path anywhere", and what the
item is about is a **pod-served viewer**: the manifest declares
`game.replay_viewer = {"bundle": "static-replay-viewer"}` and nothing else
(`tests/test_manifest.nim:60,68`), `coworld-release.yml:200-208` hard-fails certification unless the
log names the static bundle, and the route is a constant of the inherited framework rather than
manifest-declared viewer wiring. Removing it would change what the certifier probes for no gain to
the hosted path. I left it and am naming it rather than silently passing over it.

---

## NOTED (not fixed)

- `tools/build_manifest.py` opens with `os.chdir('/tmp/kaz')`, so the generator cannot be run from a
  checkout; the committed `coworld_manifest_template.json` is therefore hand-maintained (I edited
  the rules-page string in place for N1). Not a finding in this review.
- `client/chrome_common.js` reads `window.CTF_WIRE` (line ~72) as its wire-constant fallback, so in
  this fork `WIRE` is always `{}` and `SPEEDS`/`FPS` come from its literals. It is byte-identical to
  the starter by design and pinned by md5, so fixing it would break checklist item 14; the values
  agree anyway.
- The design's `hit {by, zombie, dmg, hpLeft}` broadcast event and `gate_px` on `kill` are still not
  emitted (N17 fixed only the id the feed prints).
