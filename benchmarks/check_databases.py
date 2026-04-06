#!/usr/bin/env python3
"""
Setup script to prepare all 4 databases for benchmarking.
Checks docker, PostgreSQL, InfluxDB, and ClickHouse connectivity.
"""

import subprocess
import sys
import time
import socket
from pathlib import Path

def check_port(host, port, service_name):
    """Check if a service is listening on a port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✓ {service_name:20s} is running on {host}:{port}")
            return True
        else:
            print(f"✗ {service_name:20s} NOT available on {host}:{port}")
            return False
    except Exception as e:
        print(f"✗ {service_name:20s} Error: {e}")
        return False

def run_command(cmd, description):
    """Run a shell command."""
    print(f"\n→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"  ✓ Success")
            return True
        else:
            print(f"  ✗ Failed: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("="*80)
    print("DATABASE BENCHMARK SETUP CHECKER")
    print("="*80)
    
    services = [
        ("ClickHouse Primary", "localhost", 8123),
        ("ClickHouse Native", "localhost", 9000),
        ("PostgreSQL", "localhost", 5432),
        ("InfluxDB", "localhost", 8086),
    ]
    
    print("\n1. CHECKING SERVICES")
    print("-"*80)
    
    status = {}
    for name, host, port in services:
        status[name] = check_port(host, port, name)
        time.sleep(0.5)
    
    print("\n2. SETUP INSTRUCTIONS")
    print("-"*80)
    
    # ClickHouse
    if not status.get("ClickHouse Primary") or not status.get("ClickHouse Native"):
        print("\n🔴 ClickHouse is NOT running")
        print("   Run from project root:")
        print("   docker-compose up -d clickhouse-01 clickhouse-02 clickhouse-keeper")
        print("\n   OR if Docker network issue:")
        print("   docker-compose logs clickhouse-01")
    else:
        print("\n🟢 ClickHouse is ready")
    
    # PostgreSQL
    if not status.get("PostgreSQL"):
        print("\n🔴 PostgreSQL is NOT running")
        print("   Option 1: Use Docker")
        print("   docker run -d -p 5432:5432 --name postgres -e POSTGRES_PASSWORD=postgres postgres:16-alpine")
        print("\n   Option 2: Install locally")
        print("   Windows: https://www.postgresql.org/download/windows/")
        print("   Then create database: createdb benchmarks")
    else:
        print("\n🟢 PostgreSQL is ready")
    
    # InfluxDB
    if not status.get("InfluxDB"):
        print("\n🔴 InfluxDB is NOT running")
        print("   Option 1: Use Docker")
        print("   docker run -d -p 8086:8086 --name influxdb influxdb:latest")
        print("\n   Option 2: Download from https://www.influxdata.com/products/influxdb/")
    else:
        print("\n🟢 InfluxDB is ready")
    
    print("\n3. TROUBLESHOOTING")
    print("-"*80)
    
    if not all(status.values()):
        print("\n⚠️  Some services are down. Run these commands:\n")
        print("# Restart Docker")
        print("docker-compose down")
        print("docker-compose up -d\n")
        
        print("# Check Docker status")
        print("docker ps\n")
        
        print("# View logs")
        print("docker-compose logs clickhouse-01")
        print("docker-compose logs postgres  (if using Docker)")
        print("docker-compose logs influxdb  (if using Docker)")
    
    print("\n4. READY TO BENCHMARK?")
    print("-"*80)
    
    all_ready = all(status.values())
    if all_ready:
        print("\n✓ All 4 databases are running!")
        print("\nRun benchmark:")
        print("  cd benchmarks")
        print("  python multi_db_benchmark.py")
    else:
        ready_count = sum(status.values())
        print(f"\n⚠️  Only {ready_count}/4 databases ready")
        print("\nAfter fixing the above, run:")
        print("  cd benchmarks")
        print("  python multi_db_benchmark.py")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
