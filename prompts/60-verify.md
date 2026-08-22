# Phase 60 — Verify

Purpose: prove the definition of done by fetching evidence; never by assuming.
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
/usr/bin/curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[.entries[]|select(.status=="completed")]|length'
```
Must be ≥ 2, and those rounds' `round_number`s must be **after** the round in which fillers were
registered (`log.md` records it). Rounds with `status` `failed`/`discarded` do not count; record
their `error` verbatim.

**2. Both champions ranked.**
```bash
/usr/bin/curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
(bare list, not `.entries`). Require rows for `daveey` **and** `daveey-1`, each `rounds_played ≥ 1`;
fillers absent or `policy_label` starting `Baseline`.

**3. Latest round's episode request completed with a replay.**
```bash
R=$(/usr/bin/curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
EREQ=$(/usr/bin/curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
    | jq -r '.entries[0].id')      # NOT division_id= (500); league_id=/coworld_name= are ignored
/usr/bin/curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
Require `status == "completed"`, a non-null `replay_url`, and `participants` naming `daveey` and
`daveey-1` (fillers as `Baseline (N)`).

**4. Replay bytes are valid and show the game.**
```bash
/usr/bin/curl -sSL "$(… .replay_url)" -o /tmp/ep.replay
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
/usr/bin/curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" \
 | grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' || echo CLEAN
```
Must be `CLEAN`. `LLM provider is unavailable` is a platform-wide Bedrock outage if another LLM
coworld's latest log shows it too — check one, document it, and treat it as a wait, not a defect.
`cut off at max_tokens` → raise `maxOutputTokens` (900, not 400) and re-release.

**6. The public page uses the static replay path.**
```bash
/usr/bin/curl -sS "https://softmax.com/<slug>" | grep -o '<iframe[^>]*src="[^"]*"'
```
The iframe `src` must be
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` — **never** a
`/client/replay` pod URL. A featured match must be present (absence = fewer than two ranked
players).

**7. Certification declared the static bundle.**
```bash
jq -r '.certify.replay_liveness' /tmp/rr/release-result.json
```
Must contain `Replay liveness: skipped (static replay bundle declared`.

**8. Spectator judgment.** The sandbox has no screen, so read the static viewer's **DOM** at three
scrub points (start, middle, end) and quote the readouts:
```bash
IFRAME='https://softmax.com/api/observatory/v2/coworlds/replays/static/'$COW'/<sha>/index.html?replay=<s3 url>'
# fetch the bundle's index + its derived state; report clock, scorebug plates, and feed lines
```
Write a short paragraph: is it legible, and does it show the game? Include the three sets of
readouts as evidence. Confirm the scorebug plates show full player names (not "…") at 360 px.

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
- STATE: `verify.rounds[]`, `verify.replay`, `verify.iframe_static`, `phase: "70"`, `heartbeat_at`.
- `log.md`: one line per poll and per check with its verdict.
- Asana: complete the phase-60 subtask; comment with the leaderboard rows and the replay URL.

## Retry budget

3 attempts per failing check, each a different approach (re-poll, different filter, different
round). A check that stays false after 3 attempts, or the 75-minute bound expiring →
`prompts/90-blocked.md` naming the check number and quoting the evidence.
