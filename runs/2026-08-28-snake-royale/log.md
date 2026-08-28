# 2026-08-28-snake-royale — log

2026-08-28T03:01:27Z 00 claim 2026-08-28-snake-royale idea=1217748613361187 slug=snake-royale
2026-08-28T03:01:47Z 00 claim comment held after 20s re-read; no competing claim
2026-08-28T03:02:32Z 00 run task created gid=1217946798253412 section=Running subtasks=9 heartbeat_at set session=3b129f7e
2026-08-28T03:02:32Z heartbeat phase=10
2026-08-28T03:04:08Z 10 starter=coworld-ctf reason=simultaneous per-tick grid loop with new merged rules (not a bit-exact port of one env) — starter-table row 2; precedent matrix-games/paintball/hide-and-seek
2026-08-28T03:04:08Z 10 designer dispatched round=1
2026-08-28T03:24:46Z 10 designer returned design.md (1674 lines) round=1
2026-08-28T03:24:46Z 10 checklist: starter[x] num_agents[x]=4 resolution-order[x]1-15 scoring[x]placement-permille-zero-sum end-conditions[x]complete/deadline/fault observation[x] reply-caps[x]say24/notes160-rune both-policies[x]strangler/glutton+coil/forager parallel-batch+budget[x]640s degrade[x] name-spaces[x] viewer-static[x] viewer-one-starter[x]=coworld-ctf chrome-provenance[x]byte-for-byte+appended-block transport[x] zoom[x]dropped replay-self-sufficient[x] packaging[x]3-variants tests[x]49 out-of-scope[x] — ACCEPTED round 1
2026-08-28T03:24:46Z progress phase=10 marker=design.md written and accepted
2026-08-28T03:24:46Z 10 -> 20 phase transition
2026-08-28T03:24:46Z heartbeat phase=20
2026-08-28T03:25:54Z 20 repo created https://github.com/Metta-AI/cogame-snake-royale (public); propagate-secrets run=33138843164 green; SOFTMAX_TOKEN+ANTHROPIC_API_KEY present
2026-08-28T03:25:54Z 20 builder dispatched round=1
2026-08-28T03:25:54Z heartbeat phase=20
2026-08-28T05:19:14Z 20 builder returned: ci.yml green on main run=33144094331 sha=f985499c563359a169cf6f5bea31ef04ccf28985 (jobs test/docker-smoke/wasm-viewer all success; verified independently)
2026-08-28T05:19:14Z 20 note: builder used 4 red rounds (budget 3) — round 4 (offline sim replica to measure baseline ladder) produced the green; logged as budget overrun, phase succeeded
2026-08-28T05:19:14Z 20 note: git push over HTTPS refused for this repo from sandbox (No anonymous write access); builder pushed via Git Data API — carry this into fixer briefs
2026-08-28T05:19:14Z 20 deviations recorded for review: (1) design §Tests27 baseline-margin claim empirically false, replaced with measured pinned ladder in tools/ci/baseline_tuning.json; (2) broadcast_core.js fork-in-spirit (JSON frame wire vs sprite protocol); (3) replay_broadcast.html driver IIFE partly rewritten via scripts/build_replay_page.py audit trail; (4) bitworld dep dropped; (5) replay fixtures not committed (recipes tested); (6) killfeed allowlisted in endcard-vocab test; (7) renderer_fixture.html drives broadcast_core directly; (8) whole-second attempt1Ms/retryMs guard + head-on-loser corpse exception
2026-08-28T05:19:14Z 20 exit checks: placeholders none; 3 workflows parse+active; release inputs 4/4, submit inputs 3/3; release-result/submit-result/player hits; both hooks 100755
2026-08-28T05:19:14Z progress phase=20 marker=ci-run-33144094331-green
2026-08-28T05:19:14Z 20 -> 30 phase transition review_round=1
2026-08-28T05:19:14Z heartbeat phase=30
2026-08-28T05:19:59Z 30 reviewer dispatched round=1
2026-08-28T05:41:03Z 30 reviewer returned r1-review.md (861 lines, findings=25; hard-evidence: F1 scrubber s:<tick> parsed as fraction, F2 baseline ladder margin -0.097, F3 test13 loosened to tautology in 5537503, F5 worker OffscreenCanvas escapes canvas_text gate)
2026-08-28T05:41:03Z 30 fixer dispatched round=1
2026-08-28T05:41:03Z heartbeat phase=30
2026-08-28T07:00:02Z 30 fixer returned r1-fixes.md: 24/25 fixed one-commit-each, F20 refuted, F8 divergence recorded; main=d8652fa2d92b14a6da207d71076027f806f7849e CI run=33149313876 green
2026-08-28T07:00:02Z 30 judge dispatched round=1
2026-08-28T07:00:02Z heartbeat phase=30
2026-08-28T07:14:40Z 30 judge returned r1-verdict.md blocking:0/BLOCKING:0 agree — all 15 checklist items + batch rule PASS at d8652fa; residue advisory only (F8 documented divergence, F20 note inconsistency, margin band unreachable, gameversion-tripwire PR-only)
2026-08-28T07:14:40Z progress phase=30 marker=r1-verdict.md blocking=0
2026-08-28T07:14:40Z 30 -> 40 phase transition (review loop closed in 1 round)
2026-08-28T07:14:40Z heartbeat phase=40
2026-08-28T07:15:29Z 40 builder dispatched for release chain (version 0.1.0 first, budget 3 dispatches)
2026-08-28T07:34:11Z 40 builder returned: v0.1.0 run=33150809050 step_failed=certify (websocket Ping->Pong lost in fork; lux-ai scar repeated) -> code fix 93bc8f4+18b9da8 (second commit removed a TextMessage-only guard that dropped binary registration frames); v0.1.1 run=33151446939 SUCCESS
2026-08-28T07:34:11Z 40 release: canonical=true certify.ok=true replay_liveness=skipped(static) secret_put=true cow_id=cow_dfae8bd2-c198-460c-acaf-1c3fc709688c manifest_sha=sha256:7c10c697df9f3ce9cf043d3e3964fb31a97a7aa46d0720581188f0ae49795ca3; policies strangler:v1(daveey) glutton:v1(ply_bac48eb1) coil:v1 forager:v1; release-result.json persisted to run dir
2026-08-28T07:34:11Z 40 learning-candidate: Ping->Pong fork loss is a repeat (lux-ai 0.1.0, snake-royale 0.1.0) — starter tripwire test suggestion for phase 80 LEARNINGS
2026-08-28T07:34:11Z progress phase=40 marker=release-run-33151446939 v0.1.1
2026-08-28T07:34:11Z 40 -> 50 phase transition
2026-08-28T07:34:11Z heartbeat phase=50
2026-08-28T07:37:59Z 50 seed 200 league_9f435441-c018-419e-b8af-124d7a488081 (lseed_51f62146); /leagues returns bare array not .entries — filtered client-side
2026-08-28T07:37:59Z 50 division 200 div_9b84c813-77d9-41be-9fff-6e48af4cc474; settings 200 (round_robin, filler_policy, elo k32, 15min)
2026-08-28T07:37:59Z 50 champion1 submit run=33152011311 ok=true strangler:v1 ply_44ae9048; champion2 submit run=33152052887 ok=true glutton:v1 ply_bac48eb1
2026-08-28T07:37:59Z 50 policy-versions resolved: strangler=ccd1e387 glutton=c360e14f(daveey-1 confirmed) coil=f87382d5 forager=b21c23a0
2026-08-28T07:37:59Z 50 fillers 200 registered coil+forager only; unpause 200; trigger 200
2026-08-28T07:37:59Z 50 rounds: round1 failed instantly (created 07:36:02, pre-unpause artifact) — round2 pending round_b1b63f05 created 07:36:52 with both champions in entrant_attributions
2026-08-28T07:37:59Z progress phase=50 marker=league_9f435441 round_b1b63f05 pending
2026-08-28T07:37:59Z 50 -> 60 phase transition
2026-08-28T07:37:59Z heartbeat phase=60
2026-08-28T07:38:49Z 60 verifier dispatched (8 checks, 75-min round-wait bound)
2026-08-28T08:11:26Z 60 verifier returned VERIFY.md 8/8 TRUE (2 completed rounds b1b63f05+0ee7c3f1; leaderboard daveey-1 1030.53 / daveey 969.47 both rounds_played=2; replay complete/full_time fallback 0%; log CLEAN r3; static route manifest-sha match; viewer-check 33153918882 loaded=true clocks 0/26/50 differ)
2026-08-28T08:11:26Z 60 advisories carried to LEARNINGS: parse_error mislabels transport timeout; attempt1Ms=6000 tight vs haiku tail (r2 had 3 fallback lines); feed queue not flushed on seek
2026-08-28T08:11:26Z 60 judge dispatched for verify adjudication
2026-08-28T08:11:26Z heartbeat phase=60
