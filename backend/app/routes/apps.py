from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional
from ..services.clickhouse import ch_service
from ..auth.jwt_handler import verify_token

router = APIRouter(prefix="/api/v1/apps", tags=["apps"])


@router.get("")
def list_apps(
    node_id: Optional[str] = Query(None, description="Filter by node"),
    _user: dict = Depends(verify_token),
):
    """
    List all tracked applications with their average and peak power draw.
    Sorted by average power descending (highest consumers first).
    """
    apps = ch_service.get_app_list(node_id=node_id)
    return {"apps": apps, "count": len(apps)}


@router.get("/{app_name}/energy")
def app_energy_history(
    app_name: str,
    node_id: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    aggregation: str = Query("1h"),
    _user: dict = Depends(verify_token),
):
    """
    Energy consumption history for a specific application over time.
    Uses the pre-aggregated energy_app_ranking_mv materialized view.
    """
    data = ch_service.get_app_energy_history(
        app_name=app_name,
        node_id=node_id,
        start=start,
        end=end,
        aggregation=aggregation,
    )
    return {"app_name": app_name, "data": data, "count": len(data)}
