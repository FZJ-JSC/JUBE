"""Bulbe CLI entry point.

All commands are Click groups/commands. Output uses Rich for formatting.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bulbe import __version__
from bulbe.core.config import BulbeConfig
from bulbe.core.database import Database
from bulbe.core.plugin import PluginRegistry

console = Console()

# Shared state passed via Click context
class AppContext:
    def __init__(self) -> None:
        self.config: BulbeConfig = BulbeConfig()
        self.db: Database | None = None
        self.verbose: bool = False

    def get_db(self) -> Database:
        if self.db is None:
            self.db = Database(self.config.db_path)
            self.db.initialize()
        return self.db


pass_ctx = click.make_pass_decorator(AppContext, ensure=True)


@click.group()
@click.version_option(__version__, prog_name="bulbe")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, no_color: bool) -> None:
    """Bulbe — Modular HPC benchmarking toolkit."""
    app = AppContext()
    app.config = BulbeConfig.load()
    app.verbose = verbose or app.config.verbose

    if no_color:
        app.config.color = False

    if app.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    # Load built-in plugins
    registry = PluginRegistry.get()
    registry.load_builtins()

    # Load user plugins
    for plugin_dir in [app.config.plugins_dir, *app.config.extra_plugin_dirs]:
        registry.load_from_directory(plugin_dir)

    ctx.obj = app


# --- init ---

@cli.command()
@pass_ctx
def init(ctx: AppContext) -> None:
    """Initialize a new Bulbe project in the current directory."""
    project_file = Path.cwd() / "bulbe.yaml"

    if project_file.exists():
        console.print("[yellow]bulbe.yaml already exists in this directory.[/yellow]")
        return

    ctx.config.ensure_dirs()

    template = """\
# Bulbe project configuration
# See: bulbe config show (for current settings)

# Default scheduler settings
default_scheduler: slurm
# default_partition: compute
# default_account: myproject
# default_time: "02:00:00"

# Default modules loaded for every run
# default_modules:
#   - intel-mpi/2021.6

# Working directory for run outputs
workdir: bulbe_runs

# Database file
db_path: bulbe.db
"""
    project_file.write_text(template)

    # Initialize DB
    db = ctx.get_db()
    db.close()

    console.print(f"[green]Initialized Bulbe project in {Path.cwd()}[/green]")
    console.print(f"  Config: {project_file}")
    console.print(f"  Database: {ctx.config.db_path}")
    console.print(f"  Workdir: {ctx.config.workdir}")
    console.print("\nNext: create a benchmark YAML file and run [bold]bulbe run <file>[/bold]")


# --- run ---

@cli.command("run")
@click.argument("benchmark_file", type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Generate scripts but don't submit")
@click.option("--tag", multiple=True, help="Add tags (key=value)")
@pass_ctx
def run_benchmark(ctx: AppContext, benchmark_file: Path, dry_run: bool, tag: tuple[str, ...]) -> None:
    """Run a benchmark from a YAML definition file."""
    from bulbe.core.loader import LoadError, load_benchmark, validate_benchmark

    # Parse tags
    tags = {}
    for t in tag:
        if "=" in t:
            k, v = t.split("=", 1)
            tags[k] = v
        else:
            console.print(f"[red]Invalid tag format: {t} (expected key=value)[/red]")
            sys.exit(1)

    # Load benchmark
    try:
        benchmark = load_benchmark(benchmark_file, ctx.config)
    except LoadError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    # Validate
    warnings = validate_benchmark(benchmark)
    for w in warnings:
        console.print(f"[yellow]Warning: {w}[/yellow]")

    # Apply CLI tags
    benchmark.tags.update(tags)

    console.print(f"\n[bold]Benchmark:[/bold] {benchmark.name}")
    console.print(f"[bold]Binary:[/bold]    {benchmark.app.binary}")
    console.print(f"[bold]Scheduler:[/bold] {benchmark.job.scheduler}")
    console.print(f"[bold]Nodes:[/bold]     {benchmark.job.nodes}")
    console.print(f"[bold]Tasks:[/bold]     {benchmark.job.nodes * benchmark.job.tasks_per_node}")

    if benchmark.sweeps:
        console.print(f"[bold]Sweeps:[/bold]    {', '.join(s.type for s in benchmark.sweeps)}")

    if benchmark.parameters:
        console.print(f"[bold]Parameters:[/bold]")
        for k, v in benchmark.parameters.items():
            console.print(f"  {k}: {v}")

    if dry_run:
        console.print("\n[yellow]Dry run — scripts generated but not submitted.[/yellow]")
        # TODO: Generate and display scripts
        return

    # TODO: Expand sweeps → experiments → submit via scheduler plugin
    console.print("\n[yellow]Submission not yet implemented. Use --dry-run to preview.[/yellow]")


# --- status ---

@cli.command()
@click.argument("run_id", required=False)
@pass_ctx
def status(ctx: AppContext, run_id: str | None) -> None:
    """Show run status. Without arguments, shows all recent runs."""
    db = ctx.get_db()

    if run_id:
        run = db.get_run(run_id)
        if not run:
            console.print(f"[red]Run not found: {run_id}[/red]")
            sys.exit(1)
        _print_run_detail(run)
    else:
        runs = db.list_runs(limit=20)
        if not runs:
            console.print("[dim]No runs found. Run a benchmark first.[/dim]")
            return
        _print_runs_table(runs)


# --- results ---

@cli.command()
@click.argument("benchmark_name", required=False)
@click.option("--status", "filter_status", help="Filter by status")
@click.option("--tag", multiple=True, help="Filter by tag (key=value)")
@click.option("--limit", default=50, help="Max results to show")
@click.option("--sort", "sort_by", help="Sort by column")
@pass_ctx
def results(
    ctx: AppContext,
    benchmark_name: str | None,
    filter_status: str | None,
    tag: tuple[str, ...],
    limit: int,
    sort_by: str | None,
) -> None:
    """Show benchmark results with filtering and sorting."""
    db = ctx.get_db()

    # Parse tag filters
    tag_filters = {}
    for t in tag:
        if "=" in t:
            k, v = t.split("=", 1)
            tag_filters[k] = v

    runs = db.list_runs(
        benchmark_name=benchmark_name,
        status=filter_status,
        limit=limit,
        tags=tag_filters if tag_filters else None,
    )

    if not runs:
        console.print("[dim]No matching runs found.[/dim]")
        return

    _print_runs_table(runs, sort_by=sort_by)


# --- script ---

@cli.group()
def script() -> None:
    """Script generation and validation."""


@script.command("show")
@click.argument("benchmark_file", type=click.Path(exists=True, path_type=Path))
@pass_ctx
def script_show(ctx: AppContext, benchmark_file: Path) -> None:
    """Preview the generated job script without submitting."""
    from bulbe.core.loader import LoadError, load_benchmark

    try:
        benchmark = load_benchmark(benchmark_file, ctx.config)
    except LoadError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    registry = PluginRegistry.get()
    scheduler_name = benchmark.job.scheduler

    if not registry.has_plugin("scheduler", scheduler_name):
        console.print(f"[red]No scheduler plugin for '{scheduler_name}'[/red]")
        sys.exit(1)

    scheduler = registry.get_plugin("scheduler", scheduler_name)
    script_content = scheduler.generate_script(
        experiment=None,  # TODO: pass real experiment after sweep expansion
        app=benchmark.app,
        workdir=ctx.config.workdir,
        job=benchmark.job,
        benchmark_name=benchmark.name,
    )

    from rich.syntax import Syntax

    syntax = Syntax(script_content, "bash", theme="monokai", line_numbers=True)
    console.print(syntax)


# --- template ---

@cli.group()
def template() -> None:
    """Manage benchmark templates."""


@template.command("list")
@pass_ctx
def template_list(ctx: AppContext) -> None:
    """List available benchmark templates."""
    templates_dir = ctx.config.templates_dir
    if not templates_dir.exists():
        console.print("[dim]No templates found. Create one with: bulbe template create <name>[/dim]")
        return

    table = Table(title="Benchmark Templates")
    table.add_column("Name", style="bold")
    table.add_column("File")

    for f in sorted(templates_dir.glob("*.yaml")):
        table.add_row(f.stem, str(f))

    console.print(table)


# --- config ---

@cli.group()
def config() -> None:
    """Configuration management."""


@config.command("show")
@pass_ctx
def config_show(ctx: AppContext) -> None:
    """Show current configuration."""
    from rich.pretty import Pretty

    console.print(Pretty(ctx.config.to_dict()))


# --- plugin ---

@cli.group()
def plugin() -> None:
    """Plugin management."""


@plugin.command("list")
def plugin_list() -> None:
    """List all registered plugins."""
    registry = PluginRegistry.get()

    table = Table(title="Installed Plugins")
    table.add_column("Category", style="bold")
    table.add_column("Name")
    table.add_column("Type")

    for entry in registry.list_plugins():
        ptype = "external" if entry.external_command else "python"
        table.add_row(entry.category, entry.name, ptype)

    if not registry.list_plugins():
        console.print("[dim]No plugins loaded.[/dim]")
    else:
        console.print(table)


# --- db ---

@cli.group()
def db() -> None:
    """Database operations."""


@db.command("stats")
@pass_ctx
def db_stats(ctx: AppContext) -> None:
    """Show database statistics."""
    database = ctx.get_db()

    total_runs = database.get_run_count()
    benchmarks = database.list_benchmarks()

    console.print(f"[bold]Database:[/bold] {ctx.config.db_path}")
    console.print(f"[bold]Total runs:[/bold] {total_runs}")
    console.print(f"[bold]Benchmarks:[/bold] {len(benchmarks)}")

    if benchmarks:
        table = Table(title="Benchmarks")
        table.add_column("Name", style="bold")
        table.add_column("Runs", justify="right")
        table.add_column("Last Updated")

        for b in benchmarks:
            count = database.get_run_count(b["name"])
            table.add_row(b["name"], str(count), b["updated_at"])

        console.print(table)


# --- Helpers ---

def _print_runs_table(runs: list[dict], sort_by: str | None = None) -> None:
    """Print a table of runs."""
    if sort_by and runs:
        runs = sorted(runs, key=lambda r: r.get(sort_by, ""), reverse=True)

    table = Table()
    table.add_column("ID", style="bold", max_width=12)
    table.add_column("Benchmark")
    table.add_column("Status")
    table.add_column("Job ID")
    table.add_column("Submitted")
    table.add_column("Parameters")

    status_colors = {
        "pending": "dim",
        "submitted": "blue",
        "running": "yellow",
        "completed": "green",
        "failed": "red",
        "cancelled": "dim red",
    }

    for run in runs:
        status_val = run.get("status", "unknown")
        color = status_colors.get(status_val, "white")
        params = run.get("parameters", {})
        params_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else ""

        table.add_row(
            run.get("id", "")[:12],
            run.get("benchmark_name", ""),
            f"[{color}]{status_val}[/{color}]",
            run.get("job_id", ""),
            run.get("submitted_at", "")[:19] if run.get("submitted_at") else "",
            params_str[:50],
        )

    console.print(table)


def _print_run_detail(run: dict) -> None:
    """Print detailed info for a single run."""
    console.print(f"\n[bold]Run:[/bold] {run['id']}")
    console.print(f"[bold]Benchmark:[/bold] {run['benchmark_name']}")
    console.print(f"[bold]Status:[/bold] {run['status']}")
    console.print(f"[bold]Job ID:[/bold] {run.get('job_id', 'N/A')}")
    console.print(f"[bold]Submitted:[/bold] {run.get('submitted_at', 'N/A')}")
    console.print(f"[bold]Started:[/bold] {run.get('started_at', 'N/A')}")
    console.print(f"[bold]Completed:[/bold] {run.get('completed_at', 'N/A')}")
    console.print(f"[bold]Exit code:[/bold] {run.get('exit_code', 'N/A')}")

    if run.get("parameters"):
        console.print("\n[bold]Parameters:[/bold]")
        for k, v in run["parameters"].items():
            console.print(f"  {k}: {v}")

    if run.get("results"):
        console.print("\n[bold]Results:[/bold]")
        for k, v in run["results"].items():
            console.print(f"  {k}: {v}")

    if run.get("error_message"):
        console.print(f"\n[red]Error: {run['error_message']}[/red]")
