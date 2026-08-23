blocking: 0
# Phase-60 verdict — cogball (v0.1.5)

Judge: fresh context, 2026-08-23. Adjudicating `runs/2026-08-22-cogball/VERIFY.md`
(verifier's 8/8 all-true pass, 09:34:45Z) against SPEC §Definition of done, using
`prompts/60-verify.md` as the command source. Reading order honoured: SPEC checklist →
prompt → artifacts on disk → independent re-fetches → VERIFY.md. Independent read written
before accepting any of the verifier's dispositions.

Everything below marked "re-fetched" was fetched by me in this adjudication
(2026-08-23, ~10:0xZ), read-only, with `SOFTMAX_TOKEN` / `gh`. No rounds triggered, no
workflows dispatched, nothing written to the league.

Head state under test: v0.1.5, `cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339`, manifest
`sha256:495905b1…5dce7`, release run `32624985984`;
league `league_e87130ef-ecc6-49d4-9bc1-4014b7141df5`, division
`div_45c40cad-ef84-4d48-a733-59e55f80e24c` — all matching `STATE.json`.

---

## Check 1 — ≥2 completed rounds after fillers set — PASS

**Verifier's claim:** 16 completed rounds, 0 failed/discarded, all after the filler
registration at 05:42:09Z.

**My re-fetch:** `GET /rounds?league_id=league_e87130ef…&limit=30` → HTTP 200;
`[.entries[]|select(.status=="completed")]|length` = **16** (round 17 now `pending`,
`error: null` — not a failure). Earliest completed: round 1 at `2026-08-23T05:44:06.458180Z`;
latest: round 16 at `09:29:13.606649Z`. Zero `failed`/`discarded` entries.
`log.md` line `2026-08-23T05:42:09Z 50 fillers 200: formation:v2 + swarm:v2 registered
BEFORE trigger` precedes round 1's completion by ~2 minutes. I also re-fetched
`GET /leagues/league_e87130ef…/filler-policies` (elevated) → exactly
`7c11dd63…/cogball-formation/2` and `259d11a4…/cogball-swarm/2`, matching
`STATE.policies.filler_version_ids` and neither being a champion version id.

**Assessment:** the claim reproduces exactly. 16 ≥ 2. PASS.

## Check 2 — both champions ranked, fillers absent/Baseline — PASS

**Verifier's claim:** leaderboard has exactly two rows — daveey rank 1
(`cogball-total:v2`, 16 rounds, 9 wins) and daveey-1 rank 2 (`cogball-counter:v2`,
16 rounds, 4 wins); fillers absent.

**My re-fetch:** `GET /divisions/div_45c40cad…/leaderboard` → HTTP 200, bare list,
length 2:
```
1  daveey    cogball-total:v2    1026.850301556938  16  9.0
2  daveey-1  cogball-counter:v2  973.1496984430622  16  4.0
```
Byte-for-byte the rows VERIFY.md pasted. Both `rounds_played` = 16 ≥ 1; no filler row at
all (the stronger permitted outcome). PASS.

## Check 3 — latest round's episode request completed with replay — PASS

**Verifier's claim:** round 16 → single episode request `ereq_21ccb33a…`, `completed`,
replay `f2133337-531b-4ff6-91d6-1385fb48a307.replay`, participants daveey + daveey-1,
both `is_filler: false`.

**My re-fetch:** `GET /episode-requests?round_id=round_ce3789ab…` → 1 entry,
`ereq_21ccb33a-41bc-466c-a35b-12d7eb1ffad9 / completed`. Detail GET →
`status: "completed"`, `replay_url:
https://softmax-public.s3.amazonaws.com/replays/f2133337-531b-4ff6-91d6-1385fb48a307.replay`,
participants `cogball-total v2 / daveey / is_filler:false` (seat 0) and
`cogball-counter v2 / daveey-1 / is_filler:false` (seat 1), scores 0.5/0.5. Round 16 was
still the latest completed round at my fetch time. Identical to VERIFY.md. PASS.

## Check 4 — replay bytes valid and show the game — PASS (documented substitution honoured)

**Verifier's claim:** binary `COWLDBAL` container; the design-note-declared substitute
`tools/replay_summary.py` yields strict JSON with `protocol cogball/v1` (matching the
manifest), `results.reason "complete"`, 80/80 directives `source=="llm"`, 0 fallbacks,
non-trivial notes/intents on both champion seats.

**My reproduction, end to end:**
- The substitution is genuinely declared in the accepted design note:
  `runs/2026-08-22-cogball/design.md` §"Replay bytes (self-sufficient)", line 802: *"The
  phase-60 substitute for SPEC §Definition of done check 4 is therefore:
  `python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json` …"*. The prompt's
  strict-JSON requirement is applied to the tool's output, per the note. This is the one
  substitution VERIFY.md claims, and it is real.
- Fetched the S3 object myself: HTTP 200, **185452 bytes**, header
  `C O W L D B A L … c o g b a l l` — magic and game name as claimed.
- Cloned `Metta-AI/cogame-cogball` at HEAD `ed78392` (same sha VERIFY.md used), ran the
  tool: exit 0; `jq -e` strict parse ok; `protocol` = `cogball/v1`;
  `results.reason` = `complete`; directives: **80 total, 80 `source=="llm"`, 0 fallbacks**,
  split `[{seat:0,total:40,llm:40},{seat:1,total:40,llm:40}]`; `utf8Repairs: 0`;
  0 directives with empty note+intents. Results line identical to VERIFY.md's
  (`goals [1,1]`, `shots [15,1]`, `endRule full_time`, `finalTick 5106`, seed 1770193400).
- Manifest match verified: `coworld_manifest_template.json` `.game.docs.pages[1]`
  (title "Wire protocol"), content line 141: `{"protocol":"cogball/v1",…}`.
- Spot-read directives (turns 0, 20): substantive tactical content
  ("Kickoff: AZ-1 nearest to ball (1.5m) takes the attack…"), not boilerplate.

PASS.

## Check 5 — hosted game log clean — PASS

**Verifier's claim:** 174583-byte log over 4 containers, grep for
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected` empty → CLEAN;
no exception claimed; log's seed and replay byte count tie it to check 4's episode.

**My re-fetch:** `GET /episode-requests/ereq_21ccb33a…/artifacts/logs` (elevated) →
HTTP 200, **174583 bytes**, grep → **CLEAN**, 4 `===== container` markers, and the log
contains `seed=1770193400` and `185452 bytes` — the same episode as the replay I fetched.
PASS.

## Check 6 — public page uses the static replay path — PASS

**Verifier's claim:** raw-HTML grep empty (client-rendered, the prompt's documented
fallback case); `/coworlds` shows `cow_ff38b98b` 0.1.5 as the only canonical row; SSR
playlist carries featured match `cogball.r16.e1` on replay `f2133337…`; the
`replays/session` POST returns a static-route `viewer_url` with the right cow_id,
manifest sha, and check-3 replay, `ready: true`.

**My re-fetches, all four sources:**
- `curl https://softmax.com/cogball` → HTTP 200, no `<iframe` in raw HTML (confirming the
  fallback was warranted, not a dodge);
- same page's SSR payload contains
  `playlist":[{"episodeId":"f2462e41…","coworldId":"cow_ff38b98b…","coworldVersion":"0.1.5","replayUrl":"…f2133337….replay","roundNumber":16,…,"code":"cogball.r16.e1"` —
  featured match present;
- `GET /coworlds?limit=200` → cogball rows: `cow_ff38b98b/0.1.5/canonical=true`,
  0.1.4/0.1.3/0.1.2 all `false` — only the 0.1.5 row is canonical, matching STATE;
- `POST /coworlds/replays/session` with `cow_ff38b98b` + the round-16 replay →
  `viewer_url = …/v2/coworlds/replays/static/cow_ff38b98b…/sha256%3A495905b1…/index.html?replay=…f2133337….replay&v=2`,
  `ready: true`. Static route; no `/client/replay` substring anywhere; sha equals
  `STATE.coworld.manifest_sha` URL-encoded; `?replay=` equals check 3's URL.

PASS.

## Check 7 — certification declared the static bundle — PASS

**Verifier's claim:** read from the committed
`runs/2026-08-22-cogball/release-result.json` (the prompt-pinned source), which is the
0.1.5 artifact from run 32624985984, and it contains the required string.

**My verification:** the committed file reads
`"replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`
with `{"ok":true,"version":"0.1.5","cow_id":"cow_ff38b98b…","canonical":true,"certify_ok":true}`
and a 10/10-pass certifier transcript in `output_tail`. I then audited provenance the
verifier did not need to: `gh run download 32624985984 -R Metta-AI/cogame-cogball -n
release-result` and diffed — **byte-identical to the committed copy** (release run:
`Coworld release`, completed, conclusion `success`, created 07:13:15Z). The committed
artifact is genuine, current (0.1.5, not a stale 0.1.3 copy), and contains the required
string. PASS.

## Check 8 — spectator judgment, viewer executed — PASS

**Verifier's claim:** fresh dispatch `32631291526` (09:32:37Z, this pass) against the
exact check-6 `src` (round 16 — deliberately not adopting the pre-existing green
`32630840631`, which tested round 15); `loaded: true` in 4122 ms via
`data-replay-loaded="true"`; three differing scrub clocks; `failure: null`; empty
console; judgment paragraph written from the screenshot.

**My verification:**
- `gh run view 32631291526 -R Metta-AI/coworld-builder` → workflow `viewer-check`,
  `completed/success`, created `2026-08-23T09:32:39Z` — after the claimed dispatch time,
  as required by the find-the-new-run rule.
- Downloaded that run's `viewer-check` artifact and diffed against the committed
  `runs/2026-08-22-cogball/viewer-check/`: **viewer-smoke.json and viewer-smoke.png both
  byte-identical**. The committed evidence really is that run's output.
- The committed json: `loaded: true`, `ms: 4122`,
  `signals.data_replay_loaded: "true"`, `data_replay_error: null`, `failure: null`,
  `console_tail: []`, `loading_text: null`, scrub readouts
  `0% → "3:20 TURN 1/40"`, `50% → "1:38 TURN 21/40"`, `100% → "FINAL GAME OVER"` — all
  three differ (condition 2 met). The bridge is absent (`bridge_ready: false`), which the
  prompt explicitly permits when `data-replay-loaded` carries the signal; I fetched the
  live bundle's `static_replay.js` myself (HTTP 200, 9203 B) and confirmed line 144 sets
  `data-replay-loaded` only on the worker's `loaded` message.
- The json's `url` field is **byte-identical** to the `viewer_url` my own fresh
  `replays/session` POST returned — the tested page and the public iframe are provably
  the same URL, round-16 replay included. The verifier's refusal to adopt run
  `32630840631` (round 15) was correct discipline, not theatre.
- I viewed `viewer-smoke.png` myself. It shows what the verifier says it shows: a dark
  pitch with centre circle, boxes and goals; header scorebug `1 · DAVEEY` /
  `DAVEEY-1 · 1` with `15 sh 61%` / `1 sh 38%` chips; centred `DRAW`,
  `1-1 · FULL TIME`, `reason: complete`; per-team stat panels (goals 1/1, shots on
  target 15(6) / 1(1), saves 0/0, possession 61%/38%, score 0.500/0.500); transport
  controls with speed selectors; a `GOAL LEAD` momentum strip. Those figures reconcile
  with the replay's `results` I extracted independently (`possessionTicks [2803,1782]`
  → 61%/39%). The judgment paragraph is legible, grounded in the artifacts, and honest
  about its one soft spot (`feed_lines: 0`, flagged as a legibility note, which is fair —
  it is not one of the check's two gating conditions).

All three gates hold: (a) `loaded: true` via the accepted signal, (b) three differing
clocks, (c) a judgment paragraph written from real rendered evidence. PASS.

---

## Refutations

None. I attempted to refute each of the eight claims by independent re-fetch and
artifact-provenance audit; every one reproduced. Specific refutation attempts that failed:

- **Recycled-evidence attack on check 8:** the committed viewer-check artifacts could have
  been copied from the earlier round-15 run. They are byte-identical to run
  `32631291526`'s artifact (round 16, dispatched by this pass), not to `32630840631`.
  Attack fails.
- **Stale-artifact attack on check 7:** the committed release-result.json could have been
  the 0.1.3 artifact. It carries `version 0.1.5 / cow_ff38b98b / canonical:true` and is
  byte-identical to release run 32624985984's artifact. Attack fails.
- **Wrong-episode attack on check 5:** the log could belong to a different episode. Its
  seed (1770193400) and replay byte count (185452) match the fetched replay. Attack fails.
- **Undeclared-substitution attack on check 4:** the binary-replay summary substitute is
  declared verbatim in the accepted design note (design.md line 802). Attack fails.

## Non-blocking observations (no checklist item; recorded for phase 80)

1. **Viewer tick counter vs replay tick space.** The screenshot's transport bar reads
   `4912 / 4920` while the replay's `finalTick` is 5106 (`tickCount` 5107,
   `maxTicks` 4800). VERIFY.md's "reconcile exactly" claim is scoped to
   goals/shots/possession/scores/reason — which do reconcile — and does not claim the tick
   counter, so this is not a false statement; but the viewer's displayed tick space
   differing from the replay's is worth a line in LEARNINGS.
2. **STATE.verify block is stale.** `STATE.json.verify` still carries the 0.1.3-pass
   values (`rounds [1,2]`, replay `96be8156…`, `viewer_check_run 32630840631`) while
   VERIFY.md's evidence is round 16 / `f2133337…` / run `32631291526`.
   `prompts/60-verify.md` §Writes expects these fields updated before `phase: "70"`; do so
   at the phase transition.
3. **`feed_lines: 0`** — already self-reported by the verifier; the commentary feed being
   empty at capture is a legibility nit, not a gate.
4. **`hosted_certification: "certifying"`** in the committed release artifact is an
   in-flight status string; the coworld is `canonical: true` on the platform and the
   certifier transcript is 10/10. Not a phase-60 item.

## Verdict

VERIFY.md's 8/8 all-true verdict is **upheld**. Every check's evidence was fetched inline,
nothing is NOT-FETCHED, the only substitution (check 4) is the design-declared one, the
only disk-read evidence (checks 7 and 8's committed artifacts) is exactly what the prompt
pins there — and both proved byte-identical to their CI sources under audit. No claim in
VERIFY.md is contradicted by any artifact on disk or by any of my independent re-fetches.

BLOCKING: 0
