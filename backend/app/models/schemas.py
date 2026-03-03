from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Dict, Optional, List

ALLOWED_METRICS = {
    "voltage", "cpu_freq", "cpu_util", "ram_util",
    "temperature", "power_w", "energy_wh", "uptime_s",
}


class MetricsPayload(BaseModel):
    node_id: str
    timestamp: datetime
    metrics: Dict[str, float]

    @validator("timestamp")
    def not_future(cls, v):
        if v > datetime.utcnow():
            raise ValueError("Timestamp cannot be in the future")
        return v

    @validator("metrics")
    def valid_metrics(cls, v):
        for key in v:
            if key not in ALLOWED_METRICS:
                raise ValueError(f"Unknown metric: {key}")
        return v


class MetricsQuery(BaseModel):
    node_id: Optional[str] = None
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
