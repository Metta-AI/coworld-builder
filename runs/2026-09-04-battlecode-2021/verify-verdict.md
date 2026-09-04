blocking: 0

# phase-60 verdict — battlecode-2021 (bc21 league)
Head: coworld-builder bb3ec8b (VERIFY.md + artifacts at eb5c3aa; instrument fix afc534c)
Checklist: docs/SPEC.md §Definition of done (items 1–8), as commands in prompts/60-verify.md
Independent read written before reading VERIFY.md: yes — I read SPEC + the phase-60 prompt, the
design note, STATE.json, the committed viewer-check/, viewer-check-rerun/ and release-result.json
artifacts, and re-fetched the live evidence (rounds, leaderboard, episode request, replay bytes,
hosted log, session endpoint, both public pages, both GH runs) before opening VERIFY.md.

## Standing blocking findings

None.

## Checklist pass (independent — every item re-fetched or re-read by me, not taken from VERIFY.md)

| item | status | evidence |
|---|---|---|
| 1. ≥2 completed rounds after fillers set | TRUE | Live `GET /rounds?league_id=league_cb515f3b…`: **3** completed (round_6feca3e3 #1, round_dc7a247d #2, round_9bbd44c4 #3), all `error` null, no failed/discarded row. log.md 15:47:24Z records fillers (45c48b3f, 28b535fa — neither a champion version id) before `trigger-round`. Round 1's `created_at` 15:46:26Z predates the batch log stamp, but rounds 2 (16:01:26Z) and 3 are unambiguously after the filler write, so ≥2 holds even discounting round 1. |
| 2. Both champions ranked, fillers absent | TRUE | Live `GET /divisions/div_5beaa66e…/leaderboard`: rank 1 `daveey` `battlecode-bc21-turtle:v1` 1043.75 rounds_played=3; rank 2 `daveey-1` `battlecode-bc21-muckrush:v1` 956.25 rounds_played=3. Exactly two rows; no filler, no Baseline row. |
| 3. Latest round's episode request completed with replay | TRUE | Live `GET /rounds/round_dc7a247d…/episode-requests` → ereq_1f12242c `completed`, `replay_url` …/9d29794c….replay; detail endpoint: participants `daveey` and `daveey-1`, both `is_filler:false`, scores 267.5/31.5. (Round 3's ereq_c18c0e5c is also `completed` with a replay at current head.) The flat `GET /episode-requests?round_id=` 405s — I reproduced that; the nested route is the documented one (playbook §9), not a dodge. |
| 4. Replay bytes valid, show the game | TRUE | I fetched the 71 618-byte replay: strict JSON (`jq -e` clean), `protocol` `cogame.battlecode.v1` / `game_version` GV06 / `year` bc21 (matches docs/PROTOCOL.md:222), `.result.reason == "complete"`, `policy_kind ["llm","llm"]`, `fallbacks [0,0]`, `defaults_applied 0` on both `doctrine_received` events. Seats carry two verbatim LLM sheets differing on 9 of 10 knobs with distinct mottos/notes (turtle: slanderer_ratio 70, escalate_when_ahead, empower 140; muckrush: muck_ratio 65, never bids, empower 25) — non-scripted, non-trivial, zero fallbacks. Both games full 1500 rounds, sides swapped, contested (game 1: Basil builds 1764 units and takes 2 centers yet loses the vote 1381–0). Note: the phase prompt's `.results`/`.type` jq paths return empty on this schema (`.result`/`.kind`); VERIFY.md discloses this and reads the right keys — the substance of the check is met. |
| 5. Hosted log clean | TRUE | I re-fetched `episode-requests/ereq_1f12242c…/artifacts/logs` (elevated): zero matches for the four gated patterns → CLEAN. Both openrouter POSTs `200 OK`; `refused a seat-0 connection … wrong connection token` is followed by `seat 0 connected/registered kind=llm` and contains no gated string. |
| 6. Public page uses static replay path | TRUE | Raw-HTML iframe grep empty (client-rendered — a documented dead end, correctly not recorded as a false negative). I re-ran the session call the page's JS makes: `POST /coworlds/replays/session` → `viewer_url` `…/v2/coworlds/replays/static/cow_455dff0d…/sha256%3A8ec16f22…/index.html?v=2#replay=<s3>`, `ready:true`; the `#replay=` fragment is the documented 2026-08-28 form of the static route (playbook §Featured match) and the `<sha>` is byte-identical to STATE's manifest_sha. SSR payload of `softmax.com/battlecode/bc21` has `leagueId league_cb515f3b…` and a non-empty `playlist[0]` (cow_455dff0d, 0.3.0; currently round 4 — the featured slot tracks the newest episode, which corroborates rather than contradicts VERIFY's round-2 snapshot). Zero `/client/replay` occurrences on either page. `/coworlds` shows cow_455dff0d 0.3.0 as the sole `canonical:true` row. |
| 7. Certification declared the static bundle | TRUE | Committed `runs/…/release-result.json` (5 107 B): `.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`; `ok:true`, `canonical:true`, release run 33890103949 conclusion `success` (checked via gh). Read from the committed copy, not /tmp. |
| 8. Viewer executed; replay advances; spectator judgment | TRUE (on the re-run; ruling below) | Run 33895007454: `conclusion success`, `head_sha afc534c` (the adaptive-settle fix), CI log shows `SETTLE: 20000 / SOAK: 15`; unexpired `viewer-check` artifact matches the committed `viewer-check-rerun/`. `loaded:true` via both signals (`data-replay-loaded="true"` + bridge `ready`, 1 482 ms, `failure:null`). Three clock readouts **differ**: `1:50 GAME 1 OF 2 — BOG` / `1:02 GAME 2 OF 2 — ARENA` (settle 3 515 ms) / `FINAL MATCH OVER` (settle 4 015 ms) — reconciling exactly with the replay's two-game sweep. Soak: `moved:true`, tick `round 2 → 314 → 362 / 1500` over 15 s, `page_errors []` — unattended playback advances. The judgment paragraph is present, written from the pngs, and I verified it against the screenshots myself: mid-game frame shows the Bog board, both clans' robots, scorebug with real names + recorded mottos, votes pill, killfeed lines that are verbatim replay `first_build` events, stat rail, full transport strip; the rerun png shows the FINAL endcard in plain words (`CLAN ASH WON THE ELECTION 1406 VOTES TO 0`) with both doctrine cards. It is the starter's chrome (same transport/scrubber/scorebug/endcard family as paintbot; the bc20 control renders in the same shell), not a gridlock-style rewrite. |

## Ruling on the check-8 re-run (judged on its merits)

The original FALSE was an instrument artifact, and the record proves it rather than asserts it:
the control run (33893927786, same bundle, same manifest sha, same harness, bc20's ~18×-lighter
replay) seeked across game boundaries to the endcard, isolating the variable to the bc21
replay's per-round simulation cost against a **fixed 700 ms** post-click settle. Commit afc534c
changed only the instrument — an adaptive poll that stops when the clock moves or `--settle`
elapses and records the true latency — no coworld-repo change. The re-run then answered the open
question (slow, not frozen): seeks land in 3.5–4.0 s and unattended playback advances ~360
rounds in 15 s.

SPEC §Definition of done item 8 requires (a) `loaded:true`, (b) the clock text differing across
the three scrub readouts, (c) a legible judgment paragraph that shows the game. All three hold
on the re-run. **It names no seek-latency bound**, and "degrade-never-hang" is a pin on episode
play inside `episodeTimeoutSeconds`, not on viewer scrub response; a bounded 4 s convergence
that visibly lands is degradation, not a hang, and the first frame paints in 1.5 s. The
3.5–4 s seek latency therefore does not falsify item 8. It is real spectator-experience residue
and belongs where VERIFY.md filed it: an advisory (Worker-side keyframe checkpoints), not a
blocking finding — there is no checklist item it stands against.

One instrument caveat I checked and discharge: the adaptive poll stops on *any* clock change, so
in principle normal playback could satisfy it spuriously. Here the recorded readouts are the
seek *targets* (game 2 at 50 %, FINAL at 100 %), unreachable by ≤4 s of playback from round
~360, so the seeks genuinely landed.

## Verifier report audit

| claim in VERIFY.md | I verified | agrees |
|---|---|---|
| Items 1–7 TRUE with pasted evidence | every item re-fetched live or re-read from committed artifacts (table above) | yes — and the evidence establishes each item, not just the prose |
| Item 8 FALSE at the original three attempts | committed viewer-check/ jsons: three identical `2:05 GAME 1 OF 2 — BOG` readouts, png at round 5/1500 | yes — the original FALSE was honestly earned at the time |
| Re-run supersedes: item 8 TRUE | run 33895007454 success at afc534c with settle=20000/soak=15 (CI log), committed rerun json/png match the run artifact | yes |
| Rounds/leaderboard/replay ids | all byte-identical to what I fetched (league, division, ereq, replay URL, policy version ids, manifest sha) | yes |

Nothing in VERIFY.md was claimed that its pasted evidence (or my re-fetch) fails to establish.
The one schema divergence (`.result`/`.kind` vs the prompt's `.results`/`.type`) and the one
timestamp wrinkle (round 1 created 15:46:26Z vs the 15:47:24Z batch log stamp) are both
disclosed in VERIFY.md and neither changes an item's truth value (item 1 holds on rounds 2–3
alone; item 4's required values were read with the correct keys).

## Non-blocking observations (no checklist item; phase-30 / future-work material)

- Seek latency 3.5–4 s and ~13 s to catch up to real-time playback rate on bc21 replays — the
  Worker re-simulates on seek at ~3.12 ms/round. Advisory already filed in VERIFY.md
  (keyframe checkpoints).
- Top-centre collision: the bc21 votes pill overdraws the match clock (visible in both pngs;
  also present in the bc20 control, so inherited shared chrome).
- Bottom-right stacking: the last killfeed line collides with the unit-tally strip.
- `release-result.json` `hosted_certification: "certifying"` — a phase-40 snapshot value; the
  definition-of-done does not test it, and the coworld is `canonical:true` live.

## What I could not verify

Nothing material. Every definition-of-done item was verifiable from the tree, the committed
artifacts, or a live re-fetch; both cited GitHub runs (33890103949 release, 33895007454
viewer-check re-run) were checked by id and conclusion, and the re-run's artifact is unexpired
and matches the committed copy.

BLOCKING: 0
