"""Frequency sweep plugin — CPU frequency dependency.

Generates experiments varying CPU frequency to measure frequency sensitivity.
Uses cpupower or /sys/devices/system/cpu to set frequency before each run.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from bulbe.core.models import BenchmarkDef, Experiment
from bulbe.core.plugin import bulbe_plugin


@bulbe_plugin("sweep", "frequency")
class FrequencySweep:
    """Generate experiments for CPU frequency sweeps."""

    name = "frequency"

    def generate_experiments(self, benchmark: BenchmarkDef) -> list[Experiment]:
        """Expand cpu_freq parameter into individual experiments."""
        freq_values = benchmark.parameters.get("cpu_freq")
        if not freq_values:
            return []
        if not isinstance(freq_values, list):
            freq_values = [freq_values]

        experiments = []
        for freq in freq_values:
            freq_str = str(freq)
            # Normalize: "2.4GHz" → "2400000" (kHz for cpupower)
            freq_khz = _freq_to_khz(freq_str)

            pre_cmd = (
                f"cpupower frequency-set -g userspace -f {freq_khz} 2>/dev/null || "
                f"echo 'Warning: could not set frequency to {freq_str}'"
            )

            experiments.append(
                Experiment(
                    benchmark_name=benchmark.name,
                    parameters={**benchmark.parameters, "cpu_freq": freq_str},
                    job=benchmark.job,
                    pinning=benchmark.pinning,
                    pre_commands=[pre_cmd],
                )
            )

        return experiments


def _freq_to_khz(freq: str) -> str:
    """Convert frequency string to kHz for cpupower.

    Accepts: "2.4GHz", "2400MHz", "2400000", "2.4"
    Returns: kHz string like "2400000"
    """
    freq = freq.strip()

    if freq.lower().endswith("ghz"):
        ghz = float(freq[:-3])
        return str(int(ghz * 1_000_000))
    elif freq.lower().endswith("mhz"):
        mhz = float(freq[:-3])
        return str(int(mhz * 1_000))
    elif "." in freq:
        # Assume GHz if decimal
        ghz = float(freq)
        return str(int(ghz * 1_000_000))
    else:
        # Assume already kHz
        return freq
