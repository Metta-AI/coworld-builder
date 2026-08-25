blocking: 0

# Phase 60 verdict — cooperative-hunting
Judge: fresh context. Checklist: docs/SPEC.md §Definition of done, per prompts/60-verify.md.
Independent read (checks 1–5, 7, 8 evidence re-fetched; viewer-smoke.png viewed) written **before**
reading VERIFY.md: yes. Check 6's attempt-3 evidence (SSR playlist grep + session POST) was
reproduced by me **after** reading VERIFY.md, disclosed as such below.

## Per-check table

| # | Check | Verifier | Judge | Reasoning (one line) |
|---|---|---|---|---|
| 1 | ≥2 completed rounds post-filler | TRUE | **TRUE** | Re-fetched `/rounds`: rounds 2,3,4 `completed`, round 1 `failed` ("Temporal RoundWorkflow failed before settling the round.", quoted verbatim in VERIFY); re-fetched `/leagues/$L/filler-policies` → biggame:v2 `1ccdd2e4…` + sidekick:v2 `b0ebdd65…`, neither a champion version; ≥2 holds even discounting round 2 (see A2). |
| 2 | Both champions ranked | TRUE | **TRUE** | Re-fetched leaderboard: exactly two rows — daveey / pack-caller:v2 / 1002.80 / 3 rounds and daveey-1 / quartermaster:v2 / 997.20 / 3 rounds; no filler rows at all ("fillers absent" branch satisfied). |
| 3 | Latest round ereq completed w/ replay | TRUE | **TRUE** | Re-derived R=round_c00de3a5… (round 4), EREQ=ereq_22b05732…: `status:"completed"`, non-null S3 `replay_url`, seats 0/1 = pack-caller/daveey and quartermaster/daveey-1 (`is_filler:false`), 4 filler seats; replay `.config.players` = `["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]` — I confirmed this in the replay bytes myself. |
| 4 | Replay bytes valid, show the game | TRUE | **TRUE** | Re-downloaded 1,199,042 bytes, `jq -e` strict-parses; `results.reason=="complete"`; 48 plan events, 48 `src:"llm"`, 0 fallback plans/events, `results.fallbacks=[0,0,0,0,0,0]`, `llm_requests:49`; plan `say` text is game-specific side-assignment talk, not boilerplate; envelope identity `cooperative_hunting`/`staghunt`/`cooperative-hunting/1` matches manifest `.game.name` + `.variants[0].id` (re-fetched) — see W-a on the absent `protocol` key. |
| 5 | Hosted game log clean | TRUE | **TRUE** | I re-fetched round 4's log myself (elevated header) and grepped the raw bytes for all four patterns: **0 hits, CLEAN** — the check's subject (latest round) needs no exception; rounds 2–3 wrinkle judged at W-b. |
| 6 | Public page uses static replay path | TRUE | **TRUE** | I reproduced attempt 3: page HTML SSR `playlist` carries featured match `episodeId b4f9020e…` round 4 with the same replay URL, and the session POST returns `viewer_url` = `…/v2/coworlds/replays/static/cow_d5e3a72d…/sha256%3A0dfeeb8e…/index.html?replay=<s3 url>&v=2`, `ready:true` — static path with cow_id + manifest sha, no `/client/replay` substring; raw-HTML grep empty for me too (client-rendered, the documented fallback applies); source used is recorded, as required. Attempt-2 paste nit at A1. |
| 7 | Certification declared static bundle | TRUE | **TRUE** | Read the committed `runs/2026-08-24-cooperative-hunting/release-result.json` myself: `.certify.replay_liveness` = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"; `version 0.1.4`, `manifest_sha sha256:0dfeeb8e…` byte-identical to the sha in check 6's viewer URL. |
| 8 | Viewer executed + spectator judgment | TRUE | **TRUE** | Committed `viewer-smoke.json`: `loaded:true` (both `data_replay_loaded:"true"` and bridge `ready`), `failure:null`, and three **differing** scrub clocks (`ROUND 1 OF 3 … 3/2880` → `ROUND 2 OF 3 … 1478/2880` → `ROUND 3 OF 3 ROUND CARD · 2880/2880`) — both halves of the TRUE condition hold; its `url` is byte-identical to check 6's `viewer_url` incl. `&v=2`; CI run 32812865316 = `completed/success` (checked via gh); artifacts committed; my own look at the png below. |

## Independent spectator judgment (from viewer-smoke.png, my own eyes)

The frame is legible and it is unmistakably this game rendered in the starter's chrome, not a
rewrite. Top: a six-seat scorebug split around a centred clock reading ROUND 3 OF 3 / ROUND CARD ·
2880 / 2880, each seat with colour dot, alias, policy name and a bar+number (Cog-F 3, Cog-D 3,
Cog-E 19 left; Cog-A 15, Cog-C 1, Cog-B 21 right). Centre: a "HUNT OVER" endcard with the sign
line "SCORE IS EVERY CAPTURE YOU STOOD A SIDE FOR. HIGHER IS BETTER." and ranked standings
(#1 Cog-E sidekick 31 … #6 Cog-C big_game_hunter 3) — those six numbers are exactly the replay's
`results.scores` re-ranked, which I checked against the bytes myself, so picture and record agree.
Behind the dimmed overlay a populated tile forest (rock border, trees, scattered prey sprites) is
visible, and a faint "HUNT OVER — complete" chip sits lower-right. Bottom: the paintbot/raid/hive
transport strip — restart, step-back, pause, +5s, step-forward, loop, fast-forward, a highlighted
`spoilers` toggle, tick counter 2999/2999, the 1×–16× speed rail — and a full-width scrubber
labelled HUNT with the playhead parked at 100 %. The screenshot is the endcard frame, so it proves
the finish is readable rather than mid-play action; motion is established separately by the three
differing scrub clocks, and the mid-episode content by the replay's 48 LLM plan/catch/moose_gut
events. A first-time watcher can read who won, by how much, and what the score means from this one
frame. Not empty, not frozen, not a different product.

## Findings

**W-a (wrinkle a: no top-level `protocol` key) — ADVISORY, not blocking.** design.md pins the
replay envelope (L549–570) with `format`/`coworld`/`variant` and **no** `protocol` key, so the
prompt's `jq -r '.protocol'` cannot apply verbatim to this game; the verifier's substitute —
`.coworld`==manifest `.game.name` (`cooperative_hunting`), `.variant`==`.variants[0].id`
(`staghunt`) — is the correct available reading of "protocol matches the manifest", and I
reproduced both sides of it. The check's intent (the replay identifies itself as this coworld) is
established.

**W-b (wrinkle b: rounds 2–3 `falling back` lines) — ADVISORY, not blocking.** Check 5's subject
is the latest round's log (round 4), which I fetched and grepped myself: 0 hits, literally CLEAN
with 48/48 LLM decisions and 0 fallbacks in the corresponding replay. The rounds 2–3 lines fall
under SPEC item 5's explicit escape ("a documented platform-wide cause checked against another
LLM coworld"): I re-fetched hanabi's log (`ereq_3c48da04…`, 74,993 bytes, concurrent with round 2)
and found the identical model + identical Bedrock 429 message verbatim. The verifier also did
what the prompt orders for this symptom — kept polling inside the 75-minute bound until a clean
round existed — rather than going Blocked.

**W-c (wrinkle c: round 1 failed pre-filler) — ADVISORY, not blocking.** The failed round is
recorded with its `error` verbatim as check 1 requires, is excluded from the count, and three
completed rounds remain — one more than the ≥2 the checklist demands. The ordering hazard is the
documented one (`playbooks/observatory-api.md` §6); it cost ladder time, nothing else.

**A1 (check 6, attempt 2 paste/command mismatch) — ADVISORY.** The pasted command
`jq -r '.entries[]|select(.name=="cooperative_hunting")|…'` cannot have produced the pasted output
against today's API: `/coworlds` returns a **bare array** (I fetched it; `.entries[]` errors with
"Cannot index array with string \"entries\""), and the list entries carry no
`replay_viewer`/`featured_match` keys (the pasted `null`s are what a tolerant filter projects for
missing keys). The verifier evidently ran a corrected filter and pasted the checklist's canonical
command. No weight rests on attempt 2 — it is recorded "for completeness" and its nulls are
documented platform-wide non-evidence — and attempt 3, which carries the verdict, reproduces
exactly. A paste in VERIFY.md should be the command actually run; flagging for hygiene only.

**A2 (check 1, ordering inference overreach) — ADVISORY.** VERIFY infers "the fillers were
registered between 04:48:03Z and 04:48:24Z" from round 2 having seated six agents. That
over-claims: a round row's creation does not require fillers to exist at creation — seats are
filled when the episode is scheduled, so six seats prove only that fillers existed before round
2's **episode** was seated (round 2 completed 04:55:33Z, after the 04:49:31Z log line, so no
contradiction needs explaining away). The verdict is unaffected: all three completed rounds seated
the four filler seats, and rounds 3 and 4 alone — created 05:03Z and 05:18Z, unambiguously after
any reading of the registration time — satisfy ≥2.

**A3 (replay envelope `version: "0.1.0"` vs coworld 0.1.4) — ADVISORY.** Disclosed by the
verifier itself; I confirmed the bytes say `"version":"0.1.0"` and that design.md L551 pins
exactly that constant as the envelope schema version. Nothing in the definition of done reads
this field; correctly routed to phase 80 as a legibility nit.

## Fetch disclosure

I re-fetched with $SOFTMAX_TOKEN: `/rounds`, `/divisions/$D/leaderboard`,
`/episode-requests?round_id=` + the ereq detail, the S3 replay bytes, round 4's artifacts/logs
(elevated), `/coworlds` + the coworld detail, `/leagues/$L/filler-policies` (elevated), hanabi's
artifacts/logs (elevated), the public page HTML (both slug spellings' behaviour confirmed for the
hyphenated one), and the replays/session POST; plus `gh run view 32812865316` (success). Every
paste I tested against a live re-fetch reproduced, except attempt 2's command form (A1).

## Verdict

All eight checks of SPEC §Definition of done are TRUE at head, each on evidence I re-fetched or
read from the committed artifacts myself. The three disclosed wrinkles are honest disclosures,
none blocking. Findings A1–A3 are hygiene/legibility advisories, none tied to a failing checklist
item.

BLOCKING: 0
