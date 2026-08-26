blocking: 1

# verify verdict — pistonball (phase 60)
Head: cogame-pistonball `30964b3d16bffe6a4df164e7c13b1c581f1a48e4` (main = 0.1.3 release headSha; release run 32936048068 conclusion `success`), coworld `cow_768730a3-282a-4d75-9cff-01eea560e260` v0.1.3 canonical.
Checklist: `docs/SPEC.md` §Definition of done (items 1–8) via `prompts/60-verify.md`.
Independent read written before reading fixes: yes — I re-fetched rounds, leaderboard, the round-8 episode request, the round-8 replay bytes (ran `tools/replay_summary.py` myself), the round-8 hosted log, the SSR playlist, the replay-session route, the committed `release-result.json`, and the committed `viewer-check/` artifacts, and read the screenshot, before opening VERIFY.md's Findings or `verify-fixes.md`.

## Standing blocking findings

### B1 — [viewer-evidence] SPEC item 8: the executed-viewer evidence is stale at head — the shipped 0.1.3 viewer bundle has never been executed (source: judge)
- Where: `runs/2026-08-25-pistonball/viewer-check/viewer-smoke.json` (`.url`) vs the check-6 iframe src at head.
- Verified at head:
  - The committed viewer-check (run 32933394784) executed
    `…/replays/static/cow_58917aec-…/sha256%3Ab041d203…/index.html?replay=…eab95e2d….replay` — the **0.1.2** bundle drawing the **round-4 (pre-fix)** replay (`viewer-smoke.json` `.url`, quoted verbatim from the committed file).
  - The check-6 iframe src at head is different: `POST /coworlds/replays/session` for the featured replay (SSR `playlist[0]` = `pistonball.r8.e1`, coworldVersion 0.1.3) returns
    `…/replays/static/cow_768730a3-…/sha256%3A91c1207c…/index.html?replay=…20418470….replay&v=2`, `ready:true` — the **0.1.3** bundle drawing the **round-8** replay.
  - The two bundles are not the same viewer: commit `30964b3` (F3) modified `client/replay_broadcast.html` — the exact HTML shell the static route serves and viewer-check loads — and commit `87ba292` (F2) modified `src/pistonball/replays.nim`, whose replay-event recount is compiled into the wasm re-simulator the static viewer runs. The framing "the game's viewer files did not change in the fix" is therefore false for F3 (and effectively for F2).
  - The committed `viewer-smoke.png` **visibly displays the F2 and F3 defects** (every endcard row reads `LLM/FB 0/0` including daveey/daveey-1; the `TOUCHES`/`LLM/FB` headers overprint as `TOUCHESLM/FB` — I read the image myself). As evidence of the *shipped* spectator experience it is contradicted, not merely old: 0.1.3 claims to have changed exactly what this picture shows.
  - SPEC item 8 binds the execution to "the check-6 iframe `src`" and the phase's doctrine is "fetched, never assumed" — inferring that a recompiled bundle with a changed shell still renders is precisely the inference item 8 exists to forbid (cogame-lantern, 2026-08-23). The only thing I could verify at head is that the 0.1.3 `index.html` fetches `200` (231 547 bytes) — asset-200 is expressly not rendering evidence.
- Checklist item: SPEC §Definition of done **8** ("The viewer actually renders, proven by executing it… evidence committed under `runs/<run>/viewer-check/`").
- What settles it: one re-dispatch of `viewer-check.yml` against the current check-6 iframe src (the session-route URL for `cow_768730a3…/sha256:91c1207c…` with the round-8 replay), the new `viewer-smoke.json` + `viewer-smoke.png` committed, showing `loaded:true`, three differing clock readouts, and an endcard whose champion rows show non-zero `LLM/FB` and non-colliding headers (which would simultaneously be the first rendered proof that the F2/F3 fixes work).

## Refuted

### F1 — "champion seats fall back on every turn after turn 0" → REFUTED at head (fixed, proven in production)
- Evidence: `src/pistonball/decide.nim` at `30964b3` — `let turnStart = getMonoTime()` is now sampled **after** the rate-floor sleep block (`if open.len > 0 and engine.batchStarted …: sleep(…)`), with the comment "`turnBudgetMs` bounds THIS TURN'S OWN WORK … sampled AFTER the rate-floor sleep". Production proof I fetched myself: round-8 replay `20418470-73ca-48e7-9a22-fabfec4f8f7d.replay` → `replay_summary.py` → champion seats' scripts `llm` on turns 0,1,2,3 with varied modes (`wave`/`drop`/`catch`/`hold`) and non-trivial `say` text, `fallbacks: 0`, `reason complete`/`endRule delivered`, `sharedScore 91.212`. F1 was true when found (round-2 replay: 14 fallback / 2 llm) and is fixed at the current head — refuted as a standing finding.

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
| 8. Viewer executed at head and judged | **BLOCKING (B1)** | committed evidence executes the 0.1.2 bundle/round-4 replay; 0.1.3 changed `client/replay_broadcast.html` + `replays.nim`; no rendered evidence of the shipped bundle exists |

## Fixer report audit (`reviews/verify-fixes.md`)

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed in `06bd3f7` (decide.nim, turnStart after sleep) + engine test | tree at head: `turnStart` sampled after the rate-floor block, comment matches; commit touches `src/pistonball/decide.nim`+`tests/test_engine.nim`; **production**: round-8 champions llm×4, 0 fallbacks | yes |
| F2 | fixed in `87ba292` (replays.nim recount from `script` records) + replay test | tree at head: `applyReplayEvents` increments `llmTurns`/`fallbackTurns` from `node{"source"}`; commit touches `src/pistonball/replays.nim`+`tests/test_replay.nim` | yes in tree; **rendered effect unproven** (B1) |
| F3 | fixed in `30964b3` (endcard header sizing) + viewer test | commit touches `client/replay_broadcast.html`+`tests/test_viewer.nim`; CI run 32934920010 `success` at `30964b3` (checked, not accepted) | yes in tree; **rendered effect unproven** (B1) |

## Non-blocking observations
- SPEC item 4 says "valid UTF-8 JSON" but the replay is the starter's binary `COWLDPST` format; the accepted design note pins that format and prescribes the `replay_summary.py` substitute the verifier (and I) used. The item's intent — "replay bytes are valid and show the game" — is met; noting the textual divergence for the record.
- The leaderboard now carries two third-party entrants (`relh` rank 3, `richard` rank 4, both `co-gas-pistonball-wavebot-*:v1`, rounds_played 4, `is_filler:false` in episodes). They are not this run's fillers and don't violate item 2 as written; VERIFY.md's "exactly two rows" claim is simply outdated.
- VERIFY.md's Addendum did not re-record items 2, 5 and 6 at 0.1.3; all three re-fetch TRUE at head (above), so this cost nothing this time, but a re-release addendum should re-fetch every version-sensitive item, not only check 4.
- The coordinator's Addendum quotes `llmTurns":[0,4,4,0,...]` for round 8 — champion seats sat at indices 1 and 2 there (seat order differs per episode); consistent with my read (daveey position 1, daveey-1 position 2), not a discrepancy.

## Contamination declaration
I read the coordinator's briefing note (which summarised F1 and the addendum) before my fetches — unavoidable, it was the brief itself. I did not read VERIFY.md's Findings section, the Addendum text, or `verify-fixes.md` until my own fetches above were complete; every number in the checklist pass is from my own fetches at head.

BLOCKING: 1
