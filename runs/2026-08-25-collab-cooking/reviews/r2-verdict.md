blocking: 0

# r2 verdict — collab-cooking
Head: `f82126bf5da18509ec7dd8553148adceffdbac48` (main)   Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

CI at head: run **32823608970**, conclusion **success**, all three jobs green — `test`
(97726806074), `docker-smoke` (97726805937), `wasm-viewer` (97727102090) — read with
`gh run view`, not accepted from anyone's report. The r2 review was written against `a5ec2c8`;
the fixer has since pushed ten commits (`a5ec2c8..f82126b`, 13 files, +909/−47, and
`a5ec2c8` is an ancestor of head — verified with `git merge-base --is-ancestor`). Every
disposition below is my own verification at `f82126b`.

---

## Standing blocking findings

None. All three of the review's blocking findings were true at `a5ec2c8` and are **fixed at
head** (fixed, not refuted); one non-blocking finding is refuted outright; my independent
checklist pass found no new falsification.

## Reviewer findings, disposition at head

### R2-O1 — say band clips a full-cap remark → FIXED at `e091b9c`
- Verified at head: `client/parts/game.css:100-118` — `#saybar .say-chip` no longer carries
  `max-height` or `overflow: hidden`; it is `word-break: break-all; overflow-wrap: anywhere`
  with hidden gauge chips (`.say-gauge`, `game.css:124-130`). `client/parts/game.js:108-170` —
  `ccSayBand()` lays out `SAY_RUNES = 120` copies of the widest runes (`'W'`, `\u4e00`, an
  emoji) plus the 8-rune alias prefix in the chip's own font at the chip's own measured width,
  and writes the tallest gauge to `#saybar`'s inline `min-height` on every `relayout()` pass
  (`game.js:444`, before `--topband` is computed at `:450-452`). The band is reserved speaking
  or silent; under 320 px of viewport height it is dropped entirely
  (`game.css:223-225`), matching the feed's own under-640 rule. Static pin:
  `tests/test_viewer_contract.py:147-168` fails on any reappearance of
  `max-height`/`overflow: hidden` on the chip. Dynamic pin: the new CI step (below) measured
  `scrollHeight == clientHeight` on all four full-cap chips at 13 viewports.
- Checklist item: 15 (DOM branch — reserved band sized from the server's cap, measured in the
  font). Satisfied at head.

### R2-O2 — feed `say` line inherits ctf's `nowrap` and runs off `#stage` → FIXED at `5aea159`
- Verified at head: `client/parts/game.css:144-163` — `#feed .feed-row { display: block;
  white-space: normal; overflow-wrap: anywhere; max-width: 100%; }`, an override **in the
  appended game block**; ctf's own `.feed-row` rule above the banner is untouched (the page
  still regenerates byte-identically from the starter — I ran
  `python3 tools/build_broadcast_page.py /workspace/starters/coworld-ctf`; `git diff` empty).
  `game.js:228-248` — `renderFeed` drops the oldest row while the wrapped column would grow
  past the top of the canvas. Pinned by
  `test_the_feed_rows_wrap_inside_their_column_instead_of_running_off_the_stage`
  (`test_viewer_contract.py:170-186`) and measured by the CI fixture.
- Checklist item: 15. Satisfied at head.

### R2-O3 — no gate renders model-authored DOM text → FIXED at `4d00033`
- Verified at head: `tools/ci/dom_text_smoke.mjs` (399 lines, mode 100755) loads the **real**
  `client/replay_broadcast.html` spliced exactly as the bundle splices it (real
  `chrome_common.js`, real `data/font.ttf`), stubs only the wasm core, and drives the page's
  own `onText` with a frame of four full-cap says plus six full-cap feed lines in four hostile
  shapes (Latin sentence, unbroken `W` run, CJK, ragged words), at 13 viewports including
  360×640 and the 360×223 letterboxed iframe. Assertions are non-vacuous: it reads the cap
  from **both** enforcing sources (`SAY_RUNES` in `plans.py`, `SayRunes` in the Nim module) and
  fails if they disagree (`dom_text_smoke.mjs:63-73`); it asserts every model-text node
  unclipped (`scrollHeight/Width` vs `client*`, `:283-292`), inside `#stage` (`:294-299`), the
  strings still **full-length** (`:305-315` — a quietly shortened remark fails), the band the
  same height quiet vs speaking (`:325-334`), 4 visible chips, and ≥ 4 viewports rendering all
  four full-cap strings or the run fails as "covered nothing" (`:378-383`). Wired as its own
  `ci.yml` step `Load a full-cap remark in a real browser (DOM text bands)` (`ci.yml:272-283`),
  which ran and passed at head: `dom text smoke OK: every 120-rune remark fits its band at 13
  viewports` (run 32823608970, job 97727102090). `test_viewer_contract.py:199-218` pins that
  `ci.yml` keeps running it. `viewer_smoke.mjs` remains the verbatim template (diff against
  `templates/tools/ci/viewer_smoke.mjs` empty — I ran it).
- Checklist item: 15, final bullet. Satisfied at head.

### Non-blocking findings, verified at head
- **R2-O4** (feed cap swallowed the alias prefix) → FIXED at `2a00b36` + `f82126b`:
  `plans.py:32` `FEED_RUNES = SAY_RUNES + ALIAS_CAP + 2` (=130); `live_episode.py:810`
  truncates the alias separately; Nim `FeedRunes = SayRunes + AliasRunes + 2`
  (`collab_cooking_replay.nim:57`) with `truncRunes` now defined at `:657`, **before** its
  first use in `absorb` at `:707` (the `f82126b` fix-forward for the Nim compile error that
  made run 32823219320 red; head run is green). Cross-pinned by
  `test_the_viewer_caps_a_feed_line_the_way_the_server_does`.
- **R2-O5** (under 640 px the chip is the only surface) → resolved by R2-O1; the fixture
  passes at 360×640 with the full remark rendered. The `#feed` hide under 640 px is what item
  11 asks for. Advisory, closed.
- **R2-O6** (chrome-JSON cap documented 4 KB, enforced 16 KB) → FIXED at `17d48a5`:
  `ChromeCap = 16000` with the guard `if result.len > ChromeCap`
  (`collab_cooking_replay.nim:51,944`) and an honest comment. Advisory anyway (not a checklist
  item; `broadcast_core` reads label length as u16, so 16 KB transports).
- **R2-O7** (jam beat placed by kitchen-wide count) → FIXED at `1f71d48`:
  `collab_cooking_replay.nim:622-628` counts blocked events **at the busiest tile only** and
  places the beat where that doorway passes half its own total. Advisory anyway; the `jam`
  kind has CSS (`game.css:246`) and a label, so item 14(d) holds regardless.
- **R2-O8** (count-based serve/expire attribution) → FIXED at `aeb49d4`:
  `replay.py:264-266` splits the departed tickets **once** into `served_tickets` /
  `expired_tickets`; the serve loop pops recipes from that same list (`:298-313`). Pinned by
  `test_two_serves_in_one_tick_get_the_two_recipes_that_left_the_board`
  (`test_replay_parse.py:241-279`), which covers both the two-serve and the serve-plus-expiry
  tick. Latent-only at the old head, now closed.
- **R2-O9** (dead starter CSS above the banner) → stands as **advisory**, correctly unfixed:
  deleting rules from ctf's inherited `<style>` would break the byte-level regeneration that
  item 14 demands. The one live consequence (`.feed-row` reuse) was R2-O2 and is fixed in the
  appended block.
- **R2-O10** (player-side fallback hard-codes `brigade`) → stands as **advisory**
  (`player.py:162`). Falsifies no checklist item: item 8's retry/fallback/recording all hold;
  the divergence is reachable only under a non-default `fallback_scripted`, which no shipped
  variant or fixture sets (verified in the manifest). NEEDS-DESIGN disposition is honest.
- **R2-O11** (test name overstates) → FIXED at `59349d6`: renamed to
  `test_every_baseline_name_is_selectable_and_resolves_a_role` with a docstring; diff shows
  assertions unchanged (+6/−1, the name line).

## Refuted

### R2-O12 — "`__pycache__/` and `.pytest_cache/` are committed (`git ls-files`)" → REFUTED
- Evidence: `git ls-tree -r --name-only a5ec2c8 | grep -cE '__pycache__|pytest_cache'` → **0**,
  and the same at `f82126b` → **0** (I ran both). `git ls-files` at head lists 84 paths, none
  under either directory. `.gitignore:1` has ignored `__pycache__/` since the initial commit.
  The directories exist only in the working tree (any tree that has run pytest has them),
  which is what the reviewer saw. Wrong at the sha it was written against, not merely fixed
  since — refuted. The fixer's `feb1f8a` (adding `.pytest_cache/` to `.gitignore`) closes the
  one real gap behind the misreading without any tracked file existing to remove.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 32823608970 `success` on main at `f82126b` (all three jobs; cited above). `git log -p -- tests/` over the whole run read hunk by hunk: the suite landed once (`211be3a`) and every later change is a net addition except three sanctioned re-pins — heat *total* equality replaced by **tile-for-tile** dict equality plus a non-vacuity assert (`fef552a`, stronger); the wrong-shape `MANIFEST["replay_viewer"]` pin replaced by `MANIFEST["game"]["replay_viewer"]` **plus** `"replay_viewer" not in MANIFEST` (`f4c74bd`/`fe30405`, stronger, after a finding corrected a wrong pin); a test rename with assertions unchanged (`59349d6`). No `skip`/`xfail` added, no tolerance widened, no test file removed. The one pre-existing `pytest.skip` (`test_viewer_contract.py:272`) is a starter-mount guard; I verified the guarded property directly (chrome byte-identity, item 14). Note: run 32823219320 (`feb1f8a`) was red on a Nim compile error, fixed forward at `f82126b`; head is green. |
| 2 replay re-derivation | PASS | `tests/test_rederivation.py:66-131` — recorded actions fed through a **fresh** `Simulator` built from the replay's own config/seed; frame-by-frame comparison of `t`, `c`, `st` including the omit-when-unchanged rule, `sc`, `ev` in order, plus cumulative heat (`:144-147`); two tamper tests prove it load-bearing (`:150-170`); non-vacuity pinned (`:134-141`). Green in the head test job. The viewer draws the recorded arrays (design §Viewer/Pipeline pin: recorded, not derived; no sim in wasm — `collab_cooking_replay.nim:1-21`), and this test proves the recording identical to the re-derivation. |
| 3 static viewer | PASS | `coworld_manifest_template.json:15-17` `game.replay_viewer = {"bundle":"static-replay-viewer"}` (loader-validated in CI by `tools/ci/check_manifest_loads.py` against pinned `coworld==0.1.42`); `tools/build_replay_viewer.sh` mode 100755, wired as the `coworld build` hook and asserted executable in `ci.yml:153-164`; the worker's only network call is the replay fetch; no `/client/replay`, `WS /replay`, `create_replay_app`, `COGAME_REPLAY_SERVER` in `server.py` routes (`server.py:196-267`; `test_manifest.py:124-140` asserts absence). |
| 4 both name spaces | PASS | Aliases by seeded permutation (`live_episode.py:202-211`); wire `observation`/`player_config` carry alias only (`:888-916`); prompts, plans, radio, `handoff`/`yield_to` alias-only; player sends `policy_name: alias` (`player.py:179`). Real names only in `seats[].name`, `results.names`, `/global`, and the viewer (`game.js:203` `.plate-policy`, endcard `cc-name`). Head CI scorebug renders both: `"Cog-B Cog One …"`. |
| 5 degrade-never-hang | PASS | Roster wait bounded at `process_start + 120 s` AND the deadline guard (`live_episode.py:453-459`); registration grace 5 s (`:461-466`); per-tick action wait `asyncio.wait_for(…, 0.30)` (`:474-486`); pause branch checks the guard (`:415-423`); guard = 0.6 × 1200 = 720 s from `PROCESS_START` (`server.py:47`), checked every tick (`:444`); LLM `urlopen(timeout=12)` (`llm.py:180`), batch deadline + non-blocking `poll` (`llm.py:225-249`); artifact writes `timeout=30` (`server.py:59,74`); `/global` loops bounded by `done`/`exited` (`server.py:224-234`); player dial bounded 60 s (`player.py:136-156`), exits 0 on any socket error (`:191-197`). Worst case ≈ 185–450 s play + 120 s connect + 20 s grace < 720 s; cert fixture wall clock pinned < 50 s by a passing test (`test_episode.py:169`); deadline and paused-deadline paths both tested. |
| 6 num_agents | PASS | Parsed the committed manifest: `num_agents: 4` in all **eight** variants, in `certification.game_config`, `config_schema {minimum:4, maximum:4}`, `len(certification.players)=4`, `len(certification.game_config.players)=4`. `docker_smoke.sh:110-151` enforces all four invariants with `SEAT-COUNT FAIL:` before any container starts; `SMOKE_SEATS: "4"` (`ci.yml:109`) cross-checked at `docker_smoke.sh:146-151`. Grep of the head docker-smoke log for `SEAT-COUNT FAIL`: **0 hits**; log carries `game=collab_cooking seats=4` and `smoke OK: seats=4 … reason=complete`. |
| 7 scripted baseline full episodes | PASS | `test_episode.py::test_a_complete_episode_writes_both_artifacts` — four scripted seats to natural end, `reason == "complete"`, dishes recomputed from `serve` events; `test_baselines.py:58-` — 4 baselines × 8 kitchens × 600 ticks, every action in `action_names`, one per seat per tick, `request_id == step-<t>`, talk ≤ 140 runes valid UTF-8, no seat parked > 60 ticks. Parameters are the starter's shipped brain, deliberately frozen (design §Out of scope 8); validated in fact by the head container smoke: `dishes` served, `cross_play: true`, all four policies seated, every player exited 0. |
| 8 LLM reply handling | PASS | Balanced-brace extraction tolerant of prose (`plans.py:123-155`); retry **exactly once** with the hint (`llm.py:296-329`, `for attempt in (0, 1)`); fallback recorded as a `fallback` event + `results.fallbacks` (`live_episode.py:830-839`, `:617-627`); disabled path makes zero network calls (`llm.py:197-213,274`). Pinned by `tests/test_llm.py` (one-retry, successful-retry-used, transport exception contained, rate budget, zero-credential path). |
| 9 rune-safe truncation | PASS | `truncate_runes` code-point slice (`plans.py:57-66`) applied to say (120), note (200), prompt (1200), policy names (48), talk (140), feed (130), errors (240); one `encode("utf-8")` with `ensure_ascii=False` (`replay.py:521-523`); Nim side truncates on `unicode.runes` (`collab_cooking_replay.nim:657-666`). `test_replay_parse.py::test_a_capped_multibyte_say_survives_as_valid_utf8` asserts strict decode at the cap; `test_note_is_absent_from_the_replay_entirely` alongside. |
| 10 manifest | PASS | `game.docs.readme` inline `{"type":"text","value":…}` byte-identical to `README.md` (test + my parse); four `pages[]` each `{id,title,content:{type:"text",value}}`; `game.protocols` carries **both** `player` and `global` as `{type,value}` objects (`coworld_manifest_template.json:448-456`; `test_manifest.py:104-121`); pinned loader accepts the template in the head test job. |
| 11 legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` (`game.css:184-193`); `@media (max-width: 640px)` hides `.plate-policy`/`.plate-job`/`#feed` (`game.css:214-218`); asserted by `test_plate_css_survives_the_360px_featured_match_iframe`; the dom-text fixture passes at 360×640 and 360×223. |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build the Coworld manifest (`:153`) → Certify locally (`:167`) → Upload the policies (`:206`, pinned BEFORE upload-coworld) → Upload the Coworld (`:304`) → Put the Coworld secret (`:342`, reads `game.name` from the manifest, asserts the URI namespace, `$SLUG` never reaches `secret put`). Certify runs on the manifest built in the same job (fresh binary). Three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 2 × `PLAYER_PROMPT` + 2 × `PLAYER_SCRIPTED` with champion #2 carrying `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep over the five named files exits clean — I ran it. |
| 13 viewer executes | PASS | Run 32823608970 `wasm-viewer` green **including** `Load the bundle in a real browser` (step list read from `gh run view --job=97727102090`): `{"loaded":true,"ms":336,…}`, 10 s soak advancing (`1/480 → 193/480 → 241/480`), three distinct scrub clocks, `canvas text: 0 drawn … (--strict-text-bounds)`. `needs: docker-smoke` (`ci.yml:140`); **no** `continue-on-error` in any workflow (grep, 0 hits). `data-replay-loaded` set in the shell's `loaded` branch with the bridge `ready` inside it; `data-replay-error` set in `showFailure` (`static_replay.js:29,152-158`). Link flags and bootstrap from the SAME starter: `config.nims` diff vs ctf = symbol rename + output name only, **no MODULARIZE/EXPORT_NAME on either side**; worker bootstraps `Module.onRuntimeInitialized` against `Module._cc_*` — the matched non-MODULARIZE pair; cross-pinned by `test_the_wasm_entry_the_link_flags_and_the_js_name_the_same_symbols`. |
| 14 chrome is the starter's | PASS | `chrome_common.js` and `broadcast_core.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/` (diff empty — I ran it). The committed page **regenerates byte-identically** from the starter via the committed generator (I ran it at head, post-R2-O2). CSS above the banner is ctf's head verbatim (unified diff: one trailing newline). Transport rules in the page: (a) `relayout()` writes `--hudscale`/`--band` (and `--sb`/`--dt`/`--topband`) on `document.documentElement` only (`game.js:423,438,448-453`); (b) nothing `position: fixed`; `#feed` rides `bottom: calc(var(--band,0px) + 8*var(--u))` (`game.css:135`), ticker/say band sit above the board in the reserved top band; (c) `#endcard` keeps `bottom: var(--band, 0px)` (page `:1047`), shown with `#endcard.on` (`:1058`, `game.js:310`), and every seek — scrub click, beat button, restart/back/fwd, keyboard `,` — routes through `ccSeek`, which removes `.on` first (`game.js:60-65`); (d) beats are labelled `<button>`s seeking to their tick (`game.js:256-268`) with CSS for all six emitted kinds — serve/burn/expire/jam/plan/end (`game.css:243-248`), the exact set the Nim module emits (cross-checked by test). Zoom panel: `#viewpanel`/`#zoombar`/`#minimap` markup, ids and `attachMinimap` wiring all removed for this fixed 360×216 board. |
| 15 every drawn string fits | PASS | **Canvas half:** the "canvas draws no text" pin verified from code — no `fillText`/`strokeText` in `client/parts/` or the shell JS (grep, 0 hits); board glyphs are pixie-baked sprite pixels in the Nim module; `broadcast_core.js` is the starter's byte-identical compositor. Therefore `canvas text: 0 drawn` with `--strict-text-bounds` ON (`ci.yml:247`) is the expected reading, and `never_inside = 0` holds trivially. **DOM half:** `tools/ci/dom_text_smoke.mjs` is the dedicated fixture item 15 demands — real page/chrome/font, full-cap multi-script strings on every seat plus six feed lines, non-vacuous (whole-string assertion, 4-chip assertion, ≥ 4-viewport coverage floor, cap read from both enforcing sources), running as its own red-capable `ci.yml` step; green at head (`dom text smoke OK … 13 viewports`), and the fixer demonstrated it red against the pre-fix client (108 failures). Say band reserved from the cap (`ccSayBand`), feed wraps and prunes, remark never ellipsized/shortened. |
| addendum: one parallel batch | PASS | `LlmPlanner.start_turn` submits every prompt seat's future before returning (`llm.py:288-293`); the tick loop only polls (`live_episode.py:438-439`, `PlanBatch.poll` never blocks); 4-way concurrency proven by a `threading.Barrier` in `tests/test_llm.py::test_one_parallel_batch_issues_every_seat_at_once`. No sequential path exists. |

---

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| R2-O1 | fixed `e091b9c`, band measured from the cap | CSS clip gone, gauge measurement in `ccSayBand`, reserved on every relayout, static test + CI fixture green at 13 viewports | yes |
| R2-O2 | fixed `5aea159`, override in the appended block | `#feed .feed-row` wraps; inherited rule untouched; page regenerates byte-identically; prune-to-fit in `renderFeed`; test present | yes |
| R2-O3 | fixed `4d00033`, fixture committed + in ci.yml | 399-line fixture, non-vacuous assertions, own CI step, ran green in 32823608970; `viewer_smoke.mjs` still verbatim template | yes |
| R2-O4 | fixed `2a00b36` + `f82126b` fix-forward | `FEED_RUNES=130` both sides; alias truncated separately; `truncRunes` defined before `absorb`; red run 32823219320 explained honestly | yes |
| R2-O5 | no change; resolved by R2-O1 | 360-wide viewports pass the fixture; the 640 px feed hide is item 11's own ask | yes |
| R2-O6 | fixed `17d48a5`, constant = the firing number | `ChromeCap = 16000`, guard `> ChromeCap`, honest comment | yes |
| R2-O7 | fixed `1f71d48`, count at the doorway's tile | `collab_cooking_replay.nim:622-628` filters on `bx`/`by` | yes |
| R2-O8 | fixed `aeb49d4`, one split, shared list | `replay.py:264-266,298-313`; new unit test covers both mixed-tick cases | yes |
| R2-O9 | no change, provenance forbids it | correct: deleting inherited head CSS breaks the byte-level regeneration item 14 requires | yes |
| R2-O10 | NEEDS-DESIGN, unreachable as shipped | `player.py:162`; no shipped config sets `fallback_scripted`; wire frame lacks the field; advisory | yes |
| R2-O11 | fixed `59349d6`, rename only | +6/−1 diff, assertions unchanged | yes |
| R2-O12 | DISPUTED + `.gitignore` guard | reviewer wrong: 0 tracked `__pycache__`/`.pytest_cache` paths at `a5ec2c8` **and** at head (`git ls-tree`, ran both) — refuted, and the guard commit is a sensible extra | yes |

## Non-blocking observations
- The r1 fix commits appear **twice** in history (`f4c74bd..a5ec2c8` and `fe30405..1dda007`) —
  the push tool re-minted them, as the fixer discloses. `a5ec2c8` is an ancestor of head,
  nothing was force-pushed, and `git diff a5ec2c8..f82126b` is exactly the r2 changes.
  Cosmetic history noise only.
- The viewer smoke's 0 % scrub probe still reads the pre-scrub clock (`0%="TICK 241 …"`);
  the harness's three-distinct-clocks criterion held. Template harness quirk, carried from r1.
- `word-break: break-all` on say chips can break English words mid-word; it is what makes the
  gauge an upper bound, and the trade is documented in the CSS. The r2 review's open question
  about ~4.25 px chip type at 360 px stands unresolved as a taste question — the fixture proves
  the text unclipped and full-length there, which is what item 15 gates; type size at the
  starter's own `--hudscale` floor is not a checklist item.
- Run 32823219320 (`feb1f8a`) was red on the Nim compile error `f82126b` fixed. Head is green;
  no gap in the "CI green on main at the reviewed sha" requirement, which binds at the sha.

BLOCKING: 0
