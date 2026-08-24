blocking: 0

# r-verify verdict — cogplomacy (phase 60 adjudication)
Head: run `2026-08-24-cogplomacy`, coworld `cow_9f7d3cbd-97fa-4d04-a835-1ad0661ca3a1` v0.1.1
Checklist: `docs/SPEC.md` §Definition of done (phase 60) / `prompts/60-verify.md`
Independent read written before reading VERIFY.md: **yes** — all eight items were re-fetched or
re-read from committed artifacts before VERIFY.md was opened. (The coordinator brief summarized
the verifier's flags; the API/file evidence below is my own.)

## Standing blocking findings

None. All eight definition-of-done items are TRUE at the current head, each proven by evidence
I fetched or read myself, not by VERIFY.md's assertions.

## Checklist pass (independent)

| # | item | verdict | decisive evidence | source |
|---|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** | `GET /rounds?league_id=league_cb035e15…` → rounds 2, 3, 4 `completed`, round 1 `failed` ("Temporal RoundWorkflow failed before settling the round"). Rounds 3 (created 13:43:35Z) and 4 (created 13:58:35Z) each ran a full episode with a replay, both after fillers (log.md:57, 13:29:57Z, before first trigger). **Check 1 passes on rounds 3+4 alone**; the hollow round 2 is not load-bearing. | re-fetched |
| 2 | Both champions ranked; fillers absent or Baseline | **TRUE** | `GET /divisions/div_832f5cdb…/leaderboard` (bare array) → rank 2 `daveey` `cogplomacy-diplomat:v2` rounds_played=2; rank 4 `daveey-1` `cogplomacy-opportunist:v2` rounds_played=2. Neither filler on the board. Ranks 1/3 are third-party entrants (`richard`, `relh`) who joined the public league mid-run — not fillers, not a falsifier of any item. | re-fetched |
| 3 | Latest round's episode request completed with replay; participants named correctly | **TRUE** | Round 4 (`round_6ddc6801…`) → `ereq_bf75023f-d606-4ef4-bc4a-2bd7a81e7476` `status:"completed"`, `replay_url` = `…/replays/a4d57c16-78e5-4073-8385-8a0b9f836265.replay`; participants: `daveey`/`cogplomacy-diplomat:v2` pos 1, `daveey-1`/`cogplomacy-opportunist:v2` pos 2, three seats `is_filler:true` (`hedgehog:v2` ×2, `expander:v2`), plus `relh`/`richard`. | re-fetched |
| 4 | Replay bytes valid; protocol; reason; champions doing the thing, not all fallbacks | **TRUE** | Fetched the S3 bytes myself: `jq -e` strict parse ok; `protocol` = `cogplomacy.replay.v1`; `results.reason` = `"complete"` (4/4 years, no deadline exception invoked). `scripted==true` events exist **only** on seats 4/5/6 (16/21/16) — the three Baseline fillers, scripted by design. Champion seats 1 (daveey, TURKEY) and 2 (daveey-1, ENGLAND): 16 non-scripted press/orders events each, zero fallbacks; sampled press is substantive free-text with letters and machine-checkable pledges (e.g. seat 1 Spring 1901: broadcast + 7 letters + peace/keepout pledges); adjudicate events carry 7 stabs across the game. | re-fetched |
| 5 | Hosted game log clean | **TRUE** | `GET /episode-requests/ereq_bf75023f…/artifacts/logs` (elevated) piped through the four-pattern grep → `CLEAN` (my own fetch). VERIFY.md additionally pastes the decoded game-container transcript: 7/7 seats connected, full 4 years in 178 s of a 720 s budget. | re-fetched |
| 6 | Public page uses the static replay path; featured match present | **TRUE** | Raw-HTML iframe grep empty (client-rendered — documented as *unknown*, per playbook). SSR payload of `https://softmax.com/cogplomacy` contains `state.playlist[0]` = featured match `cogplomacy.r4.e1` with `replayUrl` = the round-4 replay. `POST /coworlds/replays/session` → `ready:true`, `viewer_url` = `…/v2/coworlds/replays/static/cow_9f7d3cbd…/sha256%3A2c811d5e…/index.html?replay=<s3 url>&v=2`; the `<sha>` equals `STATE.coworld.manifest_sha` exactly; no `/client/replay` pod URL anywhere. | re-fetched |
| 7 | Certification declared the static bundle | **TRUE** | Read the committed `runs/2026-08-24-cogplomacy/release-result.json` myself: `jq -r '.certify.replay_liveness'` → `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`. Corroborated by committed `hosted-certification-0.1.1.txt`: `Canonical: yes`, `Hosted certification: certified (main-04b1b4c5f4b4)`, 10/10 pass, `Hosted smoke certification: passed`, manifest hash matches check 6's path. | committed file, read directly |
| 8 | Viewer executed; loaded:true; replay advances; spectator judgment | **TRUE** | `gh run view 32736614525` → `{"conclusion":"success","status":"completed"}` (my own check). Committed `viewer-check/viewer-smoke.json`: `loaded:true` (ms 1797) via the `coworld-replay` bridge (`bridge:["loading","ready"]`, `bridge_ready:true`, `bridge_error:[]`), `failure:null`; its `url` field is byte-identical to check 6's `viewer_url` (round-4 replay). Three scrub clocks all differ: `SPRING 1901` → `SPRING 1901 · PRESS · WAITING ON 7` → `WINTER 1904 · FINAL · GERMANY 7 CENTRES`. I viewed `viewer-smoke.png` myself: fully composed bullwhip-lineage chrome (COGPLOMACY wordmark, clock, scorebug plates with power·player·centres·units, proportional centre bar summing to 34 incl. `NEUTRAL 3`, dimmed 1901 map behind, endcard `FINAL — 4 YEARS · 34 CENTRES / richard (GERMANY) LED EUROPE` with a 7-row table matching `results` digit-for-digit, alliance graph, transport strip with colour-coded beat scrubber, `161 / 161` counter). Corroborating render `viewer-check-r3/` (round-3 replay, run 32735338630): `loaded:true`, three differing clocks, endcard `relh (RUSSIA) LED EUROPE` matching that episode. The judgment paragraph in VERIFY.md is accurate to the pixels. | re-fetched run status; committed artifacts read + screenshot viewed |

## Refuted

No verifier finding is refuted — VERIFY.md's eight TRUE verdicts all reproduced under my
independent fetches, and its three advisory flags are real observations correctly classified as
non-blocking (below).

## Adjudication of the flagged items

1. **Round 2 hollow settle** — verified: `ereq_828b2f79…` is `completed` with `episode_id:null`,
   `replay_url:null` (my fetch of `GET /episode-requests?round_id=round_31429ce9…`). Not blocking:
   item 1 requires ≥2 completed (not failed/discarded) rounds after fillers, and rounds 3 and 4
   satisfy it outright, each with a full episode and replay. VERIFY.md declares the caveat rather
   than hiding it — correct handling. Platform observation for the coordinator, not a coworld defect.
2. **Probe scorebug selector mismatch** (`scorebug:""`, `feed_lines:0` in viewer-smoke.json while
   the screenshot shows a populated scorebug and a collapsed `« LOG` panel) — not blocking. Item 8's
   binding conditions are (a) `loaded:true`, (b) three differing clock readouts, (c) a legible
   judgment written from the screenshot reconciled against the replay JSON; all three hold, and the
   SPEC's own precedent (an absent `#scrub` readout is "a legibility finding for phase 30, not a
   licence to skip the question") treats probe-readout gaps as advisory. The reconciliation was done
   from the screenshot, which I confirmed.
3. **`data-replay-loaded` attribute never set** (`signals.data_replay_loaded:null`) — not blocking.
   SPEC item 8(a) is explicitly disjunctive: `data-replay-loaded="true"` **or** the `coworld-replay`
   bridge's `ready`; `bridge_ready:true` with an empty `bridge_error` satisfies it. (It is a
   deviation from the design note's load-signalling paragraph, which promised the attribute —
   worth a follow-up, but the definition of done is what binds in phase 60.)
4. **STAB badge collision at 1280 px** (renders `STA…RUSSIA` where the badge abuts the next plate;
   right-most plate slightly clipped) — visible in the screenshot, confirmed. Cosmetic legibility
   polish, historically advisory; the scorebug remains readable and no DoD item names it. Not blocking.

## Fixer report audit (verifier-report audit)

| claim in VERIFY.md | I verified | agrees |
|---|---|---|
| 3 completed rounds (2,3,4), round 1 failed with quoted error | rounds API re-fetched, identical | yes |
| daveey rank 2 / daveey-1 rank 4, rounds_played 2 each, fillers absent | leaderboard re-fetched, identical (scores match to the digit) | yes |
| ereq_bf75023f completed, replay a4d57c16, seats as listed | re-fetched, identical | yes |
| replay strict JSON, `cogplomacy.replay.v1`, `reason:"complete"`, 0 champion fallbacks | re-fetched bytes, re-ran the filters, identical | yes |
| hosted log CLEAN on the four patterns | re-fetched with elevated header, `CLEAN` | yes |
| static viewer_url with manifest_sha, `ready:true`, featured match in SSR payload | re-fetched page + session POST, identical | yes |
| `release-result.json` liveness marker; hosted cert certified | read both committed files, verbatim match | yes |
| run 32736614525 success, loaded:true, 3 differing clocks; r3 corroboration | `gh run view` + committed jsons + both screenshots | yes |

Minor audit note (no verdict change): check 4's phrase "matches the manifest protocol" is loose —
the hosted manifest's `game.protocols` carries `player`/`global` (`cogplomacy.player.v1`), while
`cogplomacy.replay.v1` is the replay payload's own protocol string; the substantive proof that the
replay matches what the declared static bundle expects is that the bundle rendered it (check 8).

## Non-blocking observations

- Third-party entrants `richard`/`relh` joined mid-run and outrank daveey-1; no DoD item requires
  champions to lead the board, only to be ranked with rounds_played ≥ 1. Healthy public-league signal.
- daveey-1's sampled Fall 1903 orders are all holds — legal, non-scripted, within the game; noted
  only as prompt-quality colour.

BLOCKING: 0
