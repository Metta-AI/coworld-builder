blocking: 0

# Phase-60 verdict — battlecode-2023
Head: c641e28 (coworld-builder) / 47f36001 (Metta-AI/cogame-battlecode main)
Checklist: docs/SPEC.md §Definition of done + prompts/60-verify.md (both read in full, first)
Independent read written before reading VERIFY.md: yes — I fetched the rounds list, leaderboard,
latest-round episode request, latest replay, hosted log, coworld list/detail, page SSR payload,
session route, committed release-result.json and the committed viewer-check artifacts (including
the screenshot) before opening VERIFY.md.

## Summary

VERIFY.md's 8/8 all-true verdict stands. Every check's pasted evidence supports its TRUE, every
spot-check I re-fetched reproduces (or supersedes upward — the league has since completed round 3,
which also passes), and both of the verifier's own findings are correctly classified as
non-blocking: neither falsifies a definition-of-done item as written. Zero blocking findings.

## Check-by-check adjudication (verifier's evidence vs. my re-fetch)

### 1. ≥2 completed rounds after fillers — TRUE stands
- Verifier pasted the full 17:20:34Z rounds body: rounds 1 and 2 `completed`, `error: null`,
  `skip_kind: null`, zero failed/discarded. Poll log 17:06→17:20Z inside the 75-min bound.
- My re-fetch (`GET /rounds?league_id=league_e3244a55-…`): **3** completed rounds now
  (round_ae192a12 #1, round_dd56e5e4 #2, round_57f7e9e5 #3), all `completed`, no error, none
  failed/discarded.
- Fillers-before-rounds: log.md 2026-09-08T17:02:01Z records fillers 200 → unpause → trigger with
  round 1 still `pending`; so all completed rounds are after-fillers. Verified against log.md
  myself.

### 2. Both champions ranked, fillers absent — TRUE stands
- Verifier pasted the bare-list leaderboard: daveey-1/`battlecode-bc23-alchemist:v1` rank 1,
  daveey/`battlecode-bc23-duel:v1` rank 2, `rounds_played: 2` each, exactly two rows.
- My re-fetch (`GET /divisions/div_dc5f977f-…/leaderboard`): rank 1 daveey-1 alchemist:v1
  1043.75 `rounds_played 3`; rank 2 daveey duel:v1 956.25 `rounds_played 3`. No filler rows —
  the "fillers absent" branch.
- Champions are LLM prompt policies, not scripted: `tools/ci/policies.json` at
  Metta-AI/cogame-battlecode@47f36001 (fetched via gh api) gives `battlecode-bc23-duel` and
  `battlecode-bc23-alchemist` a `PLAYER_PROMPT` env; `battlecode-lemonade` and
  `battlecode-examplefuncsplayer23` are `PLAYER_SCRIPTED`. Matches STATE.policies exactly.

### 3. Latest round's episode request completed with replay — TRUE stands
- Verifier used the nested route after documenting the flat `?round_id=` 405; pasted
  `ereq_66018a01-…` `completed` with non-null replay_url and both champions seated,
  `is_filler: false`.
- My re-fetch at current head (latest is now round 3, `round_57f7e9e5-…` via
  `GET /rounds/<id>/episodes`): `ereq_a720bebc-…` `status: completed`, replay_url
  `…/replays/b17974b9-….replay`, participants daveey (duel) + daveey-1 (alchemist),
  participant_scores 253.33 / 445.67. I also reproduced the flat-route failure
  (`Method Not Allowed`), confirming the verifier's documented deviation is real, not an excuse.

### 4. Replay bytes valid and show the game — TRUE stands
- Verifier: strict `jq -e` parse ok, `protocol cogame.battlecode.v1` reconciled against the
  manifest's protocol document and the bc23 variant row, `.result.reason == "complete"`,
  2/2 doctrine decisions answered on attempt 1, 0 fallbacks, both seats `policy: llm`, seat-0
  sheet fully non-default with map-specific notes.
- My re-fetches: round-2 replay (16e08a05, 140209 bytes) and round-1 replay (f62806cf, 53548
  bytes) both strict-parse ok, `result.reason: complete`, `fallbacks [0,0]` — matching the
  pasted evidence byte for byte where pasted. The **current-head latest** replay (b17974b9,
  round 3) also strict-parses, `protocol cogame.battlecode.v1`, `result.reason: complete`,
  `fallbacks: [0,0]`, and — notably — **both** seats played their own non-default sheets
  (seat 0 launcher_rush/72/mana/never…, seat 1 carrier_eco/42/early/anchor_round 200…),
  `unknown_fields: 1` (just `notes`) on each.
- Note: the prompt's literal `.events[]|select(.type=="decision")` and `.results.reason`
  commands return 0/null on this coworld (events use `kind`, result is singular `result`) — the
  verifier translated the commands to the coworld's schema and said so. That is the correct
  reading of the check's intent, and I verified the translated evidence independently.

### 5. Hosted log clean — TRUE stands
- Verifier pasted the full decoded round-2 log: zero matches for the four patterns; both
  doctrine calls `HTTP/1.1 200 OK`; no Bedrock-capacity exception claimed.
- My re-fetch of the round-3 log (`/episode-requests/ereq_a720bebc-…/artifacts/logs`, elevated
  header): grep for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` →
  **CLEAN**. The `refused a seat-0 connection … wrong connection token` line the verifier flagged
  as an observation matches none of the four patterns ("refused" ≠ "rejected") and the real seat
  registers on the next line — correctly classified as not a failure.

### 6. Static replay path + featured match — TRUE stands
- Verifier attempted the raw-HTML grep first (empty — client-rendered page, the documented
  *unknown* outcome), showed `featured_match: null` platform-wide on the coworld API, then used
  the two playbook-sanctioned sources: SSR `state.playlist[0]` and
  `POST /coworlds/replays/session`. Which-source-was-used is recorded, as the prompt requires.
- My re-fetches: (i) `https://softmax.com/battlecode/bc23` raw HTML has no iframe but its SSR
  playlist[0] is this run's coworld `cow_93baa4e4-…` v0.6.0 — now featuring the **round-3**
  episode (5a832bc6/b17974b9), so the featured match is live and updating; (ii) the session POST
  returns `ready: true` with viewer_url
  `…/v2/coworlds/replays/static/cow_93baa4e4-…/sha256%3Aa4ae44ab…/index.html?v=2#replay=<s3>` —
  the static route, `<sha>` byte-identical to `STATE.coworld.manifest_sha`, not a
  `/client/replay` pod URL. The `#replay=` fragment form is the documented post-2026-08-28 shape
  of the same static route (playbooks/observatory-api.md §Featured match). (iii) cow_93baa4e4 is
  `canonical: true` at v0.6.0; all five older versions are `canonical: false`.

### 7. Certification declared the static bundle — TRUE stands
- Read from the **committed** `runs/2026-09-08-battlecode-2023/release-result.json`
  (commit 4c0140b, phase 40's artifact copy — the required source, not /tmp):
  `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
  /client/replay and /replay not required)` — contains the required string verbatim. I re-ran
  the jq myself on the committed file.

### 8. Viewer executed and judged — TRUE stands
- Run 34256712314 (viewer-check.yml, Metta-AI/coworld-builder): I verified via gh —
  `status: completed, conclusion: success`, `createdAt 2026-09-08T17:22:37Z` equal to the
  dispatch instant VERIFY records. Artifacts committed at
  `runs/2026-09-08-battlecode-2023/viewer-check/` (commit c641e28): viewer-smoke.json +
  viewer-smoke.png + stdout/stderr.
- I re-ran the readout jqs on the committed json myself: `loaded: true` (1368 ms), signals
  `data_replay_loaded: "true"`, `bridge: ["ready"]`, `bridge_error: []`, `failure: no failure`.
  Three scrub clocks all differ — `3:55 GAME 1 OF 3 — SCATTER` / `2:04 GAME 2 OF 3 —
  HIDEANDSEEK` / `FINAL MATCH OVER` — naming the replay's maps in play order, plus a 15 s soak
  advancing round 2 → 318 → 366. Gates (a) and (b) both hold on evidence I read directly.
- I viewed viewer-smoke.png myself: a full broadcast frame at end-of-match — scorebug strip with
  `CLAN ASH … FINAL MATCH OVER … daveey 4 / daveey-1 95` (exactly `result.points[*][2]`), winner
  endcard `CLAN BASIL — DAVEEY-1` with the correct tiebreak verdict line, two doctrine cards in
  prose, a stat block matching the replay's game-3 row (`islands_held_end [0,9]`,
  `anchors_placed [0,9]`), a feed column whose lines match the replay's late events round-for-
  round (island 13 @1984, anchor @1953, island 8 @1926, island 15 @1867, island 4 @1812), the
  populated dimmed board behind the scrim, and the starter's transport strip + momentum-graph
  scrubber at `round 2000 / 2000`. It is the paintbot/raid/hive broadcast chrome, not a rewrite —
  the gridlock test passes. The judgment paragraph in VERIFY.md is accurate to the pixel evidence.

## The verifier's two findings — weighed against the definition of done

### FINDING A (doctrine-envelope seats playing schema-default sheets) — correctly NON-BLOCKING
I verified the table independently from the round-1 and round-2 replays: r1 seat 0 (daveey)
submitted `{"protocol":…,"doctrine":{…}}` and played the default sheet
(balanced/45/…/anchor_round 400); r2 seat 1 (daveey-1) did the same. Exactly as VERIFY states,
once to each champion. Weighed against SPEC item 4 as written — valid JSON ✓, protocol match ✓,
`reason: complete` ✓, champion seats non-scripted (`policy: llm`) ✓, non-trivial content ✓ (the
submitted envelopes contain full custom doctrines; the affected seat's counterpart played a fully
custom sheet each round), not-all-fallbacks ✓ (`fallbacks [0,0]`, 2/2 decisions on attempt 1) —
no item of the definition of done is falsified. The default-on-unknown-key behaviour is designed
and documented (design.md §doctrine sheet). At the current head it is also **not recurring**: the
round-3 replay has both seats on their own non-default sheets. It remains a real quality
observation for phase 30 (envelope unwrapping, and `defaults_applied` under-reporting), correctly
routed as non-blocking.

### Seven legibility items (check 8) — correctly NON-BLOCKING
I confirmed items 1 (bc26 nouns "the alliance held / kings / cheese delivered / cats damaged" on
the bc23 endcard), 2 (17-digit float scores), 3 (doctrine cards clipping mid-sentence), 4
(winner's stat block below the fold) and 5 (HUD bleed-through) directly in viewer-smoke.png.
Item 8's gate as written is: loaded=true, three differing clocks, and a judgment paragraph that
the picture is legible and shows the game. All three hold — the frame is readable, names the
right winner with the right numbers, and its feed reconciles line-for-line with the replay JSON.
The wrong-year caption line is one row of zeros amid otherwise-correct bc23 content; it does not
make the page a different product (the chrome is verbatim the starter's), so it is a phase-30
item-14 legibility finding, not an item-8 falsifier. VERIFY classifies all seven exactly there.

## What I re-fetched (all fresh this adjudication)
- `GET /rounds?league_id=league_e3244a55-…` (check 1) — 3 completed, 0 failed/discarded.
- `GET /divisions/div_dc5f977f-…/leaderboard` (check 2) — both champions ranked, no fillers.
- `GET /rounds/round_57f7e9e5-…/episodes` + `GET /episode-requests/ereq_a720bebc-…` (check 3);
  also reproduced the flat-route `Method Not Allowed`.
- Replays b17974b9 (round 3), 16e08a05 (round 2), f62806cf (round 1) from S3 — strict-parsed,
  reasons/fallbacks/sheets audited (check 4 + FINDING A audit).
- `GET /episode-requests/ereq_a720bebc-…/artifacts/logs` elevated (check 5) — CLEAN.
- `https://softmax.com/battlecode/bc23` SSR payload + `POST /coworlds/replays/session` +
  `GET /coworlds` (check 6) — static route, ready:true, sha = manifest_sha, canonical v0.6.0.
- Committed `release-result.json` (check 7) and committed `viewer-check/` json + png (check 8);
  `gh run view 34256712314` → success; `gh api …/tools/ci/policies.json?ref=47f36001` →
  champions PLAYER_PROMPT, fillers PLAYER_SCRIPTED.
- STATE.json ids (league/division/cow/manifest_sha/policies) — all consistent with the evidence
  above.

## Non-blocking observations (for the record, none tied to a failed checklist item)
- The prompt's literal check-3/check-4 commands (`?round_id=` filter, `.type=="decision"`,
  `.results`) do not run as written against this deployment/coworld schema; the verifier's
  documented translations are faithful. Worth folding back into prompts/60-verify.md or the
  playbook so the next run doesn't rediscover the 405.
- FINDING A's "roughly half the seats" framing is already stale in the right direction: round 3
  had zero envelope-wrapped sheets.

BLOCKING: 0
