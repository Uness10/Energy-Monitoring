import secrets
from fastapi import APIRouter, Depends, HTTPException
from ..models.schemas import NodeStatus, NodeRegister
from ..services.clickhouse import ch_service
from ..services.heartbeat import heartbeat_tracker
from ..auth.jwt_handler import verify_token

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


@router.get("")
def list_nodes(_user: dict = Depends(verify_token)):
    nodes = ch_service.get_nodes()
    result = []
    for node in nodes:
        hb = heartbeat_tracker.get_status(node["node_id"])
        latest = ch_service.get_latest_metrics(node["node_id"])
        result.append(
            NodeStatus(
                node_id=node["node_id"],
                node_type=node["node_type"],
                status=hb["status"],
                last_seen=hb["last_seen"],
                adaptive_timeout=hb["timeout"],
                latest_metrics=latest or None,
            )
        )
    return result


@router.get("/{node_id}/status")
def node_status(node_id: str, _user: dict = Depends(verify_token)):
    node = ch_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    hb = heartbeat_tracker.get_status(node_id)
    latest = ch_service.get_latest_metrics(node_id)
    return NodeStatus(
        node_id=node["node_id"],
        node_type=node["node_type"],
        status=hb["status"],
        last_seen=hb["last_seen"],
        adaptive_timeout=hb["timeout"],
        latest_metrics=latest or None,
    )


@router.post("/register")
def register_node(body: NodeRegister, _user: dict = Depends(verify_token)):
    existing = ch_service.get_node(body.node_id)
    if existing:
        raise HTTPException(status_code=409, detail="Node already registered")

    api_key = f"sk-{secrets.token_hex(20)}"
    ch_service.register_node(body.node_id, body.node_type, api_key, body.description)
    return {"node_id": body.node_id, "api_key": api_key}
