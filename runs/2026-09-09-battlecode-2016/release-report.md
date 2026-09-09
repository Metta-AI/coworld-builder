# Phase 40 — Release report — run 2026-09-09-battlecode-2016

Repo: `Metta-AI/cogame-battlecode` (MOD run, eighth year module `bc16`)
Released from: `main` @ `46b92ae5ff9a78be61c659f4a2eff861aa17b838`
Dispatches spent: **1 of 3**

## Dispatches

| # | version | run id | URL | conclusion | `step_failed` | change vs previous |
|---|---|---|---|---|---|---|
| 1 | `0.8.0` | `34354493592` | https://github.com/Metta-AI/cogame-battlecode/actions/runs/34354493592 | success | `null` | — (first dispatch; `-f version=0.8.0 -f put_secret=true`, no `policies` override, no `skip_certify`) |

No retries were needed. No fixes were made to the tree in this phase; no game code was written.

Dispatch used the `dispatch-then-watch` recipe: `dispatched_at=2026-09-09T13:01:30Z` recorded
first, then `gh run list --workflow coworld-release.yml --event workflow_dispatch` polled until a
run with `createdAt >= dispatched_at` appeared (`34354493592`), and only that id was watched and
downloaded.

## Exit criterion — bullet by bullet

| Criterion | Holds? | Value |
|---|---|---|
| `ok: true` | **YES** | `"ok": true` |
| `canonical: true` | **YES** | `"canonical": true` (also `hosted_smoke: "passed"`) |
| `certify` non-null | **YES** | object present with `ok`, `replay_liveness`, `output_tail` |
| `certify.ok == true` | **YES** | `"ok": true` — all 10 transcript steps passed ("Transcript: coworld-executable (10 steps passed)") |
| `certify.replay_liveness` contains `skipped (static replay bundle declared` | **YES** | `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"` |
| one `policies[]` entry per requested policy, distinct `<name>:vN` labels | **YES** | 32 requested in `tools/ci/policies.json`, 32 returned, 32 distinct labels |
| `battlecode-bc16-pullers`.`player_id == "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | **YES** | `"player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` |
| `secret_put: true` | **YES** | `"secret_put": true` |

`policy_version_id` is `null` for all 32 entries. Expected — `upload-policy` prints no uuid;
phase 50 resolves UUIDs from `GET /policy-versions`. Not a failure.

**Exit criterion: MET.**

## STATE values for the coordinator

- `coworld.version` = `0.8.0`
- `coworld.cow_id` = `cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a`
- `coworld.manifest_sha` = `sha256:20a188ec8ada2b62879e5bb25065b3076e8dc190d6457a38538aabafb8a8419f`
- `coworld.release_run_id` = `34354493592`
- `policies.champion1` = `battlecode-bc16-bulwark:v1` (LLM `PLAYER_PROMPT`, daveey)
- `policies.champion2` = `battlecode-bc16-pullers:v1` (LLM `PLAYER_PROMPT`, daveey-1)
- `policies.fillers` = [`battlecode-bulwark:v1`, `battlecode-greenhorn:v1`] (scripted)

## All 32 policy versions minted by this run

| name | version | owning player |
|---|---|---|
| `battlecode-loyalist` | `v5` | (none — CI token / daveey) |
| `battlecode-opportunist` | `v5` | ply_bac48eb1-662e-44f8-973d-f3e016dccf5d |
| `battlecode-awu` | `v5` | (none — CI token / daveey) |
| `battlecode-scaffold` | `v5` | (none — CI token / daveey) |
| `battlecode-bc20-latticer` | `v5` | (none — CI token / daveey) |
| `battlecode-bc20-rusher` | `v5` | ply_bac48eb1-662e-44f8-973d-f3e016dccf5d |
| `battlecode-bowl-of-chowder` | `v5` | (none — CI token / daveey) |
| `battlecode-examplefuncsplayer` | `v5` | (none — CI token / daveey) |
| `battlecode-bc21-turtle` | `v4` | (none — CI token / daveey) |
| `battlecode-bc21-muckrush` | `v4` | ply_bac48eb1-662e-44f8-973d-f3e016dccf5d |
| `battlecode-california-roll` | `v4` | (none — CI token / daveey) |
| `battlecode-examplefuncsplayer21` | `v4` | (none — CI token / daveey) |
| `battlecode-bc24-fortress` | `v3` | (none — CI token / daveey) |
| `battlecode-bc24-flagrush` | `v3` | ply_bac48eb1-662e-44f8-973d-f3e016dccf5d |
| `battlecode-gone-sharkin` | `v3` | (none — CI token / daveey) |
| `battlecode-examplefuncsplayer24` | `v3` | (none — CI token / daveey) |
| `battlecode-bc25-coverage` | `v3` | (none — CI token / daveey) |
| `battlecode-bc25-siege` | `v3` | ply_bac48eb1-662e-44f8-973d-f3e016dccf5d |
| `battlecode-spaark` | `v3` | (none — CI token / daveey) |
| `battlecode-examplefuncsplayer25` | `v3` | (none — CI token / daveey) |
| `battlecode-bc23-duel` | `v2` | (none — CI token / daveey) |
| `battlecode-bc23-alchemist` | `v2` | ply_bac48eb1-662e-44f8-973d-f3e016dccf5d |
| `battlecode-lemonade` | `v2` | (none — CI token / daveey) |
| `battlecode-examplefuncsplayer23` | `v2` | (none — CI token / daveey) |
| `battlecode-bc22-rush` | `v2` | (none — CI token / daveey) |
| `battlecode-bc22-transmuter` | `v2` | ply_bac48eb1-662e-44f8-973d-f3e016dccf5d |
| `battlecode-wololo` | `v2` | (none — CI token / daveey) |
| `battlecode-examplefuncsplayer22` | `v2` | (none — CI token / daveey) |
| `battlecode-bc16-bulwark` | `v1` | (none — CI token / daveey) |
| `battlecode-bc16-pullers` | `v1` | ply_bac48eb1-662e-44f8-973d-f3e016dccf5d |
| `battlecode-bulwark` | `v1` | (none — CI token / daveey) |
| `battlecode-greenhorn` | `v1` | (none — CI token / daveey) |

## Full `release-result.json`

```json
{
  "version": "0.8.0",
  "ok": true,
  "cow_id": "cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a",
  "manifest_sha": "sha256:20a188ec8ada2b62879e5bb25065b3076e8dc190d6457a38538aabafb8a8419f",
  "canonical": true,
  "hosted_smoke": "passed",
  "hosted_certification": "certifying",
  "certify": {
    "ok": true,
    "replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)",
    "output_tail": "Docker context: default (local images use this store)\nCertifying dist/coworld_manifest.json against transcript coworld-executable\n  [run ] matriculate: manifest conforms to the Coworld schema\n  [pass] matriculate: manifest conforms to the Coworld schema\n  [run ] source-resolves: whether each runnable declares a source_url that resolves to publicly accessible source\n  [pass] source-resolves: whether each runnable declares a source_url that resolves to publicly accessible source\n  [run ] images-reachable: every declared image is pullable or inspectable\n  [pass] images-reachable: every declared image is pullable or inspectable\n  [run ] fixture-conforms: the certification fixture validates against game.config_schema after runner token injection\n  [pass] fixture-conforms: the certification fixture validates against game.config_schema after runner token injection\n  [run ] smoke-episode: the game and certification players run one episode\n  [pass] smoke-episode: the game and certification players run one episode\n  [run ] results-conform: episode results validate against results_schema\n  [pass] results-conform: episode results validate against results_schema\n  [run ] replay-present: a replay artifact was produced\n  [pass] replay-present: a replay artifact was produced\n  [run ] replay-loadable: the replay artifact has a declared viewer path\n  [pass] replay-loadable: the replay artifact has a declared viewer path\n  [run ] players-run: every declared player actually started on the smoke episode (not just declared)\n  [pass] players-run: every declared player actually started on the smoke episode (not just declared)\n  [run ] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks\n  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks\nCertified dist/coworld_manifest.json\nTranscript: coworld-executable (10 steps passed)\nTranscript report: file:///home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-hb3qqxuv/certification_report.html\nArtifacts: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-hb3qqxuv\nResults: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-hb3qqxuv/results.json\nReplay: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-hb3qqxuv/replay\nReplay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)\nLogs: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-hb3qqxuv/logs\nInspect replay: open /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-hb3qqxuv/replay in your static replay viewer bundle (see STATIC_REPLAY_VIEWERS.md)\nInspect logs: ls /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-hb3qqxuv/logs\n"
  },
  "policies": [
    {
      "name": "battlecode-loyalist",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-opportunist",
      "version": "v5",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-awu",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-scaffold",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc20-latticer",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc20-rusher",
      "version": "v5",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-bowl-of-chowder",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc21-turtle",
      "version": "v4",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc21-muckrush",
      "version": "v4",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-california-roll",
      "version": "v4",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer21",
      "version": "v4",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc24-fortress",
      "version": "v3",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc24-flagrush",
      "version": "v3",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-gone-sharkin",
      "version": "v3",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer24",
      "version": "v3",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc25-coverage",
      "version": "v3",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc25-siege",
      "version": "v3",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-spaark",
      "version": "v3",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer25",
      "version": "v3",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc23-duel",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc23-alchemist",
      "version": "v2",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-lemonade",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer23",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc22-rush",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc22-transmuter",
      "version": "v2",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-wololo",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer22",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc16-bulwark",
      "version": "v1",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc16-pullers",
      "version": "v1",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-bulwark",
      "version": "v1",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-greenhorn",
      "version": "v1",
      "policy_version_id": null,
      "player_id": null
    }
  ],
  "secret_put": true,
  "errors": [],
  "step_failed": null
}
```
