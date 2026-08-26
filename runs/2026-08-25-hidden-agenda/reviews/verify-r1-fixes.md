# verify-r1 fixes — hidden-agenda

Head: `731ab43ebbd6fcb3908b583855cc1c75270763c7` (local commit `ca271d4`, re-created by
`tools/publish.py` as `731ab43`)
CI: https://github.com/Metta-AI/cogame-hidden-agenda/actions/runs/32930232996 — **success**
(headSha `731ab43ebbd6fcb3908b583855cc1c75270763c7`; jobs `test` ✓, `docker-smoke` ✓,
`wasm-viewer` ✓)

| finding | disposition | commit | files |
|---|---|---|---|
| VERIFY check 4/5 cause B — the reply parser rejects the compact job form the prompts themselves teach | fixed | `731ab43` | `src/hidden_agenda/llm.nim:519-556` (schema hint), `src/hidden_agenda/llm.nim:576-590` (`splitCompactJob`), `src/hidden_agenda/llm.nim:605-645` (argument fallback), `src/hidden_agenda/llm.nim:658-681` (switch degrade), `tests/test_llm.nim:98-176`, `docs/POLICIES.md:106,111-115` |

One finding, one commit.

---

## Cause B — champion seats fall back to scripted because their own replies are rejected

### What the code did

Two ends disagreed with each other.

**The prompt taught the compact form.** `systemPrompt` (llm.nim:373) documents

```
  mine at:<seam>   walk to that seam and mine until your hands are full
  watch who:<cog>  stand 3-5 cells away and keep your cone on that cog
  patrol room:<r>  sweep a room's four corners looking for bodies
```

**The schema hint never spelled the sibling keys.** `userPrompt` (llm.nim:520, pre-fix) emitted

```
REPLY with ONLY {"plan":[{"job":...}], "hunch":"<=80 chars", "notes":"<=240 chars"}
  plan: 1..3 steps; job is one of mine | deposit | watch | patrol | guard | hold
```

`{"job":...}` with an ellipsis was the only structural example the model ever saw, so it wrote
the documented compact string into the one key it was shown.

**The validator demanded sibling keys and nothing else** (llm.nim:568-586, pre-fix): `job` had to
match a `JobKind` exactly, with `at`/`who`/`room` as separate keys.

Result, verbatim from the hosted round-3 log (`VERIFY.md` §5a):

```
hidden-agenda llm: seat 0 attempt 1 failed: unknown job: mine at:s2
hidden-agenda llm: seat 1 attempt 1 failed: mine needs at: one of S1..S6, got ''
hidden-agenda llm: seat 0 attempt 2 failed: mine needs at: one of S1..S6, got ''
hidden-agenda llm: seat 1 attempt 2 failed: mine needs at: one of S1..S6, got ''
```

Both attempts burn, the seat plays scripted. In round 3 this was **10 of 14** attempt-failures —
the majority cause, ahead of the Bedrock 429s (4). Champion real-LLM share across rounds 2/3/4:
12.5 % / 12.5 % / 20 %.

### What it does now

**1. The schema hint spells the exact step objects, per role and per moment** (llm.nim:519-556).
A crew seat at the opening now reads:

```
REPLY with ONLY {"plan":[<step>,...], "hunch":"<=80 chars", "notes":"<=240 chars"}
  plan: 1..3 steps; each <step> is ONE object whose argument is a SIBLING key of "job", never inside it:
    {"job":"mine","at":"S2"} {"job":"deposit"} {"job":"watch","who":"BLUE"} {"job":"patrol","room":"NW"} {"job":"guard"} {"job":"hold"}
  seam ids: S1 S2 S3 S4 S5 S6 · room ids: NW N NE SW S SE HUB
  aliases ACTIVE right now: RED BLUE GREEN YELLOW PINK
```

and the impostor seat at a meeting additionally gets the switch marked nullable and its own three
jobs:

```
REPLY with ONLY {"plan":[<step>,...], "vote":"<active alias or skip>", "switch":{"if":"<active alias or tie>","to":"<active alias or skip>"} or null, "say":"<=90 chars", "hunch":"<=80 chars", "notes":"<=240 chars"}
  plan: 1..3 steps; each <step> is ONE object whose argument is a SIBLING key of "job", never inside it:
    {"job":"mine","at":"S2"} {"job":"deposit"} {"job":"watch","who":"RED"} {"job":"patrol","room":"NW"} {"job":"guard"} {"job":"hold"}
    {"job":"hunt","who":"RED"} {"job":"strike","who":"RED"} {"job":"lurk","room":"SE"}
```

The caps, the one-JSON-object contract and the seam/room/alias lists are unchanged. The `who`
example is the first alias that is **active right now and is not this seat**, so a model that
copies the shape verbatim is not immediately rejected by
`step.who == Aliases[slot]` — the example is a legal step, not just a legal shape.
The old `plan: … job is one of <jobList>` line is gone because the example row now enumerates
exactly that role's jobs, with their shapes.

**2. The validator honours the compact form** (llm.nim:576-590, 605-645). New private helper:

```nim
proc splitCompactJob(text: string): tuple[job, arg: string] =
  ## `"mine at:S2"` -> `("mine", "S2")`. …
```

It splits on whitespace, takes the first token as the job name, and takes the text after the
first `:` in the remainder as the argument (falling back to the whole remainder if there is no
colon). `parseReply` feeds it the already-lower-cased `job` string, so the argument is
case-insensitive; each of `at` / `who` / `room` reads its **sibling key first** and falls back to
the inline argument only when the sibling is absent or empty. Every existing enum check runs
unchanged afterwards, so `mine at:S9`, `watch who:<frozen cog>`, an unknown job, and an
impostor-only job on a crew seat all still invalidate the reply.

**3. A one-sided `switch` degrades to no conditional** (llm.nim:658-681). Previously
`if condition.len == 0 or target.len == 0: raise "switch needs both \"if\" and \"to\""` threw the
whole reply away — plan, vote and all — over an **optional** field; that message is in the round-2
log. Now the conditional is simply not set. The reasoning is recorded as a code comment at the
site:

> A HALF-WRITTEN switch degrades to "no conditional" instead of invalidating the whole reply. The
> design note's reply-schema table calls a malformed switch an invalid reply, but its governing
> intent is degrade-never-hang, and the strict reading is what the retry-then-fallback cost is
> measured against … A switch that names an inactive cog is still invalid — that one is a claim
> about the roster, not a missing key.

The inactive-alias case is deliberately still `invalid`: `design.md:694`'s "naming an inactive
cog" clause survives, and `tests/test_llm.nim:89` ("a switch naming an inactive cog is invalid")
still passes untouched.

**4. `docs/POLICIES.md`** — the shipped policy contract, inlined into the coworld manifest by
`tools/build_manifest.py:228`, is updated so it does not now contradict the parser: the `switch`
row's "on violation" cell reads *"naming an inactive cog → invalid; missing one of the two keys →
no conditional"*, and a sentence after the table records that a step's argument may also be
written compactly inside `job`, with the sibling key winning when both are present.

### Test lines added — `tests/test_llm.nim`

Two new blocks, 80 lines, between `block meetingSchema` and `block sayIsIgnoredNotRejected`.

`block theCompactJobFormTheSystemPromptTeachesIsHonoured` (test_llm.nim:98-159), using a local
`plan()` helper that returns `parseReply(...).plan`:

- `{"job":"mine at:S2"}` parses to the **same `seq[PlanStep]`** as
  `{"job":"mine","at":"S2"}` — *"mine at:S2 parses to the same plan as the sibling-key form"* —
  and `compactMine[0].job == jkMine and compactMine[0].at == "S2"`.
- `{"job":"mine at:s2"}` (lower-case) equals the canonical plan — *"the compact argument is
  case-insensitive, like the sibling key"*.
- `watch who:PINK`, `patrol room:NW` each equal their canonical form; for the impostor seat
  (slot 4) `hunt who:GREEN`, `strike who:RED`, `lurk room:SE` each equal theirs.
- Nothing else is loosened: `{"job":"teleport"}` invalid (*"a genuinely unknown job is still
  invalid"*), `{"job":"scuttle at:S2"}` invalid, `{"job":"mine at:S9"}` invalid (*"a compact
  argument still has to name a real seam"*), `{"job":"hunt who:PINK"}` on a crew seat invalid.
- The prompt half: `userPrompt(sim, 0, "", "opening")` contains
  `{"job":"mine","at":"S2"}`, `{"job":"patrol","room":"NW"}` and `{"job":"watch","who":"BLUE"}`
  (a live, non-self alias); the impostor's prompt contains `{"job":"lurk","room":"SE"}` and the
  crew prompt does **not**; and *"every step the hint shows is itself a valid step"* —
  `{"job":"watch","who":"BLUE"}` parses.

`block aHalfWrittenSwitchDegradesRatherThanInvalidating` (test_llm.nim:161-176): for each of
`{"if":"tie"}`, `{"to":"skip"}` and `{}` alongside a valid plan and `"vote":"PINK"` at an open
meeting — the reply **parses**, `decision.switchIf` and `decision.switchTo` are both empty
(*"it degrades to no conditional at all"*), and `decision.vote == "PINK"` with a one-step plan
(*"and the plan and the vote survive"*).

The canonical forms are still covered by the untouched `block schema` (`mine`/`at`, `watch`/`who`,
`patrol`/`room`, case-insensitive `"s5"`) and `block meetingSchema` (`switch` with both keys, the
inactive-cog rejection, `switch: null`).

### Evidence

- Local, before the change: `nim r --hints:off --path:src tests/test_llm.nim` → `test_llm: ok`
  (baseline green, pre-existing `imported and not used: 'station'` warning unchanged).
- Local, after: all eleven `tests/*.nim` run in both debug and `-d:release` → 22/22 pass.
- CI on the pushed head `731ab43`:
  https://github.com/Metta-AI/cogame-hidden-agenda/actions/runs/32930232996 — **success**.
  `test` (both modes, every test file), `docker-smoke` (image build + a real episode) and
  `wasm-viewer` (bundle built and executed in headless chromium against that episode's replay,
  `--strict-text-bounds --soak 10`) all green.

### What this does not prove

CI runs `docker_smoke.sh` with no `ANTHROPIC_API_KEY`, so no CI job exercises a live model reply.
The proof that the *hosted* fallback rate drops is a re-run of VERIFY checks 4 and 5 against a
round played on a release built from `731ab43`. Cause A (`llm throttled (429): "Too many tokens
per day"`, confirmed platform-wide against the `coins` coworld) is untouched by this commit and
will still produce some fallbacks.

---

## NOTED (not fixed)

- `RetryHint` (llm.nim:29-32) still says *"using one of the listed job names, a seam id from the
  list, an alias that is active right now"* — accurate, but it does not restate the object shape
  either. The schema hint is in the retried user prompt in full, so the retry now carries the
  sibling keys anyway; left alone.
- `design.md:694` and its `switch` "on violation" row now describe the pre-fix behaviour. The
  design note is out of this role's write scope; flagging it for the coordinator so the note and
  the code can be reconciled.
- `VERIFY.md` check 8's two legibility observations (`feed_lines: 0` DOM-selector mismatch,
  `bridge_ready: false`) are untouched — not this finding.
