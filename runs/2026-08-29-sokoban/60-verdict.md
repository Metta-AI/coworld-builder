blocking: 0

# Phase-60 verdict — sokoban (judge, 2026-09-03)

Judged artifact: `runs/2026-08-29-sokoban/VERIFY.md` (written 2026-09-03, commit efc8209).
Checklist: `docs/SPEC.md` §Definition of done (items 1–8), procedure `prompts/60-verify.md`.
Coworld: `cow_71631422-adaa-43fd-b234-5f1aa8a08b43` v0.1.0, league `league_81761ec5…`,
division `div_e9cf6fb5…`.

Independent read written before reading VERIFY.md: **yes, with one declared caveat** — the brief
directed me to `log.md` for run history, and its 19:47Z lines contain the coordinator's one-line
summaries of the verifier's check verdicts. I read those before my evidence pass was complete.
Every number below was nonetheless re-derived from primary sources (live Observatory API, S3
replay bytes through my own fetch of `tools/replay_summary.py`, the committed viewer-check
artifacts, `gh` run records, the live page SSR payload and client bundle) before VERIFY.md
itself was opened.

**Note on head drift:** VERIFY.md was written when rounds 1–2 were the completed set. At my
verification time round 3 (`round_86a273e3`) has also completed. I verified at the current head;
everything the verifier asserted still holds there, and where round 3 changes a number I say so.

## Per-check table (independent verdicts)

| # | SPEC §Definition of done item | My verdict | Justification (independently fetched) |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** | Live `GET /rounds?league_id=`: 3 completed (r1 `round_dc0067cb`, r2 `round_df339820`, r3 `round_86a273e3`), 0 failed/discarded; fillers registered 2026-08-29T10:59:29Z (log.md) and confirmed live on `/leagues/$L/filler-policies` (`ddfec3df` pusher, `fc2ef667` nudger); all rounds created 2026-09-03 — five days after. |
| 2 | Both champions ranked; fillers absent/Baseline | **TRUE** | Live leaderboard: daveey rank 5 `sokoban-lookahead:v1` rounds_played=3; daveey-1 rank 6 `sokoban-orderfirst:v1` rounds_played=3; neither `sokoban-pusher:v1` nor `sokoban-nudger:v1` appears. (Ranks 4/6 with rp=2 at VERIFY time — drift from round 3, both readings satisfy the clause.) |
| 3 | Latest round's episode request completed with replay; participants correct | **TRUE** | Single-seat game (variant "Tier ladder (1 cog…)", `num_agents=1`) so one champion per episode — a legitimate reading, stated plainly in VERIFY. At current head (r3): daveey `ereq_1130276f` and daveey-1 `ereq_7edb532a` both `completed` with non-null S3 `replay_url`s and correct participant blocks (verified via `GET /episode-requests/<id>`); same held for r2 (`ereq_3abc05c3`, `ereq_29c9fae7`). The one failed ereq per round belongs to outsider docxology (`"player slot 0 never registered; the seat played the pusher baseline"` — quoted verbatim in VERIFY, reproduced by me). |
| 4 | Replay bytes valid, protocol matches, reason complete, champions doing the thing | **TRUE** | Binary `COWLDSOK` container is design-declared (design.md §Replay bytes, lines 1223–1246) with `tools/replay_summary.py` as the declared substitute. I fetched the tool from the repo and ran it myself on r2-daveey (`18ab1e45…`), r2-daveey-1 (`435d4b63…`), r1-daveey (`c6762631…`), r3-daveey (`efa968f5…`): strict JSON ok every time; `protocol sokoban/v1`; `reason complete / endRule ladderComplete`; LLM plans 53/53, 51/51, 47/47, 40/41 (1 fallback record, `fallbackTurns 0`); pushes 20/32/35/29. VERIFY's table matches my numbers exactly. On `levelsSolved`: see finding 4e below. |
| 5 | Hosted game log clean | **TRUE** | I fetched `/artifacts/logs` (elevated) for the champion ereqs of r2 **and** r3: zero lines matching `falling back\|LLM provider is unavailable\|cut off at max_tokens\|rejected` in all four → CLEAN. No platform exception needed. |
| 6 | Public page uses static replay path; featured match present | **TRUE** | Raw grep of `https://softmax.com/sokoban` finds no iframe (client-rendered — the playbook-documented state, not a failure). I reproduced the fallback the page's own JS uses: `POST /coworlds/replays/session` → `ready:true`, `viewer_url` = `…/v2/coworlds/replays/static/cow_71631422…/sha256%3A91df94…/index.html?v=2#replay=<s3>` — the static route in the documented fragment form, `<sha>` = STATE's manifest_sha; not a `/client/replay` pod URL. SSR payload: `playlist:[]`, `pool.replays` populated (6 entries at VERIFY time; round-3 replays now) → page state "NOW SHOWING" with the showcase (peak-score) replay featured. I verified VERIFY's client-bundle quotes verbatim in the live chunk `3eacjjdko9bjx.js` (`r.has(t.first.player_id)&&r.has(t.second.player_id)`; `case"showcase"…`; `["top-two","mine","showcase"]`). Featured match present; see finding 6c. |
| 7 | Certification declared the static bundle | **TRUE** | Committed `runs/2026-08-29-sokoban/release-result.json` (phase 40, release run 33248649858): `.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"` — read by me from the committed copy. |
| 8 | Viewer executed; loaded + advances + spectator judgment | **TRUE** | Primary run 33797533088 (conclusion `success`, verified via `gh`) was run against the exact check-6 iframe src (the featured replay `63f695d7…` — confirmed from the committed json's own `url` field). `viewer-smoke.json`: `loaded:true` via `data_replay_loaded:"true"`; three differing clock readouts (`SOLVED 0/6 · SCORE 0` → `SOLVED 2/6 · SCORE 3120229` → `SOLVED 3/6 · SCORE 6210286`); `failure: no failure`. The 100 % readout reconciles exactly against my own `replay_summary.py` run on `63f695d7…` (`levelsSolved 3, solvedWeight 6, score 6210286, finalTick 630`, seat genuinely named `pusher`/scripted — the outsider's policy is a baseline copy; the viewer is truthful, not mislabelling). `viewer-smoke.png` shows a legible Sokoban board — crates, green-outlined placed crates, goal diamonds, dead-square hatching, level chip, per-level outcome dots — inside the starter's chrome unchanged (transport strip, spoilers toggle, tick counter 630/630, 1×–8× chips, scrubber with beat marks and momentum graph): not a gridlock-style rewrite. Supporting champion run 33797255773 (`success`, `loaded:true`) advanced 0 %→50 % but its 100 % seek did not take (50 %==100 %) — disclosed honestly in VERIFY; the binding run satisfies clause (b) on its own. |

**No check was marked TRUE without fetched evidence inline.** Every VERIFY section pastes
command + output; the two declared exceptions (committed release-result.json for 7, committed
viewer-check artifacts for 8) are exactly the exceptions `prompts/60-verify.md` prescribes. Every
quantitative claim I sampled (replay summaries ×5, ereq participant blocks, logs ×4, session URL,
bundle code, gh run conclusions, release-result string) reproduced exactly.

## The five findings — blocking or not, against SPEC §Definition of done text

### 4e — champions miss the design note's `levelsSolved ≥ 1` bar in the latest round → **non-blocking**

Verified true as a fact: my own runs show daveey `levelsSolved 0` in r2 and r3, daveey-1 `0` in
r2; daveey `1` in r1 (score 1 130 137). The design note's substitute block (design.md:1236–1246)
does write `results.levelsSolved >= 1` into its "Require" list — so the verifier's exception-use
of the same design note deserved scrutiny. But the checklist is SPEC §Definition of done item 4,
and its clauses are: valid UTF-8 JSON, protocol match, `reason` complete (or design-acceptable
deadline), and "events show the champion seats *doing the thing the game is about* (LLM games:
non-scripted decisions with non-trivial content; not all fallbacks)". The design note enters
item 4 at exactly two points: the deadline exception and the binary-container substitute for the
strict-JSON/protocol/reason/events reads. The `levelsSolved ≥ 1` clause is the design author's
*additional* bar, not a SPEC clause, and SPEC's own parenthetical defines the events test for LLM
games — which passes decisively here: 53/53 LLM-sourced plans, zero fallbacks, 20 real pushes, 7
crates parked, substantive per-turn reasoning (`"Push box2 down to its target (8,7)…"`,
`"STUCK: Box0 at (3,2) has no safe push…"`). The champions are demonstrably playing Sokoban;
they are losing to scripted search (outsiders solved 2/6 and 3/6 the same round), which is a
policy-strength result. The bar was also met once in-run (r1 daveey), so it is not unreachable.
Correctly recorded as a finding; correctly not a definition-of-done failure. Worth acting on
before any "LLM vs search" announcement framing, as VERIFY itself says.

### 6c — featured match resolves via showcase to the peak-score replay (an outsider's) → **non-blocking**

SPEC item 6 requires two things: the iframe `src` is the static route (never `/client/replay`),
and "featured match present" — with the parenthetical "(absence = fewer than two ranked
players)". Both hold: the featured slot is populated (showcase mode over a non-empty
`pool.replays`; page chip "NOW SHOWING"; 7 ranked players), and the featured replay's viewer URL
is the static route (`ready:true`, manifest-sha path, fragment form) — the very URL check 8 then
executed and rendered. Nothing in SPEC item 6 requires the featured match to star the champions
or the top-two framing. The structurally-empty `playlist` is the platform page's top-two rule
(`isWatchableReplayEpisode` requires both rank-1 and rank-2 players in one episode — impossible
for a single-seat game; I verified the rule in the live bundle). That is a product/legibility
consequence of a single-seat design, properly a phase-30/coordinator note, not a DoD clause.

### 8-i — scrubber can swallow a seek issued mid-scan (champion run 50 %==100 %) → **non-blocking**

SPEC item 8(b) requires differing clock readouts on the check-6 iframe `src`; the binding
primary run (33797533088) produced three distinct readouts ending on the true final frame. The
supporting run's swallowed seek is disclosed, plausibly diagnosed (700 ms fixed wait vs a slow
box — 5 958 ms load vs 2 127 ms), and its own 0 %→50 % transition proves motion. A
seek-responsiveness/no-"seeking"-state issue is a legibility item of exactly the kind
`prompts/60-verify.md` routes to phase 30 ("an absent scrubber is a legibility finding for
phase 30"), not a DoD clause.

### 8-ii — `Unknown sprite protocol message type: 97/108/34` console warnings → **non-blocking**

No DoD clause speaks to console noise. Item 8's three clauses (loaded; advances; legible
judgment) all pass with the warnings present — the screenshot is fully drawn and reconciles
frame-for-frame with the replay record. A renderer skipping unknown message kinds is a real
polish item; it does not block.

### 8-iii — say/feed text canvas-painted, so `feed_lines`/`canvas_text` read 0 → **non-blocking**

The checklist anticipates instrument blindness and says to judge from the screenshot plus the
replay JSON when a DOM readout is absent — which VERIFY does (and I confirmed the champion-run
screenshot claim chain: turn-28 caption text is verbatim plan 28 of `18ab1e45…`). The narration
is on screen; the automated probe just cannot see it. Instrumentation/legibility note, no DoD
clause fails.

### (VERIFY finding 6, unnumbered) — `replay_summary.py` reports `tickCount` = byte length → **non-blocking**

Reproduced implicitly (I relied on `results.finalTick`, which is correct: 1044/630 etc.).
Cosmetic bug in a forensics tool; no DoD clause reads `tickCount`.

## Non-blocking observations (judge's own)

- VERIFY check 4's pasted jq output line contains keys (`budgetGuards`, `stops`) the shown
  command does not produce — a command/output paste mismatch from iteration. The numbers
  themselves reproduced exactly in my independent run; cosmetic, but paste discipline matters.
- At current head, r3-daveey's summary shows `fallbacks: 1` (an attempt-1 fallback *record*;
  `fallbackTurns: 0`, 40/41 plans LLM-sourced) — still comfortably "a small minority", no change
  to item 4.

## Verdict

All eight SPEC §Definition of done items independently re-derived **TRUE at the current head**.
The verifier's 8/8 all-true verdict is supported by its evidence, every sampled claim reproduced
from primary sources, and both self-flagged findings (4e, 6c) are correctly classified
non-blocking under the SPEC text. Zero blocking findings.

BLOCKING: 0
