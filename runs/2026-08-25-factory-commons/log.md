# 2026-08-25-factory-commons — log

2026-08-25T14:01:23Z 00 claim 2026-08-25-factory-commons idea=1217762644722022 slug=factory-commons
2026-08-25T14:01:43Z 00 claim comment held after 20s re-read — no competing claim
2026-08-25T14:02:43Z 00 run task created gid=1217829066796692 section=Running, 9 phase subtasks created, heartbeat_at=2026-08-25T14:02:43Z
2026-08-25T14:02:43Z 00 -> 10 phase transition, STATE phase=10 session=a4f7c2d1
2026-08-25T14:07:00Z 10 starter=coworld-ctf — per-tick grid loop (move/grasp/drop/press) with rules written for this coworld; Melting Pot Lua is reference material, not a bit-exact port target (moba row rejected); parley row rejected (not turn-based/talk)
2026-08-25T14:07:00Z 10 designer dispatched: design note -> runs/2026-08-25-factory-commons/design.md
2026-08-25T14:22:57Z 10 designer returned round 1: design.md 1266 lines, all 8 H2 sections present
2026-08-25T14:22:57Z 10 checklist: starter[x] num_agents=3[x] tick-order[x] scoring[x] end-conditions[x] observation[x] reply-schema+caps+rune[x] both-policies[x] parallel-batch-631s<720s[x] degrade-never-hang[x] two-namespaces[x] viewer-static-wasm[x] viewer-4-files-coworld-ctf[x] chrome-provenance+zoom-dropped[x] transport-rules[x] replay-self-sufficient[x] packaging-docs-protocols[x] tests-incl-executed-viewer-smoke[x] out-of-scope[x] — ACCEPTED round 1
2026-08-25T14:22:57Z progress phase=10 marker=design.md
2026-08-25T14:22:57Z 10 -> 20 phase transition, STATE phase=20
2026-08-25T14:22:57Z heartbeat phase=20
2026-08-25T14:24:06Z 20 repo created: https://github.com/Metta-AI/cogame-factory-commons (public)
2026-08-25T14:24:06Z 20 propagate-secrets run 32859209291 success; gh secret list shows SOFTMAX_TOKEN + ANTHROPIC_API_KEY
2026-08-25T14:24:06Z 20 builder dispatched round 1
2026-08-25T16:19:00Z 20 pushed 6d6ba8b (initial build) -> ci.yml run 32871176243 dispatched
2026-08-25T16:30:13Z 20 pushed fb3e4ac -> run 32871512297 failure (doc comments in expressions, GC-safe stubs); fixed
2026-08-25T16:30:13Z 20 pushed 87ea426 -> run pending (shadowed module names, std/json, cert fixture capMin for the soak)
2026-08-25T16:39:00Z 20 pushed 87ea426 -> run 32872320408 failure (module-name shadowing, missing std/json); docker-smoke GREEN
2026-08-25T16:47:00Z 20 pushed 6d3887c -> run 32873190436 failure (missing std/tables; renderer fixture fought its own design); docker-smoke + wasm-viewer GREEN
2026-08-25T16:56:00Z 20 pushed e9ccce0 -> run 32873913589 SUCCESS (shift/end events now land inside the recorded frames)
2026-08-25T17:05:00Z 20 pushed 62681ee -> run 32874694256 SUCCESS (two legibility fixes read off the smoke screenshot) — CLAIMED GREEN
2026-08-25T17:37:40Z 00 resume at phase 20 attempt=1 session=d409ba88
2026-08-25T17:39:13Z 20 exit checks pass on 62681ee: placeholders clean, 3 workflows parse+active, release/submit inputs present, release-result+submit-result artifacts present, champion#2 player field present
2026-08-25T17:39:13Z 20 -> 30 phase transition, STATE phase=30 review_round=1
2026-08-25T17:39:13Z heartbeat phase=30
2026-08-25T17:39:39Z 30 reviewer dispatched round 1 (repo checkout /tmp/cogame-factory-commons @ 62681ee)
2026-08-25T17:59:10Z 30 reviewer returned round 1: r1-review.md 513 lines, 1 blocking (B1 replay re-derivation test) + 18 non-blocking + 4 undetermined
2026-08-25T17:59:10Z 30 fixer dispatched round 1
2026-08-25T17:59:10Z heartbeat phase=30
2026-08-25T21:19:09Z 00 resume at phase 30 attempt=1 session=ee652d74
2026-08-25T21:20:13Z 30 fixer returned round 1 (found by resume): r1-fixes.md written, 9 commits, CI green run 32883915882 at 0079af8
2026-08-25T21:20:13Z 30 judge dispatched round 1 (fresh checkout /tmp/cogame-factory-commons-judge @ 0079af8)
2026-08-25T21:34:46Z 30 judge returned round 1: r1-verdict.md blocking: 0 / BLOCKING: 0 — loop exits after 1 round
2026-08-25T21:34:46Z progress phase=30 marker=r1-verdict.md
2026-08-25T21:34:46Z 30 -> 40 phase transition, STATE phase=40
2026-08-25T21:34:46Z heartbeat phase=40
2026-08-25T21:35:17Z 40 builder dispatched: coworld-release.yml version 0.1.0, canonical policy set from tools/ci/policies.json
2026-08-25T21:56:41Z 40 dispatch 1: version 0.1.0 run 32901879174 step_failed='Put the Coworld secret' (404: coworld registered as game.name factory_commons, step used $SLUG) — workflow fix 4b6a074 derives coworld_name from manifest game.name
2026-08-25T21:56:41Z 40 dispatch 2: version 0.1.1 run 32902713785 SUCCESS — ok/canonical/secret_put true, certify ok, replay_liveness skipped-static, 4 policies v2, champion2 player ply_bac48eb1; release-result.json copied into run dir
2026-08-25T21:56:41Z progress phase=40 marker=32902713785
2026-08-25T21:56:41Z 40 -> 50 phase transition, STATE phase=50
2026-08-25T21:56:41Z heartbeat phase=50
2026-08-25T22:08:38Z 50 note: git push over HTTPS unauthenticated in this sandbox — coworld-builder writes go via GitHub Git Data API (gh api), tree byte-identical
2026-08-25T22:08:38Z 50 seed POST /coworld-league-seeds 200 (coworld_name=factory_commons — game.name, not slug; slug 404d) league=league_96744093-0ddc-42dc-b5bf-79f195f062f0
2026-08-25T22:08:38Z 50 division PUT 200 div_8b8d506b-926f-4633-bc3d-ce6dc08a2568; settings POST 200 (elo, round_robin, filler_policy, 15min)
2026-08-25T22:08:38Z 50 champion1 submit run 32904302824 success ok:true sub_6600a2c4-00d2-48bb-961e-848d01376ef0 (daveey, factory-commons-foreman:v2)
2026-08-25T22:08:38Z 50 champion2 submit run 32904352497 success ok:true sub_d0d20eb5-dcb0-459c-a27f-0ff91035f2f2 (daveey-1, factory-commons-custodian:v2)
2026-08-25T22:08:38Z 50 fillers POST 200: steward:v2 a2b2de4d-7127-4b05-b309-121ce2e5b381, stripper:v2 f1071ff6-212d-4146-949b-ed297dd69b0b (champions excluded)
2026-08-25T22:08:38Z 50 unpause 200; trigger-round 200; rounds: r1 failed (Temporal RoundWorkflow — scheduled pre-fillers), r2 pending with both champions in entrant_attributions
2026-08-25T22:08:38Z progress phase=50 marker=league_96744093-0ddc-42dc-b5bf-79f195f062f0
2026-08-25T22:08:38Z 50 -> 60 phase transition, STATE phase=60
2026-08-25T22:08:38Z heartbeat phase=60
2026-08-25T22:09:11Z 60 verifier dispatched (league league_96744093-0ddc-42dc-b5bf-79f195f062f0, division div_8b8d506b-926f-4633-bc3d-ce6dc08a2568, cow cow_2e5dc1a2-c660-4c7b-83a1-3881b4071786)
2026-08-25T22:10:49Z 60 poll: rounds r1 failed (pre-fillers, does not count), r2 pending; leaderboard/playlist empty; check 7 TRUE from committed release-result.json; public page = softmax.com/factory-commons (hyphen) 200 with SSR payload, softmax.com/factory_commons is the generic Watch shell
2026-08-25T22:10:49Z heartbeat phase=60
2026-08-25T22:22:40Z 60 poll: r2 completed 22:12:11 (ereq_22d6a471 completed, replay ok, results.reason=complete/shift_limit, fallbacks [9,13,0] from platform-wide Bedrock 429 "Too many tokens per day" — cross-checked coins+ecos same message); r3 pending; viewer-check run 32905429599 loaded:true, 3 differing clocks
2026-08-25T22:22:40Z heartbeat phase=60
2026-08-25T22:28:56Z 60 poll: r3 completed 22:23:29 (ereq_c415d0f9, replay 3facae4f, reason=complete/factory_ruined, fallbacks [0,0,0] — throttle cleared, hosted log CLEAN on all four grep patterns); leaderboard daveey 1001.47 rp=2 / daveey-1 998.53 rp=2, no fillers; waiting on r4 for the final snapshot
2026-08-25T22:28:56Z heartbeat phase=60
2026-08-25T22:43:29Z 60 poll: r4 pending (created ~22:35); r2+r3 completed; waiting to snapshot the latest completed round for checks 3-6/8
2026-08-25T22:43:29Z heartbeat phase=60
2026-08-25T22:58:16Z 60 poll: r4 completed 22:49:14 (ereq_558ec460, replay 83ef5ad4, 900 frames, reason=complete/shift_limit, fallbacks [0,0,0], hosted log CLEAN); 3 completed rounds (2,3,4)
2026-08-25T22:58:16Z 60 check 1 TRUE (rounds 2,3,4 completed; r1 failed pre-fillers, error quoted)
2026-08-25T22:58:16Z 60 check 2 TRUE (daveey-1 1014.67 rp=3 / daveey 985.33 rp=3; fillers absent)
2026-08-25T22:58:16Z 60 check 3 TRUE (ereq_558ec460 completed, replay_url non-null, daveey+daveey-1 named, steward is_filler)
2026-08-25T22:58:16Z 60 check 4 TRUE (strict jq parse ok, protocol factory_commons.replay.v1, reason complete, 30/30 champion orders source=llm, 0 fallbacks)
2026-08-25T22:58:16Z 60 check 5 TRUE (0 matches on the four patterns; round-2 Bedrock 429 "Too many tokens per day" cross-checked platform-wide against coins+ecos and cleared by r3/r4)
2026-08-25T22:58:16Z 60 check 6 TRUE (source: SSR state.playlist[0] of softmax.com/factory-commons + POST /coworlds/replays/session -> static index.html, ready true, sha = manifest_sha)
2026-08-25T22:58:16Z 60 check 7 TRUE (committed release-result.json: "Replay liveness: skipped (static replay bundle declared...")
2026-08-25T22:58:16Z 60 check 8 TRUE (viewer-check run 32908246409 green, loaded true @1923ms, clocks SHIFT 1/SHIFT 8/FINAL differ, no failure; artifact committed to runs/.../viewer-check/)
2026-08-25T22:58:16Z 60 VERIFY.md written — verdict all-true 8/8
2026-08-25T22:58:16Z heartbeat phase=60
2026-08-25T22:59:21Z 60 verifier returned: VERIFY.md all-true 8/8, viewer-check artifacts in run dir; judge dispatched for phase-60 adjudication
2026-08-25T23:03:33Z 60 judge returned: verify-verdict.md blocking: 0 / BLOCKING: 0 — definition of done confirmed (notes: DRAW win-chip bug non-blocking, font.ttf 404 non-blocking)
2026-08-25T23:03:33Z progress phase=60 marker=verify-verdict.md
2026-08-25T23:03:33Z 60 -> 70 phase transition, STATE phase=70
2026-08-25T23:03:33Z heartbeat phase=70
2026-08-25T23:04:49Z 70 announce attempted_at written before POST
2026-08-25T23:05:11Z 70 announce msg=1541946517579890798 (HTTP 200, flags=4, embeds=[])
2026-08-25T23:05:11Z progress phase=70 marker=announce.discord_message_id=1541946517579890798
2026-08-25T23:05:11Z 70 -> 75 phase transition, STATE phase=75
2026-08-25T23:05:11Z heartbeat phase=75
