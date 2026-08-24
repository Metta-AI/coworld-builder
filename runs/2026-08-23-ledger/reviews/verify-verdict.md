blocking: 0

# verify verdict — ledger (phase 60)

Run: 2026-08-23-ledger · cow_7754c862-182c-4ec9-bca6-4311d36f2be4 · version 0.1.0
Checklist: `prompts/60-verify.md` §The eight checks / SPEC.md §Definition of done (lines 144–180)
Independent read written before reading VERIFY.md: **yes** — I re-fetched checks 1–6 from the
Observatory API, re-read the replay bytes from S3, re-read both committed viewer-check artifacts
and release-result.json, and re-downloaded all three CI artifacts from their run ids to diff
against the committed copies, before opening VERIFY.md.

Provenance audit (adversarial, all passed): the committed `viewer-check/viewer-smoke.json` is
byte-identical (jq -S diff) to the artifact of run **32675471888** (conclusion `success`,
created 2026-08-24T00:04:03Z); the committed `viewer-check-attempt1/` matches run
**32675392403** (`success`, 00:02:27Z); the committed `release-result.json` matches the
`release-result` artifact of cogame-ledger run **32673657033** (`success`). Nothing was
hand-edited between CI and the repo.

## Per-check adjudication

### Check 1 — ≥2 completed rounds after fillers — **CONFIRMED**
Re-fetched `/rounds?league_id=$L`: round 3 `completed` (round_9010fafa), round 2 `completed`
(round_3b6b2b34), round 1 `failed` with error verbatim `Temporal RoundWorkflow failed before
settling the round.` — matches the paste. Attempted refutation on the timing claim: round 2's
`created_at` (23:37:02Z) actually **precedes** the fillers-POST log stamp (23:38:06Z), so the
wall-clock argument alone would not prove "after the fillers were set". It does not stand as a
refutation because the verifier supplied the stronger, decisive evidence and I reproduced it:
both rounds' episode requests seat six `is_filler: true` seats (`ereq_d4d235d5` for round 2,
`ereq_e23450b7` for round 3 — positions 2–7 are ledger-mirror/ledger-shark, `is_filler: true` in
my own fetch). A round whose episode seats the registered fillers ran with the fillers set by
construction. TRUE stands.

### Check 2 — both champions ranked, fillers absent — **CONFIRMED**
Re-fetched `/divisions/$D/leaderboard` (bare list): exactly two rows —
`1 daveey ledger-reputation:v1 1001.4695… rounds_played 2` and
`2 daveey-1 ledger-broker:v1 998.5304… rounds_played 2`. Fillers absent. Identical to the paste.

### Check 3 — latest round's episode request — **CONFIRMED**
Latest completed round = 3 → `ereq_e23450b7-fb5c-4a9e-818b-f3f5d3f06f9e`. My fetch:
`status: "completed"`, `replay_url: …/replays/316d64ba-….replay` (non-null), participants
position 0 = `daveey`/`ledger-reputation` (`is_filler: false`), position 1 =
`daveey-1`/`ledger-broker` (`is_filler: false`), positions 2–7 filler mirror/shark. Replay
`policyNames` renders fillers as `Baseline`…`Baseline (6)`. Matches the paste field for field
(the verifier's participant table is a trim of the raw body, not an alteration).

### Check 4 — replay bytes valid and show the game — **CONFIRMED**; the vocabulary substitution is faithful, not a dodge
Re-fetched the 28 922-byte replay from S3 myself: python strict `.decode('utf-8')` +
`json.loads` pass; `protocol == "ledger.replay.v1"`; `results.reason == "complete"` (the
`deadline` allowance is not needed). The prompt's generic probes (`type=="decision"`,
`fallback==true`) return 0 **because the keys do not exist in this game's vocabulary** — the
design note (`design.md` §Event vocabulary) defines exactly five kinds keyed `kind`, with
per-meeting `scriptedA`/`scriptedB` flags, and pins the fallback log line
`ledger: seat N falling back to scripted decision`. The substituted probe measures precisely
what the checklist item is *for* (champion seats non-scripted, not all fallbacks): my
independent count over the 56 `meeting` events gives champion seats 0 and 1 **0/14 scripted
each**; the 84 `scripted: true` seat-decisions are exactly the 6 registered-scripted filler
seats × 14 rounds. Champion content is non-trivial — 26 gossip events and multi-sentence memos
citing specific rounds, subgames and numbers (e.g. seat 0's R2 memo reasoning over Gasket's R1
ULTIMATUM record). Cross-checked against the hosted log: zero `falling back` lines, so no
scripted flag is an LLM fallback. Showing the 0-result generic probes alongside the substituted
ones is the honest treatment. TRUE stands.

### Check 5 — hosted game log clean — **CONFIRMED**
Re-fetched `/episode-requests/ereq_e23450b7…/artifacts/logs` with the elevated header myself:
grep for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → **CLEAN**
(on both the raw body and the decoded text; a match inside a `b'…'` repr would surface in the
raw grep too, so the verifier's decode step could not have hidden a hit). Every
`bedrock_sidecar_complete` line is `ok:true, status_code:200`; the game container plays all 14
rounds in 269 s and exits cleanly (`episode complete, shutting down`). No exception invoked.

### Check 6 — public page uses the static replay path — **CONFIRMED**
Reproduced all three legs: (i) raw `https://softmax.com/ledger` HTML has no `<iframe` —
client-rendered, which the prompt explicitly says is *unknown*, not a false negative; (ii) the
SSR payload's `state.playlist[0]` names cow_7754c862 / ledger 0.1.0 with a replay URL and
matchup daveey vs daveey-1 (my fetch now shows `ledger.r4.e1` — the featured match has rotated
to the newer round 4 since the verifier's `ledger.r3.e1` snapshot; both prove presence);
(iii) `POST /coworlds/replays/session` returns
`…/v2/coworlds/replays/static/cow_7754c862-…/sha256%3A655ad056…/index.html?replay=<s3 url>` with
`ready: true` — the static route, `<sha>` equal to `manifest_sha` in release-result.json, and no
`/client/replay` pod URL anywhere. The verifier declared which source was used, as required.
(`/coworlds`' `featured_match: null` is documented platform-wide behaviour —
`playbooks/observatory-api.md` §Featured match — and was correctly not treated as evidence.)

### Check 7 — certification declared the static bundle — **CONFIRMED**
Read the committed `runs/2026-08-23-ledger/release-result.json` myself:
`.certify.replay_liveness == "Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)"` — contains the required prefix verbatim; the same
string appears in `certify.output_tail`. The committed file is identical to release run
32673657033's artifact (diffed). Minor: the verifier's "surrounding fields" paste
`{"ok": true, "canonical": true, "certify_ok": true}` flattens `.certify.ok` into a synthetic
`certify_ok` key that does not literally exist in the file — a cosmetic reformat; the underlying
values are real (`.ok`, `.canonical`, `.certify.ok` are all `true`). Not evidence-invalidating.

### Check 8 — viewer executed and judged — **CONFIRMED**; the disclosed retry is a legitimate probe race, not a masked defect
Run of record 32675471888: `loaded: true` via **both** signals
(`data_replay_loaded: "true"` and bridge `ready`), `failure: null`, and three differing clock
readouts — `ROUND 0 / 14` → `ROUND 8 / 14 · TABLES MEET` → `FINAL — 14 ROUNDS`. The artifact's
`url` is byte-identical to check 6's session `viewer_url`, so the thing executed is the live
public iframe. My own reconciliation beyond the verifier's: the scrubber's `98 / 98` equals the
replay's event count (1 start + 14 round + 56 meeting + 26 gossip + 1 end = 98); the endcard rows
in the screenshot match `results` exactly (daveey 6.0/5.2/14/10/4; Flywheel 2.0/2.1/14/0/14 —
the shark filler's kind 0/harsh 14); the on-screen gossip cards quote the recorded round-13
gossip events. The screenshot is the babel/parley starter chrome (wordmark, clock, status chip,
feed toggle, scorebug plates, transport band with scrubber + beat markers + position counter,
endcard stopping above the transport band) with the game's plaza, halo and gossip-rail additions
inside it — no gridlock-style rewrite.

**Attempt-1 adjudication (probe race vs viewer defect): probe race, as claimed.** Four
independent facts, none supplied by the verifier's say-so: (i) the instrument's wait loop breaks
on the bridge `ready` alone (`templates/tools/ci/viewer_smoke.mjs:366` — the verifier's citation
is the correct line) and begins scrub clicks immediately with only a 700 ms settle
(viewer_smoke.mjs:431–441); attempt 1's signals show exactly that draw — `bridge_ready: true`
with `data_replay_loaded: null`, `scorebug: ""`, `feed_lines: 0`, i.e. probes fired mid-hydration;
(ii) attempt 1's 0%→100% readouts move (`ROUND 0` → `ROUND 0 / 14`) — a shell booting under the
probes, not a frozen one; (iii) attempt 1's own screenshot, taken after the probes, shows the
fully drawn plaza at frame `1 / 98` with a populated scorebug — the viewer rendered; (iv) the
bundle is immutable (same manifest-sha URL) and the identical URL fully passed 96 seconds later —
a deterministic viewer defect does not heal; a start-condition race does. Both attempts were
committed undoctored (diffed against their CI artifacts). Retry 2 of a 3-attempt budget, with a
changed approach (timeout 90 → 180 per the run logs). One accuracy note: the longer timeout was
not the causal fix — both attempts signalled loaded in ~1.4 s and the timeout only bounds the
load-wait loop; the pass is the `data-replay-loaded`-before-`ready` ordering landing the other
way. That nuance strengthens, not weakens, the verifier's own LEARNINGS proposal (gate scrubbing
on `data-replay-loaded`, not on bridge `ready` alone).

## Refuted
None. No check's pasted evidence failed reproduction, and no TRUE rested on inferred rather than
fetched evidence (checks 1–6 re-fetched live and matching; checks 7–8 read from committed CI
artifacts whose provenance I re-verified against their run ids).

## Verifier report audit
| check | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | rounds 2+3 completed post-filler; round 1 failed, error quoted | same rounds/statuses/error fetched; filler seating in both episodes confirmed | yes |
| 2 | 2 rows: daveey, daveey-1, rp=2; fillers absent | identical leaderboard fetched | yes |
| 3 | ereq_e23450b7 completed, replay_url, participants correct | identical fetch | yes |
| 4 | strict UTF-8, ledger.replay.v1, complete, champions 28/28 live | reproduced byte-for-byte incl. scripted counts (84 = 6×14) | yes |
| 5 | CLEAN | reproduced on raw and decoded log | yes |
| 6 | SSR playlist + session POST → static route, ready:true | reproduced (featured match now rotated to r4) | yes |
| 7 | committed file contains the liveness-skipped string | reproduced; file matches run 32673657033 artifact | yes (cosmetic `certify_ok` reformat noted) |
| 8 | loaded:true, 3 differing clocks, race on attempt 1 | artifacts match runs 32675471888/32675392403; race corroborated from instrument source + attempt-1 data | yes (timeout-not-causal nuance noted) |

## Non-blocking observations
- `viewer_smoke.mjs` accepts bridge `ready` alone as "loaded" and scrubs immediately; attempt 1
  is the false-negative shape. Endorse the verifier's LEARNINGS item; the fix belongs in
  coworld-builder's template, not in cogame-ledger.
- Check 1's wall-clock framing ("round_number ≥ 2, i.e. after the fillers POST at 23:38:06Z") is
  loose — round 2's `created_at` (23:37:02Z) precedes that stamp. The check survives on the
  filler-seating evidence, which the verifier also supplied; future VERIFY.md writers should lead
  with the seating proof, not the timestamps.
- VERIFY.md check 7's "surrounding fields" JSON is a synthesized flattening, not a verbatim
  paste. Harmless here; verbatim pastes are the standard.

All eight checks TRUE at the current head. No blocking findings.

BLOCKING: 0
