-- Energy Monitoring System - ClickHouse Schema
-- Run automatically on container first start

CREATE DATABASE IF NOT EXISTS energy_monitoring;

-- Main data table: one row per metric per timestamp
CREATE TABLE IF NOT EXISTS energy_monitoring.energy_metrics (
    timestamp   DateTime64(3),
    node_id     LowCardinality(String),
    
    metric      LowCardinality(String),
    value       Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (node_id, metric, timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- Hourly aggregation materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS energy_monitoring.energy_hourly_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMMDD(hour)
ORDER BY (node_id, metric, hour)
AS SELECT
    toStartOfHour(timestamp)    AS hour,
    node_id,
    metric,
    avg(value)                  AS avg_value,
    min(value)                  AS min_value,
    max(value)                  AS max_value,
    count()                     AS sample_count
FROM energy_monitoring.energy_metrics
GROUP BY hour, node_id, metric;

-- Daily energy summary materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS energy_monitoring.energy_daily_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (node_id, day)
AS SELECT
    toDate(timestamp)                                           AS day,
    node_id,
    sum(if(metric='power_w', value, 0)) /
        count(if(metric='power_w', value, NULL))                AS avg_power_w,
    max(if(metric='power_w', value, 0))                         AS peak_power_w,
    max(if(metric='temperature', value, 0))                     AS peak_temp
FROM energy_monitoring.energy_metrics
GROUP BY day, node_id;

-- Registered nodes table
CREATE TABLE IF NOT EXISTS energy_monitoring.nodes (
    node_id         String,
    node_type       LowCardinality(String),
    api_key         String,
    description     String,
    registered      DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY node_id;
