import secrets
from fastapi import APIRouter, Depends, HTTPException

from ..models.schemas import NodeStatus, NodeRegister
from ..services.clickhouse import ch_service
from ..auth.jwt_handler import verify_token

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


@router.get("")
def list_nodes(_user: dict = Depends(verify_token)):
    """List all nodes and their status"""
    nodes = ch_service.get_nodes()
    result = []
    
    for node in nodes:
        # Get latest metrics
        latest = ch_service.get_latest_metrics(node["node_id"])
        
        result.append({
            "node_id": node["node_id"],
            "node_type": node.get("node_type", "unknown"),
            "description": node.get("description", ""),
            "status": "ONLINE" if latest else "UNKNOWN",
            "latest_metrics": latest or {},
        })
    
    return result


@router.get("/{node_id}/status")
def node_status(node_id: str, _user: dict = Depends(verify_token)):
    """Get specific node status"""
    node = ch_service.get_node(node_id)
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    latest = ch_service.get_latest_metrics(node_id)
    
    return {
        "node_id": node["node_id"],
        "node_type": node.get("node_type", "unknown"),
        "status": "ONLINE" if latest else "UNKNOWN",
        "latest_metrics": latest or {},
    }


@router.post("/register")
def register_node(body: NodeRegister, _user: dict = Depends(verify_token)):
    """Register new node (requires auth)"""
    existing = ch_service.get_node(body.node_id)
    if existing:
        raise HTTPException(status_code=409, detail="Node already registered")

    api_key = f"sk-{secrets.token_hex(20)}"
    ch_service.register_node(body.node_id, body.node_type, api_key, body.description)
    return {"node_id": body.node_id, "api_key": api_key}


@router.post("/auto-register")
def auto_register_node(body: NodeRegister):
    """
    Auto-registration endpoint for daemons (no auth required).
    Called by daemon on startup to self-register if not already registered.
    """
    existing = ch_service.get_node(body.node_id)
    if existing:
        # Already registered, return existing API key
        return {"node_id": existing["node_id"], "api_key": existing["api_key"]}

    # New node, generate API key and register
    api_key = f"sk-{body.node_id}-2026"
    ch_service.auto_register_node(body.node_id, body.node_type)
    return {"node_id": body.node_id, "api_key": api_key}