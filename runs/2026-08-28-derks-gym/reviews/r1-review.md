# r1 review — cogame-derks-gym

Repo: `Metta-AI/cogame-derks-gym` @ `70db5596b8ab90bb9207faf7e22ddb946a800375` (main HEAD, cloned to
`/tmp/cogame-derks-gym`).
Starter for provenance diffs: `/workspace/starters/cogame-moba` (read-only mount).
Design note: `/workspace/coworld-builder/runs/2026-08-28-derks-gym/design.md` (read in full).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
CI evidence: run **33166095890** (`gh run view … --log`), conclusion `success` on `main` at the
reviewed sha; jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓, `upload-coworld` ✓ (warn-and-skip).
Files read / diffed: ~45 (every server + player module, both sim C headers, all four viewer files,
the manifest, all three workflows, both CI mjs scripts, `docker_smoke.sh`, `docs/DRAFT.md`,
`docs/PORTING.md`, and 8 test modules).

Findings are numbered F1…F15. Each is an **observation of divergence or of a fact worth recording**,
not an accusation; the "Traced and consistent" section is the larger half of this report and carries
the same weight. Categorisation against the checklist is stated per finding; nothing here is a fix
proposal.

---

## Findings

### F1 — the shared draft deadline is collective, not per seat: one slow seat discards **all six** seats' picks

- Where: `server/cogame_derks_gym/draft.py:266-278`
- Observed:
  ```python
  deadline = cfg.draft_deadline_ms / 1000.0
  async def batch():
      return await asyncio.gather(*(_one_seat(source, observation) …))
  started = time.monotonic()
  try:
      gathered = await asyncio.wait_for(batch(), deadline)
  except (asyncio.TimeoutError, TimeoutError):
      elapsed = int((time.monotonic() - started) * 1000)
      gathered = [(None, "timeout", elapsed)] * defaults.NUM_SEATS
  ```
  `asyncio.gather` completes only when the **slowest** seat completes, so `wait_for` fires whenever
  any single seat exceeds `draft_deadline_ms`; the gather (and with it every already-finished child)
  is cancelled and **every** entry is replaced with `(None, "timeout", …)`. Seats that answered
  legally inside the deadline lose their picks and get the neutral loadout.
  `WsSeat.get_draft` (`server/cogame_derks_gym/server.py:181-201`) awaits its future with no per-seat
  bound, so the shared `wait_for` is the only deadline in the path.
- Reproduced (not inferred): with 6 sources, one delaying 5 s and five returning a legal frame
  immediately, `draft_deadline_ms=1000`:
  ```
  elapsed 1.00
  pid 0 seat 0 timeout {arm_none, tail_none, misc_none}
  pid 1 seat 1 timeout {arm_none, tail_none, misc_none}
  …all six seats: fallback_cause=timeout, neutral picks
  ```
- Design note requirement: §The game, Phase B step 3 — "Resolution, **per seat**, in this order:
  1. No reply by the deadline → neutral loadout, `fallback_cause: "timeout"`." `docs/DRAFT.md:139`
  repeats the heading "Resolution order, **per seat**". The shared deadline is per the note (step 1);
  the per-seat resolution of case 1 is not what the code does.
- Test coverage: `tests/test_draft.py:139-147` exercises exactly this scenario but asserts only
  seat 0, and its comment ("every seat that had not answered yet times out") describes the per-seat
  reading rather than the observed all-seats behaviour.
  `tests/test_draft.py:164-176` (all six slow) passes either way.
- Checklist: **not blocking**. The wait is explicitly bounded (item 5 satisfied — one batch, one
  deadline, and the whole turn still costs one `draft_deadline_ms`), the degrade is to the legal
  neutral loadout, and no checklist item names per-seat draft resolution. Recorded as a correctness
  divergence from the design note.

### F2 — `decision_ms` on the timeout path is the batch elapsed, identical for every seat

- Where: `server/cogame_derks_gym/draft.py:277-278`
- Observed: on the collective timeout every record gets `decision_ms = elapsed` (the deadline), not
  the seat's own measured latency from `_one_seat` (`draft.py:239-249`). A seat that answered in
  40 ms is recorded as having taken 45 000 ms.
- Design note: the draft-reveal record's `decision_ms` is documented as the seat's answer time
  (§Replay format v2, `"decision_ms": 8123`). Consequence of F1; recorded separately because it is a
  distinct field of the replay header and `results.draft`.
- Checklist: not blocking (no item names `decision_ms`).

### F3 — the inherited inline transport script carries two non-additive edits beyond the note's stated allowance

- Where: `viewer/index.html:128-138` and `viewer/index.html:140-151`
- Observed: the note (§Chrome provenance) permits the transport script to change only by
  "additive hooks only … Two literal string edits are allowed: the `<title>` and the `<header>` text
  …, and `moba_viewer.js` → `derk_viewer.js`." The actual diff against
  `/workspace/starters/cogame-moba/viewer/index.html` contains, besides those and the four additive
  hooks (`derkOnLoad`, `derkOnFrame`, `derkDismissEndcard`, `derkSetError` via `derkFail`), two
  in-place rewrites:
  - `parseHeader`: `"MOBA"`/`buf[4] !== 1` → `"DERK"`/`buf[4] !== 2` (lines 133-134);
  - `fillNames`: the starter's `const h = cfg.heroes_per_seat || 1; const team = Math.floor((seat*h)/5)`
    replaced by a `header.seat_hero_pids` lookup (lines 143-151).
  Both are forced by this game's own format (`replay.py:59-60`, magic `DERK` v2) and by the removal
  of `heroes_per_seat` from the config (§Server, config: "Removed: `heroes_per_seat`"). Every other
  line of the script is byte-identical to the starter's, the banner comment is present
  (`viewer/index.html:73-78`), no starter id is reused, re-styled or removed, and the page is
  299 lines vs the starter's 232 (an appended block, not a rewrite).
- Checklist item 14 (chrome provenance): satisfied in substance — this is the starter's page plus an
  appended, banner-delimited game block. Recorded because the diff is larger than the note's literal
  sentence allows. **Not blocking.**

### F4 — the certification fixture is not the note's `baseline ×6`

- Where: `coworld_manifest_template.json:727-747`
- Observed: `certification.players` = `[baseline, baseline, drafter, baseline, baseline,
  lane-brawler]`. The design note (§Packaging, `certification`) writes six `baseline` entries.
- This is the builder's documented deviation (commit `70db559`, "cert fixture: seat every declared
  player"). The implementation matches the claim: all three declared runnables hold a slot, the count
  is 6, and `tests/test_manifest.py:252-262` pins `set(seated) == declared` with
  `seated.count("baseline") >= len(seated) - 2`. `tools/ci/docker_smoke.sh:390-425` re-derives each
  scripted seat's expected picks from the manifest and requires ≥2 distinct pick-sets, so a fixture
  that silently reverted to one policy fails the smoke. CI: `picks=['arm_blaster','arm_needler',
  'arm_blaster','arm_blaster','arm_needler','arm_needler']` (run 33166095890, docker-smoke).
- Checklist item 6 (`num_agents`): unaffected — `len(certification.players) == 6 ==
  certification.game_config.num_agents`. **Not blocking.**

### F5 — `docker_smoke.sh` runs the certification fixture, not the note's seed-7 / 200-tick config

- Where: `tools/ci/docker_smoke.sh:90-183` (config derived from `certification.game_config`) and
  `coworld_manifest_template.json:748-778` (seed 42, `max_ticks` 1200, `tick_deadline_ms` 250,
  `draft_deadline_ms` 5000).
- Observed: the design note §Tests, Job `docker-smoke` specifies `{"seed": 7, "max_ticks": 200,
  "tick_deadline_ms": 1000, …}`. The template smoke takes its config from the cert fixture by
  construction and was not modified. The note's assertion list **is** appended verbatim in spirit at
  `tools/ci/docker_smoke.sh:328-452`: exact 16-key set, `len(scores)==6`, `sum(scores)==3.0`,
  `noop_ticks==[0]*6`, `dead_seats==[False]*6`, `draft_fallbacks==[False]*6`, ten draft records with
  `source` split `[0,1,2,5,6,7]` / `[3,4,8,9]`, seat records `fallback is False`, house records
  `player_name is None` + neutral picks, replay magic `DERK` and version 2.
- CI evidence: `derks-gym smoke OK: end_reason=tick_cap winner=None final_tick=1200 replay=87568B`.
- Builder-documented deviation, implemented as claimed. **Not blocking.**

### F6 — `--band` is viewport-bottom-referenced and capped at 70 vh, not "controls height + 8"

- Where: `viewer/derk_chrome.js:485-507`
  ```js
  let band = Math.round(height + 8);
  if (box) {
    band = Math.max(band, Math.round(window.innerHeight - box.top + 8));
    band = Math.min(band, Math.round(window.innerHeight * 0.7));
  }
  root.style.setProperty("--band", band + "px");
  root.style.setProperty("--hudscale", String(scale));
  ```
- Design note §Transport rules says `--band` = `#controls`'s measured height + 8 px. The
  implementation is the documented deviation (commit `721c548`): on a narrow tall page the transport
  sits mid-viewport, so a height-only band let `inset: 0 0 var(--band) 0` cover the scrubber.
- Both variables are set on `document.documentElement` (`:root`), as checklist item 14(a) requires,
  and `relayout` runs on `load`, `resize`, `scroll` (passive) and after the draft overlay opens or
  closes (`derk_chrome.js:509-513`, `233`, `239`, `472`).
- Verified in CI, not just inferred: `#derk-draft stops above the transport band while shown
  (761 <= 807.640625)`, `#derk-endcard stops above the transport band (761 <= 807.640625)`, and at
  360×640 `no chrome element overlaps the transport band at 360px ([])`. **Not blocking.**

### F7 — the un-drafted `loadout_digest` is 2545393349, not 0

- Where: `sim/shim.c:18-22` (`static float g_applied[NUM_PLAYERS][8]`, zero-initialised),
  `sim/loadout_common.h:109-116` (FNV-1a over the whole 10×8 table),
  `server/cogame_derks_gym/catalog.py:209-226` (the Python mirror).
- Observed: FNV-1a over 80 zero float32s = **2545393349** (computed locally from
  `catalog.loadout_digest()`), which is what both an un-drafted server sim and a viewer that pushes
  nothing produce — so the cross-check still holds. Builder-documented deviation; implemented as
  claimed. `tests/test_loadout.py:85-116` asserts C == Python for the empty table, the neutral table
  and a drafted table, and that the three differ.
- One stale artefact of this change: `tests/test_viewer.py:271-273`'s docstring still reads "An
  un-drafted replay records loadout_digest 0"; the assertions on lines 283-285 use
  `catalog.loadout_digest()`. Comment only. **Not blocking.**

### F8 — the `--strict-text-bounds` canvas-text gate covers nothing on this viewer (`total: 0`), and there is no worst-case renderer fixture

- Where: `.github/workflows/ci.yml:248-252` (flag passed), CI log
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`.
- Observed: the renderer is raylib/WebGL through emscripten (`sim/build_viewer.sh:61-70`,
  `-sUSE_GLFW=3 -sUSE_WEBGL2=1`), so `viewer_smoke.mjs`'s 2D-canvas `fillText`/`strokeText` hook
  never fires. Per checklist item 15, "`total: 0` means the check covered nothing … and is not
  evidence of anything." The flag is also kept although the board is pannable (a 41×23-cell camera
  over 128×128 — §Zoom), where the checklist says to drop it and read the number; keeping it is
  strictly safer and green.
- The compensating facts, observed: the design note's own rule is "**No text is ever read off the
  canvas**" (§Legible at 360 px), and every readout is DOM. The only model-authored string that
  reaches the viewer is the seat `note`, rendered as DOM text via `textContent`
  (`viewer/derk_chrome.js:194`, `.derk-note` styled at `derk_chrome.css:255`), inside a scrollable
  `overflow: auto` overlay (`derk_chrome.css:208-217`) — it cannot be drawn at a negative coordinate.
  There is no `client/renderer.js` in this lineage and no worst-case renderer fixture. Legibility is
  instead gated by `tools/ci/derk_viewer_checks.mjs:325-353` at 360×640: scorebug 11.2 px, feed
  10.4 px, zero band overlaps (CI-observed values).
- Checklist item 15's fixture clause is written for repos whose **viewer draws** LLM text on a
  canvas; here it does not. Recorded so the judge can rule on it explicitly. **Not blocking on my
  reading**; the fixture requirement's trigger condition ("a repo whose viewer draws model text")
  is a judgement call I am flagging rather than deciding.

### F9 — `fallback_cause: "malformed"` is declared everywhere but emitted nowhere

- Where: `server/cogame_derks_gym/draft.py:44-45` (`FALLBACK_CAUSES`),
  `coworld_manifest_template.json:470-481` (the schema enum).
- Observed: `grep '"malformed"' server/ players/` returns only the engine's **NOOP** cause taxonomy
  (`engine.py:88`, `engine.py:273`) — no draft path ever assigns it; a non-JSON or non-object frame
  resolves to `wrong_shape` (`server.py:228-234`, `draft.py:171-176`).
- This matches the design note, which lists the same 7-value enum (§Replay format v2) while its
  resolution table (§The game, Phase B step 3) produces only 6 of them. Consistent with the note,
  recorded for completeness. `tests/test_manifest.py:100-106` pins enum == module. **Not blocking.**

### F10 — `EventLog._trim`'s last-resort branch would drop a just-added undroppable event

- Where: `server/cogame_derks_gym/events.py:56-68`
  ```python
  while len(self._events) > self._max:
      for kind in _DROPPABLE: …
      else:
          del self._events[self._max:]
          return
  ```
- Observed: with 400 undroppable events already present, `add_end(...)` would append the `end` record
  and then delete index 400 onward — i.e. the `end` event itself — contradicting the note's "`draft`,
  `first_blood`, `tower`, `ancient` and `end` are never dropped."
- Unreachable in practice (inference from the map constants, stated as inference): undroppable kinds
  are 1 `draft` + 1 `first_blood` + ≤24 `tower` (24 towers, no respawn, `moba.h`) + ≤2 `ancient` +
  1 `end` ≈ 29 ≪ 400. The droppable branch always finds a `level_spike` or `kill` first.
- **Not blocking**; recorded as a latent ordering in the cap logic.

### F11 — `docs/PORTING.md` was rename-passed although the note says "kept verbatim", and three of the renamed references point at files that do not exist

- Where: `docs/PORTING.md:63`, `:86`, `:91`
- Observed: the diff against the starter is nine lines, all `cogame_moba` → `cogame_derks_gym`
  renames. Three of them rewrote plan filenames: `docs/plans/2026-08-01-cogame-derks-gym-design.md`
  and `…-implementation.md` — neither exists; the repo's plan is
  `docs/plans/2026-08-28-derks-gym-design.md`. The design note (§Packaging, Docs) says
  "`docs/PORTING.md` kept verbatim from the starter".
- The manifest's `pages[1]` links this file (`coworld_manifest_template.json:567-574`), so the dead
  references are published documentation. **Not blocking** (no checklist item covers doc-internal
  links; item 10 only requires the `docs` shape, which is correct).

### F12 — `tests/test_fidelity.py` differs from the starter in two rename-only lines

- Where: `tests/test_fidelity.py:3` and `:33`
- Observed: full diff vs `/workspace/starters/cogame-moba/tests/test_fidelity.py` is
  `from cogame_moba.sim import …` → `from cogame_derks_gym.sim import …` and the two wasm filenames
  in the module docstring. **No assertion, tolerance, seed, tick floor or skip marker changed.** The
  rename is forced by the package rename the note itself mandates (§Files forked from the starter).
- Checklist item 1's "no test loosened": verified from `git log -p -- tests/` across all four commits
  of this run (below, "Traced and consistent"). **Not blocking.**

### F13 — a champion's `note` is forwarded unbounded by the player; only the 4096-byte frame cap stops it

- Where: `players/derk_player.py:166-169` (`legal_picks` copies `note` verbatim into the picks),
  `players/client.py:256` (frame sent as-is), `server/cogame_derks_gym/server.py:222-226`
  (oversize → whole seat neutral, before the JSON parse).
- Observed: the player performs no rune truncation of its own; the server truncates on receipt
  (`draft.py:72-89`). A model that emitted a >4 kB note would therefore lose its **picks**, not just
  its note. Unreachable in practice: `MAX_TOKENS = 400` (`derk_player.py:43`) bounds the whole reply
  to roughly 1.6 kB, and the system prompt asks for `"<=120 chars"` (`derk_player.py:66`).
- The design note assigns truncation to the server ("`note` … is truncated to 120 characters on
  Unicode-scalar (rune) boundaries" as resolution step 7), which is what the code does.
  **Not blocking**; recorded as an observed interaction between two caps.

### F14 — checklist item 11's literal selector/breakpoint do not exist in this lineage

- Where: `viewer/derk_chrome.css:118-125` and `:276-284`
- Observed: cogame-moba has no scorebug plates and no `.plate-name`. The equivalent rule here is
  ```css
  #derk-roster .derk-name { flex: 1 1 auto; min-width: 3.2em; … text-overflow: ellipsis; }
  ```
  — the exact `flex: 1 1 auto; min-width: 3.2em` pair the checklist names — and labels are hidden at
  `@media (max-width: 720px)` (`.derk-stat`, `.derk-role`, `.derk-deltas` → `display: none`), not at
  640 px. The intent (names do not collapse at the embedded featured-match width) is verified in CI
  at 360 px by `derk_viewer_checks.mjs:325-353`.
- Recorded so the judge does not read the missing `.plate-name` string as an absence.
  **Not blocking.**

### F15 — no grid harness for baseline tuning is present in the repo

- Where: repo-wide grep for a tuning/grid harness returns only `scripted_player.py`'s BFS *nav grid*
  and CSS `grid-template`; there is no `tools/tune_*`, and the starter has none either.
- Observed: neither scripted baseline has free numeric parameters to tune. `puffer-forge`'s draft is
  a fixed role table (`derk_player.py:85-92`) and its micro is the **vendored pretrained network**
  (`baseline_player.py` `MobaBrain` on `moba_weights.bin`); `lane-brawler`'s draft is three
  thresholds read off the observed base stats (`derk_player.py:105-116`) and its micro is the
  starter's `ScriptedPolicy`, inherited unchanged.
- Checklist item 7's first half is met (see "Traced and consistent"); its second half ("tuned with a
  grid harness, not guessed") has no artefact in this tree. Stated as an observation, not a verdict.

---

## Traced and consistent

**Provenance**

- `vendor/` — `diff -r` against the starter: **byte-identical**, all 12 files including
  `moba_weights.bin` and the render resources. Patch set unchanged at four
  (`sim/patches/0001..0004` identical), `sim/apply_patches.sh` and `sim/shim_common.h` identical.
- `tools/ci/viewer_smoke.mjs` — `diff` against `templates/tools/ci/viewer_smoke.mjs`: **byte-identical**
  (verbatim template, as the deviation claims).
- `tools/ci/docker_smoke.sh` — template verbatim through line 327 (only `<slug>`/`<IMAGE>`/`<SEATS>`
  substituted), with the game block appended at 328-452 under its own banner. All four seat-count
  invariants intact at `:105-151`.
- `.github/workflows/coworld-release.yml` / `coworld-submit.yml` — template verbatim, substitutions
  only (`diff` shows 4 and 1 comment lines respectively).
- `sim/build_sim.sh`, `sim/build_brain.sh`, `sim/brain_shim.c`, `tools/build_replay_viewer.sh`,
  `tools/ci/next_coworld_version.py` — starter's, rename-only diffs plus the documented
  `mkdir -p "$(dirname …)"` fix in the viewer hook (`tools/build_replay_viewer.sh:25-27`).

**Draft resolution rules** (design §The game, Phase B)

- 7-value `fallback_cause` enum: `draft.py:44-45`, mirrored in the manifest (`:470-481`) and pinned
  by `tests/test_manifest.py:100-106`.
- Whole-seat neutral on `unknown_item`: `catalog.normalized_picks` returns `None` on the first
  illegal slot (`catalog.py:163-178`) and `resolve_reply` substitutes the whole neutral pick set
  (`draft.py:180-183`). Cases covered in `tests/test_draft.py:107-136`: unknown id, right id/wrong
  slot, wrong case, >24 chars, missing slot — all `unknown_item`, and the neighbouring seat keeps its
  picks.
- Frame cap 4096 **before** the JSON parse: `server.py:222-226`; wire-level test
  `tests/test_draft.py:323-340` (6 kB note → `oversize`, `draft_fallbacks == [True, False×5]`).
- Case-sensitive exact match after stripping leading/trailing ASCII spaces: `catalog.py:152-160`
  (`item_id.strip(" ")`).
- `note` ≤ 120 runes, C0/C1 and lone surrogates stripped, never mid-codepoint: `draft.py:72-89`
  (Python slicing is by code point). Tests: a 4-byte emoji straddling index 120 kept whole, the same
  emoji dropped whole one char later, a combining sequence, control/surrogate stripping, a non-string
  note yielding `""` without invalidating the picks (`tests/test_draft.py:181-228`).
- House heroes 3, 4, 8, 9 get `source: "house"`, `player_name: null`, `seat: null`, `decision_ms: 0`,
  neutral picks: `draft.py:211-215`, asserted in `tests/test_draft.py:88-95` and in the smoke's
  house-record block (`docker_smoke.sh:427-432`).
- `apply_loadout` once per pid, ascending, after `c_reset`, before tick 0:
  `draft.apply_to_sim` sorts by pid (`draft.py:312-313`); the sim is constructed
  (`moba_init` = `moba_configure` + `allocate_moba` + `c_reset`, `sim/shim.c:23-30`) at
  `server.py:520` and the engine is not started until `server.py:544`.
- Un-drafted mode skips steps 1-6 entirely (`server.py:526-532`) and still writes ten records that
  describe the sim (`draft.neutral_records`), so the viewer needs no special case.

**Decision path**

- Anthropic Messages, `claude-sonnet-4-5`, `max_tokens: 400`, one call per episode, 20 s per-call
  timeout enforced twice (`asyncio.wait_for` at `derk_player.py:236-238` and
  `aiohttp.ClientTimeout(total=20)` at `:284`).
- Tolerant parse, exactly one code fence stripped: `strip_one_fence` (`derk_player.py:127-139`),
  including a ```` ```json ```` language tag. Tests `tests/test_llm_player.py:59-89`.
- One retry at `temperature: 0` with the reminder line appended to the system prompt
  (`derk_player.py:232-259`, `:261-274`); tests assert exactly two calls, the second carrying
  `temperature == 0` (`:109-118`).
- Second failure → `forge_picks` (puffer-forge's rule), logged
  `draft_fallback=scripted reason=<…>` (`derk_player.py:256-258`) — phase 60 can count it. Reason
  vocabulary is `timeout | parse | illegal | transport:<ExcName>`; the note names the first three,
  the transport case is a strict superset. No API key → no call at all, logged once
  (`:227-231`, test `:145-155`).
- Both baselines match their documented tables: `FORGE_BY_ROLE` (`derk_player.py:85-92`) is the
  note's table verbatim; `brawler_picks` (`:105-116`) is the note's four-line rule verbatim including
  `note = "brawl build"`. `docker_smoke.sh:400-425` re-derives both from the manifest and compares to
  the recorded picks.
- Env switch: `resolve_mode` (`derk_player.py:311-335`) — `PLAYER_PROMPT` wins with a stderr line,
  both unset → `puffer-forge`, unknown scripted or prompt name raises `PlayerError`, and `main()`
  returns **2** before anything expensive is built (`:351-359`). Tests `:231-263`.
- Two name spaces on the LLM path: the request body is the draft observation minus `deadline_ms`
  (`derk_player.py:172-177`); `tests/test_llm_player.py:157-170` asserts no real player name appears
  in any request body while the alias and catalog do.

**Every wait and its bound**

| wait | bound | where |
|---|---|---|
| connect | `player_connect_timeout_seconds` (default 60) | `server.py:488-493` (`asyncio.wait_for`) |
| draft | one `asyncio.gather` under one shared `draft_deadline_ms` (default 45 000) | `draft.py:268-278` |
| per-tick seat batch | one `asyncio.gather`, per-seat `asyncio.wait_for(deadline)` | `engine.py:235-238`, `:421-434` |
| strike rule | 10 consecutive → dead; dead seats cost **no** wall clock (non-blocking probe) | `engine.py:77`, `:227-245`, `:370-393` |
| revival | first valid reply resets strikes and cancels the stale probe | `engine.py:250-268` |
| engine hard stop | `wall_clock_budget_seconds`, timed from the draft | `engine.py:210-215`, `server.py:515`, `:543` |
| done send / draft_result push | `DONE_SEND_TIMEOUT_SECONDS = 3` per seat | `server.py:209-210`, `:829-830` |
| `/global` | fire-and-forget, per-socket serialised, never awaited by the episode | `server.py:411-444` |

- Arithmetic: `derived_wall_clock_budget_seconds` = `min(0.9·1200, draft_ms/1000 + max_ticks·tick_ms/1000)`
  (`defaults.py:175-185`) → 45 + 600 = **645** for the draft variant, and the draft term is dropped
  when `draft_enabled` is false (`config.py:147-151`) → 600 for `nodraft`. Both match the manifest
  (`:689`, `:723`). Worst case 60 + 45 + 600 = **705 < 720** (60 % of 1200); pinned by
  `tests/test_manifest.py:144-162` for every variant *and* the cert fixture.
- The tick loop's break order is exactly the note's Phase C step 1: `sim.done()` → `ticks_run >=
  max_ticks` → `elapsed >= budget` (`engine.py:202-215`). There is no unbounded loop and no blocking
  read anywhere in the episode path; the all-seats-dead case explicitly yields to the loop
  (`engine.py:227-234`).

**String truncation reaching the replay**

- `note` is the only free-text field in the protocol (`docs/DRAFT.md:132-136`) and the only
  player-authored string in the header; truncated on rune boundaries at `draft.py:72-89`.
- The header is serialised with `ensure_ascii` (default) so the slice always decodes with
  `errors="strict"` (`replay.py:154-167`), and the parser decodes strictly
  (`replay.py:196-202`). Tests: `tests/test_replay.py:250-285` (strict round trip, a flipped `0x80`
  byte → `ReplayError`, `header_len = 0xFFFFFFFF` → `ReplayError` with no wrap, ragged body).

**Replay writer**

- Magic `DERK`, version u8 = 2, `u32le header_len`, body `tick_count × 60`
  (`replay.py:59-62`, `:154-167`); layout asserted at `tests/test_replay.py:72-88`.
- Header keys present and complete: `format_version`, `sim_wasm_sha256`, `catalog_version`,
  `catalog`, `config` (seed + real names, **tokens excluded** — `config.py:201-217`), `aliases`,
  `seat_hero_pids`, `house_hero_pids`, `draft` (10 records with float32-exact `applied` blocks via
  `catalog.f32`), `loadout_digest`, `events`, `result`, `tick_count`, `final_state_digest`
  (`replay.py:136-152`; `tests/test_replay.py:217-247`).
- `append_tick` rejects non-sequential ticks, wrong shapes and out-of-range values before the uint8
  cast (`replay.py:111-134`).
- Event vocabulary is the closed seven (`events.py:30-34`), cap 400 with `level_spike` then `kill`
  dropped first (`events.py:56-68`), `draft` at tick 0 over `[0,1,2,5,6,7]` (`:70-71`), `end` last
  (`server.py:558`).

**Viewer re-derivation** (checklist item 2)

- `sim_fresh()` applies `g_loadout[pid]` for every flagged pid **immediately after `c_reset(&env)`**,
  ascending pid order — `sim/viewer_main.c:112-117` — the same placement and the same shared function
  (`derk_apply_loadout`, `sim/loadout_common.h:51-78`) the server shim uses (`sim/shim.c:146-159`).
- `viewer_set_loadout` is pushed from JS out of the header's `draft[].applied`
  (`viewer/derk_chrome.js:132-150`), then `viewer_seek(0)` re-simulates through that exact path.
  Un-drafted replays push nothing (`derk_chrome.js:133-138`), matching the server, and both sides
  then digest the all-zero table.
- `loadout_digest` cross-check with an on-screen warning appended to the starter's `#warn` element
  (`derk_chrome.js:152-163`), i.e. the same element and pattern as the sim-sha mismatch warning, as
  the note requires.
- Proved, not assumed: `tests/test_viewer.py:195-268` runs the headless core over a real recorded
  drafted episode and asserts `loadoutDigest == headerLoadoutDigest == sim.loadout_digest()`,
  `stateDigest == sim.state_digest()`, and that `viewer_ancient_health`, `viewer_agent_stat` and
  `viewer_hero_positions` equal the server sim's values at the same tick.
  `tests/test_replay.py:298-342` re-simulates a real 400-tick server episode **from the replay bytes
  alone** and asserts final tick, `state_digest` and `loadout_digest`.
- Link flags: the browser build is `-sENVIRONMENT=web` with **no** `MODULARIZE`/`EXPORT_NAME`
  (`sim/build_viewer.sh:61-70`) and the shell keeps the matching `var Module = {canvas,
  onRuntimeInitialized, printErr, onAbort, onExit}` bootstrap with `<script src="derk_viewer.js">`
  last (`viewer/index.html:283-297`). The `MODULARIZE=1 / EXPORT_NAME=createViewerCore` pair exists
  only on the separate node build (`build_viewer.sh:93-102`). `tests/test_viewer.py:90-106` pins the
  split. CI: `{"loaded":true,"ms":595,…}` — the smoke's `loaded: true`, which is the evidence the
  checklist asks for.
- Markers: `data-replay-loaded="true"` on the first drawn frame after `viewer_load` succeeded and
  `Module.canvas.width > 0` (`derk_chrome.js:605-611`, called from the shell's `refreshUi` at
  `index.html:170`); `data-replay-error` set from every shell failure path — fetch/parse/`viewer_load`
  −1/tick-count mismatch via `derkFail` (`index.html:275-286`), `onAbort` and `onExit`
  (`index.html:291-292`).
- Chrome block: appended `<div id="derk">` after the starter's `#teams` under the banner comment
  (`index.html:73-115`); every new id is `derk-`-prefixed; every starter id survives
  (`tests/test_viewer.py:69-88` enumerates them).
- `#derk-draft` and `#derk-endcard` both use `position: fixed; inset: 0 0 var(--band) 0`
  (`derk_chrome.css:208-217`); **every** seek dismisses them — `input`, `pointerup`, `keyup` and
  `change` handlers all call `derkDismissEndcard` (`index.html:251`, `:256`, `:262`), which also
  hides the draft overlay (`derk_chrome.js:475-481`); the beats seek through the starter's own
  `change` path (`derk_chrome.js:390-395`).
- Scrubber beats are labelled `<button>`s with `aria-label="<kind> at tick <n>"` that seek to their
  tick (`derk_chrome.js:422-435`), with CSS for **all seven** kinds plus the `+n` collapse chip
  (`derk_chrome.css:196-203`); `tests/test_viewer.py:118-121` iterates `events.KINDS` against the CSS.
  CI: 15 beats rendered, every one labelled, last click moved `#tickinfo` `0 / 1200 → 1195 / 1200`.
- `#derk-viewpanel` is kept, with seven camera buttons calling `viewer_set_camera` and carrying
  `aria-pressed`, plus a 128×128 minimap redrawn from `viewer_hero_positions` with the camera window
  outlined (`index.html:99-103`, `derk_chrome.js:281-371`, `viewer_main.c:376-392`). The board is
  larger than the frame (41×23 cells of 128×128), so the note's condition for keeping the panel holds.

**Manifest**

- `num_agents: 6` inside `variants[0].game_config`, `variants[1].game_config` and
  `certification.game_config` (`:682`, `:717`, `:769`); **absent** from every variant top level;
  pinned by `tests/test_manifest.py:127-137` and cross-checked by `docker_smoke.sh` before any
  container starts. **No `SEAT-COUNT FAIL` anywhere in the docker-smoke log** (grepped: 0 hits).
- `replay_viewer: {"bundle": "static-replay-viewer"}` (`:12-14`); `tools/build_replay_viewer.sh`
  present, executable (asserted at `ci.yml:159-170`), and it builds the Dockerfile's `wasm-builder`
  target. No `/client/replay` pod path is declared anywhere in the manifest; the server's own
  `/client/replay` route is local viewing only, as in the starter.
- `episode_timeout_minutes: 20` at manifest top level (`:9`), mirrored in
  `defaults.PLATFORM_EPISODE_TIMEOUT_MINUTES` (`defaults.py:172`).
- `protocols` carries **both** `player` and `global` (`:543-552`); `docs` carries `readme` plus two
  `pages` with `id`/`title`/`content` (`:553-576`).
- `certification.players` seats every declared player (F4); `drafter` carries
  `ANTHROPIC_API_KEY_URI: secret://coworld/derks-gym/anthropic_api_key` (`:640-643`), pinned by
  `tests/test_manifest.py:264-278`.
- `results_schema` is closed (`additionalProperties: false`) with exactly the 16 keys
  `_results_doc` emits, and `docker_smoke.sh`'s `expected` set is the third leg — all three compared
  in `tests/test_manifest.py:70-91`. `end_reason` enum == the engine's four literals (`:93-98`).
- `tools/ci/policies.json`: four distinct policies, two `PLAYER_PROMPT` champions with champion #2
  carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, two `PLAYER_SCRIPTED` fillers, all
  running `/bin/derks-gym-player` (which the Dockerfile creates at `:84-88`). Pinned by
  `tests/test_manifest.py:279-298`.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`, `coworld-release.yml`,
  `coworld-submit.yml`, `docker_smoke.sh`, `policies.json` → **no matches** (gate exits 0).

**Tests** (design §Tests, item by item)

1. `test_fidelity.py` — inherited, rename-only (F12).
2. `test_loadout.py` — zero-loadout identity over 500 ticks comparing obs bytes, rewards and
   `state_digest` every tick (`:59-82`); per-item deltas through `hero_stat` (`:122`); clamps over all
   64 combinations × 5 roles (`:166`); survive death and level-up (`:209`); no RNG (`:253`);
   boundary validation (`:187`).
3. `test_catalog.py` — exactly 12 ids, slot-prefix rule, every delta field regex-checked against
   `vendor/upstream/moba.h`, `*_none` zero-delta, no item lowers `move_speed`, an `item-<id>` symbol
   per id in `derk_items.svg` (all 12 present), and the catalog sha256
   `7c80ff58…aef7` matching the manifest and `docs/DRAFT.md` (recomputed locally: identical).
4. `test_draft.py` — every resolution row, simultaneity (no observation carries any `picks` key),
   and the two-name-space assertion (no `real-name-N` in any observation), plus wire-level oversize,
   non-JSON, closed-socket, wrong-phase-does-not-consume-the-turn and second-message-ignored cases.
5. `test_baseline.py` — bounded orders for both baselines over 300 live ticks with
   `engine._sanitize` non-`None` every tick (`:158-184`), draft legality for all ten role/hero
   combinations plus clamp containment (`:187-212`), and a full websocket episode run to its natural
   end asserting `end_reason ∈ {ancient, tick_cap}`, `scores == [1,1,1,0,0,0]`,
   `dead_seats == [False]×6` (`:106-151`).
6. `test_llm_player.py` — stubbed transport: valid, fenced, malformed→retry→fallback, timeout,
   transport error, missing key (no call), and the no-real-name assertion.
7. `test_replay.py` — e2e through the **server** with six scripted seats, re-simulated from the bytes
   alone; header completeness; strict-UTF-8 and the three negative tests.
8. `test_viewer.py` + `viewer_core_harness.js` — malformed-bytes rejection table (incl. v1 `MOBA`
   magic and the wrapping `header_len`), cadence/pause/seek/phase-lock, digests, bundle file list.
9. Inherited suites updated for six seats and the draft phase (`test_server.py` 1078 lines,
   `test_engine.py` 833, `test_players.py`, `test_scripted.py`, `test_startup.py`, `test_vendor.py`,
   `test_sim.py`, `test_config.py`).
10. `test_manifest.py` — every tripwire the note lists, plus the two added in `70db559`.

- **No test loosened during this run** (checklist item 1, second half), verified from
  `git log -p -- tests/` across all four commits: `8b7e527` creates the suite; `74fcfc7` *adds*
  assertions to `test_loadout.py` (C↔Python digest mirror, a third drafted case) and corrects two
  assumptions (derived budget now includes the draft; un-drafted digest is the FNV of zeros, not the
  literal 0) plus makes four inline websocket clients skip phase messages; `721c548` makes those
  clients *answer* the draft and adds an explicit `wall_clock_budget_seconds` to the shared test
  config; `70db559` adds two new manifest tripwires and tightens the `drafter` env assertion. No
  deleted assertion, no widened tolerance, no `skip`/`xfail` added, no test file removed. Both wasm
  gates are hard-failed rather than skipped under `COGAME_REQUIRE_WASM_BUILD`, which `ci.yml:80-82`
  sets (`test_loadout.py:32-42`, `test_viewer.py:51-56`).

**CI** (run 33166095890, all four jobs green on `main` at the reviewed sha)

- `test`: `333 passed in 66.15s`.
- `docker-smoke`: image built, 6 player containers all exited 0, `episode end reason: tick_cap`,
  `smoke OK: seats=6 results=11159B replay=87568B`, then the game block's
  `derks-gym smoke OK: end_reason=tick_cap winner=None final_tick=1200 replay=87568B picks=[…]`.
  No `SEAT-COUNT FAIL` in the log.
- `wasm-viewer`: `needs: docker-smoke` (`ci.yml:146`); it downloads the `smoke-replay` artifact
  (sha matches the uploaded one) and **executes** the bundle in headless chromium —
  `Load the bundle in a real browser` ran, no `continue-on-error`, output
  `{"loaded":true,"ms":595,…}`; then `Assert the derks-gym chrome` printed 16 `ok` lines and
  `all derks-gym chrome checks passed`.
- `upload-coworld`: `needs: [test, docker-smoke, wasm-viewer]` (`ci.yml:314`), main-only,
  `concurrency: upload-coworld`, version from `tools/ci/next_coworld_version.py derks-gym`. It
  warned and skipped on the exact bootstrap message
  (`derks-gym has no registry rows yet; the first version is published by coworld-release.yml`) —
  the documented narrow warn-and-skip at `ci.yml:366-378`, which greps for `"no rows for coworld"`
  and re-raises anything else.
- `coworld-release.yml` step order: `Build the Coworld manifest` (:159) → `Certify locally` (:173) →
  `Upload the policies` (:216) → `Upload the Coworld` (:314) → `Put the Coworld secret` (:410).

---

## Could not determine

- **Whether F1 (collective draft timeout) has ever fired in practice.** It cannot be triggered by any
  CI path: the smoke's seats are scripted (instant) and the cert fixture's `draft_deadline_ms` is
  5 000 ms. Settling it in the wild would need a ladder episode log showing six `draft fallback to
  the neutral loadout (cause=timeout)` lines with only one slow seat, or a test that asserts a fast
  seat keeps its picks while another seat hangs past the deadline.
- **Whether checklist item 15's worst-case-renderer-fixture clause applies here** (F8). Its trigger is
  "a repo whose viewer draws LLM-authored text"; this viewer renders the only model-authored string
  (`note`) as DOM `textContent`, not on the canvas, and there is no `client/renderer.js` in the
  cogame-moba lineage. A judge ruling either way is defensible; what would settle it is an explicit
  reading of whether "draws" covers DOM chrome. Evidence in hand: `canvas_text total: 0` (so the
  canvas gate is vacuous) and CI-measured DOM font sizes 11.2 px / 10.4 px at 360 px with zero band
  overlaps.
- **Checklist item 7's "tuned with a grid harness, not guessed"** (F15). Neither this repo nor the
  starter contains a tuning harness; the baselines expose no free numeric parameters. What would
  settle it: a statement in the design note or a `tools/` harness; neither exists.
- **The hosted certification outcome.** `coworld-release.yml` has not run (`upload-coworld` skipped
  for want of a registry row), so `coworld certify` has never been executed against this manifest —
  only `tests/test_manifest.py` and `docker_smoke.sh` have. Settled by the first release run.
- **The `--strict-text-bounds` flag's future behaviour if a 2D-canvas overlay is ever added.** Today
  it gates on a metric that is structurally 0 for a WebGL renderer.
