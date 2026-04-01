# Bulbe Architecture Design

## Overview

Bulbe is a modular HPC benchmarking toolkit. It manages the full lifecycle of
benchmark runs: definition, parameter sweeps, script generation, job submission,
monitoring, result extraction, analysis, and visualization.

**Core principles:**
- **Database-first** — every run, parameter, and result is recorded from day one
- **Plugin-based** — all functionality beyond core is a plugin; easy to extend
- **Performance** — no unnecessary overhead; lazy loading; efficient queries
- **Minimal dependencies** — core runs on stdlib + 3 small packages (Click, Rich, PyYAML)
- **Air-gap friendly** — deployable as a tarball, no internet required
- **Clear code** — type-hinted, tested, easy to read and maintain

**Target:** Python 3.10+ (enables modern type hints, match statements, dataclasses)

---

## Project Structure

```
bulbe/
├── __init__.py              # Version only
├── core/                    # Foundation — no plugins depend on each other, all depend on core
│   ├── __init__.py
│   ├── models.py            # Dataclasses: BenchmarkDef, Experiment, Run, Result, SystemInfo
│   ├── database.py          # SQLite backend with WAL mode, prepared statements
│   ├── config.py            # Two-level config: global (~/.config/bulbe/) + project (./bulbe.yaml)
│   ├── plugin.py            # Plugin registry, decorator, auto-discovery
│   └── loader.py            # YAML benchmark definition → model objects
│
├── plugins/                 # Built-in plugins (each is optional, auto-discovered)
│   ├── __init__.py
│   ├── schedulers/          # Job submission backends
│   │   ├── __init__.py
│   │   ├── slurm.py         # Slurm: script generation, sbatch, squeue, scancel
│   │   ├── pbs.py           # PBS/Torque (future)
│   │   └── local.py         # Local execution (for testing)
│   ├── sweeps/              # Parameter sweep strategies
│   │   ├── __init__.py
│   │   ├── scaling.py       # Strong/weak MPI scaling
│   │   ├── frequency.py     # CPU frequency sweeps
│   │   ├── memory.py        # Memory bandwidth (socket placement)
│   │   └── custom.py        # User-defined parameter matrices
│   ├── monitors/            # Live job monitoring
│   │   ├── __init__.py
│   │   ├── tail.py          # Stream job stdout/stderr
│   │   ├── mpi_trace.py     # MPI timing extraction
│   │   └── io_monitor.py    # I/O statistics
│   ├── analysis/            # Post-run analysis
│   │   ├── __init__.py
│   │   ├── patterns.py      # Regex-based result extraction from output
│   │   ├── projections.py   # Performance modeling/extrapolation
│   │   └── comparisons.py   # Cross-run diffing
│   ├── generators/          # Script generation
│   │   ├── __init__.py
│   │   └── slurm_script.py  # Slurm batch script builder
│   ├── results/             # Output formatting
│   │   ├── __init__.py
│   │   ├── tables.py        # Rich tables with filtering
│   │   ├── plots.py         # matplotlib/plotly charts
│   │   └── export.py        # CSV, JSON, PDF reports
│   └── system/              # System info collection
│       ├── __init__.py
│       └── cpuinfo.py       # /proc/cpuinfo, lscpu, topology
│
├── cli/                     # CLI interface (Click + Rich)
│   ├── __init__.py
│   ├── main.py              # Entry point, command groups
│   ├── run.py               # `bulbe run`, `bulbe submit`
│   ├── monitor.py           # `bulbe monitor`, `bulbe tail`
│   ├── results.py           # `bulbe results`, `bulbe compare`
│   ├── db.py                # `bulbe db query`, `bulbe db export`
│   └── templates.py         # `bulbe template create/list/use`
│
├── ui/                      # Future: TUI (Textual) → desktop/web
│   └── __init__.py
│
tests/
├── unit/                    # Fast, no I/O, no subprocess
│   ├── test_models.py
│   ├── test_database.py
│   ├── test_plugin.py
│   ├── test_config.py
│   └── test_loader.py
└── integration/             # Slower, touches filesystem/DB
    ├── test_slurm_plugin.py
    └── test_cli.py
```

---

## Core Components

### 1. Data Models (`core/models.py`)

All data flows through these dataclasses. They are the single source of truth.

```
BenchmarkDef ──(expand sweeps)──→ Experiment[] ──(submit)──→ Run[]
                                                              │
                                                              ├── ResultRecord[]
                                                              └── SystemInfo
```

**Key models:**

| Model | Purpose | Mutable? |
|---|---|---|
| `BenchmarkDef` | The "recipe" — what to run, how | Yes (loaded from YAML, can be modified) |
| `AppConfig` | Binary, modules, env vars | Frozen |
| `JobSpec` | Scheduler directives (nodes, tasks, time) | Frozen |
| `PinningConfig` | Process placement (numactl, rankfile, etc.) | Frozen |
| `SweepDef` | One sweep axis (scaling, freq, memory) | Frozen |
| `PatternDef` | Regex pattern for result extraction | Frozen |
| `MonitorConfig` | What to monitor during run | Frozen |
| `Experiment` | One point in parameter space | Yes (ID assigned at creation) |
| `Run` | One execution of an experiment | Yes (status updates throughout lifecycle) |
| `ResultRecord` | One extracted result value | Frozen |
| `SystemInfo` | Hardware/software captured at run time | Frozen |

**Design choices:**
- Frozen dataclasses for anything that shouldn't change after creation
- `model_to_dict()` for serialization — handles Enum, Path, datetime
- No inheritance — composition only. Keeps the model flat and debuggable
- UUIDs (hex[:12]) for IDs — short enough for humans, unique enough for a DB

### 2. Database (`core/database.py`)

SQLite with WAL mode. Zero setup, works on any cluster.

**Schema:**
- `benchmarks` — stores the full YAML definition as JSON
- `runs` — one row per execution, with status tracking
- `results` — extracted metric values, linked to runs
- `system_info` — hardware/software snapshot per run

**Key features:**
- WAL mode — concurrent reads while monitoring writes
- JSON columns for flexible parameter/result storage
- Indexed on common query paths (benchmark name, status, timestamps)
- Batch insert for results (performance)
- `ON CONFLICT ... DO UPDATE` for idempotent saves
- Transaction context manager for atomicity

**Query patterns supported:**
- List all runs for a benchmark, filtered by status/tags
- Compare a metric across runs
- Get full history for regression detection
- Export to CSV/JSON

**Future: PostgreSQL path.**
The Database class can be subclassed for PostgreSQL when the team needs shared
access. The SQL is deliberately kept compatible — no SQLite-specific functions
except PRAGMAs (which would be swapped for PG connection params).

### 3. Plugin System (`core/plugin.py`)

**Registration:**
```python
@bulbe_plugin("scheduler", "slurm")
class SlurmScheduler:
    name = "slurm"

    def generate_script(self, experiment, app, workdir): ...
    def submit(self, script_path, workdir): ...
    def status(self, job_id): ...
    def cancel(self, job_id): ...
```

**Categories:** scheduler, sweep, monitor, analysis, system, generator, results

**Discovery order:**
1. Built-in plugins (`bulbe/plugins/`) — auto-loaded via `pkgutil.walk_packages`
2. User plugins (`~/.config/bulbe/plugins/`) — loaded from directory
3. Project plugins (`./bulbe_plugins/`) — loaded from directory
4. External plugins (any executable) — declared in config, uses JSON stdio

**Protocol classes** define the interface for each category (using `typing.Protocol`
for structural subtyping — no base class inheritance required).

**Lazy instantiation:** Plugin classes are registered but not instantiated until
first use. This keeps startup fast.

**External plugin interface (JSON stdio):**
Any executable that reads JSON on stdin and writes JSON on stdout is a valid plugin.
This enables plugins in Lua, R, C, shell scripts, or any language.

```yaml
# In bulbe.yaml
plugins:
  - name: my-analyzer
    category: analysis
    command: ./my_analyzer.lua
    interface: json-stdio
```

### 4. Configuration (`core/config.py`)

**Two-level config with env override:**

```
Priority: Environment vars > Project config > Global config > Defaults
```

| Source | Path | Purpose |
|---|---|---|
| Global | `~/.config/bulbe/config.yaml` | User defaults (account, partition, modules) |
| Project | `./bulbe.yaml` | Project-specific settings |
| Environment | `BULBE_*` | CI/automation overrides |

**Key config fields:**
- `workdir` — where run directories are created
- `db_path` — database file location
- `default_scheduler` — slurm, pbs, local
- `default_partition`, `default_account`, `default_time`
- `default_modules` — always loaded
- `extra_plugin_dirs` — additional plugin search paths

**Zero-config startup:** Everything has sensible defaults. `bulbe init` creates
a project config with comments explaining each field.

### 5. Benchmark Loader (`core/loader.py`)

Parses YAML benchmark definitions into model objects.

**Example benchmark YAML:**
```yaml
benchmark: linpack
description: "HPL benchmark on compute partition"

app:
  binary: ./xhpl
  modules: [intel-mpi/2021.6, mkl/2023.1]
  environment:
    I_MPI_FABRICS: "shm:ofi"
    OMP_NUM_THREADS: 1

job:
  scheduler: slurm
  nodes: 4
  tasks_per_node: 48
  time: "02:00:00"
  partition: compute
  account: myproject
  exclusive: true

pinning:
  strategy: numactl
  args: "--cpunodebind=0"

parameters:
  nodes: [1, 2, 4, 8]
  cpu_freq: [2.0GHz, 2.4GHz, 2.8GHz]

sweeps:
  - type: scaling
  - type: frequency
  - type: memory
    parameters:
      placement: [one_socket, both_sockets]

analysis:
  patterns:
    - name: gflops
      regex: "WR.*\\s+(\\d+\\.\\d+)$"
      unit: GFLOP/s
    - name: walltime
      regex: "Time\\s+=\\s+(\\d+\\.\\d+)"
      unit: seconds

monitor:
  tail: true
  io: true

tags:
  cluster: our-cluster
  project: client-x
```

**Loader responsibilities:**
- Validate YAML structure and types
- Apply defaults from config
- Resolve relative paths against project root
- Return a `BenchmarkDef` ready for sweep expansion

---

## Plugin Details

### Scheduler Plugins

**Interface:** `generate_script()`, `submit()`, `status()`, `cancel()`

**Slurm plugin generates:**
```bash
#!/bin/bash
#SBATCH --job-name=bulbe_linpack_001
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=48
#SBATCH --time=02:00:00
#SBATCH --partition=compute
#SBATCH --account=myproject
#SBATCH --exclusive
#SBATCH --output=bulbe_linpack_001.out
#SBATCH --error=bulbe_linpack_001.err

# --- Environment ---
module purge
module load intel-mpi/2021.6 mkl/2023.1
export I_MPI_FABRICS="shm:ofi"
export OMP_NUM_THREADS=1

# --- Pinning ---
PINNING="numactl --cpunodebind=0"

# --- Execution ---
mpirun $PINNING ./xhpl
```

**Script preview:** `bulbe script show <benchmark>` renders the script without submitting.

**Script validation:** Before submission:
- Check nodes × tasks ≤ cluster limits
- Verify modules exist (`module avail`)
- Check binary path exists
- Validate Slurm directive syntax
- Dry-run with `sbatch --test-only`

### Sweep Plugins

**Scaling sweep** — generates experiments varying node count:
```
nodes=[1,2,4,8], tasks_per_node=48 → 4 experiments
```

**Frequency sweep** — generates experiments varying CPU frequency:
```
cpu_freq=[2.0,2.4,2.8] → 3 experiments, each with cpupower pre-command
```

**Memory bandwidth sweep** — the socket placement trick:
```
For each node count:
  1. Normal placement (both sockets) — full bandwidth
  2. Pack on one socket — half bandwidth
→ 2× experiments, measures memory sensitivity
```

This is implemented by generating different pinning configs:
- Both sockets: `--map-by ppr:24:socket`
- One socket: `--map-by ppr:48:socket:PE=1 --bind-to core` + `numactl --cpunodebind=0`

**Custom sweep** — user-defined parameter matrix. Cartesian product of all
parameter values, or an explicit list of combinations.

### Monitor Plugins

**Tail monitor** — streams job stdout in real-time:
- Uses `tail -f` on the output file path
- Works via SSH to compute node if needed
- Displayed with Rich Live in CLI

**MPI trace monitor** — extracts MPI timing:
- Parses Intel MPI trace output (`-trace` flag)
- Extracts: total MPI time, top 10 calls, communication pattern
- Stores in results DB

**I/O monitor** — tracks job I/O:
- Reads `/proc/<pid>/io` on compute nodes (via job script or SSH)
- Extracts: read_bytes, write_bytes, read/write syscalls
- Computes I/O bandwidth over time

### Analysis Plugins

**Pattern extraction** — regex-based result parsing:
- Scans stdout/stderr or any file
- Supports reductions: first, last, min, max, avg, sum
- Results stored in DB immediately

**Performance projections:**
- Fits scaling curves (Amdahl's law, Gustafson's law)
- Extrapolates performance to higher node counts
- Identifies parallel efficiency bottlenecks

**Cross-run comparison:**
- Diff two runs: parameters, results, system info
- Regression detection: flag if metric worsened by >X%
- Trend analysis across tagged runs

### System Info Plugin

Collects hardware/software info at run time — all from `/proc`, `/sys`, and
standard Linux tools. No external dependencies.

**Collected data:**
- CPU: model, cores, sockets, threads, frequencies, cache sizes
- Memory: total, per-NUMA-node, bandwidth (if available)
- GPU: model, count, driver version (nvidia-smi if available)
- Network: interconnect type (Infiniband, OPA, Ethernet)
- Software: OS, kernel, MPI version, compiler, loaded modules
- Topology: NUMA layout, PCIe topology

---

## CLI Design

Built with Click (command routing) + Rich (output formatting).

```
bulbe
├── init                    # Initialize a new Bulbe project
├── run <benchmark.yaml>    # Run a benchmark (expand sweeps, submit all)
├── submit <benchmark.yaml> # Alias for run
├── status [job_id]         # Show run status (like squeue but better)
├── monitor <job_id>        # Live monitoring dashboard
├── tail <job_id>           # Stream job output
├── cancel <job_id>         # Cancel a run
├── results                 # Show results table (with filters!)
│   ├── show <benchmark>    # Table view with filtering and sorting
│   ├── compare <ids...>    # Side-by-side comparison
│   └── export <format>     # CSV, JSON, PDF
├── script                  # Script management
│   ├── show <benchmark>    # Preview generated script
│   ├── lint <script>       # Validate a job script
│   └── fmt <script>        # Format/beautify a script
├── template                # Benchmark templates
│   ├── create <name>       # Save current benchmark as template
│   ├── list                # List available templates
│   └── use <name>          # Start from a template
├── db                      # Database queries
│   ├── query               # Flexible run queries
│   ├── stats               # Summary statistics
│   └── export              # Full DB export
├── plugin                  # Plugin management
│   ├── list                # Show installed plugins
│   └── info <name>         # Plugin details
└── config                  # Configuration
    ├── show                # Show current config
    └── edit                # Open config in editor
```

**Output features:**
- Rich tables with column sorting and filtering
- Color-coded status (green=completed, yellow=running, red=failed)
- Progress bars for multi-experiment submissions
- Live-updating status display

---

## Data Flow

### Full lifecycle of a benchmark run:

```
1. DEFINE
   User writes benchmark.yaml (or uses a template)
        │
        ▼
2. LOAD
   Loader parses YAML → BenchmarkDef
   Config provides defaults, validates
        │
        ▼
3. EXPAND
   Sweep plugins expand parameters → Experiment[]
   Each experiment = one concrete configuration
        │
        ▼
4. GENERATE
   Scheduler plugin generates job scripts
   System info plugin captures environment
   Scripts can be previewed/linted before submission
        │
        ▼
5. SUBMIT
   Scheduler plugin submits jobs → Run[] created in DB
   Status: PENDING → SUBMITTED
        │
        ▼
6. MONITOR
   Monitor plugins track progress (tail, I/O, MPI trace)
   Status: SUBMITTED → RUNNING
   Live updates in CLI/TUI
        │
        ▼
7. COMPLETE
   Job finishes → status COMPLETED or FAILED
   Analysis plugins extract results from output
   Results stored in DB
        │
        ▼
8. ANALYZE
   Pattern extraction, cross-run comparison
   Performance projections, regression detection
        │
        ▼
9. REPORT
   Tables, plots, CSV/JSON/PDF export
   All queryable from CLI or future UI
```

### Database-first guarantee:

Every transition is recorded. If Bulbe crashes mid-run, the DB has the last
known state. Runs can be re-analyzed, results re-extracted. Nothing is lost.

---

## Performance Considerations

- **Startup time:** Plugin auto-discovery uses `pkgutil.walk_packages` (fast,
  no file I/O per module). Plugins are lazy-instantiated.
- **Database:** WAL mode allows concurrent reads during writes. Batch inserts
  for results. Indexes on common query columns.
- **CLI output:** Rich tables are streamed, not buffered. Large result sets
  use pagination.
- **Monitoring:** Poll-based with configurable interval. No busy loops.
- **Memory:** Experiments and runs are generated lazily (generators) for large
  parameter spaces.
- **File I/O:** Minimal — YAML loaded once, scripts written once, results
  extracted once and stored in DB.

---

## Deployment

### Single-user (default):
```bash
tar xf bulbe-0.1.0.tar.gz
export PATH=$PWD/bulbe/bin:$PATH
bulbe init
```

### Team (future):
- PostgreSQL backend for shared DB
- Central template repository
- Shared plugin directory (NFS or git)

### Air-gapped cluster:
All dependencies vendorable. The tarball includes everything needed.
No pip, no internet, no package manager required.

---

## UI Roadmap

```
Phase 1 (now):     CLI with Click + Rich
Phase 2 (soon):    TUI with Textual — terminal UI with live monitoring
Phase 3 (later):   REST API layer (FastAPI or stdlib)
Phase 4 (future):  Web dashboard and/or desktop app (Tauri)
```

The key is the **REST API layer** between core and UIs. Once that exists:
- CLI, TUI, web, and desktop all use the same API
- Features land in one place, available everywhere
- Mobile/remote access becomes possible

---

## Testing Strategy

- **Unit tests:** Cover models, DB operations, config loading, YAML parsing.
  Fast, no subprocess, no filesystem (use `:memory:` DB, tmp dirs).
- **Integration tests:** Cover CLI commands end-to-end, plugin loading,
  script generation. Use `local` scheduler for testing without Slurm.
- **CI:** Run both on every commit. `ruff` for linting, `mypy` for type checking.

---

## Dependencies

| Package | Purpose | Size | Vendorable? | Required? |
|---|---|---|---|---|
| click | CLI framework | ~300KB | Yes | Yes (core) |
| rich | Terminal output (tables, progress, colors) | ~2MB | Yes | Yes (core) |
| pyyaml | YAML parsing | ~300KB | Yes | Yes (core) |
| textual | TUI framework | ~1.5MB | Yes | No (optional) |
| matplotlib | Plotting | ~30MB | Possible | No (optional) |
| fastapi | REST API | ~500KB | Yes | No (future) |

**Core = 3 deps, ~2.6MB total.** Everything else is optional.
