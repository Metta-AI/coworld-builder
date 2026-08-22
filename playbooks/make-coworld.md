# Make a Coworld — cloud agent playbook

Faithful rewrite of the local `softmax:make-coworld` skill for an agent with **no Docker, no
Nim, no emsdk, no `coworld`/`softmax` CLI**. Every step that the local skill ran as
`cd ~/code/metta && uv run coworld …` runs instead as a **GitHub Actions workflow dispatch in
the coworld repo**; everything else is plain HTTPS from the sandbox.

Call shapes for the HTTPS half live in [`observatory-api.md`](observatory-api.md). Do not
re-derive them.

---

## Definition of done

**Done = rounds completing on softmax.com AND replays rendering at `https://softmax.com/<slug>`,
with two ranked players on the board.** Not a green repo, not a passing cert. Never report done
without having fetched a round, a leaderboard, and a replay URL yourself. A league where only
trivial fillers play is a FAILURE state — real champion policies must be in and visibly doing the
thing the game is about.

---

## The cloud substitution rule

| Local skill said | Cloud agent does |
|---|---|
| `uv run coworld build --project … --version X` | dispatch `coworld-release.yml` |
| `uv run coworld certify dist/coworld_manifest.json` | same dispatch (step 2 of the same run) |
| `uv run coworld upload-policy …` | same dispatch (`policies` input) |
| `uv run coworld upload-coworld …` | same dispatch |
| `uv run coworld secret put …` | same dispatch (`put_secret: true`) |
| `docker build …` / any local image work | the workflow's runner; never the sandbox |
| `uv run coworld submit …` | dispatch `coworld-submit.yml` (artifact `submit-result`) |
| `uv run softmax player use/unset` | inside `coworld-submit.yml` only |
| `uv run coworld episode-logs …` | `GET /episode-requests/<id>/artifacts/logs` (HTTPS) |
| league seed / divisions / settings / fillers / trigger / verify | direct HTTPS — no docker needed |
| "the metta checkout must be at origin/main" | not applicable; CI installs metta fresh from main |

### Dispatching and reading a release

```bash
REPO=Metta-AI/cogame-<slug>
# `policies` is OPTIONAL — empty means "read tools/ci/policies.json from the repo",
# which phase 20 scaffolds. Pass it only to override that file for one dispatch.
gh workflow run coworld-release.yml -R "$REPO" --ref main \
  -f version=0.1.0 \
  -f put_secret=true
# find the run just started, then block on it
RUN=$(gh run list -R "$REPO" -w coworld-release.yml -L 1 --json databaseId -q '.[0].databaseId')
gh run watch "$RUN" -R "$REPO" --exit-status || true      # never let a red run abort the phase
gh run download "$RUN" -R "$REPO" -n release-result -D /tmp/rr
jq . /tmp/rr/release-result.json
```

Other inputs: `secret_key_name` (default `anthropic_api_key`), `put_secret` (default true),
`skip_certify` (default false — **debugging only, never for a real release**; it also makes the
`certify` key `null` rather than `false`, so a `null` there means "not checked", not "failed").

`release-result.json` is written **even when a step fails**:

```json
{"version":"0.1.2","ok":true,"cow_id":"cow_…","canonical":true,
 "manifest_sha":"sha256:…","hosted_smoke":"…","hosted_certification":"…",
 "certify":{"ok":true,"replay_liveness":"skipped (static replay bundle declared…)","output_tail":"…"},
 "policies":[{"name":"<slug>-steady","version":"v1","policy_version_id":null,"player_id":null}],
 "secret_put":true,"errors":[],"step_failed":null}
```

**`policy_version_id` is ALWAYS `null`.** `upload-policy` prints only `Upload complete: <name>:vN`
and no uuid, so the workflow cannot report one. Take the `<name>:vN` labels from here and resolve
the UUIDs the filler call needs from `GET /policy-versions` with a **client-side** filter — see
`observatory-api.md` §5. `player_id` is the owning player (`null` = the CI token's own player).

Read `step_failed` first, then `errors`, then `gh run view "$RUN" -R "$REPO" --log-failed`.
Never conclude from the workflow's green/red alone — read the JSON.

**The step order inside the workflow is load-bearing and must not be reordered:**
build → certify → **upload-policies** → upload-coworld → secret put. Policies before
`upload-coworld` (the upload prunes the local image, after which `upload-policy` fails
"Docker image is not available locally"); `secret put` after it (404 otherwise).

---

## Phase 0 — Starter repo and design pins

**Never green-field. Fork the conventions of the closest existing coworld:**

| Game shape | Starter | Lineage |
|---|---|---|
| Turn-based / talk / cards / board / dice / bluff; game logic native; policy = LLM prompt | `Metta-AI/cogame-babel` (best current parley-stack template), else newest parley descendant (`cogame-bullwhip`, `cogame-focus`, `cogame-cosino`) | parley → cosino → focus → babel → bullwhip |
| Real-time grid, RL-vector policies | `Metta-AI/coworld-ctf` (paintbot) — "the best coworld we have" | ctf |
| Port of an existing C/RL env, bit-exact | `Metta-AI/cogame-moba` + its `docs/PORTING.md` | moba → nmmo |
| Game logic in an external engine/process | `Metta-AI/cogame-factorio` (Python connector, per-seat servers) | factorio |

The local skill said "if the mapping isn't obvious, ASK". A cloud agent **does not ask** —
starter choice is a rail it decides itself (SPEC §Rails). It escalates to phase 90 only when the
idea leaves a *rule* genuinely open and the readings give materially different games.

Pins that are never optional:

- Repo `Metta-AI/cogame-<slug>`, **public** — public is a certification prerequisite
  (`source-resolves` 404s on private).
- Build **both** an LLM/strategy policy and a scripted baseline from day one (same image,
  env-switched: `PLAYER_PROMPT` vs `PLAYER_SCRIPTED=1`).
- **Watchability is a requirement, not polish:**
  - Reuse the starter's replay-viewer **chrome verbatim** — same scrubber, transport bar,
    scorebug. Treat the starter's `client/renderer.js` as the exact template.
  - **Real art, not placeholders.**
  - **Replays are a static file + a browser wasm viewer — NEVER a pod.** The manifest declares
    `"replay_viewer": {"bundle": "static-replay-viewer"}`; the repo ships
    `tools/build_replay_viewer.sh` (the `coworld build` hook) that compiles the *same* sim module
    to wasm (`replay-viewer/<slug>_replay.nim`, emscripten) and bundles it with
    `renderer.js`/`chrome.css`/assets; the viewer re-derives every frame from the recorded events
    in the browser. Everything the viewer needs (names, config, per-tick state, seed) lives in the
    replay bytes; no server is contacted except S3 for the `.replay` file. The only admissible
    exception is an engine that genuinely cannot compile to wasm — then record a static artifact
    the bundle plays back, still no pod. Never declare a `/client/replay` live-server viewer.
  - Legible to a casual spectator: render "10" not "T"; show what agents are doing, not internal
    notation.
- **Two name spaces:** agents see anonymous cog aliases (no meta-gaming); the replay viewer maps
  aliases back to real player names for non-baseline seats (Bravo→daveey). Both, not either.
- **Degrade, never hang:** the game container does NOT receive `COWORLD_TIMEOUT_SECONDS` (only the
  worker sidecar does) — assume `episodeTimeoutSeconds` (1200), bound every wait, and settle/score
  early rather than overrun. An overrun episode is silently discarded. Play inside **60 %** of the
  budget (≈720 s).
- `num_agents` in every manifest variant AND the certification fixture — the ladder schedules zero
  episodes without it.

Build the game, then prove it in CI: sim tests, scripted-bot test, an end-to-end episode that
writes a replay, and a viewer smoke. The sandbox cannot run any of these locally — `ci.yml` is the
only harness.

---

## Phase 1 — Build, certify, upload (one dispatch)

Repo must contain, before the first dispatch:

- `compose.yaml` — service name = coworld name, `platform: linux/amd64`,
  `build: {context: ., network: host}`.
- `coworld_manifest_template.json` with image `{{<SERVICE>_IMAGE}}`, `num_agents` in every
  variant, `"replay_viewer": {"bundle": "static-replay-viewer"}`, and a cert fixture that also
  carries `num_agents`.
- `.github/workflows/ci.yml` and `.github/workflows/coworld-release.yml` from `templates/`.

```bash
gh repo create Metta-AI/cogame-<slug> --public --description "…"
git push -u origin main
gh workflow run coworld-release.yml -R Metta-AI/cogame-<slug> --ref main -f version=0.1.0 -f policies='…'
```

Then read `release-result.json` and require `canonical: true` and
`certify.replay_liveness` containing `skipped (static replay bundle declared`.

Notes that survive the move to CI:

- **If a smoke-passing upload strands non-canonical** (completion race): bump the version and
  re-dispatch.
- **The first upload of a brand-new image often fails hosted certification with "completed without
  a replay URL"** even though results + replay ARE in S3 (`/episode-requests/<id>/artifacts/…`
  return 200). That is the backend reconciler marking cold-pulling jobs completed before their pod
  is visible. Fix: bump the version and re-dispatch once the image is warm. It passes the second
  time. Do not debug the game for this.
- **Hosted game logs:** `GET /v2/episode-requests/<ereq>/artifacts/logs` with the elevated header.
- **Secret** is `anthropic_api_key`; the workflow puts it from the `ANTHROPIC_API_KEY` org secret,
  after `upload-coworld`.
- **LLM players on Bedrock:** force JSON with a system prompt demanding the reply **begins with
  `{`** (Haiku answers prose-first otherwise); Haiku 4.5 rejects `output_config.effort`;
  `maxOutputTokens` 900, not 400 (`cut off at max_tokens`).

---

## Phase 2 — Policies

Policies are minted by the `policies` input of the same release dispatch. Identical content
dedupes to the same version — **vary an env var to mint a distinct version**. You need distinct
versions for: champion #1, champion #2, and every filler.

```json
[{"name":"<slug>-steady","run":"/bin/<slug>_player","env":{"PLAYER_SCRIPTED":"1"}},
 {"name":"<slug>-basestock","run":"/bin/<slug>_player","env":{"PLAYER_SCRIPTED":"1","BASELINE":"basestock"}},
 {"name":"<slug>-forecaster","run":"/bin/<slug>_player","env":{"PLAYER_PROMPT":"…"}}]
```

`release-result.json.policies[]` gives `{"name","version","policy_version_id":null,"player_id"}`.
The `policy_version_id` is **always null** — resolve the UUIDs the filler-policy call needs from
`GET /policy-versions` (fetch, filter client-side on `policy_name`; the `name=` filter is ignored).

Per-policy extras the workflow accepts: `"player": "ply_…"` (upload that one policy while that
player is active — this is how champion #2 comes to be owned by `daveey-1`), `"image"` (override
`<IMAGE>:latest`), and `"run"` as either a string (shlex-split) or an array.

---

## Phase 3 — League (direct HTTPS, no docker)

Full bodies in [`observatory-api.md`](observatory-api.md). Order:

1. `POST /coworld-league-seeds` (`commissioner_key: platform`)
2. `GET /leagues` → `$L` where `game.coworld_name` matches
3. `PUT /leagues/$L/divisions` → `$D`
4. `POST /leagues/$L/settings` (round_robin, `filler_policy`, elo 1000/32, `round_interval_minutes` 15)

---

## Phase 4 — Champions and fillers (order matters)

1. **Champion #1 (daveey, `ply_44ae9048-3242-4654-881f-6d9d43347fa3`):** dispatch
   `coworld-submit.yml` with `player_id`, `policy=<name>:vN`, `league_id=$L`.
2. **Champion #2 (daveey-1, `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`):** the second champion's
   policy version must be **uploaded while daveey-1 is the active player** — a version uploaded as
   daveey is owned by daveey, and submitting it as daveey-1 409s "already assigned to player".
   `coworld-release.yml` honours an optional `"player"` field on a policy entry in the `policies`
   JSON — it wraps that one `upload-policy` in `softmax player use <ply_id>` …
   `softmax player unset` (the unset is in a `finally`, per policy *and* around the whole loop, so
   no failure path leaves the runner switched for `upload-coworld`). Give champion #2's policy
   `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, then dispatch `coworld-submit.yml` with
   the same id. `release-result.json.policies[].player_id` echoes the owner — assert it.
   **Two ranked players are REQUIRED** — the softmax.com featured match shows "No featured match
   yet" with fewer.
3. **Fillers:** resolve UUIDs first — `GET /policy-versions?limit=200`, filter client-side on
   `policy_name`, and pick the rows whose `<name>:vN` labels are **not** either champion's. Then
   `POST /leagues/$L/filler-policies` `{"policy_version_ids":[…]}`. **Filler versions
   MUST differ from champion versions** — the platform renames ANY seat whose version is in the
   filler list to "Baseline (N)", even a scored champion.
   **Set fillers BEFORE the first `trigger-round`.**
4. `POST /leagues/$L/rounds-paused` `{"paused":false}`; then `POST /leagues/$L/trigger-round` `{}`.

---

## Phase 5 — Verify (fetch, don't assume)

- `GET /rounds?league_id=$L&limit=5` → rounds exist and complete (not discarded/failed).
- `GET /divisions/$D/leaderboard` → both champions ranked.
- `GET /episode-requests?round_id=<round>` (**not** `division_id=` — it 500s), then
  `GET /episode-requests/<ereq>` → `replay_url` present, participants named correctly
  (daveey / daveey-1, fillers as Baseline).
- Fetch replay bytes (`https://softmax-public.s3.amazonaws.com/replays/<uuid>.replay`): must be
  **valid UTF-8 JSON**; `protocol` matches; `results.reason` is `complete` (or a `deadline` the
  design declares acceptable); events show the champion seats doing the thing the game is about.
- Fetch `https://softmax.com/<slug>`: featured match present, and the replay iframe `src` is
  `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` — never a
  `/client/replay` pod URL.
- Certification output must contain `Replay liveness: skipped (static replay bundle declared`.
- Let the 15-min cadence produce 2–3 more rounds before declaring done.
- **Read the hosted game log** of a completed episode and grep `falling back` /
  `LLM provider is unavailable` / `cut off at max_tokens` / `rejected`. An LLM game whose episodes
  finish in ~20 s is playing scripted. Sidecar 503 "LLM provider is unavailable" is a platform-wide
  Bedrock outage — check another LLM coworld's latest log; it will show the same.

---

## Phase 6 — Announce (Discord, not Slack)

Announcements go to Discord guild `1309708848730345493`, channel `coworlds`
`1440464430646427718`, via the Disco bot token. **Not Slack.**

```bash
/usr/bin/curl -sS -X POST \
  "https://discord.com/api/v10/channels/1440464430646427718/messages" \
  -H "authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "content-type: application/json" \
  -d '{"content":"**<Slug>** is live — <one line on the game>. Watch: https://softmax.com/<slug>"}'
```

Response `id` is the message id; record it in STATE.

---

## Common mistakes

| Symptom | Cause / fix |
|---|---|
| "replay viewer bundle must be uploaded first" | stale metta checkout — in CI, make the workflow install metta from `origin/main` |
| `coworld secret put` 404 | ran before `upload-coworld` — order matters |
| Champion renamed "Baseline (N)" | champion version listed as filler — mint distinct filler versions |
| "No featured match yet" | only one ranked player — submit the daveey-1 champion |
| Episode discarded ~20 min | game unaware of timeout — settle early inside 60 % of `episodeTimeoutSeconds` |
| Zero episodes scheduled | `num_agents` missing from a variant / cert fixture |
| Upload OK but not canonical | completion race — bump version, re-dispatch |
| League "works" but looks dead | only fillers playing — the whole point is champions visibly playing well |
| `softmax player use <name>` fails | use the `ply_id`; don't `create` (409 at cap) |
| `upload-policy`: "Docker image is not available locally" | `upload-coworld` pruned the image — policies must run **before** upload-coworld in the workflow |
| Cert fails "completed without a replay URL", artifacts exist in S3 | reconciler race on a cold image — **bump version, re-upload**; it passes the second time |
| daveey-1 submit 409 "already assigned to player" | version owned by daveey — upload a fresh policy while daveey-1 is active |
| Episodes done in ~20 s, `LLM provider is unavailable` in game log | platform Bedrock sidecar outage (all LLM coworlds) — wait, don't debug the game |
| zsh eats a var or curl breaks | `status` is reserved in zsh; use `/usr/bin/curl` if PATH is broken |
| `release-result.json.policies[].policy_version_id` is `null` | expected, always — `upload-policy` prints no uuid. Resolve UUIDs from `GET /policy-versions`, filtered client-side on `policy_name`. |
| `release-result.json.certify` is `null` | `skip_certify` was true. That is a debugging switch; re-dispatch without it. `null` means "not checked", not "failed". |
| CI red on a missing script | `tools/ci/docker_smoke.sh` absent or not `chmod +x`, or `tools/build_replay_viewer.sh` missing — both are phase-20 scaffold, not later work |
| `SEAT-COUNT FAIL:` in the docker-smoke log | one of four seat-count invariants broke: `certification.game_config.num_agents` missing, not a positive integer, or disagreeing with `len(certification.players)` / `len(certification.game_config.players)` / `SMOKE_SEATS`. The message names the manifest path — fix the fixture, not the script. Grep for the prefix; never trust the job colour alone. |
| **Scripted baseline oscillates wildly / "bullwhip" in a game that should be damped** | **stale binary** — game logic was edited but the smoke ran the previous build. Rebuild before every smoke; in CI make the smoke job `needs:` the build job, never reuse a cached binary. Cost one hour on bullwhip (2026-08-22). |
| **Replay bytes fail a strict JSON parser but render in a browser** | a string was truncated on a **byte** boundary mid-UTF-8. Truncate every string that lands in the replay (`say`, `notes`, prompts, error text) on **rune** boundaries. |
| **Round fails instantly: "Temporal RoundWorkflow failed before settling the round"** | `trigger-round` fired before any filler policy existed. **Set filler policies BEFORE the first trigger-round.** Two triggers were burned this way on bullwhip. |
| `GET /episode-requests?division_id=…` → 500 | that filter is broken. Use `round_id=<round>` or `coworld_id=<cow>`. `league_id=` and `coworld_name=` are **silently ignored** (you get unrelated rows and believe them). |
| `GET /policy-versions?name=…` returns other games' policies | the `name=` filter is ignored — fetch and filter **client-side** on `policy_name`. |
| Manifest rejected / docs missing on the coworld page | `game.docs` must be `{"readme":{"type":"text","value":"…"},"pages":[{"id","title","content":{"type":"text","value":"…"}}]}`, and `game.protocols` must carry **both** `player` and `global`. |
| Player names collapse to "…" in the featured match | the embedded featured-match iframe is ~360 px wide. Give `.plate-name` `flex: 1 1 auto; min-width: 3.2em`, and hide labels under `640px`. Check the scorebug at 360 px, not at desktop width. |
| LLM game blows the 720 s play budget | seats were queried **sequentially**. For simultaneous-decision games, issue all seats' LLM calls as **one parallel batch per turn** (`curly.makeRequests` in Nim). |

---

## Integration

Pairs with `playbooks/observatory-api.md` (exact call shapes), `ks.build-submit-policy` (policy
packaging), `ks.coworld-player-gotchas` (player-side hangs/zero-score traps), and
`cogame-moba/docs/PORTING.md` (bit-exact env ports).
