# Ollama + llama.cpp Interop

When Ollama doesn't support a model architecture, fall back to running
llama.cpp directly alongside Ollama on a different port. This is common with
newer or less mainstream architectures.

## When to use llama.cpp instead of Ollama

Ollama supports a specific set of model architectures. If a GGUF model uses
an unsupported architecture, `ollama create` from a Modelfile or `ollama run`
will fail with an error like:

```
could not create model from GGUF: unsupported model architecture: lfm2moe
```

**Known unsupported architectures** (as of Ollama 0.30.0):
- `lfm2moe` (Liquid Foundation Models, e.g. LFM2.5-8B-A1B)
- Any architecture not in Ollama's internal model loader

**Fix:** Run the GGUF directly via llama.cpp's `llama-server` on a separate
port alongside Ollama.

## Running llama.cpp alongside Ollama

Ollama typically runs on port 11434. Run llama.cpp on a different port:

```bash
# Start llama-server on port 8081 for an unsupported model
llama-server \
    -m /path/to/model-Q4_K_M.gguf \
    --port 8081 \
    -c 4096 \
    -ngl 99 \
    --host 127.0.0.1
```

Health check:
```bash
curl -s http://localhost:8081/health
```

### OpenAI-compatible endpoint (preferred)

```bash
curl http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

### Raw completion endpoint (ChatML format)

When the model doesn't have a recognized chat template in its GGUF metadata,
use the `/completion` endpoint with manual ChatML formatting:

```bash
curl http://localhost:8081/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nHello<|im_end|>\n<|im_start|>assistant\n",
    "n_predict": 256,
    "temperature": 0.7
  }'
```

Response shape:
```json
{"content": "...", "stop": true, "timings": {"prompt_n": 18, "predicted_n": 42, ...}}
```

**When to use which endpoint:**
- `/v1/chat/completions` — works when the GGUF has a chat template in metadata
- `/completion` — raw prompt input, use when chat template is missing or broken

## Memory management on constrained hardware (16GB Mac)

On Apple Silicon with unified memory, you **cannot** run multiple large models
simultaneously. Plan your model routing around single-model-at-a-time loading.

### Ollama model management

```bash
# Check which models are currently loaded in VRAM
curl -s http://localhost:11434/api/ps

# Unload a model (free VRAM for another model)
curl -s http://localhost:11434/api/generate \
  -d '{"model":"qwen3:8b","prompt":"","keep_alive":0}'
```

`keep_alive: 0` tells Ollama to immediately unload the model. Without this,
Ollama keeps models loaded for ~5 minutes after last use.

### Memory budget example (16GB M4 Mac Mini)

| Model | VRAM | Notes |
|-------|------|-------|
| Qwen3-8B Q4_K_M | ~5.5 GB | Best tool calling, primary agent |
| Qwen3-4B Q4_K_M | ~3.1 GB | Fast, but failed tool calling |
| LFM2.5-8B-A1B Q4_K_M | ~5.1 GB | 72 tok/s, MoE (1.5B active), no tool calling |

Max two smaller models simultaneously (Qwen3-4B + LFM2.5 ≈ 8.2 GB models +
system overhead fits 16 GB). Larger models must be loaded one at a time.

### Model routing strategy for constrained hardware

When building a local agent with multiple models:

1. **Fast router model** — small model that classifies/routes requests
   (e.g., LFM2.5-8B-A1B at 72 tok/s)
2. **Primary agent model** — capable model with tool calling for actual work
   (e.g., Qwen3-8B)
3. **Fallback model** — smallest model for simple/fast tasks
   (e.g., Qwen3-4B)

Load/unload models as needed. Only keep one large model in memory at a time.

## Ollama tool calling specifics

### Qwen3 models: disable thinking mode

Qwen3 models default to "thinking" mode (chain-of-thought before response).
When using the Ollama tools API, disable thinking to get clean tool calls:

```bash
curl http://localhost:11434/api/chat \
  -d '{
    "model": "qwen3:8b",
    "messages": [{"role":"user","content":"What is the weather in SF?"}],
    "tools": [{"type":"function","function":{"name":"get_weather","parameters":{"type":"object","properties":{"location":{"type":"string"}}}}}],
    "think": false
  }'
```

Without `"think": false`, Qwen3 may output its reasoning before the tool call,
which can break tool-call parsing.

### Tool calling compatibility varies by model

Not all models support Ollama's native `tools` API:

| Model | Native tool calling | Notes |
|-------|-------------------|-------|
| Qwen3-8B | ✅ Yes | Set `"think": false` |
| Qwen3-4B | ❌ No | Generates explanation instead of tool call |
| LFM2.5-8B-A1B | ❌ No | No native support; needs prompt engineering |

For models without native tool calling, use structured output prompting or
regex-based extraction from natural language responses.

## Patching Ollama's bundled llama-server

⚠️ **macOS code-signing blocks binary swaps.** Replacing Ollama's bundled
`llama-server` with a newer one from Homebrew or another source will fail
with `Killed: 9` (code-signing violation). macOS enforces signature checks
on binaries; a Homebrew-compiled binary placed into the Ollama cellar
directory will be killed on launch. **Do not attempt this approach.**

Instead, use one of these two working alternatives:

### Alternative 1: Run llama-server directly (recommended)

Skip Ollama entirely and serve the GGUF with brew's `llama-server`:

```bash
# Brew's llama.cpp is always up-to-date and properly signed
llama-server -m /path/to/model-Q4_K_M.gguf --port 8081 -c 4096 -ngl 99
```

### Alternative 2: Manually register a pre-converted GGUF in Ollama

When `ollama create` fails because its internal `llama-quantize` doesn't
support the architecture, you can bypass validation by constructing the
manifest and blobs yourself. The model will appear in `ollama list` and
`ollama run`, but **it will still fail at inference time** if Ollama's
bundled `llama-server` doesn't support the architecture. This is only
useful if the GGUF's architecture IS supported by Ollama's runtime but
the `llama-quantize` validation step is the sole blocker.

**Steps:**

1. Download a pre-converted GGUF from HuggingFace (e.g., official
   `LiquidAI/LFM2.5-8B-A1B-GGUF` repo)
2. Compute the SHA256 and place it as a blob:
   ```bash
   SHA256=$(shasum -a 256 model.gguf | cut -d' ' -f1)
   cp model.gguf ~/.ollama/models/blobs/sha256-$SHA256
   ```
3. Create supporting blobs (template, params, config) and compute their
   SHA256 + size
4. Write the manifest JSON to the right path:
   ```
   ~/.ollama/models/manifests/registry.ollama.ai/<namespace>/<model>/latest
   ```
   The `ollama list` tag becomes `<namespace>/<model>:latest`.
5. The model now appears in `ollama list`

**Manifest format** (must match Docker v2 manifest schema):
```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
  "config": {
    "mediaType": "application/vnd.docker.container.image.v1+json",
    "digest": "sha256-<config_blob_sha>",
    "size": <config_blob_size>
  },
  "layers": [
    {"mediaType":"application/vnd.ollama.image.model","digest":"sha256-<gguf_sha>","size":<gguf_size>},
    {"mediaType":"application/vnd.ollama.image.template","digest":"sha256-<template_sha>","size":<template_size>},
    {"mediaType":"application/vnd.ollama.image.params","digest":"sha256-<params_sha>","size":<params_size>}
  ]
}
```

**Key insight:** Ollama v0.30 bundles `llama-server` version 1 (ancient) while
brew's `llama.cpp` ships version 9430+. The version gap is the root cause of
unsupported architectures. Check with `llama-server --version` on each.

## Chat format for LFM2.5 models

LFM2.5 uses **ChatML** format (confirmed from `tokenizer_config.json`):
- BOS: `<|startoftext|>`
- EOS: `<|im_end|>`
- Stop token: `<|im_end|>`
- Template: `<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{response}<|im_end|>`

Use this when serving LFM2.5 GGUFs via `llama-server` with the `/completion`
endpoint, or when constructing Ollama template blobs.
