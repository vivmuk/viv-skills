#!/usr/bin/env python3
"""
Free Inference Router — Multi-provider fallback for free LLM inference.

Set environment variables for each provider you have keys for.
The router tries providers in order and falls back on failure.

Usage:
    from free_inference_router import FreeInferenceRouter
    router = FreeInferenceRouter()
    answer = router.chat([{"role": "user", "content": "Hello!"}])
    print(answer)
"""

import os
import openai
from typing import Optional, List, Dict


class FreeInferenceRouter:
    """Routes requests across free inference providers with automatic fallback."""

    PROVIDERS = [
        {
            "name": "groq",
            "base_url": "https://api.groq.com/openai/v1",
            "key_env": "GROQ_API_KEY",
            "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
            "notes": "Fastest inference (LPU). Good free RPD limits.",
        },
        {
            "name": "openrouter",
            "base_url": "https://openrouter.ai/api/v1",
            "key_env": "OPENROUTER_API_KEY",
            "models": ["openai/gpt-oss-20b:free", "nvidia/nemotron-3-nano-30b-a3b:free"],
            "notes": "17+ free models. Auto-router available.",
        },
        {
            "name": "nvidia",
            "base_url": "https://integrate.api.nvidia.com/v1",
            "key_env": "NVIDIA_API_KEY",
            "models": ["meta/llama-3.3-70b-instruct", "nvidia/nemotron-nano-9b-v2"],
            "notes": "100+ models, 1000 free credits.",
        },
        {
            "name": "cerebras",
            "base_url": "https://api.cerebras.ai/v1",
            "key_env": "CEREBRAS_API_KEY",
            "models": ["gemma-4-31b"],
            "notes": "20x faster than GPUs. $5 free credits.",
        },
        {
            "name": "sambanova",
            "base_url": "https://api.sambanova.ai/v1",
            "key_env": "SAMBANOVA_API_KEY",
            "models": ["DeepSeek-V3.1"],
            "notes": "Fast RDU inference. DeepSeek V3.1 free.",
        },
        {
            "name": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "key_env": "GEMINI_API_KEY",
            "models": ["gemini-3.6-flash", "gemini-3.5-flash-lite"],
            "notes": "Free tokens, multimodal, image gen.",
        },
        {
            "name": "huggingface",
            "base_url": "https://api-inference.huggingface.co/v1/",
            "key_env": "HF_TOKEN",
            "models": ["meta-llama/Llama-3.3-70B-Instruct"],
            "notes": "Thousands of open-weight models.",
        },
    ]

    def __init__(self, preferred_order: Optional[List[str]] = None):
        """
        Args:
            preferred_order: List of provider names to try first (e.g. ["groq", "nvidia"]).
                             Remaining providers tried in default order after.
        """
        if preferred_order:
            ordered = []
            for name in preferred_order:
                for p in self.PROVIDERS:
                    if p["name"] == name:
                        ordered.append(p)
            for p in self.PROVIDERS:
                if p not in ordered:
                    ordered.append(p)
            self._providers = ordered
        else:
            self._providers = self.PROVIDERS

    def chat(
        self,
        messages: List[Dict],
        preferred_provider: Optional[str] = None,
        model_override: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        """
        Send a chat completion request, trying providers in order.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.
            preferred_provider: Try this provider first (e.g. "groq").
            model_override: Force a specific model ID (skips model list).
            max_tokens: Max output tokens.
            temperature: Sampling temperature.
            stream: If True, returns a generator of text chunks.

        Returns:
            Generated text (or generator if stream=True).

        Raises:
            RuntimeError: If all providers fail or no API keys are set.
        """
        providers = self._providers
        if preferred_provider:
            providers = sorted(
                providers, key=lambda p: p["name"] != preferred_provider
            )

        errors = []
        for provider in providers:
            key = os.getenv(provider["key_env"])
            if not key:
                continue

            model = model_override or provider["models"][0]

            try:
                client = openai.OpenAI(
                    base_url=provider["base_url"], api_key=key
                )

                if stream:
                    return self._stream_response(
                        client, model, messages, max_tokens, temperature
                    )

                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return resp.choices[0].message.content

            except Exception as e:
                errors.append(f"{provider['name']}: {e}")
                continue

        raise RuntimeError(
            f"All providers exhausted.\nErrors:\n" + "\n".join(errors)
        )

    def _stream_response(self, client, model, messages, max_tokens, temperature):
        """Generator that yields text chunks from streaming response."""
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        for chunk in resp:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def list_available(self) -> List[Dict]:
        """List providers that have API keys configured."""
        available = []
        for p in self._providers:
            key = os.getenv(p["key_env"])
            if key:
                available.append({
                    "name": p["name"],
                    "models": p["models"],
                    "notes": p["notes"],
                })
        return available


if __name__ == "__main__":
    # Quick test
    router = FreeInferenceRouter()

    available = router.list_available()
    print(f"Available providers: {len(available)}")
    for p in available:
        print(f"  {p['name']}: {p['models']}")

    if available:
        print("\n--- Test Request ---")
        try:
            answer = router.chat(
                [{"role": "user", "content": "Say 'Hello from free inference!' in one sentence."}],
                max_tokens=50,
            )
            print(answer)
        except RuntimeError as e:
            print(f"Error: {e}")
    else:
        print("\nNo API keys found. Set at least one of:")
        print("  GROQ_API_KEY, OPENROUTER_API_KEY, NVIDIA_API_KEY,")
        print("  CEREBRAS_API_KEY, SAMBANOVA_API_KEY, GEMINI_API_KEY, HF_TOKEN")
