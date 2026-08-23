blocking: 0

# 60 verdict — escrow
Head: 0ae9b40   Checklist: docs/SPEC.md §Definition of done (phase 60, all fetched, never assumed) — 8 items   Independent read written before reading any fixer/verifier self-report beyond VERIFY.md itself: yes (VERIFY.md is the artifact under adjudication; the phase-30 review/fix files were not read)

Adjudicated: `runs/2026-08-23-escrow/VERIFY.md` (attempt 3, fetch window 18:27–18:53Z, v0.1.3 / v4 policies).
Judge re-fetches were made 2026-08-23 ~18:58–19:05Z. One post-window event explains all live drift:
**round 14 completed at 18:56:27Z**, after VERIFY.md was written.

## Standing blocking findings

None.

## Refuted

None to refute — no reviewer findings were supplied for this phase; the adjudication is of VERIFY.md directly.

## Checklist pass (independent)

Every item has fetched evidence pasted inline in VERIFY.md: command + output excerpt + explicit
per-item verdict. No item is an evidence-free assertion. Item 7's use of the committed
`release-result.json` instead of a fresh fetch is exactly what the checklist prescribes
("read from the committed `runs/<run>/release-result.json`").

| item | status | evidence (mine, independent) |
|---|---|---|
| 1. ≥2 completed rounds after fillers set | TRUE | Re-fetched `/rounds?league_id=league_cc074076…`: rounds 2–13 all `completed` (now also 14), round 1 `failed` with the exact error VERIFY quotes ("Temporal RoundWorkflow failed before settling the round."), no `discarded`. Rounds 12 (`round_3de0946c…`, 18:26:27Z) and 13 (`round_292146e4…`, 18:41:27Z) carry both v4 champion UUIDs `5153a6f7…`/`228bbef6…` in `entrant_policy_version_ids` — byte-identical to VERIFY's table. Fillers were set before the first trigger (phase 50) and re-set to v4 per log.md line 158 (`18:26:37Z … filler-policies updated to v4 … trigger-round issued`); ≥2 completed rounds follow under either reading. |
| 2. Both champions ranked, fillers absent/Baseline | TRUE | Re-fetched leaderboard `div_a8171f6e…`: daveey rank 1 `escrow-drafter:v4` (13 rounds), daveey-1 rank 2 `escrow-swapper:v4` (13 rounds); `escrow-trader`/`escrow-hoarder` absent from every row. VERIFY's snapshot (daveey-1 rank 4, 12 rounds each) differs only by round 14's Elo/round-count update — both champions RANKED in both snapshots. richard/relh are third-party players with their own `co-gas-escrow-baseline-*` policies, not this run's fillers (per coordinator context, not a violation). |
| 3. Latest round's ereq completed with replay | TRUE | Re-fetched `ereq_78850370-c03e-4fc0-b663-a59bb5d73f93`: `status: completed`, `replay_url: …/replays/1839e1b7-3f2c-418c-9eeb-28c19fd6b5dd.replay`, seat 1 = escrow-drafter v4 / daveey, seat 2 = escrow-swapper v4 / daveey-1, seats 0/3 = relh/richard baselines, all `is_filler: false`. Identical to VERIFY. |
| 4. Replay bytes valid, champions do the thing | TRUE | Re-fetched the S3 replay: 90 898 bytes (same size), `jq -e` clean strict JSON, `protocol == "escrow.replay.v1"` (matches the protocol declared in cogame-escrow `src/escrow/server.nim`, `replay-viewer/escrow_replay.nim`, `tests/test_sim.nim`), `results.reason == "complete"`. Recounted champion scripted moves myself: seats 1 and 2 = **0 scripted of 32** (all four seats 16/16 non-scripted). Event census identical (27 sign / 27 settle / 31 offer / 2 reject / 4 expire). `results` identical (`scores [162,224,184,214]`, `heartsMinted 704`). Move `say`/`text` content is substantive per-turn reasoning, not fallback boilerplate. |
| 5. Hosted game log clean | TRUE | Re-fetched `artifacts/logs` for the same ereq (elevated header), 155 956 raw bytes, decoded the `b'…'` container reprs myself (155 279 bytes): `falling back` 0, `LLM provider is unavailable` 0, `cut off at max_tokens` 0, `rejected` 0. Six benign `attempt 0 failed` retries, matching VERIFY's list. No platform exception needed. |
| 6. Public page uses the static replay path | TRUE | Re-POSTed `/coworlds/replays/session` for cow_9b73db59 + the round-13 replay: `viewer_url` byte-identical to VERIFY's — `…/v2/coworlds/replays/static/cow_9b73db59-4be9-4a59-9e56-5eed9151a871/sha256%3Af5e3e157…/index.html?replay=…`, `ready: true`, no `/client/replay`. Re-fetched `https://softmax.com/escrow`: featured match present, `coworldId cow_9b73db59…`, `coworldVersion 0.1.3`; the featured episode is now `escrow.r14.e1` (round 14, post-VERIFY) — rotation, not a contradiction; zero occurrences of `/client/replay` in the page. |
| 7. Certification declared static bundle | TRUE | Read committed `runs/2026-08-23-escrow/release-result.json` myself: `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`; `.version 0.1.3`, `.cow_id cow_9b73db59…`, `.manifest_sha sha256:f5e3e157…`, `.ok true`, `.canonical true`, `.certify.output_tail` ends with the same line and `Transcript: coworld-executable (10 steps passed)`. |
| 8. Viewer executed + spectator judgment | TRUE | Confirmed via `gh run view 32659327500`: workflow `viewer-check`, created 2026-08-23T18:50:37Z, conclusion **success**. Committed `viewer-check/round13-32659327500/viewer-smoke.json`: `loaded: true`, `data_replay_loaded: "true"`, bridge `["loading","ready"]`, `failure: null`; three scrub clocks all differ (`TURN 0` / `TURN 0 / 16 · WAITING ON 4` / `TURN 16 / 16 · FINAL`) — (a) and (b) hold. I opened `viewer-smoke.png` myself: it shows `TURN 16 / 16 · FINAL`, the four-seat scorebug (relh 162 / daveey 224 / daveey-1 184 / richard 214 with profile+goods readouts), the endcard `FINAL — 16 TURNS · 704 HEARTS MINTED`, `daveey — MOST HEARTS AT HORIZON`, and a ranked table whose every figure (hearts / fills 12·14·26·16 / signed 9·14·19·12 / forfeits 0) reconciles exactly against the replay `.results` I re-fetched, plus the scrubber and a `225 / 225` event counter. The judgment paragraph in VERIFY.md is legible, shows the game, and is faithful to the pixels — (c) holds. |

Cross-check of the identifiers named in the brief: `cow_9b73db59-4be9-4a59-9e56-5eed9151a871`,
`sha256:f5e3e157…c64c40`, version `0.1.3`, `escrow-drafter:v4`/`escrow-swapper:v4`, the round-13
replay URL, and the viewer readouts agree across VERIFY checks 3/4/6/7/8, `STATE.json`
(`.coworld` block, `release_run_id 32657361152`), `release-result.json`, `log.md` lines 157–158,
and the committed viewer-check artifacts. No internal contradiction found.

Committed artifacts confirmed present in the run directory: `VERIFY.md`, `release-result.json`,
`viewer-check/round13-32659327500/{viewer-smoke.json, viewer-smoke.png, smoke-stdout.txt,
smoke-stderr.txt}` (committed in `433864d`).

## Verifier report audit

| VERIFY claim | I verified | agrees |
|---|---|---|
| Rounds table incl. round-1 failure text, v4 scoping to rounds 12+13 | re-fetched rounds list | yes (plus new round 14) |
| Leaderboard: both champions ranked v4, fillers absent | re-fetched leaderboard | yes (ranks shifted by round 14; still satisfies item 2) |
| ereq_78850370 completed, participants, replay_url | re-fetched | yes, identical |
| Replay: strict JSON, escrow.replay.v1, complete, 0/32 champion scripted, 27/27 sign/settle, results | re-fetched bytes, recounted | yes, byte-identical metrics |
| Log: 0/0/0/0 on the four patterns after b'…' decode | re-fetched + re-decoded independently | yes |
| session route static viewer_url, ready:true | re-POSTed | yes, byte-identical URL |
| release-result.json liveness line + provenance fields | read committed file | yes |
| viewer-check 32659327500 success, loaded:true, 3 differing clocks, png content | gh run view + read committed json + viewed png | yes |

## Non-blocking observations

- `release-result.json` records `hosted_certification: "certifying"` (not a terminal "certified"). Item 7 as written requires only the replay-liveness line from the committed file, which is present; hosted-certification state is phase 40's done-when, not part of this checklist, and the coworld is live-canonical (`canonical: true` both in the file and on the coworlds list). Noted, not counted.
- The 50 % scrub clock read `TURN 0 / 16 · WAITING ON 4` rather than a mid-episode turn. The checklist requires only that the three readouts differ, which they do, and the 100 % readout proves advancement; the verifier disclosed this rather than hiding it. Noted, not counted.
- The live `softmax.com/escrow` featured match has rotated to `escrow.r14.e1` since VERIFY's fetch window (round 14 completed 18:56:27Z). Same coworld id and version; not a contradiction of check 6's evidence at its timestamp.

BLOCKING: 0
