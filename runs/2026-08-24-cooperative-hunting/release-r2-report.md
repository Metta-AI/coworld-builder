# Release r2 — cooperative-hunting (version 0.1.3)

## Fix applied this round

- **sha `5ac03d9081cf8584bbf8f987c07d15efcc775edd`** — `ci(release): give certify
  --timeout-seconds 300 so the fixture can finish`
  (`.github/workflows/coworld-release.yml`, "Certify locally" step: added
  `--timeout-seconds 300`; `--no-open-report` and the `tee "$RR/certify.log"` untouched).
  Pushed to `main` via the Git Data API (plain https push is unauthenticated for this token).
  Verified against the CLI: `coworld certify --timeout-seconds` exists, `[default: 60.0]`.
- **CI run `32807756637`** on that sha — `completed / success` (test, docker-smoke, wasm-viewer).
  <https://github.com/Metta-AI/cogame-cooperative-hunting/actions/runs/32807756637>
- Repo secrets verified present before dispatch: `SOFTMAX_TOKEN`, `ANTHROPIC_API_KEY`
  (`gh secret list -R Metta-AI/cogame-cooperative-hunting`, both 2026-08-24T15:42:19Z) —
  no re-propagation needed.

## Release dispatch

- version `0.1.3`, `put_secret=true`, no `skip_certify`, policies from `tools/ci/policies.json`
  (not overridden). Run id **`32808207318`** —
  <https://github.com/Metta-AI/cogame-cooperative-hunting/actions/runs/32808207318> —
  conclusion **failure**, `step_failed: "Upload the Coworld"`.

The certify fix worked: `Certify locally` passed for the first time (10/10 checks, ~2 min),
and `Upload the policies` passed (all four versions created). The run then failed one step
later, at `upload-coworld`, on a **new and unrelated** failure class.

### Exit-criterion checklist (release-result.json of run 32808207318)

| item | result | evidence |
|---|---|---|
| `ok: true` | **false** | `ok: false`, `step_failed: "Upload the Coworld"` |
| `canonical: true` | **false** | `canonical: null` (upload never completed) |
| `certify.ok: true` | **true** | `certify.ok: true`, exit 0, 10 steps passed |
| `certify.replay_liveness` contains `skipped (static replay bundle declared` | **true** | `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"` |
| 4 `policies[]` with distinct `<name>:vN` | **true** | `cooperative-hunting-pack-caller:v1`, `cooperative-hunting-quartermaster:v1`, `cooperative-hunting-biggame:v1`, `cooperative-hunting-sidekick:v1` |
| champion #2 `player_id == ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` | **true** | `cooperative-hunting-quartermaster` → `player_id: "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the other three `null` (`policy_version_id` null throughout, expected) |
| `secret_put: true` | **false** | `secret_put: false` — the step is skipped when upload fails |
| `cow_id` | — | `null` |
| `manifest_sha` | — | `null` |

### The blocking error (release-logs/upload.log tail)

```
RuntimeError: Request to POST /api/observatory/v2/coworlds/upload failed with HTTP 400:
{"detail":"Coworld manifest is invalid: Coworld secret cooperative-hunting/anthropic_api_key
cannot be used by Coworld 'cooperative_hunting'"}
```

Root cause — a **naming inconsistency inherited from the design note**, not a race and not a
certify problem. The server requires the Coworld-secret namespace in a `secret://coworld/<ns>/…`
reference to equal the Coworld's own name:

- `game.name` is `cooperative_hunting` (underscore) — design.md line 3 pins it, and
  `tools/build_manifest.py:625` / `coworld_manifest_template.json:15` emit it; the replay writer
  also stamps `"coworld": "cooperative_hunting"`.
- the runnable env references `secret://coworld/cooperative-hunting/anthropic_api_key` (hyphen) —
  design.md line 712, `tools/build_manifest.py:641`, `coworld_manifest_template.json:27`.
- `.github/workflows/coworld-release.yml:62` sets `SLUG: cooperative-hunting`, and `SLUG` is used
  for nothing except `coworld secret put "$SLUG" …` / `coworld secret list "$SLUG"` (lines
  359–362), i.e. the same hyphenated namespace.

This is the `manifest validation error` row of `prompts/40-release.md` §5 (fix, push,
re-dispatch), but it is a **fourth distinct fix** and the r2 brief's stop-rule applies to the
certify step only, so the decision was escalated rather than taken unilaterally.

### Proposed fix (not applied — awaiting the coordinator's go/no-go)

Keep the Coworld name the design pins (`cooperative_hunting`) and move the secret namespace onto
it — three occurrences, no game-code change:

1. `tools/build_manifest.py:641` → `secret://coworld/cooperative_hunting/anthropic_api_key`
2. `coworld_manifest_template.json:27` → same value
3. `.github/workflows/coworld-release.yml:62` → `SLUG: cooperative_hunting` (only consumer is the
   `coworld secret put` / `secret list` namespace, so the put lands in the namespace the manifest
   now references; `ci.yml`'s `SLUG` is a separate image/repo slug and stays hyphenated)

The alternative — renaming the Coworld to `cooperative-hunting` — contradicts design.md line 3
and would also touch the replay header and the docs, so it is not recommended.

Then re-dispatch as version `0.1.4` (versions are cheap; `0.1.3` already created the four policy
versions, which are content-addressed and will dedupe rather than duplicate).
