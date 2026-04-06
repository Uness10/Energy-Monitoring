from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .routes import metrics, nodes, auth, apps
from .auth.jwt_handler import verify_token
from .services.clickhouse import ch_service

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


@app.on_event("startup")
def startup_event():
    """Test ClickHouse connection on startup."""
    try:
        ch_service.client.query("SELECT 1")
        print("✅ ClickHouse connected successfully")
    except Exception as e:
        print(f"⚠️  ClickHouse connection failed: {e}")
        print("  Metrics will not be stored, but API will still work")


@app.get("/api/v1/summary", tags=["summary"])
def system_summary(_user: dict = Depends(verify_token)):
    """
    System-wide summary: node counts, total power draw.
    """
    nodes = ch_service.get_nodes()
    apps = ch_service.get_app_list()
    
    # Calculate total power
    total_power = 0.0
    for node in nodes:
        latest = ch_service.get_latest_metrics(node["node_id"])
        total_power += latest.get("power_w", 0.0)
    
    return {
        "total_nodes": len(nodes),
        "total_apps": len(set(a["app_name"] for a in apps)) if apps else 0,
        "total_power_w": round(total_power, 2),
        "nodes": nodes,
        "top_apps": sorted(apps, key=lambda x: x["avg_power_w"], reverse=True)[:10] if apps else [],
    }


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for monitoring systems."""
    try:
        ch_service.client.query("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    return {"status": "healthy", "database": db_status}