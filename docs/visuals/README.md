# Presentation Visuals - Energy Monitoring System

This directory contains all diagrams and visual assets for the 15-minute presentation on the distributed energy monitoring platform.

## Files Overview

| File | Slide | Diagram Type | Purpose |
|------|-------|-------------|---------|
| `01-system-architecture.md` | Slide 3 | Network/Flowchart | 3-tier architecture with data flow |
| `02-node-health-states.md` | Slide 7 | State Machine | Health state transitions (ONLINE/STALE/OFFLINE) |
| `03-k-sigma-learning.md` | Slide 7 | Flow Diagram | Adaptive timeout calculation with examples |
| `04-api-resilience-pattern.md` | Slide 8 | Sequence Diagram | Request lifecycle and resilience patterns |
| `05-data-collection-methods.md` | Slide 5 | Comparison Chart | Platform-specific measurement methods |

## Quick Usage

### In Markdown/GitHub
All files are `.md` with embedded Mermaid diagrams. They render automatically on:
- GitHub (README, pull requests)
- VS Code with Markdown preview
- Any Markdown viewer with Mermaid support

### Convert to Images (PNG/SVG)

#### Option 1: Mermaid CLI
```bash
# Install: npm install -g @mermaid-js/mermaid-cli
mmdc -i 01-system-architecture.md -o 01-system-architecture.svg
mmdc -i 01-system-architecture.md -o 01-system-architecture.png
```

#### Option 2: Use Online Converter
Visit https://mermaid.live/ and paste the diagram markup (copy the code block from each file)

#### Option 3: VS Code Extension
Install "Markdown Preview Mermaid Support" extension, then right-click → Export as PNG

### Insert into PowerPoint

1. **Export as PNG** using one of the methods above
2. **Insert → Pictures** → Select PNG
3. **Right-click → Replace or Update** as needed

## Presentation Flow

```
SEGMENT 1: Problem (3 min)
  └─ Slides 1-2: Context + challenges

SEGMENT 2: Solution (2 min)
  ├─ Slide 3: [📊 USE: 01-system-architecture.md]
  └─ Slide 4: Principles (no visual)

SEGMENT 3: Technical Deep Dive (6 min)
  ├─ Slide 5: [📊 USE: 05-data-collection-methods.md]
  ├─ Slide 6: Aggregation (use actual query screenshot)
  ├─ Slide 7: [📊 USE: 02-node-health-states.md + 03-k-sigma-learning.md]
  └─ Slide 8: [📊 USE: 04-api-resilience-pattern.md]

SEGMENT 4: Live Demo (3 min)
  ├─ Demo 1: Dashboard screenshot
  ├─ Demo 2: Dashboard with stale node highlighted
  └─ Demo 3: Query terminal output

SEGMENT 5: Results (1 min)
  └─ Slides 9-10: Use benchmark bar chart + bullet points
```

## Additional Assets

### Benchmark Comparison Chart

Use the Python script to generate:
```bash
python benchmarks/generate_benchmark_charts.py
```

This creates:
- `benchmark_writethrough.png` (Write throughput comparison)
- `benchmark_query_performance.png` (Query speed comparison)

### Dashboard Screenshots

Capture from live system:
1. **Demo 1**: Normal operation (all nodes ONLINE)
2. **Demo 2**: After stopping a daemon (1 node STALE/OFFLINE)
3. **Demo 3**: Query result with execution time

### Mermaid Rendering Quality

The diagrams are optimized for:
- **Resolution**: 1920x1080 (Full HD projector)
- **Font Size**: Readable from 10 feet away
- **Colors**: High contrast (accessible for colorblind)
- **Elements**: Minimal but clear

## Export Settings

When exporting Mermaid to PNG/SVG:
- **DPI**: 300 (for printing, if needed)
- **Width**: 1920px
- **Height**: Auto (usually 1080-1440px)

## Version Control

**Committed to Git:**
- ✓ All `.md` files (source diagrams)
- ✓ This README

**NOT Committed (generated):**
- `.png`, `.svg` files (too large)
- Generate on-demand for presentations

## Reusing These Diagrams

These diagrams are designed to be presentation-agnostic. You can reuse them for:
- Technical documentation
- Architecture reviews
- Blog posts
- Training materials

Just ensure proper attribution and maintain consistency with the project.

## Troubleshooting

**Diagram doesn't render?**
- Ensure Mermaid is enabled in your viewer
- Try copying the code block to https://mermaid.live/

**Need to modify?**
- Edit the Mermaid code in the `.md` file
- Re-export or re-render
- Test in multiple viewers before final presentation

**Want a different style?**
- Edit the `style` blocks in the Mermaid code
- Refer to [Mermaid documentation](https://mermaid.js.org/) for syntax
