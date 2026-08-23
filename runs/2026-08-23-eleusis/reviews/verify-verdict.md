blocking: 0

# verify verdict — eleusis (phase 60)
Head: coworld cow_39778f81-c2d7-4aab-9642-f0ef0f16990e v0.1.1 · league_0e95b506-422e-4339-9a9d-8c8a6ecdb4ea · div_1aa06f49-71bf-4e57-bd88-337261abec99
Checklist: docs/SPEC.md §Definition of done (items 1–8)
Independent read written before reading fixer/verifier self-assessments beyond VERIFY.md itself: yes — every API/page/replay/CI claim below was re-fetched or re-computed in this session (2026-08-23T20:56Z–21:00Z), not accepted from the verifier's pastes.

## Standing blocking findings

None. All eight checks re-verified independently at the current head.

## Item-by-item adjudication (adversarial re-check)

### 1. ≥2 completed rounds after fillers set — CONFIRMED TRUE
- Re-fetched `GET /rounds?league_id=league_0e95b506…&limit=20` live: rounds 2, 3, 4 `completed` (and a 5th, round 5, has since completed at 20:52:22Z — 4 completed total now). Round 1 `failed` with exactly the quoted error `"Temporal RoundWorkflow failed before settling the round."`, created 20:00:00.576Z.
- The exclusion of round 1 is legitimate and does not weaken the count: rounds 2–4 alone satisfy ≥2. That fillers were live is not inferred from timestamps alone — I re-fetched round 2's own episode request (`ereq_01c150e2…`, round_id = round 2's `round_9c4a1934…`) and it seats `eleusis-openbook`/`eleusis-hoarder` with `is_filler: true`; the two filler UUIDs `34609da6…`/`72102f0f…` appear in the rounds payload and match `STATE.policies.filler_version_ids` and neither is a champion UUID (`9c39d031…`/`1bc93007…`).
- The 75-minute bound was respected (second completion at +20 min per the polling appendix; timestamps in the appendix are consistent with the API's `completed_at` values).

### 2. Both champions ranked, fillers absent — CONFIRMED TRUE
- Re-fetched `GET /divisions/div_1aa06f49…/leaderboard` live: bare array, exactly two rows — rank 1 `daveey` / `eleusis-empiricist:v1` (rounds_played 4, wins 4) and rank 2 `daveey-1` / `eleusis-guarded:v1` (rounds_played 4, wins 0). No filler rows at all — the stronger branch of "absent or labelled Baseline". (Counts moved from 3→4 since VERIFY was written because round 5 completed; that is the ladder advancing, not a discrepancy.)

### 3. Latest round's episode request completed with replay — CONFIRMED TRUE
- Re-fetched `GET /episode-requests?round_id=round_d16b6602…` (round 4, the latest completed at verify time): one entry, `ereq_0622bf3b…`, `status: "completed"`, `replay_url` = the S3 URL VERIFY quotes. Participant detail re-fetched: seat 0 `eleusis-empiricist`/daveey `is_filler:false`, seat 1 `eleusis-guarded`/daveey-1 `is_filler:false`, seats 2–4 fillers `is_filler:true`. Participants named correctly.

### 4. Replay bytes valid, champions doing the thing — CONFIRMED TRUE
- Re-downloaded the replay from S3: 76 953 bytes, sha256 `e2b29533…` **identical** to the committed `runs/2026-08-23-eleusis/episode.replay.json` — the committed copy is the live bytes.
- Re-computed on the committed copy: strict JSON (jq parses), `protocol` = `eleusis.replay.v1` (matches design.md's declared replay payload), `results.reason` = `"complete"` (the primary legal value; design.md §End conditions declares `deadline` also acceptable, but no exception was needed).
- Re-computed decisions: 140 events of kind experiment/skip/answer; per-seat: seats 0 and 1 = 28 decisions each, `scripted: 0`; seats 2–4 = 28 each all scripted (they are the baselines). `fallback==true` count: **0**. The two verbatim champion events VERIFY quotes exist (round 2 seat 0 `RRRR pass`, seat 1 `BBBB fail`) with substantive multi-sentence hypothesis-driven reasoning — non-trivial, non-scripted content. `results.hoarded = [0,3,0,0,0]` confirmed.
- The verifier's handling of the prompt's literal `type=="decision"` jq (0 hits, explained, then re-counted on the real `kind` key) is honest and correct, not a substitution to hide a failure.

### 5. Hosted game log clean — CONFIRMED TRUE
- Re-fetched `/episode-requests/ereq_0622bf3b…/artifacts/logs` with the elevated header (HTTP 200, 122 865 bytes), independently decoded the python byte-string reprs per container, and grepped the decoded text: **0** matches for each of `falling back`, `LLM provider is unavailable`, `cut off at max_tokens`, `rejected`. Corroboration reproduced exactly: 56× `"ok":true`, 0× `"ok":false`, 56× `"status_code":200` in the bedrock-sidecar log. Container sizes match VERIFY's table (sidecar 115 027 chars, game 7 275).

### 6. Public page uses the static replay path — CONFIRMED TRUE
- Re-fetched `https://softmax.com/eleusis` (HTTP 200): no literal `<iframe src>` in raw HTML (as VERIFY recorded — unknown, not failure), but the SSR `state.playlist[0]` is present and is a **featured match** for this coworld — now `eleusis.r5.e1` (round 5, finished 20:52:18Z), daveey vs daveey-1, same `coworldId`/`divisionId`. The payload has advanced from round 4 (VERIFY's fetch) to round 5, confirming VERIFY's own observation that it tracks the ladder.
- Re-ran the `POST /coworlds/replays/session` call: `viewer_url` = `…/v2/coworlds/replays/static/cow_39778f81-c2d7-4aab-9642-f0ef0f16990e/sha256%3A8dd17e05…/index.html?replay=<s3 url>&v=2`, `ready: true`. Static route; not `/client/replay`. The cow_id matches STATE and the sha decodes to exactly `STATE.coworld.manifest_sha` = `release-result.json.manifest_sha` (`sha256:8dd17e050d7eeea2947ca6a0d255239e5eef43222d7b745f8e53b17a9aba4995`).

### 7. Certification declared the static bundle — CONFIRMED TRUE
- Read the committed `runs/2026-08-23-eleusis/release-result.json` myself: `certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` — contains the required substring — and the same line appears in `certify.output_tail` after `Certified dist/coworld_manifest.json … (10 steps passed)`. `ok:true`, `canonical:true`, `hosted_certification:"certified"`, `step_failed:null`, and `cow_id`/`manifest_sha` tie it to the item-6 iframe. The producing run `32662323162` ("Coworld release") re-checked via gh: conclusion `success`.

### 8. Viewer executed, replay advances, judgment — CONFIRMED TRUE
- Both cited CI runs re-checked via gh: 32665552865 (decisive) and 32665381318 both `viewer-check`, conclusion `success`, created 20:48:38Z / 20:45:17Z — i.e. dispatched during the verifier session as claimed, against the check-6 iframe URL (confirmed in `viewer-smoke.json.url`).
- Artifact integrity: I re-downloaded run 32665552865's `viewer-check` artifact; `viewer-smoke.json` and `viewer-smoke.png` sha256 **match the committed copies byte-for-byte**. The committed evidence is genuinely the decisive run's output, not a hand-picked or edited file.
- (a) `loaded: true` with the strong signal `data_replay_loaded: "true"` (not just the bridge), `failure: null`, no bridge errors. (b) The three scrub clocks genuinely differ: `ROUND 1 / 24 · 0 OF 5 IN` → `PREDICTION TEST 2 / 4 · 1 OF 5 ANSWERED` → `ROUND 24 / 24 · FINAL`. (c) I viewed `viewer-smoke.png` myself: it shows a fully rendered finished match — scorebug plates whose values match `results` (daveey $8.7/PUB 10/SEC 0/+$10.5 ↔ scores[0]=8.739, published[0]=10, hoarded[0]=0, credit[0]=10.5; daveey-1 $6.6/PUB 8/SEC 3/+$7.5 ↔ seat 1), endcard "THE RULE WAS — STARTS R — the first token is RED" ↔ `results.rule`, "CLOSEST: TINKER" ↔ `closest:3` (replay `names[3]` = "Tinker"), transport `268 / 268` ↔ `events|length` = 268, corkboard "91 PUBLISHED" ↔ disclose modes `{publish:89, duplicate:2, hoard:3}` (89+2 on board, 3 in the "SECRET · SPECTATORS ONLY · 3" drawer). The judgment paragraph is written from the artifacts and every number in it reconciles.
- The verifier's treatment of the first run (three identical clocks, would have been FALSE alone) as data with a root-cause analysis, followed by a re-dispatch within the retry budget, is correct procedure, and the decisive run stands on its own evidence.

## Refuted

None — no VERIFY claim was contradicted by re-fetching. Every number, id, sha, and quoted line reproduced.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1 ≥2 completed rounds after fillers | TRUE | live GET /rounds: rounds 2,3,4 (+5) completed; round 2 ereq seats `is_filler:true` |
| 2 champions ranked, fillers absent | TRUE | live GET leaderboard: exactly 2 rows, daveey + daveey-1, no fillers |
| 3 latest round ereq completed + replay | TRUE | live ereq_0622bf3b…: completed, replay_url, seats 0/1 champions |
| 4 replay valid, champions non-scripted | TRUE | S3 sha256 = committed copy; protocol/reason match; 56 champion decisions, 0 scripted, 0 fallback |
| 5 hosted log clean | TRUE | live artifacts/logs decoded: 0/0/0/0 pattern hits; 56/56 bedrock ok:true 200 |
| 6 static iframe path | TRUE | live session POST: `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=…`, ready:true; featured match in SSR payload |
| 7 cert skipped-static line | TRUE | committed release-result.json `certify.replay_liveness`; run 32662323162 success |
| 8 viewer renders + advances + judgment | TRUE | run 32665552865 success; artifact sha = committed; loaded:true, 3 differing clocks, screenshot reconciles with replay |

## Verifier report audit

| claim | verifier said | I verified | agrees |
|---|---|---|---|
| rounds 2–4 completed, r1 failed auto-fire | TRUE | live re-fetch, identical timestamps/error | yes |
| leaderboard 2 champion rows only | TRUE | live re-fetch | yes |
| ereq_0622bf3b completed, participants | TRUE | live re-fetch | yes |
| replay bytes = committed copy | committed at 76 953 B | sha256 identical to live S3 | yes |
| 140 decisions / 0 fallbacks / seats 0–1 unscripted | TRUE | re-computed on committed copy | yes |
| log CLEAN after repr-decode, 56 ok:true | TRUE | independent decode + grep | yes |
| iframe src static with matching cow/sha | TRUE | live session POST | yes |
| release-result liveness line | TRUE | read committed file; gh run success | yes |
| viewer-check 32665552865 evidence | TRUE | gh run success; artifact sha matches committed | yes |

## Non-blocking observations

1. VERIFY's three coordinator-facing observations (premature bridge `ready` in `static_replay.js`; stale `model=claude-sonnet-5` banner vs haiku-4-5 sidecar records; API shape drift for the playbook) are well-evidenced and correctly classified as non-blocking. The `ready`-before-first-frame one is worth a LEARNINGS entry: it made viewer-check attempt 1 photograph an unpainted shell and would show spectators a blank board for ~0.5–1.5 s.
2. `STATE.verify.rounds` records `["round_2","round_3","round_d16b6602…"]` — the first two are round *numbers* dressed as ids while the third is a real round id. Cosmetic inconsistency in STATE, not a checklist item.
3. Round 4 drew fillers as 3× `eleusis-openbook` (round 2 drew openbook+2×hoarder) — sampling with replacement from the filler pool; fine, but it means a given episode may not exercise both baselines.
4. The featured match on softmax.com has since advanced to round 5 (`eleusis.r5.e1`); VERIFY's round-4 snapshot was correct when taken.

BLOCKING: 0
