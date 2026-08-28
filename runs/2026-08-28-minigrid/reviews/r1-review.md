# r1 review — minigrid

Repo: `Metta-AI/cogame-minigrid` @ `d8f9e7c2509111b05c68d29498b715587e0264ed` (clone read at `/tmp/cogame-minigrid`)
Range: `5c2e70d..d8f9e7c` (7 commits; the implementation is `605307a` plus four viewer fixes)
Starter for provenance: `/workspace/starters/coworld-ctf` (read-only mount)
Design note: `/workspace/coworld-builder/runs/2026-08-28-minigrid/design.md`
Files read: 58 (all of `src/minigrid/`, `src/minigrid.nim`, `src/minigrid_player.nim`, `replay-viewer/*`,
`client/*`, all 8 `tests/*.nim`, all 3 workflows, `tools/ci/*`, `tools/build_replay_viewer.sh`, the
manifest, `compose.yaml`, `Dockerfile`), plus the CI run log and the `viewer-smoke` artifact for
run 33209437659.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15)

Method note: everything below is **observed** (read at the reviewed sha) unless labelled *inferred*
or *untested*. Three claims were checked by executing something: the CI conclusion and step list via
`gh run view 33209437659`, the `viewer-smoke.json` / `viewer-smoke.png` artifact via
`gh run download`, and the manifest against the **pinned** `coworld==0.1.43` CLI installed in this
sandbox (B1).

---

## Blocking

### B1 — `coworld_manifest_template.json` cannot be loaded by the `coworld` CLI the release workflow pins: `coworld build` raises `KeyError: 'image'`

- Where: `coworld_manifest_template.json:15-28` (`game.image`, `game.source_url` sit as siblings of
  `game.runnable`, which itself has no `image`), `coworld_manifest_template.json:485`
  (`"type": "policy"` on the one declared player), against
  `.github/workflows/coworld-release.yml:80` (`COWORLD_PKG: "coworld[auth]==0.1.43"`) and
  `:159-171` (`coworld build --template coworld_manifest_template.json`).
- Observed: the template puts the image placeholder at `game.image`:

  ```json
  "game": {
    "name": "minigrid",                                   // :12
    "image": "{{MINIGRID_IMAGE}}",                        // :15
    "source_url": "https://github.com/Metta-AI/cogame-minigrid",  // :16
    "replay_viewer": {"bundle": "static-replay-viewer"},  // :17-19
    "runnable": {"type": "game", "run": ["/bin/minigrid"], "env": {…}}   // :20-28  — no "image"
  ```

  The starter puts it *inside* `runnable`
  (`/workspace/starters/coworld-ctf/coworld_manifest_paintbot.json` → `game.runnable.image =
  "{{GAME_IMAGE}}"`, `game.runnable.source_url`), and `coworld`'s own loader requires that shape:

  ```python
  # coworld/bundle.py:118-130  (_load_template_manifest)
  runnables: list[dict[str, Any]] = [game["runnable"]]
  for section in ROLE_SECTIONS: …
  for runnable in runnables:
      image = runnable["image"]            # <- KeyError('image')
  ```

  Reproduced in this sandbox against the exact pinned version:

  ```
  $ pip install coworld==0.1.43
  $ python -c "_load_template_manifest(template, '0.1.0', {'{{MINIGRID_IMAGE}}': 'coworld-minigrid:latest'})"
  KeyError: 'image'   (coworld/bundle.py:128)
  ```

  Moving `game.image` into `game.runnable` in memory advances past the `KeyError` and exposes two
  more pydantic errors from the same call:

  ```
  game.source_url   Extra inputs are not permitted            (must be game.runnable.source_url)
  player.0.type     Input should be 'player', 'commissioner', 'grader', 'diagnoser' or 'optimizer'
                                                              (the template says "policy")
  ```

  With all three corrected the template loads clean, which also confirms the rest of the manifest —
  `game.docs` with `type: "uri"`, `game.protocols`, `config_schema`, `results_schema`, both variants
  and the certification fixture — is accepted as written.
- Checklist item: 10, **"Manifest validates."** *(category: manifest)*
- Why blocking: `coworld build` is the first step of `coworld-release.yml` and the step that invokes
  the static-viewer hook (`coworld/bundle.py:22` `REPLAY_VIEWER_BUILD_HOOK =
  Path("tools/build_replay_viewer.sh")`, called from `_build_replay_viewer_bundle` **after**
  `_load_template_manifest` returns). The build aborts before the hook runs, so no manifest and no
  static bundle are produced and certify/upload never start. Nothing in `ci.yml` catches it: the
  repo's own item-34 test is a Nim shape-check (`tests/test_minigrid_manifest.nim:123-138`) whose
  docstring claims *"CI runs `coworld`'s `validate_upload_manifest` / `_load_template_manifest` for
  real"* — no such step exists in `.github/workflows/ci.yml` (see N10).
- Caveat for the judge, stated plainly: item 10's two **enumerated** sub-clauses (the `game.docs`
  shape, `game.protocols` carrying both `player` and `global`) **do** hold — verified at
  `coworld_manifest_template.json:29-60` and by the clean load above. I am filing this against the
  item's title, "Manifest validates", because the manifest does not. A judge who reads item 10 as
  *only* its two sub-clauses will dismiss this to non-blocking; the underlying defect is the same
  either way and is reproducible with the commands above.

No other blocking finding. Items 1–9 and 11–15 were each traced and are recorded below.

---

## Non-blocking

### N1 — the agent-view 7×7 inset is computed and drawn every frame into a panel that is never made visible

- Where: `client/replay_broadcast.html:526-547` (`#fpv { … display: none; }` / `#fpv.on { display:
  block; }`), `:2275-2277` (`function renderFpv(s) { var show = s.pov >= 0 && s.fp && s.fp.cols;
  fpvEl.classList.toggle('on', !!show); }` — the only `classList` toggle of `on` for `#fpv` in the
  page), `src/minigrid/broadcast.nim:262` (`"pov": povSlot`), `src/minigrid/server.nim:398-399` and
  `src/minigrid/replay_runtime.nim:73-76` (both pass `povSlot = -1`), and no `"fp"` key is emitted
  anywhere in `src/` (grep over `src/`, `client/` returns only the starter's three consumers at
  `client/replay_broadcast.html:1832, 2276, 2281`).
- Observed: `mgRenderAgentView` (`client/replay_broadcast.html:4441-4480`) sizes and paints
  `#fpv-canvas` and sets `#fpv-name` to `ALPHA · FACING <DIR>` on every frame
  (`mgFrame`, `:4693`), and the game block contains **no** `classList` call at all
  (grep of the block region `:4091-4746`). Since `pov` is always `-1` and `fp` is never sent,
  `renderFpv` computes `show = false` on every frame and `#fpv` keeps `display: none`.
- What the note says: §Readouts item 3 — *"The agent's 7 × 7 window, inset (the idea's ask) — the
  repurposed `#fpv` panel, bottom-right in the board's letterbox gutter, drawing exactly the `view`
  array the seat receives"* (design.md:1471-1474), and §Legible at 360 px rule 5
  (design.md:1555-1558). The source idea's replay plan names it explicitly: *"agent's 7×7 window
  inset"* (design.md:63).
- Status: *inferred* from the CSS and the single toggle site — I cannot run a browser here. The CI
  screenshot (`viewer-smoke.png`, run 33209437659) was taken at the 100 % seek with the endcard up,
  which covers the board region, so it neither confirms nor refutes. `tests/test_minigrid_viewer.nim:214-215`
  asserts only that the ids are **present**, not that the panel is shown, so the suite cannot catch
  this.
- Not on the checklist: item 14's transport rules and item 15's text-bounds rules do not cover panel
  visibility, so this is advisory by the checklist's own definition.

### N2 — the eight new draw procs §Viewer names do not exist; `broadcast_core.js` is the starter's file plus a comment and one rename

- Where: `client/broadcast_core.js:2-11` (an added 10-line comment) and `:59`
  (`window.CTF_WIRE` → `window.MINIGRID_WIRE`). `diff` against
  `/workspace/starters/coworld-ctf/client/broadcast_core.js` is exactly 1 removed line and 11 added
  lines.
- Observed: `drawRoomBed`, `drawCells`, `drawObjects`, `drawAgent`, `drawFog`, `drawAgentView`,
  `drawMissionRibbon`, `drawTaskPips` appear in neither `client/broadcast_core.js` nor
  `client/replay_broadcast.html` (grep). The board is instead baked server-side into sprite
  definitions and retained-mode placements in `src/minigrid/global.nim` (fog sprites at `:62-63,
  346-347, 484`), which the file's own new comment states.
- What the note says: design.md:1367-1372 — *"Deleted: every ctf-specific draw call … Added:
  `drawRoomBed`, `drawCells`, `drawObjects`, `drawAgent`, `drawFog`, `drawAgentView`,
  `drawMissionRibbon`, `drawTaskPips`."* The shipped approach is *more* conservative than the note
  (the compositor is nearer the starter, not further), so checklist 14's provenance requirement is
  not weakened; the note is simply describing a design that was not built.

### N3 — the mission ribbon and task pips are children of `#stage`, so they overlay the board rather than living in the left letterbox gutter

- Where: `client/replay_broadcast.html:4380-4392` (`mgEnsureRibbon`: `var host = mgEl('stage'); …
  host.appendChild(ribbon)`), `:4395-…` (`mgEnsurePips`, same host), CSS at `:4146-4155`
  (`#mg-ribbon { position: absolute; left: calc(8 * var(--u)); top: calc(var(--topband, 0px) + 8 *
  var(--u)); … pointer-events: none }`) and `:4174-4181` (`#mg-pips`, same anchoring).
- Observed: `relayout()` sets `stage.style.width = boardW` (`:4050`), i.e. `#stage` **is** the board
  plus the two bands; the gutters are outside it, in `#viewport`. An element appended to `#stage` and
  anchored `left: 8u; top: --topband + 8u` therefore sits over the board's top-left corner. The CI
  screenshot shows exactly that: `go to the blue key` and the five pips drawn over the board.
- What the note says: design.md:1538-1541 — *"the mission ribbon and the task pips live in the left
  gutter, the 7 × 7 agent-view inset in the right, so neither ever overlaps the board and neither
  ever enters the transport band."* The transport-band half of that claim **does** hold (both are
  anchored downward from `--topband`; `tests/test_minigrid_viewer.nim:195-197` asserts
  `bottom: var(--band` and `position: fixed` are absent from the block), which is what checklist 14(b)
  asks for.

### N4 — under `.tiny` the plate hides the in-game alias, which §Legible at 360 px says it keeps

- Where: `client/replay_broadcast.html:4296` (`#stage.tiny .plate .mg-alias { display: none; }`),
  written by `mgRenderPlate` at `:4499-4505` (`tags.className = 'mg-alias'; … 'ALPHA · score N'`).
- Observed: at `boardW <= 620` (`:4058`) the plate keeps the real policy name (`.plate-name`, fed by
  `chrome_common.js:145-158` `teamName` → the roster's `policy`) and the carrying chip, and drops
  `ALPHA · score …`.
- What the note says: design.md:1547-1548 rule 2 — *"Under `.tiny`, the single plate keeps only
  `alias + name + solved + carrying chip`"*. Checklist item 4 is still satisfied at every width
  (the alias reaches the agent in `observationJson`, the real name reaches the spectator on the
  plate); only the note's `.tiny` composition differs.

### N5 — the endcard forbidden-vocabulary list is 16 tag-delimited strings, not the note's word list, and several elements the note lists as removed survive

- Where: `tests/test_minigrid_endcard_labels.nim:23-30` (the `Forbidden` array) and `:45-47`
  (`InheritedSelectors = ["hillchip", "lives-num", "lives-line", "pb-lbl"]`, with a docstring at
  `:9-16` recording the divergence deliberately).
- Observed in `client/replay_broadcast.html`: `ec-heart` ×8 (`:994-1006`), `hillchip` ×2,
  `lives-label` ×1, `squad-pip` ×13 (`:300-330` region), `pb-tags` ×1. The visible *text* is
  re-mapped and all twelve re-mapped strings are asserted present exactly once (`:32-44`).
- What the note says: design.md:1386-1390 lists `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`,
  `.lives-label`, `.squad-pip`, `.pb-tags`, `.squad` and the `.ec-heart` glyphs among *"Elements
  removed (exactly these …)"*, and design.md:1427-1431 specifies a word-level grep for `Lives`,
  `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`, `hill`, `POV`, `EYES`, `spray`,
  `grenade`, `med kit`, `kill`, `team`. The shipped test is narrower by construction. Keeping extra
  starter CSS is a superset of "the starter's page", so checklist 14's provenance clause is not
  falsified; the note's removal list is.

### N6 — `fallback.cause` emits `throttled`, which is not in the note's closed enum, and never emits `disconnected`

- Where: `src/minigrid/decide.nim:229-232` (`cause = "timeout" | "transport_error"`), `:231`
  (`elif error.msg.startsWith("llm throttled"): cause = "throttled"`), `:252-257` (final cause
  ladder: `no_credentials | budget_guard | throttled | parse_error`), `:159-172`
  (`no_credentials | budget_guard | rate_guard`).
- What the note says: design.md:559-561 — *"`cause ∈ {timeout, parse_error, transport_error,
  no_credentials, rate_guard, budget_guard, disconnected}`"*. `throttled` is an eighth value;
  `disconnected` is never produced (a disconnected seat is handled by `deadSeats` and the scout
  fallback instead). `fallback.cause` is not schema-constrained anywhere (it is a replay chat record,
  not a `results` key), so nothing rejects it.

### N7 — an invalid action entry is counted twice: in `repliesRepaired` **and** in `actionsDropped`

- Where: `src/minigrid/decide.nim:272` (`sim.repliesRepaired += directive.dropped`) and `:276-277`
  (`sim.installPlan(…, directive.dropped + directive.overCap, …)`), with
  `src/minigrid/sim_state.nim:285` (`sim.actionsDropped += dropped`).
- What the note says: design.md:258-262 — over-cap entries *"are dropped and counted in
  `actionsDropped`"*; an entry that fails validation is *"**dropped** …, counted in
  `repliesRepaired`"*. The code adds the invalid count to both counters. Both keys are in
  `results_schema` and neither is scored (design.md:394-396), so only the reported numbers differ.

### N8 — a turn's wall clock can reach ~11.6 s, above the 9.5 s `turnBudgetMs` the note calls "a monotonic deadline around the whole turn"

- Where: `src/minigrid/decide.nim:138-140` (`turnStart = getMonoTime()`, `budget = turnBudgetMs`),
  `:178-183` (the `turnSpacingMs` sleep, taken **after** `turnStart`), `:191-194` (the budget check,
  evaluated **before** each attempt, not during it), `:214-215`
  (`makeRequests(batch, max(1, deadlineMs div 1000))`).
- Observed, worst case for one turn: spacing sleep ≤ 2.600 s + attempt-1 deadline 6 s = 8.600 s;
  8.600 < 9.500 so the guard at `:191` lets attempt 2 start, adding 3 s → **11.6 s**.
- Consequence, traced: this does **not** break checklist 5. Every individual wait is still explicitly
  bounded (2.6 s sleep, 6 s, 3 s, all handed to `CURLOPT_TIMEOUT` in whole seconds), the budget guard
  at `:146-152` switches the LLM off once `elapsed + 2 × 10 s > 660 s` (i.e. from ~641 s), the
  wall-clock stop fires at the top of the loop (`src/minigrid/server.nim:482-486`), and the
  post-artifact hold is `max(1, min(30, 480 div 24)) = 20 s` (`server.nim:623-630`). Worst-case total
  ≈ 660 + 11.6 + 20 ≈ **692 s < 720 s**. The note's arithmetic (design.md:515-532) uses 9.5 s per
  turn; the real per-turn ceiling is 11.6 s, and its own "absolute worst" line still lands inside the
  stop.

### N9 — `docker_smoke.sh` does not fail on `reason == "fault"`; it prints the reason and continues

- Where: `tools/ci/docker_smoke.sh:306-308` (`reason = results.get("reason") …; print(f"episode end
  reason: {reason}")`) and `:322-324` (the `smoke OK:` line). No comparison against `fault` anywhere
  in the file.
- What the note says: design.md:436-437 — *"A defect: `tools/ci/docker_smoke.sh` fails the build if
  the smoke episode reports it."* The file is the shared template with only the three documented
  substitutions (`diff` against `/workspace/coworld-builder/templates/tools/ci/docker_smoke.sh` is
  6 comment/default lines), and the template has no such check. The reviewed run reported
  `episode end reason: complete` (CI log line 1997), so nothing was masked here.

### N10 — no CI step runs the installed `coworld` CLI's manifest validator, though the note and the test's own docstring say one does

- Where: `.github/workflows/ci.yml` (three jobs: `test`, `docker-smoke`, `wasm-viewer`; no `uvx
  coworld` / `validate_upload_manifest` step anywhere) versus
  `tests/test_minigrid_manifest.nim:123-125` (*"CI runs `coworld`'s `validate_upload_manifest` /
  `_load_template_manifest` for real (the collab-cooking 2026-08-25 scar)"*) and design.md:1877-1880
  (§Tests item 34).
- Observed: item 34 as shipped is a Nim string/shape check over the raw template
  (`:126-138`: `{{MINIGRID_IMAGE}}` present, `$schema` present, compose service name, platform).
- Why it matters here: this is the gate that would have caught B1 before the release workflow.

### N11 — `ci.yml` never re-runs the baseline sweep with `--check`

- Where: `.github/workflows/ci.yml` (no `tune_baselines` reference; grep returns nothing) versus
  design.md:907-909 and `src/minigrid/baselines.nim:41-42` (*"`ci.yml` re-runs the sweep with
  `--check`"*). `tools/tune_baselines.nim` is committed and
  `tests/test_minigrid_driver.nim:205-213` does pin the shipped defaults against
  `tools/ci/baseline_tuning.json` (`pick` + a 12-cell grid over 40 seeds), which is the substance of
  checklist item 7's "tuned with a grid harness, not guessed".

### N12 — the derived broadcast page is never re-derived or `--check`ed in CI

- Where: `AGENTS.md` §Layout (*"`replay_broadcast.html` is **DERIVED** by
  `tools/build_broadcast_page.py`, never hand-edited"*) and `tools/build_broadcast_page.py` (17 660
  bytes, committed non-executable, 0644). `grep -rn build_broadcast_page` over `.github/`, `tools/`
  and `tests/` matches only a comment in `tests/test_minigrid_viewer.nim:98`.
- Observed: `client/minigrid_block.html` (24 347 bytes) and the block region of
  `client/replay_broadcast.html` are both committed; nothing verifies they agree, and nothing
  verifies the pre-banner region against the starter (CI has no starter checkout). Test 36
  (`tests/test_minigrid_viewer.nim:97-131`) substitutes structural marker checks.

### N13 — `plan`, `fallback` and `budget` events exist only on playback, not on the live `/global` feed

- Where: `src/minigrid/replays.nim:125-131` (`evPlan` built from the recorded `directive` record),
  `:142-147` (`evFallback`, `evBudget` from the `fallback` / `budget_guard` records) — all inside
  `applyControlRecord`, which the live server never calls. The live turn path
  (`src/minigrid/server.nim:529-539` → `src/minigrid/decide.nim:264-287`) emits only `evSay`
  (`decide.nim:282-284`) plus whatever `stepTick` produces.
- What the note says: design.md:1255-1258 — *"`stepEvents` derives these from state deltas during
  playback, so they cost no replay bytes and are **identical live and in replay**"*. Three of the
  eighteen kinds are replay-only. The shipped viewer is the replay bundle, so the spectator
  experience the platform serves is unaffected; the live `/global` feed is poorer.

### N14 — `keycorridor`'s corridor wall is at `x = 7`, not `x = 6`

- Where: `src/minigrid/tasks.nim:178-179` (`for y in 1 ..< GridSize - 1: setAt(7, y, wall)`),
  `:196-200` (doors at `x = 7`), `:201` (`result.doorX = 7`), `:185-189` (room separators span
  `x in 8 ..< 12`), `:208` / `:218` (ball and key at `8 + draw(…, 4)`), `:221-222` (agent at (2, 6)).
- What the note says: design.md:170-176 — *"A vertical corridor at `x = 6`. Three side rooms east of
  it occupying rows `1-3`, `5-7`, `9-11`"*. The rows, the door count, the locked-red/closed-grey
  split, the key/ball placement and the start pose all match; the dividing column is one cell east,
  making the corridor the region `x ∈ 1…6` rather than the single column `x = 6`.

### N15 — the 4096-byte reply cap is applied as 4096 **runes** after parsing a body capped at 16 384 bytes

- Where: `src/minigrid/llm.nim:187-193` (`parseJson(if response.body.len > 4 * MaxReplyBytes:
  response.body[0 ..< 4 * MaxReplyBytes] else: response.body)`) and `:199-200`
  (`if result.len > MaxReplyBytes: result = result.truncateRunes(MaxReplyBytes)` — a byte-length
  test feeding a rune-count truncation).
- What the note says: design.md:699 — *"whole reply | bytes | **≤ 4096** read from the provider
  before parsing"*. Everything downstream is still rune-safe (`truncateRunes`,
  `src/minigrid/sim_types.nim:228-237`), so no broken codepoint reaches the replay; only the cap's
  units and its position relative to `parseJson` differ.

### N16 — the player container does not truncate `prompt`/`policy` before sending; the server truncates on receipt

- Where: `src/minigrid_player.nim:33-48` (`registrationBlob` embeds `prompt` and `policy` raw) versus
  `src/minigrid/server.nim:313-314` (`node{"policy"}.getStr().truncateRunes(MaxPolicyLabelRunes)`,
  `node{"prompt"}.getStr().truncateRunes(MaxPromptRunes)`).
- What the note says: design.md:483-485 — *"with `prompt` rune-truncated at `MaxPromptRunes` = 4000
  and `policy` at 64 runes"* at the registrar. The caps are enforced, one hop later; the prompt is
  never written to the replay in any case (`decide.nim:78-89`, the redacted `register` record).

### N17 — the worst-case renderer fixture does not assert that the strings it drove through the chrome came out full length, and it clamps every run's origin into the canvas before measuring

- Where: `tools/ci/renderer_fixture.html:48-53` (`SAY` built to exactly 140 runes with a 4-byte emoji
  on the boundary), `:130-165` (`transcribe()`: reads `node.textContent` from the shipped page,
  `:153-155` `var x = Math.max(0, Math.min(canvas.width - 4, box.left)); var y = Math.max(0,
  Math.min(canvas.height - size - 2, box.top));`, then `ctx.fillText(text, x, y)`), `:211-214` (the
  only assertion: `if (total === 0) fail('the shipped chrome produced no text to measure')`).
- Observed: nothing compares the transcribed run against `SAY`/`MISSION`. A game block that shortened
  a remark before writing it into a feed row would transcribe the short string and still pass. The
  origin clamp means a run the shipped layout parked wholly off-frame is pulled back to
  `canvas.width - 4` before being drawn — it would then overflow the right edge and still be counted
  `outside`, so detection is degraded rather than defeated.
- What the checklist says: item 15's last bullet — *"The fixture asserts its own strings are still
  full-length — one quietly shortened remark leaves it passing while testing nothing."* The fixture
  itself **exists**, is wired in its own `ci.yml` step (`.github/workflows/ci.yml:367-402`), loads
  the shipped `index.html` in an iframe rather than re-implementing the drawing (`:41`
  `<iframe id="frame" … src="./index.html">`), drives the real `MinigridChrome.frame/event` through
  the page's own published `MG_CTX` (`:186-205`, `client/replay_broadcast.html:4083`), renders at
  960/640/**360** px (`:47`), sets `data-replay-loaded` (`:219`), and reported
  `canvas text: 57 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)` in run 33209437659 (log line 4406). Item 15's blocking clause is *"a repo
  that draws model text and has **no such fixture**"* — there is one, so I am not filing this as
  blocking; the missing length assertion is the gap.

### N18 — `generateXland` indexes an empty seq if the rule sampler bails, and nothing in `validate()` bounds `xlandObjects` / `xlandRules`

- Where: `src/minigrid/tasks.nim:320-321` (`result.rules = sampleRuleSet(…); result.goalObject =
  result.rules[result.rules.high].output`), `src/minigrid/xland.nim:17-18` and `:32-33`
  (`sampleRuleSet` returns `@[]` when `present.len < 4`, `ruleCount < 3`, or `pool.len < 3`), and
  `src/minigrid/sim_config.nim:122-159` (`validate()` checks the deadlines, `numAgents`,
  `gridSize`/`viewSize`, the ladder length and the turn/tick identities — not `xlandObjects` or
  `xlandRules`).
- Observed: unreachable at every shipped configuration (both variants and the cert fixture set
  `xlandObjects: 6`, `xlandRules: 3` → `present.len = 6 ≥ 4`, `pool.len = 18 − 6 = 12 ≥ 3`), and the
  manifest's `config_schema` is `additionalProperties: false` over a fixed property list. A runner
  that passed `xlandObjects: 3` would hit `rules.high == -1`; the resulting exception is caught by
  `server.nim:562-568` and settled as `reason: "fault"`, so it degrades rather than hangs.

### Minor notes (same class, one line each)

- `src/minigrid/labels.nim:3` names `tests/test_minigrid_labels.nim`, which does not exist; the
  contract is asserted by `tests/test_minigrid_viewer.nim:217-221` instead.
- §Readouts item 6 (design.md:1481-1482) splits the clock across `#clock` / `#clock-time` /
  `#clock-caption`; `mgRenderClock` (`client/replay_broadcast.html:4508-4531`) writes
  `SOLVED n/5` into `#clock-time` and the whole `task … · turn … · tick … · seen … · score …` line
  into `#clock-caption`.
- `src/minigrid/decide.nim:166-175`: the pre-attempt block (`no_credentials` / `budget_guard` /
  `rate_guard`) logs `"falling back to scout"` without a first attempt. Phase 60 greps for
  `falling back`, so a credential-less run still produces the phrase — which is also what
  `src/minigrid/llm.nim:126-127` intends (`"the LLM provider is unavailable"`). The
  attempt-1/attempt-2 phrasings themselves are correct (see T14).

---

## Traced and consistent

**Resolution rules**

- `src/minigrid/sim_state.nim:511-610` — `stepTick` runs the note's numbered tick order exactly:
  tick/taskTick increment (`:521-522`), pop-or-`wait` (`:526-530`), `applyPrimitive` (`:535`),
  obstacles (`:562-564`), productions (`:567-574`), termination in the order lava → success →
  `taskTick >= taskTurnCap * turnTicks` (`:577-584`), visibility merge + subgoals (`:586-591`),
  early break by clearing the queue (`:593-597`), hash last (`:600`). Matches design.md:276-317.
- `src/minigrid/sim_state.nim:250-271` — `advanceTasks` is the turn-boundary task advance, and it is
  called from **both** paths: live at `src/minigrid/server.nim:530` and on playback at
  `src/minigrid/replays.nim:113`, immediately before `installPlan` in each. The eleven-turn window is
  enforced here (`:260-261` `if sim.taskTurns >= sim.config.taskTurnCap: sim.endTask(toTimeout)`),
  which bounds turns at 5 × 11 = 55 = `maxTurns` and ticks at 660.
- `src/minigrid/agent.nim:44-119` — the seven primitives match design.md:283-297 cell for cell:
  `left` = `(dir+3) mod 4`, `right` = `(dir+1) mod 4`, `forward` crashes on an obstacle **without
  moving** (`:59-61`), lava is passable and lethal via step 6 rather than via the move
  (`sim_types.nim:194-200`, `sim_state.nim:578-580`), `pickup` only empty-handed onto a non-obstacle
  key/ball/box, `drop` only onto empty floor, `toggle` open↔closed / unlock-with-same-colour-key
  **without consuming the key** (`:99-105`) / box → contents-or-floor.
- `src/minigrid/agent.nim:121-143` — obstacle motion is
  `Dirs[mix64(seed, taskIndex, 900 + i, tick) mod 4]`, ascending index, moves only into empty floor
  that is not the agent's cell (`:135-137`). Matches design.md:298-302 including "an obstacle never
  moves into the agent".
- `src/minigrid/xland.nim:57-93` — the production scan is ascending `(y, x)`, neighbours in
  east/south/west/north, rules in ascending index, **one firing per tick** (`return` at `:92`),
  product placed in the lower-`(y, x)` cell (`:84-91`), carried objects excluded via `objectAt`
  (`:50-55`).
- `src/minigrid/grid.nim:81-101` — `visibleMask` is the note's flood transcribed line for line:
  `vis[3][6] = true`, `j` from 6 down to 0, right sweep `i = 0…5` then left sweep `i = 6…1`, each
  setting `vis[i±1][j]` and, when `j > 0`, `vis[i±1][j-1]` and `vis[i][j-1]`; `seesBehind` is false
  for wall / closed door / locked door only (`sim_types.nim:202-208`). `viewRows` (`:103-117`) emits
  7×7, `A` at (3,6), `?` for unmarked, `#` out of grid. `knownRows` (`:143-149`) emits 13×13.
- `src/minigrid/tasks.nim` — every draw is `draw(seed, taskIndex, salt, bound)` =
  `mix64(seed, taskIndex, salt) mod bound` (`sim_types.nim:248-270`), a pure hash with an increasing
  salt and no consumed stream. Spot-checked against the note: `lavagap` `gapX ∈ 4…8`, `gapY ∈ 1…11`,
  start (1,1) east, goal (11,11) (`:67-81`); `doorkey` `wallX ∈ 5…7`, locked yellow door,
  key+agent west / goal east (`:87-123`); `multiroom` walls at x=6/y=6, three closed doors
  blue/green/purple on the 0→1, 1→2, 2→3 boundaries only, agent in room 0, goal in room 3
  (`:137-164`); `dynamic` 6 grey obstacle balls, goal (11,11), start (1,1)
  (`:230-258`); `babyai` six distinct `(type, colour)` pairs and the three-rule grammar keyed on
  `draw(seed, taskIndex, 40, 3)` (`:264-309`); `xland` six objects + the chained triple
  `(A+B)→P0, (C+D)→P1, (P0+P1)→GOAL` with products absent at the start (`xland.nim:11-43`).
  `tests/test_minigrid_sim.nim:316-372` asserts layout identity over 200 seeds under three different
  agent behaviours.

**Decision path**

- `src/minigrid/decide.nim:202-215` — one request per turn through the starter's batching path
  (`batch.post(...)` then `engine.client.curl.makeRequests(batch, deadlineMs div 1000)`), a batch of
  one for the single seat; never a sequential per-seat loop.
- `:188` `while open and attempt < 2` — **exactly one retry**; `:195-196` uses `attempt1Ms` then
  `retryMs`; `:198-201` appends the repair instruction on attempt 2 only.
- `:250-262` — on a second failure the plan becomes `scoutFallback` (`:112-117`), which calls the
  **same** `scoutPlan` proc the `scout` baseline uses (`baselines.nim:158`, re-exported through
  `scriptedPlan` at `:267-273`); `tests/test_minigrid_driver.nim:120-128` asserts the two produce the
  same actions and that the fallback's source is `dsFallback`.
- The fallback is recorded three ways so phase 60 can count it: the `fallback` chat record
  (`decide.nim:69-76`, written by `server.nim:536-537`), `results.fallbackTurns`
  (`decide.nim:280` → `sim_state.nim:900`), and the log line.
- `src/minigrid/directives.nim:41-80` — `extractJsonObject` walks for the outermost balanced `{…}`
  with string/escape awareness, falls back to first-brace…last-brace, and raises only when there is
  no object; fences and trailing prose are tolerated
  (`tests/test_minigrid_driver.nim:186-188`). `:113-153` — invalid entries are **dropped, never
  rewritten**; `goto` coords clamped to 0…12; `do` truncated at 8 runes and lower-cased; `dir`
  truncated at 5 runes and case-folded; a `say`-only reply is usable; a non-object raises.
- Budget guard `decide.nim:144-152` fires when `elapsed + 2 × ceil(turnBudgetMs/1000) >
  wallClockBudgetSeconds`, writes `budget_guard` and switches the LLM off for the rest of the
  episode. Rate guard `:119-126` keeps a rolling 60 s stamp list and blocks the 29th request in the
  window (`RateGuardMaxRequests = 28`, `:26`), taking the scout plan with `cause = "rate_guard"`
  rather than sleeping. `tests/test_minigrid_engine.nim:125-163` forces both and asserts the episode
  settles `complete`.

**Every wait and its bound**

- attempt 1 `6000 ms`, retry `3000 ms`, `turnBudgetMs 9500`, `turnSpacingMs 2600` —
  `src/minigrid/sim_config.nim:85-88`, and the same four values in both variants and the cert
  fixture (`coworld_manifest_template.json`, asserted by `tests/test_minigrid_manifest.nim:24-30`).
  `validate()` (`sim_config.nim:126-139`) rejects sub-second deadlines and
  `attempt1Ms + retryMs > turnBudgetMs`.
- Engine stop 660 s: `src/minigrid/server.nim:482-486` at the **top** of every loop iteration →
  `applyStop(edWallClock)` → `reason: deadline`, `endRule: wallClock`
  (`sim_state.nim:237-246`); `wallClockBudgetSeconds: 660` in both variants (240 in the cert
  fixture), `≤ 660` asserted by `tests/test_minigrid_manifest.nim:26` and `:57`.
- Lobby bound: `lobbyJoinTimeoutTicks 2400` at `TargetFps 24` = 100 s, paced in wall clock even under
  `fastMode` (`server.nim:517-526`, `sim_state.nim:616-630`).
- Shutdown hold: `holdSeconds = max(1, min(30, gameOverTicks div TargetFps)) = 20 s`
  (`server.nim:623-630`), then `quit(0)`.
- Player container: dialling bounded at 240 × 500 ms, registration re-sends bounded at 10,
  re-dials bounded at 6, and it exits **0** on a dead socket
  (`src/minigrid_player.nim:26-31, 112-146`).
- Total worst case ≈ 692 s < 720 s (60 % of 1200 s). See N8 for the per-turn arithmetic.

**String truncation**

- `src/minigrid/sim_types.nim:228-237` `truncateRunes` is the single shortening proc and uses
  `runeLen`/`runeSubStr`, never a byte slice; `:239-246` `sanitizeSay` (140) and `sanitizeNote` (300)
  collapse newlines then truncate. Caps at `:43-50`: `MaxSayRunes 140`, `MaxNoteRunes 300`,
  `MaxPolicyLabelRunes 64`, `MaxFallbackDetailRunes 200`, `MaxStopDetailRunes 200`,
  `MaxPromptRunes 4000`.
- Every string reaching the replay goes through it: `say`/`notes` (`directives.nim:122-123`),
  `policy` (`decide.nim:86`), `fallback.detail` (`decide.nim:75`), `stop.detail` (`decide.nim:99`),
  `stopDetail` (`sim_state.nim:242`), the fault message (`server.nim:566`), the player-failure
  message (`server.nim:288`), and provider error bodies (`llm.nim:171, 180, 186`).
  `boundedDirectiveRecord` (`directives.nim:197-219`) shrinks `say` on rune boundaries and explicitly
  never cuts the serialized JSON.
- `tests/test_minigrid_driver.nim:174-185` feeds 400 × U+1F9E9 and asserts
  `runeLen == 140/300`, `validateUtf8() == -1`, and `say.len == 140 * 4` (whole codepoints only);
  `tests/test_minigrid_replay.nim:134-173` runs `tools/replay_summary.py` over a replay with every
  capped field at its cap and asserts strict-UTF-8 JSON, no lone surrogates, and
  `protocol == "minigrid/v1"`.

**Replay writer and re-derivation**

- `src/minigrid/replays.nim:26-37` — `MinigridReplayMagic = "COWLDMGD"`, format version 1, game name
  `minigrid`, game version `1`, `joinKind: rjkNameSlotToken`, `hashOrder: rhoStop`.
- One `gameHash` per tick: `server.nim:469-474` `recordHash()` after every `sim.step()`, including
  the extra tick stepped after the stop record (`:580-583`).
- The stop is a **load-bearing record**, not an inference: written once at the last simulated tick
  (`decide.nim:94-99`, `server.nim:580-581`) and applied on playback by the **same** proc
  (`replays.nim:148-153` → `sim.applyStop`, `sim_state.nim:237-246`).
- Config JSON is self-sufficient and `tokens`-free: `sim_config.nim:242-289` writes seed, variant,
  `num_agents`, every rule constant, the ladder, `players[].name`, `slots`, `fastMode`;
  `tests/test_minigrid_replay.nim:115-125` asserts all 22 keys are present and `tokens` is absent.
- `tests/test_minigrid_replay.nim:55-64, 68-88` — `rederive` runs with `mismatchQuit = true`, so a
  per-tick hash divergence **raises**; the test does this for `gauntletComplete`, `turnCap`,
  `wallClock` **and** `fault`, and asserts identical final tick, hash, endRule, reason, tasksSolved
  and score. Checklist item 2's "frame by frame" is enforced by `checkReplayHash`
  (`replays.nim:236-265`), which compares every recorded tick's hash and refuses to skip one
  (`:245-252` treats a missing tick as a mismatch).
- The viewer derives its display from **that same** re-derivation, not a parallel recording:
  `replay-viewer/minigrid_replay.nim:17` imports `minigrid/[…, sim]`, `:69-73` calls the shared
  `initReplayRuntime` (`src/minigrid/replay_runtime.nim:15-37`), and every drawn frame comes from
  `buildReplayViewerPacket(game, replay, …)` (`:56`, `replay_runtime.nim:68-92`) over the re-simulated
  `SimServer`.
- `gameHash` mixing order (`sim_state.nim:450-487`) is exactly design.md:1022-1027: taskIndex,
  taskTick, agent `(x, y, dir, carriedKind, carriedColour)`, all 169 cells in ascending `(y, x)` as
  `(kind|obstacle, colour, doorState)`, obstacles ascending, the fired-rule bitmask and
  `productionsFired`, the three subgoal bits, the five `taskOutcome` codes and `taskProgress` values,
  then `tick`.

**Viewer wiring and playback start**

- All four viewer files come from **one** starter, renamed only: `diff` against
  `/workspace/starters/coworld-ctf/replay-viewer/` shows `config.nims` differs in 4 lines (the output
  name, the `EXPORTED_FUNCTIONS` list, two comments), `static_replay_worker.js` in 13 lines (all
  `_ctf_*` → `_minigrid_*` plus `importScripts('./…/minigrid_replay.js')` at `:239`), and
  `static_replay.js` in **one** line (the Worker's `name`).
- The bootstrap and the link flags agree: `replay-viewer/config.nims:42-54` carries **no**
  `MODULARIZE` and no `EXPORT_NAME` (non-modularized), and the worker waits for
  `Module.onRuntimeInitialized` (`static_replay_worker.js:188`, with `var Module = {}` at `:8` and
  `self.Module = Module` at `:192`). This is the pairing checklist 13 requires; the cogame-lantern
  deadlock shape is absent. `-s ABORTING_MALLOC=1` is present (`config.nims:47`).
- Load/error markers are the starter's own, both from the shell's code paths:
  `data-replay-loaded="true"` in the `'loaded'` branch (`static_replay.js:161`) and
  `data-replay-error` in `showFailure()` (`:8-20`). The artifact confirms them at runtime:
  `viewer-smoke.json` → `"loaded": true`, `"signals": {"data_replay_loaded": "true",
  "data_replay_error": null}`, `"failure": null`.
- **Playback opens at the game start, not the lobby.** `initReplayRuntime`
  (`replay_runtime.nim:28-36`) steps the lobby internally, sets `startTick = gameStartTick` the first
  tick the phase is `Playing`, then `seekReplay(replayStartTick())`; `minigrid_replay.nim:82` repeats
  the seek after the pre-scan; every seek is clamped: `beginSeek`
  (`replays.nim:436-437` `clamp(tick, replay.replayStartTick(), replay.replayMaxTick())`), and the
  scrubber axis is the same `st` (`broadcast.nim` `"st": startTick`). The pre-scan also sets it
  (`replays.nim:327-328, 347-348`). Runtime evidence: the smoke replay's first sampled tick readout
  is `"4 / 267"`, not `0 / 271`.
- Load-time pre-scan: `minigrid_replay.nim:80-81` `replay.advanceReplayScan(int.high)` before the
  first frame, so beats, lull spans and the progress series ship at full width
  (`replay_runtime.nim:80-92` gates `sendLead` on `scanComplete()`).

**Chrome provenance**

- `client/chrome_common.js` is **byte-identical** to the starter's: 40 022 bytes, sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` — confirmed by `sha256sum`
  against `/workspace/starters/coworld-ctf/client/chrome_common.js`, and pinned as a literal at
  `tests/test_minigrid_viewer.nim:9-10, 92-95`.
- `client/replay_broadcast.html` is the starter's page (234 070 B) **grown** to 237 621 B, not a
  rewrite: the starter's banner at `:4344` becomes `MINIGRID additions to the inherited coworld-ctf
  chrome` at `:4091`, the block sits after it, and the splice hook is the starter's own
  (`window.MinigridChrome.install(PB_CTX)` at `:4084`, `frame` at `:1818`, `event` at `:3224-3225`).
  The pre-banner region differs from the starter only by the note's enumerated removals (`#viewpanel`
  and its zoom controls, `#povBadge`, `#fpv-hp`, `#fpv-gear`, `#fpv-map*`, the four unused
  `.beat-marker` kinds) and the vocabulary re-map; every removed id returns 0 hits
  (`grep`: `viewpanel`, `povBadge`, `fpv-map`, `attachMinimap` call site all 0) and
  `tests/test_minigrid_viewer.nim:210-215` asserts that plus the 51 kept ids.
- Transport rules, each checked in the page: **(a)** `relayout()` sets `--hudscale`, `--topband` and
  `--band` on `document.documentElement` (`:4036-4062`, `root.style.setProperty`), the starter's own
  fixed-point loop, kept verbatim including `Math.max(0.5, Math.min(1.6, boardW / 760))` and
  `stage.classList.toggle('tiny', boardW <= 620)`. **(b)** Nothing the block adds is fixed-positioned
  or anchored from the bottom — `#mg-ribbon` and `#mg-pips` ride `top: calc(var(--topband, 0px) + …)`
  (`:4149`, `:4177`), asserted by `tests/test_minigrid_viewer.nim:195-197`. **(c)** `#endcard` keeps
  `bottom: var(--band, 0px)` (`:809-831`), is shown with `#endcard.on` (`:831`), and **every** seek
  takes it down through the starter's own frame path
  (`:1815` `else { $('endcard').classList.remove('on'); }`). **(d)** Beats are labelled, clickable
  `<button>`s that seek: `mgBeat` (`:4348-4368`) builds
  `<button class="beat-marker <kind>" title=… aria-label=…>` and sends `'s:' + tick` on click; the
  `mg-` prefix cannot shadow `chrome_common.js`'s hoisted `markBeat`
  (`tests/test_minigrid_viewer.nim:133-154` extracts the whole alias list and checks it). CSS exists
  for **exactly** the seven emitted kinds and no others —
  `grep -o '\.beat-marker\.[a-z]*'` returns `taskstart, solved, failed, unlock, produce, fallback,
  end`, matching `isBeat()` (`src/minigrid/broadcast.nim:105-111`) and asserted both ways at
  `tests/test_minigrid_viewer.nim:156-181`.
- `#viewpanel` correctly **removed** (not hidden): the board is a fixed 13 × 13 grid that
  `relayout()` letterboxes whole (`BOARD_ASPECT` from the streamed `boardW/boardH`, `:1677-1682`), so
  the pin's "fixed arena" branch applies.

**Legibility at 360 px**

- `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }` —
  `client/replay_broadcast.html:4114-4119`, identical to the starter's `:4369-4374`, asserted at
  `tests/test_minigrid_viewer.nim:199-201`.
- Label hiding under the embedded width is the starter's `.tiny` mechanism (`boardW <= 620`,
  `:4058`), with the game's own label elements hidden under it (`:4296`, `:4314`, `:4316`) —
  the starter's `#stage.tiny .pb-tags/.lives-label/.hillchip` rule was replaced in kind. All five
  `.tiny` rules the note names exist and are asserted (`tests/test_minigrid_viewer.nim:202-205`).
- The 7×7 inset draws **chips, never text** (`:4462-4475` `ctx.fillRect` only), so nothing it draws
  can escape its canvas at any `--hudscale`.
- `ci.yml`'s viewer smoke carries `--strict-text-bounds` (`.github/workflows/ci.yml:356`) and the
  fixture step carries it too (`:399`). Run 33209437659: bundle smoke
  `canvas text: 0 drawn, 0 never inside`, fixture `canvas text: 57 drawn, 0 never inside … 0
  ellipsized`. Per checklist 15 the bundle's `total: 0` is *not* evidence (the board is drawn in a
  Worker on an OffscreenCanvas — `static_replay.js:81` transfers the surface), which is precisely why
  the fixture is load-bearing here; see N17 for its one gap.

**Manifest, `num_agents`, policies, workflows**

- `num_agents: 1` in **both** variants' `game_config` and in `certification.game_config`, absent at
  every variant top level, with `players: [{"name": "Alpha"}]` in each and no literal `tokens`
  anywhere — asserted at `tests/test_minigrid_manifest.nim:13-35` and verified directly from the
  file. `len(certification.players) == len(certification.game_config.players) == num_agents == 1`.
- `tools/ci/docker_smoke.sh` is the shared template (only the three documented substitutions) and
  carries all four seat-count invariants exiting with `SEAT-COUNT FAIL:` (`:111-151`);
  `SMOKE_SEATS` defaults to `1` (`:54`) as the independent second declaration. **`SEAT-COUNT FAIL`
  appears zero times** in the run-33209437659 log (grep over the full 4 519-line log), and the
  docker-smoke job printed `smoke OK: seats=1 … reason=complete` (log line 1998). Mode is 100755.
- `game.replay_viewer = {"bundle": "static-replay-viewer"}` under `game`
  (`coworld_manifest_template.json:17-19`); `tools/build_replay_viewer.sh` exists, is committed
  100755, is the path `coworld/bundle.py:22` hard-codes as the hook, and CI invokes it by path
  (`.github/workflows/ci.yml:290`). No `/client/replay` pod path is declared to the platform — the
  only occurrences are the local dev route the starter already serves
  (`src/minigrid/server.nim:196-202`) and `docs/PROTOCOL.md:26`.
- `game.docs` = `{"readme": {…}, "pages": [3 × {"id","title","content"}]}` and `game.protocols`
  carries **both** `player` and `global` as `{"type","value"}` objects
  (`coworld_manifest_template.json:29-60`); accepted by the real CLI model once B1's three keys are
  corrected.
- `tools/ci/policies.json` — four policies, one image, `run: "/bin/minigrid-player"`: two
  `PLAYER_PROMPT` champions (`:3` `minigrid-cartographer`, `:11` `minigrid-missionfirst`) with
  champion **#2** carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`:17`), plus two
  `PLAYER_SCRIPTED` fillers (`:20` `scout`, `:28` `bumper`).
- The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows,
  `docker_smoke.sh` and `policies.json` returns nothing. The four expected residue names survive by
  design and only there: `<cow_id>`/`<sha>` in `ci.yml`'s static-route comment, `<run_id>` in the two
  artifact-readback recipes, `<name>:vN` in `coworld-submit.yml`'s policy input description.
- All three workflows present. `coworld-release.yml` order is build (`:159`) → certify (`:173`,
  with `--timeout-seconds 300` at `:184`) → upload policies (`:216`) → upload coworld (`:314`) →
  secret put (`:410`).
- `ci.yml`'s `wasm-viewer` `needs: docker-smoke` (`:243`) and runs the smoke against the replay
  docker-smoke produced (`:311-323` download, `:324-356` load). No `continue-on-error` anywhere in
  the file.

**Name spaces, scoring, end conditions**

- Agents see the alias only: `observationJson` sets `"you": seatAlias(0)` = `Alpha`
  (`sim_state.nim:771`, `:133-138`) and carries no seed, no score, no real name, no unobserved cell,
  no layout parameter, no `xland` rule table; the user message is
  `operatorBlock(prompt) & viewJson` (`llm.nim:268-269`) with no identity. The prompt itself is
  never written to the replay (`decide.nim:78-89`, redacted `register` record).
- Spectator side carries the real name: `rosterJson` (`broadcast.nim:113-136`) ships `name`
  (real) **and** `alias`; `chrome_common.js:145-158` `teamName` resolves the plate headline to the
  seat's policy, `:371-377` `rosterName` feeds the endcard rows, and `results.names[0]` is the real
  policy name while `results.aliases[0]` is `Alpha` (`sim_state.nim:838-839`,
  `tests/test_minigrid_engine.nim:85-87`). `showPlayerLabels: false` in both variants and the cert
  fixture. Runtime evidence: `viewer-smoke.json` `"scorebug": "RED KEY SCOUT Carrying 2/5 ALPHA ·
  SCORE 208130 …"` — both spaces on screen at once.
- Scoring: `sim_state.nim:196-213` — `100_000 * tasksSolved + 1_000 * progressTotal + 10 *
  speedTotal`, `speed[i] = max(0, taskTurnCap - turns)` only when solved, `progress` forced to 3 on a
  solve (`:190-191`), every term additive. `win[0] = tasksSolved >= parTasks` and `winner = 0` or
  `null` (`:841, 857-859`). `tests/test_minigrid_sim.nim:507-554` asserts the formula over randomised
  end states, both dominance bounds and the 515 500 maximum;
  `tests/test_minigrid_engine.nim:56-71` asserts the four results identities on a real episode.
  `results.scores[0]` is what the league ranks.
- End conditions: `reason ∈ {complete, deadline, fault}` (`sim_types.nim:121-125`) and
  `endRule ∈ {gauntletComplete, turnCap, wallClock, fault}` (`:127-133`), both enumerated in
  `results_schema` (`coworld_manifest_template.json`) and both closed enums in Nim.
  `gauntletComplete` at `sim_state.nim:266-268`, `turnCap` as an independent guard at `:605-610`,
  `wallClock` at `server.nim:482-486`, `fault` at `server.nim:562-568`. Unreached tasks are recorded
  `unreached` with zero turns/ticks/progress (`sim_state.nim:226-229`) and the tasks that ran keep
  their real outcomes.
- A silent seat cannot stall the episode: `server.nim:509-516` marks `deadSeats[0]`, reports exactly
  one closed-schema `{"message","failed_policy_index"}` payload (`:280-292`) and plays the gauntlet
  out on `scout`; `server.nim:498-508` refuses to start (loudly, `endRule: fault`) if a seat joined
  but never registered. `tests/test_minigrid_engine.nim:103-123` runs the never-connects case end to
  end against the real binaries and asserts `reason == "complete"` and the two-key payload.

**Tests and CI**

- CI green at the reviewed sha: `gh run list -R Metta-AI/cogame-minigrid --branch main -w ci.yml` →
  run **33209437659**, conclusion **success**, on `main` at `d8f9e7c`. All three jobs succeeded and
  every step ran — in particular `wasm-viewer :: Load the bundle in a real browser :: success`,
  `wasm-viewer :: Worst-case renderer fixture (the LLM text path) :: success`, and
  `wasm-viewer :: Headless wasm smoke of the emitted module :: success`. No step is
  `continue-on-error` and none is skipped.
- No test loosened during this run: `git log -p 605307a..HEAD -- tests/` is a single hunk,
  `tests/test_minigrid_endcard_labels.nim` **+7 lines, −0** (`d8f9e7c` adds `VerdictRelabel` and two
  new `check`s). No deleted assertion, no widened tolerance, no skip/xfail added, no test file
  removed.
- All 42 numbered design tests exist and are numbered to match (`tests/test_minigrid_{sim (1–16),
  driver (17–23), engine (24–27), replay (28–32), manifest (33–34), viewer (35–39, 41),
  endcard_labels (40), events (42)}.nim`); items 43–45 are the three `ci.yml` steps above. The design
  names some of them in files that do not exist (`test_minigrid_scoring/tasks/tuning.nim`); the
  content is present in `test_minigrid_sim.nim:507` (13. scoring), `:316` (8. generators) and
  `test_minigrid_driver.nim:205` (22. tuning).
- `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` clean), so its
  `--url`/`--out`/`--strict-text-bounds` handling is the template's.
- `tools/ci/check_gameversion.sh` and `tools/ci/next_coworld_version.py` are byte-identical to the
  starter's.
- The soak observed real advancement: `"soak": {"seconds": 10, "moved": true, before tick "4 / 267"
  → middle "196 / 267" → after "244 / 267"}`, `"page_errors": []`.

---

## Could not determine

- **Whether `#fpv` is genuinely invisible in a browser (N1).** I read the CSS and the single
  `classList.toggle('on')` site and traced `pov`/`fp` to their producers, but I cannot run a browser
  here and the CI screenshot is taken with the endcard up. What would settle it: a
  `getComputedStyle(document.getElementById('fpv')).display` probe in `viewer_smoke.mjs`, or a
  screenshot taken at the 0 % scrub position.
- **Whether `coworld build` has ever been run against this template.** No release run exists for this
  repo (`ci.yml` never invokes the CLI, and `coworld-release.yml` is `workflow_dispatch`-only), so
  B1 has not yet been observed failing in anger — only reproduced locally against the pinned
  `coworld==0.1.43`. What would settle it: a `coworld build` run, or the CI step the design's test 34
  specifies.
- **Whether the platform's server-side manifest schema is identical to the CLI's pydantic model.** I
  checked the client-side model that `coworld build` and `coworld upload-coworld` use; the server may
  differ. What would settle it: an actual upload, or the platform's published schema.
- **Whether the renderer fixture's transcription faithfully represents the shipped page's glyph
  rendering (N17).** The board and the 7×7 inset draw in a Worker on an OffscreenCanvas
  (`static_replay.js:81`), so `canvas_text.total` is 0 for the real bundle and 57 for the fixture's
  re-drawn DOM runs. What would settle it: instrumenting the Worker's OffscreenCanvas context, or a
  pixel diff of the fixture against the live page at 360 px.
- **The `dynamic` obstacle-motion invariants under long play.** I traced
  `stepObstacles` and the `crash` path statically and `tests/test_minigrid_sim.nim:125-177` covers
  them, but I did not run the suite in this sandbox (no Nim toolchain here); I am relying on the CI
  `test` job's `success` for execution evidence.
