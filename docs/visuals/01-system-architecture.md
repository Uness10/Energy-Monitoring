# System Architecture - 3-Tier Distributed Monitoring

## Diagram

```mermaid
graph TB
    subgraph Dashboard["📊 DASHBOARD LAYER"]
        UI["Real-time Dashboard<br/>10 nodes live view<br/>Power breakdown by app"]
    end
    
    subgraph API["🔧 AGGREGATION LAYER<br/>FastAPI Backend"]
        Auth["Auth & Rate<br/>Limiting"]
        AutoReg["Auto-register<br/>Idempotent"]
        Heartbeat["Heartbeat<br/>Service"]
        Fallback["Fallback Power<br/>Calculation"]
    end
    
    subgraph Daemon["🖥️ COLLECTION LAYER<br/>Autonomous Daemons"]
        D1["Linux Node<br/>Intel RAPL<br/>10s interval"]
        D2["Windows Node<br/>psutil CPU<br/>10s interval"]
        D3["RPi Node<br/>INA219/fallback<br/>10s interval"]
    end
    
    subgraph Storage["💾 STORAGE LAYER<br/>ClickHouse Cluster"]
        CH1["Shard 1<br/>Primary"]
        CH2["Shard 1<br/>Replica"]
    end
    
    D1 -->|metrics| Auth
    D2 -->|metrics| Auth
    D3 -->|metrics| Auth
    Auth --> AutoReg
    AutoReg --> Fallback
    Fallback --> Heartbeat
    Heartbeat -->|insert + heartbeat| CH1
    CH1 -.->|replicate| CH2
    CH1 -->|query| UI
    CH2 -->|query| UI
    
    style Dashboard fill:#90EE90
    style API fill:#87CEEB
    style Daemon fill:#FFB6C1
    style Storage fill:#DDA0DD
```

## Usage

- **Presentation Slide**: Slide 3 (Solution Overview)
- **File Format**: Mermaid (renders in VS Code, GitHub, Markdown viewers)
- **Export**: Copy to PowerPoint or use Mermaid CLI to export as PNG/SVG

## Key Points

- 4-tier architecture: Collection → Aggregation → Storage → Visualization
- Push-based architecture (daemons initiate)
- Stateless API layer scales horizontally
- Autonomous daemon operation (tolerates backend downtime)
