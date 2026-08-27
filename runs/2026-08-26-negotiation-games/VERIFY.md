# VERIFY — negotiation-games   (2026-08-27T00:48:00Z)

Verdict: **all-true** (8 / 8)

Run: `2026-08-26-negotiation-games` · coworld `cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5` v`0.1.1`
· league `league_88e9052f-8e37-4f2e-aea1-ea4f5fdb20e7` · division `div_5699e6c3-6cf1-4a38-9e69-e2b954332c91`

Common preamble for every `curl` below (header **names** only; values are never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_88e9052f-8e37-4f2e-aea1-ea4f5fdb20e7
D=div_5699e6c3-6cf1-4a38-9e69-e2b954332c91
COW=cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

All evidence in this file was fetched during phase 60 on 2026-08-27 between 00:26Z and 00:48Z,
except items 7 and 8 (the two documented exceptions — see each section).

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"
```

Fetched 2026-08-27T00:43:0xZ. Response (trimmed to the fields at issue; the full body also
carries `round_config`, `division` and the embedded league settings):

```json
{
  "entries": [
    {
      "id": "round_0f649abe-e64c-4ca6-9cfa-e6671c1b9419",
      "round_number": 2,
      "status": "completed",
      "error": null,
      "scheduled_by": "ladder",
      "commissioner_key": "platform",
      "completed_at": "2026-08-27T00:41:44.080045Z",
      "created_at": "2026-08-27T00:40:02.024516Z",
      "round_config": {
        "purpose": "ladder",
        "entrant_attributions": [
          {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
           "policy_version_id": "594069a3-11a9-4304-84de-14d0289ce1de",
           "league_policy_membership_id": "lpm_c8ac6a98-6b49-45b5-ad43-886f7fc34eb4"},
          {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
           "policy_version_id": "b8aeca6a-c431-4789-ae99-d468a3c9b0b6",
           "league_policy_membership_id": "lpm_c5e63388-0e85-4942-a782-037da083844f"}
        ],
        "entrant_policy_version_ids": ["594069a3-11a9-4304-84de-14d0289ce1de",
                                       "b8aeca6a-c431-4789-ae99-d468a3c9b0b6"]
      }
    },
    {
      "id": "round_cd269017-9b26-404e-a991-9e0c3a529595",
      "round_number": 1,
      "status": "completed",
      "error": null,
      "scheduled_by": "ladder",
      "commissioner_key": "platform",
      "completed_at": "2026-08-27T00:26:46.042596Z",
      "created_at": "2026-08-27T00:25:01.652446Z",
      "round_config": { "…same two entrant_attributions as round 2…" }
    }
  ],
  "total_count": 2,
  "limit": 20,
  "offset": 0
}
```

```bash
curl -sS … | jq -r 'if type=="array" then . else .entries end | [.[]|select(.status=="completed")]|length'
```
```
2
```

No round has `status` `failed` or `discarded`; `error` is `null` on both, so there is no Temporal
message to quote.

**Fillers were in force for both rounds.** Read fresh this run (this read needs `ELEV` even though
it is a read — playbook §6):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "f8763013-a6ee-41ce-8ab2-2e208719d870",
     "policy_id": "cec7c132-959e-43a3-9add-3311473a6bd7",
     "policy_name": "negotiation-games-haggler", "version": 2,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null},
    {"policy_version_id": "44c9e9fc-3e70-4d17-b413-8a9470299575",
     "policy_id": "207eb951-3189-489b-af75-69e971c8d424",
     "policy_name": "negotiation-games-hardliner", "version": 2,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null}
  ]
}
```

The same two ids appear as `filler_policy_version_ids` inside the league object embedded in the
`/rounds` body above:

```json
"filler_policy_version_ids": ["f8763013-a6ee-41ce-8ab2-2e208719d870",
                              "44c9e9fc-3e70-4d17-b413-8a9470299575"]
```

This is not a timestamp inference: **the fillers were actually seated in both completed rounds.**
Round 1's episode seated `negotiation-games-haggler:v2` at position 2 with `"is_filler": true`;
round 2's seated `negotiation-games-hardliner:v2` at position 2 with `"is_filler": true` (see
item 3 for round 2's body verbatim, and the round-1 body below):

```bash
curl -sS "$BASE/episode-requests/ereq_801e833e-64f7-4ae8-abd0-15ad1bd182ac" "${AUTH[@]}" \
 | jq '.participants[2]'          # round 1's episode
```
```json
{
  "position": 2, "kind": "policy",
  "policy_version_id": "f8763013-a6ee-41ce-8ab2-2e208719d870",
  "policy_id": "cec7c132-959e-43a3-9add-3311473a6bd7",
  "policy_name": "negotiation-games-haggler", "version": 2,
  "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
  "is_filler": true, "is_seed": false
}
```

`log.md:46` records the registration (`50 fillers registered 200: haggler:v2=f8763013-… hardliner:v2=44c9e9fc-…
(neither champion)`) ahead of `log.md:47`'s first `trigger-round`.

Status: **TRUE** — rounds 1 (`round_cd269017-9b26-404e-a991-9e0c3a529595`, completed
2026-08-27T00:26:46Z) and 2 (`round_0f649abe-e64c-4ca6-9cfa-e6671c1b9419`, completed
2026-08-27T00:41:44Z); both seated a registered filler, so both are after the fillers were set.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"
```

Fetched 2026-08-27T00:46:5xZ. Response (bare list, verbatim):

```json
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1030.5304984710244,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "negotiation-games-integrative:v2",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 969.4695015289755,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "negotiation-games-anchor:v2",
    "recent_rounds": null
  }
]
```

```bash
… | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey-1	negotiation-games-integrative:v2	1030.5304984710244	2	2.0
2	daveey	negotiation-games-anchor:v2	969.4695015289755	2	0.0
```

```bash
… | jq -r '[.[]|select(.policy_label|test("haggler|hardliner"))]|length'
```
```
0
```

Status: **TRUE** — both champions present. `daveey` (`negotiation-games-anchor:v2`) and `daveey-1`
(`negotiation-games-integrative:v2`), each `rounds_played = 2 ≥ 1`. The leaderboard has exactly two
rows; neither filler policy appears at all (the `test("haggler|hardliner")` count is 0), which
satisfies "fillers absent or `policy_label` starting `Baseline`" via the *absent* branch.

---

## 3. Latest round's episode request completed with a `replay_url` and the right participants — **TRUE**

Latest completed round is `round_number: 2` = `round_0f649abe-e64c-4ca6-9cfa-e6671c1b9419` (item 1).
The flat `GET /episode-requests?round_id=` route is 405 now (playbook §9), so the nested route:

```bash
R=round_0f649abe-e64c-4ca6-9cfa-e6671c1b9419
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"
```
```json
[
  {"id": "ereq_7670e849-43da-4d31-86b2-77aa8b4c7a2a",
   "status": "completed",
   "created_at": "2026-08-27T00:40:02.343754Z"}
]
```

```bash
EREQ=ereq_7670e849-43da-4d31-86b2-77aa8b4c7a2a
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay",
  "participants": [
    {
      "position": 0, "kind": "policy",
      "policy_version_id": "594069a3-11a9-4304-84de-14d0289ce1de",
      "policy_id": "b9fdedb0-a875-433e-8560-76670f6ba46b",
      "policy_name": "negotiation-games-anchor", "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
      "is_filler": false, "is_seed": false
    },
    {
      "position": 1, "kind": "policy",
      "policy_version_id": "b8aeca6a-c431-4789-ae99-d468a3c9b0b6",
      "policy_id": "36b65937-04cb-48ec-a461-c1f299994ebd",
      "policy_name": "negotiation-games-integrative", "version": 2,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
      "is_filler": false, "is_seed": false
    },
    {
      "position": 2, "kind": "policy",
      "policy_version_id": "44c9e9fc-3e70-4d17-b413-8a9470299575",
      "policy_id": "207eb951-3189-489b-af75-69e971c8d424",
      "policy_name": "negotiation-games-hardliner", "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
      "is_filler": true, "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 0.65},
    {"position": 1, "score": 0.85},
    {"position": 2, "score": 0.875}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, seats 0/1 are `daveey` and
`daveey-1` with `is_filler: false`, seat 2 is the filler (rendered `Baseline` in the replay's
`results.names`, item 4).

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay" \
     -o /tmp/ep.replay -w "http=%{http_code} bytes=%{size_download}\n"
```
```
http=200 bytes=11216
```

Strict parse, two independent strict parsers:

```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "open('/tmp/ep.replay','rb').read().decode('utf-8'); print('strict UTF-8 decode: ok')"
```
```
strict UTF-8 JSON: ok
strict UTF-8 decode: ok
```

```bash
jq -r '.protocol, .results.reason' /tmp/ep.replay
```
```
negotiation.replay.v1
complete
```

`protocol` matches what the coworld declares. The declaring source, fetched this run from the
repo at `main`:

```bash
gh api repos/Metta-AI/cogame-negotiation-games/contents/tools/ci/replay_check.py --jq '.content' \
 | base64 -d | grep -n 'negotiation.replay.v1'
```
```
25:PROTOCOL = "negotiation.replay.v1"
```
and `runs/2026-08-26-negotiation-games/design.md:961-964`:
```
    parsed object must carry `protocol == "negotiation.replay.v1"`, three `names`, three
    `policyNames`, `config.seed`, `config.schedule` of length `matches`, a non-empty `events`
    array whose first event is `start` and last is `end`, and `results.reason ∈
    {"complete", "deadline"}`.
```
`results.reason == "complete"` — the preferred value, so no documented-exception argument for
`deadline` is needed.

```bash
jq -c '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline"],"scores":[0.65,0.85,0.875],"points":[26,34,35],
 "matches":[4,4,4],"deals":[4,4,4],"giveaway":[2.0,0.75,-2.75],"fallbacks":[0,0,0],
 "matchesPlayed":6,"maxMatches":6,"reason":"complete"}
```

`results.fallbacks` is the authoritative fallback count for this game: **`[0,0,0]` — zero
fallbacks on every seat.** Cross-checked against the events:

```bash
jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay
```
```
0
```

Decision events in this protocol are `offer`/`accept` kinds carrying a `scripted` boolean, not
`type=="decision"`:

```bash
jq -c '[.events[].kind]|group_by(.)|map({kind:.[0],n:length})' /tmp/ep.replay
jq '.events|length' /tmp/ep.replay
jq -r '.events[0].kind, .events[-1].kind' /tmp/ep.replay
jq -r '[.events[]|select(.kind=="offer" or .kind=="accept")|{seat,scripted}]
       |group_by([.seat,.scripted])|map({seat:.[0].seat,scripted:.[0].scripted,n:length})|@json' /tmp/ep.replay
```
```
[{"kind":"accept","n":6},{"kind":"end","n":1},{"kind":"match","n":6},{"kind":"matchEnd","n":6},{"kind":"offer","n":15},{"kind":"start","n":1}]
35
start
end
[{"seat":0,"scripted":false,"n":9},{"seat":1,"scripted":false,"n":5},{"seat":2,"scripted":true,"n":7}]
```

**Champion seats 0 (`daveey`) and 1 (`daveey-1`) made 14 decisions, every one of them
`scripted: false`. Zero scripted actions on a champion seat. All 7 scripted actions belong to
seat 2, the filler, which is what a scripted baseline is for.**

Non-trivial content — a champion offer verbatim from the round-1 replay of the same coworld,
showing the structured offer, the message and the private notes the game actually produced:

```json
{"kind":"offer","match":0,"turn":2,"seat":1,"other":0,"take":[1,0,2],"worth":[10,4],"scripted":false,
 "text":"I value balls most (4pts each), books second (2pts each), hats least (0pts). You said you need the book most. I'll take all balls and the book, you get all hats. Fair?",
 "notes":"Ratchet values book highly. I value balls and book. Hats worth 0 to me. Offering to take 1 book (2pts) + 2 balls (8pts) = 10pts total, leaving Ratchet with 4 hats. Need to learn Ratchet's valuations to optimize further."}
```

Every match ended in a deal:

```bash
jq -c '.events[]|select(.kind=="matchEnd")' /tmp/ep.replay
jq -c '.events[-1]' /tmp/ep.replay
```
```json
{"kind":"matchEnd","match":0,"outcome":"deal","payoff":[10,10],"turn":3}
{"kind":"matchEnd","match":1,"outcome":"deal","payoff":[6,10],"turn":3}
{"kind":"matchEnd","match":2,"outcome":"deal","payoff":[10,9],"turn":3}
{"kind":"matchEnd","match":3,"outcome":"deal","payoff":[10,6],"turn":2}
{"kind":"matchEnd","match":4,"outcome":"deal","payoff":[0,8],"turn":8}
{"kind":"matchEnd","match":5,"outcome":"deal","payoff":[8,8],"turn":2}
{"kind":"end","match":6,"text":"complete"}
```

Status: **TRUE** — strict UTF-8 JSON, `protocol == negotiation.replay.v1` matching the declared
string, `results.reason == "complete"`, `fallbacks [0,0,0]`, champion decisions 14/14 non-scripted
with substantive offer text and reasoning notes, 6/6 matches settled as deals.

---

## 5. Hosted game log is clean — **TRUE (CLEAN)**

```bash
EREQ=ereq_7670e849-43da-4d31-86b2-77aa8b4c7a2a
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs2.raw \
     -w "http=%{http_code} bytes=%{size_download}\n"
```
```
http=200 bytes=34608
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
decoded with `ast.literal_eval` per repr before grepping (playbook §10 — line greps on the raw
form badly undercount):

```
containers: ['===== container: coworld-init-config =====', '===== container: bedrock-sidecar =====',
             '===== container: game =====', '===== container: worker =====']
decoded chars: 34481 lines: 119
```

```bash
grep -nEc 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs2.txt
grep -nE  'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs2.txt || echo CLEAN
```
```
0
CLEAN
```

Same grep against round 1's episode (`ereq_801e833e-64f7-4ae8-abd0-15ad1bd182ac`, 41189 bytes
raw / 41050 decoded) also returned `CLEAN`.

No Bedrock-capacity symptom appeared, so no cross-check against another LLM coworld's log was
required and none is claimed here.

Status: **TRUE** — all four forbidden patterns absent from the decoded log of the latest round's
episode across all four containers.

---

## 6. Public page uses the static replay path, with a featured match — **TRUE**

**Source used: the SSR payload of `https://softmax.com/negotiation-games` plus the replay-session
call the page's own JS makes.** The raw-HTML grep is recorded first and is *not* treated as a
false negative (playbook §Featured match: the page is client-rendered for the iframe platform-wide).

```bash
curl -sS "https://softmax.com/negotiation-games" -o /tmp/page2.html -w "http=%{http_code} bytes=%{size_download}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page2.html || echo "(no match — page is client-rendered)"
```
```
http=200 bytes=639471
(no match — page is client-rendered)
```

Featured match, server-rendered into the page at `state.playlist[0]` (fetched 2026-08-27T00:44:1xZ,
unescaped from the SSR string):

```json
"playlist":[{"episodeId":"26664cb7-bb7b-4e48-a0c2-bd4da6086706",
  "coworldId":"cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5",
  "coworldName":"negotiation-games","coworldVersion":"0.1.1",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay",
  "finishedAt":"2026-08-27T00:41:35.709566Z","roundNumber":2,"episodeNumber":1,
  "code":"negotiation-games.r2.e1",
  "matchup":{"divisionId":"div_5699e6c3-6cf1-4a38-9e69-e2b954332c91","divisionName":"Competition",
    "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
             "score":1030.5304984710244,"score_label":"MMR","score_value_type":"integer",
             "rounds_played":2,"episode_wins":1,"episodes_played":null,"win_rate":1,
             "policy_label":"negotiation-games-integrative:v2","recent_rounds":null},
    "second":{"rank":2,"play…
```

A featured match **is** present, and it is the latest round's episode — the same `replayUrl` as
item 3's `replay_url`.

The iframe `src` comes from the call the page's JS makes with that playlist entry:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5/sha256%3A06acbd012316b207fcd998ba50bde7d7c32447b9e93587d7203ede334219cca1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay&v=2",
  "ready": true
}
```

Path shape check, term by term:
- `/v2/coworlds/replays/static/` — the **static** route. **No `/client/replay` anywhere in it.**
- `<cow_id>` = `cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5` — matches `STATE.coworld.cow_id`.
- `<sha>` = `sha256%3A06acbd012316b207fcd998ba50bde7d7c32447b9e93587d7203ede334219cca1` — the
  coworld's manifest hash, URL-encoded.
- ends `/index.html?replay=<s3 url>`, and `ready: true` — the two conditions the playbook gives
  for static delivery.

The manifest hash is confirmed against the canonical coworld row (secondary source, fetched
2026-08-27T00:47:5xZ):

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|.[]|select(.name=="negotiation-games")
          |{id,name,version,canonical,replay_viewer,featured_match,manifest_hash}'
```
```json
{
  "id": "cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5",
  "name": "negotiation-games",
  "version": "0.1.1",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null,
  "manifest_hash": "sha256:06acbd012316b207fcd998ba50bde7d7c32447b9e93587d7203ede334219cca1"
}
{
  "id": "cow_67fd3ed5-0077-43cd-9e71-deeb879fb342",
  "name": "negotiation-games",
  "version": "0.1.0",
  "canonical": false,
  "replay_viewer": null,
  "featured_match": null,
  "manifest_hash": "sha256:fe7ff7bb9652e03270fe789812523e694d09e38db6d6b92a61b6e7573f42409b"
}
```

(`featured_match: null` on this endpoint is the known platform-wide value — it is null for every
coworld and is not evidence either way; the featured match is proved from `state.playlist[0]`
above. `canonical: true` is on v0.1.1, the version under test.)

Status: **TRUE** — featured match present (round 2, episode 1), iframe `src` is the static
`…/v2/coworlds/replays/static/<cow_id>/<manifest sha>/index.html?replay=<s3 url>` path with
`ready: true`; no `/client/replay` URL is involved.

---

## 7. Certification declared the static bundle — **TRUE**

**Documented exception to "fetch fresh": this is an artifact of *this run's* release dispatch, not a
live endpoint. Source read: the committed `runs/2026-08-26-negotiation-games/release-result.json`
(the copy phase 40 downloaded from release run `33026182056` and committed). It was present, so no
re-download from `gh run download` was needed.**

```bash
jq -r '.certify.replay_liveness' runs/2026-08-26-negotiation-games/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -r '.certify | keys' runs/2026-08-26-negotiation-games/release-result.json
```
```json
[
  "ok",
  "output_tail",
  "replay_liveness"
]
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`
exactly. Read from the committed `runs/<run>/release-result.json`, not from `/tmp`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

**Documented exception to "fetch fresh": the rendered evidence comes from a `viewer-check.yml` run
dispatched during this phase-60 execution, not from an earlier run.** No render is described here
that did not come out of that artifact.

### (a) Dispatch

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5/sha256%3A06acbd012316b207fcd998ba50bde7d7c32447b9e93587d7203ede334219cca1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay&v=2'
# dispatch_at = 2026-08-27T00:44:33Z   (SRC is item 6's iframe src, character for character)
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
```
```
33027843730	2026-08-27T00:44:34Z	in_progress
33027506937	2026-08-27T00:38:16Z	completed
33025003314	2026-08-26T23:56:14Z	completed
```

The new run is the one created **after** the dispatch timestamp (`33027843730`, created
00:44:34Z > dispatch 00:44:33Z) — found by sorting on `createdAt`, not by taking "the latest".

```bash
gh run watch 33027843730 -R Metta-AI/coworld-builder --exit-status; echo "exit=$?"
gh run view  33027843730 -R Metta-AI/coworld-builder --json status,conclusion
```
```
exit=0
{"conclusion":"success","status":"completed"}
```

```bash
gh run download 33027843730 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-26-negotiation-games/viewer-check
ls -la runs/2026-08-26-negotiation-games/viewer-check/
```
```
-rw-r--r-- 1 root root      0 Aug 27 00:45 smoke-stderr.txt
-rw-r--r-- 1 root root    482 Aug 27 00:45 smoke-stdout.txt
-rw-r--r-- 1 root root   1378 Aug 27 00:45 viewer-smoke.json
-rw-r--r-- 1 root root 347662 Aug 27 00:45 viewer-smoke.png
```

That directory is committed alongside this file.

> Note for the record: an earlier dispatch this run (`33027506937`, 00:38:16Z) rendered the
> *round-1* replay, which was the featured match at that moment. Round 2 completed at 00:41:44Z
> and became the featured match, so that run's artifact was **not** used and **not** committed —
> everything below comes from `33027843730`, which rendered exactly the item-6 `src`.

### (b) Readouts, verbatim from `runs/2026-08-26-negotiation-games/viewer-check/viewer-smoke.json`

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' …/viewer-smoke.json
```
```json
{"loaded":true,"ms":2909,"clock":"MATCH 0 / 6","scorebug":"daveey 0 PTS 0.00 daveey-1 0 PTS 0.00 Ratchet 0 PTS 0.00","feed_lines":71}
```

```bash
jq -c '.signals' …/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' …/viewer-smoke.json
```
```
no failure
```
(the raw field in the file is `"failure": null`)

Three clock readouts:

| scrub position | `clock` readout |
|---|---|
| 0 %   | `MATCH 0 / 6` |
| 50 %  | `MATCH 4 / 6 · TURN 2 / 10 · DAVEEY TO MOVE` |
| 100 % | `FINAL · 6 MATCHES` |

**All three differ.** A `#scrub` control was present — the json carries a real `scrub` array, not
the `"(no #scrub…)"` sentinel — so there is no missing-scrubber legibility caveat to raise.

Remaining fields from the same file, for completeness:

```json
"status": "REPLAY", "loading_text": "LOADING REPLAY…", "bundle": null, "replay": null, "soak": null,
"canvas_text": {"total":915,"outside":0,"ellipsized":0,"never_inside":0,
                "never_inside_samples":[],"distinct_capped":false,"samples":[]},
"console_tail": ["[bridge] loading","[bridge] ready"]
```

`smoke-stdout.txt` verbatim:
```
{"loaded":true,"ms":2909,"clock":"MATCH 0 / 6","scorebug":"daveey 0 PTS 0.00 daveey-1 0 PTS 0.00 Ratchet 0 PTS 0.00","feed_lines":71}
scrub readouts: 0%="MATCH 0 / 6"  50%="MATCH 4 / 6 · TURN 2 / 10 · DAVEEY TO MOVE"  100%="FINAL · 6 MATCHES"
canvas text: 915 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
artifacts: …/viewer-smoke.png …/viewer-smoke.json
```
`smoke-stderr.txt` is 0 bytes.

**Item 8 gate:** `loaded: true` ✔ (and independently corroborated by
`signals.data_replay_loaded == "true"` and `bridge: ["loading","ready"]`), and the three clock
readouts differ ✔. **TRUE.**

### (c) The replay JSON the viewer was asked to draw

Early:
```
match turn seat kind      scripted take     text
      —    —    start     —        —        —
0     —    —    match     —        —        —
0     1    0    offer     false    [3,1,2]  I need the hat most - it's worth everything to me. Happy to negotiate…
0     2    1    offer     false    [3,0,2]  You want the hat most - I value books and balls equally at 2pts each,…
0     3    0    accept    false    [0,1,0]  Perfect - this leverages our different preferences optimally. You get…
0     3    —    matchEnd  —        —        —
1     —    —    match     —        —        —
1     1    0    offer     false    [0,2,1]  I need hats most - they're worth the most to me. You get the books and…
1     2    2    offer     TRUE     [2,0,1]  (scripted baseline — no message)
1     3    0    accept    false    [0,2,0]  Fair deal. You clearly value books and the ball; I get what matters mo…
1     3    —    matchEnd  —        —        —
```

Middle (events 14–22):
```
2     3    1    accept    false    [1,1,0]  Perfect! You've identified my true values exactly - books are worth 8p…
2     3    —    matchEnd  —        —        —
3     —    —    match     —        —        —
3     1    1    offer     false    [3,0,0]  I value books and hats highly (2pts each), but balls not at all (0pts)…
3     2    0    accept    false    [0,2,2]  Perfect deal for me. Hats and balls are exactly what I need. Let's loc…
3     2    —    matchEnd  —        —        —
4     —    —    match     —        —        —
4     1    2    offer     TRUE     [0,2,2]  (scripted baseline)
4     2    0    offer     false    [0,0,2]  I need the balls most - they're essential to me. You can have the book…
```

Late (last 8):
```
4     7    2    offer     TRUE     [0,2,2]  (scripted baseline)
4     8    0    accept    false    [2,0,0]  Let's close this deal. You get the hats and balls you want.
4     8    —    matchEnd  —        —        —
5     —    —    match     —        —        —
5     1    2    offer     TRUE     [1,1,0]  (scripted baseline)
5     2    1    accept    false    [0,2,2]  Great deal! I value balls highly and hats not at all. You clearly valu…
5     2    —    matchEnd  —        —        —
6     —    —    end       —        —        complete
```

```bash
jq -r '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline"],"scores":[0.65,0.85,0.875],"points":[26,34,35],
 "matches":[4,4,4],"deals":[4,4,4],"giveaway":[2.0,0.75,-2.75],"fallbacks":[0,0,0],
 "matchesPlayed":6,"maxMatches":6,"reason":"complete"}
```

### Spectator judgment

The screenshot in `runs/2026-08-26-negotiation-games/viewer-check/viewer-smoke.png` is the frame
after the 100 % seek, so it shows the end state, and it is **legible and unmistakably this game**.
Top-left is the `NEGOTIATE` wordmark; the centre of the transport strip reads `FINAL · 6 MATCHES`;
top-right carries the `REPLAY` / `« LOG` toggles. Under it runs a three-seat scorebug — `daveey
26 PTS 0.65`, `daveey-1 34 PTS 0.85`, `Ratchet 35 PTS 0.88`, each with four filled deal pips — and
under that a chip strip of the six settled matches, `DEAL 10-10 · DEAL 6-10 · DEAL 10-9 · DEAL
10-6 · DEAL 0-8 · DEAL 8-8`. **Those six chips are the six `matchEnd` payoffs in the replay JSON,
in order, exactly** — the picture and the record agree with no interpretation needed. The last
deal's terms are spelled out in words beneath (`daveey-1: books ×2 · hats ×0 · balls ×4 ·
Ratchet: books ×7 · hats ×1 · balls ×0`), which is the last `accept` event's `take` and its
complement.

The playfield is the negotiation table itself: two cog avatars facing each other across it, each
with its **valuation strip** printed under its name (`books ×2 · hats ×0 · balls ×4 = 10` on the
left, `books ×7 · hats ×1 · balls ×0 = 10` on the right — the hidden per-item values the design
deliberately shows the spectator so a greedy offer reads as greedy), the third seat greyed out in
the middle labelled `SITTING OUT` (correct: only two of three seats play any given match), the
pool items rendered as small book/hat/ball icons on the felt, `worth 8` chips on the offer cards,
and the accepted offer's message quoted on the left seat's card. Over the table sits the endcard —
`FINAL — 6 MATCHES`, `Ratchet TAKES THE TABLE`, and a standings table `1 Ratchet 0.88 / 35 / 4 /
-2.8 · 2 daveey-1 0.85 / 34 / 4 / 0.8 · 3 daveey 0.65 / 26 / 4 / 2.0`. Those are `results.scores`,
`results.points`, `results.deals` and `results.giveaway` rounded for display, in rank order.

It is not a still. Along the bottom is the transport strip: a play button, a scrubber with **beat
markers** colour-coded by event kind (green diamonds at the six `accept`/deal beats, red and blue
ticks at the offers between them — the beat count reads consistently with the 35 events), and the
frame counter `35 / 35`. Motion is proved independently of the picture by the three seeks: at 0 %
the clock reads `MATCH 0 / 6` with an all-zero scorebug (the pre-roll frame), at 50 % it reads
`MATCH 4 / 6 · TURN 2 / 10 · DAVEEY TO MOVE`, and at 100 % `FINAL · 6 MATCHES`. Match 4 at turn 2
with seat 0 to move is precisely where the recorded event list sits at the halfway point — the
`4 2 0 offer` row in the middle excerpt above. The viewer drew its first frame in 2909 ms, laid
out 915 canvas text draws with **0 outside the canvas and 0 ellipsized**, emitted 71 feed lines,
and logged `[bridge] loading` → `[bridge] ready` with no error.

**Chrome provenance:** it reads as the babel lineage, which is what the design promised — the same
transport strip with a centred clock and right-hand toggles, the same beat-marked scrubber with a
frame counter, the same per-seat scorebug band, the same modal endcard with a ranked standings
table, the same muted amber-on-near-black palette and the same pixel cog avatars. What is new is
game-specific and additive rather than a rewrite: the negotiation table with its pool items, the
per-seat valuation strips, the `SITTING OUT` third seat and the `DEAL a-b` chip strip. This is not
the cogame-gridlock failure mode (a different product sharing only the element ids); it is the
starter's chrome with a bargaining table dropped into the playfield.

One legibility observation, non-blocking, for the coordinator: at the 100 % frame the endcard is
opaque and centred over the table, so the two seats' offer cards and valuation strips sit behind
it at reduced contrast. The design says the endcard is dismissed by any seek, so a spectator who
scrubs back sees the table unobstructed — but the *first* thing an arriving spectator sees on a
finished replay is the endcard covering the board. Worth noting for phase 30 if the viewer is
revisited; it does not affect any item's verdict.

Status: **TRUE** — `loaded: true`, three differing clock readouts, a screenshot that is legible,
in-lineage, and reconciles beat-for-beat with the replay JSON.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 1 & 2, both `completed`, `error: null`, both seated a registered filler |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — `daveey` and `daveey-1`, `rounds_played` 2 each; no filler rows |
| 3 | Latest round's episode completed with replay + participants | **TRUE** — `ereq_7670e849…` `completed`, `replay_url` set, seats 0/1 = champions |
| 4 | Replay bytes valid and show the game | **TRUE** — strict UTF-8 JSON, `negotiation.replay.v1`, `reason: complete`, `fallbacks [0,0,0]`, 14/14 champion decisions non-scripted |
| 5 | Hosted game log clean | **TRUE** — `CLEAN`, 0 matches across 4 containers (decoded, 34481 chars) |
| 6 | Public page uses the static replay path | **TRUE** — featured match r2.e1; `…/replays/static/<cow>/<sha>/index.html?replay=…`, `ready: true` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — run `33027843730`, `loaded: true` in 2909 ms, three differing clocks, legible in-lineage render |

**Verdict: all-true (8 / 8). Nothing NOT FETCHED. Wall clock used: ~22 minutes of the 75-minute bound.**
