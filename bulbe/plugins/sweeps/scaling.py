"""Scaling sweep plugin — strong/weak MPI scaling.

Generates experiments varying node count while keeping problem size
constant (strong) or proportional (weak).
"""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any

from bulbe.core.models import BenchmarkDef, Experiment, JobSpec
from bulbe.core.plugin import bulbe_plugin


@bulbe_plugin("sweep", "scaling")
class ScalingSweep:
    """Generate experiments for MPI scaling studies."""

    name = "scaling"

    def generate_experiments(self, benchmark: BenchmarkDef) -> list[Experiment]:
        """Expand node counts from parameters into individual experiments."""
        node_values = benchmark.parameters.get("nodes")
        if not node_values:
            node_values = [benchmark.job.nodes]
        if not isinstance(node_values, list):
            node_values = [node_values]

        experiments = []
        for nodes in node_values:
            job = replace(benchmark.job, nodes=int(nodes))
            params = {**benchmark.parameters, "nodes": nodes}
            params.pop("nodes", None)  # Don't duplicate in params dict

            experiments.append(
                Experiment(
                    benchmark_name=benchmark.name,
                    parameters={"nodes": int(nodes), **params},
                    job=job,
                    pinning=benchmark.pinning,
                )
            )

        return experiments
