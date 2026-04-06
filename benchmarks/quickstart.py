#!/usr/bin/env python3
"""
Quick start benchmark script - simplified workflow.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command."""
    print(f"\n{'='*80}")
    print(f"→ {description}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n✗ Failed: {description}")
        return False
    
    print(f"\n✓ Complete: {description}")
    return True


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         MULTI-DATABASE BENCHMARK QUICK START                              ║
║                                                                            ║
║  This will benchmark 4 databases:                                         ║
║  • ClickHouse  - Column-oriented OLAP                                     ║
║  • TimescaleDB - PostgreSQL + Time-Series                                 ║
║  • InfluxDB    - Time-Series Specialized                                  ║
║  • PostgreSQL  - Traditional Relational                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Install dependencies
    if not run_command(
        f"{sys.executable} -m pip install -q -r requirements_benchmark.txt",
        "Installing core benchmark dependencies"
    ):
        print("\nℹ  Installation failed. You can still run the benchmark without visualization.")
        # Don't exit - continue anyway
    
    # Step 2: Run benchmark
    if not run_command(
        f"{sys.executable} multi_db_benchmark.py",
        "Running comprehensive multi-database benchmark"
    ):
        return
    
    # Step 3: Generate analysis
    if not run_command(
        f"{sys.executable} analyze_benchmark.py",
        "Generating analysis and visualizations"
    ):
        return
    
    # Summary
    print(f"\n{'='*80}")
    print("BENCHMARK COMPLETE!")
    print(f"{'='*80}")
    
    results_dir = Path(__file__).parent / "results"
    print(f"\n✓ Results saved to: {results_dir}")
    print("\nGenerated files:")
    print("  • write_throughput.png      - Write speed comparison")
    print("  • query_performance.png     - Query speed comparison")
    print("  • query_breakdown.png       - Detailed query analysis")
    print("  • overall_score.png         - Performance scores")
    print("  • benchmark_report.txt      - Detailed text report")
    print("  • benchmark_results_*.json  - Raw data")
    print("  • benchmark_summary_*.csv   - Summary table")
    
    print("\n💡 Recommendations:")
    print("  1. Open the PNG files to visualize performance")
    print("  2. Read benchmark_report.txt for analysis")
    print("  3. Compare the databases for your use case")
    print("  4. Modify NUM_METRICS_PER_NODE to test different scales")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Benchmark cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        sys.exit(1)
