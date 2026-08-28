# 2026-08-28-derks-gym — log

2026-08-28T09:17:55Z 00 claim comment posted on idea 1217748466222687 (story 1217947584505315); 20s recheck clean
2026-08-28T09:18:30Z 00 claim 2026-08-28-derks-gym idea=1217748466222687 slug=derks-gym
2026-08-28T09:19:40Z 00 run task 1217944927934087 created in Running with 9 phase subtasks; heartbeat_at=2026-08-28T09:18:30Z session=3c1a9d54
2026-08-28T09:19:40Z 00 -> 10 phase transition: STATE.phase=10 written before designer dispatch
2026-08-28T09:24:00Z 10 designer dispatched round=1
2026-08-28T09:52:00Z 10 designer returned round=1: runs/2026-08-28-derks-gym/design.md (1100 lines)
2026-08-28T09:55:00Z 10 design accepted round=1 — checklist: [x] starter named+reason (cogame-moba, L3-13: idea names it; bit-exact-port row) [x] num_agents=6 single number, inside both variants' game_config + certification.game_config + <SEATS>=6 (L36-37,929,940,950,1038) [x] numbered resolution order: Phase A connect / Phase B draft steps 1-7 / Phase C play steps 1-10 (L174-238) [x] scoring 1.0/0.5/0.0 per seat, higher better, league ranks mean scores; draft not separately scored (L253-257) [x] end conditions closed 4-enum ancient/tick_cap/wall_clock(=deadline)/sim_fault with winners+tiebreak (L240-251) [x] per-seat observation: draft visible/hidden lists incl simultaneity hiding (L564-569); per-tick 510B opaque rows [x] reply schema caps: phase<=16, picks len 1, ids<=24, note<=120 runes rune-boundary, frame<=4096B (L579-581) [x] both policies one entrypoint env-switched PLAYER_PROMPT={derk-drafter-v1,derk-metagamer-v1} vs PLAYER_SCRIPTED={puffer-forge,lane-brawler}, prompts verbatim + baseline draft rules and micro written out (L261-367) [x] one parallel batch (asyncio.gather, shared 45s deadline) + arithmetic 60+45+600=705s<720s=60% of 1200, engine stop 645s (L369-387) [x] degrade-never-hang: player retry-once temp0 -> scripted; server neutral loadout 7-cause enum; NOOP+strike rule per tick; early settle (L188-204,222-225,326-331) [x] two name spaces: Cog-* aliases in-game, real names spectator-only, LLM body asserted name-free (L611-622) [x] viewer static wasm bundle static-replay-viewer, build_replay_viewer.sh hook, chrome verbatim, 7 readouts, 360px arithmetic 11.2px/10.4px >=10px floor (L717-873) [x] all four viewer files from cogame-moba alone with honest lineage mapping (no client/ dir; inline script = chrome_common role, kept verbatim additive-only); no MODULARIZE/EXPORT_NAME, onRuntimeInitialized kept; data-replay-loaded/data-replay-error set by shell (L725-759) [x] chrome provenance: index.html byte-for-byte + appended #derk block, no starter id reused, removed elements: none, zoom decided #viewpanel KEPT (41x23 camera over 128x128 board) with minimap+camera buttons (L761-813) [x] transport rules: --band/--hudscale on :root via relayout(), nothing in band, endcard+draft overlay inset 0 0 var(--band) dismissed by every seek, beats clickable labelled buttons CSS for all 7 kinds (L825-855) [x] replay self-sufficient: DERK v2 header carries names, aliases, config+seed, catalog, 10 draft records, loadout_digest, <=400 events, result, digests (L642-694) [x] packaging compose.yaml, coworld_manifest_template.json (variants draft/nodraft, num_agents inside game_config), game.docs readme+2 pages, game.protocols player+global (L876-967) [x] tests: fidelity inherited + zero-loadout identity, sim units, bounded-orders/legality both baselines (test 5), e2e episode->replay re-sim (test 7), strict-UTF-8 parse + negative tests (test 7), viewer_smoke.mjs executed in wasm-viewer job needs docker-smoke against smoke-replay artifact (L971-1066) [x] out of scope non-empty 11 items (L1075-1100)
2026-08-28T09:55:00Z 10 -> 20 phase transition: STATE.phase=20 written before builder dispatch
2026-08-28T09:55:00Z progress phase=10 marker=runs/2026-08-28-derks-gym/design.md
2026-08-28T09:39:03Z 20 repo created https://github.com/Metta-AI/cogame-derks-gym; propagate-secrets run 33160197297 success; SOFTMAX_TOKEN+ANTHROPIC_API_KEY present
2026-08-28T09:39:03Z 20 builder dispatched round=1
2026-08-28T11:03:33Z 20 builder returned round=1: ci.yml run 33165228867 success on main sha 2bcf052f1aec (verified); exit-criterion self-check passed
2026-08-28T11:03:33Z 20 retry: follow-up dispatched to builder — 2 manifest fixes per gotcha pins (cert players_missing raid 0.1.2->0.1.3: seat drafter+lane-brawler in certification.players; hive 2026-08-23: add ANTHROPIC_API_KEY_URI to drafter player env)
2026-08-28T11:14:25Z 20 builder returned follow-up: commit 70db5596 ci.yml run 33166095890 success on main (verified: conclusion=success headSha=70db5596b8ab90bb9207faf7e22ddb946a800375 == main HEAD); cert seats all 3 declared players; drafter env has ANTHROPIC_API_KEY_URI
2026-08-28T11:14:25Z progress phase=20 marker=ci-run-33166095890
2026-08-28T11:14:25Z 20 -> 30 phase transition: STATE.phase=30 review_round=1 written before reviewer dispatch
2026-08-28T11:14:25Z 30 reviewer dispatched round=1
2026-08-28T11:14:25Z heartbeat phase=30
2026-08-28T11:26:50Z 30 reviewer returned r1: reviews/r1-review.md 15 findings (F1-F15), reviewer-assessed 0 blocking
2026-08-28T11:26:50Z 30 fixer dispatched round=1
2026-08-28T11:59:07Z 30 fixer returned r1: reviews/r1-fixes.md — 8 fixed (F1,F2,F7,F8,F9,F10,F11,F13), 7 argued no-change (F3,F4,F5,F6,F12,F14,F15); main=624f1cb3 ci run 33167936624 success (verified)
2026-08-28T11:59:07Z 30 judge dispatched round=1
2026-08-28T11:59:07Z heartbeat phase=30
2026-08-28T12:14:13Z 30 judge returned r1: reviews/r1-verdict.md blocking=1 — [correctness] players/derk_player.py:147 checklist item 8: parse not prose-tolerant (only fence-strip); all other items pass
2026-08-28T12:14:13Z 30 round 2 begins: review_round=2 written
2026-08-28T12:14:13Z 30 reviewer dispatched round=2
2026-08-28T12:28:07Z 30 reviewer returned r2: reviews/r2-review.md 8 findings — F1 blocking (item 8 prose tolerance, = r1 verdict), F2 ws-heartbeat vs blocking LLM call (new, empirically reproduced), F3 cert drafter deadline, F4 fallback-recording semantics, F5-F8 minor
2026-08-28T12:28:07Z 30 fixer dispatched round=2
2026-08-28T12:28:07Z heartbeat phase=30
2026-08-28T12:53:40Z 30 fixer returned r2: reviews/r2-fixes.md — 7 commits 624f1cb..7c87e98, all 8 findings addressed (F1 blocking fixed via first_json_object); ci run 33172526475 success at 7c87e98d (verified)
2026-08-28T12:53:40Z 30 judge dispatched round=2
2026-08-28T12:53:40Z heartbeat phase=30
2026-08-28T13:03:11Z 30 judge returned r2: reviews/r2-verdict.md blocking=0 (first/last markers agree) — review loop complete after 2 rounds
2026-08-28T13:03:11Z 30 design.md run-dir copy synced to 6-value fallback enum (editor's note) per r2 verdict non-blocking note
2026-08-28T13:03:11Z progress phase=30 marker=r2-verdict.md
2026-08-28T13:03:11Z 30 -> 40 phase transition: STATE.phase=40 written before release dispatch
2026-08-28T13:15:59Z 40 builder returned: coworld-release.yml run 33173805205 success, version=0.1.0 canonical=true certified (replay_liveness skipped/static), cow_id=cow_81624b16-c509-470a-8fc2-69da83d64a3e, secret_put=true, 4 policies v1 (champion2 owner ply_bac48eb1); release-result.json persisted
2026-08-28T13:15:59Z progress phase=40 marker=release-run-33173805205
2026-08-28T13:15:59Z 40 -> 50 phase transition: STATE.phase=50 written before league work
2026-08-28T13:16:19Z 50 seed HTTP200 lseed_0ee18e64 league_44e55a9f-aa40-4523-9ed0-7f86ccc73d08
2026-08-28T13:16:40Z 50 division HTTP200 div_1bc6a659-31e8-40fe-a99b-726c82426998; settings HTTP200 (round_robin/filler_policy/elo/15min)
2026-08-28T13:17:05Z 50 champion1 submit run 33174702465 ok=true sub_1840690c (derk-drafter-v1:v1, daveey)
2026-08-28T13:19:30Z 50 champion2 submit run 33174752765 ok=true (derk-metagamer-v1:v1, daveey-1 verified via policy-versions)
2026-08-28T13:21:00Z 50 fillers HTTP200: derk-puffer-forge 0d434975-efba-4ffd-b071-24ab8f4fc6e0, derk-lane-brawler 4b650c45-b098-40ee-af64-58e2a16d98ac (neither champion)
2026-08-28T13:21:30Z 50 unpause HTTP200 paused=false; trigger-round HTTP200
2026-08-28T13:22:10Z 50 rounds: r1 failed (raced placement, single entrant) — r2 pending with BOTH champions in entrant_attributions; exit criterion met
2026-08-28T13:19:40Z progress phase=50 marker=league_44e55a9f-aa40-4523-9ed0-7f86ccc73d08
2026-08-28T13:19:40Z 50 -> 60 phase transition: STATE.phase=60 written
2026-08-28T13:20:08Z 60 verifier dispatched
2026-08-28T13:20:08Z heartbeat phase=60
2026-08-28T13:52:04Z 60 verifier returned attempt-1: VERIFY.md 5/8 TRUE — FALSE: 4g (champions drafted scripted: decision_ms=1, picks==puffer-forge table), 5 (player logs unobservable via artifacts API), 8 (loaded:true but scrub readouts empty — instrument probes #scrub/#clock, shell has #seek/#derk-clock)
2026-08-28T13:52:04Z 60 root cause check 4: cogolf gotcha (make-coworld.md L373) — player-side LLM policies need USE_BEDROCK:"true" in policies.json env; platform gates player-pod Bedrock sidecar on it; ANTHROPIC_API_KEY never materialises in player pods
2026-08-28T13:52:04Z 60 retry attempt-2 plan: (a) instrument fix — additive lineage selector fallbacks in templates/tools/ci/viewer_smoke.mjs (#seek/[id$="-clock"]/[id$="-scorebug"]); (b) builder fix — bedrock sidecar transport in derk_player + USE_BEDROCK in policies.json+manifest, emit missing ancient event; (c) release 0.1.1, resubmit champions v2, re-verify
2026-08-28T13:52:04Z progress phase=60 marker=VERIFY.md-attempt-1+viewer-check-33176460797
2026-08-28T13:52:04Z heartbeat phase=60
2026-08-28T15:03:40Z 60 builder returned fix round: commit 4897b52e (bedrock transport, USE_BEDROCK on champions+drafter, ancient event, 58 tests) ci 33178482769 green; release attempts 0.1.1 run 33179328591 (409 raced ci.yml upload), 0.1.2 run 33179644569 (hosted-cert churn 404, knights-archers gotcha), 0.1.3 run 33182295860 OK canonical certified cow_03c45b25-de4b-42e1-8e2f-056a496878c4, policies v4, secret_put=true; release-result.json overwritten
2026-08-28T15:03:40Z 60 decision (rails): gate ci.yml upload-coworld on UPLOAD_REQUIRED repo variable — a push-published uncertified version became canonical (0.1.1) and would silently supersede 0.1.3 on any future push; publishing belongs to coworld-release.yml
2026-08-28T15:03:40Z 60 decision (rails): re-run phase-50 seating at v4 (champions daveey/daveey-1 + fillers) — v1 policies predate the certified 0.1.3 image
2026-08-28T15:03:40Z progress phase=60 marker=release-run-33182295860
2026-08-28T15:03:40Z heartbeat phase=60
2026-08-28T15:06:20Z 50/60 reseat at v4: champion1 submit run 33183310110 ok, champion2 submit run 33183367599 ok (daveey-1 verified), fillers replaced with v4 UUIDs b697f833/36e7252a (GET confirms exactly those two), trigger-round HTTP200 — round 10 pending with both v4 champions in entrant_attributions (rounds 5-9 completed at v1 during the fix window)
2026-08-28T15:06:20Z 60 verifier dispatched attempt=2
2026-08-28T15:06:20Z heartbeat phase=60
2026-08-28T15:12:18Z 60 builder returned gate: commit cad9bd49 gates ci.yml upload-coworld on UPLOAD_REQUIRED=='true' (+AGENTS.md doc fix); ci run 33183451727 success with upload-coworld SKIPPED; registry read-back: 4 derks-gym rows, only 0.1.3 canonical, no 0.1.4 — no bump needed
2026-08-28T15:12:18Z heartbeat phase=60
2026-08-28T15:35:18Z 60 verifier returned attempt-2: VERIFY.md rewritten, 8/8 TRUE on v4-era rounds 10+11 (champion decision_ms 2903/2390, distinct notes, non-table picks; viewer-check 33184965298 loaded:true with 3 differing clock readouts); 3 non-blocking observations (seek-position-not-jump, WebGL warnings, first_blood attribution)
2026-08-28T15:35:18Z progress phase=60 marker=VERIFY.md-attempt-2-all-true+viewer-check-33184965298
2026-08-28T15:35:18Z 60 judge dispatched for VERIFY.md adjudication
2026-08-28T15:35:18Z heartbeat phase=60
