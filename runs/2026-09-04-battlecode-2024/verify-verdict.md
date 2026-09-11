blocking: 0

# Phase-60 verdict — battlecode-2024 (bc24)
Head: 4bcb8db6 (release sha 4bcb8db628a731a446980270159b540ffb380c09, v0.11.0, cow_b9c9aab2-42ac-4606-b1e6-442841de04de)
Checklist: prompts/60-verify.md (eight checks) against docs/SPEC.md §Definition of done
Independent read of the rendered evidence (viewer-smoke.png, viewer-smoke.json, release-result.json, replay bytes, design.md pins) written before ruling on VERIFY.md's claims: yes
Judge re-fetched every platform read independently (2026-09-11, SOFTMAX_TOKEN + gh): rounds, leaderboard, episode request, replay S3 bytes, hosted logs, bc24 page HTML, replays/session POST, CI run conclusion.

## Check 1 — ≥2 completed rounds after fillers set: TRUE (re-fetched)
Re-fetched `GET /rounds?league_id=league_8f4f934c…&limit=20`: exactly 2 entries, `round_741956f9` (round_number 2, completed 02:15:17Z, error null) and `round_958dff29` (round_number 1, completed 02:08:17Z, error null). Matches VERIFY.md byte-for-byte. log.md line 97 records the filler-policies POST at 02:07:00Z and line 99 the round-1 trigger at 02:07:17Z — fillers were registered before any round existed, so both rounds are after. No failed/discarded rounds exist in the league at all.

## Check 2 — both champions ranked, and both are LLM prompt policies: TRUE (re-fetched)
Re-fetched `GET /divisions/div_8e76c71d…/leaderboard`: rank 1 `daveey` / `battlecode-bc24-fortress:v7` (score 1030.53, rounds_played 2, win_rate 1.0); rank 2 `daveey-1` / `battlecode-bc24-flagrush:v7` (score 969.47, rounds_played 2). Only two rows — fillers absent, which SPEC accepts as the alternative to a Baseline label. Both `rounds_played ≥ 1`.
LLM-not-scripted verified from three independent sources, not the verifier's word: (a) replay `result.policy_kind == ["llm","llm"]` and `seats[].policy == "llm"` for both; (b) the hosted game log (re-fetched, decoded): `seat 0 registered kind=llm label=fortress` / `seat 1 registered kind=llm label=flagrush`, plus two `HTTP/1.1 200 OK` LLM provider calls in the bedrock-sidecar container; (c) design.md manifest (lines 1405–1415): fortress and flagrush carry `PLAYER_PROMPT`, only the fillers gone-sharkin/examplefuncsplayer24 carry `PLAYER_SCRIPTED`. No scripted policy is seated as a champion.

## Check 3 — latest round's episode request completed with a replay: TRUE (re-fetched)
Re-fetched `GET /episode-requests/ereq_eed98756…`: `status: "completed"`, `replay_url: https://softmax-public.s3.amazonaws.com/replays/29d4150a-12f4-483a-b347-65b88a76897b.replay`, participants position 0 = battlecode-bc24-fortress v7 / daveey (is_filler false), position 1 = battlecode-bc24-flagrush v7 / daveey-1 (is_filler false), scores 273.0 / 26.0. It belongs to round_741956f9 (the latest completed round). Identical to VERIFY.md.

## Check 4 — replay bytes valid and show the game: TRUE (re-fetched from S3)
Re-fetched the replay (99,632 bytes): strict `jq -e` parse ok; `protocol == "cogame.battlecode.v1"`, `format == "cogame-battlecode-replay"` — both match design.md (lines 925, 1055); `result.reason == "complete"`.
The verifier's "small decision count is by design" claim tested and upheld: design.md line 415 specifies the doctrine phase as ONE parallel batch of 2 LLM calls per match, so 2 `doctrine_requested` + 2 `doctrine_received` is the full expected decision surface. The real test the brief names passes at the source: `result.fallbacks == [0,0]`, `sheet_defaults_applied == [[],[]]`, and the event stream contains zero `doctrine_retry`/`doctrine_fallback` events (design line 710 requires a fallback to set all three signals — none fired). Both doctrine sheets are present in the replay (`seats[].sheet`/`sheet_submitted`/`notes`/`motto`) and are substantive and mutually distinct: seat 0 (fortress) build-split, flag_rush_round 850, trap_budget 55, explosive flag-ring traps, moat, retreat_hp 700; seat 1 (flagrush) attack-split, flag_rush_round 280, trap_budget 8, stun choke traps, fill_paths, retreat_hp 200. These are model-authored strategies, not the fallback sheet.
End reasons: game 1 (Randy, rounds_played 2000) `more_flag_captures` = the design's round-2000 tiebreak (design line 502 — "round 2000 reached; more flags captured", a named DominationFactor, not a timeout); game 2 (DefaultLarge, rounds_played 1958) `capture` = all three flags taken before the limit. Both are on design.md's legitimate-endings list (§End conditions); neither is `deadline`/`abandoned`. Event histogram re-computed and matches VERIFY.md exactly (6 flag_captured, 39 flag_taken, 42 flag_dropped, 34 flag_returned, 38 trap_wave, 18 mastery, 12 upgrade, 1 rout…) — real CTF gameplay, not a stub. Best-of-three settled 2–0, so 2 games not 3 is correct.

## Check 5 — hosted game log clean: TRUE (re-fetched, decoded, re-grepped)
Re-fetched `GET /episode-requests/ereq_eed98756…/artifacts/logs` with the elevated header, decoded all four `===== container =====` blocks via `ast.literal_eval` (same method VERIFY.md documents), and re-ran the four-term grep across the decoded text: zero hits → CLEAN. bedrock-sidecar shows exactly two provider POSTs, both `HTTP/1.1 200 OK`; game container shows `settled: complete`, `reason=complete games=2 scores=[273.0, 26.0]`. Matches VERIFY.md.

## Check 6 — public page uses the static replay path: TRUE (re-fetched; substitution is the documented method)
The verifier's substitution is valid, and it is not an improvisation: playbooks/observatory-api.md §Featured match / replay route (lines 312–340) records that the page is client-rendered (raw-HTML iframe grep finds nothing platform-wide), that the featured match is server-rendered into the SSR payload at `state.playlist[0]`, and that the iframe `src` comes from the exact call the page's JS makes — `POST /coworlds/replays/session`. prompts/60-verify.md itself licenses the fallback for an empty grep.
My re-fetch of `https://softmax.com/battlecode/bc24` (1,076,374 bytes): no `<iframe>` in raw HTML, **zero** occurrences of `/client/replay` anywhere in the page, and the SSR payload carries `leagueId: league_8f4f934c…` with `playlist[0]` naming this cow_id, version 0.11.0, round 2 / episode 1, and a `replayUrl` byte-identical to check 3's — a featured match is present and it is the verified episode. My own `POST /coworlds/replays/session` returned `ready: true` and `viewer_url = …/v2/coworlds/replays/static/cow_b9c9aab2…/sha256%3Aa8f75cf3…c471d/index.html?v=2#replay=<s3 url>` — the static route (the `#replay=` fragment form is documented as equivalent to `?replay=` since 2026-08-28), sha equal to `STATE.coworld.manifest_sha`, and not a `/client/replay` pod URL. The verifier also correctly resolved the page-address hazard: bare `/battlecode` is the bc26 first-league page; `/battlecode/bc24` is this league's, and its SSR payload proves it.

## Check 7 — certification declared the static bundle: TRUE (read from the committed artifact)
Read `runs/2026-09-04-battlecode-2024/release-result.json` (the committed phase-40 artifact, present on disk): `.certify.replay_liveness == "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"` — contains the required substring. Also `.certify.ok == true`, `.canonical == true`, cow_id and manifest_sha match STATE and checks 6/8.

## Check 8 — viewer executed, spectator judgment: TRUE (evidence examined directly; CI conclusion re-fetched)
- CI: `gh run view 34554357054` → workflow `viewer-check`, created 2026-09-11T02:22:20Z, `conclusion: success` — matches VERIFY.md's dispatch narrative.
- (a) `loaded: true`: viewer-smoke.json has `loaded: true`, `ms: 2823`, `signals.data_replay_loaded: "true"`, `bridge: ["ready"]`, `bridge_error: []`, `failure: null`. Its `url` is exactly the check-6 iframe src.
- (b) motion: the three scrub readouts differ — 0% `2:45 GAME 1 OF 2 — RANDY`, 50% `1:22 GAME 1 OF 2 — RANDY`, 100% `0:00 GAME 2 OF 2 — DEFAULTLARGE` — crossing a real game boundary. Not a frozen frame.
- (c) I viewed viewer-smoke.png myself (1280×800). It shows the game, legibly: a scorebug strip with CLAN ASH / CLAN BASIL, each seat's real player name and its doctrine one-liner, running points 83/16; the endcard with headline "CLAN ASH TOOK ALL THREE FLAGS AT ROUND 1958", the aggregate stat line (score 273 — 26, flags lifted 28/9, traps 159/87, …), both clans' full doctrine prose, and a "the war" per-clan totals block; an event feed at right (game 1/2 begins/wins, doctrine-read lines); a transport strip with rewind/step/play/+25/loop/fast-forward, a spoilers toggle, `round 1958 / 2000`, speed buttons 1×–16×, and a full-width scrub bar. This is the starter's chrome shape (transport strip + scrubber + scorebug + endcard), not a lookalike rewrite.
- Reconciliation I did that the verifier did not: the scorebug's 83/16 at capture time equals the replay's `game_end` (game 1 index, i.e. game 2) `points: [83,16]` — a per-game points display, consistent with the record; the endcard's 273—26 equals `result.scores`; the headline's "round 1958" equals game 2's `rounds_played`. Picture and record agree field-for-field.
- The verifier's spectator-judgment paragraph exists, is written from the rendered evidence, and its claims check out against the PNG and JSON.

## Ruling on the known cosmetic defect — endcard `#bc24-flags` overlap: NOT BLOCKING, recorded as residue
Confirmed by my own eyes in viewer-smoke.png: at 1280 px in the endcard state, the `#bc24-flags` pill ("Clan Ash ●●● – ○○○ Clan Basil  0 to win") sits over the clock/status caption and letter fragments of "MATCH OVER"/"FINAL" bleed through around the pill's edge. Why not blocking: no definition-of-done item names it — check 8's two-part rule (loaded + three differing clocks) holds, and its legibility standard ("legible, and it shows the game") is met: every load-bearing readout (winner, scores, doctrines, stats, transport, round counter) is fully legible; the occlusion touches one caption in one state at one width, and the clock itself was read programmatically without ambiguity. The phase-30 judge ruled it a non-blocking observation for the same reason (r1-verdict.md lines 324–328: "no checklist item names it"), and the verifier reproduced rather than hid it. Inflating a partially-occluded caption into a blocker would not survive SPEC's own text.

## Residue to record
- [legibility] `#bc24-flags` pill overlaps the clock/status caption in the endcard state at 1280 px ("MATCH OVER"/"FINAL" bleeds through). Cosmetic, endcard-only. Settle by: a z-order/background fill or offset on the pill in the bc24 year block, verified by re-running the CI viewer smoke at 1280 px in the endcard state; file as a follow-up card (next battlecode-year run or fleet card), not a re-open of this run.
- [legibility] No separately rendered momentum waveform is visible on the scrub bar in the endcard screenshot (plain filled track). `#scrub` responded to all three programmatic scrubs, so this is at most a cosmetic note carried from the verifier's own observation; no checklist item names a waveform for this state.

## Blocking items
None.

## Verifier report audit
| check | verifier said | judge verified | agrees |
|---|---|---|---|
| 1 | 2 completed rounds after fillers (02:07:00Z) | re-fetched rounds; log.md lines 97/99 | yes |
| 2 | both champions ranked, fillers absent, both LLM | re-fetched leaderboard; policy_kind/log/design manifest | yes |
| 3 | ereq_eed98756 completed w/ replay, participants correct | re-fetched episode request | yes |
| 4 | strict JSON, protocol match, reason=complete, fallbacks [0,0], legit end_reasons | re-fetched S3 bytes, re-ran every jq, checked design §End conditions + line 710 | yes |
| 5 | logs CLEAN after byte-repr decode | re-fetched, re-decoded, re-grepped | yes |
| 6 | static route via SSR playlist + session POST, no /client/replay | re-fetched page + POST; substitution is the playbook-documented method | yes |
| 7 | committed release-result.json declares static bundle | read the committed file | yes |
| 8 | loaded=true, 3 differing clocks, legible, starter chrome, overlap disclosed | viewed PNG/JSON myself, re-fetched CI conclusion, reconciled scorebug 83/16 to game_end points | yes |

All eight checks TRUE at the current head. The run may proceed to phase 70.

BLOCKING: 0
