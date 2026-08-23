# r1 fixes — rumor

Head: `5ac1631a1f1fdd5ecb63a6fe729281cb1181e760` (main)
CI: run **32664881692** — <https://github.com/Metta-AI/cogame-rumor/actions/runs/32664881692> —
conclusion **success** (jobs: `test` 97256635579 ✓, `docker-smoke` 97256635691 ✓,
`wasm-viewer` 97256818775 ✓), on that sha, `ci.yml`, `push` to `main`.

Review: `runs/2026-08-23-rumor/reviews/r1-review.md` — no blocking findings; F1–F17 plus four
"could not determine" items. All seventeen were worked through: **seven** produced a commit
(F1, F2, F4, F8, F15, F17 + a follow-up on F2), **ten** are recorded as no-change with the
evidence, and **two** of the four could-not-determines are now settled by committed tests
(CD1, CD3).

Nothing outside the findings was touched. The design note was not edited (it lives in
coworld-builder); note/code discrepancies are recorded below instead, and the repo's own copy at
`docs/plans/2026-08-23-rumor-design.md` was left alone for the same reason.

| finding | commit | what changed / why not | checklist item |
|---|---|---|---|
| F1 scripted flag misses an LLM fallback | `b084458` | `Decision.scripted` set by `scriptedAction`; the server takes provenance from the decision | 8 |
| F2 replay test asserts count + last frame only | `eed4a10` (+ `5ac1631`) | 41 live snapshots compared frame-for-frame against `replayMatch` | 2 |
| F3 fixture `rounds: 3` vs note's `rounds: 2` | no change | `rounds: 2` is rejected by `MinRounds = 3`; the code's value is the consistent one | 6, 12 |
| F4 `viewer_smoke.mjs` ran without `--soak` | `0219ea0` | `--soak 10` added; artefact now shows `"moved": true` | 13 |
| F5 `chrome.css` + 54 appended lines | no change | that is item 14's blessed shape (starter file + banner + game block) | 14 |
| F6 §14 transport ids absent from this lineage | no change | the ids do not exist in cogame-bullwhip either; bullwhip's equivalents verified present | 14 |
| F7 `/client/replay` pod route exists | no change | starter-inherited in-container page; the manifest declares the static bundle | 3 |
| F8 captured error text byte-sliced | `708e4b7` | `errorHead` cuts with `runeSubStr` at all five sites; test on 300 CJK runes | 9 |
| F9 `readClaim` accepts `1`/`2` for a claim | no change | strict superset of the note; `"maybe"` still degrades to `"none"` | 8 |
| F10 `parseVoteReply` derives belief 75/25 | no change | the note specifies no default; the value is clamped and only display-side | 8 |
| F11 baselines measure above the note's figures | no change | inside the test bands; README already carries the measured figures; note not editable | 7 |
| F12 no distinct `TALLY —` clock readout | no change | no frame has `phase == "tally"`; the readout has nothing to attach to | 11 |
| F13 truth stamp on canvas, not `#lightpool` | no change | note/implementation detail; the stamp renders and is legible | 14 |
| F14 three `Sim` fields absent from the note | no change | the note's listing is stale; all three are load-bearing for behaviour it specifies | — |
| F15 unbounded blocking read in the player | `7a26b72` | 5 s per-read timeout + episode deadline on the loop | 5 |
| F16 `update()` does not reject `rounds > 6` | no change | matches the note; `sampleEpisode` clamps and the schema caps at 6 | — |
| F17 uncaught double-raise in the fallback path | `ef2b6de` | inner apply wrapped in its own guard; the seat is skipped, the thread lives | 5 |
| CD1 no committed tuning harness | `e763a6a` | `tests/test_sweep.nim`: an 8-cell weight grid over 300 seeds, run in CI | 7 |
| CD2 which baseline figures are intended | no change | measurement is in the CI log; the note is not mine to update | 7 |
| CD3 retry-once network path untested | `b3ca7b7` | a real batch against a closed port: retry, fallback, `scripted` recorded | 8 |
| CD4 strict reading of item 3 | no change | see F7 | 3 |

---

## F1 — the event log's `scripted` flag did not mark an LLM seat that fell back

**Before.** `Decision` (`llm.nim:43-51`) carried no provenance, so the server computed
`wasScripted = scripted[seat] != skNone or client.disabled` (`server.nim:297`) — true only for a
seat *registered* `PLAYER_SCRIPTED` or a credential-less run. A seat whose LLM reply failed twice
and took `scriptedAction` (`llm.nim:611-614`) was written into the replay with `scripted: false`.
The fallback existed only on stdout.

**After.** `scriptedAction` marks every decision it returns (`llm.nim:238-243`), and the server
reads provenance off the decision (`server.nim:295-301`), still or-ing the registered kind and the
disabled client. `evSay`/`evVote` and `seats[i].scripted` in `tableStateJson` now say scripted
whenever a baseline decided, whatever put it there.

**Evidence.** `tests/test_bot.nim` asserts `decisions[index].scripted` for the no-credentials batch
and that the flag reaches `event.scripted` and `eventToJson()["scripted"]`; a model reply parses
with `scripted == false`. CD3's test proves the same for a *failed-batch* fallback, which is the
case the finding named. Both green in run 32664881692, debug and release.

## F2 — the re-derivation test now compares every frame

**Before.** `tests/test_sim.nim:461-480` checked `frames.len == events.len + 1` and the final frame
only; an intermediate frame could have drifted.

**After.** The live episode records `tableStateJson()` after every say and every vote, keyed by the
event count at that moment (`liveFrames`), and each of the 41 snapshots — including frame 0 against
a fresh `initSim` — is compared against `replayMatch`'s frame at that index. The count assertion
`liveFrames.len == 4 * Seats + 1` keeps the test honest about how many frames it actually compared.

**Evidence.** `[OK] a recorded episode re-derives frame by frame` in run 32664881692, both passes.

**Follow-up `5ac1631`:** the first version named the list `checkpoints`, which shadows the var
`unittest`'s `check` template captures — 12 `IgnoredSymbolInjection` warnings per compile in the
CI log (visible in run 32664648938). Renamed to `liveFrames`; no assertion changed, and the head
run's test job has zero Nim warnings.

## F3 — `rounds: 3` in the certification fixture — **no change, the code is right**

The note asks for `rounds: 2` (design 831, 904) but also specifies `MinRounds = 3` and that
`update` raises on `rounds < 3` (design 522-525), which the code implements
(`types.nim:122-123`). A `rounds: 2` fixture would be rejected at config load, so the shipped
`3` is the internally consistent value; the note contradicts itself and is not mine to edit.
Item 6's seat-count invariants are unaffected — the head docker-smoke log
(job 97256635691) has zero `SEAT-COUNT FAIL` and ends `smoke OK: seats=10 results=656B
replay=7561B reason=complete`.

## F4 — the viewer smoke now soaks

**Before.** `ci.yml:306-309` ran `viewer_smoke.mjs --timeout 90` with no `--soak`, so
`viewer-smoke.json` carried `"soak": null`: the bundle was proved to LOAD, never to PLAY. The
design note (1023-1026) gives the command with `--soak 10` and says the job "passes only when
[it] keeps advancing through the 10 s soak".

**After.** `--soak 10`, with a comment saying why. This is a deliberate departure from
`coworld-builder/templates/ci.yml`, which does not pass `--soak`; every other line of all three
workflows is still the template after the three documented substitutions.

**Evidence.** The `viewer-smoke` artefact from run 32664881692:

```json
"soak": {"seconds": 10, "moved": true,
         "before": {"clock": "ROUND 1 / 3 · WAITING ON 10"},
         "middle": {"clock": "ROUND 1 / 3 · WAITING ON 3"},
         "after":  {"clock": "ROUND 1 / 3 · WAITING ON 1"},
         "status": "REPLAY", "page_errors": []}
```

`loaded: true`, `failure: null`, three distinct scrub readouts, no page errors. The replay paces
about 40 s of dwell, so a 10 s soak lands mid-episode with room either side.

## F5 — `chrome.css` = starter + 54 appended lines — **no change**

Checklist item 14 asks for "the starter's page with a game block appended under a banner comment
(`<SLUG> additions to the inherited <starter> chrome`)". That is exactly the shape: lines 1–467
byte-identical to `/workspace/starters/cogame-bullwhip/client/chrome.css`, one append hunk under
the banner. The design note's "copied **unchanged**" is the stale text; changing the CSS to match
it would delete the five extra seat colours, the 5-column scorebug and `.beat-marker.vote` and
leave emitted marker kinds with no rule — an item-14 violation.

## F6 — §14's transport identifiers — **no change**

`relayout`, `--band`, `--hudscale`, `#endcard`, `markBeat`, `#viewpanel`, `zoomAt`, `setZoom`,
`attachMinimap` return zero hits in **both** the starter and this repo; there is no
`chrome_common.js` or `replay_broadcast.html` in the cogame-bullwhip lineage. Inventing them would
be writing a lookalike, which is what item 14 exists to catch. Bullwhip's equivalents are in place
and were re-verified: `#endscreen` toggled by `updateEndscreen`, taken down by every seek through
`setIndex(next, true)`; beat markers as scrub children whose container seeks on `pointerdown`,
with a CSS rule for every emitted kind; no zoom bar or minimap to remove, since the graph stage
fits the frame.

## F7 — `/client/replay` — **no change**

Item 3's substantive requirements hold and the reviewer traced each: the manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json:16-18`),
`tools/build_replay_viewer.sh` is committed `100755` and invoked by path, and the static shell
fetches nothing but the `?replay=` URL. The route at `server.nim:477` is an in-container page in
the **game** image; nothing declares it to the platform, and `coworld-release.yml:196-201` gates
the release on the static-bundle liveness marker precisely so a pod viewer cannot ship. It is
inherited verbatim from the starter (`cogame-bullwhip/src/bullwhip/server.nim:470`), whose own
manifest also declares a static bundle, and the design note lists it among the routes (690) while
separately forbidding a `/client/replay` pod *viewer* (776) — both of which the tree satisfies.
Removing it would put the tree at odds with its own note to satisfy a literal reading of a clause
whose purpose is already met, and would silently break the in-container replay mode
(`rumor.nim:30`). Same disposition as cogame-contagion r1/N1, which the judge accepted.

## F8 — captured error text is cut on rune boundaries

**Before.** `head[0 ..< 160]`, `body[0 .. min(high, 400)]`, `… 300]`, `result[0 .. min(high, 160)]`
— byte slices that can cut a multi-byte character in half. None reaches the replay, but all are
echoed to a hosted log, which item 9 names ("captured errors").

**After.** `errorHead(text, limit)` (`llm.nim:386-392`) strips and cuts with `runeSubStr`; used at
all five sites.

**Evidence.** New case `captured error text is cut on rune boundaries`: 300 CJK runes through
`extractJsonObject` produce a `RumorError` whose message `validateUtf8() == -1`, and
`errorHead(prose, 160).runeLen == 163`. Green in both passes of run 32664881692. (The byte slice
would have cut 160 bytes = 53⅓ characters.)

## F9 — `readClaim` accepts `"1"`/`"2"` for a talk claim — **no change**

The code is a strict superset of the note's spelling list: more tolerant, never less, and item 8
asks for tolerant parsing. `"maybe"` still degrades to `"none"` (`llm.nim:497`,
`tests/test_bot.nim:160-161`), so the one invalid-talk-reply definition is unchanged.

## F10 — `parseVoteReply` derives a missing belief as 75/25 — **no change**

Design 403 specifies no default for the ballot `belief`, so there is nothing to diverge from. The
value is clamped to 0..100 and is display-only (the belief meter and `beliefSeries`); it enters no
scoring path. A "correct" alternative would be a design choice, not a fix.

## F11 — measured 0.699/0.657 vs the note's 0.682/0.621 — **no change**

Both sets sit inside the test bands (`0.60..0.78`, `0.55..0.70`), the qualitative claims hold
(herd < gossip, herd below the clue-only floor), and `README.md:46-48` already carries the
measured figures. The note is in coworld-builder and I do not edit it — recorded here as a
discrepancy for the record. Head run values, echoed by the test job (97256635579):
`all-gossip 0.698892857142857`, `all-herd 0.6571428571428574`, `clue accuracy 0.6756`.

## F12 — no separate `TALLY — 6 BROKEN · 4 SOUND` readout — **no change (would need a design change)**

`matchHeader` renders from `tableStateJson`, and **no frame has `phase == "tally"`**: the tenth
vote runs `resolveBallot` (→ `phTally`) and then `settle` (→ `phDone`) inside the same
`applyVote`, so the frame emitted after the tally event is already `done`. A distinct tally
readout would need either a new phase-carrying frame or the renderer to switch on event kind
instead of state — a design change, not a fix at the cited site. The vote split the note wants in
that string is already in the truth readout:
`TRUTH — BARRED · HONEST 6/8 · 3 OPEN · 7 BARRED` (head viewer-smoke artefact, 100 % scrub).

## F13 — the truth stamp is canvas, not `#lightpool` — **no change**

An implementation detail of how the same thing is drawn; the reveal renders (the 100 % scrub
readout above and the smoke screenshot show it) and no checklist item names `#lightpool`. Changing
the reveal to drive the spotlight would be a viewer rewrite with nothing to gain.

## F14 — `ballotBelief`, `scriptedSeat`, `deadlineStop` absent from the note's type listing — **no change**

All three implement behaviour the note *does* specify (the tally belief point, `seats[i].scripted`
in the documented `tableStateJson`, and the `"deadline"` reason). The listing at design 540-566 is
stale; the code is not. Recorded, not changed.

## F15 — the player's receive loop is bounded

**Before.** `while true: socket.receiveMessage()` (`rumor_player.nim:63-64`) — an unbounded
blocking read, ended only by a `final` frame, a close, or an exception. In practice the game always
sends `final`, but item 5 says "no unbounded loop or blocking read" without an in-practice clause.

**After.** Every read carries a 5 s socket timeout — whisky returns `none(Message)` on
`TimeoutError`, so a quiet interval is a tick, not an exit — and the loop as a whole ends at
`epochTime() + budget + 300 s`, where `budget` is `COWORLD_TIMEOUT_SECONDS` when the platform sets
it, else the configured 1200 s. The margin is deliberate: the bound must never fire before the
game's own play deadline (720 s) plus artifact writes and the 20 s shutdown grace, so normal
episodes are unaffected. The clean-close and bad-frame guards are untouched.

**Evidence.** The head docker-smoke ran a real ten-player episode end to end with the new loop:
`smoke OK: seats=10 results=656B replay=7561B reason=complete` (job 97256635691), and the player
containers exited 0 — the smoke fails on a non-zero player exit.

## F16 — `update()` does not reject `rounds > MaxRounds` — **no change**

This matches the note (design 522 lists only `rounds < 3`), `sampleEpisode` clamps to
`MaxRounds = 6` (asserted at `tests/test_sim.nim:578-580`), and `config_schema` caps the input at
6. Making it raise would turn a currently-safe config into a hard failure and contradict the
committed test.

## F17 — the fallback path cannot escape the game thread

**Before.** The `except RumorError` handler applied the scripted fallback outside any `try`
(`server.nim:309-316`). If the outer rejection had been "has already spoken this round", the inner
`applyMessage` would raise the identical error, escape `runGame` and kill the game thread while
mummy kept answering `/healthz` — a hang, not a failure.

**After.** The fallback runs inside its own guard and logs the seat it skipped. The path stays
unreachable after the pre-checks (`pendingSeats()` under the lock, one apply per seat per turn);
this only removes the way it could have become a hang. Skipping a seat costs at most one turn —
the seat is still pending, the next batch retries it, and the play deadline bounds the loop
regardless.

---

## Could-not-determine items

### CD1 — "the baseline's parameters were tuned with a grid harness, not guessed" (item 7)

The review found no sweep committed anywhere. `tests/test_sweep.nim` is now that harness and it
runs in CI on every push, in debug and release:

- it replays the same 300 seeds through the **real rules** with the claim weight moved across
  `[0, 0.25, 0.5, 0.75, 1, 1.5, 2, 4] × ClaimLogOdds` and prints every cell, so the choice is
  recorded and drift shows in the log;
- it first asserts the parameterised baseline **reproduces the shipped one episode for episode**
  at the shipped weights, so the grid is measuring the thing that ships, not a lookalike;
- it asserts the shipped weight sits on the grid's plateau (no cell beats it by more than 0.03 on
  the same seeds) and beats the ignore-the-network cell;
- it asserts both constants are exactly `ln(0.6/0.4)` and `ln(0.56/0.44)`, the derivation their
  comments claim.

Measured at head (test job 97256635579, identical in both passes):

```
0.0x  -> 0.6787   0.25x -> 0.6787   0.5x  -> 0.6813   0.75x -> 0.6945
1.0x  -> 0.6833   1.5x  -> 0.6833   2.0x  -> 0.6517   4.0x  -> 0.6517
best cell 0.75x at 0.6945; shipped 1.0x at 0.6833
```

Only the ratio of the two weights can change a decision (the claim is the sign of a weighted sum),
which is why cells collapse into four regimes.

**NOTED (not fixed):** on these 300 seeds the 0.75× cell measures 0.011 above the shipped weight —
inside the plateau tolerance and roughly one to two standard errors of the paired difference, but
worth a wider sweep before anyone treats `ClaimLogOdds` as settled. Changing the constant is a
design change and no finding asked for it, so the code is unchanged.

### CD2 — which baseline figures are intended

Not settleable from the repo: the note's 0.682/0.621 and the measured 0.699/0.657 both pass the
committed bands. The measurements are echoed in every CI run; `README.md` carries the measured
pair; the note would need updating in coworld-builder, which I do not edit.

### CD3 — the retry-once network path, end to end

`tests/test_bot.nim` — `a dead transport retries once, falls back, and records it`. It points the
Bedrock transport at `http://127.0.0.1:1` (a closed port) so `client.disabled` is **false** and the
client really dispatches: attempt 0 fails at the transport for all ten seats, the retry gate admits
a second batch, the rate governor spaces it, attempt 1 fails the same way, and every seat comes
back with the scripted baseline decision — `claim` and `message` equal to `scriptedAction`'s, and
`scripted` true, which then reaches `evSay` and `eventToJson()["scripted"]` for all ten says. It
also pins the turn: `elapsed >= MinBatchSpacingSeconds` (proof the retry batch really was
dispatched) and `elapsed < TurnBudgetSeconds`.

Green at head in both passes (≈26 s each, which is the rate-governor spacing between the two
batches).

### CD4 — strict vs intent reading of item 3

Recorded under F7; the ruling is the judge's, and the facts are unchanged from the review.

---

## No test was weakened

`git diff ed38e35..5ac1631 -- tests/` removes exactly two lines: the `import std/[...]` line
(replaced by the same line plus `os`) and `decisions[index].message, "", true)`, replaced by
`decisions[index].message, decisions[index].notes, decisions[index].scripted)` — the literal `true`
became the flag under test, which is a strengthening. No assertion was deleted, no tolerance
widened, no `skip`/`xfail` anywhere. The test job's `[OK]` count went from **68**
(job 97231866330, at `ed38e35`) to **78** (job 97256635579, at head): five new cases — the rune-cut
error head, the dead-transport retry, and the sweep's three — each run in debug and release.

## Housekeeping

Pushes to this repo go through the GitHub git-data API (`git push` over HTTPS is refused in this
sandbox), so the commit shas above are the ones on `main`. One failed attempt left nine unreferenced
commit objects in the remote's object store; `main` was never moved to them (the API rejected the
non-fast-forward ref update), and they are unreachable garbage. No force-push, no history rewrite.
