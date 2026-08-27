blocking: 0

# Phase-60 verdict — flatland

Head: coworld `flatland` v0.1.5 · `cow_f29f97b1-da55-4662-8dbc-cefde73f528d` ·
manifest `sha256:ab884d3298105799394a683dc476cade0c9746d52dc309896c6f4bfdaca22883` ·
league `league_b8ffbdda-2f8f-45af-b905-e600ba385cff` · division `div_444f4a49-4ebc-4a04-aee6-f05dd6d88993`
Checklist: `docs/SPEC.md` §Definition of done (phase 60), as commanded by `prompts/60-verify.md`.
Independent read written before reading VERIFY.md: **yes** — every fetch below was made fresh in
this judge session (2026-08-27 ~20:40–20:50Z) before VERIFY.md was opened. Declared contamination:
the coordinator's brief summarised VERIFY's verdict count and its three flagged observations before
I started; the evidence below is my own fetches, not the brief's summaries.

Verdict: **VERIFY.md's 8/8 TRUE stands. BLOCKING: 0.** Every decisive evidence line in VERIFY.md
reproduced at the current head; the three flagged observations are all correctly classified as
non-blocking. Two minor evidence-quality corrections to VERIFY.md are recorded below; neither
changes a verdict.

## Independent checklist pass (all fetched by the judge, none inherited)

| # | item | status | decisive evidence (judge's own fetch) |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** | `GET /rounds?league_id=$L` → **4** completed (r1 19:50:00Z…r4 20:35:02Z created; r4 completed 20:42:03Z), 0 failed/discarded, every `error` null. Fillers provably in effect for round 1: round 1's own episode request `ereq_e3024455-1080-49bd-81f9-429f24019e25` has participants `[daveey ×1 is_filler:false, daveey-1 is_filler:false, daveey ×2 is_filler:true]` — a filler cannot be seated in a round unless it was registered when that round was scheduled. `GET /leagues/$L/filler-policies` → `flatland-timetable:v3` (afcff3e9…), `flatland-yielder:v3` (02c72099…), neither id equal to a champion's (9aef8143…, e41a0e59…). |
| 2 | Both champions ranked, fillers absent | **TRUE** | `GET /divisions/$D/leaderboard` (bare list, 2 rows exactly): `1 daveey-1 flatland-pathfinder:v3 1029.32 rounds=4 wins=3.0` / `2 daveey flatland-signalman:v2 970.68 rounds=4 wins=1.0`. Fillers absent by absence — the list has no third row. |
| 3 | Latest round's ereq completed with replay | **TRUE** | At VERIFY's head the latest was round 3: `GET /episode-requests/ereq_c4b78ba5-d4e8-4ab6-8504-c54ae08c812d` → `status:"completed"`, `replay_url:"…/4fe82cbb-76e5-49a9-a0f8-4a1cb64bba2e.replay"`, participants daveey + daveey-1 `is_filler:false`, two `is_filler:true` seats (named `Baseline`/`Baseline (2)` in the replay's `results.names`). The round completed since (r4, `round_5ec36cc7`) is also `completed` — the check does not decay. |
| 4 | Replay bytes valid, show the game | **TRUE** | Fetched the S3 bytes myself (484 876 B, magic `C O W L D F L T`), ran the repo's `tools/replay_summary.py` (fetched fresh from `Metta-AI/cogame-flatland`): `jq -e` → `strict UTF-8 JSON: ok`; `protocol=flatland/v1`, `results.reason="complete"` (no exception needed), `arrivedTotal=15`, `tickCount=496`. Champion seats: 62/62 order records `source=="llm"`, `llmTurns:[31,31,0,0]`, `fallbackTurns:[0,0,0,0]`, 0 fallback orders; verbs over LLM orders `{hold:127, run:191, siding:48, route:6}`; 60 radio lines with real coordination text (e.g. turn 1 Beta: "single track is up-only for me: J2->J5, J6->J8. T09 running now to F, others staggered."). Binary-container substitution is design-declared: `design.md` §"Replay bytes (self-sufficient)" names `replay_summary.py` as "**the phase-60 substitute for SPEC §Definition of done check 4**" — same mechanism as the SPEC's own design-declared `deadline` exception; the check's intent (valid bytes, non-scripted champions, not all fallbacks) is fully proven. |
| 5 | Hosted game log clean | **TRUE** | Judge's own fetch of round 3's log (`ereq_c4b78ba5…/artifacts/logs`, elevated, 128 236 B): `grep -E 'falling back\|LLM provider is unavailable\|cut off at max_tokens\|rejected'` → **CLEAN**. Round 1 (`ereq_e3024455…`, 128 240 B) also CLEAN on my own grep. Round 2 is the flagged observation — ruled on below. |
| 6 | Public page uses the static replay path | **TRUE** | Raw HTML of `https://softmax.com/flatland` has no iframe (client-rendered, as the prompt and playbook anticipate — not a false negative). Featured match present in the SSR payload `state.playlist[0]` (now `flatland.r4.e1`, coworldId `cow_f29f97b1…`). `POST $BASE/coworlds/replays/session` → `viewer_url = …/v2/coworlds/replays/static/cow_f29f97b1-…/sha256%3Aab884d32…883/index.html?replay=…&v=2`, `ready:true`; the `<sha>` URL-decodes byte-equal to `STATE.coworld.manifest_sha`. No `/client/replay` anywhere. VERIFY records which sources it used (SSR + session route), as the prompt requires. |
| 7 | Certification declared the static bundle | **TRUE** | Read the **committed** `runs/2026-08-27-flatland/release-result.json` myself: `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` — contains the required prefix verbatim. |
| 8 | Viewer executed; spectator judgment | **TRUE** | `gh run view 33113882071` → `conclusion:"success"` (created 20:33:16Z, 2 s after the logged dispatch). Committed `viewer-smoke.json`: `loaded:true` (`data_replay_loaded:"true"`, `data_replay_error:null`, first frame 4 972 ms, `failure:null`); three clock readouts **differ in every field** — 0 % `TICK 0/496 · TURN 1/31 · ARRIVED 0`, 50 % `TICK 266/496 · TURN 17/31 · ARRIVED 13 · DEADLOCK 2`, 100 % `TICK 496/496 · TURN 31/31 · ARRIVED 15 · BROKEN 3`. Both parts of the two-part TRUE condition hold. I viewed `viewer-smoke.png` myself: it is the starter's chrome (transport strip with restart/play/+5s/loop/speed chips 1×–16×, spoilers toggle, scrubber with coloured beat markers and momentum series, four-plate scorebug, endcard) showing the endcard at 100 % — `ON TIME 13`, `NETWORK SCORE 13151`, "11 breakdowns, 2 jams, 2 deadlocks, 438 ticks lost (tickCap)", per-dispatcher plates `Signalman 1 / Pathfinder 3 / Yielder 4 / Yielder 5` whose rows (`Alpha 1·3·518·2`, `Beta 3·3·0·2`, `Gamma 4·4·0·2`, `Delta 5·5·0·2`) reconcile exactly with the replay's `onTime:[1,3,4,5]` / `arrived:[3,3,4,5]`. Legible, in motion, unmistakably this game. |

## Refuted

None. Every VERIFY.md verdict I attempted to refute survived on my own fetches. The closest calls:

- **§1's "fillers were registered at 19:49Z"** — this timestamp is not itself in any fetched
  evidence (the filler-policies endpoint returns no `created_at`, and the log.md line is stamped
  19:50:51Z, *after* round 1's 19:50:00.39Z `created_at`; log lines are written in batches after the
  actions). The stated timestamp is therefore unverifiable as written — but the check's substance
  does not rest on it: round 1's episode seated two `is_filler:true` participants (my fetch of
  `ereq_e3024455…`), which is direct proof the fillers were set before round 1 ran. Verdict TRUE
  stands on stronger evidence than VERIFY cited. Evidence-quality note only.
- **§4's "champions use three of the four verbs"** — undercount: my group-by over LLM-sourced
  orders shows all **four** verbs (`hold, route, run, siding`; `route` ×6). Errs against the run,
  changes nothing.

## Rulings on the three flagged items

**1. Round 2's 9 fallback/timeout log lines — NON-BLOCKING.** Reproduced independently: my fetch of
`ereq_6b35ad65-75d5-4c60-ad2e-7bdbb0bac1e6/artifacts/logs` shows exactly 5× `seat 1 attempt 1
failed … Timeout was reached POST http://127.0.0.1:9100/…haiku…/invoke` and 4× `seat 1 falling back
to yielder (parse_error)` on turns 6/11/15/26; the same log's bedrock-sidecar container has **63
`bedrock_sidecar_complete` records, all `ok:true`, all `status_code:200`, max `latency_ms` 8059** —
so this is the game's own `attempt1Ms = 9000` sitting ~1 s above the haiku latency tail, not a
provider outage; no `LLM provider is unavailable` line exists. Round 2's replay (my own decode):
`fallbackTurns:[0,4,0,0]`, `llmTurns:[31,27,0,0]`, `reason:"complete"`, arrived 10 — the designed
degrade-never-hang path, 4/31 turns on one seat, a small minority even by check 4's standard.
Checklist item 5 binds **the latest round's** hosted log, and the prompt's retry budget explicitly
sanctions "a different round" as a retry approach; rounds 1 and 3 grep CLEAN on my own fetches.
VERIFY did not claim a platform-wide exception, judged the check on its own terms, and disclosed the
dirty round in full — exactly right. Carry forward as a tuning note (raise `attempt1Ms` margin) and
a cause-enum bug (`parse_error` logged for transport timeouts, against design.md's
`cause ∈ {timeout, parse_error, transport_error, …}`) — both confirmed, neither named by any
§Definition of done item.

**2. Four console 404s for `soldier_*_front_gun.png` — NON-BLOCKING.** Reproduced from the
committed `viewer-smoke.json` `console_tail`: four leftover coworld-ctf sprite references the
flatland bundle does not ship. Item 8's TRUE condition is (a) `loaded:true` (b) advancing clocks
(c) legible judgment — all hold with `data_replay_error:null` and `failure:null`, and the png shows
no visual hole where a spectator would look. No §Definition of done item requires a clean console.
This is not the cogame-gridlock failure (the chrome IS the starter's, verified from the png);
it is a dangling-reference cosmetic defect — phase-30 item-14 class, fix in a patch release.

**3. `feed_lines: 0` at 100 % scrub — NON-BLOCKING.** The smoke samples the feed with the play head
parked at 100 %, where the endcard overlays it by design; the png shows the feed rail behind the
endcard (`DELTA Baseline (2) 5/5 of 6 · GAMMA Baseline 4/4 · BETA daveey-1 3/3 · ALPHA daveey 1/3
late 518`), and "who is winning and why" is carried by the scorebug, the endcard tables and the
scrubber's beat markers, all rendered. Honest gap: this run has no rendered proof of live feed rows
mid-episode — a smoke-tooling improvement (sample the feed at 50 %), not a checklist failure. No
§Definition of done item names the feed.

## Verifier report audit

| claim in VERIFY.md | I verified | agrees |
|---|---|---|
| §1: 3 completed rounds, 0 failed, after fillers | 4 completed now; fillers seated in round 1's episode (stronger proof than the 19:49Z claim, which is unsourced) | yes (evidence-quality note) |
| §2: leaderboard 2 rows, both champions, fillers absent | same rows, updated to rounds=4 | yes |
| §3: ereq_c4b78ba5 completed, replay_url, seats 0/1 champions, 2/3 fillers | byte-identical on my fetch | yes |
| §4: COWLDFLT magic, strict JSON via replay_summary.py, reason complete, 62 llm / 0 fallback, real radio | reproduced end-to-end from S3 | yes ("three of four verbs" is actually four) |
| §5: round 3 CLEAN; round 2 = 9 lines, sidecar 63/63 ok max 8059 ms | reproduced both greps and the sidecar counts exactly | yes |
| §6: no raw iframe; SSR playlist featured match; session route static + ready:true; sha = manifest_sha | reproduced (playlist now r4) | yes |
| §7: committed release-result.json contains the required string | read the committed file | yes |
| §8: run 33113882071 success; loaded:true; three differing clocks; endcard values match replay results | `gh run view` conclusion success; json + png match verbatim; endcard rows = onTime/arrived arrays | yes |

## Non-blocking observations (carried forward, none tied to a checklist item)

1. `attempt1Ms=9000` vs an observed 8.06 s sidecar latency tail leaves <1 s margin (round 2 evidence).
2. Fallback `cause` mislabelled `parse_error` on transport-timeout turns.
3. Four dangling `soldier_*_front_gun.png` starter references in the static bundle (console 404s).
4. Viewer smoke samples `feed_lines` only at 100 %, where the endcard occludes the feed.
5. Scorebug plate labels truncate to `SI…`/`PA…`/`YI…` at 1280 px (starter `.tiny` density artefact).
6. VERIFY §1's "19:49Z" filler timestamp is asserted, not fetched; future runs should cite the
   seated-filler participants of round 1 instead, which is the decisive evidence.

BLOCKING: 0
