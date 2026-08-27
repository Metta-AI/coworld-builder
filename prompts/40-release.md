# Phase 40 — Release

Purpose: get a canonical, certified coworld and the policy versions the league will need.
Owner: **builder**, dispatched by the coordinator — `coworld-release.yml` runs in the coworld
repo (SPEC §Phases, `AGENT.md` §Sub-agents, `agents/builder.md` §Release). No docker in the sandbox.

## Inputs

- `STATE.repo`, `STATE.slug`, `runs/<run>/design.md` (policy prompts and baseline switches).
- `playbooks/make-coworld.md` §Phase 1/2.
- The coworld repo's repo secrets `SOFTMAX_TOKEN` and `ANTHROPIC_API_KEY`, propagated onto each coworld repo by dispatching `propagate-secrets.yml` in `Metta-AI/coworld-builder` (`gh workflow run propagate-secrets.yml -R Metta-AI/coworld-builder -f repo=cogame-<slug>`; it runs with a user token that is admin on Metta-AI repos — no org admin, no value ever in the sandbox) — set in phase 20; if `gh secret list -R Metta-AI/cogame-<slug>` does not show both, dispatch it again before the release.

## Procedure

1. Decide the version: `0.1.0` on the first attempt, then `0.1.1`, `0.1.2`, … Version bumps are
   free and are the documented fix for two distinct failures — use them rather than waiting.
2. Policies come from **`tools/ci/policies.json` in the repo** (scaffolded in phase 20 from
   `templates/tools/ci/policies.json.example`); the `policies` dispatch input is optional and only
   overrides that file for one run.

   **Canonical policy set for every run** (identical content dedupes to one version, so every
   entry must differ in content):

   | role | name | how it runs | owner |
   |---|---|---|---|
   | champion #1 | `<slug>-<prompt-name-1>` | `PLAYER_PROMPT` (LLM prompt policy) | daveey (no `player` field) |
   | champion #2 | `<slug>-<prompt-name-2>` | `PLAYER_PROMPT`, a **different** prompt | daveey-1 (`"player": "ply_bac48eb1-…"`) |
   | fillers | `<slug>-<baseline>` | `PLAYER_SCRIPTED=<baseline>` | daveey |

   **Both champions are LLM prompt policies** — a scripted policy seated as a champion fails
   definition-of-done item 4. **≥1 filler, normally 2**, and every filler is a scripted baseline
   whose version differs from both champions'. Bullwhip's real set (the shape
   `templates/tools/ci/policies.json.example` carries verbatim) was champion #1
   `bullwhip-steady`, champion #2 `bullwhip-forecaster`, fillers `bullwhip-basestock` and
   `bullwhip-mirror`:
   ```json
   [{"name":"<slug>-<prompt-name-1>","run":"/bin/<slug>-player","env":{"PLAYER_PROMPT":"…"}},
    {"name":"<slug>-<prompt-name-2>","run":"/bin/<slug>-player","env":{"PLAYER_PROMPT":"… a different prompt …"},
     "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
    {"name":"<slug>-<baseline-1>","run":"/bin/<slug>-player","env":{"PLAYER_SCRIPTED":"<baseline-1>"}},
    {"name":"<slug>-<baseline-2>","run":"/bin/<slug>-player","env":{"PLAYER_SCRIPTED":"<baseline-2>"}}]
   ```
   The scripted baselines are selected by **`PLAYER_SCRIPTED=<name>`** — the same env var the
   builder brief names (`prompts/20-build.md`), with the baseline's name as its value. There is no
   separate `BASELINE` variable.
   The optional `"player"` field wraps that one `upload-policy` in
   `softmax player use <ply_id>` / `unset` (unset in a `finally`, per policy and around the loop),
   so the version is **owned by daveey-1**. Champion #2 needs this or its submit 409s "already
   assigned to player". Entries also accept `"image"` (override `<IMAGE>:latest`) and `"run"` as a
   string (shlex-split) or an array.
3. Dispatch and block, using the **`dispatch-then-watch` recipe** in
   `playbooks/make-coworld.md` (record `dispatched_at`, poll `gh run list --event
   workflow_dispatch` until a run newer than it appears, then watch that id). A bare
   `gh run list -L 1` right after the dispatch watches the **previous** run and downloads its
   stale `release-result.json` as this dispatch's evidence — do not use it.
   ```bash
   REPO=Metta-AI/cogame-<slug>
   WF=coworld-release.yml
   # POLICIES is only needed to OVERRIDE tools/ci/policies.json for this one dispatch:
   POLICIES=$(jq -c . tools/ci/policies.json)   # or: jq -nc '[{name:…,run:…,env:{…}}, …]'
   dispatched_at=$(date -u +%FT%TZ)
   gh workflow run "$WF" -R "$REPO" --ref main \
     -f version=<v> -f put_secret=true          # add -f policies="$POLICIES" only to override
                                                 # tools/ci/policies.json for this one dispatch.
   # Never pass -f skip_certify=true for a real release: it is a debugging switch and makes
   # release-result.json.certify null (= "not checked"), which cannot satisfy the exit criterion.
   # …then find $RUN with the dispatch-then-watch recipe and:
   gh run watch "$RUN" -R "$REPO" --exit-status || true
   gh run download "$RUN" -R "$REPO" -n release-result -D /tmp/rr
   jq . /tmp/rr/release-result.json
   # PERSIST IT. /tmp does not survive the session, and phase 60 check 7 re-reads this file —
   # usually in a LATER heartbeat with an empty /tmp. Copy it into the run directory, record the
   # release run id in STATE, and commit both.
   mkdir -p runs/<run>
   cp /tmp/rr/release-result.json runs/<run>/release-result.json
   # STATE: coworld.release_run_id = "$RUN"   (phase 60's fallback re-download key)
   ```
4. Read `release-result.json` — never the workflow's colour alone. Require:
   - `canonical == true`
   - `certify.ok == true` and `certify.replay_liveness` contains
     `skipped (static replay bundle declared`
   - `policies[]` has one entry per requested policy (≥4: two champions + ≥1 filler, normally 2) —
     `{"name","version","policy_version_id","player_id"}` —
     with distinct `<name>:vN` labels, and champion #2's `player_id` ==
     `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`.
     **`policy_version_id` is always `null`** (upload-policy prints no uuid). Do not treat that as
     a failure; phase 50 resolves the UUIDs from `GET /policy-versions`, filtered client-side.
   - `secret_put == true`
5. Triage by `step_failed`:
   | `step_failed` / error | Action |
   |---|---|
   | certify: `completed without a replay URL` (artifacts exist in S3) | reconciler race on a cold image — **bump version, re-dispatch**. It passes the second time. Do not debug the game. |
   | upload OK but `canonical == false` | first check the workflow has the "Wait for the uploaded version to become canonical" step (in `templates/coworld-release.yml` since 2026-08-27 — hosted certification settles *after* `--wait-hosted-smoke` returns, and a bump can never outrun that): if missing, add it from the template and re-dispatch; if present and it timed out, read `coworld status <cow_id> --json` from the sandbox and bump only on a genuine completion race. The poll must go through the CLI — a raw HTTPS GET 403s from runners (lux-ai, 2026-08-27). |
   | certify: `did not answer a WebSocket Ping with Pong` (`game_contract_violation` in smoke-episode) | the forked server's `websocketHandler` lost coworld-ctf's `Ping → Pong` branch — restore it, push, re-dispatch (lux-ai 0.1.0, 2026-08-27). |
   | `upload-policy`: "Docker image is not available locally" | workflow ran policies after `upload-coworld` — fix `coworld-release.yml` order, push, re-dispatch. |
   | `secret put` 404 | ran before `upload-coworld` — fix order, re-dispatch. |
   | certify: zero episodes / no schedule | `num_agents` missing from a variant or the cert fixture — fix the manifest, push, re-dispatch. |
   | certify: replay-liveness **not** skipped | manifest does not declare the static bundle — fix, push, re-dispatch. |
   | manifest validation error on docs/protocols | `game.docs` needs `{readme,pages[]}` shape, `game.protocols` needs BOTH `player` and `global`. |
6. Ship small fixes as version bumps during the run rather than batching them.

## Exit criterion

`release-result.json` with `ok: true`, `canonical: true`, `certify` non-null and its
`replay_liveness` containing `skipped (static replay bundle declared`, one `policies[]` entry per
requested policy with distinct `<name>:vN` labels, champion #2's `player_id` ==
`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`, and `secret_put: true`.

## Writes

- `runs/<run>/release-result.json` — the successful dispatch's `release-result` artifact, copied
  out of `/tmp/rr` and **committed and pushed**. Phase 60 check 7 reads this committed copy
  (`prompts/60-verify.md` check 7); `/tmp` is gone by then. Overwrite it on every successful
  re-dispatch so it always matches `coworld.version`.
- STATE: `coworld.version`, `coworld.cow_id`, `coworld.manifest_sha`,
  `coworld.release_run_id` (the GitHub Actions run id of the dispatch this result came from —
  phase 60's fallback is `gh run download "$release_run_id" -R <repo> -n release-result`),
  `policies.champion1` (the daveey-owned LLM prompt policy), `policies.champion2` (the
  daveey-1-owned LLM prompt policy), `policies.fillers[]` (the scripted baselines) — all as
  `<name>:vN` **labels** (UUIDs are not available yet; phase 50 resolves them into
  `policies.filler_version_ids[]` and never overwrites these names),
  `phase_attempts["40"]`, `phase: "50"`, `heartbeat_at`.
- `log.md`: one line per dispatch — version, run id, `step_failed`, decision.
- Asana: complete the phase-40 subtask; comment with `cow_id`, version, and the release run URL.

## Retry budget

3 dispatches, each with a **different** change (bump only, manifest fix, workflow-order fix — say
which in `log.md`). A cert failure surviving three distinct fixes → `prompts/90-blocked.md`.
