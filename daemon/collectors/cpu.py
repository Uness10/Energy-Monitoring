import psutil


def get_cpu_utilization() -> float:
    return psutil.cpu_percent(interval=1)


def get_cpu_frequency() -> float:
    freq = psutil.cpu_freq()
    if freq:
        return freq.current
    return 0.0
