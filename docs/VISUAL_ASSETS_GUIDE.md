# Presentation Visual Assets - Quick Reference

## 📊 All Visual Files Ready

### Location: `docs/visuals/` (Editable Diagrams - Mermaid Format)

| File | Slide | Diagram Type | Use For |
|------|-------|-------------|---------|
| `01-system-architecture.md` | **Slide 4** | System flowchart | 3-tier architecture + data flow |
| `02-node-health-states.md` | **Slide 8** | State machine | ONLINE → STALE → OFFLINE transitions |
| `03-k-sigma-learning.md` | **Slide 8** | Comparison table | Learns node-specific timeouts |
| `04-api-resilience-pattern.md` | **Slide 9** | Sequence diagram | Request lifecycle (resilience pattern) |
| `05-data-collection-methods.md` | **Slide 6** | Platform comparison | Linux/Windows/RPi accuracy levels |
| `README.md` | Reference | Instructions | How to convert/export diagrams |

### Location: `benchmarks/` (Ready-to-Use PNG Charts - 300 DPI)

| File | Slide | Purpose | Size |
|------|-------|---------|------|
| `benchmark_writethrough.png` | **Slide 13** | Write throughput bars | 171 KB |
| `benchmark_query_performance.png` | **Slide 13** | Query speed comparison | 194 KB |
| `benchmark_analysis.png` | **Slide 13** | Combined multi-panel analysis | 385 KB |
| `benchmark_comparison_matrix.png` | **Slide 13** | Database scoring matrix | 186 KB |

---

## 🚀 Quick Usage Guide

### For Diagrams (Mermaid)

**Option 1: View in VS Code** (Easiest)
```bash
# Open any .md file in docs/visuals/
# Markdown preview auto-renders diagram
```

**Option 2: Export to PNG** (For PowerPoint)
```bash
# Using Mermaid CLI
npm install -g @mermaid-js/mermaid-cli
mmdc -i docs/visuals/01-system-architecture.md -o diagram.png

# OR use online: https://mermaid.live/
# Copy-paste code block from any .md file
```

**Option 3: Embed in PowerPoint**
1. Export as PNG using above method
2. Insert → Pictures → Select PNG
3. Done!

### For Charts (PNG)

**Copy directly to PowerPoint:**
```bash
# Just copy these files:
benchmarks/benchmark_writethrough.png
benchmarks/benchmark_query_performance.png
benchmarks/benchmark_analysis.png
```

---

## 📋 Presentation Mapping

### Segment 1: Problem (3 min)
- No specific visuals needed (text + context)

### Segment 2: Solution (2 min)
- **Slide 3**: Use `01-system-architecture.md`
  - Shows: 4-layer stack, data flow, 10s intervals
- **Slide 4**: Principles (text only, no visual needed)

### Segment 3: Technical Deep Dive (6 min)
- **Slide 5**: Use `05-data-collection-methods.md`
  - Shows: Linux RAPL (⭐⭐⭐⭐⭐) vs Windows psutil (⭐⭐⭐) vs RPi INA219
  
- **Slide 6**: Aggregation
  - Text + SQL query screenshot (capture from running system)

- **Slide 7**: Heartbeat Problem
  - Use `02-node-health-states.md` (state transitions)
  - Use `03-k-sigma-learning.md` (mathematical model with examples)

- **Slide 8**: API Design
  - Use `04-api-resilience-pattern.md` (sequence diagram)

### Segment 4: Live Demo (3 min)
- **Demo 1**: Dashboard screenshot (live system)
- **Demo 2**: Dashboard with stale node (annotate 🟡 STALE)
- **Demo 3**: Query terminal output

### Segment 5: Results (1 min)
- **Slide 9**: Use ALL 4 PNG charts from benchmarks/
  - Primary: `benchmark_analysis.png` (summary view)
  - Backup: `benchmark_writethrough.png` + `benchmark_query_performance.png`

---

## 🎨 Design Consistency

All visuals use consistent color scheme:
- **Green** (#90EE90) = ClickHouse / Recommended / Online
- **Pink** (#FFB6C1) = PostgreSQL / Alternative / Previous
- **Yellow** (#FFD700) = InfluxDB / Overkill / Caution
- **Blue** (#87CEEB) = API Layer / Processing
- **Purple** (#DDA0DD) = Storage / Database

---

## 📝 Files Generated

### In Project Root:
```
d:\S8\DS\Project2\Energy-Monitoring\
├── docs/
│   └── visuals/
│       ├── 01-system-architecture.md
│       ├── 02-node-health-states.md
│       ├── 03-k-sigma-learning.md
│       ├── 04-api-resilience-pattern.md
│       ├── 05-data-collection-methods.md
│       └── README.md
│
├── benchmarks/
│   ├── benchmark_writethrough.png
│   ├── benchmark_query_performance.png
│   ├── benchmark_analysis.png
│   ├── benchmark_comparison_matrix.png
│   └── generate_benchmark_charts.py (script)
│
└── PRESENTATION_PLAN.md (updated with visual references)
```

---

## ✅ Checklist for Presentation

- [ ] Review all diagrams in `docs/visuals/`
- [ ] Convert 1-2 key diagrams to PNG if needed (for offline viewing)
- [ ] Copy `benchmarks/*.png` files to presentation folder
- [ ] Capture live dashboard screenshots (Demos 1-3)
- [ ] Test all visuals project on presentation device
- [ ] Ensure font sizes readable from back of room
- [ ] Verify color scheme displays correctly (no projector color shifts)

---

## 🤝 Sharing Diagrams

### With Team (Pre-presentation Review)
```bash
# Send the .md files - they're lightweight and viewable in GitHub
# Team can comment on diagrams before final export
```

### For External Sharing
```bash
# Export diagrams to PNG first
# Easier to view/embed in reports, emails, etc.
```

### In Documentation
```bash
# Reference diagrams from this README
# Link: docs/visuals/01-system-architecture.md
# Auto-renders in GitHub, markdown viewers
```

---

## 🎯 Pro Tips

1. **Consistency**: All diagrams use same style - feels polished
2. **Editable**: Change colors/text in Mermaid anytime before export
3. **Resolution**: PNG files optimized for projector (300 DPI, 1920x1080)
4. **Accessible**: High contrast helps colorblind audiences
5. **Fast Export**: Can regenerate benchmark charts anytime with `python generate_benchmark_charts.py`

Ready for presentation! Good luck! 🚀
