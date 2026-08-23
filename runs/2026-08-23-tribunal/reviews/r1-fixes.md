# r1 fixes — 2026-08-23-tribunal

Repo: `Metta-AI/cogame-tribunal`, branch `main`
Head: `11ec31627ffc8e3db159e879d7b4b513f183da69` (was `d69e4e3e79ea99e1c877c00b6d6614af6b978d16`)
CI: https://github.com/Metta-AI/cogame-tribunal/actions/runs/32652071584 — **success**
(push event, `headSha == 11ec3162…`; jobs `test` 97225135935 ✔, `docker-smoke` 97225136091 ✔,
`wasm-viewer` 97225257449 ✔ including its `Load the bundle in a real browser` step, which printed
`{"loaded":true,"ms":308,…,"feed_lines":27}` and `scrub readouts: 0%="ROUND 1 / 2" 50%="ROUND 2 / 2"
100%="TRUTH — NOT GUILTY · JURY 3/3"`. `grep 'SEAT-COUNT FAIL'` over the docker-smoke log: no
matches; it printed `smoke OK: seats=5 results=342B replay=2475B reason=complete`.)

Pushed through the GitHub Git Data API (blobs → tree → commit → ref, `PATCH …/git/refs/heads/main`
with `force: false`), because the sandbox git credential has no write access to this repo. Three
commits, one per finding, fast-forward on `d69e4e3`; nothing rewritten, nothing force-pushed.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking-candidate, item 2) | **fixed** | `c02c4c04142d63e9f2ff6c7f7ed5e5387b9806a8` | `src/tribunal/sim.nim:956-971`, `tests/test_sim.nim:409-429` |
| F2 (advisory) | **fixed** | `6bcbff1483889c4b2a943dc43c7aefec92c053e4` | `src/tribunal/llm.nim:53,224-226`, `src/tribunal/server.nim:302-307`, `tests/test_bot.nim:125-134` |
| F3 (advisory) | **fixed** | `11ec31627ffc8e3db159e879d7b4b513f183da69` | `src/tribunal/sim.nim:39-40,616,657,700`, `src/tribunal/llm.nim:33`, `tests/test_sim.nim:340-343` |
| F4 (advisory) | not fixed — the note contradicts itself | — | `src/tribunal/sim.nim:314,317` |
| F5 (advisory) | not fixed — the note contradicts itself | — | `client/renderer.js:166-171` |
| F6 (advisory) | not fixed — deviation is required, item 11 satisfied | — | `client/chrome.css:266,466` |
| F7 (advisory) | not fixed — sound as implemented | — | `src/tribunal_player.nim:56-92` |
| F8 (advisory) | not fixed — deliberate, contract intact | — | `src/tribunal/llm.nim:103-106` |
| F9 (advisory) | not fixed — nothing to fix (verified reproducible) | — | `tools/make_manifest.py` |
| F10 (advisory) | not fixed — the note's literal assertion is unsatisfiable | — | `tests/test_sim.nim:230-268` |
| F11 (advisory) | **NEEDS-DESIGN** — general property of derived events, not a verdict bug | — | `src/tribunal/sim.nim:708-709` |
| F12 (advisory) | not fixed — starter-verbatim, spectator-only | — | `client/renderer.js:967-1010` |
| F13 (advisory) | not fixed — bounded by the pre-turn deadline check | — | `src/tribunal/sim.nim:215-231` |
| F14 (advisory) | not fixed — the note prescribes the fixture names | — | `coworld_manifest_template.json` |

---

## F1 — a `deadline` ending at or after the ballot re-derived as `complete` — fixed

Commit `c02c4c04` — `fix(sim): F1 — a deadline at the ballot re-derives as "deadline"`.
Satisfies **checklist item 2** ("replaying the recorded events through the sim reproduces the
recorded per-tick state frame by frame … a test asserts it").

**Reproduced first, at the reviewed sha.** Two argument rounds resolved normally (so
`resolveRound` → `openBallot` had already set `phase = phBallot`), one real juror vote, then
`forceBallot()` — the shape the server produces when the play budget expires during the closing
round and the deadline is detected at the top of the ballot turn (`server.nim:271-277`):

```
seed 21 live.reason=deadline replay.reason=complete
  tableStateJson equal: false
  recorded end event: deadline   replayed end event: complete
  results.reason live=deadline replay=complete
(same for seeds 22, 23)
```

**What the code did.** `replayMatch` recovered the deadline jump only from a vote event seen while
the phase was still `phArgument` (`sim.nim:978-982` → `beginDeadlineBallot`, which is
`if sim.done or sim.phase != phArgument: return`). With the ballot already open that call is a
no-op, the three recorded votes applied, the third called `settle`, and `settle`'s
`if sim.reason.len == 0: sim.reason = "complete"` filled in the wrong reason. The recorded `end`
event could not repair it (`of evEnd: if not sim.done:` — the sim was already done).

**What it does now.** `replayMatch` seeds `sim.reason` from the recorded `end` event's text before
replaying:

```nim
  for event in events:
    if event.kind == evEnd and event.text.len > 0:
      sim.reason = event.text
```

The reason is a wall-clock signal — which turn the play deadline landed on — that the rules cannot
re-derive from the seed and the decisions; nothing in the vote events distinguishes a
deadline-called ballot from a normal one, so the `end` event's text is the log's only carrier of
it, exactly as `event.cards` is the log's carrier of an introduction. `reason` is rendered only
once the sim is `done` (`tableStateJson():906`, `playerStateJson():931`), so seeding it changes no
earlier frame; the mid-argument path still goes through `beginDeadlineBallot` unchanged.

**Evidence.** The same probe after the fix: `live.reason=deadline replay.reason=deadline`,
`tableStateJson equal: true`, replayed end event `deadline`, `results.reason` both `deadline`, for
seeds 21/22/23. New test `tests/test_sim.nim` → *"a deadline at the ballot re-derives as a
deadline, not as complete"* asserts the frame count, `frames[^1].done`, `frames[^1].reason`, the
replayed `end` event's kind and text, `$frames[^1].tableStateJson() == $live.tableStateJson()` and
`resultsJson()["reason"]`. It **fails on the parent commit** (checked: `[FAILED] a deadline at the
ballot re-derives as a deadline, not as complete`) and passes here. In CI it ran in both modes:
`[OK] a deadline at the ballot re-derives as a deadline, not as complete` twice in job 97225135935.
The existing mid-argument deadline test (`test_sim.nim:383-394`) is untouched and still passes.

## F2 — the LLM→scripted fallback carried `scripted: false` into the replay — fixed

Commit `6bcbff14` — `fix(llm): F2 — a fallback decision is recorded as scripted in the replay`.
Strengthens **checklist item 8** ("the fallback is recorded so phase 60 can count it") on the
replay side; the stdout line item 8 relies on is unchanged.

**What the code did.** `server.nim:303` derived the event's provenance from configuration only —
`let wasScripted = scripted[seat] != skNone or client.disabled` — which is false for a seat that
was LLM-driven and merely failed twice, so `decideAll`'s final fallback (`llm.nim:595-598`) landed
in the event log and in `tableStateJson().seats[].scripted` as if Claude had produced it.

**What it does now.** `scriptedAction` stamps `result.scripted = true` on the decision it returns
(one new `Decision` field, `llm.nim:53`), and the server ORs that into the flag:

```nim
          let wasScripted = decision.scripted or
            scripted[seat] != skNone or client.disabled
```

Every scripted source is now recorded as scripted: a configured `tally`/`hedge` seat, a disabled
client, the two-attempt LLM fallback, and the post-rejection fallback at `server.nim:313-319`
(which already passed `true`). An LLM decision from `parseReply` keeps the field's default `false`.

**Evidence.** `tests/test_bot.nim`'s *"decideAll falls back to scripted with no credentials"* now
also asserts `decisions[index].scripted` for all five seats and
`not parseAdvocateReply(%*{"argument": "my own words"}).scripted`. Green in CI job 97225135935 in
both modes (`[OK] decideAll falls back to scripted with no credentials`, twice).

## F3 — `notes` capped only in the LLM parse path — fixed

Commit `11ec3162` — `fix(sim): F3 — the rules cap notes at 600 runes, not just the LLM parse`.
Satisfies **checklist item 9** ("every string that reaches the replay … is truncated on rune
boundaries; a test feeds multi-byte input at the cap").

**What the code did.** `applyArgument`/`applyWhisper`/`applyVote` stored `notes` verbatim
(`if notes.len > 0: sim.notes[seat] = notes`), so the 600-rune cap the design pins existed only in
`parseAdvocateReply`/`parseJurorReply`/`parseVoteReply`. `sim.applyArgument(seat, @[], "hi",
<800 runes>, true)` stored 800 runes into the event log and the replay JSON.

**What it does now.** The three apply procs run notes through the same rune-safe `tidy`
(`sim.nim:180-186`, `runeSubStr`) that already caps `argument`/`whisper`/`reason`, and
`MaxNotesLen = 600` moves from `llm.nim` to `sim.nim` beside the other three caps so the rules own
the limit the parse path enforces. Double-capping is inert: `cleanText` already returns exactly 600
runes (`runeSubStr(0, 599) & "…"`), which `tidy(_, 600)` leaves alone. `tidy` also collapses
newlines, which is what every other free string in the sim gets and what keeps the one-line feed
rendering (`renderer.js:1005-1009`) honest.

**Evidence.** `tests/test_sim.nim`'s multi-byte case already fed 800 × `"é"` as notes and asserted
only UTF-8 validity; it now also asserts `sim.notes[sim.advocateSeat[0]].runeLen == MaxNotesLen`
and `sim.events[^1].notes.runeLen == MaxNotesLen`, alongside the existing UTF-8 and JSON round-trip
assertions. Green in CI job 97225135935 in both modes (`[OK] a multi-byte argument is cut on rune
boundaries and stays valid UTF-8`, twice). `tests/test_bot.nim:180`'s `cleanText(long,
MaxNotesLen)` assertion is unchanged and still compiles against the moved constant.

---

## Findings not fixed, with the evidence

### F11 — the reveal fires one feed beat before the `verdict` event — NEEDS-DESIGN, not fixed

The observation reproduces, but it is **not specific to the verdict**: it is the defining property
of every *derived* event in this log, and fixing it for the verdict alone would make the verdict
inconsistent with the rest. Frame dump of a complete 2-round episode (seed 15, executed at the
fixed head, `frames[i]` labelled with the last event the feed has drawn at that scrub position):

```
frame  6 lastFeedEvent=whisper round=0 phase=argument      <- round 0 still open
frame  7 lastFeedEvent=whisper round=1 phase=argument      <- round ALREADY advanced …
frame  8 lastFeedEvent=round   round=1 phase=argument      <- … the "round" line lands here
frame 15 lastFeedEvent=vote    round=2 phase=ballot  sealed=true
frame 16 lastFeedEvent=vote    round=2 phase=done    sealed=false verdict=guilty
frame 17 lastFeedEvent=verdict round=2 phase=done    sealed=false verdict=guilty
```

Frame 7 (the state after the last whisper of round 0) already carries `round=1` while the feed's
"The bench opens round 2" line is drawn at frame 8 — exactly the offset F11 describes at frame 16.
The cause is the contract `frames[i] = state after events[0..<i]` combined with derived events
(`round`, `verdict`, `end`) being *announcements of a transition the state has already made*. The
renderer knows this and compensates deliberately: `renderer.js:1080-1082`, "The verdict frame
reveals before its event is drawn in the feed; the reveal animation is keyed off the STATE so the
two never disagree" — the clock, the scorebug and the stage all turn over on the same frame, and
only the feed line lags, as it does for every round change.

Removing the offset means the third `applyVote` must no longer settle: the reveal would have to
move to a separate step driven by the `verdict` event. That changes the resolution rule the design
note states at step 9 ("the third vote settles the episode", design lines 145-152) and touches
`applyVote`, `forceBallot`, the server turn loop (which would otherwise spin on a `phBallot` phase
with an empty `pendingSeats()`), `replayMatch`'s `evVerdict` arm, and three tests — a design change,
not the smallest change at the cited site, and one with real regression surface against the F1 fix
committed this round. Recording it as **NEEDS-DESIGN** rather than making it. No checklist item is
falsified: item 2 holds (live and replay agree frame for frame — asserted), and the sealing contract
holds (no frame *before* the verdict frame carries a vote — `test_sim.nim:230-268`).

### F4 — aliases from a second rng stream

Not fixed: the note requires both "a single rng stream … roles, truth, case, deck, deal, aliases"
(design line ~250) and that `tableNames` be carried over from bullwhip **verbatim** (design lines
249-250). `tableNames` opens its own stream (`sim.nim:202-206`), so the two requirements are
mutually exclusive and the builder kept the verbatim one. Both streams are pure functions of the
seed, so replay self-sufficiency — the property any checklist item cares about — is untouched
(`test_sim.nim:156` asserts `a.names == b.names` for a repeated seed). Changing it would alter every
seeded scenario and invalidate the tuned truth-tracking band in `test_bot.nim:92-106` for no
checklist gain.

### F5 — jury box centre-low rather than right

Not fixed: the note asks for the jury box on the right (line 694) *and* for the two podiums in the
left/right columns (lines 685-690); with five seats those are mutually exclusive, and the
implementation keeps the podium placement. Every element the note asks the jury box to contain is
present (`renderer.js:522-601, 605-666`). Viewer layout is not a checklist item and item 11 is
satisfied (see F6).

### F6 — two `chrome.css` hunks

Not fixed: a five-seat scorebug cannot use bullwhip's four-column grid, so the `repeat(5, 1fr)`
hunk is forced by the seat count. Item 11's two required rules survive verbatim —
`.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` (`chrome.css:281-293`) and
`.plate-label { display: none; }` under `@media (max-width: 640px)` (`chrome.css:461-465`) — which
the reviewer confirmed. The 520 px step sitting before the 420 px step is the cascade working as
intended: at 360 px the narrower rule wins and the bug renders two columns, which is the legible
outcome item 11 is asking for.

### F7 — the player wraps its receive loop and exits 0

Not fixed: the wrap exists because the game's `quit(0)` (`server.nim:202`) can outrun the flushed
final frame, and whisky's `receiveMessage` raises rather than returning on a close frame, so the
un-wrapped starter loop would exit non-zero on a *normal* episode end. The reviewer traced this and
found it sound for its stated purpose; no checklist item covers the player container's exit code.
Distinguishing "game finished" from "socket died at connect" in the exit code would be a new
behaviour, not a fix to a stated defect.

### F8 — the Bedrock model list drops `us.anthropic.claude-sonnet-4-6`

Not fixed: no checklist item names the model list, and the rotation contract the note actually
depends on is intact (`llm.nim:108-116, 448-460`, verified by the reviewer). The dropped id is the
one entry without a versioned inference-profile suffix; adding it back would put a model that can
deny access back into the rotation, spending a 45 s timeout to discover it. Re-adding it is a
judgement call about hosted credentials I cannot verify from the sandbox, so I am not making it
blind. If phase 60 shows access to it, it is a one-line addition at `llm.nim:103-106`.

### F9 — `tools/make_manifest.py` is a new generator

Nothing to fix: the reviewer executed the generator over a copy of the tree and got an empty
`git diff` against the committed `coworld_manifest_template.json`. Additive tooling; file modes are
already correct (`100644` for the generator, `100755` for the two `coworld build` hooks, asserted by
`ci.yml:166-174, 225-236`).

### F10 — test item 7 reworded

Not fixed: the note's literal assertion ("the built prompt string for every seat contains none of
the culprit's name") is unsatisfiable by construction — `userPrompt` must print the suspect list and
the accused (`llm.nim:364-365`), and the culprit is one of those four suspects (`sim.nim:340`).
Making the literal assertion pass would mean hiding the suspect list from the seats, which destroys
the game. The implemented test asserts the property the note is protecting (which of them it is
never leaks) over all five seats plus full pre-verdict frame sealing, and the reviewer independently
verified it over 200 seeds × 5 seats with zero leaks.

### F12 — the feed renders future events dimmed from frame 0

Not fixed: both the loop (`renderer.js:967-1010`) and the `.feed-future { opacity: 0.32 }` rule
(`chrome.css:247`) are starter-verbatim, no seat ever sees the feed, and a drag-to-seek replay
exposes the ending by construction anyway. Changing it is a starter-wide behaviour change outside
this round's findings.

### F13 — `long-trial`'s worst case lands on the 720 s line

Not fixed. The worst case is adversarial (every one of six turns consuming a full batch **and** its
retry at the 45 s LLM timeout) and it is bounded by the pre-turn deadline check regardless: the
ballot is a turn, the check runs at the top of every turn inside the lock (`server.nim:264-277`),
and `forceBallot` settles and scores synchronously, so the episode never fails to produce results
and a replay. The implementation follows the note's own formula exactly (design lines 411-412), so
moving the line means changing the note's arithmetic, not the code — and the two candidate edits
both make things worse: tightening the clamp to `maxTurns - 2` would cap `long-trial` at 4 rounds,
which is the `standard` variant, and raising the variant's `episode_timeout_seconds` changes a
manifest value the note prescribes. Item 5's checkable half holds — every wait has an explicit bound
(connect 180 s, LLM 45 s × ≤2 batches per turn, no round barrier) and there is no unbounded loop.
CI's real episode settled `reason=complete` in ~4 s (run 32652071584, job 97225136091).

### F14 — certification fixture policy names collide with the alias namespace

Not fixed: `Sprocket, Gizmo, Ratchet, Widget, Bolt` are the five names the design note prescribes
for the certification fixture (design lines 774-775), and they are generated into the manifest by
`tools/make_manifest.py`. The effect is a cosmetic alias→alias rewrite in one offline fixture; item
4 is satisfied because both namespaces exist and the split works (agents see `sim.names` only,
`resultsJson`/`policyNames`/the viewer carry policy names). Changing the fixture names would deviate
from the note to fix a scoreboard cosmetic in a fixture no league match uses.

---

## NOTED (not fixed, not a finding in this round's review)

- `tests/test_sim` and `tests/test_bot` (the compiled test binaries) are not in `.gitignore`; a
  `nim c -r tests/…` run leaves them in the worktree where `git add -A` will pick them up. I kept
  them out of all three commits by hand. Worth one line in `.gitignore` in a later round.
