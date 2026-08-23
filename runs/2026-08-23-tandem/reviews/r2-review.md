# r2 review — tandem

Range: `4b78981e77210a5f910dd679c81a32983e0a333d..668b5f5d81d5025a527391bb25f90cf2bc186d1d` (main at `668b5f5`, fresh clone at `/tmp/tandem`)
Starter: `/workspace/starters/coworld-ctf` (read-only mount)
Design note: `/workspace/coworld-builder/runs/2026-08-23-tandem/design.md`
Prior round: `r1-review.md`, `r1-fixes.md`, `r1-verdict.md` (read; every carried item re-verified below from the code at head, not from their text)
Files read at head: 31 · Files executed at head: 15 test files + `tools/tune_baselines.nim` + `client/replay_broadcast.html` (in headless chromium)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + the simultaneous-decision batching rule)

**Method note — this round had tools r1 did not.** Nim 2.2.4 is on this sandbox
(`/root/.nimby/nim-2.2.4/bin/nim`) with the full package tree, and a real chromium is at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome` with `playwright` installed. So, unlike r1,
much of what follows is **executed**, not inferred:

- all 15 `tests/*.nim` run and pass in `-d:release` locally;
- `nim r -d:release --path:src tools/tune_baselines.nim --eval` runs and reproduces the numbers
  the fix report quotes;
- `client/replay_broadcast.html` was spliced the way `server.nim:96-102` splices it (the real
  `chrome_common.js`, a stub `BroadcastCore` that only captures `config.onText`), loaded in real
  chromium, and driven with a **real** HUD frame produced by the real Nim broadcast layer
  (`broadcast.buildStateJson` over a real scripted `porter × porter` episode on seed 4417231).

Everything below is labelled **observed** (read at head), **executed** (I ran it and quote the
output), or **inferred** (reasoned, not run).

---

## Blocking

### F1 — the game block's labelled-button `markBeat` is shadowed by the inherited alias; at runtime every scrubber beat is chrome_common's unlabeled, non-clickable `<div>`

- **Where:** `client/replay_broadcast.html:1431` (`(function () {` … `:2278` `})();` — one IIFE,
  one function scope), `:1460`, `:2141-2158`; `client/chrome_common.js:538-543`, `:550-562`,
  `:473`.

- **Observed — the two declarations, both at top level of the same IIFE:**

  `client/replay_broadcast.html:1460`
  ```js
    var markBeat = C.markBeat, killMarkerTeam = C.killMarkerTeam, renderBeatMarkers = C.renderBeatMarkers;
  ```
  `client/replay_broadcast.html:2141-2158`
  ```js
    function markBeat(tick, kind, team, label) {
      …
      var mark = document.createElement('button');
      mark.type = 'button';
      mark.className = 'beat-marker ' + kind + (team ? ' ' + team : '');
      …
      mark.setAttribute('aria-label', text);
      mark.title = text;
      mark.onclick = function (ev) { ev.stopPropagation(); send('s:' + tick); };
      mark.__tick = tick;
      beatEls.push(mark);
      $('scrub').appendChild(mark);
    }
  ```

- **Executed — the binding order, in the real file's real scope.** I took lines 1431–2278
  verbatim, inserted a probe plus `return;` immediately after the alias block at `:1464` (the code
  below stays in the function body, so hoisting is unchanged), and ran it in node with only
  `window.ChromeCommon` stubbed:

  ```
  typeof markBeat        : function
  markBeat === C.markBeat: true
  markBeat.length (arity): 3
  source head            : function chromeCommonMarkBeat(tick, kind, team){ … }
  ```

  The function declaration at `:2141` is hoisted and initialised at scope entry; the `var`
  *assignment* at `:1460` then runs at script load and rebinds the name to chrome_common's copy
  before any render code executes. Every call site — `tandemIngestBeats` (`:2198`) and
  `applyEvent`'s `doorway`/`drop`/`impact`/`delivered`/`wrecked`/`gameover` arms
  (`:2207, 2211, 2214, 2218, 2222, 2225`) — resolves to `chrome_common.js:538 markBeat(tick, kind,
  team)`, which ignores the 4th argument, queues into `pendingMarkers`, and lets
  `renderBeatMarkers` (`chrome_common.js:550-562`, called from `renderTransport` at `:473`, called
  from the page's `onFrame` at `:1788`) create `document.createElement('div')` markers with no
  label, no `aria-label`, no `title` and no click handler.

- **Executed — the resulting DOM in a real browser.** Real page + real `chrome_common.js` + a real
  18-beat state frame, viewport 1280×720:

  ```
  markerCount : 18
  tagNames    : ["DIV"]
  withAriaLabel: 0     withTitle: 0     withOnclick: 0
  sample      : <div class="beat-marker doorway" style="left: 3.26252%;"></div>
  ```

  Not one `<button>`; not one label.

- **Executed — what a click on a beat actually does.** Clicking the 4th marker (the `doorway` beat
  at tick **324**) sent `"s:322"` — the seek came from the inherited scrub-bar handler
  (`client/replay_broadcast.html:1897-1906`, which maps the pointer x-fraction back onto
  `[st, mx]`) via bubbling, **not** from the marker. So the precise statement is: a beat click
  seeks to *where the pointer landed*, within the marker's half-width of the beat, and never to
  the beat's own tick; the design's `send('s:' + tick)` with `ev.stopPropagation()` never runs.

- **Executed — the collateral the r1 verdict predicted.** `beatEls` (`:2140`) stays empty, so
  `applyTandemSpoilers` (`:2165-2175`, the r1-F13 spoiler fix, commit `5dd3c60`) iterates nothing
  and is a runtime no-op. Spoilers still work, through chrome_common's own gate over its
  `markerEls` (`chrome_common.js:488-497`): with spoilers toggled off at playhead t=700, 11 of the
  18 markers got `display:none` (ticks 758, 819, 860, 969, 1086, 1186, 1193, 1283, 1290, 1315,
  1318). So there is **no separate spoiler defect** — but the fix note's premise ("the buttons it
  created") is false.

- **Observed — why CI is green over it.** `tests/test_viewer.nim:99-123 beatsAreLabelledButtons`
  is a static text grep over the page source: it asserts `"function markBeat(tick, kind, team,
  label)" in page`, `"document.createElement('button')" in page`, `"mark.setAttribute('aria-label',
  text)" in page`, `"mark.onclick" in page`. All four strings are present — in dead code. Nothing
  in the test can see a scope binding. `tools/ci/viewer_smoke.mjs` never inspects `.beat-marker`
  (its readout is `clock`/`tick`/`scorebug`/`status`/`feed_lines`/`has_scrub`, `:285-296`), so the
  browser gate cannot see it either.

- **Checklist item:** **14** — "(d) scrubber beats are labelled `<button>`s that seek to their
  tick (`chrome_common.markBeat(tick, kind, team, label)`), with CSS for every kind the page emits".
  The CSS half holds (see "Traced and consistent"). The labelled-button-that-seeks half is false in
  the running page. *(category: static-viewer)*

- **Design note, §Transport rules:** "**Scrubber beats are clickable, labelled
  `<button class="beat-marker <kind>">`** elements — the game block upgrades chrome_common's
  markers to buttons with `aria-label` and `title` (e.g. "Doorway 4 cleared — 24.1 s"), and a
  click seeks to that tick."

- **Enumerated: is anything else shadowed the same way?** No. I parsed the whole IIFE
  (lines 1431–2278) and collected every top-level declaration — 117 names, from 39 `C.*` aliases
  (`:1449-1464`) plus every top-level `function`/`var`. **`markBeat` is the only duplicate
  declaration in the scope.** No alias is re-assigned anywhere else in the IIFE (checked for
  `name =` outside the alias block: zero hits), and no game-block function name (≥ `:1984`)
  collides with a function declared above the banner. Specifically checked and clean:
  `relayout` (declared once, `:1934`), `renderScorebug` (`:2267`), `applyEvent` (`:2203`),
  `renderEndcard` (`:2235`), `applyTandemSpoilers` (`:2165`), `beatLabel` (`:2176`),
  `tandemIngestBeats` (`:2187`), `pushTandemFeed` (`:2115`), `send` (`:1725`), `getSpoilers`/
  `setSpoilers` (aliases only, `:1464`). The browser run confirms the rest of the game block
  executes: 18 markers means `renderPlates`/`renderCondition`/`renderRoute`/`renderFeed` all ran
  ahead of `tandemIngestBeats` in `renderScorebug` (`:2267-2274`) without throwing, and the page
  logged **zero** page errors.

---

## Non-blocking

### F2 — the `delivered` beat/event kind is unreachable: the sim leaves `Delivered` inside the same tick it enters it
- **Where:** `src/tandem/sim.nim:570-578` (`applyProgress` sets `sim.phase = Delivered`),
  `src/tandem/sim.nim:646-648` (step 10, same tick: `if sim.phase == Delivered:
  sim.finishGame(reasonComplete, erDelivered)` → `phase = GameOver`),
  `src/tandem/broadcast.nim:88-104` (`stepEvents` compares `sim.phase` to `tracker.prevPhase` and
  emits `{"k":"delivered"}` only in the `elif sim.phase == Delivered` arm),
  `src/tandem/server.nim:765-771` and `src/tandem/replays.nim:397-398` (both call `stepEvents`
  **after** the whole tick).
- **Executed:** a real delivered episode (seed 4417231, porter × porter, delivered at tick 1317)
  produced 18 beats — 13 `doorway`, 4 `impact`, 1 `gameover` — and **no** `delivered` beat. The
  derived event list on the final frame is `phase`/`gameover` only.
- **Note says** (§Record vocabulary B): "**Beats** (scrubber markers): `doorway`, `impact`
  (≥ 20 points), `drop`, `wrecked`, `delivered`, `gameover`."
- **Consequence:** `.beat-marker.delivered` (`client/replay_broadcast.html:1274`) and
  `applyEvent`'s `case 'delivered'` (`:2216-2219`) are dead. The banner `banner('DELIVERED',
  'good')` on that arm never fires either; the delivery is still legible from the feed line
  (`sim.nim:577-578`) and the endcard (`broadcast.nim:351-367`).
- **Not blocking:** checklist 14(d) requires *a CSS rule for every kind the page emits*; a rule
  with no kind is the harmless direction. `wrecked` **is** reachable (it is gated on the damage
  delta, `broadcast.nim:118-121`, not on the phase).

### F3 — `client/league_replayer.html` is the starter's CTF shell with rename edits only; it has no tandem game block
- **Where:** `diff /workspace/starters/coworld-ctf/client/league_replayer.html
  client/league_replayer.html` = **10 changed lines**, all renames (`CTF · League Replayer` →
  `Tandem · …`, `ctf-shell`/`ctf-replay` → `tandem-*`, two comments). Both files are 906 lines.
  The page still drives CTF beats (`:822-825`
  `if (e.k==='kill') markBeat(e.t,'kill', killMarkerTeam(e, s)); else if (e.k==='steal') … 'return'
  … 'capture'`) and still renders lives counters, flag icons and perk badges (`:127-165`,
  `:132-138 .lives-num`, `:159-164 .flagicon`, `:150-153 .perk-ico`) from state keys tandem never
  ships.
- **Note says** (§Sim module, "Kept verbatim" table): "`client/replay_broadcast.html`,
  `client/league_replayer.html` | the broadcast chrome, **with a game block appended** (§Viewer)".
  §Viewer's §Chrome provenance then only describes `replay_broadcast.html`.
- **Not blocking:** checklist 14 names `client/chrome_common.js` and
  `client/replay_broadcast.html` only. This page is the game pod's `/client/league` shell
  (`server.nim:90 LeagueReplayerPath`), not the static bundle. *Inferred* consequence: its
  wall-mounted scorebug renders blank lives/flag furniture beside the embedded board. I did not
  run it.

### F4 — the scrubber's verdict cap (`#scrub-win`) is permanently inert
- **Where:** `src/tandem/broadcast.nim:351-352` sets `"winner": ""`, `"draw": false` on the `over`
  object (correct for a cooperative game); `client/replay_broadcast.html:1799` calls
  chrome_common's `ingestBeats(s)` and `:1802` calls `setVerdict(s.over)`;
  `client/chrome_common.js:597-599` — `var cls = v.draw ? 'draw' : (v.winner || ''); if (!cls)
  return;`.
- **Observed/executed:** the winner cap and the verdict chip never appear; the state I drove the
  page with carries exactly that `over` object. The endcard carries the verdict instead
  (`:2235-2262`, verified rendering in the browser).
- **Not blocking:** the note keeps `#scrub-win` in the markup list (§Viewer "Kept") but never
  claims tandem drives it, and no checklist item names it.

### F5 — the test that guards checklist 14(d) cannot fail on F1
- **Where:** `tests/test_viewer.nim:99-123`.
- **Observed:** the proc asserts four *source strings* of the shadowed function plus one
  `.beat-marker.<kind>` rule per kind. It passes at head (I ran it) while the behaviour it names
  is absent. This is not a *loosened* test (checklist 1's second half is about changes made this
  run, and this proc was strengthened, not weakened, in `5dd3c60`); it is an insufficient one.
- **What would make it load-bearing:** an assertion about the scope, e.g. that `markBeat` does not
  appear in the `var … = C.markBeat` alias list while `function markBeat` exists in the same
  scope — or a DOM assertion in `tools/ci/viewer_smoke.mjs` over `#scrub .beat-marker` tag names.

### F6 — two `.beat-marker` base rules; the starter's geometry still wins for `height`
- **Where:** `client/replay_broadcast.html:603-610` (the inherited rule: `width: calc(2 * var(--u));
  height: calc(10 * var(--u)); transform: translateX(-1px)`) and `:1263-1267` (the game block's:
  `top: 0; bottom: 0; width: calc(3 * var(--u)); margin-left: calc(-1.5 * var(--u)); cursor:
  pointer`).
- **Observed/executed:** later rule wins per property, so the marker is 3 u wide with the game
  block's colours and `cursor: pointer`, but keeps the starter's `height: 10u` (with `top`,
  `height` and `bottom` all set, `bottom` is ignored) and the extra `translateX(-1px)`. Measured
  box at 1280 px: `x=393.34, w=3.91`. Cosmetic only; both rules are legitimately present
  (the inherited CSS above the banner is unmodified, which is what checklist 14 wants).

### F7 — comment/value drift carried over from r1, still at head
- `src/tandem/baselines.nim:411` — mule's note string is `"straight at the goal, full effort"`
  while `MuleEffort = 140` (0.55).
- `src/tandem/server.nim:477` — comment says "690 s engine stop"; the constant is 660
  (`sim_types.nim`, and `wallClockBudgetSeconds` default 660 in the manifest).
- `src/tandem/sim_types.nim:471` — `SimServer.damageAtTurnStart` is declared, never written, never
  read (the live field is `TurnEngine.damageAtTurnStart`, `decide.nim:84`). Not hashed
  (`sim_state.gameHash` does not mix it), so it costs nothing but a reader's time.
- `src/tandem_player.nim:120-122` — the startup echo prints `$prompt.len` (the **uncapped** byte
  length) although `registrationPayload` (`:67-79`) sends the 4000-rune clip. Log-only.
- All four were explicitly recorded as "NOTED (not fixed)" by the r1 fixer; I re-verified them at
  head rather than carrying the claim.

---

## Traced and consistent

**The scrubber / beat / spoiler / endcard chain, end to end (checklist 14 b–d)**
- Beat kinds actually emitted, traced from the sim: `doorway` (`broadcast.nim:106-109`, no team),
  `drop` (`:110-112`, team `cobalt`|`rust`), `impact` (`:113-116`, `dmg`), `wrecked` (`:118-121`),
  `gameover` (`:91-101`), and `delivered` — unreachable, F2. The page maps `gameover` → `over`
  (`:2197`, `:2225`).
- **CSS exists for every kind the page emits:** `.beat-marker.doorway|.impact|.drop|.wrecked|
  .delivered|.over` at `client/replay_broadcast.html:1270-1275`, plus the team tints
  `.cobalt`/`.rust` at `:1276-1277`. Executed: the 18 rendered markers carried classes
  `beat-marker doorway` (13), `beat-marker impact` (4), `beat-marker over` (1) — every one styled.
- **The `impact ≥ 20` beat filter is real and load-bearing** (r1-F13): `replays.nim:92-101`
  (`BeatKinds`, `ImpactBeatDamage* = 20`) and `:397-405` (the two `continue`s where `beatEvents` is
  built). Executed on the real episode: the sim emitted impacts of **10, 22, 12, 13, 43, 24, 23,
  19**; the beat list kept exactly **22, 43, 24, 23**. Remove the filter and four junk markers come
  back. The page keeps the same guard for old streams (`:2196`).
- **Seek routes.** Scrub click `:1897-1906` (`send('s:' + tick)`); transport buttons `:1888-1894`;
  keyboard `:1909-1926` (`b`, `e`, `,`, `.`, `r`, `f`, `+/-`, digits, `o` for spoilers). In the
  static bundle these reach the wasm core: `static_replay.js:215-217 sendCommand` →
  `static_replay_worker.js:180 message.type === 'command'`.
- **Endcard dismissal on every seek route.** `#endcard { bottom: var(--band, 0px) }` (`:741`),
  shown with the class its rule uses (`#endcard.on`, `:752` / `:2239`), and `onFrame` removes it on
  **every** frame whose phase is not `gameover` (`:1802-1803`), which is what any seek produces.
  Executed: `className` was `"on"` on the game-over frame and `""` after a frame at t=300.
- **Spoilers.** Executed: with `?spoilers` toggled off (keydown `o` → `setSpoilers`, `:1921`), the
  11 beats ahead of the playhead were hidden and the 7 behind stayed visible — through
  chrome_common's own gate (`chrome_common.js:488-497`), since the tandem gate has nothing to
  iterate (F1).
- **`relayout()` sets the variables on `:root`.** `:1934-1979`, `root =
  document.documentElement`, `--hudscale`, `--topband`, `--band`. Executed at a 360 px viewport:
  `--band: 38px`, `--hudscale: 0.500`, `#stage` class `tiny beat-active`.
- **Nothing fixed-positioned sits in the band:** tandem's overlays ride
  `bottom: calc(var(--band, 0px) + 10 * var(--u))` (`:1236`, `:1250`).

**Checklist 11 (legible at 360 px)** — executed at 360×640 with a real frame:
`.plate-name` rendered the real policy name `cobalt-policy` at 129 px, `#stage.tiny` applied,
`@media (max-width: 640px)` (`:1306-1311`) hiding `.strain-num`, `.plate-blame`, `.plate-alias`,
`#arrowlegend`. Rule at `:1172`.

**Checklist 14 provenance** — `client/chrome_common.js` sha256
`7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` on **both** copies; `diff`
empty. `client/replay_broadcast.html` carries the required banner (`:1984-1992` "TANDEM additions
to the inherited coworld-ctf chrome") with the game block below it and the starter's CSS/markup
above.

**The r1 fixes, re-verified at head (spot-trace, executed where possible)**
| r1 finding | verified at `668b5f5` | how |
|---|---|---|
| B1/F1 tuning harness | `tools/tune_baselines.nim` present, 257 lines; `--eval` **executed**: `porterxporter 20/20 mean_score 0.793727 dmg 219 ticks 1524`, `porterxmule 0.021507`, `mulexmule 0.01648` — identical to the numbers `tests/test_baselines.nim` prints (`porter mean 0.794`, `porter+mule 0.022`, `mule+mule 0.016`). `--sweep` uses `execProcess(nim, args = argv)` with an int-validated define value (`:159-169`, `:196-201`) — no shell, no injection | executed |
| F2 `damage_last_turn` | snapshot moved to the **end** of `turn()` (`decide.nim:475-478`); field read at `:207`; `tests/test_engine.nim` "damage_last_turn measures the previous turn" passes | executed |
| F3 rune-safe provider text | `llm.nim:164-170 head()` (`runeLen`/`runeSubStr`); all five cuts go through it (`:177, 185, 190, 201`) and the sixth is `:211-212 runeSubStr`; `tests/test_orders.nim` "captured error text is cut on rune boundaries" passes | executed |
| F4 drive repair | `orders.nim:308-314`: `elif hasPrevious:` unconditional; note's precedence restored | observed + test green |
| F5 disconnect degrades | `decide.nim:351` `if policy.kind == pkScripted or not policy.connected:`; `server.nim:623` clears `connected` on the close path **before** `removePlayerAt` renumbers; `registrationOf` re-sets it (`:426`); `tests/test_engine.nim` "a disconnecting seat degrades to porter and revives on reconnect" passes | executed |
| F6 prompt cap at the transport | `tandem_player.nim:24-32 PromptRuneCap = 4000`, `:50-54 clipPromptRunes`, applied at `:73` **before** `chatPacket` builds the u16-length frame (`:56-65`); `tests/test_server.nim` passes | executed |
| F7 per-player exit codes | `tools/ci/docker_smoke.sh:244-268` — bounded 60 s wait per `${prefix}-p<slot>`, then `docker inspect … ExitCode` asserted 0. CI log of run **32671500679**: `player container tandem-smoke-11060-p0 exited 0`, `…-p1 exited 0`, then `smoke OK: seats=2 … reason=complete` | observed (log cited) |
| F8 contact assertions | `tests/test_physics.nim:95-121` penetration `<= 60_000` µm and `depthUm > 0` over 600 ticks; `:123-165` `normalMilliNewtons >= 0` and `<= ContactForceCap`, and friction's per-substep Δv `< slideUmPerTick` with a `slidingSeen > 0` guard so the check cannot vacuously pass | executed |
| F10 route test | `tests/test_routes.nim` drives the real `runServerLoop`: `/healthz`, `/client/global`, `/client/player` (no socket), `/global` to `gameover`, bad token refused, 15 s shutdown grace. **Executed here**: passes, printing `game over: complete/out_of_time` and the results JSON. The 300 s health wait is a bound, not an assertion tolerance | executed |
| F11 scrape assertion | two separate asserts; `tests/test_replay.nim` "the derived event stream carries scrapes, doorways and game over" passes | executed |
| F12 end-check order | `sim.nim:651-665`: Delivered → wrecked → `out_of_time` → `physicsGuardTripped`; wall-clock stop stays in the server loop. `tests/test_determinism.nim` "the committed golden hash chain still holds" passes, so no recorded hash moved | executed |
| F13 beat list + spoiler gate | beat-list half real and pinned (above). Spoiler half is a **runtime no-op** — see F1 — but no spoiler defect stands, because chrome_common's gate does the work | executed |
| F14 `AGENTS.md` | present (7 183 B), linked from `README.md` | observed |
| F15 feed escaping | `:2125 row.textContent = line.text;`. **Executed in the browser** with a feed line `Rust: "you lead" & I'll follow <now>`: the row's `textContent` is the raw string and its `innerHTML` is the browser's own `&amp;`/`&lt;` encoding — i.e. displayed correctly and still inert | executed |

**No test was loosened this round.** `git diff 4b78981 668b5f5 -- tests/` removes exactly five
lines: `proc disconnectedSeatPlaysPorter() =` (rewritten; the old body kept in full as
`noTransportSeatPlaysPorter`), `doAssert worstPenetration < InnerWall` (→ `<= 60_000`, tighter by
5×), two by-construction asserts that are re-added inside the rewritten `contactsPush`, and
`doAssert "scrape" in rough or "impact" in rough` (→ two separate asserts). No `skip`/`xfail`, no
file removed. **All 15 test files pass locally in `-d:release`.**

**CI at the reviewed sha (checklist 1, 13)** — `gh run list -R Metta-AI/cogame-tandem --branch main
-w ci.yml`: run **32671500679**, conclusion `success`, `headSha
668b5f5d81d5025a527391bb25f90cf2bc186d1d`. Jobs `test`, `docker-smoke`, `wasm-viewer` all
`success`; `wasm-viewer`'s step **"Load the bundle in a real browser"** ran and succeeded
(`{"loaded":true,"ms":3116,…}`, `soak: 12s of playback kept advancing ("2 / 948" -> "242 / 948" ->
"290 / 948")`), as did "Native/wasm determinism gate". `grep -c "SEAT-COUNT FAIL"` over the whole
downloaded run log: **0**; the log shows `SMOKE_SEATS: 2`, `seats=2`.

**Manifest (checklists 3, 6, 10, 12)** — parsed at head: `game.replay_viewer ==
{"bundle":"static-replay-viewer"}`; `game.protocols` = `['global','player']`; `game.docs` =
`readme` + pages `rules.md`/`protocol.md`/`carrying.md`; `num_agents == 2` in variant `default`,
variant `sprint` and `certification.game_config`; `len(certification.players) == 2 ==
len(certification.game_config.players)`. `git ls-files -s`: `tools/build_replay_viewer.sh`,
`tools/ci/docker_smoke.sh`, `tools/ci/viewer_smoke.mjs` all mode `100755`. The three-name
placeholder grep over the five named files **exits 1 (no match)**, i.e. the gate passes.

---

## Could not determine

- **Whether the F1 breakage is visible in the shipped static bundle exactly as it is in the served
  page.** I drove `client/replay_broadcast.html` with a stub core; the bundle's `index.html` is
  built from the same file with `window.TandemStaticReplay` present (`:1472`, `:1708`), which
  changes only `COG_BASE` and which `createCore` is used — neither touches the `markBeat` binding.
  *Inferred*: identical. Settled by adding a `#scrub .beat-marker` tag-name assertion to
  `tools/ci/viewer_smoke.mjs` and reading the next `wasm-viewer` log.
- **What the CTF-shaped `league_replayer.html` (F3) actually renders against a tandem frame.** I
  did not run it; it needs the shell's `postMessage` frame path. Settled by loading
  `/client/league` with a tandem board iframe, or by a screenshot from the Observatory.
- **`feed_lines: 0` in the viewer-smoke JSON (r1's O9) is *not* evidence about the feed** — that I
  can now determine: `tools/ci/viewer_smoke.mjs:286` queries `#feed, .feed, #log`, and tandem's
  feed is `#killfeed` (`client/replay_broadcast.html:1820`), so the number is structurally 0 for
  this repo. The feed itself does render: executed above (F15). What remains undetermined is only
  whether the *bundle* dwells rows long enough at 1× for a spectator, which needs a soak
  screenshot.
- **Whether any hosted episode has exercised the LLM path** (`source == "llm"` orders,
  `fallbackTurns`). Everything in CI is scripted; the batch transport is covered only by the fake
  in `tests/test_engine.nim`. Phase 60's `tools/replay_summary.py` check is the intended settler.
- **Whether the 0.1.42 upload schema wants `game.tags`** (r1's O7 — the five tags are top-level).
  Settled by `validate_upload_manifest` output from a real `coworld build`.

---

## Summary

**1 blocking finding (F1, category static-viewer, checklist 14d)** — reproduced at
`668b5f5` three independent ways: by static scope analysis of the whole IIFE, by executing the real
file's scope in node, and by rendering the real page with the real `chrome_common.js` and a real
Nim-produced HUD frame in headless chromium, where all 18 scrubber beats came out as unlabeled,
handler-less `<div>`s. `markBeat` is the **only** shadowed symbol in the page. **6 non-blocking
observations (F2–F7).** Everything else on the checklist traced clean, and all fourteen r1 fixes
are intact at head with no regression found in the `e8d0742…668b5f5` series.
