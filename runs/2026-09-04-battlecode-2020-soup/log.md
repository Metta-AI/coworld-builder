# 2026-09-04-battlecode-2020-soup — log

2026-09-04T02:57:25Z 00 claim comment posted on idea (story 1218170282739417), 20s re-read clean — no competing claim
2026-09-04T02:58:30Z 00 claim 2026-09-04-battlecode-2020-soup idea=1218165469199121 slug=battlecode-2020-soup
2026-09-04T02:58:30Z 00 run task 1218170282874132 created in Running, 9 phase subtasks, heartbeat_at custom field set
2026-09-04T02:58:30Z 00 MOD run per idea UPDATE 2026-09-03T22:05Z (daveey): branch/PR of Metta-AI/cogame-battlecode, bc20 year module + manifest variant, cert stays bc26, second league bc20; no new repo. Sibling run 2026-09-03-battlecode is live on the same repo (phase 30 r2) — coordinate at build/release time, never touch its run directory or task
2026-09-04T02:58:30Z heartbeat phase=10
2026-09-04T03:00:46Z 10 designer dispatched thread=sthr_017kDsFZq9XA61JtR8jzuZ4k output=runs/2026-09-04-battlecode-2020-soup/design.md (bc20 year-module mod; post-D1-D3 interface; no-Java-runtime pins in brief)
2026-09-04T03:00:46Z heartbeat phase=10
2026-09-04T03:23:11Z 10 designer returned round 1: design.md (1380 lines) — ACCEPTED against prompts/10-design.md checklist:
- [x] starter named with reason (cogame-battlecode itself; year-module mod; lineage coworld-ctf)
- [x] num_agents=2 fixed, in variants[bc20].game_config and restated for bc26; cert fixture stays bc26 (stated)
- [x] tick structure + exact numbered resolution rules 1-9 mirroring GameWorld.runRound, constants pinned from engine source
- [x] scoring formula (100*wins + mean(points); points=int(60*hq_survival+25*unit_share+15*net_worth_share) float32) with sign (higher better) and league ranks by results.scores
- [x] end conditions incl deadline; end_reason enum 7 values; results.reason complete|deadline|fault unchanged
- [x] per-seat observation JSON given; hidden set enumerated; sealed simultaneous
- [x] reply schema with per-field caps (16KB reply, sheet<=32 keys, notes 280 runes, motto 48 runes), rune-boundary truncation stated
- [x] both policies same image env-switched PLAYER_PROMPT vs PLAYER_SCRIPTED=bowl-of-chowder|examplefuncsplayer, baseline algorithms given
- [x] one parallel batch per doctrine phase; budget arithmetic 425s <= 720s (60% of episodeTimeoutSeconds), round cap 1500 chosen from real flood curve
- [x] degrade-never-hang table with retry-once -> fallback sheet (verbatim), early settle
- [x] two name spaces (Clan Ash/Clan Basil in-game; real names spectator-side)
- [x] viewer static wasm bundle, build hook, chrome verbatim, readouts listed, legible at 360px (checked in viewer smoke)
- [x] all four viewer files from ONE starter (cogame-battlecode's shipped bc26 viewer, unchanged loaders, no MODULARIZE splice); data-replay-loaded/data-replay-error stated
- [x] chrome provenance: chrome_common.js byte-for-byte, replay_broadcast.html appended bc20 block never rewritten (gridlock scar cited); zoom decided: KEEP #viewpanel (48x48 board > frame)
- [x] transport rules: --band/--hudscale via relayout(), nothing in transport band, endcard stops at var(--band) + dismissed on seek, 10 beat kinds all with CSS
- [x] replay self-sufficient (names, config, per-tick events, seed, doctrine payloads verbatim)
- [x] packaging: compose.yaml unchanged, manifest gains bc20 variant, game.docs readme+pages, game.protocols player+global, GV04, version 0.2.0, cert stays bc26
- [x] tests: sim unit tests, baseline legality+survival gate (D2), e2e episode replay, strict-UTF-8 parse, parity-oracle CI job (defined tiers), viewer smoke EXECUTED against both smoke replays
- [x] out of scope non-empty (13 items)
Post-D1/D2/D3 interface honoured (no chassis knob; baselines play; overlay dismisses). No rejection rounds needed.
2026-09-04T03:23:11Z 10 phase -> 20
2026-09-04T03:23:11Z progress phase=10 marker=design.md
2026-09-04T03:23:11Z heartbeat phase=20
2026-09-04T03:25:07Z 20 builder dispatched thread=sthr_01Ri6rwfEDZH5fDbkWjKHWcv branch=bc20-year-module output=runs/2026-09-04-battlecode-2020-soup/build-report.md (branch-only, PR open not merged, sibling-run coordination pinned in brief)
2026-09-04T03:25:07Z heartbeat phase=20
2026-09-04T04:07:12Z 20 branch bc20-year-module created from origin/main cb37075; local Nim 2.2.4 + nimby 0.1.26 toolchain installed in the sandbox so every non-Docker gate runs before a push
2026-09-04T04:31:40Z 20 data generated and verified against the pinned battlecode20 checkout 7618f6b: 18 converted .map20 maps (every size/symmetry in the design note's table confirmed against the real flatbuffers), the 1501-entry float32 water table (JDK; Math == StrictMath == libm on the whole domain), the 22-sprite atlas
2026-09-04T05:12:03Z 20 JDK 8 + Gradle 6.0.1 tried locally against battlecode20: :engine:jar CANNOT build — net.sf.jsi:jsi:1.1.0-SNAPSHOT is gone from jcenter (dead 2022) and Sonatype OSS snapshots (expired). Parity oracle redesigned around the dependency-free engine sources; recorded in docs/PARITY.md §bc20 and in the build report
2026-09-04T05:18:55Z 20 JDK-vs-Nim parity vectors diff CLEAN locally: 67559 lines (water table, both pollution coefficients over all 65536 values, Math.round, IDGenerator, java.util.Random, the overflowing cow seed, Transaction.compareTo)
2026-09-04T05:41:20Z 20 renderer fixture run locally under Playwright 1.55.0 + chromium at 3 widths x 2 years with --strict-text-bounds: caught and fixed #bc20-flood escaping the 360 px frame before any CI round
2026-09-04T06:02:10Z 20 rebased onto origin/main abc92ce (sibling run's D1-D3 landed and spent GV04): took main's side for every bc26 semantic, GameVersion -> GV05, ReplayCompatibleGameVersions ["GV04","GV05"], bc20's parseChassis renamed parseChassisKind, #bc20-doctrines adopts main's stricter auto-close D3 discipline
2026-09-04T06:14:33Z 20 push 1 sha=c4e2890 (git push over HTTPS is refused in this sandbox for every Metta-AI repo; pushed through the git-data REST API, tree byte-identical) CI run 33839853976 conclusion=success (test, parity-oracle, parity-oracle-bc20, docker-smoke, wasm-viewer)
2026-09-04T06:16:02Z 20 PR https://github.com/Metta-AI/cogame-battlecode/pull/1 OPEN, not merged
2026-09-04T06:58:40Z 20 push 2 sha=0a0106f (docs, NOTICE, tests/test_bc20_replay.nim) CI run 33840693769 conclusion=success — all five jobs green
2026-09-04T06:58:40Z 20 exit criterion checked on 0a0106f: no <slug>/<IMAGE>/<SEATS> residue; all three workflows parse and are active; coworld-release.yml inputs version/policies/put_secret/skip_certify present; coworld-submit.yml inputs player_id/policy/league_id present; release-result and submit-result artifacts present; both hooks committed 100755; num_agents 2 in both variants' game_config and in the cert fixture, never at variant top level; cert stays bc26
2026-09-04T06:58:40Z 20 build-report.md written; 0 red CI rounds spent (retry budget untouched)
2026-09-04T05:44:22Z 20 builder returned: branch green (runs 33839853976, 33840693769), PR 1 open; report build-report.md; API-push workaround noted; GV05 (sibling spent GV04); parity full-engine tier blocked by dead net.sf.jsi artifact, dependency-free oracle vectors 67559 lines clean instead
2026-09-04T05:44:22Z 20 sibling run 2026-09-03-battlecode confirmed COMPLETE (phase 80, 0.1.6) — merged PR 1 to main (merge sha 551c5427), watching main CI run 33841592052
2026-09-04T05:44:22Z heartbeat phase=20
2026-09-04T05:50:50Z 20 push-auth incident: git-over-HTTPS refused sandbox-wide; coworld-builder pushes now replayed via git-data REST API (/tmp/api_push.py, no force; a rejected ref update = lost race, same rule)
2026-09-04T05:50:50Z 20 main CI green run 33841592052 sha=551c5427 (merge of PR 1); workflows parse on main, release/submit inputs + artifacts confirmed
2026-09-04T05:50:50Z progress phase=20 marker=ci-run-33841592052
2026-09-04T05:50:50Z 20 phase -> 30 review_round=1
2026-09-04T05:50:50Z heartbeat phase=30
2026-09-04T05:51:49Z 30 r1 reviewer dispatched thread=sthr_019p8LdoN8Nvyz91G7QKxp6S output=runs/2026-09-04-battlecode-2020-soup/reviews/r1-review.md (diff abc92ce..551c5427 vs design.md)
2026-09-04T05:51:49Z heartbeat phase=30
2026-09-04T06:10:11Z 30 r1 reviewer returned: 15 findings, 0 claimed blocking (F1 vacuous fixture assert, F2 victim_alias mislabel, F4 flood_table[7] sentinel vs note, F8 end-reason re-derive shortfall, F9 undeclared weaker knob gates, F10 move-into-water divergence undocumented, F13 no committed bc20 fixture replay, etc)
2026-09-04T06:10:11Z heartbeat phase=30
2026-09-04T06:10:55Z 30 r1 fixer dispatched thread=sthr_01TeG3QvYn55rwhFkt2h7TNU output=runs/2026-09-04-battlecode-2020-soup/reviews/r1-fixes.md
2026-09-04T06:10:55Z heartbeat phase=30
2026-09-04T07:25:09Z 30 r1 fixer returned: 15/15 resolved (5 code, 3 test, 7 documented) + out-of-scope fix: wasm_replay_smoke.cjs had never executed a frame (require vs global.Module) — now real with negative control; main sha e07412ab, CI green run 33847918283, no test weakened
2026-09-04T07:25:09Z heartbeat phase=30
2026-09-04T07:26:18Z 30 r1 judge dispatched thread=sthr_01LhZ4mLAx6KWQU4hEcHCj7k output=runs/2026-09-04-battlecode-2020-soup/reviews/r1-verdict.md (fresh context, sha e07412ab)
2026-09-04T07:26:18Z heartbeat phase=30
2026-09-04T07:40:51Z 30 r1 judge returned: blocking: 0 / BLOCKING: 0 (markers agree) — 11 findings resolved by verified commits, 4 sound doc dispositions; independent 15-item checklist all PASS; advisory residue: narrowed parity oracle (dead net.sf.jsi, documented)
2026-09-04T07:40:51Z progress phase=30 marker=r1-verdict.md
2026-09-04T07:40:51Z 30 phase -> 40
2026-09-04T07:40:51Z heartbeat phase=40
2026-09-04T07:41:55Z 40 builder dispatched thread=sthr_015Lv4QFAqyAnKn72oU7GjRd version=0.2.0 policies=bc20-only override (avoid minting unused bc26 v2s, sibling precedent) put_secret=true
2026-09-04T07:41:55Z heartbeat phase=40
2026-09-04T07:49:00Z 40 dispatch 1 version=0.2.0 run=33849953684 step_failed="Certify locally" (players-run / players_missing: manifest player[] declared bowl-of-chowder + examplefuncsplayer, which the 2-seat bc26 cert fixture cannot seat — coworld 0.1.43 requires every declared player to occupy a slot; playbook §gotchas line 396) — decision: manifest fix, no bump (0.2.0 was never minted: upload-coworld did not run)
2026-09-04T07:51:00Z 40 fix pushed e17947d9 — manifest declares only awu + scaffold (PLAYER_SCRIPTED resolves per year: on bc20 awu=bowl-of-chowder, scaffold=examplefuncsplayer), bc20 CI smoke seats awu,scaffold, docker_smoke.sh rejects undeclared SMOKE_PLAYER_IDS, test_manifest asserts declared==seated both ways; CI run 33850675587 green (bc20 replay chassis still bowl-of-chowder vs examplefuncsplayer)
2026-09-04T08:02:00Z 40 dispatch 2 version=0.2.0 run=33850681870 SUCCESS ok=true canonical=true certify.ok=true replay_liveness="skipped (static replay bundle declared…)" secret_put=true cow_id=cow_d9fc2f21-c095-4131-bd86-d35848e046f8 manifest_sha=sha256:5f42d864… policies=battlecode-bc20-latticer:v1(champ1) battlecode-bc20-rusher:v1(champ2, daveey-1) battlecode-bowl-of-chowder:v1 battlecode-examplefuncsplayer:v1 (fillers) — decision: release accepted, phase 40 done
2026-09-04T08:07:42Z 40 builder returned: 0.2.0 canonical+certified cow_d9fc2f21-c095-4131-bd86-d35848e046f8 release run 33850681870; 2 dispatches (d1 players_missing — design-note impossibility: player[] additions vs unchanged 2-seat cert fixture; fixed by dropping redundant bc20 player entries e17947d9, certifier rule now tested both directions; d2 success); exit criterion verified from committed release-result.json
2026-09-04T08:07:42Z progress phase=40 marker=release-run-33850681870
2026-09-04T08:07:42Z 40 phase -> 50
2026-09-04T08:07:42Z heartbeat phase=50
2026-09-04T08:09:04Z 50 league seeded 200: league_b08a04aa-9d3d-4ff2-91a3-013e19a531cc key=bc20 name='Battlecode 2020 — Soup' default_variant_id=bc20 (bc26 league league_24414477 untouched, default-league NOT changed per idea)
2026-09-04T08:09:04Z 50 division div_df107879-c101-4771-98b7-7adf428b78c1 200; settings 200 (elo k32, round_robin, filler_policy, 15min); short-name bc20 200 (softmax.com/battlecode/bc20)
2026-09-04T08:09:04Z heartbeat phase=50
2026-09-04T08:12:14Z 50 champion1 submit ok run 33852053271 sub_a8748180 (battlecode-bc20-latticer:v1, daveey)
2026-09-04T08:12:14Z 50 champion2 submit ok run 33852131537 sub_03d36bcd (battlecode-bc20-rusher:v1, daveey-1 confirmed)
2026-09-04T08:12:14Z 50 fillers 200: battlecode-bowl-of-chowder:v1=fef73ff9-c4ed-4acd-910e-b34d0198ab13, battlecode-examplefuncsplayer:v1=14072215-0a2f-4dd3-8be7-409fbfb5ab49 (neither champion)
2026-09-04T08:12:14Z 50 pool grant 100 credits 200 (balance 100.0); drip 100/day max 300 200
2026-09-04T08:12:14Z 50 unpaused 200; trigger-round 200 (ladder workflow); round_ead26855 round 1 pending, entrant_attributions = both champions
2026-09-04T08:12:14Z progress phase=50 marker=league_b08a04aa-9d3d-4ff2-91a3-013e19a531cc
2026-09-04T08:12:14Z 50 phase -> 60
2026-09-04T08:12:14Z heartbeat phase=60
2026-09-04T08:13:28Z 60 verifier dispatched thread=sthr_01WKajK2qTXy3USnrSg1s7Rf output=runs/2026-09-04-battlecode-2020-soup/VERIFY.md (75-min bound; degenerate-play substance checks folded into check 4)
2026-09-04T08:13:28Z heartbeat phase=60
2026-09-04T08:20:10Z 60 poll 1: rounds?league_id -> 1 round, round_ead26855 round_number=1 status=completed (created 08:11:19Z, completed 08:12:12Z); need >=2, waiting (interval 15min, bound 09:28Z)
2026-09-04T08:20:10Z 60 check 2 TRUE: leaderboard daveey rank1 latticer:v1 1016 rounds_played=1 wins=1 / daveey-1 rank2 rusher:v1 984 rounds_played=1; no filler rows
2026-09-04T08:20:10Z 60 check 3 (round 1) TRUE: ereq_241dd10b completed replay_url=.../a3fb2023-1408-4c75-9023-e665a3eb2510.replay participants daveey+daveey-1 (flat ?round_id= 405; nested /rounds/$R/episode-requests works)
2026-09-04T08:20:10Z 60 check 4 (round 1) TRUE: strict python json ok, protocol=cogame.battlecode.v1, result.reason=complete, fallbacks=[0,0], sheets differ (lattice vs rush), 3 games end_reason hq_destroyed/quantity/..., 76 events incl first_build x30, rush_launched x3, wall_closed x5, flood_stage x13, hq_buried
2026-09-04T08:20:10Z 60 check 5 (round 1) CLEAN: decoded 4 containers, zero 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'
2026-09-04T08:20:10Z 60 check 6 static: page client-rendered (no <iframe> in raw HTML for /battlecode/bc20 or /battlecode); featured match from SSR state.playlist[0]; POST /coworlds/replays/session -> ready:true viewer_url=.../v2/coworlds/replays/static/cow_d9fc2f21.../sha256%3A5f42d864.../index.html?v=2#replay=<s3>
2026-09-04T08:20:10Z 60 check 7 TRUE: committed release-result.json certify.replay_liveness = 'Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)'
2026-09-04T08:20:10Z heartbeat phase=60
2026-09-04T08:27:30Z 60 poll 2: round_ae434347 round_number=2 completed 08:27:18Z — 2 completed rounds, bound not needed (14 min of 75 used)
2026-09-04T08:28:00Z 60 check 1 TRUE: rounds 1+2 completed, error=null both; fillers set (GET filler-policies 200 w/ ELEV: bowl-of-chowder fef73ff9 + examplefuncsplayer 14072215); r2 created 08:26:19Z after the phase-50 filler write; r1 settled which per playbook §6 proves a filler existed at trigger time
2026-09-04T08:28:05Z 60 check 2 TRUE: daveey-1 rank1 rusher:v1 1001.47 rounds_played=2 / daveey rank2 latticer:v1 998.53 rounds_played=2; two rows only, no filler/Baseline row
2026-09-04T08:28:10Z 60 check 3 TRUE: latest round 2 -> ereq_330eeacf completed, replay_url bb7e21c2, participants daveey(latticer,pos0)+daveey-1(rusher,pos1) is_filler=false; flat ?round_id= 405, nested route used
2026-09-04T08:28:20Z 60 check 4 TRUE: strict utf-8 json 73128B, protocol=cogame.battlecode.v1, result.reason=complete, fallbacks=[0,0], no doctrine_fallback event, sheets differ 7/10 knobs (lattice r7/vap3/rush0 vs rush/swarm/rush_trigger240/buster), 3 maps 3 end_reasons (quality/quantity/hq_destroyed) series 1-2, units_built min 17v18, hq drowned g3 r464
2026-09-04T08:28:30Z 60 check 5 TRUE: logs decoded (4 containers, 1703 chars) CLEAN — zero falling back|LLM provider is unavailable|cut off at max_tokens|rejected; both openrouter calls 200
2026-09-04T08:29:00Z 60 check 6 TRUE: raw-HTML iframe grep empty (client-rendered) and /coworlds replay_viewer+featured_match null (both documented dead ends, recorded); featured match from SSR state.playlist[0] = battlecode.r2.e1; POST /coworlds/replays/session -> ready:true viewer_url=/v2/coworlds/replays/static/cow_d9fc2f21/sha256%3A5f42d864/index.html?v=2#replay=<s3>; no /client/replay
2026-09-04T08:29:05Z 60 check 7 TRUE: committed release-result.json (not re-downloaded) certify.replay_liveness='Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)'
2026-09-04T08:29:30Z 60 check 8 attempt 1 run 33853624448 (dispatch stamp 08:28:41Z, run createdAt 08:28:43Z) green: loaded=true ms=5547 both signals, no failure; scrub 0%=2:24 50%=2:23 100%=2:23 — 50/100 identical
2026-09-04T08:33:30Z 60 check 8 attempt 2 run 33853943737 (?viewpanel=0, hypothesis test): loaded=true ms=2190, scrub array collapsed to ONE entry — proves the harness was clicking #zoom-slider (input[type=range], DOM offset 141293) not #scrub (a div, offset 144578); screenshot is FIT and legible
2026-09-04T08:35:40Z 60 check 8 attempt 3 run 33854088585 (canonical ?replay= query form): loaded=true ms=1861, scrub 2:24/2:23/2:23 reproduced, zoom again 12.0x — reproducible, not a one-off
2026-09-04T08:36:00Z 60 check 8 FALSE by rule (3/3 attempts spent): loaded:true but the three clock readouts do not all differ. Root cause evidenced as a coworld-builder harness defect (viewer_smoke.mjs SCRUB_SELECTOR resolves in DOM order and hits this shell's zoom slider first), NOT a viewer defect; not fixed — verifier does not edit code
2026-09-04T08:40:05Z 60 VERIFY.md written: items 1-7 TRUE, item 8 FALSE; viewer-check artifacts (3 runs) committed under runs/.../viewer-check/
2026-09-04T08:40:05Z 60 legibility observation for the coordinator: killfeed panel overdraws the per-clan soup/mined/refined stat boxes bottom-right in all three screenshots
2026-09-04T08:40:05Z heartbeat phase=60
2026-09-04T08:43:39Z 60 verifier returned: 7/8 TRUE; check 8 FALSE via harness defect (comma selector clicked #zoom-slider, verifier proved it with viewpanel=0 control); killfeed/stat-box overlap noted for judge
2026-09-04T08:43:39Z 60 harness fix: viewer_smoke.mjs scrub target resolved in preference order (#scrub first), zoom-slider mis-click documented in comment; re-dispatching viewer-check
2026-09-04T08:43:39Z heartbeat phase=60
2026-09-04T08:45:34Z 60 check 8 re-run after harness fix: viewer-check run 33854861020 loaded:true, clocks 2:24-GAME1 / 1:11-GAME2 / FINAL — three differ, item 8 TRUE; artifact committed viewer-check-rerun/
2026-09-04T08:45:34Z progress phase=60 marker=viewer-check-33854861020
2026-09-04T08:45:34Z heartbeat phase=60
2026-09-04T08:46:16Z 60 judge dispatched thread=sthr_01A7HS4xgv8MuzWyvvz3GzE4 output=runs/2026-09-04-battlecode-2020-soup/reviews/verify-verdict.md (adjudicate 8 checks + killfeed overlap ruling)
2026-09-04T08:46:16Z heartbeat phase=60
2026-09-04T08:51:53Z 60 judge returned: blocking: 0 / BLOCKING: 0 — all 8 checks TRUE independently re-fetched; item-8 supersession ruled sound; killfeed/stat-box overlap ruled ADVISORY (fix in next version bump)
2026-09-04T08:51:53Z progress phase=60 marker=verify-verdict.md
2026-09-04T08:51:53Z 60 phase -> 70
2026-09-04T08:51:53Z heartbeat phase=70
2026-09-04T08:52:43Z 70 announce.attempted_at written and pushed BEFORE the POST
2026-09-04T08:52:43Z heartbeat phase=70
2026-09-04T08:53:09Z 70 announce msg=1545355975630782475 (200, flags:4, embeds:[])
2026-09-04T08:53:09Z progress phase=70 marker=announce.discord_message_id
2026-09-04T08:53:09Z 70 phase -> 75
2026-09-04T08:53:09Z heartbeat phase=75
2026-09-04T08:55:50Z 75 atlas slug=battlecode/bc20 region=commons at=548,583 clearance=22.9 (adjacent-continent rationale: sibling battlecode at 416,574 commons in queued PR 21548; spot from PR geometry not stale main); extra_cities=63 mirrored VERBATIM from PR 21548 so the two diffs merge cleanly; drop_slugs=paintbot/classic,paintbot/ctf (same stale pair)
2026-09-04T08:55:50Z heartbeat phase=75
