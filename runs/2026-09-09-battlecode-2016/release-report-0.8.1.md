# Release report — cogame-battlecode 0.8.1 (bc16 re-release)

Run: `2026-09-09-battlecode-2016` · Repo: `Metta-AI/cogame-battlecode` · Phase 60 re-release
(not a first release; 0.8.0 shipped earlier this run and is preserved beside this file as
`release-result-0.8.0.json` / `release-report-0.8.0.md`).

## Why this release exists

The shipped 0.8.0 static replay bundle rendered bc22's "THE SINGULARITY CAME AT ROUND 3000…"
win-condition clause on a **bc16** endcard, with a squeezed headline and clipped doctrine panels.
PR #12 (`bc16 endcard: year-guard the shared win-condition clause, unsqueeze the card`) fixed all
three. It is viewer-only (`client/replay_broadcast.html`, `tests/test_viewer.nim`,
`tools/ci/renderer_fixture.html`; +268/−13) — no game code, no rules, no year module. The fix only
reaches spectators once a new coworld version is released and certified, hence 0.8.1.

**No tree change was made for this release.** The version is purely the workflow input
(`design.md:2120` pins the bump convention). Released from `main@1f5cb5cfde657c5c589ac73d823898fe464885ab`.

---

## Step 1 — gate on main CI

| field | value |
|---|---|
| run id | `34371338676` |
| workflow | `CI` |
| branch / head sha | `main` / `1f5cb5cfde657c5c589ac73d823898fe464885ab` |
| attempt | 1 |
| status / conclusion | `completed` / **`success`** |
| rerun needed? | **No.** The known `tar xf nim.tar.gz --strip-components=1` exit-2 `wasm-viewer` toolchain flake did not fire; 0 of the 2 permitted reruns were used. |

All 11 jobs green on attempt 1: `test`, `docker-smoke`, `wasm-viewer`, `parity-oracle`, and the
eight per-year oracles `parity-oracle-bc16`, `-bc20`, `-bc21`, `-bc22`, `-bc23`, `-bc24`, `-bc25`.

---

## Step 2 — the release dispatch

```
dispatched_at=2026-09-09T16:59:48Z
gh workflow run coworld-release.yml -R Metta-AI/cogame-battlecode --ref main \
  -f version=0.8.1 -f put_secret=true
```

Found via the **dispatch-then-watch** recipe (`playbooks/make-coworld.md:39`) — polled
`gh run list --event workflow_dispatch` for a run with `createdAt >= dispatched_at`; never
`gh run list -L 1`.

| field | value |
|---|---|
| release run id | **`34380179056`** |
| url | https://github.com/Metta-AI/cogame-battlecode/actions/runs/34380179056 |
| createdAt | `2026-09-09T16:59:49Z` (≥ `dispatched_at`, so this is our dispatch, not a stale one) |
| head sha | `1f5cb5cfde657c5c589ac73d823898fe464885ab` |
| conclusion | **`success`** |
| dispatches used | **1 of 3** |

No `-f policies=` override was passed — the repo's `tools/ci/policies.json` (32 entries, unchanged)
was used. `-f skip_certify=true` was **never** passed.

Every workflow step succeeded, in the load-bearing order: `Build the Coworld manifest` →
`Certify locally` → `Upload the policies` → `Upload the Coworld` → `Wait for the uploaded version
to become canonical` → `Put the Coworld secret` → `Assemble release-result.json` → `Enforce canonical`.

### Exit criterion, bullet by bullet (read from the artifact, not the green tick)

Artifact: `gh run download 34380179056 -R Metta-AI/cogame-battlecode -n release-result`, persisted
to `runs/2026-09-09-battlecode-2016/release-result.json`.

| bullet | required | read | verdict |
|---|---|---|---|
| `ok` | `true` | `true` | PASS |
| `canonical` | `true` | `true` | PASS |
| `secret_put` | `true` | `true` | PASS |
| `step_failed` | `null` | `null` | PASS |
| `errors` | `[]` | `[]` | PASS |
| `certify.ok` | `true` | `true` | PASS |
| `certify.replay_liveness` | contains `skipped (static replay bundle declared` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` | PASS |
| policies | 32 for 32 requested | 32 entries, 32 distinct `<name>:vN` labels | PASS |

Supporting fields: `version: "0.8.1"`, `hosted_smoke: "passed"`,
`hosted_certification: "certifying"` (at artifact-write time — settled to `certified` in step 3
below, which is the expected sequence).

`policy_version_id` is `null` on all 32 entries. **This is expected and is not a failure** —
`upload-policy` prints only `Upload complete: <name>:vN` and no uuid
(`playbooks/make-coworld.md:94`, `prompts/40-release.md:86`).

### New identifiers

| field | value |
|---|---|
| **new `cow_id`** | `cow_089d7551-1bab-49d6-be88-157149ea97f9` |
| **new manifest sha256** | `sha256:6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9` |
| version | `0.8.1` |
| previous (0.8.0) `cow_id` | `cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a` (superseded) |
| previous (0.8.0) manifest sha | `sha256:20a188ec8ada2b62879e5bb25065b3076e8dc190d6457a38538aabafb8a8419f` |

A changed `cow_id` after a re-release is expected, always — cow ids are per-version, only the newest
row is canonical, and `game.canonical_coworld_id` auto-follows (`playbooks/make-coworld.md`, cogball 0.1.5).

---

## Policy dedupe check — **they did NOT dedupe; all four bc16 policies minted `:v2`**

The brief expected identical policy content to dedupe onto the existing `:v1` versions. **It did
not.** Every one of the 32 policies minted a fresh version, incremented by exactly one:

| policy | role | 0.8.0 label | **0.8.1 label** |
|---|---|---|---|
| `battlecode-bc16-bulwark` | bc16 champion #1 (daveey) | `v1` | **`v2`** |
| `battlecode-bc16-pullers` | bc16 champion #2 (daveey-1) | `v1` | **`v2`** |
| `battlecode-bulwark` | bc16 filler (scripted `bulwark`) | `v1` | **`v2`** |
| `battlecode-greenhorn` | bc16 filler (scripted `greenhorn`) | `v1` | **`v2`** |

The same happened across the board: `battlecode-bc20-*` v5→v6, `bc21-*` v4→v5, `bc24-*`/`bc25-*`
v3→v4, `bc22-*`/`bc23-*` v2→v3. `battlecode-bc16-pullers:v2` is correctly owned by
`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` (daveey-1).

This matches `playbooks/make-coworld.md` §Phase 2, which is explicit: *"Every `upload-policy` call
mints a fresh `vN`, even for byte-identical content (observed across three dispatches,
cogame-knights-archers 2026-08-26 — the earlier 'identical content dedupes' note is wrong)."*
It also matches this repo's own history, visible in `release-result-0.8.0.json`: bc20 policies were
already at `v5` after five releases. Dedupe is not the platform's behaviour and never was.

### The league entrants are **not** orphaned

Minting `:v2` **adds** a version; it does not replace or delete `:v1`. Verified against
`GET /policy-versions` (paginated, filtered client-side) — all four UUIDs the bc16 league
submissions point at still resolve, with unchanged ids and owners:

```
battlecode-bc16-bulwark:v1   c073ca20-f820-403f-86c7-8cbd8d704084   owner=daveey     <- league entrant, INTACT
battlecode-bc16-bulwark:v2   062b194e-7cfb-4180-9426-6cfe636b8a2a   owner=daveey     <- new, unreferenced
battlecode-bc16-pullers:v1   2175495c-757d-451e-a3e3-b3ed6f20692b   owner=daveey-1   <- league entrant, INTACT
battlecode-bc16-pullers:v2   4780b64b-6bf4-415b-8d42-da3b6b25bf8b   owner=daveey-1   <- new, unreferenced
battlecode-bulwark:v1        99053bee-f15a-4b03-bfa8-51f2e915814a   owner=daveey     <- filler, INTACT
battlecode-bulwark:v2        86dd30c5-3a28-4559-9f7d-f5203ef8b988   owner=daveey     <- new, unreferenced
battlecode-greenhorn:v1      bb2726bf-0c23-4751-b293-1cc0be05f8ea   owner=daveey     <- filler, INTACT
battlecode-greenhorn:v2      cf2d5113-4695-4d38-b182-cc58435c6960   owner=daveey     <- new, unreferenced
```

So the `:v2` mint is a fact to be aware of, but it is additive and the league's two champion
submissions and two fillers continue to point at live, correctly-owned `:v1` versions. Nothing was
deleted. This is a coordinator decision point, not a builder one — flagged, not acted on.

---

## Step 3 — hosted certification poll, SETTLED

The artifact recorded `hosted_certification: "certifying"` at write time, as expected. Polled with
the CLI (never a raw GET, which 403s — `playbooks/make-coworld.md:353`):

```bash
uvx --from 'coworld[auth]==0.1.43' softmax set-token "$SOFTMAX_TOKEN"   # sandbox CLI needs a login
uvx --from 'coworld[auth]==0.1.43' coworld status cow_089d7551-1bab-49d6-be88-157149ea97f9 --json
```

Settled on the first authenticated poll at `2026-09-09T17:14:28Z`.

### Verbatim evidence — `.certification`

```json
{
  "coworld_id": "cow_089d7551-1bab-49d6-be88-157149ea97f9",
  "state": "certified",
  "certified": true,
  "contract_version": "main-935475525ce0",
  "certification_job_id": "fc4250f2-6d88-4180-ac09-a47d7af4e8d6",
  "failed_step": null,
  "failure": null,
  "transcript_summary": [
    {"id": "matriculate",       "status": "pass"},
    {"id": "source-resolves",   "status": "pass"},
    {"id": "images-reachable",  "status": "pass"},
    {"id": "fixture-conforms",  "status": "pass"},
    {"id": "smoke-episode",     "status": "pass"},
    {"id": "results-conform",   "status": "pass"},
    {"id": "replay-present",    "status": "pass"},
    {"id": "replay-loadable",   "status": "pass"},
    {"id": "players-run",       "status": "pass"},
    {"id": "supporting-roles",  "status": "pass"}
  ],
  "completed_at": "2026-09-09T17:07:59.606824Z"
}
```

### Verbatim evidence — `.coworld`

```json
{
  "id": "cow_089d7551-1bab-49d6-be88-157149ea97f9",
  "name": "battlecode",
  "version": "0.8.1",
  "canonical": true,
  "manifest_hash": "sha256:6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9",
  "size_bytes": 40837
}
```

### Required assertions

| assertion | read | verdict |
|---|---|---|
| `.certification.state == "certified"` | `certified` | PASS |
| `.certification.certified == true` | `true` | PASS |
| `.certification.failed_step` null | `null` | PASS |
| `.certification.failure` null | `null` | PASS |
| `.coworld.canonical == true` | `true` | PASS |
| `.coworld.version == "0.8.1"` | `0.8.1` | PASS |

All 10 certification transcript steps pass. `completed_at` is `2026-09-09T17:07:59.606824Z`.
The hosted `manifest_hash` matches the artifact's `manifest_sha` exactly, confirming the certified
coworld is the one this run uploaded.

---

## Summary

`Metta-AI/cogame-battlecode` **0.8.1** is released, canonical and certified from
`main@1f5cb5cf`, carrying PR #12's bc16 endcard fix. Spectators now get the year-guarded
win-condition clause, the unsqueezed headline and unclipped doctrine panels.

- new `cow_id`: `cow_089d7551-1bab-49d6-be88-157149ea97f9`
- new manifest sha: `sha256:6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9`
- release run: `34380179056` (`success`), main CI gate: `34371338676` (`success`, attempt 1)
- 1 of 3 dispatches used; 0 of 2 permitted CI reruns used
- **open item for the coordinator:** all four bc16 policies minted `:v2` rather than deduping to
  `:v1`; the `:v1` entrants are intact and still referenced, but the coordinator may want to decide
  whether the league should be repointed at `:v2`.
