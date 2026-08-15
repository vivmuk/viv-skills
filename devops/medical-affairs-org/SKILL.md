---
name: medical-affairs-org
description: Deploy a Medical Affairs AI org on Railway (kanban+dashboard).
---

# Medical Affairs AI Organization — Railway deployment

A complete, always-on Medical Affairs function reimagined for AI: one Railway
service running the **official** `nousresearch/hermes-agent` image, with a
`grok-4-6` orchestrator profile + 8 `deepseek-v4-flash-0731-fast` worker
profiles routed through Hermes' in-gateway **kanban dispatcher**, a web
dashboard (basic auth), Telegram, and 46 external skills (26 Medical Affairs +
20 Venice).

Worked example: **Dhyan** (`@DhyanAIbot`, `https://dhyan-production.up.railway.app`).

## Why the OFFICIAL image (not the custom tini Dockerfile)

The `jiva-telegram-deploy` fleet uses a custom `python:3.13-slim` + tini
Dockerfile. For a **multi-profile + dashboard** org, use the official image
instead — it already ships:

- s6-overlay supervision for **gateway + dashboard + per-profile gateways**
- skills sync (`tools/skills_sync.py` — category-based bundled skills)
- first-boot config seeding (`stage2-hook.sh` seeds `config.yaml`, `SOUL.md`, `.env`)
- `/opt/data` volume layout (NOT `/root/.hermes`)

So the derived image only layers in org-specific content. No `entrypoint.sh`, no
`tini`, no manual dashboard supervision.

## Architecture

```
Dhyan (default profile, grok-4-6)  ← kanban orchestrator + Telegram + dashboard
   │  decompose + route (kanban_create, parents=[...])
   ▼
8 worker profiles (deepseek-v4-flash-0731-fast), spawned on-demand by dispatcher
   literaturereview · evidencesynthesis · citationverifier · medicalinformation
   competitiveintel · kolengagement · content · medicalstrategy
```

- **One-level-deep** (orchestrator → workers, no nesting): `delegation.max_spawn_depth: 1`.
- **Vision fallback** `openai-gpt-56-luna` · **image** `grok-imagine-image-2-0` · **video** `ltx-2-5-pro-*`.
- Kanban dispatcher runs in-gateway (`kanban.dispatch_in_gateway: true`).

## Prerequisites

- Railway CLI logged in (`railway whoami`).
- Fresh Venice inference key (own key, not shared with siblings).
- Fresh Telegram bot token via @BotFather (one token = one poller).
- The two skill repos (both standard `SKILL.md` format, Hermes-compatible):
  - `Open-Medical-Affairs-AI/Medical-Affairs-Skills` — **branch `claude/medical-affairs-agent-workshop-ttpxhf`** (NOT main)
  - `veniceai/skills` — branch `main`

## Build steps

### 1. Scaffold + clone skills

```bash
mkdir -p ~/tmp/<org>-deploy/{hermes,profiles,skills,docker}
cd ~/tmp/<org>-deploy
git clone --depth 1 --branch claude/medical-affairs-agent-workshop-ttpxhf \
  https://github.com/Open-Medical-Affairs-AI/Medical-Affairs-Skills.git skills-src/Medical-Affairs-Skills
git clone --depth 1 https://github.com/veniceai/skills.git skills-src/venice-skills
```

Stage skills into **category layout** (bundled skills are `skills/<category>/<name>/SKILL.md`):

```bash
cp -R skills-src/Medical-Affairs-Skills/skills/* skills/medical-affairs/
cp -R skills-src/venice-skills/skills/* skills/venice/
cp -R skills-src/Medical-Affairs-Skills/house-rules skills/medical-affairs/_house-rules
cp -R skills-src/Medical-Affairs-Skills/shared skills/medical-affairs/_shared
```

The MA repo's `AGENTS.md` defines a **six-stage contract** (ORIENT → INVENTORY →
RETRIEVE → ANALYSE → CHALLENGE → DELIVER) and **4 always-load foundation skills**
(`medical-affairs-foundations`, `evidence-appraisal`, `citation-integrity`,
`deliverable-quality-review`) — bake these into EVERY worker's SOUL, not just one.

### 2. Dockerfile (the critical `CMD` fix)

```dockerfile
FROM nousresearch/hermes-agent:latest
COPY hermes/cli-config.yaml /opt/hermes/cli-config.yaml.example   # seeds config.yaml
COPY hermes/SOUL.md /opt/hermes/docker/SOUL.md                    # seeds SOUL.md
COPY skills/ /opt/hermes/skills/                                  # merges into bundled tree
COPY profiles/ /opt/hermes/profiles-seed/
COPY docker/03-<org>-profiles /etc/cont-init.d/03-<org>-profiles
RUN chmod 755 /etc/cont-init.d/03-<org>-profiles
CMD ["gateway", "run"]   # ← REQUIRED (see gotcha #1)
```

### 3. Orchestrator config (`hermes/cli-config.yaml`)

`model.default` = orchestrator model, `provider: custom`,
`base_url: https://api.venice.ai/api/v1`, **omit `api_key`** (resolved from
`OPENAI_API_KEY`/`VENICE_API_KEY` Railway env). Add `kanban.dispatch_in_gateway: true`,
`delegation.max_spawn_depth: 1`, `agent.api_max_retries: 3`.

### 4. Worker profiles (`profiles/<name>/{config.yaml,SOUL.md}`)

Each worker: `model.default: deepseek-v4-flash-0731-fast`, `provider: custom`,
venice `base_url`. SOUL.md carries the worker's scope + skill list + the MA
contract. **All skills sync to all workers** (bundle-everything, scope-via-SOUL);
physical per-worker skill separation is a later optimization.

### 5. cont-init script (`docker/03-<org>-profiles`)

Runs after stage2-hook + reconcile-profiles. For each worker:
`hermes profile create <name> --no-alias --description "..."` (guarded by
existence), then overwrite `config.yaml` + `SOUL.md`, then copy bundled skills
into the profile's `skills/`. Drop to `hermes` user via `s6-setuidgid`.

### 6. Railway setup

```bash
cd ~/tmp/<org>-deploy
railway init --name <org> --workspace "vivmuk's Projects"
railway add --service <org>
railway link -p <project-id> -s <org>
railway volume add --mount-path /opt/data      # NOT /root/.hermes
railway domain --port 9119                     # dashboard port
```

### 7. Env vars (Railway → Variables)

```env
OPENAI_API_KEY=*** Venice key        VENICE_API_KEY=*** same
TELEGRAM_BOT_TOKEN=***               TELEGRAM_ALLOWED_USERS=6808691714
TELEGRAM_HOME_CHANNEL=6808691714     TELEGRAM_FALLBACK_IPS=149.154.166.110,149.154.167.220
HERMES_GATEWAY_BOOTSTRAP_STATE=running
HERMES_DASHBOARD=1                   HERMES_DASHBOARD_HOST=0.0.0.0
HERMES_DASHBOARD_PORT=9119           HERMES_DASHBOARD_BASIC_AUTH_USERNAME=***
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=***   HERMES_DASHBOARD_BASIC_AUTH_SECRET=*** (openssl rand -base64 32)
```

### 8. Deploy + verify

```bash
railway up --service <org> --detach
curl -s https://<org>-production.up.railway.app/api/status
# expect: gateway_running:true, telegram connected, auth_required:true,
#         profiles: [default, <8 workers>], overall: ok
```

## Gotchas (all hit at least once)

1. **`CMD []` kills the container.** The official image's CMD is empty, so
   `main-wrapper.sh` defaults to interactive `hermes`, which prints
   `Input is not a terminal (fd=0)` and exits on TTY-less Railway — triggering
   s6 stage-3 shutdown of the WHOLE tree (gateway + dashboard → 502). **Fix:
   `CMD ["gateway", "run"]`** in the derived Dockerfile. (`main-hermes` s6
   service is a `sleep infinity` no-op; the gateway runs as the CMD main program.)
2. **Volume path is `/opt/data`, not `/root/.hermes`** (official image layout).
3. **Model IDs drift.** Verify every ID against live `/v1/models` first — image/video
   models are on `?type=image` / `?type=video` filters, NOT the default text list
   (`grok-imagine-image-2-0` and `ltx-2-5-pro-*` won't appear in the plain list).
4. **Dashboard fails closed** without a full auth provider (username+password+secret).
5. **MA repo default branch is a Claude workshop branch**, not `main`.
6. **MA skills use Claude-style frontmatter** (`allowed-tools`, `license`) — Hermes'
   loader ignores unknown keys (only reads `name`/`description`/`metadata`), so they load fine.
7. **Profile names must be lowercase alphanumeric** (`hermes profile create` constraint).

## Worker roster (reference)

| Worker | Skills |
|---|---|
| literaturereview | pubmed-search, systematic-literature-review, clinical-trials-search |
| evidencesynthesis | evidence-appraisal, evidence-synthesis, evidence-gap-analysis |
| citationverifier | citation-integrity |
| medicalinformation | medical-information-response, medical-terminology-mapping, plain-language-summary |
| competitiveintel | congress-intelligence, regulatory-label-intelligence, field-insight-synthesis |
| kolengagement | kol-engagement-brief, field-insight-synthesis, insight-generation |
| content | scientific-manuscript, scientific-communication-strategy, medical-slide-deck, congress-abstract-and-poster, data-visualization-for-medical, mlr-review-readiness |
| medicalstrategy | medical-strategy-plan, strategic-analysis, insight-generation, launch-planning |

Foundation (every worker): medical-affairs-foundations, evidence-appraisal, citation-integrity, deliverable-quality-review.
