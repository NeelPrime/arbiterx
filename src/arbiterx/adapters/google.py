"""Google Gemini adapter implementation."""

from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator

import httpx

from arbiterx.adapters.base import ModelAdapter
from arbiterx.router.handoff import ConversationState


class GoogleAdapter(ModelAdapter):
    """Adapter for Google's Gemini API.

    Supports Gemini 1.5 Pro, 2.0 Pro, and Flash models.

    Example:
        >>> adapter = GoogleAdapter("gemini-2.0-pro", api_key="...")
        >>> response = await adapter.complete([{"role": "user", "content": "Hello"}])
    """

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, model_name: str = "gemini-2.0-flash", **kwargs: Any) -> None:
        api_key = kwargs.pop("api_key", "") or os.environ.get("GOOGLE_AI_API_KEY", "")
        super().__init__(model_name, api_key=api_key, **kwargs)
        if not self.base_url:
            self.base_url = self.DEFAULT_BASE_URL

    def _build_request(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> dict[str, Any]:
        """Build the Gemini API request body.

        Gemini uses 'user' and 'model' roles with 'parts' content structure.
        """
        contents: list[dict[str, Any]] = []
        system_instruction: str = ""

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}],
                })

        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
            },
        }

        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        return body

    async def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Send messages to Gemini and return the complete response."""
        body = self._build_request(messages, **kwargs)
        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
        return ""

    async def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[str]:
        """Stream response tokens from Gemini."""
        body = self._build_request(messages, **kwargs)
        url = (
            f"{self.base_url}/models/{self.model_name}:streamGenerateContent"
            f"?key={self.api_key}&alt=sse"
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=body) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    try:
                        event = json.loads(payload)
                        candidates = event.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        continue

    def format_messages(self, state: ConversationState) -> list[dict[str, str]]:
        """Format state for Gemini's API.

        Gemini uses 'user'/'model' roles. System prompt goes into
        systemInstruction (handled by _build_request).
        """
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
        """Estimate tokens — Gemini uses ~4 chars per token on average."""
        return max(1, len(text) // 4)
