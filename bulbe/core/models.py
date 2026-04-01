"""Core data models for Bulbe.

All benchmark data flows through these dataclasses. They are the single source
of truth for what a benchmark is, how it runs, and what it produces.

Design principles:
- Immutable where possible (frozen dataclasses)
- Serializable to/from dict for DB and YAML
- No external dependencies — pure Python stdlib + dataclasses
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class RunStatus(Enum):
    """Lifecycle states of a benchmark run."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SweepType(Enum):
    """Built-in parameter sweep strategies."""

    SCALING = "scaling"
    FREQUENCY = "frequency"
    MEMORY = "memory"
    CUSTOM = "custom"


@dataclass(frozen=True)
class AppConfig:
    """Application under test."""

    binary: str
    modules: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    pre_commands: list[str] = field(default_factory=list)
    post_commands: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JobSpec:
    """Scheduler job specification — maps 1:1 to scheduler directives."""

    scheduler: str = "slurm"
    nodes: int = 1
    tasks_per_node: int = 1
    cpus_per_task: int = 1
    time: str = "01:00:00"
    partition: str = ""
    account: str = ""
    exclusive: bool = True
    extra_directives: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PinningConfig:
    """Process/thread pinning configuration."""

    strategy: str = "none"  # none, numactl, rankfile, i_mpi_pin, srun
    args: str = ""
    map_by: str = ""  # for mpirun --map-by
    bind_to: str = ""  # for mpirun --bind-to


@dataclass(frozen=True)
class PatternDef:
    """Regex pattern for extracting results from output."""

    name: str
    regex: str
    file: str = "stdout"  # stdout, stderr, or a filename
    reduction: str = "last"  # first, last, min, max, avg, sum
    unit: str = ""
    dtype: str = "float"  # float, int, str


@dataclass(frozen=True)
class SweepDef:
    """Parameter sweep definition."""

    type: str  # scaling, frequency, memory, custom
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MonitorConfig:
    """What to monitor during a run."""

    tail: bool = False
    io: bool = False
    mpi_trace: bool = False
    system_stats: bool = False
    poll_interval: float = 5.0  # seconds


@dataclass
class BenchmarkDef:
    """Complete benchmark definition — parsed from YAML.

    This is the "recipe". It describes *what* to run and *how*.
    """

    name: str
    app: AppConfig
    job: JobSpec
    parameters: dict[str, Any] = field(default_factory=dict)
    sweeps: list[SweepDef] = field(default_factory=list)
    patterns: list[PatternDef] = field(default_factory=list)
    pinning: PinningConfig = field(default_factory=PinningConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    tags: dict[str, str] = field(default_factory=dict)
    description: str = ""

    @property
    def id(self) -> str:
        return self.name


@dataclass
class Experiment:
    """A single point in parameter space — one concrete run configuration.

    Generated from a BenchmarkDef by expanding sweeps/parameters.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    benchmark_name: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    job: JobSpec = field(default_factory=JobSpec)
    pinning: PinningConfig = field(default_factory=PinningConfig)
    pre_commands: list[str] = field(default_factory=list)

    def label(self) -> str:
        """Human-readable label from parameters."""
        parts = [f"{k}={v}" for k, v in sorted(self.parameters.items())]
        return ", ".join(parts) if parts else self.id


@dataclass
class Run:
    """A single execution of an experiment — tracks state and results.

    This is the "instance". It records *what happened*.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    experiment_id: str = ""
    benchmark_name: str = ""
    status: RunStatus = RunStatus.PENDING
    job_id: str = ""  # scheduler job ID (e.g. Slurm JOBID)
    workdir: Path = field(default_factory=lambda: Path("."))
    script_path: Path = field(default_factory=lambda: Path("."))
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    exit_code: int | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    system_info: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    error_message: str = ""


@dataclass(frozen=True)
class SystemInfo:
    """Captured system information for a run."""

    hostname: str = ""
    cpu_model: str = ""
    cpu_cores: int = 0
    cpu_sockets: int = 0
    cpu_threads_per_core: int = 0
    numa_nodes: int = 0
    memory_total_gb: float = 0.0
    os_version: str = ""
    kernel_version: str = ""
    gpu_model: str = ""
    gpu_count: int = 0
    interconnect: str = ""
    mpi_version: str = ""
    compiler_version: str = ""
    modules_loaded: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResultRecord:
    """A single extracted result value tied to a run."""

    run_id: str
    name: str
    value: float | int | str
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# --- Serialization helpers ---

def model_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a dataclass to a plain dict, handling nested types."""
    from dataclasses import asdict

    def _convert(v: Any) -> Any:
        if isinstance(v, Enum):
            return v.value
        if isinstance(v, Path):
            return str(v)
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    raw = asdict(obj)
    return _walk_dict(raw, _convert)


def _walk_dict(d: dict[str, Any], fn: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = _walk_dict(v, fn)
        elif isinstance(v, list):
            out[k] = [_walk_dict(i, fn) if isinstance(i, dict) else fn(i) for i in v]
        else:
            out[k] = fn(v)
    return out
