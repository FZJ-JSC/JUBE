"""Tests for the benchmark YAML loader."""

import tempfile
from pathlib import Path

import pytest
import yaml

from bulbe.core.loader import LoadError, load_benchmark, validate_benchmark


def _write_yaml(data: dict, tmp_path: Path) -> Path:
    """Helper: write a dict to a YAML file, return path."""
    path = tmp_path / "bench.yaml"
    path.write_text(yaml.dump(data))
    return path


class TestLoadBenchmark:
    def test_minimal_valid(self, tmp_path):
        data = {
            "benchmark": "test",
            "app": {"binary": "./myapp"},
        }
        path = _write_yaml(data, tmp_path)
        b = load_benchmark(path)

        assert b.name == "test"
        assert b.app.binary == "./myapp"
        assert b.job.scheduler == "slurm"
        assert b.job.nodes == 1

    def test_full_definition(self, tmp_path):
        data = {
            "benchmark": "hpl",
            "description": "HPL benchmark",
            "app": {
                "binary": "./xhpl",
                "modules": ["intel-mpi/2021.6", "mkl/2023.1"],
                "environment": {"OMP_NUM_THREADS": "1"},
            },
            "job": {
                "scheduler": "slurm",
                "nodes": 4,
                "tasks_per_node": 48,
                "time": "02:00:00",
                "partition": "compute",
                "account": "myproject",
            },
            "pinning": {
                "strategy": "numactl",
                "args": "--cpunodebind=0",
            },
            "parameters": {
                "nodes": [1, 2, 4, 8],
                "cpu_freq": ["2.0GHz", "2.4GHz"],
            },
            "sweeps": [
                {"type": "scaling"},
                {"type": "frequency"},
            ],
            "analysis": {
                "patterns": [
                    {
                        "name": "gflops",
                        "regex": r"WR.*\s+(\d+\.\d+)$",
                        "unit": "GFLOP/s",
                    },
                ],
            },
            "monitor": {"tail": True, "io": True},
            "tags": {"cluster": "test-cluster"},
        }
        path = _write_yaml(data, tmp_path)
        b = load_benchmark(path)

        assert b.name == "hpl"
        assert b.description == "HPL benchmark"
        assert b.app.binary == "./xhpl"
        assert len(b.app.modules) == 2
        assert b.job.nodes == 4
        assert b.job.tasks_per_node == 48
        assert b.pinning.strategy == "numactl"
        assert len(b.parameters["nodes"]) == 4
        assert len(b.sweeps) == 2
        assert len(b.patterns) == 1
        assert b.patterns[0].name == "gflops"
        assert b.monitor.tail is True
        assert b.tags["cluster"] == "test-cluster"

    def test_missing_name_raises(self, tmp_path):
        data = {"app": {"binary": "./myapp"}}
        path = _write_yaml(data, tmp_path)

        with pytest.raises(LoadError) as exc_info:
            load_benchmark(path)
        assert "Missing 'benchmark'" in str(exc_info.value)

    def test_missing_binary_raises(self, tmp_path):
        data = {"benchmark": "test", "app": {}}
        path = _write_yaml(data, tmp_path)

        with pytest.raises(LoadError) as exc_info:
            load_benchmark(path)
        assert "app.binary" in str(exc_info.value)

    def test_file_not_found(self):
        with pytest.raises(LoadError) as exc_info:
            load_benchmark(Path("/nonexistent/file.yaml"))
        assert "File not found" in str(exc_info.value)

    def test_invalid_yaml(self, tmp_path):
        path = tmp_path / "bench.yaml"
        path.write_text("just a string, not a mapping")

        with pytest.raises(LoadError) as exc_info:
            load_benchmark(path)
        assert "root must be a mapping" in str(exc_info.value)


class TestValidateBenchmark:
    def test_valid_benchmark_no_warnings(self, tmp_path):
        data = {"benchmark": "test", "app": {"binary": "./myapp"}}
        path = _write_yaml(data, tmp_path)
        b = load_benchmark(path)

        warnings = validate_benchmark(b)
        assert len(warnings) == 0

    def test_warns_on_large_task_count(self, tmp_path):
        data = {
            "benchmark": "test",
            "app": {"binary": "./myapp"},
            "job": {"nodes": 500, "tasks_per_node": 48},
        }
        path = _write_yaml(data, tmp_path)
        b = load_benchmark(path)

        warnings = validate_benchmark(b)
        assert any("Very large task count" in w for w in warnings)
