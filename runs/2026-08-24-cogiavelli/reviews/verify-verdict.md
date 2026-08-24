blocking: 0

# verify verdict — cogiavelli (phase 60)
Run: 2026-08-24-cogiavelli · v0.1.1 · cow_f54e03ab-39e9-4763-b46f-51556727bdd4
Checklist: docs/SPEC.md §Definition of done (items 1–8), as operationalised by prompts/60-verify.md
Independent read written before adjudicating VERIFY.md's verdict labels: yes
Adjudicated: does the evidence VERIFY.md *contains* prove each item — not whether its labels say TRUE.

## Standing blocking findings

None.

## Per-check adjudication

### 1. ≥2 completed rounds after fillers set — PROVEN
Pasted rounds list shows rounds 2, 3, 4 `completed` (14:08:07Z, 14:23:09Z, 14:38:39Z), round 1
`failed` with the verbatim error `Temporal RoundWorkflow failed before settling the round.`
(excluded by design — known context). Live elevated `GET /leagues/$L/filler-policies` confirms
both fillers registered (`bddc599d…`, `4ce9c9d1…`, matching STATE.policies.filler_version_ids).
Even under the worst-case reading of the filler timestamp (see observation 1 below — 14:07:02Z,
the log-line write time, rather than VERIFY's claimed 14:03Z), all three completed rounds finish
after it; the ≥2 requirement holds on the pasted evidence under either reading.

### 2. Both champions ranked — PROVEN
Pasted leaderboard (bare array, correct endpoint): `daveey-1` rank 1 `cogiavelli-borgia:v2`
rounds_played 3; `daveey` rank 4 `cogiavelli-medici:v2` rounds_played 3. Neither filler policy
appears as a row. `relh`/`richard` at ranks 2–3 are third-party platform players (known context,
not a defect; their ~14:34Z arrival is what displaced daveey to rank 4 and VERIFY documents it).
Spot-refetch reproduced all four rows verbatim.

### 3. Latest round's episode request — PROVEN
Round 4 is `max_by(.round_number)` of the completed set; `ereq_12b0cd3d-09f0-40fb-ac32-35e64ff8787c`
pasted with `status: "completed"`, non-null `replay_url`, participants naming `daveey` (pos 1,
medici:v2) and `daveey-1` (pos 2, borgia:v2), fillers flagged `is_filler: true` and surfacing as
`Baseline` / `Baseline (2)` in the replay's `policyNames` (item 4). Spot-refetch matched.

### 4. Replay bytes — PROVEN
Strict-parse shown under two independent parsers (`jq -e`, python strict utf-8 decode);
`protocol == cogiavelli.replay.v1`; `results.reason == "complete"` (no deadline exception
needed). The prompt's literal `select(.type=="decision")` does not apply — this replay is
`kind`-tagged (known context); the press/orders `scripted:true` census is the correct adaptation
and its numbers reconcile internally: event census 72 press + 72 orders = 144 = 6 seats × 24;
champion seats 1 and 2 `scripted = 0/24` (zero fallbacks, stronger than "small minority"); only
seats 4/5 — the scripted fillers by construction — are 24/24. Non-trivial content pasted (real
press with pledges, real orders with an adjudicator-repaired `nonadjacent` in `illegal[]`).
I re-fetched the replay (265223 bytes) and reproduced the census, results and stab counts exactly.
Arithmetic reconciliation I ran myself: all six `scores` match `(cities + min(ducats,24)/24)/24`
to the digit against the pasted `cities`/`ducats`.

### 5. Hosted log clean — PROVEN
Elevated fetch shown (200254 bytes, 4 containers), grep zero matches in both the decoded text and
the raw bytes; corroborated by 96 `bedrock_sidecar_call` / 96 `bedrock_sidecar_complete` (1:1 — no
retries, no truncation) which equals the expected 4 LLM seats × 4 years × 3 seasons × 2 phases.
No platform-exception claim was needed or made.

### 6. Static replay path + featured match — PROVEN
The raw-HTML grep found nothing and VERIFY recorded it as unknown-not-failure, exactly as the
prompt instructs. The prompt's named fallback (coworld detail API) was fetched and shown to be
uninformative — `featured_match: null` for all 46 canonical coworlds — before falling through to
the page's actual data path (SSR `state.playlist[0]` + `POST /coworlds/replays/session`), both
sources recorded. The pasted evidence proves both requirements: featured match present
(`cogiavelli.r4.e1`, the same episode as items 3–5, `inspectUrl` naming the same ereq), and the
iframe `src` is `…/v2/coworlds/replays/static/cow_f54e03ab…/sha256%3A0489a9e7…/index.html?replay=<s3 url>`
with `<sha>` = STATE.coworld.manifest_sha and no `/client/replay` substring. Independently
corroborated: the CI-produced `viewer-smoke.json` `.url` (a different producer) is byte-identical
to the session `viewer_url`, and my refetch of the page SSR reproduced `playlist[0]` verbatim.
The 14:24–14:35Z empty-playlist transient is documented with an established cause and resolved
within the retry budget; the TRUE rests on the post-round-4 fetch, not on the excuse.

### 7. Certification static-bundle declaration — PROVEN
Read from the committed `runs/2026-08-24-cogiavelli/release-result.json` (commit `a6561a6`),
source stated, `/tmp` not consulted. I read the committed file myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` —
contains the required substring. `policy_version_id: null` in that artifact is expected (known
context).

### 8. Viewer executed and judged — PROVEN
Dispatch → find-run-by-createdAt (not latest-blind) → run `32740208697` `conclusion: success`
(I re-verified via `gh`: success, created 14:40:57Z, workflow viewer-check) → artifacts committed
under `runs/…/viewer-check/` (commits `5c6e776`, `87153ab`). The pasted readouts match the
committed `viewer-smoke.json` byte-for-byte: `loaded: true` at 1095 ms via **both** signals
(`data-replay-loaded="true"` and bridge `ready`), `failure: null`, and three **differing** clock
readouts (`SPRING 1499` / `SPRING 1501 · LETTERS · TURK` / `FINAL · VENICE 6 CITIES`) from a real
`#scrub`. The judgment paragraph is written from the rendered evidence and I checked it against
the png myself: COGIAVELLI wordmark, centred clock, six seat-coloured scorebug plates, city-share
bar with treasury row (`NEUTRAL 4` = 24 − 20 owned ✓), labelled Italy map, endcard with ranked
table and payer×target ledger, transport strip `237 / 237` with a dense momentum scrubber — the
babel-lineage chrome, not a gridlock-style rewrite. Endcard reconciles field-for-field with
`results` (e.g. daveey-1·VENICE 6/48đ/24đ/0.292 vs cities[2]=6, ducats[2]=48, spent[2]=24,
scores[2]=0.29166…), and I additionally verified the per-power STAB split VERIFY only summed:
replay stab census by power index is {0: 2, 2: 6} which in canonical power order
(VENICE, MILAN, FLORENCE, …) is VENICE 2, FLORENCE 6 — exactly the endcard's column. The two
legibility observations (letterboxed map; unitless winner reads oddly) are correctly routed as
non-blocking phase-30 material, not check failures.

## Refuted

None — no reviewer findings existed for this phase; this verdict is the independent adjudication
of VERIFY.md itself. No check's verdict label had to be overturned: in every case the pasted
evidence, not the label, carries the claim.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1 ≥2 completed rounds post-fillers | TRUE | VERIFY §1 rounds JSON (r2/r3/r4 completed); filler-policies 200; spot-refetch consistent |
| 2 both champions ranked | TRUE | VERIFY §2 leaderboard rows (daveey-1 r1, daveey r4, 3 rounds each); refetch identical |
| 3 latest round ereq completed + replay | TRUE | VERIFY §3 ereq_12b0cd3d JSON; refetch identical |
| 4 replay bytes valid, champions live | TRUE | VERIFY §4; my refetch reproduced census 0/24 scripted on seats 1–2, scores arithmetic checks |
| 5 hosted log clean | TRUE | VERIFY §5 grep=0 decoded+raw; 96/96 bedrock call/complete |
| 6 static iframe + featured match | TRUE | VERIFY §6 session viewer_url (static route, manifest sha); SSR playlist[0]; my refetch of SSR matches |
| 7 cert declared static bundle | TRUE | committed release-result.json read directly by me; commit a6561a6 |
| 8 viewer executed, judged | TRUE | run 32740208697 success (re-verified); committed viewer-smoke.json/png match pasted readouts; png inspected |

## Verifier report audit

| check | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | 3 completed rounds after fillers | rounds JSON + filler read; holds under both 14:03Z and 14:07Z readings | yes |
| 2 | both champions ranked, fillers absent | refetched leaderboard, identical | yes |
| 3 | ereq completed, replay_url, participants | refetched ereq, identical | yes |
| 4 | strict JSON, complete, 0/24 fallbacks | refetched replay, reproduced every number | yes |
| 5 | CLEAN, 96/96 bedrock | internally consistent; expected-call arithmetic checks | yes |
| 6 | featured match + static src | refetched SSR playlist; CI url cross-matches session url | yes |
| 7 | committed artifact contains substring | read committed file myself | yes |
| 8 | loaded:true, 3 clocks differ, chrome faithful | gh run success; json/png match; endcard↔results↔stabs reconciled incl. per-power split | yes |

## Non-blocking observations

1. **Check 1 timestamp imprecision.** VERIFY states fillers were "registered at 14:03Z (log.md
   line 50)", but log.md line 50's written timestamp is 14:07:02Z (phase-50 log lines were
   batch-written). Immaterial to the verdict — all three completed rounds finish after 14:07:02Z
   too — but the citation is looser than the claim.
2. **Check 1 un-pasted detail.** "Round 1 carried only one entrant (61d34873-…, medici)" has no
   pasted fetch behind it. Non-load-bearing: round 1's exclusion rests on its `failed` status and
   verbatim error, which are pasted.
3. **Check 6 source set.** The evidence path used (SSR playlist + session POST) is a third source
   beyond the prompt's two named ones, adopted only after both named sources were fetched and
   shown empty/uninformative, with all of it recorded. This is the page's real data path per the
   playbook and the right call; noting it only because the prompt's letter names two sources.

BLOCKING: 0
