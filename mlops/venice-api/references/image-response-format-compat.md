# Image Model `response_format` Compatibility

Learned from live API testing (June 2026). Not all Venice image models support the `response_format` parameter.

## Model Compatibility

| Model | `response_format: "b64_json"` | `response_format: "url"` | Default (omit) |
|-------|-------------------------------|--------------------------|----------------|
| `flux-2-max` | ✅ Works | ✅ Works | Returns b64_json |
| `flux-2-pro` | ✅ Works | ✅ Works | Returns b64_json |
| `gpt-image-2` | ✅ Works | ✅ Works | Returns b64_json |
| `nano-banana-pro` | ❌ **400 error** | Not tested | Returns URL format |
| `nano-banana-2` | ❌ Likely fails | Not tested | Returns URL format |
| `grok-imagine-image-quality` | N/A (different schema) | N/A | Returns `images[]` as plain b64 strings. Rejects `response_format` param |
| `qwen-image-2-pro` | Not tested | Not tested | Unknown |

## The Problem

When calling `POST /v1/images/generations` with `response_format: "b64_json"` on unsupported models like `nano-banana-pro`, the API returns:

```
HTTP 400 Bad Request
```

No detailed error body is returned — just the status code.

## Fix

Omit `response_format` entirely when using `nano-banana-pro` or `nano-banana-2`. The default response format for these models returns image URLs instead of base64 data. If you need base64, download from the URL and encode manually, or switch to `flux-2-max` which supports `b64_json`.

```python
# ❌ Fails on nano-banana-pro
payload = {"model": "nano-banana-pro", "prompt": "...", "response_format": "b64_json"}

# ✅ Works — omit response_format
payload = {"model": "nano-banana-pro", "prompt": "...", "size": "1024x1024"}
```

## `grok-imagine-image-quality` — Unique Response Format

This model has a **different response schema** from all other Venice image models. It does NOT use the standard `data[].b64_json` format.

### Response structure

```json
{
  "id": "...",
  "images": ["<plain-base64-string>", ...],
  "request": {...},
  "timing": {...}
}
```

Key differences:
- **Top-level key is `images`** (not `data`)
- **Each entry is a plain base64 string** (not an object with `b64_json` or `url` keys)
- No `revised_prompt` field

### Parsing code

```python
result = json.loads(resp.read())

# Standard models (flux, gpt-image, nano-banana)
if "data" in result:
    img_data = result["data"][0]
    b64 = img_data.get("b64_json") or img_data.get("url")
# grok-imagine-image-quality
elif "images" in result:
    b64 = result["images"][0]  # plain base64 string

if isinstance(b64, str) and b64.startswith("http"):
    img_bytes = urllib.request.urlopen(b64).read()
else:
    img_bytes = base64.b64decode(b64)
```

### Rejected parameters

The following params cause HTTP 400 on `grok-imagine-image-quality`:
- `resolution` (e.g. "4K")
- `cfg_scale`
- `steps`
- `style_preset`
- `seed`

**Only these params work**: `model`, `prompt`, `aspect_ratio`, `format`, `hide_watermark`, `safe_mode`

### When to use

Good for data-heavy infographic slides. Quality is competitive with flux-2-max for chart/diagram prompts. Does NOT render text in images as well as gpt-image-2.

## Detection Strategy

If you get a 400 from an image generation call and the prompt/size params are valid, try removing `response_format` and retry. This is the most likely cause for models outside the Flux/GPT families.

For `grok-imagine-image-quality`, also remove `resolution`, `cfg_scale`, `steps`, `style_preset`, and `seed` — these cause 400s even with valid prompt/size.
