#!/usr/bin/env python3
"""
Analyze benchmark results and generate plots (matplotlib optional).
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import statistics

try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib not available. Analysis will be text only.")

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_latest_results():
    """Load the latest benchmark results."""
    json_files = sorted(RESULTS_DIR.glob("benchmark_results_*.json"))
    if not json_files:
        print("No benchmark results found")
        return None
    
    latest = json_files[-1]
    with open(latest) as f:
        return json.load(f)


def analyze_results(results):
    """Analyze benchmark results."""
    print("\n" + "="*80)
    print("BENCHMARK ANALYSIS")
    print("="*80)
    
    analysis = {}
    
    for db_name, db_results in results.items():
        print(f"\n{db_name.upper()}")
        print("-" * 40)
        
        analysis[db_name] = {}
        
        # Write throughput
        if "write" in db_results:
            throughput = db_results["write"].get("throughput_rows_per_sec", 0)
            write_time = db_results["write"].get("time_seconds", 0)
            analysis[db_name]["write_throughput"] = throughput
            analysis[db_name]["write_time"] = write_time
            
            print(f"Write Throughput: {throughput:>12,.0f} rows/sec")
            print(f"Write Time:       {write_time:>12.2f} seconds")
        
        # Query performance
        if "queries" in db_results:
            queries = db_results["queries"]
            query_times = list(queries.values())
            
            if query_times:
                avg_query = statistics.mean(query_times)
                min_query = min(query_times)
                max_query = max(query_times)
                
                analysis[db_name]["avg_query_ms"] = avg_query
                analysis[db_name]["min_query_ms"] = min_query
                analysis[db_name]["max_query_ms"] = max_query
                
                print(f"Avg Query Time:   {avg_query:>12.2f} ms")
                print(f"Min Query Time:   {min_query:>12.2f} ms")
                print(f"Max Query Time:   {max_query:>12.2f} ms")
                
                print("\nQuery Details:")
                for q_name, q_time in sorted(queries.items()):
                    print(f"  {q_name}: {q_time:>10.2f}ms")
    
    return analysis


def generate_plots(results, analysis):
    """Generate comparison plots (skipped if matplotlib unavailable)."""
    if not HAS_MATPLOTLIB:
        print("Skipping plot generation (matplotlib not available)")
        return
    
    db_names = list(results.keys())
    
    # ─── Plot 1: Write Throughput ───────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    
    write_throughputs = []
    for db in db_names:
        tp = analysis[db].get("write_throughput", 0)
        write_throughputs.append(tp)
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    bars = ax.bar(db_names, write_throughputs, color=colors[:len(db_names)])
    
    ax.set_ylabel('Throughput (rows/sec)', fontsize=12, fontweight='bold')
    ax.set_title('Write Throughput Comparison', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:,.0f}',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "write_throughput.png", dpi=150)
    print("✓ Saved write_throughput.png")
    plt.close()
    
    # ─── Plot 2: Query Performance ──────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    
    avg_queries = []
    for db in db_names:
        avg = analysis[db].get("avg_query_ms", 0)
        avg_queries.append(avg)
    
    bars = ax.bar(db_names, avg_queries, color=colors[:len(db_names)])
    
    ax.set_ylabel('Time (milliseconds)', fontsize=12, fontweight='bold')
    ax.set_title('Average Query Time Comparison', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}ms',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "query_performance.png", dpi=150)
    print("✓ Saved query_performance.png")
    plt.close()
    
    # ─── Plot 3: Query Performance Breakdown ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 6))
    
    query_names = ["Q1 (Avg)", "Q2 (Group By)", "Q3 (Time Range)"]
    x = np.arange(len(query_names))
    width = 0.2
    
    for i, db in enumerate(db_names):
        queries = results[db].get("queries", {})
        times = [queries.get(f"q{j+1}_", 0) for j in range(3)]
        
        # Get actual query times
        q_times = []
        for j in range(1, 4):
            for q_key, q_val in queries.items():
                if f"q{j}_" in q_key:
                    q_times.append(q_val)
                    break
            else:
                q_times.append(0)
        
        ax.bar(x + i*width, q_times, width, label=db, color=colors[i])
    
    ax.set_ylabel('Time (milliseconds)', fontsize=12, fontweight='bold')
    ax.set_title('Query Performance Breakdown', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * (len(db_names) - 1) / 2)
    ax.set_xticklabels(query_names)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "query_breakdown.png", dpi=150)
    print("✓ Saved query_breakdown.png")
    plt.close()
    
    # ─── Plot 4: Overall Performance Score ─────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    
    scores = []
    for db in db_names:
        # Higher throughput is better (normalize to 0-100)
        throughput = analysis[db].get("write_throughput", 1)
        max_throughput = max(analysis[d].get("write_throughput", 1) for d in db_names)
        tp_score = (throughput / max_throughput) * 50 if max_throughput > 0 else 0
        
        # Lower query time is better
        avg_query = analysis[db].get("avg_query_ms", 1)
        max_query = max(analysis[d].get("avg_query_ms", 1) for d in db_names)
        q_score = (1 - (avg_query / max_query)) * 50 if max_query > 0 else 0
        
        total_score = tp_score + q_score
        scores.append(total_score)
    
    bars = ax.bar(db_names, scores, color=colors[:len(db_names)])
    
    ax.set_ylabel('Score (0-100)', fontsize=12, fontweight='bold')
    ax.set_title('Overall Performance Score', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "overall_score.png", dpi=150)
    print("✓ Saved overall_score.png")
    plt.close()


def generate_report(results, analysis):
    """Generate text report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
{'='*80}
DATABASE BENCHMARK REPORT
{'='*80}
Generated: {timestamp}

BENCHMARK PARAMETERS:
- Nodes: {10}
- Apps per node: {5}
- Metrics per node: {100_000:,}
- Batch size: {1000}
- Total time series: {50}

{'='*80}
RESULTS SUMMARY
{'='*80}

"""
    
    for db_name, db_analysis in analysis.items():
        report += f"\n{db_name.upper()}\n"
        report += "-" * 40 + "\n"
        
        tp = db_analysis.get("write_throughput", 0)
        wt = db_analysis.get("write_time", 0)
        aq = db_analysis.get("avg_query_ms", 0)
        minq = db_analysis.get("min_query_ms", 0)
        maxq = db_analysis.get("max_query_ms", 0)
        
        report += f"Write Throughput:     {tp:>12,.0f} rows/sec\n"
        report += f"Write Time:           {wt:>12.2f} seconds\n"
        report += f"Avg Query Time:       {aq:>12.2f} ms\n"
        report += f"Min Query Time:       {minq:>12.2f} ms\n"
        report += f"Max Query Time:       {maxq:>12.2f} ms\n"
    
    report += f"\n{'='*80}\n"
    report += "RECOMMENDATIONS\n"
    report += f"{'='*80}\n\n"
    
    # Find best in each category
    best_throughput = max(analysis.items(), key=lambda x: x[1].get("write_throughput", 0))
    best_query = min(analysis.items(), key=lambda x: x[1].get("avg_query_ms", float('inf')))
    
    report += f"Best Write Performance: {best_throughput[0]} ({best_throughput[1].get('write_throughput', 0):,.0f} rows/sec)\n"
    report += f"Best Query Performance: {best_query[0]} ({best_query[1].get('avg_query_ms', 0):.2f}ms avg)\n"
    
    report += "\nCONCLUSION:\n"
    report += "- Use the above results to choose the best database for your workload\n"
    report += "- Consider both write throughput and query speed in your decision\n"
    
    report_path = RESULTS_DIR / "benchmark_report.txt"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\n✓ Report saved to {report_path}")
    print(report)


if __name__ == "__main__":
    results = load_latest_results()
    
    if results:
        analysis = analyze_results(results)
        generate_plots(results, analysis)
        generate_report(results, analysis)
        
        print("\n" + "="*80)
        print("All analysis files saved to:", RESULTS_DIR)
        print("="*80)
    else:
        print("No benchmark results to analyze. Run multi_db_benchmark.py first.")
