-- Energy Monitoring System - ClickHouse Schema (Revised)
-- Run automatically on container first start
-- Supports 2-node replication via ReplicatedMergeTree

CREATE DATABASE IF NOT EXISTS energy_monitoring;

-- ─────────────────────────────────────────────────────────
-- Main data table
-- One row per (node, app, metric, timestamp)
-- app_name = 'system' for whole-node KPIs
-- app_name = 'firefox' etc for per-application energy
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS energy_monitoring.energy_metrics (
    timestamp   DateTime64(3),
    node_id     LowCardinality(String),
    app_name    LowCardinality(String) DEFAULT 'system',
    metric      LowCardinality(String),
    value       Float64
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/energy_metrics', '{replica}')
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (node_id, app_name, metric, timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- ─────────────────────────────────────────────────────────
-- Hourly aggregation (avg / min / max per hour per app)
-- ─────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS energy_monitoring.energy_hourly_mv
ENGINE = ReplicatedAggregatingMergeTree(
    '/clickhouse/tables/energy_hourly_mv', '{replica}'
)
PARTITION BY toYYYYMMDD(hour)
ORDER BY (node_id, app_name, metric, hour)
AS SELECT
    toStartOfHour(timestamp)    AS hour,
    node_id,
    app_name,
    metric,
    avg(value)                  AS avg_value,
    min(value)                  AS min_value,
    max(value)                  AS max_value,
    count()                     AS sample_count
FROM energy_monitoring.energy_metrics
GROUP BY hour, node_id, app_name, metric;

-- ─────────────────────────────────────────────────────────
-- Daily energy summary per node per app
-- ─────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS energy_monitoring.energy_daily_mv
ENGINE = ReplicatedAggregatingMergeTree(
    '/clickhouse/tables/energy_daily_mv', '{replica}'
)
PARTITION BY toYYYYMM(day)
ORDER BY (node_id, app_name, day)
AS SELECT
    toDate(timestamp)                                           AS day,
    node_id,
    app_name,
    sum(if(metric='power_w', value, 0)) /
        count(if(metric='power_w', value, NULL))                AS avg_power_w,
    max(if(metric='power_w', value, 0))                         AS peak_power_w,
    max(if(metric='temperature', value, 0))                     AS peak_temp
FROM energy_monitoring.energy_metrics
GROUP BY day, node_id, app_name;

-- ─────────────────────────────────────────────────────────
-- Per-app energy ranking (hourly, excludes 'system')
-- Used for "which app consumed most energy" queries
-- ─────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS energy_monitoring.energy_app_ranking_mv
ENGINE = ReplicatedAggregatingMergeTree(
    '/clickhouse/tables/energy_app_ranking_mv', '{replica}'
)
PARTITION BY toYYYYMMDD(hour)
ORDER BY (node_id, hour, app_name)
AS SELECT
    toStartOfHour(timestamp)                        AS hour,
    node_id,
    app_name,
    avg(if(metric='power_w', value, 0))             AS avg_power_w,
    sum(if(metric='power_w', value, 0))             AS total_power_w,
    avg(if(metric='cpu_util', value, 0))            AS avg_cpu_util,
    count()                                         AS sample_count
FROM energy_monitoring.energy_metrics
WHERE app_name != 'system'
GROUP BY hour, node_id, app_name;

-- ─────────────────────────────────────────────────────────
-- Registered nodes
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS energy_monitoring.nodes (
    node_id         String,
    node_type       LowCardinality(String),
    api_key         String,
    description     String,
    registered      DateTime DEFAULT now()
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/nodes', '{replica}')
ORDER BY node_id;
