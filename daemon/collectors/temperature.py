import psutil
import os
import platform


def get_temperature() -> float:
    """
    Get system temperature in Celsius.
    Works on Linux and Raspberry Pi.
    Returns 0.0 on Windows or if temperature cannot be read.
    """
    
    # Try psutil first (Linux only)
    try:
        if hasattr(psutil, 'sensors_temperatures'):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
    except (AttributeError, OSError):
        pass

    # Raspberry Pi / Linux fallback: read from thermal zone
    thermal_path = "/sys/class/thermal/thermal_zone0/temp"
    if os.path.exists(thermal_path):
        try:
            with open(thermal_path) as f:
                return int(f.read().strip()) / 1000.0
        except (IOError, ValueError):
            pass

    # Windows or unsupported system - return 0
    return 0.0
