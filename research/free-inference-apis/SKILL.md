---
name: free-inference-apis
description: >
  Catalog and usage guide for free LLM inference APIs — OpenRouter, NVIDIA NIM,
  Google Gemini, Groq, Cloudflare Workers AI, Cerebras, SambaNova, HuggingFace,
  Cohere, and Chutes.ai. Includes API keys, endpoints, rate limits, code examples,
  and model selection guidance.
version: 1.0.0
author: Vega
tags:
  - free-inference
  - llm
  - api
  - openrouter
  - nvidia
  - google-gemini
  - groq
  - cloudflare
  - cerebras
  - sambanova
  - huggingface
  - cohere
---

# Free Inference APIs — Complete Catalog & Usage Guide

## Overview

Ten providers offer genuinely free LLM inference via OpenAI-compatible APIs. Most
use the same `POST /v1/chat/completions` interface — only the `base_url` and API key
change. This skill covers signup, endpoints, rate limits, available models, and
working code for each.

## Quick Reference Table

| Provider | Free Tier | API Standard | Base URL | Best For |
|---|---|---|---|---|
| OpenRouter | 17 free models, no credit card | OpenAI | `https://openrouter.ai/api/v1` | Model variety, auto-routing |
| NVIDIA NIM | 1,000 free credits on signup | OpenAI | `https://integrate.api.nvidia.com/v1` | Large models (550B), 1M context |
| Google Gemini | Free tokens, no credit card | Custom / OpenAI | `https://generativelanguage.googleapis.com/v1beta` | Multimodal, image gen, TTS |
| Groq | Free plan, generous RPD | OpenAI | `https://api.groq.com/openai/v1` | Ultra-low latency (LPU) |
| Cloudflare Workers AI | 10,000 Neurons/day free | Custom / REST | `https://api.cloudflare.com/client/v4/accounts/{id}/ai/run/` | Edge inference, images |
| Cerebras | $5 free credits | OpenAI | `https://api.cerebras.ai/v1` | Fastest inference (wafer-scale) |
| SambaNova | Free tier available | OpenAI | `https://api.sambanova.ai/v1` | DeepSeek, Llama, fast |
| HuggingFace | Free tier with monthly credits | Custom / OpenAI | `https://api-inference.huggingface.co` | Open-weight model variety |
| Cohere | Trial keys (free, limited) | Custom | `https://api.cohere.com/v2` | Rerank, embed, Command A |
| Chutes.ai | Free API access | OpenAI | `https://api.chutes.ai/v1` | Open models, streaming |

---

## 1. OpenRouter (Best Starting Point)

**Signup:** https://openrouter.ai/keys — create account, generate API key. No credit
card required for free models.

### Free Models (as of Aug 2026)

| Model ID | Context | Modality | Notes |
|---|---|---|---|
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1,000,000 | text→text | 55B active / 550B total MoE |
| `nvidia/nemotron-3-super-120b-a12b:free` | 262,144 | text→text | 120B MoE, 12B active |
| `nvidia/nemotron-3-nano-30b-a3b:free` | 256,000 | text→text | Efficient agent model |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256,000 | text+image+audio+video→text | Multimodal |
| `nvidia/nemotron-nano-12b-v2-vl:free` | 128,000 | text+image+video→text | Vision + video |
| `nvidia/nemotron-nano-9b-v2:free` | 128,000 | text→text | Small + fast |
| `nvidia/nemotron-3.5-content-safety:free` | 128,000 | text+image→text | Content moderation |
| `google/gemma-4-31b-it:free` | 262,144 | text+image+video→text | 31B dense, multimodal |
| `google/gemma-4-26b-a4b-it:free` | 262,144 | text+image+video→text | 26B MoE, 3.8B active |
| `openai/gpt-oss-20b:free` | 131,072 | text→text | OpenAI open-weights, Apache 2.0 |
| `cohere/north-mini-code:free` | 256,000 | text→text | 30B MoE coding model |
| `poolside/laguna-s-2.1:free` | 262,144 | text→text | 118B coding agent |
| `poolside/laguna-xs-2.1:free` | 262,144 | text→text | 33B coding agent |
| `inclusionai/ling-3.0-tiny:free` | 262,144 | text→text | 7.9B MoE, 1.3B active |
| `openrouter/free` | 200,000 | text+image→text | Auto-routes to available free model |

### Code Example

```python
import openai

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="YOUR_OPENROUTER_KEY",
)

response = client.chat.completions.create(
    model="nvidia/nemotron-3-ultra-550b-a55b:free",
    messages=[{"role": "user", "content": "Explain quantum entanglement simply."}],
)
print(response.choices[0].message.content)
```

### Curl

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-20b:free",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Key Notes
- Free models have `:free` suffix in the model ID.
- Rate limits: ~20 requests/min, 200 requests/day for free tier.
- May show rate-limit errors during peak times — retry or try another free model.
- The `openrouter/free` model auto-routes to any available free model.

---

## 2. NVIDIA NIM (Best for Large Models)

**Signup:** https://build.nvidia.com — sign in with NVIDIA account, get API key from
any model page. 1,000 free credits on signup.

### Available Models (100+ models)

**Flagship LLMs:**
- `nvidia/nemotron-3-ultra-550b-a55b` — 550B MoE, 1M context
- `nvidia/nemotron-3-super-120b-a12b` — 120B MoE, 256K context
- `nvidia/nemotron-3-nano-30b-a3b` — 30B MoE
- `nvidia/nemotron-nano-9b-v2` — 9B, reasoning + non-reasoning
- `deepseek-ai/deepseek-v4-flash-0731` — DeepSeek V4 Flash
- `z-ai/glm-5.2` — GLM 5.2
- `moonshotai/kimi-k2.6` — Kimi K2.6
- `minimaxai/minimax-m3` — MiniMax M3
- `meta/llama-3.3-70b-instruct` — Llama 3.3 70B
- `meta/llama-3.1-70b-instruct` — Llama 3.1 70B
- `mistralai/mistral-large-2-instruct` — Mistral Large 2
- `openai/gpt-oss-120b` — GPT-OSS 120B
- `openai/gpt-oss-20b` — GPT-OSS 20B
- `google/gemma-4-31b-it` — Gemma 4 31B
- `google/gemma-3-12b-it` — Gemma 3 12B
- `stepfun-ai/step-3.7-flash` — Step 3.7 Flash

**Multimodal:**
- `meta/llama-3.2-90b-vision-instruct` — 90B vision
- `nvidia/nemotron-nano-12b-v2-vl` — 12B video + vision
- `microsoft/phi-3-vision-128k-instruct` — Phi-3 Vision

**Code:**
- `bigcode/starcoder2-15b` — StarCoder2
- `meta/codellama-70b` — CodeLlama 70B
- `mistralai/codestral-22b-instruct-v0.1` — Codestral

**Embeddings:**
- `nvidia/nv-embedqa-e5-v5`
- `nvidia/llama-3.2-nv-embedqa-1b-v1`
- `baai/bge-m3`

### Code Example

```python
import openai

client = openai.OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="YOUR_NVIDIA_KEY",
)

response = client.chat.completions.create(
    model="meta/llama-3.3-70b-instruct",
    messages=[{"role": "user", "content": "Write a Python function to merge sort."}],
    max_tokens=512,
)
print(response.choices[0].message.content)
```

### Key Notes
- 1,000 free credits on signup (each credit ≈ 1 request for most models).
- OpenAI-compatible — just change `base_url` and `api_key`.
- Best place to try massive models like Nemotron Ultra 550B.

---

## 3. Google Gemini API (Best for Multimodal)

**Signup:** https://aistudio.google.com — get API key. No credit card for free tier.

### Free Tier Models

| Model | Endpoint ID | Capabilities |
|---|---|---|
| Gemini 3.6 Flash | `gemini-3.6-flash` | Text, multimodal, agentic |
| Gemini 3.5 Flash | `gemini-3.5-flash` | Frontier coding + agentic |
| Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | Fast, cost-effective |
| Gemini 3.1 Flash-Lite | `gemini-3.1-flash-lite` | Frontier-class at low cost |
| Gemini 3.1 Pro (preview) | `gemini-3.1-pro` | Advanced intelligence |
| Gemini 3 Flash (preview) | `gemini-3-flash` | Frontier performance |
| Nano Banana 2 | `gemini-3.1-flash-image` | Image generation |
| Gemini 3.1 Flash TTS | `gemini-3.1-flash-tts` | Text-to-speech |
| Gemini Omni Flash | `gemini-omni-flash` | Video generation |

### Free Tier Limits
- **Input/output tokens:** Free of charge
- **RPM:** ~15 (varies by model)
- **RPD:** ~1,500 (varies by model)
- **Grounding with Google Search:** 5,000 free requests/month
- **Content used to improve products** (free tier only)

### Code Example (Python SDK)

```python
from google import genai

client = genai.Client(api_key="YOUR_GEMINI_KEY")

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Explain the theory of relativity in simple terms.",
)
print(response.text)
```

### Code Example (OpenAI-compatible)

```python
import openai

client = openai.OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key="YOUR_GEMINI_KEY",
)

response = client.chat.completions.create(
    model="gemini-3.6-flash",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### Image Generation (Free)

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_GEMINI_KEY")

response = client.models.generate_content(
    model="gemini-3.1-flash-image",
    contents="A serene mountain landscape at sunrise",
    config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
)
# Access image data
for part in response.candidates[0].content.parts:
    if part.inline_data:
        with open("output.png", "wb") as f:
            f.write(part.inline_data.data)
```

---

## 4. Groq (Best for Speed)

**Signup:** https://console.groq.com/keys — create API key. No credit card.

### Free Plan Models & Rate Limits

| Model ID | RPM | RPD | TPM | TPD |
|---|---|---|---|---|
| `llama-3.3-70b-versatile` | 30 | 1,000 | 12K | 100K |
| `llama-3.1-8b-instant` | 30 | 14,400 | 6K | 500K |
| `openai/gpt-oss-120b` | 30 | 1,000 | 8K | 200K |
| `openai/gpt-oss-20b` | 30 | 1,000 | 8K | 200K |
| `qwen/qwen3.6-27b` | 30 | 1,000 | 8K | 200K |
| `groq/compound` | 30 | 250 | 70K | — |
| `groq/compound-mini` | 30 | 250 | 70K | — |
| `whisper-large-v3` | 20 | 2,000 | — | — |
| `whisper-large-v3-turbo` | 20 | 2,000 | — | — |

### Code Example

```python
import openai

client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="YOUR_GROQ_KEY",
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Write a haiku about debugging."}],
)
print(response.choices[0].message.content)
```

### Key Notes
- LPU (Language Processing Unit) delivers ~500+ tokens/sec — fastest inference.
- `llama-3.1-8b-instant` has the most generous daily limit (14,400 requests/day).
- Supports tool/function calling, JSON mode, and vision.

---

## 5. Cloudflare Workers AI (Best for Edge)

**Signup:** https://dash.cloudflare.com — create account, get Account ID and API token.

### Free Tier
- **10,000 Neurons/day** free (no credit card)
- Neurons = unit of AI compute (varies by model)

### Available Models

**LLM:**
- `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- `@cf/meta/llama-3.1-8b-instruct`
- `@cf/meta/llama-3.1-70b-instruct`
- `@cf/mistral/mistral-7b-instruct-v0.1`
- `@cf/meta/llama-2-7b-chat-fp16`
- `@cf/microsoft/phi-2`

**Image:**
- `@cf/stabilityai/stable-diffusion-xl-base-1.0`
- `@cf/black-forest-labs/flux-1-schnell`

**Embeddings:**
- `@cf/baai/bge-base-en-v1.5`
- `@cf/baai/bge-large-en-v1.5`

**Audio:**
- `@cf/openai/whisper`

### Code Example

```python
import requests

ACCOUNT_ID = "your_account_id"
API_TOKEN = "your_api_token"

response = requests.post(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    headers={"Authorization": f"Bearer {API_TOKEN}"},
    json={
        "messages": [
            {"role": "user", "content": "What is the capital of France?"}
        ]
    },
)
print(response.json()["result"]["response"])
```

### Key Notes
- Also works via Workers binding: `env.AI.run('@cf/meta/llama-3.1-8b-instruct', ...)`
- Image generation and Whisper STT are also free within 10K Neurons/day.
- Best for edge-deployed apps with Cloudflare's global network.

---

## 6. Cerebras (Best for Throughput)

**Signup:** https://cerebras.ai — create account, get API key. $5 free credits.

### Free Tier
- $5 in free credits on signup
- Access to all Cerebras-powered models
- World's fastest inference — 20x faster than GPUs (wafer-scale)

### Available Models
- `gemma-4-31b` — Multimodal document analysis
- `kimi-k2.6` — Financial dashboard generation
- `glm-4.7` — Code generation
- `codex-spark` — Salesforce clone, coding
- `llama-4-scout` — 2,000+ tokens/sec
- `llama-4-maverick`

### Code Example

```python
import openai

client = openai.OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key="YOUR_CEREBRAS_KEY",
)

response = client.chat.completions.create(
    model="gemma-4-31b",
    messages=[{"role": "user", "content": "Analyze this document..."}],
)
print(response.choices[0].message.content)
```

### Key Notes
- OpenAI-compatible — just change base_url and key.
- 20x faster token generation than GPU providers.
- $5 credits last a while for small models (Gemma, Llama-4 Scout).

---

## 7. SambaNova (Best for DeepSeek/Llama)

**Signup:** https://sambanova.ai — create account, get API key from dashboard.

### Available Models
- `DeepSeek-V3.1` — Full DeepSeek V3.1
- `Meta-Llama-3.1-8B-Instruct`
- `Meta-Llama-3.3-70B-Instruct`
- `Qwen3-72B-Instruct`

### Code Example

```python
import openai

client = openai.OpenAI(
    base_url="https://api.sambanova.ai/v1",
    api_key="YOUR_SAMBANOVA_KEY",
)

response = client.chat.completions.create(
    model="DeepSeek-V3.1",
    messages=[{"role": "user", "content": "Write a SQL query to..."}}],
    stream=True,
)
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Key Notes
- OpenAI-compatible API.
- RDU (Reconfigurable Dataflow Unit) — very fast inference.
- Free tier access with rate limits.

---

## 8. HuggingFace Inference API (Best for Open Weights)

**Signup:** https://huggingface.co/settings/tokens — create account, generate access token.

### Free Tier
- Generous free tier with monthly credits
- Additional credits for PRO users ($9/mo)
- All-in-one API: text generation, image, embeddings, NER, summarization

### Code Example

```python
import requests

API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.3-70B-Instruct"
headers = {"Authorization": "Bearer YOUR_HF_TOKEN"}

response = requests.post(
    API_URL,
    headers=headers,
    json={
        "inputs": "What is machine learning?",
        "parameters": {"max_new_tokens": 256},
    },
)
print(response.json()[0]["generated_text"])
```

### Also: OpenAI-compatible endpoint

```python
import openai

client = openai.OpenAI(
    base_url="https://api-inference.huggingface.co/v1/",
    api_key="YOUR_HF_TOKEN",
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Key Notes
- Supports thousands of open-weight models.
- Serverless — models may need to cold-start (first request may be slow).
- Router API (`https://router.huggingface.co/v1/chat/completions`) auto-selects provider.

---

## 9. Cohere (Best for Rerank + Embed)

**Signup:** https://dashboard.cohere.com — create account, get trial API key.

### Free Tier
- Trial keys: free but rate-limited
- Production keys: paid, higher limits

### Models
- `command-a` — Command A (frontier LLM)
- `command-a-reasoning` — Reasoning variant
- `embed-v4.0` — Multilingual embeddings
- `rerank-v3.5` — Reranking model

### Code Example

```python
import cohere

co = cohere.ClientV2("YOUR_COHERE_KEY")

response = co.chat(
    model="command-a",
    messages=[{"role": "user", "content": "What is the meaning of life?"}],
)
print(response.message.content[0].text)
```

### Embed + Rerank

```python
# Embeddings
embeds = co.embed(
    texts=["machine learning", "deep learning"],
    model="embed-v4.0",
    input_type="search_document",
)

# Rerank
results = co.rerank(
    model="rerank-v3.5",
    query="What is AI?",
    documents=["Artificial intelligence is...", "AI means...", "Bananas are..."],
    top_n=2,
)
```

---

## 10. Chutes.ai (Best for Open Model Streaming)

**Signup:** https://chutes.ai — create account, get API key.

### Code Example

```python
import requests

response = requests.post(
    "https://api.chutes.ai/v1/chat/completions",
    headers={
        "Authorization": "Bearer YOUR_CHUTES_KEY",
        "Content-Type": "application/json",
    },
    json={
        "model": "deepseek-ai/DeepSeek-V3.1",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": True,
    },
    stream=True,
)
for line in response.iter_lines():
    if line and line.startswith(b"data: "):
        print(line.decode()[6:])
```

---

## Unified Multi-Provider Router

Here's a Python class that tries multiple free providers with automatic fallback:

```python
import openai
import os
from typing import Optional

class FreeInferenceRouter:
    """Routes requests across free inference providers with fallback."""

    PROVIDERS = [
        {"name": "groq", "base_url": "https://api.groq.com/openai/v1",
         "key_env": "GROQ_API_KEY", "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]},
        {"name": "openrouter", "base_url": "https://openrouter.ai/api/v1",
         "key_env": "OPENROUTER_API_KEY", "models": ["openai/gpt-oss-20b:free"]},
        {"name": "nvidia", "base_url": "https://integrate.api.nvidia.com/v1",
         "key_env": "NVIDIA_API_KEY", "models": ["meta/llama-3.3-70b-instruct"]},
        {"name": "cerebras", "base_url": "https://api.cerebras.ai/v1",
         "key_env": "CEREBRAS_API_KEY", "models": ["gemma-4-31b"]},
        {"name": "sambanova", "base_url": "https://api.sambanova.ai/v1",
         "key_env": "SAMBANOVA_API_KEY", "models": ["DeepSeek-V3.1"]},
        {"name": "gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
         "key_env": "GEMINI_API_KEY", "models": ["gemini-3.6-flash"]},
    ]

    def chat(self, messages: list, preferred_provider: Optional[str] = None) -> str:
        providers = self.PROVIDERS
        if preferred_provider:
            providers = sorted(providers, key=lambda p: p["name"] != preferred_provider)

        for provider in providers:
            key = os.getenv(provider["key_env"])
            if not key:
                continue
            try:
                client = openai.OpenAI(base_url=provider["base_url"], api_key=key)
                model = provider["models"][0]
                resp = client.chat.completions.create(
                    model=model, messages=messages, max_tokens=1024,
                )
                return resp.choices[0].message.content
            except Exception as e:
                print(f"  {provider['name']} failed: {e}")
                continue
        raise RuntimeError("All providers exhausted or no API keys set.")
```

### Usage

```python
router = FreeInferenceRouter()

# Set env vars first:
# export GROQ_API_KEY=...
# export OPENROUTER_API_KEY=...
# export NVIDIA_API_KEY=...

answer = router.chat([{"role": "user", "content": "What is the speed of light?"}])
print(answer)
```

---

## Environment Variable Setup

```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENROUTER_API_KEY="sk-or-..."
export NVIDIA_API_KEY="nvapi-..."
export GEMINI_API_KEY="AIza..."
export GROQ_API_KEY="gsk_..."
export CLOUDFLARE_ACCOUNT_ID="your_account_id"
export CLOUDFLARE_API_TOKEN="cf-..."
export CEREBRAS_API_KEY="csk-..."
export SAMBANOVA_API_KEY="sm-..."
export HF_TOKEN="hf_..."
export COHERE_API_KEY="..."
export CHUTES_API_KEY="..."
```

Verify keys are set:
```bash
env | grep -E "OPENROUTER|NVIDIA|GEMINI|GROQ|CEREBRAS|SAMBANOVA|HF_TOKEN|COHERE|CHUTES|CLOUDFLARE"
```

---

## Pitfalls

1. **Free model IDs change.** OpenRouter adds/removes free models frequently. Always
   query `GET /api/v1/models` and filter for `:free` suffix.
2. **Rate limits are organization-level**, not per-key. Creating multiple keys doesn't
   multiply your quota.
3. **Gemini free tier uses your data** to improve Google products. Don't send sensitive
   data on the free tier.
4. **Cold starts on HuggingFace.** First request to an inactive model may take 30-60s.
5. **Cerebras credits run out.** $5 is generous for small models but burns fast on 70B+.
6. **Groq RPD resets at midnight UTC.** The 1,000 RPD on 70B is tight — use 8B for bulk.
7. **NVIDIA credits are one-time.** 1,000 credits don't replenish — use wisely.
8. **Cohere trial keys have strict rate limits.** ~100 requests/month on some models.
9. **Cloudflare Neurons vary by model.** A 70B model uses far more Neurons than a 7B.
10. **OpenRouter free models may queue.** During peak hours, expect delays or 429s.

---

## Choosing the Right Provider

| Use Case | Best Provider | Why |
|---|---|---|
| General chat / Q&A | Groq | Fastest, generous RPD on 8B |
| Large context (1M tokens) | NVIDIA NIM | Nemotron Ultra 550B, 1M context |
| Multimodal (image/video) | Google Gemini | Native image gen, video, TTS |
| Coding tasks | OpenRouter (Poolside/Cohere) | Free coding-specific models |
| Open-weight variety | HuggingFace | Thousands of models |
| Rerank + embeddings | Cohere | Best-in-class rerank model |
| Ultra-low latency | Groq / Cerebras | LPU / Wafer-scale hardware |
| Edge deployment | Cloudflare | Global edge network |
| DeepSeek models | SambaNova | Free DeepSeek V3.1 access |
| Fallback resilience | OpenRouter `openrouter/free` | Auto-routes to available free model |

---

## Refreshing Model Lists (Do This First)

Model lists and free tiers change frequently. Before using this skill, refresh the
data by querying provider APIs directly. See `references/provider-rate-limits.md`
for the last-known scraped data (Aug 2026) and the exact commands used.

```bash
# List OpenRouter free models (filter for :free suffix or zero pricing)
curl -s https://openrouter.ai/api/v1/models | python3 -c "
import json, sys
for m in json.load(sys.stdin)['data']:
    p = m.get('pricing', {})
    if float(p.get('prompt', '1') or '1') == 0 and float(p.get('completion', '1') or '1') == 0:
        print(m['id'])
"

# List all NVIDIA NIM models (no auth needed for model list)
curl -s https://integrate.api.nvidia.com/v1/models | python3 -c "
import json, sys
for m in json.load(sys.stdin)['data']:
    print(m['id'])
"

# Scrape provider docs for rate-limit details
curl -s -L 'https://console.groq.com/docs/rate-limits' | python3 -c '
import sys, re
html = sys.stdin.read()
text = re.sub(r\"<script[^>]*>.*?</script>\", \"\", html, flags=re.DOTALL)
text = re.sub(r\"<style[^>]*>.*?</style>\", \"\", text, flags=re.DOTALL)
text = re.sub(r\"<[^>]+>\", \" \", text)
text = re.sub(r\"\s+\", \" \", text).strip()
idx = text.find(\"Free Plan Limits\")
if idx > 0: print(text[idx:idx+2000])
'

# Scrape Google Gemini pricing
curl -s -L 'https://ai.google.dev/pricing' | python3 -c '
import sys, re
html = sys.stdin.read()
text = re.sub(r\"<script[^>]*>.*?</script>\", \"\", html, flags=re.DOTALL)
text = re.sub(r\"<style[^>]*>.*?</style>\", \"\", text, flags=re.DOTALL)
text = re.sub(r\"<[^>]+>\", \" \", text)
text = re.sub(r\"\s+\", \" \", text).strip()
idx = text.find(\"Free Tier\")
if idx > 0: print(text[idx:idx+1000])
'
```

## Verification Commands

```bash
# Test Groq connectivity
curl -s https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Say hi"}]}' | python3 -m json.tool
```

## Companion Files

- **`scripts/free_inference_router.py`** — Drop-in Python class with multi-provider fallback. Import and call `.chat()`.
- **`references/provider-rate-limits.md`** — Last-known rate limits and model lists scraped from provider docs (Aug 2026). Use as baseline; refresh with commands above.
- **Visual HTML guide** — A beautifully laid out interactive HTML page with all provider cards, code examples, and signup links. Located at `/home/vivgates/free-inference-guide/index.html`.
