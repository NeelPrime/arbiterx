"""Abstract base class for all model adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from arbiterx.router.handoff import ConversationState, Message


class ModelAdapter(ABC):
    """Abstract interface for LLM provider adapters.

    All adapters must implement complete(), stream(), format_messages(),
    and count_tokens(). Subclasses handle provider-specific API formats,
    authentication, and error handling.

    Attributes:
        model_name: The identifier of the model being used.
        max_tokens: Maximum output tokens supported.
    """

    def __init__(self, model_name: str, api_key: str = "", **kwargs: Any) -> None:
        """Initialize the adapter.

        Args:
            model_name: Model identifier (e.g., "claude-sonnet-4-20250514").
            api_key: API key for authentication.
            **kwargs: Additional provider-specific configuration.
        """
        self.model_name = model_name
        self.api_key = api_key
        self.max_tokens: int = kwargs.get("max_tokens", 4096)
        self.temperature: float = kwargs.get("temperature", 0.7)
        self.base_url: str = kwargs.get("base_url", "")

    @abstractmethod
    async def complete(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> str:
        """Send messages and return a complete response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            The complete response text from the model.

        Raises:
            NotImplementedError: Subclass must implement.
        """
        ...

    @abstractmethod
    async def stream(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream response tokens as they are generated.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            **kwargs: Additional parameters.

        Yields:
            Response text chunks as they arrive.

        Raises:
            NotImplementedError: Subclass must implement.
        """
        ...

    @abstractmethod
    def format_messages(self, state: ConversationState) -> list[dict[str, str]]:
        """Convert a ConversationState into the provider's message format.

        Different providers have different conventions for system messages,
        multi-turn formatting, and metadata. This method handles those
        translations.

        Args:
            state: The conversation state to format.

        Returns:
            List of message dicts formatted for this provider's API.
        """
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string.

        Each provider may use different tokenizers. This provides a
        provider-appropriate estimate.

        Args:
            text: The text to tokenize.

        Returns:
            Estimated token count.
        """
        ...

    def _build_messages(self, state: ConversationState) -> list[dict[str, str]]:
        """Default message builder — can be overridden by subclasses.

        Combines system prompt, context snippets, and conversation messages
        into a flat list.
        """
        messages: list[dict[str, str]] = []

        # System prompt with context
        system_parts = [state.system_prompt] if state.system_prompt else []
        if state.context_snippets:
            system_parts.append("\n--- Context ---\n" + "\n---\n".join(state.context_snippets))

        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        # Conversation messages
        for msg in state.messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name!r})"
