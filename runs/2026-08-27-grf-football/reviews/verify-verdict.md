blocking: 0

# Phase-60 verdict — grf-football (2026-08-27)

Judge: fresh context. Read order: SPEC §Definition of done → prompts/60-verify.md →
VERIFY.md → viewer-check/{viewer-smoke.json,viewer-smoke.png} → STATE.json. This is a phase-60
adjudication, so VERIFY.md itself is the object under review; every load-bearing claim in it was
**re-fetched or re-derived independently** before ruling — nothing below rests on the verifier's
paste alone.

Head facts verified: league `league_973d55af-…`, division `div_8915b808-…`,
cow `cow_60738189-…` v0.1.2, manifest sha `sha256:cc1320b5…a36cd69`, champions
`grf-football-tiki:v3` (daveey) / `grf-football-counter:v3` (daveey-1), fillers zonal:v3 +
gegenpress:v3 (confirmed live via `GET /leagues/$L/filler-policies`, elevated).

## Item-by-item (each independently re-fetched, 2026-08-27T~13Z)

| # | SPEC item | my fetch | verdict |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | `/rounds?league_id=` (bare array): round 2 `completed` 10:59:25Z, round 3 `completed` 11:14:28Z; round 1 `failed` ("Temporal RoundWorkflow failed before settling the round"), excluded; a round 4 now `pending`, irrelevant | **TRUE** (see caveat A) |
| 2 | both champions ranked, fillers absent/Baseline | `/divisions/$D/leaderboard`: exactly 2 rows — daveey-1 (counter:v3, MMR 1030.53, rounds_played 2, wins 2) and daveey (tiki:v3, 969.47, rounds_played 2, wins 0); no filler rows | **TRUE** (see adjudication) |
| 3 | latest round's ereq completed + replay + participants | `ereq_afd7c2ec-…`: `completed`, replay_url `…7ec2e9c2-….replay`, positions 0/1 = tiki:v3/daveey and counter:v3/daveey-1 `is_filler:false`, positions 2–7 the two fillers `is_filler:true` | **TRUE** |
| 4 | replay bytes valid, protocol, reason, champions doing the thing | fetched the bytes myself (200, 474783 B), decoded with the repo's `tools/replay_summary.py` @ head 6c9962d, `jq -e` strict-parses; `reason:complete`, `endRule:full_time`; seats 0 and 1 **24/24 `source:"llm"`**, `fallbacks:0`, `llmTurns [24,24,0,…]`, notes situation-specific football | **TRUE** (see caveats B, C) |
| 5 | hosted log clean | re-fetched `…/artifacts/logs` elevated (200, 103792 B), decoded the `b'…'` reprs myself, grep over decoded text: **0 hits** for `falling back\|LLM provider is unavailable\|cut off at max_tokens\|rejected`; 48 `bedrock_sidecar_call`, 48 completes all `ok:true`/200 | **TRUE** (see adjudication — the check is structurally blind to the demotion) |
| 6 | public page static replay path + featured match | raw HTML has no iframe (client-rendered — the prompt's documented fallback applies); SSR payload `playlist[0]` = `grf-football.r3.e1` matchup daveey-1 vs daveey with the round-3 replayUrl (re-extracted from a fresh page fetch); `POST /coworlds/replays/session` returns `viewer_url` on the **static** route with sha = `STATE.coworld.manifest_sha`, `ready:true`; no `/client/replay` anywhere | **TRUE** |
| 7 | certification declared static bundle | committed `runs/…/release-result.json` in the tree: `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`; `.certify.ok`/`.ok` both true | **TRUE** |
| 8 | viewer executed + spectator judgment | run 33066666879 re-checked via gh: `completed/success`; committed viewer-smoke.json: `loaded:true` (1839 ms, `data_replay_loaded:"true"`, `failure:null`); three scrub clocks all differ (`4:00 KICKOFF` → `1:53 2ND HALF · TURN 13/24` → `FINAL GAME OVER FULL TIME`); I viewed viewer-smoke.png myself: endcard "DAVEEY-1 + BASELINE WINS 0-2 / FULL TIME" over a drawn pitch, per-team box scores with BLUE-6 = 2 goals reconciling with `results.goals[7]==2`, `teamGoals [0,2]`, possession 31/68 % ≈ `teamPossessionTicks [1056,2296]`; chrome is the starter's (transport strip, speed chips, momentum graph, scorebug, endcard) | **TRUE** |

The judgment paragraph in VERIFY.md is fair to the screenshot: the picture is legible, it is
football, and it reconciles with the replay record. Not the gridlock failure mode.

## Adjudicated finding — seat-registration race (round 2 champion silently demoted)

**Verified true, from the bytes, not from the verifier's word.** I fetched round 2's replay
(`67c06162-…`, 490412 B) and decoded it myself: `results.llmTurns == [24,0,0,0,0,0,0,0]`; seat 1
(BLUE-10 = daveey-1's `grf-football-counter:v3`) has **24/24 `source:"scripted"`, `latency_ms:0`,
note "hold the zone, support the ball, press when it is close"** — the zonal default. Register
records: round 2 `policyKinds` = `["llm",null,null,"scripted","scripted",null,null,"scripted"]`
(4/8 recorded; champion seat 1 **null**); round 3 = 5/8 with filler seat 7 null (assigned
gegenpress, played zonal). Round 2's hosted log: 24 `bedrock_sidecar_call` (one champion, not
two), zero pattern hits, and `player connected: daveey-1` / `player joined: daveey-1 as BLUE-10`
present — so the loss is after join, exactly as VERIFY.md diagnoses. Round 2's leaderboard result
(a daveey-1 win) was therefore earned by the server-default zonal script playing under the
champion's name.

**Ruling: NON-BLOCKING against the definition of done.** On the checklist's terms:

- Item 1 counts rounds by `status` and timing only; round 2 is `completed` and completed after
  the fillers were set. Nothing in the item speaks to how a counted round was played.
- Item 2 requires rows for daveey and daveey-1 with `rounds_played ≥ 1` and fillers
  absent/Baseline. Met literally. The item does not warrant the provenance of the MMR.
- Items 3–5 — the only items that examine episode *content* — are explicitly scoped to the
  **latest** round's episode request ("Latest round's episode request", SPEC item 3; items 4–5
  operate on that ereq's replay and log). Round 3's champions ran 24/24 LLM with 0 fallbacks,
  verified from the bytes. The affected round is not the object of any content check.
- No other item touches round 2.

So every check's own terms are met on evidence I fetched myself, and I cannot tie the race to a
named definition-of-done item without rewriting the item. It does not block done-ness.

**It is, however, a real defect and must be recorded — for learnings and as a repo issue:**

1. **The defect**: seat registration is fire-and-forget; when the register record is lost after
   join (4/8 recorded in round 2, 5/8 in round 3 — nondeterministic), the seat silently plays the
   server-default `zonal` script under the assigned policy's name. A champion LLM policy was
   demoted to a baseline for an entire counted episode with **zero observable signal**: no
   `fallback` record, no log line (which is precisely why check 5 was clean), `latency_ms:0` the
   only tell.
2. **Ladder integrity**: daveey-1's 2-0 record includes one win played by zonal. If the featured
   episode had been round 2's instead of round 3's, spectators would watch a mislabeled baseline
   presented as the champion.
3. **Verification blind spot**: checks 4/5 examine only the latest round, so this class of defect
   passes verification whenever it misses the final round. Both observed episodes had ≥1 demoted
   seat (round 2: 4 seats incl. a champion; round 3: 3 seats incl. a filler on the wrong script).
4. **Fix direction** (repo): ack/retry registration, or refuse to start the match until all 8
   register records are recorded; at minimum, log loudly when a seat assigned an LLM policy plays
   scripted — that single log line would make check 5 catch this forever after.

## Smaller notes — classification

- **Momentum graph labelled `LIVES LEAD`** (visible bottom-left of viewer-smoke.png; un-retargeted
  coworld-ctf label in a football coworld). **Advisory.** Item 8 requires loaded + advancing +
  a legible judgment + the starter's chrome; all hold. A stale strip label is a legibility polish
  finding of the kind 60-verify.md routes to phase 30, not a FALSE item 8. Log as a follow-up.
- **Viewer timeline 6120 vs replay `tickCount` 6420** (last ~300 recorded ticks unreachable on the
  scrubber; 6120 = maxTicks 5760 + gameOverTicks 360). **Advisory.** No item requires scrubber
  reach of every recorded tick; the 100 % readout is `FINAL GAME OVER FULL TIME` and the endcard
  renders. Repo note: server records ~300 ticks past the viewer's declared end — trim or extend.
- **`feed_lines: 0`**. **Advisory.** Read at the first-frame moment (clock `4:00 KICKOFF`), before
  any event exists, so it is not evidence of a broken feed — but nothing in this run's evidence
  shows the feed *populated* either. Item 8's terms (loaded, advancing clocks, judgment) don't
  require feed_lines > 0, and the scorebug/endcard prove "who is winning and why". Recommend one
  targeted mid-match feed readout in a future viewer-smoke.

## Caveats found in my own pass (none blocking)

- **A. Check-1 narrative inaccuracy in VERIFY.md**: it says fillers (set ~10:52Z) were "before
  round 2 was created at 10:51:56Z" — literally false; round 2's *row* predates the registration
  by ~seconds. Immaterial: the SPEC item's condition is rounds **completed** after fillers were
  set (10:59:25Z and 11:14:28Z both are), and both counted episodes' participant lists contain
  the fillers `is_filler:true`, proving they were in place at matchmaking. Also, round 1's error
  string is the playbook §6 documented symptom of a trigger issued *before* fillers exist — the
  "fillers before first trigger-round" design pin was in fact violated by seconds in phase 50 and
  cost round 1; worth a learnings line, but the pin is a phase-50 process rule, not a
  definition-of-done item, and the failed round is excluded from the count as the checklist
  directs.
- **B. Replay format vs SPEC letter**: SPEC item 4 says "valid UTF-8 JSON"; the bytes are the
  starter's binary format (`COWLDFTB…`). The accepted design note (design.md §"Replay bytes
  (self-sufficient)", lines 821–843) explicitly declares the binary format and rewrites check 4's
  procedure through `tools/replay_summary.py` + `jq -e` — the exact procedure the verifier ran and
  I reran. This deviation was adjudicated upstream at phases 10/30; ruling on it now would be
  re-litigating the accepted design. TRUE stands; noted for the record.
- **C. `protocol` is a constant** in `replay_summary.py` (the verifier disclosed this honestly);
  the identity actually carried in the bytes is `gameName grf-football` + `gameVersion 6`, which
  matches the manifest's game. Acceptable under B; a future format rev could embed the protocol
  string.

## Fixer/verifier report audit

| claim in VERIFY.md | I verified | agrees |
|---|---|---|
| rounds 2,3 completed, round 1 failed w/ quoted error | re-fetched `/rounds` | yes |
| leaderboard 2 rows, both champions, rounds_played 2 | re-fetched | yes |
| ereq_afd7c2ec completed, replay_url, 8 participants | re-fetched | yes |
| replay: llm 24/24 both champions, 0 fallbacks, complete/full_time | re-fetched bytes + re-decoded | yes |
| log CLEAN, 48 bedrock calls all ok | re-fetched + re-decoded + re-grepped | yes |
| SSR playlist featured match, session API static viewer_url | re-fetched both | yes |
| release-result.json liveness string | read committed file | yes |
| viewer-check 33066666879 success, loaded:true, 3 differing clocks | gh run view + committed json + viewed png | yes |
| round-2 demotion forensics (llmTurns [24,0,…], 4/8+5/8 registers, 24 calls, join present) | re-derived all four from bytes/logs | yes |
| "fillers before round 2 was created" | round 2 created_at 10:51:56Z precedes ~10:52Z registration | **no — immaterial (caveat A)** |

## Verdict

All eight definition-of-done items are TRUE on independently fetched evidence. The
seat-registration race is real, serious, and non-blocking on the checklist's terms; it goes to
learnings and a repo issue, not to a re-verify. The three smaller notes are advisory.

BLOCKING: 0
