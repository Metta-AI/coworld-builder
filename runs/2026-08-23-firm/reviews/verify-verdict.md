blocking: 0

# Phase 60 verdict — firm
Run: 2026-08-23-firm   Checklist: docs/SPEC.md §Definition of done (per prompts/60-verify.md)
Evidence file: runs/2026-08-23-firm/VERIFY.md   Judged: 2026-08-24 (fresh context)
Independent read: I read prompts/60-verify.md and SPEC §Definition of done, then VERIFY.md and
the committed evidence, and re-fetched every fetchable claim myself before writing this. The
burden was on VERIFY.md; my re-fetches were for refutation. None refuted anything.

## Adjudication, check by check

### 1. ≥2 completed rounds after fillers set — TRUE, stands
VERIFY.md pastes the poll trail, the final `GET /rounds` body (rounds 1 and 2 both
`status:"completed"`, `error:null`), the elevated filler-policies read, and round 1's replay
`policyNames` showing the three `Baseline` seats. My re-fetch: `GET /rounds?league_id=league_31edf62a…`
returns rounds 1 and 2 completed (02:57:15Z, 03:12:35Z; a round 3 is `pending`, which does not
count and was not counted). `GET /leagues/…/filler-policies` returns exactly
`4ef7b5b5…=firm-steady` and `c99a2095…=firm-taskmaster` — neither is a champion policy-version
(`bc171418…`/`8250a440…`). I re-fetched round 1's replay
(`…/10851618-157a-4954-ac66-19b6b58707f3.replay`) and confirmed
`policyNames: ["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]`, and round 2's
episode request carries the two filler ids with `is_filler:true`. Both counted rounds were
seated with the fillers; there is no pre-filler round to exclude. The check's substance is
proven functionally, not just from log timestamps (see observation O1).

### 2. Both champions ranked, fillers absent — TRUE, stands
Evidence pasted inline (bare-array leaderboard, both rows quoted in full). My re-fetch of
`GET /divisions/div_ec0a2aaa…/leaderboard` returns exactly the two rows in VERIFY.md:
`1 daveey-1 firm-hand:v1 1001.4695… rounds_played=2`, `2 daveey firm-boss:v1 998.5304…
rounds_played=2`. No filler rows exist.

### 3. Latest round's episode request completed with replay — TRUE, stands
Evidence pasted inline (round id, `ereq_2045780a…`, full participants JSON). My re-fetch:
`status:"completed"`, `replay_url` non-null (the `74f5cf6e…` S3 URL), seats 0/1 are
`firm-boss`/daveey and `firm-hand`/daveey-1 with `is_filler:false`; seats 2–4 are the fillers
with `is_filler:true`.

### 4. Replay bytes valid, protocol matches, shows the game — TRUE, stands
Evidence pasted inline including the jq commands and the kind/scripted breakdowns. My re-fetch
of the replay bytes: `jq -e` parses (strict UTF-8 JSON ok); `protocol == "firm.replay.v1"`;
`results.reason == "complete"`; 16/16 champion-seat decisions (`memo`/`work`, seats 0–1)
`scripted:false` with `say` > 20 chars; 0 events with `fallback==true`. The quoted decision
content (marginal-hour arithmetic vs the $1.50 toil cost, machine condition tracking) is
non-trivial and is this game. On "protocol matches the manifest": VERIFY.md is honest that the
literal id `firm.replay.v1` is declared in the design note while the published manifest names
the sibling `firm.player.v1` and describes the replay event vocabulary in `protocols.global` —
I fetched the live manifest and confirmed `protocols.global` specifies exactly the
`start/shift/memo/work/settle/end` events with their field shapes, which the replay uses
field-for-field, and `results` reconciles with item 3's `participant_scores` number-for-number.
The claim as written is accurate (see observation O2).

### 5. Hosted game log clean — TRUE, stands
Evidence pasted inline (grep, CLEAN, raw-vs-decoded cross-check, container list, verbatim game
head/tail). My re-fetch of `/episode-requests/ereq_2045780a…/artifacts/logs` (elevated header):
37,953 raw bytes, 4 containers (`coworld-init-config`, `bedrock-sidecar`, `game`, `worker`);
grep for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → 0 matches
on the raw bytes AND 0 matches after decoding the python byte-string reprs (37,656 decoded
chars). CLEAN, no exception needed.

### 6. Public page uses the static replay path — TRUE, stands
VERIFY.md documents which source it used (the API the page reads, with the raw-HTML grep shown
coming back empty on a client-rendered shell) — exactly what the prompt requires. My re-fetch:
`https://softmax.com/firm` raw HTML has no iframe but its SSR payload carries
`playlist":[{"episodeId":"9f842ce1…` referencing the same `74f5cf6e…` replay (featured match
present, round 2 episode 1); `POST /coworlds/replays/session` returns
`viewer_url = …/v2/coworlds/replays/static/cow_39c7f43c…/sha256%3A5ddddfc0…/index.html?replay=<s3 url>&v=2`
with `ready:true`, the sha equal to STATE's `manifest_sha`; that URL serves HTTP 200. It is the
static route, not a `/client/replay` pod URL.

### 7. Certification declared the static bundle — TRUE, stands
I read the committed `runs/2026-08-23-firm/release-result.json` myself (committed at dd974eb,
from release run 32684174950 — matching STATE's `release_run_id`): `.certify.replay_liveness`
is `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not
required)"`, and the certify transcript shows 10/10 steps passed. Source stated correctly
(committed copy, not /tmp).

### 8. Viewer executed and judged — TRUE, stands
- Run 32685986524: I re-checked via `gh run view` — `conclusion:"success"`, created
  2026-08-24T03:18:06Z (1 s after the logged dispatch; the find-the-new-run rule was followed).
- Artifacts are committed at ce804bb under `runs/2026-08-23-firm/viewer-check/` (working tree
  clean) — the provenance note's "needs committing" was satisfied before this verdict.
- `viewer-smoke.json` read directly: `loaded:true`, `ms:1339`, bridge `["loading","ready"]`,
  `bridge_ready:true`, `failure:null`. **Part 1 of the TRUE condition holds.**
- The three scrub readouts in the json: `SHIFT 0` / `SHIFT 0 / 8 · WAITING ON 5` /
  `FINAL · PROFIT $2,279.20` — all three differ, and `$2,279.20` equals the replay's
  `results.profit = 2279.2`. **Part 2 holds.**
- The pasted readouts match the committed json byte-for-byte (I diffed the claims against the
  file). The `scorebug:""`/`feed_lines:0` explanation checks out against
  `templates/tools/ci/viewer_smoke.mjs` (its `text()` returns `null` for an absent selector,
  `""` for present-but-empty; the `#feed,.feed,#log` query found no node), and the screenshot
  shows the scorebug fully populated.
- I viewed `viewer-smoke.png` myself: THE FIRM wordmark, clock `FINAL · PROFIT $2,279.20`,
  five-seat scorebug strip, status line, office panel + order board + four machine cards with
  cog sprites, condition bars and speech-bubble reports, the momentum graph with the
  DEMAND SWITCH marker, the tick-marked scrubber (`58 / 58`), and the endcard
  `Ratchet RAN A TIGHT SHOP` whose five rows (pay, units, scores, order) reconcile exactly with
  the replay's `results`. It is the bullwhip/starter chrome (transport strip, scrubber +
  momentum graph, scorebug, endcard) — no cogame-gridlock-style rewrite. The spectator-judgment
  paragraph is present, specific, and consistent with what the png actually shows.

## Refuted
None. Every claim in VERIFY.md that I re-fetched reproduced.

## Non-blocking observations
- O1 [check 1] Phase 50's log.md lines are batch-stamped (lines 45–55 share timestamps; "round
  1 pending" is stamped 02:57:29Z, 14 s after the API's round-1 `completed_at`), so wall-clock
  ordering of filler registration cannot be read from log.md alone. VERIFY.md correctly leaned
  on the functional proof (Baseline seats in round 1's replay; `is_filler:true` participants),
  which I verified. Future runs: stamp phase-50 log lines at action time.
- O2 [check 4] The published manifest nowhere contains the literal string `firm.replay.v1`
  (only `firm.player.v1`); the replay protocol id is pinned by the design note and the
  manifest's `protocols.global` event-vocabulary description. VERIFY.md states this accurately.
  Declaring the replay protocol id in the manifest would make this check mechanical next time.
- O3 [check 8] `feed_lines:0` because the shell has no `#feed`/`.feed`/`#log` element (reports
  render as floor speech bubbles + the « LOG button); `scorebug` empty at the 1,339 ms first
  paint. Both correctly flagged in VERIFY.md as legibility notes, not check failures.
- O4 STATE.json's `verify` block is still the placeholder (`rounds:[]`, `iframe_static:false`)
  and `phase` is still "60" — the phase-60 §Writes STATE update is the coordinator's post-verdict
  step, noted here so it is not forgotten.

BLOCKING: 0
