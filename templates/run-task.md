# Run task template

Goes to: the **Coworld Builder** Asana board (`$BUILDER_PROJECT`), section *Running*.
Created by phase 00 (`prompts/00-claim.md`), one per claimed Coworld Idea.

Substitute: `<slug>`, `<idea title>`, `<run>` (= `<YYYY-MM-DD>-<slug>`), `<idea task gid>`,
`<idea task url>`, `<run task url>`.

---

## Title

```
RUN <slug> — <idea title>
```

One run task per idea, forever. If the title already exists on the board, the idea is
claimed — skip it (SPEC §Runtime step 4).

## Description

```
Idea:  <idea task url>
Repo:  https://github.com/Metta-AI/cogame-<slug>
Page:  https://softmax.com/<slug>
Run:   runs/<run>/ in Metta-AI/coworld-builder (STATE.json, log.md, reviews/, VERIFY.md)
CI:    https://github.com/Metta-AI/cogame-<slug>/actions

Coordinator: coworld-builder (hourly heartbeat, minute 11). This task is the lock:
while it sits in Running with a fresh heartbeat_at, no other run starts.

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

heartbeat_at: <ISO8601 UTC>
```

## The heartbeat line

The last line of the description is rewritten by the coordinator, in place, at least every
15 minutes of work and on every phase transition:

```
heartbeat_at: 2026-08-22T16:40:00Z
```

Rules:

- Exactly one `heartbeat_at:` line, always last, always `YYYY-MM-DDTHH:MM:SSZ` (UTC, no
  offsets, no fractional seconds). The next heartbeat parses it with a strict format —
  an unparseable stamp is treated as **stale**.
- The same value is written to `runs/<run>/STATE.json.heartbeat_at` in the same action,
  and both are committed and pushed. STATE is the record; the task line is the lock.
- Fresh (< 90 min): another run is live → the heartbeat exits without touching anything.
- Stale (≥ 90 min): the run is yours → resume at `STATE.json.phase`.

## Subtasks

Phase 00 creates one subtask per phase, titled `<n> <name>` (`10 design`, `20 build`, …),
unassigned, and completes each one as its phase finishes. They are progress reporting for
humans; the checklist above and `STATE.json.phase` are the machine-readable truth.
