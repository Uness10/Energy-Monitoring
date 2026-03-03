import psutil


def get_ram_utilization() -> float:
    return psutil.virtual_memory().percent
