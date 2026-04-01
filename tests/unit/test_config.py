"""Tests for the configuration system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from bulbe.core.config import BulbeConfig


class TestBulbeConfig:
    def test_defaults(self):
        config = BulbeConfig()
        assert config.default_scheduler == "slurm"
        assert config.default_time == "01:00:00"
        assert config.color is True
        assert config.verbose is False

    def test_to_dict(self):
        config = BulbeConfig()
        d = config.to_dict()
        assert "default_scheduler" in d
        assert "db_path" in d
        assert d["default_scheduler"] == "slurm"

    def test_load_from_project_file(self, tmp_path):
        project_yaml = tmp_path / "bulbe.yaml"
        project_yaml.write_text(yaml.dump({
            "default_scheduler": "pbs",
            "default_partition": "gpu",
            "default_account": "myaccount",
        }))

        config = BulbeConfig.load(project_root=tmp_path)
        assert config.default_scheduler == "pbs"
        assert config.default_partition == "gpu"
        assert config.default_account == "myaccount"

    def test_env_override(self):
        env = {
            "BULBE_SCHEDULER": "local",
            "BULBE_PARTITION": "debug",
            "BULBE_VERBOSE": "true",
        }
        with patch.dict(os.environ, env, clear=False):
            config = BulbeConfig.load()
            assert config.default_scheduler == "local"
            assert config.default_partition == "debug"
            assert config.verbose is True

    def test_ensure_dirs(self, tmp_path):
        config = BulbeConfig(
            workdir=tmp_path / "runs",
            global_dir=tmp_path / "global",
            templates_dir=tmp_path / "global" / "templates",
            plugins_dir=tmp_path / "global" / "plugins",
        )
        config.ensure_dirs()

        assert (tmp_path / "runs").is_dir()
        assert (tmp_path / "global").is_dir()
        assert (tmp_path / "global" / "templates").is_dir()
        assert (tmp_path / "global" / "plugins").is_dir()
