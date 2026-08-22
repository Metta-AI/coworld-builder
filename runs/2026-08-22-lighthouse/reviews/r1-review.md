# r1 review — lighthouse

- **Repo / sha reviewed:** clean checkout at `/workspace/scratch/review-lighthouse`,
  `Metta-AI/cogame-lighthouse` @ `a16bebc62f3101598926913a76fcfba20be7d9f5`
  (`docs: amend the design note to the shipped constants`).
- **Design note:** `/workspace/coworld-builder/runs/2026-08-22-lighthouse/design.md`,
  byte-identical to the repo's `docs/plans/2026-08-22-lighthouse-design.md`. The
  §Tuning revision block (board 11×9, ascending key draw, tidePeriod 7/5, lantern
  one-step lookahead + never-twice-in-a-row) is treated as authoritative and is **not**
  reported as a deviation.
- **Checklist consulted:** `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (read, and
  each finding is tagged with the item it touches — categorisation is the judge's call,
  not mine).
- **Files read in full:** `src/lighthouse.nim`, `src/lighthouse/{types,sim,llm,server}.nim`,
  `src/lighthouse_player.nim`, `tests/{test_sim,test_bot,test_replay}.nim`,
  `replay-viewer/{lighthouse_replay.nim,static_replay.js,index.html,config.nims}`,
  `coworld_manifest_template.json`, `tools/build_replay_viewer.sh`,
  `tools/ci/{docker_smoke.sh,policies.json}`, `.github/workflows/ci.yml`,
  `client/chrome.css`, plus targeted reads of `client/renderer.js` (1513 lines),
  `.github/workflows/coworld-release.yml`, `client/fixtures/gen_fixture.js`,
  `compose.yaml`, `lighthouse.nimble`, `README.md`. Starters `cogame-babel` and
  `cogame-bullwhip` consulted for the "kept verbatim" claims.
- **Execution evidence:** Nim 2.2.4 is present in this sandbox at `~/.nimby/nim/bin`, so
  several observations below are **executed**, not inferred. I rebuilt `nim.cfg` exactly
  as `ci.yml` does and ran the test suite plus three purpose-built probes against the
  real sim. Probes are labelled **[executed]**; everything else is **[read]** or
  **[inferred]**.
- **CI:** `ci.yml` run **32600293001** on this sha — `conclusion: success`, jobs
  `test` ✓ 13s, `docker-smoke` ✓ 59s, `wasm-viewer` ✓ 53s (`gh run view 32600293001`).
  docker-smoke log contains no `SEAT-COUNT FAIL`; it prints
  `game=lighthouse seats=4 ...` and `smoke OK: seats=4 results=252B replay=4280B reason=timeup`.

---

## Findings

Seventeen. Each gives `file:line`, what the code does, and what the note says.

---

### F1 — `glyphAt` masks water under a key glyph, so `wallhug` walks into the tide

**Where:** `src/lighthouse/sim.nim:428-444` (`glyphAt`), `src/lighthouse/llm.nim:354-357`
(`passable`), `src/lighthouse/llm.nim:372-408` (`wallhugAction`).

**What the code does** [read]:

```nim
# sim.nim:428-444
proc glyphAt*(sim: Sim, x, y: int): char =
  if not sim.inBounds(x, y): return '#'
  let runner = sim.runnerAt(x, y)
  if runner > 0: return char(ord('0') + runner)
  if (x, y) == sim.exitAt: return (if sim.gateOpen: 'O' else: 'E')
  if (x, y) in sim.keysOnFloor: return 'K'      # <-- before the water check
  if sim.isWall(x, y): return '#'
  if sim.isFlooded(x, y): return '~'
  '.'
```

`runnerWindow` (sim.nim:456-467) is built from `glyphAt`, and `wallhug`'s only legality
test is:

```nim
# llm.nim:354-357
proc passable(window: array[3, string], move: Move): bool =
  let step = delta(move)
  let cell = window[step.y + 1][step.x + 1]
  cell notin {'#', '~'}
```

An **uncollected key on a flooded tile renders as `K`, not `~`**, so `passable` returns
true and the runner orders a move into open water.

**Reproduced** [executed]. Driving `lantern` + three `wallhug` to the natural end over 16
seeds, seed 21 proposes five moves into unflooded-target-false tiles:

```
tick 25 clock 38 waterLine 5: runner 2 at (1,4) -> (1,5) glyph='K' window=["#..","#@#","#K#"]
tick 26 clock 39 waterLine 5: runner 2 at (1,4) -> (1,5) glyph='K' ...
tick 27 clock 41 ... tick 28 clock 42 ... tick 29 clock 44   (5 in all)
```

Every other seed I drove (1, 7, 42, 1234, 11, 2, 9, 3, 4, 5, 100, 777, 55, 8, 13) was clean.

**What the note says.** §Decisions, *Scripted baseline `wallhug`* step 1: take the ordered
direction only if "that direction's neighbour in the window **is floor and not `~`**";
step 2: "the **open, unflooded** neighbour"; step 3: "the first neighbour that is floor
and **not flooded**". §Tests `test_bot` #1: "no move ever passes through a wall, off the
grid, **or into a flooded tile**". `rules.md` in the manifest repeats it ("open and dry
in the window").

**Consequence, traced.** `applyTick` step 4b (sim.nim:537-540) blocks the move and sets
`blocked`, so **no rule is broken and the sim state stays legal** — the runner loses the
tick and bumps repeatedly. On seed 21 that is 5 wasted ticks with the water two rows
below. Checklist item 7's "asserts every order/action is inside its legal bounds" is the
item this touches.

---

### F2 — the load-bearing legality assertion in `test_bot` is vacuous (`and` where the note needs `or`)

**Where:** `tests/test_bot.nim:68-74`.

```nim
      ## No move ever passes through a wall, off the grid, or into water.
      let step = delta(moves[index])
      let target = (result.sim.pos[index].x + step.x,
        result.sim.pos[index].y + step.y)
      if moves[index] != mvWait:
        check not (result.sim.isWall(target[0], target[1]) and
          result.sim.isFlooded(target[0], target[1]))
```

**What the code does** [read + inferred]. The assertion fires only when the target is
**both** a wall **and** flooded. `isWall` (sim.nim:97-100) returns `true` off-grid;
`isFlooded` (sim.nim:117-120) returns `false` off-grid, so an off-grid target passes. A
dry wall passes (`true and false`). **Open water passes** (`false and true`). The three
conditions the comment names are exactly the three the assertion cannot detect. The
intended predicate is `not (isWall or isFlooded)`.

The only case that would fail is a tile that is simultaneously wall and flooded, which
`passable` already rejects (`glyphAt` returns `'#'` before `'~'`), so the check is
**never** exercised.

**Confirmed against F1** [executed]: on seed 21 the five illegal targets have
`isWall == false`, so `not (false and true) == true` — the test goes green on a baseline
that walked into the sea five times.

**What the note says.** §Tests `test_bot` #1 calls this "the load-bearing assertion" and
demands "no move ever passes through a wall, off the grid, or into a flooded tile".
Checklist item 7 requires the test to assert "every order/action is inside its legal bounds".

**Not a loosening within this run** [executed]: `git log --oneline -- tests/` shows tests/
was touched by exactly one commit, `8f57cf7`, and every line there is an addition. Nothing
was deleted, widened, skipped, or removed after the fact. This is a defect as written, not
a regression.

*Note for the fixer's benefit only (I am not proposing the fix):* the post-`applyTick`
checks at `tests/test_bot.nim:79-84` (`not isWall(pos)`, `not isFlooded(pos)`) are correct
and do fire, but they check the **resolved** position, which `applyTick` has already made
legal — they catch a sim bug, not a baseline bug.

---

### F3 — replay-config fallbacks still carry the pre-retune board (17 × 11, tidePeriod 4)

**Where:** `src/lighthouse/server.nim:524-539` and
`replay-viewer/lighthouse_replay.nim:26-36`.

```nim
# server.nim:524-532
proc configFromReplay*(payload: JsonNode): GameConfig =
  result = defaultGameConfig()
  let recorded = payload["config"]
  result.seed = recorded{"seed"}.getInt(0)
  result.maxTicks = recorded{"maxTicks"}.getInt(45)
  result.width = recorded{"width"}.getInt(17)      # default 17
  result.height = recorded{"height"}.getInt(11)    # default 11
  result.tideDelay = recorded{"tideDelay"}.getInt(10)
  result.tidePeriod = recorded{"tidePeriod"}.getInt(4)   # default 4
```

`replay-viewer/lighthouse_replay.nim:31-34` is identical (17 / 11 / 4).

**What the code does** [read]. `defaultGameConfig()` is called first and already sets
11 / 9 / 7 (`types.nim:79-86`), and is then overwritten by `getInt(17)` / `getInt(11)` /
`getInt(4)` whenever the recorded config omits the key. So a replay missing `width`,
`height` or `tidePeriod` re-derives on the **old** board rather than on the current default.

**What the note says.** §Tuning revision: the shipped board is 11 × 9 and `tidePeriod` is 7;
"the sections above are written with the shipped values". §Sim module lists the defaults
as `width` (11), `height` (9), `tidePeriod` (7).

**Reachability** [inferred]. `replayConfigJson` (server.nim:162-175) always writes
`width`, `height`, `tidePeriod`, and `tests/test_replay.nim:63-68` does too, so no
lighthouse-written replay hits the fallback. If one ever did, `checkRecordedBoard`
(sim.nim:766-777) would compare the seed-derived grid with the recorded grid and raise
`"the recorded maze does not match the seeded one"` — a **loud** failure, not a silently
wrong board. This is therefore latent, not live. Touches checklist item 2 (replay
re-derivation) only in the latent sense.

---

### F4 — the note's §Tests "Viewer smoke" repo-side checks are not in CI

**Where:** `.github/workflows/ci.yml:190-241` (`wasm-viewer` job),
`tools/build_replay_viewer.sh:58-59`.

**What the code does** [read]. The `wasm-viewer` job does exactly four things: asserts
`tools/build_replay_viewer.sh` is a file (`ci.yml:208-211`) and `-x` (`212-216`), runs it
(`219`), asserts `index.html` is non-empty and that ≥1 `*.wasm` larger than 1 byte exists
(`221-234`), and uploads the bundle (`236-241`). The build hook's own post-checks are
`test -f "${output_dir}/index.html"` and `grep -q 'data-replay' .../static_replay.js`
(`build_replay_viewer.sh:58-59`).

Absent from the tree entirely [executed — `grep -rn 'node --check' .` returns nothing]:

- `node --check client/renderer.js`
- `node --check replay-viewer/static_replay.js`
- a grep for `coworld-replay`
- a grep for `tell("ready")`
- "every file `index.html` references exists in the bundle"

**What the note says.** §Tests, *Viewer smoke*: "…`node --check client/renderer.js` and
`node --check replay-viewer/static_replay.js` pass; and `replay-viewer/static_replay.js`
contains `data-replay`, `coworld-replay` and `tell("ready")`" and "every file `index.html`
references exists in the bundle".

**Substance of what the checks would have asserted, verified by hand** [read]:

- `replay-viewer/static_replay.js:56` contains `data-replay-error` (so the existing
  `grep -q 'data-replay'` passes on a substring), `:26` `src: "coworld-replay"`, `:123`
  `tell("ready")`. All three strings are genuinely present.
- `index.html` references `./chrome.css` (:6), `./renderer.js` (:37),
  `./lighthouse_replay.js` (:38), `./static_replay.js` (:39). The hook copies all four
  (`build_replay_viewer.sh:45-51`) plus six assets into `assets/` (`52-56`), and
  `static_replay.js:117` sets `assetBase: "./assets"`. The bundle is complete.

So the *properties* hold; the *checks the note promises* are missing. Touches checklist
item 3 (static viewer) only insofar as the note's own guard is absent.

---

### F5 — `lantern` transmit exception (c) reads "tide rose in the last 2 clock units", not "since the last message"

**Where:** `src/lighthouse/llm.nim:308-334`, specifically `:313-317` and `:326`.

```nim
  let last = if sim.messages.len > 0: sim.messages[^1][1] else: ""
  var roseSinceLastWord = true
  if sim.messages.len > 0:
    roseSinceLastWord = tideRowsAt(sim.config, sim.clock) !=
      tideRowsAt(sim.config, sim.clock - 2)
  ...
    if roseSinceLastWord and sim.pos[index].y + 2 >= sim.waterLine():
      return true
```

**What the code does** [read]. The window is a fixed `clock - 2 .. clock`, i.e. "did the
tide step within the last two clock units". The last message may be many ticks — and many
clock units — older than that.

**What the note says.** §Decisions, `lantern` step 6 exception (c): "the tide rose **since
the last message** and a runner is within 2 tiles of the water".

**Effect** [executed]. It makes (c) fire *less* often, which is conservative for the talk
budget. Measured talk rates on the fixture seeds are 51.9 / 52.0 / 51.4 / 51.4 %, inside
the note's ≤ 60 % bar and matching the §Tuning revision's claimed 51–52 %. Exceptions (a),
(b) and (d) match the note as written (llm.nim:321-334). Exception (d) checks for an
`evKey` at `sim.tick - 1` that completed the set, which is the only tick on which the gate
can have flipped from the decider's viewpoint (step 6 runs after step 2), so "flipped this
tick" is faithfully rendered as "flipped last tick".

---

### F6 — `parseMoveToken` accepts `"H"`, an alias the note does not list

**Where:** `src/lighthouse/llm.nim:173-183`.

```nim
  of "WAIT", "STAY", "HOLD", "H": mvWait
```

**What the note says.** §Reply schema, runner reply: "with the aliases `NORTH`/`UP`,
`SOUTH`/`DOWN`, `EAST`/`RIGHT`, `WEST`/`LEFT`, `STAY`/`HOLD`/`WAIT`. Anything else (`"NE"`,
`42`, missing) is a **parse failure**." `"H"` is not on that list, and the manifest's
`rules.md` (`coworld_manifest_template.json:291`) repeats the note's list without `H`.

**Traced rationale** [read]. Champion #2 `lighthouse-pilot` is specified with the grammar
`"<Alias>:<N|S|E|W|H>"` (design §Decisions; `tools/ci/policies.json:13`), and
`orderedDirection` (llm.nim:279-306) routes ordered directions through the same
`parseMoveToken`, so without `"H"` a pilot keeper's `H` would not parse for `wallhug`
either. The addition is coherent with the shipped champion prompt; it is a widening of the
note's accepted-token set, undocumented in the note and in `rules.md`.

---

### F7 — keeper `message` newline handling replaces, does not collapse

**Where:** `src/lighthouse/llm.nim:650-652`.

```nim
  result.message = cleanText(
    payload{"message"}.getStr().replace("\n", " ").replace("\r", " "),
    MaxMessageLen)
```

**What the code does** [read]. Each `\n` and each `\r` becomes one space, so `"a\r\n\nb"`
becomes `"a   b"` (three spaces). `cleanText` (llm.nim:162-169) then strips the ends and
rune-truncates, but does not squeeze interior runs.

**What the note says.** §Reply schema, keeper reply: "Newlines are **collapsed to single
spaces** before truncation." `\r` is not mentioned either way.

**Effect** [read]. Cosmetic in the replay/subtitle; the rune cap and UTF-8 validity are
unaffected. `tests/test_bot.nim:232-234` asserts the single-newline case
(`"one\ntwo"` → `"one two"`), which passes.

---

### F8 — at 11 × 9 the dead-end key filter is inoperative on most seeds; the "fewer than 3 candidates" fallback is the normal path

**Where:** `src/lighthouse/sim.nim:291-349`.

**What the code does** [read]. `placeKeys` collects dead-end rooms (`openNeighbourCount == 1`)
with `y ≤ height - 4` (= 5), not a start, not the exit, not adjacent to it, reachable
(`:298-310`). If `candidates.len < keyCount` it takes the total fallback at `:319-349`:
**all floor tiles** with `y ≤ 5` under the same exclusions, ranked by *descending* exit
distance, greedily taking those pairwise ≥ 6 apart, then topping up.

**Measured** [executed] — dead-end candidate count and the shipped keys, 13 seeds at the
shipped 11 × 9 defaults:

| seed | dead-end candidates | fallback taken | keys that are dead ends |
|---|---|---|---|
| 1 | 2 | yes | 1 / 3 |
| 7 | 2 | yes | 1 / 3 |
| 42 | **0** | yes | **0 / 3** |
| 1234 | 1 | yes | 1 / 3 |
| 11 (cert) | 1 | yes | 1 / 3 |
| 2 | 3 | no | 3 / 3 |
| 9 | 3 | no | 3 / 3 |
| 21, 3, 4, 5, 100, 777 | 2,1,1,2,1,2 | yes | 2,1,0,1,1,2 |

11 of 13 seeds take the fallback. On seed 42, **no** key is in a dead end (keys land at
(1,5), (5,5), (9,5)).

**What the note says.** §The game step 5 (as amended) explicitly anticipates this: "If
fewer than 3 candidates exist at all — which **does** occur at 11 × 9, so this path is live
rather than defensive — fall back to the floor tiles…". The measurement above **confirms**
that sentence. The tension is with the same paragraph's other claim: "The dead-end filter
is what keeps the keeper load-bearing; a blind runner still cannot find a key without it."
On the majority of seeds there is no dead-end filter in effect. The note is also careful to
say the fallback "applies the same 'not the exit tile, not adjacent to it, not a start'
exclusions", which is true (sim.nim:325-328) — it just does not preserve dead-endness.

Recording this as a finding because the note's stated *reason for* the placement rule does
not hold on most boards, not because the code diverges from the amended text. (For what
it is worth: the newest commit on `main`, `1db815d`, is titled "docs: say plainly that the
key fallback is the normal path at 11x9" — see F14.)

---

### F9 — the fallback key path skips the stable board ordering and can top up below the 6-tile separation the test asserts unconditionally

**Where:** `src/lighthouse/sim.nim:330-349` (fallback) vs `:371-381` (main path);
`tests/test_sim.nim:130-133`.

**What the code does** [read]:

- Main path: after the draw, keys are sorted into `(y, x)` order — "A stable board order so
  the viewer and the keeper's map agree" (`:373-381`).
- Fallback path: `sim.keysAt = picked; sim.keysOnFloor = picked; return` (`:347-349`) —
  **no** `(y, x)` sort. Order is still deterministic (it follows `tiles`, itself
  deterministically ranked at `:330`), but it is exit-distance order, not board order.
- Fallback top-up (`:342-346`): once the ≥ 6-apart greedy pass runs out, it appends any
  remaining tile with no separation check at all.

Meanwhile `tests/test_sim.nim:130-133` asserts pairwise BFS distance `>= 6` for **every**
seed, unconditionally.

**What the note says.** §Tests `test_sim` #3 permits the exception: "pairwise BFS distance
≥ 6 (**or the documented fallback**)". The shipped test is stricter than the note.

**Measured** [executed]: min pairwise key distance is ≥ 6 on all 13 seeds probed
(6, 6, 6, 6, 8, 8, 8, 12, 16, 20, …), so the top-up branch is not reached on any of them
and the unconditional assertion holds. Latent, not live.

---

### F10 — `applyTick` overwrites the whole `scripted` array, clearing resolved seats' flags

**Where:** `src/lighthouse/sim.nim:513` and `src/lighthouse/server.nim:326-335`.

```nim
  sim.scripted = scripted            # sim.nim:513 — wholesale replacement
```

```nim
        for index, seat in seats:    # server.nim:332-335 — only PENDING seats
          let decision = decisions[index]
          notes[seat] = decision.notes
          scriptedFlags[seat] = decision.scripted
```

**What the code does** [read]. `scriptedFlags` is a fresh zeroed `array[Seats, bool]` each
tick (server.nim:331), filled only for `pendingSeats()`. A runner that escaped or drowned
is not in `pendingSeats` (sim.nim:411-419), so from the next tick on its `scripted` entry
is `false` in `sim.scripted` and in every subsequent `evTick.scripted` and
`boardStateJson().seats[i].scripted`.

**What the note says.** §Decisions #2: the fallback is "logged `scripted: true` on that
seat's slot in the tick event" so "phase 60 can count it". Checklist item 8 requires the
fallback to be recorded.

**Effect** [read]. The per-tick record for the tick on which the fallback actually happened
is correct — the flag is written before the seat resolves. What is lost is the *carry* of
the flag on later ticks for an already-resolved seat, and the final `boardStateJson`. A
phase-60 counter that sums `evTick.scripted[seat]` over the ticks the seat played is
unaffected; one that reads the last frame would undercount.

---

### F11 — the subtitle ellipsis is not rune-safe

**Where:** `client/renderer.js:92-99` (`ellipsize`), used at `:789-841` (`drawSubtitle`),
line `:812` `var maxLines = box.w < 420 ? 2 : 1;`.

```js
  function ellipsize(ctx, text, maxWidth) {
    if (ctx.measureText(text).width <= maxWidth) return text;
    var cut = text;
    while (cut.length > 1 && ctx.measureText(cut + "…").width > maxWidth) {
      cut = cut.slice(0, -1);
    }
    return cut + "…";
  }
```

`String.prototype.slice` operates on UTF-16 code units, so a trailing astral character
(e.g. `🌊`, which the note's §Tests `test_replay` deliberately puts in messages) can be cut
between its surrogates, yielding a lone surrogate.

**What the note says.** Two things, in tension with each other. §Viewer, *Legible at
360 px*: "the subtitle plate wraps to at most two lines, **ellipsised on a rune-safe
boundary**". §Viewer, *Chrome reused verbatim*: `ellipsize` is one of the helpers "copied
unchanged" from babel's `client/renderer.js` — and babel's is exactly the code above.

**Scope** [read]. This is canvas rendering only. It cannot reach the replay bytes:
everything that reaches the replay goes through `cleanText` (llm.nim:162-169,
`runeSubStr`) or `runeSubStr` for prompts (server.nim:480-481). Checklist item 9 concerns
strings that reach the replay and is unaffected.

---

### F12 — `client/chrome.css` differs from babel's by more than the note's "byte-for-byte apart from the scorebug rules"

**Where:** `client/chrome.css:266`, `:288-292`, `:446-461`.

**Diff against `/workspace/starters/cogame-babel/client/chrome.css`** [executed]:

- `:266` `grid-template-columns: repeat(5, 1fr)` → `repeat(4, 1fr)` — **named in the note**.
- `:288-292` `min-width: 0; flex: 0 1 auto` → `min-width: 3.2em; flex: 1 1 auto` with a
  comment — **named in the note**, and byte-identical in substance to bullwhip's rule.
- `:446-461` a new block the note does not name: `.plate-status`, `.plate-msg`,
  `.plate.drowned .plate-name`, `.plate.escaped .plate-name`, `.feed-notes`, `.feed-tick`,
  a `@media (max-width: 640px)` block (verbatim from `cogame-bullwhip/client/chrome.css:460-463`,
  including `.plate-score` and `#scorebug` gap/padding, not just `.plate-label`), and a new
  `@media (max-width: 420px) { #scorebug { grid-template-columns: repeat(2, 1fr); } }`.

**What the note says.** §Packaging: "`client/chrome.css` is babel's byte-for-byte apart
from the scorebug rules named in §Viewer, which babel does not have." The 420 px block and
the six lighthouse plate/feed classes are not named in §Viewer. They are all consistent
with §Viewer's described chrome (status glyphs, message counts, notes lines) and are
additive; the note's "byte-for-byte apart from X" phrasing simply understates the delta.

The two rules checklist item 11 names are both present and correct:
`.plate-name { flex: 1 1 auto; min-width: 3.2em; }` at `:288-292`, and
`@media (max-width: 640px) { .plate-label { display: none; } }` at `:455-456`.

---

### F13 — `/client/replay` route, `client/replay.html` and the `/replay` websocket exist

**Where:** `src/lighthouse/server.nim:7` (doc comment), `:13`, `:447-451`
(`replayUpgradeHandler`), `:515` (`result.get("/client/replay", htmlHandler("replay.html"))`),
`:520` (`result.get("/replay", replayUpgradeHandler)`), `:541-565` (`runReplayServer`);
`client/replay.html` (74 lines); `src/lighthouse.nim:29-30`.

**What the code does** [read]. In replay mode the entrypoint starts `runReplayServer`,
which parses `runtimeConfig.replay`, precomputes `states` via `statesFromEvents` →
`replayMatch`, and serves a pod-side page at `/client/replay` plus the payload over
`WS /replay`.

**What the note says.** Two things, in tension. §Server, *Kept unchanged*: "the routes
(`GET /healthz`, `/client/global`, `/client/player`, **`/client/replay`**, …;
`WS /player`, `WS /global`, **`WS /replay`**)". §Out of scope (v1): "A live
`/client/replay` pod viewer. Replays are the static wasm bundle, always."

**What the checklist says.** Item 3: "No `/client/replay` pod path anywhere.
*(category: static-viewer)*".

**Context I verified** [executed]:

- Both starters ship the identical route and page:
  `cogame-babel/src/babel/server.nim:502` and
  `cogame-bullwhip/src/bullwhip/server.nim:470`, each with `client/replay.html`, and both
  manifests declare `"replay_viewer": {"bundle": "static-replay-viewer"}`.
- Lighthouse's manifest declares only the static bundle
  (`coworld_manifest_template.json:14-16`), never a `/client/replay` viewer URL.
- `coworld-release.yml:186-196` hard-fails certification unless the certify log reports the
  **static** replay bundle, with the error text "a pod-served `/client/replay` viewer is
  not acceptable".
- The static bundle contains no reference to it: `index.html` and `static_replay.js` never
  mention `/client/replay`, and `attachLive`'s `new WebSocket` (renderer.js:1288) is only
  reachable from `client/global.html`, which is not in the bundle.

I am recording the literal presence of the path because the checklist names it literally.
Whether starter-inherited dead code counts against item 3 when the manifest declares the
static bundle is a judgement I am deliberately not making.

---

### F14 — the reviewed sha is no longer the head of `main`

**Where:** n/a (repository state).

**Observed** [executed]:

```
$ git ls-remote origin main
1db815deb90d7c74951d92c39d2b8510efe524bb   refs/heads/main
$ git rev-parse HEAD
a16bebc62f3101598926913a76fcfba20be7d9f5
```

`gh run list -R Metta-AI/cogame-lighthouse --branch main -w ci.yml` shows the newer commit
is `docs: say plainly that the key fallback is the normal path at 11x9`, run
**32600520418**, `conclusion: success`. The brief named `a16bebc` as "the current `main`";
`main` has since advanced by one docs-only commit. Everything in this review was read at
`a16bebc`. `git log --oneline -- tests/` and `-- src/` show the newer commit touches
neither, but I have not read its diff.

---

### F15 — the drown-ordering test does not exercise the "escape chance before drowning" half

**Where:** `tests/test_sim.nim:232-245`.

```nim
  test "drowning happens after the move, the pickup and the escape chance":
    var sim = handSim(keys = @[(3, 6)], starts = [(2, 6), (5, 6), (7, 6)])
    sim.clock = 11
    check sim.waterLine() == 7
    sim.step([mvEast, mvWait, mvWait])
    check sim.keysCollected == 1        # move + pickup happened
    check sim.gateOpen
    check sim.waterLine() == 6
    check sim.status[0] == rsDrowned    # then drowned
```

**What the code does** [read]. Runner 0 moves to (3, 6), takes the key, the gate opens, the
clock advances, row 6 floods, all three drown. Nobody is ever on the exit tile `(1, 0)`, so
the **escape** leg of the ordering (step 7 before steps 9/10) is not asserted here.
`tests/test_sim.nim:200-215` asserts escape-vs-gate ordering but with no water in play.

**What the note says.** §Tests `test_sim` #5: "a runner standing on a row that floods this
tick drowns *after* it has had its move, its pickup **and its escape chance**."

**The code itself is correct** [read]: sim.nim:566-578 (step 7, escape, sets `pos` to
`(-1,-1)`) precedes sim.nim:581 (step 8, clock) and sim.nim:584-598 (steps 9/10, drown),
and step 10 skips anyone whose status is no longer `rsActive`. This is a coverage gap, not
a behaviour defect.

---

### F16 — runner starts are seed-independent at the shipped 11 × 9 board

**Where:** `src/lighthouse/sim.nim:251-277`.

**What the code does** [read + executed]. `placeStarts` builds the bottom room row
`{1, 3, 5, 7, 9}` (width 11), then shuffles and draws 3 with pairwise `|Δx| ≥ 4`, up to 50
attempts, falling back to `[rooms[0], rooms[len div 2], rooms[^1]]`. On five rooms spaced 2
apart, `{1, 5, 9}` is the **only** triple satisfying the constraint, and it is also exactly
the fallback. Confirmed over 13 seeds [executed]: every one gives
`starts = [(1,7), (5,7), (9,7)]`.

**What the note says.** §The game step 4: "Three distinct rooms on the bottom room row
`y = height - 2` (= 7), **drawn from the seed** subject to pairwise `|Δx| ≥ 4`".

The code does draw from the seed; the constraint just has a unique solution at width 11, so
the draw is degenerate. §Two name spaces' anti-pre-baking argument rests on "the maze is
fresh every episode" and re-drawn aliases, both of which do vary
(`initSim` → `carveMaze`/`placeExit`/`placeKeys`, `tableNames`; verified: grids, exits and
key sets all differ across the 13 seeds probed). The **starts** do not. Not a code/note
mismatch; an observation about what the shipped board makes of the rule.

---

### F17 — `evTick.notes` carries repeated notes, not `""`

**Where:** `src/lighthouse/sim.nim:616-618`, `src/lighthouse/types.nim:67`.

```nim
  for seat in 0 ..< Seats:
    record.notes.add(notes[seat])
```

**What the code does** [read]. `applyTick` records exactly the `notes` argument. The
server passes `decision.notes` (server.nim:334), which is `""` only when the reply omitted
or blanked the field (`cleanText("")` at llm.nim:649/669). A model that returns the *same*
notes text every tick writes the full string into every `evTick`.

**What the note says.** §Sim module event table, `tick`: "`notes` (`[string × 4]`, `""`
where **unchanged** this tick)"; `types.nim:67` repeats the wording.

**Effect** [read]. Replay size only; re-derivation is unaffected — `replayMatch`
(sim.nim:813-817) feeds the recorded notes straight back into `applyTick`, which keeps the
previous value on `""` (sim.nim:510-512), so the frames are identical either way, and
`tests/test_sim.nim:386` asserts `frames[^1].notes == sim.notes`.

---

## Confirmations

Everything below I opened, traced and found consistent with the note (as amended).

### The twelve resolution steps — `src/lighthouse/sim.nim:495-634`

Read step by step against §The game. `applyTick` implements steps 3–12 in exactly the
note's order:

| step | note | code | verdict |
|---|---|---|---|
| 1 Observe | state at start of tick; resolved runners not observed | `pendingSeats` sim.nim:411-419, snapshot taken under the lock before the batch (server.nim:313-314) | ✓ |
| 2 Decide | one parallel batch | `decideAll` llm.nim:691-739 (see below) | ✓ |
| 3 Transmit | `transmit && non-empty after truncation` → `spoke`, `evSay`, queued for `t+1` | `:516-525`; `let talking = spoke and text.len > 0`; `evSay` with `cost = 1`; `sim.inbox` set at `:623`, **after** the tick record | ✓ |
| 4 Moves | seat order 1,2,3; OOB/wall/flooded ⇒ bump, position unchanged | `:527-542`; `isWall` returns true off-grid (`:97-99`) so OOB is covered; `sim.blocked[index] = true` and no position change | ✓ |
| 5 Pickup | seat order; remove, `keysCollected += 1`, `keysHeld += 1`, `evKey` | `:544-560` | ✓ |
| 6 Gate | latch, never closes | `:562-564` `if sim.keysCollected >= sim.config.keyCount: sim.gateOpen = true` | ✓ |
| 7 Exit | seat order; on open gate ⇒ `escaped`, off board, `evEscape` | `:566-578`, sets `pos = (-1,-1)` | ✓ |
| 8 Clock | `+= 1 + (spoke ? 1 : 0)` | `:581` | ✓ |
| 9 Tide | recompute from new clock | pure functions `tideRows`/`waterLine` (`:102-115`) — nothing to recompute | ✓ |
| 10 Drown | still-active + flooded ⇒ `drowned`, off board, `evDrown` | `:584-598` | ✓ |
| 11 Record | `evTick` with the post-resolution board, then `tick += 1` | `:600-620` | ✓ |
| 12 End | (a) all three resolved → complete; (b) `clock >= floodClock` → complete; (c) `tick >= maxTicks` → timeup | `:628-634`, in that order | ✓ |

- **Clock/tide arithmetic.** `tideRows = clamp((clock - tideDelay) div tidePeriod, 0, height)`
  (`:102-105`), `waterLine = height - tideRows` (`:110-112`),
  `floodClock = tideDelay + height * tidePeriod` (`:114-115`), `flooded ⇔ y >= waterLine`
  (`:117-120`). Byte-for-byte the note's formulas. At the shipped defaults
  `floodClock = 10 + 9 × 7 = 73`; `tests/test_sim.nim:141-158` asserts monotonicity, the
  `clock < tideDelay ⇒ 0` boundary, `tideRows == height` at `floodClock`, and the flooded
  predicate for every row.
- **Collision-free movement.** No occupancy check anywhere in step 4;
  `tests/test_sim.nim:247-257` drives two runners onto one tile and then swaps them,
  asserting both succeed unblocked. ✓ §The game, *Collisions*.
- **`applyTick` raises only on impossible arguments** (`:500-507`): a call after `done`,
  or a non-`WAIT` move for a resolved runner. A blocked move is never an error. ✓ §Sim module.
- **Errors.** `endEarly` (`:636-642`) is idempotent and settles `"deadline"`;
  `tests/test_sim.nim:316-330` proves both, and that `reason ∈ {complete, timeup, deadline}`
  and nothing else.

### Maze generation — `sim.nim:161-407`

- **Seed stream.** `initRand(int64(config.seed) * 7919 + 17)`, one stream, drawn in the
  order maze → exit → starts → keys (`:396-402`). Exactly §The game's preamble.
- **Perfect maze.** `carveMaze` (`:161-196`) is an explicit-stack recursive backtracker over
  odd/odd rooms starting at `(1, height-2)` (`:174-176`), shuffling all four neighbours per
  room, carving the wall between (`:190-192`). Each room is carved exactly once, so the
  floor graph is a tree. `tests/test_sim.nim:84-106` asserts `edges == tiles - 1`, full
  reachability from the exit, and a sealed border but for the exit — green in CI on all four
  fixture seeds.
- **Exit.** `placeExit` (`:245-249`): `exitX = 1 + 2 * rng.rand(odds - 1)` with
  `odds = (width-1) div 2`; Nim's `rand(max)` is inclusive, so `exitX ∈ {1,3,5,7,9}` at
  width 11 — odd, in `1 .. width-2`, carved on row 0. ✓
- **Key placement constraints.** `y ≤ height - 4`, not a start, not the exit, Manhattan
  distance from the exit `> 1` (i.e. not adjacent), reachable (`:304-307`). Ascending exit
  distance via `rankByExitDistance(..., nearestFirst = true)` (`:279-289`, `:315-316`) —
  the amended note's ascending draw. Pool = nearest 8 (`:351`), 50 draws for pairwise
  BFS ≥ 6 (`:353-370`), on failure the 3 nearest outright (`:371-372`). ✓ §The game step 5.
- **Determinism.** `tests/test_sim.nim:429-442` asserts identical grid/exit/starts/keys/names
  for the same seed and a different grid for a different seed; `tableNames` (`:124-140`) uses
  its own stream `seed * 6779 + 31`, keeper from `KeeperNames`, runners from `CogNames`. ✓
- **Independently reproduced** [executed]: seed 11 (the certification fixture) carves
  ```
  #########.#   #.........#   #.###.###.#   #.#.#.#...#   #.#.#.#.###
  #...#.#...#   #####.###.#   #.....#...#   ###########
  ```
  with exit (9,0), starts (1,7)/(5,7)/(9,7), keys (3,3)/(1,3)/(5,5), aliases
  `["Fresnel","Tinker","Gasket","Piston"]` — **exactly** the `GRID`, `EXIT`, `STARTS`,
  `KEYS` and `NAMES` hard-coded in `client/fixtures/gen_fixture.js:14-30`. The dev fixture
  is genuinely seed-11-consistent, as its header claims.

### The decision path — `src/lighthouse/llm.nim:691-739`

- **One parallel batch per tick.** `decideAll` builds a single `RequestBatch`, `batch.post`
  per open seat, then `client.curl.makeRequests(batch, client.timeoutSeconds)` (`:714-723`).
  Structurally identical to bullwhip's `decideAll`
  (`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:419-472`), which the note
  names as the source. **No sequential per-seat call anywhere**; `server.nim:324` calls
  `decideAll` once per tick, outside the lock, on a snapshot. ✓ Checklist's
  simultaneous-decision clause.
- **Tolerant parse.** `extractJsonObject` (`:568-578`) takes `text.find('{') .. text.rfind('}')`,
  so prose and ```` ```json ```` fences are accepted; `tests/test_bot.nim:239-245` asserts
  the fenced case, the "Sure! {…} hope that helps" case, and rejection of pure prose. ✓
  Checklist item 8.
- **Exactly one retry, with a hint.** `for attempt in 0 .. 1` (`:711`); on `attempt > 0` the
  seat's user prompt gets `retryHint(seat)` (`:719-720`, `:681-687`), which is the note's
  wording verbatim, with the keeper variant naming `transmit` and `message`. ✓
- **Role-appropriate scripted fallback, logged.** `:736-739`:
  `echo "lighthouse llm: seat ", seat, " falling back to scripted decision"` then
  `scriptedAction(sim, seat, skAuto)` → `roleKind` (`:78-84`) picks `lantern` for slot 0 and
  `wallhug` otherwise. The note's exact log string. ✓
- **`scripted` flag recorded.** `lanternAction:350` and `wallhugAction:376` set
  `result.scripted = true`; LLM decisions leave it false; `server.nim:335` copies it into
  `scriptedFlags[seat]`; `sim.nim:618` writes it into `evTick.scripted`. ✓ (see F10 for the
  carry-over caveat).
- **No credentials ⇒ immediate scripted, no network.** `newLlmClient` (`:129-158`) sets
  `disabled = true` when neither Bedrock nor an Anthropic key resolves;
  `decideAll:706-708` short-circuits every seat to `scriptedAction` before the batch loop,
  and `:712` breaks out of the loop. `tests/test_bot.nim:170-194` asserts `client.disabled`,
  that all decisions are scripted and match `scriptedAction`, and that the whole call takes
  < 1000 ms. ✓
- **Blocked ≠ fallback.** A bump never enters `stillOpen`; only parse/transport failures do
  (`:727-734`). ✓ §Decisions #3.
- **Transport ported from babel.** Bedrock-bearer → `ANTHROPIC_API_KEY` →
  `ANTHROPIC_API_KEY_URI` (`:86-97`, `:135-158`), Haiku-first candidate list (`:99-113`),
  `output_config.effort` suppressed for haiku/4-5 (`:596-599`), `max_tokens` from
  `config.maxOutputTokens` (900), system prompt demanding "begin with the character { and
  end with }" (`:449-451`). ✓ §Decisions preamble.

### Every wait and its bound

| wait | where | bound | note says |
|---|---|---|---|
| LLM batch (both attempts) | `llm.nim:723` `makeRequests(batch, client.timeoutSeconds)` | `config.llmTimeoutSeconds`, default **18** (`types.nim:92`, schema 5..300 default 18) | §Decisions #4: 18 s, worst case 2 × 18 = 36 s ✓ |
| play deadline | `server.nim:296-312` — checked **inside the loop, before** `decideAll`, under the lock | `gameStart + timeoutSeconds * 0.6`, `PlayBudgetFraction = 0.6` (`:248`); `timeoutSeconds` from `COWORLD_TIMEOUT_SECONDS` else `config.episodeTimeoutSeconds` (1200) ⇒ **720 s**; past it → `endEarly()` → `reason = "deadline"` → `break` between ticks → results + replay written | §Decisions #5 verbatim ✓ Checklist item 5 |
| player connect | `server.nim:257-265` `while epochTime() < deadline … sleep(200)` | `config.playerConnectTimeoutSeconds`, default **180.0** (`types.nim:89`); the episode then starts with whoever connected (`:267-271`) and unregistered seats keep `skNone`/empty prompt | §Decisions #6 ✓ |
| spectator pacing | `server.nim:353-359` | `config.turnDelayMs`, capped by `sampleEpisode` to `PacingBudgetMs div maxTicks` = 15000/45 = 333 ≥ 250 (`sim.nim:151-152`) | §Budget arithmetic ✓ |
| artifact handshake | `server.nim:234`, `:244` | two fixed `sleep(500)` | §Server, `finishEpisode` ordering ✓ |
| main game loop | `server.nim:296` `while true` | terminates on `sim.done` (`:302`) or the deadline (`:304`); `applyTick` increments `tick` every iteration and settles at `maxTicks`; an `applyTick` raise is caught at `:346-350` and settles `deadline` | Checklist item 5, "no unbounded loop" ✓ |
| viewer fetch | `replay-viewer/static_replay.js:14`, `:71-88` | `FETCH_TIMEOUT_MS = 20000` via `AbortController`, with a Retry button and `tell("error")` | §Viewer, "the 20 s `AbortController` fetch bound … stays exactly as it is" ✓ |
| player container | `src/lighthouse_player.nim:58-83` | `while true: socket.receiveMessage()`, unbounded — but it is a **blocking read on a socket the game closes**: `finishEpisode` sends `final` then `quit(0)` (server.nim:229-246), and the player also breaks on `"final"` (`:76-78`). Byte-for-byte babel's loop (diffed: only strings, the default prompt and the `PLAYER_SCRIPTED` string change) | §Server, player, protocol: "verbatim except…" ✓ |

**Budget arithmetic re-checked** [read]. `sampleEpisode` (`sim.nim:142-153`) caps
`maxTicks ≤ EpisodeCallBudget div CallsPerTick = 220 div 4 = 55`, floors at `MinTicks = 4`,
caps `turnDelayMs ≤ 15000 div maxTicks`, and is idempotent via the `sampled` flag —
`tests/test_sim.nim:444-461` asserts all five properties including
`sampleEpisode(fitted) == fitted` and that the shipped 45/250 survive untouched. The
worst-case sum in §Budget arithmetic (558 s < 720 s) is arithmetic on these constants and
holds.

### String truncation on rune boundaries

- `cleanText(text, limit)` — `llm.nim:162-169`: `strip()`, then
  `if runeLen > limit: runeSubStr(0, limit - 1) & "…"`. Exactly bullwhip's truncator as the
  note specifies.
- **160** — keeper `message`: `MaxMessageLen` (`sim.nim:28`), applied at `llm.nim:650-652`
  and by `lanternMessage` (`llm.nim:277`).
- **400** — keeper `notes`: `MaxKeeperNotes` (`sim.nim:29`), `llm.nim:649`.
- **200** — runner `notes`: `MaxRunnerNotes` (`sim.nim:30`), `llm.nim:669`.
- **4000** — inbound `{"type":"prompt"}` frames: `server.nim:35` `MaxPromptLen = 4000`,
  applied at `:480-481` with `prompt.runeSubStr(0, MaxPromptLen)` — rune-based, per §Reply
  schema's "truncated on rune boundaries here too".
- **Captured errors** also go through `cleanText`: `extractJsonObject` quotes the reply head
  at `cleanText(text, 160)` (`llm.nim:575`), and the max-tokens error likewise
  (`llm.nim:637`).
- **Tested.** `tests/test_sim.nim:332-351` builds a 400-rune multi-byte string, checks
  `runeLen == 160/400/200` after truncation, and `validateUtf8 == -1` on every serialised
  event, on `resultsJson` and on `boardStateJson`. `tests/test_replay.nim:12-49, 80-96`
  builds a whole episode whose messages and all four seats' notes sit **exactly** on the
  160/400/200 boundaries using `≤ → 🌊 é 水`, serialises the full payload, and asserts
  `validateUtf8(payload) == -1`, `parseJson` succeeds, and a byte-identical
  `eventFromJson`/`eventToJson` round-trip. ✓ Checklist item 9.

### The replay writer — `server.nim:162-197`, `sim.nim:748-764`, `sim.nim:829-933`

- **Payload shape** matches §Replay payload exactly: `protocol` `"lighthouse.replay.v1"`,
  `names` (aliases), `policyNames`, `config`, `events`, `results` (`server.nim:176-190`).
- **Self-sufficiency.** `replayConfigJson` (`:162-175`) merges `seededConfigJson`
  (`grid`, `exit`, `starts`, `keys` — sim.nim:748-764) with `seed`, `maxTicks`, `width`,
  `height`, `tideDelay`, `tidePeriod`, `keyCount`, `messageCap`, `sampled: true`. The viewer
  needs no other input. ✓
- **Event vocabulary.** `eventToJson` (`sim.nim:829-890`) writes exactly the note's table:
  `start` → `{"kind":"start"}` alone (tick is `-1`, suppressed by `:831-832`);
  `say` → `seat`(0), `cost`(1), `text`; `key` → `seat`, `x`, `y`, `keysCollected`;
  `escape` → `seat`, `escaped`; `drown` → `seat`, `x`, `y`, `drowned`;
  `tick` → `clock`, `tideRows`, `positions`, `alive`, `moves`, `blocked`, `keysOnFloor`,
  `keysCollected`, `gateOpen`, `escaped`, `drowned`, `notes`, `scripted`;
  `end` → `tick` (= ticks played, `sim.nim:491`) and `text` (= reason).
- **Order within a tick** is `say` → `key`* → `escape`* → `drown`* → `tick`, which is the
  order `applyTick` appends them (`:525`, `:560`, `:577`, `:597`, `:619`). ✓
- **Round-trip.** `tests/test_sim.nim:410-427` drives an episode that produces **all seven**
  kinds and asserts `eventFromJson(eventToJson(e)) == e` and `$roundtrip == $original` for
  each, plus that every `EventKind` was seen.
- **`resultsJson`** (`sim.nim:646-671`) reports **policy** names
  (`sim.config.players[seat].name`, with a comment saying so), the same `teamScore` in all
  four `scores` slots, `roles`, and the ten scalar fields the note lists. The
  `results_schema` in the manifest (`:158-268`) requires exactly those thirteen keys with
  `additionalProperties: false`, `scores` 4 numbers in `[0, 42]`, and
  `reason ∈ {complete, timeup, deadline}`. ✓
- **`boardStateJson`** (`sim.nim:675-744`) emits the note's §boardStateJson object key for
  key, including `messageCost: 1`, `messageAge = max(0, tick - 1 - lastMessageTick)`
  (0 on the tick the message lands, since `tick` was already incremented), `phase`,
  `gameDone`, `reason`. `tests/test_sim.nim:496-516` asserts fourteen of those fields.
- **Scoring.** `teamScore` (`sim.nim:469-477`):
  `6 * clamp(K/keyCount) + 10 * E + 6 * B`, `B = clamp(1 - clock/floodClock, 0, 1)` only
  when `E == 3`. Positive sign, range `[0, 42]`, charged against the **clock**. Identical
  for all four seats. Hand-computed in `tests/test_sim.nim:259-299` for all three out
  (`6 + 30 + 6·bonus`), two out (`26.0` exactly), and total wipeout (`0.0`). ✓ §Scoring.

### Replay re-derivation and the viewer — checklist item 2

- **`replayMatch`** (`sim.nim:779-825`): `initSim(config)`, cross-check the recorded board,
  clear `sim.events`, push frame 0, then for each event append a frame — so
  `frames.len == events.len + 1` by construction. `say` is buffered into `spoke`/`message`
  and replayed by `applyTick`; `key`/`escape`/`drown` are discarded because `applyTick`
  re-derives them; `end` calls `settle(event.text)` only if not already done, which is what
  makes a `deadline` stop re-derivable. ✓ §Sim module.
- **The cross-check.** `checkRecordedBoard` (`:766-777`) compares the recorded `grid`,
  `exit`, `starts` and `keys` against `seededConfigJson()` and raises
  `"the recorded maze does not match the seeded one"`. Both call sites pass it:
  `server.nim:192-197` (`statesFromEvents`) and `replay-viewer/lighthouse_replay.nim:46`.
- **Tests.** `tests/test_sim.nim:353-390` drives a pseudo-random episode, round-trips every
  event through JSON, then asserts `frames.len == events.len + 1`, `frames[^1].done`,
  matching `reason`/`keysCollected`/`escapedCount`/`notes`, and
  `$frames[^1].boardStateJson() == $sim.boardStateJson()` — frame-by-frame identity from the
  recorded events alone. `:392-408` mutates one grid character and asserts the raise.
  `tests/test_replay.nim:98-118` does the same **through `lhLoadReplay`, the very proc
  exported to wasm, compiled natively**, asserting `states.len == events.len + 1` and
  `$states[^1] == $sim.boardStateJson()`; `:120-134` asserts the mutated-grid rejection with
  the exact error string. ✓
- **The viewer derives from that re-derivation, not a parallel recording.**
  `static_replay.js:91-119` hands the raw bytes to `_lh_load_replay`, reads back the enriched
  payload, and calls `LighthouseRenderer.attachReplay({… payload})`.
  `renderer.js:1419-1450` reads `payload.states` and `currentState()` returns
  `states[min(index, states.length-1)]`; the scorebug, clock, endscreen and canvas all draw
  from `currentState()` (`:1463-1499`). Nothing reads a recorded state array written by the
  server's live path. ✓
- **Static bundle.** `coworld_manifest_template.json:14-16` declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is
  committed **mode 100755** [executed: `git ls-files -s` → `100755 … tools/build_replay_viewer.sh`],
  compiles `replay-viewer/lighthouse_replay.nim` with `nim c -d:emscripten` or the pinned
  `Dockerfile.replay-viewer` container, asserts both artefacts non-empty (`:40-41`), and
  copies `lighthouse_replay.{js,wasm}`, `index.html`, `static_replay.js`, `renderer.js`,
  `chrome.css` and the six real assets (`:45-56`). `ci.yml:205-234` asserts the file exists,
  is `-x`, builds, and that the bundle carries a non-empty `index.html` and a non-empty
  `.wasm`.
- **No network but S3.** [executed] `grep -n 'fetch(\|XMLHttpRequest\|WebSocket'` over
  `renderer.js` + `static_replay.js` returns exactly two hits: `static_replay.js:76`
  `fetch(url…)` — the `?replay=` S3 GET — and `renderer.js:1288` `new WebSocket(url)`,
  which lives inside `attachLive`, reachable only from `client/global.html`, which is **not**
  in the bundle. Assets load from the relative `./assets` path inside the bundle itself
  (`static_replay.js:117`, `renderer.js:66-71`). ✓
- **`coworld-replay` bridge intact.** `static_replay.js:25-31` `tell()` with
  `{src: "coworld-replay", type}`, `tell("loading")` at `:31`, `tell("error", message)` at
  `:57`, `tell("ready")` at `:123` after two `requestAnimationFrame`s. `config.nims:41`
  exports `_lh_load_replay,_lh_payload_ptr,_lh_payload_len,_lh_error_ptr,_lh_error_len`
  under `EXPORT_NAME=LighthouseReplayModule`, matching the note's §Packaging list exactly. ✓

### Both name spaces — checklist item 4

- **Agents see aliases only.** `systemPrompt` (`llm.nim:425-461`) and both prompt builders
  (`:471-560`) address the seat by `sim.names[seat]`, which comes from `tableNames`
  (`sim.nim:124-140`). `policyNames` never enters a prompt. The player `final` frame carries
  aliases, not policy names — `server.nim:213-228` builds `aliasNames` from `state.sim.names`
  with a comment saying exactly that.
- **Viewer maps aliases → real names for non-baseline seats.** `makeNameMap`
  (`renderer.js:853-876`) is babel's `client/renderer.js:692-720` verbatim minus the
  babel-specific `glyphs`/`glyph` member, `isBaselineFiller` regex
  `/^baseline(\s*\(\d+\))?$/i` included byte-for-byte (`:849-851`). It is applied at
  `:1427` (replay), `:1272`/`:1294` (live), `:911`, `:941`, `:1012`, `:1120`, `:1137`
  (scorebug, feed, thumbnails, endscreen). Recorded events keep aliases; only rendering
  swaps. ✓

### The manifest — checklist items 6 and 10

- **`num_agents` present in every variant and in the certification fixture**:
  `standard` `:385`, `spring-tide` `:415`, `certification.game_config` `:443`. Also declared
  in `config_schema` as `{"type":"integer","minimum":4,"maximum":4}` (`:68-73`).
- **Seat counts agree**: `len(certification.players) == 4` (`:449-462`),
  `len(certification.game_config.players) == 4` (`:429-442`), `num_agents == 4`, and
  `SMOKE_SEATS` default `4` (`docker_smoke.sh:47`). `tools/ci/docker_smoke.sh:98-143`
  enforces all four invariants **before** `docker network create` (`:183`), each exiting
  non-zero with a `SEAT-COUNT FAIL:` prefix (`:105`, `:115`, `:123`, `:130`, `:140`).
  [executed] The docker-smoke job log for run 32600293001 contains **no** `SEAT-COUNT FAIL`
  and prints `game=lighthouse seats=4 … num_agents: 4 …` and `smoke OK: seats=4`.
- **`game.docs` shape** (`:280-295`): `{"readme": {"type":"text","value":…},
  "pages":[{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…}}]}` —
  exactly the checklist's required shape. The `rules.md` value reproduces the twelve
  numbered steps, the tide formula, the scoring formula and its sign, the observation split
  and both baselines, as §Packaging requires.
- **`game.protocols` carries both keys**: `player` (`:271-274`, the full
  `lighthouse.player.v1` frame catalogue including "a policy is just a prompt" and the
  `PLAYER_PROMPT`/`PLAYER_SCRIPTED` recipe) and `global` (`:275-278`, the `boardStateJson`
  snapshot plus `type`/`game`/`policyNames`/`events`/`started`/`done`/`connected` and the
  `index.html?replay=<url>` note). ✓
- **`config_schema` vs code defaults** — I checked every one:
  | key | schema | `defaultGameConfig()` | agree |
  |---|---|---|---|
  | `maxTicks` | 4..55, default 45 | 45 (`types.nim:74`) | ✓ (55 = `EpisodeCallBudget div CallsPerTick`) |
  | `width` | 9..25, default 11 | 11 (`:79`) | ✓ |
  | `height` | 9..15, default 9 | 9 (`:80`) | ✓ |
  | `tideDelay` | 0..40, default 10 | 10 (`:81`) | ✓ |
  | `tidePeriod` | 1..12, default 7 | 7 (`:85`) | ✓ |
  | `keyCount` | 1..5, default 3 | 3 (`:86`) | ✓ |
  | `episodeTimeoutSeconds` | 60..6000, default 1200 | 1200 (`:87`) | ✓ |
  | `turnDelayMs` | 0..2000, default 250 | 250 (`:88`) | ✓ |
  | `model` | default `claude-sonnet-5` | same (`:90`) | ✓ |
  | `maxOutputTokens` | 64..2000, default 900 | 900 (`:91`) | ✓ |
  | `llmTimeoutSeconds` | 5..300, default 18 | 18 (`:92`) | ✓ |
  | `player_connect_timeout_seconds` | ≥0, default 180 | 180.0 (`:89`) | ✓ |
  `additionalProperties: false`, `required: [tokens, players]`, both `minItems`/`maxItems` 4.
  Runtime validation in `update` (`types.nim:139-148`) enforces `maxTicks ≥ 4`, odd width/height ≥ 9,
  `keyCount ≥ 1`, `tidePeriod ≥ 1`; `initSim` re-validates (`sim.nim:384-395`). The shipped
  11 × 9 is inside the note's own unchanged schema ranges, as §Tuning revision claims. ✓
- **Three player runnables** (`:297-364`) with the note's ids, envs and resources
  (`requests {cpu 100m, memory 64Mi}, limits {cpu 1}`), all `{{LIGHTHOUSE_IMAGE}}` /
  `/bin/lighthouse-player`. Game runnable `:19-29` with `run: ["/bin/lighthouse"]`,
  `ANTHROPIC_API_KEY_URI: secret://coworld/lighthouse/anthropic_api_key`, the right
  `source_url`. Tags `:3-11` are the note's seven. ✓

### The scaffold — checklist item 12

- **Three workflows present**: `.github/workflows/{ci,coworld-release,coworld-submit}.yml`.
- **Release order.** `coworld-release.yml`, one `release` job: `coworld build` (`:146-159`,
  which builds the image from `compose.yaml` in this same run) → `coworld certify`
  (`:161-196`) → **Upload the policies** (`:198-…`, with an explicit comment "BEFORE
  upload-coworld") → `coworld upload-coworld` (`:303-333`) → `coworld secret put`
  (`:337-352`, "AFTER upload-coworld"). ✓ Certify additionally hard-fails unless the log
  reports the static replay bundle (`:186-196`).
- **`tools/ci/docker_smoke.sh` present and executable**: `100755` [executed], and `ci.yml:162-170`
  asserts both `-f` and `-x` and invokes it **by path** (`:181`), not through `bash`.
- **`tools/ci/policies.json` — four distinct policies** (`:1-31`): two `PLAYER_PROMPT`
  champions `lighthouse-beacon` (`:3-8`) and `lighthouse-pilot` (`:10-16`), plus two
  `PLAYER_SCRIPTED` fillers `lighthouse-lantern` (`:18-23`) and `lighthouse-wallhug`
  (`:25-30`). **Champion #2 — the second `PLAYER_PROMPT` entry, `lighthouse-pilot` — carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` at `:15`.** ✓ Both prompt texts
  match the note's §Decisions champion prompts (ASCII-dashed).
- **Placeholder gate** [executed]:
  ```
  $ grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/ci.yml \
      .github/workflows/coworld-release.yml .github/workflows/coworld-submit.yml \
      tools/ci/docker_smoke.sh tools/ci/policies.json ; echo $?
  1
  ```
  No matches → the gate exits 0. The four documented expected-residue names are all present
  and none is a placeholder: `<cow_id>`/`<sha>` in `ci.yml:185`, `<run_id>` in
  `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` in
  `coworld-submit.yml:31`. Substitution took: `ci.yml:28-29` `SLUG: lighthouse`,
  `IMAGE: coworld-lighthouse`; `docker_smoke.sh:5` "Substitute: lighthouse,
  coworld-lighthouse, 4" and `:42-47` the substituted defaults including
  `seats_expected="${SMOKE_SEATS:-4}"`. ✓
- **Packaging.** `compose.yaml` service name `lighthouse`, image `coworld-lighthouse:latest`,
  `platform: linux/amd64`, `build.context: .`, `network: host` — the note's §Packaging block
  verbatim. `lighthouse.nimble` requires `nim >= 2.2.4`, `bitworld >= 0.1.0`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`. `replay-viewer/config.nims:38` sets
  `EXPORT_NAME=LighthouseReplayModule`, output `lighthouse_replay.js`, and the exact
  `EXPORTED_FUNCTIONS` list from §Packaging.

### Scripted baselines and the competence floor — checklist item 7

- **`lantern`** (`llm.nim:220-350`) follows §Decisions step by step: BFS from the exit and
  from every uncollected key over **unflooded** floor (`:225-228`, `avoidFlooded = true`);
  greedy nearest-pair (runner, key) assignment sorted ascending with ties by runner then key
  index (`:236-252`); leftovers target the exit (`:230-232`, `:257`); the **one-step-ahead**
  aim (`:263-269`) exactly as §Tuning revision specifies, holding when the runner is already
  there or no path exists; message `"<Alias> <step>; …"` through `cleanText(…, 160)`
  (`:271-277`); and the transmit policy with **never twice in a row**
  (`justSpoke`, `:345-349`), the `tick mod 2 == 0` rhythm, repeat-suppression
  (`repeat`, `:347`) and the four exceptions (`:308-334`). Deterministic, no RNG, no notes.
- **`wallhug`** (`llm.nim:372-408`): obey the inbox, else a standing order aged ≤ 3
  (`StandingMaxAge = 3`, `:37`, `:381-385`); ordered `hold` ⇒ wait (`:388-389`); blocked ⇒
  nearest compass angle **clockwise-first** (`turnRight`, `turnLeft`, `turnBack`, `:395-399`)
  matching the note's "ties → clockwise"; else left-hand wall-following
  `left → straight → right → back` (`:403-407`) with the heading derived from the last
  non-`WAIT` move and defaulting north (`headingOf`, `:359-370`); all-blocked ⇒ `WAIT`.
  No RNG, no notes. (The one divergence — the water-under-key glyph — is F1.)
- **Role substitution.** `roleKind` (`:78-84`) forces slot 0 → `lantern` and every other
  slot → `wallhug` whenever anything is registered; `server.nim:487-491` logs
  `"lighthouse: slot N registered X; playing Y for its role"` exactly as the note specifies.
  `tests/test_bot.nim:145-168` asserts all eight `roleKind` combinations, all seven
  `parseScriptKind` values, and that the substituted decisions really have the other
  baseline's shape.
- **Full legal episodes to the natural end.** `tests/test_bot.nim:86-106` drives
  `lantern` + three `wallhug` per seed and asserts `done`,
  `reason ∈ {complete, timeup}`, `tick ≤ maxTicks`, wall clock `< maxTicks × 50` ms,
  `0 ≤ scores ≤ 42`, and `validateUtf8($results) == -1`. Per-move it asserts the five legal
  tokens (`:60`), `runeLen ≤ 160` and valid UTF-8 on every message (`:56-57`), and
  `notes.len == 0` on both baselines (`:50`).
- **Competence floor, measured** [executed, and matching the CI log verbatim]:
  ```
  seed 1:    27 ticks, clock 41, keys 3, escaped 2, drowned 1, score 26.00, talked 14/27
  seed 7:    25 ticks, clock 38, keys 3, escaped 3, drowned 0, score 38.88, talked 13/25
  seed 42:   35 ticks, clock 53, keys 3, escaped 3, drowned 0, score 37.64, talked 18/35
  seed 1234: 37 ticks, clock 56, keys 3, escaped 3, drowned 0, score 37.40, talked 19/37
  seeds with every key collected: 4/4; seeds with all three out: 3/4
  talk rates 0.5185 / 0.5200 / 0.5143 / 0.5135      (bar: ≤ 0.60)
  instruction following: 130/146 = 0.8904            (bar: ≥ 0.80)
  ```
  Every number in §Tuning revision's "Measured outcome" paragraph reproduces exactly:
  4/4 keys, 3/4 all-out, 51–52 % talk, 89 % instruction-following, scores 26–39, episodes
  25–37 ticks with one drowning on seed 1. The thresholds in `tests/test_bot.nim`
  (`rate <= 0.60`, `keyed >= 3`, `allOut >= 2`, `rate >= 0.80`) are the note's §Tests numbers
  as written, and **none was weakened** [executed: tests/ has exactly one commit, all
  additions].
- **Tuned with a harness, not guessed.** §Tuning revision documents the oracle
  (min over key→runner assignments of max over runners of `dist(start,key)+dist(key,exit)`),
  the 17 × 11 measurements (55/47/53/81 on the fixture seeds; 47–93 over sixty), and the
  swept `tidePeriod` grid (4, 5, 6, 8, 10, 14 × `maxTicks` 45, 55). `README.md:86-113`
  repeats it in a Deviations table. The harness itself is not committed — see
  *Could not determine*.
- **CI item 1, second half** [executed]: `git log --oneline --all -- tests/` →
  a single commit, `8f57cf7`. `git log -p 4919c7c..a16bebc -- tests/` shows additions only:
  no deleted assertion, no widened tolerance, no `skip`/`xfail`, no removed file.

### Per-seat observation split — `llm.nim:425-564`

Traced against §Per-seat observation, line by line.

*Keeper (`keeperPrompt`, `:471-524`)* gets: the whole grid via `keeperView`
(`sim.nim:446-454`, `height` lines of `width` chars) with the note's exact glyph legend
(`:474-476`); per-runner alias, `(x, y)`, status, last move and BUMPED flag, keys carried
(`:477-492`); `tideRows`, `waterLine`, `clock`/`floodClock` (`:493-498`) and
**`ticksUntilNextFlood` computed both ways** — "The next row floods in N tick(s) if you stay
silent, in M tick(s) if you transmit every tick" (`:502-504`, `floodCountdown` at
`:463-469`, `M = (need+1) div 2`); `tick`/`maxTicks` (`:472`); keys and gate (`:505-507`);
its own notes (`:508-510`); and the last **5** transmissions with their ticks
(`TranscriptLen = 5`, `:33`, `:511-518`). It never receives another seat's notes — the only
`sim.notes` access is `sim.notes[KeeperSeat]`.

*Runner (`runnerPrompt`, `:526-560`)* gets: the 3 × 3 window with `@` for itself and `#`
off-grid (`:530-534`, `runnerWindow` at `sim.nim:456-467`); `keysIHold`,
`keysCollected`/`keyCount`, `gateOpen` (`:535-539`); `tick`/`maxTicks` (`:528`); `inbox`
verbatim or `(silence)` (`:540-542`); the standing order with its age (`:543-548`,
`standingAge` at `sim.nim:482-483`); its own notes (`:555-556`); and its last **6** moves
with their `(blocked)` markers (`MoveHistoryLen = 6`, `:35`, `:549-554`). It never receives
the map, its coordinates, `clock`, `tideRows`, `waterLine`, other runners' state, or any
other seat's notes — [executed] `grep` confirms `runnerPrompt` contains no `sim.pos`,
`sim.clock`, `sim.tideRows`, `sim.waterLine` or `sim.grid` reference.

*Player-socket frames* are redacted the same way: `playerStateJson`
(`server.nim:96-135`) sends only the seat's own status/keys/lastMove/blocked/messages plus
team-level counters — no grid, no coordinates, no tide, and no other seat's notes.

### Reply schema and parsing

- **Keeper** (`parseKeeperReply`, `llm.nim:641-664`): `transmit` absent ⇒ inferred from a
  non-empty message (`:654`); a `JBool`, `JString` (`"1"/"true"/"yes"`) or `JInt` flag all
  honoured (`:655-661`); empty or whitespace-only message ⇒ silence whatever the flag says
  (`:662-664`, since `cleanText` strips); `notes` capped at 400 and, when absent, left `""`
  so `applyTick:510-512` keeps the previous notes. ✓
- **Runner** (`parseRunnerReply`, `:666-675`): missing `move` raises, non-string `move`
  raises, `parseMoveToken` raises on anything outside the token set. ✓
- **Tested exactly as §Tests #8 lists**: `tests/test_bot.nim:196-237` covers
  `{"move":"north"}`, `{"move":"n"}`, `{"move":" E "}`, `{"move":"WAIT"}`, `{"move":"left"}`
  (plus `"Down"`, `"hold"`), rejects `{"move":"NE"}`, `{"move":42}`, `{}`,
  `{"notes":"no move"}`, and asserts `{"transmit":true,"message":"   "}` is silence and
  `{"message":"go N"}` transmits.

### Viewer composition — `client/renderer.js`, `replay-viewer/index.html`

All twelve readouts in §Viewer are present, with the note's own constants:
god-view maze with masonry walls (`drawWall` `:281-299`) and integer-scaled letterboxing
(`computeLayout` `:225-…`); portcullis exit with a keyhole `n/3` plate and a
`GATE_FLARE_MS = 600` flare (`drawPortcullis` `:335-…`, `:43`); bobbing amber keys
(`drawKey` `:301-333`); fog scrim `rgba(12, 10, 8, 0.62)` (`SCRIM`, `:48`, `fogLayer`
`:405-413`); tide `rgba(58, 124, 140, 0.55)` (`WATER`, `:46`) easing over
`TIDE_EASE_MS = 500` (`:42`) with a `DROWN_BURST_MS = 700` bubble burst (`:44`,
`drawBubbles` `:660-681`); the radio subtitle plate with a `◉ +N TICK` badge
(`drawSubtitle` `:789-841`, badge text at `:837`) holding `PICK_HOLD_MS = 2500` then fading
`PICK_FADE_MS = 700` (`:38-39`) and drawing `— silence —` when empty (`:813`); three corner
thumbnails (`drawThumbnails` `:723-787`) collapsing at 520 px and hiding at 420 px
(`:223-228`, `:616`); the rotating lighthouse beam (`drawLighthouse` `:683-721`); the
four-plate scorebug (`updateScorebug` `:1112-1150`) with `◉` message count + `MSGS` label +
team score on the keeper plate and pips + status glyph + `▶` pending on the runners; the
clock `TICK n / 45 · TIDE ROW w · KEYS k/3 [· FINAL]` (`matchHeader` `:1098-1110`); the feed
with one `TICK n` head per tick and the note's phrasings — `Fresnel: "…" (+1 tick)`,
`moves north`, `bumps a wall`, `takes a key (2/3)`, `THE GATE OPENS`, `escapes`,
`is taken by the tide`, `Final — 2 of 3 out, 3 keys, score 26.0` (`describeEvent`
`:909-931`, `tickText` `:933-955`, `endText` `:957-963`, `renderFeed` `:969-…`); and the
endscreen with the four verdicts, the `timeup`/`deadline` reason lines and the columns
`role, status, keys, messages, score` (`verdictText` `:1152-1161`, `reasonLine` `:1163-1172`,
`updateEndscreen` `:1174-…`). `index.html` carries the note's exact element ids and the
`LIGHT<span>HOUSE</span>` wordmark. Nothing renders internal notation.

### Server wiring

Routes (`server.nim:511-522`) are babel's set; the asset handler blocks `/`, `\` and leading
`.` (`:381-383`); **Ping → Pong is answered in `websocketHandler`** (`:466-468`) with the
comment about the certifier; `writeArtifact` honours `COGAME_RESULTS_METHOD` /
`COGAME_SAVE_REPLAY_METHOD` (`:146-160`); `finishEpisode` sends `final` to players **first**,
`sleep(500)`, writes results, writes the replay, `sleep(500)`, `quit(0)` (`:199-246`) — the
note's ordering exactly. The tick loop is deadline-check → snapshot under lock → `decideAll`
**outside** the lock → `applyTick` under lock → `broadcastLocked()` → `sleep(turnDelayMs)`
(`:296-355`), which is §Server's description verbatim. `src/lighthouse.nim:26-48` reads the
runtime config, branches to replay mode, randomises an unpinned seed **before**
`sampleEpisode` (`:34-42`), and starts the game server.

---

## Could not determine

1. **Whether the grid harness behind §Tuning revision's sweep is reproducible.** The note
   describes an oracle and a `tidePeriod` × `maxTicks` sweep; no harness script is committed
   (`tools/` holds only `build_replay_viewer.sh` and `ci/`). I reproduced the *outcome*
   (4/4 keys, 3/4 all-out, 51–52 % talk, 89 % obedience) exactly, and the §Tests
   competence/oracle test at `tests/test_bot.nim:117-131` is the committed decision rule —
   but the sweep itself is only attested by the note and `README.md:86-113`. What would
   settle it: the harness committed under `tools/`, or its output pasted into `runs/…/log.md`.
2. **Whether the newest `main` commit `1db815d` changes anything material.** I reviewed
   `a16bebc` as briefed. `git log --stat` shows `1db815d` touches neither `src/` nor `tests/`,
   and its CI run 32600520418 is green, but I did not read its diff. What would settle it: a
   one-line confirmation of which files it touches, or re-pointing the review at it.
3. **Whether `/client/replay` (F13) counts against checklist item 3.** The checklist says
   "anywhere"; the design note keeps the route deliberately in §Server while forbidding a
   live pod viewer in §Out of scope; both starters ship it identically; the manifest declares
   only the static bundle and the release workflow hard-fails on a pod-served viewer. This is
   a scope question about the checklist's wording, not a fact about the code, and I have
   deliberately not resolved it.
4. **Whether the F1 water-under-key bump ever costs an episode.** I found it on 1 of 16 seeds
   (5 ticks lost, episode still completed). What would settle it: a wider seed sweep of
   `escapedCount` with and without the glyph priority corrected.
5. **Behaviour under a live LLM.** Everything about the LLM path — real batch latency,
   the 18 s bound in practice, the retry rate, the 720 s deadline — is untested here; the
   sandbox has no credentials and CI runs the no-credentials path only
   (`docker_smoke.sh:186-191` prints "no ANTHROPIC_API_KEY: the game must complete on its
   scripted baselines"). This is phase-60 territory.

---

## Summary

**17 findings**, of which four are reproduced by execution against the real sim (F1, F2, F8,
F16), one is a repository-state note (F14), and the rest are read from the code. The
strongest pair is **F1 + F2**: `wallhug` can order a move into open water because a key glyph
masks the water glyph, and the test that is supposed to catch exactly that
(`tests/test_bot.nim:73-74`) uses `and` where it needs `or`, which makes it vacuous. **F3**
(pre-retune 17/11/4 fallbacks in both replay-config readers) and **F4** (the note's viewer
smoke checks absent from CI) are the other two that touch named checklist items directly.
Everything in the *Confirmations* section I opened and traced; the twelve resolution steps,
the tide and scoring arithmetic, the one-parallel-batch decision path with its single hinted
retry and role-appropriate logged fallback, every wait and its bound, the four rune caps, the
replay writer and its frame-by-frame re-derivation through the wasm entry point, the manifest
(`num_agents` ×3, `game.docs`, both protocols, schema-vs-code defaults), the scaffold
(three workflows, both scripts `100755`, four policies with champion #2's `player` id, clean
placeholder gate), and the viewer chrome (both 360 px rules, `makeNameMap`, no network but S3)
all match the note as amended.
