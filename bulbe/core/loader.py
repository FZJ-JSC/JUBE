"""Benchmark YAML loader.

Parses benchmark definition files into model objects, applying defaults
from config and validating structure.

Design: fail fast with clear error messages. No silent defaults for
critical fields (binary, nodes). Warnings for non-critical issues.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from bulbe.core.config import BulbeConfig
from bulbe.core.models import (
    AppConfig,
    BenchmarkDef,
    JobSpec,
    MonitorConfig,
    PatternDef,
    PinningConfig,
    SweepDef,
)

logger = logging.getLogger(__name__)


class LoadError(Exception):
    """Raised when a benchmark YAML cannot be loaded or validated."""

    def __init__(self, path: str, errors: list[str]) -> None:
        self.path = path
        self.errors = errors
        msg = f"Failed to load {path}:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(msg)


def load_benchmark(path: Path, config: BulbeConfig | None = None) -> BenchmarkDef:
    """Load a benchmark definition from a YAML file.

    Args:
        path: Path to the YAML file.
        config: Optional config for applying defaults.

    Returns:
        A validated BenchmarkDef ready for sweep expansion.

    Raises:
        LoadError: If the file is invalid or missing required fields.
    """
    if not path.exists():
        raise LoadError(str(path), [f"File not found: {path}"])

    with open(path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise LoadError(str(path), ["YAML root must be a mapping"])

    errors: list[str] = []
    warnings: list[str] = []

    # --- Required fields ---
    name = raw.get("benchmark") or raw.get("name")
    if not name:
        errors.append("Missing 'benchmark' or 'name' field")

    # --- App config ---
    app_data = raw.get("app", {})
    if not app_data.get("binary"):
        errors.append("Missing 'app.binary' — what should Bulbe run?")

    if errors:
        raise LoadError(str(path), errors)

    app = _parse_app(app_data)

    # --- Job spec ---
    job_data = raw.get("job", {})
    job = _parse_job(job_data, config)

    # --- Pinning ---
    pinning_data = raw.get("pinning", {})
    pinning = _parse_pinning(pinning_data)

    # --- Parameters ---
    parameters = raw.get("parameters", {})

    # --- Sweeps ---
    sweeps_data = raw.get("sweeps", [])
    sweeps = [_parse_sweep(s) for s in sweeps_data]

    # --- Patterns ---
    analysis_data = raw.get("analysis", {})
    patterns_data = analysis_data.get("patterns", [])
    patterns = [_parse_pattern(p) for p in patterns_data]

    # --- Monitor ---
    monitor_data = raw.get("monitor", {})
    monitor = _parse_monitor(monitor_data)

    # --- Tags ---
    tags = raw.get("tags", {})
    description = raw.get("description", "")

    # Log warnings
    for w in warnings:
        logger.warning("%s: %s", path, w)

    return BenchmarkDef(
        name=name,
        app=app,
        job=job,
        parameters=parameters,
        sweeps=sweeps,
        patterns=patterns,
        pinning=pinning,
        monitor=monitor,
        tags=tags,
        description=description,
    )


def load_benchmark_from_string(content: str, config: BulbeConfig | None = None) -> BenchmarkDef:
    """Load a benchmark from a YAML string (for testing/API use)."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        f.flush()
        return load_benchmark(Path(f.name), config)


def _parse_app(data: dict[str, Any]) -> AppConfig:
    return AppConfig(
        binary=data.get("binary", ""),
        modules=data.get("modules", []),
        environment=data.get("environment", {}),
        pre_commands=data.get("pre_commands", []),
        post_commands=data.get("post_commands", []),
    )


def _parse_job(data: dict[str, Any], config: BulbeConfig | None = None) -> JobSpec:
    defaults = {
        "scheduler": config.default_scheduler if config else "slurm",
        "partition": config.default_partition if config else "",
        "account": config.default_account if config else "",
        "time": config.default_time if config else "01:00:00",
    }

    return JobSpec(
        scheduler=data.get("scheduler", defaults["scheduler"]),
        nodes=data.get("nodes", 1),
        tasks_per_node=data.get("tasks_per_node", 1),
        cpus_per_task=data.get("cpus_per_task", 1),
        time=data.get("time", defaults["time"]),
        partition=data.get("partition", defaults["partition"]),
        account=data.get("account", defaults["account"]),
        exclusive=data.get("exclusive", True),
        extra_directives=data.get("extra_directives", []),
    )


def _parse_pinning(data: dict[str, Any]) -> PinningConfig:
    return PinningConfig(
        strategy=data.get("strategy", "none"),
        args=data.get("args", ""),
        map_by=data.get("map_by", ""),
        bind_to=data.get("bind_to", ""),
    )


def _parse_sweep(data: dict[str, Any]) -> SweepDef:
    return SweepDef(
        type=data.get("type", "custom"),
        parameters=data.get("parameters", {}),
    )


def _parse_pattern(data: dict[str, Any]) -> PatternDef:
    return PatternDef(
        name=data.get("name", ""),
        regex=data.get("regex", ""),
        file=data.get("file", "stdout"),
        reduction=data.get("reduction", "last"),
        unit=data.get("unit", ""),
        dtype=data.get("dtype", "float"),
    )


def _parse_monitor(data: dict[str, Any]) -> MonitorConfig:
    return MonitorConfig(
        tail=data.get("tail", False),
        io=data.get("io", False),
        mpi_trace=data.get("mpi_trace", False),
        system_stats=data.get("system_stats", False),
        poll_interval=data.get("poll_interval", 5.0),
    )


def validate_benchmark(benchmark: BenchmarkDef) -> list[str]:
    """Validate a loaded benchmark for common issues. Returns list of warnings."""
    warnings: list[str] = []

    if not benchmark.app.binary:
        warnings.append("No binary specified")

    if benchmark.job.nodes < 1:
        warnings.append(f"Invalid node count: {benchmark.job.nodes}")

    if benchmark.job.tasks_per_node < 1:
        warnings.append(f"Invalid tasks_per_node: {benchmark.job.tasks_per_node}")

    total_tasks = benchmark.job.nodes * benchmark.job.tasks_per_node
    if total_tasks > 10000:
        warnings.append(f"Very large task count: {total_tasks} — is this intentional?")

    for pattern in benchmark.patterns:
        if not pattern.regex:
            warnings.append(f"Pattern '{pattern.name}' has empty regex")

    if benchmark.monitor.mpi_trace and not any(
        "trace" in cmd.lower() or "-trace" in cmd.lower()
        for cmd in benchmark.app.pre_commands
    ):
        warnings.append(
            "MPI trace monitoring enabled but no trace flag in pre_commands. "
            "Consider adding '-trace' to your mpirun arguments."
        )

    return warnings
