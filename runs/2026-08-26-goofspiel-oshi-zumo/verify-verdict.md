blocking: 0

# Phase-60 verdict — goofspiel-oshi-zumo

Run: `2026-08-26-goofspiel-oshi-zumo` · coworld `cow_649ab26c-c3a7-4755-8997-a909c953ef01` v0.1.2
Checklist: `prompts/60-verify.md` §The eight checks / `docs/SPEC.md` §Definition of done
Independent read written before reading VERIFY.md: **yes** — every check below was re-fetched
live (rounds, leaderboard, episode request, replay bytes, hosted log, SSR page + replays/session,
committed release-result.json, viewer-check run + committed viewer-smoke.json/png, which I viewed
myself) before VERIFY.md was opened. VERIFY.md was then audited against those independent fetches.

## Check 1 — ≥2 completed rounds after fillers were set: **CONFIRMED**

My fetch of `GET /rounds?league_id=league_af4bfc41…` returns five rounds: round 5 pending,
rounds 4/3/2 `completed`, round 1 `failed` with error
`Temporal RoundWorkflow failed before settling the round.` — quoted verbatim in VERIFY.md as the
checklist requires. Fillers were POSTed at 2026-08-26T23:18:30Z (`log.md` line 51); my re-fetch of
`GET /leagues/$L/filler-policies` confirms `goofspiel-oshi-zumo-match:v2` (56252dee) and
`hoard:v2` (13df4c2e) are registered now, matching STATE and neither being a champion version.
Rounds **3** (created 23:31:29.69Z, completed 23:35:46Z) and **4** (created 23:47:13.67Z, completed
23:51:29Z) are both unambiguously post-filler. VERIFY.md correctly *declines to count* round 2
(created 23:16:29Z, two minutes before the filler POST) rather than padding the count with it —
the conservative reading. Two counted completed rounds ≥ 2. Pasted evidence matches my fetches
byte-for-byte.

## Check 2 — both champions ranked, fillers absent/Baseline: **CONFIRMED**

My fetch of `GET /divisions/div_8ec54c0e…/leaderboard` (bare list):
```
1  daveey-1  goofspiel-oshi-zumo-reader:v2                   1049.20  3  4.0
2  relh      co-gas-goofspiel-oshi-zumo-match-relhalpha:v1   1000.0   1  1.0
3  richard   co-gas-goofspiel-oshi-zumo-match-richard:v1     1000.0   1  1.0
4  daveey    goofspiel-oshi-zumo-tempo:v2                     950.80  3  1.0
```
`daveey` and `daveey-1` both ranked with `rounds_played = 3 ≥ 1`. Neither filler policy
(`…-match:v2` / `…-hoard:v2`) appears on the board — fillers **absent**, which satisfies the
"absent or labelled Baseline" disjunction. The third-party rows do **not** falsify the check:
`relh` and `richard` are real entrants — their policy versions (230face9, bf26100e) are not in the
league's `filler_policy_versions` (re-fetched above), and the round-4 episode request marks both
`is_filler: false`. Their labels contain the substring "match" only because they self-named their
submissions; they are not this run's fillers. VERIFY.md documents exactly this, correctly.

## Check 3 — latest round's episode request completed with a replay: **CONFIRMED**

Latest completed round is 4 (`round_f572a6f4…`). The flat `GET /episode-requests?round_id=` is
405 on this deployment (I hit it myself; the playbook documents it); the nested
`GET /rounds/<id>/episode-requests` returns exactly one entry, `ereq_1e52db7f…`, `completed`.
My fetch of `GET /episode-requests/ereq_1e52db7f…`: `status == "completed"`, non-null
`replay_url` (`…/replays/da00ff5a….replay`), participants naming **daveey** (seat 1,
goofspiel-oshi-zumo-tempo v2) and **daveey-1** (seat 2, goofspiel-oshi-zumo-reader v2), plus the
two third parties, all with scores. No `Baseline (N)` seat exists because four real policies
filled the table — the checklist's "(fillers as `Baseline (N)`)" is conditional on fillers being
seated, and none were. Pasted evidence identical to my fetch.

## Check 4 — replay bytes valid and show the game: **CONFIRMED**

I downloaded the replay myself (18216 bytes): `jq -e` strict parse passes; `protocol` is
`gozu.replay.v1`, matching the design note §Replay bytes and the server source (the live manifest
declares only `player`/`global` protocols — I fetched `GET /coworlds/<cow>` and
`.manifest.game.protocols | keys == ["global","player"]` — so the design/source is the right
referent, and VERIFY.md checked the source at the release sha rather than asserting).
`results.reason == "complete"`, `ending == "prizes-exhausted"` — the design's `deadline`
concession was not needed. This game emits no `decision` event kind; provenance rides in each
`reveal`'s `scripted[]`/`fellBack[]` and `results.fallbacks[]` — VERIFY.md says so explicitly
rather than pasting a vacuous `0` for a generic filter, which is the honest reading. My own
tally over the 13 reveals: champion seats 1 and 2 are `scripted: false` in **13/13** rounds,
`fellBack: false` in 13/13, `results.fallbacks == [0,0,0,0]`, and both carry a non-empty,
game-referential `say` in all 13 reveals ("Dumping the lowest card on a small prize. Pace early,
strike late.", "Final round—Widget goes all in for the 10!"). Non-scripted, non-trivial, zero
fallbacks. Scores sum to 0; points sum to 91. TRUE on my own evidence.

## Check 5 — hosted game log is clean: **CONFIRMED**

I fetched `GET /episode-requests/ereq_1e52db7f…/artifacts/logs` (elevated) myself: 59879 raw
bytes; grep on the raw bytes for `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected` → **CLEAN**. I also reproduced VERIFY.md's decode path (the body is python
byte-string reprs under 4 container headers): 59391 decoded chars, **0 hits**, `"ok":true` × 26,
`"ok":false` × 0, `HTTP/1.1 200 OK` × 26 — identical numbers to VERIFY.md's paste, and the
26 = 13 rounds × 2 LLM seats reconciliation with `fallbacks:[0,0,0,0]` holds. No platform-outage
carve-out was needed.

## Check 6 — public page uses the static replay path: **CONFIRMED**

My raw-HTML grep of `https://softmax.com/goofspiel-oshi-zumo` finds no iframe (client-rendered,
as the playbook documents — recorded as unknown, not a false negative). The SSR payload's
`state.playlist[0]` (I extracted it myself) carries the featured match
`goofspiel-oshi-zumo.r4.e1` — the check-3 episode, replay `da00ff5a…`, matchup naming rank-1
`daveey-1` — so a featured match is present. My own
`POST /coworlds/replays/session {coworld_id, replay_uri}` returns
`viewer_url = …/v2/coworlds/replays/static/cow_649ab26c…/sha256%3A128417c7…/index.html?replay=<s3 url>&v=2`,
`ready: true`. The `<sha>` equals `manifest_hash` from `GET /coworlds/<cow>` (I fetched it:
`sha256:128417c7…` — match) and equals `STATE.coworld.manifest_sha`. Static route, ends
`/index.html`, no `/client/replay` pod URL anywhere. VERIFY.md states which source was used
(C, with B for the featured match), as required.

Transcription blemish, weighed and found non-blocking: the "for completeness" `/coworlds` list
paste in VERIFY.md shows a command (`jq -r '.entries[]|…'`) that cannot have produced the pasted
output against the live endpoint (which returns a bare array — I hit it; `.entries` errors), and
the pasted rows include a `name` key absent from the jq projection. The substantive content of
that paste (canonical:true, `featured_match` null platform-wide) is true — I verified it
independently — and the check's verdict rests on sources B and C, both verified. A command-line
transcription artifact in a supplementary fetch, not evidence that fails to prove the claim.

## Check 7 — certification declared the static bundle: **CONFIRMED**

The committed `runs/2026-08-26-goofspiel-oshi-zumo/release-result.json` exists in the tree; my own
`jq -r '.certify.replay_liveness'` on it returns
`Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`
— containing the required substring. VERIFY.md names its source (the committed phase-40 copy,
not `/tmp`, not a re-download), as the checklist demands.

## Check 8 — viewer executed, then judged: **CONFIRMED**

Run identity: I checked `gh run view 33025003314` myself — workflow `viewer-check`,
`createdAt 2026-08-26T23:56:14Z` (two seconds after the logged dispatch), `conclusion: success`.
The evidence is committed at `runs/…/viewer-check/` (all four files present). From the committed
`viewer-smoke.json`, read myself:
- `{"loaded":true,"ms":1455,…,"feed_lines":42}`; signals
  `{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}`;
  `failure: no failure`; the json's `url` is byte-identical to the check-6 `viewer_url`.
- Three scrub readouts, all different: 0% `GOOFSPIEL · ROUND 0 / 13`; 50% `GOOFSPIEL · ROUND 7 /
  13 · PRIZE 7`; 100% `GOOFSPIEL · ROUND 13 / 13 · FINAL`. The 50% frame reconciles with the
  replay: `config.prizeOrder[6] == 7`. The replay advances.
- `canvas_text: {total:1783, outside:0, ellipsized:0, never_inside:0}` — matches VERIFY.md's paste.

I viewed `viewer-smoke.png` myself. It shows what the judgment paragraph says it shows: GOZU
wordmark top-left, clock `GOOFSPIEL · ROUND 13 / 13 · FINAL` centred, REPLAY chip and «LOG toggle
top-right, a four-plate scorebug with player names over alias sub-labels (relh/RATCHET,
daveey/TINKER, daveey-1/WIDGET, richard/GIZMO), points and budget rules and final bid cards
(10/11/12/10 — numeric, never T/J/Q/K), the endcard `FINAL — 13 ROUNDS / daveey-1 TAKES IT /
COMPLETE — ALL 13 PRIZES AWARDED` with a standings table whose numbers (0.26/40.3/91/0 etc.) are
identical to `results.scores`/`points`/`spent`/`fallbacks` in the replay bytes, two say-band
quotes that are the exact strings of the last `reveal` event, and a transport strip with play
button, beat-marked scrubber and `28 / 28` counter (28 = 1 start + 13 prize + 13 reveal + 1 end —
the replay's event count). The endcard stops above the transport band; controls unobstructed.
The chrome is visibly the babel/parley-family Ink & Print furniture (wordmark/clock/chip band,
plate scorebug, modal endcard, beat scrubber), not a rewrite sharing only ids. All three limbs of
item 8 — loaded:true, differing clocks, a judgment paragraph written from the rendered evidence —
hold, and the paragraph's specific claims check out against the png and the replay JSON.
VERIFY.md's three legibility notes (collapsed feed default, endcard covering the final board at
100%, overbid path unexercised by this episode) are correctly framed as non-blocking.

## Non-blocking observations (mine, not counted)

- [evidence-hygiene] Two pastes in VERIFY.md show command/output mismatches that read as
  transcription artifacts: check 6's `/coworlds` list command (`.entries[]` against a bare-array
  endpoint, output containing a key outside the jq projection) and check 8's `gh run list --json
  databaseId,createdAt,status` output containing an `event` key not requested. In both cases the
  substantive facts verify independently and the load-bearing sources are elsewhere; neither
  falsifies a check.
- [naming] The replay's `policyNames` (and hence the scorebug plates) carry **player** names
  (`relh`, `daveey`, `daveey-1`, `richard`) rather than policy labels (`goofspiel-oshi-zumo-
  tempo:v2`, …). The design note's "policy display names, spectator-side" reads more naturally as
  the labels. Not a definition-of-done item — the two-name-space separation (alias vs. spectator
  identity) is intact and visible in the png — but worth a look before a future round.

## Summary

| # | check | verdict |
|---|---|---|
| 1 | ≥2 completed rounds post-filler | CONFIRMED (rounds 3, 4; round 1 error quoted; round 2 conservatively excluded) |
| 2 | both champions ranked, fillers absent | CONFIRMED (daveey-1 #1, daveey #4, both rp=3; relh/richard are real entrants, not fillers) |
| 3 | latest round ereq completed + replay | CONFIRMED (ereq_1e52db7f, replay da00ff5a) |
| 4 | replay bytes valid, champions playing | CONFIRMED (strict JSON, gozu.replay.v1, complete, 26/26 live LLM bids, 0 fallbacks) |
| 5 | hosted log clean | CONFIRMED (0 hits raw and decoded; 26/26 Bedrock 200) |
| 6 | static replay path + featured match | CONFIRMED (SSR playlist[0] + replays/session, static route on manifest_hash, ready:true) |
| 7 | cert declared static bundle | CONFIRMED (committed release-result.json, exact substring) |
| 8 | viewer executed and judged | CONFIRMED (run 33025003314 success; loaded:true; 3 differing clocks; png verified by this judge) |

Zero of the eight checks rest on assertion or inference where a fetch was possible; every pasted
readout I re-fetched matched. No blocking findings.

BLOCKING: 0
