blocking: 0

# verify verdict — tandem (phase 60)
Run: 2026-08-23-tandem   Checklist: prompts/60-verify.md / docs/SPEC.md §Definition of done
Independent read written before reading VERIFY.md: yes (all eight items re-fetched live,
2026-08-24T01:29–01:34Z, before opening the verifier's report).

## Standing blocking findings

None. All eight definition-of-done items verified TRUE at the current state, independently of
the verifier's pastes.

## Checklist pass (independent — my own fetches, not the verifier's)

| item | status | evidence |
|---|---|---|
| 1. ≥2 completed rounds after fillers | TRUE | `GET /rounds?league_id=$L` live: rounds 2,3,4 **and now 5** `status:"completed"`; round 1 `failed` ("Temporal RoundWorkflow failed before settling the round.", raced the unpause — log.md:56–58 shows fillers registered before the first trigger). Even discounting the empty round 3, rounds 2/4/5 give ≥2. |
| 2. Both champions ranked, fillers absent | TRUE | `GET /divisions/$D/leaderboard` live: rank 1 `daveey` `tandem-anchor:v1` rounds_played 3; rank 2 `daveey-1` `tandem-feather:v1` rounds_played 3; exactly two rows — no filler rows at all. (VERIFY pasted rounds_played 2; it has since moved to 3 — forward motion, not staleness.) |
| 3. Latest round's ereq completed with replay | TRUE | Round 4 (latest completed at verify time): `ereq_c24a96c8` `status:"completed"`, `replay_url` `…/090b12fd-….replay`, participants `daveey` (tandem-anchor v1) + `daveey-1` (tandem-feather v1), both `is_filler:false`. Round 5's ereq (`ereq_6b611c1f`) is likewise completed with a replay — the property still holds at head. |
| 4. Replay bytes valid and show the game | TRUE | I fetched `090b12fd-….replay` (78 876 B, etag f2aeb3cc…) myself: binary `COWLDTDM` container — the format design.md §"Replay bytes" (l.889–917) declares, with `tools/replay_summary.py` as the declared strict-JSON decode; coworld-builder's own `templates/tools/ci/docker_smoke.sh:31–32` sanctions binary replay formats. Decoded with the repo's tool: `jq -e` ok, `protocol tandem/v1`, `results.reason "complete"` (`endRule out_of_time` — design.md l.374 declares it a legal, scored end), `policyKinds ["llm","llm"]`, both `register` records `kind:"llm"` present in the raw bytes, **100/100 orders `source:"llm"` (50/50 per seat), `fallbacks 0`, `fallbackTurns [0,0]`** (one turn-0 timeout *attempt* whose retry succeeded), `utf8Repairs 0`. Orders carry distinct situational notes/says (doorways, strain in newtons, partner coordination) — non-trivial, non-templated. |
| 5. Hosted game log clean | TRUE | `GET /episode-requests/ereq_c24a96c8/artifacts/logs` (elevated) fetched myself: zero matches for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → CLEAN; all Bedrock sidecar invocations HTTP 200 (haiku model, real calls with token usage). |
| 6. Public page uses the static replay path | TRUE | Raw HTML has no iframe (client-rendered — the documented case). SSR payload `state.playlist[0]` = featured tandem match (now `tandem.r5.e1`; `tandem.r4.e1` at verify time), both ranked players in the matchup. `POST $BASE/coworlds/replays/session` returns `viewer_url` `…/v2/coworlds/replays/static/cow_77d94979-…/sha256%3A92cde…5147f4/index.html?replay=<s3 url>&v=2`, `ready:true` — the static route with `<sha>` = STATE's `manifest_sha`; not `/client/replay`. |
| 7. Certification declared static bundle | TRUE | Committed `runs/2026-08-23-tandem/release-result.json` `.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`. Release run 32676640602 (Metta-AI/cogame-tandem) conclusion `success`, checked via `gh run view`. Coworld `canonical:true` live. |
| 8. Viewer executed and judged | TRUE | Run 32679404498 conclusion `success` (checked via `gh run view`, not accepted from the report). `viewer-smoke.json`: `loaded:true` (`data_replay_loaded:"true"`, `failure:null`, no console errors, first frame 5 067 ms); its `url` is byte-identical to check 6's session `viewer_url`. Three scrub clocks differ: `1:40 TIME LEFT` → `0:49 TIME LEFT` → `FINAL GAME OVER`. I viewed `viewer-smoke.png` myself: it is the ctf-starter shell (scorebug with both player names and strain readouts, transport strip with spoilers toggle and 1×–16× speeds, condition scrubber) over the tandem endcard "OUT OF TIME — 8% of the route · CONDITION 100% · SCORE 0.019 · daveey + daveey-1 · complete/out_of_time", stats `1632 peak N` / `0/3 blame` / `0 drops` — each reconciling with the replay's `strainPeakNewtons[0]=1632`, `blame:[0,3]`, `jointScore 0.018943`, `progress 0.076`. The judgment paragraph in VERIFY.md is present, substantive, matches the picture, and honestly reports the weak play as an in-genre failure-to-coordinate. Evidence committed under `runs/2026-08-23-tandem/viewer-check/`. |

## Refuted / adjudicated

No checks to refute — the verifier reported 8/8 TRUE and my independent pass agrees on all
eight. The two verifier-recorded observations, adjudicated as instructed:

- **(A) Round 3 completed empty** (`ereq_3638b303`: `status:"completed"`, `episode_id:null`,
  `replay_url:null`, artifacts 404 — I confirmed the null replay_url live). **Does not falsify
  any item.** Item 1 is satisfied by rounds 2 and 4 (and now 5) alone; item 3 concerns the
  latest completed round, which produced a real scored episode. A platform dispatch drop,
  correctly recorded rather than excused. Non-blocking.
- **(B) Round 2, champion #2's seat played 100 % scripted** (register never arrived). I
  confirmed from round 2's replay bytes: only one `register` record (seat 0). **Does not
  falsify item 4**, whose SPEC text is judged on the fetched replay — the latest round's
  (round 4) — where I verified from the raw bytes that both champion seats registered
  `kind:"llm"` and played 100/100 LLM-sourced orders with 0 fallback turns. Intermittent,
  did not reproduce, correctly flagged for the coordinator. Non-blocking.

## Verifier report audit

| claim | verifier said | I verified | agrees |
|---|---|---|---|
| Rounds completed | 3 (2,3,4) | 4 now (2,3,4,5); 3 at verify time | yes |
| Fillers before first trigger | log.md:56–58 + live filler-policies | same log lines; round 1 created 00:37:00 after filler registration | yes |
| Leaderboard | 2 rows, rounds_played 2 | 2 rows, rounds_played 3 now | yes (advanced) |
| Round-4 ereq | completed, replay 090b12fd, correct participants | identical live | yes |
| Replay decode | strict JSON, tandem/v1, complete/out_of_time, 100 llm orders, 0 fallbacks | identical from my own fetch + repo decoder | yes |
| **Check-4 `od` header paste** | claimed as round 4's header | **it is round 2's** (`d6032a99`, 73 740 B) — bytes `…260 200 3 1…345 022` match ep2, not ep4 (`…300 377 N 1…% 022`); the `ls -l 78876` line on the same paste *is* round 4's | **no — see observation 1 below** |
| Hosted log CLEAN | 0 matches over decoded 208 608 chars | 0 matches over the raw body too; 200s throughout | yes |
| Featured match + static src | SSR playlist + session endpoint | identical live (playlist now r5) | yes |
| release-result.json liveness line | exact string present | exact string present in committed copy | yes |
| viewer-check run green | 32679404498 | `gh run view`: completed/success | yes |
| Scrub clocks differ | 1:40 / 0:49 / FINAL | same in committed viewer-smoke.json | yes |

## Non-blocking observations

1. **Evidence-hygiene defect in VERIFY.md check 4:** the pasted `od -c` header (lines 188–189)
   is round 2's replay (`d6032a99…`, 73 740 B), pasted under round 4's `curl`/`ls` commands —
   almost certainly a stale `/tmp/ep.replay` paste from the observation-B work. Every
   *substantive* check-4 claim (decode, protocol, results, orders, registers, seed 2146724700)
   is genuinely round 4's — I reproduced all of them from the live object — so the verdict is
   unaffected; but a paste attributed to a command it did not come from is exactly what this
   audit exists to catch. Worth a line in LEARNINGS.
2. **Item 4's "valid UTF-8 JSON" is met via the design-declared decode, not the raw S3 bytes**:
   the replay is the ctf starter's binary `COWLDTDM` container (design.md l.889–917 declares it
   and the `replay_summary.py` substitute; `templates/tools/ci/docker_smoke.sh:31–32` sanctions
   binary replay formats). The verifier disclosed the substitution openly and pasted both the
   raw magic and the decoder run. SPEC §Definition of done item 4's literal wording predates
   binary-replay starters; suggest the SPEC maintainers codify the decoder path.
3. **Gameplay quality:** the champions completed only 7.6 % of the route (jointScore 0.019),
   spending the late game in a leadership standoff. Legal (`complete/out_of_time` is a declared
   scored end), legible, and honestly judged — but a prompt-tuning opportunity, not a defect.
4. `feed_lines: 0` in the smoke DOM (verifier's own flag) — the play-by-play feed is absent or
   hidden at the endcard; a phase-30-style legibility item for a future version, not a
   definition-of-done failure.

BLOCKING: 0
