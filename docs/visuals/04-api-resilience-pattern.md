# API Resilience Pattern - Stateless Ingestion

## Diagram

```mermaid
sequenceDiagram
    participant Daemon as Daemon (Node-5)
    participant API as FastAPI Backend
    participant CH as ClickHouse
    
    Daemon->>API: POST /metrics<br/>{node_id, power_w, cpu_percent}
    
    rect rgb(200, 220, 255)
    API->>API: 1. Auto-register node<br/>(if not exists)
    API->>API: 2. Estimate power<br/>(if power_w == 0)
    end
    
    API->>CH: 3. Insert metrics<br/>(fire-and-forget)
    API->>API: 4. Record heartbeat<br/>(async, non-blocking)
    
    API-->>Daemon: {"status": "ok"} ⚡ 2ms
    
    Note over CH: Processing continues<br/>while request returns
```

## Usage

- **Presentation Slide**: Slide 8 (API Design for Reliability)
- **File Format**: Mermaid (sequence diagram)
- **Purpose**: Show request lifecycle and resilience patterns

## Key Principles

### 1. **Idempotent Operations**
- Auto-register checks if node exists first
- Safe to retry without side effects
- No database locks needed

### 2. **Graceful Degradation**
- If `power_w == 0` but `cpu_percent > 0`: Estimate power
- Formula: `10W + (cpu% / 100) × 50W`
- Process never rejects data

### 3. **Async Acknowledgment**
- Heartbeat recording is non-blocking
- ClickHouse insert is "fire-and-forget"
- Request returns in <2ms

### 4. **Stateless Design**
- No session tracking
- No locks or transactions
- Scales horizontally (add more API instances)
- Each instance independent

## Production Pattern

This pattern is used by:
- **Stripe**: Payment ingestion API
- **Datadog**: Metrics collection
- **New Relic**: Event ingestion
- **CloudFlare**: Log streaming

All designed for high-reliability distributed data collection.
