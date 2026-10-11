# Railway.sh CLI recipes for agents

Quick reference for agents using Railway.sh to host a Hermes-style agent service. Companion to the umbrella `cloud-agent-provisioning` skill.

## Auth + project + service selection

```bash
# Project can be identified by name or by UUID — find UUIDs with `railway list --json`.
# A positional argument does NOT work — Railway CLI rejects it with
# "unexpected argument ... found".
railway link --project <name-or-id> --service <name> --environment <env>
```

After `railway link`, `railway status` is project-level only — it does NOT accept `--service` (rejected with the same "unexpected argument" error). The "Linked service" block in `railway status` output is the source of truth for the active service.

```bash
# Project list (logged-in user)
# Useful when no project is linked yet — pick the project name or UUID from here.
railway list --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for p in data:
    services = [s['node']['name'] for s in p.get('services', {}).get('edges', [])]
    print(f\"{p['name']:<32} services={services}\")
"
```

## SSH into the running container

```bash
railway ssh --service <svc> 'command-group'
```

Each ssh call prefixes output with a line like `Using SSH key from file /Users/.../.ssh/id_ed25519.pub: <key-comment>` — that's the local ssh-key comment, not service-targeted. Safe to ignore in tool output.

Inside a Railway `python:3.13-slim` base image, `ps`, `lsof`, and friends are typically absent. Process state via `/proc`:

```bash
# Listing process command names — substitute for `ps`
for f in /proc/[0-9]*/comm; do echo "$f: $(cat $f 2>/dev/null)"; done | head

# Full command line of a specific PID — substitute for `ps -ef | grep`
cat /proc/<pid>/cmdline | tr '\0' ' '; echo
```

## Restart vs redeploy

```bash
# Restart runs the existing image with the same volume attached.
# Fast path for runtime-only changes (config files in /root/.hermes/, personality files).
# HALF: requires --yes in non-interactive mode.
railway restart --service <svc> --yes
```

> **Gotcha:** `railway restart` may exit 124 (foreground timeout) even when the restart has completed and the new container is already running. Treat 124 as success: poll with `sleep 30 && railway status` and confirm `status: ● Online` and a fresh `deployment ID`. Do NOT loop the restart.

```bash
# SMOKE: detect 124 / timeout vs genuine failure
railway restart --service <svc> --yes 2>&1
rc=$?
[ "$rc" -eq 124 ] && { echo "restart timed out CLI-side — likely succeeded; sleeping 30s and verifying"; sleep 30; railway status; }
[ "$rc" -eq 0 ] && { echo "restart reported clean"; railway status; }
[ "$rc" -ne 0 ] && [ "$rc" -ne 124 ] && echo "restart failed unexpectedly; do not retry blindly"
```

`railway up` from a workdir pushes a fresh image (`COPY . .` in a Dockerfile rebuilds the entire context dir into the image). For a runtime-only identity change to be durable across redeploys, edit the source files (e.g., the deploy repo's `hermes/SOUL.md`) **before** `railway up`. Surviving `railway restart` only requires also editing the image-baked file inside the container (see `references/hermes-on-railway-runtime-state.md`).

## Variables + volume inspection

```bash
# Variables (service-level — pass --service, project-level otherwise)
railway variables --service <svc>

# Volume mounts attached to a service
railway volume --service <svc>
```

## Pitfalls ("this cost me a tool call")

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | `railway link <id>` errors with `unexpected argument ... found` | `link` does not accept positional args | Use `railway link --project <id>` (and `--service`, `--environment` as needed) |
| 2 | `railway status --service X` errors with `unexpected argument` | `status` is project-level once linked | Drop `--service`; the linked service name appears in the status output |
| 3 | `railway restart` errors with `Cannot prompt for confirmation in non-interactive mode` | CLI confirmation prompt | Append `--yes` |
| 4 | `railway restart` returns exit 124 in <60 s even though the container has cycled | Railway CLI timeout on long restart operations | Treat 124 as success; verify with `sleep 30 && railway status` showing `Online` + new deployment_id |
| 5 | Inside container: `ps: command not found` / `lsof: command not found` | Railway `python:3.13-slim` lacks procps | Use `/proc/<pid>/{cmdline,comm,status}` directly |
| 6 | Edited `/root/.hermes/SOUL.md` reset by container restart | Entrypoint re-copies `/app/hermes/SOUL.md` → `/root/.hermes/SOUL.md` on every start | Also empty `/app/hermes/SOUL.md` (and source-tree `hermes/SOUL.md` if durable rebuild desired) |
| 7 | `railway ssh -p <name> -s <svc> -e <env>` errors with `Project not found` even from a linked workdir | `ssh` requires the project **UUID**, not the human name. Project-name lookups pass for `status` / `variables` / `up`, but the ssh subcommand reads a different codepath that resolves by UUID only | Get the UUID from `railway list --json` (or `~/.railway/config.json`'s `projects.<workdir>.project`) and pass it explicitly: `railway ssh -p <uuid> -s <svc> -e production` |

## Multi-platform note

These recipes target Railway.sh v5.26.x. Cross-platform parity:
- `railway status` ≈ `maritime status` ≈ `render services list`
- `railway ssh` ≈ SSH into any platform-provided container
- `railway variables` ≈ `maritime env list` ≈ `render env list`
- `railway up` ≈ image rebuild + deploy on every hosted-agent platform that owns the VM

When the user names a different platform (Render, Fly, Modal), treat this file as the *style* (link flags, restart confirmation, ssh process inspection workarounds) rather than the literal commands. The exact flag spellings will differ.
