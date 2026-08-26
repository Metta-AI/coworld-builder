blocking: 0

# Phase-60 verdict — knights-archers

Run: 2026-08-26-knights-archers · coworld 0.1.3 · cow_23e4f026-6724-4b80-bb34-dcd02c214ee2 ·
manifest sha256:d0773202419ec87be0fe873839c0f6be817b03ee21ca2dd95bf108b5512e91c6
Checklist: docs/SPEC.md §Definition of done, as commands in prompts/60-verify.md.
Judge read order: SPEC → 60-verify.md → own re-fetches → VERIFY.md → viewer-check artifacts.
Adjudicated 2026-08-26 ~15:47Z with independent re-fetches (noted per item); the ladder has
kept running since VERIFY.md's fetch window (rounds 4–6 completed after it), which changes
current leaderboard numbers but nothing VERIFY.md rests on.

## Verdict on the eight checks

| # | Check | VERIFY.md says | Judge verification | Stands? |
|---|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE — rounds 1,2,3 completed, fillers set 14:19:41Z before round 1 | **Re-fetched** `GET /rounds?league_id=…`: rounds 1–3 (now 1–6) all `completed`, `error null`, zero failed/discarded. `log.md:65–66` shows `filler-policies 200` on the line before `trigger-round 200`; round 1's episode seated `is_filler:true` policies, which per the playbook is impossible if fillers were absent at trigger. Rounds 2 and 3 alone satisfy the ≥2 bound under any reading. | TRUE |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE — daveey-1 rank 1, daveey rank 2, rounds_played 3 | **Re-fetched** `GET /divisions/…/leaderboard`: exactly two rows, `daveey` and `daveey-1`, both `rounds_played 6 ≥ 1` (ranks have swapped since 15:03Z — expected drift, both still ranked). No filler row; VERIFY.md pastes the elevated filler-policies read showing filler version ids (`eb972301-…`, `83dfcd5d-…`) distinct from both champion ids. | TRUE |
| 3 | Latest round's episode completed with replay | TRUE — round 3, `ereq_2e17e8b4` | **Re-fetched** `GET /episode-requests/ereq_2e17e8b4-…`: `status completed`, `replay_url` = the `ccba0605-…` S3 URL, participants exactly as pasted — daveey (warden:v3), daveey-1 (volley:v3), two `is_filler:true` seats. Byte-identical to VERIFY.md's paste. Round 3 was the latest completed round at fetch time (round 4 completed 15:17Z, after the 15:03Z pin). | TRUE |
| 4 | Replay bytes valid, champions really playing | TRUE — strict JSON via decoder, protocol match, complete, 36/36 llm, 0 fallbacks | **Re-fetched the replay bytes** (60084 B, magic `COWLDKAZ`) and **re-ran the decode myself** with `tools/replay_summary.py` fetched fresh from the repo: strict-JSON parse ok, `protocol knights-archers/v1`, `results.reason complete`, `teamKills 16`, per-seat directive sources `[{seat0: llm 18},{seat1: llm 18},{seat2: scripted 18},{seat3: scripted 18}]`, `fallbacks 0`, 72 directives total. Champion notes are real reasoning text ("Turn 1: Single zombie at [1163,40]…"), not boilerplate. The binary-format substitution is not ad hoc: `design.md` §Replay bytes declares it verbatim as "The phase-60 substitute for SPEC §Definition of done check 4" with exactly the commands VERIFY.md ran. | TRUE |
| 5 | Hosted game log clean | TRUE — 0 matching lines, raw and decoded, on round 3 | **Re-fetched** round 3's log (77134 B, same size): raw `grep -cE` = 0; my own per-container decode also 0 matching. Sidecar shows 36× `200 OK` to `bedrock-runtime.us-east-1.amazonaws.com`, matching check 4's 36 llm directives. The check passes on its **first branch** — no exception invoked; the round-2 outage section is documentation only, and its platform-wide nature is properly cross-checked against particle-worlds (different coworld, different image digest, same minute, same openrouter 402 → 503). | TRUE |
| 6 | Public page uses static replay path | TRUE — SSR playlist + session endpoint, static path, ready:true | **Re-fetched**: iframe grep on the page is still empty (client-rendered, as the prompt anticipates); page SSR payload still carries `playlist[0]` for coworld 0.1.3 (now r6.e1 — the ladder moved on); `POST /coworlds/replays/session` returns `viewer_url` = `…/v2/coworlds/replays/static/cow_23e4f026-…/sha256%3Ad0773202…/index.html?replay=<s3 url>&v=2`, `ready: true`, no `/client/replay` anywhere. The source substitution (SSR payload + session call instead of `/coworlds` `featured_match`) is explained and I confirmed its premise: `featured_match` is `null` for **every** canonical coworld right now (checked 10), so it is not evidence of absence for this one. VERIFY.md recorded which sources it used, as required. | TRUE |
| 7 | Certification declared static bundle | TRUE — committed release-result.json | **Read the committed file myself**: `jq -r '.certify.replay_liveness'` → `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`. Same file also shows `version 0.1.3`, `ok true`, matching cow id and manifest sha, `hosted_smoke passed`, `canonical true`, `errors []`. Source correctly named as the committed copy, never `/tmp`. | TRUE |
| 8 | Viewer executed and judged | TRUE — run 32982870977, loaded:true, three differing readouts, judgment paragraph | **Re-fetched the run**: 32982870977 `completed`/`success`, created 14:51:31Z (matches the claimed 14:51:29Z dispatch). Artifacts are committed (`acd61c0`). `viewer-smoke.json`: `loaded: true`, `data_replay_loaded "true"`, bridge `ready`, `failure: null`; scrub readouts 0%/50%/100% are three **differing, monotonically advancing** clocks (turn 0 → 9 → 14, clock 1:36 → 1:00 → 0:40). **I inspected viewer-smoke.png myself**: it shows a populated, legible horde-defence frame — knight plates (15/16 kills), archer plates (4/0 kills, 28 shots · 12 hits / 0), clock `0:30 TIME LEFT / WAVE 1/2 · 8 ALIVE · TURN 16/24`, `8 DEAD WALKING · LEADER 948PX` pressure bar, arena with the striped gate strip left, dark-red breach zone right with green zombies filing out, red heroes mid-board with speech bubbles, orange dashed closest-call line, and the starter's transport strip (rewind/play/+5s/step/loop/ffwd/spoilers, tick `1591 / 3396`, 1×–16× speeds) over a `KILLS vs HORDE PRESSURE` momentum scrubber — the starter's chrome, not a rewrite. The judgment paragraph matches what the png actually shows, including the honest nits (`player-N` plates, `feed_lines: 0`). | TRUE |

## The two substitutions, adjudicated

- **Check 8's `?replay=` parameter** (rendered round-2 replay `fb25d37a-…`, featured is now round-3
  `ccba0605-…`): declared explicitly in VERIFY.md §8(a), not hidden. The dispatch at 14:51:29Z
  preceded round 3's completion (14:55:33Z), so the src it tested **was** check 6's src at that
  moment. The two URLs differ only in `?replay=`; same cow id and same manifest sha — I confirmed
  this against the `url` field inside viewer-smoke.json. The second dispatch (32984003113, against
  the round-3 src) I re-fetched myself: **still `queued`** at 15:47Z, corroborating the
  exhausted-runner explanation. What check 8 proves — this coworld's live static bundle loads,
  draws, and advances on a real ladder replay — is proven. Not blocking.
- **Check 4's binary decode**: prescribed verbatim by the design note (§Replay bytes names it "the
  phase-60 substitute" and gives the exact commands). I re-ran the decode independently and got the
  same numbers. Not blocking.

## Non-blocking observations (concur with VERIFY.md §Observations)

- O1 (`turnSpacingMs` > `turnBudgetMs` latching fallback) is a real correctness finding for phase 30
  follow-up, but round 3 — the pinned evidence — is 36/36 llm with 0 fallbacks, so no check is
  falsified.
- O2 (`player-0…player-3` hero plates instead of names/aliases) is a legibility item for phase 30
  item 14; the judgment paragraph discloses it and the frame is otherwise legible and on-chrome, so
  check 8's gate (loaded + advancing + honest judgment) still holds.
- Trivial: VERIFY.md's header-block paste shows `"ndirectives":72` where the decoder emits the
  directives array (length 72) — same fact, cosmetic presentation; and one speech bubble the
  paragraph reads as `close` looks more like `loose`/`choke` in the png — both are recorded `say`
  values, immaterial.

## Blocking findings

None.

BLOCKING: 0
