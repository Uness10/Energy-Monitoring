import psutil
import os


def get_temperature() -> float:
    # Try psutil first (works on most Linux systems)
    temps = psutil.sensors_temperatures()
    if temps:
        for name, entries in temps.items():
            if entries:
                return entries[0].current

    # Raspberry Pi fallback: read from thermal zone
    thermal_path = "/sys/class/thermal/thermal_zone0/temp"
    if os.path.exists(thermal_path):
        with open(thermal_path) as f:
            return int(f.read().strip()) / 1000.0

    return 0.0
