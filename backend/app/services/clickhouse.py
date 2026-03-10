import logging
import clickhouse_connect
from datetime import datetime
from typing import Optional
from ..config import get_settings

log = logging.getLogger(__name__)


class ClickHouseService:
    """
    ClickHouse client with automatic failover to replica node.
    Primary: clickhouse-01  →  Replica: clickhouse-02
    """

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
                log.info("Connected to ClickHouse at %s:%s", host, port)
                return client
            except Exception as e:
                log.warning("ClickHouse at %s:%s unreachable: %s", host, port, e)

        raise RuntimeError("No ClickHouse node reachable (tried primary and replica)")

    def _execute(self, fn):
        """Execute fn(client). On connection error, reset and retry once via replica."""
        try:
            return fn(self.client)
        except Exception as e:
            log.warning("ClickHouse query failed (%s), reconnecting...", e)
            self._client = None
            return fn(self.client)

    # ─── Writes ───────────────────────────────────────────────────────────────

    def insert_metrics(
        self,
        node_id: str,
        timestamp: datetime,
        metrics: dict,
        app_metrics: list[dict] | None = None,
    ):
        """
        Insert system-level KPIs (app_name='system') and optional per-app rows.
        Each metric becomes one row: (timestamp, node_id, app_name, metric, value)
        """
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

        self._execute(_insert)

    def register_node(self, node_id: str, node_type: str, api_key: str, description: str = ""):
        def _insert(client):
            client.insert(
                "nodes",
                [[node_id, node_type, api_key, description]],
                column_names=["node_id", "node_type", "api_key", "description"],
            )
        self._execute(_insert)

    # ─── Reads ────────────────────────────────────────────────────────────────

    def query_metrics(
        self,
        node_id: Optional[str] = None,
        app_name: Optional[str] = None,
        metric: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        aggregation: Optional[str] = None,
    ) -> list:
        if aggregation:
            return self._query_aggregated(node_id, app_name, metric, start, end, aggregation)
        return self._query_raw(node_id, app_name, metric, start, end)

    def _build_where(self, node_id, app_name, metric, start, end, ts_col="timestamp") -> tuple[str, dict]:
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
            conditions.append(f"{ts_col} >= {{start:DateTime64(3)}}")
            params["start"] = start
        if end:
            conditions.append(f"{ts_col} <= {{end:DateTime64(3)}}")
            params["end"] = end
        return " AND ".join(conditions), params

    def _query_raw(self, node_id, app_name, metric, start, end) -> list:
        where, params = self._build_where(node_id, app_name, metric, start, end)
        query = f"""
            SELECT timestamp, node_id, app_name, metric, value
            FROM energy_metrics
            WHERE {where}
            ORDER BY timestamp DESC
            LIMIT 10000
        """
        def _q(client):
            result = client.query(query, parameters=params)
            return [
                {"timestamp": r[0], "node_id": r[1], "app_name": r[2],
                 "metric": r[3], "value": r[4]}
                for r in result.result_rows
            ]
        return self._execute(_q)

    def _query_aggregated(self, node_id, app_name, metric, start, end, aggregation) -> list:
        agg_funcs = {
            "1min":  "toStartOfMinute(timestamp)",
            "5min":  "toStartOfFiveMinutes(timestamp)",
            "1h":    "toStartOfHour(timestamp)",
            "1d":    "toStartOfDay(timestamp)",
        }
        if aggregation not in agg_funcs:
            return self._query_raw(node_id, app_name, metric, start, end)

        time_expr = agg_funcs[aggregation]
        where, params = self._build_where(node_id, app_name, metric, start, end)
        query = f"""
            SELECT
                {time_expr}        AS bucket,
                node_id,
                app_name,
                metric,
                avg(value)         AS avg_value,
                min(value)         AS min_value,
                max(value)         AS max_value,
                count()            AS sample_count
            FROM energy_metrics
            WHERE {where}
            GROUP BY bucket, node_id, app_name, metric
            ORDER BY bucket DESC
            LIMIT 10000
        """
        def _q(client):
            result = client.query(query, parameters=params)
            return [
                {"timestamp": r[0], "node_id": r[1], "app_name": r[2],
                 "metric": r[3], "avg_value": r[4], "min_value": r[5],
                 "max_value": r[6], "sample_count": r[7]}
                for r in result.result_rows
            ]
        return self._execute(_q)

    def get_nodes(self) -> list:
        def _q(client):
            result = client.query(
                "SELECT node_id, node_type, description, registered FROM nodes ORDER BY node_id"
            )
            return [
                {"node_id": r[0], "node_type": r[1], "description": r[2], "registered": r[3]}
                for r in result.result_rows
            ]
        return self._execute(_q)

    def get_node(self, node_id: str) -> Optional[dict]:
        def _q(client):
            result = client.query(
                "SELECT node_id, node_type, api_key, description, registered "
                "FROM nodes WHERE node_id = {node_id:String}",
                parameters={"node_id": node_id},
            )
            if not result.result_rows:
                return None
            r = result.result_rows[0]
            return {"node_id": r[0], "node_type": r[1], "api_key": r[2],
                    "description": r[3], "registered": r[4]}
        return self._execute(_q)

    def get_latest_metrics(self, node_id: str) -> dict:
        """Returns the most recent value for each system-level KPI."""
        def _q(client):
            result = client.query(
                """
                SELECT metric, argMax(value, timestamp)
                FROM energy_metrics
                WHERE node_id = {node_id:String}
                  AND app_name = 'system'
                  AND timestamp >= now() - INTERVAL 5 MINUTE
                GROUP BY metric
                """,
                parameters={"node_id": node_id},
            )
            return {r[0]: r[1] for r in result.result_rows}
        return self._execute(_q)

    # ─── Per-App Queries ──────────────────────────────────────────────────────

    def get_app_list(self, node_id: Optional[str] = None) -> list:
        """List all tracked applications with their latest power readings."""
        conditions = ["app_name != 'system'",
                      "timestamp >= now() - INTERVAL 1 HOUR"]
        params = {}
        if node_id:
            conditions.append("node_id = {node_id:String}")
            params["node_id"] = node_id
        where = " AND ".join(conditions)
        query = f"""
            SELECT
                node_id,
                app_name,
                avg(if(metric='power_w', value, 0))  AS avg_power_w,
                max(if(metric='power_w', value, 0))  AS peak_power_w,
                max(timestamp)                        AS last_seen,
                count()                               AS samples
            FROM energy_metrics
            WHERE {where}
            GROUP BY node_id, app_name
            ORDER BY avg_power_w DESC
        """
        def _q(client):
            result = client.query(query, parameters=params)
            return [
                {"node_id": r[0], "app_name": r[1], "avg_power_w": r[2],
                 "peak_power_w": r[3], "last_seen": r[4], "samples": r[5]}
                for r in result.result_rows
            ]
        return self._execute(_q)

    def get_app_energy_history(
        self,
        app_name: str,
        node_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        aggregation: str = "1h",
    ) -> list:
        """Per-app energy over time from the ranking materialized view."""
        conditions = ["app_name = {app_name:String}"]
        params = {"app_name": app_name}
        if node_id:
            conditions.append("node_id = {node_id:String}")
            params["node_id"] = node_id
        if start:
            conditions.append("hour >= {start:DateTime64(3)}")
            params["start"] = start
        if end:
            conditions.append("hour <= {end:DateTime64(3)}")
            params["end"] = end
        where = " AND ".join(conditions)
        query = f"""
            SELECT hour, node_id, app_name, avg_power_w, total_power_w,
                   avg_cpu_util, sample_count
            FROM energy_app_ranking_mv
            WHERE {where}
            ORDER BY hour DESC
            LIMIT 5000
        """
        def _q(client):
            result = client.query(query, parameters=params)
            return [
                {"timestamp": r[0], "node_id": r[1], "app_name": r[2],
                 "avg_power_w": r[3], "total_power_w": r[4],
                 "avg_cpu_util": r[5], "sample_count": r[6]}
                for r in result.result_rows
            ]
        return self._execute(_q)

    def verify_api_key(self, api_key: str) -> Optional[str]:
        """Returns node_id if api_key is valid, else None."""
        def _q(client):
            result = client.query(
                "SELECT node_id FROM nodes WHERE api_key = {key:String}",
                parameters={"key": api_key},
            )
            return result.result_rows[0][0] if result.result_rows else None
        return self._execute(_q)


# Singleton
ch_service = ClickHouseService()
