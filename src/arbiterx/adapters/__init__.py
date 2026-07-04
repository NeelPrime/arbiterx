"""Model adapters for LLM providers."""

from arbiterx.adapters.anthropic import AnthropicAdapter
from arbiterx.adapters.base import ModelAdapter
from arbiterx.adapters.google import GoogleAdapter
from arbiterx.adapters.ollama import OllamaAdapter
from arbiterx.adapters.openai import OpenAIAdapter
from arbiterx.adapters.openrouter import OpenRouterAdapter

__all__ = [
    "ModelAdapter",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "GoogleAdapter",
    "OllamaAdapter",
    "OpenRouterAdapter",
]

# Registry for adapter lookup by provider name
ADAPTER_REGISTRY: dict[str, type[ModelAdapter]] = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAIAdapter,
    "google": GoogleAdapter,
    "ollama": OllamaAdapter,
    "openrouter": OpenRouterAdapter,
}


def get_adapter(provider: str, model_name: str, **kwargs) -> ModelAdapter:
    """Factory function to get an adapter by provider name.

    Args:
        provider: Provider identifier (anthropic, openai, google, ollama, openrouter).
        model_name: Model name to use.
        **kwargs: Additional configuration for the adapter.

    Returns:
        An initialized ModelAdapter instance.

    Raises:
        ValueError: If the provider is not registered.
    """
    adapter_cls = ADAPTER_REGISTRY.get(provider)
    if adapter_cls is None:
        available = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
        raise ValueError(f"Unknown provider '{provider}'. Available: {available}")
    return adapter_cls(model_name, **kwargs)
