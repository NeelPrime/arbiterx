"""Anthropic (Claude) adapter implementation."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

from arbiterx.adapters.base import ModelAdapter
from arbiterx.router.handoff import ConversationState


class AnthropicAdapter(ModelAdapter):
    """Adapter for Anthropic's Claude API.

    Handles the Anthropic-specific message format where system prompts
    are passed as a separate top-level parameter rather than as a message.

    Example:
        >>> adapter = AnthropicAdapter("claude-sonnet-4-20250514", api_key="sk-...")
        >>> response = await adapter.complete([{"role": "user", "content": "Hello"}])
    """

    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, model_name: str = "claude-sonnet-4-20250514", **kwargs: Any) -> None:
        api_key = kwargs.pop("api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        super().__init__(model_name, api_key=api_key, **kwargs)
        if not self.base_url:
            self.base_url = self.DEFAULT_BASE_URL
        self.api_version: str = kwargs.get("api_version", "2023-06-01")

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }

    def _build_request(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        """Build the Anthropic API request body."""
        # Separate system messages from conversation
        system_parts: list[str] = []
        api_messages: list[dict[str, str]] = []

        for msg in messages:
            if msg["role"] == "system":
                system_parts.append(msg["content"])
            else:
                api_messages.append(msg)

        body: dict[str, Any] = {
            "model": self.model_name,
            "messages": api_messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        if system_parts:
            body["system"] = "\n\n".join(system_parts)

        temperature = kwargs.get("temperature", self.temperature)
        if temperature is not None:
            body["temperature"] = temperature

        return body

    async def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Send messages to Claude and return the complete response."""
        body = self._build_request(messages, **kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self._headers(),
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        # Extract text from content blocks
        content_blocks = data.get("content", [])
        text_parts = [block["text"] for block in content_blocks if block.get("type") == "text"]
        return "\n".join(text_parts)

    async def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[str]:
        """Stream response tokens from Claude using SSE."""
        body = self._build_request(messages, **kwargs)
        body["stream"] = True

        async with (
            httpx.AsyncClient(timeout=120.0) as client,
            client.stream(
                "POST",
                f"{self.base_url}/messages",
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
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield delta.get("text", "")
                except json.JSONDecodeError:
                    continue

    def format_messages(self, state: ConversationState) -> list[dict[str, str]]:
        """Format state for Anthropic's API.

        Anthropic expects system prompt as a separate parameter, so it's
        stored in a system message that _build_request will extract.
        """
        messages: list[dict[str, str]] = []

        # System prompt
        system_parts: list[str] = []
        if state.system_prompt:
            system_parts.append(state.system_prompt)
        if state.context_snippets:
            system_parts.append(
                "<context>\n" + "\n---\n".join(state.context_snippets) + "\n</context>"
            )
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        # Conversation messages
        for msg in state.messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def count_tokens(self, text: str) -> int:
        """Estimate tokens using Claude's ~3.5 chars per token average."""
        return max(1, len(text) // 4 + len(text) % 4)
