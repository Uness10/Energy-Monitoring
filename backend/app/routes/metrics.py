from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import Optional
from ..models.schemas import MetricsPayload
from ..services.clickhouse import ch_service
from ..services.heartbeat import heartbeat_tracker
from ..services.aggregation import get_aggregation_level
from ..auth.api_key import verify_api_key
from ..auth.jwt_handler import verify_token

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.post("", status_code=200)
def ingest_metrics(
    payload: MetricsPayload,
    node_id: str = Depends(verify_api_key),
):
    if payload.node_id != node_id:
        raise HTTPException(status_code=403, detail="API key does not match node_id in payload")

    ch_service.insert_metrics(
        node_id=payload.node_id,
        timestamp=payload.timestamp.replace(tzinfo=None),
        metrics=payload.metrics,
        app_metrics=[a.model_dump() for a in payload.app_metrics] if payload.app_metrics else None,
    )
    heartbeat_tracker.record(payload.node_id)

    app_count = len(payload.app_metrics) if payload.app_metrics else 0
    return {
        "status": "ok",
        "metrics_count": len(payload.metrics),
        "app_metrics_count": app_count,
    }


@router.get("")
def query_metrics(
    node_id: Optional[str] = Query(None),
    app_name: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    aggregation: Optional[str] = Query(None),
    _user: dict = Depends(verify_token),
):
    if start and end and not aggregation:
        aggregation = get_aggregation_level(start, end)

    data = ch_service.query_metrics(
        node_id=node_id,
        app_name=app_name,
        metric=metric,
        start=start,
        end=end,
        aggregation=aggregation,
    )
    return {"data": data, "count": len(data), "aggregation": aggregation}


@router.get("/aggregated")
def query_aggregated(
    node_id: Optional[str] = Query(None),
    app_name: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    aggregation: str = Query("1h"),
    _user: dict = Depends(verify_token),
):
    data = ch_service.query_metrics(
        node_id=node_id,
        app_name=app_name,
        metric=metric,
        start=start,
        end=end,
        aggregation=aggregation,
    )
    return {"data": data, "count": len(data), "aggregation": aggregation}
