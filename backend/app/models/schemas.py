from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

ALLOWED_METRICS = {
    "voltage", "cpu_freq", "cpu_util", "ram_util",
    "temperature", "power_w", "energy_wh", "uptime_s",
}


class AppMetrics(BaseModel):
    """Per-application energy metrics collected by the daemon."""
    app_name: str
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    power_w: float = 0.0
    energy_wh: float = 0.0


class MetricsPayload(BaseModel):
    node_id: str
    timestamp: datetime
    metrics: Dict[str, float]
    app_metrics: Optional[List[AppMetrics]] = None

    @validator("timestamp")
    def not_future(cls, v):
        if v.replace(tzinfo=None) > datetime.utcnow():
            raise ValueError("Timestamp cannot be in the future")
        return v

    @validator("metrics")
    def valid_metrics(cls, v):
        for key in v:
            if key not in ALLOWED_METRICS:
                raise ValueError(f"Unknown metric: {key}")
        if "cpu_util" in v and not (0 <= v["cpu_util"] <= 100):
            raise ValueError("cpu_util must be 0–100")
        if "ram_util" in v and not (0 <= v["ram_util"] <= 100):
            raise ValueError("ram_util must be 0–100")
        return v


class MetricsQuery(BaseModel):
    node_id: Optional[str] = None
    app_name: Optional[str] = None
    metric: Optional[str] = None
    start: datetime
    end: datetime
    aggregation: Optional[str] = None  # '1min', '5min', '1h', '1d'


class NodeStatus(BaseModel):
    node_id: str
    node_type: str
    status: str  # ONLINE, STALE, OFFLINE, UNKNOWN
    last_seen: Optional[datetime] = None
    adaptive_timeout: float
    latest_metrics: Optional[Dict[str, float]] = None


class NodeRegister(BaseModel):
    node_id: str
    node_type: str = Field(..., pattern="^(workstation|rpi|mobile)$")
    description: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "viewer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AppSummary(BaseModel):
    node_id: str
    app_name: str
    avg_power_w: float
    peak_power_w: float
    last_seen: Optional[datetime] = None
    samples: int
