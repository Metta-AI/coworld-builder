# Phase 20 — Build

Purpose: create the public repo and implement the design note until `ci.yml` is green on `main`.
Owner: builder sub-agent, driven by the coordinator. The sandbox cannot compile — CI is the harness.

## Inputs

- `runs/<run>/design.md` (accepted in phase 10), `STATE.slug`, `STATE.starter`, `STATE.repo`.
- Starter repo, mounted read-only at `/workspace/starters/<STATE.starter>` (the builder still
  `git clone`s it into the new repo's working tree so the new repo gets a clean history).
- `templates/README.md`, `templates/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `templates/tools/ci/{docker_smoke.sh,policies.json.example}`.
- `playbooks/make-coworld.md` §Phase 0 / §Phase 1.

## Procedure

1. Create the repo, **public** (public is a certification prerequisite; `source-resolves` 404s on
   private):
   ```bash
   gh repo create Metta-AI/cogame-<slug> --public --description "<one line>"
   ```
2. Send the **builder** brief (self-contained):

   > Implement `Metta-AI/cogame-<slug>` from the design note at `<abs path to runs/<run>/design.md>`,
   > forking the conventions of `<starter>`, mounted read-only at
   > `/workspace/starters/<starter>`. Copy the starter's layout, chrome, and
   > build scripts verbatim where the note does not override them. Deliver on `main`:
   > `src/` (sim module, server, LLM policy, scripted baseline — one image, env-switched
   > `PLAYER_PROMPT` vs `PLAYER_SCRIPTED=1`), `client/` (viewer reusing the starter's
   > `renderer.js`/`chrome.css` chrome), `replay-viewer/<slug>_replay.nim` +
   > `tools/build_replay_viewer.sh` (the `coworld build` hook, emscripten, same sim module),
   > `compose.yaml` (service name `<slug>`, `platform: linux/amd64`,
   > `build: {context: ., network: host}`), `coworld_manifest_template.json`
   > (image `{{<SLUG>_IMAGE}}`, `num_agents` in EVERY variant and in the cert fixture,
   > `"replay_viewer": {"bundle": "static-replay-viewer"}`, `game.docs` =
   > `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`,
   > `game.protocols` with BOTH `player` and `global`), `tests/`, `README.md`, and this scaffold
   > copied from `<abs path>/templates/` (per-file docs in `templates/README.md`) with the
   > placeholders `<slug>`, `<IMAGE>` (the compose image name minus `:latest`, e.g.
   > `coworld-<slug>`) and `<SEATS>` substituted. `<SEATS>` is the seat count **from the design
   > note**, and it is a cross-check, not a fallback: `docker_smoke.sh` fails if it disagrees with
   > the manifest's `certification.game_config.num_agents`, which is how a manifest edited without
   > the design note (or vice versa) gets caught. Files: `.github/workflows/ci.yml`,
   > `.github/workflows/coworld-release.yml`, `.github/workflows/coworld-submit.yml`,
   > `tools/ci/docker_smoke.sh` (**`chmod +x`**), and `tools/ci/policies.json` (from
   > `templates/tools/ci/policies.json.example` — copy **and edit**: the example's `bullwhip-*`
   > names and prompts are bullwhip's; rewrite names and prompts for THIS game. Only the shape is
   > inherited: **two LLM prompt policies** (`PLAYER_PROMPT`, one per champion, different prompts)
   > **+ ≥1 scripted baseline, normally two** (`PLAYER_SCRIPTED=<baseline name>`), all in the same
   > image, env-switched, with champion #2 — the second `PLAYER_PROMPT` entry — carrying
   > `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`).
   > `ci.yml`'s `docker-smoke` job calls `tools/ci/docker_smoke.sh` and its `wasm-viewer` job
   > calls `tools/build_replay_viewer.sh` — if either file is missing or non-executable the repo's
   > CI cannot go green, so both are part of this scaffold, not a later step.
   > Hard requirements, each of which is a blocking review finding if missed:
   > truncate every recorded string on RUNE boundaries; **for simultaneous-decision games** issue
   > all seats' LLM calls as ONE parallel batch per turn (`curly.makeRequests`) — a turn-based
   > sequential game calls the seat whose turn it is, and the design note says which shape this
   > game is; bound every wait and settle inside 60 % of
   > `episodeTimeoutSeconds` (720 s); parse LLM replies tolerantly, retry once, then fall back to
   > the scripted move; anonymous cog aliases in-game and real player names spectator-side only;
   > `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and labels hidden under 640 px so the
   > scorebug stays legible at 360 px.
   > You cannot run Docker/Nim locally. Push and let `ci.yml` be the only verdict. Any smoke that
   > runs a binary must depend on a fresh build of that binary in the same workflow run — a stale
   > binary silently produces wrong gameplay.
   > Report: commit shas, the CI run id, and anything in the design note you could not implement.

3. Watch CI. Find the run the way the **`dispatch-then-watch` recipe** in
   `playbooks/make-coworld.md` prescribes — never `-L 1` straight after the push, which can watch
   the previous run. `ci.yml` here is push-triggered, so match on the sha you just pushed:
   ```bash
   SHA=$(git -C <repo checkout> rev-parse HEAD)
   RUN=$(gh run list -R Metta-AI/cogame-<slug> --workflow ci.yml --event push \
           --json databaseId,headSha,createdAt -L 10 \
         | jq -r --arg s "$SHA" '[.[]|select(.headSha==$s)]|sort_by(.createdAt)|last|.databaseId // empty')
   gh run watch "$RUN" -R Metta-AI/cogame-<slug> --exit-status || \
     gh run view "$RUN" -R Metta-AI/cogame-<slug> --log-failed
   ```
4. On red, feed the failing log back to the builder. Do not fix by weakening or deleting a test —
   that is failure, not completion.
5. When green, tune the scripted baseline with a grid harness in CI (sweep its parameters, keep the
   config that plays the game well) and assert bounded, legal orders in a test.

## Exit criterion

`ci.yml` conclusion `success` on `main`, at a commit whose tree contains: the manifest template with
`num_agents` everywhere, `tools/build_replay_viewer.sh`, `tools/ci/docker_smoke.sh` (executable),
`tools/ci/policies.json`, all three workflows, both policy entry points, and the tests the design
note listed. No unsubstituted placeholder survives:

```bash
if grep -n '<slug>\|<IMAGE>\|<SEATS>' \
  .github/workflows/ci.yml .github/workflows/coworld-release.yml \
  .github/workflows/coworld-submit.yml tools/ci/docker_smoke.sh tools/ci/policies.json
then echo "::error::unsubstituted placeholders remain"; exit 1; fi
```
Grep for those **three names only** — never a bare `<`. Substitution is global and deliberately
includes comments, so four angle-bracket names survive by design and are runtime values, not
residue: `<cow_id>`/`<sha>` in `ci.yml`'s static-replay-route comment, `<run_id>` in the
artifact-readback recipes in `coworld-release.yml` and `coworld-submit.yml`, and `<name>:vN` in
`coworld-submit.yml`'s `policy` input description. `templates/README.md` lists them as expected
residue — do not file them as findings.

## Writes

- STATE: `repo`, `phase: "30"`, `review_round: 1`, `heartbeat_at`.
- `log.md`: one line per push/CI attempt with the run id and conclusion.
- Asana: complete the phase-20 subtask; comment with the repo URL and the green CI run URL.

## Retry budget

3 builder rounds against a red CI (each round must change approach, and say how, in `log.md`).
On exhaustion → `prompts/90-blocked.md` with the failing job name and the last 40 log lines —
**scrubbed** per `prompts/90-blocked.md` step 2 (CI logs carry tokens in URLs; mask anything
token-shaped before it leaves the sandbox).
