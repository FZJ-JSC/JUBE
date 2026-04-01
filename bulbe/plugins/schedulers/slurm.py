"""Slurm scheduler plugin.

Generates Slurm batch scripts, submits via sbatch, queries via squeue/sacct,
cancels via scancel. Maps 1:1 from JobSpec to #SBATCH directives — no magic.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from bulbe.core.models import AppConfig, Experiment, JobSpec, PinningConfig
from bulbe.core.plugin import bulbe_plugin

logger = logging.getLogger(__name__)


@bulbe_plugin("scheduler", "slurm")
class SlurmScheduler:
    """Slurm job scheduler."""

    name = "slurm"

    def generate_script(
        self,
        experiment: Experiment | None,
        app: AppConfig,
        workdir: Path,
        job: JobSpec | None = None,
        benchmark_name: str = "bulbe",
        pinning: PinningConfig | None = None,
    ) -> str:
        """Generate a Slurm batch script.

        Args:
            experiment: The experiment (if from a sweep). Can be None for preview.
            app: Application configuration.
            workdir: Working directory for the job.
            job: Job specification. Uses experiment's if not provided.
            benchmark_name: Name for job naming.
            pinning: Process pinning config.

        Returns:
            Complete bash script as a string.
        """
        if job is None and experiment is not None:
            job = experiment.job
        if job is None:
            job = JobSpec()

        if pinning is None and experiment is not None:
            pinning = experiment.pinning
        if pinning is None:
            pinning = PinningConfig()

        exp_id = experiment.id if experiment else "preview"
        job_name = f"bulbe_{benchmark_name}_{exp_id}"

        lines: list[str] = []
        lines.append("#!/bin/bash")
        lines.append(f"#SBATCH --job-name={job_name}")
        lines.append(f"#SBATCH --nodes={job.nodes}")
        lines.append(f"#SBATCH --ntasks-per-node={job.tasks_per_node}")

        if job.cpus_per_task > 1:
            lines.append(f"#SBATCH --cpus-per-task={job.cpus_per_task}")

        lines.append(f"#SBATCH --time={job.time}")

        if job.partition:
            lines.append(f"#SBATCH --partition={job.partition}")
        if job.account:
            lines.append(f"#SBATCH --account={job.account}")
        if job.exclusive:
            lines.append("#SBATCH --exclusive")

        lines.append(f"#SBATCH --output={job_name}.out")
        lines.append(f"#SBATCH --error={job_name}.err")

        for directive in job.extra_directives:
            if not directive.startswith("#SBATCH"):
                directive = f"#SBATCH {directive}"
            lines.append(directive)

        lines.append("")

        # --- Environment ---
        lines.append("# --- Environment ---")
        lines.append("module purge")
        if app.modules:
            lines.append(f"module load {' '.join(app.modules)}")

        for key, value in app.environment.items():
            lines.append(f'export {key}="{value}"')

        lines.append("")

        # --- Pre-commands ---
        if app.pre_commands:
            lines.append("# --- Pre-commands ---")
            for cmd in app.pre_commands:
                lines.append(cmd)
            lines.append("")

        # --- Pinning ---
        pinning_prefix = ""
        if pinning.strategy == "numactl":
            pinning_prefix = f"numactl {pinning.args} " if pinning.args else "numactl "
        elif pinning.strategy == "srun":
            # Pinning handled via srun flags — added to extra_directives or inline
            pass

        # --- Execution ---
        lines.append("# --- Execution ---")
        total_tasks = job.nodes * job.tasks_per_node

        mpirun_opts = []
        if pinning.map_by:
            mpirun_opts.append(f"--map-by {pinning.map_by}")
        if pinning.bind_to:
            mpirun_opts.append(f"--bind-to {pinning.bind_to}")

        mpirun_opts_str = " ".join(mpirun_opts)
        if mpirun_opts_str:
            mpirun_opts_str = " " + mpirun_opts_str

        lines.append(f"mpirun -np {total_tasks}{mpirun_opts_str} {pinning_prefix}{app.binary}")

        # --- Post-commands ---
        if app.post_commands:
            lines.append("")
            lines.append("# --- Post-commands ---")
            for cmd in app.post_commands:
                lines.append(cmd)

        lines.append("")
        return "\n".join(lines)

    def submit(self, script_path: Path, workdir: Path) -> str:
        """Submit a job script via sbatch. Returns the job ID."""
        try:
            result = subprocess.run(
                ["sbatch", str(script_path)],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            raise RuntimeError("sbatch not found — is Slurm installed and in PATH?")
        except subprocess.TimeoutExpired:
            raise RuntimeError("sbatch timed out after 30 seconds")

        if result.returncode != 0:
            raise RuntimeError(f"sbatch failed: {result.stderr.strip()}")

        # Parse "Submitted batch job 123456"
        match = re.search(r"Submitted batch job (\d+)", result.stdout)
        if not match:
            raise RuntimeError(f"Could not parse job ID from sbatch output: {result.stdout}")

        job_id = match.group(1)
        logger.info("Submitted job %s from %s", job_id, script_path)
        return job_id

    def status(self, job_id: str) -> str:
        """Query job status via squeue/sacct. Returns a status string."""
        # Try squeue first (for queued/running jobs)
        try:
            result = subprocess.run(
                ["squeue", "-j", job_id, "-h", "-o", "%T"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fall back to sacct (for completed jobs)
        try:
            result = subprocess.run(
                ["sacct", "-j", job_id, "-n", "-o", "State", "--parsable2"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                # sacct can return multiple lines (job + job steps)
                states = result.stdout.strip().split("\n")
                return states[0].strip().lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return "unknown"

    def cancel(self, job_id: str) -> bool:
        """Cancel a job via scancel."""
        try:
            result = subprocess.run(
                ["scancel", job_id],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def validate_script(self, script_path: Path) -> list[str]:
        """Validate a script using sbatch --test-only. Returns list of issues."""
        issues: list[str] = []

        try:
            result = subprocess.run(
                ["sbatch", "--test-only", str(script_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                issues.append(f"sbatch --test-only failed: {result.stderr.strip()}")
        except FileNotFoundError:
            issues.append("sbatch not found — cannot validate")
        except subprocess.TimeoutExpired:
            issues.append("sbatch --test-only timed out")

        return issues
