blocking: 0

# Phase-60 verdict — cogmud
Run: 2026-08-24-cogmud · Checklist: docs/SPEC.md §Definition of done (8 items)
Evidence file: runs/2026-08-24-cogmud/VERIFY.md (read after forming my own read of STATE, log.md, release-result.json, viewer-check/ and the live API)
Independent read written before reading the verifier's conclusions: yes — I re-fetched rounds, leaderboard, the round-4 replay, the round-4 hosted log, the replay-session route, and the viewer-check CI run myself, and viewed viewer-smoke.png myself.

## Adjudication of the retry / re-pin (checks 3, 4, 5)

**Legitimate and honestly documented.** The retry note is in VERIFY.md's header and in
log.md:61–65 (`60 verifier returned VERIFY.md: 7 TRUE, check 5 FALSE … retry check 3/4/5:
re-pin to round 4 … documented retry approach 'different round', attempt 1`). "Different
round" is an explicitly listed approach in `prompts/60-verify.md` §Retry budget. The
superseded round-3 evidence is preserved verbatim in Appendix A, **including the FALSE
verdict** (A.3) with its diagnosis and a fleet cross-check that honestly declines the
platform-wide excuse. At re-execution (05:47:46Z) round 4 genuinely was the latest completed
round — the pasted rounds listing shows round 5 `pending` — so the re-pin does not cherry-pick
a favourable round; it pins to the round the check's own `max_by` selector chooses. Nothing
was hidden: the one FALSE result of the whole verification is the most thoroughly documented
section in the file.

Checks 6/8 staying on the featured match `cogmud.r3.e1` is not a mismatch: SPEC item 6 is a
property of the page's featured match, and item 8 is dispatched "against the check-6 iframe
`src`" by the SPEC's own text. The pinning note explains this correctly.

## Per-item verdicts

### 1. ≥2 completed rounds after fillers set — **TRUE**
VERIFY.md pastes the full rounds listing (rounds 2, 3 completed; round 4 later; round 1
`failed` with its error verbatim, the documented pre-filler pattern) and the elevated
filler-policies read. My re-fetch now shows rounds 2–5 `completed`, 1 `failed`. Rounds 3
(created 05:17:28Z) and 4 (05:32:28Z) postdate the filler POST (log.md:51, 05:03:28Z) beyond
any doubt, and both replays' `Baseline (N)` seat renaming (pasted in A.2 and check 4) proves
the fillers were in force. ≥2 post-filler completed rounds holds even discounting round 2
entirely (see observation 1 below).

### 2. Both champions ranked, fillers absent/Baseline — **TRUE**
Full leaderboard body pasted: `daveey`/`cogmud-merchant:v1` rank 1 and
`daveey-1`/`cogmud-broker:v1` rank 2, `rounds_played: 2` each; fillers absent. My live
re-fetch: daveey rank 1 and daveey-1 rank 4, `rounds_played: 4` each; the two intervening
rows are outside players (`richard`, `relh`), not fillers; `cogmud-factor:v1` /
`cogmud-magpie:v1` still absent. Satisfied at write time and still at head.

### 3. Latest round's episode request completed with replay — **TRUE** (pinned round 4)
Rounds listing pasted proving round 4 is the latest completed (round 5 `pending`);
`ereq_2fc0e53e…` `status:"completed"` with non-null `replay_url`; full participants body
pasted naming `daveey` (pos 1) and `daveey-1` (pos 2), fillers `is_filler:true`. The two
outside entrants do not affect the requirement. Superseded round-3 run preserved in A.1.

### 4. Replay bytes valid and show the game — **TRUE** (pinned round 4)
I re-fetched the replay myself: 61086 bytes, strict `jq -e` parse OK, `protocol
"cogmud.replay.v1"`, `results.reason "complete"`, champion seats (1, 2) 0/28 scripted,
fillers 14/14 scripted — byte-identical to VERIFY.md's pasted counts. The adaptation of the
prompt's generic `.type=="decision"`/`.fallback` filters to cogmud's `kind:"act"`/`scripted`
schema is shown in both forms and is auditable. Protocol reconciled against the game source,
design note and viewer. Verbatim champion sentences pasted are non-trivial, free-form,
in-game-meaningful (commissions bought, delivered, price-talk). Satisfies the item fully.

### 5. Hosted game log clean — **TRUE** (pinned round 4)
I independently downloaded and decoded `ereq_2fc0e53e…/artifacts/logs` (122896 raw bytes,
matching): **0 hits** on `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected`; 56 `bedrock_sidecar_complete`, all `("true","200")`; 0 rate-limited;
`turn 14 of 14 at 161s`; `episode complete, shutting down`. All of VERIFY.md's claims
reproduce exactly. The round-3 FALSE (one local parser-caused `falling back` line) is kept in
A.3 with a correct refusal to claim the platform-wide exception. Clean at the pinned round.

### 6. Public page uses static replay path — **TRUE**
Empty raw-HTML iframe grep correctly treated as unknown per the prompt; sources used are
named (SSR `state.playlist[0]` for the featured match; `POST /coworlds/replays/session` for
the `src`). Featured match `cogmud.r3.e1` present with both champions in the matchup. I
re-ran the session POST myself and got the identical
`…/v2/coworlds/replays/static/cow_42773bd0…/sha256%3A83f70a…/index.html?replay=…` URL,
`ready:true`; `<cow_id>` = STATE.coworld.cow_id, `<sha>` = STATE.coworld.manifest_sha, no
`/client/replay` anywhere; `canonical:true` re-confirmed live.

### 7. Certification declared the static bundle — **TRUE**
Read from the committed `runs/2026-08-24-cogmud/release-result.json` (source stated, never
`/tmp`). I read the file myself: `.certify.replay_liveness` = `Replay liveness: skipped
(static replay bundle declared; /client/replay and /replay not required)`, `.certify.ok:true`,
`.canonical:true`, `.step_failed:null`, and the same string appears in `.certify.output_tail`.
The `manifest_sha` matches the `<sha>` in check 6's iframe src.

### 8. Viewer executed, then judged — **TRUE**
- Dispatch is real: I verified run 32693641402 via `gh` — `workflowName: viewer-check`,
  `createdAt 2026-08-24T05:28:07Z` (after the 05:28:04Z dispatch), `conclusion: success`.
- Evidence committed: `viewer-check/viewer-smoke.json` + `viewer-smoke.png` are in the run dir.
- Gate (a): `loaded: true` at 1833 ms via **both** signals — `data_replay_loaded:"true"` and
  bridge `["loading","ready"]`, `bridge_error: []`, `failure: null` — verbatim in the
  committed json.
- Gate (b): the three scrub clocks differ — `TURN 1 / 14 · WAITING ON 6` → `TURN 8 / 14 ·
  WAITING ON 6` → `FINAL · BASELINE (2) 1.85` — verbatim in the committed json.
- Gate (c): I viewed the png myself. It shows exactly what the judgment paragraph says: the
  COGMUD masthead with clock `FINAL · BASELINE (2) 1.85`, the six-seat scorebug strip, the
  town band `TURN 14/14 · 26 COIN IN PLAY · 7 COMMISSION UNITS FILLED · 2 ROBBERIES · 5
  DEALS`, the nine-room parchment map with keepers' stock/price stalls and named cog sprites,
  the endcard `Ratchet WALKED OUT RICHEST` over a COIN/PACK/POINTS/ROBBERIES/SCORE table
  whose six rows I checked against the replay `results` (all reconcile: e.g. Ratchet 4/14/32/
  0/1.85 = seat-3 coin 4, wealth 18−4, questPoints 32, score 1.85), the SCORE BY TURN
  momentum graph, the transport strip with coloured tick marks, `101 / 101`, and the eight
  beat buttons matching the top-salience events. Legible, shows the game, and carries the
  starter's chrome (transport strip, scrubber, scorebug, endcard, momentum graph) — not the
  gridlock rewrite failure mode.

## Non-blocking observations

1. **Check 1 overclaims round 2's ordering.** VERIFY.md says rounds 2 and 3 were "created
   after the fillers were registered", but round 2's `created_at` (05:02:27Z) precedes the
   batched log line recording the filler POST (05:03:28Z), and round 2's replay seat names
   are claimed ("pasted in Appendix A.2") but A.2 is round 3's replay — round 2's names are
   nowhere pasted. This does not change the item's verdict (rounds 3 and 4 alone satisfy
   "≥2 completed after fillers set", with pasted Baseline-renaming proof), but the sentence
   is stronger than its evidence.
2. **Viewer name-swap inconsistency** (clock says `BASELINE (2)` while endcard/scorebug/beats
   say `Ratchet` for the same seat) — confirmed in the png; correctly carried as a phase-30
   style legibility item, not an item-8 failure.
3. **Reply-parser strictness** (round-3 `EOF expected` → one champion fallback) — correctly
   marked FALSE at round 3, correctly not excused as platform-wide, and correctly carried
   forward as a LEARNINGS/fix item. Rounds 2 and 4 grep clean; my re-fetch of round 4
   confirms.

## Summary

| item | VERIFY.md evidence inline? | my re-check | verdict |
|---|---|---|---|
| 1 | yes (rounds body, filler read, error verbatim) | live: rounds 2–5 completed | TRUE |
| 2 | yes (full leaderboard body) | live: both champions ranked, fillers absent | TRUE |
| 3 | yes (rounds + ereq bodies, round 4) | — (bodies complete and self-consistent) | TRUE |
| 4 | yes (parses, counts, sentences) | re-fetched replay: identical | TRUE |
| 5 | yes (decoded grep, corroboration) | re-fetched log: 0 hits, 56× ok/200 | TRUE |
| 6 | yes (4 sources, src verbatim) | re-ran session POST: identical static URL | TRUE |
| 7 | yes (committed file, string verbatim) | read the file: string present | TRUE |
| 8 | yes (committed json+png, judgment) | gh run success; viewed png: reconciles | TRUE |

All eight items carry fetched evidence inline (command + output) that satisfies SPEC
§Definition of done. The one retry re-pinned checks 3/4/5 to a different completed round per
the documented budget, with the superseded FALSE evidence preserved verbatim. No blocking
items.

BLOCKING: 0
