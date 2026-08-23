blocking: 0

# Phase-60 verdict — rumor
Run: 2026-08-23-rumor · cow_46b04bae-028d-4f7a-8444-c18590d68521 v0.1.0 · league_21909e9d-0b13-4750-afec-f8a4213c03a7 / div_52959ca4-61f9-4828-bbe5-33261daea950
Checklist: docs/SPEC.md §Definition of done (items 1–8) as operationalised by prompts/60-verify.md.
Independent read written before reading VERIFY.md: **yes** — I read the checklist, the design note,
STATE.json, log.md, all four committed artifacts (ep.replay, release-result.json, viewer-check/*),
the rendered viewer-smoke.png, and ran my own API/GH spot-checks before opening VERIFY.md.

## Provenance ruling (the clobber-and-rewrite blockquote)

VERIFY.md declares it was truncated by a coordinator-side `git reset --hard` and rewritten from the
verifier's transcript, with no evidence re-fetched. I treated every claim in it as unverified and
re-checked what is checkable now. **The evidence chain holds**, on three independent grounds:

1. **The two locally-held artifacts are byte-identical to their independent sources.** I re-downloaded
   the `viewer-check` artifact of run 32667485621 fresh and `cmp`'d all four files against the
   committed `runs/2026-08-23-rumor/viewer-check/` copies: `viewer-smoke.json`, `viewer-smoke.png`,
   `smoke-stdout.txt`, `smoke-stderr.txt` — **all identical**. I fetched
   `https://softmax-public.s3.amazonaws.com/replays/829157f1-6642-44f7-9543-566df8ac959c.replay`
   fresh and `cmp`'d it against the committed `ep.replay` (18 414 B) — **byte-identical**.
2. **Every server-side claim I re-fetched matches the transcript quotes** (details per check below):
   round ids and the round-1 error string verbatim, filler policy_version_ids, ereq id + replay_url,
   participants, leaderboard rows, manifest_hash, the SSR `state.playlist` behaviour, and the CI run's
   status/conclusion.
3. Nothing in the rewritten file contradicts anything on the live services or on disk.

## Item-by-item ruling

### 1. ≥2 completed rounds after fillers were set — **TRUE, confirmed**
My fetch of `GET /rounds?league_id=$L&limit=20` (2026-08-23T~21:5xZ): rounds now number 1–4 —
round 1 `failed` with error verbatim `"Temporal RoundWorkflow failed before settling the round."`
(matches VERIFY.md line 68 exactly), rounds **2, 3, 4 all `completed`** → completed count is now 3,
≥ 2. Fillers: my elevated GET of `/leagues/$L/filler-policies` returns exactly
`1c39bed2-6a01-445b-8581-a0123b2f58c8` (rumor-gossip v1) and `212b1fe4-1a64-4c1f-a944-3a1439e01c12`
(rumor-herd v1), matching STATE.policies.filler_version_ids and neither equal to a champion version
id (`3083c67e-…`, `e895c6ce-…` per the participants I fetched). log.md:44 records round 1 as the
pre-filler auto-round; rounds 2+ post-date the filler PUT, and my round-3/round-4 participants fetch
shows eight `is_filler: true` seats drawn from that list. The failed round's error is recorded
verbatim, as the checklist requires.

### 2. Both champions ranked, fillers absent — **TRUE, confirmed**
My fetch of `GET /divisions/$D/leaderboard` (bare list):
```
1  daveey    rumor-corroborate:v1  1000.0  3  0.0
2  daveey-1  rumor-skeptic:v1      1000.0  3  0.0
```
Both champions ranked, `rounds_played` now 3 (VERIFY.md said 2 at 21:27Z — round 4 has since
completed; not a contradiction, a later head). Exactly two rows: fillers **absent**, satisfying
"absent or `Baseline…`" by absence.

### 3. Latest round's episode request completed with a replay — **TRUE, confirmed**
At VERIFY time the latest completed round was 3; I re-fetched its episode request
`ereq_07ed5434-ccf3-4d07-a4ee-81753599f3b0`: `status: "completed"`, `replay_url:
https://softmax-public.s3.amazonaws.com/replays/829157f1-6642-44f7-9543-566df8ac959c.replay`
(matches STATE.verify.replay), participants seat 0 = `rumor-corroborate` / `daveey` /
`is_filler: false`, seat 1 = `rumor-skeptic` / `daveey-1` / `is_filler: false`
(player_id `ply_bac48eb1-…` = daveey-1, distinct from daveey's `ply_44ae9048-…`), eight filler
seats `is_filler: true`. I also checked the round that completed after VERIFY closed: round 4's
`ereq_5542d848-2891-4148-b58c-0813e6fea6fd` is likewise `completed` with a replay_url and the same
seat-0/seat-1 champions — the check also holds at the current head, not just at the transcript's
timestamp. VERIFY.md's shape note (fillers appear as structured `is_filler` rows here and as
`Baseline (N)` in the replay's `policyNames`) is accurate — I saw both forms myself.

### 4. Replay bytes valid and show the game — **TRUE, confirmed**
On the committed `ep.replay` (byte-identical to S3, see Provenance):
- strict UTF-8 decode + `json.loads` under Python's strict parser: **ok**;
- `protocol: "rumor.replay.v1"` — matches the design note (§Replay payload) and the manifest lineage;
- `results.reason: "complete"` — the normal ending, no deadline exception needed;
- events: `{start:1, round:6, say:50, vote:10, tally:1, end:1}` = 69, i.e. 60 decisions;
- champion seats (0 = daveey, 1 = daveey-1 per `policyNames`): 12 decisions (10 says + 2 votes),
  **all `scripted: false`**, messages 163–240 runes of substantive, game-relevant content (source
  ledgers, saboteur suspicion, corroboration counts — I read them); seat 0's claim moves A→B→(vote A),
  so it is play, not a constant. The 48 `scripted: true` decisions belong to the eight
  `Baseline (N)` filler seats, whose scripted play is their design (PLAYER_SCRIPTED baselines), not
  fallbacks — champion fallback count is **0**. No `fallback` key or string exists anywhere in the
  bytes. VERIFY.md's open declaration of the `.type=="decision"`/`.fallback` schema divergence from
  the prompt's bullwhip-flavoured jq is correct and honest; the substance of the check (champions
  non-scripted, non-trivial, not fallbacks) is met.

### 5. Hosted game log clean — **TRUE, confirmed by re-fetch**
I re-fetched `GET /episode-requests/ereq_07ed5434-…/artifacts/logs` with the elevated header myself:
HTTP 200, **27 811 bytes** (exactly the size VERIFY.md states).
`grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'` over the raw
bytes → **CLEAN** (a raw-bytes grep would catch the patterns even inside undecoded `b'…'` reprs, so
this is at least as strict as VERIFY's decoded grep). No platform-wide-Bedrock exception needed.

### 6. Public page uses the static replay path — **TRUE, confirmed**
Which source: like the verifier, I could not use the raw-HTML iframe grep — my fetch of
`https://softmax.com/rumor` (HTTP 200, 417 129 B) contains **no** `<iframe` (client-rendered, exactly
as playbooks/observatory-api.md §Featured match documents). What I verified instead:
- **Featured match present**: the page's SSR payload carries `state.playlist[0]` — now
  `rumor.r4.e1` (round 4, replayUrl `…/d73fdc8a-….replay`, matchup daveey vs daveey-1). At VERIFY
  time it was `rumor.r3.e1` with the check-4 replay; the playlist advancing to the newer round is
  the feature working, not a contradiction.
- **Static route**: I made no POSTs (judge constraint), so I did not re-call `replays/session`; but
  the URL the verifier's CI run actually loaded (recorded in `viewer-smoke.json.url`, produced by
  run 32667485621 which I verified) is
  `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_46b04bae-…/sha256%3A83e14e80…/index.html?replay=<s3 url>&v=2`
  — the `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=` shape with `<sha>` equal to
  the coworld's `manifest_hash` (I confirmed `manifest_hash` via my own `/coworlds` fetch, which also
  confirms the row has no `replay_viewer`/`featured_match` keys, exactly as VERIFY.md says). No
  `/client/replay` anywhere.

### 7. Certification declared the static bundle — **TRUE, confirmed**
Read from the **committed** `runs/2026-08-23-rumor/release-result.json` (phase 40's artifact):
`.certify.replay_liveness` =
`"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`
— contains the required string verbatim. `.certify.ok: true`, transcript "10 steps passed".

### 8. Viewer executed, then judged — **TRUE, confirmed**
- **CI fact checked, not accepted**: `gh run view 32667485621 -R Metta-AI/coworld-builder` →
  `✓ main viewer-check`, job `viewer-check in 31s (ID 97263090147)`, conclusion success, artifact
  `viewer-check` present. Fresh artifact download is byte-identical to the committed copy.
- **Gate (a) loaded**: `"loaded": true` in 732 ms via the `coworld-replay` bridge
  (`bridge: ["loading","ready"]`, `bridge_ready: true`, `bridge_error: []`, `failure: null`).
- **Gate (b) advances**: the three scrub clock readouts differ — 0 % `ROUND 1`, 50 %
  `ROUND 1 / 5 · WAITING ON 10`, 100 % `TRUTH — FLOODED · HONEST 5/8 · 5 FLOODED · 5 DRY`.
- **Gate (c) judgment**: I read `viewer-smoke.png` myself. It is a fully rendered, legible Rumor
  end-frame: RUMOR wordmark, top-band clock with the tally readout, REPLAY chip + «LOG toggle,
  a two-row scorebug carrying all ten seats with belief %, score and COG/SABOTEUR role tags, the
  graph stage visible behind a centred endcard (`THE TRUTH WAS FLOODED / HONEST COGS 5 / 8 /
  SABOTEURS: SPROCKET, TINKER` over a ten-row role/clue/vote/✓✗/score table), a BELIEF TIDE momentum
  strip, and a tick-marked scrubber reading `69 / 69`. It reconciles exactly with the replay record
  I parsed independently: `truth:"A"`/`optionA:"FLOODED"`, `honestCorrect:5/honestSeats:8`,
  `roles[5]`/`roles[8]` = Saboteur = aliases Sprocket/Tinker, votes 5×A/5×B = the clock's
  `5 FLOODED · 5 DRY` and `verdict:"split"`, scores 0.55/−0.25/−0.32/−0.55 displayed to one decimal
  as 0.6/−0.3/−0.3/−0.6, and 69 events = the 69/69 counter. It wears the starter's chrome (topband,
  scorebug, endcard table, momentum strip, transport + scrubber — the paintbot/raid/hive family
  layout), not a gridlock-style rewrite. VERIFY.md's explanation of `scorebug:""`/`feed_lines:0` as
  load-instant readouts is consistent with the populated scorebug in the post-scrub screenshot and
  with the collapsed-by-default feed.

## Spot-checks run (summary)

| # | spot-check | result |
|---|---|---|
| 1 | `GET /rounds?league_id=$L` | 3 completed (2,3,4), round 1 failed w/ error verbatim = VERIFY quote |
| 2 | `GET /divisions/$D/leaderboard` | daveey + daveey-1 only, rounds_played 3/3 |
| 3 | `GET /episode-requests?round_id=` + detail, rounds 3 and 4 | both completed w/ replay_url, champions at seats 0/1 |
| 4 | S3 fetch + `cmp` vs committed ep.replay; strict JSON parse; per-seat scripted counts | identical; ok; champions 12/12 non-scripted |
| 5 | elevated `GET …/artifacts/logs` (27 811 B) + raw grep | CLEAN |
| 6 | `https://softmax.com/rumor` SSR payload; `GET /coworlds` manifest_hash | playlist[0] featured match present; sha matches viewer URL |
| 7 | committed release-result.json | required string verbatim |
| 8 | `gh run view 32667485621`; artifact re-download + `cmp`; read the png | success; byte-identical; judgment stands |
| — | elevated `GET /leagues/$L/filler-policies` | the two filler version ids, neither a champion |

## Non-blocking observations

- Both champions sit at Elo 1000.0 with `episode_wins` 0 after three level rounds — the ladder's
  arithmetic on drawn episodes, not missing results; check 2 requires ranking, not separation.
- VERIFY.md's leaderboard/round counts are one round staler than the current head (its evidence is
  timestamped 21:27Z; round 4 completed 21:37Z). Every such difference is in the passing direction.

## Ruling

All eight checks TRUE at the current head; the rewritten VERIFY.md's evidence chain is intact — the
two locally-restored artifacts are byte-identical to their independent sources, and every
re-fetchable claim re-fetched true. No check's evidence is missing, unfetched, or contradicted.

BLOCKING: 0
