# r1 review — coworld-builder

Neutral trace of the repository at `/Users/daveey/code/coworld-builder` (uncommitted working tree;
`git log` reports no commits on `main`). Read in full: `docs/SPEC.md`, `AGENT.md`, `prompts/*.md`,
`agents/*.md`, `agents/*.json`, `fleet/cloud.md`, `fleet/deployment.json`, `fleet/bin/deploy.py`,
`playbooks/*.md`, `learnings/LEARNINGS.md`, `README.md`. `templates/` skipped per brief (its
`STATE.template.json` is quoted once, as context for a STATE-schema disagreement, not reviewed).
Cross-referenced: `daveey/cogamer` `origin/main:fleet/bin/fleetctl.py` and
`origin/main:fleet/PROTOCOLS.md`, and the worked example `/Users/daveey/code/cogame-bullwhip`.

Nothing was edited.

---

## 1. Consistency between SPEC and each prompt / agent

### 1.1 What agrees

These are the load-bearing invariants, and they are stated identically everywhere they appear:

- **Policy-before-upload order.** `docs/SPEC.md:95-96` (upload policies before `upload-coworld`,
  secret put after) = `prompts/40-release.md:47-53` (triage table) = `agents/builder.md:45-50` =
  `playbooks/make-coworld.md:68-71` = acceptance item 12 at `prompts/30-review-loop.md:100-102`.
  No file disagrees.
- **Filler/trigger order.** `docs/SPEC.md:96` = `prompts/50-league.md:69,79-80` =
  `playbooks/observatory-api.md:90,101-102` = `playbooks/make-coworld.md:206-210` =
  `learnings/LEARNINGS.md:60-61`. All say fillers before the first `trigger-round`, all give the
  same Temporal failure string.
- **Who owns Asana writes.** SPEC and `AGENT.md` put every Asana write on the coordinator; every
  sub-agent prompt forbids it explicitly (`agents/designer.md:58`, `agents/builder.md:68`,
  `agents/reviewer.md:77`, `agents/fixer.md:70`, `agents/judge.md:95`, `agents/verifier.md:79`).
  Each phase prompt's "Writes" section is addressed to the coordinator, so the phases owned by
  sub-agents (20/30/60) are not a contradiction.
- **Verdict marker format.** `prompts/30-review-loop.md:60-63` and `agents/judge.md:39-48,93-94`
  agree exactly: `blocking: <n>` as the first line, `BLOCKING: <n>` as the last, both deliberate,
  a mismatch is malformed. The exit criterion at `prompts/30-review-loop.md:109-110` restates it.
  `docs/SPEC.md:107` only says `verdict.blocking == 0` and never mentions the double marker — SPEC
  is silent, not contradictory.
- **STATE field names.** Every `STATE.<field>` reference across `AGENT.md` and `prompts/*.md`
  resolves against the schema at `docs/SPEC.md:120-133`: `run`, `idea_task`, `run_task`, `slug`,
  `repo`, `starter`, `phase`, `phase_attempts`, `review_round`, `coworld.{version,cow_id,
  manifest_sha}`, `policies.{champion1,champion2,fillers}`, `league.{id,division}`,
  `verify.{rounds,replay,iframe_static}`, `announce.discord_message_id`, `blocked`,
  `heartbeat_at`, `log`. No prompt invents a field name. (One type disagreement — see 1.2.)
- **Phase exit criteria.** Prompt exit criteria are supersets of, not substitutes for, the SPEC
  table: `prompts/50-league.md:90-94` adds fillers-registered and rounds-unpaused to SPEC's "both
  champions entrants; round triggered"; `prompts/40-release.md:57-61` adds `secret_put` and
  per-policy distinct version ids; `prompts/60-verify.md:101-105` adds the judge's `BLOCKING: 0`
  to SPEC's "checklist all-true", which SPEC's own phase table already implies by naming the
  owner "verifier → judge" (`docs/SPEC.md:54`). No prompt is weaker than SPEC.
- **Rails and Blocked triggers** are word-for-word consistent across `docs/SPEC.md:165-171`,
  `AGENT.md:80-88`, `prompts/90-blocked.md:14-22`, `prompts/10-design.md:22-23`,
  `playbooks/make-coworld.md:86-88`.
- **Section ids.** `fleet/cloud.md:46-52` and `playbooks/observatory-api.md:213-219` carry the same
  literal gids; `prompts/00-claim.md:8,10`, `prompts/80-close.md:10-12`, `prompts/90-blocked.md:11`
  and `prompts/70-announce.md:11` hard-code values that match cloud.md exactly. The Asana user gid
  `1209016834701578` and both `ply_` ids match across `prompts/50-league.md:49,56`,
  `playbooks/make-coworld.md:194,196` and `playbooks/observatory-api.md:213-215`.

### 1.2 Where they disagree

**A. The champion-policy naming is inconsistent across three files, and phase 50 submits a policy
phase 40 never mints.**

| file:line | says |
|---|---|
| `prompts/40-release.md:19-24` | mints five names: `-steady` (`PLAYER_SCRIPTED=1`), `-basestock`, `-mirror` (both scripted), `-forecaster` (`PLAYER_PROMPT`), `-hedger` (`PLAYER_PROMPT`, `"player": ply_bac48…` = daveey-1) |
| `prompts/50-league.md:53` | champion #1 = `<slug>-forecaster:v1` (daveey) — consistent with the above |
| `prompts/50-league.md:65` | champion #2 = **`<slug>-steady-llm:v1`** (daveey-1) — a name that appears nowhere else in the repo |
| `docs/SPEC.md:126-127` | `champion1: bullwhip-steady:v1`, `champion2: bullwhip-forecaster:v1`, `fillers: [basestock, mirror]` |

Three consequences. (i) The daveey-1-owned version phase 40 mints is `-hedger`; phase 50 submits
`-steady-llm`, which does not exist → `coworld submit` fails, 3 retries, phase 90. (ii) SPEC's
example makes `champion1` = `-steady`, which `prompts/40-release.md:19` defines as the **scripted**
policy — a coordinator taking SPEC's STATE block as the pattern seats a scripted bot as a champion,
which then fails definition-of-done item 4 (`docs/SPEC.md:71-74`, "non-scripted decisions ... not
all fallbacks") and `playbooks/make-coworld.md:17-19` ("a league where only trivial fillers play is
a FAILURE state"). (iii) SPEC's champion2 (`-forecaster`) is 50-league's champion **#1**, so the
daveey/daveey-1 ownership is inverted relative to the `"player"` field phase 40 sets.

**B. Filler count and `policies.fillers[]` type.** `docs/SPEC.md:127` shows two fillers, as names.
`prompts/40-release.md:16` says "two champions + three fillers". `prompts/50-league.md:73` registers
exactly two UUIDs. `prompts/40-release.md:66-67` says STATE gets fillers as "names `:vN`) plus the
`policy_version_id` UUIDs"; `prompts/50-league.md:98` says STATE gets "`policies.fillers[]` UUIDs".
The schema has one flat list with no room for both, so phase 50 overwrites phase 40's names.

**C. Design-note section names.** `prompts/10-design.md:35-38` mandates eight H2 headings "**in this
order and with these names**": `## The game`, `## Decisions: LLM with scripted fallback`,
`## Sim module`, `## Server, player, protocol`, `## Viewer`, `## Packaging`, `## Tests`,
`## Out of scope (v1)`. `docs/SPEC.md:49` names a different set (starter, rules, scoring, events,
state JSON, viewer, packaging, tests) and `agents/designer.md:26-29` repeats SPEC's set as "each as
its own section". `agents/designer.md:11-15` says the phase prompt outranks it, so the conflict is
declared — but the designer's own spec of its deliverable is wrong, and the coordinator's
acceptance checklist (`prompts/10-design.md:51-79`) grades against neither list's headings.

**D. Phase 40 ownership.** `docs/SPEC.md:52` ("builder (CI)"), `AGENT.md:42` and `AGENT.md:65`
("builder | phase 20 and phase 40"), and `agents/builder.md:45-50` all put phase 40 on the builder.
`prompts/40-release.md:4` says "Owner: coordinator dispatching `coworld-release.yml`".

**E. Trigger/filler prose vs the review checklist.** `prompts/30-review-loop.md:104-105` makes
sequential LLM calls a blocking `timeout` finding "for simultaneous-decision games", and
`prompts/10-design.md:64-66` requires the design to declare the parallel batch — but the design-note
checklist item is conditional ("Simultaneous-decision games:") while the builder brief at
`prompts/20-build.md:39-40` states it unconditionally ("issue all seats' LLM calls as ONE parallel
batch per turn"). For a turn-based sequential game the builder brief is wrong; for a simultaneous
game everything agrees.

**F. `heartbeat_at` storage.** `AGENT.md:24,102-104` and `docs/SPEC.md:30` say to write
`heartbeat_at` "on the run task". `prompts/00-claim.md:21-22` reads it as "custom field, else the
last `heartbeat` line in `runs/<run>/log.md`". `fleet/cloud.md` defines no custom-field gid,
`prompts/00-claim.md:32-34` (task creation) never creates one, and no file anywhere defines the
`heartbeat` log-line format — the log-line formats that *are* specified are
`prompts/00-claim.md:53` (`00 claim …`), `prompts/70-announce.md:39`, `prompts/90-blocked.md:56-57`.

**G. AGENT.md binds the coordinator to a claim/heartbeat protocol that contradicts its own.**
`AGENT.md:126-131` makes `/workspace/cogamer/fleet/PROTOCOLS.md` §CLAIM PROTOCOL and §HEARTBEAT
binding "before your first claim of a run". Those sections (PROTOCOLS.md:27-74, 401-420) specify a
worker-id + comment-first + re-read-before-claim algorithm over `Planned`/`Building` sections and an
`owner` field, 10-minute heartbeats, and a **60-minute** staleness definition. The Coworld Builder
board has no `Planned` section (`fleet/cloud.md:48-51`) and no owner field, `prompts/00-claim.md`
implements none of the claim algorithm, and SPEC/AGENT use **90** minutes and 15-minute heartbeats.

**H. Phase-prompt path form.** `AGENT.md:49` says read `prompts/<phase>.md`; the files are
`prompts/00-claim.md` … `prompts/90-blocked.md`. `prompts/00-claim.md:47` and
`prompts/90-blocked.md:68` use the correct glob form `prompts/<STATE.phase>-*.md`.

**I. SPEC's loop line missing from the phase prompt.** `docs/SPEC.md:105` has "if review has no
findings: judge runs anyway"; the loop block at `prompts/30-review-loop.md:14-24` omits it. Only
`agents/judge.md:81-82` carries the intent.

**J. Board sections.** `README.md:86-87` says the board has sections *Planned*, *Running*,
*Blocked*, *Done*; `fleet/cloud.md:48-51` and `prompts/00-claim.md:8` say Running / Blocked / Done /
**Fleet**.

**K. `fleet/mirror/`.** `docs/SPEC.md:20` ("config mirrored in git under `fleet/mirror/`, applied
out") and `docs/SPEC.md:161` promise a mirror; `fleet/bin/deploy.py` has no `export` or `diff`
subcommand (`deploy.py:404-409`) and no `fleet/mirror/` directory exists.

---

## 2. Executability — HTTPS + `gh` + `git` only

Assumed present in the sandbox but declared nowhere in the repo: `gh`, `git`, `jq`, `curl`,
`python3`. Every prompt leans on `jq` heavily (`prompts/50-league.md:30`, `60-verify.md:23-55`) and
on `gh` (`20-build.md:51-53`, `40-release.md:33-37`, `50-league.md:51-54`). Only `gh` and `curl` are
named in SPEC.

| phase | executable as written? | the steps that are not |
|---|---|---|
| 00 claim | yes, except F above | Asana section moves (steps 3/`80-close.md:31`/`90-blocked.md:41`) are named but no call shape is given; Asana needs `POST /sections/{gid}/addTask`, and the section gids in `fleet/cloud.md:48-51` are never used by any prompt. `$BUILDER_PROJECT` (`AGENT.md:16`) is not an env var set by `fleet/deployment.json` — it is a table row in `fleet/cloud.md:49`; a literal `$BUILDER_PROJECT` in a curl URL expands to empty. |
| 10 design | **no** | `prompts/10-design.md:11` ("read-only starter repos mounted in the sandbox") and `:32` ("mounted read-only at `<path>`") describe mounts that `fleet/deployment.json:18-33` does not declare — only `coworld-builder` and `cogamer` are mounted. `docs/SPEC.md:39-42` claims six starter repos are mounted. `agents/designer.md:18-19` says instead "read from its public repo", and `agents/builder.md:16` says `git clone` — so the sub-agents are right and SPEC + the phase prompt are wrong. The coordinator's brief template at `10-design.md:32` will interpolate a path that does not exist. |
| 20 build | mostly | `gh repo create` + `git push` to `Metta-AI/cogame-<slug>` — a repo that is **not** a mounted resource. The deployment's `authorization_token` (`fleet/deployment.json:24,31`) is per-resource; nothing in the repo says git is configured with a credential helper for arbitrary `Metta-AI` repos, or that `GH_TOKEN` (`fleet/cloud.md:18`, substituted at egress) reaches `git` as opposed to `gh`. No docker/nim/uv is invoked locally — that constraint is honoured. `prompts/20-build.md:58` ("tune the scripted baseline with a grid harness in CI") has no dispatch named and no template input; it is a CI job that must exist in `templates/ci.yml`. |
| 30 review | yes | Pure filesystem + `gh`. `agents/fixer.md:28` runs CI, which is HTTPS. |
| 40 release | mostly | `$POLICIES` is used at `prompts/40-release.md:33` but never assigned. `gh run list -L 1` at `:34` races the dispatch (see B8). `gh run download -n release-result` at `:36` assumes the template uploads that artifact on failure too (`playbooks/make-coworld.md:55`) — a `templates/` contract, out of scope here. |
| 50 league | mostly | All HTTPS except submission, which `playbooks/observatory-api.md:183-205` flags as **BINDING with no HTTPS route known** — it depends entirely on `templates/coworld-submit.yml` existing and honouring `player_id`/`policy`/`league_id` and emitting `submit-result.json`. The `"player"` field on a policy entry (`prompts/40-release.md:24`) is a second such binding on `templates/coworld-release.yml`. Both are out of scope but are hard dependencies of an in-scope prompt. |
| 60 verify | **check 8 is not executable** | `docs/SPEC.md:83-84`, `prompts/60-verify.md:86-93` and `agents/verifier.md:58-62` require reading the **rendered DOM** of a wasm replay viewer at three scrub points. The sandbox has no screen (stated) and no headless browser is mounted, installed, or named anywhere. `curl` of `index.html` returns the bundle shell, not derived state; the wasm never executes. The comment at `60-verify.md:90` ("fetch the bundle's index + its derived state") describes something curl cannot do. Since `60-verify.md:101-105` requires **all eight** checks true, phase 60 cannot exit clean. Check 6 (`60-verify.md:73`) greps raw HTML from `softmax.com/<slug>` for an `<iframe>` — fine if that page is server-rendered, a false negative if it is client-rendered; nothing in the repo records which. |
| 70 announce | yes | Plain Discord REST with `$DISCORD_BOT_TOKEN` from vault `vlt_011CeJJ4eJ7h2TKoPBwKhA4M` (`fleet/cloud.md:19`), which is in `vault_ids` at `fleet/cloud.md:13`. |
| 80 close | yes, minus the section-move gap | — |
| 90 blocked | yes, minus D8 below | — |

Small portability note: every curl in the prompts is spelled `/usr/bin/curl`. That absolute path is
a **macOS zsh** workaround, documented as such at `playbooks/make-coworld.md:270` ("zsh eats a var
or curl breaks ... use `/usr/bin/curl` if PATH is broken"). It is pinned into a Linux cloud sandbox
where curl may live elsewhere.

Ids referenced by prompts but absent from `fleet/cloud.md`: both `ply_` player ids
(`prompts/50-league.md:49,56`), the `heartbeat_at` custom-field gid, and the run-task section move
targets by name. `AGENT.md:27-29` says "All ids ... are in `fleet/cloud.md` ... never hard-code an
id from memory", but the prompts hard-code Asana project gids, Discord ids and both player ids
inline. That is safe today because every literal matches `fleet/cloud.md` /
`playbooks/observatory-api.md:211-219` — it is a maintenance hazard, not a current defect.

---

## 3. Dupe guard and resume — tracing heartbeat steps 1-5

The algorithm is stated twice, identically: `docs/SPEC.md:22-31` and `AGENT.md:16-25`, implemented
by `prompts/00-claim.md:16-41`.

**Case 1 — fresh run (no Running, no Blocked, ideas queued).** Step 1 lists Running → empty. Step 3
lists Blocked → empty. Step 4 lists ideas, skips those whose gid appears as `idea_task` in
`runs/*/STATE.json`, takes the top one, creates the run task in *Running*, writes STATE, pushes.
Works — with two gaps:
- *No race guard.* Between the listing at step 1 and the create at step 4 there is no re-read, no
  claim comment, and no post-claim verification. Two heartbeats that overlap (cron plus a manual
  `deploy.py run`, or a retried deployment run) both see an empty board and both create a run task
  and a public repo for the same idea. `AGENT.md:126-129` points at PROTOCOLS §CLAIM PROTOCOL,
  which exists precisely because "plain PUT+sleep-20 claims raced 4 confirmed times"
  (PROTOCOLS.md:31-32) — but `prompts/00-claim.md` implements none of it.
- *Dedupe reads a possibly-stale mount.* Step 4's skip list is `runs/*/STATE.json` on the local
  checkout. `AGENT.md:94-95` requires `git pull --rebase` before every **write**;
  `prompts/00-claim.md:28` does not pull before the **read** that decides the claim.

**Case 2 — live run (Running, `heartbeat_at` < 90 min).** Step 1 exits, writing nothing
(`prompts/00-claim.md:23-24`). Correct, and the only case with no gap in its own terms. But the
threshold interacts badly with the schedule: the cron is hourly (`fleet/deployment.json:15`,
`fleet/cloud.md:39`) and `AGENT.md:154-159` requires a fresh `heartbeat_at` write **at session
end**. So a run that needs more than one heartbeat looks alive for 90 minutes after its session
died; the firing at T+60 exits, and only T+120 resumes. A multi-heartbeat run therefore advances at
best every two hours. There is no "session ended cleanly, safe to resume" marker distinct from
"alive".

**Case 3 — stale run (Running, `heartbeat_at` > 90 min).** Step 2 adopts it and jumps to step 5,
which re-reads STATE, refreshes `heartbeat_at`, appends `resume at phase <n>`, and enters
`prompts/<STATE.phase>-*.md`. Gaps:
- *Staleness has no reliable input* — see finding 1.2.F. If the custom field does not exist and no
  `heartbeat` line format is defined, step 2 cannot distinguish case 2 from case 3. That is the
  entire dupe guard.
- *No crash counter.* The resume path (`prompts/00-claim.md:39-41`) does not touch
  `phase_attempts`. Retry budgets are only consumed by a phase noticing its own step failed
  (`prompts/20-build.md:73`, `40-release.md:72`, etc.). A phase that reliably kills the session —
  sandbox OOM, an unbounded `gh run watch`, a wedged poll — is re-entered every ~2 h forever, never
  reaching 90.
- *Ambiguity with more than one stale Running task.* `prompts/00-claim.md:25` says "A *Running*
  task with a **stale** `heartbeat_at` → it is yours" without saying which, or that only one may be
  adopted per heartbeat.

**Case 4 — Blocked with the human subtask resolved.** Step 3 moves the task to *Running* and
resumes. Gaps:
- *"Its human subtask" is not identified.* `prompts/00-claim.md:26-28` says "fetch its subtasks; if
  the human subtask is `completed: true`". But `prompts/00-claim.md:34` creates **eight phase
  subtasks** on every run task, and `prompts/80-close.md:29,41` completes them as the run
  progresses. A run blocked at phase 40 already has subtasks 10, 20, 30 complete. Nothing points at
  `STATE.blocked.subtask` (which `prompts/90-blocked.md:32` does record) or at the
  `BLOCKED <slug> @<phase>:` title prefix (`90-blocked.md:36`) or the assignee. A naive read
  resumes a run whose human ask is still open, re-enters the failed phase, and returns to 90.
- *`phase_attempts` reset is specified in the wrong file.* `prompts/90-blocked.md:68` says the
  resume happens "with `phase_attempts[<n>]` reset to 0". The resume path that actually executes
  (`prompts/00-claim.md:26-28,39-41`) never mentions it. Without the reset, the resumed phase's
  budget is already spent, it goes straight back to 90, and `prompts/90-blocked.md:34` creates a
  **second** subtask — violating that same file's exit criterion at `:50` ("exactly one open human
  subtask").
- *`STATE.blocked` is never cleared.* `prompts/90-blocked.md:44` keeps it; nothing on the resume
  path nulls it. A run that unblocks and finishes still reports `blocked` in STATE, which
  `README.md:98` tells a human to read as the run's status.

**Case 5 — Blocked, subtask unresolved.** Step 3 does not match, so control falls through to step 4
and the heartbeat **claims a new idea**. The blocked run then starves: every later heartbeat hits
step 1 first and exits while the new run's heartbeat is fresh, and only reaches step 3 once nothing
is Running. If the new run also blocks, there are two Blocked tasks and step 3's iteration order is
undefined. This may be the intended "concurrency = 1, keep making progress" behaviour, but neither
`docs/SPEC.md:22-31`, `AGENT.md:16-25`, nor `README.md` says so, and nothing bounds how much of the
idea board gets consumed while a Blocked run waits on a human.

**One more duplication path, outside the five cases.** `AGENT.md:145-147` (hard rule 4) forbids more
than one Discord post per run and keys the guard on `STATE.announce.discord_message_id`.
`prompts/70-announce.md:18-28` posts first and `:38` writes STATE after. A session that dies between
the 200 response and the STATE push resumes at phase 70 and posts a second message. The guard is
correct; its write ordering is not.

---

## 4. Secrets and destructive actions

**Strong points.** `AGENT.md:133-152` is an unambiguous hard-rule block: never print a secret
(rule 1), never force-push including `--force-with-lease` (rule 2), never delete a league / coworld
/ division / policy / repo (rule 3), one Discord post per run (rule 4), never create/reorder/delete
Coworld Ideas (rule 5). Every sub-agent prompt repeats the relevant subset
(`agents/builder.md:69-70`, `agents/fixer.md:61`, `agents/verifier.md:81`,
`agents/reviewer.md:71,77`, `agents/judge.md:88,95`). Every credential in every prompt is
referenced as `$VAR`, never inlined. `agents/verifier.md:67-68` explicitly says to name headers and
never their values. `deploy.py` never prints the API key (`deploy.py:58-68`) and `redact()`
(`deploy.py:114-128`) masks both key-named fields and `ghp_`/`gho_`/`github_pat_`/`sk-ant-` shaped
strings before any `--dry-run` output. `deploy.py:229` avoids fetching a `gh` token at all under
`--dry-run`. `SOFTMAX_TOKEN` and `ANTHROPIC_API_KEY` are org secrets consumed by CI only
(`docs/SPEC.md:35`, `agents/builder.md:41-43`, `prompts/40-release.md:10`) — the agent never holds
them.

**Places a secret could still surface.**

1. `fleet/bin/deploy.py:88-89` writes the raw HTTP error body (2000 chars) to stderr on any 4xx/5xx.
   For `create`, the request that failed carries `resources[*].authorization_token` (a live `gh`
   token, `deploy.py:229-232`); if the API echoes request context in an error, it lands unredacted
   in the operator's terminal and in any CI log capturing it. `redact()` is applied to `--dry-run`
   output but not to this path. `fleetctl.py:60-61` re-raises without printing a body at all.
2. `prompts/90-blocked.md:9,38` require the **exact error text** of three failed attempts to be
   pasted into an Asana subtask body, and `prompts/20-build.md:75` sends "the last 40 log lines" of
   a failed CI job to phase 90. CI logs routinely contain URLs with embedded tokens. No prompt says
   to scrub before pasting; only the general `AGENT.md:137` rule covers it.
3. `prompts/60-verify.md:51,89` handle `replay_url` and build an iframe URL containing it. If S3
   ever hands back a presigned URL, `agents/verifier.md:17-22` ("paste the actual response bytes")
   would put its signature into a committed `VERIFY.md`. `agents/verifier.md:81` anticipates this
   ("do not paste a token-bearing URL"); `playbooks/observatory-api.md:167` says the URLs are public
   S3 paths, so the risk is latent rather than present.

**Destructive actions.** I found none. No prompt issues a DELETE against Asana, GitHub, Discord or
the Observatory. `softmax player unset` (`playbooks/observatory-api.md:193`) is scoped to an
`always()` step inside the submit workflow and is a session-state reset, not a deletion. The one
sanctioned mutation of the human's queue — completing the idea task — is confined to phase 80
(`prompts/80-close.md:5,31`) and explicitly permitted by `AGENT.md:148-149`. `git push --force` is
forbidden three times over.

**Non-secret disclosure worth naming.** `prompts/20-build.md:15-18` creates a **public** repo, and
`prompts/00-claim.md:33` copies the idea text verbatim into the run task while
`prompts/10-design.md:27,38` copies it verbatim into a design note that lands in that public repo.
Any confidential text a human puts in a Coworld Idea is published. Nothing warns about this.

---

## 5. `fleet/bin/deploy.py` vs the `daveey/cogamer` conventions

Reference: `git show origin/main:fleet/bin/fleetctl.py` in `/Users/daveey/code/daveey-cogamer`.

**Faithfully carried over.** `key()` (`deploy.py:58-68` = `fleetctl.py:38-47`), the `api()` helper
with the same headers, `anthropic-version: 2023-06-01`, `anthropic-beta:
managed-agents-2026-04-01`, 120 s timeout and 3-try backoff (`deploy.py:77-95` =
`fleetctl.py:50-66`); `AGENT_FIELDS` and `DEPL_FIELDS` identical (`deploy.py:47,49` =
`fleetctl.py:78-79`); `norm_depl()` byte-identical including the `<resupply-at-apply>` substitution
(`deploy.py:203-216` = `fleetctl.py:82-95`); `live_state()` name-prefix filtering
(`deploy.py:197-200` = `fleetctl.py:98-101`); the "POST only the differing fields — the update
endpoint 400s on full-config bodies, and an agent repoint needs `agent.type`" rule, carried across
**with its comment** (`deploy.py:335-340` = `fleetctl.py:211-217`); tokens from `gh auth token` at
apply time only and never in git (`deploy.py:71-74`, `fleet/deployment.json:24,31`).

**Divergences.**

| # | deploy.py | fleetctl.py | effect |
|---|---|---|---|
| 1 | `cmd_create` (`:239-277`) POSTs `/agents` unconditionally | `cmd_apply` (`:173-178`) creates only `if live is None` | a second `create` duplicates all seven agents **and** creates a second `coworld-builder-hourly` deployment — two hourly crons firing the same coordinator |
| 2 | `page()` (`:98-108`) follows `next_page_url` only | `page()` (`:68-75`) also falls back to `has_more` + `after_id` | `/agents` is account-wide and filtered client-side (`:198`); if the account's agent list pages by `has_more`, `live_state()` silently truncates |
| 3 | `cmd_update` writes `("TBD","TBD")` into `rows` when a live agent is missing (`:288-290`) and then `write_cloud(rows)` unconditionally (`:348-349`) | `cmd_apply` never writes ids back | a lookup miss (divergence 2, a rename, an API blip) **overwrites the real ids in `fleet/cloud.md` with `TBD`** — and if the deployment is missing (`:320`) its row is dropped from the table entirely, which is exactly what `_deployment_id()` (`:353-357`) and `cmd_run`/`cmd_status` depend on |
| 4 | `cmd_update` `continue`s past a missing sub-agent (`:291`) **before** the roster append at `:301`/`:309`/`:315` | n/a (fleetctl has no coordinator roster) | the coordinator is then versioned with a short `multiagent.agents` list, silently dropping a sub-agent from the roster |
| 5 | `VERSIONED_FIELDS` includes `multiagent` (`:48`) | version body sends only `description, model, tools, skills` (`:184-185`) | untested against the update endpoint, which fleetctl's own comment says 400s on immutable fields |
| 6 | `VERSIONED_FIELDS` omits `mcp_servers` though `AGENT_FIELDS` includes it (`:47-48`) | same shape, but fleetctl fixed exactly this class of bug for `skills` and left a comment (`:179-181`) | an `mcp_servers` edit in `agents/*.json` is a silent no-op on `update` |
| 7 | `cmd_create` calls `write_cloud()` only after the deployment POST (`:273-277`) | n/a | a failure at the deployment step leaves seven orphan agents whose ids were never recorded; the fix-forward is another `create`, which duplicates them (divergence 1) |
| 8 | no `export` / `diff` (`:404-409`) | `export` + `diff` with exit-1-on-drift, a steward duty (`:104-157`) | no drift detection, and `docs/SPEC.md:20,161` + `fleet/cloud.md:61` promise `fleet/mirror/` |
| 9 | `api()` prints the error body (`:88-89`) | re-raises silently (`:60-61`) | see §4.1 |

**Correct-as-written details worth recording**, since they look wrong at a glance: `cmd_update`'s
`changed` list is computed from `cmp_want`, which has `initial_events` popped (`:326`), so a
deployment update never re-fires the kickoff message — matching fleetctl's deliberate "kickoff
messages are deliberate" stance (`fleetctl.py:202-203`). The precedence in
`cmd_status`'s `(runs.get("data") or runs) if isinstance(runs, dict) else runs` (`:388`) parses as
intended. `read_cloud()`'s regexes (`:142-143`) both match `fleet/cloud.md:11,13` and correctly
yield two vault ids. The roster is fully built before the coordinator because
`ROLES + ["coordinator"]` puts it last (`:285`).

---

## 6. Findings

### BLOCKING

1. **BLOCKING** — `prompts/50-league.md:65` submits champion #2 as `<slug>-steady-llm:v1`, a policy
   name minted nowhere; `prompts/40-release.md:23-24` mints `<slug>-hedger` as the daveey-1-owned
   version. Phase 50 fails on every run. *Fix: change `50-league.md:65` to
   `-f policy='<slug>-hedger:v1'`.*
2. **BLOCKING** — `docs/SPEC.md:126` sets `champion1: bullwhip-steady:v1`, which
   `prompts/40-release.md:19` defines as the `PLAYER_SCRIPTED=1` policy, so SPEC's own example
   seats a scripted bot as a champion and fails definition-of-done item 4 (`docs/SPEC.md:71-74`).
   *Fix: rewrite the SPEC STATE example as `champion1: bullwhip-forecaster:v1`,
   `champion2: bullwhip-hedger:v1`.*
3. **BLOCKING** — `docs/SPEC.md:39-42` and `prompts/10-design.md:11,32` and `prompts/20-build.md:9`
   assume the six starter repos are mounted read-only; `fleet/deployment.json:18-33` mounts only
   `coworld-builder` and `cogamer`, so the designer brief interpolates a nonexistent path. *Fix:
   either add the starters as `github_repository` resources in `fleet/deployment.json`, or change
   those three references to `git clone` as `agents/builder.md:16` already does.*
4. **BLOCKING** — `prompts/00-claim.md:21-22` reads `heartbeat_at` from an Asana custom field that
   `fleet/cloud.md` never identifies and `prompts/00-claim.md:32-34` never creates, falling back to
   a `heartbeat` log line whose format no file defines. The dupe guard has no reliable input.
   *Fix: create the custom field, record its gid in `fleet/cloud.md`, and pin one log-line format
   (`<UTC> heartbeat phase=<n>`) in `AGENT.md:102`.*
5. **BLOCKING** — `prompts/00-claim.md:16-38` claims with no staleness re-read, no claim comment and
   no post-claim verification, while `AGENT.md:126-129` binds the coordinator to
   `PROTOCOLS.md` §CLAIM PROTOCOL, which exists because that pattern raced four times. Two
   overlapping heartbeats duplicate a run and a public repo. *Fix: add to `00-claim.md` step 4 a
   `git pull --rebase`, a re-GET of the idea immediately before claiming, a `claimed by
   coworld-builder run <run>` comment posted **before** the run task is created, and a 20 s re-read
   that yields if an earlier claim comment exists.*
6. **BLOCKING** — `prompts/00-claim.md:26-28` resumes a Blocked run when "the human subtask" is
   complete, but `prompts/00-claim.md:34` puts eight phase subtasks on every run task and
   `prompts/80-close.md:29` completes them; the human subtask is never identified. A run resumes
   with its ask still open and loops back to 90. *Fix: match on `STATE.blocked.subtask` (recorded at
   `90-blocked.md:32`), falling back to the `BLOCKED ` title prefix.*
7. **BLOCKING** — the `phase_attempts` reset on unblock is specified only at
   `prompts/90-blocked.md:68`; the resume path at `prompts/00-claim.md:26-28,39-41` never does it,
   so the resumed phase re-exhausts immediately and files a second Blocked subtask, violating
   `prompts/90-blocked.md:50`. *Fix: add "set `phase_attempts[<STATE.phase>] = 0` and
   `blocked = null`" to `00-claim.md` step 3.*
8. **BLOCKING** — `prompts/40-release.md:34-35` (also `prompts/20-build.md:51` and
   `playbooks/make-coworld.md:49`) take `gh run list -L 1` immediately after `gh workflow run`,
   which races registration and can watch the **previous** run and download its stale
   `release-result.json` as this dispatch's evidence. *Fix: poll
   `gh run list --json databaseId,createdAt,event` until a `workflow_dispatch` run newer than the
   dispatch timestamp appears, then watch that id.*
9. **BLOCKING** — `prompts/00-claim.md:39-41` never increments `phase_attempts` on resume, so a
   phase that reliably kills the session is re-entered every ~2 h forever and never reaches 90.
   *Fix: on the resume path, increment `phase_attempts[<phase>]`; at 3, enter
   `prompts/90-blocked.md`.*
10. **BLOCKING** — `prompts/70-announce.md:18-28` posts to Discord before writing
    `announce.discord_message_id` at `:38`; a session death in between produces a second post on
    resume, violating `AGENT.md:145-147`. *Fix: write and push a `announce.attempted_at` marker to
    STATE before the POST, and treat a set marker with no id as "verify by searching the channel,
    never re-post blind".*
11. **BLOCKING** — `docs/SPEC.md:83-84` / `prompts/60-verify.md:86-93` / `agents/verifier.md:58-62`
    require DOM readouts from a rendered wasm viewer at three scrub points; the sandbox has no
    screen and no headless browser is provided, so definition-of-done item 8 can never be true and
    `prompts/60-verify.md:101-105` requires all eight. Every run ends at phase 90.
    *Fix: either add a headless-browser binding (and name it in `fleet/cloud.md`), or restate item 8
    as a judgment written from the replay JSON plus the bundle's static asset manifest.*
12. **BLOCKING** — `fleet/bin/deploy.py:239-277` (`cmd_create`) has no live-state check, so a second
    `create` duplicates all seven agents and creates a second `coworld-builder-hourly` deployment —
    two hourly crons, duplicate heartbeats, duplicate runs. `fleetctl.py:174-178` creates only when
    `live is None`. *Fix: call `live_state()` first and refuse (or skip) any name that already
    exists.*
13. **BLOCKING** — `fleet/bin/deploy.py:288-290,320,348-349`: when a live agent or the deployment is
    not found, `cmd_update` writes `TBD` (or omits the row) and then rewrites `fleet/cloud.md`
    unconditionally, destroying the ids `_deployment_id()` (`:353-357`), `run` and `status` depend
    on. The `page()` gap at `:98-108` (vs `fleetctl.py:68-75`) makes a spurious miss plausible.
    *Fix: never write `TBD` over an existing id — preserve the prior row on a miss, and exit
    non-zero.*
14. **BLOCKING** — `fleet/bin/deploy.py:288-291`: a missing sub-agent is `continue`d past **before**
    the roster append at `:301`, so the coordinator is versioned with a truncated
    `multiagent.agents` list and silently loses a sub-agent. *Fix: abort the whole `update` if any
    role in `ROLES` is missing live.*

### MINOR

15. **MINOR** — `prompts/40-release.md:16` says "three fillers" while `docs/SPEC.md:127` shows two
    and `prompts/50-league.md:73` registers two UUIDs. *Fix: pick one count and state it in all
    three.*
16. **MINOR** — `prompts/40-release.md:66-67` writes `policies.fillers[]` as names + UUIDs;
    `prompts/50-league.md:98` writes it as UUIDs; `docs/SPEC.md:127` shows names. *Fix: add a
    `policies.filler_version_ids[]` field to the SPEC schema and keep `fillers[]` as names.*
17. **MINOR** — `prompts/10-design.md:35-38` mandates eight exact H2 names that neither
    `docs/SPEC.md:49` nor `agents/designer.md:26-29` matches. *Fix: replace the section list in
    SPEC and `designer.md` with the eight names from the phase prompt.*
18. **MINOR** — `prompts/40-release.md:4` puts phase 40 on the coordinator; `docs/SPEC.md:52`,
    `AGENT.md:42,65` and `agents/builder.md:45` put it on the builder. *Fix: make `40-release.md:4`
    say "builder, dispatched by the coordinator".*
19. **MINOR** — `prompts/20-build.md:39-40` requires one parallel LLM batch per turn
    unconditionally; `prompts/10-design.md:64` and `prompts/30-review-loop.md:104` scope it to
    simultaneous-decision games. *Fix: add "for simultaneous-decision games" to the builder brief.*
20. **MINOR** — `AGENT.md:126-131` makes PROTOCOLS §CLAIM PROTOCOL and §HEARTBEAT binding, but they
    assume a `Planned` section and an `owner` field this board lacks (`fleet/cloud.md:48-51`) and
    specify 60-min staleness / 10-min heartbeats against this system's 90 / 15
    (`docs/SPEC.md:22,30`). *Fix: cite only §ESCALATION HANDOFF, §CRUX DECISIONS and §STRUCTURED
    RECORDS, and say the claim/heartbeat numbers here supersede.*
21. **MINOR** — the 90-minute staleness threshold exceeds the 60-minute cron
    (`fleet/deployment.json:15`), and `AGENT.md:154-159` refreshes `heartbeat_at` at session end, so
    a multi-heartbeat run advances only every other firing. *Fix: drop the threshold below the cron
    interval (e.g. 45 min), or have the closing write stamp a `session_ended_at` the next heartbeat
    treats as immediately resumable.*
22. **MINOR** — `prompts/00-claim.md:25` does not say which stale *Running* task to adopt, or that
    only one may be adopted. *Fix: "the stale task with the oldest `heartbeat_at`; adopt exactly
    one".*
23. **MINOR** — `prompts/00-claim.md:26-31` falls through from an unresolved Blocked run to claiming
    a **new** idea; neither `docs/SPEC.md:22-31` nor `README.md` documents this. *Fix: state the
    policy explicitly and cap the number of simultaneously-Blocked runs.*
24. **MINOR** — `STATE.blocked` is never cleared on resume (`prompts/90-blocked.md:44`,
    `prompts/00-claim.md:39-41`), so a finished run still reports blocked to the human reading path
    at `README.md:98`. *Fix: null it in `00-claim.md` step 3.*
25. **MINOR** — `prompts/90-blocked.md:42` posts the blocked comment to `1217704774784096`, which is
    the Coworld **Ideas project** gid (`fleet/cloud.md:46`), not the idea task. *Fix: use
    `STATE.idea_task`.*
26. **MINOR** — `prompts/40-release.md:20-21` introduces a `BASELINE` env var that
    `prompts/20-build.md:24-26` never asks the builder to implement (it names only `PLAYER_PROMPT`
    vs `PLAYER_SCRIPTED=1`); the worked example uses `PLAYER_SCRIPTED=<name>`
    (`cogame-bullwhip/docs/plans/2026-08-22-bullwhip-design.md:199-200`). Distinct versions are
    still minted, but the two "different" baselines run identical code. *Fix: add `BASELINE` to the
    builder brief, or switch the policy entries to `PLAYER_SCRIPTED=basestock|mirror`.*
27. **MINOR** — `AGENT.md:49` says read `prompts/<phase>.md`; the files are `<phase>-<name>.md` and
    the correct glob is used at `prompts/00-claim.md:47`. *Fix: use `prompts/<phase>-*.md`.*
28. **MINOR** — `AGENT.md:16` and `docs/SPEC.md:23` write `$BUILDER_PROJECT` as a shell variable; it
    is set by nothing (`fleet/deployment.json` declares no env) and exists only as a table row at
    `fleet/cloud.md:49`. *Fix: write it as "the Coworld Builder gid in `fleet/cloud.md`".*
29. **MINOR** — no prompt gives the Asana call shape for a section move
    (`prompts/00-claim.md:32`, `80-close.md:31`, `90-blocked.md:41`), and the section gids at
    `fleet/cloud.md:48-51` are never used. *Fix: add `POST /sections/{gid}/addTask {"task": gid}` to
    `playbooks/observatory-api.md` §Non-Observatory calls.*
30. **MINOR** — `README.md:86-87` lists a *Planned* section the board does not have
    (`fleet/cloud.md:48-51` has *Fleet*). *Fix: correct the README.*
31. **MINOR** — `docs/SPEC.md:105` ("if review has no findings: judge runs anyway") is missing from
    the loop at `prompts/30-review-loop.md:14-24`. *Fix: add the line to the loop block.*
32. **MINOR** — `prompts/30-review-loop.md:15` starts the loop at `STATE.review_round` with no floor
    (the STATE template initialises it to `0`, and only `prompts/20-build.md:68` sets it to 1), so a
    resume straight into phase 30 writes `r0-*.md` files. *Fix: `round = max(STATE.review_round, 1)`.*
33. **MINOR** — `$POLICIES` is referenced at `prompts/40-release.md:33` but never assigned. *Fix:
    show the `POLICIES=$(jq -nc …)` assignment.*
34. **MINOR** — `docs/SPEC.md:20,161` and `fleet/cloud.md:61` promise `fleet/mirror/` (a fleetctl
    export) and drift detection; `deploy.py` has neither (`:404-409`), and no `fleet/mirror/`
    exists. *Fix: add `export`/`diff` subcommands, or drop the mirror from SPEC.*
35. **MINOR** — `fleet/bin/deploy.py:47-48`: `mcp_servers` is in `AGENT_FIELDS` but not
    `VERSIONED_FIELDS`, so an edit to it is a silent no-op on `update` — the exact bug
    `fleetctl.py:179-181` documents fixing for `skills`. *Fix: add `mcp_servers` to
    `VERSIONED_FIELDS`.*
36. **MINOR** — `fleet/bin/deploy.py:48` sends `multiagent` in the version body where
    `fleetctl.py:184-185` deliberately sends only description/model/tools/skills; unverified against
    the endpoint's immutable-field 400s. *Fix: confirm with `--dry-run` + one real `update`, and
    note the result in a comment.*
37. **MINOR** — `fleet/bin/deploy.py:88-89` prints the raw HTTP error body unredacted; the failing
    `create` request carries a live `gh` token. *Fix: pass the body through `redact()` before
    writing it.*
38. **MINOR** — `fleet/bin/deploy.py:267-277`: `write_cloud()` runs only after the deployment POST,
    so a failure there leaves seven agents created with no ids recorded. *Fix: write the agent rows
    as soon as they are created.*
39. **MINOR** — `fleet/bin/deploy.py:98-108` drops the `has_more`/`after_id` pagination fallback
    that `fleetctl.py:68-75` carries; `/agents` is account-wide and filtered client-side at `:198`.
    *Fix: port the fallback.*
40. **MINOR** — `prompts/90-blocked.md:9,38` and `prompts/20-build.md:75` paste exact CI error text
    and 40 raw log lines into Asana with no scrub step. *Fix: add "redact anything matching a token
    shape before pasting" to `90-blocked.md` step 2.*
41. **MINOR** — every curl is pinned to `/usr/bin/curl`, a macOS-zsh workaround documented as such
    at `playbooks/make-coworld.md:270`, inside a Linux sandbox. *Fix: use `curl` and drop the note,
    or state that the sandbox image guarantees that path.*
42. **MINOR** — `prompts/60-verify.md:73` greps raw HTML from `softmax.com/<slug>` for an `<iframe>`;
    a client-rendered page yields a false negative on definition-of-done item 6. *Fix: record in
    `playbooks/observatory-api.md` whether that page is server-rendered, and give the fallback (the
    coworld detail API) if not.*
43. **MINOR** — `prompts/20-build.md:15-18` creates a **public** repo into which
    `prompts/10-design.md:27,38` copies the idea text verbatim; a confidential idea is published
    with no warning. *Fix: add a line to `00-claim.md` telling the coordinator to go to phase 90 if
    the idea text is marked confidential.*
44. **MINOR** — `prompts/50-league.md` depends on two contracts owed by `templates/`: an optional
    `"player"` field on a policy entry in `coworld-release.yml` (`prompts/40-release.md:24`,
    `playbooks/observatory-api.md:199-201`) and `coworld-submit.yml` emitting `submit-result.json`
    (`playbooks/observatory-api.md:196-197`). Both are marked BINDING in the playbook; neither is
    verified here (templates out of scope). *Fix: keep the BINDING markers and add a phase-20
    exit check that both workflow files parse and accept the named inputs.*
45. **MINOR** — `AGENT.md:27-29` says never to hard-code an id, but the prompts inline Asana project
    gids, both Discord ids and both `ply_` ids; the `ply_` ids are absent from `fleet/cloud.md`
    entirely (they live only in `playbooks/observatory-api.md:213-214`). *Fix: add a Players table
    to `fleet/cloud.md` and have `50-league.md` cite it.*

**Totals: 14 BLOCKING, 31 MINOR.**
