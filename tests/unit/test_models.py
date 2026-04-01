"""Tests for core data models."""

from datetime import datetime
from pathlib import Path

from bulbe.core.models import (
    AppConfig,
    BenchmarkDef,
    Experiment,
    JobSpec,
    MonitorConfig,
    PatternDef,
    PinningConfig,
    ResultRecord,
    Run,
    RunStatus,
    SweepDef,
    SystemInfo,
    model_to_dict,
)


class TestRunStatus:
    def test_values(self):
        assert RunStatus.PENDING.value == "pending"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"


class TestAppConfig:
    def test_defaults(self):
        app = AppConfig(binary="./xhpl")
        assert app.binary == "./xhpl"
        assert app.modules == []
        assert app.environment == {}

    def test_frozen(self):
        app = AppConfig(binary="./xhpl")
        try:
            app.binary = "other"  # type: ignore
            assert False, "Should be frozen"
        except AttributeError:
            pass


class TestJobSpec:
    def test_defaults(self):
        job = JobSpec()
        assert job.scheduler == "slurm"
        assert job.nodes == 1
        assert job.tasks_per_node == 1
        assert job.time == "01:00:00"
        assert job.exclusive is True

    def test_custom(self):
        job = JobSpec(nodes=4, tasks_per_node=48, partition="compute")
        assert job.nodes == 4
        assert job.tasks_per_node == 48
        assert job.partition == "compute"


class TestExperiment:
    def test_auto_id(self):
        e1 = Experiment()
        e2 = Experiment()
        assert e1.id != e2.id
        assert len(e1.id) == 12

    def test_label(self):
        e = Experiment(parameters={"nodes": 4, "freq": "2.4GHz"})
        label = e.label()
        assert "nodes=4" in label
        assert "freq=2.4GHz" in label


class TestRun:
    def test_defaults(self):
        run = Run()
        assert run.status == RunStatus.PENDING
        assert run.results == {}
        assert run.exit_code is None

    def test_status_transition(self):
        run = Run()
        run.status = RunStatus.RUNNING
        assert run.status == RunStatus.RUNNING
        run.status = RunStatus.COMPLETED
        run.exit_code = 0
        assert run.exit_code == 0


class TestBenchmarkDef:
    def test_minimal(self):
        b = BenchmarkDef(
            name="test",
            app=AppConfig(binary="./app"),
            job=JobSpec(),
        )
        assert b.name == "test"
        assert b.id == "test"
        assert b.sweeps == []
        assert b.patterns == []


class TestModelToDict:
    def test_simple(self):
        run = Run(
            id="abc123",
            benchmark_name="test",
            status=RunStatus.COMPLETED,
            workdir=Path("/tmp/work"),
        )
        d = model_to_dict(run)
        assert d["id"] == "abc123"
        assert d["status"] == "completed"
        assert d["workdir"] == "/tmp/work"

    def test_nested(self):
        b = BenchmarkDef(
            name="test",
            app=AppConfig(binary="./app", modules=["mpi/1.0"]),
            job=JobSpec(nodes=4),
        )
        d = model_to_dict(b)
        assert d["app"]["binary"] == "./app"
        assert d["app"]["modules"] == ["mpi/1.0"]
        assert d["job"]["nodes"] == 4
