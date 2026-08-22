# r1 fixes — lighthouse

Head: `eeb1004f3c8adbdde1ce562b1bec7ca3d3495ebb` (`Metta-AI/cogame-lighthouse` `main`)
CI: [ci.yml run 32602216061](https://github.com/Metta-AI/cogame-lighthouse/actions/runs/32602216061)
— **conclusion: success** on that exact sha (`test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓;
`SEAT-COUNT FAIL` appears 0 times in the log, `smoke OK: seats=4 results=252B replay=4280B
reason=timeup`).

Reviewed sha was `a16bebc`; `main` had already advanced to `1db815d` (F14), which is the base
these fifteen commits sit on. Every commit is one finding; nothing else was touched.

The whole suite was run locally before each push with Nim 2.2.4 (`~/.nimby/nim/bin`, `nim.cfg`
rebuilt exactly as `ci.yml` does), in **both** debug and `-d:release`: 9 + 4 + 26 `[OK]`s, zero
failures. No test was disabled, skipped, weakened or deleted. Three tests were **added**
(F3, F10, F17), three existing ones gained assertions (F1, F7, F15), and the legality drive
gained a corrected predicate and a wider seed list (F2).

| finding | disposition | commit | files |
|---|---|---|---|
| F1 glyph masks water under a key | fixed | `58e0314` | `src/lighthouse/sim.nim:444-462`, `tests/test_sim.nim:555-562`, note §Per-seat observation, manifest `rules.md` |
| F2 vacuous legality assertion | fixed | `f5c5f90` | `tests/test_bot.nim:10-16,74-84,98` |
| F3 stale 17/11/4 replay fallbacks | fixed | `654e0b0` | `src/lighthouse/server.nim:524-536`, `replay-viewer/lighthouse_replay.nim:28-38`, `tests/test_replay.nim:120-133` |
| F4 note's viewer-smoke checks absent from CI | fixed | `3503bfc` | `.github/workflows/ci.yml:224-272` |
| F5 lantern exception (c) window | fixed | `34bf871` | `src/lighthouse/llm.nim:323-352` |
| F6 undocumented `H` alias | fixed (docs) | `9ed9bd7` | note §Reply schema, manifest `rules.md` |
| F7 newlines replaced, not collapsed | fixed | `8045db5` | `src/lighthouse/llm.nim:171-185,682-684`, `tests/test_bot.nim:241-249` |
| F8 dead-end reason overstated | fixed (docs) | `d3cc14a` | manifest `rules.md` step 5, `README.md:98`, `src/lighthouse/sim.nim:315-321` |
| F9 fallback ordering / top-up separation | fixed | `7ebff3d` | `src/lighthouse/sim.nim:322-364`, `client/fixtures/gen_fixture.js:29`, `client/fixtures/sample_replay.json` |
| F10 `scripted` array overwritten wholesale | fixed | `2c5bba7` | `src/lighthouse/sim.nim:539-547,650-651`, `tests/test_sim.nim:272-289` |
| F11 `ellipsize` not rune-safe | fixed | `17aec90` | `client/renderer.js:92-107`, note §Viewer |
| F12 chrome.css delta understated | fixed (docs) | `8e29974` | note §Packaging |
| F13 `/client/replay` route exists | **no change — refuted for checklist item 3** | — | `src/lighthouse/server.nim:515`, `coworld_manifest_template.json:14-16`, `.github/workflows/coworld-release.yml:186-196` |
| F14 reviewed sha is not head | **no change — repository state, resolved** | — | — |
| F15 drown test misses the escape leg | fixed | `efab54c` | `tests/test_sim.nim:232-270` |
| F16 starts seed-independent at 11 × 9 | **accepted — documented, no code change** | `6aec2b7` | note §The game step 4 |
| F17 `evTick.notes` repeats notes | fixed | `eeb1004` | `src/lighthouse/sim.nim:527-537,649-650`, `tests/test_sim.nim:435-458` |

**14 fixed** (11 with a code, test or CI change; 3 documentation-only: F6, F8, F12),
**1 accepted and documented** (F16 — a docs commit, no code change), **1 refuted** (F13 — no
commit), **1 repository-state note** (F14 — no commit). 17 findings, 15 commits.

The design note changed under F1, F6, F11, F12 and F16;
`runs/2026-08-22-lighthouse/design.md` has been overwritten with the new content and is
byte-identical to the repo's `docs/plans/2026-08-22-lighthouse-design.md` at the head sha
(not committed in coworld-builder — that is the coordinator's).

---

## F1 — `glyphAt` masked water under a key glyph

**Was:** `glyphAt` resolved runner → exit → **key** → wall → water → floor, so an uncollected key
on a flooded tile rendered `K`. `wallhug`'s only legality test is `passable`
(`llm.nim:354-357`, `cell notin {'#', '~'}`), so the runner read the tile as open and ordered a
move into open water.

**Is:** runner → exit → wall → **water** → key → floor. A tile a runner may not enter can no
longer render as anything but `~`, in the keeper's map and in the 3 × 3 window alike.

**Evidence.** A probe driving `lantern` + three `wallhug` to the natural end over 16 seeds
reported 5 illegal proposals before (all on seed 21, the reviewer's case: `tick 25..29`,
`runner 2 at (1,4) -> (1,5) glyph='K' wall=false flooded=true`) and **0** after. The four
fixture seeds are bit-identical either way (27/25/35/37 ticks, scores 26.00/38.88/37.64/37.40,
talk 51.85/52.00/51.43/51.35 %), so §Tuning revision's measured numbers still hold. A new
assertion in `tests/test_sim.nim` "views" floods a key tile and checks `glyphAt`,
`keeperView()` and `runnerWindow()` all show `~`.

**Checklist:** item 7 — "asserts every order/action is inside its legal bounds"; this is the
half of it that lived in the baseline rather than the test.

## F2 — the load-bearing legality assertion was vacuous

**Was:** `check not (isWall(target) and isFlooded(target))`. Only a tile that is *both* wall and
water fires it — which `passable` already refuses — so it never fired at all. A dry wall, an
off-grid target (`isWall` true, `isFlooded` false) and open water all passed.

**Is:** two separate checks, `not isWall(target)` and `not isFlooded(target)`, and the legality
episode is driven over a wider seed list (`LegalitySeeds = [1, 7, 42, 1234, 3, 5, 11, 13, 21,
55]`) so the assertion has something to catch. The four tuning fixtures `[1, 7, 42, 1234]` are
untouched: the talk-budget, competence and instruction-following tests still run on exactly
those, with exactly the thresholds the note names.

**Evidence.** With F1 reverted in a scratch copy, the corrected assertion fails five times on
seed 21 (`Check failed: not result.sim.isFlooded(target[0], target[1])` … `was true`); with F1
in place all ten seeds pass. This is the pairing the review called load-bearing, and it now
holds in both directions.

**Checklist:** item 7, and item 1's "no test loosened" — this is a tightening, and the diff on
`tests/` is additions plus that one predicate.

## F3 — replay-config fallbacks carried the pre-retune board

**Was:** `configFromReplay` (`server.nim`) and `lhLoadReplay` (the wasm entry point) both called
`defaultGameConfig()` and then overwrote it with `getInt(17)` / `getInt(11)` / `getInt(4)` —
a second, stale copy of the board constants — whenever a recorded config omitted a key.

**Is:** every fallback is the field `defaultGameConfig()` already set
(`recorded{"width"}.getInt(result.width)`), so the shipped board has one source of truth and
cannot go stale on the next retune.

**Evidence.** New test in `tests/test_replay.nim` strips `width`, `height`, `tideDelay`,
`tidePeriod` and `keyCount` out of a recorded payload and asserts the wasm entry point still
returns 1 and re-derives a final frame identical to the live sim's `boardStateJson`. With 17/11
put back, it fails: `lhLoadReplay(...) was 0` (`checkRecordedBoard` rejects the 11 × 9 grid
against a 17 × 11 re-derivation).

**Checklist:** item 2 (replay re-derivation) — latent before, guarded now.

## F4 — the note's repo-side viewer smoke checks were not in CI

**Was:** the `wasm-viewer` job asserted the hook's mode, ran it, and checked for a non-empty
`index.html` and one non-empty `.wasm`. `grep -rn 'node --check' .` returned nothing.

**Is:** two additions to that job —

- *Check the viewer scripts parse and keep the coworld bridge* (before the build):
  `node --check client/renderer.js`, `node --check replay-viewer/static_replay.js`, and
  `grep -qF` for `data-replay`, `coworld-replay` and `tell("ready")`;
- a reference sweep inside *Assert the bundle is complete*: every `src=`/`href=` in the built
  `index.html` is resolved against the bundle directory, and any that is missing or empty fails
  the job.

**Evidence.** In the green run, the job prints `viewer scripts OK` and
`referenced and present: ./chrome.css | ./renderer.js | ./lighthouse_replay.js |
./static_replay.js`. Locally, deleting one of those from a mock bundle makes the sweep exit
non-zero.

**Checklist:** item 3 (static viewer) — the guard the note promised now exists.

## F5 — `lantern` exception (c) measured a fixed window, not "since the last message"

**Was:** `tideRowsAt(clock) != tideRowsAt(clock - 2)`. **Is:** compared against
`clockAtLastMessage(sim)`, the clock recorded on the `evTick` of the tick the last transmission
went out on (the tick number alone will not do — the clock advances by 1 or 2). Falls back to
"true" before the keeper has spoken, as before.

**Evidence.** Behaviour-neutral on everything measured: over 16 seeds the ticks, keys, escapes,
drownings, scores and talk rates are identical to before the change, because the rhythm, the
never-twice-in-a-row rule and repeat-suppression still bound when an exception can act. The
note's 51–52 % stays true.

**Checklist:** none directly; it is a code-vs-note divergence in §Decisions.

## F6 — `"H"` accepted but undocumented

No behaviour change, deliberately: champion #2 `lighthouse-pilot` is specified with the grammar
`"<Alias>:<N|S|E|W|H>"` (`tools/ci/policies.json:13`) and `orderedDirection` routes a keeper's
ordered direction through the same `parseMoveToken`, so removing `H` would break the shipped
pilot prompt for `wallhug` runners too. §Reply schema's alias list and the manifest's `rules.md`
now carry `H` with that reason.

**Checklist:** item 10 (manifest docs accuracy), advisory.

## F7 — newline handling replaced instead of collapsing

**Was:** `.replace("\n", " ").replace("\r", " ")`, so `"a\r\n\nb"` became `"a   b"`.
**Is:** `collapseNewlines`, one run of `\n`/`\r` → one space; spacing the model typed is left
alone. **Evidence:** the existing `"one\ntwo"` → `"one two"` assertion still passes and
`"a\r\n\nb\n\nc"` → `"a b c"` is asserted alongside it. Cosmetic only — the rune cap and UTF-8
validity were never affected.

## F8 — the dead-end filter's stated reason does not hold at 11 × 9

Documentation only; the note's §The game step 5 had already been amended and needed nothing.
The three places that repeat the rule had not caught up and still credited dead-endness with
keeping the keeper load-bearing: the manifest's `rules.md` step 5 (now states the floor-tile
fallback and that it is the normal case at 11 × 9), `README.md`'s Deviations row, and the
comment above `rankByExitDistance`. The difficulty is attributed to the distance filter the
fallback shares.

## F9 — fallback key path skipped board order and could top up under the bar

**Was:** the fallback returned `picked` in exit-distance order (no `(y, x)` sort, unlike the main
path whose comment says the sort exists "so the viewer and the keeper's map agree"), and once the
≥ 6-apart greedy pass ran out it appended any remaining tile with no separation check — while
`tests/test_sim.nim:130-133` asserts pairwise BFS distance ≥ 6 unconditionally.

**Is:** the greedy pass walks the required separation down one tile at a time (6, 5, 4, …) rather
than abandoning it, so a board too cramped for a 6-apart triple still gets the widest spread it
can carry; the result is then sorted into `(y, x)` board order like the main path.

**Evidence.** Over 16 seeds the key *sets* are unchanged (the ≥ 6 pass already succeeded on all
of them) and every episode plays out identically — ticks, keys, escapes, scores, talk rates. Only
the recorded order changes, so `client/fixtures/gen_fixture.js`'s hand-written seed-11 `KEYS`
went from `[[3,3],[1,3],[5,5]]` to `[[1,3],[3,3],[5,5]]` and `sample_replay.json` was regenerated
by the committed script (same episode: 61 events, keys 3/3, escaped 2, drowned 1, score 26.0 —
matching a real seed-11 run).

**Checklist:** item 7's "legal bounds" applied to placement, and item 2 (the replay's `config.keys`
is now in the same order the viewer and keeper see).

## F10 — `applyTick` cleared resolved seats' `scripted` flags

**Was:** `sim.scripted = scripted`, wholesale, every tick. The server fills that array only for
`pendingSeats()`, so from the tick after a runner escaped or drowned its slot read `false` in
`sim.scripted`, in every later `evTick.scripted` and in the final `boardStateJson`.

**Is:** only the seats that decided this tick write their flag (the keeper always, a runner while
it `wasActive`), and the tick record carries the carried-over value. Replay is unaffected by
construction — `replayMatch` feeds the recorded flags back and a resolved seat's is ignored the
same way — which the existing frame-by-frame re-derivation test confirms.

**Evidence.** New test drives a runner out and asserts `sim.scripted[1]`,
`events[^1].scripted[1]` and `boardStateJson()["seats"][1]["scripted"]` all survive the ticks it
no longer plays; restoring the wholesale assignment fails all three.

**Checklist:** item 8 — "the fallback is recorded so phase 60 can count it".

## F11 — `ellipsize` was not rune-safe

**Was:** `cut.slice(0, -1)` — UTF-16 code units, so a trailing astral rune could be cut between
its surrogates. **Is:** pops code points off `Array.from(text)`.

**Evidence.** With a harness that measures by UTF-16 unit, on `"abc" + 🌊🌊🌊` at a width that
lands mid-pair, the old code returns `"abc🌊\ud83c…"` (lone high surrogate) and the new one
`"abc🌊…"`. Canvas rendering only — nothing that reaches the replay bytes goes through it. §Viewer's
"copied unchanged" list no longer claims `ellipsize` is verbatim babel and names the one change.

**Checklist:** item 11 is about the scorebug rules and is unaffected; item 9 (replay strings) was
never in scope here. This closes a note-vs-code contradiction.

## F12 — the chrome.css claim understated the delta

Documentation only. §Packaging now names all four additions (4-column `#scorebug`, the
`.plate-name` rule, bullwhip's whole `@media (max-width: 640px)` block including `.plate-score`
and the `#scorebug` gap/padding, and lighthouse's six plate/feed classes with the
`@media (max-width: 420px)` two-column fallback) instead of "byte-for-byte apart from the
scorebug rules". The two rules checklist item 11 names are unchanged and present:
`client/chrome.css:288-292` and `:455-456`.

## F13 — `/client/replay` route: no change, refuted for checklist item 3

**No code change, deliberately.** Checklist item 3's clause is about what the game **declares**
as its replay viewer, and lighthouse declares only the static bundle:

- `coworld_manifest_template.json:14-16` — `"replay_viewer": {"bundle": "static-replay-viewer"}`,
  and no pod viewer URL anywhere in the manifest;
- `.github/workflows/coworld-release.yml:186-196` — certification **hard-fails** unless the
  certify log reports the static replay bundle, with the error text "a pod-served
  `/client/replay` viewer is not acceptable". The release workflow is itself the check for this
  item, and it passes on the declared manifest;
- the static bundle contains no reference to the route: `index.html` and `static_replay.js` never
  mention `/client/replay`, and `attachLive`'s `new WebSocket` (`renderer.js:1288`) is reachable
  only from `client/global.html`, which is not in the bundle;
- both starters ship the identical route and page (`cogame-babel/src/babel/server.nim:502`,
  `cogame-bullwhip/src/bullwhip/server.nim:470`, each with `client/replay.html`), and both
  declare the static bundle in their manifests. Deleting starter-inherited server plumbing that
  the manifest never advertises would be a change with no effect on what the platform serves, and
  would break local `coworld run` replay inspection.

If the judge reads item 3 literally as "the string must not appear in the tree", this is the one
finding I am leaving for adjudication rather than acting on unilaterally: the removal is
mechanical (`server.nim:7,13,447-451,515,520,541-565`, `client/replay.html`,
`src/lighthouse.nim:29-30`) and can be done in r2 in one commit if that is the call.

## F14 — reviewed sha is not head: no change

Repository state, not a defect. `1db815d` ("docs: say plainly that the key fallback is the normal
path at 11x9") touched only `docs/plans/2026-08-22-lighthouse-design.md`
(`git show --stat 1db815d`: 1 file, +13/−6) and was itself green (run 32600520418). All fifteen
fix commits are stacked on it, so head is now strictly ahead of both the reviewed sha and the one
the brief named.

## F15 — the drown-ordering test missed the escape leg

The code was already correct (step 7 at `sim.nim:566-578` precedes step 8 at `:581` and steps
9/10 at `:584-598`); the coverage was not. The test now also drives a runner onto the exit tile
with the gate open **on the exact tick its row floods** and asserts it escapes while the other
two drown, plus the event order within that tick (`escape`, `drown`, `drown`).

**Evidence.** Moving the drown block ahead of the exit block in `applyTick` fails exactly this
new assertion (`Check failed: order == @[evEscape, evDrown, evDrown]`) and nothing else in the
suite — which is precisely the gap it closes.

**Checklist:** item 7's "asserts every order/action is inside its legal bounds", ordering half.

## F16 — starts are seed-independent at 11 × 9: accepted, documented

**No code change.** `placeStarts` does draw from the seed; the constraint simply has a unique
solution at width 11 — the bottom room row is `{1, 3, 5, 7, 9}` and `{1, 5, 9}` is the only
triple pairwise ≥ 4 apart, which is also the fallback. Confirmed over 13 seeds: every one gives
`[(1,7), (5,7), (9,7)]`. Changing the separation or the row would be a design change to a pinned
rule with measured consequences for the competence bar, so the note now states the degeneracy in
§The game step 4 instead, and points out that the maze, the exit, the key set and the aliases —
what §Two name spaces' anti-pre-baking argument actually rests on — do vary per seed.

## F17 — `evTick.notes` repeated unchanged notes

**Was:** `applyTick` recorded the `notes` argument verbatim, which is `""` only when the reply
omitted the field; a model returning the same notes every tick wrote the whole string into every
frame, against the event table's "`""` where **unchanged** this tick".

**Is:** a seat's notes are updated only when the incoming text is non-empty **and** different,
and the tick event records the text on the tick it changed, `""` otherwise.

**Evidence.** New test asserts the first tick records the notes, the second records `""` while
`sim.notes` keeps them, a changed note is recorded again, and `replayMatch` over that log ends
with `frames[^1].notes == sim.notes`. The existing frame-by-frame re-derivation test and the
`test_replay` rune-boundary episode (which sends the same 400/200-rune notes every tick) both
still pass.

**Checklist:** item 2 — the frames are identical either way; this only stops the replay carrying
the same string N times.

---

## NOTED (not fixed)

Out of scope for this round; no code touched.

1. **The tuning harness behind §Tuning revision's sweep is still not committed** (the reviewer's
   *Could not determine* #1). I reproduced the outcome again (4/4 keys, 3/4 all out, 51–52 % talk,
   130/146 = 89.0 % instruction-following) but the `tidePeriod` × `maxTicks` sweep itself remains
   attested only by the note and `README.md:86-113`.
2. **`keeperPrompt`/`runnerPrompt` glyph legends** still read "`~` water, `K` key" without the
   precedence F1 added to the note and `rules.md`. Harmless (the map itself is now unambiguous),
   but a future round could make the legend say it too.
3. **`client/fixtures/dev_shell.html` and `sample_replay.json` are not exercised by CI.** F4 added
   `node --check` for the two shipped viewer scripts; the dev fixture generator is checked by hand
   only (`node --check client/fixtures/gen_fixture.js` passes).
