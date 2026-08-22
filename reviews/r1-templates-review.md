# R1 — `templates/` CI review

Reviewed at `coworld-builder@b0836af` (working tree clean). Ground truth:
`/Users/daveey/code/cogame-bullwhip` (Dockerfile, Dockerfile.replay-viewer, compose.yaml,
tools/build_replay_viewer.sh, coworld_manifest_template.json, tmp/run_e2e.sh), the precedent
`/Users/daveey/code/cogame-factorio/.github/workflows/ci.yml`, and the **actual `coworld` CLI
source** unpacked from the uv cache (0.1.34 at
`~/.cache/uv/archive-v0/Zveif8g6Ow4mr73LNwBPr/coworld`, 0.1.38 at `.../qMrFt_bzTnDB4cPyN8MgU`,
0.1.39 at `.../z-wG7jhwBPuo_X9qctdGN`).

Note: `templates/tools/ci/docker_smoke.sh`, `templates/README.md` and `prompts/{20,30,40,50}`
were rewritten by another agent mid-review (seat-count cross-check work, commits `29b3e04`,
`aa922f8`, `e462c71`). Everything below was re-read and re-executed against the current tree.

---

## 1. Per-file trace

### `templates/ci.yml`
Push/PR/dispatch. Top-level `env` = `SLUG`, `IMAGE`, `NIMBY_VERSION 0.1.26`, `NIM_VERSION 2.2.4`
(all literals — no expression contexts, so the file parses). Three independent jobs, no `needs`.

- **`test`** (L37–144): checkout → cache `~/.nimby` + `~/.cache/nim` → arch-detect and download
  `nimby-Linux-{X64,ARM64}` pinned by `NIMBY_VERSION` → `nimby use $NIM_VERSION` → `nimby --global
  sync nimby.lock` (skipped if absent) → **regenerate `nim.cfg`** from `~/.nimby/pkgs/*` and append
  `--path:"src"`. That is byte-for-byte the recipe in bullwhip's `Dockerfile` L37–42, so a green
  `test` really does mean "the image's compiler and package tree agree". Pins match bullwhip's
  Dockerfile (nimby 0.1.26 / Nim 2.2.4). Note bullwhip's `Dockerfile.replay-viewer` pins nimby
  **0.1.27**, deliberately un-mirrored.
  Test loop (L109–144): `set -uo pipefail` (no `-e`, deliberate — it accumulates `fail` instead of
  aborting), default `tests/*.nim`, each file run debug **and** `-d:release`, narrowed by repo
  variables `NIM_TESTS`/`NIM_TESTS_DEBUG_ONLY`/`NIM_TESTS_RELEASE_ONLY`. Empty test set is a hard
  error. Correct, and it closes the "CI runs DEBUG only" hole.
- **`docker-smoke`** (L150–161): `docker build --platform=linux/amd64 -t "${IMAGE}:ci" .` then
  `bash tools/ci/docker_smoke.sh "${IMAGE}:ci"`. Identical shape to factorio's precedent
  (`ci.yml:57–60`). Sets no `SMOKE_*` env, so the script's scaffold-substituted defaults are what
  gets exercised — including `<SEATS>`, which is what makes the new cross-check meaningful.
- **`wasm-viewer`** (L170–201): `bash tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`,
  then asserts non-empty `index.html` and ≥1 non-empty `*.wasm`, then uploads `static-replay-viewer`.
  Matches bullwhip's hook contract (one absolute-path argument; the hook falls back to the pinned
  `emscripten/emsdk:4.0.15` container). **But it invokes the hook via `bash`, which ignores the
  file's exec bit — and `coworld build` hard-requires that bit.** See BLOCKING-4.

### `templates/coworld-release.yml`
`workflow_dispatch` only; inputs `version` (required, regex-validated `MAJOR.MINOR.PATCH`),
`policies`, `secret_key_name` (default `anthropic_api_key`), `put_secret` (default true),
`skip_certify` (default false). `concurrency: coworld-release`, `cancel-in-progress: false` — right
call for a non-idempotent publish.

Step order, traced: `Validate inputs` → `Authenticate to Softmax` → `Resolve the policy list` →
`Build the Coworld manifest` → `Certify locally` → **`Upload the policies`** → `Upload the Coworld`
→ `Put the Coworld secret` → `Assemble release-result.json` (`always()`) → two artifact uploads
(`always()`) → `Enforce canonical`.

**The mandated order holds**: build → certify → upload every policy → `upload-coworld
--wait-hosted-smoke` → `coworld secret put`. Policies precede `upload-coworld`; `secret put`
follows it. `Assemble` and both uploads run before `Enforce canonical`, so the artifact exists even
when the canonical gate fails — that is the right sequencing and prompt 40 depends on it.

Verified against the real CLI:
- `coworld build` (bundle.py L23–75) runs `docker compose pull` then **`docker compose build
  --pull`**, so `${IMAGE}:latest` genuinely exists locally by the time `upload-policy` runs — this
  is why `<IMAGE>` must equal compose's `image:` minus `:latest`. It also invokes the replay-viewer
  hook and writes the bundle next to the output manifest.
- `upload-policy` prints `Upload complete: {name}:v{version}` (upload.py L1383) — the workflow's
  `^Upload complete: (\S+):(v\d+)$` matches exactly.
- `upload-coworld` prints `Hosted smoke certification: passed`, `Upload complete: <name>:<semver>`,
  `Coworld: cow_…`, `Manifest hash: sha256:…`, `Canonical: yes|no`, `Hosted certification: <state>`
  (upload.py L1319–1335) — every regex in the parse block matches.
- Every option used (`--timeout-seconds`, `--wait-hosted-smoke`,
  `--hosted-smoke-timeout-seconds`, `--name`, `--run`, `--secret-env`, `--compose`, `--template`,
  `--output`) exists in 0.1.34 **and** in 0.1.38.
- `coworld secret list` (cli.py L203–222) prints only name/owner/size/updated — **no value**. No
  secret leak there. `ANTHROPIC_API_KEY` goes to a `mktemp` + `chmod 600` file, is never echoed, and
  is removed. Clean.

Champion-#2 identity handling (L200–262) is the strongest part of the file: `softmax player use
<ply>` wraps exactly one `upload-policy`, `unset` runs in a per-policy `finally` **and** in a
whole-loop `finally`, and a failed `player use` is recorded as a failure rather than silently
uploading as the token owner. The command line is deliberately not echoed because `--secret-env`
values ride on it.

`release-result.json` (L339–391) emits `version, ok, cow_id, manifest_sha, canonical, hosted_smoke,
hosted_certification, certify{ok,replay_liveness,output_tail}, policies[{name,version,
policy_version_id,player_id}], secret_put, errors[], step_failed`. `current_step` is written at the
top of each step, so `step_failed` names the step that died.

### `templates/coworld-submit.yml`
Slug-independent. `player_id`/`policy`/`league_id`, `concurrency: coworld-submit`,
`cancel-in-progress: false`. `softmax player use` → `coworld submit "$POLICY" --league "$LEAGUE_ID"
--no-open-browser` (both options confirmed present in 0.1.34 cli.py L776–806) → `player unset` in an
`always()` step → `submit-result.json` in an `always()` step → artifact `submit-result`. If
`player use` fails, `set -e` kills the step before `$SR/rc` is written and Assemble reports
`{"ok": false, "exit_code": null, "error": "submit did not run"}` — degraded but consumable.

### `templates/tools/ci/docker_smoke.sh`
Containerised twin of `tmp/run_e2e.sh`. Reads `certification.game_config` as the episode config,
injects `tokens` (`token-N`), maps each cert slot's `player_id` onto the manifest's `player[]` entry
to reuse its `run` and `env` — so the smoke plays the certifier's seat mix. Game gets
`COGAME_HOST/PORT/CONFIG_URI/RESULTS_URI/SAVE_REPLAY_URI/PLAYER_FAILURE_URI` against a bind-mounted
tmpdir; players get `COWORLD_PLAYER_WS_URL=ws://<prefix>-game:8080/player?slot=N&token=token-N`.
**All six `COGAME_*` names and `COWORLD_PLAYER_WS_URL` are real names in the coworld runner
contract** (verified against `coworld/runner/runner.py`, `kubernetes_runner.py`, `play.py`), and the
WS URL shape matches `runner/RUNNER_README.md` L8 verbatim.

The new seat-count gate (L94–139) is the right design: `certification.game_config.num_agents` is the
single source, `None`/non-int/`bool` is a hard `SEAT-COUNT FAIL`, and `len(certification.players)`,
`len(game_config.players)` and `SMOKE_SEATS`/`<SEATS>` are all cross-checked against it before any
container starts. A non-numeric `SMOKE_SEATS` (unsubstituted placeholder) is correctly ignored here
and left to the phase-20 placeholder gate. `isinstance(declared, bool)` is excluded before the
`int` check — correct, `True` would otherwise pass as 1.

Assertions after the run: no `player_failure.json`, `results.json` non-empty valid UTF-8 JSON object
with `names`/`scores` of length `seats`, replay non-empty and (unless `SMOKE_REQUIRE_REPLAY_JSON=0`)
valid JSON. `dump_logs` on every failure path. `trap cleanup EXIT` removes the prefixed containers.

### `templates/tools/ci/policies.json.example`
Four entries: `bullwhip-steady` (PLAYER_PROMPT, token owner = champion #1), `bullwhip-forecaster`
(PLAYER_PROMPT + `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` = champion #2),
`bullwhip-basestock` and `bullwhip-mirror` (`PLAYER_SCRIPTED`, fillers). Valid JSON; every entry has
`name` and `run`, and `run` is a string, so the workflow's `shlex.split` path is the one exercised.
`/bin/bullwhip-player` matches the Dockerfile's second entrypoint. The champion-#2 `player` field
matches the required `ply_bac48eb1-…` identity.

### `templates/README.md`
Accurate per-file documentation, now consistent with the rewritten `docker_smoke.sh` (it correctly
describes `<SEATS>` as a cross-check, not a fallback, and lists the four pre-flight checks). Its
placeholder-residue claim was verified: after substituting `<slug>`/`<IMAGE>`/`<SEATS>`, the only
angle-bracket tokens left in the copied files are `<run_id>`, `<name>`, `<cow_id>`, `<sha>` — plus
`<seats>` inside a `SEAT-COUNT FAIL` message string at `docker_smoke.sh:105` and `<SEATS>` inside
two more message strings at L129/L137, which the README does not mention.

### `templates/STATE.template.json`, `run-task.md`, `blocked-subtask.md`, `announce.md`
Valid JSON / prose templates, no CI surface. `STATE.template.json` keys line up with what prompts
40 and 50 write (`coworld.{version,cow_id,manifest_sha}`, `policies.{champion1,champion2,fillers}`,
`league.{id,division}`). No findings.

---

## 2. Interface check vs the phase prompts

| prompt expects | template provides | verdict |
|---|---|---|
| `gh workflow run coworld-release.yml -f version= -f put_secret= [-f policies=] [-f skip_certify=]` (40 §3) | exactly those four inputs plus `secret_key_name` | OK |
| artifact name `release-result`, file `release-result.json` (40 §3) | `name: release-result`, path `…/release-result.json` | OK |
| `canonical == true` (40 §4) | `canonical: True/False/None` from `^Canonical: (yes\|no)$` | OK |
| `certify.ok == true` (40 §4) | `certify.ok` | OK |
| `certify.replay_liveness` contains `skipped (static replay bundle declared` (40 §4, exit criterion) | captured from `certify.log` — **but the pinned CLI can never emit that string** | **BLOCKING-1** |
| `policies[]` = `{name,version,policy_version_id,player_id}`, `policy_version_id` always null (40 §4) | exactly that shape, `policy_version_id: None` hard-coded | OK |
| champion #2 `player_id == ply_bac48eb1-…` (40 §4) | set from the policy entry's `"player"` | OK |
| `secret_put == true` (40 §4) | `bool(secret and secret.get("ok"))` | OK |
| triage by `step_failed` (40 §5) | `current_step` written at the head of every step | OK |
| `-f skip_certify=true` ⇒ `certify: null` (40 §3 comment) | `load("certify.json", None)` ⇒ `certify: None` | OK |
| `gh workflow run coworld-submit.yml -f player_id= -f policy= -f league_id=` (50 §5/§6) | exactly those three | OK |
| artifact `submit-result` = `{ok,player_id,policy,league_id,exit_code,output_tail,error}` (50 §5) | exactly those seven keys | OK |
| `tools/ci/policies.json` must define **five** versions, 2 champions + 3 fillers (40 §2) | example defines **four**; README and 20-build describe four; 50 §7 posts **two** filler UUIDs | MINOR-7 |
| policy `run` = `/bin/<slug>_player` (40 §2 example) | everything else uses `/bin/<slug>-player` | MINOR-8 |
| champion names (50 §5/§6) `<slug>-forecaster` / `<slug>-steady-llm` | 40 §2 says forecaster/hedger; example says steady/forecaster | MINOR-9 |
| "if either file is missing or **non-executable** the repo's CI cannot go green" (20 §2) | false for `tools/build_replay_viewer.sh` — ci.yml runs it with `bash` | **BLOCKING-4** |
| 20 exit criterion lists `tools/ci/docker_smoke.sh (executable)` | does not require `tools/build_replay_viewer.sh` executable, which is the one that actually must be | **BLOCKING-4** |

Everything the prompts read out of `release-result.json` and `submit-result.json` is produced with
the right key names and types. The interface is sound; the two structural breaks are BLOCKING-1
(a field the prompts gate on can never be satisfied) and BLOCKING-4.

---

## 3. What I ran, and the output

**Environment**: `docker info` → OK; `coworld-bullwhip:latest` present (`e74220606cef`, 91.4MB,
linux/amd64 running under emulation on this arm64 host). No `shellcheck`, `actionlint` or `yamllint`
available.

**a. `bash -n` on every shell.** `templates/tools/ci/docker_smoke.sh` → clean. Plus all 22 `run:`
blocks extracted from the three workflows (with `${{ … }}` stubbed to a token) and all 6 embedded
`python3 … <<'PY'` heredocs dedented and `ast.parse`d:

```
OK   ci.yml:test:Install nimby and Nim
OK   ci.yml:test:Sync Nim dependencies
OK   ci.yml:test:Regenerate nim.cfg from the synced package tree
OK   ci.yml:test:Run tests
OK   ci.yml:docker-smoke:Build image
OK   ci.yml:docker-smoke:Raw-Docker episode smoke
OK   ci.yml:wasm-viewer:Build the static replay viewer bundle
OK   ci.yml:wasm-viewer:Assert the bundle is complete
OK   coworld-release.yml:release:Validate inputs
OK   coworld-release.yml:release:Authenticate to Softmax
OK   coworld-release.yml:release:Resolve the policy list        py OK (12 lines)
OK   coworld-release.yml:release:Build the Coworld manifest
OK   coworld-release.yml:release:Certify locally                py OK (25 lines)
OK   coworld-release.yml:release:Upload the policies            py OK (80 lines)
OK   coworld-release.yml:release:Upload the Coworld             py OK (22 lines)
OK   coworld-release.yml:release:Put the Coworld secret
OK   coworld-release.yml:release:Assemble release-result.json   py OK (87 lines)
OK   coworld-release.yml:release:Enforce canonical
OK   coworld-submit.yml:submit:Authenticate to Softmax
OK   coworld-submit.yml:submit:Submit
OK   coworld-submit.yml:submit:Unset the player identity
OK   coworld-submit.yml:submit:Assemble submit-result.json      py OK (27 lines)

22 run blocks, 6 embedded python heredocs checked
```

**b. YAML / JSON validation.**

```
OK templates/ci.yml: top keys=['name', True, 'concurrency', 'env', 'jobs']  jobs=['test', 'docker-smoke', 'wasm-viewer']
OK templates/coworld-release.yml: top keys=['name', True, 'concurrency', 'env', 'jobs']  jobs=['release']
OK templates/coworld-submit.yml: top keys=['name', True, 'concurrency', 'env', 'jobs']  jobs=['submit']
OK json policies.json.example, entries: ['bullwhip-steady', 'bullwhip-forecaster', 'bullwhip-basestock', 'bullwhip-mirror']
OK json STATE.template.json, keys: ['run','idea_task','run_task','slug','repo','starter','phase','phase_attempts','review_round','coworld','policies','league','verify','announce','blocked','heartbeat_at','log']
```

All three parse as YAML. (`True` is PyYAML resolving the `on:` key — expected, not a defect.)
**YAML well-formedness does not catch BLOCKING-2/3**, which are expression-context errors GitHub
raises at workflow-load time; no local linter here can see them.

**c. `docker_smoke.sh` for real against `coworld-bullwhip:latest`.** Command:

```
SMOKE_SLUG=bullwhip SMOKE_SEATS=4 \
SMOKE_MANIFEST=/Users/daveey/code/cogame-bullwhip/coworld_manifest_template.json \
SMOKE_TIMEOUT=420 bash templates/tools/ci/docker_smoke.sh coworld-bullwhip:latest
```

Verbatim output (platform-mismatch warnings from arm64 emulation elided):

```
slot 0: player_id=bullwhip-player run=['/bin/bullwhip-player'] env=0
slot 1: player_id=bullwhip-basestock run=['/bin/bullwhip-player'] env=1
slot 2: player_id=bullwhip-player run=['/bin/bullwhip-player'] env=0
slot 3: player_id=bullwhip-mirror run=['/bin/bullwhip-player'] env=1
game=bullwhip seats=4 config={"players": [{"name": "Sprocket"}, {"name": "Gizmo"}, {"name": "Ratchet"}, {"name": "Widget"}], "num_agents": 4, "seed": 7, "weeks": 8, "turnDelayMs": 0, "player_connect_timeout_seconds": 180, "tokens": ["token-0", "token-1", "token-2", "token-3"]}
no ANTHROPIC_API_KEY: the game must complete on its scripted baselines
starting game container (coworld-bullwhip:latest /bin/bullwhip) ...
waiting for the episode (game container exit, up to 420s) ...
episode end reason: complete
smoke OK: seats=4 results=233B replay=7864B reason=complete
```

`RC=0`, no leftover `bullwhip-smoke-*` containers after the trap ran. The seat-mix mapping is
exactly the certification fixture (slots 1 and 3 pick up `PLAYER_SCRIPTED` from the manifest's
player entries; slots 0 and 2 run LLM-driven and fall back to scripted with no API key, as designed).
Bullwhip's replay is JSON, so the default `SMOKE_REQUIRE_REPLAY_JSON=1` is right for it.

**d. Negative paths of the new seat-count gate** (all fail before any container starts):

```
A) SMOKE_SEATS=5 vs manifest 4
   SEAT-COUNT FAIL: the manifest fixture declares 4 seats but SMOKE_SEATS/<SEATS> says 5.
   The design note and the manifest disagree; fix whichever is wrong.

B) num_agents removed from certification.game_config
   SEAT-COUNT FAIL: certification.game_config.num_agents is missing from …/no_na.json.
     The seat count must be declared in the certification fixture (and in every variant).
     Add "num_agents": <seats> to certification.game_config and re-run.

C) SMOKE_SEATS unset (literal <SEATS> placeholder)
   ignored as documented; run proceeds → smoke OK: seats=4 … reason=complete

D) certification.players truncated to 3
   SEAT-COUNT FAIL: certification.game_config.num_agents is 4 but certification.players
   names 3 seats. The fixture must seat exactly num_agents players.
```

All four behave exactly as `templates/README.md` documents.

**e. CLI ground truth from the unpacked wheels** (the decisive evidence for BLOCKING-1):

```
coworld 0.1.34  cli.py:343  typer.echo("Replay liveness: verified /client/replay and /replay")   # unconditional, only occurrence
coworld 0.1.38  cli.py:592  uses_static_replay_viewer_bundle = _uses_static_replay_viewer_bundle(result)
                cli.py:594  typer.echo("Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)")
                cli.py:596  typer.echo("Replay liveness: verified /client/replay and /replay")
coworld 0.1.39  cli.py:596/598  same as 0.1.38
```

I also confirmed 0.1.38 is a drop-in for this workflow: same `softmax-cli==0.26.27` pin, same
`Upload complete: {name}:v{version}` format, same `Coworld:` / `Manifest hash:` / `Canonical:` /
`Hosted smoke certification: passed` lines, and `--secret-env`, `--wait-hosted-smoke`,
`--hosted-smoke-timeout-seconds`, `--open-browser/--no-open-browser`,
`--open-report/--no-open-report`, `--compose`, `--template` all still present. And
`CertificationResult.package: CoworldPackage` (certifier.py:139–141) means
`_uses_static_replay_viewer_bundle`'s getattr chain resolves for a manifest declaring
`game.replay_viewer.bundle` — so on 0.1.38 the marker really does print for a bullwhip-shaped
manifest. The liveness line is `typer.echo`, not rich `console.print`, so it is never width-wrapped
in CI.

Also checked: `webbrowser.open()` with no registered browser returns `False` and does not raise, so
the missing `--no-open-report` is cosmetic (MINOR-10).

No pushes, no `gh` writes, no `softmax`/Observatory calls were made.

---

## 4. Findings

### BLOCKING

**1. `coworld-release.yml:62` — the pinned CLI can never print the marker the certify gate requires.**
`COWORLD_PKG: "coworld[auth]==0.1.34"`, but `LIVENESS_MARKER` (L64) is
`Replay liveness: skipped (static replay bundle declared`. In 0.1.34 that string does not exist
anywhere in the package: `cli.py:343` unconditionally echoes `Replay liveness: verified
/client/replay and /replay`. The conditional form was introduced in **0.1.38** (`cli.py:592–596`).
So the `Certify locally` step raises `certification did not report the STATIC replay bundle` on
**every** dispatch, the job dies before any policy is uploaded, and
`release-result.json.certify.ok` is `false` forever — prompt 40's exit criterion is unsatisfiable.
*Fix:* `COWORLD_PKG: "coworld[auth]==0.1.38"` (verified drop-in; also update `coworld-submit.yml:45`
to keep the two files on one pin).

**2. `coworld-release.yml:63` — `runner` context is not available in workflow-level `env`; the
workflow is invalid and no job ever starts.**
`RR: ${{ runner.temp }}/release-result` sits in the top-level `env:` block. GitHub's
context-availability table allows only `github`, `secrets`, `inputs`, `vars` there (`runner` is
step-level only — `jobs.<job_id>.steps.{env,run,with}`; it is not even allowed in
`jobs.<job_id>.env`). The run fails at workflow load with `Unrecognized named-value: 'runner'`,
so **no `release-result` artifact is ever produced** and prompt 40 step 3's `gh run download` has
nothing to fetch. Corroboration: no workflow anywhere on this machine uses `runner.` in a top-level
`env` — the gh-aw generated workflows use it only in step `env:`/`with:`.
*Fix:* `RR: /tmp/release-result`, and change the two `upload-artifact` `path:` values (L434, L444–445)
from `${{ runner.temp }}/release-result/…` to `/tmp/release-result/…` so both halves agree.

**3. `coworld-submit.yml:46` — same defect.**
`SR: ${{ runner.temp }}/submit-result` in the top-level `env:` block. Champion submission never
runs; phase 50 steps 5 and 6 both die at dispatch.
*Fix:* `SR: /tmp/submit-result`, and `path:` at L132 to `/tmp/submit-result/submit-result.json`.

**4. `ci.yml:178` — CI cannot detect a non-executable `tools/build_replay_viewer.sh`, which
`coworld build` hard-requires.**
`coworld/bundle.py:87–91` refuses to build unless `build_hook.is_file() and os.access(build_hook,
os.X_OK)` — `Coworld builds with a source replay viewer bundle require an executable build hook`.
But `ci.yml:178` runs it as `bash tools/build_replay_viewer.sh …`, which ignores the exec bit, so
`wasm-viewer` goes green on a mode-0644 hook and the failure only surfaces later, in
`coworld-release.yml`'s `Build the Coworld manifest`. This is exactly the gap `prompts/20-build.md`
claims is closed ("if either file is missing or **non-executable** the repo's CI cannot go green"),
and 20's exit criterion requires the exec bit on `tools/ci/docker_smoke.sh` — which is invoked with
`bash` and does not need it — while omitting it for `build_replay_viewer.sh`, which does.
(bullwhip's own copy is `100755`, so the requirement is satisfiable; nothing enforces it.)
*Fix:* add `test -x tools/build_replay_viewer.sh || { echo "::error::tools/build_replay_viewer.sh
must be executable (coworld build requires it)"; exit 1; }` as the first step of `wasm-viewer`, and
move the `(executable)` note in 20's exit criterion onto `tools/build_replay_viewer.sh`.

### MINOR

**5. `coworld-release.yml:249–250, 266` — a failing `upload-policy` can carry `--secret-env` values
into the `release-result` artifact.** Failure text is `(proc.stderr or proc.stdout).strip()[-500:]`,
written to `policy_errors.json` and then into `release-result.json.errors[]`, which is uploaded. A
typer `BadParameter` on a malformed `--secret-env` echoes the offending `KEY=VALUE`. Impact today is
nil (policy env is only `PLAYER_PROMPT`/`PLAYER_SCRIPTED`, already public in the repo), but the
channel exists. *Fix:* redact `=`-bearing tokens in the failure string before appending.

**6. `coworld-release.yml:366–369` — an unparsed `Canonical:` line yields `ok:false` with an empty
`errors[]`.** `canonical_raw is None` adds no error, so prompt 40 §5's triage table has nothing to
match and `step_failed` misleadingly names the last step that started. *Fix:* also append an error
when `canonical_raw is None`.

**7. `prompts/40-release.md:18` — policy count contradicts every other file.** 40 demands "five
distinct versions (two champions + three fillers)"; `policies.json.example` has four,
`templates/README.md` and `prompts/20-build.md` both describe four (2 champions + 2 scripted
baselines), and `prompts/50-league.md:82` posts exactly two filler UUIDs. *Fix:* make 40 say four
(two champions + two fillers), or add a third baseline to the example and to 50.

**8. `prompts/40-release.md:22–27` — `run` is `/bin/<slug>_player` (underscore).** Every other
reference — README, docker_smoke defaults, the example, bullwhip's Dockerfile — uses
`/bin/<slug>-player`. *Fix:* hyphen.

**9. `prompts/50-league.md:53, 67` — champion policy names disagree with 40 and with the example.**
50 submits `<slug>-forecaster` as daveey and `<slug>-steady-llm` as daveey-1; 40 §2's example pairs
forecaster (token owner) with hedger (daveey-1); `policies.json.example` pairs steady (token owner)
with forecaster (daveey-1). `<slug>-steady-llm` appears nowhere else. The *structure* is consistent
(the entry carrying `"player"` is champion #2), but three different name pairs invite submitting a
daveey-1-owned version as daveey and 409-ing. *Fix:* use one name pair across 40, 50 and the example,
or state the rule by role ("champion #2 is whichever entry carries `player`").

**10. `coworld-release.yml:151` — `coworld certify` runs without `--no-open-report`.** Harmless
(verified `webbrowser.open()` returns `False` headless rather than raising), but it is dead work.
*Fix:* append `--no-open-report`.

**11. `ci.yml:7–8` — stale header comment.** Still describes `<SEATS>` as "used only as the
docker-smoke fallback when the manifest fixture cannot be read"; `docker_smoke.sh` now hard-fails on
a mismatch and `templates/README.md` documents it as a cross-check. *Fix:* mirror the README wording.

**12. `templates/README.md:26–31` — the placeholder-residue list is incomplete.** After substitution
`grep -n '<'` also returns `<seats>` (`docker_smoke.sh:105`) and `<SEATS>` (L129, L137) inside
`SEAT-COUNT FAIL` message strings, which the README's "only those four" claim omits — a phase-20
placeholder gate written to that claim would false-positive. *Fix:* add those three to the expected-
residue list, or reword the messages.

**13. `coworld-release.yml:11–13, 184` — the "upload-coworld prunes the local image" rationale is
unverified.** No `prune`, `rmi` or image removal exists anywhere in coworld 0.1.34 or 0.1.38; the
only image mutations are `docker tag`, `docker pull` and `docker image save`. The **ordering is
correct regardless** and matches the empirical failure in `prompts/40-release.md:62`, but the stated
mechanism should not be trusted as the reason. *Fix:* soften the comment to "observed:
`upload-policy` reports the image missing if it runs after `upload-coworld`".

**14. `ci.yml:49` — the primary cache key can never hit.** It ends in `${{ github.sha }}`, so every
run misses the primary key, restores via `restore-keys`, and writes a fresh cache entry per commit.
Works, but churns the 10 GB cache budget. *Fix:* drop `-${{ github.sha }}` from `key`.

**15. `ci.yml:26` — `SLUG` is defined and never used** in `ci.yml` (`docker_smoke.sh` carries its own
substituted default). *Fix:* drop it, or pass `SMOKE_SLUG: ${{ env.SLUG }}` in the docker-smoke step.

**16. `coworld-release.yml:436` / `coworld-submit.yml:133` — `if-no-files-found: warn`.** If the
artifact is ever absent, prompt 40 §3 / 50 §5's unconditional `gh run download … -n release-result`
fails with an opaque "no artifact matches" rather than a named cause. *Fix:* `error`, so the workflow
names the problem itself.

**17. `docker_smoke.sh:54` — the `coworld-local` network is shared, fixed-name, and never removed.**
Fine on an ephemeral GH runner; locally it collides with the network `coworld play` manages and
leaks after every run. *Fix:* name it `${prefix}-net` and remove it in `cleanup`.

---

## Counts

**4 BLOCKING, 13 MINOR.**
