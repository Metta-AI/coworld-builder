# Phase 70 — Announce

Purpose: post the coworld to Discord `#coworlds` and record the message id.
Owner: coordinator. Discord, **not** Slack.

## Inputs

- `STATE.slug`, `STATE.repo`, `STATE.league.id`, `runs/<run>/VERIFY.md` (for the one-line hook and
  the replay link), `runs/<run>/design.md` (for the game summary).
- `templates/announce.md`.
- Guild `1309708848730345493`, channel `#coworlds` `1440464430646427718`.

## Procedure

1. Compose from `templates/announce.md`: name, one sentence on what the game is, one sentence on
   what makes it watchable, the two champions and their current ranks, the play link
   `https://softmax.com/<slug>`, and the repo link. Keep it under ~1000 characters.
2. Post:
   ```bash
   /usr/bin/curl -sS -X POST \
     "https://discord.com/api/v10/channels/1440464430646427718/messages" \
     -H "authorization: Bot $DISCORD_BOT_TOKEN" \
     -H 'content-type: application/json' \
     -d @/tmp/announce.json          # {"content":"…"}
   ```
   Build `/tmp/announce.json` with `jq -n --arg c "$BODY" '{content:$c}'` so quoting cannot corrupt
   the message.
3. Read `.id` from the 200 response — that is the message id.
4. Do **not** announce before phase 60 has passed. A dead-looking league announced is worse than a
   late announcement.

## Exit criterion

HTTP 200 from the POST and a non-empty `.id`, recorded in STATE.

## Writes

- STATE: `announce.discord_message_id`, `phase: "80"`, `heartbeat_at`.
- `log.md`: `<UTC> 70 announce msg=<id>`.
- Asana: complete the phase-70 subtask; comment with the message id and the posted text.

## Retry budget

3 attempts (re-encode the body, shorten it, re-read the token from the vault env). On exhaustion →
`prompts/90-blocked.md` with the exact Discord error JSON. A 401/403 is a credential block, not a
formatting problem — go to 90 immediately rather than retrying.
