# r2 fixes — coworld-builder

Round-2 fixer pass over `reviews/r1-verdict.md` §New findings (3 BLOCKING + 8 MINOR).
Base: `14124ff`. Head after this pass: `d910277` (+ this ledger). **11 findings, 11 commits,
one commit per finding, nothing pushed.**

The judge's suggested fix was applied as written in every case; where SPEC had to move with it,
SPEC moved (noted per row). No fix contradicts SPEC — the two SPEC sections that had codified a
broken path (§Runtime step 4's "confidential → phase 90", §State's silence on the release
artifact) were corrected, which is what "change SPEC first, then the prompts" requires.

| # | sev | sha | what changed |
|---|---|---|---|
| 1 | BLOCKING | `39df72c` | **Release result survives the session.** `prompts/40-release.md` step 3 now copies the `release-result` artifact to `runs/<run>/release-result.json` and its §Writes require that file committed plus `STATE.coworld.release_run_id`. `prompts/60-verify.md` check 7 reads the committed copy — no `/tmp` — with `gh run download "$release_run_id" -D "runs/<run>"` as the documented fallback before any `NOT FETCHED`. `agents/verifier.md` carries item 7 as the **one** named exception to "never reuse a fetch from an earlier phase" (it is this run's release artifact, not a live endpoint) and names the same fallback. `docs/SPEC.md` §State documents `coworld.release_run_id` and the committed copy; §Definition of done item 7 and §Repo layout point at it; `templates/STATE.template.json` gains `release_run_id`. |
| 2 | BLOCKING | `a698f4e` | **Unstartable ideas are SKIPPED, not routed into an unrunnable phase 90.** `prompts/00-claim.md` step 4.3 has two gates — confidentiality, and startability (no starter mapping *and* the gap is a human decision per §Rails) — and a five-step SKIP procedure (a)…(e): one `skipped by coworld-builder: <reason>` comment on the idea task; the gid appended to the committed `runs/SKIPPED.json` (created as `[]`); **one Fleet-section card** (`1217747860605582`) assigned to David Bloomin (`1209016834701578`) titled `SKIPPED <idea title>: <reason>`, deduped by title; a `runs/heartbeats.log` line; then **continue to the next idea**. Step 4.2 skips gids in `runs/SKIPPED.json` *and* ideas already carrying that comment, so the queue never re-selects one; step 4.5's re-GET drops an idea a concurrent heartbeat just skipped. Exit criterion gains (c2); §Writes lists the new artifacts. `prompts/90-blocked.md` gains a **Precondition**: 90 needs a run task and a STATE, so it is never entered from a bare idea. `docs/SPEC.md` §Runtime step 4 replaces "it goes to phase 90 instead" with the SKIPPED path; §Blocked states the run precondition. |
| 3 | BLOCKING | `7c92d23` | **Resume race guard.** `prompts/00-claim.md` step 5 is now 5.0/5.1/5.2: 5.0 mints a session nonce (`secrets.token_hex(4)`), writes `STATE.session_id` with `heartbeat_at` and `session_ended_at: null` in one push, logs `00 resume at phase <n> attempt=<k> session=<nonce>`, and on a **rejected push** rebases and **exits** if `log.md`'s last `00 resume` line carries another nonce; then re-GETs Asana custom field `1217748424048134` after 20 s and exits if it moved past its stamp. The Blocked-resume path (step 3.3) is explicitly routed through the same guard. A new **rejected-push rule** at the end of step 4 covers claims *and* resumes (never force). Exit criterion (b) covers "lost a resume race". `AGENT.md` gains heartbeat step 2a, the `session_id` and rejected-push bullets; `docs/SPEC.md` §Runtime gains step 2a and §State documents `session_id`; `templates/STATE.template.json` gains it. |
| 4 | MINOR | `9ba8d7c` | **One definition of "blocking".** The contradicting sentence in `agents/judge.md` ("an unverifiable item is not automatically blocking") is deleted; it now defers to the brief's rule — an item unverifiable from the tree or from cited CI evidence **counts as blocking**, listed with what would settle it, no third status. `prompts/30-review-loop.md` states the rule once in the judge brief and makes checklist item 1 verifiable in the sandbox: CI conclusion from `gh run list`, "no test loosened" from `git log -p --since=<run start> -- tests/` in the coworld repo, with the hunks that count as a finding. |
| 5 | MINOR | `4b2e26c` | `templates/STATE.template.json` gains `session_ended_at`, `policies.filler_version_ids`, `announce.attempted_at` (written by `00-claim` 4.9, `50-league`, `70-announce`; defined in SPEC §State). `templates/README.md` states the template must carry **every** SPEC §State field and names the recent additions. |
| 6 | MINOR | `fb9d843` | `templates/run-task.md`: `$BUILDER_PROJECT` → the board gid from `fleet/cloud.md` with the explicit "nothing exports it"; title is `<slug> — coworld run <run>` (the name `00-claim` step 4.8 creates) and the claimed-test is the STATE/SKIPPED lookup, not the title; the description's `heartbeat_at:` line and its rules are **deleted** and replaced by §Where the heartbeat lives — custom field `1217748424048134` with the PUT shape, the `log.md` fallback, and the fresh/stale + `session_ended_at` semantics. `templates/README.md` §run-task.md rewritten to match. |
| 7 | MINOR | `b381c4d` | `templates/blocked-subtask.md` replaces the four-field `STATE.blocked` list with the **six** fields `90-blocked.md` writes (`phase, at, ask, error, attempts, subtask`), shows the JSON, and flags `subtask` as load-bearing for `00-claim` step 3.1. `templates/README.md` mirrors it. |
| 8 | MINOR | `b3ecfda` | A yielding heartbeat writes `00 yield idea=<gid> to=<other run>` to the shared `runs/heartbeats.log` and its closing note — **never** `runs/<other-run>/log.md` (`AGENT.md` hard rule 7). Hard rule 7 now names the two shared, appendable files at the root of `runs/` (`heartbeats.log`, `SKIPPED.json`) so the rule and the instruction do not collide. |
| 9 | MINOR | `dcd7417` | `prompts/00-claim.md` gains **step 0: tool preflight** — `command -v jq`, and if missing, use the `python3 -c 'import json…'` equivalents and log `00 jq missing — using python3 json` rather than blocking. `fleet/cloud.md` gains a §Sandbox tooling table (git/gh/curl/python3 guaranteed, jq preflighted, docker/nim/emsdk absent by design). |
| 10 | MINOR | `5934579` | Phase 80 is **exempt from the resume counter**, matching `80-close.md` §Retry budget ("a failed close does not go to 90"): no increment, no 90, a distinct log line. `prompts/80-close.md` states the exemption from its side. |
| 11 | MINOR | `d910277` | The resume counter counts **only markerless sessions**. `AGENT.md` §Ending a heartbeat requires a `<UTC> progress phase=<nn> marker=<value>` line when the session advanced its phase; `00-claim` step 5.1 resets `phase_attempts[<nn>]` to 0 when such a line is newer than the last `00 resume`, with a per-phase marker table (10…70), then increments. So phase 20's builds and phase 30's four rounds are no longer Blocked as "ended three sessions without progress". `docs/SPEC.md` §Phases records both this and finding 10. |

## Not changed, and why

- The `/tmp` paths in `prompts/60-verify.md` checks 4, 6 and 8 (`/tmp/ep.replay`, `/tmp/idx.html`,
  `/tmp/static_replay.js`) stay: those are fetched **fresh in phase 60's own session** and are
  meant to be transient. Only the check-7 artifact crossed a session boundary, and only it moved.
- `prompts/40-release.md` still downloads the artifact into `/tmp/rr` before copying it into
  `runs/<run>/` — that is one session's own working dir, and the copy is what phase 60 reads.

## Verification (run at head, after the last commit)

```
python3 -m py_compile fleet/bin/deploy.py                       → OK
env -u ANTHROPIC_API_KEY python3 fleet/bin/deploy.py --dry-run create → exit 0
json.load: agents/*.json (7), fleet/deployment.json,
           templates/STATE.template.json, runs/SKIPPED.json,
           templates/tools/ci/policies.json.example             → 11/11 ok
yaml.safe_load: templates/{ci,coworld-release,coworld-submit}.yml → 3/3 ok
bash -n on every `run:` block in the three workflows            → 26 blocks, 0 failures
bash -n templates/tools/ci/docker_smoke.sh                      → ok
grep 'release-result' prompts/60-verify.md                      → no /tmp path (lines 89-101)
grep '$BUILDER_PROJECT' templates/run-task.md                   → absent
grep -r '$BUILDER_PROJECT' (repo)                               → only reviews/*.md (the review record)
```

Diff against `14124ff`: 16 files, +386 / −86.
