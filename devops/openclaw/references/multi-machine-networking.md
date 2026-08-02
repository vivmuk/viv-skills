# Multi-Machine Agent Networking

Connecting Hermes and OpenClaw agents across multiple home computers (Linux/WSL, macOS, Windows).

## Recommended Architecture: Tailscale + MCP

### Step 1: Tailscale Mesh VPN

Tailscale gives each machine a stable `100.x.x.x` IP reachable from any other machine, even remotely. Zero-config NAT traversal.

**Install on each machine:**
```bash
# Linux / WSL
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# macOS
brew install tailscale
# or App Store — Tailscale app

# Windows
# Download from tailscale.com, or winget install Tailscale.Tailscale
```

After `tailscale up` on all machines, each gets a stable IP. Verify:
```bash
tailscale status  # shows all connected machines and their IPs
ping 100.x.x.x   # test connectivity
```

**WSL note**: Run Tailscale inside WSL (not Windows) if the Hermes/OpenClaw gateway runs in WSL. Alternatively, run Tailscale on Windows and use the Windows Tailscale IP from WSL via port forwarding.

### Step 2: Hermes MCP Server ↔ Client

Each Hermes instance exposes its tools via MCP so other machines can call them.

**On each machine**, start Hermes as an MCP server:
```bash
hermes mcp serve --port 8900
```

**On each other machine**, register the remote Hermes:
```bash
# On PC-2, connect to PC-1's Hermes (100.x.x.x from Tailscale)
hermes mcp add pc1-hermes --url http://100.x.x.x:8900

# On Mac, connect to PC-1
hermes mcp add pc1-hermes --url http://100.x.x.x:8900

# On PC-1, connect to PC-2 and Mac
hermes mcp add pc2-hermes --url http://100.x.x.x:8900
hermes mcp add mac-hermes --url http://100.x.x.x:8900
```

Result: cross-machine tool calling. When you ask Hermes on PC-2 to do something, it can delegate to PC-1's tools directly.

### Step 3: OpenClaw Gateway as Hub (Optional)

If one machine has more compute, run OpenClaw as the central agent hub:

```bash
# On the hub machine — expose to Tailscale network (not 0.0.0.0 unless you want LAN access too)
openclaw gateway --port 18789 --host 0.0.0.0
```

From any other machine:
```bash
openclaw agent --message "Build me a FastAPI auth service" --gateway http://100.x.x.x:18789
```

### Step 4: Shared Messaging Channel (Simplest)

All agents join the same Telegram group or Discord channel. No networking config needed — just configure each agent with its own bot token (or different bots in the same group). Agents discover each other through messages.

## Firewall Notes

- Tailscale handles NAT traversal — no port forwarding needed
- On Linux, ensure the firewall allows Tailscale traffic (usually automatic)
- WSL2: Tailscale runs inside WSL, so the WSL instance gets its own Tailscale IP
- macOS: Tailscale app runs natively, handles everything

## Full Mesh Topology

```
┌──────────────────────────────────────────┐
│         Tailscale mesh (100.x.x.x)       │
│                                          │
│  PC-1 (WSL)     PC-2 (WSL)     Mac       │
│  ┌─────────┐    ┌─────────┐   ┌────────┐ │
│  │ Hermes  │◄──►│ Hermes  │◄──►│ Hermes │ │
│  │ :8900   │    │ :8900   │   │ :8900  │ │
│  │         │    │         │   │        │ │
│  │OpenClaw │    │OpenClaw │   │OpenClaw│ │
│  │ :18789  │    │ :18789  │   │:18789  │ │
│  └─────────┘    └─────────┘   └────────┘ │
└──────────────────────────────────────────┘
```

Each machine:
1. Tailscale for networking (30 min one-time setup)
2. `hermes mcp serve` to expose tools
3. `hermes mcp add` to discover other machines
4. Each Hermes keeps its own Telegram connection for user interaction
