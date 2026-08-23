blocking: 0

# Phase 60 verify verdict — gridlock

Run: `2026-08-23-gridlock` · judge fresh-context adjudication of `VERIFY.md` (verifier claimed 8/8 all-true)
Checklist: `docs/SPEC.md` §Definition of done · procedure: `prompts/60-verify.md`
Independent read: SPEC + phase prompt + VERIFY.md's raw evidence + the committed
`viewer-check/viewer-smoke.{json,png}` were read, and every spot-checkable claim was re-fetched
live from this sandbox at ~15:47–15:52Z (2026-08-23), **before** any conclusion was adopted from
the verifier's verdicts. Declared contamination: none beyond VERIFY.md itself, which is the
document under adjudication.

Verdict: **all eight checks VERIFIED at head. Blocking: 0.** Two evidence-quality notes recorded
below (one factual error in VERIFY.md's check-1 prose, corrected by my own fetch; one rendered-HUD
defect in check 8, ruled non-blocking with reasons).

---

## 1. ≥2 completed rounds after fillers set — VERIFIED

Re-fetched `GET /rounds?league_id=league_4c0f039e-…` myself at ~15:48Z: rounds 1 and 2 both
`status: "completed"`, `error: null`, completed 15:21:50.690956Z and 15:36:51.388422Z (round 3 was
`pending` at my fetch and finished 15:51:46Z per the live page — the ladder continues, which only
strengthens the check). Fillers set at 15:19:01Z
(`log.md:55 "50 filler-policies POST 200 (dispatcher+beeline only, neither champion)"`), before
both completions. I additionally fetched **round 1's** episode request
(`ereq_76649802-101c-48d0-8d20-7a926a13761f`, not in VERIFY.md): its participants seat both
champions (`is_filler: false`) **and both registered fillers** — `gridlock-beeline` and
`gridlock-dispatcher`, both `is_filler: true` — so the fillers were demonstrably in effect for
every counted round. 0 failed, 0 discarded.

**Correction to VERIFY.md's prose (non-blocking):** VERIFY.md line 36–38 says fillers were
registered "**before** round 1 was created (15:17:41Z)". That is backwards — 15:19:01Z is *after*
the round object's 15:17:41Z `created_at` (the ladder pre-creates a pending round when settings
enable). The claim the checklist actually makes — the counted rounds *completed* after the fillers
were set, with fillers seated — is true, on evidence I fetched myself (round 1 completed
15:21:50Z > 15:19:01Z; fillers seated in round 1's episode). A wrong parenthetical in the
narrative, not a wrong verdict.

## 2. Both champions ranked, fillers absent/Baseline — VERIFIED

Re-fetched `GET /divisions/div_349162e2-…/leaderboard` myself (bare array, 2 rows):
`1 daveey gridlock-flowwright:v1 1030.5304984710244 2 2.0` and
`2 daveey-1 gridlock-backstreet:v1 969.4695015289755 2 0.0` — byte-identical to VERIFY.md's
paste. Both champions present, `rounds_played = 2 ≥ 1`; no filler rows at all (the permitted
"absent" disposition).

## 3. Latest round's episode request completed with replay, participants correct — VERIFIED

Re-fetched `GET /episode-requests/ereq_49c11f68-c5df-4791-8a45-ac1743ccf6d2` myself:
`status: "completed"`, `replay_url:
https://softmax-public.s3.amazonaws.com/replays/b0474583-f10a-4a2c-b062-fc65175d6d64.replay`,
seat 0 `gridlock-flowwright`/`daveey`/`is_filler:false`, seat 1
`gridlock-backstreet`/`daveey-1`/`is_filler:false`, seats 2–3 `gridlock-beeline`/`is_filler:true`.
The verifier's explanation for `player_name: daveey` on filler seats (uploader ownership) is
consistent with the `is_filler` flags and with the replay's own
`names: ["daveey","daveey-1","Baseline","Baseline (2)"]`, which I parsed from the bytes myself.

## 4. Replay bytes valid, show the game — VERIFIED

Re-fetched the S3 bytes myself: 360837 bytes; `jq -e .` strict parse → **ok**;
`protocol == "gridlock.replay.v1"` (pinned at `design.md:885`, which I read);
`results.reason == "complete"`, `end_rule == "full_time"` (no `deadline` exception needed).
Champion provenance re-computed from my own copy: seats 0 and 1 have 20/20 `plan` events with
`source: "llm"`, seats 2–3 20/20 `scripted`; `turns_llm [20,20,0,0]`, `fallback_turns [0,0,0,0]`,
zero `fallback==true` events; 38 of 40 champion plan notes textually distinct, referencing live
state (jam_index, stalled_pct, rival totals). Fallbacks are 0 of 40 — "not all fallbacks" holds
maximally. The verifier's note that gridlock's decision type is `plan` (so the phase prompt's
literal `type=="decision"` filter returns 0) is correct and honestly recorded, with both filters
shown.

## 5. Hosted game log clean — VERIFIED

Re-fetched `/episode-requests/ereq_49c11f68…/artifacts/logs` with the elevated header myself:
83392 bytes (same size as VERIFY.md recorded); my own
`grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'` → **CLEAN**.
The verifier's second-approach un-escaped re-grep (0 hits over 190 decoded lines, all four
containers present) is corroborated by the game-container excerpt showing 4/4 seats registered
and `episode complete: reason=complete scores=[188.0,184.0,186.0,186.0]`.

## 6. Public page uses the static replay path — VERIFIED

Re-verified both legs myself. (i) Raw `https://softmax.com/gridlock` HTML has no `<iframe>` — the
verifier's "client-rendered, fall back" call is correct, and the fallback taken is recorded, as
the prompt requires. (ii) The SSR payload's `playlist[0]` at my fetch is a **featured match**
(now `gridlock.r3.e1`, finished 15:51:46Z — the round after the verifier's snapshot; same
division, same two champions ranked first/second). (iii) I re-ran the
`POST /coworlds/replays/session` call myself with the same body and got the **identical**
`viewer_url`:
`…/v2/coworlds/replays/static/cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6/sha256%3A38c6a5c2…/index.html?replay=<s3 url>&v=2`,
`ready: true` — the static route, with `<sha>` decoding to exactly `STATE.coworld.manifest_sha`,
which also matches the `/coworlds` row I fetched (`canonical: true`, `manifest_hash` identical).
No `/client/replay` pod URL anywhere.

## 7. Certification declared the static bundle — VERIFIED

Read the committed `runs/2026-08-23-gridlock/release-result.json` myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` and `.certify.ok` = `true`. Committed in `cb202b3`
(verified via `git log -- <path>`). Source correctly the committed copy, not `/tmp`.

## 8. Spectator judgment — viewer executed and judged — VERIFIED

- CI fact re-checked myself: `gh run view 32649388472 -R Metta-AI/coworld-builder` →
  `{"conclusion":"success","status":"completed","createdAt":"2026-08-23T15:42:22Z","workflowName":"viewer-check"}`.
- Artifacts committed under `runs/2026-08-23-gridlock/viewer-check/` and read myself:
  `viewer-smoke.json` has `loaded: true`, signals
  `data_replay_loaded:"true"`, `bridge:["loading","ready","ready"]`, `bridge_ready:true`,
  `bridge_error:[]`, `failure: null` — condition (a) holds via **both** accepted signals.
- Three scrub clock readouts, from the artifact itself: `03:20 TURN 0/20` → `01:37 TURN 10/20` →
  `00:00 TURN 19/20` — all three differ; condition (b) holds.
- I viewed `viewer-smoke.png` myself: a drawn frame, not a spinner — end card "Saffron wins — 188
  parcels", four-row score table whose every number matches `results.delivered [188,184,186,186]`,
  `mean_trip_seconds` and `backlog_final` from the replay bytes I fetched; 6 feed lines matching
  the turn-19 plan events; depot chips Saffron 188 / Copper 184 / Cobalt 186 / Verde 186 all
  correct; JAM 27, transport bar, minimap present. The judgment paragraph is written, legible,
  and reconciled — condition (c) holds.

**Ruling on the disclosed advisory (the corner-plate transposition):** confirmed by my own read
of the png — the top-left plate pairs `Baseline · Cobalt` with **184** and the top-right pairs
`daveey-1 · Copper` with **186**, i.e. the two middle seats' totals are swapped relative to
`results.delivered` ([188,184,186,186]). I weighed whether this falsifies item 8 and conclude it
does **not**: the two binding conditions of `prompts/60-verify.md` (loaded:true; three differing
clocks) are untouched, and SPEC's condition (c) — "legible, and it shows the game" — survives
because the winner, the full score table, the depot chips and the feed in the *same frame* all
carry the correct values; the defect is confined to two of four corner plates, is contradicted by
three correct surfaces in view, and was disclosed rather than glossed. It is a real HUD indexing
bug (a spectator reading only the plates would mis-order Copper and Cobalt — 2nd vs 3rd place)
and belongs in a phase-30-style follow-up for a later version, but no definition-of-done item
requires every HUD element to be correct, and the frame as a whole remains a legible account of
the match. Non-blocking observation, not a FALSE.

---

## Refuted

None. Every check's verdict survived re-fetch. The single factual error found (check 1's
"before round 1 was created" parenthetical) is in the narrative, not the verdict, and the
underlying criterion was re-established from primary evidence.

## Verifier report audit

| check | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | TRUE, 2 completed post-filler | re-fetched rounds + round-1 episode participants (fillers seated) | yes (prose error noted) |
| 2 | TRUE, 2 rows, fillers absent | re-fetched leaderboard, byte-identical | yes |
| 3 | TRUE, completed + replay_url + participants | re-fetched ereq_49c11f68 | yes |
| 4 | TRUE, strict JSON, 0 fallbacks | re-fetched bytes, re-ran parse + provenance filters | yes |
| 5 | TRUE, CLEAN | re-fetched log (83392 B), re-ran grep → CLEAN | yes |
| 6 | TRUE, static route, featured match | re-ran session POST (identical URL), re-read SSR playlist | yes |
| 7 | TRUE, committed artifact | read committed file + git log | yes |
| 8 | TRUE, loaded + 3 clocks + judgment | gh run view success; read json + png myself | yes |

## Non-blocking observations

- [viewer-hud] Corner name plates transpose Cobalt/Copper delivered totals (184↔186) at the final
  frame; end card, score table, depot chips and feed are correct. Fix the plate score indexing in
  a later version.
- [verify-prose] VERIFY.md check 1 says fillers were set "before round 1 was created (15:17:41Z)";
  the round object predates the filler POST (15:19:01Z). Immaterial: round 1 completed after, with
  fillers seated in its episode.

BLOCKING: 0
