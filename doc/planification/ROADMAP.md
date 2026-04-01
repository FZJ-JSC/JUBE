# Bulbe — Implementation Roadmap

## Vision

Bulbe is a modular HPC benchmarking tool that manages the full lifecycle:
**definition → execution → analysis → projection → reporting**.

Its core unique value is the **dependency analysis model**: a quantitative,
reproducible methodology for projecting benchmark performance from a known
reference machine to any target architecture.

---

## Phase Overview

| Phase | Name | Deliverable | Depends on |
|---|---|---|---|
| 0 | Foundation | Core models, DB, plugin system, config, YAML loader, CLI skeleton | — |
| 1 | Execution Engine | End-to-end `bulbe run`: sweeps → scripts → submit → poll → collect | Phase 0 |
| 2 | Dependency Model | Campaign system, coefficient computation, projection engine | Phase 1 |
| 3 | Shared Database | PostgreSQL backend, team namespacing, multi-user support | Phase 1 |
| 4 | Reporting | CSV/JSON/HTML export, scaling plots, projection reports | Phase 2 |
| 5 | TUI | Live monitoring dashboard, results browser, campaign manager | Phase 1, 4 |

**Phase 0 is complete.** Implementation starts at Phase 1.

---

## Phase Descriptions

### Phase 0 — Foundation *(COMPLETE)*
**Delivered:**
- `bulbe/core/`: models, database (SQLite), plugin registry, config, YAML loader
- `bulbe/plugins/schedulers/`: Slurm and local scheduler
- `bulbe/plugins/sweeps/`: scaling, frequency, memory bandwidth
- `bulbe/plugins/analysis/patterns.py`: regex result extraction
- `bulbe/plugins/system/cpuinfo.py`: hardware/software info collection
- `bulbe/cli/main.py`: Click CLI skeleton with stub commands

**State at exit:** The framework exists. Nothing runs end-to-end yet.

---

### Phase 1 — Execution Engine
**Goal:** `bulbe run benchmark.yaml` works completely, end-to-end.

**Delivers:**
- Sweep expander: `BenchmarkDef` → `list[Experiment]`
- Script generator plugin: `Experiment` → SBATCH/bash script file
- Run orchestrator: submit → poll → collect → store loop
- Wired `bulbe run` and `bulbe status` CLI commands
- Result extraction wired to run completion

**State at exit:** A user can define a benchmark in YAML, run `bulbe run`,
watch it submit to Slurm, poll until done, extract results, and query them
with `bulbe results`.

---

### Phase 2 — Dependency Analysis Model
**Goal:** Quantitative performance projection from reference to target machine.

**Delivers:**
- `DependencyCampaign` concept: named set of coordinated sweeps
- Campaign YAML definition format (extends benchmark YAML)
- Coefficient computation engine (α: compute, β: memory, γ: MPI, δ: I/O)
- `TargetMachine` model (target machine specs)
- Projection formula and `ProjectionResult` model
- `bulbe campaign run`, `bulbe campaign analyze`, `bulbe project` CLI commands

**State at exit:** A user runs `bulbe campaign run campaign.yaml`, waits for
all coordinated sweeps to complete, then runs `bulbe campaign analyze` to get
dependency coefficients and `bulbe project --target machine.yaml` to get a
projected runtime with confidence intervals.

---

### Phase 3 — Shared Database
**Goal:** 20-person team shares a single database.

**Delivers:**
- `DatabaseBackend` protocol abstracting SQLite and PostgreSQL
- `PostgreSQLDatabase` implementation
- `db_url` config key (e.g. `postgresql://user:pass@host/bulbe`)
- `BULBE_DB_URL` environment variable override
- User namespacing (runs tagged with `owner`)
- `bulbe db migrate` command

**State at exit:** The team runs Bulbe against a shared PostgreSQL instance.
Each user's runs are visible to all but tagged with their username. SQLite
remains available for local/air-gapped use.

---

### Phase 4 — Reporting
**Goal:** Machine-readable and human-readable output from all result types.

**Delivers:**
- `bulbe results export --format csv|json` wired end-to-end
- `bulbe report generate` → HTML report with embedded plots
- Scaling efficiency plot (parallel efficiency vs node count)
- Dependency pie chart (α/β/γ/δ breakdown)
- Projection summary table (reference vs target, per metric)
- matplotlib used for plots (optional dependency)

**State at exit:** A user runs `bulbe report generate --campaign <id>`
and gets a self-contained HTML file with all results, plots, and projections,
suitable for sharing with a customer.

---

### Phase 5 — TUI
**Goal:** Terminal UI for live monitoring and interactive result exploration.

**Delivers:**
- `bulbe monitor` opens a Textual app
- Live job status dashboard (updates every N seconds)
- Results browser (filterable, sortable table)
- Campaign overview screen

**State at exit:** `bulbe monitor` replaces `watch bulbe status` with a
proper interactive terminal application.

---

## Dependency Graph

```
Phase 0 (Foundation)
    │
    ▼
Phase 1 (Execution Engine) ──────────────────────┐
    │                                             │
    ├──────────────┐                              │
    ▼              ▼                              ▼
Phase 2        Phase 3                        Phase 5
(Dependency    (Shared DB)                    (TUI)
 Model)
    │
    ▼
Phase 4
(Reporting)
```

Phases 2, 3, and 5 can be worked on in parallel once Phase 1 is complete.
Phase 4 requires Phase 2 (needs dependency coefficients to report on).

---

## What Bulbe Deliberately Does NOT Do

- No job scheduling (Slurm/PBS handle that)
- No source code compilation or build system integration
- No automatic cluster discovery or SSH management
- No web server or cloud sync (Phase 3 uses PostgreSQL directly)
- No machine learning for projections (deterministic analytical model only)
- No support for non-Linux systems

---

## Air-Gap Deployment

Every phase must remain deployable in an air-gapped environment:

- All Python dependencies listed in `pyproject.toml` must be vendorable
- No network calls at runtime (no telemetry, no update checks, no remote plugins)
- Database migrations run locally
- HTML reports are self-contained (no CDN links)
- Optional dependencies (matplotlib, textual, psycopg2) are truly optional —
  the tool must degrade gracefully when they are absent

---

## Open Questions (Cross-Phase)

These questions affect multiple phases and must be resolved before the
relevant phase plan is finalized:

1. **"UI dependency"** in the projection model: the user mentioned running
   a test for "UI dependency" alongside MPI, frequency, and memory sweeps.
   Clarification needed: is this I/O dependency, or a different metric?
   *(Affects Phase 2)*

2. **Scalability campaign format**: scalability tests at scale may need
   different sweep configurations from dependency campaigns. Clarification
   needed on whether they are a separate campaign type or parameterized
   dependency campaigns. *(Affects Phase 2)*

3. **Per-user vs shared database**: the preference for "maybe personal too"
   needs to be resolved before Phase 3 is finalized. Options:
   a) Single shared DB with user tags
   b) Per-user DB + optional aggregation view
   c) Both, configurable
   *(Affects Phase 3)*
