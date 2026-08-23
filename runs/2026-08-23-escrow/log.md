# 2026-08-23-escrow — log

2026-08-23T13:02:00Z 00 claim 2026-08-23-escrow idea=1217704516772355 slug=escrow
2026-08-23T13:04:30Z 00 run task 1217753074035208 created in Running with 8 phase subtasks session=8bdafd79
2026-08-23T13:05:00Z 00 -> 10 phase transition: entering design
2026-08-23T13:08:00Z 10 starter chosen: Metta-AI/cogame-bullwhip — turn-based economic game, LLM-prompt policies, simultaneous per-turn numeric decisions with inter-seat messages: first row of the starter table, newer descendant closer than babel (babel is a referential-language game; escrow is a trading economy like bullwhip)
2026-08-23T13:08:00Z 10 designer dispatch pending; output=/workspace/scratch/cogame-escrow/docs/plans/2026-08-23-escrow-design.md
2026-08-23T13:10:30Z 10 designer dispatched (thread sthr_01NnmgqrRT9w2xXmp1wRehCi); output=/workspace/scratch/cogame-escrow/docs/plans/2026-08-23-escrow-design.md
2026-08-23T13:25:00Z 10 designer returned round 1; note at /workspace/scratch/cogame-escrow/docs/plans/2026-08-23-escrow-design.md (753 lines)
2026-08-23T13:25:30Z 10 checklist: starter[x] num_agents=4[x] resolution-order-9-steps+horizon-closure[x] scoring-free-hearts-positive-mean[x] end-conditions-complete-deadline-only[x] observation-open-outcry-only-notes-hidden[x] reply-caps-rune(offer240/say160/notes600/prompt4000)[x] both-policies-trader-hoarder[x] parallel-batch-330s<720s[x] degrade-never-hang-retry-probe-fallback-deadline-check[x] name-spaces-alias-policy[x] viewer-static-360px[x] viewer-all-four-files-bullwhip[x] replay-self-sufficient-seed-events-results[x] packaging-docs-2pages-protocols-both[x] tests-19-incl-legality-e2e-utf8-viewer-executed[x] out-of-scope-7-items[x] — ACCEPTED round 1, zero rejections
2026-08-23T13:26:00Z 10 design.md copied to runs/2026-08-23-escrow/design.md; phase -> 20
2026-08-23T13:26:00Z progress phase=10 marker=runs/2026-08-23-escrow/design.md
2026-08-23T13:26:00Z heartbeat phase=20
2026-08-23T13:27:00Z 20 repo created: https://github.com/Metta-AI/cogame-escrow (public)
2026-08-23T13:29:00Z 20 propagate-secrets run 32641961887 success; gh secret list on cogame-escrow shows SOFTMAX_TOKEN + ANTHROPIC_API_KEY
2026-08-23T13:29:30Z 20 builder dispatch pending
2026-08-23T13:20:07Z 20 builder dispatched (thread sthr_01CNk73xmq1jqdgdxm7tH9FD); repo=Metta-AI/cogame-escrow starter=cogame-bullwhip
2026-08-23T13:20:07Z heartbeat phase=20
2026-08-23T14:20:16Z 20 builder returned: CI green run 32644872806 on d68c5ecd58c8ebfb0f8c2d3b5ffa7be99c41bceb (jobs test/docker-smoke/wasm-viewer all success); 3 documented small deviations (Sim type in types.nim, renderContract(sim,c), trader surplus never HEARTS + zero-live offer rule)
2026-08-23T14:20:16Z 20 note: sandbox git-push-over-HTTPS to github.com fails (token auth rejected); builder pushed via git-data API — relayed as data, phases 40/50 use gh workflow dispatch and are unaffected
2026-08-23T14:20:16Z progress phase=20 marker=ci-run-32644872806
2026-08-23T14:20:16Z 20 -> 30 phase transition: entering review loop round 1
2026-08-23T14:20:16Z heartbeat phase=30
2026-08-23T14:28:24Z 20 asana: phase-20 subtask completed, comment posted, heartbeat_at refreshed
2026-08-23T14:28:24Z 00 note: coordinator's git push over HTTPS to github.com now also rejected (auth); pushes for this session go via git-data API helper (/tmp/api_push.sh), fast-forward only, never forced
2026-08-23T14:29:17Z 30 r1 reviewer dispatched (thread sthr_01FhjjRsS7UjZdNQQCncKmRv); repo checkout /workspace/scratch/cogame-escrow-repo @ d68c5ec
2026-08-23T14:29:17Z heartbeat phase=30
2026-08-23T14:42:05Z 30 r1 review returned: 10 findings (F1 blocking: LLM-fallback seats recorded scripted:false; F2-F10 advisory), 3 could-not-determine; reviews/r1-review.md
2026-08-23T14:42:05Z progress phase=30 marker=reviews/r1-review.md
2026-08-23T14:42:05Z 30 r1 fixer dispatch pending
2026-08-23T14:42:46Z 30 r1 fixer dispatched (thread sthr_01BokQzMn9Rhy2r9mTLJgoAh)
2026-08-23T14:42:46Z heartbeat phase=30
2026-08-23T14:57:17Z 30 r1 fixer returned: F1/F2/F4/F10 fixed (commits 3b6c3eb,122cf57,1ecfa58,dac4fc4), F3/F5-F9 dismissed with evidence; CI green run 32646647329 @ dac4fc4c6c58a6465bae07f0c1cbc308b5cbf0e6; reviews/r1-fixes.md
2026-08-23T14:57:17Z progress phase=30 marker=reviews/r1-fixes.md
2026-08-23T14:57:17Z 30 r1 judge dispatch pending
2026-08-23T14:58:16Z 30 r1 judge dispatched (thread sthr_01HE1CwjzKZjEzjWZ7mo82q5) on sha dac4fc4c6c58a6465bae07f0c1cbc308b5cbf0e6
2026-08-23T14:58:16Z heartbeat phase=30
2026-08-23T15:06:06Z 30 r1 verdict returned: BLOCKING: 1 ([other] checklist item 7 second sentence — no grid-harness tuning record in the tree); reviews/r1-verdict.md
2026-08-23T15:06:06Z progress phase=30 marker=reviews/r1-verdict.md
2026-08-23T15:06:06Z 30 round 1 -> 2; plan: reviewer r2 on current head, fixer r2 gets r2-review + the r1-verdict residue (commit a real sweep harness + tuning record), judge r2
2026-08-23T15:06:39Z 30 r2 reviewer dispatched (thread sthr_011eorMUvcoyKkFi3CcV6mLw) on sha dac4fc4
2026-08-23T15:06:39Z heartbeat phase=30
2026-08-23T15:16:20Z 30 r2 review returned: 5 findings (F1 blocking = grid-harness tuning record still absent; F2-F5 advisory); four r1 fix commits trace clean; reviews/r2-review.md
2026-08-23T15:16:20Z progress phase=30 marker=reviews/r2-review.md
2026-08-23T15:16:20Z 30 r2 fixer dispatch pending
2026-08-23T15:17:02Z 30 r2 fixer dispatched (thread sthr_01NwtfLiAwaGsSnPg8gMFM13); mandate: real grid harness + committed tuning record + CI wiring for F1, F2-F5 fix-or-dismiss
2026-08-23T15:17:02Z heartbeat phase=30
2026-08-23T15:38:38Z 30 r2 fixer returned: F1 fixed (grid harness tools/tune_baseline.nim + docs/tuning.md + CI check step; argmax tradeUnits=6/needFills=3 adopted, 2.27x autarky), F2/F4/F5 fixed, F3 dismissed; CI green run 32648809792 @ 798d9504155b23b60210a166bd1871a1a4538327; reviews/r2-fixes.md
2026-08-23T15:38:38Z progress phase=30 marker=reviews/r2-fixes.md
2026-08-23T15:38:38Z 30 r2 judge dispatch pending
2026-08-23T15:39:44Z 30 r2 judge dispatched (thread sthr_01EwoXCdpgA7NCDSF2zdhJcf) on sha 798d9504155b23b60210a166bd1871a1a4538327
2026-08-23T15:39:44Z heartbeat phase=30
2026-08-23T15:47:20Z 30 r2 verdict returned: blocking:0 / BLOCKING:0 agree; all 13 checklist items PASS at 798d9504155b23b60210a166bd1871a1a4538327; reviews/r2-verdict.md
2026-08-23T15:47:20Z progress phase=30 marker=reviews/r2-verdict.md
2026-08-23T15:47:20Z 30 -> 40 phase transition: entering release
2026-08-23T15:47:20Z heartbeat phase=40
2026-08-23T15:48:10Z 40 builder dispatched for release (thread sthr_01Qz3e93WropTT2bvjPwqr3b); version plan 0.1.0+, policies from tools/ci/policies.json
2026-08-23T15:48:10Z heartbeat phase=40
2026-08-23T15:55:19Z 40 release dispatch 1 (v0.1.0) run 32649696984: ok=true canonical=true certify.ok=true (replay_liveness skipped/static) hosted_certification=certified secret_put=true; cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9
2026-08-23T15:55:19Z progress phase=40 marker=release-run-32649696984
2026-08-23T15:55:19Z 40 -> 50 phase transition: entering league
2026-08-23T15:55:19Z heartbeat phase=50
2026-08-23T15:56:41Z 50 seed 200: lseed_8f100285-e06a-4194-8ab4-cfc407719205 league_cc074076-5938-403e-81db-d278c031db6d
2026-08-23T15:56:41Z 50 division 200: div_a8171f6e-62bd-41e5-b470-f15d675faee9 (Competition, level 1)
2026-08-23T15:56:41Z 50 settings 200: ladder round_robin/filler_policy, elo mean, round_interval_minutes=15
2026-08-23T15:56:41Z progress phase=50 marker=league_cc074076-5938-403e-81db-d278c031db6d
2026-08-23T15:56:41Z heartbeat phase=50
2026-08-23T15:57:42Z 50 champion1 submit run 32650135326 ok=true sub_45532554-56c2-46e5-8a7f-abb857ee890d (escrow-drafter:v1, daveey)
2026-08-23T16:00:06Z 50 champion2 submit run 32650182901 ok=true sub_664a688e-c0cd-4712-bd35-b8d962c0ac59 (escrow-swapper:v1, daveey-1)
2026-08-23T16:00:06Z 50 policy-version UUIDs resolved: drafter=6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d swapper=ae792ad8-75d3-4eb6-aea3-4dfa8548907a(daveey-1) trader=0505950f-bd65-46d4-ac4a-b3d0ad40c11b hoarder=b07b36d6-c4aa-4dce-b5af-a3dc0f7a6016
2026-08-23T16:00:06Z 50 filler-policies 200: trader + hoarder registered, neither champion
2026-08-23T16:00:06Z 50 rounds-paused=false 200; trigger-round 200 (workflow ladder-league_cc074076-5938-403e-81db-d278c031db6d)
2026-08-23T16:00:06Z 50 rounds: round 1 failed (auto-fired at settings time, before fillers/champions — superseded), round 2 pending with both champions in entrant_attributions
2026-08-23T16:00:06Z progress phase=50 marker=sub_664a688e-c0cd-4712-bd35-b8d962c0ac59
2026-08-23T16:00:06Z 50 -> 60 phase transition: entering verify
2026-08-23T16:00:06Z heartbeat phase=60
2026-08-23T16:01:37Z 60 verifier dispatched (thread sthr_01U2RchApcy8Pu2t2GuRUuKM); 75-min round wait bound, polls refresh heartbeat
2026-08-23T16:01:37Z heartbeat phase=60
2026-08-23T16:02:04Z heartbeat phase=60
2026-08-23T16:02:04Z 60 poll rounds: 2:pending 1:failed (completed>=2: 0)
2026-08-23T16:07:04Z heartbeat phase=60
2026-08-23T16:07:04Z 60 poll rounds: 2:completed 1:failed (completed>=2: 1)
2026-08-23T16:12:51Z heartbeat phase=60
2026-08-23T16:12:51Z 60 poll rounds: 2:completed 1:failed (completed>=2: 1)
2026-08-23T16:17:54Z heartbeat phase=60
2026-08-23T16:17:54Z 60 poll rounds: 3:completed 2:completed 1:failed (completed>=2: 2)
2026-08-23T16:19:21Z heartbeat phase=60
2026-08-23T16:19:21Z 60 poll rounds: 3:completed 2:completed 1:failed (completed>=2: 2)
2026-08-23T16:28:22Z heartbeat phase=60
2026-08-23T16:28:22Z 60 poll rounds: 3:completed 2:completed 1:failed (completed>=2: 2)
2026-08-23T16:33:15Z heartbeat phase=60
2026-08-23T16:33:15Z 60 poll rounds: 4:completed 3:completed 2:completed 1:failed (completed>=2: 3)
2026-08-23T16:33:17Z heartbeat phase=60
2026-08-23T16:33:17Z 60 poll rounds: 4:completed 3:completed 2:completed 1:failed (completed>=2: 3)
2026-08-23T16:43:00Z heartbeat phase=60
2026-08-23T16:43:00Z 60 check 1 TRUE: rounds 2,3,4 completed (round 1 failed pre-fillers: "Temporal RoundWorkflow failed before settling the round.")
2026-08-23T16:43:00Z 60 check 2 TRUE: leaderboard daveey rank1 escrow-drafter:v1 elo 1043.75 rounds_played 3; daveey-1 rank2 escrow-swapper:v1 elo 956.25 rounds_played 3; fillers absent
2026-08-23T16:43:00Z 60 check 3 TRUE: ereq_52e240bb-5356-478b-9240-5505de228f4a completed, replay https://softmax-public.s3.amazonaws.com/replays/f17e146a-7e0d-4d30-85eb-645120b855fc.replay, participants daveey/daveey-1 non-filler + 2 is_filler
2026-08-23T16:43:00Z 60 check 4 FALSE: strict JSON ok, protocol escrow.replay.v1, results.reason complete — but champion seats 19/32 (59%) moves scripted==true (seat0 12/16, seat1 7/16); same on rounds 2 (18/32) and 3 (15/32)
2026-08-23T16:43:00Z 60 check 5 FALSE: 19 'falling back' occurrences in hosted log; cause = escrow rune legality rejections (unfunded LOCK, "not addressed to you", bad_condition, EOF expected); 0 'LLM provider is unavailable'; cross-check contagion+raid latest logs clean => not a platform cause
2026-08-23T16:43:00Z 60 check 6 TRUE: raw-HTML iframe grep empty (client-rendered); SSR state.playlist[0] featured match escrow.r4.e1; POST /coworlds/replays/session -> static /v2/coworlds/replays/static/cow_65c18d00.../sha256%3A0e1cafee.../index.html?replay=... ready:true
2026-08-23T16:43:00Z 60 check 7 TRUE: committed runs/2026-08-23-escrow/release-result.json .certify.replay_liveness = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"
2026-08-23T16:43:00Z 60 check 8 TRUE: viewer-check run 32652062253 loaded:true ms=4011 failure:null bridge ready; scrub 0%="TURN 0" 50%="TURN 0 / 16 · WAITING ON 4" 100%="TURN 16 / 16 · FINAL"; corroborating run 32651276492 (round 3) 50%="TURN 8 / 16"; artifacts in runs/2026-08-23-escrow/viewer-check/
2026-08-23T16:43:00Z 60 VERIFY.md written: 6 TRUE / 2 FALSE (checks 4 and 5, single root cause = champion LLM prompts emit illegal contract runes)
2026-08-23T16:44:31Z 60 verifier returned: 6 TRUE / 2 FALSE (check 4: champion fallback share 59%/47%/56% over rounds 4/3/2; check 5: 19 'falling back' lines — illegal DSL from both champion prompts, 0 Bedrock-capacity, 0 max_tokens); VERIFY.md + viewer-check/ written
2026-08-23T16:44:31Z progress phase=60 marker=VERIFY.md-r4-checks-6of8
2026-08-23T16:44:31Z 60 ruling (rails: policy prompts): remediation is prompt-side — rewrite both champion prompts (free-stock accounting before LOCK, SIGN only offers addressed to you and payable, exact IF grammar), re-release v0.1.1, resubmit champions as v2, re-verify checks 1-5 on fresh rounds. Not a Blocked condition.
2026-08-23T16:44:31Z heartbeat phase=60
2026-08-23T16:45:58Z 60 remediation builder dispatched (thread sthr_01UeRakBzEFS3eRKsa9vt4ox): rewrite champion prompts (legality drills), re-release v0.1.1 -> drafter:v2/swapper:v2
2026-08-23T16:45:58Z heartbeat phase=60
2026-08-23T17:15:08Z 60 remediation builder returned: prompts rewritten (sha 5f8edf8, CI 32652942677 green); release 0.1.1 run 32653108817 canonical-race fail -> 0.1.2 run 32653621867 ok canonical certified secret_put; cow_add93c03-c2c9-455e-bc63-d2495fdcd2af; labels all :v3 (uploads do not dedupe on this deployment)
2026-08-23T17:15:08Z progress phase=60 marker=release-run-32653621867
2026-08-23T17:17:45Z 50/60 champions resubmitted as v3: drafter run 32654255979 ok sub_991f6f27, swapper run 32654297598 ok sub_728547e1 (daveey-1)
2026-08-23T17:17:45Z 50/60 filler-policies updated to v3 UUIDs (trader 9d09a38a, hoarder 3ed1facb); trigger-round issued 2026-08-23T17:17:45Z
2026-08-23T17:17:45Z progress phase=60 marker=sub_728547e1-caa0-4eef-846c-31160a580fd1
2026-08-23T17:17:45Z heartbeat phase=60
2026-08-23T17:18:44Z 60 verifier re-dispatched (thread sthr_01PM3ittaG5y6B317vUVm2xU) for post-remediation verification against v3 rounds (round 8+)
2026-08-23T17:18:44Z heartbeat phase=60
2026-08-23T17:19:20Z heartbeat phase=60
2026-08-23T17:19:20Z 60 poll rounds: 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 0)
2026-08-23T17:24:28Z heartbeat phase=60
2026-08-23T17:24:28Z 60 poll rounds: 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 0)
2026-08-23T17:29:22Z heartbeat phase=60
2026-08-23T17:29:22Z 60 poll rounds: 8:pending(v3) 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 0)
2026-08-23T17:34:16Z heartbeat phase=60
2026-08-23T17:34:16Z 60 poll rounds: 8:completed(v3) 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 1)
2026-08-23T17:39:37Z heartbeat phase=60
2026-08-23T17:39:37Z 60 poll rounds: 8:completed(v3) 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 1)
2026-08-23T17:44:30Z heartbeat phase=60
2026-08-23T17:44:30Z 60 poll rounds: 9:pending(v3) 8:completed(v3) 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 1)
2026-08-23T17:49:23Z heartbeat phase=60
2026-08-23T17:49:23Z 60 poll rounds: 9:completed(v3) 8:completed(v3) 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 2)
2026-08-23T17:49:24Z heartbeat phase=60
2026-08-23T17:49:24Z 60 poll rounds: 9:completed(v3) 8:completed(v3) 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 2)
2026-08-23T17:50:57Z heartbeat phase=60
2026-08-23T17:50:57Z 60 poll rounds: 9:completed(v3) 8:completed(v3) 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 2)
2026-08-23T17:52:32Z heartbeat phase=60
2026-08-23T17:52:32Z 60 poll rounds: 9:completed(v3) 8:completed(v3) 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed (completed v3: 2)
2026-08-23T17:57:29Z 60 attempt 2 (post-remediation, v3) check 1 TRUE: v3 rounds 8 (round_946f98fa) + 9 (round_3ee96829) completed after fillers set 17:17:45Z; rounds 2-7 excluded (v1 entrants), round 1 excluded failed "Temporal RoundWorkflow failed before settling the round."
2026-08-23T17:57:29Z 60 attempt 2 check 2 TRUE: daveey-1 rank1 escrow-swapper:v3 elo 1010.46 rounds_played 8; daveey rank2 escrow-drafter:v3 elo 989.54 rounds_played 8; fillers absent
2026-08-23T17:57:29Z 60 attempt 2 check 3 TRUE: round 9 ereq_73571e3e-28b4-47aa-8132-ef472f02392e completed, replay https://softmax-public.s3.amazonaws.com/replays/7d6b61ae-7b27-400d-b6e2-310d5c848e11.replay, seats 0/1 = drafter:v3 (daveey) / swapper:v3 (daveey-1) is_filler false
2026-08-23T17:57:29Z 60 attempt 2 check 4 FALSE: strict JSON ok, protocol escrow.replay.v1, results.reason complete — champion moves scripted 13/32 (40.6%) round 9 (seat0 5/16, seat1 8/16), 10/32 (31.3%) round 8; also signed [0,0,0,0] and 0 sign/settle events in round 9 (14 offers all expired)
2026-08-23T17:57:29Z 60 attempt 2 check 5 FALSE: 13 'falling back' lines round 9 (10 round 8) after decoding the b'...' container reprs; cause 'C<n> is not addressed to you' 22/35 rejected attempts; 0 'LLM provider is unavailable', 0 'cut off at max_tokens', 0 'rejected' => platform exception not applicable
2026-08-23T17:57:29Z 60 attempt 2 check 6 TRUE: raw-HTML grep empty (client-rendered); SSR state.playlist[0] = escrow.r9.e1 on cow_add93c03 v0.1.2 (not stale); POST /coworlds/replays/session -> /v2/coworlds/replays/static/cow_add93c03-c2c9-455e-bc63-d2495fdcd2af/sha256%3A292118f0.../index.html?replay=... ready:true
2026-08-23T17:57:29Z 60 attempt 2 check 7 TRUE: committed runs/2026-08-23-escrow/release-result.json (v0.1.2 run 32653621867) .certify.replay_liveness = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"
2026-08-23T17:57:29Z 60 attempt 2 check 8 TRUE: viewer-check run 32656128193 (fresh dispatch 17:50:31Z) loaded:true ms=3034 failure:null bridge ready; scrub 0%="TURN 0" 50%="TURN 0 / 16 · WAITING ON 4" 100%="TURN 16 / 16 · FINAL"; scorebug:""/feed_lines:0 = known generic-probe gap; artifacts runs/2026-08-23-escrow/viewer-check/round9-32656128193/
2026-08-23T17:57:29Z 60 VERIFY.md rewritten (attempt 2): 6 TRUE / 2 FALSE — checks 4 and 5, root cause unchanged in kind (champion prompts SIGN contracts addressed to another cog) though reduced from 59% to 31-41% fallback
2026-08-23T17:57:29Z heartbeat phase=60
2026-08-23T17:58:48Z 60 verifier attempt 2 returned: 6 TRUE / 2 FALSE (check 4: 40.6%/31.3% champion fallbacks on rounds 9/8; check 5: 13/10 falling-back lines). Dominant residual: 22/35 'not addressed to you' signs; new modes: leading-alias syntax 3/35, trailing-prose EOF 6/35. unfunded + bad_condition eliminated by remediation 1.
2026-08-23T17:58:48Z progress phase=60 marker=VERIFY.md-r9-attempt2
2026-08-23T17:58:48Z 60 ruling: remediation 2 = different approach (game-side): observation gains precomputed SIGNABLE-NOW list + SPENDABLE per good, extractJsonObject tolerates trailing prose, offer-text normalization (strip leading non-OFFER line, truncate after ELSE); prompts reinforce addressing; release 0.1.3 -> v4
2026-08-23T17:58:48Z heartbeat phase=60
2026-08-23T17:59:44Z 60 remediation-2 builder dispatched (thread sthr_01TyZ9tJ29bhNkd2C8K1fjij): SIGNABLE-NOW observation, tolerant extraction, offer normalization, prompt tweak, release 0.1.3
2026-08-23T17:59:44Z heartbeat phase=60
2026-08-23T18:24:41Z 60 remediation-2 builder returned: 4 commits (head c155695: SIGNABLE-NOW observation + tolerant extraction + offer normalization + prompts v4), CI 32657199935 green, release 0.1.3 run 32657361152 ok/canonical/certified first dispatch; cow_9b73db59-4be9-4a59-9e56-5eed9151a871, labels :v4
2026-08-23T18:24:41Z progress phase=60 marker=release-run-32657361152
2026-08-23T18:26:37Z 60 v4 champions resubmitted: drafter run 32657967398 ok sub_7fc0e093, swapper run 32658006933 ok sub_da3bf046 (daveey-1)
2026-08-23T18:26:37Z 60 filler-policies updated to v4 (trader fb6d64e0, hoarder d9d3f7f8); trigger-round issued
2026-08-23T18:26:37Z progress phase=60 marker=sub_da3bf046-c492-4b45-ab2c-f82868a3138b
2026-08-23T18:26:37Z heartbeat phase=60
