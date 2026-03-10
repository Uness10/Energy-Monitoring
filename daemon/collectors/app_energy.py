"""
Per-application energy attribution via Intel RAPL + /proc/<pid>/stat.

Algorithm:
  1. Read total package energy delta from RAPL (microjoules)
  2. Read CPU time for each tracked process from /proc/<pid>/stat
  3. Compute each app's share:
       app_energy = (app_cpu_time / total_cpu_time) × total_rapl_energy
  4. Return list of {app_name, pid, cpu_percent, power_w, energy_wh}
"""

import os
import time
import logging
import psutil

log = logging.getLogger(__name__)

RAPL_PATH = "/sys/class/powercap/intel-rapl:0/energy_uj"
RAPL_MAX_PATH = "/sys/class/powercap/intel-rapl:0/max_energy_range_uj"

_prev_rapl_uj: float | None = None
_prev_rapl_time: float | None = None
_prev_proc_times: dict[int, float] = {}          # pid → cpu_time_seconds
_cumulative_energy: dict[str, float] = {}         # app_name → wh


def _read_rapl() -> float | None:
    if not os.path.exists(RAPL_PATH):
        return None
    with open(RAPL_PATH) as f:
        return float(f.read().strip())


def _read_rapl_max() -> float:
    if not os.path.exists(RAPL_MAX_PATH):
        return 2.0e14  # common default ~55 Wh
    with open(RAPL_MAX_PATH) as f:
        return float(f.read().strip())


def _get_proc_cpu_time(pid: int) -> float | None:
    """Return total CPU time (user + system) in seconds for a PID."""
    try:
        stat_path = f"/proc/{pid}/stat"
        with open(stat_path) as f:
            fields = f.read().split()
        # fields[13] = utime, fields[14] = stime (in clock ticks)
        ticks = int(fields[13]) + int(fields[14])
        return ticks / os.sysconf("SC_CLK_TCK")
    except (FileNotFoundError, IndexError, ValueError):
        return None


def _normalize_app_name(proc: psutil.Process) -> str:
    """Return a clean application name from a process."""
    try:
        name = proc.name()
        # Strip common suffixes and paths
        name = os.path.basename(name)
        for suffix in (".exe", ".sh", ":Z", "(deleted)"):
            name = name.replace(suffix, "")
        return name.strip() or "unknown"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "unknown"


def collect_app_energy(config: dict) -> list[dict]:
    """
    Collect per-application energy metrics.

    Returns a list of dicts:
    [
      {"app_name": "firefox", "pid": 1234, "cpu_percent": 12.1,
       "power_w": 10.5, "energy_wh": 0.03},
      ...
    ]
    """
    global _prev_rapl_uj, _prev_rapl_time, _prev_proc_times, _cumulative_energy

    app_cfg = config.get("app_tracking", {})
    if not app_cfg.get("enabled", False):
        return []

    mode = app_cfg.get("mode", "top_n")
    top_n = app_cfg.get("top_n", 10)
    whitelist = set(app_cfg.get("whitelist", []))
    min_cpu = app_cfg.get("min_cpu_percent", 1.0)

    now = time.time()

    # ── Step 1: RAPL delta ───────────────────────────────────────────────────
    rapl_uj = _read_rapl()
    rapl_delta_w = 0.0

    if rapl_uj is not None and _prev_rapl_uj is not None:
        delta_uj = rapl_uj - _prev_rapl_uj
        # Handle RAPL counter wrap
        if delta_uj < 0:
            delta_uj += _read_rapl_max()
        delta_t = now - _prev_rapl_time
        if delta_t > 0:
            rapl_delta_w = (delta_uj / 1e6) / delta_t  # watts

    if rapl_uj is not None:
        _prev_rapl_uj = rapl_uj
        _prev_rapl_time = now

    # ── Step 2: Enumerate processes ──────────────────────────────────────────
    try:
        all_procs = list(psutil.process_iter(["pid", "name", "cpu_percent", "status"]))
    except Exception as e:
        log.warning("psutil process_iter failed: %s", e)
        return []

    # Filter to candidates
    candidates = []
    for proc in all_procs:
        try:
            if proc.info["status"] in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
                continue
            cpu = proc.info["cpu_percent"] or 0.0
            app_name = _normalize_app_name(proc)

            if mode == "whitelist" and app_name not in whitelist:
                continue
            if cpu < min_cpu and mode == "top_n":
                continue

            candidates.append((proc, app_name, cpu))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # For top_n: sort by CPU and take top N
    if mode == "top_n":
        candidates.sort(key=lambda x: x[2], reverse=True)
        candidates = candidates[:top_n]

    if not candidates:
        return []

    # ── Step 3: CPU time per process ─────────────────────────────────────────
    proc_cpu_times: dict[int, float] = {}
    for proc, _, _ in candidates:
        t = _get_proc_cpu_time(proc.pid)
        if t is not None:
            proc_cpu_times[proc.pid] = t

    # Delta CPU time per process since last call
    delta_times: dict[int, float] = {}
    total_delta = 0.0
    for pid, curr_time in proc_cpu_times.items():
        prev_time = _prev_proc_times.get(pid, curr_time)
        delta = max(curr_time - prev_time, 0.0)
        delta_times[pid] = delta
        total_delta += delta

    _prev_proc_times = proc_cpu_times

    # ── Step 4: Attribute energy proportionally ───────────────────────────────
    results = []
    for proc, app_name, cpu_pct in candidates:
        pid = proc.pid
        delta_t = delta_times.get(pid, 0.0)
        share = (delta_t / total_delta) if total_delta > 0 else 0.0
        power_w = share * rapl_delta_w

        # Cumulative energy in Wh
        interval = config.get("collection_interval_seconds", 10)
        _cumulative_energy[app_name] = _cumulative_energy.get(app_name, 0.0)
        _cumulative_energy[app_name] += power_w * (interval / 3600.0)

        results.append({
            "app_name": app_name,
            "pid": pid,
            "cpu_percent": round(cpu_pct, 2),
            "power_w": round(power_w, 3),
            "energy_wh": round(_cumulative_energy[app_name], 4),
        })

    # Sort by power descending
    results.sort(key=lambda x: x["power_w"], reverse=True)
    return results
