"""OpenRouter adapter — unified gateway to multiple model providers."""

from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator

import httpx

from arbiterx.adapters.base import ModelAdapter
from arbiterx.router.handoff import ConversationState


class OpenRouterAdapter(ModelAdapter):
    """Adapter for OpenRouter's unified API.

    Provides access to Claude, GPT, Gemini, Llama, Mistral, and other
    models through a single API endpoint with OpenAI-compatible format.

    Example:
        >>> adapter = OpenRouterAdapter("anthropic/claude-sonnet-4-20250514")
        >>> response = await adapter.complete([{"role": "user", "content": "Hello"}])
    """

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, model_name: str = "anthropic/claude-sonnet-4-20250514", **kwargs: Any) -> None:
        api_key = kwargs.pop("api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
        super().__init__(model_name, api_key=api_key, **kwargs)
        if not self.base_url:
            self.base_url = self.DEFAULT_BASE_URL
        self.site_name: str = kwargs.get("site_name", "arbiterx")
        self.app_name: str = kwargs.get("app_name", "ArbiterX")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": f"https://github.com/neelpatel/{self.site_name}",
            "X-Title": self.app_name,
        }

    def _build_request(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> dict[str, Any]:
        """Build the OpenRouter request body (OpenAI-compatible)."""
        body: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        temperature = kwargs.get("temperature", self.temperature)
        if temperature is not None:
            body["temperature"] = temperature

        # OpenRouter-specific: route selection
        if kwargs.get("route"):
            body["route"] = kwargs["route"]

        return body

    async def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Send messages via OpenRouter and return the complete response."""
        body = self._build_request(messages, **kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""

    async def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[str]:
        """Stream response tokens from OpenRouter."""
        body = self._build_request(messages, **kwargs)
        body["stream"] = True

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=body,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload == "[DONE]":
                        break
                    try:
                        event = json.loads(payload)
                        delta = event["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    def format_messages(self, state: ConversationState) -> list[dict[str, str]]:
        """Format state for OpenRouter's API (OpenAI-compatible)."""
        messages: list[dict[str, str]] = []

        system_parts: list[str] = []
        if state.system_prompt:
            system_parts.append(state.system_prompt)
        if state.context_snippets:
            system_parts.append("## Context\n" + "\n---\n".join(state.context_snippets))
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        for msg in state.messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def count_tokens(self, text: str) -> int:
        """Estimate tokens — conservative ~4 chars per token."""
        return max(1, len(text) // 4)

    async def list_models(self) -> list[dict[str, Any]]:
        """List available models on OpenRouter."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
