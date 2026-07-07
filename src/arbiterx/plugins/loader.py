"""Plugin loader that discovers and loads plugins from directories and entry_points."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class ArbiterXPlugin(Protocol):
    """Protocol that all arbiterx plugins must satisfy."""

    name: str
    version: str

    def activate(self) -> None:
        """Called when the plugin is loaded and activated."""
        ...

    def deactivate(self) -> None:
        """Called when the plugin is being unloaded."""
        ...


@dataclass
class PluginInfo:
    """Metadata about a discovered plugin."""

    name: str
    version: str
    module_path: str
    source: str  # "directory", "entry_point", "explicit"
    is_active: bool = False
    error: str | None = None


@dataclass
class PluginRegistry:
    """Registry of all discovered and loaded plugins."""

    plugins: dict[str, PluginInfo] = field(default_factory=dict)
    instances: dict[str, Any] = field(default_factory=dict)

    @property
    def active_plugins(self) -> list[PluginInfo]:
        """Return all currently active plugins."""
        return [p for p in self.plugins.values() if p.is_active]

    @property
    def failed_plugins(self) -> list[PluginInfo]:
        """Return plugins that failed to load."""
        return [p for p in self.plugins.values() if p.error is not None]


class PluginLoader:
    """Discovers and loads arbiterx plugins.

    Plugins can be loaded from:
    1. A local plugins directory (Python modules with a Plugin class)
    2. Installed packages via entry_points (group: 'arbiterx.plugins')
    3. Explicit module paths

    Example:
        >>> loader = PluginLoader(plugin_dirs=["./plugins"])
        >>> loader.discover()
        >>> loader.load_all()
        >>> for plugin in loader.registry.active_plugins:
        ...     print(plugin.name)
    """

    ENTRY_POINT_GROUP = "arbiterx.plugins"

    def __init__(
        self,
        plugin_dirs: list[str] | None = None,
        auto_discover: bool = True,
    ) -> None:
        """Initialize the plugin loader.

        Args:
            plugin_dirs: List of directory paths to scan for plugins.
            auto_discover: Whether to also check entry_points.
        """
        self.plugin_dirs: list[Path] = []
        if plugin_dirs:
            self.plugin_dirs = [Path(d) for d in plugin_dirs]

        self.auto_discover = auto_discover
        self.registry = PluginRegistry()

    def discover(self) -> list[PluginInfo]:
        """Discover all available plugins from configured sources.

        Returns:
            List of discovered PluginInfo objects.
        """
        discovered: list[PluginInfo] = []

        # Scan plugin directories
        for plugin_dir in self.plugin_dirs:
            discovered.extend(self._scan_directory(plugin_dir))

        # Scan entry points
        if self.auto_discover:
            discovered.extend(self._scan_entry_points())

        # Register all discovered plugins
        for info in discovered:
            self.registry.plugins[info.name] = info

        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered

    def load_all(self) -> int:
        """Load and activate all discovered plugins.

        Returns:
            Number of successfully loaded plugins.
        """
        loaded = 0
        for name, _info in self.registry.plugins.items():
            if self.load_plugin(name):
                loaded += 1
        return loaded

    def load_plugin(self, name: str) -> bool:
        """Load and activate a specific plugin by name.

        Args:
            name: The plugin name to load.

        Returns:
            True if successfully loaded, False otherwise.
        """
        if name not in self.registry.plugins:
            logger.error(f"Plugin '{name}' not found in registry")
            return False

        info = self.registry.plugins[name]

        try:
            module = self._import_module(info.module_path)
            plugin_class = self._find_plugin_class(module)

            if plugin_class is None:
                info.error = "No Plugin class found in module"
                logger.error(f"Plugin '{name}': {info.error}")
                return False

            instance = plugin_class()
            instance.activate()

            self.registry.instances[name] = instance
            info.is_active = True
            info.error = None
            logger.info(f"Loaded plugin: {name} v{info.version}")
            return True

        except Exception as e:
            info.error = str(e)
            info.is_active = False
            logger.error(f"Failed to load plugin '{name}': {e}")
            return False

    def unload_plugin(self, name: str) -> bool:
        """Deactivate and unload a plugin.

        Args:
            name: The plugin name to unload.

        Returns:
            True if successfully unloaded.
        """
        if name not in self.registry.instances:
            return False

        try:
            instance = self.registry.instances[name]
            instance.deactivate()
        except Exception as e:
            logger.warning(f"Error deactivating plugin '{name}': {e}")

        del self.registry.instances[name]
        if name in self.registry.plugins:
            self.registry.plugins[name].is_active = False

        logger.info(f"Unloaded plugin: {name}")
        return True

    def _scan_directory(self, directory: Path) -> list[PluginInfo]:
        """Scan a directory for plugin modules."""
        discovered: list[PluginInfo] = []

        if not directory.exists() or not directory.is_dir():
            logger.debug(f"Plugin directory not found: {directory}")
            return discovered

        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".py" and not item.name.startswith("_"):
                info = self._inspect_module_file(item)
                if info:
                    discovered.append(info)
            elif item.is_dir() and (item / "__init__.py").exists():
                info = self._inspect_module_file(item / "__init__.py")
                if info:
                    info.module_path = str(item)
                    discovered.append(info)

        return discovered

    def _scan_entry_points(self) -> list[PluginInfo]:
        """Scan installed packages for arbiterx plugin entry points."""
        discovered: list[PluginInfo] = []

        try:
            if sys.version_info >= (3, 10):
                from importlib.metadata import entry_points

                eps = entry_points(group=self.ENTRY_POINT_GROUP)
            else:
                from importlib.metadata import entry_points

                all_eps = entry_points()
                eps = all_eps.get(self.ENTRY_POINT_GROUP, [])

            for ep in eps:
                discovered.append(
                    PluginInfo(
                        name=ep.name,
                        version="unknown",
                        module_path=ep.value,
                        source="entry_point",
                    )
                )
        except Exception as e:
            logger.debug(f"Error scanning entry points: {e}")

        return discovered

    def _inspect_module_file(self, path: Path) -> PluginInfo | None:
        """Inspect a Python file for plugin metadata."""
        try:
            # Read file to extract name/version without importing
            content = path.read_text(encoding="utf-8")

            name = path.stem
            version = "0.3.0"

            # Try to extract version from module
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("__version__"):
                    parts = stripped.split("=", 1)
                    if len(parts) == 2:
                        version = parts[1].strip().strip("\"'")
                        break

            # Check if it has a Plugin class
            if "class " not in content or "Plugin" not in content:
                return None

            return PluginInfo(
                name=name,
                version=version,
                module_path=str(path),
                source="directory",
            )
        except (OSError, UnicodeDecodeError):
            return None

    def _import_module(self, module_path: str) -> Any:
        """Import a module from a file path or dotted module name."""
        path = Path(module_path)

        if path.exists():
            # Import from file path
            spec = importlib.util.spec_from_file_location(f"arbiterx_plugin_{path.stem}", str(path))
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot create module spec for: {module_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        else:
            # Import as dotted module name
            return importlib.import_module(module_path)

    def _find_plugin_class(self, module: Any) -> type | None:
        """Find the Plugin class in a loaded module."""
        # Look for a class named 'Plugin' or ending with 'Plugin'
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and attr_name.endswith("Plugin"):
                # Verify it has the required interface
                if hasattr(attr, "activate") and hasattr(attr, "deactivate"):
                    return attr

        # Fallback: look for 'Plugin' attribute directly
        if hasattr(module, "Plugin"):
            return module.Plugin

        return None
