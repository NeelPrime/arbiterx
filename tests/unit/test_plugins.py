"""Tests for the plugin system."""

from __future__ import annotations

import pytest

from arbiterx.adapters import ADAPTER_REGISTRY, ModelAdapter
from arbiterx.plugins import PluginLoader, register_adapter, register_routing_rule


class TestRegisterAdapter:
    """Tests for register_adapter adding to ADAPTER_REGISTRY."""

    def test_register_adapter_adds_to_registry(self) -> None:
        """register_adapter should add a new entry to ADAPTER_REGISTRY."""

        class FakeAdapter(ModelAdapter):
            async def complete(self, messages, **kwargs):
                return ""

            async def stream(self, messages, **kwargs):
                yield ""

            def format_messages(self, state):
                return []

            def count_tokens(self, text):
                return 0

        register_adapter("test-fake-provider", FakeAdapter)

        assert "test-fake-provider" in ADAPTER_REGISTRY
        assert ADAPTER_REGISTRY["test-fake-provider"] is FakeAdapter

        # Cleanup
        del ADAPTER_REGISTRY["test-fake-provider"]

    def test_register_adapter_overwrites_existing(self) -> None:
        """register_adapter should overwrite an existing entry for the same name."""

        class AdapterV1(ModelAdapter):
            async def complete(self, messages, **kwargs):
                return ""

            async def stream(self, messages, **kwargs):
                yield ""

            def format_messages(self, state):
                return []

            def count_tokens(self, text):
                return 0

        class AdapterV2(ModelAdapter):
            async def complete(self, messages, **kwargs):
                return ""

            async def stream(self, messages, **kwargs):
                yield ""

            def format_messages(self, state):
                return []

            def count_tokens(self, text):
                return 0

        register_adapter("test-overwrite-provider", AdapterV1)
        register_adapter("test-overwrite-provider", AdapterV2)

        assert ADAPTER_REGISTRY["test-overwrite-provider"] is AdapterV2

        # Cleanup
        del ADAPTER_REGISTRY["test-overwrite-provider"]


class TestRegisterRoutingRule:
    """Tests for register_routing_rule adding to _CUSTOM_RULES."""

    def test_register_routing_rule_adds_to_list(self) -> None:
        """register_routing_rule should append to _CUSTOM_RULES."""
        from arbiterx.router.table import _CUSTOM_RULES

        initial_count = len(_CUSTOM_RULES)

        rule = {"match": {"type": "security"}, "model": "claude-opus", "fallback": "gpt-4o"}
        register_routing_rule(rule)

        assert len(_CUSTOM_RULES) == initial_count + 1
        assert _CUSTOM_RULES[-1] is rule

        # Cleanup
        _CUSTOM_RULES.pop()

    def test_register_routing_rule_preserves_existing(self) -> None:
        """Registering a new rule should not remove existing rules."""
        from arbiterx.router.table import _CUSTOM_RULES

        initial_count = len(_CUSTOM_RULES)

        rule1 = {"match": {"type": "code"}, "model": "gpt-4o"}
        rule2 = {"match": {"type": "math"}, "model": "o1"}

        register_routing_rule(rule1)
        register_routing_rule(rule2)

        assert len(_CUSTOM_RULES) == initial_count + 2

        # Cleanup
        _CUSTOM_RULES.pop()
        _CUSTOM_RULES.pop()


class TestPluginLoader:
    """Tests for PluginLoader instantiation and basic behavior."""

    def test_plugin_loader_instantiates(self) -> None:
        """PluginLoader should instantiate without errors."""
        loader = PluginLoader()
        assert isinstance(loader, PluginLoader)

    def test_plugin_loader_with_dirs(self, tmp_path) -> None:
        """PluginLoader should accept plugin directory paths."""
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()

        loader = PluginLoader(plugin_dirs=[str(plugin_dir)])
        assert len(loader.plugin_dirs) == 1

    def test_plugin_loader_discover_empty_dir(self, tmp_path) -> None:
        """Discovering in an empty directory should return empty list."""
        plugin_dir = tmp_path / "empty_plugins"
        plugin_dir.mkdir()

        loader = PluginLoader(plugin_dirs=[str(plugin_dir)], auto_discover=False)
        discovered = loader.discover()
        assert discovered == []

    def test_plugin_loader_registry_initially_empty(self) -> None:
        """A fresh PluginLoader should have no active plugins."""
        loader = PluginLoader(auto_discover=False)
        loader.discover()
        assert len(loader.registry.active_plugins) == 0

    def test_plugin_loader_discover_finds_plugin_file(self, tmp_path) -> None:
        """PluginLoader should discover a valid plugin file."""
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()

        plugin_file = plugin_dir / "sample_plugin.py"
        plugin_file.write_text('''\
"""A sample plugin."""

__version__ = "1.0.0"


class SamplePlugin:
    name = "sample"
    version = "1.0.0"

    def activate(self):
        pass

    def deactivate(self):
        pass
''')

        loader = PluginLoader(plugin_dirs=[str(plugin_dir)], auto_discover=False)
        discovered = loader.discover()

        assert len(discovered) == 1
        assert discovered[0].name == "sample_plugin"
        assert discovered[0].version == "1.0.0"
