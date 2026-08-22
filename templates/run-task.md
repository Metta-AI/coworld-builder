# Run task template

Goes to: the **Coworld Builder** Asana board — the gid in the Asana table of `fleet/cloud.md`
(`1217747772236871`); it is a row in that table, **not** a shell variable, and nothing exports
`BUILDER_PROJECT` — section *Running* (`1217747860567752`).
Created by phase 00 (`prompts/00-claim.md`), one per claimed Coworld Idea.

Substitute: `<slug>`, `<idea title>`, `<run>` (= `<YYYY-MM-DD>-<slug>`), `<idea task gid>`,
`<idea task url>`, `<run task url>`.

---

## Title

```
<slug> — coworld run <run>
```

That exact form — it is the name `prompts/00-claim.md` step 4.8 creates. One run task per idea,
forever. The authoritative "is this idea claimed" test is the idea's gid appearing as `idea_task`
in some `runs/*/STATE.json` (or its gid in `runs/SKIPPED.json`), not the title
(`prompts/00-claim.md` step 4.2).

## Description

```
Idea:  <idea task url>
Repo:  https://github.com/Metta-AI/cogame-<slug>
Page:  https://softmax.com/<slug>
Run:   runs/<run>/ in Metta-AI/coworld-builder (STATE.json, log.md, reviews/, VERIFY.md)
CI:    https://github.com/Metta-AI/cogame-<slug>/actions

Coordinator: coworld-builder heartbeats a/b/c (minutes 11/31/51 UTC). This task is this run's
lock: a fresh heartbeat_at (the custom field, not this text) means a session is working it and
no other session may take it. Up to max_parallel_runs (fleet/cloud.md) runs are in Running at
once.

Phases (SPEC §Phases). The current phase is the first unchecked line.

- [ ] 00 claim      — run task + subtasks + runs/<run>/STATE.json + log.md
- [ ] 10 design     — docs/plans/<date>-<slug>-design.md accepted against the checklist
- [ ] 20 build      — repo scaffolded from the starter; ci.yml green on main
- [ ] 30 review     — reviewer/fixer/judge loop; judge returns zero blocking findings
- [ ] 40 release    — coworld-release.yml: build → certify → policies → upload → secret;
                      Canonical: yes, hosted certification certified
- [ ] 50 league     — league + division + settings, champions daveey & daveey-1,
                      fillers set BEFORE the first trigger-round
- [ ] 60 verify     — runs/<run>/VERIFY.md; every line of SPEC §Definition of done fetched
- [ ] 70 announce   — posted in Discord #coworlds; message id in STATE
- [ ] 80 close      — executive summary here and on the idea task; LEARNINGS entry;
                      this task Done, idea task completed

Blocked (90) is not a phase in this list: it is where any phase goes after three
distinct failed attempts. It moves this task to Blocked and files a subtask for a human.
```

The description carries **no** `heartbeat_at:` line. Do not add one — nothing reads it.

## Where the heartbeat lives

`heartbeat_at` is the Asana **custom field `1217748424048134`** (text, UTC ISO-8601, on the
Coworld Builder project; gid in `fleet/cloud.md`). It is read from the task's `custom_fields`
array and written with the custom_fields map:

```bash
curl -sS -X PUT "https://app.asana.com/api/1.0/tasks/<run task gid>" \
  -H "Authorization: Bearer $ASANA_PAT" -H 'content-type: application/json' \
  -d '{"data":{"custom_fields":{"1217748424048134":"2026-08-22T16:40:00Z"}}}'
```

Rules (`prompts/00-claim.md` step 2, `AGENT.md` §STATE, log, heartbeat discipline):

- Always `YYYY-MM-DDTHH:MM:SSZ` (UTC, no offsets, no fractional seconds); an unparseable
  stamp is treated as **stale**.
- The same value is written to `runs/<run>/STATE.json.heartbeat_at` in the same action,
  and STATE is committed and pushed. STATE is the record; the custom field is the lock.
- If the field is empty or absent, the fallback is the last
  `<UTC ISO-8601> heartbeat phase=<nn>` line in `runs/<run>/log.md` — that exact format, and
  nothing else counts.
- Fresh (< 90 min) **and** `STATE.session_ended_at` null or older: a session is working this run
  right now → any other heartbeat leaves it alone and counts it toward `live`
  (`max_parallel_runs`, `fleet/cloud.md` §Parallelism). Several runs fresh at once is normal.
- Stale (≥ 90 min), **or** `session_ended_at` ≥ `heartbeat_at`: the run is yours → resume at
  `STATE.json.phase`, through the session-nonce guard (`prompts/00-claim.md` step 5.0).

## Subtasks

Phase 00 creates one subtask per phase, titled `<n> <name>` (`10 design`, `20 build`, …),
unassigned, and completes each one as its phase finishes. They are progress reporting for
humans; the checklist above and `STATE.json.phase` are the machine-readable truth.
