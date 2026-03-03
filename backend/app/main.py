from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import metrics, nodes, auth

app = FastAPI(
    title="Energy Monitoring System",
    description="Backend API for the MLab Energy Monitoring Framework",
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
app.include_router(auth.router)


@app.get("/api/v1/summary")
def system_summary():
    from .services.clickhouse import ch_service
    from .services.heartbeat import heartbeat_tracker

    nodes_list = ch_service.get_nodes()
    statuses = heartbeat_tracker.get_all_statuses()

    online = sum(1 for s in statuses.values() if s["status"] == "ONLINE")
    stale = sum(1 for s in statuses.values() if s["status"] == "STALE")
    offline = sum(1 for s in statuses.values() if s["status"] == "OFFLINE")

    return {
        "total_nodes": len(nodes_list),
        "online": online,
        "stale": stale,
        "offline": offline,
        "nodes": statuses,
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
