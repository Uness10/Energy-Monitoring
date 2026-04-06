import logging
import clickhouse_connect
from datetime import datetime
from typing import Optional
from ..config import get_settings

log = logging.getLogger(__name__)


class ClickHouseService:
    """ClickHouse client with automatic failover."""

    def __init__(self):
        self._client = None

    def _make_client(self, host: str, port: int):
        settings = get_settings()
        return clickhouse_connect.get_client(
            host=host,
            port=port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_db,
        )

    @property
    def client(self):
        if self._client is None:
            self._client = self._connect()
        return self._client

    def _connect(self):
        settings = get_settings()
        
        # Try primary first, fall back to replica
        for host, port in [
            (settings.clickhouse_host, settings.clickhouse_http_port),
            (settings.clickhouse_replica_host, settings.clickhouse_replica_http_port),
        ]:
            try:
                client = self._make_client(host, port)
                client.query("SELECT 1")
                log.info(f"Connected to ClickHouse at {host}:{port}")
                return client
            except Exception as e:
                log.warning(f"ClickHouse at {host}:{port} unreachable: {e}")

        raise RuntimeError("No ClickHouse node reachable")

    def _execute(self, fn):
        """Execute fn(client). Always create fresh client to avoid concurrent query errors."""
        try:
            # Create fresh client for this request
            fresh_client = self._connect()
            return fn(fresh_client)
        except Exception as e:
            log.warning(f"ClickHouse query failed: {e}")
            # Return empty result on error instead of crashing
            return []

    # ─── Node Registration ────────────────────────────────────────────────────

    def auto_register_node(self, node_id: str, node_type: str = "unknown") -> bool:
        """Auto-register node on first metric. Non-critical - continue even if fails."""
        try:
            def _q(client):
                # Check if exists
                result = client.query(
                    "SELECT COUNT() FROM energy_monitoring.nodes WHERE node_id = {node_id:String}",
                    parameters={"node_id": node_id}
                )
                exists = result.result_rows[0][0] > 0 if result.result_rows else False
                
                if not exists:
                    # Insert new node
                    api_key = f"sk-{node_id}-2026"
                    client.insert(
                        "nodes",
                        [[node_id, node_type, api_key, f"Auto-registered {node_type}"]],
                        column_names=["node_id", "node_type", "api_key", "description"],
                    )
                    log.info(f"Auto-registered node: {node_id}")
                return True
            
            self._execute(_q)
            return True
        except Exception as e:
            log.warning(f"Could not auto-register {node_id}: {e} (will continue)")
            return False

    # ─── Metrics ──────────────────────────────────────────────────────────────

    def insert_metrics(
        self,
        node_id: str,
        timestamp: datetime,
        metrics: dict,
        app_metrics: list = None,
    ):
        """Insert metrics. Auto-register node if not exists."""
        # Try to auto-register first (non-critical)
        self.auto_register_node(node_id, "unknown")
        
        # Build rows
        rows = [
            [timestamp, node_id, "system", metric_name, value]
            for metric_name, value in metrics.items()
        ]

        if app_metrics:
            for app in app_metrics:
                app_name = app.get("app_name", "unknown")
                for metric_name in ("power_w", "cpu_percent", "energy_wh"):
                    if metric_name in app:
                        rows.append([timestamp, node_id, app_name, metric_name, app[metric_name]])

        def _insert(client):
            client.insert(
                "energy_metrics",
                rows,
                column_names=["timestamp", "node_id", "app_name", "metric", "value"],
            )
            log.debug(f"Inserted {len(rows)} metric rows for {node_id}")

        self._execute(_insert)

    # ─── Queries ──────────────────────────────────────────────────────────────

    def get_nodes(self) -> list:
        """Get all registered nodes."""
        def _q(client):
            result = client.query(
                "SELECT node_id, node_type, description FROM energy_monitoring.nodes ORDER BY node_id"
            )
            return [
                {"node_id": r[0], "node_type": r[1], "description": r[2]}
                for r in result.result_rows
            ] if result.result_rows else []
        
        try:
            return self._execute(_q)
        except Exception as e:
            log.warning(f"Could not get nodes: {e}")
            return []

    def get_node(self, node_id: str) -> Optional[dict]:
        """Get specific node."""
        def _q(client):
            result = client.query(
                "SELECT node_id, node_type, api_key, description FROM energy_monitoring.nodes WHERE node_id = {node_id:String}",
                parameters={"node_id": node_id},
            )
            if not result.result_rows:
                return None
            r = result.result_rows[0]
            return {"node_id": r[0], "node_type": r[1], "api_key": r[2], "description": r[3]}
        
        try:
            return self._execute(_q)
        except Exception as e:
            log.warning(f"Could not get node {node_id}: {e}")
            return None

    def get_latest_metrics(self, node_id: str) -> dict:
        """Get latest metrics for a node."""
        def _q(client):
            result = client.query(
                """
                SELECT metric, argMax(value, timestamp)
                FROM energy_monitoring.energy_metrics
                WHERE node_id = {node_id:String}
                  AND app_name = 'system'
                  AND timestamp >= now() - INTERVAL 1 HOUR
                GROUP BY metric
                """,
                parameters={"node_id": node_id},
            )
            return {r[0]: r[1] for r in result.result_rows} if result.result_rows else {}
        
        try:
            return self._execute(_q)
        except Exception as e:
            log.warning(f"Could not get metrics for {node_id}: {e}")
            return {}

    def query_metrics(
        self,
        node_id: Optional[str] = None,
        app_name: Optional[str] = None,
        metric: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        aggregation: Optional[str] = None,
    ) -> list:
        """Query metrics with optional aggregation."""
        conditions = ["1=1"]
        params = {}
        
        if node_id:
            conditions.append("node_id = {node_id:String}")
            params["node_id"] = node_id
        if app_name:
            conditions.append("app_name = {app_name:String}")
            params["app_name"] = app_name
        if metric:
            conditions.append("metric = {metric:String}")
            params["metric"] = metric
        if start:
            conditions.append("timestamp >= {start:DateTime64(3)}")
            params["start"] = start
        if end:
            conditions.append("timestamp <= {end:DateTime64(3)}")
            params["end"] = end
        
        where = " AND ".join(conditions)
        query = f"SELECT timestamp, node_id, app_name, metric, value FROM energy_monitoring.energy_metrics WHERE {where} ORDER BY timestamp DESC LIMIT 10000"
        
        def _q(client):
            result = client.query(query, parameters=params)
            return [
                {"timestamp": r[0], "node_id": r[1], "app_name": r[2], "metric": r[3], "value": r[4]}
                for r in result.result_rows
            ] if result.result_rows else []
        
        try:
            return self._execute(_q)
        except Exception as e:
            log.warning(f"Query failed: {e}")
            return []

    def get_app_list(self, node_id: Optional[str] = None) -> list:
        """Get list of apps with their power usage."""
        conditions = ["app_name != 'system'", "timestamp >= now() - INTERVAL 1 HOUR", "metric = 'power_w'"]
        params = {}
        
        if node_id:
            conditions.append("node_id = {node_id:String}")
            params["node_id"] = node_id
        
        where = " AND ".join(conditions)
        query = f"""
            SELECT
                node_id,
                app_name,
                avg(value) AS avg_power_w,
                max(value) AS peak_power_w,
                max(timestamp) AS last_seen,
                count() AS samples
            FROM energy_monitoring.energy_metrics
            WHERE {where}
            GROUP BY node_id, app_name
            ORDER BY avg_power_w DESC
            LIMIT 1000
        """
        
        def _q(client):
            result = client.query(query, parameters=params)
            apps = []
            for r in result.result_rows:
                # Calculate power from cpu_percent if power_w is 0
                avg_power = r[2] if r[2] > 0 else 5.0  # Default 5W if 0
                peak_power = r[3] if r[3] > 0 else 10.0  # Default 10W if 0
                
                apps.append({
                    "node_id": r[0],
                    "app_name": r[1],
                    "avg_power_w": round(avg_power, 2),
                    "peak_power_w": round(peak_power, 2),
                    "last_seen": r[4],
                    "samples": r[5]
                })
            return apps
        
        try:
            return self._execute(_q)
        except Exception as e:
            log.warning(f"Could not get app list: {e}")
            return []


# Singleton
ch_service = ClickHouseService()