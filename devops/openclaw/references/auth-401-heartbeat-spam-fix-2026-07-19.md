# OpenClaw Auth 401 → Heartbeat/Cron Spam Fix

Session: 2026-07-19
Symptom: Telegram DM from `🎯 Kriya` every ~30 min: `⚠️ Heartbeat check failed before it could produce an update.`
Root cause: stale Venice API key in `~/.openclaw/auth-profiles.json`, plus per-agent SQLite auth stores not synced.

## Diagnostic log signature

Gateway log (`/tmp/openclaw/openclaw-2026-07-18.log`):

```
FailoverError: 401 "Authentication failed"
traceId: 5e40c751f1549fef0cebcd7451256407
lanes: main, session:agent:main:cron:7fd8a726-...:run:*
```

Cron state (`~/.openclaw/state/openclaw.sqlite` `cron_jobs` table) showed:
- `last_run_status: error`
- `last_error: FallbackSummaryError: All models failed (4): venice/...: 401 "Authentication failed" ...`
- `consecutive_errors: 1`

## What was wrong

| File | Key | Status |
|------|-----|--------|
| `~/.hermes/config.yaml` | `VENICE_INFERENCE_KEY_LbAZyawSbfq7U08rJvE7LIiEBeavWmZSoKulQeRQDY` | valid, current |
| `~/.openclaw/openclaw.json` | `VENICE_INFERENCE_KEY_LbAZyaw...` | valid, current |
| `~/.openclaw/auth-profiles.json` | `VENICE_INFERENCE_KEY_g9lMRHQtrPlonwmkZO9l81SiYCZfPN3QmxCR0Z-usc` | **stale** |
| `~/.openclaw/agents/main/agent/openclaw-agent.sqlite` | empty `auth_profile_store` | missing |
| `~/.openclaw/agents/kriya/agent/openclaw-agent.sqlite` | empty/no auth table | missing |

The per-agent SQLite auth stores were not populated, so the gateway fell back to `auth-profiles.json`, which held an old key. Even after fixing `main`, the named `kriya` agent continued to fail because its own SQLite store was still empty.

## Fix applied

```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use 24
NEW_KEY=$(grep -oP 'VENICE_INFERENCE_KEY_[A-Za-z0-9_-]+' ~/.openclaw/openclaw.json | head -1)

python3 - <<'PY'
import json, os, sqlite3, time
new_key = os.environ['NEW_KEY']
base = os.path.expanduser('~/.openclaw')

# Update legacy/shared auth-profiles.json
p = os.path.join(base, 'auth-profiles.json')
if os.path.exists(p):
    with open(p) as f: d = json.load(f)
    d.setdefault('profiles', {})
    for pid in ['venice:default', 'venice:manual']:
        d['profiles'][pid] = {'type': 'api_key', 'provider': 'venice', 'key': new_key}
    with open(p, 'w') as f: json.dump(d, f, indent=2)
    print('updated auth-profiles.json')

# Update every per-agent SQLite auth store
for agent_dir in ['agents/main/agent', 'agents/kriya/agent']:
    db = os.path.join(base, agent_dir, 'openclaw-agent.sqlite')
    if not os.path.exists(db):
        print(f'skipping {db}')
        continue
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS auth_profile_store (
        store_key TEXT PRIMARY KEY, store_json TEXT NOT NULL, updated_at INTEGER NOT NULL)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS auth_profile_state (
        state_key TEXT PRIMARY KEY, state_json TEXT NOT NULL, updated_at INTEGER NOT NULL)''')
    now = int(time.time() * 1000)
    store = {'version': 1, 'profiles': {
        'venice:default': {'type': 'api_key', 'provider': 'venice', 'key': new_key},
        'venice:manual':  {'type': 'api_key', 'provider': 'venice', 'key': new_key}
    }}
    cur.execute("INSERT OR REPLACE INTO auth_profile_store VALUES (?,?,?)",
                ('primary', json.dumps(store), now))
    state = {'version': 1, 'lastGood': {}, 'usageStats': {}}
    cur.execute("INSERT OR REPLACE INTO auth_profile_state VALUES (?,?,?)",
                ('primary', json.dumps(state), now))
    conn.commit()
    conn.close()
    print(f'updated {db}')
PY

systemctl --user restart openclaw-gateway.service
sleep 5 && curl -s http://127.0.0.1:18789/health
# → {"ok":true,"status":"live"}

# Verify both agents and run a Kriya smoke test
openclaw models status
openclaw models status --agent kriya
openclaw agent --agent kriya --local --message "pong"
# → provider HTTP 200, response returned
```

## Key takeaways

- When every Venice model fails with `401 Authentication failed` across the entire fallback chain, the issue is a stale/missing provider key — not bad models.
- `~/.openclaw/openclaw.json` and `~/.openclaw/auth-profiles.json` can hold different keys. The gateway may use the latter.
- v2026.6.x+ stores auth per-agent in `~/.openclaw/agents/<name>/agent/openclaw-agent.sqlite`. Fixing `main` does **not** fix `kriya`.
- Always verify named agents independently with `openclaw models status --agent <name>` and a real agent turn.
