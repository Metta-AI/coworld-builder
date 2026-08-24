blocking: 0

# Phase 60 verdict — matrix-games
Run: `2026-08-24-matrix-games` · cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531 v0.1.1
Checklist: SPEC §Definition of done (8 items) · VERIFY.md read after forming spot-check plan; independent re-fetches performed for items 1, 2, 3, 4, 6, 8 (run conclusion) before judging.

## Per-item

**1. ≥2 completed rounds after fillers set — VERIFIED.**
VERIFY.md pastes the fetched `GET /rounds` bare array (command + full JSON) showing rounds 2 and 3 `completed`, round 1 `failed` with the documented pre-filler error quoted verbatim. My re-fetch returns the same statuses (a new round 4 is `pending`, which changes nothing). The post-filler claim is evidenced, not asserted: the live filler-policies fetch plus both episodes seating six `is_filler: true` seats, corroborated by log.md's phase-50 sequence (round 1 failed pre-fillers; round 2 was the post-filler trigger).

**2. Both champions ranked, fillers absent/Baseline — VERIFIED.**
VERIFY.md pastes the fetched leaderboard (command + full JSON): exactly two rows, `daveey-1`/`matrix-games-brinkman:v2` rank 1 and `daveey`/`matrix-games-reader:v2` rank 2, no filler rows. My re-fetch matches row for row (ranks, policy labels, rounds_played=2).

**3. Latest round's episode request completed with replay + participants — VERIFIED.**
VERIFY.md pastes the fetched episode-request for round 3 (`ereq_00d096dc…`, `status: "completed"`, non-null `replay_url`, eight participants with champions at seats 0/1 `is_filler: false` and champion policy_version_ids matched to STATE). My re-fetch confirms the id, status, and a replay_url byte-identical to `STATE.verify.replay`.

**4. Replay bytes valid and show the game — VERIFIED.**
VERIFY.md fetches the S3 bytes and shows strict-UTF-8 validation twice (`jq -e` + python strict decode), `protocol == "matrix.replay.v1"` (pinned in design.md §The replay file and in the repo's replays.nim/test, both quoted), `results.reason == "complete"` — the strong branch, so design.md's declared-acceptable `deadline` clause (line 284) is not needed. The `k`/`source` vocabulary deviation is real (design.md §Event vocabulary, line 547) and the prompt's literal jq is shown returning 0 before the adapted form. My re-fetch reproduces: 264160 bytes, protocol/reason/ending identical, champion seats 24/24 orders `source=llm`, 0 fallback. The pasted `say` excerpts are non-trivial, game-specific decisions ("paper beats rock", opponents named by alias), not boilerplate.

**5. Hosted game log clean — VERIFIED.**
VERIFY.md fetches the log with the elevated header (HTTP 200, 52691 bytes), documents the byte-repr decode step per the playbook, and shows the exact four-pattern grep returning CLEAN, plus positive evidence the LLM path ran (801/637-char prompts, bedrock transport, 24 llm orders). Round 2's log grepped clean too. Command + output present; no exception invoked. Not re-fetched (elevated artifact), but the evidence is fetched output, not inference.

**6. Public page static replay path — VERIFIED.**
The raw-HTML grep's empty result is recorded as a documented deviation (client-rendered page), and the fallback sources carry fetched evidence: the SSR `state.playlist[0]` shows a featured match (round 3 episode 1, replayUrl identical to check 3's), and `POST /coworlds/replays/session` returns the static route. My re-fetch of the session POST returns the identical `viewer_url`: `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with `<sha>` = STATE `manifest_sha` (URL-encoded) and `ready: true`; the string `/client/replay` does not appear.

**7. Certification declared static bundle — VERIFIED.**
Read from the committed artifact as required: `runs/2026-08-24-matrix-games/release-result.json` line 11, `certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"` — contains the required substring exactly. I read the same file and confirm.

**8. Viewer executed + spectator judgment — VERIFIED.**
(a) Loaded: the committed `viewer-smoke.json` carries `loaded: true`, `data_replay_loaded: "true"`, bridge `["loading","ready"]`, `bridge_error: []`, `failure: null` — not an all-200-assets inference. The dispatch→run correlation is evidenced (dispatch 19:43:51Z, run 32769835228 created 19:43:53Z, next-newest 17:01Z); I re-checked the run: `conclusion: success`. (b) Advances: the three scrub readouts differ (BEAT 1/TICK 1 → BEAT 7/TICK 317 → BEAT 12/TICK 599), present in the committed json. (c) Judgment: I viewed `viewer-smoke.png` myself — it is a legible full broadcast frame showing the game: eight-plate scorebug whose scores/enc counts match `results.scores`/`perSeatInteractions` exactly, spelled-out clock "BEAT 12 / 12 / TICK 599 OF 600", the 3×3 rock/paper/scissors payoff matrix panel, token legend, six feed rows matching the replay's event tail (DUNE/GORSE/FERN/CEDAR pickups), the endcard "BASELINE (2) TAKES THE YARD" with a results table that is `results` verbatim, and the starter's transport strip + scrubber + convention curves — paintbot/coworld-ctf-lineage chrome, as claimed. The verifier's paragraph describes what the pixels show and honestly flags the endcard scrim; motion is established by the readouts, not the single frame.

## Notes (non-blocking)
- A round 4 is now `pending` on the ladder; it postdates VERIFY.md and does not affect any item.
- Minor timestamp looseness: log.md's phase-50 batch entry is stamped 19:20:35Z while round 2 was created 19:19:32Z; the entry's internal ordering (fillers → trigger → round 2 pending) and the six Baseline seats in both episodes settle the post-filler question regardless.

## Summary
| # | item | verdict |
|---|---|---|
| 1 | ≥2 completed post-filler rounds | VERIFIED |
| 2 | champions ranked, fillers absent | VERIFIED |
| 3 | episode request completed + replay + participants | VERIFIED |
| 4 | replay bytes valid, complete, 24/24 LLM | VERIFIED |
| 5 | hosted log clean | VERIFIED |
| 6 | featured match + static iframe src | VERIFIED |
| 7 | liveness-skipped in committed release-result.json | VERIFIED |
| 8 | viewer executed, advances, judgment supported by png | VERIFIED |

BLOCKING: 0
