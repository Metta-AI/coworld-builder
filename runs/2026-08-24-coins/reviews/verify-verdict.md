blocking: 0

# Phase 60 verdict — coins (re-verification adjudication)

Judge: fresh context, 2026-09-03. Adjudicating `runs/2026-08-24-coins/VERIFY.md` (written
2026-09-03T19:22:23Z, commit 2662eb6, claiming 8/8 TRUE) against `docs/SPEC.md` §Definition of
done and `prompts/60-verify.md`. Independent read written before consulting any disposition
other than VERIFY.md itself; every check below was **re-fetched live by the judge** (rounds,
leaderboard, episode request, replay bytes, hosted log, softmax.com/coins SSR payload, replay
session endpoint, viewer-check run conclusion) — not taken from the document. The viewer PNG
was inspected by the judge directly.

Reading order followed: SPEC §Definition of done → prompts/60-verify.md → VERIFY.md →
viewer-check/{viewer-smoke.json, viewer-smoke.png} → design.md → release-result.json → log.md.

---

## Check 1 — ≥2 completed rounds after fillers set — **VERDICT UPHELD (TRUE)**

Re-fetched: `GET /rounds?league_id=league_e9506fcc…&limit=20` → HTTP 200, **20/20
`completed`** (rounds 175–194), 0 failed/discarded, latest completed round is still 194
(`round_c2415ebd-…`) — identical to VERIFY.md's table. Fillers were registered before round 1:
`log.md` line `2026-08-25T01:56:08Z 50 fillers 200: a652fffc (reciprocator:v2) + 9356e1ac
(titfortat:v2) registered; neither champion in list`, with `round 1 pending` logged in the same
minute. VERIFY.md additionally re-fetched `GET /leagues/$L/filler-policies` fresh and pasted the
two filler rows. Requirement is ≥2; evidence shows 20. The evidence discharges the check as
specified.

## Check 2 — both champions ranked; fillers absent or Baseline — **VERDICT UPHELD (TRUE)**

Re-fetched: `GET /divisions/div_d7a79bf3…/leaderboard` → HTTP 200, bare list, byte-for-byte
consistent with VERIFY.md:
- `daveey` / `coins-truce:v2` — rank 4, `rounds_played` **193** ≥ 1;
- `daveey-1` / `coins-ledger:v2` — rank 3, `rounds_played` **192** ≥ 1;
- no row labelled `Baseline`, and neither filler policy (`coins-reciprocator:v2` /
  `coins-titfortat:v2`, policy ids `93f81540…` / `36c09d66…`) appears in any row.

Refutation attempt — do the five outside entrants (richard, relh, Andre von Auto, Andrew
Brower, docxology), two of whom outrank both champions, break the item? **No.** SPEC item 2
requires both champions **ranked** with the prompt's `rounds_played ≥ 1`, and fillers absent or
Baseline. It does not require champions to lead. The rank-1/2 `co-gas-coins-reciprocator-*`
labels are other players' submissions (different player ids, different policy ids), not this
run's fillers — VERIFY.md verified the policy-id distinction explicitly and correctly.

## Check 3 — latest round's episode request completed with a replay — **VERDICT UPHELD (TRUE)**

Re-fetched: `GET /episode-requests/ereq_5af03905-…` → `status:"completed"`, non-null
`replay_url` (`…/replays/abaf7183-….replay`), `round_id` = round 194's id, participants
`daveey` (`coins-truce` v2, position 0) and `daveey-1` (`coins-ledger` v2, position 1), both
`is_filler:false`, scores 13–10. Matches VERIFY.md exactly.

Two deviations from the prompt's literal command, both legitimate and both disclosed:
(a) the flat `?round_id=` route now 405s — VERIFY.md used the nested
`/rounds/$R/episode-requests`, the working call the playbook records; (b) the prompt's
`.entries[0]` heuristic was replaced by selecting the champion-vs-champion pairing out of the
21-episode round-robin, with the other champion episodes listed so the pick is not
cherry-picked. The check's substance — completed, replay present, participants named correctly
— is discharged. No filler is seated in any episode, so the "fillers as `Baseline (N)`" clause
is vacuously satisfied.

## Check 4 — replay bytes valid and show the game — **VERDICT UPHELD (TRUE)** (was FALSE 2026-08-25)

Re-fetched and re-parsed the replay bytes myself (36017 bytes, HTTP 200):
- `jq -e` strict parse: **ok** (valid UTF-8 JSON);
- `protocol` = `coins.replay.v1` — exactly design.md's pinned string. The manifest declares no
  replay-protocol string (its `protocols` are player/global docs), so VERIFY.md correctly
  checked the manifest-side contract that exists — the results schema — and
  `results.reason == "random_end"` is in the manifest enum
  `["random_end","beat_cap","deadline","forfeit"]` and design.md's legal set. Not a `deadline`,
  so no design exception needed;
- order sources: **`{"llm":24}` — 24/24, zero fallbacks**, `[.events[]|select(.fallback==true)]`
  → 0. Confirmed independently;
- the game's subject matter happens: `thefts:[0,1]`, `stolenFrom:[1,0]`, one real `theft` event
  at beat 12, three `blocked why:"restraint"` events, scores 13–10.

The decision content pasted in VERIFY.md (`say`/`notes` referencing coordinates, theft
counters, score gaps) is non-trivial. The four-round trend table (110/110 llm across rounds
191–194) exceeds what the check requires. The 2026-08-25 failure mode (41/48 fallbacks,
thefts [0,0]) is demonstrably gone. TRUE as specified.

## Check 5 — hosted game log clean — **VERDICT UPHELD (TRUE)** (was FALSE 2026-08-25)

Re-fetched `GET /episode-requests/ereq_5af03905/artifacts/logs` (elevated header, HTTP 200,
4791 bytes), decoded the python byte-string reprs myself per playbook §10, and grepped the
decoded text: **zero matches** for `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected` → CLEAN. 24 sidecar LLM calls, all `HTTP/1.1 200 OK` — agreeing exactly
with check 4's 24 `source:"llm"` orders. No 429, no throttle string anywhere in the decoded
log. Both seats registered `llm`. VERIFY.md's methodology note (raw grep is not evidence;
decoded grep is) is correct and was honoured. Since the log is clean, no platform-wide
cross-check was required. TRUE as specified.

## Check 6 — public page uses the static replay path — **VERDICT UPHELD (TRUE)**

Re-fetched `https://softmax.com/coins` (HTTP 200): the raw-HTML iframe grep finds nothing
(client-rendered — per the playbook, *unknown*, not a failure), and the SSR payload carries
`state.playlist[0]` = featured match `coins.r194.e11` with this run's `leagueId`
(`league_e9506fcc…`) — featured match **present**. Re-ran the session endpoint myself:
`POST /coworlds/replays/session` for the featured replay → HTTP 200,
`viewer_url = …/v2/coworlds/replays/static/cow_bd320430-…/sha256%3A6b286bdb…/index.html?v=2#replay=<s3 url>`,
`ready:true`. That is the static route in its documented post-2026-08-28 fragment form
(`playbooks/observatory-api.md` §Featured match: "both are the static route"), and it is not a
`/client/replay` pod URL. VERIFY.md recorded which source it used, as the prompt requires.

Refutation attempt — the `<cow_id>`/`<sha>` in the URL are the canonical v0.1.4 coworld's
(`cow_bd320430…`), not this run's v0.1.2 (`cow_e5c32ad5…`, which 404s on the session endpoint).
Does that break the item as written? **No.** SPEC item 6 constrains the *shape* of the iframe
src the public page serves (`static/<cow_id>/<sha>/…`, never a pod URL); it does not pin the
cow_id to STATE's. The page serves the coworld the league is actually running — same repo,
same owner, a later release, still a static bundle — and VERIFY.md flagged the drift openly
rather than absorbing it. The featured match being an outside pairing (richard vs relh) also
breaks nothing: item 6 requires "featured match present", not a champion match.

## Check 7 — certification declared the static bundle — **VERDICT UPHELD (TRUE)**

Read the committed `runs/2026-08-24-coins/release-result.json` myself:
`.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)"` — contains the required string exactly. Source is
the committed phase-40 artifact (release run 32798747762, v0.1.2), which is what the prompt
requires — the check is defined against this run's own release artifact, and the later v0.1.4
platform release does not alter what this run's certification output said. `certify.ok: true`,
10/10 transcript steps passed. TRUE as specified.

## Check 8 — spectator judgment; viewer executed — **VERDICT UPHELD (TRUE)**

- **Execution:** viewer-check run **33795836783** re-checked via `gh run view` →
  `status: completed, conclusion: success`, created 2026-09-03T19:20:17Z — 2 s after the logged
  dispatch, so the find-the-new-run race was handled. Evidence committed at
  `runs/2026-08-24-coins/viewer-check/` as required.
- **(a) loaded:** `viewer-smoke.json` → `loaded: true`, `ms: 1313`,
  `data_replay_loaded: "true"` **and** bridge `["loading","ready"]`, `bridge_error: []`,
  `failure: null`. Both load signals fired.
- **(b) advances:** the three scrub readouts differ — `BEAT 1 / 12 TICK 1 OF 240 · 6 COINS` →
  `BEAT 7 / 12 TICK 135 OF 240 · 3 COINS` → `FINAL 12 BEATS · RANDOM_END` — beat, tick and
  coins-on-board all changing, so the wasm bundle is genuinely stepping frames.
- **(c) judgment:** I opened `viewer-smoke.png` myself. It is a finished broadcast frame:
  two-sided scorebug (13 copper / 10 cobalt with STOLE 0 / STOLE 1), the endcard
  "COINS-PLAYER HOLDS THE ROOM" with `12 BEATS · ENDED AT RANDOM · 25 COINS`, the rules line,
  and a results table reading exactly `13/15/0/1/100%` and `10/10/1/0/90%` — every number
  matching the replay's `results` (`scores [13,10]`, `pickups [15,10]`, `thefts [0,1]`,
  `stolenFrom [1,0]`, `restraint [1.0,0.9]`, `reason random_end`). Transport strip with
  loop/pause/+5s/spoilers/speed chips, `RED WINS 239 / 239`, and a score-lead momentum graph
  with per-beat marks — the paintbot/raid/hive starter chrome, not a gridlock-style rewrite.
  VERIFY.md's judgment paragraph describes this frame accurately, reconciles it against the
  replay events, and says plainly what is weak (duplicate COINS-PLAYER labels, spoilers-on
  totals at tick 1, feed_lines 0, font.ttf 404) rather than glossing it. All three SPEC item-8
  conditions hold.

---

## Independent definition-of-done pass

| # | item | status | evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | TRUE | judge re-fetch: 20/20 completed (175–194); fillers set 2026-08-25T01:56:08Z before round 1 (log.md) |
| 2 | both champions ranked; fillers absent/Baseline | TRUE | judge re-fetch: daveey rank 4 rp 193, daveey-1 rank 3 rp 192; no filler/Baseline row |
| 3 | latest round's ereq completed with replay | TRUE | judge re-fetch: ereq_5af03905 completed, replay_url present, participants daveey/daveey-1 |
| 4 | replay valid, shows the game, not all fallbacks | TRUE | judge re-parse: strict JSON ok, protocol coins.replay.v1, reason random_end, 24/24 llm, 0 fallback, 1 theft + 3 restraint blocks |
| 5 | hosted log clean | TRUE | judge re-fetch + decode: 0 pattern matches, 24× HTTP 200, no 429/throttle |
| 6 | public page static replay path; featured match | TRUE | judge re-fetch: SSR playlist[0]=coins.r194.e11; session → `…/replays/static/<cow>/<sha>/index.html?v=2#replay=…`, no /client/replay |
| 7 | cert output: replay liveness skipped (static) | TRUE | committed release-result.json `.certify.replay_liveness` contains the exact string |
| 8 | viewer executed, advances, judged | TRUE | run 33795836783 success; loaded:true; 3 differing clocks; PNG inspected by judge, matches replay results exactly |

## Verifier report audit

| claim | VERIFY.md said | judge verified | agrees |
|---|---|---|---|
| completed rounds page | 20/20, latest 194 | 20/20, latest 194 | yes |
| leaderboard rows | 7 rows, champions rank 3/4 | identical rows | yes |
| ereq_5af03905 | completed, replay abaf7183, champions seated | identical | yes |
| order sources | {"llm":24}, 0 fallback | {"llm":24}, 0 fallback | yes |
| log CLEAN | 0 matches decoded, 24× 200 | 0 matches decoded, 24× 200 | yes |
| session viewer_url | static fragment form, ready:true | identical URL shape, ready:true | yes |
| release-result string | replay liveness skipped (static) | present verbatim | yes |
| viewer-check 33795836783 | green, loaded:true, 3 clocks differ | conclusion success; json/png as claimed | yes |

No claim in VERIFY.md failed refutation. No verdict is asserted without inline output; the two
non-fetched items (7, 8's artifact) are exactly the documented exceptions the prompt allows.

## Findings

1. **NON-BLOCKING** — Coworld drift vs STATE: canonical `coins` is `cow_bd320430-…` v0.1.4;
   STATE records `cow_e5c32ad5-…` v0.1.2, which now 404s on the replay-session endpoint.
   Checks 3–6/8 correctly judged against what the platform actually serves; check 7 against
   this run's own artifact. No SPEC item pins the cow_id. STATE update is the coordinator's.
2. **NON-BLOCKING** — replay `policyNames = ["coins-player","coins-player"]`: scorebug/endcard
   label both seats identically; a spectator needs the colour cue to tell champions apart.
   Known residue, legibility item, does not fail any of item 8's three conditions.
3. **NON-BLOCKING** — spoilers-on default: final totals visible at tick 1 (`took 15/10` in the
   0 % scorebug capture). Cosmetic.
4. **NON-BLOCKING** — `feed_lines: 0` in the smoke capture (endcard covering the board at
   capture time; say-texts confirmed present in the replay). Unresolved from the artifact
   alone; honestly disclosed.
5. **NON-BLOCKING** — `font.ttf` 404 in the static bundle; renders in fallback font.
6. **NON-BLOCKING** — ladder cadence ~4h48m vs configured 15 min; platform scheduling, not a
   definition-of-done item.
7. **NON-BLOCKING** — `release-result.json` records `hosted_certification: "certifying"`
   (in-flight at artifact-capture time). A phase-40 observation; check 7 as written requires
   only the replay-liveness string, which is present, and the coworld has been serving league
   episodes for 194 rounds since.

No blocking findings. VERIFY.md's 8/8 TRUE verdict stands in full.

BLOCKING: 0
