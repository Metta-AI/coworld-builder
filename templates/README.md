# templates/

Files a coworld-builder agent copies into a freshly created `Metta-AI/cogame-<slug>` repo
(the workflows and the shell/JSON under `tools/`), plus the Asana/Discord/state templates the
coordinator fills in from the sandbox.

The sandbox has **no docker, no nim, no emsdk and no coworld CLI**. Everything that needs one
lives in `ci.yml`, `coworld-release.yml` or `coworld-submit.yml` and runs in GitHub Actions;
the agent pushes, dispatches with `gh workflow run`, polls with `gh run watch`, and reads
results out of the uploaded artifacts.

## Placeholders

Three placeholders appear across the copied files. Substitute all of them before the first
push; a leftover `<` in a workflow is a syntax-valid, semantically dead reference.

| placeholder | meaning | example |
| --- | --- | --- |
| `<slug>` | lowercase game slug. Also the repo suffix (`cogame-<slug>`), the Coworld `game.name`, the secret namespace, the page path `softmax.com/<slug>`, and the binary names `/bin/<slug>` and `/bin/<slug>-player`. | `bullwhip` |
| `<IMAGE>` | local docker image name **without a tag**. Must equal the `image:` in `compose.yaml` minus `:latest`, because `coworld build` builds that tag and `upload-policy` cuts policies from it. | `coworld-bullwhip` |
| `<SEATS>` | seat count (`num_agents`). A **cross-check**, not a fallback: `docker_smoke.sh` takes the seat count solely from `certification.game_config.num_agents` in `coworld_manifest_template.json` and hard-fails if this value disagrees with it. | `4` |

`run-task.md`, `blocked-subtask.md` and `announce.md` carry their own additional
substitutions; each file lists them at the top.

Four other angle-bracket names appear **inside comments and input descriptions only** and are
runtime values, not substitutions — leave them alone: `<run_id>` (a GitHub Actions run id, in
the `gh run download` recipes), `<name>` (a policy name, in the `<name>:vN` input
description), and `<cow_id>` / `<sha>` (in the note about the platform's static replay route
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html`). After substitution, the residue check

```bash
grep -rnE '<[A-Za-z_][A-Za-z0-9_]*>' .github/workflows tools/ci
```

should return exactly those four names and nothing else. Grep for the placeholder *shape*, not
for a bare `<`: the copied files legitimately contain `<<'PY'` heredocs and `slot < seats`
comparisons, and a gate written against a bare `<` false-positives on every one of them.

---

## `ci.yml` → `.github/workflows/ci.yml`

Push/PR/dispatch CI for the coworld repo, and phase 20's exit criterion (green on `main`).
Three jobs.

**`test`** installs nimby to `~/.local/bin` (arch-detected `nimby-Linux-X64` /
`nimby-Linux-ARM64`, pinned by the `NIMBY_VERSION` env), runs `nimby use $NIM_VERSION`,
`nimby --global sync nimby.lock`, then regenerates `nim.cfg` from `~/.nimby/pkgs` — exactly
the Dockerfile build-stage recipe, because the committed `nim.cfg` pins the *author's*
machine paths and is wrong on every other host. It then runs every test file twice: once
debug (`nim r --hints:off --path:src <t>`) and once release
(`nim r --hints:off -d:release --path:src <t>`). Debug catches range and overflow bugs;
release catches compile errors and codegen bugs that a debug-only CI has repeatedly shipped
to production. Three optional **repo variables** narrow that: `NIM_TESTS` (space-separated
file list, default `tests/*.nim`), `NIM_TESTS_DEBUG_ONLY` and `NIM_TESTS_RELEASE_ONLY`
(space-separated file lists to run in one mode only). Set them with
`gh variable set NIM_TESTS --body "tests/test_sim.nim tests/test_bot.nim"`.

**`docker-smoke`** runs `docker build --platform=linux/amd64 -t <IMAGE>:ci .` and then
`tools/ci/docker_smoke.sh <IMAGE>:ci`.

**`wasm-viewer`** runs `tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`
(which falls back to the pinned `emscripten/emsdk:4.0.15` container in
`Dockerfile.replay-viewer`, since the runner has no `emcc`), asserts `index.html` and at
least one non-empty `.wasm` exist, and uploads the bundle as the `static-replay-viewer`
artifact. A bundle that does not build means every hosted replay hangs on the platform's
static viewer route, so this job is not optional.

## `tools/ci/docker_smoke.sh` → `tools/ci/docker_smoke.sh` (chmod +x)

The containerised twin of a local `tmp/run_e2e.sh`: one game container plus one player
container per seat on a per-run docker network (`<slug>-smoke-<pid>-net`, created and removed
by the script), all from the production image.
It reads `coworld_manifest_template.json`, takes `certification.game_config` as the episode
config (injecting `tokens`), and gives each slot the **`run` and `env` of
the manifest player its certification fixture names** — so the smoke plays the same seat mix
the certifier will.

**The seat count is never guessed.** It comes from exactly one place,
`certification.game_config.num_agents`, and a missing, non-integer, or inconsistent value is a
**hard failure** (message prefix `SEAT-COUNT FAIL:`), not a warning — a smoke that quietly
picks a seat count and goes green is a green signal derived from the wrong game, which nothing
downstream re-checks. Four checks fire before any container starts: `num_agents` present;
`num_agents` a positive integer; `len(certification.players)` equal to it; and
`len(certification.game_config.players)` equal to it. `SMOKE_SEATS` / `<SEATS>` is an
independent second declaration substituted at scaffold time from the design note and is
verified to agree — a non-numeric value means the placeholder was never substituted, which the
phase-20 placeholder gate catches separately, so it is ignored here. The game gets the `COGAME_*` contract with `file:///coworld/...` URIs
against a bind-mounted temp dir; each player gets
`COWORLD_PLAYER_WS_URL=ws://<prefix>-game:8080/player?slot=N&token=token-N`. It asserts the
game container exits 0, `results.json` is valid UTF-8 JSON with `names`/`scores` of the right
length, `replay.json` is non-empty (and parses as JSON unless told otherwise), and no
`player_failure.json` was written; on any failure it dumps every container's logs.

Overridable by env: `SMOKE_IMAGE`, `SMOKE_SLUG`, `SMOKE_GAME_BIN` (default `/bin/<slug>`),
`SMOKE_PLAYER_BIN` (default `/bin/<slug>-player`), `SMOKE_MANIFEST`, `SMOKE_SEATS`
(cross-check, see above),
`SMOKE_PORT` (8080), `SMOKE_TIMEOUT` (900), `SMOKE_REQUIRE_REPLAY_JSON` (1 — set `0` for a
binary replay format such as CTF's `.bitreplay`), `SMOKE_EXTRA_ENV` (`"K=V K=V"` applied to
every player). If `ANTHROPIC_API_KEY` is present it is forwarded to the game container so the
LLM path is exercised; CI does not set it, which is deliberate — the game must complete on
its scripted baselines with no credentials at all.

## `coworld-release.yml` → `.github/workflows/coworld-release.yml`

`workflow_dispatch` only. Inputs: **`version`** (required, `MAJOR.MINOR.PATCH`),
**`policies`** (JSON array of `{name, run, env:{...}}`; empty ⇒ read `tools/ci/policies.json`
from the repo), **`secret_key_name`** (default `anthropic_api_key`), **`put_secret`**
(default true), **`skip_certify`** (default false, debugging only).
`concurrency: coworld-release`, `cancel-in-progress: false` — a killed upload can leave a
half-published version behind.

The step order is load-bearing and is the whole point of the file:

1. `softmax set-token "$SOFTMAX_TOKEN"` via `uvx --from "coworld[auth]==0.1.38"`.
2. `coworld build --version $VERSION --project . --compose compose.yaml --template coworld_manifest_template.json --output dist/coworld_manifest.json`.
3. `coworld certify dist/coworld_manifest.json`, teed to an artifact, and **failed unless the
   output contains `Replay liveness: skipped (static replay bundle declared`** — that line is
   the proof the replay ships as a static bundle rather than a `/client/replay` pod.
4. `coworld upload-policy <IMAGE>:latest --name <name> --run <argv…> [--secret-env K=V …]`
   for every policy. **Before** step 5: observed, `upload-policy` reports the local image
   missing when it runs after `upload-coworld` (the ordering is empirical — no prune or
   `rmi` exists in the CLI — but it is reproducible). `run` may be a string (shell-split) or an array; a policy may
   override `image`. The command is never echoed — `--secret-env` values are secrets.
   A policy entry may also carry **`"player": "ply_…"`**: that one upload is wrapped in
   `softmax player use <ply_id>` … `softmax player unset`, so the version is *owned* by that
   identity. This is not cosmetic — a version uploaded as `daveey` cannot later be submitted
   as `daveey-1` (409 "already assigned to player"), so champion #2 must be uploaded while
   `daveey-1` is active, and CI is the only place `softmax player use` can run. The unset
   runs in a `finally` at both the per-policy and whole-step level, so no failure can leave
   the runner — or the later `upload-coworld` / `secret put` steps — impersonating anyone.
5. `coworld upload-coworld dist/coworld_manifest.json --timeout-seconds 900
   --wait-hosted-smoke --hosted-smoke-timeout-seconds 1800`.
6. `coworld secret put <slug> <secret_key_name> <tmpfile>` with `ANTHROPIC_API_KEY` written to
   a mode-600 temp file that is deleted immediately. **After** step 5: the secret namespace
   does not exist until the Coworld does.

It parses `Coworld: cow_…`, `Manifest hash: sha256:…`, `Canonical: yes|no`,
`Hosted smoke certification: passed` and each `Upload complete: <name>:vN`, writes them to
`$GITHUB_STEP_SUMMARY` as a table, and — **always, even on failure** — uploads
`release-result.json` as the artifact **`release-result`**:

```json
{"version":"0.1.2","ok":true,"cow_id":"cow_…","manifest_sha":"sha256:…","canonical":true,
 "hosted_smoke":"passed","hosted_certification":"passed",
 "certify":{"ok":true,"replay_liveness":"Replay liveness: skipped (static replay bundle declared…)","output_tail":"…"},
 "policies":[{"name":"bullwhip-steady","version":"v1","policy_version_id":null,"player_id":null},
             {"name":"bullwhip-forecaster","version":"v1","policy_version_id":null,
              "player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"}],
 "secret_put":true,"errors":[],"step_failed":null}
```

(`policy_version_id` is always `null`: `upload-policy` prints only `name:vN`. `player_id` is
`null` when the policy was uploaded as the `SOFTMAX_TOKEN` owner.) The raw
`certify.log`, `upload.log` and built manifest go up as **`release-logs`**. A final step fails
the job if `canonical` is not `true`. Read it back with:

```bash
gh run download <run_id> -R Metta-AI/cogame-<slug> -n release-result -D /tmp/rr
jq . /tmp/rr/release-result.json
```

Requires org secrets `SOFTMAX_TOKEN` and `ANTHROPIC_API_KEY` on `Metta-AI`.

## `coworld-submit.yml` → `.github/workflows/coworld-submit.yml`

`workflow_dispatch` with `player_id`, `policy` (`<name>:vN`) and `league_id`. Runs
`softmax player use <player_id>` → `coworld submit <policy> --league <league_id>
--no-open-browser` → `softmax player unset` in an `always()` step, so a failed run never
leaves the runner impersonating someone. Uploads `submit-result.json` as artifact
**`submit-result`**: `{"ok", "player_id", "policy", "league_id", "exit_code", "output_tail",
"error"}`. Phase 50 dispatches it twice — once as `daveey`, once as `daveey-1` — because
champion submission has no HTTPS endpoint and the sandbox has no CLI. Slug-independent: no
placeholders to substitute. Requires `SOFTMAX_TOKEN`.

## `tools/ci/policies.json.example` → `tools/ci/policies.json`

The default policy set `coworld-release.yml` uploads when its `policies` input is empty.
A JSON array of `{"name", "run", "env":{…}}` with two optional keys, `"image"` (override the
default `<IMAGE>:latest`) and `"player"` (`ply_…` — upload this one version *as* that
identity). `run` is the in-image entrypoint (`/bin/<slug>-player`) and every `env` entry
becomes a `--secret-env K=V` on the policy version. The example is the Bullwhip set: two LLM
policies whose whole strategy is their `PLAYER_PROMPT` (`bullwhip-steady` = champion #1,
uploaded as the token owner `daveey`; `bullwhip-forecaster` = champion #2, carrying
`"player": "ply_bac48eb1-…"` so it is owned by `daveey-1`) plus two scripted baselines
(`bullwhip-basestock`, `bullwhip-mirror`, selected with `PLAYER_SCRIPTED`) — the shape every
coworld inherits, an LLM policy and a scripted baseline from the same image, env-switched.
Copy to `tools/ci/policies.json` and replace with the game's own set; keep filler versions
distinct from champion versions.

## `STATE.template.json` → `runs/<run>/STATE.json` (in **this** repo, not the coworld repo)

The `SPEC.md` §State schema with empty values — **every** field SPEC §State defines, including
`coworld.release_run_id` (phase 40), `policies.filler_version_ids` (phase 50),
`announce.attempted_at` (phase 70), and the heartbeat trio `session_ended_at` / `session_id`
(phase 00). A phase told to write "from `templates/STATE.template.json`" must find its key here.
`phase` starts at `"00"`, `review_round` at `0`, `blocked` at `null`. Written by phase 00, rewritten and pushed on every heartbeat and
every phase transition; it is the record that a resumed run reads to know where it was.

## `run-task.md` → the Asana run task on the Coworld Builder board

Title pattern `RUN <slug> — <idea title>`, description with the idea/repo/run/CI links, the
00…80 phase checklist, and the `heartbeat_at:` line the coordinator rewrites in place. The
task is the lock: a fresh `heartbeat_at` (< 90 min) means another run is live and the
heartbeat exits; a stale one means the run is yours to resume at `STATE.json.phase`.
Substitutions listed in the file.

## `blocked-subtask.md` → a subtask of the run task, assigned to David Bloomin

Title `BLOCKED <slug> @<phase>: <one-line ask>`; body = the verbatim failure, the three
*distinct* attempts, the single decision/credential/action needed, and the
`Resume: complete this subtask; the next heartbeat resumes at phase <n>` line. Includes the
list of things that must **never** be filed as blocked because the rails say the coordinator
decides them itself.

## `announce.md` → the Discord `#coworlds` post (phase 70)

The message shape — title + `softmax.com/<slug>` link, two paragraphs (what the game is /
the catch), a **"A policy is just a prompt."** entry paragraph, what the replay shows, and
the repo link — capped at **1800 characters**, with the actual Bullwhip post (1,589 chars)
as the worked example and a note on what that example does right.
