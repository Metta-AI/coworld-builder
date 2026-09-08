# VERIFY — battlecode-2023   (2026-09-08T17:30Z)

Verdict: **all-true — 8 / 8**

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | TRUE — rounds 1 and 2, both `completed`, 0 failed / 0 discarded |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE — daveey-1 + daveey, `rounds_played: 2` each; no filler rows |
| 3 | Latest round's episode request completed with a replay | TRUE — `ereq_66018a01-…` completed, `replay_url` non-null, both champions seated |
| 4 | Replay bytes valid and show the game | TRUE — strict UTF-8 JSON, `protocol` matches, `result.reason == "complete"`, 0 fallbacks of 2 decisions |
| 5 | Hosted game log clean | TRUE — CLEAN, zero matches for all four patterns |
| 6 | Public page uses the static replay path | TRUE — `…/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=…`, `ready: true` |
| 7 | Certification declared the static bundle | TRUE — `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Viewer executed and judged | TRUE — `loaded: true`, three differing clock readouts, 15 s soak advanced |

**One substantive non-blocking finding (FINDING A, under check 4):** in each of the two completed
rounds one champion wrapped its doctrine in a `{"protocol":…,"doctrine":{…}}` envelope, so all
twelve knobs landed in `sheet_unknown_fields` and that seat played the **schema-default** doctrine.
This is documented behaviour (`design.md` lines 671–676: unknown key → that field's default, "a cog
can never forfeit a match by answering badly — only by answering weakly"), it produces **zero**
fallbacks, and it does not make any check false — but it means roughly half the seats are currently
being decided on the default sheet rather than the cog's, and the endcard's doctrine card
consequently states a plan the cog did not write. Details and per-round table under check 4.

**Seven legibility findings for phase 30** are recorded under check 8; two of them
(bc26 nouns "the alliance held / kings built / cheese delivered / cats damaged" on a bc23 endcard,
and doctrine cards clipping their last line) are the **same two** the bc25 sibling raised on
2026-09-08 and are still unfixed at `client/replay_broadcast.html`.

Run: `2026-09-08-battlecode-2023` · slug `battlecode-2023` · coworld **name** `battlecode`
(`cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7`, v0.6.0, `canonical: true`, manifest_sha
`sha256:a4ae44ab88615b434ccef7b6d6edc82bb8cdc6aec397d9f3efcaa89c70ef133e`)
League `league_e3244a55-f8b9-486b-9412-51dc1f56c978` ("Battlecode 2023 — Tempest", short-name
`bc23`) · Division `div_dc5f977f-2f98-4796-8cdd-87ecf673704f`
Base: `BASE=https://softmax.com/api/observatory/v2`
Headers sent (values never printed): `Authorization: Bearer $SOFTMAX_TOKEN`,
`User-Agent: coworld-builder/1.0`, and on artifact/elevated reads `X-Use-Elevated-Privileges: true`.

Public page for **this** league: `https://softmax.com/battlecode/bc23` (the game's default page
`https://softmax.com/battlecode` belongs to the **bc26** league and is not this run's).

Fillers `battlecode-lemonade:v1` (`9fdf3e34-ab4d-4246-8c6e-136eea314b30`) and
`battlecode-examplefuncsplayer23:v1` (`7fe2fb41-b76b-4cdf-b962-8491e8cd060a`) were registered
**before** the first trigger-round (log.md 2026-09-08T17:02:01Z: "fillers 200 … unpause 200;
trigger 200 … round 1 pending"), so **every** completed round counts toward check 1. Neither filler
was ever seated: both rounds ran the two champions head-to-head.

Wall-clock bound for polling: 75 minutes from 2026-09-08T17:05Z → 18:20Z. Two completed rounds were
reached at **17:17:45Z**, 13 minutes in; the bound was not approached. Every check below was fetched
fresh during this session, with the two documented exceptions: check 7 (the committed
`release-result.json` from phase 40) and check 8's rendered evidence (the artifact of the
`viewer-check.yml` run **dispatched in this session**, `34256712314`).

---

## 1. ≥2 completed rounds after fillers were set

Poll log (all `GET $BASE/rounds?league_id=$L&limit=20`, HTTP 200 every time; the coordinator owns
`log.md` and the Asana heartbeat, so the polls are recorded here):

| poll (UTC) | rounds seen |
|---|---|
| 17:06:39Z | r1 completed |
| 17:07:24Z | r1 completed |
| 17:08:10Z | r1 completed |
| 17:08:55Z | r1 completed |
| 17:09:40Z | r1 completed |
| 17:10:26Z | r1 completed |
| 17:11:25Z | r1 completed |
| 17:12:10Z | r1 completed |
| 17:12:55Z | r1 completed |
| 17:13:40Z | r1 completed |
| 17:14:26Z | r1 completed |
| 17:15:11Z | r1 completed |
| 17:15:56Z | r1 completed |
| 17:16:25Z | **r2 pending**, r1 completed |
| 17:17:05Z | r2 pending, r1 completed |
| **17:17:45Z** | **r2 completed**, r1 completed |
| 17:18:26Z / 17:19:06Z / 17:19:46Z | r2 completed, r1 completed (stable) |

Intermediate poll body at 17:16:25Z, pasted so the progression is on the record:

```json
[{"round_number":2,"status":"pending","completed_at":null,"error":null},
 {"round_number":1,"status":"completed","completed_at":"2026-09-08T17:02:26.773259Z","error":null}]
```

**Final fetch — 2026-09-08T17:20:34Z**

```
GET $BASE/rounds?league_id=league_e3244a55-f8b9-486b-9412-51dc1f56c978&limit=20
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
```
(this deployment wraps `/rounds` in `{"entries":[…]}`; normalised with
`jq 'if type=="array" then . else .entries end'`)

```json
[
  {
    "id": "round_dd56e5e4-f5c5-4ab1-bc0f-f7de36abd916",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "skip_kind": null,
    "completed_at": "2026-09-08T17:17:44.056041Z",
    "entrants": [
      {
        "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
        "subject_type": "player",
        "policy_version_id": "11d10cb0-c000-42ec-be69-04e8c078719b",
        "league_policy_membership_id": "lpm_19aaac79-22e0-4ef3-9152-072ca75b05fe"
      },
      {
        "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
        "subject_type": "player",
        "policy_version_id": "dc1a2710-de27-48bc-b1ae-4dde4c15b07d",
        "league_policy_membership_id": "lpm_504e320e-48f9-4d88-ade4-98f18729e10b"
      }
    ]
  },
  {
    "id": "round_ae192a12-8d0c-4ba8-bfc7-335886bc208b",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "skip_kind": null,
    "completed_at": "2026-09-08T17:02:26.773259Z",
    "entrants": [
      {
        "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
        "subject_type": "player",
        "policy_version_id": "11d10cb0-c000-42ec-be69-04e8c078719b",
        "league_policy_membership_id": "lpm_19aaac79-22e0-4ef3-9152-072ca75b05fe"
      },
      {
        "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
        "subject_type": "player",
        "policy_version_id": "dc1a2710-de27-48bc-b1ae-4dde4c15b07d",
        "league_policy_membership_id": "lpm_504e320e-48f9-4d88-ade4-98f18729e10b"
      }
    ]
  }
]
```

```
$ … | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

Status: **TRUE** — rounds **1** and **2**, both `"status": "completed"` (17:02:26.773259Z and
17:17:44.056041Z), `error: null` and `skip_kind: null` on both. **Zero** `failed` or `discarded`
rounds exist in the league (the list has exactly these two entries). Both rounds' entrants are the
two champion policy versions `11d10cb0-…` (daveey / duel) and `dc1a2710-…` (daveey-1 / alchemist).
The fillers were registered at 2026-09-08T17:02:01Z per `log.md`, in the same phase-50 step and
**before** the `trigger-round` call that produced round 1 (round 1 was still `pending` at that
point and settled 25 s later), so **both** completed rounds are after-fillers rounds.

---

## 2. Both champions ranked; fillers absent / Baseline

```
GET $BASE/divisions/div_dc5f977f-2f98-4796-8cdd-87ecf673704f/leaderboard
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
```
fetched **2026-09-08T17:20:34Z** (after round 2) — bare JSON list, pasted verbatim:

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
    "policy_label": "battlecode-bc23-alchemist:v1",
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
    "policy_label": "battlecode-bc23-duel:v1",
    "recent_rounds": null
  }
]
```

Earlier fetch of the same endpoint at **17:05:1xZ** (after round 1 only), pasted so the
progression is on the record:

```json
[
  {"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":1016.0,"score_label":"MMR","rounds_played":1,"episode_wins":1.0,"win_rate":1.0,
   "policy_label":"battlecode-bc23-alchemist:v1"},
  {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":984.0,"score_label":"MMR","rounds_played":1,"episode_wins":0.0,"win_rate":0.0,
   "policy_label":"battlecode-bc23-duel:v1"}
]
```

Status: **TRUE** — `daveey-1` (`battlecode-bc23-alchemist:v1`) rank 1, `rounds_played: 2`;
`daveey` (`battlecode-bc23-duel:v1`) rank 2, `rounds_played: 2`. Both ≥ 1, and both are the
STATE champion policies. Neither filler (`battlecode-lemonade:v1`,
`battlecode-examplefuncsplayer23:v1`) appears anywhere in the list — the "fillers absent" branch
of the requirement. The list has exactly two rows.

---

## 3. The latest round's episode request completed with a replay and the right participants

Latest completed round = **round 2**, `round_dd56e5e4-f5c5-4ab1-bc0f-f7de36abd916` (from the
check-1 fetch above).

The flat `GET $BASE/episode-requests?round_id=…` route 405s on this deployment, confirmed fresh
this run (`playbooks/observatory-api.md` §9):

```
$ curl -sS -o /dev/null -w 'HTTP %{http_code}\n' \
    "$BASE/episode-requests?round_id=round_dd56e5e4-f5c5-4ab1-bc0f-f7de36abd916&limit=20" …
HTTP 405
```

so the **nested** route was used:

```
GET $BASE/rounds/round_dd56e5e4-f5c5-4ab1-bc0f-f7de36abd916/episode-requests
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
```
fetched 2026-09-08T17:20:42Z:

```json
[
  {
    "id": "ereq_66018a01-7a9a-4f54-bff7-92cc373662f7",
    "status": "completed",
    "replay_url": "https://softmax-public.s3.amazonaws.com/replays/16e08a05-82d7-4447-ad97-ee53be22557f.replay"
  }
]
```

```
GET $BASE/episode-requests/ereq_66018a01-7a9a-4f54-bff7-92cc373662f7
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
| jq '{status, replay_url, participants, participant_scores}'
```
fetched 2026-09-08T17:20:46Z:

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/16e08a05-82d7-4447-ad97-ee53be22557f.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "11d10cb0-c000-42ec-be69-04e8c078719b",
      "policy_id": "06e88aa6-74a4-44ef-84db-a7ac79078e9a",
      "policy_name": "battlecode-bc23-duel",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "dc1a2710-de27-48bc-b1ae-4dde4c15b07d",
      "policy_id": "c8150cd2-d26b-4da6-89fa-f1ce64ff1950",
      "policy_name": "battlecode-bc23-alchemist",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    { "position": 0, "score": 234.33333333333334 },
    { "position": 1, "score": 464.6666666666667 }
  ]
}
```

Status: **TRUE** — `"status": "completed"`, non-null `replay_url`, and `participants` names
`daveey` (`battlecode-bc23-duel` v1, policy_version `11d10cb0-…`, the STATE champion-1 version id
seated in `round_config.entrant_attributions`) and `daveey-1` (`battlecode-bc23-alchemist` v1,
policy_version `dc1a2710-…`, champion 2). Both `is_filler: false`; no filler seats were needed
(two ranked players, two seats), so no `Baseline (N)` rows appear. `participant_scores` are
non-degenerate (234.33 vs 464.67).

*(Round 1's episode request, fetched the same way at 17:05Z, was also `completed`:
`ereq_a2aa2be9-8e08-4763-a564-6da95c4b8fb9` →
`https://softmax-public.s3.amazonaws.com/replays/f62806cf-fd55-4d14-80aa-f0224238b5ed.replay`.)

---

## 4. Replay bytes are valid and show the game

```
$ curl -sSL 'https://softmax-public.s3.amazonaws.com/replays/16e08a05-82d7-4447-ad97-ee53be22557f.replay' -o /tmp/ep.replay -w 'HTTP %{http_code} bytes=%{size_download}\n'
HTTP 200 bytes=140209
```

Strict UTF-8 JSON parse (`jq -e . /tmp/ep.replay`, a strict parser — not a browser):

```
strict UTF-8 JSON: ok
```

```
$ jq -r '.protocol, .format, .version, .game_version, .year' /tmp/ep.replay
cogame.battlecode.v1
cogame-battlecode-replay
1
GV09
bc23

$ jq -r '.result.reason' /tmp/ep.replay
complete

$ jq -r '.results' /tmp/ep.replay
null
```

(As on every Battlecode year, the episode result sits under the **singular** key `result`;
`.results` is `null`. `design.md` line 1301 f. pins `reason` on the `result` object.)

**Protocol matches the manifest.** The manifest declares `game.protocols.{player,global}` as URIs
to `docs/PROTOCOL.md`, and that document's line 1 is the protocol id; the bc23 section restates it,
and the manifest carries the bc23 variant the replay says it played:

```
$ gh api repos/Metta-AI/cogame-battlecode/contents/coworld_manifest_template.json -H 'Accept: application/vnd.github.raw' | jq -c '.game.protocols'
{"player":{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"},"global":{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"}}

$ gh api repos/Metta-AI/cogame-battlecode/contents/docs/PROTOCOL.md -H 'Accept: application/vnd.github.raw' | grep -n 'cogame\.battlecode\.v1\|^## bc23'
1:# `cogame.battlecode.v1`
...
432:## bc23
435:The protocol id is **unchanged** — `cogame.battlecode.v1`. …

$ gh api …/coworld_manifest_template.json … | jq -r '.variants[]|"\(.name)\t\(.game_config.year)\t\(.game_config.gamesPerMatch)\t\(.game_config.num_agents)"'
Battlecode 2026 — Uneasy Alliances (2 seats)	bc26	3	2
Battlecode 2020 — Soup (2 seats)	bc20	3	2
Battlecode 2021 — Campaign (2 seats)	bc21	3	2
Battlecode 2024 — Breadwars (2 seats)	bc24	3	2
Battlecode 2025 — Chromatic Conflict (2 seats)	bc25	3	2
Battlecode 2023 — Tempest (2 seats)	bc23	3	2
```

```
$ jq -c '.config, .plan' /tmp/ep.replay
{"year":"bc23","pool":"mixed","seed":1002640040,"gamesPerMatch":3,"maxRounds":2000,"num_agents":2}
{"maps":["Scatter","HideAndSeek","Rainbow"],"side_a_slots":[0,1,0],"abandon_after":[-1,-1,-1],"max_rounds":2000}
```

**Decisions and fallbacks.** This game's "decision" is the one sealed doctrine turn per seat
(`design.md` §Decisions — one parallel batch of two LLM calls, `doctrineBudgetMs = 45000`):

```
$ jq -c '.events[]|select(.kind|test("doctrine"))' /tmp/ep.replay
{"kind":"doctrine_requested","ms":0,"slot":0,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_requested","ms":0,"slot":1,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_received","ms":15990,"slot":0,"attempt":1,"latency_ms":15990,"defaults_applied":0,"unknown_fields":1}
{"kind":"doctrine_received","ms":15990,"slot":1,"attempt":1,"latency_ms":15990,"defaults_applied":0,"unknown_fields":7}

$ jq -r '[.events[]|select(.kind|test("fallback"))]|length' /tmp/ep.replay
0
$ jq -r '[.seats[]|select(.fallback!=null)]|length' /tmp/ep.replay
0
```

**2 of 2 decisions answered on attempt 1, 0 fallbacks.** Both seats are `policy: "llm"` on the
`lemonade` chassis:

```
$ jq -r '.seats[]|[.slot,.alias,.name,.policy,.chassis,(.sheet|tostring),(.sheet_unknown_fields|tostring),(.sheet_defaults_applied|tostring),(.fallback|tostring)]|@tsv' /tmp/ep.replay
0	Clan Ash	daveey	llm	lemonade	{"opening":"launcher_rush","launcher_ratio":72,"well_priority":"mana","elixir_tech":"never","elixir_spend":"accelerating_anchors","anchor_round":1100,"anchor_budget":15,"island_priority":"nearest","amplifier_use":"escort","destabilizer_use":"siege","retreat_on_launcher_loss":"regroup","carrier_throw":75}	["notes"]	[]	null
1	Clan Basil	daveey-1	llm	lemonade	{"opening":"balanced","launcher_ratio":45,"well_priority":"balanced","elixir_tech":"mid","elixir_spend":"accelerating_anchors","anchor_round":400,"anchor_budget":35,"island_priority":"nearest","amplifier_use":"one","destabilizer_use":"defend","retreat_on_launcher_loss":"regroup","carrier_throw":25}	["protocol","game_version","year","slot","alias","doctrine","notes"]	[]	null
```

Seat 0 (`daveey`, `battlecode-bc23-duel`) is a fully non-default sheet — every one of the twelve
knobs differs from the schema default printed in the replay's own `prompt_preamble`
(`balanced / 45 / balanced / mid / accelerating_anchors / 400 / 35 / nearest / one / defend /
regroup / 25`): `launcher_rush`, `72`, `mana`, `never`, anchor at `1100` on `15 %`, `escort`,
`siege`, `carrier_throw 75`. Its `notes` are map-specific and freshly generated:

```
$ jq -r '.seats[0].notes[0:180]' /tmp/ep.replay
DOCTRINE: Launcher supremacy through opening mana starve. PRIMARY TARGET: Enemy HQ at (41,15) on Scatter; (4,22) on HideAndSeek; (38,28) on Rainbow. Strike group (launchers + siege
$ jq -r '.seats[1].notes[0:180]' /tmp/ep.replay
**Game 1 (Scatter, 8 islands):** Target islands 0, 1, 2 — the three largest at 15, 15, 8 tiles each. These form a loose cluster and are most defensible. Hold the other 3 of the rem
```

⚠ **Seat 1 (`daveey-1`) wrapped its sheet in a protocol envelope and therefore played the default
doctrine — see FINDING A below.** Its `sheet_submitted` is:

```
$ jq -r '.seats[1].sheet_submitted' /tmp/ep.replay | head -c 330
{"protocol":"cogame.battlecode.v1","game_version":"GV09","year":"bc23","slot":1,"alias":"Clan Basil","doctrine":{"opening":"carrier_eco","launcher_ratio":42,"well_priority":"balanced","elixir_tech":"early","elixir_spend":"accelerating_anchors","anchor_round":280,"anchor_budget":55,"island_priority":"contested","amplifier_use":"one","destabilizer_use":"defend",…
```

so all twelve knobs sat under a `doctrine` key, were recorded in `sheet_unknown_fields`
(`["protocol","game_version","year","slot","alias","doctrine","notes"]`), and the applied `sheet`
is the schema default. This is **documented, designed behaviour**, not an engine defect —
`design.md` §"The bc23 doctrine sheet" (lines 671–676):

> Unknown key, wrong type or out-of-range value → **that field's default**, recorded in
> `sheet_defaults_applied` / `sheet_unknown_fields`. A sheet can never be rejected, so a cog can
> never forfeit a match by answering badly — only by answering weakly.

Event stream — 155 events, all game-substance kinds:

```
$ jq -r '[.events[].kind]|group_by(.)|map("\(.[0])\t\(length)")|.[]' /tmp/ep.replay
anchor_built	44
conquest_progress	6
doctrine_received	2
doctrine_requested	2
duel	57
episode_end	1
episode_start	1
first_action	6
game_end	3
game_start	3
island_captured	28
island_lost	1
well_transformed	1
```

Result — a full **three-game** match, 2000 rounds on each of three real bc23 maps, decided 2–1:

```
$ jq -c '{reason:.result.reason,names:.result.names,aliases:.result.aliases,scores:.result.scores,wins:.result.wins,points:.result.points,games:[.result.games[]|{map,end_reason,winner,rounds_played,islands_held_end,anchors_placed}]}' /tmp/ep.replay
{"reason":"complete","names":["daveey","daveey-1"],"aliases":["Clan Ash","Clan Basil"],"scores":[234.33333333333334,464.6666666666667],"wins":[1,2],"points":[[25,74,4],[74,25,95]],"games":[{"map":"Scatter","end_reason":"more_sky_islands","winner":1,"rounds_played":2000,"islands_held_end":[1,3],"anchors_placed":[1,4]},{"map":"HideAndSeek","end_reason":"more_sky_islands","winner":0,"rounds_played":2000,"islands_held_end":[11,3],"anchors_placed":[11,3]},{"map":"Rainbow","end_reason":"more_sky_islands","winner":1,"rounds_played":2000,"islands_held_end":[0,9],"anchors_placed":[0,9]}]}
```

`reason` is `"complete"` — **not** the `deadline` branch, so no deadline exception is being claimed.

Status: **TRUE** — valid strict-UTF-8 JSON; `protocol == "cogame.battlecode.v1"` matching the
manifest's protocol document and the bc23 manifest variant; `.result.reason == "complete"`; both
champion seats made real, non-scripted, distinct decisions with **0 fallbacks out of 2 decisions**;
the episode played three full 2000-round games on three real bc23 maps and produced a decided
2–1 result.

### FINDING A (non-blocking for check 4, but the coordinator should see it) — champions keep wrapping the sheet in an envelope, so one champion per round plays the default doctrine

It happened in **both** completed rounds, once to each champion:

| round | seat | `unknown_fields` | applied sheet |
|---|---|---|---|
| 1 | 0 `daveey` / duel | `["protocol","game_version","year","slot","doctrine","notes"]` (6) | **all twelve knobs = schema default** |
| 1 | 1 `daveey-1` / alchemist | `["notes"]` (1) | the model's own knobs |
| 2 | 0 `daveey` / duel | `["notes"]` (1) | the model's own knobs |
| 2 | 1 `daveey-1` / alchemist | `["protocol","game_version","year","slot","alias","doctrine","notes"]` (7) | **all twelve knobs = schema default** |

Round-1 evidence (`/tmp/ep_r1.replay`, from
`https://softmax-public.s3.amazonaws.com/replays/f62806cf-fd55-4d14-80aa-f0224238b5ed.replay`,
HTTP 200, 53548 bytes, strict-parse ok):

```
$ jq -r '.seats[0].sheet_submitted' /tmp/ep_r1.replay | head -c 200
{"protocol":"cogame.battlecode.v1","game_version":"GV09","year":"bc23","slot":0,"doctrine":{"opening":"launcher_rush","launcher_ratio":72,"well_priority":"mana","elixir_tech":"never","elixir_spend":"acceler…
$ jq -c '.seats[0].sheet' /tmp/ep_r1.replay
{"opening":"balanced","launcher_ratio":45,"well_priority":"balanced","elixir_tech":"mid","elixir_spend":"accelerating_anchors","anchor_round":400,"anchor_budget":35,"island_priority":"nearest","amplifier_use":"one","destabilizer_use":"defend","retreat_on_launcher_loss":"regroup","carrier_throw":25}
```

Two consequences worth a phase-30 look:

1. **Spectator-visible contradiction.** The endcard's doctrine card renders the *applied* sheet, so
   the round-2 screenshot says "Clan Basil **opens balanced**, 45 % of its builds are launchers …
   converts a well to elixir from round 500 … first anchor at round 400" while daveey-1 actually
   wrote `carrier_eco`, `42`, `elixir_tech: early`, `anchor_round: 280`, `anchor_budget: 55`,
   `island_priority: contested`. The picture is honest about what was *played*; it silently
   disagrees with what the cog *said*. (See check 8.)
2. **`defaults_applied` under-reports it.** `doctrine_received.defaults_applied` is `0` and
   `sheet_defaults_applied` is `[]` on the affected seat even though **all twelve** knobs fell to
   default, because the keys were absent rather than malformed. Nothing in the replay's summary
   fields, and nothing in the hosted log, says "this seat played the default sheet"; only comparing
   `sheet` against `sheet_submitted` reveals it.

Neither makes check 4 false under `prompts/60-verify.md` (0 fallbacks, non-scripted, non-trivial,
documented default-on-unknown-key behaviour) — but it means the league is currently deciding
roughly half its seats on the *default* doctrine rather than the cog's.

---

## 5. Hosted game log is clean

```
GET $BASE/episode-requests/ereq_66018a01-7a9a-4f54-bff7-92cc373662f7/artifacts/logs
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
    -H X-Use-Elevated-Privileges: true
```
```
HTTP 200 bytes=1754
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers; decoded per
repr with `ast.literal_eval` before grepping (29 decoded lines — `playbooks/observatory-api.md`
§10). **Full decoded body, verbatim:**

```
===== container: coworld-init-config =====

===== container: bedrock-sidecar =====
2026-09-08 17:16:29,065 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"66018a01-7a9a-4f54-bff7-92cc373662f7","job_request_id":"16e08a05-82d7-4447-ad97-ee53be22557f","role":"game","slot":"game","image_digest":"sha256:bf33710abb5000bd991c5274150ff85598543318861ffc43b58595a4cd9be343"}
[2026-09-08 17:16:29 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-08 17:16:29,309 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-08 17:16:37,243 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-08 17:16:44,723 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"

===== container: game =====
battlecode config: year=bc23 pool=mixed seed=1002640040 games=3 maxRounds=2000 num_agents=2 matchBudget=340s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 0 connected
battlecode: seat 1 connected
battlecode: seat 0 registered kind=llm label=duel
battlecode: seat 1 registered kind=llm label=alchemist
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=3 scores=[234.33333333333334, 464.6666666666667] sim=21.459s wall=43.857s

===== container: worker =====

```

```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs_r2.txt || echo CLEAN
CLEAN
```

Status: **TRUE** — zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens`, `rejected`. Both doctrine calls returned `HTTP/1.1 200 OK`; **no**
Bedrock-capacity exception is being claimed. Round 1's log was fetched the same way
(`ereq_a2aa2be9-…`, HTTP 200, 1723 bytes) and was also `CLEAN`, with the same two
`HTTP/1.1 200 OK` doctrine calls and `settled: complete`.

*Observation, not a failure (identical to the bc25 sibling's note):* the line
`battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token` is the
seat-token guard doing its job on a stray connect — the real seat 0 connects on the next line and
registers `kind=llm label=duel`. It contains none of the four forbidden strings and did not affect
the episode. Note also that the log records the doctrine phase only as `battlecode: doctrine`; it
does **not** report that one seat's sheet fell to defaults (FINDING A).

---

## 6. The public page uses the static replay path

**Deviation recorded (briefed by the coordinator, and confirmed here):** this coworld's name is
`battlecode`, not the run slug, and the run's league is the **bc23** league, reached at the
short-name route `https://softmax.com/battlecode/bc23`. `https://softmax.com/battlecode` opens the
coworld's *default* league (bc26), which is not this run's, so the check was run against the bc23
page.

**Source (a) — raw-HTML grep, per the prompt's first command. Attempted first; found nothing
(the page is client-rendered).**

```
$ curl -sS "https://softmax.com/battlecode/bc23" -o bc23page.html -w 'HTTP %{http_code} bytes=%{size_download}\n'
HTTP 200 bytes=953049
$ grep -o '<iframe[^>]*src="[^"]*"' bc23page.html
(no output — NO IFRAME IN RAW HTML)
```
fetched 2026-09-08T17:22:06Z. Per `prompts/60-verify.md` check 6 and
`playbooks/observatory-api.md` §Featured match, an empty grep here is *unknown*, not a false
negative.

**Source (b) — the coworld detail API. Fetched; `featured_match` is `null`, the documented
platform-wide behaviour, so it is not the evidence either.**

```
$ curl -sS "$BASE/coworlds?limit=200" -H Authorization… -H User-Agent… \
  | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="battlecode")|{id,name,canonical,version,replay_viewer,featured_match}'
{"id":"cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7","name":"battlecode","canonical":true,"version":"0.6.0","replay_viewer":null,"featured_match":null}
{"id":"cow_e58e703d-3d34-4d27-b8eb-4464a6209170","name":"battlecode","canonical":false,"version":"0.5.0","replay_viewer":null,"featured_match":null}
{"id":"cow_455dff0d-7f57-4b21-a28d-6603d9c458d0","name":"battlecode","canonical":false,"version":"0.3.0","replay_viewer":null,"featured_match":null}
{"id":"cow_d9fc2f21-c095-4131-bd86-d35848e046f8","name":"battlecode","canonical":false,"version":"0.2.0","replay_viewer":null,"featured_match":null}
{"id":"cow_cfddca58-fa27-4dfd-bab8-38619b06fee7","name":"battlecode","canonical":false,"version":"0.1.6","replay_viewer":null,"featured_match":null}
{"id":"cow_6f3468fa-5cf5-4c4b-95cf-1d87dc41bfa2","name":"battlecode","canonical":false,"version":"0.1.5","replay_viewer":null,"featured_match":null}
```

This is also a fresh confirmation that **this run's `cow_93baa4e4-…` v0.6.0 is the canonical
battlecode coworld** (`canonical: true`; every earlier version is `false`).

**Source (c) — the page's own SSR payload, `state.playlist[0]`. THIS IS THE SOURCE USED for the
featured match** (`playbooks/observatory-api.md` §Featured match). Unescaped and pasted from the
17:22:06Z fetch:

```json
"leagueId":"league_e3244a55-f8b9-486b-9412-51dc1f56c978",
"playlist":[{"episodeId":"dee0f7eb-ff12-4fbe-865e-ab8529f393a2",
 "coworldId":"cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7",
 "coworldName":"battlecode","coworldVersion":"0.6.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/16e08a05-82d7-4447-ad97-ee53be22557f.replay",
 "finishedAt":"2026-09-08T17:17:42.549170Z","roundNumber":2,"episodeNumber":1,
 "code":"battlecode.r2.e1",
 "matchup":{"divisionId":"div_dc5f977f-2f98-4796-8cdd-87ecf673704f","divisionName":"Competition",
   "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
     "score":1030.5304984710244,"rounds_played":2,"episode_wins":2,"win_rate":1,
     "policy_label":"battlecode-bc23-alchemist:v1"},
   "second":{"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "score":969.4695015289755,"rounds_played":2,"episode_wins":0,"win_rate":0,
     "policy_label":"battlecode-bc23-duel:v1"}},
 "seats":2,"roster":["daveey-1","daveey"],
 "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_66018a01-7a9a-4f54-bff7-92cc373662f7",
 "outcome":"first"}]
```

```
$ grep -o 'softmax-public.s3.amazonaws.com/replays/[a-f0-9-]*\.replay' bc23page.html | sort -u
softmax-public.s3.amazonaws.com/replays/16e08a05-82d7-4447-ad97-ee53be22557f.replay
```

The bc23 page's SSR `leagueId` is **this run's league**, the coworld is **this run's v0.6.0
`cow_93baa4e4-…`**, and the only replay the page references is **this run's round-2 replay** —
the same `replay_url` check 3 read off `ereq_66018a01-…`, and the `inspectUrl` names that same
episode request. So a featured match is present and belongs to the bc23 league.

**Source (d) — the iframe `src` itself, from the call the page's JS makes.**

```
POST $BASE/coworlds/replays/session
  -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
  -H content-type: application/json
  -d '{"coworld_id":"cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/16e08a05-82d7-4447-ad97-ee53be22557f.replay"}'
```
fetched 2026-09-08T17:22:2xZ:

```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7/sha256%3Aa4ae44ab88615b434ccef7b6d6edc82bb8cdc6aec397d9f3efcaa89c70ef133e/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F16e08a05-82d7-4447-ad97-ee53be22557f.replay","ready":true}
```
```
HTTP 200
```

Status: **TRUE** — sources used: **(c)** the bc23 page's SSR `state.playlist[0]` for the featured
match, and **(d)** `POST /coworlds/replays/session` for the iframe `src`. (a) found no iframe
because the page is client-rendered; (b) is `null` platform-wide. The `src` is

```
…/v2/coworlds/replays/static/cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7/sha256%3Aa4ae44ab88615b434ccef7b6d6edc82bb8cdc6aec397d9f3efcaa89c70ef133e/index.html?v=2#replay=<s3 url>
```

— the **static** route, with `ready: true`. The `<sha>` is the coworld's manifest hash, and it is
byte-for-byte `STATE.coworld.manifest_sha`
(`sha256:a4ae44ab88615b434ccef7b6d6edc82bb8cdc6aec397d9f3efcaa89c70ef133e`, URL-encoded). It is
**not** a `/client/replay` pod URL. The replay is delivered as the URL-encoded **fragment**
`#replay=` rather than `?replay=` — the documented post-2026-08-28 form of the same static route
(`playbooks/observatory-api.md` §Featured match) — and it is exactly what check 8 below loaded and
rendered.

---

## 7. Certification declared the static replay bundle

Source read: **the committed `runs/2026-09-08-battlecode-2023/release-result.json`** — the copy
phase 40 downloaded from release run `34252334397` (`Metta-AI/cogame-battlecode`) and committed
in `4c0140b battlecode-2023: phase 40 release 0.6.0 certified canonical (run 34252334397)`. It was
already present in the working tree, so **no** `gh run download` re-fetch was needed, and `/tmp`
was not consulted.

```
$ jq -r '.certify.replay_liveness' runs/2026-09-08-battlecode-2023/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)

$ jq -r '.certify | keys' runs/2026-09-08-battlecode-2023/release-result.json
[
  "ok",
  "output_tail",
  "replay_liveness"
]

$ jq -r 'keys' runs/2026-09-08-battlecode-2023/release-result.json
[
  "canonical",
  "certify",
  "cow_id",
  "errors",
  "hosted_certification",
  "hosted_smoke",
  "manifest_sha",
  "ok",
  "policies",
  "secret_put",
  "step_failed",
  "version"
]

$ git log --oneline -1 -- runs/2026-09-08-battlecode-2023/release-result.json
4c0140b battlecode-2023: phase 40 release 0.6.0 certified canonical (run 34252334397)
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`
verbatim.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

**(a) Dispatch.** `viewer-check.yml` in `Metta-AI/coworld-builder` was dispatched **this run**
against the exact iframe `src` from check 6, with the bc23 timings the design pins
(`design.md` §"Playback pacing — check 8 must be dispatched with `settle=20000 soak=15`",
lines 1533–1542; `timeout=120` to match `ci.yml`'s bc23 `wasm-viewer` job):

```
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
    -f url='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7/sha256%3Aa4ae44ab88615b434ccef7b6d6edc82bb8cdc6aec397d9f3efcaa89c70ef133e/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F16e08a05-82d7-4447-ad97-ee53be22557f.replay' \
    -f timeout=120 -f settle=20000 -f soak=15
DISPATCHED  2026-09-08T17:22:37Z
```

The new run was found by sorting on `createdAt`, not by taking "the latest" blind:

```
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|"\(.databaseId)\t\(.createdAt)\t\(.status)"'
34256712314	2026-09-08T17:22:37Z	in_progress
34191692693	2026-09-08T05:43:04Z	completed
34190741103	2026-09-08T05:28:17Z	completed
```

`34256712314` is the run whose `createdAt` equals the dispatch instant (the two older runs are the
bc25 sibling's, 12 hours earlier).

```
$ gh run watch 34256712314 -R Metta-AI/coworld-builder --exit-status   # exit=0
$ gh run view 34256712314 -R Metta-AI/coworld-builder --json status,conclusion
{"conclusion":"success","status":"completed"}
$ gh run download 34256712314 -R Metta-AI/coworld-builder -n viewer-check \
    -D runs/2026-09-08-battlecode-2023/viewer-check
```

Committed at `runs/2026-09-08-battlecode-2023/viewer-check/` — `viewer-smoke.json` (1871 B),
`viewer-smoke.png` (548824 B), `smoke-stdout.txt` (663 B), `smoke-stderr.txt` (0 B, empty).

**(b) The readouts.**

`jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-check/viewer-smoke.json` — verbatim:

```json
{"loaded":true,"ms":1368,"clock":"3:55 GAME 1 OF 3 — SCATTER doctrines","scorebug":"CLAN ASH daveey 47 3:55 GAME 1 OF 3 — SCATTER doctrines CLAN BASIL daveey-1 52","feed_lines":6}
```

`jq -c '.signals' viewer-check/viewer-smoke.json`:

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```

`jq -r '.failure // "no failure"'` → `no failure`.  `console_tail` → `["[bridge] ready"]`.
`status` → `"OPEN"`.  `loading_text` → `null`.  `smoke-stderr.txt` is empty; `soak.page_errors`
is `[]`.  `canvas_text` → `{"total":0,"outside":0,"ellipsized":0,"never_inside":0,…}` (this shell
draws no text *into* the canvas — all chrome text is DOM, as on the bc25 sibling).

**The three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)\t\(.settle_ms)"'`):**

| scrub | clock readout | settle |
|---|---|---|
| 0 % | `3:55 GAME 1 OF 3 — SCATTER doctrines` | — |
| 50 % | `2:04 GAME 2 OF 3 — HIDEANDSEEK doctrines` | 10038 ms |
| 100 % | `FINAL MATCH OVER doctrines` | 9038 ms |

Three readouts, **all three different**, and they name the maps the replay JSON says were played
(`Scatter`, `HideAndSeek`, then the end of game 3 `Rainbow`) in the right order. The settle
latencies (10.0 s and 9.0 s) confirm the design's reason for pinning `settle=20000`: this sim
re-simulates from the last keyframe on every seek, and a 700 ms settle would have expired first.

Unattended playback also advanced on its own (15-second soak, from `viewer-smoke.json.soak` and
`smoke-stdout.txt`):

```json
{"seconds":15,"moved":true,
 "before":{"clock":"4:10 GAME 1 OF 3 — SCATTER doctrines","tick":"round 2 / 2000"},
 "middle":{"clock":"3:57 GAME 1 OF 3 — SCATTER doctrines","tick":"round 318 / 2000"},
 "after":{"clock":"3:55 GAME 1 OF 3 — SCATTER doctrines","tick":"round 366 / 2000"},
 "status":"OPEN","page_errors":[]}
```
```
soak: 15s of playback kept advancing ("round 2 / 2000" -> "round 318 / 2000" -> "round 366 / 2000")
scrub readouts: 0%="3:55 GAME 1 OF 3 — SCATTER doctrines"  50%="2:04 GAME 2 OF 3 — HIDEANDSEEK doctrines"  100%="FINAL MATCH OVER doctrines"
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
```

**Item 8 gate: `loaded: true` ✓ (via `data-replay-loaded="true"` *and* the `coworld-replay`
bridge's `ready`), and the three clock readouts differ ✓. Status: TRUE.**

**(c) The replay JSON the viewer was asked to draw** — ordered excerpts from `/tmp/ep.replay`
(check 4's bytes; `game` is 0-indexed, `round` is the in-game round), so the picture and the record
can be reconciled.

Early:

```
$ jq -r '.events[]|[(.game//"-"),(.round//"-"),.kind,(.alias//"-"),((.detail//.island//"")|tostring)]|@tsv' /tmp/ep.replay | head -22
-	-	episode_start	-	
-	-	doctrine_requested	-	
-	-	doctrine_requested	-	
-	-	doctrine_received	-	
-	-	doctrine_received	-	
0	0	game_start	-	
0	1	first_action	Clan Basil	
0	1	first_action	Clan Ash	
0	349	duel	-	
0	400	anchor_built	Clan Basil	
0	400	anchor_built	Clan Basil	
0	405	anchor_built	Clan Basil	
0	410	island_captured	Clan Basil	3
0	428	anchor_built	Clan Basil	
0	449	duel	-	
0	522	island_captured	Clan Basil	6
0	522	conquest_progress	Clan Basil	
0	525	anchor_built	Clan Basil	
0	538	island_captured	Clan Basil	2
0	546	anchor_built	Clan Basil	
0	593	island_captured	Clan Basil	8
0	593	conquest_progress	Clan Basil	
```

Middle (game 2 = `HideAndSeek`, the one Clan Ash won):

```
1	1115	duel	-	
1	1116	duel	-	
1	1120	anchor_built	Clan Ash	
1	1124	island_captured	Clan Ash	3
1	1147	island_captured	Clan Ash	9
1	1179	anchor_built	Clan Ash	
1	1187	island_captured	Clan Ash	14
1	1187	conquest_progress	Clan Ash	
1	1194	duel	-	
1	1240	duel	-	
1	1332	duel	-	
1	1406	island_captured	Clan Ash	16
1	1461	anchor_built	Clan Ash	
1	1481	island_captured	Clan Ash	15
```

Late (game 3 = `Rainbow`):

```
2	1603	anchor_built	Clan Basil	
2	1614	island_captured	Clan Basil	6
2	1640	duel	-	
2	1683	duel	-	
2	1694	anchor_built	Clan Basil	
2	1711	island_captured	Clan Basil	2
2	1722	anchor_built	Clan Basil	
2	1744	island_captured	Clan Basil	10
2	1744	conquest_progress	Clan Basil	
2	1784	anchor_built	Clan Basil	
2	1812	island_captured	Clan Basil	4
2	1841	anchor_built	Clan Basil	
2	1867	island_captured	Clan Basil	15
2	1903	anchor_built	Clan Basil	
2	1926	island_captured	Clan Basil	8
2	1953	anchor_built	Clan Basil	
2	1984	island_captured	Clan Basil	13
2	2000	game_end	-	
-	-	episode_end	-	complete
```

```
$ jq -c '[.events[]|select(.kind=="island_captured")][0], [.events[]|select(.kind=="game_end")][0]' /tmp/ep.replay
{"kind":"island_captured","game":0,"round":410,"alias":"Clan Basil","island":3,"held_now":1,"anchor":"standard","tiles":5,"to_win":6}
{"kind":"game_end","game":0,"round":2000,"winner_alias":"Clan Basil","winner_slot":1,"end_reason":"more_sky_islands","points":[25,74]}

$ jq -c '.result|{reason,names,scores,wins,points}' /tmp/ep.replay
{"reason":"complete","names":["daveey","daveey-1"],"scores":[234.33333333333334,464.6666666666667],"wins":[1,2],"points":[[25,74,4],[74,25,95]]}
```

### Spectator judgment

**It is legible, and it shows this game.** The screenshot
(`runs/2026-09-08-battlecode-2023/viewer-check/viewer-smoke.png`, 1280×800, taken at the 100 %
scrub position, so it is the end-of-match state) is a full broadcast frame — not a blank canvas
and not a loading shell:

- **Top strip / scorebug.** `CLAN ASH` on the left with its team colour swatch, `FINAL / MATCH
  OVER` in the centre, and the two clan/player/points pairs `daveey 4` and `daveey-1 95` — which
  are exactly the replay's game-3 `points` (`result.points[0][2] = 4`, `result.points[1][2] = 95`).
  Behind the endcard the live scorebug band is still there, reading `ASH 0 · /15 to win · … ·
  neutral of 20`. A spectator can read who won and by how much at a glance.
- **The board.** The bc23 map is drawn behind the endcard scrim: carrier, launcher (triangle),
  amplifier and cloud glyphs are scattered across a dark-olive grid with two headquarters
  structures visible. It is dimmed (correctly, so the endcard reads), and it is populated — not an
  empty arena. Nothing is drawn *into* the canvas as text (`canvas_text.total: 0`).
- **The endcard.** `CLAN BASIL — DAVEEY-1`, `THE ROUND LIMIT RAN OUT AND THE POINTS DECIDED IT`
  (correct — all three games ended `more_sky_islands` at round 2000, i.e. the tiebreak ladder, not
  a 75 % conquest), and `score 234.33333333333334 — 464.6666666666667` matching `result.scores`.
- **The doctrine cards** render each seat's *applied* sheet back as English prose. Clan Ash:
  "rushes launchers, 72 % of its builds are launchers, mines mana first, no elixir programme, so
  its sink never opens, first anchor at round 1100 with 15 % of income reserved, goes for the
  nearest islands, an amplifier escorting every launcher group, its strike group sieges…" — every
  number is seat 0's sheet from check 4, and the "no elixir programme, so its sink never opens"
  sentence is the exact copy `design.md` line 697 promises for `elixir_tech: never`. Clan Basil:
  "opens balanced, 45 % of its builds are launchers, mines whichever it is short of, converts a
  well to elixir from round 500, spends elixir on accelerating anchors, first anchor at round 400
  with 35 % of income reserved, goes for the nearest islands, one amplifier per headquarters…" —
  the **default** sheet, which is what was played, and which contradicts what daveey-1 actually
  wrote (FINDING A).
- **The stat block** under the cards: `Clan Ash — islands 0 captured / 0 lost / 0 held at the end,
  0 rounds holding one · anchors 3 built / 0 placed / 0 lost (0 accelerating) · mined ◆0 ◇2993 ✦0 ·
  banked 2720 · thrown away 80 · wells 0 transformed / 0 upgraded · built 39 carriers, 160
  launchers, 16 amplifiers, 0, 0, 133 lost · damage launcher 21383 / throw 100 / destabiliser 0 /
  headquarters 0 · anchor healing 0 · array writes 39454 · current rides 2990`, and
  `Clan Basil — islands 9 captured / 0 lost / 9 held at the end, 1064 rounds holding one · anchors
  12 built / 9 placed / 0 lost (7 accelerating) · mined ◆10697 ◇2053 ✦3229 · banked 15010 · thrown
  away 100`. Those match the replay's game-3 row (`islands_held_end: [0,9]`,
  `anchors_placed: [0,9]`) and they *explain* the loss: Ash spent everything on launchers
  (160 built, 21383 launcher damage) and planted no anchors; Basil mined 3229 elixir, planted 9
  anchors of which 7 were accelerating, and took the islands.
- **The feed** (right column, 6 lines, dimmed behind the endcard): `Game 3 — Clan Basil wins (more
  sky islands)`, `Clan Basil anchors island 13 (9 of the 15 it needs) — game 3, round 1984`,
  `Clan Basil builds a accelerating anchor — game 3, round 1953`, `Clan Basil anchors island 8
  (8 of the 15 it needs) — game 3, round 1926`, `…anchor — game 3, round 1903`, `Clan Basil anchors
  island 15 (7 of the 15 it needs) — game 3, round 1867`, `…round 1841`, `Clan Basil anchors island
  4 (6 of the 15 it needs) — game 3, round 1812`. Those are, line for line and round number for
  round number, the **late excerpt of the replay JSON above** (island 13 @ 1984, anchor @ 1953,
  island 8 @ 1926, anchor @ 1903, island 15 @ 1867, anchor @ 1841, island 4 @ 1812). The picture
  and the record agree exactly.
- **The transport strip** across the bottom: restart / step-back / play / `+25` / step / loop /
  fast-forward buttons, a `spoilers` toggle, `round 2000 / 2000`, speed buttons
  `1× 2× 3× 4× 8× 16×`, and a full-width scrubber whose tick marks are the event momentum graph,
  with the playhead at the far right. A `doctrines` toggle sits under the clock (the dismissible
  `#bc23-doctrines` overlay control the design's D3 requires).

**Does it look like the starter's chrome?** Yes — this is the same broadcast shell as
paintbot/raid/hive and as the bc25 sibling verified 12 hours earlier: same transport strip, same
scrubber-with-momentum-graph, same scorebug band, same two-column doctrine endcard, same feed
column. It is **not** a rewrite that merely shares ids (the cogame-gridlock failure). The bc23
year block adds year-specific vocabulary throughout — islands anchored, accelerating anchors,
elixir wells, launcher duels, current rides, array writes.

**Legibility findings for the coordinator (none of them makes item 8 false — the viewer loads,
advances, seeks, and reads correctly):**

1. **Wrong-year captions on the endcard — the bc25 finding, still unfixed.** Between the verdict
   line and the doctrine cards the endcard reads `the alliance held / score 234.33333333333334 —
   464.6666666666667 · kings built 0/0 · cheese delivered 0/0 · cats damaged 0/0`. bc23 has no rat
   kings, no cheese, no cats and no alliance — those are **bc26** ("Uneasy Alliances") nouns, and
   `client/replay_broadcast.html` emits them unconditionally for every year. The bc25 VERIFY
   (`runs/2026-09-07-battlecode-2025/VERIFY.md`, check 8 finding 1) raised exactly this against
   `replay_broadcast.html:4983,4994-4996`; it reproduces verbatim on bc23. Phase-30 item-14.
2. **The score is printed as a raw float.** `score 234.33333333333334 — 464.6666666666667`. bc25
   showed `465.5 — 33.5` and looked fine because its scores were halves; a best-of-three where a
   side takes 2 of 3 produces thirds, and the endcard prints all seventeen digits. Should be
   rounded (e.g. `234.3 — 464.7`).
3. **Doctrine cards still clip their last line — also the bc25 finding, still unfixed.** Both cards
   end mid-sentence at the card's bottom edge ("group, its strike group sieges" / "amplifier per
   headquarters") with no ellipsis and no scroll affordance. `canvas_text.ellipsized` is 0 because
   this is DOM text in the endcard, not canvas text, so the smoke test's clipping detector cannot
   see it.
4. **The endcard overflows the 1280×800 viewport.** Clan Ash's stat block renders all seven lines;
   Clan Basil's is cut after its third line (`mined … banked 15010 · thrown away 100`) — its
   `wells`, `built`, `damage`, `anchor healing` lines are below the fold, above the transport strip.
   The losing side gets a full report and the *winning* side gets a truncated one.
5. **The dimmed live HUD bleeds through the endcard text.** On the right of the stat block the
   underlying side panel (`Clan Ash ◆2530 ◇433 ✦0 ↑2720 banked · 3083 in flight 0→Ex · 0×3 …`)
   overlaps the centred endcard lines, so two different numbers sit on top of each other. A solid
   scrim behind the endcard body would fix it.
6. **Grammar: "builds a accelerating anchor"** in the feed (should be "an"). Cosmetic.
7. **No motto on the scorebug.** `jq -r '.seats[]|[.slot,.alias,(.motto//"(none)")]|@tsv'` shows
   both seats' `motto` is the empty string, so the clan blocks are name + points only and spread
   across the full width with a large gap. bc25 rendered a motto there and read better. Not a
   defect in the shell — the bc23 doctrine reply apparently does not solicit a motto.
