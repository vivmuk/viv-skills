# Venice AI Image Model Catalog (June 2026)

Extracted from `GET /v1/models?type=image` API response. See `venice_list_models` for live data.

## Model Comparison Table

| Model | Spec Prompt Limit | Gateway Limit | Max Resolution | Aspect Ratios | Price/Gen | Best For |
|-------|-------------------|---------------|----------------|---------------|-----------|----------|
| `flux-2-max` | 3K | 1500 | 2K | 1:1, 16:9, 9:16, etc. | ~$0.04 | Best overall quality, fast iteration |
| `flux-2-pro` | 3K | 1500 | 2K | Standard | ~$0.02 | Budget quality, good balance |
| `gpt-image-2` | 10K | 1500 | 4K | 1:1, 16:9, 9:16 | ~$0.08 | Best text rendering, detailed infographics |
| `nano-banana-2` | 32K | 1500 | 2K | Standard | ~$0.005 | Fast/cheap, avatars, thumbnails |
| `nano-banana-pro` | 32K | 1500 | 2K | Standard | ~$0.01 | Better quality than nano-banana-2, same family |
| `ideogram-v4` | 10K | 1500 | 2K | Standard | ~$0.04 | Text-heavy designs, typography |
| `recraft-v4-pro` | 10K | 1500 | 2K | Standard | ~$0.04 | Professional illustration |
| `seedream-v4` | 10K | 1500 | 2K | Standard | ~$0.03 | Strong portrait generation |
| `qwen-image-2-pro` | 10K | 1500 | 2K | Standard | ~$0.03 | Good quality alternative |
| `grok-imagine` | 7.5K | 1500 | 2K | Standard | ~$0.04 | Grok ecosystem |
| `hunyuan-image-v3` | 10K | 1500 | 2K | Standard | ~$0.03 | Tencent model, solid quality |
| `gpt-image-1-5` | 10K | 1500 | 2K | Standard | ~$0.05 | Mid-range OpenAI |
| `venice-sd35` | 1.5K | 1500 | 1K | 1:1 | ~$0.01 | Batch/budget, SD3.5-based |
| `lustify-sdxl` | 1.5K | 1500 | 1K | Standard | ~$0.01 | Anime/illustration style |
| `wai-anim-xl` | 1.5K | 1500 | 1K | Standard | ~$0.01 | Anime (WAI) |

## Model Selection Guide

**For infographics / text-heavy images**: `gpt-image-2` (best text rendering, 4K resolution, but 3-5 min gen time)

**For carousels / social cards**: `flux-2-max` (fast 20-50s, good quality) for drafts → `gpt-image-2` for final hero slide only

**For avatars / thumbnails**: `nano-banana-2` (cheapest, fastest, ~10-30s)

**For batch generation**: `venice-sd35` or `nano-banana-2` (lowest cost)

## Key Parameters by Model

### gpt-image-2
- **Only accepts**: `prompt`, `model`, `n`, `response_format`, `size`
- **Does NOT accept**: `width`, `height`, `steps`, `style_preset`, `seed`, `negative_prompt`, `safe_mode`
- **Size format**: `"1024x1024"`, `"1792x1024"`, or `"4K"`
- **Response**: Returns `b64_json` by default

### nano-banana-pro
- **Does NOT support** `response_format: "b64_json"` — returns 400
- Omit `response_format` and use default URL format, or use `flux-2-max` instead

### flux-2-max / flux-2-pro
- Full parameter support: `width`, `height`, `steps`, `style_preset`, `seed`, `negative_prompt`
- `size` parameter also accepted as alternative to `width`+`height`
- Returns `b64_json` by default

## Prompt Length Workaround

All models are gateway-capped at 1500 chars. For complex infographics requiring more detail:

1. Generate a base layout with `flux-2-max` (fast, ~30s)
2. Iterate on the prompt, packing maximum information into 1499 chars
3. Final render with `gpt-image-2` for best text rendering
4. Use telegraphic style: titles > data > layout > colors — omit verbose descriptions
