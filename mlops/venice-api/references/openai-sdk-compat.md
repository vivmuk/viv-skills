# Venice API — OpenAI SDK Compatibility Notes

Tested with `openai` Python SDK v1.x pointing at
`https://api.venice.ai/api/v1` as the base URL.

## Issue 1: `venice_parameters` rejected as unknown kwarg

**Error:**
```
TypeError: AsyncCompletions.create() got an unexpected keyword argument 'venice_parameters'
```

**Cause:** The OpenAI SDK validates keyword arguments against its typed
schema. `venice_parameters` is not part of the OpenAI API spec, so the
SDK rejects it before the request is even sent.

**Fix:** Pass Venice-specific parameters via the `extra_body` dict. The SDK
sends `extra_body` keys as-is in the JSON body without validation.

```python
resp = await client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
    temperature=0.3,
    extra_body={
        "venice_parameters": {"include_venice_system_prompt": False}
    },
)
```

This works for both `client.chat.completions.create()` and
`client.chat.completions.create()` with `response_format={"type": "json_object"}`.

## Issue 2: `max_tokens=None` serializes to `null`, causes 400

**Error:**
```
BadRequestError: Error code: 400
{"message": "'max_completion_tokens' must be an integer and at least 1", ...}
```

(or similar depending on the model — some Venice models reject `null` for
`max_tokens` while OpenAI's own API accepts it)

**Fix:** Only include `max_tokens` in the request when it has a real value:

```python
kwargs = dict(model=model, messages=messages, temperature=temperature)
if max_tokens is not None:
    kwargs["max_tokens"] = max_tokens
resp = await client.chat.completions.create(**kwargs, extra_body=extra_body)
```

## Issue 3: Content filtering on scraped web text

**Error:**
```
BadRequestError: Error code: 400
{"error": "Input text data may contain inappropriate content.", ...}
```

**Cause:** Models like `deepseek-v4-pro` have an input-side content safety
filter. When a pipeline scrapes arbitrary web pages and feeds the raw text
as user message content, the filter can flag innocuous content.

**Fix:** Pass `venice_parameters: {include_venice_system_prompt: false}` via
`extra_body`. This disables the Venice-injected system prompt that enables
the safety filter.

Note: This only affects the input filter, not output generation. For
uncensored output, use models with `nsfw=True` or `venice-uncensored-*`
models.

## Tested Models (2026-05-27)

| Model | Context | `max_tokens=None` OK? | Content filter? | Notes |
|-------|---------|----------------------|-----------------|-------|
| `deepseek-v4-pro` | 1M | ❌ (400 error) | ✅ Has filter | Best for reasoning |
| `deepseek-v4-flash` | 1M | Not tested | Likely same | Cheaper/faster |
| `gemma-4-uncensored` | 256K | Not tested | No filter | Uncensored |
| `nano-banana-2` | N/A | N/A (image model) | N/A | Image gen |
