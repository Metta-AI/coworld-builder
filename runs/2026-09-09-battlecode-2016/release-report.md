# Release report — battlecode 0.8.2

Run: `2026-09-09-battlecode-2016` · Repo: `Metta-AI/cogame-battlecode` (MOD run) · Phase 40, third
release of this run.

## Summary

| field | value |
|---|---|
| version | **0.8.2** |
| `cow_id` | **`cow_26cf6929-4ace-4d27-b4e6-da7edd5eb2ef`** |
| `manifest_sha` | **`sha256:2985d08f2c180920f3a93f3701f44d18e95250ccb87a10ea156536c21de8bf81`** |
| release run | **`34399197087`** — conclusion `success` |
| release run URL | https://github.com/Metta-AI/cogame-battlecode/actions/runs/34399197087 |
| released from | `main` @ `6e89d0fe57cb12e564451a2d2dec6bc99bd7024d` |
| dispatches used | **1 of 3** |
| supersedes | 0.8.1 (`cow_089d7551-1bab-49d6-be88-157149ea97f9`) |

Why this release: PR #13 (`bc16-duel-label`, merged 18:55:03Z) fixed bc16's killfeed label, which
the Nim broadcast layer generates at episode time and bakes into every replay. It read
`LAUNCHER DUEL` — bc23 vocabulary in a year with no launcher unit — and now reads
`TRADE — N attackers lost to M`, which is what bc16 actually counts. Only episodes produced by a
new coworld version carry the fix, hence the version bump.

## What was dispatched

```bash
dispatched_at=2026-09-09T20:08:01Z
gh workflow run coworld-release.yml -R Metta-AI/cogame-battlecode --ref main \
  -f version=0.8.2 -f put_secret=true
```

No `-f policies=` override — the repo's `tools/ci/policies.json` (32 entries) is correct and
unchanged. No `-f skip_certify=true`. The run was located with the `dispatch-then-watch` recipe
(`playbooks/make-coworld.md` §RECIPE): the poll returned `databaseId 34399197087`,
`createdAt 2026-09-09T20:08:02Z`, `headSha 6e89d0fe57cb12e564451a2d2dec6bc99bd7024d` — created
after the stamp and distinct from 0.8.1's run `34380179056`. Wall time ~8m30s
(20:08:02Z → 20:16:3xZ).

## Gate: main CI at the released sha

`gh run view 34391925052 -R Metta-AI/cogame-battlecode --json status,conclusion,headSha`

```json
{"conclusion":"success","createdAt":"2026-09-09T18:55:06Z",
 "displayTitle":"Merge pull request #13 from Metta-AI/bc16-duel-label",
 "headSha":"6e89d0fe57cb12e564451a2d2dec6bc99bd7024d",
 "status":"completed","updatedAt":"2026-09-09T19:59:16Z","workflowName":"CI"}
```

`completed` / `success` at the exact sha released. `git/ref/heads/main` confirmed at
`6e89d0fe57cb12e564451a2d2dec6bc99bd7024d` at dispatch time.

## Exit criterion — read from `release-result.json`, not the green tick

| bullet | required | value read |
|---|---|---|
| `ok` | `true` | **`true`** |
| `canonical` | `true` | **`true`** |
| `secret_put` | `true` | **`true`** |
| `step_failed` | `null` | **`null`** |
| `errors` | `[]` | **`[]`** |
| `certify.ok` | `true` | **`true`** |
| `certify.replay_liveness` | contains `skipped (static replay bundle declared` | **`"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`** — substring test `true` |
| `policies[]` | 32 for 32 requested | **32**, all labels distinct (32 unique `name:vN`) |
| champion #2 `player_id` | `ply_bac48eb1-…` | **`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`** on `battlecode-bc16-pullers` |
| `policy_version_id` | `null` expected, not a failure | `null` on all 32 — expected (`upload-policy` prints no uuid) |

Also in the artifact: `hosted_smoke: "passed"`, `hosted_certification: "certified"`.
All 10 certification transcript steps passed locally in the runner (matriculate,
source-resolves, images-reachable, fixture-conforms, smoke-episode, results-conform,
replay-present, replay-loadable, players-run, supporting-roles).

## 32-policy check and the labels that came back

32 entries requested in `tools/ci/policies.json`, 32 entries in `policies[]`. Every policy minted a
fresh `vN` label, which is documented platform behaviour (`playbooks/make-coworld.md` §Phase 2:
every `upload-policy` call mints a fresh version even for byte-identical content). Minting is
additive; nothing was resubmitted or repointed in the league.

**The four bc16 policies (0.8.1 → 0.8.2):**

| role | name | 0.8.1 | 0.8.2 | owner |
|---|---|---|---|---|
| champion #1 | `battlecode-bc16-bulwark` | `:v2` | **`:v3`** | daveey (`player_id: null`) |
| champion #2 | `battlecode-bc16-pullers` | `:v2` | **`:v3`** | daveey-1 (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) |
| filler | `battlecode-bulwark` | `:v2` | **`:v3`** | daveey (`player_id: null`) |
| filler | `battlecode-greenhorn` | `:v2` | **`:v3`** | daveey (`player_id: null`) |

Filler versions (`:v3` on `battlecode-bulwark` / `battlecode-greenhorn`) differ from the
champions' by name; both champions are LLM prompt policies (`PLAYER_PROMPT`), both fillers are
scripted (`PLAYER_SCRIPTED`).

The other 28 entries (the bc20/bc21/bc22/bc23/bc24/bc25 year modules and the shared base set) also
minted: `battlecode-loyalist`/`opportunist`/`awu`/`scaffold` and the bc20 four at `:v7`, the bc21
four at `:v6`, the bc24 and bc25 fours at `:v5`, the bc23 and bc22 fours at `:v4`.

The league deliberately stays on its `:v1` policy versions
(`c073ca20-f820-403f-86c7-8cbd8d704084`, `2175495c-757d-451e-a3e3-b3ed6f20692b`,
`99053bee-f15a-4b03-bfa8-51f2e915814a`, `bb2726bf-0c23-4751-b293-1cc0be05f8ea`). No submit or
repoint was performed here — that is the coordinator's call.

## Certification poll — settled

The sandbox CLI starts unauthenticated, so:

```bash
uvx --from 'coworld[auth]==0.1.43' softmax set-token "$SOFTMAX_TOKEN"     # -> Token saved for https://softmax.com/api
uvx --from 'coworld[auth]==0.1.43' coworld status cow_26cf6929-4ace-4d27-b4e6-da7edd5eb2ef --json
```

Settled on the **first** poll — no waiting was needed; `completed_at` (20:15:33Z) precedes the
workflow's own completion, so the "Wait for the uploaded version to become canonical" step had
already absorbed the settle. Verbatim:

```json
{
  "coworld": {
    "id": "cow_26cf6929-4ace-4d27-b4e6-da7edd5eb2ef",
    "name": "battlecode",
    "version": "0.8.2",
    "canonical": true,
    "manifest_hash": "sha256:2985d08f2c180920f3a93f3701f44d18e95250ccb87a10ea156536c21de8bf81"
  },
  "certification": {
    "coworld_id": "cow_26cf6929-4ace-4d27-b4e6-da7edd5eb2ef",
    "state": "certified",
    "certified": true,
    "contract_version": "main-bb8260360bbb",
    "certification_job_id": "bd54579f-f5f1-444f-831d-99e2d22ee685",
    "failed_step": null,
    "failure": null,
    "transcript_summary": [
      {"id": "matriculate", "status": "pass"},
      {"id": "source-resolves", "status": "pass"},
      {"id": "images-reachable", "status": "pass"},
      {"id": "fixture-conforms", "status": "pass"},
      {"id": "smoke-episode", "status": "pass"},
      {"id": "results-conform", "status": "pass"},
      {"id": "replay-present", "status": "pass"},
      {"id": "replay-loadable", "status": "pass"},
      {"id": "players-run", "status": "pass"},
      {"id": "supporting-roles", "status": "pass"}
    ],
    "completed_at": "2026-09-09T20:15:33.117753Z"
  },
  "hosted_smoke_episodes": [
    {"id": "ereq_149e0a54-8af1-44ce-8723-137078d9ab04", "status": "completed", "error": null},
    {"id": "ereq_3002623d-9d5e-4e8f-9483-6dc75baf3bc3", "status": "completed", "error": null},
    {"id": "ereq_58d51429-b081-4dd4-814c-239c63d2281f", "status": "completed", "error": null},
    {"id": "ereq_b385e298-f7f4-4dda-aff5-e8b92b8de53c", "status": "completed", "error": null},
    {"id": "ereq_b5a6c550-fd00-45df-9ae7-4b746ab42269", "status": "completed", "error": null}
  ]
}
```

Checks against the step-3 requirements:

- `.certification.state == "certified"` ✅
- `.certification.certified == true` ✅
- `.certification.failed_step == null` ✅
- `.certification.failure == null` ✅
- `.coworld.canonical == true` at `.coworld.version == "0.8.2"` ✅
- hosted `.coworld.manifest_hash` == artifact `.manifest_sha`
  (`sha256:2985d08f2c180920f3a93f3701f44d18e95250ccb87a10ea156536c21de8bf81`) ✅ — byte-identical
- all 5 hosted smoke episodes `completed`, `error: null` ✅

`coworld status` was used rather than a raw GET on the certification endpoint (that 403s).

## Version history for this run

| version | `cow_id` | manifest sha256 | release run | state |
|---|---|---|---|---|
| 0.8.0 | `cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a` | `sha256:20a188ec8ada…` | — | superseded |
| 0.8.1 | `cow_089d7551-1bab-49d6-be88-157149ea97f9` | `sha256:6179e72b1e73…` | `34380179056` | superseded |
| **0.8.2** | **`cow_26cf6929-4ace-4d27-b4e6-da7edd5eb2ef`** | **`sha256:2985d08f2c18…`** | **`34399197087`** | **canonical + certified** |

Prior artifacts are preserved: `release-result-0.8.0.json` / `release-report-0.8.0.md` and
`release-result-0.8.1.json` / `release-report-0.8.1.md`. Nothing was deleted.

## Files written by this phase

- `runs/2026-09-09-battlecode-2016/release-result.json` — the 0.8.2 `release-result` artifact
  (phase 60 check 7 reads this exact filename)
- `runs/2026-09-09-battlecode-2016/release-report.md` — this report
- `runs/2026-09-09-battlecode-2016/release-result-0.8.1.json` — `git mv` of the previous
  `release-result.json`
- `runs/2026-09-09-battlecode-2016/release-report-0.8.1.md` — `git mv` of the previous
  `release-report.md`

No game code was touched: 0.8.2 is `main@6e89d0fe` built as-is, with the version supplied purely as
a workflow input.
