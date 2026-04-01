"""Local scheduler plugin — runs benchmarks as local processes.

Used for testing Bulbe without a real scheduler. Runs the generated
script via bash in a subprocess.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
from pathlib import Path
from typing import Any

from bulbe.core.models import AppConfig, Experiment, JobSpec, PinningConfig
from bulbe.core.plugin import bulbe_plugin

logger = logging.getLogger(__name__)

# Track running processes by "job ID" (PID)
_processes: dict[str, subprocess.Popen[str]] = {}


@bulbe_plugin("scheduler", "local")
class LocalScheduler:
    """Run benchmarks as local bash processes."""

    name = "local"

    def generate_script(
        self,
        experiment: Experiment | None,
        app: AppConfig,
        workdir: Path,
        job: JobSpec | None = None,
        benchmark_name: str = "bulbe",
        pinning: PinningConfig | None = None,
    ) -> str:
        """Generate a simple bash script for local execution."""
        lines: list[str] = ["#!/bin/bash", f"# Bulbe local run: {benchmark_name}", ""]

        # Modules (best effort — module command may not exist locally)
        if app.modules:
            lines.append("# Modules (skipped in local mode)")
            for mod in app.modules:
                lines.append(f"# module load {mod}")
            lines.append("")

        # Environment
        for key, value in app.environment.items():
            lines.append(f'export {key}="{value}"')
        if app.environment:
            lines.append("")

        # Pre-commands
        for cmd in app.pre_commands:
            lines.append(cmd)
        if app.pre_commands:
            lines.append("")

        # Execution
        lines.append(f"{app.binary}")

        # Post-commands
        if app.post_commands:
            lines.append("")
            for cmd in app.post_commands:
                lines.append(cmd)

        lines.append("")
        return "\n".join(lines)

    def submit(self, script_path: Path, workdir: Path) -> str:
        """Run script locally, return PID as job ID."""
        proc = subprocess.Popen(
            ["bash", str(script_path)],
            cwd=str(workdir),
            stdout=open(workdir / f"{script_path.stem}.out", "w"),
            stderr=open(workdir / f"{script_path.stem}.err", "w"),
        )
        job_id = str(proc.pid)
        _processes[job_id] = proc
        logger.info("Started local process %s from %s", job_id, script_path)
        return job_id

    def status(self, job_id: str) -> str:
        """Check if the process is still running."""
        proc = _processes.get(job_id)
        if proc is None:
            return "unknown"

        ret = proc.poll()
        if ret is None:
            return "running"
        elif ret == 0:
            return "completed"
        else:
            return "failed"

    def cancel(self, job_id: str) -> bool:
        """Kill the local process."""
        proc = _processes.get(job_id)
        if proc is None:
            return False

        try:
            os.kill(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
            return True
        except (OSError, subprocess.TimeoutExpired):
            try:
                os.kill(proc.pid, signal.SIGKILL)
                return True
            except OSError:
                return False
