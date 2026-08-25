# r2 fixes — collab-cooking

Head: **`f82126bf5da18509ec7dd8553148adceffdbac48`** (`main`)
CI: run **32823608970** — conclusion **`success`**
(<https://github.com/Metta-AI/cogame-collab-cooking/actions/runs/32823608970>), all three jobs
green: `test` (206 passed / 1 skipped), `docker-smoke` (`smoke OK: seats=4 … reason=complete`),
`wasm-viewer` (including `Load the bundle in a real browser` and the new
`Load a full-cap remark in a real browser (DOM text bands)`).

| finding | disposition | commit | files |
|---|---|---|---|
| R2-O1 (blocking) | fixed | `e091b9c` | `client/parts/game.css:81-135,223-225`, `client/parts/game.js:95-171,444`, `client/replay_broadcast.html`, `tests/test_viewer_contract.py:147-168` |
| R2-O2 (blocking) | fixed | `5aea159` | `client/parts/game.css:144-165`, `client/parts/game.js:228-248`, `client/replay_broadcast.html`, `tests/test_viewer_contract.py:170-186` |
| R2-O3 (blocking) | fixed | `4d00033` | `tools/ci/dom_text_smoke.mjs` (new, 399 lines), `.github/workflows/ci.yml:249-293`, `tests/test_viewer_contract.py:199-218`, `.gitignore` |
| R2-O4 | fixed | `2a00b36` + `f82126b` | `src/collab_cooking/coworld/plans.py:29-32`, `live_episode.py:52,571,810`, `replay-viewer/collab_cooking_replay.nim:46-51,657-666,706-708,888`, `tests/test_replay_parse.py`, `tests/test_viewer_contract.py` |
| R2-O5 | no code change | — | see below |
| R2-O6 | fixed | `17d48a5` | `replay-viewer/collab_cooking_replay.nim:45-51,944` |
| R2-O7 | fixed | `1f71d48` | `replay-viewer/collab_cooking_replay.nim:609-628` |
| R2-O8 | fixed | `aeb49d4` | `src/collab_cooking/coworld/replay.py:258-269,295-315,347-352`, `tests/test_replay_parse.py` |
| R2-O9 | no code change | — | see below |
| R2-O10 | NEEDS-DESIGN | — | `src/collab_cooking/coworld/player.py:162` |
| R2-O11 | fixed | `59349d6` | `tests/test_baselines.py:165-171` |
| R2-O12 | **DISPUTED** (+ one-line guard) | `feb1f8a` | `.gitignore` |

Measurement method for the after-numbers below is the review's own: the real
`client/replay_broadcast.html` spliced exactly as the Dockerfile splices it (real
`client/chrome_common.js`, real `data/font.ttf`), the wasm core stubbed so the page's own
`ccSayBar` / `renderFeed` / `relayout` do the work, and a frame carrying a full-cap 120-rune `say`
on **every** seat plus six full-cap feed lines, in headless chromium 1.55.0. That harness is now
committed as `tools/ci/dom_text_smoke.mjs` and runs in CI, so every number below is reproducible
with `node tools/ci/dom_text_smoke.mjs`. Its four cap-length strings are a Latin sentence, an
unbroken `W` run with no break opportunity, CJK (multi-byte runes) and a ragged word pattern —
the last is ~2× taller than the sentence the review measured, so the "before" numbers here are at
or above the review's.

---

## R2-O1 — the say band clipped a full-cap remark

**What it did.** `#saybar .say-chip` carried `max-height: calc(22 * var(--u)); overflow: hidden`.
Nothing in the sizing derived from `SAY_RUNES`, so the comment above it ("sized from the 120-rune
cap") was not true of any line of code. Measured at head: chip `clientHeight` 26 px against
`scrollHeight` 57 px for the review's own sentence at 1280×800 — and 97 px (CJK) and 149 px
(ragged) for the other two shapes a 120-rune remark can take, i.e. **54 %, 73 % and 83 % hidden**.

**What it does now.** `ccSayBand()` (`game.js:134-171`) measures the cap: three hidden gauge chips
— `SAY_RUNES` copies of the widest rune a remark can be made of (`W`, a CJK ideograph, an emoji),
plus an 8-rune alias prefix — laid out in the chip's own font at the chip's own width, and writes
the tallest of them to `#saybar`'s inline `min-height` on every `relayout()` pass, **before**
`--topband` is computed from it. `max-height`/`overflow: hidden` are gone. `word-break: break-all`
is what makes the gauge an upper bound rather than a guess: every line fills to the box edge, so
no ragged 120-rune string can be taller than a dense run of the widest glyph (this is why the
band is 90 px and not 149 px). The band is reserved whether or not a seat is speaking, so the
board still never moves.

Two guards, both measured rather than guessed: past `SAY_BAND_SHARE` (35 %) of the viewport
height the chip type scales down (`--sayfit`) so the whole cap still fits — the remark is never
cut — and that same share is what stops the band and the board from chasing each other down (a
taller band narrows the board, which narrows the chips, which would need a taller band). Under
320 px of viewport height the band is dropped entirely by a media rule, exactly as the feed is
dropped under 640 px of width; a surface that cannot show a whole remark should not show a fifth
of one.

**Evidence (measured, after).** `scrollHeight == clientHeight` on all four chips at every viewport
where the band shows:

| viewport | stage | `--hudscale` | `--topband` | chip client/scroll before | chip client/scroll after | say band quiet → speaking |
|---|---|---|---|---|---|---|
| 1280×800 | 838 px | 1.103 | 213 px | 26 / 57–149 | **90 / 90** | 90.0 → 90.0 px |
| 1024×640 | 655 px | 0.862 | 167 px | 21 / 46–120 | **70 / 70** | 70.0 → 70.0 px |
| 900×558 | 562 px | 0.739 | 142 px | 18 / 40–105 | **60 / 60** | 60.0 → 60.0 px |
| 640×397 | 392 px | 0.516 | 111 px | 13 / 28–73 | **42 / 42** | 42.0 → 42.0 px |
| 414×736 | 414 px | 0.545 | 122 px | 12 / 26–68 | **51 / 51** | 51.0 → 51.0 px |
| 360×640 | 360 px | 0.500 | 115 px | 11 / 24–63 | **46 / 46** | 46.0 → 46.0 px |
| 1920×1080 | 1135 px | 1.493 | 286 px | 35 / 42–130 | **121 / 121** | 121.0 → 121.0 px |

No-jump, the other half of the design's claim, also holds at the new size: `#saybar` and
`--topband` are identical between the silent frame and the four-full-cap-say frame at every
viewport (the fixture fails on a difference of more than 1 px). The cost is the honest price of
the reservation: the board is 8–12 % narrower at desktop sizes (908 → 838 px at 1280×800) and
unchanged at 360 px, where it is width-bound.

At 360×223 — the letterboxed row in the review's table, where the chip showed 11 px of a 57 px
line box — the band is now dropped and the board is *larger* than before (152 → 175 px wide), so
nothing there is clipped either. Checklist item: **15**, DOM branch (reserved band sized from the
server's cap, measured in the font; no ellipsized sentence).

## R2-O2 — the feed line ran off the clipped stage

**What it did.** The game block reuses ctf's `.feed-row` class, whose inherited rule is
`white-space: nowrap; max-width: none`. Measured at head, 1280×800: row box 249 px wide,
line 594 px wide on one unwrapped line — **58 % of the remark outside the column**, painting past
the right edge of `#stage`, which is `overflow: hidden`.

**What it does now.** An override in the **appended game block** (`#feed .feed-row`), not an edit
above the banner comment: `display: block; white-space: normal; overflow-wrap: anywhere;
max-width: 100%`. Provenance is intact — `client/replay_broadcast.html` still regenerates
byte-identically from the mounted starter (`python3 tools/build_broadcast_page.py
/workspace/starters/coworld-ctf`, `git status` clean), ctf's own rule is untouched, and the test
asserts both halves. A wrapped row is taller, so `renderFeed` now drops the oldest row while the
column would otherwise grow past the top of the canvas — a feed shows the last lines that fit,
and no line is ever cut.

**Evidence (measured, after).** `scrollWidth == clientWidth` on every feed row, every row inside
`#stage`:

| viewport | row clientWidth | row scrollWidth before | row scrollWidth after | rows shown | past stage right |
|---|---|---|---|---|---|
| 1280×800 | 230 px | 594–1359 px | **230 px** | 6 | −8.8 px (inside) |
| 1024×640 | 180 px | 469–1113 px | **180 px** | 6 | −6.9 px |
| 900×558 | 154 px | 413–988 px | **154 px** | 6 | −5.9 px |
| 1280×360 | 104 px | 265–619 px | **104 px** | 5 | −4.0 px |
| 1280×321 | 73 px | 265–619 px | **73 px** | 2 | −4.0 px |
| 1920×1080 | 312 px | 710–1730 px | **312 px** | 6 | −11.9 px |

(At 640 px and below the feed is `display: none` by the pre-existing media rule, so there is
nothing to measure and nothing to clip.) Checklist item: **15**.

## R2-O3 — no gate could see either bug

**What it does now.** `tools/ci/dom_text_smoke.mjs` is the worst-case renderer fixture, in the
shape a DOM viewer needs. It loads the real page with the real chrome and the real font, stubs
only the wasm core, and drives the page's own `onText` with a frame built to hurt: a full-cap
remark on every seat and six full-cap feed lines, Latin, CJK (multi-byte), one unbroken token and
one ragged word pattern. The cap is read from the two places that enforce it (`SAY_RUNES` in
`coworld/plans.py`, `SayRunes` in the Nim module) and the run fails if they disagree, so the
fixture is pinned to what the server would actually let a model say.

At 13 viewports (1920×1080 down to 360×640 and 360×223) it asserts, for every model-text node:
`scrollHeight <= clientHeight + 1`, `scrollWidth <= clientWidth + 1`, the node's box inside
`#stage`, the string still rendered **in full** (so a quietly shortened remark fails the fixture
instead of passing it), and the reserved band the same height speaking and silent. It refuses to
pass vacuously: four viewports must have rendered all four full-cap strings, four visible chips
each, and a viewport that drops the band must show no partial remark anywhere either.

Wired as its own `ci.yml` step in the `wasm-viewer` job after the existing browser load, with
`dom-text-smoke.json` and `dom-text-smoke.png` uploaded as evidence.
`tools/ci/viewer_smoke.mjs` is **not** modified — it is a verbatim template copy and stays
canvas-only.

**Evidence.** Run 32823608970, step `Load a full-cap remark in a real browser (DOM text bands)`:
`dom text smoke OK: every 120-rune remark fits its band at 13 viewports`. The gate is real, not
decorative: the committed script, run unchanged against the reviewed head's own client
(`git archive a5ec2c8 | tar -x`), reports **108 failures** — 52 vertical clips and 56 horizontal
ones — beginning `1280x800 say-chip[0]: clipped vertically -- scrollHeight 57 > clientHeight 26
(54% hidden)` and including `1280x800 feed-row[2]: clipped horizontally -- scrollWidth 1359 >
clientWidth 249`. `tests/test_viewer_contract.py`
pins that `ci.yml` still runs it. Checklist item: **15**, final bullet.

## R2-O4 — the feed line's cap did not cover its alias prefix

Both sides composed `"<alias>: <say>"` and then cut the whole line to 120 runes, so the last 7
runes of every full-cap remark were dropped before CSS ever saw the line. The alias and the
remark are now truncated separately and the line cap is sized from the sum:
`FEED_RUNES = SAY_RUNES + ALIAS_CAP + 2` (130) in `coworld/plans.py`, `FeedRunes = SayRunes +
AliasRunes + 2` in the Nim module. Pinned by `tests/test_replay_parse.py`
(`test_a_feed_line_carries_the_whole_say_and_the_alias`, driven by the existing 120-rune
multi-byte say: the text after the prefix must equal all 120 runes) and by a contract test that
the two caps agree. `f82126b` is a fix-forward on the same finding: the first commit put the
first call to `truncRunes` above the proc's definition and Nim rejected it
(`collab_cooking_replay.nim(696, 17) Error: undeclared identifier: 'truncRunes'`, run
32823219320); the proc moved up, nothing else changed. This is the "flagged judgment call" in the
brief, fixed the way it asks: the remark keeps its full 120 runes.

## R2-O5 — no code change (resolved by R2-O1)

The observation is that under 640 px the feed is hidden, leaving the say chip as the only surface
for model text at the design's own 360 px target. That is now a working surface rather than a
clipped one: measured at 360×640 the chip is 46 px of reserved band with `scrollHeight ==
clientHeight` and the whole 120-rune remark rendered. The `#feed { display: none }` rule under
640 px is deliberate and is what checklist item 11 asks for, so it stays.

## R2-O6 — the chrome-JSON cap

`ChromeCap = 4000 # the state JSON is <= 4 KB` was enforced as `ChromeCap * 4`. The constant is
now `16000` and the guard is `if result.len > ChromeCap` — the same 16 000 bytes, no behaviour
change — with the nominal ~4 KB and the reason it is not a limit (a 400-tile heat array alone
approaches 5 KB) in the comment.

## R2-O7 — the jam beat's placement

`bn` is the busiest *tile's* blocked total, but the running count walked **every** blocked event
anywhere, so on the head replay (bn = 87, 359 blocked events) the beat landed at tick 36 of 480.
The running count is now taken at that doorway's own tile, so the beat lands where that doorway
has taken half of the jams it takes all episode, which is what the comment claims.

## R2-O8 — serve/expire attribution

The departed tickets are now split **once** into served and expired, and the serve events draw
their recipes from that same list in the same order, so two serves in a tick can no longer both
claim the first departed ticket's recipe and the two decisions cannot disagree. Single-serve
ticks — every tick in the head replay — derive exactly what they derived before, so
`test_rederivation` still holds frame for frame. Pinned by a new unit test on `derive_events`:
two serves in one tick get the two recipes that actually left the board, and a serve plus an
expiry in one tick is one of each.

## R2-O9 — no code change

The dead half is inherited chrome. `client/replay_broadcast.html` is generated by
`tools/build_broadcast_page.py` from ctf's page and must regenerate byte-identically from a fresh
starter checkout (checklist item 14, provenance); deleting rules from ctf's own `<style>` would
break exactly that. The live half — `.feed-row`, which the game block reuses — is R2-O2, and it
is fixed by an override in the appended block, which is the only way to fix it without touching
the inherited page.

## R2-O10 — NEEDS-DESIGN (not fixed)

`player.py:162` gives a prompt seat `DEFAULT_BASELINE` regardless of `config.fallback_scripted`.
The player process cannot know the game's `fallback_scripted` today: `player_config`
(`live_episode.py:886-902`) does not carry it. Fixing it properly means adding a field to the
player wire protocol — `docs/protocol.md`'s `player_config` frame and the design note's protocol
table both enumerate that frame — which is a design change, not a fix at the cited site. The
divergence is also unreachable in anything the repo ships: all eight variants and the
certification fixture omit `fallback_scripted`, so both sides run `brigade`. Recorded here rather
than changed, as in r1.

## R2-O12 — DISPUTED

No `__pycache__` or `.pytest_cache` path is tracked, at head or at the reviewed sha:

```
$ git ls-tree -r --name-only a5ec2c8602856d21ad8ec3e4f70af7c6fab82ede | wc -l
83
$ git ls-tree -r --name-only a5ec2c8602856d21ad8ec3e4f70af7c6fab82ede | grep -cE '__pycache__|pytest_cache'
0
$ git check-ignore -v src/collab_cooking/coworld/__pycache__/replay.cpython-311.pyc
.gitignore:1:__pycache__/	src/collab_cooking/coworld/__pycache__/replay.cpython-311.pyc
```

`.gitignore:1` has ignored `__pycache__/` all along; the directories exist in any working tree
that has run pytest (mine included), which `ls` shows and `git ls-files` does not. The GitHub tree
API agrees: `gh api repos/Metta-AI/cogame-collab-cooking/git/trees/main?recursive=1` lists no such
path. One real gap behind the misreading: `.pytest_cache/` itself was not ignored, so a
`git add -A` could have committed it. `feb1f8a` adds that one line. No tracked file was removed,
because there was none.

---

## NOTED (not fixed)

- The push tool (`tools/push_via_api.py`) had no local→remote sha map for the r1 chain in this
  clone, so its first run re-minted the ten r1 commits on top of the previous head before adding
  mine. Nothing was force-pushed and `a5ec2c8` is still an ancestor of `main`; the net
  `git diff a5ec2c8..f82126b` is exactly the ten r2 commits' changes and no more (13 files, 909
  insertions, 47 deletions). The state file
  is correct now, so later pushes append.
- The say band is a visible cost at desktop sizes (`--topband` 164 → 213 px at 1280×800, board
  908 → 838 px). That is the price of a 120-rune cap on four seats in quarter-width chips, and it
  is measured rather than chosen; a smaller band needs a smaller cap or a different say layout,
  which is a design decision, not a fix.
- `word-break: break-all` on the say chip means a long English word can break mid-word in a
  narrow chip. It is what makes the reserved band an upper bound instead of a guess (the ragged
  alternative measures 149 px against 90 px at 1280×800 for the same cap), so the trade is
  deliberate.
- The review's "could not determine" on 4.25 px chip type at 360 px is unchanged by these fixes:
  the type scale is the starter's `--hudscale` floor and the game block's `8.5 * var(--u)`, and
  nothing here touched either at that width (the band's `--sayfit` is 1 at every viewport ≥ 321 px
  tall).
