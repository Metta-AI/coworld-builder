blocking: 0

# Phase 60 verdict — continuous-control
Head: 9893ed8f2f475fed0af1fdd96a72275db5622203   Checklist: prompts/60-verify.md / docs/SPEC.md §Definition of done   Independent read written before reading VERIFY.md: yes

Judge session 2026-09-03T19:44Z–19:55Z. I formed my own read of the checklist, the design note,
the committed evidence (`viewer-check/`, `release-result.json`) and live API state **before**
opening VERIFY.md, then audited VERIFY.md's claims against my own fetches. Live spot-checks were
run on checks 1, 2, 3, 4, 5, 6 and the check-8 CI run — more than the two the brief requires.
Note: the league has advanced since VERIFY.md was written (round 3 completed 2026-09-03T19:40:39Z,
seven new episodes); every check was re-verified **at the current head of the league state**, and
all eight still hold there.

## Line-item rulings on the eight checks

### 1. ≥2 completed rounds after fillers set — **CONFIRMED**
Live re-fetch (`GET /rounds?league_id=league_62a1e77b…`): now **3** completed rounds —
round 1 `round_26e98f6c…` (2026-09-03T19:10:37Z), round 2 `round_74324044…` (19:25:38Z),
round 3 `round_cce830d1…` (19:40:39Z), all `status: completed`, `error: null`, no
failed/discarded rounds. Fillers `trotter:v2 bd151d35` + `plodder:v2 ece2febe` were registered
2026-08-29T13:26:58Z (`log.md` phase-50 line), before round 1 existed. VERIFY.md's evidence
(2 rounds at 19:39Z) was correct when written and is stronger now.

### 2. Both champions ranked; fillers absent/Baseline — **CONFIRMED**
Live re-fetch (`GET /divisions/div_07b556f6…/leaderboard`, bare array): `daveey-1`
`continuous-control-throttle:v2` now **rank 1** (rounds_played 3, 15 wins), `daveey`
`continuous-control-gaitsmith:v2` **rank 6** (rounds_played 3), among 7 ranked players. No row
for trotter/plodder and no `policy_label` starting `Baseline`. VERIFY.md's rank-2/rank-7 snapshot
was the round-2 state; the check's requirements (both champions ranked, `rounds_played ≥ 1`,
fillers absent) hold at head.

### 3. Latest round's episode requests completed with replay — **CONFIRMED**
Live re-fetch at head: latest completed round is now round 3. `GET /rounds/round_cce830d1…/
episode-requests` → all **7** `completed`, every one with a non-null S3 `replay_url`. Champion
episodes present: `ereq_b60b1122…` (daveey, score 15.86) and `ereq_7a208d20…` (daveey-1, score
55.019). The flat `?round_id=` route 405s exactly as VERIFY.md and the playbook say (I reproduced
the 405). The single-seat reading — no one episode can name both champions at `num_agents: 1`, so
both champions' own episodes are fetched — is design-pinned (design.md §124: exactly one seat,
always) and is the same reading VERIFY.md applied to round 2. Sound.

### 4. Replay bytes valid and show the game — **CONFIRMED** (design-declared substitute, honestly applied)
I independently downloaded the **round-3** daveey replay (`88bd2a29….replay`) — a different
episode from the verifier's — and reproduced the whole chain. The raw bytes are the binary
`COWLDCCL` container (magic verified with `od`; `jq -e` fails on them, exit 5, exactly as
VERIFY.md candidly shows for its own replay). This is not a defect the verifier papered over:
design.md lines 1325–1352 (accepted at phase 10) pin the binary starter format and declare **the
phase-60 substitute for SPEC check 4** verbatim — `tools/replay_summary.py` → one strict-UTF-8
JSON object → strict parser. Executed on my replay: `strict UTF-8 JSON: ok`; `protocol
continuous-control/v1` (matches the manifest: `coworld_manifest_template.json` `protocols.player`
→ `docs/PROTOCOL.md` line 3 "Protocol name: **`continuous-control/v1`**" — I fetched both from
the repo); `reason complete`, `endRule ladderComplete`; 19 LLM orders, **0 fallbacks**, 4 distinct
gaits, 15 distinct cadences, `distanceTotal 30.223` (> 5), non-empty says. I also re-ran the
substitute on the verifier's own round-2 replay (`f546620f…`) and got **byte-identical results**
to VERIFY.md's paste: totalReturn 20.543, distanceTotal 36.344, uprightTicksTotal 113,
saturatedTicks 514, falls 2, finalTick 691, 20 LLM orders / 0 fallbacks / 19 says / 4 gaits /
14 cadences `[0,10,12,18,20,26,28,30,34,36,37,42,45,50]`. The verifier's numbers are exact.
The deviation from SPEC's literal "valid UTF-8 JSON" wording is declared in the accepted design
with precedent (knights-archers; the coworld-ctf starter lineage is binary by construction), the
substitute preserves the check's intent (valid bytes, protocol match, healthy end, non-scripted
non-fallback champion play), and VERIFY.md discloses the substitution rather than hiding it.
Not a refutation.

### 5. Hosted game log clean — **CONFIRMED**
Live re-fetch at head: `GET /episode-requests/ereq_b60b1122…/artifacts/logs` (elevated, round-3
daveey episode) grepped for `falling back|LLM provider is unavailable|cut off at max_tokens|
rejected` → **CLEAN**. VERIFY.md checked both round-2 champion logs (decoded from `b'…'` reprs
first — more rigorous than a raw grep) and pasted champion #1's full log: 20/20 LLM calls
`HTTP/1.1 200 OK`, episode `complete/ladderComplete`. No platform-outage exception needed.

### 6. Public page uses the static replay path — **CONFIRMED** (single-seat precedent correctly applied)
Reproduced all four sources live:
- Raw-HTML grep for `<iframe` → nothing, as the playbook's lighthouse finding predicts
  (client-rendered iframe; empty grep = unknown, not failure).
- `/coworlds` detail: `{"canonical":true,"replay_viewer":null,"featured_match":null}` —
  `featured_match: null` is platform-wide noise, per the playbook.
- SSR payload of `https://softmax.com/continuous-control`, extracted myself by brace-matching:
  `state.playlist` = `[]`, `state.pool.replays` = **7** (now the round-3 episodes — the pool
  tracks the latest round, i.e. it is alive, not stale), page text contains "No featured match
  yet" (1 occurrence).
- Session endpoint `POST /coworlds/replays/session` with the round-3 replay → `ready: true`,
  `viewer_url` = `…/v2/coworlds/replays/static/cow_39456c26…/sha256%3A5a975e9f…/index.html?v=2
  #replay=<s3 url>` — the static route in the post-2026-08-28 fragment form, sha =
  `STATE.coworld.manifest_sha`, **not** a `/client/replay` pod URL.
Cross-check reproduced: `softmax.com/sokoban` (single-seat) shows "No featured match yet";
`softmax.com/paintbot` (multi-seat) does not. The structural cause is real — a
`playlist[].matchup:{first,second}` needs two ranked players in one episode, impossible at
`num_agents: 1` — and the LEARNINGS §2026-08-28 nethack entry records exactly this reading
("pool non-empty + static route = TRUE", used for procgen, crafter, nethack). The check-6 wording
gap is the SPEC's, not this run's; the precedent is recorded and consistently applied. The named
cause for absence ("fewer than two ranked players") demonstrably does not apply — 7 players are
ranked.

### 7. Certification declared the static bundle — **CONFIRMED**
Read the committed `runs/2026-08-29-continuous-control/release-result.json` myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` — contains the required prefix verbatim. `certify.ok:
true`, all cert stages `[pass]` in `output_tail`. Correct source (committed copy, not `/tmp`).

### 8. Viewer executed and judged — **CONFIRMED**
CI fact-check: run **33797485426** on `Metta-AI/coworld-builder` / workflow `viewer-check`,
created 2026-09-03T19:37:05Z (after the 19:37:04Z dispatch), `status: completed`,
`conclusion: success` — fetched via `gh run view`, not accepted from the report. The committed
`viewer-check/viewer-smoke.json` matches VERIFY.md's paste byte-for-byte:
- **(a) loaded:** `{"loaded":true,"ms":3940}`, signals `data_replay_loaded:"true"`,
  `data_replay_error:null`, `failure: "no failure"`. Condition 1 holds.
- **(b) advances:** the three scrub readouts differ — 0 % `0.1 m · 1.13 m/s … STAGE 1/3 · HOPPER
  · TICK 8/468`; 50 % `18.1 m · 2.10 m/s STAGE 2/3 · CHEETAH · TICK 263/468`; 100 % `2.8 m ·
  0.00 m/s STAGE 3/3 · WALKER · TICK 51/468`. Three stages, three morphologies, three ticks.
  Condition 2 holds.
- **(c) judgment:** I viewed `viewer-smoke.png` myself. It is unmistakably this game and the
  starter's chrome: scorebug (`20.5 RETURN gaitsmith ALPHA`, three stage pips), centred clock
  plate, transport strip with rewind/pause/+5s/loop, `spoilers` toggle, `691 / 691` (=
  `results.finalTick`), 1×/2×/4×/8× speed buttons, scrubber with the RETURN momentum graph and
  fall/stage beat markers — the coworld-ctf lineage, not a gridlock-style rewrite. Reconciliation
  holds to the decimal: endcard table `-0.1/0.1, 34.0/16.6, 2.4/3.8` = the replay's
  `stageDistance/stageReturn` `[-0.07,33.983,2.431] / [0.11,16.605,3.828]`; `RETURN 20.5`,
  `SCORE 20.543`, `0 OF 3 LINED OUT, 2 FALLS`, red/green/red pips = `fell/ran/fell`; the 100 %
  clock's WALKER tick 51 = `stageTicksRun[2] = 51`. The endcard defects VERIFY.md reports are
  real and visible in the png (ruled on below), and the verifier reported them rather than
  hiding them. All three conditions of SPEC item 8 hold.

## Residue rulings (bar: SPEC §Definition of done, not perfection)

1. **Endcard per-stage table text-column collision** (`STAGE BODYRESUDISTANRETURN` header; outcome
   word overprinting the morphology name) — **NON-BLOCKING.** Verified in the png. Check 8(c)
   demands a legible picture that shows the game; the frame as a whole is legible — scorebug,
   clock, stage pips, numeric columns, headline return and score are all correct and readable,
   and the collided information (outcome per stage) is redundantly carried by the coloured pips
   and the numbers. A real phase-30-class legibility defect for a patch release; not a failure of
   any DoD item.
2. **Endcard subtitle wrong values** (`PAR 40000000 MISSED` — micro-points without the divisor;
   `0.0 m covered, 0 upright ticks, 0 saturated ticks` vs the replay's 36.344 m / 113 / 514) —
   **NON-BLOCKING, but the most material residue.** Verified: I re-derived the true totals from
   the replay myself and they match the verifier's contradiction claim exactly; `par: 40.0` and
   the hosted log's own `return 20542601 micro-points` line confirm the missing-divisor
   diagnosis. The claim the line makes that matters competitively — par missed — is true
   (20.543 < 40), and every scoring surface the DoD actually tests (scorebug, clock, stage
   table numerics, SCORE) is correct. One secondary stats line misreports; no DoD item turns on
   it. Should be first in line for a patch.
3. **`feed_lines: 0` at load; GAIT ORDER labels dimmed under the endcard scrim** —
   **NON-BLOCKING.** The load-time `feed_lines` undercount is a recorded platform-wide artefact
   of the smoke tool (LEARNINGS: judge the feed from the png), and the png shows a feed line
   (`FINAL — RETURN 20.5, 0 LINED OUT, 2 FALLS`) and the GAIT ORDER panel present with its bars.
   Dimming under an end-of-replay scrim at the 100 % frame is expected endcard behaviour; no DoD
   item requires the feed panel to survive the endcard undimmed.
4. **"No featured match yet" / empty playlist** — **NON-BLOCKING.** Structural at
   `num_agents: 1` (matchup needs two ranked players in one episode), recorded precedent applied
   for the third time (procgen, crafter, nethack), pool carries all 7 latest-round episodes, the
   session endpoint serves the static route with `ready: true`, and I reproduced the
   single-vs-multi-seat contrast live (sokoban yes / paintbot no). The check-6 substance — static
   path, never a pod URL — is proven.

## Refuted
None. Every claim in VERIFY.md that I re-tested reproduced exactly: the leaderboard and rounds
(advanced, but in the confirming direction), the 405 on the flat episode-requests route, the
binary magic and the substitute's outputs (byte-identical results object on the same replay),
CLEAN logs at head, the empty playlist / 7-deep pool / static session route, the committed
cert string, and the CI run id, timestamp and conclusion for the viewer check.

## Fixer/verifier report audit
| claim | verifier said | I verified | agrees |
|---|---|---|---|
| completed rounds | 2 (r1, r2), error null | 3 at head, all error null, all post-filler | yes |
| champions ranked | daveey-1 #2, daveey #7, rp=2 | daveey-1 #1, daveey #6, rp=3, no Baseline rows | yes |
| latest round ereqs | 7/7 completed w/ replay_url (r2) | 7/7 completed w/ replay_url (r3, at head) | yes |
| replay substitute | design-pinned, strict JSON ok, 20 llm / 0 fallback / 4 gaits / 14 cadences | identical on same replay; independent r3 replay also passes (19/0/4/15) | yes |
| manifest protocol | continuous-control/v1 via PROTOCOL.md | fetched manifest+PROTOCOL.md from repo, matches | yes |
| logs CLEAN | both champions, decoded | CLEAN at head (r3 daveey, raw grep) | yes |
| playlist/pool | playlist 0, pool 7, sokoban-vs-multi contrast | reproduced all three live | yes |
| session route | static, ready:true, sha=manifest_sha | reproduced live with r3 replay | yes |
| cert string | committed file, exact prefix | read committed file, exact prefix present | yes |
| viewer-check run | 33797485426, dispatched 19:37:04Z, green | gh run view: created 19:37:05Z, success | yes |
| viewer readouts | loaded:true, 3 differing clocks | committed json matches paste byte-for-byte; png viewed | yes |
| endcard defects | 2 defects, non-blocking residue | both visible in png; contradiction values re-derived | yes |

## Verdict
VERIFY.md is confirmed on all eight checks; its two documented deviations (the design-pinned
binary-replay substitute for check 4 and the single-seat pool reading for check 6) are both
declared, precedented, and verified rather than assumed. All four residue items are real, all
four are NON-BLOCKING against SPEC §Definition of done. The endcard subtitle (item 2) is the one
that should not survive the next patch release.

BLOCKING: 0
