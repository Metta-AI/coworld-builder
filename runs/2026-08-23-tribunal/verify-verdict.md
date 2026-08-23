blocking: 0

# Phase-60 verdict — tribunal

Run `2026-08-23-tribunal` · adjudicated 2026-08-23 · judge context fresh (no prior sight of this run).
Checklist: `docs/SPEC.md` §Definition of done (items 1–8), read before VERIFY.md.
Independent read of the artifacts (STATE.json, release-result.json, episode.replay.json,
viewer-check/*, log.md) formed before accepting any VERIFY.md claim. Every check below was
either re-fetched live by me or read from the committed artifact by me; nothing is accepted on
the verifier's assertion alone.

## Per-item adjudication

### 1. ≥2 completed rounds after fillers set — **PROVEN**
- Re-fetched `GET /rounds?league_id=league_17699528-…&limit=20` myself: exactly two entries,
  round_number 1 (`round_aefed7c8-…`) and 2 (`round_3b46b826-…`), both `status=completed`,
  `error` empty, none failed/discarded. Matches VERIFY.md's paste.
- Adversarial point I pressed: VERIFY.md cites the `log.md` line stamped `17:00:11Z 50 fillers
  registered … (before first trigger)`, but round 1 was **created 16:59:02Z** — the log line is a
  batched phase-50 checkpoint (five phase-50 events share the 17:00:11Z stamp), so the log
  timestamp alone proves nothing about ordering. What settles it is the verifier's *other*
  evidence, which I reproduced: I fetched round 1's episode request
  (`ereq_7c23b2fc-…`, completed) and its replay
  (`replays/a260a841-….replay`) — `policyNames` = `["daveey","daveey-1","Baseline","Baseline (2)",
  "Baseline (3)"]`. Round 1's episode empirically seated three filler Baselines, so the fillers
  were in force before the earliest counted round ran. The item as SPEC states it holds.

### 2. Both champions ranked, fillers absent/Baseline — **PROVEN**
- Re-fetched `GET /divisions/div_2b2cf964-…/leaderboard` myself: exactly two rows —
  rank 1 `daveey-1` `tribunal-juror:v1` 1030.53 (2 rounds, 2 wins), rank 2 `daveey`
  `tribunal-advocate:v1` 969.47 (2 rounds, 0 wins). No filler rows; in-episode they are
  `Baseline (N)` (item 4 replay). Matches VERIFY.md exactly.

### 3. Latest round's episode request — **PROVEN**
- Re-fetched `GET /episode-requests?round_id=round_3b46b826-…`: single entry
  `ereq_a84a27d9-…` `completed`; detail shows non-null `replay_url`
  (`…/cd9fe302-….replay`), seats 0/1 = daveey (tribunal-advocate:v1) / daveey-1
  (tribunal-juror:v1) with `is_filler:false`, seats 2–4 fillers `is_filler:true`. Matches.

### 4. Replay bytes — **PROVEN**
- Re-fetched the replay from S3 myself: HTTP 200, 10250 bytes, passes `jq -e` (strict UTF-8
  JSON), `protocol == tribunal.replay.v1` (matches the design note §"Replay payload —
  tribunal.replay.v1", design.md:551), `results.reason == "complete"`.
- Byte-for-byte identical (jq-normalized diff) to the committed
  `runs/2026-08-23-tribunal/episode.replay.json`.
- Re-ran the decision census myself: champion seats 0 and 1 each 4/4 decision events
  `scripted:false`; filler seats 5/5 scripted (by design, not fallback); zero events with
  `fallback==true`. Argument texts are distinct per round and substantive (240–320 chars text +
  452–600 chars notes). Not all fallbacks; not trivial.

### 5. Hosted game log — **PROVEN**
- Re-fetched `/episode-requests/ereq_a84a27d9-…/artifacts/logs` with the elevated header
  myself: HTTP 200, 22690 bytes; my own
  `grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'`
  returned nothing → CLEAN. No cross-coworld check needed since the capacity string is absent.

### 6. Public page static replay path — **PROVEN** (sources declared and reproduced)
- The verifier deviated from the prompt's listed fallback (`GET /coworlds`, whose
  `replay_viewer`/`featured_match` are null platform-wide) and used the page's SSR payload plus
  `POST /coworlds/replays/session`. It declared which sources it used, as the prompt requires.
  I reproduced both: my fetch of `https://softmax.com/tribunal` (HTTP 200) contains the SSR
  `playlist` with featured match `tribunal.r2.e1`, this coworld's id, and the item-3 replay URL —
  featured match present in the actually-fetched page; my POST to `/coworlds/replays/session`
  returned the identical
  `…/v2/coworlds/replays/static/cow_074e3eb0-…/sha256%3A25965cf8…/index.html?replay=…&v=2`,
  `ready:true`. The sha matches `STATE.coworld.manifest_sha`. `grep -c 'client/replay'` on the
  page HTML = 0. Any residual doubt that the page *embeds* this URL is closed by item 8, which
  executed that exact URL in a browser and it rendered this game.

### 7. Certification declared static bundle — **PROVEN**
- Read the committed `runs/2026-08-23-tribunal/release-result.json` myself:
  `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
  /client/replay and /replay not required)`; `ok:true`, `canonical:true`,
  `hosted_certification:"certified"`, all 10 cert steps pass in `output_tail`. Source is the
  committed copy from release run 32652915687, consistent with `STATE.coworld.release_run_id`.

### 8. Viewer executed + spectator judgment — **PROVEN**
- CI fact checked: `gh run view 32654376748 -R Metta-AI/coworld-builder` →
  `viewer-check`, `completed`/`success`, created 2026-08-23T17:17:53Z.
- I re-downloaded the run's `viewer-check` artifact and diffed it against the committed
  `runs/2026-08-23-tribunal/viewer-check/` — **identical**, so the committed png/json are
  genuinely that run's output, and `viewer-smoke.json`'s recorded `url` is the exact item-6
  static URL (so the run tested the right thing).
- (a) loaded: `loaded:true`, bridge `["loading","ready"]`, `bridge_ready:true`,
  `failure:null`, 731 ms. (b) advances: scrub clocks `ROUND 1` → `ROUND 1 / 4` →
  `TRUTH — GUILTY · JURY 3/3` — three differing readouts. (c) I inspected
  `viewer-smoke.png` myself: a fully painted courtroom — TRIBUNAL topband with
  `TRUTH — GUILTY · JURY 3/3`, five-seat scorebug strip (daveey −1.0 DEF, daveey-1 +1.0 PROS,
  three jurors +1.0 GUILTY), colour-coded evidence cards (E10/E8/E7/E1 prosecution amber,
  E9/E12 defence blue), disclosure counters, juror GUILTY chips with quote bubbles,
  `SCALES OF EVIDENCE` bar GUILT 12 / 10 INNOCENCE, event-tick scrubber at 30/30, and an
  endcard (`VERDICT GUILTY · TRUTH GUILTY · 4 ROUNDS`, `daveey-1 CARRIED THE ROOM`, full
  role/vote/truth/score table). Every element reconciles with the replay JSON I fetched
  (4 rounds, 3 guilty votes, truth guilty, scores −1/+1/+1/+1/+1). The chrome is the
  bullwhip-family shell (topband/scorebug/momentum bar/scrubber/endcard), not a rewrite.
  The verifier's judgment paragraph is an accurate description of the screenshot, and the
  screenshot shows the game. Legible: yes.

## Non-blocking observations (carry forward, not defects in this phase)
- Check 1: the batched `log.md` timestamp (fillers line 17:00:11Z vs round 1 created 16:59:02Z)
  is non-probative on its own; the round-1 replay seats are the real proof. Future runs should
  log the filler registration with its actual UTC time, not a checkpoint batch.
- Check 8: the probe's generic selectors read `scorebug:""` / `feed_lines:0` although both
  regions visibly render — the verifier already flagged this as a phase-30 selector-naming note;
  it does not touch item 8's pass conditions.

## Roll-up

| # | item | VERIFY.md | judge (independently re-fetched/read) |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | TRUE | PROVEN (re-fetched; round-1 replay seats the fillers) |
| 2 | champions ranked, fillers absent | TRUE | PROVEN (re-fetched) |
| 3 | latest ereq completed + replay_url | TRUE | PROVEN (re-fetched) |
| 4 | replay valid, shows the game | TRUE | PROVEN (re-fetched; matches committed copy) |
| 5 | hosted log clean | TRUE | PROVEN (re-fetched, my own grep) |
| 6 | static replay path + featured match | TRUE | PROVEN (page SSR + session endpoint reproduced) |
| 7 | cert declared static bundle | TRUE | PROVEN (committed release-result.json read directly) |
| 8 | viewer executed, judgment | TRUE | PROVEN (run 32654376748 success; artifact diff identical; png inspected) |

No SPEC §Definition of done item is unproven at adjudication time.

BLOCKING: 0
