# Mimeo Integration Pattern — Venice API Migration

Pattern for cloning a third-party repo that uses a different AI provider
and migrating it to the Venice AI API. Specifically applied to the
K-Dense-AI/mimeo expert-knowledge-distillation pipeline.

## General Pattern

1. **Clone shallow:** `git clone --depth 1` or `git init && git fetch --depth 1 origin main` (the latter is more reliable if the remote is slow)
2. **Identify all API touchpoints:** Search for `base_url`, `api_key`, `OpenAI(`, `httpx`, `requests` to find every place that calls an external API
3. **Replace the base URL + key:** Most Python AI apps use the OpenAI SDK; just change `base_url` and `api_key` to Venice's
4. **Rewrite non-OpenAI endpoints:** Image generation, web search, etc. need custom code since Venice's endpoints differ from the original provider
5. **Handle SDK compatibility:** Venice accepts OpenAI-compatible chat endpoints but has differences (see `openai-sdk-compat.md`)
6. **Consolidate API keys:** If the original uses multiple providers, check if Venice covers all capabilities (e.g., Venice Augment API replaces separate search providers)
7. **Build a frontend** if the repo is CLI-only — a single `index.html` SPA served by FastAPI with SSE for pipeline progress

## Files Modified in Mimeo

| File | Change |
|------|--------|
| `config.py` | `VENICE_API_KEY` + `VENICE_BASE_URL` instead of OpenRouter; `DEFAULT_MODEL=gemma-4-uncensored` (deepseek-v4-pro has input content filter that blocks scraped web text — unusable for raw pipeline stages), `DEFAULT_AVATAR_MODEL=nano-banana-2` |
| `llm.py` | `AsyncOpenAI(base_url=VENICE_BASE_URL, api_key=...)`; `extra_body` for `venice_parameters`; conditional `max_tokens` |
| `avatar.py` | Replaced OpenRouter chat-completions image prompt with Venice `/images/generations` endpoint via httpx |
| `parallel_client.py` | Replaced Parallel SDK with Venice `/augment/search` + `/augment/scrape` via httpx |
| `cli.py` | Updated help text, added `web` command |
| `web.py` | FastAPI server with SSE pipeline progress, serves SPA + infographic |
| `.env` | Single `VENICE_API_KEY` for everything |

## Key Pitfalls

1. **Content filter on input text:** Scraped web content triggers Venice's safety filter on models like `deepseek-v4-pro` and `deepseek-v4-flash`. The `extra_body={"venice_parameters": {"include_venice_system_prompt": False}}` workaround sometimes helps, but `deepseek-v4-pro`'s input filter is aggressive enough that it still blocks legitimate scraped text (HTTP 400 with `"Input text data may contain inappropriate content."`). For pipelines that feed raw scraped web content, **use `gemma-4-uncensored` instead** — it has no input-side content filter and 256K context.
2. **`max_tokens=None` → 400:** Venice rejects `null` for `max_tokens`. Only include it when non-None.
3. **`venice_parameters` as kwarg:** OpenAI SDK rejects unknown kwargs. Must use `extra_body=`.
4. **Model naming:** Venice model IDs don't always match upstream names (e.g., no "croc" model; use `deepseek-v4-pro` for 1M ctx).
5. **Image endpoint differs:** Venice uses `/images/generations` with a `model` param, not chat completions with an image prompt.
6. **Git clone timeouts:** Use `git init + git fetch --depth 1` if `git clone --depth 1` hangs.

## Smart Model Routing

Mimeo's 8-stage pipeline benefits from using different models for different stages rather than one model for everything:

- **Raw/scraped-text stages** (discovery, distillation, research extraction) → `gemma-4-uncensored` (no content filter, 256K ctx)
- **Final authoring/critique stages** (synthesis, critique, verification) → `openai-gpt-55-pro` or `deepseek-v4-pro` (higher quality, 1M ctx, no scraped text in input at this point)
- **Fast/cheap stages** (identity resolution, simple classification) → `deepseek-v4-flash` or `llama-3.3-70b`

Implementation: set `MIMEO_MODEL` in `.env` for the default, then pass `--model` per-stage in the pipeline runner. Alternatively, add a `model_overrides` dict to `Settings` that maps stage names to model IDs.

## Avatar Model Upgrades

The default `nano-banana-2` works but produces basic quality. Better options:

- `flux-2-max` — Best overall quality for detailed painterly portraits
- `gpt-image-2` — Excellent prompt adherence
- `nano-banana-pro` — Same family as nano-banana-2, better quality
- `recraft-v4-pro` — Professional illustration style

Set via `MIMEO_AVATAR_MODEL` in `.env` or `--avatar-model` CLI flag.

## Frontend Architecture

When the original repo is CLI-only, build a web frontend:

- **FastAPI server** (`web.py`) with SSE for real-time pipeline progress
- **Single `index.html`** SPA with dark theme, expert cards, and Markdown viewer
- **Infographic route** (`/infographic`) for visual summaries
- Serve from `frontend/` directory, mounted as static files
- Run on port 8000 by default

## Deployment Considerations

The web server can be deployed to any platform that supports Python + FastAPI:

- **Local:** `python -m mimeo.web` or `uvicorn mimeo.web:app`
- **Docker:** Add a Dockerfile with Python 3.12+, install deps, expose 8000
- **Cloud:** Fly.io, Railway, Render — all support FastAPI natively
- **Note:** Venice API key must be set as an environment variable in production
