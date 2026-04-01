"""Tests for the database layer."""

import json
from datetime import datetime
from pathlib import Path

from bulbe.core.database import Database
from bulbe.core.models import ResultRecord, Run, RunStatus


class TestDatabase:
    def setup_method(self):
        self.db = Database(":memory:")
        self.db.initialize()

    def teardown_method(self):
        self.db.close()

    def test_initialize_creates_tables(self):
        cur = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row["name"] for row in cur.fetchall()}
        assert "benchmarks" in tables
        assert "runs" in tables
        assert "results" in tables
        assert "system_info" in tables

    def test_save_and_get_benchmark(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl", "nodes": 4})
        b = self.db.get_benchmark("hpl")
        assert b is not None
        assert b["name"] == "hpl"

    def test_list_benchmarks(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})
        self.db.save_benchmark("stream", {"binary": "./stream"})
        benchmarks = self.db.list_benchmarks()
        assert len(benchmarks) == 2

    def test_save_and_get_run(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})

        run = Run(
            id="run001",
            experiment_id="exp001",
            benchmark_name="hpl",
            status=RunStatus.COMPLETED,
            parameters={"nodes": 4},
            results={"gflops": 123.4},
        )
        self.db.save_run(run)

        fetched = self.db.get_run("run001")
        assert fetched is not None
        assert fetched["id"] == "run001"
        assert fetched["status"] == "completed"
        assert fetched["parameters"] == {"nodes": 4}
        assert fetched["results"] == {"gflops": 123.4}

    def test_list_runs_with_filter(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})

        for i in range(5):
            status = RunStatus.COMPLETED if i < 3 else RunStatus.FAILED
            run = Run(
                id=f"run{i:03d}",
                experiment_id=f"exp{i:03d}",
                benchmark_name="hpl",
                status=status,
            )
            self.db.save_run(run)

        all_runs = self.db.list_runs(benchmark_name="hpl")
        assert len(all_runs) == 5

        completed = self.db.list_runs(benchmark_name="hpl", status="completed")
        assert len(completed) == 3

        failed = self.db.list_runs(status="failed")
        assert len(failed) == 2

    def test_update_run_status(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})

        run = Run(id="run001", experiment_id="exp001", benchmark_name="hpl")
        self.db.save_run(run)

        self.db.update_run_status("run001", RunStatus.RUNNING, job_id="12345")
        fetched = self.db.get_run("run001")
        assert fetched["status"] == "running"
        assert fetched["job_id"] == "12345"

    def test_save_and_get_results(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})
        run = Run(id="run001", experiment_id="exp001", benchmark_name="hpl")
        self.db.save_run(run)

        record = ResultRecord(run_id="run001", name="gflops", value=456.7, unit="GFLOP/s")
        self.db.save_result(record)

        results = self.db.get_results(run_id="run001")
        assert len(results) == 1
        assert results[0]["name"] == "gflops"
        assert results[0]["value"] == "456.7"

    def test_batch_save_results(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})
        run = Run(id="run001", experiment_id="exp001", benchmark_name="hpl")
        self.db.save_run(run)

        records = [
            ResultRecord(run_id="run001", name="gflops", value=100.0),
            ResultRecord(run_id="run001", name="walltime", value=45.3),
            ResultRecord(run_id="run001", name="efficiency", value=0.87),
        ]
        self.db.save_results_batch(records)

        results = self.db.get_results(run_id="run001")
        assert len(results) == 3

    def test_compare_runs(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})

        for i in range(3):
            run = Run(
                id=f"run{i:03d}",
                experiment_id=f"exp{i:03d}",
                benchmark_name="hpl",
                parameters={"nodes": 2**i},
            )
            self.db.save_run(run)
            self.db.save_result(
                ResultRecord(run_id=f"run{i:03d}", name="gflops", value=100.0 * (i + 1))
            )

        comparison = self.db.compare_runs(["run000", "run001", "run002"], "gflops")
        assert len(comparison) == 3

    def test_get_run_count(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})
        self.db.save_benchmark("stream", {"binary": "./stream"})

        for i in range(3):
            self.db.save_run(Run(id=f"hpl{i}", experiment_id=f"e{i}", benchmark_name="hpl"))
        self.db.save_run(Run(id="stream0", experiment_id="e0", benchmark_name="stream"))

        assert self.db.get_run_count() == 4
        assert self.db.get_run_count("hpl") == 3
        assert self.db.get_run_count("stream") == 1

    def test_save_system_info(self):
        self.db.save_benchmark("hpl", {"binary": "./xhpl"})
        run = Run(id="run001", experiment_id="exp001", benchmark_name="hpl")
        self.db.save_run(run)

        info = {
            "hostname": "node001",
            "cpu_model": "Intel Xeon 8380",
            "cpu_cores": 40,
            "cpu_sockets": 2,
            "numa_nodes": 2,
            "memory_total_gb": 256.0,
        }
        self.db.save_system_info("run001", info)

        cur = self.db.conn.execute("SELECT * FROM system_info WHERE run_id = ?", ("run001",))
        row = dict(cur.fetchone())
        assert row["hostname"] == "node001"
        assert row["cpu_cores"] == 40
