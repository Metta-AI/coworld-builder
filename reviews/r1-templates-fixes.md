# R1 — `templates/` review, fixes

Fixes for `reviews/r1-templates-review.md` (**4 BLOCKING, 13 MINOR**). Every change is confined to
`templates/`; everything a finding needs outside `templates/` is written out verbatim in
[§3](#3-proposed-edits-outside-templates) instead of applied.

**Result: 4/4 BLOCKING fixed, 11/13 MINOR fixed or verified-already-correct, 2 MINOR deferred to
the prompts fixer** (MINOR-7 and MINOR-9 are prompt-side only and were already resolved there by
the concurrent fixer; MINOR-8 is prompt-side and is still open — see §3).

---

## 1. Finding → sha → what changed

| finding | sha | file(s) | what changed |
|---|---|---|---|
| **BLOCKING-1** | `e06e5df` | `coworld-release.yml`, `coworld-submit.yml`, `README.md` | `COWORLD_PKG` bumped `coworld[auth]==0.1.34` → `==0.1.38` in both workflows, and the README's step-1 recipe with them. Added a comment at the pin saying 0.1.38 is a **floor**: `LIVENESS_MARKER` is only emitted from 0.1.38 on, so a lower pin makes the certify gate unsatisfiable. **0.1.38 verified to exist and run here**: `uvx --from "coworld[auth]==0.1.38" coworld --help` → exit 0, full command list including `upload-policy`, `upload-coworld`, `submit`, `secret`, `player`. `coworld certify --help` on 0.1.38 confirms `--no-open-report` (used by tpl-10). |
| **BLOCKING-2** | `46a5d05` | `coworld-release.yml` | `RR: ${{ runner.temp }}/release-result` deleted from the workflow-level `env:`. A new **first** step `Export the result directory` writes `RR=${RUNNER_TEMP}/release-result` to `$GITHUB_ENV` and `mkdir -p`s it, so every later step (including the `always()` ones) reads it from the env context. Both `upload-artifact` `path:` values now use `${{ env.RR }}/…` so there is exactly one definition of the path and the two halves cannot drift. No `runner.` expression is left anywhere outside step scope. |
| **BLOCKING-3** | `5ad50fe` | `coworld-submit.yml` | Same fix for `SR`: removed from workflow `env:`, exported from `$RUNNER_TEMP` in a first step, artifact `path:` → `${{ env.SR }}/submit-result.json`. |
| **BLOCKING-4** | `94cfece` | `ci.yml` | New step `Assert the replay-viewer build hook is present and executable` (first step of `wasm-viewer`) — `test -f` then `test -x tools/build_replay_viewer.sh`, with the `coworld build` rationale (`bundle.py` requires `os.X_OK`) and the `git update-index --chmod=+x` fix in the error text. The hook is now invoked as `./tools/build_replay_viewer.sh …`, **not** `bash …`, so a mode-0644 hook fails CI exactly where `coworld build` would. Matching `test -f` / `test -x` assertion added for `tools/ci/docker_smoke.sh` in `docker-smoke`, and it too is invoked by path. |
| MINOR-5 | `3ed96c9` | `coworld-release.yml` | `redact()` helper in the `Upload the policies` heredoc rewrites every `KEY=VALUE` token to `KEY=***` before the text is recorded. Applied to all three failure/warning strings (`player use` failure, `upload-policy` failure, `player unset` warning), so a typer `BadParameter` echoing a `--secret-env` pair can no longer ride into the uploaded `release-result.json`. |
| MINOR-6 | `85c8a9a` | `coworld-release.yml` | `canonical_raw is None` now appends a named error (`no 'Canonical: yes\|no' line in the upload-coworld output (exit_code=…) … see release-logs/upload.log`), so `ok:false` is never reported with an empty `errors[]` and phase 40's triage table has something to match. |
| MINOR-7 | — | *(no template change)* | Verified: `policies.json.example` already holds exactly the canonical **four** — `bullwhip-steady` (LLM prompt, token owner = champion #1), `bullwhip-forecaster` (LLM prompt + `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` = champion #2), `bullwhip-basestock` and `bullwhip-mirror` (`PLAYER_SCRIPTED` fillers), each with realistic `PLAYER_PROMPT` text. `/Users/daveey/code/cogame-bullwhip/tmp/` carries **no** usable prompt text (`run_e2e.sh` sets `PLAYER_PROMPT=""` and drives the scripted baselines only), so the example's existing prompts were kept. `prompts/40-release.md` no longer says "five" — the concurrent fixer replaced it with a role table. |
| MINOR-8 | — | *(prompt-side only)* | Still open in `prompts/40-release.md` and `playbooks/make-coworld.md`; exact replacements in §3. The template side already uses `/bin/<slug>-player` everywhere. |
| MINOR-9 | — | *(no template change)* | Verified resolved on the prompt side: `prompts/50-league.md:54,72` now name `bullwhip-steady:v1` / `bullwhip-forecaster:v1`, matching `policies.json.example`, and both cite `STATE.policies.champion{1,2}` as the authority rather than a literal name. |
| MINOR-10 | `0fc0754` | `coworld-release.yml` | `coworld certify … --no-open-report` (flag confirmed present in 0.1.38). |
| MINOR-11 | `9510644` | `ci.yml` | Header comment for `<SEATS>` rewritten from "used only as the docker-smoke fallback when the manifest fixture cannot be read" to the README's wording: a **cross-check** that hard-fails on disagreement with `certification.game_config.num_agents`. |
| MINOR-12 | `8d7ce0a` | `docker_smoke.sh`, `ci.yml`, `coworld-release.yml`, `README.md` | Angle brackets removed from the three `SEAT-COUNT FAIL` message/comment sites (`Add a "num_agents" integer …`, `SMOKE_SEATS is an independent second declaration…`, `SMOKE_SEATS says {seats_expected}`) plus two brackets my own tpl-4/tpl-5 text had introduced (`bash <script>`, `=<redacted>`). After substituting `<slug>`/`<IMAGE>`/`<SEATS>`, the placeholder-shaped residue across all copied files is now **exactly** `<run_id>`, `<name>`, `<cow_id>`, `<sha>` — the four the README names. The README's residue recipe was also made executable and precise: it now greps `'<[A-Za-z_][A-Za-z0-9_]*>'` and explains that a gate written against a bare `<` false-positives on `<<'PY'` heredocs and `slot < seats` comparisons. |
| MINOR-13 | `acdd77a` | `coworld-release.yml`, `README.md` | The "upload-coworld prunes the local image" rationale is now stated as **observed**: `upload-policy` reports the local image missing when it runs after `upload-coworld`; the comment explicitly says no prune/`rmi` exists in the CLI and that only the ordering is established. Ordering itself unchanged. |
| MINOR-14 | `981ebce` | `ci.yml` | `-${{ github.sha }}` dropped from the nimby cache `key` so the primary key can hit; `restore-keys` shortened to the pin prefix so it still degrades gracefully when `nimby.lock` changes. |
| MINOR-15 | `a2d494f` | `ci.yml` | `SLUG` is no longer dead: the `Raw-Docker episode smoke` step passes `SMOKE_SLUG: ${{ env.SLUG }}`, making the workflow env the single source for the entry-point names and the script's substituted default a fallback. |
| MINOR-16 | `4b894ec`, `6d997a8` | `coworld-release.yml`, `coworld-submit.yml` | `if-no-files-found: warn` → `error` on `release-result` and `submit-result` — the two artifacts phases 40 and 50 download unconditionally, so a missing one now names itself instead of surfacing as an opaque `gh run download` failure. `release-logs` deliberately **stays** on `warn` (`6d997a8`), with a comment: with `skip_certify=true`, or on a failure before `coworld build`, some of its paths legitimately do not exist and the run should not gain a second red step for it. |
| MINOR-17 | `4cd428f` | `docker_smoke.sh`, `README.md` | The docker network is now per-run (`${prefix}-net`, i.e. `<slug>-smoke-<pid>-net`), unconditionally created and removed in `cleanup`. No more collision with the `coworld-local` network `coworld play` manages, and no leak after a local run. README updated. |

Commit range: `e06e5df..4cd428f` on `main`, **not pushed**. (The other fixer's `r1-*` commits are
interleaved in that range; the `tpl-*` commits are mine.)

### Concurrency disclosure (read this)

Two of my commits picked up the other fixer's in-flight working-tree edits because I used
`git commit -a`:

- **`94cfece` (tpl-4) also contains a `fleet/bin/deploy.py` hunk that is not mine.** The content is
  the other fixer's and is byte-identical to what was in their working tree; I neither wrote nor
  modified it. It is simply attributed to the wrong commit. Their later `r1-12` / `r1-39` commits
  cover the rest of that file. Nothing is lost; only the commit message is inaccurate. Left as-is
  rather than rebased, because rewriting history would change the SHAs of their commits while they
  are still working.
- An `--amend` of mine briefly landed on top of their `r1-21` commit. It was **undone**:
  `r1-21` is back at its original content (`eaaa208`), their then-uncommitted `docs/SPEC.md` and
  `prompts/00-claim.md` edits were restored to the working tree untouched (they have since
  committed them), and my change was re-committed alone as `6d997a8` with an explicit pathspec.
  Verified afterwards: `git log --name-only -- templates/` over the whole range shows **only**
  `tpl-*` commits touching `templates/`.

---

## 2. Verification (re-run after the fixes)

Driver: `scratchpad/verify.py` — YAML parse, JSON parse, `runner.*` scope check, `bash -n` on every
`run:` block with `${{ … }}` stubbed, `ast.parse` on every embedded `python3 … <<'PY'` heredoc,
`bash -n` on `docker_smoke.sh`, and the placeholder-residue check.

```
OK yaml ci.yml: top keys=['name', True, 'concurrency', 'env', 'jobs']  jobs=['test', 'docker-smoke', 'wasm-viewer']
OK yaml coworld-release.yml: top keys=['name', True, 'concurrency', 'env', 'jobs']  jobs=['release']
OK yaml coworld-submit.yml: top keys=['name', True, 'concurrency', 'env', 'jobs']  jobs=['submit']
OK json tools/ci/policies.json.example: ['bullwhip-steady', 'bullwhip-forecaster', 'bullwhip-basestock', 'bullwhip-mirror']
OK json STATE.template.json: ['run', 'idea_task', 'run_task', 'slug', 'repo', 'starter', 'phase', 'phase_attempts', 'review_round', 'coworld', 'policies', 'league', 'verify', 'announce', 'blocked', 'heartbeat_at', 'log']
ok   runner ctx at steps scope: ci.yml.jobs.test.steps.1.with.key -> ${{ runner.os }}
ok   runner ctx at steps scope: ci.yml.jobs.test.steps.1.with.restore-keys -> ${{ runner.os }}
runner-context scope check done
OK   ci.yml:test:Install nimby and Nim
OK   ci.yml:test:Sync Nim dependencies
OK   ci.yml:test:Regenerate nim.cfg from the synced package tree
OK   ci.yml:test:Run tests
OK   ci.yml:docker-smoke:Assert the smoke script is present and executable
OK   ci.yml:docker-smoke:Build image
OK   ci.yml:docker-smoke:Raw-Docker episode smoke
OK   ci.yml:wasm-viewer:Assert the replay-viewer build hook is present and executable
OK   ci.yml:wasm-viewer:Build the static replay viewer bundle
OK   ci.yml:wasm-viewer:Assert the bundle is complete
OK   coworld-release.yml:release:Export the result directory
OK   coworld-release.yml:release:Validate inputs
OK   coworld-release.yml:release:Authenticate to Softmax
OK   coworld-release.yml:release:Resolve the policy list   py OK (12 lines)
OK   coworld-release.yml:release:Build the Coworld manifest
OK   coworld-release.yml:release:Certify locally   py OK (25 lines)
OK   coworld-release.yml:release:Upload the policies   py OK (89 lines)
OK   coworld-release.yml:release:Upload the Coworld   py OK (22 lines)
OK   coworld-release.yml:release:Put the Coworld secret
OK   coworld-release.yml:release:Assemble release-result.json   py OK (98 lines)
OK   coworld-release.yml:release:Enforce canonical
OK   coworld-submit.yml:submit:Export the result directory
OK   coworld-submit.yml:submit:Authenticate to Softmax
OK   coworld-submit.yml:submit:Submit
OK   coworld-submit.yml:submit:Unset the player identity
OK   coworld-submit.yml:submit:Assemble submit-result.json   py OK (27 lines)

26 run blocks, 6 embedded python heredocs checked
OK   bash -n tools/ci/docker_smoke.sh
OK   placeholder residue after substitution == ['<cow_id>', '<name>', '<run_id>', '<sha>']

ALL CHECKS PASSED
```

### `actionlint`-style `runner.*` scope gate

No `actionlint` on this machine, so the check is done structurally rather than textually: the
workflow is loaded as YAML and every string is walked, tracking whether the path passed through a
job's `steps:` list. Any `${{ runner.… }}` reached **without** crossing `steps:` is a failure. The
two surviving hits are both `jobs.test.steps[1].with.*` — step scope, which is legal. The gate is
`scratchpad/verify.py`; the equivalent one-liner for a shell gate is:

```bash
python3 - <<'PY'
import re, sys, yaml, pathlib
EXPR = re.compile(r"\$\{\{[^}]*\}\}")
bad = []
def scan(node, path, in_steps):
    if isinstance(node, dict):
        for k, v in node.items(): scan(v, path + [str(k)], in_steps or str(k) == "steps")
    elif isinstance(node, list):
        for i, v in enumerate(node): scan(v, path + [str(i)], in_steps)
    elif isinstance(node, str):
        for e in EXPR.findall(node):
            if re.search(r"\brunner\s*\.", e) and not in_steps:
                bad.append(f"{'.'.join(path)} -> {e}")
for f in ["ci.yml", "coworld-release.yml", "coworld-submit.yml"]:
    scan(yaml.safe_load(pathlib.Path(f"templates/{f}").read_text()), [f], False)
print("\n".join(bad) or "no runner.* outside steps scope")
sys.exit(1 if bad else 0)
PY
```

### `docker_smoke.sh` run for real

Docker present; `coworld-bullwhip:latest` = `sha256:e74220606cef…`, 91.4 MB, `linux/amd64` under
emulation on this arm64 host. Header says the script takes `[image]` as `$1` plus `SMOKE_*` env:

```
SMOKE_SLUG=bullwhip SMOKE_SEATS=4 \
SMOKE_MANIFEST=/Users/daveey/code/cogame-bullwhip/coworld_manifest_template.json \
SMOKE_TIMEOUT=420 bash templates/tools/ci/docker_smoke.sh coworld-bullwhip:latest
```

Verbatim output (arm64 platform-mismatch warnings elided):

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

`RC=0`. After the trap ran: `0` leftover `bullwhip-smoke-*` containers and `0` leftover
`bullwhip-smoke-*` networks — the MINOR-17 per-run network is created and removed cleanly, and the
pre-existing `coworld-local` network (owned by `coworld play`) is now left untouched.

The seat-count gate still fires with the reworded (bracket-free) messages, before any container
starts:

```
A) SMOKE_SEATS=5 vs manifest 4
   SEAT-COUNT FAIL: the manifest fixture declares 4 seats but SMOKE_SEATS says 5.
   The design note and the manifest disagree; fix whichever is wrong.

B) num_agents removed from certification.game_config
   SEAT-COUNT FAIL: certification.game_config.num_agents is missing from /tmp/no_na.json.
     The seat count must be declared in the certification fixture (and in every variant).
     Add a "num_agents" integer to certification.game_config and re-run.
```

No pushes, no `gh` writes, no `softmax`/Observatory calls were made. The one network call was
`uvx --from "coworld[auth]==0.1.38" coworld --help` (and `coworld certify --help`), to verify the
new pin exists.

---

## 3. Proposed edits outside `templates/`

None of these were applied — `prompts/` and `playbooks/` belong to the other fixer. Line numbers are
as of `c208ea2`; match on the quoted text, not the number, since that tree is moving.

### 3.1 BLOCKING-4 — `prompts/20-build.md` claims CI catches the executable bit on the wrong file

The claim is now **true for both files** after `94cfece`, but 20's own wording still points the
`chmod +x` at `docker_smoke.sh` alone and its exit criterion omits the hook that actually needs it.

**(a) `prompts/20-build.md:45`** — replace:

```
   > `tools/ci/docker_smoke.sh` (**`chmod +x`**), and `tools/ci/policies.json` (from
```

with:

```
   > `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` (**both `chmod +x`** — `coworld
   > build` hard-requires `os.X_OK` on the replay-viewer hook), and `tools/ci/policies.json` (from
```

**(b) `prompts/20-build.md:52–54`** — replace:

```
   > `ci.yml`'s `docker-smoke` job calls `tools/ci/docker_smoke.sh` and its `wasm-viewer` job
   > calls `tools/build_replay_viewer.sh` — if either file is missing or non-executable the repo's
   > CI cannot go green, so both are part of this scaffold, not a later step.
```

with:

```
   > `ci.yml`'s `docker-smoke` job calls `tools/ci/docker_smoke.sh` and its `wasm-viewer` job
   > calls `tools/build_replay_viewer.sh`, each by path and each behind a `test -x` assertion — if
   > either file is missing or non-executable the repo's CI cannot go green, so both are part of
   > this scaffold, not a later step. The exec bit on `tools/build_replay_viewer.sh` is not
   > cosmetic: `coworld build` refuses to package a source replay-viewer bundle unless the hook is
   > `os.X_OK` ("Coworld builds with a source replay viewer bundle require an executable build
   > hook"), so a mode-0644 hook that slipped past CI would fail in phase 40 instead. Set it with
   > `git update-index --chmod=+x <path>`.
```

**(c) `prompts/20-build.md:88`** — replace:

```
`num_agents` everywhere, `tools/build_replay_viewer.sh`, `tools/ci/docker_smoke.sh` (executable),
```

with:

```
`num_agents` everywhere, `tools/build_replay_viewer.sh` (**executable**), `tools/ci/docker_smoke.sh`
(**executable**),
```

### 3.2 MINOR-8 — `/bin/<slug>_player` underscore contradicts every other file

Every other reference (README, `docker_smoke.sh` defaults, `policies.json.example`, bullwhip's
Dockerfile) uses the **hyphen** form `/bin/<slug>-player`.

**`prompts/40-release.md:37,38,40,41`** and **`playbooks/make-coworld.md:211,212,214,215`** —
replace every `"/bin/<slug>_player"` with `"/bin/<slug>-player"`. Both blocks become:

```json
[{"name":"<slug>-<prompt-name-1>","run":"/bin/<slug>-player","env":{"PLAYER_PROMPT":"…"}},
 {"name":"<slug>-<prompt-name-2>","run":"/bin/<slug>-player","env":{"PLAYER_PROMPT":"… a different prompt …"},
  "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
 {"name":"<slug>-<baseline-1>","run":"/bin/<slug>-player","env":{"PLAYER_SCRIPTED":"<baseline-1>"}},
 {"name":"<slug>-<baseline-2>","run":"/bin/<slug>-player","env":{"PLAYER_SCRIPTED":"<baseline-2>"}}]
```

A one-shot equivalent:

```bash
sed -i '' 's#/bin/<slug>_player#/bin/<slug>-player#g' \
  prompts/40-release.md playbooks/make-coworld.md
```

### 3.3 BLOCKING-1 — the `0.1.34` pin outside `templates/`

**Nothing to change.** `grep -rn '0\.1\.3' prompts/ playbooks/ agents/ fleet/ docs/ AGENT.md`
returns no hits: the pin is named only in the two workflow templates and `templates/README.md`, all
three of which are on `0.1.38` as of `e06e5df`. If a prompt or playbook later grows a
`coworld[auth]==` reference, it must say **0.1.38 or newer** — the certify gate's
`Replay liveness: skipped (static replay bundle declared` line does not exist before 0.1.38.

### 3.4 MINOR-7 / MINOR-9 — already resolved on the prompt side, keep them that way

The canonical set is now consistent, and should stay pinned to these facts:

- **four** policy versions: 2 LLM-prompt champions + 2 `PLAYER_SCRIPTED` fillers;
- champion #1 = the LLM prompt policy **without** a `player` field (bullwhip: `bullwhip-steady:v1`,
  submitted as daveey `ply_44ae9048-3242-4654-881f-6d9d43347fa3`);
- champion #2 = **whichever entry carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`**
  (bullwhip: `bullwhip-forecaster:v1`), uploaded while daveey-1 is active;
- fillers = `bullwhip-basestock:v1`, `bullwhip-mirror:v1`.

`prompts/50-league.md` already resolves the names through `STATE.policies.champion{1,2}` rather than
literals, which is the durable form; `prompts/40-release.md`'s role table already says the same by
role. No further edit needed — this section exists so a later rewrite does not reintroduce the
three-different-name-pairs problem the review found.
