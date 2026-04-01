# Plan: Phase 1 — Execution Engine

## Status
PLANNED

## Summary

Phase 0 built the framework: models, database, plugin system, config, YAML loader,
and CLI skeleton. Nothing runs end-to-end yet. Phase 1 closes that gap.

At the start of this phase, `bulbe run benchmark.yaml` exists as a CLI command stub
that does nothing. At the end, it fully executes: loads the YAML, expands sweeps
into experiments, generates job scripts, submits them to Slurm (or runs them
locally), polls until completion, extracts results from output files, and stores
everything in the database.

---

## Prerequisites

- Phase 0 complete (all of `bulbe/core/`, `bulbe/plugins/schedulers/`,
  `bulbe/plugins/sweeps/`, `bulbe/plugins/analysis/patterns.py`,
  `bulbe/plugins/system/cpuinfo.py`, and `bulbe/cli/main.py` exist)

---

## Scope

### In Scope
- `SweepExpander`: a utility that calls registered sweep plugins to expand
  a `BenchmarkDef` into a flat `list[Experiment]`
- `ScriptGenerator` plugin interface + Slurm implementation that writes
  a complete SBATCH script to disk
- `RunOrchestrator`: submit experiments, poll until done, collect results
- Wire `bulbe run <file>` end-to-end using the orchestrator
- Wire `bulbe status [run_id]` to show live DB state
- Wire `bulbe results [benchmark]` to query results from the DB
- Local scheduler working end-to-end for tests without Slurm
- Integration test using the local scheduler

### Out of Scope
- Live streaming of job output during run (`bulbe tail` — Phase 5)
- Dependency analysis campaigns (Phase 2)
- PostgreSQL backend (Phase 3)
- HTML/plot reporting (Phase 4)
- TUI (Phase 5)
- `bulbe cancel`, `bulbe monitor` commands (Phase 5)
- Script linting / `sbatch --test-only` validation (post-Phase 1 polish)

---

## Key Decisions

- **Engine lives in `bulbe/engine/`**, not in the CLI or in a plugin. The CLI
  stays thin (argument parsing + display only). The engine has no CLI imports.
- **Sweep expansion is synchronous and eager**: all experiments are expanded
  before any submission. This simplifies error handling and progress display.
  Large parameter spaces (>10 000 experiments) are not a target use case.
- **Script generator is a plugin** (`category = "generator"`) so it can be
  replaced per-scheduler. The Slurm generator is the built-in default.
- **Polling is the completion mechanism**: the orchestrator polls `scheduler.status()`
  on a configurable interval. There are no callbacks or event hooks in Phase 1.
- **Result extraction happens immediately after a run completes**, not as a
  separate step. The orchestrator calls the pattern extractor before moving on.
- **The local scheduler writes scripts to temp dirs and runs them as subprocesses.**
  It does not mock anything — it actually executes the generated script.
- **Run working directory** is `<config.workdir>/<benchmark_name>/<run_id>/`.
  It is created before script generation and contains: the script, stdout, stderr,
  and any files the benchmark produces.

---

## New Data Structures

```python
# bulbe/engine/orchestrator.py

from dataclasses import dataclass, field
from enum import Enum

class SubmitMode(Enum):
    """Controls how the orchestrator submits experiments."""
    ALL = "all"         # Submit all experiments immediately (default)
    SEQUENTIAL = "seq"  # Submit one, wait, submit next (for tests)


@dataclass
class OrchestratorConfig:
    """Runtime parameters for the orchestrator."""
    poll_interval: int = 30        # seconds between status polls
    max_wait: int = 86400          # maximum total wait time in seconds (24h)
    submit_mode: SubmitMode = SubmitMode.ALL
    dry_run: bool = False          # generate scripts but do not submit
```

No new core models are added in this phase.
`Run`, `Experiment`, `ResultRecord`, `SystemInfo` from Phase 0 are used as-is.

---

## Tasks

---
### TASK-1-1: Create sweep expander utility

**File:** `bulbe/engine/sweep_expander.py` — CREATE

**Depends on:** none

**Context:**
The `BenchmarkDef` model contains a list of `SweepDef` objects. Each registered
sweep plugin knows how to expand one `SweepDef` into a set of parameter combinations.
This utility calls the registered sweep plugins in order and returns a flat list of
`Experiment` objects — one per unique parameter combination. It is the bridge between
the YAML definition and the actual runs.

**Interface:**
```python
class SweepExpander:
    """Expands a BenchmarkDef into a flat list of Experiments using sweep plugins."""

    def __init__(self, registry: PluginRegistry) -> None: ...

    def expand(self, benchmark: BenchmarkDef) -> list[Experiment]:
        """Expand all sweeps in benchmark into a flat list of Experiments.

        If benchmark has no sweeps defined, returns a single Experiment
        with the base parameters from benchmark.job.

        Returns experiments in a deterministic order (sorted by parameter
        combination string representation).

        Raises:
            PluginNotFoundError: if a sweep type referenced in benchmark is
                not registered in the registry.
        """
        ...
```

**Behavior:**
- If `benchmark.sweeps` is empty, returns `[Experiment(params=base_params)]`
  where `base_params` is derived from `benchmark.job` (nodes, tasks_per_node, etc.)
- Each `Experiment` has a unique `id` (hex UUID, 12 chars)
- Each `Experiment` has `benchmark_name` set to `benchmark.name`
- Each `Experiment` has `params` dict containing all swept parameter values
- The Cartesian product of independent sweep axes is computed: if sweep A
  produces `[x1, x2]` and sweep B produces `[y1, y2]`, the result is
  `[x1+y1, x1+y2, x2+y1, x2+y2]`
- Sweep plugins are called via `registry.get("sweep", sweep_def.type)`
- Raises `PluginNotFoundError` (not `KeyError`) if sweep type not found

**Tests:**
File: `tests/unit/test_sweep_expander.py` — CREATE
- `test_no_sweeps_returns_single_experiment`: BenchmarkDef with no sweeps → list of 1
- `test_scaling_sweep_returns_n_experiments`: nodes=[1,2,4] → 3 experiments
- `test_cartesian_product_of_two_sweeps`: 3 nodes × 2 freqs → 6 experiments
- `test_experiments_have_unique_ids`: no two experiments share an id
- `test_unknown_sweep_type_raises`: unregistered sweep type raises `PluginNotFoundError`
- `test_benchmark_name_propagated`: each experiment has correct `benchmark_name`

**Acceptance Criteria:**
- [ ] All listed tests pass
- [ ] `mypy --strict bulbe/engine/sweep_expander.py` reports zero errors
- [ ] `ruff check bulbe/engine/sweep_expander.py` reports zero errors

---
### TASK-1-2: Create engine package init

**File:** `bulbe/engine/__init__.py` — CREATE

**Depends on:** none

**Context:**
Empty init file to make `bulbe/engine/` a Python package.

**Interface:**
```python
# empty — no public API exported from the package level
```

**Behavior:**
- File is empty (or contains only a module docstring)

**Tests:**
None required.

**Acceptance Criteria:**
- [ ] `python -c "import bulbe.engine"` succeeds without error

---
### TASK-1-3: Create script generator plugin interface

**File:** `bulbe/plugins/generators/__init__.py` — MODIFY

**Depends on:** TASK-1-2

**Context:**
The `generators` plugin category exists but has no Protocol definition.
The Slurm scheduler already contains some script generation logic that must be
extracted into a proper generator plugin. This task defines the Protocol that
all generator plugins must satisfy, so the Slurm generator in TASK-1-4 has
a clear contract to implement.

**Interface:**
```python
from typing import Protocol, runtime_checkable
from pathlib import Path
from bulbe.core.models import Experiment, BenchmarkDef

@runtime_checkable
class ScriptGeneratorProtocol(Protocol):
    """Protocol for all script generator plugins."""
    name: str
    category: str  # must equal "generator"

    def generate(
        self,
        experiment: Experiment,
        benchmark: BenchmarkDef,
        workdir: Path,
    ) -> Path:
        """Generate a job script for experiment and write it to workdir.

        Returns the absolute path to the written script file.

        Raises:
            OSError: if workdir does not exist or is not writable.
            ValueError: if experiment or benchmark contain invalid combinations.
        """
        ...
```

**Behavior:**
- The Protocol is exported from `bulbe.plugins.generators`
- No instantiation happens in this file

**Tests:**
File: `tests/unit/test_generator_protocol.py` — CREATE
- `test_slurm_generator_satisfies_protocol`: after TASK-1-4, assert
  `isinstance(SlurmScriptGenerator(), ScriptGeneratorProtocol)` is True

**Acceptance Criteria:**
- [ ] `from bulbe.plugins.generators import ScriptGeneratorProtocol` works
- [ ] `mypy --strict bulbe/plugins/generators/__init__.py` reports zero errors

---
### TASK-1-4: Implement Slurm script generator plugin

**File:** `bulbe/plugins/generators/slurm_script.py` — CREATE

**Depends on:** TASK-1-3

**Context:**
The Slurm scheduler plugin (`bulbe/plugins/schedulers/slurm.py`) already contains
script generation logic mixed with submission logic. This task extracts script
generation into a standalone generator plugin that satisfies `ScriptGeneratorProtocol`.
The Slurm scheduler plugin's `generate_script` method may delegate to this plugin
or be refactored to call it — but the generator plugin is the canonical implementation.

The generated script must be a valid SBATCH batch script. The script structure is
defined in ARCHITECTURE.md ("Slurm plugin generates" section). Follow it exactly.

**Interface:**
```python
@bulbe_plugin("generator", "slurm")
class SlurmScriptGenerator:
    """Generates SBATCH batch scripts for Slurm job submission."""
    name = "slurm"
    category = "generator"

    def generate(
        self,
        experiment: Experiment,
        benchmark: BenchmarkDef,
        workdir: Path,
    ) -> Path:
        """Generate a complete SBATCH script and write it to workdir/job.sh.

        Returns the absolute path to the written script file (workdir/job.sh).

        Raises:
            OSError: if workdir does not exist.
            ValueError: if experiment.params contains no node count.
        """
        ...

    def _build_header(self, experiment: Experiment, benchmark: BenchmarkDef, workdir: Path) -> str:
        """Build the #SBATCH directive block."""
        ...

    def _build_environment(self, benchmark: BenchmarkDef) -> str:
        """Build module load and export lines."""
        ...

    def _build_execution(self, experiment: Experiment, benchmark: BenchmarkDef) -> str:
        """Build the mpirun/srun execution line with pinning."""
        ...
```

**Behavior:**
- Output file is always named `job.sh` inside `workdir`
- Script begins with `#!/bin/bash`
- `#SBATCH --job-name` is set to `bulbe_{benchmark.name}_{experiment.id}`
- `#SBATCH --output` is set to `{workdir}/stdout.log`
- `#SBATCH --error` is set to `{workdir}/stderr.log`
- All keys from `benchmark.job` (nodes, tasks_per_node, time, partition,
  account, exclusive) are emitted as `#SBATCH` directives if present
- `module purge` is emitted before any `module load` calls
- Each module in `benchmark.app.modules` becomes a `module load <name>` line
- Each key in `benchmark.app.environment` becomes an `export KEY=VALUE` line
- If `benchmark.job.pinning` is set, the pinning prefix is prepended to the launch command
- The launch command is `srun` by default; `mpirun` if `benchmark.app.mpi_launcher == "mpirun"`
- If `experiment.params` contains `cpu_freq`, a `cpupower frequency-set` pre-command is emitted
  before the launch line
- The script is written with mode `0o750` (owner read/write/exec, group read/exec)

**Tests:**
File: `tests/unit/test_slurm_script_generator.py` — CREATE
- `test_generates_job_sh_in_workdir`: file named `job.sh` is created in tmp workdir
- `test_header_contains_sbatch_directives`: nodes, tasks_per_node, time appear as #SBATCH lines
- `test_environment_section_present`: module load and export lines present
- `test_cpu_freq_param_emits_cpupower`: experiment with cpu_freq → cpupower line in script
- `test_no_cpu_freq_param_no_cpupower`: experiment without cpu_freq → no cpupower line
- `test_workdir_not_exist_raises_oserror`: non-existent workdir raises OSError
- `test_script_is_executable`: generated file has executable bit set

**Acceptance Criteria:**
- [ ] All listed tests pass
- [ ] `mypy --strict bulbe/plugins/generators/slurm_script.py` reports zero errors
- [ ] `ruff check bulbe/plugins/generators/slurm_script.py` reports zero errors
- [ ] `isinstance(SlurmScriptGenerator(), ScriptGeneratorProtocol)` is True

---
### TASK-1-5: Implement run orchestrator

**File:** `bulbe/engine/orchestrator.py` — CREATE

**Depends on:** TASK-1-1, TASK-1-2, TASK-1-3, TASK-1-4

**Context:**
This is the core of Phase 1. The orchestrator ties together sweep expansion,
script generation, job submission, status polling, and result extraction into
a single callable function. The CLI `run` command will call `run_benchmark()` and
display progress. The orchestrator has no CLI imports and no Rich/Click dependencies.

**Interface:**
```python
@dataclass
class OrchestratorConfig:
    """Runtime parameters for the orchestrator."""
    poll_interval: int = 30
    max_wait: int = 86400
    submit_mode: SubmitMode = SubmitMode.ALL
    dry_run: bool = False


class RunOrchestrator:
    """Coordinates the full lifecycle of a benchmark run session."""

    def __init__(
        self,
        db: Database,
        registry: PluginRegistry,
        config: OrchestratorConfig | None = None,
    ) -> None: ...

    def run_benchmark(
        self,
        benchmark: BenchmarkDef,
        workdir_root: Path,
        on_submit: Callable[[Experiment, Run], None] | None = None,
        on_complete: Callable[[Run], None] | None = None,
        on_failed: Callable[[Run], None] | None = None,
    ) -> list[Run]:
        """Execute the full benchmark lifecycle for all experiments.

        Expands sweeps, generates scripts, submits all jobs, polls until
        completion, and extracts results for each completed run.

        Args:
            benchmark: loaded BenchmarkDef from YAML
            workdir_root: base directory; each run gets a subdirectory
            on_submit: optional callback invoked immediately after submission
            on_complete: optional callback invoked when a run reaches COMPLETED
            on_failed: optional callback invoked when a run reaches FAILED

        Returns:
            list of all Run objects (final state) sorted by experiment index

        Raises:
            PluginNotFoundError: if required scheduler or generator plugin is missing
            RuntimeError: if max_wait is exceeded before all runs finish
        """
        ...

    def _prepare_workdir(self, benchmark_name: str, run_id: str, workdir_root: Path) -> Path:
        """Create and return the working directory for one run."""
        ...

    def _submit_one(
        self,
        experiment: Experiment,
        benchmark: BenchmarkDef,
        workdir: Path,
    ) -> Run:
        """Generate script, submit job, record Run in DB, return Run."""
        ...

    def _poll_loop(self, runs: list[Run], scheduler: SchedulerProtocol) -> None:
        """Block until all runs reach a terminal state (COMPLETED or FAILED).

        Updates run status in DB as changes are detected.

        Raises:
            RuntimeError: if max_wait seconds elapse without all runs finishing.
        """
        ...

    def _collect_results(self, run: Run, benchmark: BenchmarkDef) -> list[ResultRecord]:
        """Extract results from run output files, store in DB, return records."""
        ...
```

**Behavior:**
- `run_benchmark` returns immediately in `dry_run=True` mode after generating
  scripts; no jobs are submitted; runs are stored with status `DRY_RUN`
- `on_submit`, `on_complete`, `on_failed` callbacks are optional; absence of
  a callback does not change behavior
- Working directory for run `R` is `workdir_root / benchmark.name / R.id`
- Directory is created before script generation; raises `OSError` if it cannot
  be created
- `_submit_one` records the Run in the DB with status `SUBMITTED` before returning
- `_poll_loop` calls `scheduler.status(run.job_id)` every `poll_interval` seconds
- When a run transitions to COMPLETED, `_collect_results` is called immediately
- When a run transitions to FAILED, `on_failed` callback is called; results are
  not extracted (no error is raised — other runs continue)
- A run's `started_at` is set when it first transitions from PENDING/SUBMITTED
  to RUNNING
- A run's `finished_at` is set when it first transitions to COMPLETED or FAILED
- All DB writes are wrapped in transactions (use `db.transaction()`)
- System info is collected via the `system` plugin and stored once per run
  before job submission

**Tests:**
File: `tests/integration/test_orchestrator.py` — CREATE
*(Uses the local scheduler and a temp dir — no Slurm required)*
- `test_run_benchmark_single_experiment`: 1 experiment, local scheduler, completes
- `test_run_benchmark_multiple_experiments`: 3 experiments, all complete
- `test_dry_run_generates_scripts_no_submission`: dry_run=True, no DB job records
- `test_on_complete_callback_called`: callback fires for each completed run
- `test_results_extracted_after_completion`: DB contains ResultRecords after run
- `test_workdir_structure_correct`: workdir/benchmark/run_id/job.sh exists after run
- `test_failed_run_does_not_block_others`: one failing run, others still complete

**Acceptance Criteria:**
- [ ] All listed tests pass
- [ ] `mypy --strict bulbe/engine/orchestrator.py` reports zero errors
- [ ] `ruff check bulbe/engine/orchestrator.py` reports zero errors
- [ ] `bulbe run examples/bulbe/simple_benchmark.yaml --dry-run` executes without error

---
### TASK-1-6: Wire `bulbe run` CLI command

**File:** `bulbe/cli/main.py` — MODIFY

**Depends on:** TASK-1-5

**Context:**
The `run` command in `bulbe/cli/main.py` is currently a stub. This task replaces
the stub body with a call to `RunOrchestrator.run_benchmark()`, adds a Rich
progress display, and wires `--dry-run` and `--scheduler` options. The CLI is
responsible for display only — no business logic here.

**Interface:**
```python
# Additions/modifications to existing CLI command

@cli.command()
@click.argument("benchmark_file", type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True, default=False,
              help="Generate scripts but do not submit jobs.")
@click.option("--scheduler", default=None,
              help="Override default scheduler (slurm, local).")
@click.option("--poll-interval", default=30, show_default=True,
              help="Seconds between status polls.")
@click.pass_context
def run(ctx: click.Context, benchmark_file: Path, dry_run: bool,
        scheduler: str | None, poll_interval: int) -> None:
    """Load BENCHMARK_FILE and run all experiments."""
    ...
```

**Behavior:**
- Loads the benchmark YAML via `Loader.load(benchmark_file)`; prints a
  Rich error panel and exits with code 1 on `LoadError`
- Instantiates `RunOrchestrator` with settings from `AppContext`
- Displays a Rich `Progress` bar with one task per experiment
- The `on_submit` callback advances the progress bar label to show job ID
- The `on_complete` callback marks the progress bar task complete (green)
- The `on_failed` callback marks the progress bar task failed (red)
- After all runs finish, prints a summary table: run ID, experiment params,
  status, duration, key results (first pattern match per run)
- `--scheduler` option, if given, overrides `benchmark.job.scheduler`
- Exits with code 0 if all runs completed, code 2 if any run failed

**Tests:**
File: `tests/integration/test_cli_run.py` — CREATE
- `test_run_dry_run_exits_zero`: `bulbe run simple.yaml --dry-run` exits 0
- `test_run_dry_run_prints_experiment_count`: output contains number of experiments
- `test_run_invalid_yaml_exits_one`: malformed YAML file → exit code 1

**Acceptance Criteria:**
- [ ] All listed tests pass
- [ ] `bulbe run --help` shows all options documented above
- [ ] `bulbe run examples/bulbe/simple_benchmark.yaml --dry-run` runs without error
- [ ] `mypy --strict bulbe/cli/main.py` reports zero errors

---
### TASK-1-7: Wire `bulbe status` CLI command

**File:** `bulbe/cli/main.py` — MODIFY

**Depends on:** TASK-1-5

**Context:**
`bulbe status` (with no argument) shows all recent runs from the DB.
`bulbe status <run_id>` shows details for one run. This command is pure DB
query + display — no orchestrator involvement.

**Interface:**
```python
@cli.command()
@click.argument("run_id", required=False, default=None)
@click.option("--benchmark", "-b", default=None, help="Filter by benchmark name.")
@click.option("--limit", "-n", default=20, show_default=True,
              help="Maximum number of runs to display.")
@click.pass_context
def status(ctx: click.Context, run_id: str | None, benchmark: str | None,
           limit: int) -> None:
    """Show run status. Pass RUN_ID for details on one run."""
    ...
```

**Behavior:**
- With no `run_id`: queries DB for recent runs, displays a Rich table with
  columns: ID (first 8 chars), benchmark, status (color-coded), nodes,
  submitted_at, duration
- With `run_id`: displays a detail panel for that run including all params,
  system info summary, and extracted results
- Status colors: COMPLETED=green, RUNNING=yellow, FAILED=red,
  SUBMITTED/PENDING=cyan, DRY_RUN=dim
- If `run_id` is given but not found in DB, prints error and exits code 1
- `--benchmark` filters the list to only runs of that benchmark name

**Tests:**
File: `tests/integration/test_cli_status.py` — CREATE
- `test_status_empty_db_shows_empty_table`: no runs → table with zero rows, exit 0
- `test_status_with_run_id_shows_details`: after a dry-run, run_id shows detail view
- `test_status_unknown_run_id_exits_one`: unknown id → exit code 1

**Acceptance Criteria:**
- [ ] All listed tests pass
- [ ] `bulbe status --help` shows documented options
- [ ] `mypy --strict` passes on modified sections

---
### TASK-1-8: Wire `bulbe results` CLI command

**File:** `bulbe/cli/main.py` — MODIFY

**Depends on:** TASK-1-5

**Context:**
`bulbe results` shows extracted result records from the DB, filterable by
benchmark name, metric name, and tag. This is the primary way to inspect
benchmark output after runs complete.

**Interface:**
```python
@cli.command()
@click.argument("benchmark_name", required=False, default=None)
@click.option("--metric", "-m", default=None, help="Filter by metric name.")
@click.option("--tag", "-t", multiple=True, help="Filter by tag (repeatable).")
@click.option("--limit", "-n", default=50, show_default=True)
@click.pass_context
def results(ctx: click.Context, benchmark_name: str | None, metric: str | None,
            tag: tuple[str, ...], limit: int) -> None:
    """Show extracted benchmark results."""
    ...
```

**Behavior:**
- Displays a Rich table: run ID (8 chars), benchmark, metric name, value,
  unit, params summary (key=value pairs, truncated to 40 chars)
- If no results found for given filters, prints "No results found." and exits 0
- Multiple `--tag` options are ANDed: run must have all specified tags
- Table is sorted by `finished_at` descending (most recent first)

**Tests:**
File: `tests/integration/test_cli_results.py` — CREATE
- `test_results_empty_db`: no results → "No results found." message, exit 0
- `test_results_filtered_by_benchmark`: only matching benchmark results shown

**Acceptance Criteria:**
- [ ] All listed tests pass
- [ ] `bulbe results --help` shows documented options

---

## Open Questions

1. **MPI launcher command**: The script generator must choose between `srun`
   and `mpirun`. The current models don't have a `mpi_launcher` field on
   `AppConfig`. Either add it to `AppConfig` or default to `srun` always.
   Decision needed before TASK-1-4.

2. **Existing Slurm script generation in `slurm.py`**: The existing
   `SlurmScheduler.generate_script()` method may duplicate TASK-1-4.
   The implementation agent should check `bulbe/plugins/schedulers/slurm.py`
   and either refactor it to delegate to `SlurmScriptGenerator` or remove
   the duplicate. Do not maintain two implementations of the same logic.

3. **`SchedulerProtocol` location**: The `_poll_loop` method in TASK-1-5
   references `SchedulerProtocol`. Verify this Protocol is already defined
   in `bulbe/core/plugin.py` or add it there before implementing TASK-1-5.
