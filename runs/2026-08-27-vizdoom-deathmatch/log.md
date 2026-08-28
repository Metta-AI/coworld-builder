# 2026-08-27-vizdoom-deathmatch — log

2026-08-27T21:23:01Z 00 claim comment posted on idea 1217748519766654
2026-08-27T21:24:15Z 00 claim 2026-08-27-vizdoom-deathmatch idea=1217748519766654 slug=vizdoom-deathmatch run_task=1217924356123841 session=7565f38f
2026-08-27T21:24:15Z 00 run task created in Running with 9 phase subtasks; starter=coworld-ctf
2026-08-27T21:24:15Z 00 -> 10 phase transition; STATE written
2026-08-27T21:26:30Z 10 rails: starter=coworld-ctf (idea's own cheaper-alternative path: crewrift engine has vision cones, guns, respawn, deathmatch arena); seats=8 as 4v4 team DM (idea integrity note prefers team DM, server-assigned teams); scoring pinned by idea: frags − deaths
2026-08-27T21:26:30Z 10 dispatch designer: design note for cogame-vizdoom-deathmatch from starter coworld-ctf
2026-08-27T21:50:01Z 10 designer returned design.md (1859 lines); checklist review: starter [x] num_agents [x] resolution-order [x] scoring [x] end-conditions [x] observation [x] reply-schema [x] both-policies [x] parallel-batch-budget [x] degrade-never-hang [x] name-spaces [x] viewer-static [x] viewer-one-starter [x] chrome-provenance [x] transport-rules [x] replay-self-sufficient [x] packaging [x] tests [x] out-of-scope [x] — ACCEPTED round 1
2026-08-27T21:50:01Z progress phase=10 marker=design.md written and accepted (1859 lines)
2026-08-27T21:50:01Z 10 -> 20 phase transition: entering build
2026-08-27T21:50:01Z heartbeat phase=20
2026-08-27T21:50:56Z 20 repo created: https://github.com/Metta-AI/cogame-vizdoom-deathmatch (public)
2026-08-27T21:50:56Z 20 propagate-secrets.yml run 33119972081 green; SOFTMAX_TOKEN + ANTHROPIC_API_KEY on repo
2026-08-27T21:50:56Z 20 dispatch builder round 1
2026-08-27T21:50:56Z heartbeat phase=20
2026-08-27T23:37:40Z 20 builder returned: CI green run 33126418568 sha 3e49fa42 (test/docker-smoke/wasm-viewer all pass); exit criteria verified (placeholders clean, 3 workflows active, release/submit inputs+artifacts present, exec bits, manifest pins)
2026-08-27T23:37:40Z 20 builder caveats logged for review: gated-not-deleted mechanics, sim.nim unsplit, cones broadcast-not-drawn, no tuning sweep, no renderer_fixture, wasm_replay_smoke uninvoked, helmets viewer-side only, legacy staticRead art kept, chrome_common.js 2-line delta (VZD_WIRE), endcard-label test narrowed, haiku-only llm ladder (raid learning)
2026-08-27T23:37:40Z 20 note: builder pushed via Git Data API (sandbox git-push refused); main history carries ~130 repeated-message commits, tree correct, never force-pushed — cosmetic, accepted
2026-08-27T23:37:40Z progress phase=20 marker=ci-run-33126418568-green
2026-08-27T23:37:40Z 20 -> 30 phase transition: entering review loop round 1
2026-08-27T23:37:40Z heartbeat phase=30
2026-08-27T23:38:46Z 30 repo cloned to /workspace/cogame-vizdoom-deathmatch at 3e49fa42; dispatch reviewer round 1
2026-08-27T23:38:46Z heartbeat phase=30
2026-08-28T00:00:58Z 30 reviewer returned r1-review.md: 29 findings, 4 blocking (F1 replay re-derivation test missing, F2 model-text legibility fixture missing, F3 baseline tuning absent, F4 chrome_common.js divergence undocumented) + F5 team-kill scoring defect flagged non-blocking
2026-08-28T00:00:58Z 30 dispatch fixer round 1
2026-08-28T00:00:58Z heartbeat phase=30
2026-08-28T01:23:46Z 30 fixer returned r1-fixes.md: 16 commits (F1-F5 all fixed with evidence, 10 advisories fixed, rest disputed/deferred with reasons); CI green run 33132259050 sha 7e2d1d0a; design.md updated with F4 patch record; baseline sweep moved rusherHuntPx 520->120, postRotation 2->1
2026-08-28T01:23:46Z 30 dispatch judge round 1 on sha 7e2d1d0a
2026-08-28T01:23:46Z heartbeat phase=30
2026-08-28T01:38:34Z 30 judge returned r1-verdict.md: blocking 0 (first/last markers agree); all 4 review blockers refuted-as-fixed; 15/15 checklist items verified independently at sha 7e2d1d0a, CI 33132259050
2026-08-28T01:38:34Z progress phase=30 marker=r1-verdict.md blocking=0
2026-08-28T01:38:34Z 30 -> 40 phase transition: entering release
2026-08-28T01:38:34Z heartbeat phase=40
2026-08-28T01:39:04Z 40 dispatch builder for release (version 0.1.0 first attempt)
2026-08-28T01:39:04Z heartbeat phase=40
2026-08-28T01:48:36Z 40 release dispatch 1/3: version=0.1.0 run=33133544667 step_failed=null — SUCCESS first dispatch; canonical=true, certify.ok=true (replay_liveness skipped/static), secret_put=true; cow_4e53e339-ec7c-4059-8e13-881aedbea5ba; policies vzd-pointman:v1 vzd-crossfire:v1 (daveey-1) vzd-rusher:v1 vzd-sentry:v1
2026-08-28T01:48:36Z progress phase=40 marker=release-run-33133544667 release-result.json
2026-08-28T01:48:36Z 40 -> 50 phase transition: entering league
2026-08-28T01:48:36Z heartbeat phase=50
2026-08-28T01:52:30Z 50 seed POST 200 lseed_daa2baf2; league league_00dcb926-7f23-4507-8a2d-6684cb0e7c4b (GET /leagues returns bare array, not .entries — filtered client-side)
2026-08-28T01:52:30Z 50 division PUT 200 div_67b01fa1-41ae-493c-8a1d-bb69f08bd83a; settings POST 200 (elo, round_robin, filler_policy, 15 min)
2026-08-28T01:52:30Z 50 champion1 submit run 33134044321 ok=true vzd-pointman:v1 daveey; champion2 submit run 33134075747 ok=true vzd-crossfire:v1 daveey-1
2026-08-28T01:52:30Z 50 policy-versions resolved: pointman d4fdd9d3 daveey, crossfire 3a4fba26 daveey-1, rusher 009fc22a, sentry 8dd54435
2026-08-28T01:52:30Z 50 filler-policies POST 200: rusher+sentry UUIDs only, neither champion; rounds-paused false 200; trigger-round 200
2026-08-28T01:52:30Z 50 rounds: round 1 failed (Temporal RoundWorkflow, auto-round before fillers landed — superseded), round 2 pending with both champions in entrant_attributions
2026-08-28T01:52:30Z progress phase=50 marker=league_00dcb926-7f23-4507-8a2d-6684cb0e7c4b round-2-pending
2026-08-28T01:52:30Z 50 -> 60 phase transition: entering verify
2026-08-28T01:52:30Z heartbeat phase=60
2026-08-28T02:17:33Z 60 verifier returned VERIFY.md: 8/8 TRUE — rounds 2+3 completed, both champions ranked (elo 1001.47/998.53), replay complete/full_time with 48 LLM directives 0 fallbacks, hosted log CLEAN, static iframe route (fragment #replay= variant), release-result liveness skipped, viewer-check 33135119698 loaded=true clocks advance
2026-08-28T02:17:33Z 60 verifier notes (non-blocking): viewer_smoke feed selector misses #killfeed (probe artefact); scrub clicks undershoot (endcard unobserved); inherited 'hill red=0 blue=0' log line; ordersRejected[0]=1
2026-08-28T02:17:33Z progress phase=60 marker=VERIFY.md 8/8 viewer-check-33135119698
2026-08-28T02:17:33Z 60 dispatch judge for definition-of-done adjudication
2026-08-28T02:17:33Z heartbeat phase=60
2026-08-28T02:26:03Z 60 judge returned verify-verdict.md: blocking 0 — all 8 items TRUE, all 4 substitutions ruled SOUND, evidence re-fetched independently
2026-08-28T02:26:03Z 60 -> 70 phase transition: entering announce
2026-08-28T02:26:03Z heartbeat phase=70
2026-08-28T02:27:05Z 70 announce attempted_at written before POST
