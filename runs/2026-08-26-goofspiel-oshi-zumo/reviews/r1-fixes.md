# r1 fixes — cogame-goofspiel-oshi-zumo

Head: `af5e9bbc3af17c6433b9b3453381332fac51aecb` (main)
CI: https://github.com/Metta-AI/cogame-goofspiel-oshi-zumo/actions/runs/33020196047 — **success**
(jobs `test`, `docker-smoke`, `wasm-viewer` all `success`; single run, one push of nine commits).

Pushed through the GitHub Git Data API (blobs → trees → commits → one fast-forward of
`heads/main`); every created tree sha was compared against the local commit's tree sha before the
ref moved, so the pushed content is byte-identical to what was tested locally, exec bits included
(`tools/build_replay_viewer.sh` and `tools/ci/docker_smoke.sh` are still `100755`).

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | fixed | `511e3695` | `client/renderer.js:295-385`, `tools/ci/renderer_fixture.html:50-330` |
| F2 | no change — evidence | — | `src/gozu/sim.nim:204-210`, `coworld_manifest_template.json` |
| F3 | fixed | `8357bf1a` | `src/gozu/llm.nim:452-480`, `tests/test_llm.nim` (new) |
| F4 | fixed | `f924c03d` | `tests/test_bot.nim:62-66` |
| F5 | fixed (label only) | `af5e9bbc` | `tests/test_sim.nim:225-232` |
| F6 | fixed | `c1208a7a` | `scripts/tune_baselines.nim` (new), `docs/baseline-tuning.md` (new) |
| F7 | fixed | `5241e7bd` | `src/gozu/server.nim:237`, `:366-379` |
| F8 | fixed | `1c12d060` | `src/gozu/sim.nim:703-717`, `tests/test_replay.nim:166-181` |
| F9 | no change — evidence | — | `coworld_manifest_template.json`, design.md:857-864 |
| F10 | fixed | `45382432` | `client/renderer.js:99-107`, `:355-359` |
| F11 | fixed | `2ebbae24` | `src/gozu_player.nim:46-67` |

Local verification before the push: every `tests/*.nim` in debug **and** `-d:release` (Nim 2.2.4,
the CI recipe), `src/gozu.nim` and `src/gozu_player.nim` built in release,
`tools/ci/chrome_scope_check.mjs`, and the renderer fixture driven by
`tools/ci/viewer_smoke.mjs --strict-text-bounds` in headless chromium against a local copy of the
shipped page.

---

## F1 — a full-cap `say` was drawn ellipsized at narrow widths

**Commit `511e3695`.** Checklist item 15 ("ellipsis is … a defect for **sentences** … widen the
band, do not shorten the text") and its worst-case-fixture bullet.

*Was:* the band was reserved for exactly `SAY_LINES = 2` lines with the font floored at 7 px, so at
360 px with four seats it held ≈ 136 px of run while an 80-rune remark needs ≈ 560 px.
`wrapLines` appended `…` to the second line: the sentence was cut. The fixture could not see it —
`viewer_smoke.mjs` keeps only the first 12 `ellipsized` samples and all 12 were the 24-char
`clampName` nameplate cut — so 374 ellipsized draws sat in a green log.

*Is:*

- `client/renderer.js:361-382` `sayBand(ctx, layout)` reserves as many **lines** as `MAX_SAY = 80`
  worst-case (full-width) runes need at this panel width, measuring `永` in the band's own font at
  the current `--hudscale`, plus one line of slack for word-wrap ragging, capped at 55 % of the
  panel so the block above it keeps its room. The band is still reserved whether or not a seat is
  speaking, so nothing jumps when a remark lands.
- `client/renderer.js:301-317` `splitToFit` breaks an over-long run on **rune** boundaries (never
  inside a surrogate pair) instead of ellipsizing it — a Japanese sentence is one 80-rune "word"
  that word wrapping cannot break at all, which the old code cut on every screen size.
- `client/renderer.js:349-359` the panel's pad and content width are now the ones the band
  measures against (`panelPad` / `panelContentW`), so the two cannot drift apart.

*The fixture now catches the defect it was supposed to catch* (`tools/ci/renderer_fixture.html`):

- a **second** worst case, `fullCapRun`, an 80-rune Japanese sentence with **no spaces** in it
  (asserted space-free and 80 runes at start-up, alongside the existing mixed CJK/latin/emoji
  line);
- every say opens with a unique full-width mark, so a fragment on the canvas is attributable to
  the remark it came from;
- `watchDraws` records every string the shell draws; `checkRemarks` (`:271-311`) fails if any
  remark fragment carries an ellipsis, if a remark that reached the canvas was not drawn in full
  (`drawnInFull`, `:257-269`, reassembles the consecutive band lines and compares rune for rune),
  or if **no** remark reached the canvas at all — a fixture that gates nothing is now a failure;
- a fresh shell per (mode, width), sized before it loads, and `states[0]` already carries a
  full-cap remark on every seat, so the worst case is on screen at every one of 360/640/1280 px in
  both modes rather than wherever playback happened to be.

**Evidence.** Negative control, run locally against the shipped page with the new fixture and the
band forced back to two lines: `VIEWER SMOKE FAILED: data-replay-error: remark ELLIPSIZED at
goofspiel @ 360px: "burning a king on a…"`. With the fix, CI run 33020196047, job `wasm-viewer`,
step *Renderer text fixture (360 / 640 / 1280 px)*:
`canvas text: 1449 drawn, 0 never inside the canvas (0 draws crossed an edge), 138 ellipsized`,
and every one of the printed `ellipsized` samples is a nameplate
(`"goofspiel-oshi-zumo-rea…"`, `"goofspiel-oshi-zumo-tem…"`) — no remark is among them, which is
now an assertion rather than an inference. The real-replay smoke in the same job is
`13356 drawn, 0 never inside …, 0 ellipsized`.

## F2 — `pool` is "awarded so far", not the note's literal `pool = 91`

**No change; the finding is a documentation reconciliation against the design note, and the note
is not mine to edit.**

The code implements the note's *other* sentence, design.md:190-193 ("a deadline episode is fully
scored at the stop, goofspiel from prizes already awarded"), and it has to: with a fixed 91 the
deadline score array does not sum to 0, which would break the zero-sum property
`tests/test_sim.nim:245-272` asserts over 200 seeded episodes in both modes. On a `complete`
episode `roundsPlayed == 13` and `awardedPool == 91`, so the formula reduces to exactly the note's
`(points_i − 22.75) / 68.25` — the CI smoke's `results.json` shows `points [22.75×4]`,
`scores [0.0×4]`. The deviation is already documented where a reader meets it: the shipped rules
page (`coworld_manifest_template.json`, `game.docs.pages[0]`: "`pool` = the prize value awarded so
far (91 for a complete episode)") and the code comment at `src/gozu/sim.nim:205-207`. The reviewer
records no checklist bearing, and item 10 / `results_schema` is satisfied. What remains is a line
in the note's §Scoring; the design note is the coordinator's artifact, not the fixer's.

## F3 — any `bid` string starting with a/j/q/k was read as a card letter

**Commit `8357bf1a`.** Checklist item 8 (LLM reply handling: retry once, then record the
fallback) — the old behaviour bypassed both.

*Was:* `parseBidText` switched on `trimmed[0].toUpperAscii()` before any numeric scan. Confirmed
by building the pre-fix tree and running the public entry point:

```
a bid of 11 -> 1
just 12     -> 11
```

Both are legal cards, so `decideAll`'s validator (`llm.nim:549`) and the server's re-check
(`server.nim:330`) accepted them: no retry, `fallbacks` not incremented, and the seat bid a card
it never asked for.

*Is:* `src/gozu/llm.nim:452-480` — `rankLetter` accepts the letter only when the trimmed reply
**is** the token (bare, or wrapped in the usual quotes/punctuation: `K`, `k`, `"k"`, `K.`).
Anything else falls through to the numeric scan, whose raise is what triggers the retry carrying
`bidList(sim.legalBids(seat))` and then the scripted fallback — the path item 8 requires.

*Evidence:* `tests/test_llm.nim` (new, runs in both CI modes) pins the accepted forms
(`"11"`, `"  13  "`, `"11 — the king"`, `"7, keeping the ace back"`, ints, floats, `A/j/Q/K.`),
that a bare letter is goofspiel-only, and that `"a bid of 11"`, `"just 12"`,
`"queen or king, whichever is left"` and `"keeping the 13 back"` all raise. Green in CI run
33020196047, job `test`, debug and `-d:release`.

## F4 — no test asserted `results.reason == "complete"` for an all-scripted episode

**Commit `f924c03d`.** Checklist item 7, first half (the second half, "every order/action inside
its legal bounds", was already asserted at `tests/test_bot.nim:48`).

`playAll` now reads the reason out of `resultsJson()` — the same object the platform receives —
at `tests/test_bot.nim:66`, so it is asserted by every baseline-driven episode in the file:
assertion 12 (200 seeds × both modes × both baselines, and the mixed-baseline table), assertion
14, and assertion 15's certification fixture. Previously the only `reason` assertions were on
hand-driven episodes and recorded fixtures, and the all-scripted case existed only as a line in
the docker-smoke log. Green in CI run 33020196047, job `test`.

## F5 — assertion 7's sweep was driven by synthetic bidders, not by `match`/`hoard`

**Commit `af5e9bbc` — label only, no assertion changed.**

The reviewer's own mitigation is the answer to the coverage half: the property the note states —
both **real** baselines, `minBid = 1`, `coins = 20`, every seeded episode inside 20 rounds, 200
seeds — is asserted by `tests/test_bot.nim:64-78`, which calls `scriptedBid` for `skMatch` and
`skHoard` and checks `oshi.roundsPlayed <= 20` and termination. What was actually wrong was the
title: `tests/test_sim.nim`'s suite 7 said "both baselines" while driving `legal[0]` and a
rotating index. It is now "every seeded episode ends within 20 rounds, for any legal bidder", with
a comment pointing at the test that runs the baselines. Nothing was deleted, skipped or widened —
the sweep is the *stronger* claim (termination is a property of the rules, not of the bidder), it
just is not the claim its name made.

## F6 — no grid-tuning harness for the baselines in the tree

**Commit `c1208a7a`.** Checklist item 7, last sentence.

`scripts/tune_baselines.nim` (new) sweeps the three constants the prescribed rules leave free —
goofspiel `hoard`'s cheap/dear split, oshi-zumo `match`'s spend-rate multiplier `k`, oshi-zumo
`hoard`'s desperation divisor `f` — over a grid, playing the swept bidder in seat 0 against the
shipped baselines and against a uniform-random legal bidder over the same 200 seeds at every grid
point. At the **shipped** grid point the harness asserts every bid it produces equals
`scriptedBid`'s (`checkedBid`), so the table is about the code that ships rather than a lookalike
written beside it. `docs/baseline-tuning.md` (new) records the run and reproduces it in one line
(`nim c -r scripts/tune_baselines.nim 200`).

Result: every shipped constant sits at (or tied at) the peak of its curve — split 7 is the maximum
against `match` (0.1882) and within noise of the maximum against random; `k = 1.0` is at the flat
peak against random (0.98) and falls away on both sides; `f = 2` is at the flat peak (0.98) and
beats `match` head to head. **No baseline changed**, which is also why this is a harness and a
recorded table rather than a code change: the note prescribes these exact algorithms
(design.md:263-280) and the grid agrees with them.

## F7 — the game thread had no exception guard

**Commit `5241e7bd`.** Checklist item 5 (category `hang`).

*Was:* `runGame` ran unguarded on its own thread. A raise — the reachable one is `writeArtifact`'s
`IOError` on a non-2xx artifact POST (`server.nim:150-151`) — killed the thread while the mummy
server kept serving, so `finishEpisode`'s `quit(0)` never ran and the container stayed up until
the platform's own episode timeout, with no diagnosis.

*Is:* the episode body is `playEpisode` (`src/gozu/server.nim:237`) and `runGame`
(`:366-379`) is a `try` / `except CatchableError` wrapper that logs the message and `quit(1)`s.
A failed episode that ends is a result; a container that will not exit is not. Nothing else
changed — the normal path still ends in `finishEpisode`'s `quit(0)` after the 20 s grace, which
CI's docker-smoke exercises (`smoke OK: seats=4 … reason=complete`, all four player containers
exited 0).

## F8 — `checkReveal` skipped the points comparison on a length mismatch

**Commit `1c12d060`.** Checklist item 2 (replay re-derivation asserted by a test).

`src/gozu/sim.nim:709-717` now raises on the length itself instead of guarding the element-wise
comparison with `if event.points.len == logged.points.len`, so a recorded reveal carrying a
shorter or longer `points` array is the raised drift design.md:498-499 promises rather than a
silent pass. `tests/test_replay.nim:166-181` records a real episode, truncates one reveal's
`points` from 4 to 3 and asserts `replayMatch` raises `GozuError`. Green in CI run 33020196047,
job `test`, both modes.

## F9 — the certification fixture's policy names come from the alias pool

**No change; the manifest follows the note.**

design.md:857-864 prescribes `Sprocket / Gizmo / Ratchet / Widget` as the fixture's policy names,
and `CogNames` (`src/gozu/sim.nim:17-20`) is the alias pool the seeded `tableNames` draws from —
so a collision in the *fixture* is a consequence of the note's own two lists overlapping, not of
the code diverging from it. The reviewer's own reading agrees: "the two name spaces are working
exactly as designed (policy name in `.plate-name`, alias in `.plate-alias`); the collision only
makes the cert/smoke replay confusing to read", and the finding carries no checklist bearing
(item 4 is satisfied — agents see aliases only, the viewer maps aliases to policy names for
non-baseline seats). Changing the fixture names would be a deviation from the authoritative note
to improve the legibility of one CI artifact; if that is wanted, it belongs in the note first.

## F10 — the say band's font scale came from the canvas layout, not `--hudscale`

**Commit `45382432`.** design.md:743-745 ("sized from `MaxSayLen = 80` … measured in the render
font **at the current `--hudscale`**").

`client/renderer.js:99-107` adds `hudScale()`, which reads the computed `--hudscale` off
`document.documentElement` — the variable `C.relayout()` sets (`chrome_common.js:493-500`) — and
falls back to 1 when it is absent. `computeLayout` carries it as `layout.hud` (one read per drawn
frame) and `sayFontPx` (`:355-359`) applies it: `max(7, round(11 * layout.scale * layout.hud))`.
The 7 px floor is unchanged, and F1's band sizing measures in exactly this font, so the reserved
band now follows the chrome's own scale as the note describes.

## F11 — the player's receive loop was an untimed blocking read

**Commit `2ebbae24`.** Checklist item 5 ("no unbounded loop or **blocking read**").

`src/gozu_player.nim:56-67`: the loop passed no timeout, so `whisky.receiveMessage` used its
default of `-1` — block until a frame arrives or the socket dies. The bound was the game's
behaviour, not the player's code. The read now carries
`timeout = COWORLD_TIMEOUT_SECONDS (1200 s when the env is silent) + 120 s`, which is longer than
any legitimate gap between frames (the game broadcasts every round and sends `final` before it
quits) and is still an explicit end to the wait. whisky returns `none` on a timeout — the same
clean exit-0 path a closed socket already took — and the log line now names which of the two
happened. CI's docker-smoke still reports `all 4 player containers exited 0`.

---

## NOTED (not fixed)

- The reserved band is a large empty dashed box at 360 px with four seats (≈ 55 % of the panel),
  because it is sized for 80 full-width runes at the 7 px floor. That is the trade item 15 asks
  for ("reserved whether or not anything is speaking, so the scene does not jump"), but a
  re-layout that moved remarks to a frame-wide strip below the panels at narrow widths would read
  better. That is a design-note change, not a fix.
- `scripts/tune_baselines.nim` is not compiled by any CI job (nothing outside `tests/*.nim` is),
  so it can rot. Wiring it into `ci.yml` as a compile-only step was out of scope for this round.
- In oshi-zumo `hoard` beats `match` head to head at every tested spend rate above 0.5
  (`docs/baseline-tuning.md`). Both are legal and both terminate; it is worth knowing before the
  ladder is read as a strength ordering.
