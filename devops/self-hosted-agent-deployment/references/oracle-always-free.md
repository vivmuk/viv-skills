# Oracle Cloud Always Free — VM tier for personal agents

Concrete recipe (June 2026, validated). Use this when "Always Free
eligible" is a hard requirement. For other clouds see
`references/<cloud>.md` (add yours via `skill_manage write_file`).

## Why Oracle for $0/mo

- Always Free Arm A1.Flex: 4 OCPU + 24 GB RAM, 200 GB block
  storage, 10 TB egress/month. **Forever free**, not a 12-month
  promo.
- Same shape available on x86 (`VM.Standard.E2.1.Micro`: 1 OCPU +
  1 GB) if you need x86 for some reason (Dockerfile rebuilt for
  glibc mismatch etc.).
- Egress budget is enough for a Telegram bot + a Cloudflare
  tunnel bootstrapping — typical agent traffic ~1 GB/month.

## Pitfalls

- **Region choice is sticky.** Always Free VMs live in a single
  region. If Oracle retires that region, **snapshot → restore** to
  another region (~30 min downtime). Pick a region with good
  Always Free capacity at signup (`--region us-ashburn-1` etc.).
- **Outbound HTTP is permitted by default.** Inbound SSH only.
  Cloudflare Tunnel works because the tunnel daemon initiates the
  outbound connection — no inline firewall changes needed.
- **No ARM emulation for x86-only Docker images.** Most agent
  Dockerfiles are AMD64; on Ampere ARM, multi-arch images work,
  pure x86 images do not. The Dockerfile shipped with upstream
  Hermes Agent is multi-arch (`debian:13.4` works on both).
- **Ephemeral public IP** — convert to a **reserved public IP**
  before SSH-from-laptop workflow starts, otherwise your IP
  changes on every reboot and you have to rediscover it via the
  OCI console.

## Bootstrap (after VM is up)

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install curl unzip git docker.io
sudo usermod -aG docker $USER
newgrp docker                       # or log out/in
sudo systemctl enable --now docker
sudo apt -y install docker-compose-plugin
docker compose version              # confirm 2.x
```

`HERMES_UID` in the Compose env should equal the host user's UID
(1000 for the default `ubuntu` user). The Compose stage2 hook
remaps the in-container non-root user to that UID so volumes stay
owned correctly.

## SSH hardening (recommended but not required)

- Disable password auth: `sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config`
- Add `fail2ban` if you expose SSH publicly.

## References

- Oracle Always Free shape list: https://www.oracle.com/cloud/free/
- A1.Flex capacity is shared across a tenancy. If quota is exhausted
  in your home region, try the next region over.
