# r1 fixes — coworld-builder

Every finding in `reviews/r1-review.md` (14 BLOCKING, 31 MINOR), what changed, and the commit
that carries it. Commits are on `main`, unpushed. One commit per finding or per tightly related
group; the group's commit is named `r1-<lowest finding>` and its message lists the rest.

Note on shas: a concurrent session working `templates/` reset the branch twice while these
commits were being made. Nothing was lost — where a commit object was dropped, the content was
re-committed intact by the next commit, and the table below cites the sha that is **reachable
from `main` now** (verified by grepping the working tree for every fix).

## BLOCKING

| # | commit | what changed |
|---|---|---|
| 1 | `c1ee21c` | `50-league` no longer submits `<slug>-steady-llm:v1`. Both champion submissions now read the label phase 40 recorded (`STATE.policies.champion1` / `champion2`) instead of naming a policy inline. |
| 2 | `c1ee21c` | Canonical naming pinned everywhere: champion #1 and #2 are **LLM prompt policies** (`PLAYER_PROMPT`; #2 owned by daveey-1), fillers are the **scripted baselines** (`PLAYER_SCRIPTED=<name>`), ≥1 filler, normally 2. SPEC's example (`bullwhip-steady` / `bullwhip-forecaster` / `bullwhip-basestock` + `bullwhip-mirror`) is now correct and matches `templates/tools/ci/policies.json.example` verbatim, so no scripted bot can be seated as a champion. |
| 3 | `1c6818e` | The six starters are declared as read-only `github_repository` resources in `fleet/deployment.json`, mounted at `/workspace/starters/<name>`; SPEC, `10-design`, `20-build`, `agents/designer.md`, `agents/builder.md` and `fleet/cloud.md` all use that path. `deploy.py` re-supplies a token for **every** repo mount and now names them on apply. The builder still `git clone`s the starter for a clean history. |
| 4 | `9463e3c` | `heartbeat_at` is the Asana custom field `1217748424048134` (text, UTC ISO-8601, on the Coworld Builder project): read from `custom_fields[]`, written with the custom_fields map. The fallback log line has one pinned format — `<UTC ISO-8601> heartbeat phase=<nn>` — stated in both `AGENT.md` and `00-claim`. |
| 5 | `d363eaa`, `c57dd74` | Claim is comment-first: `git pull --rebase` before the dedupe read, re-GET of the idea (task + comments) immediately before claiming, the `claimed by coworld-builder run <run>` comment posted **before** the run task exists, a 20 s re-read that yields to an earlier claim, and a non-forcing rebase-and-exit if the push races. |
| 6 | `6430636` | The Blocked resume matches **`STATE.blocked.subtask`** (falling back to the `BLOCKED ` title prefix + assignee), never "a completed subtask" — the eight phase subtasks no longer look like the human ask. |
| 7 | `66ed1da` | On unblock: `phase_attempts[<phase>] = 0` **and** `blocked = null`, committed and pushed before the resume. `90-blocked` §Resume now points at `00-claim` step 3 as the code path. (Also finding 24.) |
| 8 | `0d76ebc` | `dispatch-then-watch` is one named recipe in `playbooks/make-coworld.md`: record `dispatched_at`, poll `gh run list --workflow <wf> --event workflow_dispatch --json databaseId,createdAt,status -L 5` for a run created at/after it (120 s ceiling), then `gh run watch <id> --exit-status`. Phases 20/40/50 cite it; `-L 1` appears only as a prohibition. (Also finding 33: `POLICIES=$(jq -c . tools/ci/policies.json)` is now assigned.) |
| 9 | `76c99e7` | The resume path increments `phase_attempts[<phase>]` before doing any work; at 3 it enters `90-blocked` with "phase `<n>` has ended three sessions without progress". A session-killing phase can no longer loop forever. |
| 10 | `aad66e9` | `announce.attempted_at` is written and **pushed before** the Discord POST; a resume with the marker set and no id searches `GET /channels/<id>/messages?limit=20` for this run's `https://softmax.com/<slug>` link and adopts the id it finds. Posting blind is forbidden. SPEC's STATE schema and `AGENT.md` rule 4 say the same. |
| 11 | `e81d858` | Definition-of-done item 8 is now a fetched judgment: (a) the replay JSON's events/states, (b) the bundle `index.html` at the iframe `src` **and every asset it references** (`<script src>`, `<link href>`, the `.wasm` in the module loader) all 200 with non-trivial sizes, (c) the `coworld-replay` postMessage bridge including `tell("ready")` present in the fetched `static_replay.js`/index. "No DOM readouts, no browser, no screenshot" in SPEC, `60-verify` and `agents/verifier.md`. Items 1–7 unchanged. |
| 12 | `342f3dc` | `deploy.py create` calls `live_state()` first and **refuses** if any agent or the deployment name already exists, printing each id and pointing at `update`. `--dry-run create` skips the live call (and says so) so it still runs offline. |
| 13 | `342f3dc` | `write_cloud()` merges instead of rewriting: a row this run did not resolve keeps what `fleet/cloud.md` already recorded, and **a real id is never overwritten with `TBD`**. A missing deployment no longer drops its row, and `update` exits non-zero when the deployment leg did not run. (Also finding 38: agent ids are written before the deployment POST; finding 39: `page()` now follows `has_more`/`after_id`.) |
| 14 | `342f3dc` | `cmd_update` pre-flights every role in `ROLES + coordinator` and **aborts before any POST or write** if one is missing live — the coordinator can no longer be versioned with a truncated `multiagent.agents` roster. |

## MINOR

| # | commit | what changed |
|---|---|---|
| 15 | `c1ee21c` | One filler count everywhere: "≥1 filler, normally 2". "Three fillers" / "five distinct versions" are gone from `40-release`; the review checklist says "at least four distinct policies". |
| 16 | `ae452cf` | SPEC's STATE schema gains `policies.filler_version_ids[]` (UUIDs, written by phase 50); `fillers[]` stays `<name>:vN` names written by phase 40, and 50 is told never to overwrite it. |
| 17 | `846d951` | SPEC §Phases and `agents/designer.md` now carry the **same eight H2 names** the phase prompt mandates, in order. |
| 18 | `846d951` | `40-release` owner is "builder, dispatched by the coordinator" — agrees with SPEC, `AGENT.md`, `agents/builder.md`. |
| 19 | `846d951` | The builder brief's parallel-batch requirement is scoped "for simultaneous-decision games", with the sequential case named. |
| 20 | `e984288` | `AGENT.md` cites only PROTOCOLS §ESCALATION HANDOFF, §CRUX DECISIONS, §STRUCTURED RECORDS, and says explicitly that this system's claim algorithm and its 90-min / 15-min numbers supersede §CLAIM PROTOCOL / §HEARTBEAT (which assume a *Planned* section and an `owner` field this board lacks). |
| 21 | `eaaa208` | New `STATE.session_ended_at`: the closing step stamps it, the resume clears it, and a *Running* task whose `session_ended_at` ≥ `heartbeat_at` is immediately resumable. A multi-session run advances on the **next** hourly firing instead of every other one. The 90-minute threshold is unchanged (so `templates/run-task.md`'s lock description stays true — see the templates note below). |
| 22 | `cce7203` | "Adopt the stale task with the **oldest** `heartbeat_at`; adopt exactly one per heartbeat", with the rest logged by gid. |
| 23 | `cce7203`, `c57dd74` | The Blocked→new-idea fall-through is stated as deliberate policy in `00-claim` and SPEC, and capped: **at most 2 simultaneously-Blocked runs**, after which the heartbeat claims nothing and exits. |
| 24 | `66ed1da` | `STATE.blocked = null` on resume (with finding 7). |
| 25 | `cce7203` | The phase-90 idea comment goes to `STATE.idea_task`, explicitly **not** the Ideas *project* gid `1217704774784096`. |
| 26 | `c1ee21c` | The invented `BASELINE` env var is gone: baselines are `PLAYER_SCRIPTED=<name>`, the switch the builder brief actually asks for and the example file uses. |
| 27 | `846d951` | `AGENT.md` says read `prompts/<phase>-*.md` (the glob the files actually match). |
| 28 | `846d951` | `$BUILDER_PROJECT` is written as "the Coworld Builder gid in `fleet/cloud.md`" in `AGENT.md`, SPEC and `cloud.md` — nothing exports it. |
| 29 | `cce7203` | `playbooks/observatory-api.md` §Non-Observatory calls now gives the Asana shapes the prompts need: section move (`POST /sections/<gid>/addTask`), create-in-section, the `heartbeat_at` custom-field read/write, comments and subtasks. `00-claim`'s exit criterion cites it. |
| 30 | `846d951` | README's one-time-setup lists *Running / Blocked / Done / Fleet* and notes there is no *Planned* section. |
| 31 | `846d951` | "if the review has no findings: the judge still runs" is in the phase-30 loop block. |
| 32 | `846d951` | `round = max(STATE.review_round, 1)` — a resume into phase 30 cannot write `r0-*.md`. |
| 33 | `0d76ebc` | `POLICIES` is assigned where it is used (and marked as override-only). |
| 34 | `214d0bf` | The `fleet/mirror/` promise is removed from SPEC §Runtime and §Repo layout: git is the source of truth, `deploy.py update` is the reconciler, and the mirror/diff pair is named as a cogamer-fleet duty this repo does not have. |
| 35 | `7d89a6a` | `mcp_servers` added to `VERSIONED_FIELDS` with the comment naming the class of bug. |
| 36 | `7d89a6a` | **Partial by necessity.** `multiagent` stays in the version body, now with a comment saying it is *unverified* against the update endpoint's immutable-field 400s and naming the check (a `--dry-run update` plus one real `update` after a roster edit) and where to record the result. No live account is reachable from this task, so the empirical half is left to the first real `update`. |
| 37 | `7d89a6a` | HTTP error bodies pass through a new `redact_text()` (masks `ghp_/gho_/ghu_/ghs_/github_pat_/sk-ant-` shapes) before reaching stderr. |
| 38 | `342f3dc` | `write_cloud()` runs as soon as the agents exist, before the deployment POST. |
| 39 | `7d89a6a` | `page()` follows `next_page_url` **and** `has_more`/`after_id`, with a loop guard — `live_state()` can no longer silently truncate. |
| 40 | `214d0bf` | `90-blocked` step 2 gets an explicit scrub list (token shapes, `Bearer`, presigned-URL signatures, `user:pw@host`) before anything is pasted into Asana; `20-build`'s 40-log-lines handoff cites it. |
| 41 | `c208ea2` | Every `/usr/bin/curl` outside `templates/` is now plain `curl`; the playbook gotcha row and the API playbook header say why the absolute path is a macOS-zsh artefact that must not be pinned in a Linux sandbox. |
| 42 | `214d0bf` | An empty iframe grep on `softmax.com/<slug>` is "unknown", not false: `60-verify` falls back to the coworld detail API, records which source it used, and `observatory-api.md` gets a §Featured match / replay route noting the server-rendering question is open. |
| 43 | `cce7203` | `00-claim` refuses to claim an idea whose text is marked confidential/internal/do-not-publish and goes to phase 90 instead — the repo it would land in is public. |
| 44 | `f6f87be` | Phase 20's exit criterion now checks that all three workflows parse (`gh api repos/…/actions/workflows/<wf>`) and that `coworld-release.yml` / `coworld-submit.yml` carry the input names phases 40/50 pass, the `release-result` / `submit-result` artifacts, and the per-policy `player` field. |
| 45 | `cce7203` | `fleet/cloud.md` gains an **Observatory players** table with both `ply_` ids and what each is for; `50-league` cites it and says `cloud.md` wins if an inlined literal ever disagrees. |

## Nothing was skipped

All 14 blocking and all 31 minor findings were acted on. Finding 36 is the only one that could not
be *completed* here (it asks for an empirical result from a real `update` against the live API);
what it asks to be written down is written down, and the check is named in the code comment.

## Owed by the `templates/` review (not touched here, per the brief)

These follow from fixes above and need the templates fixer's hand:

1. `templates/STATE.template.json` should gain the three new STATE fields: `session_ended_at`
   (null), `announce.attempted_at` (null), and `policies.filler_version_ids` (`[]`).
2. `templates/run-task.md` and `templates/README.md` describe the heartbeat lock. The 90-minute
   threshold is unchanged, so they are still correct — but they should mention that a run whose
   `STATE.session_ended_at` is ≥ its `heartbeat_at` is resumable immediately.
3. `templates/tools/ci/policies.json.example` already matches the canonical set exactly
   (`bullwhip-steady` and `bullwhip-forecaster` as `PLAYER_PROMPT` champions, `bullwhip-basestock`
   and `bullwhip-mirror` as `PLAYER_SCRIPTED` fillers, champion #2 carrying `"player"`), so it
   needed no edit; keep it that way.

## Verification run after the last commit

- `python3 -m py_compile fleet/bin/deploy.py` — OK.
- `python3 fleet/bin/deploy.py --dry-run create` — exit 0, prints the eight repo mounts and the
  collision-check notice.
- `agents/*.json`, `fleet/deployment.json`, `templates/tools/ci/policies.json.example` — all parse.
- `grep` for `<slug>-steady-llm`, `hedger`, `BASELINE` as an env var — no hits.
- `grep` for `-L 1` — hits only the four places that forbid it.
- `grep -i` for `DOM` in `prompts/60-verify.md`, `agents/verifier.md`, `docs/SPEC.md` — hits only
  the "no DOM readouts" prohibitions.
