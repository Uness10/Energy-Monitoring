# k-sigma Timeout Learning

## Diagram

```mermaid
graph TB
    subgraph Example["Example: 3 Different Nodes"]
        N1["Node-1: Fast sender<br/>Intervals: 10, 10.2, 9.8, 10.1<br/>mean=10, σ=0.15<br/>⟹ timeout = 10 + 4×0.15 = 10.6s"]
        N2["Node-2: Slow sender<br/>Intervals: 58, 62, 60, 59<br/>mean=60, σ=2<br/>⟹ timeout = 60 + 4×2 = 68s"]
        N3["Node-3: Learned pattern<br/>Intervals: 30, 28, 32, 35, 29, 31<br/>mean=31, σ=2.5<br/>⟹ timeout = 31 + 4×2.5 = 41s"]
    end
    
    Result["✓ No false positives!<br/>✓ Fast real-failure detection!<br/>Statistical confidence: 99.99% (4σ)"]
    
    Example --> Result
```

## Usage

- **Presentation Slide**: Slide 7 (Heartbeat Problem)
- **File Format**: Mermaid (flow diagram)
- **Purpose**: Explain adaptive timeout calculation

## Formula

```
timeout = mean_interval + 4 × standard_deviation
```

- **mean_interval**: Average time between node's heartbeats
- **standard_deviation**: Variation in that interval
- **4×σ**: 99.99% confidence level (statistical guarantee)

## Why This Works

- Different nodes have different network latencies and load patterns
- Fixed timeout: Either too strict (false alarms) or too loose (slow detection)
- Adaptive k-sigma: Learns each node's unique pattern
- Statistical guarantee: Only 0.01% chance of false positive

## Comparison

| Strategy | Fast Nodes | Slow Nodes | False Positives |
|----------|-----------|-----------|-----------------|
| Fixed 30s | ✓ STALE after 15s | ❌ Never OFFLINE | High |
| Fixed 120s | ✗ Never STALE | ✓ OK | Very High |
| k-sigma | ✓ Timeout ≈ 10s | ✓ Timeout ≈ 68s | 0.01% (optimal) |
