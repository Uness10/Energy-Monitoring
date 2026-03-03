import os
import time

_last_energy_uj = None
_last_energy_time = None
_cumulative_energy_wh = 0.0


def _read_rapl_energy() -> float | None:
    """Read energy counter from Intel RAPL (microjoules)."""
    rapl_path = "/sys/class/powercap/intel-rapl:0/energy_uj"
    if os.path.exists(rapl_path):
        with open(rapl_path) as f:
            return int(f.read().strip())
    return None


def get_voltage() -> float:
    """
    Read system voltage. Hardware-specific.
    Returns a default 220V for workstations, or reads INA219 for RPi.
    """
    # INA219 via i2c (Raspberry Pi with power sensor)
    try:
        from ina219 import INA219
        ina = INA219(0.1)
        ina.configure()
        return ina.voltage()
    except Exception:
        pass

    # Default nominal voltage for workstations
    return 220.0


def get_power_watts() -> float:
    """Estimate current power consumption in watts."""
    global _last_energy_uj, _last_energy_time

    energy_uj = _read_rapl_energy()
    now = time.time()

    if energy_uj is not None and _last_energy_uj is not None:
        delta_uj = energy_uj - _last_energy_uj
        delta_t = now - _last_energy_time
        if delta_t > 0 and delta_uj >= 0:
            _last_energy_uj = energy_uj
            _last_energy_time = now
            return (delta_uj / 1e6) / delta_t  # watts

    if energy_uj is not None:
        _last_energy_uj = energy_uj
        _last_energy_time = now

    # Fallback: rough estimate from CPU utilization
    import psutil
    cpu = psutil.cpu_percent(interval=0)
    idle_watts = 30.0
    max_watts = 150.0
    return idle_watts + (max_watts - idle_watts) * (cpu / 100.0)


def get_energy_wh() -> float:
    """Cumulative energy consumption in Wh."""
    global _cumulative_energy_wh
    power = get_power_watts()
    # Assume this is called every ~10 seconds
    _cumulative_energy_wh += power * (10.0 / 3600.0)
    return _cumulative_energy_wh
