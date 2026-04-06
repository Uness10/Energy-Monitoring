from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class NodeHealth:
    """AI-powered node health tracker with adaptive timeout."""
    last_seen: datetime = None
    intervals: list = field(default_factory=list)
    max_history: int = 100
    k: float = 4.0  # k-sigma multiplier (4 standard deviations = 99.99% confidence)
    min_samples: int = 5
    fallback_timeout: float = 30.0

    def record_arrival(self, now: datetime):
        """Record when a node sends metrics and update interval history."""
        if self.last_seen:
            gap = (now - self.last_seen).total_seconds()
            self.intervals.append(gap)
            # Keep only recent history to adapt to changes
            if len(self.intervals) > self.max_history:
                self.intervals.pop(0)
        self.last_seen = now

    def get_timeout(self) -> float:
        """Calculate adaptive timeout based on historical intervals."""
        if len(self.intervals) < self.min_samples:
            return self.fallback_timeout
        
        mean = sum(self.intervals) / len(self.intervals)
        var = sum((x - mean) ** 2 for x in self.intervals) / len(self.intervals)
        std = var ** 0.5
        
        # Timeout = mean + k*std (e.g., 4-sigma = 99.99% confidence)
        return mean + self.k * std

    def get_status(self) -> str:
        """
        Determine node status based on age and timeout.
        
        ONLINE:  age < timeout (expected behavior)
        STALE:   timeout <= age < 2*timeout (late but not offline)
        OFFLINE: age >= 2*timeout (definitely down)
        UNKNOWN: never seen before
        """
        if not self.last_seen:
            return "UNKNOWN"
        
        now = datetime.now(timezone.utc)
        age = (now - self.last_seen).total_seconds()
        timeout = self.get_timeout()
        
        if age < timeout:
            return "ONLINE"
        elif age < timeout * 2:
            return "STALE"
        else:
            return "OFFLINE"


class HeartbeatTracker:
    """Intelligent heartbeat tracker for energy monitoring nodes."""
    
    def __init__(self):
        self.nodes = defaultdict(NodeHealth)

    def record_arrival(self, node_id: str, timestamp: datetime = None):
        """Record metric arrival from a node."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        self.nodes[node_id].record_arrival(timestamp)

    def get_status(self, node_id: str) -> dict:
        """Get current status of a node."""
        h = self.nodes[node_id]
        return {
            "node_id": node_id,
            "status": h.get_status(),
            "last_seen": h.last_seen,
            "timeout": h.get_timeout(),
        }

    def get_all_statuses(self) -> Dict[str, dict]:
        """Get status of all tracked nodes."""
        return {nid: self.get_status(nid) for nid in self.nodes}


# Singleton instance
heartbeat_service = HeartbeatTracker()