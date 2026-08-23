# 2026-08-23-gridlock — log

2026-08-23T08:59:07Z 00 claim comment posted on idea 1217704767292352
2026-08-23T08:59:45Z 00 claim 2026-08-23-gridlock idea=1217704767292352 slug=gridlock
2026-08-23T09:00:16Z 00 run task created gid=1217752130347986 with 8 phase subtasks; heartbeat_at written
2026-08-23T09:00:48Z 00 STATE written phase=10 session=ffe374dd
2026-08-23T09:01:25Z 10 starter decided: Metta-AI/coworld-ctf (paintbot) — real-time loop with new rules (signalised road grid, queue/congestion dynamics), RL-vector/code-agent seats; nothing pre-exists to port and no external engine, so rows moba/factorio don't apply
2026-08-23T09:01:25Z heartbeat phase=10
2026-08-23T09:02:10Z 10 designer dispatched thread=sthr_01HBvUWjQ9WokQCHyKnMY9Pr brief=self-contained (idea verbatim, checklist path, phase-0 pins, starter=coworld-ctf all four viewer files, output=runs/2026-08-23-gridlock/design.md)
2026-08-23T09:18:10Z 10 designer returned thread=sthr_01HBvUWjQ9WokQCHyKnMY9Pr design.md=1442 lines
2026-08-23T09:18:10Z 10 checklist: starter [x] num_agents=4-everywhere [x] resolution-order-numbered(14) [x] scoring+sign+league-ranks [x] end-conditions+deadline+reason-enum [x] per-seat-observation [x] reply-schema-rune-caps [x] both-policies-env-switched [x] one-parallel-batch+720s-budget [x] degrade-never-hang [x] two-name-spaces [x] viewer-static-wasm+360px [x] viewer-single-starter-all-four-files=coworld-ctf [x] replay-self-sufficient [x] packaging-manifest+docs+both-protocols [x] tests-incl-executed-viewer-smoke [x] out-of-scope-non-empty [x]
2026-08-23T09:18:10Z 10 design ACCEPTED round 1, zero rejections
2026-08-23T09:18:10Z progress phase=10 marker=runs/2026-08-23-gridlock/design.md
2026-08-23T09:18:10Z 10 -> 20 phase transition
2026-08-23T09:18:10Z heartbeat phase=20
2026-08-23T09:19:14Z 20 repo created https://github.com/Metta-AI/cogame-gridlock (public)
2026-08-23T09:19:14Z 20 propagate-secrets run=32630657567 success; gh secret list shows SOFTMAX_TOKEN + ANTHROPIC_API_KEY
2026-08-23T09:20:03Z 20 builder dispatched thread=sthr_011rehx42fDrX33gxoEk5YHc brief=self-contained (design note path, starter mount, templates, exit checks, hard requirements, 3-round budget)
2026-08-23T11:01:30Z 20 builder returned thread=sthr_011rehx42fDrX33gxoEk5YHc ci.yml GREEN run=32635065143 sha=4b74806 (93 files; exit checks all pass; verified independently: conclusion=success on main head)
2026-08-23T11:01:30Z 20 builder notes: (1) viewer chrome authored to paintbot architecture not byte-copied (CTF compositor is CTF-specific) (2) momentum curves declarative only (3) test_server static (4) digest-sensitivity test perturbs by 37 not 1 (5) plaza moved off lane cells (6) commons effect mild at default demand, dispatcher>beeline ordering holds at rush demand — items for reviewer to weigh
2026-08-23T11:01:30Z 20 RAIL DECISION (coordinator): league plays variant `rush` — builder measured order-limited (not congestion-limited) play at default demand (all-dispatcher 732 vs all-beeline 730, zero gridlock events) vs a real congestion spread at rush (1295 v 1125, stable across 4 seeds); the idea's thesis (greedy routing causes the jam) is only visible at rush. Applies at phase 50 league settings/variant selection.
2026-08-23T11:01:30Z 20 note: builder pushed via Git Data API workaround — git-credential-anthropic rejected on fresh repo (app installation gap); not blocking, flag in phase-80 learnings
2026-08-23T11:01:30Z progress phase=20 marker=ci-run-32635065143
2026-08-23T11:01:30Z 20 -> 30 phase transition review_round=1
2026-08-23T11:01:30Z heartbeat phase=30
2026-08-23T11:02:19Z 30 r1 reviewer dispatched thread=sthr_01QnznsdvzScY77CeNVywTpy target=4b74806 output=runs/2026-08-23-gridlock/reviews/r1-review.md
2026-08-23T11:19:07Z 30 r1 reviewer returned: 25 findings, 0 blocking per reviewer (r1-review.md); notable: F9 disconnect-degrade unimplemented, F10 default-prompt seat, F15-17 chrome id gaps, F18 viewer_smoke.mjs older template rev, F25 no tuning-harness artefact
2026-08-23T11:19:07Z progress phase=30 marker=r1-review.md
2026-08-23T11:19:45Z 30 r1 fixer dispatched thread=sthr_019g963yEg3dbGUtLdBNAAZE (coordinator rulings: dead chrome ids may be hidden/removed rather than wired; momentum layer stays deferred; F25 needs a real committed sweep harness)
2026-08-23T14:36:17Z 00 attempts_reset phase=30 reason=progress marker=r1-review.md
2026-08-23T14:36:17Z 00 resume at phase 30 attempt=1 session=a0e45f38
2026-08-23T14:37:54Z 30 r1 fixer re-dispatch (previous fixer pushed 17 commits F2..F25, CI green run=32638156016 sha=b732790f, but r1-fixes.md missing; new fixer reconciles existing commits + addresses F1,F3,F5,F17,F19,F22,F23,F24 and writes the artifact)
2026-08-23T14:58:03Z 30 r1 fixer returned thread=sthr_01KJi3zjQHqepVdnnUXimzN2: 6 new commits (F3,F17,F19,F22,F23,+F21-followup), 3 no-change with evidence (F1,F5,F24), head=0decf322 CI GREEN run=32646687184 incl new viewer-native job; r1-fixes.md covers all 25
2026-08-23T14:58:03Z progress phase=30 marker=r1-fixes.md
2026-08-23T14:58:03Z 30 r1 judge dispatched (fresh context, target sha=0decf3220186f0ae07d7b03731624c07d1277847, output=reviews/r1-verdict.md)
2026-08-23T14:58:03Z heartbeat phase=30
2026-08-23T15:05:48Z 30 r1 judge returned thread=sthr_01UurAnMuEEum2rkDbo83n7z verdict=r1-verdict.md blocking=0 (all 13 checklist items + batching rule PASS at 0decf322; 21 advisories resolved by commits, 3 no-change upheld)
2026-08-23T15:05:48Z progress phase=30 marker=r1-verdict.md
2026-08-23T15:05:48Z 30 -> 40 phase transition (review loop exited round 1, zero blocking)
2026-08-23T15:05:48Z heartbeat phase=40
2026-08-23T15:06:24Z 40 builder dispatched thread=TBD brief=release chain v0.1.0 (dispatch-then-watch, persist release-result.json, no skip_certify)
2026-08-23T15:13:34Z 40 release dispatch version=0.1.0 run=32647554701 step_failed=none decision=first dispatch (no policies override, no skip_certify) green on attempt 1; cow_id=cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6 canonical=true secret_put=true 4 policies at v1
2026-08-23T15:14:45Z 40 builder returned thread=sthr_01SFoennpX6UboASv6xkkztq release 0.1.0 GREEN first dispatch run=32647554701 cow=cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6 canonical=true certify.ok=true secret_put=true
2026-08-23T15:14:45Z progress phase=40 marker=release-run-32647554701
2026-08-23T15:14:45Z 40 -> 50 phase transition
2026-08-23T15:14:45Z heartbeat phase=50
2026-08-23T15:15:59Z 50 seed 200 league=league_4c0f039e-3a99-48ad-9d72-c3f85a110ea8 (seed lseed_23685dba)
2026-08-23T15:15:59Z 50 division PUT 200 div=div_349162e2-db36-4d23-a13f-49b0bf84df8e (note: GET /leagues returns bare array, not .entries — filtered accordingly)
2026-08-23T15:15:59Z 50 settings POST 200 (elo k=32 init=1000 mean, round_robin, filler_policy, interval=15m)
2026-08-23T15:15:59Z progress phase=50 marker=league_4c0f039e-3a99-48ad-9d72-c3f85a110ea8
2026-08-23T15:15:59Z heartbeat phase=50
2026-08-23T15:19:01Z 50 champion1 submitted run=32648018148 ok=true sub=sub_0ae61300-6015-4583-92a5-c7e8eae11d87 policy=gridlock-flowwright:v1 player=daveey
2026-08-23T15:19:01Z 50 champion2 submitted run=32648049519 ok=true sub=sub_8dc366ca-50d2-48f9-94ad-dc81a588ee13 policy=gridlock-backstreet:v1 player=daveey-1
2026-08-23T15:19:01Z 50 policy-version UUIDs resolved: flowwright=35bdf51f backstreet=bf5cf3e0(daveey-1) dispatcher=b72ad0fa beeline=74c2a80b
2026-08-23T15:19:01Z 50 filler-policies POST 200 (dispatcher+beeline only, neither champion)
2026-08-23T15:19:01Z 50 rounds-paused=false 200; trigger-round 200 workflow=ladder-league_4c0f039e
2026-08-23T15:19:01Z 50 round 1 status=pending, entrant_attributions carry both champions
2026-08-23T15:19:01Z progress phase=50 marker=sub_8dc366ca-50d2-48f9-94ad-dc81a588ee13
2026-08-23T15:19:01Z 50 -> 60 phase transition
2026-08-23T15:19:01Z heartbeat phase=60
2026-08-23T15:19:29Z 60 verifier dispatched thread=TBD (8 checks, poll bound 75m, output=runs/2026-08-23-gridlock/VERIFY.md + viewer-check/)
2026-08-23T15:20:50Z heartbeat phase=60
2026-08-23T15:25:58Z heartbeat phase=60
2026-08-23T15:31:31Z heartbeat phase=60
2026-08-23T15:31:33Z heartbeat phase=60
2026-08-23T15:36:24Z heartbeat phase=60
2026-08-23T15:41:08Z heartbeat phase=60
2026-08-23T15:42:20Z heartbeat phase=60
2026-08-23T15:44:56Z heartbeat phase=60
2026-08-23T15:48:21Z 60 check1 TRUE rounds completed=2 (r1 15:21:50Z, r2 15:36:51Z) both after fillers set 15:19:01Z; 0 failed/discarded
2026-08-23T15:48:21Z 60 check2 TRUE leaderboard daveey rank1 gridlock-flowwright:v1 elo=1030.53 rp=2 wins=2 | daveey-1 rank2 gridlock-backstreet:v1 elo=969.47 rp=2 wins=0; fillers absent
2026-08-23T15:48:21Z 60 check3 TRUE ereq_49c11f68-c5df-4791-8a45-ac1743ccf6d2 status=completed replay_url set; seats daveey/daveey-1 is_filler=false, seats 2-3 beeline is_filler=true
2026-08-23T15:48:21Z 60 check4 TRUE replay 360837B strict-JSON ok protocol=gridlock.replay.v1 reason=complete end_rule=full_time; champion plans 40/40 source=llm, fallbacks 0, 38 distinct notes
2026-08-23T15:48:21Z 60 check5 TRUE hosted log CLEAN (0 hits raw and un-escaped) for falling back|LLM provider is unavailable|cut off at max_tokens|rejected; game container reason=complete
2026-08-23T15:48:21Z 60 check6 TRUE iframe src static /v2/coworlds/replays/static/cow_69f7b3ab/sha256:38c6a5c2.../index.html?replay=... ready=true; featured match from SSR state.playlist[0] = gridlock.r2.e1 (raw-HTML grep empty, page client-rendered)
2026-08-23T15:48:21Z 60 check7 TRUE certify.replay_liveness="Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)" read from committed runs/2026-08-23-gridlock/release-result.json (cb202b3), no re-download needed
2026-08-23T15:48:21Z 60 check8 TRUE viewer-check run=32649388472 conclusion=success loaded=true ms=3245 bridge=[loading,ready,ready]; clocks 0%=03:20 TURN 0/20 50%=01:37 TURN 10/20 100%=00:00 TURN 19/20; feed_lines=6; finding: corner HUD transposes Cobalt/Copper totals (184<->186) vs results/end-card/depot chips
2026-08-23T15:48:21Z 60 VERIFY.md written verdict=all-true 8/8; waited 21m of 75m bound (bound NOT hit)
2026-08-23T15:49:34Z 60 verifier returned thread=sthr_011aeWXnuCJPjemmYy7cXpJv VERIFY.md 8/8 TRUE (2 completed rounds, both champions ranked, replay valid reason=complete, logs CLEAN, static iframe, viewer-check run=32649388472 loaded=true clocks advance; advisory: HUD corner-plate score transposition noted for later version)
2026-08-23T15:49:34Z progress phase=60 marker=VERIFY.md-all-true
2026-08-23T15:49:34Z 60 judge dispatched (fresh context, adjudicate VERIFY.md vs SPEC definition of done)
2026-08-23T15:49:34Z heartbeat phase=60
2026-08-23T15:54:30Z 60 judge returned thread=sthr_01PsikKPSe2se1jyEs1s31Ra verify-verdict.md BLOCKING=0 (all 8 verified; 2 non-blocking notes: [viewer-hud] plate transposition, [verify-prose] filler-timing wording)
2026-08-23T15:54:30Z progress phase=60 marker=verify-verdict.md
2026-08-23T15:54:30Z 60 -> 70 phase transition
2026-08-23T15:54:30Z heartbeat phase=70
2026-08-23T15:57:23Z 70 RAIL DECISION REVISED: league stays on variant=default. Phase-20 rush decision was motivated by scripted-baseline near-tie at default demand; verified league play shows champion spread at default (r1/r2: flowwright 2-0, elo 1030.5 v 969.5, jam mean 24 peak 31) and the platform requires a pause+lock maintenance window to change variant (POST seed default_variant_id=rush -> 409) — not worth re-opening a verified league pre-announce. Revision logged, noted on run task.
2026-08-23T15:58:16Z 70 announce.attempted_at written before POST
2026-08-23T15:58:39Z 70 announce msg=1541114401652875304
2026-08-23T15:58:39Z progress phase=70 marker=discord_message_id=1541114401652875304
2026-08-23T15:58:39Z 70 -> 80 phase transition
2026-08-23T15:58:39Z heartbeat phase=80
2026-08-23T16:00:45Z 80 close complete: summary on run task (1217754209113345) + idea task (1217754158982006), LEARNINGS entry appended, all 8 phase subtasks complete, idea 1217704767292352 completed, run task moved to Done
2026-08-23T16:00:45Z progress phase=80 marker=run-task-Done
2026-08-23T16:00:45Z session end: run complete at phase 80; no next action — run is Done
