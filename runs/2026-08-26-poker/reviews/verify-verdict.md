blocking: 0

# Phase 60 verdict — poker (verify adjudication)

Head of record: coworld `cow_08add75e-311a-46ba-9b5d-05888954986e` v0.1.0, league
`league_14d979bc-860c-4c64-a706-e867a2ac1ca5`, division `div_2c39ffc7-6856-4d5f-ad55-c19072cd23b6`.
Checklist: `docs/SPEC.md` §Definition of done (items 1–8) as operationalized by
`prompts/60-verify.md`. Independent read written before reading VERIFY.md: **yes** — I
re-read the SPEC and the phase-60 prompt, then examined the committed artifacts
(`STATE.json`, `release-result.json`, `viewer-check/viewer-smoke.{json,png}`) and ran my
own fetches before opening VERIFY.md. (I judged this repo's review round 1 earlier today;
this pass was made against the definition-of-done checklist afresh, not against my r1
notes.)

Adjudication: **VERIFY.md proves every line of the definition of done with fetched
evidence.** All eight checks TRUE. The rounds-1/2 anomaly is properly documented residue,
not a blocker (reasoning below).

## Spot-checks (independent re-fetches, all reproduced)

1. **Leaderboard** — `GET /divisions/div_2c39ffc7…/leaderboard` re-fetched live: exactly
   two rows, `daveey-1 / poker-exploiter:v1` rank 1 and `daveey / poker-scholar:v1` rank 2,
   both now `rounds_played: 4` (a 4th round completed since VERIFY.md was written — the
   ladder is still producing), fillers absent. Matches check 2's claim; the only deltas
   are the expected time-forward ones (rounds 3→4, scores drifted).
2. **Replay bytes** — re-fetched
   `replays/bb8f4285-d608-47ea-9ec2-717f52e89911.replay` (83 303 bytes): decodes as
   strict UTF-8, parses as JSON, `protocol: poker.replay.v1`, `results.reason: complete`,
   60/60 hands, `decisions: [66, 75]`, **`fallbacks: [0, 0]`, `forcedFolds: [0, 0]`**,
   `names: ["daveey","daveey-1"]`, 122 non-empty `say` events with contextual table talk
   ("you're too predictable with that check" / "fair point, can't connect with that").
   Champion seats demonstrably doing the thing the game is about; zero scripted decisions.
3. **Screenshot** — I viewed the committed `viewer-check/viewer-smoke.png` myself: dark
   arena, green felt, two cog sprites labelled `daveey` (red, stack 19, dealer chip) and
   `daveey-1` (blue, stack 21), a face-up K♠, `POKER` wordmark, clock
   `HAND 60 / 60 · MIRROR · ROUND 1 · POT 0 · ANTE 1`, `REPLAY` status, `« LOG` toggle,
   amber `KUHN` rung badge, two-plate scorebug with signed nets (−1 / +1) and pip strips,
   full-width scrubber with per-hand beat markers and counter `794 / 795` (= the replay's
   795 events). The verifier's description of the picture is accurate, and it is
   unambiguously the cosino/parley-lineage chrome, not a lookalike.
4. **Round-3 hosted log** — re-fetched
   `episode-requests/ereq_6c5ec646…/artifacts/logs` with the elevated header and decoded
   the byte-string reprs: **0** occurrences of each of `falling back`,
   `LLM provider is unavailable`, `cut off at max_tokens`, `rejected`; upstream histogram
   `142 × bedrock-runtime.us-east-1.amazonaws.com → 200`; banner shows
   `soft stop at 660s, hard stop at 672s` (the phase-30 B2 guards live in production).
5. **Static replay route** — re-ran `POST /coworlds/replays/session` for this cow +
   replay: `viewer_url` is
   `…/v2/coworlds/replays/static/cow_08add75e…/sha256%3A3f77538f…/index.html?replay=<s3>`,
   `ready: true`; the sha decodes to `STATE.coworld.manifest_sha` exactly; not a
   `/client/replay` pod URL.

## Per-check adjudication

| # | Check | Verdict | Notes |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | **TRUE** | VERIFY.md fetched 3 completed / 0 failed and — with above-required rigor — excluded round 1 (created 22 s *before* filler registration at 18:39:20Z), passing on rounds 2–3 alone. My re-fetch: 4 completed, 0 failed, all `error: null`. |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | Reproduced live (spot-check 1). `player_id`s match STATE and release-result. |
| 3 | Latest round's ereq completed with replay | **TRUE** | Nested route (flat route 405s — documented); `status: completed`, non-null `replay_url`, both champions seated `is_filler: false`. No `Baseline (N)` seats is correct, not a gap: `kuhn` is a 2-seat variant and the two champions fill the table. Scores sum to 1.0 per the design's scoring rule. |
| 4 | Replay valid, protocol matches, shows the game | **TRUE** | Reproduced byte-for-byte (spot-check 2). The verifier's adaptation of the generic `.type=="decision"` filter to this game's `kind` vocabulary is correct and disclosed (the literal command would return 0 and mislead). 95 distinct say lines vs the 11 canned baseline quips of rounds 1–2 is a sound scripted-vs-model discriminator. `reason: complete` — no design exception needed. |
| 5 | Hosted log clean | **TRUE** | Reproduced (spot-check 4): all four patterns 0, 142 × Bedrock 200, zero throttles. The byte-string-repr decode before grepping is the correct method (a raw line grep would still have found 0 here, so the result is robust either way). |
| 6 | Public page uses the static replay path | **TRUE** | Raw iframe grep empty (client-rendered page) — recorded as unknown, not a false negative, per the prompt. The verifier then used the SSR `state.playlist[0]` (featured match present, and it is the round-3 episode — `replayUrl` byte-identical to check 3) plus the replay-session API for the iframe `src`; source recorded. I reproduced the session call (spot-check 5): static route, matching cow_id and manifest_sha. Check 8's browser run loading that exact URL and drawing frames is end-to-end confirmation the route serves. |
| 7 | Certification declared the static bundle | **TRUE** | Read from the committed `release-result.json` myself: `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` — the required prefix verbatim; `certify.ok: true`, 10/10 transcript steps, `hosted_certification: certified`. |
| 8 | Viewer executed, then judged | **TRUE** | Run `33004894052` success; committed `viewer-smoke.json`: `loaded: true` via **both** `data-replay-loaded="true"` and bridge `ready`, `data_replay_error: null`, `failure: null`, first frame at 7 964 ms; the three clock readouts differ (HAND 1 → HAND 30 · MIRROR · SHOWDOWN · POT 4 → HAND 60); `canvas text: 816 drawn, 0 never inside, 0 ellipsized`. The `.url` field proves it rendered the round-3 replay (the superseded round-2 dispatch is disclosed, not hidden). The spectator-judgment paragraph is written from the rendered evidence, reconciles the 50 % readout against recorded hand 30 and the scorebug against `results.net: [-1, 1]`, identifies the chrome as cosino-lineage, and honestly logs two minor legibility observations (end-of-strip frame is not the endcard; `MIRROR` is jargon) — both cosmetic, neither a check condition. I verified the screenshot supports every claim in the paragraph (spot-check 3). |

## The anomaly — properly documented residue, not a blocker

Rounds 1–2 ran 100 % scripted (`fallbacks == decisions`) because the platform's LLM
sidecar was routed to `openrouter.ai` and got `402 Payment Required` on all 274 calls;
round 3 ran clean on Bedrock (142/142 → 200, zero fallbacks). My adjudication:

- **It does not touch any check's truth.** Checks 3–5 and 8 evaluate round 3, which is
  clean — no exception clause even needs invoking. Check 1 counts *completed* rounds
  (rounds 1–2 completed, none failed/discarded; and rounds 3 + now 4 satisfy the count
  even under a stricter champion-meaningful reading). Check 2 requires both champions
  ranked with `rounds_played ≥ 1` — satisfied on round 3 alone.
- **The verifier's handling is exemplary rather than evasive**: it explicitly declined
  the Bedrock-*capacity* exception (402 is billing/routing, not capacity), fetched the
  failing round's sidecar histogram as proof of cause, cross-checked two other LLM
  coworlds' sidecars healthy in overlapping windows (so the fault was not poker's
  manifest — all three declare the same env shape), and recorded the self-clearing
  timeline (19:03Z → 19:09Z).
- **The residue is on the record where it belongs**: the Elo-noise consequence
  (rounds 1–2 rated two scripted baselines against each other) is flagged for the
  coordinator, and it dilutes with every clean round — a 4th completed round already
  exists at my re-fetch. Meanwhile the outage inadvertently demonstrated the design's
  degrade-never-hang path in production: both outage episodes still completed with valid
  zero-sum replays.

One process note, not a defect: VERIFY.md's check-5 log fetch and check-6 SSR extraction
paste decoded/derived excerpts rather than the full raw bodies — inherent to 292 KB log
bodies and a 611 KB SSR page — but every derived number I re-computed from the live
sources matched exactly, so the excerpts are faithful.

## Conclusion

Every line of SPEC §Definition of done is proven with fetched (or, for check 8, executed)
evidence; five independent spot-checks reproduced the verifier's claims without
discrepancy; the single anomaly is platform-side, cleared, correctly classified outside
the capacity exception, and fully documented with cause, cross-checks and consequences.
Nothing blocks.

BLOCKING: 0
