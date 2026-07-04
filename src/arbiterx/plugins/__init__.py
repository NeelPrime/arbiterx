"""Plugin system for extending ArbiterX with custom models and routing rules.

Extension Points:
    - Custom model adapters (register via `register_adapter`)
    - Custom routing rules (register via `register_routing_rule`)
    - Custom task classifiers (register via `register_classifier`)

Example plugin file (my_plugin.py):
    from arbiterx.plugins import ArbiterXPlugin, register_adapter
    from arbiterx.adapters.base import ModelAdapter

    class MyCustomAdapter(ModelAdapter):
        ...

    class Plugin(ArbiterXPlugin):
        name = "my-plugin"
        version = "1.0.0"

        def activate(self):
            register_adapter("my-provider", MyCustomAdapter)

        def deactivate(self):
            pass
"""

from arbiterx.plugins.loader import ArbiterXPlugin, PluginInfo, PluginLoader, PluginRegistry

__all__ = [
    "ArbiterXPlugin",
    "PluginInfo",
    "PluginLoader",
    "PluginRegistry",
    "register_adapter",
    "register_routing_rule",
    "register_classifier",
]


def register_adapter(provider_name: str, adapter_cls: type) -> None:
    """Register a custom model adapter.

    Args:
        provider_name: Unique identifier for the provider (e.g., "my-model").
        adapter_cls: A class extending ModelAdapter.
    """
    from arbiterx.adapters import ADAPTER_REGISTRY

    ADAPTER_REGISTRY[provider_name] = adapter_cls


def register_routing_rule(rule: dict) -> None:
    """Register a custom routing rule.

    Args:
        rule: A dict with 'match' conditions and 'model' target.
              Example: {"match": {"type": "security"}, "model": "opus", "fallback": "o1"}
    """
    from arbiterx.router.table import _CUSTOM_RULES

    _CUSTOM_RULES.append(rule)


def register_classifier(name: str, classifier_fn) -> None:
    """Register a custom task classifier function.

    Args:
        name: Name for the classifier.
        classifier_fn: A callable that takes (task: str) -> dict with keys:
                      task_type, complexity, context_scope.
    """
    from arbiterx.router.classifier import _CUSTOM_CLASSIFIERS

    _CUSTOM_CLASSIFIERS[name] = classifier_fn
