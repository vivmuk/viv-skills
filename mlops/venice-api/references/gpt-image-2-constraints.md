# Venice Image API — Gateway-Level Constraints

Learned from live API testing (June 2026). These apply to ALL image models, not just gpt-image-2.

## ⚠️ 1500-Char Prompt Limit (ALL Models)

The Venice API gateway validates the `prompt` field at a **maximum of 1500 characters** for every image model, regardless of what the model spec advertises. This was confirmed by testing:

- 1499 chars → ✅ accepted
- 1501 chars → ❌ rejected with `"String must contain at most 1500 character(s)"`

This applies even to models whose specs show much higher limits:

| Model | Spec Limit | Gateway Reality |
|-------|-----------|-----------------|
| `gpt-image-2` | 10,000 | 1500 |
| `nano-banana-2` | 32,768 | 1500 |
| `nano-banana-pro` | 32,768 | 1500 |
| `flux-2-max` | 3,000 | 1500 |
| `flux-2-pro` | 3,000 | 1500 |
| `ideogram-v4` | 10,000 | 1500 |
| `recraft-v4-pro` | 10,000 | 1500 |
| `seedream-v4` | 10,000 | 1500 |
| `qwen-image-2-pro` | 10,000 | 1500 |
| `grok-imagine` | 7,500 | 1500 |
| `venice-sd35` | 1,500 | 1500 |

This is a gateway-level validation, not a model limitation. When Venice removes this gateway cap, the model-spec limits will apply automatically.

## gpt-image-2 Specific Constraints

Beyond the shared 1500-char prompt limit, gpt-image-2 has additional restrictions:

### Accepted Parameters Only

| Parameter   | Accepted | Notes |
|-------------|----------|-------|
| `prompt`    | ✅       | Max 1500 chars (gateway cap) |
| `model`     | ✅       | `"gpt-image-2"` |
| `n`         | ✅       | Number of images |
| `response_format` | ✅ | `"b64_json"` or `"url"` |
| `size`      | ✅       | e.g. `"1024x1024"`, `"1792x1024"`. Supports `"4K"` resolution |
| `width`     | ❌       | Returns `"Unrecognized key(s) in object: 'width'"` |
| `height`    | ❌       | Returns `"Unrecognized key(s) in object: 'height'"` |
| `steps`     | ❌       | Not accepted |
| `style_preset` | ❌    | Not accepted |
| `seed`      | ❌       | Not accepted |
| `negative_prompt` | ❌ | Not accepted |
| `safe_mode` | ❌       | Not accepted |

### Minimal Working Request

```json
{
  "prompt": "A professional infographic about...",
  "model": "gpt-image-2",
  "n": 1,
  "size": "1024x1024",
  "response_format": "b64_json"
}
```

## Prompt Packing Strategy (1500 chars)

With only 1500 chars, craft prompts that prioritize:
- Overall composition and layout description
- Key section titles and data points (verbatim in prompt)
- Color scheme and style direction (hex codes)

Avoid:
- Verbose descriptions of every detail
- Long lists that exceed the limit
- Redundant style instructions
- Full paragraphs — use telegraphic style

## Error Response Shape

```json
{
  "details": {
    "_errors": ["Unrecognized key(s) in object: 'width', 'height'"],
    "prompt": {
      "_errors": ["String must contain at most 1500 character(s)"]
    }
  },
  "issues": [
    {"code": "too_big", "maximum": 1500, "type": "string", ...},
    {"code": "unrecognized_keys", "keys": ["width", "height"], ...}
  ]
}
```

## Timeout

- `gpt-image-2`: Set timeout ≥300s. Can take up to 5 minutes for complex scenes.
- `flux-2-max`: Usually completes in 20-50s. Timeout of 120s is sufficient.
- `nano-banana-2`: Usually completes in 10-30s.
