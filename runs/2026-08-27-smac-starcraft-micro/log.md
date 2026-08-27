# 2026-08-27-smac-starcraft-micro — log

2026-08-27T04:00:30Z 00 claim comment posted on idea 1217748613153120 (story 1217890744283311)
2026-08-27T04:00:55Z 00 claim re-check after 20s: no competing claim comment — claim holds
2026-08-27T04:01:45Z 00 run task created gid=1217890744511822 section=Running + 9 phase subtasks (10..80)
2026-08-27T04:02:01Z 00 heartbeat_at custom field set on run task
2026-08-27T04:02:20Z 00 claim 2026-08-27-smac-starcraft-micro idea=1217748613153120 slug=smac-starcraft-micro session=c7061c35
2026-08-27T04:02:20Z 00 startability: real-time tick-loop micro combat, one cog per unit vs scripted enemy -> coworld-ctf starter row (SPEC pin: ANY real-time loop with new rules); idea names Metta-AI/coworld-bw (not a mounted starter) as base and itself sanctions a dependency-free SMAX-style clone -> coworld-bw is RULES/SCENARIO REFERENCE only, ships as new public Metta-AI/cogame-smac-starcraft-micro per trick-taking/poker EXTENSION precedent; not confidential
2026-08-27T04:02:20Z 00 phase transition 00 -> 10
2026-08-27T04:02:20Z heartbeat phase=10
2026-08-27T04:02:51Z 10 starter=coworld-ctf (real-time tick-loop micro combat with new rules -> starter table row 2; knights-archers/paintball precedent; coworld-bw not mounted, SMAX-style dependency-free clone sanctioned by idea text)
2026-08-27T04:03:42Z 10 designer dispatched round=1 thread=sthr_017Jqbc4BQK9tbqahYk8o5DR output=runs/2026-08-27-smac-starcraft-micro/design-draft.md session=c7061c35
2026-08-27T04:20:40Z 10 designer returned round=1 file=design-draft.md (1531 lines)
2026-08-27T04:20:40Z 10 checklist: [x] starter=coworld-ctf+reason (real-time micro loop, new rules; coworld-bw not mounted -> reference only per binding ruling) [x] num_agents=5 single unambiguous (SMAC 2s3z shape) in all 4 variants (default/outnumbered/corridor/heavy) + certification.game_config + SMOKE_SEATS=<SEATS>=5 [x] resolution rules numbered: server frame steps 1-5 + sim.step 6.1-6.9 + hash step 7 + battle-switch step 8; wipe evaluated before victory [x] scoring battle=0.6*won+0.3*dmgFrac+0.1*(1-lossFrac), teamScore=sum/maxGames in [0,1] higher-better identical all seats, creditEpsilon 0.0004 < 0.000606 one-ranger-shot proof, league ranks Elo over results.scores [x] end conditions: reason enum {complete,deadline,fault}, endRule enum {victory,wipe,full_time,wall_clock,sim_fault,host_error}, deadline case defined + declared acceptable, wall-clock stop as load-bearing record (particle-worlds scar) [x] per-seat observation: fogOfWar false, visible list + hidden list (seeds, RNG, others' current-turn directives, prompts, real names) [x] reply schema rune caps (note 160, id 16, say 10, policy 48, detail 200, directive record 900, prompt 4000) + rune-boundary truncation + tolerant parsing [x] both policies same image env-switched: PLAYER_PROMPT champions marshal(daveey)/skirmish(daveey-1) with full prompts, PLAYER_SCRIPTED=focusfire|charge with exact algorithms [x] parallel batch: all 5 seats one batch/turn, attempt1 6000ms + retry 3000ms <= turnBudget 10000ms, turnSpacing 12000ms -> 25 rpm < 30 cap; expected 317s worst 612s stop 690s < 720s=60% of 1200 [x] degrade: retry once -> focusfire fallback, throttle no-retry fail-fast, budget guard early settle, no-creds offline instant, no failure leaves unit unactuated [x] two name spaces (RANGER-*/BLADE-*/E<n> in-game, real names spectator-only, test_identity_privacy both directions) [x] viewer: static wasm bundle + build hook executable + mkdir-before-containment (ecos scar); ALL FOUR files from coworld-ctf only (config.nims non-modularized onRuntimeInitialized set, smac_replay.nim, static_replay*.js, index.html); data-replay-loaded on first drawn frame + data-replay-error; ready posted after loaded (chorus scar) [x] chrome provenance: chrome_common.js byte-for-byte sha-pinned, broadcast_core.js single-identifier diff, replay_broadcast.html appended block (gridlock scar), removals listed exactly, zoom decided: #viewpanel dropped (fixed arena) [x] transport: --band/--hudscale on :root by relayout(), no overlay in band, endcard bottom var(--band) + dismissed by every seek, beats = clickable labelled buttons w/ CSS for all 5 kinds emitted and no others (tandem shadowing guard) [x] replay self-sufficient: COWLDSMC header + config (seed, mapSpec, roles, enemyRoles, constants) + joins + per-cog masks + chat records + per-tick hash; enemy re-derived from seed [x] packaging: compose smac_starcraft_micro -> {{SMAC_STARCRAFT_MICRO_IMAGE}}, manifest (no literal tokens, num_agents in variants not top-level, docs readme+4 pages text form, protocols player+global object form, results_schema 26 keys additionalProperties:false, arrays bounded, secret ns = game.name, cert fixture 5 scripted seats --timeout-seconds 300, limits.cpu "1") [x] tests: 14 suites incl bounded-orders/legality 500 states x both baselines x 5 seats (test_control), e2e replay + strict-UTF-8 + emoji boundary (test_replay), every-variant-constructs-sim (collab-cooking scar), docker_smoke SMOKE_SEATS=5 SMOKE_REQUIRE_REPLAY_JSON=0, wasm-viewer EXECUTES viewer_smoke.mjs vs docker-smoke replay + native<->wasm hash gate [x] out-of-scope 15 items — ACCEPTED round 1, zero rejections
2026-08-27T04:20:40Z 10 design.md copied; phase transition 10 -> 20
2026-08-27T04:20:40Z heartbeat phase=20
2026-08-27T04:20:40Z progress phase=10 marker=design.md
2026-08-27T04:22:06Z 20 repo created https://github.com/Metta-AI/cogame-smac-starcraft-micro (public)
2026-08-27T04:22:06Z 20 propagate-secrets run 33039164604 success; gh secret list shows SOFTMAX_TOKEN + ANTHROPIC_API_KEY
2026-08-27T04:22:06Z 20 rails: board art per design note §Art = starter's shipped soldier/rig real art (red=ours, blue=enemy, green=swarm recomposited); nano-banana not required (knights-archers/paintball ctf-lineage precedent — design note is authoritative)
2026-08-27T04:23:03Z 20 builder dispatched round=1 thread=sthr_01BF828ZQx4HSgwAVpqSXUVF session=c7061c35
2026-08-27T06:44:14Z 20 builder returned round=1: CI GREEN run 33046300533 sha=190ef840 on main (test+docker-smoke+wasm-viewer all success); exit checks pass (placeholders clean, 3 workflows active w/ pinned inputs+artifacts, exec bits 100755, viewer_smoke.mjs verbatim)
2026-08-27T06:44:14Z 20 infra note: sandbox git push rejected (credential path); builder pushed via Git Data API — later phases pushing repo content must use the API route
2026-08-27T06:44:14Z 20 builder deviations logged: (1) OPEN wasm hash mismatch ~tick 450 on cert-fixture replay, gate exits 0 without failing (AGENTS.md §OPEN; 3 floats already removed from hashed path; suspect diamondSpinAngle) (2) focusfire>charge strict only on default, spread asserted instead (3) deleted mechanics gated off not deleted (4) spawn lines not baked (5) swarm not recomposited 0.7x, blade keeps gun silhouette (6) test_viewer grep excludes pinned chrome_common.js (7) README real not template (8) record_fixture.sh + starter tests dropped
2026-08-27T06:44:14Z 20 phase transition 20 -> 30 review_round=1
2026-08-27T06:44:14Z heartbeat phase=30
2026-08-27T06:44:14Z progress phase=20 marker=33046300533
2026-08-27T06:45:07Z 30 reviewer dispatched r1 thread=sthr_012ZrDSuHWtjSBofkTAcomMM sha=190ef840 session=c7061c35
2026-08-27T07:10:35Z 30 reviewer returned r1: 8 blocking (B1 battleIndex hashed but not mirrored in playback -> deterministic mismatch at battle end; B2 no test replays anything; B3 wasm gate mis-wired reads display player not scan builder + under-sampled; B4 test loosened 6e21fe0 focusfire>=charge -> tautology; B5 lives-label not hidden under 640px; B6 armybars occlude scorebug plates; B7 no worst-case renderer fixture, canvas_text total 0; B8 no test asserts reason==complete) + 18 advisory; r1-review.md 224 lines
2026-08-27T07:11:24Z 30 fixer dispatched r1 thread=sthr_017rBaSS2s74DAZ9oJfxjQpU session=c7061c35
2026-08-27T07:11:24Z heartbeat phase=30
2026-08-27T09:11:52Z 30 fixer returned r1: r1-fixes.md; head=84b271b8 CI green run 33055917137; 19 commits (B1 advanceBattle one-proc live+playback, B2 native replay test found 2 recorder infidelities, B3 gate can fail + corrupt-hash test, B4 focus>charge strict all 4 variants via real control fixes + charge over-commit, B5/B6 viewer pins, B7 renderer text fixture + shoutBubbleMaxHeight live, B8 reason==complete, N9/N7a/N5 fixed, N1 disputed w/ evidence); deviation flagged: baselines' prose in design note refuted by measurement, docs/RULES.md+manifest regenerated to match code
2026-08-27T09:11:52Z 30 judge dispatched r1 sha=84b271b85f8f809699a90adbc89a538e59013f0f session=c7061c35
2026-08-27T09:11:52Z heartbeat phase=30
2026-08-27T09:23:26Z 30 judge returned r1: verdict blocking=0/BLOCKING=0 (r1-verdict.md); all B1-B8 resolved at head 84b271b8; independent 15-item checklist pass + parallel-batch rule; residue non-blocking
2026-08-27T09:23:26Z 30 phase transition 30 -> 40
2026-08-27T09:23:26Z heartbeat phase=40
2026-08-27T09:23:26Z progress phase=30 marker=r1-verdict.md
2026-08-27T09:24:14Z 40 builder dispatched thread=sthr_012ryiL2eaAfN5qGuA3su6xo (release chain, version 0.1.0 first, budget 3 dispatches) session=c7061c35
2026-08-27T10:10:16Z 40 builder returned: release 0.1.2 dispatch 3/3 green run=33060960111 cow_id=cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc canonical=true certified (liveness skipped-static) secret_put=true; 4 policies v3 (marshal/skirmish champions, focusfire/charge fillers), champion2 player_id=ply_bac48eb1; dispatch 1 (0.1.0) real lobby-pacing bug fixed 97b4c7bd (fastMode burned join grace), dispatch 2 (0.1.1) canonical completion race + bounded read-only confirm step bb0323da; release-result.json + release-summary.md committed
2026-08-27T10:10:16Z 40 template delta suggestion recorded: fold 'Confirm the Coworld is canonical' step into templates/coworld-release.yml (read-only bounded poll after secret put) — for phase 80 LEARNINGS
2026-08-27T10:10:16Z 40 phase transition 40 -> 50
2026-08-27T10:10:16Z heartbeat phase=50
2026-08-27T10:10:16Z progress phase=40 marker=33060960111
2026-08-27T10:11:51Z 50 seed POST /coworld-league-seeds 200 lseed_bbb867a2 league_id=league_f42b4821-882b-428e-b803-630671e86726
2026-08-27T10:11:51Z 50 division PUT 200 div_efd2ab9a-88fd-4c97-952c-64f38e3fadaa (Competition level 1)
2026-08-27T10:11:51Z 50 settings POST 200 (elo k=32 round_robin filler_policy, round_interval=15m)
2026-08-27T10:11:51Z 50 champion1 submit dispatching coworld-submit.yml policy=smac-starcraft-micro-marshal:v3 player=ply_44ae9048
2026-08-27T10:15:53Z 50 champion1 submit run 33061981148 success submit-result ok=true policy=smac-starcraft-micro-marshal:v3 player=ply_44ae9048
2026-08-27T10:15:53Z 50 champion2 submit run 33062051533 success submit-result ok=true policy=smac-starcraft-micro-skirmish:v3 player=ply_bac48eb1 (version owned by daveey-1 confirmed via /policy-versions)
2026-08-27T10:15:53Z 50 fillers POST 200: focusfire:v3=2964b7ba, charge:v3=a1ecf538 (neither champion)
2026-08-27T10:15:53Z 50 unpause POST 200 paused=false; trigger-round POST 200 workflow=ladder-league_f42b4821
2026-08-27T10:15:53Z 50 rounds: round 1 failed (fired at unpause instant 10:13:00Z, Temporal RoundWorkflow race; fillers WERE set prior) — round 2 (my trigger 10:13:38Z) pending with both champions in entrant_attributions (marshal:v3 ply_44ae9048, skirmish:v3 ply_bac48eb1) — exit criterion met
2026-08-27T10:15:53Z 50 phase transition 50 -> 60
2026-08-27T10:15:53Z heartbeat phase=60
2026-08-27T10:15:53Z progress phase=50 marker=league_f42b4821-882b-428e-b803-630671e86726
2026-08-27T10:17:01Z 60 verifier dispatched thread=sthr_019Pk1pYSHYZfudFhjMJj7db (8 checks, 75-min bound, replay_summary.py substitute for binary COWLDSMC per design note) session=c7061c35
2026-08-27T10:17:01Z heartbeat phase=60
2026-08-27T10:45:21Z 60 verifier returned: VERIFY.md 7/8 TRUE (1 rounds>=2: r2+r3 completed; 2 both champions ranked daveey-1 1001.47 / daveey 998.53; 3 ereq_bf914c1c completed replay_url ok; 4 COWLDSMC via replay_summary.py protocol ok reason=complete 37/38 champion directives llm; 6 static route sha=manifest_sha via SSR payload; 7 committed release-result liveness skipped-static; 8 viewer-check run 33063761313 loaded=true 3 clocks differ, chrome is the starter's) — check 5 FALSE: round-3 log 2x 'falling back' cause=parse_error 'reply named no commanded cog' (round 2: 1 hit, retry succeeded, 0 fallbackTurns); platform-429 exception REFUTED (all sidecar calls 200; knights-archers shows real 429s, this does not)
2026-08-27T10:45:21Z 60 adjudication (rails): check-5 hits are a real but small design deviation — design.md reply-schema repair table pins 'empty/missing cogs -> keep last turn's directive' and 'unmatched entry -> assign by position'; code instead treats it as parse_error -> retry -> focusfire fallback. Also attempt-1 interim log line contains literal 'falling back' even when the retry succeeds. Decision: targeted fix + release 0.1.3, then re-verify — not a check weakening, not Blocked
2026-08-27T10:45:21Z 60 verifier template finding recorded for phase-80 LEARNINGS: viewer_smoke.mjs probes #feed/.feed/#log but ctf-lineage feed is #killfeed -> feed_lines always 0 on paintbot lineage
2026-08-27T10:45:21Z heartbeat phase=60
2026-08-27T10:45:21Z progress phase=60 marker=VERIFY.md
2026-08-27T10:46:06Z 60 builder dispatched thread=sthr_01Ms1YQPp1eVAjzd68pKUi6d (check-5 fix: design-pinned repair table + interim log wording; release 0.1.3) session=c7061c35
2026-08-27T11:13:15Z 60 builder returned: check-5 fix shipped (8968e88f repair-table per design, 545afa9f terminal-only 'falling back' wording; tests extended, none weakened); ci green 33064860833; release 0.1.3 one dispatch run=33065622007 cow_id=cow_345bfc54-561e-4606-8de1-e3086f37d58a canonical=true certified secret_put=true; policies v4 uploaded (league keeps v3 submissions — fix is game-server-side); release-result.json overwritten
2026-08-27T11:13:15Z 60 builder flags logged: (a) bare-order-object without cogs wrapper takes repair path not honoured — small gap, advisory; (b) residual grep risk if max_tokens truncation hits attempt 1 (interim line echoes error.msg) — accepted, maxOutputTokens=900 makes it unlikely
2026-08-27T11:13:15Z 60 waiting for >=1 completed round on 0.1.3 image before re-verify (rounds every 15m)
2026-08-27T11:13:15Z heartbeat phase=60
2026-08-27T11:13:15Z progress phase=60 marker=33065622007
2026-08-27T11:23:15Z 60 round 6 completed on 0.1.3 (round_e71db7a4, ereq_805f41dc): coordinator pre-grep of hosted log = 0 hits (CLEAN)
2026-08-27T11:23:15Z 60 verifier re-dispatched (focused) thread=sthr_011XMQDdHmRkf8tMPhNEkhBA bound=40min session=c7061c35
2026-08-27T11:23:15Z heartbeat phase=60
2026-08-27T11:33:23Z 60 verifier re-verify returned: 8/8 TRUE (check 5 CLEAN on round 6 / 0.1.3: 0 grep hits raw+unescaped, 46/46 sidecar 200, repair lines benign; leaderboard daveey-1 1018.43 / daveey 981.57 rounds_played 5; featured match on 0.1.3 sha; viewer-check 33067338841 loaded=true clocks differ)
2026-08-27T11:33:23Z 60 minor findings logged: repair line 'kept last turn's directive on turn 0' semantics (advisory, phase-30-class); endcard never exercised by probe; feed_lines harness gap confirmed (#killfeed vs #feed selectors) — all for LEARNINGS
2026-08-27T11:33:23Z 60 judge dispatched for VERIFY.md adjudication
2026-08-27T11:33:23Z heartbeat phase=60
2026-08-27T11:33:23Z progress phase=60 marker=viewer-check-33067338841
2026-08-27T11:40:30Z 60 judge returned: verify-verdict.md blocking=0/BLOCKING=0; all 8 checks independently re-fetched and reconciled; 4 advisories non-blocking
2026-08-27T11:40:30Z 60 phase transition 60 -> 70
2026-08-27T11:40:30Z heartbeat phase=70
2026-08-27T11:41:54Z 70 announce attempted_at written (pre-POST marker), body 1791 chars
2026-08-27T11:42:19Z 70 announce msg=1542499437710934097 (200, flags=4, embeds=[])
2026-08-27T11:42:19Z 70 phase transition 70 -> 75
2026-08-27T11:42:19Z heartbeat phase=75
2026-08-27T11:42:19Z progress phase=70 marker=1542499437710934097
2026-08-27T11:43:12Z 75 atlas: slug live in /api/coworlds (episodes_7d=6); continent=paintlands (real-time combat micro, shooters/RTS row — cooperative motive but the game is a battle, not a commons); spot 202,270 clearance 39.5; label 'SMAC Micro'
2026-08-27T11:43:36Z 75 atlas dispatch=33068619866 region=paintlands at=202,270 clearance=39.5
2026-08-27T11:48:45Z 75 atlas dispatch 1 (33068619866) failed step=build: 35 unplaced leagues; fix per step 8 = extra_cities
2026-08-27T11:48:45Z 75 atlas retry 2: own dot moved 202,270 -> 184,255 clearance 23.4 (PR 20621 branch geometry: atari-cabinet took 202,270); extra_cities=35 (32 reused from open PR 20621 branch atlas/trick-taking-33040001908; placed by me: board-gauntlet tabletop 814,283 c=23.4, grf-football simulations 515,262 c=22.9, magent-battle simulations 533,247 c=22.9 — borrowed-env precedent)
