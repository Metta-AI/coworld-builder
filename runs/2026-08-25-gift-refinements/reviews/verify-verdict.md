blocking: 0

# verify verdict — gift-refinements (phase 60, verification round 2)

Head: coworld-builder d5026e6 · cogame-gift-refinements d874ebd55a7244a57baa711c92651eaf55c4b08a ·
coworld 0.1.2 `cow_e19d6eae-78b4-447d-878d-b856c435db87` ·
Checklist: `prompts/60-verify.md` / `docs/SPEC.md` §Definition of done ·
Independent read written before adjudicating: yes (checklist → design note → run artifacts →
STATE → VERIFY.md → live re-fetches). Judged 2026-08-26, fresh context. Every claim below was
re-fetched live by the judge, not accepted from VERIFY.md.

## Per-check adjudication

### 1. ≥2 completed rounds after the fillers were set — TRUE **SUSTAINED**
Re-fetched `GET /rounds?league_id=league_aa42c0da…&limit=30` live: 8 completed rounds (2–9),
round 1 `failed` with error verbatim `Temporal RoundWorkflow failed before settling the round.`,
round 10 `pending`. I independently extracted `round_config.entrant_attributions` per round:
rounds 2–6 carry mirror `81167874` (v2) + patron `b88073d9` (v2); round 7 carries mirror
`7377bf74` (**v3**) + patron `b88073d9` (**v2**); rounds 8 and 9 carry mirror `7377bf74` (v3) +
patron `d848d844` (v3). The exclusion table in VERIFY.md is therefore **evidenced by the API, not
asserted** — I reproduced it byte-for-byte from a fresh fetch. Fillers: live
`GET /leagues/…/filler-policies` returns exactly `reciprocator:v3 e9f53270` + `hoarder:v3 2c45167f`,
neither a champion id; registration at 03:46:48Z per log.md line 98; rounds 8 (created 04:00:44Z)
and 9 (created 04:15:44Z) are both after it. The verifier's rule (count only rounds carrying both
:v3 champion attributions, post-re-wire) is *stricter* than the checklist's literal rule and the
check passes under both readings. The jq-filter deviation (dual-shape guard vs the prompt's
`.entries[]`) is declared and immaterial — the live body was `{entries:…}` and yields 8 either way.

### 2. Both champions ranked — TRUE **SUSTAINED**
Re-fetched the division leaderboard live: exactly two rows —
`1 daveey gift-refinements-mirror:v3 1049.94 rp=8 wins=6.0` and
`2 daveey-1 gift-refinements-patron:v3 950.06 rp=8 wins=2.0`. Both `rounds_played ≥ 1`, labels
rolled to `:v3`, no filler rows at all ("fillers absent" satisfied on the absent branch).
Ownership cross-checked live via `/policy-versions`: mirror:v3 `7377bf74` → daveey, patron:v3
`d848d844` → daveey-1 — matches VERIFY.md's pasted table.

### 3. Latest round's episode request completed with a replay — TRUE **SUSTAINED**
Round 9 is the latest completed round (and the latest both-v3 round — no divergence between the
prompt's "latest" and the verifier's "pinned"). Live:
`GET /episode-requests?round_id=round_7e355346…` → one entry,
`ereq_f3e3a82c-ec2f-4610-b941-86f48bd6361c completed`. Detail: `status=completed`, `replay_url`
non-null (`…/c3935602-3bd8-41f3-aacc-7421ab7a18f5.replay`), participants pos 0 = mirror v3 daveey
`is_filler:false`, pos 1 = patron v3 daveey-1 `is_filler:false`, pos 2–5 fillers v3
`is_filler:true`. The `Baseline (N)` display strings live in the replay's `results.names`
(verified: `["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]`); the
API-shape note in VERIFY.md is accurate.

### 4. Replay bytes valid and show the game — TRUE **SUSTAINED**
I re-downloaded the replay (162 688 bytes, matching VERIFY.md) and recounted myself:
strict parse (`jq -e` ok; python `decode('utf-8','strict')` ok), `protocol
gift-refinements.replay.v1` present verbatim in the live 0.1.2 manifest
(`manifest_hash sha256:accb4520…` = STATE.coworld.manifest_sha), `results.reason == "complete"`,
`ending round_limit`. Order provenance recounted with my own jq:
champion seats (0,1) → **`llm=24`**, zero scripted/fallback/retry; all 72 orders → `llm=24
scripted=48` (the 48 scripted are the four filler seats, as they must be). Event census matches
(`gift=152 order=72 round=12 consume=12 defect=1 …`). The verifier's handling of the prompt's
literal filters (`.type=="decision"` / `.fallback==true` → 0 because this schema keys `.k` /
`.source`) is declared, correct, and the schema-correct count is the meaningful one. The order
table's content is non-trivial and game-specific (seat 1 running a committed gift chain with Cyr,
latencies 4.4–6.2 s). Round-8 corroboration re-verified live: `llm=23 retry=1`, zero
scripted/fallback. Champion authenticity holds; design.md's failure state does not occur.

### 5. Hosted game log clean — TRUE **SUSTAINED**
Re-fetched `…/artifacts/logs` with the elevated header (51 476 bytes, matching), decoded the
`b'…'` reprs myself, and grepped: `falling back` 0, `LLM provider is unavailable` 0,
`cut off at max_tokens` 0, `rejected` 0 — CLEAN on decoded and raw; also 0 on `parse_error`,
`throttl`, `429`, `"ok":false`, `Traceback`. Lobby line present verbatim:
`gift-refinements: lobby closed with 6/6 seats connected, 6 registered`; seats 0 and 1 register
`"kind":"llm"`; summary line `episode finished reason=complete … llmOrders=24 fallbacks=0`;
24 sidecar calls all `"ok":true,"status_code":200`, model haiku-4-5. No platform-wide exception
needed to be invoked. The round-8 caveat (one first-attempt `parse_error` whose retry succeeded)
is honestly disclosed, does not touch the pinned round, and I verified its replay shows
`retry=1` with no scripted degradation.

### 6. Public page uses the static replay path — TRUE **SUSTAINED**
Re-fetched `https://softmax.com/gift-refinements` live: zero `<iframe>` in raw HTML (client-
rendered — correctly treated as unknown, not a false negative). The SSR payload carries the
featured match: `"code":"gift-refinements.r9.e1"`, `coworldId cow_e19d6eae…`, `coworldVersion
0.1.2`, `replayUrl …c3935602…` — the same replay verified under check 4, with both ranked players
in `matchup`. Live `POST /coworlds/replays/session` for that coworld+replay returns
`viewer_url = …/v2/coworlds/replays/static/cow_e19d6eae…/sha256%3Aaccb4520…/index.html?replay=…`,
`ready:true`. Static path, cow_id + manifest sha, ends `/index.html` — **no `/client/replay` pod
URL anywhere**. The verifier named its source (C) and why A found nothing and B is null
platform-wide (`replay_viewer:null, featured_match:null` on every row — I saw the same). Evidence
is fetched, not reconstructed.

### 7. Certification declared the static bundle — TRUE **SUSTAINED**
Read the committed `runs/2026-08-25-gift-refinements/release-result.json` myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` — the required string. File identity fields match this
release: `version 0.1.2`, `cow_id cow_e19d6eae…`, `manifest_sha sha256:accb4520…`,
`certify.ok:true`, all 10 cert steps `[pass]` in `output_tail`. Cross-checked the release run
live: `gh run view 32927080527 -R Metta-AI/cogame-gift-refinements` → `success`,
`headSha d874ebd5…` — the fix commit VERIFY.md names. The `hosted_certification:"certifying"`
snapshot is explained and is phase 40's concern, not this check's.

### 8. Spectator judgment — viewer executed — TRUE **SUSTAINED**
Verified live: `gh run view 32930044755 -R Metta-AI/coworld-builder` →
`{"conclusion":"success","status":"completed","createdAt":"2026-08-26T04:23:33Z"}` — CI green is
a checked fact, not an accepted one. Artifacts are committed in the tree; I read them myself:
`viewer-smoke.json` → `loaded:true` at 3442 ms, `data_replay_loaded:"true"`,
`data_replay_error:null`, `failure: no failure`, and the `.url` field is byte-identical to the
check-6 `viewer_url` (right bundle, right replay). Three clock readouts differ:
`ROUND 1 / 12 TICK 0 OF 720` → `ROUND 7 / 12 TICK 376 OF 720` → `FINAL TICK 719 OF 720`. I viewed
`viewer-smoke.png` (1280×800): it is unmistakably the starter's chrome — scorebug with the two
plates (155 TOKENS BANKED / 152 GIFTS GIVEN), roster strip, transport strip with speed selector,
scrubber with the TOKENS IN PLAY momentum graph, endcard `CYR WINS — Baseline · ROUND LIMIT` with
the six scores, and the trust-graph panel with weighted edges. Every on-screen number reconciles
with the replay I downloaded (scores [33,11,46,22,26,17] sum to the 155 banked; 152 gifts; 344
minted; 1 defection). Legible, shows the game, not a gridlock-style rewrite. The judgment
paragraph exists and is grounded in the rendered evidence. `feed_lines:0` is correctly scoped:
the capture is at the final tick under the endcard overlay, and the check's two gates
(`loaded:true` + differing clocks) both hold.

## Findings the verifier disclosed that I confirm are non-blocking
- Round 8's single first-attempt `parse_error` (patron omitting `target`) whose retry succeeded —
  verified in the round-8 replay (`llm=23 retry=1`, zero scripted). Prompt-durability note, not a
  DoD item; the pinned round is clean.
- Scripted baselines out-score both LLM champions (CYR/reciprocator 46 vs daveey 33, daveey-1 11;
  endcard reads `CYR WINS — Baseline`). DoD asks the champions play with real LLM decisions,
  which 24/24 `llm` orders prove; balance is a phase-30 observation, correctly flagged rather
  than laundered.

## Non-blocking observations (judge's own)
- `feed_lines:0` in the smoke capture means the run's rendered evidence never shows a feed row;
  the momentum graph, clocks, scorebug and endcard carry the who-is-winning story, so check 8
  stands, but a mid-episode capture would make future verdicts stronger.
- Check 6's decisive evidence came via the `replays/session` POST (source C) rather than the two
  sources the prompt enumerates; it is the exact call the page's JS makes and the verifier
  documented the fallback chain, so I treat it as satisfying "record which source you used".

## Fetch audit
| check | VERIFY.md said | judge re-fetched | agrees |
|---|---|---|---|
| 1 | 8 completed; rounds 8+9 both-v3; r1 failed; r7 patron v2 | live /rounds + attributions | yes |
| 2 | 2 rows, daveey/daveey-1 :v3, rp=8, no fillers | live leaderboard | yes |
| 3 | ereq_f3e3a82c completed, replay_url, participants v3 | live episode-request | yes |
| 4 | strict JSON, protocol, complete, 24/24 llm | re-downloaded + recounted | yes |
| 5 | CLEAN, lobby 6/6, llmOrders=24 fallbacks=0 | re-fetched + re-decoded + re-grepped | yes |
| 6 | SSR featured r9.e1; session → static viewer_url | live page fetch + session POST | yes |
| 7 | committed file carries liveness string, 0.1.2 | read committed file + gh run view | yes |
| 8 | run 32930044755 success; loaded; 3 clocks differ | gh run view + committed artifacts + png | yes |

No check's TRUE rests on stale, inconsistent, or reconstructed evidence; every inline paste in
VERIFY.md reproduced exactly under fresh fetches at judgment time.

BLOCKING: 0
