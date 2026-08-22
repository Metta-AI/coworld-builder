# coworld-builder — cloud ids

The single source of truth for every id this repo's tooling and its agents need.
`fleet/bin/deploy.py` **reads** the environment/vault lines and the ids table, and **rewrites**
the ids table (between the markers) after `create`. Everything else here is hand-maintained.

Ids are not secrets. Tokens are — none appear in this file, ever.

## Environment & vaults

- `environment_id: env_017PXeSYBWccAvG8XynueHm6` — the ctf-team cloud environment. Reused
  deliberately: it already has the egress allow-list and the sandbox shape these agents need.
- `vault_ids: vlt_011CdApMvqzJr9CKNMkuVDW3, vlt_011CeJJ4eJ7h2TKoPBwKhA4M` — the first carries
  `SOFTMAX_TOKEN`, `GH_TOKEN`, `ASANA_PAT`; the second `DISCORD_BOT_TOKEN`; all substituted at egress.

| vault | id | credentials | status |
|---|---|---|---|
| fleet vault (shared) | `vlt_011CdApMvqzJr9CKNMkuVDW3` | `SOFTMAX_TOKEN`, `GH_TOKEN`, `ASANA_PAT` | live |
| coworld-builder-discord | `vlt_011CeJJ4eJ7h2TKoPBwKhA4M` | `DISCORD_BOT_TOKEN` → host `discord.com` (credential `vcrd_01QU9AwcE3bj7PRqFN1WuvxX`) | live (created 2026-08-22 via `POST /vaults {display_name}` then `POST /vaults/{id}/credentials {display_name, auth:{type:environment_variable, secret_name, secret_value, networking:{type:limited, allowed_hosts}, injection_location:{header,body}}}`) |


## Managed Agents ids

Filled in by `python3 fleet/bin/deploy.py create`. Do not hand-edit ids; re-run the tool.

<!-- ids:start -->
| name | kind | model | id | version |
|---|---|---|---|---|
| coworld-builder-designer | agent | claude-opus-5 | TBD | TBD |
| coworld-builder-builder | agent | claude-opus-5 | TBD | TBD |
| coworld-builder-reviewer | agent | claude-opus-5 | TBD | TBD |
| coworld-builder-fixer | agent | claude-opus-5 | TBD | TBD |
| coworld-builder-judge | agent | claude-fable-5 | TBD | TBD |
| coworld-builder-verifier | agent | claude-opus-5 | TBD | TBD |
| coworld-builder-coordinator | agent | claude-fable-5 | TBD | TBD |
| coworld-builder-hourly | deployment | — | TBD | — |
<!-- ids:end -->

Deployment schedule: `11 * * * *` UTC (hourly, minute 11 — staggered clear of the cogamer
fleet's crons). Config: `fleet/deployment.json`.

## Asana

| what | gid |
|---|---|
| Coworld Ideas (the input queue; read-only to the agent — never create or reorder) | `1217704774784096` |
| Coworld Builder (`$BUILDER_PROJECT` — run tasks live here) | `1217747772236871` |
| Coworld Builder section Running | `1217747860567752` |
| Coworld Builder section Blocked | `1217762552336061` |
| Coworld Builder section Done | `1217748136343842` |
| Coworld Builder section Fleet (setup + fleet cards) | `1217747860605582` |
| David Bloomin (assignee for every Blocked subtask) | `1209016834701578` |
| `heartbeat_at` custom field (text, UTC ISO-8601; on the Coworld Builder project) | `1217748424048134` |

## Discord

| what | id |
|---|---|
| guild | `1309708848730345493` |
| `#coworlds` (the one channel this agent may post to) | `1440464430646427718` |

One message per run, phase 70 only. See AGENT.md §Hard safety rules.

## GitHub

| what | value |
|---|---|
| this repo (read-write mount at `/workspace/coworld-builder`) | `https://github.com/Metta-AI/coworld-builder` |
| cogamer (read mount at `/workspace/cogamer`, for `fleet/PROTOCOLS.md`) | `https://github.com/daveey/cogamer` |
| starters (read mounts at `/workspace/starters/<name>`) | `Metta-AI/`: `cogame-babel`, `cogame-bullwhip`, `cogame-parley`, `coworld-ctf`, `cogame-moba`, `cogame-factorio` |
| coworld repos created per run | `https://github.com/Metta-AI/cogame-<slug>` |
| org secrets required on `Metta-AI` for Actions | `SOFTMAX_TOKEN`, `ANTHROPIC_API_KEY` |
