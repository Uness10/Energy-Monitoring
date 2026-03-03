import time
import psutil


def get_uptime_seconds() -> float:
    return time.time() - psutil.boot_time()
