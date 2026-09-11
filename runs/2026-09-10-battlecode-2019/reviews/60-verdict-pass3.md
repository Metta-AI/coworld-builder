blocking: 0

# 60 verdict (pass 3) — battlecode-2019

**Headline: All eight definition-of-done checks independently re-verified TRUE at the current head (coworld 0.11.6 / `cow_d8457b5a-acbd-4112-acee-bca7082b654f`, round 8); pass 3's verdicts stand, no finding blocks announce/close.**

BLOCKING: 0

Judge: fresh context. Reading order honoured: SPEC §Definition of done → `prompts/60-verify.md` →
design note (grep/ranged) → **independent platform fetches and notes** → only then VERIFY.md pass 3.
Independent read written before reading pass 3: **yes** (all API fetches, replay parses, log decodes,
leaderboard, page fetch, and the png viewing below were done before opening VERIFY.md lines 881+).
Every number below is from my own fetches on 2026-09-11 ~09:55–10:05Z, not copied from VERIFY.md.

---

## The eight checks — my own verdicts

### 1. ≥2 completed rounds after fillers were set — **TRUE** (agree with pass 3)

```
GET $BASE/rounds?league_id=league_1ce0515e-…&limit=20
1  round_aa77a013  completed  2026-09-10T23:16:10Z
2  round_6acab2f9  completed  2026-09-11T00:50:31Z
3  round_d4748b8f  completed  2026-09-11T05:59:26Z
4  round_3212ddbc  completed  2026-09-11T06:07:08Z
5  round_c371eeca  failed     "only 4/6 planned slots produced scoring evidence; …at most 0%…"
6  round_d984ec42  failed     "only 3/6 planned slots produced scoring evidence; …"
7  round_9f125158  failed     "only 2/6 planned slots produced scoring evidence; …"
8  round_113f3531  completed  2026-09-11T09:39:09Z
```
Five completed rounds; fillers were registered 2026-09-10T13:35:00Z (log.md: `POST /leagues/$L/filler-policies
200 … set BEFORE any trigger`), before round 1 was even created (22:56:56Z). Failed rounds 5–7 recorded
with verbatim errors, matching pass 3's quotes byte-for-byte.

### 2. Both champions ranked — **TRUE** (agree)

```
GET $BASE/divisions/div_f794f180-…/leaderboard   (bare list)
1  Games Bond  gb-bc19-preach:v1                  1048.01  rounds_played=1  wins=3
2  daveey-1    battlecode-bc19-preachers:v1       1039.12  rounds_played=5  wins=7
3  daveey      battlecode-bc19-saber:v1           1000.85  rounds_played=5  wins=6
4  docxology   daf-battlecode-carrier-doctrine:v2  912.02  rounds_played=5  wins=2
```
Both champions ranked with `rounds_played=5 ≥ 1`; neither filler (`battlecode-saber:v1`,
`battlecode-examplefuncsplayer19:v1`) appears. Two third-party entrants — normal for a public league.

### 3. Latest round's episode request completed with a replay — **TRUE** (agree, see Q1)

Latest completed round = 8. `GET $BASE/rounds/round_113f3531-…/episode-requests` (flat form is 405):
all **six** entries `status=completed` with non-null `replay_url`. `entries[0]` = `ereq_68c7522e`
(daveey-1 vs Games Bond) — completed, replay `8b4a5124…`, but names only one champion. The
champion-vs-champion episode:
```
GET $BASE/episode-requests/ereq_7c51f79f-b2cd-45b5-b024-cff817666648
status=completed  replay_url=…/replays/cf3635bd-1a84-4d3e-8a27-bd62808cf69f.replay
participants: daveey / battlecode-bc19-saber v1 (35935ce8…), daveey-1 / battlecode-bc19-preachers v1 (d179231c…)
coworld_id=cow_d8457b5a-…  coworld_version=0.11.6  episode_id=8cdcae74-…
```
This is the only round-8 episode that satisfies the check's own "participants naming daveey **and**
daveey-1" requirement. Matches STATE.verify.replay exactly.

### 4. Replay bytes valid and show the game — **TRUE** (agree)

Downloaded `cf3635bd….replay` (79,385 bytes) and strict-parsed with Python `bytes.decode('utf-8')` +
`json.loads` (not a browser): **ok**. `protocol=cogame.battlecode.v1` (design-pinned id), `year=bc19`,
`result.reason=complete`, 2 games (2–0 clinch, declared legal in design §clinch semantics), both
`end_reason=more_castles` at `rounds_played=1000`. Doctrine events:
```
doctrine_received slot 0 attempt 1 latency 40000ms defaults_applied 0 unknown_fields 4
doctrine_retry    slot 1 cause timeout
doctrine_received slot 1 attempt 2 latency 7904ms  defaults_applied 0 unknown_fields 0
result.fallbacks = [0,0]; seats[*].fallback = null; policy_kind ["llm","llm"]
```
Both champion sheets are distinct, non-trivial LLM content (slot 0 `opening:pilgrim_eco, pilgrim_curve:14,
church_expansion:early…`; slot 1 `opening:preacher_rush, preacher_share:60, church_expansion:never…`).
Zero fallbacks — not merely "a small minority". I also re-verified pass 3's quoted game-0 stat block
(`units_built [8,38], pilgrims_built [3,12], crusaders_built [2,10], prophets_built [3,0], attacks [21,38],
kills [4,9]`) — matches byte-for-byte, and 98 events including duels, church_built, preacher_splash,
castle_lost, tiebreak.

### 5. Hosted game log is clean — **TRUE** (agree)

I fetched **all six** round-8 log artifacts with `AUTH+ELEV`, split on `===== container: … =====`,
decoded each `b'…'` body with `ast.literal_eval(...).decode()`, and grepped **every container** (not
just `game`) for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`:
```
ereq_68c7522e  CLEAN   ereq_03f14b7a  CLEAN   ereq_7c51f79f (designated)  CLEAN
ereq_9edc55b6  CLEAN   ereq_e7496745  CLEAN   ereq_a7fd21a9  CLEAN
```
Three episodes (`7c51f79f`, `a7fd21a9`, `e7496745`) each carry one `seat 1 attempt 1 failed, will
retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/…` followed by a successful
retry and `settled: complete` — a recovered retry is not a forbidden pattern and each replay's
`fallbacks=[0,0]` confirms no fallback resulted. Manifest scope containment independently confirmed
from `GET $BASE/coworlds/$COW`: bc19 = `attempt1Ms 40000 / retryMs 24000 / doctrineBudgetMs 75000 /
maxOutputTokens 3000 / num_agents 2`; **all nine** other variants = `20000/12000/45000`, `maxOutputTokens`
key **absent**. Pass 3's per-episode seeds (336221280/281/282) and scores match my fetched logs exactly.

### 6. Public page uses the static replay path — **TRUE** (agree)

`curl https://softmax.com/battlecode/bc19` → no `<iframe` in raw HTML (client-rendered, as the prompt
anticipates). SSR payload fallback, my own fetch:
```
"state":{"leagueId":"league_1ce0515e-…","playlist":[{"episodeId":"d8b62e6f-…",
 "coworldId":"cow_d8457b5a-…","coworldVersion":"0.11.6",
 "replayUrl":"…/replays/8b4a5124-2ea5-4e1f-9f63-3bff84cbeb5e.replay","roundNumber":8,
 "inspectUrl":"…episode-request:ereq_68c7522e-…"}]
```
Featured match present and **current** (round 8, canonical coworld). The viewer URL the check-8 run
actually loaded (from committed `viewer-smoke.json`):
`https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_d8457b5a-acbd-4112-acee-bca7082b654f/sha256%3A83648d8f…/index.html?v=2#replay=…8b4a5124….replay`
— the static route carrying exactly the canonical cow_id + manifest sha, never `/client/replay`. I
GET'd that URL myself: **HTTP 200**, 389,344 bytes, a `data-coworld-replay-bootstrap` script that
rewrites `#replay=` into `?replay=` (so the `#replay` form is the platform's current shape of the
same static route). I did not repeat pass 3's `POST /coworlds/replays/session` (judge is read-only);
the GET plus the executed viewer-check against the same URL verify the same fact.

### 7. Certification declared the static bundle — **TRUE** (agree)

Committed `runs/…/release-result.json` (byte-identical to `release-result-0.11.6.json`, `diff` clean):
```
jq -r '.certify.replay_liveness'  →  Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
version=0.11.6  cow_id=cow_d8457b5a-…  manifest_sha=sha256:83648d8f…  ok=true  canonical=true  step_failed=null  errors=[]
```
Also re-fetched live: `GET $BASE/coworlds/$COW/certification` → `state=certified, certified=true,
failed_step=null`; and `GET $BASE/coworlds?limit=200` → 0.11.6/`cow_d8457b5a` is the **newest**
battlecode row and the **only** canonical one.

### 8. Spectator judgment, viewer executed — **TRUE** (agree)

GitHub run `34585977572` (viewer-check.yml, created 2026-09-11T09:47:25Z — after 0.11.6 went
canonical 09:08Z and round 8 completed 09:39Z): `conclusion=success`. I re-downloaded its artifact
and md5-compared against the committed `runs/…/viewer-check/`: **byte-identical** (json
`60d34643…`, png `ebb60605…`). Readouts:
```
loaded=true  ms=2088  signals={data_replay_loaded:"true", data_replay_error:null, bridge:["ready"]}
0%   1:23 GAME 1 OF 2 — SEED-0001 doctrines
50%  0:41 GAME 2 OF 2 — SEED-0060 doctrines
100% FINAL MATCH OVER doctrines
failure: no failure
```
Three genuinely differing readouts; reconciled against my own parse of the rendered replay
(`8b4a5124`: game 0 map `seed-0001`, game 1 map `seed-0060`, both `more_castles`, points game 2
`[22,77]`, scores `[29.5,469.5]` → on-screen "22/77", "score 30 — 470"). I viewed the committed png
myself: a legible dark endcard in the starter's chrome — scorebug strip ("CLAN ASH · daveey-1 22 ·
FINAL MATCH OVER · CLAN BASIL · Games Bond … 77"), winner banner "CLAN BASIL — GAMES BOND" with "THE
GAME ENDED ON MORE CASTLES IN GAME 2, ROUND 1000", two side-by-side free-text doctrine panels
(genuinely different: 150 vs 200 fuel reserve, range-squared 100 vs 80, distinct motto), per-side
stat blocks, an event feed on the right (CASTLE DOWN / preacher blasts with round numbers), transport
strip + scrubber + "round 1000 / 1000" + speed buttons. It shows the game and is not empty, static,
or a different product.

---

## The six questions

**Q1 — designated episode vs `entries[0]`.** Round 8's `entries[0]` is `ereq_68c7522e` (daveey-1 vs
third-party Games Bond): it *cannot* satisfy check 3's own requirement that participants name both
`daveey` and `daveey-1`. The only round-8 episode that can is the champion-vs-champion
`ereq_7c51f79f`, which is what pass 3 designates. The substitution is **declared explicitly** in
VERIFY.md (check 3, "Designated episode for checks 3/4/5 this pass … chosen because it is the only
round-8 episode that literally satisfies…"), and it made the pass **harder, not easier**: pass 3
verified *both* episodes on checks 3/4 and all six on check 5, and the designated episode is one of
the three whose log carries a retry line — `entries[0]`'s log is the cleaner of the two. No
cherry-pick.

**Q2 — rounds 5–7 failures.** Genuinely external. I fetched all nine failed episode-requests across
rounds 5–7: every one has `episode_id: null` (no episode was ever created) and an httpx
transport-layer error (`RemoteProtocolError (HTTP status unavailable)`, `ReadError (HTTP status
unavailable)`, one `Coworld relay request attempt 1/4 failed with RemoteProtoc…`); their "logs"
artifact is a 64-byte error stub with **no containers** — this coworld's code never ran for those
slots. Same-window cross-check from `GET $BASE/rounds?limit=100` (all leagues): between ~08:50 and
~09:25Z many unrelated leagues' rounds failed with the identical `only N/M planned slots produced
scoring evidence` error (e.g. rounds numbered 32/33/34 of a 12-slot league, 104/105 of a 20-slot
league, 1880 of a 24-slot league, 6711/6712, 1363/1364, 5382–5386…), recovering to completed across
the board by ~09:30Z. Round 8 then ran 6/6 clean at 09:39Z. Nothing implicates bc19's own code; the
completed episodes inside the failed rounds all settled `reason=complete`.

**Q3 — is check 5's TRUE earned or lucky?** Earned. I decoded **all six** round-8 logs myself
(every container): zero occurrences of any forbidden pattern in any of them — not one lucky episode
but a clean sweep (12/12 champion-and-third-party seats, `fallbacks=[0,0]` in both replays I
parsed). The two prior failure modes map onto the two fixes: the 20000 ms attempt-1 timeouts of
passes 1–2 are gone (attempt-1 latencies observed up to the new 40000 ms bound, e.g. slot 0 at
exactly 40000 ms, delivered clean), and no `cut off at max_tokens` appears anywhere post-3000-token
cap (log.md 09:23Z records six-of-six first-attempt parse failures under the old 1200 cap in rounds
3–4). Caveat honestly recorded: round 8 is one round; a provider 503 storm would still produce
fallbacks by design (round 5's `ereq_9fe1a837` did, inside the documented platform-branch of check
5, in a round that failed for external reasons anyway). The check as specified judges the designated
episode's log — clean — and pass 3 over-delivered by proving all six.

**Q4 — is the pinned evidence the new artifact set?** Yes. `viewer-smoke.json`'s `url` carries
`cow_d8457b5a` and `sha256%3A83648d8f…` (the current canonical pair, not `cow_5657f03c`). The
committed `viewer-check/` files are **md5-identical** to the artifacts of run `34585977572`
(created 09:47:25Z, success) which I re-downloaded myself. Structurally impossible to be the old run
34544098607's output: the png features **Games Bond**, who first appears in round 8.

**Q5 — is the rendered replay a bc19 episode of this league?** Yes. The rendered replay
`8b4a5124…` is round 8's `ereq_68c7522e` in `league_1ce0515e` (the page payload's
`state.leagueId` and `inspectUrl` name it; my API fetch of that ereq returns the same replay_url,
`coworld_version 0.11.6`, variant "Battlecode 2019 — Crusade"); the replay JSON itself reads
`year: bc19`. Not a bc26 sibling.

**Q6 — `loaded: true` and three differing clocks?** Yes. `loaded:true`, `data_replay_loaded:"true"`,
bridge `["ready"]`, no error, `failure: no failure`; and the three scrub readouts differ genuinely —
mid-game-1 (`1:23 … SEED-0001`), mid-game-2 (`0:41 … SEED-0060`), endcard (`FINAL MATCH OVER`) —
i.e. the replay advances across games, not one frozen frame.

---

## Fixer/verifier report audit

| pass-3 claim | I verified | agrees |
|---|---|---|
| 0.11.6/cow_d8457b5a canonical, certified, sha 83648d8f | coworlds list + detail + certification fetched | yes |
| 5 completed rounds, 3 failed w/ verbatim errors | rounds list fetched | yes, byte-identical |
| leaderboard rows (4 players, both champions rounds_played=5) | leaderboard fetched | yes, byte-identical |
| all 6 round-8 ereqs completed w/ replay_url | nested endpoint fetched | yes |
| designated replay: strict JSON, complete, fallbacks [0,0], doctrine events | downloaded + parsed | yes, incl. stat block |
| all 6 logs CLEAN; 3 recovered retries; seeds 336221280/281/282 | all 6 fetched + decoded | yes |
| bc19 config 40000/24000/75000/3000; 9 siblings 20000/12000/45000/absent | manifest fetched | yes |
| SSR playlist[0] = round 8 / 0.11.6 / 8b4a5124 | page fetched | yes |
| static viewer URL carries cow_d8457b5a + sha 83648d8f | URL GET 200 + viewer-smoke.json | yes |
| release-result.json liveness-skipped, 0.11.6 fields | committed file read | yes |
| run 34585977572 green; artifacts committed | gh run view + re-download + md5 | yes |
| png: endcard, doctrine panels, feed, transport strip | viewed png myself | yes (two nits below) |

## Refuted findings

None to refute — pass 3 contains no finding I could show wrong, overstated, or stale, and my
independent pass surfaced no blocking finding pass 3 missed.

## NON-BLOCKING observations

1. **VERIFY.md line 1 still reads "Verdict: 1 item false"** (pass-2's header). Pass 3 is appended
   with a superseding summary as the brief sanctions, but a reader parsing only the head of the file
   gets a stale verdict. Worth a one-line pointer at the top ("superseded by Pass 3, below") next
   time a multi-pass VERIFY.md ships.
2. Only **one** completed round (8) ran under 0.11.6 itself; the ≥2-completed-rounds item is
   satisfied by rounds 1–4+8 of the same league with the same submitted champion policy-versions
   (:v1, 35935ce8/d179231c) across config-only re-releases. SPEC item 1 pins "after the fillers were
   set", not "under the final version", so this is compliant — recorded so nobody later mistakes
   round 8 for two.
3. Two trivial slips in pass 3's screenshot prose: the speed buttons end at **16×**, not "15×", and
   the two doctrine panels differ in *three* particulars (fuel 150/200, range-squared 100/80, motto),
   not "only" two — the extra difference strengthens, not weakens, the two-independent-LLM-outputs
   point.
4. Every round-8 `game` container logs `refused a seat-0 connection: seat 0 was given the wrong
   connection token` once before the real seat connects; harmless (the real seat then connects and
   registers) and present in all six episodes, but if it is a platform double-dial it will show up in
   every future log grep — worth knowing it is expected noise.
5. The static route's current shape is `index.html?v=2#replay=<url-encoded>` with an in-page
   bootstrap that rewrites `#replay=` → `?replay=`; SPEC §DoD item 6's literal `?replay=` text is
   one platform rev behind. A SPEC touch-up would spare a future verifier the reconciliation.
6. `error_type` on the rounds-5–7 failed ereqs is inconsistently `crash` vs `config_error` for the
   same transport error text — platform-side labelling noise, recorded here so the `config_error`
   rows are not misread as a bc19 manifest problem.

## What I could NOT verify, and why

- **Pass 3's hourly platform-completion table** (paged `/rounds` back to 2026-09-09): I reproduced
  only a 100-row window around the incident, which confirms the qualitative shape (many leagues
  failing 08:50–09:25Z, recovery by ~09:30Z) but not the exact hourly percentages. Direction
  corroborated; exact figures taken as pass 3's own measurement. Not a checklist item.
- **Rounds 1–4 historical fallback tallies** quoted in pass 3's check-5 "historical context": I did
  not re-fetch rounds 1–4 logs; they are explicitly non-load-bearing history under superseded
  versions. Not a checklist item.
- **`POST /coworlds/replays/session`**: not re-issued (judge is read-only against the platform).
  Verified equivalently by GET-ing the returned static URL (200, coworld-replay bootstrap) and by
  the executed viewer-check having loaded exactly that URL.
- **A live browser render of softmax.com/battlecode/bc19's DOM iframe**: no browser in this sandbox;
  verified via the SSR payload + the static URL + the CI-executed render, which is precisely the
  evidence path `prompts/60-verify.md` prescribes for client-rendered pages.

None of the above leaves a checklist item unverified: all eight items are verified from my own
fetches or from committed, re-downloaded CI evidence.

BLOCKING: 0
