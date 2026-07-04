"""Ollama adapter for local model inference."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from arbiterx.adapters.base import ModelAdapter
from arbiterx.router.handoff import ConversationState


class OllamaAdapter(ModelAdapter):
    """Adapter for Ollama local inference server.

    Supports any model available via Ollama's OpenAI-compatible API.
    No API key needed — runs entirely local.

    Example:
        >>> adapter = OllamaAdapter("qwen2.5-coder:7b")
        >>> response = await adapter.complete([{"role": "user", "content": "Hello"}])
    """

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(self, model_name: str = "qwen2.5-coder:7b", **kwargs: Any) -> None:
        super().__init__(model_name, api_key="", **kwargs)
        if not self.base_url:
            self.base_url = self.DEFAULT_BASE_URL

    def _build_request(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        """Build the Ollama API request body (OpenAI-compatible format)."""
        body: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
            },
        }
        return body

    async def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Send messages to Ollama and return the complete response."""
        body = self._build_request(messages, **kwargs)
        body["stream"] = False

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        return data.get("message", {}).get("content", "")

    async def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[str]:
        """Stream response tokens from Ollama."""
        body = self._build_request(messages, **kwargs)
        body["stream"] = True

        async with (
            httpx.AsyncClient(timeout=300.0) as client,
            client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=body,
            ) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    content = event.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if event.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    def format_messages(self, state: ConversationState) -> list[dict[str, str]]:
        """Format state for Ollama's API.

        Ollama supports standard system/user/assistant roles.
        """
        messages: list[dict[str, str]] = []

        system_parts: list[str] = []
        if state.system_prompt:
            system_parts.append(state.system_prompt)
        if state.context_snippets:
            system_parts.append("Context:\n" + "\n---\n".join(state.context_snippets))
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        for msg in state.messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def count_tokens(self, text: str) -> int:
        """Estimate tokens — most local models use ~4 chars per token."""
        return max(1, len(text) // 4)

    async def is_available(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[str]:
        """List available models on the Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError):
            return []
