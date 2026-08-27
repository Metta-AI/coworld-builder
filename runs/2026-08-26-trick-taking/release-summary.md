# Phase 40 — Release summary — cogame-trick-taking

**Result: green on the first dispatch. All exit criteria met.**

| field | value |
|---|---|
| repo | `Metta-AI/cogame-trick-taking` (branch `main`, head `179aa9993c4d1308b1a26945e1d758e63d16957f`) |
| version | `0.1.0` |
| `cow_id` | `cow_0de16cf6-8d0f-4601-8ca7-1c60fc3544d0` |
| `manifest_sha` | `sha256:51bc9a9042ab935a7b2fe0da48bd5547940ca601011e72d8f9750c1b27eeabf1` |
| release run id | `33036293815` |
| release run URL | https://github.com/Metta-AI/cogame-trick-taking/actions/runs/33036293815 |
| run conclusion | `success` (2026-08-27T03:24:58Z → 03:36:13Z) |
| `ok` / `canonical` | `true` / `true` |
| `hosted_smoke` / `hosted_certification` | `passed` / `certified` |
| `certify.ok` | `true` — 10/10 transcript steps passed |
| `certify.replay_liveness` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` |
| `secret_put` | `true` |
| `step_failed` | `null` (`errors: []`) |

## Policy versions

Source: `tools/ci/policies.json` in the repo (no `-f policies=` override was passed). Four
distinct entries, four distinct `<name>:vN` labels.

| role | label | how it runs | owner / `player_id` |
|---|---|---|---|
| champion #1 (daveey, `PLAYER_PROMPT`) | `trick-taking-signaller:v1` | `/bin/trick-taking-player`, `PLAYER_PROMPT` (signalling prompt) | `null` (CI token's own player = daveey) |
| champion #2 (daveey-1, `PLAYER_PROMPT`) | `trick-taking-counter:v1` | `/bin/trick-taking-player`, `PLAYER_PROMPT` (card-counter prompt) | **`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`** |
| filler (scripted) | `trick-taking-follow:v1` | `/bin/trick-taking-player`, `PLAYER_SCRIPTED=follow` | `null` (daveey) |
| filler (scripted) | `trick-taking-tracker:v1` | `/bin/trick-taking-player`, `PLAYER_SCRIPTED=tracker` | `null` (daveey) |

`policy_version_id` is `null` on all four entries — expected (`upload-policy` prints no uuid);
phase 50 resolves the UUIDs from `GET /policy-versions` filtered client-side on `policy_name`
and matched on these exact `<name>:vN` labels.

## Dispatches

| # | version | run id | `step_failed` | decision |
|---|---|---|---|---|
| 1 | `0.1.0` | `33036293815` | `null` — all steps green | **Accepted.** `release-result.json` satisfies every exit criterion; no re-dispatch needed. Retry budget: 1 of 3 used. |

Dispatch command (dispatch-then-watch recipe, `dispatched_at=2026-08-27T03:24:56Z`, run found by
polling `gh run list --event workflow_dispatch` for `createdAt >= dispatched_at`, then
`gh run watch 33036293815`):

```
gh workflow run coworld-release.yml -R Metta-AI/cogame-trick-taking --ref main \
  -f version=0.1.0 -f put_secret=true
```

`-f skip_certify=true` was never passed. Step order in `coworld-release.yml` was verified before
dispatch and is the load-bearing one: build manifest → certify locally → **upload the policies** →
upload the Coworld → **put the Coworld secret** (which reads the namespace from
`dist/coworld_manifest.json`'s `game.name`, not from the slug variable).

## Preflight

- `gh secret list -R Metta-AI/cogame-trick-taking` showed both `SOFTMAX_TOKEN` and
  `ANTHROPIC_API_KEY` (set 2026-08-26T23:39:11Z in phase 20) — `propagate-secrets.yml` did not
  need re-dispatching.
- `tools/ci/policies.json` at `main` was verified to match design.md §Policies exactly: two
  `PLAYER_PROMPT` champions (`trick-taking-signaller`, `trick-taking-counter`) and two
  `PLAYER_SCRIPTED` fillers (`follow`, `tracker`), with champion #2 carrying
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`.

## Files written by this phase

- `runs/2026-08-26-trick-taking/release-result.json` — the `release-result` artifact of run
  `33036293815`, verbatim.
- `runs/2026-08-26-trick-taking/release-summary.md` — this file.

No changes were pushed to `Metta-AI/cogame-trick-taking`; the release ran against the phase-20
head unmodified.
