---
name: open-design-first
description: "Use Open Design first for design-related work: UI/UX, visual prototypes, landing pages, decks, brand systems, artifact previews, image/video/audio assets, and design critique. Starts/uses local nexu-io/open-design wired to Venice via ~/.hermes/.env."
---

# Open Design First

## Trigger

Load this skill for any design-related task, including:

- UI/UX design, app screens, dashboards, landing pages, websites, product mockups
- Visual systems, brand exploration, moodboards, logos, marketing creatives
- Decks, presentations, infographics, HTML artifacts, prototypes, previewable demos
- Image/video/audio asset generation or design templates
- Design critique, iteration, or converting rough ideas into polished visuals

Default workflow: **try Open Design first**, then fall back to direct Hermes tools only if Open Design is unavailable or clearly not useful.

## Local setup facts

- Repo: `~/repos/open-design`
- Launcher: `~/.local/bin/open-design-venice`
- Web UI: `http://127.0.0.1:5175`
- Daemon: `http://127.0.0.1:7457`
- Node runtime: `~/.local/node-v24.15.0-linux-x64`
- Venice credential source: `~/.hermes/.env`
  - `VENICE_INFERENCE_KEY` and `VENICE_API_KEY` are expected there.
  - Never print, log, hard-code, or copy API keys into prompts/files.
- OpenAI-compatible Venice base URL: `https://api.venice.ai/api/v1`
- Default Venice text model for helper calls: `z-ai-glm-5-turbo`
- Default Venice image model for Open Design media: `z-image-turbo`

## Start / check

```bash
~/.local/bin/open-design-venice start web --daemon-port 7457 --web-port 5175
~/.local/bin/open-design-venice status
```

Health checks:

```bash
python3 - <<'PY'
import urllib.request, json
print(urllib.request.urlopen('http://127.0.0.1:7457/api/health', timeout=10).read().decode())
print(urllib.request.urlopen('http://127.0.0.1:5175', timeout=10).status)
PY
```

If env changes, restart:

```bash
~/.local/bin/open-design-venice restart web --daemon-port 7457 --web-port 5175
```

Stop when done if the user wants it stopped:

```bash
~/.local/bin/open-design-venice stop
```

## Configuration already applied

The local Open Design daemon is configured with:

- `agentId: hermes`
- onboarding completed
- custom instructions to use Open Design skills/templates first and keep Venice keys private
- media providers:
  - `custom-image` → Venice OpenAI-compatible image endpoint, model `z-image-turbo`
  - `openai` → Venice OpenAI-compatible base URL, model `z-image-turbo`
  - API keys are supplied from environment (`source: env`), not stored in Open Design config.

Verify media config without exposing secrets:

```bash
python3 - <<'PY'
import urllib.request, json
cfg=json.loads(urllib.request.urlopen('http://127.0.0.1:7457/api/media/config', timeout=10).read().decode())
for k in ['custom-image','openai']:
    p=cfg['providers'][k]
    print(k, p['configured'], p['source'], p['baseUrl'], p.get('model'))
PY
```

Expected source is `env` and `apiKeyTail` should be empty.

## How to use during design tasks

1. Start/check Open Design (`open-design-venice status` — if idle, start; do not skip when the complaint is design quality).
2. Prefer Open Design's built-in skills/templates/design systems for the design task.
3. Use the UI at `http://127.0.0.1:5175` for interactive visual iteration and artifact preview.
4. When generating media through Open Design, prefer the `custom-image` provider/model path backed by Venice (`z-image-turbo`).
5. If the task is a website/git repo refresh, import the existing checkout into Open Design with `POST /api/import/folder` so edits happen in the real git folder, then branch, implement, verify, and commit locally before asking about push/PR. See `references/git-site-refresh.md`.
6. For design PRs, verify the visual delta before claiming success: compare PR branch vs live/main, capture a preview/screenshot when possible, and explicitly say whether the public site is still unchanged because the PR is unmerged. See `references/design-pr-visibility.md`.
7. When Playwright/Chromium is unavailable in WSL, use the Windows Chrome/Edge fallback script `scripts/capture-wsl-windows-chrome-screenshot.ps1` against a local HTTP server, then deliver the PNG with `MEDIA:/absolute/path`.
8. If producing assets for Telegram delivery, export/save the resulting artifact locally and send via `MEDIA:/absolute/path`.
9. If Open Design fails, capture the specific command, HTTP status, and recent logs, then fall back to an appropriate Hermes creative skill/tool.

### Pitch / investor decks

When the user wants a refined / non-wrapper pitch deck: attempt Open Design first, pair with `viv-design` (BRAND register) and `pptx` anti-bland layouts. If the daemon is idle/unavailable, still apply viv-design + wide art-directed pptxgenjs — do **not** default to equal-card SaaS templates.

## Design-led git website refresh

Use this sequence when the user says to update a site/repo: check Open Design, clone/fetch the repo, create a `design/...` branch, import the folder through `/api/import/folder`, generate concise implementation-ready direction, edit the actual source files, run static/app checks, commit locally, and ask before pushing/opening a PR. The detailed recipe and verification scriptlets are in `references/git-site-refresh.md`.

Before presenting the work as a redesign, perform a visibility check: confirm whether the user is viewing live `main` or the PR branch, provide a preview/screenshot when tooling allows it, and be candid if the visual delta is modest. The pitfall checklist is in `references/design-pr-visibility.md`.

## Troubleshooting

- If `open-design-venice status` says idle, start it with the command above.
- If Venice calls fail, verify `~/.hermes/.env` contains `VENICE_INFERENCE_KEY` or `VENICE_API_KEY`; do not print values.
- If the daemon/web are running but UI is stale, restart web/daemon with the launcher.
- If `od doctor` fails with `Cannot access 'CONFIG_STRING_FLAGS' before initialization`, use `tools-dev status/check` and HTTP health endpoints instead; this is an upstream CLI build-order bug observed in the local checkout.
