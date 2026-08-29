blocking: 0

# r4 verdict — minigrid (phase 60, verification round 3 adjudication)
Head: coworld-builder 2dacc05 / cogame-minigrid 85a2f68 · Checklist: docs/SPEC.md §Definition of done (as commands: prompts/60-verify.md) · Independent read written before reading VERIFY.md: yes

Judged: `runs/2026-08-28-minigrid/VERIFY.md` (round 3, 2026-08-29T06:45Z, against 0.1.2 /
`cow_70e4993f`). I ran my own pass of all eight checks against the **live head** before opening
VERIFY.md, then re-fetched every load-bearing claim in it. Between the verifier's session and
mine the ladder produced **round 36** (completed 06:53:16Z), so several of my fetches land on a
newer "latest round" than VERIFY.md's round 35 — where that matters I verified **both**.

Exit criterion enforced: all eight checks TRUE and this verdict returns BLOCKING: 0. **Both hold.**

---

## Per-check adjudication

### 1. ≥2 completed rounds after the fillers were set — verifier: TRUE (14 qualifying). **I concur: TRUE.**

My fetch (`GET $BASE/rounds?league_id=$L&limit=200`, 2026-08-29 ~06:57Z): **36 rounds, all 36
`completed`, zero failed, zero discarded** (`error` null on every row). Qualifying rounds
(`round_number ≥ 22`, the v3 rollover) now number **15**. I re-fetched
`GET /leagues/$L/filler-policies` (elevated) myself:

```
{"policy_name":"minigrid-scout","version":3,"policy_version_id":"2b6d21f5-c38f-40f9-9b4b-940992d59558"}
{"policy_name":"minigrid-bumper","version":3,"policy_version_id":"8a3c9bde-be76-4b80-9001-40766483e943"}
```

— exactly `STATE.policies.filler_version_ids`, both v3, neither a champion uuid. `log.md:112`
records the v3 filler replacement at `2026-08-29T03:17:07Z`, before round 22 (completed
03:22:24Z). The verifier's "14 qualifying rounds" was correct at its timestamp; it is 15 now.
Refutation attempt failed.

### 2. Both champions ranked — verifier: TRUE. **I concur: TRUE.**

My fetch (`GET /divisions/$D/leaderboard`, bare list):

```
1  richard   co-gas-minigrid-subgoal-router-richard:v1  1135.50  34  45.0
2  daveey    minigrid-cartographer:v3                    982.63  36  36.0
3  daveey-1  minigrid-missionfirst:v3                    881.86  36  23.0
```

`daveey` and `daveey-1` both present on their v3 labels, `rounds_played` 36 ≥ 1; the two fillers
(`minigrid-scout`, `minigrid-bumper`) **absent** from the leaderboard — the stronger of the two
permitted conditions. `richard` at rank 1 is a genuine third-party entrant
(`ply_ded11f40`, `is_filler:false` in every episode I fetched), not a filler; a third-party
outranking the champions is not a condition of this check. Refutation attempt failed.

### 3. Latest round's episode request completed with a replay — verifier: TRUE (round 35). **I concur: TRUE (verified at round 36).**

At my head the latest completed round is **36** (`round_bb0fb9b3-…`). My fetch of its nested
episode request (`GET /rounds/$R/episode-requests` → `ereq_5d550ce7-c5b5-4a94-96df-a07681df1acc`):

```
status "completed", replay_url "…/replays/9e860912-de19-4f4a-b6ee-64aad04497aa.replay",
participants: pos0 minigrid-cartographer v3 daveey (is_filler:false),
              pos1 minigrid-missionfirst v3 daveey-1 (is_filler:false),
              pos2 co-gas-minigrid-subgoal-router-richard v1 richard (is_filler:false),
              pos3 minigrid-bumper v3 daveey (is_filler:true)
```

I also confirmed the verifier's flat-route substitution claim is legitimate: the playbook
(§9) records `GET /episode-requests?round_id=` → HTTP 405 since 2026-08-26; the nested route is
the documented working shape. Note: fillers are flagged `is_filler: true` with their real policy
name rather than renamed `Baseline (N)` — the platform's current participant shape; the
champions are named correctly and the filler is machine-identifiable, which is the substance of
the check. Refutation attempt failed.

### 4. Replay bytes valid and show the game — verifier: TRUE. **I concur: TRUE.**

The replay is the design-declared **binary `COWLDMGD`** container (design.md:1199), with
`tools/replay_summary.py` the declared phase-60 substitute for the raw-`jq` command
(design.md:1208–1222). I verified this at both replays:

- **Raw bytes, round 36** (`9e860912…`, 214 648 B): header `43 4f 57 4c 44 4d 47 44` =
  `COWLDMGD`, then format version, length-prefixed `minigrid`, length-prefixed gameVersion
  **`3`** — matching manifest `game.name` and the v2.1 addendum's GameVersion bump
  (`src/minigrid/sim_types.nim:22: GameVersion* = "3"`).
- **Summary, round 36** (repo @ 85a2f68): `jq -e .` strict parse ok; `protocol minigrid/v1`,
  `gameVersion "3"`, `reason "complete"`, `endRule allLanesComplete`; **84 LLM plans, 0 for
  seats 0/1 non-LLM**, `fallbackTurns [0,0,0,0]`, `retriedTurns [1,0,0,0]`; 28 `goto` verbs
  across the champion seats; non-trivial says (e.g. seat 1: *"get to the green goal square; not
  seen yet; sweeping east and south"*).
- **Summary, round 35** (`2e5030b6…`, 154 361 B — the exact replay VERIFY.md §4 used): my run
  reproduces the verifier's numbers **exactly**: `{llm:67, scripted:21}` plans,
  `fallbackTurns [0,0,0,0]`, `retriedTurns [0,0,0,0]`, `tasksSolved [1,1,1,4]`,
  `scores [105050,106050,107050,414090]`, `turnsPlayed 25`, max batch `latency_ms` **12 000**.

Champion seats do the thing the game is about: all their decisions are `source=="llm"`, none
fallback, with coordinates and mission language in the says. Refutation attempt failed.

The verifier's "honesty note" that `protocol` is a tool constant is accurate — see advisory A4;
I confirmed `tools/replay_summary.py:79` (`protocol = "minigrid/v1"`) and the two build gates it
cited (`tests/test_minigrid_replay.nim:178`, `.github/workflows/ci.yml:252`) at head 85a2f68.
This does not make the check false: the on-the-wire identity (header gameName + GameVersion) was
verified from the bytes, by the verifier and independently by me.

### 5. Hosted game log clean — verifier: TRUE, zero matches in all 14 qualifying rounds. **I concur: TRUE.**

This was round 2's FALSE and is the load-bearing check of this round, so I re-fetched
independently rather than trusting the table: `GET /episode-requests/<id>/artifacts/logs`
(elevated), decoded per-`b'…'`-repr with `ast.literal_eval` before grepping
(`falling back|LLM provider is unavailable|cut off at max_tokens|rejected`) for a **5-round
sample: rounds 22, 27, 31, 34 and 36** (36 postdates VERIFY.md):

```
round_d35995fe (r22) ereq_c17d03a3  hits: 0  CLEAN
round_a6a1509e (r27) ereq_413f8376  hits: 0  CLEAN
round_d6b0ded0 (r31) ereq_fbe20285  hits: 0  CLEAN
round_676b07e5 (r34) ereq_ec136116  hits: 0  CLEAN
round_bb0fb9b3 (r36) ereq_5d550ce7  hits: 0  CLEAN
```

Zero matches in every round I sampled, including one the verifier never saw. The mechanism
claim also holds: the shipped ladder is `attempt1Ms 18000 / retryMs 12000 / turnBudgetMs 30000`
(confirmed in `coworld_manifest_template.json` at 85a2f68), and the worst batch latency I
measured myself (12 000 ms in r35, via the replay) sits under it with real headroom, versus
0.1.1's 11 000 ms deadline it would have breached. The verifier's r25/r26
`attempt 1 failed, will retry (schema_error)` lines are consistent with the replays'
`retriedTurns` counters and are **not** matched by the check's pattern — by design
(AGENTS.md: attempt 1 says `will retry`; only a genuine second failure logs `falling back`),
and the grep phrase list is SPEC's, not the verifier's. No platform-wide exception was claimed
and none was needed. Refutation attempt failed.

### 6. Public page uses the static replay path — verifier: TRUE (SSR payload + session endpoint). **I concur: TRUE.**

My fetches: `https://softmax.com/minigrid` (772 774 B) — zero `<iframe` in raw HTML, as the
playbook predicts for the client-rendered page, and the SSR payload carries
`state.playlist[0]` = featured match `minigrid.r36.e1` on `cow_70e4993f…` / `0.1.2` with
`replayUrl …9e860912….replay` (the playlist has rolled forward from the verifier's r35 — same
coworld, same route). `POST $BASE/coworlds/replays/session` for that replay returned:

```
viewer_url ".../v2/coworlds/replays/static/cow_70e4993f-58ea-4678-8d19-ffa1866214b1/
  sha256%3Aefc95d48…763e97/index.html?v=2#replay=…9e860912….replay", ready: true
```

— the static route with the 0.1.2 manifest sha; the `?v=2#replay=` URL-encoded-fragment form is
the documented 2026-08-28 static shape (`playbooks/observatory-api.md:326`). No `/client/replay`
anywhere. `GET /coworlds` confirms `cow_70e4993f` `canonical: true`, `manifest_hash` equal to the
sha in the path. Refutation attempt failed.

### 7. Certification declared the static bundle — verifier: TRUE (committed artifact). **I concur: TRUE.**

From the committed copy:

```
$ jq -r '.certify.replay_liveness' runs/2026-08-28-minigrid/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

with `version 0.1.2`, `ok true`, `canonical true`, `hosted_smoke "passed"`, `cow_id` and
`manifest_sha` equal to STATE's. I re-ran the verifier's provenance check myself:
`gh run download 33230336307 -R Metta-AI/cogame-minigrid -n release-result` →
`md5 ae87a49ba6770cdc48a7bb20632ea79d` for **both** the artifact and the committed file —
byte-identical, exactly as VERIFY.md §7 claims. Refutation attempt failed.
(Note: `.hosted_certification` reads `"certifying"` — the artifact's snapshot value at write
time; the coworld is `canonical: true` on the live API today, so this is not evidence against
any of the eight checks.)

### 8. Spectator judgment, viewer executed — verifier: TRUE. **I concur: TRUE.**

- **Run fact checked, not accepted:** `gh run view 33239074400 -R Metta-AI/coworld-builder` →
  `{"conclusion":"success","status":"completed","createdAt":"2026-08-29T06:41:27Z",
  "workflowName":"viewer-check"}` — created 2 s after the logged dispatch, as VERIFY.md shows.
- **(a) loaded:** committed `viewer-check/viewer-smoke.json` (1 752 B): `loaded: true` at
  1 933 ms via `data_replay_loaded: "true"`; `data_replay_error` null, `failure` null,
  `loading_text` null, `console_tail` []. The `url` field is character-for-character the check-6
  session route for the r35 featured replay. (`bridge_ready` false is fine — the check accepts
  either signal, and the DOM attribute is present.)
- **(b) advances:** the three scrub clocks are pairwise distinct — `TURN 1/30 · PHASE 1/5 ·
  LAVAGAP TICK 2/720` → `TURN 13/30 · PHASE 3/5 · MULTIROOM TICK 290/720` → `TURN 25/30 ·
  PHASE 5/5 · BABYAI TICK 578/720`, with DELTA's solve counter 0 → 2 → 3.
- **(c) judgment paragraph:** present in VERIFY.md §8 and — having opened
  `viewer-smoke.png` (531 864 B) myself — accurate to the pixel evidence: a legible 2×2
  quad of identically-seeded boards (red/blue top borders, GAMMA/DELTA labelled below), mission
  ribbon `PHASE 5/5 · BABYAI / "go to the green ball"` matching `taskMissions[4]` in the replay,
  five-task pip stack, `DELTA · FACING WEST` POV inset, 20 feed lines, and coworld-ctf's
  transport strip: restart/step/play/`+5s`/loop controls, `spoilers` toggle, `578 / 579` frame
  readout, `1×…16×` speed selector, and the momentum-graph scrubber with four coloured traces.
  Starter chrome, not a rewrite. The paragraph's one data discrepancy (100 % clock shows
  pre-credit `DELTA 3` versus `results.tasksSolved [1,1,1,4]`) is disclosed and correctly
  attributed to the scrub landing on frame 578 of 579 (advisory A1), and I verified the
  reconciliation numbers (`turnsPlayed 25`, `finalTick/tickCount 578`) against my own
  replay-summary run of the same bytes.

The evidence is committed under `runs/2026-08-28-minigrid/viewer-check/` (git status clean).
Refutation attempt failed on all three limbs.

---

## Refuted verifier findings

**None.** Every claim I re-fetched reproduced: the round table, the leaderboard rows, the
episode-request shape, the round-35 replay summary (all twelve numbers), the log CLEANs, the
session viewer_url, the artifact md5, the CI run conclusion, and the readouts against the
committed json and png. I also attempted to *demote* each of the verifier's four self-declared
non-blocking findings into a blocking one and failed each time (see below).

## The four self-declared findings, adjudicated

- **A1 — endcard unreachable from the 100 % scrub position (lands on frame 578 of 579).**
  Real: the png's transport reads `578 / 579` and the 100 % clock shows pre-credit scores.
  **Not blocking.** Check 8's three conditions (loaded; three differing clock readouts; legible
  judgment showing the game) all hold; SPEC names an absent/odd scrubber behaviour "a legibility
  finding for phase 30, not a licence to skip the question", and the endcard demonstrably exists
  in the product (round 2's render captured it; nothing here rests on that render). Advisory.
- **A2 — ALPHA/BETA lanes lack text labels; header chips grouped by column; carrying banners
  alternate word order.** Confirmed from the png. Cosmetic legibility; the lanes remain
  identifiable by border colour + header chips, and the frame is legible. **Not blocking.**
- **A3 — champions' mean solves (1.00 / 0.79) below the scripted filler (1.57).** Confirmed from
  the replay summaries (r36: champions 0/0 solves, richard 1). Check 4 requires non-scripted,
  non-trivial champion decisions and not-all-fallbacks — all satisfied; check 2 requires the
  champions ranked — they are. Policy strength versus its own baseline is not one of the eight
  checks. **Not blocking.**
- **A4 — `replay_summary.py` hard-codes `protocol`.** Confirmed at `tools/replay_summary.py:79`.
  The container genuinely carries no `minigrid/v1` string (its identity is gameName +
  GameVersion, which the tool *does* parse from the header and which both the verifier and I
  checked against the raw bytes), and the constant is pinned by test and CI gates. The evidence
  path is honest as long as readers know the field's provenance — which VERIFY.md discloses.
  **Not blocking.**

## Additional advisory findings (mine, not the verifier's)

- **A5 — STATE.verify is stale relative to VERIFY.md round 3.** `STATE.json` still carries
  round-1 values `verify.rounds = [{n:15},{n:16},{n:17}]` and
  `verify.replay = …3fe6e480….replay`, while `verify.viewer_check_run` was already updated to
  `33239074400` (round 3's run). VERIFY.md's own "For STATE" block prescribes
  `[{33},{34},{35}]` / `…2e5030b6….replay`. Not one of the eight checks (it is phase-60
  §Writes bookkeeping), but the coordinator should apply the prescribed STATE update at the
  60→70 transition so the committed record matches the verification that actually stands.
- **A6 — participant "Baseline (N)" renaming absent from the episode-request shape.** Fillers
  appear under their real policy names with `is_filler: true` (and leaderboard-absent). This is
  the platform's current shape, not a defect of this run; noted so a future verifier does not
  read prompts/60-verify.md §3's `Baseline (N)` parenthetical as a hard requirement against it.

## Verifier report audit

| claim | verifier said | I verified | agrees |
|---|---|---|---|
| rounds all completed | 35/35, 14 qualifying | 36/36, 15 qualifying at my head | yes |
| live filler set | v3 pair, uuids = STATE | same two uuids fetched elevated | yes |
| leaderboard | daveey #2 / daveey-1 #3, fillers absent | same at head (scores moved with r36) | yes |
| latest-round ereq | r35 completed + replay_url | r36 completed + replay_url at head | yes |
| r35 replay summary | 67 llm / 0 fallbacks / scores 105050… | reproduced exactly from same bytes | yes |
| logs clean ×14 | 0 matches, 1 073×HTTP 200 | 0 matches in my 5-round sample incl. r36 | yes |
| flat GET 405 | substituted nested route | playbook §9 documents the 405 | yes |
| session viewer_url | static route, ready:true | same shape for r36 replay | yes |
| release-result md5 | ae87a49b… identical to artifact | re-downloaded, identical | yes |
| viewer-check run | 33239074400 success | gh run view: success | yes |
| scrub readouts | three distinct clocks | committed json matches verbatim | yes |
| png description | quad, chrome, 578/579, labels | opened png; matches, incl. the label gaps | yes |
| protocol constant | tool line 79 + 2 build gates | all three line-verified at 85a2f68 | yes |

## Checklist pass (independent)

| # | item | status | evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | TRUE | 36/36 completed, 0 failed; fillers set 03:17:07Z (log.md:112); rounds 22–36 after it |
| 2 | both champions ranked, fillers absent/Baseline | TRUE | leaderboard rows daveey #2 / daveey-1 #3, v3 labels, 36 rounds; fillers absent |
| 3 | latest round ereq completed + replay | TRUE | r36 `ereq_5d550ce7…` completed, replay_url `…9e860912….replay`, participants correct |
| 4 | replay valid, shows the game | TRUE | COWLDMGD header minigrid/gv3 (raw bytes); summary strict-JSON ok, reason complete, 0 fallback turns, champions all-LLM with gotos/says |
| 5 | hosted log clean | TRUE | 0 pattern hits in rounds 22/27/31/34/36 (decoded reprs), corroborating verifier's 14/14 |
| 6 | static replay path + featured match | TRUE | SSR playlist[0] = minigrid.r36.e1; session `viewer_url` static + `ready:true`; canonical cow matches sha |
| 7 | cert declared static bundle | TRUE | committed release-result.json line verbatim; md5-identical to run 33230336307 artifact |
| 8 | viewer executed + spectator judgment | TRUE | run 33239074400 success; loaded:true 1933 ms; 3 distinct clocks; accurate judgment paragraph; evidence committed |

**All eight checks TRUE at the current head. Zero blocking findings. Six advisories (A1–A6),
none of which makes any of the eight checks not-actually-true. The exit criterion of
prompts/60-verify.md — all eight TRUE and the judge returning BLOCKING: 0 — is met.**

BLOCKING: 0
