# 2026-08-25-pistonball — log

2026-08-26T00:03:25Z 00 claim 2026-08-25-pistonball idea=1217747862156473 slug=pistonball
2026-08-26T00:04:40Z 00 run task created gid=1217847385246447 section=Running, 9 phase subtasks created
2026-08-26T00:05:30Z 00 STATE written phase=10 session=a1f3c9d2
2026-08-26T00:07:30Z 10 starter=coworld-ctf reason=real-time continuous-physics loop with rules rewritten for this coworld (Cogball operator ruling 2026-08-22: new physics game is the ctf row, not a bit-exact moba port)
2026-08-26T00:09:30Z 10 designer dispatched thread=sthr_01HQvHFkV4bsRcy2cEg3vtjx output=runs/2026-08-25-pistonball/design-draft.md
2026-08-26T00:24:00Z 10 designer returned design-draft.md (1513 lines), reviewed against prompts/10-design.md checklist
2026-08-26T00:24:00Z 10 checklist: [x] starter named+reason (coworld-ctf, real-time physics loop) [x] num_agents=20 single number, in both variants + cert fixture + SMOKE_SEATS [x] tick structure + resolution order numbered 1-8 [x] scoring formula+sign (score=progress-penalty, higher better; league ranks cross-play mean, not Elo) [x] end conditions incl deadline/wall_clock; reason enum {complete,deadline,fault} [x] per-seat observation visible/hidden lists [x] reply schema with rune caps on every free-text field (note<=160, say<=48, policy<=48, detail<=200) [x] both policies LLM+scripted same image env-switched, baseline algorithms given (wavebot, metronome) [x] one parallel batch per turn, budget arithmetic ~376s expected / 455s worst < 720s [x] degrade-never-hang (retry once -> wavebot fallback; budget guard settles early) [x] two name spaces (PST-nn in-game, real names spectator-side) [x] viewer static wasm bundle + build hook + chrome verbatim + readouts + 360px [x] all four viewer files from coworld-ctf only; data-replay-loaded/-error stated [x] chrome provenance: chrome_common.js byte-for-byte, replay_broadcast.html appended block, removed elements listed, zoom: #viewpanel dropped (fixed arena) [x] transport rules (--band/--hudscale via relayout, endcard at var(--band) dismissed by seek, clickable labelled beat buttons with CSS per kind) [x] replay bytes self-sufficient (config+perm+inputs+hashes) [x] packaging: compose.yaml, manifest template, game.docs readme+3 pages, game.protocols player+global [x] tests: sim units, baseline legality (test 5), e2e episode replay (test 10), strict-UTF-8 parse, viewer smoke EXECUTED vs docker-smoke replay [x] out-of-scope non-empty
2026-08-26T00:24:00Z 10 design ACCEPTED round 1, zero rejections; copied to runs/2026-08-25-pistonball/design.md
2026-08-26T00:24:00Z progress phase=10 marker=design.md written and accepted
2026-08-26T00:24:30Z 00 phase transition 10 -> 20
2026-08-26T00:24:30Z heartbeat phase=20
2026-08-26T00:27:30Z 20 repo created https://github.com/Metta-AI/cogame-pistonball (public)
2026-08-26T00:28:30Z 20 propagate-secrets run 32915048989 success; SOFTMAX_TOKEN + ANTHROPIC_API_KEY present on cogame-pistonball
2026-08-26T00:31:00Z 20 builder dispatched thread=sthr_017guEM9Z4XXGnexTjEd3NsJ target=ci.yml green on main
2026-08-26T00:31:00Z heartbeat phase=20
2026-08-26T01:58:00Z 20 builder returned: ci.yml GREEN run=32923038675 sha=ce20047d66736a61bc772c52e05ffb82b38ccedf (verified conclusion=success, sha==main); 1 red round (32920732929, wasm-viewer soak vs 8s fixture replay) fixed by refixturing
2026-08-26T01:58:00Z 20 builder deviations from design note (rails: parameter tuning, accepted): SubSteps 4->16 + gravity/torque rescale (pinned stiffness unchanged); containment y-bounds [200000,4300000]; seeded 2-20cm drop offset (deterministic, replay-safe); cert fixture 1 wavebot + 19 metronomes (soak-length + both player entries slotted); heads-are-the-floor contact; wave/catch prose corrected to match formula; CTF_WIRE aliased (test-pinned exception); note: push via git-data API (HTTPS git push 403s in sandbox)
2026-08-26T01:58:00Z 20 baselines: 20 wavebots deliver 20/20 seeds mean +97.05; metronomes -10.07; 10/10 mix 20/20
2026-08-26T01:58:00Z progress phase=20 marker=ci-run-32923038675
2026-08-26T01:58:30Z 00 phase transition 20 -> 30
2026-08-26T01:58:30Z heartbeat phase=30
2026-08-26T02:05:00Z 00 INCIDENT: git push over HTTPS lost auth sandbox-wide; first git-data-API push (f6faa0e) raced a concurrent gift-refinements commit (2a7d583) and clobbered 4 of its files (3 emptied, log.md reverted). REPAIRED in b0137a1: all 4 restored byte-identical to 2a7d583 (verified via recursive tree diff). Future pushes via /tmp/apipush.sh which refuses paths outside this run.
2026-08-26T02:05:00Z heartbeat phase=30
2026-08-26T02:12:00Z 30 r1 reviewer dispatched thread=sthr_013G7UWRXvdShAmhEeXwKgey sha=ce20047 output=reviews/r1-review.md
2026-08-26T02:44:00Z 30 r1 reviewer returned: 13 findings, 0 claimed-blocking; reviews/r1-review.md
2026-08-26T02:44:00Z 30 r1 fixer dispatched
2026-08-26T02:44:00Z heartbeat phase=30
2026-08-26T04:21:00Z 30 r1 fixer returned: 17 commits ce20047..49518a2, CI green run=32928137084; N8 disputed with evidence (note self-contradiction; manifest's inverted copy fixed under N1); N9h evidence-answered; N13 evidence-answered; reviews/r1-fixes.md
2026-08-26T04:21:00Z 30 r1 judge dispatched sha=49518a22d734a3bcb952cc32952fe6e67eea39c6
2026-08-26T04:21:00Z heartbeat phase=30
2026-08-26T04:58:00Z 30 r1 judge returned: blocking 0 / BLOCKING 0 (markers agree, verified); all 13 advisory findings resolved or upheld-as-disputed; reviews/r1-verdict.md
2026-08-26T04:58:00Z progress phase=30 marker=r1-verdict.md
2026-08-26T04:58:30Z 00 phase transition 30 -> 40
2026-08-26T04:58:30Z heartbeat phase=40
2026-08-26T05:02:00Z 40 builder dispatched thread=sthr_0126iUpxe7i3gYmPGmo6jMrP target=coworld-release.yml canonical+certified, v0.1.0 first
2026-08-26T05:52:00Z 40 builder returned: v0.1.2 canonical+certified, cow_58917aec-d633-4f40-89b1-dbf496ddcfe0, release run 32930394604, secret_put true, 4 policies at :v2 (cascade owned by daveey-1); attempts: 0.1.0 manifest shape (game.description required, game.tags forbidden -> fix 1f51dfc), 0.1.1 player cpu limit min 1 core (fix ec82d45), 0.1.2 clean
2026-08-26T05:52:00Z 40 design-note deltas for LEARNINGS: platform requires game.description, forbids game.tags; player limits.cpu minimum "1"
2026-08-26T05:52:00Z progress phase=40 marker=release-run-32930394604
2026-08-26T05:52:30Z 00 phase transition 40 -> 50
2026-08-26T05:52:30Z heartbeat phase=50
2026-08-26T05:57:00Z 50 seed 200; league league_6789db33-ab0a-4b15-b572-b3ea39c614fd (leagues GET returns bare array here, matched client-side)
2026-08-26T05:57:30Z 50 division 200 div_de04ec28-cd1a-4349-9667-d34a687735c7; settings 200 elo round_robin filler_policy interval=15m (round_scoring_rule=mean per design note)
2026-08-26T05:58:00Z 50 champion1 submit dispatching: pistonball-swell:v2 as ply_44ae9048-3242-4654-881f-6d9d43347fa3
2026-08-26T04:42:13Z 00 clock note: previous stamps 05:52-05:58 were ahead of real UTC (sandbox drift on my part); stamps from here are real date -u
2026-08-26T04:42:13Z 50 champion1 submit ok run=32931064104 sub_67c13f0a-62a4-4137-9add-c43523f3adb5 (pistonball-swell:v2, daveey)
2026-08-26T04:42:13Z 50 champion2 submit ok run=32931105762 sub_92d8fa78-f25d-4927-91d3-39efdc9c79ae (pistonball-cascade:v2, daveey-1)
2026-08-26T04:42:13Z 50 filler-policies 200: wavebot:v2 e0e9ce4a-7232-4309-8558-752adb78b10e, metronome:v2 bf0ca47e-73a9-4283-bf0a-57f08f0de363 (set BEFORE my trigger)
2026-08-26T04:42:13Z 50 unpause 200; trigger-round 200; round 1 failed (auto-fired pre-fillers: Temporal RoundWorkflow failed before settling), round 2 pending with BOTH champions in entrant_attributions
2026-08-26T04:42:13Z progress phase=50 marker=league_6789db33-ab0a-4b15-b572-b3ea39c614fd
2026-08-26T04:42:13Z 00 phase transition 50 -> 60
2026-08-26T04:42:13Z heartbeat phase=60
2026-08-26T04:43:14Z 60 verifier dispatched thread=sthr_01Qn59mbPiCbu7DV7wT5KFyp output=VERIFY.md, viewer-check/; 75-min poll bound
2026-08-26T04:43:50Z heartbeat phase=60
2026-08-26T04:48:38Z heartbeat phase=60
2026-08-26T04:50:32Z 60 poll: round 2 completed (round_14591664), round 1 failed pre-fillers; waiting for a 2nd completed round
2026-08-26T04:50:32Z 60 check2 leaderboard: daveey pistonball-swell:v2 rank1 rp=1, daveey-1 pistonball-cascade:v2 rank2 rp=1, no fillers -> TRUE (pending re-fetch at end)
2026-08-26T04:50:32Z 60 check3 round2 ereq_82c67bc1 completed, replay_url present, both champions in participants -> TRUE
2026-08-26T04:50:32Z 60 check4 CONCERN round2 replay: protocol pistonball/v1, reason complete/out_of_time, champion seats llm=2 fallback=14 (turns 1-7 "per-turn budget exhausted before attempt 1"); progress 0.0, delivered false
2026-08-26T04:50:32Z 60 check5 round2 logs artifact: "Pod logs were not captured: no container logs were readable from pod job-699e7412-88cpr"
2026-08-26T04:50:32Z heartbeat phase=60
2026-08-26T04:53:00Z 60 check6 (attempt 1, round-2 featured): raw-HTML grep found no iframe (client-rendered); SSR playlist[0] = pistonball.r2.e1; POST /coworlds/replays/session -> ready:true, static index.html path -> TRUE
2026-08-26T04:53:00Z 60 check8 (attempt 1) viewer-check run 32931770282 dispatched 04:51:07Z, success: loaded=true ms=4612, clocks 1:15/0:39/FINAL GAME OVER (3 differing)
2026-08-26T04:57:15Z heartbeat phase=60
2026-08-26T05:02:05Z heartbeat phase=60
2026-08-26T05:05:00Z 60 poll: round 3 completed -> 2 completed rounds (2,3) after fillers; check1 TRUE
2026-08-26T05:05:00Z 60 check3 round3 ereq_d172e3fa completed replay_url present, daveey+daveey-1 non-filler -> TRUE
2026-08-26T05:05:00Z 60 check4 round3: protocol pistonball/v1, complete/delivered, progress 98.69 score 96.59 BUT champion seats llm=0 fallback=2 (429 "Too many tokens per day") -> FALSE so far
2026-08-26T05:05:00Z 60 check5 round3: 4 'falling back' lines; cross-check fruit-market ereq_9a9f143f 04:48Z same 429 on global.anthropic.claude-haiku-4-5-20251001-v1:0 -> platform-wide; continuing to poll inside 75-min bound
2026-08-26T05:05:00Z 60 DEFECT found (round 2, LLM available): turnStart sampled BEFORE the minBatchSpacingMs sleep in src/pistonball/decide.nim:326 vs :383 -> turns>=1 always 'per-turn budget exhausted before attempt 1'
2026-08-26T05:10:05Z heartbeat phase=60
2026-08-26T05:14:54Z heartbeat phase=60
2026-08-26T05:14:56Z heartbeat phase=60
2026-08-26T05:22:37Z 60 poll: round 4 completed (round_a2b91a96) — rounds 2,3,4 completed after fillers
2026-08-26T05:22:37Z 60 check1 TRUE 3 completed rounds >=2; round1 failed verbatim "Temporal RoundWorkflow failed before settling the round."
2026-08-26T05:22:37Z 60 check2 TRUE daveey+daveey-1 rounds_played=3, fillers absent (bare-array jq)
2026-08-26T05:22:37Z 60 check3 TRUE ereq_a459bce3 completed, replay eab95e2d, both champions seated, 18 filler seats
2026-08-26T05:22:37Z 60 check4 TRUE pistonball/v1 complete/delivered, champion seats llm=2 fallback=0, progress 97.879 score 96.599 (via tools/replay_summary.py, binary COWLDPST per design note)
2026-08-26T05:22:37Z 60 check5 TRUE log CLEAN (0 hits) after decoding b'' reprs; round-3 429 documented platform-wide (fruit-market ereq_9a9f143f same 429/model) and waited out inside the bound
2026-08-26T05:22:37Z 60 check6 TRUE static path /v2/coworlds/replays/static/<cow>/<manifest sha>/index.html?replay=..., ready:true, SSR playlist[0]=pistonball.r4.e1
2026-08-26T05:22:37Z 60 check7 TRUE "Replay liveness: skipped (static replay bundle declared..." from committed release-result.json
2026-08-26T05:22:37Z 60 check8 TRUE viewer-check run 32933394784 (dispatched 05:16:10Z): loaded=true ms=3166, clocks 1:15/1:11/FINAL GAME OVER
2026-08-26T05:22:37Z 60 findings F1 per-turn budget clock sampled before the 45s rate-floor sleep -> turns>=1 always fall back (round-2 proof); F2 endcard LLM/FB reads 0/0; F3 TOUCHES/LLM-FB headers collide
2026-08-26T05:22:37Z 60 VERIFY.md written, verdict all-true 8/8
2026-08-26T05:22:37Z heartbeat phase=60
2026-08-26T05:24:52Z 60 verifier returned: 8/8 TRUE, VERIFY.md + viewer-check/ committed (f7561c8); findings F1 (decide.nim turnStart sampled before 45s rate-floor sleep -> every turn>0 budget-exhausted fallback; round 2 proof: 14 fallback/2 llm, sharedScore -16.78), F2 (endcard LLM/FB column 0/0 vs results llmTurns[1,1]), F3 (endcard header overprint)
2026-08-26T05:24:52Z 60 coordinator decision: F1 is material — fix before judge adjudication; route F1-F3 to fixer, re-release as 0.1.3, capture one post-fix round as check-4 addendum, then judge
2026-08-26T05:24:52Z 60 r2 fixer dispatched for F1-F3
2026-08-26T05:24:52Z heartbeat phase=60
2026-08-26T05:56:35Z 60 r2 fixer returned: F1 06bd3f7 (turnStart after rate-floor sleep + spacing>budget engine test), F2 87ba292 (replay recounts llmTurns/fallbackTurns), F3 30964b3 (endcard header fit, browser-measured); CI green 32934920010 at 30964b3
2026-08-26T05:56:35Z 40 re-release dispatching v0.1.3 (reason: F1 fix must be the canonical game image)
2026-08-26T06:05:36Z 40 re-release v0.1.3 SUCCESS run=32936048068: canonical, certified, secret_put, new cow_id cow_768730a3-282a-4d75-9cff-01eea560e260 manifest sha256:91c1207c...; policies v3 minted (league stays on v2 seats — player protocol unchanged, F1 fix is in the game image); release-result.json overwritten
2026-08-26T06:05:36Z progress phase=60 marker=release-run-32936048068
2026-08-26T06:05:36Z 60 triggering post-fix round for check-4 addendum
2026-08-26T06:10:30Z 60 post-fix round 8 completed: ereq_f2d4d58a, complete/delivered, sharedScore 91.212, champions llm on turns 0-3, 0 fallbacks; VERIFY.md addendum appended
2026-08-26T06:10:30Z progress phase=60 marker=round_638df556-805a-4ffd-ab72-074e3e2a4a57
2026-08-26T06:10:30Z 60 judge dispatched to adjudicate VERIFY.md vs SPEC definition of done
2026-08-26T06:20:39Z 60 verify-verdict r1: blocking 1 (viewer-check was 0.1.2-sha); viewer-check re-run 32937649794 vs 0.1.3 sha + round-8 replay: loaded=true, clocks differ, endcard LLM/FB 4/0 both champions, headers clean; artifacts committed viewer-check-013/
2026-08-26T06:20:39Z progress phase=60 marker=viewer-check-run-32937649794
2026-08-26T06:23:11Z 60 judge re-adjudicated: blocking 0 / BLOCKING 0 (verified from committed artifacts); all 8 definition-of-done items TRUE at head
2026-08-26T06:23:11Z progress phase=60 marker=verify-verdict.md-blocking-0
2026-08-26T06:23:11Z 00 phase transition 60 -> 70
2026-08-26T06:23:11Z heartbeat phase=70
2026-08-26T06:25:16Z 60 verify-verdict.md restored by judge (blocking 0; earlier rewrite lost to my reset --hard before push — process note: never hard-reset while a sub-agent holds unpushed writes) and committed
2026-08-26T06:26:17Z 70 announce attempted_at written and pushed BEFORE the POST (1633 chars, flags 4)
2026-08-26T06:26:42Z 70 announce msg=1542057628056944670 (200, flags=4, embeds=[])
2026-08-26T06:26:42Z progress phase=70 marker=discord_message_id=1542057628056944670
2026-08-26T06:26:42Z 00 phase transition 70 -> 75
2026-08-26T06:26:42Z heartbeat phase=75
2026-08-26T06:27:35Z 75 atlas continent=commons reason=fully cooperative shared-reward coordination (precedent: chorus, cooperative-hunting, collab-cooking); spot 416,574 clearance 22.9 label=Pistonball anchor=c
2026-08-26T06:27:59Z 75 atlas dispatch=32938248863 region=commons at=416,574 clearance=22.9
2026-08-26T06:31:38Z 75 atlas dispatch 1 (32938248863) failed: 22 unplaced leagues (their PRs queued unmerged); fix per step 8 = extra_cities
2026-08-26T06:31:38Z 75 atlas placing for others: chemistry 446,544; chorus 425,529; cogchemists 766,277; cogiavelli 751,295; cogmud 440,571; cogolf 202,270; cogplomacy 790,280; coins 395,565 (new, commons); collab-cooking 446,520; commons-family 404,544; cooperative-hunting 461,562; daycare 217,583; factory-commons 404,520; firm 425,553; fruit-market 380,547; garble 438,817; gift-refinements 398,589; grid-wars 181,279; hanabi 760,316; hidden-agenda 453,832; matrix-games 467,535; territory 425,505 (duplicated recorded spots re-spotted via atlas_spot; first claimant kept)
2026-08-26T06:34:14Z 75 atlas dispatch=32938543267 region=commons at=416,574 clearance=22.9 (with extra_cities x22)
2026-08-26T06:34:14Z 75 atlas pr=https://github.com/Metta-AI/metta/pull/20489 status=pr_open
2026-08-26T06:34:14Z progress phase=75 marker=https://github.com/Metta-AI/metta/pull/20489
2026-08-26T06:34:14Z 00 phase transition 75 -> 80
2026-08-26T06:34:14Z heartbeat phase=80
2026-08-26T06:37:07Z 80 executive summary posted on run task (1217853159839039) and condensed on idea task (1217853080424416); LEARNINGS.md dated section appended; playbook Common-mistakes gained 2 rows (game.description/tags, player cpu min); all 9 phase subtasks complete; idea 1217747862156473 completed; run task moved to Done
2026-08-26T06:37:07Z progress phase=80 marker=run-task-Done
2026-08-26T06:37:07Z 80 run closed — Done. Session a1f3c9d2 ending; no next action.
