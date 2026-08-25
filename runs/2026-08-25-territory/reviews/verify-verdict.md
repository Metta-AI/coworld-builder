blocking: 0

# phase-60 verdict — territory
Run: 2026-08-25-territory   Coworld: cow_e7cac219-31d0-45c5-93f8-649434351365 v0.1.1
Checklist: docs/SPEC.md §Definition of done (per prompts/60-verify.md)
Independent read written before reading VERIFY.md: yes — I re-fetched every API-checkable claim
myself (rounds, leaderboard, episode request, both replays, hosted logs, page SSR, replay session,
viewer-check run) and viewed viewer-smoke.png before opening VERIFY.md.

## Standing blocking findings

None. All eight checks are TRUE, each proven by fetched evidence that I independently reproduced.

## Checklist pass (independent)

| item | status | evidence (my own fetch, 2026-08-25 ~13:5x–14:0xZ) |
|---|---|---|
| 1. ≥2 completed rounds after fillers | TRUE | `GET /rounds?league_id=…` → rounds 2 (`round_e6aa04b8`) and 3 (`round_7a7a2fe9`) `completed`; round 1 `failed` with error verbatim `Temporal RoundWorkflow failed before settling the round.` (pre-filler, not counted; error recorded as the prompt requires). "After fillers" is proven clock-independently: both counted rounds seated exactly the registered filler policy-version ids `95091fc5…` / `d8d5829a…` (match `STATE.policies.filler_version_ids`), and fillers were POSTed before the first `trigger-round` (log.md phase 50). |
| 2. Both champions ranked | TRUE | `GET /divisions/$D/leaderboard` (bare list) → exactly two rows: `1 daveey territory-steward:v1 1030.53 rounds_played=2 wins=2`, `2 daveey-1 territory-condottiere:v1 969.47 rounds_played=2 wins=0`. Both `rounds_played ≥ 1`; fillers entirely absent. No filler rows, no `Baseline` rows needed. |
| 3. Latest round's episode completed with replay | TRUE | Round 3 → `ereq_d1b638fb-7588-4052-acea-0a69098f6126`, `status=="completed"`, `replay_url` = `…/1c2d12a8-0303-4ab0-a399-f2fa983a0da9.replay`. Participants: seat 0 `daveey` and seat 1 `daveey-1` with `is_filler:false`; 7 filler seats. (This endpoint shows fillers under real policy names with `is_filler:true`; the `Baseline (N)` display form appears in the replay `players[]` and the rendered scorebug — VERIFY.md records this honestly and I confirm it.) |
| 4. Replay bytes valid, show the game | TRUE | Fetched the 3,897,298-byte replay myself: `jq -e` ok **and** python strict UTF-8 decode + `json.loads` ok. `protocol == "cogweb.replay.v1"` (matches the manifest's global-protocol declaration). `results.reason == "complete"`, `turnsPlayed: 18` — the healthy value; no `deadline` exception invoked. Champion fallbacks: `results.fallbacks == [0,3,0,…]`, cross-checked against `actPrompt` frames — 36 champion decisions, 3 `usedFallback:true` (8.3%, a small minority), and the fallback cause is the game's affordability validator ("cannot afford this set"), not an LLM outage. 40 talk lines, all from the two champions, doctrine-consistent and game-specific (a negotiated border "east of 6,0" referenced across turns); 19 snapshots for 18 turns + FINAL; the `endcard` event is present with `reason:"complete"`. |
| 5. Hosted game log clean | TRUE | Fetched `/artifacts/logs` with the elevated header myself (1772 B, 4 containers): `grep -E 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'` → zero hits on the raw bytes → CLEAN. Game container ends `episode finished; scores=[149,75,249,259,220,0,177,250,336]` — exactly `results.scores`. No Bedrock symptom, so no platform-wide exception needed. |
| 6. Public page uses the static path | TRUE | Raw HTML has no `<iframe` (client-rendered — *unknown*, not a failure, per the prompt and playbook; `featured_match` is null platform-wide, which I confirmed across all coworlds). The page's SSR payload carries `state.playlist[0]` — a featured match with both champions in the matchup (now `territory.r4.e1`; the ladder advanced past the verifier's `territory.r3.e1`, both consistent). `POST /coworlds/replays/session` → `viewer_url` = `…/v2/coworlds/replays/static/cow_e7cac219…/sha256%3Ac437064a…/index.html?replay=<s3 url>&v=2`, `ready:true`; `<sha>` equals the certified `manifest_sha`. Zero occurrences of `/client/replay` in the page or the viewer URL. |
| 7. Certification declared the static bundle | TRUE | Read the **committed** `runs/2026-08-25-territory/release-result.json` myself: `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` — contains the required string verbatim; `.ok`, `.canonical` true; `manifest_sha` matches check 6's URL segment. |
| 8. Viewer executed, spectator judgment | TRUE | `gh run view 32852582973` → `status: completed, conclusion: success`, created 13:18:54Z (1 s after the recorded dispatch — the find-the-new-run discipline was followed; the artifact's `url` field echoes the exact check-6 viewer URL, replay uuid included). `viewer-smoke.json`: `loaded: true` at 1294 ms via **both** signals (`data_replay_loaded:"true"` and bridge `ready`), `failure: null`, `loading_text: null`. Three clock readouts **differ**: 0% `Turn 1 / 18 · Commit`, 50% `Turn 11 / 18 · Commit`, 100% `Turn 14 / 18 · Commit` — both parts of the two-part TRUE condition hold. I viewed `viewer-smoke.png` myself: a dense, legible console that is unmistakably the cogherence chrome (TERRITORY wordmark + `#clock` in the top bar, PAINT BANKED scorebug with alias-over-policy rows incl. `Sable/daveey` and `Ochre/daveey-1`, WARS STARTED ledger with real smear sentences, 169-hex board with owner-coloured territory and legend, TURN LOG with priced claims, CHANNELS showing the champions' actual T14 talk verbatim from the replay, beat-button rail 01–14 with per-seat share bars and COMMIT·RESOLVE·UPKEEP strip). Picture reconciles with the record: `pool 146/146` ↔ `poolStart==poolEnd==146`; `wars started 0` ↔ `razes:[0,…]`; `Violet 0 … ▮×1` ↔ `Violet earned 0 paint from 1 wall`. Not a gridlock-style lookalike. The judgment paragraph in VERIFY.md is present, accurate, and matches what I see. |

## Refuted

Nothing to refute: I found no TRUE verdict resting on unfetched, misread, or stale evidence. Every
quoted byte in VERIFY.md that I re-fetched reproduced (rounds, leaderboard rows to the decimal,
participant ids, replay byte count 3897298, fallback turns [3,4,9], log CLEAN, session `viewer_url`,
cert string, run 32852582973 success, all four viewer readouts). The verifier's side claims also
check out: round 2's replay really does record `razes:[5,2,0,0,3,2,0,0,0]`, pool 163→150, and
champion scores 276>172, exactly as cited.

## The verifier's four self-reported non-blocking findings — adjudicated

1. **log.md clock ~67 min ahead of real UTC** — **advisory**. No checklist item depends on log.md
   wall stamps. The only check that could have leaned on them (check 1's "after the fillers were
   set") is proven clock-independently: both counted rounds seated the registered filler
   policy-version ids, which is only possible if the filler list predated them. Bookkeeping defect
   for the coordinator; correctly declared inside VERIFY.md itself.
2. **100% scrub lands on Turn 14, not FINAL — endcard unreachable from the beat row's right edge** —
   **advisory, the most substantive of the four**. Check 8's TRUE condition is exactly two-part
   (`loaded:true` + three differing clock readouts) plus a legible judgment paragraph; all three
   hold (Turn 1 → 11 → 14 is motion, not a frozen frame). prompts/60-verify.md itself classifies
   scrubber shortcomings as "a legibility finding for phase 30, not a licence to skip the question",
   and the question was answered from the screenshot + replay JSON. The endcard *exists* in the
   replay (I verified the `endcard` event with the full deadweight-loss payload) and per design
   renders on the FINAL slot; what failed is reaching that slot from the visible beat row in a
   1280 px viewport. That means the coworld's headline read-out (`pool 146→146`, reason, scores) is
   hard to reach for a spectator scrubbing to the right edge — worth a phase-30-class follow-up
   (does the beat row scroll or clip?), but it does not falsify any DoD item. Not blocking.
3. **Fully peaceful featured episode (0 razes, pool 146→146)** — **advisory (curation)**. Check 4
   demands champions doing the thing the game is about: non-scripted, non-trivial decisions, not
   all fallbacks — satisfied (claims on real coordinates, a border negotiated and honoured across
   turns, 3/36 fallbacks). The design note explicitly declares a zero-raze partition a legal and
   meaningful outcome of a mixed-motive game whose measured quantity is deadweight loss (a reading
   of 0 is a data point). The destruction mechanic demonstrably works in this league — I verified
   round 2's replay (12 razes, pool 163→150). No checklist item requires the featured match to
   showcase destruction. Not blocking.
4. **Scripted baselines out-earned both champions (up to 336 vs 149/75)** — **advisory (balance)**.
   No checklist item constrains champion-vs-filler score. The leaderboard ranks only the two
   champions against each other (fillers absent), so Elo is unaffected; daveey beat daveey-1 in
   both episodes (276>172, 149>75), coherent with wins 2–0. A game-balance note for a later pass.
   Not blocking.

## Non-blocking observations (mine)

- In viewer-smoke.png some scorebug policy labels ellipsize at 1280 px ("Baseli…") and one alias
  reads clipped ("Verdar[t]"); the design's degrade rules anticipate hiding the policy name only
  below 640 px. Cosmetic; the champion rows (`daveey`, `daveey-1`) are fully legible. Phase-30-class
  polish, not tied to any DoD item.
- The static viewer is served from `api.observatory.softmax-research.net` rather than the
  `softmax.com` proxy — documented platform behaviour (playbook: the proxy 404s the shell for every
  coworld), not a defect here.

## Verifier report audit

| claim (VERIFY.md) | verifier said | I verified | agrees |
|---|---|---|---|
| completed rounds | 2 (rounds 2, 3), round 1 failed pre-filler | same, error string verbatim | yes |
| leaderboard | daveey 1030.53 rp=2 w=2; daveey-1 969.47 rp=2 w=0; no fillers | same to the decimal | yes |
| episode request | ereq_d1b638fb completed, replay 1c2d12a8, champs seats 0/1 | same | yes |
| replay | strict JSON 3897298 B, cogweb.replay.v1, complete/18, fallbacks 3/36 turns 3,4,9 | same, incl. python strict decode | yes |
| hosted log | CLEAN, 4 containers, scores echo results | same (raw-bytes grep = 0 hits) | yes |
| page/static path | SSR playlist featured match; session → static URL ready:true; no /client/replay | same (playlist now r4.e1 — ladder advanced; still both champions, still static) | yes |
| cert | replay-liveness skipped string in committed release-result.json | same | yes |
| viewer-check | run 32852582973 green; loaded:true 1294 ms; clocks 1/11/14 | gh run success; json + png match | yes |
| side claims | round-2 razes [5,2,0,0,3,2,0,0,0] pool 163→150; champ scores 276>172 | fetched round-2 replay: exact | yes |

Verdict: the definition of done is proven. All eight checks TRUE at the current head; the four
self-reported findings are advisory.

BLOCKING: 0
