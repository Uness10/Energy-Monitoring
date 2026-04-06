#!/usr/bin/env python3
"""
Benchmark installer for Windows (bypasses MSYS64 SSL issues).
Run this from Anaconda Prompt or Windows cmd.
"""

import subprocess
import sys
import platform

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
print(f"Platform: {platform.platform()}\n")

packages = [
    "clickhouse-connect",
    "influxdb-client",
]

print("Installing core benchmark packages...\n")

for package in packages:
    print(f"→ Installing {package}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", package],
        capture_output=False
    )
    if result.returncode == 0:
        print(f"✓ {package} installed\n")
    else:
        print(f"✗ {package} failed (will try next)\n")

# psycopg2-binary needs special handling
print("→ Installing psycopg2-binary...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "--no-build-isolation", "psycopg2-binary"],
    capture_output=False
)
if result.returncode == 0:
    print("✓ psycopg2-binary installed\n")
else:
    print("✗ psycopg2-binary skipped (TimescaleDB tests won't run)\n")

# Try matplotlib (optional)
print("→ Installing matplotlib (optional for charts)...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "matplotlib"],
    capture_output=False
)
if result.returncode == 0:
    print("✓ matplotlib installed (plots will be generated)\n")
else:
    print("⚠  matplotlib skipped (text analysis only)\n")

print("="*80)
print("Installation complete!")
print("="*80)
print("\n✓ Ready to run benchmark:")
print("  python quickstart.py")
print("\nOr manually:")
print("  python multi_db_benchmark.py")
print("  python analyze_benchmark.py")
