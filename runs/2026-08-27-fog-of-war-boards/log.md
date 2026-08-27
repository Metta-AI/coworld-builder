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
