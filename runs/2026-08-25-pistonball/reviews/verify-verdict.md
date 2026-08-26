blocking: 0

# verify verdict — pistonball (phase 60, re-adjudicated after Addendum 2)
Head: cogame-pistonball `30964b3d16bffe6a4df164e7c13b1c581f1a48e4` (main = 0.1.3 release headSha; release run 32936048068 conclusion `success`), coworld `cow_768730a3-282a-4d75-9cff-01eea560e260` v0.1.3 canonical.
Checklist: `docs/SPEC.md` §Definition of done (items 1–8) via `prompts/60-verify.md`.
Independent read written before reading fixes: yes — in round 1 of this adjudication I re-fetched rounds, leaderboard, the round-8 episode request, the round-8 replay bytes (ran `tools/replay_summary.py` myself), the round-8 hosted log, the SSR playlist, the replay-session route, the committed `release-result.json`, and the committed viewer-check artifacts, and read both screenshots, before opening VERIFY.md's Findings or `verify-fixes.md`. This revision re-verifies the new `viewer-check-013/` evidence from the committed files and the run id, not from the addendum's prose.

## Standing blocking findings

None. The single blocker from the previous verdict (B1) is resolved at head — see below.

### B1 (previous verdict) — [viewer-evidence] SPEC item 8: executed-viewer evidence was stale (0.1.2 bundle) → RESOLVED at head
- Where: `runs/2026-08-25-pistonball/viewer-check-013/viewer-smoke.json` + `viewer-smoke.png`; viewer-check run **32937649794**.
- Verified at head, from the committed artifacts (not the addendum's summary):
  - `viewer-smoke.json` `.url` is byte-for-byte the current check-6 iframe src:
    `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_768730a3-282a-4d75-9cff-01eea560e260/sha256%3A91c1207c7f679847f054a230f0d44e58aad9f52d927f8cc5678e3f619aa33915/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F20418470-73ca-48e7-9a22-fabfec4f8f7d.replay&v=2` — the **0.1.3** bundle (cow_id and manifest sha both match STATE) drawing the **round-8** replay, i.e. exactly the URL my own session POST returned in round 1.
  - Gate (a): `{"loaded":true,"ms":3109}`, signals `{"data_replay_loaded":"true","data_replay_error":null}`, `failure: no failure`.
  - Gate (b): the three scrub clocks differ — `0% → 1:15 TIME LEFT`, `50% → 0:59 TIME LEFT`, `100% → FINAL GAME OVER`.
  - Gate (c): I read `viewer-smoke.png` myself. It is the starter's chrome, item for item — scorebug strip (phase chip `59%`, `91.2 SCORE` in green, `THE BANK - 20 cogs`, momentum micro-graph, `FINAL / GAME OVER`, journey bar `GOAL WALL — 50% — START` with the puck on the goal end), transport strip with `spoilers`, `BANK WINS 781 / 782`, `1×…16×` speed buttons, and the scrubber with beat markers and journey trace. The endcard reads `BALL ON THE GOAL WALL`, `91.2 SHARED SCORE`, and a 20-row `POLICY · PISTON · IN PHASE · TOUCHES · LLM/FB` table in which **the headers no longer collide (F3 fixed in the shipped bundle)** and **`daveey` (piston 12) and `daveey-1` (piston 4) both read `4/0` under LLM/FB (F2 fixed in the shipped bundle)** — which reconciles exactly with my own round-8 replay read (champion seats `source:"llm"` on turns 0–3 = 4 llm turns each, `fallbacks: 0`); the Baseline and third-party wavebot-fork rows read `0/0`, correct for scripted seats.
  - CI fact checked, not accepted: run 32937649794 in Metta-AI/coworld-builder, workflow `viewer-check`, created 2026-08-26T06:19:23Z, `status completed`, `conclusion success`.
- Checklist item: SPEC §Definition of done **8** — all three sub-gates now hold against the shipped bundle, with the evidence committed under `runs/2026-08-25-pistonball/viewer-check-013/`.

## Refuted

### F1 — "champion seats fall back on every turn after turn 0" → REFUTED at head (fixed, proven in production)
- Evidence: `src/pistonball/decide.nim` at `30964b3` — `let turnStart = getMonoTime()` is now sampled **after** the rate-floor sleep block (`if open.len > 0 and engine.batchStarted …: sleep(…)`), with the comment "`turnBudgetMs` bounds THIS TURN'S OWN WORK … sampled AFTER the rate-floor sleep". Production proof I fetched myself: round-8 replay `20418470-73ca-48e7-9a22-fabfec4f8f7d.replay` → `replay_summary.py` → champion seats' scripts `llm` on turns 0,1,2,3 with varied modes (`wave`/`drop`/`catch`/`hold`) and non-trivial `say` text, `fallbacks: 0`, `reason complete`/`endRule delivered`, `sharedScore 91.212`. And now also rendered: the shipped viewer's endcard shows `4/0` for both champions. F1 was true when found (round-2 replay: 14 fallback / 2 llm) and is fixed at the current head.

### "VERIFY.md's main body is 0.1.2-era, so items 1–6 are stale" → REFUTED by re-fetch: every one is true at head
- Item 1: `GET /rounds?league_id=league_6789db33…` → rounds **2–8 all `completed`** (7 ≥ 2), round 1 `failed` with error verbatim "Temporal RoundWorkflow failed before settling the round." (auto-fired pre-fillers; excluded). SPEC item 1 requires only *completed rounds after the fillers were set* — it says nothing about post-fix behaviour, so the pre-fix rounds 2–7 count; the item is true regardless because round 8 alone plus any one of 2–7 satisfies it.
- Item 2: `GET /divisions/div_de04ec28…/leaderboard` (bare array) → `1 daveey pistonball-swell:v2 1000.0 7 0.0` and `2 daveey-1 pistonball-cascade:v2 1000.0 7 0.0`; this run's fillers (wavebot:v2/metronome:v2) absent. TRUE.
- Item 3: latest completed round = 8 (`round_638df556…`) → `ereq_f2d4d58a…` `status completed`, `replay_url` non-null, participants name `daveey` (pistonball-swell v2) and `daveey-1` (pistonball-cascade v2), 16 seats `is_filler:true` (Baseline (N) in the replay names), plus 2 third-party entrants (see observations). TRUE.
- Item 4: round-8 replay bytes fetched from S3; design-declared binary `COWLDPST` substitute (`design.md` §Replay bytes, lines 937–962) applied: `replay_summary.py` output is strict UTF-8 JSON (`jq -e` ok), `protocol pistonball/v1` matches, `reason complete`/`delivered`, champions LLM on every turn, 0 fallbacks. TRUE — and the "deadline" exemption was not needed.
- Item 5: `GET /episode-requests/ereq_f2d4d58a…/artifacts/logs` (elevated) → grep for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → **CLEAN**. TRUE at head for the latest round (VERIFY's round-3 429 was correctly documented platform-wide per the prompt's exception and waited out inside the bound).
- Item 6: raw HTML has no iframe (client-rendered, treated as unknown per playbook); SSR payload carries `playlist[0]` = `pistonball.r8.e1` at coworldVersion 0.1.3 with both champions in the matchup (featured match present); session route returns the static path with the **0.1.3 manifest sha** (`sha256:91c1207c…` = `STATE.coworld.manifest_sha`), `ready:true`, no `/client/replay` anywhere. TRUE.
- Item 7: committed `runs/2026-08-25-pistonball/release-result.json` (overwritten at re-release, matching STATE: version 0.1.3, `cow_768730a3…`, canonical true) → `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`. Release run 32936048068: `conclusion success`, headSha `30964b3…`. TRUE.

## Checklist pass (independent)

| item | status | evidence (path/fetch) |
|---|---|---|
| 1. ≥2 completed rounds post-fillers | TRUE | `GET /rounds` — rounds 2–8 `completed`, round 1 `failed` (error quoted), fillers set before trigger (log.md 04:42:13Z; 18 filler seats in round-2 episode) |
| 2. Both champions ranked, fillers absent/Baseline | TRUE | leaderboard: daveey rp=7, daveey-1 rp=7; wavebot:v2/metronome:v2 absent |
| 3. Latest round's ereq completed with replay | TRUE | `ereq_f2d4d58a…` completed, `replay_url` s3 …20418470…, daveey + daveey-1 seated, fillers `is_filler:true` |
| 4. Replay valid, shows the game, champions not fallbacks | TRUE | round-8 bytes → summary JSON strict-parses; `pistonball/v1`, `complete/delivered`, champion scripts `llm` turns 0–3, varied `mode`/`up_m`/`say`, `fallbacks 0` |
| 5. Hosted log clean | TRUE | round-8 logs grep → CLEAN |
| 6. Static replay path + featured match | TRUE | SSR `playlist[0]`=r8.e1@0.1.3; session → `…/replays/static/cow_768730a3…/sha256%3A91c1207c…/index.html?replay=…`, `ready:true` |
| 7. Cert declared static bundle | TRUE | committed `release-result.json` → `Replay liveness: skipped (static replay bundle declared…`; run 32936048068 success |
| 8. Viewer executed at head and judged | TRUE | `viewer-check-013/`: executed URL = current check-6 src (0.1.3 sha + round-8 replay); `loaded:true` 3109 ms; clocks 1:15 / 0:59 / FINAL differ; run 32937649794 success; screenshot = starter chrome, endcard reconciles with replay (champions 4/0 LLM/FB, headers fit) |

## Fixer report audit (`reviews/verify-fixes.md`)

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed in `06bd3f7` (decide.nim, turnStart after sleep) + engine test | tree at head: `turnStart` sampled after the rate-floor block, comment matches; **production**: round-8 champions llm×4, 0 fallbacks; **rendered**: endcard 4/0 | yes |
| F2 | fixed in `87ba292` (replays.nim recount from `script` records) + replay test | tree at head: `applyReplayEvents` increments `llmTurns`/`fallbackTurns` from `node{"source"}`; **rendered in the shipped bundle**: champions read `4/0`, scripted seats `0/0` (viewer-check-013 png) | yes |
| F3 | fixed in `30964b3` (endcard header sizing) + viewer test | commit touches `client/replay_broadcast.html`; CI 32934920010 `success`; **rendered in the shipped bundle**: `TOUCHES` and `LLM/FB` headers sit cleanly in their own columns in both table halves (viewer-check-013 png) | yes |

## Non-blocking observations
- SPEC item 4 says "valid UTF-8 JSON" but the replay is the starter's binary `COWLDPST` format; the accepted design note pins that format and prescribes the `replay_summary.py` substitute the verifier (and I) used. The item's intent — "replay bytes are valid and show the game" — is met; noting the textual divergence for the record.
- The leaderboard now carries two third-party entrants (`relh` rank 3, `richard` rank 4, both `co-gas-pistonball-wavebot-*:v1`, rounds_played 4, `is_filler:false` in episodes). They are not this run's fillers and don't violate item 2 as written. Their endcard rows correctly read `0/0` LLM/FB (scripted).
- VERIFY.md's Addendum 1 did not re-record items 2, 5 and 6 at 0.1.3; all three re-fetch TRUE at head, so this cost nothing this time, but a re-release addendum should re-fetch every version-sensitive item, not only check 4. Addendum 2 now covers item 8 properly.
- The superseded 0.1.2 evidence remains at `runs/2026-08-25-pistonball/viewer-check/`; it is historical F2/F3 proof, no longer item-8 evidence. Keeping both directories is fine; VERIFY.md's item-8 body still cites the old one, with Addendum 2 as the operative record.
- The coordinator's Addendum 1 quotes `llmTurns":[0,4,4,0,...]` for round 8 — champion seats sat at indices 1 and 2 there (seat order differs per episode); consistent with my read (daveey position 1, daveey-1 position 2), not a discrepancy.

## Contamination declaration
I read the coordinator's briefing notes (which summarised F1, Addendum 1 and Addendum 2) before my fetches — unavoidable, they were the briefs. In round 1 I did not read VERIFY.md's Findings, the Addendum text, or `verify-fixes.md` until my own fetches were complete; in this revision I verified Addendum 2's claims from the committed `viewer-check-013/` files and the GitHub run id before accepting any of them. Every number in the checklist pass is from my own fetches at head.

BLOCKING: 0
