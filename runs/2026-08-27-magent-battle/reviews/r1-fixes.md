# r1 fixes — magent-battle

Repo: `Metta-AI/cogame-magent-battle` @ **`3c85c8d428f71b64771a1768107bf5d55d964a28`** (main)
Head before: `95e94c9853de770c9afdea85d8d8144e80df9374`
CI: <https://github.com/Metta-AI/cogame-magent-battle/actions/runs/33057473716> — **success**
(all four jobs `test`, `manifest`, `docker-smoke`, `wasm-viewer` green; **170 `[OK]`, 0 `[FAILED]`**
across the four shards in debug and release, up from 164 — no test was deleted, skipped, loosened or
widened; every change to `tests/` in this round ADDS assertions, and the two it rewrote
(`test_magent_engine`'s closed payload, `test_magent_endcard_labels`' presence check) are strictly
stronger afterwards.)

Local commits were replayed onto the remote through the Git Data API (one remote commit per local
commit, ref moved once), so the shas below are the REMOTE ones and are what the judge should read.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | no change — already recorded and asserted | — | `vendor/PATCHES.md` §7, `tests/test_magent_spawn.nim:83` |
| F2 | fixed | `05b9692` | `vendor/PATCHES.md:1-14` |
| F3 | fixed | `24117ab` | `src/magent/sim_types.nim:46-51`, `vendor/PATCHES.md` §9 |
| F4 | fixed | `d2336d6` | `client/broadcast_core.js:1-46,164-176,442-463` |
| F5 | fixed | `b039266` | `tests/test_magent_viewer.nim:108-124` |
| F6 | fixed as documented divergence (behaviour unchanged) | `abdac5e` | `vendor/PATCHES.md` §10 |
| F7 | fixed | `652020a` | `src/magent/sim_types.nim:110-124`, `src/magent/llm.nim:181-186`, `tests/test_magent_replay.nim:246-266` |
| F8 | fixed (`disconnected` emitted; `throttled` documented) | `5060520` | `src/magent/decide.nim:244-255`, `docs/PROTOCOL.md:135-157`, `tests/test_magent_engine.nim:64-74` |
| F9 | fixed | `47baf4f` | `.github/workflows/ci.yml:407-421` |
| F10 | fixed | `0c35f69` | `tools/ci/renderer_fixture.html:53-74,151-166` |
| F11 | fixed (both halves) | `dcc4349` | `client/page_script.js:469-481,525-535`, `client/game_block.html:210-232,331-360` |
| F12 | fixed | `8f3e60a` | `client/game_block.html:331-337` |
| F13 | fixed | `cf945d3` | `src/magent/broadcast.nim:186-210,237` |
| F14 | fixed | `4cb6fae` | `client/game_block.html:1-12` |
| F15a (duplicated caps) | fixed | `3c79553` | `src/magent_battle_player.nim:20-36` |
| F15b (unreachable event kinds) | fixed | `8a18705` | `src/magent/episode.nim:89-108`, `src/magent/sim_types.nim:35-40`, `src/magent/broadcast.nim:58`, `src/magent/replay_runtime.nim:169`, `tests/test_magent_engine.nim:76-108` |
| F15c ("present exactly once") | fixed | `885a968` | `tests/test_magent_endcard_labels.nim:24-46,92-108` |
| F15d (no `tune_baselines --check` in CI) | fixed | `51b82ee` | `.github/workflows/ci.yml:152-164` |
| F15e (`p0.log`/`p1.log`) | fixed | `1b886c0` | `.gitignore`, `p0.log`, `p1.log` (deleted) |
| F15e (`nim.cfg` "committed AND ignored") | **DISPUTED** | — | `git ls-tree 95e94c9 -- nim.cfg` → empty |
| F15f (failure payload asserted against a literal) | fixed | `5f68303` | `src/magent/roster.nim:130-136`, `src/magent/server.nim:290-301`, `tests/test_magent_engine.nim:51-63` |
| F15 (league_replayer.html, magentReward strings, MaxUnits 400, object `orders`, Dockerfile `.data`, "connects then never answers") | **no change — argued below** | — | — |
| F16 | no change — the note's table is stale, the tree is right | — | `coworld_manifest_template.json:4,114,202` |
| F17 | fixed | `900d9d0` | `coworld_manifest_template.json:114` |
| F18 | fixed by CONFORMING to the checklist (note says otherwise) | `dd7a833` | `coworld_manifest_template.json:30-53`, `tools/embed_manifest_docs.py`, `tests/test_magent_manifest.nim:93-121` |
| F19 | fixed | `3c85c8d` | `client/page_script.js:577-584`, `client/game_block.html:68-72`, `tools/ci/renderer_fixture.html:39-42`, `tests/test_magent_viewer.nim:216-219` |

Nothing in `prompts/`, `agents/`, `fleet/`, `docs/SPEC.md`, the review report or the design note was
touched. `client/replay_broadcast.html` was regenerated three times (F11, F12, F14, F19) with
`tools/build_broadcast_page.py` against the read-only starter — never hand-edited — and F5's new
byte pin on the inherited prefix (60,731 B, SHA-1 `753E95A5…6395`) is unchanged by all four, which is
itself the evidence that only the appended block moved.

---

## F1 — `mapSize 31` spawns 30 per army, not 25 — no change

The reviewer's own assessment is that the delta is sound, is filed in `PATCHES.md` §7, is asserted by
`tests/test_magent_spawn.nim:83-85`, and is propagated into the manifest. There is nothing left to
fix: the note's 25 came from miscounting a `range(9,21,2)` as five rows, and the note itself told the
builder to "assert the number rather than trusting this paragraph". Evidence: `PATCHES.md` §7 and the
green `spawn` suite in run 33057473716.

## F2 — PATCHES.md's title did not cover the note-vs-code sections — `05b9692`

The file was titled "Documented divergences from upstream `battle_v4`" while §6 and §7 are
divergences from the design note. Title and preamble now name both kinds and say which sections are
which (1-5 and 8 upstream; 6, 7 and above the note), so the two later additions in this round (§9,
§10) land in a file whose title covers them. Doc only.

## F3 — the superseded playback model in `sim_types.nim` — `24117ab`

`TargetFps`'s doc-comment still said "one tick per animation frame at 30 fps, so 600 ticks of episode
play for 20 s", contradicting `replay_runtime.nim:13-20` (`TicksPerSecondBase = 8`) two files away,
and the delta was recorded nowhere. The comment now says what `TargetFps` actually is (the
presentation rate and the accumulator's denominator) and points at the new `PATCHES.md` §9, which
records the rate, the missing `0.5` chip, and why 8 ticks/s serves the note's own stated reason (a
soak must observe advancement) better than 1 tick/frame. Evidence for the rate, from this run's soak:
`0 / 117 → 59 / 117 → 75 / 117` over 10 s ≈ 7.5-8 ticks/s.

## F4 — `broadcast_core.js`'s provenance header overstated what was kept — `d2336d6`

The header claimed the file kept the starter's core "function for function", naming `pushFeed` as
inherited — and `pushFeed` does not exist in coworld-ctf's core at all. The header now states plainly
that this is a retargeted rewrite (a sprite-protocol/pixel-camera core cannot be line-forked onto an
integer cell grid; no proc in it is byte-identical) and enumerates what genuinely IS inherited: the
module shape, every method `static_replay_worker.js` and `page_script.js` call, the callback
contract, the `getPaceStats()` shape the adapter mirrors, `pushFeed(text)`'s SIGNATURE (the cogball
latch — the one name whose shape rather than body is the inherited thing), the websocket mode and the
`?embed=1` path. It also states that the core draws no text at all, which is why both smoke steps
report `canvas text: 0` legitimately.

The same commit removes the core's own feed-row formatter, which F4 traced as dead: the rows went to
`onText`, and the page's `onText` is its JSON frame parser, so every row was parsed, failed and
dropped while the game block built the visible feed from the same events. That also removed a second
copy of the feed vocabulary (`FIRST BLOOD`, `IS ROUTED`, …) that no gate covered. `pushFeed` and the
pace queue stay, because `getPaceStats().queued` reports them and `test_magent_viewer.nim:232` pins
the signature.

## F5 — nothing on main would catch a hand-edit of the inherited page — `b039266`

`tools/build_broadcast_page.py` reproduces the committed page from the starter byte for byte (I
re-verified: `cmp` silent), but it needs the read-only starter mount, which no CI runner has — so the
note's promised "a test asserts the starter's byte prefix is intact" was absent in practice. The new
test hashes exactly the inherited region (everything before the forked page IIFE, i.e. up to the
`<script>` after the `BROADCAST_CORE` marker) and pins its length and SHA-1 as literals, so an edit
above the splice fails on a runner with no mount. Evidence: `[OK] the inherited page prefix is
byte-pinned`, both modes, run 33057473716.

The note's other half — "the file only grows" — is not implemented and should not be: the fork
legitimately *shrinks* the page by deleting `#viewpanel`, `#fpv*`, the ctf plate internals and ~15 KB
of base64 heart PNGs. Recorded here rather than "fixed".

## F6 — `turnSpacingMs` is a blocking sleep — `abdac5e` (documented, no behaviour change)

Real and reproduced: `decide.nim:252-255` sleeps on the game loop, so no tick advances during the
rate floor, and because `turnStart` is taken before it the worst case inside one turn is 8 + 9 = 17 s
against a 14 s `turnBudgetMs` (the budget then suppresses the retry, not the first call). Every wait
is still explicitly bounded and the episode arithmetic still fits: ~615 s worst case < 660 s stop <
720 s settle target, and a stop landing mid-turn is served at most 17 s late (677 s).

Making the wait non-blocking is a **design change, not a fix**: `engine.turn` would have to become a
state machine polled by `runEpisodeFrame` instead of a proc that runs a turn and returns its records.
I did not make it. `PATCHES.md` §10 records the divergence, the bound at each site, the arithmetic,
and the one observable cost (a live LLM episode holds the board still for up to 8 s between command
turns; the replay is unaffected, because playback derives every frame from the recorded orders).

## F7 — the reply cap was enforced in runes, not bytes — `652020a`

`if body.len > MaxReplyBytes: body = body.truncateRunes(MaxReplyBytes)` — a byte test with a rune
cut, so up to ~32 KB of a multi-byte body reached `parseJson`. Added `sim_types.truncateBytes`: cuts
at most `limit` bytes and backs off over continuation bytes, so the result is valid UTF-8 if the input
was, and used it at the one cap that is genuinely a byte budget. Every rune cap elsewhere is
untouched. Test: 4-byte emoji filled past the cap (cut ≤ 8192, loses at most one codepoint,
`validateUtf8() == -1`) and a 3-byte codepoint straddling the cap (dropped whole, not halved) —
`[OK] the reply byte cap cuts bytes on a codepoint boundary`.

## F8 — the cause vocabulary — `5060520`

Two halves, handled differently:

* **`disconnected` never emitted** — fixed. A seat with `not sim.joined[seat]` now writes one
  `fallback` record per turn with cause `disconnected`, so a replay reader can tell "nobody was home"
  from "a scripted filler was seated". The directive stays `scripted` (a seat that never registered
  has no policy to fall back FROM), so `llmTurns`/`fallbackTurns` are unchanged and no existing
  assertion moves. `tests/test_magent_engine.nim`'s "no seat can stall" now parses the replay bytes
  and asserts every fallback record is slot 1 with cause `disconnected`.
* **`throttled` is not in the note's enum** — kept, and documented. A 429 with no other candidate
  model needs a different answer from a broken transport, and nothing consumes the set as closed.
  `docs/PROTOCOL.md` now carries the full cause table with a line saying `throttled` is the
  divergence and why.

## F9 — the smoke never soaked — `47baf4f`

`--soak 10` added to `ci.yml`'s browser step. Evidence, run 33057473716, step "Load the bundle in a
real browser":

```
soak: 10s of playback kept advancing ("0 / 117" -> "59 / 117" -> "75 / 117")
```

Advancement is now gated (the harness fails unless the LAST interval moved), which is the cogball
0.1.4 freeze class the soak exists for and what the note asked for.

## F10 — the fixture did not assert its own strings — `0c35f69`

Checklist item 15's exact clause. Before rendering anything the fixture now fails unless `CAP_SAY` is
still 120 runes (`MaxSayRunes`) and still ends on the two cap-straddling 4-byte emoji, and unless the
long policy name is still long enough to crowd a 360 px plate; after rendering, each width asserts the
laid-out row's `textContent` still CONTAINS the whole remark, so a page-side truncation fails instead
of leaving a correctly-sized box holding a shortened sentence. Evidence: the fixture step reports
`{"loaded":true,"ms":2049}` and `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` — a
failed assertion sets `data-replay-error`, which the harness fails fast on.

## F11 — verdict and spoilers — `dcc4349`

* `#scrub-win` / `#win-chip` stayed empty for the whole replay because `chrome_common.ingestBeats`
  only knows `steal/return/capture/gameover`. The endcard now calls `setVerdict` on the frame the
  pair completes — the chrome's own documented fallback path ("older servers that ship no beats still
  get the verdict once playback reaches the end") — with this game's vocabulary: the ALIAS takes the
  pair (or `DRAW`), never a colour, so the endcard re-mapping table still holds and the forbidden-word
  gate stays green.
* `applySpoilers` walks only the chrome's own `markerEls`, so with spoilers OFF this game's five beat
  kinds still sat ahead of the playhead while `#btn-spoilers`' retitled tooltip promised otherwise.
  The block now applies the identical rule (`__tick > s.t`) to the buttons it appended, every frame
  and on the toggle itself (button click and the `o` key), so a flip while paused takes effect.

`chrome_common.js` is untouched and still byte-identical (its pinned length 40022 / SHA-1 assertion is
green).

## F12 — duplicate beat button after a backward seek — `8f3e60a`

`if (jumped) placed = {};` cleared the dedup map without removing the buttons already on `#scrub`, so
a live `fallback`/`firstblood` replayed after the seek appended a second identical marker. The reset
is gone (a marker is a permanent annotation of the timeline; nothing removes the nodes, so the dedup
map must persist too). Feed and banner clearing on a jump is unchanged.

## F13 — the live dev page's inert transport axis — `cf945d3`

In live mode `replayPlayer` is default-initialised, so the packet carried `t=0, st=0, mx=1` and empty
`lulls/beats/lead`: `#tick-clock` read `0 / 1` with a static playhead, and an empty `lead` object
disabled `chrome_common`'s own accumulate-as-played momentum fallback. Live frames now take the axis
from the sim clock (`tick` of `maxTicks`) and OMIT the three pre-scanned series, which only exist for
a recorded episode. Replay mode is unchanged field for field —
`[OK] the state packet the viewer consumes is well formed` still asserts all fourteen keys including
`lulls/beats/lead`.

## F14 — the CI scrub click was swallowed by the muster curtain — `4cb6fae`

Confirmed at the cited site: `#lockerroom` is `inset: 0; z-index: 25` and only becomes click-through
when `.gone` lands, 900 ms (`LOCKER_MIN_DWELL_MS`) after the first frame, while the smoke clicked at
~400 ms. Fixed in this fork's own appended block — not by touching the inherited rule, the fade or the
dwell, and not by changing the shared harness: the curtain is declared `pointer-events: none`, which
is honest (it has no interactive children here: backdrop, sprites, rotating caption).

Evidence that a real mid-replay seek now happens, run 33057473716:

```
scrub readouts: 0%="game 2/2 · turn 1/15 TICK 15/300 · 13 V 14"
                50%="game 2/2 · turn 1/15 TICK 4/300 · 30 V 30"
                100%="game 2/2 · turn 2/15 TICK 26/300 · 0 V 5"
```

The 50 % click seeks BACKWARDS from tick 15 to tick 4 with both armies whole — a state playback cannot
reach by advancing, i.e. the seek was served. (Before: `0%` and `50%` were the same frame.) The
harness reports the readouts and does not gate them; that is shared-template behaviour I deliberately
did not change, and F9's soak is the gate that does fail on a frozen viewer.

## F15 — the smaller deltas

Fixed:

* **duplicated caps** (`3c79553`) — `src/magent_battle_player.nim` re-declared `MaxPromptRunes`,
  `MaxPolicyLabelRunes` and its own `truncateRunes`; it now imports `magent/sim_types`, so the caps
  the server enforces and the caps the registration is cut at are the same constants.
* **three unreachable `SimEventKind` values** (`8a18705`) — `runTurnIfDue` now emits `TurnStart` per
  turn, `Fallback` per fallen-back seat and `Rout` for an army that lost ≥ `RoutLostThreshold`
  soldiers since the previous turn. That threshold is a new `sim_types` constant replacing the
  literal `10` that `broadcast.nim` (feed event) and `replay_runtime.nim` (scrubber beat) each
  carried, so the three rout rules cannot disagree. Events are not part of `gameHash`, so the hash
  chain is untouched (`docker-smoke` + the replay re-derivation suites are green). New test drives one
  turn with 12 soldiers dead: `[OK] the tier-2 event stream emits every kind it declares`.
* **"present exactly once"** (`885a968`) — the nine strings that genuinely occur once are now counted
  (comments stripped), so a re-mapping that shipped both the new and the old word fails; the three
  that legitimately occur more than once are listed separately WITH the reason (`alive-label` is a
  class: markup + its rule + the `.tiny` rule; "Forming up on the line" is the static caption and the
  first rotating prep-talk line; "showing recorded orders" is the inherited static `#mmwarn` text and
  the JS that rewrites it with the tick). The note's blanket "exactly once" is wrong for those three.
* **`tune_baselines --check` missing from CI** (`51b82ee`) — added to the `test` job, at the tool's own
  horizon (`maxTicks 200`, which is what the pick was tuned at) rather than only the shorter sweep
  inside `test_magent_tuning.nim`. Evidence: `shipped pick ranks 7 of 27: ok`.
* **stray artifacts** (`1b886c0`) — `p0.log` / `p1.log` deleted and `p*.log` ignored.
* **the closed failure payload** (`5f68303`) — the shape moved to `roster.playerFailurePayload`, which
  `server.declarePlayerFailure` writes and the test now parses, so the assertion is against the bytes
  the server emits instead of a literal the test builds.

**DISPUTED — `nim.cfg` is "both committed and listed in `.gitignore`".** It is not committed:
`git ls-tree 95e94c9853de770c9afdea85d8d8144e80df9374 -- nim.cfg` prints nothing (the tree at that sha
holds `.dockerignore … vendor`, no `nim.cfg`). The file exists only in the sandbox working copy,
written by `nimby --global sync`; `ci.yml` regenerates it from the runner's package tree and
`.dockerignore` keeps it out of the image build context, so the `.gitignore` entry is correct. I
briefly committed it while acting on the finding, caught it, and the entry is restored with a comment
saying why — the finding is the only thing in this round that asked for a change the tree did not
need. (Its other half, `p0.log`/`p1.log`, was real: those two WERE tracked.)

No change, argued:

* **`client/league_replayer.html` absent** — the note lists it as forked; nothing in the tree
  references it and `?embed=1` support lives in `page_script.js:174-240`. Adding a file nothing loads
  would be worse than the note being stale.
* **`results.magentReward` is decimal strings** — `coworld_manifest_template.json:145` declares
  `{"items":{"type":"string"}}`, `docs/PROTOCOL.md` shows strings, and
  `tests/test_magent_manifest.nim` asserts the results key set equals `armyResultsJson`'s. Schema,
  docs and code agree; only the note's example shows numbers. Changing the wire to numbers would
  break the closed results schema for no gain.
* **`MaxUnits = 400` vs the note's 200** — a pool ceiling; 45×45 spawns 81 per army, so both values
  are above the largest configured board. 400 is the safer of two arbitrary numbers.
* **`orders` accepted as an object keyed by squad id** — strictly more tolerant than the note, and a
  non-array/non-object `orders` still raises `DirectiveError` (`directives.nim:176-177`), which is
  what the retry/fallback ladder needs; asserted at `test_magent_control.nim:210-215`.
* **`Dockerfile.replay-viewer` expects no `magent_replay.data`** — correct, since the asset preload
  (`--preload-file`/`FILESYSTEM=1`) was dropped; design.md:1091's file list is stale. The bundle CI
  builds and executes has exactly `{js,wasm}` and `wasm-viewer` is green.
* **"a seat that connects then never answers"** — the note's test 18 wording does not map onto this
  game: seats send **no inputs at all** (the server computes every soldier's action), so a connected
  seat has nothing to answer with. The only "never answers" mode is the LLM leg, and
  `test_magent_engine.nim:59-74` covers it end to end (`llmTurns[0] == 0`, `fallbackTurns[0] > 0`,
  `reason == complete`). I added no third test for a state the protocol cannot produce.

## F16 — the note's arithmetic table is stale — no change

`episode_timeout_minutes` 20, `wallClockBudgetSeconds` 660 (240 in the cert fixture), schema maximum
660, `clampConfig` re-clamping, and `tests/test_magent_manifest.nim:141-155` asserting
`timeoutSeconds >= 1200`, `budget <= 660` and `budget*100 <= timeoutSeconds*60`. The tree is right and
the finding is about the design note's own worked example, which the fixer must not edit. The real
worst case (~615 s) is now written down in `PATCHES.md` §10 (F6) and in the manifest description
(F17), which is where a reader will look.

## F17 — "55 percent" — `900d9d0`

The description now gives both numbers and the bridge between them: 660 is 55 % of the assumed 1200 s
timeout, and it leaves the worst-case episode (~615 s, plus at most 17 s to serve a stop landing
mid-turn) inside the 60 % / 720 s settle target. Values unchanged; the `manifest` job is green.

## F18 — `game.docs` `"type":"uri"` vs the checklist's `"type":"text"` — `dd7a833` (conformed)

The structure was already item 10's; the discriminator was not. **The note and the checklist conflict
here** — design.md:1116-1118 specifies `uri` explicitly, and CI's `manifest` job proved the platform
validator accepts it — and I resolved it in the **checklist's** favour, because that is what the
verdict is gated on and because conforming costs nothing behavioural.

`README.md`, `docs/RULES.md` and `docs/PORTING-MAGENT.md` are now embedded verbatim as
`{"type":"text","value":…}`. Inlining duplicates files that also live in the tree, so the copy is
written by one committed script (`tools/embed_manifest_docs.py`, which splices only the docs block and
re-parses the manifest before writing) and `tests/test_magent_manifest.nim` asserts each inline value
equals the file it came from — the copy cannot drift. `game.protocols` still carries both `player` and
`global` as objects. Evidence: `[OK] protocols and docs are objects, not bare strings` and the
`manifest` job (coworld 0.1.43's `validate_upload_manifest` / `_load_template_manifest` /
`load_manifest`) green on the inlined manifest in run 33057473716.

## F19 — `.tiny` at 620 px vs the checklist's "under 640px" — `3c85c8d` (conformed)

`relayout()` now toggles `.tiny` at `boardW < 640`, so the 621-640 px band no longer keeps labels the
game block's own comment said were gone. The change is in the fork's own `page_script.js` (the
starter's 620 is inherited *there*, not in the shared chrome), the comment says where the threshold
lives, `tests/test_magent_viewer.nim` re-pins the literal, and the worst-case fixture now drives
**630 px** alongside 360/620/1024 — which also settles the reviewer's "could not determine" item about
whether any real width sat in that band. Evidence: fixture step `{"loaded":true,"ms":2049}` with the
four widths, and `[OK] transport, endcard and the 360 px rules`.

---

## Also settled from the review's "Could not determine"

* **"Whether `viewer_smoke --soak 10` would pass on this bundle"** — it does: F9's soak line above.
* **"Whether the 620 px `.tiny` threshold matters at any real embed width"** — moot: the threshold is
  640 now and the fixture drives 630 (F19).
* Still open by construction (needs a keyed run, phase 60): whether the LLM leg works against a live
  provider, and whether a 45×45 episode with real LLM latency settles inside 660 s. `docker_smoke.sh`
  runs with no `ANTHROPIC_API_KEY`, so every CI directive is `scripted`.

## NOTED (not fixed)

Seen while working, not a finding in this round, code left alone:

* `broadcast_core.js`'s `pushFeed`/`drainFeed` now have no caller inside the core (the dead formatter
  went with F4). They are kept deliberately — `getPaceStats().queued` reports the queue and
  `test_magent_viewer.nim:232` pins the signature against the cogball 0.1.4 latch — but a future round
  could decide whether the adapter should be pushing rows into it at all.
* `buildStateJson` still ships `"en": true` in live mode, so a scrubber click on the developer page
  sends an `s:` command the live server ignores. Harmless, dev-only, and outside F13's cited symptom.
* `chrome_common.js`'s `markBeat`/`renderBeatMarkers`/`killMarkerTeam` are unreachable in this fork
  (no `steal/return/capture` beats). They stay because the file is byte-identical to the starter's by
  rule.
