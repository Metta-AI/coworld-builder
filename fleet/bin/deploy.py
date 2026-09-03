#!/usr/bin/env python3
"""deploy.py — create and maintain the coworld-builder managed agents + deployment.

Git is the source of truth for configuration; the Anthropic Managed-Agents API is the runtime.
Modelled on daveey/cogamer's fleet/bin/fleetctl.py (same api()/key() helpers, same
"tokens are never in git, re-supplied at apply time" rule).

  create             create whatever does not exist live yet: the six sub-agents
                     (agents/<role>.json + agents/<role>.md), the coordinator
                     (agents/coordinator.json + AGENT.md) with the roster ids, and each of the
                     K heartbeat deployments in fleet/deployment.json's `deployments` list, with
                     repo tokens from `gh auth token`. Anything already live is SKIPped, never
                     duplicated — so `create` is also how deployment b and c are added while a
                     is already running. Writes every id into fleet/cloud.md's ids table.
  update             compare local config against live and POST a new agent version wherever the
                     system prompt or (model, tools, description, skills, multiagent) differ; then
                     reconcile ALL K deployments (name/schedule/resources/vaults/agent version).
  run                POST /deployments/{id}/run — a manual heartbeat, off-schedule.
                     `--name <suffix>` picks which one (default `a`).
  status             every deployment's latest runs + their session status.

Parallelism: several coworld runs advance at once. Each of the K deployments is one heartbeat
cron (staggered inside the hour); `max_parallel_runs` in fleet/cloud.md §Parallelism is the cap
the coordinator itself enforces. fleet/deployment.json is the authority for what this tool
applies; fleet/cloud.md §Parallelism is the same table for the agents to read, and a
disagreement between them prints a WARNING here.

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
DEPLOYMENT_PREFIX = "coworld-builder-"
# The pre-parallelism single deployment. `update` renames it to LEGACY_TARGET (same id, new
# schedule) rather than creating a second cron beside it; it is never deleted.
LEGACY_DEPLOYMENT_NAME = "coworld-builder-hourly"
LEGACY_TARGET = "coworld-builder-a"

AGENT_FIELDS = ("name", "description", "model", "tools", "mcp_servers", "skills", "multiagent")
# `mcp_servers` was in AGENT_FIELDS but not here, so an edit to it in agents/<role>.json was a
# silent no-op on `update` — the same class of bug fleetctl.py fixed for `skills` (its comment at
# cmd_apply). Added 2026-08-22.
# `multiagent` is sent in the version body too, so a roster change takes effect. fleetctl.py sends
# only description/model/tools/skills, and its comment warns the update endpoint 400s on immutable
# fields; `multiagent` here is UNVERIFIED against that endpoint. Verify with `--dry-run update`
# followed by one real `update` after a roster edit, and record the outcome in this comment.
VERSIONED_FIELDS = ("description", "model", "tools", "mcp_servers", "skills", "multiagent")
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
            # The failing request may carry a live `gh` token (create's resources), and some
            # APIs echo request context back in the error body — redact before printing.
            sys.stderr.write("HTTP %s %s %s\n%s\n" % (e.code, m, path, redact_text(
                e.read().decode("utf-8", "replace"))[:2000]))
            raise
        except Exception:
            if i < tries - 1:
                time.sleep(2 ** i)
                continue
            raise


def page(path):
    """Every row of a list endpoint. Follows `next_page_url` AND the `has_more`/`after_id`
    form, exactly as fleetctl.py does — `/agents` is account-wide and filtered client-side, so
    a dropped page silently truncates live_state() and makes an existing agent look missing."""
    base = path.split("?", 1)[0]
    query = path.split("?", 1)[1] if "?" in path else ""
    out, url = [], path + ("&" if "?" in path else "?") + "limit=100"
    seen = set()
    while url:
        d = api(url)
        rows = d.get("data", d if isinstance(d, list) else []) if isinstance(d, dict) else d
        rows = rows or []
        out += rows
        nxt = d.get("next_page_url") if isinstance(d, dict) else None
        if nxt and nxt.startswith(API):
            nxt = nxt[len(API):]
        if not nxt and isinstance(d, dict) and d.get("has_more") and rows and rows[-1].get("id"):
            after = rows[-1]["id"]
            if after in seen:          # defensive: an endpoint that never advances
                break
            seen.add(after)
            nxt = "%s?%slimit=100&after_id=%s" % (base, (query + "&") if query else "", after)
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


TOKENISH = re.compile(r"\b(ghp_|gho_|ghu_|ghs_|github_pat_|sk-ant-)[A-Za-z0-9_\-]+")


def redact_text(s):
    """Mask token-shaped substrings in free text (HTTP error bodies, tails, logs)."""
    return TOKENISH.sub(lambda m: m.group(1) + "<redacted>", s or "")


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
            ids[cells[0]] = {"kind": cells[1], "model": cells[2], "id": cells[3].strip("`"),
                             "version": cells[4]}
    return {
        "environment_id": env.group(1) if env else None,
        "vault_ids": [v.strip() for v in vaults.group(1).split(",")] if vaults else [],
        "ids": ids,
    }


def read_parallelism():
    """fleet/cloud.md §Parallelism: `max_parallel_runs: N` and the {suffix: cron} table.

    Documentation for the agents (they read `max_parallel_runs`), and a cross-check for this
    tool — `fleet/deployment.json` is what gets applied.
    """
    body = open(CLOUD_MD, encoding="utf-8").read()
    sec = body.split("## Parallelism", 1)[1].split("\n## ", 1)[0] if "## Parallelism" in body else ""
    m = re.search(r"`max_parallel_runs:\s*(\d+)`", sec)
    crons = {}
    row = re.compile(r"^\|\s*`%s([a-z0-9\-]+)`\s*\|\s*`([^`]+)`\s*\|" % re.escape(DEPLOYMENT_PREFIX))
    for line in sec.splitlines():
        mm = row.match(line.strip())
        if mm:
            crons[mm.group(1)] = mm.group(2)
    return {"max_parallel_runs": int(m.group(1)) if m else None, "crons": crons}


def deployment_specs():
    """[(name, suffix, cron)] from fleet/deployment.json's `deployments` list, cross-checked
    against fleet/cloud.md §Parallelism. One template body, K names and K crons."""
    cfg = json.load(open(DEPLOYMENT_JSON, encoding="utf-8"))
    specs = cfg.get("deployments")
    if not specs:
        raise SystemExit("fleet/deployment.json declares no `deployments` list — parallelism "
                         "needs one entry per heartbeat cron, e.g. {\"suffix\":\"a\","
                         "\"cron\":\"11 * * * *\"}")
    out, seen = [], set()
    for s in specs:
        suf, cron = s.get("suffix"), s.get("cron")
        if not suf or not cron:
            raise SystemExit("every `deployments` entry needs `suffix` and `cron`: %r" % (s,))
        if suf in seen:
            raise SystemExit("duplicate deployment suffix %r in fleet/deployment.json" % suf)
        seen.add(suf)
        out.append((DEPLOYMENT_PREFIX + suf, suf, cron))
    doc = read_parallelism()
    for name, suf, cron in out:
        if suf not in doc["crons"]:
            print("WARNING %s is not in fleet/cloud.md §Parallelism" % name)
        elif doc["crons"][suf] != cron:
            print("WARNING %s: cron %r in fleet/deployment.json, %r in fleet/cloud.md "
                  "§Parallelism (deployment.json wins)" % (name, cron, doc["crons"][suf]))
    for suf in doc["crons"]:
        if suf not in seen:
            print("WARNING fleet/cloud.md §Parallelism lists %s%s, which fleet/deployment.json "
                  "does not declare" % (DEPLOYMENT_PREFIX, suf))
    if doc["max_parallel_runs"] is None:
        print("WARNING fleet/cloud.md has no `max_parallel_runs:` line — the coordinator reads it")
    return out


def write_cloud(rows):
    """Merge rows into the ids table between the markers. rows: name -> (kind, model, id, version).

    Merging, never replacing: a row this run did not resolve keeps whatever `fleet/cloud.md`
    already recorded, and **a real id is never overwritten with TBD**. `_deployment_id()`, `run`
    and `status` all read those ids back, so a lookup miss (a rename, an API blip, a truncated
    page) that stamped TBD over them used to break the tool until a human re-ran `create`.
    """
    existing = read_cloud()["ids"]
    merged = {}
    order = [n for n in list(existing) if n not in rows] + list(rows)
    seen = []
    for name in order:
        if name in seen:
            continue
        seen.append(name)
        old = existing.get(name)
        old_row = (old["kind"], old.get("model"), old.get("id"), old.get("version")) if old else None
        new_row = rows.get(name)
        if new_row is None:
            merged[name] = old_row
            continue
        kind, model, ident, version = new_row
        if (not ident or ident == "TBD") and old_row and old_row[2] and old_row[2] != "TBD":
            print("KEEPING recorded id for %s (%s) — this run did not resolve one"
                  % (name, old_row[2]))
            merged[name] = (kind, model or old_row[1], old_row[2], old_row[3])
            continue
        merged[name] = (kind, model or (old_row[1] if old_row else None), ident, version)

    body = open(CLOUD_MD, encoding="utf-8").read()
    head, rest = body.split(IDS_START, 1)
    _, tail = rest.split(IDS_END, 1)
    lines = ["| name | kind | model | id | version |", "|---|---|---|---|---|"]
    for name, row in merged.items():
        kind, model, ident, version = row
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
    # The list endpoint stops at 100 rows and the account has more deployments than that
    # (2026-09-03: `update` reported all three heartbeats MISSING and would have skipped the
    # agent repoint). Anything cloud.md already records is fetched by id instead.
    cloud = read_cloud()
    for name, _suffix, _cron in deployment_specs():
        if name in dps:
            continue
        # Read the recorded id directly: _deployment_id() falls back to live_state() when the
        # row is absent, which would recurse.
        dep_id = ((cloud["ids"].get(name) or {}).get("id") or "").strip("`")
        if not dep_id or dep_id == "TBD":
            continue
        try:
            d = api("/deployments/%s" % dep_id)
        except Exception as exc:  # noqa: BLE001 - a stale id must not abort the whole pass
            print("WARN deployment %s (%s) not fetchable by id: %s" % (name, dep_id, exc))
            continue
        if d.get("name", name).startswith("coworld-builder-"):
            dps[d.get("name", name)] = d
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


def deployment_body(coordinator_id, coordinator_version, cloud, spec, with_token=True):
    """The one template body in fleet/deployment.json, stamped with this spec's name and cron."""
    name, _suffix, cron = spec
    cfg = json.load(open(DEPLOYMENT_JSON, encoding="utf-8"))
    cfg.pop("_comment", None)
    # `deployments` is this tool's fan-out list, not part of the API body.
    cfg.pop("deployments", None)
    cfg["name"] = name
    sched = dict(cfg.get("schedule") or {})
    sched.update({"type": "cron", "expression": cron, "timezone": sched.get("timezone", "UTC")})
    cfg["schedule"] = sched
    cfg["agent"] = {"type": "agent", "id": coordinator_id, "version": coordinator_version}
    cfg["environment_id"] = cloud["environment_id"]
    cfg["vault_ids"] = [v for v in cloud["vault_ids"] if v and not v.startswith("<")]
    if not cfg["environment_id"] or cfg["environment_id"].startswith("<"):
        raise SystemExit("fleet/cloud.md has no usable `environment_id:` line")
    if not cfg["vault_ids"]:
        raise SystemExit("fleet/cloud.md has no usable `vault_ids:` line")
    tok = gh_token() if with_token else "<resupply-at-apply>"
    repos = [r for r in cfg.get("resources") or [] if r.get("type") == "github_repository"]
    if not repos:
        raise SystemExit("fleet/deployment.json declares no github_repository resources")
    for r in repos:
        # EVERY repo mount gets the token re-supplied here — this repo, cogamer, and each of the
        # six read-only starters at /workspace/starters/<name>.
        r["authorization_token"] = tok
    print("%s: %d repo mount(s): %s"
          % (name, len(repos), ", ".join(r["mount_path"] for r in repos)))
    return cfg


# --------------------------------------------------------------------------- commands


def cmd_create(args):
    """Create what is missing, SKIP what exists. Never duplicates a name.

    fleetctl.py's apply creates only `if live is None`, and this used to be a blanket refusal:
    a second `create` would otherwise duplicate all seven agents AND add a second cron firing
    the same coordinator. Parallelism made the blanket refusal wrong — adding deployment b and
    c while a is live is a normal `create` — so the guard moved from "refuse if anything
    exists" to "create only the names that do not exist live".
    """
    cloud = read_cloud()
    specs = deployment_specs()
    if args.dry_run:
        print("(dry run — live state not read; a real `create` SKIPs every agent and deployment "
              "that already exists live and creates only the missing ones)")
        ags, dps = {}, {}
    else:
        ags, dps = live_state()

    rows, roster, made_agent = {}, [], False
    for role in ROLES:
        name, body = load_agent(role)
        live = ags.get(name)
        if live is not None:
            print("SKIP agent %s (live %s v%s) — `update` versions it" % (
                name, live["id"], live.get("version")))
            rows[name] = ("agent", body["model"]["id"], live["id"], live.get("version"))
            roster.append({"type": "agent", "id": live["id"], "version": live.get("version")})
            continue
        if args.dry_run:
            show("POST /agents (%s)" % name, body)
            rows[name] = ("agent", body["model"]["id"], "TBD", "TBD")
            roster.append({"type": "agent", "id": "<dry-run>", "version": 1})
            continue
        a = api("/agents", body)
        print("CREATED agent %s %s v%s" % (name, a["id"], a["version"]))
        rows[name] = ("agent", body["model"]["id"], a["id"], a["version"])
        roster.append({"type": "agent", "id": a["id"], "version": a["version"]})
        made_agent = True

    name, body = load_agent("coordinator")
    body.setdefault("multiagent", {})["type"] = "coordinator"
    body["multiagent"]["agents"] = roster
    live_coord = ags.get(name)
    if live_coord is not None:
        print("SKIP agent %s (live %s v%s) — `update` versions it" % (
            name, live_coord["id"], live_coord.get("version")))
        rows[name] = ("agent", body["model"]["id"], live_coord["id"], live_coord.get("version"))
        coord_id, coord_ver = live_coord["id"], live_coord.get("version")
        if made_agent:
            print("NOTE the coordinator already existed, so its roster still lacks the "
                  "sub-agent(s) just created — run `update` to version it with the full roster.")
    elif args.dry_run:
        show("POST /agents (%s)" % name, body)
        rows[name] = ("agent", body["model"]["id"], "TBD", "TBD")
        coord_id, coord_ver = "<dry-run>", 1
    else:
        c = api("/agents", body)
        coord_id, coord_ver = c["id"], c["version"]
        print("CREATED agent %s %s v%s" % (name, coord_id, coord_ver))
        rows[name] = ("agent", body["model"]["id"], coord_id, coord_ver)

    # Record the agent ids BEFORE the deployment POSTs: a failure there used to leave seven
    # created agents whose ids were never written down.
    if not args.dry_run:
        write_cloud(rows)

    legacy = dps.get(LEGACY_DEPLOYMENT_NAME)
    for spec in specs:
        dname, _suffix, cron = spec
        live_depl = dps.get(dname)
        if live_depl is not None:
            print("SKIP deployment %s (live %s, schedule %s) — `update` reconciles it" % (
                dname, live_depl["id"], (live_depl.get("schedule") or {}).get("expression")))
            rows[dname] = ("deployment", None, live_depl["id"], None)
            continue
        if dname == LEGACY_TARGET and legacy is not None:
            # Creating -a beside the legacy cron would double the heartbeat rate on the same
            # coordinator. `update` renames the legacy deployment instead.
            print("SKIP deployment %s: the legacy %s (%s) is live — run `update`, which renames "
                  "it to %s. It is never deleted." % (
                      dname, LEGACY_DEPLOYMENT_NAME, legacy["id"], LEGACY_TARGET))
            continue
        depl = deployment_body(coord_id, coord_ver, cloud, spec, with_token=not args.dry_run)
        if args.dry_run:
            show("POST /deployments (%s)" % dname, depl)
            rows[dname] = ("deployment", None, "TBD", None)
            continue
        d = api("/deployments", depl)
        print("CREATED deployment %s %s (%s UTC)" % (d["name"], d["id"], cron))
        rows[dname] = ("deployment", None, d["id"], None)

    if args.dry_run:
        print("\n(dry run — nothing created, cloud.md untouched; %d deployment(s): %s)"
              % (len(specs), ", ".join(s[0] for s in specs)))
        return
    write_cloud(rows)


def cmd_update(args):
    cloud = read_cloud()
    specs = deployment_specs()
    ags, dps = live_state()
    # Pre-flight: every role must exist live before anything is POSTed or written. A role missed
    # here (rename, API blip, truncated page) used to be `continue`d past BEFORE the roster
    # append, so the coordinator was versioned with a short multiagent.agents list and silently
    # lost a sub-agent — and its row was stamped TBD over a real id in fleet/cloud.md.
    missing = [load_agent(role)[0] for role in ROLES + ["coordinator"]
               if load_agent(role)[0] not in ags]
    if missing:
        for n in missing:
            print("MISSING live agent %s" % n)
        raise SystemExit(
            "aborting update: %d role(s) above are not live. Updating now would version the "
            "coordinator with a truncated roster and overwrite recorded ids. Create the missing "
            "agent(s) first (`create` on an empty account, or by hand), then re-run `update`."
            % len(missing))
    rows = {}
    roster = []
    for role in ROLES + ["coordinator"]:
        name, body = load_agent(role)
        live = ags[name]
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
    legacy = dps.get(LEGACY_DEPLOYMENT_NAME)
    reconciled, missing, no_coord = [], [], []
    for spec in specs:
        dname, _suffix, _cron = spec
        live_depl = dps.get(dname)
        if live_depl is None and dname == LEGACY_TARGET and legacy is not None:
            # The pre-parallelism deployment IS deployment a: same id, new name and cron. Never
            # delete it and never create a second one beside it — that would double the cron.
            print("ADOPTING legacy deployment %s %s as %s (rename + reschedule, same id)"
                  % (LEGACY_DEPLOYMENT_NAME, legacy["id"], dname))
            live_depl = legacy
        if live_depl is None:
            # Do NOT put a row in `rows` for it: write_cloud() then preserves whatever cloud.md
            # already recorded, which is what _deployment_id()/run/status read.
            print("MISSING live deployment %s — run `create` to add it; `update` reconciles "
                  "only what exists" % dname)
            missing.append(dname)
            continue
        if not coord or coord[2] == "TBD":
            print("SKIP deployment %s: no coordinator id" % dname)
            no_coord.append(dname)
            continue
        want = deployment_body(coord[2], coord[3], cloud, spec, with_token=not args.dry_run)
        cmp_want = json.loads(json.dumps(want))
        cmp_want.pop("initial_events", None)
        for r in cmp_want.get("resources") or []:
            if r.get("type") == "github_repository":
                r["authorization_token"] = "<resupply-at-apply>"
        got = norm_depl(live_depl)
        changed = [k for k in cmp_want if got.get(k) != cmp_want.get(k)]
        if not changed:
            print("unchanged deployment %s" % dname)
        else:
            # POST only the differing fields: the update endpoint 400s on full-config bodies
            # (immutable fields), and an agent repoint needs agent.type.
            payload = {k: want[k] for k in changed}
            if "agent" in payload:
                payload["agent"] = {"type": "agent", "id": want["agent"]["id"],
                                    "version": want["agent"]["version"]}
            if args.dry_run:
                show("POST /deployments/%s (%s)" % (live_depl["id"], dname), payload)
            else:
                api("/deployments/%s" % live_depl["id"], payload)
                print("UPDATED deployment %s (%s)" % (dname, ", ".join(changed)))
        rows[dname] = ("deployment", None, live_depl["id"], None)
        reconciled.append(dname)

    print("deployments (%d configured): %s" % (len(specs), "; ".join(
        "%s cron=%s %s" % (n, c, "reconciled" if n in reconciled else
                           ("MISSING — run create" if n in missing else "skipped"))
        for n, _s, c in specs)))

    if not args.dry_run:
        write_cloud(rows)
    # A deployment that simply has not been created yet is a normal partial state while
    # parallelism is being rolled out (b and c added by `create` after a exists) — it is
    # reported, not fatal. Nothing reconciled at all, or a missing coordinator id, still is.
    if no_coord:
        raise SystemExit("update incomplete: no coordinator id for %s" % ", ".join(no_coord))
    if not reconciled:
        raise SystemExit("update incomplete: no deployment was updated (see above) — "
                         "run `create` first")


def _deployment_id(cloud, name, dry_run=False):
    row = cloud["ids"].get(name)
    ident = (row or {}).get("id", "").strip("`")
    if ident and ident != "TBD":
        return ident
    if dry_run:
        return "<%s id not yet in cloud.md — run create>" % name
    _, dps = live_state()
    d = dps.get(name)
    if not d and name == LEGACY_TARGET:
        d = dps.get(LEGACY_DEPLOYMENT_NAME)      # pre-rename account
    if not d:
        raise SystemExit("no deployment %s — run `create` first" % name)
    return d["id"]


def _resolve_name(suffix):
    """`a` or `coworld-builder-a` -> the configured deployment name."""
    specs = deployment_specs()
    by_suffix = {suf: name for name, suf, _ in specs}
    if suffix in by_suffix:
        return by_suffix[suffix]
    if suffix in [name for name, _, _ in specs]:
        return suffix
    raise SystemExit("unknown deployment %r — fleet/deployment.json declares: %s"
                     % (suffix, ", ".join("%s (%s)" % (s, n) for n, s, _ in specs)))


def cmd_run(args):
    name = _resolve_name(args.name)
    dep = _deployment_id(read_cloud(), name, args.dry_run)
    if args.dry_run:
        show("POST /deployments/%s/run (%s)" % (dep, name), {})
        return
    d = api("/deployments/%s/run" % dep, {})
    print("triggered %s -> %s" % (name, json.dumps(redact(d))[:400]))


def cmd_status(args):
    cloud = read_cloud()
    for name, _suffix, cron in deployment_specs():
        try:
            dep = _deployment_id(cloud, name, args.dry_run)
        except SystemExit as e:
            # One deployment that does not exist yet must not hide the others' status.
            print("%s cron=%s — %s" % (name, cron, e))
            continue
        if args.dry_run:
            show("GET /deployment_runs?deployment_id=%s&limit=%d (%s, cron %s)"
                 % (dep, args.limit, name, cron), {})
            continue
        d = api("/deployments/%s" % dep)
        sched = (d.get("schedule") or {}).get("expression")
        print("%s %s status=%s schedule=%s agent=%s v%s" % (
            d.get("name", name), dep, d.get("status"), sched,
            d.get("agent", {}).get("id"), d.get("agent", {}).get("version")))
        if d.get("paused_reason"):
            print("  paused_reason: %s" % d["paused_reason"])
        runs = api("/deployment_runs?deployment_id=%s&limit=%d" % (dep, args.limit))
        for r in ((runs.get("data") or []) if isinstance(runs, dict) else runs)[: args.limit]:
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
    sub.add_parser("create", help="create the missing sub-agents, coordinator, and deployments")
    sub.add_parser("update", help="new agent versions where config differs; reconcile all "
                                  "deployments")
    r = sub.add_parser("run", help="POST /deployments/{id}/run — a manual heartbeat")
    r.add_argument("--name", default="a",
                   help="which heartbeat deployment: a suffix (a/b/c) or the full name")
    s = sub.add_parser("status", help="every deployment's latest runs + session status")
    s.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    {"create": cmd_create, "update": cmd_update, "run": cmd_run, "status": cmd_status}[
        args.cmd](args)


if __name__ == "__main__":
    main()
