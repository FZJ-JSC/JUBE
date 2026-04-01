# Bulbe

Modular HPC benchmarking toolkit.

Bulbe manages the full lifecycle of benchmark runs: definition, parameter sweeps,
script generation, job submission, monitoring, result extraction, analysis, and
visualization.

## Features

- **YAML-based benchmark definitions** — simple, readable, no XML
- **Plugin architecture** — schedulers, sweeps, monitors, analysis are all pluggable
- **Database-first** — every run and result recorded in SQLite from day one
- **Parameter sweeps** — scaling, CPU frequency, memory bandwidth analysis built-in
- **Script generation** — Slurm scripts with preview, validation, and linting
- **System capture** — hardware/software info recorded per run automatically
- **Result extraction** — regex patterns with filtering, sorting, comparison
- **CLI with Rich output** — tables, colors, syntax highlighting

## Quick Start

```bash
# Install
pip install -e .

# Initialize a project
bulbe init

# Preview a job script
bulbe script show my_benchmark.yaml

# Run a benchmark
bulbe run my_benchmark.yaml

# Check status
bulbe status

# View results
bulbe results
```

## Benchmark Definition

```yaml
benchmark: hpl
app:
  binary: ./xhpl
  modules: [intel-mpi/2021.6, mkl/2023.1]

job:
  nodes: 4
  tasks_per_node: 48
  time: "02:00:00"
  partition: compute

parameters:
  nodes: [1, 2, 4, 8]

sweeps:
  - type: scaling
  - type: frequency
  - type: memory

analysis:
  patterns:
    - name: gflops
      regex: "WR.*\\s+(\\d+\\.\\d+)$"
      unit: GFLOP/s
```

See `examples/bulbe/` for full examples.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design document.

## Requirements

- Python 3.10+
- 3 dependencies: Click, Rich, PyYAML

## License

BSD-2-Clause. See [LICENSE](LICENSE).
