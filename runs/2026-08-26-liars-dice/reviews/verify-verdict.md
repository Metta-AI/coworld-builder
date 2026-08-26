blocking: 0

# Phase-60 verdict — liars-dice (2026-08-26)

Adjudicated fresh: SPEC §Definition of done and `prompts/60-verify.md` read first, the run
artifacts (`viewer-smoke.json`, `viewer-smoke.png`) and the live APIs checked independently,
VERIFY.md read last and audited claim-by-claim. Every Observatory call below was re-fetched by
this judge at adjudication time (2026-08-26, post-22:49Z); nothing was taken on the verifier's
word alone. Head evidence: `runs/2026-08-26-liars-dice/VERIFY.md` (commit `439704a`),
`release-result.json` (commit `83901cd`).

## Check 1 — ≥2 completed rounds after fillers set: CONFIRMED

Re-fetched `GET /rounds?league_id=league_3aa78ed0…`: rounds 1 and 2 both `completed`
(`22:23:24.743Z`, `22:38:25.440Z`), both `error: null`, no failed/discarded rounds — identical
to VERIFY.md's paste.

One wording defect audited hard: VERIFY.md says the fillers were registered "at 22:22:44Z"
while round 1 was created at `22:22:00.93Z`, then asserts the fillers preceded the round — as
written, those two timestamps do not prove that ordering (the 22:22:44Z stamp is the log's
batch-write time for the whole phase-50 heartbeat, not the HTTP call time). I settled it
independently: round 1's episode request `ereq_e059906f` was created at `22:22:01.249Z`,
0.3 s after the round, and **already seats both fillers** (`liars-dice-bayes`,
`liars-dice-pressure`, both `is_filler: true`) — the ladder can only seat registered fillers,
so registration necessarily preceded round 1's creation. And on the SPEC's literal wording
("rounds **completed** after the fillers were set"), both completions (22:23:24Z, 22:38:25Z)
post-date even the latest possible registration time. TRUE stands on either reading; the
narrative sentence is sloppy, not wrong in substance (noted below, non-blocking).

## Check 2 — both champions ranked, fillers absent: CONFIRMED

Re-fetched `GET /divisions/div_5428acaf…/leaderboard`: exactly two rows —
`1 daveey liars-dice-calibrator:v1 1001.47 rounds_played=2` and
`2 daveey-1 liars-dice-needler:v1 998.53 rounds_played=2`. Matches VERIFY.md verbatim. Both
champions ranked with `rounds_played ≥ 1`; fillers absent from the board (and re-verified as
the registered filler set via `GET /leagues/$L/filler-policies`: bayes v1 + pressure v1,
neither a champion policy).

## Check 3 — latest round's episode request completed with replay: CONFIRMED

Re-fetched `GET /rounds/round_9ce791c0…/episode-requests` →
`ereq_e1729468-7562-42f5-89c0-d144b1a22483`, `status: "completed"`, non-null `replay_url`
(`…/replays/880929b7-….replay`). Participants: seats 0/1 = `daveey` (calibrator) and
`daveey-1` (needler), `is_filler: false`; seats 2/3 = bayes/pressure, `is_filler: true`.
Participant scores `[0.6875, 0.5, 0.25, 0.5625]`. All identical to VERIFY.md's paste. The
documented 405 on the flat `?round_id=` route and the nested-route workaround are accepted as
a platform divergence per the brief.

## Check 4 — replay bytes valid and show the game: CONFIRMED

Re-fetched the replay from S3 myself: 11340 bytes, `jq -e` strict parse ok, `protocol` =
`liarsdice.replay.v1` (matches design.md §Replay payload line 523; the manifest carries no
`replay` protocol key — its `protocols` map is `["global","player"]` — so the verifier's
comparison against the design declaration plus the manifest's `reason` enum
(`["complete","deadline"]`) was the correct available check, and it documented that).
`results.reason == "complete"`. Decision events use `kind` (documented divergence, accepted):
29 bid/challenge events, **0** with `fallback == true`; champion seats: seat 0 n=8, seat 1
n=6, all `scripted=0 fallback=0`, every one with non-empty `say`. The table talk is
non-trivial and situational ("Widget's pattern finally breaks—fives are scarce and 3 x 5 is a
stretch."). All numbers reproduce VERIFY.md's paste exactly.

## Check 5 — hosted game log clean: CONFIRMED

Re-fetched `GET /episode-requests/ereq_e1729468…/artifacts/logs` with the elevated header:
32257 raw bytes, 4 containers, decoded the python byte-string reprs myself, then ran the exact
four-pattern grep: **CLEAN** — zero matches for `falling back|LLM provider is
unavailable|cut off at max_tokens|rejected`. Matches the verifier's result independently, not
just its paste.

## Check 6 — public page uses the static replay path: CONFIRMED

Reproduced all three steps. (i) Raw-HTML grep of `https://softmax.com/liars-dice` finds no
iframe — the page is client-rendered, exactly as VERIFY.md recorded, so no false negative.
(ii) The SSR payload does contain `playlist":[{"episodeId":"c3c77e26-…` with the round-2
replay URL `880929b7-….replay` — featured match present (`liars-dice.r2.e1`, daveey vs
daveey-1). (iii) `POST /coworlds/replays/session` returns `ready: true` and `viewer_url` =
`…/v2/coworlds/replays/static/cow_0fa24212-…/sha256%3Af370529105d16354…/index.html?replay=…`
— the static route, the sha matching `STATE.coworld.manifest_sha` exactly, and no
`/client/replay` anywhere. VERIFY.md named its sources correctly.

## Check 7 — certification declared the static bundle: CONFIRMED

Read the committed `runs/2026-08-26-liars-dice/release-result.json` (commit `83901cd`,
phase-40's artifact, as the prompt requires — not `/tmp`): `.certify.replay_liveness` =
`Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not
required)`. Contains the required prefix verbatim. Release run 33018791088 in
`Metta-AI/cogame-liars-dice` re-checked: `conclusion: success`.

## Check 8 — viewer executed, then judged: CONFIRMED

- **Execution**: viewer-check run 33020556574 re-checked via `gh run view`: `conclusion:
  success`, created `22:43:06Z` (after the 22:43:04Z dispatch — the find-the-new-run rule was
  followed; the next-most-recent run is 20:59Z, so no race). Artifacts committed at
  `runs/2026-08-26-liars-dice/viewer-check/` in commit `439704a`.
- **8.1 loaded**: `viewer-smoke.json` line 2: `"loaded": true`, first frame at 2428 ms, via
  the `coworld-replay` bridge (`"bridge": ["loading","ready"]`, `bridge_ready: true`,
  `bridge_error: []`, `failure: null`). Not an asset-200 inference — the bundle actually
  signalled ready. Holds.
- **8.2 advancement**: the three scrub readouts in the artifact are `DEAL 0` (0 %),
  `DEAL 0 / 8` (50 %), `DEAL 8 / 8 · FINAL` (100 %) — three distinct strings. Holds. (0 % vs
  50 % differ only by the ` / 8` suffix, i.e. both are pre-deal-1 states, but the SPEC's test
  is that the clock *text* differs, and the 100 % readout plus the endcard prove the replay
  runs to its end.)
- **8.3 judgment paragraph**: present in VERIFY.md and — my own independent read of
  `viewer-smoke.png` below — accurate.

**Judge's independent spectator read of viewer-smoke.png**: The frame is legible and it is
unmistakably a finished game of Liar's Dice in the starter's chrome. Transport strip across
the top: title **LIAR'S DICE** left, clock **DEAL 8 / 8 · FINAL** centred, **REPLAY · « LOG**
right. Scorebug strip beneath it: `daveey +3`, `daveey-1 0`, `Widget −4`, `Bolt +1` with pip
meters — exactly `results.points [3, 0, -4, 1]` in seat order. Four robot avatars around an
elliptical table, each with five face-up dice (the reveal state) and name/points labels;
speech bubbles carry the last deal's table talk verbatim from the replay's `say` fields ("Not
seeing many fives out there—must be hiding somewhere!" top; "Widget's pattern finally
breaks—fives are scarce and 3 x 5 is a stretch." left); a private-notes card at lower left
shows daveey's final-challenge reasoning (truncated with an ellipsis at its bottom line).
Centred endcard: **FINAL — 8 DEALS / daveey TAKES THE TABLE** with a four-row ranked table
whose SCORE/W/L/BLUFF/CHALLENGE columns I reconciled cell-by-cell against the replay's
`results` (`scores [0.6875,0.5,0.25,0.5625]`, `wins [4,1,1,2]`, `losses [1,1,5,1]`,
`bluffRate [0,0,0.5,0]`; challenge rates 50/14/17/25 % re-derive from
`challenges/(bids+challenges)`). Bottom: scrubber with play button, coloured per-event tick
marks, counter **39 / 39** — the replay has exactly 39 events. It advances (the three clock
readouts), it is not empty or frozen, and the chrome — transport strip, scrubber with event
track, scorebug, endcard — is the starter's product, not a rewrite sharing ids.

## Non-blocking observations

- Check 1's narrative sentence ("both after the fillers were registered at 22:22:44Z / before
  round 1 was created at 22:22:00.93Z") is internally garbled: the two timestamps it cites
  run the wrong way. The verdict is nevertheless correct — proven here via round 1's own
  episode request seating both fillers at 22:22:01Z — but a verifier should not leave an
  ordering claim resting on a batch-write log timestamp.
- `scorebug: ""` / `feed_lines: 0` in viewer-smoke.json are empty DOM readouts because this
  starter paints scorebug and feed inside the canvas; the canvas-text counter (2338 draws, 0
  outside) and the screenshot supply the evidence. The verifier documented this correctly as
  an instrumentation gap. A future viewer-smoke probe that reads the canvas-painted scorebug
  would close it.
- The two legibility notes the verifier flagged for the coordinator stand as observed: (i) 84
  of 2338 canvas-text draws ellipsized in the notes panel (long notes cut, not wrapped);
  (ii) filler seats labelled by table alias (`Widget`/`Bolt`) rather than `Baseline` in the
  scorebug/endcard, so the picture alone doesn't identify the baselines. Neither maps to a
  Definition-of-done item; both are phase-30-class legibility polish for a future round.

## Verdict

All eight checks CONFIRMED: the pasted evidence supports each TRUE, no verdict contradicts
its fetched output once the check-1 ordering was independently settled, and every claim I
re-fetched reproduced exactly. The definition of done is proven.

BLOCKING: 0
