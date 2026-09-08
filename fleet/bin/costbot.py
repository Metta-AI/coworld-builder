#!/usr/bin/env python3
"""costbot.py — daily token-spend report for one Managed Agents fleet, posted to Discord.

One file, python3 stdlib only, identical in every fleet repo that carries it. Everything
fleet-specific is in `fleet/costbot.json` next to it (see CONFIG below).

  report [--day YYYY-MM-DD] [--post]
        Sum yesterday's (UTC) sessions for this fleet — every session whose deployment name
        starts with one of `deployment_prefixes` — and break the cost down by the agent that
        ran each thread (the coordinator and each sub-agent are separate threads, so this is the
        per-sub-agent split). Adds a trailing-7-day total. Prints the message; `--post` also
        sends it to `discord_channel_id` as the bot behind DISCORD_BOT_TOKEN, unless a message
        carrying this day's marker is already in the channel (so a re-run never double-posts).
  deploy [--dry-run]
        Create or update the reporter agent (`<fleet>-costbot`, system prompt = fleet/costbot.md)
        and its daily deployment from fleet/costbot.json; writes the ids back into that file.
  run   POST /deployments/{id}/run — fire the reporter now (it reports *yesterday*).
  status
        The reporter deployment's latest runs and their sessions.

Dollars are the API's own `usage.list_cost`: everything the session consumed priced at public
list rates (model tokens, web searches, and session running time at $0.08/h). Billed spend may
be lower with negotiated discounts. Per-thread costs exclude running time and are rounded
independently, so the "runtime/other" line is the session total minus the thread sum.

Credentials, never printed and never written to git:
  ANTHROPIC_AUTH_TOKEN  a federated `sk-ant-oat01-` bearer token (GitHub Actions gets one from
                        Workload Identity Federation; see .github/workflows/costbot.yml). Already
                        bound to the workspace, so no workspace header is sent.
  ANTHROPIC_API_KEY     else: an API key from the env, else AWS Secrets Manager
                        `daveey/anthropic/org-key` (profile softmax-org). An org-wide key gets
                        `anthropic-workspace-id: <workspace_id>` from the config on every call.
  DISCORD_BOT_TOKEN     env, else Secrets Manager `vault/discord/disco/app` (profile softmax,
                        JSON key DISCORD_BOT_TOKEN) — the disco bot.
  repo mount token      `gh auth token`, at `deploy` time only.
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "..", "costbot.json")
SYSTEM_MD = os.path.join(HERE, "..", "costbot.md")
API = "https://api.anthropic.com/v1"
DISCORD = "https://discord.com/api/v10"
MARKER = "[costbot %s %s]"  # fleet, day — the double-post guard greps for this
TOKENISH = re.compile(r"\b(ghp_|gho_|ghu_|ghs_|github_pat_|sk-ant-)[A-Za-z0-9_\-]+")


# --------------------------------------------------------------------------- config + creds


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    for k in ("fleet", "deployment_prefixes", "environment_id", "vault_ids", "discord_channel_id", "repo"):
        if not cfg.get(k):
            raise SystemExit(f"fleet/costbot.json is missing `{k}`")
    cfg.setdefault("ids", {})
    return cfg


def save_config(cfg):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=1)
        f.write("\n")


def _secret(secret_id, profile, region=None):
    cmd = [
        "aws",
        "secretsmanager",
        "get-secret-value",
        "--secret-id",
        secret_id,
        "--profile",
        profile,
        "--query",
        "SecretString",
        "--output",
        "text",
    ]
    if region:
        cmd += ["--region", region]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def anthropic_auth():
    """Headers that authenticate to the Anthropic API. ANTHROPIC_AUTH_TOKEN (a federated
    `sk-ant-oat01-` bearer token, already bound to its workspace) wins; else ANTHROPIC_API_KEY;
    else the org key from Secrets Manager. Only a key needs the workspace header."""
    tok = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if tok:
        return {"authorization": "Bearer " + tok}
    k = os.environ.get("ANTHROPIC_API_KEY")
    if not k:
        k = _secret("daveey/anthropic/org-key", "softmax-org")
        os.environ["ANTHROPIC_API_KEY"] = k
    return {"x-api-key": k}


def discord_token():
    t = os.environ.get("DISCORD_BOT_TOKEN")
    if not t:
        t = json.loads(_secret("vault/discord/disco/app", "softmax", "us-east-1"))["DISCORD_BOT_TOKEN"]
        os.environ["DISCORD_BOT_TOKEN"] = t
    return t


def gh_token():
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def redact_text(s):
    return TOKENISH.sub(lambda m: m.group(1) + "<redacted>", s or "")


# --------------------------------------------------------------------------- http


def _request(url, headers, body=None, method=None, tries=4, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    m = method or ("POST" if data else "GET")
    for i in range(tries):
        r = urllib.request.Request(url, data=data, method=m, headers=headers)
        try:
            with urllib.request.urlopen(r, timeout=timeout) as f:
                raw = f.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            text = redact_text(e.read().decode("utf-8", "replace"))[:1500]
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(2 ** (i + 1))
                continue
            sys.stderr.write("HTTP {} {} {}\n{}\n".format(e.code, m, url.split("?")[0], text))
            raise
        except (urllib.error.URLError, TimeoutError):
            if i < tries - 1:
                time.sleep(2 ** (i + 1))
                continue
            raise


def api(cfg, path, body=None, method=None, params=None):
    headers = {
        **anthropic_auth(),
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "managed-agents-2026-04-01",
        "content-type": "application/json",
    }
    if cfg.get("workspace_id") and "x-api-key" in headers:
        headers["anthropic-workspace-id"] = cfg["workspace_id"]
    url = API + path + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
    return _request(url, headers, body, method)


def page(cfg, path, params=None):
    """Every row of a list endpoint. Follows the cursor form (`next_page` -> `page=`) and the
    older `has_more`/`after_id` form; stops on a cursor that does not advance."""
    out, p, seen = [], dict(params or {}), set()
    p["limit"] = 100
    while True:
        d = api(cfg, path, params=p)
        rows = d.get("data") or []
        out += rows
        cur = d.get("next_page")
        if cur:
            if cur in seen:
                break
            seen.add(cur)
            p["page"] = cur
            continue
        if d.get("has_more") and rows and rows[-1].get("id"):
            after = rows[-1]["id"]
            if after in seen:
                break
            seen.add(after)
            p["after_id"] = after
            continue
        return out
    return out


def discord(path, body=None, params=None):
    headers = {
        "authorization": "Bot " + discord_token(),
        "content-type": "application/json",
        "user-agent": "DiscordBot (costbot, 1.0)",
    }
    url = DISCORD + path + ("?" + urllib.parse.urlencode(params) if params else "")
    return _request(url, headers, body, timeout=60)


# --------------------------------------------------------------------------- report


def cents(x):
    return int(((x or {}).get("list_cost") or {}).get("amount") or 0)


def usd(c):
    return f"${c / 100.0:.2f}"


def short(name, fleet):
    """`coworld-builder-designer` -> `designer`; the fleet's own name stays as is."""
    if name == fleet:
        return name
    pre = fleet + "-"
    return name.removeprefix(pre)


def fleet_deployments(cfg):
    prefixes = tuple(cfg["deployment_prefixes"])
    return {d["id"]: d["name"] for d in page(cfg, "/deployments") if d["name"].startswith(prefixes)}


def sessions_between(cfg, start, end):
    return page(cfg, "/sessions", {"created_at[gte]": start, "created_at[lt]": end, "include_archived": "true"})


def collect(cfg, day):
    """Everything the message needs, as plain data (also what --json prints)."""
    d0 = dt.date.fromisoformat(day)
    start, end = f"{d0}T00:00:00Z", f"{d0 + dt.timedelta(days=1)}T00:00:00Z"
    week_start = f"{d0 - dt.timedelta(days=6)}T00:00:00Z"
    depls = fleet_deployments(cfg)
    week = [s for s in sessions_between(cfg, week_start, end) if s.get("deployment_id") in depls]
    todays = [s for s in week if s["created_at"] >= start]

    by_agent, by_depl = {}, {}
    total = threads_total = 0
    for s in todays:
        c = cents(s.get("usage"))
        total += c
        dep = depls[s["deployment_id"]]
        b = by_depl.setdefault(dep, {"cents": 0, "sessions": 0})
        b["cents"] += c
        b["sessions"] += 1
        for t in page(cfg, "/sessions/{}/threads".format(s["id"])):
            a = t.get("agent") or {}
            name = a.get("name") or a.get("type") or "?"
            u = t.get("usage") or {}
            tc = cents(u)
            threads_total += tc
            row = by_agent.setdefault(
                name,
                {
                    "cents": 0,
                    "threads": 0,
                    "output_tokens": 0,
                    "input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "active_seconds": 0.0,
                },
            )
            row["cents"] += tc
            row["threads"] += 1
            row["output_tokens"] += u.get("output_tokens") or 0
            row["input_tokens"] += u.get("input_tokens") or 0
            row["cache_read_input_tokens"] += u.get("cache_read_input_tokens") or 0
            row["active_seconds"] += u.get("active_seconds") or 0.0
    for name in cfg.get("roster") or []:
        by_agent.setdefault(
            name,
            {
                "cents": 0,
                "threads": 0,
                "output_tokens": 0,
                "input_tokens": 0,
                "cache_read_input_tokens": 0,
                "active_seconds": 0.0,
            },
        )
    return {
        "fleet": cfg["fleet"],
        "day": day,
        "sessions": len(todays),
        "total_cents": total,
        "runtime_other_cents": max(total - threads_total, 0),
        "by_agent": by_agent,
        "by_deployment": by_depl,
        "week": {
            "start": week_start[:10],
            "end": day,
            "sessions": len(week),
            "total_cents": sum(cents(s.get("usage")) for s in week),
        },
    }


def ktok(n):
    return f"{round(n / 1000.0)}k" if n >= 1000 else str(n)


def render(r):
    fleet, day = r["fleet"], r["day"]
    plural = "" if r["sessions"] == 1 else "s"
    lines = [
        f"💸 **{fleet}** — token spend for {day} (UTC): **{usd(r['total_cents'])}** over {r['sessions']} session{plural}"
    ]
    rows = sorted(r["by_agent"].items(), key=lambda kv: (-kv[1]["cents"], kv[0]))
    width = max([len(short(n, fleet)) for n, _ in rows] + [len("runtime/other")])
    table = []
    for name, b in rows:
        table.append(
            f"{short(name, fleet):<{width}}  {usd(b['cents']):>9}  {b['threads']:>3} thr  {ktok(b['output_tokens']):>5} out tok"
        )
    table.append(f"{'runtime/other':<{width}}  {usd(r['runtime_other_cents']):>9}")
    lines.append("```")
    lines += table
    lines.append("```")
    if len(r["by_deployment"]) > 1:
        lines.append(
            "by cron: "
            + " · ".join(f"{n} {usd(b['cents'])} ({b['sessions']})" for n, b in sorted(r["by_deployment"].items()))
        )
    w = r["week"]
    marker = MARKER % (fleet, day)
    lines.append(
        f"7-day ({w['start']} → {w['end']}): **{usd(w['total_cents'])}** over {w['sessions']} sessions"
        f" · list price · sessions by UTC start · {marker}"
    )
    msg = "\n".join(lines)
    if len(msg) > 1990:  # Discord caps content at 2000
        msg = msg[:1980] + "\n…"
    return msg


def already_posted(cfg, day):
    marker = MARKER % (cfg["fleet"], day)
    msgs = discord("/channels/{}/messages".format(cfg["discord_channel_id"]), params={"limit": 50})
    return any(marker in (m.get("content") or "") for m in msgs)


def cmd_report(args, cfg):
    day = args.day or (dt.datetime.now(dt.UTC).date() - dt.timedelta(days=1)).isoformat()
    r = collect(cfg, day)
    if args.json:
        print(json.dumps(r, indent=1, sort_keys=True))
        return
    msg = render(r)
    print(msg)
    if not args.post:
        return
    if already_posted(cfg, day):
        print(
            "\n(not posted: a message with {} is already in channel {})".format(
                MARKER % (cfg["fleet"], day), cfg["discord_channel_id"]
            )
        )
        return
    m = discord(
        "/channels/{}/messages".format(cfg["discord_channel_id"]), {"content": msg, "allowed_mentions": {"parse": []}}
    )
    print("\nposted: message {} in channel {}".format(m.get("id"), m.get("channel_id")))


# --------------------------------------------------------------------------- deploy / run / status


def reporter_name(cfg):
    return cfg["fleet"] + "-costbot"


def agent_body(cfg):
    with open(SYSTEM_MD, encoding="utf-8") as f:
        system = f.read()
    return {
        "name": reporter_name(cfg),
        "description": "{}: daily token-spend reporter. Runs fleet/bin/costbot.py once and relays its output.".format(
            cfg["fleet"]
        ),
        "model": cfg.get("model") or {"id": "claude-sonnet-5", "effort": {"type": "low"}, "speed": "standard"},
        "tools": [
            {
                "type": "agent_toolset_20260401",
                "default_config": {"enabled": True, "permission_policy": {"type": "always_allow"}},
                "configs": [],
            }
        ],
        "system": system,
    }


def deployment_body(cfg, agent_id, agent_version, with_token=True):
    repo = cfg["repo"]
    script = repo["mount_path"].rstrip("/") + "/fleet/bin/costbot.py"
    return {
        "name": reporter_name(cfg),
        "agent": {"type": "agent", "id": agent_id, "version": agent_version},
        "environment_id": cfg["environment_id"],
        "vault_ids": list(cfg["vault_ids"]),
        "schedule": {"type": "cron", "expression": cfg.get("schedule") or "30 0 * * *", "timezone": "UTC"},
        "resources": [
            {
                "type": "github_repository",
                "url": repo["url"],
                "mount_path": repo["mount_path"],
                "authorization_token": gh_token() if with_token else "<resupply-at-apply>",
            }
        ],
        "initial_events": [
            {
                "type": "user.message",
                "content": [
                    {
                        "type": "text",
                        "text": f"Daily cost report. Run exactly once: `python3 {script} report --post` and reply with its stdout.",
                    }
                ],
            }
        ],
        "budget": {
            "type": "limit",
            "max_list_cost": {"amount": str(cfg.get("budget_cents") or 200), "currency": "USD"},
        },
    }


def norm_depl(d):
    out = {
        k: d.get(k)
        for k in ("name", "environment_id", "vault_ids", "schedule", "resources", "budget", "initial_events")
    }
    out["agent"] = {"type": "agent", "id": d["agent"]["id"], "version": d["agent"]["version"]}
    if out.get("schedule"):
        out["schedule"] = {k: out["schedule"][k] for k in ("type", "expression", "timezone") if k in out["schedule"]}
    res = []
    for r in out.get("resources") or []:
        r = {k: v for k, v in dict(r).items() if k not in ("id", "created_at", "updated_at")}
        if r.get("type") == "github_repository":
            r["authorization_token"] = "<resupply-at-apply>"
        res.append(r)
    out["resources"] = res
    return out


def redact(obj):
    """Deep copy with every credential-shaped value masked. Used by --dry-run."""
    if isinstance(obj, dict):
        return {
            k: ("<redacted>" if k in ("authorization_token", "secret_value") else redact(v)) for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    if isinstance(obj, str):
        return redact_text(obj)
    return obj


def show(label, payload):
    print(f"--- {label} ---")
    print(json.dumps(redact(payload), indent=1, sort_keys=True))


def cmd_deploy(args, cfg):
    ids = cfg["ids"]
    name = reporter_name(cfg)
    want = agent_body(cfg)

    live = None
    if ids.get("agent"):
        live = api(cfg, "/agents/{}".format(ids["agent"]))
    else:
        for a in page(cfg, "/agents"):
            if a["name"] == name:
                live = a
                break
    if live is None:
        if args.dry_run:
            show("POST /agents", want)
            agent_id, version = "<new>", 1
        else:
            a = api(cfg, "/agents", want)
            agent_id, version = a["id"], a["version"]
            print(f"CREATED agent {name} {agent_id} v{version}")
    else:
        agent_id, version = live["id"], live["version"]
        differs = (live.get("system") or "") != want["system"] or any(
            live.get(k) != want[k] for k in ("description", "model", "tools")
        )
        if differs:
            payload = {k: want[k] for k in ("description", "model", "tools", "system")}
            if args.dry_run:
                show(f"POST /agents/{agent_id} ({name})", payload)
            else:
                a = api(cfg, f"/agents/{agent_id}", payload)
                version = a["version"]
                print(f"VERSIONED agent {name} -> v{version}")
        else:
            print(f"unchanged agent {name} (live v{version})")
    ids["agent"], ids["agent_version"] = agent_id, version

    live_d = None
    if ids.get("deployment"):
        live_d = api(cfg, "/deployments/{}".format(ids["deployment"]))
    else:
        for d in page(cfg, "/deployments"):
            if d["name"] == name:
                live_d = d
                break
    body = deployment_body(cfg, agent_id, version, with_token=not args.dry_run)
    if live_d is None:
        if args.dry_run:
            show("POST /deployments", body)
        else:
            d = api(cfg, "/deployments", body)
            ids["deployment"] = d["id"]
            print(
                "CREATED deployment {} {} next={}".format(
                    name, d["id"], (d.get("schedule") or {}).get("upcoming_runs_at")
                )
            )
    else:
        ids["deployment"] = live_d["id"]
        cmp_want = json.loads(json.dumps(body))
        cmp_want["resources"][0]["authorization_token"] = "<resupply-at-apply>"
        got = norm_depl(live_d)
        changed = [k for k in cmp_want if got.get(k) != cmp_want[k]]
        if not changed:
            print("unchanged deployment {} ({})".format(name, live_d["id"]))
        else:
            payload = {k: body[k] for k in changed}
            if args.dry_run:
                show("POST /deployments/{} ({})".format(live_d["id"], name), payload)
            else:
                api(cfg, "/deployments/{}".format(live_d["id"]), payload)
                print("UPDATED deployment {} ({})".format(name, ", ".join(changed)))
    if not args.dry_run:
        save_config(cfg)
        print(f"wrote ids -> {os.path.relpath(CONFIG)}")


def cmd_run(args, cfg):
    dep = cfg["ids"].get("deployment")
    if not dep:
        raise SystemExit("no deployment id in fleet/costbot.json — run `deploy` first")
    d = api(cfg, f"/deployments/{dep}/run", {})
    print("triggered {} -> run={} session={}".format(reporter_name(cfg), d.get("id"), d.get("session_id")))


def cmd_status(args, cfg):
    dep = cfg["ids"].get("deployment")
    if not dep:
        raise SystemExit("no deployment id in fleet/costbot.json — run `deploy` first")
    d = api(cfg, f"/deployments/{dep}")
    print(
        "{} {} status={} schedule={} next={} agent={} v{}".format(
            d.get("name"),
            dep,
            d.get("status"),
            (d.get("schedule") or {}).get("expression"),
            ((d.get("schedule") or {}).get("upcoming_runs_at") or ["?"])[0],
            d["agent"]["id"],
            d["agent"]["version"],
        )
    )
    if d.get("paused_reason"):
        print("  paused_reason: {}".format(d["paused_reason"]))
    runs = api(cfg, "/deployment_runs", params={"deployment_id": dep, "limit": args.limit})
    for r in runs.get("data") or []:
        line = "  {}  run={}".format(r.get("created_at"), r.get("id"))
        if r.get("error"):
            print(line + "  ERROR {}".format(json.dumps(r["error"])[:200]))
            continue
        sid = r.get("session_id")
        if sid:
            s = api(cfg, f"/sessions/{sid}")
            line += "  session={} {} cost={}".format(sid, s.get("status"), usd(cents(s.get("usage"))))
        print(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="deploy: print payloads instead of sending them")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="yesterday's spend by sub-agent; --post sends it to Discord")
    r.add_argument("--day", help="UTC day YYYY-MM-DD (default: yesterday)")
    r.add_argument("--post", action="store_true", help="post to Discord (skipped if already posted)")
    r.add_argument("--json", action="store_true", help="print the raw numbers instead of the message")
    sub.add_parser("deploy", help="create/update the reporter agent + daily deployment")
    sub.add_parser("run", help="fire the reporter deployment now")
    s = sub.add_parser("status", help="the reporter deployment's latest runs")
    s.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    cfg = load_config()
    {"report": cmd_report, "deploy": cmd_deploy, "run": cmd_run, "status": cmd_status}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
