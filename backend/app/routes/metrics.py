from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional

from ..models.schemas import MetricsPayload
from ..services.clickhouse import ch_service
from ..services.heartbeat import heartbeat_service
from ..auth.api_key import verify_api_key
from ..auth.jwt_handler import verify_token

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.post("", status_code=200)
def ingest_metrics(
    payload: MetricsPayload,
    node_id: str = Depends(verify_api_key),
):
    """
    Ingest metrics from a daemon.
    Auto-registers the node if it doesn't exist.
    Records heartbeat to mark node as ONLINE.
    Calculates app power from CPU percent.
    """
    # Auto-register node (non-critical, continues even if fails)
    ch_service.auto_register_node(node_id, node_type="unknown")

    # Fix app metrics: calculate power_w from cpu_percent if not provided
    fixed_app_metrics = []
    if payload.app_metrics:
        for app in payload.app_metrics:
            app_dict = app.model_dump()
            cpu_pct = app_dict.get("cpu_percent", 0)
            power_w = app_dict.get("power_w", 0)
            
            # If power_w is 0 or not provided but cpu_percent exists, estimate power
            # Model: baseline 10W + up to 50W based on CPU usage (so 100% CPU = 60W per app)
            if power_w == 0 and cpu_pct > 0:
                app_dict["power_w"] = round(10.0 + (cpu_pct / 100.0) * 50.0, 2)
            elif power_w == 0 and cpu_pct == 0:
                # Idle app consumes nominal power
                app_dict["power_w"] = round(2.0, 2)
            
            fixed_app_metrics.append(app_dict)

    # Insert metrics
    ch_service.insert_metrics(
        node_id=node_id,
        timestamp=payload.timestamp.replace(tzinfo=None),
        metrics=payload.metrics,
        app_metrics=fixed_app_metrics if fixed_app_metrics else None,
    )
    
    # Record heartbeat (marks node as ONLINE in dashboard)
    try:
        heartbeat_service.record_arrival(node_id, payload.timestamp)
    except Exception as e:
        # Non-critical - continue even if heartbeat fails
        pass

    app_count = len(fixed_app_metrics) if fixed_app_metrics else 0
    return {
        "status": "ok",
        "node_id": node_id,
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
    _user: dict = Depends(verify_token),
):
    """Query metrics."""
    data = ch_service.query_metrics(
        node_id=node_id,
        app_name=app_name,
        metric=metric,
        start=start,
        end=end,
    )
    return {"data": data, "count": len(data)}


@router.get("/aggregated")
def query_aggregated(
    node_id: Optional[str] = Query(None),
    app_name: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    _user: dict = Depends(verify_token),
):
    """Query aggregated metrics."""
    data = ch_service.query_metrics(
        node_id=node_id,
        app_name=app_name,
        metric=metric,
        start=start,
        end=end,
    )
    return {"data": data, "count": len(data)}


@router.get("/nodes")
def get_all_nodes(_user: dict = Depends(verify_token)):
    """Get all nodes."""
    nodes = ch_service.get_nodes()
    return {
        "nodes": nodes,
        "total_nodes": len(nodes),
    }


@router.get("/nodes/{node_id}")
def get_node_metrics(node_id: str, _user: dict = Depends(verify_token)):
    """Get metrics for specific node."""
    node = ch_service.get_node(node_id)
    latest = ch_service.get_latest_metrics(node_id)
    return {
        "node_id": node_id,
        "node": node,
        "latest_metrics": latest,
    }


@router.get("/apps")
def get_apps(node_id: Optional[str] = Query(None), _user: dict = Depends(verify_token)):
    """Get app usage across all nodes."""
    apps = ch_service.get_app_list(node_id)
    return {
        "apps": apps,
        "total_apps": len(apps),
    }