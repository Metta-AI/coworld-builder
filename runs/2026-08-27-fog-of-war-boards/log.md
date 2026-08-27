# 2026-08-27-fog-of-war-boards — log

2026-08-27T00:23:20Z 00 claim comment posted on idea 1217762703112930 (story 1217887524787304)
2026-08-27T00:23:45Z 00 claim re-check after 20s: no competing claim comment — claim holds
2026-08-27T00:25:00Z 00 run task created gid=1217887556852534 section=Running + 9 phase subtasks (10..80)
2026-08-27T00:25:30Z 00 heartbeat_at custom field set on run task
2026-08-27T00:26:00Z 00 claim 2026-08-27-fog-of-war-boards idea=1217762703112930 slug=fog-of-war-boards session=325aebfd
2026-08-27T00:26:00Z 00 startability: fog-of-war-boards = 2-seat turn-based hidden-info board family (OpenSpiel kriegspiel/dark_hex/phantom_go/phantom_ttt/rbc) -> parley/babel starter row per prior OpenSpiel-port precedent; not confidential
2026-08-27T00:26:00Z 00 heartbeat check: live=2 (negotiation-games hb 00:21Z, trick-taking hb 23:38Z, both fresh) < max_parallel_runs=3; blocked=1 (coins, subtask 1217809924523748 still open) < 2 — claim allowed
2026-08-27T00:30:00Z 10 starter=cogame-babel — 2-seat turn-based hidden-info board family, game logic native, policy=LLM prompt -> first starter-table row (babel is the best current parley-stack template)
2026-08-27T00:30:00Z 10 designer dispatched: design note docs/plans/2026-08-27-fog-of-war-boards-design.md
2026-08-27T00:44:00Z 10 designer returned design.md (1278 lines): v1 = phantom-ttt-3, dark-hex-4, dark-hex-5, recon-hex-5 (monotone-knowledge invariant); kriegspiel/RBC/phantom-go out of scope with reasons
2026-08-27T00:46:00Z 10 checklist: starter[x] num_agents=2-everywhere[x] resolution-order-numbered[x] scoring-formula-sign-rank[x] end-conditions-reason={complete,deadline}[x] per-seat-observation-and-hidden-list[x] reply-schema-caps-rune-truncation[x] both-policies-env-switched-with-baseline-algos[x] simultaneous-batch-n/a-stated+720s-arithmetic[x] degrade-never-hang[x] two-name-spaces[x] viewer-static-wasm-bundle-hook-readouts-360px[x] viewer-starter-babel-all-four-files+data-replay-loaded/error[x] chrome-provenance-byte-copied-regions-6-named-edits-removals=none-zoom-dropped[x] transport-rules[x] replay-bytes-self-sufficient[x] packaging-compose-manifest-docs-protocols-both[x] tests-sim-bot-e2e-utf8-viewer-smoke-executed[x] out-of-scope-non-empty[x]
2026-08-27T00:46:00Z 10 accepted round 1 — no bounce; spot-checked babel d55d999 line claims (791, 966-967, 1179, chrome.css 443L, MODULARIZE/EXPORT_NAME) all exact
2026-08-27T00:46:00Z progress phase=10 marker=design.md written and accepted
2026-08-27T00:46:00Z 10 -> 20 phase transition
2026-08-27T00:45:00Z 20 repo created public: https://github.com/Metta-AI/cogame-fog-of-war-boards
2026-08-27T00:45:10Z 20 propagate-secrets run 33027869773 success; gh secret list shows SOFTMAX_TOKEN + ANTHROPIC_API_KEY
2026-08-27T00:47:00Z 20 builder dispatched: implement design.md, drive ci.yml to green on main
2026-08-27T00:47:00Z heartbeat phase=20
2026-08-27T01:59:32Z 20 builder returned: ci.yml green on main run=33031534557 sha=791cf71eb702cbf060812483a98d2bf6ea9b16d6 (commits 935a2a9, a15121b red-on-fixture, 791cf71 green); exit checks all pass
2026-08-27T01:59:32Z 20 note: sandbox https git-push rejected for coworld repos — builder pushed via GitHub Git Data API (blobs->tree->commit->ref) after a Contents-API bootstrap; later phases should expect the same
2026-08-27T01:59:32Z 20 builder deviations for review: (1) dwell constants raised for soak margin + test pins it (2) endcard keeps babel's ROUNDS/LEADS wording under six-edit letter (3) chrome prelude COLORS/seatColor byte-copied not exported (4) ci.yml +--soak 10 +fixture/scope steps (5) recon baselines sense-then-pick on copy (6) GameEvent.result spelled outcome in Nim, serialises as result (7) art real nano-banana
2026-08-27T01:59:32Z progress phase=20 marker=ci-run-33031534557
2026-08-27T01:59:32Z 20 -> 30 phase transition
2026-08-27T01:59:32Z heartbeat phase=30
2026-08-27T02:19:12Z 30 r1 reviewer returned: 15 findings (2 blocking legibility B1 fixture-gate-strength B2 ellipsis-padding; 13 non-blocking N1-N13; 4 could-not-determine incl sense>0 untested in CI)
2026-08-27T02:19:12Z 30 fixer dispatched on r1-review.md
2026-08-27T02:19:12Z heartbeat phase=30
2026-08-27T02:37:57Z 30 r1 fixer returned: 10 commits, green sha 0e893df12ee180b31e95a5701a88c20a73e16745 CI run 33033443296 success; B1 B2 N1 N2 N4 N5 N8a N11 N12 N13d fixed, N3 N6 N7 N8b N10 N13-rest rebutted, N9 needs-design noted
2026-08-27T02:37:57Z 30 judge dispatched (fresh context) on r1 at sha 0e893df
2026-08-27T02:37:57Z heartbeat phase=30
2026-08-27T02:48:06Z 30 r1 judge verdict: blocking 0 (B1 B2 refuted-at-head; independent 15-item pass clean; noted non-blocking: ~2.3s theoretical overshoot, say band constants, sense>0 unrendered in CI)
2026-08-27T02:48:06Z progress phase=30 marker=r1-verdict.md
2026-08-27T02:48:06Z 30 -> 40 phase transition at sha 0e893df12ee180b31e95a5701a88c20a73e16745
2026-08-27T02:48:06Z heartbeat phase=40
2026-08-27T02:56:35Z 40 release 0.1.0 first dispatch success: run 33034451372, canonical true, hosted certification certified, secret_put true, 4 policy versions (prober:v1 owned by daveey-1)
2026-08-27T02:56:35Z 40 cow_id=cow_5f8e4d33-49d7-4b19-8092-cc69d201344c manifest_sha=sha256:3af044a284b6a9e2b4b5a1d7d73c03d0cc9fc701ebc4a3dff49af9fc8e569341
2026-08-27T02:56:35Z progress phase=40 marker=release-run-33034451372
2026-08-27T02:56:35Z 40 -> 50 phase transition
2026-08-27T02:56:35Z heartbeat phase=50
2026-08-27T02:57:36Z 50 seed 200: lseed_ae7059f7-848c-425d-ad74-0daecd940a80 league_26ccabcd-af33-4f17-b9d7-f44626a7c625 (note: GET /leagues returns a bare array, matched client-side)
2026-08-27T02:57:36Z 50 division PUT 200: div_8c9c080c-31db-4672-8146-d73cd81ebc42; settings POST 200: round_robin/elo/mean, round_interval_minutes=15
2026-08-27T02:57:36Z heartbeat phase=50
2026-08-27T03:00:31Z 50 champion1 submit run 33034890250 ok sub_c3c77102-ff7c-45fe-824d-f5e530dcd990 (cartographer:v1, daveey)
2026-08-27T03:00:31Z 50 champion2 submit run 33034921745 ok (prober:v1, daveey-1, uuid 208c6f1d-5280-407f-95b6-0c235da1d1af, player_name=daveey-1 confirmed)
2026-08-27T03:00:31Z 50 fillers registered 200: probe=2a72f9fd-d46b-40dc-b48a-48f4f2362fba sweep=c403da22-b419-46d8-b613-52835baef133 (neither champion)
2026-08-27T03:00:31Z 50 unpaused 200; trigger-round 200; round 1 failed (auto-trigger during placement, pre-fillers — expected), round 2 pending with both champions in entrant_attributions
2026-08-27T03:00:31Z progress phase=50 marker=league_26ccabcd-af33-4f17-b9d7-f44626a7c625-round-2-pending
2026-08-27T03:00:31Z 50 -> 60 phase transition
2026-08-27T03:00:31Z heartbeat phase=60
2026-08-27T03:01:45Z 60 heartbeat phase=60
2026-08-27T03:08:50Z 60 heartbeat phase=60 poll: rounds completed=1 (r2); awaiting r3
2026-08-27T03:14:09Z 60 heartbeat phase=60 poll: rounds completed=1 (r2); awaiting r3 (interval 15m, r2 created 02:59Z)
2026-08-27T03:22:35Z 60 heartbeat phase=60 round 3 completed; checks 1-8 fetched, viewer-check run 33036080393 loaded=true
2026-08-27T03:26:00Z 60 check 1 TRUE: rounds 2 (completed 03:01:15Z) + 3 (completed 03:15:32Z); round 1 failed pre-fillers (1 entrant, no filler in entrant_attributions) — excluded
2026-08-27T03:26:00Z 60 check 2 TRUE: daveey 1001.47 rp=2 ew=1 cartographer:v1 | daveey-1 998.53 rp=2 ew=1 prober:v1; fillers absent
2026-08-27T03:26:00Z 60 check 3 TRUE: ereq_999e93c3-63af-4db3-becd-99b4f32e938e completed, replay_url set, participants daveey+daveey-1 is_filler=false (nested route /rounds/$R/episode-requests; flat GET 405s)
2026-08-27T03:26:00Z 60 check 4 TRUE: 4212B strict UTF-8 JSON, protocol=fogboards.replay.v1, reason=complete, 6 attempts 0 scripted 0 fellBack, results.fallbacks=[0,0]
2026-08-27T03:26:00Z 60 check 5 TRUE: round-3 hosted log CLEAN (decoded + raw). Round 2 had bedrock haiku-4-5 throttle 429 "Too many tokens per day" -> model fallback; cross-checked platform-wide against negotiation-games ereq_854455ae (same 429, same window)
2026-08-27T03:26:00Z 60 check 6 TRUE: raw-HTML grep empty (client-rendered) + /coworlds featured_match null (platform-wide); used SSR state.playlist[0] (round 3 featured) + POST /coworlds/replays/session -> static /v2/coworlds/replays/static/$COW/sha256%3A3af044a2.../index.html?replay=... ready:true
2026-08-27T03:26:00Z 60 check 7 TRUE: committed runs/.../release-result.json .certify.replay_liveness = "Replay liveness: skipped (static replay bundle declared; ...)"
2026-08-27T03:26:00Z 60 check 8 TRUE: viewer-check run 33036080393 green; loaded=true ms=2047; scrub PLY 0 -> PLY 4 -> PLY 6/FINAL (three differ); feed_lines=22; canvas_text 1067/0 outside/0 ellipsized; no failure
2026-08-27T03:26:00Z 60 VERIFY.md written: 8/8 TRUE
