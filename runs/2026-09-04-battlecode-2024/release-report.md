# Phase 40 — Release report — `2026-09-04-battlecode-2024`

- Repo: `Metta-AI/cogame-battlecode` (MOD run — adds the `bc24` year module)
- Slug: `battlecode-2024`; year key `bc24`; platform coworld slug `battlecode`
- Version assigned by the coordinator: **0.11.0** (shared version namespace; 0.9.1 and 0.10.0 were
  in flight on the bc19 / bc17 runs — 0.10.x was never touched)
- **Result: released on the first dispatch. 1 dispatch used of a budget of 3.**

## Gate evidence (pre-dispatch)

| check | result |
|---|---|
| `main` sha at gate | `4bcb8db628a731a446980270159b540ffb380c09` (2026-09-10T23:35:58Z, "Merge pull request #20 … bc26(GV14): cats restore the target snapshot tile") |
| `ci.yml` on that exact sha | run **34542870700**, event `push`, `completed` / **`success`** |
| `main` re-read immediately before dispatch | `4bcb8db628a731a446980270159b540ffb380c09` — unmoved, no re-gate needed |
| sha the release actually snapshots | run 34552459781 `headSha` = `4bcb8db628a731a446980270159b540ffb380c09` ✅ |
| repo secrets | `SOFTMAX_TOKEN` (2026-09-03T20:14:29Z) and `ANTHROPIC_API_KEY` (2026-09-03T20:14:29Z) both present — `propagate-secrets.yml` not needed, not dispatched |
| manifest `game.replay_viewer.bundle` | `"static-replay-viewer"` ✅ |
| bc24 variant | `Battlecode 2024 — Breadwars (2 seats)`, `game_config.year_key == "bc24"`, `game_config.num_agents == 2` ✅ (all 10 variants carry `num_agents: 2`) |
| certification fixture | `certification.game_config.num_agents == 2` ✅ |
| `coworld-release.yml` step order | Build manifest (L168) → Certify locally (L182) → **Upload the policies** (L225) → Upload the Coworld (L323) → **Wait for the uploaded version to become canonical** (L361) → Put the Coworld secret (L419) → Assemble release-result (L445) ✅ — wait-for-canonical present in its proper place, between upload and secret put |
| `tools/ci/policies.json` | 40 entries (4 × 10 years), unmodified by me. No `-f policies=` override passed; no `-f skip_certify`. |
| in-flight `coworld-release.yml` runs at gate | none (newest prior was 34480332524, `success`, 2026-09-10T13:03Z) — no queueing behind the `concurrency: coworld-release` group |

### bc24 policy entries verified on `main` before dispatch

| role | name | selector | player field |
|---|---|---|---|
| champion #1 | `battlecode-bc24-fortress` | `PLAYER_PROMPT` (LLM, 1012-char prompt: "You command a flock of 50 ducks in Battlecode 2024. Three of your flags; three o…") | none → daveey |
| champion #2 | `battlecode-bc24-flagrush` | `PLAYER_PROMPT` (LLM, 933-char **different** prompt: "You command a flock of 50 ducks in Battlecode 2024. Capturing all three enemy fl…") | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` → daveey-1 |
| filler | `battlecode-gone-sharkin` | `PLAYER_SCRIPTED=gone-sharkin` | none |
| filler | `battlecode-examplefuncsplayer24` | `PLAYER_SCRIPTED=examplefuncsplayer24` | none |

All four run `/bin/battlecode-player`; both champions are LLM prompt policies, both fillers scripted.

## Dispatches

| # | version | change vs previous | run id | conclusion | `step_failed` | decision |
|---|---|---|---|---|---|---|
| 1 | `0.11.0` | — (first dispatch; `--ref main` @ `4bcb8db`, `put_secret=true`, no policy override, no `skip_certify`) | [34552459781](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34552459781) | `success` (01:53:22Z → 02:01:06Z) | `null` | **Accepted** — artifact satisfies every exit-criterion bullet. No re-dispatch. |

Run discovery used the `dispatch-then-watch` recipe: `dispatched_at=2026-09-11T01:53:21Z` recorded
before `gh workflow run`, then `gh run list --event workflow_dispatch` polled until a run with
`createdAt >= dispatched_at` appeared → `34552459781` (`createdAt` 2026-09-11T01:53:22Z). The
artifact below came from `gh run download 34552459781 -n release-result`.

## Result

| field | value |
|---|---|
| version | `0.11.0` |
| `cow_id` | `cow_b9c9aab2-42ac-4606-b1e6-442841de04de` |
| `manifest_sha` | `sha256:a8f75cf35577878ed80694c2b0383b18c3fe7de547b44dbb80bb25e91e9c471d` |
| release run id | `34552459781` |
| released `main` sha | `4bcb8db628a731a446980270159b540ffb380c09` |
| `hosted_smoke` | `passed` |
| `hosted_certification` | `certifying` (settled; the wait step confirmed canonical) |

### Exit criteria

| bullet | verdict |
|---|---|
| `ok: true` | **PASS** |
| `canonical: true` | **PASS** |
| `certify` non-null, `certify.ok: true` | **PASS** |
| `certify.replay_liveness` contains `skipped (static replay bundle declared` | **PASS** — `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"` |
| `policies[]` one entry per requested policy (40), distinct `<name>:vN` labels | **PASS** — 40 entries, 40 distinct labels |
| four bc24 names present | **PASS** — `battlecode-bc24-fortress:v7`, `battlecode-bc24-flagrush:v7`, `battlecode-gone-sharkin:v7`, `battlecode-examplefuncsplayer24:v7` |
| `battlecode-bc24-flagrush.player_id == "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | **PASS** |
| `policy_version_id` null on every entry | expected/documented — not a failure; phase 50 resolves UUIDs from `GET /policy-versions` |
| `secret_put: true` | **PASS** |
| `step_failed` / `errors` | `null` / `[]` |

### bc24 policy labels minted by this release

| role | label | owner |
|---|---|---|
| champion #1 | `battlecode-bc24-fortress:v7` | daveey (`player_id: null`) |
| champion #2 | `battlecode-bc24-flagrush:v7` | daveey-1 (`player_id: ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) |
| filler | `battlecode-gone-sharkin:v7` | daveey |
| filler | `battlecode-examplefuncsplayer24:v7` | daveey |

Filler versions (`v7`) are the same integer as the champions' here because every name is on its own
counter and all four bc24 names were minted together on each dispatch; the *labels* are distinct,
which is the requirement. (Non-bc24 names ran v1…v9 on their own counters.)

## Files written by this phase

- `runs/2026-09-04-battlecode-2024/release-result.json` — byte-identical copy of run 34552459781's `release-result` artifact
- `runs/2026-09-04-battlecode-2024/release-report.md` — this file
- `runs/2026-09-04-battlecode-2024/STATE.json` — `coworld.*` and `policies.*` filled in, `phase_attempts["40"] = 1`; `phase`, `heartbeat_at`, `session_id`, `session_ended_at` untouched

Nothing was committed or pushed in `coworld-builder`; nothing was pushed to `cogame-battlecode`
(no branch, PR, or `tools/ci/policies.json` touched).

## Full `release-result.json`

```json
{
  "version": "0.11.0",
  "ok": true,
  "cow_id": "cow_b9c9aab2-42ac-4606-b1e6-442841de04de",
  "manifest_sha": "sha256:a8f75cf35577878ed80694c2b0383b18c3fe7de547b44dbb80bb25e91e9c471d",
  "canonical": true,
  "hosted_smoke": "passed",
  "hosted_certification": "certifying",
  "certify": {
    "ok": true,
    "replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)",
    "output_tail": "Docker context: default (local images use this store)\nCertifying dist/coworld_manifest.json against transcript coworld-executable\n  [run ] matriculate: manifest conforms to the Coworld schema\n  [pass] matriculate: manifest conforms to the Coworld schema\n  [run ] source-resolves: whether each runnable declares a source_url that resolves to publicly accessible source\n  [pass] source-resolves: whether each runnable declares a source_url that resolves to publicly accessible source\n  [run ] images-reachable: every declared image is pullable or inspectable\n  [pass] images-reachable: every declared image is pullable or inspectable\n  [run ] fixture-conforms: the certification fixture validates against game.config_schema after runner token injection\n  [pass] fixture-conforms: the certification fixture validates against game.config_schema after runner token injection\n  [run ] smoke-episode: the game and certification players run one episode\n  [pass] smoke-episode: the game and certification players run one episode\n  [run ] results-conform: episode results validate against results_schema\n  [pass] results-conform: episode results validate against results_schema\n  [run ] replay-present: a replay artifact was produced\n  [pass] replay-present: a replay artifact was produced\n  [run ] replay-loadable: the replay artifact has a declared viewer path\n  [pass] replay-loadable: the replay artifact has a declared viewer path\n  [run ] players-run: every declared player actually started on the smoke episode (not just declared)\n  [pass] players-run: every declared player actually started on the smoke episode (not just declared)\n  [run ] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks\n  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks\nCertified dist/coworld_manifest.json\nTranscript: coworld-executable (10 steps passed)\nTranscript report: file:///home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-82ocyx5a/certification_report.html\nArtifacts: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-82ocyx5a\nResults: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-82ocyx5a/results.json\nReplay: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-82ocyx5a/replay\nReplay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)\nLogs: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-82ocyx5a/logs\nInspect replay: open /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-82ocyx5a/replay in your static replay viewer bundle (see STATIC_REPLAY_VIEWERS.md)\nInspect logs: ls /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-82ocyx5a/logs\n"
  },
  "policies": [
    {
      "name": "battlecode-loyalist",
      "version": "v9",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-opportunist",
      "version": "v9",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-awu",
      "version": "v9",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-scaffold",
      "version": "v9",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc20-latticer",
      "version": "v9",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc20-rusher",
      "version": "v9",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-bowl-of-chowder",
      "version": "v9",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer",
      "version": "v9",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc21-turtle",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc21-muckrush",
      "version": "v8",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-california-roll",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer21",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc24-fortress",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc24-flagrush",
      "version": "v7",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-gone-sharkin",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer24",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc25-coverage",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc25-siege",
      "version": "v7",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-spaark",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer25",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc23-duel",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc23-alchemist",
      "version": "v6",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-lemonade",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer23",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc22-rush",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc22-transmuter",
      "version": "v6",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-wololo",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer22",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc16-bulwark",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc16-pullers",
      "version": "v5",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-bulwark",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-greenhorn",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc19-saber",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc19-preachers",
      "version": "v2",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-saber",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer19",
      "version": "v2",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc17-orchard",
      "version": "v1",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc17-tankrush",
      "version": "v1",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-orchard",
      "version": "v1",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer17",
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
