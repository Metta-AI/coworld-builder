blocking: 0

# Phase-60 verify verdict — smac-starcraft-micro
Judge pass: 2026-08-27, fresh context. Checklist: `docs/SPEC.md` §Definition of done, as
commanded by `prompts/60-verify.md`. Evidence audited: `VERIFY.md` (re-verify pass of
2026-08-27T11:23Z–11:28Z), the committed exhibits, and my own re-fetches. Independent read of
the exhibits and re-fetches was formed before accepting any VERIFY.md conclusion. Ladder
drift since VERIFY (round 7 completed 11:33:44Z, MMR now 1032.74/967.26, featured match now
r7) was observed and is expected, not a discrepancy.

## Standing blocking findings

None.

## Check-by-check audit (independent re-fetch where possible)

| # | VERIFY claim | My verification | verdict |
|---|---|---|---|
| 1 | 5 completed rounds (r2–r6), r1 failed Temporal race, fillers set before every counted round | Re-fetched `/rounds?league_id=…`: now 6 completed (r2–r7), r1 `failed` with the exact error string VERIFY quotes. Re-fetched round-2 ereq (`ereq_e860f660…`, created 10:13:39.296Z): carries both filler UUIDs `2964b7ba…` and `a1ecf538…` = `STATE.policies.filler_version_ids` — fetched proof fillers preceded the earliest counted round, independent of the batch-timestamped log lines | TRUE stands |
| 2 | daveey-1 1018.43 / daveey 981.57, 5 rounds each, fillers absent | Re-fetched leaderboard (bare list): daveey-1 1032.74 rank 1 / daveey 967.26 rank 2, 6 rounds each (drift = one more round). Both champions present, `rounds_played ≥ 1`, neither filler on the board | TRUE stands |
| 3 | `ereq_805f41dc…` (round 6) completed, S3 replay_url, champions seats 0–1 `is_filler:false`, three filler seats `is_filler:true` | Re-fetched both the round-6 sub-resource and the ereq detail: byte-for-byte the same status, replay_url, participants and participant_scores VERIFY pastes. Round 6 was the latest completed round at VERIFY time; round 7 postdates it. The `?round_id=` → sub-resource deviation is documented and still evidence-by-fetch | TRUE stands |
| 4 | Binary `COWLDSMC` replay; design-declared substitute; protocol/v1, reason `complete`, enemyKilled 5/5, 46/46 champion directives `llm`, 0 fallbacks | Re-fetched the S3 bytes (93871 B, magic `COWLDSMC`), fresh-cloned `Metta-AI/cogame-smac-starcraft-micro` (head `545afa9f…`, same commit VERIFY names), ran `tools/replay_summary.py`: exit 0, `jq -e` strict-parses, `protocol smac-starcraft-micro/v1`, `reason complete`, `enemyKilled 5`, 115 directives {llm:46, scripted:69}, seats<2 sources `["llm"]` only, all 46 with non-empty notes, `fallbacks 0`, `fallbackTurns [0,0,…]`. The substitute clause exists verbatim at design.md ~L982–992 ("The phase-60 substitute for SPEC §Definition of done check 4") and the deadline-acceptable clause at ~L346; neither exception was actually needed (reason is `complete`) | TRUE stands |
| 5 | CLEAN — 0 matches for all four patterns on raw and unescaped body; two `repaired:` lines replace the former `falling back`; 46/46 Bedrock 200s | Re-fetched `/artifacts/logs` with the elevated header (HTTP 200, 103740 B — same size). Grep on the raw body: CLEAN. Decoded the `b'…'`/`b"…"` container blocks myself: CLEAN again; both `smac llm: seat 0 repaired: reply named no commanded cog; kept last turn's directive on turn 0` lines present; 46 × `HTTP/1.1 200 OK`, zero 4xx/5xx; battle-done and Replay-written lines match VERIFY's excerpt. (My decode yields 527 physical lines vs VERIFY's 199 — decode methodology, same content.) No exception invoked; none needed | TRUE stands |
| 6 | Client-rendered page; SSR playlist featured match; `replays/session` returns static viewer URL with the 0.1.3 sha; not a pod URL | Re-fetched `https://softmax.com/smac-starcraft-micro` (200, no iframe in served HTML — client-rendered as claimed; SSR playlist present, now r7/0.1.3). Re-fetched `/coworlds`: 0.1.3 `cow_345bfc54…` is the only canonical, `replay_viewer`/`featured_match` null platform-wide as claimed. Re-POSTed `/coworlds/replays/session` with the round-6 replay: identical `viewer_url` — `/v2/coworlds/replays/static/cow_345bfc54…/sha256%3A3c1e7703…/index.html?replay=…&v=2`, `ready:true`; sha matches `STATE.coworld.manifest_sha`; not `/client/replay` | TRUE stands |
| 7 | Committed `release-result.json` (0.1.3): `Replay liveness: skipped (static replay bundle declared…` | Read the committed file: string present verbatim; `version 0.1.3`, `cow_345bfc54…`, `manifest_sha sha256:3c1e7703…` all match STATE and the check-6 iframe sha; `canonical:true`, `hosted_smoke:passed`, cert transcript 10/10 pass. Release run `33065622007` confirmed on GitHub: success, `headSha 545afa9f…` (the fix commit) | TRUE stands |
| 8 | Run 33067338841, `loaded:true` @3310 ms, three differing clocks, judgment paragraph from the png | Run 33067338841 confirmed: success, created 11:25:59Z (matches the dispatch-then-poll narrative). Downloaded its `viewer-check` artifact fresh: `viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt` all **byte-identical** to the committed copies — the exhibits are the real CI output, and the json's `.url` is exactly the check-6 iframe src. `loaded:true`, `data_replay_loaded:"true"`, `failure:null`; three scrub clocks all differ (battle 1/turn 1 → battle 2 "FINAL 3 V 0" turn 5 → battle 2 5V5 turn 7). I viewed the png myself: it matches the judgment paragraph — scorebug (daveey 4 DMG / daveey-1 0 DMG / Baseline 20 DMG), clock `0:29 BATTLE 2/3 · DEFAULT · 5 V 5 · TURN 7/12`, OURS 480/480 (100%) vs THEIRS 436/480 (91%) bars, mid-arena melee with damage spray and tracers, a legible `hold` speech label plus enemy-tag labels, killfeed `BLADE-gamma: charge`, transport strip with spoilers toggle and `RED WINS 735 / 3007` counter, 1×–16× speed buttons, ARMY HP LEAD momentum graph — the starter's chrome, not a rewrite. The harness-gap claim checks out: `templates/tools/ci/viewer_smoke.mjs:425` queries `#feed, .feed, #log`; the repo's element is `#killfeed` (`client/replay_broadcast.html:438`), so `feed_lines:0` is a probe gap, and the killfeed visibly renders in the png | TRUE stands |

## Refuted

None — no VERIFY evidence line failed reconciliation with a fresh fetch. Every number, id,
sha, string and readout I re-fetched matched, modulo declared ladder drift.

## Advisories (non-blocking)

- [check 1] The phase-50 log lines are batch-timestamped 10:15:53Z, *after* rounds 1–2 fired
  (10:13:00Z/10:13:38Z), so the log alone cannot prove filler-before-round ordering; the
  proof rests entirely on the fetched round-2 ereq carrying both filler UUIDs at
  10:13:39.296Z — which holds, and VERIFY correctly leads with it. Log-hygiene nit only.
- [check 7] The 0.1.3 `release-result.json` lists all four policies at **v4**, while STATE,
  the leaderboard and every episode run **v3** version-UUIDs. The re-release minted new,
  unused policy versions; league entrants are pinned to v3 so no functional effect, but a
  future reader comparing STATE labels to the release artifact will trip on it.
- [check 8] Confirmed and carried forward from VERIFY: (a) the `#feed,.feed,#log` vs
  `#killfeed` harness selector gap (fix belongs in `templates/tools/ci/viewer_smoke.mjs`);
  (b) the 100 % scrub lands mid-battle-2, so the endcard is never exercised by the probe;
  (c) the repair line "kept last turn's directive **on turn 0**" names a previous turn that
  does not exist on turn 0 — harmless here (0 fallbacks in the replay) but worth a look.
- [check 8] The 50 % scrub readout (`FINAL BATTLE 2/3 · 3 V 0`) sits *ahead* of the 100 %
  readout (`0:29 BATTLE 2/3 · 5 V 5 · TURN 7/12`) in game time — the shell's percent→tick
  mapping is non-monotonic across the three-battle timeline. The check only requires the
  readouts to differ (they do), but the mapping is a spectator-legibility oddity.

## Verdict

All eight checks are supported by fetched (or CI-executed) evidence, and every line I could
re-fetch reconciled. VERIFY.md's evidence is genuine, current at head, and correctly scoped;
the two design-declared clauses it leans on (binary-replay substitute, deadline-acceptable)
exist in design.md and only the first was needed. Zero blocking findings.

BLOCKING: 0
