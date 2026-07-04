"""Tests for model adapter instantiation and format_messages."""

from __future__ import annotations

import pytest

from arbiterx.adapters import (
    ADAPTER_REGISTRY,
    AnthropicAdapter,
    GoogleAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
    get_adapter,
)
from arbiterx.adapters.base import ModelAdapter
from arbiterx.router.handoff import ConversationState, Message


class TestAdapterInstantiation:
    """Tests that all adapters can be instantiated without errors."""

    def test_anthropic_adapter_instantiates(self) -> None:
        """AnthropicAdapter should instantiate with a model name."""
        adapter = AnthropicAdapter("claude-sonnet-4-20250514", api_key="test-key")
        assert isinstance(adapter, ModelAdapter)
        assert adapter.model_name == "claude-sonnet-4-20250514"

    def test_openai_adapter_instantiates(self) -> None:
        """OpenAIAdapter should instantiate with a model name."""
        adapter = OpenAIAdapter("gpt-4o", api_key="test-key")
        assert isinstance(adapter, ModelAdapter)
        assert adapter.model_name == "gpt-4o"

    def test_google_adapter_instantiates(self) -> None:
        """GoogleAdapter should instantiate with a model name."""
        adapter = GoogleAdapter("gemini-2.0-flash", api_key="test-key")
        assert isinstance(adapter, ModelAdapter)
        assert adapter.model_name == "gemini-2.0-flash"

    def test_ollama_adapter_instantiates(self) -> None:
        """OllamaAdapter should instantiate with a model name (no API key)."""
        adapter = OllamaAdapter("qwen2.5-coder:7b")
        assert isinstance(adapter, ModelAdapter)
        assert adapter.model_name == "qwen2.5-coder:7b"

    def test_openrouter_adapter_instantiates(self) -> None:
        """OpenRouterAdapter should instantiate with a model name."""
        adapter = OpenRouterAdapter("anthropic/claude-sonnet-4-20250514", api_key="test-key")
        assert isinstance(adapter, ModelAdapter)
        assert adapter.model_name == "anthropic/claude-sonnet-4-20250514"


class TestGetAdapterFactory:
    """Tests for the get_adapter factory function."""

    def test_get_adapter_anthropic(self) -> None:
        """get_adapter('anthropic', ...) should return an AnthropicAdapter."""
        adapter = get_adapter("anthropic", "claude-sonnet-4-20250514", api_key="test-key")
        assert isinstance(adapter, AnthropicAdapter)

    def test_get_adapter_openai(self) -> None:
        """get_adapter('openai', ...) should return an OpenAIAdapter."""
        adapter = get_adapter("openai", "gpt-4o", api_key="test-key")
        assert isinstance(adapter, OpenAIAdapter)

    def test_get_adapter_google(self) -> None:
        """get_adapter('google', ...) should return a GoogleAdapter."""
        adapter = get_adapter("google", "gemini-2.0-flash", api_key="test-key")
        assert isinstance(adapter, GoogleAdapter)

    def test_get_adapter_ollama(self) -> None:
        """get_adapter('ollama', ...) should return an OllamaAdapter."""
        adapter = get_adapter("ollama", "llama3")
        assert isinstance(adapter, OllamaAdapter)

    def test_get_adapter_openrouter(self) -> None:
        """get_adapter('openrouter', ...) should return an OpenRouterAdapter."""
        adapter = get_adapter(
            "openrouter", "anthropic/claude-sonnet-4-20250514", api_key="test-key"
        )
        assert isinstance(adapter, OpenRouterAdapter)

    def test_get_adapter_unknown_raises(self) -> None:
        """get_adapter with unknown provider should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_adapter("nonexistent_provider", "some-model")

    def test_adapter_registry_has_all_providers(self) -> None:
        """ADAPTER_REGISTRY should contain all 5 expected providers."""
        expected = {"anthropic", "openai", "google", "ollama", "openrouter"}
        assert expected.issubset(set(ADAPTER_REGISTRY.keys()))


class TestFormatMessages:
    """Tests for format_messages output structure."""

    @pytest.fixture
    def conversation_state(self) -> ConversationState:
        """Create a sample ConversationState for testing."""
        state = ConversationState(
            system_prompt="You are a helpful assistant.",
            context_snippets=["File: main.py\ndef hello(): pass"],
            messages=[
                Message(role="user", content="What does hello() do?"),
                Message(role="assistant", content="It's a no-op function."),
                Message(role="user", content="Can you improve it?"),
            ],
        )
        return state

    def test_anthropic_format_messages(self, conversation_state: ConversationState) -> None:
        """AnthropicAdapter.format_messages should produce system + user/assistant messages."""
        adapter = AnthropicAdapter("claude-sonnet-4-20250514", api_key="test-key")
        messages = adapter.format_messages(conversation_state)

        assert isinstance(messages, list)
        assert len(messages) > 0
        # First should be system message
        assert messages[0]["role"] == "system"
        assert "helpful assistant" in messages[0]["content"]
        # Should include conversation messages
        roles = [m["role"] for m in messages[1:]]
        assert "user" in roles
        assert "assistant" in roles

    def test_openai_format_messages(self, conversation_state: ConversationState) -> None:
        """OpenAIAdapter.format_messages should include system message in list."""
        adapter = OpenAIAdapter("gpt-4o", api_key="test-key")
        messages = adapter.format_messages(conversation_state)

        assert isinstance(messages, list)
        assert messages[0]["role"] == "system"
        # Should have system + 3 conversation messages = 4 total
        assert len(messages) == 4

    def test_google_format_messages(self, conversation_state: ConversationState) -> None:
        """GoogleAdapter.format_messages should produce messages with system role."""
        adapter = GoogleAdapter("gemini-2.0-flash", api_key="test-key")
        messages = adapter.format_messages(conversation_state)

        assert isinstance(messages, list)
        assert len(messages) > 0
        # System message present
        system_msgs = [m for m in messages if m["role"] == "system"]
        assert len(system_msgs) == 1

    def test_ollama_format_messages(self, conversation_state: ConversationState) -> None:
        """OllamaAdapter.format_messages should produce standard message list."""
        adapter = OllamaAdapter("qwen2.5-coder:7b")
        messages = adapter.format_messages(conversation_state)

        assert isinstance(messages, list)
        assert messages[0]["role"] == "system"
        # Verify context is included in system message
        assert "main.py" in messages[0]["content"]

    def test_openrouter_format_messages(self, conversation_state: ConversationState) -> None:
        """OpenRouterAdapter.format_messages should produce OpenAI-compatible format."""
        adapter = OpenRouterAdapter("anthropic/claude-sonnet-4-20250514", api_key="test-key")
        messages = adapter.format_messages(conversation_state)

        assert isinstance(messages, list)
        assert messages[0]["role"] == "system"
        assert len(messages) == 4

    def test_format_messages_empty_state(self) -> None:
        """format_messages with empty state should not crash."""
        adapter = OpenAIAdapter("gpt-4o", api_key="test-key")
        state = ConversationState()
        messages = adapter.format_messages(state)
        assert isinstance(messages, list)


class TestCountTokens:
    """Tests for count_tokens estimation."""

    @pytest.mark.parametrize(
        "adapter_cls,model_name",
        [
            (AnthropicAdapter, "claude-sonnet-4-20250514"),
            (OpenAIAdapter, "gpt-4o"),
            (GoogleAdapter, "gemini-2.0-flash"),
            (OllamaAdapter, "qwen2.5-coder:7b"),
            (OpenRouterAdapter, "anthropic/claude-sonnet-4-20250514"),
        ],
    )
    def test_count_tokens_returns_positive_int(
        self, adapter_cls: type[ModelAdapter], model_name: str
    ) -> None:
        """count_tokens should return a positive integer for non-empty text."""
        adapter = (
            adapter_cls(model_name, api_key="test-key")
            if adapter_cls != OllamaAdapter
            else adapter_cls(model_name)
        )
        result = adapter.count_tokens("Hello, this is a test string with some words.")
        assert isinstance(result, int)
        assert result > 0

    @pytest.mark.parametrize(
        "adapter_cls,model_name",
        [
            (AnthropicAdapter, "claude-sonnet-4-20250514"),
            (OpenAIAdapter, "gpt-4o"),
            (GoogleAdapter, "gemini-2.0-flash"),
            (OllamaAdapter, "qwen2.5-coder:7b"),
            (OpenRouterAdapter, "anthropic/claude-sonnet-4-20250514"),
        ],
    )
    def test_count_tokens_reasonable_estimate(
        self, adapter_cls: type[ModelAdapter], model_name: str
    ) -> None:
        """Token count for a ~100-char string should be roughly 20-50 tokens."""
        adapter = (
            adapter_cls(model_name, api_key="test-key")
            if adapter_cls != OllamaAdapter
            else adapter_cls(model_name)
        )
        text = "The quick brown fox jumps over the lazy dog. " * 3  # ~135 chars
        result = adapter.count_tokens(text)
        # Rough heuristic: should be between 10 and 100 for ~135 chars
        assert 10 <= result <= 100

    def test_count_tokens_minimum_one(self) -> None:
        """count_tokens should return at least 1 even for very short text."""
        adapter = OpenAIAdapter("gpt-4o", api_key="test-key")
        result = adapter.count_tokens("hi")
        assert result >= 1
