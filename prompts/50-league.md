# Phase 50 — League

Purpose: seed the league, seat two ranked champions and the fillers, unpause, and trigger a round.
Owner: coordinator. All HTTPS except champion submission, which is a CI dispatch.

## Inputs

- `STATE.slug`, `STATE.coworld.cow_id`, `STATE.policies.*` (names and `policy_version_id`s from
  `release-result.json`).
- `playbooks/observatory-api.md` — every body below is quoted from it.

## Procedure

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true" -H 'content-type: application/json')
```

1. **Seed**
   ```bash
   /usr/bin/curl -sS -X POST "$BASE/coworld-league-seeds" "${AUTH[@]}" "${ELEV[@]}" -d '{
     "coworld_name":"<slug>","league_key":"default","league_name":"<Slug>",
     "template":"commissioner_driven","enabled":true,
     "overrides":{"commissioner_key":"platform"}}'
   ```
2. **League id** — fetch and match client-side on `game.coworld_name`:
   ```bash
   L=$(/usr/bin/curl -sS "$BASE/leagues?limit=200" "${AUTH[@]}" \
       | jq -r '.entries[]|select(.game.coworld_name=="<slug>")|.id')
   ```
3. **Division**
   ```bash
   D=$(/usr/bin/curl -sS -X PUT "$BASE/leagues/$L/divisions" "${AUTH[@]}" "${ELEV[@]}" \
       -d '{"divisions":[{"name":"Competition","level":1,"type":"competition","hidden":false}]}' \
       | jq -r '.divisions[0].id')
   ```
4. **Settings**
   ```bash
   /usr/bin/curl -sS -X POST "$BASE/leagues/$L/settings" "${AUTH[@]}" "${ELEV[@]}" -d "{
     \"ladder\":{\"enabled\":true,
       \"scheduler\":{\"strategy\":\"round_robin\",\"insufficient_players\":\"filler_policy\"},
       \"fulfillment\":{\"allowed_failures\":0.0,\"retry_times\":2},
       \"ranking\":{\"algorithm\":\"elo\",\"initial_rating\":1000.0,\"k_factor\":32.0,
                    \"round_scoring_rule\":\"mean\"},
       \"divisions\":[{\"division_id\":\"$D\",\"name\":\"Competition\"}]},
     \"round_interval_minutes\":15}"
   ```
5. **Champion #1 — daveey** (`ply_44ae9048-3242-4654-881f-6d9d43347fa3`):
   ```bash
   gh workflow run coworld-submit.yml -R Metta-AI/cogame-<slug> --ref main \
     -f player_id=ply_44ae9048-3242-4654-881f-6d9d43347fa3 \
     -f policy='<slug>-forecaster:v1' -f league_id="$L"
   ```
   Watch the run, download the `submit-result` artifact, require `ok: true`.
6. **Champion #2 — daveey-1** (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`): its policy version must
   have been **uploaded while daveey-1 was the active player** — a version uploaded as daveey is
   owned by daveey and submitting it as daveey-1 409s "already assigned to player". Phase 40 mints
   it by putting `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` on that policy entry in the
   `policies` JSON. If it did not, re-dispatch `coworld-release.yml` with a bumped version and that
   field set, then submit:
   ```bash
   gh workflow run coworld-submit.yml -R Metta-AI/cogame-<slug> --ref main \
     -f player_id=ply_bac48eb1-662e-44f8-973d-f3e016dccf5d \
     -f policy='<slug>-steady-llm:v1' -f league_id="$L"
   ```
   **Two ranked players are REQUIRED** — with fewer, softmax.com/<slug> shows "No featured match
   yet".
7. **Fillers — BEFORE any trigger-round.** Use the `policy_version_id` UUIDs of the versions that
   are **not** either champion:
   ```bash
   /usr/bin/curl -sS -X POST "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" \
     -d '{"policy_version_ids":["<uuid-basestock>","<uuid-mirror>"]}'
   ```
   Any seat whose version is in this list is renamed "Baseline (N)" — including a scored champion.
   Verify the response lists exactly the two filler UUIDs and neither champion's.
8. **Unpause, then trigger**
   ```bash
   /usr/bin/curl -sS -X POST "$BASE/leagues/$L/rounds-paused" "${AUTH[@]}" "${ELEV[@]}" -d '{"paused":false}'
   /usr/bin/curl -sS -X POST "$BASE/leagues/$L/trigger-round"  "${AUTH[@]}" "${ELEV[@]}" -d '{}'
   ```
9. Confirm the round exists and is not instantly failed:
   ```bash
   /usr/bin/curl -sS "$BASE/rounds?league_id=$L&limit=5" "${AUTH[@]}" \
     | jq -r '.entries[]|[.round_number,.status,(.error//"-")]|@tsv'
   ```
   `Temporal RoundWorkflow failed before settling the round` = fillers were not set before the
   trigger. Fix step 7, then trigger again.

## Exit criterion

`GET /divisions/$D/leaderboard` (or the round's `round_config.entrant_attributions`) shows **both**
champions as entrants, filler policy ids registered and distinct from the champions', rounds
unpaused, and at least one round in `pending`/`running`/`completed` — not `failed`.

## Writes

- STATE: `league.id`, `league.division`, `policies.fillers[]` UUIDs, `phase: "60"`, `heartbeat_at`.
- `log.md`: one line per API call with the HTTP status and the id returned.
- Asana: complete the phase-50 subtask; comment with `league_id`, `division_id`, and both champion
  policy labels.

## Retry budget

3 attempts per step, each varying the approach (re-fetch ids, re-issue with elevated header,
re-check the filler list). Two failed triggers with fillers verifiably set → `prompts/90-blocked.md`
quoting the round's `error` field verbatim.
