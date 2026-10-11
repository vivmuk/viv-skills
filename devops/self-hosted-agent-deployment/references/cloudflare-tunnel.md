# Cloudflare Tunnel — secure ingress without opening ports

Recipe for putting a personal agent behind a Cloudflare-managed
hostname without exposing the agent's HTTP port to the public
internet.

## Why this over opening ports

- **Free tier**: unlimited tunnels.
- **No inbound firewall rules needed** — only SSH on the VM.
- **Identity / auth**: Cloudflare Access can add OIDC-style auth
  on top without rebuilding your agent.
- **DNS is one CNAME**: `agent.example.com → <UUID>.cfargotunnel.com`.

## One-time setup (on the VM)

```bash
# Install (Ubuntu / Debian ARM)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb \
     -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Authenticate (opens browser, applies cert.pem to ~/.cloudflared/)
cloudflared tunnel login

# Create the tunnel (writes ~/.cloudflared/<UUID>.json)
cloudflared tunnel create my-agent

# Copy the credentials into your deploy dir
mkdir -p ./tunnel
cp ~/.cloudflared/<UUID>.json ./tunnel/credentials.json
chmod 600 ./tunnel/credentials.json
```

In Cloudflare DNS console for a domain you already manage, add a
**CNAME**: `<TUNNEL_HOSTNAME>` → `<UUID>.cfargotunnel.com`. (Cloudflare
auto-detects this if you `cloudflared tunnel route dns` instead.)

Update `.env` to plug the UUID + hostname into Compose:

```
TUNNEL_ID=<UUID>
TUNNEL_HOSTNAME=agent.example.com
```

## config.yml (mounted into the cloudflared container)

```yaml
tunnel: ${TUNNEL_ID}
credentials-file: /etc/cloudflared/credentials.json

originRequest:
  connectTimeout: 30s
  keepAliveConnections: 4
  keepAliveTimeout: 90s
  httpHostHeader: ${TUNNEL_HOSTNAME}

ingress:
  - hostname: ${TUNNEL_HOSTNAME}
    path: /health
    service: http_status:200           # public probe, no upstream
  - hostname: ${TUNNEL_HOSTNAME}
    service: http://<agent-service>:8642
  - service: http_status:404            # mandatory catch-all
```

Pitfall: the `path: /health` rule returns 200 directly from the
tunnel daemon without contacting the upstream. This means your
uptime monitor sees "always 200" even when the agent is down.
**Either** remove that rule, or split health into `/health`
(upstream) and `/livez` (tunnel). For Hermes specifically, the
agent exposes `/health` and `/health/detailed` — leave the
ingress unmatched and let public `/health` always 200.

## Compose fragment

```yaml
tunnel:
  image: cloudflare/cloudflared:latest
  container_name: tunnel
  restart: unless-stopped
  depends_on:
    agent:
      condition: service_healthy
  volumes:
    - ./tunnel:/etc/cloudflared:ro
  networks: [internal]
  command: ["tunnel", "--config", "/etc/cloudflared/config.yml", "run"]
```

## Verify

```bash
# On the VM
docker compose logs --tail=20 tunnel
# Look for: "Registered tunnel connection" repeating.

# From anywhere
curl -fsS https://${TUNNEL_HOSTNAME}/health
```

If `curl` 404s, check the DNS CNAME is resolving to
`<UUID>.cfargotunnel.com`. If `curl` 502/503, check the agent
service is up and listening on 8642.

## Recovery after VM rebuild

Credentials file lives at `~/.cloudflared/<UUID>.json` — back this
up. After VM rebuild: re-install cloudflared, copy back the file,
re-run `docker compose up -d tunnel`. The DNS CNAME doesn't need
to change.

## See also

- `templates/cloudflared-config.yml` — full template
- `scripts/healthcheck.sh` — combined VM-local + tunnel-public probe
