#!/usr/bin/env python3
"""
wire-venice-key.py — bind VENICE_API_KEY into every agent's adapterConfig.env.

Use cases:
  - Initial setup: paperclip server is up but no agent has VENICE_API_KEY.
  - Key rotation: the old VENICE_API_KEY in .env was replaced; agents need PATCH.
  - New company: agents were created without Venice; re-wire in one shot.

Reads VENICE_API_KEY from ~/.paperclip/instances/default/.env (set by the user
or by `paperclipai configure`). Falls back to the user's shell env. PATCHes
each agent via the Paperclip REST API. Idempotent: skips agents that already
have VENICE_API_KEY in adapterConfig.env.

Also injects VENICE_MODEL (default: nvidia-nemotron-3-ultra-550b-a55b) and
VENICE_API_BASE (default: https://api.venice.ai/api/v1) if not present.

Usage:
  python3 wire-venice-key.py                       # use defaults
  python3 wire-venice-key.py --company-id <uuid>   # different company
  python3 wire-venice-key.py --api-base <url>      # different paperclip host
  python3 wire-venice-key.py --key <VENICE...xx>   # override the key explicitly
  python3 wire-venice-key.py --dry-run             # just report status, no PATCH
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_API = "http://127.0.0.1:3100"
DEFAULT_ENV = "/Users/vivgatesai/.paperclip/instances/default/.env"
DEFAULT_MODEL = "nvidia-nemotron-3-ultra-550b-a55b"
DEFAULT_BASE = "https://api.venice.ai/api/v1"


def load_key_from_env_file(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        for line in f:
            if line.startswith("VENICE_API_KEY=***                return line.strip().split("=", 1)[1]
    return None


def patch_agent(api, company, agent_id, cfg, key, model, base):
    env = dict(cfg.get("env", {}))
    changed = False
    if "VENICE_API_KEY" not in env:
        env["VENICE_API_KEY"] = {"type": "plain", "value": key}
        changed = True
    if "VENICE_MODEL" not in env:
        env["VENICE_MODEL"] = {"type": "plain", "value": model}
        changed = True
    if "VENICE_API_BASE" not in env:
        env["VENICE_API_BASE"] = {"type": "plain", "value": base}
        changed = True
    if not changed:
        return True, "already-wired"
    new_cfg = {**cfg, "env": env}
    body = json.dumps({"adapterConfig": new_cfg}).encode()
    req = urllib.request.Request(
        f"{api}/api/agents/{agent_id}",
        data=body,
        method="PATCH",
        headers={"Content-Type": "application/json", "Company-Id": company},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status == 200, f"PATCH {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"PATCH {e.code}: {e.read().decode()[:200]}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--api-base", default=DEFAULT_API, help="Paperclip API base URL")
    p.add_argument("--company-id", default=os.environ.get("PAPERCLIP_COMPANY_ID"),
                   help="Company UUID (or set PAPERCLIP_COMPANY_ID)")
    p.add_argument("--env-file", default=DEFAULT_ENV, help="Path to Paperclip instance .env")
    p.add_argument("--key", help="Override VENICE_API_KEY (otherwise read from .env)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--venice-base", default=DEFAULT_BASE, dest="venice_base",
                   help="Venice API base URL (stored as VENICE_API_BASE)")
    p.add_argument("--dry-run", action="store_true", help="List agents and exit, no PATCH")
    args = p.parse_args()

    if not args.company_id:
        ctx = os.path.expanduser("~/.paperclip/context.json")
        if os.path.exists(ctx):
            try:
                with open(ctx) as f:
                    cid = json.load(f).get("profiles", {}).get("default", {}).get("companyId")
                if cid:
                    args.company_id = cid
            except Exception:
                pass
    if not args.company_id:
        print("ERROR: --company-id required (or set PAPERCLIP_COMPANY_ID)", file=sys.stderr)
        return 2

    key = args.key or os.environ.get("VENICE_API_KEY") or load_key_from_env_file(args.env_file)
    if not key:
        print(f"ERROR: VENICE_API_KEY not found. Set --key, export it, or write to {args.env_file}",
              file=sys.stderr)
        return 2
    if not key.startswith("VENICE_"):
        print(f"WARNING: key does not start with 'VENICE_' — proceeding anyway ({len(key)} chars)")

    req = urllib.request.Request(f"{args.api_base}/api/companies/{args.company_id}/agents")
    try:
        agents = json.loads(urllib.request.urlopen(req, timeout=10).read())
    except urllib.error.HTTPError as e:
        print(f"ERROR: list agents failed: {e.code} {e.read().decode()[:200]}", file=sys.stderr)
        return 1
    agents = agents if isinstance(agents, list) else agents.get("agents", [])
    print(f"Found {len(agents)} agents in company {args.company_id}")

    if args.dry_run:
        for a in agents:
            env = (a.get("adapterConfig") or {}).get("env", {})
            has = "VENICE_API_KEY" in env
            print(f"  {'OK ' if has else 'NO '} {a.get('name'):25} (id {a.get('id')[:8]})")
        return 0

    ok = skip = fail = 0
    for a in agents:
        aid = a["id"]
        name = a.get("name", "?")
        cfg = a.get("adapterConfig") or {}
        if not cfg:
            print(f"  {name:25} SKIP — no adapterConfig")
            skip += 1
            continue
        success, msg = patch_agent(args.api_base, args.company_id, aid, cfg, key,
                                   args.model, args.venice_base)
        flag = "  OK" if success else "FAIL"
        print(f"  {flag} {name:25} {msg}")
        if success and msg == "already-wired":
            skip += 1
        elif success:
            ok += 1
        else:
            fail += 1

    print(f"\nDone: {ok} patched, {skip} already wired, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
