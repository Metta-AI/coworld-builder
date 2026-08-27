blocking: 0

# verify verdict — lux-ai (phase 60)

Head evidence: cow_85ac57ce-ce33-44dc-a00f-d74141fdd9fe v0.1.4, league_91cd77d4, div_42529bfd,
round_ee8f3123 / ereq_336aa5ca / replay 117bf12d, viewer-check run 33106609970.
Checklist: `docs/SPEC.md` §Definition of done (read from the file) + `prompts/60-verify.md`.
Reading order declared: in phase 60 VERIFY.md is itself the artifact under adjudication, so it was
read as part of the brief — but **no verdict below rests on its pasted bytes**. Every check was
re-fetched or re-run independently (live API, live page, S3 bytes decoded with the repo's own tool,
`gh run view`, the committed artifacts), and the re-fetches are quoted below.

## Checklist pass (independent, one row per definition-of-done line)

| # | SPEC §Definition-of-done line | My verdict | My evidence (re-fetched/re-read, not VERIFY.md's paste) |
|---|---|---|---|
| 1 | ≥2 rounds `completed` after fillers set | **TRUE** | Live `GET /rounds?league_id=league_91cd77d4…` at judging time: `[{"round_number":3,"status":"pending"},{"round_number":2,"status":"completed","error":null,"completed_at":"2026-08-27T19:01:22Z"},{"round_number":1,"status":"completed","error":null,"completed_at":"2026-08-27T18:44:00Z"}]`. No failed/discarded. `log.md:62` records fillers registered **before** the first trigger (`forester:v4=4269d16d prospector:v4=3613cd05 … BEFORE trigger`); both completions post-date that line's 18:43:11Z timestamp. |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | Live `GET /divisions/div_42529bfd…/leaderboard`: exactly two rows — `1 daveey lux-ai-lumberjack:v4 1030.53 rounds_played=2 wins=2.0`, `2 daveey-1 lux-ai-nightwatch:v4 969.47 rounds_played=2 wins=0.0`. No filler row, no `Baseline` label. |
| 3 | Latest round's episode request completed with replay, participants named | **TRUE** | Live `GET /episode-requests/ereq_336aa5ca…`: `status:"completed"`, `replay_url:"…/replays/117bf12d-a428-47b0-a50c-ba62377cc8f9.replay"`, participants `daveey`/lux-ai-lumberjack:v4 and `daveey-1`/lux-ai-nightwatch:v4, both `is_filler:false`. |
| 4 | Replay bytes: strict UTF-8 JSON, protocol matches, reason complete, champions doing the thing, not all fallbacks | **TRUE** (via the declared substitute; see adjudications A and B) | I fetched the S3 bytes myself (HTTP 200, 252300 bytes, magic `COWLDLUX`), fetched `tools/replay_summary.py` from `Metta-AI/cogame-lux-ai` myself, and ran it: `jq -e` passes strict; `protocol lux-ai/v1`, `reason complete`, `endRule full_time`, `cityTiles [2,0]`, `fallbacks 0`, 72/72 directives `source=="llm"`, 72/72 with non-empty `note`, 360/360 turns. Source constant `src/lux/sim_types.nim:28 ReplayProtocol* = "lux-ai/v1"` matches; the manifest's protocol prose itself declares "Binary `COWLDLUX`. `tools/replay_summary.py` turns it into one strict-UTF-8 JSON object". Directive notes are genuine turn-anchored strategy, not boilerplate. |
| 5 | Hosted log clean (elevated) | **TRUE** | Re-fetched `…/artifacts/logs` with the elevated header myself: HTTP 200, 148558 bytes (byte-identical count to VERIFY.md's), `grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'` → **0** on the raw bytes. No Bedrock-capacity cross-check needed. |
| 6 | Public page: featured match present, iframe src is the static path, never `/client/replay` | **TRUE** | Re-fetched `https://softmax.com/lux-ai` myself (200, 686 KB): SSR payload contains `\"episodeId\":\"aba8f475-…\"`, code `lux-ai.r2.e1`, replayUrl `…117bf12d….replay`; `grep -c '/client/replay'` → **0** in the whole page. The session route's `viewer_url` is `…/v2/coworlds/replays/static/cow_85ac57ce…/sha256%3Ae8483de3…/index.html?replay=…` where the sha equals `STATE.coworld.manifest_sha` exactly — and check 8's CI run **loaded that exact URL and drew a frame**, which is stronger than a string match. |
| 7 | Certification: `Replay liveness: skipped (static replay bundle declared` from the committed release-result.json | **TRUE** | Read the committed `runs/2026-08-27-lux-ai/release-result.json` myself: `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`, `.certify.ok` = `true`. Required substring present verbatim. |
| 8 | Viewer executed: loaded:true, three differing clock readouts, spectator judgment from the rendered thing | **TRUE** (see adjudication C) | `gh run view 33106609970` myself: `conclusion:"success"`, created 19:03:57Z (after the 19:03:54Z dispatch — the find-the-new-run discipline was followed). Committed `viewer-smoke.json`: `loaded:true`, `ms:4048`, `data_replay_loaded:"true"`, `failure:null`, `console_tail:[]`, and three **different** scrub clocks (0% lobby caption, 50% `TURN 198/360 … RED 10 – 4 BLUE`, 100% `TURN 359/360 … RED 2 – 0 BLUE`). I looked at `viewer-smoke.png` myself — see C. |

## Adjudications on the flagged points

### A. Check 4's binary-replay exception — the design note really declares it, and it was run faithfully
`design.md:1090–1117` §"Replay bytes (self-sufficient)" declares the starter's binary `COWLDLUX`
container, `SMOKE_REQUIRE_REPLAY_JSON=0`, and names `tools/replay_summary.py` as "**The phase-60
substitute for SPEC §Definition of done check 4**" with the exact command sequence. Independently,
the released manifest's own protocol prose declares the same substitute. I re-ran the substitute
end-to-end from the released repo's copy of the tool and reproduced the verifier's output field
for field. The substitute is legitimate (the strict-UTF-8 clause exists to prove the bytes are
well-formed and machine-parseable; here they parse strictly under the format's own decoder **and**
rendered in headless chromium), the declaration predates verification, and the precedent
(2026-08-26-atari-cabinet/COWLDCAB) is real. **Faithfully declared, faithfully executed. Not blocking.**

### B. The cityTiles-sum deviation — the verifier's ruling holds
Observed `results.cityTiles [2,0]`, sum 2; `design.md:1115` asks `> 2` ("somebody built something").
Ruling: **TRUE stands; not blocking.** Reasons:
1. The threshold appears in **neither** SPEC §Definition of done check 4 **nor**
   `prompts/60-verify.md` check 4. The checklist is the only source of blocking, and its four
   requirements (strict parse, protocol match, reason complete-or-declared-deadline, non-scripted
   champion decisions that are not all fallbacks) are all met — I verified each independently.
2. The threshold is the design's *proxy* for "somebody built something", and the thing it proxies
   is directly evidenced in the same object: `cityTilesBuilt [12,6]` (18 tiles built),
   `unitsBuilt [31,7]`, `resourcesMined [[11573,0,0],[5055,0,0]]`; each seat starts with 1 tile and
   RED ended with 2, so even the *net* end-state shows building. The end-state sum is small because
   night attrition destroyed 16 of the 18 built tiles (`cityTilesLost [10,6]`), not because nothing
   was built — the directive log narrates exactly that arc (RED at 10 tiles by turn 190, the
   turn-200 "EMERGENCY", BLUE's turn-340 "0 cities … Survive to 360").
3. The verifier recorded the deviation openly and escalated it rather than hiding or rounding it.
   That is the correct handling of a design-note self-check that fails while the definition of
   done passes.
The residue is a proxy miscalibrated by one tile plus a balance observation — phase-30/design
material, not a definition-of-done falsification. Recorded below as non-blocking.

### C. Check 8's screenshot — it is the starter's chrome, and the clocks genuinely differ
I examined `viewer-smoke.png` (1280×800) directly. It shows: the centre headline clock
`TURN 359 / 360 · NIGHT 10/10` with `CYCLE 9 OF 9 · DIRECTIVE 36/36 · RED 2 – 0 BLUE` beneath;
scorebug flanking it (`daveey / RED-ALPHA / 2 units · 623 fuel · 34 research / 2 CITY TILES` left,
`daveey-1 / BLUE-ALPHA / 2 units · 0 fuel · 47 research / 0 CITY TILES` right) with the
red/blue research bar between; a rendered 16×16 night board with real terrain art (rock formations,
two mirror-symmetric wood clusters, two gold-outlined red city tiles, four unit chips with cargo
pips); two directive bubbles quoting the turn-350 notes verbatim from the replay JSON; the
**starter transport strip** (restart / step-back / pause / +5s / play / loop / fast-forward,
`spoilers` toggle, `359 / 359` counter, `1× 2× 4× 8× 16×` speed buttons); and the **scrubber with
the CITY TILES momentum area chart and beat ticks**. This is the coworld-ctf broadcast chrome with
a game-specific block appended — not the cogame-gridlock rewrite failure. The three scrub clocks
differ and the on-screen numbers reconcile with `results` (units [2,2], research [34,47],
cityTiles [2,0]). The 0% readout is the lobby caption `-- WAITING FOR PLAYERS` rather than
`TURN 0/360` — the readouts still differ, which is what the check requires; the lobby-frame left
edge is a polish note. The **endcard** is not visible (capture is at turn 359 of 360, one frame
short), so it is unconfirmed from this screenshot; it is not a requirement of definition-of-done
line 8 (loaded / advances / judgment paragraph), and everything that *is* required is evidenced.

## Refuted
None. No VERIFY.md verdict was found to be wrong or overstated; every pasted evidence block I
re-fetched reproduced (rounds, leaderboard, episode request, replay bytes and their decode,
log bytes and grep, page SSR, session viewer_url, release-result.json, CI run conclusion).

## Verifier report audit
| check | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | TRUE, rounds 1+2 completed after fillers 18:43:11Z | live rounds list: both completed, error null | yes |
| 2 | TRUE, two rows, no fillers | live leaderboard: identical rows | yes |
| 3 | TRUE, ereq completed, replay_url, champions seated | live episode request: identical | yes |
| 4 | TRUE with recorded deviation | re-ran substitute from repo tool: identical output; deviation adjudicated not-blocking (B) | yes |
| 5 | TRUE, CLEAN | re-fetched logs (148558 bytes), raw grep 0 | yes |
| 6 | TRUE, SSR + session route, static path | re-fetched page: featured `lux-ai.r2.e1`, zero `/client/replay`; sha = manifest_sha | yes |
| 7 | TRUE from committed artifact | read committed file: substring verbatim | yes |
| 8 | TRUE, loaded + 3 differing clocks | `gh run view`: success; json + png examined directly | yes |

## Non-blocking observations (for the coordinator / phase-30 backlog)
- Design-note proxy `cityTiles sum > 2` (design.md:1115) missed by one tile at end-state [2,0];
  night attrition destroyed 16/18 built tiles and BLUE finished at 0. Balance/threshold-calibration
  note, not a done-ness defect.
- 0% scrub lands on the lobby frame (`-- WAITING FOR PLAYERS`) instead of turn 0.
- `feed_lines: 0` from the DOM probe while directive bubbles are plainly painted — the commentary
  lives outside the probed element.
- Endcard not confirmable from a turn-359/360 capture.
- Round 1 `created_at` 18:42:06Z precedes the 18:43:11Z batch log line that records the
  fillers-before-trigger sequence; the line is a post-hoc batch summary and its ordering claim
  ("BEFORE trigger") plus both rounds' champion-only entrants make the check's intent verifiable,
  but per-action timestamps in log.md would have made this trivially checkable.

## Standing blocking findings
None. All eight definition-of-done lines verified from my own re-fetches or the committed
artifacts; nothing was unverifiable.

BLOCKING: 0
