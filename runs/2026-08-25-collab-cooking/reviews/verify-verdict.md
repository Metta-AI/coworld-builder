blocking: 0

# verify verdict — collab-cooking (phase 60, attempt 2)

Judge: fresh context (thread sthr_01NdwBhRdW2UWUeU7NkVPjeT via coordinator brief), 2026-08-25T~11:0xZ.
Checklist: `docs/SPEC.md` §Definition of done (phase 60, all fetched, never assumed) — the eight items.
VERIFY under judgment: `runs/2026-08-25-collab-cooking/VERIFY.md` (attempt 2, 10:45Z, verdict 8/8 TRUE).
Head facts: coworld v0.1.3 `cow_19938c0f-195a-45f8-95da-761f0ffe04cb`, manifest
`sha256:ae8627b0c7abde4a8807b3fff2e641a9f289512221ecd494de9c9753afeb3cf1`,
league `league_592e6ed0-3f01-4084-bb90-75ace0db0063`, division `div_027403b9-3208-43b8-b2e6-499bd18681e5`.
Reading order honored: SPEC checklist → VERIFY.md → committed viewer-check artifacts → STATE.json/log.md;
I re-fetched checks 1, 2, 3 and 6 from the live API myself, plus checks 4 and 5 (replay bytes and
hosted log) and the CI run conclusions for 7 and 8, before writing this. Not re-litigated per the
coordinator's brief: round 1 (filler race), rounds 2–7 (pre-fix `game_unhealthy`), the legitimacy of
external entrant `richard`.

**Result: all eight checks stand at the current head. Zero blocking findings. Every VERIFY.md
assertion I re-fetched reproduced; two snapshots have moved with time (leaderboard, featured match)
in ways that keep their checks true.**

---

## Check 1 — ≥2 rounds completed after fillers were set → TRUE (re-fetched)

Re-fetched `GET /rounds?league_id=league_592e6ed0…&limit=30` (shape `{"entries":[…]}` as VERIFY
says). VERIFY's ten-row table reproduces **verbatim** — same round ids, statuses, timestamps, and
round 1's exact error string `Temporal RoundWorkflow failed before settling the round.` One
evolution since: round 10 (`round_e75b7054`, `pending` in VERIFY) is now `completed`
(10:47:55Z), making **9 completed rounds**, all after the 08:42:05Z filler registration
(log.md:57). Re-fetched episode requests confirm the stricter reading VERIFY applied: post-fix
rounds with **completed episodes** = r8 (`ereq_35289237`), r9 (`ereq_876d0e7c`), and now also r10
(`ereq_1eb7057d`, completed, replay `e0b10331….replay`). ≥2 on either reading. **Stands.**

## Check 2 — both champions ranked, fillers absent/Baseline → TRUE (re-fetched; snapshot superseded but check holds)

Re-fetched `GET /divisions/div_027403b9…/leaderboard` (bare list, as VERIFY says). The board has
**moved since VERIFY's 10:38Z fetch** — round 10 produced the ladder's first decisive results:

```
1  richard   co-gas-collab-cooking-runner-richard:v1  Elo 1032  rounds 5  wins 2
2  daveey    collab-cooking-expo:v3                   Elo  984  rounds 9  wins 0
3  daveey-1  collab-cooking-linecook:v3               Elo  984  rounds 9  wins 0
```

This is **not** a contradiction of VERIFY.md: its snapshot (all three at 1000/0, daveey rank 1) was
accurate when taken, and the SPEC item requires only that *both champions are ranked* and *fillers
absent or labelled Baseline* — it does not require the champions to hold ranks 1–2. At the current
head `daveey` and `daveey-1` are both ranked (ranks 2–3, `rounds_played: 9`), and neither filler
(`collab-cooking-brigade`, `collab-cooking-passer`) appears as a row. VERIFY's side-claim "every
completed episode so far has been a draw" is now stale (richard has 2 episode wins from r10) but
was true of rounds 2–9. **Stands.**

## Check 3 — latest round's episode request completed with replay, participants named → TRUE (re-fetched)

Re-fetched `GET /episode-requests?round_id=round_8f0dfbaa…` and the detail
`GET /episode-requests/ereq_876d0e7c…`: `status: "completed"`, `replay_url:
https://softmax-public.s3.amazonaws.com/replays/d0c99032-68e2-478a-9007-84fdf727336b.replay`, and
the four participants **exactly** as VERIFY prints them — seat 0 `collab-cooking-expo` v3 /
`daveey` / `is_filler:false`, seat 1 `collab-cooking-linecook` v3 / `daveey-1` / `is_filler:false`,
seat 2 `richard`, seat 3 `collab-cooking-brigade` v3 / `is_filler:true`; scores
`[3.0, 3.0, 3.0, 3.03]`. I also fetched round 10's episode request (created after VERIFY was
written): `ereq_1eb7057d` `completed` with an S3 replay — so the check also holds against the
literally-latest round at my fetch time. **Stands.**

## Check 4 — replay bytes valid, show the game → TRUE (re-fetched the bytes)

I fetched the r9 replay myself: HTTP 200, **403849 bytes** (byte-identical size to VERIFY),
`jq -e` strict-parses it, `protocol: "collab-cooking.replay.v1"` — matching the design note's
declared envelope (design.md:815 area, verified), `results.reason: "complete"`, 900/900 ticks.
Reproduced VERIFY's analysis queries myself:

- plan census: `[{slot:0,total:12,llm:12},{slot:1,total:12,llm:12}]` — **24/24 champion plans
  `src:"llm"`, zero fallback-sourced plans** — matches VERIFY exactly;
- fallback census: `[{slot:0,n:6,causes:["transport"]},{slot:1,n:6,causes:["transport"]}]` — matches;
- serve events: `salad t167 / soup t239 / soup t690`, all `Cog-A` — matches;
- last two plans t862/t865 with the exact `say` strings VERIFY quotes — match verbatim;
- `results`: `dishes:3`, `cross_play:true`, `seat_kinds
  ["prompt","prompt","scripted:runner","scripted:brigade"]`, `delivered [0,0,0,3]`,
  `orders_expired 47`, `burned {pot:3,fryer:0}`, `names [daveey,daveey-1,richard,Baseline]` — all match.

SPEC's bar is "champion seats *doing the thing the game is about* — non-scripted decisions with
non-trivial content; not all fallbacks." The plans are all LLM-sourced, carry real coordination
content (station/recipe/handoff/yield_to plus `say` lines naming the partner and the missing
ingredient), and fallbacks are 12 of 36 plan-turns with a documented platform cause (check 5). The
champions playing *badly* (0 dishes delivered vs the scripted filler's 3) does not falsify any
definition-of-done line — no SPEC item requires champions to score, and the decisions are
demonstrably non-scripted and non-trivial. That is the balance/prompt-quality note the coordinator
already holds, correctly filed as non-blocking. **Stands.**

## Check 5 — hosted game log clean → TRUE, documented exception verified (re-fetched)

Re-fetched `GET /episode-requests/ereq_876d0e7c…/artifacts/logs` with the elevated header
(HTTP 200), decoded the `b'…'` container reprs the same way, grepped the four patterns myself:

```
falling back                  0
LLM provider is unavailable   0
cut off at max_tokens         0
rejected                      1
```

The single `rejected` hit is exactly the line VERIFY quotes, in exactly the context VERIFY quotes:
a pod-local (`127.0.0.1`) `WebSocket /player?slot=0&token=bad" 403` at startup, immediately
following a *valid* token=… 200 and immediately preceding the accepted `/global` connection — the
certification runner's negative auth probe, proof the token gate works, not an LLM degradation.
The precedent VERIFY cites (`runs/2026-08-24-commons-family/reviews/verify-verdict.md`) accepted
the identical line. I also reproduced the 429 analysis: exactly **24** `collab-cooking llm:` lines,
**24/24** `http 429 "Too many tokens per day"` — the platform daily-token cap, which VERIFY
cross-checked against two other live coworlds' logs from the same window (coins ×24 + its own
`falling back` lines; cooperative-hunting ×2 with the throttle named). That is precisely the
documented, cross-checked platform-wide cause the SPEC text allows. I could not re-fetch the coins/
cooperative-hunting logs' *historical* state, but VERIFY's quotes are specific (ereq ids, counts,
line numbers) and consistent with the 429s I did reproduce in this run's own log; the exception is
adequately evidenced. **Stands.**

## Check 6 — public page uses the static replay path → TRUE (re-fetched; featured match rotated, check holds)

Re-fetched `https://softmax.com/collab-cooking` (HTTP 200, 550185 bytes): no server-rendered
`<iframe src=` (as VERIFY and the playbook document — client-rendered), and the SSR
`state.playlist[0]` is **present** — now `collab_cooking.r10.e1` (finished 10:46:43Z,
`coworldId: cow_19938c0f…`, `coworldVersion: 0.1.3`, replay `e0b10331….replay`, matchup
first=richard / second=daveey). The featured match **rotated from r9 to r10** between VERIFY's
10:39Z fetch and mine — expected 15-minute-cadence behavior, not a discrepancy; a featured match
is present either way, from the canonical v0.1.3 coworld. Re-ran the page's session call
`POST /coworlds/replays/session` for the current featured replay:

```
viewer_url: https://api.observatory.softmax-research.net/v2/coworlds/replays/static/
  cow_19938c0f-195a-45f8-95da-761f0ffe04cb/sha256%3Aae8627b0…/index.html?replay=…&v=2
ready: true
```

Static route, correct cow_id, correct manifest sha (matches STATE and my `GET /coworlds` re-fetch:
v0.1.3 is the sole `canonical:true` entry). **Not** a `/client/replay` pod URL. **Stands.**

## Check 7 — certification declared the static bundle → TRUE (verified from the committed artifact)

Read `runs/2026-08-25-collab-cooking/release-result.json` from the tree (the SPEC-named source):
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` — contains the required prefix. `.ok: true`,
`.certify.ok: true`, `.version: "0.1.3"`, `.cow_id: cow_19938c0f…` — it is the v0.1.3 artifact, not
the stale v0.1.1. Release run `32834816635` on `Metta-AI/cogame-collab-cooking` ("Coworld
release"): `conclusion: success`, checked via gh, not accepted from the report. **Stands.**

## Check 8 — viewer executed + spectator judgment → TRUE (artifacts verified, PNG read independently)

- **(a) loaded:** `viewer-smoke.json` (committed): `loaded: true`, `ms: 2424`,
  `signals.data_replay_loaded: "true"`, `bridge: ["ready"]`, `bridge_error: []`, `failure: null`,
  and `.url` is the check-6 static route for the r9 replay verbatim. The producing run
  `32838395169` (viewer-check, created 10:40:30Z): `conclusion: success` — checked via gh. ✅
- **(b) advances:** three scrub readouts `TICK 2 OF 900 / TICK 468 OF 900 / TICK 900 OF 900` with
  live-order counts 1/3/0 — all three differ. ✅
- **(c) judgment:** present in VERIFY, and I read `viewer-smoke.png` myself before comparing. The
  PNG shows what VERIFY says it shows, in detail: the four-seat scorebug around the centred
  `TICK 900 OF 900 / 0 ORDERS LIVE` clock (Cog-B daveey chop 0 · Cog-C daveey-1 pot 0 · Cog-D
  richard carrying 0 · Cog-A Baseline carrying 3); the dish ticker `salad·Cog-A·t167 /
  soup·Cog-A·t239 / soup·Cog-A·t690` — matching the serve events I extracted from the replay
  bytes myself; the say band carrying the t862/t865 champion lines verbatim with the two scripted
  seats correctly greyed "no word yet"; the endcard `3 DISHES SERVED · THE WHOLE BRIGADE SHARES
  ONE SCORE · 47 tickets expired · 3 pots burned · 0 fryers burned` with the ranked list
  (Cog-A/Baseline 3, then the three 0s) — every number reconciling with `results` in the replay;
  the populated feed overlay (champion says + repeated "…ticket expires · nobody served it"); the
  full ctf-family transport strip (rewind/step/play/+5s/loop/ff, `spoilers`, `900 / 900`, speed
  chips 1×–16×) over the momentum scrubber. It renders, it advances, it is the starter chrome, and
  the game is legible: a casual spectator sees who served what and when, what the champions were
  saying, and what it cost. Evidence committed under `runs/<run>/viewer-check/`. ✅

**Stands.** My own spectator read agrees with the verifier's: the viewer is truthful and legible;
what it truthfully shows is champions who narrate a soup they never finish — a balance/prompt
finding for the coordinator, not a viewer defect.

---

## Discrepancies found (none blocking)

1. **Leaderboard snapshot superseded** (check 2): richard now rank 1, Elo 1032/2 wins; champions
   984/984 at ranks 2–3 with `rounds_played: 9`. VERIFY's 10:38Z snapshot was accurate then; the
   SPEC item ("both champions ranked") remains true now. Time-evolution, not contradiction.
2. **Featured match rotated r9 → r10** (check 6): still present, still canonical v0.1.3, still the
   static route (`ready: true` re-confirmed). The committed viewer-check executed the *then*-check-6
   src (r9) through the identical bundle (`cow_id`/`sha` unchanged; only `?replay=` differs) — the
   check was correctly evaluated against the head at verification time.

## Non-blocking observations (carried forward, not counted)

- The momentum scrubber's graph label reads **`LIVES LEAD`** in the PNG — ctf-starter vocabulary
  with no meaning in a cooking game. Cosmetic chrome nit for a future version.
- `feed_lines: 0` in viewer-smoke.json vs a visibly populated feed in the PNG — probe selector
  mismatch, as VERIFY documented (round-8 run returned 1); the PNG is the rendered evidence.
- The balance note stands as the verifier filed it: LLM champions 0 dishes vs scripted filler 3,
  47/50 tickets expired, 1434 blocked-move events. No definition-of-done line is falsified by it.
  Round 10 (richard's 2 wins) shows the ladder is no longer a pure draw machine.

## Audit of the verifier's report

| check | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | 8 completed rounds; post-fix completed episodes r8+r9 | re-fetched: table verbatim; now 9 completed, r10's episode also completed | yes |
| 2 | both champions ranked v3, rounds_played 8, no filler rows | re-fetched: still ranked (now ranks 2–3, rounds 9), no filler rows | yes (snapshot moved) |
| 3 | ereq_876d0e7c completed, S3 replay, participants correct | re-fetched detail: identical, field for field | yes |
| 4 | 403849 B strict JSON, complete 900/900, 24/24 llm plans, serve t167/t239/t690 | re-fetched bytes and re-ran the jq: identical | yes |
| 5 | 0/0/0 + one token=bad `rejected`; 24×429 platform cause | re-fetched log, re-decoded, re-grepped: identical counts, identical context | yes |
| 6 | SSR playlist[0] featured; session POST → static route ready:true | re-fetched both: featured present (r10 now), static route confirmed | yes (rotated) |
| 7 | committed release-result.json carries the liveness-skipped string | read the committed file + gh run 32834816635 success | yes |
| 8 | run 32838395169 success, loaded:true, 3 differing clocks, PNG reconciles | gh conclusion success; read json + png myself; reconciled against replay bytes I fetched | yes |

BLOCKING: 0
