"""Memory bandwidth sweep plugin — socket placement trick.

For each node count, generates two experiments:
1. Normal placement (both sockets) — full memory bandwidth
2. Packed on one socket — half effective bandwidth

By comparing performance between the two, you measure memory sensitivity.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from bulbe.core.models import BenchmarkDef, Experiment, PinningConfig
from bulbe.core.plugin import bulbe_plugin


@bulbe_plugin("sweep", "memory")
class MemoryBandwidthSweep:
    """Generate experiments for memory bandwidth sensitivity analysis."""

    name = "memory"

    def generate_experiments(self, benchmark: BenchmarkDef) -> list[Experiment]:
        """Generate paired experiments: full bandwidth vs. half bandwidth.

        Uses socket placement to control effective memory bandwidth.
        """
        node_values = benchmark.parameters.get("nodes")
        if not node_values:
            node_values = [benchmark.job.nodes]
        if not isinstance(node_values, list):
            node_values = [node_values]

        tasks_per_node = benchmark.job.tasks_per_node
        experiments = []

        for nodes in node_values:
            nodes = int(nodes)
            job_both = replace(benchmark.job, nodes=nodes)

            # --- Full bandwidth: processes spread across both sockets ---
            tasks_per_socket = tasks_per_node // 2
            pinning_both = PinningConfig(
                strategy="mpirun",
                map_by=f"ppr:{tasks_per_socket}:socket",
                bind_to="core",
            )

            experiments.append(
                Experiment(
                    benchmark_name=benchmark.name,
                    parameters={
                        **benchmark.parameters,
                        "nodes": nodes,
                        "placement": "both_sockets",
                        "effective_bw": "full",
                    },
                    job=job_both,
                    pinning=pinning_both,
                )
            )

            # --- Half bandwidth: all processes on one socket ---
            # Same total tasks, but packed onto socket 0
            job_packed = replace(benchmark.job, nodes=nodes * 2, tasks_per_node=tasks_per_node)
            pinning_one = PinningConfig(
                strategy="numactl",
                args="--cpunodebind=0 --membind=0",
                map_by=f"ppr:{tasks_per_node}:socket",
                bind_to="core",
            )

            experiments.append(
                Experiment(
                    benchmark_name=benchmark.name,
                    parameters={
                        **benchmark.parameters,
                        "nodes": nodes * 2,
                        "placement": "one_socket",
                        "effective_bw": "half",
                    },
                    job=job_packed,
                    pinning=pinning_one,
                )
            )

        return experiments
