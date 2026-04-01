"""Database layer for Bulbe.

SQLite-backed storage for all benchmark runs, results, and system info.
Every run is recorded from the moment it's created — nothing is lost.

Design:
- SQLite for local/single-user (default, zero setup)
- Schema designed for fast filtering and cross-run comparison
- All queries return plain dicts or model objects — no ORM overhead
- WAL mode for concurrent read/write (monitoring + querying)
- Prepared statements cached for performance
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

from bulbe.core.models import (
    ResultRecord,
    Run,
    RunStatus,
    model_to_dict,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS benchmarks (
    name        TEXT PRIMARY KEY,
    definition  TEXT NOT NULL,  -- full YAML stored as JSON
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    tags        TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS runs (
    id              TEXT PRIMARY KEY,
    experiment_id   TEXT NOT NULL,
    benchmark_name  TEXT NOT NULL REFERENCES benchmarks(name),
    status          TEXT NOT NULL DEFAULT 'pending',
    job_id          TEXT NOT NULL DEFAULT '',
    workdir         TEXT NOT NULL DEFAULT '',
    script_path     TEXT NOT NULL DEFAULT '',
    submitted_at    TEXT,
    started_at      TEXT,
    completed_at    TEXT,
    exit_code       INTEGER,
    parameters      TEXT NOT NULL DEFAULT '{}',
    results         TEXT NOT NULL DEFAULT '{}',
    system_info     TEXT NOT NULL DEFAULT '{}',
    tags            TEXT NOT NULL DEFAULT '{}',
    error_message   TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT NOT NULL REFERENCES runs(id),
    name        TEXT NOT NULL,
    value       TEXT NOT NULL,
    unit        TEXT NOT NULL DEFAULT '',
    timestamp   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS system_info (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT NOT NULL REFERENCES runs(id),
    hostname    TEXT NOT NULL DEFAULT '',
    cpu_model   TEXT NOT NULL DEFAULT '',
    cpu_cores   INTEGER NOT NULL DEFAULT 0,
    cpu_sockets INTEGER NOT NULL DEFAULT 0,
    numa_nodes  INTEGER NOT NULL DEFAULT 0,
    memory_gb   REAL NOT NULL DEFAULT 0.0,
    gpu_model   TEXT NOT NULL DEFAULT '',
    gpu_count   INTEGER NOT NULL DEFAULT 0,
    mpi_version TEXT NOT NULL DEFAULT '',
    raw_data    TEXT NOT NULL DEFAULT '{}'
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_runs_benchmark ON runs(benchmark_name);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_submitted ON runs(submitted_at);
CREATE INDEX IF NOT EXISTS idx_results_run ON results(run_id);
CREATE INDEX IF NOT EXISTS idx_results_name ON results(name);
CREATE INDEX IF NOT EXISTS idx_system_info_run ON system_info(run_id);
"""


class Database:
    """SQLite database for Bulbe benchmark data."""

    def __init__(self, path: Path | str = ":memory:") -> None:
        self.path = Path(path) if path != ":memory:" else path
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = self._connect()
        return self._conn

    def _connect(self) -> sqlite3.Connection:
        db_path = str(self.path)
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        self.conn.executescript(SCHEMA_SQL)

        # Track schema version
        cur = self.conn.execute("SELECT version FROM schema_version")
        row = cur.fetchone()
        if row is None:
            self.conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,)
            )
        self.conn.commit()
        logger.debug("Database initialized at %s (schema v%d)", self.path, SCHEMA_VERSION)

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for atomic transactions."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # --- Benchmark CRUD ---

    def save_benchmark(self, name: str, definition: dict[str, Any], tags: dict[str, str] | None = None) -> None:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO benchmarks (name, definition, tags, updated_at)
                   VALUES (?, ?, ?, datetime('now'))
                   ON CONFLICT(name) DO UPDATE SET
                       definition = excluded.definition,
                       tags = excluded.tags,
                       updated_at = datetime('now')""",
                (name, json.dumps(definition), json.dumps(tags or {})),
            )

    def get_benchmark(self, name: str) -> dict[str, Any] | None:
        cur = self.conn.execute("SELECT * FROM benchmarks WHERE name = ?", (name,))
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    def list_benchmarks(self) -> list[dict[str, Any]]:
        cur = self.conn.execute("SELECT * FROM benchmarks ORDER BY updated_at DESC")
        return [dict(row) for row in cur.fetchall()]

    # --- Run CRUD ---

    def save_run(self, run: Run) -> None:
        data = model_to_dict(run)
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO runs (id, experiment_id, benchmark_name, status, job_id,
                       workdir, script_path, submitted_at, started_at, completed_at,
                       exit_code, parameters, results, system_info, tags, error_message)
                   VALUES (:id, :experiment_id, :benchmark_name, :status, :job_id,
                       :workdir, :script_path, :submitted_at, :started_at, :completed_at,
                       :exit_code, :parameters, :results, :system_info, :tags, :error_message)
                   ON CONFLICT(id) DO UPDATE SET
                       status = excluded.status,
                       job_id = excluded.job_id,
                       started_at = excluded.started_at,
                       completed_at = excluded.completed_at,
                       exit_code = excluded.exit_code,
                       results = excluded.results,
                       system_info = excluded.system_info,
                       error_message = excluded.error_message""",
                {
                    **data,
                    "parameters": json.dumps(data["parameters"]),
                    "results": json.dumps(data["results"]),
                    "system_info": json.dumps(data["system_info"]),
                    "tags": json.dumps(data["tags"]),
                },
            )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        cur = self.conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
        if row is None:
            return None
        result = dict(row)
        for json_field in ("parameters", "results", "system_info", "tags"):
            result[json_field] = json.loads(result[json_field])
        return result

    def list_runs(
        self,
        benchmark_name: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
        tags: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query runs with flexible filtering."""
        conditions = []
        params: list[Any] = []

        if benchmark_name:
            conditions.append("benchmark_name = ?")
            params.append(benchmark_name)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM runs {where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.execute(query, params)
        rows = []
        for row in cur.fetchall():
            r = dict(row)
            for json_field in ("parameters", "results", "system_info", "tags"):
                r[json_field] = json.loads(r[json_field])
            # Post-filter by tags if requested
            if tags and not all(r["tags"].get(k) == v for k, v in tags.items()):
                continue
            rows.append(r)
        return rows

    def update_run_status(self, run_id: str, status: RunStatus, **kwargs: Any) -> None:
        """Efficiently update just the status and optional fields."""
        sets = ["status = ?"]
        params: list[Any] = [status.value]

        for key in ("job_id", "started_at", "completed_at", "exit_code", "error_message"):
            if key in kwargs:
                sets.append(f"{key} = ?")
                val = kwargs[key]
                if isinstance(val, datetime):
                    val = val.isoformat()
                params.append(val)

        params.append(run_id)
        with self.transaction() as conn:
            conn.execute(f"UPDATE runs SET {', '.join(sets)} WHERE id = ?", params)

    # --- Results ---

    def save_result(self, record: ResultRecord) -> None:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO results (run_id, name, value, unit, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (record.run_id, record.name, str(record.value), record.unit,
                 record.timestamp.isoformat()),
            )

    def save_results_batch(self, records: list[ResultRecord]) -> None:
        """Batch insert for performance."""
        with self.transaction() as conn:
            conn.executemany(
                """INSERT INTO results (run_id, name, value, unit, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    (r.run_id, r.name, str(r.value), r.unit, r.timestamp.isoformat())
                    for r in records
                ],
            )

    def get_results(
        self,
        run_id: str | None = None,
        name: str | None = None,
        benchmark_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query results with flexible filters."""
        if benchmark_name:
            query = """
                SELECT r.*, runs.benchmark_name, runs.parameters
                FROM results r
                JOIN runs ON r.run_id = runs.id
                WHERE runs.benchmark_name = ?
                ORDER BY r.timestamp DESC
            """
            cur = self.conn.execute(query, (benchmark_name,))
        elif run_id and name:
            cur = self.conn.execute(
                "SELECT * FROM results WHERE run_id = ? AND name = ?", (run_id, name)
            )
        elif run_id:
            cur = self.conn.execute("SELECT * FROM results WHERE run_id = ?", (run_id,))
        else:
            cur = self.conn.execute("SELECT * FROM results ORDER BY timestamp DESC LIMIT 1000")

        return [dict(row) for row in cur.fetchall()]

    # --- System Info ---

    def save_system_info(self, run_id: str, info: dict[str, Any]) -> None:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO system_info (run_id, hostname, cpu_model, cpu_cores,
                       cpu_sockets, numa_nodes, memory_gb, gpu_model, gpu_count,
                       mpi_version, raw_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    info.get("hostname", ""),
                    info.get("cpu_model", ""),
                    info.get("cpu_cores", 0),
                    info.get("cpu_sockets", 0),
                    info.get("numa_nodes", 0),
                    info.get("memory_total_gb", 0.0),
                    info.get("gpu_model", ""),
                    info.get("gpu_count", 0),
                    info.get("mpi_version", ""),
                    json.dumps(info),
                ),
            )

    # --- Aggregation queries ---

    def compare_runs(self, run_ids: list[str], metric: str) -> list[dict[str, Any]]:
        """Compare a specific metric across multiple runs."""
        placeholders = ",".join("?" * len(run_ids))
        cur = self.conn.execute(
            f"""SELECT r.run_id, r.value, r.unit, runs.parameters
                FROM results r
                JOIN runs ON r.run_id = runs.id
                WHERE r.run_id IN ({placeholders}) AND r.name = ?
                ORDER BY r.timestamp""",
            [*run_ids, metric],
        )
        rows = []
        for row in cur.fetchall():
            d = dict(row)
            d["parameters"] = json.loads(d["parameters"])
            rows.append(d)
        return rows

    def get_run_count(self, benchmark_name: str | None = None) -> int:
        if benchmark_name:
            cur = self.conn.execute(
                "SELECT COUNT(*) FROM runs WHERE benchmark_name = ?", (benchmark_name,)
            )
        else:
            cur = self.conn.execute("SELECT COUNT(*) FROM runs")
        return cur.fetchone()[0]
