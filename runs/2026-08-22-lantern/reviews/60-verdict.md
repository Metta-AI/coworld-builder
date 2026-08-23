blocking: 0

# Phase 60 verdict — lantern (run 2026-08-22-lantern)

Judge adjudication, fresh context, 2026-08-23. VERIFY.md re-read against SPEC §Definition of
done item by item, with live re-fetches of every claim that could be re-fetched. All re-fetches
were made in this session with `$SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`, and the
elevated header where the route needs it. Independent read of the evidence was formed from the
live API/S3/bundle responses before crediting VERIFY.md's phrasing.

Head facts confirmed: coworld `lantern` v0.1.4, `cow_d1fe527f-ee07-42ff-804d-f40be734d05f`,
`canonical: true`, `manifest_hash sha256:8911282…4af286f4` (matches STATE.coworld.manifest_sha);
league `league_16893be5-934d-43b4-9155-d27f600ffffe`;
division `div_af46a8ef-67ec-4780-9c72-0cf70e260999`.

---

## 1. ≥2 completed rounds after the fillers were set — PASS

**Claim:** rounds 2 and 3 `completed`; round 1 `failed` pre-fillers and is excluded.
**Re-checked live:** `GET /rounds?league_id=$L&limit=20` →
`[.entries[]|select(.status=="completed")]|length` = **2**; the completed rounds are
`round_93bc2d0b-7454-41e2-8be6-4612d6b61b70` (#2, completed 2026-08-23T03:38:19Z) and
`round_b878a6b2-fa79-4fe1-a015-d6c0f7ac23ae` (#3, completed 2026-08-23T03:53:40Z). Round 1 is
`failed` with error `Temporal RoundWorkflow failed before settling the round.` — exactly as
VERIFY.md quotes — and had a single entrant, consistent with the pre-filler cause.
`GET /leagues/$L/filler-policies` (elevated) reproduces exactly two fillers: `lantern-warden:v3`
(`72a889c0…`) and `lantern-moth:v3` (`713f2616…`), neither a champion version. `log.md` line 47
records `fillers registered BEFORE trigger` at 03:37:33Z; round 2 was created 03:36:27Z but
seats both champion versions and all four filler seats (check 3's participants), so the fillers
were in force for both counted rounds. The round-1 exclusion is documented and reproduces.

## 2. Both champions ranked; fillers absent/Baseline — PASS

**Claim:** two-row leaderboard, `daveey` rank 1 and `daveey-1` rank 2, both `rounds_played 2`.
**Re-checked live:** `GET /divisions/$D/leaderboard` →
```
1	daveey	lantern-warren:v3	1030.5304984710244	2	2.0
2	daveey-1	lantern-owlnight:v3	969.4695015289755	2	0.0
```
Identical to VERIFY.md to the last decimal. Both champions ranked with `rounds_played ≥ 1`;
no filler rows at all (absent — the passing branch of the SPEC's "absent or labelled Baseline").

## 3. Latest round's episode request completed with a replay — PASS

**Claim:** `ereq_d3790a64-847e-4954-8373-30ace92e84de` on round 3 is `completed` with a replay
URL and correct participants.
**Re-checked live:** `GET /episode-requests/ereq_d3790a64…` → `status: "completed"`,
`replay_url: https://softmax-public.s3.amazonaws.com/replays/eb43b47f-b765-4820-a0ca-9e8077f26200.replay`,
participants: position 0 = `lantern-warren` v3 / `daveey` (`is_filler: false`), position 1 =
`lantern-owlnight` v3 / `daveey-1` (`is_filler: false`), positions 2–5 = `lantern-warden` ×3 +
`lantern-moth` v3, all `is_filler: true`. Matches VERIFY.md exactly; the fillers render
spectator-side as `Baseline`…`Baseline (4)` per the replay's `results.names` (re-fetched in
check 4).

## 4. Replay bytes valid and show the game — PASS

**Claim:** 313,685 bytes of strict UTF-8 JSON, `protocol lantern.replay.v1` matching the
manifest, `results.reason complete`, champion seats 100 % LLM orders, zero fallbacks.
**Re-checked live:** fetched the replay from S3 → HTTP 200, 313,685 bytes; `jq -e .` parses
clean (strict parser); `.protocol` = `lantern.replay.v1`; `.results.reason` = `complete`,
`.results.end_rule` = `full_time` (no deadline exception relied on). The coworld detail's
manifest carries `lantern.replay.v1` at `manifest.game.protocols.global.value`, so the protocol
matches the manifest. Order sources by seat, reproduced exactly:
seat 0 → 28/28 `llm`, seat 1 → 29/29 `llm`, seats 2–5 → all `scripted`;
`[.events[]|select(.type=="fallback")]|length` = **0**;
`results.policy_kinds` = `["llm","llm","scripted","scripted","scripted","scripted"]`;
`results.llm_turns` = `[28,29,0,0,0,0]`; `results.fallback_turns` all zero;
`results.names` = `["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]`.
The documented adaptation (lantern uses `order` events with `source` ∈ {llm, scripted, fallback}
instead of a `decision` type) reproduces and is faithful to the check's intent: the champion
seats' decisions are non-scripted, non-trivial, and not fallbacks — there are literally none.

## 5. Hosted game log clean — PASS

**Claim:** zero matches for the four failure strings, raw and decoded; 57 Bedrock calls all 200.
**Re-checked live:** `GET /episode-requests/$EREQ/artifacts/logs` (elevated) → HTTP 200,
118,926 bytes; `grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'`
→ **CLEAN** on the raw artifact, and **0** matches on my own independently decoded copy of the
repr blocks. All four containers present (`coworld-init-config`, `bedrock-sidecar`, `game`,
`worker`); 57 `bedrock_sidecar_complete` markers = 28 + 29 = the champion seats' LLM order count
from check 4. No exception invoked; none needed.

## 6. Public page uses the static replay path — PASS

**Claim:** raw-HTML iframe grep is empty (client-rendered); the SSR payload's `playlist[0]` is
featured match `lantern.r3.e1`; `POST /coworlds/replays/session` returns the static viewer URL.
**Re-checked live:** `https://softmax.com/lantern` → HTTP 200, ~343 KB; iframe grep empty
(reproduces — the prompt's own §6 anticipates this and names the fallback); SSR payload contains
`playlist":[{"episodeId":"604d4282…","coworldName":"lantern","coworldVersion":"0.1.4",
"replayUrl":"…eb43b47f….replay","roundNumber":3,…,"code":"lantern.r3.e1","matchup":{…daveey…}}`
— featured match present with a two-player matchup. The session POST reproduces byte-for-byte:
`viewer_url` =
`https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_d1fe527f-ee07-42ff-804d-f40be734d05f/sha256%3A891128215115bf6b75a1e51bd0299ba909b4b7595fbcd30d615ffe454af286f4/index.html?replay=…eb43b47f….replay&v=2`,
`ready: true`. That is the required
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` shape with `<sha>` = the
coworld manifest_hash (documented gotcha) and **no** `/client/replay` pod URL anywhere. The
documented adaptations (working host `api.observatory.softmax-research.net`;
`replay_viewer`/`featured_match` null platform-wide in `GET /coworlds`) are accepted as
documented and do not affect the pass. `canonical: true` on 0.1.4 also confirmed live.

## 7. Certification declared the static bundle — PASS

**Claim:** the committed `runs/2026-08-22-lantern/release-result.json` contains the marker.
**Re-checked:** the file is committed in the run directory;
`jq -r '.certify.replay_liveness'` →
`Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`
— contains the required literal `Replay liveness: skipped (static replay bundle declared`.
`.certify.ok` = `true`. Read from the committed copy, exactly as the prompt requires (not /tmp,
no `gh run download` needed).

## 8. Spectator judgment — PASS

**Claim:** legible replay narrative from three fetches; 15/15 bundle assets 200 with real bytes;
postMessage bridge with ready signal present.
**Re-checked live:**
- *(a)* From the re-fetched replay: the event stream reproduces (368 sound, 156 order,
  56 crate_push, 42 turn_start, crate_pry/crate_lock/crate_break, spot/found, half/act
  structure, `end` at t=5040); `results` shows `winner: 0`, `halves_played: 2`, scores
  0.693/0.307 zero-sum by side, hidden-time and finds stats — the champion seats' activity
  reads as the hide-and-seek game the design describes.
- *(b)* Bundle assets spot-checked fresh against the viewer_url base:
  `index.html` 200/109,341 B; `static_replay.js` 200/9,831 B; `lantern_replay.wasm`
  200/184,932 B — `file` confirms `WebAssembly (wasm) binary module version 0x1 (MVP)`;
  `art/cog_moth.png` 200/1,562 B — `file` confirms `PNG image data, 128 x 128, 8-bit RGBA`.
  Sizes match VERIFY.md's table exactly; no 0-byte or HTML-error-page body.
- *(c)* Fetched `static_replay.js`: `grep -c 'coworld-replay'` = **2**;
  `grep -n "tell('ready')"` hits at line **153**
  (`window.requestAnimationFrame(function () { tell('ready'); });`). The single-quote spelling
  is the documented adaptation of the check's double-quoted literal; the bridge and ready
  signal are present.
The judgment paragraph is written from the three fetches only — no DOM, browser, or screenshot
claims. Compliant.

---

## Notes (non-blocking)

- VERIFY.md's check-4 manifest-protocol grep output is pasted mid-word (`eplay bytes…`) — an
  artifact of the 60-char context window in the grep, not an evidence defect; I confirmed the
  protocol declaration independently at `manifest.game.protocols.global.value`.
- Round 2 (`created 03:36:27Z`) predates the `log.md` filler timestamp line (03:37:33Z, which
  logs the whole phase-50 batch), but its participant list seats all four fillers — the fillers
  were demonstrably in force for both counted rounds, which is what the check requires.

## Summary

| # | Definition-of-done item | VERIFY.md | Judge re-check | Verdict |
|---|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | TRUE | 2 completed (#2, #3), round 1 failed/excluded, fillers reproduce | PASS |
| 2 | Both champions ranked | TRUE | daveey & daveey-1, rounds_played 2 each, no filler rows | PASS |
| 3 | Latest round ereq completed w/ replay | TRUE | completed, replay_url set, participants correct | PASS |
| 4 | Replay valid, shows the game | TRUE | strict JSON, protocol match, complete, 57/57 llm orders, 0 fallbacks | PASS |
| 5 | Hosted log clean | TRUE | CLEAN raw + decoded, 57 Bedrock completes | PASS |
| 6 | Static replay path on public page | TRUE | SSR featured match + session POST static URL, no pod URL | PASS |
| 7 | Cert declared static bundle | TRUE | committed artifact carries the literal, certify.ok true | PASS |
| 8 | Spectator judgment | TRUE | events legible, assets 200/real bytes, bridge + tell('ready') @153 | PASS |

Every VERIFY.md claim I re-fetched reproduced at head; the documented adaptations all
reproduce and are faithful to the checks' intent. No blocking findings.

BLOCKING: 0
