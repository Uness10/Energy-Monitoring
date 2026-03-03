import clickhouse_connect
from datetime import datetime
from typing import Optional
from ..config import get_settings


class ClickHouseService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            settings = get_settings()
            self._client = clickhouse_connect.get_client(
                host=settings.clickhouse_host,
                port=settings.clickhouse_http_port,
                username=settings.clickhouse_user,
                password=settings.clickhouse_password,
                database=settings.clickhouse_db,
            )
        return self._client

    def insert_metrics(self, node_id: str, timestamp: datetime, metrics: dict):
        rows = [
            [timestamp, node_id, metric_name, value]
            for metric_name, value in metrics.items()
        ]
        self.client.insert(
            "energy_metrics",
            rows,
            column_names=["timestamp", "node_id", "metric", "value"],
        )

    def query_metrics(
        self,
        node_id: Optional[str] = None,
        metric: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        aggregation: Optional[str] = None,
    ) -> list:
        if aggregation:
            return self._query_aggregated(node_id, metric, start, end, aggregation)
        return self._query_raw(node_id, metric, start, end)

    def _query_raw(self, node_id, metric, start, end) -> list:
        conditions = ["1=1"]
        params = {}
        if node_id:
            conditions.append("node_id = {node_id:String}")
            params["node_id"] = node_id
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
        query = f"""
            SELECT timestamp, node_id, metric, value
            FROM energy_metrics
            WHERE {where}
            ORDER BY timestamp DESC
            LIMIT 10000
        """
        result = self.client.query(query, parameters=params)
        return [
            {"timestamp": row[0], "node_id": row[1], "metric": row[2], "value": row[3]}
            for row in result.result_rows
        ]

    def _query_aggregated(self, node_id, metric, start, end, aggregation) -> list:
        agg_map = {
            "1min": ("toStartOfMinute", "energy_metrics"),
            "5min": ("toStartOfFiveMinutes", "energy_metrics"),
            "1h": ("hour", "energy_hourly_mv"),
            "1d": ("day", "energy_daily_mv"),
        }
        if aggregation not in agg_map:
            return self._query_raw(node_id, metric, start, end)

        if aggregation in ("1h",):
            return self._query_hourly_mv(node_id, metric, start, end)

        time_func, table = agg_map[aggregation]
        conditions = ["1=1"]
        params = {}
        if node_id:
            conditions.append("node_id = {node_id:String}")
            params["node_id"] = node_id
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
        query = f"""
            SELECT {time_func}(timestamp) AS bucket, node_id, metric,
                   avg(value) AS avg_value, min(value) AS min_value,
                   max(value) AS max_value, count() AS sample_count
            FROM energy_metrics
            WHERE {where}
            GROUP BY bucket, node_id, metric
            ORDER BY bucket DESC
            LIMIT 10000
        """
        result = self.client.query(query, parameters=params)
        return [
            {
                "timestamp": row[0], "node_id": row[1], "metric": row[2],
                "avg_value": row[3], "min_value": row[4],
                "max_value": row[5], "sample_count": row[6],
            }
            for row in result.result_rows
        ]

    def _query_hourly_mv(self, node_id, metric, start, end) -> list:
        conditions = ["1=1"]
        params = {}
        if node_id:
            conditions.append("node_id = {node_id:String}")
            params["node_id"] = node_id
        if metric:
            conditions.append("metric = {metric:String}")
            params["metric"] = metric
        if start:
            conditions.append("hour >= {start:DateTime}")
            params["start"] = start
        if end:
            conditions.append("hour <= {end:DateTime}")
            params["end"] = end

        where = " AND ".join(conditions)
        query = f"""
            SELECT hour, node_id, metric, avg_value, min_value, max_value, sample_count
            FROM energy_hourly_mv
            WHERE {where}
            ORDER BY hour DESC
            LIMIT 10000
        """
        result = self.client.query(query, parameters=params)
        return [
            {
                "timestamp": row[0], "node_id": row[1], "metric": row[2],
                "avg_value": row[3], "min_value": row[4],
                "max_value": row[5], "sample_count": row[6],
            }
            for row in result.result_rows
        ]

    def get_nodes(self) -> list:
        result = self.client.query(
            "SELECT node_id, node_type, description, registered FROM nodes ORDER BY node_id"
        )
        return [
            {"node_id": r[0], "node_type": r[1], "description": r[2], "registered": r[3]}
            for r in result.result_rows
        ]

    def get_node(self, node_id: str) -> Optional[dict]:
        result = self.client.query(
            "SELECT node_id, node_type, api_key, description, registered FROM nodes WHERE node_id = {node_id:String}",
            parameters={"node_id": node_id},
        )
        if not result.result_rows:
            return None
        r = result.result_rows[0]
        return {"node_id": r[0], "node_type": r[1], "api_key": r[2], "description": r[3], "registered": r[4]}

    def register_node(self, node_id: str, node_type: str, api_key: str, description: str = ""):
        self.client.insert(
            "nodes",
            [[node_id, node_type, api_key, description]],
            column_names=["node_id", "node_type", "api_key", "description"],
        )

    def get_latest_metrics(self, node_id: str) -> dict:
        result = self.client.query(
            """
            SELECT metric, value
            FROM energy_metrics
            WHERE node_id = {node_id:String}
              AND timestamp >= now() - INTERVAL 5 MINUTE
            ORDER BY timestamp DESC
            LIMIT 8
            """,
            parameters={"node_id": node_id},
        )
        return {row[0]: row[1] for row in result.result_rows}


# Singleton
ch_service = ClickHouseService()
