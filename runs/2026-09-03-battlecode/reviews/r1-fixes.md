# r1 fixes — battlecode

Repo: `Metta-AI/cogame-battlecode`. Base: `3eb7915` (the reviewed sha).
**Head: `81ffb0e41d51b4622e9377d0dcc02a8946cbd08c`**
**CI: <https://github.com/Metta-AI/cogame-battlecode/actions/runs/33824171362> — conclusion `success`**
(run id **33824171362**, `ci.yml`, push to `main`, head `81ffb0e`; jobs `test` ✓, `parity-oracle` ✓,
`docker-smoke` ✓, `wasm-viewer` ✓ — all four green, no `continue-on-error`, no `SEAT-COUNT FAIL`
anywhere in the log).

Seventeen findings, seventeen commits, one per finding, in this order (N2 first: B1's new runtime
proof needs a scrub gate that actually seeks).

| finding | commit | what changed | checklist item |
|---|---|---|---|
| **B1** `#endcard` shown with a class that has no rule | `84b1792` | `.show` → `.on` at both toggle sites; test_viewer pins the rule + both sites; the smoke records the endcard's **computed display** and `ci.yml` fails unless it is shown after the 100 % seek | **14(c)** |
| N1 same mismatch on `#mmwarn` | `764069d` | `mm.classList.add('on')`; test_viewer pins it | 14 (viewer honesty) |
| N2 scrub gate clicked the zoom slider | `524d7e0` | selectors resolved in priority order, not as one comma list; the matched selector is reported and `ci.yml` requires `#scrub` | 13 (viewer executes) |
| N3 budget timeout recorded twice, cause overwritten | `991b965` | the timeout branch names the cause, logs it and clears `open`; test drives `decide()` at a closed port and asserts one event per seat | 8 |
| N4 `plan.abandon_after` was dead data | `8a98179` | `Deriver.gameRecord` reads it when a game has no header; frames planned from the plan; determinism test now builds the document the recorder writes | 2 |
| N5 chain compared once per game, three stats missing | `9ff4a07` | all seven per-team stats folded; `games[].hash_chain_rounds` records the chain after every round; the deriver compares each round (**GV02**) | 2 |
| N6 knob-teeth seed loop was inert | `785a33e` | the seed perturbs `spec.randomSeed`; 3 seeds × 3 maps = 9 distinct games; table re-measured | 7 |
| N7 `never` == `retaliate_only` | `badbe32` | `never` no longer opens hostilities after the flip (**GV03**); `docs/RULES.md` spells out all five values; combat test asserts they differ | 7 / knob teeth |
| N8 fixture copied the page's CSS and skipped the harness | `4725555` | the fixture **links** the page's own `<style>` block (extracted by `ci.yml`), uses the page's DOM at 3 widths, measures every element, and is driven by `viewer_smoke.mjs --strict-text-bounds` | **15** |
| N9 round-loop order vs the note | `212db9a` | **by design, documented** — the code is the *engine's* order and the parity gate requires it; `docs/RULES.md` now cites `InternalRobot.java:1176-1191` and `GameWorld.java:1178-1180` | 2 / correctness |
| N10 prompt payload not in the replay | `3d98f98` | `seats[].prompt`, `seats[].fallback_detail`, document-level `prompt_preamble`, all parsed back; tests + `docs/REPLAY.md` | 9 |
| N11 `NOTICE` missing | `1d2b21c` | `NOTICE` with both upstreams at their **pinned commits** and a per-artifact provenance table; test_manifest asserts it | 12 / licensing |
| N12 `#btn-skip` not relabelled | `a234016` | **by design, documented** — `#btn-fwd` is the button that does +25; relabelling the auto-skip toggle would misname it. Comment + test pin both labels and both key bindings | 14 |
| N13 four vacuous test claims (a–d) | `2ee91f9` | the coworld CLI now validates the template in CI (**and found two real manifest defects, fixed**); every end reason asserted and `seenReasons` used; the Dockerfile scan de-vacuumed; the endcard-bound assertion reads the endcard's own rule | 1, 2, **10** |
| N14 reply cap in runes, not bytes | `a8684c0` | `truncateBytes` (byte cap, rune boundary) used by `parseReply`; tests | 9 |
| N15 dead spoiler guard + ungated beat markers | `93bbf33` | the block gates its own markers on the starter's rule at every frame and both toggles; dead guard removed | 14(d) |
| N16 `scaffold` is examplefuncsplayer verbatim | `81ffb0e` | **by design, required by the parity gate** — the note describes a bot that does not exist upstream; `docs/PARITY.md` says so with the upstream file cited | 7 / parity |

Nothing was weakened to make anything pass: every test file change in these commits is an added or
strengthened assertion (five of them fail on the pre-fix code — see the per-finding notes), plus the
two mechanical de-vacuumings in N13c/N13d, which make previously-always-true checks able to fail.

---

## B1 — `#endcard` was filled in and never displayed

`client/replay_broadcast.html:1859` is `#endcard.on { display: flex; … }`; there is no
`#endcard.show` rule and no bare `.show` rule in the page, so `renderEndcard`'s
`classList.add('show')` left the score screen at `display: none` for the whole replay, and
`dismissEndcard` removed the same dead class. Both sites now use `.on`.

Proof, at three levels:

* `tests/test_viewer.nim` pins the CSS rule, both toggle sites, the **absence** of any
  `$('endcard').classList.{add,remove}('show')`, and the absence of a `#endcard.show {` rule that
  could justify one. (The reviewer's point stands: the old shard only grepped for the string
  `dismissEndcard`, which the broken page also contained.)
* `tools/ci/viewer_smoke.mjs` now reports the endcard's **computed display** and text at each scrub
  readout.
* `.github/workflows/ci.yml`'s `wasm-viewer` job fails the build unless, after the 100 % seek, the
  card is displayed and carries a clan line.

Evidence from the green run (job `wasm-viewer`, step *Load the bundle in a real browser*):

```
scrub readouts (#scrub): 0%="0:07 GAME 1 OF 1 — TOOMUCHCHEESE"  50%="0:08 …"  100%="FINAL MATCH OVER"
scrub selector: #scrub
endcard after the 100% seek: shown=true text=CLAN ASH — CLAN ASH
```

`shown=true` is the assertion that was `false` before this commit — and this is the first CI run in
this repo's history that ever reached the end of a replay (see N2).

## N2 — the scrub gate clicked the zoom slider

`SCRUB_SELECTOR = '#scrub, #seek, input[type="range"]'` was handed to Playwright as one list, which
resolves in **document order**, so `.first()` returned `#viewpanel`'s zoom slider
(`client/replay_broadcast.html:2673`) rather than `#scrub` (`:2725`). The three differing clocks the
gate requires came from free-running playback; no seek was ever exercised. The selectors are now
tried one at a time in priority order, the matched one is recorded as `scrub_selector` in
`viewer-smoke.json`, and `ci.yml` fails when it is not `#scrub`. Evidence: `scrub selector: #scrub`
and a 100 % readout of `FINAL MATCH OVER` (it read `0:05`, mid-match, in the reviewed run's
artifact).

## N3 — a spent budget was also recorded as a parse failure

`src/battlecode/decide.nim:164-169` left the timed-out seats in `open`, so the tail loop at `:220`
recorded a **second** `doctrine_fallback` for the same seat and overwrote `"timeout"` with
`"parse"`. The branch now names the cause, echoes the `falling back` line phase 60 greps for, and
`open.setLen(0)` before the `break`. `tests/test_sheet.nim` drives `decide()` against a closed local
port (no network) with a 1 ms phase budget and asserts **exactly one** `doctrine_fallback` per seat
and that the surviving cause equals the event's; on the pre-fix code that check reports `got 2 want 1`
for both seats.

## N4 — `abandon_after` was written, parsed and read by nobody

`newDeriver` planned frames from `doc.games[].rounds`, and the abandoned game has no `GameHeader` at
all (`playMatch` breaks before `outcomes.add`, so `server.nim` never writes one). A real `deadline`
replay therefore dropped its last game — in a one-game match, the whole replay. `Deriver.gameRecord`
now answers *how many rounds did game i play, and on what chain* from the header when there is one
and from `plan.abandon_after` when there is not; `newDeriver`/`restart` plan from the plan's games,
and `advance` looks the header up by index instead of indexing `doc.games[wantGame]` positionally
(which is only correct while every game has a header). `tests/test_determinism.nim`'s `deadline`
block now builds the document **the recorder actually writes** — no header, `abandon_after = 200` —
and asserts 200 frames, stopping at round 200, no mismatch. On the old deriver that block plans 0
frames and dereferences a nil world.

The test does not drive the abort from the real clock: a game plays in ~10 ms here and the smallest
budget `playGame` accepts is a whole second, so a wall-clock-driven abort is mode-dependent (it fires
in debug and not in release). Recorded as a limitation rather than papered over.

## N5 — the chain was compared once per game, and covered four stats of seven

Two halves, one commit, **GameVersion GV02** (an existing GV01 recording cannot be re-derived under
the new chain, and the format gained a load-bearing field):

* `processEndOfRound` now folds all seven per-team stats the engine reports — the missing three are
  dirt and both trap counts, exactly the ones `GameWorld.processEndOfRound` passes to
  `addTeamInfo` (`GameWorld.java:1016`). A re-derivation that diverged only in dirt or in traps
  standing used to reproduce the chain exactly.
* Each game header now carries `hash_chain_rounds` — the chain after **every** round, 16 hex digits
  each, written straight from the recorder's own loop — and `advance` compares one round at a time,
  falling back to the final-chain check for a recording without the list (and still checking the
  final value on its own, so a document whose two records disagree is caught). `bc_mismatch_round`
  now names the **first** divergent round, which is what the note and `docs/REPLAY.md` claim.

`tests/test_replay.nim` corrupts round 40's entry and asserts `mismatchRound == 40`; the old code
could only ever report the game's last round.

## N6 — the seed loop played the same game twice

`seed` was never used: `playGame` has no seed parameter and the world RNG comes from the map's own
seed field, so each map played the byte-identical game once per seed and every total was doubled.
The loop now perturbs `spec.randomSeed`, and `Seeds = [1, 2, 3]` — the note's "three seeds each",
9 distinct games per paired set. Every gate still passes on real samples (measured, in the shard's
header table: rats 58→257, kings 0→7, cheese 2555→7740, cat traps 0→74, rat traps 0→165, dirt 0→143,
cat damage 0→12520, cats fed 0→40, chassis wins 4/5 of 9). The `chassis` row's declared deviation is
restated as "≥ 4 of 9" with its reason (awu dominates every economic measure; scaffold still steals
round-limit points games).

## N7 — two of the five `backstab_policy` values were one behaviour

`kit.hostilitiesOpen` returned `true` for every doctrine once the world flipped, so `never` and
`retaliate_only` were indistinguishable while `sheet.plainWords` printed two different stories.
`never` now means never: the clan never takes an enemy rat as a target, flipped or not, and lays no
rat traps (`traps.nim` already gates those on the same predicate — **which the note's knob table
explicitly describes**: "with hostilities closed, enemy rats are simply not candidates for
bite/ratnap/throw/rat-trap", so the reviewer's sub-observation that the rat-trap gate is "not in the
note" is *refuted*). Rules change ⇒ **GV03**. `docs/RULES.md` now defines all five values, including
`when_ahead`'s round-200 floor, which the reviewer noted was undocumented.
`tests/test_rules_combat.nim` asserts the two policies agree before the flip and differ after it.

## N8 — the fixture tested its own CSS, and not through the harness

The fixture duplicated the game block's rules **and** added three declarations the page does not
ship (`max-width`+`overflow:hidden` on `.plate`, ellipsis on `.plate-sub`, `overflow:hidden` on
`#doctrines`) — and its verdict is "does this box escape `#frame`", which a box with
`overflow:hidden` cannot. Now:

* `page_styles.css` **is** `client/replay_broadcast.html`'s `<style>` block, extracted verbatim by
  the `wasm-viewer` job (`page_styles.css: 131558 bytes from 1 <style> block(s)` in the green run);
  the fixture declares no rule for any element it measures and reports
  `page_styles.css did not load` rather than silently measuring an unstyled page;
* the markup is the page's own DOM (`#viewport > #stage > #chrome > #scorebug > .plates > .plate`,
  `#coopchip`, `#econ`, `#doctrines`) with the band variables `relayout()` computes;
* three widths in one load (360 / 720 / 1280) via iframes, so each one's media queries see its own
  width;
* the verdict walks **every** element under `#chrome` for frame containment and every filled readout
  for hidden content;
* `ci.yml` serves it and runs `node tools/ci/viewer_smoke.mjs --url … --strict-text-bounds`, so it
  reports a `canvas_text` line like the bundle does
  (`canvas text: 0 drawn, 0 never inside the canvas … (--strict-text-bounds)`) and its
  `viewer-smoke.json` is uploaded.

I verified locally, in headless chromium, that the fixture goes red when the page's CSS regresses
(`#doctrines escapes the frame …`) and when `page_styles.css` is absent. **This also settles one of
the review's "could not determine" items**: with the page's real rules, `.plate-sub` (real name +
48-rune motto) does not overflow the scorebug at 640–1280 px — it wraps — and nothing under `#chrome`
clips its own text at any of the three widths.

## N9 — round-loop order: documented, by design

No code change, and the finding is real only against the note's prose. The code's order is the
**engine's** order, and the parity oracle's Tier A (rounds 1–50, bit-exact, blocking) requires
exactly it. Read at tag `engine.1.2.5`:

* king cheese consumption and starvation: `InternalRobot.processEndOfTurn`
  (`InternalRobot.java:1176-1189`) — not `processBeginningOfTurn`, which is the note's step 4;
* the cat state machine: the same `processEndOfTurn` (`InternalRobot.java:1191`) — not the body's
  controller, which is the note's step 5;
* zero rat kings / all cats dead: `GameWorld.destroyRobot` → `checkWin` (`GameWorld.java:1178-1180`);
  `processEndOfRound` runs only the round-limit ladder (`GameWorld.java:1021`) — the note's step 8
  puts both at end of round.

`docs/RULES.md` already documented the code's order; it now also names the note's paragraph and
states what the engine does at each point, in a table, so a reader of either document finds the
divergence. Green evidence that the order is the right one: `TIER B DefaultSmall/arrows/closeup/
toomuchcheese/cheesefarm: bit-exact through round 200` in run 33824171362.

## N10 — the observation is now in the replay

`seats[].prompt` carries the payload the server composed for that seat, verbatim (null for a seat
that never called); `prompt_preamble` carries the system half once, because it is identical for both
seats and is where this port keeps the note's `rules_digest` and `sheet_schema` content;
`seats[].fallback_detail` carries the provider's own last line, already cut to
`MaxFallbackDetailRunes` (200) with newlines collapsed. All three round-trip through `parseReplay`.
`tests/test_replay.nim` asserts the payload, the preamble, the `null` for a scripted seat, and that a
400-rune provider message lands at exactly 200 runes and still parses as strict UTF-8.

## N11 — `NOTICE`

Written, with the pinned commits the note asks for: `battlecode/battlecode26` tag `engine.1.2.5` =
`991c91af9c35db497f3508393cb6a6f5610725c0`, `awu7/battlecode-2026` branch `final` =
`a70328eacaab18622cdac838f5e4e981c2a1f0cd` (both read from the GitHub API). It maps every derived
artifact in this tree to what it derives from, credits the starter the viewer chrome is forked from
and the embedded pixel font, and states that no upstream Java source runs in any image.
`tests/test_manifest.nim` asserts the file exists and names both upstreams, both commits, the licence
and the no-Java claim, so the README link cannot go stale again.

## N12 — the `+25` label: documented, by design

The note names `#btn-skip`; in this lineage that id is the auto-skip-quiet-stretches **toggle**
(`'f'` → `skipLulls`, `src/battlecode/broadcast.nim:54`) and `#btn-fwd` is the forward step (`'.'` →
+25 rounds, `broadcast.nim:51` resolved in `replay-viewer/bc_replay.nim:113`). The label is on the
button that does the thing; putting "+25 rounds" on the toggle would name it after a behaviour it
does not have. The page's comment now says that in full, and `tests/test_viewer.nim` pins both labels
and both command bindings so a later edit cannot swap them.

## N13 — four vacuous claims, and two real manifest defects

**(a)** The note's shard 12 asks for the installed `coworld` CLI's own
`_load_template_manifest`/`validate_upload_manifest` over the template. That call now exists as a
`test`-job step (a Nim shard cannot import a Python package), pinned to the same CLI version
`coworld-release.yml` uses. **The first time it ran it rejected the template**, for two reasons, both
fixed in `coworld_manifest_template.json`:

* `game.owner` was missing and is **required** by `CoworldGameManifest`;
* `resources.limits.memory` is forbidden — `CoworldResourceLimits` accepts `cpu` only — on the game
  runnable and both player runnables. The declared memory moved to `resources.requests`, where the
  schema defines it (the numbers are unchanged: 4Gi game, 512Mi players).

This is exactly the phase-40 failure `playbooks/make-coworld.md`'s own known-issue table warns about
("Certify locally fails `manifest_invalid` on a template repo CI passed … `game.owner` required").
Green evidence: `coworld accepted the template: battlecode with 1 variant(s)`.
`tests/test_manifest.nim` also asserts the step is still wired and re-checks both defects in Nim.

**(b)** "record → re-derive for every end reason" asserted no end reason at all, `cats_cleared` had
no record→re-derive, and `var seenReasons` was declared and never used. `deriveAndCompare` now
returns the outcomes and takes an optional map; `round_limit` and `kings_destroyed` assert their
per-game `end_reason`; `cats_cleared` plays a **real** match (two cat-hunting clans that never turn
on each other clear `cheesefarm`'s cats near round 420), records it and re-derives it; the `deadline`
block registers `abandoned` (the one reason that never reaches `results.games[]`); and a final block
fails if any `EndReason` is missing from `seenReasons`.

**(c)** The JVM check was `banned notin dockerfile or "no jdk" in dockerfile`, and `Dockerfile:7`
says "NO JDK, NO JRE, NO JAVA, NO NODE" — the right-hand disjunct was true for every word, so the
check passed vacuously. It now scans the instructions with comments stripped (and asserts there are
instructions to scan). The Dockerfile is in fact clean.

**(d)** "the endcard stops at the transport band" matched `bottom: calc(var(--band` in `#econ` and
`#doctrines`. It now reads the `#endcard` rule itself and asserts its own `bottom: var(--band, 0px)`,
`top: var(--topband, 0px)` and `display: none`.

*Note on this commit's message:* backticks in the message I passed were interpolated by the shell, so
a few quoted fragments are missing from the commit text on GitHub. The diff is unaffected; the full
reasoning is above.

## N14 — the whole-reply cap

`parseReply` tested bytes and then cut runes, so a 16 KB cap admitted up to 64 KB of astral-plane
text. `sim_types.truncateBytes` cuts to at most `limit` **bytes**, still on a rune boundary.
`tests/test_sheet.nim` asserts a 40 KB astral sample lands inside the cap and stays valid UTF-8, that
a short reply is untouched, that the object at the front of an over-long reply is still parsed, and
that a reply whose *object* runs past the cap no longer parses — which is what the cap means (that
seat retries). The last check fails on the old code.

## N15 — spoilers

The beat buttons are appended straight to `#scrub` (they cannot go through
`markBeat`/`renderBeatMarkers`, which build divs and whose name this block may not reuse), so
`chrome_common`'s `applySpoilers`, which walks its own private `markerEls`, never saw them: with
spoilers off, a future BACKSTAB marker was on the scrubber from frame 0. The block now keeps its own
list and applies the starter's rule (hide a marker ahead of the playhead) on every frame, when the
markers are built, and on both spoiler toggles. `renderFeed`'s second guard was unreachable — the
line above already returns for a future beat — and is gone, with the reason written where it was.

## N16 — `scaffold`: by design, required by the parity gate

No code change, and the note is the thing that is wrong. I read
`example-bots/src/main/examplefuncsplayer/RobotPlayer.java` at tag `engine.1.2.5` in full: its entire
turn is `if (rc.canMoveForward()) rc.moveForward(); else { int d = rng.nextInt(8); if (rc.canTurn())
rc.turn(directions[d]); }`. There is no biting and no cheese pickup, so the note's §Scripted
baselines describes a bot that does not exist upstream. Tier A diffs this chassis against **that**
Java bot bit-exactly for rounds 1–50 on five maps, so a bite or a pickup here would diverge on the
first round a rat stands next to something. `docs/PARITY.md` now states that, naming the note's
paragraph and the upstream file, beside the snippet it already carried.

---

## Still open / NOTED (not fixed)

* **The review's third "could not determine" is answered** (`.plate-sub` does not overflow at
  ≥ 640 px — see N8). The second is now partly answered: the endcard *is* raised and displayed after
  a seek to the end in CI, on every run; whether it **re-arms** after scrubbing back from `FINAL` is
  still a runtime property no gate covers (the smoke seeks forward only).
* **The `deadline` abort is not exercised end to end by a test** (N4): a game plays in milliseconds
  and `playGame`'s smallest budget is one second, so a real wall-clock abort is mode-dependent. The
  deriver half is tested against the document the recorder writes; the recorder half is read, not
  run.
* **`parity-oracle`'s 33-second job time** (the reviewer's first "could not determine") is unchanged
  and untouched by these fixes; the same five maps produce the same per-map winners in the new run.
* **`game.runnable.resources.requests.memory = 4Gi`** is now in the field the schema defines, but the
  hosted baseline in the CLI's own docs is 1 CPU / 512Mi for a game container. If the backend clamps
  or rejects requests above a role maximum, phase 40 will say so loudly; I kept the builder's
  declared number rather than inventing a smaller one.
* **`ReplayFormatVersion` is still 1** although `games[].hash_chain_rounds`, `seats[].prompt`,
  `seats[].fallback_detail` and `prompt_preamble` were added. All four are additive and
  `GameVersion` (GV01 → GV03) already refuses an older recording, so nothing can be misread; bumping
  the format version as well would be the tidier record.
