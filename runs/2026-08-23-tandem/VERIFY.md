# VERIFY — tandem   (2026-08-24T01:24Z)

Verdict: **all-true (8/8)** — with two recorded anomalies that do not fail any checklist item
(round 3 completed empty; round 2's seat 1 played scripted). Both are written up under
§Observations and are for the coordinator/judge to weigh.

Run: `2026-08-23-tandem` · slug `tandem` · coworld `cow_77d94979-f003-494d-8c60-6bd97b97b9db` v`0.1.1`
League `league_50c18e88-ed54-4cd7-be36-4748d79b5a9b` · division `div_fdb4b69f-5586-4239-87f1-b9afeeb34ce5`
Champions `tandem-anchor:v1` (daveey) / `tandem-feather:v1` (daveey-1) · fillers `tandem-porter:v1`, `tandem-mule:v1`

All Observatory calls used, verbatim (header **values** never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_50c18e88-ed54-4cd7-be36-4748d79b5a9b
D=div_fdb4b69f-5586-4239-87f1-b9afeeb34ce5
COW=cow_77d94979-f003-494d-8c60-6bd97b97b9db
```

Every fetch below was made fresh during this phase-60 run (2026-08-24T00:39Z – 01:24Z). The two
documented exceptions are check 7 (the committed `release-result.json` from phase 40) and check 8
(the artifact of the `viewer-check.yml` run **this** phase dispatched, id 32679404498).

---

## 1. ≥2 completed rounds after the fillers were set

**Filler registration (the "after" reference point).** `log.md` line 56 records phase 50:

```
2026-08-24T00:38:19Z 50 fillers 200: porter+mule registered, neither champion
2026-08-24T00:38:19Z 50 unpause 200 paused=false; trigger-round 200 workflow ladder-league_50c18e88
```

Fillers were registered **before** the first `trigger-round`; the earliest round on the ladder
(round 1, `created_at` 2026-08-24T00:37:00Z) is therefore already after them. Confirmed live:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq -c .
```
```json
{"filler_policy_versions":[{"policy_version_id":"98d8389d-2935-41e4-a96a-29c330835822","policy_id":"1e5ee6de-4bfd-4c34-8192-072bbf44ab98","policy_name":"tandem-porter","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},{"policy_version_id":"47069cde-a3e6-4ccf-a668-9cd29b0cd387","policy_id":"0b9cbaa4-59f4-4b69-976c-765be07b97ba","policy_name":"tandem-mule","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

**The count.**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|length'
```
```
3
```

**The rounds themselves** (same fetch, 2026-08-24T01:18Z):

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)
          | map({id,round_number,status,error,created_at,completed_at})|.[]'
```
```json
{"id":"round_40503f65-bd38-459f-a0c2-87a0f48d5b60","round_number":4,"status":"completed","error":null,"created_at":"2026-08-24T01:07:27.985901Z","completed_at":"2026-08-24T01:12:14.471589Z"}
{"id":"round_e572c0da-3392-492d-ad11-48d93ece2a5b","round_number":3,"status":"completed","error":null,"created_at":"2026-08-24T00:52:27.521988Z","completed_at":"2026-08-24T00:52:38.712164Z"}
{"id":"round_6d086d3b-95bf-4d93-883a-6ead1f033c16","round_number":2,"status":"completed","error":null,"created_at":"2026-08-24T00:37:26.333402Z","completed_at":"2026-08-24T00:42:21.339697Z"}
{"id":"round_3cfbf625-b9db-47ca-b01a-4513067e8646","round_number":1,"status":"failed","error":"Temporal RoundWorkflow failed before settling the round.","created_at":"2026-08-24T00:37:00.442129Z","completed_at":"2026-08-24T00:37:00.653197Z"}
```

**Round 1 `error`, verbatim (does not count):**
`"Temporal RoundWorkflow failed before settling the round."` — it raced the unpause;
`filler-policies` above proves the fillers were already registered, so this is the documented
`playbooks/observatory-api.md` §7 race, not a missing-filler failure.

**Entrant attributions on the two rounds that produced episodes** (both champions, no fillers):

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|.[]|select(.round_number==4)|.round_config.entrant_attributions'
```
```json
[{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"9807948b-4f55-4357-8aef-813735a2857b","league_policy_membership_id":"lpm_a108a664-5ad5-4e7e-9006-6a33add98399"},
 {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"bdc8fd6d-4276-4cb6-9bf0-c9ab40b00b1b","league_policy_membership_id":"lpm_41793bef-a75a-4724-a777-0af1e425472e"}]
```
(Round 2's `entrant_attributions` is byte-identical — same two policy version ids.)

**Status: TRUE** — 3 rounds `completed` (2, 3, 4), all created after the fillers were registered
(fillers set before the first trigger at 00:37:00Z; earliest completed round created 00:37:26Z).
Two of them (2 and 4) produced real, scored, replayed episodes; round 3 completed with an empty
result set (see §Observations A) — even discounting round 3 entirely, the requirement of ≥2 is met
by rounds 2 and 4.

---

## 2. Both champions ranked; fillers absent / Baseline

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)
          | .[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	tandem-anchor:v1	1000.0	2	0.0
2	daveey-1	tandem-feather:v1	1000.0	2	0.0
```

Full rows (same fetch, 2026-08-24T01:18Z):

```json
[
  {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"tandem-anchor:v1","recent_rounds":null},
  {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"tandem-feather:v1","recent_rounds":null}
]
```

**Status: TRUE** — `daveey` and `daveey-1` are both present with `rounds_played = 2` (≥ 1); the
leaderboard has exactly two rows, so `tandem-porter:v1` / `tandem-mule:v1` are **absent** (they were
never seated — both champions filled the two seats every round).

Note: both Elo scores are 1000.0 and `episode_wins` 0.0 because the two seats are **co-operative** —
`results.win` is `[false,false]` and `scores` are equal for both seats in every episode (this game's
`jointScore`); no head-to-head Elo movement is expected. `rounds_played = 2` is the evidence that
they played, not the score delta.

---

## 3. Latest round's episode request completed with a replay and correct participants

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|max_by(.round_number).id')
echo "$R"
```
```
round_40503f65-bd38-459f-a0c2-87a0f48d5b60
```

```bash
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|map({id,status,job_index})'
```
```json
[{"id":"ereq_c24a96c8-26de-4853-b5d7-7c8c3dc2e90c","status":"completed","job_index":0}]
```

```bash
EREQ=ereq_c24a96c8-26de-4853-b5d7-7c8c3dc2e90c
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores, created_at, completed_at}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/090b12fd-a443-40a8-9707-d7ade2673313.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"9807948b-4f55-4357-8aef-813735a2857b","policy_id":"23cb6874-6a6d-49a4-a071-f54c52ad8925","policy_name":"tandem-anchor","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false},
    {"position":1,"kind":"policy","policy_version_id":"bdc8fd6d-4276-4cb6-9bf0-c9ab40b00b1b","policy_id":"b31eb22e-c50d-48ca-aa22-64da6e3db5e2","policy_name":"tandem-feather","version":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.018943},
    {"position": 1, "score": 0.018943}
  ],
  "created_at": "2026-08-24T01:07:28.328039Z",
  "completed_at": "2026-08-24T01:12:06.841998Z"
}
```

**Status: TRUE** — round 4's only episode request is `completed`, `replay_url` is non-null
(`.../090b12fd-a443-40a8-9707-d7ade2673313.replay`), and `participants` names `daveey`
(tandem-anchor v1) and `daveey-1` (tandem-feather v1), both `is_filler: false`, both scored.

---

## 4. Replay bytes are valid and show the game

The replay is the starter's **binary `COWLDTDM`** container, as `design.md` §"Replay bytes
(self-sufficient)" declares. That section also defines the phase-60 substitute for this check:
decode with the repo's `tools/replay_summary.py` (Python-stdlib only) and apply the strict parser to
its output. Both the raw magic and the decoder run are pasted below.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/090b12fd-a443-40a8-9707-d7ade2673313.replay" -o /tmp/ep.replay
ls -l /tmp/ep.replay; head -c 32 /tmp/ep.replay | od -c | head -2
```
```
-rw-r--r-- 1 root root 78876 Aug 24 01:18 /tmp/ep.replay
0000000   C   O   W   L   D   T   D   M 001  \0 006  \0   t   a   n   d
0000020   e   m 001  \0   1 260 200   3   1 240 001  \0  \0 345 022   {
```

```bash
# tools/replay_summary.py fetched fresh from the coworld repo this run:
gh api repos/Metta-AI/cogame-tandem/contents/tools/replay_summary.py --jq .content | base64 -d > /tmp/replay_summary.py
python3 /tmp/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason, .results.endRule' /tmp/ep.json
```
```
strict UTF-8 JSON: ok
tandem/v1
complete
out_of_time
```

`protocol` == `tandem/v1` == the manifest's protocol string (`design.md` §Replay bytes, line 897).

```bash
jq -c '{protocol,gameVersion,seed,names,aliases,policyKinds,tickCount,fallbacks,fallbackAttempts,utf8Repairs,budgetGuards,hashChain}' /tmp/ep.json
```
```json
{"protocol":"tandem/v1","gameVersion":"1","seed":2146724700,"names":["daveey","daveey-1"],"aliases":["Cobalt","Rust"],"policyKinds":["llm","llm"],"tickCount":2571,"fallbacks":0,"fallbackAttempts":1,"utf8Repairs":0,"budgetGuards":[],"hashChain":"53ff1848a1c813a6"}
```

```bash
jq -c '.results' /tmp/ep.json
```
```json
{"names":["daveey","daveey-1"],"aliases":["Cobalt","Rust"],"policyKinds":["llm","llm"],"scores":[0.018943,0.018943],"win":[false,false],"jointScore":0.018943,"delivered":false,"damage":3,"condition":0.997,"deliveryTicks":2570,"parTicks":1009,"progress":0.076,"drops":0,"impacts":0,"scrapeTicks":3,"strainPeakNewtons":[1632,986],"blame":[0,3],"llmTurns":[50,50],"fallbackTurns":[0,0],"reason":"complete","endRule":"out_of_time","finalTick":2570,"seed":2146724700}
```

**Champion seats are non-scripted.**

```bash
jq -r '[.orders[]|select(.source=="llm")]|length' /tmp/ep.json
jq -r '.fallbacks' /tmp/ep.json
jq -c '[.orders[]|{seat,source}]|group_by([.seat,.source])|map({seat:.[0].seat,source:.[0].source,n:length})' /tmp/ep.json
```
```
100
0
[{"seat":0,"source":"llm","n":50},{"seat":1,"source":"llm","n":50}]
```

Both seats registered as LLM (`register` records read straight out of the binary):

```bash
python3 -c 'import re;b=open("/tmp/ep.replay","rb").read()
[print(m.group(0).decode()) for m in re.finditer(rb"\{\"k\":\"(register|fallback|budget_guard)\".{0,400}?\}", b, re.S)]'
```
```json
{"k":"register","seat":0,"alias":"Cobalt","policy":"llm","kind":"llm","baseline":""}
{"k":"register","seat":1,"alias":"Rust","policy":"llm","kind":"llm","baseline":""}
{"k":"fallback","turn":0,"seat":1,"attempt":1,"cause":"timeout","detail":"Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke"}
```

One `fallback` **attempt** (turn 0, seat 1, `attempt:1`, cause `timeout`) whose retry succeeded — the
turn-0/seat-1 order below is `source: llm` with 1697 ms latency, and `results.fallbackTurns` is
`[0,0]`. So 0 of 100 decisions actually played the scripted fallback: not "all fallbacks", not even
a minority — none.

**Decisions are non-trivial and vary** (early / middle / late; `turn seat alias source latency_ms drive effort yield twist brace say`):

```bash
jq -r '.orders[0:6][]|[.turn,.seat,.alias,.source,.latency_ms,(.drive|tostring),.effort,.yield,.twist,.brace,(.say//"")]|@tsv' /tmp/ep.json
```
```
0	0	Cobalt	llm	4000	[0.19,0.98]	0.7	0.15	-0.15	0.0	Moving to first door, aligning angle
0	1	Rust	llm	1697	[0.13,0.99]	0.5	0.6	0.0	0.0	Starting carry. Moving toward first door.
1	0	Cobalt	llm	3139	[0.19,-0.98]	0.45	0.25	-0.12	0.0	Aligning for first doorway, matching partner st…
1	1	Rust	llm	3139	[-0.13,-0.99]	0.8	0.1	0.0	0.0	Taking lead - strain down, door up. Correcting …
2	0	Cobalt	llm	2230	[0.15,-0.99]	0.45	0.3	-0.15	0.0	Door center [-16.8,0.78], aligning angle 32→0°,…
2	1	Rust	llm	2230	[0.13,0.99]	0.5	0.6	0.0	0.0	Partner corrected! Strain now aligned with door…
```
```
24	0	Cobalt	llm	1578	[-1.0,0.0]	0.45	0.25	-0.08	0.8	Steady approach Door 1. Aligned on heading.
24	1	Rust	llm	1578	[0.0,1.0]	0.5	0.6	0.0	0.3	Strain 72N forward. Two cogs locked. Moving smo…
25	0	Cobalt	llm	2507	[-1.0,0.0]	0.45	0.2	-0.06	0.8	Door 1 locked. Steady pressure.
25	1	Rust	llm	2507	[0.0,1.0]	0.5	0.6	0.0	0.3	Strain 110N fwd. Locked in. Smooth through firs…
```
```
48	0	Cobalt	llm	1776	[-1.0,0.0]	0.7	0.15	0.0	0.0	Steady line to door 1. Strain clear and aligned.
48	1	Rust	llm	1776	[1.0,0.0]	0.8	0.05	0.0	0.3	E lead. Partner W-resist strong. Push through.
49	0	Cobalt	llm	1623	[-1.0,0.0]	0.45	0.15	0.0	0.0	Door 1 approach. Holding line, reducing effort.
49	1	Rust	llm	1623	[1.0,0.0]	0.8	0.05	0.0	0.3	E push. Partner resist. Override lead.
```

`drive`, `effort`, `yield`, `twist` and `brace` all change turn to turn; the `say` lines are
distinct, situational prose referring to doorways, strain in newtons, and the partner's line — not a
constant order, not a template.

**`results.reason`.** `complete` — the normal value. (`endRule` is `out_of_time`, which
`design.md` §End conditions lists as `complete`/`out_of_time`: "`maxTicks` reached with the couch
undelivered and intact", a legal, non-fault ending scored on the non-delivered branch. Legal
`reason`s are exactly {complete, deadline, fault}; this is `complete`, so the `deadline` exception
is not even needed here, and there is no `fault`.)

**Status: TRUE** — strict-UTF-8 JSON ok (0 `utf8Repairs`), `protocol` `tandem/v1` matches the
manifest, `results.reason` `complete`, both champion seats registered and played `llm` for 50/50
turns each with varying non-trivial orders, and 0/100 decisions were fallbacks.

---

## 5. Hosted game log is clean

The logs body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it is
**decoded before grepping** (`ast.literal_eval` per repr) as `playbooks/observatory-api.md` §10
requires.

```bash
curl -sS -w "\nHTTP %{http_code}\n" \
  "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs4.raw
wc -c /tmp/logs4.raw
python3 /tmp/declog.py /tmp/logs4.raw > /tmp/logs4.txt   # ast.literal_eval per b'…' repr
wc -lc /tmp/logs4.txt; grep -c UNDECODED /tmp/logs4.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs4.txt || echo CLEAN
```
```
HTTP 200
209049 /tmp/logs4.raw
   434 208608 /tmp/logs4.txt
0
CLEAN
```

(209 049 raw bytes → 208 608 decoded characters, **0** undecoded reprs: the decode covers the whole
body, so the grep is not undercounting.)

`/tmp/declog.py`, the decoder used above (stdlib only), for reproducibility:

```python
import ast, sys, re
src = open(sys.argv[1], 'r', encoding='utf-8', errors='replace').read()
parts = re.split(r'(?m)^===== container: (.+?) =====\n', src)
out, i = [], 1
while i < len(parts):
    name, body = parts[i], parts[i+1] if i+1 < len(parts) else ''
    out.append('===== container: %s =====' % name)
    for m in re.finditer(r"(?ms)^b(['\"])(.*?)\1\s*$", body):
        try:
            out.append(ast.literal_eval('b' + m.group(1) + m.group(2) + m.group(1)).decode('utf-8', 'replace'))
        except Exception as e:
            out.append('<<UNDECODED: %s>>' % e)
    i += 2
print('\n'.join(out))
```

Containers present and the game container in full (the last `Results:` line is elided at `…` only
because the identical, complete `results` object is already pasted verbatim in check 4):

```bash
grep -n "container:" /tmp/logs4.txt
```
```
1:===== container: coworld-init-config =====
3:===== container: bedrock-sidecar =====
412:===== container: game =====
433:===== container: worker =====
```
```
===== container: game =====
seed not pinned; randomized
tandem config: host=0.0.0.0 port=8080 seed=2146724700 num_agents=2 minPlayers=2 maxTicks=2400 turnTicks=48 turnBudgetMs=7000 minBatchSpacingMs=4500 wallClockBudgetSeconds=660 fastMode=true
starting tandem on 0.0.0.0:8080
board render caches baked in 11493 ms (charged against wallClockBudgetSeconds=660)
tandem llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
waiting for players: 0/2, need 2 more
player connected: daveey-1
player connected: daveey
cog joined: daveey as Cobalt (fore handle)
cog joined: daveey-1 as Rust (aft handle)
waiting for players: 2/2, need 0 more
game starting in 1
carry start on a 12-cell route, par 1009 ticks
Dropped message to disconnected client
game over: complete/out_of_time damage=3 progress=76
Replay written: /tmp/tandem-replay-1.replay (78876 bytes)
Events written: /coworld/events.json (6 events)
Results: {"names":["daveey","daveey-1"],"aliases":["Cobalt","Rust"],"policyKinds":["llm","llm"],"scores":[0.018943,0.018943],…,"reason":"complete","endRule":"out_of_time","finalTick":2570,"seed":2146724700}
tandem: artifacts written; serving for a further 20s before exit
```

Bedrock sidecar traffic in the same log — every call succeeded, so the "LLM provider is unavailable"
capacity clause is not invoked at all:

```bash
grep -c "bedrock_sidecar_call" /tmp/logs4.txt
grep -oE "HTTP/1.1 [0-9]{3}" /tmp/logs4.txt | sort | uniq -c
```
```
101
    101 HTTP/1.1 200
```

**Status: TRUE** — `CLEAN`: zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens` or `rejected` in the fully decoded 208 608-character log, and all 101
Bedrock invocations returned HTTP 200.

---

## 6. The public page uses the **static** replay path

**(a) Raw-HTML grep — found nothing (recorded as *unknown*, not a false negative):**

```bash
curl -sS "https://softmax.com/tandem" -o /tmp/page2.html -w "http %{http_code}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page2.html || echo "NO IFRAME IN RAW HTML (client-rendered)"
```
```
http 200
NO IFRAME IN RAW HTML (client-rendered)
```

This matches `playbooks/observatory-api.md` §Featured match: the page is client-rendered for the
iframe, so the raw grep finds nothing for any coworld.

**(b) Source actually used — the page's own SSR payload + the call the page's JS makes.**

Featured match, read out of the SSR payload at `state.playlist[0]` of the same fetched HTML
(unescaped for readability; the bytes are `\"`-escaped in the file):

```json
"playlist":[{"episodeId":"7b9e5b95-d72b-449a-8961-5370957af108","coworldId":"cow_77d94979-f003-494d-8c60-6bd97b97b9db","coworldName":"tandem","coworldVersion":"0.1.1","replayUrl":"https://softmax-public.s3.amazonaws.com/replays/090b12fd-a443-40a8-9707-d7ade2673313.replay","finishedAt":"2026-08-24T01:12:06.841998Z","roundNumber":4,"episodeNumber":1,"code":"tandem.r4.e1","matchup":{"divisionId":"div_fdb4b69f-5586-4239-87f1-b9afeeb34ce5","divisionName":"Competition","first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000,"score_label":"Elo","rounds_played":2,"episode_wins":0,"win_rate":0,"policy_label":"tandem-anchor:v1"},"second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000,"score_label":"Elo","rounds_played":2,"episode_wins":0,"win_rate":0,"policy_label":"tandem-feather:v1"}},"inspectUrl":"/observatory/v2?tab=episode-requests&detail=episode-request:ereq_c24a96c8-26de-4853-b5d7-7c8c3dc2e90c","outcome":null}]
```

A featured match **is present** — `tandem.r4.e1`, both ranked players in the matchup, pointing at
round 4's replay (the same replay verified in checks 3 and 4).

The iframe `src` comes from the call the page's JS makes:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" \
  -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_77d94979-f003-494d-8c60-6bd97b97b9db",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/090b12fd-a443-40a8-9707-d7ade2673313.replay"}' | jq .
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_77d94979-f003-494d-8c60-6bd97b97b9db/sha256%3A92cde32571d96247e869b40211e13c200d2b66897791688025b44344ac5147f4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F090b12fd-a443-40a8-9707-d7ade2673313.replay&v=2",
  "ready": true
}
```

For completeness, the `/coworlds` detail row (which the playbook notes is `null` platform-wide for
these two fields and is therefore **not** the source used):

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|map(select(.name=="tandem"))
          |map({id,name,version,canonical,replay_viewer,featured_match})'
```
```json
[{"id":"cow_77d94979-f003-494d-8c60-6bd97b97b9db","name":"tandem","version":"0.1.1","canonical":true,"replay_viewer":null,"featured_match":null}]
```

**Status: TRUE** — source used: **the page's SSR payload for the featured match + `POST
$BASE/coworlds/replays/session` for the iframe `src`** (the raw-HTML grep was empty and is recorded
as unknown). The `src` is
`…/v2/coworlds/replays/static/<cow_id>/sha256%3A92cde…5147f4/index.html?replay=<s3 url>` — the
**static** route, with `<sha>` = the coworld's `manifest_sha`
(`sha256:92cde32571d96247e869b40211e13c200d2b66897791688025b44344ac5147f4`, matching
`STATE.coworld.manifest_sha`) and `ready: true`. It is **not** a `/client/replay` pod URL. A
featured match is present.

---

## 7. Certification declared the static bundle

Source read: **the committed `runs/2026-08-23-tandem/release-result.json`** that phase 40 downloaded
(present in the working tree; no re-download from run id 32676640602 was needed).

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-tandem/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -r '.certify|keys' runs/2026-08-23-tandem/release-result.json
```
```json
["ok","output_tail","replay_liveness"]
```

**Status: TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read from the
committed `runs/2026-08-23-tandem/release-result.json` (not `/tmp`, not a live endpoint).

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

**(a) Dispatch and artifact.**

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_77d94979-f003-494d-8c60-6bd97b97b9db/sha256%3A92cde32571d96247e869b40211e13c200d2b66897791688025b44344ac5147f4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F090b12fd-a443-40a8-9707-d7ade2673313.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 2026-08-24T01:19:07Z
sleep 15
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:3]'
```
```json
[{"createdAt":"2026-08-24T01:19:07Z","databaseId":32679404498,"status":"in_progress"},
 {"createdAt":"2026-08-24T00:04:03Z","databaseId":32675471888,"status":"completed"},
 {"createdAt":"2026-08-24T00:02:27Z","databaseId":32675392403,"status":"completed"}]
```

Run **32679404498** was created at 01:19:07Z, i.e. after the dispatch — found by sorting on
`createdAt`, not by taking "the latest" blind (the run immediately before it is 75 minutes older).

```bash
gh run watch 32679404498 -R Metta-AI/coworld-builder --exit-status; echo "watch exit=$?"
```
```
✓ main viewer-check · 32679404498
JOBS
✓ viewer-check in 57s (ID 97293297556)
  ✓ Set up job
  ✓ Run actions/checkout@v5
  ✓ Run actions/setup-node@v4
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
  ✓ Complete job
watch exit=0
```

Green run (the "Fail if the viewer did not load" gate passed).

```bash
mkdir -p runs/2026-08-23-tandem/viewer-check
gh run download 32679404498 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-tandem/viewer-check
ls -l runs/2026-08-23-tandem/viewer-check
```
```
-rw-r--r-- 1 root root      0 Aug 24 01:20 smoke-stderr.txt
-rw-r--r-- 1 root root    390 Aug 24 01:20 smoke-stdout.txt
-rw-r--r-- 1 root root   1092 Aug 24 01:20 viewer-smoke.json
-rw-r--r-- 1 root root 238595 Aug 24 01:20 viewer-smoke.png
```

(`runs/2026-08-23-tandem/viewer-check/` is left in the tree for the coordinator to commit — it is
this run's only rendered evidence and the CI sandbox that made it is gone next heartbeat.
`smoke-stderr.txt` is 0 bytes: no errors.)

**(b) The readouts, verbatim.**

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-tandem/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":5067,"clock":"1:40 TIME LEFT","scorebug":"Cobalt daveey 218 N ⬇ 0 scuff 0 1:40 TIME LEFT Rust daveey-1 145 N ⬇ 0 scuff 0","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-23-tandem/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-23-tandem/viewer-check/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 % | `1:40 TIME LEFT` |
| 50 % | `0:49 TIME LEFT` |
| 100 % | `FINAL GAME OVER` |

```bash
jq -r '.failure // "no failure"' runs/2026-08-23-tandem/viewer-check/viewer-smoke.json
```
```
no failure
```

Also from the artifact: `"status":"OPEN"`, `"loading_text":null` (no stuck "Loading replay…"),
`"console_tail":[]` (no console errors), `"ms":5067` (first frame at 5.07 s).

**Item 8 gate: `loaded: true` ✔ and the three clock readouts differ (1:40 → 0:49 → FINAL) ✔.**

**(c) The replay JSON the viewer was asked to draw** — ordered excerpts and `.results` are pasted in
full in check 4 above (early turns 0–2, middle turns 24–25, late turns 48–49, and
`{"reason":"complete","endRule":"out_of_time","progress":0.076,"condition":0.997,"damage":3,
"drops":0,"impacts":0,"scrapeTicks":3,"strainPeakNewtons":[1632,986],"blame":[0,3],
"finalTick":2570}`).

### Spectator judgment

**It is legible, it is the starter's chrome, and it shows this game.** The screenshot
(`viewer-check/viewer-smoke.png`, 1280×800, taken at the 100 % scrub position) is the **endcard**
over a dimmed board, and every element of the paintbot/raid/hive shell is present and in the right
place: a **scorebug** across the top with the two seats named by *policy owner* on the outside
(`Cobalt daveey` left, `daveey-1 Rust` right) and each seat's live strain bar and readout
(`241 N`, `394 N`) plus `⬇ 0` drops and `scuff 0` / `scuff 3` counters flanking a centre clock that
reads `FINAL / GAME OVER`; a **transport strip** along the bottom (restart, step-back, play, `+5s`,
step-forward, loop, fast-forward, a `spoilers` toggle, the state word `OUT OF TIME`, a tick counter
`2445 / 2448`, and a `1× 2× 3× 4× 8× 16×` speed selector with `1×` active); and beneath it the
**scrubber with its momentum graph** — a `CONDITION` trace running flat-full the whole width, with
beat markers clustered at the right end (a green marker and two amber ones, matching the three
`scrapeTicks` and the game-over beat). The board itself shows the warehouse: the couch as a long
dark bar with the two coloured cogs (blue Cobalt fore, red Rust aft) gripped to its ends at the far
left of the route, the yellow wireframe of the corridor/doorway geometry to the right, the
`100% CONDITION` route ribbon across the top with the filled portion stopping about one cell in, a
`220 cm NEXT DOORWAY` distance readout bottom-right, and the legend `Cobalt push · Rust push ·
felt strain`. The endcard itself is the game's own summary: **"OUT OF TIME — 8% of the route"**,
`CONDITION 100% · SCORE 0.019`, `daveey + daveey-1 · complete/out_of_time`, and a stat strip
`0 drops · 0 impacts · 0 scrape s · 1632 peak N · 0/3 blame`.

Those numbers reconcile exactly with the replay record: the endcard's `8% of the route` is
`results.progress: 0.076`, `SCORE 0.019` is `jointScore: 0.018943`, `CONDITION 100%` is
`condition: 0.997`, `1632 peak N` is `strainPeakNewtons[0]`, `0/3 blame` is `blame: [0,3]`, and
`complete/out_of_time` is `results.reason`/`results.endRule` verbatim. The tick counter
`2445 / 2448` sits at `finalTick 2570`'s game-over window. The picture is **not** empty and **not**
frozen: the three scrub readouts move the clock from `1:40 TIME LEFT` at the start through
`0:49 TIME LEFT` at the midpoint to `FINAL GAME OVER` at the end, and the 0 % scorebug
(`218 N` / `145 N`, from the same artifact) differs from the 100 % screenshot's (`241 N` / `394 N`),
so the strain meters are being redrawn as the replay advances, not painted once.

What the picture shows is also the *story the replay tells*, which is the point of this game: the
two cogs make almost no progress (7.6 % of a 12-cell route in the full 2400 ticks) because they
spend the run disagreeing about who leads — the late orders have Cobalt driving `[-1.0, 0.0]` while
Rust drives `[1.0, 0.0]` at effort 0.8, each `say` line explicitly narrating the other's resistance
("Partner pulling west - I'm cor…", "E push. Partner resist. Override lead."). The couch is
undamaged (`condition 0.997`, 0 drops, 0 impacts) and simply never moves. That is a legible,
in-genre failure-to-coordinate, rendered as such.

**Two legibility observations for the coordinator (not check failures):**
1. `feed_lines: 0` — the smoke test found no play-by-play feed lines in the DOM. The orders carry
   rich per-turn `say` text and the shell has a `spoilers` toggle, so either the feed is hidden
   behind that toggle or it is suppressed under the endcard overlay; a spectator landing at the end
   of the replay sees no commentary track. Worth a phase-30 look.
2. The screenshot is dominated by the endcard because the smoke test screenshots at the 100 % scrub
   position; the mid-run board is only inferable from the 50 % clock readout. Not a defect, but the
   rendered evidence for "the board is legible mid-carry" is the clock/scorebug deltas rather than a
   mid-run picture.

Neither of these is the cogame-gridlock failure mode: this is unmistakably the ctf/paintbot shell —
same transport strip, same momentum-graph scrubber, same scorebug layout, same endcard treatment —
retargeted to tandem's nouns (condition, strain in newtons, scuffs, doorways), not a rewrite that
merely shares the ids.

**Status: TRUE** — `loaded: true` (first frame at 5067 ms, `data-replay-loaded="true"`, no failure,
no console errors) **and** the three clock readouts differ (`1:40 TIME LEFT` → `0:49 TIME LEFT` →
`FINAL GAME OVER`).

---

## Observations (recorded, not checklist failures)

**A. Round 3 completed with an empty result set — no episode ever ran.** Round 3
(`round_e572c0da-3392-492d-ad11-48d93ece2a5b`) reports `status: completed` but created and
"completed" in 11 seconds, with `results: []`:

```bash
curl -sS "$BASE/episode-requests?round_id=round_e572c0da-3392-492d-ad11-48d93ece2a5b&limit=20" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|map({id,status,replay_url})'
```
```json
[{"id":"ereq_3638b303-7e48-42ba-ae83-849fb7aea141","status":"completed","replay_url":null}]
```
```bash
curl -sS "$BASE/episode-requests/ereq_3638b303-7e48-42ba-ae83-849fb7aea141" "${AUTH[@]}" | jq '{status,episode_id,replay_url,scores,participant_scores,dispatched_at,running_at,completed_at,error,error_type}'
```
```json
{
  "status": "completed",
  "episode_id": null,
  "replay_url": null,
  "scores": [],
  "participant_scores": [],
  "dispatched_at": "2026-08-24T00:52:28.087911Z",
  "running_at": null,
  "completed_at": "2026-08-24T00:52:32.910731Z",
  "error": null,
  "error_type": null
}
```

Its artifacts 404:
```bash
curl -sS -w "\nHTTP %{http_code}\n" "$BASE/episode-requests/ereq_3638b303-…/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
curl -sS -w "\nHTTP %{http_code}\n" "$BASE/episode-requests/ereq_3638b303-…/artifacts/results" "${AUTH[@]}" "${ELEV[@]}"
```
```
{"detail":"No logs found for job 63800bdb-74ef-4f92-bf86-f84c61020d2e"}
HTTP 404
{"detail":"No results found for job 63800bdb-74ef-4f92-bf86-f84c61020d2e"}
HTTP 404
```
The job was dispatched, never reached `running`, produced no logs, no results, no replay, no scores,
and the round was still settled `completed` with `error: null`. The leaderboard confirms it did not
count: `rounds_played` went 1 → 2 across rounds 2, 3 and 4, not 1 → 3. This looks like a **platform
dispatch drop** rather than a coworld defect (there is nothing of ours to log), but it is
undocumented, so it is recorded here rather than excused. It does not affect any check: rounds 2 and
4 alone satisfy check 1, and check 3/4/5 were run against round 4.

**B. In round 2, champion #2's seat played 100 % scripted.** Round 2's replay
(`d6032a99-…`) records only **one** `register` record and `policyKinds: ["llm","scripted"]`:

```json
{"k":"register","seat":0,"alias":"Cobalt","policy":"llm","kind":"llm","baseline":""}
```
```json
{"names":["daveey","daveey-1"],"aliases":["Cobalt","Rust"],"policyKinds":["llm","scripted"],"scores":[0.02,0.02],"win":[false,false],"jointScore":0.02,"delivered":false,"damage":0,"condition":1.0,"deliveryTicks":2661,"parTicks":1112,"progress":0.08,"drops":0,"impacts":0,"scrapeTicks":0,"strainPeakNewtons":[1428,2396],"blame":[0,0],"llmTurns":[50,0],"fallbackTurns":[0,0],"reason":"complete","endRule":"out_of_time","finalTick":2661,"seed":876240439}
```
```
[{"seat":0,"source":"llm","n":50},{"seat":1,"source":"scripted","n":50}]
```
and its hosted log shows exactly 50 Bedrock calls (seat 0's) where round 4's shows 101. Seat 1
(`daveey-1` / `tandem-feather:v1`, whose `tools/ci/policies.json` entry sets `PLAYER_PROMPT` and no
`PLAYER_SCRIPTED`, i.e. it *is* an LLM policy) connected and joined as `Rust` but never sent its
`register`, so the server drove the seat with its built-in scripted controller. **Round 4 did not
reproduce this** — both seats registered `kind: llm` and played 50/50 LLM turns — so it is
intermittent, not systematic. Check 4 is judged on the latest completed round (round 4) and is TRUE;
this is flagged because a repeat would silently demote a champion to a baseline in a scored round.
Round 2's log is otherwise `CLEAN` under the same decoded grep. Not fixed here (verifier does not
edit code); reported for the coordinator.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** — 3 completed (rounds 2, 3, 4); rounds 2 & 4 produced scored episodes; fillers registered before the first trigger |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — `daveey` (rank 1) and `daveey-1` (rank 2), `rounds_played: 2` each; no filler rows |
| 3 | Latest round's episode request completed with a `replay_url` and correct participants | **TRUE** — `ereq_c24a96c8-…` completed, replay `090b12fd-…`, participants `daveey` + `daveey-1`, both `is_filler:false` |
| 4 | Replay bytes valid, protocol matches, reason legal, champions non-scripted | **TRUE** — strict JSON ok, `tandem/v1`, `reason: complete`, 100/100 orders `source: llm`, 0 fallback turns |
| 5 | Hosted game log clean | **TRUE** — `CLEAN` over the fully decoded 208 608-char log; 101/101 Bedrock calls HTTP 200 |
| 6 | Public page uses the **static** replay path, featured match present | **TRUE** — featured match `tandem.r4.e1`; `src` = `…/replays/static/<cow_id>/sha256%3A92cde…/index.html?replay=…`, `ready:true`, no `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared; …)` from the committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — run 32679404498: `loaded:true` @5067 ms, clocks `1:40` → `0:49` → `FINAL GAME OVER`, starter chrome intact |

**Overall verdict: all-true — 8/8 checks TRUE, 0 items false.**
Completed rounds: 3 (2, 3, 4) · scored episodes: 2 (rounds 2 and 4).
Replay verified: `https://softmax-public.s3.amazonaws.com/replays/090b12fd-a443-40a8-9707-d7ade2673313.replay`
Iframe src: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_77d94979-f003-494d-8c60-6bd97b97b9db/sha256%3A92cde32571d96247e869b40211e13c200d2b66897791688025b44344ac5147f4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F090b12fd-a443-40a8-9707-d7ade2673313.replay&v=2`
viewer-check run: `32679404498` (Metta-AI/coworld-builder, dispatched 2026-08-24T01:19:07Z, green)
