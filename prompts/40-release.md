# Phase 40 — Release

Purpose: get a canonical, certified coworld and the policy versions the league will need.
Owner: coordinator dispatching `coworld-release.yml` in the coworld repo. No docker in the sandbox.

## Inputs

- `STATE.repo`, `STATE.slug`, `runs/<run>/design.md` (policy prompts and baseline switches).
- `playbooks/make-coworld.md` §Phase 1/2.
- Org secrets `SOFTMAX_TOKEN`, `ANTHROPIC_API_KEY` on `Metta-AI` (used by CI, never by the agent).

## Procedure

1. Decide the version: `0.1.0` on the first attempt, then `0.1.1`, `0.1.2`, … Version bumps are
   free and are the documented fix for two distinct failures — use them rather than waiting.
2. Compose the `policies` input — **five distinct versions** (two champions + three fillers), because identical content dedupes to
   one version and fillers must differ from champions:
   ```json
   [{"name":"<slug>-steady","run":"/bin/<slug>_player","env":{"PLAYER_SCRIPTED":"1"}},
    {"name":"<slug>-basestock","run":"/bin/<slug>_player","env":{"PLAYER_SCRIPTED":"1","BASELINE":"basestock"}},
    {"name":"<slug>-mirror","run":"/bin/<slug>_player","env":{"PLAYER_SCRIPTED":"1","BASELINE":"mirror"}},
    {"name":"<slug>-forecaster","run":"/bin/<slug>_player","env":{"PLAYER_PROMPT":"…"}},
    {"name":"<slug>-hedger","run":"/bin/<slug>_player","env":{"PLAYER_PROMPT":"…"},
     "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"}]
   ```
   The optional `"player"` field wraps that one `upload-policy` in
   `softmax player use <ply_id>` / `unset`, so the version is **owned by daveey-1**. Champion #2
   needs this or its submit 409s "already assigned to player".
3. Dispatch and block:
   ```bash
   REPO=Metta-AI/cogame-<slug>
   gh workflow run coworld-release.yml -R "$REPO" --ref main \
     -f version=<v> -f policies="$POLICIES" -f put_secret=true
   RUN=$(gh run list -R "$REPO" -w coworld-release.yml -L 1 --json databaseId -q '.[0].databaseId')
   gh run watch "$RUN" -R "$REPO" --exit-status || true
   gh run download "$RUN" -R "$REPO" -n release-result -D /tmp/rr
   jq . /tmp/rr/release-result.json
   ```
4. Read `release-result.json` — never the workflow's colour alone. Require:
   - `canonical == true`
   - `certify.ok == true` and `certify.replay_liveness` contains
     `skipped (static replay bundle declared`
   - `policies[]` has one entry per requested policy, each with a distinct `policy_version_id`, and champion #2's entry is owned by `daveey-1`
   - `secret_put == true`
5. Triage by `step_failed`:
   | `step_failed` / error | Action |
   |---|---|
   | certify: `completed without a replay URL` (artifacts exist in S3) | reconciler race on a cold image — **bump version, re-dispatch**. It passes the second time. Do not debug the game. |
   | upload OK but `canonical == false` | completion race — bump version, re-dispatch. |
   | `upload-policy`: "Docker image is not available locally" | workflow ran policies after `upload-coworld` — fix `coworld-release.yml` order, push, re-dispatch. |
   | `secret put` 404 | ran before `upload-coworld` — fix order, re-dispatch. |
   | certify: zero episodes / no schedule | `num_agents` missing from a variant or the cert fixture — fix the manifest, push, re-dispatch. |
   | certify: replay-liveness **not** skipped | manifest does not declare the static bundle — fix, push, re-dispatch. |
   | manifest validation error on docs/protocols | `game.docs` needs `{readme,pages[]}` shape, `game.protocols` needs BOTH `player` and `global`. |
6. Ship small fixes as version bumps during the run rather than batching them.

## Exit criterion

`release-result.json` with `ok: true`, `canonical: true`, static replay liveness skipped, one
distinct policy version id per requested policy (champion #2's owned by `daveey-1`), and
`secret_put: true`.

## Writes

- STATE: `coworld.version`, `coworld.cow_id`, `coworld.manifest_sha`,
  `policies.champion1`, `policies.champion2`, `policies.fillers[]` (names `:vN`) plus the
  `policy_version_id` UUIDs, `phase_attempts["40"]`, `phase: "50"`, `heartbeat_at`.
- `log.md`: one line per dispatch — version, run id, `step_failed`, decision.
- Asana: complete the phase-40 subtask; comment with `cow_id`, version, and the release run URL.

## Retry budget

3 dispatches, each with a **different** change (bump only, manifest fix, workflow-order fix — say
which in `log.md`). A cert failure surviving three distinct fixes → `prompts/90-blocked.md`.
