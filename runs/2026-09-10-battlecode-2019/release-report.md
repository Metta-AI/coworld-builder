# Phase 40 — Release report — `2026-09-10-battlecode-2019`

Coworld repo: **`Metta-AI/cogame-battlecode`** (public)
Released version: **`0.9.0`** (supersedes `0.8.2`, the bc16 run's release)
Released from: `main` @ **`f5de5bdbab21fb897f6eb4c27be76a1dced8f6bb`** (PR #16)
Phase 40 attempts: **1 dispatch of 3 budgeted** — succeeded on the first, no retry, no bump.

## Gate (before any dispatch)

`ci.yml` run **`34472691904`** on `main` @ `f5de5bdbab21fb897f6eb4c27be76a1dced8f6bb`
concluded **`success`** at `2026-09-10T13:01:57Z` (12/12 jobs; the long pole was the `test`
job, ~79 min). Watched to conclusion before dispatching. `main` was re-checked immediately
before the dispatch and was still at `f5de5bdbab…`, so the release snapshotted the exact
tree the gate verified.

Repo secrets verified once, both present, neither re-propagated:

| secret | last updated |
|---|---|
| `ANTHROPIC_API_KEY` | 2026-09-03T20:14:29Z |
| `SOFTMAX_TOKEN` | 2026-09-03T20:14:29Z |

`propagate-secrets.yml` was **not** dispatched (not needed).

## Pre-dispatch verification

- `tools/ci/policies.json` on `main`: **36 entries** (4 per year × 9 years), unchanged. Read
  from the repo, **no `policies` dispatch input passed** — the file is the source of truth.
- The four bc19 entries verified in the file before dispatch:
  - `battlecode-bc19-saber` — `PLAYER_PROMPT`, no `player` field (daveey) — champion #1
  - `battlecode-bc19-preachers` — a **different** `PLAYER_PROMPT`, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (daveey-1) — champion #2
  - `battlecode-saber` — `PLAYER_SCRIPTED=saber` (daveey) — filler
  - `battlecode-examplefuncsplayer19` — `PLAYER_SCRIPTED=examplefuncsplayer19` (daveey) — filler
- `coworld_manifest_template.json`: `game.replay_viewer.bundle = "static-replay-viewer"`
  (the static bundle declaration that makes replay-liveness skip); the `bc19` variant carries
  `game_config.num_agents = 2` and the `certification` fixture carries `num_agents = 2`.
- `.github/workflows/coworld-release.yml` step order confirmed load-bearing-correct:
  build manifest → **Certify locally** → **Upload the policies** → **Upload the Coworld** →
  **Wait for the uploaded version to become canonical** → **Put the Coworld secret** →
  assemble `release-result.json` → Enforce canonical.
  The "Wait for the uploaded version to become canonical" step **is present**.

## Dispatches

Found with the `dispatch-then-watch` recipe: `dispatched_at=2026-09-10T13:03:52Z` recorded
first, then `gh run list --event workflow_dispatch` polled until a run with
`createdAt >= dispatched_at` appeared. A bare `gh run list -L 1` was never used, so the
artifact below is from the run this phase actually started (created `13:03:53Z`, one second
after `dispatched_at`) and not a stale predecessor.

| # | version | run id | dispatched | concluded | `step_failed` | `errors` | decision |
|---|---|---|---|---|---|---|---|
| 1 | `0.9.0` | [`34480332524`](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34480332524) | 2026-09-10T13:03:52Z | `success` @ 13:11:17Z | `null` | `[]` | **Accepted.** All exit criteria met on the first dispatch. No retry, no version bump, no fix. |

Command used (no `-f policies=…`, no `-f skip_certify=true`):

```bash
gh workflow run coworld-release.yml -R Metta-AI/cogame-battlecode --ref main \
  -f version=0.9.0 -f put_secret=true
```

Step timings for the accepted run (`release` job, headSha `f5de5bdbab…`):

| step | result | duration |
|---|---|---|
| Build the Coworld manifest | success | 13:04:10 → 13:07:16 (3m06s) |
| Certify locally | success | 13:07:16 → 13:07:39 (23s) |
| Upload the policies | success | 13:07:39 → 13:08:44 (1m05s) |
| Upload the Coworld (`--wait-hosted-smoke`) | success | 13:08:44 → … |
| Wait for the uploaded version to become canonical | success | … |
| Put the Coworld secret | success | … |
| Enforce canonical | success | run ended 13:11:17Z |

The 23-second local certify is **normal for this repo**, not a skip: the previous successful
release (`0.8.2`, run `34399197087`) certified in 22 s with the same 10-step transcript.
`skip_certify` was not passed, and `certify` is non-null with all ten steps `[pass]`.

## Result — read from `release-result.json`, not from the run's colour

| exit criterion | required | actual | verdict |
|---|---|---|---|
| `ok` | `true` | `true` | PASS |
| `canonical` | `true` | `true` | PASS |
| `certify` | non-null | non-null (10/10 transcript steps passed) | PASS |
| `certify.ok` | `true` | `true` | PASS |
| `certify.replay_liveness` | contains `skipped (static replay bundle declared` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` | PASS |
| `policies[]` | one entry per requested policy, distinct `<name>:vN` | **36 entries, 36 distinct labels** (one per entry in `tools/ci/policies.json`) | PASS |
| champion #2 `player_id` | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` on `battlecode-bc19-preachers` | PASS |
| `secret_put` | `true` | `true` | PASS |

Supporting fields: `hosted_smoke: "passed"`, `hosted_certification: "certifying"`,
`step_failed: null`, `errors: []`.
`hosted_certification: "certifying"` is expected and benign — the release workflow's own
comment on the canonical-wait step documents that hosted certification settles after
`--wait-hosted-smoke` returns and that this value still reads back `canonical: true`, which
it did.

### Release identifiers

- **`cow_id`: `cow_5657f03c-4ae9-406c-87c6-ea797645fece`**
- **`manifest_sha`: `sha256:fa770afb41e203a187691b5ab75de70990b3aebd1695b57da6986a939af37503`**
- **`version`: `0.9.0`**
- **`release_run_id`: `34480332524`**

### The four bc19 policy labels (for phase 50 seating)

| role | label | owner | `player_id` in the artifact |
|---|---|---|---|
| champion #1 | **`battlecode-bc19-saber:v1`** | daveey | `null` (CI token's own player) |
| champion #2 | **`battlecode-bc19-preachers:v1`** | daveey-1 | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` |
| filler | **`battlecode-saber:v1`** | daveey | `null` |
| filler | **`battlecode-examplefuncsplayer19:v1`** | daveey | `null` |

All four are at `v1` because these four policy **names** are new in this run — each name has
its own independent version counter, so a first upload is always `v1`. The four labels are
distinct because the names are distinct, which is what the exit criterion requires. This
matches the precedent set by every prior year in this repo (the bc16 run's four landed
together at `v4`, bc20's at `v8`, bc21's at `v7`).

`policy_version_id` is `null` on all 36 entries. **This is normal and is not a failure** —
`upload-policy` prints only `Upload complete: <name>:vN` and no UUID. Phase 50 resolves the
UUIDs from `GET /policy-versions` with a client-side filter.

## Notes for phase 50 (league seating)

- Seat champions **`battlecode-bc19-saber:v1`** (daveey) and **`battlecode-bc19-preachers:v1`**
  (daveey-1). Both are LLM prompt policies driven by `PLAYER_PROMPT`, as definition-of-done
  item 4 requires; neither champion is scripted.
- Fillers **`battlecode-saber:v1`** and **`battlecode-examplefuncsplayer19:v1`** are the
  scripted baselines (`PLAYER_SCRIPTED=saber` / `=examplefuncsplayer19`).
- Champion #2 was uploaded while `daveey-1` was the active player, so its version is already
  owned by `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`. Its submit must **not** be re-owned or
  it will 409 "already assigned to player".
- Resolve the four UUIDs from `GET /policy-versions` filtered client-side on these exact
  `<name>:vN` labels. Do not expect them in this artifact.
- The variant to seat is **`bc19`** (`Battlecode 2019 — Crusade (2 seats)`), `num_agents = 2`.
- The coworld to point the league at is `cow_5657f03c-4ae9-406c-87c6-ea797645fece` at `0.9.0`.

## Notes for phase 60 (verification)

- The committed `runs/2026-09-10-battlecode-2019/release-result.json` **is** the artifact from
  run `34480332524`, copied byte-for-byte out of `gh run download … -n release-result`.
  Fallback if it is ever needed:
  `gh run download 34480332524 -R Metta-AI/cogame-battlecode -n release-result`.
- The replay viewer is the **static wasm bundle** (`game.replay_viewer.bundle =
  "static-replay-viewer"`), which is why `certify.replay_liveness` is skipped rather than
  probed. A pod/client replay URL appearing anywhere in phase 60 would be a bug, not a pass.
- The released tree is `f5de5bdbab21fb897f6eb4c27be76a1dced8f6bb`. The phase-30 F6c
  comment-only fix (`src/battlecode/years/bc19/chassis/econ.nim:97-98`) was deliberately
  sequenced to land **after** this dispatch, so `main` will move past `f5de5bdbab…` without
  changing what `0.9.0` contains. `0.9.0` does not include F6c. Verify against
  `f5de5bdbab…`, not against `main`'s head.

## Deviations, blockers, workarounds

None. No retry was consumed, no template delta was needed, no secret was missing, no
workflow order fix was required, and nothing in the design note was found wrong or
impossible. `skip_certify` was never passed; the `policies` override input was never passed.

## `release-result.json` (verbatim, run `34480332524`)

```json
{
  "version": "0.9.0",
  "ok": true,
  "cow_id": "cow_5657f03c-4ae9-406c-87c6-ea797645fece",
  "manifest_sha": "sha256:fa770afb41e203a187691b5ab75de70990b3aebd1695b57da6986a939af37503",
  "canonical": true,
  "hosted_smoke": "passed",
  "hosted_certification": "certifying",
  "certify": {
    "ok": true,
    "replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)",
    "output_tail": "Docker context: default (local images use this store)\nCertifying dist/coworld_manifest.json against transcript coworld-executable\n  [run ] matriculate: manifest conforms to the Coworld schema\n  [pass] matriculate: manifest conforms to the Coworld schema\n  [run ] source-resolves: whether each runnable declares a source_url that resolves to publicly accessible source\n  [pass] source-resolves: whether each runnable declares a source_url that resolves to publicly accessible source\n  [run ] images-reachable: every declared image is pullable or inspectable\n  [pass] images-reachable: every declared image is pullable or inspectable\n  [run ] fixture-conforms: the certification fixture validates against game.config_schema after runner token injection\n  [pass] fixture-conforms: the certification fixture validates against game.config_schema after runner token injection\n  [run ] smoke-episode: the game and certification players run one episode\n  [pass] smoke-episode: the game and certification players run one episode\n  [run ] results-conform: episode results validate against results_schema\n  [pass] results-conform: episode results validate against results_schema\n  [run ] replay-present: a replay artifact was produced\n  [pass] replay-present: a replay artifact was produced\n  [run ] replay-loadable: the replay artifact has a declared viewer path\n  [pass] replay-loadable: the replay artifact has a declared viewer path\n  [run ] players-run: every declared player actually started on the smoke episode (not just declared)\n  [pass] players-run: every declared player actually started on the smoke episode (not just declared)\n  [run ] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks\n  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks\nCertified dist/coworld_manifest.json\nTranscript: coworld-executable (10 steps passed)\nTranscript report: file:///home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-tl_wg3x1/certification_report.html\nArtifacts: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-tl_wg3x1\nResults: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-tl_wg3x1/results.json\nReplay: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-tl_wg3x1/replay\nReplay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)\nLogs: /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-tl_wg3x1/logs\nInspect replay: open /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-tl_wg3x1/replay in your static replay viewer bundle (see STATIC_REPLAY_VIEWERS.md)\nInspect logs: ls /home/runner/work/cogame-battlecode/cogame-battlecode/tmp/coworld-cert-tl_wg3x1/logs\n"
  },
  "policies": [
    {
      "name": "battlecode-loyalist",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-opportunist",
      "version": "v8",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-awu",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-scaffold",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc20-latticer",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc20-rusher",
      "version": "v8",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-bowl-of-chowder",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer",
      "version": "v8",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc21-turtle",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc21-muckrush",
      "version": "v7",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-california-roll",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer21",
      "version": "v7",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc24-fortress",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc24-flagrush",
      "version": "v6",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-gone-sharkin",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer24",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc25-coverage",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc25-siege",
      "version": "v6",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-spaark",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer25",
      "version": "v6",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc23-duel",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc23-alchemist",
      "version": "v5",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-lemonade",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer23",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc22-rush",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc22-transmuter",
      "version": "v5",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-wololo",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer22",
      "version": "v5",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc16-bulwark",
      "version": "v4",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc16-pullers",
      "version": "v4",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-bulwark",
      "version": "v4",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-greenhorn",
      "version": "v4",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc19-saber",
      "version": "v1",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-bc19-preachers",
      "version": "v1",
      "policy_version_id": null,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"
    },
    {
      "name": "battlecode-saber",
      "version": "v1",
      "policy_version_id": null,
      "player_id": null
    },
    {
      "name": "battlecode-examplefuncsplayer19",
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
