# coworld-builder — cloud ids

The single source of truth for every id this repo's tooling and its agents need.
`fleet/bin/deploy.py` **reads** the environment/vault lines and the ids table, and **rewrites**
the ids table (between the markers) after `create`. Everything else here is hand-maintained.

Ids are not secrets. Tokens are — none appear in this file, ever.

## Environment & vaults

Everything below lives in the Anthropic Console workspace **`daveey-builder-rl`**
(`workspace_id: wrkspc_01MGK1QjvxLGdUFCeExDjLSb`). The fleet was migrated here from the Default
workspace on 2026-09-05; the originals there are paused, never deleted. `fleet/bin/deploy.py` reads
the `workspace_id:` line and sends it as `anthropic-workspace-id` on every call, because the key it
uses (`daveey/anthropic/org-key`) is org-scoped.

- `environment_id: env_019SmBGHe5jFJRAx79XbLJ2t` — the `coworld-builder` cloud environment
  (unrestricted egress).
- `vault_ids: vlt_011Ceji2nezKy48HL8omxZoS, vlt_011Ceji2osuWzkRdtzSAjvGe, vlt_011Ceji2q5bkjbNtYCpaXoXW` — the first carries
  `SOFTMAX_TOKEN`, `GH_TOKEN`, `ASANA_PAT`; the second `DISCORD_BOT_TOKEN`; the third `GEMINI_API_KEY`
  (nano-banana board art, `playbooks/art-nanobanana.md`); all substituted at egress.

| vault | id | credentials | status |
|---|---|---|---|
| coworld-builder-shared | `vlt_011Ceji2nezKy48HL8omxZoS` | `SOFTMAX_TOKEN` → `softmax.com`, `*.softmax.com` (`vcrd_01XH1j2iVb3ZAwykg2hstrKK`); `GH_TOKEN` → `api.github.com` (`vcrd_011msqcS7eDVDvYyzWX79DgU`); `ASANA_PAT` → `app.asana.com` (`vcrd_01V7tG4EumFwF1BeYQ1uvzJy`, rotated 2026-09-07 to the `asana/coworld-builder-pat` token, identity daveey@softmax.com) | live |
| coworld-builder-discord | `vlt_011Ceji2osuWzkRdtzSAjvGe` | `DISCORD_BOT_TOKEN` → `discord.com` (`vcrd_014rxX1s6cDGqcJcsdzYauuo`, the **disco** bot `1477537399365046415`, value from Secrets Manager `vault/discord/disco/app`) | live |
| coworld-builder-gemini | `vlt_011Ceji2q5bkjbNtYCpaXoXW` | `GEMINI_API_KEY` → `generativelanguage.googleapis.com` (`vcrd_01AhEHwN8rXu3oa4KTzNhToY`); value from Secrets Manager `polis/shared/gemini-api-key` | live |
| costbot-anthropic (shared with paintbot-rl) | `vlt_011Cepp92ZY28CEh9BDzynFT` | `ANTHROPIC_API_KEY` → `api.anthropic.com`, header only (`vcrd_01NW7V4DuCrMqm8LawqDSNnZ`); the org key, used **only** by the cost reporter below — never attach it to the heartbeat deployments | live (created 2026-09-07) |

Credentials are created with `POST /vaults {display_name}` then `POST /vaults/{id}/credentials
{display_name, auth:{type:environment_variable, secret_name, secret_value, networking:{type:limited,
allowed_hosts}, injection_location:{header,body}}}`; values are write-only and are rotated in place.

## Parallelism

Several coworld runs advance at the same time. Each deployment below is one heartbeat cron on
the **same** coordinator agent; every firing adopts **at most one** unit of work (resume a stale
run, resume an unblocked run, or claim one new idea) and then exits — so the crons fan out the
work, and the cap below is what bounds it.

- `max_parallel_runs: 3` — the maximum number of *Running* runs with a **fresh** heartbeat
  (< 180 min and no `session_ended_at ≥ heartbeat_at` — 3 h because a coordinator blocked in a long sub-agent thread cannot heartbeat) that may exist at once. A heartbeat that
  finds the cap reached does not claim a new idea; it still resumes a stale or unblocked run.
  This is the throttle to lower when the shared resource (Bedrock capacity) is tight — lower it
  here, no redeploy needed, the coordinator reads this file every heartbeat. Worst case is
  **cap + 1**: two heartbeats that overlap within seconds (a cron plus a manual or retried run)
  can both see `live = cap − 1` and both claim; there is deliberately no re-check after a claim
  (the claim itself is the commitment). Lowering it never
  stops runs already in flight; it only stops new claims.
- The separate bound of **2 simultaneously-Blocked runs** (`prompts/00-claim.md` step 3) is
  unchanged and independent.

| deployment | cron (UTC) | status |
|---|---|---|
| `coworld-builder-a` | `11 * * * *` | paused since 2026-09-08 — fired by the gate |
| `coworld-builder-b` | `31 * * * *` | paused since 2026-09-08 — fired by the gate |
| `coworld-builder-c` | `51 * * * *` | paused since 2026-09-08 — fired by the gate |

**The crons are paused.** `.github/workflows/heartbeat-gate.yml` runs `fleet/bin/heartbeat_gate.py`
every 20 minutes and POSTs `/deployments/<id>/run` on the least-recently-run of the three only when
there is a unit of work (an idle Fable heartbeat cost ~$1.2–1.5 and 58 of 66 sessions on 2026-09-07
were idle). `python3 fleet/bin/deploy.py unpause` restores the crons; `pause` re-pauses them. The
pause is a live status, not a field in `fleet/deployment.json`, so `deploy.py update` never touches
it. Every fired session carries the `$200` budget in `fleet/deployment.json`.

The same table lives in `fleet/deployment.json`'s `deployments` list, which is what
`fleet/bin/deploy.py` actually applies; `deploy.py` prints a WARNING if the two disagree.
`coworld-builder-a` **is** the original `coworld-builder-hourly` deployment, renamed and
rescheduled in place by `deploy.py update` — same id, never deleted, never duplicated.

## Managed Agents ids

Filled in by `python3 fleet/bin/deploy.py create`. Do not hand-edit ids; re-run the tool.

<!-- ids:start -->
| name | kind | model | id | version |
|---|---|---|---|---|
| coworld-builder-designer | agent | claude-opus-5 | `agent_015htUThBTiX7Fra5qrEpquP` | 1 |
| coworld-builder-builder | agent | claude-opus-5 | `agent_01AthKSsUbWvWosHh7HZjCAr` | 1 |
| coworld-builder-reviewer | agent | claude-opus-5 | `agent_01CsHjdc4pxeqSVDW7JvzBcZ` | 1 |
| coworld-builder-fixer | agent | claude-opus-5 | `agent_01QMN2xVrv6ns2csqFh6hs3w` | 1 |
| coworld-builder-judge | agent | claude-fable-5 | `agent_01Qr1e1BWYz9uFFqsNHhkizq` | 1 |
| coworld-builder-verifier | agent | claude-opus-5 | `agent_01KfCo21DgZQmQVjZeDcvM54` | 1 |
| coworld-builder-coordinator | agent | claude-fable-5 | `agent_01DjRYToc7AQajSeXcQmrfrp` | 1 |
| coworld-builder-a | deployment | — | `depl_01DjRYVBHvWDKLniB32apgZ8` | — |
| coworld-builder-b | deployment | — | `depl_019XuubNJYzeb3cix2Xv3vmS` | — |
| coworld-builder-c | deployment | — | `depl_01Tw4fZqARa9zFXdbdognKay` | — |
<!-- ids:end -->

These are the `daveey-builder-rl` ids (all v1, created at the 2026-09-05 migration). The
pre-migration Default-workspace agents (coordinator v5 etc.) are paused there and are not what
the crons run. Each heartbeat deployment carries a `$200` session budget cap.

Deployment schedules: `11`, `31`, `51 * * * *` UTC — hourly each, 20 minutes apart, staggered
clear of the cogamer fleet's crons (§Parallelism). Config: `fleet/deployment.json`.

## Cost reporting (costbot)

A separate, tiny agent posts the fleet's **previous-UTC-day token spend in dollars, broken down by
sub-agent**, to Discord as the disco bot every day at 00:30 UTC. It is read-only and is not part of
the heartbeat: the coordinator never runs it and never reads its config.

| what | value |
|---|---|
| tool | `fleet/bin/costbot.py` (`report`, `deploy`, `run`, `status`) — python3 stdlib, same file as in paintbot-rl |
| config | `fleet/costbot.json` (fleet name, deployment-name prefixes, workspace/environment/vault ids, Discord channel, cron, model; `ids` written by `deploy`) |
| agent | `coworld-builder-costbot` `agent_01HBxn8TtFzoFMZzEgSDq5Wt` v1, `claude-sonnet-5` effort low, system prompt `fleet/costbot.md` |
| deployment | `coworld-builder-costbot` `depl_01LH1ofjgY85RD25bTvBQpC5`, cron `30 0 * * *` UTC, `$2` session budget |
| vaults | `coworld-builder-discord` + `costbot-anthropic` (above) |
| destination | disco's DM channel with David Bloomin, `1477593964675862618` |
| numbers | the API's `usage.list_cost` per session and per thread (list price; billed may be lower). Sessions counted by UTC start; a message carrying `[costbot coworld-builder <day>]` already in the channel means that day is done and a re-run does not post again |

Preview or re-run by hand: `python3 fleet/bin/costbot.py report [--day YYYY-MM-DD] [--post]`;
`costbot.py run` fires the reporter now (it reports yesterday). Change the cron, model, or channel in
`fleet/costbot.json` and run `costbot.py deploy`.

## Sandbox tooling

What the agents' sandbox is known to provide. `jq` appears in almost every phase prompt; if the
preflight in `prompts/00-claim.md` step 0 finds it missing, the prompts' `python3` equivalents are
used instead and the gap is logged — it is never a reason to block.

| tool | status | used by |
|---|---|---|
| `git` | guaranteed | every phase (this repo + the coworld repo) |
| `gh` | **NOT guaranteed** — the 00-claim preflight installs v2.63.2 from the release tarball (2026-08-22 the first run hit this) | every GitHub step (repo create, workflow dispatch/watch, secrets list) |
| `gh` | guaranteed | phases 20, 30, 40, 50, 60 (workflow dispatch, run watch, artifact download) |
| `curl` | guaranteed | Asana, Observatory, softmax.com, Discord |
| `python3` | guaranteed | `fleet/bin/deploy.py`; the fallback for every `jq` line |
| `jq` | expected, preflighted (`prompts/00-claim.md` step 0) | JSON reads/writes in 00, 20, 40, 50, 60, 70 |
| `Pillow` (python) | not preinstalled — `python3 -m pip install --user pillow` | `playbooks/art-nanobanana.md` step 2 (keying/splitting sprite sheets) |
| docker / nim / emsdk | **absent by design** | all compilation happens in GitHub Actions |

## Asana

| what | gid |
|---|---|
| Coworld Ideas (the input queue; read-only to the agent — never create or reorder) | `1217704774784096` |
| Coworld Builder (run tasks live here; SPEC/AGENT call it "the Builder board" — no env var sets it) | `1217747772236871` |
| Coworld Builder section Running | `1217747860567752` |
| Coworld Builder section Blocked | `1217762552336061` |
| Coworld Builder section Done | `1217748136343842` |
| Coworld Builder section Fleet (setup + fleet cards) | `1217747860605582` |
| David Bloomin (assignee for every Blocked subtask) | `1209016834701578` |
| `heartbeat_at` custom field (text, UTC ISO-8601; on the Coworld Builder project) | `1217748424048134` |

## Observatory players

| player | id | used for |
|---|---|---|
| `daveey` | `ply_44ae9048-3242-4654-881f-6d9d43347fa3` | champion #1 submission (phase 50) |
| `daveey-1` | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` | champion #2: the `"player"` field on its policy entry (phase 40) **and** its submission (phase 50) |

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
| the atlas (phase 75) | `Metta-AI/metta` — **not mounted**; `atlas-update.yml` checks it out in CI with `GH_PAT` and opens one PR per run against `web/softmax.com/src/scripts/atlas/`. The agent never pushes to `metta` main and never merges the PR by hand |
| CI credentials | repo secrets on `Metta-AI/coworld-builder`: `SOFTMAX_TOKEN`, `ANTHROPIC_API_KEY`, `GH_PAT` (user token, admin on Metta-AI repos — the fleet mount-token convention); `.github/workflows/propagate-secrets.yml` copies the first two onto any `Metta-AI/<repo>` with it. No GitHub App: the org apps are installed on softmax-agents, not Metta-AI |
