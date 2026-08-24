# VERIFY — firm   (2026-08-24T03:20Z)

Verdict: **all-true** (8 / 8)

Run `2026-08-23-firm` · coworld `cow_39c7f43c-706d-49e0-9259-2686b86c9d71` v0.1.0 ·
manifest_sha `sha256:5ddddfc0545dc05e591a875a896c11b47a0fb85e9899892d5ae7877d1f0d793e` ·
league `league_31edf62a-9174-4975-b39b-cd1555853bff` · division `div_ec0a2aaa-96cf-4fe2-8327-485c316ad4e6`.

Every call below was made fresh during phase 60 of this run (02:59Z–03:20Z), with headers
`Authorization: Bearer …` and `User-Agent: coworld-builder/1.0` (values never printed);
`X-Use-Elevated-Privileges: true` added where noted. The two documented exceptions to
"fetch fresh" are item 7 (the committed `release-result.json` from this run's release
dispatch) and item 8 (the artifact of the `viewer-check.yml` run dispatched at 03:18Z **this
run**).

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | TRUE |
| 2 | Both champions ranked, fillers absent | TRUE |
| 3 | Latest round's episode request completed with replay | TRUE |
| 4 | Replay bytes valid, protocol matches, shows the game | TRUE |
| 5 | Hosted game log clean | TRUE |
| 6 | Public page uses the static replay path | TRUE |
| 7 | Certification declared the static bundle | TRUE |
| 8 | Viewer executed in a browser and judged | TRUE |

---

## 1. ≥2 completed rounds after the fillers were set

Polled every 5 minutes from 02:59:22Z; two rounds completed at 03:14:22Z, well inside the
75-minute bound. Poll trail (`runs/2026-08-23-firm/poll.log`, each line also heartbeat-logged
to `log.md`):

```
2026-08-24T02:59:22Z completed=1 [{"n":1,"s":"completed"}]
2026-08-24T03:04:22Z completed=1 [{"n":1,"s":"completed"}]
2026-08-24T03:09:22Z completed=1 [{"n":1,"s":"completed"}]
2026-08-24T03:14:22Z completed=2 [{"n":2,"s":"completed"},{"n":1,"s":"completed"}]
DONE 2026-08-24T03:14:22Z n=2
```

Final fetch, 2026-08-24T03:17:13Z:

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_31edf62a-9174-4975-b39b-cd1555853bff&limit=20
   -H Authorization -H User-Agent
$ jq -r '[.entries[]|select(.status=="completed")]|length'
2
```

```json
{
  "entries": [
    {
      "id": "round_1456d48a-6b1d-4c12-ab4f-155a36982085",
      "round_number": 2,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-24T03:10:53.078252Z",
      "completed_at": "2026-08-24T03:12:35.040213Z",
      "entrants": [
        {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
         "policy_version_id": "bc171418-6b75-404f-a087-06f103e19b4f",
         "league_policy_membership_id": "lpm_000bf14a-5ab8-4959-a8a1-3f542d33e1f0"},
        {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
         "policy_version_id": "8250a440-163d-45c8-a32b-c21cb1ebb762",
         "league_policy_membership_id": "lpm_eb4e6915-04d5-4980-b086-d7c93c5becbc"}
      ]
    },
    {
      "id": "round_9dd7c937-f649-424f-acfe-8744a7c8a790",
      "round_number": 1,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-24T02:55:52.730054Z",
      "completed_at": "2026-08-24T02:57:15.795864Z",
      "entrants": [
        {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
         "policy_version_id": "bc171418-6b75-404f-a087-06f103e19b4f",
         "league_policy_membership_id": "lpm_000bf14a-5ab8-4959-a8a1-3f542d33e1f0"},
        {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
         "policy_version_id": "8250a440-163d-45c8-a32b-c21cb1ebb762",
         "league_policy_membership_id": "lpm_eb4e6915-04d5-4980-b086-d7c93c5becbc"}
      ]
    }
  ]
}
```

No round has `status` `failed` or `discarded`; both `error` fields are `null`.

**Fillers were in force for both rounds.** The registered filler set, read fresh (this read needs
the elevated header even though it is a read):

```
GET $BASE/leagues/$L/filler-policies   -H Authorization -H User-Agent -H X-Use-Elevated-Privileges
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "4ef7b5b5-85fd-4c83-81e0-cf89c6bf54a1", "policy_name": "firm-steady",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
  {"policy_version_id": "c99a2095-485d-4a9a-b4f0-a9f4355f21ec", "policy_name": "firm-taskmaster",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}]}
```

Neither id is a champion id (`bc171418…` / `8250a440…`). Round 1 was *seated* with them — its own
replay names the filler seats `Baseline`, which only happens once the filler list exists
(re-fetched 03:19:49Z):

```
$ curl -sSL https://softmax-public.s3.amazonaws.com/replays/10851618-157a-4954-ac66-19b6b58707f3.replay | jq -c '.policyNames'
["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]
```

Status: **TRUE** — rounds 1 and 2 both `completed` (02:57:15.795864Z and 03:12:35.040213Z), both
seated after the filler policies `4ef7b5b5…` + `c99a2095…` were registered (`log.md`
`2026-08-24T02:57:29Z 50 fillers 200 registered …`, and round 1's replay already shows the
`Baseline` seats).

---

## 2. Both champions ranked; fillers absent / Baseline

```
GET $BASE/divisions/div_ec0a2aaa-96cf-4fe2-8327-485c316ad4e6/leaderboard  -H Authorization -H User-Agent
(bare JSON list, not .entries)
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey-1	firm-hand:v1	1001.4695015289755	2	1.0
2	daveey	firm-boss:v1	998.5304984710245	2	1.0
```

Full rows (fetched 03:17Z):

```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1001.4695015289755,"score_label":"Elo","rounds_played":2,"episode_wins":1.0,
  "win_rate":0.5,"policy_label":"firm-hand:v1"},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":998.5304984710245,"score_label":"Elo","rounds_played":2,"episode_wins":1.0,
  "win_rate":0.5,"policy_label":"firm-boss:v1"}]
```

Status: **TRUE** — `daveey` (`firm-boss:v1`) and `daveey-1` (`firm-hand:v1`) both present, each
`rounds_played = 2 ≥ 1`. The leaderboard has exactly two rows: the fillers `firm-steady:v1` and
`firm-taskmaster:v1` are **absent** (they are seated as `Baseline` and are not ranked).

---

## 3. Latest completed round's episode request completed, with a replay

Latest completed round = `round_1456d48a-6b1d-4c12-ab4f-155a36982085` (round_number 2, from item 1).

```
GET $BASE/episode-requests?round_id=round_1456d48a-6b1d-4c12-ab4f-155a36982085&limit=20
$ jq -r '[.entries[]|{id,status}]'
[{"id": "ereq_2045780a-2c84-4c43-8ab2-0f16e28b22f9", "status": "completed"}]

GET $BASE/episode-requests/ereq_2045780a-2c84-4c43-8ab2-0f16e28b22f9
$ jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/74f5cf6e-dcb1-499a-94fe-32c4fee6cb86.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "bc171418-6b75-404f-a087-06f103e19b4f",
     "policy_name": "firm-boss", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": false},
    {"position": 1, "kind": "policy", "policy_version_id": "8250a440-163d-45c8-a32b-c21cb1ebb762",
     "policy_name": "firm-hand", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "kind": "policy", "policy_version_id": "c99a2095-485d-4a9a-b4f0-a9f4355f21ec",
     "policy_name": "firm-taskmaster", "version": 1, "player_name": "daveey", "is_filler": true},
    {"position": 3, "kind": "policy", "policy_version_id": "4ef7b5b5-85fd-4c83-81e0-cf89c6bf54a1",
     "policy_name": "firm-steady", "version": 1, "player_name": "daveey", "is_filler": true},
    {"position": 4, "kind": "policy", "policy_version_id": "4ef7b5b5-85fd-4c83-81e0-cf89c6bf54a1",
     "policy_name": "firm-steady", "version": 1, "player_name": "daveey", "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.15916666666666668},
    {"position": 1, "score": 0.1716666666666667},
    {"position": 2, "score": 0.9496666666666665},
    {"position": 3, "score": 0.2029166666666667},
    {"position": 4, "score": 0.2029166666666667}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, seats 0/1 are the champions
`daveey` (`firm-boss`) and `daveey-1` (`firm-hand`) with `is_filler:false`; seats 2–4 are the
fillers (`is_filler:true`, rendered `Baseline`/`Baseline (2)`/`Baseline (3)` in the replay).

---

## 4. Replay bytes are valid and show the game

```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/74f5cf6e-dcb1-499a-94fe-32c4fee6cb86.replay" -o /tmp/ep.replay
$ ls -l /tmp/ep.replay
-rw-r--r-- 1 root root 24622 Aug 24 03:17 /tmp/ep.replay
$ jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ jq -r '.protocol, .results.reason' /tmp/ep.replay
firm.replay.v1
complete
```

`protocol` = `firm.replay.v1`, exactly the string the design note declares
(`runs/2026-08-23-firm/design.md` §"Replay payload — `firm.replay.v1`", line 654:
`{"protocol":"firm.replay.v1",`). The coworld's published manifest declares the sibling ids
`firm.player.v1` (`manifest.game.protocols.player`) and describes this replay's event vocabulary
(`start` / `shift` / `memo` / `work` / `settle` / `end`) in `manifest.game.protocols.global`;
the replay's events use precisely that vocabulary.

`results.reason == "complete"` — the design note's natural ending; the acceptable-`deadline`
exception was not needed.

Firm's replay events carry `kind`, not `type`, and mark non-scripted seats with `scripted:false`
(there is no `fallback` field in this protocol — the prompt's `.type=="decision"` /
`.fallback==true` filters are the bullwhip-lineage generic form). The equivalents:

```
$ jq -r '[.events[]|.kind]|group_by(.)|map("\(.[0]): \(length)")|.[]' /tmp/ep.replay
end: 1
memo: 8
settle: 8
shift: 8
start: 1
work: 32
$ jq -r '[.events[]|select(.scripted!=null)|"\(.kind) seat=\(.seat) scripted=\(.scripted)"]|group_by(.)|map("\(.[0]): \(length)")|.[]' /tmp/ep.replay
memo seat=2 scripted=true: 8
work seat=0 scripted=false: 8
work seat=1 scripted=false: 8
work seat=3 scripted=true: 8
work seat=4 scripted=true: 8
$ jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay
0
$ jq -r '[.events[]|select(.kind=="memo" or .kind=="work")]|length' /tmp/ep.replay
40
$ jq -r '[.events[]|select((.kind=="memo" or .kind=="work") and .scripted==false)]|length' /tmp/ep.replay
16
$ jq -r '[.events[]|select((.kind=="memo" or .kind=="work") and .scripted==false and ((.say//"")|length)>20)]|length' /tmp/ep.replay
16
```

40 decisions; the two champion seats contributed 16 of them, **every one `scripted:false`** and
every one carrying a substantive report (>20 runes). Zero fallbacks. This episode's seeded
permutation put a filler (`Baseline`, seat 2) in the office and both champions on machines.

```
$ jq -c '.names,.policyNames,.config,.results' /tmp/ep.replay
["Bolt","Gasket","Ratchet","Tinker","Gizmo"]
["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]
{"shifts":8,"seed":659892741,"reports":true,"sampled":true}
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"],
 "scores":[0.15916666666666668,0.1716666666666667,0.9496666666666665,0.2029166666666667,0.2029166666666667],
 "roles":["Worker","Worker","Manager","Worker","Worker"],
 "pay":[38.2,41.2,0.0,48.7,48.7],"units":[90,91,0,92,88],
 "revenue":2906.0,"wages":626.8000000000001,"profit":2279.2,
 "shifts":8,"maxShifts":8,"reason":"complete"}
```

`results` validates against the manifest's `results_schema` field-for-field (`pay` 0.0 and `units`
0 on the manager seat; `scores` are the normalized per-shift statistic) and the
`participant_scores` in item 3 are the same five numbers.

Champion decision content — the champions are visibly playing *this* game (marginal hour vs.
$1.50 toil, machine condition, an underpaying manager):

```
$ jq -r '.events[]|[.shift,(.seat//"-"),.kind,((.say//.text//"")|.[0:110])]|@tsv' /tmp/ep.replay | head -14
	-	start
0	-	shift	Standing order: machines 1-3 on line A, machine 4 on line B. Six hours running, three on maintenance.
0	2	memo	All four machines on line A. Ten hours running. Maintenance is not output.
0	0	work	Machine 1 condition 100. Running 6 hours line A, maintaining 3. Following standing orders and memo.
0	1	work	Machine 2 starting shift 0. Following orders: line A, 6 run hours, 3 maintenance. Condition 100. Will report u
0	3	work	Machine 3: condition 100, ran 0, maintained 0, 0 units.
0	4	work	Machine 4: condition 100, ran 0, maintained 0, 0 units.
0	-	settle
1	-	shift	All four machines on line A. Ten hours running. Maintenance is not output.
1	2	memo	All four machines on line A. Ten hours running. Maintenance is not output.
1	0	work	Machine 1 condition 100. Running 10h line A per memo. All four machines ordered to line A; pool at 20% means ~
1	1	work	Running full 10h line A per memo. Condition 100→70. Marginal hour: ~2 units * 1.0 * $10 * 0.05 = $1.00 < $1.50
1	3	work	Machine 3: condition 100, ran 6, maintained 3, 12 units.
1	4	work	Machine 4: condition 100, ran 6, maintained 3, 12 units.
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON, `protocol` = `firm.replay.v1` as declared,
`results.reason == "complete"`, 16/16 champion decisions non-scripted and non-trivial, zero
fallbacks.

---

## 5. Hosted game log is clean

```
GET $BASE/episode-requests/ereq_2045780a-2c84-4c43-8ab2-0f16e28b22f9/artifacts/logs
   -H Authorization -H User-Agent -H X-Use-Elevated-Privileges
$ ls -l logs.raw
-rw-r--r-- 1 root root 37953 Aug 24 03:17 logs.raw
# the body is python b'…' byte-string reprs under '===== container: … =====' headers —
# decoded with ast.literal_eval per repr before grepping (37,800 chars, 146 lines, 4 containers)
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs.txt || echo CLEAN
CLEAN
```

(The same grep on the *undecoded* bytes also returns 0 matches, so the decode did not hide
anything: `grep -cE … logs.raw` → `0`.)

Containers present: `coworld-init-config`, `bedrock-sidecar`, `game`, `worker`. The `game`
container, verbatim head and tail:

```
===== container: game =====
firm: seed not pinned; randomized
firm: seats=5 shifts=8 reports=true model=claude-sonnet-5
firm: serving on 0.0.0.0:8080
firm: player slot 4 connected (1/5)
firm: slot 4 delivered a prompt (1167 chars, scripted steady)
firm: player slot 1 connected (2/5)
firm: slot 1 delivered a prompt (1292 chars)
firm: player slot 2 connected (3/5)
firm: slot 2 delivered a prompt (1167 chars, scripted taskmaster)
…
firm: starting with 5/5 players connected
firm llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
firm: episode timeout 1200s (assumed); playing until 720s
firm: shift 0 of 8 at 6s
firm: shift 0 Ratchet (Manager) orders @["A", "A", "A", "A"] payroll 20 split @[25, 25, 25, 25] at 14s
firm: shift 0 Bolt (Machine 1) runs line A 6h, maintains 3h at 14s
…
firm: shift 7 Ratchet (Manager) orders @["B", "B", "B", "B"] payroll 20 split @[25, 25, 25, 25] at 53s
firm: shift 7 Bolt (Machine 1) runs line B 6h, maintains 4h at 53s
firm: shift 7 Gasket (Machine 2) runs line B 6h, maintains 4h at 53s
firm: shift 7 Tinker (Machine 3) runs line B 6h, maintains 3h at 53s
firm: shift 7 Gizmo (Machine 4) runs line B 6h, maintains 3h at 53s
firm: writing results and replay
firm: episode complete, shutting down
```

Status: **TRUE** — zero occurrences of `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens` or `rejected`; every shift resolved on the LLM path (all eight shifts
logged, no retries, episode ran 53 s of a 720 s play budget). No documented exception invoked.

---

## 6. The public page uses the static replay path

Source used: **the API the page reads** (the raw-HTML grep is not evidence either way — the page
is client-rendered for the iframe, as `playbooks/observatory-api.md` §Featured match records).

```
$ curl -sS "https://softmax.com/firm" | grep -o '<iframe[^>]*src="[^"]*"'
(no output — 445,451 bytes of client-rendered shell; the iframe exists only after JS runs)
```

**Featured match** — server-rendered into the page's SSR payload at `state.playlist[0]`
(fetched 03:17Z, verbatim excerpt from the HTML):

```
playlist\":[{\"episodeId\":\"9f842ce1-354d-4dfa-976a-03829f46455b\",
\"coworldId\":\"cow_39c7f43c-706d-49e0-9259-2686b86c9d71\",\"coworldName\":\"firm\",
\"coworldVersion\":\"0.1.0\",
\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/74f5cf6e-dcb1-499a-94fe-32c4fee6cb86.replay\",
\"finishedAt\":\"2026-08-24T03:12:30.558556Z\",\"roundNumber\":2,\"episodeNumber\":1,
\"code\":\"firm.r2.e1\",\"matchup\":{\"divisionId\":\"div_ec0a2aaa-96cf-4fe2-8327-485c316ad4e6\",
\"divisionName\":\"Competition\",\"first\":{\"rank\":1,
\"player_id\":\"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d\",\"player_name\":\"daveey-1\",
\"score\":1001.4695015289755,\"score_label\":\"Elo\",…
```

The featured match is round 2 episode 1 (`firm.r2.e1`) — the same replay verified in items 3–4 —
with the ranked matchup daveey-1 vs daveey.

The coworld detail row (bare array; `featured_match` is `null` platform-wide and is not evidence):

```
GET $BASE/coworlds?limit=200   -H Authorization -H User-Agent
$ jq -r '.[]|select(.name=="firm")|{id,name,version,canonical,replay_viewer:.manifest.game.replay_viewer,featured_match,manifest_hash}'
{
  "id": "cow_39c7f43c-706d-49e0-9259-2686b86c9d71",
  "name": "firm",
  "version": "0.1.0",
  "canonical": true,
  "replay_viewer": {"bundle": "sha256:fd34ac8ef1eff414f47ac54617f5671bb35dbc95dded107b6de2275ad8eee935"},
  "featured_match": null,
  "manifest_hash": "sha256:5ddddfc0545dc05e591a875a896c11b47a0fb85e9899892d5ae7877d1f0d793e"
}
```

**The iframe `src`** — the call the page's own JS makes:

```
POST $BASE/coworlds/replays/session   -H Authorization -H User-Agent -H content-type
  {"coworld_id":"cow_39c7f43c-706d-49e0-9259-2686b86c9d71",
   "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/74f5cf6e-dcb1-499a-94fe-32c4fee6cb86.replay"}
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_39c7f43c-706d-49e0-9259-2686b86c9d71/sha256%3A5ddddfc0545dc05e591a875a896c11b47a0fb85e9899892d5ae7877d1f0d793e/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F74f5cf6e-dcb1-499a-94fe-32c4fee6cb86.replay&v=2",
  "ready": true
}
```
```
$ curl -sS -o /dev/null -w "index.html HTTP %{http_code}\n" "$SRC"
index.html HTTP 200
```

The path is `/v2/coworlds/replays/static/<cow_id>/<manifest_hash url-encoded>/index.html?replay=<s3 url>`
with `<cow_id>` = `cow_39c7f43c-706d-49e0-9259-2686b86c9d71` and `<sha>` =
`sha256:5ddddfc0545dc05e591a875a896c11b47a0fb85e9899892d5ae7877d1f0d793e` — STATE's
`manifest_sha`, matching. It is **not** a `/client/replay` pod URL, and `ready: true`.

Status: **TRUE** — featured match present (`firm.r2.e1`), iframe `src` is the static route,
served 200.

---

## 7. Certification declared the static bundle

Source: the **committed** `runs/2026-08-23-firm/release-result.json` (the artifact phase 40
downloaded from release run `32684174950`). No re-download was needed.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-23-firm/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
$ jq -r '.certify|keys' runs/2026-08-23-firm/release-result.json
["ok","output_tail","replay_liveness"]
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`,
read from the committed `runs/2026-08-23-firm/release-result.json` (not `/tmp`, not a re-download).

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

Dispatched against the exact iframe `src` from item 6, at 2026-08-24T03:18:05Z:

```
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
    -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_39c7f43c-706d-49e0-9259-2686b86c9d71/sha256%3A5ddddfc0545dc05e591a875a896c11b47a0fb85e9899892d5ae7877d1f0d793e/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F74f5cf6e-dcb1-499a-94fe-32c4fee6cb86.replay&v=2" \
    -f timeout=90
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
   | jq -c 'sort_by(.createdAt)|reverse|.[0]'
{"createdAt":"2026-08-24T03:18:06Z","databaseId":32685986524,"status":"in_progress"}
   # created 1 s after the dispatch — the new run, not "the latest" taken blind
$ gh run watch 32685986524 -R Metta-AI/coworld-builder --exit-status
✓ main viewer-check · 32685986524   viewer-check in 36s (ID 97311032834)   conclusion: success
$ gh run download 32685986524 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-firm/viewer-check
-rw-r--r-- 1 root root      0 viewer-check/smoke-stderr.txt
-rw-r--r-- 1 root root    317 viewer-check/smoke-stdout.txt
-rw-r--r-- 1 root root   1117 viewer-check/viewer-smoke.json
-rw-r--r-- 1 root root 367641 viewer-check/viewer-smoke.png
```
Run URL: https://github.com/Metta-AI/coworld-builder/actions/runs/32685986524

The readouts, verbatim:

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-firm/viewer-check/viewer-smoke.json
{"loaded":true,"ms":1339,"clock":"SHIFT 0","scorebug":"","feed_lines":0}

$ jq -c '.signals' runs/2026-08-23-firm/viewer-check/viewer-smoke.json
{"data_replay_loaded":null,"data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}

$ jq -r '.failure // "no failure"' runs/2026-08-23-firm/viewer-check/viewer-smoke.json
no failure

$ jq -r '.console_tail[]' runs/2026-08-23-firm/viewer-check/viewer-smoke.json
[bridge] loading
[bridge] ready
```

The three clock readouts:

| scrub position | `#clock` |
|---|---|
| 0 % | `SHIFT 0` |
| 50 % | `SHIFT 0 / 8 · WAITING ON 5` |
| 100 % | `FINAL · PROFIT $2,279.20` |

All three **differ**, and the 100 % readout's `$2,279.20` is exactly `results.profit = 2279.2`
from the replay bytes in item 4.

Two null readouts, recorded rather than glossed: `scorebug` is `""` (the `#scorebug` element
**exists** — the probe returns `null` when the selector is absent — but its text was empty at the
1,339 ms first-frame sample, before the seat strip painted; the screenshot taken after the scrub
shows it fully populated), and `feed_lines` is `0` because this shell has no `#feed`/`.feed`/`#log`
list: Firm renders each seat's report as a speech bubble pinned to its machine card instead of a
scrolling feed. `#scrub` **is** present (the three readouts above were taken by dragging it).
Both are legibility observations for the coordinator, not check failures.

Status: **TRUE** — `loaded: true` (bridge `ready`, first frame at 1,339 ms) **and** the three
clock readouts differ.

### The replay JSON the viewer was asked to draw (ordered excerpts)

Middle of the episode:

```
$ jq -r '.events[]|[.shift,(.seat//"-"),.kind,((.say//.text//"")|.[0:110])]|@tsv' /tmp/ep.replay | sed -n '25,34p'
3	0	work	Machine 1 condition 76, switching to B. Running 10h per memo. Report condition 46 after shift.
3	1	work	Condition 82. Marginal analysis: 1 run hour = ~1.91 units * $10 * 20% * 25% = $0.955 << $1.50 effort. Pool spl
3	3	work	Machine 3: condition 100, ran 6, maintained 3, 12 units.
3	4	work	Machine 4: condition 100, ran 6, maintained 3, 12 units.
3	-	settle
4	-	shift	All four machines on line B. Ten hours running. Maintenance is not output.
4	2	memo	All four machines on line B. Ten hours running. Maintenance is not output.
4	0	work	Machine 1 condition 52 after 10h B last shift. Running 10h B this shift as ordered. Condition will drop to 22.
4	1	work	Machine 2 running full shift line B at condition 100. Marginal: 2*(0.5+100/200)*10*$10*20%*25%=$2.50/hr, justi
4	3	work	Machine 3: condition 100, ran 6, maintained 3, 8 units.
```

Late:

```
$ … | tail -12
6	1	work	Condition 40, wearing fast. Running 6h B + 4h maint to stabilize. Marginal calc: 6h @ cond 40→28→16: ~9.6 unit
6	3	work	Machine 3: condition 100, ran 6, maintained 3, 12 units.
6	4	work	Machine 4: condition 100, ran 6, maintained 3, 12 units.
6	-	settle
7	-	shift	All four machines on line B. Ten hours running. Maintenance is not output.
7	2	memo	All four machines on line B. Ten hours running. Maintenance is not output.
7	0	work	Condition 70, running 6h on B per memo. Maintenance 4h to sustain output. Ready for final shift.
7	1	work	Condition 46, marginal analysis: 1 run hr @ cond 46 makes ~2.46 units. Worth $0.74/hr vs $1.50 effort. Below t
7	3	work	Machine 3: condition 100, ran 6, maintained 3, 12 units.
7	4	work	Machine 4: condition 100, ran 6, maintained 3, 12 units.
7	-	settle
8	-	end	complete
```

```
$ jq -r '.results' /tmp/ep.replay
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"],
 "scores":[0.1591666…,0.1716666…,0.9496666…,0.2029166…,0.2029166…],
 "roles":["Worker","Worker","Manager","Worker","Worker"],
 "pay":[38.2,41.2,0.0,48.7,48.7],"units":[90,91,0,92,88],
 "revenue":2906.0,"wages":626.8,"profit":2279.2,"shifts":8,"maxShifts":8,"reason":"complete"}
```

### Spectator judgment

**It is legible, it moves, and it is unmistakably this game.** `viewer-smoke.png` (taken in CI at
the 100 % scrub position) shows the bullwhip-lineage chrome intact: the wordmark **THE FIRM** top
left, a centred transport clock reading `FINAL · PROFIT $2,279.20`, a `REPLAY` chip and a `« LOG`
button top right; below it the **scorebug strip** with all five seats — `daveey $38.20 MACHINE 1
25% 0.16`, `daveey-1 $41.20 MACHINE 2 25% 0.17`, the underlined leader `Ratchet $2,279.20 MANAGER
0.95`, `Tinker $48.70 MACHINE 3` and `Gizmo $48.70 MACHINE 4`; then the amber status line
`SHIFT 8/8 · BOARD A 12 · B 33 · NEXT A 12 · B 33 · POOL 20% · PROFIT $2,279.20`. The floor beneath
it draws THE OFFICE panel (the manager cog, `POOL 20%`, `PROFIT $2,279.20`), an ORDER BOARD with A
and B demand bars, and four machine cards, each with a cog sprite, a `COND` bar (76, 52, …, 100),
a line chip, a units count and a pay/share row — plus the workers' reports as speech bubbles
("Condition 70, running 6h on B per memo. Maintenance 4h to sustain output. Ready for final
shift."). Across the bottom sits the **momentum graph** (`DEMAND VS UNITS MADE`, with the
`DEMAND SWITCH` marker and a legend for A made / B made / profit / demand) and the **scrubber /
transport strip** with a play button, per-event tick marks and the counter `58 / 58`. Centred over
it all is the **endcard**: `FINAL — 8 SHIFTS · PROFIT $2,279.20`, the headline
`Ratchet RAN A TIGHT SHOP`, and the ranked table (Ratchet Manager $2,279.20 0.95; Tinker 92 units
$48.70 0.20; Gizmo 88 $48.70 0.20; daveey-1 Machine 2 91 $41.20 0.17; daveey Machine 1 90 $38.20
0.16). Every number on that endcard reconciles with the replay's `results` above — same pay, same
units, same scores, same order.

Nothing is empty, frozen or unreadable: the clock went `SHIFT 0` → `SHIFT 0 / 8 · WAITING ON 5` →
`FINAL · PROFIT $2,279.20` across the scrub, i.e. the viewer both draws and advances, and the
intermediate `WAITING ON 5` proves it renders the mid-episode simultaneous-decision state rather
than only the endcard. The picture also *tells the story the log tells*: a taskmaster manager
ordering all four machines onto one line at a 20 % pool, workers whose reports argue the marginal
hour is worth less than the $1.50 of toil, machine conditions falling on the two champion-owned
machines (76 and 52) while the two scripted-steady machines sit at 100, and a firm that ends
richer than its workers. That is the principal–agent squeeze the design promises, visible without
reading the JSON.

Two legibility notes for phase 30 rather than defects: the shell exposes `#clock` and `#scrub` but
its seat strip's `#scorebug` reads empty at first paint (populated a moment later), and there is
no `#feed`/`#log` list element — the reports live in the floor bubbles and behind the `« LOG`
button — so the generic smoke probe reports `feed_lines: 0` for a viewer that is in fact showing
five reports on screen.

---

### Provenance

- Rounds / leaderboard / episode-request / logs / coworlds / replay-session: fetched live
  02:59Z–03:20Z on 2026-08-24 against `https://softmax.com/api/observatory/v2`.
- Replay bytes: `https://softmax-public.s3.amazonaws.com/replays/74f5cf6e-dcb1-499a-94fe-32c4fee6cb86.replay`,
  fetched 03:17Z.
- Item 7: `runs/2026-08-23-firm/release-result.json` (committed by phase 40 from release run 32684174950).
- Item 8: artifact of `viewer-check.yml` run **32685986524**, dispatched by this phase at 03:18:05Z,
  downloaded to `runs/2026-08-23-firm/viewer-check/` (needs committing — it is this run's only
  rendered evidence).
