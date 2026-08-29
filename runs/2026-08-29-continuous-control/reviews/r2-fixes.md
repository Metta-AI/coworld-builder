# r2 fixes — continuous-control

Head: `b67f8c8673e85b9895165609040a68aae93e8c44`
CI: https://github.com/Metta-AI/cogame-continuous-control/actions/runs/33252260364 — **success**
(jobs: `test` success, `docker-smoke` success, `wasm-viewer` success; `gh run list` also shows the
F1 commit's own run 33252249362 on 38cc254a green. The six runs between them are `cancelled`: the
workflow's `concurrency: ci-${{ github.ref }}` group superseded each intermediate push. The head
run is the one that matters and it is green on `main`.)

Range: `a8db2b32..b67f8c86`, eight commits, one per finding. Every commit was replayed onto `main`
through the Git Data API (blobs → tree with `base_tree` → commit → `PATCH refs/heads/main`,
`force: false`) one commit at a time; nothing was force-pushed and no history was rewritten. Each
API tree sha was checked against the local `git rev-parse <sha>^{tree}` before the ref moved.

| finding | disposition | commit | files |
|---|---|---|---|
| r2-F1 (blocking) | fixed | `38cc254a` | client/cc_block.html:591-609, client/replay_broadcast.html:3548-3566, tests/test_cc_viewer.nim:70-83, .github/workflows/ci.yml:340-366 |
| r1-verdict B1 | fixed (with F3) | `460e7ddb` | tools/ci/renderer_fixture.html:182-262 (poll :195-213, say row :231-273) |
| r2-F2 | fixed | `86c57d37` | tests/test_cc_viewer.nim:78-85 |
| r2-F3 | fixed | `cd6784bb` | tools/ci/renderer_fixture.html:40-58, :215-223 |
| r2-F4 | fixed | `316fbe69` | tools/ci/viewer_smoke.mjs:425-433, docs/PHYSICS.md:145-153 |
| r2-F5 | no change (informational; now measured) | — | tools/ci/renderer_fixture.html:245-273 |
| r2-F6 | fixed | `739942b1` | docs/PHYSICS.md:135-144 |
| r2-F7 | fixed | `97b387e4` | tests/test_cc_sim.nim:352-385 |
| r2-F8 | fixed | `b67f8c86` | tests/test_cc_endcard_labels.nim:39-61 |

## The evidence F1 and B1 turn on, before and after

| signal (source) | a8db2b32 (run 33249877981) | b67f8c86 (run 33252260364) |
|---|---|---|
| `viewer-smoke.json` `feed_lines` | `0` | **`2`** |
| `viewer-smoke.json` `console_tail` | twelve `[error] continuous-control chrome event: TypeError: Failed to execute 'insertBefore' on 'Node': parameter 1 is not of type 'Node'. at Object.pushFeed …` | **zero** `continuous-control chrome` lines (15 lines, all `[warning] Unknown sprite protocol message type: 97/34`) |
| new ci.yml step "The chrome swallowed no error while the replay played" | did not exist | `chrome errors in the smoke's console tail: 0 of 15 lines` |
| `renderer-fixture/viewer-smoke.json` | `loaded: true`, `console_tail: []` — and, as it turns out, measuring a page whose feed could not run at all (see B1 below) | `loaded: true`, `ms: 1222`, `failure: null`, `data_replay_loaded: "true"` — with the say row now asserted present, full-length and inside the frame at 360 / 640 / 1280 px |
| both `--strict-text-bounds` steps | `canvas text: 0 drawn, 0 never inside` | unchanged: `0 drawn, 0 never inside` (the viewer draws no canvas 2D text at all; item 15's escape hatch is the fixture, and the fixture now covers the model's string) |

---

## r2-F1 — the `say` is never drawn: `ccFeed` hands a string to `pushFeed(row: Node)` — **fixed**, `38cc254a`

**What the code did.** `ccFeed(text, cls)` called `ctx.pushFeed(text, cls || '')`
(`client/cc_block.html:594-596`, page `:3551-3553`). The inherited `pushFeed` takes a **Node** —
`feedEl.insertBefore(row, feedEl.firstChild)` (`:2286-2293`, byte-for-byte the starter's) — so the
call threw `TypeError: parameter 1 is not of type 'Node'` before any of its body ran.
`CcChrome.event`'s catch logged and returned `false`, `applyEvent` treated that as "not handled"
and fell through to a ctf switch with no cc case. Result: no cc feed line ever entered the DOM at
any width, including the 140-rune LLM `say`; and because `stagestart` and `fall` push their feed
line *before* `ctx.banner(...)`, both banners were pre-empted with it.

**What it does now.** The block builds the row itself, in exactly the shape the starter's own
appended block uses (`coworld-ctf/client/replay_broadcast.html:4508-4513`, `feedRow`):

```js
  function ccFeed(text, cls) {
    if (!ctx || !ctx.pushFeed) return;
    var row = document.createElement('div');
    row.className = 'feed-row' + (cls ? ' ' + cls : '');
    row.textContent = text;
    ctx.pushFeed(row);
  }
```

`textContent`, not `innerHTML`: the `say` line carries model-authored text straight off the replay,
so no markup path is opened. The `cls` the old call discarded (`say` / `good` / `bad`) now lands on
the row as a class, which is what the fixture selects on. The two `ctx.banner(…)` calls pass the
starter's second argument explicitly, so the chip's class is `banner-chip ` rather than
`banner-chip undefined`.

`client/replay_broadcast.html` was **regenerated** by `scripts/build_broadcast_page.py` from
`/workspace/starters/coworld-ctf/client/replay_broadcast.html` + the edited block — never
hand-edited. (Re-running the generator on the shipped block before the change reproduced the
committed page byte-identically, so provenance is intact either side of the fix.)

**The test pin.** `tests/test_cc_viewer.nim:78` asserted `"ctx.pushFeed(text, cls" in page` — the
*wrong half* of the mismatch, which is precisely why a green suite kept F1 alive (that is r2-F2).
It now asserts `"ctx.pushFeed(row)" in page`. **This is the correction of a wrong assertion, not a
weakening**: the assertion that pins the callee (`function pushFeed(row)`, sliced out of the
starter's own file at test time) is untouched, and the F2 commit adds two further checks on top.

**Making the swallowed path loud.** The catch already logged with a distinctive prefix, and that
log was sitting in CI's own artifact while everything stayed green. `ci.yml` gains a step,
`The chrome swallowed no error while the replay played`, that reads the smoke's
`viewer-smoke.json` and fails the `wasm-viewer` job on any `continuous-control chrome` line in
`console_tail`. It printed `chrome errors in the smoke's console tail: 0 of 15 lines` at head.
(Honest limit, stated in the step's comment: `console_tail` is the last 30 console lines, so the
step reads what the harness recorded, not every line the page ever printed. The exhaustive guard
for a dropped feed line is the fixture, below.)

**Evidence.** Head-run artifact `viewer-smoke/viewer-smoke.json`: `feed_lines: 2` (was `0`),
`console_tail` free of any `continuous-control chrome` line (was twelve TypeErrors), the new gate
step green, and the `renderer-fixture` step green with the say row asserted rendered. Locally, the
real page (marker-substituted exactly as `Dockerfile.replay-viewer:31-34` assembles it, served over
http, driven through the page's own `onText` path in headless chromium) rendered the four surviving
feed rows and one banner chip at 360 / 640 / 1280 px; reverting `ccFeed` to the string call in the
same harness reproduced the twelve-per-run `at Object.pushFeed` TypeErrors and an empty feed.

**Checklist item:** 15 (the LLM-authored string is now drawn at all, which is the precondition for
measuring it), and 14(iii)/13 indirectly — a chrome whose every event handler failed silently is
not the starter's chrome working.

## r1-verdict B1 — item 15 unverifiable for the LLM `say` — **fixed**, `460e7ddb` (+ `cd6784bb` for the string itself)

B1 named three defects. (a) and (b) — a 133-rune SAY behind a no-op `slice(0, 140)` and no
length assertion — are r2-F3, commit `cd6784bb`. (c) — the feed row is never measured — is this
commit. The fixture now:

* takes `#killfeed .feed-row.say` **at the moment the say event is driven**. The inherited feed
  keeps `MAX_FEED = 4` rows and the seven events after `say` push it out, so measuring after the
  loop would measure nothing — this is why the check is inside the loop.
* **fails if that row is absent.** This is the standing guard for F1's class of bug: a feed line
  dropped inside `CcChrome`'s catch now turns the renderer-fixture step red instead of passing
  invisibly.
* asserts the row still carries all 140 runes it was fed (a truncating render is a failure, not a
  pass).
* asserts the row's box is non-empty **and inside the frame** at 360 / 640 / 1280 px — all four
  edges against the iframe's own `innerWidth`/`innerHeight`. `.feed-row` is
  `white-space: nowrap; max-width: none` under `html { overflow: hidden }`, so "inside the feed's
  column" is not the question; "inside the frame" is.
* asserts a banner chip rendered — the other casualty of a throw in the feed.

**And it waits for the page's own first frame before driving anything.** This is the substantive
find of this round and it answers the review's "Could not determine" #1 (why the fixture's own
`console_tail` was empty while the bundle step recorded twelve errors from the same code path):
the block's `ctx` — the inherited `pushFeed`/`banner` — is only handed to it when the **page**
calls `CcChrome.frame(s, PB_CTX, …)` (`window.CcChrome.install(PB_CTX)` at `:2952` runs *before*
the appended block defines `window.CcChrome`, so `install` is never reached; `ctx` is set by the
per-frame calls). `window.CcChrome` exists as soon as the page's scripts run, so the old
100 ms-poll drove the block with `ctx === null`, where `ccFeed`'s own guard returns early and
nothing is pushed at all — no throw, no row, nothing to see. The fixture would have measured a page
that could not talk and passed. It now polls for `#cc-ribbon`, which the block's `ccEnsureNodes()`
creates on that first real frame and nothing else does, for 20 s, then fails by name.

**Evidence.** Head run's `renderer-fixture/viewer-smoke.json`: `loaded: true`, `ms: 1222`,
`failure: null`, `data_replay_loaded: "true"` — reached only if all three iframes drove a real
frame and every assertion above passed at all three widths. Locally, against the real page: pass at
all three widths with the say row `561 x 16 px` at `[536, 617, 1097, 633]` in `1280 x 720`; with
`ccFeed` reverted to the string call the same fixture fails with
``no `.feed-row.say` rendered``.

**Checklist item:** 15 — the worst-case renderer fixture now drives the real page with a full-cap
remark **and asserts that remark rendered, at full length, inside the frame**, which is what the
item asks of the escape hatch it prescribes when `canvas_text.total == 0`.

## r2-F2 — test 42 asserted both halves of the mismatch — **fixed**, `86c57d37`

The call-site half had to change in the F1 commit for CI to be green there, so this commit adds
what the test was actually missing: `row.className = 'feed-row'` is present (the row is built here,
with the starter's class) and `ctx.pushFeed(text` appears **nowhere** in the page. A future edit
that reverts to passing the text is red at the unit level, without needing a browser. Nothing was
deleted: test 42 keeps the starter-derived callee pin verbatim and gains two checks.
Verified locally: `nim r tests/test_cc_viewer.nim` 7/7.

**Checklist item:** 1 (no test loosened — this strengthens one) in service of 15.

## r2-F3 — the fixture's "Exactly 140 runes" SAY was 133 — **fixed**, `cd6784bb`

The literal is now exactly 140 runes — `MaxSayRunes` (`src/cc/sim_types.nim:37`) — and the no-op
`Array.from(SAY).slice(0, 140)` is gone. The fixture measures its own string and, if it ever
drifts, sets `data-replay-error` and throws **before building a single iframe**, so the smoke
reports the reason rather than quietly testing a short row. Inside each iframe it additionally
cross-checks against the cap the engine itself publishes (`window.CC_WIRE.maxSayRunes`, emitted by
`src/cc/wire_constants.nim`), so a server-side cap change this file did not follow is red too.
Verified: `Array.from(SAY).length === 140` locally, and the head run's fixture step green with the
cross-check live.

**Checklist item:** 15 — "the fixture asserts its own strings are still full-length".

## r2-F4 — `viewer_smoke.mjs`'s feed probe could not match `#killfeed` — **fixed**, `316fbe69`

The probe read `#feed, .feed, #log, [id$="-feed"]`; this lineage's feed is coworld-ctf's
`<div id="killfeed">`, which matches none of them, so `feed_lines` was structurally 0 for this
viewer whatever the feed did. `#killfeed` joins the list, in the same lineage-fallback style as the
`#seek` / `#derk-clock` entries the file already carries. The number stays **reported, not gated**:
rows expire on the inherited dwell timer, so a 0 between beats is legitimate and gating it would
flake.

The review's other two observations under F4 are accurate and are **not** changed: the harness
still has no DOM text measurement (item 15 does not ask it to grow any — it prescribes the fixture,
which is where the DOM measurement now lives), and `console_tail` still gates nothing *inside* the
harness — the new `ci.yml` step in the F1 commit is what gates it, in the repo rather than in the
shared template.

This is the repo's only divergence from the builder's copy of `viewer_smoke.mjs`, so
`docs/PHYSICS.md` records it as divergence 16 rather than leaving the "copied verbatim" claim in
`ci.yml`'s header quietly false.

**Evidence.** Head run: `feed_lines: 2` on the real bundle with the CI replay, from
`{"loaded":true,"ms":584,…,"feed_lines":2}` in the step log and in the artifact.

**On the brief's question — what does the CI replay guarantee?** It has no LLM text (no
`ANTHROPIC_API_KEY` in `docker_smoke.sh`, so the seat plays scripted and emits no `say`), but it is
**not** feed-less: `stagestart`, `order` (every turn), `stride`, `milestone`, `stageend` and `end`
all route through `ccFeed`, and the scripted episode emits them. So the smoke does now observe real
feed rows from the real replay — `feed_lines: 2` above, sampled while two rows were within their
dwell window. Because rows expire, the *guaranteed* lower bound at an arbitrary sampling instant is
0, which is why this number is reported and the **fixture** is the gate.

**Checklist item:** 15 (evidence quality — a probe that reads 0 by construction is not evidence),
13 (the smoke's readouts now describe this viewer).

## r2-F5 — the full-cap say row fits the frame; B1's overflow arithmetic does not reproduce — **no change**

Nothing to fix: the review's own measurement (and mine) show the row inside the frame at all three
widths, and the r1 verdict's "clips at the left frame edge" half does not reproduce. I did **not**
add a `.feed-row.say { max-width … }` override — that would be a design change to bound something
that is not overflowing, and it would invalidate the measurement rather than settle it.

What changed is that the claim is no longer only a measurement in a review: the fixture asserts it
on every CI run at 360 / 640 / 1280 px (B1 commit). My own numbers, on the real page in headless
chromium with the real font: the say row is `561 x 16 px` at `[536, 617, 1097, 633]` in
`1280 x 720`, and inside the frame at 640 and 360 as well.

## r2-F6 — `docs/PHYSICS.md` divergence 15 cited a stale replay size — **fixed**, `739942b1`

`132 082 B` was from an earlier run; run 33249877981 logged `replay.json (131999 bytes)`. The size
moves with the strings each episode records, so the note now quotes it to the kilobyte
("about 132 000 B") and cites the run the exact figure came from. The surrounding claim (~130 KB
rather than the design note's ~32 KB estimate, bounded by `MaxOrderRecordRunes = 6000` per record)
is unchanged and correct.

## r2-F7 — the note's fall-limit literals were pinned nowhere, and the hopper's `fwHigh` branch was unreachable in test 11 — **fixed**, `97b387e4`

Test 11 re-derived `isUnhealthy` from the same spec fields it was testing, so it passed for any
values of them. It now also pins the design note's literals (`design.md:277`) — hopper
`lowY == 0.70 m`, `maxPitch == 20°`, `highY == GuardMaxYQ16` (a world-box guard, explicitly *not* a
fall condition, which is what r1-F5 made it); walker `0.80 / 2.00 m / 57°`; cheetah
`terminates == false` — and drives each branch at its own boundary for both terminating bodies, so
`fwHigh` fires deterministically on the hopper instead of waiting for a draw from a band that can
no longer reach 20 m. The randomised sweep and both its aggregate checks are untouched; four
`check`s became sixteen.
Verified locally: `nim r` and `nim r -d:release` on `tests/test_cc_sim.nim`, 14/14 both modes.

**Checklist item:** 1 (strictly more assertions), 7 adjacent.

## r2-F8 — test 47b greped only the appended block — **fixed**, `b67f8c86`

The note scopes the forbidden-vocabulary grep to the built page **and** `broadcast_core.js`; the
test read `core` but never greped it. It now runs the same 16 tokens over the comment-stripped
`broadcast_core.js` as well, and offenders name their file. As the review predicted, the outcome is
unchanged today (zero hits at these exact spellings), which is the point: the gate now covers the
forked draw layer where a paintbot word could re-enter unseen.
Verified locally: `nim r tests/test_cc_endcard_labels.nim`, 4/4.

**Checklist item:** 14 (provenance / vocabulary), 1.

---

## NOTED (not fixed)

* **`Unknown sprite protocol message type: 97` / `: 34`** (the review's "Could not determine" #2)
  — 15 of these warnings are still in the head run's `console_tail`. Unchanged by this round, not a
  finding, and I did not trace `broadcast_core.js`'s packet dispatch; `97` is `'a'` and `34` is
  `'"'`, consistent with JSON text arriving on the sprite binary path. It gates nothing and the
  replay plays.
* **`failed` in the fixture is last-write-wins** across its checks and across widths, so the
  reported message is the last failure rather than the first. Pre-existing shape; I kept it rather
  than restructure a file two commits already touch this round.
* **The champion prompts still tell a cog a brake saves a fall** (`tools/ci/policies.json`) — the
  r1 verdict's own non-blocking observation, unchanged, not a finding this round.
* **The renderer fixture is now sensitive to iframe boot time** (20 s for `#cc-ribbon` in each of
  three iframes). At head the whole fixture step took 1 222 ms, so the margin is wide, but it is a
  new way for the step to go red if a runner is pathologically slow. That is the intended trade:
  the alternative is the fixture silently measuring a page whose chrome never received its context.

## Local verification used for this round

No Docker daemon and no emscripten here, so the wasm bundle itself is CI-only. Everything else was
run locally before pushing: Nim 2.2.4 via `nimby` with `nim.cfg` regenerated exactly as `ci.yml`
does, all `tests/test_*.nim` green in debug (62/62) and `test_cc_sim.nim` also green in
`-d:release`; and the real `client/replay_broadcast.html` — the three `Dockerfile.replay-viewer`
markers substituted, `data/font.ttf` served as `./font.ttf`, the static-replay adapter stood in for
the wasm core so the page's own `onText` → `applyEvent` → `CcChrome` path runs — driven in headless
chromium (Playwright 1.55.0) at 360 / 640 / 1280 px, both with the real `tools/ci/renderer_fixture.html`
in its own iframes and with the block regressed to the old string call to confirm the fixture fails.
