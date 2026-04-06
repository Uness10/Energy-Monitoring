#!/usr/bin/env python3
"""
Generate presentation-quality benchmark visualization charts.
Creates PNG files suitable for PowerPoint/presentations.

Usage:
    python generate_benchmark_charts.py
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams
import numpy as np

# Set up professional style
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Arial', 'Helvetica']
rcParams['figure.dpi'] = 300
rcParams['savefig.dpi'] = 300
rcParams['lines.linewidth'] = 2
rcParams['axes.labelsize'] = 12
rcParams['axes.titlesize'] = 14
rcParams['xtick.labelsize'] = 11
rcParams['ytick.labelsize'] = 11
rcParams['legend.fontsize'] = 11


def generate_throughput_chart():
    """Generate write throughput comparison chart."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    databases = ['ClickHouse\n(CHOSEN)', 'PostgreSQL', 'InfluxDB\n(Overkill)']
    throughput = [16502, 936, 202729]
    colors = ['#90EE90', '#FFB6C1', '#FFD700']
    
    # Create horizontal bar chart
    bars = ax.barh(databases, throughput, color=colors, edgecolor='black', linewidth=1.5)
    
    # Customize
    ax.set_xlabel('Rows/Second (Throughput)', fontsize=12, fontweight='bold')
    ax.set_title('Database Write Throughput Comparison\n(Ingesting 100K metrics)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xscale('log')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, throughput)):
        label_x = val * 1.5
        ax.text(label_x, bar.get_y() + bar.get_height()/2, f'{val:,} rows/sec',
                va='center', ha='left', fontweight='bold', fontsize=11)
    
    # Add decision indicator
    ax.text(16502, -0.5, '✓ Sufficient throughput\nfor 100+ nodes',
            ha='center', fontsize=9, style='italic', color='green', fontweight='bold')
    
    # Add grid
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Set x-axis limits
    ax.set_xlim(100, 500000)
    
    plt.tight_layout()
    plt.savefig('benchmark_writethrough.png', bbox_inches='tight', dpi=300)
    print("✓ Saved: benchmark_writethrough.png")
    plt.close()


def generate_query_performance_chart():
    """Generate query performance comparison chart."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Data: (database, min_ms, max_ms)
    databases = ['ClickHouse\n(CHOSEN)', 'PostgreSQL']
    min_times = [12, 36]
    max_times = [68, 117]
    
    x_pos = np.arange(len(databases))
    width = 0.35
    
    # Create grouped bars
    bars1 = ax.bar(x_pos - width/2, min_times, width, label='Best Case (ms)',
                   color='#4CAF50', edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x_pos + width/2, max_times, width, label='Worst Case (ms)',
                   color='#FF6B6B', edgecolor='black', linewidth=1.5)
    
    # Customize
    ax.set_ylabel('Query Execution Time (milliseconds)', fontsize=12, fontweight='bold')
    ax.set_title('Query Performance Comparison\n(7-day historical aggregation, 100K+ metrics)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(databases, fontsize=11, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}ms', ha='center', va='bottom',
                    fontweight='bold', fontsize=10)
    
    # Add speedup annotation
    speedup = max_times[1] / max_times[0]
    ax.text(0.5, 100, f'ClickHouse is {speedup:.1f}x faster →',
            ha='center', fontsize=11, style='italic', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#90EE90', alpha=0.7))
    
    # Add grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    ax.set_ylim(0, 140)
    
    plt.tight_layout()
    plt.savefig('benchmark_query_performance.png', bbox_inches='tight', dpi=300)
    print("✓ Saved: benchmark_query_performance.png")
    plt.close()


def generate_combined_analysis():
    """Generate combined analysis showing why ClickHouse was chosen."""
    fig = plt.figure(figsize=(14, 8))
    
    # Create grid for subplots
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)
    
    # Chart 1: Write Throughput (top-left)
    ax1 = fig.add_subplot(gs[0, 0])
    databases = ['ClickHouse', 'PostgreSQL', 'InfluxDB']
    throughput = [16502, 936, 202729]
    colors = ['#90EE90', '#FFB6C1', '#FFD700']
    bars = ax1.barh(databases, throughput, color=colors, edgecolor='black', linewidth=1.5)
    ax1.set_xlabel('Rows/Sec', fontweight='bold')
    ax1.set_title('Write Throughput', fontweight='bold', fontsize=11)
    ax1.set_xscale('log')
    ax1.grid(axis='x', alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)
    
    # Chart 2: Query Performance (top-right)
    ax2 = fig.add_subplot(gs[0, 1])
    query_min = [12, 36]
    query_max = [68, 117]
    x = np.arange(2)
    width = 0.35
    ax2.bar(x - width/2, query_min, width, label='Min', color='#4CAF50', edgecolor='black', linewidth=1.5)
    ax2.bar(x + width/2, query_max, width, label='Max', color='#FF6B6B', edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Milliseconds', fontweight='bold')
    ax2.set_title('Query Performance (7-day)', fontweight='bold', fontsize=11)
    ax2.set_xticks(x)
    ax2.set_xticklabels(['ClickHouse', 'PostgreSQL'], fontsize=9)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_axisbelow(True)
    
    # Chart 3: Complexity Score (bottom-left)
    ax3 = fig.add_subplot(gs[1, 0])
    complexity = [3, 2, 8]
    colors_complex = ['#90EE90', '#FFB6C1', '#FF6B6B']
    bars = ax3.barh(databases, complexity, color=colors_complex, edgecolor='black', linewidth=1.5)
    ax3.set_xlabel('Operational Complexity', fontweight='bold')
    ax3.set_title('Setup & Maintenance', fontweight='bold', fontsize=11)
    ax3.set_xlim(0, 10)
    for bar, val in zip(bars, complexity):
        ax3.text(val + 0.2, bar.get_y() + bar.get_height()/2, f'{val}/10',
                va='center', fontweight='bold', fontsize=9)
    ax3.grid(axis='x', alpha=0.3, linestyle='--')
    ax3.set_axisbelow(True)
    
    # Chart 4: Decision Rationale (bottom-right)
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('off')
    
    analysis_text = """
    DECISION RATIONALE
    
    ✓ ClickHouse Selected:
      • 16.5K rows/sec: SUFFICIENT for 100+ nodes
      • 12-68ms queries: APPROPRIATE for dashboard
      • Low complexity: EASY to operate
      • Cost-effective: NO overkill
    
    ✗ PostgreSQL: Too slow for this workload
      (936 rows/sec, 36-117ms queries)
    
    ✗ InfluxDB: Overkill + complex
      (Performance unused, higher ops burden)
    """
    
    ax4.text(0.05, 0.95, analysis_text, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#E8F5E9', alpha=0.8, pad=1))
    
    fig.suptitle('Database Selection Analysis\nBenchmark Results & Architecture Decision',
                fontsize=14, fontweight='bold', y=0.98)
    
    plt.savefig('benchmark_analysis.png', bbox_inches='tight', dpi=300)
    print("✓ Saved: benchmark_analysis.png")
    plt.close()


def generate_architecture_comparison():
    """Generate visual comparison of key metrics across all databases."""
    fig, ax = plt.subplots(figsize=(13, 7))
    
    # Normalized scores (0-10 scale for comparison)
    metrics = ['Write\nThroughput', 'Query\nSpeed', 'Operational\nSimplicity', 'Cost', 'Scalability']
    clickhouse = [8, 9, 8, 9, 9]
    postgresql = [4, 5, 7, 8, 6]
    influxdb = [10, 10, 4, 5, 9]
    
    x = np.arange(len(metrics))
    width = 0.25
    
    # Create bars
    bars1 = ax.bar(x - width, clickhouse, width, label='ClickHouse', 
                   color='#90EE90', edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x, postgresql, width, label='PostgreSQL',
                   color='#FFB6C1', edgecolor='black', linewidth=1.5)
    bars3 = ax.bar(x + width, influxdb, width, label='InfluxDB',
                   color='#FFD700', edgecolor='black', linewidth=1.5)
    
    # Customize
    ax.set_ylabel('Score (0-10)', fontsize=12, fontweight='bold')
    ax.set_title('Database Comparison Matrix\n(Scoring each dimension for 100+ node monitoring)',
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11, fontweight='bold')
    ax.set_ylim(0, 11)
    ax.legend(fontsize=11, loc='upper right')
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                   f'{height:.0f}', ha='center', va='bottom',
                   fontweight='bold', fontsize=9)
    
    # Add grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Add decision indicator
    ax.text(0, -1.5, '→ ClickHouse: Best balance of performance, simplicity, and cost',
           fontsize=11, fontweight='bold', color='green')
    
    plt.tight_layout()
    plt.savefig('benchmark_comparison_matrix.png', bbox_inches='tight', dpi=300)
    print("✓ Saved: benchmark_comparison_matrix.png")
    plt.close()


def main():
    """Generate all benchmark charts."""
    print("Generating presentation-quality benchmark charts...\n")
    
    generate_throughput_chart()
    generate_query_performance_chart()
    generate_combined_analysis()
    generate_architecture_comparison()
    
    print("\n✅ All charts generated successfully!")
    print("\nFiles created:")
    print("  1. benchmark_writethrough.png - Write throughput comparison")
    print("  2. benchmark_query_performance.png - Query speed comparison")
    print("  3. benchmark_analysis.png - Combined analysis with rationale")
    print("  4. benchmark_comparison_matrix.png - Multi-dimension comparison")
    print("\nReady for PowerPoint insertion!")


if __name__ == "__main__":
    main()
