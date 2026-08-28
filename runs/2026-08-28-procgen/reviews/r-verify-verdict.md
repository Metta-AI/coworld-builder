blocking: 0

# phase-60 verdict — procgen
Head: 3c143bcd (cogame-procgen, `prefill the assistant turn with `{``) · Checklist: docs/SPEC.md §Definition of done (items 1–8) · Independent read written before reading any self-report: yes (fresh-context adjudication; VERIFY.md is the artifact under judgment, read after the checklist)

Adjudicated 2026-08-28 ~22:5xZ against VERIFY.md (written 22:36–22:45Z). All live re-fetches
below were performed by the judge in this pass, GETs only (plus one `gh run view`).

## Standing blocking findings

None.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1. ≥2 rounds completed after fillers set | TRUE | VERIFY.md pastes fetched `GET /rounds` output (10 completed, 0 failed/discarded, all after fillers set 20:13:43Z per log.md:38 and the re-fetched filler registration). Judge live re-fetch: now **11** rounds, all `completed`, none failed/discarded — round 11 completed 22:47:12.759013Z. |
| 2. Both champions ranked, fillers absent/Baseline | TRUE | VERIFY.md pastes the fetched leaderboard. Judge live re-fetch of `div_6efcf3a6…/leaderboard`: `daveey` (`procgen-cartographer:v1`, rank 3, rounds_played 11, MMR 976.1) and `daveey-1` (`procgen-scrambler:v1`, rank 2, rounds_played 11, MMR 996.2) both ranked; `richard` rank 1; neither filler (`procgen-pathfinder`, `procgen-scavenger`) on the board, no Baseline row. Ranks have shifted since 22:37Z (daveey-1 overtook daveey in round 11) — the item requires both ranked, which holds. |
| 3. Latest round's episode requests completed with replay_url, participants named | TRUE | VERIFY.md anchored round 10 with pasted nested-route output. Round **11** has since completed, so the judge re-verified at the actual latest: `GET /rounds/round_74718756…/episode-requests` → 3 requests, all `completed`, all `coworld_id cow_84cce351-…` (0.1.2), all with non-null S3 `replay_url`; participants `daveey`/`procgen-cartographer`, `daveey-1`/`procgen-scrambler`, `richard`/`co-gas-procgen-safe-route-richard`, `is_filler:false` on all. |
| 4. Replay bytes valid, show the game, not all fallbacks | TRUE | VERIFY.md pastes the declared JSON substitute (`tools/replay_summary.py`, design.md §Replay bytes) applied to all three round-10 replays: strict UTF-8 JSON, `protocol procgen/v1`, `reason complete`, 72/78/79 turns all `source=="llm"`, `fallbacks=0` — "not all fallbacks" is satisfied at zero, verifiable from the pasted summaries. Judge re-verified independently on the **round-11** replays at head 3c143bc: all three parse strict (`jq -e` ok), `procgen/v1` / `complete`, 72/78/68 actions all `llm`, `fallbacks=0`, names daveey/daveey-1/richard. |
| 5. Hosted game logs clean (latest round) | TRUE | The adversarial check. History: rounds 1–9 were NOT clean (0.1.0 `falling back (parse_error)`, 0.1.1 residual `cut off at max_tokens`) — VERIFY.md declares this honestly and anchors the gate to round 10, all-0.1.2. Round **11** completed after VERIFY.md was written, so the judge fetched all three round-11 logs itself (`/episode-requests/<id>/artifacts/logs`, elevated header), decoded the `b'…'` byte-string reprs per-repr, and grepped: **0 matches** for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` in all three decoded bodies AND 0 for the widened case-insensitive `falling|unavailable|max_tokens|reject` on all three raw bodies. All three episodes ran on `cow_84cce351` (0.1.2) and ended `episode complete (gauntlet_complete)` (282/338/346 frames, 72/78/68 turns). The item holds at the actual latest round, not just the one VERIFY.md cited. |
| 6. Public page uses the static replay path | TRUE | VERIFY.md contains fetched, pasted evidence: page 200 at 762126 B; featured match present in the SSR payload at `state.pool.replays[0]` (round 10 ep 3, 0.1.2); the session endpoint the page's JS calls returns `viewer_url` = `…/v2/coworlds/replays/static/cow_84cce351-…/sha256%3Ac263c8bd…/index.html?v=2#replay=<encoded s3 url>`, `ready:true` — the static route with the 0.1.2 manifest sha, no `/client/replay` anywhere. Shape deviation from the SPEC's literal `?replay=` (it is `?v=2#replay=`) is the platform's current static-route shape as VERIFY.md documents; the substantive requirement (static bundle path, never a pod URL) is met. |
| 7. Certification declared the static bundle | TRUE | Judge read the committed `runs/2026-08-28-procgen/release-result.json` directly: `version 0.1.2`, `cow_id cow_84cce351-…`, `certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` — the required string verbatim, from the 0.1.2 release artifact, `ok:true`, 10/10 cert steps in the transcript tail. |
| 8. Viewer executed + spectator judgment | TRUE | Judge opened the committed artifacts itself. `viewer-check/viewer-smoke.json`: `loaded:true` (1938 ms), `data_replay_loaded:"true"`, `data_replay_error:null`, `failure:null`, `status:"LIVE"`, and the three scrub clocks **all differ** — `LEVEL 1/8 … frame 0` → `LEVEL 5/8 … frame 42 … UNSEEN SEED 1762650379` → `LEVEL 8/8 … frame 60 … SEEN SEED 1032`; the opened URL is byte-identical to check 6's `viewer_url`. `viewer-smoke.png` viewed by the judge: legible endcard (`SCORE 0.306 — mean over 4 unseen levels`, `SEEN 0.438 · UNSEEN 0.306 · GAP +0.132`), eight-row level table whose rows match the replay `results` arrays exactly (incl. level 4 chaser/died, level 7 miner/cleared/1000), scorebug `richard COG-alpha L8/8 · MAZE SEEN`, transport strip + `SEEN vs UNSEEN` momentum scrubber, feed lines matching the replay says. The judgment paragraph in VERIFY.md is written from what was drawn and reconciles with the record. CI fact-check: run 33217648127, `status completed`, `conclusion success`, created 22:39:40Z (matching the 22:39:38Z dispatch claim). |

## Refuted

Nothing to refute: this is a phase-60 adjudication of VERIFY.md, and no claim in it was found
stale, wishful, or falsified. Its two staleness exposures were checked hardest:

- **Round 11 post-dates VERIFY.md** (completed 22:47:12Z vs. the 22:45Z write). Judged on the
  actual latest: round 11 is clean on items 3, 4 and 5 (evidence above), so the newer round
  strengthens rather than falsifies the document.
- **Leaderboard drift**: daveey-1 has overtaken daveey since VERIFY.md's fetch. Item 2 requires
  both champions ranked and fillers absent, which still holds.

## Non-blocking observations

- SPEC item 6's literal iframe-src shape (`index.html?replay=`) differs from the platform's
  current `index.html?v=2#replay=<url-encoded>` fragment shape. VERIFY.md documents this; the
  static-vs-pod requirement is unambiguous either way. If the SPEC text is meant to be literal,
  update it to the current shape.
- `ordersRejected: 3` in the richard replay results is a results-schema counter (silent
  symbol-level repair, design.md), not a log line; VERIFY.md's note on it is accurate — no
  `rejected` line exists in any hosted log checked (rounds 10 and 11).
- The 0.1.2 release seated `:v3` policy uploads while the league plays `:v1`; VERIFY.md's
  reasoning (engine-side fixes travel with the image, prompt text unchanged) is consistent with
  the clean round-10/11 logs observed.

## Fixer report audit

Not applicable — phase 60 has no fixer report; the artifact under audit is VERIFY.md, whose
claims were all re-verified above (live for items 1–5, committed artifacts opened directly for
7–8, pasted-inline evidence accepted and cross-checked for 6).

BLOCKING: 0
