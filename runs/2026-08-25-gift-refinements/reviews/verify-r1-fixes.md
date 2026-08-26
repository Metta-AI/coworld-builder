# verify-r1 fixes — gift-refinements

Repo: `Metta-AI/cogame-gift-refinements` · main head **`d874ebd55a7244a57baa711c92651eaf55c4b08a`**
CI: `ci.yml` run **32926345524**
(https://github.com/Metta-AI/cogame-gift-refinements/actions/runs/32926345524) on that exact head —
conclusion **success** (test ✅, manifest-loads ✅, docker-smoke ✅, wasm-viewer ✅).

| defect | disposition | remote commit | files |
|---|---|---|---|
| D1 — lobby closes before the champion pods connect | fixed | `b4a29faed3110776011819e482e6deefe172b138` | `src/gift_refinements/sim_config.nim`, `src/gift_refinements/server.nim:356-367`, `tests/test_llm.nim:177-203` |
| D2 — mirror champion prompt causes `parse_error` fallback | fixed | `d874ebd55a7244a57baa711c92651eaf55c4b08a` | `tools/ci/policies.json`, `docs/plans/2026-08-25-gift-refinements-design.md:487-518`, `tests/test_manifest.nim:264-282` |

Both were pushed with `tools/push_via_api.py` (plain `git push` 401s on this repo), one invocation
per defect against the tree of that defect's local commit, so the remote history is two commits on
top of `30a0405` — one per defect, no force-push, no history rewrite. Local commit shas were
`b688f3e` (D1) and `f419222` (D2); the API push re-creates them, hence the different remote shas.

---

## D1 — the lobby must not close while seats are missing

**What the code did.** `runEpisode`'s lobby loop (`server.nim`) had two early-return conditions:

```nim
    if connected.len >= config.numAgents and registered >= config.numAgents:
      break
    if connected.len > 0 and registered >= connected.len and
        elapsedSeconds() >= 5:
      break
```

The second one — "every socket that happens to be connected has registered" — fired at t=5 s, the
moment the fast scripted filler pods had registered. `playerConnectTimeoutSeconds = 180` was never
reached, and the champion pods connected into an already-running round loop. Live evidence
(VERIFY.md check 4): round 2 `lobby closed with 3/6 seats connected, 3 registered`
(`llmOrders=1`, champion sources `llm=1 scripted=23`); round 4 `lobby closed with 4/6 seats
connected, 4 registered` (`llmOrders=2 fallbacks=1`, `llm=2 fallback=1 scripted=21`); round 3
`6/6` → `llmOrders=24`. `design.md` line 320: a scripted policy seated as a champion is a failure
state.

**What it does now.** The close rule is one predicate, `GameConfig.lobbyShouldClose(connected,
registered, elapsedSeconds)` in `src/gift_refinements/sim_config.nim`:

```nim
  if elapsedSeconds >= config.playerConnectTimeoutSeconds:
    return true
  connected >= config.numAgents and registered >= config.numAgents
```

The adaptive short-circuit now requires **every declared seat** (`numAgents` = 6) to be both
connected and registered. A partly-filled lobby waits out `playerConnectTimeoutSeconds` and only
then closes, seating scripted fallbacks for the missing seats exactly as before — the "seated.len
== 0 → forfeit" path, the held-registration re-drain and the round-loop drain are untouched. The
server loop became `while true: … if config.lobbyShouldClose(connectedSeats().len, registered,
elapsedSeconds()): break`.

**The test that pins it.** `tests/test_llm.nim`, block `lobbyStaysOpenUntilEverySeatIsIn`
(banner: `the lobby waits for every seat unless the connect timeout elapsed`). It asserts, on the
shipped default config:

- for every `connected = registered = 1..5`: the lobby does **not** close at t=0, at t=5 s (the old
  short-circuit's exact trigger point), or at `playerConnectTimeoutSeconds - 1` — this is the
  round-2/round-4 state, and it now stays open;
- 6 connected with only 5 registered does not close (a connected-but-unregistered champion pod);
- 6 connected + 6 registered closes immediately at t=0 (round 3's healthy path, and the CI smoke's);
- 0/0 closes at exactly `playerConnectTimeoutSeconds`, and 3/3 closes past it (the bound still
  holds, so a missing pod can never hang the episode).

**Evidence it works.** Run 32926345524 → job `test`: `✓ the lobby waits for every seat unless the
connect timeout elapsed` in both the debug and the release pass. Job `docker-smoke` plays a real
6-seat containerised episode: `starting game container` at 03:28:54Z, `smoke OK: seats=6 …
reason=complete` at 03:29:16Z — 21 s for the whole episode, i.e. the lobby still closed early
(≪180 s) once all six pods were in, and `all 6 player containers exited 0`.

## D2 — the champion prompts name `consume` as a field, not a job

**What happened.** Round 4 log: `unknown job consume (expected collect|meet|hold|evade)` → retry →
`target is required when job is meet or gift > 0` → `gift-refinements llm: seat 0 falling back to
scripted order (parse_error) on round 12`. The mirror prompt's own vocabulary caused it: *"stop
collecting and **spend or bank** your raw first. **Bank** only when you are holding more than ten
tokens…"* — nothing in the operator text tied "bank" to the order's `consume` field, so the model
answered `{"job":"consume", …}`.

**Prompt diff (`tools/ci/policies.json`).** Parser strictness and fallback recording are unchanged;
only the two `PLAYER_PROMPT` strings changed.

`gift-refinements-mirror`:

- removed: *"stop collecting and spend or bank your raw first. Bank only when you are holding more
  than ten tokens or when there are two rounds left;"*
- added: *"stop collecting — use job "hold" or job "meet" — and clear the raw first, either by
  firing it away as gift beams or by setting the "consume" field to "end" for that round. Set
  "consume":"end" only when you are holding more than ten tokens or when there are two rounds left,
  and "consume":"never" otherwise;"*
- appended (both champions, verbatim): *"SCHEMA, no exceptions: "job" is exactly one of collect,
  meet, hold or evade. Consuming is NOT a job — it is the separate "consume" field, whose only
  values are "now", "end" and "never" — so never answer with "job":"consume". Whenever "job" is
  "meet", or "gift" is greater than 0, "target" must be another cog's alias string, never null."*

`gift-refinements-patron` (checked for the same ambiguity, and it had it — "Hold your super tokens",
"the close banks whatever is left", with no field named):

- *"pick the ONE cog with the best return and commit — **answer job "meet" with that cog as
  "target"** every round"* (was: "meet it every round");
- *"**Keep the "consume" field on "never" while the chain is running:** hold your super tokens until
  the last two rounds…"* (was: "Hold your super tokens until…");
- plus the same SCHEMA sentence.

Prompt lengths 1352 / 1283 runes, well inside `MaxPromptRunes = 4000`, so nothing is truncated out
of the operator block. The docs copy of both prompts
(`docs/plans/2026-08-25-gift-refinements-design.md`, the in-repo design-note copy — the run's
`design.md` was not touched) was updated to the shipped text with a note naming the round-4 failure.

**Pinned by** `tests/test_manifest.nim`, block `policiesJsonNamesThisGame`: every `PLAYER_PROMPT`
must contain `collect, meet, hold or evade` and `Consuming is NOT a job`. Evidence: run
32926345524 → `✓ policies.json: two prompt champions (one owned by daveey-1) and two fillers`,
debug and release.

The optional parser tolerance (mapping a top-level `"consume"` job to hold+consume) was **not**
added, per the brief.

---

## NOTED (not fixed)

- `README.md`'s "Where this repo differs from the design note" section enumerates *ten* readings and
  does not carry an eleventh for D1. The in-repo design note still says at line 555 that
  "the lobby returns as soon as every connected socket has registered" — that sentence is now
  contradicted by `lobbyShouldClose`. Left alone deliberately: editing it is a design-note change,
  not a defect fix. Whoever owns the note should record that the adaptive close requires all
  `num_agents` seats.
- D1 leaves the "missing seat plays `reciprocator`" behaviour in place after the timeout; the
  verifier's suggestion of treating an unregistered champion seat at round start as a **hard error**
  is a design change (it would turn a degraded episode into a failed one) and was not made.

---

## Final state

- main sha: `d874ebd55a7244a57baa711c92651eaf55c4b08a`
- ci.yml run id: **32926345524** — conclusion **success**, head sha `d874ebd5…` (the pushed head,
  not a re-run of an older commit). The intermediate D1-only head `b4a29fae…` has its own push-run,
  32926265039.
- `coworld-release.yml` was **not** dispatched and the league was not touched.
