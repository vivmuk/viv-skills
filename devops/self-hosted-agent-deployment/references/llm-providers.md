# LLM providers — pick the cheapest viable OpenAI-compatible endpoint

The cheapest widely-available providers that work with a personal
agent's tool-use surface. All expose an OpenAI-compatible endpoint
(`/chat/completions`), all have a free tier that's adequate for a
personal agent.

| Provider | Free tier ceiling | Default model | OpenAI-URL | Notes |
|---|---|---|---|---|
| **Venice AI** | ~$5/mo DIEM cap | `minimax-m3` (cheap, 500K ctx) | `https://api.venice.ai/api/v1` | Hosts many open-source models; uncensored fine-tuned variants available |
| **OpenRouter** | several `:free` model slugs | `meta-llama/llama-4-maverick:free` | `https://openrouter.ai/api/v1` | Aggregator over many vendors; free model slugs rotate, expect to switch |
| **Google AI Studio (Gemini)** | 15 RPM | `gemini-2.5-flash-lite` | `https://generativelanguage.googleapis.com/v1beta/openai/` | The cheapest non-Venice option; free RPM cap means rate-limit on busy days |

## Provider selection logic for a personal agent

1. **If you already have a Venice account** with an attached
   inference key, use Venice as primary. Same key for local
   machine and cloud deploy. Spend ledgered at
   `/tmp/aipharmaxchange_spend/spend_YYYY-MM-DD.json` style.
2. **Add OpenRouter as fallback** behind a `:free` model slug.
   When the primary 5xxs or rate-limits, the agent seamlessly
   retries with OpenRouter. Free models rotate; check monthly.
3. **Skip Gemini unless you're Google-primary**. Google AI
   Studio's 15-RPM cap means busy days hit the limit. The paid
   tier is cheap, but you're paying for the same inference
   Venice serves free or near-free.

## Multi-provider config (Hermes-flavored, but the pattern
generalises)

```yaml
model:
  default: minimax-m3                     # primary
  context_length: 500000
  max_output_tokens: 32000

providers:
  venice:
    type: openai
    base_url: ${VENICE_BASE_URL}
    api_key: ${VENICE_API_KEY}
    default_model: ${VENICE_MODEL}
  openrouter:
    type: openai
    base_url: ${OPENROUTER_BASE_URL}
    api_key: ${OPENROUTER_API_KEY}
    default_model: ${OPENROUTER_DEFAULT_MODEL}

fallback_providers:
  - openrouter                            # second choice
  - venice                                # third if openrouter 5xx's too
```

`.env` declares the secrets; the placeholder syntax in `config.yaml`
gets substituted at container start.

## Pitfalls

- **Hex codes from the model name leak through prompts.** Not
  relevant to API calls but matters for image prompts.
- **OpenRouter `:free` models change without notice.** Don't
  pin to a slug that might disappear — keep the env var
  `OPENROUTER_DEFAULT_MODEL` swappable in `.env`, switch it on
  rate.
- **Venice DIEM cap is a per-key limit, not a per-account limit.**
  Generate a separate key per environment (local / cloud) so the
  cloud agent's runaway loads don't blow the local DIEM cap.
- **No tool-use on truly free models.** Some `:free` OpenRouter
  models don't support `tools`. Verify before wiring — the
  agent's channel will surface a "tool_use not supported" 400
  in the first few turns otherwise.

## Switching providers without rebuilding the image

The image is provider-agnostic. Just change `.env` and
`docker compose up -d`. New provider, no image rebuild.

## See also

- `templates/config.yaml.example` — copy-pasteable provider block
- `references/secrets-management.md` — env var hygiene
