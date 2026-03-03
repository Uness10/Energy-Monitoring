from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from ..models.schemas import MetricsPayload, MetricsQuery
from ..services.clickhouse import ch_service
from ..services.heartbeat import heartbeat_tracker
from ..services.aggregation import get_aggregation_level
from ..auth.api_key import verify_api_key
from ..auth.jwt_handler import verify_token

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.post("")
def ingest_metrics(payload: MetricsPayload, node_id: str = Depends(verify_api_key)):
    if payload.node_id != node_id:
        raise HTTPException(status_code=403, detail="API key does not match node_id")

    ch_service.insert_metrics(payload.node_id, payload.timestamp, payload.metrics)
    heartbeat_tracker.record(payload.node_id)

    return {"status": "ok", "metrics_count": len(payload.metrics)}


@router.get("")
def query_metrics(
    node_id: str = None,
    metric: str = None,
    start: datetime = None,
    end: datetime = None,
    aggregation: str = None,
    _user: dict = Depends(verify_token),
):
    if start and end and not aggregation:
        aggregation = get_aggregation_level(start, end)

    data = ch_service.query_metrics(
        node_id=node_id, metric=metric, start=start, end=end, aggregation=aggregation
    )
    return {"data": data, "count": len(data), "aggregation": aggregation}


@router.get("/aggregated")
def query_aggregated(
    node_id: str = None,
    metric: str = None,
    start: datetime = None,
    end: datetime = None,
    aggregation: str = "1h",
    _user: dict = Depends(verify_token),
):
    data = ch_service.query_metrics(
        node_id=node_id, metric=metric, start=start, end=end, aggregation=aggregation
    )
    return {"data": data, "count": len(data), "aggregation": aggregation}
