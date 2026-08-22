#!/usr/bin/env python3
"""deploy.py — create and maintain the coworld-builder managed agents + deployment.

Git is the source of truth for configuration; the Anthropic Managed-Agents API is the runtime.
Modelled on daveey/cogamer's fleet/bin/fleetctl.py (same api()/key() helpers, same
"tokens are never in git, re-supplied at apply time" rule).

  create             create the six sub-agents (agents/<role>.json + agents/<role>.md), then the
                     coordinator (agents/coordinator.json + AGENT.md) with the roster ids, then
                     the deployment (fleet/deployment.json) with repo tokens from `gh auth token`.
                     Writes every id into fleet/cloud.md's ids table.
  update             compare local config against live and POST a new agent version wherever the
                     system prompt or (model, tools, description, skills, multiagent) differ; then
                     update the deployment (schedule/resources/vaults/agent version) if it drifted.
  run                POST /deployments/{id}/run — a manual heartbeat, off-schedule.
  status             latest deployment runs + their session status.

  --dry-run          print the payloads (redacted) instead of sending them. Works on every
                     subcommand.

Credentials: ANTHROPIC_API_KEY from the environment, else AWS Secrets Manager
(daveey/anthropic/api-key, profile softmax-org). Repo tokens from `gh auth token`, at apply
time only. This tool never prints a token, an api key, or a vault secret.

Run from anywhere; paths resolve against the repo root. python3 stdlib only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLOUD_MD = os.path.join(ROOT, "fleet", "cloud.md")
AGENTS_DIR = os.path.join(ROOT, "agents")
DEPLOYMENT_JSON = os.path.join(ROOT, "fleet", "deployment.json")
API = "https://api.anthropic.com/v1"

ROLES = ["designer", "builder", "reviewer", "fixer", "judge", "verifier"]
COORDINATOR = "coworld-builder-coordinator"
DEPLOYMENT_NAME = "coworld-builder-hourly"

AGENT_FIELDS = ("name", "description", "model", "tools", "mcp_servers", "skills", "multiagent")
VERSIONED_FIELDS = ("description", "model", "tools", "skills", "multiagent")
DEPL_FIELDS = ("name", "environment_id", "vault_ids", "schedule", "resources")

IDS_START = "<!-- ids:start -->"
IDS_END = "<!-- ids:end -->"


# --------------------------------------------------------------------------- credentials


def key():
    """ANTHROPIC_API_KEY from env, else Secrets Manager. Never printed."""
    k = os.environ.get("ANTHROPIC_API_KEY")
    if not k:
        k = subprocess.run(
            ["aws", "secretsmanager", "get-secret-value", "--secret-id",
             "daveey/anthropic/api-key", "--profile", "softmax-org",
             "--query", "SecretString", "--output", "text"],
            capture_output=True, text=True, check=True).stdout.strip()
        os.environ["ANTHROPIC_API_KEY"] = k
    return k


def gh_token():
    """A GitHub token for the repo resources. Never printed, never written to git."""
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                          check=True).stdout.strip()


def api(path, body=None, method=None, tries=3):
    data = json.dumps(body).encode() if body is not None else None
    m = method or ("POST" if data else "GET")
    for i in range(tries):
        r = urllib.request.Request(API + path, data=data, method=m, headers={
            "x-api-key": key(), "anthropic-version": "2023-06-01",
            "anthropic-beta": "managed-agents-2026-04-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=120) as f:
                return json.loads(f.read())
        except urllib.error.HTTPError as e:
            sys.stderr.write("HTTP %s %s %s\n%s\n" % (e.code, m, path, e.read().decode(
                "utf-8", "replace")[:2000]))
            raise
        except Exception:
            if i < tries - 1:
                time.sleep(2 ** i)
                continue
            raise


def page(path):
    out, url = [], path + ("&" if "?" in path else "?") + "limit=100"
    while url:
        d = api(url)
        rows = d.get("data", d if isinstance(d, list) else [])
        out += rows
        nxt = d.get("next_page_url") if isinstance(d, dict) else None
        if nxt and nxt.startswith(API):
            nxt = nxt[len(API):]
        url = nxt
    return out


# --------------------------------------------------------------------------- redaction


SECRETISH = re.compile(r"(authorization_token|token|api_key|x-api-key|secret|password)",
                       re.IGNORECASE)


def redact(obj):
    """Deep-copy with anything that smells like a credential replaced. Used by --dry-run."""
    if isinstance(obj, dict):
        return {k: ("<redacted>" if SECRETISH.search(str(k)) and isinstance(v, str) else redact(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    if isinstance(obj, str) and (obj.startswith("ghp_") or obj.startswith("gho_")
                                 or obj.startswith("github_pat_") or obj.startswith("sk-ant-")):
        return "<redacted>"
    return obj


def show(label, payload):
    print("--- %s ---" % label)
    print(json.dumps(redact(payload), indent=1, sort_keys=True))


# --------------------------------------------------------------------------- cloud.md


def read_cloud():
    """Parse fleet/cloud.md: environment_id, vault_ids, and the ids table."""
    body = open(CLOUD_MD, encoding="utf-8").read()
    env = re.search(r"`environment_id:\s*([A-Za-z0-9_\-]+)`", body)
    vaults = re.search(r"`vault_ids:\s*([^`]+)`", body)
    ids = {}
    section = body.split(IDS_START, 1)[1].split(IDS_END, 1)[0] if IDS_START in body else ""
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(cells) >= 5 and cells[0].startswith("coworld-builder-"):
            ids[cells[0]] = {"kind": cells[1], "id": cells[3],
                             "version": cells[4]}
    return {
        "environment_id": env.group(1) if env else None,
        "vault_ids": [v.strip() for v in vaults.group(1).split(",")] if vaults else [],
        "ids": ids,
    }


def write_cloud(rows):
    """Rewrite the ids table between the markers. rows: name -> (kind, model, id, version)."""
    body = open(CLOUD_MD, encoding="utf-8").read()
    head, rest = body.split(IDS_START, 1)
    _, tail = rest.split(IDS_END, 1)
    lines = ["| name | kind | model | id | version |", "|---|---|---|---|---|"]
    for name, (kind, model, ident, version) in rows.items():
        lines.append("| %s | %s | %s | %s | %s |" % (
            name, kind, model or "—", "`%s`" % ident if ident and ident != "TBD" else "TBD",
            version if version is not None else "—"))
    open(CLOUD_MD, "w", encoding="utf-8").write(
        head + IDS_START + "\n" + "\n".join(lines) + "\n" + IDS_END + tail)
    print("wrote ids table -> %s" % CLOUD_MD)


# --------------------------------------------------------------------------- local config


def load_system(spec):
    """Resolve a `<file: path>` system field to the file's text, relative to the repo root."""
    m = re.match(r"^\s*<file:\s*(.+?)\s*>\s*$", spec or "")
    if not m:
        raise SystemExit("system field must be '<file: path>', got: %r" % (spec,))
    path = os.path.join(ROOT, m.group(1))
    if not os.path.exists(path):
        raise SystemExit("system prompt file missing: %s" % path)
    return open(path, encoding="utf-8").read()


def load_agent(name_or_role):
    """agents/<role>.json (+ its system file) -> (name, body-for-the-API)."""
    path = os.path.join(AGENTS_DIR, name_or_role + ".json")
    cfg = json.load(open(path, encoding="utf-8"))
    cfg.pop("_comment", None)
    body = {k: cfg[k] for k in AGENT_FIELDS if cfg.get(k) is not None}
    body["system"] = load_system(cfg.get("system"))
    return cfg["name"], body


def live_state():
    ags = {a["name"]: a for a in page("/agents") if a["name"].startswith("coworld-builder-")}
    dps = {d["name"]: d for d in page("/deployments") if d["name"].startswith("coworld-builder-")}
    return ags, dps


def norm_depl(d):
    out = {k: d.get(k) for k in DEPL_FIELDS}
    out["agent"] = {"id": d["agent"]["id"], "version": d["agent"]["version"]}
    if out.get("schedule"):
        out["schedule"] = {k: out["schedule"][k] for k in ("type", "expression", "timezone")
                           if k in out["schedule"]}
    res = []
    for r in out.get("resources") or []:
        r = {k: v for k, v in dict(r).items() if k not in ("id", "created_at", "updated_at")}
        if r.get("type") == "github_repository":
            r["authorization_token"] = "<resupply-at-apply>"
        res.append(r)
    out["resources"] = res
    return out


def deployment_body(coordinator_id, coordinator_version, cloud, with_token=True):
    cfg = json.load(open(DEPLOYMENT_JSON, encoding="utf-8"))
    cfg.pop("_comment", None)
    cfg["agent"] = {"type": "agent", "id": coordinator_id, "version": coordinator_version}
    cfg["environment_id"] = cloud["environment_id"]
    cfg["vault_ids"] = [v for v in cloud["vault_ids"] if v and not v.startswith("<")]
    if not cfg["environment_id"] or cfg["environment_id"].startswith("<"):
        raise SystemExit("fleet/cloud.md has no usable `environment_id:` line")
    if not cfg["vault_ids"]:
        raise SystemExit("fleet/cloud.md has no usable `vault_ids:` line")
    tok = gh_token() if with_token else "<resupply-at-apply>"
    for r in cfg.get("resources") or []:
        if r.get("type") == "github_repository":
            r["authorization_token"] = tok
    return cfg


# --------------------------------------------------------------------------- commands


def cmd_create(args):
    cloud = read_cloud()
    rows, roster = {}, []
    for role in ROLES:
        name, body = load_agent(role)
        if args.dry_run:
            show("POST /agents (%s)" % name, body)
            rows[name] = ("agent", body["model"]["id"], "TBD", "TBD")
            roster.append({"type": "agent", "id": "<dry-run>", "version": 1})
            continue
        a = api("/agents", body)
        print("CREATED agent %s %s v%s" % (name, a["id"], a["version"]))
        rows[name] = ("agent", body["model"]["id"], a["id"], a["version"])
        roster.append({"type": "agent", "id": a["id"], "version": a["version"]})

    name, body = load_agent("coordinator")
    body.setdefault("multiagent", {})["type"] = "coordinator"
    body["multiagent"]["agents"] = roster
    if args.dry_run:
        show("POST /agents (%s)" % name, body)
        rows[name] = ("agent", body["model"]["id"], "TBD", "TBD")
        coord_id, coord_ver = "<dry-run>", 1
    else:
        c = api("/agents", body)
        coord_id, coord_ver = c["id"], c["version"]
        print("CREATED agent %s %s v%s" % (name, coord_id, coord_ver))
        rows[name] = ("agent", body["model"]["id"], coord_id, coord_ver)

    depl = deployment_body(coord_id, coord_ver, cloud, with_token=not args.dry_run)
    if args.dry_run:
        show("POST /deployments", depl)
        rows[DEPLOYMENT_NAME] = ("deployment", None, "TBD", None)
        print("\n(dry run — nothing created, cloud.md untouched)")
        return
    d = api("/deployments", depl)
    print("CREATED deployment %s %s (%s UTC)" % (
        d["name"], d["id"], depl["schedule"]["expression"]))
    rows[DEPLOYMENT_NAME] = ("deployment", None, d["id"], None)
    write_cloud(rows)


def cmd_update(args):
    cloud = read_cloud()
    ags, dps = live_state()
    rows = {}
    roster = []
    for role in ROLES + ["coordinator"]:
        name, body = load_agent(role)
        live = ags.get(name)
        if live is None:
            print("MISSING live agent %s — run `create` first (or create it by hand)" % name)
            rows[name] = ("agent", body["model"]["id"], "TBD", "TBD")
            continue
        if role == "coordinator" and roster:
            body.setdefault("multiagent", {})["type"] = "coordinator"
            body["multiagent"]["agents"] = roster
        differs = (live.get("system") or "") != body["system"] or any(
            live.get(k) != body.get(k) for k in VERSIONED_FIELDS if body.get(k) is not None)
        if not differs:
            print("unchanged agent %s (live v%s)" % (name, live.get("version")))
            rows[name] = ("agent", body["model"]["id"], live["id"], live.get("version"))
            if role != "coordinator":
                roster.append({"type": "agent", "id": live["id"], "version": live.get("version")})
            continue
        payload = {"system": body["system"], **{k: body[k] for k in VERSIONED_FIELDS
                                                if body.get(k) is not None}}
        if args.dry_run:
            show("POST /agents/%s (%s)" % (live["id"], name), payload)
            rows[name] = ("agent", body["model"]["id"], live["id"], live.get("version"))
            if role != "coordinator":
                roster.append({"type": "agent", "id": live["id"], "version": live.get("version")})
            continue
        a = api("/agents/%s" % live["id"], payload)
        print("VERSIONED agent %s -> v%s" % (name, a["version"]))
        rows[name] = ("agent", body["model"]["id"], a["id"], a["version"])
        if role != "coordinator":
            roster.append({"type": "agent", "id": a["id"], "version": a["version"]})

    coord = rows.get(COORDINATOR)
    live_depl = dps.get(DEPLOYMENT_NAME)
    if live_depl is None:
        print("MISSING live deployment %s — run `create` first" % DEPLOYMENT_NAME)
    elif not coord or coord[2] == "TBD":
        print("SKIP deployment: no coordinator id")
    else:
        want = deployment_body(coord[2], coord[3], cloud, with_token=not args.dry_run)
        cmp_want = json.loads(json.dumps(want))
        cmp_want.pop("initial_events", None)
        for r in cmp_want.get("resources") or []:
            if r.get("type") == "github_repository":
                r["authorization_token"] = "<resupply-at-apply>"
        got = norm_depl(live_depl)
        changed = [k for k in cmp_want if got.get(k) != cmp_want.get(k)]
        if not changed:
            print("unchanged deployment %s" % DEPLOYMENT_NAME)
        else:
            # POST only the differing fields: the update endpoint 400s on full-config bodies
            # (immutable fields), and an agent repoint needs agent.type.
            payload = {k: want[k] for k in changed}
            if "agent" in payload:
                payload["agent"] = {"type": "agent", "id": want["agent"]["id"],
                                    "version": want["agent"]["version"]}
            if args.dry_run:
                show("POST /deployments/%s" % live_depl["id"], payload)
            else:
                api("/deployments/%s" % live_depl["id"], payload)
                print("UPDATED deployment %s (%s)" % (DEPLOYMENT_NAME, ", ".join(changed)))
        rows[DEPLOYMENT_NAME] = ("deployment", None, live_depl["id"], None)

    if not args.dry_run:
        write_cloud(rows)


def _deployment_id(cloud, dry_run=False):
    row = cloud["ids"].get(DEPLOYMENT_NAME)
    ident = (row or {}).get("id", "").strip("`")
    if ident and ident != "TBD":
        return ident
    if dry_run:
        return "<deployment id not yet in cloud.md — run create>"
    _, dps = live_state()
    d = dps.get(DEPLOYMENT_NAME)
    if not d:
        raise SystemExit("no deployment %s — run `create` first" % DEPLOYMENT_NAME)
    return d["id"]


def cmd_run(args):
    dep = _deployment_id(read_cloud(), args.dry_run)
    if args.dry_run:
        show("POST /deployments/%s/run" % dep, {})
        return
    d = api("/deployments/%s/run" % dep, {})
    print("triggered %s -> %s" % (DEPLOYMENT_NAME, json.dumps(redact(d))[:400]))


def cmd_status(args):
    dep = _deployment_id(read_cloud(), args.dry_run)
    if args.dry_run:
        show("GET /deployment_runs?deployment_id=%s&limit=%d" % (dep, args.limit), {})
        return
    d = api("/deployments/%s" % dep)
    sched = (d.get("schedule") or {}).get("expression")
    print("%s %s status=%s schedule=%s agent=%s v%s" % (
        DEPLOYMENT_NAME, dep, d.get("status"), sched,
        d.get("agent", {}).get("id"), d.get("agent", {}).get("version")))
    if d.get("paused_reason"):
        print("  paused_reason: %s" % d["paused_reason"])
    runs = api("/deployment_runs?deployment_id=%s&limit=%d" % (dep, args.limit))
    for r in (runs.get("data") or runs if isinstance(runs, dict) else runs)[: args.limit]:
        sid = r.get("session_id")
        line = "  %s  run=%s" % (r.get("created_at"), r.get("id"))
        if r.get("error"):
            print(line + "  ERROR %s" % json.dumps(redact(r["error"]))[:200])
            continue
        if sid:
            s = api("/sessions/%s" % sid)
            line += "  session=%s %s updated=%s" % (sid, s.get("status"), s.get("updated_at"))
        print(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="print redacted payloads instead of sending them")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("create", help="create the sub-agents, the coordinator, and the deployment")
    sub.add_parser("update", help="new agent versions where config differs; update the deployment")
    sub.add_parser("run", help="POST /deployments/{id}/run — a manual heartbeat")
    s = sub.add_parser("status", help="latest deployment runs + session status")
    s.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    {"create": cmd_create, "update": cmd_update, "run": cmd_run, "status": cmd_status}[
        args.cmd](args)


if __name__ == "__main__":
    main()
