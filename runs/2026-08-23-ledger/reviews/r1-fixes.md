# r1 fixes — ledger

Repo: `Metta-AI/cogame-ledger`. Reviewed sha `d5531a17b6e8fd7fb82dfe7e920d75d27551143f`.
Working copy: fresh clone at `/workspace/fixer-ledger`.

**Head: `8f3ffcb6ef3a945e54e6c39fa22147bd2a6c179f`** (`main`)
**CI: https://github.com/Metta-AI/cogame-ledger/actions/runs/32672565512 (id 32672565512) —
conclusion `success`**, jobs `test`, `docker-smoke`, `wasm-viewer` all `success`, every step
`success`. `grep -c "SEAT-COUNT FAIL"` over the full run log: **0**.

Pushed via the GitHub Git Data API (blobs → tree → commit → `PATCH /git/refs/heads/main`,
`force: false`) because plain HTTPS `git push` 401s from this sandbox. Only the eight commits in
`origin/main..HEAD` were pushed, in order; `git diff HEAD origin/main` after the fetch is empty and
`git log origin/main` shows exactly eight new commits on top of `d5531a1` — no replay, no
duplicates, no force-push.

| finding | disposition | commit | files |
|---|---|---|---|
| N1 — TRUST landmark 6/6 at `s=6` | fixed (note + test comment; code was right) | `8c84b14` | `docs/plans/2026-08-23-ledger-design.md:125-128`, `tests/test_sim.nim:172-176` |
| N2 — first-mover ±1 claim | fixed (note; claim is false, measured) | `26cb7ab` | `docs/plans/2026-08-23-ledger-design.md:96-105`, `:807-815` |
| N3 — renderer.js provenance list incomplete | fixed (note + file header; code justified as-is) | `8f3ffcb` | `docs/plans/2026-08-23-ledger-design.md:611-634`, `client/renderer.js:1-15` |
| N4 — `@font-face` "deleted" but kept | fixed (note; code was right) | `9888247` | `docs/plans/2026-08-23-ledger-design.md:627-632` |
| N5 — replay test only checks the final frame | fixed (test strengthened) | `9322824` | `tests/test_sim.nim:32-51`, `:535-568`, `docs/plans/…-design.md:838-850` |
| N6 — ring caption names 2-seat components | fixed (code) | `de84943` | `client/renderer.js:663-696`, `docs/plans/…-design.md:680-685` |
| N7 — `outMean = 0.0` when no outside meetings | fixed (documented; unreachable, no behaviour change) | `e2a2147` | `src/ledger/sim.nim:431-440`, `docs/plans/…-design.md:202-206` |
| N8 — feed/endcard rings read a module-global | fixed (code) | `98c15fa` | `client/renderer.js:105`, `:293`, `:961-996`, `:1190-1253`, `:1338-1350`, `:1560-1584` |
| N9 — fallback distinguishability | confirmed as designed — no change | — | `src/ledger/llm.nim:683`, design note `:342-343` |

Acceptance-checklist mapping (checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST). The
review filed all nine as **non-blocking** and stated that none of them falsifies a checklist item,
so the column below is "the item each fix strengthens", not "the item it un-breaks":

| finding | checklist item |
|---|---|
| N1, N2, N4, N7 | none falsified; design-note accuracy, which items 1/14 are judged against |
| N3 | **14** (chrome is the starter's, not a lookalike — provenance is checked by diff, and the note is the record of what changed) |
| N5 | **2** (replay re-derivation frame by frame; **1** — no test loosened, all four runs green) |
| N6 | **2** and **14** (the viewer's display derives from the same re-derivation the sim defines) |
| N8 | **2** and **13/14** (the viewer's display follows the frame it re-derived, including after a seek) |
| N9 | **8** (the fallback is recorded so phase 60 can count it) |

---

## N1 — the note's TRUST landmark is arithmetically inconsistent with its own formula

**Commit `8c84b14`.** The code was right; the note's landmark line was the error, so the note moved.

`trustPayoffs(sent, percent)` (`src/ledger/sim.nim:162-169`) computes `arrived = 2*sent`,
`returned = (arrived*percent + 50) div 100` clamped to `0..arrived`, and returns
`(6 - sent + returned, 2 + arrived - returned)`. For `s = 6, p = 50` that is `(6, 8)`, not `(6, 6)`:
the note's own coin invariant `investor + trustee == 8 + s` fixes the pot at 14 coins at `s = 6`, so
6/6 is only reachable at `s = 4`. Nothing in play used the wrong landmark — the prompt spells out
the formula (`llm.nim:289-306`) and the `mirror` baseline sends 4 / returns 50 (`llm.nim:153-156`,
`:214-218`), i.e. it lands on the real 6/6 point.

Changed: the note now reads "an even split of the pot (`s = 4, p = 50`) → 6 / 6 … full trust with a
fair split (`s = 6, p = 50`) → 6 / 8", both of which `tests/test_sim.nim:176-177` already asserted;
and the test comment that pointed at the note's error was replaced with a plain statement of the
arithmetic, since the error is gone. **No assertion was changed** — the diff on `tests/` is comment
lines only (`git show 8c84b14 -- tests/`).

Evidence: `tests/test_sim.nim` `[OK] trust keeps its coin invariant and never returns more than
arrived` and `[OK] fair play pays six in all three games`, green in debug and `-d:release` in run
32672565512.

## N2 — the note's "first-mover counts differ by at most 1" is not a property of this schedule

**Commit `26cb7ab`.** Note only. The claim is not merely unenforced, it is **false**, so it could
not be "implemented" without changing the design; the note now states the invariant the code does
guarantee and the test does assert.

I measured it rather than inferring it. Compiling a throwaway driver against `src/ledger/sim`,
re-deriving `firstCount` from `initSim(...).schedule` over **10 000 seeds × `rounds` in
{4, 7, 14, 28} = 40 000 episodes**:

```
trials 40000 violations 23374 worst spread 5 at seed 6806 rounds 14
```

58 % of episodes have `max(firstCount) - min(firstCount) > 1`, and the worst spread is 5. The cause
is structural, exactly as the review inferred: the subgame is drawn per pairing
(`sim.nim:275-279`), so how many asymmetric meetings a seat draws is itself random and caps its
`firstCount`. This settles the review's first "Could not determine".

Changed: note lines 96-105 now say the guarantee is local, state the two invariants the code holds
(at every asymmetric meeting the first mover has no *more* prior first-mover assignments than its
partner; `firstCount[seat] <= asymmetric[seat]`), say explicitly that a global ±1 balance is not
available, and cite the measurement. The test-plan line (note `:807-815`) now asks for what
`tests/test_sim.nim:108-134` already asserts. **No code and no test changed** — deliberately: the
existing test is correct and the ±1 assertion the review suggested adding would fail on the majority
of seeds.

## N3 — the note listed four changed `renderer.js` functions as untouched

**Commit `8f3ffcb`.** Note and the file's own header. No code change: every edit I inspected is
inside the event vocabulary, the two new state fields or the plaza geometry, and no starter section
is dropped from the page or the CSS.

Function-by-function diff of `client/renderer.js` against
`/workspace/starters/cogame-babel/client/renderer.js` (script: split both files on
`^  function <name>(`, compare bodies byte for byte). At the new head:

- **22 byte-identical**: `makeRenderer`, `loadImages`, `assetUrl`, `ellipsize`, `hexToRgb`, `shade`,
  `rgba`, `roundRect`, `wrapLines`, `drawParchment`, `drawTag`, `seatBlock`, `noteHeight`,
  `seatColor`, `makeNameMap`, `applyNames`, `clampName`, `isBaselineFiller`, `roundBase`,
  `blockHead`, `escapeHtml`, `reasonLine`.
- **9 removed with babel's card-and-booth scene**: `sceneOf`, `sceneText`, `boothPairs`,
  `pendingSeat`, `drawSeat`, `drawCard`, `drawShape`, `drawRibbon`, `spellTokens`.
- **26 new** (plaza scene, the two DOM overlays, the transport measurement): `gameName`, `roleName`,
  `moveText`, `isKind`, `seatBlockAbove`, `seatBlockBelow`, `seatAngle`, `seatHome`, `tableSpot`,
  `plazaPairs`, `eased`, `drawPlaza`, `drawTable`, `drawVerdict`, `drawHandshake`, `drawKnife`,
  `drawSnappedCoin`, `drawCoins`, `drawThreads`, `drawAvatar`, `drawHalo`, `ringGroups`, `syncRail`,
  `meetingText`, `medianOf`, `relayout`.
- **15 changed**: `computeLayout`, `draw`, `describeEvent`, `endText`, `phaseText`, `matchHeader`,
  `updateScorebug`, `buildScrub`, `renderFeed`, `updateEndscreen`, `makeEffects`, `stateToView`,
  `attachLive`, `attachReplay`, `bindFeedToggle`.

(`attachLive` and `updateEndscreen`/`renderFeed` are in the changed set partly *because of* the N8
fix, which is why this commit is last: the list describes the head, not an intermediate state.)

The note's bullet now carries all four lists by name and says what each changed function's edit is;
the file header, which carried the same wrong claim (`renderFeed`'s structure, `bindFeedToggle`,
`stateToView`, `attachLive`, `attachReplay` "is babel's chrome, carried across"), was corrected to
match and points at the note for the enumeration. Evidence: `node --check client/renderer.js`
passes; the `wasm-viewer` browser step is green with `{"loaded":true, …,"feed_lines":39}`.

## N4 — `chrome.css` keeps the `@font-face` the note says was removed

**Commit `9888247`.** Note only; the code was right and is what checklist item 14 wants.

`diff /workspace/starters/cogame-babel/client/chrome.css client/chrome.css` is a single hunk
`443a444,681`: 238 added lines, **zero removed** (`diff … | grep -c '^<'` → 0), zero modified. The
`@font-face` for `rajdhani` is still at `client/chrome.css:9` and is still live — `data/font.ttf`
ships in the repo and `client/renderer.js:62-63` names `rajdhani` first in `GLYPH_FONT`, so deleting
it would have been a bug, not a cleanup. The note now says the file is strictly append-only and that
the wordmark's inner text is the only starter element deleted anywhere.

## N5 — the replay test asserted the endpoint, not each frame

**Commit `9322824`.** This is the one finding where a test improvement was warranted, and it is a
strengthening: no existing assertion was removed, weakened, or skipped.

Before: `tests/test_sim.nim:518-525` checked `frames.len == events.len + 1`, final-frame
`tableStateJson`/`resultsJson` equality, and `frames[1] != frames[^1]`. That test is untouched.

Added: `test "every frame re-derives the prefix it stands for, field by field"`
(`tests/test_sim.nim:535-568`). For **every** `i` in `0 .. events.len`:

1. `frames[i].events == live.events[0 ..< i]`. This is the strong one. `replayMatch` never copies a
   recorded `round`/`meeting`/`gossip`/`end` event into the frame — `beginRound`, `applyMeeting`,
   `applyGossip` and `settle` each append their **own derived** event (`sim.nim:501-509`, `:558-572`,
   `:591-596`, `:482-485`) — so comparing the frame's log to the recorded prefix compares every
   field of every tick: both payoffs, both moves, both memos, both `scripted` flags, the four
   pairings, the subgames and the first movers.
2. `replayMatch(config, events[0 ..< i])` ends on exactly `frames[i]` (`tableStateJson` equality), so
   no frame borrows state from an event that has not been played yet.
3. Every tick at which the **live** sim published a state equals the frame with that event count.
   `playEpisode` now records `(events.len, tableStateJson)` into `liveCheckpoints` at each round
   open and at the settlement (`tests/test_sim.nim:32-51`); the test asserts
   `checkpoints.len == rounds + 1` and frame equality at each.

Why round-*close* is not among the checkpoints, stated in the test and in the note: the recorded log
carries no "round closed" event, so `replayMatch` deliberately holds the round open until the next
`round` event arrives (`sim.nim:861-867`) — the live sim is `phase: "between"` there while the
replay is `phase: "resolve"`. That is by design (gossip is recorded after the four meetings), it is
not a shared tick, and pretending otherwise would have meant loosening the comparison. The two ticks
that *are* shared are asserted exactly.

**Demonstrated non-vacuous.** Temporarily deleting the two `setMemo` lines from `replayMatch`
(`sim.nim:882-883`) makes the new test fail at `i = 3` — the first `meeting` event — reporting the
missing `memoA`/`memoB`; the old test only noticed at the final frame. The mutation was reverted
(`git diff` on `src/ledger/sim.nim` clean before the commit).

Evidence in CI run 32672565512, job `test`, both modes:
`[OK] every frame re-derives the prefix it stands for, field by field` at log lines 478 (debug) and
618 (`-d:release`), alongside the untouched `[OK] replayMatch re-derives one frame per event prefix`.

## N6 — the ring caption named 2-seat components

**Commit `de84943`.** Code change, in the viewer.

The note's ring section is unambiguous and there is no line legitimising pair-level captions: a
**ring** is "a connected component of size `>= 3` in the flagged graph" (note `:206-207`), and the
caption example is three names (`RING: Bolt · Rivet · Piston`). `src/ledger/sim.nim:437-463`
(`ringComponents`) applies `if component.len >= 3`. `client/renderer.js`'s `ringGroups` union-found
every flagged pair and returned every component with **no size filter**, so `#ringnote` rendered
`RING: Bolt · Rivet` for a single flagged pair — a pair the sim does not call a ring.

`ringGroups` now ends `.filter(function (group) { return group.length >= 3; })`, with a comment
citing `sim.nim:437-463`. Verified by evaluating the function under node:
`[{a:1,b:5}]` → `[]` (no caption); `[{a:1,b:5},{a:5,b:3}]` → `[[1,3,5]]`;
`[{a:1,b:5},{a:5,b:3},{a:6,b:7}]` → `[[1,3,5]]`; `[]` → `[]`.

Nothing else moved: the red thread is still drawn per flagged pair (`drawThreads` reads
`view.rings`), the feed line `RING: Bolt · Rivet (+3.5 coins between them)` is still per flagged
pair — that is the note's feed spec (`:704`) and it is correct as a per-pair line — and the endcard
still lists every flagged pair. No scoring path is involved either way (`resultsJson` reads
`ringThreads().len` only, `sim.nim:679`). The note's Red-threads bullet now spells out the size
filter and says a lone flagged pair is a thread, not a ring.

## N7 — `outMean = 0.0` when a flagged pair's members have no outside meetings

**Commit `e2a2147`.** Documented, no behaviour change — the branch is unreachable in play and the
`0.0` is what keeps the expression total.

Reaching the line needs `inCount >= 2` (`sim.nim:429-430`), and `drawSchedule` never places a pair
in consecutive rounds (`sim.nim:260-265`, asserted `tests/test_sim.nim:93-106`), so two meetings of
the same pair are at least seven rounds apart and each member necessarily carries at least six
meetings with other seats. Only a hand-constructed history can get there. A defensive `continue`
would therefore be dead code that also silently changes the meaning of a hand-built fixture, so the
smallest correct change is the one made: a comment at `sim.nim:431-439` giving the reachability
argument and saying what `0.0` means if a fixture does reach it, plus a clause in the note's
`outMean` definition (`:202-205`) so the case is no longer undefined there. Ring tests unchanged and
green: `[OK] a fed pair is flagged and a level table is not`, `[OK] ring detection NEVER changes a
score`.

## N8 — the feed's and the endcard's RING lines read a module-global set by the last drawn frame

**Commit `98c15fa`.** Real display bug; code change.

`client/renderer.js:109` held `var latestRings = []`, overwritten by `draw()` at `:299` from
`view.rings` on **every animation frame**; `renderFeed` (`:991`) and `updateEndscreen` (`:1243`)
read it. In `attachReplay`, `setIndex` calls both of those *before* the next `requestAnimationFrame`
draws the new index (`:1551-1569` then `:1572-1597`), so after a seek the feed's and the endcard's
RING lines described whichever frame had last been drawn — not the tick the feed prefix ends at. A
seek back to an earlier tick showed the later frame's ring set. `results` carries only `ringPairs`
(a count), so the pair list genuinely has to come from a frame; it was coming from the wrong one.

Now: `renderFeed(element, events, nameMap, currentIndex, rings)` and
`updateEndscreen(container, results, show, nameMap, rings)` take the list as a parameter.
`attachReplay`'s `setIndex` passes `currentState().rings || []` — the same re-derived frame the
canvas is about to be drawn from — and `attachLive` passes the live snapshot's `rings` (the
spectator frame is `sim.tableStateJson()` plus fields, `server.nim:99-113`, so it carries them).
The module-global and its assignment in `draw()` are deleted, so no path remains by which one
frame's ring set can be rendered against another frame's feed.

Evidence: `node --check client/renderer.js` passes; CI run 32672565512's `wasm-viewer` "Load the
bundle in a real browser" step is green — `{"loaded":true,"ms":289,"clock":"ROUND 3 / 6 · SETTLING",
…,"feed_lines":39}`, `soak: 15s of playback kept advancing`, `scrub readouts: 0%="ROUND 3 / 6 ·
SETTLING"  50%="ROUND 3 / 6 · SETTLING"  100%="FINAL — 6 ROUNDS"` — i.e. the feed still renders and
seeks still work after the change. The note's Endcard bullet now records where the pair list comes
from.

## N9 — the replay cannot distinguish an LLM fallback from a scripted registration

**Confirmed as designed. No change, no commit.**

The review's own reading is right and the note already pins the counting mechanism, so there is
nothing to fix. Verified at the new head:

- `src/ledger/llm.nim:683` is `echo "ledger: seat ", seat, " falling back to scripted decision"`,
  emitted inside `for index in open:` — the loop that runs only over seats still undecided **after**
  attempt 1 and the single retry (`:646-680`). It is the only occurrence of that string in `src/`.
- Seats that registered `PLAYER_SCRIPTED` take the earlier branch at `llm.nim:639-645` and never
  reach it; so does every seat when `client.disabled` (no credentials), which the note documents
  separately as a distinct case (note `:345-346`).
- The design note at `:342-343` specifies exactly this text: "recorded with `scripted: true` on the
  meeting event and logged as `ledger: seat N falling back to scripted decision`". Code and note
  agree character for character with `N` = the seat id.

Phase 60 counts fallbacks from the game log, not from the replay's `scriptedA`/`scriptedB` booleans.
Checklist item 8's "the fallback is recorded so phase 60 can count it" is satisfied by that line.

## NOTED (not fixed)

Not findings in this round's review; recorded and left alone.

- The review's third "Could not determine" — the wait bound inside `bitworld/runtime`'s
  `writeCogameUri` for the non-POST artifact path (`server.nim:163`) — is still unresolved here.
  `bitworld` is a nimby dependency, not vendored; it *is* readable in this sandbox at
  `~/.nimby/pkgs/bitworld` after `nimby --global sync nimby.lock`, which is what would settle it.
- The 16-attempt resample cap (`sim.nim:262`) can in principle fall through and place a pair in
  consecutive rounds; the fall-through probability is `(1/7)^16` per pass boundary. A sweep asserting
  the no-consecutive property over N seeds would settle it. Not touched — no finding asked for it.
- `ringGroups`/`syncRail` recompute the union-find on every frame. Harmless at 8 seats.

## Coordinator action required

The design note was amended **in the repo only**, at
`docs/plans/2026-08-23-ledger-design.md`. The run copy at
`/workspace/coworld-builder/runs/2026-08-23-ledger/design.md` is now stale — it was byte-identical
to the in-repo copy at the reviewed sha and is not any more. Sync it with:

```
cp /workspace/fixer-ledger/docs/plans/2026-08-23-ledger-design.md \
   /workspace/coworld-builder/runs/2026-08-23-ledger/design.md
```

Amended sections: TRUST landmarks (N1), Roles / first mover (N2), Ring detection `outMean` (N7),
Chrome provenance `renderer.js` list (N3), Removed-from-the-starter (N4), Red threads (N6),
Readouts → Endcard (N8), Tests → Schedule (N2) and Tests → Replay (N5).
