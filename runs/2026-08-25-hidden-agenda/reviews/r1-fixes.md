# r1 fixes — hidden-agenda

Repo: `Metta-AI/cogame-hidden-agenda`
Head: `dd84d91871ecb6f0eb94d8b6bd54b43a15fddf89` (origin/main)
CI: run **32925353796** — <https://github.com/Metta-AI/cogame-hidden-agenda/actions/runs/32925353796>
— conclusion **`success`**, `headSha` `dd84d91871ecb6f0eb94d8b6bd54b43a15fddf89`, jobs `test` ✓
`docker-smoke` ✓ `wasm-viewer` ✓. `grep 'SEAT-COUNT FAIL'` over the full job log: **0 hits**; 22
`test_*: ok` lines (eleven files × debug and `-d:release`).

Fourteen commits, one per finding (plus one fix-forward on B2, labelled as such). Every change was
built and run locally against the real toolchain (Nim 2.2.4 via `nimby use 2.2.4` +
`nimby --global sync nimby.lock`, all eleven test files debug and `-d:release`) and, for the page,
driven end to end in headless chromium against real packets from a real replay.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `eea1c85` | `src/hidden_agenda/server.nim:12-20,34,287-289,412`, `docs/PROTOCOL.md:47`, `coworld_manifest_template.json`, `tests/test_manifest.nim:93` |
| B2 | fixed | `44d190c` + `dd84d91` (fix-forward) | `tools/build_page.py`, `tools/_page_script.js`, `tools/_page_css.css`, `client/replay_broadcast.html`, `tests/test_broadcast.nim`, `README.md` |
| B3 | fixed | `8ac004c` | `tests/test_vision.nim:94-131`, `tests/test_replay.nim:190-317` |
| N1 | **DISPUTED** (fix refuted by measurement; the constant is now documented) | `39a1c10` | `src/hidden_agenda/sim_config.nim:66-76` |
| N6 | fixed | `a9b7152` | `src/hidden_agenda/scripted.nim:95-114`, `tests/test_meeting.nim:214-251` |
| N14 | fixed | `7beb614` | `src/hidden_agenda/llm.nim:35-60,704-709`, `tests/test_llm.nim:263-419` |
| N15 | fixed | `29cffb4` | `src/hidden_agenda/sim_types.nim:50-66`, `sim_state.nim:141-149`, `sim_config.nim:172-179`, `tests/test_replay.nim:154-192` |
| N16 | fixed | `9ff9782` | `src/hidden_agenda/server.nim:128-155`, `docs/PROTOCOL.md:21`, `tests/test_noleak.nim` |
| N17 | fixed | `0c7fa26` | `src/hidden_agenda/llm.nim:265-283`, `docs/POLICIES.md:81`, `tests/test_llm.nim:232-262` |
| N18 | fixed | `aebe9bd` | `src/hidden_agenda/global.nim:245-300`, `tests/test_broadcast.nim:120-167` |
| N22 | fixed (seed 11 half **DISPUTED**) | `4e86228` | `tools/build_manifest.py:305-317`, `coworld_manifest_template.json`, `tests/test_manifest.nim:241` |
| N23 | fixed | `29cfdf4` | `docs/RULES.md:9-13,93,132,153-158,226-232`, `docs/POLICIES.md:59`, `README.md:22`, `coworld_manifest_template.json`, `tests/test_manifest.nim:257-303` |
| N32 | fixed | `3f1d35a` | `.github/workflows/ci.yml:314-318,347-362` |
| N2 N3 N4 N5 N7 N8 N9 N10 N11 N12 N13 N19 N20 N21 N24 N25 N26 N27 N28 N29 N30 N31 | not fixed — see **NOTED** below | — | — |

---

## B1 — the game container still serves a `/client/replay` page route

**Commit `eea1c85`.** Satisfies **checklist item 3 (static viewer)**.

What the code did: `server.nim:34` `staticRead`'d the broadcast page into the binary, `:287-289`
served it from `replayPageHandler`, `:412` routed `GET /client/replay` at it, `docs/PROTOCOL.md:47`
advertised it in the route table, and `tools/build_manifest.py` inlined that table into both
`game.protocols` values, so the path was on the platform-facing page as well as in the pod.

What it does now: the route, the handler and the `staticRead` are gone; the module header says why
(the static bundle is the only replay surface, and a pod replay page keeps a game container alive to
watch a finished episode); `docs/PROTOCOL.md` replaces the row with a positive statement that no
route serves a replay page and that the bundle contacts nothing but S3; the manifest is regenerated
from the edited doc.

I did **not** take the "the starter carries the same route, so item 3 must mean the manifest" reading
the reviewer offered as counter-evidence. Item 3's last sentence is unconditional and a judge has to
be able to verify "no `/client/replay` pod path anywhere" **from the tree**, so the tree now makes
that trivially checkable — and asserts it:

```nim
# tests/test_manifest.nim, block replayViewerIsAStaticBundle
for dir in ["src", "docs", "client"]: ... if "/client/replay" in readFile(path): offenders.add ...
for path in ["README.md", "coworld_manifest_template.json"]: ...
check(offenders.len == 0, "no /client/replay pod path anywhere, found it in: " & ...)
```

Evidence: the test fails on the pre-fix tree (`FAIL: no /client/replay pod path anywhere, found it
in: src/hidden_agenda/server.nim, docs/PROTOCOL.md, coworld_manifest_template.json`) and passes on
this one; `test_manifest: ok` in both modes locally and in CI.

## B2 — the page inherited the starter's CSS but not its markup or its script

**Commits `44d190c` and `dd84d91` (fix-forward).** Satisfies **checklist item 14 (chrome is the
starter's, not a lookalike)**, and keeps item 11.

What the code did: `tools/build_page.py:12` sliced `src[0:704] + src[833:1451]` — the starter's CSS
**head only**. The 143-line body was a hand port (`tools/_page_markup.html`) and the ~3,050-line page
script was re-authored as 30 functions (`tools/_page_script.js`) against the starter's 187. Product:
2,180 lines against the starter's 4,660 — 47 %, which is the size test item 14 names.

What it does now: `build_page.py` slices all three halves out of the starter and asserts every cut,
line by line, so a starter bump fails loudly instead of cutting the wrong block:

* **CSS** — unchanged from before (verbatim minus the removed blocks; the reviewer verified this
  half was already byte-identical).
* **Markup** — the starter's body `1462..1604`, with `#viewpanel`, `#mmwarn`, `#povBadge` and `#fpv`
  cut, the airlock caption and the two re-lettered literals applied, and this game's
  `#rosterstrip` / `#voteboard` / `#ec-roles` appended. `tools/_page_markup.html` is deleted; there
  is nothing left to hand-port.
* **Script** — the starter's page script `1605..4342` minus the first-person raycaster and the
  eye-level cog art it billboards, the `fpmap` wall silhouette, `renderPov`, `renderMismatch`, the
  zoom/pan/minimap cluster with its keys, and the `?viewpanel=0` opt-out; plus three hook lines
  (`AgendaChrome.install` / `.frame` / `.event` against an `HA_CTX` built beside the starter's own
  `PB_CTX`), the bundle's global name (`HiddenAgendaStaticReplay`) and the `.plate-name` class item
  11 needs on the classic plate.

So these are now the starter's own code rather than re-implementations under its names: the
locker-room curtain and its dwell floor, the two tempo levers (`animFactor`, `dwellFloor`), the beat
pulse, the League-Replayer embed bridge and its `postMessage` transport relay, the `?t=` and
`?achievement=` deep links, `syncBoardAspect`, the flag icon, `renderSquad` / `ensureScorebug` /
`renderScorebug` / `updateFlag` / `shortName`, the kill-feed and banner-lane queues, the whole
endcard (`endcardWinCondition`, `endcardOrder`, `endcardBadge`, `renderEndcardRows`,
`ensureEndcardTeams`, `renderEndcard`), the transport wiring with `seekToFraction` and its queued
first click, the keyboard map and `relayout()`.

`tools/_page_script.js` is rewritten as the **appended block**. It re-implements none of the above
and reaches the inherited chrome through the context, exactly as the starter's PAINTBALL block does:
`CTX.pushFeed(row)` (one argument, the row element — the starter's signature), `CTX.banner`,
`CTX.esc`, `CTX.send`, `CTX.C.markBeat` / `setVerdict` / `getSpoilers` / `setName`. Its beat builder
is still `buildAgendaBeats`, never `markBeat`, and its helpers are `byId` / `htmlEsc` rather than
`$` / `esc` so no name in it collides with the inherited alias list.

Result: **3,171 lines** against the starter's 4,660 (68 %), with ~1,500 lines legitimately removed
(the raycaster alone is ~1,100).

New guard, `tests/test_broadcast.nim:theScriptIsTheStartersToo`: pins the size against the starter's
4,660, asserts **29 inherited script functions** by name, the starter's own missing-splice guard, the
`PB_CTX` context, the absence of all eleven removed identifiers (`renderFpv`, `syncViewUi`,
`ZOOM_STEP`, `panCellBoardPx`, `COG_ART`, `CtfStaticReplay`, …) and that `window.AgendaChrome = {`
appears **after** the banner comment — i.e. the block is appended, never spliced in.

Evidence, beyond the test: I built the dist-shaped page locally (wire constants from
`tools/gen_wire_constants.nim`, `chrome_common.js`, `broadcast_core.js`, a `HiddenAgendaStaticReplay`
stub standing in for the worker adapter) and drove it in headless chromium with **real packets**
produced by `global.buildReplayPacket` from a real 607-tick episode — the first frame, both freezes,
all four meetings, the endcard, then every transport button, every keyboard shortcut, a scrub click,
a beat-marker click and a 360 px resize. **Zero page errors.** Rendered: both plates with numerals
and sublines, `TICK 607 / 900` + `FINAL`, the five-chip roster strip, the vote board with
`RESOLVES IN 11` counting down, the feed (`PINK EJECTED 2-1 — THE IMPOSTOR`), the banner lane, **11
clickable `button.beat-marker`s and 0 leftover divs**, the endcard with a five-row role-reveal table
and `#ec-teams` emptied, the six speed chips, the `RACE TO WIN` momentum paths, and `--band` /
`--topband` / `--hudscale` set on `:root`.

Two things the fix-forward commit `dd84d91` corrects, both mine:

1. Inheriting `renderScorebug` wholesale left the plate **headline** as the starter's `teamName()`,
   which is the policies seated on the team. The design note specifies `CREW` and `IMPOSTOR`
   (design.md:1149-1155), and the docker-smoke run printed the symptom — `PINK CREW LEFT 3
   PINK · PINK`. The appended block now writes both headlines over the inherited render. Both name
   spaces are still on screen: the roster strip, the impostor subline and the endcard's role table
   all carry the policy names (checklist item 4).
2. Three CSS lines in the game block so the roster strip clips a long **policy** name instead of
   running off the stage (`#rosterstrip { overflow: hidden }`, `.rchip { min-width: 0 }`,
   `.rchip .rpol { overflow: hidden; text-overflow: ellipsis }`). The alias never shrinks. This was
   pre-existing, not caused by the rewrite, but it is in the block this commit owns and it is two
   lines; it is called out here rather than buried.

## B3 — nothing asserted the per-tick re-derivation

**Commit `8ac004c`.** Satisfies **checklist item 2 (replay re-derivation, "a test asserts it")**.

What the code did: `tests/test_vision.nim:97-113` played a full episode and then indexed
`sim.frames[^1]` — one frame — under a docstring promising "every cog on every tick". Nothing
re-derived `d`, `g` or `ph` at all.

What it does now, two tests:

* `tests/test_vision.nim:recordedMaskMatches` rebuilds the whole roster **from each frame's own `c`
  array** (cell, facing, state code) and recomputes every slot's mask through the production
  `seesCog`, on **every** frame, and asserts the comparison count is exactly `frames.len * Seats`
  so the loop cannot silently shrink again.
* `tests/test_replay.nim:eventsReDeriveEveryFrame` works from the replay **bytes** — what a viewer
  actually holds. It folds the recorded event rows forward one tick at a time and checks each
  recorded frame: `d` against the `deposit` rows (and each row's own running `total`), per-seam `g`
  against the `mine` and `seam` rows starting from `seamCapacity`, `ph` against the `meeting` rows
  played through the four meeting tick offsets, and `v` against the frame's own cells. It then walks
  **every** tick through `global.replayFrame` and asserts the viewer's packet is that same frame,
  field for field — the "the viewer derives its display from that same re-derivation, not from a
  parallel recording" half of the item.

Evidence that it bites: perturbing `recordFrame` to write `d + 1` at one tick produces
`FAIL: tick 250: recorded deposits 3 != the count re-derived from the deposit rows 2`. Both files
pass debug and release, locally and in CI.

## N1 — `awarenessRadius = 4` where the ladder authorises 3 — **DISPUTED as a code change**

**Commit `39a1c10`** documents the constant; it does **not** change it, because 3 does not work.

I made the change the finding implies (`sim_config.nim:67` → 3, `tools/build_manifest.py` default
and all three variants → 3) and ran the oracle. Measured:

```
awarenessRadius = 3:  FAIL c: mean witnessed freezes 1.81, impostor win rate 0.38   (ceiling 0.35)
                      FAIL e: 7/29 witnessed freezes convicted (0.24)                (floor 0.60)
awarenessRadius = 4:  PASS c: mean witnessed freezes 1.62, impostor win rate 0.00
                      PASS e: 16/26 witnessed freezes convicted (0.62)
```

The design note's own rule is "**That test is the enforcement, not this table**" (design.md:541-542),
and step (e) is the ladder rung that points in this direction; the code walked it one further rather
than reaching for a pinned constant. Reverting to 4 and shipping the measurement in a comment at the
constant is the honest resolution. The finding is right that the value was undocumented; it is wrong
that 3 is available.

## N6 — the impostor's bandwagon vote could never fire

**Commit `a9b7152`.** `openMeeting` appends the **current** meeting's `MeetingRecord` with five empty
votes and `runDecisionPoint` runs immediately after, so `lastMeetingCounts`, reading
`sim.meetings[^1]`, always saw an empty table: `rankedByVotes` always returned `@[]`, the impostor
always fell through to the stale-cog fallback, and `switchTo` was pinned at `"skip"` for whole
episodes. It now walks back to the newest record carrying an `outcome` — the previous, resolved
meeting — which works inside a meeting and outside one without coupling to `inMeeting`.

New `tests/test_meeting.nim:theImpostorBandwagonsOnThePreviousMeeting` resolves one meeting with a
known tally, opens a second, and asserts the impostor votes a leader of the first and switches to the
runner-up. On the old code it fails with `got 'skip'`. The seven feasibility gates still pass
(`test_feasibility: ok`), and `test_baseline` still audits 192 episodes clean.

## N14 — nothing drove `decideAll`'s transport or retry path

**Commit `7beb614`.** Satisfies **checklist item 8's** "retries once … then falls back — and the
fallback is recorded" by testing it rather than only implementing it.

Every driver block constructed `disabledLlmClient()`, which short-circuits before the batch loop, so
`dsRetry` was produced nowhere and the transport ladder was unasserted. `LlmClient` gains a
`BatchSender` seam — `nil` in production, where the batch still goes to `client.curl.makeRequests` —
and a `stubbedLlmClient` constructor. Five new cases: a transport error retried once **inside the
same decision point**, recorded `dsRetry`, with the retry hint present in the second batch's body; a
429 retried once then recorded `dsFallback`; a 403 disabling the client so every later seat is
scripted with **no further batch**; junk that is not JSON retried once then falling back; and a retry
batch that carries **only** the seats that failed (`batchSizes == @[5, 4]`). `decideAll` never
raises in any of them.

## N15 — `MaxPolicyLen` was declared and used nowhere

**Commit `29cffb4`.** Policy names arrive from `config.players[].name` and reach `policyNames[]`,
`results.names[]`, every `reveal` row's `policy` field and the viewer's roster chips;
`config.variant` and `config.model` are pinned verbatim into the replay's config document. None went
through `cleanText`, so the note's "the same rune-safe truncation applies to **every** string that
reaches the replay" was false for them. `cleanText` / `oneLine` move to `sim_types.nim` (the base
module, re-exported from `sim_state`) so `sim_config`, which owns `variant` and `model`, can reach
them without an import cycle; both sites now cap at `MaxPolicyLen` on rune boundaries.
`tests/test_replay.nim:policyNamesAndVariantAreCapped` pushes 270 multi-byte runes through all four
and reads the bytes back (`FAIL: a policy name is capped at MaxPolicyLen in RUNES, got 274` on the
old code).

## N16 — the `final` frame carried no `slot`

**Commit `9ff9782`.** `broadcastFinal` built one payload and sent it to every socket. It is now built
per socket with that socket's slot, matching design.md:1001 and the `welcome` / `state` frames. Still
no `roles[]`, no `impostorSlot`, no `seed` — `tests/test_noleak.nim:noRolesInWelcomeOrFinal` asserts
both halves.

## N17 — a frozen or ejected seat's frame carried no `canAct` / `canVote`

**Commit `0c7fa26`.** `docs/POLICIES.md:81` and the manifest's policies page both promise
`canAct: false`; `seatView` emitted no such key, so the promise was false on the wire.
Both flags are now in the frame (`canAct` = this seat is active, `canVote` = that and a meeting is
open) and `tests/test_llm.nim:frozenAndEjectedSeatsAreToldTheyCannotAct` asserts all four
combinations and that the flags agree with `activeSeats()`.

## N18 — the viewer drew `cool = 0` and `RESOLVED` for the whole replay

**Commit `aebe9bd`.** `replayChrome` hard-coded `freezeCooldown = 0` and `meetingIn = 0`, so on the
**static bundle path — the one the platform serves** — the impostor plate's pip bar read fully
charged the instant after a freeze and the vote board read `RESOLVED` for the whole meeting. Both are
exact functions of the recorded rows plus the recorded config, so the walk over `eventsByTick` that
already rebuilds the vote board now also tracks the last `freeze` tick and the `meeting` open tick.
`tests/test_broadcast.nim:bothCountdownsAreDerivedFromTheBytes` asserts 0 before the first freeze,
`freezeCooldownTicks` on the freeze tick, one-per-tick decay, and a countdown that opens at
`resolveTick` and reaches 0 exactly on the resolve tick.

## N22 — the certification fixture barely outlasted the soak

**Commit `4e86228`.** The fixture produced a 343-tick episode = 14.3 s of playback against a 10 s
soak: a 4.3 s margin, and a replay barely longer than the soak reports a finished playback as a
frozen one. The lurker's second freeze is what ends the episode and it is gated by
`freezeCooldownTicks`, so the **fixture** pins 500 (inside the schema's 30..600). The episode is now
**608 ticks = 25.3 s**, still `complete` / `impostor_ejected`, still 2 freezes both witnessed, now 4
meetings and 15 votes. `tests/test_manifest.nim`'s floor moves 12 s → 20 s so the margin cannot
erode. CI confirms: `soak: 10s of playback kept advancing ("1 / 607" -> "193 / 607" -> "241 / 607")`.

**The seed half is DISPUTED.** The note's `seed: 11` is not adopted: with the impostor pinned to slot
4 the spawn rotation is the only seed-driven variation and it has period 5, so seed 11 plays a
**29-tick** episode with one freeze and one meeting. I swept seeds 1..60 and 1..15 × five cooldowns;
seed 5 at cooldown 500 is the best fixture available on every count.

## N23 — six places where the shipped docs contradicted the shipped code

**Commit `29cfdf4`.** All six are on the platform-facing page, because `tools/build_manifest.py`
inlines `README.md`, `docs/RULES.md`, `docs/POLICIES.md` and `docs/PROTOCOL.md` into `game.docs` /
`game.protocols`. Fixed: the spawn table ((11,7)(15,7)(11,11)(15,11) → the real
(9,7)(17,7)(9,11)(17,11), with the reason); `awarenessRadius` 2 → 4 in all three docs;
`freezeCooldownTicks` 220 → 260; meeting seats "in slot order" → by `(row, col)` of where each cog
stood, and why; move resolution "one slot-ordered pass" → the multi-pass sweep with the `(row, col)`
tie-break and cell swaps. The sixth, `canAct: false`, was fixed in the **code** instead (N17) —
the docs were right and the wire was wrong.

To stop the next drift, `tests/test_manifest.nim:docsQuoteTheRealConstants` parses every
`<constant> = <number>` out of all four shipped docs and checks it against `defaultGameConfig()`, and
checks the spawn table against `SpawnCells`. Evidence it bites: reverting one doc line gives
`FAIL: docs/RULES.md says awarenessRadius = 2; the game runs 4`.

## N32 — the renderer fixture's evidence was never uploaded

**Commit `3f1d35a`.** The fixture step writes to `dist/fixture` (`--out`); the upload step collected
only the repo root, where only the first smoke step writes. So the **only** measurement in the
`wasm-viewer` job that covers any drawn text (`canvas text: 144 drawn, 0 never inside …`) survived in
the job log and nowhere else. Both paths are collected now. The same step's comment claimed the cert
fixture is "900 ticks = 37.5 s"; it is corrected to the real 608 ticks = 25.3 s.

---

## NOTED (not fixed)

Each of these is a real observation I read and chose to leave. None falsifies a checklist item.

* **N2 spawn cells widened, N3 multi-pass move resolution, N4 meeting seats by `(row, col)`,
  N7 seeded seam phase, N8/N9 gate populations** — declared deviations that match the code. Their
  only defect was that the *docs* did not say so; that is fixed in N23. The constants themselves are
  load-bearing (`station.nim:69-75` records the tick-one-freeze failure the spawn widening repairs).
* **N5 `mostStaleActive` tie-break is rotation-based, N10 `lurk` completes on any sighting, N11
  `watch` refuses a chokepoint, N26 the second plan step re-runs the same seam chooser** — four
  baseline-behaviour deltas. Each one retunes every feasibility gate: N5 and N26 change which seam
  and which suspect four crew converge on, and gate (f)'s whole point is that the crew-win rate must
  not depend on which slot drew the impostor. The note itself says the oracle is the enforcement.
  Changing them to match prose, with no gate asking for the change, is churn with a real chance of
  turning the suite red. N26's "next-best" also has no defined reference point once the cog has
  walked to the grate.
* **N12 `parseReply` rejects a `who` naming the seat itself** — the code is stricter than the note's
  table. `tests/test_baseline.nim:52-54` asserts the same rule for the baselines, so relaxing it
  would mean loosening a test to satisfy prose. Left strict.
* **N13 a 429 is retried in the same decision point** — the note says both things
  (design.md:837-839 and :845-846) and the code implements the first; the 401/403 half
  (`client.disabled = true`, every later seat scripted) matches :845 exactly. This is a note-internal
  contradiction, and N14's new tests now pin the behaviour that exists.
* **N19 the frame key is `ph`, not `m`** — the note is internally inconsistent (its own example frame
  prints `"d":0,"m":0,"ph":0`); the code emits `ph`, `docs/PROTOCOL.md:71` documents `b.ph`, and no
  consumer reads `m`. Refuted as a code fault.
* **N20 `results.ticks` is the frame count** — `tests/test_replay.nim:47-50` pins
  `frames.len == results.ticks`, `finalFrame` uses the same number, and the replay's `end.t` is the
  last tick. Renaming it is a naming question with a live consumer contract behind it.
* **N21 the LLM error text and `PLAYER_PROMPT` never reach the replay** — the reviewer's own
  conclusion: neither string is in the note's `order` field list, so nothing in the event vocabulary
  could carry them; both caps are applied rune-safely where the strings exist. Note-vs-note.
* **N24 `test_manifest.nim` does not run coworld's `_load_template_manifest`** — the `coworld`
  package is not installed on a CI runner and this sandbox has no way to install it, so a test
  calling it would be red for everyone. **Deferred: needs the coworld CLI in `ci.yml`**, which is a
  workflow-dependency decision, not a fix.
* **N25 six design sub-claims are implemented but not isolated by a test** — real gaps (the mining
  reset on meeting open, the freeze refused during a meeting, the vacuous `seenBy` assertion, the
  start-of-tick witness snapshot, cross-process determinism, the `switchTick − 1` snapshot). Each is
  covered indirectly by `test_baseline`'s 192-episode audit or by an adjacent assertion, and none is
  a checklist item. Worth a round-2 pass; not this round's scope.
* **N27 the bundle smoke reports `canvas_text: 0 drawn`** — structural (the bundle renders on an
  OffscreenCanvas in a Worker) and exactly the case item 15 anticipates; the mitigation it names is
  present, green, and now has its evidence uploaded (N32). CI at this head prints
  `canvas text: 144 drawn, 0 never inside the canvas` for the fixture.
* **N28 the fixture's LLM-text half uses its own markup and CSS** — real, and the right fix is to
  drive the shipped `feedRow` / `banner` / `renderVoteBoard` builders inside the fixture against the
  shipped stylesheet at 360 px and gate the `overflowing` count it already computes. The B2 rewrite
  makes that straightforward (the block exposes `window.HiddenAgendaChrome`), but it is a new CI
  surface rather than a fix to a finding, and every literal clause of item 15's fixture requirement
  already holds. **Deferred to round 2.**
* **N29 `#stage.tiny` switches at 620 px, the note says 640** — a 20 px band. Item 11's two hard
  requirements (`.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and labels hidden under the tiny
  threshold) both hold, and the note states both numbers itself.
* **N30 the player container ships a `DefaultPrompt`** — not in the note, harmless in CI (both
  fillers set `PLAYER_SCRIPTED`) and offline (no credentials → scripted). Changing it changes what an
  env-less seat *is*, which is a design decision, not a repair. **NEEDS-DESIGN if it matters.**
* **N31 the deposit feed row fires every 4, the deposit beat every 8** — cosmetic; the note pins
  neither period.

## Verification summary

* All eleven `tests/*.nim` run locally twice each (debug and `-d:release`) against Nim 2.2.4 and the
  locked package tree: `ALLDONE fail=0`.
* Feasibility oracle at the shipped constants: `PASS a` on all three variants, `PASS b 0.50`,
  `PASS c 1.62 / 0.00`, `PASS d 1.00`, `PASS e 16/26 (0.62)`, `PASS f/uniform 0.05`,
  `PASS f/slots 0.06`, `PASS g worst 11-12 batches`.
* Page driven in headless chromium against real replay packets: zero page errors, every surface
  rendering, at 1280 px and at 360 px.
* CI on `main` at `3f1d35a7` (thirteen of the fourteen commits):
  <https://github.com/Metta-AI/cogame-hidden-agenda/actions/runs/32924876005> — `success`;
  `grep SEAT-COUNT FAIL` over the full log: **0 hits**; `{"loaded":true,"ms":357,...}`;
  `soak: 10s of playback kept advancing`; `smoke OK: seats=5 results=429B replay=93247B
  reason=complete`.

**FINAL CI:** run **32925353796** on `main` at `dd84d91871ecb6f0eb94d8b6bd54b43a15fddf89` —
conclusion **`success`**.

```
smoke OK: seats=5 results=429B replay=93247B reason=complete
{"loaded":true,"ms":317,"clock":"TICK 242 / 900 MEETING 2 — VOTING",
 "scorebug":"CREW DEPOSITS 4 4 / 12 TICK 242 / 900 MEETING 2 — VOTING IMPOSTOR CREW LEFT 3 PINK · PINK"}
soak: 10s of playback kept advancing ("2 / 607" -> "194 / 607" -> "242 / 607")
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized   [bundle, worker/OffscreenCanvas]
canvas text: 144 drawn, 0 never inside the canvas (66 draws crossed an edge), 0 ellipsized [renderer fixture]
```

The `viewer-smoke` artifact of this run contains `viewer-smoke.png`, `viewer-smoke.json`,
`dist/fixture/viewer-smoke.png` and `dist/fixture/viewer-smoke.json` — the N32 fix, confirmed by
downloading it.
