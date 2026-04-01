"""Pattern-based result extraction from benchmark output.

Scans stdout/stderr/files for regex patterns defined in the benchmark YAML.
Supports reductions (first, last, min, max, avg, sum) when a pattern matches
multiple times.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from bulbe.core.models import PatternDef, ResultRecord, Run
from bulbe.core.plugin import bulbe_plugin

logger = logging.getLogger(__name__)

REDUCTIONS = {
    "first": lambda vals: vals[0] if vals else None,
    "last": lambda vals: vals[-1] if vals else None,
    "min": lambda vals: min(vals) if vals else None,
    "max": lambda vals: max(vals) if vals else None,
    "avg": lambda vals: sum(vals) / len(vals) if vals else None,
    "sum": lambda vals: sum(vals) if vals else None,
}


@bulbe_plugin("analysis", "patterns")
class PatternExtractor:
    """Extract results from output files using regex patterns."""

    name = "patterns"

    def extract(self, run: Run, patterns: list[PatternDef]) -> list[ResultRecord]:
        """Extract all pattern matches from a run's output files.

        Args:
            run: The completed run.
            patterns: List of pattern definitions to match.

        Returns:
            List of extracted ResultRecord objects.
        """
        records: list[ResultRecord] = []

        for pattern in patterns:
            file_path = _resolve_output_file(run, pattern.file)
            if file_path is None or not file_path.exists():
                logger.warning(
                    "Output file not found for pattern '%s': %s",
                    pattern.name,
                    pattern.file,
                )
                continue

            try:
                content = file_path.read_text()
            except OSError:
                logger.warning("Could not read %s", file_path)
                continue

            matches = re.findall(pattern.regex, content)
            if not matches:
                logger.debug("No matches for pattern '%s' in %s", pattern.name, file_path)
                continue

            # Convert to numeric values
            values = _convert_matches(matches, pattern.dtype)
            if not values:
                continue

            # Apply reduction
            reduce_fn = REDUCTIONS.get(pattern.reduction, REDUCTIONS["last"])
            value = reduce_fn(values)
            if value is None:
                continue

            records.append(
                ResultRecord(
                    run_id=run.id,
                    name=pattern.name,
                    value=value,
                    unit=pattern.unit,
                )
            )
            logger.debug(
                "Extracted %s = %s %s (from %d matches, reduction=%s)",
                pattern.name,
                value,
                pattern.unit,
                len(values),
                pattern.reduction,
            )

        return records

    def analyze(self, runs: list[Any]) -> dict[str, Any]:
        """Analyze interface — extracts patterns from all runs."""
        all_records: dict[str, list[ResultRecord]] = {}
        for run in runs:
            if hasattr(run, "patterns"):
                records = self.extract(run, run.patterns)
                all_records[run.id] = records
        return {"extracted": all_records}


def _resolve_output_file(run: Run, file_spec: str) -> Path | None:
    """Resolve a file spec to an actual path."""
    workdir = run.workdir

    if file_spec == "stdout":
        # Look for .out file in workdir
        out_files = list(workdir.glob("*.out"))
        return out_files[0] if out_files else None
    elif file_spec == "stderr":
        err_files = list(workdir.glob("*.err"))
        return err_files[0] if err_files else None
    else:
        path = workdir / file_spec
        return path if path.exists() else None


def _convert_matches(matches: list[Any], dtype: str) -> list[float | int | str]:
    """Convert regex matches to typed values."""
    values: list[float | int | str] = []

    for match in matches:
        # If match is a tuple (multiple groups), take the first group
        if isinstance(match, tuple):
            match = match[0]

        try:
            if dtype == "float":
                values.append(float(match))
            elif dtype == "int":
                values.append(int(match))
            else:
                values.append(str(match))
        except (ValueError, TypeError):
            logger.debug("Could not convert '%s' to %s", match, dtype)
            continue

    return values
