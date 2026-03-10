from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routes import metrics, nodes, auth, apps
from .auth.jwt_handler import verify_token
from .services.clickhouse import ch_service
from .services.heartbeat import heartbeat_tracker

app = FastAPI(
    title="Energy Monitoring System",
    description="Backend API for the MLab distributed energy monitoring framework.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router)
app.include_router(nodes.router)
app.include_router(apps.router)
app.include_router(auth.router)


@app.get("/api/v1/summary", tags=["summary"])
def system_summary(_user: dict = Depends(verify_token)):
    """
    System-wide summary: node counts by status, total power draw.
    """
    nodes_list = ch_service.get_nodes()
    all_statuses = heartbeat_tracker.get_all_statuses()

    summary_rows = []
    total_power = 0.0

    for node in nodes_list:
        nid = node["node_id"]
        hb = all_statuses.get(nid, {"status": "UNKNOWN", "last_seen": None, "timeout": 30.0})
        latest = ch_service.get_latest_metrics(nid)
        power = latest.get("power_w", 0.0)
        total_power += power
        summary_rows.append({
            "node_id": nid,
            "node_type": node["node_type"],
            "status": hb["status"],
            "last_seen": hb["last_seen"],
            "power_w": power,
        })

    status_counts = {"ONLINE": 0, "STALE": 0, "OFFLINE": 0, "UNKNOWN": 0}
    for row in summary_rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    return {
        "total_nodes": len(nodes_list),
        **status_counts,
        "total_power_w": round(total_power, 2),
        "nodes": summary_rows,
    }


@app.get("/health", tags=["health"])
def health_check():
    try:
        ch_service.client.query("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "healthy", "database": db_status}
