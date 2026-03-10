from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NodeHealth:
    last_seen: datetime = None
    intervals: list = field(default_factory=list)
    max_history: int = 100
    k: float = 4.0
    min_samples: int = 5
    fallback_timeout: float = 30.0

    def record_arrival(self, now: datetime):
        if self.last_seen:
            gap = (now - self.last_seen).total_seconds()
            self.intervals.append(gap)
            if len(self.intervals) > self.max_history:
                self.intervals.pop(0)
        self.last_seen = now

    def get_timeout(self) -> float:
        if len(self.intervals) < self.min_samples:
            return self.fallback_timeout
        mean = sum(self.intervals) / len(self.intervals)
        var = sum((x - mean) ** 2 for x in self.intervals) / len(self.intervals)
        std = var ** 0.5
        return mean + self.k * std

    def get_status(self) -> str:
        if not self.last_seen:
            return "UNKNOWN"
        age = (datetime.utcnow() - self.last_seen).total_seconds()
        timeout = self.get_timeout()
        if age < timeout:
            return "ONLINE"
        elif age < timeout * 2:
            return "STALE"
        return "OFFLINE"


class HeartbeatTracker:
    def __init__(self):
        self.nodes = defaultdict(NodeHealth)

    def record(self, node_id: str):
        self.nodes[node_id].record_arrival(datetime.utcnow())

    def get_status(self, node_id: str) -> dict:
        h = self.nodes[node_id]
        return {
            "status": h.get_status(),
            "last_seen": h.last_seen,
            "timeout": h.get_timeout(),
        }

    def get_all_statuses(self) -> dict:
        return {nid: self.get_status(nid) for nid in self.nodes}


# Singleton
heartbeat_tracker = HeartbeatTracker()
