blocking: 0

# Phase-60 verdict — fruit-market
Run: `2026-08-25-fruit-market`   Checklist: `prompts/60-verify.md` §The eight checks / `docs/SPEC.md` §Definition of done
Independent read: evidence files and live API were re-fetched **before** accepting any VERIFY.md
claim; VERIFY.md was read after the checklist, SPEC, STATE.json, release-result.json, and the
committed viewer-check artifacts. Judge re-fetches were made 2026-08-25 ~23:47Z with
`Authorization: Bearer $SOFTMAX_TOKEN` (value never printed) against
`https://softmax.com/api/observatory/v2`, handling both bare-array and `{entries:}` shapes.

## Per-check verdicts (all independently re-verified)

### 1. ≥2 completed rounds after fillers — TRUE, confirmed
Re-fetched `GET /rounds?league_id=league_758061e3-46cb-49db-aef0-a28fb10ba80e&limit=20` (bare
array). Completed set: round 3 `round_92b46dc0-bde6-43d4-8a1e-c981885a1b79` (completed
2026-08-25T23:36:00Z) and round 2 `round_fbba2cf3-68cc-4a67-9ea2-d5fc4f5a6e8e` (completed
23:22:57Z) → count **2**. Round 1 is `failed` with error `"Temporal RoundWorkflow failed before
settling the round."` — recorded verbatim in VERIFY.md as required, correctly excluded. (A round 4
`pending` has since appeared; it changes nothing.) Fillers-first: I re-fetched both completed
rounds' episode requests — round 2 (`ereq_174442dd-6b44-4879-85b8-85331b43747a`) seats 6
`is_filler:true` participants plus daveey/daveey-1, round 3 (`ereq_acad5282…`) likewise; a round
cannot seat unregistered fillers, so both are post-filler. VERIFY.md's reasoning holds.

### 2. Both champions ranked — TRUE, confirmed
Re-fetched `GET /divisions/div_794ae52e-812a-4ad9-be2f-b4da9ae25a7f/leaderboard` (bare list),
exactly two rows:
```
1  daveey    fruit-market-broker:v1   1030.5304984710244  2  2.0
2  daveey-1  fruit-market-ricardo:v1   969.4695015289755  2  0.0
```
Both champions present, each `rounds_played = 2 ≥ 1`; fillers **absent** (the permitted outcome).
Matches VERIFY.md to the digit.

### 3. Latest round's episode request — TRUE, confirmed
Re-fetched `GET /episode-requests/ereq_acad5282-4127-48b2-8377-43a4bb528db2`:
`status: "completed"`, `replay_url:
https://softmax-public.s3.amazonaws.com/replays/8bc52824-0664-410c-8caf-3abc9469e4e4.replay`,
participants seat 0 = `fruit-market-broker`/`daveey`, seat 1 = `fruit-market-ricardo`/`daveey-1`,
seats 2–7 `is_filler: true` (hauler ×4, homesteader ×2). Participant scores
`[30, 0, 52, 36, 33, 54, 135, 52]` — identical to VERIFY.md.

### 4. Replay bytes valid and show the game — TRUE, confirmed
Re-downloaded the replay from the URL above: **332 562 bytes**, byte-count identical to
VERIFY.md's; `jq -e` strict parse → `strict UTF-8 JSON: ok`. `protocol =
"fruit-market.replay.v1"` (corroborated against the repo: the string appears in
`src/fruit_market/replays.nim`, `tests/test_replay.nim`, and the design note);
`results.reason = "complete"`, `ending = "round_limit"`. Independent recount of order sources:
all seats → `llm: 24, scripted: 72`; **champion seats 0/1 → `llm: 24` only** — zero `fallback`,
zero `scripted`, zero `retry`; `[.events[]|select(.fallback==true)]|length` → 0. Champion `say`
lengths min 58 / max 80 over 24 orders — non-trivial. 11 `trade` events;
`results.scores = [30,0,52,36,33,54,135,52]`, `starving_ticks = [0,480,0,0,0,0,0,0]`. VERIFY.md's
note that the spec's literal `.type=="decision"` probe returns 0 under this protocol's `k`/`source`
field names is accurate (I got 0 too); its substitute queries are faithful equivalents.

### 5. Hosted log clean — TRUE, confirmed
Re-fetched `GET /episode-requests/ereq_acad5282…/artifacts/logs` with the elevated header:
52 442 raw bytes, decoded per byte-string repr (52 275 chars). Grep of
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected` on **both** the decoded
text and the raw body → **CLEAN** / zero matches. Log content is this episode's
(`variant=concentric-rivers seats=8 rounds=12`, 45 `fruit-market:` lines).

### 6. Static replay path + featured match — TRUE, confirmed
Re-fetched `https://softmax.com/fruit-market` (563 583 bytes): no raw `<iframe` in HTML
(client-rendered, as VERIFY.md recorded — it correctly did not log a false negative), featured
match code `fruit-market.r3.e1` present in the SSR payload, and **zero** occurrences of
`client/replay` anywhere in the page. Re-issued the page's own `POST /coworlds/replays/session`
call and got the identical `viewer_url`:
`…/v2/coworlds/replays/static/cow_4a33390e-40e5-4bfc-826a-d2987347d8a8/sha256%3A041ac84194867475b2adf8e02ac063e464e18fffc06935dda742a7676e1d3626/index.html?replay=<s3 url>&v=2`,
`ready: true`. Static route, correct cow_id, manifest sha matches STATE and release-result.json.
VERIFY.md declared which source it used, as the prompt requires.

### 7. Certification declared the static bundle — TRUE, confirmed
Read the committed `runs/2026-08-25-fruit-market/release-result.json` myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` — contains the required prefix. Same file also shows
`canonical: true`, `hosted_certification: "certified"`, 10/10 cert steps passed.

### 8. Viewer executed and judged — TRUE, confirmed
Re-fetched run **32911662736** via `gh run view -R Metta-AI/coworld-builder`:
`{"conclusion":"success","status":"completed","workflowName":"viewer-check","createdAt":"2026-08-25T23:38:22Z"}`
— matching VERIFY.md's dispatch instant. The committed `viewer-check/viewer-smoke.json`:
`loaded: true` (via `data_replay_loaded: "true"`), `ms: 5101`, `failure: null`, and its `url` is
byte-identical to the check-6 session `viewer_url`. Three scrub clocks all differ and move
forward: `ROUND 1 / 12 TICK 0 OF 719` → `ROUND 7 / 12 TICK 375 OF 719` → `FINAL MARKET CLOSED`.
Both TRUE-conditions hold.

**Judge's own read of `viewer-smoke.png`** (I viewed the image): it is the endcard at 100 % scrub
over a visible, dimmed tile-map board. Top scorebug: `APPLE FARMERS score 123` /
`BANANA FARMERS score 269` with fruit-chip inventory rows; centred `FINAL / MARKET CLOSED`. Roster
strip of all eight cogs with scores matching `results.scores` seat-for-seat (Gale 135 … Bram 0).
Endcard: `GALE WINS`, chip `ROUND LIMIT`, `winner Baseline (5) on 135 points`, two team panels,
and the summary line `Ash 30 · Bram 0 · Cedar 52 · Dune 36 · Elm 33 · Fern 54 · Gale 135 ·
Holt 52 — 11 trades · mean 1.50 apples per banana · 1 cog starved` — every number reconciles with
the replay JSON I fetched (11 trades, mean_rate_x100=150, seat 1 starving_ticks 480). Behind it:
labelled market stalls (WEST/NORTH/SOUTH/EAST awnings), named cogs, fruit-glyph offer bubbles
(e.g. `3🍎→2🍌`, `6🍎→4🍌`), and an order-book panel on the right (`BRAM 6🍎→4🍌 south`,
`ASH 3🍌→2🍎 west`, …). Bottom: the starter's transport strip (restart / step / play / +5s / loop /
ffwd, `spoilers` toggle, `BANANA WINS`, `719 / 719`, 1×–16× speed rail) over a scrubber with tick
markers and the `APPLES PER BANANA` momentum graph. This **is** the starter's chrome, not a
gridlock-style rewrite. Legible, advancing, and it shows who won and why. The spectator-judgment
paragraph in VERIFY.md is an accurate description of this image — nothing in it overstates the
evidence.

## The verifier's three observations — judged, none rises to a done-failure

1. **`feed_lines: 0` (champion `say` strings not surfaced on screen).** Check 8's TRUE-conditions
   are `loaded: true` + differing clocks + the judgment paragraph; a feed count is a readout to
   paste, not a gate. The screenshot carries the same information graphically (offer bubbles,
   order book, scorebug). Legibility polish for a future phase-30, not blocking.
2. **Endcard labels `LIVES LEFT` / `K` / `D` / `CLSTR` / `CAP` inherited from coworld-ctf.**
   Confirmed in the png (all-zero columns). The failure mode SPEC names (cogame-gridlock) is a
   viewer that *doesn't* share the starter chrome; this is the starter chrome with two unmapped
   labels. Cosmetic; the winner, scores, and summary line are all correct and readable. Not a
   definition-of-done failure.
3. **Champion ricardo scores 0 in both rounds (starves at t=240, rests thereafter).** Check 2
   requires both champions ranked with `rounds_played ≥ 1` — holds at 2 each, score
   notwithstanding. Check 4 requires non-scripted, non-trivial champion decisions — seat 1's 12
   orders are all `source: "llm"` with 58–80-char barter reasoning (harvests, posts a 6-for-4
   offer at the south stall, then rests at 0 stamina — a legal response to its state). A weak
   strategy is a policy-quality issue, not a doneness failure under SPEC's eight checks. Worth
   the follow-up VERIFY.md suggests; not blocking.

## What I could not fully verify
- The built `dist/coworld_manifest.json` protocol field itself (built in CI, not committed); I
  corroborated `fruit-market.replay.v1` from the repo's source (`src/fruit_market/replays.nim`,
  `tests/test_replay.nim`, design note) and the manifest_sha in the static viewer URL matches
  STATE and release-result.json. I judge this sufficiently evidenced, not blocking.

## Summary
All eight checks re-verified TRUE at re-fetch time; VERIFY.md's evidence is accurate,
appropriately sourced, and in no case contradicted. Zero blocking findings.

BLOCKING: 0
