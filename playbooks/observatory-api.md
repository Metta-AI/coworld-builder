# Observatory v2 API — call shapes that work

Exactly what the Bullwhip run (2026-08-22) used and observed. Copy these; do not re-derive.
Anything marked **BINDING** is a contract another part of this repo must provide.

## Auth and base

All calls use plain `curl` from `$PATH`. Never pin `/usr/bin/curl`: that is a local macOS/zsh
workaround, and the cloud sandbox is Linux where the binary may sit elsewhere.

```bash
BASE=https://softmax.com/api/observatory/v2
# SOFTMAX_TOKEN is a vault credential substituted at egress; it is never printed.
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")     # add on EVERY write, and on artifacts/logs
```

- Reads: `AUTH` only. Writes: `AUTH` + `ELEV`.
- Some endpoints 403 on a bare `Authorization` header — always send `User-Agent` too. A 403 on one
  endpoint after a 200 on another is a header problem, not a permissions problem.
- Probe: `GET $BASE/../whoami` (note: `whoami` sits under `/api/observatory`, not `/v2`).

---

## 1. Seed a league

```bash
curl -sS -X POST "$BASE/coworld-league-seeds" "${AUTH[@]}" "${ELEV[@]}" \
  -H 'content-type: application/json' -d '{
  "coworld_name": "<slug>",
  "league_key": "default",
  "league_name": "<Slug>",
  "template": "commissioner_driven",
  "enabled": true,
  "overrides": {"commissioner_key": "platform"}
}'
```

`commissioner_key: platform` is mandatory; without it the ladder never schedules.

## 2. Find the league id

```bash
curl -sS "$BASE/leagues?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | .[] | select(.game.coworld_name=="<slug>") | .id'
```

Match on **`game.coworld_name`**, not on the league name. `?name=` style filters are unreliable
here — fetch and filter client-side. **`GET /leagues` returns a bare array** (observed 2026-08-22),
and by 2026-08-24 **`/rounds` and `/policy-versions` return bare arrays too** (they used to wrap in
`{entries:…}`) — always handle both shapes: `jq 'if type=="array" then . else .entries end'`.

## 3. Divisions

```bash
curl -sS -X PUT "$BASE/leagues/$L/divisions" "${AUTH[@]}" "${ELEV[@]}" \
  -H 'content-type: application/json' -d '{
  "divisions": [{"name":"Competition","level":1,"type":"competition","hidden":false}]
}'
```

Response: `{"divisions":[{"id":"div_…","name":"Competition","level":1,"type":"competition","hidden":false}]}`
→ `D=$(… | jq -r '.divisions[0].id')`.

## 4. Settings

```bash
curl -sS -X POST "$BASE/leagues/$L/settings" "${AUTH[@]}" "${ELEV[@]}" \
  -H 'content-type: application/json' -d "{
  \"ladder\": {
    \"enabled\": true,
    \"scheduler\": {\"strategy\": \"round_robin\", \"insufficient_players\": \"filler_policy\"},
    \"fulfillment\": {\"allowed_failures\": 0.0, \"retry_times\": 2},
    \"ranking\": {\"algorithm\": \"elo\", \"initial_rating\": 1000.0, \"k_factor\": 32.0,
                  \"round_scoring_rule\": \"mean\"},
    \"divisions\": [{\"division_id\": \"$D\", \"name\": \"Competition\"}]
  },
  \"round_interval_minutes\": 15
}"
```

## 5. Policy versions

```bash
# The name= filter is SILENTLY IGNORED. Fetch, then filter client-side.
curl -sS "$BASE/policy-versions?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | .[]
          | select(.policy_name|startswith("<slug>-"))
          | [.policy_name, .policy_version_id, .player_name] | @tsv'
```

List key: `entries` — **or a bare array** (observed 2026-08-24; use the dual-shape jq above).
Row fields used: **`policy_name`**, **`policy_version_id`**, **`player_name`**.

**This is the only source of policy-version UUIDs.** `release-result.json.policies[]` reports
`policy_version_id: null` for every policy — `coworld upload-policy` prints only
`Upload complete: <name>:vN` and no uuid, so CI cannot pass one back. Take the `<name>:vN` labels
from the release artifact, then resolve them here. Use `player_name` to confirm champion #2's
version is owned by `daveey-1`.

## 6. Filler policies — BEFORE the first trigger-round

```bash
curl -sS -X POST "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" \
  -H 'content-type: application/json' \
  -d '{"policy_version_ids": ["<uuid-1>", "<uuid-2>"]}'
```

Filler version ids must **differ** from the champions' — any seat whose version is in this list is
renamed "Baseline (N)", including a scored champion.

A `trigger-round` issued before any filler exists fails instantly with
`Temporal RoundWorkflow failed before settling the round`.

`GET /leagues/$L/filler-policies` (the read) **403s on bare AUTH**
(`{"detail":"User is not a softmax team member"}`) — it needs
`X-Use-Elevated-Privileges: true` even though it is a read (raid, 2026-08-23).

## 7. Unpause and trigger

```bash
curl -sS -X POST "$BASE/leagues/$L/rounds-paused" "${AUTH[@]}" "${ELEV[@]}" \
  -H 'content-type: application/json' -d '{"paused": false}'

curl -sS -X POST "$BASE/leagues/$L/trigger-round" "${AUTH[@]}" "${ELEV[@]}" \
  -H 'content-type: application/json' -d '{}'
```

## 8. Rounds

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=10" "${AUTH[@]}" | jq .
```

Shape:

```json
{"entries": [
  {"id": "rnd_…", "round_number": 3, "status": "completed", "error": null,
   "round_config": {"entrant_attributions": [ … ]}}
]}
```

`status` ∈ `pending | running | completed | failed | discarded`. On failure read `error` verbatim
— it is the only place the Temporal message appears. `entrant_attributions[]` tells you which
policy versions were actually seated.

## 9. Episode requests

```bash
# WORKS
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"
curl -sS "$BASE/episode-requests?coworld_id=$COW&limit=20" "${AUTH[@]}"

# DOES NOT WORK
# ?division_id=…    -> HTTP 500
# ?league_id=…      -> filter SILENTLY IGNORED (returns unrelated rows)
# ?coworld_name=…   -> filter SILENTLY IGNORED
```

List key: `entries`. Detail:

```bash
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

Fields used: `status`, `replay_url`, `participants` (seat → display name; champions must show
`daveey` / `daveey-1`, fillers `Baseline (N)`), `participant_scores`.

## 10. Artifacts and hosted logs

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs"    "${AUTH[@]}" "${ELEV[@]}"
curl -sS "$BASE/episode-requests/$EREQ/artifacts/results" "${AUTH[@]}" "${ELEV[@]}"
curl -sS "$BASE/episode-requests/$EREQ/artifacts/replay"  "${AUTH[@]}" "${ELEV[@]}"
```

The elevated header is required here even though it is a read. The logs body is python
`b'…'` byte-string reprs under `===== container: <name> =====` headers — **decode before
grepping** (python3 `ast.literal_eval` per repr), or line-based greps badly undercount
(escrow, 2026-08-23). Grep the decoded text for
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected`.

Replay bytes also live at `https://softmax-public.s3.amazonaws.com/replays/<uuid>.replay`
(`replay_url` gives the exact URL). Parse them with a **strict** UTF-8 JSON parser
(`jq -e . < file`) — browsers tolerate invalid UTF-8, strict parsers do not.

## 11. Leaderboard

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

Returns a **bare JSON list** (not `{"entries":…}`). Row fields: `rank`, `player_name`,
`policy_label`, `score`, `rounds_played`, `episode_wins`.

Done requires both `daveey` and `daveey-1` present with `rounds_played >= 1`, and fillers either
absent or labelled `Baseline`.

## 12. Champion submission — no HTTPS route; use `coworld-submit.yml`

There is **no documented Observatory endpoint** for submitting a policy to a league as a given
player; the Bullwhip run did it with the `coworld` CLI locally, and the cloud agent has no CLI.
`templates/coworld-submit.yml` (slug-independent, no placeholders) covers it. It runs:

```bash
softmax player use <player_id>
coworld submit <policy> --league <league_id> --no-open-browser
softmax player unset          # always() step
```

Inputs: `player_id`, `policy` (`<name>:vN`), `league_id`. `concurrency: coworld-submit`,
`cancel-in-progress: false`. Artifact `submit-result` → `submit-result.json`:

```json
{"ok": true, "player_id": "ply_…", "policy": "<slug>-<prompt-name-1>:v1", "league_id": "league_…",
 "exit_code": 0, "output_tail": "…", "error": null}
```

Submission stays in its own workflow — do not fold it into the release workflow.

```bash
gh workflow run coworld-submit.yml -R Metta-AI/cogame-<slug> --ref main \
  -f player_id=ply_44ae9048-3242-4654-881f-6d9d43347fa3 \
  -f policy="$CH1" -f league_id="$L"      # CH1 = STATE.policies.champion1, e.g. bullwhip-steady:v1
```

Champion #1 is the daveey-owned **LLM prompt** policy; champion #2 is the second LLM prompt policy,
uploaded while daveey-1 was active. The fillers are the scripted baselines (≥1, normally 2). Never
submit a scripted baseline as a champion.

Ownership is set at **upload** time, not submit time: give champion #2's policy entry
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` in `coworld-release.yml`'s `policies` JSON,
or the submit 409s "already assigned to player".

If a direct API route is later discovered, document it here and keep the workflow as fallback.

---

## Literal ids

| Thing | Id |
|---|---|
| Player `daveey` | `ply_44ae9048-3242-4654-881f-6d9d43347fa3` |
| Player `daveey-1` | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` |
| Asana user David Bloomin | `1209016834701578` |
| Asana project **Coworld Ideas** | `1217704774784096` |
| Asana project **Coworld Builder** | `1217747772236871` (sections Running / Blocked / Done / Fleet — section gids in `fleet/cloud.md`) |
| Discord guild | `1309708848730345493` |
| Discord channel `#coworlds` | `1440464430646427718` |

## Non-Observatory calls

```bash
# Asana — read a task (add opt_fields for custom_fields / memberships / subtasks)
curl -sS "https://app.asana.com/api/1.0/tasks/<gid>?opt_fields=name,completed,notes,custom_fields,memberships.section.gid" \
  -H "Authorization: Bearer $ASANA_PAT"

# Discord (Disco bot) — announcements, NOT Slack
curl -sS -X POST "https://discord.com/api/v10/channels/1440464430646427718/messages" \
  -H "authorization: Bot $DISCORD_BOT_TOKEN" -H 'content-type: application/json' \
  -d '{"content":"…"}'

# GitHub
GH_TOKEN=$GH_TOKEN gh workflow run … -R Metta-AI/cogame-<slug>
```

### Asana section moves (phases 00, 80, 90)

Moving a task between *Running* / *Blocked* / *Done* is **one call**, against the **section**
gid (they are in `fleet/cloud.md`; a task is moved *into* a section, never "set" on the task):

```bash
# section gids: Running 1217747860567752 | Blocked 1217762552336061 | Done 1217748136343842
curl -sS -X POST "https://app.asana.com/api/1.0/sections/<section_gid>/addTask" \
  -H "Authorization: Bearer $ASANA_PAT" -H 'content-type: application/json' \
  -d '{"data":{"task":"<task_gid>"}}'
```

Creating a task directly in a section uses the same section gid on the create:
`POST /tasks {"data":{"projects":["1217747772236871"],"memberships":[{"project":"1217747772236871","section":"1217747860567752"}],"name":…,"notes":…}}`.

### `heartbeat_at` (custom field `1217748424048134`)

```bash
# read (needs opt_fields=custom_fields)
curl -sS "https://app.asana.com/api/1.0/tasks/<task_gid>?opt_fields=custom_fields" \
  -H "Authorization: Bearer $ASANA_PAT" \
 | jq -r '.data.custom_fields[]|select(.gid=="1217748424048134")|.text_value'
# write (custom_fields is a MAP keyed by field gid)
curl -sS -X PUT "https://app.asana.com/api/1.0/tasks/<task_gid>" \
  -H "Authorization: Bearer $ASANA_PAT" -H 'content-type: application/json' \
  -d '{"data":{"custom_fields":{"1217748424048134":"<UTC ISO-8601>"}}}'
```

### Comments and subtasks

```bash
curl -sS -X POST "https://app.asana.com/api/1.0/tasks/<task_gid>/stories" \
  -H "Authorization: Bearer $ASANA_PAT" -H 'content-type: application/json' \
  -d '{"data":{"text":"…"}}'
curl -sS "https://app.asana.com/api/1.0/tasks/<task_gid>/subtasks?opt_fields=name,completed,assignee" \
  -H "Authorization: Bearer $ASANA_PAT"
```

## Featured match / replay route

`https://softmax.com/<slug>` is the human page. **Whether it is server-rendered is not recorded
here** — the bullwhip run read the iframe out of the raw HTML successfully, but a client-rendered
build would return a shell and the grep would find nothing. Treat an empty grep as *unknown*, not
as a failure, and fall back to the API the page itself reads:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '.entries[]|select(.name=="<slug>")|{id,canonical,replay_viewer,featured_match}'
```

(`?name=` on `/coworlds` is ignored — filter client-side, and select on the key `canonical`.)
The static replay route is
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`; a `/client/replay` pod
URL is a failure either way.

**Answered (lighthouse run, 2026-08-22):** the page is now **client-rendered** for the iframe —
the raw-HTML grep finds nothing for any coworld, and `/coworlds`' `featured_match` is `null`
platform-wide, so neither is evidence. What works:
- The featured match is server-rendered into the page's SSR payload at `state.playlist[0]`.
- The iframe `src` comes from the call the page's own JS makes:
  `POST $BASE/coworlds/replays/session {"coworld_id":"<cow_id>","replay_uri":"<s3 url>"}` →
  `{"viewer_url","ready"}`; static delivery ⇔ `ready:true` and the path ends `/index.html`.
- In the static route, `<sha>` is the coworld's **manifest_hash** (`sha256:…`, URL-encoded), NOT
  the replay-viewer bundle digest (that 404s).
- The route is served by `api.observatory.softmax-research.net`; the same path through the
  `softmax.com/api/observatory` proxy returns `404 {"detail":"Replay viewer shell not found"}`
  for every coworld — proxy behaviour, not a defect in yours.

## Gotchas carried forward from earlier campaigns

- `/v2/leagues/<id>/rounds` 404s; the flat `/v2/rounds?league_id=` is the real route. Conversely
  episodes are nested: `/v2/rounds/<id>/episodes`. The two rules are inverted — don't generalize.
- `limit` is honoured only up to 200.
- `/v2/coworlds?name=` is ignored; filter client-side and select on the key **`canonical`** (not
  `is_canonical`, which is absent from every row).
- `POST /v2/episodes/search` takes only a nested `where` tree; flat kwargs 422 with
  `extra_forbidden`.
