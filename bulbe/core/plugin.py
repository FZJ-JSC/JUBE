"""Plugin system for Bulbe.

Plugins are the extension mechanism for Bulbe. Each plugin registers itself
into a category (scheduler, sweep, monitor, analysis, system, generator, results)
and exposes a standard interface for that category.

Two registration paths:
1. Python plugins — use the @bulbe_plugin decorator or register_plugin()
2. External plugins — any executable that speaks JSON on stdin/stdout

Plugin discovery:
- Built-in plugins in bulbe/plugins/ are auto-loaded
- User plugins from ~/.config/bulbe/plugins/ or project-local ./bulbe_plugins/
- External plugins declared in config YAML
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# --- Plugin categories and interfaces ---

PLUGIN_CATEGORIES = frozenset({
    "scheduler",
    "sweep",
    "monitor",
    "analysis",
    "system",
    "generator",
    "results",
})


@runtime_checkable
class SchedulerPlugin(Protocol):
    """Interface for scheduler plugins (Slurm, PBS, local, etc.)."""

    name: str

    def generate_script(self, experiment: Any, app: Any, workdir: Path) -> str: ...
    def submit(self, script_path: Path, workdir: Path) -> str: ...
    def status(self, job_id: str) -> str: ...
    def cancel(self, job_id: str) -> bool: ...


@runtime_checkable
class SweepPlugin(Protocol):
    """Interface for parameter sweep plugins."""

    name: str

    def generate_experiments(self, benchmark: Any) -> list[Any]: ...


@runtime_checkable
class MonitorPlugin(Protocol):
    """Interface for monitoring plugins."""

    name: str

    def start(self, run: Any) -> None: ...
    def poll(self, run: Any) -> dict[str, Any]: ...
    def stop(self, run: Any) -> None: ...


@runtime_checkable
class AnalysisPlugin(Protocol):
    """Interface for analysis plugins."""

    name: str

    def analyze(self, runs: list[Any]) -> dict[str, Any]: ...


@runtime_checkable
class SystemPlugin(Protocol):
    """Interface for system info collection plugins."""

    name: str

    def collect(self) -> dict[str, Any]: ...


# --- Plugin registry ---

@dataclass
class PluginEntry:
    """Registry entry for a loaded plugin."""

    name: str
    category: str
    cls: type | None = None
    instance: Any = None
    external_command: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class PluginRegistry:
    """Central registry for all plugins.

    Thread-safe singleton pattern. Fast lookup by category + name.
    """

    _instance: PluginRegistry | None = None

    def __init__(self) -> None:
        self._plugins: dict[str, dict[str, PluginEntry]] = {
            cat: {} for cat in PLUGIN_CATEGORIES
        }
        self._loaded_paths: set[str] = set()

    @classmethod
    def get(cls) -> PluginRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (for testing)."""
        cls._instance = None

    def register(
        self,
        category: str,
        name: str,
        cls: type | None = None,
        instance: Any = None,
        external_command: str = "",
        metadata: dict[str, str] | None = None,
    ) -> None:
        if category not in PLUGIN_CATEGORIES:
            raise ValueError(
                f"Unknown plugin category '{category}'. "
                f"Valid: {', '.join(sorted(PLUGIN_CATEGORIES))}"
            )

        if name in self._plugins[category]:
            logger.warning("Overwriting plugin %s/%s", category, name)

        self._plugins[category][name] = PluginEntry(
            name=name,
            category=category,
            cls=cls,
            instance=instance,
            external_command=external_command,
            metadata=metadata or {},
        )
        logger.debug("Registered plugin %s/%s", category, name)

    def get_plugin(self, category: str, name: str) -> Any:
        """Get a plugin instance. Instantiates on first access."""
        entry = self._plugins.get(category, {}).get(name)
        if entry is None:
            raise KeyError(f"No plugin '{name}' in category '{category}'")

        if entry.instance is None and entry.cls is not None:
            entry.instance = entry.cls()

        return entry.instance

    def list_plugins(self, category: str | None = None) -> list[PluginEntry]:
        """List all registered plugins, optionally filtered by category."""
        if category:
            return list(self._plugins.get(category, {}).values())
        return [
            entry
            for cat_plugins in self._plugins.values()
            for entry in cat_plugins.values()
        ]

    def has_plugin(self, category: str, name: str) -> bool:
        return name in self._plugins.get(category, {})

    def load_builtins(self) -> None:
        """Auto-discover and load all built-in plugins from bulbe.plugins.*."""
        import bulbe.plugins as plugins_pkg

        for _importer, modname, _ispkg in pkgutil.walk_packages(
            plugins_pkg.__path__, prefix="bulbe.plugins."
        ):
            if modname in self._loaded_paths:
                continue
            try:
                importlib.import_module(modname)
                self._loaded_paths.add(modname)
                logger.debug("Loaded built-in plugin module: %s", modname)
            except Exception:
                logger.exception("Failed to load plugin module: %s", modname)

    def load_from_directory(self, path: Path) -> None:
        """Load plugins from a directory of Python files."""
        if not path.is_dir():
            return
        for py_file in sorted(path.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            mod_name = py_file.stem
            if mod_name in self._loaded_paths:
                continue
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location(mod_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)  # type: ignore[union-attr]
                    self._loaded_paths.add(mod_name)
                    logger.debug("Loaded user plugin: %s", py_file)
            except Exception:
                logger.exception("Failed to load user plugin: %s", py_file)


# --- Decorator for easy plugin registration ---

def bulbe_plugin(category: str, name: str | None = None) -> Callable[[type], type]:
    """Decorator to register a class as a Bulbe plugin.

    Usage:
        @bulbe_plugin("scheduler", "slurm")
        class SlurmScheduler:
            ...

        @bulbe_plugin("sweep")  # name defaults to class name
        class FrequencySweep:
            ...
    """

    def decorator(cls: type) -> type:
        plugin_name = name or cls.__name__
        PluginRegistry.get().register(category=category, name=plugin_name, cls=cls)
        return cls

    return decorator


def register_plugin(category: str, name: str, cls: type) -> None:
    """Imperative registration (alternative to decorator)."""
    PluginRegistry.get().register(category=category, name=name, cls=cls)
