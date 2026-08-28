blocking: 0

# verify verdict — hide-and-seek (phase 60)
Head: f12906f8c3149676226ff17c89f5df3b6cfef393   Checklist: prompts/60-verify.md §The eight checks / docs/SPEC.md §Definition of done   Independent read written before reading fixes: yes

Order of reading followed: `prompts/60-verify.md`, SPEC §Definition of done, the design note,
the rendered evidence (`viewer-check/viewer-smoke.png` + `viewer-smoke.json`, read and judged
before VERIFY.md), then VERIFY.md. No fixer report exists for phase 60; the audited document is
VERIFY.md itself. Every load-bearing claim was **re-fetched fresh by this judge** (03:0xZ,
after VERIFY.md's 02:43Z) — verdicts below rest on my fetches, not the verifier's paste.

## Standing blocking findings

None.

## Refuted

None to refute — VERIFY.md claims 8/8 TRUE and every claim survived my attempt to break it.
The three places I pressed hardest, and what I found:

1. **Check 1's "after the fillers" claim.** Round 2's `created_at` (02:15:03Z) is *before* the
   filler-policies POST (02:16:12Z, log.md:49) — the one soft spot in the whole file. But the
   check's substance is that counted rounds ran *with* the fillers, and both did: I fetched both
   episode requests fresh and both carry four `is_filler: true` seats
   (`ereq_60c137bb…` and `ereq_e221daea…` → fillers `hns-burrow`/`hns-scatter` ×3). Round 1 — the
   round that actually fired pre-filler — failed with the exact error VERIFY.md quotes verbatim
   (`Temporal RoundWorkflow failed before settling the round.`) and was excluded, not counted.
   Completed rounds are numbered 2 and 3, both after failed round 1. Stands as TRUE.
2. **Check 4's strict-JSON claim against binary bytes.** The S3 bytes are binary (`COWLDHNS`
   magic, first 8 bytes, checked myself). This is not a dodge: design.md §Replay bytes
   (design.md:1106–1132) declares the binary starter format and the exact phase-60 substitute
   (`tools/replay_summary.py` → one strict-UTF-8 JSON object), and SPEC's item-4 substance is met
   on my own run of it: parses strict, `protocol == "hide-and-seek/v1"`, `reason complete` /
   `endRule full_time` / `games 2`, champion seats made **40 LLM orders with 0 fallbacks**
   (`{"llm":40,"scripted":80}`, `fallbackTurns [0,0,0,0,0,0]`) — 0 is a small minority of 40.
   Locks 4 / grabs 3 non-zero. Stands as TRUE.
3. **Check 6's featured-match claim against the API's `featured_match: null`.** I re-fetched the
   page: no `<iframe>` in raw HTML (client-rendered, as VERIFY.md says), but the SSR payload
   carries `playlist":[{"episodeId":"f74b6625…","coworldName":"hide-and-seek",…,"roundNumber":3,
   "code":"hide-and-seek.r3.e1","matchup":{…daveey vs daveey-1…}}]` — featured match present. The
   session endpoint returns the static route
   `…/v2/coworlds/replays/static/cow_ccb33c23…/sha256%3Ac7efab01…/index.html?v=2#replay=<s3 url>`
   with `ready: true`; the sha equals `STATE.coworld.manifest_sha`; not a `/client/replay` pod
   URL. Stands as TRUE (the `?v=2#replay=` vs `?replay=` form variance is real and correctly
   flagged for the playbook; check 8 executed that exact string to `loaded: true`).

## Checklist pass (independent)

| item | status | evidence (my fetch, path:line or run) |
|---|---|---|
| 1. ≥2 completed rounds after fillers set | TRUE | `/rounds?league_id=…` fresh: rounds 2 (completed 02:21:56Z) and 3 (02:36:03Z); round 1 `failed`, error quoted; both counted rounds seated `is_filler:true` fillers (both ereqs fetched fresh); filler set fetched: `hns-burrow:v3`/`hns-scatter:v3`, version ids match STATE, neither a champion |
| 2. Both champions ranked, fillers absent/Baseline | TRUE | leaderboard fresh: `1 daveey hns-quartermaster:v3 1030.53 rounds_played=2`, `2 daveey-1 hns-torchbearer:v3 969.47 rounds_played=2`; exactly two rows, fillers absent |
| 3. Latest round's ereq completed with replay | TRUE | `ereq_60c137bb…` fresh: `status completed`, `replay_url` = s3 `2b8607e0….replay`, seat 0 daveey / seat 1 daveey-1, seats 2–5 `is_filler:true` |
| 4. Replay bytes valid, show the game | TRUE | fetched 85 815 bytes (HTTP 200, magic `COWLDHNS`); ran `replay_summary.py` myself: strict JSON ok, `hide-and-seek/v1`, `complete`/`full_time`, names `["daveey","daveey-1","Baseline",…]`, 40 champion LLM orders, **0 fallbacks**, locks 4, grabs 3 |
| 5. Hosted game log clean | TRUE | fetched round-3 log myself (HTTP 200, 84 312 B); grep of the four patterns on the **raw** body: zero matches → CLEAN. Round 2's single degrade is a recorded observation on a non-latest round, correctly not a check-5 failure |
| 6. Public page uses static replay path | TRUE | page SSR playlist (featured r3.e1, daveey vs daveey-1) + session endpoint `viewer_url` = static `/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html`, `ready: true`, never `/client/replay` |
| 7. Certification declared static bundle | TRUE | committed `runs/2026-08-27-hide-and-seek/release-result.json` → `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`; same cow_id + manifest_sha as check 6 |
| 8. Viewer executed, then judged | TRUE | run 33136591103 `conclusion: success` (checked via gh); `viewer-smoke.json`: `loaded:true`, `data_replay_loaded:"true"`, `failure:null`, three scrub clocks **differ** (tick 947 g1 → 2267 g2 → FINAL 3584); I looked at the png myself — see below |

**My own read of `viewer-smoke.png`** (formed before reading VERIFY.md): a legible endcard —
FINAL / GAME OVER, `EPISODE +0.140 / −0.140`, banner `BOTH SIDES HIDDEN — EXPOSURE DECIDED`,
two per-seat tables (HIDERS 1490 ticks unseen: TORCHBEARER/HIDER-alpha 81/640/4 locks;
SEEKERS 1466: QUARTERMASTER/SEEKER-alpha 721/0) over the rendered warren room, with the
starter's transport strip (restart/step/play/`+5s`/loop/ffwd, `spoilers` toggle, `2637 / 2640`,
`1×–16×` chips) and a scrubber with event beats and a `HIDDEN LEAD` momentum graph that runs red
then blue. It reconciles digit-for-digit with my own summary output: seen column 0/640/457/33/240/0
= `seatSeenTicks`, `+0.140/−0.140` = `scores`, `-495/-775` = `gameMargins`, 4 locks on
HIDER-alpha = `locks`. It is the starter's chrome retargeted, not a rewrite — not the
cogame-gridlock failure mode. The spectator-judgment paragraph in VERIFY.md is present, accurate,
and honest about its two legibility nits (`TICK 3584/2160` overflow in game 2; all-zero first
frame) — both correctly non-blocking.

## Verifier report audit

| claim in VERIFY.md | verifier said | I verified | agrees |
|---|---|---|---|
| completed rounds | 2 (rounds 2, 3), round 1 failed excluded | fresh fetch: identical (plus round 4 now pending) | yes |
| both counted rounds seated fillers | is_filler:true seats in both ereqs | fetched both ereqs fresh: 4 filler seats each | yes |
| leaderboard | daveey 1030.53 / daveey-1 969.47, rounds_played 2/2, two rows | fresh fetch: identical | yes |
| ereq_60c137bb | completed, replay_url, champions seats 0–1 | fresh fetch: identical | yes |
| replay | strict-JSON summary, 40 LLM / 0 fallbacks, complete | fetched bytes + ran summariser myself: identical numbers | yes |
| round-3 log | CLEAN | raw grep on my own fetch: zero matches | yes |
| round-2 log not clean (observation) | 1 `falling back` at seat 1 turn 5 | consistent with round-2 replay `fallbackTurns [0,1,0,0,0,0]` as pasted; not re-fetched (non-load-bearing: check 5 is defined on the latest round) | yes |
| featured match + static iframe | SSR playlist r3.e1; session endpoint static URL, ready:true | fresh fetch of both: identical | yes |
| release-result.json liveness line | present | read committed file myself | yes |
| viewer-check run | 33136591103 success, loaded:true, 3 differing clocks | `gh run view`: success; json + png read myself | yes |

## Non-blocking observations

- The `?v=2#replay=` fragment form (vs the prompt's `?replay=` query) should be folded into
  `playbooks/observatory-api.md`, as VERIFY.md itself flags.
- The two legibility nits (tick-counter overflow past game 1; all-zero scorebug for the first
  ~5 s) are phase-30-grade polish items for a future version, not DoD failures.
- `feed_lines: 0` in viewer-smoke.json is the early-sample artifact VERIFY.md explains; the png
  shows the directive feed populated.

BLOCKING: 0
