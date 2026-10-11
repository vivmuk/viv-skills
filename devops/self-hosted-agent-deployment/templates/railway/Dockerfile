# syntax=docker/dockerfile:1.7
# Railway-side Dockerfile for a Hermes-style personal agent.
# Design choices (see ../references/railway.md for the full rationale):
#   - python:3.13-slim base matches hermes-agent wheels
#   - tini as PID 1 reaps zombie MCP stdio subprocesses (gotcha #16)
#   - pre-install any stdio MCP packages at build time (gotcha #8);
#     `npx -y @<pkg>` cold-starts can hang silently in Railway
#   - EXPOSE 8642 (Hermes API server's default per
#     hermes_cli/service_manager.py:656; override with API_SERVER_PORT)
#   - ENTRYPOINT goes through tini → entrypoint.sh — DO NOT set
#     startCommand in railway.json (gotcha #17)

FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl bash git nodejs npm build-essential tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Install hermes-agent. Pin via HERMES_VERSION build arg if you need
# reproducibility; omit it for latest release.
ARG HERMES_VERSION=
RUN if [ -n "${HERMES_VERSION}" ]; then \
        pip install --no-cache-dir "hermes-agent==${HERMES_VERSION}"; \
    else \
        pip install --no-cache-dir hermes-agent; \
    fi

# Pre-install any stdio MCP servers you depend on so `npx` finds them
# locally at runtime. Add one RUN line per server.
# RUN npm install -g @notionhq/notion-mcp-server

ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

# Sanity check — verify install succeeded
RUN hermes --version || (echo "hermes install failed" && exit 1)

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8642

ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/entrypoint.sh"]
