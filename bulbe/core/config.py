"""Configuration system for Bulbe.

Two-level config:
1. Global config: ~/.config/bulbe/config.yaml — user defaults
2. Project config: ./bulbe.yaml — project-specific settings

Project config overrides global. Environment variables override both
(BULBE_DB_PATH, BULBE_WORKDIR, etc.).

Designed for zero-config startup: everything has sensible defaults.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_GLOBAL_DIR = Path.home() / ".config" / "bulbe"
DEFAULT_DB_NAME = "bulbe.db"
DEFAULT_WORKDIR = "bulbe_runs"


@dataclass
class BulbeConfig:
    """Complete Bulbe configuration."""

    # Paths
    project_root: Path = field(default_factory=Path.cwd)
    workdir: Path = field(default_factory=lambda: Path.cwd() / DEFAULT_WORKDIR)
    db_path: Path = field(default_factory=lambda: Path.cwd() / DEFAULT_DB_NAME)
    global_dir: Path = field(default_factory=lambda: DEFAULT_GLOBAL_DIR)
    templates_dir: Path = field(default_factory=lambda: DEFAULT_GLOBAL_DIR / "templates")
    plugins_dir: Path = field(default_factory=lambda: DEFAULT_GLOBAL_DIR / "plugins")

    # Scheduler defaults
    default_scheduler: str = "slurm"
    default_partition: str = ""
    default_account: str = ""
    default_time: str = "01:00:00"

    # Modules
    default_modules: list[str] = field(default_factory=list)

    # Monitoring
    monitor_poll_interval: float = 5.0

    # Display
    color: bool = True
    verbose: bool = False

    # Plugin paths (additional user plugin directories)
    extra_plugin_dirs: list[Path] = field(default_factory=list)

    @classmethod
    def load(cls, project_root: Path | None = None) -> BulbeConfig:
        """Load config from global + project files + environment."""
        config = cls()

        # 1. Global config
        global_file = config.global_dir / "config.yaml"
        if global_file.exists():
            global_data = _load_yaml_file(global_file)
            if global_data:
                config = _apply_dict(config, global_data)

        # 2. Project config
        root = project_root or Path.cwd()
        project_file = root / "bulbe.yaml"
        if not project_file.exists():
            project_file = root / "bulbe.yml"
        if project_file.exists():
            project_data = _load_yaml_file(project_file)
            if project_data:
                config = _apply_dict(config, project_data)
                config.project_root = root

        # 3. Environment overrides
        config = _apply_env(config)

        return config

    def ensure_dirs(self) -> None:
        """Create necessary directories."""
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.global_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "workdir": str(self.workdir),
            "db_path": str(self.db_path),
            "default_scheduler": self.default_scheduler,
            "default_partition": self.default_partition,
            "default_account": self.default_account,
            "default_time": self.default_time,
            "default_modules": self.default_modules,
            "monitor_poll_interval": self.monitor_poll_interval,
            "color": self.color,
            "verbose": self.verbose,
        }


def _load_yaml_file(path: Path) -> dict[str, Any] | None:
    """Load a YAML file, returning None on error."""
    try:
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None
    except ImportError:
        logger.warning("PyYAML not available, skipping config file: %s", path)
        return None
    except Exception:
        logger.exception("Failed to load config: %s", path)
        return None


def _apply_dict(config: BulbeConfig, data: dict[str, Any]) -> BulbeConfig:
    """Apply a dict of values to a config, only setting known fields."""
    path_fields = {"project_root", "workdir", "db_path", "global_dir", "templates_dir", "plugins_dir"}

    for key, value in data.items():
        if not hasattr(config, key):
            logger.warning("Unknown config key: %s", key)
            continue
        if key in path_fields:
            setattr(config, key, Path(value))
        elif key == "extra_plugin_dirs":
            setattr(config, key, [Path(p) for p in value])
        else:
            setattr(config, key, value)
    return config


def _apply_env(config: BulbeConfig) -> BulbeConfig:
    """Override config with BULBE_* environment variables."""
    env_map = {
        "BULBE_DB_PATH": ("db_path", Path),
        "BULBE_WORKDIR": ("workdir", Path),
        "BULBE_SCHEDULER": ("default_scheduler", str),
        "BULBE_PARTITION": ("default_partition", str),
        "BULBE_ACCOUNT": ("default_account", str),
        "BULBE_VERBOSE": ("verbose", lambda v: v.lower() in ("1", "true", "yes")),
    }

    for env_var, (attr, converter) in env_map.items():
        value = os.environ.get(env_var)
        if value is not None:
            setattr(config, attr, converter(value))

    return config
