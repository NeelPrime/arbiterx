"""OpenAI adapter implementation."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

from arbiterx.adapters.base import ModelAdapter
from arbiterx.router.handoff import ConversationState


class OpenAIAdapter(ModelAdapter):
    """Adapter for OpenAI's Chat Completions API.

    Supports GPT-4o, GPT-4o-mini, o1, o3, and other OpenAI models.

    Example:
        >>> adapter = OpenAIAdapter("gpt-4o", api_key="sk-...")
        >>> response = await adapter.complete([{"role": "user", "content": "Hello"}])
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(self, model_name: str = "gpt-4o", **kwargs: Any) -> None:
        api_key = kwargs.pop("api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        super().__init__(model_name, api_key=api_key, **kwargs)
        if not self.base_url:
            self.base_url = self.DEFAULT_BASE_URL

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_request(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        """Build the OpenAI API request body."""
        body: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        temperature = kwargs.get("temperature", self.temperature)
        if temperature is not None:
            body["temperature"] = temperature

        return body

    async def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Send messages and return the complete response."""
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
        """Stream response tokens using SSE."""
        body = self._build_request(messages, **kwargs)
        body["stream"] = True

        async with (
            httpx.AsyncClient(timeout=120.0) as client,
            client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=body,
            ) as response,
        ):
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
        """Format state for OpenAI's Chat Completions API.

        OpenAI natively supports system messages in the messages array.
        """
        messages: list[dict[str, str]] = []

        # System prompt with context
        system_parts: list[str] = []
        if state.system_prompt:
            system_parts.append(state.system_prompt)
        if state.context_snippets:
            system_parts.append("## Context\n" + "\n---\n".join(state.context_snippets))
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        # Conversation messages
        for msg in state.messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def count_tokens(self, text: str) -> int:
        """Estimate tokens using GPT's ~4 chars per token average."""
        return max(1, len(text) // 4)
