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
