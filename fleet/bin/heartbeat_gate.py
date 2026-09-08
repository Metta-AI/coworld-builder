#!/usr/bin/env python3
"""heartbeat_gate.py — decide, without an LLM, whether a coworld-builder heartbeat has a unit of
work, and fire a heartbeat deployment only when it does.

Why this exists (2026-09-07 spend review): the coordinator is a Fable session that costs
$1.14–1.46 every time it wakes up, and 58 of 66 sessions in one day woke up, read the boards, and
found nothing to do — ≈ $90/day of heartbeats that shipped nothing. The question they answered
("is there a unit of work?") is deterministic: Asana board state, `runs/*/STATE.json`, and a probe
exit code. This script answers it for ~$0 and fires the coordinator only on "yes". The
coordinator still runs `prompts/00-claim.md` in full when fired — every race guard is unchanged.

Modes (python3 stdlib only):

  decide            (default) print the decision as JSON. Exit 0 always once a decision is made;
                    non-zero only on an unexpected error.
  --fire            after deciding, POST /deployments/{id}/run on the least-recently-run heartbeat
                    deployment (fleet/cloud.md ids table) when there is work. Needs
                    ANTHROPIC_AUTH_TOKEN (a federated bearer token — what the workflow uses) or
                    ANTHROPIC_API_KEY (an org key; the workspace header comes from fleet/cloud.md).
  --alert           when the Builder board is unreachable, post ONE Discord message per UTC day to
                    `#coworlds` (needs DISCORD_BOT_TOKEN). Never fires the coordinator on a 403.
  --summary         sandbox mode, run by the coordinator as `prompts/00-claim.md` step 0: does the
                    gh/jq preflight, `git pull --rebase`, and prints the same decision JSON with the
                    details the claim needs (candidate idea text, stale runs, probe results) so the
                    coordinator does not spend six tool calls and 50 KB of context re-deriving it.

Decision rules mirror `prompts/00-claim.md` steps 1–4.2, in the same order:

  1. Builder board unreachable (403/5xx)                     -> board_error, no work, no fire
  2. Running task stale (heartbeat_at ≥ 180 min) or ended
     (STATE.session_ended_at ≥ heartbeat_at)                 -> work: resume (oldest first)
  3. Blocked task whose STATE.blocked.subtask is complete,
     or whose STATE.blocked.probe exits 0                    -> work: unblock
  3.5 ≥ 2 Blocked and no `QUEUE STALLED <today>` Fleet card  -> work: escalate
  4. live < max_parallel_runs and fresh-Blocked < 2 and a
     claimable idea exists (not in any STATE.idea_task, not
     in runs/SKIPPED.json, no claimed-by/skipped-by comment,
     not a mod of a repo a Running run is already editing)   -> work: claim
  else                                                       -> nothing to do

Confidentiality and startability of an idea stay with the coordinator (SPEC §Rails): a skipped
idea lands in runs/SKIPPED.json and is filtered out here forever after.

Credentials come from the environment only (ASANA_PAT, ANTHROPIC_AUTH_TOKEN or ANTHROPIC_API_KEY,
DISCORD_BOT_TOKEN, plus whatever a probe needs). Nothing is ever printed but their presence.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CLOUD_MD = os.path.join(ROOT, "fleet", "cloud.md")
SANDBOX_ROOT = "/workspace/coworld-builder"   # probes are written against this path
ASANA = "https://app.asana.com/api/1.0"
ANTHROPIC = "https://api.anthropic.com/v1"
DISCORD = "https://discord.com/api/v10"
STALE_MIN = 180
FRESH_BLOCK_H = 24
MAX_FRESH_BLOCKED = 2
ALERT_MARKER = "[gate-alert %s]"

# Defaults; fleet/cloud.md overrides every one of these.
IDS = {
    "ideas": "1217704774784096", "builder": "1217747772236871",
    "running": "1217747860567752", "blocked": "1217762552336061",
    "done": "1217748136343842", "fleet": "1217747860605582",
    "human": "1209016834701578", "heartbeat_field": "1217748424048134",
    "discord_channel": "1440464430646427718",
}


# --------------------------------------------------------------------------- helpers


def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(s):
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        t = dt.datetime.fromisoformat(s)
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
        return t.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def _request(url, headers, body=None, method=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                               headers=dict(headers, **({"content-type": "application/json"} if data else {})))
    with urllib.request.urlopen(r, timeout=timeout) as f:
        raw = f.read()
        return json.loads(raw) if raw else {}


class BoardError(Exception):
    pass


def asana(path, params=None, body=None, method=None):
    tok = os.environ.get("ASANA_PAT")
    if not tok:
        raise BoardError("ASANA_PAT is not set")
    url = ASANA + path + ("?" + urllib.parse.urlencode(params) if params else "")
    try:
        return _request(url, {"authorization": "Bearer " + tok}, body, method)
    except urllib.error.HTTPError as e:
        raise BoardError("HTTP %s %s %s" % (e.code, path.split("?")[0], e.read().decode("utf-8", "replace")[:200]))
    except (urllib.error.URLError, TimeoutError) as e:
        raise BoardError("%s %s" % (path, e))


def asana_all(path, params):
    """Follow Asana's offset pagination."""
    out, p = [], dict(params, limit=100)
    while True:
        d = asana(path, p)
        out += d.get("data") or []
        nxt = (d.get("next_page") or {}).get("offset")
        if not nxt:
            return out
        p["offset"] = nxt


def anthropic(path, body=None, method=None):
    h = {"anthropic-version": "2023-06-01", "anthropic-beta": "managed-agents-2026-04-01"}
    tok = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if tok:
        # A federated `sk-ant-oat01-` bearer token (the workflow mints one per run from GitHub's
        # OIDC token): already bound to the workspace, so no workspace header.
        h["authorization"] = "Bearer " + tok
    elif key:
        h["x-api-key"] = key
        ws = workspace_id()
        if ws:
            h["anthropic-workspace-id"] = ws
    else:
        raise SystemExit("neither ANTHROPIC_AUTH_TOKEN nor ANTHROPIC_API_KEY is set — cannot fire a deployment")
    return _request(ANTHROPIC + path, h, body, method, timeout=120)


def discord(path, body=None, params=None):
    tok = os.environ.get("DISCORD_BOT_TOKEN")
    if not tok:
        return None
    url = DISCORD + path + ("?" + urllib.parse.urlencode(params) if params else "")
    return _request(url, {"authorization": "Bot " + tok, "user-agent": "DiscordBot (heartbeat-gate, 1.0)"}, body)


# --------------------------------------------------------------------------- fleet/cloud.md


def read_cloud():
    body = open(CLOUD_MD, encoding="utf-8").read()
    ids = dict(IDS)
    rows = re.findall(r"^\|\s*(.+?)\s*\|\s*`(\d{6,})`\s*\|", body, re.M)
    for what, gid in rows:
        w = what.lower()
        if w.startswith("coworld ideas"):
            ids["ideas"] = gid
        elif w.startswith("coworld builder section running"):
            ids["running"] = gid
        elif w.startswith("coworld builder section blocked"):
            ids["blocked"] = gid
        elif w.startswith("coworld builder section done"):
            ids["done"] = gid
        elif w.startswith("coworld builder section fleet"):
            ids["fleet"] = gid
        elif w.startswith("coworld builder"):
            ids["builder"] = gid
        elif "heartbeat_at" in w:
            ids["heartbeat_field"] = gid
        elif "david bloomin" in w:
            ids["human"] = gid
        elif w.startswith("`#coworlds`"):
            ids["discord_channel"] = gid
    m = re.search(r"`max_parallel_runs:\s*(\d+)`", body)
    ids["max_parallel_runs"] = int(m.group(1)) if m else 3
    m = re.search(r"`workspace_id:\s*([A-Za-z0-9_\-]+)`", body)
    ids["workspace_id"] = m.group(1) if m else ""
    depls = {}
    sec = body.split("<!-- ids:start -->", 1)[1].split("<!-- ids:end -->", 1)[0] if "<!-- ids:start -->" in body else ""
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[0].startswith("coworld-builder-") and cells[1] == "deployment":
            ident = cells[3].strip("`")
            if ident and ident != "TBD" and not cells[0].endswith("-costbot"):
                depls[cells[0]] = ident
    ids["deployments"] = depls
    return ids


_WS = None


def workspace_id():
    global _WS
    if _WS is None:
        _WS = os.environ.get("ANTHROPIC_WORKSPACE_ID") or read_cloud()["workspace_id"]
    return _WS


# --------------------------------------------------------------------------- repo state


def load_states(root):
    """run dir -> STATE dict, for every runs/*/STATE.json."""
    out = {}
    runs = os.path.join(root, "runs")
    if not os.path.isdir(runs):
        return out
    for d in sorted(os.listdir(runs)):
        p = os.path.join(runs, d, "STATE.json")
        if os.path.isfile(p):
            try:
                out[d] = json.load(open(p, encoding="utf-8"))
            except ValueError:
                continue
    return out


def skipped_gids(root):
    p = os.path.join(root, "runs", "SKIPPED.json")
    try:
        return set(str(x) for x in json.load(open(p, encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def log_heartbeat(root, run):
    """Fallback for an empty custom field: the last `<UTC> heartbeat phase=<nn>` line of log.md."""
    p = os.path.join(root, "runs", run, "log.md")
    last = None
    try:
        for line in open(p, encoding="utf-8"):
            m = re.match(r"^(\S+) heartbeat phase=\d\d", line)
            if m:
                last = parse_ts(m.group(1)) or last
    except OSError:
        pass
    return last


# --------------------------------------------------------------------------- decision


def custom_field(task, gid):
    for f in task.get("custom_fields") or []:
        if f.get("gid") == gid:
            return f.get("text_value") or f.get("display_value")
    return None


def host_repo(text):
    m = re.search(r"mod of (?:the existing )?`?(?:Metta-AI/)?([A-Za-z0-9_.\-]+)`?", text or "", re.I)
    return m.group(1).rstrip(".,;:)") if m else None


def decide(root, ids, want_details=False, probe_root=None):
    t0 = now()
    d = {"at": iso(t0), "work": False, "kind": "none", "reason": "", "live": 0,
         "max_parallel_runs": ids["max_parallel_runs"], "fresh_blocked": 0, "blocked_total": 0,
         "board_error": None, "notes": []}
    states = load_states(root)
    by_task = {}
    for run, st in states.items():
        if st.get("run_task"):
            by_task[str(st["run_task"])] = (run, st)

    # 1. the Builder board
    try:
        tasks = asana_all("/tasks", {"project": ids["builder"],
                                     "opt_fields": "name,completed,memberships.section.gid,custom_fields,created_at"})
    except BoardError as e:
        d["board_error"] = str(e)
        d["reason"] = "Builder board unreachable — not firing"
        return d
    section = {}
    for t in tasks:
        for m in t.get("memberships") or []:
            sg = (m.get("section") or {}).get("gid")
            if sg:
                section.setdefault(t["gid"], sg)

    running = [t for t in tasks if section.get(t["gid"]) == ids["running"] and not t.get("completed")]
    blocked = [t for t in tasks if section.get(t["gid"]) == ids["blocked"] and not t.get("completed")]

    # 2. freshness of every Running task
    live, resumable, running_repos = 0, [], []
    for t in running:
        run, st = by_task.get(t["gid"], (None, None))
        hb = parse_ts(custom_field(t, ids["heartbeat_field"]))
        if hb is None and run:
            hb = log_heartbeat(root, run)
        if st and st.get("repo"):
            running_repos.append(str(st["repo"]).rstrip("/"))
        ended = parse_ts((st or {}).get("session_ended_at"))
        age_min = (t0 - hb).total_seconds() / 60 if hb else None
        fresh = hb is not None and age_min < STALE_MIN and (ended is None or ended < hb)
        row = {"task": t["gid"], "name": t.get("name"), "run": run, "phase": (st or {}).get("phase"),
               "heartbeat_at": iso(hb) if hb else None, "age_min": round(age_min) if age_min is not None else None,
               "session_ended_at": (st or {}).get("session_ended_at"), "fresh": fresh}
        if fresh:
            live += 1
        else:
            if run is None:
                d["notes"].append("Running task %s has no runs/*/STATE.json with run_task=%s" % (t["gid"], t["gid"]))
            resumable.append((hb or dt.datetime.min.replace(tzinfo=dt.timezone.utc), row))
    d["live"] = live
    if want_details:
        d["running"] = [r for _, r in resumable] + [{"task": t["gid"], "name": t.get("name"), "fresh": True}
                                                     for t in running if t["gid"] not in {r["task"] for _, r in resumable}]
    if resumable:
        resumable.sort(key=lambda x: x[0])
        row = resumable[0][1]
        d.update(work=True, kind="resume", reason="stale or cleanly-ended run: %s (phase %s)" % (row["run"] or row["task"], row["phase"]),
                 target=row)
        return d

    # 3. Blocked tasks: subtask complete or probe passing
    d["blocked_total"] = len(blocked)
    fresh_blocked, unblock, blocked_rows = 0, None, []
    for t in blocked:
        run, st = by_task.get(t["gid"], (None, None))
        b = (st or {}).get("blocked") or {}
        row = {"task": t["gid"], "name": t.get("name"), "run": run, "phase": (st or {}).get("phase"),
               "blocked_at": b.get("at"), "subtask": b.get("subtask"), "subtask_completed": None,
               "probe": b.get("probe"), "probe_rc": None}
        sub_gid = b.get("subtask")
        created = None
        if not sub_gid:
            try:
                subs = asana_all("/tasks/%s/subtasks" % t["gid"], {"opt_fields": "name,completed,assignee.gid,created_at"})
            except BoardError as e:
                d["notes"].append("subtasks of %s unreadable: %s" % (t["gid"], e))
                subs = []
            for s in subs:
                if str(s.get("name", "")).startswith("BLOCKED ") and (s.get("assignee") or {}).get("gid") == ids["human"]:
                    sub_gid, row["subtask"] = s["gid"], s["gid"]
                    row["subtask_completed"] = bool(s.get("completed"))
                    created = parse_ts(s.get("created_at"))
                    break
        if sub_gid and row["subtask_completed"] is None:
            try:
                s = asana("/tasks/%s" % sub_gid, {"opt_fields": "completed,created_at"}).get("data") or {}
                row["subtask_completed"] = bool(s.get("completed"))
                created = parse_ts(s.get("created_at"))
            except BoardError as e:
                d["notes"].append("subtask %s unreadable: %s" % (sub_gid, e))
        blocked_at = parse_ts(b.get("at")) or created
        if blocked_at and (t0 - blocked_at).total_seconds() < FRESH_BLOCK_H * 3600:
            fresh_blocked += 1
        probe = b.get("probe")
        if probe and isinstance(probe, str) and probe.strip() and not row["subtask_completed"]:
            cmd = probe.replace(SANDBOX_ROOT, probe_root or root)
            try:
                rc = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=60).returncode
            except (subprocess.TimeoutExpired, OSError):
                rc = 124
            row["probe_rc"] = rc
        blocked_rows.append(row)
        if unblock is None and (row["subtask_completed"] or row["probe_rc"] == 0):
            unblock = row
    d["fresh_blocked"] = fresh_blocked
    if want_details:
        d["blocked"] = blocked_rows
    if unblock:
        d.update(work=True, kind="unblock", target=unblock,
                 reason="blocked run ready to resume: %s (%s)" % (
                     unblock["run"] or unblock["task"], "subtask completed" if unblock["subtask_completed"] else "probe passed"))
        return d

    # 3.5 escalate stalled blocks once per UTC day
    if len(blocked) >= 2:
        title = "QUEUE STALLED %s" % t0.strftime("%Y-%m-%d")
        try:
            fleet = asana_all("/tasks", {"section": ids["fleet"], "opt_fields": "name,completed"})
            if not any(str(t.get("name", "")).startswith(title) for t in fleet):
                d.update(work=True, kind="escalate", reason="%d blocked runs and no `%s` card yet" % (len(blocked), title))
                return d
        except BoardError as e:
            d["notes"].append("Fleet section unreadable: %s" % e)

    # 4. claim a new idea
    if live >= ids["max_parallel_runs"]:
        d["reason"] = "cap reached (live=%d/%d)" % (live, ids["max_parallel_runs"])
        return d
    if fresh_blocked >= MAX_FRESH_BLOCKED:
        d["reason"] = "%d runs freshly Blocked, not claiming" % fresh_blocked
        return d
    try:
        ideas = asana_all("/tasks", {"project": ids["ideas"], "opt_fields": "name,completed,notes"})
    except BoardError as e:
        d["board_error"] = str(e)
        d["reason"] = "Ideas board unreachable — not firing"
        return d
    taken = {str(st.get("idea_task")) for st in states.values() if st.get("idea_task")}
    skipped = skipped_gids(root)
    deferred, checked = [], 0
    for idea in ideas:
        if idea.get("completed") or idea["gid"] in taken or idea["gid"] in skipped:
            continue
        host = host_repo(idea.get("name", "")) or host_repo(idea.get("notes", ""))
        if host and any(r.endswith("/" + host) or r.endswith(host) for r in running_repos):
            deferred.append({"idea": idea["gid"], "host": host})
            continue
        if checked >= 10:
            d["notes"].append("more than 10 candidate ideas; stopped comment checks at 10")
            break
        checked += 1
        try:
            stories = asana_all("/tasks/%s/stories" % idea["gid"], {"opt_fields": "text,created_at"})
        except BoardError as e:
            d["notes"].append("stories of idea %s unreadable: %s" % (idea["gid"], e))
            stories = []
        texts = [str(s.get("text", "")) for s in stories]
        if any(x.startswith("claimed by coworld-builder run") or x.startswith("skipped by coworld-builder:") for x in texts):
            continue
        target = {"idea": idea["gid"], "name": idea.get("name")}
        if want_details:
            target["notes"] = idea.get("notes")
        d.update(work=True, kind="claim", target=target, deferred=deferred,
                 reason="claimable idea: %s (%s); live=%d/%d" % (idea.get("name"), idea["gid"], live, ids["max_parallel_runs"]))
        return d
    d["deferred"] = deferred
    d["reason"] = "nothing to do (live=%d/%d, %d ideas deferred behind busy host repos)" % (live, ids["max_parallel_runs"], len(deferred))
    return d


# --------------------------------------------------------------------------- fire / alert


def pick_deployment(ids):
    """The heartbeat deployment whose last run is oldest. Returns (name, id, skip_reason)."""
    best = None
    for name, dep in sorted(ids["deployments"].items()):
        runs = anthropic("/deployment_runs?deployment_id=%s&limit=1" % dep).get("data") or []
        last = parse_ts(runs[0].get("created_at")) if runs else None
        sid = runs[0].get("session_id") if runs else None
        if last and sid and (now() - last).total_seconds() < 15 * 60:
            try:
                s = anthropic("/sessions/%s" % sid)
                if s.get("status") == "running":
                    return name, dep, "a session on %s started %d s ago and is still running — it will see this work itself" % (
                        name, (now() - last).total_seconds())
            except urllib.error.HTTPError:
                pass
        key = last or dt.datetime.min.replace(tzinfo=dt.timezone.utc)
        if best is None or key < best[0]:
            best = (key, name, dep)
    if best is None:
        raise SystemExit("no heartbeat deployment ids in fleet/cloud.md")
    return best[1], best[2], None


def fire(ids, d):
    name, dep, skip = pick_deployment(ids)
    if skip:
        d["fired"] = None
        d["notes"].append(skip)
        return
    r = anthropic("/deployments/%s/run" % dep, {})
    d["fired"] = {"deployment": name, "id": dep, "run": r.get("id"), "session": r.get("session_id")}


def alert(ids, d):
    day = now().strftime("%Y-%m-%d")
    marker = ALERT_MARKER % day
    ch = ids["discord_channel"]
    try:
        msgs = discord("/channels/%s/messages" % ch, params={"limit": 50})
        if msgs is None:
            d["notes"].append("DISCORD_BOT_TOKEN not set; alert not posted")
            return
        if any(marker in (m.get("content") or "") for m in msgs):
            d["notes"].append("alert already posted today")
            return
        text = ("⚠️ coworld-builder heartbeat gate: the Builder board is unreachable, so no heartbeat is being fired.\n"
                "`%s`\nFix the ASANA_PAT credential or the board access, then the gate resumes on its own. %s" % (
                    d["board_error"][:300], marker))
        m = discord("/channels/%s/messages" % ch, {"content": text, "allowed_mentions": {"parse": []}, "flags": 4})
        d["notes"].append("alert posted: message %s" % (m or {}).get("id"))
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        d["notes"].append("alert failed: %s" % e)


# --------------------------------------------------------------------------- sandbox summary


def preflight():
    """The gh/jq preflight from prompts/00-claim.md step 0, and a fresh pull of the mount."""
    out = {}
    if subprocess.run(["bash", "-lc", "command -v gh"], capture_output=True).returncode != 0:
        subprocess.run(["bash", "-lc",
                        "curl -fsSL https://github.com/cli/cli/releases/download/v2.63.2/gh_2.63.2_linux_amd64.tar.gz | tar -xz -C /tmp "
                        "&& (install -m 0755 /tmp/gh_2.63.2_linux_amd64/bin/gh /usr/local/bin/gh 2>/dev/null "
                        "|| (mkdir -p $HOME/.local/bin && install -m 0755 /tmp/gh_2.63.2_linux_amd64/bin/gh $HOME/.local/bin/gh))"],
                       capture_output=True)
    for tool in ("gh", "jq", "git", "curl"):
        out[tool] = subprocess.run(["bash", "-lc", "command -v %s" % tool], capture_output=True).returncode == 0
    pull = subprocess.run(["git", "-C", ROOT, "pull", "--rebase", "-q"], capture_output=True, text=True)
    out["git_pull"] = "ok" if pull.returncode == 0 else ("failed: " + (pull.stderr or "")[-200:])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fire", action="store_true", help="fire a heartbeat deployment when there is work")
    ap.add_argument("--alert", action="store_true", help="post one Discord alert per day when the board is unreachable")
    ap.add_argument("--summary", action="store_true", help="sandbox mode: preflight + pull + decision with details")
    ap.add_argument("--root", default=ROOT, help="repo checkout to read runs/ from (default: this script's repo)")
    args = ap.parse_args()

    ids = read_cloud()
    d = {}
    if args.summary:
        d["preflight"] = preflight()
    d.update(decide(args.root, ids, want_details=args.summary, probe_root=args.root))
    if d.get("board_error"):
        if args.alert:
            alert(ids, d)
    elif d["work"] and args.fire:
        fire(ids, d)
    d["credentials_present"] = {k: bool(os.environ.get(k)) for k in ("ASANA_PAT", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY", "DISCORD_BOT_TOKEN", "GH_TOKEN", "SOFTMAX_TOKEN")}
    print(json.dumps(d, indent=1, sort_keys=True))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("**%s** — %s%s\n" % (d["kind"], d["reason"], (" → fired %s" % d["fired"]["deployment"]) if d.get("fired") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
