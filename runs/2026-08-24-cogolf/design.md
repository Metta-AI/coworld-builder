# cogame-cogolf — design note (2026-08-24)

Forked from **`Metta-AI/cogame-factorio`** (read at `/workspace/starters/cogame-factorio`), because the
idea pins "sandboxed like Factorio's code harness" with a *code agent* policy interface, and factorio is
the only starter that already ships code-as-a-move over the websocket (a per-turn program reply, a
sandboxed execution step with its own timeout, per-seat noop/strike bookkeeping, a code/output plaque in
the replay chrome). **Every convention there holds here unless this note says otherwise.** The one
structural departure, decided up front: cogolf needs **no external engine** — there is no Factorio
server, no FLE, no RCON, no `/opt/factorio`. The "engine" is a sandboxed Python test-runner that lives
inside the game container. Everything in the starter that touches `factorio.py` / `session.py` / the FLE
dependency is deleted; the server, player harness, protocol shape, replay-writing discipline, viewer
stack and CI shape are kept. That deletion is what makes the smaller decisions below simple: the game
image is `python:3.11-slim` + `aiohttp` (no 520 MiB Factorio download, no `uv` FLE tree), every seat
shares one deterministic in-process world instead of one VM each, and an episode costs seconds of CPU
rather than minutes of simulation.

**Source idea (verbatim, Asana idea task 1217704516788789 — "18 Cogolf — write a program that passes my tests; write tests that break your program"):**

> Two seats alternate: a spec is revealed; each writes an implementation and a test suite. You score for
> tests that fail the opponent's code and for code that passes the opponent's tests; ambiguous specs make
> the reading of intent the contest. Sandboxed like Factorio's code harness.
>
> Seats: 2
> Motive: zero-sum, adversarial verification
> Policy interface: code agent
> Fills gap: adversarial programming / spec interpretation
> Integrity (anti-collusion): Two-player zero-sum with sandboxed execution — collusion has no payoff
> surface; anonymous aliases prevent cross-episode win-trading.
>
> Replay plan (watchability): No walls of code: each test is a projectile fired at the opponent's
> code-fortress — deflected (pass) or breaching with crumble FX (fail); the spec hangs as a scroll above
> the arena. Endcard shows the single killer test with a one-line why.

---

## The game

**Cogolf is a nine-hole match between two code agents.** Each hole reveals one deliberately ambiguous
spec. Both seats simultaneously submit (a) an implementation of `solve(...)` and (b) up to five test
cases. Then the harness cross-fires: your tests are shot at their code, theirs at yours, and a hidden
"par" suite audits both. You score for shots that breach and lose for shots you take. The specs are
written so that one clause admits two honest readings; a hidden **reference implementation** settles
which reading is real, and a test only counts if the reference agrees with it. So the contest is exactly
what the idea names: read the intent better than your opponent, then aim at where their reading differs.

### Seats, names, and the two name spaces

- **`num_agents` = 2. Always 2, in every variant and in the certification fixture. There is no other
  seat count.** Slot 0 and slot 1 are symmetric; the game is zero-sum between them.
- **In-game aliases (what a policy sees):** slot 0 = `Ash`, slot 1 = `Basil`. Fixed, anonymous, and the
  only identity in `welcome`, in any observation, in a spec prompt, or in an opponent's history entry. A
  policy can never learn which player or policy it is facing, so there is no cross-episode win-trading
  surface.
- **Real player names (spectator side only):** `config.players[i].name` (e.g. `daveey`, `daveey-1`,
  `Baseline (1)`) is recorded in the replay as `names[i]` and rendered by the viewer's seat chips and
  endcard under the alias. It is never sent to a player container. Both name spaces are recorded in the
  replay: `names` (real) and `aliases` (in-game).

### The spec deck

Twelve specs ship in `server/cogame_cogolf/specs/` (one module per spec, key = module name), deck id
`core`, `DECK_VERSION = "core-1"`. Every spec's `solve` takes and returns **JSON values only** (null,
bool, int, float, str, list, dict-with-string-keys) — that is what makes a test a data record instead of
an expression, and it is what makes the replay legible.

Each spec module declares exactly these attributes:

| attribute | type | meaning |
|---|---|---|
| `KEY` | str | stable id, e.g. `"range_merge"` |
| `TITLE` | str, ≤ 48 chars | scroll headline |
| `PROMPT` | str, ≤ 1200 chars | the spec text shown to **both** seats, verbatim |
| `SIGNATURE` | dict | `{"function":"solve","params":[{"name":"xs","type":"list[int]"}],"returns":"int"}` |
| `EXAMPLES` | 2 items | `{"args":[...],"expect":...}` — shown to both seats, reference-consistent |
| `reference(*args)` | callable | the hidden oracle; the only authority on the ambiguous clause |
| `PAR_TESTS` | 4 items | hidden audit cases `{"name","args","expect"}` (reference-consistent) |
| `SAFE_TESTS` | 5 items | reference-consistent shots the `literalist` baseline fires |
| `EDGE_TESTS` | 5 items | aggressive shots (some reference-*in*consistent) the `pedant` baseline fires |
| `LITERAL_IMPL` | str | source the `literalist` baseline submits |
| `NAIVE_IMPL` | str | source the `pedant` baseline submits |
| `AMBIGUITY` | str, ≤ 140 chars | one-line spectator note: what the reference decided. **Replay only** |

The twelve specs and the clause the reference settles:

| key | one-line spec | the ambiguity the reference resolves |
|---|---|---|
| `longest_run` | length of the longest run of equal elements | empty list → `0`, not an error |
| `median` | median of a list of ints | even length → the **lower** middle, not the mean |
| `title_case` | capitalise each word of a string | an already-ALL-CAPS word is left untouched; runs of spaces are preserved |
| `roman` | int 1..3999 → Roman numeral | subtractive forms (`4`→`"IV"`); out of range → reference **raises** (such tests are illegal) |
| `chunk` | split a list into chunks of size `n` | the trailing short chunk is **kept**; `n <= 0` → reference raises |
| `dedupe` | remove duplicate items | first-occurrence order preserved, **not** sorted |
| `word_count` | word → count dict for a string | keys lowercased; edge punctuation stripped; `don't` is one word |
| `round_to` | round a float to `n` decimals | half-**away-from-zero**, not banker's; negative `n` rounds to tens/hundreds |
| `range_merge` | merge overlapping `[start,end]` intervals | ends are inclusive, so `[1,2]` and `[2,3]` **do** merge |
| `top_k` | the `k` most frequent items | ties broken by first appearance; `k` > distinct → all of them; `k = 0` → `[]` |
| `path_norm` | normalise a POSIX-ish path | trailing slash dropped except for `"/"`; `..` at root is dropped, not an error |
| `score_grade` | numeric score → letter grade at 90/80/70/60 | boundaries are **inclusive lower bounds**; `>100` clamps to `"A"`; negative → `"F"` |

A hole's spec is drawn without replacement:
`random.Random(seed).sample(sorted(deck_keys), holes)`. `seed` comes from `config.seed` when it is a
positive integer, otherwise the server mints `secrets.randbits(32)`. **The resolved seed is recorded in
the results doc and in the replay**, so an episode is reproducible from its bytes.

The deck is public (the repo is public). That is deliberate and symmetric: both seats see the same
prompt, neither policy container has repo access at runtime, and the reference stays out of every
observation. A memorised deck would help both champions equally.

### One hole, in exact resolution order

Numbered; the engine executes these steps in this order for hole `h` (1-based, `holes` total):

1. **Draw and reveal.** The engine picks spec `h` from the seeded sample and emits `hole_start`. Both
   seats are sent the *same* `observation` message (§Server, player, protocol) in one send loop — one
   parallel batch, not seat-by-seat.
2. **Collect.** The engine waits until `hole_deadline_seconds` for both seats' `submission` messages,
   concurrently (`asyncio.wait` over both seats, not two sequential awaits).
3. **Retry once.** For each seat with no valid submission at the deadline, the engine immediately
   re-sends the identical observation with `"retry": true` and `deadline_seconds = retry_deadline_seconds`
   and waits again (again for both retrying seats concurrently).
4. **Fallback.** A seat still without a valid submission gets one synthesised by
   `server/cogame_cogolf/baseline.py::literalist(spec)` — a real, legal move. The seat's
   `fallbacks` counter and the matching `fallback_causes` counter (`timeout`, `malformed`, `oversize`,
   `disconnected`, `host_error`) increment, and the `submission` event records
   `"fallback": {"cause": "...", "baseline": "literalist"}`. **No seat is ever removed from play; every
   hole is resolved for both seats.**
5. **Sanitise.** Each submission is normalised: free-text fields truncated on rune boundaries, tests
   beyond the cap dropped, lone surrogates replaced with `U+FFFD`, control characters other than `\n`
   and `\t` stripped. (Caps in §Server, player, protocol.)
6. **Load.** Each seat's `impl` is loaded in the sandbox. If it fails to compile or does not define a
   callable `solve`, the seat's impl is marked `broken: true` with a ≤ 300-char reason; **a broken impl
   fails every shot and every par test** for that hole.
7. **Legality gate.** Every test of both seats is run against the spec's `reference` in the sandbox. A
   test is **legal** iff: the args are a JSON list matching the signature's arity, the reference call
   neither raises nor exceeds its CPU budget, and `canon(reference(*args)) == canon(expect)`. Otherwise
   it is **illegal** with a reason in
   `{arity, not_json, oversize, ref_error, ref_timeout, ref_mismatch, duplicate}` — `duplicate` = the
   same canonical `args` as an earlier *legal* test from the same seat in the same hole. Illegal tests
   never fire and never score. They are recorded, and their reason is returned to their author in the
   next observation.
8. **Cross-fire.** Seat 0's legal tests are run against seat 1's impl and vice versa, in submission
   order. Outcome per shot: `held` if the defender returns a value equal (`canon`) to `expect`;
   `breach` if it returns anything else, raises, exceeds its per-call CPU budget, returns a
   non-JSON-representable value, or the defender's impl is broken. The defender's observed value or
   error text (≤ 300 chars, rune-truncated) is recorded.
9. **Par audit.** The spec's four hidden `PAR_TESTS` are run against each impl. `par_fails[i]` = how
   many the seat's impl failed (same pass/fail rule as step 8).
10. **Score the hole** (formula below), emit `test_verdict` per shot, `par_result` per seat, and
    `hole_score`.
11. **Wall guard.** If `wall_remaining < hole_reserve_seconds` (80 s) the episode stops here with
    `reason = "deadline"`; otherwise go to hole `h+1`, or finish with `reason = "complete"` after the
    last hole.

**Equality (`canon`)** is defined once and used everywhere: tuples become lists; only
`None/bool/int/float/str/list/dict[str]` are representable; `NaN`/`Infinity` are not; numbers compare by
value so `1 == 1.0`; **`True` never equals `1`** (bools are type-tagged); dict key order is irrelevant;
strings compare by exact code points. A value outside that set makes the call a `breach` for the
defender (`bad_value`).

### Scoring — formula, sign, what the league ranks by

For hole `h`, seat `i`, opponent `j`:

```
hole_score[i][h] = (breaches[i][h] + par_fails[j][h]) - (breaches[j][h] + par_fails[i][h])
```

where `breaches[i][h]` = seat `i`'s **legal** tests that made seat `j`'s impl fail (0..5), and
`par_fails[i][h]` = hidden par tests seat `i`'s own impl failed (0..4). Illegal tests contribute nothing.

```
scores[i] = sum over resolved holes of hole_score[i][h]
```

- **Sign: higher is better.** A positive score means you breached more than you were breached and your
  code survived the audit better than theirs.
- **Zero-sum by construction:** `hole_score[0][h] == -hole_score[1][h]` and therefore
  `scores[0] + scores[1] == 0` — a unit test asserts this on randomised outcome matrices.
- Per-hole range is ±9; a nine-hole match ranges ±81.
- **The league ranks by `scores`**: the platform reads the per-seat scalar out of the results doc, higher
  wins, `scores == [0, 0]` is a draw, and Elo follows from that. There is no secondary tiebreak inside
  the game.

The `par_fails` term is what stops a degenerate "write no tests, write no code" equilibrium: even against
a silent opponent, code that fails the hidden audit loses points. The `breaches` term is the idea's
"tests that fail the opponent's code"; the negated `breaches[j]` term is its "code that passes the
opponent's tests". Both are in, and the pair is exactly antisymmetric.

**Killer test** (for the endcard): among all `breach` shots of the winning seat, the one with the largest
`hole_score` swing, tie-broken by earliest hole then lowest test index. Recorded as
`killer_test = {"hole", "slot", "target_slot", "name", "why"}`, with the shot's author-supplied `why`
line. If the match is a draw or nobody breached, `killer_test` is `null` and the endcard says
`NO BREACH — DRAWN MATCH`.

### End conditions and legal `results.reason` values

The results doc key is **`reason`** (renamed from the starter's `end_reason`, because the platform's
phase-60 verification and `tools/ci/docker_smoke.sh` both read `results.reason`). The closed enum is
exactly three values:

| `reason` | when | scores |
|---|---|---|
| `complete` | all `holes` holes resolved | full match |
| `deadline` | the engine's `wall_clock_budget_seconds` expired, or `wall_remaining < 80 s` before a hole started | as of the last **fully resolved** hole; a hole interrupted mid-resolution is discarded, not half-scored |
| `harness_fault` | the sandbox runner could not be spawned or the spec deck failed to load mid-episode | as of the last fully resolved hole; artifacts still written; process exits 0 |

`deadline` is an acceptable ending for phase 60 verification but not the expected one: the timing
arithmetic below puts a normal nine-hole episode at ≈ 230 s and the worst case at 677 s, both inside the
720 s play budget. A seat that never connects does **not** end the episode: it plays the `literalist`
fallback every hole, and the lowest never-connected slot is reported once to
`COGAME_PLAYER_FAILURE_URI` (starter behaviour, kept).

Exit codes (starter's, kept): `0` episode complete (including `deadline`/`harness_fault`, artifacts
attempted); `2` missing or invalid config (unknown deck, `holes` > deck size, seats ≠ 2).

### Timing arithmetic (stated out loud, so the builder can check it)

`episode_timeout_minutes = 20` → the platform's `episodeTimeoutSeconds` is 1200 s; the play budget is
**60 % = 720 s**.

- Per hole, worst case: `hole_deadline_seconds` 40 + `retry_deadline_seconds` 15 = **55 s** of decision
  time (both seats in parallel — the batch costs the max of the two, not the sum), plus sandbox
  resolution: 3 subprocess batches (reference legality; impl 0; impl 1) × `sandbox_batch_seconds` 6 =
  **18 s**. Worst case **73 s/hole**.
- `9 × 73 = 657 s` + ≈ 20 s of startup/connect + ≈ 3 s of artifact writing = **680 s < 720 s**. ✅
- Typical case: Haiku answers a submission in 12–25 s, the sandbox in < 1 s → ≈ 25 s/hole → **≈ 230 s**
  per episode.
- `wall_clock_budget_seconds = 700` (engine hard stop, well under the 1200 s container kill), and
  `hole_reserve_seconds = 80` keeps the engine from starting a hole it cannot finish.
- **Bedrock sidecar rate limit** (30 requests/minute/episode): 2 seats × 1 call/hole, holes ≥ 25 s apart
  → ≤ 5 requests/minute even with every retry firing. The engine additionally floors the gap between
  two consecutive hole reveals at **4 s** (`min_hole_spacing_seconds`), so a pathologically fast episode
  (all-scripted seats) cannot burst the sidecar either.

---

## Decisions: LLM with scripted fallback

One image, one player entrypoint, env-switched — the pin, satisfied literally.

`/bin/cogolf-player` → `python -m players.main`, which chooses a policy at startup:

1. `PLAYER_SCRIPTED=<name>` set → the named scripted baseline (`literalist` or `pedant`). Any other
   value is a fatal startup error (exit 1) — a typo must not silently become an LLM seat.
2. else `PLAYER_PROMPT` set (or a provider is detectable: `AWS_BEARER_TOKEN_BEDROCK` /
   `AWS_ENDPOINT_URL_BEDROCK_RUNTIME` / `ANTHROPIC_API_KEY`) → the LLM policy, with `PLAYER_PROMPT`
   appended to the system preamble as the policy's strategy paragraph.
3. else → `literalist`. (So a credential-less CI or local run still plays a full, legal episode.)

### The LLM policy (`players/llm_player.py`, forked from the starter's)

- Provider detection, the Bedrock-sidecar HTTP client, the `with_options(timeout=…, max_retries=1)`
  wrapper and the "any API failure → safe move" discipline are the starter's, kept.
- **Model candidates change**: `["us.anthropic.claude-haiku-4-5-20251001-v1:0",
  "us.anthropic.claude-sonnet-4-5-20250929-v1:0"]`, haiku first.
  `us.anthropic.claude-sonnet-4-6` is **removed** from the candidate list (it times out on every sidecar
  call — cogame-raid, 2026-08-23).
- `max_tokens = 1800` (an impl of ~60 lines plus five test records; 400/900 truncate mid-function),
  `COGAME_LLM_TIMEOUT` default `32` s so a call cannot outlive the 40 s hole deadline.
- **System prompt** (fixed preamble; `PLAYER_PROMPT` is appended as a final paragraph):

  > You are one of two code agents playing cogolf, a nine-hole adversarial-programming match.
  > Each hole you get one deliberately ambiguous spec. You must reply with ONE implementation of
  > `solve(...)` and up to 5 test cases. Your tests are fired at your opponent's implementation; their
  > tests are fired at yours. A hidden reference implementation decides every ambiguous clause: a test of
  > yours only counts if the reference agrees with it, and a hidden 4-case audit runs against your code
  > every hole. You score `(your breaching tests + their audit failures) − (their breaching tests + your
  > audit failures)`. So: implement the reading a careful author most likely meant, and aim your tests at
  > the clauses where a careless reader would diverge from that reading.
  > REPLY FORMAT — your reply MUST BEGIN WITH `{` and be a single JSON object:
  > `{"impl": "def solve(...):\n    ...", "tests": [{"name": "...", "args": [...], "expect": ..., "why": "..."}], "note": "..."}`.
  > `impl` is Python source (stdlib only, no imports of socket/subprocess/ctypes/multiprocessing, no file
  > or network access, no infinite loops — each call gets 1 second of CPU). `args` is the argument LIST
  > for one `solve(*args)` call and `expect` is the exact JSON value it must return. `why` is one short
  > sentence naming the clause you are testing. Emit no prose outside the JSON object.
- **Reply parsing is lenient; the wire is strict.** The player harness tries, in order: (a) `json.loads`
  of the whole reply; (b) `json.loads` of the first `{...}` balanced span (this accepts trailing prose);
  (c) the fenced-block fallback — the first ```python block becomes `impl` and the first ```json block is
  parsed for `tests`/`note`. Only after that does the harness build the strict
  `{"type": "submission", ...}` wire message. If none of the three yields an `impl` string, the harness
  sends the **scripted `literalist` submission for this hole** rather than nothing, and logs
  `llm_player: falling back (unparseable reply)` — so a parse failure costs a weak move, never a noop.
- Prompt bounds: the observation is rendered to ≤ 6000 chars (spec prompt verbatim; history compacted to
  the last 4 holes, each ≤ 1200 chars); the `api_docs` reference block (≈ 6 KB, the submission schema and
  one worked example) is sent as a `cache_control: ephemeral` system block, with the starter's
  retry-without-caching path kept.

### The scripted baselines (`server/cogame_cogolf/baseline.py`, shared by the player and the engine)

Both are pure functions `baseline(spec, hole) -> submission dict`; the module imports only the spec deck
and the stdlib, so the engine can call it for the degrade path and `players/main.py` can call it as a
policy. Algorithms:

- **`literalist`** — the reference-aligned reader. `impl = spec.LITERAL_IMPL` (a plain implementation
  that follows the prompt's *text* and matches the reference on all but one clause per spec — the spec
  author picks which). `tests = spec.SAFE_TESTS[:max_tests_per_hole]`, which are reference-consistent by
  construction, so every shot is legal. `note = "playing the text as written"`. Deterministic: same spec →
  same submission.
- **`pedant`** — the edge-case sniper. `impl = spec.NAIVE_IMPL` (correct on the common path, divergent
  from the reference on a *different* clause than `LITERAL_IMPL`, so the two baselines break each other).
  `tests = spec.EDGE_TESTS[:max_tests_per_hole]` — aggressive boundary shots, some of which the reference
  rejects; those come back illegal, which is exactly the lesson the baseline exists to demonstrate.
  `note = "aiming at the edges"`.
- Unknown spec key (a deck extended without updating a baseline): `impl` is a stub returning the first
  example's `expect` for matching args and `None` otherwise, `tests` are the spec's two `EXAMPLES`. Always
  bounded, always schema-valid.

### Degrade-never-hang

| failure | what happens |
|---|---|
| no reply by `hole_deadline_seconds` | one retry at `retry_deadline_seconds`, then the `literalist` fallback submission; cause `timeout` |
| reply is not JSON / wrong `type` / wrong `hole` / `impl` not a string | same: retry once, then fallback; cause `malformed` (a reply for another hole is dropped and counted, and the hole keeps waiting until its deadline) |
| message > 16 KB or `impl` > 4000 chars | same: retry once, then fallback; cause `oversize` |
| seat never connects (`player_connect_timeout_seconds`, default 90) | play continues with the fallback every hole; cause `disconnected`; one `COGAME_PLAYER_FAILURE_URI` report for the lowest such slot |
| the LLM API errors / refuses / returns unparseable text | the *player* substitutes the `literalist` submission (no wire noop at all) |
| a submitted impl loops forever / allocates / imports a blocked module | the sandbox kills it: per-call CPU cap 1.0 s, per-batch wall cap 6 s, `RLIMIT_AS` 256 MB; the affected calls become `breach`es for the defender |
| the sandbox subprocess dies mid-batch | results that arrived as NDJSON lines are kept; missing calls are recorded `timeout` (a breach for the defender) |
| wall budget expires | the episode settles early with `reason = "deadline"` and the scores of the last fully resolved hole |

`done` is broadcast **before** artifacts are written; results and replay are written independently with
errors aggregated; `/healthz` and `/global` keep answering for a **20 s** shutdown grace after the
artifacts are written before the process exits 0 (cogame-lantern 0.1.3 — the certification runner pings
`/global` after the player pods start).

---

## Sim module

`server/cogame_cogolf/` (fork of `server/cogame_factorio/`; `factorio.py` and `session.py` are deleted,
`sandbox.py`, `specs/`, `scoring.py` and `baseline.py` are new):

| file | role |
|---|---|
| `contract.py` | stdlib-only wire strings: `PROTOCOL = "cogame.cogolf.v1"`, message types, key tuples, caps, `FALLBACK_CAUSES`, `REASONS`, `ILLEGAL_REASONS`, `SHOT_OUTCOMES`. Golden copy in `tests/contract_manifest.txt` — the starter's four-surface rename rule (contract / manifest txt / `docs/PROTOCOL.md` / `players/`) is kept |
| `version.py` | `GAME_VERSION = "GV01"`, prepend-only changelog `GV01 (cogolf-v1): nine holes, zero-sum cross-fire scoring` |
| `config.py` | `GameConfig` ↔ manifest `config_schema` (fields below) |
| `specs/` | `__init__.py` (deck registry, `DECK_VERSION`, `load_deck(name)`) + twelve spec modules |
| `sandbox.py` | the code harness (below) |
| `scoring.py` | `hole_score()`, `match_scores()`, `killer_test()` — pure, no I/O |
| `baseline.py` | `literalist()`, `pedant()` (above) |
| `engine.py` | the hole loop of §The game, steps 1–11; all waits bounded |
| `replay.py` | the replay document writer |
| `results.py` | the closed results schema |
| `server.py` | aiohttp: `/healthz`, `/player`, `/global`, `/client/global`, `/client/player`, replay mode (`/replay-data`, `/client/replay/`) — the starter's file with the FLE startup path removed |
| `uris.py` | starter's, verbatim |

### `config_schema` fields (defaults in brackets)

`tokens` (injected), `players` (2 name objects), **`num_agents` [2]**, `deck` [`"core"`], `holes` [9,
1..12], `seed` [0 = mint one], `hole_deadline_seconds` [40], `retry_deadline_seconds` [15],
`max_tests_per_hole` [5, 1..5], `par_tests_per_hole` [4, fixed by the deck], `call_cpu_seconds` [1.0],
`sandbox_batch_seconds` [6], `hole_reserve_seconds` [80], `min_hole_spacing_seconds` [4],
`player_connect_timeout_seconds` [90], `wall_clock_budget_seconds` [700].
`additionalProperties: false`; `num_agents` is `{"type":"integer","minimum":2,"maximum":2,"default":2}` —
the schema itself refuses any other seat count.

### The sandbox (`sandbox.py`) — "like Factorio's code harness", but local

One **subprocess per (impl, hole)**, never a thread, never the server's own interpreter:

- Launch: `[sys.executable, "-I", "-S", "-m", "cogame_cogolf.sandbox_runner"]`, cwd = a fresh empty temp
  dir, `env` scrubbed to `{"PYTHONPATH": <server dir>, "PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8"}`,
  `stdin` = the job JSON, `stdout` = NDJSON results, `stderr` captured (≤ 2000 chars, kept for the log
  only).
- Job JSON: `{"source": "<impl>", "calls": [{"id": 3, "args": [...]}, ...], "cpu_seconds": 1.0}`.
- In the child, before the impl is touched: `resource.setrlimit` for `RLIMIT_AS` 256 MB, `RLIMIT_FSIZE`
  0 (any file write fails), `RLIMIT_NPROC` (no forks), `RLIMIT_NOFILE` 16; `sys.addaudithook` denying
  every event whose name starts with `socket.`, `subprocess.`, `os.exec`, `ctypes.`, `shutil.`,
  `urllib.`, plus `os.system`, `import` of `socket`/`ctypes`/`multiprocessing`/`threading`, and any
  `open` with a write mode; `os.setuid` to the image's unprivileged `cogolf` uid when the process starts
  as root.
- Per call: `signal.setitimer(ITIMER_VIRTUAL, cpu_seconds)` around `solve(*args)`; the handler raises
  `TimeoutError`. Each result is written and **flushed** as one NDJSON line
  `{"id":3,"ok":true,"value":<canon>}` or `{"id":3,"ok":false,"kind":"error|timeout|bad_value","text":"..."}`
  *before* the next call starts, so a batch that is killed at `sandbox_batch_seconds` still yields every
  result it had produced.
- The parent enforces `sandbox_batch_seconds` with `subprocess.run(timeout=...)` + `kill()`, and marks
  every id it never received as `{"ok": false, "kind": "timeout"}`.
- The reference implementation runs through the **same** runner (trusted source, `cpu_seconds` 2.0), so
  there is exactly one execution path and one equality function in the codebase.

This is defence in depth, not a claim of a hardened jail: the only code that ever reaches it comes from
the two policy containers of one ephemeral episode pod, and the episode is over in minutes.

### Replay document (`replay.py`) — the viewer's only input

UTF-8 JSON at `COGAME_SAVE_REPLAY_URI`, self-sufficient (names, aliases, config, seed, deck version, per
hole state, per-beat events, result — the viewer contacts nothing but S3 for this file):

```jsonc
{
  "format": "cogame-cogolf-replay",
  "version": 1,
  "game_version": "GV01",
  "config": { /* resolved GameConfig, tokens EXCLUDED */ },
  "seed": 1234567,
  "deck": "core", "deck_version": "core-1",
  "names":   ["daveey", "daveey-1"],     // real players — spectator side only
  "aliases": ["Ash", "Basil"],           // what the policies saw
  "holes": [
    {
      "hole": 1,
      "spec": {"key": "range_merge", "title": "Merge ranges", "prompt": "…",
               "signature": {…}, "examples": […], "ambiguity": "Ends are inclusive: [1,2] and [2,3] merge."},
      "seats": [
        {"slot": 0, "impl": "def solve(rs):\n    …", "impl_lines": 14, "broken": false,
         "note": "treating ends as inclusive", "fallback": null,
         "tests": [{"idx": 0, "name": "touching", "args": [[[1,2],[2,3]]], "expect": [[1,3]],
                    "why": "spec says ranges include both ends",
                    "legal": true, "legal_reason": null,
                    "outcome": "breach", "observed": "[[1, 2], [2, 3]]"}],
         "par_fails": 1, "par_total": 4},
        {"slot": 1, "…": "…"}
      ],
      "hole_score": [3, -3],
      "cumulative": [3, -3]
    }
  ],
  "events": [ /* the beat stream, below */ ],
  "result": { /* identical to COGAME_RESULTS_URI */ }
}
```

**Event vocabulary** (`events[]`, one array, chronological; the viewer's timeline unit is a **beat** and
every event is exactly one beat):

| `kind` | fields | drawn as |
|---|---|---|
| `hole_start` | `hole`, `spec_key`, `title`, `prompt_head` (≤ 160 chars) | the scroll unfurls; both fortresses rebuild to 9 bricks |
| `submission` | `hole`, `slot`, `impl_lines`, `impl_chars`, `test_count`, `note`, `fallback` | the seat's tee lights; a fallback tees up in grey with a `FALLBACK` chip |
| `test_verdict` | `hole`, `slot`, `target_slot`, `idx`, `name`, `args`, `expect`, `why`, `legal`, `legal_reason`, `outcome` (`breach`\|`held`\|`illegal`), `observed` | a dart flies tee→fortress: breach = brick crumbles + red flash; held = shield ping; illegal = the dart drops into the bunker with a sand splash |
| `par_result` | `hole`, `slot`, `par_fails`, `par_total` | 4 grey audit darts fall from the scroll onto the fortress |
| `hole_score` | `hole`, `score` `[s0,s1]`, `cumulative` `[c0,c1]` | the pin flags rise/fall; the hole banner flips |
| `episode_end` | `reason`, `scores`, `killer_test` | the endcard |

Sizes: a 9-hole match is ≈ 130 events and ≈ 120 KB of JSON. Everything is held in memory and written once
at the end, plus a best-effort partial replay on `harness_fault` (starter's discipline).

### Results document (`results.py`) — CLOSED schema, triple-synced

Keys (== manifest `results_schema` == `tools/ci/docker_smoke.sh` expectations; `tests/test_manifest.py`
is the tripwire): `names` (string[2]), `aliases` (string[2]), `scores` (number[2], zero-sum),
`hole_scores` (number[2][]), `breaches` (int[2]), `breaches_taken` (int[2]), `par_fails` (int[2]),
`tests_fired` (int[2]), `illegal_tests` (int[2]), `holes_played` (int), `fallbacks` (int[2]),
`fallback_causes` (object[2] with `timeout`/`malformed`/`oversize`/`disconnected`/`host_error`),
`reason` (enum `complete`\|`deadline`\|`harness_fault`), `wall_clock_seconds` (number), `seed` (int),
`deck_version` (str), `killer_test` (object\|null).

---

## Server, player, protocol

Protocol id **`cogame.cogolf.v1`**, documented in `docs/PROTOCOL.md` (fork of the starter's page).
Transport, routes, tokens, reconnect semantics and the runtime contract (`COGAME_CONFIG_URI`,
`COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_HOST`/`COGAME_PORT`,
`COGAME_LOAD_REPLAY_URI`) are the starter's, unchanged. `GET /client/global` and
`GET /client/player?slot=N&token=T` keep serving real token-checked pages, registered before any
catch-all static route, and neither opens a player socket (cogame-lantern 0.1.1).

### `welcome` (once per connection)

```json
{"type": "welcome", "protocol": "cogame.cogolf.v1", "game_version": "GV01",
 "slot": 0, "alias": "Ash", "opponent_alias": "Basil",
 "holes": 9, "hole_deadline_seconds": 40, "retry_deadline_seconds": 15,
 "rules": {"max_tests_per_hole": 5, "max_impl_chars": 4000, "max_test_name_chars": 40,
           "max_why_chars": 120, "max_args_chars": 400, "max_expect_chars": 400,
           "max_note_chars": 200, "max_message_bytes": 16384,
           "par_tests_per_hole": 4, "call_cpu_seconds": 1.0,
           "blocked": ["socket", "subprocess", "ctypes", "multiprocessing", "threading",
                       "file writes", "network"]},
 "episode": {"game_version": "GV01", "seats": 2, "slot": 0, "holes": 9, "deck": "core",
             "deck_version": "core-1", "seed": 1234567, "scoring": "zero_sum_v1"},
 "api_docs": "<how to write a submission: the JSON schema, the legality gate, the scoring formula, one worked example — ≈6 KB>"}
```

Every episode parameter is stated at t=0; a policy must never infer one from play (starter rule, kept).
`welcome` carries **no** real player name — only aliases.

### `observation` (one per hole; re-sent once with `retry: true` if the seat missed the deadline)

```json
{"type": "observation", "hole": 3, "deadline_seconds": 40, "retry": false,
 "observation": {
   "hole": 3, "holes": 9,
   "spec": {"key": "range_merge", "title": "Merge ranges", "prompt": "…verbatim, ≤1200 chars…",
            "signature": {"function": "solve",
                          "params": [{"name": "ranges", "type": "list[list[int]]"}],
                          "returns": "list[list[int]]"},
            "examples": [{"args": [[[1,3],[5,7]]], "expect": [[1,3],[5,7]]},
                         {"args": [[]], "expect": []}]},
   "you":      {"alias": "Ash",   "slot": 0, "score": 3},
   "opponent": {"alias": "Basil", "slot": 1, "score": -3},
   "history": [
     {"hole": 2, "spec_key": "median", "hole_score": 3,
      "your_tests":  [{"name": "even length", "args": [[1,2,3,4]], "expect": 2,
                       "legal": true, "legal_reason": null, "outcome": "breach"}],
      "their_tests": [{"name": "empty", "args": [[]], "expect": null, "why": "…",
                       "outcome": "held", "your_result": "null"}],
      "their_note": "aiming at the edges",
      "your_par_fails": 1, "their_par_fails": 2}
   ],
   "rules": { /* same object as welcome.rules */ }}}
```

**Visible to a seat:** the spec prompt, signature and two worked examples (identical for both seats); its
own alias, the opponent's alias, both cumulative scores; and, for the last **4** resolved holes: its own
tests with legality verdicts and reasons and outcomes, the opponent's tests **with args, expect and why**
(they were fired at you — you are entitled to see the shots that hit you) plus what your code returned,
the opponent's `note`, and both seats' par-fail **counts**.

**Hidden from a seat:** the opponent's implementation source; the reference implementation; the contents
of the par tests (only the counts are revealed); the ambiguity note; which specs later holes will use;
the opponent's real player name and policy; anything about other episodes. `history` is capped at 4
holes, each rendered ≤ 1200 chars, so the observation stays under ~8 KB.

### `submission` (the reply)

```json
{"type": "submission", "hole": 3,
 "impl": "def solve(ranges):\n    …",
 "tests": [{"name": "touching ends", "args": [[[1,2],[2,3]]], "expect": [[1,3]],
            "why": "spec says both ends are included"}],
 "note": "reading ends as inclusive"}
```

Caps, and what breaking each one costs:

| field | cap | over-cap behaviour |
|---|---|---|
| whole message | 16384 **bytes** | malformed → retry → fallback |
| `impl` | 4000 **characters** | malformed → retry → fallback (never truncated: truncated code is broken code, and a silent truncation would look like a bad implementation instead of a protocol error) |
| `tests` | 5 entries | entries past the 5th are **dropped** (recorded as `dropped_tests`) |
| `tests[].name` | 40 characters | **truncated** on rune boundaries, `…` appended |
| `tests[].why` | 120 characters | **truncated** on rune boundaries, `…` appended |
| `tests[].args` | 400 characters of compact JSON | that test is `illegal: oversize` |
| `tests[].expect` | 400 characters of compact JSON | that test is `illegal: oversize` |
| `note` | 200 characters | **truncated** on rune boundaries, `…` appended |
| `observed` (server-side) | 300 characters | **truncated** on rune boundaries |

**Every truncation is on rune (Unicode code point) boundaries, never bytes** — Python `str` slicing is
code-point based, so the rule is: decode once at the websocket edge, cap the `str`, and only then
re-encode. Additionally every string that lands in the replay is passed through
`s.encode("utf-8", "surrogatepass").decode("utf-8", "replace")`, replacing lone surrogates with
`U+FFFD`, and control characters other than `\n`/`\t` are stripped, so the replay always parses under a
strict UTF-8 JSON reader (the bullwhip byte-truncation bug, prevented by construction).

A reply whose `hole` is not the pending hole is dropped and counted (`wrong_hole`); the hole keeps
waiting until its deadline. A reply that arrives after the fallback has already been synthesised is
ignored.

### `done` and `/global`

`done` is `{"type": "done", "result": {…}}`, broadcast before artifacts are written; the server then
closes the socket and **the player process must exit 0**. The player harness (`players/client.py`,
forked) wraps its receive loop so a close frame or a truncated read exits 0 rather than raising
(cogame-raid 0.1.3 — the same latent bug shape).

`/global` is broadcast-only: an initial
`{"type":"status","game_version":"GV01","aliases":[…],"names":[…],"holes":9,"hole":0,"scores":[0,0],"done":false}`,
a `{"type":"progress","hole":k,"scores":[s0,s1],"killer":null}` after every resolved hole, and the final
`{"type":"done","result":{…}}`.

---

## Viewer

Static wasm bundle only — **`"replay_viewer": {"bundle": "static-replay-viewer"}`** in the manifest,
built by the `coworld build` hook **`tools/build_replay_viewer.sh`** (the starter's script with the image
tag and the expected-file list renamed to `cogolf_replay.{js,wasm,data}`). **Never a `/client/replay`
pod viewer.**

### All four viewer files come from ONE starter: `cogame-factorio`

| file | provenance |
|---|---|
| `replay-viewer/config.nims` | **cogame-factorio**, with the output name `cogolf_replay.js` and the `EXPORTED_FUNCTIONS` list renamed `_factorio_*` → `_cogolf_*`. The link flags stay factorio's: **no `MODULARIZE`, no `EXPORT_NAME`** |
| `replay-viewer/cogolf_replay.nim` (wasm entry) | **cogame-factorio** `replay-viewer/factorio_replay.nim`, forked: same Bitworld sprite-packet emission, same `{.exportc.}` surface renamed `cogolf_set_atlas` / `cogolf_load_replay` / `cogolf_frame` / `cogolf_input` / `cogolf_packet_ptr`/`_len` / `cogolf_error_ptr`/`_len` / `cogolf_stage_ptr`/`_len` / `cogolf_profile_ptr`/`_len`; the parser and scene builder are rewritten for the cogolf replay |
| `client/static_replay.js` + `client/static_replay_worker.js` | **cogame-factorio**, mechanically renamed (`FactorioStaticReplay` → `CogolfStaticReplay`, `Module._factorio_*` → `Module._cogolf_*`, `importScripts('./broadcast_core.js', './cogolf_replay.js')`). The bootstrap is untouched: `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts` — the **non-modularized** pairing that matches `config.nims` |
| `index.html` | **cogame-factorio** `client/replay_broadcast.html`, copied to `index.html` by `viewer/build_viewer.sh` (starter's script, file names renamed) |

**One starter for all four. No file is taken from ctf, babel or paintbot directly.** Splicing one
starter's shell onto another's emscripten link flags is what deadlocked cogame-lantern (2026-08-23);
here the link flags and the bootstrap ship as a matched pair from the same repo.

**Load signals.** `client/static_replay.js` sets
`document.documentElement.setAttribute('data-replay-loaded', 'true')` **on the first drawn frame** —
moved from the starter's worker `loaded` branch into the `firstFrame` branch, so the attribute means
"pixels were composited", not "bytes were parsed". `showFailure()` and the page's `showFailCard()` both
set `document.documentElement.setAttribute('data-replay-error', <message>)`. `tools/ci/viewer_smoke.mjs`
reads exactly those two attributes.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** from cogame-factorio (spoiler gate, name helpers
  `stripSeatSuffix`/`teamHeadline`/`setName`/`esc`, clock `fmt`, speed chips, `renderTransport`,
  `setMarkers`, `setVerdict`, drag/hover scrubbing). Not one line is edited; cogolf's beat semantics ride
  in through the existing `ctx` callbacks (`getState`/`seek`/`setPlaying`/`setSpeed`/`onSpoilers`).
- **`client/broadcast_core.js` is copied byte-for-byte** (the Bitworld sprite compositor).
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a rewrite
  that reuses the ids. Concretely: start from factorio's file; delete the elements listed below; append
  (a) a `<div id="scroll">` and a `<div id="feed">` inside `#stage` after `#tooltip`, (b) a
  `<section id="cogolf-plaque">` inside `#plaque-r`, (c) a second `<style id="cogolf-css">` block after
  the starter's `<style>` carrying only cogolf's additions. The boot state machine, fail card, no-data /
  stuck timers, `?hud=` handling, `ResizeObserver`, keyboard map and `ChromeCommon` wiring stay as they
  are, with `step` renamed to `beat` inside the existing functions.
- **Removed from the starter page, by id:** `#maptools` and its children `#tilepos`, `#zoom`, `#fit`,
  `#fitmap`, `#follow`; `#charmark` and `#charmark-lbl`; `#legend` and `#legend-cols`; the `f`/`g`/`c`
  key bindings and the `fitBase`/`fitMap`/`setFollow`/`focusCharacter`/`startCharGlide` functions that
  drove them; the `inventory` and `flows` plaque sections.
- **Zoom: dropped entirely.** The cogolf arena is a fixed 40 × 22-tile stage (two fortresses, two tees,
  one scroll) that always fits the frame, so there is no `#viewpanel`, no zoom bar and no minimap — the
  rule is "keep them only for boards larger than the frame", and this board never is.

### Transport rules

- A `relayout()` (added to the page, called on load and from a `ResizeObserver` on `#transport`) writes
  **`--band`** (the measured transport-band height in px) and **`--hudscale`** (the resolved `?hud=`
  multiplier) on **`:root`**. The starter's `--u`/`--hud` tokens stay; `--hudscale` is the resolved value
  other rules read.
- The transport band is the page's own CSS-grid row (`grid-template-rows: auto auto minmax(0,1fr) auto`,
  `#transport{grid-row:4}`), and **nothing is ever overlaid on it**: `#scroll`, `#feed`, `#tooltip`,
  `#status`, `#loader`, `#failcard` and `#endcard` all live inside `#stage` (grid row 3).
- **The endcard stops at `var(--band)`** — `#endcard{inset:0 0 var(--band) 0}` — and
  `hideEndCard()` is called from `seek()`, so **every** seek (click, drag, keyboard, beat button)
  dismisses it.
- **Scrubber beats are clickable, labelled `<button>` elements**, not decorative divs: each carries
  `aria-label` (e.g. `hole 4: breach by Ash — "empty list"`), `title`, and an on-click `seek(beat)`.
  CSS exists for **every kind emitted**: `.beat-marker.hole` (paper tick at each hole start),
  `.beat-marker.breach` (red), `.beat-marker.illegal` (ghost, short), `.beat-marker.fallback` (amber),
  `.beat-marker.killer` (bright amber, tall). The `.scrub-key` legend strip is relabelled to those five.

### What it draws (real art, no placeholders)

- **The arena**: a dusk links background, two stone **code-fortresses** (left = slot 0 / `Ash`, right =
  slot 1 / `Basil`), each 9 bricks (5 possible incoming shots + 4 audit darts) rebuilt at every
  `hole_start`; a tee in front of each; a pin flag on each keep whose height tracks the cumulative score.
- **The scroll**: a parchment banner across the top of the stage, drawn by the wasm renderer; the spec
  **title and prompt head** are an HTML overlay (`#scroll`) pinned over it so the text is crisp at any
  size.
- **Shots**: a dart arcs tee → opposing fortress over 700 ms at 1×. `held` → shield ring + ping;
  `breach` → the brick crumbles into debris with a red flash; `illegal` → the dart drops short into a
  sand bunker with a splash. Par audit darts fall grey from the scroll.
- **Art pipeline**: `viewer/tools/build_atlas.py` is **replaced** — the starter's Wube/FLE sprite cutter
  and `viewer/assets/README.md`'s Factorio provenance are deleted with it. The fork's script draws a
  deterministic 32-px atlas with Pillow (brick, cracked brick, debris, dart, shield ring, sand splash,
  parchment, pin flag, tee, grass and stone tiles, two seat pennants) and commits
  `viewer/assets/atlas.{png,json}` (< 200 KB). **No Factorio art is downloaded, committed or shipped.**
  Everything else the renderer needs is generated procedurally in Nim via the starter's `genSpriteId`.

### Readouts (all of them, and legible at 360 px)

- `#scorebug`: `COGOLF` wall name + `#gver` (`GV01`); `#clock` = `HOLE 3 / 9` with the caption = the
  spec title; `#stepro` = this hole's readout for the selected seat (`shots`, `breach`, `held`,
  `illegal`, `par ✗`); `#seatchips` = two chips, each `ASH` (alias, big) over `daveey` (real player
  name, small) with the cumulative score and this hole's ±delta.
- `#feed` (stage overlay, bottom-left): the last 4 beats as one line each —
  `H3 · Ash ▸ "touching ends" — BREACH (Basil returned [[1,2],[2,3]])`. This is the id
  `viewer_smoke.mjs` counts lines from.
- `#transport`: `#tick-clock` = `beat 42 / 126`, play/step/skip/end buttons, spoilers toggle, speed chips
  (0.5/1/2/4/8×), and the scrub track with the five beat kinds.
- `#plaque-r` (`#cogolf-plaque`): the spec prompt in full, the selected seat's `impl` source, and its
  test table (`name`, `args → expect`, verdict, `why`), plus `#result` at the end.
- **Legibility at 360 px** (the featured-match iframe width): `.plate-name{flex:1 1 auto; min-width:3.2em}`
  and every readout label hidden under `640px`, so names ellipsize instead of collapsing to "…"; the
  right plaque auto-collapses to its tab (`#main[data-right="0"]`) under `720px`, leaving the arena, the
  scorebug and the feed. **The scorebug is checked at 360 px, not at desktop width.**

### Replay bytes are self-sufficient

`names`, `aliases`, `config` (tokens excluded), `seed`, `deck`/`deck_version`, `game_version`, every
hole's spec text and both seats' submissions and verdicts, the full event stream and the result document
are all in the file. The viewer fetches nothing but the `.replay` URL (or `/replay-data` in the game
container's replay mode).

---

## Packaging

- **`compose.yaml`** — the starter's two services, kept, so the manifest placeholders derive from the
  compose service names (`game` → `{{GAME_IMAGE}}`, `player` → `{{PLAYER_IMAGE}}`):

  ```yaml
  services:
    game:   {image: cogame-cogolf-game:latest,   platform: linux/amd64,
             build: {context: ., dockerfile: Dockerfile, target: game,   network: host}}
    player: {image: cogame-cogolf-player:latest, platform: linux/amd64,
             build: {context: ., dockerfile: Dockerfile, target: player, network: host}}
  ```

- **`Dockerfile`** — three stages, forked from the starter with the Factorio/FLE half deleted:
  `wasm-builder` (emsdk 4.0.15 + nimby 0.1.27 + Nim 2.2.4 + `nimby --global sync nimby.lock` running
  `bash viewer/build_viewer.sh`); `player` (`python:3.11-slim` + `aiohttp` + `anthropic`/`boto3` + the
  stdlib-only `contract.py` — one player image, both policy modes, `CMD ["/bin/cogolf-player"]`);
  `game` (`python:3.11-slim` + `aiohttp` + `server/` + `players/` + the built `viewer/dist/`, an
  unprivileged `cogolf` uid for the sandbox, `CMD ["/bin/cogolf"]`). `/bin/cogolf` and
  `/bin/cogolf-player` are two-line shims for `python -m cogame_cogolf.server` and `python -m players.main`
  (this is what `tools/ci/docker_smoke.sh` and `tools/ci/policies.json` invoke).
- **`coworld_manifest_template.json`** — `$schema`, ≥ 3 tags (`code-agents`, `adversarial`,
  `testing`, `spec-interpretation`), `episode_timeout_minutes: 20`, `game.runnable.type: "game"`,
  `game.config_schema` a real JSON Schema, `variants[].description` on every variant,
  `"replay_viewer": {"bundle": "static-replay-viewer"}`, and top-level `player[]` entries with
  `id`/`type`/`name`/`description` (the `coworld` 0.1.42 upload contract).
  - `game.docs` = `{"readme": {"type":"uri", "value": ".../README.md"},
    "pages": [{"id":"rules.md","title":"Rules & submission contract", …docs/RULES.md},
    {"id":"replay.md","title":"Replay format", …docs/REPLAY.md}]}`.
  - `game.protocols` carries **both** `player` and `global`, each `{"type":"uri"}` pointing at
    `docs/PROTOCOL.md`.
  - **Two bundled players**, both scripted, so that every declared player entry can be seated in the
    certification fixture (cogame-raid 0.1.2 → 0.1.3): `literalist`
    (`run: ["/bin/cogolf-player"]`, `env: {"PLAYER_SCRIPTED": "literalist"}`) and `pedant`
    (`env: {"PLAYER_SCRIPTED": "pedant"}`).
  - **Variants — `num_agents` in every one:**

    | id | name | `num_agents` | config |
    |---|---|---|---|
    | `duel` | Nine holes (2 seats) | **2** | `holes: 9, deck: "core", hole_deadline_seconds: 40, retry_deadline_seconds: 15, max_tests_per_hole: 5, wall_clock_budget_seconds: 700` |
    | `blitz` | Five holes, fast (2 seats) | **2** | `holes: 5, deck: "core", hole_deadline_seconds: 30, retry_deadline_seconds: 12, max_tests_per_hole: 4, wall_clock_budget_seconds: 420` |

  - **Certification fixture — `num_agents: 2`**, and it pins every field its ending depends on:

    ```json
    "certification": {
      "players": [{"player_id": "literalist"}, {"player_id": "pedant"}],
      "game_config": {"players": [{"name": "Literalist"}, {"name": "Pedant"}],
                      "num_agents": 2, "deck": "core", "holes": 3, "seed": 7,
                      "hole_deadline_seconds": 20, "retry_deadline_seconds": 10,
                      "max_tests_per_hole": 5, "sandbox_batch_seconds": 6,
                      "player_connect_timeout_seconds": 90,
                      "wall_clock_budget_seconds": 240}}
    ```

    Three holes × ≈ 14 beats = ≈ 42 beats ≈ 29 s of playback at 1×, which outlasts any `--soak` window
    the viewer smoke uses (cogame-ecos, 2026-08-23).
- **`tools/ci/docker_smoke.sh`** — the coworld-builder template (it derives the seat count solely from
  `certification.game_config.num_agents`), with **`<SEATS>` = 2**, `<slug>` = `cogolf`,
  `<IMAGE>` = `cogame-cogolf`. `SMOKE_GAME_BIN=/bin/cogolf`, `SMOKE_PLAYER_BIN=/bin/cogolf-player`,
  `SMOKE_REQUIRE_REPLAY_JSON=1`. Committed mode 100755.
- **`tools/build_replay_viewer.sh`** — the starter's hook, expected-file list
  `index.html chrome_common.js replay_doc.js static_replay.js static_replay_worker.js broadcast_core.js
  cogolf_replay.js cogolf_replay.wasm cogolf_replay.data`, `mkdir -p` on the output parent before the
  containment check (cogame-ecos, 2026-08-23). Committed mode 100755.
- **`tools/ci/viewer_smoke.mjs`** — copied verbatim from coworld-builder `templates/tools/ci/`.
- **`tools/ci/policies.json`** — four policies, all one image, one entrypoint, env-switched:

  ```json
  [{"name":"cogolf-architect","run":"/bin/cogolf-player",
    "env":{"PLAYER_PROMPT":"Play for the reading a careful spec author most likely meant. Before you write code, name the one clause in the prompt that admits two readings and pick the reading that is consistent with BOTH worked examples; implement that reading defensively so no input raises. Spend your tests on the clause you picked: five small, clearly-legal cases that a reader of the other reading would get wrong."}},
   {"name":"cogolf-sniper","run":"/bin/cogolf-player",
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "env":{"PLAYER_PROMPT":"Play the boundaries. Enumerate the empty, single-element, tie, zero, negative and out-of-range inputs for this spec, decide what the reference must do with each from the prompt's exact words, and implement all of them without raising. Fire your five tests at the boundaries your opponent is most likely to have skipped, and use the history of which of your tests came back illegal to recalibrate what the reference actually does."}},
   {"name":"cogolf-literalist","run":"/bin/cogolf-player","env":{"PLAYER_SCRIPTED":"literalist"}},
   {"name":"cogolf-pedant","run":"/bin/cogolf-player","env":{"PLAYER_SCRIPTED":"pedant"}}]
  ```

  Champion #1 = `cogolf-architect` (daveey), champion #2 = `cogolf-sniper` (uploaded while
  `daveey-1` is the active player, hence the `player` field); fillers = the two scripted policies.
  **Both champions are `PLAYER_PROMPT`.**
- `.github/workflows/ci.yml` (coworld-builder template with `SLUG=cogolf`, `IMAGE=cogame-cogolf`;
  the `test` job runs `uv run pytest` instead of the Nim block, `docker-smoke` and `wasm-viewer` verbatim)
  and `coworld-release.yml` from `templates/`.

---

## Tests

Everything below runs in `ci.yml` (the sandbox has no docker, no Nim, no emsdk and no browser).

**Sim / unit (pytest, `tests/`)**

1. `test_specs.py` — for all twelve deck specs: `reference` passes its own `EXAMPLES` and all four
   `PAR_TESTS`; every `EXAMPLES`/`PAR_TESTS`/`SAFE_TESTS` args and expect are JSON round-trippable;
   `PROMPT` ≤ 1200 chars and `TITLE` ≤ 48; `AMBIGUITY` non-empty; keys unique; deck ≥ the default
   `holes`; `LITERAL_IMPL` and `NAIVE_IMPL` compile and define `solve`, and they diverge from the
   reference on **different** clauses (so the two baselines break each other).
2. `test_sandbox.py` — an infinite loop is killed at `call_cpu_seconds`; `import socket` and
   `subprocess.run` are denied by the audit hook; a file write fails (`RLIMIT_FSIZE`); a 1 GB allocation
   raises instead of OOM-killing the container; a syntax error yields `broken` with a reason; NDJSON
   results that arrived before a batch kill are kept and missing ids become `timeout`; `canon` equality
   (`1 == 1.0`, `True != 1`, dict order irrelevant, tuple → list, `NaN` rejected).
3. `test_scoring.py` — the hole formula; **`scores[0] + scores[1] == 0` over 1000 randomised outcome
   matrices**; illegal tests score zero; `killer_test` selection and its tie-breaks; a draw yields
   `killer_test: null`.
4. `test_submission.py` — schema validation and the cap table: over-cap `impl` → `malformed`; a 6th test
   dropped; `name`/`why`/`note` truncated **on rune boundaries** (a 4-byte emoji sitting on the cap is
   not split, and the result re-encodes as strict UTF-8); a lone surrogate becomes `U+FFFD`; over-cap
   `args`/`expect` → `illegal: oversize`; wrong `hole` → counted and dropped, not fatal.
5. `test_engine.py` — one hole resolves in the numbered order; both observations go out **before** either
   reply is awaited (the parallel-batch assertion: a fake source records send timestamps); a missing
   reply produces exactly one retry and then the fallback; the wall guard ends the episode with
   `reason: "deadline"` and discards the in-flight hole; `harness_fault` still writes artifacts.
6. **`test_baselines.py` — the bounded-orders / legality assertion.** For every deck spec × every
   baseline (`literalist`, `pedant`) and for the unknown-key path: the submission validates against the
   wire schema; `impl` ≤ 4000 chars; ≤ `max_tests_per_hole` tests; every `args`/`expect` within its cap
   and JSON-representable; every call is bounded (no baseline submission ever hits the sandbox
   timeout). Additionally **every `literalist` test passes the reference legality gate** (its shots are
   legal by construction), and no baseline ever emits a duplicate test within a hole.
7. `test_results.py` + `test_manifest.py` — the closed-schema triple sync (`results.py` key set ==
   manifest `results_schema` == `docker_smoke.sh` expectations; the `reason` enum matches); **every
   variant and the certification fixture carry `num_agents: 2`, equal to `len(players)` and to
   `len(certification.players)`**; the manifest validates against the CLI's `validate_upload_manifest`
   shape (tags, `$schema`, `runnable.type`, `episode_timeout_minutes`, `variants[].description`,
   `game.docs`, both `game.protocols`).
8. `test_contract.py` — `contract.py` against the golden `tests/contract_manifest.txt` (the silent-failure
   tripwire the starter uses).
9. `test_server.py` — `/healthz`, `/client/global` and `/client/player?slot=&token=` all serve real pages
   without opening a player socket; a bad token is 403 and a duplicate live socket is 409; `/global` and
   `/healthz` still answer during the 20 s shutdown grace.
10. `test_players.py` — the env switch (`PLAYER_SCRIPTED` wins over `PLAYER_PROMPT`, an unknown baseline
    name exits 1, no env → `literalist`); the three LLM reply-parsing paths (strict JSON, JSON with
    trailing prose, fenced python + fenced json) and the unparseable → `literalist` substitution; the
    harness **exits 0** on `done` and on a dead socket.

**End-to-end**

11. `test_e2e.py` — an in-process episode, 2 scripted seats × 3 holes, writing `results.json` and a
    replay to a temp dir: `reason == "complete"`, `scores` zero-sum, `holes_played == 3`, both artifacts
    present, `replay["result"] == results`.
12. `test_replay.py` — **strict-UTF-8 replay parse**: `json.loads(replay_bytes.decode("utf-8"))` with no
    error handler, on a replay built from submissions containing emoji, CJK, a lone surrogate and a
    string sitting exactly on every cap; plus the structural contract — `names`, `aliases`, `config`,
    `seed`, `deck_version`, every hole's spec and both seats' data, and **at least one event of every
    kind** in the vocabulary.
13. `test_viewer.py` — the built bundle's file list, the page contract (reads `?replay=`, falls back to
    `/replay-data`, relative asset paths only, sets `data-replay-loaded`/`data-replay-error`, the removed
    starter ids are absent and the appended cogolf ids are present), the atlas manifest shape, and
    `tools/wasm_replay_smoke.cjs` loading the **exact emitted** wasm module under node against
    `tests/fixtures/sample_replay.json` (skipped without a wasm build unless
    `COGAME_REQUIRE_WASM_BUILD=1`, which CI sets).

**CI jobs**

14. `docker-smoke` — `tools/ci/docker_smoke.sh cogame-cogolf:ci`: the production image, one game
    container plus **2** player containers driven by the certification fixture, game exits 0, results and
    a UTF-8-JSON replay written, `SEAT-COUNT` cross-check against `<SEATS>=2`; the replay is uploaded as
    the `smoke-replay` artifact.
15. **`wasm-viewer` (viewer smoke — the bundle is EXECUTED, not merely built)** — `needs: docker-smoke`;
    builds the bundle with `./tools/build_replay_viewer.sh`, downloads the `smoke-replay` artifact, and
    runs `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json
    --timeout 90 --soak 12` under Playwright-pinned-1.55.0 chromium. It must report `loaded: true` via
    `data-replay-loaded`, the clock/tick/scorebug readouts must **advance** across the soak, and
    `viewer-smoke.{png,json}` are uploaded as evidence.

---

## Out of scope (v1)

- More than two seats (the schema pins `num_agents` to exactly 2), team play, and any non-zero-sum
  variant.
- Free-form test code: tests are `{args, expect}` records against `solve(*args)`, never arbitrary
  `assert` expressions or property-based generators.
- Multi-function / multi-file specs, non-JSON signatures (objects, generators, callbacks), and specs
  whose reference is nondeterministic.
- Languages other than Python for the submitted implementation.
- Mutation scoring, coverage scoring, code-golf length scoring, and any style/lint component — v1 scores
  only breaches and audit failures.
- Per-seat private specs, asymmetric specs, and specs generated at runtime by an LLM; the deck is a fixed
  twelve-module set drawn by a recorded seed.
- Negotiation, chat, or any channel between seats beyond the one-line `note` echoed in the next
  observation.
- Revealing the reference implementation or the par-test contents to a seat (only counts are revealed);
  no post-match "solution" message.
- Any Factorio/FLE inheritance: no external engine process, no RCON, no Wube art, no `map`/terrain block
  in the replay.
- Viewer zoom, minimap, `#viewpanel`, camera follow, and free panning — the arena is fixed and always
  fits the frame.
- A live `/client/replay` pod viewer, and any viewer data source other than the replay bytes.
