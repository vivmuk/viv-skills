# Neon Postgres — managed free-tier Postgres for personal agents

Recipe for using Neon free tier as the operational-state store
(separate from the agent's primary memory, which stays on the host
volume).

## Why Neon for $0/mo

- Free tier: 1919 MB-hours storage + 0.5 GB.
- Postgres 16, with branchable databases (git-style) for testing
  agent changes against a Postgres fork.
- SSL by default — connection strings end in `?sslmode=require`.
- No networking to set up; the connection string Just Works from
  any cloud VM.

## When to use Neon vs volume-mounted Postgres

- **Use Neon** when: the data is operational (logs, task state,
  events) and you'd benefit from querying it from anywhere other
  than the agent host.
- **Use a volume-mounted SQLite or local Postgres** when: the data
  is the agent's primary recall / conversation log and you want
  zero-latency local reads.

**Do not** use Neon as the agent's primary memory store unless
the agent natively supports Postgres. Most agents have their own
embed-friendly local store (Hermes = SQLite at `/opt/data/
state.db`; Codex = `~/.codex/sessions/`; OpenClaw =
`~/.openclaw/state.db`). Rewriting memory for Postgres is a
multi-week project; defer.

## Connection string

`postgresql://USER:***@HOST/DB?sslmode=require`. The `sslmode=require`
suffix is mandatory; without it, Neon rejects the connection.

## Schema example for an operational-event sidecar

```sql
CREATE TABLE IF NOT EXISTS agent_events (
  id          BIGSERIAL PRIMARY KEY,
  ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
  level       TEXT NOT NULL,
  service     TEXT,
  message     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS agent_events_ts_idx ON agent_events(ts DESC);
```

This powers the optional `neon-logger.js` sidecar in
`scripts/neon-logger.js` — poll the agent's stdout/file log every
5s, batch-INSERT new lines.

## Reconciling log rotation

If the agent rotates its log file (rename + new file), the
sidecar must reset its read offset. Pattern: stat the file each
poll; if the inode changed, reset offset to 0 and start from the
top of the new file.

## See also

- `references/secrets-management.md` — how to wire `DATABASE_URL`
  into `.env` and keep it `chmod 600`.
- `scripts/neon-logger.js` — opt-in sidecar (5s poll loop,
  Postgres batch INSERT).
