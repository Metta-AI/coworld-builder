#!/usr/bin/env bash
# phase-60 round poller: appends a heartbeat line per poll, stops when >=2 rounds completed
BASE=https://softmax.com/api/observatory/v2
L=league_31edf62a-9174-4975-b39b-cd1555853bff
RUNDIR=/workspace/coworld-builder/runs/2026-08-23-firm
END=$(( $(date -u +%s) + 75*60 ))
while :; do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  BODY=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" \
    -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
  N=$(printf '%s' "$BODY" | jq -r '[.entries[]|select(.status=="completed")]|length')
  printf '%s heartbeat phase=60\n' "$TS" >> "$RUNDIR/log.md"
  printf '%s completed=%s %s\n' "$TS" "$N" \
    "$(printf '%s' "$BODY" | jq -c '[.entries[]|{n:.round_number,s:.status}]')" >> "$RUNDIR/poll.log"
  if [ "$N" -ge 2 ]; then echo "DONE $TS n=$N" >> "$RUNDIR/poll.log"; break; fi
  if [ "$(date -u +%s)" -ge "$END" ]; then echo "TIMEOUT $TS n=$N" >> "$RUNDIR/poll.log"; break; fi
  sleep 300
done
