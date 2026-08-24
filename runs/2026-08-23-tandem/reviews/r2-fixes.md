# r2 fixes — tandem

Head: `ac662b2af8e3802b12dfc5c3e67d19feed3dc8c5` (origin/main)
CI: https://github.com/Metta-AI/cogame-tandem/actions/runs/32674800419 — **success**
(run id **32674800419**, `headSha ac662b2af8e3802b12dfc5c3e67d19feed3dc8c5`; jobs `test`,
`docker-smoke`, `wasm-viewer` all `success`; `wasm-viewer`'s step **"Load the bundle in a real
browser" ran and succeeded** — `{"loaded":true,"ms":2885,…}`, `soak: 12s of playback kept advancing
("1 / 948" -> "241 / 948" -> "289 / 948")`; `grep -c "SEAT-COUNT FAIL"` over the `docker-smoke` job
log: **0**, with `SMOKE_SEATS: 2`, `player container …-p0 exited 0`, `…-p1 exited 0`,
`smoke OK: seats=2 … reason=complete`.)

Base: `668b5f5d81d5025a527391bb25f90cf2bc186d1d`. Seven commits, one per finding, published through
the GitHub Data API (blobs → tree → commit per commit, then ONE fast-forward `PATCH
refs/heads/main`; direct `git push` 403s in this sandbox). `git fetch` after the PATCH confirms
`origin/main == ac662b2` and that its tree is identical to the locally tested tree. The series was
published exactly once — one CI run exists for this head.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking, static-viewer, 14d) | fixed | `59c52f6` | `client/replay_broadcast.html:2151-2167,2207-2234`, `tests/test_viewer.nim:101` |
| F2 | fixed | `01d73df` | `src/tandem/broadcast.nim:38,58,90-98`, `tests/test_replay.nim:193-243` |
| F3 | fixed | `20c4b28` | `client/league_replayer.html` (readouts), `tests/test_viewer.nim:214-249` |
| F4 | fixed | `f345cd5` | `client/replay_broadcast.html:1285-1294,2288-2320`, `tests/test_viewer.nim:193-212` |
| F5 | fixed | `f939b2f` | `tests/test_viewer.nim:124-191` (`identHead` + `noAliasIsShadowed`) |
| F6 | fixed | `19d48c5` | `client/replay_broadcast.html:1261-1275` (the game block's `.beat-marker`, now at :1269) |
| F7 (4 items) | fixed | `ac662b2` | `src/tandem/baselines.nim:411`, `src/tandem/server.nim:477`, `src/tandem/sim_types.nim:471`, `src/tandem_player.nim:120` |

7 findings, 7 fixed, 0 disputed, 0 needing design.

Local verification before publishing: **all 15 `tests/*.nim` pass in BOTH debug and `-d:release`**
(`tests/test_perf.nim` release-only, per `NIM_TESTS_RELEASE_ONLY`), Nim 2.2.4, `nim.cfg` regenerated
from this host's package tree. The viewer work was verified the way the r2 reviewer verified the
defect: the page spliced exactly as `server.nim:96-102` splices it (real `chrome_common.js`, a stub
`BroadcastCore`), loaded in the sandbox's real chromium
(`/opt/pw-browsers/chromium-1194/chrome-linux/chrome` + playwright), driven with a **real** HUD
frame from the real Nim broadcast layer (`buildStateJson` over a real scripted `porter × porter`
episode on seed 4417231, delivered at tick 1317).

---

## F1 — the game block's labelled-button `markBeat` was shadowed by the inherited alias

**Reproduced first, at `668b5f5`.** Real page + real `chrome_common.js` + the real 18-beat frame,
1280×720: `markerCount 18`, `tagNames ["DIV"]`, `withAriaLabel 0`, `withTitle 0`, `withOnclick 0`,
sample `<div class="beat-marker doorway" style="left: 3.26252%;"></div>`; a click on the 4th marker
(the doorway at tick **324**) sent **`s:322`** — the scrub bar's pointer-fraction handler, not the
marker; `beatEls` stayed empty so `applyTandemSpoilers` was a no-op. Exactly the reviewer's numbers.

**What the code did:** the game block declared `function markBeat(tick, kind, team, label)`
(`:2141`) in the same function scope as the inherited alias `var markBeat = C.markBeat` (`:1460`).
`var` and `function` share one scope: the declaration hoists, then the alias assignment overwrites
the binding at load, so all seven call sites resolved to `chrome_common.js:538`'s three-argument
`<div>` builder.

**What it does now:** the game block's builder is named **`markTandemBeat`** and its seven call
sites (`tandemIngestBeats` plus `applyEvent`'s doorway/drop/impact/delivered/wrecked/gameover arms)
call it. The name can no longer be captured, and **nothing above the banner changed** — the
reviewer offered dropping `markBeat` from the alias list as the alternative, but the repo's own
`AGENTS.md` freezes that region ("Tandem-specific behaviour goes in the appended game block … never
above it"), and checklist 14 wants the inherited chrome unmodified, so the rename is the fix that
respects both. A ten-line comment at the declaration records why the name is not `markBeat`, so it
cannot be "tidied" back.

**Evidence (same harness, at head):** `markerCount 19` (18 + the F2 delivered beat), `tagNames
["BUTTON"]`, `withAriaLabel 19`, `withTitle 19`, `withOnclick 19`, sample
`<button type="button" class="beat-marker doorway" aria-label="Doorway 1 cleared — 0:02" title="…">`;
a **real pointer click** (browser hit-testing, `elementFromPoint` confirms the button is on top)
on the tick-324 doorway sends **`s:324`** — its own tick; with spoilers off at a t=700 frame,
**11 of the beats ahead of the playhead hide through `applyTandemSpoilers`** (ticks 758, 819, 860,
969, 1086, 1186, 1193, 1283, 1290, 1315, 1318 — the reviewer's exact list), i.e. the tandem gate is
now live rather than a no-op. Zero page errors.

`tests/test_viewer.nim`'s existing needle was updated to the new name in the same commit (a rename,
not a loosening); the assertion that makes this class of bug *catchable* is F5.

**Checklist item:** 14(d).

## F2 — the `delivered` beat now fires

**What the code did:** `stepEvents` emitted `{"k":"delivered"}` only from `elif sim.phase ==
Delivered` (`broadcast.nim:102-104`). `sim.nim:570-578` sets `phase = Delivered` in step 7 and
`sim.nim:646-648` finishes the game in step 10 of the **same tick**, and both callers derive events
after the whole tick, so the arm was unreachable: `.beat-marker.delivered`, `case 'delivered'`'s
`banner('DELIVERED','good')` and `beatLabel`'s entry were dead.

**What it does now:** `BroadcastTracker` carries `delivered: bool`, and the beat is emitted on that
transition — the same shape the `wrecked` beat already used (a delta, not a phase) — ahead of the
game-over beat of the same frame. The event's `t` is the frame tick, as every other derived event's
is, and its `ticks` field carries `sim.deliveryTick`.

**Evidence:** the real seed-4417231 `porter × porter` episode derived **18** beats (kinds doorway,
impact, gameover) before and **19** after (doorway, impact, **delivered**, gameover), and the
delivered marker renders in the browser. New test `tests/test_replay.nim` "a delivery emits its
`delivered` beat" fails on the pre-fix `broadcast.nim` with *"a delivered episode emitted 0
`delivered` events"* and passes at head (CI log, both modes: `ok  a delivery emits its 'delivered'
beat`).

**Determinism:** broadcast events are derived state and are not mixed into `gameHash` (verified in
`sim_state.gameHash`; the reviewer's F7 note about `damageAtTurnStart` says the same about hashed
fields). `tests/test_determinism.nim` "the committed golden hash chain still holds" passes
unchanged — **no golden hash was regenerated, because none moved**.

**Checklist item:** 14(d) (the emitted-kind ↔ CSS-rule pairing, now complete in both directions).

## F3 — the league shell reads tandem's stream

**Which holds, checked first as the brief asked:** the file is **live** — `server.nim:90`
`LeagueReplayerPath = "/client/league"`, served at `server.nim:276-282` from
`EmbeddedLeagueReplayerHtml` (`:103`). It is **not** in `coworld_manifest_template.json`. It **is**
in the static bundle: `Dockerfile.replay-viewer` splices it to `replay-viewer/dist/league.html`
(visible in this run's build log, and the build asserts `test -f replay-viewer/dist/league.html`).
**Correction to my own commit message for this fix**, which says "not in the static bundle": that
half is wrong — the bundle does ship it as `league.html`. The conclusion is unchanged and stronger:
both delivery paths serve this page, so aligning it was the right call, not removing it.

**What the code did:** the page was the starter's CTF shell with ten rename-only lines. It drove
`kill`/`steal`/`return`/`capture` beats and rendered flag icons, lives pips, perk badges and a
K/D/Lives table out of `s.teams[side].lives`, `.flag`, `p.k`, `p.d`, `p.lives`, `p.carry` — keys
tandem never ships.

**What it does now** (the shell itself is kept — wall homography, layout, postMessage bridge,
transport drive, standings footer, status escalation are untouched):
- plaque header: a strain gauge (fill = `teams.<side>.load`, amber ≥ 80 %) with "N felt" and the
  drop count, replacing the flag icon and the lives meter;
- roster table: **Name / Strain / Blame** with the policy kind (`llm`/`scripted`), replacing
  K / D / Lives pips and the dead-seat dimming;
- beats: `doorway`, `drop`, `impact (≥ 20)`, `delivered`, `wrecked`, `over`, one CSS rule and a
  livery tint each, plus `ingestTandemBeats` placing the precomputed `s.beats` up front the way the
  board does;
- the verdict cap/chip carry the ending (F4's vocabulary), the momentum label reads `CONDITION`,
  the spoilers button describes tandem's timeline, and `.cobalt`/`.rust` join the team-tint utility.

**Evidence:** driven in chromium with the real HUD frame, the plaques read
`242 N FELT DROPS 0 | NAME STRAIN BLAME | cobalt-policy 1 SCRIPTED 242 N 117` (and the mirrored
`228 N … rust-policy … 68`), the wall corners read `COBALT-POLICY` / `RUST-POLICY`, the scrubber
places **19 tandem beats** (`doorway`, `impact`, `delivered`, `over`), the chip reads **DELIVERED**,
and the page logs no errors (the only console errors are the harness's missing wall JPEGs and the
absent board iframe under `file://`). New test `leagueShellReadsTandemsStream` pins both directions
(ctf's identifiers gone, tandem's present, a CSS rule per beat kind).

**Checklist item:** 14 (chrome provenance — the shell stays the starter's).

## F4 — the scrubber's verdict cap carries tandem's ending

**Semantic decided:** tandem is fully cooperative, so `over.winner` stays `""` and `over.draw`
stays `false` — inventing a winner to satisfy chrome_common's chip would print "DELIVERED WINS".
The verdict that exists here is the **ending**, so the game block drives `#scrub-win` and
`#win-chip` itself with `endRule`: DELIVERED / COUCH WRECKED / OUT OF TIME / TIME BUDGET / FAULT,
one `--tc` tint per rule, rendered from the same per-frame hook. chrome_common still owns the
elements nominally but never writes them (its `verdict` stays null because `setVerdict` returns on
an empty class), so there is nothing to fight over. No spoiler gate is needed: `over` rides
game-over frames only, so the cap cannot appear ahead of the playhead, and any seek away clears it
on the next frame.

**Evidence:** on the real game-over frame the cap is `scrub-win show delivered` with
`title="DELIVERED"` and the chip reads `DELIVERED` in green; forcing `endRule=out_of_time` gives
`OUT OF TIME`, `endRule=wrecked` gives `COUCH WRECKED`; at a t=700 frame the cap is hidden again.
Screenshot of the transport band confirms the chip renders in the tbar beside the tick clock.
`broadcast.nim` is unchanged — this is a viewer fix, not a wire change.

**Checklist item:** 14 (transport rules); no checklist item required it, and the design note does
not claim tandem drives the cap, so this is an improvement rather than a compliance fix.

## F5 — the guard that can now fail on F1's class of bug

`beatsAreLabelledButtons` was (and remains) a text grep; the new `noAliasIsShadowed` checks the
**scope**. It collects every name aliased out of the shared chrome (`var x = C.x`) and every name
declared by a top-level `function`/`var` of the same IIFE, over **both**
`client/replay_broadcast.html` and `client/league_replayer.html`, and fails if a name is in both
sets — precisely the condition under which the alias assignment overwrites a local declaration at
load. It needs no browser, so it runs in the `test` job.

**Verified it fails on pre-fix code, as the brief required:** running only that proc against the
page at `db00bc7^` (the tree at `668b5f5`) aborts with

```
`name notin declared` `markBeat` is BOTH aliased from chrome_common and declared at the top level
of the same scope in client/replay_broadcast.html: the alias assignment wins at load and the local
declaration is dead code (r2-F1). Give the local one its own name.
```

and passes at head (CI, both modes: `ok  no chrome alias is shadowed by a declaration in the same
scope`). It also carries two sanity floors (≥ 20 aliases, ≥ 20 declarations found) so it cannot
pass vacuously if the parse ever stops matching the file.

**Not done, deliberately:** the reviewer's alternative — a `#scrub .beat-marker` tag-name assertion
inside `tools/ci/viewer_smoke.mjs` — would edit a file the design note requires be "copied verbatim,
no substitutions" from `templates/tools/ci/`. The scope check gets the same class of bug without
touching it.

**Checklist items:** 1 (no test loosened — nothing was removed or widened; two assertions were
added and one needle followed a rename) and 14(d).

## F6 — one effective `.beat-marker` geometry

The inherited rule (`:603-610`) and the game block's (`:1263-1267`) both set `.beat-marker`
geometry, and the cascade resolves per property, so the starter's `height: calc(10 * var(--u))` and
`transform: translateX(-1px)` still won. The game block's rule now overrides both explicitly
(`height: auto` so its `top: 0; bottom: 0` spans the track, `transform: none` because the centring
is `margin-left`). The inherited rule is untouched.

**Evidence:** measured in chromium at 1280 px on a real frame, the marker box goes from
`x=393.34 w=3.91 h=13.02` to a full-track `h=44.30` at the tick's own x (the 1 px offset is gone).
Screenshot attached in the run notes: green doorway ticks, amber impacts, full-height, on the track.

## F7 — the four drifts, re-judged

All four were still at head, all four are one-line corrections with no behaviour attached, so they
are corrected rather than noted a second time:

- `baselines.nim:411` — the mule's order `note` said "full effort" while `MuleEffort = 140` (0.55,
  deliberately: the sweep is in the constant's own docstring and in `docs/BASELINE-TUNING.md`).
  That string is **spectator-visible** — it rides the replay `order` record into the match feed —
  so a false one is worth a line. Now "straight at the goal, never yielding". The constant is
  unchanged; `tests/test_baselines.nim` still prints `porter mean 0.794 vs mule mean 0.016`.
- `server.nim:477` — "690 s engine stop" → 660 s (`wallClockBudgetSeconds`), matching the constant,
  the manifest default and the note.
- `sim_types.nim:471` — `SimServer.damageAtTurnStart` deleted: declared, never written, never read
  (the live field is `TurnEngine.damageAtTurnStart`, `decide.nim:84`), not hashed. The golden hash
  chain is unchanged, which the determinism test confirms.
- `tandem_player.nim:120` — the startup line printed the uncapped byte length of the prompt while
  the frame carries the 4000-rune clip; it now prints the clipped **rune** count and the cap.

---

## NOTED (not fixed)

- `src/tandem/sim_types.nim:470` — `SimServer.lastDamageTurn` is also declared, never written and
  never read (same class as the `damageAtTurnStart` the review named, and equally unhashed). It was
  **not** in any r2 finding, so it is left alone rather than folded into F7's commit.
- `tools/ci/viewer_smoke.mjs` still reads `#feed, .feed, #log` and so reports `feed_lines: 0` for a
  page whose feed is `#killfeed` (the reviewer settled that this is not evidence about the feed).
  The file is a verbatim template copy; changing it is a template-level decision, not a repo one.
- `client/league_replayer.html` still calls chrome_common's `ingestBeats(s)`, which for tandem only
  ever reaches `setVerdict` and returns. It is inherited, inert and harmless; removing it would be
  churn in a file this round already touched heavily.
