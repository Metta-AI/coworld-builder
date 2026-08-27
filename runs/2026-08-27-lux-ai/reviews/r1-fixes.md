# r1 fixes — lux-ai

Head: `66b5d3bb2c5c88d9b947437c1194f180681bc702` (`main`)
CI: https://github.com/Metta-AI/cogame-lux-ai/actions/runs/33090975748 — **success**
(`test`, `docker-smoke`, `wasm-viewer` all green; every step green, including
`The scripted baselines are the swept pick`, `Load the bundle in a real browser`,
`Native <-> wasm hash gate`, `Worst-case chrome fixture` and the new
`The commander line fits its band`).

B1 was also proved green on its own, before anything else was pushed:
run https://github.com/Metta-AI/cogame-lux-ai/actions/runs/33090307926,
headSha `e673713cdbf64ada4c8fcb4f3b6bf16fcbe91dcb`, conclusion **success**.

`git push` over HTTPS is refused in this sandbox ("No anonymous write access"), so
every commit was published through the GitHub API (blob → tree → commit →
fast-forward `heads/main`, never forced), one API commit per finding, and each
remote tree was verified byte-equal to the local tree before the next was pushed.
The shas below are the **remote** ones.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `e673713` | `scripts/lux_block.html`, `client/replay_broadcast.html:1827-1884,2408-2414`, `tools/ci/renderer_fixture.html`, `.github/workflows/ci.yml:402-446`, `tests/test_lux_viewer.nim:227-266` |
| N2 | fixed | `db780f6` | `src/lux/llm.nim:71-85` |
| N14 | fixed | `7e8a89e` | `tests/test_lux_directives.nim:84-105` |
| N16 | fixed | `27d10f6` | `tests/test_lux_engine.nim:31-58` |
| N4 | fixed | `66b5d3b` | `src/lux/sim_state.nim:45-58,191`, `src/lux/resolve.nim:122,129,167-169,269,300,323`, `src/lux/micro.nim:315`, `tests/test_lux_resolve.nim:388-431` |
| N1, N3, N5, N6, N11, N12, N13, N15, N17, N18, N19 | not fixed (see below) | — | — |

---

## B1 — the worst-case fixture produced no text-fit evidence, and the note had no band

`e673713`. Three defects under one finding; the fix is one commit because the CI
gate the third part adds would be red without the second.

**What the code did — including one thing the review could not see from the source.**
I rebuilt the shipped bundle locally the way `Dockerfile.replay-viewer` builds it
(the `sed` over `client/replay_broadcast.html` plus `chrome_common.js`,
`broadcast_core.js`, `static_replay.js`, a hand-emitted `wire_constants.js`) and
ran `tools/ci/viewer_smoke.mjs` against the fixture in headless chromium
(Playwright 1.55.0, the pinned version). Result:

1. **The shim never took.** The fixture spliced its wasm shim *before*
   `<script src="./static_replay.js">`, and `static_replay.js:284` assigns
   `window.LuxStaticReplay` itself — so the shim was overwritten, every iframe
   booted the real worker, and all three died inside the iframe with
   `data-replay-error: "Missing required replay URL"`. Measured, before any
   change: `[{"width":"360","err":"Missing required replay URL","loaded":null,
   "adapterIsShim":false,"feedRows":0}, …]` for all three widths. The top-level
   page still set `data-replay-loaded`, so the smoke was green. The fixture was
   rendering **nothing at all** — a stronger statement than the review's.
2. **The 160-rune note had no band.** With the shim fixed, the full-cap note
   rendered into the starter's `.feed-row .badge` and I measured the boxes the
   review said it could not:

   | width | `#stage` | badge box | verdict |
   |---|---|---|---|
   | 360 | `[116,0,245,203]` | `[-163,150,235,154]` | starts 279 px left of the stage |
   | 620 | `[166,0,455,350]` | `[47,297,445,301]` | starts 119 px left of the stage |
   | 1280 | `[329,0,952,722]` | `[283,634,935,642]` | starts 46 px left of the stage |

   The review's arithmetic (~390 px of text in a 114 px column at 360 px) was
   right: the measured badge is 398 px wide. `#stage { overflow: hidden }` clips
   all of it. The commander line was invisible at **every** width, not only 360.
3. **Nothing asserted the strings**, and the second frame was fed from an
   uncaught `setTimeout`.

**What it does now.**

- (a) *A reserved band, sized from the cap.* `scripts/lux_block.html` gives the
  directive rows their own `lux-say` class: `display: block`, `width: 100%` of the
  feed column, `white-space: normal`, `overflow-wrap: anywhere` (a 160-rune note
  need not contain a space), `min-height: var(--lux-say-band)`, and a
  `#killfeed` `min-height` that holds the band **whether or not anybody is
  speaking**. Every number is derived from the server's cap and the badge's own
  font, in the CSS, next to the rule: `--lux-note-runes: 160` (MaxNoteRunes) ×
  `--lux-note-em: 0.69` (measured mean uppercase advance of `--finefont` at the
  badge's 0.1em tracking) × `--lux-note-size: 7` (the badge font, in `--u`) = 773
  `--u` of text; the column gives 206 `--u` per line (168 at `.tiny`, where the
  starter narrows `#killfeed` to 190 `--u`), so the band reserves
  `ceil(773/206) = 4` lines (5 at `.tiny`) plus the speaker line.
  `client/replay_broadcast.html` was **regenerated** with
  `scripts/fork_broadcast_page.py`, not hand-edited; `chrome_common.js` and
  `broadcast_core.js` are untouched and still byte-identical to the starter's
  (their sha256 pins in `tests/test_lux_viewer.nim` are green in CI).
- (b) *The fixture asserts its own strings.* It feeds turn 430 then turn **431**
  (stride 1: the page reads a jump of more than `stride*4+2` ticks as a seek and
  calls `clearFeed()`, so the old 430→440 pair would have measured one turn's
  rows), waits out the row's entrance animation, then reads each commander line
  back out of the iframe's DOM: rune length against the string it fed
  (`FED.indexOf(text)` plus `runes !== NOTE_RUNES`), box against `#stage` and the
  iframe viewport, `scrollWidth`/`scrollHeight` against the client box. Both
  seats must be found at all three widths. A throw in either frame now rejects
  into `data-replay-error` instead of escaping an uncaught `setTimeout`.
- (c) *The measurement is gated in CI.* The fixture prints one
  `LUX-TEXTFIT {json}` console line; `viewer_smoke.mjs` copies the console tail
  into `fixture-out/viewer-smoke.json`; the new `ci.yml` step
  **`The commander line fits its band`** parses that line and fails the job on a
  missing measurement, a short note, a clipped note, a note outside the stage or
  the viewport, or fewer than two seats × three widths. It is a separate step
  precisely because `--strict-text-bounds` cannot gate this repo: all of its
  chrome text is DOM, so `canvas text: 0 drawn` is structural, and the step's own
  comment says so.

**Evidence.** CI run 33090975748, job `wasm-viewer`, step
`The commander line fits its band`:

```
text fit: {"chrome_off_stage": 0, "chrome_outside": 1, "clipped": 0, "failures": [],
           "measured": 48, "note_runes": 160, "notes": 12, "outside": 0, "short": 0, "widths": 3}
  360px: stage [116, 0, 245, 203]  band [144, 27, 239, 165]  4 commander lines, 160 runes each
  620px: stage [166, 0, 455, 350]  band [354, 174, 449, 312]  4 commander lines, 160 runes each
  1280px: stage [329, 0, 952, 722]  band [755, 464, 942, 660]  4 commander lines, 160 runes each
commander band OK: 48 boxes measured, 12 full-cap notes inside #stage at 360/620/1280 px
  (1 partial chrome overflow reported, not gated)
```

The `canvas_text` line the checklist asks to be cited is, in the same job, step
`Worst-case chrome fixture`:
`canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`
— structurally zero, which is exactly why the step above exists.

**The gate is not vacuous.** Both regressions were run locally against the same
harness and both exit 1:

- band CSS removed → `VIEWER SMOKE FAILED: data-replay-error: Error: text does not
  fit: 360px: the commander band crosses the left edge of #stage (band
  -152,159,235,164 in stage 116,0,245,203) | …`
- one fed note quietly shortened to 60 runes → `… 360px: the note rendered 60
  runes, the server cap is 160 | …` (all three widths).

**Two tiers, deliberately.** The gate fails on the model-authored band (full
length, unclipped, wholly inside `#stage` and the viewport). The rest of the
chrome — `.plate`, `.plate-name`, non-`lux-say` feed rows — is measured and
**reported**, and fails only if a box has no intersection with the stage at all.
That mirrors `viewer_smoke.mjs`'s own doctrine (`never_inside` is gated,
`outside` is reported). The one reported `chrome_outside` is the right-hand
`.plate-name` at the 360×203 embed, where `#stage` letterboxes to 129 px wide and
the checklist's own item-11 rule (`.plate-name { min-width: 3.2em }`) then
overflows the 19 px side track by ~15 px. Making that box fit would mean either
dropping item 11's `min-width` or removing plate content, so it is reported,
printed by the CI step, and left alone — see NOTED below.

Checklist item satisfied: **15** (third and fourth bullets: a reserved band sized
from the server's cap and measured in the font it draws in; a fixture that
asserts its own strings are full-length, with the step and its `canvas_text` line
cited). Item 14 is untouched: the page still regenerates from the starter mount
plus one appended block, and the two byte-pinned JS files were not edited.

---

## N2 — the Bedrock model ladder had one entry

`db780f6`. `bedrockModelIds()` returned only
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, so `tryNextBedrockModel` could
never return true: a 403 carrying "Model access is denied" fell through to
`client.disabled = true` (LLM dead for the rest of the episode) and every 429 set
`client.throttled`, which `decide.turn` treats as "skip the retry". The note's
ladder (§Decisions) is haiku-4-5 **then**
`us.anthropic.claude-sonnet-4-5-20250929-v1:0`; that second entry is back, the
`sonnet-4-6` exclusion is unchanged, and the docstring now says why the list must
have more than one member. `BEDROCK_MODEL` still pins one. No test touched
bedrock before or after; effort suppression still fires for both ids (`"4-5"`).

## N14 — the "9 KB reply" test asserted a tautology

`7e8a89e`. `check (recovered or true)` computed `recovered` and threw it away.
I traced the actual path: `truncateRunes(4096)` cuts this reply open with **no
closing brace at all**, so `extractJsonObject`'s balanced scan finds nothing,
`rfind('}')` returns -1, and it raises `DirectiveError: no JSON object in reply`.
The test now asserts that message — i.e. the caller gets an error it can record
as `parse_error`, never a raw `JsonParsingError` from underneath — and adds the
half the title claimed but never tested: a 9 KB reply whose object closes inside
the cap parses to `stFuel`. `check capped.runeLen == MaxReplyBytes` is kept.
Nothing was weakened: a tautology became two assertions
(`[OK] a 9 KB reply is capped, and the cut-open remainder fails as a CLASSIFIED error`,
run 33090975748, four times — debug and release, twice each).

## N16 — the timing test asserted the note's arithmetic, not the code's

`27d10f6`. The test asserted 36 × max(spacing 6 s, budget 11 s) = 396 s. The code
takes `turnStart` at the top of `decide.turn`, sleeps up to `turnSpacingMs`
*after* it, and checks the budget **before** each attempt instead of bounding the
attempt, so the worst turn is 6 s + a 7 s attempt-1 timeout = 13 s. The test now
asserts `turnSpacingMs + attempt1Ms == 13000`, that this **exceeds**
`turnBudgetMs`, that 36 × 13 = 468 s, that 468 + 3 + 100 + 20 = 591 s < 660 s, and
— stronger than the line it replaces — that the wall-clock stop's top-of-loop
check can overshoot by one more worst-case turn and still land inside 720 s
(`wallClockBudgetSeconds + 13 <= 720`). No behaviour changed; the arithmetic in
the test is now the code's.

## N4 — four declared config knobs were not read by the sim

`66b5d3b`. `workerCargo`, `cartCargo`, `workerCooldown` and `cartCooldown` were
parsed by `config.update`, echoed into the replay config header and declared in
`config_schema`, while every consumer called `sim_types.cargoCap(kind)` /
`baseCooldown(kind)`, which read the compile-time constants — and
`applyCityBuilds` charged a literal `20` that only coincidentally equalled
`WorkerCooldown`. `sim_state` now exposes `cargoCap(world, kind)` and
`baseCooldown(world, kind)` reading `world.config`, and the transfer, movement,
mining, city-build and sim-guard sites call those.

- **No behaviour change at the shipped defaults**: `defaultGameConfig` seeds all
  four fields from the very constants the rules used to read, the hash mix is
  untouched, and `GameVersion` therefore stays at 1. CI confirms it — the
  determinism, replay-re-derivation and full-episode baseline tests are green and
  `The scripted baselines are the swept pick` reports the identical pick and
  identical objective key: `pick: workers=6 fuelNights=18 prospectorEarly=6
  prospectorLate=10 seedTiles=8  key=[1, 5, 4, 86]` → `tune_baselines --check ok`.
- The replay config header already carried all four, so an episode that *does*
  override one now re-derives with the value it recorded, which it could not
  before.
- Two new cases in `tests/test_lux_resolve.nim` fail against the constants: a
  12-unit worker cargo cap on mining, a 30-unit cart cap on a transfer, a
  40-tenth worker cooldown on a move and on a city build (recovering 22 on the
  freshly paved tile), and a 15-tenth cart cooldown (recovering 12 on the road it
  just paved). Green as
  `[OK] the configured cargo caps and cooldowns are the ones the rules use` and
  `[OK] a city build costs the CONFIGURED worker cooldown`.

---

## Findings I did not fix, and why

**N5 — the cart hand-off is evaluated before the night policy.** The finding is
correct: `micro.nim:300-336` runs `block handoff` before the `npShelter` rule at
`:339-349`, and the note numbers night policy as rule 1. I did **not** reorder
them. This is a rules change: it alters scripted play, so it needs a
`GameVersion` bump *and* a re-run of `tools/tune_baselines.nim --write`, because
the tuner's objective ends in a tiebreaker on *total city tiles built*
(`tools/tune_baselines.nim:8-17`) and CI re-runs the whole sweep with `--check`
on every push. Any change to the micro layer moves those totals and can move the
argmax; worse, the sweep's first gate is "forester wins the pinned seed and both
sides survive all nine nights", which no re-sweep can satisfy if no grid point
does. This sandbox has no Nim toolchain (`nim`, `nimby` absent), so I could
neither re-run the sweep nor re-derive the constants, and a wrong guess would
have cost the round's green CI for a non-blocking finding. Recommended follow-up,
in one commit, by someone with the toolchain: move the `block handoff` below the
night rule, bump `GameVersion` to 2 with a `GV2 (micro order)` changelog line,
run `nim r -d:release --path:src tools/tune_baselines.nim --write`, and re-run
`tests/test_lux_baselines.nim`.

**N1, N3, N6, N11, N12, N13, N15, N17, N18, N19 — not in this round's scope.**
The brief named B1 (must) and N2/N4/N5/N14/N16 (cheap and genuinely defects). Of
the rest, N1 (lobby-start divergence) and N6 (`build: "city"` blocks research)
are rules/behaviour changes with the same GameVersion + re-sweep cost as N5; N3
(`gameOverTicks` unheld), N13 (whole-reply cap in runes, not bytes) and N17/N18
are behaviour or contract changes the review itself marks as self-consistent or
safer-as-shipped; N11/N12 (undocumented deviations) and N15 (tests the note
specifies that are absent) are real gaps but are documentation and new-test work,
not defect fixes, and none of them falsify a checklist item. I changed no code
for any of them.

## NOTED (not fixed)

- **The right-hand `.plate-name` clips at the 360×203 embed.** Found by the new
  measurement, reported by the CI step as `chrome_outside: 1`. At that embed the
  stage letterboxes to 129 px wide, the scorebug's side track is ~19 px, and item
  11's mandated `.plate-name { min-width: 3.2em }` overflows it by ~15 px into
  `#stage { overflow: hidden }`. Fixing it means either dropping the item-11
  rule or dropping plate content at `.tiny`; both are design decisions outside
  B1, so the box is measured and printed rather than gated.
- **A budget-exhausted seat gets two fallback records for one turn** — one
  `cause: "timeout"` at `decide.nim:218-219` and one from the "anything still
  open" loop at `:285-286` (the review's own second observation under N16).
  `results.fallbackTurns` counts once; only the record count doubles. Left alone:
  it changes the replay's chat records, which is behaviour, and it is not what
  N16 was filed for.
- **`relayout()` flaps around its `.tiny` threshold at 1280×722.** The fitted
  stage came out 623 px wide (not tiny) in one run and 597 px (tiny) in the next,
  because the band heights and the board fit chase each other and the loop stops
  after four passes. Inherited from the starter, harmless for the gate (the band
  fits in both states), noted because it makes any future pixel-exact assertion
  at that size flaky.

## Test discipline (checklist item 1, second half)

`git log -p 1c36d56..HEAD -- tests/` removes exactly three assertion lines, all in
this round, all replaced by strictly stronger ones:

- `check config.wallClockBudgetSeconds <= 720` → `check
  config.wallClockBudgetSeconds + worstTurnMs div 1000 <= 720` (N16).
- `check (recovered or true)` → `check reason.startsWith("no JSON object in
  reply")` plus `check parse(survivor).stance == stFuel` (N14).
- `check capped.runeLen == MaxReplyBytes` moved four lines earlier in the same
  test; it is still asserted (`tests/test_lux_directives.nim:90`).

No `skip`, no `xfail`, no widened tolerance, no deleted test file. Two test files
gained tests (`test_lux_viewer.nim` +2, `test_lux_resolve.nim` +2).
