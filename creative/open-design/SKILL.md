---
name: open-design
version: 0.1.0
description: AI design engine that generates production-ready artifacts (HTML, PNG, React, Tailwind) using DESIGN.md brand contracts and Venice API. Daemon with 155+ skills.
tags: [design, branding, venice, infographic, carousel, design-system, ai-art]
triggers:
  - open design
  - design engine
  - branded content
  - design artifacts
  - brand contract
  - nano-banana
---

# Open Design — AI Design Engine

Open Design is an AI-powered design generation tool that produces real design artifacts (HTML, PNG, React components, Tailwind CSS) using DESIGN.md brand contract files. It wraps Venice AI (or any OpenAI-compatible LLM) as a BYOK provider and exposes 155+ skills for content creation.

## When to Use

- Generate branded visual content (carousels, infographics, social cards, ads)
- Enforce consistent brand identity across AI-generated designs
- Produce production-ready HTML/CSS artifacts, not just raw images
- Create a design system with AI that "knows" the brand rules
- Batch-generate visual assets with brand compliance baked in

For DESIGN.md file authoring and linting, use the `design-md` skill. For raw Venice image generation without brand contracts, use the `venice-api` skill. This skill is for the Open Design daemon that *consumes* DESIGN.md files and *uses* Venice to generate output.

## Setup & Installation

### Prerequisites

- **Node.js 24+** (required — older versions fail). Install via fnm:
  ```bash
  fnm install 24 && fnm use 24
  ```
- **pnpm** (corepack recommended):
  ```bash
  corepack enable && corepack prepare pnpm@latest --activate
  ```

### Install from GitHub

Open Design is NOT on npm — must clone from source:

```bash
git clone <open-design-repo-url> /tmp/open-design
cd /tmp/open-design
pnpm install
```

### Wire Venice as BYOK Provider

Create `~/.open-design/config.json`:

```json
{
  "providers": {
    "openai": {
      "apiKey": "VENICE_INFERENCE_KEY_xxx",
      "baseUrl": "https://api.venice.ai/api/v1"
    }
  }
}
```

Open Design treats Venice as an OpenAI-compatible provider. The `openai` provider key is the default.

### Start the Daemon

Open Design has TWO entry points and THREE components. The right way to run the full stack is `tools-dev`, not the bare `od.mjs`.

**Components:**
- **daemon** — the API server (port assigned by tools-dev, e.g. 62677)
- **web** — the Next.js web UI on a different port (e.g. 62678)
- **desktop** — the Electron app (not needed for browser use)

**Bare daemon (API only, no UI):**
```bash
export PATH="/Users/vivgatesai/.local/share/fnm/node-versions/v24.16.0/installation/bin:$PATH"
cd /tmp/open-design
node apps/daemon/bin/od.mjs --port 7456 --no-open
```
Returns 404 at `/` (no UI served). Use this only if you don't need the web UI (e.g. headless API access from Paperclip). All-in-one if you only need the API.

**Full stack via tools-dev (recommended):**
```bash
export PATH="/Users/vivgatesai/.local/share/fnm/node-versions/v24.16.0/installation/bin:$PATH"
cd /tmp/open-design
node ./node_modules/.bin/../@open-design/tools-dev/bin/tools-dev.mjs start web --json
```
Starts BOTH the daemon AND the web UI. Returns JSON with both URLs. `start daemon` and `start web` can also be issued separately. The web UI is the Next.js app at `apps/web/`.

**tools-dev commands:** `start [app]`, `run [app]`, `status [app]`, `stop [app]`, `restart [app]`, `logs [app]`, `inspect <app>`, `check [app]`. App = `daemon`, `web`, or `desktop`. Omit app for `all`.

**Port discovery:** tools-dev assigns ephemeral ports (62677, 62678, etc.) — do NOT hardcode 7456. Read the JSON output of `start` or use `tools-dev status` to discover the live ports. The web URL and the daemon API URL are DIFFERENT ports.

**Pitfall**: Two daemons cannot share a port. If a bare `od.mjs` is on 7456, `tools-dev start daemon` will pick a different port and the two will be redundant. Kill the bare one (`kill <pid>`) before starting tools-dev if you want the canonical port.

**Pitfall**: `pnpm dev` may fail with module resolution errors after certain pnpm versions. If it does, use the tools-dev path. The daemon also requires an `OD_API_TOKEN` env var for API auth; tools-dev auto-generates one if you set `OD_API_TOKEN=$(openssl rand -hex 32)`.

**Pitfall**: If the daemon was previously running, kill the old process before restarting. The daemon does not have a built-in hot-reload for DESIGN.md changes — a full restart is required.

### Verify

```bash
curl -s http://127.0.0.1:7456/api/design-systems
curl -s http://127.0.0.1:7456/api/skills | python3 -c 'import sys,json; print(len(json.load(sys.stdin)), "skills loaded")'
```

## Creating a Brand Design System

1. **Create the DESIGN.md** following the `design-md` skill schema (9 canonical sections: Overview, Colors, Typography, Layout, Elevation, Shapes, Components, Do's and Don'ts)
2. **Place it in the design-systems directory**:
   ```
   /tmp/open-design/design-systems/<brand-name>/DESIGN.md
   ```
3. **Restart the daemon** — it auto-discovers new design systems on startup
4. **Verify detection**: `curl -s http://127.0.0.1:7456/api/design-systems`

The DESIGN.md becomes the "brand contract" that all generated artifacts must follow. Skills like `brandkit`, `brand-guidelines`, and `stitch-design-taste` reference it automatically.

## Key Skills (155+ total)

### Content & Social Media
- `card-twitter` — Social media card images (X/Twitter, LinkedIn)
- `card-xiaohongshu` — Xiaohongshu/Little Red Book cards
- `article-magazine` — Long-form magazine-style article layouts
- `ad-creative` — Ad/banner creatives
- `copywriting` — Brand-consistent copy generation
- `social-x-post-card` — X/Twitter post card design

### Brand & Design
- `brandkit` — Brand asset generation
- `brand-guidelines` — Generate brand guideline pages
- `color-expert` — Color palette consultation
- `stitch-design-taste` — Design quality review/critique
- `design-taste-frontend` — Frontend design quality review
- `canvas-design` — General canvas layout design
- `creative-director` — Creative direction and art direction

### Code & Web
- `web-artifacts-builder` — Full web page/app generation
- `slides` — Presentation slide decks
- `d3-visualization` — Data visualization charts

### Venice-Native Skills
- `venice-image-generate` — Direct Venice image generation
- `venice-image-edit` — Venice image editing
- `venice-video` — Venice video generation
- `venice-audio-speech` — Venice TTS
- `venice-audio-music` — Venice music generation

### Smart Routing
- `stitch-loop` — Iterative design refinement loop
- `brainstorming` — Ideation and concept exploration

## API Endpoints

- `GET /api/design-systems` — List detected design systems
- `GET /api/skills` — List all available skills
- `POST /api/generate` — Generate an artifact with a specific skill
- `POST /api/render` — Render an artifact to PNG/HTML

## Generating Content

### Direct Venice Image Gen (via Open Design)

When using the Venice-native skills inside Open Design, the daemon handles prompt formatting, brand contract injection, and model routing. This produces more consistent output than calling Venice directly.

### Using a Skill

Skills are invoked via the API or the daemon's CLI. Each skill accepts a prompt and optionally a design system reference. The skill automatically:
1. Injects the DESIGN.md brand tokens into the prompt
2. Routes to the appropriate model (Venice cloud via BYOK)
3. Formats the output as the appropriate artifact type (HTML, PNG, etc.)

## Multi-Agent Pattern (Paperclip + Open Design)

When using Paperclip AI agents with Open Design:

1. **Create a Brand Guardian agent** (role: `designer`) with brand-related skills
2. **Assign Venice model per agent role**:
   - Creative/reasoning → `nvidia-nemotron-3-ultra-550b-a55b`
   - Analysis/research → `deepseek-v4-pro`
   - Code/engineering → `gemma-4-uncensored`
3. **Inject skill list per agent** — Each agent's system prompt should list its assigned Open Design skills and Venice model
4. **Brand Guardian reviews all output** against DESIGN.md before publishing

## Pitfalls

1. **Node 24 is required at RUNTIME, not just install time** — `better-sqlite3` native binding is compiled for the Node version present at `pnpm install`. If you have Node 22 on PATH and Node 24 via fnm, the daemon will start with `ERR_DLOPEN_FAILED` on `better-sqlite3` and exit within 5s. The fix is to RUN the daemon with Node 24, not Node 22. The fnm Node 24 binary lives at `~/.local/share/fnm/node-versions/v24.16.0/installation/bin/node` (or whatever version fnm installed). Prepend it to PATH: `export PATH="/Users/vivgatesai/.local/share/fnm/node-versions/v24.16.0/installation/bin:$PATH"`. Verify with `node --version` before starting the daemon.
2. **Not on npm** — Must clone from GitHub. There is no `npm install open-design`.
3. **Web frontend may not be built** — The daemon API works fine, but the web UI at `http://127.0.0.1:7456/` may show 404 if `dist/` doesn't exist. Use `--no-open` and interact via API.
4. **nano-banana-pro doesn't support `response_format: "b64_json"`** — Returns 400. Omit `response_format` or use default URL format. Use `flux-2-max` for b64 output.
5. **DESIGN.md must be in the design-systems directory** — The daemon only scans `/tmp/open-design/design-systems/<name>/DESIGN.md`. Files elsewhere are not detected.
6. **Daemon must restart to pick up new design systems** — No hot-reload for DESIGN.md changes. Kill and restart `pnpm dev --no-open`.
7. **Venice API key must be in `~/.open-design/config.json`** — Env vars are not read. The `providers.openai.apiKey` field is the only path.
8. **1500-char prompt limit (ALL Venice image models)** — The Venice API gateway hard-caps the `prompt` field at 1500 chars for every image model, not just gpt-image-2. Model specs show 10K-32K but the gateway rejects >1500. For complex infographics, distill the prompt to: titles > data points > layout > colors. See `venice-api` skill `references/venice-image-model-catalog.md` for the full spec-vs-reality table.

## See Also

- `design-md` — Author and lint DESIGN.md brand spec files
- `venice-api` — Full Venice API reference and model catalog
- `content-marketing-pipeline` — Content pipeline that uses Open Design for branded visuals
- `openclaw` — OpenClaw agent platform for persistent bot deployment
