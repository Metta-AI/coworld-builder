# r2 review — collab-cooking

Head reviewed: **`a5ec2c8602856d21ad8ec3e4f70af7c6fab82ede`** (`main`, 2026-08-24 23:17:45 -0700)
Range: `6b081b1..a5ec2c8` (the ten r1 fix commits). **No commit has landed since the r1 verdict** —
head is byte-for-byte the sha the r1 judge ruled on, so the one standing blocking finding is
re-verified below at the same commit rather than at a new one.
Files read: 34   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
CI at head: run **32816344271**, conclusion `success`; `test` (200 passed / 1 skipped),
`docker-smoke`, `wasm-viewer` (including `Load the bundle in a real browser`) all green — read from
`gh run view 32816344271 --json jobs`, not carried from r1.

Method note: for the DOM findings below I did not reason from the CSS alone. I spliced the real
`client/chrome_common.js` over the committed page's `<!-- CHROME_COMMON -->` marker (what the bundle
build does), stubbed `CcStaticReplay.createCore` to capture the game block's own `onText`, and drove
the page's real `ccSayBar`/`renderFeed`/`relayout` in headless chromium 1.55.0 with a frame carrying
a full-cap 120-rune `say` on every seat. Every number labelled *measured* comes from that run;
numbers labelled *inferred* are arithmetic I did not execute.

---

## Blocking

### R2-O1 — the say band still clips a full-cap remark; unchanged at head, and now measured

- Where: `client/parts/game.css:94-106` (`#saybar .say-chip`), specifically `:99`
  `max-height: calc(22 * var(--u))` and `:100` `overflow: hidden`; generated page
  `client/replay_broadcast.html:1555-1567`; renderer `client/parts/game.js:95-106` (`ccSayBar`),
  page `:1880`.
- Observed (code): the chip is
  ```css
  #saybar .say-chip {
    flex: 1 1 0;
    min-width: 0;
    font-size: calc(8.5 * var(--u));
    line-height: calc(11 * var(--u));
    max-height: calc(22 * var(--u));
    overflow: hidden;
  ```
  `ccSayBar` writes the whole string with no truncation, no `title`, no ellipsis:
  `esc(say || 'no word yet')` (`game.js:103`). The server cap is `SAY_RUNES = 120`
  (`src/collab_cooking/coworld/plans.py:28`), applied at `plans.py:191`, and the Nim module hands the
  full 120 runes to the DOM (`replay-viewer/collab_cooking_replay.nim:852`,
  `truncRunes(seatSay[index], SayRunes)`, `SayRunes = 120` at `:46`). The comment directly above the
  rule (`game.css:81-82`) says "The say band is sized from the 120-rune cap"; `120` appears nowhere
  else in the file and nothing in the sizing derives from it.
- Observed (measured, headless chromium, real page, four full-cap says):

  | viewport | `#stage` width | `--hudscale` | chip width | line-height | chip `clientHeight` | chip `scrollHeight` | hidden |
  |---|---|---|---|---|---|---|---|
  | 1280×800 | 913 px | 1.201 | 216 px | 13.12 px | 26 px | 58 px | **55 %** |
  | 900×558 | 638 px | 0.839 | 152 px | 9.23 px | 18 px | 40 px | **55 %** |
  | 640×397 | 447 px | 0.588 | 107 px | 6.47 px | 13 px | 28 px | **54 %** |
  | 360×640 | 360 px | 0.500 | 86 px | 5.50 px | 11 px | 24 px | **54 %** |
  | 360×223 (letterboxed) | 162 px | 0.500 | 36 px | 5.50 px | 11 px | 57 px | **81 %** |

  `clippedY` is `true` at every width. A full-cap remark needs ≈ 4.3 line boxes in its chip; the box
  shows 2. There is no scrollbar (`overflow: hidden`), no ellipsis, and no `title` attribute, so the
  clipped runes are not recoverable by hover either.
- Checklist item: **15**, the DOM branch the r1 judge applied — "Any text laid out relative to
  another element … gets a **reserved band in the layout**, sized from the cap the server enforces on
  that string (`MaxSayLen` and its kin) and measured in the font it will be drawn in. Sizing by eye …
  is the bug above." Also its ellipsis rule: a shortened *remark* means "the box is too small — widen
  the band, do not shorten the text."
- Why blocking: the last ~55 % of every full-cap LLM remark is invisible at every viewport width in
  the `--hudscale` clamp band, including the 360 px featured-match iframe the design names as a
  target (`design.md:1036-1038`). No gate can see it — see R2-O3.
- One half of the design's claim *does* hold, measured: the band does not jump. `#saybar` measures
  28.8 px empty and 29.0 px with four full-cap says at 1280×800, and `--topband` stays `158px`, so
  the board never moves (`design.md:1028-1029`). The stability was bought by the clip, not by sizing
  from the cap.

### R2-O2 — the feed's `say` line is laid out `nowrap` and runs off the clipped stage (new)

- Where: inherited starter rule `client/replay_broadcast.html:488-504` (`.feed-row`, `white-space:
  nowrap` at `:503`, `max-width: none` at `:502`); game block `client/parts/game.css:110-136`
  (`#feed`, page `:1571-1597`); renderer `client/parts/game.js:150-160` (`renderFeed`); `#stage`
  `overflow: hidden` at `client/replay_broadcast.html:84`.
- Observed (code): the game block reuses ctf's `.feed-row` class name for its own rows
  (`game.js:155`, `row.className = 'feed-row ' + (line.kind || 'info')`). The starter's `.feed-row`
  rule sets `white-space: nowrap; max-width: none;` and its own comment explains why that was safe
  *there*: "rows are right-anchored (align-items:flex-end on #killfeed) so a long row grows leftward —
  bounded by the small font + the pre-bounded 10-char name, so it can't run away"
  (`replay_broadcast.html:499-502`). The game's `#feed` (`game.css:110-121`) sets `flex-direction:
  column` but **not** `align-items: flex-end`, and its rows carry whole sentences, including
  `"<alias>: <say>"` (`collab_cooking_replay.nim:678-679`). Nothing in the game block overrides
  `white-space`.
- Observed (measured, 1280×800, one feed line = `Cog-A: ` + a 120-rune say):
  ```
  whiteSpace: "nowrap"   maxWidth: "none"   #feed align-items: "normal"   #stage overflow: "hidden"
  row box:  left 834.1  right 1086.3   (252 px wide)
  text:     left 843.3  right 1468.9   (625.6 px wide, one single line)
  #stage:   left 183.5  right 1096.5
  → 372.4 px of the line sits past the right edge of #stage, which is overflow:hidden
  → 59.5 % of the rendered remark is clipped away
  ```
  The same probe with the five feed strings a scripted-only episode can actually produce is entirely
  inside the stage at 1280×800 and at 900×560 (`Cog-C serves soup - dish 9` −109 px,
  `Cog-A leaves chopped meat on the counter` −18 px, `ticket salad expires - nobody served it`
  −47 px, `Cog-B fell back to brigade - illegal_station` −28 px, `the pot burns - nobody plated it`
  −81 px; negative = inside). Only the model-authored line overflows.
- Checklist item: **15** — "text with nowhere to go is invisible to the load signal, to the soak,
  and to a screenshot"; and the last bullet, which names exactly this class ("the whole class of
  chrome that exists only to show what a model said is untested by every gate above").
- Why blocking: the feed is the *other* surface for a remark, and it clips ~60 % of one for the same
  reason the say chip clips ~55 % — an inherited rule sized for ctf's 10-char names carrying this
  game's sentences. Together with R2-O1 there is no surface in the viewer on which a full-cap remark
  is fully legible.

### R2-O3 — no fixture, test or static check pins any DOM text band against its rune cap, and the CI replay is confirmed to carry zero model text

- Where: `tests/test_viewer_contract.py` (17 tests, `:55-215`); the closest is
  `:139` `test_plate_css_survives_the_360px_featured_match_iframe`, a substring grep over the CSS for
  `.plate-name`. No test renders a `say`, measures an element, or references `SAY_RUNES`
  (`grep -rn 'saybar\|say-chip' --include=*.py` returns exactly one hit,
  `tests/test_viewer_contract.py:109`, an id-presence list). `.github/workflows/ci.yml:243-248` runs
  `viewer_smoke.mjs … --strict-text-bounds` against the docker-smoke replay and nothing else.
- Observed (evidence from the head artifacts, not inference): I downloaded the head
  `smoke-replay` artifact (run 32816344271) and parsed it —
  ```
  results.json: reason=complete dishes=11 llm_requests=0 fallbacks=[2,0,0,0]
                seat_kinds=['prompt','scripted:brigade','scripted:passer','scripted:courier']
  replay.json:  480 ticks, plan events = 0, plan events carrying a say = 0
  ```
  and the browser step's own line: `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed
  an edge), 0 ellipsized (--strict-text-bounds)`. So `canvas_text.total == 0` — which checklist 15
  states "means the check covered nothing … and is not evidence of anything" — and the replay the
  gate runs on provably contains no `say` at all.
- Observed (the gate structurally cannot see either DOM finding): `tools/ci/viewer_smoke.mjs` (709
  lines) instruments exactly two functions — `wrap("fillText")` and `wrap("strokeText")` at
  `:414-415`, measured against their own canvas at `:323` and reported as `canvas_text` at `:632`.
  There is no `scrollWidth`/`clientHeight`/`getBoundingClientRect` probe anywhere in the file, so no
  DOM overflow — R2-O1's `overflow: hidden` chip or R2-O2's off-stage row — is visible to it even if
  the replay did carry a `say`.
- Checklist item: **15**, final bullet: "**The CI replay cannot talk** … A repo whose viewer draws
  LLM-authored text must therefore ship a **worst-case renderer fixture**: a page that … hands it a
  frame built to hurt (a full-cap remark on *every* seat at once …), renders it at several canvas
  sizes, sets `data-replay-loaded`, and is driven by `viewer_smoke.mjs --strict-text-bounds` in its
  own `ci.yml` step. The fixture asserts its own strings are still full-length … a repo that draws
  model text and has no such fixture is a blocking `legibility` finding."
- Why blocking: the checklist makes the missing fixture blocking on its own terms, and it is the
  mechanism by which R2-O1 survived a full round and R2-O2 was never seen at all. The harness I
  wrote for this review (real page + real `ccSayBar`/`renderFeed` + a four-seat full-cap frame) is
  the shape of check that would catch both; nothing equivalent exists in the tree.

---

## Non-blocking

### R2-O4 — the feed line is rune-truncated to 120 *including* the alias prefix, so it can never carry a full-cap say
- Where: `replay-viewer/collab_cooking_replay.nim:678-679` (builds `alias & ": " & say`) and `:870`
  (`truncRunes(line.text, 120)`); the same shape server-side for `/global` at
  `src/collab_cooking/coworld/live_episode.py:571` and `:808`.
- Observed: the composed line is `"Cog-A: "` (7 runes) + up to 120 runes of say = up to 127 runes,
  then cut to 120 — so the last 7 runes of a full-cap remark are dropped before CSS ever sees the
  line. `say` itself is unaffected in `seats[].say` (`:852`) and in the replay's `plan` event
  (`plans.py:102-116`).
- What the checklist says: item 15's "widen the band, do not shorten the text" is written against the
  `ellipsized` counter on canvas draws, so I do not read this as an independent falsification. It is
  recorded because it removes the "read it in the feed instead" mitigation for R2-O1 and because
  anyone widening the say band has to decide about this line too.

### R2-O5 — under 640 px the feed is hidden, leaving the clipped chip as the only surface for model text
- Where: `client/parts/game.css:181-185` (`@media (max-width: 640px) { … #feed { display: none } }`),
  page `:1642-1646`.
- Observed (measured at 360×640): `#feed` computed `display: none`, `#scorebug .plate .plate-policy`
  `display: none`, `.plate-name` 92 px wide and not clipped (`scrollWidth == clientWidth`). The
  scorebug half of this is exactly what checklist item **11** asks for and it passes; the note is
  only that at the design's own 360 px target (`design.md:1036-1038`) the say chip is the sole
  remaining place a remark appears, and it shows 11 px of a 24 px line box.

### R2-O6 — the chrome-JSON cap is documented as 4 KB and enforced at 16 KB
- Where: `replay-viewer/collab_cooking_replay.nim:45` (`ChromeCap = 4000 # the state JSON is <= 4 KB`)
  vs `:926` (`if result.len > ChromeCap * 4:`).
- Observed: the guard fires at 16 000 bytes, four times the documented figure, and its only remedy is
  to drop `beats`. `design.md:930-932` says the object is "≤ 4 KB". Inferred, not measured: with
  `MaxHeatTiles = 400` (`:41`) the `heat` array alone can approach 5 KB, so the emitted label
  routinely exceeds the documented cap without ever reaching the guard. No functional consequence
  found: `broadcast_core.js:97` reads the label length as a u16 (65 535 max), so 16 KB transports
  fine. Not a checklist item.

### R2-O7 — the "Jam at the doorway" beat is placed by a different quantity than its comment claims
- Where: `replay-viewer/collab_cooking_replay.nim:598-612`.
- Observed: the comment says "marks the busiest doorway once, at the tick the heat peaks". The code
  takes `bn` = the busiest *tile's* total blocked count (`:600-603`), then walks the ticks
  accumulating `running` = **every** blocked event anywhere (`:606-609`) and places the beat at the
  first tick where `running * 2 >= bn`. On the head smoke replay: `bn = 87`, total blocked = 359, and
  the beat lands at **tick 36 of 480** — the first 7.5 % of the episode, not the heat peak. The beat
  kind has CSS (`game.css:206`) and a label, so item 14(d) is satisfied; only the placement is off.
  Not a checklist item.

### R2-O8 — serve/expire disambiguation and per-serve recipe attribution are count-based, not identity-based
- Where: `src/collab_cooking/coworld/replay.py:258-266` and `:343-351` (`_served_recipe`).
- Observed: tickets that left the board are matched to serves by *count* (`served_now -= 1` over the
  sorted set of departed tickets), and `_served_recipe` returns the first departed ticket in sorted
  order for **every** serve in that tick. Inferred consequence: a tick carrying two serves, or one
  serve plus one expiry, can attribute the wrong recipe and can log an expiry as a serve or vice
  versa, which would move `results.served_by_recipe` and `results.orders_expired`. **Not observed at
  head**: on the smoke replay there were 0 ticks with more than one serve and 0 ticks with a serve and
  an expiry together, and the event-derived recipe counts equal `results.served_by_recipe` exactly
  (`{'soup':5,'salad':4,'fries':2}`). Latent, not live. Not a checklist item.

### R2-O9 — dead starter CSS for removed elements survives in the inherited head
- Where: `client/replay_broadcast.html:470-522` (`#killfeed`, `.feed-row` and its children),
  `:1427` (`#stage.tiny #killfeed`), plus the `#viewpanel`/`#zoom-*` rules the r1 judge listed.
- Observed and re-verified: the markup is gone (`grep 'id="viewpanel"|id="killfeed"|id="fpv|
  id="lockerroom"|attachMinimap'` over the page returns nothing) and `test_the_page_dropped_the_
  ctf_specific_elements` pins that. The r1 judge ruled this harmless residue, and mechanically it is —
  except that the surviving `.feed-row` rule is not dead at all, because the game block reuses the
  class. That live half is R2-O2; this entry records the rest.

### R2-O10 — `player.py` hard-codes the prompt seat's fallback baseline (r1-O15, carried forward and re-verified)
- Where: `src/collab_cooking/coworld/player.py:162`,
  `baseline = register.get("baseline", DEFAULT_BASELINE) if register["kind"] == "scripted" else DEFAULT_BASELINE`.
- Observed: a prompt seat always executes `DEFAULT_BASELINE` (`brigade`) when no plan is in force,
  regardless of `config.fallback_scripted`, which the game side does honour
  (`live_episode.py:401`, `:470`). Diverges only under a non-default `fallback_scripted`; nothing
  shipped sets one (all eight variants and the cert fixture omit it). Advisory, as in r1.

### R2-O11 — a test's name overstates what it asserts
- Where: `tests/test_baselines.py:165-175`,
  `test_every_baseline_name_is_selectable_and_distinct_from_the_default`.
- Observed: it resolves each baseline's role at slot 3 and asserts
  `brigade == runner == passer == "all_rounder"`, `courier == "server"` — i.e. three of the four are
  identical at that slot, which is correct behaviour (`passer` differs by zone/handoff, not by role)
  but is the opposite of "distinct from the default". Naming only; the assertions are real and were
  not weakened. Not a checklist item.

### R2-O12 — `__pycache__/` and `.pytest_cache/` are committed
- Where: `src/collab_cooking/coworld/__pycache__/`, `src/collab_cooking/agent/brain/__pycache__/`,
  `.pytest_cache/v/cache/nodeids`, and six more directories (`git ls-files`).
- Observed: unchanged from r1. Hygiene only.

---

## Traced and consistent

The r1 fix areas the brief named, each re-verified at head from the code and, where an artifact
could settle it, from the head `smoke-replay` artifact I downloaded rather than from the r1 reports.

- `tools/build_manifest.py` + `coworld_manifest_template.json` — I ran `python3 tools/build_manifest.py`
  over a copy of the committed file: **regenerates byte-identically** (`git status` clean afterwards).
  I then installed `coworld==0.1.42` locally and ran the repo's own gate,
  `tools/ci/check_manifest_loads.py`, which calls the real
  `coworld.bundle._load_template_manifest`: `manifest OK: … game.replay_viewer.bundle=
  static-replay-viewer, game.owner=daveey@softmax.com`. Parsed shape: no top-level `version`, no
  `game.display_name`, `game.owner` present, `game.replay_viewer = {"bundle":
  "static-replay-viewer"}`, `game.protocols` carries `player` **and** `global` each as
  `{type,value}`, `game.docs.readme` is `{type:"text",value}` and all four `pages[]` are
  `{id,title,content:{type,value}}`, `results_schema.reason` enum is exactly
  `["complete","deadline","no_players"]`, `episode_timeout_minutes: 20`. (items 3, 10)
- `num_agents` — 4 in all eight variants, in `certification.game_config`, in
  `config_schema` (`minimum: 4, maximum: 4`, `tools/build_manifest.py:125`),
  `len(certification.players) == 4`, `len(certification.game_config.players) == 4`; the generator
  derives all of them from one `NUM_AGENTS = 4` (`build_manifest.py:31`).
  `tools/ci/docker_smoke.sh:106-151` enforces all four invariants with `SEAT-COUNT FAIL:` before any
  container starts, and cross-checks `SMOKE_SEATS` (`ci.yml:109`, `"4"`) at `:141-149`.
  `grep -c 'SEAT-COUNT FAIL'` over the full head CI log (3 121 lines, pulled with `gh run view --log`)
  = **0**; the log carries `game=collab_cooking seats=4 …` and `smoke OK: seats=4 … reason=complete`.
  (item 6)
- `tests/test_rederivation.py` — read in full. `rebuild()` (`:66-115`) builds a **fresh**
  `Simulator` from the replay's own `config`/`seed`, replays each tick's recorded action
  (`:85-88`), re-captures (`:89`), re-derives events (`:90`), re-derives the blocked flag bit from
  the sim while reading the two wire-only bits back from the recording (`:94-99`), and re-splits the
  out-of-band events so only derived ones are under test (`:106-113`). The comparison
  (`:118-131`) covers `t`, `c`, `st` **including presence** (the omit-when-unchanged rule), `sc` and
  `ev` in order. The non-vacuity test (`:134-141`) pins 240 ticks, >100 event-bearing ticks, >100
  `st`-bearing ticks and >2 carried-item kinds. Both tamper tests are real: `:150-156` shifts one cog
  one tile from tick 120 on, `:159-170` deletes one derived event, and each asserts
  `pytest.raises(AssertionError)`. All five PASSED in the head run. (item 2)
- `live_episode.py` pause/deadline — `:414-423`: the pause branch evaluates `self._deadline_reached()`
  and settles `"deadline"` *before* `asyncio.sleep(0.05)`, so a spectator `pause` cannot park the
  episode past the guard. `_deadline_reached` (`:449-451`) is `monotonic() - process_start >=
  0.6 × 1200 = 720 s`, anchored at process start, and is also checked inside `_wait_for_roster`
  (`:457`). Every other wait is bounded: roster `process_start + 120 s` (`:455`), registration grace
  `REGISTER_GRACE_SECONDS` (`:462`), action wait `asyncio.wait_for(…, policy_action_timeout_seconds)`
  (`:474-486`), pacing sleep (`:441-443`), shutdown grace `asyncio.sleep(20)` (`:977`). Server side:
  `urlopen(…, timeout=30)` on both artifact paths (`server.py:59`, `:74`); the `/global` sender loops
  on `episode.done` then `episode.exited` (`server.py:226-234`), both of which the settle path sets.
  Player side: `connect_with_retry` bounded at `CONNECT_RETRY_SECONDS = 60` with capped backoff
  (`player.py:136-156`), and `main()` swallows any exception and `sys.exit(0)` (`:191-197`).
  I found no unbounded loop and no blocking read. (item 5)
- heat — `replay.py:323` keys `heat` by the cog's own tile, the same tile the `blocked` event carries
  (`:324-333`). On the head artifact the two agree **tile for tile**: 19 tiles, 359 blocked events,
  `{(x,y): n for x,y,n in replay["heat"]} == Counter(event tiles)` is `True`. The viewer accumulates
  the overlay from the events (`collab_cooking_replay.nim:666-669`) and reads the document's `heat`
  only to pick the busiest tile for the jam beat (`:565-568`, `:599-603`). (r1-O4)
- `expires` — `replay.py:429-439` writes each live ticket's absolute expiry from
  `build_ticket_specs` via `ticket_expiries` (`:148-155`), i.e. the engine's own schedule. On the head
  artifact all 602 ticket entries carry `expires >= 0`. The clock readout derives `EXPIRING` from it
  (`collab_cooking_replay.nim:884-886`, `expires - tick <= 12`) and the head browser log reads
  `TICK 242 OF 480 3 ORDERS LIVE · 1 EXPIRING`. (r1-O5)
- event order — `replay.py:334-339` stable-sorts each tick's derived events into `DIFF_ORDER`. On the
  head artifact: **0** ticks out of 480 carry derived events out of order, no slot-tie inversions, and
  no event name outside `EVENT_NAMES`. Out-of-band events are prepended as a block by
  `_record` (`live_episode.py:519-522`) / appended by `_push_event` (`:578-590`), which is what
  `test_rederivation.rebuild` accounts for. (r1-O7)
- `docker_smoke.sh` healthz gate — `:221-239`: probes `/healthz` from inside the game container,
  bounded at 120 s, fails hard if the container exits first or the deadline passes, and only then
  starts the players. Player exits are checked individually with a 60 s bound (`:270-290`). Head log:
  `waiting for /healthz … → game is serving /healthz; starting 4 player containers → every player
  container exited 0`; head artifact `disconnected: [false,false,false,false]`,
  `seat_kinds: ["prompt","scripted:brigade","scripted:passer","scripted:courier"]`,
  `cross_play: true`, `dishes: 11`. (r1-O6, item 7)
- `coworld-release.yml` — step order is Build the Coworld manifest (`:153`) → Certify locally (`:167`)
  → Upload the policies (`:206`) → Upload the Coworld (`:304`) → Put the Coworld secret (`:342`).
  The secret step reads `game.name` out of the committed manifest, asserts
  `ANTHROPIC_API_KEY_URI` starts with `secret://coworld/<game.name>/`, and passes `$game_name`
  (not `$SLUG`) to both `coworld secret put` and `coworld secret list` (`:366-381`).
  `tools/ci/policies.json` is 2 × `PLAYER_PROMPT` + 2 × `PLAYER_SCRIPTED` with champion #2 carrying
  `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The three-name placeholder gate
  (`<slug>`/`<IMAGE>`/`<SEATS>` over the five named files) exits clean — I ran it. All three
  workflows present; `build_replay_viewer.sh`, `docker_smoke.sh`, `viewer_smoke.mjs` all mode
  `100755` per `git ls-files -s`. (items 12, r1-O8)
- item 1, "no test loosened" — `git log -p 1f8902f..HEAD -- tests/` shows exactly two removed
  assertion lines, both re-pins: `test_replay_parse.py`'s heat *total* comparison replaced by a
  tile-for-tile equality plus a non-vacuity assert (`59c50aa`), and `test_manifest.py`'s
  `MANIFEST["replay_viewer"]` (the **wrong** shape) replaced by `MANIFEST["game"]["replay_viewer"]`
  plus `"replay_viewer" not in MANIFEST` and a whole new admitted-keys test (`f4c74bd`). No
  `skip`/`xfail`/`--skip` added, no widened tolerance, no test file removed; every other change is a
  net addition. The single skip in the run (`test_viewer_contract.py:197`) is the pre-existing
  starter-mount guard, and I verified the property it guards directly: `client/chrome_common.js` and
  `client/broadcast_core.js` `diff` **empty** against `/workspace/starters/coworld-ctf/client/`.
- item 14 provenance — `client/replay_broadcast.html` **regenerates byte-identically** from the
  mounted starter with the committed generator (`python3 tools/build_broadcast_page.py
  /workspace/starters/coworld-ctf`; I ran it, `git status` clean). Transport rules, each checked in
  the page: (a) `relayout()` writes `--hudscale`, `--sb`, `--dt`, `--topband`, `--band` on
  `document.documentElement` only (`game.js:335`, `:350`, `:357-362`) and the game block never writes
  them elsewhere; (b) nothing is `position: fixed` anywhere in the page, `#dishticker`/`#saybar` sit
  at `top: var(--sb)` / `top: calc(var(--sb) + var(--dt))` above the board, `#feed` rides
  `bottom: calc(var(--band, 0px) + 8 * var(--u))` (`game.css:113`); (c) `#endcard` keeps
  `bottom: var(--band, 0px)` (page `:1047`), is shown with `#endcard.on` (page `:1058`,
  `game.js:222`), and every playhead-moving control routes through `ccSeek`, which removes `.on`
  first (`game.js:60-65`; scrub click `:309-316`, beat markers `:175-178`, restart/back/fwd
  `:291-293`, keyboard `,` `:321`); (d) beats are labelled `<button>`s with `title`/`aria-label` that
  seek to their tick (`game.js:168-180`), and all six kinds the Nim emits — `serve`, `burn`,
  `expire`, `jam`, `plan`, `end` — have a rule (`game.css:203-208`). `#viewpanel`/`#zoombar`/
  `#minimap`/`#fpv*`/`#lockerroom`/`#killfeed` markup is absent and `attachMinimap` is never called.
- item 13 — `wasm-viewer` is green at head **including** `Load the bundle in a real browser`
  (step list read from `gh run view`), `needs: docker-smoke` (`ci.yml:140`), no `continue-on-error`
  anywhere. The browser step's own output: `{"loaded":true,"ms":327,"clock":"TICK 242 OF 480 3 ORDERS
  LIVE · 1 EXPIRING","feed_lines":6}`. Link flags and bootstrap are the **same** starter: `diff`
  against ctf's `config.nims` is a symbol rename only (`ctf_*` → `cc_*`, output filename, one comment
  path) with **no** `MODULARIZE` and **no** `EXPORT_NAME` on either side, and the worker bootstraps
  `Module.onRuntimeInitialized` (`static_replay_worker.js:162`) against `Module._cc_*` exports —
  the matched non-MODULARIZE pair. `data-replay-loaded` / `data-replay-error` both set from the
  shell's own paths (`static_replay.js:29` and `:152`).
- items 4, 8, 9 — the wire `observation` carries no names (`live_episode.py:904-914`); `player_config`
  carries `alias` only (`:886-902`); real names live in `seats[].name`, `results.names` and the
  scorebug. The head artifact confirms the alias permutation is live: slot 0 is `Cog-B`, slot 1 is
  `Cog-A`. Parsing is balanced-brace and prose-tolerant (`plans.py:119-151`); the retry is exactly
  once with the hint (`llm.py:296-329`, `for attempt in (0, 1)` at `:304`); every failure classifies into
  `FALLBACK_CAUSES` and is recorded as a `fallback` event plus `results.fallbacks`
  (`live_episode.py:829-837`, `:617-627`) — the head artifact shows `fallbacks: [2,0,0,0]` and
  `llm_requests: 0` on the credential-less path, which is the designed `disabled` behaviour.
  `truncate_runes` is a code-point slice (`plans.py:53-62`) applied to say/note/prompt/talk/errors;
  the Nim side truncates on `unicode.runes` (`collab_cooking_replay.nim:826-835`); `note` appears
  nowhere in the replay writer, the Nim module, or the head artifact bytes (checked
  `b'"note"' in replay.json` → `False`).
- addendum, one parallel batch — `LlmPlanner.start_turn` submits every prompt seat to the pool
  before returning (`llm.py:288-293`) and `PlanBatch.poll` never blocks (`llm.py:225-243`); the tick
  loop only polls (`live_episode.py:438-439`).

---

## Could not determine

- **Whether the say chip's rendered text is legible at the 360 px embed even before the clip.** At
  `--hudscale 0.500` the chip's computed `font-size` is **4.25 px** (measured). The 0.5 floor and the
  `/760` reference are the starter's verbatim (`/workspace/starters/coworld-ctf/client/
  replay_broadcast.html:4144`, identical to `game.js:349`), so I did not file it — but the `8.5 * var(--u)`
  choice for a *sentence* is the game block's own (`game.css:97`), and the starter's own scorebug type
  is `12 * var(--u)` at a further `0.8` local scale. What would settle it: a screenshot review at
  360 px, or a reviewer decision on whether 4.25 px type is inside item 11's "do not collapse".
- **Whether a `plan` turn ever produces two serves or a serve-plus-expiry in the same tick in a real
  LLM episode** (R2-O8). The head replay has neither, and CI cannot produce an LLM episode. What
  would settle it: one hosted episode with a key, or a unit test that drives two seats onto the pass
  on the same tick.
- **Whether the ~55 % clip in R2-O1 changes with the bundled `rajdhani` pixel font.** My harness ran
  from `file://` with `--pixfont` falling back to the system sans, which is also what the CI browser
  step does for the same reason; the chip does not use `--pixfont` in any case (`game.css:94-106`
  sets no `font-family`, so it inherits `--finefont` from `body`). What would settle it: rendering
  the built bundle's `index.html`, where the preloaded font is present, and re-measuring.
