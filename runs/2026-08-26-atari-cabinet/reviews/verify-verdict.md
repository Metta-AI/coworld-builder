blocking: 0

# Phase-60 verdict — atari-cabinet
Checklist: docs/SPEC.md §Definition of done (8 items) · Evidence under judgment:
runs/2026-08-26-atari-cabinet/VERIFY.md (verifier claims 8/8 TRUE) · Independent read
written before accepting any of the verifier's dispositions: yes (SPEC → 60-verify.md →
design.md §Replay bytes → viewer-check artifacts + release-result.json + STATE, then VERIFY.md,
then live re-fetches).

## Standing blocking findings

None. Every VERIFY claim I tested either reproduced live at adjudication time or is supported
by the committed artifact it cites.

## Blocking items

(none)

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1. ≥2 completed rounds after fillers | TRUE | Live re-fetch: rounds 1–3 all `completed`, `error: null` (round 4 now pending — ladder still producing). Rounds 2 (20:36:00Z) and 3 (20:51:01Z) are strictly after the filler POST on any reading of its 20:21:59Z batched log timestamp; the verifier correctly did **not** rest the check on round 1's sub-minute ordering. |
| 2. Both champions ranked, fillers absent | TRUE | Live re-fetch of `divisions/$D/leaderboard` (bare array): `1 daveey atari-cabinet-castellan:v4 rounds_played=3 wins=3.0`, `2 daveey-1 atari-cabinet-gunner:v4 rounds_played=3 wins=0.0`; only two rows, fillers absent. Matches VERIFY.md:196–198 verbatim. |
| 3. Latest round's ereq completed + replay | TRUE | Live re-fetch of `ereq_21bff821-d7a9-462b-b8a2-f858c79d6ab0`: `status: completed`, `replay_url` = the S3 URL in STATE.verify.replay; seats 0/1 are daveey/daveey-1 `is_filler:false`, seats 2/3 the two filler version ids `is_filler:true`. Fillers surface as raw policy names + `is_filler` flag rather than `Baseline (N)` — a deployment shape VERIFY.md:285–289 discloses; the Baseline display names are proven in the replay `names` array and the rendered scorebug (items 4, 8). Champions are named correctly, which is what the item requires. |
| 4. Replay bytes valid, shows the game | TRUE (via design-declared substitute) | I re-fetched the replay (200, 127 994 bytes, magic `COWLDCAB`), re-fetched `tools/replay_summary.py` from the released repo, and re-ran the decode myself: `strict UTF-8 JSON: ok`, `protocol atari-cabinet/v1`, `results.reason complete`, `endRule full_time`, **48 LLM stances / 0 fallbacks**, `llmTurns [24,24,0,0]`, `fallbackTurns [0,0,0,0]`, 4 distinct stance verbs, 48/48 distinct `say` strings, `saves` sum 121, `names ["daveey","daveey-1","Baseline","Baseline (2)"]` — identical to VERIFY.md:331–384. On the letter-vs-intent question see Ruling 2 below. |
| 5. Hosted game log clean | TRUE | I re-fetched `…/artifacts/logs` (elevated, 200, 104 970 bytes): raw grep for the four bad strings = **0 matches**; `bedrock-runtime` ×48 (= the 48 LLM stances), `openrouter.ai` ×0. Round 3 is clean outright — no exception clause needed. On round 2 see Ruling 1 below. |
| 6. Public page uses the static replay path | TRUE | Method is the playbook-sanctioned one (observatory-api.md §Featured match, "Answered (lighthouse run, 2026-08-22)": raw grep finds nothing platform-wide and `/coworlds` `featured_match` is null platform-wide; SSR `state.playlist[0]` + session POST are the working sources — VERIFY used exactly those and said so). I reproduced both: the live SSR payload carries `playlist[0]` for this coworld (now round 4 — it was round 3 at verification time, consistent with the then-current leaderboard it embeds), and `POST /coworlds/replays/session` returns `ready:true` with `viewer_url` = `…/v2/coworlds/replays/static/cow_5bc1ce13…/sha256%3A3749debc…/index.html?replay=<s3>&v=2` — the static route, `<sha>` = STATE.coworld.manifest_sha, not a `/client/replay` pod URL. |
| 7. Certification declared the static bundle | TRUE | Read the committed `runs/…/release-result.json` myself (3 992 bytes, in git): `.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`; `.certify.ok: true`; 10/10 transcript steps pass in `output_tail`. The stale `hosted_certification: "certifying"` field is correctly flagged in VERIFY and superseded by the live `canonical: true` on v0.1.3. |
| 8. Viewer executed and judged | TRUE | CI run 33013149654 (`viewer-check`) `conclusion: success` — checked via `gh run view`, not accepted from VERIFY. Committed `viewer-smoke.json`: `loaded: true` at 2 764 ms via `data_replay_loaded:"true"`, `data_replay_error: null`, `failure: null`; three scrub clocks all differ (2:00/T1 → 0:59/T13 → 0:23/T20). Its `url` is byte-identical to check 6's session `viewer_url` (same round-3 replay). I viewed `viewer-smoke.png` myself: a legible Warlords arena at 0:13 / turn 22/24 / tick 2573/2928 — four corner brick lattices with chipped gaps, paddles, balls with particle trail, per-cabinet stance captions (`GUARD`×3, `CHASE >RED`) that match the decoded turn-21 stance vector seat-by-seat, champion say-lines `BLUE: B1 inbound 14t, defend` / `RED: defending the mouth` verbatim from the replay records, full note panels, a four-seat scorebug with hearts/chip bars, and the ctf-family transport strip (restart/step/play/+5s/loop/ffwd, `spoilers`, tick counter, 1×–16× speed bank) over a scrubber with momentum trace. Starter chrome, not a rewrite. The judgment paragraph in VERIFY is accurate to the pixels. |

## Rulings on the two declared wrinkles

**1. Round 2 ran 100 % scripted-fallback — not blocking.** SPEC's items 3–5 are explicitly
scoped to *the latest round's* episode request, which was round 3, clean outright (I reproduced
the CLEAN grep and the 48 Bedrock / 0 openrouter counts live). Item 1 requires only `completed`
(not failed/discarded) — round 2 is `completed`, `error: null`. Even a strict intent reading
("the coworld demonstrably plays its game with LLM champions on the ladder") is satisfied twice
over: rounds 1 **and** 3 are both 48/48 LLM, 0 fallbacks, on the same sidecar image digest that
round 2 carried when the platform routed it to openrouter (402 ×96) — the within-run three-round
table in VERIFY's Anomaly section pins the cause platform-side without needing the cross-coworld
clause, and the verifier honestly reported that the cross-coworld clause was *not* satisfiable
(poker's overlapping episodes were clean on a different digest) rather than leaning on it.
Round 2 is also positive evidence of the degrade-never-hang design pin: 100 % provider failure
still produced a completed, scored, `full_time` episode. Residue: round 2 stays on the ladder
and in `rounds_played: 3` — disclosed in VERIFY observation 4; nothing in SPEC forbids it.

**2. Check 4's strict-JSON via the design-declared decoder — not blocking.** The replay is the
starter's binary `COWLDCAB` container; `design.md` lines 1180–1204 declare exactly this before
release, name it "The phase-60 substitute for SPEC §Definition of done check 4", and specify the
decode-and-assert procedure verbatim — which the verifier ran, and which I re-ran independently
with the decoder fetched fresh from the released repo, reproducing every number. Every
substantive clause of item 4 (parseable under a strict parser, protocol match, `reason:
complete`, non-scripted non-trivial champion decisions, not all fallbacks) is verified against
strict UTF-8 JSON; item 4's own text already admits design-declared variance ("or a `deadline`
that the design declares acceptable"), and SPEC's design pins mandate the starter's static wasm
viewer, whose format this is. Item 8 proves the real consumer of the bytes parses them. Intent
satisfied; the deviation is declared, not smuggled.

## Verifier report audit

| claim | verifier said | I verified | agrees |
|---|---|---|---|
| rounds 1–3 completed, error null | TRUE | live re-fetch | yes |
| leaderboard rows (2, exact labels/counts) | TRUE | live re-fetch, byte-identical | yes |
| ereq status/replay_url/participants | TRUE | live re-fetch | yes |
| replay decode (48/0, protocol, results) | TRUE | independent re-decode, identical | yes |
| round-3 log CLEAN, 48 bedrock / 0 openrouter | TRUE | live re-fetch + raw grep | yes |
| session POST viewer_url static + ready | TRUE | live re-POST, identical URL | yes |
| featured match in SSR playlist[0] | TRUE | live page fetch (playlist now round 4 — consistent drift, not a discrepancy) | yes |
| release-result.json liveness string | TRUE | read committed file | yes |
| viewer-check run success, loaded, 3 clocks | TRUE | `gh run view` + committed json/png | yes |
| poker cross-check *failed* to corroborate | disclosed | taken as stated (against interest, and not load-bearing — round 3 needs no exception) | yes |

## Non-blocking observations (near-misses for the coordinator)

- Had round 3 not completed inside the polling window, check 5 could **not** have passed on
  round 2: the documented-exception clause requires cross-coworld corroboration the verifier
  itself proved absent. The pass is real but was one round from a block.
- The 100 % scrub readout is turn 20/24 / 0:23, not the final tick — the "three readouts differ"
  condition is met, but the scrubber does not reach the endcard; the screenshot (turn 22) sits
  *past* the 100 % readout. Odd instrument behaviour, disclosed denominator mismatch
  (`finalTick` 5275 vs 2928) also unexplained. Neither touches a checklist clause.
- `feed_lines: 0` (no `#feed` id) and `canvas_text.total: 0` (WebGL renderer; the ellipsis
  instrument is inert here) — both disclosed; the r1 ellipsis concern was checked by eye against
  the png, where the two 160-rune notes render complete. Phase-30 legibility nits, correctly
  routed as observations.
- Trivial: VERIFY names the momentum-graph label `HULL LEAD`; the png reads `HOLD LEAD`.
  Immaterial to any clause.

BLOCKING: 0
