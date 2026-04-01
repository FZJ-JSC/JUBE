"""CPU and system information collector.

Reads from /proc, /sys, and standard Linux tools. No external dependencies.
Captures everything needed to reproduce a benchmark environment.
"""

from __future__ import annotations

import logging
import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

from bulbe.core.models import SystemInfo
from bulbe.core.plugin import bulbe_plugin

logger = logging.getLogger(__name__)


@bulbe_plugin("system", "cpuinfo")
class CPUInfoCollector:
    """Collect CPU and system information from the local node."""

    name = "cpuinfo"

    def collect(self) -> dict[str, Any]:
        """Collect system information. Returns a dict matching SystemInfo fields."""
        info: dict[str, Any] = {}

        info["hostname"] = platform.node()
        info["os_version"] = platform.platform()
        info["kernel_version"] = platform.release()

        # CPU info from /proc/cpuinfo
        cpu = _parse_proc_cpuinfo()
        info["cpu_model"] = cpu.get("model", "")
        info["cpu_cores"] = cpu.get("cores", 0)
        info["cpu_sockets"] = cpu.get("sockets", 0)
        info["cpu_threads_per_core"] = cpu.get("threads_per_core", 0)

        # NUMA topology
        info["numa_nodes"] = _count_numa_nodes()

        # Memory
        info["memory_total_gb"] = _get_memory_gb()

        # GPU (nvidia-smi if available)
        gpu = _detect_gpu()
        info["gpu_model"] = gpu.get("model", "")
        info["gpu_count"] = gpu.get("count", 0)

        # MPI version
        info["mpi_version"] = _get_mpi_version()

        # Loaded modules
        info["modules_loaded"] = _get_loaded_modules()

        # Interconnect
        info["interconnect"] = _detect_interconnect()

        return info

    def collect_as_model(self) -> SystemInfo:
        """Collect and return as a SystemInfo dataclass."""
        data = self.collect()
        return SystemInfo(**{k: v for k, v in data.items() if k in SystemInfo.__dataclass_fields__})


def _parse_proc_cpuinfo() -> dict[str, Any]:
    """Parse /proc/cpuinfo for CPU details."""
    result: dict[str, Any] = {"model": "", "cores": 0, "sockets": 0, "threads_per_core": 0}

    try:
        content = Path("/proc/cpuinfo").read_text()
    except OSError:
        # Try lscpu as fallback
        return _parse_lscpu()

    # Extract model name from first processor entry
    match = re.search(r"model name\s*:\s*(.+)", content)
    if match:
        result["model"] = match.group(1).strip()

    # Count physical IDs (sockets) and processor entries
    physical_ids = set()
    core_ids_per_socket: dict[str, set[str]] = {}
    processor_count = 0

    for block in content.split("\n\n"):
        if "processor" not in block:
            continue
        processor_count += 1

        phys_match = re.search(r"physical id\s*:\s*(\d+)", block)
        core_match = re.search(r"core id\s*:\s*(\d+)", block)

        if phys_match:
            phys_id = phys_match.group(1)
            physical_ids.add(phys_id)
            if core_match:
                core_ids_per_socket.setdefault(phys_id, set()).add(core_match.group(1))

    num_sockets = len(physical_ids) or 1
    total_cores = sum(len(cores) for cores in core_ids_per_socket.values())
    if total_cores == 0:
        total_cores = processor_count

    result["sockets"] = num_sockets
    result["cores"] = total_cores
    result["threads_per_core"] = processor_count // total_cores if total_cores > 0 else 1

    return result


def _parse_lscpu() -> dict[str, Any]:
    """Fallback: parse lscpu output."""
    result: dict[str, Any] = {"model": "", "cores": 0, "sockets": 0, "threads_per_core": 0}

    try:
        out = subprocess.run(["lscpu"], capture_output=True, text=True, timeout=5)
        if out.returncode != 0:
            return result
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return result

    for line in out.stdout.splitlines():
        if "Model name:" in line:
            result["model"] = line.split(":", 1)[1].strip()
        elif "Socket(s):" in line:
            result["sockets"] = int(line.split(":", 1)[1].strip())
        elif "Core(s) per socket:" in line:
            cores_per = int(line.split(":", 1)[1].strip())
            result["cores"] = cores_per * result.get("sockets", 1)
        elif "Thread(s) per core:" in line:
            result["threads_per_core"] = int(line.split(":", 1)[1].strip())

    return result


def _count_numa_nodes() -> int:
    """Count NUMA nodes from /sys or numactl."""
    sys_path = Path("/sys/devices/system/node")
    if sys_path.exists():
        return len(list(sys_path.glob("node[0-9]*")))

    try:
        out = subprocess.run(
            ["numactl", "--hardware"], capture_output=True, text=True, timeout=5
        )
        if out.returncode == 0:
            match = re.search(r"available:\s*(\d+)", out.stdout)
            if match:
                return int(match.group(1))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return 0


def _get_memory_gb() -> float:
    """Get total memory in GB from /proc/meminfo."""
    try:
        content = Path("/proc/meminfo").read_text()
        match = re.search(r"MemTotal:\s*(\d+)\s*kB", content)
        if match:
            return round(int(match.group(1)) / 1024 / 1024, 1)
    except OSError:
        pass
    return 0.0


def _detect_gpu() -> dict[str, Any]:
    """Detect GPUs via nvidia-smi."""
    result: dict[str, Any] = {"model": "", "count": 0}

    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,count", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            lines = out.stdout.strip().splitlines()
            result["count"] = len(lines)
            if lines:
                result["model"] = lines[0].split(",")[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return result


def _get_mpi_version() -> str:
    """Detect MPI version."""
    for cmd in [["mpirun", "--version"], ["mpiexec", "--version"]]:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if out.returncode == 0 and out.stdout.strip():
                # Return first line
                return out.stdout.strip().splitlines()[0]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return ""


def _get_loaded_modules() -> list[str]:
    """Get currently loaded environment modules."""
    # LOADEDMODULES is set by the module system
    loaded = os.environ.get("LOADEDMODULES", "")
    if loaded:
        return [m for m in loaded.split(":") if m]
    return []


def _detect_interconnect() -> str:
    """Detect network interconnect type."""
    # Check for InfiniBand
    ib_path = Path("/sys/class/infiniband")
    if ib_path.exists() and list(ib_path.iterdir()):
        devices = [d.name for d in ib_path.iterdir()]
        try:
            rate_path = ib_path / devices[0] / "ports" / "1" / "rate"
            if rate_path.exists():
                rate = rate_path.read_text().strip()
                return f"InfiniBand ({rate})"
        except OSError:
            pass
        return "InfiniBand"

    # Check for OmniPath
    opa_path = Path("/sys/class/opa")
    if opa_path.exists():
        return "OmniPath"

    return "Ethernet"
