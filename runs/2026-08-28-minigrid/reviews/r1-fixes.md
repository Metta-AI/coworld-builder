# r1 fixes — minigrid

Repo: `Metta-AI/cogame-minigrid`, branch `main`
Head: **`b19bc085bbd70f63fcc6c4277b45ad71fad3d908`** (17 commits on top of the reviewed
`d8f9e7c`)
CI: run **33213509695** — <https://github.com/Metta-AI/cogame-minigrid/actions/runs/33213509695>
— conclusion **success** on `main` at `b19bc085` (all three jobs green, every step ran, no
`continue-on-error`, no skips). `SEAT-COUNT FAIL` appears **0 times** in that run's log.

Evidence lines from run 33213509695:

```
test        Manifest loads under the pinned coworld CLI  manifest loads: minigrid coworld-minigrid:latest 2 variants
test        Re-run the baseline sweep with --check       baseline tuning matches the recorded sweep
docker-smoke Raw-Docker episode smoke                    smoke OK: seats=1 results=1046B replay=56889B reason=complete
wasm-viewer  Load the bundle in a real browser           canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
wasm-viewer  Worst-case renderer fixture (the LLM path)  canvas text: 74 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
```

(The fixture measured 57 runs at the reviewed sha and 74 now: the say row and the agent-view
inset's captions are text the fixture could not see before.)

No test was weakened, skipped or deleted. Test-file changes this round are **additions only**:
`test_minigrid_manifest.nim` (+2 assertions on the manifest shape the CLI requires, +2
`expect ConfigError` cases), `test_minigrid_viewer.nim` (+1 derivation assertion). One assertion
was *corrected*, not loosened: test 34 asserted `game.image`, the location that made the manifest
unloadable (B1); it now asserts `game.runnable.image` plus the absence of the two keys at `game`.

---

## Disposition table

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| **B1** manifest cannot be loaded by `coworld==0.1.43` | **fixed** | `1187590` | `coworld_manifest_template.json:15-27,484`, `tests/test_minigrid_manifest.nim:123-138` | **10 (manifest)**, 12 |
| N1 `#fpv` 7×7 inset never made visible | fixed | `4796dea` | `client/minigrid_block.html:409-423`, `client/replay_broadcast.html`, `tools/ci/renderer_fixture.html` | 14, 15 (advisory) |
| N2 the eight named draw procs do not exist | **no change** (design-level) | — | `client/broadcast_core.js` | 14 — not falsified |
| N3 ribbon/pips overlay the board, not the left gutter | **no change** (design-level) | — | `client/minigrid_block.html:57-92` | 14(b) — holds |
| N4 `.tiny` hides the in-game alias | fixed | `c8abac4` | `client/minigrid_block.html:220-228` | 4, 11 |
| N5 endcard vocabulary list narrower than the note's | **disputed / no change** | — | `tests/test_minigrid_endcard_labels.nim` | 14 — not falsified |
| N6 `fallback.cause` emits `throttled`; never `disconnected` | **disputed / no change** | — | `src/minigrid/decide.nim:229-257` | 8 — holds |
| N7 invalid entry counted twice | fixed | `b22f971` | `src/minigrid/decide.nim:277-300` | 8 |
| N8 a turn can reach ~11.6 s against a 9.5 s budget | fixed | `a1a8f57` | `src/minigrid/decide.nim:188-205` | 5 (timeout) |
| N9 `docker_smoke.sh` does not fail on `reason == "fault"` | **disputed / no change** | — | `.github/workflows/ci.yml:253` | 1, 12 |
| N10 no CI step runs the real CLI validator | fixed | `2aebf85` | `.github/workflows/ci.yml:57-88` | **10 (manifest)** |
| N11 `ci.yml` never re-runs the sweep with `--check` | fixed | `5cae390` | `.github/workflows/ci.yml:186-193` | 7 |
| N12 derived page never re-derived or `--check`ed | fixed | `4dbec8e` | `tests/test_minigrid_viewer.nim:128-136` | 14 |
| N13 `plan`/`fallback`/`budget` are replay-only | fixed | `4f3dc37` | `src/minigrid/replays.nim:92-127`, `src/minigrid/server.nim:385-390` | 2, 14 |
| N14 `keycorridor` corridor wall at `x = 7`, not `x = 6` | **NEEDS-DESIGN / no change** | — | `src/minigrid/tasks.nim:178-222` | — |
| N15 4096-**byte** cap applied as runes after a 16 KB parse | **disputed / no change** | — | `src/minigrid/llm.nim:187-200` | 9 — holds |
| N16 player container does not truncate before sending | fixed | `c9f8c59` | `src/minigrid_player.nim:23,38-45` | 9 |
| N17 fixture asserts nothing about its own string lengths | fixed | `3269c27` + `617e4b9` | `tools/ci/renderer_fixture.html` | **15 (legibility)** |
| N18 `generateXland` indexes an empty seq; no bound in `validate()` | fixed | `2e003ac` | `src/minigrid/sim_config.nim:160-176`, `tests/test_minigrid_manifest.nim:123-138` | 5, 7 |
| minor 1 `labels.nim` names a test file that does not exist | fixed | `de5a505` | `src/minigrid/labels.nim:1-5` | — |
| minor 2 the `#clock` three-way split | **disputed / no change** | — | `client/replay_broadcast.html:4508-4531` | — |
| minor 3 pre-attempt block logs `falling back` | **disputed / no change** | — | `src/minigrid/decide.nim:166-175` | 8 |
| *(unlisted, fix-forward)* `replay_summary.py` gameVersion scan is flaky | fixed | `5cfe938` | `tools/replay_summary.py:76-93` | 1 |
| *(unlisted, found by N17)* model-authored feed rows run off the frame | fixed | `e8f96f1` + `b19bc08` | `client/minigrid_block.html:198-214`, `tools/ci/renderer_fixture.html` | **15 (legibility)** |

---

## B1 — the manifest the pinned CLI cannot load

**Was:** `game.image` and `game.source_url` sat as siblings of `game.runnable`, and the one
declared player was typed `"policy"`. `coworld build` — the first step of `coworld-release.yml`,
which pins `coworld[auth]==0.1.43` — reads the image off **every** runnable
(`coworld/bundle.py:128`) and raised `KeyError: 'image'` before the static-viewer hook ran.

**Is:** the placeholder and `source_url` live inside `game.runnable`; `player[0].type` is
`"player"`, a member of the CLI's own enum.

**Evidence:** reproduced against the pinned version before and after the change:

```
$ python3 -c "_load_template_manifest(template,'0.1.0',{'{{MINIGRID_IMAGE}}':'coworld-minigrid:latest'})"
before:  KeyError: 'image'                    (coworld/bundle.py:128)
after :  OK — CoworldManifest(game.name='minigrid', game.runnable.image='coworld-minigrid:latest')
```

and in CI, on the pushed head: `test :: Manifest loads under the pinned coworld CLI ::
manifest loads: minigrid coworld-minigrid:latest 2 variants` (run 33213509695). Satisfies
checklist item 10 — the manifest now validates under the loader the release run uses, and the
item's two enumerated sub-clauses (`game.docs`, both protocols) were already true and still are.

## N10 — the CI step that would have caught B1

Design note test 34 says a CI step runs the installed `coworld`'s own
`validate_upload_manifest` / `_load_template_manifest`, and the Nim test's docstring claimed one
did; the shipped item 34 was a string/shape check. The `test` job now installs
`coworld[auth]==0.1.43` (the same pin `coworld-release.yml` uses, with a comment tying the two
together) via `uv run --no-project --with` and loads the template through the real
`_load_template_manifest`, with the placeholder map compose.yaml's single service derives. A
release-breaking manifest is now red on push rather than at `coworld build`.

## N1 — the 7×7 agent-view inset

**Was:** `mgRenderAgentView` painted `#fpv-canvas` and wrote `ALPHA · FACING <DIR>` every frame
into a panel whose only `on` toggle is the inherited `renderFpv()`, which requires
`s.pov >= 0 && s.fp` — keys this fork never sends. `#fpv` stayed `display: none` for the whole
replay.

**Is:** the game block adds `on` whenever it has a view to draw. It runs after the inherited
render (the page's frame path calls `MinigridChrome.frame` last), and a frame without `mg.view`
returns before the toggle, so the lobby still shows nothing.

**Evidence:** `tools/ci/renderer_fixture.html` now probes the *shipped page's*
`getComputedStyle(#fpv).display` at 960/640/360 px after driving a frame that carries a view, and
throws if it is `none`. That probe is green in run 33213509695, and the fixture's measured run
count rose from 57 to 74 — `#fpv-name` / `#fpv-cap` are among the runs it can now see, because
they have a real geometry instead of a zero box.

**Not done, and why:** §Legible at 360 px places the inset in the board's *right letterbox
gutter*. The gutters live in `#viewport`, outside `#stage` (`relayout()` sizes `#stage` to the
board), and `#killfeed` owns the bottom-right of the stage. Moving the panel out of `#stage` is
the same design change as N3 and is recorded there.

## N4 — the alias at `.tiny`

`#stage.tiny .plate .mg-alias { display: none }` became a shrink-and-ellipsise rule (7u, bounded
width), so the plate keeps `alias + name + solved + carrying chip` at the embedded width, which is
rule 2 of §Legible at 360 px. The selector test 39 asserts is unchanged.

## N7 — one entry, one counter

`installPlan` and the `directive` record's `dropped` slot now carry `directive.overCap` only;
`repliesRepaired` keeps the validation failures. The record is what playback feeds back into
`installPlan`, so `actionsDropped` still reads identically live and on re-derivation. Neither key
is scored.

## N8 — the whole turn inside `turnBudgetMs`

Each attempt is now given `min(configured deadline, time the turn has left)`, so the
`turnSpacingMs` rate floor comes out of the same budget. Worst case falls from 11.6 s to ≈9.5 s
(+ the whole-second `CURLOPT_TIMEOUT` floor); the healthy path is unchanged — with no sleep,
attempt 1 still gets 6 s and the retry 3 s. Checklist item 5's per-wait bounds were already
satisfied; this restores the note's per-turn arithmetic.

## N11 — the sweep runs in CI

`nim c -r -d:release --path:src tools/tune_baselines.nim --check` is a step in the `test` job.
Run 33213509695: `baseline tuning matches the recorded sweep` (the step took ~2.5 min).

## N12 — the derived page cannot drift from its source

CI has no starter checkout, so `build_broadcast_page.py --check` cannot run there. Test 36 now
asserts `client/replay_broadcast.html` **ends with** `client/minigrid_block.html`, modulo the one
`window.PaintballChrome` → `window.MinigridChrome` rename the deriver applies — the block region's
derivation, verified without a starter. A hand-edit of the derived artifact is now red.

## N13 — the live feed carries the same events

The `plan` / `fallback` / `budget` derivation moved into `replays.pushControlEvents`, called from
both paths: `server.nim`'s `writeChat` (which already fed the same record to the feed-directive
stream) and `applyControlRecord` on playback. One derivation, so live and replay cannot drift.
Event order is unchanged on both sides (`fallback` → `say` → `plan`).

## N16 — caps applied at the sender

`registrationBlob` truncates `prompt` at `MaxPromptRunes` (4000) and `policy` at
`MaxPolicyLabelRunes` (64) with the same `truncateRunes` the server uses, which is where the note
puts them. The server keeps its own truncation on receipt — a seat container is not trusted input.

## N17 — the fixture asserts its own strings

`transcribe` now collects every run it measured, and each width asserts that some run still
carries the whole 140-rune say **and** the whole mission sentence, naming the longest run it did
find when it does not. The fixture also checks its own say is 140 runes before driving anything.

That assertion immediately caught two real defects, both fixed in this round:

1. **The fixture's own say was 132 runes, not 140** (`617e4b9`). The base sentence is 130 runes and
   the builder sliced 138 out of it. The base is now repeated before the slice; nothing was
   shortened. CI run 33212164694 is the failure: `the fixture built a 132-rune say; MaxSayRunes is
   140`.
2. **The say row ran off the frame at 360 px** (`e8f96f1`). The `say` was driven last so it
   survives the four-row feed and could be measured for the first time; the strict-bounds check
   then reported it drawn from x=66 to x=371 in a 360×203 frame (CI run 33212976659). The
   inherited `.feed-row` is `white-space: nowrap`, sized to content — right for a paintball kill
   line, wrong for a 140-rune remark. Model-authored rows (`say`, the `taskstart` mission line,
   the plan line) now carry `.mg-remark` and wrap inside the feed's reserved width. The band was
   widened; no text was shortened, which is what checklist item 15 requires.
   `b19bc08` teaches the fixture to transcribe a wrapping run as a block (wrapped to the
   element's own box width) instead of as one impossible line; `nowrap` runs are unchanged, so a
   label with nowhere to go still reports `outside`.

Final fixture line: `canvas text: 74 drawn, 0 never inside the canvas (0 draws crossed an edge),
0 ellipsized (--strict-text-bounds)`.

## N18 — the xland constants are bounded where configs arrive

`validate()` now carries the bounds `config_schema` already declared (`xlandRules == 3`,
`4 ≤ xlandObjects ≤ 8`), below which `sampleRuleSet` returns an empty seq and `generateXland`
indexes it. Test 33 asserts both raise `ConfigError`. Both shipped variants and the cert fixture
are unaffected (6 / 3).

## Unlisted, fix-forward: `replay_summary.py` was flaky

CI run 33212164694 also failed test 30 on `parsed["gameVersion"] == GameVersion`, which none of my
commits touched. Cause: the header's version was recovered by scanning for ASCII digits after the
game name and stopping at the first non-digit, and the bytes after the version are a timestamp —
whenever its low byte landed in `'0'..'9'` the scan returned `"1"` plus that digit. Roughly one run
in twenty-five, on every replay, in CI **and** in phase 60's definition-of-done recipe. Every
string in the header is length-prefixed (little-endian uint16), so the version is now read by its
prefix. Verified locally against the committed fixture (`tests/replays/gauntlet-seed42.replay` →
`"1"`) and against a synthetic header whose next byte is `'2'`, where the old scan returned `"12"`.

---

## Disputed — no change, with evidence

**N5 — the endcard vocabulary list.** The elements the note lists as "removed"
(`hillchip`, `lives-num`, `lives-label`, `pb-tags`, `squad-pip`, the `ec-heart` glyphs) are
**load-bearing in the shipped design**: `mgRenderPlate`
(`client/replay_broadcast.html:4516-4539`) writes the solved count into `#lives-red`, the carrying
chip into `#hill-red` and the alias into `#tags-red` — the starter's own elements, repurposed and
re-labelled, which is what "the starter's page plus a block" means. Removing them would delete the
readouts they now carry. The shipped test asserts each of the twelve re-mapped strings appears
exactly once and records the divergence in its own docstring
(`tests/test_minigrid_endcard_labels.nim:9-16`). Checklist 14 is not falsified — the reviewer says
so too.

**N6 — `fallback.cause` values.** `throttled` names a provider 429 with no other model candidate
(`decide.nim:231`, `llm.nim` sets `client.throttled`); the note's enum has no member for it.
Folding it into `rate_guard` would conflate it with the *server-side* guard that never made a
request (`decide.nim:119-126`), and folding it into `transport_error` would hide the one cause an
operator most wants to see. `disconnected` is unused because a disconnected seat never reaches the
decision path at all: `server.nim:509-516` marks `deadSeats[0]` and the gauntlet plays out on
`scout` without a turn being taken. The field is a replay chat record, not a `results` key, so
nothing validates it. Checklist item 8 (retry once, fall back, record the fallback) holds either
way — `tests/test_minigrid_driver.nim:120-128` and `tests/test_minigrid_engine.nim:125-163`.

**N9 — `docker_smoke.sh` and `reason == "fault"`.** The build *does* fail on a fault, one step
later and in this repo's own workflow: `.github/workflows/ci.yml:253` asserts
`summary["results"]["reason"] in ("complete", "deadline")` over the replay the smoke just
produced, and exits non-zero otherwise. `docker_smoke.sh` is the shared template with only the
three documented substitutions (the reviewer verified this); adding a repo-local check there would
diverge the shared file to duplicate a gate that already exists. Reviewed run reported
`episode end reason: complete`; the green run 33213509695 reports the same.

**N15 — the reply cap's units.** `llm.nim:187-193` parses from at most `4 × MaxReplyBytes` of the
provider's **envelope** and then caps the extracted text at `MaxReplyBytes` runes. Cutting the
envelope at 4096 bytes, as a literal reading of the note's table would require, would slice a
provider JSON document mid-object and turn every long-but-legal reply into a `parse_error` — the
4× headroom is the envelope, not the content. Everything downstream is rune-safe
(`truncateRunes`, `sanitizeSay` 140, `sanitizeNote` 300), which is what checklist item 9 asks for
and what `tests/test_minigrid_driver.nim:174-185` proves.

**Minor 2 — the clock split.** The starter's clock markup has exactly two text slots inside
`#clock` (`.time#clock-time` and `.caption#clock-caption`, `client/replay_broadcast.html:1257-1263`).
The note's three-way split needs a third element; the shipped mapping puts the big numeral in the
numeral slot and the rest in the caption. Adding an element to the inherited scorebug to satisfy a
prose split is a change to the starter's chrome, which is exactly what checklist 14 discourages.

**Minor 3 — `falling back` before an attempt.** The pre-attempt block
(`decide.nim:166-175`) fires only when no request can be made at all — no credentials, budget
guard, rate guard. The turn genuinely falls back to the scout plan, so the log phrase is accurate
and phase 60's count is right; AGENTS.md's rule ("only a genuine SECOND failure may log `falling
back`; attempt 1 says `will retry`") is about the retry ladder, and that ladder is correct
(`decide.nim:227-236`). Changing the phrase would make a credential-less run invisible to phase
60's grep, which `llm.nim:126-127` deliberately intends.

## NEEDS-DESIGN — no change

**N2 — the eight draw procs.** The note describes a compositor rewrite (`drawRoomBed`,
`drawCells`, `drawObjects`, `drawAgent`, `drawFog`, `drawAgentView`, `drawMissionRibbon`,
`drawTaskPips`); the shipped board is baked server-side into sprite definitions and retained-mode
placements in `src/minigrid/global.nim`, leaving `client/broadcast_core.js` one rename away from
the starter's. That is *more* conservative than the note and is what checklist 14's provenance
clause wants. Rewriting the compositor to match the note's prose would delete a working,
starter-identical file and re-open every wire and hash question in it. If the note is to be
followed literally here, that is a design decision, not a fix.

**N3 — the gutters.** §Legible at 360 px puts the mission ribbon and pips in the left letterbox
gutter and the 7×7 inset in the right. Both gutters are in `#viewport`, **outside** `#stage`
(`relayout()` sets `stage.style.width = boardW`), so honouring it means re-hosting three overlays
on `#viewport`, deciding their behaviour at widths where the stage fills the viewport and no
gutter exists, and re-deriving their anchors from `--topband`/`--band` on a different box. The
transport-band half of the note's claim already holds and is asserted
(`tests/test_minigrid_viewer.nim:195-197`), and item 14(b) is satisfied. I did not attempt the
re-hosting: it cannot be verified in this sandbox (no browser), and the fixture only measures text
geometry, not overlap.

**N14 — `keycorridor`'s dividing column.** The wall is at `x = 7`, the note says `x = 6`; every
other property of the generator (rows, door count, the locked-red/closed-grey split, key and ball
placement, start pose) matches. Moving the column changes every generated layout for that family,
which changes every per-tick `gameHash`, which per AGENTS.md requires a `GameVersion` bump **and**
re-recorded `tests/replays/*.replay` fixtures. There is no Nim toolchain in this sandbox, so the
fixtures cannot be re-recorded here, and shipping the layout change without them would make test
32 and the re-derivation tests red. The divergence is cosmetic (the corridor is the region
`x ∈ 1…6` rather than the single column `x = 6`) and affects no checklist item.

---

## NOTED (not fixed)

- `tools/build_broadcast_page.py` is committed 0644. It is always invoked as `python3 tools/...`,
  so nothing breaks; the `coworld build` hook exec-bit rule applies to
  `tools/build_replay_viewer.sh`, which is 100755.
- `repliesRepaired` is incremented on the live path only (`decide.nim:277`); the `directive`
  record carries no field for it, so a re-derived episode reports 0 where the live one reported
  *n*. Not raised in this review, not scored, and not part of the hash — but it is the same class
  of live/replay asymmetry as N13 and would need a record field to fix.
- `viewer-smoke` artifact upload only collects the repo-root `viewer-smoke.{png,json}`, so the
  **fixture's** artifacts (`dist/fixture/…`) are never uploaded. When the fixture step fails, its
  JSON is only visible in the step log.
