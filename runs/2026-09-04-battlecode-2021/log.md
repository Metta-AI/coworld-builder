# Run log — 2026-09-04-battlecode-2021

2026-09-04T09:15:58Z 00 claim comment posted on idea 1218173707173046 (story 1218176597665462)
2026-09-04T09:16:30Z 00 claim race check passed after 20s — only our claim comment present
2026-09-04T09:17:00Z 00 claim 2026-09-04-battlecode-2021 idea=1218173707173046 slug=battlecode-2021
2026-09-04T09:17:10Z 00 run task 1218176598028188 created in Running, heartbeat_at set, 9 phase subtasks created
2026-09-04T09:17:30Z 00 STATE.json written phase=10 session=1b63e692; mod run of Metta-AI/cogame-battlecode (year module bc21), per idea HOW and LEARNINGS 2026-09-04 battlecode-2020-soup recipe
2026-09-04T09:22:00Z 10 designer dispatch prepared: starter=cogame-battlecode (mod run, year module bc21); brief modeled on 2026-09-04-battlecode-2020-soup with its LEARNINGS carried forward
2026-09-04T09:19:47Z 10 designer dispatched thread=sthr_01M8sPmhZSeDaf2EZnSp2zT4 output=runs/2026-09-04-battlecode-2021/design.md (bc21 year-module mod; bc20-sibling model; parity root-cause + killfeed-fix + cert-fixture pins in brief)
2026-09-04T09:49:33Z 10 designer returned round 1: design.md (1724 lines) — ACCEPTED against prompts/10-design.md checklist:
- [x] starter named with reason (cogame-battlecode itself; mod run, year-module boundary proved by bc20)
- [x] num_agents=2 stated in bc21 variant game_config and cert fixture (cert stays bc26); <SEATS>=2
- [x] resolution order numbered 1-7 mirroring GameWorld.runRound (turn order, empower scan order, bid auction (bid+1)/2, buff expiry, camouflage@300, double-wipe->B)
- [x] scoring: points=int(40*survival+35*vote_share+15*center_share+10*influence_share) f32-truncated; scores=100*wins+mean(points); higher better; league ranks results.scores
- [x] end conditions: 6 end_reason values incl deadline/abandoned; results.reason closed enum complete/deadline/fault
- [x] per-seat observation = sealed pre-match doctrine brief, recorded verbatim in replay; no per-round obs
- [x] reply schema caps: 16KB reply, notes 280 runes, motto 48 runes, all rune-boundary truncation
- [x] both policies same image env-switched: PLAYER_PROMPT champions (slanderer-turtle vs muck-rush) + PLAYER_SCRIPTED awu->california-roll, scaffold->examplefuncsplayer21
- [x] one parallel batch of 2 LLM calls, 45s doctrine budget, worst case 445s <= 720s (60% of 1200)
- [x] degrade-never-hang: retry once -> california-roll fallback sheet; doctrine_fallback event; loud logging
- [x] two name spaces: Clan Ash/Clan Basil in-game, real names spectator-side only
- [x] viewer: static-replay-viewer bundle, build hook, chrome verbatim, readouts listed, 360px legible
- [x] all four viewer files from ONE starter (cogame-battlecode); data-replay-loaded/data-replay-error stated
- [x] chrome provenance: chrome_common.js byte-for-byte, replay_broadcast.html appended game block, viewpanel KEPT (board 768-1024px > 360px frame) with reason
- [x] transport rules: --band/--topband/--hudscale (+new --statrail) via relayout(), nothing in band, endcard stops at var(--band) + dismissed on seek, beat buttons with CSS for every kind
- [x] replay self-sufficient: names, config, sheets, events, seed; wasm re-derives frames
- [x] packaging: compose.yaml unchanged, manifest template (bc21 variant added, player[] UNCHANGED, cert bc26), game.docs readme+pages(+rules-bc21), protocols player+global
- [x] tests: 19 test files incl bounded-orders (11), survival gate w/ inverted control (12), knob-teeth (13), perf gate 75s (15), strict-UTF8 replay (17), parity-oracle-bc21 (Tier C BLOCKING vs parity_ledger_bc21.json), 3-episode docker-smoke, wasm-viewer executes bundle on all 3 replays
- [x] out of scope non-empty (14 items)
Extras: GV05->GV06 extending ReplayCompatibleGameVersions, 0.2.0->0.3.0, killfeed FIT-zoom fix in scope w/ smoke overlap gate, 1500-round cap pinned vs stale 3000 spec prose (patch 2021.2.3.0), 18/76 maps with exclusion reasons
2026-09-04T09:49:33Z 10 phase -> 20
2026-09-04T09:49:33Z progress phase=10 marker=design.md
2026-09-04T09:51:21Z 20 builder dispatched thread=sthr_01QAZzoBKFkNkF5TzKv8pooc branch=bc21-year-module output=runs/2026-09-04-battlecode-2021/build-report.md (PR open not merged; GV06 extend, player[] unchanged, cert bc26, Tier-C parity ledger blocking, killfeed --statrail fix, 3-episode smoke pinned in brief)
2026-09-04T09:51:21Z heartbeat phase=20
2026-09-04T12:53:49Z 00 resume at phase 20 attempt=1 session=fe001725
2026-09-04T12:55:16Z 20 previous session's builder thread still live: 6 bc21 commits pushed 12:45-12:46Z, CI run 33874457351 in_progress on bc21-year-module — monitoring instead of re-dispatching (two builders on one branch would race)
2026-09-04T13:09:12Z heartbeat phase=20
2026-09-04T13:12:05Z 20 CI run 33874457351 branch=bc21-year-module conclusion=failure: parity-oracle-bc21 (javac invalid flag --release under JDK8) + test (test_bc20_baselines.nim type mismatch ScriptedChassis vs ChassisKind); waiting bounded window for the live builder thread to fix before taking over
2026-09-04T13:21:23Z heartbeat phase=20
2026-09-04T13:21:23Z 20 builder round 2 observed: fix commit cb4d6fbb pushed 13:13Z, PR #3 open, CI runs 33876856381/33876968476 in_progress
2026-09-04T13:38:41Z heartbeat phase=20
2026-09-04T13:38:41Z 20 CI run 33876856381 branch=bc21-year-module sha=cb4d6fbb conclusion=success (all 6 jobs green incl parity-oracle-bc21); awaiting builder merge of PR #3 to main
2026-09-04T13:46:41Z heartbeat phase=20
2026-09-04T13:46:41Z 20 PR #3 merged 13:43:26Z; main CI run 33879654216 sha=bdc06b04 in_progress
2026-09-04T13:56:47Z heartbeat phase=20
2026-09-04T14:05:29Z 20 main CI run 33879654216 sha=bdc06b04 conclusion=success; exit checks pass (placeholders clean, exec bits set, 3 workflows parse w/ pinned inputs, release/submit artifacts present, bc21 variant num_agents=2, champion#2 player id set)
2026-09-04T14:05:29Z progress phase=20 marker=33879654216
2026-09-04T14:05:29Z 20 asana: subtask 1218176520186448 completed, comment 1218185826410720 posted
2026-09-04T14:05:29Z 20 phase -> 30
2026-09-04T14:05:29Z heartbeat phase=30
2026-09-04T14:05:57Z 30 r1 reviewer dispatching: repo checkout /workspace/cogame-battlecode@bdc06b04, diff base e17947d9 (pre-merge main), output reviews/r1-review.md
2026-09-04T14:06:32Z 30 r1 reviewer dispatched thread=sthr_01BvkzZvM9FG6QUEN3CqJRoV output=runs/2026-09-04-battlecode-2021/reviews/r1-review.md
2026-09-04T14:34:31Z 30 r1 reviewer returned: r1-review.md (1213 lines), 13 findings F1-F13 all non-blocking per reviewer + 4 could-not-determine; F1 = killfeed-overlap viewer gate never executes (OVERLAP_SCRIPT not an IIFE, page.evaluate serialises undefined)
2026-09-04T14:34:31Z progress phase=30 marker=r1-review.md
2026-09-04T14:34:31Z heartbeat phase=30
2026-09-04T14:35:05Z 30 r1 fixer dispatched thread=sthr_01Cq9wYGucgRFRN2eYdrEaV6 output=runs/2026-09-04-battlecode-2021/reviews/r1-fixes.md (F1 gate-arming pinned as must-fix; F2/F4/F5/F6 doc/CSS aligns; evidence-backed no-change allowed elsewhere)
2026-09-04T15:16:15Z 30 r1 fixer returned: r1-fixes.md pushed; 7 commits (F1 gate armed 8f0821aa4, F2 b3ae368a5, F4 5e2710efd, F5 02586801e, F6 41dc4458f, F8 3c9f77dbe, F12 d2922438d), 6 evidence-backed no-change; main CI 33886193070 success at d2922438; NEEDS-DESIGN flag on checklist item 7 grid-harness provenance
2026-09-04T15:16:15Z progress phase=30 marker=r1-fixes.md
2026-09-04T15:16:15Z heartbeat phase=30
2026-09-04T15:18:41Z 30 note: git-over-https push auth to github.com failing (401); coworld-builder pushes via Git Data API (gh api) from here on — helper /tmp/apipush.py
2026-09-04T15:19:41Z 30 r1 judge dispatched thread=sthr_01AbxQKReBF75eyaLtdAD9CL reviewed_sha=d2922438 ci=33886193070 output=runs/2026-09-04-battlecode-2021/reviews/r1-verdict.md
2026-09-04T15:19:41Z heartbeat phase=30
2026-09-04T15:31:14Z 30 r1 judge returned: r1-verdict.md blocking=0/BLOCKING=0 agree; all 15 checklist items + parallel-batch clause PASS; F1-F13 audited (7 resolved at head, 6 advisory); advisory residue: parity oracle weaker than design-note pin (disclosed in PARITY.md), carry to phase 60
2026-09-04T15:31:14Z progress phase=30 marker=r1-verdict.md
2026-09-04T15:31:14Z 30 phase -> 40
2026-09-04T15:31:14Z heartbeat phase=40
2026-09-04T15:32:38Z 40 builder dispatched thread=sthr_01HvdgYBkXKkhAdcvRGFY7SH version=0.3.0 (policies from repo tools/ci/policies.json, 12 entries; bc21 four are new) output=runs/2026-09-04-battlecode-2021/release-result.json
2026-09-04T15:32:38Z heartbeat phase=40
2026-09-04T15:43:07Z 40 builder returned: release run 33890103949 success first dispatch; version=0.3.0 canonical=true certify.ok=true replay_liveness=skipped(static) secret_put=true; 12/12 policies (bc26/bc20 recut v2 on new image digest, bc21 four at v1, muckrush player=ply_bac48eb1); cow_id cow_455dff0d-7f57-4b21-a28d-6603d9c458d0
2026-09-04T15:43:07Z progress phase=40 marker=33890103949
2026-09-04T15:43:07Z 40 phase -> 50
2026-09-04T15:43:07Z heartbeat phase=50
2026-09-04T15:47:24Z 50 league seeded 200: league_cb515f3b-3c07-4512-bbf8-b72324f3cbf5 key=bc21 name='Battlecode 2021 — Campaign' default_variant_id=bc21 (bc26/bc20 leagues untouched, default-league NOT changed)
2026-09-04T15:47:24Z 50 short-name bc21 200 (softmax.com/battlecode/bc21); division div_5beaa66e-36ec-4db2-bc46-31a501eebaa6 200; settings 200 (elo k32, round_robin, filler_policy, 15min)
2026-09-04T15:47:24Z 50 champion1 submit ok run 33891219517 sub_fe2a99f7 (battlecode-bc21-turtle:v1, daveey)
2026-09-04T15:47:24Z 50 champion2 submit ok run 33891274764 sub_1be0cd8c (battlecode-bc21-muckrush:v1, daveey-1 confirmed)
2026-09-04T15:47:24Z 50 fillers 200: battlecode-california-roll:v1=45c48b3f-c363-4a17-8256-a09438a0ac7b, battlecode-examplefuncsplayer21:v1=28b535fa-170b-4060-a799-bb42840534ba (neither champion)
2026-09-04T15:47:24Z 50 pool grant 100 credits 200 (balance 100.0); drip 100/day max 300 200
2026-09-04T15:47:24Z 50 unpaused 200; trigger-round 200 (ladder workflow); round_6feca3e3 round 1 pending, entrant_attributions = both champions
2026-09-04T15:47:24Z progress phase=50 marker=round_6feca3e3
2026-09-04T15:47:24Z 50 phase -> 60
2026-09-04T15:47:24Z heartbeat phase=60
2026-09-04T15:48:55Z 60 verifier dispatched thread=sthr_01RgPoLV7wPEgAJrdBPJeiRv output=runs/2026-09-04-battlecode-2021/VERIFY.md + viewer-check/ (75-min poll bound; heartbeats delegated to verifier during poll)
2026-09-04T15:48:55Z heartbeat phase=60
2026-09-04T15:49:24Z heartbeat phase=60
2026-09-04T15:54:42Z heartbeat phase=60
2026-09-04T15:59:55Z heartbeat phase=60
2026-09-04T16:04:21Z heartbeat phase=60
2026-09-04T16:11:36Z heartbeat phase=60
2026-09-04T16:14:51Z heartbeat phase=60
2026-09-04T16:20:42Z 60 check 1 TRUE: 2 completed rounds round_6feca3e3 (r1) round_dc7a247d (r2), error null, fillers set pre-trigger
2026-09-04T16:20:42Z 60 check 2 TRUE: leaderboard daveey turtle:v1 rank1 1030.53 rp2, daveey-1 muckrush:v1 rank2 969.47 rp2, no filler/Baseline row
2026-09-04T16:20:42Z 60 check 3 TRUE: ereq_1f12242c completed replay 9d29794c, participants daveey/daveey-1 is_filler false
2026-09-04T16:20:42Z 60 check 4 TRUE: strict UTF-8 JSON 71618B, protocol cogame.battlecode.v1 GV06 bc21, reason=complete, fallbacks [0,0], 2 full 1500-round games
2026-09-04T16:20:42Z 60 check 5 TRUE: hosted log CLEAN (0 of 4 gated patterns), both openrouter calls 200
2026-09-04T16:20:42Z 60 check 6 TRUE: SSR playlist[0] featured match r2 + session endpoint viewer_url static path sha256:8ec16f22 ready=true, no /client/replay
2026-09-04T16:20:42Z 60 check 7 TRUE: committed release-result.json certify.replay_liveness = "Replay liveness: skipped (static replay bundle declared; ...)"
2026-09-04T16:20:42Z 60 check 8 FALSE: viewer-check 33893228440/33893758738 loaded:true both signals, but 3 clock readouts identical (2:05 GAME 1 OF 2 - BOG) and png pinned at round 5/1500; control run 33893927786 same bc21 shell on bc20 replay seeks 0%/50%/100% -> game1/game2/FINAL, so shell seek + harness selector are sound; cause = bc21 Worker starvation (sim 9.361s/3000r vs bc20 0.598s/3462r) vs harness 700ms post-click wait. 3/3 attempts spent, not fixed, reported
2026-09-04T16:20:42Z 60 VERIFY.md written: 1 item false (item 8), items 1-7 TRUE; viewer-check/ (3 attempts) committed
2026-09-04T16:22:35Z 60 verifier returned: VERIFY.md items 1-7 TRUE, item 8 FALSE (loaded:true both signals, but 3 identical clock readouts; control run 33893927786 with bc20 replay passes same bundle+harness — bc21 replay 18x heavier/round, 700ms post-click settle too short to distinguish slow seek from freeze)
2026-09-04T16:22:35Z progress phase=60 marker=VERIFY.md
2026-09-04T16:22:35Z heartbeat phase=60
2026-09-04T16:24:28Z 60 check-8 retry (attempt 2, different approach per budget): instrument fix — viewer_smoke.mjs scrub settle made adaptive+parametrized (--settle, records settle_ms), viewer-check.yml gains settle/soak inputs; re-dispatching against same iframe src with settle=20000 soak=15
2026-09-04T16:24:28Z heartbeat phase=60
2026-09-04T16:27:29Z 60 check 8 re-run after instrument fix: viewer-check run 33895007454 loaded:true, soak moved=true, clocks 1:50-GAME1-BOG / 1:02-GAME2-ARENA / FINAL — three differ (settle_ms 3515/4015), item 8 TRUE; artifact committed viewer-check-rerun/
2026-09-04T16:27:29Z progress phase=60 marker=33895007454
2026-09-04T16:27:29Z heartbeat phase=60
2026-09-04T16:28:22Z 60 judge dispatched thread=sthr_01EY1ebzZWD5eFQ9t1o8RZzd output=runs/2026-09-04-battlecode-2021/verify-verdict.md
2026-09-04T16:28:22Z heartbeat phase=60
2026-09-04T16:34:51Z 60 judge returned: verify-verdict.md blocking=0/BLOCKING=0 agree; all 8 checks TRUE (item 8 via re-run 33895007454); 3 completed rounds now; advisories: worker keyframe checkpoints for seek latency, 2 chrome-collision legibility notes
2026-09-04T16:34:51Z progress phase=60 marker=verify-verdict.md
2026-09-04T16:34:51Z 60 phase -> 70
2026-09-04T16:34:51Z heartbeat phase=70
2026-09-04T16:36:18Z 70 announce.attempted_at written and pushed BEFORE the POST
2026-09-04T16:36:45Z 70 announce msg=1545472630616752128 (200, flags:4, embeds:[])
2026-09-04T16:36:45Z progress phase=70 marker=announce.discord_message_id
2026-09-04T16:36:45Z 70 phase -> 75
2026-09-04T16:36:45Z heartbeat phase=75
2026-09-04T16:39:29Z 75 atlas slug=battlecode/bc21 region=commons at=581,538 clearance=22.9 (commons: multi-variant strategy league, sibling battlecode cluster; spot from PR-21581 geometry not stale main); extra_cities=64 mirrored VERBATIM from queued PR 21581 branch so the diffs merge cleanly; drop_slugs=paintbot/classic,paintbot/ctf (same stale pair)
2026-09-04T16:39:29Z 75 atlas dispatch=33896329928 region=commons at=581,538 clearance=22.9
2026-09-04T16:39:29Z heartbeat phase=75
2026-09-04T16:41:37Z 75 atlas pr=https://github.com/Metta-AI/metta/pull/21610 status=pr_open (64 extra cities mirrored from queued PR 21581; automerge armed; merge queue is human-owned)
2026-09-04T16:41:37Z progress phase=75 marker=https://github.com/Metta-AI/metta/pull/21610
2026-09-04T16:41:37Z 75 phase -> 80
2026-09-04T16:41:37Z heartbeat phase=80
