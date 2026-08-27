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

### RECIPE `dispatch-then-watch` — the only way to find the run you just started

**Never `gh run list … -L 1` straight after `gh workflow run`.** The dispatch returns before the
run is registered, so the newest row is often the *previous* run — you then watch a finished run
and download **its** stale artifact as this dispatch's evidence. Record the dispatch time first
and poll until a `workflow_dispatch` run created at or after it appears (Z-suffixed ISO-8601
timestamps compare correctly as strings):

```bash
REPO=Metta-AI/cogame-<slug>
WF=coworld-release.yml            # or ci.yml, coworld-submit.yml
dispatched_at=$(date -u +%FT%TZ)
gh workflow run "$WF" -R "$REPO" --ref main -f …
RUN=""
for i in $(seq 1 24); do                                   # 24 × 5 s = 120 s ceiling
  RUN=$(gh run list -R "$REPO" --workflow "$WF" --event workflow_dispatch \
          --json databaseId,createdAt,status -L 5 \
        | jq -r --arg t "$dispatched_at" \
            '[.[]|select(.createdAt >= $t)]|sort_by(.createdAt)|last|.databaseId // empty')
  [ -n "$RUN" ] && break
  sleep 5
done
[ -n "$RUN" ] || { echo "no workflow_dispatch run registered within 120 s"; exit 1; }
gh run watch "$RUN" -R "$REPO" --exit-status || true       # never let a red run abort the phase
```

Every phase that dispatches a workflow uses this recipe by name and does not restate it:
`prompts/20-build.md` (for a **push**-triggered `ci.yml` run the same rule applies with
`--event push` and a `headSha` match on the commit you just pushed), `prompts/40-release.md`
(`coworld-release.yml`), `prompts/50-league.md` (`coworld-submit.yml`, twice).

### Dispatching and reading a release

```bash
# `policies` is OPTIONAL — empty means "read tools/ci/policies.json from the repo",
# which phase 20 scaffolds. Pass it only to override that file for one dispatch.
# Dispatch and find $RUN with the dispatch-then-watch recipe above, then:
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
 "policies":[{"name":"<slug>-<prompt-name-1>","version":"v1","policy_version_id":null,"player_id":null}],
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
| Any real-time game loop (grid or continuous physics) with rules written for this coworld, RL-vector policies | `Metta-AI/coworld-ctf` (paintbot) — "the best coworld we have" | ctf |
| Bit-exact port of an existing, external C/RL env (rules pre-exist as code) | `Metta-AI/cogame-moba` + its `docs/PORTING.md` | moba → nmmo |

New physics games (Cogball, Lantern, Tandem) take paintbot, not moba — operator ruling 2026-08-22.
| Game logic in an external engine/process | `Metta-AI/cogame-factorio` (Python connector, per-seat servers) | factorio |

The local skill said "if the mapping isn't obvious, ASK". A cloud agent **does not ask** —
starter choice is a rail it decides itself (SPEC §Rails). It escalates to phase 90 only when the
idea leaves a *rule* genuinely open and the readings give materially different games.

Pins that are never optional:

- Repo `Metta-AI/cogame-<slug>`, **public** — public is a certification prerequisite
  (`source-resolves` 404s on private).
- Build **both** an LLM/strategy policy and a scripted baseline from day one (same image,
  env-switched: `PLAYER_PROMPT` vs `PLAYER_SCRIPTED=<baseline name>`).
- **Watchability is a requirement, not polish:**
  - Reuse the starter's replay-viewer **chrome verbatim** — same scrubber, transport bar,
    scorebug. Treat the starter's `client/renderer.js` as the exact template. "Verbatim" means
    the starter's page **plus an appended game block** and a byte-identical `chrome_common.js`;
    a from-scratch page that reuses the starter's ids is not it (cogame-gridlock, 2026-08-23).
    Transport rules: `--band`/`--hudscale` on `:root`, nothing overlaid in the transport band,
    the endcard stops above it and every seek dismisses it, scrubber beats are clickable labelled
    buttons. The zoom bar + minimap (`#viewpanel`) exist only for boards larger than the frame —
    a fixed arena removes them.
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
  episodes without it. It lives **inside each variant's `game_config`** (and
  `certification.game_config`), never at the variant's top level: `CoworldVariant` is
  `additionalProperties: false` and rejects a variant-level `num_agents`
  (cogame-goofspiel-oshi-zumo 0.1.0, 2026-08-26).

Build the game, then prove it in CI: sim tests, scripted-bot test, an end-to-end episode that
writes a replay, and a viewer smoke. The sandbox cannot run any of these locally — `ci.yml` is the
only harness.

---

## Phase 1 — Build, certify, upload (one dispatch)

Repo must contain, before the first dispatch:

- `compose.yaml` — service name = coworld name, `platform: linux/amd64`,
  `build: {context: ., network: host}`.
- `coworld_manifest_template.json` with image `{{<SERVICE>_IMAGE}}`, `num_agents` in every
  variant's **`game_config`** (variant top level rejects it — see §Phase 0),
  `"replay_viewer": {"bundle": "static-replay-viewer"}`, and a cert fixture whose `game_config`
  also carries `num_agents`.
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
- **Secret** is `anthropic_api_key`; the workflow puts it from the repo's `ANTHROPIC_API_KEY` secret (propagated by coworld-builder's `propagate-secrets.yml`),
  after `upload-coworld`.
- **LLM players on Bedrock:** force JSON with a system prompt demanding the reply **begins with
  `{`** (Haiku answers prose-first otherwise); Haiku 4.5 rejects `output_config.effort`;
  `maxOutputTokens` 900, not 400 (`cut off at max_tokens`).

---

## Phase 2 — Policies

Policies are minted by `tools/ci/policies.json` in the repo (or the `policies` input of the same
release dispatch, which overrides it for one run). **Every `upload-policy` call mints a fresh
`vN`, even for byte-identical content** (observed across three dispatches, cogame-knights-archers
2026-08-26 — the earlier "identical content dedupes" note is wrong): after any re-dispatch, take
the labels from the LAST successful `release-result.json` and resolve UUIDs by exact `<name>:vN`
match, never "the only version of that name". You need distinct policies for: champion #1,
champion #2, and every filler.

The canonical set: **two LLM prompt champions** (champion #1 owned by daveey, champion #2 by
daveey-1) plus **≥1 scripted filler, normally 2**. Bullwhip's real set was `bullwhip-steady`
(champion #1), `bullwhip-forecaster` (champion #2), `bullwhip-basestock` and `bullwhip-mirror`
(fillers):

```json
[{"name":"<slug>-<prompt-name-1>","run":"/bin/<slug>-player","env":{"PLAYER_PROMPT":"…"}},
 {"name":"<slug>-<prompt-name-2>","run":"/bin/<slug>-player","env":{"PLAYER_PROMPT":"… different …"},
  "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
 {"name":"<slug>-<baseline-1>","run":"/bin/<slug>-player","env":{"PLAYER_SCRIPTED":"<baseline-1>"}},
 {"name":"<slug>-<baseline-2>","run":"/bin/<slug>-player","env":{"PLAYER_SCRIPTED":"<baseline-2>"}}]
```

A **scripted policy seated as a champion is a FAILURE state** (see §Definition of done) — both
champions run `PLAYER_PROMPT`.

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
curl -sS -X POST \
  "https://discord.com/api/v10/channels/1440464430646427718/messages" \
  -H "authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "content-type: application/json" \
  -d '{"content":"**<Slug>** is live — <one line on the game>. Watch: https://softmax.com/<slug>","flags":4}'
```

`"flags":4` is `SUPPRESS_EMBEDS` — required, the post must not unfurl its links into embed
cards. Response `id` is the message id; record it in STATE. To strip embeds from a message
that was already posted without the flag: `PATCH .../messages/<id>` with `{"flags":4}`.

---

## Common mistakes

- **TypeScript/pnpm-lineage coworlds (cogherence forks): the release workflow must build the JS bundles** (`pnpm install --frozen-lockfile && pnpm build`) before `coworld build`/manifest — the Dockerfile COPYs `dist`/`dist-server` and the stock template has no node step (territory 0.1.0, 2026-08-25). Playwright installs go in `$RUNNER_TEMP` (`npm install --no-save` breaks on `workspace:*`).

| Symptom | Cause / fix |
|---|---|
| phase-60 check 5 red with `falling back` hits while the sidecar shows all-200, no throttling | `attempt1Ms` sits below the hosted BATCH p90 (the deadline covers all seats' parallel calls + sidecar queueing, not one call) — raise the deadlines (pommerman 0.1.1: 12000/5000/18000) and reword the attempt-1 retry notice to `will retry`; only a genuine fallback may say `falling back` |
| "replay viewer bundle must be uploaded first" | the pinned `coworld` CLI is < 0.1.42: it does not wait for the server to finish expanding the replay-viewer bundle before POSTing the manifest (`_wait_for_replay_viewer_bundle` added in 0.1.42). Bump `COWORLD_PKG` in the workflow (seen: cogame-lighthouse run 32603113899, 2026-08-22) |
| `coworld secret put` 404 | ran before `upload-coworld` — order matters |
| Upload rejects "Coworld secret <ns> cannot be used by Coworld" though local certify passed | the secret namespace must be **`game.name`**, not the slug — they differ whenever the game name has an underscore (`commons_family` vs `commons-family`). Read `game.name` from the manifest in the `secret put` step (cogame-commons-family 0.1.1, 2026-08-24) |
| Local `Certify locally` times out at ~61 s on a fixture that plays fine | `coworld certify` defaults to `--timeout-seconds 60` covering start + connect grace + every round + post-game linger. Size the cert fixture to `grace + rounds×pacing_floor + linger < 50 s` and pin it with a test (cogame-commons-family 0.1.0, 2026-08-24) |
| Manifest upload: "2 validation errors for Coworld Manifest" on `game.protocols` | `game.protocols.player`/`.global` (like `game.docs.readme`) must be `{"type":"text","value":…}` objects, not bare strings — repo CI does not catch it, the platform validator does (cogame-garble v0.1.0, 2026-08-24) |
| Manifest build: `game.description` Field required / `game.tags` Extra inputs are not permitted | the validator requires `game.description` and forbids `game.tags` (tags live top-level only); pin both in the repo's manifest test (cogame-pistonball 0.1.0, 2026-08-26) |
| Manifest build: `variants.N.num_agents — Extra inputs are not permitted` | `num_agents` belongs inside `variants[].game_config`, never at the variant's top level (`CoworldVariant` is `additionalProperties: false`; the platform reads only `game_config.num_agents`). Pin its absence at variant level in the manifest test (cogame-goofspiel-oshi-zumo 0.1.0, 2026-08-26) |
| Upload 400 `player cpu limit '500m' is below the minimum of '1'` | bundled `player[].resources.limits.cpu` minimum is `"1"` — use the starter's `{requests: 100m/64Mi, limits: {cpu: "1"}}` even for 20 lightweight seats (cogame-pistonball 0.1.1, 2026-08-26) |
| Certify locally: matriculate rejects "game_config must not include runner-managed tokens" | a variant or the cert fixture carries a literal `tokens: […]`; remove it from every `game_config` — `config_schema` keeps *requiring* `tokens` because the runner injects them (cogame-knights-archers 0.1.0, 2026-08-26) |
| Hosted certification `failed`, `failed_step: smoke-episode`, detail = the certifier's own internal `…/v2/episode-requests` call 404ing, `retryable: false` — while local certify passed 10/10 and hosted smoke passed | platform route churn, not a game defect. Bump the version and re-dispatch with no code change once the backend settles; cross-check another run/coworld to confirm it is churn (cogame-knights-archers 0.1.2→0.1.3, 2026-08-26) |
| `Upload the policies` fails on the FIRST `upload-policy` only: HTTP 400 `Container image img_… is not ready` — the rest upload seconds later | cold-image reconciler race right after the image registers; not a game defect. Bump the version and re-dispatch (cogame-flatland 0.1.3, 2026-08-27) |
| Local certify `smoke-episode`: `Bad player token was accepted: ws://…/player?slot=0&token=bad` | the certifier probes with a wrong token; the player websocket handler must close unless the token matches the seat (coworld-ctf does; a fresh-written server may not — cogame-flatland 0.1.1, 2026-08-27) |
| Champion renamed "Baseline (N)" | champion version listed as filler — mint distinct filler versions |
| "No featured match yet" | only one ranked player — submit the daveey-1 champion |
| Episode discarded ~20 min | game unaware of timeout — settle early inside 60 % of `episodeTimeoutSeconds` |
| Zero episodes scheduled | `num_agents` missing from a variant / cert fixture |
| League episodes all `game_unhealthy` exit 1, no logs, cert was green | a config-scaled resource mint blew mettagrid's one-byte feature-id cap (256) at the variants' `max_steps` while the smaller cert fixture fit — test EVERY variant's `game_config` constructs, not just the fixture (cogame-collab-cooking 0.1.1, 2026-08-25) |
| Phase 40 `Certify locally` fails `manifest_invalid` on a template repo CI passed | run the installed coworld's own `_load_template_manifest` as a CI step: 0.1.42 wants `game.replay_viewer` (not top-level), no top-level `version`, no `game.display_name`, `game.owner` required, and no runner-managed `tokens` in the cert fixture (cogame-collab-cooking, 2026-08-25) |
| Upload OK but not canonical | completion race — bump version, re-dispatch |
| `upload-coworld --wait-hosted-smoke` green but "Canonical: no" / "Hosted certification: certifying", EVERY dispatch | not the completion race and a bump does NOT fix it: the CLI returns when hosted smoke passes, ~2 min before hosted certification settles the canonical flag. Add a "Confirm canonical" step between upload-coworld and secret put that polls `uvx --from "$COWORLD_PKG" coworld status <cow_id> --json` → `.coworld.canonical` (up to 900 s). Do NOT poll with a raw urllib/curl GET from the runner — it HTTPErrors where the CLI's authenticated client works (cogame-atari-cabinet 0.1.0–0.1.3, 2026-08-26) |
| cow_id changed after a re-release | expected, always — cow ids are per-version; only the newest row is canonical and `game.canonical_coworld_id` auto-follows. Update STATE/VERIFY/announce to the new id (cogball 0.1.5, 2026-08-23) |
| Speech bubbles / captions render as slivers or read cut short, everything green | text drawn at a negative coordinate: the string was laid out relative to something else (a bubble growing upward from a cog at the top of the arena) with no room reserved for it. A canvas accepts the draw silently, so the load signal, the soak and the screenshot all pass. Reserve a **band in the layout** sized from the server's own cap on that string (`MaxSayLen`), measured in the font it is drawn in, and run `viewer_smoke.mjs --strict-text-bounds` in the wasm-viewer job — for a fixed arena `canvas_text.never_inside` must be 0. Gate on `never_inside`, not `outside`: an entrance animation that slides a card on from off-frame is outside for a few frames by design (cogchemists, 2026-08-24) |
| Viewer chrome that shows LLM text (speech bubbles, remark feed, notes panel) is never exercised by CI | `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY`, so every seat plays the scripted baseline and a scripted baseline emits no `say`/`notes` — **every replay CI produces carries zero LLM text**. Nothing that plays a replay can draw that chrome. Ship a worst-case renderer fixture (`tools/ci/renderer_fixture.html`: loads the real renderer, full-cap remark on every seat, several canvas sizes, self-checks its own string lengths) and run `viewer_smoke.mjs --strict-text-bounds` against it in its own ci.yml step (cogchemists, 2026-08-24) |
| Viewer passes the CI load test but freezes mid-replay when played | mid-replay exception latches `static_replay.js` into `failed` (cogball 0.1.4: starter-inherited `pushFeed` signature drift); scrub readouts pass because seeking skips the killing frame. Run `viewer_smoke.mjs --soak` (uninterrupted playback must keep advancing) in the wasm-viewer job |
| League "works" but looks dead | only fillers playing — the whole point is champions visibly playing well |
| `softmax player use <name>` fails | use the `ply_id`; don't `create` (409 at cap) |
| Cert fails `manifest_invalid: game.config_schema.properties.<arr> must declare minItems and maxItems` | every ARRAY property in `config_schema` needs `minItems`/`maxItems` bounds, not just `required` membership (tandem 0.1.0, 2026-08-23; bound `tokens` to num_agents) |
| Scrubber beats render as unlabeled divs / never seek, all static greps green | game-block `function markBeat` shadowed by the chrome alias block's `var markBeat = C.markBeat` (hoisting) — rename the game-block builder and add a scope-duplication test over the alias list (tandem, 2026-08-23) |
| `upload-policy`: "Docker image is not available locally" | `upload-coworld` pruned the image — policies must run **before** upload-coworld in the workflow |
| Cert fails "completed without a replay URL", artifacts exist in S3 | reconciler race on a cold image — **bump version, re-upload**; it passes the second time |
| daveey-1 submit 409 "already assigned to player" | version owned by daveey — upload a fresh policy while daveey-1 is active |
| Episodes done in ~20 s, `LLM provider is unavailable` in game log | platform Bedrock sidecar outage (all LLM coworlds) — wait, don't debug the game |
| zsh eats a var (`status` is reserved in zsh) | a **local macOS/zsh** trap only. The cloud sandbox is Linux running `bash`: call plain `curl`, and never pin `/usr/bin/curl` — that absolute path is a macOS workaround and is not necessarily where `curl` lives on the sandbox image. |
| `release-result.json.policies[].policy_version_id` is `null` | expected, always — `upload-policy` prints no uuid. Resolve UUIDs from `GET /policy-versions`, filtered client-side on `policy_name`. |
| `release-result.json.certify` is `null` | `skip_certify` was true. That is a debugging switch; re-dispatch without it. `null` means "not checked", not "failed". |
| CI red on a missing script | `tools/ci/docker_smoke.sh` absent or not `chmod +x`, or `tools/build_replay_viewer.sh` missing — both are phase-20 scaffold, not later work |
| `SEAT-COUNT FAIL:` in the docker-smoke log | one of four seat-count invariants broke: `certification.game_config.num_agents` missing, not a positive integer, or disagreeing with `len(certification.players)` / `len(certification.game_config.players)` / `SMOKE_SEATS`. The message names the manifest path — fix the fixture, not the script. Grep for the prefix; never trust the job colour alone. |
| Release fails at "Build the Coworld manifest" with pydantic errors | manifest predates the `coworld` 0.1.42 upload contract: `game.runnable.type:"game"` required; `episode_timeout_minutes` top-level; bundled players top-level `player[]` with id/type/name/description; `variants[].description` required; `game.config_schema` a real JSON Schema (CLI validates variants + cert fixture against it, injecting `tokens`); `$schema` + ≥3 `tags`. Validate offline with the CLI's `validate_upload_manifest` before dispatching (hive 0.1.0, 2026-08-23) |
| Champion seats fall back to scripted on a large share of turns in a formal-output (DSL) game | prompt drills alone only halve it — precompute the legal choice set in the observation (list membership computed by the same predicate the validator applies), accept trailing prose in JSON extraction, normalize the structured field pre-parse (escrow 0.1.3, 2026-08-23) |
| A champion (or filler) plays the scripted DEFAULT baseline for a whole episode, `latency_ms:0`, no error anywhere | the seat's register packet was lost after join — the server fell back to the default script silently (grf-football round 2, 2026-08-27: champion 24/24 scripted, 24 not 48 bedrock calls). Make the server log loudly / refuse to start when a seat has no register record; audit replays by per-seat `llmTurns` and bedrock-call count = seats × turns |
| Round 1 fails "Temporal RoundWorkflow failed before settling the round" immediately after seeding | it auto-fired at settings time, before champions/fillers existed — expected, not a defect; the round you trigger after the fillers are registered is what counts (escrow, 2026-08-23) |
| After a re-release the ladder keeps playing the OLD champions | policy uploads never dedupe: every release mints new versions for ALL policies, unchanged fillers included — resubmit both champions at the new labels AND re-register fillers with the new UUIDs before triggering (escrow v3→v4, 2026-08-23) |
| League episodes all play scripted despite `secret put` ok | the game runnable's manifest `env` lacks `ANTHROPIC_API_KEY_URI: secret://coworld/<slug>/anthropic_api_key` — the hosted container never receives the secret. Local certify still passes (client disables itself offline), so this only surfaces at phase 60 check 4 (hive, 2026-08-23) |
| League episodes all play scripted; policies are player-side LLM (factorio lineage) | the policy `env` in `tools/ci/policies.json` lacks `USE_BEDROCK: "true"` — the platform gates the player pod's Bedrock sidecar on it (`resolve_player_bedrock`); `PLAYER_PROMPT` alone gets no sidecar and the seat silently plays scripted; invisible to `results.fallbacks` and the hosted log (player stderr not bundled); surfaces only at phase-60 check 4 (cogolf, 2026-08-24) |
| First round `failed: Temporal RoundWorkflow failed before settling the round` seconds after seeding | a round auto-created before fillers/champion #2 were registered. Not your trigger: exclude it from the trigger budget, verify your own round's `entrant_attributions` carries both champions (hive, 2026-08-23) |
| **Scripted baseline oscillates wildly / "bullwhip" in a game that should be damped** | **stale binary** — game logic was edited but the smoke ran the previous build. Rebuild before every smoke; in CI make the smoke job `needs:` the build job, never reuse a cached binary. Cost one hour on bullwhip (2026-08-22). |
| **Replay bytes fail a strict JSON parser but render in a browser** | a string was truncated on a **byte** boundary mid-UTF-8. Truncate every string that lands in the replay (`say`, `notes`, prompts, error text) on **rune** boundaries. |
| **Round fails instantly: "Temporal RoundWorkflow failed before settling the round"** | `trigger-round` fired before any filler policy existed. **Set filler policies BEFORE the first trigger-round.** Two triggers were burned this way on bullwhip. |
| `GET /episode-requests?division_id=…` → 500 | that filter is broken. Use `round_id=<round>` or `coworld_id=<cow>`. `league_id=` and `coworld_name=` are **silently ignored** (you get unrelated rows and believe them). |
| `GET /policy-versions?name=…` returns other games' policies | the `name=` filter is ignored — fetch and filter **client-side** on `policy_name`. |
| Manifest rejected / docs missing on the coworld page | `game.docs` must be `{"readme":{"type":"text","value":"…"},"pages":[{"id","title","content":{"type":"text","value":"…"}}]}`, and `game.protocols` must carry **both** `player` and `global`. |
| Player names collapse to "…" in the featured match | the embedded featured-match iframe is ~360 px wide. Give `.plate-name` `flex: 1 1 auto; min-width: 3.2em`, and hide labels under `640px`. Check the scorebug at 360 px, not at desktop width. |
| LLM game blows the 720 s play budget | seats were queried **sequentially**. For simultaneous-decision games, issue all seats' LLM calls as **one parallel batch per turn** (`curly.makeRequests` in Nim). |
| `coworld build`: "Coworld image placeholder does not match a Compose service: {{GAME_IMAGE}}" | manifest image placeholders are derived from **compose service names** (`service lantern` → `{{LANTERN_IMAGE}}`); `{{GAME_IMAGE}}`/`{{PLAYER_IMAGE}}` are not a thing. Derive the placeholder from `compose.yaml` in the manifest generator (lantern 0.1.0, 2026-08-23). |
| Cert smoke-episode `game_contract_violation: HTTP contract check failed … /client/player … 404` | the episode runner probes `/healthz`, `GET /client/player?slot=0&token=<t>`, a bad-token player websocket, and `GET /client/global` **before starting player pods**. Serve real pages on both `/client/` routes (registered before any catch-all asset route); neither may open the player socket (lantern 0.1.1). |
| Cert smoke-episode `Game websocket did not answer a WebSocket Ping with Pong: …/global` | the runner pings `/global` (2 s deadline) **after** the player pods start — a short episode may already have exited. Keep `/healthz` + `/global` answering for a bounded shutdown grace (~20 s) after artifacts are written, then exit; the runner waits on process exit anyway (lantern 0.1.3 → fixed in 0.1.4). |
| Policy labels bump vN on every release even with identical prompts | versions do **not** dedupe across releases — the image digest changes, so each release mints `<name>:v(N+1)`. Phase 50 must use the vN from the **successful** release; stale v(N−1) fillers make the ladder schedule a stale image or rename a champion "Baseline (N)". |
| Every `git push` to GitHub suddenly fails "Invalid username or token" — including to coworld-builder, which pushed fine minutes earlier | a sub-agent ran `gh auth setup-git`, which overwrites the sandbox's working helper (`/usr/local/bin/git-credential-anthropic`) in `~/.gitconfig` with gh's own (whose basic-auth b64 defeats egress substitution). Never run `gh auth setup-git`; repair with `git config --global credential.helper /usr/local/bin/git-credential-anthropic` (raid, 2026-08-23). |
| Cert `players-run` fails `players_missing`: "player[N] ('<name>') has no certification slot" | **every** player entry declared in the manifest must occupy a slot in `certification.players` — a fixture of `baseline × N` fails the moment the manifest also declares other runnables. Seat each declared player at least once; keep the strong baseline on the seats that decide the fixture's outcome (raid 0.1.2 → 0.1.3, 2026-08-23). |
| Git Data API push to a brand-new repo 409s `Git Repository is empty` | the Data API cannot create a repo's first object — bootstrap the initial commit via the Contents API (one file), then blobs→tree→commit→ref work normally (ecos, 2026-08-23) |
| `tools/build_replay_viewer.sh` exits 1 when `ci.yml` runs it on a fresh checkout | paintbot's hook resolves its output path by `cd`-ing into the parent, which does not exist yet in CI (`coworld build` pre-creates it, CI does not). `mkdir -p` the parent before the containment check — every fork of paintbot's hook inherits this (ecos, 2026-08-23) |
| `wasm-viewer --soak` reports a finished replay as frozen | the smoke replay is shorter than the soak window (e.g. 90 ticks = 3.75 s < a 10 s soak), so playback legitimately ends and the last interval cannot advance. Size the cert/smoke fixture so the replay outlasts the soak (ecos: 6×60 ticks = 15 s, 2026-08-23) |
| Cert smoke-episode `player_error`: "Player container exited with status 1", player log ends in `receiveFrame … Error receiving WebSocket frame` | whisky's `receiveMessage` **raises** on a close frame or truncated read (only timeout returns `none`), and mummy's `send` only queues — the game's `quit(0)` can outrun the flushed `done` frame. Race: passes one dispatch, fails the next. Fix in the **player**: wrap the receive loop in `try/except CatchableError` and exit 0 on a dead socket. Also make `docker_smoke.sh` assert every **player** container's exit code (cert does; the starter smoke only checks the game's). Latent in `cogame-bullwhip/src/bullwhip_player.nim` (raid 0.1.3 → 0.1.4, 2026-08-23). |
| Hosted log: `bedrock_sidecar_rate_limited … 30 requests/minute` + fallbacks on a **fast** episode only | the sidecar caps **30 req/min per episode** and sim-time pacing gives no wall-clock floor: 2 LLM seats at ~2 s wall/turn ≈ 57 rpm. Intermittent — slow episodes stay under. Floor the inter-batch wall spacing (e.g. ≥ 4 s between batches for 2 seats). And the ladder fallback `us.anthropic.claude-sonnet-4-6` **times out on every sidecar call** — one throttle cascades into scripted fallbacks; keep haiku, drop that candidate (raid round 2, 2026-08-23). |
| viewer smoke green but softmax.com embed samples an unpainted shell (clock on the `BAR 0` placeholder, dead scrubber) | the shell posts the `coworld-replay` bridge `ready` on rAF timing at the call site, before `attachReplay`'s render callback draws the first frame — and `viewer_smoke.mjs` accepts `ready` **or** `data-replay-loaded`, whichever first, so CI cannot catch the wrong order. Post `ready` from a callback fired after `data-replay-loaded="true"` is set (chorus `3c11c953`, 2026-08-24) |
| Cert smoke-episode `episode_timeout` "Timed out waiting for game container to exit" at ~60 s, on a fixture that is otherwise green | `coworld certify` defaults `--timeout-seconds 60`. Size check: fixture rounds × ticks ÷ tickHz + shutdown grace; if > ~40 s, add `--timeout-seconds 300` to the certify step in `coworld-release.yml`. Do not shrink the fixture — the viewer soak needs the derived smoke replay long (cooperative-hunting 0.1.2 → 0.1.3, 2026-08-25) |
| `upload-coworld` HTTP 400 "Coworld secret <ns> cannot be used by Coworld '<name>'" after a fully green certify | the `secret://coworld/<ns>/…` namespace must equal `game.name` exactly. The template's single `SLUG` conflates the hyphenated image slug with the secret ns; an underscored `game.name` breaks at upload and certify cannot see it. Fix ns in `build_manifest.py`, the manifest template, and the release workflow's `secret put`; leave ci.yml's SLUG alone. Related: `POST /coworld-league-seeds` also wants `game.name`, not the page slug (cooperative-hunting, 2026-08-25) |
| Deadline-ended replays hash-mismatch at the stop tick (viewer shows a hash warning on every slow-LLM episode) while `complete` replays are clean | the wall-clock stop banks the round + finishes the game OUTSIDE `sim.step` and the same iteration still records the hash; a wall-clock fact cannot be re-derived from sim state. Record the stop as one load-bearing record applied by the SAME proc on record and playback, bump GameVersion, and add a record→re-derive test for EVERY end reason, not just complete (particle-worlds 13c66d7, 2026-08-26) |
| Renderer fixture passes `--strict-text-bounds` but the shipped chrome clips text anyway | the fixture re-implements the drawing instead of executing the shipped page (Worker/OffscreenCanvas renderers make the main smoke's `canvas_text` 0, so the fixture is the ONLY text gate). Load the real `dist/static-replay-viewer/index.html` in an iframe, shim only the wasm entry, drive the page's own text path, and transcribe DOM runs to canvas at measured geometry (particle-worlds 46cf69d, 2026-08-26) |

---

## Integration

Pairs with `playbooks/observatory-api.md` (exact call shapes), `ks.build-submit-policy` (policy
packaging), `ks.coworld-player-gotchas` (player-side hangs/zero-score traps), and
`cogame-moba/docs/PORTING.md` (bit-exact env ports).
