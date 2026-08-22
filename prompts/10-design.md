# Phase 10 — Design

Purpose: turn the idea text into a single design note that fully determines the build.
Owner: designer sub-agent, accepted (or bounced) by the coordinator against the checklist below.

## Inputs

- `STATE.idea_task`, `STATE.slug`, `STATE.run`.
- The idea task's notes (verbatim) — fetch fresh, do not use a cached paraphrase.
- `playbooks/make-coworld.md` §Phase 0 (design pins).
- The six starter repos, mounted read-only at `/workspace/starters/<name>` (see the starter
  table; the mounts are declared in `fleet/deployment.json`).

## Starter table (the coordinator picks; it never asks)

| Game shape | Starter (mount) | Lineage |
|---|---|---|
| Turn-based / talk / cards / board / dice / bluff; game logic native; policy = LLM prompt | `Metta-AI/cogame-babel` (`/workspace/starters/cogame-babel`) — the best current parley-stack template. Fall back to a newer descendant (`cogame-bullwhip`, `/workspace/starters/cogame-bullwhip`) if it is closer. | parley → cosino → focus → babel → bullwhip |
| **Any real-time game loop** (grid OR continuous physics, new rules written for this coworld), RL-vector policies | `Metta-AI/coworld-ctf` (paintbot) — `/workspace/starters/coworld-ctf` | ctf |
| Bit-exact port of an **existing, external** C/RL environment (the rules already exist as code you must reproduce; e.g. NMMO, MOBA) | `Metta-AI/cogame-moba` + `docs/PORTING.md` — `/workspace/starters/cogame-moba` | moba → nmmo |

A new physics game (Box2D soccer, hide-and-seek, couch-carrying) is the FIRST row, not the second — nothing pre-exists to port; paintbot supplies the loop, the per-tick replay, the static viewer and the chrome, and you swap the arena rules for the physics sim. (Operator ruling 2026-08-22, Cogball.)
| Game logic in an external engine/process | `Metta-AI/cogame-factorio` (Python connector, per-seat servers) — `/workspace/starters/cogame-factorio` | factorio |

`Metta-AI/cogame-parley` is mounted too (`/workspace/starters/cogame-parley`) as the lineage's
root reference.

Ambiguity between two starters is a **rail**: pick the one with the closer turn structure and log
the reason. Never go to phase 90 for a starter choice.

## Procedure

1. Fetch the idea text and record it verbatim into the design note's source-idea block.
2. Choose the starter from the table; write `STATE.starter`.
3. Send the **designer** brief (self-contained):

   > Write the design note for a new coworld at `Metta-AI/cogame-<slug>`, forked from
   > `<starter>` (mounted read-only at `/workspace/starters/<starter>`). Source idea, verbatim:
   > `<idea text>`.
   > Output exactly one file: `docs/plans/<YYYY-MM-DD>-<slug>-design.md` in the new repo, with
   > these H2 sections **in this order and with these names**:
   > `## The game`, `## Decisions: LLM with scripted fallback`, `## Sim module`,
   > `## Server, player, protocol`, `## Viewer`, `## Packaging`, `## Tests`,
   > `## Out of scope (v1)`. Precede them with a title line and a paragraph naming the starter
   > and stating "every convention there holds here unless this note says otherwise", then the
   > verbatim source idea.
   > The note must decide, not survey: exact seat count (`num_agents`), exact resolution rules in
   > numbered order, exact scoring formula and sign, exact end conditions and `results.reason`
   > values, the full observation each seat gets, the reply schema with per-field character caps,
   > the event record written to the replay, the viewer's readouts, the manifest variants, and the
   > test list. Reference `playbooks/make-coworld.md` §Phase 0 for the non-optional pins and state
   > how each is satisfied. Do not write code. Do not ask questions — decide and log the reason.

4. Coordinator reviews the returned note against the **design-note checklist** below. Reject with
   named gaps at most 3 times; each rejection must name the failing checklist items.
5. Copy the accepted note to `runs/<run>/design.md`, commit, push.

## Design-note checklist (all must be answerable from the note alone)

- [ ] Starter named, with the one-line reason.
- [ ] `num_agents` fixed and stated as a single unambiguous number; it appears in the packaging
      section for **every** manifest variant and the cert fixture. Phase 20 substitutes it into
      `<SEATS>` in `tools/ci/docker_smoke.sh`, where it becomes an independent cross-check against
      the manifest — so a vague or ranged seat count here fails CI later, not here.
- [ ] Turn/tick structure and the exact resolution order, numbered.
- [ ] Scoring formula, its sign, and what the league ranks by.
- [ ] End conditions, including the `deadline` case, and which `results.reason` values are legal.
- [ ] Per-seat observation: exactly what is visible and what is hidden.
- [ ] Reply schema with a character cap on every free-text field (and a note that truncation is on
      **rune** boundaries).
- [ ] Both policies specified: LLM prompt policy **and** scripted baseline, same image,
      env-switched (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=<baseline name>`), plus the baseline's algorithm.
- [ ] Simultaneous-decision games: states that all seats' LLM calls go out as **one parallel batch
      per turn**, and gives the per-turn wall-clock budget inside 60 % of `episodeTimeoutSeconds`
      (≈720 s total).
- [ ] Degrade-never-hang: what happens when a seat's decision times out or fails to parse
      (retry once → fallback to the scripted move), and how the episode settles early.
- [ ] Two name spaces: anonymous cog aliases in-game; real player names spectator-side only.
- [ ] Viewer: static wasm bundle (`replay_viewer.bundle = static-replay-viewer`), the build hook
      `tools/build_replay_viewer.sh`, the starter chrome reused verbatim, the readouts listed, and
      an explicit note that it is legible at **360 px** wide.
- [ ] Replay bytes are self-sufficient: every field the viewer needs is recorded (names, config,
      per-tick state, seed).
- [ ] Packaging: `compose.yaml`, `coworld_manifest_template.json`, `game.docs`
      (`readme` + `pages`) and `game.protocols` (**both** `player` and `global`).
- [ ] Tests: sim unit tests, a bounded-orders/legality assertion on the scripted baseline, an
      end-to-end episode writing a replay, a strict-UTF-8 replay parse, and a viewer smoke.
- [ ] Out of scope (v1) is non-empty.

## Exit criterion

`docs/plans/<date>-<slug>-design.md` exists on `main` of the new repo (or in the working tree ready
for phase 20's first push), every checklist box is checked in `runs/<run>/log.md`, and a copy is at
`runs/<run>/design.md`.

## Writes

- STATE: `starter`, `repo`, `phase: "20"`, `heartbeat_at`.
- `runs/<run>/design.md`; `log.md` line per designer round with the rejected items.
- Asana: complete the phase-10 subtask; comment with the starter and the one-line game summary.

## Retry budget

3 designer rounds. On the 4th failure → `prompts/90-blocked.md`, but only if the residual gap is a
genuinely open **rule** whose readings give materially different games. Anything the rails cover
(seat count, scoring when the idea pins one, parameter tuning, viewer composition) the coordinator
decides itself and logs.
