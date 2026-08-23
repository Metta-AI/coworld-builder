# 2026-08-23-hive — log

2026-08-23T04:14:57Z 00 claim comment posted on idea 1217704658784785 (story 1217750894927064)
2026-08-23T04:15:35Z 00 claim uncontested after 20s re-read
2026-08-23T04:15:58Z 00 claim 2026-08-23-hive idea=1217704658784785 slug=hive
2026-08-23T04:15:58Z 00 run task 1217750914627503 created in Running, 8 phase subtasks, heartbeat_at set session=6f943827
2026-08-23T04:15:58Z 00 phase -> 10
2026-08-23T04:18:30Z 10 starter chosen: Metta-AI/coworld-ctf — real-time grid loop with rules written for this coworld, RL-vector policies batched over bodies: the exact coworld-ctf row of the starter table
2026-08-23T04:18:30Z 10 designer dispatch pending; output=/workspace/scratch/cogame-hive/docs/plans/2026-08-23-hive-design.md
2026-08-23T04:20:10Z 10 designer dispatched (thread sthr_01NA9LTLokTvMvy1zxsVwnwU); output=/workspace/scratch/cogame-hive/docs/plans/2026-08-23-hive-design.md
2026-08-23T04:34:31Z 10 designer returned round 1; note at /workspace/scratch/cogame-hive/docs/plans/2026-08-23-hive-design.md (1337 lines)
2026-08-23T04:34:31Z 10 checklist: starter[x] num_agents=4[x] resolution-order-15-steps[x] scoring-share-constant-sum-elo[x] end-conditions-reason-enum-3[x] observation-visible-hidden[x] reply-caps-rune(note140/say32/policy48/detail200/prompt4000)[x] both-policies-marcher-driftling[x] parallel-batch-495s<720s[x] degrade-never-hang-retry-fallback-budget-guard[x] name-spaces-alias-permutation[x] viewer-static-360px[x] replay-self-sufficient-json[x] packaging-docs-protocols-both[x] tests-16-incl-e2e-utf8-viewer-smoke[x] out-of-scope-10-items[x] — ACCEPTED round 1, zero rejections
2026-08-23T04:34:31Z 10 design.md copied to runs/2026-08-23-hive/design.md; phase -> 20
2026-08-23T04:34:31Z progress phase=10 marker=runs/2026-08-23-hive/design.md
2026-08-23T04:35:20Z 20 repo Metta-AI/cogame-hive created public
2026-08-23T04:35:20Z 20 propagate-secrets run 32618229619 success; SOFTMAX_TOKEN + ANTHROPIC_API_KEY on cogame-hive
2026-08-23T04:36:08Z 20 builder dispatched (thread sthr_01BuNQZNLLWQj7WpSJXL31LF); target ci.yml green on main of Metta-AI/cogame-hive
2026-08-23T04:36:08Z heartbeat phase=20
2026-08-23T05:54:02Z 20 builder returned: ci.yml run 32621277603 success on main sha 48465f363ff1c09079d57fc40da717bd2f37e594 (first attempt); all exit-criteria checks pass (workflows parse, inputs present, artifacts named, hooks 100755, placeholder grep clean) — verified independently by coordinator
2026-08-23T05:54:02Z 20 builder deviations noted for review: main-thread viewer instead of worker shell; wasm emits packet + JS composites; 2 extra wasm exports; viewer node-smoke moved to wasm-viewer job; authored rock set differs from note's illustrative shapes; golden-digest nudge scope; delivery volume ~150-500/match vs note's 1500-3000 estimate (params as specified — phase 50 knob: sourceLifeTicks/maxOrbits)
2026-08-23T05:54:02Z 20 note: sandbox git-push over HTTPS rejected; builder pushed via Git Data API (blobs/tree/commit/ref) preserving modes
2026-08-23T05:54:02Z progress phase=20 marker=ci-run-32621277603
2026-08-23T05:54:02Z 20 phase -> 30 (review_round 1)
2026-08-23T05:55:50Z 30 r1 reviewer dispatched (thread sthr_01LDLUyjeauT18DotXkXBjDz); repo checkout /workspace/scratch/cogame-hive-repo @ 48465f3
2026-08-23T05:55:50Z heartbeat phase=30
2026-08-23T06:11:45Z 30 r1 reviewer returned: 30 findings (3 candidate-blocking: wasm-viewer job missing browser smoke+needs, data-replay-loaded marker shape/timing, recall kernel), 12 traced-consistent; reviews/r1-review.md (558 lines)
2026-08-23T06:11:45Z 30 r1 fixer dispatch pending
2026-08-23T06:12:30Z 30 r1 fixer dispatched (thread sthr_016v1c7fcMyynDciCsJvpgJE)
2026-08-23T06:12:30Z heartbeat phase=30
2026-08-23T07:07:26Z 30 r1 fixer returned: 20 commits, main -> 34b3dc9e7355d5047e95109ad117f813a509d950, ci run 32624269486 success; B1/B2/B3 fixed, 13 non-blocking fixed, 8+ refuted with evidence, grid harness added (marcher rank 1 of 9); reviews/r1-fixes.md
2026-08-23T07:07:26Z progress phase=30 marker=r1-fixes.md
2026-08-23T07:08:15Z 30 r1 judge dispatched (thread sthr_01N9AnxGaCx5SVp3KWBZJaiZ); repo @ 34b3dc9
2026-08-23T07:08:15Z heartbeat phase=30
2026-08-23T07:17:37Z 30 r1 judge returned: blocking 0 (both markers agree); all 13 checklist items pass at 34b3dc9, all 3 review blockers dismissed-as-fixed; reviews/r1-verdict.md
2026-08-23T07:17:37Z progress phase=30 marker=r1-verdict.md
2026-08-23T07:17:37Z 30 phase -> 40
2026-08-23T07:18:27Z 40 builder dispatched for release (same thread sthr_01BuNQZNLLWQj7WpSJXL31LF); start version 0.1.0
2026-08-23T07:18:27Z heartbeat phase=40
2026-08-23T07:37:46Z 40 dispatch 1: version 0.1.0 run 32625232683 step_failed="Build the Coworld manifest" (6 pydantic errors vs coworld 0.1.42 upload contract) — decision: fix manifest shape, not a race
2026-08-23T07:37:46Z 40 dispatch 2: version 0.1.1 run 32625651640 ok=true canonical=true certify.ok=true secret_put=true liveness=skipped(static); fix commit 084391c (manifest to 0.1.42 contract + ANTHROPIC_API_KEY_URI env on game runnable)
2026-08-23T07:37:46Z 40 hosted certification polled: state=certified, 10/10 steps pass; hosted smoke passed (5 episodes); cow_89df098f-6f9b-42ee-adc0-ecf1252103cd
2026-08-23T07:37:46Z 40 release-result.json persisted to runs/2026-08-23-hive/release-result.json
2026-08-23T07:37:46Z progress phase=40 marker=release-run-32625651640
2026-08-23T07:37:46Z 40 phase -> 50
2026-08-23T07:38:54Z 50 seed created lseed_dfccbb9f-a89c-4311-a528-007b27f7a483; league league_2d1d904b-5465-4b84-9845-b28164d22f7e (note: GET /leagues returns a bare array, not .entries)
2026-08-23T07:38:54Z 50 division div_86b9824f-b420-4d0a-8902-a7878b2102c7 (Competition); settings POST 200 (elo k32 round_robin filler_policy, round_interval 15m)
2026-08-23T07:38:54Z heartbeat phase=50
2026-08-23T07:41:09Z 50 champion1 submit run 32626121206 ok=true (hive-pathwright:v1, daveey)
2026-08-23T07:41:09Z 50 champion2 submit run 32626144433 ok=true (hive-swarmraid:v1, daveey-1; policy-version row confirms player_name=daveey-1)
2026-08-23T07:41:09Z 50 fillers registered: hive-marcher:v1 79e9d9b4-bdff-4117-8d92-0eafdc697bfe + hive-driftling:v1 ab07597a-c008-45f4-91f2-14d7594ec4ef (response lists exactly these two, neither champion)
2026-08-23T07:41:09Z 50 unpaused; trigger-round accepted; round 2 pending with BOTH champions in entrant_attributions; round 1 failed (auto-created before fillers/champion2 — predates the trigger, not counted against trigger budget)
2026-08-23T07:41:09Z progress phase=50 marker=league_2d1d904b-5465-4b84-9845-b28164d22f7e-round2
2026-08-23T07:41:09Z 50 phase -> 60
2026-08-23T07:42:09Z 60 verifier dispatched (thread sthr_012F1jpjoGAnFUk8S6bGEdHB); polling bounded 75 min
2026-08-23T07:42:09Z heartbeat phase=60
2026-08-23T07:46:16Z heartbeat phase=60
2026-08-23T07:51:26Z 60 poll: rounds 2=completed, 1=failed; awaiting round 3 (auto ~07:55Z)
2026-08-23T07:51:26Z heartbeat phase=60
2026-08-23T08:00:43Z 60 round 3 completed (round_0eaae974); checks 1-6 re-fetched against round 3; viewer-check re-dispatched run 32627090556
2026-08-23T08:00:43Z heartbeat phase=60
2026-08-23T08:06:35Z 60 check 1 TRUE: rounds 2 + 3 completed (both after fillers 07:41:09Z); round 1 failed "Temporal RoundWorkflow failed before settling the round." (predates fillers, not counted)
2026-08-23T08:06:35Z 60 check 2 TRUE: leaderboard 2 rows — daveey-1/hive-swarmraid:v1 Elo 1001.47 rp=2, daveey/hive-pathwright:v1 Elo 998.53 rp=2; no filler rows
2026-08-23T08:06:35Z 60 check 3 TRUE: round 3 ereq_4dce5786 completed, replay_url 334e0e3a…; participants daveey + daveey-1 (is_filler false) + 2 fillers
2026-08-23T08:06:35Z 60 check 4 TRUE: 211002 B strict UTF-8 JSON; protocol hive.replay.v1; complete/full_time; 40/40 champion doctrines source=llm, 0 fallbacks, 39 distinct notes
2026-08-23T08:06:35Z 60 check 5 TRUE: artifacts/logs 83767 B, grep CLEAN
2026-08-23T08:06:35Z 60 check 6 TRUE: raw-HTML grep empty (client-rendered) + /coworlds featured_match null -> used SSR state.playlist[0] (hive.r3.e1) + POST /coworlds/replays/session -> static index.html route, ready:true, no /client/replay
2026-08-23T08:06:35Z 60 check 7 TRUE: committed runs/2026-08-23-hive/release-result.json -> "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"
2026-08-23T08:06:35Z 60 check 8 TRUE: viewer-check run 32627090556 success; loaded=true ms=6611 bridge=[loading,ready]; clocks 3:19 TURN 0/20 -> 1:37 TURN 10/20 -> FINAL GAME OVER; artifact in runs/2026-08-23-hive/viewer-check/
2026-08-23T08:06:35Z 60 VERIFY.md written: 8/8 TRUE; no writes to league/rounds/policies; nothing pushed (sandbox cannot push)
2026-08-23T08:06:35Z heartbeat phase=60
2026-08-23T08:08:43Z 60 verifier returned: 8/8 TRUE (VERIFY.md 860 lines, evidence inline); rounds 2+3 completed, both champions ranked rp=2 (daveey-1 1001.47, daveey 998.53), replay reason=complete 40/40 llm doctrines 0 fallbacks, log CLEAN, static viewer route confirmed, viewer-check run 32627090556 loaded:true clocks differ
2026-08-23T08:08:43Z progress phase=60 marker=VERIFY.md-8-true
2026-08-23T08:08:43Z 60 judge adjudication dispatch pending
