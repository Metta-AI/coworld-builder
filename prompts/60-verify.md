# Phase 60 — Verify

Purpose: prove the definition of done by fetching evidence; never by assuming. Check 8 is the
one exception to "fetch only": the viewer is opened in a real browser, in CI, because a viewer
whose files all fetch 200 can still never draw a frame (cogame-lantern, 2026-08-23).
Owner: verifier sub-agent, adjudicated by the judge. Output is `runs/<run>/VERIFY.md`.

## Inputs

- `STATE.league.id` (`$L`), `STATE.league.division` (`$D`), `STATE.coworld.cow_id` (`$COW`),
  `STATE.slug`, `STATE.coworld.version`.
- `playbooks/observatory-api.md`.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

## The eight checks (SPEC §Definition of done, as commands)

**1. ≥2 completed rounds after the fillers were set.**
```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[.entries[]|select(.status=="completed")]|length'
```
Must be ≥ 2, and those rounds' `round_number`s must be **after** the round in which fillers were
registered (`log.md` records it). Rounds with `status` `failed`/`discarded` do not count; record
their `error` verbatim.

**2. Both champions ranked.**
```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
(bare list, not `.entries`). Require rows for `daveey` **and** `daveey-1`, each `rounds_played ≥ 1`;
fillers absent or `policy_label` starting `Baseline`.

**3. Latest round's episode request completed with a replay.**
```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
EREQ=$(curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
    | jq -r '.entries[0].id')      # NOT division_id= (500); league_id=/coworld_name= are ignored
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
Require `status == "completed"`, a non-null `replay_url`, and `participants` naming `daveey` and
`daveey-1` (fillers as `Baseline (N)`).

**4. Replay bytes are valid and show the game.**
```bash
curl -sSL "$(… .replay_url)" -o /tmp/ep.replay
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"   # strict parser, not a browser
jq -r '.protocol, .results.reason' /tmp/ep.replay
jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep.replay
jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay
```
Require: valid UTF-8 JSON under a strict parser; `protocol` matches the manifest;
`results.reason == "complete"` (or a `deadline` the design note declares acceptable); champion
seats' decisions are non-scripted with non-trivial content — **not all fallbacks** (fallback count
must be a small minority of decisions).

**5. Hosted game log is clean.**
```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" \
 | grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' || echo CLEAN
```
Must be `CLEAN`. `LLM provider is unavailable` is a platform-wide Bedrock **capacity** symptom,
not a defect in this coworld, if another LLM coworld's latest log shows it too **or** another run
in flight is hitting it at the same time (runs are parallel and Bedrock capacity is the one
resource they share — SPEC §Parallelism and per-run isolation). Check one, document which, and
**wait**: keep polling inside the 75-minute bound below rather than going Blocked. Only when that
bound expires is it an outage for phase 90. The operator's throttle is `max_parallel_runs` in
`fleet/cloud.md` §Parallelism.
`cut off at max_tokens` → raise `maxOutputTokens` (900, not 400) and re-release.

**6. The public page uses the static replay path.**
```bash
curl -sS "https://softmax.com/<slug>" | grep -o '<iframe[^>]*src="[^"]*"'
```
If that grep finds **nothing**, do not record a false negative: the page may be client-rendered,
in which case the iframe exists only after JS runs and there is no browser here. Fall back to the
coworld detail API, which is what the page reads (see `playbooks/observatory-api.md`
§Featured match / replay route):
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '.entries[]|select(.name=="<slug>")|{id,canonical,replay_viewer,featured_match}'
```
Record in VERIFY.md **which** of the two sources you used. The iframe `src` must be
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` — **never** a
`/client/replay` pod URL. A featured match must be present (absence = fewer than two ranked
players).

**7. Certification declared the static bundle.**
The evidence is `runs/<run>/release-result.json` — the artifact phase 40 downloaded and
**committed** (`prompts/40-release.md` §Writes). Read the committed copy, never `/tmp`: phase 40
usually ran in an earlier heartbeat and that sandbox's `/tmp` is gone.
```bash
jq -r '.certify.replay_liveness' runs/<run>/release-result.json
```
If the file is missing (a run whose phase 40 predates this rule), re-download it from the release
run id STATE recorded, then commit it — do **not** mark the check NOT FETCHED without trying:
```bash
RR=$(jq -r '.coworld.release_run_id' runs/<run>/STATE.json)
REPO=$(jq -r '.repo' runs/<run>/STATE.json)          # Metta-AI/cogame-<slug>
gh run download "$RR" -R "$REPO" -n release-result -D "runs/<run>"   # lands as release-result.json
jq -r '.certify.replay_liveness' runs/<run>/release-result.json
```
Must contain `Replay liveness: skipped (static replay bundle declared`. Paste the `jq` output and
say which of the two sources you read it from.

**8. Spectator judgment — the viewer is EXECUTED, then judged.** The sandbox has no screen and
no headless browser, but GitHub Actions does. Do not fetch assets and infer: dispatch
`viewer-check.yml` in this repo, which opens the live iframe `src` in headless chromium and
reports whether a frame was ever drawn.

*(a) Dispatch the load test against the iframe `src` from check 6.*
```bash
SRC='<the full iframe src from check 6, including ?replay=>'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# find-the-new-run: the dispatch API returns no run id, so poll for a run created
# after the dispatch instead of grabbing "the latest", which races other runs.
sleep 8
RUN=$(gh run list -R Metta-AI/coworld-builder -w viewer-check.yml \
      --json databaseId,createdAt,status -L 10 \
      | jq -r 'sort_by(.createdAt)|reverse|.[0].databaseId')
gh run watch "$RUN" -R Metta-AI/coworld-builder --exit-status || true   # a red run is DATA, not an abort
mkdir -p runs/<run>/viewer-check
gh run download "$RUN" -R Metta-AI/coworld-builder -n viewer-check -D runs/<run>/viewer-check
```
Commit `runs/<run>/viewer-check/` (the png and the json) with VERIFY.md — it is this run's only
rendered evidence and the sandbox that produced it is gone by the next heartbeat.

*(b) Paste the readouts into VERIFY.md.* From `runs/<run>/viewer-check/viewer-smoke.json`:
```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/<run>/viewer-check/viewer-smoke.json
jq -c '.signals' runs/<run>/viewer-check/viewer-smoke.json
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/<run>/viewer-check/viewer-smoke.json
jq -r '.failure // "no failure"' runs/<run>/viewer-check/viewer-smoke.json
```
Paste the JSON line verbatim and the **three clock readouts** (0 %, 50 %, 100 %) as a table.

**Item 8 is TRUE only if both hold:**
1. `loaded: true` — the viewer drew a frame and said so, via `data-replay-loaded="true"` or the
   `coworld-replay` bridge's `ready`. `loaded: false` is check 8 FALSE, full stop: a viewer that
   never renders is not a spectator experience, whatever the asset table says. cogame-lantern
   (2026-08-23) had every asset 200 and `tell("ready")` in the JS and still hung forever on
   "Loading replay…" — that is precisely what this check now catches.
2. The **three clock readouts differ**. A replay that renders one frame and never advances is a
   failure, not a pass. If the shell exposes no `#scrub` the json says so (`"(no #scrub…)"`); say
   that in VERIFY.md and judge motion from the screenshot plus the replay JSON instead — an
   absent scrubber is a legibility finding for phase 30, not a licence to skip the question.

*(c) The replay JSON — what the viewer was asked to draw.* From `/tmp/ep.replay` (check 4), so
the readouts can be reconciled against the recorded episode:
```bash
jq -r '.events[]|[.tick,.seat,.type,(.summary//.say//.action//"")]|@tsv' /tmp/ep.replay | head -40
jq -r '.events[]|[.tick,.seat,.type,(.summary//.say//.action//"")]|@tsv' /tmp/ep.replay | tail -20
jq -r '.results' /tmp/ep.replay
```

**Write the spectator-judgment paragraph** — is it legible, and does it show the game? Its
evidence is now the rendered thing: `viewer-smoke.png` (what a spectator sees), the three clock
readouts (that it advances), the scorebug and feed-line counts (that it says who is winning and
why), reconciled against the replay events above. Say plainly if the picture is empty, static,
or unreadable. **You may describe the screenshot** — for the first time there is one; what you
may still not do is claim a DOM readout you did not download. Also say whether the screenshot
**looks like the starter's chrome** — the same transport strip, scrubber with momentum graph,
scorebug and endcard as paintbot/raid/hive. A page that renders but looks like a different product
is the cogame-gridlock failure (2026-08-23): a rewrite sharing only the ids. That is a phase-30
item-14 finding; send it back rather than certifying it.

## Waiting

The ladder produces a round every 15 minutes. Poll checks 1 and 3 every 5 minutes, bounded at
**75 minutes** of wall clock. Refresh `heartbeat_at` at every poll. On timeout with fewer than two
completed rounds → `prompts/90-blocked.md`.

## Exit criterion

`runs/<run>/VERIFY.md` contains all eight checks with the **fetched evidence inline** (command,
output excerpt, verdict) and every one is TRUE. The judge re-reads VERIFY.md against SPEC
§Definition of done and returns `BLOCKING: 0`.

## Writes

- `runs/<run>/VERIFY.md`.
- `runs/<run>/viewer-check/` — `viewer-smoke.json` and `viewer-smoke.png` from the dispatched
  `viewer-check.yml` run (committed; the CI sandbox that produced them is gone next heartbeat).
- STATE: `verify.rounds[]`, `verify.replay`, `verify.iframe_static`, `verify.viewer_check_run`,
  `phase: "70"`, `heartbeat_at`.
- `log.md`: one line per poll and per check with its verdict.
- Asana: complete the phase-60 subtask; comment with the leaderboard rows and the replay URL.

## Retry budget

3 attempts per failing check, each a different approach (re-poll, different filter, different
round). A check that stays false after 3 attempts, or the 75-minute bound expiring →
`prompts/90-blocked.md` naming the check number and quoting the evidence.
