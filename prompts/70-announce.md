# Phase 70 — Announce

Purpose: post the coworld to Discord `#coworlds` and record the message id.
Owner: coordinator. Discord, **not** Slack.

## Inputs

- `STATE.slug`, `STATE.repo`, `STATE.league.id`, `runs/<run>/VERIFY.md` (for the one-line hook and
  the replay link), `runs/<run>/design.md` (for the game summary).
- `templates/announce.md`.
- Guild `1309708848730345493`, channel `#coworlds` `1440464430646427718`.

## Procedure

0. **Resume guard — run this before composing anything.** If `STATE.announce.discord_message_id`
   is set, the run has already announced: do nothing, go to phase 75. If
   `STATE.announce.attempted_at` is set but the id is **not**, a previous session died between the
   POST and the STATE write. **Never post blind in that case** — search the channel first and
   adopt the id if the message is already there:
   ```bash
   curl -sS "https://discord.com/api/v10/channels/1440464430646427718/messages?limit=20" \
     -H "authorization: Bot $DISCORD_BOT_TOKEN" \
    | jq -r --arg u "https://softmax.com/<slug>" \
        '.[]|select(.content|contains($u))|[.id,.timestamp,.author.username]|@tsv'
   ```
   A row whose `content` contains this run's play link `https://softmax.com/<slug>` **is** our
   message: record its `.id` in STATE, log `<UTC> 70 announce adopted existing msg=<id>`, run
   step 4b on it (older posts may still carry embeds), and go to phase 75. Only if the search comes back empty (widen to `limit=100` once) may you post.
1. Compose from `templates/announce.md`: name, one sentence on what the game is, one sentence on
   what makes it watchable, the two champions and their current ranks, the play link
   `https://softmax.com/<slug>`, and the repo link. Keep it ≤ 1800 characters (the hard limit in `templates/announce.md`).
2. **Write the attempt marker BEFORE the POST**: set `STATE.announce.attempted_at` = now (UTC
   ISO-8601), commit, **push**. An unpushed marker cannot protect the next heartbeat; that is the
   whole point of writing it first.
3. Post:
   ```bash
   curl -sS -X POST \
     "https://discord.com/api/v10/channels/1440464430646427718/messages" \
     -H "authorization: Bot $DISCORD_BOT_TOKEN" \
     -H 'content-type: application/json' \
     -d @/tmp/announce.json          # {"content":"…","flags":4}
   ```
   Build `/tmp/announce.json` with `jq -n --arg c "$BODY" '{content:$c, flags:4}'` so quoting
   cannot corrupt the message. **`flags: 4` is `SUPPRESS_EMBEDS` and is mandatory** — the
   announcement is plain text; Discord must not unfurl the softmax.com or GitHub links into
   embed cards under it.
4. Read `.id` from the 200 response — that is the message id. Write it to STATE and push
   immediately, before any other work.
4b. **Confirm no embeds.** The 200 body must have `.flags == 4` and `.embeds == []`. If it
   does not (or if an adopted message from step 0 shows embeds), strip them in place — this is
   an edit, not a new post, so it does not violate the post-once rule:
   ```bash
   curl -sS -X PATCH \
     "https://discord.com/api/v10/channels/1440464430646427718/messages/<id>" \
     -H "authorization: Bot $DISCORD_BOT_TOKEN" \
     -H 'content-type: application/json' \
     -d '{"flags":4}'
   ```
   Log `<UTC> 70 announce embeds-suppressed msg=<id>`.
5. Do **not** announce before phase 60 has passed. A dead-looking league announced is worse than a
   late announcement.

## Exit criterion

HTTP 200 from the POST and a non-empty `.id`, recorded in STATE, and the message carries
`flags: 4` (no embeds).

## Writes

- STATE: `announce.attempted_at` (pushed **before** the POST), `announce.discord_message_id`
  (pushed immediately after the 200), `phase: "75"`, `heartbeat_at`.
- `log.md`: `<UTC> 70 announce msg=<id>` (plus `embeds-suppressed` if step 4b had to PATCH).
- Asana: complete the phase-70 subtask; comment with the message id and the posted text.

## Retry budget

3 attempts (re-encode the body, shorten it, re-read the token from the vault env). On exhaustion →
`prompts/90-blocked.md` with the exact Discord error JSON. A 401/403 is a credential block, not a
formatting problem — go to 90 immediately rather than retrying.
