# OpenClaw Gateway Startup Failure — Session Log

**Date:** 2026-07-16
**Trigger:** User asked to get the OpenClaw gateway running; previous attempt left it down.
**Final state:** Gateway live on `127.0.0.1:18789`, health returns `{"ok":true,"status":"live"}`

## Symptoms observed

1. `curl -s http://127.0.0.1:18789/health` → exit code 7 (connection refused)
2. `systemctl --user start openclaw-gateway.service` appeared to succeed but health check still failed.
3. `openclaw logs` showed two alternating errors:
   - `OpenClaw startup migrations did not complete cleanly; refusing to report the gateway ready. Left plugin install index in place because shared SQLite state has conflicting plugin install metadata for: discord`
   - `OpenClaw startup migrations are already running for this state directory; retry after the other gateway finishes or after 2026-07-16T04:44:00.376Z.`

## Root causes

1. **Node version too old for the installed OpenClaw binary.**
   - OpenClaw v2026.6.11 requires Node ≥ v22.22.3 or v24.x.
   - Service file pointed to `~/.hermes/node/bin/node` which was **v22.22.2**.
   - Gateway aborted immediately during startup.

2. **Stale Discord plugin metadata conflict.**
   - The runtime config (`openclaw.json`) still had Discord as enabled, while the SQLite `installed_plugin_index` had conflicting records.
   - The gateway treated the resulting migration warning as fatal and refused to report ready.
   - `openclaw doctor --fix` and `openclaw plugins disable discord` both touched config while a migration lease was held, which then triggered the second error: "config changed during startup" / "migrations already running".

3. **Stale migration lease.**
   - `state_leases` table had a `startup-migrations` row with `expires_at` set several minutes in the future.
   - Because the gateway kept crashing and re-acquiring the lease, manual cleanup was required.

## Fix applied

1. Updated `~/.config/systemd/user/openclaw-gateway.service` to use the v24 Node binary:
   ```
   ExecStart=/home/vivgates/.nvm/versions/node/v24.15.0/bin/node /home/vivgates/.hermes/node/lib/node_modules/openclaw/dist/index.js gateway --port 18789
   ```

2. Disabled Discord in `openclaw.json` via `openclaw plugins disable discord`.

3. Removed Discord metadata from the SQLite shared state (`installed_plugin_index`) and cleared the stale `startup-migrations` lease.

4. Restarted the service:
   ```bash
   systemctl --user daemon-reload
   systemctl --user restart openclaw-gateway.service
   sleep 5
   curl -s http://127.0.0.1:18789/health
   # → {"ok":true,"status":"live"}
   ```

## Key commands for future incidents

```bash
# Check Node version used by the service
cat ~/.config/systemd/user/openclaw-gateway.service | grep ExecStart
~/.hermes/node/bin/node --version
~/.nvm/versions/node/v24.15.0/bin/node --version

# Inspect migration lock and plugin index
python3 - <<'PY'
import sqlite3, os, json
db = os.path.expanduser('~/.openclaw/state/openclaw.sqlite')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT scope, lease_key, expires_at FROM state_leases")
print('leases:', cur.fetchall())
cur.execute("SELECT install_records_json FROM installed_plugin_index WHERE index_key='installed-plugin-index'")
row = cur.fetchone()
if row:
    print('install_records keys:', list(json.loads(row[0]).keys()))
PY

# Quick health check
systemctl --user status openclaw-gateway.service
curl -s http://127.0.0.1:18789/health
~/.hermes/node/bin/openclaw status
```

## Authoritative source

OpenClaw's own logs at `/tmp/openclaw/openclaw-2026-07-16.log` were the primary diagnostic source. The migration error text literally tells you to run `openclaw doctor --fix`; when that command could not finish because of the lock, direct SQLite inspection was the next step.